import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
r = requests.get('https://hongguoduanju.com/search?query=郭宇欣', headers=headers)
print("Search with query=郭宇欣:")
m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
if m:
    data = json.loads(m.group(1))
    sp = data.get('loaderData', {}).get('search_page', {})
    print("query in sp:", sp.get('query'))
    print("totalCount:", sp.get('totalCount'))
    print("searchList len:", len(sp.get('searchList', [])))
    if sp.get('searchList'):
        print("First item:", json.dumps(sp['searchList'][0], ensure_ascii=False)[:300])

scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text)
for s in scripts:
    if not s.startswith('http'):
        continue
    print('Script:', s)
    js_text = requests.get(s, headers=headers).text
    api_matches = re.findall(r'["\'](/[^"\'\s]+api[^"\'\s]+)["\']', js_text)
    if api_matches:
        print('  api matches:', set(api_matches[:10]))
    kw_matches = re.findall(r'search\w*', js_text, re.I)
    print('  search occurrences:', len(kw_matches))
