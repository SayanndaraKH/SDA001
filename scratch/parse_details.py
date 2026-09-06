import sys
import re

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=== Analyzing movies_12978.html ===")
with open('movies_12978.html', 'r', encoding='utf-8', errors='ignore') as f:
    text1 = f.read()

# Look for title, poster, tags, description, episode buttons/links
print("Title:", re.findall(r'<h1[^>]*>(.*?)</h1>', text1))
print("Posters:", re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"]', text1)[:5])
print("Episode links (first 10):", re.findall(r'href=[\'"](/play/[^\'"#\?]+)[\'"]', text1)[:10])

print("\n=== Analyzing play_12978.html ===")
with open('play_12978.html', 'r', encoding='utf-8', errors='ignore') as f:
    text2 = f.read()

# Look for video tag, iframe, scripts with m3u8 or player config
print("Video tags:", re.findall(r'<video[^>]*>.*?</video>', text2, re.DOTALL))
print("Iframes:", re.findall(r'<iframe[^>]*>.*?</iframe>', text2, re.DOTALL | re.IGNORECASE))
print("Any iframe src:", re.findall(r'<iframe[^>]+src=[\'"]([^\'"]+)[\'"]', text2, re.IGNORECASE))

# Look for m3u8, mp4, player scripts
m3u8s = re.findall(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', text2)
print("m3u8 occurrences:", m3u8s)

mp4s = re.findall(r'https?://[^\s\'"]+\.mp4[^\s\'"]*', text2)
print("mp4 occurrences:", mp4s)

# Look for script blocks
scripts = re.findall(r'<script[^>]*>(.*?)</script>', text2, re.DOTALL)
print("Total scripts:", len(scripts))
for i, s in enumerate(scripts):
    if any(k in s for k in ['player', 'url', 'video', 'source', 'play', 'Hls', 'dp', 'art']):
        print(f"\n--- Script {i} ---")
        print(s.strip()[:600])
