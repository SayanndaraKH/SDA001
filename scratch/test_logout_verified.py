import sys, urllib.request, json
sys.stdout.reconfigure(encoding='utf-8')

# Login test_user_777
req = urllib.request.Request('http://127.0.0.1:8000/dl/access/login', 
    data=json.dumps({'identity': 'test_user_777', 'password': 'password123'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'})
res = json.loads(urllib.request.urlopen(req).read())
tok = res.get('token')
print('Logged in user:', res.get('user', {}).get('username'))

# Logout
req_logout = urllib.request.Request('http://127.0.0.1:8000/dl/access/logout', 
    data=json.dumps({'token': tok}).encode('utf-8'),
    headers={'Content-Type': 'application/json'})
res_logout = json.loads(urllib.request.urlopen(req_logout).read())
print('Logout response:', res_logout)

# Check status after logout
res_after = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8000/dl/access/status?token={tok}').read())
print('Status after logout:')
print('  authenticated:', res_after.get('authenticated'))
print('  must_login:', res_after.get('must_login'))
print('  role:', res_after.get('role'))
print('  username:', res_after.get('username'))
print('  status:', res_after.get('status'))
print('  package_name:', res_after.get('package_name'))
