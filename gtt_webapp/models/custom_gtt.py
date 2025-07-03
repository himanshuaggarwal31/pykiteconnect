import oracledb
import logging
from datetime import datetime
from db_config import get_connection, configuration
from flask import current_app

# Configure logging early
logger = logging.getLogger('custom_data')

def create_custom_gtt_table():
    """Create the custom GTT orders table if it doesn't exist"""
    # Use direct connection for table creation since Flask app context might not be available
    with oracledb.connect(**configuration['db_config']) as connection:
        with connection.cursor() as cursor:
            # Add columns if table exists
            try:
                # First try to add the last_price column if needed
                try:
                    cursor.execute("""
                        ALTER TABLE custom_gtt_orders 
                        ADD last_price NUMBER
                    """)
                    logger.info("Added last_price column to custom_gtt_orders table")
                    connection.commit()
                except oracledb.DatabaseError as e:
                    if 'ORA-01430' in str(e):  # Column already exists
                        pass
                    elif 'ORA-00942' in str(e):  # Table does not exist
                        pass
                    else:
                        raise e
                
                # Try to add notes column if needed
                try:
                    cursor.execute("""
                        ALTER TABLE custom_gtt_orders 
                        ADD notes VARCHAR2(500)
                    """)
                    logger.info("Added notes column to custom_gtt_orders table")
                    connection.commit()
                except oracledb.DatabaseError as e:
                    if 'ORA-01430' in str(e):  # Column already exists
                        pass
                    elif 'ORA-00942' in str(e):  # Table does not exist
                        pass
                    else:
                        raise e
                
                # Try to add trigger_values column if needed
                try:
                    cursor.execute("""
                        ALTER TABLE custom_gtt_orders 
                        ADD trigger_values VARCHAR2(100)
                    """)
                    logger.info("Added trigger_values column to custom_gtt_orders table")
                    connection.commit()
                except oracledb.DatabaseError as e:
                    if 'ORA-01430' in str(e):  # Column already exists
                        pass
                    elif 'ORA-00942' in str(e):  # Table does not exist
                        pass
                    else:
                        raise e
            except Exception as e:
                logger.error(f"Error adding columns to custom_gtt_orders: {str(e)}")
                # Continue with table creation anyway

            # Create table if it doesn't exist
            cursor.execute('''
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE custom_gtt_orders (
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
                    )';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE = -955 THEN NULL; 
                        ELSE RAISE;
                        END IF;
                END;
            ''')
            connection.commit()

def get_custom_logger():
    global logger
    return logger

def sanitize_number(val):
    if val is None or val == '':
        return None
    try:
        return float(val)
    except Exception:
        return None
        
def sanitize_input(val):
    """Sanitize input to prevent SQL injection"""
    if val is None:
        return None
    if isinstance(val, str):
        # Remove dangerous characters
        return val.strip().replace("'", "''")
    return val

def add_custom_gtt_order(data):
    """Add a new custom GTT order (full field coverage, robust validation, debug logging)"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][add_custom_gtt_order] Incoming data: {data}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        out_id = cursor.var(int)
        
        # For a two-leg order, combine target_price and stop_loss into trigger_values
        trigger_values = None
        if data.get('trigger_type') == 'two-leg' and data.get('target_price') and data.get('stop_loss'):
            trigger_values = f"{data.get('stop_loss')},{data.get('target_price')}"
        elif data.get('trigger_values'):
            trigger_values = data.get('trigger_values')
            
        # Prepare all fields for insert
        params = {
            'symbol': sanitize_input(data.get('symbol')),
            'company_name': sanitize_input(data.get('company_name')),
            'nifty_rank': sanitize_number(data.get('nifty_rank')),
            'exchange': sanitize_input(data.get('exchange', 'NSE')),
            'order_type': sanitize_input(data.get('order_type')),
            'trigger_type': sanitize_input(data.get('trigger_type')),
            'trigger_price': sanitize_number(data.get('trigger_price')),
            'last_price': sanitize_number(data.get('last_price')),
            'quantity': sanitize_number(data.get('quantity')),
            'target_price': sanitize_number(data.get('target_price')),
            'stop_loss': sanitize_number(data.get('stop_loss')),
            'trigger_values': sanitize_input(trigger_values),
            'notes': sanitize_input(data.get('notes')),
            'is_active': 1,
            'placed_on_kite': sanitize_number(data.get('placed_on_kite', 0)),
            'kite_trigger_id': sanitize_number(data.get('kite_trigger_id')),
            'id': out_id
        }
        logger.debug(f"[DEBUG][add_custom_gtt_order] SQL params: {params}")
        # First try the insert with all fields
        try:
            cursor.execute("""
                INSERT INTO custom_gtt_orders (
                    symbol, company_name, nifty_rank, exchange, order_type, trigger_type,
                    trigger_price, last_price, quantity, target_price, stop_loss, trigger_values,
                    notes, created_at, updated_at, is_active, placed_on_kite, kite_trigger_id
                ) VALUES (
                    :symbol, :company_name, :nifty_rank, :exchange, :order_type, :trigger_type,
                    :trigger_price, :last_price, :quantity, :target_price, :stop_loss, :trigger_values,
                    :notes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :is_active, :placed_on_kite, :kite_trigger_id
                ) RETURNING id INTO :id
            """, params)
        except oracledb.DatabaseError as e:
            if 'ORA-00904' in str(e) and 'TRIGGER_VALUES' in str(e):
                # If trigger_values column is missing, try without it
                logger.warning(f"[WARNING] Column TRIGGER_VALUES missing, attempting insert without it: {str(e)}")
                cursor.execute("""
                    INSERT INTO custom_gtt_orders (
                        symbol, company_name, nifty_rank, exchange, order_type, trigger_type,
                        trigger_price, last_price, quantity, target_price, stop_loss,
                        notes, created_at, updated_at, is_active, placed_on_kite, kite_trigger_id
                    ) VALUES (
                        :symbol, :company_name, :nifty_rank, :exchange, :order_type, :trigger_type,
                        :trigger_price, :last_price, :quantity, :target_price, :stop_loss,
                        :notes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :is_active, :placed_on_kite, :kite_trigger_id
                    ) RETURNING id INTO :id
                """, params)
            else:
                # Re-raise other errors
                raise
        
        connection.commit()
        logger.info(f"[INFO][add_custom_gtt_order] Order added successfully with ID: {out_id.getvalue()}")
        return out_id.getvalue()[0]
    except Exception as e:
        logger.error(f"[ERROR][add_custom_gtt_order] Failed to add order: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def update_custom_gtt_order(order_id, data):
    """Update an existing custom GTT order"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][update_custom_gtt_order] Updating order {order_id} with data: {data}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        # Build the SET clause dynamically based on provided fields
        set_clauses = []
        params = {'id': order_id}
        
        # Special handling for trigger_values if target_price and stop_loss are provided
        if data.get('trigger_type') == 'two-leg' and ('target_price' in data or 'stop_loss' in data):
            # Get current values first
            current_order = get_order_by_id(order_id)
            target = sanitize_number(data.get('target_price', current_order.get('target_price')))
            stop_loss = sanitize_number(data.get('stop_loss', current_order.get('stop_loss')))
            
            if target is not None and stop_loss is not None:
                data['trigger_values'] = f"{stop_loss},{target}"
        
        # Map fields to database columns
        field_map = {
            'symbol': 'symbol',
            'company_name': 'company_name',
            'nifty_rank': 'nifty_rank',
            'exchange': 'exchange',
            'order_type': 'order_type',
            'trigger_type': 'trigger_type',
            'trigger_price': 'trigger_price',
            'last_price': 'last_price',
            'quantity': 'quantity',
            'target_price': 'target_price',
            'stop_loss': 'stop_loss',
            'trigger_values': 'trigger_values',
            'notes': 'notes',
            'is_active': 'is_active',
            'placed_on_kite': 'placed_on_kite',
            'kite_trigger_id': 'kite_trigger_id'
        }
        
        for key, column in field_map.items():
            if key in data:
                value = data[key]
                if key in ['trigger_price', 'last_price', 'quantity', 'target_price', 'stop_loss', 'nifty_rank']:
                    value = sanitize_number(value)
                elif isinstance(value, str):
                    value = sanitize_input(value)
                    
                set_clauses.append(f"{column} = :{key}")
                params[key] = value
                
        if not set_clauses:
            logger.warning(f"[WARNING][update_custom_gtt_order] No valid fields to update for order {order_id}")
            return False
            
        # Always update the updated_at timestamp
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        # Build and execute the query
        query = f"""
            UPDATE custom_gtt_orders
            SET {", ".join(set_clauses)}
            WHERE id = :id
        """
        logger.debug(f"[DEBUG][update_custom_gtt_order] SQL: {query}, Params: {params}")
        cursor.execute(query, params)
        affected = cursor.rowcount
        connection.commit()
        
        logger.info(f"[INFO][update_custom_gtt_order] Order {order_id} updated successfully ({affected} rows)")
        return affected > 0
    except Exception as e:
        logger.error(f"[ERROR][update_custom_gtt_order] Failed to update order {order_id}: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def delete_custom_gtt_order(order_id):
    """Delete a custom GTT order"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][delete_custom_gtt_order] Deleting order: {order_id}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        cursor.execute("""
            DELETE FROM custom_gtt_orders
            WHERE id = :id
        """, {'id': order_id})
        
        affected = cursor.rowcount
        connection.commit()
        
        logger.info(f"[INFO][delete_custom_gtt_order] Order {order_id} deleted successfully ({affected} rows)")
        return affected > 0
    except Exception as e:
        logger.error(f"[ERROR][delete_custom_gtt_order] Failed to delete order {order_id}: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def get_custom_gtt_orders(search='', order_type='', kite_status='', page=1, per_page=25):
    """Get all custom GTT orders with filtering, pagination, and sorting"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][get_custom_gtt_orders] Fetching orders with search: '{search}', order_type: '{order_type}', kite_status: '{kite_status}', page: {page}, per_page: {per_page}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        # Build WHERE clause based on filters
        where_clauses = ["is_active = 1"]
        params = {}
        
        if search:
            where_clauses.append("(UPPER(symbol) LIKE UPPER(:search) OR UPPER(company_name) LIKE UPPER(:search))")
            params['search'] = f"%{sanitize_input(search)}%"
            
        if order_type:
            where_clauses.append("order_type = :order_type")
            params['order_type'] = sanitize_input(order_type)
            
        if kite_status:
            if kite_status == 'placed':
                where_clauses.append("placed_on_kite = 1")
            elif kite_status == 'not_placed':
                where_clauses.append("placed_on_kite = 0")
        
        # Build the final WHERE clause
        where_clause = " AND ".join(where_clauses)
        
        # Get total count first
        count_query = f"""
            SELECT COUNT(*) FROM custom_gtt_orders
            WHERE {where_clause}
        """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Calculate pagination
        offset = (page - 1) * per_page
        
        # Get records with pagination
        query = f"""
            SELECT * FROM (
                SELECT 
                    o.*,
                    ROW_NUMBER() OVER (ORDER BY updated_at DESC) AS rn
                FROM custom_gtt_orders o
                WHERE {where_clause}
            ) WHERE rn > :offset AND rn <= :limit
        """
        params['offset'] = offset
        params['limit'] = offset + per_page
        
        logger.debug(f"[DEBUG][get_custom_gtt_orders] SQL: {query}, Params: {params}")
        cursor.execute(query, params)
        
        columns = [col[0].lower() for col in cursor.description]
        records = []
        
        for row in cursor:
            record = {}
            for i, value in enumerate(row):
                if columns[i] == 'created_at' or columns[i] == 'updated_at':
                    record[columns[i]] = value.strftime("%Y-%m-%d %H:%M:%S") if value else None
                else:
                    record[columns[i]] = value
            records.append(record)
            
        logger.info(f"[INFO][get_custom_gtt_orders] Retrieved {len(records)} of {total_count} total orders")
        return {
            'records': records,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'pages': (total_count + per_page - 1) // per_page
        }
    except Exception as e:
        logger.error(f"[ERROR][get_custom_gtt_orders] Failed to fetch orders: {str(e)}", exc_info=True)
        raise
    finally:
        if connection:
            connection.close()

def get_order_by_id(order_id):
    """Get a single order by ID"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][get_order_by_id] Fetching order: {order_id}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT * FROM custom_gtt_orders
            WHERE id = :id
        """, {'id': order_id})
        
        row = cursor.fetchone()
        if not row:
            logger.warning(f"[WARNING][get_order_by_id] Order {order_id} not found")
            return None
            
        columns = [col[0].lower() for col in cursor.description]
        order = {}
        
        for i, value in enumerate(row):
            if columns[i] == 'created_at' or columns[i] == 'updated_at':
                order[columns[i]] = value.strftime("%Y-%m-%d %H:%M:%S") if value else None
            else:
                order[columns[i]] = value
                
        logger.debug(f"[DEBUG][get_order_by_id] Order found: {order}")
        return order
    except Exception as e:
        logger.error(f"[ERROR][get_order_by_id] Failed to fetch order {order_id}: {str(e)}", exc_info=True)
        raise
    finally:
        if connection:
            connection.close()

def update_kite_status(order_id, trigger_id):
    """Update order with Kite trigger ID and placed status"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][update_kite_status] Updating Kite status for order {order_id} with trigger ID {trigger_id}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE custom_gtt_orders
            SET placed_on_kite = 1,
                kite_trigger_id = :trigger_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """, {'id': order_id, 'trigger_id': trigger_id})
        
        affected = cursor.rowcount
        connection.commit()
        
        logger.info(f"[INFO][update_kite_status] Order {order_id} Kite status updated successfully ({affected} rows)")
        return affected > 0
    except Exception as e:
        logger.error(f"[ERROR][update_kite_status] Failed to update Kite status for order {order_id}: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def reset_kite_status(order_id):
    """Reset Kite status for an order"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][reset_kite_status] Resetting Kite status for order {order_id}")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE custom_gtt_orders
            SET placed_on_kite = 0,
                kite_trigger_id = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """, {'id': order_id})
        
        affected = cursor.rowcount
        connection.commit()
        
        logger.info(f"[INFO][reset_kite_status] Order {order_id} Kite status reset successfully ({affected} rows)")
        return affected > 0
    except Exception as e:
        logger.error(f"[ERROR][reset_kite_status] Failed to reset Kite status for order {order_id}: {str(e)}", exc_info=True)
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def get_orders_not_on_kite():
    """Get all orders that have not been placed on Kite yet"""
    logger = get_custom_logger()
    connection = None
    try:
        logger.debug(f"[DEBUG][get_orders_not_on_kite] Fetching orders not on Kite")
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT * FROM custom_gtt_orders
            WHERE placed_on_kite = 0 AND is_active = 1
            ORDER BY updated_at DESC
        """)
        
        columns = [col[0].lower() for col in cursor.description]
        orders = []
        
        for row in cursor:
            order = {}
            for i, value in enumerate(row):
                if columns[i] == 'created_at' or columns[i] == 'updated_at':
                    order[columns[i]] = value.strftime("%Y-%m-%d %H:%M:%S") if value else None
                else:
                    order[columns[i]] = value
            orders.append(order)
            
        logger.info(f"[INFO][get_orders_not_on_kite] Found {len(orders)} orders not on Kite")
        return orders
    except Exception as e:
        logger.error(f"[ERROR][get_orders_not_on_kite] Failed to fetch orders not on Kite: {str(e)}", exc_info=True)
        raise
    finally:
        if connection:
            connection.close()

def place_order_on_kite(order_id, kite):
    """Place a custom GTT order on Kite"""
    logger = get_custom_logger()
    try:
        # Get order details
        order = get_order_by_id(order_id)
        if not order:
            logger.error(f"[ERROR][place_order_on_kite] Order {order_id} not found")
            raise ValueError(f"Order {order_id} not found")
            
        if order['placed_on_kite']:
            logger.warning(f"[WARNING][place_order_on_kite] Order {order_id} already placed on Kite")
            return {'trigger_id': order['kite_trigger_id']}
            
        # Prepare trigger values
        trigger_values = []
        if order['trigger_type'] == 'two-leg':
            if order['trigger_values']:
                trigger_values = [float(x.strip()) for x in str(order['trigger_values']).split(',')]
            elif order['target_price'] and order['stop_loss']:
                trigger_values = [float(order['stop_loss']), float(order['target_price'])]
        elif order['trigger_price']:
            trigger_values = [float(order['trigger_price'])]
            
        if not trigger_values:
            logger.error(f"[ERROR][place_order_on_kite] No trigger values for order {order_id}")
            raise ValueError(f"No trigger values for order {order_id}")
            
        # Get last price if not provided
        last_price = order['last_price']
        if not last_price:
            instrument = f"{order['exchange']}:{order['symbol']}"
            quote = kite.quote([instrument])
            last_price = quote[instrument]['last_price']
            # Update order with current market price
            update_custom_gtt_order(order_id, {'last_price': last_price})
            
        # Prepare orders list
        if order['trigger_type'] == 'single' or len(trigger_values) == 1:
            kite_orders = [{
                "transaction_type": order['order_type'],
                "quantity": int(order['quantity']),
                "price": trigger_values[0],
                "order_type": "LIMIT",
                "product": "CNC"
            }]
        elif order['trigger_type'] == 'two-leg' and len(trigger_values) == 2:
            # For SELL orders with two-leg
            if order['order_type'] != 'SELL':
                logger.error(f"[ERROR][place_order_on_kite] Two-leg orders only supported for SELL, not {order['order_type']}")
                raise ValueError(f"Two-leg orders only supported for SELL, not {order['order_type']}")
                
            stop_loss, target = trigger_values
            kite_orders = [
                {
                    "transaction_type": "SELL",
                    "quantity": int(order['quantity']),
                    "price": target,
                    "order_type": "LIMIT",
                    "product": "CNC"
                },
                {
                    "transaction_type": "SELL",
                    "quantity": int(order['quantity']),
                    "price": stop_loss,
                    "order_type": "LIMIT",
                    "product": "CNC"
                }
            ]
        else:
            logger.error(f"[ERROR][place_order_on_kite] Invalid trigger configuration for order {order_id}")
            raise ValueError(f"Invalid trigger configuration for order {order_id}")
            
        # Place GTT order on Kite
        logger.debug(f"[DEBUG][place_order_on_kite] Placing order on Kite: {order['symbol']}, {order['order_type']}, trigger values: {trigger_values}")
        response = kite.place_gtt(
            trigger_type=order['trigger_type'],
            tradingsymbol=order['symbol'],
            exchange=order['exchange'],
            trigger_values=trigger_values,
            last_price=last_price,
            orders=kite_orders
        )
        
        trigger_id = response['trigger_id']
        logger.info(f"[INFO][place_order_on_kite] Order {order_id} placed on Kite with trigger ID {trigger_id}")
        
        # Update order with Kite trigger ID
        update_kite_status(order_id, trigger_id)
        
        return {'trigger_id': trigger_id}
    except Exception as e:
        logger.error(f"[ERROR][place_order_on_kite] Failed to place order {order_id} on Kite: {str(e)}", exc_info=True)
        raise

def place_multiple_orders_on_kite(order_ids, kite):
    """Place multiple custom GTT orders on Kite"""
    logger = get_custom_logger()
    results = {
        'success': [],
        'failed': []
    }
    
    for order_id in order_ids:
        try:
            result = place_order_on_kite(order_id, kite)
            results['success'].append({
                'order_id': order_id,
                'trigger_id': result['trigger_id']
            })
        except Exception as e:
            logger.error(f"[ERROR][place_multiple_orders_on_kite] Failed to place order {order_id}: {str(e)}", exc_info=True)
            results['failed'].append({
                'order_id': order_id,
                'error': str(e)
            })
    
    logger.info(f"[INFO][place_multiple_orders_on_kite] Placed {len(results['success'])} orders, {len(results['failed'])} failed")
    return results
