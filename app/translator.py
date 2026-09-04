import os
import json
import re
import html
import threading
import time
import requests

CONFIG_DIR = os.path.join(
    os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'),
    'HongguoDownloader'
)
TRANSLATION_CACHE_FILE = os.path.join(CONFIG_DIR, 'translations_cache.json')
GEMINI_CONFIG_FILE = os.path.join(CONFIG_DIR, 'gemini_pool.json')

_t_lock = threading.Lock()
_cache = {}

def _load_cache():
    global _cache
    if os.path.exists(TRANSLATION_CACHE_FILE):
        try:
            with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}

def _save_cache():
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = TRANSLATION_CACHE_FILE + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(_cache, f, ensure_ascii=False, indent=1)
        os.replace(tmp, TRANSLATION_CACHE_FILE)
    except Exception:
        pass

_load_cache()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
}

class GeminiPoolManager:
    """Manages a pool of Gemini API Keys with auto-rotation, cooldown on 429, and quota failover."""
    def __init__(self):
        self.lock = threading.Lock()
        self.enabled = True
        self.model = "gemini-flash-latest"
        self.keys = []
        self.key_stats = {}
        self.current_idx = 0
        self.load_config()

    def load_config(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if os.path.exists(GEMINI_CONFIG_FILE):
            try:
                with open(GEMINI_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.enabled = data.get('enabled', True)
                    m = data.get('model', 'gemini-flash-latest')
                    self.model = 'gemini-flash-latest' if m == 'gemini-1.5-flash' else m
                    self.keys = [k.strip() for k in data.get('keys', []) if k.strip()]
                    self.key_stats = data.get('stats', {})
            except Exception:
                pass
        env_keys = os.environ.get('GEMINI_API_KEYS') or os.environ.get('GEMINI_API_KEY')
        if env_keys and not self.keys:
            self.keys = [k.strip() for k in env_keys.replace(',', '\n').splitlines() if k.strip()]

    def save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            data = {
                'enabled': self.enabled,
                'model': self.model,
                'keys': self.keys,
                'stats': self.key_stats
            }
            tmp = GEMINI_CONFIG_FILE + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, GEMINI_CONFIG_FILE)
        except Exception:
            pass

    def get_status(self):
        now = time.time()
        with self.lock:
            details = []
            for k in self.keys:
                st = self.key_stats.get(k, {})
                cd = st.get('cooldown_until', 0)
                is_cd = cd > now
                status_str = "cooling_down" if is_cd else st.get('status', 'ready')
                details.append({
                    'key_masked': k[:6] + '...' + k[-4:] if len(k) > 10 else '***',
                    'key_full': k,
                    'status': status_str,
                    'cooldown_remaining': max(0, int(cd - now)) if is_cd else 0,
                    'success_count': st.get('success_count', 0),
                    'error_count': st.get('error_count', 0),
                    'last_used': st.get('last_used', 0)
                })
            return {
                'enabled': self.enabled,
                'model': self.model,
                'total_keys': len(self.keys),
                'active_keys': len([d for d in details if d['status'] in ('ready', 'ok')]),
                'keys': details
            }

    def set_config(self, key_list, model=None, enabled=None):
        with self.lock:
            cleaned = []
            for k in key_list:
                k = (k or '').strip()
                if k and k not in cleaned:
                    cleaned.append(k)
            self.keys = cleaned
            if model:
                self.model = model
            if enabled is not None:
                self.enabled = bool(enabled)
            self.save_config()

    def translate_with_gemini(self, text: str) -> tuple:
        """Attempts translation using healthy Gemini API keys in the pool. Returns (translated_text, key_masked)."""
        if not self.enabled or not self.keys:
            return '', ''
        
        is_synopsis = len(text) > 50 or '\n' in text or '。' in text
        if is_synopsis:
            prompt = (
                "You are a professional translator specializing in movies and drama synopses. "
                "Translate the following Chinese drama synopsis/introduction into natural, fluent Khmer. "
                "Translate the complete text accurately, preserving its narrative and emotional tone. "
                "Return ONLY the Khmer translation without any explanation, markdown, quotation marks, or English words.\n\n"
                f"Synopsis:\n{text}"
            )
            max_tokens = 1200
        else:
            prompt = (
                "You are a professional film title translator specializing in Chinese short dramas. "
                "Translate the following Chinese drama title into a natural, engaging, native Khmer title. "
                "Return ONLY the Khmer translated title without any explanation, markdown, quotation marks, or English words.\n\n"
                f"Title: {text}"
            )
            max_tokens = 100
        
        now = time.time()
        with self.lock:
            available_keys = []
            for k in self.keys:
                st = self.key_stats.setdefault(k, {'status': 'ready', 'cooldown_until': 0, 'success_count': 0, 'error_count': 0})
                if st.get('cooldown_until', 0) <= now and st.get('status') != 'invalid':
                    available_keys.append(k)
            
            if not available_keys:
                for k in self.keys:
                    if self.key_stats[k].get('status') != 'invalid':
                        available_keys.append(k)
                if not available_keys:
                    return '', ''

        for key in available_keys:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens}
            }
            try:
                r = requests.post(url, json=payload, timeout=6)
                with self.lock:
                    st = self.key_stats.setdefault(key, {})
                    st['last_used'] = int(time.time())

                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get('candidates') or []
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts:
                            res = parts[0].get('text', '').strip()
                            res = re.sub(r'^["\'「『]|["\'」』]$', '', res).strip()
                            res = re.sub(r'^(Khmer|ចំណងជើងខ្មែរ)[:：\s]+', '', res, flags=re.I).strip()
                            if res:
                                with self.lock:
                                    st['status'] = 'ok'
                                    st['success_count'] = st.get('success_count', 0) + 1
                                    self.save_config()
                                masked = key[:6] + '...' + key[-4:] if len(key) > 10 else '***'
                                return res, masked
                elif r.status_code == 429:
                    with self.lock:
                        st['status'] = 'cooling_down'
                        st['cooldown_until'] = int(time.time()) + 60
                        st['error_count'] = st.get('error_count', 0) + 1
                        self.save_config()
                    continue
                elif r.status_code in (400, 403):
                    with self.lock:
                        st['status'] = 'invalid'
                        st['error_count'] = st.get('error_count', 0) + 1
                        self.save_config()
                    continue
            except Exception:
                continue

        return '', ''

gemini_pool = GeminiPoolManager()

def translate_to_khmer(text: str, force_provider: str = None) -> str:
    """Translates text to Khmer with Gemini Pool -> Google Translate fallback cascade."""
    if not text:
        return ''
    text = text.strip()
    
    with _t_lock:
        if text in _cache:
            return _cache[text]

    res = ''

    # Step 1: Try Gemini API Key Pool if enabled
    if force_provider != 'google':
        try:
            gem_res, _ = gemini_pool.translate_with_gemini(text)
            if gem_res:
                res = gem_res
        except Exception:
            pass

    # Step 2: Fallback to Google Translate mobile web
    if not res:
        try:
            u = f"https://translate.google.com/m?sl=zh-CN&tl=km&q={requests.utils.quote(text)}"
            r = requests.get(u, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                m = re.search(r'class="result-container">([^<]+)<', r.text)
                if m:
                    res = html.unescape(m.group(1).strip())
        except Exception:
            pass

    # Step 3: Fallback to Google Translate gtx API
    if not res:
        try:
            u = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=km&dt=t&q={requests.utils.quote(text)}"
            r = requests.get(u, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                data = r.json()
                res = "".join([part[0] for part in data[0] if part and part[0]]).strip()
        except Exception:
            pass

    # Step 4: Fallback to MyMemory
    if not res:
        try:
            u = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=zh-CN|km"
            r = requests.get(u, headers=HEADERS, timeout=5)
            if r.status_code == 200:
                j = r.json()
                res = html.unescape(j.get('responseData', {}).get('translatedText') or '').strip()
        except Exception:
            pass

    if res:
        with _t_lock:
            _cache[text] = res
            _save_cache()
    return res

def translate_batch(texts: list) -> dict:
    """Translates a batch of texts in parallel, utilizing cache and Gemini Pool + Google fallbacks."""
    out = {}
    missing = []
    for t in texts:
        t = (t or '').strip()
        if not t:
            continue
        with _t_lock:
            if t in _cache:
                out[t] = _cache[t]
                continue
        missing.append(t)
    
    if missing:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(translate_to_khmer, t): t for t in missing}
            for fut in futs:
                t = futs[fut]
                try:
                    out[t] = fut.result()
                except Exception:
                    out[t] = ''
    return out
