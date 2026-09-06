import sys, urllib.request, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = 'https://8movie.com/movies/1/'
html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10).read().decode('utf-8', 'ignore')

# Find cat menu
matches = re.findall(r'<a[^>]+href=["\'](/movies/(\d+)/?)["\'][^>]*>(.*?)</a>', html)
cats = []
for full_href, cid, label in matches:
    clean_label = re.sub(r'<[^>]+>', '', label).strip()
    if clean_label and (cid, clean_label) not in cats:
        cats.append((cid, clean_label))

# Find pagination
pagers = re.findall(r'href=["\'](/movies/1/[^"\']+)["\']', html)
print("Page links on /movies/1/:", set(pagers))

# Check page 2
url2 = 'https://8movie.com/movies/1/page/2/'
try:
    html2 = urllib.request.urlopen(urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10).read().decode('utf-8', 'ignore')
    print("Page 2 length:", len(html2))
except Exception as e:
    print("Page 2 error:", e)

url2_alt = 'https://8movie.com/movies/1/2/'
try:
    html2_alt = urllib.request.urlopen(urllib.request.Request(url2_alt, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10).read().decode('utf-8', 'ignore')
    print("Page 2 alt length:", len(html2_alt))
except Exception as e:
    print("Page 2 alt error:", e)

