import subprocess, os

html_test = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Battambang:wght@400;700;900&family=Kantumruy+Pro:wght@400;600;700;800&family=Koulen&family=Moul&family=Siemreap&display=swap" rel="stylesheet">
<style>
body { background: #18110b; color: #fff; padding: 40px; font-size: 24px; }
.test { margin-bottom: 25px; padding: 15px; border: 1px solid #333; }
</style>
</head>
<body>
<div class="test" style="font-family:'Khmer OS Battambang','Battambang',sans-serif; letter-spacing:0.02em;">
  1. Old style in modal: Khmer OS Battambang, letter-spacing: 0.02em<br>
  សូមស្វាគមន៍មកកាន់! SYD DRAMA
</div>

<div class="test" style="font-family:'Battambang',sans-serif; font-weight:700; letter-spacing:normal;">
  2. Battambang (Google Fonts), letter-spacing: normal<br>
  សូមស្វាគមន៍មកកាន់! SYD DRAMA
</div>

<div class="test" style="font-family:'Kantumruy Pro',sans-serif; font-weight:700; letter-spacing:normal;">
  3. Kantumruy Pro (Google Fonts), letter-spacing: normal<br>
  សូមស្វាគមន៍មកកាន់! SYD DRAMA
</div>

<div class="test" style="font-family:'Siemreap',sans-serif; font-weight:700; letter-spacing:normal;">
  4. Siemreap, letter-spacing: normal<br>
  សូមស្វាគមន៍មកកាន់! SYD DRAMA
</div>

<div class="test" style="font-family:'Koulen',cursive; font-size: 28px; letter-spacing:normal;">
  5. Koulen (Google Fonts display font), letter-spacing: normal<br>
  សូមស្វាគមន៍មកកាន់! SYD DRAMA
</div>
</body>
</html>"""

with open('scratch/font_test.html', 'w', encoding='utf-8') as f:
    f.write(html_test)

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
out_path = os.path.abspath('scratch/font_test.png')
file_url = 'file:///' + os.path.abspath('scratch/font_test.html').replace('\\', '/')
cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=5000',
    '--window-size=1000,900',
    f'--screenshot={out_path}',
    file_url
]
subprocess.run(cmd, timeout=20)
print('Generated font_test.png:', os.path.exists(out_path))
