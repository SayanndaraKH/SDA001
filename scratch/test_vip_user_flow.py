import subprocess, os, json, urllib.request

# 1. Create or get regular test user
reg_payload = json.dumps({
    "username": "dara_test1",
    "name": "Sok Dara",
    "contact": "012888999",
    "password": "password123",
    "note": "Testing regular user flow",
    "package": "1_year",
    "device_id": "DEV-TEST-DARA-99"
}).encode('utf-8')

try:
    req = urllib.request.Request("http://127.0.0.1:8000/dl/access/register", data=reg_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        res_data = json.loads(resp.read().decode('utf-8'))
        print("Register response:", res_data.get('ok'))
except Exception as e:
    print("Register error or already exists:", e)

# 2. Login to get token
login_payload = json.dumps({
    "identity": "dara_test1",
    "password": "password123",
    "device_id": "DEV-TEST-DARA-99"
}).encode('utf-8')

req = urllib.request.Request("http://127.0.0.1:8000/dl/access/login", data=login_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    user_token = res.get('token')
    print("Logged in, token:", user_token)

# 3. Take screenshot of VIP request modal when loaded with this user token
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
out_path = os.path.abspath('scratch/regular_user_vip_modal.png')

# Open downloader with auth_token in URL
url = f"http://127.0.0.1:8000/?auth_token={user_token}"

# In headless Chrome, we evaluate opening the VIP modal
cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=5000',
    '--window-size=1280,1000',
    f'--screenshot={out_path}',
    url
]
subprocess.run(cmd, timeout=20)
print('Screenshot exists:', os.path.exists(out_path))
