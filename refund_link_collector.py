from playwright.sync_api import Page
import time
from typing import List
import logging

# Configurable wait times (in seconds)
WAIT_AFTER_BUTTON_CLICK = 0.2  # Wait after clicking refund button
WAIT_AFTER_NO_BUTTON = 0.2     # Wait after clicking "No" button
WAIT_AFTER_NAVIGATION = 3     # Wait after navigating to next order

logger = logging.getLogger(__name__)

def print_pages(context, prefix="Current pages"):
    """Helper to print all current pages"""
    logger.debug(f"\n{prefix}:")
    for p in context.pages:
        logger.debug(f"- {p.url}")

def get_refund_pages(context) -> List[str]:
    """Get all reverse-pages URLs currently open"""
    return [p.url for p in context.pages if 'reverse-pages' in p.url]

def handle_refund_process(page: Page, order_dict: dict) -> dict:
    """Process orders and add refund URLs to dictionary"""
    try:
        print("\n📋 Orders to process:")
        for order_id in order_dict.keys():
            print(f"  • Order {order_id}")
        
        # Close any existing refund pages before starting
        for p in page.context.pages:
            if 'reverse-pages' in p.url:
                p.close()
        
        order_items = list(order_dict.items())
        for i, (order_id, data) in enumerate(order_items):
            logger.debug(f"\nProcessing order URL: {data['order_url']}")
            
            try:
                # Navigate to order
                page.goto(data['order_url'])
                page.bring_to_front()
                page.wait_for_load_state('networkidle')
                
                # Find all refund buttons for this order
                refund_buttons = page.locator('button.comet-btn:has-text("Returns/refunds")').all()
                if not refund_buttons:
                    print(f"  • Order {order_id}: ❌ No refund buttons available")
                    continue
                
                print(f"\nProcessing refund buttons for Order {order_id}...")
                print(f"  • Found {len(refund_buttons)} buttons")
                
                # Click all refund buttons for this order
                for button_index, refund_button in enumerate(refund_buttons):
                    print(f"  • Clicking button {button_index + 1} of {len(refund_buttons)}")
                    refund_button.click()
                    
                    # Wait for potential "No" button
                    time.sleep(WAIT_AFTER_BUTTON_CLICK)
                    
                    # Handle "No" button if it appears
                    no_button = page.locator('.comet-modal button.comet-btn:not(.comet-btn-primary):has-text("No")').first
                    if no_button.is_visible():
                        logger.debug("Found No button, clicking it...")
                        no_button.click()
                        time.sleep(WAIT_AFTER_NO_BUTTON)
                
                # Immediately navigate to next order or back to list
                print("  • Waiting for refund pages to load...")
                if i < len(order_items) - 1:
                    next_url = order_items[i + 1][1]['order_url']
                    print("  • Navigating to next order...")
                else:
                    next_url = "https://www.aliexpress.com/p/order/index.html"
                    print("  • Navigating back to order list...")
                
                page.goto(next_url)
                
                # Now wait for tabs to open
                time.sleep(3)  # Increased wait time to ensure all tabs open
                
                # Collect all refund pages that were opened for this order
                refund_pages = get_refund_pages(page.context)
                order_dict[order_id]['refund_urls'] = refund_pages
                
                if refund_pages:
                    print(f"  • Order {order_id}: ✅ Found {len(refund_pages)} refund links")
                else:
                    print(f"  • Order {order_id}: ❌ No refund links found")
                    input("\n⚠️ No refund links found for this order! Press Enter to continue or Ctrl+C to quit...")
                
                # Close all refund pages before moving to next order
                for p in page.context.pages:
                    if 'reverse-pages' in p.url:
                        p.close()
                
            except Exception as e:
                logger.error(f"Error processing order {order_id}: {e}")
                continue
        
        print("\n📊 Summary of refund links:")
        for order_id, data in order_dict.items():
            refund_count = len(data.get('refund_urls', []))
            print(f"  • Order {order_id}: {refund_count} refund links found")
        
        return order_dict
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return order_dict