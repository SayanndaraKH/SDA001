import urllib.request, re, sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0'}

for name, path in [('Home', '/'), ('Category 1', '/movies/1/'), ('Category 4', '/movies/4/'), ('Update', '/movies/update/'), ('Rank', '/movies/rank/')]:
    url = 'https://8movie.com' + path
    html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode('utf-8', 'ignore')
    cards = set(re.findall(r'/movies/(\d+)', html))
    print(f"{name:<12} ({path}): found {len(cards)} unique dramas")

# Check if there are scroll/load more endpoints or AJAX endpoints in javascript
ajax_urls = re.findall(r'[\'"](/[^"\'\s]+\.php[^"\'\s]*)[\'"]|[\'"](/api/[^"\'\s]*)[\'"]', html)
print("Any ajax or api endpoints in rank html:", ajax_urls)
