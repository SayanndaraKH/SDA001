from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1000, 'height': 720})
    page.goto('http://localhost:8000')
    page.wait_for_timeout(1000)
    # Set dark mode
    page.evaluate('document.documentElement.setAttribute("data-theme", "dark")')
    page.evaluate('openFolderPickerModal()')
    page.wait_for_timeout(500)
    # Click drive F:
    page.evaluate('document.querySelectorAll(".fp-drv-btn")[3].click()')
    page.wait_for_timeout(300)
    page.screenshot(path='scratch/folder_picker_dark_verified.png')
    browser.close()
print('Dark mode screenshot captured')
