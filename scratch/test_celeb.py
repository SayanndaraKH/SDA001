import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
celeb_id = '7407367781366125849' # 郭宇欣
urls = [
    f'https://hongguoduanju.com/celebrity?celebrity_id={celeb_id}',
    f'https://hongguoduanju.com/celebrity/{celeb_id}',
    f'https://hongguoduanju.com/actor?celebrity_id={celeb_id}',
    f'https://hongguoduanju.com/search?keyword=郭宇欣',
    f'https://hongguoduanju.com/search?q=郭宇欣',
]
for u in urls:
    try:
        r = requests.get(u, headers=headers, timeout=10)
        print(f"URL: {u} -> Status: {r.status_code}, len: {len(r.text)}")
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            loader = data.get('loaderData', {})
            print("  loader keys:", list(loader.keys()))
    except Exception as e:
        print(f"Error {u}: {e}")
