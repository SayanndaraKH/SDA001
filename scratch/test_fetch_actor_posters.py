import requests, re, json, sys, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

def get_actor_dramas_from_hongguo_web(actor_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    url = f'https://hongguoduanju.com/search/{urllib.parse.quote(actor_name)}'
    r = requests.get(url, headers=headers, timeout=12)
    m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
    if not m:
        return []
    
    data = json.loads(m.group(1))
    slist = data.get('loaderData', {}).get('search_(keyword)/page', {}).get('searchList', [])
    dramas = []
    seen = set()

    for it in slist:
        # Check item0 video_list
        vlist = it.get('video_list', [])
        for v in vlist:
            sid = str(v.get('series_id') or '')
            if sid and sid not in seen:
                seen.add(sid)
                dramas.append({
                    'series_id': sid,
                    'title': v.get('series_title') or '',
                    'cover': v.get('series_cover') or '',
                    'episode_cnt': v.get('episode_cnt') or 0,
                    'category': ' / '.join([c.get('name') for c in v.get('category_list', []) if c.get('name')]),
                    'score': '8.2'
                })
        # Check doc_type 23
        vd = it.get('video_data')
        if vd and isinstance(vd, dict):
            sid = str(vd.get('series_id') or '')
            if sid and sid not in seen:
                seen.add(sid)
                dramas.append({
                    'series_id': sid,
                    'title': vd.get('series_title') or it.get('name') or '',
                    'cover': vd.get('series_cover') or '',
                    'episode_cnt': vd.get('episode_cnt') or 0,
                    'category': ' / '.join([c.get('name') for c in vd.get('category_list', []) if c.get('name')]),
                    'score': '8.1'
                })
    return dramas

for actor in ['王阡惠', '魏尊', '刘欣迪', '东东', '郭宇欣', '马秋元']:
    res = get_actor_dramas_from_hongguo_web(actor)
    print(f"Actor '{actor}' -> Found {len(res)} posters directly from hongguoduanju.com:")
    for d in res[:3]:
        print(f"   🎬 {d['title']} ({d['episode_cnt']} ភាគ) - Poster: {d['cover'][:50]}...")
