# -*- coding: utf-8 -*-
import subprocess, time, os, urllib.request, json

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Helper script that creates a small runner HTML to load the app in an iframe or directly,
# injects the state, and takes screenshots
test_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;background:#110b07">
<iframe id="appFrame" src="http://127.0.0.1:8000/" style="width:1280px;height:900px;border:none"></iframe>
<script>
window.addEventListener('message', e => {});
</script>
</body>
</html>
"""

with open("scratch/runner.html", "w", encoding="utf-8") as f:
    f.write(test_html)

# We can also test directly with Chrome evaluating script or using a temporary test page:
# Let's create specific test states in a helper test page
state_vip_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<iframe id="f" src="http://127.0.0.1:8000/" style="width:1280px;height:960px;border:none"></iframe>
<script>
const f = document.getElementById('f');
f.onload = () => {
  setTimeout(() => {
    try {
      const win = f.contentWindow;
      // Set user access as regular user
      win.userAccess = {
        authenticated: true,
        username: 'soktest1',
        name: 'សុខ ពិសិដ្ឋ',
        contact: '012888999',
        is_admin: false,
        is_vip: false,
        status: 'user',
        device_id: 'test_dev_001',
        settings: {
          khqr_image: 'https://upload.wikimedia.org/wikipedia/commons/d/d0/QR_code_for_mobile_English_Wikipedia.svg',
          telegram_admin: 'https://t.me/syd_admin_support',
          telegram_group: 'https://t.me/syd_drama_community'
        }
      };
      win.updateAccessUI(win.userAccess);
      win.openUserRegisterModal('vip');
      document.title = "STATE_VIP_READY";
    } catch(e){
      console.error(e);
    }
  }, 1000);
};
</script>
</body>
</html>
"""

with open("scratch/view_vip.html", "w", encoding="utf-8") as f:
    f.write(state_vip_html)

# Admin Dashboard Tab 1 (User Management)
state_admin_users_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<iframe id="f" src="http://127.0.0.1:8000/" style="width:1280px;height:960px;border:none"></iframe>
<script>
const f = document.getElementById('f');
f.onload = () => {
  setTimeout(() => {
    try {
      const win = f.contentWindow;
      win.localStorage.setItem('syd_auth_token', '8888');
      win.userAccess = {
        authenticated: true,
        username: 'ADMIN',
        name: 'Administrator',
        is_admin: true,
        is_vip: true,
        role: 'admin',
        device_id: 'admin_pc'
      };
      win.updateAccessUI(win.userAccess);
      win.openUserControl();
      win.switchUcTab('users');
      document.title = "STATE_ADMIN_USERS_READY";
    } catch(e){
      console.error(e);
    }
  }, 1200);
};
</script>
</body>
</html>
"""

with open("scratch/view_admin_users.html", "w", encoding="utf-8") as f:
    f.write(state_admin_users_html)

# Admin Dashboard Tab 2 (KHQR & Telegram Settings)
state_admin_settings_html = """<!doctype html>
<html>
<head><meta charset="utf-8"></head>
<body>
<iframe id="f" src="http://127.0.0.1:8000/" style="width:1280px;height:960px;border:none"></iframe>
<script>
const f = document.getElementById('f');
f.onload = () => {
  setTimeout(() => {
    try {
      const win = f.contentWindow;
      win.localStorage.setItem('syd_auth_token', '8888');
      win.userAccess = {
        authenticated: true,
        username: 'ADMIN',
        name: 'Administrator',
        is_admin: true,
        is_vip: true,
        role: 'admin',
        device_id: 'admin_pc'
      };
      win.updateAccessUI(win.userAccess);
      win.openUserControl();
      win.switchUcTab('settings');
      document.title = "STATE_ADMIN_SETTINGS_READY";
    } catch(e){
      console.error(e);
    }
  }, 1200);
};
</script>
</body>
</html>
"""

with open("scratch/view_admin_settings.html", "w", encoding="utf-8") as f:
    f.write(state_admin_settings_html)

print("Generated test state HTML files!")
