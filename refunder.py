import logging
from playwright.sync_api import Page
import time

logger = logging.getLogger(__name__)

class Refunder:
    def __init__(self, page: Page, image_path: str, refund_message: str):
        self.page = page
        self.image_path = image_path
        self.refund_message = refund_message

    def check_refund_status(self) -> str:
        """Check if refund is already issued or in another state"""
        try:
            refund_complete = self.page.locator('.reminder--statusStr--3FMxRSU:has-text("Refund complete")').first
            if refund_complete.is_visible():
                logger.debug("Found 'Refund complete' status")
                return "refund_already_issued"
            
            dropdown = self.page.locator('.comet-v2-select-show-arrow').first
            if dropdown.is_visible():
                logger.debug("Found refund form dropdown")
                return "can_submit"
            
            logger.debug("Could not determine refund status")
            return "unclear"
            
        except Exception as e:
            logger.error(f"Error checking refund status: {e}")
            return "unclear"

    def fill_refund_form(self) -> bool:
        """Fill out the refund form with reason, message and image"""
        try:
            print("  • Filling refund form...")
            
            logger.debug("Selecting refund reason")
            dropdown = self.page.locator('.comet-v2-select-show-arrow').first
            dropdown.click()
            time.sleep(1)
            
            logger.debug("Selecting reason: Tracked as returned/canceled/lost")
            reason = self.page.locator('.comet-v2-menu-item:has-text("Tracked as returned/canceled/lost")').first
            reason.click()
            time.sleep(1)
            
            logger.debug("Entering message")
            textarea = self.page.locator('.commet--textarea--Sg0xapL').first
            textarea.fill(self.refund_message)
            time.sleep(1)
            
            logger.debug("Uploading image")
            file_input = self.page.locator('input[type="file"]').first
            file_input.set_input_files(self.image_path)
            time.sleep(2)
            
            print("  • ✅ Form submitted")
            return True
            
        except Exception as e:
            print(f"❌ Error filling refund form: {e}")
            return False

    def process_refund_page(self, refund_url: str) -> bool:
        """Process a single refund page"""
        try:
            print(f"\nProcessing refund page: {refund_url}")
            self.page.goto(refund_url)
            self.page.wait_for_load_state('networkidle')
            
            # First check the status
            status = self.check_refund_status()
            print(f"Detected refund status: {status}")
            
            if status == "refund_already_issued":
                print("✅ Refund was already issued!")
                return True
                
            if status != "can_submit":
                print("❌ Cannot submit refund - status unclear")
                return False
            
            # If we can submit, proceed with refund submission
            print("Proceeding with refund submission...")
            return self.fill_refund_form()
            
        except Exception as e:
            print(f"❌ Error processing refund: {e}")
            return False

def process_refunds(page: Page, order_dict: dict, image_path: str, refund_message: str) -> dict:
    """Process refunds and update dictionary with results"""
    refunder = Refunder(page, image_path, refund_message)
    successful = 0
    failed = 0
    
    print("\n📋 Processing refunds:")
    
    for order_id, data in order_dict.items():
        refund_url = data['refund_url']
        if not refund_url:
            continue
            
        print(f"\n🔄 Order {order_id}:")
        logger.debug(f"Processing URL: {refund_url}")
        
        try:
            page.goto(refund_url)
            page.wait_for_load_state('networkidle')
            
            status = refunder.check_refund_status()
            
            if status == "refund_already_issued":
                print("  • ✅ Refund already issued")
                order_dict[order_id]['refund_state'] = 'refund_already_issued'
                successful += 1
            elif status == "can_submit" and refunder.fill_refund_form():
                order_dict[order_id]['refund_state'] = 'submitted'
                successful += 1
            else:
                print("  • ❓ Status unclear")
                order_dict[order_id]['refund_state'] = 'unclear'
                failed += 1
            
        except Exception as e:
            logger.error(f"Error processing order {order_id}: {e}")
            print("  • ❌ Processing failed")
            order_dict[order_id]['refund_state'] = 'failed'
            failed += 1
        
        time.sleep(2)
    
    print("\n📊 Summary:")
    print(f"  • ✅ Successful: {successful}")
    print(f"  • ❌ Failed: {failed}")
    print(f"  • 📦 Total: {len(order_dict)}")
    
    return order_dict