
"""
Migration Engine
Core migration logic for SQLite to DynamoDB migration
"""

import sqlite3
import boto3
import json
import time
from datetime import datetime
from botocore.exceptions import ClientError, BotoCoreError

from data_transformers import DataTransformers
from dynamodb_manager import DynamoDBManager


class MigrationEngine:
    """Main migration engine that orchestrates the migration process"""
    
    def __init__(self, config, state_manager):
        self.config = config
        self.state_manager = state_manager
        self.sqlite_conn = None
        self.dynamodb_manager = None
        self.transformers = DataTransformers()
        
        # Initialize connections
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize database connections"""
        try:
            # SQLite connection
            self.sqlite_conn = sqlite3.connect(self.config['source_db'])
            self.sqlite_conn.row_factory = sqlite3.Row  # Enable column access by name
            
            # DynamoDB connection
            self.dynamodb_manager = DynamoDBManager(
                region=self.config['aws_region'],
                table_configs=self.config['target_tables']
            )
            
        except Exception as e:
            raise Exception(f"Failed to initialize connections: {str(e)}")
    
    def run_migration(self, force=False, specific_table=None):
        """Run the complete migration process"""
        try:
            print("Starting migration process...")
            self.state_manager.start_migration()
            
            # Create DynamoDB tables if they don't exist
            if not self._create_target_tables(force):
                return False
            
            # Determine which tables to migrate
            tables_to_migrate = [specific_table] if specific_table else [
                'MusicCatalog', 'CustomerOrders', 'Playlists', 'EmployeeManagement'
            ]
            
            # Migrate each table
            for table_name in tables_to_migrate:
                if not self.state_manager.is_table_completed(table_name):
                    print(f"\nMigrating {table_name}...")
                    success = self._migrate_table(table_name)
                    if not success:
                        self.state_manager.fail_migration(f"Failed to migrate {table_name}")
                        return False
                else:
                    print(f"\n{table_name} already completed, skipping...")
            
            # Complete migration
            self.state_manager.complete_migration()
            print("\nMigration completed successfully!")
            return True
            
        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            print(error_msg)
            self.state_manager.fail_migration(error_msg)
            return False
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
    
    def resume_migration(self):
        """Resume an interrupted migration"""
        if not self.state_manager.can_resume():
            print("No migration to resume")
            return False
        
        print("Resuming migration...")
        state = self.state_manager.get_state()
        
        # Find incomplete tables
        incomplete_tables = []
        for table_name, table_state in state['tables'].items():
            if table_state['status'] in ['not_started', 'in_progress']:
                incomplete_tables.append(table_name)
        
        if not incomplete_tables:
            self.state_manager.complete_migration()
            print("All tables completed, marking migration as done")
            return True
        
        # Resume migration for incomplete tables
        return self.run_migration(specific_table=None)
    
    def _create_target_tables(self, force=False):
        """Create DynamoDB tables"""
        print("Creating DynamoDB tables...")
        
        for logical_name, physical_name in self.config['target_tables'].items():
            schema = self.config['table_schemas'][logical_name]
            
            try:
                created = self.dynamodb_manager.create_table(
                    table_name=physical_name,
                    schema=schema,
                    force=force
                )
                
                if created:
                    print(f"  ✓ Created table: {physical_name}")
                else:
                    print(f"  ✓ Table exists: {physical_name}")
                    
            except Exception as e:
                print(f"  ✗ Failed to create table {physical_name}: {str(e)}")
                return False
        
        return True
    
    def _migrate_table(self, table_name):
        """Migrate a specific table"""
        try:
            if table_name == 'MusicCatalog':
                return self._migrate_music_catalog()
            elif table_name == 'CustomerOrders':
                return self._migrate_customer_orders()
            elif table_name == 'Playlists':
                return self._migrate_playlists()
            elif table_name == 'EmployeeManagement':
                return self._migrate_employee_management()
            else:
                raise Exception(f"Unknown table: {table_name}")
                
        except Exception as e:
            self.state_manager.add_error(f"Error migrating {table_name}: {str(e)}", table_name)
            return False
    
    def _migrate_music_catalog(self):
        """Migrate music catalog (Artist -> Album -> Track hierarchy)"""
        table_name = 'MusicCatalog'
        physical_table = self.config['target_tables'][table_name]
        
        # Get counts for progress tracking
        counts = self._get_music_catalog_counts()
        total_records = counts['artists'] + counts['albums'] + counts['tracks']
        
        self.state_manager.start_table_migration(table_name, total_records)
        
        # Update entity counts
        for entity_type, count in counts.items():
            self.state_manager.update_entity_progress(table_name, entity_type, total=count)
        
        # Get resume point
        last_artist_id = self.state_manager.get_last_processed_id(table_name, 'artists')
        last_album_id = self.state_manager.get_last_processed_id(table_name, 'albums')
        last_track_id = self.state_manager.get_last_processed_id(table_name, 'tracks')
        
        # Migrate artists
        if not self._migrate_artists(physical_table, last_artist_id):
            return False
        
        # Migrate albums
        if not self._migrate_albums(physical_table, last_album_id):
            return False
        
        # Migrate tracks
        if not self._migrate_tracks(physical_table, last_track_id):
            return False
        
        self.state_manager.complete_table_migration(table_name)
        return True
    
    def _migrate_artists(self, table_name, last_processed_id=None):
        """Migrate artist records"""
        query = """
        SELECT a.ArtistId, a.Name,
               COUNT(DISTINCT al.AlbumId) as AlbumCount,
               COUNT(DISTINCT t.TrackId) as TrackCount
        FROM Artist a
        LEFT JOIN Album al ON a.ArtistId = al.ArtistId
        LEFT JOIN Track t ON al.AlbumId = t.AlbumId
        """
        
        if last_processed_id:
            query += f" WHERE a.ArtistId > {last_processed_id}"
        
        query += " GROUP BY a.ArtistId, a.Name ORDER BY a.ArtistId"
        
        cursor = self.sqlite_conn.execute(query)
        batch_items = []
        processed_count = 0
        
        for row in cursor:
            # Transform artist data
            artist_item = self.transformers.transform_artist(dict(row))
            batch_items.append(artist_item)
            
            # Batch write when limit reached
            if len(batch_items) >= self.config['batch_size']:
                if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                    return False
                
                processed_count += len(batch_items)
                self.state_manager.update_entity_progress(
                    'MusicCatalog', 'artists', 
                    migrated=processed_count, 
                    last_id=row['ArtistId']
                )
                batch_items = []
                print(f"  Migrated {processed_count} artists...")
        
        # Write remaining items
        if batch_items:
            if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                return False
            processed_count += len(batch_items)
            self.state_manager.update_entity_progress(
                'MusicCatalog', 'artists',
                migrated=processed_count,
                last_id=batch_items[-1]['ArtistId']['N']
            )
        
        print(f"  ✓ Migrated {processed_count} artists")
        return True
    
    def _migrate_albums(self, table_name, last_processed_id=None):
        """Migrate album records"""
        query = """
        SELECT al.AlbumId, al.Title, al.ArtistId,
               a.Name as ArtistName,
               COUNT(t.TrackId) as TrackCount
        FROM Album al
        JOIN Artist a ON al.ArtistId = a.ArtistId
        LEFT JOIN Track t ON al.AlbumId = t.AlbumId
        """
        
        if last_processed_id:
            query += f" WHERE al.AlbumId > {last_processed_id}"
        
        query += " GROUP BY al.AlbumId, al.Title, al.ArtistId, a.Name ORDER BY al.AlbumId"
        
        cursor = self.sqlite_conn.execute(query)
        batch_items = []
        processed_count = 0
        
        for row in cursor:
            # Transform album data
            album_item = self.transformers.transform_album(dict(row))
            batch_items.append(album_item)
            
            # Batch write when limit reached
            if len(batch_items) >= self.config['batch_size']:
                if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                    return False
                
                processed_count += len(batch_items)
                self.state_manager.update_entity_progress(
                    'MusicCatalog', 'albums',
                    migrated=processed_count,
                    last_id=row['AlbumId']
                )
                batch_items = []
                print(f"  Migrated {processed_count} albums...")
        
        # Write remaining items
        if batch_items:
            if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                return False
            processed_count += len(batch_items)
            self.state_manager.update_entity_progress(
                'MusicCatalog', 'albums',
                migrated=processed_count,
                last_id=batch_items[-1]['AlbumId']['N']
            )
        
        print(f"  ✓ Migrated {processed_count} albums")
        return True
    
    def _migrate_tracks(self, table_name, last_processed_id=None):
        """Migrate track records"""
        query = """
        SELECT t.TrackId, t.Name, t.AlbumId, t.MediaTypeId, t.GenreId,
               t.Composer, t.Milliseconds, t.Bytes, t.UnitPrice,
               al.Title as AlbumTitle, a.ArtistId, a.Name as ArtistName,
               g.Name as GenreName, mt.Name as MediaTypeName
        FROM Track t
        JOIN Album al ON t.AlbumId = al.AlbumId
        JOIN Artist a ON al.ArtistId = a.ArtistId
        LEFT JOIN Genre g ON t.GenreId = g.GenreId
        LEFT JOIN MediaType mt ON t.MediaTypeId = mt.MediaTypeId
        """
        
        if last_processed_id:
            query += f" WHERE t.TrackId > {last_processed_id}"
        
        query += " ORDER BY t.TrackId"
        
        cursor = self.sqlite_conn.execute(query)
        batch_items = []
        processed_count = 0
        
        for row in cursor:
            # Transform track data
            track_item = self.transformers.transform_track(dict(row))
            batch_items.append(track_item)
            
            # Batch write when limit reached
            if len(batch_items) >= self.config['batch_size']:
                if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                    return False
                
                processed_count += len(batch_items)
                self.state_manager.update_entity_progress(
                    'MusicCatalog', 'tracks',
                    migrated=processed_count,
                    last_id=row['TrackId']
                )
                batch_items = []
                print(f"  Migrated {processed_count} tracks...")
        
        # Write remaining items
        if batch_items:
            if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                return False
            processed_count += len(batch_items)
            self.state_manager.update_entity_progress(
                'MusicCatalog', 'tracks',
                migrated=processed_count,
                last_id=batch_items[-1]['TrackId']['N']
            )
        
        print(f"  ✓ Migrated {processed_count} tracks")
        return True
    
    def _migrate_customer_orders(self):
        """Migrate customer orders"""
        table_name = 'CustomerOrders'
        physical_table = self.config['target_tables'][table_name]
        
        # Get counts
        customer_count = self._get_table_count('Customer')
        order_count = self._get_table_count('Invoice')
        total_records = customer_count + order_count
        
        self.state_manager.start_table_migration(table_name, total_records)
        
        # Migrate customers with their orders
        return self._migrate_customers_with_orders(physical_table)
    
    def _migrate_customers_with_orders(self, table_name):
        """Migrate customers with embedded order data"""
        query = """
        SELECT c.CustomerId, c.FirstName, c.LastName, c.Company, c.Address,
               c.City, c.State, c.Country, c.PostalCode, c.Phone, c.Fax, c.Email,
               c.SupportRepId, e.FirstName as RepFirstName, e.LastName as RepLastName,
               i.InvoiceId, i.InvoiceDate, i.BillingAddress, i.BillingCity,
               i.BillingState, i.BillingCountry, i.BillingPostalCode, i.Total,
               il.InvoiceLineId, il.TrackId, il.UnitPrice, il.Quantity,
               t.Name as TrackName, a.Name as ArtistName, al.Title as AlbumTitle
        FROM Customer c
        LEFT JOIN Employee e ON c.SupportRepId = e.EmployeeId
        LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
        LEFT JOIN InvoiceLine il ON i.InvoiceId = il.InvoiceId
        LEFT JOIN Track t ON il.TrackId = t.TrackId
        LEFT JOIN Album al ON t.AlbumId = al.AlbumId
        LEFT JOIN Artist a ON al.ArtistId = a.ArtistId
        ORDER BY c.CustomerId, i.InvoiceDate, il.InvoiceLineId
        """
        
        cursor = self.sqlite_conn.execute(query)
        
        # Group data by customer
        customers_data = {}
        for row in cursor:
            customer_id = row['CustomerId']
            if customer_id not in customers_data:
                customers_data[customer_id] = {
                    'profile': dict(row),
                    'orders': {}
                }
            
            if row['InvoiceId']:
                invoice_id = row['InvoiceId']
                if invoice_id not in customers_data[customer_id]['orders']:
                    customers_data[customer_id]['orders'][invoice_id] = {
                        'invoice_data': dict(row),
                        'line_items': []
                    }
                
                if row['InvoiceLineId']:
                    customers_data[customer_id]['orders'][invoice_id]['line_items'].append(dict(row))
        
        # Transform and write customer data
        batch_items = []
        processed_count = 0
        
        for customer_id, customer_data in customers_data.items():
            # Create customer profile item
            profile_item = self.transformers.transform_customer_profile(
                customer_data['profile'], customer_data['orders']
            )
            batch_items.append(profile_item)
            
            # Create order items
            for order_data in customer_data['orders'].values():
                order_item = self.transformers.transform_customer_order(
                    customer_id, order_data
                )
                batch_items.append(order_item)
            
            # Batch write when limit reached
            if len(batch_items) >= self.config['batch_size']:
                if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                    return False
                
                processed_count += len(batch_items)
                self.state_manager.update_table_progress(
                    'CustomerOrders', processed_count, customer_id
                )
                batch_items = []
                print(f"  Migrated {processed_count} customer/order records...")
        
        # Write remaining items
        if batch_items:
            if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                return False
            processed_count += len(batch_items)
            self.state_manager.update_table_progress(
                'CustomerOrders', processed_count
            )
        
        print(f"  ✓ Migrated {processed_count} customer/order records")
        return True
    
    def _migrate_playlists(self):
        """Migrate playlists"""
        table_name = 'Playlists'
        physical_table = self.config['target_tables'][table_name]
        
        playlist_count = self._get_table_count('Playlist')
        self.state_manager.start_table_migration(table_name, playlist_count)
        
        return self._migrate_playlist_data(physical_table)
    
    def _migrate_playlist_data(self, table_name):
        """Migrate playlist data with embedded tracks"""
        query = """
        SELECT p.PlaylistId, p.Name as PlaylistName,
               pt.TrackId, t.Name as TrackName, t.Milliseconds, t.UnitPrice,
               a.Name as ArtistName, al.Title as AlbumTitle
        FROM Playlist p
        LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId
        LEFT JOIN Track t ON pt.TrackId = t.TrackId
        LEFT JOIN Album al ON t.AlbumId = al.AlbumId
        LEFT JOIN Artist a ON al.ArtistId = a.ArtistId
        ORDER BY p.PlaylistId, t.Name
        """
        
        cursor = self.sqlite_conn.execute(query)
        
        # Group by playlist
        playlists_data = {}
        for row in cursor:
            playlist_id = row['PlaylistId']
            if playlist_id not in playlists_data:
                playlists_data[playlist_id] = {
                    'playlist_info': dict(row),
                    'tracks': []
                }
            
            if row['TrackId']:
                playlists_data[playlist_id]['tracks'].append(dict(row))
        
        # Transform and write playlist data
        batch_items = []
        processed_count = 0
        
        for playlist_data in playlists_data.values():
            playlist_item = self.transformers.transform_playlist(playlist_data)
            batch_items.append(playlist_item)
            
            if len(batch_items) >= self.config['batch_size']:
                if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                    return False
                
                processed_count += len(batch_items)
                self.state_manager.update_table_progress('Playlists', processed_count)
                batch_items = []
                print(f"  Migrated {processed_count} playlists...")
        
        # Write remaining items
        if batch_items:
            if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                return False
            processed_count += len(batch_items)
            self.state_manager.update_table_progress('Playlists', processed_count)
        
        print(f"  ✓ Migrated {processed_count} playlists")
        return True
    
    def _migrate_employee_management(self):
        """Migrate employee management data"""
        table_name = 'EmployeeManagement'
        physical_table = self.config['target_tables'][table_name]
        
        employee_count = self._get_table_count('Employee')
        self.state_manager.start_table_migration(table_name, employee_count)
        
        return self._migrate_employee_data(physical_table)
    
    def _migrate_employee_data(self, table_name):
        """Migrate employee data"""
        query = """
        SELECT e.EmployeeId, e.LastName, e.FirstName, e.Title, e.ReportsTo,
               e.BirthDate, e.HireDate, e.Address, e.City, e.State, e.Country,
               e.PostalCode, e.Phone, e.Fax, e.Email,
               m.FirstName as ManagerFirstName, m.LastName as ManagerLastName,
               COUNT(c.CustomerId) as CustomerCount
        FROM Employee e
        LEFT JOIN Employee m ON e.ReportsTo = m.EmployeeId
        LEFT JOIN Customer c ON e.EmployeeId = c.SupportRepId
        GROUP BY e.EmployeeId
        ORDER BY e.EmployeeId
        """
        
        cursor = self.sqlite_conn.execute(query)
        batch_items = []
        processed_count = 0
        
        for row in cursor:
            employee_item = self.transformers.transform_employee(dict(row))
            batch_items.append(employee_item)
            
            if len(batch_items) >= self.config['batch_size']:
                if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                    return False
                
                processed_count += len(batch_items)
                self.state_manager.update_table_progress('EmployeeManagement', processed_count)
                batch_items = []
                print(f"  Migrated {processed_count} employees...")
        
        # Write remaining items
        if batch_items:
            if not self.dynamodb_manager.batch_write_items(table_name, batch_items):
                return False
            processed_count += len(batch_items)
            self.state_manager.update_table_progress('EmployeeManagement', processed_count)
        
        print(f"  ✓ Migrated {processed_count} employees")
        return True
    
    def _get_music_catalog_counts(self):
        """Get record counts for music catalog entities"""
        counts = {}
        for entity in ['Artist', 'Album', 'Track']:
            cursor = self.sqlite_conn.execute(f"SELECT COUNT(*) FROM {entity}")
            counts[entity.lower() + 's'] = cursor.fetchone()[0]
        return counts
    
    def _get_table_count(self, table_name):
        """Get record count for a table"""
        cursor = self.sqlite_conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def validate_migration(self):
        """Validate the migrated data"""
        print("Validating migration...")
        
        validation_results = {}
        
        for logical_name, physical_name in self.config['target_tables'].items():
            print(f"Validating {logical_name}...")
            
            # Get source counts
            source_count = self._get_source_count_for_table(logical_name)
            
            # Get target count
            target_count = self.dynamodb_manager.get_table_item_count(physical_name)
            
            validation_results[logical_name] = {
                'source_count': source_count,
                'target_count': target_count,
                'count_match': source_count == target_count
            }
        
        return validation_results
    
    def _get_source_count_for_table(self, logical_name):
        """Get source record count for logical table"""
        if logical_name == 'MusicCatalog':
            counts = self._get_music_catalog_counts()
            return sum(counts.values())
        elif logical_name == 'CustomerOrders':
            customer_count = self._get_table_count('Customer')
            order_count = self._get_table_count('Invoice')
            return customer_count + order_count
        elif logical_name == 'Playlists':
            return self._get_table_count('Playlist')
        elif logical_name == 'EmployeeManagement':
            return self._get_table_count('Employee')
        else:
            return 0


