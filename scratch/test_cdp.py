# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, os, sys
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

# Launch Chrome with remote debugging
chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
port = 9222
user_data_dir = os.path.abspath("scratch/chrome_debug_profile")

cmd = [
    chrome,
    f"--remote-debugging-port={port}",
    f"--user-data-dir={user_data_dir}",
    "--headless",
    "--disable-gpu",
    "about:blank"
]
proc = subprocess.Popen(cmd)
time.sleep(1.5)

try:
    # Get WebSocket debugger URL
    version_url = f"http://127.0.0.1:{port}/json/version"
    ver_info = json.loads(urllib.request.urlopen(version_url).read())
    print("Browser:", ver_info.get("Browser"))

    # Create new target / page
    new_page_url = f"http://127.0.0.1:{port}/json/new?http://127.0.0.1:8000/?auth_token=usr_a774fa0087246dc72db6dbe2136b6039"
    page_info = json.loads(urllib.request.urlopen(urllib.request.Request(new_page_url, method='PUT')).read())
    ws_url = page_info.get("webSocketDebuggerUrl")
    print("Page WS:", ws_url)
    
    # Wait for page to execute
    time.sleep(3)

    # Use python's websocket or urllib to inspect
    # Let's see if we have websockets installed
except Exception as e:
    print("CDP Error:", e)
finally:
    proc.terminate()
