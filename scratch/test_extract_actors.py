import requests, re, json, sys, concurrent.futures
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

r = requests.get('https://hongguoduanju.com/', headers=headers, timeout=12)
m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
sids = []
if m:
    data = json.loads(m.group(1))
    sections = data.get('loaderData', {}).get('page', {}).get('homeSections', [])
    for s in sections:
        for v in s.get('video_list', []):
            sid = v.get('series_id')
            title = v.get('series_title')
            if sid and (sid, title) not in sids:
                sids.append((sid, title))

print(f"Got {len(sids)} dramas from homepage")

def fetch_cast(item):
    sid, title = item
    url = f'https://hongguoduanju.com/detail?series_id={sid}'
    try:
        r = requests.get(url, headers=headers, timeout=8)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            d = json.loads(m.group(1))
            sd = d.get('loaderData', {}).get('detail_page', {}).get('seriesDetail', {})
            celebs = sd.get('celebrities', [])
            return (title, sid, celebs)
    except Exception as e:
        pass
    return (title, sid, [])

actors = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for title, sid, celebs in ex.map(fetch_cast, sids):
        print(f"Drama: {title} ({sid}) -> {len(celebs)} actors")
        for c in celebs:
            name = c.get('nickname')
            if name and name not in actors:
                actors[name] = {
                    'name': name,
                    'role': c.get('sub_title', '').replace('饰 ', ''),
                    'avatar': c.get('avatar', ''),
                    'celebrity_id': c.get('celebrity_id', ''),
                    'drama': title,
                    'sid': sid
                }

print(f"\nTotal unique actors extracted from homepage dramas: {len(actors)}")
for a in list(actors.values())[:10]:
    print(f"  🎭 {a['name']} ({a['role']}) - Drama: {a['drama']} - Avatar: {a['avatar'][:40]}...")
