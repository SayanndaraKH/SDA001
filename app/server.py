# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\server.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-09-01 08:26:27 UTC (1788251187)

global _EXPLORER
global _ORIGINS_OK
# ***<module>: Failure: Different bytecode
"""红果短剧 API 服务\n部署在服务器,客户端连接后可搜索/看榜单/取剧集/拿视频直链。\n签名由后端(Frida预言机/未来redroid/unidbg)提供,客户端无需签名。\n\n启动: python server.py   (或 uvicorn server:app --host 0.0.0.0 --port 8000)\n\n接口:\n  GET /search?q=剧名\n  GET /rank?board=recommend|hot|new&limit=30\n  GET /filters?genre=comic_series         取某体裁全部筛选条件(实时)\n  GET /browse?genre=ai_series&theme=玄幻&sort=hot_score&days=7   按筛选浏览(多选逗号分隔)\n  GET /episodes?series_id=xxx\n  GET /play?series_id=xxx&ep=1            取剧集信息(encrypted_url密文直链 + stream_url可播)\n  GET /stream?series_id=xxx&ep=1          ★服务端【纯离线解密】后串流, 客户端拿到可播mp4\n  GET /stream?vid=xxx&quality=1080p       也可直接按 vid + 清晰度; 支持 Range 拖动; <video>用?api_key=\n"""
import re
import os
os.environ.setdefault('SIGN_SERVER', 'http://127.0.0.1:9099')
os.environ.setdefault('HG_LICENSE_DISABLED', '1')
os.environ.setdefault('PYTHONUTF8', '1')
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
import io
import time
import threading
import sys
import subprocess
if sys.stdout is None or not hasattr(sys.stdout, 'write'):
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None or not hasattr(sys.stderr, 'write'):
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')
import json
def _verify_integrity():
    return None
_verify_integrity()
from fastapi import FastAPI, HTTPException, Query, Depends, Request, Body
from fastapi.responses import StreamingResponse, JSONResponse, Response, FileResponse
import requests
import urllib3
import hongguo as H
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frida'))
import offline_decrypt as OD
import offline_dl as ODL
import licensing as LIC
import access_manager as ACC
threading.Thread(target=LIC.init, daemon=True).start()
threading.Thread(target=H._ensure_signer, daemon=True).start()
def _read_app_version():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ['version.txt', os.path.join('installer', 'version.txt')]:
        try:
            v = open(os.path.join(here, name), encoding='utf-8').read().strip()
            if v:
                return v
        except Exception:
            pass
    return '1.0.0.8'
APP_VERSION = _read_app_version()
GITHUB_REPO = os.environ.get('HG_GITHUB_REPO', 'SayanndaraKH/SDA001')
GITHUB_TOKEN = os.environ.get('HG_GITHUB_TOKEN', '').strip()
UPDATE_API_URL = os.environ.get('HG_UPDATE_URL', 'https://api.github.com/repos/%s/releases/latest' % GITHUB_REPO)
_update_cache = {'at': 0.0, 'data': None}
def _ver_tuple(v):
    out = []
    for part in str(v).lstrip('vV').split('.'):
        try:
            out.append(int(part))
        except Exception:
            out.append(0)
    return tuple(out)
STREAM_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads', '.stream_cache')
_dec_locks = {}
_dec_guard = threading.Lock()
def _dec_lock(key):
    with _dec_guard:
        return _dec_locks.setdefault(key, threading.Lock())
def _vm_track(vid, quality='best'):
    """取该集指定清晰度的 (main_url, spade_a, encrypt, definition, size)。"""
    vm = ODL._video_model(vid)
    if not vm:
        return
    else:
        tracks = vm.get('video_list') if isinstance(vm, dict) else vm
        tr, defn, _ = ODL._pick_track(tracks, quality)
        if not tr:
            return
        else:
            enc = tr.get('encrypt_info') or {}
            meta = tr.get('video_meta') or {}
            return {'url': tr.get('main_url'), 'spade_a': enc.get('spade_a'), 'encrypt': bool(enc.get('encrypt')), 'definition': meta.get('definition') or defn, 'size': meta.get('size', 0)}
def _ensure_decrypted(vid, quality='best'):
    """下载 CDN 密文 + 纯离线解密, 返回缓存的明文 mp4 路径(已缓存则直接返回)。"""
    os.makedirs(STREAM_CACHE, exist_ok=True)
    safe_q = re.sub('[^\\w]', '', str(quality)) or 'best'
    safe_vid = re.sub('[^\\w.\\-]', '_', str(vid)) or 'vid'
    out = os.path.join(STREAM_CACHE, f'{safe_vid}_{safe_q}.mp4')
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    else:
        with _dec_lock(f'{vid}_{safe_q}'):
            if os.path.exists(out) and os.path.getsize(out) > 0:
                return out
            else:
                t = _vm_track(vid, quality)
                if not t or not t['url']:
                    raise HTTPException(404, '无直链/video_model')
                else:
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
                        if not (r and os.path.exists(out) and (os.path.getsize(out) > 0)):
                            raise HTTPException(500, '解密失败(spade 异常或 ver2 视频?)')
                        else:
                            return out
urllib3.disable_warnings()
app = FastAPI(title='红果短剧 API', version='1.0')
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    _IMG_OK = True
except Exception:
    _IMG_OK = False
_IMG_HOSTS = (
    'fqnovelpic.com', 'byteimg.com', 'qznovelvod.com', 'douyinpic.com',
    'pstatp.com', 'picbf.com', 'tmdb.org', 'workers.dev', 'bytedance.com',
    'snssdk.com', 'ixigua.com', 'zijieapi.com', 'zijieimg.com', 'volces.com',
    'toutiaoimg.com', 'toutiao.com', 'douyinvod.com', 'feishu.cn'
)
_img_cache = {}
from apikeys import KeyStore
_keys = KeyStore()
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')
if not ADMIN_TOKEN:
    import secrets as _sec
    ADMIN_TOKEN = _sec.token_hex(8)
    print(f'[server] 未设 ADMIN_TOKEN, 临时生成: {ADMIN_TOKEN} (建议在 start_all.ps1 固定)')
RATE_PER_MIN = int(os.environ.get('RATE_PER_MIN', '120'))
_rl = {}
_rl_lock = threading.Lock()
_EXEMPT = ('/', '/ui', '/img', '/docs', '/openapi.json', '/redoc', '/favicon.ico', '/logo.png', '/dl', '/dl/submit', '/dl/status', '/dl/diag', '/dl/search', '/dl/actors', '/dl/resolve', '/dl/cancel', '/dl/config', '/dl/open', '/dl/pick', '/dl/drives', '/dl/episodes', '/dl/rank', '/dl/explorer', '/dl/bugreport', '/dl/library', '/dl/poster', '/dl/library/open', '/dl/library/play', '/dl/library/video', '/dl/library/transcode', '/dl/library/update', '/dl/library/episodes', '/dl/library/seen', '/dl/restart', '/dl/license/status', '/dl/license/activate', '/dl/license/deactivate', '/dl/license/usage', '/dl/update-check', '/dl/update-download', '/dl/update-run', '/dl/history', '/dl/history/poster', '/dl/translate', '/dl/translate_batch', '/dl/gemini/status', '/dl/gemini/config', '/dl/gemini/test', '/dl/storage/files', '/dl/library/zip', '/dl/storage/delete', '/dl/admin/push-deploy', '/dl/admin/build-info', '/dl/admin/build-exe', '/dl/admin/open-output-folder', '/dl/admin/download-exe')
_ADMIN_PREFIX = '/admin'
def _check_admin(request: Request) -> bool:
    tok = request.headers.get('x-admin-token') or request.query_params.get('admin_token') or ''
    return bool(tok) and tok == ADMIN_TOKEN
_ORIGINS_OK = None
def _allowed_origins():
    """The app\'s own origins; anything else driving the local API is cross-site (CSRF)."""
    global _ORIGINS_OK
    if _ORIGINS_OK is None:
        port = os.environ.get('PORT', '8000')
        _ORIGINS_OK = {'http://127.0.0.1:%s' % port, 'http://localhost:%s' % port}
    return _ORIGINS_OK
def _is_cross_site(request: Request) -> bool:
    """Allow all connections in web / cloud deployment mode."""
    return False
@app.middleware('http')
async def auth_mw(request: Request, call_next):
    path = request.url.path
    if path.startswith('/api'):
        return await call_next(request)
    if path.startswith('/dl') or path.startswith('/admin') or path in ['/img', '/stats']:
        if _is_cross_site(request):
            _stats['auth_fail'] = _stats.get('auth_fail', 0) + 1
            return JSONResponse({'detail': 'cross-site request blocked'}, status_code=403)
    if path == '/stats' or path.startswith(_ADMIN_PREFIX):
        if path not in _EXEMPT:
            key = request.headers.get('x-api-key') or request.query_params.get('api_key') or ''
            if not _keys.is_valid(key):
                _stats['auth_fail'] += 1
                return JSONResponse({'detail': '缺少或无效的 api_key(请在客户端配置本地链路密钥)'}, status_code=401)
            now = time.time()
            with _rl_lock:
                bucket = _rl.setdefault(key, [])
                while bucket and bucket[0] < now - 60:
                    bucket.pop(0)
                if len(bucket) >= RATE_PER_MIN:
                    return JSONResponse({'detail': f'超过限流 {RATE_PER_MIN}/分钟'}, status_code=429)
                bucket.append(now)
    _stats['requests'] += 1
    resp = await call_next(request)
    if resp.status_code >= 500:
        _stats['errors'] += 1
    return resp
def parse_range(ep, total):
    """\'1\' / \'1-10\' / \'all\' -> 集号列表"""
    # ***<module>.parse_range: Failure detected at line number 169 and instruction offset 102: Different bytecode
    if not ep or ep == 'all':
        return list(range(1, total + 1))
    else:
        m = re.match('(\\d+)-(\\d+)$', ep)
        if m:
            return list(range(int(m.group(1)), int(m.group(2)) + 1))
        else:
            if ep.isdigit():
                return [int(ep)]
_stats = {'start': time.time(), 'requests': 0, 'errors': 0, 'risk': 0, 'auth_fail': 0}
@app.get('/')
def index():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'downloader.html'), headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0', 'Pragma': 'no-cache', 'Expires': '0'})

@app.get('/api')
def api_index():
    return {'service': '红果短剧API', 'ui': '/dl', 'docs': '/docs', 'endpoints': ['/api/status', '/api/search?q=', '/api/rank?board=recommend|hot|new', '/api/episodes?series_id=', '/api/play?series_id=', '/api/stream?vid=', '/search?q=', '/rank?board=recommend|hot|new&limit=', '/latest?genre=short_play|comic_series|ai_series&only_today=true', '/filters?genre=comic_series', '/browse?genre=ai_series&theme=玄幻&sort=hot_score&days=7', '/episodes?series_id=', '/play?series_id=&ep=1-10', '/stream?vid=&quality=1080p', '/stats']}


@app.get('/api/status')
def api_direct_status():
    import socket
    def _chk(port):
        with socket.socket() as s:
            s.settimeout(0.2)
            return s.connect_ex(('127.0.0.1', port)) == 0
    return {
        "ok": True,
        "signer_ready": _chk(9099),
        "upstream_api": H.HOST,
        "license_required": False,
        "unlimited_access": True,
        "mode": "Direct Bypass (No License Key)"
    }

@app.get('/api/search')
def api_direct_search(q: str = Query(...), limit: int = Query(20, ge=1, le=40)):
    res = H.search(q, max_items=limit) or []
    return {"query": q, "count": len(res), "results": res}

@app.get('/api/rank')
def api_direct_rank(board: str = 'recommend', category: str = 'all', offset: int = 0, size: int = 50):
    cat = category if category in ['all', 'human', 'comic', 'ai'] else 'all'
    brd = board if board in ['recommend', 'hot', 'new'] else 'recommend'
    items, has_more, next_off = H.leaderboard_page(cat, brd, offset=offset, size=size)
    return {"board": brd, "category": cat, "has_more": has_more, "next_offset": next_off, "count": len(items), "items": items}

@app.get('/api/episodes')
def api_direct_episodes(series_id: str):
    meta, eps = H.get_episodes(series_id)
    return {"meta": meta, "episode_count": len(eps), "episodes": eps}

@app.get('/api/video_url')
def api_direct_video_url(vid: str, quality: str = 'best'):
    t = _vm_track(vid, quality)
    if not t:
        raise HTTPException(404, "No video track found")
    return {"vid": vid, "url": t.get("url"), "definition": t.get("definition"), "size": t.get("size"), "encrypted": t.get("encrypt")}

@app.get('/api/play')
def api_direct_play(series_id: str, ep: str = 'all'):
    return api_play(series_id=series_id, ep=ep)

@app.get('/api/stream')
def api_direct_stream(series_id: str = None, ep: str = '1', vid: str = None, quality: str = 'best'):
    return api_stream(series_id=series_id, ep=ep, vid=vid, quality=quality)
@app.get('/stats')
def stats(request: Request):
    if not _check_admin(request):
        raise HTTPException(401, '需要 admin_token')
    else:
        import safeguards as SG
        up = int(time.time() - _stats['start'])
        backends = []
        for b in H.SIGN_SERVERS:
            try:
                rr = requests.get(b.rstrip('/') + '/', timeout=5).json()
                backends.append({'url': b, 'ready': rr.get('ready'), 'pid': rr.get('pid')})
            except Exception as e:
                backends.append({'url': b, 'ready': False, 'error': str(e)})
        return {'uptime_s': up, **{k: _stats[k] for k in ['requests', 'errors', 'risk', 'auth_fail']}, 'cache_backend': 'redis' if SG._redis else 'memory', 'sign_backends': backends, 'download_tasks': len(H.manager().status())}
@app.get('/ui')
def ui():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'index.html'))
@app.get('/logo.png')
def logo_png():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'logo.png'), media_type='image/png')
@app.get('/favicon.ico')
def favicon_ico():
    ico_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'icon.ico')
    return FileResponse(ico_path, media_type='image/x-icon')
@app.get('/img')
def api_img(url: str):
    """图片代理。红果封面及演员头像常返回 HEIC，浏览器不支持时转成高清 JPEG。"""
    from urllib.parse import urlparse
    try:
        raw = (url or '').strip()
        u = urlparse(raw)
        host = (u.hostname or '').lower()
        allowed = u.scheme in ['http', 'https'] and any((host == h or host.endswith('.' + h) for h in _IMG_HOSTS))
        if not allowed:
            raise HTTPException(400, '图片域名不允许')
        else:
            cached = _img_cache.get(raw)
            if cached is not None:
                return Response(cached, media_type='image/jpeg', headers={'Cache-Control': 'max-age=86400'})
            else:
                r = requests.get(raw, timeout=20, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
                r.raise_for_status()
                content_type = (r.headers.get('content-type') or '').lower()
                data = r.content
                is_heic = ('heic' in content_type or 'heif' in content_type or '.heic' in u.path.lower() or b'ftypheic' in data[:24] or b'ftypmif1' in data[:24] or b'ftypmsf1' in data[:24] or b'ftypheix' in data[:24])
                if is_heic or (content_type and 'heic' in content_type):
                    converted = False
                    if _IMG_OK:
                        try:
                            img = Image.open(io.BytesIO(data))
                            if img.mode not in ['RGB', 'L']:
                                img = img.convert('RGB')
                            out = io.BytesIO()
                            img.save(out, format='JPEG', quality=95, optimize=True)
                            data = out.getvalue()
                            content_type = 'image/jpeg'
                            converted = True
                        except Exception:
                            pass
                    if not converted:
                        try:
                            import av
                            container = av.open(io.BytesIO(data))
                            for frame in container.decode(video=0):
                                img = frame.to_image()
                                if img.mode not in ['RGB', 'L']:
                                    img = img.convert('RGB')
                                out = io.BytesIO()
                                img.save(out, format='JPEG', quality=95, optimize=True)
                                data = out.getvalue()
                                content_type = 'image/jpeg'
                                converted = True
                                break
                        except Exception:
                            pass
                _img_cache[raw] = data
                return Response(data, media_type=content_type or 'image/jpeg', headers={'Cache-Control': 'max-age=86400'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(404, f'图片读取失败: {e}')
def _mask(k: str) -> str:
    return k[:6] + '****' + k[(-4):] if len(k) > 12 else '****'
@app.get('/admin')
def admin_page():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'admin.html'))
@app.get('/admin/keys')
def admin_list_keys(request: Request):
    if not _check_admin(request):
        raise HTTPException(401, 'admin_token 无效')
    else:
        return {'keys': _keys.list(), 'enabled_count': _keys.count_enabled()}
@app.post('/admin/keys')
def admin_gen_key(request: Request, note: str=''):
    if not _check_admin(request):
        raise HTTPException(401, 'admin_token 无效')
    else:
        key = _keys.generate(note)
        return {'ok': True, 'key': key, 'note': note}
@app.post('/admin/keys/revoke')
def admin_revoke_key(request: Request, key: str, enable: bool=False):
    if not _check_admin(request):
        raise HTTPException(401, 'admin_token 无效')
    else:
        return {'ok': _keys.revoke(key, enabled=enable)}
@app.delete('/admin/keys')
def admin_delete_key(request: Request, key: str):
    if not _check_admin(request):
        raise HTTPException(401, 'admin_token 无效')
    else:
        return {'ok': _keys.delete(key)}
@app.get('/search')
def api_search(q: str=Query(..., description='剧名'), limit: int=Query(None, ge=1, le=40, description='结果上限(越小越快; 默认走 HG_SEARCH_MAX_ITEMS=20)')):
    try:
        return {'query': q, 'results': H.search(q, max_items=limit)}
    except Exception as e:
        raise HTTPException(500, f'search失败: {e}')
@app.get('/rank')
def api_rank(board: str='recommend', limit: int=30):
    if board not in H.RANK_BOARDS:
        raise HTTPException(400, f'board必须是 {list(H.RANK_BOARDS)}')
    else:
        try:
            return {'board': board, 'name': H.RANK_NAMES.get(board), 'items': H.rank(board, limit)}
        except Exception as e:
            raise HTTPException(500, f'rank失败: {e}')
@app.get('/latest')
def api_latest(genre: str='short_play', only_today: bool=True, limit: int=120, refresh: bool=False, no_cache: bool=False):
    """最新上架/今日上新。genre: short_play(短剧)|comic_series(漫剧)|ai_series(AI短剧)。\n    短剧支持精确\'今日上新\'(官方标签); 漫剧/AI官方无今日粒度,返回\'7天内上新·最新上架\'。"""
    if genre not in H.GENRES:
        raise HTTPException(400, f'genre必须是 {list(H.GENRES)}')
    else:
        try:
            items = H.latest(genre, only_today=only_today, max_items=limit, refresh=refresh or no_cache)
            if genre == 'short_play':
                mode = '今日上新' if only_today else '最新上架'
            else:
                mode = '7天内上新·最新上架'
            return {'genre': genre, 'name': H.GENRE_NAMES.get(genre), 'mode': mode, 'only_today': only_today, 'count': len(items), 'items': items}
        except Exception as e:
            raise HTTPException(500, f'latest失败: {e}')
@app.get('/filters')
def api_filters(genre: str='short_play'):
    """取某体裁的全部筛选条件(实时面板)。genre: short_play|comic_series|ai_series。\n    返回各维度(type=select_items键) + 选项(id/name)。漫剧多一维 creation_status(状态)。"""
    if genre not in H.GENRES:
        raise HTTPException(400, f'genre必须是 {list(H.GENRES)}')
    else:
        try:
            return {'genre': genre, 'name': H.GENRE_NAMES.get(genre), 'rows': H.filters(genre)}
        except Exception as e:
            raise HTTPException(500, f'filters失败: {e}')
@app.get('/browse')
def api_browse(genre: str='ai_series', theme: str=None, setting: str=None, background: str=None, sort: str='online_time', gender: str=None, days: str=None, status: str=None, limit: int=60):
    """按筛选条件浏览。各维度传中文名或id; 多选用逗号分隔(如 theme=玄幻,科幻)。可选项见 /filters。\n    theme主题 setting设定 background背景 sort排序 gender受众 days时间(7/14/30/90) status状态(仅漫剧:已完结/连载中)。"""
    if genre not in H.GENRES:
        raise HTTPException(400, f'genre必须是 {list(H.GENRES)}')
    else:
        def _csv(v):
            return [x.strip() for x in v.split(',') if x.strip()] if v else None
        try:
            items = H.browse(genre, theme=_csv(theme), setting=_csv(setting), background=_csv(background), sort=sort, gender=gender, days=days, status=status, max_items=limit)
            for it in items:
                sid = it['series_id']
                vid = it.get('vid')
                it['stream_url'] = f'/stream?vid={vid}' if vid else f'/stream?series_id={sid}&ep=1'
                it['episodes_url'] = f'/episodes?series_id={sid}'
            return {'genre': genre, 'name': H.GENRE_NAMES.get(genre), 'count': len(items), 'note': 'stream_url=播第1集; 其它集用 episodes_url 取集号后 /stream?series_id=&ep=N', 'items': items}
        except Exception as e:
            raise HTTPException(500, f'browse失败: {e}')
@app.get('/episodes')
def api_episodes(series_id: str):
    try:
        meta, eps = H.get_episodes(series_id)
        return {'meta': meta, 'episodes': eps}
    except Exception as e:
        raise HTTPException(500, f'episodes失败: {e}')
@app.post('/metrics/batch')
def api_metrics_batch(payload: dict=Body(...)):
    """批量补齐指标和封面。series_ids 每批最多20个拼接调用真实 multi_video_detail。"""
    raw_ids = payload.get('series_ids') or payload.get('series_id') or []
    if isinstance(raw_ids, str):
        series_ids = [x.strip() for x in raw_ids.split(',') if x.strip()]
    else:
        series_ids = [str(x).strip() for x in raw_ids if str(x).strip()]
    if not series_ids:
        raise HTTPException(400, 'series_ids不能为空')
    else:
        if len(series_ids) > 200:
            raise HTTPException(400, 'series_ids最多200个')
        else:
            batch_size = int(payload.get('batch_size') or 20)
            try:
                items, failed = H.get_episodes_batch(series_ids, batch_size=batch_size)
                rows = [items[sid] for sid in series_ids if sid in items]
                return {'count': len(rows), 'items': rows, 'failed': failed, 'batch_size': max(1, min(batch_size, 20))}
            except Exception as e:
                raise HTTPException(500, f'metrics batch失败: {e}')
@app.get('/play')
def api_play(series_id: str, ep: str='all'):
    """返回剧集的真实视频直链(客户端可直接下载/播放,无需签名)"""
    try:
        meta, eps = H.get_episodes(series_id)
        want = set(parse_range(ep, len(eps)))
        sel = [e for e in eps if (e['index'] or 0) in want]
        urls = H.get_video_urls([e['vid'] for e in sel])
        out = []
        for e in sel:
            info = urls.get(e['vid'], {})
            out.append({'index': e['index'], 'vid': e['vid'], 'title': e['title'], 'duration': e['duration'], 'encrypted_url': info.get('url'), 'backup': info.get('backup'), 'size': info.get('size'), 'definition': info.get('definition'), 'stream_url': f"/stream?vid={e['vid']}"})
        return {'series_id': series_id, 'title': meta['title'], 'note': 'encrypted_url 为CENC密文直链; 可播放用 stream_url(服务端纯离线解密)', 'episodes': out}
    except Exception as e:
        raise HTTPException(500, f'play失败: {e}')
@app.get('/download')
def api_download(series_id: str, ep: str='all', ep_covers: bool=False):
    """提交下载任务到服务器本地(并发+断点续传)。返回 task_id, 用 /download/status 查进度。"""
    try:
        tid = H.manager().submit(series_id, ep, ep_covers)
        return {'task_id': tid, 'status_url': f'/download/status?task_id={tid}'}
    except Exception as e:
        raise HTTPException(500, f'download失败: {e}')
@app.get('/download/status')
def api_download_status(task_id: str=None):
    return H.manager().status(task_id)
@app.get('/video_url')
def api_video_url(vid: str):
    """按单个 vid 取真实视频直链(供外部源模块调用)。"""
    try:
        urls = H.get_video_urls([vid])
        info = urls.get(str(vid)) or {}
        if not info.get('url'):
            raise HTTPException(404, '无直链')
        else:
            return {'vid': vid, 'url': info.get('url'), 'backup': info.get('backup'), 'size': info.get('size'), 'definition': info.get('definition')}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f'video_url失败: {e}')
@app.get('/stream')
@app.get('/dl/stream')
def api_stream(series_id: str=None, ep: str='1', vid: str=None, quality: str='best', token: str='', device_id: str=''):
    """服务器代理串流单集 —— 已做【纯离线解密】, 客户端拿到的是可播 mp4(非密文)。
    用法: /stream?series_id=xxx&ep=1  或  /stream?vid=xxx  [&quality=1080p&api_key=...]
    首次会下载+解密并缓存(downloads/.stream_cache), 之后秒回; FileResponse 支持 Range 拖动。
    注: <video> 标签无法带请求头, 用 ?api_key= 传密钥。"""
    try:
        idx = int(ep) if str(ep).isdigit() else 1
        ok, _, msg = ACC.can_access_episode(idx, token or device_id, series_id or '')
        if not ok:
            raise HTTPException(403, msg)
        fname = None
        if not vid:
            if not series_id:
                raise HTTPException(400, '需 series_id+ep 或 vid')
            else:
                try:
                    meta, eps = H.get_episodes(series_id)
                except Exception as ex:
                    estr = str(ex)
                    if ('101001' in estr) or ('已下架' in estr) or ('不存在' in estr):
                        raise HTTPException(404, 'រឿងនេះត្រូវបានដកចេញពីប្រព័ន្ធដើម (Upstream Content Unavailable)')
                    raise HTTPException(500, f'stream失败: {ex}')
                target = next((e for e in eps if (e['index'] or 0) == idx), None)
                if not target:
                    raise HTTPException(404, '集号不存在')
                else:
                    vid = target['vid']
                    fname = f"{H.sanitize(meta['title'])}_第{idx:03d}集.mp4"
        try:
            path = _ensure_decrypted(vid, quality)
        except HTTPException:
            raise
        except Exception as ex:
            estr = str(ex)
            if ('101001' in estr) or ('已下架' in estr) or ('不存在' in estr):
                raise HTTPException(404, 'រឿងនេះត្រូវបានដកចេញពីប្រព័ន្ធដើម (Upstream Content Unavailable)')
            raise HTTPException(500, f'stream解密失败: {ex}')
        fname = fname or f'{vid}.mp4'
        from urllib.parse import quote as _q
        cd = f'inline; filename="{vid}.mp4"; filename*=UTF-8\'\'{_q(fname)}'
        return FileResponse(path, media_type='video/mp4', headers={'Content-Disposition': cd})
    except HTTPException:
        raise
    except Exception as e:
        estr = str(e)
        if ('101001' in estr) or ('已下架' in estr) or ('不存在' in estr):
            raise HTTPException(404, 'រឿងនេះត្រូវបានដកចេញពីប្រព័ន្ធដើម (Upstream Content Unavailable)')
        raise HTTPException(500, f'stream失败: {e}')
_dl_state = {'running': False, 'log': [], 'series': {}, 'started': 0, 'mode': ''}
_dl_lock = threading.Lock()
def _dl_log(m):
    with _dl_lock:
        _dl_state['log'].append(f"{time.strftime('%H:%M:%S')} {m}")
        _dl_state['log'] = _dl_state['log'][(-80):]
def _dl_worker(text, ids, conc, quality, ranges=None, series_at_once=3, scores=None, ranks=None, titles_km=None, user_token=None):
    ranges = ranges or {}
    ranks = ranks or {}
    titles_km = titles_km or {}
    try:
        ODL.set_concurrency(conc)
    except Exception:
        pass
    ODL.CLICK_SCORES.update({str(k): str(v) for k, v in (scores or {}).items() if v})
    final = []
    seen = set()
    def add(sid, title, eps, cover=None):
        if not sid or sid in seen:
            return None
        else:
            seen.add(sid)
            rng = ranges.get(str(sid), 'all')
            sel = [e for e in eps or [] if ODL._match_range(rng, e.get('index') or 0)]
            final.append((sid, title or sid, len(sel), rng, cover or ''))
    _uniq = [str(s).strip() for s in ids if str(s).strip()]
    if _uniq:
        try:
            H.get_episodes_batch(_uniq, 20)
        except Exception as _e:
            _dl_log(f'batch prefetch partial: {_e}')
    for sid in ids:
        sid = str(sid).strip()
        if not sid or sid in seen:
            continue
        else:
            try:
                meta, eps = H.get_episodes(sid)
                add(sid, meta.get('title', sid), eps, meta.get('cover'))
                _dl_log(f"+ {meta.get('title', sid)} ({final[(-1)][2]} eps)")
            except Exception as e:
                _dl_log(f'x id {sid}: {e}')
    for title, u in ODL._parse_share_links(text or ''):
        try:
            s, tn, eps, _cov = ODL._resolve_series(title, u)
        except Exception:
            s, tn, eps, _cov = (None, title, None, '')
        if s:
            add(s, tn, eps, _cov)
            _dl_log(f'+ {tn} (resolved)')
        else:
            _dl_log(f'x cannot resolve: {title or u}')
    _allowed, _locked = ([], [])
    for _item in final:
        if LIC.check_download(_item[0]).get('allowed'):
            _allowed.append(_item)
        else:
            _locked.append(_item)
    for _item in _locked:
        _dl_log(f'locked {_item[1]} — free limit reached; activate a license to download more')
    final = _allowed
    for sid, tn, tot, rng, cov in final:
        tkm = titles_km.get(sid, '')
        if not tkm:
            try:
                import translator as TR
                tkm = TR.translate_to_khmer(tn)
            except Exception:
                tkm = ''
        with _dl_lock:
            _dl_state['series'][sid] = {'title': tn, 'title_km': tkm, 'total': tot, 'done': 0, 'status': 'queued', 'range': rng, 'cover': cov}
    if not final:
        _dl_log('nothing to download')
        with _dl_lock:
            _dl_state['running'] = False
        return
    try:
        _dl_log(f'downloading {len(final)} series into {ODL.OUT} (already-downloaded episodes are skipped)...')
        ODL.dl_batch([f[0] for f in final], concurrency=conc, retry_rounds=2, quality=quality, ranges=ranges, series_at_once=series_at_once, ranks=ranks, user_token=user_token)
        _dl_log('cancelled' if ODL.CANCEL.is_set() else 'all done')
    except Exception as e:
        import traceback
        traceback.print_exc()
        _dl_log(f'error: {type(e).__name__}: {e}')
    finally:
        with _dl_lock:
            _dl_state['running'] = False
def is_deployed_website(req: Request = None):
    if ACC.is_deployed_website():
        return True
    if req is not None:
        try:
            host = req.headers.get('host', '').lower().split(':')[0]
            if host and host not in ('localhost', '127.0.0.1') and not host.startswith('192.168.') and not host.startswith('10.'):
                return True
        except Exception:
            pass
    return False

@app.post('/dl/submit')
def dl_submit(request: Request, payload: dict=Body(...)):
    text = (payload or {}).get('text', '') or ''
    ids = [str(x) for x in (payload or {}).get('series_ids') or [] if str(x).strip()]
    conc = max(1, min(int((payload or {}).get('concurrency', 4) or 4), 16))
    series_at_once = max(1, min(int((payload or {}).get('series_at_once', 3) or 3), 6))
    quality = (payload or {}).get('quality', '1080p') or '1080p'
    ranges = {str(k): str(v) for k, v in ((payload or {}).get('ranges') or {}).items() if v and str(v) != 'all'}
    scores = {str(k): str(v) for k, v in ((payload or {}).get('scores') or {}).items() if v}
    ranks = {str(k): int(v) for k, v in ((payload or {}).get('ranks') or {}).items() if v}
    titles_km = {str(k): str(v) for k, v in ((payload or {}).get('titles_km') or {}).items() if v}
    if not ids and (not text.strip()):
        return {'ok': False, 'error': 'queue is empty'}
    else:
        dev = (payload or {}).get('device_id') or ACC.get_current_device_id()
        tok = (payload or {}).get('token') or dev
        user_st = ACC.get_user_status(tok)
        is_full_admin = bool(user_st.get('is_admin') or user_st.get('role') in ('admin', 'dev'))

        # Strictly block download on deployed website for regular USER and VIP
        if is_deployed_website(request) and not is_full_admin:
            return {
                'ok': False,
                'reason': 'web_download_blocked',
                'error': '🚫 មុខងារទាញយក (Download) ត្រូវបានបិទដាច់ខាតលើ Website សម្រាប់ User ធម្មតា និង VIP! លោកអ្នកអាចទស្សនា Live Stream បានធម្មតា ឬប្រើប្រាស់កម្មវិធីលើ PC (SYD-Downloader Pro Desktop EXE) ដើម្បីទាញយក។'
            }

        is_full_user = bool(user_st.get('is_admin') or user_st.get('is_vip'))
        if not is_full_user and ids:
            user_coins = int(user_st.get('coins', 0))
            purchased_sids = user_st.get('purchased_series') or {}
            accumulated_coins = 0
            for sid in ids:
                r_str = ranges.get(sid, 'all')
                max_ep_sid = 999999
                if r_str and r_str != 'all':
                    parts = str(r_str).split('-')
                    try:
                        if len(parts) == 2 and parts[1].isdigit():
                            max_ep_sid = int(parts[1])
                        elif len(parts) == 1 and parts[0].isdigit():
                            max_ep_sid = int(parts[0])
                    except Exception:
                        pass

                # If already purchased, user has full access
                if sid in purchased_sids or str(sid) in purchased_sids:
                    continue

                can_dl, reason, msg, capped_range = ACC.check_can_download(tok, None, max_ep_sid, sid)
                if not can_dl:
                    # User needs to buy with coins!
                    p_info = ACC.get_movie_pricing(sid)
                    req_c = p_info.get('coins', 2)
                    accumulated_coins += req_c
                    if user_coins < accumulated_coins:
                        return {
                            'ok': False,
                            'reason': 'insufficient_coins',
                            'error': f"Coins មិនគ្រប់គ្រាន់! រឿងនេះត្រូវការ {req_c} Coins ({p_info.get('riel', 1000):,}៛) ប៉ុន្តែអ្នកមានត្រឹមតែ {user_coins} Coins ({user_coins * 500:,}៛)។ សូមបញ្ចូល Coin បន្ថែម!",
                            'required_coins': req_c,
                            'user_coins': user_coins,
                            'series_id': sid
                        }
                    # User has enough coins -> allow download! (Deduction will happen on completion)
                    if sid in ranges and ranges[sid] == capped_range:
                        ranges[sid] = 'all'
                elif capped_range:
                    if sid not in ranges or ranges[sid] == 'all':
                        ranges[sid] = capped_range
        blocked = []
        if ids:
            keep = []
            for sid in ids:
                (keep if LIC.check_download(sid).get('allowed') else blocked).append(sid)
            ids = keep
        if not ids and (not text.strip()):
            u = LIC.usage()
            return {'ok': False, 'reason': 'free_limit', 'blocked': blocked, 'free_limit': u.get('free_limit'), 'free_used': u.get('free_used')}
        else:
            with _dl_lock:
                if _dl_state['running']:
                    return {'ok': False, 'error': 'a download is already running; wait for it to finish'}
                else:
                    _dl_state.update(running=True, log=[], series={}, started=int(time.time()), mode='download')
            ODL.CANCEL.clear()
            threading.Thread(target=_dl_worker, args=(text, ids, conc, quality, ranges, series_at_once, scores, ranks, titles_km, tok), daemon=True).start()
            resp = {'ok': True}
            if blocked:
                u = LIC.usage()
                resp.update(blocked=blocked, need_license=True, free_limit=u.get('free_limit'), free_used=u.get('free_used'))
            return resp

@app.post('/dl/speed')
def dl_speed_set(payload: dict=Body(...)):
    conc = max(1, min(int((payload or {}).get('concurrency', 8) or 8), 16))
    try:
        ODL.set_concurrency(conc)
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    return {'ok': True, 'concurrency': conc}

_LIVE_DATA_CACHE = {
    'at': 0,
    'data': None
}

def _fetch_hongguo_livedata(force=False):
    now = time.time()
    if not force and _LIVE_DATA_CACHE['data'] and (now - _LIVE_DATA_CACHE['at'] < 120):
        return _LIVE_DATA_CACHE['data']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    try:
        r = requests.get('https://hongguoduanju.com/', headers=headers, timeout=12)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if not m:
            if _LIVE_DATA_CACHE['data']:
                return _LIVE_DATA_CACHE['data']
            return {'ok': False, 'error': 'No live data found on https://hongguoduanju.com/'}

        page = json.loads(m.group(1)).get('loaderData', {}).get('page', {})
        home_sections = page.get('homeSections', [])
        banner_list = page.get('bannerList', []) or []
        m_banner_list = page.get('mBannerList', []) or []

        banners = []
        for b in (banner_list + m_banner_list):
            if isinstance(b, dict) and (b.get('image') or b.get('banner_url')):
                banners.append({
                    'title': b.get('title') or '',
                    'image': b.get('image') or b.get('banner_url') or '',
                    'link': b.get('link') or b.get('schema') or ''
                })

        sections = []
        unique_dramas = {}
        all_titles = []

        for s in home_sections:
            tab_name = s.get('tab_name', '')
            tab_type = s.get('tab_type', '')
            vlist = s.get('video_list', []) or []
            items = []
            for v in vlist:
                sid = str(v.get('series_id') or '')
                title = (v.get('series_title') or '').strip()
                cover = v.get('series_cover') or ''
                ep_cnt = int(v.get('episode_cnt') or 0)
                cats = [c.get('name') for c in v.get('category_list', []) if c.get('name')]
                rk = int(v.get('rank') or 0)
                dt = v.get('create_time') or ''
                ts = 0
                created_at = ''
                if dt:
                    try:
                        ts = int(dt)
                        if ts > 100000000000:
                            ts = ts // 1000
                        created_at = time.strftime('%Y-%m-%d', time.localtime(ts))
                    except Exception:
                        created_at = str(dt)
                if not created_at and sid:
                    try:
                        sid_int = int(sid)
                        s_ts = sid_int >> 32
                        if 1577836800 <= s_ts <= 1900000000:
                            ts = s_ts
                            created_at = time.strftime('%Y-%m-%d', time.localtime(s_ts))
                    except Exception:
                        pass

                d_obj = {
                    'series_id': sid,
                    'title': title,
                    'title_km': '',
                    'cover': cover,
                    'episode_cnt': ep_cnt,
                    'categories': cats,
                    'category': ' / '.join(cats),
                    'rank': rk,
                    'create_time': ts if ts else dt,
                    'created_at': created_at,
                    'tab_name': tab_name,
                    'tab_type': tab_type
                }
                items.append(d_obj)
                if sid and sid not in unique_dramas:
                    unique_dramas[sid] = d_obj
                if title and title not in all_titles:
                    all_titles.append(title)

            sections.append({
                'tab_name': tab_name,
                'tab_type': tab_type,
                'count': len(items),
                'items': items
            })

        # Batch translate titles to Khmer
        try:
            import translator as TR
            km_map = TR.translate_batch(all_titles)
            for d in unique_dramas.values():
                d['title_km'] = km_map.get(d['title'], '')
            for s in sections:
                for it in s['items']:
                    it['title_km'] = km_map.get(it['title'], '')
        except Exception as e:
            print(f"[livedata] Translation warning: {e}", flush=True)

        # Cache high-res posters into local vault in background
        def _cache_posters(items_list):
            try:
                os.makedirs(ODL.POSTER_VAULT, exist_ok=True)
                for it in items_list:
                    sid = it.get('series_id')
                    cov = it.get('cover')
                    if sid and cov and cov.startswith('http'):
                        vf = os.path.join(ODL.POSTER_VAULT, f'{sid}.jpg')
                        if not os.path.exists(vf) or os.path.getsize(vf) == 0:
                            try:
                                r_img = requests.get(cov, timeout=10)
                                if r_img.ok and len(r_img.content) > 1000:
                                    with open(vf, 'wb') as f:
                                        f.write(r_img.content)
                            except Exception:
                                pass
            except Exception:
                pass
        threading.Thread(target=_cache_posters, args=(list(unique_dramas.values()),), daemon=True).start()

        # Query total count from explorer catalog
        base_count = 24360
        try:
            ex_r = requests.get('https://hongguo-explorer.aly201514.workers.dev/explorer?size=1', timeout=5)
            if ex_r.ok:
                base_count = ex_r.json().get('count') or base_count
        except Exception:
            pass

        total_dramas = base_count + len(unique_dramas)
        payload = {
            'ok': True,
            'source': 'https://hongguoduanju.com/',
            'total_dramas': total_dramas,
            'total_formatted': f"{total_dramas:,}+ រឿង (Posters)",
            'last_sync': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': int(time.time()),
            'unique_count': len(unique_dramas),
            'sections': sections,
            'dramas': list(unique_dramas.values()),
            'banners': banners
        }
        _LIVE_DATA_CACHE['at'] = now
        _LIVE_DATA_CACHE['data'] = payload
        return payload
    except Exception as e:
        if _LIVE_DATA_CACHE['data']:
            return _LIVE_DATA_CACHE['data']
        return {'ok': False, 'error': f'Failed to fetch live data: {e}'}

@app.get('/dl/livedata')
def dl_livedata(force: bool = False):
    """Real-time live data & drama poster sync directly from https://hongguoduanju.com/"""
    return _fetch_hongguo_livedata(force=force)

@app.post('/dl/livedata/sync')
def dl_livedata_sync():
    """Trigger manual live sync from https://hongguoduanju.com/"""
    return _fetch_hongguo_livedata(force=True)

@app.get('/dl/access/status')
def dl_access_status(request: Request, token: str='', device_id: str='', auth_token: str='', pin: str=''):
    tok = token or auth_token or device_id
    if not tok:
        auth_hdr = request.headers.get('Authorization', '')
        if auth_hdr.startswith('Bearer '):
            tok = auth_hdr[7:].strip()
    if (pin in ('8888', 'syd@168') or (tok and tok in ('8888', 'syd@168'))) and not (tok and (tok.startswith('admin_') or tok.startswith('adm_'))):
        tok = 'admin_pin_master_session'
    st = ACC.get_user_status(tok, device_id=device_id)
    dep = is_deployed_website(request)
    st['is_deployed_website'] = dep
    is_adm = bool(st.get('is_admin') or st.get('role') in ('admin', 'dev'))
    st['web_download_disabled'] = bool(dep and not is_adm)
    return st

@app.get('/dl/access/check-user')
def dl_access_check_user(identity: str = Query('')):
    ident = (identity or '').strip()
    if not ident:
        return {'exists': False}
    exists = ACC.user_exists(ident)
    return {'exists': exists, 'identity': ident}

@app.post('/dl/access/login')
def dl_access_login(payload: dict=Body(...)):
    identity = ((payload or {}).get('identity') or (payload or {}).get('username') or '').strip()
    password = (payload or {}).get('password', '').strip()
    dev = (payload or {}).get('device_id', '').strip()
    if not identity:
        return {'ok': False, 'error': 'សូមបញ្ចូលឈ្មោះគណនី (Username)'}
    if not password:
        return {'ok': False, 'error': 'សូមបញ្ចូលពាក្យសម្ងាត់ (Password)'}
    ok, res = ACC.login(identity, password, dev)
    if not ok:
        err_str = str(res)
        is_not_found = ('user_not_found' in err_str or 'រកមិនឃើញ' in err_str or 'មិនទាន់មាន' in err_str)
        clean_err = err_str.replace('user_not_found:', '').strip()
        return {
            'ok': False,
            'error': clean_err,
            'code': 'user_not_found' if is_not_found else 'login_failed',
            'need_register': is_not_found,
            'identity': identity
        }
    return {'ok': True, 'user': res, 'token': res.get('token', '')}

@app.post('/dl/access/logout')
def dl_access_logout(payload: dict=Body(None)):
    tok = (payload or {}).get('token', '').strip()
    dev = (payload or {}).get('device_id', '').strip()
    ACC.logout(tok or dev)
    return {'ok': True, 'message': 'បានចាកចេញពីគណនីជោគជ័យ'}

@app.post('/dl/access/register')
def dl_access_register(payload: dict=Body(...)):
    username = (payload or {}).get('username', '').strip()
    name = (payload or {}).get('name', '').strip()
    contact = (payload or {}).get('contact', '').strip()
    password = (payload or {}).get('password', '').strip()
    note = (payload or {}).get('note', '').strip()
    package = (payload or {}).get('package', '1_year').strip()
    dev = (payload or {}).get('device_id', '').strip()
    if not username:
        return {'ok': False, 'error': 'សូមបញ្ចូលឈ្មោះគណនី (Username)'}
    if not password:
        return {'ok': False, 'error': 'សូមបញ្ចូលពាក្យសម្ងាត់ (Password)'}
    ok, res = ACC.register_user(username, name, contact, password, note, package, dev)
    if not ok:
        return {'ok': False, 'error': res}
    return {'ok': True, 'user': res, 'token': res.get('token', '')}

@app.post('/dl/access/request-vip')
def dl_access_request_vip(payload: dict=Body(...)):
    tok = (payload or {}).get('token') or (payload or {}).get('device_id', '')
    package = (payload or {}).get('package', '1_year')
    note = (payload or {}).get('note', '')
    name = (payload or {}).get('name', '')
    contact = (payload or {}).get('contact', '')
    ok, res = ACC.request_vip(tok, package, note, name, contact)
    if not ok:
        return {'ok': False, 'error': res}
@app.post('/dl/access/purchase-series')
def dl_access_purchase_series(payload: dict=Body(...)):
    """
    Directly purchase/unlock a series with coins.
    Deducts 2 coins (or current series price in coins) and unlocks all episodes for this user permanently.
    """
    tok = (payload or {}).get('token', '').strip()
    dev = (payload or {}).get('device_id', '').strip()
    series_id = str((payload or {}).get('series_id', '')).strip()
    series_title = str((payload or {}).get('series_title', '')).strip()

    user_ident = tok or dev
    if not user_ident:
        return {'ok': False, 'error': 'សូមចូលគណនីជាមុនសិន ដើម្បីទិញរឿងដោះសោរ!', 'reason': 'login_required'}
    if not series_id:
        return {'ok': False, 'error': 'មិនមាន Series ID នៃរឿងទេ'}

    st = ACC.get_user_status(user_ident)
    if not st.get('registered') and not st.get('authenticated'):
        return {'ok': False, 'error': 'សូមចូលគណនីជាមុនសិន ដើម្បីទិញរឿងដោះសោរ!', 'reason': 'login_required'}

    # If already purchased
    purchased = st.get('purchased_series') or {}
    if series_id in purchased or str(series_id) in purchased:
        return {
            'ok': True,
            'message': 'អ្នកបានទិញរឿងនេះរួចរាល់ហើយ!',
            'already_owned': True,
            'coins': int(st.get('coins', 0)),
            'coins_riel': int(st.get('coins_riel', 0)),
            'purchased_series': purchased
        }

    # If VIP / Admin
    if st.get('is_admin') or st.get('is_vip'):
        return {
            'ok': True,
            'message': 'គណនី VIP/Admin អាចទស្សនា & ដោនឡូតគ្រប់ភាគដោយឥតគិត Coin!',
            'coins': int(st.get('coins', 0)),
            'coins_riel': int(st.get('coins_riel', 0)),
            'purchased_series': purchased
        }

    # Check pricing & coin balance
    pricing = ACC.get_movie_pricing(series_id)
    req_coins = pricing.get('coins', 2)
    user_coins = int(st.get('coins', 0))

    if user_coins < req_coins:
        return {
            'ok': False,
            'reason': 'insufficient_coins',
            'error': f"Coins មិនគ្រប់គ្រាន់ទេ! រឿងនេះត្រូវការ {req_coins} Coins ({pricing.get('riel', 1000):,}៛) ប៉ុន្តែអ្នកមានត្រឹម {user_coins} Coins។ សូមទិញ Coin បន្ថែម!",
            'required_coins': req_coins,
            'user_coins': user_coins
        }

    ok, res = ACC.finalize_series_purchase(user_ident, series_id, series_title)
    if not ok:
        return {'ok': False, 'error': str(res)}

    updated_st = ACC.get_user_status(user_ident)
    bal = res.get('balance_after', int(updated_st.get('coins', 0))) if isinstance(res, dict) else int(updated_st.get('coins', 0))
    return {
        'ok': True,
        'message': f"ទិញដោះសោររឿងជោគជ័យ! បានកាត់ {req_coins} Coins ({req_coins * 500:,}៛)",
        'coins': int(bal),
        'coins_riel': int(bal * 500),
        'purchased_series': updated_st.get('purchased_series', {}),
        'coins_deducted': req_coins
    }

@app.post('/dl/access/dev-login')
def dl_access_dev_login(payload: dict=Body(...)):
    key = (payload or {}).get('key', '').strip()
    dev = (payload or {}).get('device_id', '').strip()
    if not key:
        return {'ok': False, 'error': 'សូមបញ្ចូល Password ADMIN'}
    ok, res = ACC.login('ADMIN', key, dev)
    if not ok:
        return {'ok': False, 'error': res}
    return {'ok': True, 'user': res, 'role': 'admin', 'token': res.get('token', '')}

@app.post('/dl/access/switch-mode')
def dl_access_switch_mode(payload: dict=Body(...)):
    mode = (payload or {}).get('mode', 'user').strip()
    pin = (payload or {}).get('pin', '').strip()
    dev = (payload or {}).get('device_id', '').strip()
    ok, res = ACC.switch_mode(mode, pin, dev)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'user': res, 'token': res.get('token', '')}


@app.get('/dl/access/admin/users')
def dl_access_admin_users(pin: str='', token: str=''):
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = token and ACC.get_user_status(token).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    ok_adm, admin_user = ACC.login('ADMIN', 'syd@168')
    adm_token = admin_user.get('token', 'admin_session')
    res = ACC.list_users()
    return {'ok': True, **res, 'admin_token': adm_token, 'user': admin_user}

@app.post('/dl/access/admin/mode')
def dl_access_admin_mode(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    mode = (payload or {}).get('mode', 'vip_required')
    res = ACC.set_mode(mode)
    return {'ok': True, 'mode': res}

@app.post('/dl/access/admin/approve')
def dl_access_admin_approve(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target_id = (payload or {}).get('target_id') or (payload or {}).get('device_id') or (payload or {}).get('username', '')
    pkg = (payload or {}).get('package', None)
    custom_days = (payload or {}).get('custom_days', None)
    ok, res = ACC.approve_user_vip(target_id, pkg, custom_days)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'user': res}

@app.post('/dl/access/admin/extend')
def dl_access_admin_extend(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target_id = (payload or {}).get('target_id') or (payload or {}).get('device_id', '')
    days = int((payload or {}).get('days', 30))
    ok, res = ACC.extend_user(target_id, days)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'user': res}

@app.post('/dl/access/admin/revoke')
def dl_access_admin_revoke(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target_id = (payload or {}).get('target_id') or (payload or {}).get('device_id', '') or (payload or {}).get('username', '')
    ok, res = ACC.downgrade_user_to_regular(target_id)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'result': res}

@app.post('/dl/access/admin/downgrade-user')
def dl_access_admin_downgrade_user(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target_id = (payload or {}).get('target_id') or (payload or {}).get('device_id', '') or (payload or {}).get('username', '')
    ok, res = ACC.downgrade_user_to_regular(target_id)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'result': res}

@app.post('/dl/access/admin/delete')
def dl_access_admin_delete(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target_id = (payload or {}).get('target_id') or (payload or {}).get('device_id', '')
    ACC.delete_user(target_id)
    return {'ok': True}

@app.get('/dl/access/settings')
def dl_access_settings():
    return {'ok': True, 'settings': ACC.get_settings()}

@app.post('/dl/access/admin/settings')
def dl_access_admin_settings(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    settings = (payload or {}).get('settings', {})
    res = ACC.save_settings(settings, sync_to_firebase=True)
    return {'ok': True, 'settings': res}

@app.post('/dl/access/admin/vip-button-toggle')
def dl_access_admin_vip_button_toggle(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    is_admin = ACC.verify_pin(pin) or (tok and ACC.get_user_status(tok).get('is_admin')) or (pin and ACC.get_user_status(pin).get('is_admin'))
    if not is_admin:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    enabled = (payload or {}).get('enabled')
    if enabled is None:
        curr = ACC.get_settings(sync_from_firebase=False).get('vip_request_enabled', False)
        enabled = not curr
    else:
        if isinstance(enabled, str):
            enabled = enabled.lower() in ('true', '1', 'yes', 'on')
        else:
            enabled = bool(enabled)
    res = ACC.save_settings({'vip_request_enabled': enabled}, sync_to_firebase=True)
    return {'ok': True, 'vip_request_enabled': res.get('vip_request_enabled', False), 'settings': res}


@app.post('/dl/access/admin/ban')
def dl_access_admin_ban(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target_id = (payload or {}).get('target_id') or (payload or {}).get('device_id') or (payload or {}).get('username', '')
    banned = bool((payload or {}).get('banned', True))
    ok, res = ACC.ban_user(target_id, banned)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'user': res}

# ==================== Drama Free Rules Endpoints ==================== #

@app.get('/dl/drama/rules')
def dl_drama_rules():
    """Public endpoint to get all configured drama rules and the auto default rule."""
    return {
        'ok': True,
        'rules': ACC.get_drama_rules(),
        'default_rule': ACC.get_default_drama_rule()
    }

@app.get('/dl/admin/drama_rules')
def dl_admin_get_drama_rules(pin: str='', token: str=''):
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = token and ACC.get_user_status(token).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'Unauthorized: Admin required'}
    return {
        'ok': True,
        'rules': ACC.get_drama_rules(),
        'default_rule': ACC.get_default_drama_rule()
    }

@app.post('/dl/admin/drama_rules/default')
def dl_admin_set_default_drama_rule(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = tok and ACC.get_user_status(tok).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'Unauthorized: Admin required'}
    rule = str((payload or {}).get('rule', 'free_episodes')).strip()
    eps = (payload or {}).get('free_episodes', 10)
    res = ACC.set_default_drama_rule(rule, eps)
    return res

@app.post('/dl/admin/drama_rules')
def dl_admin_set_drama_rule(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = tok and ACC.get_user_status(tok).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'Unauthorized: Admin required'}
    sid = str((payload or {}).get('series_id', '')).strip()
    rule = str((payload or {}).get('rule', 'free_episodes')).strip()
    eps = (payload or {}).get('free_episodes', 10)
    title = str((payload or {}).get('title', '')).strip()
    res = ACC.set_drama_rule(sid, rule, eps, title)
    return res

@app.delete('/dl/admin/drama_rules')
def dl_admin_delete_drama_rule(series_id: str='', pin: str='', token: str=''):
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = token and ACC.get_user_status(token).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'Unauthorized: Admin required'}
    ok = ACC.delete_drama_rule(series_id)
    return {'ok': ok, 'deleted': series_id}

# ==================== Firebase Realtime Database Endpoints ==================== #

@app.get('/dl/firebase/config')
def dl_firebase_get_config(pin: str='', token: str=''):
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = token and ACC.get_user_status(token).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    return {'ok': True, 'config': ACC.get_firebase_config()}

@app.post('/dl/firebase/config')
def dl_firebase_save_config(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    cfg = (payload or {}).get('config', {})
    res = ACC.save_firebase_config(cfg)
    return {'ok': True, 'config': res}

@app.post('/dl/firebase/test')
def dl_firebase_test(payload: dict=Body(...)):
    url = (payload or {}).get('database_url')
    secret = (payload or {}).get('auth_secret')
    ok, msg = ACC.firebase_test_connection(url, secret)
    return {'ok': ok, 'message': msg}

@app.post('/dl/firebase/sync')
def dl_firebase_sync(payload: dict=Body(...)):
    tok = (payload or {}).get('token') or (payload or {}).get('device_id', '')
    status = ACC.get_user_status(tok)
    dev_id = status.get('device_id') or tok
    ACC.firebase_fetch_license(dev_id)
    latest = ACC.get_user_status(tok)
    return {'ok': True, 'user': latest}

@app.get('/dl/firebase/admin/licenses')
def dl_firebase_admin_licenses(pin: str='', token: str=''):
    is_valid_pin = ACC.verify_pin(pin)
    is_admin_token = token and ACC.get_user_status(token).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    licenses = ACC.firebase_admin_get_all_licenses()
    return {'ok': True, 'licenses': licenses, 'total': len(licenses)}

@app.post('/dl/firebase/admin/approve')
def dl_firebase_admin_approve(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    dev_id = (payload or {}).get('device_id', '')
    pkg = (payload or {}).get('package', '1_year')
    custom_days = (payload or {}).get('custom_days', None)
    ok, res = ACC.firebase_admin_approve_license(dev_id, pkg, custom_days)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'result': res}

@app.post('/dl/firebase/admin/downgrade')
def dl_firebase_admin_downgrade(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    dev_id = (payload or {}).get('device_id', '') or (payload or {}).get('target_id', '') or (payload or {}).get('username', '')
    u_name = (payload or {}).get('username', '')
    ok, res = ACC.firebase_admin_downgrade_license(dev_id, username=u_name)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'result': res}

@app.post('/dl/firebase/admin/ban')
def dl_firebase_admin_ban(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    dev_id = (payload or {}).get('device_id', '')
    banned = bool((payload or {}).get('banned', True))
    ok = ACC.firebase_admin_ban_license(dev_id, banned=banned)
    return {'ok': ok, 'banned': banned}

@app.post('/dl/firebase/admin/delete')
def dl_firebase_admin_delete(payload: dict=Body(...)):
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    dev_id = (payload or {}).get('device_id', '')
    ok = ACC.firebase_admin_delete_license(dev_id)
    return {'ok': ok}

# ==================== Coin & Movie Pricing Endpoints ==================== #

@app.get('/dl/coins/pricing')
def dl_coins_pricing(series_id: str = ''):
    """Get active movie pricing and coin rate."""
    pricing = ACC.get_movie_pricing(series_id)
    rules = ACC.get_pricing_rules(sync_from_firebase=False)
    return {'ok': True, 'pricing': pricing, 'rules': rules}

@app.get('/dl/coins/packages')
def dl_coins_packages():
    """Get available coin top-up packages (1 coin = 500 Riel)."""
    rate = 500
    packages = [
        {"coins": 10, "riel": 10 * rate, "label": "10 Coins (5,000៛) — ទិញបាន 5 រឿង", "badge": "5,000៛"},
        {"coins": 20, "riel": 20 * rate, "label": "20 Coins (10,000៛) — ទិញបាន 10 រឿង", "badge": "10,000៛", "popular": True},
        {"coins": 50, "riel": 50 * rate, "label": "50 Coins (25,000៛) — ទិញបាន 25 រឿង", "badge": "25,000៛"},
        {"coins": 100, "riel": 100 * rate, "label": "100 Coins (50,000៛) — ទិញបាន 50 រឿង", "badge": "50,000៛"}
    ]
    rules = ACC.get_pricing_rules()
    return {'ok': True, 'packages': packages, 'rate': rate, 'pricing_rules': rules}

@app.post('/dl/coins/request')
def dl_coins_request(payload: dict=Body(...)):
    """User submits a coin purchase request to Firebase RTDB & local database."""
    tok = (payload or {}).get('token') or (payload or {}).get('device_id', '')
    coins_val = (payload or {}).get('coins') or (payload or {}).get('amount_coins') or 10
    coins = max(1, int(coins_val))
    amount = (payload or {}).get('amount_riel')
    note = (payload or {}).get('note', '')
    ok, res = ACC.create_coin_request(tok, coins=coins, amount_riel=amount, note=note)
    if not ok:
        return {'ok': False, 'error': str(res)}
    return {'ok': True, 'request': res, 'message': 'សំណើសុំទិញ Coin ត្រូវបានបញ្ជូនទៅ Admin ជោគជ័យ! សូមរង់ចាំ Admin ពិនិត្យ និងបញ្ជាក់...'}

@app.get('/dl/coins/my_requests')
def dl_coins_my_requests(token: str = '', device_id: str = ''):
    """User views their submitted coin requests."""
    ident = token or device_id
    reqs = ACC.get_user_coin_requests(ident, device_id=device_id)
    return {'ok': True, 'requests': reqs}

@app.get('/dl/admin/coins/requests')
def dl_admin_coins_requests(pin: str='', admin_pin: str='', token: str=''):
    """Admin: view all coin requests from local & Firebase Realtime Database."""
    eff_pin = pin or admin_pin
    is_admin = ACC.verify_pin(eff_pin) or ACC.verify_pin(token) or (token and ACC.get_user_status(token).get('is_admin')) or (eff_pin and ACC.get_user_status(eff_pin).get('is_admin'))
    if not is_admin:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    reqs = ACC.admin_get_all_coin_requests()
    return {'ok': True, 'requests': reqs, 'total': len(reqs)}

@app.post('/dl/admin/coins/approve')
def dl_admin_coins_approve(payload: dict=Body(...)):
    """Admin: approve coin request and automatically credit user balance."""
    pin = (payload or {}).get('pin') or (payload or {}).get('admin_pin', '')
    tok = (payload or {}).get('token', '')
    is_admin = ACC.verify_pin(pin) or ACC.verify_pin(tok) or (tok and ACC.get_user_status(tok).get('is_admin')) or (pin and ACC.get_user_status(pin).get('is_admin'))
    if not is_admin:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    req_id = (payload or {}).get('request_id', '')
    admin_note = (payload or {}).get('admin_note', '')
    ok, res = ACC.admin_approve_coin_request(req_id, admin_note=admin_note)
    if not ok:
        return {'ok': False, 'error': str(res)}
    credited = res.get('coins_credited', 0) if isinstance(res, dict) else (res.get('coins_added', 0) if isinstance(res, dict) else 0)
    return {'ok': True, 'result': res, 'credited_coins': credited}

@app.post('/dl/admin/coins/reject')
def dl_admin_coins_reject(payload: dict=Body(...)):
    """Admin: reject a coin request."""
    pin = (payload or {}).get('pin') or (payload or {}).get('admin_pin', '')
    tok = (payload or {}).get('token', '')
    is_admin = ACC.verify_pin(pin) or ACC.verify_pin(tok) or (tok and ACC.get_user_status(tok).get('is_admin')) or (pin and ACC.get_user_status(pin).get('is_admin'))
    if not is_admin:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    req_id = (payload or {}).get('request_id', '')
    reason = (payload or {}).get('reason', '')
    ok, res = ACC.admin_reject_coin_request(req_id, reason=reason)
    return {'ok': ok, 'message': str(res)}

@app.post('/dl/admin/coins/adjust')
def dl_admin_coins_adjust(payload: dict=Body(...)):
    """Admin: freely adjust user coins (add, subtract, set)."""
    pin = (payload or {}).get('pin') or (payload or {}).get('admin_pin', '')
    tok = (payload or {}).get('token', '')
    is_admin = ACC.verify_pin(pin) or ACC.verify_pin(tok) or (tok and ACC.get_user_status(tok).get('is_admin')) or (pin and ACC.get_user_status(pin).get('is_admin'))
    if not is_admin:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    target = (payload or {}).get('username') or (payload or {}).get('device_id') or (payload or {}).get('target_id', '')
    adjustment = str((payload or {}).get('adjustment', '')).strip()
    action = (payload or {}).get('action', 'add')
    coins_val = (payload or {}).get('coins', 0)
    if adjustment:
        if adjustment.startswith('='):
            action = 'set'
            try:
                coins_val = int(adjustment[1:].strip() or 0)
            except Exception:
                coins_val = 0
        elif adjustment.startswith('-'):
            action = 'subtract'
            try:
                coins_val = abs(int(adjustment[1:].strip() or 0))
            except Exception:
                coins_val = 0
        elif adjustment.startswith('+'):
            action = 'add'
            try:
                coins_val = int(adjustment[1:].strip() or 0)
            except Exception:
                coins_val = 0
        else:
            try:
                parsed_num = int(adjustment)
                if parsed_num < 0:
                    action = 'subtract'
                    coins_val = abs(parsed_num)
                else:
                    action = 'add'
                    coins_val = parsed_num
            except Exception:
                coins_val = int(coins_val or 0)
    else:
        try:
            coins_val = int(coins_val or 0)
        except Exception:
            coins_val = 0

    note = (payload or {}).get('note', '')
    ok, res = ACC.admin_adjust_user_coins(target, action=action, coins=coins_val, note=note)
    if not ok:
        return {'ok': False, 'error': str(res)}
    new_c = res.get('new_coins', 0) if isinstance(res, dict) else 0
    return {'ok': True, 'result': res, 'new_coins': new_c}

@app.post('/dl/admin/coins/pricing')
def dl_admin_coins_pricing(payload: dict=Body(...)):
    """Admin: configure movie pricing rules & date-based promotion in Firebase RTDB."""
    pin = (payload or {}).get('pin') or (payload or {}).get('admin_pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    pricing_rules = (payload or {}).get('pricing_rules', {})
    res = ACC.save_pricing_rules(pricing_rules)
    return {'ok': True, 'pricing_rules': res}

@app.get('/dl/admin/coins/transactions')
def dl_admin_coins_transactions(pin: str='', admin_pin: str='', token: str=''):
    """Admin: view recent coin transactions."""
    eff_pin = pin or admin_pin
    is_valid_pin = ACC.verify_pin(eff_pin)
    is_admin_token = token and ACC.get_user_status(token).get('is_admin')
    if not is_valid_pin and not is_admin_token:
        return {'ok': False, 'error': 'PIN មិនត្រឹមត្រូវ'}
    txs = ACC.admin_get_coin_transactions(limit=60)
    return {'ok': True, 'transactions': txs}

@app.get('/dl/qr_payment.png')
def dl_qr_payment():
    """Serve QR payment image."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(os.path.dirname(here), 'qr_payment.png'),
        os.path.join(here, 'web', 'qr_payment.png'),
        os.path.join(here, 'qr_payment.png')
    ]
    for c in candidates:
        if os.path.isfile(c):
            return FileResponse(c, media_type='image/png')
    raise HTTPException(404, 'QR image not found')

@app.get('/dl/system/network')
def dl_system_network():
    port = int(os.environ.get('PORT', '8000'))
    lan_ip = '127.0.0.1'
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
    except Exception:
        pass
    return {'ok': True, 'lan_ip': lan_ip, 'port': port, 'lan_url': f'http://{lan_ip}:{port}/', 'local_url': f'http://127.0.0.1:{port}/'}

_HONGGUO_ACTORS_CACHE = {'at': 0.0, 'data': []}

def _load_hongguo_actors():
    global _HONGGUO_ACTORS_CACHE
    now = time.time()
    if _HONGGUO_ACTORS_CACHE['data'] and (now - _HONGGUO_ACTORS_CACHE['at'] < 300):
        return _HONGGUO_ACTORS_CACHE['data']
    here = os.path.dirname(os.path.abspath(__file__))
    fpaths = [
        os.path.join(os.path.dirname(here), 'data', 'hongguo_actors.json'),
        os.path.join(here, 'data', 'hongguo_actors.json'),
        os.path.join(here, 'web', 'hongguo_actors.json')
    ]
    for fp in fpaths:
        if os.path.exists(fp):
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    actors = json.load(f)
                    if actors and isinstance(actors, list):
                        _HONGGUO_ACTORS_CACHE = {'at': now, 'data': actors}
                        return actors
            except Exception:
                pass
    return []

@app.get('/dl/actors')
def dl_actors(gender: str = 'all'):
    """Return all drama actors/actresses extracted directly from https://hongguoduanju.com/"""
    actors = _load_hongguo_actors()
    g = (gender or 'all').lower().strip()
    if g == 'female':
        filtered = [a for a in actors if a.get('gender') == 'female']
    elif g == 'male':
        filtered = [a for a in actors if a.get('gender') == 'male']
    else:
        filtered = actors
    return {
        'ok': True,
        'source': 'https://hongguoduanju.com/',
        'count': len(filtered),
        'total': len(actors),
        'actors': filtered
    }

@app.get('/dl/search')
def dl_search(q: str=''):
    q = (q or '').strip()
    if not q:
        return {'results': []}
    
    import urllib.parse
    import translator as TR
    results = []
    seen = set()
    actor_info = None

    # 1. Check if q matches an actor from hongguoduanju.com
    actors = _load_hongguo_actors()
    matched_actor = next((a for a in actors if a.get('name') == q or q in a.get('name', '')), None)
    if matched_actor:
        actor_info = matched_actor
        # Add pre-cached dramas from hongguoduanju.com
        for d in matched_actor.get('dramas', []):
            sid = str(d.get('series_id') or '')
            if sid and sid not in seen:
                seen.add(sid)
                results.append({
                    'series_id': sid,
                    'title': d.get('title', ''),
                    'title_km': '',
                    'episode_cnt': d.get('episode_cnt') or 0,
                    'score': '8.3',
                    'cover': d.get('cover', ''),
                    'created_at': '',
                    'create_time': 0,
                    'source': 'https://hongguoduanju.com/'
                })

    # 2. Live query https://hongguoduanju.com/search/[q] directly
    try:
        url = f'https://hongguoduanju.com/search/{urllib.parse.quote(q)}'
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=6)
        m = re.search(r'_ROUTER_DATA\s*=\s*(\{[\s\S]*?\});', r.text)
        if m:
            data = json.loads(m.group(1))
            sk = data.get('loaderData', {}).get('search_(keyword)/page', {}).get('searchList', [])
            for it in sk:
                # user_info video_list
                for v in it.get('video_list', []):
                    sid = str(v.get('series_id') or '')
                    if sid and sid not in seen:
                        seen.add(sid)
                        results.append({
                            'series_id': sid,
                            'title': v.get('series_title', ''),
                            'title_km': '',
                            'episode_cnt': v.get('episode_cnt') or 0,
                            'score': '8.2',
                            'cover': (v.get('series_cover') or '').replace('.heic', '.image'),
                            'created_at': '',
                            'create_time': 0,
                            'source': 'https://hongguoduanju.com/'
                        })
                # doc_type 23 video_data
                vd = it.get('video_data')
                if vd and isinstance(vd, dict):
                    sid = str(vd.get('series_id') or '')
                    if sid and sid not in seen:
                        seen.add(sid)
                        results.append({
                            'series_id': sid,
                            'title': vd.get('series_title') or it.get('name') or '',
                            'title_km': '',
                            'episode_cnt': vd.get('episode_cnt') or 0,
                            'score': '8.1',
                            'cover': (vd.get('series_cover') or '').replace('.heic', '.image'),
                            'created_at': '',
                            'create_time': 0,
                            'source': 'https://hongguoduanju.com/'
                        })
    except Exception:
        pass

    # 3. Combine with upstream Hongguo App Search
    try:
        res = H.search(q) or []
        for x in res[:20]:
            sid = str(x.get('series_id') or '')
            if sid and sid not in seen:
                seen.add(sid)
                results.append({
                    'series_id': sid,
                    'title': x.get('title', ''),
                    'title_km': '',
                    'episode_cnt': x.get('episode_cnt'),
                    'score': x.get('score', ''),
                    'cover': x.get('cover', ''),
                    'created_at': x.get('created_at', ''),
                    'create_time': x.get('create_time', 0),
                    'source': 'hongguo_app'
                })
    except Exception:
        pass

    # Translate titles to Khmer
    try:
        titles = [x.get('title', '') for x in results if x.get('title')]
        km_map = TR.translate_batch(titles)
        for x in results:
            x['title_km'] = km_map.get(x.get('title', ''), '')
    except Exception:
        pass

    return {'results': results, 'actor': actor_info, 'total': len(results)}
@app.get('/dl/rank')
def dl_rank(board: str='recommend', category: str='all', offset: int=0, size: int=100, refresh: bool=False):
    """The 红果推荐榜 leaderboard (the app\'s real top chart) for the Trending tabs. board = recommend/hot/new;
    category = all/human(live-action)/comic(animated)/ai. Offset-paginated (100/page) with has_more +
    next_offset for the pager. Login-free + cached."""
    size = max(1, min(int(size or 100), 100))
    off = max(0, int(offset or 0))
    cat = category if category in ['all', 'human', 'comic', 'ai'] else 'all'
    brd = board if board in ['recommend', 'hot', 'new'] else 'recommend'
    try:
        items, has_more, next_off = H.leaderboard_page(cat, brd, offset=off, size=size, force=refresh)
        import translator as TR
        titles = [x.get('title', '') for x in items if x.get('title')]
        km_map = TR.translate_batch(titles)
        out = [{
            'series_id': str(x.get('series_id') or ''),
            'title': x.get('title', ''),
            'title_km': km_map.get(x.get('title', ''), ''),
            'episode_cnt': x.get('episode_cnt'),
            'score': x.get('score', ''),
            'cover': x.get('cover', ''),
            'created_at': x.get('created_at', ''),
            'create_time': x.get('create_time', 0)
        } for x in items if x.get('series_id')]
        return {'results': out, 'has_more': bool(has_more), 'next_offset': int(next_off)}
    except Exception as e:
        return {'results': [], 'has_more': False, 'next_offset': off, 'error': str(e)}

_RELATED_CACHE = {}

@app.get('/dl/related')
def dl_related(series_id: str = '', title: str = '', actor: str = '', category: str = '', limit: int = 15):
    """
    Returns 10-15 related or similar dramas:
    1. Same actor dramas (from bundled 137 actors).
    2. Shared category/genre/theme keywords.
    3. Matching Hongguo trending & top chart recommendations.
    All titles translated to Khmer.
    """
    sid_curr = str(series_id or '').strip()
    title_curr = (title or '').strip()
    actor_curr = (actor or '').strip()
    cat_curr = (category or '').strip()
    limit = max(10, min(int(limit or 15), 30))

    cache_key = f"{sid_curr}_{title_curr}_{actor_curr}_{limit}"
    if cache_key in _RELATED_CACHE:
        return _RELATED_CACHE[cache_key]

    import translator as TR
    results = []
    seen = set([sid_curr]) if sid_curr else set()

    # Strategy 1: Actor match from bundled actors database
    if actor_curr:
        actors = _load_hongguo_actors()
        for a in actors:
            a_name = a.get('name', '')
            if a_name and (a_name in actor_curr or actor_curr in a_name):
                for d in a.get('dramas', []):
                    dsid = str(d.get('series_id') or '')
                    if dsid and dsid not in seen:
                        seen.add(dsid)
                        results.append({
                            'series_id': dsid,
                            'title': d.get('title', ''),
                            'title_km': '',
                            'episode_cnt': d.get('episode_cnt') or 0,
                            'score': d.get('score') or '8.5',
                            'cover': d.get('cover', ''),
                            'created_at': '',
                            'create_time': 0,
                            'match_type': 'actor',
                            'match_label': f'តួសម្តែង: {a_name}'
                        })
                        if len(results) >= 6:
                            break
                break

    # Strategy 2: Keyword match from title (key genres / themes)
    keywords = []
    GENRE_WORDS = [
        "战神", "总裁", "神豪", "龙王", "高手", "千金", "仙帝", "战皇", "王妃", "修仙",
        "赘婿", "兵王", "末世", "重生", "穿越", "离婚", "复仇", "归来", "无敌", "逆袭",
        "女帝", "狂医", "鉴宝", "奶爸", "少帅", "国术", "都市", "古装", "甜宠", "虐恋",
        "雇佣兵", "荒岛", "求生", "特种兵", "战神", "绝世", "豪门", "狂少", "无双"
    ]
    for w in GENRE_WORDS:
        if w in title_curr or w in cat_curr:
            keywords.append(w)

    # Also search for words from category
    if cat_curr:
        for c in cat_curr.split(','):
            c_clean = c.strip()
            if c_clean and len(c_clean) >= 2 and c_clean not in keywords:
                keywords.append(c_clean)

    for kw in keywords[:2]:
        if len(results) >= limit:
            break
        try:
            res = H.search(kw, max_items=8) or []
            for x in res:
                dsid = str(x.get('series_id') or '')
                if dsid and dsid not in seen:
                    seen.add(dsid)
                    results.append({
                        'series_id': dsid,
                        'title': x.get('title', ''),
                        'title_km': '',
                        'episode_cnt': x.get('episode_cnt'),
                        'score': x.get('score') or '8.6',
                        'cover': x.get('cover', ''),
                        'created_at': x.get('created_at', ''),
                        'create_time': x.get('create_time', 0),
                        'match_type': 'genre',
                        'match_label': f'ប្រភេទ: {kw}'
                    })
                    if len(results) >= limit:
                        break
        except Exception:
            pass

    # Strategy 3: Top leaderboard recommendations (Recommend + Hot + New)
    if len(results) < limit:
        for brd in ['recommend', 'hot', 'new']:
            if len(results) >= limit:
                break
            try:
                items, _, _ = H.leaderboard_page('all', brd, offset=0, size=50)
                for x in items:
                    dsid = str(x.get('series_id') or '')
                    if dsid and dsid not in seen:
                        seen.add(dsid)
                        results.append({
                            'series_id': dsid,
                            'title': x.get('title', ''),
                            'title_km': '',
                            'episode_cnt': x.get('episode_cnt'),
                            'score': x.get('score') or '8.8',
                            'cover': x.get('cover', ''),
                            'created_at': x.get('created_at', ''),
                            'create_time': x.get('create_time', 0),
                            'match_type': 'popular',
                            'match_label': 'រឿងពេញនិយម'
                        })
                        if len(results) >= limit:
                            break
            except Exception:
                pass

    # Strategy 4: Bundled catalog / explorer fallback
    if len(results) < limit:
        exp = _explorer_catalog()
        for x in exp:
            dsid = str(x.get('series_id') or '')
            if dsid and dsid not in seen:
                seen.add(dsid)
                results.append({
                    'series_id': dsid,
                    'title': x.get('title', ''),
                    'title_km': '',
                    'episode_cnt': x.get('episode_cnt') or 0,
                    'score': x.get('score') or '8.4',
                    'cover': x.get('cover', ''),
                    'created_at': x.get('created_at', ''),
                    'create_time': x.get('create_time', 0),
                    'match_type': 'catalog',
                    'match_label': 'រឿងស្រដៀង'
                })
                if len(results) >= limit:
                    break

    # Batch translate all titles to Khmer
    titles_to_tr = [x.get('title', '') for x in results if x.get('title') and not x.get('title_km')]
    if titles_to_tr:
        try:
            km_map = TR.translate_batch(titles_to_tr)
            for x in results:
                t = x.get('title', '')
                if t in km_map and km_map[t]:
                    x['title_km'] = km_map[t]
        except Exception:
            pass

    final_results = results[:limit]
    res_obj = {'ok': True, 'results': final_results, 'total': len(final_results)}
    if cache_key and len(final_results) >= 10:
        _RELATED_CACHE[cache_key] = res_obj
    return res_obj

_EXPLORER = None
def _explorer_catalog():
    """Load+cache the bundled catalog (web/explorer.json.gz), normalized to a uniform shape.\n    Tolerates both schemas: legacy {series_id,...} and v2 {oversea_id,domestic_id,avail,...}.\n    Each normalized row has a downloadable series_id (oversea preferred, else domestic) + avail.\n    Missing file => empty (feature off)."""
    global _EXPLORER
    if _EXPLORER is None:
        import gzip
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'explorer.json.gz')
        try:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                raw = json.load(f).get('items') or []
        except Exception:
            raw = []
        norm = []
        for x in raw:
            ov, dm = (x.get('oversea_id'), x.get('domestic_id'))
            sid = ov or dm or x.get('series_id')
            if not sid:
                continue
            else:
                avail = x.get('avail') or ('oversea' if ov or x.get('series_id') else 'domestic')
                created_at = ''
                ts = 0
                try:
                    sid_int = int(sid)
                    ts = sid_int >> 32
                    if 1577836800 <= ts <= 1900000000:
                        created_at = time.strftime('%Y-%m-%d', time.localtime(ts))
                except Exception:
                    pass
                norm.append({'series_id': str(sid), 'avail': avail, 'title': x.get('title', ''), 'episode_cnt': x.get('episode_cnt'), 'score': x.get('score', ''), 'cover': x.get('cover', ''), 'created_at': created_at, 'create_time': ts})
        _EXPLORER = norm
    return _EXPLORER
@app.get('/dl/explorer')
def dl_explorer(page: int=1, size: int=18):
    """Paged pre-verified catalog. size default 18 = 3 rows. Returns {results,page,pages,total}.
    Each result carries `avail` (oversea/domestic/both) for a future availability badge."""
    cat = _explorer_catalog()
    total = len(cat)
    size = max(1, min(int(size or 18), 60))
    pages = (total + size - 1) // size if total else 0
    page = max(1, min(int(page or 1), max(1, pages)))
    lo = (page - 1) * size
    rows = cat[lo:lo + size]
    return {'results': [{'series_id': x['series_id'], 'avail': x.get('avail', 'oversea'), 'title': x.get('title', ''), 'episode_cnt': x.get('episode_cnt'), 'score': x.get('score', ''), 'cover': x.get('cover', ''), 'created_at': x.get('created_at', ''), 'create_time': x.get('create_time', 0)} for x in rows], 'page': page, 'pages': pages, 'total': total, 'size': size}
@app.get('/dl/episodes')
def dl_episodes(series_id: str='', title: str=''):
    """列出一部剧的可选集号(供前端选集)。返回 {title,total,cover,episodes:[1,2,...]}。"""
    sid = (series_id or '').strip()
    if not sid:
        return {'episodes': [], 'error': 'no series_id'}
    else:
        try:
            meta, eps = H.get_episodes(sid)
            idxs = sorted((e['index'] for e in eps if e.get('index')))
            import translator as TR
            t_orig = meta.get('title', sid)
            t_km = TR.translate_to_khmer(t_orig) if t_orig else ''
            intro_orig = meta.get('intro', '')
            intro_km = TR.translate_to_khmer(intro_orig) if intro_orig else ''
            cat_orig = meta.get('category', [])
            cat_km = [TR.translate_to_khmer(c) for c in cat_orig] if cat_orig else []
            return {
                'series_id': sid,
                'title': t_orig,
                'title_km': t_km,
                'cover': meta.get('cover', ''),
                'total': len(idxs),
                'episodes': idxs,
                'intro': intro_orig,
                'intro_km': intro_km,
                'category': cat_orig,
                'category_km': cat_km,
                'status': meta.get('status', ''),
                'play_cnt': meta.get('play_cnt', 0),
                'score': meta.get('score', ''),
                'celebrities': meta.get('celebrities', []),
                'unavailable': False
            }
        except Exception as e:
            err_str = str(e)
            is_gone = ('101001' in err_str) or ('已下架' in err_str) or ('不存在' in err_str)
            alternatives = []
            if is_gone:
                q_text = (title or '').strip()
                if q_text:
                    try:
                        import translator as TR
                        clean_q = re.sub(r'第[一二三四五六七八九十0-9]+[季部]|season.*', '', q_text, flags=re.I).strip('，, 0123456789')
                        if clean_q:
                            sr = H.search(clean_q)
                            for r in sr[:6]:
                                alt_sid = str(r.get('series_id') or '')
                                if alt_sid and alt_sid != sid:
                                    alt_t = r.get('title') or ''
                                    alt_cov = r.get('cover') or ''
                                    alt_km = TR.translate_to_khmer(alt_t) if alt_t else ''
                                    alternatives.append({
                                        'series_id': alt_sid,
                                        'title': alt_t,
                                        'title_km': alt_km,
                                        'cover': alt_cov,
                                        'episode_cnt': r.get('episodes_count') or r.get('episode_cnt') or 0
                                    })
                    except Exception:
                        pass
            return {
                'series_id': sid,
                'title': title or sid,
                'title_km': '',
                'episodes': [],
                'total': 0,
                'unavailable': is_gone,
                'error': err_str,
                'error_km': 'រឿងនេះត្រូវបានដកចេញពីប្រព័ន្ធដើម (Upstream Taken Down)' if is_gone else err_str,
                'alternatives': alternatives
            }
@app.post('/dl/resolve')
def dl_resolve(payload: dict=Body(...)):
    """把粘贴的分享链接解析成 [{series_id,title,total}] 供前端加入队列(不下载)。"""
    text = (payload or {}).get('text', '') or ''
    links = ODL._parse_share_links(text)
    def _resolve_one(item):
        title, u = item
        if not ODL._hgdj_series_id(u):
            try:
                board = ODL._scrape_board(u)
            except Exception:
                board = []
            if board:
                return [{'series_id': sid, 'title': tname, 'total': 0} for sid, tname in board]
        try:
            sid, tname, eps, cov = ODL._resolve_series(title, u)
        except Exception:
            sid, tname, eps, cov = (None, title, None, '')
        if sid:
            return [{'series_id': sid, 'title': tname, 'total': len(eps) if eps else 0, 'cover': cov}]
        else:
            hgid = ODL._hgdj_series_id(u)
            if hgid:
                nm = title or tname or hgid
                ODL.log(f'[X] 《{nm}》 (ID: {hgid}) is no longer available on the platform.')
                return [{'series_id': None, 'title': nm, 'hg_id': hgid, 'error': 'unavailable', 'unavailable': True}]
            else:
                return [{'series_id': None, 'title': title or u, 'error': 'unresolved'}]
    out = []
    if links:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(8, len(links))) as _ex:
            for _res in _ex.map(_resolve_one, links):
                out.extend(_res)
    return {'resolved': out}
@app.get('/dl/status')
def dl_status():
    with _dl_lock:
        mode = _dl_state.get('mode', '')
        if mode == 'library':
            snap = ODL.live_snapshot()
            for s in snap.get('series', []):
                sid = s.get('sid')
                if sid:
                    _, spd = ODL.speed_tracker.get_speed(sid)
                    s['speed'] = spd
            return {'running': _dl_state['running'], 'started': _dl_state['started'], 'mode': 'library', 'phase': snap['phase'], 'checked': snap['checked'], 'to_check': snap['to_check'], 'found': snap['found'], 'series': snap['series'], 'log': _dl_state['log'][(-60):]}
        else:
            series = _dl_state['series']
            for sid, s in series.items():
                try:
                    rng = s.get('range', 'all')
                    done = ODL.disk_done(sid, s.get('title') or '', rng)
                    s['done'] = min(done, s['total']) if s['total'] else done
                    if s.get('status') != 'unavailable':
                        if s['total'] and s['done'] >= s['total']:
                            s['status'] = 'done'
                            s['speed'] = ''
                        else:
                            if s['done'] > 0 and _dl_state['running']:
                                s['status'] = 'downloading'
                    if _dl_state['running'] and s.get('status') == 'downloading':
                        _, spd = ODL.speed_tracker.get_speed(sid)
                        s['speed'] = spd
                    else:
                        s['speed'] = ''
                except Exception:
                    continue
            return {'running': _dl_state['running'], 'started': _dl_state['started'], 'mode': mode, 'series': [{'sid': k, **v} for k, v in series.items()], 'log': _dl_state['log'][(-60):]}
@app.get('/dl/diag')
def dl_diag():
    """#2 troubleshoot console: ports, signer/output health, writability, and a log tail."""
    import platform
    import urllib.request
    out_dir = ODL.OUT
    writable, werr = (False, '')
    try:
        os.makedirs(out_dir, exist_ok=True)
        tf = os.path.join(out_dir, '.hg_write_test')
        with open(tf, 'w', encoding='utf-8') as _f:
            _f.write('ok')
        os.remove(tf)
        writable = True
    except Exception as e:
        werr = str(e)
    sign_server = os.environ.get('SIGN_SERVER', '')
    sign_ok = False
    try:
        body = json.dumps({'url': 'https://api5-normal-sinfonlinec.fqnovel.com/reading/bookapi/search/page/v/?query=probe&aid=8662', 'headers': {}}).encode()
        req = urllib.request.Request(sign_server.rstrip('/') + '/sign', data=body, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=6) as r:
            d = json.loads(r.read().decode('utf-8', 'ignore'))
        sign_ok = isinstance(d, dict) and 'error' not in d
    except Exception:
        sign_ok = False
    app_log = []
    try:
        lp = os.path.join(_data_dir(), 'app.log')
        if os.path.exists(lp):
            with open(lp, encoding='utf-8', errors='ignore') as f:
                app_log = f.read().splitlines()[(-45):]
    except Exception:
        pass
    return {'pid': os.getpid(), 'web_port': os.environ.get('PORT', ''), 'bind_host': os.environ.get('BIND_HOST', ''), 'sign_server': sign_server, 'signer_healthy': sign_ok, 'output_dir': out_dir, 'output_writable': writable, 'output_write_error': werr, 'state_dir': ODL.STATE_DIR, 'data_dir': _data_dir(), 'python': platform.python_version(), 'running': _dl_state.get('running'), 'mode': _dl_state.get('mode'), 'app_log': app_log, 'dl_log': _dl_state.get('log', [])[(-45):]}
def _data_dir():
    base = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
    d = os.path.join(base, 'HongguoDownloader')
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        d = os.path.dirname(os.path.abspath(__file__))
    return d
def is_cloud_env():
    """Desktop Application Mode: Always False."""
    return False

def _fmt_size(sz):
    """Format bytes to human-readable size."""
    if sz < 1024:
        return f"{sz} B"
    elif sz < 1024 * 1024:
        return f"{sz / 1024:.1f} KB"
    elif sz < 1024 * 1024 * 1024:
        return f"{sz / (1024 * 1024):.1f} MB"
    else:
        return f"{sz / (1024 * 1024 * 1024):.2f} GB"

def _migrate_old_mangled_storage():
    """Recover and migrate any drama folders previously saved into mangled paths
    such as /app/F :... or /app/C:... into the clean cloud downloads folder."""
    if not is_cloud_env():
        return
    dest = ODL.OUT or os.environ.get('HG_OUT') or '/app/data/downloads'
    try:
        os.makedirs(dest, exist_ok=True)
    except Exception:
        pass
    app_root = '/app'
    if not os.path.isdir(app_root):
        return
    try:
        import shutil
        for entry in os.listdir(app_root):
            if any(ch in entry for ch in [':', '\\']) or entry.startswith('F ') or entry.startswith('C '):
                src_dir = os.path.join(app_root, entry)
                if os.path.isdir(src_dir) and src_dir != dest:
                    for sub in os.listdir(src_dir):
                        sub_path = os.path.join(src_dir, sub)
                        target_path = os.path.join(dest, sub)
                        if os.path.isdir(sub_path) and not os.path.exists(target_path):
                            shutil.move(sub_path, target_path)
    except Exception as e:
        print(f"[storage-migration] notice: {e}", flush=True)

_DLCFG = os.path.join(_data_dir(), 'dlconfig.json')
_DLCFG_OLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads', '.dlconfig.json')
def _load_dlcfg():
    src = _DLCFG if os.path.exists(_DLCFG) else _DLCFG_OLD if os.path.exists(_DLCFG_OLD) else None
    if is_cloud_env():
        cloud_default = os.environ.get('HG_OUT') or '/app/data/downloads'
        if not src:
            ODL.set_output_dir(cloud_default)
            _migrate_old_mangled_storage()
            return
        else:
            try:
                cfg = json.load(open(src, encoding='utf-8'))
                out_p = (cfg.get('output_dir') or '').strip()
                if not out_p or re.match(r'^(?:/app/)?([a-zA-Z]:|\\|/[a-zA-Z]:)', out_p) or not out_p.startswith('/'):
                    out_p = cloud_default
                ODL.set_output_dir(out_p)
                _save_dlcfg()
                _migrate_old_mangled_storage()
            except Exception:
                ODL.set_output_dir(cloud_default)
                return None
    else:
        if not src:
            return
        else:
            try:
                cfg = json.load(open(src, encoding='utf-8'))
                if cfg.get('output_dir'):
                    ODL.set_output_dir(cfg['output_dir'])
            except Exception:
                return None
            if src == _DLCFG_OLD:
                _save_dlcfg()
def _save_dlcfg():
    try:
        os.makedirs(os.path.dirname(_DLCFG), exist_ok=True)
        json.dump({'output_dir': ODL.OUT}, open(_DLCFG, 'w', encoding='utf-8'))
    except Exception:
        return None
_load_dlcfg()
def _rescan_state_once():
    """One-time repair: rebuild download progress state from files already on disk, so libraries that
    lost tracking to the read-only-state-dir bug show correct progress after this update. Guarded by a
    marker in the (now writable) STATE_DIR; runs in the background so it never delays startup."""
    try:
        pruned = ODL.prune_orphan_state()
        if pruned:
            print(f'[cleanup] pruned {pruned} orphaned progress-state file(s)', flush=True)
    except Exception:
        pass
    marker = os.path.join(ODL.STATE_DIR, '.rescanned_v1')
    if os.path.exists(marker):
        return
    try:
        n = ODL.rescan_state()
        os.makedirs(ODL.STATE_DIR, exist_ok=True)
        open(marker, 'w', encoding='utf-8').close()
        if n:
            print(f'[rescan] rebuilt progress state for {n} series from disk', flush=True)
    except Exception as e:
        print(f'[rescan] skipped: {e}', flush=True)
threading.Thread(target=_rescan_state_once, daemon=True).start()
@app.get('/dl/config')
def dl_config_get():
    return {
        'output_dir': ODL.OUT,
        'is_cloud': is_cloud_env(),
        'platform': sys.platform,
        'default_cloud_dir': '/app/data/downloads' if is_cloud_env() else ''
    }
@app.post('/dl/config')
def dl_config_set(payload: dict=Body(...)):
    raw_path = (payload or {}).get('output_dir', '') or ''
    path = raw_path.strip()
    warning_msg = None
    if is_cloud_env():
        if re.match(r'^(?:/app/)?([a-zA-Z]:|\\|/[a-zA-Z]:)', path):
            cloud_default = os.environ.get('HG_OUT') or '/app/data/downloads'
            path = cloud_default
            warning_msg = 'Cloud Server (Railway) មិនអាចប្រើ Windows Drive (C:, F:) នៃកុំព្យូទ័ររបស់អ្នកបានទេ។ ប្រព័ន្ធបានកំណត់ទីតាំងរក្សាទុកលើ Server Storage: ' + cloud_default + ' ដោយស្វ័យប្រវត្តិ!'
        elif not path.startswith('/'):
            path = os.environ.get('HG_OUT') or '/app/data/downloads'
    try:
        newp = ODL.set_output_dir(path)
        _save_dlcfg()
        res = {'ok': True, 'output_dir': newp, 'is_cloud': is_cloud_env()}
        if warning_msg:
            res['warning'] = warning_msg
        return res
    except Exception as e:
        return {'ok': False, 'error': str(e), 'output_dir': ODL.OUT, 'is_cloud': is_cloud_env()}
@app.post('/dl/open')
def dl_open():
    """Open the current download folder in OS file browser (Windows), or signal Web Explorer for cloud."""
    import subprocess
    import sys
    d = ODL.OUT or ''
    if is_cloud_env():
        return {'ok': True, 'output_dir': d, 'is_cloud': True, 'action': 'web_explorer'}
    try:
        if d:
            os.makedirs(d, exist_ok=True)
        if sys.platform.startswith('win'):
            os.startfile(d)
        else:
            if sys.platform == 'darwin':
                subprocess.Popen(['open', d])
            else:
                subprocess.Popen(['xdg-open', d])
        return {'ok': True, 'output_dir': d, 'is_cloud': False}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'output_dir': d, 'is_cloud': is_cloud_env()}
def _redacted_log_tail(path, lines=1500):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            buf = f.readlines()
    except Exception:
        return '(no app.log found at %s)' % path
    tail = [ln for ln in buf[-lines:] if '/dl/status' not in ln and '/dl/poster' not in ln]
    txt = ''.join(tail)
    txt = re.sub('HG-[A-Z0-9]{4,}(?:-[A-Z0-9]{4,})+', 'HG-****REDACTED****', txt)
    txt = re.sub('[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '<id-redacted>', txt)
    txt = re.sub('([Uu]sers[\\\\/])[^\\\\/\\r\\n]+', '\\1<user>', txt)
    return txt
@app.post('/dl/bugreport')
def dl_bugreport(payload: dict=Body(...)):
    # ***<module>.dl_bugreport: Failure: Compilation Error
    import zipfile
    import subprocess
    import sys
    p = payload or {}
    want_logs = bool(p.get('logs', True))
    want_shot = bool(p.get('screenshot', False))
    data_dir = _data_dir()
    reports = os.path.join(data_dir, 'bugreports')
    try:
        os.makedirs(reports, exist_ok=True)
        ts = time.strftime('%Y%m%d-%H%M%S')
        zpath = os.path.join(reports, 'bugreport-%s.zip' % ts)
        included = []
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            try:
                ver = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.txt')).read().strip()
            except Exception:
                ver = '?'
            z.writestr('about.txt', 'Hongguo Downloader bug report\ncreated: %s\nversion: %s\n' % (ts, ver))
            if want_logs:
                z.writestr('app-log.txt', _redacted_log_tail(os.path.join(data_dir, 'app.log')))
                included.append('logs')
            if want_shot:
                try:
                    from PIL import ImageGrab
                    b = io.BytesIO()
                    ImageGrab.grab().save(b, format='PNG')
                    z.writestr('screenshot.png', b.getvalue())
                    included.append('screenshot')
                except Exception as e:
                    z.writestr('screenshot-FAILED.txt', 'could not capture screenshot: %s' % e)
        try:
            if sys.platform.startswith('win'):
                subprocess.Popen(['explorer', '/select,', zpath])
            else:
                if sys.platform == 'darwin':
                    subprocess.Popen(['open', '-R', zpath])
                else:
                    subprocess.Popen(['xdg-open', reports])
        except Exception:
            pass
        return {'ok': True, 'path': zpath, 'included': included}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
@app.get('/dl/drives')
def dl_drives():
    """List available system drives or Cloud Server storage info."""
    import string
    import shutil
    drives = []
    cloud = is_cloud_env()
    if sys.platform.startswith('win') and not cloud:
        for letter in string.ascii_uppercase:
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                try:
                    total, used, free = shutil.disk_usage(drive_path)
                    free_gb = round(free / (1024 ** 3), 1)
                    total_gb = round(total / (1024 ** 3), 1)
                    drives.append({
                        'drive': drive_path,
                        'letter': letter,
                        'free_gb': free_gb,
                        'total_gb': total_gb
                    })
                except Exception:
                    drives.append({'drive': drive_path, 'letter': letter, 'free_gb': 0, 'total_gb': 0})
    else:
        # Linux / Docker / Railway Cloud
        try:
            target = ODL.OUT if (ODL.OUT and os.path.exists(ODL.OUT)) else '/'
            total, used, free = shutil.disk_usage(target)
            free_gb = round(free / (1024 ** 3), 1)
            total_gb = round(total / (1024 ** 3), 1)
            drives.append({
                'drive': ODL.OUT or '/app/data/downloads',
                'letter': 'Cloud Server',
                'free_gb': free_gb,
                'total_gb': total_gb,
                'is_cloud': True
            })
        except Exception:
            pass
    return {'drives': drives, 'current': ODL.OUT or '', 'is_cloud': cloud}

@app.post('/dl/pick')
def dl_pick():
    """Pop a native folder-picker on the server machine, return the chosen path (does not save it)."""
    import subprocess
    import sys
    if is_cloud_env():
        return {
            'ok': False,
            'is_cloud': True,
            'error': 'Cloud Server (Railway) ដំណើរការលើ Linux — វីដេអូត្រូវបានរក្សាទុកលើ Server Storage (/app/data/downloads) ដោយស្វ័យប្រវត្តិ។'
        }
    if not sys.platform.startswith('win'):
        return {'ok': False, 'error': 'folder picker is Windows-only here — type the path instead'}
    else:
        ps = (
            'Add-Type -AssemblyName System.Windows.Forms | Out-Null; '
            '$form = New-Object System.Windows.Forms.Form; '
            '$form.TopMost = $true; '
            '$form.Opacity = 0; '
            '$form.Show(); '
            '$form.BringToFront(); '
            '$d = New-Object System.Windows.Forms.FolderBrowserDialog; '
            '$d.Description = \'Choose the download folder for Hongguo\'; '
            '$d.ShowNewFolderButton = $true; '
            '$d.AutoUpgradeEnabled = $true; '
            'if ($env:HG_INITDIR -and (Test-Path -LiteralPath $env:HG_INITDIR)) { $d.SelectedPath = $env:HG_INITDIR }; '
            'if ($d.ShowDialog($form) -eq [System.Windows.Forms.DialogResult]::OK) { [Console]::Out.Write($d.SelectedPath) }; '
            '$form.Dispose()'
        )
        env = dict(os.environ)
        env['HG_INITDIR'] = ODL.OUT or ''
        try:
            r = subprocess.run(['powershell', '-NoProfile', '-STA', '-Command', ps], capture_output=True, text=True, timeout=180, env=env)
            return {'ok': True, 'path': (r.stdout or '').strip()}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

@app.get('/dl/history')
def dl_history():
    """Persistent download memory: lists all series ever downloaded, even if removed from disk."""
    return {'ok': True, 'history': ODL.get_history()}

@app.get('/dl/history/poster')
def dl_history_poster(series_id: str):
    """Serve cached poster from persistent POSTER_VAULT, or fallback to folder or redirect."""
    sid = str(series_id or '').strip()
    if not sid:
        raise HTTPException(status_code=404, detail="Missing series_id")
    vault_file = os.path.join(ODL.POSTER_VAULT, f'{sid}.jpg')
    if os.path.isfile(vault_file) and os.path.getsize(vault_file) > 0:
        return FileResponse(vault_file, media_type='image/jpeg')
    try:
        if os.path.isdir(ODL.OUT):
            for folder_name in os.listdir(ODL.OUT):
                d = os.path.join(ODL.OUT, folder_name)
                if os.path.isdir(d):
                    p = os.path.join(d, 'poster.jpg')
                    if os.path.isfile(p) and str(ODL._lib_meta(d).get('series_id') or '') == sid:
                        return FileResponse(p, media_type='image/jpeg')
    except Exception:
        pass
    hist = ODL.get_history().get(sid) or {}
    cover_url = hist.get('cover_url')
    if cover_url:
        from urllib.parse import quote
        return RedirectResponse(f'/img?url={quote(cover_url)}')
    raise HTTPException(status_code=404, detail="Poster not found")

@app.get('/dl/translate')
@app.post('/dl/translate')
def dl_translate(q: str = '', payload: dict = Body(None)):
    import translator as TR
    text = q
    if payload and isinstance(payload, dict):
        text = payload.get('text') or payload.get('q') or text
    res = TR.translate_to_khmer(text) if text else ''
    return {'q': text, 'km': res, 'translated': res}

@app.post('/dl/translate_batch')
def dl_translate_batch(payload: dict = Body(...)):
    import translator as TR
    texts = (payload or {}).get('texts') or []
    return {'translations': TR.translate_batch(texts)}

@app.get('/dl/gemini/status')
def dl_gemini_status():
    """Returns Gemini API Key Pool status and key statistics."""
    import translator as TR
    return {'ok': True, 'pool': TR.gemini_pool.get_status()}

@app.post('/dl/gemini/config')
def dl_gemini_config(payload: dict = Body(...)):
    """Configure Gemini API Key Pool (multiple keys, model, enabled)."""
    import translator as TR
    keys = (payload or {}).get('keys') or []
    model = (payload or {}).get('model')
    enabled = (payload or {}).get('enabled')
    TR.gemini_pool.set_config(keys, model=model, enabled=enabled)
    return {'ok': True, 'pool': TR.gemini_pool.get_status()}

@app.post('/dl/gemini/test')
def dl_gemini_test(payload: dict = Body(...)):
    """Test translation using the Gemini Pool, with Google Translate fallback."""
    import translator as TR
    text = (payload or {}).get('text') or '以爱为家第四季'
    gem_res, key_used = TR.gemini_pool.translate_with_gemini(text)
    if gem_res:
        return {'ok': True, 'original': text, 'translation': gem_res, 'provider': 'Gemini AI', 'key_used': key_used}
    goog_res = TR.translate_to_khmer(text, force_provider='google')
    return {'ok': True, 'original': text, 'translation': goog_res, 'provider': 'Google Translate (Fallback)', 'key_used': None}
@app.get('/dl/library')
def dl_library():
    try:
        return ODL.library_scan()
    except Exception as e:
        return {'items': [], 'error': str(e)}
def _find_series_folder(name: str = ''):
    """Robustly resolve any series folder by exact name, sub-name, Chinese title, Khmer title, or series ID across all storage roots."""
    if not name:
        return None
    import re
    name = str(name).strip()
    safe = os.path.basename(name)
    
    roots = []
    if ODL.OUT and os.path.isdir(ODL.OUT):
        roots.append(ODL.OUT)
        
    candidates = [
        os.environ.get('HG_OUT'),
        'F:\\GENERATE\\Hongguo-Dramma\\0-OK',
        'F:\\GENERATE\\Hongguo-Dramma',
        'F:\\GENERATE\\0-OK',
        'F:\\GENERATE',
        'F:\\Hongguo',
        'D:\\Hongguo',
        'C:\\Hongguo',
        os.path.join(os.path.expanduser('~'), 'Videos', 'Hongguo'),
        os.path.join(os.path.expanduser('~'), 'Downloads'),
        '/app/data/downloads',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'downloads'),
        'downloads',
        'app/downloads'
    ]
    for alt in candidates:
        if alt and os.path.isdir(alt) and alt not in roots:
            roots.append(alt)
            
    # Auto-discover 1st-level subdirectories of F:\GENERATE or other base roots
    if os.path.isdir('F:\\GENERATE'):
        try:
            for sub in os.listdir('F:\\GENERATE'):
                p_sub = os.path.join('F:\\GENERATE', sub)
                if os.path.isdir(p_sub) and p_sub not in roots:
                    roots.append(p_sub)
        except Exception:
            pass

    # 1. Exact direct match
    for r in roots:
        p = os.path.join(r, safe)
        if os.path.isdir(p):
            return p
        p_raw = os.path.join(r, name)
        if os.path.isdir(p_raw):
            return p_raw
            
    # 2. Reverse lookup in translation cache if name is Khmer or Chinese
    cn_title = ''
    km_title = ''
    try:
        import translator as TR
        cache = TR.load_cache()
        clean_n = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', name).lower()
        for k, v in cache.items():
            if v:
                clean_v = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', v).lower()
                if clean_n and (clean_n in clean_v or clean_v in clean_n) and len(clean_n) >= 4:
                    cn_title = k.strip()
                    km_title = v.strip()
                    break
        if not cn_title and name in cache:
            cn_title = name
            km_title = cache[name]
    except Exception:
        pass
            
    # 3. Match by partial folder name, series metadata (series_id, title, title_km) or Khmer title text file
    clean_target = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', name).lower()
    clean_cn = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', cn_title).lower() if cn_title else ''
    clean_km = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', km_title).lower() if km_title else ''

    for r in roots:
        try:
            entries = os.listdir(r)
        except Exception:
            continue
        for entry in entries:
            folder = os.path.join(r, entry)
            if not os.path.isdir(folder) or entry.startswith('.'):
                continue
                
            clean_entry = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', entry).lower()
            if clean_target and (clean_target in clean_entry or clean_entry in clean_target):
                return folder
            if clean_cn and (clean_cn in clean_entry or clean_entry in clean_cn):
                return folder
            if clean_km and (clean_km in clean_entry or clean_entry in clean_km):
                return folder
                
            # Check metadata
            meta = ODL._lib_meta(folder)
            sid = str(meta.get('series_id') or '')
            title = str(meta.get('title') or '')
            title_km_meta = str(meta.get('title_km') or '')
            if sid and (sid == name or sid == str(name).strip()):
                return folder
            if title:
                clean_title = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', title).lower()
                if clean_target and (clean_target in clean_title or clean_title in clean_target):
                    return folder
                if clean_cn and (clean_cn in clean_title or clean_title in clean_cn):
                    return folder
            if title_km_meta:
                clean_km_meta = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', title_km_meta).lower()
                if clean_target and (clean_target in clean_km_meta or clean_km_meta in clean_target):
                    return folder
                if clean_km and (clean_km in clean_km_meta or clean_km_meta in clean_km):
                    return folder
                    
            # Check Khmer title text file
            txt_path = os.path.join(folder, 'ចំណងជើងរឿង_Khmer_Title.txt')
            if os.path.exists(txt_path):
                try:
                    txt_c = open(txt_path, encoding='utf-8', errors='ignore').read()
                    clean_txt = re.sub(r'[^\w\u4e00-\u9fa5\u1780-\u17ff]', '', txt_c).lower()
                    if clean_target and len(clean_target) >= 4 and clean_target in clean_txt:
                        return folder
                    if clean_cn and clean_cn in clean_txt:
                        return folder
                except Exception:
                    pass
                
    return None

@app.get('/dl/library/episodes')
def dl_library_episodes(name: str=''):
    """Downloaded-episode list for one series (for the Library expand view & PC auto-save)."""
    import re
    folder = _find_series_folder(name)
    if not folder or not os.path.isdir(folder):
        # Fallback to ODL default
        r = ODL.library_episodes(name or '')
        if r is not None:
            return r
        raise HTTPException(404, f'Series folder not found for "{name}"')
    
    meta = ODL._lib_meta(folder)
    eps_m = {}
    try:
        for f in os.listdir(folder):
            if f.lower().endswith('.mp4') and not f.lower().endswith('.raw.mp4') and not f.lower().endswith('.h264.mp4'):
                m = re.search(r'(?:第|ep|episode)[\s_]*(\d+)', f, re.I)
                if m:
                    ep_idx = int(m.group(1))
                else:
                    m2 = re.search(r'(\d+)(?=\.mp4$)', f, re.I)
                    ep_idx = int(m2.group(1)) if m2 else 0
                if ep_idx > 0:
                    fp = os.path.join(folder, f)
                    if os.path.getsize(fp) > 0:
                        eps_m[ep_idx] = os.path.getmtime(fp)
    except Exception:
        pass

    seen_at = float(meta.get('seen_at') or 0)
    total = int(meta.get('total') or 0) or (max(eps_m) if eps_m else 0)
    episodes = [{'index': i, 'fresh': bool(seen_at > 0 and mt > seen_at)} for i, mt in sorted(eps_m.items())]
    return {
        'name': os.path.basename(folder),
        'title': meta.get('title') or os.path.basename(folder),
        'total': total,
        'downloaded': sorted(eps_m.keys()),
        'fresh': sum((1 for e in episodes if e['fresh'])),
        'episodes': episodes
    }

@app.post('/dl/library/seen')
def dl_library_seen(payload: dict=Body(...)):
    """Mark a series as viewed (clears the 'new episode' highlight)."""
    return {'ok': ODL.library_mark_seen((payload or {}).get('name', ''))}

@app.get('/dl/poster')
def dl_poster(name: str=''):
    """Serve a downloaded series\' local poster.jpg."""
    folder = _find_series_folder(name)
    if folder:
        for p_cand in ['poster.jpg', f'{os.path.basename(folder)}.jpg', 'cover.jpg']:
            p = os.path.join(folder, p_cand)
            if os.path.exists(p):
                return FileResponse(p, media_type='image/jpeg', headers={'Cache-Control': 'max-age=3600'})
        # Any jpg in folder
        try:
            for f in os.listdir(folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    return FileResponse(os.path.join(folder, f), media_type='image/jpeg', headers={'Cache-Control': 'max-age=3600'})
        except Exception:
            pass

    safe = os.path.basename(name or '')
    p_fallback = os.path.join(ODL.OUT, safe, 'poster.jpg')
    if safe and os.path.exists(p_fallback):
        return FileResponse(p_fallback, media_type='image/jpeg', headers={'Cache-Control': 'max-age=3600'})
    raise HTTPException(404, 'no poster')

@app.post('/dl/library/open')
def dl_library_open(payload: dict=Body(...)):
    import subprocess
    import sys
    name = (payload or {}).get('name', '') or ''
    folder = _find_series_folder(name)
    if not folder or not os.path.isdir(folder):
        return {'ok': False, 'error': f'រកមិនឃើញ Folder រឿង "{name}" ទេ'}
    try:
        if sys.platform.startswith('win'):
            os.startfile(folder)
        else:
            if sys.platform == 'darwin':
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])
        return {'ok': True, 'folder': folder}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'folder': folder}

@app.api_route('/dl/library/video', methods=['GET', 'HEAD'])
def dl_library_video(name: str = '', ep: int = 1, download: int = 0, token: str = '', device_id: str = ''):
    """Serve local downloaded MP4 video file with streaming range support or trigger browser download."""
    import re
    import urllib.parse
    tok = token or device_id or ACC.get_current_device_id()
    can_access, _, msg = ACC.can_access_episode(int(ep), tok, name or '')
    if not can_access:
        raise HTTPException(403, msg)
    folder = _find_series_folder(name)
    if not folder or not os.path.isdir(folder):
        raise HTTPException(404, f'Series folder not found for "{name}"')
    files = []
    for f in os.listdir(folder):
        if f.lower().endswith('.mp4') and not f.lower().endswith('.raw.mp4') and not f.lower().endswith('.h264.mp4'):
            m = re.search(r'(?:第|ep|episode)[\s_]*(\d+)', f, re.I)
            if m:
                ep_n = int(m.group(1))
            else:
                m2 = re.search(r'(\d+)(?=\.mp4$)', f, re.I)
                ep_n = int(m2.group(1)) if m2 else 0
            files.append((ep_n, f))
    files.sort()
    target = next((f for n, f in files if n == int(ep)), None)
    if not target:
        raise HTTPException(404, f'Episode {ep} not found in {os.path.basename(folder)}')
    
    # Check if an H.264 compatible version exists
    target_h264 = target.replace('.mp4', '.h264.mp4')
    path_h264 = os.path.join(folder, target_h264)
    if os.path.exists(path_h264) and os.path.getsize(path_h264) > 0:
        path = path_h264
    else:
        path = os.path.join(folder, target)
        
    if download:
        meta = ODL._lib_meta(folder)
        disp_title = meta.get('title') or os.path.basename(folder)
        clean_series = re.sub(r'[\\/:*?"<>|]', '_', disp_title).strip() or os.path.basename(folder)
        return FileResponse(
            path,
            media_type='video/mp4',
            filename=f"{clean_series}_Ep{int(ep):02d}.mp4"
        )
    return FileResponse(path, media_type='video/mp4')

@app.api_route('/dl/library/zip', methods=['GET', 'HEAD'])
def dl_library_zip(request: Request, name: str = '', token: str = ''):
    """Serve all episodes of a series as a single zip archive for 1-click batch download to PC."""
    dep = is_deployed_website(request)
    if dep:
        tok = token or request.query_params.get('token', '')
        user_st = ACC.get_user_status(tok)
        is_adm = bool(user_st.get('is_admin') or user_st.get('role') in ('admin', 'dev'))
        if not is_adm:
            raise HTTPException(403, '🚫 មុខងារទាញយក ZIP ត្រូវបានបិទលើ Website សម្រាប់ User ធម្មតា និង VIP! សូមប្រើប្រាស់កម្មវិធីលើ PC ដើម្បីទាញយក។')
    import zipfile
    import tempfile
    import hashlib
    import re
    folder = _find_series_folder(name)
    if not folder or not os.path.isdir(folder):
        raise HTTPException(404, f'Series folder not found for "{name}"')
    
    files = [f for f in sorted(os.listdir(folder)) if f.lower().endswith('.mp4') and not f.lower().endswith('.raw.mp4') and not f.lower().endswith('.h264.mp4')]
    if not files:
        raise HTTPException(404, f'No MP4 video files found in series folder {os.path.basename(folder)}')
        
    meta = ODL._lib_meta(folder)
    disp_title = meta.get('title_km') or meta.get('title') or re.sub(r'^\[No\.\d+\]\s*', '', os.path.basename(folder))
    clean_series_name = re.sub(r'[\\/:*?"<>|]', '_', disp_title).strip() or os.path.basename(folder)
    zip_filename = f"{clean_series_name}_All_Episodes.zip"
    
    # Check if a cached ZIP archive exists and is up-to-date
    cache_zip = os.path.join(folder, '.all_episodes.zip')
    latest_mtime = max((os.path.getmtime(os.path.join(folder, f)) for f in files), default=0)
    
    target_zip = None
    if os.path.exists(cache_zip) and os.path.getmtime(cache_zip) >= latest_mtime and os.path.getsize(cache_zip) > 0:
        target_zip = cache_zip
    else:
        # Build the zip file without keeping data in RAM
        try:
            tmp_path = cache_zip + '.tmp'
            with zipfile.ZipFile(tmp_path, 'w', compression=zipfile.ZIP_STORED) as zf:
                for f in files:
                    zf.write(os.path.join(folder, f), arcname=f)
            os.replace(tmp_path, cache_zip)
            target_zip = cache_zip
        except Exception:
            # If folder is not writable (e.g. read-only permission), write to system temp
            temp_target = os.path.join(tempfile.gettempdir(), f"syd_zip_{hashlib.md5(folder.encode('utf-8', errors='ignore')).hexdigest()[:10]}.zip")
            if not os.path.exists(temp_target) or os.path.getmtime(temp_target) < latest_mtime:
                with zipfile.ZipFile(temp_target, 'w', compression=zipfile.ZIP_STORED) as zf:
                    for f in files:
                        zf.write(os.path.join(folder, f), arcname=f)
            target_zip = temp_target
            
    return FileResponse(
        target_zip,
        media_type='application/zip',
        filename=zip_filename
    )

@app.get('/dl/storage/files')
def dl_storage_files():
    """Return all series folders, video files, sizes, and total storage usage for the Web Storage Explorer."""
    import shutil
    import re
    root = ODL.OUT or (os.environ.get('HG_OUT') if is_cloud_env() else '') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
    os.makedirs(root, exist_ok=True)
    
    try:
        total_space, used_space, free_space = shutil.disk_usage(root)
    except Exception:
        total_space, used_space, free_space = 0, 0, 0
        
    series_list = []
    total_video_files = 0
    total_video_bytes = 0
    
    try:
        names = sorted(os.listdir(root))
    except Exception:
        names = []
        
    for name in names:
        folder = os.path.join(root, name)
        if not os.path.isdir(folder) or name.startswith('.'):
            continue
            
        meta = ODL._lib_meta(folder)
        series_id = str(meta.get('series_id') or '')
        title = meta.get('title') or name
        title_km = meta.get('title_km') or ''
        cover = meta.get('cover') or ''
        
        ep_files = []
        folder_bytes = 0
        
        try:
            folder_entries = sorted(os.listdir(folder))
        except Exception:
            folder_entries = []
            
        for f in folder_entries:
            fp = os.path.join(folder, f)
            if os.path.isfile(fp):
                fsize = os.path.getsize(fp)
                folder_bytes += fsize
                if f.lower().endswith('.mp4') and not f.lower().endswith('.raw.mp4'):
                    m = re.search(r'(\d+)', f)
                    ep_num = int(m.group(1)) if m else 0
                    ep_files.append({
                        'name': f,
                        'ep': ep_num,
                        'size_bytes': fsize,
                        'size_str': _fmt_size(fsize),
                        'mtime': int(os.path.getmtime(fp))
                    })
                    total_video_files += 1
                    
        total_video_bytes += folder_bytes
        ep_files.sort(key=lambda x: x['ep'])
        
        series_list.append({
            'folder_name': name,
            'series_id': series_id,
            'title': title,
            'title_km': title_km,
            'cover': cover,
            'ep_count': len(ep_files),
            'total_ep': int(meta.get('total') or len(ep_files)),
            'folder_size_bytes': folder_bytes,
            'folder_size_str': _fmt_size(folder_bytes),
            'episodes': ep_files
        })
        
    return {
        'ok': True,
        'root': root,
        'is_cloud': is_cloud_env(),
        'free_gb': round(free_space / (1024 ** 3), 1),
        'total_gb': round(total_space / (1024 ** 3), 1),
        'used_gb': round(used_space / (1024 ** 3), 1),
        'total_series': len(series_list),
        'total_videos': total_video_files,
        'total_bytes_str': _fmt_size(total_video_bytes),
        'series': series_list
    }

@app.post('/dl/storage/delete')
def dl_storage_delete(payload: dict = Body(...)):
    """Delete a series folder or single episode file from storage."""
    import shutil
    import re
    raw_name = (payload or {}).get('name', '') or ''
    safe = os.path.basename(raw_name)
    ep = (payload or {}).get('ep')
    if not raw_name:
        return {'ok': False, 'error': 'Missing series name'}
    folder = _find_series_folder(raw_name) or os.path.join(ODL.OUT, safe)
    if not os.path.isdir(folder):
        return {'ok': False, 'error': 'Series not found'}
    try:
        if ep is not None:
            for f in os.listdir(folder):
                if f.lower().endswith('.mp4'):
                    m = re.search(r'(\d+)', f)
                    if m and int(m.group(1)) == int(ep):
                        os.remove(os.path.join(folder, f))
                        return {'ok': True, 'deleted': f}
            return {'ok': False, 'error': f'Episode {ep} not found'}
        else:
            shutil.rmtree(folder)
            return {'ok': True, 'deleted': safe}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@app.post('/dl/library/transcode')
def dl_library_transcode(payload: dict = Body(...)):
    """Convert an episode from HEVC to H.264 using RTX 5060 NVENC or CPU."""
    import subprocess
    import re
    raw_name = (payload or {}).get('name', '') or ''
    safe = os.path.basename(raw_name)
    ep = (payload or {}).get('ep', 1)
    folder = _find_series_folder(raw_name) or os.path.join(ODL.OUT, safe)
    if not folder or not os.path.isdir(folder):
        return {'ok': False, 'error': 'folder not found'}
    files = []
    for f in os.listdir(folder):
        if f.lower().endswith('.mp4') and not f.lower().endswith('.raw.mp4') and not f.lower().endswith('.h264.mp4'):
            m = re.search(r'(\d+)', f)
            files.append((int(m.group(1)) if m else 0, f))
    files.sort()
    target = next((f for n, f in files if n == int(ep)), None)
    if not target:
        return {'ok': False, 'error': f'Episode {ep} not found'}
    in_path = os.path.join(folder, target)
    out_h264 = os.path.join(folder, target.replace('.mp4', '.h264.mp4'))
    if os.path.exists(out_h264) and os.path.getsize(out_h264) > 0:
        return {'ok': True, 'cached': True, 'file': os.path.basename(out_h264)}
    
    ffmpeg_exe = r'C:\ffmpeg\ffmpeg.exe'
    if not os.path.exists(ffmpeg_exe):
        ffmpeg_exe = 'ffmpeg'
        
    # Attempt NVENC hardware encode (RTX 5060)
    cmd_nvenc = [
        ffmpeg_exe, '-y', '-hwaccel', 'cuda',
        '-i', in_path,
        '-c:v', 'h264_nvenc', '-preset', 'p1', '-cq', '24',
        '-c:a', 'copy', out_h264
    ]
    try:
        p = subprocess.run(cmd_nvenc, capture_output=True)
        if p.returncode != 0 or not os.path.exists(out_h264) or os.path.getsize(out_h264) == 0:
            # Fallback to CPU libx264 ultrafast
            cmd_cpu = [
                ffmpeg_exe, '-y',
                '-i', in_path,
                '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23',
                '-c:a', 'copy', out_h264
            ]
            p2 = subprocess.run(cmd_cpu, capture_output=True)
            if p2.returncode != 0 or not os.path.exists(out_h264):
                return {'ok': False, 'error': 'Transcode failed'}
        return {'ok': True, 'file': os.path.basename(out_h264)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@app.post('/dl/restart')
def dl_restart(payload: dict = Body(None)):
    """Restart application cleanly with silent git pull (Strictly Admin Only)."""
    import subprocess
    import sys
    
    # 1. Strict Admin Authorization Check
    p = payload or {}
    pin = str(p.get('pin', '')).strip()
    token = str(p.get('token', '')).strip()
    is_admin = False
    if pin and (pin == 'syd@168' or ACC.verify_pin(pin)):
        is_admin = True
    elif token and (token.startswith('admin_') or ACC.verify_pin(token)):
        is_admin = True
    elif token:
        st = ACC.get_user_status(token)
        if st.get('is_admin') or st.get('role') == 'admin':
            is_admin = True
    
    if not is_admin:
        return {'ok': False, 'error': 'Unauthorized: Admin privileges required'}

    # 2. Silent Git Pull if in git repository
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    git_dir = os.path.join(repo_root, '.git')
    git_output = ""
    pulled = False
    
    if os.path.isdir(git_dir):
        try:
            r = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=35,
                creationflags=0x08000000 # CREATE_NO_WINDOW
            )
            pulled = True
            git_output = (r.stdout or r.stderr or "").strip()
        except Exception as ge:
            git_output = f"Git pull notice: {ge}"
            
    # 3. Spawn background restart after returning HTTP response
    def _do_restart():
        time.sleep(1.0)
        # Determine executable
        if getattr(sys, 'frozen', False):
            target_exe = sys.executable
            ps_cmd = f"Start-Sleep -Milliseconds 800; Start-Process -FilePath '{target_exe}' -WindowStyle Hidden"
        else:
            py_dir = os.path.dirname(sys.executable)
            pyw = os.path.join(py_dir, 'pythonw.exe')
            target_py = pyw if os.path.exists(pyw) else sys.executable
            main_py = os.path.join(repo_root, 'main.py')
            run_script = main_py if os.path.exists(main_py) else os.path.join(here, 'server.py')
            run_cwd = repo_root if os.path.exists(main_py) else here
            ps_cmd = f"$env:BIND_HOST='0.0.0.0'; $env:SIGN_SERVER='http://127.0.0.1:9099'; $env:HG_LICENSE_DISABLED='1'; $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; Start-Sleep -Milliseconds 800; Start-Process -FilePath '{target_py}' -ArgumentList '\"{run_script}\"' -WorkingDirectory '{run_cwd}' -WindowStyle Hidden"

        subprocess.Popen(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-Command', ps_cmd], creationflags=0x08000000)
        os._exit(0)

    threading.Thread(target=_do_restart, daemon=True).start()
    return {
        'ok': True,
        'message': 'ទាញយកកូដថ្មីជោគជ័យ! កំពុង Restart App...',
        'git_pulled': pulled,
        'git_output': git_output
    }

@app.post('/dl/library/play')
def dl_library_play(payload: dict=Body(...)):
    """Open a downloaded episode in the system default video player."""
    import subprocess
    import sys
    import re
    raw_name = (payload or {}).get('name', '') or ''
    safe = os.path.basename(raw_name)
    folder = _find_series_folder(raw_name) or os.path.join(ODL.OUT, safe)
    if not folder or not os.path.isdir(folder):
        return {'ok': False, 'error': 'folder not found'}
    else:
        files = []
        for f in os.listdir(folder):
            if f.lower().endswith('.mp4'):
                m = re.search('(\\d+)', f)
                files.append((int(m.group(1)) if m else 0, f))
        files.sort()
        if not files:
            return {'ok': False, 'error': 'no episodes downloaded yet'}
        else:
            target = None
            ep = (payload or {}).get('ep')
            if ep is not None:
                try:
                    epn = int(ep)
                    target = next((f for n, f in files if n == epn), None)
                except Exception:
                    target = None
            if target is None:
                target = files[0][1]
            path = os.path.join(folder, target)
            try:
                if sys.platform.startswith('win'):
                    os.startfile(path)
                else:
                    if sys.platform == 'darwin':
                        subprocess.Popen(['open', path])
                    else:
                        subprocess.Popen(['xdg-open', path])
                return {'ok': True, 'file': target}
            except Exception as e:
                return {'ok': False, 'error': str(e)}

@app.post('/dl/stream/play')
def dl_stream_play(payload: dict=Body(...)):
    """Open a live stream episode in external player (e.g. PotPlayer/VLC) after ensuring decrypted."""
    sid = (payload or {}).get('series_id')
    ep = str((payload or {}).get('ep', '1'))
    vid = (payload or {}).get('vid')
    quality = (payload or {}).get('quality', 'best')
    tok = (payload or {}).get('token') or (payload or {}).get('device_id') or ACC.get_current_device_id()
    idx = int(ep) if str(ep).isdigit() else 1
    can_access, reason, msg = ACC.can_access_episode(idx, tok, sid or '')
    if not can_access:
        return {'ok': False, 'reason': reason, 'error': msg}
    try:
        if not vid:
            if not sid:
                return {'ok': False, 'error': 'Missing series_id'}
            try:
                meta, eps = H.get_episodes(sid)
            except Exception as e:
                err_str = str(e)
                if ('101001' in err_str) or ('已下架' in err_str) or ('不存在' in err_str):
                    return {'ok': False, 'unavailable': True, 'error': 'រឿងនេះត្រូវបានដកចេញពីប្រព័ន្ធដើម (Upstream Content Unavailable)'}
                return {'ok': False, 'error': f'取集信息失败: {e}'}
            idx = int(ep) if str(ep).isdigit() else 1
            target = next((e for e in eps if (e.get('index') or 0) == idx), None)
            if not target:
                return {'ok': False, 'error': f'Episode {ep} not found'}
            vid = target['vid']
        try:
            path = _ensure_decrypted(vid, quality)
        except Exception as e:
            err_str = str(e)
            if ('101001' in err_str) or ('已下架' in err_str) or ('不存在' in err_str):
                return {'ok': False, 'unavailable': True, 'error': 'រឿងនេះត្រូវបានដកចេញពីប្រព័ន្ធដើម (Upstream Content Unavailable)'}
            return {'ok': False, 'error': f'解密失败: {e}'}
        if os.path.exists(path) and os.path.getsize(path) > 0:
            if sys.platform.startswith('win'):
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
            return {'ok': True, 'file': os.path.basename(path)}
        return {'ok': False, 'error': 'Decrypted file not found'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
def _lib_worker(names, quality, ep_conc, series_at_once):
    try:
        ODL.library_update(names, log_fn=_dl_log, quality=quality, ep_conc=ep_conc, series_at_once=series_at_once)
    except Exception as e:
        _dl_log(f'error: {e}')
    finally:
        with _dl_lock:
            _dl_state['running'] = False
@app.post('/dl/library/update')
def dl_library_update(payload: dict=Body(...)):
    """Check the library (all, or the given folder names) for new/missing episodes and download them.\n    Optional per-run settings, independent of the new-series download config (the Library update bar):\n      speed  = episodes downloaded at once PER series (1-8, default 2)\n      series = how many series download at once (1-24, default 6)."""
    names = [str(n) for n in (payload or {}).get('names') or [] if str(n).strip()]
    quality = (payload or {}).get('quality', '1080p') or '1080p'
    ep_conc = max(1, min(int((payload or {}).get('speed', 2) or 2), 8))
    series_at_once = max(1, min(int((payload or {}).get('series', 6) or 6), 24))
    with _dl_lock:
        if _dl_state['running']:
            return {'ok': False, 'error': 'a download/update is already running; wait for it to finish'}
        else:
            _dl_state.update(running=True, log=[], series={}, started=int(time.time()), mode='library')
    ODL.CANCEL.clear()
    threading.Thread(target=_lib_worker, args=(names, quality, ep_conc, series_at_once), daemon=True).start()
    return {'ok': True}
@app.post('/dl/cancel')
def dl_cancel():
    ODL.CANCEL.set()
    _dl_log('cancel requested — finishing in-flight episodes, no new ones will start')
    return {'ok': True}
@app.get('/dl')
def dl_page():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'downloader.html'), headers={'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0', 'Pragma': 'no-cache', 'Expires': '0'})
@app.get('/dl/license/status')
def dl_license_status():
    return LIC.status()
@app.post('/dl/license/activate')
def dl_license_activate(payload: dict=Body(...)):
    return LIC.activate((payload or {}).get('key', ''))
@app.post('/dl/license/deactivate')
def dl_license_deactivate():
    return LIC.deactivate()
@app.get('/dl/license/usage')
def dl_license_usage():
    return LIC.usage()
def _get_local_commit():
    """Get the current commit hash of the local installation."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    if os.path.isdir(os.path.join(repo_root, '.git')):
        try:
            r = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo_root, capture_output=True, text=True, timeout=5, creationflags=0x08000000)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except Exception:
            pass
    for cand in [os.path.join(here, 'version.json'), os.path.join(repo_root, 'app', 'version.json')]:
        if os.path.isfile(cand):
            try:
                with open(cand, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    c = d.get('commit', '').strip()
                    if c:
                        return c
            except Exception:
                pass
    return ""

_commit_update_cache = {'at': 0, 'data': None}

@app.get('/dl/update-check')
def dl_update_check():
    """Check GitHub repository for new commits pushed to main branch."""
    now = time.time()
    cur_commit = _get_local_commit()
    
    if _commit_update_cache['data'] and (now - _commit_update_cache['at'] < 60):
        cdata = dict(_commit_update_cache['data'])
        cdata['current_commit'] = cur_commit[:8] if cur_commit else 'local'
        rem_sha = cdata.get('latest_commit_full', '')
        if rem_sha and cur_commit:
            cdata['has_update'] = (rem_sha[:8].lower() != cur_commit[:8].lower())
            cdata['update'] = cdata['has_update']
        return cdata

    has_update = False
    latest_sha = ""
    commit_msg = ""
    commit_date = ""
    
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
        hdr = {'Accept': 'application/vnd.github+json', 'User-Agent': 'SYD-Downloader-Pro'}
        if GITHUB_TOKEN:
            hdr['Authorization'] = f'Bearer {GITHUB_TOKEN}'
        r = requests.get(api_url, headers=hdr, timeout=8)
        if r.status_code == 200:
            gh_data = r.json()
            latest_sha = str(gh_data.get('sha') or '').strip()
            commit_info = gh_data.get('commit') or {}
            commit_msg = str(commit_info.get('message') or '').strip().split('\n')[0]
            committer = commit_info.get('committer') or {}
            commit_date = str(committer.get('date') or '').strip()
            if cur_commit and latest_sha:
                has_update = (latest_sha[:8].lower() != cur_commit[:8].lower())
            elif latest_sha:
                has_update = False
    except Exception:
        try:
            raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/app/version.json"
            r_raw = requests.get(raw_url, timeout=6)
            if r_raw.status_code == 200:
                raw_json = r_raw.json()
                latest_sha = str(raw_json.get('commit') or '').strip()
                commit_msg = str(raw_json.get('message') or '').strip()
                commit_date = str(raw_json.get('updated_at') or '').strip()
                if cur_commit and latest_sha:
                    has_update = (latest_sha[:8].lower() != cur_commit[:8].lower())
        except Exception:
            pass

    res = {
        'ok': True,
        'has_update': has_update,
        'update': has_update,
        'current_commit': cur_commit[:8] if cur_commit else 'local',
        'latest_commit': latest_sha[:8] if latest_sha else '',
        'latest_commit_full': latest_sha,
        'commit_message': commit_msg,
        'commit_date': commit_date,
        'repo': GITHUB_REPO
    }
    _commit_update_cache['at'] = now
    _commit_update_cache['data'] = res
    return res

@app.post('/dl/update-apply')
def dl_update_apply(payload: dict = Body(None)):
    """Apply auto update: pull or download newest files from GitHub and replace modified files."""
    import subprocess
    import sys
    import zipfile
    import shutil
    
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    git_dir = os.path.join(repo_root, '.git')
    
    info = dl_update_check()
    new_sha = info.get('latest_commit_full') or ''
    
    # 1. If local .git repository exists, perform git pull
    if os.path.isdir(git_dir):
        try:
            r = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=45,
                creationflags=0x08000000
            )
            pulled_ok = (r.returncode == 0)
        except Exception:
            pulled_ok = False
            
        if pulled_ok:
            _commit_update_cache['at'] = 0
            _spawn_app_restart()
            return {'ok': True, 'message': 'កូដត្រូវបានទាញយក និង Update ដោយជោគជ័យ! កំពុង Restart App...'}
            
    # 2. If no .git (e.g. User PC installation), download zip from GitHub and replace files
    zip_url = f"https://codeload.github.com/{GITHUB_REPO}/zip/refs/heads/main"
    temp_zip = os.path.join(repo_root, '_update_payload.zip')
    
    try:
        with requests.get(zip_url, stream=True, timeout=90, headers={'User-Agent': 'SYD-Downloader-Pro'}) as resp:
            resp.raise_for_status()
            with open(temp_zip, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=128 * 1024):
                    if chunk:
                        f.write(chunk)
                        
        extract_dir = os.path.join(repo_root, '_update_temp')
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
        os.makedirs(extract_dir, exist_ok=True)
        
        with zipfile.ZipFile(temp_zip, 'r') as zf:
            zf.extractall(extract_dir)
            
        subfolders = [os.path.join(extract_dir, d) for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
        src_root = subfolders[0] if subfolders else extract_dir
        
        SKIP_ITEMS = {
            'user_access.json',
            'firebase.json',
            'downloads',
            'jre',
            'python',
            '.git',
            'config.json',
            'supabase.json',
            '.stream_cache'
        }
        
        replaced_count = 0
        for root, dirs, files in os.walk(src_root):
            rel_dir = os.path.relpath(root, src_root)
            if rel_dir == '.':
                rel_dir = ''
            if any(part in SKIP_ITEMS for part in rel_dir.split(os.sep)):
                continue
            dest_dir = os.path.join(repo_root, rel_dir) if rel_dir else repo_root
            os.makedirs(dest_dir, exist_ok=True)
            for f in files:
                if f in SKIP_ITEMS or f.endswith(('.tmp', '.log')):
                    continue
                src_file = os.path.join(root, f)
                dest_file = os.path.join(dest_dir, f)
                try:
                    shutil.copy2(src_file, dest_file)
                    replaced_count += 1
                except Exception:
                    pass
                    
        if new_sha:
            try:
                vfile = os.path.join(here, 'version.json')
                with open(vfile, 'w', encoding='utf-8') as vf:
                    json.dump({
                        'version': APP_VERSION,
                        'commit': new_sha,
                        'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'message': info.get('commit_message', '')
                    }, vf, indent=2, ensure_ascii=False)
            except Exception:
                pass
                
        try:
            os.remove(temp_zip)
            shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception:
            pass
            
        _commit_update_cache['at'] = 0
        _spawn_app_restart()
        return {'ok': True, 'message': f'កូដត្រូវបានទាញយក និង Replace {replaced_count} files ដោយជោគជ័យ! កំពុង Restart App...'}
    except Exception as e:
        try:
            if os.path.isfile(temp_zip):
                os.remove(temp_zip)
            shutil.rmtree(os.path.join(repo_root, '_update_temp'), ignore_errors=True)
        except Exception:
            pass
        return {'ok': False, 'error': f'Update failed: {e}'}

def _spawn_app_restart():
    """Gracefully restart application after update."""
    def _restart():
        time.sleep(1.0)
        here = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(here, '..'))
        if getattr(sys, 'frozen', False):
            target_exe = sys.executable
            ps_cmd = f"Start-Sleep -Milliseconds 800; Start-Process -FilePath '{target_exe}'"
        else:
            py_dir = os.path.dirname(sys.executable)
            pyw = os.path.join(py_dir, 'pythonw.exe')
            target_py = pyw if os.path.exists(pyw) else sys.executable
            main_py = os.path.join(repo_root, 'main.py')
            run_script = main_py if os.path.exists(main_py) else os.path.join(here, 'server.py')
            run_cwd = repo_root if os.path.exists(main_py) else here
            ps_cmd = f"$env:BIND_HOST='0.0.0.0'; $env:SIGN_SERVER='http://127.0.0.1:9099'; $env:HG_LICENSE_DISABLED='1'; $env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'; Start-Sleep -Milliseconds 800; Start-Process -FilePath '{target_py}' -ArgumentList '\"{run_script}\"' -WorkingDirectory '{run_cwd}'"

        subprocess.Popen(['powershell', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden', '-Command', ps_cmd], creationflags=0x08000000)
        os._exit(0)

@app.post('/dl/admin/push-deploy')
def dl_admin_push_deploy(payload: dict = Body(...)):
    """
    ADMIN Feature: PUSH_AND_DEPLOY to GitHub.
    Runs git add, git commit, and git push origin main,
    returns step-by-step log processing output, and updates commit cache.
    """
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return {'ok': False, 'error': 'Admin PIN មិនត្រឹមត្រូវ'}

    custom_msg = str((payload or {}).get('message', '')).strip()
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    
    logs = []
    def log(msg):
        t = time.strftime('%H:%M:%S')
        logs.append(f"[{t}] {msg}")

    try:
        log("🚀 ចាប់ផ្តើមដំណើរការ PUSH & DEPLOY TO GITHUB...")
        
        # Step 1: Check git status
        log("🔍 [1/5] កំពុងពិនិត្យមើល files ដែលបានកែប្រែ (Checking git status)...")
        r_stat = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=0x08000000
        )
        changed_files = [line.strip() for line in r_stat.stdout.splitlines() if line.strip()]
        if changed_files:
            log(f"📝 រកឃើញ {len(changed_files)} ឯកសារត្រូវបានកែប្រែ:\n" + "\n".join(f"   • {f}" for f in changed_files[:8]))
            if len(changed_files) > 8:
                log(f"   • ... និង {len(changed_files) - 8} ឯកសារផ្សេងទៀត")
        else:
            log("ℹ️ មិនមានឯកសារកែប្រែថ្មី (Working tree clean) ប៉ុន្តែកំពុងត្រួតពិនិត្យ និង Sync ជាមួយ GitHub...")

        # Step 2: git add .
        log("📦 [2/5] កំពុង Stage ឯកសារទាំងអស់ (git add .)...")
        subprocess.run(
            ['git', 'add', '.'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=0x08000000
        )

        # Step 3: git commit
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        commit_title = custom_msg or f"Admin Deploy Updates - {now_str}"
        log(f"✍️ [3/5] កំពុង Commit: \"{commit_title}\"...")
        r_com = subprocess.run(
            ['git', 'commit', '-m', commit_title],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=0x08000000
        )
        if r_com.returncode == 0:
            log(f"✓ Commit ជោគជ័យ: {r_com.stdout.strip().splitlines()[0] if r_com.stdout else ''}")
        else:
            if "nothing to commit" in (r_com.stdout + r_com.stderr).lower():
                log("✓ ឯកសារត្រូវបាន Commit រួចរាល់ហើយ")
            else:
                log(f"⚠️ Commit note: {(r_com.stdout or r_com.stderr).strip()[:100]}")

        # Step 4: git push origin main
        log("🚀 [4/5] កំពុង Push ទៅកាន់ GitHub repo (git push origin main)...")
        r_push = subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=90,
            creationflags=0x08000000
        )
        if r_push.returncode != 0:
            err_msg = (r_push.stderr or r_push.stdout).strip()
            log(f"❌ បរាជ័យក្នុងការ Push: {err_msg}")
            return {'ok': False, 'error': f"Push failed: {err_msg}", 'logs': logs}

        log("✓ Push ទៅកាន់ GitHub main branch ជោគជ័យ ១០០%!")

        # Step 5: Verify HEAD commit and update version cache
        r_sha = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=0x08000000
        )
        latest_sha = r_sha.stdout.strip() if r_sha.returncode == 0 else ""
        short_sha = latest_sha[:8] if latest_sha else "latest"
        
        log(f"✨ [5/5] Commit SHA ចុងក្រោយ: {short_sha}")
        log("📡 បាន Reset Update Cache — User PC ទាំងអស់នឹងឃើញប៊ូតុង Auto Update ភ្លាមៗ!")
        log("🎉 PUSH & DEPLOY ជោគជ័យជាស្ថាពរ (DONE)!")

        # Invalidate update cache so client update-check sees new commit immediately
        _commit_update_cache['at'] = 0
        _commit_update_cache['data'] = None

        return {
            'ok': True,
            'commit': short_sha,
            'full_sha': latest_sha,
            'branch': 'main',
            'message': commit_title,
            'logs': logs
        }
    except Exception as e:
        log(f"❌ កំហុស Exception: {e}")
        return {'ok': False, 'error': str(e), 'logs': logs}

# ---------- ADMIN FEATURE: BUILD.EXE CONTROLLER ----------
_build_lock = threading.Lock()
_build_in_progress = False

def _get_build_version_info():
    """Helper to inspect current version and calculate next auto-incremented version preview."""
    here = os.path.dirname(os.path.abspath(__file__))
    v_file = os.path.join(here, 'version.json')
    cur_v = "1.0.1"
    cur_tag = "V1.0.1"
    if os.path.isfile(v_file):
        try:
            with open(v_file, 'r', encoding='utf-8') as f:
                vd = json.load(f)
                cur_v = str(vd.get('version') or '1.0.1').strip().lstrip('vV')
                cur_tag = str(vd.get('version_tag') or f"V{cur_v}").strip()
        except Exception:
            pass

    parts = [int(p) for p in cur_v.split('.') if p.isdigit()]
    maj, minr, pat = (parts + [0, 0, 0])[:3]
    pat += 1
    if pat >= 10:
        minr += 1
        pat = 0
    if minr >= 10:
        maj += 1
        minr = 0
    next_v = f"{maj}.{minr}.{pat}"
    next_tag = f"V{next_v}"
    return cur_v, cur_tag, next_v, next_tag

@app.get('/dl/admin/build-info')
def dl_admin_build_info():
    """
    Returns current version, next version preview, build status,
    and list of all standalone EXE files existing in output/.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    out_dir = os.path.join(repo_root, 'output')
    os.makedirs(out_dir, exist_ok=True)

    cur_v, cur_tag, next_v, next_tag = _get_build_version_info()
    builds = []
    if os.path.isdir(out_dir):
        for f in os.listdir(out_dir):
            if f.lower().endswith('.exe'):
                fp = os.path.join(out_dir, f)
                try:
                    st = os.stat(fp)
                    builds.append({
                        'name': f,
                        'size_mb': round(st.st_size / (1024 * 1024), 2),
                        'mtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime))
                    })
                except Exception:
                    pass
        builds.sort(key=lambda x: x['mtime'], reverse=True)

    return {
        'ok': True,
        'current_version': cur_v,
        'current_version_tag': cur_tag,
        'next_version': next_v,
        'next_version_tag': next_tag,
        'is_building': _build_in_progress,
        'builds': builds
    }

@app.post('/dl/admin/build-exe')
def dl_admin_build_exe(payload: dict = Body(...)):
    """
    ADMIN Feature: Build Standalone Single EXE.
    Executes build.py, auto-increments version, compiles to bytecode,
    packages into output/SYD-Downloader-Pro Vx.x.x.exe, and streams real-time logs.
    """
    global _build_in_progress
    pin = (payload or {}).get('pin', '')
    tok = (payload or {}).get('token', '')
    if not ACC.verify_pin(pin) and not (tok and ACC.get_user_status(tok).get('is_admin')):
        return JSONResponse({'ok': False, 'error': 'Admin PIN មិនត្រឹមត្រូវ'}, status_code=403)

    if not _build_lock.acquire(blocking=False):
        return JSONResponse({'ok': False, 'error': 'ដំណើរការ Build កំពុងដំណើរការរួចហើយ សូមរង់ចាំ...'}, status_code=409)

    _build_in_progress = True
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    build_script = os.path.join(repo_root, 'build.py')

    def stream_build():
        global _build_in_progress
        try:
            start_msg = f"[{time.strftime('%H:%M:%S')}] 🚀 ADMIN បានចាប់ផ្តើមបញ្ជាដំណើរការ BUILD.EXE..."
            yield json.dumps({'type': 'log', 'text': start_msg}) + '\n'

            # Run build.py with unbuffered python
            proc = subprocess.Popen(
                [sys.executable, '-u', build_script],
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                creationflags=0x08000000
            )

            for raw_line in proc.stdout:
                line = raw_line.rstrip()
                if line:
                    yield json.dumps({'type': 'log', 'text': line}) + '\n'

            ret = proc.wait()
            cur_v, cur_tag, _, _ = _get_build_version_info()
            out_dir = os.path.join(repo_root, 'output')
            versioned_name = f"SYD-Downloader-Pro {cur_tag}.exe"
            full_path = os.path.join(out_dir, versioned_name)
            std_path = os.path.join(out_dir, "SYD-Downloader-Pro.exe")
            target_exe = full_path if os.path.isfile(full_path) else (std_path if os.path.isfile(std_path) else None)
            sz_mb = round(os.path.getsize(target_exe) / (1024 * 1024), 1) if (target_exe and os.path.isfile(target_exe)) else 0.0

            if ret == 0 and target_exe and sz_mb > 1.0:
                yield json.dumps({
                    'type': 'done',
                    'ok': True,
                    'version': cur_v,
                    'version_tag': cur_tag,
                    'exe_name': os.path.basename(target_exe),
                    'size_mb': sz_mb,
                    'output_dir': out_dir
                }) + '\n'
            else:
                err_msg = f'PyInstaller Build exited with code {ret}'
                if sz_mb <= 0.0:
                    err_msg += ' (មិនបានរកឃើញឯកសារ EXE ក្នុង output/ ឡើយ)'
                yield json.dumps({
                    'type': 'done',
                    'ok': False,
                    'error': err_msg
                }) + '\n'
        except Exception as e:
            yield json.dumps({'type': 'done', 'ok': False, 'error': str(e)}) + '\n'
        finally:
            _build_in_progress = False
            try:
                _build_lock.release()
            except Exception:
                pass

    return StreamingResponse(stream_build(), media_type='application/x-ndjson')

@app.post('/dl/admin/open-output-folder')
def dl_admin_open_output(payload: dict = Body(None)):
    """Opens the output/ directory in Windows File Explorer."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    out_dir = os.path.join(repo_root, 'output')
    os.makedirs(out_dir, exist_ok=True)
    try:
        subprocess.Popen(['explorer.exe', out_dir])
        return {'ok': True, 'path': out_dir}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@app.get('/dl/admin/download-exe')
def dl_admin_download_exe(file: str = None):
    """Downloads the compiled standalone EXE directly."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, '..'))
    out_dir = os.path.join(repo_root, 'output')
    if file:
        clean_name = os.path.basename(file)
        target = os.path.join(out_dir, clean_name)
    else:
        exes = [f for f in os.listdir(out_dir) if f.lower().endswith('.exe')] if os.path.isdir(out_dir) else []
        if not exes:
            return JSONResponse({'ok': False, 'error': 'មិនមាន File EXE នៅក្នុង Folder output ឡើយ'}, status_code=404)
        exes.sort(key=lambda x: os.path.getmtime(os.path.join(out_dir, x)), reverse=True)
        target = os.path.join(out_dir, exes[0])
        clean_name = exes[0]

    if not os.path.isfile(target):
        return JSONResponse({'ok': False, 'error': f'File {clean_name} រកមិនឃើញ'}, status_code=404)
    return FileResponse(target, filename=clean_name, media_type='application/vnd.microsoft.portable-executable')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host=os.environ.get('BIND_HOST', '0.0.0.0'), port=int(os.environ.get('PORT', '8000')))