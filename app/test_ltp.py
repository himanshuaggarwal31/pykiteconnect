import os
import logging
from dotenv import load_dotenv
from kiteconnect import KiteConnect

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LTPTester:
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

    def test_ltp(self):
        """Test LTP fetch functionality"""
        try:
            # Test with a few symbols
            instruments = ["NSE:INFY", "NSE:TCS", "NSE:RELIANCE", "NSE:HDFCBANK", "NSE:RELAXO"]
            logger.info(f"Fetching LTP for: {instruments}")
            
            # Get last prices
            ltp_data = self.kite.ltp(instruments)
            logger.info("LTP Response:")
            for key, value in ltp_data.items():
                logger.info(f"{key}: {value}")
            
        except Exception as e:
            logger.error(f"Error testing LTP: {str(e)}")

if __name__ == "__main__":
    tester = LTPTester()
    tester.test_ltp()
