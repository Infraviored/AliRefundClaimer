from playwright.sync_api import Page
import json
import time
import logging

logger = logging.getLogger(__name__)

class LoginHandler:
    def __init__(self, page: Page):
        self.page = page

    def load_credentials(self):
        """Load login credentials from json file"""
        try:
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
                return creds['email'], creds['password']
        except FileNotFoundError:
            logger.error("credentials.json not found!")
            return None, None

    def login(self):
        """Handle the login process"""
        print("\n🔐 Logging in to AliExpress...")
        email, password = self.load_credentials()
        if not email or not password:
            raise Exception("Failed to load credentials!")

        logger.debug("Navigating to login page")
        self.page.goto('https://login.aliexpress.com/')
        
        logger.debug("Entering credentials")
        self.page.locator('input[type="text"]').fill(email)
        self.page.keyboard.press('Enter')
        self.page.locator('input[type="password"]').fill(password)
        self.page.keyboard.press('Enter')
        
        print("  • Waiting for login completion...")
        self.page.wait_for_url('**/de.aliexpress.com/**', timeout=120000)
        print("  • ✅ Login successful")

    def navigate_to_orders(self):
        """Navigate to orders page and set up environment"""
        print("\n📑 Preparing orders page...")
        
        logger.debug("Navigating to orders page")
        self.page.goto('https://www.aliexpress.com/p/order/index.html')
        time.sleep(3)
        
        # Change language to English
        try:
            logger.debug("Attempting to change language to English")
            self.page.locator('.ship-to--simpleMenuItem--2ARVOMW').click()
            self.page.locator('.select--text--1b85oDo').nth(1).click()
            self.page.locator('.select--item--32FADYB:has-text("English")').click()
            self.page.locator('.es--saveBtn--w8EuBuy').click()
            print("  • Language set to English")
            
            logger.debug("Waiting for page to stabilize after language change")
            time.sleep(3)
            
        except Exception as e:
            logger.warning(f"Could not change language: {e}")

        # Accept cookies if needed
        try:
            logger.debug("Checking for cookie prompt")
            accept_button = self.page.locator('.btn-accept')
            accept_button.wait_for(state='visible', timeout=5000)
            accept_button.click()
            logger.debug("Accepted cookies")
        except Exception:
            logger.debug("No cookie prompt found")

        # Wait for order page elements
        logger.debug("Waiting for order page elements")
        self.page.wait_for_selector('.order-item', timeout=10000)
        self.page.wait_for_selector('.order-item-btns', timeout=10000)
        print("  • ✅ Orders page ready") 