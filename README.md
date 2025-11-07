# SQLite to PostgreSQL Data Migration Project

A simple yet effective data migration solution for migrating from on-premises SQLite to AWS Aurora PostgreSQL with incremental synchronization capabilities.

## Project Overview

This project implements a custom Python ETL pipeline designed to handle weekly incremental data migrations during a 6-month parallel operation period. The solution provides complete control over the migration process while maintaining simplicity and cost-effectiveness.

## Key Features

- **Incremental Migration**: Timestamp-based change detection for efficient weekly synchronization
- **Simple Architecture**: Pure Python solution without containerization complexity
- **State Management**: SQLite-based tracking of migration progress and history
- **Automated Scheduling**: Cron-based weekly execution with comprehensive logging
- **Data Validation**: Built-in integrity checks and validation processes
- **Error Recovery**: Robust error handling with automatic retry mechanisms
- **Configuration-Driven**: YAML-based configuration for easy customization

## Architecture

The solution uses a custom Python ETL pipeline with the following components:

- **Python ETL Application**: Core migration logic using SQLAlchemy and Pandas
- **Virtual Environment**: Isolated dependency management
- **PostgreSQL Staging**: Temporary staging tables for data validation
- **Cron Job**: Simple scheduling for weekly automated execution
- **SQLite Database**: Local state management and job logging
- **File-based Logging**: Monitoring and alerting through structured log files

## Migration Process

1. **Change Detection**: Identify modified records since last migration
2. **Data Extraction**: Extract changed data in configurable batches
3. **Data Transformation**: Handle schema mapping and data type conversions
4. **Data Loading**: Load data through staging tables with validation
5. **State Management**: Update migration timestamps and statistics
6. **Validation**: Verify data integrity and generate reports

## Benefits

- ✅ **Cost Effective**: Pay only for compute time during migrations
- ✅ **Full Control**: Complete visibility into the migration process
- ✅ **Simple Deployment**: Runs on any machine with Python installed
- ✅ **Easy Debugging**: Straightforward troubleshooting and modification
- ✅ **Minimal Dependencies**: Uses standard Python libraries
- ✅ **Quick Start**: No complex infrastructure setup required

## Database Schema

The project uses the Chinook sample database, which represents a digital media store with tables for artists, albums, tracks, customers, and sales data.

![Chinook Database ER Diagram](chinook-er-diagram.png)

*Database Entity-Relationship diagram showing the complete schema structure and relationships between tables.*

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Detailed technical architecture and implementation
- [`ARCHITECTURE-OPTIONS.md`](ARCHITECTURE-OPTIONS.md) - Comparison of different architectural approaches

## Getting Started

1. **Prerequisites**: Python 3.8+, SQLite client libraries, PostgreSQL client libraries
2. **Installation**: Clone repository and set up virtual environment
3. **Configuration**: Configure database connections and table mappings
4. **Testing**: Run initial migration test with sample data
5. **Deployment**: Set up cron job for weekly automated execution

## Target Use Case

Perfect for organizations needing to:
- Migrate from SQLite to PostgreSQL during cloud transition
- Maintain data synchronization during parallel system operation
- Implement cost-effective migration without complex infrastructure
- Retain full control over the migration process and logic

This solution is designed for the 6-month parallel operation period where both on-premises and cloud systems need to stay synchronized through weekly incremental migrations.
