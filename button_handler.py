from playwright.sync_api import Page

def add_checkboxes_to_orders(page: Page):
    try:
        print("DEBUG: Starting to add checkboxes...")
        page.evaluate('''() => {
            // Store selected URLs globally
            window.selectedOrderUrls = window.selectedOrderUrls || [];
            
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
                    if (this.style.backgroundColor === 'rgb(0, 153, 102)') {
                        this.style.backgroundColor = '';
                        this.style.color = '';
                        window.selectedOrderUrls = window.selectedOrderUrls.filter(u => u !== url);
                        console.log('DEBUG: Order deselected:', url);
                    } else {
                        this.style.backgroundColor = '#009966';
                        this.style.color = 'white';
                        window.selectedOrderUrls.push(url);
                        console.log('DEBUG: Order selected:', url);
                    }
                };
                order.querySelector('.order-item-btns').appendChild(button);
            }

            // Add process button
            if (!document.getElementById('process-orders-button')) {
                const processButton = document.createElement('button');
                processButton.innerHTML = 'Process Selected Orders';
                processButton.id = 'process-orders-button';
                processButton.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    padding: 15px 30px;
                    font-size: 18px;
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    z-index: 1000;
                `;
                
                processButton.onclick = function() {
                    console.log('DEBUG: Process button clicked. Selected URLs:', window.selectedOrderUrls);
                    document.dispatchEvent(new CustomEvent('processOrdersClicked'));
                };
                
                document.body.appendChild(processButton);
            }

            // Add buttons to existing orders
            document.querySelectorAll('.order-item').forEach(addButtonToOrder);
            
            // Keep checking for new orders
            setInterval(() => {
                document.querySelectorAll('.order-item').forEach(addButtonToOrder);
            }, 1000);
        }''')
        
        # Add console message handler
        page.on("console", lambda msg: print(f"BROWSER: {msg.type} - {msg.text}"))
        
        print("DEBUG: Setup complete - buttons and handlers added")
        
    except Exception as e:
        print(f"ERROR in add_checkboxes_to_orders: {str(e)}")