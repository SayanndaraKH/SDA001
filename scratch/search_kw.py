import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

js = requests.get('https://lf-fe.fqnovelstatic.com/obj/novel-fanqie-fe/growth/incentive-h5-monorepo/apps/hongguo/static/js/search.86347cb5.js').text

for target in ['searchList', 'totalCount', 'search_page', 'fetch', 'api', 'keyword', 'series_id']:
    idx = 0
    matches = 0
    while matches < 3:
        idx = js.find(target, idx)
        if idx == -1:
            break
        start = max(0, idx - 100)
        end = min(len(js), idx + 100)
        print(f"Target '{target}' at {idx}:")
        print(js[start:end])
        idx += len(target)
        matches += 1
