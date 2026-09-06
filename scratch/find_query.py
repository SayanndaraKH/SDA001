import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

js = requests.get('https://lf-fe.fqnovelstatic.com/obj/novel-fanqie-fe/growth/incentive-h5-monorepo/apps/hongguo/static/js/search.86347cb5.js').text
idx = 0
while True:
    idx = js.find('query', idx)
    if idx == -1:
        break
    start = max(0, idx - 150)
    end = min(len(js), idx + 150)
    print("--- MATCH AT", idx, "---")
    print(js[start:end])
    idx += 5
