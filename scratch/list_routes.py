import sys, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('app/server.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Find FastAPI app routes: @app.get(...), @app.post(...)
routes = re.findall(r'@app\.(get|post|delete|put)\([\'"]([^\'"]+)[\'"]', text)
print(f"Total routes: {len(routes)}")
for r in routes:
    print(f"  {r[0].upper():<6} {r[1]}")
