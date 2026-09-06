import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/diff_downloader.diff', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'ទិញ', text)]
print('Matches for ទិញ:', len(matches))
for idx in matches[:15]:
    print(text[max(0, idx-50):min(len(text), idx+150)])
    print('-'*40)
