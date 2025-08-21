from flask import Blueprint, request, jsonify, current_app
import logging
from models.custom_gtt import (
    get_custom_gtt_orders, add_custom_gtt_order, update_custom_gtt_order,
    delete_custom_gtt_order, get_order_by_id, place_order_on_kite, 
    place_multiple_orders_on_kite, delete_multiple_orders, update_kite_status, reset_kite_status
)

custom_gtt_api = Blueprint('custom_gtt_api', __name__)

# Configure logging
logger = logging.getLogger('custom_data')

@custom_gtt_api.route('/save-order', methods=['POST'])
def save_order():
    """Save a new GTT order to the database (not sent to Kite)"""
    try:
        # Log request information for debugging
        logger.debug(f"[API] Save order request method: {request.method}")
        logger.debug(f"[API] Save order request content type: {request.content_type}")
        logger.debug(f"[API] Save order request headers: {dict(request.headers)}")
        
        if not request.is_json:
            logger.error(f"[API] Request is not JSON. Content-Type: {request.content_type}")
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
            
        # Try to parse JSON data
        try:
            data = request.json
            logger.debug(f"[API] Save order request data: {data}")
            
            # Validate that data is not None and is a dict
            if data is None:
                logger.error(f"[API] Request JSON data is None")
                return jsonify({
                    'success': False,
                    'error': 'Request JSON data is empty or None'
                }), 400
                
            if not isinstance(data, dict):
                logger.error(f"[API] Request JSON data is not a dictionary: {type(data)}")
                return jsonify({
                    'success': False,
                    'error': f'Request JSON data must be an object/dictionary, got {type(data).__name__}'
                }), 400
                
        except Exception as json_err:
            logger.error(f"[API] Error parsing JSON data: {str(json_err)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Error parsing JSON data: {str(json_err)}'
            }), 400
        
        # Validate required fields - use safer get method with proper fallback
        required_fields = ['symbol', 'order_type', 'trigger_type', 'quantity']
        missing_fields = []
        
        for field in required_fields:
            try:
                field_value = data.get(field) if hasattr(data, 'get') else data[field] if field in data else None
                if not field_value:
                    missing_fields.append(field)
            except (KeyError, AttributeError, TypeError) as field_err:
                logger.error(f"[API] Error accessing field '{field}': {str(field_err)}")
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"[API] Missing required fields: {missing_fields}")
            return jsonify({
                'success': False, 
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Ensure company name is properly handled as optional
        if 'company_name' in data and not data['company_name']:
            data['company_name'] = None
        
        # Add order to database
        order_id = add_custom_gtt_order(data)
        logger.info(f"[API] Order saved successfully with ID: {order_id}")
        
        # Fetch the complete order with all fields
        order_data = get_order_by_id(order_id) if order_id else None
        
        # Set explicit content type and return JSON
        response = jsonify({
            'success': True,
            'message': 'Order saved successfully',
            'order_id': order_id,
            'order': order_data  # Return complete order for UI refresh
        })
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        logger.error(f"[API] Error saving order: {str(e)}", exc_info=True)
        response = jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        })
        response.headers['Content-Type'] = 'application/json'
        return response, 500
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/update-order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    """Update an existing GTT order"""
    try:
        data = request.json
        logger.debug(f"[API] Update order request data for ID {order_id}: {data}")
        
        update_custom_gtt_order(order_id, data)
        logger.info(f"[API] Order {order_id} updated successfully")
        
        return jsonify({
            'success': True,
            'message': f'Order {order_id} updated successfully'
        })
    except Exception as e:
        logger.error(f"[API] Error updating order {order_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/orders', methods=['GET'])
def get_orders():
    """Get all saved GTT orders"""
    try:
        # Log the request for debugging
        logger.info(f"[API] GET /orders request received with args: {request.args}")
        
        # Get query parameters for filtering and sorting
        search = request.args.get('search', '')
        advanced_search = request.args.get('advanced_search', '')
        order_type = request.args.get('order_type', '')
        kite_status = request.args.get('kite_status', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        sort_by = request.args.get('sort_by', '')
        sort_order = request.args.get('sort_order', 'asc')
        
        logger.debug(f"[API] Filtered parameters: search='{search}', advanced_search='{advanced_search}', order_type='{order_type}', kite_status='{kite_status}', page={page}, per_page={per_page}, sort_by='{sort_by}', sort_order='{sort_order}'")
        
        # Get orders from database
        orders = get_custom_gtt_orders(
            search=search,
            advanced_search=advanced_search,
            order_type=order_type,
            kite_status=kite_status,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        logger.info(f"[API] Retrieved {len(orders['records'])} orders out of {orders['total_count']} total")
        
        return jsonify(orders)
    except Exception as e:
        logger.error(f"[API] Error getting orders: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'records': []
        }), 500

@custom_gtt_api.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get a specific GTT order by ID"""
    try:
        order = get_order_by_id(order_id)
        if not order:
            return jsonify({
                'success': False,
                'error': f'Order with ID {order_id} not found'
            }), 404
            
        return jsonify({
            'success': True,
            'order': order
        })
    except Exception as e:
        logger.error(f"[API] Error getting order {order_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/delete-order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    """Delete a GTT order"""
    try:
        deleted = delete_custom_gtt_order(order_id)
        if not deleted:
            return jsonify({
                'success': False,
                'error': f'Order with ID {order_id} not found or could not be deleted'
            }), 404
            
        logger.info(f"[API] Order {order_id} deleted successfully")
        return jsonify({
            'success': True,
            'message': f'Order {order_id} deleted successfully'
        })
    except Exception as e:
        logger.error(f"[API] Error deleting order {order_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/place-order/<int:order_id>', methods=['POST'])
def place_order(order_id):
    """Place a specific GTT order on Kite"""
    try:
        # Get Kite connection from the app
        kite = current_app.config.get('kite')
        if not kite:
            logger.error("[API] Kite connection not available")
            return jsonify({
                'success': False,
                'error': 'Kite connection not available'
            }), 500
        
        result = place_order_on_kite(order_id, kite)
        logger.info(f"[API] Order {order_id} placed on Kite with trigger ID {result.get('trigger_id')}")
        return jsonify({
            'success': True,
            'message': f'Order placed on Kite with trigger ID {result.get("trigger_id")}',
            'trigger_id': result.get('trigger_id')
        })
    except Exception as e:
        logger.error(f"[API] Error placing order {order_id} on Kite: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/place-orders', methods=['POST'])
def place_multiple_orders():
    """Place multiple GTT orders on Kite"""
    try:
        # Get Kite connection from the app
        kite = current_app.config.get('kite')
        if not kite:
            logger.error("[API] Kite connection not available")
            return jsonify({
                'success': False,
                'error': 'Kite connection not available'
            }), 500
        
        # Get order IDs from request
        data = request.json
        order_ids = data.get('order_ids', [])
        if not order_ids:
            return jsonify({
                'success': False,
                'error': 'No order IDs provided'
            }), 400
        
        # Place orders on Kite
        results = place_multiple_orders_on_kite(order_ids, kite)
        logger.info(f"[API] {len(results['success'])} orders placed successfully, {len(results['failed'])} failed")
        
        return jsonify({
            'success': True,
            'message': f"{len(results['success'])} orders placed successfully",
            'results': results
        })
    except Exception as e:
        logger.error(f"[API] Error placing multiple orders: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/delete-orders', methods=['POST'])
def delete_multiple_orders_api():
    """Delete multiple GTT orders"""
    try:
        # Get order IDs from request
        data = request.json
        order_ids = data.get('order_ids', [])
        if not order_ids:
            return jsonify({
                'success': False,
                'error': 'No order IDs provided'
            }), 400
        
        # Delete orders
        results = delete_multiple_orders(order_ids)
        logger.info(f"[API] {len(results['success'])} orders deleted successfully, {len(results['failed'])} failed")
        
        return jsonify({
            'success': True,
            'message': f"{len(results['success'])} orders deleted successfully",
            'results': results
        })
    except Exception as e:
        logger.error(f"[API] Error deleting multiple orders: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/get-latest-price/<symbol>', methods=['GET'])
def get_latest_price(symbol):
    """Get the latest price for a trading symbol"""
    try:
        # Get Kite connection from the app
        kite = current_app.config.get('kite')
        if not kite:
            logger.error("[API] Kite connection not available")
            return jsonify({
                'success': False,
                'error': 'Kite connection not available'
            }), 500
        
        # Get exchange from query parameter, default to NSE
        exchange = request.args.get('exchange', 'NSE')
        instrument = f"{exchange}:{symbol}"
        
        # Get quote from Kite
        quote = kite.quote([instrument])
        if instrument not in quote:
            return jsonify({
                'success': False,
                'error': f'Symbol {symbol} not found on {exchange}'
            }), 404
            
        latest_price = quote[instrument]['last_price']
        logger.info(f"[API] Latest price for {instrument}: {latest_price}")
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'exchange': exchange,
            'latest_price': latest_price,
            'quote_data': quote[instrument]
        })
    except Exception as e:
        logger.error(f"[API] Error fetching latest price for {symbol}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@custom_gtt_api.route('/get-symbol-info/<symbol>', methods=['GET'])
def get_symbol_info(symbol):
    """Get comprehensive symbol information from NIFTY_MCAP and STOCK_DATA tables"""
    connection = None
    cursor = None
    try:
        from db_config import get_connection
        
        symbol_upper = symbol.upper()
        exchange = request.args.get('exchange', 'NSE')
        
        connection = get_connection()
        cursor = connection.cursor()
        
        # Get company details from NIFTY_MCAP table
        nifty_query = """
            SELECT symbol, company_name, mcap_lakhs, nifty_rank, him_rating, rating_date
            FROM ADMIN.NIFTY_MCAP
            WHERE symbol = :symbol
        """
        cursor.execute(nifty_query, {'symbol': symbol_upper})
        nifty_result = cursor.fetchone()
        
        # Get latest price from STOCK_DATA table
        stock_query = """
            SELECT symbol, last_price
            FROM stock_data
            WHERE date1 = (SELECT MAX(date1) FROM stock_data)
            AND symbol = :symbol
        """
        cursor.execute(stock_query, {'symbol': symbol_upper})
        stock_result = cursor.fetchone()
        
        # Prepare response data
        response_data = {
            'success': True,
            'symbol': symbol,
            'exchange': exchange
        }
        
        # Add company information if found
        if nifty_result:
            response_data.update({
                'company_name': nifty_result[1],
                'mcap_lakhs': float(nifty_result[2]) if nifty_result[2] else None,
                'nifty_rank': int(nifty_result[3]) if nifty_result[3] else None,
                'him_rating': nifty_result[4],
                'rating_date': nifty_result[5].isoformat() if nifty_result[5] else None
            })
            logger.info(f"[API] Company details for {symbol}: {nifty_result[1]}")
        
        # Add latest price if found
        if stock_result:
            response_data['latest_price'] = float(stock_result[1])
            logger.info(f"[API] Latest price for {symbol}: {stock_result[1]}")
        
        # If no data found in either table, try fallback
        if not nifty_result and not stock_result:
            # Fallback company mapping
            symbol_to_company_map = {
                'RELIANCE': 'Reliance Industries Limited',
                'TCS': 'Tata Consultancy Services Limited',
                'HDFCBANK': 'HDFC Bank Limited',
                'INFY': 'Infosys Limited',
                'HINDUNILVR': 'Hindustan Unilever Limited',
                'ICICIBANK': 'ICICI Bank Limited',
                'KOTAKBANK': 'Kotak Mahindra Bank Limited',
                'BAJFINANCE': 'Bajaj Finance Limited',
                'ITC': 'ITC Limited',
                'SBIN': 'State Bank of India',
                'WIPRO': 'Wipro Limited',
                'ASIANPAINT': 'Asian Paints Limited',
                'MARUTI': 'Maruti Suzuki India Limited',
                'LTIM': 'LTIMindtree Limited',
                'HCLTECH': 'HCL Technologies Limited',
            }
            
            fallback_company = symbol_to_company_map.get(symbol_upper)
            if fallback_company:
                response_data['company_name'] = fallback_company
                logger.info(f"[API] Using fallback company name for {symbol}: {fallback_company}")
            
            # Try to get price from Kite if available
            kite = current_app.config.get('kite')
            if kite:
                try:
                    instrument = f"{exchange}:{symbol_upper}"
                    quote = kite.quote([instrument])
                    if instrument in quote:
                        response_data['latest_price'] = quote[instrument]['last_price']
                        logger.info(f"[API] Got latest price from Kite for {symbol}: {quote[instrument]['last_price']}")
                except Exception as kite_error:
                    logger.warning(f"[API] Failed to get price from Kite for {symbol}: {str(kite_error)}")
        
        # If still no data found, return error
        if 'company_name' not in response_data and 'latest_price' not in response_data:
            return jsonify({
                'success': False,
                'error': f'No information found for symbol {symbol}'
            }), 404
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"[API] Error fetching symbol info for {symbol}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        # Ensure database resources are closed
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if connection:
            try:
                connection.close()
            except:
                pass

@custom_gtt_api.route('/reset-kite-status/<int:order_id>', methods=['POST'])
def reset_kite_status(order_id):
    """Reset the Kite status of an order"""
    try:
        reset_result = reset_kite_status(order_id)
        if not reset_result:
            return jsonify({
                'success': False,
                'error': f'Order with ID {order_id} not found or could not be reset'
            }), 404
            
        logger.info(f"[API] Order {order_id} Kite status reset successfully")
        return jsonify({
            'success': True,
            'message': f'Order {order_id} Kite status reset successfully'
        })
    except Exception as e:
        logger.error(f"[API] Error resetting Kite status for order {order_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
