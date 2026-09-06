import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/diff_downloader.diff', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx2 = text.find('id="coinModal"')
idx2_end = text.find('</div>\n \n <!-- System Info Modal', idx2)
if idx2_end == -1:
    idx2_end = text.find('<!-- System Info Modal', idx2)
print("=== FULL COIN MODAL HTML ===")
print(text[idx2:idx2_end])

idx_js = text.find('// --- User Coin Modal Logic ---')
idx_js_end = text.find('// ====================================================\n+// DRAMA RULES', idx_js)
if idx_js_end == -1:
    idx_js_end = idx_js + 5000
print("\n=== FULL COIN JS ===")
print(text[idx_js:idx_js_end])
