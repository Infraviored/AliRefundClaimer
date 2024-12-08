from playwright.sync_api import sync_playwright
from login_handler import LoginHandler
from button_handler import add_checkboxes_to_orders
from refund_link_collector import handle_refund_process
from refunder import process_refunds
import time
import logging
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)
# Constants
IMAGE_PATH = "/home/schneider/Downloads/hermes_return_page-0001.jpg"
REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"
# Test URLs for development
DEV_TEST_URLS = [
    "https://www.aliexpress.com/p/order/detail.html?orderId=3043091352647135"
    # "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938137135",
    # "https://www.aliexpress.com/p/order/detail.html?orderId=3044357010087135",
]

# Default refund message
DEFAULT_REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"

def get_user_input():
    """Get refund message and image path from user"""
    print("\n🔧 Setup Configuration:")
    
    # Check for hardcoded image path
    if 'IMAGE_PATH' in globals():
        print(f"  • Using hardcoded image path: {IMAGE_PATH}")
        image_path = IMAGE_PATH
    else:
        while True:
            image_path = input("\nEnter the path to your proof image: ").strip()
            if os.path.exists(image_path):
                print(f"  • ✅ Image found: {image_path}")
                break
            print("  • ❌ Image not found, please try again")
    
    # Check for hardcoded refund message
    if 'REFUND_MESSAGE' in globals():
        print(f"  • Using hardcoded refund message")
        refund_message = REFUND_MESSAGE
    else:
        print("\nUse default refund message?")
        print(f"  {DEFAULT_REFUND_MESSAGE}")
        choice = input("\nPress Enter to use default, or 'n' for custom message: ").strip().lower()
        
        if choice == 'n':
            refund_message = input("\nEnter your custom refund message: ").strip()
            print(f"  • ✅ Using custom message")
        else:
            refund_message = DEFAULT_REFUND_MESSAGE
            print(f"  • ✅ Using default message")
    
    return image_path, refund_message



def create_order_dict(urls: list[str]) -> dict:
    """Create initial dictionary with order IDs as keys"""
    order_dict = {}
    for url in urls:
        if 'orderId=' in url:
            order_id = url.split('orderId=')[1].split('&')[0]
            order_dict[order_id] = {
                'order_url': url,
                'refund_url': None,
                'refund_state': None
            }
    return order_dict

def print_order_state(order_dict: dict, stage: str):
    """Debug print current state of orders"""
    logger.debug(f"\nOrder State after {stage}:")
    logger.debug("-"*20)
    for order_id, data in order_dict.items():
        logger.debug(f"\nOrder ID: {order_id}")
        for key, value in data.items():
            logger.debug(f"  {key}: {value}")
    logger.debug("\nRaw dictionary:")
    logger.debug(order_dict)
    logger.debug("-"*20)

def dev_mode(page):
    """Development mode: directly process test URLs"""
    print("\n🔍 Starting development test mode...")
    
    # Create initial order dictionary
    order_dict = create_order_dict(DEV_TEST_URLS)
    print("\n📋 Orders to process:")
    for order_id in order_dict.keys():
        print(f"  • {order_id}")
    print_order_state(order_dict, "initialization")
    
    # Get refund URLs
    order_dict = handle_refund_process(page, order_dict)
    print_order_state(order_dict, "getting refund URLs")
    
    # Process refunds
    if any(data['refund_url'] for data in order_dict.values()):
        print("\n🎯 Starting refund submissions...")
        order_dict = process_refunds(page, order_dict, IMAGE_PATH, REFUND_MESSAGE)
        print_order_state(order_dict, "refund processing")

def main(development_mode=True):
    # Get user input for configuration
    image_path, refund_message = get_user_input()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized',
                '--window-size=1920,1080',
                '--remote-debugging-port=9222'
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 1080},
            color_scheme='light',
            locale='en-US',
            timezone_id='Europe/Berlin'
        )
        
        page = context.new_page()
        
        # Disable webdriver detection
        page.evaluate('''() => {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        }''')
        
        try:
            # Login and navigate
            login_handler = LoginHandler(page)
            login_handler.login()
            login_handler.navigate_to_orders()
            
            if development_mode:
                dev_mode(page)
            else:
                add_checkboxes_to_orders(page)
                page.evaluate('''() => {
                    window.startProcessing = false;
                    document.addEventListener('processOrdersClicked', () => {
                        console.log('DEBUG: Process button clicked');
                        window.startProcessing = true;
                    });
                }''')
                
                print("\n✅ Setup complete!")
                print("Select orders and click 'Process Selected Orders' to begin")
                print("Press Ctrl+C to quit")
                
                while True:
                    try:
                        should_process = page.evaluate('window.startProcessing || false')
                        if should_process:
                            urls = page.evaluate('window.selectedOrderUrls || []')
                            if urls and len(urls) > 0:
                                order_dict = create_order_dict(urls)
                                print(f"\n📋 Processing {len(urls)} orders:")
                                for order_id in order_dict.keys():
                                    print(f"  • {order_id}")
                                
                                order_dict = handle_refund_process(page, order_dict)
                                if any(data['refund_url'] for data in order_dict.values()):
                                    order_dict = process_refunds(page, order_dict, image_path, refund_message)
                                
                                page.evaluate('''() => {
                                    window.startProcessing = false;
                                    window.selectedOrderUrls = [];
                                }''')
                                print("\n⏳ Waiting for new orders...")
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error in main loop: {str(e)}")
                        logger.debug(traceback.format_exc())
                
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
        finally:
            input("\nPress Enter to close the browser...")
            browser.close()

if __name__ == "__main__":
    main(development_mode=False)