from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--start-maximized',  # Start maximized
            '--window-size=1920,1080'  # Full HD
        ]
    )
    page = browser.new_page()
    page.goto('https://login.aliexpress.com/')
    input("Press Enter to close...") 