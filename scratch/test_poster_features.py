import sys
import os
import time
import urllib.request
import json
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"

print("Starting SYD-8Movie server on port 8008...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.server:app", "--host", "127.0.0.1", "--port", "8008", "--log-level", "warning"],
    cwd=TARGET_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(3)

def api_get(path):
    url = f"http://127.0.0.1:8008{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()

def api_post(path, data):
    url = f"http://127.0.0.1:8008{path}"
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

try:
    print("--- 1. Testing /img proxy ---")
    img_data = api_get("/img?url=https://8movie.com/p/12978-kcho.jpg")
    print(f"Image proxy returned {len(img_data)} bytes (valid JPEG: {img_data[:2] == b'\xff\xd8'})")

    print("\n--- 2. Testing /api/catalog page 1 & 2 ---")
    d1 = json.loads(api_get("/api/catalog?cat=1&page=1").decode())
    print(f"Page 1 items: {d1.get('count')}")
    d2 = json.loads(api_get("/api/catalog?cat=1&page=2").decode())
    print(f"Page 2 items: {d2.get('count')}")
    if d2.get("items"):
        print("Page 2 item 1:", d2["items"][0]["title"])

    print("\n--- 3. Testing Batch Poster Download (3 dramas) ---")
    batch_res = api_post("/api/download/posters_batch", {
        "dramas": d1.get("items", [])[:3]
    })
    print("Batch submission:", batch_res)

    print("Waiting 4s for posters to download...")
    time.sleep(4)

    posters_gallery = os.path.join(os.path.expanduser("~"), "Videos", "SYD-8Movie", "Posters")
    if os.path.exists(posters_gallery):
        files = os.listdir(posters_gallery)
        print(f"Posters gallery folder ({posters_gallery}) has {len(files)} files:")
        for f in files:
            p = os.path.join(posters_gallery, f)
            print("  ", f, "=>", os.path.getsize(p), "bytes")
    else:
        print("Posters gallery folder not found yet")

finally:
    proc.terminate()
    print("\nServer terminated cleanly.")
