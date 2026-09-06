import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import test_scraper as s


print('--- Test Category 1 ---')
cat1 = s.get_catalog('1')
print(f'Cat 1 total items: {len(cat1)}')
if cat1:
    print('Item 1:', cat1[0])

print('\n--- Test Search "狂野" ---')
search_res = s.search_dramas('狂野')
print(f'Search total items: {len(search_res)}')
if search_res:
    print('Item 1:', search_res[0])

print('\n--- Test Drama Detail 12978 ---')
detail = s.get_drama_detail('12978')
print('Title:', detail['title'])
print('Poster:', detail['poster'])
print('Tags:', detail['tags'])
print('Episodes count:', detail['episodes_count'])
if detail['episodes']:
    print('Ep 1:', detail['episodes'][0])
