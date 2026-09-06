import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

js = requests.get('https://lf-fe.fqnovelstatic.com/obj/novel-fanqie-fe/growth/incentive-h5-monorepo/apps/hongguo/static/js/search.86347cb5.js').text
print('Length:', len(js))
urls = re.findall(r'https?://[^\s"\'<>]+', js)
print('URLs in search.js:', set(urls))
# Find string literals
paths = re.findall(r'["\'](/[a-zA-Z0-9_\-\/]+)["\']', js)
print('Paths:', set([p for p in paths if '/' in p and len(p) > 2]))

# Look for parameter names or query patterns
m = re.findall(r'(\w+)\s*:\s*(\w+)', js)
print('Sample props:', [f"{k}:{v}" for k, v in m if 'search' in k.lower() or 'query' in k.lower() or 'keyword' in k.lower()][:20])
