"""
Migration State Manager
Handles tracking migration progress and state persistence
"""

import json
import os
from datetime import datetime
from pathlib import Path


class MigrationState:
    """Manages migration state and progress tracking"""
    
    def __init__(self, state_file='migration_state.json'):
        self.state_file = Path(state_file)
        self.default_state = {
            'status': 'not_started',  # not_started, in_progress, completed, failed
            'start_time': None,
            'end_time': None,
            'last_update': None,
            'current_phase': None,
            'tables': {
                'MusicCatalog': {
                    'status': 'not_started',
                    'total_records': 0,
                    'records_migrated': 0,
                    'last_processed_id': None,
                    'start_time': None,
                    'end_time': None,
                    'entities': {
                        'artists': {'total': 0, 'migrated': 0, 'last_id': None},
                        'albums': {'total': 0, 'migrated': 0, 'last_id': None},
                        'tracks': {'total': 0, 'migrated': 0, 'last_id': None}
                    }
                },
                'CustomerOrders': {
                    'status': 'not_started',
                    'total_records': 0,
                    'records_migrated': 0,
                    'last_processed_id': None,
                    'start_time': None,
                    'end_time': None,
                    'entities': {
                        'customers': {'total': 0, 'migrated': 0, 'last_id': None},
                        'orders': {'total': 0, 'migrated': 0, 'last_id': None}
                    }
                },
                'Playlists': {
                    'status': 'not_started',
                    'total_records': 0,
                    'records_migrated': 0,
                    'last_processed_id': None,
                    'start_time': None,
                    'end_time': None
                },
                'EmployeeManagement': {
                    'status': 'not_started',
                    'total_records': 0,
                    'records_migrated': 0,
                    'last_processed_id': None,
                    'start_time': None,
                    'end_time': None
                }
            },
            'errors': [],
            'validation_results': {}
        }
    
    def initialize(self):
        """Initialize migration state"""
        state = self.default_state.copy()
        state['last_update'] = datetime.now().isoformat()
        self._save_state(state)
    
    def get_state(self):
        """Get current migration state"""
        if not self.state_file.exists():
            return self.default_state.copy()
        
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self.default_state.copy()
    
    def update_state(self, updates):
        """Update migration state"""
        state = self.get_state()
        state.update(updates)
        state['last_update'] = datetime.now().isoformat()
        self._save_state(state)
    
    def start_migration(self):
        """Mark migration as started"""
        self.update_state({
            'status': 'in_progress',
            'start_time': datetime.now().isoformat(),
            'current_phase': 'initialization'
        })
    
    def complete_migration(self):
        """Mark migration as completed"""
        self.update_state({
            'status': 'completed',
            'end_time': datetime.now().isoformat(),
            'current_phase': 'completed'
        })
    
    def fail_migration(self, error_message):
        """Mark migration as failed"""
        state = self.get_state()
        state['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'message': error_message
        })
        state.update({
            'status': 'failed',
            'end_time': datetime.now().isoformat()
        })
        self._save_state(state)
    
    def start_table_migration(self, table_name, total_records=0):
        """Start migration for a specific table"""
        state = self.get_state()
        state['tables'][table_name].update({
            'status': 'in_progress',
            'total_records': total_records,
            'start_time': datetime.now().isoformat()
        })
        state['current_phase'] = f'migrating_{table_name.lower()}'
        self._save_state(state)
    
    def complete_table_migration(self, table_name):
        """Complete migration for a specific table"""
        state = self.get_state()
        state['tables'][table_name].update({
            'status': 'completed',
            'end_time': datetime.now().isoformat()
        })
        self._save_state(state)
    
    def update_table_progress(self, table_name, records_migrated, last_processed_id=None):
        """Update progress for a specific table"""
        state = self.get_state()
        state['tables'][table_name]['records_migrated'] = records_migrated
        if last_processed_id is not None:
            state['tables'][table_name]['last_processed_id'] = last_processed_id
        self._save_state(state)
    
    def update_entity_progress(self, table_name, entity_type, total=None, migrated=None, last_id=None):
        """Update progress for a specific entity within a table"""
        state = self.get_state()
        if table_name in state['tables'] and 'entities' in state['tables'][table_name]:
            entity_state = state['tables'][table_name]['entities'].get(entity_type, {})
            
            if total is not None:
                entity_state['total'] = total
            if migrated is not None:
                entity_state['migrated'] = migrated
            if last_id is not None:
                entity_state['last_id'] = last_id
            
            state['tables'][table_name]['entities'][entity_type] = entity_state
            self._save_state(state)
    
    def get_table_state(self, table_name):
        """Get state for a specific table"""
        state = self.get_state()
        return state['tables'].get(table_name, {})
    
    def get_last_processed_id(self, table_name, entity_type=None):
        """Get the last processed ID for resuming migration"""
        table_state = self.get_table_state(table_name)
        
        if entity_type and 'entities' in table_state:
            return table_state['entities'].get(entity_type, {}).get('last_id')
        
        return table_state.get('last_processed_id')
    
    def is_table_completed(self, table_name):
        """Check if table migration is completed"""
        table_state = self.get_table_state(table_name)
        return table_state.get('status') == 'completed'
    
    def is_migration_completed(self):
        """Check if entire migration is completed"""
        state = self.get_state()
        return state.get('status') == 'completed'
    
    def can_resume(self):
        """Check if migration can be resumed"""
        state = self.get_state()
        return state.get('status') == 'in_progress'
    
    def add_error(self, error_message, table_name=None):
        """Add an error to the state"""
        state = self.get_state()
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': error_message
        }
        if table_name:
            error_entry['table'] = table_name
        
        state['errors'].append(error_entry)
        self._save_state(state)
    
    def get_migration_summary(self):
        """Get a summary of migration progress"""
        state = self.get_state()
        
        total_records = 0
        migrated_records = 0
        completed_tables = 0
        
        for table_name, table_state in state['tables'].items():
            total_records += table_state.get('total_records', 0)
            migrated_records += table_state.get('records_migrated', 0)
            if table_state.get('status') == 'completed':
                completed_tables += 1
        
        return {
            'overall_status': state.get('status'),
            'total_tables': len(state['tables']),
            'completed_tables': completed_tables,
            'total_records': total_records,
            'migrated_records': migrated_records,
            'progress_percentage': (migrated_records / total_records * 100) if total_records > 0 else 0,
            'start_time': state.get('start_time'),
            'last_update': state.get('last_update'),
            'error_count': len(state.get('errors', []))
        }
    
    def reset(self):
        """Reset migration state"""
        if self.state_file.exists():
            self.state_file.unlink()
        self.initialize()
    
    def _save_state(self, state):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except IOError as e:
            raise Exception(f"Failed to save migration state: {str(e)}")


