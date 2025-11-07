#!/usr/bin/env python3
"""
SQLite Database Schema Analyzer and Documentation Generator
Analyzes the Chinook SQLite database and generates comprehensive documentation.
"""

import sqlite3
import json
from datetime import datetime
from collections import defaultdict

class DatabaseAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
    def get_tables(self):
        """Get all tables in the database"""
        self.cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name):
        """Get detailed schema information for a table"""
        # Get column information
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row['name'],
                'type': row['type'],
                'not_null': bool(row['notnull']),
                'default_value': row['dflt_value'],
                'primary_key': bool(row['pk'])
            })
        
        # Get foreign keys
        self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = []
        for row in self.cursor.fetchall():
            foreign_keys.append({
                'column': row['from'],
                'references_table': row['table'],
                'references_column': row['to']
            })
        
        # Get indexes
        self.cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = []
        for row in self.cursor.fetchall():
            index_name = row['name']
            self.cursor.execute(f"PRAGMA index_info({index_name})")
            index_columns = [col['name'] for col in self.cursor.fetchall()]
            indexes.append({
                'name': index_name,
                'unique': bool(row['unique']),
                'columns': index_columns
            })
        
        return {
            'columns': columns,
            'foreign_keys': foreign_keys,
            'indexes': indexes
        }
    
    def get_table_statistics(self, table_name):
        """Get statistics for a table"""
        # Row count
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = self.cursor.fetchone()[0]
        
        # Get column statistics
        schema = self.get_table_schema(table_name)
        column_stats = {}
        
        for column in schema['columns']:
            col_name = column['name']
            col_type = column['type'].upper()
            
            # Basic stats for all columns
            self.cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")
            distinct_count = self.cursor.fetchone()[0]
            
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL")
            null_count = self.cursor.fetchone()[0]
            
            stats = {
                'distinct_values': distinct_count,
                'null_count': null_count,
                'null_percentage': (null_count / row_count * 100) if row_count > 0 else 0
            }
            
            # Additional stats for numeric columns
            if any(t in col_type for t in ['INT', 'REAL', 'NUMERIC', 'DECIMAL']):
                try:
                    self.cursor.execute(f"SELECT MIN({col_name}), MAX({col_name}), AVG({col_name}) FROM {table_name} WHERE {col_name} IS NOT NULL")
                    min_val, max_val, avg_val = self.cursor.fetchone()
                    stats.update({
                        'min_value': min_val,
                        'max_value': max_val,
                        'average_value': round(avg_val, 2) if avg_val else None
                    })
                except:
                    pass
            
            # Additional stats for text columns
            elif 'TEXT' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
                try:
                    self.cursor.execute(f"SELECT MIN(LENGTH({col_name})), MAX(LENGTH({col_name})), AVG(LENGTH({col_name})) FROM {table_name} WHERE {col_name} IS NOT NULL")
                    min_len, max_len, avg_len = self.cursor.fetchone()
                    stats.update({
                        'min_length': min_len,
                        'max_length': max_len,
                        'average_length': round(avg_len, 2) if avg_len else None
                    })
                except:
                    pass
            
            column_stats[col_name] = stats
        
        return {
            'row_count': row_count,
            'column_statistics': column_stats
        }
    
    def get_database_overview(self):
        """Get overall database statistics"""
        tables = self.get_tables()
        total_rows = 0
        table_info = {}
        
        for table in tables:
            stats = self.get_table_statistics(table)
            total_rows += stats['row_count']
            table_info[table] = stats['row_count']
        
        # Get database file size
        import os
        file_size = os.path.getsize(self.db_path)
        
        return {
            'total_tables': len(tables),
            'total_rows': total_rows,
            'database_size_bytes': file_size,
            'database_size_mb': round(file_size / (1024 * 1024), 2),
            'tables': table_info
        }
    
    def generate_documentation(self):
        """Generate comprehensive database documentation"""
        print("Analyzing Chinook SQLite Database...")
        print("=" * 60)
        
        # Database overview
        overview = self.get_database_overview()
        print(f"\n📊 DATABASE OVERVIEW")
        print(f"Database File: {self.db_path}")
        print(f"File Size: {overview['database_size_mb']} MB ({overview['database_size_bytes']:,} bytes)")
        print(f"Total Tables: {overview['total_tables']}")
        print(f"Total Records: {overview['total_rows']:,}")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Table summary
        print(f"\n📋 TABLE SUMMARY")
        print(f"{'Table Name':<20} {'Row Count':<15} {'Percentage':<12}")
        print("-" * 50)
        for table, count in sorted(overview['tables'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / overview['total_rows'] * 100) if overview['total_rows'] > 0 else 0
            print(f"{table:<20} {count:<15,} {percentage:<12.1f}%")
        
        # Detailed table analysis
        tables = self.get_tables()
        for table_name in sorted(tables):
            print(f"\n" + "=" * 60)
            print(f"🗂️  TABLE: {table_name}")
            print("=" * 60)
            
            schema = self.get_table_schema(table_name)
            stats = self.get_table_statistics(table_name)
            
            print(f"\n📈 Table Statistics:")
            print(f"  • Total Rows: {stats['row_count']:,}")
            
            print(f"\n🏗️  Schema Information:")
            print(f"{'Column':<20} {'Type':<15} {'Null':<8} {'PK':<4} {'Default':<15}")
            print("-" * 70)
            
            for col in schema['columns']:
                null_ok = "Yes" if not col['not_null'] else "No"
                pk = "✓" if col['primary_key'] else ""
                default = str(col['default_value']) if col['default_value'] else ""
                print(f"{col['name']:<20} {col['type']:<15} {null_ok:<8} {pk:<4} {default:<15}")
            
            # Foreign Keys
            if schema['foreign_keys']:
                print(f"\n🔗 Foreign Keys:")
                for fk in schema['foreign_keys']:
                    print(f"  • {fk['column']} → {fk['references_table']}.{fk['references_column']}")
            
            # Indexes
            if schema['indexes']:
                print(f"\n📇 Indexes:")
                for idx in schema['indexes']:
                    unique_str = " (UNIQUE)" if idx['unique'] else ""
                    columns_str = ", ".join(idx['columns'])
                    print(f"  • {idx['name']}: {columns_str}{unique_str}")
            
            # Column Statistics
            print(f"\n📊 Column Statistics:")
            for col_name, col_stats in stats['column_statistics'].items():
                print(f"\n  {col_name}:")
                print(f"    • Distinct Values: {col_stats['distinct_values']:,}")
                print(f"    • Null Values: {col_stats['null_count']:,} ({col_stats['null_percentage']:.1f}%)")
                
                if 'min_value' in col_stats:
                    print(f"    • Range: {col_stats['min_value']} - {col_stats['max_value']}")
                    if col_stats['average_value'] is not None:
                        print(f"    • Average: {col_stats['average_value']}")
                
                if 'min_length' in col_stats:
                    print(f"    • Length Range: {col_stats['min_length']} - {col_stats['max_length']} chars")
                    if col_stats['average_length'] is not None:
                        print(f"    • Average Length: {col_stats['average_length']} chars")
        
        # Relationships overview
        print(f"\n" + "=" * 60)
        print(f"🔗 DATABASE RELATIONSHIPS")
        print("=" * 60)
        
        all_relationships = []
        for table_name in tables:
            schema = self.get_table_schema(table_name)
            for fk in schema['foreign_keys']:
                all_relationships.append(f"{table_name}.{fk['column']} → {fk['references_table']}.{fk['references_column']}")
        
        if all_relationships:
            for rel in sorted(all_relationships):
                print(f"  • {rel}")
        else:
            print("  No foreign key relationships found.")
        
        print(f"\n" + "=" * 60)
        print("✅ Analysis Complete!")
        print("=" * 60)
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    db_path = "Chinook_Sqlite.sqlite"
    analyzer = DatabaseAnalyzer(db_path)
    
    try:
        analyzer.generate_documentation()
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
