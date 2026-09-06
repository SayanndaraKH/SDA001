import requests, re, json, sys, os, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

def test_actor_search(actor_name):
    # Load actors
    data_file = os.path.join('data', 'hongguo_actors.json')
    actors = []
    actor_map = {}
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            actors = json.load(f)
            actor_map = {a['name']: a for a in actors}
    
    actor_obj = actor_map.get(actor_name)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    items = []
    seen = set()
    
    # 1. Pre-cached dramas for this actor
    if actor_obj and actor_obj.get('dramas'):
        for d in actor_obj['dramas']:
            sid = str(d.get('series_id') or '')
            if sid and sid not in seen:
                seen.add(sid)
                items.append({
                    'series_id': sid,
                    'title': d.get('title') or '',
                    'cover': d.get('cover') or '',
                    'episode_cnt': d.get('episode_cnt') or 0,
                    'score': '8.3',
                    'category': f"តួអង្គ: {actor_obj.get('role', 'តួឯក')}"
                })
                
    # 2. Live search on hongguoduanju.com
    try:
        url = f'https://hongguoduanju.com/search/{urllib.parse.quote(actor_name)}'
        r = requests.get(url, headers=headers, timeout=8)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            sk = data.get('loaderData', {}).get('search_(keyword)/page', {}).get('searchList', [])
            for it in sk:
                for v in it.get('video_list', []):
                    sid = str(v.get('series_id') or '')
                    if sid and sid not in seen:
                        seen.add(sid)
                        items.append({
                            'series_id': sid,
                            'title': v.get('series_title') or '',
                            'cover': v.get('series_cover') or '',
                            'episode_cnt': int(v.get('episode_cnt') or 0),
                            'score': '8.2'
                        })
                vd = it.get('video_data')
                if vd and isinstance(vd, dict):
                    sid = str(vd.get('series_id') or '')
                    if sid and sid not in seen:
                        seen.add(sid)
                        items.append({
                            'series_id': sid,
                            'title': vd.get('series_title') or it.get('name') or '',
                            'cover': vd.get('series_cover') or '',
                            'episode_cnt': int(vd.get('episode_cnt') or 0),
                            'score': '8.1'
                        })
    except Exception as e:
        print("Live search error:", e)
        
    return items

results = test_actor_search('王阡惠')
print(f"Total posters for 王阡惠: {len(results)}")
for r in results[:5]:
    print(f"  🎬 {r['title']} (sid: {r['series_id']}, eps: {r['episode_cnt']})")
