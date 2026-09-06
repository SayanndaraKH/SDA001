import urllib.request, re, sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for cat in ['1', '4', '5', 'update', 'rank']:
    url = f'https://8movie.com/movies/{cat}/'
    html = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10).read().decode('utf-8', 'ignore')
    
    # Check all img tags with src or data-src or data-original
    srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    data_srcs = re.findall(r'<img[^>]+data-src=["\']([^"\']+)["\']', html)
    data_origs = re.findall(r'<img[^>]+data-original=["\']([^"\']+)["\']', html)
    
    p_srcs = [s for s in srcs if '/p/' in s]
    print(f"Cat {cat}: src={len(srcs)} (/p/={len(p_srcs)}), data-src={len(data_srcs)}, data-original={len(data_origs)}")

    # Let's inspect snippet of a few card blocks
    cards = re.findall(r'<div[^>]*class=["\'][^"\']*picsize[^"\']*["\'][^>]*>.*?</div>', html, re.DOTALL)
    print(f"  picsize blocks count: {len(cards)}")
    if cards:
        print("  Sample picsize block:\n   ", cards[0][:300].replace('\n', ' '))
