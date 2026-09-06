import sys, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app/web/downloader.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("File length:", len(text))
# Find main sections or views
sections = re.findall(r'<section[^>]+id=["\']([^"\']+)["\']', text)
print("Section IDs:", sections)
div_ids = re.findall(r'<div[^>]+id=["\']([^"\']+)["\']', text)
print("Div IDs (first 30):", div_ids[:30])

# Find title or headers
headers = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', text)
print("H1-H3 headers (sample):", [re.sub(r'<[^>]+>', '', h).strip() for h in headers[:15]])

# Look for JavaScript functions in downloader.html
funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)
print("JS functions count:", len(funcs))
print("Sample JS functions:", funcs[:30])
