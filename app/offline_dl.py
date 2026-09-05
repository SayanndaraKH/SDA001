# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\offline_dl.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-08-31 16:22:21 UTC (1788193341)

global OUT
# ***<module>: Failure: Different bytecode
"""红果全自动纯离线下载器: 搜索/榜单 → 选集 → API 取 spade+直链 → 本地 unwrap → 下载 → 解密。\n支持整剧批量 + 多线程并发 + 断点续传(进度持久化) + 失败集自动重试。\n\n链路: hongguo API(签名) 取 video_model(main_url + encrypt_info.spade_a)\n      → unwrap_spade 纯算法出 content key(无 KEK) → 下载 CDN 密文 → senc 读 base_iv\n      → AES-128-CTR 解密 → 明文 mp4。解密纯离线; 仅取 spade/直链需签名。\n\n进度持久化: downloads/.state/series_<id>.json (每集完成即保存; 重跑自动续传只补未完成)。\n\n用法:\n  python offline_dl.py search \"剧名\"\n  python offline_dl.py rank [recommend|hot|new]\n  python offline_dl.py quals <vid>                                 # 列某集可选清晰度\n  python offline_dl.py series <series_id> [范围 1-5/3/all] [-c 并发] [-r 重试轮] [-q 清晰度]\n  python offline_dl.py resume <series_id> [-c 并发] [-r 重试轮] [-q 清晰度]   # 只补未完成/失败集\n  python offline_dl.py vid <vid> [输出文件名] [-q 清晰度]\n  python offline_dl.py batch <id1> <id2> ... [-c 并发] [-r 重试轮] [-q 清晰度]   # 多剧并行(全局并发上限)\n  python offline_dl.py collection [list] [-c 并发] [-r 重试轮] [-q 清晰度]     # 抓账号\"我的\"追剧全部并行下载(list=只列出)\n  python offline_dl.py url \"<分享文案>\" 或 url links.txt [-c][-r][-q]   # 分享链接→解析→并行下载整剧(可多条;已下完自动跳过;多条可存文件一行一个)\n  python offline_dl.py favsync [list] [-c 并发] [-r 重试轮] [-q 清晰度]        # 实时抓模拟器\"收藏\"→并行同步(跳过已下,补缺集/新集);list=只列出\n  python offline_dl.py fixaudio [目录或文件]                        # 修复旧下载\"有画面无声音\"(默认修 downloads/ 全部)\n  python offline_dl.py status <series_id>                          # 看进度\n  # 默认: 清晰度 1080p; series 不给范围=全部集(1-N); 每部剧独立文件夹 downloads/剧名/第NNN集.mp4。\n  # -c: 全局并发上限(跨剧共享, 总同时下载+解密任务数 ≤ -c, 默认4; 多剧/收藏并行下载); -r: 失败重试轮数(默认2)。\n  # -q: 1080p(默认)/720p/540p/480p/360p/best/worst(或纯数字); 不存在则取<=请求的最高档。\n"""
import sys
import os
import json
import re
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'frida'))
import hongguo as H
import offline_decrypt as OD
OUT = os.environ.get('HG_OUT') or os.path.join(ROOT, 'downloads')
_META = os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'), 'HongguoDownloader')
STATE_DIR = os.path.join(_META, '.state')
CLICK_SCORES = {}
_plock = threading.Lock()
_state_lock = threading.Lock()
_meta_lock = threading.Lock()
CANCEL = threading.Event()
_LIVE_LOCK = threading.Lock()
_LIVE = {'running': False, 'phase': '', 'started': 0, 'checked': 0, 'to_check': 0, 'found': 0, 'series': {}}
def _live_reset(to_check=0):
    with _LIVE_LOCK:
        _LIVE.update(running=True, phase='checking', started=int(time.time()), checked=0, to_check=to_check, found=0, series={})
def _live_finish(cancelled=False):
    with _LIVE_LOCK:
        _LIVE['running'] = False
        _LIVE['phase'] = 'cancelled' if cancelled else 'done'
def _live_running():
    return _LIVE['running']
def _live_series(sid, **kw):
    with _LIVE_LOCK:
        if not _LIVE['running']:
            return
        else:
            s = _LIVE['series'].setdefault(str(sid), {'inflight': {}})
            s.update(kw)
def _live_checked(inc=1, found=0):
    with _LIVE_LOCK:
        _LIVE['checked'] += inc
        _LIVE['found'] += found
def _live_ep_bytes(sid, idx, done, total):
    with _LIVE_LOCK:
        if not _LIVE['running']:
            return
        else:
            s = _LIVE['series'].get(str(sid))
            if s is None:
                return
            else:
                s.setdefault('inflight', {})[int(idx or 0)] = (int(done), int(total or 0))

class SpeedTracker:
    """Tracks real-time download speed per drama (rolling window bytes/sec)."""
    def __init__(self):
        self.lock = threading.Lock()
        self.series_stats = {}

    def report_chunk(self, sid, ep_idx, current_bytes, total_bytes):
        now = time.time()
        with self.lock:
            st = self.series_stats.setdefault(str(sid), {
                "window": [],
                "ep_bytes": {},
                "speed_bps": 0,
                "speed_str": "",
                "last_active": now
            })
            prev_ep = st["ep_bytes"].get(ep_idx, 0)
            delta = current_bytes - prev_ep
            st["ep_bytes"][ep_idx] = current_bytes
            st["last_active"] = now

            if delta > 0:
                st["window"].append((now, delta))

            cutoff = now - 2.0
            st["window"] = [(t, b) for (t, b) in st["window"] if t >= cutoff]

            if len(st["window"]) >= 2:
                dt = max(0.2, st["window"][-1][0] - st["window"][0][0])
                total_win_bytes = sum(b for (t, b) in st["window"])
                bps = total_win_bytes / dt
            elif len(st["window"]) == 1:
                bps = st["window"][0][1] / 0.4
            else:
                bps = 0

            st["speed_bps"] = bps
            st["speed_str"] = self.format_speed(bps)

    def ep_done(self, sid, ep_idx):
        with self.lock:
            st = self.series_stats.get(str(sid))
            if st:
                st["ep_bytes"].pop(ep_idx, None)

    def get_speed(self, sid):
        now = time.time()
        with self.lock:
            st = self.series_stats.get(str(sid))
            if not st:
                return 0, ""
            if now - st.get("last_active", 0) > 3.0:
                st["speed_bps"] = 0
                st["speed_str"] = ""
                st["window"].clear()
                return 0, ""
            return st["speed_bps"], st["speed_str"]

    @staticmethod
    def format_speed(bps):
        if bps <= 0:
            return ""
        if bps >= 1024 * 1024 * 1024:
            return f"{bps / (1024 * 1024 * 1024):.1f} GB/s"
        elif bps >= 1024 * 1024:
            return f"{bps / (1024 * 1024):.1f} MB/s"
        elif bps >= 1024:
            return f"{bps / 1024:.0f} KB/s"
        else:
            return f"{int(bps)} B/s"

speed_tracker = SpeedTracker()
def _live_ep_done(sid, idx, ok=True):
    with _LIVE_LOCK:
        if not _LIVE['running']:
            return
        else:
            s = _LIVE['series'].get(str(sid))
            if s is None:
                return
            else:
                s.get('inflight', {}).pop(int(idx or 0), None)
                if ok:
                    s['dl_done'] = int(s.get('dl_done', 0)) + 1
def live_snapshot():
    """Fast in-memory snapshot for /dl/status. `frac` = fraction of the whole series present now\n    (already-downloaded + this run\'s finished episodes + the in-flight episode\'s byte fraction),\n    which is exactly what the poster clock-reveal renders."""
    with _LIVE_LOCK:
        series = []
        for sid, s in _LIVE['series'].items():
            if s.get('state', '') in ['pending', 'uptodate']:
                continue
            else:
                total = int(s.get('total') or 0)
                have = int(s.get('have') or 0)
                dl_done = int(s.get('dl_done') or 0)
                inflight = s.get('inflight') or {}
                infrac = 0.0
                for d, t in inflight.values():
                    if t:
                        infrac += min(1.0, d / t)
                have_now = have + dl_done + infrac
                frac = have_now / total if total else 0.0
                done_eps = min(total, have + dl_done) if total else have + dl_done
                series.append({'sid': sid, 'name': s.get('name'), 'title': s.get('title') or s.get('name'), 'total': total, 'done': done_eps, 'have': have, 'need': int(s.get('need') or 0), 'state': s.get('state', ''), 'status': s.get('state', ''), 'score': s.get('score', ''), 'frac': max(0.0, min(1.0, frac))})
        return {'running': _LIVE['running'], 'phase': _LIVE['phase'], 'started': _LIVE['started'], 'checked': _LIVE['checked'], 'to_check': _LIVE['to_check'], 'found': _LIVE['found'], 'series': series}
def set_output_dir(path):
    """设置下载输出目录(整剧文件夹+mp4存这里)。元数据仍在项目 downloads/.state。返回生效路径。"""
    global OUT
    if path and str(path).strip():
        p = str(path).strip()
        # Protect against Windows drive paths on Linux/Docker/Cloud environments
        if not sys.platform.startswith('win'):
            if re.match(r'^(?:/app/)?([a-zA-Z]:|\\|/[a-zA-Z]:)', p) or not p.startswith('/'):
                p = os.environ.get('HG_OUT') or '/app/data/downloads'
        OUT = os.path.abspath(os.path.expanduser(p))
        try:
            os.makedirs(OUT, exist_ok=True)
        except Exception:
            pass
    return OUT
def log(msg):
    with _plock:
        print(msg, flush=True)
def _state_path(sid):
    return os.path.join(STATE_DIR, f'series_{sid}.json')
def _load_state(sid):
    p = _state_path(sid)
    if not os.path.exists(p):
        for old in [os.path.join(OUT, '.state', f'series_{sid}.json'), os.path.join(ROOT, 'downloads', '.state', f'series_{sid}.json')]:
            if os.path.exists(old):
                p = old
                break
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding='utf-8'))
        except Exception:
            pass
    return {'series_id': str(sid), 'title': '', 'episodes': {}}
def _save_state(sid, st):
    os.makedirs(STATE_DIR, exist_ok=True)
    with _state_lock:
        tmp = _state_path(sid) + '.tmp'
        json.dump(st, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        os.replace(tmp, _state_path(sid))
def _is_done(st, idx):
    """状态 done 且输出文件仍在(>0) 才算完成(支持文件被删后重下)。"""
    e = st['episodes'].get(str(idx))
    if not e or e.get('status') != 'done':
        return False
    else:
        f = e.get('file')
        return bool(f) and os.path.exists(f) and (os.path.getsize(f) > 0)
FAV_JSON = os.path.join(_META, '.favorites.json')
def _grab_favorites():
    # irreducible cflow, using cdg fallback
    """实时从模拟器红果 app 本地库抓\"收藏\"(t_video_serial_collection)。\n    做法: root 拷贝登录用户 reading_db 到 /sdcard → adb pull → 本地 Python sqlite3 读\n    (避免 adb shell 引号问题, WAL 也一起拉)。返回 [{series_id,name,series_cnt,content_type}]。\n    需要: adb + 已 root(su) + 设备在线 + app 已登录。"""
    # ***<module>._grab_favorites: Failure: Compilation Error
    import subprocess
    import sqlite3
    adb = os.environ.get('ADB') or 'C:\\Program Files\\Netease\\MuMuPlayer\\nx_main\\adb.exe'
    dev = os.environ.get('ADB_DEVICE', '127.0.0.1:16384')
    pkg = os.environ.get('HG_PKG', 'com.phoenix.read.oversea.gp')
    def run(*a, timeout=45):
        # ***<module>._grab_favorites.run: Failure: Different bytecode
        return subprocess.run([adb, '-s', dev] + list(a), capture_output=True, text=True, timeout=timeout)
    def su(cmd):
        return run('shell', 'su -c \'' + cmd + '\'')
    ls = su(f'ls -1 /data/data/{pkg}/files/').stdout
    uids = [x.strip() for x in ls.splitlines() if x.strip().isdigit() and x.strip() != '0']
    if not uids:
        raise RuntimeError('找不到登录用户目录 (app 未登录 / adb 未 root / 设备离线?)')
    else:
        os.makedirs(STATE_DIR, exist_ok=True)
        loc = os.path.join(STATE_DIR, '_favdb')
        favs, seen = ([], set())
        for uid in uids:
            rdb = f'/data/data/{pkg}/files/{uid}/reading_db_{uid}'
            su(f'cp {rdb} /sdcard/_hgfav.db 2>/dev/null; cp {rdb}-wal /sdcard/_hgfav.db-wal 2>/dev/null; cp {rdb}-shm /sdcard/_hgfav.db-shm 2>/dev/null; chmod 666 /sdcard/_hgfav.db*')
            for sfx in ['', '-wal', '-shm']:
                run('pull', f'/sdcard/_hgfav.db{sfx}', loc + sfx)
            su('rm -f /sdcard/_hgfav.db*')
            if not os.path.exists(loc):
                continue
            con = sqlite3.connect(loc)
            try:
                cur = con.execute('SELECT series_id, series_name, series_cnt, content_type FROM t_video_serial_collection WHERE is_delete=0 ORDER BY collect_time DESC')
                for sid, name, cnt, ctype in cur.fetchall():
                    sid = str(sid)
                    if sid and sid not in seen:
                        seen.add(sid)
                        favs.append({'series_id': sid, 'name': name or sid, 'series_cnt': cnt, 'content_type': ctype})
            except sqlite3.OperationalError:
                pass
            con.close()
            for sfx in ['', '-wal', '-shm']:
                try:
                    os.remove(loc + sfx)
                except OSError:
                    pass
        return favs
def _parse_share_links(text):
    """从(可能多行的)分享文案解析出 (标题, url) 列表。\n    例每行: 《凡修逆仙》免费看全集https://novelquickapp.com/s/xxxx/\n    优先按《》配对其后的 url; 无《》则只收 url。"""
    import re
    pairs = re.findall('《([^》]+)》[^《]*?(https?://[^\\s，,、）)】\\]《]+)', text)
    if pairs:
        return [(t, u) for t, u in pairs]
    else:
        return [(None, u) for u in re.findall('https?://[^\\s，,、）)】\\]]+', text)]
def _scrape_board(url):
    """榜单/热榜分享链接(top_list, 如 hot-list-share) → 抓页面 SSR 里的系列列表。\n    返回 [(series_id, title)]; 非榜单链接返回 []。榜单分享页把列表内嵌在 window._SSR_DATA\n    (转义 JSON 字符串)里, 逐个 series_id 就近配对 book_name/title。"""
    import re
    try:
        import requests
        r = requests.get(url, timeout=25, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 12)'})
    except Exception:
        return []
    t = r.text
    if 'hot-list-share' not in r.url and 'top_list' not in t and ('_SSR_DATA' not in t):
        return []
    else:
        def grab(marker):
            i = t.find(marker)
            if i < 0:
                return ''
            else:
                j = t.find('</script>', i)
                return t[i:j if j > 0 else i + 200000]
        blob = grab('window._SSR_DATA') + '\n' + grab('window._ROUTER_DATA')
        un = blob
        for _ in range(3):
            un2 = un.replace('\\\\', '\\').replace('\\\"', '\"').replace('\\/', '/')
            un2 = re.sub('\\\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), un2)
            if un2 == un:
                break
            else:
                un = un2
        out, seen = ([], set())
        for m in re.finditer('\"series_id\"\\s*:\\s*\"?(\\d{15,})\"?', un):
            sid = m.group(1)
            if sid in seen:
                continue
            else:
                win = un[max(0, m.start() - 600):m.start() + 600]
                tm = re.search('\"(?:book_name|title|series_name|bookName)\"\\s*:\\s*\"([^\"]{1,60})\"', win)
                if tm:
                    seen.add(sid)
                    out.append((sid, tm.group(1)))
        return out
def _resolve_share_one(url):
    """解析单条短链 → 候选 series_id 列表(video_id 优先, content/vid 兜底)。"""
    import re
    from urllib.parse import unquote
    cands = []
    if not url:
        return cands
    else:
        try:
            import requests
            r = requests.get(url, timeout=25, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 12)'})
            dec = unquote(unquote(r.url + ' ' + r.text[:8000]))
            for key in ['video_series_id', 'video_id', 'series_id', 'book_id', 'material_id', 'content_id', 'vid']:
                for v in re.findall(key + '[\\\"\':= ]{1,4}(\\d{15,})', dec):
                    if v not in cands:
                        cands.append(v)
        except Exception as ex:
            log(f'[url] 短链 {url} 解析失败({ex})')
        return cands
def _hgdj_series_id(url):
    """hongguoduanju.com detail 链接 → 其 series_id(与 红果 series_id 完全一致)。\n    只从 URL 文本解析 id, 不请求 hongguoduanju.com; 之后用现有 红果 方法下载。"""
    if not url or 'hongguoduanju.com' not in url.lower():
        return None
    else:
        m = re.search('series_id=(\\d{15,})', url)
        return m.group(1) if m else None
def _resolve_series(title, url):
    """把 (标题,url) 解析成已验证的 (series_id, title, episodes) 或 (None,title,None)。\n    候选来源: 短链里的 video_id 等 + 标题搜索; 逐个 get_episodes 验证, 标题匹配优先。"""
    _sid = _hgdj_series_id(url)
    if _sid:
        try:
            _m, _e = H.get_episodes(_sid, max_retries=1, timeout=8, sign_timeout=8)
            if _e:
                return (_sid, _m.get('title'), _e, _m.get('cover') or '')
            else:
                log(f'[hgdj] series_id {_sid} 无剧集 (已下架)')
                return (None, title, None, '')
        except Exception as ex:
            log(f'[hgdj] series_id {_sid} 取集失败 (可能已下架): {ex}')
            return (None, title, None, '')
    else:
        cands = _resolve_share_one(url)
        if title:
            try:
                for x in (H.search(title) or [])[:3]:
                    if str(x['series_id']) not in cands:
                        cands.append(str(x['series_id']))
            except Exception:
                pass
        fallback = None
        for c in cands:
            try:
                m2, e2 = H.get_episodes(c)
            except Exception:
                continue
            t2 = m2.get('title', '')
            if not title or title in t2 or t2 in title:
                return (c, m2.get('title'), e2, m2.get('cover') or '')
            else:
                if fallback is None:
                    fallback = (c, m2.get('title'), e2, m2.get('cover') or '')
        return fallback if fallback else (None, title, None, '')
def _load_favjson():
    if os.path.exists(FAV_JSON):
        try:
            return json.load(open(FAV_JSON, encoding='utf-8'))
        except Exception:
            pass
    return {'updated': 0, 'series': {}}
def _save_favjson(data):
    os.makedirs(OUT, exist_ok=True)
    data['updated'] = int(time.time())
    tmp = FAV_JSON + '.tmp'
    json.dump(data, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.replace(tmp, FAV_JSON)
def _video_model(vid):
    body = {'biz_param': {'detail_page_version': 0, 'device_level': 3, 'disable_digg_stat': False, 'disable_video_relate_book': False, 'need_all_video_definition': True, 'need_mp4_align': False, 'use_os_player': False, 'use_server_dns': False, 'video_platform': 1024}, 'mixed_video_id_map': {'1': [str(vid)]}}
    d = H.api('POST', '/novel/player/multi_video_model/v1/', body=body).get('data', {})
    v = d.get(str(vid)) or (list(d.values())[0] if d else None)
    if not v or not v.get('video_model'):
        return None
    else:
        return json.loads(v['video_model'])
def _defn(t):
    return ((t.get('video_meta') or {}).get('definition') or '').lower()
def _sz(t):
    return (t.get('video_meta') or {}).get('size', 0) or 0
def _dnum(t):
    return int(re.sub('\\D', '', _defn(t)) or 0)
def list_quals(vm):
    """返回 [(definition, size, wxh, codec, encrypt)] 按分辨率升序。"""
    out = []
    for t in vm.get('video_list', []):
        m = t.get('video_meta') or {}
        out.append((_defn(t) or '?', _sz(t), f"{m.get('vwidth')}x{m.get('vheight')}", m.get('codec_type') or t.get('codec_type'), (t.get('encrypt_info') or {}).get('encrypt')))
    return sorted(out, key=lambda x: int(re.sub('\\D', '', x[0]) or 0))
def _pick_track(tracks, quality='best'):
    """按清晰度选轨。tracks: video_list 轨道列表。quality: best(默认)/worst/1080p/720p/540p/480p/360p(或纯数字)。\n    指定清晰度不存在时取 <=请求 的最高一档(没有则最低)。返回 (track, 实际definition, 是否回退)。"""
    tracks = tracks or []
    if not tracks:
        return (None, None, False)
    else:
        q = str(quality or 'best').lower().strip()
        if q in ['best', 'max', 'high', 'highest']:
            t = max(tracks, key=_sz)
            return (t, _defn(t), False)
        else:
            if q in ['worst', 'min', 'low', 'lowest']:
                t = min(tracks, key=_sz)
                return (t, _defn(t), False)
            else:
                qnum = re.sub('\\D', '', q)
                exact = [t for t in tracks if _defn(t) == q or (qnum and re.sub('\\D', '', _defn(t)) == qnum)]
                if exact:
                    t = max(exact, key=_sz)
                    return (t, _defn(t), False)
                else:
                    avail = sorted(tracks, key=_dnum)
                    le = [t for t in avail if qnum and _dnum(t) <= int(qnum)]
                    t = le[(-1)] if le else avail[0]
                    return (t, _defn(t), True)
def dl_vid(vid, name=None, retries=2, quiet=False, quality='1080p', tracks=None, outdir=None, on_bytes=None):
    # irreducible cflow, using cdg fallback
    """下载+解密单集; 返回输出路径或 None。各集独立文件, 线程安全。quality 见 _pick_track。\n    tracks: 预取的 video_list 轨道(批量签名得到); None 则自取。\n    outdir: 输出目录(整剧下载时=downloads/剧名/, 单集=downloads/)。\n    首次用预取轨道(不再签名); 重试时强制重取直链(force, 处理 URL 过期)——仅失败集才重签。"""
    # ***<module>.dl_vid: Failure: Compilation Error
    outdir = outdir or OUT
    os.makedirs(outdir, exist_ok=True)
    name = H.sanitize(name or str(vid))
    out = os.path.join(outdir, name + '.mp4')
    if os.path.exists(out) and os.path.getsize(out) > 0:
        if not quiet:
            log(f'[=] 跳过(已存在): {name}')
        return out
    m_legacy = re.search(r'第(\d+)集', name)
    if m_legacy:
        legacy_out = os.path.join(outdir, f"第{m_legacy.group(1)}集.mp4")
        if os.path.exists(legacy_out) and os.path.getsize(legacy_out) > 0:
            if not quiet:
                log(f'[=] 跳过(已存在): {os.path.basename(legacy_out)}')
            return legacy_out
    ct = os.path.join(outdir, name + '.enc.mp4')
    last = None
    for attempt in range(retries):
        try:
            tk = tracks if tracks and attempt == 0 else H.get_video_tracks([vid], force=attempt > 0).get(str(vid))
            if not tk:
                last = '无video_model'
                continue
            tr, gotdef, fallback = _pick_track(tk, quality)
            if not tr:
                last = '无video_list'
                continue
            enc = tr.get('encrypt_info') or {}
            meta = tr.get('video_meta') or {}
            if not quiet:
                fb = f' (无{quality}, 回退)' if fallback else ''
                log(f"[*] {name}  [{meta.get('definition')}{fb}, {(meta.get('size') or 0) // 1024}KB]")
            if not enc.get('encrypt'):
                H.download_file(tr['main_url'], out, on_bytes=on_bytes)
                return out
            H.download_file(tr['main_url'], ct, on_bytes=on_bytes)
            r = OD.offline_decrypt(enc.get('spade_a'), ct, out)
            final = out if os.path.exists(out) and os.path.getsize(out) > 0 else r
            if final and os.path.exists(final) and (os.path.getsize(final) > 0):
                if final != out:
                    try:
                        os.replace(final, out)
                        final = out
                    except OSError:
                        pass
                for tmp in [ct, os.path.splitext(out)[0] + '.raw.mp4']:
                    if tmp != final and os.path.exists(tmp):
                        try:
                            os.remove(tmp)
                        except OSError:
                            pass
                return final
            last = '解密失败'
        except Exception as ex:
            last = str(ex)
        if attempt + 1 < retries:
            if not quiet:
                log(f'    {name} 第{attempt + 1}次失败({last}), 重试...')
            time.sleep(1.5)
    log(f'[X] {name} 失败: {last}')
    try:
        if os.path.exists(ct):
            os.remove(ct)
    except OSError:
        pass
    dl_vid.last_error = last
    return None
class SeriesCtx:
    """一部剧的下载上下文: 状态/标题/集列表/清晰度 + 各自的状态锁。"""
    def __init__(self, sid, title, state, eps, quality):
        self.sid = sid
        self.title = title
        self.state = state
        self.eps = eps
        self.quality = quality
        self.lock = threading.Lock()
        self.tracks = {}
        self.folder = None
def _match_range(rng, idx):
    """rng='all' 或选择串 '1,3,5-8'(逗号分隔, 每段是单集或 a-b 区间); 判定单集 idx 是否入选。"""
    if not rng or rng == 'all':
        return True
    for tok in str(rng).split(','):
        tok = tok.strip()
        if not tok:
            continue
        if '-' in tok:
            a, _, b = tok.partition('-')
            try:
                if int(a) <= idx <= int(b):
                    return True
            except ValueError:
                pass
        elif tok.isdigit() and idx == int(tok):
            return True
    return False

def _download_poster(folder, cover_url):
    """把封面存进 folder/poster.jpg(HEIC/webp 自动转 JPEG; 已存在则跳过)。"""
    if not cover_url or not folder:
        return None
    jpg = os.path.join(folder, 'poster.jpg')
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(jpg) and os.path.getsize(jpg) > 0:
        return jpg
    try:
        r = H.http_request('GET', cover_url, timeout=30)
        r.raise_for_status()
        raw = r.content
        try:
            from PIL import Image
            import io as _io
            try:
                import pillow_heif
                pillow_heif.register_heif_opener()
            except Exception:
                pass
            Image.open(_io.BytesIO(raw)).convert('RGB').save(jpg, 'JPEG', quality=88)
        except Exception:
            dest = os.path.join(folder, 'poster' + H.img_ext(cover_url))
            with open(dest, 'wb') as f:
                f.write(raw)
            jpg = dest
        log(f'  封面已存: {os.path.basename(jpg)}')
        return jpg
    except Exception as ex:
        log(f'  封面保存失败: {ex}')
        return None

def _save_poster(title, cover_url, folder=None):
    """整剧封面存进 folder/poster.jpg 或 OUT/剧名/poster.jpg。"""
    dst = folder or (os.path.join(OUT, title) if title else None)
    if dst:
        _download_poster(dst, cover_url)

def _save_series_meta(title, series_id, meta, folder=None):
    """把 series_id/title/total/cover/score 落进 剧名/.series.json。
    合并旧值: 保留 seen_at(用户上次查看该剧的时间, 用于高亮"新集")与已有 score。
    folder: 显式目标文件夹(Library 查新传入该剧的现有文件夹, 避免写进 OUT/title 的错位副本)。"""
    if not title and not folder:
        return
    folder = folder or os.path.join(OUT, title)
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, '.series.json')
    with _meta_lock:
        try:
            old = {}
            try:
                old = json.load(open(p, encoding='utf-8'))
            except Exception:
                pass
            data = {'series_id': str(series_id), 'title': meta.get('title') or title, 'total': int(meta.get('episode_cnt') or 0), 'cover': meta.get('cover') or '', 'score': CLICK_SCORES.get(str(series_id)) or meta.get('score') or '', 'seen_at': old.get('seen_at', 0), 'updated': int(time.time())}
            json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        except Exception:
            return None

HISTORY_FILE = os.path.join(_META, 'download_history.json')
POSTER_VAULT = os.path.join(_META, 'posters')
_history_lock = threading.Lock()

def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_history():
    init_history_cache()
    with _history_lock:
        return _load_history()

def record_download_history(series_id, title=None, title_km=None, total=0, downloaded=0, cover_url=None, completed=False, poster_file=None):
    if not series_id:
        return
    sid = str(series_id)
    os.makedirs(_META, exist_ok=True)
    os.makedirs(POSTER_VAULT, exist_ok=True)
    with _history_lock:
        hist = _load_history()
        cur = hist.get(sid) or {}
        now = int(time.time())
        cur['series_id'] = sid
        if title:
            cur['title'] = title
        if title_km:
            cur['title_km'] = title_km
        elif not cur.get('title_km') and cur.get('title'):
            try:
                import translator as TR
                cur['title_km'] = TR.translate_to_khmer(cur['title'])
            except Exception:
                pass
        if total:
            cur['total'] = int(total)
        if downloaded:
            cur['downloaded'] = max(int(downloaded), int(cur.get('downloaded', 0)))
        if cover_url:
            cur['cover_url'] = cover_url
        if completed or (cur.get('total') and cur.get('downloaded', 0) >= cur.get('total', 0) and cur.get('total', 0) > 0):
            cur['completed'] = True
            cur['completed_at'] = cur.get('completed_at') or now
        cur['first_at'] = cur.get('first_at') or now
        cur['updated_at'] = now

        vault_poster = os.path.join(POSTER_VAULT, f'{sid}.jpg')
        if poster_file and os.path.isfile(poster_file) and os.path.getsize(poster_file) > 0:
            try:
                import shutil
                if not os.path.exists(vault_poster) or os.path.getsize(vault_poster) == 0:
                    shutil.copyfile(poster_file, vault_poster)
            except Exception:
                pass
        elif cover_url and (not os.path.exists(vault_poster) or os.path.getsize(vault_poster) == 0):
            try:
                threading.Thread(target=_download_vault_poster, args=(vault_poster, cover_url), daemon=True).start()
            except Exception:
                pass
        cur['has_poster'] = os.path.exists(vault_poster) and os.path.getsize(vault_poster) > 0
        hist[sid] = cur
        try:
            tmp = HISTORY_FILE + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(hist, f, ensure_ascii=False, indent=1)
            os.replace(tmp, HISTORY_FILE)
        except Exception as e:
            log(f'Failed to save history: {e}')

def _download_vault_poster(vault_poster, cover_url):
    try:
        import requests
        os.makedirs(os.path.dirname(vault_poster), exist_ok=True)
        r = requests.get(cover_url, timeout=15)
        if r.status_code == 200 and len(r.content) > 500:
            with open(vault_poster, 'wb') as f:
                f.write(r.content)
    except Exception:
        pass

_history_inited = False
def init_history_cache():
    global _history_inited
    if _history_inited:
        return
    _history_inited = True
    os.makedirs(_META, exist_ok=True)
    os.makedirs(POSTER_VAULT, exist_ok=True)
    try:
        if os.path.isdir(OUT):
            for name in os.listdir(OUT):
                folder = os.path.join(OUT, name)
                if not os.path.isdir(folder) or name.startswith('.'):
                    continue
                meta = _lib_meta(folder)
                sid = str(meta.get('series_id') or '')
                if not sid:
                    continue
                eps_m = _lib_eps_mtime(folder)
                local = len(eps_m)
                total = int(meta.get('total') or 0)
                cover = meta.get('cover') or ''
                p_file = os.path.join(folder, 'poster.jpg')
                record_download_history(
                    sid,
                    title=meta.get('title') or name,
                    total=total,
                    downloaded=local,
                    cover_url=cover,
                    completed=(local >= total and total > 0) or local > 0,
                    poster_file=p_file if os.path.isfile(p_file) else None
                )
    except Exception as e:
        log(f'init_history_cache error: {e}')

_EP_RE = re.compile(r'^(?:.*_)?第(\d+)集\.mp4$')

def _lib_local_eps(folder):
    out = set()
    try:
        for f in os.listdir(folder):
            m = _EP_RE.match(f)
            if m and os.path.getsize(os.path.join(folder, f)) > 0:
                out.add(int(m.group(1)))
    except Exception:
        pass
    return out

def _series_folder(sid, title):
    """Best-effort output folder for a series: OUT/sanitized-title, else scan the library for the folder
    whose .series.json carries this series_id. May point at a not-yet-created folder (caller = 0 eps)."""
    sid = str(sid)
    cand = os.path.join(OUT, H.sanitize(title)) if title else ''
    if cand and os.path.isdir(cand):
        return cand
    try:
        for name in os.listdir(OUT):
            d = os.path.join(OUT, name)
            if os.path.isdir(d) and str(_lib_meta(d).get('series_id') or '') == sid:
                return d
    except Exception:
        pass
    return cand

def disk_done(sid, title, rng='all'):
    """Count episodes ACTUALLY present on disk for this series (within range). Source of truth for the
    queue progress bar — survives deleted/moved files, read-only libraries, and missing state files
    (fixes both the 'shows complete after delete' and 'stuck at queued' bugs)."""
    eps = _lib_local_eps(_series_folder(sid, title))
    if rng and rng != 'all':
        eps = {i for i in eps if _match_range(rng, i)}
    return len(eps)

def prune_orphan_state():
    """Delete persisted state files for series whose output folder no longer exists (moved/deleted).
    Hygiene so stale 'done' state never lingers; the queue bar already reads disk, this just tidies up."""
    n = 0
    try:
        for f in os.listdir(STATE_DIR):
            if not f.startswith('series_') or not f.endswith('.json'):
                continue
            p = os.path.join(STATE_DIR, f)
            try:
                st = json.load(open(p, encoding='utf-8'))
            except Exception:
                continue
            sid = st.get('series_id') or f[len('series_'):-len('.json')]
            folder = _series_folder(sid, st.get('title') or '')
            if not folder or not os.path.isdir(folder) or (not _lib_local_eps(folder)):
                try:
                    os.remove(p)
                    n += 1
                except Exception:
                    pass
    except Exception:
        pass
    return n

def _lib_eps_mtime(folder):
    """{集号: 文件mtime} for downloaded episodes (used to detect newly-added episodes)."""
    out = {}
    try:
        for f in os.listdir(folder):
            m = _EP_RE.match(f)
            if m:
                fp = os.path.join(folder, f)
                if os.path.getsize(fp) > 0:
                    out[int(m.group(1))] = os.path.getmtime(fp)
    except Exception:
        pass
    return out

def _lib_meta(folder):
    p = os.path.join(folder, '.series.json')
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding='utf-8'))
        except Exception:
            pass
    return {}

def _lib_write_seen(folder, ts):
    """Set seen_at in a series' .series.json (merges, keeps other fields)."""
    p = os.path.join(folder, '.series.json')
    with _meta_lock:
        try:
            d = _lib_meta(folder)
            if not d:
                return False
            d['seen_at'] = int(ts)
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
            return True
        except Exception:
            return False
def library_scan():
    """扫描 OUT 下每个剧文件夹(纯本地无网络) -> {items:[{name,series_id,title,local,total,new,poster,cover}], root}。"""
    init_history_cache()
    root = OUT
    items = []
    _now = time.time()
    try:
        names = sorted(os.listdir(root))
    except Exception:
        return {'items': [], 'root': root}
    for name in names:
        folder = os.path.join(root, name)
        if not os.path.isdir(folder) or name.startswith('.'):
            continue
        else:
            eps_m = _lib_eps_mtime(folder)
            local = len(eps_m)
            meta = _lib_meta(folder)
            if local == 0 and (not meta):
                    continue
            total = int(meta.get('total') or 0)
            seen_at = float(meta.get('seen_at') or 0)
            if seen_at <= 0:
                _lib_write_seen(folder, _now)
                seen_at = _now
                fresh = 0
            else:
                fresh = sum((1 for mt in eps_m.values() if mt > seen_at))
            items.append({'name': name, 'series_id': str(meta.get('series_id') or ''), 'title': meta.get('title') or name, 'local': local, 'total': total, 'new': max(0, total - local) if total else 0, 'fresh': fresh, 'score': meta.get('score') or '', 'updated': int(meta.get('updated') or 0), 'poster': meta.get('cover') or ''})
    return {'items': items, 'root': root}
def library_episodes(name):
    """某剧的本地集清单(供 Library 展开): 已下集号 + 哪些是\"新\"(上次查看后新增)。"""
    folder = os.path.join(OUT, name)
    if not os.path.isdir(folder):
        return
    else:
        meta = _lib_meta(folder)
        eps_m = _lib_eps_mtime(folder)
        seen_at = float(meta.get('seen_at') or 0)
        total = int(meta.get('total') or 0) or (max(eps_m) if eps_m else 0)
        episodes = [{'index': i, 'fresh': bool(seen_at > 0 and mt > seen_at)} for i, mt in sorted(eps_m.items())]
        return {'name': name, 'title': meta.get('title') or name, 'total': total, 'downloaded': sorted(eps_m.keys()), 'fresh': sum((1 for e in episodes if e['fresh'])), 'episodes': episodes}
def library_mark_seen(name):
    """把该剧标记为\"已查看\": seen_at=now, 清掉\"新集\"高亮(下次更新的集才算新)。"""
    return _lib_write_seen(os.path.join(OUT, name), time.time())
def rescan_state(root=None):
    """从磁盘上已存在的剧集文件重建下载进度状态。修复\"状态目录不可写\"这个 bug 造成的丢失:\n    剧集其实下载成功了, 但状态文件写进了只读安装目录 -> 丢跟踪 -> 进度停在 0。对 OUT 下每个带\n    .series.json(有 series_id)的剧文件夹, 把已存在的每一集在状态文件里标为 done(写进新的可写\n    STATE_DIR)。只新增/修复, 从不删除已有状态。返回修复的剧数。"""
    root = root or OUT
    fixed = 0
    try:
        names = [n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n)) and (not n.startswith('.'))]
    except Exception:
        return 0
    for name in names:
        folder = os.path.join(root, name)
        try:
            meta = _lib_meta(folder)
            sid = meta.get('series_id')
            if not sid:
                continue
            else:
                eps_m = _lib_eps_mtime(folder)
                if not eps_m:
                    continue
                else:
                    st = _load_state(sid)
                    state_eps = st.setdefault('episodes', {})
                    changed = False
                    for idx, mt in eps_m.items():
                        k = str(int(idx))
                        e = state_eps.get(k)
                        if e and e.get('status') == 'done':
                                continue
                        fp = os.path.join(folder, f'第{int(idx):03d}集.mp4')
                        state_eps[k] = {'vid': (e or {}).get('vid', ''), 'status': 'done', 'file': fp if os.path.exists(fp) else (e or {}).get('file', ''), 'attempts': (e or {}).get('attempts', 1), 'ts': int(mt)}
                        changed = True
                    if changed:
                        st['series_id'] = str(sid)
                        st['title'] = st.get('title') or meta.get('title') or name
                        _save_state(sid, st)
                        fixed += 1
        except Exception:
            continue
    return fixed
def _resolve_lib_sid(folder, title):
    try:
        sid = _lib_meta(folder).get('series_id')
        if sid:
            return str(sid)
        hits = H.search(title) or []
        for x in hits[:3]:
            t = x.get('title', '')
            if title and (title in t or t in title):
                return str(x['series_id'])
        if hits:
            return str(hits[0]['series_id'])
    except Exception:
        pass
    return None

def _backfill_score(folder, title, sid):
    """Add the rating ★ to a library series' .series.json. The detail API (multi_video_detail)
    does NOT return a score -- confirmed live -- so we look it up from search (which does, and
    matches by series_id). One-time + best-effort: skips once a score is saved, never raises."""
    try:
        if str(_lib_meta(folder).get('score') or '').strip():
            return False
        hits = H.search(title) or []
        score = ''
        for h in hits:
            if str(h.get('series_id')) == str(sid):
                score = str(h.get('score') or '').strip()
                break
        if not score:
            for h in hits:
                t = h.get('title', '')
                if t and (t == title or t in title or title in t):
                    score = str(h.get('score') or '').strip()
                    break
        if not score:
            return False
        p = os.path.join(folder, '.series.json')
        with _meta_lock:
            d = _lib_meta(folder) or {}
            if str(d.get('score') or '').strip():
                return False
            d['score'] = score
            json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
            _live_series(sid, score=score)
            return True
    except Exception:
        return False
def _download_series_missing(sid, folder, title, missing, eps, quality, ep_conc, retry_rounds):
    """Download one series\' missing episodes INTO its existing `folder`, `ep_conc` at a time,\n    to completion. `eps` is the fresh episode list from the scan; `missing` the indices to fetch."""
    missing_set = set((int(i) for i in missing))
    sel = [e for e in eps if int(e.get('index') or 0) in missing_set]
    if not sel:
        return
    else:
        st = _load_state(sid)
        st['title'] = H.sanitize(title)
        st['series_id'] = str(sid)
        st['quality'] = quality
        ctx = SeriesCtx(sid, H.sanitize(title), st, sel, quality)
        ctx.folder = folder
        try:
            ctx.tracks = H.get_video_tracks([e['vid'] for e in sel])
        except Exception as ex:
            log(f'  track prefetch failed for 《{title}》: {ex}')
        run_jobs([(ctx, e) for e in sel], ep_conc, retry_rounds)
def library_update(names, log_fn=None, quality='1080p', ep_conc=2, series_at_once=6, retry_rounds=2):
    """Streaming Library update. A batched checker (20 series per signed call, FRESH -- it bypasses\n    the 6h episode cache so brand-new episodes are actually seen) runs ahead and feeds a pool of\n    `series_at_once` download lanes. Each lane downloads one series\' missing/new episodes (`ep_conc`\n    at a time) into that series\' EXISTING folder, to completion, before taking the next series.\n    Checking and downloading overlap, so downloads start within seconds instead of after a full scan.\n    Live progress is reported into _LIVE (read by server /dl/status). names empty = whole library.\n\n    NOTE: no CANCEL.clear() here -- the caller (server /dl/library/update) clears it once at job start.\n    """
    # ***<module>.library_update: Failure: Different bytecode
    lg = log_fn or log
    root = OUT
    if not names:
        try:
            names = [n for n in sorted(os.listdir(root)) if os.path.isdir(os.path.join(root, n)) and (not n.startswith('.'))]
        except Exception:
            names = []
    targets = []
    for name in names:
        if CANCEL.is_set():
            break
        else:
            folder = os.path.join(root, name)
            if not os.path.isdir(folder):
                continue
            else:
                title = _lib_meta(folder).get('title') or name
                sid = _resolve_lib_sid(folder, title)
                if not sid:
                    lg(f'  ? can\'t identify 《{title}》, skipped')
                    continue
                else:
                    targets.append((name, folder, title, str(sid)))
    _live_reset(to_check=len(targets))
    for name, folder, title, sid in targets:
        _live_series(sid, name=name, title=title, state='pending')
    if not targets:
        lg('Library: nothing to check')
        _live_finish()
        return {'updated': 0}
    else:
        lg(f'Checking {len(targets)} series for new episodes (20 at a time)...')
        def _score_worker():
            try:
                with ThreadPoolExecutor(max_workers=2) as ex:
                    for _ in ex.map(lambda t: not CANCEL.is_set() and _backfill_score(t[1], t[2], t[3]), targets):
                        if CANCEL.is_set():
                            break
            except Exception:
                return None
        score_thread = threading.Thread(target=_score_worker, daemon=True)
        score_thread.start()
        by_sid = {sid: (name, folder, title) for name, folder, title, sid in targets}
        order = [sid for _, _, _, sid in targets]
        lanes = max(1, min(int(series_at_once or 6), 24))
        epc = max(1, min(int(ep_conc or 2), 8))
        work_q = queue.Queue()
        STOP = object()
        done_count = {'n': 0}
        dc_lock = threading.Lock()
        def producer():
            for i in range(0, len(order), 20):
                if CANCEL.is_set():
                    break
                else:
                    chunk = order[i:i + 20]
                    try:
                        res = H.get_episodes_multi(chunk, batch_size=20, force=True)
                    except Exception as ex:
                        lg(f'  x check batch failed: {ex}')
                        res = {}
                    for sid in chunk:
                        if CANCEL.is_set():
                            break
                        else:
                            name, folder, title = by_sid[sid]
                            me = res.get(sid)
                            if not me:
                                _live_series(sid, state='uptodate')
                                _live_checked(1)
                                continue
                            else:
                                meta, eps = me
                                server_idx = sorted((e['index'] for e in eps if e.get('index')))
                                local_idx = _lib_local_eps(folder)
                                missing = [x for x in server_idx if x not in local_idx]
                                try:
                                    _save_series_meta(title, sid, meta, folder=folder)
                                    if not os.path.exists(os.path.join(folder, 'poster.jpg')):
                                        _download_poster(folder, meta.get('cover'))
                                except Exception:
                                    pass
                                total = len(server_idx)
                                if missing:
                                    _live_series(sid, state='queued', have=len(local_idx), total=total, need=len(missing), dl_done=0)
                                    _live_checked(1, found=1)
                                    lg(f'  + 《{title}》 {len(missing)} new episode(s)')
                                    work_q.put((sid, folder, title, missing, eps))
                                else:
                                    _live_series(sid, state='uptodate', have=len(local_idx), total=total)
                                    _live_checked(1)
            with _LIVE_LOCK:
                _LIVE['phase'] = 'downloading'
            for _ in range(lanes):
                work_q.put(STOP)
        def lane():
            while True:
                job = work_q.get()
                if job is STOP:
                    return
                else:
                    if CANCEL.is_set():
                        continue
                    else:
                        sid, folder, title, missing, eps = job
                        _live_series(sid, state='downloading')
                        try:
                            _download_series_missing(sid, folder, title, missing, eps, quality, epc, retry_rounds)
                            _live_series(sid, state='cancelled' if CANCEL.is_set() else 'done')
                            if not CANCEL.is_set():
                                with dc_lock:
                                    done_count['n'] += 1
                        except Exception as ex:
                            _live_series(sid, state='error')
                            lg(f'  x 《{title}》 update failed: {ex}')
        prod = threading.Thread(target=producer, daemon=True)
        prod.start()
        lane_threads = [threading.Thread(target=lane, daemon=True) for _ in range(lanes)]
        for t in lane_threads:
            t.start()
        prod.join()
        for t in lane_threads:
            t.join()
        score_thread.join(timeout=8)
        _live_finish(cancelled=CANCEL.is_set())
        if CANCEL.is_set():
            lg('Library update cancelled')
        else:
            lg(f"Library update done — {done_count['n']} series updated")
        return {'updated': done_count['n']}
def _prepare(series_id, rng, quality, rank=None):
    """取剧集+范围过滤+加载状态, 返回 (ctx, pending待下集, skipped已完成数)。"""
    meta, eps = H.get_episodes(series_id)
    raw_title = H.sanitize(meta['title'])
    ep_cnt = meta.get('episode_cnt') or len(eps) or 0
    # Add video rank to front and episode count to end of folder name:
    # "លេខរឿងនៅពីមុខវិញ បែបនេះ [No.70] 长公主蜀道山，皇帝连夜下诏罪己 (61ភាគ)"
    suffix = f" ({ep_cnt}ភាគ)" if ep_cnt else ""
    if rank:
        try:
            r_num = int(rank)
            prefix = f"[No.{r_num:02d}] "
        except Exception:
            prefix = f"[{rank}] "
        folder_title = f"{prefix}{raw_title}{suffix}"
    else:
        folder_title = f"{raw_title}{suffix}"

    folder = _series_folder(series_id, folder_title)
    os.makedirs(folder, exist_ok=True)
    _save_poster(folder_title, meta.get('cover'), folder=folder)
    _save_series_meta(folder_title, series_id, meta, folder=folder)

    # Automatic Khmer translation for title and save text file:
    # "បន្ថែមសមត្ថភាព បង្ហាញ ចំណងជើងជាភាសាខ្មែរ ដោយស្វ័យប្រវត្តិ ក្រោមអក្សចិន នៅពេលdownload ចំណងជើងរឿងភាសាខ្មែរ យកទៅជាមួយដែរ ជាfile text"
    title_km = ''
    try:
        import translator as TR
        title_km = TR.translate_to_khmer(meta.get('title') or raw_title)
    except Exception:
        pass

    info_file = os.path.join(folder, 'ចំណងជើងរឿង_Khmer_Title.txt')
    try:
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("==================================================\n")
            f.write("🎬 ព័ត៌មានរឿង / DRAMA INFORMATION\n")
            f.write("==================================================\n")
            f.write(f"🇰🇭 ចំណងជើងភាសាខ្មែរ (Khmer Title) : {title_km}\n")
            f.write(f"🇨🇳 ចំណងជើងដើម (Chinese Title)       : {meta.get('title') or raw_title}\n")
            f.write(f"🔢 ចំនួនភាគសរុប (Total Episodes)     : {ep_cnt} ភាគ\n")
            f.write(f"🆔 លេខសម្គាល់ (Series ID)            : {series_id}\n")
            if rank:
                f.write(f"🏆 លេខរៀង Poster (Rank)             : No.{int(rank):02d}\n")
            f.write(f"📁 ថតរក្សាទុក (Folder Name)           : {os.path.basename(folder)}\n")
            f.write("==================================================\n")
            f.write("ទាញយកដោយ Hongguo Downloader\n")
        log(f"  ✓ បានរក្សាទុកចំណងជើងខ្មែរ: {title_km or 'N/A'} ចូលក្នុង {os.path.basename(info_file)}")
    except Exception as e:
        log(f"  Failed to write Khmer title text file: {e}")

    p_file = os.path.join(folder, 'poster.jpg')
    record_download_history(
        series_id,
        title=meta.get('title') or raw_title,
        title_km=title_km,
        total=ep_cnt,
        cover_url=meta.get('cover'),
        poster_file=p_file if os.path.isfile(p_file) else None
    )
    st = _load_state(series_id)
    st['title'] = os.path.basename(folder)
    st['series_id'] = str(series_id)
    st['quality'] = quality
    if rank:
        st['rank'] = rank
    if rng and rng != 'all':
        eps = [e for e in eps if _match_range(rng, e['index'] or 0)]
    if rng == 'all' and ep_cnt and (len(eps) < ep_cnt):
        log(f'  ⚠《{raw_title}》标称 {ep_cnt} 集, 接口只返回 {len(eps)} 集(可能分页/部分未上架)')
    ctx = SeriesCtx(series_id, st['title'], st, eps, quality)
    ctx.folder = folder
    pending = [e for e in eps if not _is_done(st, e['index'])]
    rng_lbl = f'1-{len(eps)}' if rng == 'all' else rng
    log(f"《{st['title']}》共 {ep_cnt or '?'} 集 | {meta['status']} | 目标 {rng_lbl}({len(eps)}集) | 跳过已完成 {len(eps) - len(pending)} | 待下 {len(pending)} | 清晰度 {quality}")
    if pending:
        try:
            ctx.tracks = H.get_video_tracks([e['vid'] for e in pending])
            log(f'  预取直链 {len(ctx.tracks)}/{len(pending)} 集 (批量签名~{(len(pending) + 4) // 5}次, 替代逐集{len(pending)}次)')
        except Exception as ex:
            log(f'  预取直链失败, 将逐集回退取流: {ex}')
    return (ctx, pending, len(eps) - len(pending))
def _episode_task(ctx, e):
    """下载+解密一集并更新该剧状态(线程安全, 增量落盘)。返回 bool 成功。"""
    if CANCEL.is_set():
        return False
    else:
        idx = e['index']
        outdir = ctx.folder or os.path.join(OUT, ctx.title)
        def _cb(d, t):
            speed_tracker.report_chunk(ctx.sid, idx, d, t)
            if _live_running():
                _live_ep_bytes(ctx.sid, idx, d, t)
        ep_name = f"{H.sanitize(ctx.title)}_第{idx or 0:03d}集"
        path = dl_vid(e['vid'], ep_name, retries=2, quality=ctx.quality, tracks=ctx.tracks.get(str(e['vid'])), outdir=outdir, on_bytes=_cb)
        speed_tracker.ep_done(ctx.sid, idx)
        _live_ep_done(ctx.sid, idx, ok=bool(path))
        with ctx.lock:
            ent = ctx.state['episodes'].setdefault(str(idx), {'vid': e['vid'], 'attempts': 0})
            ent['vid'] = e['vid']
            ent['attempts'] = ent.get('attempts', 0) + 1
            ent['ts'] = int(time.time())
            if path:
                ent['status'] = 'done'
                ent['file'] = path
                ent.pop('error', None)
            else:
                ent['status'] = 'failed'
                ent['error'] = getattr(dl_vid, 'last_error', '?')
            _save_state(ctx.sid, ctx.state)
        return bool(path)
def run_jobs(jobs, cap, retry_rounds):
    # irreducible cflow, using cdg fallback
    """全局并发池跑所有 (ctx, episode) 任务; cap=全局并发上限(跨剧共享); 失败自动多轮重试。"""
    # ***<module>.run_jobs: Failure: Different control flow
    if not jobs:
        return
    cnt = {'ok': 0, 'fail': 0}
    clock = threading.Lock()
    t0 = time.time()
    todo = jobs
    rnd = 0
    while todo:
        total = len(todo)
        cnt['ok'] = cnt['fail'] = 0
        def work(ctx, e):
            if CANCEL.is_set():
                return
            else:
                ok = _episode_task(ctx, e)
                with clock:
                    cnt['ok' if ok else 'fail'] += 1
                    n = cnt['ok'] + cnt['fail']
                    log(f"    进度 {n}/{total}  (成功{cnt['ok']} 失败{cnt['fail']})")
        actual_cap = get_concurrency(cap)
        with ThreadPoolExecutor(max_workers=actual_cap) as ex:
            list(as_completed([ex.submit(work, ctx, e) for ctx, e in todo]))
        if CANCEL.is_set():
            log('  [已取消]')
            break
        failed = [(ctx, e) for ctx, e in todo if not _is_done(ctx.state, e['index'])]
        if not failed or rnd >= retry_rounds:
            break
        rnd += 1
        log(f'\n[全局重试 {rnd}/{retry_rounds}] 失败 {len(failed)} 集, 退避后重试...')
        time.sleep(3 * rnd)
        todo = failed
    log(f'  (本批 {len(jobs)} 任务用时 {int(time.time() - t0)}s)')
def _summary(ctx):
    okn = sum((1 for e in ctx.eps if _is_done(ctx.state, e['index'])))
    fail = sorted((int(i) for i, e in ctx.state['episodes'].items() if e.get('status') != 'done' and any((ep['index'] or 0 == int(i) for ep in ctx.eps))))
    log(f'《{ctx.title}》完成 {okn}/{len(ctx.eps)} 集' + (f', 仍失败: {fail}' if fail else ' ✓'))
    if fail:
        log(f'    可重跑补齐: python offline_dl.py resume {ctx.sid}')
    return {'ok': okn, 'fail': len(fail), 'total': len(ctx.eps)}
def dl_series(series_id, rng='all', concurrency=4, retry_rounds=2, quality='best'):
    ctx, pending, _ = _prepare(series_id, rng, quality)
    if not pending:
        log(f'《{ctx.title}》全部已完成 ✓ -> {OUT}')
        return _summary(ctx)
    else:
        log(f'  全局并发 {concurrency}')
        run_jobs([(ctx, e) for e in pending], concurrency, retry_rounds)
        return _summary(ctx)
_MAX_TOTAL_EP_THREADS = 64
_CURRENT_CONC = 8
_CURRENT_CONC_LOCK = threading.Lock()

def set_concurrency(c):
    global _CURRENT_CONC
    with _CURRENT_CONC_LOCK:
        _CURRENT_CONC = max(1, min(int(c or 4), 16))
    seg_map = {1: 2, 2: 3, 4: 4, 6: 6, 8: 8, 12: 8, 16: 10}
    os.environ['HG_DL_SEGMENTS'] = str(seg_map.get(_CURRENT_CONC, 8))
    log(f'[Speed] Live concurrency set to {_CURRENT_CONC} (segments: {os.environ["HG_DL_SEGMENTS"]})')

def get_concurrency(fallback=None):
    with _CURRENT_CONC_LOCK:
        return _CURRENT_CONC if _CURRENT_CONC else (fallback or 8)

def dl_batch(series_ids, concurrency=4, retry_rounds=2, quality='best', ranges=None, series_at_once=3, ranks=None):
    if concurrency:
        set_concurrency(concurrency)
    ranges = ranges or {}
    ranks = ranks or {}
    series_ids = [str(s) for s in series_ids]
    par = max(1, min(int(series_at_once or 1), 6))
    ep_conc = max(1, min(int(concurrency or get_concurrency() or 4), 16))
    ep_conc = max(1, min(ep_conc, max(1, _MAX_TOTAL_EP_THREADS // par)))
    prepared = []
    for sid in series_ids:
        if CANCEL.is_set():
            break
        try:
            ctx, pending, _ = _prepare(sid, ranges.get(sid, 'all'), quality, rank=ranks.get(sid))
            prepared.append((ctx, pending))
        except Exception as ex:
            log(f'[X] 剧 {sid} 准备失败: {ex}')
    log(f'\n=== 多剧下载: {len(prepared)} 部剧, 同时 {par} 部, 每部集并发 {ep_conc} -> {OUT} ===')
    def _run(ctx, pending):
        if pending and (not CANCEL.is_set()):
            run_jobs([(ctx, e) for e in pending], ep_conc, retry_rounds)
        summ = _summary(ctx)
        okn = summ.get('ok', 0)
        tot = summ.get('total', 0)
        p_file = os.path.join(ctx.folder, 'poster.jpg') if hasattr(ctx, 'folder') and ctx.folder else None
        record_download_history(
            ctx.sid,
            title=ctx.title,
            total=tot,
            downloaded=okn,
            completed=(okn >= tot and tot > 0),
            poster_file=p_file if p_file and os.path.isfile(p_file) else None
        )
        return summ
    results = []
    if par <= 1:
        for ctx, pending in prepared:
            if CANCEL.is_set():
                break
            else:
                results.append(_run(ctx, pending))
    else:
        with ThreadPoolExecutor(max_workers=par) as ex:
            futs = [ex.submit(_run, ctx, pending) for ctx, pending in prepared]
            for f in as_completed(futs):
                try:
                    results.append(f.result())
                except Exception as ex2:
                    log(f'[X] {ex2}')
    tot_ok = sum((r.get('ok', 0) for r in results))
    tot_all = sum((r.get('total', 0) for r in results))
    log(f'\n=== 批量完成: {tot_ok}/{tot_all} 集, {len(prepared)} 部剧 -> {OUT} ===')
def show_status(series_id):
    st = _load_state(series_id)
    eps = st.get('episodes', {})
    done = [int(i) for i, e in eps.items() if e.get('status') == 'done']
    fail = [int(i) for i, e in eps.items() if e.get('status') != 'done']
    log(f"《{st.get('title') or series_id}》 已完成 {len(done)} 集" + (f', 失败/未完成: {sorted(fail)}' if fail else ' (无失败)'))
    for i in sorted(fail):
        log(f"    第{i:03d}集 failed: {eps[str(i)].get('error', '?')} (试过{eps[str(i)].get('attempts', 0)}次)")
def _pop_opts(args):
    """取出 -c N / -r N / -q 清晰度; 返回(剩余, 并发, 重试轮, 清晰度)。默认清晰度 1080p。"""
    c, r, q, rest, i = (4, 2, '1080p', [], 0)
    while i < len(args):
        if args[i] in ('-c', '--concurrency') and i + 1 < len(args):
            c = max(1, int(args[i + 1]))
            i += 2
        else:
            if args[i] in ['-r', '--retry'] and i + 1 < len(args):
                r = max(0, int(args[i + 1]))
                i += 2
            else:
                if args[i] in ['-q', '--quality'] and i + 1 < len(args):
                    q = args[i + 1]
                    i += 2
                else:
                    rest.append(args[i])
                    i += 1
    return (rest, c, r, q)
def main():
    # irreducible cflow, using cdg fallback
    # ***<module>.main: Failure: Compilation Error
    if len(sys.argv) < 2:
        print(__doc__)
        return
    else:
        cmd = sys.argv[1]
        CANCEL.clear()
        rest, conc, rr, q = _pop_opts(sys.argv[2:])
        if cmd == 'search':
            for x in H.search(rest[0]):
                print(f"  {x['series_id']}  [{x['episode_cnt']}集] ★{x.get('score', '')}  {x['title']}")
        else:
            if cmd == 'rank':
                for x in H.rank(rest[0] if rest else 'recommend'):
                    print(f"  {x['rank']:>2}. {x['series_id']}  [{x['episode_cnt']}集]  {x['title']}")
            else:
                if cmd == 'quals':
                    vm = _video_model(rest[0])
                    if not vm:
                        print('无 video_model')
                        return
                    else:
                        print(f'vid {rest[0]} 可选清晰度:')
                        for d, sz, wh, codec, enc in list_quals(vm):
                            print(f'  {d:>7}  {sz // 1024:>7}KB  {wh:>10}  codec={codec}  encrypt={enc}')
                else:
                    if cmd == 'series':
                        dl_series(rest[0], rest[1] if len(rest) > 1 else 'all', concurrency=conc, retry_rounds=rr, quality=q)
                    else:
                        if cmd == 'resume':
                            dl_series(rest[0], 'all', concurrency=conc, retry_rounds=rr, quality=q)
                        else:
                            if cmd == 'url':
                                if len(rest) == 1 and os.path.isfile(rest[0]):
                                    text = open(rest[0], encoding='utf-8').read()
                                    log(f'[url] 从文件读取: {rest[0]}')
                                else:
                                    text = '\n'.join(rest)
                                links = _parse_share_links(text)
                                if not links:
                                    log('[url] 未找到分享链接')
                                    return
                                else:
                                    log(f'[url] 解析 {len(links)} 条分享链接...')
                                    ids, seen = ([], set())
                                    for title, u in links:
                                        board = _scrape_board(u)
                                        if board:
                                            log(f'  ★ 榜单: {len(board)} 部')
                                            for bsid, btitle in board:
                                                if bsid not in seen:
                                                    seen.add(bsid)
                                                    ids.append(bsid)
                                                    log(f'     · 《{btitle}》 {bsid}')
                                        else:
                                            sid, tname, eps, _cov = _resolve_series(title, u)
                                            if sid and sid not in seen:
                                                seen.add(sid)
                                                ids.append(sid)
                                                log(f'  ✓ 《{tname}》 series_id={sid} ({len(eps)}集)')
                                            else:
                                                if sid:
                                                    log(f'  = 《{tname}》 重复, 跳过')
                                                else:
                                                    log(f"  ✗ 无法解析: 《{title or '?'}》 {u}")
                                    if not ids:
                                        log('[url] 没有可下载的剧')
                                        return
                                    else:
                                        log(f'\n=== 下载 {len(ids)} 部 (已下完自动跳过, 只补缺集/新集; 全局并发 {conc}, 清晰度 {q}) ===')
                                        dl_batch(ids, concurrency=conc, retry_rounds=rr, quality=q)
                            else:
                                if cmd == 'favsync':
                                    only_list = bool(rest and rest[0] == 'list')
                                    store = _load_favjson()
                                    try:
                                        db = _grab_favorites()
                                        for it in db:
                                            s = store['series'].setdefault(it['series_id'], {})
                                            s.setdefault('name', it['name'])
                                            s['fav_series_cnt'] = it.get('series_cnt') or s.get('fav_series_cnt')
                                            s['content_type'] = it.get('content_type')
                                            s['last_seen'] = int(time.time())
                                            s.pop('unfavorited', None)
                                        if db:
                                            log(f'[favsync] 设备实时增补 {len(db)} 部合并进收藏库')
                                    except Exception as ex:
                                        log(f'[favsync] 设备实时抓取跳过({ex}); 用已存 favorites.json')
                                    _save_favjson(store)
                                    ids = [sid for sid, s in store['series'].items() if not s.get('unfavorited')]
                                    log(f'[favsync] 收藏共 {len(ids)} 部 (favorites.json):')
                                    for sid in ids:
                                        s = store['series'][sid]
                                        log(f"  {sid}  [{s.get('fav_series_cnt')}集]  {s.get('name')}")
                                    if only_list or not ids:
                                        if not ids:
                                            log('(收藏为空; 先用截图抓取填充 favorites.json)')
                                        return None
                                    else:
                                        log(f'\n=== 同步下载 {len(ids)} 部收藏: 跳过已下完, 自动补缺集/新集 (-c {conc}, 清晰度 {q}) ===')
                                        dl_batch(ids, concurrency=conc, retry_rounds=rr, quality=q)
                                        for sid in ids:
                                            st = _load_state(sid)
                                            done = sum((1 for e in st.get('episodes', {}).values() if e.get('status') == 'done'))
                                            store['series'][sid]['downloaded_eps'] = done
                                            store['series'][sid]['last_sync'] = int(time.time())
                                        _save_favjson(store)
                                        log(f'[favsync] 完成; 收藏+下载状态已存 {os.path.relpath(FAV_JSON, ROOT)}')
                                else:
                                    if cmd == 'fixaudio':
                                        import glob
                                        from decutil import strip_cenc
                                        target = rest[0] if rest else OUT
                                        files = [target] if os.path.isfile(target) else glob.glob(os.path.join(target, '**', '*.mp4'), recursive=True)
                                        fixed = skipped = 0
                                        for f in files:
                                            tmp = f + '.fixtmp'
                                            try:
                                                r = strip_cenc(f, tmp)
                                                if r:
                                                    os.replace(tmp, f)
                                                    fixed += 1
                                                    log(f'  [✓] 修复 {os.path.relpath(f, ROOT)}')
                                                else:
                                                    skipped += 1
                                            except Exception as ex:
                                                log(f'  [X] {f}: {ex}')
                                                skipped += 1
                                            finally:
                                                if os.path.exists(tmp):
                                                    try:
                                                        os.remove(tmp)
                                                    except OSError:
                                                        pass
                                        log(f'\nfixaudio 完成: 修复 {fixed} 个, 跳过(已正常/无需) {skipped} 个 -> {target}')
                                    else:
                                        if cmd == 'status':
                                            show_status(rest[0])
                                        else:
                                            if cmd == 'vid':
                                                dl_vid(rest[0], rest[1] if len(rest) > 1 else None, quality=q)
                                            else:
                                                if cmd == 'batch':
                                                    dl_batch(rest, concurrency=conc, retry_rounds=rr, quality=q)
                                                else:
                                                    if cmd == 'collection':
                                                        items = H.get_collection()
                                                        log(f'我的收藏/追剧: {len(items)} 部短剧')
                                                        for it in items:
                                                            log(f"  {it['series_id']}  {it['name']}")
                                                        if rest and rest[0] == 'list':
                                                            return
                                                        ids = [it['series_id'] for it in items]
                                                        if not ids:
                                                            log('(收藏为空, 或都是小说/漫剧未纳入)')
                                                            return
                                                        else:
                                                            log(f'\n=== 开始并行下载我的收藏 {len(ids)} 部 (全局并发 {conc}, 清晰度 {q}, 已下架自动跳过) ===')
                                                            dl_batch(ids, concurrency=conc, retry_rounds=rr, quality=q)
                                                    else:
                                                        print(__doc__)
if __name__ == '__main__':
    main()