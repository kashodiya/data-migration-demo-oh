
#!/usr/bin/env python3
"""
Demo Migration Script
Demonstrates the migration tool functionality without requiring AWS credentials
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_transformers import DataTransformers
from migration_state import MigrationState
from config_manager import ConfigManager


class DemoMigration:
    """Demo migration that shows data transformation without AWS"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.state_manager = MigrationState()
        self.transformers = DataTransformers()
        self.sqlite_conn = None
    
    def run_demo(self):
        """Run the migration demo"""
        print("🚀 Chinook Database Migration Tool Demo")
        print("=" * 50)
        
        # Load configuration
        config = self.config_manager.load_config()
        if not config:
            print("❌ No configuration found. Please run 'python migrate.py init' first.")
            return False
        
        print(f"📁 Source Database: {config['source_db']}")
        print(f"🌍 AWS Region: {config['aws_region']}")
        print(f"📦 Batch Size: {config['batch_size']}")
        
        # Connect to SQLite
        try:
            self.sqlite_conn = sqlite3.connect(config['source_db'])
            self.sqlite_conn.row_factory = sqlite3.Row
            print("✅ Connected to SQLite database")
        except Exception as e:
            print(f"❌ Failed to connect to database: {str(e)}")
            return False
        
        # Demo each table transformation
        print("\n🔄 Demonstrating Data Transformations:")
        print("-" * 40)
        
        self._demo_music_catalog()
        self._demo_customer_orders()
        self._demo_playlists()
        self._demo_employee_management()
        
        # Show migration state tracking
        self._demo_state_tracking()
        
        print("\n✅ Demo completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Configure AWS credentials (aws configure or IAM roles)")
        print("2. Run: python migrate.py migrate --source ../Chinook_Sqlite.sqlite")
        print("3. Monitor progress: python migrate.py status")
        print("4. Validate results: python migrate.py validate --source ../Chinook_Sqlite.sqlite")
        
        return True
    
    def _demo_music_catalog(self):
        """Demo MusicCatalog transformation"""
        print("\n🎵 MusicCatalog Transformation:")
        
        # Get sample artist data
        cursor = self.sqlite_conn.execute("""
            SELECT a.ArtistId, a.Name,
                   COUNT(DISTINCT al.AlbumId) as AlbumCount,
                   COUNT(DISTINCT t.TrackId) as TrackCount
            FROM Artist a
            LEFT JOIN Album al ON a.ArtistId = al.ArtistId
            LEFT JOIN Track t ON al.AlbumId = t.AlbumId
            WHERE a.ArtistId = 1
            GROUP BY a.ArtistId, a.Name
        """)
        
        artist_data = dict(cursor.fetchone())
        artist_item = self.transformers.transform_artist(artist_data)
        
        print(f"  📊 Source: Artist '{artist_data['Name']}' (ID: {artist_data['ArtistId']})")
        print(f"  🔄 Target: PK='{artist_item['PK']['S']}', SK='{artist_item['SK']['S']}'")
        print(f"  📈 Albums: {artist_item['AlbumCount']['N']}, Tracks: {artist_item['TrackCount']['N']}")
        
        # Get sample track data
        cursor = self.sqlite_conn.execute("""
            SELECT t.TrackId, t.Name, t.AlbumId, t.UnitPrice,
                   al.Title as AlbumTitle, a.ArtistId, a.Name as ArtistName,
                   g.Name as GenreName, mt.Name as MediaTypeName
            FROM Track t
            JOIN Album al ON t.AlbumId = al.AlbumId
            JOIN Artist a ON al.ArtistId = a.ArtistId
            LEFT JOIN Genre g ON t.GenreId = g.GenreId
            LEFT JOIN MediaType mt ON t.MediaTypeId = mt.MediaTypeId
            WHERE t.TrackId = 1
        """)
        
        track_data = dict(cursor.fetchone())
        track_item = self.transformers.transform_track(track_data)
        
        print(f"  📊 Source: Track '{track_data['Name']}' (${track_data['UnitPrice']})")
        print(f"  🔄 Target: PK='{track_item['PK']['S']}', SK='{track_item['SK']['S']}'")
        print(f"  🎼 Genre: {track_item.get('GenreName', {}).get('S', 'N/A')}")
    
    def _demo_customer_orders(self):
        """Demo CustomerOrders transformation"""
        print("\n👥 CustomerOrders Transformation:")
        
        # Get sample customer with orders
        cursor = self.sqlite_conn.execute("""
            SELECT c.CustomerId, c.FirstName, c.LastName, c.Email, c.Country, c.City,
                   c.Company, c.Address, c.State, c.PostalCode, c.Phone, c.Fax, c.SupportRepId,
                   COUNT(i.InvoiceId) as OrderCount,
                   COALESCE(SUM(i.Total), 0) as TotalSpent
            FROM Customer c
            LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
            WHERE c.CustomerId = 1
            GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Email, c.Country, c.City,
                     c.Company, c.Address, c.State, c.PostalCode, c.Phone, c.Fax, c.SupportRepId
        """)
        
        customer_data = dict(cursor.fetchone())
        
        # Get orders for this customer
        cursor = self.sqlite_conn.execute("""
            SELECT InvoiceId, InvoiceDate, Total
            FROM Invoice
            WHERE CustomerId = 1
            ORDER BY InvoiceDate
            LIMIT 3
        """)
        
        orders_data = {}
        for row in cursor.fetchall():
            orders_data[row['InvoiceId']] = {
                'invoice_data': dict(row),
                'line_items': []
            }
        
        customer_item = self.transformers.transform_customer_profile(customer_data, orders_data)
        
        print(f"  📊 Source: {customer_data['FirstName']} {customer_data['LastName']} ({customer_data['Email']})")
        print(f"  🔄 Target: PK='{customer_item['PK']['S']}', SK='{customer_item['SK']['S']}'")
        print(f"  💰 Orders: {customer_item['TotalOrders']['N']}, Spent: ${customer_item['TotalSpent']['N']}")
    
    def _demo_playlists(self):
        """Demo Playlists transformation"""
        print("\n🎶 Playlists Transformation:")
        
        # Get sample playlist
        cursor = self.sqlite_conn.execute("""
            SELECT p.PlaylistId, p.Name as PlaylistName,
                   COUNT(pt.TrackId) as TrackCount
            FROM Playlist p
            LEFT JOIN PlaylistTrack pt ON p.PlaylistId = pt.PlaylistId
            WHERE p.PlaylistId = 1
            GROUP BY p.PlaylistId, p.Name
        """)
        
        playlist_info = dict(cursor.fetchone())
        
        # Get sample tracks
        cursor = self.sqlite_conn.execute("""
            SELECT pt.TrackId, t.Name as TrackName, t.Milliseconds, t.UnitPrice,
                   a.Name as ArtistName, al.Title as AlbumTitle
            FROM PlaylistTrack pt
            JOIN Track t ON pt.TrackId = t.TrackId
            JOIN Album al ON t.AlbumId = al.AlbumId
            JOIN Artist a ON al.ArtistId = a.ArtistId
            WHERE pt.PlaylistId = 1
            LIMIT 5
        """)
        
        tracks = [dict(row) for row in cursor.fetchall()]
        
        playlist_data = {
            'playlist_info': playlist_info,
            'tracks': tracks
        }
        
        playlist_item = self.transformers.transform_playlist(playlist_data)
        
        print(f"  📊 Source: Playlist '{playlist_info['PlaylistName']}' ({playlist_info['TrackCount']} tracks)")
        print(f"  🔄 Target: PK='{playlist_item['PK']['S']}', SK='{playlist_item['SK']['S']}'")
        print(f"  🎵 Sample tracks: {len(tracks)} embedded")
    
    def _demo_employee_management(self):
        """Demo EmployeeManagement transformation"""
        print("\n👔 EmployeeManagement Transformation:")
        
        # Get sample employee
        cursor = self.sqlite_conn.execute("""
            SELECT e.EmployeeId, e.FirstName, e.LastName, e.Title,
                   e.ReportsTo, m.FirstName as ManagerFirstName, m.LastName as ManagerLastName,
                   COUNT(c.CustomerId) as CustomerCount
            FROM Employee e
            LEFT JOIN Employee m ON e.ReportsTo = m.EmployeeId
            LEFT JOIN Customer c ON e.EmployeeId = c.SupportRepId
            WHERE e.EmployeeId = 1
            GROUP BY e.EmployeeId
        """)
        
        employee_data = dict(cursor.fetchone())
        employee_item = self.transformers.transform_employee(employee_data)
        
        print(f"  📊 Source: {employee_data['FirstName']} {employee_data['LastName']} ({employee_data['Title']})")
        print(f"  🔄 Target: PK='{employee_item['PK']['S']}', SK='{employee_item['SK']['S']}'")
        print(f"  👥 Customers: {employee_item['CustomerCount']['N']}")
    
    def _demo_state_tracking(self):
        """Demo migration state tracking"""
        print("\n📊 Migration State Tracking Demo:")
        
        # Simulate starting migration
        self.state_manager.start_migration()
        
        # Simulate table progress
        self.state_manager.start_table_migration('MusicCatalog', 4125)
        self.state_manager.update_entity_progress('MusicCatalog', 'artists', total=275, migrated=100, last_id=100)
        self.state_manager.update_entity_progress('MusicCatalog', 'albums', total=347, migrated=200, last_id=200)
        
        # Show current state
        state = self.state_manager.get_state()
        summary = self.state_manager.get_migration_summary()
        
        print(f"  📈 Overall Status: {summary['overall_status']}")
        print(f"  📊 Progress: {summary['migrated_records']}/{summary['total_records']} records")
        print(f"  🎯 Completion: {summary['progress_percentage']:.1f}%")
        print(f"  📅 Started: {summary['start_time']}")
        
        # Reset state for clean demo
        self.state_manager.reset()


def main():
    """Main demo function"""
    demo = DemoMigration()
    success = demo.run_demo()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

