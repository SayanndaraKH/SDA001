import urllib.request, re, sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://8movie.com/movies/1/2.html'
html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode('utf-8', 'ignore')
print('Page 2 HTML length:', len(html))
cards = re.findall(r'<a[^>]+href=[\'"]/movies/(\d+)[\'"][^>]*title=[\'"]([^\'"]+)[\'"]', html)
print('Page 2 cards count:', len(cards))
for did, title in cards[:5]:
    print('  ', did, title)
