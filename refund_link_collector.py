from playwright.sync_api import Page, TimeoutError
import time
from typing import Dict, List, Optional

def print_pages(context, prefix="Current pages"):
    """Helper to print all current pages"""
    print(f"\nDEBUG: {prefix}:")
    for p in context.pages:
        print(f"- {p.url}")

def get_refund_pages(context) -> List[str]:
    """Get all reverse-pages URLs currently open"""
    return [p.url for p in context.pages if 'reverse-pages' in p.url]

def handle_refund_process(page: Page, order_dict: dict) -> dict:
    """Process orders and add refund URLs to dictionary"""
    try:
        initial_url = page.url
        print(f"\nStarting from order list: {initial_url}")
        
        # Convert dict items to list for easier indexing
        order_items = list(order_dict.items())
        
        # Process each order
        for i, (order_id, data) in enumerate(order_items):
            print(f"\nOrder {i+1}/{len(order_dict)} {'='*20}")
            url = data['order_url']
            print(f"Processing order: {url}")
            
            current_refund_pages = get_refund_pages(page.context)
            
            try:
                page.goto(url)
                page.wait_for_load_state('networkidle')
                
                print("Looking for Returns/refunds button...")
                refund_button = page.locator('button.comet-btn:has-text("Returns/refunds")').first
                if not refund_button.is_visible():
                    print("❌ No Returns/refunds button found, skipping...")
                    continue
                
                refund_button.click()
                print("Clicked Returns/refunds button")
                time.sleep(3)
                
                # Try No button if needed
                no_button = page.locator('.comet-modal button.comet-btn:not(.comet-btn-primary):has-text("No")').first
                if no_button.is_visible():
                    print("Found No button, clicking it...")
                    no_button.click()
                    time.sleep(3)
                
                # If this isn't the last order, go to next order to force context update
                if i < len(order_items) - 1:
                    next_order_id, next_data = order_items[i + 1]
                    next_url = next_data['order_url']
                    print(f"\nNavigating to next order to check for new tabs...")
                    page.goto(next_url)
                else:
                    # For last order, return to list
                    print(f"\nLast order, returning to list: {initial_url}")
                    page.goto(initial_url)
                
                page.wait_for_load_state('networkidle')
                
                # Check for new refund pages
                new_refund_pages = get_refund_pages(page.context)
                print("\nCurrent refund pages:")
                for p in new_refund_pages:
                    print(f"- {p}")
                
                # The newest refund page belongs to the current order
                new_pages = [p for p in new_refund_pages if p not in current_refund_pages]
                if new_pages:
                    order_dict[order_id]['refund_url'] = new_pages[-1]
                    print(f"✅ Found refund page for order {order_id}")
                
            except Exception as e:
                print(f"\n❌ Error processing order: {e}")
                continue
        
        return order_dict
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        return order_dict