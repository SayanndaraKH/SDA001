import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/diff_downloader.diff', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('id="coinModal"')
idx2 = text.find('window.openCoinModal', idx)
print("=== COIN MODAL HTML ===")
print(text[idx:idx+3000])

print("\n=== COIN JS LOGIC ===")
print(text[idx2:idx2+3500])
