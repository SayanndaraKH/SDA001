"""Direct FastAPI Service for Hongguo Short Drama / Novel API.
Connects directly to the original website (api5-normal-sinfonlinec.fqnovel.com)
without requiring any License Key, Supabase verification, or API Key tokens.
"""

import os
import sys
import time
import socket
import subprocess
import threading
import re
from typing import Optional, List, Dict, Any
from urllib.parse import quote as url_quote

# Configure environment for direct operation
os.environ.setdefault('HG_LICENSE_DISABLED', '1')
os.environ.setdefault('SIGN_SERVER', 'http://127.0.0.1:9099')
os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(ROOT, 'app')
FRIDA = os.path.join(APP, 'frida')
SIGN_DIR = os.path.join(APP, 'sign')
JAVA = os.path.join(ROOT, 'jre', 'bin', 'java.exe')
DEFAULT_OUT = os.path.join(os.path.expanduser('~'), 'Videos', 'Hongguo')
STREAM_CACHE = os.path.join(ROOT, 'downloads', '.stream_cache')

if APP not in sys.path:
    sys.path.insert(0, APP)
if FRIDA not in sys.path:
    sys.path.insert(0, FRIDA)

import urllib3
urllib3.disable_warnings()

from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Import core business logic from app
import hongguo as H
import offline_dl as ODL
import offline_decrypt as OD
try:
    import translator as TR
    HAS_TRANSLATOR = True
except Exception:
    HAS_TRANSLATOR = False

# Ensure local signer is available
_signer_proc = None

def _is_port_open(port: int, host: str = '127.0.0.1') -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0

def ensure_signer():
    """Ensure the unidbg offline signer is running on port 9099."""
    global _signer_proc
    sign_port = 9099
    if _is_port_open(sign_port):
        return True
    
    jar_path = os.path.join(SIGN_DIR, 'unidbg-sign.jar')
    if os.path.exists(JAVA) and os.path.exists(jar_path):
        try:
            print(f"[direct_fastapi] Starting offline signer on port {sign_port}...")
            cmd = [
                JAVA,
                '-Xmx512m',
                '-XX:+ExitOnOutOfMemoryError',
                '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
                '-cp', 'unidbg-sign.jar',
                'com.hongguo.sign.FqTrace',
                'serve', str(sign_port)
            ]
            flags = 0x08000000 if sys.platform.startswith('win') else 0  # CREATE_NO_WINDOW
            _signer_proc = subprocess.Popen(cmd, cwd=SIGN_DIR, creationflags=flags)
            
            # Wait up to 15 seconds for signer port to open
            t0 = time.time()
            while time.time() - t0 < 15:
                if _is_port_open(sign_port):
                    print(f"[direct_fastapi] Offline signer is ready on port {sign_port}!")
                    return True
                time.sleep(0.5)
        except Exception as e:
            print(f"[direct_fastapi] Warning: Failed to auto-launch signer: {e}")
    return _is_port_open(sign_port)

# Decryption cache lock
_dec_locks: Dict[str, threading.Lock] = {}
_dec_guard = threading.Lock()

def _get_dec_lock(key: str) -> threading.Lock:
    with _dec_guard:
        return _dec_locks.setdefault(key, threading.Lock())

def _vm_track(vid: str, quality: str = 'best'):
    """Fetch track details (URL, spade_a, encryption status) from original site."""
    vm = ODL._video_model(vid)
    if not vm:
        return None
    tracks = vm.get('video_list') if isinstance(vm, dict) else vm
    tr, defn, _ = ODL._pick_track(tracks, quality)
    if not tr:
        return None
    enc = tr.get('encrypt_info') or {}
    meta = tr.get('video_meta') or {}
    return {
        'url': tr.get('main_url'),
        'spade_a': enc.get('spade_a'),
        'encrypt': bool(enc.get('encrypt')),
        'definition': meta.get('definition') or defn,
        'size': meta.get('size', 0)
    }

def _ensure_decrypted(vid: str, quality: str = 'best') -> str:
    """Download encrypted CDN video and decrypt locally into a clean MP4."""
    os.makedirs(STREAM_CACHE, exist_ok=True)
    safe_q = re.sub(r'[^\w]', '', str(quality)) or 'best'
    safe_vid = re.sub(r'[^\w.\-]', '_', str(vid)) or 'vid'
    out = os.path.join(STREAM_CACHE, f'{safe_vid}_{safe_q}.mp4')
    
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
        
    with _get_dec_lock(f'{vid}_{safe_q}'):
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return out
        
        t = _vm_track(vid, quality)
        if not t or not t.get('url'):
            raise HTTPException(404, detail='No video stream found on original server')
            
        if not t['encrypt']:
            H.download_file(t['url'], out)
            return out
        else:
            ct = out + '.enc'
            H.download_file(t['url'], ct)
            r = OD.offline_decrypt(t['spade_a'], ct, out)
            try:
                os.remove(ct)
            except OSError:
                pass
            if not (r and os.path.exists(out) and os.path.getsize(out) > 0):
                raise HTTPException(500, detail='Offline decryption failed')
            return out

# Download queue & worker
_dl_state = {'running': False, 'log': [], 'series': {}, 'started': 0}
_dl_lock = threading.Lock()

def _dl_log(m: str):
    with _dl_lock:
        _dl_state['log'].append(f"{time.strftime('%H:%M:%S')} {m}")
        _dl_state['log'] = _dl_state['log'][-100:]

def _run_download_job(series_ids: List[str], ranges: Dict[str, str], quality: str, concurrency: int):
    with _dl_lock:
        _dl_state['running'] = True
        _dl_state['started'] = int(time.time())
        _dl_state['log'] = []
        _dl_state['series'] = {}
    
    ODL.CANCEL.clear()
    out_dir = os.environ.get('HG_OUT', DEFAULT_OUT)
    os.makedirs(out_dir, exist_ok=True)
    
    _dl_log(f"Starting direct download of {len(series_ids)} series to {out_dir}")
    try:
        final_list = []
        for sid in series_ids:
            try:
                meta, eps = H.get_episodes(sid)
                title = meta.get('title', sid)
                rng = ranges.get(sid, 'all')
                sel = [e for e in eps or [] if ODL._match_range(rng, e.get('index') or 0)]
                final_list.append(sid)
                with _dl_lock:
                    _dl_state['series'][sid] = {
                        'title': title,
                        'total': len(sel),
                        'range': rng,
                        'status': 'downloading'
                    }
                _dl_log(f"+ Added: {title} ({len(sel)} episodes, range: {rng})")
            except Exception as ex:
                _dl_log(f"x Failed to prepare series {sid}: {ex}")

        if final_list:
            ODL.dl_batch(
                final_list,
                concurrency=concurrency,
                retry_rounds=2,
                quality=quality,
                ranges=ranges
            )
            _dl_log("Download finished successfully!")
        else:
            _dl_log("No valid series to download")
    except Exception as e:
        _dl_log(f"Download error: {e}")
    finally:
        with _dl_lock:
            _dl_state['running'] = False

# Initialize FastAPI App
app = FastAPI(
    title="Hongguo Direct API (No License Key)",
    description="Direct FastAPI connection to official ByteDance Hongguo API without License Key restrictions",
    version="2.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    threading.Thread(target=ensure_signer, daemon=True).start()

@app.get("/", tags=["System"])
def api_index():
    return {
        "service": "Hongguo Direct FastAPI (No License Key)",
        "upstream_host": H.HOST,
        "license_mode": "Permanent Unlimited (Direct Bypass)",
        "status": "online",
        "docs_url": "/docs",
        "endpoints": {
            "search": "/api/search?q={query}&limit=20",
            "rank": "/api/rank?board={recommend|hot|new}&category={all|human|comic|ai}",
            "latest": "/api/latest?genre={short_play|comic_series|ai_series}",
            "filters": "/api/filters?genre=short_play",
            "browse": "/api/browse?genre=ai_series&sort=online_time",
            "episodes": "/api/episodes?series_id={id}",
            "video_url": "/api/video_url?vid={vid}&quality=1080p",
            "play": "/api/play?series_id={id}&ep=1-5",
            "stream": "/api/stream?series_id={id}&ep=1 or ?vid={vid}",
            "download": "POST /api/download",
            "download_status": "/api/download/status",
            "system_status": "/api/status"
        }
    }

@app.get("/api/status", tags=["System"])
def api_status():
    signer_ok = _is_port_open(9099)
    out_dir = os.environ.get('HG_OUT', DEFAULT_OUT)
    return {
        "ok": True,
        "signer_ready": signer_ok,
        "signer_server": os.environ.get('SIGN_SERVER', 'http://127.0.0.1:9099'),
        "upstream_api": H.HOST,
        "license_required": False,
        "unlimited_access": True,
        "output_directory": out_dir,
        "has_khmer_translator": HAS_TRANSLATOR
    }

@app.get("/api/search", tags=["Content"])
def api_search(
    q: str = Query(..., description="Drama title or keyword to search"),
    limit: int = Query(20, ge=1, le=40, description="Max results")
):
    """Search short dramas directly from original Hongguo API."""
    ensure_signer()
    try:
        res = H.search(q, max_items=limit) or []
        km_map = {}
        if HAS_TRANSLATOR and res:
            try:
                titles = [x.get('title', '') for x in res if x.get('title')]
                km_map = TR.translate_batch(titles)
            except Exception:
                pass
        
        results = []
        for x in res:
            item = dict(x)
            if km_map.get(item.get('title')):
                item['title_km'] = km_map[item['title']]
            results.append(item)
            
        return {"query": q, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(500, detail=f"Search failed: {e}")

@app.get("/api/rank", tags=["Content"])
def api_rank(
    board: str = Query("recommend", description="Board: recommend, hot, new"),
    category: str = Query("all", description="Category: all, human, comic, ai"),
    offset: int = Query(0, ge=0, description="Page offset"),
    size: int = Query(50, ge=1, le=100, description="Number of items")
):
    """Get real-time leaderboard directly from original API."""
    ensure_signer()
    cat = category if category in ['all', 'human', 'comic', 'ai'] else 'all'
    brd = board if board in ['recommend', 'hot', 'new'] else 'recommend'
    try:
        items, has_more, next_off = H.leaderboard_page(cat, brd, offset=offset, size=size)
        km_map = {}
        if HAS_TRANSLATOR and items:
            try:
                titles = [x.get('title', '') for x in items if x.get('title')]
                km_map = TR.translate_batch(titles)
            except Exception:
                pass

        results = []
        for x in items:
            item = dict(x)
            if km_map.get(item.get('title')):
                item['title_km'] = km_map[item['title']]
            results.append(item)

        return {
            "board": brd,
            "category": cat,
            "has_more": has_more,
            "next_offset": next_off,
            "count": len(results),
            "items": results
        }
    except Exception as e:
        raise HTTPException(500, detail=f"Rank retrieval failed: {e}")

@app.get("/api/latest", tags=["Content"])
def api_latest(
    genre: str = Query("short_play", description="Genre: short_play, comic_series, ai_series"),
    only_today: bool = Query(True, description="Only today's releases"),
    limit: int = Query(60, ge=1, le=120)
):
    """Fetch today's newest dramas directly from original API."""
    ensure_signer()
    if genre not in H.GENRES:
        raise HTTPException(400, detail=f"Invalid genre. Allowed: {list(H.GENRES)}")
    try:
        items = H.latest(genre, only_today=only_today, max_items=limit)
        return {
            "genre": genre,
            "only_today": only_today,
            "count": len(items),
            "items": items
        }
    except Exception as e:
        raise HTTPException(500, detail=f"Latest fetch failed: {e}")

@app.get("/api/filters", tags=["Content"])
def api_filters(genre: str = Query("short_play", description="Genre")):
    """Get category filter choices from original API."""
    ensure_signer()
    if genre not in H.GENRES:
        raise HTTPException(400, detail=f"Invalid genre. Allowed: {list(H.GENRES)}")
    try:
        return {"genre": genre, "filters": H.filters(genre)}
    except Exception as e:
        raise HTTPException(500, detail=f"Filters fetch failed: {e}")

@app.get("/api/browse", tags=["Content"])
def api_browse(
    genre: str = Query("ai_series"),
    theme: Optional[str] = Query(None),
    setting: Optional[str] = Query(None),
    sort: str = Query("online_time"),
    limit: int = Query(60, ge=1, le=100)
):
    """Browse catalog with multi-facet filters."""
    ensure_signer()
    def _csv(v):
        return [x.strip() for x in v.split(',') if x.strip()] if v else None
    try:
        items = H.browse(genre, theme=_csv(theme), setting=_csv(setting), sort=sort, max_items=limit)
        return {"genre": genre, "count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(500, detail=f"Browse failed: {e}")

@app.get("/api/episodes", tags=["Content"])
def api_episodes(series_id: str = Query(..., description="Original series ID")):
    """Get full episode list and metadata for a series directly from original API."""
    ensure_signer()
    try:
        meta, eps = H.get_episodes(series_id)
        return {"meta": meta, "episode_count": len(eps), "episodes": eps}
    except Exception as e:
        raise HTTPException(500, detail=f"Episode fetch failed: {e}")

@app.get("/api/video_url", tags=["Streaming"])
def api_video_url(vid: str = Query(..., description="Episode Video ID"), quality: str = Query("best")):
    """Fetch direct CDN video URL and decryption metadata for a specific video ID."""
    ensure_signer()
    try:
        track = _vm_track(vid, quality)
        if not track:
            raise HTTPException(404, detail="No video stream found for vid")
        return {
            "vid": vid,
            "url": track.get("url"),
            "definition": track.get("definition"),
            "size": track.get("size"),
            "encrypted": track.get("encrypt")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Video URL fetch failed: {e}")

@app.get("/api/play", tags=["Streaming"])
def api_play(series_id: str = Query(...), ep: str = Query("all")):
    """Get playable episode metadata with streaming links."""
    ensure_signer()
    try:
        meta, eps = H.get_episodes(series_id)
        total = len(eps)
        if ep == 'all':
            want = set(range(1, total + 1))
        elif '-' in ep:
            start, end = map(int, ep.split('-'))
            want = set(range(start, end + 1))
        elif ep.isdigit():
            want = {int(ep)}
        else:
            want = set(range(1, total + 1))
            
        selected = [e for e in eps if (e.get('index') or 0) in want]
        urls = H.get_video_urls([e['vid'] for e in selected])
        
        episodes_data = []
        for e in selected:
            idx = e.get('index')
            vid = e.get('vid')
            u = urls.get(vid, {})
            episodes_data.append({
                "index": idx,
                "vid": vid,
                "title": e.get('title'),
                "stream_url": f"/api/stream?vid={vid}",
                "cdn_url": u.get('url'),
                "definition": u.get('definition'),
                "size": u.get('size')
            })
            
        return {
            "series_id": series_id,
            "title": meta.get('title'),
            "cover": meta.get('cover'),
            "episodes": episodes_data
        }
    except Exception as e:
        raise HTTPException(500, detail=f"Play info failed: {e}")

@app.get("/api/stream", tags=["Streaming"])
def api_stream(
    vid: Optional[str] = Query(None, description="Video ID"),
    series_id: Optional[str] = Query(None, description="Series ID"),
    ep: int = Query(1, description="Episode index (if series_id given)"),
    quality: str = Query("best")
):
    """Stream decrypted playable MP4 video directly (supports browser playback and scrubbing)."""
    ensure_signer()
    try:
        if not vid:
            if not series_id:
                raise HTTPException(400, detail="Must supply either 'vid' or 'series_id'")
            meta, eps = H.get_episodes(series_id)
            target = next((e for e in eps if (e.get('index') or 0) == ep), None)
            if not target:
                raise HTTPException(404, detail=f"Episode {ep} not found in series {series_id}")
            vid = target['vid']
            
        path = _ensure_decrypted(vid, quality)
        filename = f"{vid}.mp4"
        cd = f'inline; filename="{filename}"'
        return FileResponse(path, media_type="video/mp4", headers={"Content-Disposition": cd})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Streaming failed: {e}")

@app.post("/api/download", tags=["Download"])
def api_download(payload: Dict[str, Any] = Body(...)):
    """Start an unlimited batch download to local storage without any license check."""
    ensure_signer()
    raw_ids = payload.get('series_ids') or payload.get('series_id') or []
    if isinstance(raw_ids, (str, int)):
        series_ids = [str(raw_ids).strip()]
    else:
        series_ids = [str(x).strip() for x in raw_ids if str(x).strip()]
        
    if not series_ids:
        raise HTTPException(400, detail="series_id or series_ids is required")
        
    ranges = payload.get('ranges') or {}
    if not isinstance(ranges, dict):
        ranges = {sid: str(payload.get('range', 'all')) for sid in series_ids}
    else:
        for sid in series_ids:
            ranges.setdefault(sid, str(payload.get('range', 'all')))
            
    quality = str(payload.get('quality', '1080p'))
    concurrency = max(1, min(int(payload.get('concurrency', 4)), 16))
    
    with _dl_lock:
        if _dl_state['running']:
            return {"ok": False, "error": "A download job is already running"}
            
    threading.Thread(
        target=_run_download_job,
        args=(series_ids, ranges, quality, concurrency),
        daemon=True
    ).start()
    
    return {
        "ok": True,
        "message": "Download started directly without license check",
        "series_count": len(series_ids),
        "concurrency": concurrency,
        "quality": quality
    }

@app.get("/api/download/status", tags=["Download"])
def api_download_status():
    """Get current download progress and logs."""
    with _dl_lock:
        return dict(_dl_state)

@app.post("/api/download/cancel", tags=["Download"])
def api_download_cancel():
    """Cancel running download jobs."""
    ODL.CANCEL.set()
    _dl_log("Download cancelled by user request")
    return {"ok": True, "message": "Cancellation requested"}

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '0.0.0.0')
    print(f"============================================================")
    print(f" Hongguo Direct FastAPI (No License Key)")
    print(f" Running at: http://127.0.0.1:{port}")
    print(f" Interactive Swagger API Docs: http://127.0.0.1:{port}/docs")
    print(f"============================================================")
    uvicorn.run(app, host=host, port=port)
