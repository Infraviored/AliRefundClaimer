from playwright.sync_api import sync_playwright
import json
import os
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

def change_all_to_english(page):
    try:
        print("Changing language to English...")
        page.locator('.ship-to--simpleMenuItem--2ARVOMW').click()
        print("Clicked country selector")
        
        try:
            page.locator('.select--text--1b85oDo').first.click()
            print("Clicked language dropdown")
        except:
            print("Could not click language dropdown, trying to continue...")
            
        try:
            page.locator('.select--item--32FADYB').first.click()
            print("Selected English")
        except:
            print("Could not select English, trying to continue...")
            
    except Exception as e:
        print(f"Warning: Could not change language: {e}")

def change_language_to_english(page):
    try:
        print("Changing display language to English...")
        # Open menu (from change_all_to_english)
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

def wait_for_orders_page_ready(page):
    time.sleep(1)
    try:
        print("Waiting for orders page to be fully loaded...")
        # Wait for some key elements that indicate the page is ready
        page.wait_for_selector('.order-item', timeout=10000)
        page.wait_for_selector('.order-item-btns', timeout=10000)
        print("Orders page is ready")
    except Exception as e:
        print(f"Error waiting for page: {e}")

def handle_refund_in_tab(page):
    try:
        print("Looking for Returns/refunds button...")
        refund_button = page.locator('span:has-text("Returns/refunds")')
        refund_button.wait_for(state='visible', timeout=5000)
        refund_button.click()
        print("Clicked Returns/refunds button")
        
        print("Looking for 'No' button...")
        no_button = page.locator('button.comet-btn:has-text("No")')
        no_button.wait_for(state='visible', timeout=5000)
        no_button.click()
        print("Clicked 'No' button")
        
    except Exception as e:
        print(f"Error in refund process: {e}")

def add_checkboxes_to_orders(page):
    try:
        print("Adding selection buttons to order items...")
        page.evaluate('''() => {
            // Add process button at the bottom
            const processButton = document.createElement('button');
            processButton.innerHTML = 'Process Selected Orders';
            processButton.id = 'process-orders-button';
            processButton.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                padding: 15px 30px;
                font-size: 18px;
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                z-index: 1000;
            `;
            document.body.appendChild(processButton);

            // Add selection buttons to each order
            const orders = document.querySelectorAll('.order-item');
            orders.forEach((order, index) => {
                const button = document.createElement('button');
                button.innerHTML = 'Select for Processing';
                button.className = 'comet-btn comet-btn-block order-item-btn selection-button';
                button.setAttribute('data-order-id', order.querySelector('a[href*="order/detail"]').href);
                button.onclick = function() {
                    if (this.style.backgroundColor === 'rgb(0, 153, 102)') {
                        this.style.backgroundColor = '';
                        this.style.color = '';
                        console.log('Order deselected');
                    } else {
                        this.style.backgroundColor = '#009966';
                        this.style.color = 'white';
                        console.log('Order selected');
                    }
                };
                order.querySelector('.order-item-btns').appendChild(button);
            });

            // Add click handler for process button
            document.getElementById('process-orders-button').onclick = async function() {
                const selectedButtons = document.querySelectorAll('.selection-button[style*="background-color: rgb(0, 153, 102)"]');
                console.log(`Processing ${selectedButtons.length} selected orders...`);
                selectedButtons.forEach((button, index) => {
                    const orderDetailUrl = button.getAttribute('data-order-id');
                    console.log(`Opening order detail ${index + 1}/${selectedButtons.length}`);
                    window.open(orderDetailUrl, '_blank');
                });
            };
        }''')
        print("Added selection buttons and process button")
        
        # Add event listener for console logs from the page
        page.on("console", lambda msg: print(f"Page log: {msg.text}"))
        
    except Exception as e:
        print(f"Error adding buttons: {e}")

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
            # viewport={'width': 1920, 'height': 1080},
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
            
            # Handle new pages that are opened
            page.context.on("page", lambda new_page: handle_refund_in_tab(new_page))
            
            print("\nPress Ctrl+C when you want to quit.")
            while True:
                pass
                
        except KeyboardInterrupt:
            print("\nClosing browser...")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_simple_login()