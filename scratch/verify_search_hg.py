import requests, re, json, sys, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'}

for a in ['王阡惠', '魏尊', '郭宇欣']:
    url = f'https://hongguoduanju.com/search/{urllib.parse.quote(a)}'
    r = requests.get(url, headers=headers, timeout=12)
    m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
    if m:
        data = json.loads(m.group(1))
        sk = data.get('loaderData', {}).get('search_(keyword)/page', {})
        slist = sk.get('searchList', [])
        print(f"=== Actor: {a} (Found {len(slist)}) ===")
        for it in slist[:3]:
            print(f"  Title: {it.get('series_title')}")
            print(f"  ID: {it.get('series_id')}")
            print(f"  Cover: {it.get('series_cover')}")
            print(f"  Eps: {it.get('episode_cnt')}")
