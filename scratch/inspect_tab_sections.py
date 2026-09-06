import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="userCtrlModal"')
end_idx = text.find('id="pushDeployModal"', idx)

content = text[idx:end_idx]

import re
for sec in ['ucTabUsersSec', 'ucTabSettingsSec', 'ucTabSysSec', 'ucTabFirebaseSec']:
    s = content.find(f'id="{sec}"')
    if s != -1:
        print(f'=== {sec} ===')
        print(content[s:s+400])
