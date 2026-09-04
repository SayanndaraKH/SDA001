import subprocess, os

html_test = """<!DOCTYPE html>
<html>
<body style="margin:0;background:#15100d">
<iframe id="f" src="http://127.0.0.1:8000/?token=usr_24e49c84c91ccd7c0f75adf75163db1a&auth=vip" style="width:1280px;height:1050px;border:none;"></iframe>
<script>
window.addEventListener('load', () => {
  setTimeout(() => {
    try {
      const doc = document.getElementById('f').contentDocument || document.getElementById('f').contentWindow.document;
      const scrollEl = doc.querySelector('.modal-scroll');
      if (scrollEl) {
        scrollEl.scrollTop = 450;
      }
    } catch(e) { console.error(e); }
  }, 2000);
});
</script>
</body>
</html>"""

with open('scratch/test_scroll_vip.html', 'w', encoding='utf-8') as f:
    f.write(html_test)

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
out_path = os.path.abspath('scratch/vip_direct_modal_scrolled.png')
file_url = 'file:///' + os.path.abspath('scratch/test_scroll_vip.html').replace('\\', '/')

cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=7000',
    '--window-size=1280,1050',
    f'--screenshot={out_path}',
    file_url
]
subprocess.run(cmd, timeout=30)
print('Screenshot exists:', os.path.exists(out_path))
