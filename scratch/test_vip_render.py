import subprocess, os

token = "usr_24e49c84c91ccd7c0f75adf75163db1a"

html_content = f"""<!DOCTYPE html>
<html>
<body style="margin:0;background:#15100d">
<iframe id="testFrame" src="http://127.0.0.1:8000/?auth_token={token}" style="width:1280px;height:950px;border:none;"></iframe>
<script>
window.addEventListener('load', () => {{
  setTimeout(() => {{
    const fWin = document.getElementById('testFrame').contentWindow;
    // Open VIP modal
    if(fWin && fWin.openUserRegisterModal) {{
      fWin.openUserRegisterModal('vip');
      // Scroll modal-scroll down a bit so all steps are visible
      setTimeout(() => {{
        const m = fWin.document.querySelector('.modal-scroll');
        if(m) m.scrollTop = 120;
      }}, 500);
    }}
  }}, 1500);
}});
</script>
</body>
</html>"""

with open('scratch/test_chantha_vip.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
out_path = os.path.abspath('scratch/chantha_vip_modal_view.png')
file_url = 'file:///' + os.path.abspath('scratch/test_chantha_vip.html').replace('\\', '/')

cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=6000',
    '--window-size=1280,1050',
    f'--screenshot={out_path}',
    file_url
]
subprocess.run(cmd, timeout=25)
print("Screenshot generated:", os.path.exists(out_path))
