"""
Saved Filters Management for Advanced Search
Handles saving, loading, and managing user-defined search filters
"""

import json
import os
from datetime import datetime
from flask import current_app

class SavedFiltersManager:
    def __init__(self):
        self.filters_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'saved_filters.json')
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure the data directory exists"""
        data_dir = os.path.dirname(self.filters_file)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Initialize filters file if it doesn't exist
        if not os.path.exists(self.filters_file):
            self.save_filters_to_file([])
    
    def load_saved_filters(self):
        """Load all saved filters from file"""
        try:
            with open(self.filters_file, 'r') as f:
                filters = json.load(f)
                
            # Ensure each filter has required fields
            validated_filters = []
            for filter_data in filters:
                if isinstance(filter_data, dict) and all(key in filter_data for key in ['id', 'name', 'query']):
                    validated_filters.append(filter_data)
                    
            return validated_filters
        except (FileNotFoundError, json.JSONDecodeError) as e:
            current_app.logger.error(f"Error loading saved filters: {str(e)}")
            return []
    
    def save_filters_to_file(self, filters):
        """Save filters list to file"""
        try:
            with open(self.filters_file, 'w') as f:
                json.dump(filters, f, indent=2)
            return True
        except Exception as e:
            current_app.logger.error(f"Error saving filters: {str(e)}")
            return False
    
    def save_filter(self, name, query, description=""):
        """Save a new filter"""
        filters = self.load_saved_filters()
        
        # Generate unique ID
        filter_id = max([f['id'] for f in filters], default=0) + 1
        
        # Create new filter
        new_filter = {
            'id': filter_id,
            'name': name.strip(),
            'query': query.strip(),
            'description': description.strip(),
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_used': None,
            'usage_count': 0
        }
        
        # Check for duplicate names
        if any(f['name'].lower() == name.lower() for f in filters):
            return {'success': False, 'error': 'Filter name already exists'}
        
        filters.append(new_filter)
        
        if self.save_filters_to_file(filters):
            return {'success': True, 'filter': new_filter}
        else:
            return {'success': False, 'error': 'Failed to save filter'}
    
    def delete_filter(self, filter_id):
        """Delete a filter by ID"""
        filters = self.load_saved_filters()
        original_count = len(filters)
        
        filters = [f for f in filters if f['id'] != filter_id]
        
        if len(filters) < original_count:
            if self.save_filters_to_file(filters):
                return {'success': True, 'message': 'Filter deleted successfully'}
            else:
                return {'success': False, 'error': 'Failed to delete filter'}
        else:
            return {'success': False, 'error': 'Filter not found'}
    
    def update_filter_usage(self, filter_id):
        """Update filter usage statistics"""
        filters = self.load_saved_filters()
        
        for filter_data in filters:
            if filter_data['id'] == filter_id:
                filter_data['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                filter_data['usage_count'] = filter_data.get('usage_count', 0) + 1
                break
        
        self.save_filters_to_file(filters)
    
    def get_filter_by_id(self, filter_id):
        """Get a specific filter by ID"""
        filters = self.load_saved_filters()
        for filter_data in filters:
            if filter_data['id'] == filter_id:
                return filter_data
        return None
    
    def get_popular_filters(self, limit=5):
        """Get most frequently used filters"""
        filters = self.load_saved_filters()
        sorted_filters = sorted(filters, key=lambda x: x.get('usage_count', 0), reverse=True)
        return sorted_filters[:limit]
    
    def export_filters(self):
        """Export all filters as JSON"""
        return self.load_saved_filters()
    
    def import_filters(self, imported_filters, overwrite=False):
        """Import filters from JSON data"""
        try:
            if not overwrite:
                existing_filters = self.load_saved_filters()
                existing_names = {f['name'].lower() for f in existing_filters}
                
                # Filter out duplicates
                new_filters = []
                skipped = []
                
                for filter_data in imported_filters:
                    if filter_data['name'].lower() not in existing_names:
                        # Generate new ID
                        filter_data['id'] = max([f['id'] for f in existing_filters], default=0) + len(new_filters) + 1
                        new_filters.append(filter_data)
                    else:
                        skipped.append(filter_data['name'])
                
                all_filters = existing_filters + new_filters
            else:
                # Reassign IDs for imported filters
                for i, filter_data in enumerate(imported_filters, 1):
                    filter_data['id'] = i
                all_filters = imported_filters
                skipped = []
            
            if self.save_filters_to_file(all_filters):
                return {
                    'success': True, 
                    'imported': len(imported_filters) - len(skipped),
                    'skipped': len(skipped),
                    'skipped_names': skipped
                }
            else:
                return {'success': False, 'error': 'Failed to save imported filters'}
                
        except Exception as e:
            return {'success': False, 'error': f'Import failed: {str(e)}'}

# Global instance
saved_filters_manager = SavedFiltersManager()
