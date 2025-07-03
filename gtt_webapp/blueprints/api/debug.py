from flask import Blueprint, jsonify, current_app, request
from models.custom_gtt import add_custom_gtt_order
from db_config import configuration
import logging
import oracledb
from datetime import datetime
from datetime import datetime

debug_api = Blueprint('debug_api', __name__)
logger = logging.getLogger('custom_data')

@debug_api.route('/routes', methods=['GET'])
def list_routes():
    """List all available routes"""
    routes = []
    
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': str(rule)
        })
        
    return jsonify({
        'routes': routes
    })

@debug_api.route('/test-save', methods=['POST'])
def test_save():
    """Test the save order functionality"""
    try:
        # Log request information for debugging
        logger.debug(f"[DEBUG] Test save request method: {request.method}")
        logger.debug(f"[DEBUG] Test save request content type: {request.content_type}")
        logger.debug(f"[DEBUG] Test save request headers: {dict(request.headers)}")
        
        if not request.is_json:
            logger.error(f"[DEBUG] Request is not JSON. Content-Type: {request.content_type}")
            response = jsonify({
                'success': False,
                'error': 'Request must be JSON'
            })
            response.headers['Content-Type'] = 'application/json'
            return response, 400
            
        # Try to parse JSON data
        try:
            data = request.json
            logger.debug(f"[DEBUG] Test save order with data: {data}")
        except Exception as json_err:
            logger.error(f"[DEBUG] Error parsing JSON data: {str(json_err)}", exc_info=True)
            response = jsonify({
                'success': False,
                'error': f'Error parsing JSON data: {str(json_err)}'
            })
            response.headers['Content-Type'] = 'application/json'
            return response, 400
        
        # Complete data for testing with all fields from DB
        test_data = {
            'symbol': data.get('symbol', 'TEST'),
            'company_name': data.get('company_name'),  # Allow to be None
            'nifty_rank': data.get('nifty_rank', 0),
            'exchange': data.get('exchange', 'NSE'),
            'order_type': data.get('order_type', 'BUY'),
            'trigger_type': data.get('trigger_type', 'single'),
            'quantity': data.get('quantity', 1),
            'trigger_price': data.get('trigger_price', 100.0),
            'last_price': data.get('last_price', 105.0),
            'target_price': data.get('target_price'),
            'stop_loss': data.get('stop_loss'),
            'trigger_values': None,  # Set to None by default
            'notes': data.get('notes', '')
        }
        
        # For single-trigger orders, set trigger_values only for two-leg orders
        if test_data['trigger_type'] == 'two-leg' and test_data['stop_loss'] and test_data['target_price']:
            test_data['trigger_values'] = f"{test_data['stop_loss']},{test_data['target_price']}"
        
        # Log explicit check for notes field
        if 'notes' in data:
            logger.debug(f"[DEBUG] Notes field found in request: {data['notes']}")
            
        logger.debug(f"[DEBUG] Attempting to save order with test_data: {test_data}")
        order_id = add_custom_gtt_order(test_data)
        logger.debug(f"[DEBUG] Test order saved with ID: {order_id}")
        
        response = jsonify({
            'success': True,
            'order_id': order_id,
            'message': 'Test order saved successfully'
        })
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        logger.error(f"[DEBUG] Error saving test order: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 500

@debug_api.route('/table-info', methods=['GET'])
def get_table_info():
    """Get information about the custom_gtt_orders table"""
    connection = None
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT table_name 
            FROM user_tables 
            WHERE table_name = 'CUSTOM_GTT_ORDERS'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            return jsonify({
                'exists': False,
                'message': 'Table CUSTOM_GTT_ORDERS does not exist'
            })
        
        # Get column information
        cursor.execute("""
            SELECT column_name, data_type, data_length, nullable
            FROM user_tab_columns
            WHERE table_name = 'CUSTOM_GTT_ORDERS'
            ORDER BY column_id
        """)
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'length': row[2],
                'nullable': row[3] == 'Y'
            })
        
        return jsonify({
            'exists': True,
            'table_name': 'CUSTOM_GTT_ORDERS',
            'columns': columns
        })
    except Exception as e:
        logger.error(f"[ERROR] Failed to get table info: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500
    finally:
        if connection:
            connection.close()

@debug_api.route('/fix-table', methods=['POST'])
def fix_table():
    """Fix the custom_gtt_orders table structure if needed"""
    connection = None
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        results = {
            'actions': [],
            'success': True
        }
        
        # Check if table exists
        cursor.execute("""
            SELECT table_name 
            FROM user_tables 
            WHERE table_name = 'CUSTOM_GTT_ORDERS'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            results['actions'].append('Table does not exist, creating table')
            # Create the table
            cursor.execute('''
                CREATE TABLE custom_gtt_orders (
                    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    symbol VARCHAR2(50),
                    company_name VARCHAR2(100),
                    nifty_rank NUMBER,
                    exchange VARCHAR2(10),
                    order_type VARCHAR2(10),
                    trigger_type VARCHAR2(20),
                    trigger_price NUMBER,
                    last_price NUMBER,
                    quantity NUMBER,
                    target_price NUMBER,
                    stop_loss NUMBER,
                    trigger_values VARCHAR2(100),
                    notes VARCHAR2(500),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    is_active NUMBER(1),
                    placed_on_kite NUMBER(1),
                    kite_trigger_id NUMBER
                )
            ''')
            connection.commit()
        else:
            # Check for missing columns
            for column_name, data_type in [
                ('trigger_values', 'VARCHAR2(100)'),
                ('notes', 'VARCHAR2(500)'),
                ('last_price', 'NUMBER'),
                ('company_name', 'VARCHAR2(100)'),
                ('nifty_rank', 'NUMBER')
            ]:
                try:
                    cursor.execute(f"""
                        SELECT {column_name}
                        FROM custom_gtt_orders
                        WHERE ROWNUM = 1
                    """)
                    results['actions'].append(f'Column {column_name} exists')
                except oracledb.DatabaseError as e:
                    if 'ORA-00904' in str(e):  # Column does not exist
                        try:
                            results['actions'].append(f'Adding missing column {column_name}')
                            cursor.execute(f"""
                                ALTER TABLE custom_gtt_orders
                                ADD {column_name} {data_type}
                            """)
                            connection.commit()
                        except Exception as alter_e:
                            results['actions'].append(f'Error adding column {column_name}: {str(alter_e)}')
                            results['success'] = False
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"[ERROR] Failed to fix table: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if connection:
            connection.close()

@debug_api.route('/test-route', methods=['GET'])
def test_route():
    """Test that routes are registered correctly"""
    try:
        logger.debug("[DEBUG] Test route accessed")
        
        # Collect routes for debugging
        routes = []
        for rule in current_app.url_map.iter_rules():
            if '/api/' in str(rule):
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'rule': str(rule)
                })
                
        response = jsonify({
            'success': True,
            'message': 'Debug route is working correctly',
            'api_routes': routes
        })
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        logger.error(f"[DEBUG] Error in test route: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': str(e)
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 500

@debug_api.route('/diagnostics', methods=['GET'])
def run_diagnostics():
    """Run comprehensive diagnostics to help troubleshoot issues"""
    diagnostics = {
        'timestamp': datetime.now().isoformat(),
        'tests': [],
        'summary': {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
    }
    
    def add_test(name, status, message, details=None):
        test_result = {
            'name': name,
            'status': status,  # 'pass', 'fail', 'warning'
            'message': message
        }
        if details:
            test_result['details'] = details
        diagnostics['tests'].append(test_result)
        diagnostics['summary']['total_tests'] += 1
        if status == 'pass':
            diagnostics['summary']['passed'] += 1
        elif status == 'fail':
            diagnostics['summary']['failed'] += 1
        elif status == 'warning':
            diagnostics['summary']['warnings'] += 1
    
    # Test 1: Database connectivity
    try:
        with oracledb.connect(**configuration['db_config']) as connection:
            add_test('Database Connection', 'pass', 'Successfully connected to Oracle database')
    except Exception as e:
        add_test('Database Connection', 'fail', f'Failed to connect to database: {str(e)}')
    
    # Test 2: Table existence and structure
    try:
        with oracledb.connect(**configuration['db_config']) as connection:
            with connection.cursor() as cursor:
                # Check if table exists
                cursor.execute("""
                    SELECT COUNT(*) FROM user_tables 
                    WHERE table_name = 'CUSTOM_GTT_ORDERS'
                """)
                table_exists = cursor.fetchone()[0] > 0
                
                if table_exists:
                    # Get column information
                    cursor.execute("""
                        SELECT column_name, data_type, nullable 
                        FROM user_tab_columns 
                        WHERE table_name = 'CUSTOM_GTT_ORDERS'
                        ORDER BY column_id
                    """)
                    columns = cursor.fetchall()
                    
                    required_columns = ['ID', 'SYMBOL', 'ORDER_TYPE', 'QUANTITY', 'TRIGGER_TYPE']
                    missing_columns = []
                    for req_col in required_columns:
                        if not any(col[0] == req_col for col in columns):
                            missing_columns.append(req_col)
                    
                    if missing_columns:
                        add_test('Table Structure', 'fail', 
                               f'Missing required columns: {", ".join(missing_columns)}',
                               {'columns': [{'name': col[0], 'type': col[1], 'nullable': col[2]} for col in columns]})
                    else:
                        add_test('Table Structure', 'pass', 
                               f'Table exists with {len(columns)} columns',
                               {'columns': [{'name': col[0], 'type': col[1], 'nullable': col[2]} for col in columns]})
                else:
                    add_test('Table Structure', 'fail', 'CUSTOM_GTT_ORDERS table does not exist')
    except Exception as e:
        add_test('Table Structure', 'fail', f'Error checking table structure: {str(e)}')
    
    # Test 3: KiteConnect availability
    try:
        kite = current_app.config.get('kite')
        if kite:
            # Try to get profile to test connection
            profile = kite.profile()
            add_test('KiteConnect', 'pass', f'KiteConnect available for user: {profile.get("user_name", "Unknown")}')
        else:
            add_test('KiteConnect', 'warning', 'KiteConnect not configured')
    except Exception as e:
        add_test('KiteConnect', 'fail', f'KiteConnect error: {str(e)}')
    
    # Test 4: API endpoints accessibility
    routes_to_test = [
        '/api/test',
        '/api/custom-gtt/orders',
        '/api/table-info',
        '/custom-gtt/'
    ]
    
    for route in routes_to_test:
        try:
            # Check if route exists in URL map
            endpoint_exists = any(str(rule) == route for rule in current_app.url_map.iter_rules())
            if endpoint_exists:
                add_test(f'Route {route}', 'pass', 'Route is registered')
            else:
                add_test(f'Route {route}', 'fail', 'Route not found in URL map')
        except Exception as e:
            add_test(f'Route {route}', 'fail', f'Error checking route: {str(e)}')
    
    # Test 5: Sample data fetch
    try:
        from models.custom_gtt import get_custom_gtt_orders
        orders = get_custom_gtt_orders()
        add_test('Sample Data Fetch', 'pass', f'Successfully fetched {len(orders)} sample records')
    except Exception as e:
        add_test('Sample Data Fetch', 'fail', f'Error fetching sample data: {str(e)}')
    
    return jsonify(diagnostics)
