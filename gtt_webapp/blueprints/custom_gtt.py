from flask import Blueprint, render_template, request, jsonify, current_app
import logging
from models.custom_gtt import (
    get_custom_gtt_orders, add_custom_gtt_order, update_custom_gtt_order,
    delete_custom_gtt_order, update_kite_status, reset_kite_status,
    get_orders_not_on_kite, get_order_by_id, place_order_on_kite,
    place_multiple_orders_on_kite
)

custom_gtt_bp = Blueprint('custom_gtt', __name__, url_prefix='/custom-gtt')

# Configure logging
logger = logging.getLogger('custom_data')

def check_gtt_conflict(kite, symbol, order_type):
    """Check if a similar GTT exists for the symbol"""
    try:
        existing_gtts = kite.get_gtts()
        for gtt in existing_gtts:
            if (gtt['condition']['tradingsymbol'] == symbol and 
                gtt['orders'][0]['transaction_type'] == order_type):
                return True
        return False
    except Exception as e:
        logger.error(f"[ERROR][check_gtt_conflict] Error checking for GTT conflicts: {str(e)}", exc_info=True)
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
            instrument = f"{order.get('exchange', 'NSE')}:{order['symbol']}"
            quote = kite.quote([instrument])
            last_price = quote[instrument]['last_price']
            
            # Update the order with current market price
            update_custom_gtt_order(order['id'], {'last_price': last_price})
        else:
            last_price = float(order['last_price'])
        
        # Prepare trigger values
        trigger_values = []
        if order.get('trigger_type') == 'two-leg':
            if order.get('target_price') and order.get('stop_loss'):
                trigger_values = [float(order['stop_loss']), float(order['target_price'])]
            elif order.get('trigger_values'):
                trigger_values = [float(val.strip()) for val in str(order['trigger_values']).split(',')]
        elif order.get('trigger_price'):
            trigger_values = [float(order['trigger_price'])]
        else:
            raise ValueError("No trigger values provided")

        # Validate trigger prices
        is_valid, error_message = validate_trigger_prices(order['order_type'], last_price, trigger_values)
        if not is_valid:
            raise ValueError(error_message)

        return {
            'trigger_type': order['trigger_type'],
            'tradingsymbol': order['symbol'],
            'exchange': order.get('exchange', 'NSE'),
            'trigger_values': trigger_values,
            'last_price': last_price,
            'quantity': int(order['quantity']),
            'order_type': order['order_type']
        }
    except Exception as e:
        logger.error(f"[ERROR][prepare_gtt_order] Failed to prepare GTT order: {str(e)}", exc_info=True)
        raise

@custom_gtt_bp.route('/')
def index():
    """Render the custom GTT orders page"""
    try:
        kite = current_app.config.get('kite')
        error = None
        if not kite:
            error = "Kite connection not available. Please make sure you have valid access token."
        
        return render_template('custom_gtt/index.html', error=error)
    except Exception as e:
        logger.error(f"[ERROR][index] Error rendering index page: {str(e)}", exc_info=True)
        return render_template('custom_gtt/index.html', error=str(e))

@custom_gtt_bp.route('/fetch')
def fetch():
    """API endpoint to fetch custom GTT orders with filtering and pagination"""
    try:
        # Get query parameters
        search = request.args.get('search', '')
        order_type = request.args.get('order_type', '')
        kite_status = request.args.get('kite_status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        
        # Get orders from database
        orders = get_custom_gtt_orders(
            search=search,
            order_type=order_type,
            kite_status=kite_status,
            page=page,
            per_page=per_page
        )
        
        return jsonify(orders)
    except Exception as e:
        logger.error(f"[ERROR][fetch] Error fetching orders: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'records': [],
            'total_count': 0
        })

@custom_gtt_bp.route('/add', methods=['POST'])
def add():
    """Add a new custom GTT order"""
    try:
        data = request.form.to_dict()
        logger.debug(f"[DEBUG][add] Adding new order with data: {data}")
        
        # Validate required fields
        required_fields = ['symbol', 'order_type', 'quantity']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400
        
        # Add order to database
        order_id = add_custom_gtt_order(data)
        
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        logger.error(f"[ERROR][add] Error adding order: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/update/<int:order_id>', methods=['POST'])
def update(order_id):
    """Update an existing custom GTT order"""
    try:
        data = request.form.to_dict()
        logger.debug(f"[DEBUG][update] Updating order {order_id} with data: {data}")
        
        update_custom_gtt_order(order_id, data)
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"[ERROR][update] Error updating order {order_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/delete/<int:order_id>', methods=['POST'])
def delete(order_id):
    """Delete a custom GTT order"""
    try:
        logger.debug(f"[DEBUG][delete] Deleting order {order_id}")
        delete_custom_gtt_order(order_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"[ERROR][delete] Error deleting order {order_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/place-on-kite/<int:order_id>', methods=['POST'])
def place_on_kite(order_id):
    """Place a custom GTT order on Kite"""
    try:
        logger.debug(f"[DEBUG][place_on_kite] Placing order {order_id} on Kite")
        kite = current_app.config.get('kite')
        
        if not kite:
            logger.error("[ERROR][place_on_kite] Kite connection not available")
            return jsonify({'error': 'Kite connection not available'}), 500
        
        # Get order details
        order = get_order_by_id(order_id)
        if not order:
            return jsonify({'error': f'Order {order_id} not found'}), 404
        
        # Check for existing GTT with same symbol and order type
        if check_gtt_conflict(kite, order['symbol'], order['order_type']):
            return jsonify({'error': f"A similar GTT order for {order['symbol']} with {order['order_type']} already exists on Kite"}), 400
        
        # Place the order on Kite
        result = place_order_on_kite(order_id, kite)
        
        return jsonify({
            'success': True,
            'trigger_id': result.get('trigger_id'),
            'message': f"Order placed on Kite with trigger ID {result.get('trigger_id')}"
        })
    except Exception as e:
        logger.error(f"[ERROR][place_on_kite] Error placing order {order_id} on Kite: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/place-multiple', methods=['POST'])
def place_multiple():
    """Place multiple custom GTT orders on Kite"""
    try:
        kite = current_app.config.get('kite')
        if not kite:
            logger.error("[ERROR][place_multiple] Kite connection not available")
            return jsonify({'error': 'Kite connection not available'}), 500
        
        # Get order IDs from request
        order_ids = request.json.get('order_ids', [])
        if not order_ids:
            return jsonify({'error': 'No order IDs provided'}), 400
        
        logger.debug(f"[DEBUG][place_multiple] Placing multiple orders: {order_ids}")
        
        # Check for conflicts first
        conflicts = []
        for order_id in order_ids:
            order = get_order_by_id(order_id)
            if not order:
                continue
                
            if check_gtt_conflict(kite, order['symbol'], order['order_type']):
                conflicts.append(f"{order['symbol']} ({order['order_type']})")
        
        if conflicts:
            return jsonify({
                'error': f"Similar GTT orders already exist on Kite for: {', '.join(conflicts)}",
                'conflicts': conflicts
            }), 400
        
        # Place orders on Kite
        results = place_multiple_orders_on_kite(order_ids, kite)
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f"Successfully placed {len(results['success'])} orders, {len(results['failed'])} failed"
        })
    except Exception as e:
        logger.error(f"[ERROR][place_multiple] Error placing multiple orders: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/reset-kite-status/<int:order_id>', methods=['POST'])
def reset_status(order_id):
    """Reset Kite status for a custom GTT order"""
    try:
        logger.debug(f"[DEBUG][reset_status] Resetting Kite status for order {order_id}")
        reset_kite_status(order_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"[ERROR][reset_status] Error resetting Kite status for order {order_id}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@custom_gtt_bp.route('/get-last-price', methods=['GET'])
def get_last_price():
    """Get the latest price for a symbol"""
    try:
        symbol = request.args.get('symbol')
        exchange = request.args.get('exchange', 'NSE')
        
        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400
        
        kite = current_app.config.get('kite')
        if not kite:
            logger.error("[ERROR][get_last_price] Kite connection not available")
            return jsonify({'error': 'Kite connection not available'}), 500
        
        instrument = f"{exchange}:{symbol}"
        logger.debug(f"[DEBUG][get_last_price] Getting last price for {instrument}")
        
        try:
            quote = kite.quote([instrument])
            last_price = quote[instrument]['last_price']
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'exchange': exchange,
                'last_price': last_price
            })
        except Exception as e:
            logger.error(f"[ERROR][get_last_price] Error getting quote for {instrument}: {str(e)}", exc_info=True)
            return jsonify({'error': f"Could not get price for {symbol}: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"[ERROR][get_last_price] Error getting last price: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
