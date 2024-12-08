import logging
from playwright.sync_api import Page
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class Refunder:
    def __init__(self, page: Page, image_path: str, refund_message: str, refund_message_2: str):
        self.page = page
        self.image_path = image_path
        self.refund_message = refund_message
        self.refund_message_2 = refund_message_2
        
    def check_refund_status(self) -> str:
        """Check if refund is already issued or in another state"""
        try:
            # Check for completed refund
            refund_complete = self.page.locator('.reminder--statusStr--3FMxRSU:has-text("Refund complete")').first
            if refund_complete.is_visible():
                logger.debug("Found 'Refund complete' status")
                return "refund_already_issued"
            
            # Check for waiting response state
            waiting_response = self.page.locator('.reminder--statusStr--3FMxRSU:has-text("Waiting for your response")').first
            if waiting_response.is_visible():
                logger.debug("Found 'Waiting for response' status")
                return "needs_response"
            
            # Check for ongoing review state - updated locators
            ongoing_review_title = self.page.locator('.verticalSteps--title--1m4xoBw:has-text("We\'re reviewing your request")').first
            ongoing_review_status = self.page.locator('.reminder--statusStr--3FMxRSU:has-text("Waiting for AliExpress\'s feedback")').first
            
            if ongoing_review_title.is_visible() or ongoing_review_status.is_visible():
                logger.debug("Found 'Waiting for feedback' status")
                # Debug info
                print("    Debug: Found review status")
                print(f"    Title visible: {ongoing_review_title.is_visible()}")
                print(f"    Status visible: {ongoing_review_status.is_visible()}")
                return "refund_ongoing"
            
            # Check for normal refund form
            dropdown = self.page.locator('.comet-v2-select-show-arrow').first
            if dropdown.is_visible():
                logger.debug("Found refund form dropdown")
                return "can_submit"
            
            # Debug info for unclear status
            print("    Debug: Could not determine status")
            print("    Trying to find review elements:")
            print(f"    Review title exists: {ongoing_review_title.count() > 0}")
            print(f"    Review status exists: {ongoing_review_status.count() > 0}")
            
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
            time.sleep(.1)
            
            logger.debug("Selecting reason: Tracked as returned/canceled/lost")
            reason = self.page.locator('.comet-v2-menu-item:has-text("Tracked as returned/canceled/lost")').first
            reason.click()
            time.sleep(.1)
            
            logger.debug("Entering message")
            textarea = self.page.locator('.commet--textarea--Sg0xapL').first
            textarea.fill(self.refund_message)
            time.sleep(.1)
            
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
                time.sleep(3)
                
                print("  • ✅ Refund form submitted successfully")
                return True
                
            except Exception as e:
                input(f"❌ Submit button error: {e}. Press Enter to continue...")
                return False
            
        except Exception as e:
            print(f"❌ Error filling refund form: {e}")
            return False

    def handle_waiting_response(self) -> bool:
        """Handle the case where we need to disagree and provide more evidence"""
        try:
            print("  • Handling waiting response case...")
            
            # Click View possible solutions
            solutions_button = self.page.locator('button:has-text("View possible solutions")').first
            solutions_button.click()
            time.sleep(.1)
            
            # Click disagree checkbox
            disagree_checkbox = self.page.locator('.cco--checkTitle--Gzot0Aj:has-text("I don\'t agree with above solution(s)")').first
            disagree_checkbox.click()
            time.sleep(.1)
            
            # Click Upload more photos/videos and wait for modal
            upload_button = self.page.locator('button:has-text("Upload more photos/videos")').first
            upload_button.click()
            
            # Wait for modal to appear and textarea to be visible
            print("  • Waiting for upload modal...")
            textarea = self.page.locator('.evidence--textarea--2LZFL8b').first
            textarea.wait_for(state='visible', timeout=10000)
            
            # Fill in the evidence text first
            print("  • Entering disagreement message...")
            textarea.fill(self.refund_message_2)
            time.sleep(.1)
            
            # Now upload the image
            print("  • Uploading image...")
            file_input = self.page.locator('input[type="file"][accept*="image"]').first
            file_input.set_input_files(self.image_path)
            
            # Wait for image upload to complete
            print("  • Waiting for image upload...")
            try:
                # Wait for the specific success structure: container with thumbnail that has background-image
                self.page.wait_for_selector('.upload--imageContainer--3tTIByI .upload--imageThumb--1diFoUj[style*="background-image"]', 
                                          timeout=30000)
                print("  • ✅ Image uploaded successfully")
                
                # Wait for submit button to become enabled and visible
                submit_button = self.page.locator('.comet-v2-modal-footer button.comet-v2-btn-primary').first
                submit_button.wait_for(state='visible', timeout=10000)
                time.sleep(1)  # Small delay to ensure button is clickable
                submit_button.click()
                time.sleep(3)
                
                print("  • ✅ Additional evidence submitted")
                return True
                
            except Exception as e:
                print(f"❌ Error during image upload or submission: {e}")
                return False
            
        except Exception as e:
            print(f"❌ Error handling waiting response: {e}")
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
            
            match status:
                case "refund_already_issued":
                    print("    ✅ Refund already issued")
                    return True
                
                case "needs_response":
                    print("📝 Need to provide additional evidence...")
                    return self.handle_waiting_response()
                    
                case "can_submit":
                    print("Proceeding with refund submission...")
                    return self.fill_refund_form()
                    
                case "refund_ongoing":
                    print("    ⏳ Refund is under review by AliExpress")
                    return True  # Mark as successful since we've identified the state
                
                case _:
                    print("❌ Cannot submit refund - status unclear")
                    return False
            
        except Exception as e:
            print(f"❌ Error processing refund: {e}")
            return False

def process_refunds(page: Page, order_dict: dict, image_path: str, refund_message: str, refund_message_2: str) -> dict:
    """Process refunds and update dictionary with results"""
    print("\n📋 Processing refunds:")
    
    # Clean up any existing refund tabs first
    print("  • Cleaning up old refund tabs...")
    for p in page.context.pages:
        if 'reverse-pages' in p.url:
            p.close()
    
    for order_id, data in order_dict.items():
        refund_urls = data.get('refund_urls', [])
        
        # Handle case where no refund links were found
        if not refund_urls:
            print(f"\n⚠️ No refund links found for Order {order_id}")
            print("Options:")
            print("1. Try to detect refund link again")
            print("2. Enter refund URL manually")
            print("3. Skip this order")
            
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                print("\nOpening order page...")
                page.goto(data['order_url'])
                page.wait_for_load_state('networkidle')
                input("\nPress Enter after clicking the refund button...")
                
                # Try to detect new refund tabs
                new_refund_urls = []
                for p in page.context.pages:
                    if 'reverse-pages' in p.url and p.url not in refund_urls:
                        new_refund_urls.append(p.url)
                        print(f"Found new refund URL: {p.url}")
                
                if new_refund_urls:
                    refund_urls.extend(new_refund_urls)
                    data['refund_urls'] = refund_urls
                    print(f"✅ Added {len(new_refund_urls)} new refund URLs")
                else:
                    print("❌ No new refund URLs detected")
                    data['status'] = 'failed'
                    data['status_detail'] = 'no_refund_links_found'
                    continue
            
            elif choice == "2":
                manual_url = input("\nEnter the refund URL: ").strip()
                if manual_url:
                    refund_urls.append(manual_url)
                    data['refund_urls'] = refund_urls
                else:
                    data['status'] = 'failed'
                    data['status_detail'] = 'manual_url_empty'
                    continue
            
            else:  # choice == "3" or invalid
                print("Skipping order...")
                data['status'] = 'failed'
                data['status_detail'] = 'skipped_by_user'
                continue
        
        print(f"\n🔄 Order {order_id}:")
        
        for i, refund_url in enumerate(refund_urls, 1):
            print(f"  • Processing item {i} of {len(refund_urls)}")
            
            try:
                refund_page = page.context.new_page()
                refund_page.goto(refund_url)
                refund_page.bring_to_front()
                refund_page.wait_for_load_state('networkidle')
                
                refunder = Refunder(refund_page, image_path, refund_message, refund_message_2)
                status = refunder.check_refund_status()
                
                # Update the order data with status
                data['status'] = status
                data['last_checked_url'] = refund_url
                data['last_check_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                match status:
                    case "refund_already_issued":
                        print("    ✅ Refund already issued")
                        data['status'] = 'already_issued'
                    case "needs_response":
                        if refunder.handle_waiting_response():
                            print("    ✅ Additional evidence submitted")
                            data['status'] = 'evidence_submitted'
                        else:
                            print("    ❌ Failed to submit additional evidence")
                            data['status'] = 'failed'
                            data['status_detail'] = 'evidence_submission_failed'
                    case "can_submit":
                        if refunder.fill_refund_form():
                            print("    ✅ Refund submitted")
                            data['status'] = 'refund_submitted'
                        else:
                            print("    ❌ Failed to submit refund")
                            data['status'] = 'failed'
                            data['status_detail'] = 'refund_submission_failed'
                    case "refund_ongoing":
                        print("    ⏳ Refund is under review by AliExpress")
                        data['status'] = 'refund_ongoing'
                    case _:
                        print("    ❌ Status unclear")
                        data['status'] = 'failed'
                        data['status_detail'] = 'status_unclear'
                
                # Close the tab after processing
                refund_page.close()
                
            except Exception as e:
                logger.error(f"Error processing order {order_id}: {e}")
                print(f"    ❌ Processing failed: {e}")
                data['status'] = 'failed'
                data['status_detail'] = str(e)
            
            time.sleep(2)
    
    return order_dict