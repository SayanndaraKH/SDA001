# -*- coding: utf-8 -*-
import subprocess, time, os, urllib.request, json

# 1. Save sample settings via Admin endpoint to test KHQR & Telegram links
admin_payload = {
    "pin": "8888",
    "token": "",
    "settings": {
        # A tiny sample 1x1 png data URI
        "khqr_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "telegram_admin": "https://t.me/syd_admin_support",
        "telegram_group": "https://t.me/syd_drama_community"
    }
}
req = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/admin/settings",
    data=json.dumps(admin_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
print("Save settings result:", res)

# 2. Register a test regular user if not exists
reg_payload = {
    "username": "soktest1",
    "name": "សុខ ពិសិដ្ឋ",
    "contact": "012888999",
    "password": "password123",
    "note": "User ធម្មតាសាកល្បង",
    "package": "",  # no VIP requested yet
    "device_id": "test_dev_001"
}
req_reg = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/register",
    data=json.dumps(reg_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
try:
    res_reg = json.loads(urllib.request.urlopen(req_reg).read().decode('utf-8'))
    print("Register user result:", res_reg.get('ok'), res_reg.get('error', ''))
except Exception as e:
    print("Register exception:", e)

# 3. Login as this regular user to get token
login_payload = {
    "identity": "soktest1",
    "password": "password123",
    "device_id": "test_dev_001"
}
req_login = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/login",
    data=json.dumps(login_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_login = json.loads(urllib.request.urlopen(req_login).read().decode('utf-8'))
user_token = res_login.get('token', '')
print("Login regular user token:", user_token[:15] + "...")

# 4. Check status of this user
req_stat = urllib.request.urlopen(f"http://127.0.0.1:8000/dl/access/status?token={user_token}")
user_stat = json.loads(req_stat.read().decode('utf-8'))
print("User status:", user_stat.get('status'), "is_vip:", user_stat.get('is_vip'), "role:", user_stat.get('role'))

# 5. Check Admin login
req_adm_login = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/login",
    data=json.dumps({"identity": "ADMIN", "password": "8888", "device_id": "admin_dev"}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_adm = json.loads(urllib.request.urlopen(req_adm_login).read().decode('utf-8'))
admin_token = res_adm.get('token', '')
print("Admin token:", admin_token[:15] + "...")

# 6. Test Admin list users
req_users = urllib.request.urlopen(f"http://127.0.0.1:8000/dl/access/admin/users?pin=8888&token={admin_token}")
users_data = json.loads(req_users.read().decode('utf-8'))
print("Admin users count:", len(users_data.get('users', [])), "vip_count:", users_data.get('vip_count'), "regular_count:", users_data.get('regular_count'))

# 7. Test Ban user
print("Testing banning user...")
ban_req = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/admin/ban",
    data=json.dumps({"pin": "8888", "token": admin_token, "target_id": "soktest1", "banned": True}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_ban = json.loads(urllib.request.urlopen(ban_req).read().decode('utf-8'))
print("Ban result:", res_ban)

# Verify banned user cannot login
req_login_banned = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/login",
    data=json.dumps(login_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_login_banned = json.loads(urllib.request.urlopen(req_login_banned).read().decode('utf-8'))
print("Login attempt for banned user ok:", res_login_banned.get('ok'), "error:", res_login_banned.get('error'))

# Unban user
print("Unbanning user...")
unban_req = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/admin/ban",
    data=json.dumps({"pin": "8888", "token": admin_token, "target_id": "soktest1", "banned": False}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_unban = json.loads(urllib.request.urlopen(unban_req).read().decode('utf-8'))
print("Unban result:", res_unban.get('ok'))

# 8. Test Approve VIP with custom days (e.g. 45 days)
print("Approving user with 45 custom days...")
app_req = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/admin/approve",
    data=json.dumps({"pin": "8888", "token": admin_token, "target_id": "soktest1", "package": "custom", "custom_days": 45}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_app = json.loads(urllib.request.urlopen(app_req).read().decode('utf-8'))
print("Approve result ok:", res_app.get('ok'), "package_name:", res_app.get('user', {}).get('package_name'), "expires_date:", res_app.get('user', {}).get('expires_date'))

# Verify user status now has 45 days left
# Re-login to get updated status
res_login2 = json.loads(urllib.request.urlopen(req_login).read().decode('utf-8'))
tok2 = res_login2.get('token')
req_stat2 = urllib.request.urlopen(f"http://127.0.0.1:8000/dl/access/status?token={tok2}")
user_stat2 = json.loads(req_stat2.read().decode('utf-8'))
print("User VIP active:", user_stat2.get('is_vip'), "days_left:", user_stat2.get('days_left'), "expires_date:", user_stat2.get('expires_date'))

# Demote / Revoke back to regular
rev_req = urllib.request.Request(
    "http://127.0.0.1:8000/dl/access/admin/revoke",
    data=json.dumps({"pin": "8888", "token": admin_token, "target_id": "soktest1"}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
res_rev = json.loads(urllib.request.urlopen(rev_req).read().decode('utf-8'))
print("Revoke result ok:", res_rev.get('ok'))

req_stat3 = urllib.request.urlopen(f"http://127.0.0.1:8000/dl/access/status?token={tok2}")
user_stat3 = json.loads(req_stat3.read().decode('utf-8'))
print("After revoke - is_vip:", user_stat3.get('is_vip'), "status:", user_stat3.get('status'))
