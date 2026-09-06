import sys
import os
import time
import urllib.request
import json
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"
sys.path.insert(0, TARGET_DIR)

# 1. Start server in background subprocess
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
        return json.loads(r.read().decode('utf-8'))

def api_post(path, data):
    url = f"http://127.0.0.1:8008{path}"
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

try:
    print("--- 1. Testing /api/status ---")
    st = api_get("/api/status")
    print("Status:", st)

    print("\n--- 2. Testing /api/categories ---")
    cats = api_get("/api/categories")
    print(f"Categories count: {len(cats)}")

    print("\n--- 3. Testing /api/catalog?cat=1 ---")
    cat_items = api_get("/api/catalog?cat=1")
    print(f"Catalog items count: {cat_items.get('count')}")
    if cat_items.get("items"):
        item0 = cat_items["items"][0]
        print("Sample Item:", item0["title"], "-> Khmer:", item0.get("title_km"))

    print("\n--- 4. Testing /api/episodes?id=12978 ---")
    detail = api_get("/api/episodes?id=12978")
    print("Drama Detail:", detail["title"], "Episodes:", detail["episodes_count"])
    print("Poster:", detail["poster"])
    if detail["episodes"]:
        print("Ep 1:", detail["episodes"][0])

    print("\n--- 5. Testing Poster Download ---")
    post_res = api_post("/api/download/poster", {
        "drama_id": "12978",
        "drama_title": detail["title"],
        "title_km": detail.get("title_km", ""),
        "poster_url": detail["poster"]
    })
    print("Poster download submitted:", post_res)

    # Wait 2 seconds and check status
    time.sleep(2)
    dl_status = api_get("/api/download/status")
    print("Download Status:", dl_status["active_count"], "active,", dl_status["completed_count"], "completed")

    print("\n--- 6. Testing Episode 1 Download ---")
    ep1 = detail["episodes"][0]
    ep_res = api_post("/api/download/episode", {
        "drama_id": "12978",
        "drama_title": detail["title"],
        "title_km": detail.get("title_km", ""),
        "ep_num": 1,
        "hls_url": ep1["hls_url"],
        "poster_url": detail["poster"]
    })
    print("Episode download submitted:", ep_res)

    print("Waiting 10s for download to complete...")
    for i in range(12):
        time.sleep(1)
        dl_status = api_get("/api/download/status")
        tasks = dl_status["tasks"]
        ep_task = next((t for t in tasks if t["ep_num"] == 1), None)
        if ep_task:
            print(f"  Sec {i+1}: status={ep_task['status']}, size={ep_task.get('size_mb')} MB, speed={ep_task.get('speed')}")
            if ep_task["status"] == "completed":
                print("  => Download completed successfully!")
                break

    print("\n--- 7. Testing /api/library ---")
    lib = api_get("/api/library")
    print("Library dramas:", lib.get("count"))
    if lib.get("dramas"):
        print("First Drama Folder:", lib["dramas"][0])

finally:
    proc.terminate()
    print("\nServer terminated cleanly.")
