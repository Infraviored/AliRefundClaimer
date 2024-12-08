from playwright.sync_api import Page, TimeoutError
import time

def print_pages(context, prefix="Current pages"):
    """Helper to print all current pages"""
    print(f"\nDEBUG: {prefix}:")
    for p in context.pages:
        print(f"- {p.url}")

def force_context_update(page: Page):
    """Force Playwright to update its context by doing a tiny navigation"""
    current_url = page.url
    page.goto(current_url)
    page.wait_for_load_state('networkidle')

def handle_refund_process(page: Page, url: str):
    """Process a single refund URL"""
    try:
        print(f"\nProcessing order: {url}")
        page.goto(url)
        page.wait_for_load_state('networkidle')
        
        context = page.context
        
        print("\nLooking for Returns/refunds buttons...")
        refund_button = page.locator('button.comet-btn:has-text("Returns/refunds")').first
        if not refund_button.is_visible():
            raise Exception("Could not find Returns/refunds button")
        
        # Get initial state
        initial_urls = [p.url for p in context.pages]
        print_pages(context, "Before clicking Returns/refunds")
        
        # Click Returns/refunds
        refund_button.click()
        print("Clicked Returns/refunds button")
        time.sleep(3)
        
        # Force context update and check for new pages
        force_context_update(page)
        current_urls = [p.url for p in context.pages]
        print_pages(context, "After Returns/refunds")
        
        if len(current_urls) > len(initial_urls):
            print("\n🎯 SUCCESS! New page opened!")
            return True
        
        # Try No button
        print("\nLooking for 'No' button in popup...")
        no_button = page.locator('.comet-modal button.comet-btn:not(.comet-btn-primary):has-text("No")').first
        if not no_button.is_visible():
            raise Exception("Could not find No button")
        
        # Store current state
        initial_urls = [p.url for p in context.pages]
        print_pages(context, "Before clicking No")
        
        no_button.click()
        print("Clicked 'No' button")
        time.sleep(3)
        
        # Force context update and check for new pages again
        force_context_update(page)
        current_urls = [p.url for p in context.pages]
        print_pages(context, "After clicking No")
        
        if len(current_urls) > len(initial_urls):
            print("\n🎯 SUCCESS! New page opened!")
            return True
            
        print("\nDEBUG: Final state:")
        print_pages(context)
        raise Exception("No new pages detected")
        
    except Exception as e:
        print(f"\n❌ Failed to process refund: {e}")
        print_pages(context, "Final state")
        return None