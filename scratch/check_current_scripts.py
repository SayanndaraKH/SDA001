import re
from py_mini_racer import MiniRacer

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', html, re.DOTALL)
print(f'Found {len(scripts)} scripts in downloader.html')

mr = MiniRacer()
mr.eval('''
function checkJs(src) {
    try {
        new Function(src);
        return "OK";
    } catch(e) {
        return String(e);
    }
}
''')

for i, s in enumerate(scripts):
    status = mr.call('checkJs', s)
    print(f'Script {i} (len={len(s)}): {status}')
