from flask import Blueprint, jsonify, request, current_app
from datetime import datetime

api_bp = Blueprint('api', __name__)

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

        # Prepare orders list
        if trigger_type == 'single' and len(trigger_values) == 1:
            orders = [
                {
                    "transaction_type": transaction_type,
                    "quantity": quantity,
                    "price": trigger_values[0],
                    "order_type": "LIMIT",
                    "product": "CNC"
                }
            ]
        elif trigger_type == 'two-leg' and len(trigger_values) == 2:
            if transaction_type == 'BUY':
                return jsonify({'error': 'Two-leg orders are not supported for BUY transaction type.'}), 400
            stop_loss, target = trigger_values
            if not (stop_loss < last_price < target):
                return jsonify({'error': f'Invalid trigger values for SELL OCO: stop_loss ({stop_loss}) < last_price ({last_price}) < target ({target})'}), 400
            orders = [
                {
                    "transaction_type": "SELL",
                    "quantity": quantity,
                    "price": stop_loss,
                    "order_type": "LIMIT",
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
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    try:
        kite.delete_gtt(trigger_id=trigger_id)
        return jsonify({'message': 'Order deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/gtt/orders/bulk', methods=['POST'])
def create_bulk_orders():
    """Create multiple GTT orders in bulk."""
    data = request.json
    kite = current_app.config.get('kite')
    if kite is None:
        return jsonify({'error': 'KiteConnect is not initialized. Please check access_token.txt.'}), 500
    results = []
    for order in data.get('orders', []):
        try:
            tradingsymbol = order['tradingsymbol']
            exchange = order['exchange']
            trigger_type = order['trigger_type']
            trigger_values_raw = order['trigger_values']
            last_price = float(order['last_price'])
            transaction_type = order['transaction_type']
            quantity = int(order['quantity'])
            if trigger_type == 'two-leg':
                trigger_values = [float(x.strip()) for x in trigger_values_raw.replace(';', ',').split(',')]
            else:
                trigger_values = [float(trigger_values_raw.strip())]
            if trigger_type == 'single' and len(trigger_values) == 1:
                orders = [
                    {
                        "transaction_type": transaction_type,
                        "quantity": quantity,
                        "price": trigger_values[0],
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]
            elif trigger_type == 'two-leg' and len(trigger_values) == 2:
                if transaction_type == 'BUY':
                    results.append({'success': False, 'error': 'Two-leg orders are not supported for BUY', 'symbol': tradingsymbol})
                    continue
                stop_loss, target = trigger_values
                if not (stop_loss < last_price < target):
                    results.append({'success': False, 'error': f'Invalid trigger values for SELL OCO: stop_loss ({stop_loss}) < last_price ({last_price}) < target ({target})', 'symbol': tradingsymbol})
                    continue
                orders = [
                    {
                        "transaction_type": "SELL",
                        "quantity": quantity,
                        "price": stop_loss,
                        "order_type": "LIMIT",
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
            else:
                results.append({'success': False, 'error': 'Invalid trigger_type or trigger_values', 'symbol': tradingsymbol})
                continue
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
