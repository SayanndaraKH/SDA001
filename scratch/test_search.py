import sys, urllib.request, urllib.parse, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode('utf-8', 'ignore')
    except Exception as e:
        return f"ERROR: {e}"

# 1. Let's inspect nav links in home page sample
with open('8movie_sample.html', 'r', encoding='utf-8', errors='ignore') as f:
    home_html = f.read()

# Find navigation bar
nav = re.findall(r'<nav[^>]*>.*?</nav>', home_html, re.DOTALL)
if nav:
    print("Nav links:")
    for a in re.findall(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', nav[0]):
        text = re.sub(r'<[^>]+>', '', a[1]).strip()
        print(f"  {text} -> {a[0]}")

# Find search form in home page
forms = re.findall(r'<form[^>]*>.*?</form>', home_html, re.DOTALL)
print("\nForms found:", len(forms))
for f in forms:
    print(f[:400])

# Let's test search URLs:
# e.g. /search?q=..., /search/..., /?s=..., etc.
test_searches = [
    'https://8movie.com/search?q=%E7%8B%82%E9%87%8E', # 狂野
    'https://8movie.com/search/%E7%8B%82%E9%87%8E',
    'https://8movie.com/?s=%E7%8B%82%E9%87%8E',
    'https://8movie.com/movies/1/',
    'https://8movie.com/movies/2/',
]

print("\nTesting URLs:")
for u in test_searches:
    res = fetch(u)
    if "ERROR" in res:
        print(f"  {u} => {res}")
    else:
        title = re.findall(r'<title>(.*?)</title>', res)
        print(f"  {u} => OK (len={len(res)}, title={title})")
