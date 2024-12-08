"""
AliExpress Refund Automation Tool
--------------------------------

This script automates the process of submitting refunds on AliExpress.

Usage:
    Normal Mode: 
        - Run the script normally to use the interactive UI mode
        - Select orders through the web interface
        - Process refunds in batches
    
    Development Mode:
        - Set development_mode=True in main()
        - Configure DEV_TEST_URLS with specific order URLs
        - Set IMAGE_PATH and REFUND_MESSAGE constants
        - Useful for testing specific orders or debugging

Configuration:
    - credentials.json must contain valid AliExpress login credentials
    - For development mode, configure the constants below
    - For normal mode, configuration is done through UI
"""

from playwright.sync_api import sync_playwright
from login_handler import LoginHandler
from button_handler import add_checkboxes_to_orders
from refund_link_collector import handle_refund_process
from refunder import process_refunds
import time
import logging
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Development Mode Constants
# Note: Only used when development_mode=True
DEV_TEST_URLS = [
    "https://www.aliexpress.com/p/order/detail.html?orderId=3043091352647135",  # 2 refund buttons
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042816799787135",  # 1 refund button
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938177135",  # 1 button, no refund link
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938197135"   # 1 refund button
]
IMAGE_PATH = "/home/schneider/Downloads/hermes_return_page-0001.jpg"  # Required for development mode
REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"
REFUND_MESSAGE_2 = "I do NOT AGREE. THE PACKAGE WAS RETURNED! I expect a full refund! Check the attached document!"

# Default refund messages for normal mode
DEFAULT_REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"
DEFAULT_REFUND_MESSAGE_2 = "I do NOT AGREE. THE PACKAGE WAS RETURNED! I expect a full refund! Check the attached document!"

def setup_credentials() -> tuple[str, str]:
    """Set up or load credentials before browser launch"""
    if os.path.exists('credentials.json'):
        print("\n📝 Found existing credentials.json")
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
        print("  ✅ Credentials loaded successfully")
        return creds['email'], creds['password']
    
    print("\n🔐 First-time setup: Credentials")
    print("You can either:")
    print("  1. Enter credentials now (they'll be saved locally)")
    print("  2. Skip and enter them in the browser later")
    print("\nNote: Credentials are stored locally in credentials.json")
    print("      You can inspect the code to verify security")
    
    choice = input("\nEnter credentials now? (y/n): ").strip().lower()
    if choice != 'y':
        print("  • Skipping credentials setup")
        return None, None
    
    email = input("\nEnter AliExpress email: ").strip()
    password = input("Enter AliExpress password: ").strip()
    
    with open('credentials.json', 'w') as f:
        json.dump({'email': email, 'password': password}, f)
    print("  • ✅ Credentials saved to credentials.json")
    
    return email, password

def get_initial_config() -> dict:
    """Get all configuration before browser launch"""
    config = {
        'pause_for_review': False,
        'image_path': None,
        'refund_message': DEFAULT_REFUND_MESSAGE
    }
    
    print("\n⚙️ Process Configuration:")
    choice = input("Pause for review after collecting refund links? (y/n): ").strip().lower()
    config['pause_for_review'] = choice == 'y'
    
    # Get image path
    while True:
        image_path = input("\nEnter the path to your proof image: ").strip()
        if os.path.exists(image_path):
            print(f"  • ✅ Image found: {image_path}")
            config['image_path'] = image_path
            break
        print("  • ❌ Image not found, please try again")
    
    # Get refund message
    print("\nUse default refund message?")
    print(f"  {DEFAULT_REFUND_MESSAGE}")
    choice = input("\nPress Enter to use default, or 'n' for custom message: ").strip().lower()
    if choice == 'n':
        config['refund_message'] = input("\nEnter your custom refund message: ").strip()
        print("  • ✅ Using custom message")
    else:
        print("  • ✅ Using default message")
    
    return config

def create_order_dict(urls: list[str]) -> dict:
    """
    Create initial dictionary with order IDs as keys.
    Args:
        urls: List of order URLs
    Returns:
        dict: Dictionary with order information
    """
    order_dict = {}
    for url in urls:
        if 'orderId=' in url:
            order_id = url.split('orderId=')[1].split('&')[0]
            order_dict[order_id] = {
                'order_url': url,
                'refund_urls': [],
                'refund_state': None
            }
    return order_dict

def process_batch(page, urls: list[str], config: dict):
    """Process a batch of orders."""
    order_dict = create_order_dict(urls)
    print(f"\n📋 Processing {len(urls)} orders:")
    for order_id in order_dict.keys():
        print(f"  • {order_id}")
    
    # Collect refund links
    order_dict = handle_refund_process(page, order_dict)
    
    # Optional pause for review
    if config['pause_for_review']:
        print("\n📋 Review collected refund links:")
        for order_id, data in order_dict.items():
            print(f"\nOrder {order_id}:")
            for url in data.get('refund_urls', []):
                print(f"  • {url}")
        input("\nPress Enter to start processing refunds (or Ctrl+C to quit)...")
    
    # Process refunds if links were found
    if any(data.get('refund_urls', []) for data in order_dict.values()):
        print("\n🎯 Starting refund submissions...")
        order_dict = process_refunds(page, order_dict, config['image_path'], 
                                   config['refund_message'], config['refund_message_2'])
    else:
        print("\n❌ No refund links found to process!")
        input("Press Enter to continue...")

def main(development_mode=False):
    """Main entry point for the script."""
    # Setup before browser launch
    if not development_mode:
        setup_credentials()
        config = get_initial_config()
    else:
        print("\n🔍 Starting in development mode...")
        config = {
            'pause_for_review': False,
            'image_path': IMAGE_PATH,
            'refund_message': REFUND_MESSAGE
        }
        if not os.path.exists(config['image_path']):
            raise ValueError(f"Development mode requires valid IMAGE_PATH. Current path not found: {config['image_path']}")
    
    print("\n🌐 Launching browser...")
    
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
            login_handler = LoginHandler(page)
            login_handler.login()
            login_handler.navigate_to_orders()
            
            # Add selection buttons in both modes
            add_checkboxes_to_orders(page)
            
            if development_mode:
                # Process test URLs directly
                print("\n📋 Processing test URLs...")
                order_dict = create_order_dict(DEV_TEST_URLS)
                process_batch(page, DEV_TEST_URLS, config)
            else:
                # Normal mode - wait for button click
                page.evaluate('''() => {
                    window.startProcessing = false;
                    document.addEventListener('processOrdersClicked', () => {
                        console.log('DEBUG: Process button clicked');
                        window.startProcessing = true;
                    });
                }''')
                
                print("\n✅ Setup complete!")
                print("Select orders and click 'Process All Refunds' to begin")
                print("Press Ctrl+C to quit")
                
                while True:
                    should_process = page.evaluate('window.startProcessing || false')
                    if should_process:
                        urls = page.evaluate('window.selectedOrderUrls || []')
                        if urls and len(urls) > 0:
                            process_batch(page, urls, config)
                            
                        # Reset for next batch
                        page.evaluate('''() => {
                            window.startProcessing = false;
                            window.selectedOrderUrls = [];
                        }''')
                        print("\n⏳ Waiting for new orders...")
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
        finally:
            input("\nPress Enter to close the browser...")
            browser.close()

if __name__ == "__main__":
    main(development_mode=True)