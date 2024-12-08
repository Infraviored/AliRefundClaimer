from playwright.sync_api import sync_playwright
import time
from order_processor import handle_refund_process  # Import the actual processor

def test_process_orders():
    """Test script for processing orders with existing browser session"""
    with sync_playwright() as p:
        try:
            # Connect to existing browser
            browser = p.chromium.connect_over_cdp('http://localhost:9222')
            context = browser.contexts[0]  # Get the first context
            page = context.pages[0]  # Get the first page
            
            # Test URLs
            test_urls = [
                "https://www.aliexpress.com/p/order/detail.html?orderId=3042816799787135",
                # Add more test URLs as needed
            ]
            
            print("\n🔍 Starting test processing...")
            for url in test_urls:
                print(f"\n📋 Testing URL: {url}")
                
                # Use the actual processing function
                result = handle_refund_process(page, url)
                print(f"Result: {'✅ Success' if result else '❌ Failed'}")
                
                print("\n⏸️  Press Enter to continue to next URL (Ctrl+C to exit)...")
                input()
                
        except KeyboardInterrupt:
            print("\n👋 Test ended by user")
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            print(traceback.format_exc())
        finally:
            # Just disconnect, don't close the browser
            browser.disconnect()
            print("\n🔌 Disconnected from browser")

if __name__ == "__main__":
    test_process_orders() 