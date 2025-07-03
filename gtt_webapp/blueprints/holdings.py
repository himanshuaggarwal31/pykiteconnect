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
