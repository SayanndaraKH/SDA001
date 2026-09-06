import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="userCtrlModal"')
end_idx = text.find('</div>\n</div>\n\n', idx)
if end_idx == -1:
    end_idx = text.find('<!--', idx + 500)

print('Modal length:', end_idx - idx)
# Find all tabs inside this modal
import re
tabs = re.findall(r'id="(ucTab\w+)"', text[idx:end_idx])
print('Found tab sections:', tabs)
