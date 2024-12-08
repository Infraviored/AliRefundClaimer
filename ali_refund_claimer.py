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
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('DEBUG') else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Development Mode Constants
# Note: Only used when development_mode=True

#   • 3044357010127135
#   • 3043329396767135
#   • 3043091352607135
#   • 3043091352627135
#   • 3043091352647135
#   • 3042816799787135
#   • 3042417938137135
#   • 3042417938157135
#   • 3042417938177135
#   • 3042417938197135
#   • 3042417938217135
DEV_TEST_URLS = [
    "https://www.aliexpress.com/p/order/detail.html?orderId=3044357010127135",  # 2 refund buttons
    "https://www.aliexpress.com/p/order/detail.html?orderId=3043329396767135",  # 2 refund buttons
    "https://www.aliexpress.com/p/order/detail.html?orderId=3043091352607135",  # 2 refund buttons
    "https://www.aliexpress.com/p/order/detail.html?orderId=3043091352627135",  # 2 refund buttons
    "https://www.aliexpress.com/p/order/detail.html?orderId=3043091352647135",  # 2 refund buttons
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042816799787135",  # 1 refund button
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938137135",  # 1 refund button
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938157135",  # 1 refund button
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938177135",  # 1 button, no refund link
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938197135",  # 1 refund button
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938217135"   # 1 refund button
]

IMAGE_PATH = "/home/schneider/Downloads/hermes_return_page-0001.jpg"  # Required for development mode
REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"
REFUND_MESSAGE_2 = "I do NOT AGREE. THE PACKAGE WAS RETURNED! I expect a full refund! Check the attached document!"

# Default refund messages for normal mode
DEFAULT_REFUND_MESSAGE = "The package was not picked up in time and was RETURNED to the sender. The attached document shows this"
DEFAULT_REFUND_MESSAGE_2 = "I do NOT AGREE. THE PACKAGE WAS RETURNED! I expect a full refund! Check the attached document!"

def save_dict_to_log(order_dict: dict):
    """Save the order dictionary to a log file with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"log_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(order_dict, f, indent=2)
    print(f"\n📝 Results saved to {filename}")

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
        'refund_message': DEFAULT_REFUND_MESSAGE,
        'refund_message_2': DEFAULT_REFUND_MESSAGE_2,
        'save_log': False
    }
    
    print("\n⚙️ Process Configuration:")
    choice = input("Pause for review after collecting refund links? (y/n): ").strip().lower()
    config['pause_for_review'] = choice == 'y'
    
    choice = input("Save results to log file? (y/n): ").strip().lower()
    config['save_log'] = choice == 'y'
    
    # Get image path
    while True:
        image_path = input("\nEnter the path to your proof image: ").strip()
        if os.path.exists(image_path):
            print(f"  • ✅ Image found: {image_path}")
            config['image_path'] = image_path
            break
        print("  • ❌ Image not found, please try again")
    
    # Get refund messages
    print("\nUse default refund messages?")
    print(f"Message 1 (Initial): {DEFAULT_REFUND_MESSAGE}")
    print(f"Message 2 (Disagreement): {DEFAULT_REFUND_MESSAGE_2}")
    choice = input("\nPress Enter to use default, or 'n' for custom messages: ").strip().lower()
    if choice == 'n':
        config['refund_message'] = input("\nEnter your custom initial message: ").strip()
        config['refund_message_2'] = input("Enter your custom disagreement message: ").strip()
        print("  • ✅ Using custom messages")
    else:
        print("  • ✅ Using default messages")
    
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

def process_batch(page, urls: list[str], config: dict) -> dict:
    """Process a batch of order URLs"""
    print("\n📋 Processing orders:")
    order_dict = create_order_dict(urls)
    
    # Print orders to process
    print("\n📋 Orders to process:")
    for order_id in order_dict:
        print(f"  • Order {order_id}")
    
    # Collect refund links
    order_dict = handle_refund_process(page, order_dict)
    
    # Process refunds
    print("\n🎯 Starting refund submissions...")
    order_dict = process_refunds(
        page=page,
        order_dict=order_dict,
        image_path=config['image_path'],
        refund_message=config['refund_message'],
        refund_message_2=config['refund_message_2']
    )
    
    # Print summary
    print_final_summary(order_dict)
    return order_dict  # Return the updated dictionary

def print_final_summary(order_dict: dict):
    """Print a comprehensive summary based on order dictionary states"""
    print("\n" + "="*50)
    print("📊 Processing Results")
    print("="*50)
    
    # First show per-order results
    print("\nPer-Order Results:")
    for order_id, data in order_dict.items():
        status = data.get('status', 'unknown')
        detail = data.get('status_detail', '')
        status_icon = {
            'refund_submitted': '✅',
            'evidence_submitted': '📝',
            'refund_ongoing': '⏳',
            'already_issued': '✨',
            'failed': '❌',
            'unknown': '❓'
        }.get(status, '❓')
        
        print(f"{status_icon} Order {order_id}: {status.replace('_', ' ').title()}")
        if detail:
            print(f"   └─ Details: {detail}")
    
    # Then show categorized summary
    print("\n" + "="*50)
    print("Categorized Summary")
    print("="*50)
    
    # Group orders by status
    status_groups = {
        'refund_submitted': [],
        'evidence_submitted': [],
        'refund_ongoing': [],
        'already_issued': [],
        'failed': []
    }
    
    for order_id, data in order_dict.items():
        status = data.get('status', 'failed')
        status_groups[status].append(order_id)
    
    if status_groups['refund_submitted']:
        print(f"\n✅ New Refund Requests Sent ({len(status_groups['refund_submitted'])} orders):")
        for order_id in status_groups['refund_submitted']:
            print(f"  • {order_id}")
    
    if status_groups['evidence_submitted']:
        print(f"\n📝 Additional Evidence Submitted ({len(status_groups['evidence_submitted'])} orders):")
        for order_id in status_groups['evidence_submitted']:
            print(f"  • {order_id}")
    
    if status_groups['refund_ongoing']:
        print(f"\n⏳ Refunds Under Review ({len(status_groups['refund_ongoing'])} orders):")
        for order_id in status_groups['refund_ongoing']:
            print(f"  • {order_id}")
    
    if status_groups['already_issued']:
        print(f"\n✨ Refunds Already Issued ({len(status_groups['already_issued'])} orders):")
        for order_id in status_groups['already_issued']:
            print(f"  • {order_id}")
    
    if status_groups['failed']:
        print(f"\n❌ Failed Processing ({len(status_groups['failed'])} orders):")
        for order_id in status_groups['failed']:
            detail = order_dict[order_id].get('status_detail', 'No details available')
            print(f"  • {order_id} - {detail}")
    
    # Print final statistics
    print("\n" + "="*50)
    print("Final Statistics")
    print("="*50)
    
    successful_states = ['refund_submitted', 'evidence_submitted', 'refund_ongoing', 'already_issued']
    total_success = sum(len(status_groups[state]) for state in successful_states)
    success_rate = (total_success / len(order_dict)) * 100 if order_dict else 0
    
    print(f"\n📦 Total Orders Processed: {len(order_dict)}")
    print(f"✅ Successfully Processed: {total_success}")
    print(f"❌ Failed: {len(status_groups['failed'])}")
    print(f"📈 Success Rate: {success_rate:.1f}%")

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
            'refund_message': REFUND_MESSAGE,
            'refund_message_2': REFUND_MESSAGE_2,
            'save_log': True
        }
        if not os.path.exists(config['image_path']):
            raise ValueError(f"Development mode requires valid IMAGE_PATH. Current path not found: {config['image_path']}")
    
    print("\n🌐 Launching browser...")
    
    order_dict = {}  # Initialize here
    
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
                order_dict = process_batch(page, DEV_TEST_URLS, config)
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
                            order_dict = process_batch(page, urls, config)
                            
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
            if development_mode or config.get('save_log', False):
                save_dict_to_log(order_dict)
            input("\nPress Enter to close the browser...")
            browser.close()

if __name__ == "__main__":
    main(development_mode=True)
    