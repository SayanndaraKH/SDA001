# -*- coding: utf-8 -*-
import subprocess, os, json, tempfile

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
tmp_dir = tempfile.mkdtemp()
png_out = os.path.abspath("scratch/logout_modal_state.png")

# HTML harness that starts logged in as soktest1, then clicks logout
harness_html = """<!doctype html>
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
      // Mock confirm to return true automatically
      win.confirm = () => true;
      // Log in as soktest1 first
      win.userAccess = {
        authenticated: true,
        username: 'soktest1',
        name: 'សុខ ពិសិដ្ឋ',
        is_admin: false,
        is_vip: false,
        status: 'user'
      };
      win.localStorage.setItem('syd_auth_token', 'test_token');
      win.updateAccessUI(win.userAccess);
      win.closeUserRegisterModal();

      // Now click logout after 500ms
      setTimeout(() => {
        const logoutBtn = win.document.getElementById('topLogoutBtn');
        if(logoutBtn){
          logoutBtn.click();
        }
      }, 500);
    } catch(e){
      console.error(e);
    }
  }, 1000);
};
</script>
</body>
</html>
"""

with open("scratch/test_logout.html", "w", encoding="utf-8") as f:
    f.write(harness_html)

test_path = os.path.abspath("scratch/test_logout.html")
cmd = [
    chrome,
    "--headless=new",
    "--disable-web-security",
    f"--user-data-dir={tmp_dir}",
    "--window-size=1280,960",
    f"--screenshot={png_out}",
    "--virtual-time-budget=4000",
    f"file:///{test_path}"
]

p = subprocess.run(cmd, capture_output=True)
print("Logout test finished. Screenshot created:", os.path.exists(png_out))
