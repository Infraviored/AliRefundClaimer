from playwright.sync_api import Page, TimeoutError
import time
from typing import Dict, List, Optional

def print_pages(context, prefix="Current pages"):
    """Helper to print all current pages"""
    print(f"\nDEBUG: {prefix}:")
    for p in context.pages:
        print(f"- {p.url}")

def extract_order_id(url: str) -> Optional[str]:
    """Extract order ID from either order detail or refund page URL"""
    if 'orderId=' in url:
        return url.split('orderId=')[1].split('&')[0]
    if 'tradeOrderLineId=' in url:
        return url.split('tradeOrderLineId=')[1].split('&')[0]
    if 'reverseOrderLineId=' in url:
        return url.split('reverseOrderLineId=')[1].split('&')[0]
    return None

def handle_refund_process(page: Page, urls: list[str]):
    """Process a list of order URLs and map them to their refund pages"""
    try:
        # Store initial order list URL
        initial_url = page.url
        print(f"\nStarting from order list: {initial_url}")
        
        # Track order IDs we're processing
        order_ids = [extract_order_id(url) for url in urls]
        print(f"Processing orders: {order_ids}")
        
        # Process each order to open refund pages
        for i, url in enumerate(urls, 1):
            print(f"\nOrder {i}/{len(urls)} {'='*20}")
            print(f"Processing order: {url}")
            
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
                
            except Exception as e:
                print(f"\n❌ Error processing order: {e}")
                continue
        
        # Return to order list to force context update
        print(f"\nReturning to order list: {initial_url}")
        page.goto(initial_url)
        page.wait_for_load_state('networkidle')
        
        # Now map order IDs to their refund pages
        context = page.context
        print("\n🎯 Final state of all opened pages:")
        print_pages(context)
        
        print("\n🎯 Mapping orders to refund pages:")
        refund_pages = [p for p in context.pages if 'reverse-pages' in p.url]
        order_to_refund: Dict[str, str] = {}
        
        # Debug each refund page URL parsing
        for refund_page in refund_pages:
            refund_url = refund_page.url
            print(f"\nAnalyzing refund URL: {refund_url}")
            order_id = extract_order_id(refund_url)
            print(f"Extracted order ID: {order_id}")
            print(f"Looking for match in: {order_ids}")
            
            # Try partial matching if exact match fails
            if order_id not in order_ids:
                for original_id in order_ids:
                    if original_id in order_id or order_id in original_id:
                        print(f"Found partial match: {original_id} ↔ {order_id}")
                        order_to_refund[original_id] = refund_url
                        print(f"✅ Order {original_id} → {refund_url}")
            else:
                order_to_refund[order_id] = refund_url
                print(f"✅ Order {order_id} → {refund_url}")
        
        print("\nProcessing Results:")
        print(f"Total Orders: {len(urls)}")
        print(f"Found Refund Pages: {len(order_to_refund)}")
        print(f"Missing Refund Pages: {len(urls) - len(order_to_refund)}")
        
        # TODO: Process refund pages (dummy for now)
        print("\nReady to process refund pages...")
        for order_id, refund_url in order_to_refund.items():
            print(f"\nWould process refund for order {order_id}:")
            print(f"- URL: {refund_url}")
            print("- Would check for Yes button")
            print("- Would perform refund actions")
        
        return order_to_refund
            
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        if 'context' in locals():
            print_pages(context, "Final state")
        return {}