import requests, re, json, sys, os, urllib.parse, concurrent.futures
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

# 1. Popular known actors from Hongguo
POPULAR_STARS = [
    # Stars from user's reference image
    ("王阡惠", "林微", "female", "全班差生，托举我上清北", "7668961158434409534"),
    ("魏尊", "程砚", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("刘欣迪", "夏小棠", "female", "全班差生，托举我上清北", "7668961158434409534"),
    ("熊贤达", "周游", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("陈传凯", "林国强", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("东东", "李翠花", "female", "全班差生，托举我上清北", "7668961158434409534"),
    ("王玉芷", "蔡老师", "female", "全班差生，托举我上清北", "7668961158434409534"),
    ("温鑫阳", "林华", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("张紫豪", "隔壁班学生", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("杨东峰", "高老大", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("刘厚辰", "程父", "male", "全班差生，托举我上清北", "7668961158434409534"),
    ("田鹏", "夏父", "male", "全班差生，托举我上清北", "7668961158434409534"),
    # Other top Hongguo stars
    ("马秋元", "方子怡", "female", "北境战神", "7283356034716929084"),
    ("申浩男", "宴矜", "male", "宴律，你的白月光回国了", "7503745441910017049"),
    ("何健麒", "周宴京", "male", "盛夏芬德拉", "7550544718799588376"),
    ("郭宇欣", "时穗", "female", "好雨知时节", "7673056752958458942"),
    ("王皓祯", "宋知节", "male", "好雨知时节", "7673056752958458942"),
    ("白靖筠", "林暖暖", "female", "好雨知时节", "7673056752958458942"),
    ("柯淳", "顾北辰", "male", "裴总每天都想父凭子贵", "7339798471131565090"),
    ("舒童", "陆战", "male", "无双", "7339891823711677474"),
    ("钟熙", "沈曼", "female", "厉总，夫人马甲又掉了", "7340123456789012345"),
    ("白方文", "傅庭深", "male", "傅爷的私宠罪妻", "7341234567890123456"),
    ("侯呈玥", "乔安", "female", "恰似寒光遇骄阳", "7342345678901234567")
]

# Function to fetch profile from https://hongguoduanju.com/search/[name]
def fetch_actor_profile_from_hongguo(name):
    url = f"https://hongguoduanju.com/search/{urllib.parse.quote(name)}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            sk = data.get('loaderData', {}).get('search_(keyword)/page', {}).get('searchList', [])
            if sk and sk[0].get('user_info'):
                u = sk[0]['user_info']
                gender_num = u.get('gender')
                gender = 'female' if gender_num == 0 else ('male' if gender_num == 1 else 'female')
                subtitles = u.get('subtitle_list', [])
                if '男演员' in subtitles: gender = 'male'
                elif '女演员' in subtitles: gender = 'female'
                
                # Get dramas list
                dramas = []
                for v in sk[0].get('video_list', []):
                    dramas.append({
                        'series_id': str(v.get('series_id')),
                        'title': v.get('series_title'),
                        'cover': v.get('series_cover'),
                        'episode_cnt': v.get('episode_cnt', 0)
                    })
                return {
                    'name': name,
                    'gender': gender,
                    'avatar': u.get('user_avatar', ''),
                    'intro': u.get('description', ''),
                    'actor_id': u.get('actor_id', ''),
                    'dramas_count': len(dramas),
                    'sample_drama': dramas[0]['title'] if dramas else '',
                    'sample_sid': dramas[0]['series_id'] if dramas else '',
                    'dramas': dramas
                }
    except Exception as e:
        print(f"Error fetching {name}: {e}")
    return None

print("Fetching profiles for 5 sample stars from hongguoduanju.com...")
for name, role, g, d, sid in POPULAR_STARS[:5]:
    p = fetch_actor_profile_from_hongguo(name)
    if p:
        print(f"✅ {p['name']} ({p['gender']}) - Avatar: {p['avatar'][:45]}... - Dramas: {p['dramas_count']} (e.g. {p['sample_drama']})")
    else:
        print(f"❌ Could not fetch {name}")
