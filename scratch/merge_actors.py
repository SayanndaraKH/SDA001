import json

with open('scratch/actors_sample.json', 'r', encoding='utf-8') as f:
    sample = json.load(f)

extra = []
try:
    with open('scratch/extra_stars.json', 'r', encoding='utf-8') as f:
        extra = json.load(f)
except Exception:
    pass

for a in sample:
    if a['name'] == '王玉芷':
        a['gender'] = 'female'
    if a['name'] == '田鹏':
        a['gender'] = 'male'

all_actors = []
seen = set()
for a in sample + extra:
    if a['name'] not in seen:
        seen.add(a['name'])
        all_actors.append(a)

print(f"Combined unique actors: {len(all_actors)}")
with open('scratch/all_initial_actors.json', 'w', encoding='utf-8') as f:
    json.dump(all_actors, f, ensure_ascii=False, indent=2)
print("Saved all_initial_actors.json successfully!")
