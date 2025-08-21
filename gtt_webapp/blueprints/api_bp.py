from flask import Blueprint, jsonify, request, current_app, url_for
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger('custom_data')

api_bp = Blueprint('api', __name__)

@api_bp.route('/test', methods=['GET'])
def test_api():
    """Simple endpoint to test if the API blueprint is registered correctly"""
    logger.debug("API test endpoint hit")
    return jsonify({
        'success': True,
        'message': 'API blueprint is working correctly',
        'blueprint_name': api_bp.name,
        'timestamp': datetime.now().isoformat()
    })

# --- GTT endpoints now only use KiteConnect ---

@api_bp.route('/gtt/order', methods=['POST'])
def create_order():
    """Create a new GTT order using KiteConnect"""
    data = request.json
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    try:
        # Parse and validate input
        tradingsymbol = data['tradingsymbol']
        exchange = data['exchange']
        trigger_type = data['trigger_type']
        trigger_values_raw = data['trigger_values']
        last_price = float(data['last_price'])
        transaction_type = data['transaction_type']
        quantity = int(data['quantity'])

        # Support both comma and semicolon for two-leg
        if trigger_type == 'two-leg':
            trigger_values = [float(x.strip()) for x in trigger_values_raw.replace(';', ',').split(',')]
        else:
            trigger_values = [float(trigger_values_raw.strip())]

        # Create orders
        if trigger_type == 'single':
            orders = [{
                "transaction_type": transaction_type,
                "quantity": quantity,
                "price": trigger_values[0],
                "order_type": "LIMIT",
                "product": "CNC"
            }]
        elif trigger_type == 'two-leg' and transaction_type == 'SELL':
            stop_loss, target = trigger_values
            orders = [
                {
                    "transaction_type": "SELL",
                    "quantity": quantity,
                    "price": target,
                    "order_type": "LIMIT",
                    "product": "CNC"
                },
                {
                    "transaction_type": "SELL",
                    "quantity": quantity,
                    "price": stop_loss,
                    "order_type": "LIMIT",
                    "product": "CNC"
                }
            ]
        else:
            return jsonify({'error': 'Invalid trigger_type or trigger_values.'}), 400

        # Place GTT order using KiteConnect
        result = kite.place_gtt(
            trigger_type=trigger_type,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
            trigger_values=trigger_values,
            last_price=last_price,
            orders=orders
        )
        return jsonify({
            'message': 'GTT order placed successfully',
            'trigger_id': result.get('trigger_id'),
            'order': {
                'tradingsymbol': tradingsymbol,
                'exchange': exchange,
                'trigger_type': trigger_type,
                'trigger_values': trigger_values,
                'last_price': last_price,
                'transaction_type': transaction_type,
                'quantity': quantity
            }
        }), 201
    except KeyError as e:
        return jsonify({'error': f'Missing required field: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/gtt/order/<int:trigger_id>', methods=['DELETE'])
def delete_gtt_order(trigger_id):
    """Delete a GTT order using KiteConnect"""
    print(f"[DEBUG] Delete GTT order called with trigger_id: {trigger_id}")
    logger.info(f"Delete GTT order called with trigger_id: {trigger_id}")
    kite = current_app.config.get('kite')
    if kite is None:
        print("[ERROR] KiteConnect is not initialized")
        logger.error("KiteConnect is not initialized")
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    try:
        print(f"[DEBUG] Attempting to delete GTT with trigger_id: {trigger_id}")
        logger.info(f"Attempting to delete GTT with trigger_id: {trigger_id}")
        result = kite.delete_gtt(trigger_id)
        print(f"[DEBUG] Delete GTT result: {result}")
        logger.info(f"Delete GTT result: {result}")
        return jsonify({'message': f'GTT order {trigger_id} deleted successfully', 'trigger_id': result.get('trigger_id')}), 200
    except Exception as e:
        print(f"[ERROR] Failed to delete GTT {trigger_id}: {str(e)}")
        logger.error(f"Failed to delete GTT {trigger_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/gtt/orders', methods=['GET'])
def get_gtt_orders():
    """Get all GTT orders using KiteConnect"""
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    try:
        orders = kite.get_gtts()
        return jsonify({'orders': orders})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/quote', methods=['GET'])
def get_quote():
    """Get quote for a symbol"""
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    
    symbol = request.args.get('symbol')
    exchange = request.args.get('exchange', 'NSE')
    
    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400
        
    try:
        instrument = f"{exchange}:{symbol}"
        quote = kite.quote([instrument])
        return jsonify({'quote': quote[instrument]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/multi-gtt-order', methods=['POST'])
def place_multiple_gtt_orders():
    """Place multiple GTT orders in one go"""
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    
    data = request.json
    orders = data.get('orders', [])
    
    if not orders:
        return jsonify({'error': 'No orders provided'}), 400
    
    results = []
    for order in orders:
        try:
            # Extract order details
            tradingsymbol = order.get('tradingsymbol')
            exchange = order.get('exchange', 'NSE')
            transaction_type = order.get('transaction_type')
            quantity = int(order.get('quantity', 0))
            trigger_type = order.get('trigger_type', 'single')
            
            # Get trigger values based on trigger type
            trigger_values = []
            if trigger_type == 'single':
                trigger_price = float(order.get('trigger_price', 0))
                trigger_values = [trigger_price]
            elif trigger_type == 'two-leg':
                stop_loss = float(order.get('stop_loss', 0))
                target = float(order.get('target_price', 0))
                trigger_values = [stop_loss, target]
            
            # Get last price from order or fetch it
            last_price = order.get('last_price')
            if not last_price:
                instrument = f"{exchange}:{tradingsymbol}"
                quote = kite.quote([instrument])
                last_price = quote[instrument]['last_price']
            else:
                last_price = float(last_price)
            
            # Create orders list based on trigger type
            if trigger_type == 'single':
                orders = [{
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "price": trigger_values[0],
                    "order_type": "LIMIT",
                    "product": "CNC"
                }]
            elif trigger_type == 'two-leg' and transaction_type == 'SELL':
                stop_loss, target = trigger_values
                orders = [
                    {
                        "transaction_type": "SELL",
                        "quantity": quantity,
                        "price": target,
                        "order_type": "LIMIT",
                        "product": "CNC"
                    },
                    {
                        "transaction_type": "SELL",
                        "quantity": quantity,
                        "price": stop_loss,
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]
            else:
                results.append({'success': False, 'error': 'Invalid trigger_type or transaction_type', 'symbol': tradingsymbol})
                continue
            
            # Place GTT order using KiteConnect
            result = kite.place_gtt(
                trigger_type=trigger_type,
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                trigger_values=trigger_values,
                last_price=last_price,
                orders=orders
            )
            results.append({'success': True, 'trigger_id': result.get('trigger_id'), 'symbol': tradingsymbol})
        except Exception as e:
            results.append({'success': False, 'error': str(e), 'symbol': order.get('tradingsymbol', '')})
    return jsonify({'results': results})

@api_bp.route('/gtt/orders/bulk', methods=['POST'])
def create_bulk_gtt_orders():
    """Create multiple GTT orders using KiteConnect (for multi GTT modal)"""
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    
    data = request.json
    orders = data.get('orders', [])
    
    if not orders:
        return jsonify({'error': 'No orders provided'}), 400
    
    results = []
    for order in orders:
        try:
            # Extract order details
            tradingsymbol = order.get('tradingsymbol')
            exchange = order.get('exchange', 'NSE')
            transaction_type = order.get('transaction_type')
            quantity = int(order.get('quantity', 0))
            trigger_type = order.get('trigger_type', 'single')
            last_price = float(order.get('last_price', 0))
            
            # Parse trigger values
            trigger_values_raw = order.get('trigger_values', '')
            if trigger_type == 'two-leg':
                trigger_values = [float(x.strip()) for x in trigger_values_raw.replace(';', ',').split(',')]
            else:
                trigger_values = [float(trigger_values_raw.strip())]
            
            # Create orders based on trigger type
            if trigger_type == 'single':
                orders_list = [{
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "price": trigger_values[0],
                    "order_type": "LIMIT",
                    "product": "CNC"
                }]
            elif trigger_type == 'two-leg':
                if len(trigger_values) != 2:
                    raise ValueError("Two-leg GTT requires exactly 2 trigger values")
                
                if transaction_type == 'SELL':
                    # For SELL: first value is stop-loss (lower), second is target (higher)
                    stop_loss, target = trigger_values
                    orders_list = [
                        {
                            "transaction_type": "SELL",
                            "quantity": quantity,
                            "price": stop_loss,
                            "order_type": "SL",
                            "product": "CNC"
                        },
                        {
                            "transaction_type": "SELL", 
                            "quantity": quantity,
                            "price": target,
                            "order_type": "LIMIT",
                            "product": "CNC"
                        }
                    ]
                else:  # BUY
                    # For BUY: first value is target (higher), second is stop-loss (lower)
                    target, stop_loss = trigger_values
                    orders_list = [
                        {
                            "transaction_type": "BUY",
                            "quantity": quantity,
                            "price": target,
                            "order_type": "LIMIT",
                            "product": "CNC"
                        },
                        {
                            "transaction_type": "BUY",
                            "quantity": quantity,
                            "price": stop_loss,
                            "order_type": "SL",
                            "product": "CNC"
                        }
                    ]
            else:
                raise ValueError(f"Unsupported trigger type: {trigger_type}")
            
            # Place GTT order using KiteConnect
            result = kite.place_gtt(
                trigger_type=trigger_type,
                tradingsymbol=tradingsymbol,
                exchange=exchange,
                trigger_values=trigger_values,
                last_price=last_price,
                orders=orders_list
            )
            
            results.append({
                'success': True, 
                'trigger_id': result.get('trigger_id'), 
                'symbol': tradingsymbol
            })
            
        except Exception as e:
            logger.error(f"Error creating GTT order for {order.get('tradingsymbol', 'unknown')}: {str(e)}")
            results.append({
                'success': False, 
                'error': str(e), 
                'symbol': order.get('tradingsymbol', 'unknown')
            })
    
    return jsonify({'results': results})

@api_bp.route('/sync-kite-gtts-to-oracle', methods=['POST'])
def sync_kite_gtts_to_oracle():
    """Truncate and load KITE_GTTS table in Oracle with fresh GTT data"""
    try:
        # Get KiteConnect instance
        kite = current_app.config.get('kite')
        if kite is None:
            return jsonify({
                'success': False,
                'error': 'KiteConnect is not initialized. Please check access_token.txt.'
            }), 500

        # Fetch GTT orders from Kite
        logger.info("Fetching GTT orders from KiteConnect...")
        gtt_orders = kite.get_gtts()
        logger.info(f"Retrieved {len(gtt_orders)} GTT orders from KiteConnect")

        # Import Oracle database connection
        from db_config import get_connection
        import oracledb
        
        # Connect to Oracle database
        logger.info("Connecting to Oracle database...")
        with get_connection() as connection:
            cursor = connection.cursor()
            
            # Truncate the table
            logger.info("Truncating ADMIN.KITE_GTTS table...")
            cursor.execute("TRUNCATE TABLE ADMIN.KITE_GTTS")
            
            # Prepare insert statement
            insert_sql = """
                INSERT INTO ADMIN.KITE_GTTS (
                    user_id, ttype, status, tradingsymbol, texchange, 
                    trigger_values, transaction_type, quantity, last_price, 
                    created_at, updated_at, expires_at
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12
                )
            """
            
            # Process and insert each GTT order
            records_inserted = 0
            for gtt in gtt_orders:
                try:
                    # Parse dates once for the GTT
                    created_at = None
                    updated_at = None
                    expires_at = None
                    
                    if 'created_at' in gtt:
                        try:
                            created_at = datetime.fromisoformat(gtt['created_at'].replace('Z', '+00:00'))
                        except:
                            created_at = None
                    
                    if 'updated_at' in gtt:
                        try:
                            updated_at = datetime.fromisoformat(gtt['updated_at'].replace('Z', '+00:00'))
                        except:
                            updated_at = None
                    
                    if 'expires_at' in gtt:
                        try:
                            expires_at = datetime.fromisoformat(gtt['expires_at'].replace('Z', '+00:00'))
                        except:
                            expires_at = None
                    
                    # Get trigger values list
                    trigger_values_list = []
                    if 'condition' in gtt and 'trigger_values' in gtt['condition']:
                        trigger_list = gtt['condition']['trigger_values']
                        if isinstance(trigger_list, list):
                            trigger_values_list = [float(tv) for tv in trigger_list]
                        elif isinstance(trigger_list, (int, float)):
                            trigger_values_list = [float(trigger_list)]
                    
                    # Process each order within the GTT
                    if 'orders' in gtt and len(gtt['orders']) > 0:
                        for i, order in enumerate(gtt['orders']):
                            try:
                                # For two-leg orders, map each order to its corresponding trigger value
                                # For single orders, use the first (and only) trigger value
                                trigger_value_for_order = None
                                if len(trigger_values_list) > 0:
                                    if gtt.get('type') == 'two-leg' and i < len(trigger_values_list):
                                        # Use the specific trigger value for this order index
                                        trigger_value_for_order = trigger_values_list[i]
                                    else:
                                        # For single-leg or fallback, use first trigger value
                                        trigger_value_for_order = trigger_values_list[0]
                                
                                # Insert record for each order with its specific trigger value
                                cursor.execute(insert_sql, [
                                    gtt.get('user_id'),
                                    gtt.get('type'),  # GTT type (single/two-leg)
                                    gtt.get('status'),
                                    gtt.get('condition', {}).get('tradingsymbol'),
                                    gtt.get('condition', {}).get('exchange'),
                                    trigger_value_for_order,  # Specific trigger value for this order
                                    order.get('transaction_type'),
                                    order.get('quantity'),
                                    gtt.get('condition', {}).get('last_price'),
                                    created_at,
                                    updated_at,
                                    expires_at
                                ])
                                records_inserted += 1
                                
                                logger.debug(f"Inserted order {i+1} for GTT {gtt.get('id')}: "
                                           f"Type={gtt.get('type')}, "
                                           f"TriggerValue={trigger_value_for_order}, "
                                           f"Transaction={order.get('transaction_type')}")
                                
                            except Exception as e:
                                logger.error(f"Error inserting order {i+1} within GTT {gtt.get('id', 'unknown')}: {str(e)}")
                                continue
                    else:
                        # If no orders array, insert the GTT itself with basic info
                        first_trigger_value = trigger_values_list[0] if trigger_values_list else None
                        cursor.execute(insert_sql, [
                            gtt.get('user_id'),
                            gtt.get('type'),  # GTT type (single/two-leg)
                            gtt.get('status'),
                            gtt.get('condition', {}).get('tradingsymbol'),
                            gtt.get('condition', {}).get('exchange'),
                            first_trigger_value,  # First trigger value as number
                            None,  # transaction_type
                            None,  # quantity
                            gtt.get('condition', {}).get('last_price'),
                            created_at,
                            updated_at,
                            expires_at
                        ])
                        records_inserted += 1
                        
                except Exception as e:
                    logger.error(f"Error processing GTT {gtt.get('id', 'unknown')}: {str(e)}")
                    continue
            
            # Commit the transaction
            connection.commit()
            logger.info(f"Successfully inserted {records_inserted} records into ADMIN.KITE_GTTS")
            
            return jsonify({
                'success': True,
                'message': f'Successfully synchronized {records_inserted} GTT orders to Oracle database',
                'records_processed': records_inserted
            })
            
    except Exception as e:
        logger.error(f"Error syncing GTT orders to Oracle: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to sync data: {str(e)}'
        }), 500
