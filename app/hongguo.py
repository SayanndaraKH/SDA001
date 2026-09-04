# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\hongguo.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-09-01 08:27:58 UTC (1788251278)

global _dm
global _oracle
global _last_refresh
# ***<module>: Failure: Different bytecode
"""红果短剧下载器 (命令行)\n依赖: Frida 签名预言机(模拟器后台运行红果 + frida-server)。\n\n用法:\n  python hongguo.py search \"极品皇太子\"          # 搜索,列出剧\n  python hongguo.py episodes <series_id>          # 列出某剧全部剧集\n  python hongguo.py rank [recommend|hot|new] [数量]  # 漫剧榜单(推荐/热播/新剧)\n  python hongguo.py latest [short_play|comic_series|ai_series] [--all]  # 今日上新(--all=最新上架全部)\n  python hongguo.py filters [short_play|comic_series|ai_series]   # 列出该体裁全部筛选条件(及参数id)\n  python hongguo.py browse <体裁> [--theme 主题][--setting 设定][--bg 背景][--sort 排序][--gender 受众][--status 状态(仅漫剧)][--days 7][--n 60]\n  python hongguo.py download <series_id> [集号范围]  # 下载,如 1-10 或 all(默认all)\n\n例: python hongguo.py download 7638207474180312089 1-3\n例: python hongguo.py browse ai_series --theme 玄幻 --setting 逆袭 --sort hot_score --days 7\n程序内: filters(genre) / browse(genre, theme=, setting=, background=, sort=, gender=, days=, max_items=)\n"""
import sys
import os
import json
import time
import hashlib
import re
import subprocess
import threading
import urllib3
import requests

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    import frida
except Exception:
    frida = None
import safeguards as SG
from safeguards import RiskControlError, AuthExpiredError, ContentUnavailableError
import downloader as DL
import devicepool
IMPERSONATE = os.environ.get('IMPERSONATE', 'chrome')
HONGGUO_PROXY = os.environ.get('HONGGUO_PROXY', '').strip()
try:
    from curl_cffi import requests as _cffi
    _HAS_CFFI = True
except Exception:
    _cffi = None
    _HAS_CFFI = False
def _ext_proxies():
    return {'http': HONGGUO_PROXY, 'https': HONGGUO_PROXY} if HONGGUO_PROXY else None
import threading as _th
_tls = _th.local()
def _ext_session():
    s = getattr(_tls, 'ext', None)
    if s is None:
        if _HAS_CFFI and IMPERSONATE:
            s = _cffi.Session()
        else:
            s = requests.Session()
            ad = requests.adapters.HTTPAdapter(pool_connections=16, pool_maxsize=32, max_retries=0)
            s.mount('https://', ad)
            s.mount('http://', ad)
        _tls.ext = s
    return s
def http_request(method, url, **kw):
    """对外部(红果/CDN)发请求: 线程本地 Session 复用连接 + verify=False + 代理 + curl_cffi 指纹伪装。\n    curl_cffi 未安装或 IMPERSONATE 为空 → 透明退回原生 requests(行为不变)。"""
    kw.setdefault('verify', False)
    if HONGGUO_PROXY:
        kw.setdefault('proxies', _ext_proxies())
    s = _ext_session()
    if _HAS_CFFI and IMPERSONATE:
            kw.setdefault('impersonate', IMPERSONATE)
    return s.request(method, url, **kw)
urllib3.disable_warnings()
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, 'config.json'), encoding='utf-8'))
ADB = os.environ.get('ADB', 'D:\\Program Files\\Netease\\MuMu Player 12\\shell\\adb.exe')
DEV = os.environ.get('ADB_DEVICE', '127.0.0.1:16384')
FRIDA_HOST = os.environ.get('FRIDA_HOST', '127.0.0.1:27042')
HOST = CFG['api_host']
OUT_DIR = os.path.join(HERE, 'downloads')
_pool = devicepool.load_pool(CFG['base_query'])
def rotate_device():
    """主动换下一台池设备(无池时无操作)。可在每部剧/每会话开始调用以分散身份。"""
    if _pool:
        return _pool.rotate()
IMAGE_SHRINK = 'W3siaW1hZ2VfdHlwZSI6MywiaW1hZ2Vfd2lkdGgiOjkwMCwic2hyaW5rX3R5cGUiOjN9LHsiaW1h\nZ2VfdHlwZSI6NCwiaW1hZ2Vfd2lkdGgiOjU0LCJzaHJpbmtfdHlwZSI6NH1d\n'
class Oracle:
    """Frida 签名预言机"""
    def __init__(self):
        pid = int(subprocess.run([ADB, '-s', DEV, 'shell', 'pidof', 'com.phoenix.read'], capture_output=True, text=True).stdout.split()[0])
        dev = frida.get_device_manager().add_remote_device(FRIDA_HOST)
        self.session = dev.attach(pid)
        self.script = self.session.create_script(open(os.path.join(HERE, 'frida', 'oracle.js'), encoding='utf-8').read())
        self.script.load()
    def sign(self, url, headers):
        return self.script.exports_sync.sign(url, headers)
_oracle = None
_oracle_lock = threading.RLock()
def oracle():
    global _oracle
    if _oracle is None:
        with _oracle_lock:
            if _oracle is None:
                _oracle = Oracle()
if not os.environ.get('SIGN_SERVER'):
    os.environ['SIGN_SERVER'] = 'http://127.0.0.1:9099'
SIGN_SERVERS = [s.strip() for s in (os.environ.get('SIGN_SERVER') or 'http://127.0.0.1:9099').split(',') if s.strip()]
SIGN_LIST = (os.environ.get('HG_SIGN_LIST') or '').strip().lower() in ['1', 'true', 'yes', 'on']
_sign_rr = [0]
_sign_rr_lock = threading.Lock()
def _next_sign_server():
    with _sign_rr_lock:
        i = _sign_rr[0] % len(SIGN_SERVERS)
        _sign_rr[0] = (_sign_rr[0] + 1) % max(1, len(SIGN_SERVERS))
        return SIGN_SERVERS[i]
def _sign_session():
    """对本机签名服务的线程本地 Session(keep-alive, 省每签名一次握手/TIME_WAIT)。"""
    s = getattr(_tls, 'sign', None)
    if s is None:
        s = requests.Session()
        s.mount('http://', requests.adapters.HTTPAdapter(pool_connections=8, pool_maxsize=16, max_retries=0))
        _tls.sign = s
    return s
def _ensure_signer(port=9099):
    try:
        import socket, shutil
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            if s.connect_ex(('127.0.0.1', port)) == 0:
                return True
    except Exception:
        pass
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jar = os.path.join(root, 'app', 'sign', 'unidbg-sign.jar')
    cands = [
        os.path.join(root, 'jre', 'bin', 'javaw.exe'),
        os.path.join(root, 'jre', 'bin', 'java.exe'),
        shutil.which('javaw'),
        shutil.which('java')
    ]
    java = next((c for c in cands if c and os.path.isfile(c)), None)
    if java and os.path.isfile(jar):
        subprocess.Popen([
            java,
            '-Xmx512m',
            '-XX:+ExitOnOutOfMemoryError',
            '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
            '-cp', 'unidbg-sign.jar',
            'com.hongguo.sign.FqTrace', 'serve', str(port)
        ], cwd=os.path.dirname(jar), creationflags=0x08000000)
        t0 = time.time()
        while time.time() - t0 < 15:
            time.sleep(0.5)
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.4)
                    if s.connect_ex(('127.0.0.1', port)) == 0:
                        return True
            except Exception:
                pass
    return False

def sign(url, headers, timeout=40):
    """签名。多签名服务轮询+故障转移; 自动检测并拉起本机 unidbg 签名服务。"""
    if SIGN_SERVERS:
        errs = []
        sess = _sign_session()
        for attempt_loop in range(2):
            for _ in range(len(SIGN_SERVERS)):
                base = _next_sign_server()
                try:
                    r = sess.post(base.rstrip('/') + '/sign', json={'url': url, 'headers': headers}, timeout=timeout)
                    r.raise_for_status()
                    j = r.json()
                    if 'error' in j:
                        raise RuntimeError(j['error'])
                    else:
                        return j
                except Exception as e:
                    errs.append(f'{base}: {e}')
            if attempt_loop == 0 and any(('127.0.0.1' in s or 'localhost' in s) for s in SIGN_SERVERS):
                # 尝试自动拉起签名服务
                if _ensure_signer(SIGN_PORT):
                    time.sleep(0.5)
                    continue
        raise RuntimeError('所有签名服务失败: ' + '; '.join(errs))
    else:
        with _oracle_lock:
            return oracle().sign(url, headers)
_refresh_lock = threading.Lock()
_last_refresh = 0
def refresh_session():
    """登录态过期时,从签名服务 /grab 抓取 app 当前的新鲜 token/设备参数,更新 CFG。"""
    global _last_refresh
    # ***<module>.refresh_session: Failure: Different control flow
    with _refresh_lock:
        if time.time() - _last_refresh < 20:
            return
        else:
            if not SIGN_SERVERS:
                return
            else:
                try:
                    r = requests.get(SIGN_SERVERS[0].rstrip('/') + '/grab', timeout=60)
                    data = r.json()
                    if 'error' in data:
                        print('[refresh] grab失败:', data['error'])
                    else:
                        from urllib.parse import urlparse, parse_qsl
                        q = dict(parse_qsl(urlparse(data['url']).query))
                        DEVICE_KEYS = set(CFG['base_query'].keys()) | {'klink_egdi', 'cdid', 'channel', 'update_version_code', 'iid', 'device_id'}
                        for k in DEVICE_KEYS:
                            if k in q and q[k]:
                                    CFG['base_query'][k] = q[k]
                        for k, v in (data.get('headers') or {}).items():
                            kl = k.lower()
                            if kl in ['cookie', 'x-tt-token', 'x-tt-store-region', 'x-tt-store-region-src'] and v:
                                    CFG['session_headers'][kl] = v.strip('[]')
                        _last_refresh = time.time()
                        try:
                            json.dump(CFG, open(os.path.join(HERE, 'config.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                        print('[refresh] 登录态已刷新, token长度=%d' % len(CFG['session_headers'].get('x-tt-token', '')))
                except Exception as e:
                    print('[refresh] 异常:', e)
def build_url(path, extra=None):
    q = dict(CFG['base_query'])
    if _pool:
        q.update(_pool.current()['query'])
    if extra:
        q.update(extra)
    q['_rticket'] = str(int(time.time() * 1000))
    qs = '&'.join((f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in q.items()))
    return f'https://{HOST}{path}?{qs}'
def _api_once(method, path, body, extra_query, signed=True, timeout=30, sign_timeout=40):
    url = build_url(path, extra_query)
    headers = dict(CFG['session_headers'])
    if _pool:
        _ua = _pool.current().get('user_agent')
        if _ua:
            headers['user-agent'] = _ua
        headers.pop('x-tt-token', None)
        headers.pop('cookie', None)
    headers['content-type'] = 'application/json; charset=utf-8'
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        headers['x-ss-stub'] = hashlib.md5(data).hexdigest().upper()
    if signed:
        headers.update(sign(url, headers, timeout=sign_timeout))
    headers.pop('accept-encoding', None)
    SG.throttle.wait()
    r = http_request(method, url, data=data, headers=headers, timeout=timeout)
    j = r.json()
    SG.check_response(j)
    return j
def api(method, path, body=None, extra_query=None, max_retries=3, signed=True, timeout=30, sign_timeout=40):
    """带签名的 API 调用,含重试退避 + 登录态自动刷新。\n    signed=False: 免签(列表/榜单/筛选类接口红果不校验签名, 不占用签名后端)。\n    sign_timeout: 签名后端单次超时(默认40; 下架探测传短超时)。"""
    last = None
    for attempt in range(max_retries):
        try:
            return _api_once(method, path, body, extra_query, signed=signed, timeout=timeout, sign_timeout=sign_timeout)
        except AuthExpiredError as e:
            last = e
            print(f'[api] 登录态失效,刷新后重试 ({path})')
            refresh_session()
            time.sleep(1)
        except RiskControlError as e:
            last = e
            rotate_device()
            wait = 2 ** attempt + 1
            print(f'[api] 风控/异常,换设备退避{wait}s重试 ({path}): {e}')
            time.sleep(wait)
        except (requests.RequestException, ValueError) as e:
            last = e
            rotate_device()
            time.sleep(1.5 * (attempt + 1))
    raise last if last else RuntimeError('api 失败')
def _cover_tags(d):
    """提取封面角标(爆剧/新剧/独播…)。cover_tag_info_list 结构不定, 容错取文本。"""
    out = []
    for t in d.get('cover_tag_info_list') or []:
        if isinstance(t, dict):
            v = t.get('text') or t.get('content') or t.get('name') or t.get('tag_text') or t.get('title')
            if v:
                out.append(re.sub('<[^>]+>', '', str(v)))
        else:
            if isinstance(t, str) and t:
                    out.append(t)
    return out
def _parse_search_cell(cell):
    """从综合tab的一个cell解析短剧条目; 非短剧(无集数)或无id返回 None。"""
    # ***<module>._parse_search_cell: Failure: Different control flow
    sid = cell.get('book_id') or cell.get('search_result_id')
    if not sid:
        return
    else:
        vd = cell.get('video_detail') or {}
        vdata = cell.get('video_data')
        if isinstance(vdata, list) and vdata:
            vdata = vdata[0]
        else:
            if not isinstance(vdata, dict):
                vdata = {}
        inner = vdata.get('video_detail') or {}
        ep = vd.get('episode_cnt') or vdata.get('episode_cnt') or inner.get('episode_cnt') or 0
        if not ep:
            return
        else:
            title = cell.get('title') or cell.get('book_name') or vd.get('series_title') or (vdata.get('title') if isinstance(vdata, dict) else '') or inner.get('series_title') or sid
            title = re.sub('<[^>]+>', '', str(title)).strip()
            created_at = ''
            ts = 0
            try:
                sid_int = int(sid)
                ts = sid_int >> 32
                if 1577836800 <= ts <= 1900000000:
                    created_at = time.strftime('%Y-%m-%d', time.localtime(ts))
            except Exception:
                pass
            cover_url = vdata.get('cover') or vd.get('series_cover') or vd.get('cover') or ''
            return {'series_id': str(sid), 'title': title, 'episode_cnt': ep, 'score': vdata.get('score') or inner.get('score') or '', 'play_cnt': vdata.get('play_cnt') or inner.get('series_play_cnt') or 0, 'hot': vdata.get('rec_text') or '', 'copyright': inner.get('copyright') or 0, 'cover': cover_url, 'horiz_cover': vdata.get('horiz_cover') or '', 'cover_tags': _cover_tags(vdata), 'created_at': created_at, 'create_time': ts if created_at else 0}
def search(query, max_items=None):
    """搜索短剧。原生接口按综合tab分页(next_offset+passback+search_id),\n    这里循环翻页累计短剧结果, 直到 has_more=False 或达 max_items / 翻页上限。\n    max_items 越小翻页越少越快(单 IP 顺序翻页是单次延迟主因); 默认走 HG_SEARCH_MAX_ITEMS(20)。\n    """
    if max_items is None:
        max_items = int(os.environ.get('HG_SEARCH_MAX_ITEMS', '20'))
    max_items = max(1, min(max_items, 40))
    ck = SG.cache_key('search', query, max_items)
    cached = SG.cache_get(ck)
    if cached is not None:
        return cached
    else:
        results, seen = ([], set())
        offset, passback, search_id = (0, '', '')
        for _ in range(12):
            q = {'query': query, 'tab_name': 'feed', 'search_source': '1', 'offset': str(offset), 'count': '0', 'use_correct': 'true'}
            if passback:
                q['passback'] = passback
            if search_id:
                q['search_id'] = search_id
            j = api('GET', '/reading/bookapi/search/tab/v', extra_query=q)
            tabs = j.get('search_tabs') or []
            if not tabs:
                break
            else:
                tab = tabs[0]
                data = tab.get('data') or []
                for cell in data:
                    item = _parse_search_cell(cell)
                    if not item or item['series_id'] in seen:
                        continue
                    else:
                        seen.add(item['series_id'])
                        results.append(item)
                nxt = tab.get('next_offset')
                offset = nxt if nxt is not None else offset
                passback = tab.get('passback') or passback
                search_id = tab.get('search_id') or search_id
                if not tab.get('has_more') or not data or len(results) >= max_items:
                    break
        results = results[:max_items]
        SG.cache_set(ck, results, ttl=600)
        return results
def _episodes_body(series_id):
    return {'biz_param': {'detail_page_version': 0, 'disable_digg_stat': False, 'disable_video_relate_book': False, 'image_shrink_datas_str': IMAGE_SHRINK, 'need_all_video_definition': False, 'need_mp4_align': False, 'screen_width_px': '900', 'source': 7, 'use_os_player': False, 'use_server_dns': False}, 'series_id': series_id}
def _parse_episode_detail(sid, vd):
    eps = []
    for e in (vd or {}).get('video_list', []):
        eps.append({'index': e.get('vid_index'), 'vid': e.get('vid'), 'title': e.get('title', '')[:30], 'duration': e.get('duration'), 'cover': e.get('episode_cover') or e.get('cover') or '', 'comment_count': e.get('comment_count', 0), 'digged_count': e.get('digged_count', 0)})
    eps.sort(key=lambda x: x.get('index') or 0)
    first_ep_cover = next((e.get('cover') for e in eps if e.get('cover')), '')
    celebs = []
    for c in (vd or {}).get('celebrities', []):
        av = c.get('avatar') or c.get('avatar_url') or c.get('thumb_url') or c.get('image') or c.get('head_image') or ''
        if isinstance(av, dict):
            av = av.get('url') or av.get('uri') or ''
        name = c.get('nickname') or c.get('name') or c.get('actor_name') or ''
        role = c.get('role_name') or c.get('role') or ''
        celebs.append({'演员': name, '角色': role, '头像': av, '简介': (c.get('intro') or '')[:80]})
    meta = {
        'series_id': sid,
        'title': (vd or {}).get('series_title', sid),
        'intro': (vd or {}).get('series_intro', ''),
        'episode_cnt': (vd or {}).get('episode_cnt', len(eps)),
        'status': '完结' if (vd or {}).get('series_status') == 1 else '连载中',
        'play_cnt': (vd or {}).get('series_play_cnt', 0),
        'followed_cnt': (vd or {}).get('followed_cnt', 0),
        'create_time': (vd or {}).get('create_time', 0),
        'cover': (vd or {}).get('series_cover') or first_ep_cover,
        'score': (vd or {}).get('score') or (vd or {}).get('douban_score') or (vd or {}).get('rating') or '',
        'category': re.findall('"name":"([^"]+)"', (vd or {}).get('category_schema', '')),
        'celebrities': celebs
    }
    return (meta, eps)
def get_episodes(series_id, max_retries=3, timeout=30, sign_timeout=40):
    sid = str(series_id)
    ck = SG.cache_key('episodes', sid)
    cached = SG.cache_get(ck)
    if cached is not None:
        return cached
    else:
        j = api('POST', '/novel/player/multi_video_detail/v1/', body=_episodes_body(sid), max_retries=max_retries, timeout=timeout, sign_timeout=sign_timeout)
        data = j.get('data', {})
        meta, eps = _parse_episode_detail(sid, data.get(sid, {}).get('video_data', {}))
        SG.cache_set(ck, (meta, eps), ttl=21600)
        return (meta, eps)
def get_collection(tab_types=(2, 5, 8), page_limit=50, max_pages=40):
    # irreducible cflow, using cdg fallback
    """抓取账号「我的」里已追剧/订阅的短剧系列。\n    接口: GET /reading/user/subscribe/list/v0 (需签名), 按 tab_type 分组 + offset 分页。\n    返回去重后的 [{\'series_id\',\'name\',\'item_type\'}] (仅视频短剧, 用 detail_schema 里的 series_id 判定, 过滤小说)。\n    tab_type: 2/8=追剧列表, 5=另一组; 跨 tab 去重。已下架的剧仍会返回, 下载阶段自动跳过。"""
    # ***<module>.get_collection: Failure: Compilation Error
    seen = {}
    for tt in tab_types:
        offset = 0
        for _ in range(max_pages):
            try:
                extra = {'subscribe_order_type': '0', 'swipe_type': '0', 'subscribe_offset': str(offset), 'offset': str(offset), 'tab_type': str(tt), 'limit': str(page_limit), 'is_online': 'false', 'need_calendar_schema': 'false'}
                j = api('GET', '/reading/user/subscribe/list/v0', extra_query=extra, signed=True)
                d = j.get('data') or {}
                items = d.get('subscribe_items') or []
                for it in items:
                    schema = it.get('detail_schema') or ''
                    m = re.search('series_id=(\\d+)', schema)
                    sid = m.group(1) if m else str(it.get('item_id') or '')
                    is_video = 'series_id=' in schema or 'Series' in schema
                    if sid and is_video and (sid not in seen):
                        seen[sid] = {'series_id': sid, 'name': it.get('name') or sid, 'item_type': it.get('item_type')}
                if not d.get('has_more') or not items:
                    break
                offset = d.get('next_offset') or (offset + len(items))
            except Exception as ex:
                print(f'[collection] tab_type={tt} offset={offset} 取用失败: {ex}')
                break
    return list(seen.values())
def get_episodes_batch(series_ids, batch_size=20):
    # irreducible cflow, using cdg fallback
    """批量取剧集元数据。multi_video_detail 支持 series_id 用逗号拼接；实测 20 个/批稳定，30 个会参数错误。"""
    # ***<module>.get_episodes_batch: Failure: Compilation Error
    ids, seen = ([], set())
    for sid in series_ids or []:
        sid = str(sid).strip()
        if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
    batch_size = max(1, min(int(batch_size or 20), 20))
    out, failed = ({}, [])
    todo = []
    for sid in ids:
        cached = SG.cache_get(SG.cache_key('episodes', sid))
        if cached is not None:
            out[sid] = cached[0]
        else:
            todo.append(sid)
    for i in range(0, len(todo), batch_size):
        batch = todo[i:i + batch_size]
        try:
            j = api('POST', '/novel/player/multi_video_detail/v1/', body=_episodes_body(','.join(batch)))
            data = j.get('data', {}) or {}
            for sid in batch:
                vd = (data.get(sid) or {}).get('video_data') or {}
                if not vd:
                    failed.append({'series_id': sid, 'error': 'empty detail'})
                    continue
                meta, eps = _parse_episode_detail(sid, vd)
                SG.cache_set(SG.cache_key('episodes', sid), (meta, eps), ttl=21600)
                out[sid] = meta
        except Exception as e:
            failed.extend(({'series_id': sid, 'error': str(e)} for sid in batch))
    return (out, failed)
def get_episodes_multi(series_ids, batch_size=20, force=False):
    # irreducible cflow, using cdg fallback
    """批量取多部剧的完整 (meta, eps)。multi_video_detail 支持 series_id 逗号拼接(每批≤20)。\n    返回 {sid: (meta, eps)}; 未返回的剧不在结果里(调用方自行跳过)。\n    force=True: 跳过 6 小时剧集缓存, 强制取最新 —— Library 查新必须用它才能看到刚上线的新集。"""
    # ***<module>.get_episodes_multi: Failure: Different control flow
    ids, seen = ([], set())
    for sid in series_ids or []:
        sid = str(sid).strip()
        if sid and sid not in seen:
                seen.add(sid)
                ids.append(sid)
    batch_size = max(1, min(int(batch_size or 20), 20))
    out, todo = ({}, [])
    for sid in ids:
        if not force:
            cached = SG.cache_get(SG.cache_key('episodes', sid))
            if cached is not None:
                out[sid] = cached
                todo.append(sid)
    for i in range(0, len(todo), batch_size):
        batch = todo[i:i + batch_size]
        try:
            j = api('POST', '/novel/player/multi_video_detail/v1/', body=_episodes_body(','.join(batch)))
            data = j.get('data', {}) or {}
            for sid in batch:
                vd = (data.get(sid) or {}).get('video_data') or {}
                if not vd:
                    continue
                else:
                    meta, eps = _parse_episode_detail(sid, vd)
                    SG.cache_set(SG.cache_key('episodes', sid), (meta, eps), ttl=21600)
                    out[sid] = (meta, eps)
        except Exception as e:
            print(f'[get_episodes_multi] batch failed: {e}')
    return out
def get_video_urls(vids, force=False):
    """批量取视频直链。返回 {vid: {\"url\":, \"size\":, \"definition\":}}\n    每个vid的直链缓存5小时(url_expire约6h),命中则不重复调video_model,大幅降低风控。\n    force=True 跳过缓存强制重取(续传时直链过期用)。"""
    out = {}
    todo = []
    for v in vids:
        c = None if force else SG.cache_get(SG.cache_key('vmodel', str(v)))
        if c is not None:
            out[str(v)] = c
        else:
            todo.append(v)
    for i in range(0, len(todo), 5):
        batch = [str(v) for v in todo[i:i + 5]]
        body = {'biz_param': {'detail_page_version': 0, 'device_level': 3, 'disable_digg_stat': False, 'disable_video_relate_book': False, 'need_all_video_definition': True, 'need_mp4_align': False, 'use_os_player': False, 'use_server_dns': False, 'video_platform': 1024}, 'mixed_video_id_map': {'1': batch}}
        j = api('POST', '/novel/player/multi_video_model/v1/', body=body)
        for vid, v in (j.get('data') or {}).items():
            vm = v.get('video_model')
            if not vm:
                continue
            else:
                vmj = json.loads(vm)
                best = None
                for item in vmj.get('video_list', []):
                    meta = item.get('video_meta', {})
                    size = meta.get('size', 0)
                    if best is None or size > best['size']:
                        best = {'url': item.get('main_url'), 'backup': item.get('backup_url'), 'size': size, 'definition': meta.get('definition', '?')}
                if best:
                    out[vid] = best
                    SG.cache_set(SG.cache_key('vmodel', vid), best, ttl=18000)
    return out
def get_video_tracks(vids, force=False, batch_size=5):
    """批量取每个vid的完整 video_list 轨道(含 main_url/backup_url/video_meta/encrypt_info.spade_a)。\n    与 get_video_urls 不同: 保留 spade_a(离线解密必需) 和全部清晰度轨道(供选清晰度)。\n    一次 5 个 vid(app 真实批量大小)→ 5 集只签 1 次, 大幅降签名/节流/风控压力。\n    按 vid 缓存 5h(main_url url_expire 约6h); force=True 跳过缓存(URL过期续传用)。\n    返回 {vid(str): [track,...]}; 未返回的 vid 不在结果里(调用方自行回退)。"""
    out, todo, seen = ({}, [], set())
    for v in vids:
        v = str(v)
        if v in seen:
            continue
        else:
            seen.add(v)
            c = None if force else SG.cache_get(SG.cache_key('vmtracks', v))
            if c is not None:
                out[v] = c
            else:
                todo.append(v)
    bs = max(1, min(int(batch_size or 5), 5))
    for i in range(0, len(todo), bs):
        batch = todo[i:i + bs]
        body = {'biz_param': {'detail_page_version': 0, 'device_level': 3, 'disable_digg_stat': False, 'disable_video_relate_book': False, 'need_all_video_definition': True, 'need_mp4_align': False, 'use_os_player': False, 'use_server_dns': False, 'video_platform': 1024}, 'mixed_video_id_map': {'1': batch}}
        j = api('POST', '/novel/player/multi_video_model/v1/', body=body)
        for vid, v in (j.get('data') or {}).items():
            vm = v.get('video_model')
            if not vm:
                continue
            else:
                tracks = json.loads(vm).get('video_list') or []
                if tracks:
                    out[str(vid)] = tracks
                    SG.cache_set(SG.cache_key('vmtracks', str(vid)), tracks, ttl=18000)
    return out
import uuid
import datetime
def _is_today_ts(ts):
    """unix秒是否为今天(中国时区UTC+8)"""
    if not ts:
        return False
    else:
        d = (datetime.datetime.utcfromtimestamp(ts) + datetime.timedelta(hours=8)).date()
        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).date()
        return d == now
COMIC_RANK_CELL = '7470092475068071998'
RANK_BOARDS = {'recommend': 'comic_series_hot_rank', 'hot': 'comic_series_hot_play', 'new': 'comic_series_new_rank'}
RANK_NAMES = {'recommend': '漫剧推荐榜', 'hot': '漫剧热播榜', 'new': '漫剧新剧榜'}
def rank(board='recommend', limit=30):
    """获取漫剧榜单。board: recommend/hot/new。返回排名列表。"""
    ck = SG.cache_key('rank', board, limit)
    cached = SG.cache_get(ck)
    if cached is not None:
        return cached
    else:
        sub = RANK_BOARDS.get(board, board)
        results, offset, sess = ([], 0, str(uuid.uuid4()))
        while len(results) < limit:
            q = {'cell_id': COMIC_RANK_CELL, 'tab_type': '26', 'client_req_type': '2', 'client_template': '2', 'screen_width_px': '1350', 'selected_items': 'comic_series_rank', 'sub_selected_items': sub, 'session_uuid': sess}
            if offset:
                q['offset'] = str(offset)
            j = api('GET', '/reading/bookapi/bookmall/cell/change/v', extra_query=q, signed=SIGN_LIST)
            cv = j.get('data', {}).get('cell_view', {})
            cells = cv.get('cell_data', [])
            if not cells:
                break
            for item in cells:
                v = item.get('video_data')
                if isinstance(v, list):
                    v = v[0] if v else {}
                sid = v.get('series_id') or v.get('book_id')
                if not sid:
                    continue
                else:
                    results.append({'rank': len(results) + 1, 'series_id': str(sid), 'title': v.get('title', ''), 'episode_cnt': v.get('episode_cnt', 0), 'score': v.get('score', ''), 'play_cnt': v.get('play_cnt', 0), 'hot': v.get('rec_text') or '', 'copyright': v.get('copyright', ''), 'cover': v.get('cover', ''), 'intro': (v.get('video_desc') or '')[:50]})
            if not cv.get('has_more'):
                break
            offset = cv.get('next_offset', offset + len(cells))
        results = results[:limit]
        SG.cache_set(ck, results, ttl=1800)
        return results
GENRES = {'short_play': ('default', 'short_play'), 'comic_series': ('comic_series', 'comic_series'), 'ai_series': ('ai_series', 'ai_series')}
GENRE_NAMES = {'short_play': '短剧', 'comic_series': '漫剧', 'ai_series': 'AI短剧'}
def latest(genre='short_play', only_today=True, max_items=120, stop_ids=None, refresh=False):
    """最新上架。\n    - 短剧(short_play): 官方有\'今日上新\'标签。only_today=True 精确返回今日上新(扫描多页,\n      整页无今日才停,处理交错); False 返回最新上架全部。\n    - 漫剧/AI(comic_series/ai_series): 官方无\'今日\'粒度(最细7天)且不暴露上线时间,\n      统一返回\'7天内上新·最新上架\'(days_7筛选+上线时间降序,顶部最新)。only_today 不影响结果,\n      item.today 字段对这两类恒为 False(无法判定)。\n    """
    if genre not in GENRES:
        raise ValueError(f'genre必须是 {list(GENRES)}')
    else:
        scene, g = GENRES[genre]
        tag_today = genre == 'short_play'
        online_time = [] if tag_today else ['days_7']
        want_today = tag_today and only_today
        out, shown, offset, pages, done = ([], [], 0, 0, False)
        while len(out) < max_items and pages < 20:
                body = {'filter_ids': ','.join(shown), 'req_scene': scene, 'offset': offset, 'need_selector_panel': False, 'limit': 18, 'select_items': {'category_dim_epoch': [], 'online_time': online_time, 'gender': [], 'category_dim_role': [], 'genre': [g], 'sort': ['online_time'], 'category_dim_theme': []}, 'session_id': '', 'req_type': 'only_content', 'client_req_type': 3}
                j = api('POST', '/reading/distribution/category/landpage/v', body=body, signed=SIGN_LIST)
                items = j.get('data', {}).get('video_data', [])
                if not items:
                    break
                page_today = 0
                for it in items:
                    sid = str(it.get('series_id'))
                    if stop_ids and sid in stop_ids:
                            done = True
                            break
                    shown.append(sid)
                    subs = [s.get('content') for s in it.get('sub_title_list') or []]
                    is_today = '今日上新' in subs
                    if is_today:
                        page_today += 1
                    cats = []
                    for nm in re.findall('\"name\":\"([^\"]+)\"', it.get('category_schema', '')):
                        if nm and nm not in cats:
                                cats.append(nm)
                    if not cats:
                        for s in subs:
                            if not s or s == '今日上新' or re.match('^[\\d.]+万', s) or ('播放' in s) or re.match('^\\d+集$', s):
                                continue
                            else:
                                if s not in cats:
                                    cats.append(s)
                    if want_today and (not is_today):
                            continue
                    out.append({'series_id': sid, 'title': it.get('title', ''), 'episode_cnt': it.get('episode_cnt', 0), 'score': it.get('score', ''), 'play_cnt': it.get('play_cnt', 0), 'cover': it.get('cover', ''), 'category': ' / '.join(cats), 'today': is_today, 'copyright': it.get('copyright', ''), 'premiere': (it.get('tag_info') or {}).get('text', ''), 'intro': (it.get('video_desc') or '')[:50]})
                    if len(out) >= max_items:
                        break
                pages += 1
                if done:
                    break
                if want_today and page_today == 0:
                    break
                if not j.get('data', {}).get('has_more', True):
                    break
                offset += len(items)
        return out
FILTER_CATE = {'脑洞': 'cate_755', '奇幻': 'cate_6', '剧情': 'cate_316', '玄幻': 'cate_7', '末世': 'cate_68', '豪门': 'cate_936', '科幻': 'cate_1092', '冒险': 'cate_1182', '重生': 'cate_36', '穿越': 'cate_37', '逆袭': 'cate_739', '异能': 'cate_598', '系统': 'cate_19', '反转': 'cate_756', '娱乐圈': 'cate_43', '总裁': 'cate_29', '架空': 'cate_452', 'cate_1': {'都市': 'cate_758', '古代': 'cate_599', '异界': 'cate_4', '校园': 'cate_127', '职场': 'cate_79', '年代': 'cate_11', '乡村': 'cate_390'}}
FILTER_SORT = {'最新上架': 'online_time', '最新': 'online_time', '最高热度': 'hot_score', '热度': 'hot_score', 'hot': 'hot_score', '最高收藏': 'hot_collect', '收藏': 'hot_collect'}
FILTER_GENDER = {'男频': '1', '男': '1', '女频': '0', '女': '0'}
FILTER_DAYS = {'7': 'days_7', '14': 'days_14', '30': 'days_30', '90': 'days_90', '7天内上新': 'days_7', '14天内上新': 'days_14', '30天内上新': 'days_30', '90天内上新': 'days_90'}
FILTER_STATUS = {'已完结': 'creation_status_0', '完结': 'creation_status_0', '连载中': 'creation_status_1', '连载': 'creation_status_1'}
def _ids(val, mapping):
    """单值或列表 -> id 列表; 名称按 mapping 映射, 已是 id/未知则原样透传。"""
    if val is None or val == '':
        return []
    else:
        vals = val if isinstance(val, (list, tuple)) else [val]
        out = []
        for v in vals:
            v = str(v).strip()
            if v:
                out.append(mapping.get(v, v))
        return out
def filters(genre='short_play'):
    """取某体裁的实时筛选面板。返回 [{type,row_name,selection_type,items:[{id,name}]}]。\n    type 即 select_items 的键(genre/category_dim_theme/category_dim_role/category_dim_epoch/sort/gender/online_time)。"""
    # ***<module>.filters: Failure: Different bytecode
    scene, g = GENRES.get(genre, ('default', 'short_play'))
    body = {'filter_ids': '', 'req_scene': scene, 'offset': 0, 'limit': 1, 'need_selector_panel': True, 'req_type': 'default', 'client_req_type': 3, 'select_items': {'category_dim_epoch': [], 'online_time': [], 'gender': [], 'category_dim_role': [], 'genre': [g], 'sort': [], 'category_dim_theme': []}, 'session_id': ''}
    rows = api('POST', '/reading/distribution/category/landpage/v', body=body, signed=SIGN_LIST).get('data', {}).get('selector_rows', [])
    return [{'type': r.get('type'), 'row_name': r.get('row_name'), 'selection_type': r.get('selection_type'), 'items': [{'id': it.get('selector_item_id'), 'name': it.get('show_name')} for it in rows]} for r in ADB]
def browse(genre='short_play', theme=None, setting=None, background=None, sort='online_time', gender=None, days=None, status=None, max_items=120):
    """按筛选条件浏览短剧/漫剧/AI短剧。各维度可传中文名或 id(cate_xxx)，单值或列表(多选)。\n    - genre   体裁: short_play/comic_series/ai_series\n    - theme   主题: 脑洞/奇幻/剧情/玄幻/末世/豪门/科幻/冒险 ...\n    - setting 设定: 重生/穿越/逆袭/异能/系统/反转/娱乐圈/总裁 ...\n    - background 背景: 架空/都市/古代/异界/校园/职场/年代/乡村/民国 ...\n    - sort    排序: 最新上架(online_time)/最高热度(hot_score)/最高收藏(hot_collect)\n    - gender  受众: 男频(1)/女频(0)\n    - days    时间: 7/14/30/90 (天内上新)\n    - status  状态(仅漫剧): 已完结/连载中\n    全部可选项见 filters(genre)。返回 [{series_id,title,episode_cnt,score,play_cnt,cover,category,intro}]。"""
    # ***<module>.browse: Failure: Different control flow
    if genre not in GENRES:
        raise ValueError(f'genre 必须是 {list(GENRES)}')
    else:
        scene, g = GENRES[genre]
        sel = {'genre': [g], 'category_dim_theme': _ids(theme, FILTER_CATE), 'category_dim_role': _ids(setting, FILTER_CATE), 'category_dim_epoch': _ids(background, FILTER_CATE), 'sort': _ids(sort, FILTER_SORT) or ['online_time'], 'gender': _ids(gender, FILTER_GENDER), 'creation_status': _ids(status, FILTER_STATUS), 'online_time': _ids(days, FILTER_DAYS)}
        out, shown, offset, pages = ([], [], 0, 0)
        while len(out) < max_items and pages < 20:
                body = {'filter_ids': ','.join(shown), 'req_scene': scene, 'offset': offset, 'need_selector_panel': False, 'limit': 18, 'select_items': sel, 'session_id': '', 'req_type': 'only_content', 'client_req_type': 3}
                j = api('POST', '/reading/distribution/category/landpage/v', body=body, signed=SIGN_LIST)
                items = j.get('data', {}).get('video_data', [])
                if not items:
                    break
                for it in items:
                    sid = str(it.get('series_id'))
                    shown.append(sid)
                    cats = []
                    for nm in re.findall('\"name\":\"([^\"]+)\"', it.get('category_schema', '')):
                        if nm and nm not in cats:
                                cats.append(nm)
                    out.append({'series_id': sid, 'title': it.get('title', ''), 'episode_cnt': it.get('episode_cnt', 0), 'score': it.get('score', ''), 'play_cnt': it.get('play_cnt', 0), 'cover': it.get('cover', ''), 'copyright': it.get('copyright', ''), 'category': ' / '.join(cats), 'duration': it.get('comment_count', 0), 'horiz_cover': it.get('horiz_cover') or '', 'cover_tags': _cover_tags(it)})
                    if len(out) >= max_items:
                        break
                pages += 1
                if not j.get('data', {}).get('has_more', True):
                    break
                offset += len(items)
        return out
FEED_SORT = {'recommend': 'hot_score', 'hot': 'hot_collect', 'new': 'online_time'}
def feed_page(board='recommend', offset=0, size=100):
    """Mainstream 短剧 (live-action) feed for the Trending tabs, offset-paginated so the UI can page through\n    the thousands available. board -> sort (recommend=热度 / hot=收藏 / new=最新上架). De-dupes within the\n    window. Returns (items, has_more, next_offset). Cached per (board, offset, size)."""
    sort = FEED_SORT.get(board, 'hot_score')
    ck = SG.cache_key('feed', board, int(offset or 0), int(size))
    cached = SG.cache_get(ck)
    if cached is not None:
        return cached
    else:
        scene, g = GENRES['short_play']
        sel = {'genre': [g], 'category_dim_theme': [], 'category_dim_role': [], 'category_dim_epoch': [], 'sort': [sort], 'gender': [], 'creation_status': [], 'online_time': []}
        out, seen, cur, pages, has_more = ([], set(), int(offset or 0), 0, False)
        while len(out) < size and pages < 12:
                body = {'filter_ids': '', 'req_scene': scene, 'offset': cur, 'need_selector_panel': False, 'limit': 30, 'select_items': sel, 'session_id': '', 'req_type': 'only_content', 'client_req_type': 3}
                j = api('POST', '/reading/distribution/category/landpage/v', body=body, signed=SIGN_LIST)
                data = j.get('data', {}) or {}
                items = data.get('video_data', []) or []
                cur += len(items)
                for it in items:
                    sid = str(it.get('series_id') or '')
                    if not sid or sid in seen:
                        continue
                    else:
                        seen.add(sid)
                        cats = []
                        for nm in re.findall('\"name\":\"([^\"]+)\"', it.get('category_schema', '')):
                            if nm and nm not in cats:
                                    cats.append(nm)
                        out.append({'series_id': sid, 'title': it.get('title', ''), 'episode_cnt': it.get('episode_cnt', 0), 'score': it.get('score', ''), 'play_cnt': it.get('play_cnt', 0), 'cover': it.get('cover', ''), 'category': ' / '.join(cats), 'intro': (it.get('video_desc') or '')[:50]})
                        if len(out) >= size:
                            break
                pages += 1
                has_more = bool(data.get('has_more', False))
                if not items or not has_more:
                    break
        if len(out) >= size:
            has_more = True
        res = (out[:size], has_more, cur)
        SG.cache_set(ck, res, ttl=1800)
        return res
RANK_CELL = '7470092475068071998'
LB_SEL = {'all': 'all', 'human': 'human', 'comic': 'comic_series_rank', 'ai': 'ai_playlet'}
LB_KEYS = {('all', 'recommend'): 'ranklist_hot_sc', ('all', 'hot'): 'ranklist_hot_play_sc', ('all', 'new'): 'ranklist_new_rank_sc', ('human', 'recommend'): 'human_hot_sc', ('human', 'hot'): 'human_hot_play', ('human', 'new'): 'human_new_rank', ('comic', 'recommend'): 'comic_series_hot_rank', ('comic', 'hot'): 'comic_series_hot_play', ('comic', 'new'): 'comic_series_new_rank', ('ai', 'recommend'): 'ai_playlet_hot_sc', ('ai', 'hot'): 'ai_playlet_hot_play', ('ai', 'new'): 'ai_playlet_new_rank'}
def leaderboard_page(category='all', board='recommend', offset=0, size=100, force=False):
    """A page of the 红果推荐榜 leaderboard (curated top chart, sorted by watch/interaction/interest).
    category: all/human/comic/ai; board: recommend/hot/new. Offset-paginated. Returns (items, has_more,
    next_offset). Login-free (bookmall list endpoint). Cached per (category, board, offset, size)."""
    sub = LB_KEYS.get((category, board)) or LB_KEYS['all', 'recommend']
    ck = SG.cache_key('lb', category, board, int(offset or 0), int(size))
    if not force:
        cached = SG.cache_get(ck)
        if cached is not None:
            return cached
    sess = str(uuid.uuid4())
    out, seen, cur, pages, has_more = ([], set(), int(offset or 0), 0, False)
    while len(out) < size and pages < 25:
            q = {'cell_id': RANK_CELL, 'tab_type': '26', 'client_req_type': '2', 'client_template': '2', 'screen_width_px': '1350', 'session_uuid': sess, 'selected_items': LB_SEL.get(category, 'all'), 'sub_selected_items': sub}
            if cur:
                q['offset'] = str(cur)
            j = api('GET', '/reading/bookapi/bookmall/cell/change/v', extra_query=q, signed=SIGN_LIST)
            cv = (j.get('data') or {}).get('cell_view') or {}
            cells = cv.get('cell_data') or []
            if not cells:
                break
            for it in cells:
                v = it.get('video_data')
                if isinstance(v, list):
                    v = v[0] if v else {}
                v = v or {}
                sid = v.get('series_id') or v.get('book_id')
                if not sid or str(sid) in seen:
                    continue
                else:
                    seen.add(str(sid))
                    # Extract creation date from ByteDance 64-bit snowflake ID
                    created_at = ''
                    ts = 0
                    try:
                        sid_int = int(sid)
                        ts = sid_int >> 32
                        if 1577836800 <= ts <= 1900000000:
                            created_at = time.strftime('%Y-%m-%d', time.localtime(ts))
                    except Exception:
                        pass
                    out.append({
                        'series_id': str(sid),
                        'title': v.get('title', ''),
                        'episode_cnt': v.get('episode_cnt', 0),
                        'score': v.get('score', ''),
                        'play_cnt': v.get('play_cnt', 0),
                        'cover': v.get('cover', ''),
                        'created_at': created_at,
                        'create_time': ts if created_at else 0
                    })
                    if len(out) >= size:
                        break
            pages += 1
            has_more = bool(cv.get('has_more', False))
            nxt = cv.get('next_offset')
            cur = int(nxt) if nxt is not None else cur + len(cells)
            if not has_more:
                break
    if len(out) >= size:
        has_more = True
    res = (out[:size], has_more, cur)
    SG.cache_set(ck, res, ttl=1800)
    return res
def sanitize(name):
    return re.sub('[\\\\/:*?\"<>|]', '_', name).strip()[:60]
def img_ext(url):
    """从图片URL推断扩展名"""
    path = url.split('?')[0].lower()
    for e in ['.heic', '.jpeg', '.jpg', '.webp', '.png']:
        if path.endswith(e):
            return e
    return '.jpg'
def download_image(url, path):
    try:
        r = http_request('GET', url, timeout=30)
        r.raise_for_status()
        with open(path, 'wb') as f:
            f.write(r.content)
    except Exception as ex:
        print(f'    封面下载失败: {ex}')
        return False
    else:
        return True
_shared_dl_session = None
_shared_dl_lock = threading.Lock()

def _get_shared_dl_session(pool_size=128):
    global _shared_dl_session
    if _shared_dl_session is None:
        with _shared_dl_lock:
            if _shared_dl_session is None:
                s = requests.Session()
                ad = requests.adapters.HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size * 2, max_retries=1)
                s.mount('https://', ad)
                s.mount('http://', ad)
                _shared_dl_session = s
    return _shared_dl_session

def _probe_range_support(url):
    """Probe if URL supports HTTP Range (206) and obtain total length."""
    try:
        s = _get_shared_dl_session()
        # Fast HEAD request first (takes ~40ms)
        h = s.head(url, verify=False, timeout=6)
        if h.status_code in (200, 206):
            cr = h.headers.get('content-range', '')
            total = int(cr.split('/')[-1]) if '/' in cr else int(h.headers.get('content-length', 0))
            if total > 0:
                accept_ranges = h.headers.get('accept-ranges', '').lower()
                return total, ('bytes' in accept_ranges or h.status_code == 206 or bool(cr))
        # Fallback to GET bytes=0-0 probe
        r = s.get(url, headers={'Range': 'bytes=0-0'}, stream=True, verify=False, timeout=8)
        if r.status_code == 206:
            cr = r.headers.get('content-range', '')
            total = int(cr.split('/')[-1]) if '/' in cr else 0
            r.close()
            return total, total > 0
        if r.status_code == 200:
            total = int(r.headers.get('content-length', 0))
            r.close()
            return total, False
    except Exception:
        pass
    return 0, False

def download_file(url, path, on_bytes=None):
    """下载到 path。支持 Multi-segment 并发分段下载 (6-8 streams) 以突破 CDN 单连接限速，
    并在不支持 Range 时无缝回退到单流下载。on_bytes(done_bytes, total_bytes): 进度回调。"""
    tmp = path + '.part'
    max_segments = max(1, int(os.environ.get('HG_DL_SEGMENTS', '8')))

    # 1. 尝试多连接并发分段下载 (Multi-Segment Download)
    if max_segments > 1:
        try:
            total, range_ok = _probe_range_support(url)
            if range_ok and total >= 1048576:
                nseg = min(max_segments, max(2, total // 524288))
                seg_len = total // nseg
                ranges = [(i * seg_len, total - 1 if i == nseg - 1 else (i + 1) * seg_len - 1) for i in range(nseg)]

                with open(tmp, 'wb') as f:
                    f.truncate(total)

                prog = [0] * nseg
                lock = threading.Lock()
                last_cb = [0.0]
                errs = []
                sess = _get_shared_dl_session(nseg * 2)

                def _dl_worker(idx, lo, hi):
                    try:
                        r = sess.get(url, headers={'Range': f'bytes={lo}-{hi}'}, stream=True, verify=False, timeout=40)
                        if r.status_code not in (200, 206):
                            raise IOError(f"HTTP {r.status_code}")
                        with open(tmp, 'r+b') as f:
                            f.seek(lo)
                            for chunk in r.iter_content(262144):
                                if chunk:
                                    f.write(chunk)
                                    with lock:
                                        prog[idx] += len(chunk)
                                        if on_bytes:
                                            now = time.time()
                                            if now - last_cb[0] >= 0.2 or sum(prog) >= total:
                                                last_cb[0] = now
                                                try:
                                                    on_bytes(sum(prog), total)
                                                except Exception:
                                                    pass
                        r.close()
                    except Exception as e:
                        errs.append(e)

                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=nseg) as ex:
                    list(ex.map(lambda r: _dl_worker(*r), [(i, lo, hi) for i, (lo, hi) in enumerate(ranges)]))

                if not errs and os.path.exists(tmp) and os.path.getsize(tmp) == total:
                    if on_bytes:
                        try:
                            on_bytes(total, total)
                        except Exception:
                            pass
                    os.replace(tmp, path)
                    return True
        except Exception:
            pass  # Fall back to single-stream download below

    # 2. 单流下载 (Single-Stream Fallback)
    r = http_request('GET', url, stream=True, timeout=60)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    done = 0
    last_pct = -1
    last_cb = 0.0
    if on_bytes:
        try:
            on_bytes(0, total)
        except Exception:
            pass
    with open(tmp, 'wb') as f:
        for chunk in r.iter_content(262144):
            f.write(chunk)
            done += len(chunk)
            if on_bytes:
                now = time.time()
                if now - last_cb >= 0.2 or (total and done >= total):
                    last_cb = now
                    try:
                        on_bytes(done, total)
                    except Exception:
                        pass
            if total:
                pct = done * 100 // total
                if pct != last_pct and pct % 10 == 0:
                    print(f'    {pct}% ({done // 1024}/{total // 1024} KB)')
                    last_pct = pct
    try:
        r.close()
    except Exception:
        pass
    os.replace(tmp, path)
    return True
_dm = None
def manager(concurrency=3):
    global _dm
    if _dm is None:
        _dm = DL.DownloadManager(get_episodes, get_video_urls, OUT_DIR, concurrency=concurrency)
    return _dm
def cmd_download(series_id, rng='all', ep_covers=False):
    # irreducible cflow, using cdg fallback
    """命令行下载: 用下载管理器(并发+断点续传),轮询进度。"""
    dm = manager()
    tid = dm.submit(series_id, rng, ep_covers)
    last = ''
    while True:
        t = dm.status(tid)
        st = t.get('state', '')
        line = f"[{st}] {t.get('done', 0)}/{t.get('total', 0)} 完成, 失败{t.get('failed', 0)}"
        if line != last:
            print(line)
            last = line
        if st.startswith('完成') or st.startswith('错误'):
            break
        time.sleep(1.5)
    print('->', t.get('folder', ''))
def cmd_download_old(series_id, rng='all', ep_covers=False):
    meta, eps = get_episodes(series_id)
    title = sanitize(meta['title'])
    print(f"《{title}》共 {len(eps)} 集 | {meta['status']} | {meta['play_cnt']}播放 | 标签:{'/'.join(meta['category'])}")
    folder = os.path.join(OUT_DIR, title)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, 'info.json'), 'w', encoding='utf-8') as f:
        json.dump({**meta, 'episodes': eps}, f, ensure_ascii=False, indent=2)
    if meta.get('cover'):
        cov = os.path.join(folder, f"cover{img_ext(meta['cover'])}")
        if not os.path.exists(cov):
            print('  下载封面...')
            download_image(meta['cover'], cov)
    if rng != 'all':
        m = re.match('(\\d+)-(\\d+)', rng)
        if m:
            lo, hi = (int(m.group(1)), int(m.group(2)))
            eps = [e for e in eps if lo <= (e['index'] or 0) <= hi]
        else:
            if rng.isdigit():
                eps = [e for e in eps if (e['index'] or 0) == int(rng)]
    vids = [e['vid'] for e in eps]
    print(f'获取 {len(vids)} 集的视频直链...')
    urls = get_video_urls(vids)
    for e in eps:
        if ep_covers and e.get('cover'):
                ec = os.path.join(folder, f"{title}_第{e['index']:03d}集{img_ext(e['cover'])}")
                if not os.path.exists(ec):
                    download_image(e['cover'], ec)
        info = urls.get(e['vid'])
        if not info or not info['url']:
            print(f"  第{e['index']}集: 无直链,跳过")
            continue
        else:
            fn = os.path.join(folder, f"{title}_第{e['index']:03d}集.mp4")
            if os.path.exists(fn) and os.path.getsize(fn) > 0:
                    print(f"  第{e['index']}集: 已存在,跳过")
                    continue
            print(f"  第{e['index']}集 [{info['definition']}, {info['size'] // 1024}KB] -> {os.path.basename(fn)}")
            try:
                download_file(info['url'], fn)
            except Exception as ex:
                print(f'    下载失败: {ex}')
    print(f'完成 -> {folder}')
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    if len(sys.argv) < 2:
        print(__doc__)
        return
    else:
        cmd = sys.argv[1]
        if cmd == 'search':
            for r in search(sys.argv[2]):
                hot = f" {r['hot']}" if r['hot'] else f" {r['play_cnt']}播放"
                score = f" ★{r['score']}" if r['score'] else ''
                print(f"  {r['series_id']}  [{r['episode_cnt']}集]{score}{hot}  {r['title']}")
                if r['intro']:
                    print(f"      {r['intro']}  | 出品:{r['copyright']}")
        else:
            if cmd == 'episodes':
                meta, eps = get_episodes(sys.argv[2])
                print(f"《{meta['title']}》{meta['episode_cnt']}集 | {meta['status']} | {meta['play_cnt']}播放 | 标签:{'/'.join(meta['category'])}")
                if meta['celebrities']:
                    print('  主演: ' + '、'.join((f"{c['演员']}({c['角色']})" for c in meta['celebrities'][:6])))
                print(f"  简介: {meta['intro'][:80]}")
                for e in eps[:200]:
                    print(f"  {e['index']:>3}  vid={e['vid']}  {e['duration']}s  赞{e['digged_count']}  {e['title']}")
            else:
                if cmd == 'latest':
                    genre = sys.argv[2] if len(sys.argv) > 2 else 'short_play'
                    only_today = '--all' not in sys.argv
                    items = latest(genre, only_today=only_today, max_items=300)
                    if genre == 'short_play':
                        tag = '今日上新' if only_today else '最新上架'
                    else:
                        tag = '7天内上新·最新上架'
                    print(f'=== {GENRE_NAMES.get(genre, genre)} · {tag} ({len(items)}部) ===')
                    for it in items:
                        print(f"  [{it['episode_cnt']}集] ★{it['score']} {it['play_cnt']}播放 [{it['category']}] {it['title']}  (id={it['series_id']})")
                else:
                    if cmd == 'rank':
                        board = sys.argv[2] if len(sys.argv) > 2 else 'recommend'
                        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 30
                        print(f'=== {RANK_NAMES.get(board, board)} ===')
                        for r in rank(board, limit):
                            hot = r['hot'] or f"{r['play_cnt']}播放"
                            score = f" ★{r['score']}" if r['score'] else ''
                            print(f"  {r['rank']:>2}. [{r['episode_cnt']}集]{score} {hot}  {r['title']}  (id={r['series_id']})")
                    else:
                        if cmd == 'download':
                            rng = 'all'
                            ep_covers = '--ep-covers' in sys.argv
                            for a in sys.argv[3:]:
                                if not a.startswith('--'):
                                    rng = a
                                    break
                            cmd_download(sys.argv[2], rng, ep_covers)
                        else:
                            if cmd == 'filters':
                                genre = sys.argv[2] if len(sys.argv) > 2 else 'short_play'
                                print(f'=== {GENRE_NAMES.get(genre, genre)} 筛选面板 ===')
                                for row in filters(genre):
                                    opts = '  '.join((f"{it['name']}={it['id']}" for it in row['items']))
                                    print(f"【{row['row_name']}】(type={row['type']}, 多选={row['selection_type'] == 2})\n  {opts}")
                            else:
                                if cmd == 'browse':
                                    genre = sys.argv[2] if len(sys.argv) > 2 and (not sys.argv[2].startswith('--')) else 'ai_series'
                                    def _opt(name):
                                        return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else None
                                    items = browse(genre, theme=_opt('--theme'), setting=_opt('--setting'), background=_opt('--bg'), sort=_opt('--sort') or 'online_time', gender=_opt('--gender'), days=_opt('--days'), status=_opt('--status'), max_items=int(_opt('--n') or 60))
                                    print(f'=== {GENRE_NAMES.get(genre, genre)} 筛选结果 ({len(items)}部) ===')
                                    for it in items:
                                        print(f"  [{it['episode_cnt']}集] ★{it['score']} {it['play_cnt']}播放 [{it['category']}] {it['title']}  (id={it['series_id']})")
                                else:
                                    print(__doc__)
if __name__ == '__main__':
    main()