# -*- coding: utf-8 -*-
import subprocess, time, os, urllib.request, json, sys

sys.stdout.reconfigure(encoding='utf-8')

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome):
    chrome = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

token = "usr_c76e0b9127a368d4e45f45f0b40126e3"

html_content = f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');

// Set token into iframe's localStorage before it initializes or right after
window.addEventListener('message', () => {{}});

frame.onload = () => {{
  try {{
    const win = frame.contentWindow;
    win.localStorage.setItem('syd_auth_token', '{token}');
    win.localStorage.setItem('syd_auth_user', 'test_user_777');
    
    // Trigger checkUserAccess to fetch authentic status
    win.checkUserAccess().then(() => {{
      document.title = "AUTH_LOADED";
    }});
  }} catch(e) {{
    console.error(e);
  }}
}};
</script>
</body>
</html>
"""

with open("scratch/test_auth_coin.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# 1. Capture authenticated topbar with Coin Badge
out_badge = os.path.abspath("scratch/auth_coin_badge.png")
cmd1 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_badge}",
    f"file:///{os.path.abspath('scratch/test_auth_coin.html').replace(os.sep, '/')}"
]
print("Capturing authenticated topbar...")
subprocess.run(cmd1, timeout=20)
print(f"Auth topbar saved: {os.path.exists(out_badge)} ({os.path.getsize(out_badge) if os.path.exists(out_badge) else 0} bytes)")

# 2. Capture Coin Wallet Modal
html_modal = f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {{
  try {{
    const win = frame.contentWindow;
    win.localStorage.setItem('syd_auth_token', '{token}');
    win.localStorage.setItem('syd_auth_user', 'test_user_777');
    
    win.checkUserAccess().then(() => {{
      setTimeout(() => {{
        win.openCoinModal();
        document.title = "COIN_MODAL_OPEN";
      }}, 500);
    }});
  }} catch(e) {{
    console.error(e);
  }}
}};
</script>
</body>
</html>
"""
with open("scratch/test_auth_modal.html", "w", encoding="utf-8") as f:
    f.write(html_modal)

out_modal = os.path.abspath("scratch/auth_coin_modal.png")
cmd2 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_modal}",
    f"file:///{os.path.abspath('scratch/test_auth_modal.html').replace(os.sep, '/')}"
]
print("Capturing coin modal...")
subprocess.run(cmd2, timeout=20)
print(f"Coin modal saved: {os.path.exists(out_modal)} ({os.path.getsize(out_modal) if os.path.exists(out_modal) else 0} bytes)")

# 3. Capture Drama Detail with Buy Drama Button
html_detail = f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {{
  try {{
    const win = frame.contentWindow;
    win.localStorage.setItem('syd_auth_token', '{token}');
    win.localStorage.setItem('syd_auth_user', 'test_user_777');
    
    win.checkUserAccess().then(() => {{
      setTimeout(() => {{
        // Open drama detail
        win.openDramaDetail('7662291674818677784');
        document.title = "DRAMA_DETAIL_OPEN";
      }}, 600);
    }});
  }} catch(e) {{
    console.error(e);
  }}
}};
</script>
</body>
</html>
"""
with open("scratch/test_auth_detail.html", "w", encoding="utf-8") as f:
    f.write(html_detail)

out_detail = os.path.abspath("scratch/auth_drama_detail.png")
cmd3 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_detail}",
    f"file:///{os.path.abspath('scratch/test_auth_detail.html').replace(os.sep, '/')}"
]
print("Capturing drama detail...")
subprocess.run(cmd3, timeout=20)
print(f"Drama detail saved: {os.path.exists(out_detail)} ({os.path.getsize(out_detail) if os.path.exists(out_detail) else 0} bytes)")

# 4. Capture Logout -> Mandatory Login Modal
html_logout = f"""<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {{
  try {{
    const win = frame.contentWindow;
    win.localStorage.setItem('syd_auth_token', '{token}');
    win.localStorage.setItem('syd_auth_user', 'test_user_777');
    
    win.checkUserAccess().then(() => {{
      setTimeout(() => {{
        // Perform explicit logout
        win.doExplicitLogout();
        document.title = "LOGGED_OUT_MODAL_OPEN";
      }}, 600);
    }});
  }} catch(e) {{
    console.error(e);
  }}
}};
</script>
</body>
</html>
"""
with open("scratch/test_auth_logout.html", "w", encoding="utf-8") as f:
    f.write(html_logout)

out_logout = os.path.abspath("scratch/auth_logout_modal.png")
cmd4 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_logout}",
    f"file:///{os.path.abspath('scratch/test_auth_logout.html').replace(os.sep, '/')}"
]
print("Capturing logout modal...")
subprocess.run(cmd4, timeout=20)
print(f"Logout modal saved: {os.path.exists(out_logout)} ({os.path.getsize(out_logout) if os.path.exists(out_logout) else 0} bytes)")
