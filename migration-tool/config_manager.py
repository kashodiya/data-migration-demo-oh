
"""
Configuration Manager for Migration Tool
Handles loading and saving migration configuration
"""

import json
import os
from pathlib import Path


class ConfigManager:
    """Manages migration configuration settings"""
    
    def __init__(self, config_file='migration_config.json'):
        self.config_file = Path(config_file)
        self.default_config = {
            'source_db': None,
            'aws_region': 'us-east-1',
            'batch_size': 25,
            'target_tables': {
                'MusicCatalog': 'chinook-music-catalog',
                'CustomerOrders': 'chinook-customer-orders',
                'Playlists': 'chinook-playlists',
                'EmployeeManagement': 'chinook-employee-management'
            },
            'table_schemas': {
                'MusicCatalog': {
                    'billing_mode': 'ON_DEMAND',
                    'global_secondary_indexes': [
                        {
                            'index_name': 'GSI1-NameSearch',
                            'keys': ['GSI1PK', 'GSI1SK']
                        },
                        {
                            'index_name': 'GSI2-GenreSearch', 
                            'keys': ['GSI2PK']
                        }
                    ]
                },
                'CustomerOrders': {
                    'billing_mode': 'ON_DEMAND',
                    'global_secondary_indexes': [
                        {
                            'index_name': 'GSI1-EmailSearch',
                            'keys': ['GSI1PK', 'GSI1SK']
                        }
                    ]
                },
                'Playlists': {
                    'billing_mode': 'ON_DEMAND',
                    'global_secondary_indexes': []
                },
                'EmployeeManagement': {
                    'billing_mode': 'ON_DEMAND',
                    'global_secondary_indexes': []
                }
            }
        }
    
    def save_config(self, config):
        """Save configuration to file"""
        # Merge with defaults
        merged_config = self.default_config.copy()
        merged_config.update(config)
        
        with open(self.config_file, 'w') as f:
            json.dump(merged_config, f, indent=2)
    
    def load_config(self):
        """Load configuration from file"""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            # Ensure all required fields are present
            merged_config = self.default_config.copy()
            merged_config.update(config)
            return merged_config
            
        except (json.JSONDecodeError, IOError) as e:
            raise Exception(f"Failed to load configuration: {str(e)}")
    
    def get_table_name(self, logical_name):
        """Get physical DynamoDB table name for logical table"""
        config = self.load_config()
        if not config:
            raise Exception("No configuration loaded")
        
        return config['target_tables'].get(logical_name)
    
    def get_table_schema(self, logical_name):
        """Get table schema configuration"""
        config = self.load_config()
        if not config:
            raise Exception("No configuration loaded")
        
        return config['table_schemas'].get(logical_name, {})
    
    def update_config(self, updates):
        """Update existing configuration"""
        config = self.load_config()
        if not config:
            config = self.default_config.copy()
        
        config.update(updates)
        self.save_config(config)
    
    def config_exists(self):
        """Check if configuration file exists"""
        return self.config_file.exists()

