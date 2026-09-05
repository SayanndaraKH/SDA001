from playwright.sync_api import sync_playwright
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 950})
    page.goto("http://127.0.0.1:8000/?token=usr_24e49c84c91ccd7c0f75adf75163db1a")
    page.wait_for_timeout(2000)
    page.evaluate("""() => {
        document.querySelectorAll('.modal').forEach(m => m.hidden = true);
        if (window.openStorageExplorerModal) {
            window.openStorageExplorerModal();
        }
    }""")
    page.wait_for_timeout(1000)
    out_path = os.path.abspath("scratch/storage_explorer_verified.png")
    page.screenshot(path=out_path)
    browser.close()
    print("Screenshot saved to", out_path)
