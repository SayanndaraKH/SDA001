import requests, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check routes in lib-router.b116123e.js or homepage
r = requests.get('https://hongguoduanju.com/')
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', r.text)
for s in scripts:
    if not s.startswith('http'):
        continue
    txt = requests.get(s).text
    # look for route paths
    paths = re.findall(r'path:\s*["\']([^"\']+)["\']', txt)
    if paths:
        print(f"Paths in {s.split('/')[-1]}:", set(paths))
