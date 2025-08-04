from flask import Blueprint, render_template

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug-sql-gtt')
def debug_sql_gtt():
    return render_template('debug_sql_gtt.html')
