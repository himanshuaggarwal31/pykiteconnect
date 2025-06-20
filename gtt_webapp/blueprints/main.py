from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    try:
        kite = current_app.config.get('kite')
        if kite is None:
            flash('KiteConnect is not initialized. Please check if access_token.txt exists.', 'error')
            return render_template('dashboard.html', orders=[], error=True)
            
        gtt_orders = kite.get_gtts()
        return render_template('dashboard.html', orders=gtt_orders, error=False)
    except Exception as e:
        error_msg = str(e)
        flash(f'Error fetching GTT orders: {error_msg}', 'error')
        return render_template('dashboard.html', orders=[], error=True)

@main_bp.route('/order/<int:trigger_id>')
def order_detail(trigger_id):
    try:
        kite = current_app.config['kite']
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
        kite = current_app.config['kite']
        kite.delete_gtt(trigger_id=trigger_id)
        flash('Order deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting order: {str(e)}', 'error')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/order/edit/<int:trigger_id>', methods=['GET', 'POST'])
def edit_order(trigger_id):
    kite = current_app.config['kite']
    
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
