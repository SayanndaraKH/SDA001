import subprocess, time

# Run chrome with a tiny script or clip
cmd = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--headless=new",
    "--screenshot=C:\\Users\\Administrator\\.gemini\\antigravity-ide\\brain\\aff77dff-1d57-4946-9200-ffdc4d0aaa00\\footer_verified.png",
    "--window-size=1440,3600",
    "--virtual-time-budget=5000",
    "http://127.0.0.1:8000/?nomodal=1"
]
p = subprocess.run(cmd, capture_output=True)
print("Finished. Code:", p.returncode)
