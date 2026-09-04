# -*- coding: utf-8 -*-
import subprocess, time, os, urllib.request, json

# 1. Test backend endpoints
print("Testing /dl/access/settings...")
req = urllib.request.urlopen("http://127.0.0.1:8000/dl/access/settings")
data = json.loads(req.read().decode('utf-8'))
print("Settings response:", data)

print("Testing /dl/access/status...")
req = urllib.request.urlopen("http://127.0.0.1:8000/dl/access/status")
status_data = json.loads(req.read().decode('utf-8'))
print("Status authenticated:", status_data.get('authenticated'), "role:", status_data.get('role'))

# 2. Test Chrome Headless rendering & screenshots
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
screenshot_out = os.path.abspath("scratch/test_startup_modal.png")

cmd = [
    chrome,
    "--headless=new",
    "--window-size=1280,960",
    "--screenshot=" + screenshot_out,
    "--virtual-time-budget=4000",
    "http://127.0.0.1:8000/downloader.html"
]

p = subprocess.run(cmd, capture_output=True, text=True)
print("Chrome return code:", p.returncode)
print("Screenshot generated:", os.path.exists(screenshot_out))
