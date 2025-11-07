#!/usr/bin/env python3
"""
Chinook Database Migration Tool
Supports incremental migration from SQLite to DynamoDB
"""

import argparse
import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from migration_engine import MigrationEngine
from config_manager import ConfigManager
from migration_state import MigrationState


def main():
    parser = argparse.ArgumentParser(
        description='Chinook Database Migration Tool - SQLite to DynamoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize migration with default settings
  python migrate.py init --source ../Chinook_Sqlite.sqlite

  # Run full migration
  python migrate.py migrate --source ../Chinook_Sqlite.sqlite

  # Resume interrupted migration
  python migrate.py resume

  # Check migration status
  python migrate.py status

  # Validate migrated data
  python migrate.py validate --source ../Chinook_Sqlite.sqlite
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize migration configuration')
    init_parser.add_argument('--source', required=True, help='Path to source SQLite database')
    init_parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    init_parser.add_argument('--batch-size', type=int, default=25, help='DynamoDB batch size (default: 25)')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Start migration process')
    migrate_parser.add_argument('--source', help='Path to source SQLite database')
    migrate_parser.add_argument('--force', action='store_true', help='Force migration even if tables exist')
    migrate_parser.add_argument('--table', help='Migrate specific table only')
    
    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume interrupted migration')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate migrated data')
    validate_parser.add_argument('--source', required=True, help='Path to source SQLite database')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset migration state')
    reset_parser.add_argument('--confirm', action='store_true', help='Confirm reset operation')
    reset_parser.add_argument('--force', action='store_true', help='Force reset without confirmation')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Initialize configuration and state managers
        config_manager = ConfigManager()
        state_manager = MigrationState()
        
        if args.command == 'init':
            return handle_init(args, config_manager, state_manager)
        elif args.command == 'migrate':
            return handle_migrate(args, config_manager, state_manager)
        elif args.command == 'resume':
            return handle_resume(config_manager, state_manager)
        elif args.command == 'status':
            return handle_status(state_manager)
        elif args.command == 'validate':
            return handle_validate(args, config_manager, state_manager)
        elif args.command == 'reset':
            return handle_reset(args, state_manager)
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def handle_init(args, config_manager, state_manager):
    """Initialize migration configuration"""
    print("Initializing migration configuration...")
    
    # Validate source database
    if not os.path.exists(args.source):
        print(f"Error: Source database not found: {args.source}")
        return 1
    
    # Create configuration
    config = {
        'source_db': os.path.abspath(args.source),
        'aws_region': args.region,
        'batch_size': args.batch_size,
        'target_tables': {
            'MusicCatalog': 'chinook-music-catalog',
            'CustomerOrders': 'chinook-customer-orders', 
            'Playlists': 'chinook-playlists',
            'EmployeeManagement': 'chinook-employee-management'
        }
    }
    
    config_manager.save_config(config)
    state_manager.initialize()
    
    print("Migration configuration initialized successfully!")
    print(f"Source database: {config['source_db']}")
    print(f"AWS region: {config['aws_region']}")
    print(f"Batch size: {config['batch_size']}")
    
    return 0


def handle_migrate(args, config_manager, state_manager):
    """Start migration process"""
    print("Starting migration process...")
    
    # Load configuration
    config = config_manager.load_config()
    if not config:
        print("Error: No configuration found. Run 'init' command first.")
        return 1
    
    # Override source if provided
    if args.source:
        config['source_db'] = os.path.abspath(args.source)
    
    # Validate source database
    if not os.path.exists(config['source_db']):
        print(f"Error: Source database not found: {config['source_db']}")
        return 1
    
    # Initialize migration engine
    engine = MigrationEngine(config, state_manager)
    
    # Run migration
    success = engine.run_migration(
        force=args.force,
        specific_table=args.table
    )
    
    if success:
        print("Migration completed successfully!")
        return 0
    else:
        print("Migration failed. Check logs for details.")
        return 1


def handle_resume(config_manager, state_manager):
    """Resume interrupted migration"""
    print("Resuming migration...")
    
    # Load configuration
    config = config_manager.load_config()
    if not config:
        print("Error: No configuration found. Run 'init' command first.")
        return 1
    
    # Check if there's a migration to resume
    state = state_manager.get_state()
    if state['status'] == 'completed':
        print("No migration to resume. Migration already completed.")
        return 0
    
    if state['status'] == 'not_started':
        print("No migration to resume. Run 'migrate' command to start.")
        return 1
    
    # Initialize migration engine and resume
    engine = MigrationEngine(config, state_manager)
    success = engine.resume_migration()
    
    if success:
        print("Migration resumed and completed successfully!")
        return 0
    else:
        print("Migration resume failed. Check logs for details.")
        return 1


def handle_status(state_manager):
    """Show migration status"""
    state = state_manager.get_state()
    
    print("Migration Status:")
    print(f"  Overall Status: {state['status']}")
    print(f"  Started: {state.get('start_time', 'Not started')}")
    print(f"  Last Updated: {state.get('last_update', 'Never')}")
    
    if 'tables' in state:
        print("\nTable Progress:")
        for table_name, table_state in state['tables'].items():
            status = table_state.get('status', 'not_started')
            records = table_state.get('records_migrated', 0)
            total = table_state.get('total_records', 0)
            
            if total > 0:
                percentage = (records / total) * 100
                print(f"  {table_name}: {status} ({records}/{total} records, {percentage:.1f}%)")
            else:
                print(f"  {table_name}: {status}")
    
    return 0


def handle_validate(args, config_manager, state_manager):
    """Validate migrated data"""
    print("Validating migrated data...")
    
    # Load configuration
    config = config_manager.load_config()
    if not config:
        print("Error: No configuration found. Run 'init' command first.")
        return 1
    
    # Override source if provided
    if args.source:
        config['source_db'] = os.path.abspath(args.source)
    
    # Initialize migration engine and validate
    engine = MigrationEngine(config, state_manager)
    validation_results = engine.validate_migration()
    
    print("\nValidation Results:")
    for table_name, results in validation_results.items():
        print(f"\n{table_name}:")
        print(f"  Record count match: {'✓' if results['count_match'] else '✗'}")
        print(f"  Source records: {results['source_count']}")
        print(f"  Target records: {results['target_count']}")
        
        if 'sample_validation' in results:
            sample_results = results['sample_validation']
            print(f"  Sample validation: {'✓' if sample_results['passed'] else '✗'}")
            if not sample_results['passed']:
                print(f"    Issues: {sample_results['issues']}")
    
    return 0


def handle_reset(args, state_manager):
    """Reset migration state"""
    if not args.confirm and not args.force:
        print("Warning: This will reset all migration progress.")
        print("Use --confirm or --force flag to proceed.")
        return 1
    
    state_manager.reset()
    print("Migration state reset successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
