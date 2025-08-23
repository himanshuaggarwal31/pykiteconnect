from flask import Blueprint, jsonify, request
import logging
import oracledb
import sys
import os
from db_config import configuration
from models.custom_gtt import add_custom_gtt_order, get_custom_gtt_orders
from datetime import datetime

# Add the parent directory to access auth module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from auth.simple_oauth import login_required
from auth.access_control import feature_required

sql_results_gtt_api = Blueprint('sql_results_gtt_api', __name__)

# Configure logging
logger = logging.getLogger('custom_data')

@sql_results_gtt_api.route('/add-gtt-order', methods=['POST'])
@login_required
@feature_required('sql_results')
def add_gtt_order():
    """Add a GTT order from SQL results page"""
    try:
        # Log request information for debugging
        logger.debug(f"[API] Add GTT order from SQL results request method: {request.method}")
        logger.debug(f"[API] Add GTT order content type: {request.content_type}")
        
        if not request.is_json:
            logger.error(f"[API] Request is not JSON. Content-Type: {request.content_type}")
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
            
        # Parse JSON data
        data = request.json
        logger.debug(f"[API] Add GTT order request data: {data}")
        
        # Required fields
        required_fields = ['symbol', 'order_type', 'trigger_type']
        missing_fields = []
        
        # Validate required fields
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)
                
        if missing_fields:
            logger.error(f"[API] Missing required fields: {missing_fields}")
            return jsonify({
                'success': False,
                'error': f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
            
        try:
            # Check if order already exists
            logger.debug(f"[API] Checking if order already exists for symbol: {data.get('symbol')}, order_type: {data.get('order_type')}")
            orders_result = get_custom_gtt_orders(
                search=data.get('symbol'),
                order_type=data.get('order_type'),
                kite_status='not_placed',
                page=1,
                per_page=10
            )
            
            existing_orders = orders_result.get('records', []) if orders_result else []
            logger.debug(f"[API] Found {len(existing_orders)} existing orders")
            
            if existing_orders and len(existing_orders) > 0:
                # Return the existing order for editing
                existing_order = existing_orders[0]
                logger.info(f"[API] Order already exists for symbol {data.get('symbol')}, returning for editing")
                return jsonify({
                    'success': True,
                    'message': 'Order already exists for this symbol',
                    'exists': True,
                    'order': existing_order
                })
        except Exception as e:
            logger.error(f"[API] Error checking for existing orders: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"Error checking for existing orders: {str(e)}"
            }), 500
            
        try:
            # Get order data from database using the provided SQL query
            logger.debug(f"[API] Fetching order data from database for symbol: {data.get('symbol')}")
            
            connection = None
            try:
                connection = oracledb.connect(**configuration['db_config'])
                cursor = connection.cursor()
                
                # Execute the query to get order data from stock_data and nifty_mcap tables
                fetch_query = """
                    SELECT DISTINCT sd.symbol                        AS symbol,
                                    nm.company_name                  AS company_name,
                                    nm.nifty_rank                    AS nifty_rank,
                                    'NSE'                            AS exchange,
                                    :order_type                      AS order_type,
                                    CASE 
                                        WHEN :order_type = 'BUY' THEN 'single'
                                        ELSE :trigger_type
                                    END                              AS trigger_type,
                                    CASE 
                                        WHEN :order_type = 'BUY' THEN ROUND(close_price * 0.9, 4)
                                        WHEN :order_type = 'SELL' AND :trigger_type = 'single' THEN ROUND(close_price * 1.1, 4)
                                        WHEN :order_type = 'SELL' AND :trigger_type = 'two-leg' THEN NULL
                                        ELSE ROUND(close_price * 0.9, 4)
                                    END AS trigger_price,
                                    CASE 
                                        WHEN :order_type = 'BUY' THEN ROUND(close_price * 1.3, 4)
                                        WHEN :order_type = 'SELL' AND :trigger_type = 'single' THEN NULL
                                        WHEN :order_type = 'SELL' AND :trigger_type = 'two-leg' THEN ROUND(close_price * 1.15, 4)
                                        ELSE ROUND(close_price * 1.3, 4)
                                    END AS target_price,
                                    CASE 
                                        WHEN :order_type = 'SELL' AND :trigger_type = 'two-leg' THEN ROUND(close_price * 0.95, 4)
                                        ELSE NULL
                                    END AS stop_loss,
                                    last_price                       AS last_price,
                                    0                                AS quantity,
                                    1                                AS is_active,
                                    0                                AS placed_on_kite
                      FROM stock_data  sd
                           LEFT OUTER JOIN NIFTY_MCAP nm ON (sd.symbol = nm.symbol)
                     WHERE date1 = getnthdate() AND sd.symbol = :symbol
                """
                
                # Force single leg for BUY orders
                trigger_type = data.get('trigger_type')
                if data.get('order_type') == 'BUY':
                    trigger_type = 'single'
                
                cursor.execute(fetch_query, {
                    'symbol': data.get('symbol'),
                    'order_type': data.get('order_type'),
                    'trigger_type': trigger_type
                })
                
                result = cursor.fetchone()
                cursor.close()
                
                if not result:
                    logger.warning(f"[API] No stock data found for symbol: {data.get('symbol')}")
                    return jsonify({
                        'success': False,
                        'error': f"No stock data found for symbol: {data.get('symbol')}"
                    }), 404
                
                # Convert result to dictionary
                columns = ['symbol', 'company_name', 'nifty_rank', 'exchange', 'order_type', 
                          'trigger_type', 'trigger_price', 'target_price', 'stop_loss', 'last_price', 
                          'quantity', 'is_active', 'placed_on_kite']
                
                order_data = {}
                for i, col in enumerate(columns):
                    order_data[col] = result[i]
                
                # Add timestamps
                order_data['created_at'] = datetime.now()
                order_data['updated_at'] = datetime.now()
                
                logger.debug(f"[API] Order data from database: {order_data}")
                
            except Exception as db_error:
                logger.error(f"[API] Database error fetching order data: {str(db_error)}", exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f"Database error: {str(db_error)}"
                }), 500
            finally:
                if connection:
                    connection.close()
            
            # Add the order to the database using the fetched data
            logger.debug(f"[API] Adding new GTT order for symbol: {order_data.get('symbol')}")
            order_id = add_custom_gtt_order(order_data)
            
            if not order_id:
                logger.error("[API] Failed to add order - no order ID returned")
                return jsonify({
                    'success': False,
                    'error': "Failed to add order - database error"
                }), 500
                
            logger.info(f"[API] GTT order added successfully with ID: {order_id}")
            
            # Return success with order data
            return jsonify({
                'success': True,
                'message': 'GTT order added successfully',
                'order_id': order_id,
                'order_data': order_data
            })
        except Exception as e:
            logger.error(f"[API] Error adding GTT order: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"Error adding GTT order: {str(e)}"
            }), 500
    except Exception as e:
        logger.error(f"[API] Error adding GTT order from SQL results: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500

@sql_results_gtt_api.route('/get-last-price', methods=['GET'])
@login_required
@feature_required('sql_results')
def get_last_price():
    """Get the last price for a symbol"""
    connection = None
    try:
        symbol = request.args.get('symbol')
        logger.debug(f"[API] Get last price for symbol: {symbol}")
        
        if not symbol:
            logger.warning("[API] Symbol parameter is missing")
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400
            
        # Connect to database
        try:
            connection = oracledb.connect(**configuration['db_config'])
            cursor = connection.cursor()
        except Exception as db_error:
            logger.error(f"[API] Database connection error: {str(db_error)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"Database connection error: {str(db_error)}"
            }), 500
        
        try:
            # Query to get last price
            query = """
                SELECT last_price 
                FROM stock_data 
                WHERE symbol = :symbol AND date1 = getnthdate() 
                ORDER BY date1 DESC
            """
            
            cursor.execute(query, {'symbol': symbol})
            result = cursor.fetchone()
            logger.debug(f"[API] Last price query result: {result}")
        except Exception as query_error:
            logger.error(f"[API] Error executing query: {str(query_error)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f"Query error: {str(query_error)}"
            }), 500
        finally:
            # Close cursor if open
            if cursor:
                cursor.close()
        
        if result and result[0]:
            last_price = float(result[0])
            logger.info(f"[API] Found last price for {symbol}: {last_price}")
            return jsonify({
                'success': True,
                'last_price': last_price
            })
        else:
            logger.warning(f"[API] No price data found for symbol: {symbol}")
            # Try to get price from close_price if last_price is not available
            try:
                query = """
                    SELECT close_price 
                    FROM stock_data 
                    WHERE symbol = :symbol AND date1 = getnthdate() 
                    ORDER BY date1 DESC
                """
                
                cursor = connection.cursor()
                cursor.execute(query, {'symbol': symbol})
                result = cursor.fetchone()
                cursor.close()
                
                if result and result[0]:
                    close_price = float(result[0])
                    logger.info(f"[API] Found close price for {symbol}: {close_price}")
                    return jsonify({
                        'success': True,
                        'last_price': close_price
                    })
            except Exception as fallback_error:
                logger.error(f"[API] Error in fallback price query: {str(fallback_error)}", exc_info=True)
            
            return jsonify({
                'success': False,
                'error': 'No price data found for symbol'
            }), 404
    except Exception as e:
        logger.error(f"[API] Error getting last price: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500
    finally:
        # Ensure connection is closed
        if connection:
            try:
                connection.close()
                logger.debug("[API] Database connection closed")
            except Exception as close_error:
                logger.error(f"[API] Error closing database connection: {str(close_error)}")
