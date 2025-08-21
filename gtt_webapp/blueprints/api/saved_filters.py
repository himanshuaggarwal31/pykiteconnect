"""
API endpoints for saved filters management
"""

from flask import Blueprint, request, jsonify
import logging
from models.saved_filters import saved_filters_manager

saved_filters_api = Blueprint('saved_filters_api', __name__)

# Configure logging
logger = logging.getLogger('custom_data')

@saved_filters_api.route('/saved-filters', methods=['GET'])
def get_saved_filters():
    """Get all saved filters"""
    try:
        filters = saved_filters_manager.load_saved_filters()
        
        # Sort by usage count and creation date
        filters.sort(key=lambda x: (x.get('usage_count', 0), x.get('created_at', '')), reverse=True)
        
        return jsonify({
            'success': True,
            'filters': filters,
            'count': len(filters)
        })
    except Exception as e:
        logger.error(f"[API] Error getting saved filters: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@saved_filters_api.route('/saved-filters', methods=['POST'])
def save_filter():
    """Save a new filter"""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        name = data.get('name', '').strip()
        query = data.get('query', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Filter name is required'
            }), 400
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Filter query is required'
            }), 400
        
        result = saved_filters_manager.save_filter(name, query, description)
        
        if result['success']:
            logger.info(f"[API] Saved filter '{name}': {query}")
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"[API] Error saving filter: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@saved_filters_api.route('/saved-filters/<int:filter_id>', methods=['DELETE'])
def delete_filter(filter_id):
    """Delete a saved filter"""
    try:
        result = saved_filters_manager.delete_filter(filter_id)
        
        if result['success']:
            logger.info(f"[API] Deleted filter ID: {filter_id}")
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        logger.error(f"[API] Error deleting filter {filter_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@saved_filters_api.route('/saved-filters/<int:filter_id>/use', methods=['POST'])
def use_filter(filter_id):
    """Mark filter as used and return its query"""
    try:
        filter_data = saved_filters_manager.get_filter_by_id(filter_id)
        
        if not filter_data:
            return jsonify({
                'success': False,
                'error': 'Filter not found'
            }), 404
        
        # Update usage statistics
        saved_filters_manager.update_filter_usage(filter_id)
        
        logger.info(f"[API] Used filter '{filter_data['name']}': {filter_data['query']}")
        
        return jsonify({
            'success': True,
            'filter': filter_data
        })
        
    except Exception as e:
        logger.error(f"[API] Error using filter {filter_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@saved_filters_api.route('/saved-filters/popular', methods=['GET'])
def get_popular_filters():
    """Get most popular filters"""
    try:
        limit = int(request.args.get('limit', 5))
        filters = saved_filters_manager.get_popular_filters(limit)
        
        return jsonify({
            'success': True,
            'filters': filters,
            'count': len(filters)
        })
    except Exception as e:
        logger.error(f"[API] Error getting popular filters: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@saved_filters_api.route('/saved-filters/export', methods=['GET'])
def export_filters():
    """Export all filters as JSON"""
    try:
        filters = saved_filters_manager.export_filters()
        
        return jsonify({
            'success': True,
            'filters': filters,
            'export_date': saved_filters_manager.load_saved_filters()[0]['created_at'] if filters else None
        })
    except Exception as e:
        logger.error(f"[API] Error exporting filters: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@saved_filters_api.route('/saved-filters/import', methods=['POST'])
def import_filters():
    """Import filters from JSON data"""
    try:
        data = request.json
        if not data or 'filters' not in data:
            return jsonify({
                'success': False,
                'error': 'No filters data provided'
            }), 400
        
        overwrite = data.get('overwrite', False)
        result = saved_filters_manager.import_filters(data['filters'], overwrite)
        
        if result['success']:
            logger.info(f"[API] Imported filters: {result['imported']} imported, {result['skipped']} skipped")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[API] Error importing filters: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
