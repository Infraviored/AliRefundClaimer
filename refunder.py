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
            
            # Wait for image upload to complete
            try:
                print("  • Waiting for image upload...")
                # Wait for the specific success structure: container with thumbnail that has background-image
                self.page.wait_for_selector('.upload--imageContainer--3tTIByI .upload--imageThumb--1diFoUj[style*="background-image"]', timeout=30000)
                print("  • ✅ Image uploaded successfully")
                
            except Exception as e:
                input(f"❌ Error during image upload: {e}. Press Enter to continue...")
                return False
            
            # Click Next Step button
            next_button = self.page.locator('button:has-text("Next step")')
            if not next_button.is_visible():
                input("❌ Next step button not found. Press Enter to continue...")
                return False
            
            next_button.click()
            
            # Wait for new page to load and find Submit button
            try:
                print("  • Waiting for submit page to load...")
                # Wait for and click the specific Submit button (not Back button)
                submit_button = self.page.locator('button[data-pl="buyersubmit_btn_submit"]:has-text("Submit")').first
                submit_button.wait_for(state='visible', timeout=10000)
                submit_button.click()
                
                # Wait for and handle confirmation popup
                print("  • Waiting for confirmation popup...")
                confirm_button = self.page.locator('.comet-v2-modal-footer button:has-text("Confirm")').first
                confirm_button.wait_for(state='visible', timeout=10000)
                confirm_button.click()
                time.sleep(1)
                
                print("  • ✅ Refund form submitted successfully")
                return True
                
            except Exception as e:
                input(f"❌ Submit button error: {e}. Press Enter to continue...")
                return False
            
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
    successful = 0
    failed = 0
    
    print("\n📋 Processing refunds:")
    
    # Clean up any existing refund tabs first
    print("  • Cleaning up old refund tabs...")
    for p in page.context.pages:
        if 'reverse-pages' in p.url:
            p.close()
    
    for order_id, data in order_dict.items():
        refund_urls = data.get('refund_urls', [])
        if not refund_urls:
            continue
            
        print(f"\n🔄 Order {order_id}:")
        
        for i, refund_url in enumerate(refund_urls, 1):
            logger.debug(f"Processing URL: {refund_url}")
            print(f"  • Processing item {i} of {len(refund_urls)}")
            
            try:
                # Open fresh tab with Playwright
                refund_page = page.context.new_page()
                refund_page.goto(refund_url)
                refund_page.bring_to_front()  # Ensure this tab is visible
                refund_page.wait_for_load_state('networkidle')
                
                # Create new Refunder instance with the new page
                refunder = Refunder(refund_page, image_path, refund_message)
                status = refunder.check_refund_status()
                
                if status == "refund_already_issued":
                    print("    ✅ Refund already issued")
                    successful += 1
                elif status == "can_submit" and refunder.fill_refund_form():
                    print("    ✅ Refund submitted")
                    successful += 1
                else:
                    print("    ❓ Status unclear")
                    failed += 1
                
                # Close the tab after processing
                refund_page.close()
                
            except Exception as e:
                logger.error(f"Error processing order {order_id}: {e}")
                print("    ❌ Processing failed")
                failed += 1
            
            time.sleep(2)
    
    print("\n📊 Summary:")
    print(f"  • ✅ Successful: {successful}")
    print(f"  • ❌ Failed: {failed}")
    print(f"  • 📦 Total: {len(order_dict)}")
    
    return order_dict