import sys, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('search_result.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("--- CONTENT AFTER NAV ---")
content = text[5000:]
print(content[:3000])
