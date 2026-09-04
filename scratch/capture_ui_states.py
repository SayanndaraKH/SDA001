# -*- coding: utf-8 -*-
import subprocess, time, os, json, urllib.request

# Put a nice sample KHQR image into settings so it displays nicely
admin_payload = {
    "pin": "8888",
    "token": "",
    "settings": {
        "khqr_image": "https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg",
        "telegram_admin": "https://t.me/syd_admin",
        "telegram_group": "https://t.me/syd_community"
    }
}
req = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/admin/settings",
    data=json.dumps(admin_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
urllib.request.urlopen(req)

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# 1. Capture regular user VIP request modal with KHQR and Telegram links
# We can create a lightweight test HTML or execute script via chrome remote debugging.
# Or even simpler: create a test page or use a Chrome session with devtools protocol.
print("Settings configured successfully!")
