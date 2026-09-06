import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/diff_downloader.diff', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# 1. Top Coin Badge
idx_top = text.find('id="topCoinBadge"')
start_top = text.rfind('\n+', 0, idx_top)
end_top = text.find('</div>', idx_top) + 6

print("--- TOP BADGE ---")
lines_top = [l[1:] if l.startswith('+') else l for l in text[start_top:end_top].split('\n')]
top_badge_html = '\n'.join(lines_top).strip()
print(top_badge_html)

# 2. Coin Modal HTML
idx_modal = text.find('id="coinModal"')
start_modal = text.rfind('\n+', 0, idx_modal)
# find closing </div> of modal
# It ends right before <!-- System Info Modal
end_modal = text.find('<!-- System Info Modal', idx_modal)
lines_modal = [l[1:] if l.startswith('+') else l for l in text[start_modal:end_modal].split('\n')]
modal_html = '\n'.join(lines_modal).strip()

with open('scratch/extracted_coin_modal.html', 'w', encoding='utf-8') as f_out:
    f_out.write(modal_html)
print(f"Extracted coin modal HTML: {len(modal_html)} bytes")

# 3. Coin JS
idx_js = text.find('// --- User Coin Modal Logic ---')
end_js = text.find('window.adminRefreshCoinTransactions = function()', idx_js)
end_js2 = text.find('};', end_js) + 2
lines_js = [l[1:] if l.startswith('+') else l for l in text[idx_js:end_js2].split('\n')]
js_code = '\n'.join(lines_js).strip()

with open('scratch/extracted_coin_logic.js', 'w', encoding='utf-8') as f_out:
    f_out.write(js_code)
print(f"Extracted coin JS logic: {len(js_code)} bytes")
