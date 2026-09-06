import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}
url = 'https://hongguoduanju.com/detail?series_id=7673056752958458942'
r = requests.get(url, headers=headers, timeout=15)
m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
if m:
    data = json.loads(m.group(1))
    loader = data.get('loaderData', {})
    detail_page = loader.get('detail_page', {})
    print("detail_page keys:", list(detail_page.keys()))
    for k, v in detail_page.items():
        if isinstance(v, (dict, list)):
            print(f"  {k}: {type(v)} -> sample: {json.dumps(v, ensure_ascii=False)[:200]}")
        else:
            print(f"  {k}: {v}")
