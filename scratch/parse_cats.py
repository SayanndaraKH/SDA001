import sys, urllib.request, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

url = 'https://8movie.com/movies/1/'
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode('utf-8', 'ignore')

links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
print("Total links on /movies/1/:", len(links))
for href, text in links:
    clean_text = re.sub(r'<[^>]+>', '', text).strip()
    if clean_text and any(k in href for k in ['/movies/', '/tag', '/rank', 'genre']):
        print(f"  {clean_text} -> {href}")
