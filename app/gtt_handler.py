import os
from kiteconnect import KiteConnect
import pandas as pd
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress debug logs from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)

class GTTHandler:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize KiteConnect
        self.kite = KiteConnect(api_key=os.getenv('API_KEY'))
          # Get access token from file
        try:
            with open(os.path.join(os.path.dirname(__file__), 'access_token.txt'), 'r') as f:
                access_token = f.read().strip()
                self.kite.set_access_token(access_token)
        except FileNotFoundError:
            logger.error("access_token.txt not found. Please run AutoConnect.py first to generate access token.")
            raise Exception("Please run AutoConnect.py first to generate access token")
        except Exception as e:
            logger.error(f"Error setting access token: {str(e)}")
            raise

    # Refactored place_gtt_order function to align with documented code
    def place_gtt_order(self, row):
        """Place a GTT order based on CSV row data"""
        try:
            # Convert trigger values from string to list
            trigger_values = [float(x.strip()) for x in str(row['trigger_values']).split(';')]

            # Prepare orders list with validation
            if row['trigger_type'] == 'single' and len(trigger_values) == 1:
                orders = [
                    {
                        "transaction_type": row['transaction_type'],
                        "quantity": int(row['quantity']),
                        "price": trigger_values[0],  # Use trigger value as the order price
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]
            elif row['trigger_type'] == 'two-leg' and len(trigger_values) == 2:  # OCO order
                if row['transaction_type'] == 'BUY':
                    logger.warning("Two-leg orders are not supported for BUY transaction type")
                    return None
                
                # Validate trigger prices for SELL OCO order
                last_price = float(row['last_price'])
                stop_loss, target = trigger_values[0], trigger_values[1]
                
                # For SELL OCO orders:
                # - First trigger (stop loss) must be below last price
                # - Second trigger (target) must be above last price
                if not (stop_loss < last_price < target):
                    logger.error(f"Invalid trigger values for SELL OCO: stop_loss ({stop_loss}) < last_price ({last_price}) < target ({target})")
                    return None
                
                # Set order prices same as trigger values
                orders = [
                    {
                        "transaction_type": "SELL",
                        "quantity": int(row['quantity']),
                        "price": stop_loss,  # Use exact stop loss value
                        "order_type": "LIMIT",
                        "product": "CNC"
                    },
                    {
                        "transaction_type": "SELL",
                        "quantity": int(row['quantity']),
                        "price": target,     # Use exact target value
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]
            else:
                logger.error(f"Invalid trigger_type or trigger_values count for {row['tradingsymbol']}")
                return None

            # Place GTT order using documented method
            result = self.kite.place_gtt(
                trigger_type=row['trigger_type'],
                tradingsymbol=row['tradingsymbol'],
                exchange=row['exchange'],
                trigger_values=trigger_values,
                last_price=float(row['last_price']),
                orders=orders
            )

            logger.info(f"GTT order placed successfully for {row['tradingsymbol']}. Trigger ID: {result['trigger_id']}")
            return result['trigger_id']

        except Exception as e:
            logger.error(f"Error placing GTT order for {row.get('tradingsymbol', '')}: {str(e)}")
            return None

    def modify_gtt_order(self, trigger_id, row):
        """Modify an existing GTT order"""
        try:
            trigger_values = [float(x.strip()) for x in str(row['trigger_values']).split(';')]
            
            # Prepare orders list
            if row['trigger_type'] == 'single':
                orders = [
                    {
                        "transaction_type": row['transaction_type'],
                        "quantity": int(row['quantity']),
                        "price": float(row['price']),
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]
            else:  # two-leg order
                if row['transaction_type'] == 'BUY':
                    logger.warning("Two-leg orders are not allowed for BUY transaction type. Skipping order.")
                    return False
                
                # Validate trigger prices for SELL OCO order
                last_price = float(row['last_price'])
                stop_loss_price = trigger_values[0]  # Lower trigger
                target_price = trigger_values[1]     # Higher trigger
                
                orders = [
                    {
                        "transaction_type": "SELL",  # Main order (stop-loss)
                        "quantity": int(row['quantity']),
                        "price": stop_loss_price - 1,
                        "order_type": "LIMIT",
                        "product": "CNC"
                    },
                    {
                        "transaction_type": "SELL",  # Secondary order (target)
                        "quantity": int(row['quantity']),
                        "price": target_price + 1,
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]
            
            # Modify GTT order
            result = self.kite.modify_gtt(
                trigger_id=trigger_id,
                trigger_type=row['trigger_type'],
                tradingsymbol=row['tradingsymbol'],
                exchange=row['exchange'],
                trigger_values=trigger_values,
                last_price=float(row['last_price']),
                orders=orders
            )
            
            logger.info(f"GTT order modified successfully for {row['tradingsymbol']}. Trigger ID: {trigger_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error modifying GTT order for {row['tradingsymbol']}: {str(e)}")
            return False

    def delete_gtt_order(self, trigger_id):
        """Delete a GTT order"""
        try:
            self.kite.delete_gtt(trigger_id=trigger_id)
            logger.info(f"GTT order deleted successfully. Trigger ID: {trigger_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting GTT order {trigger_id}: {str(e)}")
            return False

    def get_all_gtt_orders(self):
        """Get all GTT orders"""
        try:
            return self.kite.get_gtts()
        except Exception as e:
            logger.error(f"Error fetching GTT orders: {str(e)}")
            return []

    def check_holdings(self):
        """Get holdings and return a dict of tradingsymbol -> quantity"""
        try:
            holdings = self.kite.holdings()  # Using correct method name
            holdings_dict = {}
            for holding in holdings:
                holdings_dict[holding['tradingsymbol']] = holding.get('quantity', 0)
                logger.info(f"Found holding: {holding['tradingsymbol']}, Quantity: {holding.get('quantity', 0)}")
            return holdings_dict
        except Exception as e:
            logger.error(f"Error fetching holdings: {str(e)}")
            return {}

    def try_place_oco_order(self, row):
        """Try placing OCO order using trigger values from CSV"""
        try:
            # For SELL orders, check holdings first
            if row['transaction_type'] == 'SELL':
                holdings = self.check_holdings()
                if row['tradingsymbol'] not in holdings:
                    logger.error(f"Cannot place SELL order for {row['tradingsymbol']}: No holdings found")
                    return None
                if holdings[row['tradingsymbol']] < int(row['quantity']):
                    logger.error(f"Cannot place SELL order for {row['tradingsymbol']}: "
                               f"Insufficient holdings (have: {holdings[row['tradingsymbol']]}, need: {row['quantity']})")
                    return None

            # Get trigger values from CSV
            trigger_values = [float(x.strip()) for x in str(row['trigger_values']).split(';')]
            if len(trigger_values) != 2:
                logger.error(f"OCO order requires exactly 2 trigger values, got {len(trigger_values)}")
                return None

            last_price = float(row['last_price'])
            stop_loss, target = trigger_values[0], trigger_values[1]

            if row['transaction_type'] == 'SELL':
                # For SELL OCO orders:
                # - First trigger (stop loss) must be below last price
                # - Second trigger (target) must be above last price
                if not (stop_loss < last_price < target):
                    logger.error(f"Invalid trigger values for SELL OCO: stop_loss ({stop_loss}) < last_price ({last_price}) < target ({target})")
                    return None

                # Set order prices same as trigger values
                orders = [
                    {
                        "transaction_type": "SELL",
                        "quantity": int(row['quantity']),
                        "price": stop_loss,  # Use exact stop loss value
                        "order_type": "LIMIT",
                        "product": "CNC"
                    },
                    {
                        "transaction_type": "SELL",
                        "quantity": int(row['quantity']),
                        "price": target,     # Use exact target value
                        "order_type": "LIMIT",
                        "product": "CNC"
                    }
                ]

                logger.info(f"Placing OCO order for {row['tradingsymbol']} (Holdings: {holdings[row['tradingsymbol']]}): "
                           f"SL Trigger={stop_loss:.2f} (Order: {orders[0]['price']:.2f}), "
                           f"Target Trigger={target:.2f} (Order: {orders[1]['price']:.2f})")

                # Place GTT order using documented method
                result = self.kite.place_gtt(
                    trigger_type=row['trigger_type'],
                    tradingsymbol=row['tradingsymbol'],
                    exchange=row['exchange'],
                    trigger_values=trigger_values,
                    last_price=last_price,
                    orders=orders
                )

                if result and 'trigger_id' in result:
                    logger.info(f"Successfully placed OCO order")
                    return result['trigger_id']
            
            else:
                logger.warning("Two-leg orders are not supported for BUY transaction type")
                return None

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error placing GTT order for {row['tradingsymbol']}: {error_msg}")
            return None

    def process_csv_orders(self, csv_file):
        """Process GTT orders from CSV file"""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Get existing GTT orders
            existing_gtts = self.get_all_gtt_orders()
            existing_symbols = {gtt['condition']['tradingsymbol']: gtt['id'] for gtt in existing_gtts}
            
            results = []
            for _, row in df.iterrows():
                tradingsymbol = row['tradingsymbol']
                
                if tradingsymbol in existing_symbols:
                    # Modify existing GTT order
                    success = self.modify_gtt_order(existing_symbols[tradingsymbol], row)
                    action = 'modified' if success else 'failed to modify'
                    trigger_id = existing_symbols[tradingsymbol] if success else None
                else:
                    # Place new GTT order
                    if row['trigger_type'] == 'two-leg':
                        # For OCO orders, try with increasingly wider spreads
                        trigger_id = self.try_place_oco_order(row)
                    else:
                        # For single-leg orders, try once
                        trigger_id = self.place_gtt_order(row)
                    action = 'placed' if trigger_id else 'failed to place'
                
                results.append({
                    'tradingsymbol': tradingsymbol,
                    'action': action,
                    'trigger_id': trigger_id
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV orders: {str(e)}")
            return {}

    def export_gtts_to_csv(self, filename='current_gtt_orders.csv'):
        """Export current GTT orders to CSV file"""
        try:
            gtts = self.get_all_gtt_orders()
            if not gtts:
                logger.warning("No GTT orders found to export")
                return False

            # Prepare data for CSV
            rows = []
            for gtt in gtts:
                condition = gtt['condition']
                trigger_values = ';'.join(str(x) for x in condition['trigger_values'])
                
                # For each order in the GTT
                for order in gtt['orders']:
                    row = {
                        'tradingsymbol': condition['tradingsymbol'],
                        'exchange': condition['exchange'],
                        'trigger_type': gtt['type'],
                        'trigger_values': trigger_values,
                        'last_price': condition['last_price'],
                        'transaction_type': order['transaction_type'],
                        'quantity': order['quantity'],
                        'price': order['price'],
                        'status': gtt['status'],
                        'gtt_id': gtt['id'],
                        'created_at': gtt['created_at'],
                        'expires_at': gtt['expires_at']
                    }
                    rows.append(row)

            # Write to CSV
            if rows:
                import pandas as pd
                df = pd.DataFrame(rows)
                df.to_csv(filename, index=False)
                logger.info(f"GTT orders exported to {filename}")
                return True
            else:
                logger.warning("No GTT orders data to export")
                return False

        except Exception as e:
            logger.error(f"Error exporting GTT orders to CSV: {str(e)}")
            return False

def main():
    # Initialize GTT handler
    gtt_handler = GTTHandler()
    
    # Process orders from CSV
    results = gtt_handler.process_csv_orders('gtt_orders.csv')

    
    # Print results
    for result in results:
        print(f"Symbol: {result['tradingsymbol']}, Action: {result['action']}, Trigger ID: {result['trigger_id']}")
    
    # Export current GTT orders if --export flag is provided
    import sys
    if '--export' in sys.argv:
        print("\nExporting current GTT orders...")
        if gtt_handler.export_gtts_to_csv():
            print("GTT orders exported to current_gtt_orders.csv")
        else:
            print("Failed to export GTT orders")

    # Print all current GTT orders
    print("\nCurrent GTT Orders:")
    current_gtts = gtt_handler.get_all_gtt_orders()
    for gtt in current_gtts:
        try:
            print(f"Symbol: {gtt['condition']['tradingsymbol']}, ID: {gtt['id']}, Status: {gtt['status']}")
        except KeyError as e:
            print(f"Error accessing GTT order details: {e}")

    # Delete successfully placed orders
    print("\nDeleting successful orders...")
    for result in results:
        if result['action'] == 'placed' and result['trigger_id']:
            if gtt_handler.delete_gtt_order(result['trigger_id']):
                print(f"Deleted GTT order for {result['tradingsymbol']} (Trigger ID: {result['trigger_id']})")
            else:
                print(f"Failed to delete GTT order for {result['tradingsymbol']} (Trigger ID: {result['trigger_id']})")

if __name__ == "__main__":
    main()
