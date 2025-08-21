from flask import Blueprint, render_template, request, jsonify, current_app
import oracledb
import logging
from decimal import Decimal, InvalidOperation
import traceback
import sys
import os

# Add the parent directory to access auth module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from auth.simple_oauth import login_required, get_current_user
from auth.access_control import feature_required, log_user_action

custom_data_bp = Blueprint('custom_data', __name__)
logger = logging.getLogger('custom_data')

def validate_decimal(value, field_name):
    """Validate and convert string to Decimal"""
    try:
        if value is not None:
            return Decimal(str(value))
        return None
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.error(f"Invalid decimal value for {field_name}: {value}")
        raise ValueError(f"Invalid decimal value for {field_name}")

@custom_data_bp.route('/')
@login_required
@feature_required('custom_data')
@log_user_action('view_custom_data')
def index():
    return render_template('custom_data/index.html')

@custom_data_bp.route("/fetch", methods=["GET"])
@login_required
@feature_required('custom_data')
@log_user_action('fetch_custom_data')
def fetch_data():
    """Fetch data from the Custom_data table and return it as JSON."""
    logger.info("Fetching all custom data records")
    connection = None
    cursor = None
    
    try:
        connection = current_app.config['oracle_connection']
        cursor = connection.cursor()
        query = """
            SELECT Symbol, Quantity, Avg_Price, S1, S2, S3, S4, S5 
            FROM Custom_data 
            ORDER BY Symbol
        """
        logger.debug(f"Executing query: {query}")
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [col[0].upper() for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        logger.info(f"Successfully fetched {len(data)} records")
        return jsonify(data)
    
    except oracledb.DatabaseError as e:
        error, = e.args
        logger.error(f"Database error in fetch_data: {error.code} - {error.message}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Database error: {error.message}"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in fetch_data: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "An unexpected error occurred"}), 500
    
    finally:
        if cursor:
            cursor.close()

@custom_data_bp.route("/update", methods=["POST"])
@login_required
@feature_required('custom_data')
@log_user_action('update_custom_data')
def update_data():
    """Update a specific cell in the Custom_data table."""
    logger.info("Processing update request")
    connection = None
    cursor = None
    
    try:
        data = request.json
        symbol = data.get("Symbol")
        column = data.get("Column")
        value = data.get("Value")
        
        logger.info(f"Update request for Symbol: {symbol}, Column: {column}, Value: {value}")
        
        # Input validation
        if not symbol:
            logger.error("Missing required field: Symbol")
            return jsonify({"error": "Symbol is required"}), 400
            
        # Validate column names to prevent SQL injection
        valid_columns = {"Symbol", "Quantity", "Avg_Price", "S1", "S2", "S3", "S4", "S5"}
        if column not in valid_columns:
            logger.error(f"Invalid column name: {column}")
            return jsonify({"error": f"Invalid column: {column}"}), 400
        
        # Validate decimal values
        if column in {"Quantity", "Avg_Price", "S1", "S2", "S3", "S4", "S5"}:
            try:
                value = validate_decimal(value, column)
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

        connection = current_app.config['oracle_connection']
        cursor = connection.cursor()
        
        query = f"""
            MERGE INTO Custom_data target
            USING (SELECT :symbol AS symbol, :value AS value FROM dual) source
            ON (target.Symbol = source.symbol)
            WHEN MATCHED THEN
                UPDATE SET
                    {column} = source.value,
                    upd_date = TRUNC(SYSDATE)
            WHEN NOT MATCHED THEN
                INSERT (Symbol, {column}, upd_date)
                VALUES (source.symbol, source.value, TRUNC(SYSDATE))
        """
        logger.debug(f"Executing query: {query}")
        cursor.execute(query, {"value": value, "symbol": symbol})
        connection.commit()
        logger.info(f"Successfully updated {symbol} - {column}")
        return jsonify({"message": "Data updated successfully"})
    
    except oracledb.DatabaseError as e:
        error, = e.args
        logger.error(f"Database error in update_data: {error.code} - {error.message}")
        logger.error(traceback.format_exc())
        if connection:
            connection.rollback()
        return jsonify({"error": f"Database error: {error.message}"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in update_data: {str(e)}")
        logger.error(traceback.format_exc())
        if connection:
            connection.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500
    
    finally:
        if cursor:
            cursor.close()

@custom_data_bp.route("/delete", methods=["POST"])
@login_required
@feature_required('custom_data')
@log_user_action('delete_custom_data')
def delete_data():
    """Delete a record from the Custom_data table based on the Symbol."""
    logger.info("Processing delete request")
    connection = None
    cursor = None
    
    try:
        data = request.json
        symbol = data.get("Symbol")
        
        logger.info(f"Delete request for Symbol: {symbol}")
        
        if not symbol:
            logger.error("Missing required field: Symbol")
            return jsonify({"error": "Symbol is required"}), 400

        connection = current_app.config['oracle_connection']
        cursor = connection.cursor()
        query = "DELETE FROM Custom_data WHERE Symbol = :symbol"
        logger.debug(f"Executing query: {query}")
        cursor.execute(query, {"symbol": symbol})
        connection.commit()
        logger.info(f"Successfully deleted record for Symbol: {symbol}")
        return jsonify({"message": f"Record for Symbol '{symbol}' deleted successfully"})
    
    except oracledb.DatabaseError as e:
        error, = e.args
        logger.error(f"Database error in delete_data: {error.code} - {error.message}")
        logger.error(traceback.format_exc())
        if connection:
            connection.rollback()
        return jsonify({"error": f"Database error: {error.message}"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in delete_data: {str(e)}")
        logger.error(traceback.format_exc())
        if connection:
            connection.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500
    
    finally:
        if cursor:
            cursor.close()

@custom_data_bp.route("/add", methods=["POST"])
@login_required
@feature_required('custom_data')
@log_user_action('add_custom_data')
def add_data():
    """Add a new record to the Custom_data table."""
    logger.info("Processing add request")
    connection = None
    cursor = None
    
    try:
        data = request.json
        symbol = data.get("Symbol")
        
        # Log incoming data
        logger.info(f"Add request with data: {data}")
        
        # Validate required fields
        if not symbol:
            logger.error("Missing required field: Symbol")
            return jsonify({"error": "Symbol is required"}), 400
            
        # Convert and validate decimal fields
        try:
            quantity = validate_decimal(data.get("Quantity"), "Quantity")
            avg_price = validate_decimal(data.get("Avg_Price"), "Avg_Price")
            s1 = validate_decimal(data.get("S1"), "S1")
            s2 = validate_decimal(data.get("S2"), "S2")
            s3 = validate_decimal(data.get("S3"), "S3")
            s4 = validate_decimal(data.get("S4"), "S4")
            s5 = validate_decimal(data.get("S5"), "S5")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        connection = current_app.config['oracle_connection']
        cursor = connection.cursor()
        
        # Check if symbol already exists
        cursor.execute("SELECT 1 FROM Custom_data WHERE Symbol = :symbol", {"symbol": symbol})
        if cursor.fetchone():
            logger.error(f"Symbol {symbol} already exists")
            return jsonify({"error": f"Symbol {symbol} already exists"}), 409
            
        query = """
            INSERT INTO Custom_data 
            (Symbol, Quantity, Avg_Price, S1, S2, S3, S4, S5, upd_date)
            VALUES (:symbol, :quantity, :avg_price, :s1, :s2, :s3, :s4, :s5, TRUNC(SYSDATE))
        """
        params = {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": avg_price,
            "s1": s1,
            "s2": s2,
            "s3": s3,
            "s4": s4,
            "s5": s5
        }
        
        logger.debug(f"Executing query: {query}")
        logger.debug(f"Query parameters: {params}")
        
        cursor.execute(query, params)
        connection.commit()
        logger.info(f"Successfully added new record for Symbol: {symbol}")
        return jsonify({"message": "Data added successfully"})
    
    except oracledb.DatabaseError as e:
        error, = e.args
        logger.error(f"Database error in add_data: {error.code} - {error.message}")
        logger.error(traceback.format_exc())
        if connection:
            connection.rollback()
        return jsonify({"error": f"Database error: {error.message}"}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in add_data: {str(e)}")
        logger.error(traceback.format_exc())
        if connection:
            connection.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500
    
    finally:
        if cursor:
            cursor.close()
