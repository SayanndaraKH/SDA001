import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="userCtrlModal"')
foot_idx = text.find('class="modal-foot"', idx)
print(text[foot_idx:foot_idx+1200])
