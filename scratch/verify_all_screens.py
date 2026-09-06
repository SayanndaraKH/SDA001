# -*- coding: utf-8 -*-
import subprocess, time, os, urllib.request, json, sys

sys.stdout.reconfigure(encoding='utf-8')

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome):
    chrome = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Login test_user_777 to obtain a fresh token
req = urllib.request.Request('http://127.0.0.1:8000/dl/access/login', 
    data=json.dumps({'identity': 'test_user_777', 'password': 'password123'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read())
tok = res.get('token')
print("Active Token for test_user_777:", tok)

# 1. Capture Coin Modal
out_modal = os.path.abspath("scratch/coin_modal_verified.png")
cmd1 = [
    chrome, "--headless", "--disable-gpu", "--window-size=1280,900",
    "--virtual-time-budget=6000", f"--screenshot={out_modal}",
    f"http://127.0.0.1:8000/?auth_token={tok}&action=coin_modal"
]
print("Capturing Coin Modal...")
subprocess.run(cmd1, timeout=25)
print(f"Coin modal saved: {os.path.exists(out_modal)} ({os.path.getsize(out_modal) if os.path.exists(out_modal) else 0} bytes)")

# 2. Capture Drama Detail with Buy Drama Button
out_detail = os.path.abspath("scratch/drama_detail_coin_verified.png")
cmd2 = [
    chrome, "--headless", "--disable-gpu", "--window-size=1280,900",
    "--virtual-time-budget=6000", f"--screenshot={out_detail}",
    f"http://127.0.0.1:8000/?auth_token={tok}&action=detail&drama_id=7662291674818677784"
]
print("Capturing Drama Detail with Coin Buy Button...")
subprocess.run(cmd2, timeout=25)
print(f"Drama detail saved: {os.path.exists(out_detail)} ({os.path.getsize(out_detail) if os.path.exists(out_detail) else 0} bytes)")

# 3. Capture Mandatory Login Modal after Logout
out_logout = os.path.abspath("scratch/logout_mandatory_verified.png")
cmd3 = [
    chrome, "--headless", "--disable-gpu", "--window-size=1280,900",
    "--virtual-time-budget=6000", f"--screenshot={out_logout}",
    f"http://127.0.0.1:8000/?auth_token={tok}&action=logout"
]
print("Capturing Logout -> Mandatory Login Modal...")
subprocess.run(cmd3, timeout=25)
print(f"Logout modal saved: {os.path.exists(out_logout)} ({os.path.getsize(out_logout) if os.path.exists(out_logout) else 0} bytes)")
