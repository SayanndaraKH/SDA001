import os
from playwright.sync_api import sync_playwright

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out_dir = r"C:\Users\Administrator\.gemini\antigravity-ide\brain\ffc62a79-9c27-4f81-a4bb-e448e6666322"

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path, headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 1100})
    
    # 1. Open as regular user chantha_user
    page.goto('http://127.0.0.1:8000/?token=usr_24e49c84c91ccd7c0f75adf75163db1a&auth=vip', wait_until='networkidle')
    page.wait_for_timeout(1200)
    
    # Capture Top View
    top_png = os.path.join(out_dir, "vip_modal_top.png")
    page.screenshot(path=top_png)
    print("Saved:", top_png)
    
    # Scroll inside modal-scroll
    modal_scroll = page.locator('#userRegisterModal .modal-scroll')
    modal_scroll.evaluate("el => el.scrollTop = 480")
    page.wait_for_timeout(500)
    
    # Capture Scrolled View (Steps 2, 3, 4)
    scrolled_png = os.path.join(out_dir, "vip_modal_scrolled.png")
    page.screenshot(path=scrolled_png)
    print("Saved:", scrolled_png)
    
    # Test clicking VIP 3 months card
    pkg_3m = page.locator('.vip-pkg-card[data-pkg="3_months"]')
    pkg_3m.click()
    page.wait_for_timeout(400)
    
    # Check Telegram Admin link href
    tg_link = page.locator('#vipTgAdminLink')
    href = tg_link.get_attribute('href')
    print("Telegram Admin link with 3_months selected:", href)
    
    browser.close()
