
# Chinook Database Migration Tool

A CLI tool for migrating the Chinook SQLite database to AWS DynamoDB with support for incremental migration and resume functionality.

## Features

- **Incremental Migration**: Tracks progress and allows resuming interrupted migrations
- **File-based Control**: Simple JSON-based state management for migration tracking
- **AWS Integration**: Automatically creates DynamoDB tables with proper schemas
- **Data Transformation**: Converts normalized SQLite data to optimized NoSQL format
- **Validation**: Validates migrated data against source database
- **Error Handling**: Comprehensive error handling with retry logic

## Architecture

The tool migrates data from the normalized Chinook SQLite database to four optimized DynamoDB tables:

1. **MusicCatalog** - Complete music hierarchy (Artist → Album → Track)
2. **CustomerOrders** - Customer profiles and order history  
3. **Playlists** - Playlist management with embedded tracks
4. **EmployeeManagement** - Staff hierarchy and customer assignments

## Prerequisites

- Python 3.7+
- AWS CLI configured with appropriate permissions
- EC2 instance with IAM roles for DynamoDB access (when running on EC2)
- Source SQLite database (Chinook_Sqlite.sqlite)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure AWS credentials are configured:
```bash
aws configure
# OR use IAM roles when running on EC2
```

## Usage

### Initialize Migration

```bash
python migrate.py init --source ../Chinook_Sqlite.sqlite
```

Options:
- `--source`: Path to source SQLite database (required)
- `--region`: AWS region (default: us-east-1)
- `--batch-size`: DynamoDB batch size (default: 25)

### Run Migration

```bash
# Full migration
python migrate.py migrate --source ../Chinook_Sqlite.sqlite

# Force migration (recreate tables)
python migrate.py migrate --force

# Migrate specific table only
python migrate.py migrate --table MusicCatalog
```

### Resume Interrupted Migration

```bash
python migrate.py resume
```

### Check Migration Status

```bash
python migrate.py status
```

### Validate Migration

```bash
python migrate.py validate --source ../Chinook_Sqlite.sqlite
```

### Reset Migration State

```bash
python migrate.py reset --confirm
```

## Configuration

The tool creates a `migration_config.json` file with the following structure:

```json
{
  "source_db": "/path/to/Chinook_Sqlite.sqlite",
  "aws_region": "us-east-1",
  "batch_size": 25,
  "target_tables": {
    "MusicCatalog": "chinook-music-catalog",
    "CustomerOrders": "chinook-customer-orders",
    "Playlists": "chinook-playlists",
    "EmployeeManagement": "chinook-employee-management"
  }
}
```

## State Management

Migration progress is tracked in `migration_state.json`:

```json
{
  "status": "in_progress",
  "start_time": "2025-11-07T10:30:00",
  "tables": {
    "MusicCatalog": {
      "status": "completed",
      "total_records": 4125,
      "records_migrated": 4125,
      "entities": {
        "artists": {"total": 275, "migrated": 275, "last_id": 275},
        "albums": {"total": 347, "migrated": 347, "last_id": 347},
        "tracks": {"total": 3503, "migrated": 3503, "last_id": 3503}
      }
    }
  }
}
```

## DynamoDB Schema

### MusicCatalog Table

- **Primary Key**: PK (Artist/Album ID), SK (Entity type/ID)
- **GSI1**: Name-based search (GSI1PK, GSI1SK)
- **GSI2**: Genre-based search (GSI2PK)

Key Patterns:
- Artists: `PK="ARTIST#1"`, `SK="METADATA"`
- Albums: `PK="ARTIST#1"`, `SK="ALBUM#1"`
- Tracks: `PK="ALBUM#1"`, `SK="TRACK#1"`

### CustomerOrders Table

- **Primary Key**: PK (Customer ID), SK (Profile/Order timestamp)
- **GSI1**: Email-based search (GSI1PK, GSI1SK)

Key Patterns:
- Customer Profile: `PK="CUSTOMER#1"`, `SK="PROFILE"`
- Orders: `PK="CUSTOMER#1"`, `SK="ORDER#2021-01-01T00:00:00Z"`

### Playlists Table

- **Primary Key**: PK (Playlist ID), SK (Metadata)

Key Patterns:
- Playlist: `PK="PLAYLIST#1"`, `SK="METADATA"`

### EmployeeManagement Table

- **Primary Key**: PK (Employee ID), SK (Profile)

Key Patterns:
- Employee: `PK="EMPLOYEE#1"`, `SK="PROFILE"`

## Error Handling

The tool includes comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **Throttling**: Built-in retry logic for DynamoDB throttling
- **Data Validation**: Validates data integrity during transformation
- **State Recovery**: Can resume from any point of failure

## Monitoring

Monitor migration progress:

```bash
# Check overall status
python migrate.py status

# View detailed logs
tail -f migration.log  # If logging is enabled
```

## Troubleshooting

### Common Issues

1. **AWS Permissions**: Ensure IAM user/role has DynamoDB permissions
2. **Table Exists**: Use `--force` flag to recreate existing tables
3. **Large Items**: Tool automatically handles DynamoDB item size limits
4. **Network Issues**: Built-in retry logic handles temporary network issues

### Recovery

If migration fails:

1. Check the error in migration state: `python migrate.py status`
2. Fix the underlying issue (permissions, network, etc.)
3. Resume migration: `python migrate.py resume`

### Reset and Restart

To completely restart migration:

```bash
python migrate.py reset --confirm
python migrate.py migrate --force
```

## Performance

- **Batch Size**: Configurable batch size (default: 25 items)
- **Parallel Processing**: Single-threaded for data consistency
- **Memory Usage**: Processes data in batches to minimize memory usage
- **Network Optimization**: Uses batch operations to minimize API calls

## Security

- Uses AWS IAM for authentication and authorization
- No hardcoded credentials in configuration files
- Supports both IAM users and EC2 instance roles
- Data is encrypted in transit and at rest (DynamoDB default)

## License

This tool is provided as-is for demonstration purposes.

