from flask import Flask, jsonify, request, render_template
import oracledb
from app.gtt_webapp.db_config import configuration  # Import the configuration file
import warnings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning)

# Initialize Flask app
app = Flask(__name__)

# Use the db_config from the imported configuration
db_config = configuration['db_config']
connection = oracledb.connect(**db_config)


@app.route("/")
def index():
    return render_template("index.html")  # Frontend template for displaying the table


@app.route("/fetch_data", methods=["GET"])
def fetch_data():
    """
    Fetch data from the Custom_data table and return it as JSON.
    """
    try:
        cursor = connection.cursor()
        # Fetch specific columns in the desired order
        query = "SELECT Symbol, Quantity, Avg_Price, S1, S2, S3, S4, S5 FROM Custom_data ORDER BY Symbol"
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [col[0].upper() for col in cursor.description]
        # columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        return jsonify(data)
    except oracledb.Error as error:
        return jsonify({"error": str(error)}), 500


@app.route("/update_data", methods=["POST"])
def update_data():
    """
    Update a specific cell in the Custom_data table.
    """
    try:
        data = request.json
        symbol = data.get("Symbol")
        column = data.get("Column")
        value = data.get("Value")

        # Validate column names to prevent SQL injection
        valid_columns = {"Symbol", "Quantity", "Avg_Price", "S1", "S2", "S3", "S4", "S5"}
        if column not in valid_columns:
            return jsonify({"error": f"Invalid column: {column}"}), 400

        # Perform the update query
        cursor = connection.cursor()
        # query = f"UPDATE Custom_data SET {column} = :value, upd_date = TRUNC(SYSDATE) WHERE Symbol = :symbol"
        query = f"""MERGE INTO Custom_data target
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
        cursor.execute(query, {"value": value, "symbol": symbol})
        connection.commit()
        return jsonify({"message": "Data updated successfully"})
    except oracledb.Error as error:
        return jsonify({"error": str(error)}), 500


@app.route("/delete_data", methods=["POST"])
def delete_data():
    """
    Delete a record from the Custom_data table based on the Symbol.
    """
    try:
        data = request.json
        symbol = data.get("Symbol")

        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400

        cursor = connection.cursor()
        query = "DELETE FROM Custom_data WHERE Symbol = :symbol"
        cursor.execute(query, {"symbol": symbol})
        connection.commit()
        return jsonify({"message": f"Record for Symbol '{symbol}' deleted successfully"})
    except oracledb.Error as error:
        return jsonify({"error": str(error)}), 500


@app.route("/add_data", methods=["POST"])
def add_data():
    """
    Add a new record to the Custom_data table.
    """
    try:
        data = request.json
        symbol = data.get("Symbol")
        quantity = data.get("Quantity")
        avg_price = data.get("Avg_Price")
        s1 = data.get("S1")
        s2 = data.get("S2")
        s3 = data.get("S3")
        s4 = data.get("S4")
        s5 = data.get("S5")

        # Ensure all required fields are provided
        if not symbol:
            return jsonify({"error": "Symbol is required"}), 400

        cursor = connection.cursor()
        query = """
            INSERT INTO Custom_data (Symbol, Quantity, Avg_Price, S1, S2, S3, S4, S5, upd_date)
            VALUES (:symbol, :quantity, :avg_price, :s1, :s2, :s3, :s4, :s5, TRUNC(SYSDATE))
        """
        cursor.execute(query, {
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": avg_price,
            "s1": s1,
            "s2": s2,
            "s3": s3,
            "s4": s4,
            "s5": s5
        })
        connection.commit()
        return jsonify({"message": "Data added successfully"})
    except oracledb.Error as error:
        return jsonify({"error": str(error)}), 500



if __name__ == "__main__":
    app.run(debug=True)
