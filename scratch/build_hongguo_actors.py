import requests, re, json, sys, os, urllib.parse, concurrent.futures, time
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

def clean_url(u):
    if not u: return ""
    return u.replace('.heic', '.image') if '.heic' in u else u

# 1. Base list of core verified actors
CORE_NAMES = [
    # Stars from user's screenshot
    "王阡惠", "魏尊", "刘欣迪", "熊贤达", "陈传凯", "东东",
    "王玉芷", "温鑫阳", "张紫豪", "杨东峰", "刘厚辰", "田鹏",
    # Top trending stars on Hongguo
    "马秋元", "申浩男", "何健麒", "郭宇欣", "王皓祯", "白靖筠",
    "柯淳", "舒童", "钟熙", "白方文", "侯呈玥", "庞瀚辰",
    "徐梦洁", "余茵", "赵夕汐", "杨咩咩", "曾辉", "韩雨彤",
    "王道铁", "张楚萱", "岳鹏飞", "左一", "鹿单东", "白妍"
]

actors_map = {}

# 1. Fetch search profile from https://hongguoduanju.com/search/[name]
def fetch_from_search(name):
    url = f"https://hongguoduanju.com/search/{urllib.parse.quote(name)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            sk = data.get('loaderData', {}).get('search_(keyword)/page', {}).get('searchList', [])
            if sk and sk[0].get('user_info'):
                u = sk[0]['user_info']
                g_num = u.get('gender')
                gender = 'female' if g_num == 0 else ('male' if g_num == 1 else 'female')
                subs = u.get('subtitle_list', [])
                if '男演员' in subs: gender = 'male'
                elif '女演员' in subs: gender = 'female'

                dramas = []
                # item 0 video_list
                for v in sk[0].get('video_list', []):
                    sid = str(v.get('series_id') or '')
                    if sid:
                        dramas.append({
                            'series_id': sid,
                            'title': v.get('series_title') or '',
                            'cover': clean_url(v.get('series_cover') or ''),
                            'episode_cnt': int(v.get('episode_cnt') or 0),
                            'intro': v.get('series_intro') or ''
                        })
                # doc_type 23
                for it in sk[1:]:
                    vd = it.get('video_data')
                    if vd and isinstance(vd, dict):
                        sid = str(vd.get('series_id') or '')
                        if sid and not any(d['series_id'] == sid for d in dramas):
                            dramas.append({
                                'series_id': sid,
                                'title': vd.get('series_title') or it.get('name') or '',
                                'cover': clean_url(vd.get('series_cover') or ''),
                                'episode_cnt': int(vd.get('episode_cnt') or 0),
                                'intro': vd.get('series_intro') or ''
                            })

                return {
                    'name': name,
                    'gender': gender,
                    'avatar': clean_url(u.get('user_avatar') or ''),
                    'intro': u.get('description') or '',
                    'actor_id': str(u.get('actor_id') or ''),
                    'dramas_count': len(dramas),
                    'sample_drama': dramas[0]['title'] if dramas else '',
                    'sample_sid': dramas[0]['series_id'] if dramas else '',
                    'dramas': dramas
                }
    except Exception as ex:
        print(f"Error fetching search for {name}: {ex}")
    return None

print(f"Fetching {len(CORE_NAMES)} core stars from hongguoduanju.com...")
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
    results = list(ex.map(fetch_from_search, CORE_NAMES))
    for res in results:
        if res and res.get('name'):
            actors_map[res['name']] = res
            print(f"  ⭐ {res['name']} ({res['gender']}) -> {res['dramas_count']} dramas from hongguo")

# 2. Fetch dramas from homepage and category on hongguoduanju.com
print("\nFetching homepage & category dramas from hongguoduanju.com...")
home_sids = []
try:
    r_home = requests.get('https://hongguoduanju.com/', headers=HEADERS, timeout=12)
    m_h = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r_home.text)
    if m_h:
        d_h = json.loads(m_h.group(1))
        for s in d_h.get('loaderData', {}).get('page', {}).get('homeSections', []):
            for v in s.get('video_list', []):
                sid = v.get('series_id')
                t = v.get('series_title')
                if sid and (sid, t) not in home_sids:
                    home_sids.append((sid, t))
except Exception as e:
    print(f"Error fetching home: {e}")

print(f"Found {len(home_sids)} homepage dramas. Fetching cast details...")

def fetch_detail_cast(item):
    sid, title = item
    url = f"https://hongguoduanju.com/detail?series_id={sid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            d = json.loads(m.group(1))
            sd = d.get('loaderData', {}).get('detail_page', {}).get('seriesDetail', {})
            return (sid, title, sd.get('celebrities', []), sd.get('series_cover', ''))
    except Exception:
        pass
    return (sid, title, [], '')

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    detail_res = list(ex.map(fetch_detail_cast, home_sids))
    for sid, title, celebs, cover in detail_res:
        for c in celebs:
            name = (c.get('nickname') or '').strip()
            if not name: continue
            role = (c.get('sub_title') or '').replace('饰 ', '').strip()
            avatar = clean_url(c.get('avatar') or '')
            cid = str(c.get('celebrity_id') or '')

            if name in actors_map:
                if role and not actors_map[name].get('role'):
                    actors_map[name]['role'] = role
                if not actors_map[name].get('avatar') and avatar:
                    actors_map[name]['avatar'] = avatar
                if not any(d.get('series_id') == str(sid) for d in actors_map[name].get('dramas', [])):
                    actors_map[name]['dramas'].append({
                        'series_id': str(sid),
                        'title': title,
                        'cover': clean_url(cover),
                        'episode_cnt': 0
                    })
                    actors_map[name]['dramas_count'] = len(actors_map[name]['dramas'])
            else:
                # Infer gender
                is_female = any(k in role for k in ['小姐', '妈', '姨', '妻', '妹', '娘', '女', '妃', '夫人'])
                is_male = any(k in role for k in ['爷', '少', '总', '父', '哥', '帝', '弟', '皇', '生', '臣'])
                gender = 'female' if (is_female and not is_male) else ('male' if (is_male and not is_female) else 'female')

                actors_map[name] = {
                    'name': name,
                    'role': role,
                    'gender': gender,
                    'avatar': avatar,
                    'celebrity_id': cid,
                    'intro': f"演员 {name}，在《{title}》中饰演 {role}",
                    'dramas_count': 1,
                    'sample_drama': title,
                    'sample_sid': str(sid),
                    'dramas': [{
                        'series_id': str(sid),
                        'title': title,
                        'cover': clean_url(cover),
                        'episode_cnt': 0
                    }]
                }

final_list = list(actors_map.values())
# Sort so core actors and actors with photos come first
final_list.sort(key=lambda a: (0 if a['avatar'] else 1, -a['dramas_count']))

print(f"\n==========================================")
print(f"TOTAL ACTORS EXTRACTED FROM HONGGUO: {len(final_list)}")
print(f"Female: {sum(1 for a in final_list if a['gender']=='female')}")
print(f"Male: {sum(1 for a in final_list if a['gender']=='male')}")
print(f"With Avatars: {sum(1 for a in final_list if a['avatar'])}")

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, 'hongguo_actors.json')
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(final_list, f, ensure_ascii=False, indent=2)

print(f"Saved to {out_file}")
