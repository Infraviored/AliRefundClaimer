from playwright.sync_api import Page
import json
import time

class LoginHandler:
    def __init__(self, page: Page):
        self.page = page

    def load_credentials(self):
        try:
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
                return creds['email'], creds['password']
        except FileNotFoundError:
            print("ERROR: credentials.json not found!")
            return None, None

    def login(self):
        print("Starting login process...")
        email, password = self.load_credentials()
        if not email or not password:
            raise Exception("Failed to load credentials!")

        self.page.goto('https://login.aliexpress.com/')
        print("Entering credentials...")
        self.page.locator('input[type="text"]').fill(email)
        self.page.keyboard.press('Enter')
        self.page.locator('input[type="password"]').fill(password)
        self.page.keyboard.press('Enter')
        
        print("Waiting for login completion...")
        self.page.wait_for_url('**/de.aliexpress.com/**', timeout=120000)
        print("Login successful")

    def navigate_to_orders(self):
        print("Navigating to orders page...")
        self.page.goto('https://www.aliexpress.com/p/order/index.html')
        time.sleep(3)  # Wait for initial load
        
        # Change language to English
        try:
            self.page.locator('.ship-to--simpleMenuItem--2ARVOMW').click()
            self.page.locator('.select--text--1b85oDo').nth(1).click()
            self.page.locator('.select--item--32FADYB:has-text("English")').click()
            self.page.locator('.es--saveBtn--w8EuBuy').click()
            print("Language set to English")
            
            # Wait for page reload after language change
            print("Waiting for page to stabilize after language change...")
            time.sleep(3)  # Increased wait time to ensure page is stable
            
        except Exception as e:
            print(f"Warning: Could not change language: {e}")

        # Accept cookies if needed
        try:
            accept_button = self.page.locator('.btn-accept')
            accept_button.wait_for(state='visible', timeout=5000)
            accept_button.click()
        except Exception:
            pass  # Cookie prompt might not appear

        # Wait for order page elements
        self.page.wait_for_selector('.order-item', timeout=10000)
        self.page.wait_for_selector('.order-item-btns', timeout=10000)
        print("Orders page ready") 