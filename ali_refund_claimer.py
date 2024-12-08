from playwright.sync_api import sync_playwright
import json
from button_handler import add_checkboxes_to_orders
from order_processor import wait_for_orders_page_ready, handle_refund_process
import time

viewport_width = 1280
viewport_height = 1080

def load_credentials():
    try:
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
            return creds['email'], creds['password']
    except FileNotFoundError:
        print("credentials.json not found!")
        return None, None

def handle_login(page):
    email, password = load_credentials()
    if not email or not password:
        raise Exception("Failed to load credentials!")

    print("Entering credentials...")
    page.locator('input[type="text"]').fill(email)
    page.keyboard.press('Enter')
    page.locator('input[type="password"]').fill(password)
    page.keyboard.press('Enter')
    
    print("Waiting for successful login...")
    page.wait_for_url('**/de.aliexpress.com/**', timeout=120000)
    print("Login detected!")

def navigate_to_orders(page):
    print("Navigating to orders page...")
    page.goto('https://www.aliexpress.com/p/order/index.html')
    print("On orders page.")

def change_language_to_english(page):
    try:
        print("Changing display language to English...")
        # Open menu
        page.locator('.ship-to--simpleMenuItem--2ARVOMW').click()
        print("Clicked country selector")
        
        # Click language dropdown and select English
        page.locator('.select--text--1b85oDo').nth(1).click()
        print("Clicked language dropdown")
        page.locator('.select--item--32FADYB:has-text("English")').click()
        print("Selected English")
        
        # Click save
        save_button = page.locator('.es--saveBtn--w8EuBuy')
        save_button.wait_for(state='visible', timeout=5000)
        save_button.click()
        print("Saved language preference")
            
    except Exception as e:
        print(f"Warning: Could not change language: {e}")

def accept_cookies(page):
    try:
        print("Looking for cookie accept button...")
        accept_button = page.locator('.btn-accept')
        accept_button.wait_for(state='visible', timeout=5000)
        accept_button.click()
        print("Accepted cookies")
    except Exception as e:
        print(f"No cookie button found or already accepted: {e}")

def process_selected_orders(page):
    try:
        print("\n🔍 DEBUG: Starting process_selected_orders")
        
        # Get URLs with debug info
        print("🔍 DEBUG: Evaluating window.selectedOrderUrls")
        urls = page.evaluate('''() => {
            console.log('DEBUG: Current selectedOrderUrls:', window.selectedOrderUrls);
            return window.selectedOrderUrls;
        }''')
        
        print(f"🔍 DEBUG: Retrieved URLs: {urls}")
        
        if not urls or len(urls) == 0:
            print("❌ No orders selected!")
            return

        print(f"\n🎯 Found {len(urls)} orders to process")
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n📦 Order {i}/{len(urls)} {'='*20}")
            print(f"🔍 DEBUG: Processing URL: {url}")
            
            if handle_refund_process(page, url):
                successful += 1
            else:
                failed += 1
            
            print("\nWaiting 2 seconds before next order...")
            time.sleep(2)
        
        print(f"\n📊 Processing complete!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📋 Total: {len(urls)}")
            
    except Exception as e:
        print(f"❌ ERROR in process_selected_orders: {str(e)}")
        print(f"🔍 DEBUG: Full error details:")
        import traceback
        print(traceback.format_exc())

def test_simple_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized',
                '--window-size=1920,1080'
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': viewport_width, 'height': viewport_height},
            color_scheme='light',
            locale='en-US',
            timezone_id='Europe/Berlin'
        )
        
        page = context.new_page()
        
        page.evaluate('''() => {
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
        }''')
        
        try:
            print("Navigating to login page...")
            page.goto('https://login.aliexpress.com/')
            
            handle_login(page)
            navigate_to_orders(page)
            change_language_to_english(page)
            accept_cookies(page)
            
            # Wait for page to be ready after language change
            wait_for_orders_page_ready(page)
            
            # Now add the buttons
            add_checkboxes_to_orders(page)
            
            # Add event listener for the process button
            page.evaluate('''() => {
                window.startProcessing = false;  // Flag to control processing
                document.addEventListener('processOrdersClicked', () => {
                    console.log('DEBUG: Process button clicked!');
                    window.startProcessing = true;  // Set flag when button is clicked
                });
            }''')
            
            print("\nSetup complete!")
            print("Select orders and click 'Process Selected Orders' to begin")
            print("Press Ctrl+C when you want to quit.")
            
            while True:
                try:
                    # Only check for processing if button was clicked
                    should_process = page.evaluate('window.startProcessing || false')
                    if should_process:
                        urls = page.evaluate('window.selectedOrderUrls || []')
                        if urls and len(urls) > 0:
                            print("\nStarting to process selected orders...")
                            process_selected_orders(page)
                            # Reset flags after processing
                            page.evaluate('''() => {
                                window.startProcessing = false;
                                window.selectedOrderUrls = [];
                            }''')
                            print("\nWaiting for new orders to process...")
                    time.sleep(1)
                except Exception as e:
                    print(f"ERROR in main loop: {str(e)}")
                    print("Full error details:")
                    import traceback
                    print(traceback.format_exc())
                
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_simple_login()