from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_from_directory
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

# Import the lazy KiteConnect function
def get_kite_instance():
    """Get or create KiteConnect instance with lazy initialization"""
    from kiteconnect import KiteConnect
    
    if current_app.config.get('kite') is not None:
        return current_app.config['kite']
        
    api_key = current_app.config.get('kite_api_key')
    access_token = current_app.config.get('kite_access_token')
    
    if not api_key or not access_token:
        current_app.logger.error("KiteConnect credentials not available")
        return None
        
    try:
        current_app.logger.debug("Creating new KiteConnect instance...")
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        
        # Test the connection
        profile = kite.profile()
        current_app.logger.info(f"KiteConnect connection successful. User: {profile.get('user_name', 'Unknown')}")
        
        # Cache the working instance
        current_app.config['kite'] = kite
        return kite
        
    except Exception as e:
        current_app.logger.error(f"Failed to create KiteConnect instance: {str(e)}")
        return None

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    try:
        kite = get_kite_instance()
        if kite is None:
            current_app.logger.warning("KiteConnect is not available in dashboard route")
            return render_template('dashboard.html', orders=[], error=True)
        
        current_app.logger.debug("Attempting to fetch GTT orders...")
        gtt_orders = kite.get_gtts()
        current_app.logger.info(f"Successfully fetched {len(gtt_orders)} GTT orders")
        
        return render_template('dashboard.html', orders=gtt_orders, error=False)
        
    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Error in dashboard route: {error_msg}", exc_info=True)
        
        # Provide more specific error messages
        if "403" in error_msg or "TokenException" in error_msg:
            flash(f'Access token error: {error_msg}. Please regenerate your access token.', 'error')
        elif "NetworkException" in error_msg:
            flash(f'Network error: {error_msg}. Please check your internet connection.', 'error')
        elif "General" in error_msg and "exception" in error_msg.lower():
            flash(f'API error: {error_msg}. Please check your API key and token.', 'error')
        else:
            flash(f'Error fetching GTT orders: {error_msg}', 'error')
            
        return render_template('dashboard.html', orders=[], error=True)

@main_bp.route('/order/<int:trigger_id>')
def order_detail(trigger_id):
    try:
        kite = get_kite_instance()
        if kite is None:
            flash('KiteConnect is not available', 'error')
            return redirect(url_for('main.dashboard'))
            
        order = next((o for o in kite.get_gtts() if o['id'] == trigger_id), None)
        if order:
            return render_template('order_detail.html', order=order)
        flash('Order not found', 'error')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash(f'Error fetching order details: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/order/delete/<int:trigger_id>', methods=['POST'])
def delete_order(trigger_id):
    try:
        kite = get_kite_instance()
        if kite is None:
            flash('KiteConnect is not available', 'error')
            return redirect(url_for('main.dashboard'))
            
        kite.delete_gtt(trigger_id=trigger_id)
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting order: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/order/edit/<int:trigger_id>', methods=['GET', 'POST'])
def edit_order(trigger_id):
    kite = get_kite_instance()
    if kite is None:
        flash('KiteConnect is not available', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            # Get current order details
            current_order = next((o for o in kite.get_gtts() if o['id'] == trigger_id), None)
            if not current_order:
                flash('Order not found', 'error')
                return redirect(url_for('main.dashboard'))

            # Prepare data for modification
            trigger_values = [float(x.strip()) for x in request.form['trigger_values'].split(',')]
            orders = []
            for order in current_order['orders']:
                orders.append({
                    "transaction_type": order['transaction_type'],
                    "quantity": int(request.form['quantity']),
                    "price": float(request.form['price']),
                    "order_type": order['order_type'],
                    "product": order['product']
                })

            # Modify GTT order
            kite.modify_gtt(
                trigger_id=trigger_id,
                trigger_type=current_order['type'],
                tradingsymbol=current_order['condition']['tradingsymbol'],
                exchange=current_order['condition']['exchange'],
                trigger_values=trigger_values,
                last_price=float(request.form['last_price']),
                orders=orders
            )
            
            flash('Order updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            flash(f'Error updating order: {str(e)}', 'error')
            return redirect(url_for('main.edit_order', trigger_id=trigger_id))
            
    try:
        order = next((o for o in kite.get_gtts() if o['id'] == trigger_id), None)
        if order:
            return render_template('edit_order.html', order=order)
        flash('Order not found', 'error')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash(f'Error fetching order details: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/fetch')
def fetch_orders():
    """Fetch GTT orders with search and pagination support"""
    try:
        kite = current_app.config.get('kite')
        if kite is None:
            return jsonify({
                'error': 'KiteConnect is not initialized. Please run AutoConnect.py to generate access_token.txt'
            }), 500

        # Get query parameters
        search = request.args.get('search', '').upper()
        order_type = request.args.get('type', '')
        status = request.args.get('status', '')
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 25))
        except ValueError:
            return jsonify({
                'error': 'Invalid pagination parameters. Page and per_page must be numbers.'
            }), 400

        # Fetch all orders with error handling
        try:
            all_orders = kite.get_gtts()
        except Exception as e:
            # Check for common error types and provide specific messages
            error_msg = str(e)
            if 'token' in error_msg.lower():
                return jsonify({
                    'error': 'Session expired. Please login again using AutoConnect.py'
                }), 401
            elif 'network' in error_msg.lower():
                return jsonify({
                    'error': 'Network error. Please check your internet connection'
                }), 503
            else:
                return jsonify({
                    'error': f'Error fetching orders from Kite: {error_msg}'
                }), 500

        # Apply filters
        filtered_orders = all_orders
        if search:
            filtered_orders = [
                order for order in filtered_orders
                if (search in order['condition']['tradingsymbol'].upper() or
                    search in order['condition']['exchange'].upper() or
                    search in order['type'].upper() or
                    search in order['status'].upper())
            ]
        
        if order_type:
            filtered_orders = [
                order for order in filtered_orders
                if order['type'].lower() == order_type.lower()
            ]
        
        if status:
            filtered_orders = [
                order for order in filtered_orders
                if order['status'].lower() == status.lower()
            ]

        # Calculate pagination
        total_count = len(filtered_orders)
        if total_count == 0:
            return jsonify({
                'records': [],
                'total_count': 0,
                'page': page,
                'per_page': per_page,
                'total_pages': 0,
                'message': 'No orders found matching your criteria'
            })

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_orders = filtered_orders[start_idx:end_idx]

        return jsonify({
            'records': paginated_orders,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })

    except Exception as e:
        # Log the full error for debugging
        current_app.logger.error(f'Unexpected error in fetch_orders: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'An unexpected error occurred. Please try again or contact support if the issue persists.'
        }), 500

@main_bp.route('/test')
def test_page():
    """Serve a simple test page for API testing"""
    return render_template('test.html')

@main_bp.route('/debug-gtt')
def debug_gtt():
    """Serve the GTT debug page"""
    return send_from_directory('.', 'debug_gtt.html')

@main_bp.route('/table-debug')
def table_debug():
    """Debug page for testing table functionality"""
    debug_file = os.path.join(current_app.root_path, 'table_debug.html')
    if os.path.exists(debug_file):
        return send_from_directory(current_app.root_path, 'table_debug.html')
    else:
        return "<h1>Debug file not found</h1>", 404

@main_bp.route('/inspect-gtt')
def inspect_gtt():
    """Inspect the main GTT page structure"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>GTT Page Inspector</title>
        <style>
            body { font-family: monospace; margin: 20px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ccc; }
            .result { background: #f5f5f5; padding: 10px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <h1>GTT Page Inspector</h1>
        
        <div class="section">
            <h2>Test API Endpoint</h2>
            <button onclick="testAPI()">Test API</button>
            <div id="apiResult" class="result"></div>
        </div>
        
        <div class="section">
            <h2>Check Main Page Elements</h2>
            <button onclick="checkMainPage()">Inspect Main Page</button>
            <div id="mainPageResult" class="result"></div>
        </div>
        
        <script>
            async function testAPI() {
                const resultDiv = document.getElementById('apiResult');
                try {
                    const response = await fetch('/api/custom-gtt/orders');
                    const data = await response.json();
                    resultDiv.textContent = 'API Status: ' + response.status + '\\n' + JSON.stringify(data, null, 2);
                } catch (error) {
                    resultDiv.textContent = 'API Error: ' + error.message;
                }
            }
            
            function checkMainPage() {
                const resultDiv = document.getElementById('mainPageResult');
                // Open the main page in a new window for inspection
                const mainWindow = window.open('/custom-gtt', 'mainPage', 'width=1200,height=800');
                
                setTimeout(() => {
                    try {
                        const table = mainWindow.document.getElementById('customGttTable');
                        const tbody = mainWindow.document.getElementById('customGttTableBody');
                        
                        let result = 'Main Page Inspection:\\n';
                        result += 'Table found: ' + (table ? 'YES' : 'NO') + '\\n';
                        result += 'Table body found: ' + (tbody ? 'YES' : 'NO') + '\\n';
                        
                        if (table) {
                            result += 'Table className: ' + table.className + '\\n';
                            result += 'Table style.display: ' + table.style.display + '\\n';
                            result += 'Table offsetHeight: ' + table.offsetHeight + '\\n';
                            result += 'Table offsetWidth: ' + table.offsetWidth + '\\n';
                        }
                        
                        if (tbody) {
                            result += 'Tbody innerHTML length: ' + tbody.innerHTML.length + '\\n';
                            result += 'Tbody children count: ' + tbody.children.length + '\\n';
                        }
                        
                        // Check for JavaScript errors
                        const errors = mainWindow.console.error;
                        result += 'Console errors detected: ' + (errors ? 'YES' : 'NO') + '\\n';
                        
                        resultDiv.textContent = result;
                    } catch (error) {
                        resultDiv.textContent = 'Error inspecting main page: ' + error.message;
                    }
                }, 2000);
            }
        </script>
    </body>
    """

@main_bp.route('/test-table-population')
def test_table_population():
    """Test table population functionality"""
    return send_from_directory(current_app.root_path, 'test_table_population.html')

@main_bp.route('/final-diagnostic')
def final_diagnostic():
    """Final comprehensive diagnostic page"""
    return send_from_directory(current_app.root_path, 'final_diagnostic.html')

@main_bp.route('/direct-debug')
def direct_debug():
    """Direct table debug page without popup windows"""
    return send_from_directory(current_app.root_path, 'direct_table_debug.html')

@main_bp.route('/test_dashboard')
def test_dashboard():
    """Test dashboard page for debugging UI/UX"""
    return send_from_directory('.', 'test_dashboard.html')

@main_bp.route('/debug/kite')
def debug_kite():
    """Debug route to test KiteConnect connection"""
    try:
        kite = get_kite_instance()
        if kite is None:
            return jsonify({
                'status': 'error',
                'message': 'KiteConnect could not be initialized',
                'credentials_available': {
                    'api_key': current_app.config.get('kite_api_key') is not None,
                    'access_token': current_app.config.get('kite_access_token') is not None
                }
            })
        
        # Test basic connection
        try:
            profile = kite.profile()
            return jsonify({
                'status': 'success',
                'message': 'KiteConnect connection working',
                'user': profile.get('user_name'),
                'user_id': profile.get('user_id'),
                'email': profile.get('email')
            })
        except Exception as api_e:
            return jsonify({
                'status': 'error',
                'message': f'KiteConnect API call failed: {str(api_e)}',
                'error_type': type(api_e).__name__
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Debug route error: {str(e)}',
            'error_type': type(e).__name__
        })