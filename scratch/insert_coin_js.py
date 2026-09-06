# -*- coding: utf-8 -*-
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/patch_all_features.py', 'r', encoding='utf-8') as f:
    patch_lines = f.readlines()

# Extract coin_js_block between line 194 and line 500
coin_js_lines = patch_lines[193:500]
coin_js = "".join(coin_js_lines).strip()

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Target insertion point: right before `</script>\n<script>\n/* Display size`
target = "</script>\n<script>\n/* Display size"
if target not in html_content:
    print("Error: target not found!")
    sys.exit(1)

if "window.buyDramaWithCoins" in html_content:
    print("Already contains window.buyDramaWithCoins!")
else:
    new_content = html_content.replace(target, "\n\n" + coin_js + "\n\n" + target, 1)
    with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully inserted coin_js into app/web/downloader.html!")
