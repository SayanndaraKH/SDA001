import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/diff_downloader.diff', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('ddCoinPriceBadge')
print(text[max(0, idx-400):min(len(text), idx+1200)])
