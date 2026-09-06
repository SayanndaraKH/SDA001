import sys
import re
import json
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


with open('8movie_sample.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

title = re.findall(r'<title>(.*?)</title>', text, re.IGNORECASE)
print('Title:', title)

# Look for article or movie card patterns
# Often WordPress (e.g. DoPlay, Torovix, PsyPlay) or MacCMS or similar
articles = re.findall(r'<article[^>]*>.*?</article>', text, re.DOTALL)
print('Article count:', len(articles))

items = re.findall(r'class="[^"]*item[^"]*"', text, re.IGNORECASE)
print('item count:', len(items))

# Let's inspect some image tags and links
posters = re.findall(r'<img[^>]+src=[\'"]([^\'"]+)[\'"][^>]*>', text)
print('Sample images:', posters[:8])

# Let's find relative links
hrefs = re.findall(r'href=[\'"](/[^\'"#\?]+)[\'"]', text)
print('Unique relative links count:', len(set(hrefs)))
movie_hrefs = [h for h in set(hrefs) if not any(h.endswith(ext) for ext in ['.css', '.js', '.png', '.ico', '.jpg'])]
print('Sample links (up to 30):')
for h in sorted(movie_hrefs)[:30]:
    print(' ', h)

# Let's inspect snippet of html where /p/12978 appears
pos = text.find('/p/12978')
if pos != -1:
    print('\n--- Snippet around /p/12978 ---')
    print(text[max(0, pos-200):min(len(text), pos+400)])

