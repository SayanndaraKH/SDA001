import re

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

modals = re.findall(r'<div class="modal"[^>]*id="([^"]+)"[^>]*>.*?<div class="modal-card"[^>]*style="([^"]+)"', text, re.DOTALL)
for m_id, style in modals:
    # extract max-width
    mw = re.search(r'max-width:([^;]+)', style)
    print(f'{m_id}: {mw.group(1) if mw else "none"}')
