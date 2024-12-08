from playwright.sync_api import Page
import time

def wait_for_orders_page_ready(page: Page):
    """Wait for the orders page to be fully loaded"""
    print("Waiting for orders page to be fully loaded...")
    try:
        # Wait a moment for initial load
        time.sleep(3)
        
        # Wait for key elements
        page.wait_for_selector('.order-item', timeout=10000)
        page.wait_for_selector('.order-item-btns', timeout=10000)
        print("✓ Orders page is ready")
        
    except Exception as e:
        print(f"❌ Error waiting for orders page: {e}")

def handle_refund_process(page: Page, url: str):
    """Process a single refund URL with detailed logging"""
    try:
        print(f"\n🔄 Processing URL: {url}")
        
        # Navigate to the order detail page
        print("Navigating to order detail page...")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        print(f"✓ Page loaded: {page.url}")
        
        # Look for refund button
        print("\nLooking for Returns/refunds button...")
        refund_button = page.locator('span[data-spm-anchor-id*="Returns/refunds"]')
        
        try:
            refund_button.wait_for(state='visible', timeout=10000)
            print("✓ Found Returns/refunds button")
            refund_button.click()
            print("✓ Clicked Returns/refunds button")
        except Exception as e:
            print(f"❌ Error finding/clicking refund button: {e}")
            print(f"Current page content: {page.content()}")
            return False
        
        # Look for No button
        print("\nLooking for 'No' button...")
        no_button = page.locator('button.comet-btn span[data-spm-anchor-id*="No"]')
        
        try:
            no_button.wait_for(state='visible', timeout=10000)
            print("✓ Found 'No' button")
            no_button.click()
            print("✓ Clicked 'No' button")
        except Exception as e:
            print(f"❌ Error finding/clicking No button: {e}")
            print(f"Current page content: {page.content()}")
            return False
            
        print("\n✅ Successfully processed refund for this order")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error processing refund: {e}")
        return False