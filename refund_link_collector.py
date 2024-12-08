from playwright.sync_api import Page
import time
from typing import List
import logging

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
        
        logger.debug(f"Starting from order list: {page.url}")
        
        order_items = list(order_dict.items())
        for i, (order_id, data) in enumerate(order_items):
            logger.debug(f"Processing order URL: {data['order_url']}")
            
            current_refund_pages = get_refund_pages(page.context)
            try:
                page.goto(data['order_url'])
                page.wait_for_load_state('networkidle')
                
                logger.debug("Looking for Returns/refunds button...")
                refund_button = page.locator('button.comet-btn:has-text("Returns/refunds")').first
                if not refund_button.is_visible():
                    print(f"  • Order {order_id}: ❌ No refund button available")
                    continue
                
                refund_button.click()
                logger.debug("Clicked Returns/refunds button")
                time.sleep(3)
                
                # Try No button if needed
                no_button = page.locator('.comet-modal button.comet-btn:not(.comet-btn-primary):has-text("No")').first
                if no_button.is_visible():
                    logger.debug("Found No button, clicking it...")
                    no_button.click()
                    time.sleep(3)
                
                # If this isn't the last order, go to next order to force context update
                if i < len(order_items) - 1:
                    next_order_id, next_data = order_items[i + 1]
                    next_url = next_data['order_url']
                    logger.debug("Navigating to next order to check for new tabs...")
                    page.goto(next_url)
                else:
                    logger.debug(f"Last order, returning to list: {page.url}")
                    page.goto(page.url)
                
                page.wait_for_load_state('networkidle')
                
                # Check for new refund pages
                new_refund_pages = get_refund_pages(page.context)
                logger.debug("\nCurrent refund pages:")
                for p in new_refund_pages:
                    logger.debug(f"- {p}")
                
                # The newest refund page belongs to the current order
                new_pages = [p for p in new_refund_pages if p not in current_refund_pages]
                if new_pages:
                    order_dict[order_id]['refund_url'] = new_pages[-1]
                    print(f"  • Order {order_id}: ✅ Found refund link")
                    logger.debug(f"Refund URL: {new_pages[-1]}")
                else:
                    print(f"  • Order {order_id}: ❌ No refund link found")
                
            except Exception as e:
                logger.error(f"Error processing order {order_id}: {e}")
                continue
        
        print("\n📊 Summary of refund links:")
        for order_id, data in order_dict.items():
            status = "✅ Found" if data['refund_url'] else "❌ Not found"
            print(f"  • Order {order_id}: {status}")
        
        return order_dict
            
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        return order_dict