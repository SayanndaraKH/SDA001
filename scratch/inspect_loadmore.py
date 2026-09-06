import urllib.request, re, sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0'}
html = urllib.request.urlopen(urllib.request.Request('https://8movie.com/movies/1/', headers=headers), timeout=10).read().decode('utf-8', 'ignore')

# Find all scripts mentioning loadmore or pagemore
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i, s in enumerate(scripts):
    if 'loadmore' in s or 'pagemore' in s or 'load=' in s:
        print(f"--- Script {i} ---")
        print(s[:1500])
        print("...")

# Also look for external js files
srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
print("External scripts:", srcs)
