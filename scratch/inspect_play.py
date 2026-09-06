import sys, re
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('play_12978.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

for m in re.finditer(r'https?://[^\s\'"]+\.mp4', text):
    start = max(0, m.start() - 150)
    end = min(len(text), m.end() + 150)
    print('Context around mp4:')
    print(repr(text[start:end]))
    break

# Find title and meta
for tag in ['title', 'h1', 'h2']:
    print(f"{tag}:", re.findall(rf'<{tag}[^>]*>(.*?)</{tag}>', text, re.I))

# Find breadcrumbs or drama title
breadcrumbs = re.findall(r'<ol[^>]*breadcrumb[^>]*>.*?</ol>', text, re.DOTALL | re.I)
print("breadcrumbs:", breadcrumbs)

# Check movie details in play page
print("Meta tags:")
for m in re.findall(r'<meta[^>]+>', text):
    if any(k in m for k in ['title', 'description', 'og:']):
        print(" ", m)
