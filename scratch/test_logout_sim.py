import subprocess, os, json, re

# Directly test by opening http://127.0.0.1:8000/
# Since syd_auth_token is empty in a fresh headless Chrome profile,
# it automatically tests the unauthenticated / logged out state!

chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
out_path = os.path.abspath('scratch/logout_mandatory_state.png')

cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--no-sandbox',
    '--virtual-time-budget=4000',
    '--window-size=1280,900',
    f'--screenshot={out_path}',
    'http://127.0.0.1:8000/'
]

subprocess.run(cmd, timeout=20)
print('Screenshot generated:', os.path.exists(out_path))
