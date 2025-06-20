import oracledb
from datetime import datetime
from db_config import get_connection, configuration
from flask import current_app

def create_custom_gtt_table():
    """Create the custom GTT orders table if it doesn't exist"""
    # Use direct connection for table creation since Flask app context might not be available
    with oracledb.connect(**configuration['db_config']) as connection:
        with connection.cursor() as cursor:
            # First try to add the last_price column if table exists
            try:
                cursor.execute("""
                    ALTER TABLE custom_gtt_orders 
                    ADD last_price NUMBER
                """)
                connection.commit()
            except oracledb.DatabaseError as e:
                if 'ORA-01430' in str(e):  # Column already exists
                    pass
                elif 'ORA-00942' in str(e):  # Table does not exist
                    pass
                else:
                    raise e

            # Create table if it doesn't exist
            cursor.execute('''
                BEGIN
                    EXECUTE IMMEDIATE 'CREATE TABLE custom_gtt_orders (
                        id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        symbol VARCHAR2(50) NOT NULL,
                        company_name VARCHAR2(100),
                        nifty_rank NUMBER,
                        order_type VARCHAR2(10) NOT NULL,
                        trigger_price NUMBER NOT NULL,
                        last_price NUMBER,
                        quantity NUMBER NOT NULL,
                        target_price NUMBER,
                        stop_loss NUMBER,
                        notes VARCHAR2(500),
                        tags VARCHAR2(200),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        is_active NUMBER(1) DEFAULT 1,
                        placed_on_kite NUMBER(1) DEFAULT 0,
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

def get_custom_gtt_orders(page=1, per_page=25, order_type=None, kite_status=None):
    """
    Fetch custom GTT orders with pagination and filters only (no search)
    Args:
        page: Current page number (1-based)
        per_page: Number of records per page
        order_type: Filter by order type (BUY/SELL)
        kite_status: Filter by Kite placement status (0/1)
    """
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        query = """
            SELECT id, symbol, company_name, nifty_rank, order_type, 
                   trigger_price, last_price, quantity, target_price, stop_loss, 
                   notes, tags, created_at, updated_at, is_active, 
                   placed_on_kite, kite_trigger_id
            FROM custom_gtt_orders
            WHERE is_active = 1
        """
        params = {}
        if order_type:
            query += " AND order_type = :order_type"
            params['order_type'] = order_type
        if kite_status:
            query += " AND placed_on_kite = :kite_status"
            params['kite_status'] = kite_status
        query += " ORDER BY id DESC OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY"
        params['offset'] = (page - 1) * per_page
        params['limit'] = per_page
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        records = [dict(zip(columns, row)) for row in rows]
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM custom_gtt_orders WHERE is_active = 1")
        total_count = cursor.fetchone()[0]
        return {
            'records': records,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }
    except Exception as e:
        return {'records': [], 'total_count': 0, 'error': str(e)}

def add_custom_gtt_order(data):
    """Add a new custom GTT order"""
    connection = None
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        out_id = cursor.var(int)
        
        cursor.execute("""
            INSERT INTO custom_gtt_orders (
                symbol, company_name, nifty_rank, order_type, 
                trigger_price, last_price, quantity, target_price, stop_loss, 
                notes, tags, updated_at
            ) VALUES (
                :symbol, :company_name, :nifty_rank, :order_type,
                :trigger_price, :last_price, :quantity, :target_price, :stop_loss,
                :notes, :tags, CURRENT_TIMESTAMP
            )
            RETURNING id INTO :id
        """, {
            'symbol': data['symbol'],
            'company_name': data.get('company_name'),
            'nifty_rank': data.get('nifty_rank'),
            'order_type': data['order_type'],
            'trigger_price': data['trigger_price'],
            'last_price': data.get('last_price'),  # Include last_price in insert
            'quantity': data['quantity'],
            'target_price': data.get('target_price'),
            'stop_loss': data.get('stop_loss'),
            'notes': data.get('notes'),
            'tags': data.get('tags'),
            'id': out_id
        })
        
        connection.commit()
        result = out_id.getvalue()
        cursor.close()
        return result
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Database error in add_custom_gtt_order: {str(e)}")
        raise
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass

def update_custom_gtt_order(order_id, data):
    """Update a custom GTT order"""
    connection = None
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        update_cols = []
        params = {'id': order_id}
        
        # Build dynamic update query based on provided fields
        for key in ['symbol', 'company_name', 'nifty_rank', 'order_type', 
                   'trigger_price', 'last_price', 'quantity', 'target_price', 
                   'stop_loss', 'notes', 'tags']:
            if key in data:
                update_cols.append(f"{key} = :{key}")
                params[key] = data[key]
        
        if update_cols:
            update_cols.append("updated_at = CURRENT_TIMESTAMP")
            query = f"""
                UPDATE custom_gtt_orders 
                SET {', '.join(update_cols)}
                WHERE id = :id
            """
            cursor.execute(query, params)
            connection.commit()
            cursor.close()
            return True
        return False
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Database error in update_custom_gtt_order: {str(e)}")
        raise
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass

def delete_custom_gtt_order(order_id):
    """Soft delete a custom GTT order"""
    connection = None
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        
        cursor.execute("""
            UPDATE custom_gtt_orders
            SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
        """, {'id': order_id})
        
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        if connection:
            connection.rollback()
        print(f"Database error in delete_custom_gtt_order: {str(e)}")
        raise
    finally:
        if connection:
            try:
                connection.close()
            except:
                pass

def update_kite_status(order_id, trigger_id):
    """Update Kite placement status for a custom GTT order"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE custom_gtt_orders
                SET placed_on_kite = 1, 
                    kite_trigger_id = :trigger_id,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """, {'id': order_id, 'trigger_id': trigger_id})
            connection.commit()
            return True

def reset_kite_status(order_id):
    """Reset Kite placement status when GTT is deleted"""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE custom_gtt_orders
                SET placed_on_kite = 0, 
                    kite_trigger_id = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """, {'id': order_id})
            connection.commit()
            return True

def get_orders_not_on_kite():
    """Fetch all custom GTT orders that are not yet placed on Kite"""
    try:
        connection = oracledb.connect(**configuration['db_config'])
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, symbol, company_name, nifty_rank, order_type, 
                   trigger_price, quantity, target_price, stop_loss, 
                   notes, tags, created_at, updated_at, is_active, 
                   placed_on_kite, kite_trigger_id
            FROM custom_gtt_orders
            WHERE is_active = 1 
            AND placed_on_kite = 0
            ORDER BY symbol
        """)
        columns = [col[0].lower() for col in cursor.description]
        result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return result
    except Exception as e:
        print(f"Database error in get_orders_not_on_kite: {str(e)}")
        raise
