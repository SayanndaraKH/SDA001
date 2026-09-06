import requests, re, json, sys, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'}

test_actors = ['王阡惠', '魏尊', '刘欣迪', '郭宇欣', '马秋元', '何健麒']

for a in test_actors:
    url = f'https://hongguoduanju.com/search/{urllib.parse.quote(a)}'
    try:
        r = requests.get(url, headers=headers, timeout=12)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            sk = data.get('loaderData', {}).get('search_(keyword)/page', {})
            slist = sk.get('searchList', [])
            total = sk.get('totalCount', len(slist))
            print(f"Actor '{a}' -> Total on hongguoduanju.com: {total}, fetched {len(slist)}")
            for item in slist[:2]:
                print(f"   🎬 {item.get('series_title')} (ID: {item.get('series_id')}, Eps: {item.get('episode_cnt')}) Cover: {item.get('series_cover')[:60]}...")
        else:
            print(f"Actor '{a}' -> No router data")
    except Exception as e:
        print(f"Error {a}: {e}")
