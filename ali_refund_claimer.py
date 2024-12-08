from playwright.sync_api import sync_playwright
from login_handler import LoginHandler
from button_handler import add_checkboxes_to_orders
from refund_link_collector import handle_refund_process
from refunder import process_refunds
import time

# Constants
IMAGE_PATH = "/home/schneider/Downloads/hermes_return_page-0001.jpg"
REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"

# Test URLs for development
DEV_TEST_URLS = [
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938137135",
    "https://www.aliexpress.com/p/order/detail.html?orderId=3044357010087135",
    # Add more URLs as needed
]

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
    print(f"\n🔍 Order State after {stage}:")
    print("-"*20)
    for order_id, data in order_dict.items():
        print(f"\nOrder ID: {order_id}")
        for key, value in data.items():
            print(f"  {key}: {value}")
    print("raw dictionary:")
    print(order_dict)
    print("-"*20)

def dev_mode(page):
    """Development mode: directly process test URLs"""
    print("\n🔍 Starting development test mode...")
    
    # Create initial order dictionary
    order_dict = create_order_dict(DEV_TEST_URLS)
    print_order_state(order_dict, "initialization")
    
    # Get refund URLs
    order_dict = handle_refund_process(page, order_dict)
    print_order_state(order_dict, "getting refund URLs")
    
    # Process refunds
    if any(data['refund_url'] for data in order_dict.values()):
        print("\n🎯 Starting refund submissions...")
        order_dict = process_refunds(page, order_dict, IMAGE_PATH, REFUND_MESSAGE)
        print_order_state(order_dict, "refund processing")

def main(development_mode=True):  # Set to True for testing
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
                # Run development test mode
                dev_mode(page)
            else:
                # Normal operation mode
                add_checkboxes_to_orders(page)
                
                # Setup processing trigger
                page.evaluate('''() => {
                    window.startProcessing = false;
                    document.addEventListener('processOrdersClicked', () => {
                        console.log('DEBUG: Process button clicked');
                        window.startProcessing = true;
                    });
                }''')
                
                print("\nSetup complete!")
                print("Select orders and click 'Process Selected Orders' to begin")
                print("Press Ctrl+C when you want to quit.")
                
                while True:
                    try:
                        should_process = page.evaluate('window.startProcessing || false')
                        if should_process:
                            urls = page.evaluate('window.selectedOrderUrls || []')
                            if urls and len(urls) > 0:
                                print(f"\nProcessing {len(urls)} orders...")
                                # Get refund URLs
                                order_to_refund = handle_refund_process(page, urls, REFUND_MESSAGE)
                                
                                if order_to_refund:
                                    print("\n🎯 Starting refund submissions...")
                                    # Process all refund URLs
                                    refund_urls = list(order_to_refund.values())
                                    process_refunds(page, refund_urls, IMAGE_PATH, REFUND_MESSAGE)
                                
                                # Reset flags after processing
                                page.evaluate('''() => {
                                    window.startProcessing = false;
                                    window.selectedOrderUrls = [];
                                }''')
                                print("\nWaiting for new orders to process...")
                        time.sleep(1)
                    except Exception as e:
                        print(f"ERROR in main loop: {str(e)}")
                        import traceback
                        print(traceback.format_exc())
                
        except KeyboardInterrupt:
            print("\nClosing browser...")
        finally:
            input("Press Enter to close the browser...")
            browser.close()

if __name__ == "__main__":
    main(development_mode=True)  # Set to True for testing, False for normal operation