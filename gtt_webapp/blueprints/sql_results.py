from flask import Blueprint, render_template, request, jsonify
import oracledb
import csv
import json
import os
import sys
from datetime import datetime
from db_config import configuration

# Add the parent directory to access auth module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from auth.simple_oauth import login_required
from auth.access_control import feature_required

sql_results_bp = Blueprint('sql_results', __name__, url_prefix='/sql-results')

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql_results_cache')
CACHE_INFO_FILE = os.path.join(CACHE_DIR, 'cache_info.json')

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def get_database_connection():
    """Get Oracle database connection"""
    try:
        db_config = configuration['db_config']
        return oracledb.connect(**db_config)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_cache_info():
    """Get cache information"""
    if os.path.exists(CACHE_INFO_FILE):
        try:
            with open(CACHE_INFO_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache_info(info):
    """Save cache information"""
    try:
        with open(CACHE_INFO_FILE, 'w') as f:
            json.dump(info, f, indent=2)
    except Exception as e:
        print(f"Error saving cache info: {e}")

def get_cached_results():
    """Get cached results from CSV files"""
    cache_info = get_cache_info()
    results = []
    
    for query_name, info in cache_info.get('queries', {}).items():
        csv_file = os.path.join(CACHE_DIR, f"{query_name.replace(' ', '_').replace('/', '_')}.csv")
        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    if rows:
                        columns = list(rows[0].keys())
                        results.append({
                            "query_name": query_name,
                            "columns": columns,
                            "rows": rows,
                            "row_count": len(rows),
                            "cached_at": info.get('cached_at', 'Unknown')
                        })
            except Exception as e:
                print(f"Error reading cache file {csv_file}: {e}")
    
    return results

@sql_results_bp.route('/')
@login_required
@feature_required('sql_results')
def index():
    """SQL Results main page"""
    cache_info = get_cache_info()
    return render_template('sql_results/index.html', 
                         cache_info=cache_info,
                         last_fetch=cache_info.get('last_fetch', 'Never'))

@sql_results_bp.route('/api/fetch-data', methods=['POST'])
@login_required
@feature_required('sql_results')
def fetch_data():
    """Fetch data from database and cache it"""
    try:
        data = request.get_json()
        nifty_rank = data.get('nifty_rank', '600')
        
        connection = get_database_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = connection.cursor()
        
        # Get current user's trading ID for filtering
        from auth.access_control import UserDataFilter
        current_trading_user_id = UserDataFilter.get_user_trading_id()
        
        # Fetch all queries from the QUERY_REPOSITORY table with user filtering
        query_repo = """SELECT *
  FROM (  SELECT file_seq || execution_order     AS query_id,
                 TO_CHAR (TRIM (query_text))     AS query_text,
                 report_name                     AS query_name
            FROM report_sql
           WHERE (trading_user_id IS NULL OR trading_user_id = :trading_user_id)
        ORDER BY file_seq, TO_NUMBER (execution_order))"""
        
        cursor.execute(query_repo, {'trading_user_id': current_trading_user_id})
        queries = cursor.fetchall()
        
        # Execute each query and cache results
        results = []
        cache_info = {
            'last_fetch': datetime.now().isoformat(),
            'nifty_rank_used': nifty_rank,
            'queries': {}
        }
        
        for query_id, query_text, query_name in queries:
            try:
                # Replace parameter
                modified_query = query_text.replace('p_nifty_rank', str(nifty_rank))
                
                cursor.execute(modified_query)
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                
                # Convert rows to list of dicts
                dict_rows = []
                for row in rows:
                    dict_row = {}
                    for i, col in enumerate(columns):
                        # Handle different data types
                        value = row[i]
                        if value is None:
                            dict_row[col] = ''
                        else:
                            dict_row[col] = str(value)
                    dict_rows.append(dict_row)
                
                # Save to CSV
                csv_filename = f"{query_name.replace(' ', '_').replace('/', '_')}.csv"
                csv_file = os.path.join(CACHE_DIR, csv_filename)
                
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    if dict_rows:
                        writer = csv.DictWriter(f, fieldnames=columns)
                        writer.writeheader()
                        writer.writerows(dict_rows)
                
                # Add to cache info
                cache_info['queries'][query_name] = {
                    'cached_at': datetime.now().isoformat(),
                    'row_count': len(dict_rows),
                    'csv_file': csv_filename
                }
                
                results.append({
                    "query_name": query_name,
                    "columns": columns,
                    "rows": dict_rows,
                    "row_count": len(dict_rows)
                })
                
            except Exception as e:
                print(f"Error executing query {query_name}: {e}")
                continue
        
        # Save cache info
        save_cache_info(cache_info)
        
        cursor.close()
        connection.close()
        
        return jsonify({
            "success": True,
            "message": f"Successfully fetched {len(results)} queries",
            "results": results,
            "cache_info": cache_info
        })
        
    except Exception as e:
        print(f"Error in fetch_data: {e}")
        return jsonify({"error": str(e)}), 500

@sql_results_bp.route('/api/get-cached-data')
@login_required
@feature_required('sql_results')
def get_cached_data():
    """Get cached data from CSV files"""
    try:
        results = get_cached_results()
        cache_info = get_cache_info()
        
        return jsonify({
            "success": True,
            "results": results,
            "cache_info": cache_info
        })
        
    except Exception as e:
        print(f"Error in get_cached_data: {e}")
        return jsonify({"error": str(e)}), 500

@sql_results_bp.route('/api/clear-cache', methods=['POST'])
@login_required
@feature_required('sql_results')
def clear_cache():
    """Clear all cached data"""
    try:
        # Remove all CSV files
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.csv'):
                os.remove(os.path.join(CACHE_DIR, filename))
        
        # Clear cache info
        save_cache_info({})
        
        return jsonify({
            "success": True,
            "message": "Cache cleared successfully"
        })
        
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return jsonify({"error": str(e)}), 500
