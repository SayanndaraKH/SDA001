import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="userCtrlModal"')
print(text[idx:idx+3500])
