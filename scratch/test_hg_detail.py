import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

test_urls = [
    'https://hongguoduanju.com/detail?series_id=7673056752958458942',
    'https://hongguoduanju.com/play?series_id=7673056752958458942',
    'https://hongguoduanju.com/series/7673056752958458942',
    'https://hongguoduanju.com/drama?series_id=7673056752958458942',
]

for url in test_urls:
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"URL: {url} -> Status: {r.status_code}, len: {len(r.text)}")
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            loader = data.get('loaderData', {})
            print("  loaderData keys:", list(loader.keys()))
            page = loader.get('page', {})
            print("  page keys:", list(page.keys()))
            for pk, pv in page.items():
                if isinstance(pv, dict):
                    print(f"    page[{pk}] keys: {list(pv.keys())}")
                elif isinstance(pv, list):
                    print(f"    page[{pk}] len: {len(pv)}")
    except Exception as e:
        print(f"Error {url}: {e}")
