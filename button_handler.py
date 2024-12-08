from playwright.sync_api import Page
import logging
import traceback

logger = logging.getLogger(__name__)

def add_checkboxes_to_orders(page: Page):
    """Add selection buttons to orders and process button"""
    try:
        print("\n🔄 Adding selection buttons to orders...")
        
        # Wait for orders to be visible first
        page.wait_for_selector('.order-item', timeout=10000)
        
        # Filter console messages to only show our debug messages
        def handle_console(msg):
            if msg.text.startswith('DEBUG:'):
                print(f"BROWSER: {msg.text}")
                
        page.on("console", handle_console)
        
        # Check if buttons are already added
        existing_buttons = page.locator('.selection-button').count()
        if existing_buttons > 0:
            print("  • Buttons already present")
            return
        
        page.evaluate('''() => {
            // Function to add button to a single order
            function addButtonToOrder(order) {
                if (order.querySelector('.selection-button')) return;
                
                const button = document.createElement('button');
                button.innerHTML = 'Select for Processing';
                button.className = 'comet-btn comet-btn-block order-item-btn selection-button';
                const orderUrl = order.querySelector('a[href*="order/detail"]').href;
                button.setAttribute('data-order-id', orderUrl);
                
                button.onclick = function() {
                    const url = this.getAttribute('data-order-id');
                    if (this.style.backgroundColor === 'rgb(245, 134, 52)') {
                        this.style.backgroundColor = '';
                        this.style.color = '';
                        window.selectedOrderUrls = window.selectedOrderUrls.filter(u => u !== url);
                    } else {
                        this.style.backgroundColor = '#f58634';
                        this.style.color = 'white';
                        if (!window.selectedOrderUrls) window.selectedOrderUrls = [];
                        window.selectedOrderUrls.push(url);
                    }
                };
                
                // Prepend button instead of append
                const buttonContainer = order.querySelector('.order-item-btns');
                buttonContainer.insertBefore(button, buttonContainer.firstChild);
            }

            // Add process button
            if (!document.getElementById('process-orders-button')) {
                const processButton = document.createElement('button');
                processButton.innerHTML = 'Process All Refunds';
                processButton.id = 'process-orders-button';
                processButton.style.cssText = `
                    position: fixed;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    padding: 15px 30px;
                    font-size: 20px;
                    background-color: #f58634;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    z-index: 1000;
                `;
                
                processButton.onclick = function() {
                    document.dispatchEvent(new CustomEvent('processOrdersClicked'));
                };
                
                document.body.appendChild(processButton);
            }

            // Add buttons to all orders
            document.querySelectorAll('.order-item').forEach(addButtonToOrder);
            
            // Keep checking for new orders
            setInterval(() => {
                document.querySelectorAll('.order-item').forEach(addButtonToOrder);
            }, 1000);
        }''')
        
        # Verify buttons were added
        page.wait_for_selector('.selection-button', timeout=5000)
        print("  • ✅ Selection buttons added successfully")
        
    except Exception as e:
        print(f"❌ Error adding buttons: {e}")
        logger.error(f"Button addition failed: {e}")
        logger.debug(traceback.format_exc())