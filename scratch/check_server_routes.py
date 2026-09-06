with open(r'C:\Users\Administrator\Desktop\SYD-8Move\app\server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
routes = re.findall(r'@app\.(get|post)\(["\']([^"\']+)["\']', text)
print("Routes found in SYD-8Move/app/server.py:")
for r in routes:
    print(" ", r)
