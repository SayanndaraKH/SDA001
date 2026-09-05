# -*- coding: utf-8 -*-
import sys, urllib.request, json, time

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
FB_BASE = "https://syd-drama-default-rtdb.firebaseio.com"

print("=" * 70)
print("TESTING FIREBASE REALTIME DATABASE STARTUP CHECK & VIP WORKFLOW")
print("=" * 70)

# STEP 0: Clean up any old test license first
print("\n[Step 0] Cleaning test license...")
clean_req = urllib.request.Request(
    f"{BASE_URL}/dl/firebase/admin/delete",
    data=json.dumps({"pin": "8888", "device_id": "d1_c32730ad5cd271421a6c7d52bc81952e"}).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
try:
    with urllib.request.urlopen(clean_req) as resp:
        print("  Cleaned old license:", resp.read().decode('utf-8'))
except Exception as e:
    print("  Clean note:", e)

# STEP 1: Startup check - User PC opens app with NO account in Firebase
print("\n[Step 1] Startup Check: User PC opens app (no account in Firebase)")
status_req = urllib.request.Request(f"{BASE_URL}/dl/access/status")
with urllib.request.urlopen(status_req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    print(f"  Authenticated: {data.get('authenticated')}")
    print(f"  Has Firebase Account: {data.get('has_firebase_account')}")
    print(f"  Must Register: {data.get('must_register')}")
    print(f"  Role: {data.get('role')}")
    print(f"  Message: {data.get('message')}")
    assert data.get('authenticated') == False, "Must be unauthenticated"
    assert data.get('must_register') == True, "Must require registration"
    assert data.get('has_firebase_account') == False, "Must not have Firebase account"
    print("  => SUCCESS: Fresh User PC is forced to register as User ធម្មតា!")

# STEP 2: Register as User ធម្មតា (Free Tier 1-10)
print("\n[Step 2] User registers account as User ធម្មតា")
reg_payload = {
    "username": "sok_kheang168",
    "name": "សុខ ឃាង",
    "contact": "098765432",
    "password": "pass1688password",
    "note": "User PC regular registration test"
}
reg_req = urllib.request.Request(
    f"{BASE_URL}/dl/access/register",
    data=json.dumps(reg_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(reg_req) as resp:
    reg_res = json.loads(resp.read().decode('utf-8'))
    print(f"  Register OK: {reg_res.get('ok')}")
    user_token = reg_res.get('token')
    print(f"  User Token: {user_token}")
    assert reg_res.get('ok') == True, "Registration must succeed"

# Check User PC status after registration
status_req2 = urllib.request.Request(f"{BASE_URL}/dl/access/status?token={user_token}")
with urllib.request.urlopen(status_req2) as resp:
    u_data = json.loads(resp.read().decode('utf-8'))
    print(f"  Authenticated: {u_data.get('authenticated')}")
    print(f"  Role: {u_data.get('role')}")
    print(f"  Status: {u_data.get('status')}")
    print(f"  Is VIP: {u_data.get('is_vip')}")
    print(f"  Max Free Episodes: {u_data.get('max_free_episodes')}")
    assert u_data.get('authenticated') == True
    assert u_data.get('role') == "user"
    assert u_data.get('is_vip') == False
    assert u_data.get('max_free_episodes') == 10
    print("  => SUCCESS: User is now registered as User ធម្មតា (episodes 1-10 free)!")

# Check Firebase Realtime Database
fb_req = urllib.request.Request(f"{FB_BASE}/licenses/d1_c32730ad5cd271421a6c7d52bc81952e.json", headers={"User-Agent": "SYD-Test"})
with urllib.request.urlopen(fb_req) as resp:
    fb_data = json.loads(resp.read().decode('utf-8'))
    print(f"  Firebase Sync: Username={fb_data.get('username')}, Role={fb_data.get('role')}, VIP={fb_data.get('is_vip')}")
    assert fb_data.get('username') == "sok_kheang168"
    assert fb_data.get('is_vip') == False
    print("  => SUCCESS: Firebase Realtime Database received User ធម្មតា record!")

# STEP 3: User requests VIP package
print("\n[Step 3] User clicks 'ស្នើសុំ VIP' (Submits VIP Request)")
vip_req_payload = {
    "token": user_token,
    "package": "1_year",
    "name": "សុខ ឃាង",
    "contact": "098765432",
    "note": "សំណើសុំ VIP 1 ឆ្នាំ"
}
vip_req = urllib.request.Request(
    f"{BASE_URL}/dl/access/request-vip",
    data=json.dumps(vip_req_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(vip_req) as resp:
    vip_res = json.loads(resp.read().decode('utf-8'))
    print(f"  Request VIP OK: {vip_res.get('ok')}")
    assert vip_res.get('ok') == True

# Verify Firebase Realtime Database has pending_vip
with urllib.request.urlopen(fb_req) as resp:
    fb_data = json.loads(resp.read().decode('utf-8'))
    print(f"  Firebase Status: {fb_data.get('status')}, Requested Package: {fb_data.get('requested_package')}, Is VIP: {fb_data.get('is_vip')}")
    assert fb_data.get('status') == "pending_vip"
    assert fb_data.get('is_vip') == False
    print("  => SUCCESS: Firebase Realtime Database updated with pending_vip request!")

# STEP 4: ADMIN Approves VIP
print("\n[Step 4] ADMIN Approves VIP Request in Admin Panel")
appr_payload = {
    "pin": "8888",
    "device_id": "d1_c32730ad5cd271421a6c7d52bc81952e",
    "package": "1_year"
}
appr_req = urllib.request.Request(
    f"{BASE_URL}/dl/firebase/admin/approve",
    data=json.dumps(appr_payload).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(appr_req) as resp:
    appr_res = json.loads(resp.read().decode('utf-8'))
    print(f"  Admin Approve OK: {appr_res.get('ok')}")
    assert appr_res.get('ok') == True

# STEP 5: User PC checks status (Live VIP detection)
print("\n[Step 5] User PC polls status & detects ADMIN Approval")
with urllib.request.urlopen(status_req2) as resp:
    final_data = json.loads(resp.read().decode('utf-8'))
    print(f"  Is VIP: {final_data.get('is_vip')}")
    print(f"  Status: {final_data.get('status')}")
    print(f"  Package Badge: {final_data.get('package_badge')}")
    print(f"  Max Free Episodes: {final_data.get('max_free_episodes')}")
    assert final_data.get('is_vip') == True
    assert final_data.get('status') == "approved"
    assert final_data.get('max_free_episodes') == 999999
    print("  => SUCCESS: User PC is now VIP (Unlimited Episodes Unlocked)!")

# CLEANUP
print("\n[Cleanup] Cleaning up test license from Firebase...")
with urllib.request.urlopen(clean_req) as resp:
    print("  Deleted test license:", resp.read().decode('utf-8'))

print("\n" + "=" * 70)
print("ALL TESTS PASSED 100%! FULL WORKFLOW VERIFIED SUCCESSFULLY!")
print("=" * 70)
