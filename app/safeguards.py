# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\safeguards.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-08-31 16:51:18 UTC (1788195078)

"""风控防护层: 缓存 + 节流 + 风控识别。被 hongguo.py 使用。"""
import time
import threading
import hashlib
import json
import random
import os
import pickle
_cache = {}
_cache_lock = threading.Lock()
_redis = None
_REDIS_URL = os.environ.get('REDIS_URL')
if _REDIS_URL:
    try:
        import redis as _redislib
        _redis = _redislib.from_url(_REDIS_URL)
        _redis.ping()
        print('[cache] 使用 Redis:', _REDIS_URL)
    except Exception as e:
        print('[cache] Redis 不可用,回退内存:', e)
        _redis = None
def cache_get(key):
    if _redis is not None:
        try:
            v = _redis.get('hg:' + key)
            return pickle.loads(v) if v else None
        except Exception:
            return None
    else:
        with _cache_lock:
            v = _cache.get(key)
            if v and v[0] > time.time():
                return v[1]
            else:
                if v:
                    _cache.pop(key, None)
        return None
def cache_set(key, val, ttl):
    if _redis is not None:
        try:
            _redis.setex('hg:' + key, int(ttl), pickle.dumps(val))
        except Exception:
            pass
        return None
    else:
        with _cache_lock:
            _cache[key] = (time.time() + ttl, val)
def cache_key(*parts):
    return hashlib.md5(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
class Throttle:
    def __init__(self, min_interval=float(os.environ.get('HG_THROTTLE_MIN_INTERVAL', '0.6')), jitter=float(os.environ.get('HG_THROTTLE_JITTER', '0.4')), burst=float(os.environ.get('HG_THROTTLE_BURST', '3')), refill_per_sec=float(os.environ.get('HG_THROTTLE_REFILL', '1.5'))):
        self.min_interval = min_interval
        self.jitter = jitter
        self.lock = threading.Lock()
        self.last = 0.0
        self.tokens = burst
        self.burst = burst
        self.refill = refill_per_sec
        self.token_ts = time.time()
    def wait(self):
        with self.lock:
            now = time.time()
            self.tokens = min(self.burst, self.tokens + (now - self.token_ts) * self.refill)
            self.token_ts = now
            gap = now - self.last
            need = self.min_interval + random.uniform(0, self.jitter)
            sleep = 0.0
            if gap < need:
                sleep = need - gap
            if self.tokens < 1:
                sleep = max(sleep, (1 - self.tokens) / self.refill)
            if sleep > 0:
                time.sleep(sleep)
            self.tokens = max(0, self.tokens - 1)
            self.last = time.time()
throttle = Throttle()
class RiskControlError(Exception):
    # return None
    pass
class AuthExpiredError(Exception):
    """登录态(token/cookie)过期"""
    pass
class ContentUnavailableError(Exception):
    """剧集/内容已下架、删除或不存在(与设备/风控无关 → 不换设备、不重试, 直接判定不可用)。"""
GONE_CODES = {101001}
GONE_KEYWORDS = ('已下架', '下架', '已删除', '内容不存在', '已失效', '不存在')
AUTH_CODES = {403, 1001, 401, 8}
AUTH_KEYWORDS = ('token', '登录', 'login', '未登录', 'not login', 'unauthor', '登陆', 'session', 'expire', '凭证', '重新登录')
RISK_CODES = {8, 100002, 110001, 100001}
RISK_KEYWORDS = ('verify', 'captcha', 'risk', '频繁', '稍后', '验证', 'rate limit', 'too many')
def check_response(j):
    """检查响应。正常返回; 登录过期抛 AuthExpiredError; 风控/异常抛 RiskControlError。"""
    if not isinstance(j, dict):
        return
    else:
        code = j.get('code')
        msg = (j.get('message') or '') + (j.get('BaseResp', {}).get('StatusMessage', '') if isinstance(j.get('BaseResp'), dict) else '')
        ml = msg.lower()
        if code in (0, None):
            if any((k in ml for k in RISK_KEYWORDS)):
                raise RiskControlError(f'疑似风控: {msg}')
        else:
            if code in GONE_CODES or any((k in msg for k in GONE_KEYWORDS)):
                raise ContentUnavailableError(f'内容已下架/不存在 code={code} msg={msg}')
            else:
                if code in AUTH_CODES or any((k in ml for k in AUTH_KEYWORDS)):
                    raise AuthExpiredError(f'登录态失效 code={code} msg={msg}')
                else:
                    if code in RISK_CODES or any((k in ml for k in RISK_KEYWORDS)):
                        raise RiskControlError(f'风控触发 code={code} msg={msg}')
                    else:
                        raise RiskControlError(f'接口返回异常 code={code} msg={msg}')