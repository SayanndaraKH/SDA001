import os, re, json

filepath = 'app/access_manager.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace free_episodes default 10 -> 5
replacements = [
    ('"free_episodes": 10', '"free_episodes": 5'),
    ('"max_free_episodes": 10,', '"max_free_episodes": 5,'),
    ('user["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 10)', 'user["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 5)'),
    ('target["max_free_episodes"] = 10', 'target["max_free_episodes"] = 5'),
    ('su["max_free_episodes"] = 10', 'su["max_free_episodes"] = 5'),
    ('u["max_free_episodes"] = 10', 'u["max_free_episodes"] = 5'),
    ('s_user["max_free_episodes"] = 10', 's_user["max_free_episodes"] = 5'),
    ('def set_default_drama_rule(rule: str = "free_episodes", free_episodes: int = 10) -> dict:', 'def set_default_drama_rule(rule: str = "free_episodes", free_episodes: int = 5) -> dict:'),
    ('eps = 999999 if rule_type == "free_all" else max(1, int(free_episodes or 10))', 'eps = 999999 if rule_type == "free_all" else max(1, int(free_episodes or 5))'),
    ('default_rule = d.get("drama_rules_default", {"rule": "free_episodes", "free_episodes": 10})', 'default_rule = d.get("drama_rules_default", {"rule": "free_episodes", "free_episodes": 5})'),
    ('"free_episodes": default_rule.get("free_episodes", 10),', '"free_episodes": default_rule.get("free_episodes", 5),'),
    ('def set_drama_rule(series_id: str, rule: str = "free_episodes", free_episodes: int = 10, title: str = "") -> dict:', 'def set_drama_rule(series_id: str, rule: str = "free_episodes", free_episodes: int = 5, title: str = "") -> dict:'),
    ('d_rule = get_drama_rule(series_id) if series_id else {"rule": "free_episodes", "free_episodes": 10}', 'd_rule = get_drama_rule(series_id) if series_id else {"rule": "free_episodes", "free_episodes": 5}'),
    ('limit = d_rule.get("free_episodes", 10)', 'limit = d_rule.get("free_episodes", 5)'),
    ('u["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 10)', 'u["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 5)'),
    ('"max_free_episodes": 0 if banned else 10,', '"max_free_episodes": 0 if banned else 5,'),
    ('Regular user gets free access to episodes 1-10.', 'Regular user gets free access to episodes 1-5.'),
    ('episodes 1-10', 'episodes 1-5'),
    ('1-10 episodes', '1-5 episodes'),
    ('1-10 or custom', '1-5 or custom'),
    ('1 to 10', '1 to 5'),
    ('1-10', '1-5')
]

for old, new in replacements:
    content = content.replace(old, new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated app/access_manager.py successfully.")

# Also update user_access.json in app/ and in %LOCALAPPDATA%
for fpath in ['app/user_access.json', os.path.join(os.environ.get('LOCALAPPDATA', ''), 'HongguoDownloader', 'user_access.json')]:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            d = json.load(f)
        if 'drama_rules_default' in d:
            d['drama_rules_default']['free_episodes'] = 5
        for u in d.get('users', {}).values():
            if not u.get('is_admin') and not u.get('is_vip'):
                if u.get('max_free_episodes') == 10:
                    u['max_free_episodes'] = 5
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        print(f"Updated {fpath} successfully.")
