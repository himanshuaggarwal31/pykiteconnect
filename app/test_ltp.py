import os
import logging
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from kiteconnect.exceptions import KiteException

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LTPTester:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize KiteConnect
        api_key = os.getenv('API_KEY')
        if not api_key:
            logger.error("API_KEY not found in .env file")
            raise Exception("API_KEY not found in .env file")
            
        self.kite = KiteConnect(api_key=api_key)
          
        # Get access token from file
        try:
            with open(os.path.join(os.path.dirname(__file__), 'access_token.txt'), 'r') as f:
                access_token = f.read().strip()
                if not access_token:
                    raise Exception("access_token.txt is empty")
                self.kite.set_access_token(access_token)
                logger.info("Successfully set access token")
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
            
            try:
                # First try getting user profile to verify session is active
                profile = self.kite.profile()
                logger.info(f"Session active for user: {profile['user_name']}")
            except Exception as e:
                logger.error(f"Failed to get profile, session may be invalid: {str(e)}")
                raise

            # Get last prices
            ltp_data = self.kite.ltp(instruments)
            logger.info("LTP Response:")
            for key, value in ltp_data.items():
                logger.info(f"{key}: {value}")
            
        except KiteException as e:
            logger.error(f"KiteConnect API error: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error code: {getattr(e, 'code', 'N/A')}")
            logger.error(f"Error message: {getattr(e, 'message', str(e))}")
            raise
        except Exception as e:
            logger.error(f"Error testing LTP: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            raise

if __name__ == "__main__":
    tester = LTPTester()
    tester.test_ltp()
