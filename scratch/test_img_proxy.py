import os
import hashlib
import urllib.request

cache_dir = r"C:\Users\Administrator\Desktop\SYD-8Move\app\data\poster_cache"
os.makedirs(cache_dir, exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://8movie.com/'
}

def get_proxied_image(url: str):
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://8movie.com' + url
    
    # Hash for cache
    h = hashlib.md5(url.encode()).hexdigest() + '.jpg'
    cache_path = os.path.join(cache_dir, h)

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
        return cache_path, True

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
            if len(data) > 100:
                with open(cache_path, 'wb') as f:
                    f.write(data)
                return cache_path, False
    except Exception as e:
        print(f"Error caching {url}: {e}")
    return None, False

# Test with 3 posters
test_urls = [
    'https://8movie.com/p/12978-kcho.jpg',
    'https://8movie.com/p/12499-sjbj.jpg',
    '/p/13759-xaqq.jpg'
]

for u in test_urls:
    p, from_cache = get_proxied_image(u)
    print(f"URL: {u} -> Path: {p}, Cached: {from_cache}")
