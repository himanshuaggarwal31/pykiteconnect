from flask import Blueprint, render_template, request, jsonify, current_app
import logging
from datetime import datetime

holdings_bp = Blueprint('holdings', __name__)
logger = logging.getLogger('holdings')

def get_kite_instance():
    """Get KiteConnect instance from app config"""
    return current_app.config.get('kite')

@holdings_bp.route('/')
def index():
    """Display holdings page"""
    try:
        kite = get_kite_instance()
        if kite is None:
            logger.warning("KiteConnect is not available in holdings route")
            return render_template('holdings/index.html', holdings=[], error=True)
        
        logger.debug("Attempting to fetch holdings...")
        holdings = kite.holdings()
        logger.info(f"Successfully fetched {len(holdings)} holdings")
        
        return render_template('holdings/index.html', holdings=holdings, error=False)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in holdings route: {error_msg}", exc_info=True)
        
        # Provide more specific error messages
        if "403" in error_msg or "TokenException" in error_msg:
            error_message = f'Access token error: {error_msg}. Please regenerate your access token.'
        elif "NetworkException" in error_msg:
            error_message = f'Network error: {error_msg}. Please check your internet connection.'
        elif "General" in error_msg and "exception" in error_msg.lower():
            error_message = f'API error: {error_msg}. Please check your API key and token.'
        else:
            error_message = f'Error fetching holdings: {error_msg}'
            
        return render_template('holdings/index.html', holdings=[], error=True, error_message=error_message)

@holdings_bp.route('/api/holdings')
def api_holdings():
    """API endpoint to fetch holdings data"""
    try:
        kite = get_kite_instance()
        if kite is None:
            return jsonify({'error': 'KiteConnect is not available. Please check access_token.txt.'}), 500
        
        holdings = kite.holdings()
        
        # Calculate totals
        total_investment = sum(float(h.get('average_price', 0)) * float(h.get('quantity', 0)) for h in holdings)
        total_current_value = sum(float(h.get('last_price', 0)) * float(h.get('quantity', 0)) for h in holdings)
        total_pnl = total_current_value - total_investment
        total_pnl_percentage = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        
        return jsonify({
            'holdings': holdings,
            'summary': {
                'total_investment': round(total_investment, 2),
                'total_current_value': round(total_current_value, 2),
                'total_pnl': round(total_pnl, 2),
                'total_pnl_percentage': round(total_pnl_percentage, 2),
                'total_holdings': len(holdings)
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching holdings via API: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@holdings_bp.route('/api/holdings/<tradingsymbol>')
def api_holding_detail(tradingsymbol):
    """API endpoint to fetch specific holding details"""
    try:
        kite = get_kite_instance()
        if kite is None:
            return jsonify({'error': 'KiteConnect is not available. Please check access_token.txt.'}), 500
        
        holdings = kite.holdings()
        holding = next((h for h in holdings if h.get('tradingsymbol') == tradingsymbol), None)
        
        if not holding:
            return jsonify({'error': 'Holding not found'}), 404
            
        return jsonify(holding)
        
    except Exception as e:
        logger.error(f"Error fetching holding detail for {tradingsymbol}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@holdings_bp.route('/api/auctions')
def api_auctions():
    """API endpoint to fetch auction instruments"""
    try:
        kite = get_kite_instance()
        if kite is None:
            return jsonify({'error': 'KiteConnect is not available. Please check access_token.txt.'}), 500
        
        auctions = kite.auctions()
        return jsonify({'auctions': auctions, 'total': len(auctions)})
        
    except Exception as e:
        logger.error(f"Error fetching auctions: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@holdings_bp.route('/api/sell/market', methods=['POST'])
def sell_market_order():
    """Place a market sell order for a holding"""
    try:
        kite = get_kite_instance()
        if kite is None:
            return jsonify({'error': 'KiteConnect is not available. Please check access_token.txt.'}), 500
        
        data = request.get_json()
        tradingsymbol = data.get('tradingsymbol')
        exchange = data.get('exchange', 'NSE')
        quantity = data.get('quantity')
        product = data.get('product', 'CNC')
        
        if not all([tradingsymbol, quantity]):
            return jsonify({'error': 'Missing required fields: tradingsymbol, quantity'}), 400
        
        # Place market sell order
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=int(quantity),
            product=product,
            order_type=kite.ORDER_TYPE_MARKET
        )
        
        logger.info(f"Market sell order placed: {order_id} for {quantity} shares of {tradingsymbol}")
        
        return jsonify({
            'message': 'Market sell order placed successfully',
            'order_id': order_id,
            'order_details': {
                'tradingsymbol': tradingsymbol,
                'exchange': exchange,
                'quantity': quantity,
                'order_type': 'MARKET',
                'transaction_type': 'SELL',
                'product': product
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error placing market sell order: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@holdings_bp.route('/api/sell/gtt', methods=['POST'])
def sell_gtt_order():
    """Place a GTT sell order (single-leg or two-leg) for a holding"""
    try:
        kite = get_kite_instance()
        if kite is None:
            return jsonify({'error': 'KiteConnect is not available. Please check access_token.txt.'}), 500
        
        data = request.get_json()
        tradingsymbol = data.get('tradingsymbol')
        exchange = data.get('exchange', 'NSE')
        quantity = data.get('quantity')
        product = data.get('product', 'CNC')
        trigger_type = data.get('trigger_type')  # 'single' or 'two-leg'
        trigger_prices = data.get('trigger_prices', [])
        last_price = data.get('last_price')
        
        if not all([tradingsymbol, quantity, trigger_type, trigger_prices, last_price]):
            return jsonify({'error': 'Missing required fields: tradingsymbol, quantity, trigger_type, trigger_prices, last_price'}), 400
        
        if trigger_type not in ['single', 'two-leg']:
            return jsonify({'error': 'Invalid trigger_type. Must be "single" or "two-leg"'}), 400
        
        # Validate trigger prices based on type
        if trigger_type == 'single' and len(trigger_prices) != 1:
            return jsonify({'error': 'Single-leg GTT requires exactly 1 trigger price'}), 400
        elif trigger_type == 'two-leg' and len(trigger_prices) != 2:
            return jsonify({'error': 'Two-leg GTT requires exactly 2 trigger prices'}), 400
        
        # Create orders based on trigger type
        if trigger_type == 'single':
            orders = [{
                "exchange": exchange,
                "tradingsymbol": tradingsymbol,
                "transaction_type": kite.TRANSACTION_TYPE_SELL,
                "quantity": int(quantity),
                "order_type": kite.ORDER_TYPE_LIMIT,
                "product": product,
                "price": float(trigger_prices[0])
            }]
            kite_trigger_type = kite.GTT_TYPE_SINGLE
        else:  # two-leg
            orders = [
                {
                    "exchange": exchange,
                    "tradingsymbol": tradingsymbol,
                    "transaction_type": kite.TRANSACTION_TYPE_SELL,
                    "quantity": int(quantity),
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": product,
                    "price": float(trigger_prices[0])
                },
                {
                    "exchange": exchange,
                    "tradingsymbol": tradingsymbol,
                    "transaction_type": kite.TRANSACTION_TYPE_SELL,
                    "quantity": int(quantity),
                    "order_type": kite.ORDER_TYPE_LIMIT,
                    "product": product,
                    "price": float(trigger_prices[1])
                }
            ]
            kite_trigger_type = kite.GTT_TYPE_OCO
        
        # Place GTT order
        result = kite.place_gtt(
            trigger_type=kite_trigger_type,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            trigger_values=trigger_prices,
            last_price=float(last_price),
            orders=orders
        )
        
        logger.info(f"GTT sell order placed: trigger_id={result.get('trigger_id')} for {quantity} shares of {tradingsymbol}")
        
        return jsonify({
            'message': 'GTT sell order placed successfully',
            'trigger_id': result.get('trigger_id'),
            'order_details': {
                'tradingsymbol': tradingsymbol,
                'exchange': exchange,
                'quantity': quantity,
                'trigger_type': trigger_type,
                'trigger_prices': trigger_prices,
                'last_price': last_price,
                'transaction_type': 'SELL',
                'product': product
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error placing GTT sell order: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@holdings_bp.route('/api/check-gtt-exists-bulk', methods=['POST'])
def check_gtt_exists_bulk():
    """Check if GTT orders exist for multiple symbols using Oracle database lookup"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400
        
        # Validate symbols format (should be list of dicts with tradingsymbol and exchange)
        if not all(isinstance(symbol, dict) and 'tradingsymbol' in symbol and 'exchange' in symbol for symbol in symbols):
            return jsonify({'error': 'Symbols must be objects with tradingsymbol and exchange fields'}), 400
        
        # Import Oracle database connection
        from db_config import get_connection
        
        # Connect to Oracle database
        with get_connection() as connection:
            cursor = connection.cursor()
            
            # Prepare query to check for existing GTT orders
            # We check for active status only
            query = """
                SELECT DISTINCT tradingsymbol, texchange 
                FROM ADMIN.KITE_GTTS 
                WHERE tradingsymbol = :tradingsymbol 
                AND texchange = :exchange 
                AND status = 'active'
            """
            
            results = {}
            for symbol in symbols:
                tradingsymbol = symbol['tradingsymbol']
                exchange = symbol['exchange']
                
                # Execute query for this symbol
                cursor.execute(query, {
                    'tradingsymbol': tradingsymbol,
                    'exchange': exchange
                })
                
                # Check if any records found
                found_records = cursor.fetchall()
                symbol_key = f"{exchange}:{tradingsymbol}"
                results[symbol_key] = len(found_records) > 0
                
                logger.debug(f"GTT check for {symbol_key}: {len(found_records)} active GTT orders found")
        
        logger.info(f"Bulk GTT existence check completed for {len(symbols)} symbols")
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error checking GTT existence in bulk: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
