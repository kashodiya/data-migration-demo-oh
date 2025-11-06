
# Data Migration Architecture

## Overview
This document describes the chosen architecture for migrating data from on-premises MySQL to AWS Aurora PostgreSQL. The solution implements a custom Python ETL pipeline designed for incremental data migration during a 6-month parallel operation period.

## Architecture: Custom Python ETL Pipeline

### Solution Overview
A custom ETL pipeline built in Python that provides complete control over the migration process while maintaining simplicity and cost-effectiveness. The solution runs weekly incremental migrations to keep the cloud database synchronized with on-premises data.

### Core Components

#### 1. Python ETL Application
- **Technology**: Python 3.8+ with SQLAlchemy and Pandas
- **Purpose**: Core migration logic handling extraction, transformation, and loading
- **Features**:
  - Database connectivity management
  - Change detection and incremental processing
  - Schema mapping between MySQL and PostgreSQL
  - Data type conversion and validation
  - Error handling and recovery mechanisms

#### 2. Virtual Environment
- **Technology**: Python venv or virtualenv
- **Purpose**: Isolated dependency management
- **Benefits**:
  - Prevents dependency conflicts
  - Ensures consistent execution environment
  - Easy deployment across different systems

#### 3. PostgreSQL Staging Area
- **Technology**: Temporary tables in Aurora PostgreSQL
- **Purpose**: Data validation and integrity checks
- **Features**:
  - Staging tables for each source table
  - Data comparison and validation queries
  - Rollback capability for failed migrations

#### 4. Cron Job Scheduling
- **Technology**: Unix/Linux cron daemon
- **Purpose**: Automated weekly execution
- **Configuration**: Runs every Sunday at 2:00 AM
- **Command**: `/path/to/venv/bin/python /path/to/migration/main.py`

#### 5. SQLite State Management
- **Technology**: SQLite database
- **Purpose**: Track migration state and metadata
- **Data Stored**:
  - Last migration timestamps per table
  - Migration job history and status
  - Error logs and retry counts
  - Data validation results

#### 6. File-based Logging
- **Technology**: Python logging module
- **Purpose**: Monitoring and troubleshooting
- **Features**:
  - Structured log files with rotation
  - Different log levels (INFO, WARNING, ERROR)
  - Migration metrics and performance data
  - Email alerts for critical errors

### Architecture Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   MySQL         │    │  Python ETL      │    │  Aurora PostgreSQL  │
│   (On-premises) │    │  Pipeline        │    │  (AWS Cloud)        │
│                 │    │                  │    │                     │
│  ┌─────────────┐│    │ ┌──────────────┐ │    │ ┌─────────────────┐ │
│  │ Source      ││────┤ │ Change       │ │    │ │ Staging Tables  │ │
│  │ Tables      ││    │ │ Detection    │ │    │ │                 │ │
│  └─────────────┘│    │ └──────────────┘ │    │ └─────────────────┘ │
│                 │    │ ┌──────────────┐ │    │ ┌─────────────────┐ │
│                 │    │ │ Data         │ │────┤ │ Target Tables   │ │
│                 │    │ │ Transform    │ │    │ │                 │ │
│                 │    │ └──────────────┘ │    │ └─────────────────┘ │
└─────────────────┘    │ ┌──────────────┐ │    └─────────────────────┘
                       │ │ SQLite       │ │
                       │ │ State DB     │ │
                       │ └──────────────┘ │
                       └──────────────────┘
```

### Detailed Migration Process

#### 1. Configuration Phase
- Load database connection parameters from environment variables
- Read table mapping configuration from YAML files
- Initialize logging and state management systems
- Validate connectivity to both source and target databases

#### 2. Change Detection Phase
- Query SQLite state database for last migration timestamp per table
- Execute incremental queries on MySQL using timestamp-based filtering
- Identify new, updated, and deleted records since last migration
- Handle tables without timestamp columns using full comparison

#### 3. Data Extraction Phase
- Extract changed records in configurable batch sizes (default: 1000 records)
- Handle large datasets with pagination to manage memory usage
- Apply data quality checks and filtering rules
- Log extraction metrics and any data anomalies

#### 4. Data Transformation Phase
- Convert MySQL data types to PostgreSQL equivalents
- Handle character encoding differences (latin1 to UTF-8)
- Apply business logic transformations as configured
- Validate transformed data against target schema constraints

#### 5. Data Loading Phase
- Create staging tables in Aurora PostgreSQL
- Load transformed data into staging tables
- Perform data validation and integrity checks
- Execute UPSERT operations to merge data into target tables
- Handle primary key conflicts and constraint violations

#### 6. State Management Phase
- Update migration timestamps in SQLite database
- Record migration statistics and performance metrics
- Log successful completion or error details
- Clean up temporary staging tables

#### 7. Validation Phase
- Compare record counts between source and target
- Execute data quality validation queries
- Generate migration summary report
- Send email notifications for success/failure

### Key Implementation Features

#### Incremental Migration Logic
```python
class IncrementalMigrator:
    def __init__(self, config):
        self.mysql_conn = self.create_mysql_connection(config)
        self.postgres_conn = self.create_postgres_connection(config)
        self.state_db = sqlite3.connect('migration_state.db')
        self.logger = self.setup_logging()
    
    def migrate_table(self, table_name):
        try:
            # Get last migration timestamp
            last_migration = self.get_last_migration_time(table_name)
            
            # Extract changes since last migration
            changes = self.extract_changes(table_name, last_migration)
            
            if not changes.empty:
                # Transform data for PostgreSQL
                transformed_data = self.transform_data(table_name, changes)
                
                # Load into staging and then target
                self.load_data(table_name, transformed_data)
                
                # Update migration state
                self.update_migration_state(table_name)
                
                self.logger.info(f"Successfully migrated {len(changes)} records from {table_name}")
            else:
                self.logger.info(f"No changes detected for table {table_name}")
                
        except Exception as e:
            self.logger.error(f"Migration failed for table {table_name}: {str(e)}")
            raise
```

#### Error Handling and Recovery
- Automatic retry mechanism for transient failures
- Transaction rollback for data consistency
- Detailed error logging with stack traces
- Email alerts for critical failures
- Manual recovery procedures documented

#### Performance Optimization
- Configurable batch sizes for memory management
- Parallel processing for independent tables
- Connection pooling for database efficiency
- Incremental processing to minimize data transfer
- Compression for large data transfers

### Configuration Management

#### Database Connections
```yaml
# config/database.yaml
mysql:
  host: ${MYSQL_HOST}
  port: ${MYSQL_PORT}
  database: ${MYSQL_DATABASE}
  username: ${MYSQL_USERNAME}
  password: ${MYSQL_PASSWORD}

postgresql:
  host: ${POSTGRES_HOST}
  port: ${POSTGRES_PORT}
  database: ${POSTGRES_DATABASE}
  username: ${POSTGRES_USERNAME}
  password: ${POSTGRES_PASSWORD}
```

#### Table Mapping Configuration
```yaml
# config/table_mapping.yaml
tables:
  users:
    source_table: users
    target_table: users
    timestamp_column: updated_at
    primary_key: user_id
    transformations:
      - column: phone_number
        type: format_phone
      - column: email
        type: lowercase
    
  orders:
    source_table: orders
    target_table: orders
    timestamp_column: modified_date
    primary_key: order_id
    batch_size: 500
```

### Deployment and Operations

#### Installation Steps
1. Clone repository to target server
2. Create Python virtual environment
3. Install dependencies from requirements.txt
4. Configure database connections and table mappings
5. Initialize SQLite state database
6. Set up cron job for weekly execution
7. Configure log rotation and monitoring

#### Monitoring and Alerting
- Log file monitoring for error patterns
- Email notifications for migration failures
- Weekly summary reports with statistics
- Dashboard for migration history and trends
- Automated health checks for database connectivity

#### Maintenance Procedures
- Weekly log file review and cleanup
- Monthly performance optimization review
- Quarterly disaster recovery testing
- Semi-annual dependency updates
- Documentation updates as needed

### Security Considerations

#### Database Security
- Encrypted connections (SSL/TLS) for all database communications
- Least privilege database user accounts
- Password management through environment variables
- Network security groups restricting database access
- Regular security updates for Python dependencies

#### Data Protection
- No sensitive data stored in log files
- Temporary staging data cleanup after migration
- Audit trail of all migration activities
- Data masking for non-production environments
- Compliance with data retention policies

### Advantages

1. **Simplicity**: Single technology stack that most teams understand
2. **Cost Control**: Pay only for compute time during migrations
3. **Full Control**: Complete visibility and control over migration process
4. **Incremental Friendly**: Easy to implement change detection logic
5. **Quick Start**: Begin development immediately without complex setup
6. **No Infrastructure Overhead**: Runs on any machine with Python
7. **Easy Debugging**: Simple to troubleshoot and modify
8. **Minimal Dependencies**: Uses standard Python libraries

### Limitations

1. **Development Time**: Requires custom development effort
2. **Maintenance**: Need to maintain custom code
3. **Manual Scaling**: Single-threaded execution by default
4. **Error Recovery**: Must implement comprehensive error handling
5. **Monitoring**: Basic monitoring compared to enterprise solutions

### Success Metrics

- **Data Consistency**: 99.9% accuracy between source and target
- **Migration Performance**: Complete weekly migration within 4-hour window
- **Reliability**: Less than 1% failure rate for weekly migrations
- **Recovery Time**: Automatic recovery from failures within 30 minutes
- **Data Freshness**: Target data no more than 7 days behind source

This architecture provides a robust, maintainable, and cost-effective solution for the 6-month parallel operation period while maintaining the simplicity requested.

