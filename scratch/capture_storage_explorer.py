import subprocess, os

html_test = """<!DOCTYPE html>
<html>
<body style="margin:0;background:#15100d">
<iframe id="f" src="http://127.0.0.1:8000/?token=usr_24e49c84c91ccd7c0f75adf75163db1a" style="width:1280px;height:950px;border:none;"></iframe>
<script>
window.addEventListener('load', () => {
  setTimeout(() => {
    try {
      const doc = document.getElementById('f').contentDocument || document.getElementById('f').contentWindow.document;
      const win = document.getElementById('f').contentWindow;
      doc.querySelectorAll('.modal').forEach(m => m.hidden = true);
      const m = doc.getElementById('storageExplorerModal');
      if (m) {
        m.hidden = false;
        if (win.refreshStorageExplorer) win.refreshStorageExplorer();
      }
    } catch(e) { console.error(e); }
  }, 2500);
});
</script>
</body>
</html>"""

with open('scratch/test_storage_explorer.html', 'w', encoding='utf-8') as f:
    f.write(html_test)

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
out_path = os.path.abspath('scratch/storage_explorer_verified.png')
file_url = 'file:///' + os.path.abspath('scratch/test_storage_explorer.html').replace('\\', '/')

cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=7000',
    '--window-size=1280,950',
    f'--screenshot={out_path}',
    file_url
]
subprocess.run(cmd, timeout=30)
print("Screenshot captured to", out_path)
