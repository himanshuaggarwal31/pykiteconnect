from flask import Blueprint, render_template, request, jsonify, current_app
from models.custom_gtt import (
    get_custom_gtt_orders, add_custom_gtt_order, update_custom_gtt_order,
    delete_custom_gtt_order, update_kite_status, reset_kite_status,
    get_orders_not_on_kite
)

custom_gtt_bp = Blueprint('custom_gtt', __name__, url_prefix='/custom-gtt')

def check_gtt_conflict(kite, symbol, order_type):
    """Check if a similar GTT exists for the symbol"""
    try:
        existing_gtts = kite.get_gtts()
        for gtt in existing_gtts:
            if (gtt['condition']['tradingsymbol'] == symbol and 
                gtt['orders'][0]['transaction_type'] == order_type):
                return True
        return False
    except:
        return False  # In case of API error, allow order placement

def validate_trigger_prices(order_type, last_price, trigger_values):
    """
    Validate trigger prices based on order type and last price
    For BUY: trigger price should be lower than last price
    For SELL: trigger price should be higher than last price
    Returns a tuple of (bool, str) where bool indicates if valid and str contains any error message
    """
    error_msg = None
    
    try:
        # Convert all values to float for comparison
        last_price = float(last_price)
        trigger_values = [float(price) for price in trigger_values]
        
        if order_type == 'BUY':
            invalid_prices = [price for price in trigger_values if price >= last_price]
            if invalid_prices:
                error_msg = f"For BUY orders, trigger price(s) {invalid_prices} must be lower than current market price ({last_price})"
                return False, error_msg
        else:  # SELL
            invalid_prices = [price for price in trigger_values if price <= last_price]
            if invalid_prices:
                error_msg = f"For SELL orders, trigger price(s) {invalid_prices} must be higher than current market price ({last_price})"
                return False, error_msg
                
        return True, None
        
    except ValueError as e:
        return False, f"Invalid price values: {str(e)}"

def prepare_gtt_order(order, kite):
    """Prepare GTT order with proper price validation"""
    try:
        # Get the current market price if not provided
        if not order.get('last_price'):
            instrument = f"NSE:{order['symbol']}"
            quote = kite.quote([instrument])
            last_price = quote[instrument]['last_price']
            
            # Update the order with current market price
            from models.custom_gtt import update_custom_gtt_order
            update_custom_gtt_order(order['id'], {'last_price': last_price})
        else:
            last_price = float(order['last_price'])
        
        # Prepare trigger values
        trigger_values = []
        if order.get('target_price'):
            trigger_values.append(float(order['target_price']))
        if order.get('stop_loss'):
            trigger_values.append(float(order['stop_loss']))
        if not trigger_values:
            trigger_values = [float(order['trigger_price'])]

        # Validate trigger prices
        is_valid, error_message = validate_trigger_prices(order['order_type'], last_price, trigger_values)
        if not is_valid:
            raise ValueError(error_message)

        # Sort trigger values appropriately (higher to lower for BUY, lower to higher for SELL)
        trigger_values = sorted(trigger_values, reverse=(order['order_type'] == 'BUY'))

        # Prepare orders list
        kite_orders = []
        if len(trigger_values) == 1:
            kite_orders = [{
                "transaction_type": order['order_type'],
                "quantity": int(order['quantity']),
                "price": trigger_values[0],
                "order_type": "LIMIT",
                "product": "CNC"
            }]
        elif len(trigger_values) == 2:
            # For BUY: target is lower, stop-loss is higher
            # For SELL: target is higher, stop-loss is lower
            target, stop_loss = trigger_values if order['order_type'] == 'SELL' else reversed(trigger_values)
            
            kite_orders = [
                {
                    "transaction_type": order['order_type'],
                    "quantity": int(order['quantity']),
                    "price": target,
                    "order_type": "LIMIT",
                    "product": "CNC"
                },
                {
                    "transaction_type": order['order_type'],
                    "quantity": int(order['quantity']),
                    "price": stop_loss,
                    "order_type": "LIMIT",
                    "product": "CNC"
                }
            ]

        return {
            "trigger_type": "single" if len(trigger_values) == 1 else "two-leg",
            "tradingsymbol": order['symbol'],
            "exchange": "NSE",
            "trigger_values": trigger_values,
            "last_price": last_price,
            "orders": kite_orders
        }
    except Exception as e:
        raise ValueError(f"Error preparing order for {order['symbol']}: {str(e)}")

@custom_gtt_bp.route('/')
def index():
    """Render the custom GTT orders page"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        order_type = request.args.get('order_type', '')
        kite_status = request.args.get('kite_status', '')
        
        # Validate per_page
        per_page = min(max(per_page, 5), 100)
        
        result = get_custom_gtt_orders(
            page=page,
            per_page=per_page,
            order_type=order_type,
            kite_status=kite_status
        )
        
        return render_template(
            'custom_gtt/index.html',
            orders=result['records'],
            total_count=result['total_count'],
            page=result['page'],
            per_page=result['per_page'],
            total_pages=result['total_pages']
        )
    except Exception as e:
        return render_template('custom_gtt/index.html', orders=[], error=str(e))

@custom_gtt_bp.route('/fetch')
def fetch():
    """Fetch custom GTT orders with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        order_type = request.args.get('order_type', '')
        kite_status = request.args.get('kite_status', '')
        
        # Validate per_page
        per_page = min(max(per_page, 5), 100)
        
        result = get_custom_gtt_orders(
            page=page,
            per_page=per_page,
            order_type=order_type,
            kite_status=kite_status
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/add', methods=['POST'])
def add():
    """Add a new custom GTT order"""
    try:
        data = request.json
        order_id = add_custom_gtt_order(data)
        return jsonify({'id': order_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/update/<int:order_id>', methods=['POST'])
def update(order_id):
    """Update a custom GTT order"""
    try:
        data = request.json
        success = update_custom_gtt_order(order_id, data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/delete/<int:order_id>', methods=['POST'])
def delete(order_id):
    """Delete a custom GTT order"""
    try:
        success = delete_custom_gtt_order(order_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/place-on-kite/<int:order_id>', methods=['POST'])
def place_on_kite(order_id):
    """Place a custom GTT order on Kite"""
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized'}), 500

    try:
        orders = get_custom_gtt_orders()
        order = next((o for o in orders if o['id'] == order_id), None)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Check for conflicts
        if check_gtt_conflict(kite, order['symbol'], order['order_type']):
            return jsonify({'error': 'Similar GTT already exists'}), 400

        # Prepare and validate GTT order
        gtt_params = prepare_gtt_order(order, kite)
        
        # Place GTT order
        result = kite.place_gtt(**gtt_params)

        # Update local database
        update_kite_status(order_id, result['trigger_id'])

        return jsonify({
            'message': 'GTT order placed successfully',
            'trigger_id': result['trigger_id']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/place-multiple', methods=['POST'])
def place_multiple():
    """Place multiple custom GTT orders on Kite"""
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized'}), 500

    try:
        data = request.json
        order_ids = data.get('order_ids', [])
        if not order_ids:
            return jsonify({'error': 'No orders selected'}), 400

        # Get all orders not on Kite
        available_orders = {str(order['id']): order for order in get_orders_not_on_kite()}
        
        # Filter selected orders that are not yet on Kite
        selected_orders = [available_orders[str(id)] for id in order_ids if str(id) in available_orders]
        
        if not selected_orders:
            return jsonify({'error': 'No eligible orders found to place on Kite'}), 400

        success_count = 0
        errors = []

        for order in selected_orders:
            try:
                # Check for conflicts
                if check_gtt_conflict(kite, order['symbol'], order['order_type']):
                    errors.append(f"Order for {order['symbol']}: Similar GTT already exists")
                    continue

                # Prepare and validate GTT order
                gtt_params = prepare_gtt_order(order, kite)
                
                # Place GTT order
                result = kite.place_gtt(**gtt_params)

                # Update local database
                update_kite_status(order['id'], result['trigger_id'])
                success_count += 1

            except Exception as e:
                errors.append(f"Order for {order['symbol']}: {str(e)}")

        return jsonify({
            'success_count': success_count,
            'error_count': len(errors),
            'errors': errors
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/reset-kite-status/<int:order_id>', methods=['POST'])
def reset_kite(order_id):
    """Reset Kite placement status for a custom GTT order"""
    try:
        success = reset_kite_status(order_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/place', methods=['POST'])
def place_gtt_order():
    try:
        data = request.get_json()
        # Log the incoming data for debugging
        print('Received /place payload:', data, flush=True)
        # Only use required fields for Kite
        tradingsymbol = data.get('tradingsymbol')
        exchange = data.get('exchange')
        trigger_type = data.get('trigger_type')
        trigger_values = data.get('trigger_values')
        last_price = data.get('last_price')
        transaction_type = data.get('transaction_type')
        quantity = data.get('quantity')
        # Here you would call your Kite API logic, e.g. place_gtt_order_kite(...)
        # For now, just return the received payload for debug
        return jsonify({'success': True, 'received': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/place-multi', methods=['POST'])
def place_multi_gtt_orders():
    try:
        data = request.get_json()
        print('Received /place-multi payload:', data, flush=True)
        orders = data.get('orders', [])
        results = []
        for order in orders:
            tradingsymbol = order.get('tradingsymbol')
            exchange = order.get('exchange')
            trigger_type = order.get('trigger_type')
            trigger_values = order.get('trigger_values')
            last_price = order.get('last_price')
            transaction_type = order.get('transaction_type')
            quantity = order.get('quantity')
            # Here you would call your Kite API logic for each order
            # For now, just append the received order for debug
            results.append({'tradingsymbol': tradingsymbol, 'received': order, 'success': True})
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
