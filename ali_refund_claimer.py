from playwright.sync_api import sync_playwright
from login_handler import LoginHandler
from button_handler import add_checkboxes_to_orders
from order_processor import handle_refund_process
import time

# Test URLs for development
DEV_TEST_URLS = [
    "https://www.aliexpress.com/p/order/detail.html?orderId=3042417938137135",
    "https://www.aliexpress.com/p/order/detail.html?orderId=3044357010087135",
    # Add more URLs as needed
]

def dev_mode(page):
    """Development mode: directly process test URLs"""
    print("\n🔍 Starting development test mode...")
    print(f"Processing {len(DEV_TEST_URLS)} test orders...")
    
    successful = 0
    failed = 0
    
    for i, url in enumerate(DEV_TEST_URLS, 1):
        print(f"\nOrder {i}/{len(DEV_TEST_URLS)} {'='*20}")
        if handle_refund_process(page, url):
            successful += 1
        else:
            failed += 1
        time.sleep(2)
    
    print(f"\nProcessing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(DEV_TEST_URLS)}")

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
                                successful = 0
                                failed = 0
                                
                                for i, url in enumerate(urls, 1):
                                    print(f"\nOrder {i}/{len(urls)} {'='*20}")
                                    if handle_refund_process(page, url):
                                        successful += 1
                                    else:
                                        failed += 1
                                    time.sleep(2)
                                
                                print(f"\nProcessing complete!")
                                print(f"Successful: {successful}")
                                print(f"Failed: {failed}")
                                print(f"Total: {len(urls)}")
                                
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
            browser.close()

if __name__ == "__main__":
    main(development_mode=True)  # Set to True for testing, False for normal operation