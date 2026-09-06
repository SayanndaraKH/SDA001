import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}
r = requests.get('https://hongguoduanju.com/', headers=headers, timeout=15)
m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
if m:
    data = json.loads(m.group(1))
    page = data['loaderData']['page']
    sections = page.get('homeSections', [])
    for s in sections:
        print('Section:', s.get('tab_name'), len(s.get('video_list', [])))
        if s.get('video_list'):
            sample = s['video_list'][0]
            print('Keys in video:', list(sample.keys()))
            print('Sample video:', json.dumps(sample, ensure_ascii=False))

# Look for detail page URLs
detail_urls = re.findall(r'https?://hongguoduanju\.com[^\s"\'<>]+', r.text)
print('Detail URLs on homepage:', set(detail_urls))

# Also search for script src
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text)
print('Script count:', len(scripts))
for s in scripts[:5]:
    print('Script:', s)
