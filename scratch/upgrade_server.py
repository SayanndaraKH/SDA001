import os

TARGET = r"C:\Users\Administrator\Desktop\SYD-8Move\app\server.py"

code = r'''# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import hashlib
import urllib.request
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Query, Body, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

# Relative imports within app package
try:
    from .scraper_8movie import (
        search_dramas, get_catalog, get_drama_detail, CATEGORIES
    )
    from .downloader import DownloaderManager
    from .translator import translate_to_khmer, translate_batch
except ImportError:
    from scraper_8movie import (
        search_dramas, get_catalog, get_drama_detail, CATEGORIES
    )
    from downloader import DownloaderManager
    from translator import translate_to_khmer, translate_batch

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, 'web')
DATA_DIR = os.path.join(HERE, 'data')
POSTER_CACHE_DIR = os.path.join(DATA_DIR, 'poster_cache')
CONFIG_FILE = os.path.join(HERE, 'config.json')

os.makedirs(POSTER_CACHE_DIR, exist_ok=True)

HEADERS_IMG = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://8movie.com/'
}

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "port": 8008,
        "host": "127.0.0.1",
        "output_dir": os.path.join(os.path.expanduser("~"), "Videos", "SYD-8Movie"),
        "max_concurrent_downloads": 3,
        "auto_translate": True,
        "theme": "dark"
    }

def save_config(cfg: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

cfg = load_config()

app = FastAPI(title="SYD-8Movie API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

downloader = DownloaderManager(
    output_dir=cfg.get("output_dir"),
    max_workers=cfg.get("max_concurrent_downloads", 3)
)

def _enrich_titles_with_khmer(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not cfg.get("auto_translate", True):
        return cards
    titles = [c.get("title", "") for c in cards if not c.get("title_km")]
    if titles:
        trans_map = translate_batch(titles[:40])
        for c in cards:
            if not c.get("title_km"):
                c["title_km"] = trans_map.get(c.get("title", ""), "")
    return cards

# ----------------- UI / Static Routes -----------------
@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
async def index():
    idx_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(idx_path):
        with open(idx_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h3>SYD 8Movie Downloader: index.html not found</h3>")

@app.get("/logo.png")
async def logo():
    p = os.path.join(WEB_DIR, "logo.png")
    if os.path.exists(p):
        return FileResponse(p, media_type="image/png")
    return JSONResponse({"error": "not found"}, status_code=404)

# ----------------- Poster Image Proxy -----------------
@app.get("/img")
async def proxy_image(url: str = Query(..., description="Image URL to proxy and cache")):
    raw = (url or '').strip()
    if not raw:
        return FileResponse(os.path.join(WEB_DIR, "logo.png"), media_type="image/png")

    if not raw.startswith("http"):
        raw = "https://8movie.com" + raw

    # Disk Cache check
    h = hashlib.md5(raw.encode()).hexdigest() + ".jpg"
    cache_path = os.path.join(POSTER_CACHE_DIR, h)

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
        return FileResponse(cache_path, media_type="image/jpeg", headers={"Cache-Control": "max-age=86400"})

    try:
        req = urllib.request.Request(raw, headers=HEADERS_IMG)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read()
            if len(data) > 100:
                with open(cache_path, "wb") as f:
                    f.write(data)
                return FileResponse(cache_path, media_type="image/jpeg", headers={"Cache-Control": "max-age=86400"})
    except Exception as e:
        pass

    # Fallback to local logo if image fails
    return FileResponse(os.path.join(WEB_DIR, "logo.png"), media_type="image/png")

# ----------------- API Endpoints -----------------
@app.get("/api/status")
async def get_status():
    st = downloader.get_status()
    return {
        "status": "online",
        "app": "SYD-8Movie Pro",
        "version": "1.0.0",
        "output_dir": downloader.output_dir,
        "active_downloads": st["active_count"],
        "queued_downloads": st["queued_count"],
        "completed_downloads": st["completed_count"]
    }

@app.get("/api/categories")
async def get_categories():
    return CATEGORIES

@app.get("/api/catalog")
async def api_catalog(cat: str = Query("1", description="Category ID"), page: int = Query(1, description="Page number")):
    cards = get_catalog(cat, page=page)
    cards = _enrich_titles_with_khmer(cards)
    return {"category": cat, "page": page, "count": len(cards), "items": cards}

@app.get("/api/search")
async def api_search(q: str = Query("", description="Search keyword"), page: int = Query(1, description="Page number")):
    cards = search_dramas(q, page=page)
    cards = _enrich_titles_with_khmer(cards)
    return {"query": q, "page": page, "count": len(cards), "items": cards}

@app.get("/api/rank")
async def api_rank(page: int = Query(1)):
    cards = get_catalog("rank", page=page)
    cards = _enrich_titles_with_khmer(cards)
    return {"category": "rank", "page": page, "count": len(cards), "items": cards}

@app.get("/api/latest")
async def api_latest(page: int = Query(1)):
    cards = get_catalog("update", page=page)
    cards = _enrich_titles_with_khmer(cards)
    return {"category": "update", "page": page, "count": len(cards), "items": cards}

@app.get("/api/episodes")
async def api_episodes(id: str = Query(..., description="Drama ID")):
    detail = get_drama_detail(id)
    if detail.get("title") and not detail.get("title_km"):
        detail["title_km"] = translate_to_khmer(detail["title"])
    return detail

@app.post("/api/download/episode")
async def download_episode(payload: Dict[str, Any] = Body(...)):
    drama_id = str(payload.get("drama_id", ""))
    drama_title = payload.get("drama_title", "")
    title_km = payload.get("title_km", "")
    ep_num = int(payload.get("ep_num", 1))
    hls_url = payload.get("hls_url", "")
    poster_url = payload.get("poster_url", "")

    if not hls_url:
        raise HTTPException(status_code=400, detail="Missing hls_url")

    tid = downloader.submit_episode(drama_id, drama_title, title_km, ep_num, hls_url, poster_url)
    return {"status": "queued", "task_id": tid}

@app.post("/api/download/poster")
async def download_poster(payload: Dict[str, Any] = Body(...)):
    drama_id = str(payload.get("drama_id", ""))
    drama_title = payload.get("drama_title", "")
    title_km = payload.get("title_km", "")
    poster_url = payload.get("poster_url", "")

    if not poster_url:
        raise HTTPException(status_code=400, detail="Missing poster_url")

    tid = downloader.submit_poster(drama_id, drama_title, title_km, poster_url)
    return {"status": "queued", "task_id": tid}

@app.post("/api/download/posters_batch")
async def download_posters_batch(payload: Dict[str, Any] = Body(...)):
    """Batch download posters for all dramas in the list"""
    dramas = payload.get("dramas", [])
    task_ids = []
    for d in dramas:
        did = str(d.get("id", ""))
        title = d.get("title", "")
        t_km = d.get("title_km", "")
        p_url = d.get("poster", "")
        if did and p_url:
            tid = downloader.submit_poster(did, title, t_km, p_url)
            task_ids.append(tid)
    return {"status": "queued", "count": len(task_ids), "task_ids": task_ids}

@app.post("/api/download/batch")
async def download_batch(payload: Dict[str, Any] = Body(...)):
    drama_id = str(payload.get("drama_id", ""))
    drama_title = payload.get("drama_title", "")
    title_km = payload.get("title_km", "")
    episodes = payload.get("episodes", [])
    poster_url = payload.get("poster_url", "")

    if not episodes:
        raise HTTPException(status_code=400, detail="No episodes provided")

    task_ids = downloader.submit_batch(drama_id, drama_title, title_km, episodes, poster_url)
    return {"status": "queued", "count": len(task_ids), "task_ids": task_ids}

@app.get("/api/download/status")
async def download_status():
    return downloader.get_status()

@app.post("/api/download/cancel")
async def cancel_download(payload: Dict[str, Any] = Body(...)):
    task_id = payload.get("task_id", "")
    downloader.cancel_task(task_id)
    return {"status": "cancelled", "task_id": task_id}

@app.post("/api/download/clear")
async def clear_downloads():
    downloader.clear_completed()
    return {"status": "cleared"}

@app.post("/api/open")
async def open_folder(payload: Dict[str, Any] = Body(default={})):
    path = payload.get("path")
    downloader.open_folder(path)
    return {"status": "opened", "path": path or downloader.output_dir}

@app.post("/api/play")
async def play_media(payload: Dict[str, Any] = Body(...)):
    file_path = payload.get("file_path", "")
    if file_path and os.path.exists(file_path):
        downloader.play_file(file_path)
        return {"status": "playing", "file_path": file_path}
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/api/config")
async def get_config():
    return cfg

@app.post("/api/config")
async def update_config(new_cfg: Dict[str, Any] = Body(...)):
    global cfg
    cfg.update(new_cfg)
    save_config(cfg)
    if "output_dir" in new_cfg:
        downloader.output_dir = new_cfg["output_dir"]
        os.makedirs(downloader.output_dir, exist_ok=True)
    if "max_concurrent_downloads" in new_cfg:
        downloader.max_workers = int(new_cfg["max_concurrent_downloads"])
    return cfg

@app.get("/api/library")
async def get_library():
    out_dir = downloader.output_dir
    items = []
    if os.path.exists(out_dir):
        for entry in os.listdir(out_dir):
            full_path = os.path.join(out_dir, entry)
            if os.path.isdir(full_path):
                files = os.listdir(full_path)
                mp4_files = [f for f in files if f.lower().endswith(".mp4")]
                posters = [f for f in files if f.lower().endswith((".jpg", ".png", ".webp"))]
                poster_path = os.path.join(full_path, posters[0]) if posters else ""
                items.append({
                    "folder_name": entry,
                    "folder_path": full_path,
                    "episodes_count": len(mp4_files),
                    "episodes": sorted(mp4_files),
                    "has_poster": bool(posters),
                    "poster_path": poster_path
                })
    return {"output_dir": out_dir, "count": len(items), "dramas": items}
'''

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated server.py with /img proxy and pagination.")
