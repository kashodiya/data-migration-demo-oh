#!/usr/bin/env python3
"""
Test script to verify SQLite database connectivity and data extraction
"""

import sqlite3
import sys
from pathlib import Path

def test_sqlite_connection():
    """Test SQLite database connection and basic queries"""
    db_path = "../Chinook_Sqlite.sqlite"
    
    if not Path(db_path).exists():
        print(f"Error: Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("✓ SQLite connection successful")
        
        # Test basic table counts
        tables = ['Artist', 'Album', 'Track', 'Customer', 'Invoice', 'Playlist', 'Employee']
        
        print("\nTable Record Counts:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"  {table}: {count:,} records")
        
        # Test sample data extraction for MusicCatalog
        print("\nSample Artist Data:")
        cursor.execute("""
            SELECT a.ArtistId, a.Name,
                   COUNT(DISTINCT al.AlbumId) as AlbumCount,
                   COUNT(DISTINCT t.TrackId) as TrackCount
            FROM Artist a
            LEFT JOIN Album al ON a.ArtistId = al.ArtistId
            LEFT JOIN Track t ON al.AlbumId = t.AlbumId
            GROUP BY a.ArtistId, a.Name
            ORDER BY a.ArtistId
            LIMIT 3
        """)
        
        for row in cursor.fetchall():
            print(f"  Artist {row['ArtistId']}: {row['Name']} ({row['AlbumCount']} albums, {row['TrackCount']} tracks)")
        
        # Test sample customer data
        print("\nSample Customer Data:")
        cursor.execute("""
            SELECT c.CustomerId, c.FirstName, c.LastName, c.Email,
                   COUNT(i.InvoiceId) as OrderCount
            FROM Customer c
            LEFT JOIN Invoice i ON c.CustomerId = i.CustomerId
            GROUP BY c.CustomerId, c.FirstName, c.LastName, c.Email
            ORDER BY c.CustomerId
            LIMIT 3
        """)
        
        for row in cursor.fetchall():
            print(f"  Customer {row['CustomerId']}: {row['FirstName']} {row['LastName']} ({row['Email']}) - {row['OrderCount']} orders")
        
        conn.close()
        print("\n✓ Database connectivity test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Database connectivity test failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_sqlite_connection()
    sys.exit(0 if success else 1)
