# -*- coding: utf-8 -*-
import subprocess, time, os, urllib.request, json
import sys
sys.stdout.reconfigure(encoding='utf-8')

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(chrome):
    chrome = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

test_runner_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {
  setTimeout(() => {
    try {
      const win = frame.contentWindow;
      // Mock logged in user with 8 coins
      win.userAccess = {
        authenticated: true,
        username: 'test_user_777',
        name: 'Test User',
        contact: '012345678',
        role: 'user',
        is_admin: false,
        is_vip: false,
        coins: 8,
        coins_riel: 4000,
        purchased_series: {},
        max_free_episodes: 5,
        settings: {
          vip_request_enabled: true
        }
      };
      win.updateAccessUI(win.userAccess);
      document.title = "LOGGED_IN_STATE_READY";
    } catch(e){
      console.error(e);
    }
  }, 1200);
};
</script>
</body>
</html>
"""

with open("scratch/test_runner_coin.html", "w", encoding="utf-8") as f:
    f.write(test_runner_html)

# 1. Capture logged-in topbar with Coin badge
out_img = os.path.abspath("scratch/coin_badge_verified.png")
cmd = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_img}",
    f"file:///{os.path.abspath('scratch/test_runner_coin.html').replace(os.sep, '/')}"
]
print("Running chrome screenshot for topbar coin badge...")
subprocess.run(cmd, timeout=15)
print(f"Screenshot saved: {os.path.exists(out_img)} ({os.path.getsize(out_img) if os.path.exists(out_img) else 0} bytes)")

# 2. Capture Coin Modal
test_modal_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {
  setTimeout(() => {
    try {
      const win = frame.contentWindow;
      win.userAccess = {
        authenticated: true,
        username: 'test_user_777',
        name: 'Test User',
        contact: '012345678',
        role: 'user',
        is_admin: false,
        is_vip: false,
        coins: 8,
        coins_riel: 4000,
        purchased_series: {},
        max_free_episodes: 5
      };
      win.updateAccessUI(win.userAccess);
      win.openCoinModal();
      document.title = "COIN_MODAL_READY";
    } catch(e){
      console.error(e);
    }
  }, 1200);
};
</script>
</body>
</html>
"""
with open("scratch/test_modal_coin.html", "w", encoding="utf-8") as f:
    f.write(test_modal_html)

out_modal_img = os.path.abspath("scratch/coin_modal_verified.png")
cmd2 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_modal_img}",
    f"file:///{os.path.abspath('scratch/test_modal_coin.html').replace(os.sep, '/')}"
]
print("Running chrome screenshot for coin modal...")
subprocess.run(cmd2, timeout=15)
print(f"Coin modal screenshot saved: {os.path.exists(out_modal_img)} ({os.path.getsize(out_modal_img) if os.path.exists(out_modal_img) else 0} bytes)")

# 3. Capture Drama Detail with Coin Buy Button
test_detail_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
const frame = document.getElementById('appFrame');
frame.onload = () => {
  setTimeout(() => {
    try {
      const win = frame.contentWindow;
      win.userAccess = {
        authenticated: true,
        username: 'test_user_777',
        role: 'user',
        coins: 8,
        purchased_series: {}
      };
      win.updateAccessUI(win.userAccess);
      // Mock opening drama
      win.ddCurrentDrama = {
        id: '7662291674818677784',
        title: '测试剧集',
        title_km: 'រឿងខ្លីតេស្តសាកល្បង',
        total: 50,
        score: '9.2'
      };
      win.renderDramaDetailUI(win.ddCurrentDrama);
      document.getElementById('appFrame').style.display = 'block';
      win.document.getElementById('resultsSec').hidden = true;
      win.document.getElementById('dramaDetailSec').hidden = false;
      document.title = "DRAMA_DETAIL_READY";
    } catch(e){
      console.error(e);
    }
  }, 1200);
};
</script>
</body>
</html>
"""
with open("scratch/test_detail_coin.html", "w", encoding="utf-8") as f:
    f.write(test_detail_html)

out_detail_img = os.path.abspath("scratch/drama_detail_coin_verified.png")
cmd3 = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    f"--screenshot={out_detail_img}",
    f"file:///{os.path.abspath('scratch/test_detail_coin.html').replace(os.sep, '/')}"
]
print("Running chrome screenshot for drama detail coin buy button...")
subprocess.run(cmd3, timeout=15)
print(f"Drama detail screenshot saved: {os.path.exists(out_detail_img)} ({os.path.getsize(out_detail_img) if os.path.exists(out_detail_img) else 0} bytes)")
