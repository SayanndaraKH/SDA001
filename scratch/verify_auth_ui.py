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

# HTML wrapper that loads the app, logs in via token, and performs UI actions
def make_runner_html(js_action):
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/?auth_token={tok}" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {{
  setTimeout(() => {{
    try {{
      const win = frame.contentWindow;
      {js_action}
    }} catch(e) {{
      console.error(e);
    }}
  }}, 1500);
}};
</script>
</body>
</html>
"""

# 1. Capture Coin Modal
with open("scratch/runner_coin_modal.html", "w", encoding="utf-8") as f:
    f.write(make_runner_html("win.openCoinModal();"))

out_modal = os.path.abspath("scratch/auth_coin_modal_verified.png")
cmd1 = [
    chrome, "--headless", "--disable-gpu", "--window-size=1280,900",
    "--virtual-time-budget=6000", f"--screenshot={out_modal}",
    f"file:///{os.path.abspath('scratch/runner_coin_modal.html').replace(os.sep, '/')}"
]
print("Capturing Coin Modal...")
subprocess.run(cmd1, timeout=25)
print(f"Coin modal saved: {os.path.exists(out_modal)} ({os.path.getsize(out_modal) if os.path.exists(out_modal) else 0} bytes)")

# 2. Capture Drama Detail with Buy Drama with Coins button
detail_js = """
// Open drama detail
win.openDramaDetail('7662291674818677784');
"""
with open("scratch/runner_drama_detail.html", "w", encoding="utf-8") as f:
    f.write(make_runner_html(detail_js))

out_detail = os.path.abspath("scratch/auth_drama_detail_verified.png")
cmd2 = [
    chrome, "--headless", "--disable-gpu", "--window-size=1280,900",
    "--virtual-time-budget=6000", f"--screenshot={out_detail}",
    f"file:///{os.path.abspath('scratch/runner_drama_detail.html').replace(os.sep, '/')}"
]
print("Capturing Drama Detail with Coin Buy Button...")
subprocess.run(cmd2, timeout=25)
print(f"Drama detail saved: {os.path.exists(out_detail)} ({os.path.getsize(out_detail) if os.path.exists(out_detail) else 0} bytes)")

# 3. Capture Mandatory Login Modal after Logout
logout_js = """
win.confirm = () => true; // auto-confirm confirm dialog
win.doExplicitLogout();
"""
with open("scratch/runner_logout.html", "w", encoding="utf-8") as f:
    f.write(make_runner_html(logout_js))

out_logout = os.path.abspath("scratch/auth_logout_mandatory_verified.png")
cmd3 = [
    chrome, "--headless", "--disable-gpu", "--window-size=1280,900",
    "--virtual-time-budget=6000", f"--screenshot={out_logout}",
    f"file:///{os.path.abspath('scratch/runner_logout.html').replace(os.sep, '/')}"
]
print("Capturing Logout -> Mandatory Login Modal...")
subprocess.run(cmd3, timeout=25)
print(f"Logout modal saved: {os.path.exists(out_logout)} ({os.path.getsize(out_logout) if os.path.exists(out_logout) else 0} bytes)")
