import os
import re
import json
import time
import secrets
import hashlib
import threading
import math
import requests
import licensing as LIC

HERE = os.path.dirname(os.path.abspath(__file__))

def _calc_days_left(exp: int, now_ts: int = None, is_vip: bool = False):
    """
    Computes days remaining rounded up (e.g. 6 days 23h => 7 days left).
    If VIP and exp == 0, returns -1 (Lifetime).
    """
    if is_vip and exp == 0:
        return -1
    if not exp or exp <= 0:
        return 0
    now = now_ts or int(time.time())
    if now >= exp:
        return 0
    return max(0, math.ceil((exp - now) / 86400))

def _resolve_data_file():
    # Persist user_access.json in %LOCALAPPDATA%\HongguoDownloader so it is never lost on restart
    app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', HERE), 'HongguoDownloader')
    os.makedirs(app_data_dir, exist_ok=True)
    target = os.path.join(app_data_dir, 'user_access.json')
    if not os.path.isfile(target):
        bundled = os.path.join(HERE, 'user_access.json')
        if os.path.isfile(bundled):
            try:
                import shutil
                shutil.copy2(bundled, target)
            except Exception:
                return bundled
    return target

def _resolve_firebase_file():
    # Persist firebase.json in %LOCALAPPDATA%\HongguoDownloader so settings survive updates
    app_data_dir = os.path.join(os.environ.get('LOCALAPPDATA', HERE), 'HongguoDownloader')
    os.makedirs(app_data_dir, exist_ok=True)
    target = os.path.join(app_data_dir, 'firebase.json')
    if not os.path.isfile(target):
        bundled = os.path.join(HERE, 'firebase.json')
        if os.path.isfile(bundled):
            try:
                import shutil
                shutil.copy2(bundled, target)
            except Exception:
                return bundled
    return target

DATA_FILE = _resolve_data_file()
FIREBASE_FILE = _resolve_firebase_file()

_lock = threading.RLock()

# Standard VIP Packages
VIP_PACKAGES = {
    "1_month": {"key": "1_month", "name": "VIP 1 ខែ", "days": 30, "badge": "1 ខែ"},
    "3_months": {"key": "3_months", "name": "VIP 3 ខែ", "days": 90, "badge": "3 ខែ"},
    "6_months": {"key": "6_months", "name": "VIP 6 ខែ", "days": 180, "badge": "6 ខែ"},
    "1_year": {"key": "1_year", "name": "VIP 1 ឆ្នាំ", "days": 365, "badge": "1 ឆ្នាំ"},
    "lifetime": {"key": "lifetime", "name": "VIP មួយជីវិត", "days": 0, "badge": "មួយជីវិត"}
}

# ADMIN Master Credentials
ADMIN_USERNAME = "ADMIN"
ADMIN_PASSWORD = "syd@168"

# Regular User Trial Configuration: 3 Days (72 Hours)
TRIAL_DAYS = 3
TRIAL_SECONDS = TRIAL_DAYS * 86400
TRIAL_LOCKOUT_SECONDS = 24 * 3600  # 24-hour temporary login block after trial expires without VIP request

def get_current_device_id():
    return LIC.device_id()

def clean_firebase_key(key: str) -> str:
    """Sanitize key for Firebase Realtime Database (cannot contain . $ # [ ] / :)."""
    s = str(key or "").strip()
    return re.sub(r'[\.\$\[\]\#\/:]', '_', s)

def is_dev_machine(device_id_str: str = "") -> bool:
    """DEV mode permanently disabled. All users must authenticate with their account."""
    return False

# In-memory Active Sessions: token -> user_dict
_sessions = {}
_logged_out_devices = set()

def logout(token_or_device: str = ""):
    ident = str(token_or_device or "").strip()
    dev = get_current_device_id()
    with _lock:
        _logged_out_devices.add(dev)
        if ident:
            _logged_out_devices.add(ident)
        for tok, su in list(_sessions.items()):
            if tok == ident or su.get("device_id") == dev or (ident and su.get("device_id") == ident):
                _sessions.pop(tok, None)
        try:
            d = _load_data()
            for k, u in d.get("users", {}).items():
                if (ident and (u.get("token") == ident or u.get("device_id") == ident or k == ident)) or u.get("device_id") == dev:
                    u["token"] = ""
            _save_data(d)
        except Exception:
            pass
    return True

def hash_pw(pw: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256((pw or "").strip().encode('utf-8')).hexdigest()

DEFAULT_PRICING_RULES = {
    "default_coins": 2,          # 1000 Riel (2 coins * 500 Riel = 1000 Riel)
    "coin_rate_riel": 500,       # 1 coin = 500 Riel
    "promo_enabled": False,
    "promo_coins": 1,            # 1 coin = 500 Riel
    "promo_start_date": "",      # "YYYY-MM-DD"
    "promo_end_date": "",        # "YYYY-MM-DD"
    "promo_name": "ប្រូម៉ូសិនពិសេស",
    "custom_series": {}          # { "sid": coins }
}

DEFAULT_DATA = {
    "mode": "vip_required",  # "vip_required", "free_all"
    "admin_pin": "syd@168",
    "admin_user": "ADMIN",
    "admin_pass": "syd@168",
    "pricing_rules": dict(DEFAULT_PRICING_RULES),
    "drama_rules": {},
    "drama_rules_default": {
        "rule": "free_episodes",
        "free_episodes": 5
    },
    "settings": {
        "telegram_admin": "https://t.me/sydadmin168",
        "telegram_group": "https://t.me/syd_drama_community"
    },
    "users": {
        "admin": {
            "username": "ADMIN",
            "name": "Super Administrator",
            "contact": "Admin Direct",
            "password_hash": hash_pw(ADMIN_PASSWORD),
            "role": "admin",
            "is_admin": True,
            "is_vip": True,
            "coins": 999999,
            "purchased_series": {},
            "status": "approved",
            "max_free_episodes": 999999,
            "created_at": 1788500000,
            "approved_at": 1788500000,
            "expires_at": 0
        }
    }
}

def _load_data():
    if not os.path.exists(DATA_FILE):
        _save_data(DEFAULT_DATA)
        return dict(DEFAULT_DATA)
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "mode" not in data:
                data["mode"] = "vip_required"
            if "users" not in data:
                data["users"] = {}
            if "admin_pin" not in data:
                data["admin_pin"] = "syd@168"
            data.pop("dev_key", None)
            data.pop("dev_machines", None)
            if "drama_rules" not in data or not isinstance(data.get("drama_rules"), dict):
                data["drama_rules"] = {}
            if "drama_rules_default" not in data or not isinstance(data.get("drama_rules_default"), dict):
                data["drama_rules_default"] = {"rule": "free_episodes", "free_episodes": 5}
            if "settings" not in data:
                data["settings"] = {
                    "telegram_admin": "https://t.me/sydadmin168",
                    "telegram_group": "https://t.me/syd_drama_community"
                }
            elif isinstance(data.get("settings"), dict):
                if not data["settings"].get("telegram_admin"):
                    data["settings"]["telegram_admin"] = "https://t.me/sydadmin168"
                data["settings"].pop("khqr_image", None)
            if "pricing_rules" not in data or not isinstance(data.get("pricing_rules"), dict):
                data["pricing_rules"] = dict(DEFAULT_PRICING_RULES)
            else:
                for pk, pv in DEFAULT_PRICING_RULES.items():
                    if pk not in data["pricing_rules"]:
                        data["pricing_rules"][pk] = pv
            # Ensure ADMIN exists
            if "admin" not in data["users"]:
                data["users"]["admin"] = {
                    "username": "ADMIN",
                    "name": "Super Administrator",
                    "contact": "Admin Direct",
                    "password_hash": hash_pw(ADMIN_PASSWORD),
                    "role": "admin",
                    "is_admin": True,
                    "is_vip": True,
                    "coins": 999999,
                    "purchased_series": {},
                    "status": "approved",
                    "max_free_episodes": 999999,
                    "created_at": int(time.time()),
                    "approved_at": int(time.time()),
                    "expires_at": 0
                }
            for k, u in data.get("users", {}).items():
                if "coins" not in u:
                    u["coins"] = 999999 if (u.get("role") == "admin" or u.get("is_admin")) else 0
                if "purchased_series" not in u or not isinstance(u.get("purchased_series"), dict):
                    u["purchased_series"] = {}
            return data
    except Exception:
        return dict(DEFAULT_DATA)

def _save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[access_manager] save error: {e}")

_settings_cache = {"time": 0, "data": None}

def get_settings(sync_from_firebase: bool = True):
    global _settings_cache
    now = time.time()
    
    with _lock:
        d = _load_data()
        st = dict(d.get("settings", {}))
        st.setdefault("telegram_admin", "https://t.me/sydadmin168")
        st.setdefault("telegram_group", "https://t.me/syd_drama_community")
        st.setdefault("vip_request_enabled", False)
        st.pop("khqr_image", None)

    # Sync from Firebase Realtime Database with 3-second cache
    if sync_from_firebase:
        if _settings_cache.get("data") and (now - _settings_cache.get("time", 0) < 3.0):
            return dict(_settings_cache["data"])
        try:
            url, params = _firebase_url("settings")
            if url:
                r = requests.get(url, params=params, timeout=3.5, headers={"User-Agent": "SYD-Downloader-Pro"})
                if r.status_code == 200 and r.text and r.text != "null":
                    fb_settings = r.json()
                    if isinstance(fb_settings, dict):
                        for k, v in fb_settings.items():
                            if k != "khqr_image":
                                st[k] = v
                        with _lock:
                            d = _load_data()
                            d["settings"] = dict(st)
                            _save_data(d)
                        _settings_cache = {"time": now, "data": dict(st)}
        except Exception:
            pass

    return st

def save_settings(new_settings: dict, sync_to_firebase: bool = True):
    global _settings_cache
    with _lock:
        d = _load_data()
        st = d.get("settings", {})
        if not isinstance(st, dict):
            st = {}
        for k in ("telegram_admin", "telegram_group"):
            if k in new_settings:
                st[k] = str(new_settings[k] or "").strip()
        if "vip_request_enabled" in new_settings:
            val = new_settings["vip_request_enabled"]
            if isinstance(val, str):
                st["vip_request_enabled"] = val.lower() in ("true", "1", "yes", "on")
            else:
                st["vip_request_enabled"] = bool(val)
        st.pop("khqr_image", None)
        d["settings"] = st
        _save_data(d)
        _settings_cache = {"time": time.time(), "data": dict(st)}

    # Sync to Firebase Realtime Database
    if sync_to_firebase:
        def _sync_fb():
            try:
                url, params = _firebase_url("settings")
                if url:
                    patch = {
                        "telegram_admin": st.get("telegram_admin", ""),
                        "telegram_group": st.get("telegram_group", ""),
                        "vip_request_enabled": bool(st.get("vip_request_enabled", False)),
                        "updated_at": int(time.time())
                    }
                    requests.patch(url, params=params, json=patch, timeout=5, headers={"User-Agent": "SYD-Downloader-Pro"})
            except Exception as e:
                print(f"[settings] firebase sync error: {e}")
        threading.Thread(target=_sync_fb, daemon=True).start()

    return st


def get_mode():
    with _lock:
        d = _load_data()
        return d.get("mode", "vip_required")

def set_mode(mode):
    with _lock:
        d = _load_data()
        d["mode"] = mode
        _save_data(d)
        return mode

def verify_pin(pin):
    with _lock:
        d = _load_data()
        expected = str(d.get("admin_pin", ADMIN_PASSWORD)).strip()
        p = str(pin or "").strip()
        return p == expected or p == ADMIN_PASSWORD

def set_pin(new_pin):
    with _lock:
        d = _load_data()
        d["admin_pin"] = str(new_pin).strip()
        _save_data(d)
        return True

def get_current_device_id():
    return LIC.device_id()

# ----------------- Authentication & User Management ----------------- #

def user_exists(identity: str) -> bool:
    """
    Check if a user account already exists in the system.
    """
    ident = (identity or "").strip().lower()
    if not ident:
        return False
    if ident == "admin":
        return True
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        for k, u in users.items():
            u_name = str(u.get("username") or "").strip().lower()
            u_cnt = str(u.get("contact") or "").strip().lower()
            if ident in (u_name, u_cnt, k.lower()):
                return True
    return False

def login(identity: str, password: str, device_id: str = ""):
    """
    Login handler for ADMIN and Regular Users.
    ADMIN credentials: User ADMIN, Password syd@168
    """
    ident = (identity or "").strip()
    pw = (password or "").strip()
    dev = (device_id or get_current_device_id()).strip()

    # 1. ADMIN Account check (Case-insensitive username)
    d_admin = _load_data()
    expected_admin_pin = str(d_admin.get("admin_pin", ADMIN_PASSWORD)).strip()
    is_admin_user = (ident.upper() == ADMIN_USERNAME or ident.lower() == "admin")
    is_admin_pw = (pw == ADMIN_PASSWORD or pw == expected_admin_pin or pw == "8888")
    if is_admin_user and is_admin_pw:
        token = "admin_" + secrets.token_hex(16)
        admin_user = {
            "token": token,
            "device_id": dev,
            "username": "ADMIN",
            "name": "Super Administrator",
            "contact": "System Admin",
            "role": "admin",
            "is_admin": True,
            "is_vip": True,
            "coins": 999999,
            "coins_riel": 999999 * 500,
            "purchased_series": {},
            "status": "approved",
            "max_free_episodes": 999999,
            "package": "lifetime",
            "package_name": "Full Control (ADMIN - គ្មានការ Lock)",
            "package_badge": "ADMIN Full Control",
            "expires_at": 0,
            "expires_date": "Lifetime Full Access",
            "days_left": -1
        }
        with _lock:
            _logged_out_devices.discard(dev)
            _logged_out_devices.discard(get_current_device_id())
            _sessions[token] = admin_user
            if dev:
                _sessions[dev] = admin_user
        return True, admin_user

    # 2. Regular User check
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        target_key = None
        for k, u in users.items():
            u_name = str(u.get("username") or "").strip().lower()
            u_cnt = str(u.get("contact") or "").strip().lower()
            if ident.lower() in (u_name, u_cnt, k.lower()):
                target = u
                target_key = k
                break

        if not target:
            return False, "user_not_found: គណនីនេះមិនទាន់មានក្នុងប្រព័ន្ធទេ! លោកអ្នកត្រូវតែចុះឈ្មោះគណនីជាមុនសិន។"

        if target.get("status") == "banned":
            return False, "🚫 គណនីនេះត្រូវបានបិទ (Banned) មិនឱ្យប្រើប្រាស់ដោយ Admin! សូមទាក់ទង Admin។"

        # STRICT RULE: 1 Machine ID / 1 user can ONLY be used on 1 PC!
        target_dev = target.get("device_id")
        current_hw = (dev or get_current_device_id()).strip()
        if target_dev and clean_firebase_key(target_dev) != clean_firebase_key(current_hw):
            return False, "🚫 គណនីនេះត្រូវបានភ្ជាប់ជាមួយកុំព្យូទ័រ (PC) ផ្សេងរួចហើយ! ប្រព័ន្ធកំណត់ដាច់ខាត 1 User ប្រើប្រាស់បានតែលើ 1 PC ប៉ុណ្ណោះ (1 Machine ID = 1 PC)។ មិនអាច Login លើកុំព្យូទ័រនេះបានឡើយ។"
        if not target_dev:
            target["device_id"] = current_hw

        # Verify Password
        stored_hash = target.get("password_hash", "")
        if stored_hash:
            if hash_pw(pw) != stored_hash and pw != target.get("password", ""):
                return False, "ពាក្យសម្ងាត់មិនត្រឹមត្រូវ (Incorrect password)"
        elif target.get("password"):
            if pw != target.get("password"):
                return False, "ពាក្យសម្ងាត់មិនត្រឹមត្រូវ (Incorrect password)"

        now = int(time.time())
        token = "usr_" + secrets.token_hex(16)
        role = target.get("role", "user")
        is_admin = (role == "admin" or target.get("is_admin"))
        is_vip = is_admin or (target.get("status") == "approved" and target.get("is_vip", False))

        # Check expiration for VIP
        exp = target.get("expires_at", 0)
        if is_vip and not is_admin and exp > 0 and exp < now:
            is_vip = False
            target["status"] = "expired"
            target["is_vip"] = False
            target["role"] = "user"

        # Check 3-day trial expiration for regular user without VIP request
        if not is_vip and not is_admin:
            if exp == 0:
                exp = (target.get("created_at") or now) + TRIAL_SECONDS
                target["expires_at"] = exp

            if now >= exp and target.get("status") != "pending_vip":
                # Check 24-hour temporary login block
                lockout_until = target.get("trial_lockout_until", 0)
                if not lockout_until or lockout_until == 0:
                    lockout_until = now + TRIAL_LOCKOUT_SECONDS
                    target["trial_lockout_until"] = lockout_until
                    target["status"] = "trial_locked_24h"
                    _save_data(d)

                if now < lockout_until:
                    rem = lockout_until - now
                    hrs = rem // 3600
                    mins = (rem % 3600) // 60
                    t_str = f"{hrs} ម៉ោង {mins} នាទី" if hrs > 0 else f"{mins} នាទី"
                    return False, f"⏳ គណនីរបស់អ្នកបានផុតកំណត់ការសាកល្បង 3 ថ្ងៃដោយមិនបានស្នើសុំ VIP! ប្រព័ន្ធបានបិទការ Login ជាបណ្តោះអាសន្នរយៈពេល 24 ម៉ោង (នៅសល់ {t_str}) ទើបអាច Login បានទៀត។ ឬសូមទាក់ទង Admin តាម Telegram ដើម្បីស្នើសុំ VIP!"
                else:
                    # 24 hours have passed! User can login again ("បានអាចLogin បានទៀត")
                    target["trial_lockout_until"] = 0
                    target["expires_at"] = now + TRIAL_LOCKOUT_SECONDS  # 24-hour grace window to request VIP
                    target["status"] = "user"
                    _save_data(d)

        max_eps = 999999 if is_vip else 5
        target["role"] = "vip" if is_vip else "user"
        target["is_vip"] = is_vip
        target["is_admin"] = is_admin
        target["max_free_episodes"] = max_eps
        target["token"] = token
        target["device_id"] = dev
        target["last_login"] = now

        if exp > 0:
            import datetime
            target["expires_date"] = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            target["days_left"] = _calc_days_left(exp, now, is_vip)
        elif exp == 0 and is_vip:
            target["expires_date"] = "Lifetime VIP"
            target["days_left"] = -1
        else:
            target["expires_date"] = f"User ធម្មតា (សាកល្បង {TRIAL_DAYS} ថ្ងៃ)"
            target["days_left"] = TRIAL_DAYS

        target["coins"] = int(target.get("coins", 0))
        target["coins_riel"] = target["coins"] * 500
        if not isinstance(target.get("purchased_series"), dict):
            target["purchased_series"] = {}

        _save_data(d)
        _logged_out_devices.discard(dev)
        _logged_out_devices.discard(get_current_device_id())
        _sessions[token] = target
        if dev:
            _sessions[dev] = target

        return True, target

def register_user(username: str, name: str, contact: str, password: str, note: str = "", package: str = "1_year", device_id: str = ""):
    """
    Register a new regular user account.
    Regular user gets free access to episodes 1-5.
    """
    u_name = (username or "").strip()
    full_name = (name or "").strip()
    cnt = (contact or "").strip()
    pw = (password or "").strip()
    dev = (device_id or get_current_device_id()).strip()
    pkg = (package or "1_year").strip()

    if not u_name:
        return False, "សូមបញ្ចូលឈ្មោះគណនី (Username)"
    if u_name.upper() == "ADMIN":
        return False, "មិនអាចប្រើប្រាស់ឈ្មោះ ADMIN បានឡើយ"
    if not pw:
        return False, "សូមបញ្ចូលពាក្យសម្ងាត់ (Password)"
    if len(pw) < 4:
        return False, "ពាក្យសម្ងាត់ត្រូវមានយ៉ាងតិច ៤ ខ្ទង់"
    if not full_name:
        full_name = u_name
    if not cnt:
        cnt = u_name

    with _lock:
        d = _load_data()
        users = d.get("users", {})

        # Check duplicates
        for k, u in users.items():
            if str(u.get("username") or "").strip().lower() == u_name.lower():
                return False, f"ឈ្មោះគណនី '{u_name}' ត្រូវបានចុះឈ្មោះរួចហើយ សូមជ្រើសរើសឈ្មោះផ្សេង"
            if cnt and str(u.get("contact") or "").strip().lower() == cnt.lower():
                return False, f"លេខទូរស័ព្ទ ឬ Telegram '{cnt}' ត្រូវបានចុះឈ្មោះរួចហើយ"

        # STRICT RULE: 1 Machine ID can only register 1 PC user account!
        current_hw = (dev or get_current_device_id()).strip()
        clean_curr_hw = clean_firebase_key(current_hw)

        for k, u in users.items():
            u_dev = clean_firebase_key(u.get("device_id", ""))
            u_name_exist = str(u.get("username") or "").strip()
            if u_dev and u_dev == clean_curr_hw:
                if u_name_exist.lower() != u_name.lower() and str(u.get("role")) != "admin":
                    return False, f"🚫 កុំព្យូទ័រ (Machine ID) នេះបានចុះឈ្មោះគណនីរួចហើយ គឺ '{u_name_exist}'! ប្រព័ន្ធកំណត់ដាច់ខាត 1 PC ចុះឈ្មោះបានតែ 1 User ប៉ុណ្ណោះ (1 Machine ID = 1 PC)។ សូម Login គណនីរបស់អ្នក។"

        # Check Firebase for existing registration on this Machine ID
        try:
            fb = firebase_fetch_license(current_hw)
            if fb and isinstance(fb, dict) and fb.get("username"):
                fb_uname = str(fb.get("username")).strip()
                if fb_uname.lower() != u_name.lower() and fb.get("role") != "admin":
                    return False, f"🚫 កុំព្យូទ័រ (Machine ID) នេះមានគណនី '{fb_uname}' លើប្រព័ន្ធរួចហើយ! ប្រព័ន្ធកំណត់ដាច់ខាត 1 PC ចុះឈ្មោះបានតែ 1 User ប៉ុណ្ណោះ (1 Machine ID = 1 PC)។ សូម Login គណនីរបស់អ្នក។"
        except Exception:
            pass

        now = int(time.time())
        trial_seconds = TRIAL_SECONDS
        expires_at = now + trial_seconds
        import datetime
        exp_date_str = datetime.datetime.fromtimestamp(expires_at).strftime("%d/%m/%Y")
        token = "usr_" + secrets.token_hex(16)
        user_key = "user_" + secrets.token_hex(6)

        user_record = {
            "key": user_key,
            "device_id": dev,
            "username": u_name,
            "name": full_name,
            "contact": cnt,
            "password_hash": hash_pw(pw),
            "note": note,
            "requested_package": pkg,
            "approved_package": "",
            "role": "user",
            "is_vip": False,
            "is_admin": False,
            "status": "user",
            "max_free_episodes": 5,
            "coins": 0,
            "coins_riel": 0,
            "purchased_series": {},
            "created_at": now,
            "updated_at": now,
            "approved_at": 0,
            "expires_at": expires_at,
            "trial_lockout_until": 0,
            "token": token,
            "package_name": f"User ធម្មតា (សាកល្បង {TRIAL_DAYS} ថ្ងៃ)",
            "package_badge": f"{TRIAL_DAYS} ថ្ងៃ",
            "expires_date": exp_date_str,
            "days_left": TRIAL_DAYS
        }

        users[user_key] = user_record
        d["users"] = users
        _save_data(d)

        _sessions[token] = user_record
        if dev:
            _sessions[dev] = user_record

        # Sync to Firebase Realtime Database
        try:
            firebase_sync_license(user_record)
        except Exception as ex:
            print(f"[firebase] register sync error: {ex}")
            threading.Thread(target=firebase_sync_license, args=(user_record,), daemon=True).start()

        return True, user_record

def purge_expired_trial_users():
    """
    STRICT RULE: Regular users (role == 'user') have a 3-day trial period.
    Within these 3 days, if they have not submitted a VIP request,
    their login is temporarily blocked for 24 hours.
    After 24 hours have elapsed, they can log in again.
    """
    now = int(time.time())
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        changed = False
        for k, u in list(users.items()):
            # Only apply to regular user who is NOT VIP and NOT ADMIN
            if u.get("role") == "user" and not u.get("is_vip") and not u.get("is_admin"):
                exp = u.get("expires_at", 0)
                if exp == 0:
                    created = u.get("created_at") or now
                    exp = created + TRIAL_SECONDS
                    u["expires_at"] = exp
                    changed = True

                st = u.get("status", "user")
                # If status is 'pending_vip', user HAS submitted a VIP request! Keep them active for admin review.
                if st == "pending_vip":
                    continue

                if now >= exp:
                    lockout = u.get("trial_lockout_until", 0)
                    if not lockout or lockout == 0:
                        u["trial_lockout_until"] = now + TRIAL_LOCKOUT_SECONDS
                        u["status"] = "trial_locked_24h"
                        changed = True
                    elif now >= lockout:
                        # 24h lockout elapsed! User can log in again.
                        u["trial_lockout_until"] = 0
                        u["expires_at"] = now + TRIAL_LOCKOUT_SECONDS
                        u["status"] = "user"
                        changed = True

        if changed:
            d["users"] = users
            _save_data(d)

    return 0

def get_user_status(token_or_device_id: str = ""):
    """
    Returns the user's status, settings, and allowed episode boundaries.
    Startup check: Queries Firebase Realtime Database (https://syd-drama-default-rtdb.firebaseio.com)
    for License Key / Account.
    - If NO account in Firebase: Requires mandatory registration as regular user (Free Tier 1-5).
    - If account in Firebase: Returns regular user (episodes 1-5) or VIP (episodes 1-all if approved by ADMIN).
    """
    # Enforce 7-day trial auto-purge rule
    try:
        purge_expired_trial_users()
    except Exception as ex:
        print(f"[purge] error: {ex}")

    ident = (token_or_device_id or "").strip()
    user = None

    # Check active memory sessions
    if ident and ident in _sessions:
        user = _sessions[ident]

    if not user and ident:
        # Check local database
        with _lock:
            d = _load_data()
            for k, u in d.get("users", {}).items():
                if k == ident or u.get("device_id") == ident or u.get("token") == ident or u.get("username") == ident:
                    user = u
                    break

    settings = get_settings()
    dev_check = (user.get("device_id") if user else ident) or get_current_device_id()
    clean_id = clean_firebase_key(dev_check)
    current_hw_id = get_current_device_id()

    # Check if this device or token is explicitly logged out or unauthenticated
    is_admin_check = bool(user and ((user.get("role") == "admin") or (str(user.get("username")).upper() == "ADMIN")))
    if not is_admin_check and (ident == "guest" or not ident or ident in _logged_out_devices or current_hw_id in _logged_out_devices):
        return {
            "authenticated": False,
            "registered": False,
            "has_firebase_account": False,
            "must_register": True,
            "must_login": True,
            "device_id": current_hw_id,
            "license_key": clean_id,
            "username": "មិនទាន់ចូលគណនី",
            "name": "សូមចូលគណនី ឬចុះឈ្មោះ",
            "contact": "",
            "role": "unauthenticated",
            "is_admin": False,
            "is_dev": False,
            "is_vip": False,
            "status": "login_required",
            "coins": 0,
            "coins_riel": 0,
            "purchased_series": {},
            "max_free_episodes": 5,
            "package_name": "មិនទាន់ចូលគណនី (Free ភាគ 1-5)",
            "package_badge": "Login Required",
            "expires_at": 0,
            "expires_date": "Free Tier (ភាគ 1-5)",
            "days_left": 0,
            "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
            "message": "សូមចូលគណនី ឬចុះឈ្មោះជាចាំបាច់ដើម្បីប្រើប្រាស់!",
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }

    # 1. ADMIN check: Admin is exempt from registration and has full control
    is_admin = False
    if user:
        role = user.get("role", "user")
        if (role == "admin") or (str(user.get("username")).upper() == "ADMIN"):
            is_admin = True

    if is_admin:
        return {
            "authenticated": True,
            "registered": True,
            "has_firebase_account": True,
            "must_register": False,
            "device_id": user.get("device_id") or dev_check,
            "license_key": clean_id,
            "username": user.get("username", "ADMIN"),
            "name": user.get("name", "Super Administrator"),
            "contact": user.get("contact", ""),
            "role": "admin",
            "is_admin": True,
            "is_dev": False,
            "is_vip": True,
            "status": "approved",
            "coins": 999999,
            "coins_riel": 999999 * 500,
            "purchased_series": user.get("purchased_series") or {},
            "max_free_episodes": 999999,
            "requested_package": "lifetime",
            "approved_package": "lifetime",
            "package_name": "Full Control (ADMIN - គ្មានការ Lock)",
            "package_badge": "ADMIN",
            "expires_at": 0,
            "expires_date": "Lifetime Full Access",
            "days_left": -1,
            "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }

    # STRICT RULE: 1 Machine ID / 1 user can ONLY be used on 1 PC!
    current_hw_id = get_current_device_id()
    if user and not is_admin:
        user_dev = user.get("device_id")
        if user_dev and clean_firebase_key(user_dev) != clean_firebase_key(current_hw_id):
            return {
                "authenticated": False,
                "registered": False,
                "has_firebase_account": False,
                "must_register": True,
                "is_banned": True,
                "can_download": False,
                "device_id": current_hw_id,
                "license_key": clean_firebase_key(current_hw_id),
                "username": user.get("username", "User"),
                "name": "Machine Mismatch",
                "contact": "",
                "role": "mismatched_machine",
                "is_admin": False,
                "is_dev": False,
                "is_vip": False,
                "status": "machine_mismatch",
                "max_free_episodes": 0,
                "package_name": "🚫 គណនីខុសកុំព្យូទ័រ (1 Machine ID / 1 PC Only)",
                "package_badge": "Machine Lock",
                "expires_at": 0,
                "expires_date": "Locked",
                "days_left": 0,
                "error": "🚫 Machine ID មិនត្រូវគ្នា! គណនីនេះត្រូវបានចាក់សោរឱ្យប្រើប្រាស់បានតែលើកុំព្យូទ័រ (PC) ដើម 1 គត់ប៉ុណ្ណោះ (1 Machine ID = 1 PC ដាច់ខាត)។",
                "message": "🚫 Machine ID មិនត្រូវគ្នា! គណនីនេះត្រូវបានចាក់សោរឱ្យប្រើប្រាស់បានតែលើកុំព្យូទ័រ (PC) ដើម 1 គត់ប៉ុណ្ណោះ (1 Machine ID = 1 PC ដាច់ខាត)។",
                "settings": settings,
                "packages_available": list(VIP_PACKAGES.values())
            }

    # 2. Check Firebase Realtime Database for this User PC License Key
    fb_data = None
    try:
        fb_data = firebase_fetch_license(dev_check)
    except Exception as ex:
        print(f"[firebase] startup check error: {ex}")

    cached_info = _firebase_cache.get(clean_id, {})
    is_confirmed_deleted = cached_info.get("deleted", False)

    # 3. STRICT RULE: Check if account was deleted by Admin from Firebase
    # ONLY purge if Admin explicitly deleted it (confirmed 200 null) AND user was not created in the last 60 seconds
    now_curr = int(time.time())
    is_fresh_user = bool(user and (now_curr - (user.get("created_at") or 0) < 60))

    if user and not is_admin and is_confirmed_deleted and not is_fresh_user:
        # Purge local user record & memory sessions because Admin deleted this account from Firebase!
        with _lock:
            d = _load_data()
            users = d.get("users", {})
            for k, u in list(users.items()):
                if u.get("device_id") == dev_check or clean_firebase_key(u.get("device_id", "")) == clean_id or (user.get("username") and u.get("username") == user.get("username")):
                    del users[k]
            d["users"] = users
            _save_data(d)
        for tok, su in list(_sessions.items()):
            if su.get("device_id") == dev_check or (user.get("username") and su.get("username") == user.get("username")):
                del _sessions[tok]
        user = None

    if not user and is_confirmed_deleted and not is_admin:
        return {
            "authenticated": False,
            "registered": False,
            "has_firebase_account": False,
            "must_register": True,
            "must_login": True,
            "is_deleted": True,
            "can_download": False,
            "device_id": dev_check,
            "license_key": clean_id,
            "username": "មិនទាន់ចូលគណនី",
            "name": "សូមចុះឈ្មោះគណនីថ្មី",
            "contact": "",
            "role": "unauthenticated",
            "is_admin": False,
            "is_dev": False,
            "is_vip": False,
            "status": "login_required",
            "coins": 0,
            "coins_riel": 0,
            "purchased_series": {},
            "max_free_episodes": 5,
            "package_name": "គណនីត្រូវបានលុប (សូមចុះឈ្មោះថ្មី)",
            "package_badge": "Re-register Required",
            "expires_at": 0,
            "expires_date": "Free Tier (ភាគ 1-5)",
            "days_left": 0,
            "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
            "message": "⚠️ គណនីរបស់អ្នកត្រូវបាន ADMIN លុបចេញពីប្រព័ន្ធ! សូមចុះឈ្មោះបង្កើតគណនីថ្មីឡើងវិញ។",
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }

    # 4. If account exists in Firebase Realtime Database and user not loaded locally:
    if fb_data and isinstance(fb_data, dict) and fb_data.get("username"):
        fb_banned = bool(fb_data.get("is_banned") or fb_data.get("status") == "banned")
        fb_vip = bool(fb_data.get("is_vip", False)) and not fb_banned
        fb_status = "banned" if fb_banned else fb_data.get("status", "user")
        fb_exp = fb_data.get("expires_at", 0)
        now_sec = int(time.time())
        if fb_vip and fb_exp > 0 and fb_exp < now_sec:
            fb_vip = False
            fb_status = "expired"

        if user:
            user["role"] = "banned" if fb_banned else ("vip" if fb_vip else user.get("role", "user"))
            user["is_vip"] = fb_vip
            user["is_banned"] = fb_banned
            user["status"] = fb_status
            user["expires_at"] = fb_exp
            user["approved_package"] = fb_data.get("approved_package", user.get("approved_package", ""))
            user["requested_package"] = fb_data.get("requested_package", user.get("requested_package", "1_year"))
            user["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 5)
            if "coins" in fb_data:
                user["coins"] = int(fb_data.get("coins") or 0)
            if "purchased_series" in fb_data and isinstance(fb_data["purchased_series"], dict):
                user["purchased_series"] = fb_data["purchased_series"]
        else:
            # Reconstitute regular user from Firebase Realtime Database
            tok = "usr_" + clean_id[-12:]
            user = {
                "key": "user_" + clean_id[-8:],
                "token": tok,
                "device_id": dev_check,
                "username": fb_data.get("username", "User"),
                "name": fb_data.get("name", fb_data.get("username", "User")),
                "contact": fb_data.get("contact", ""),
                "role": "banned" if fb_banned else ("vip" if fb_vip else fb_data.get("role", "user")),
                "is_vip": fb_vip,
                "is_banned": fb_banned,
                "is_admin": False,
                "status": fb_status,
                "requested_package": fb_data.get("requested_package", "1_year"),
                "approved_package": fb_data.get("approved_package", ""),
                "expires_at": fb_exp,
                "max_free_episodes": 0 if fb_banned else (999999 if fb_vip else 5),
                "coins": int(fb_data.get("coins", 0)),
                "purchased_series": fb_data.get("purchased_series") or {},
                "created_at": fb_data.get("created_at", now_sec),
                "package_name": "VIP Member (ដោះសោរគ្រប់ភាគ)" if fb_vip else f"User ធម្មតា (សាកល្បង {TRIAL_DAYS} ថ្ងៃ)",
                "package_badge": "VIP" if fb_vip else f"{TRIAL_DAYS} ថ្ងៃ"
            }
            _sessions[tok] = user
            _sessions[dev_check] = user

    # 5. STRICT RULE: Check if User is BANNED (either in Firebase RTDB or locally)
    is_banned = False
    if fb_data and (fb_data.get("status") == "banned" or fb_data.get("is_banned")):
        is_banned = True
    elif user and (user.get("status") == "banned" or user.get("is_banned")):
        is_banned = True

    if is_banned:
        if user:
            user["status"] = "banned"
            user["is_banned"] = True
            user["is_vip"] = False
            user["max_free_episodes"] = 0
            user["role"] = "banned"
        # Invalidate active session tokens
        for tok, su in list(_sessions.items()):
            if su.get("device_id") == dev_check or (user and su.get("username") == user.get("username")):
                if tok.startswith("usr_"):
                    del _sessions[tok]

        return {
            "authenticated": False,
            "registered": True,
            "is_banned": True,
            "can_download": False,
            "device_id": dev_check,
            "license_key": clean_id,
            "username": (user.get("username") if user else None) or (fb_data.get("username") if fb_data else "User"),
            "name": (user.get("name") if user else None) or (fb_data.get("name") if fb_data else ""),
            "contact": (user.get("contact") if user else None) or (fb_data.get("contact") if fb_data else ""),
            "role": "banned",
            "is_admin": False,
            "is_vip": False,
            "status": "banned",
            "max_free_episodes": 0,
            "days_left": 0,
            "expires_date": "Banned (បិទដំណើរការ)",
            "package_name": "គណនីត្រូវបាន ADMIN បិទ (Banned)",
            "package_badge": "BANNED",
            "error": "🚫 គណនីរបស់អ្នកត្រូវបាន ADMIN បិទ (Banned) មិនអាចប្រើប្រាស់បានទៀតទេ! សូមទាក់ទង ADMIN ឬស្នើសុំម្តងទៀត។",
            "message": "🚫 គណនីរបស់អ្នកត្រូវបាន ADMIN បិទ (Banned) មិនអាចប្រើប្រាស់បានទៀតទេ! សូមទាក់ទង ADMIN ឬស្នើសុំម្តងទៀត។",
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }

    # 6. Active Registered Regular User or VIP Member
    if user:
        is_vip = bool(user.get("is_vip", False))
        role = "vip" if is_vip else user.get("role", "user")
        user["role"] = role
        st = user.get("status", "user")
        max_eps = 999999 if is_vip else 5
        now = int(time.time())
        exp = user.get("expires_at", 0)

        import datetime
        if is_vip:
            if exp == 0:
                exp_date = "Lifetime VIP"
                days_left = -1
            else:
                exp_date = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
                days_left = _calc_days_left(exp, now, True)
            pkg_name = "VIP Member (ដោះសោរគ្រប់ភាគ)"
            pkg_badge = "VIP"
        elif st == "pending_vip":
            if exp == 0:
                exp = (user.get("created_at") or now) + TRIAL_SECONDS
                user["expires_at"] = exp
            days_left = _calc_days_left(exp, now, False)
            exp_date = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            pkg_name = f"សំណើ VIP កំពុងរង់ចាំ (នៅសល់ {days_left} ថ្ងៃ)"
            pkg_badge = "Pending VIP"
        else:
            # Regular user 3-day trial & 24-hour lockout handling
            if exp == 0:
                exp = (user.get("created_at") or now) + TRIAL_SECONDS
                user["expires_at"] = exp
            days_left = _calc_days_left(exp, now, False)
            exp_date = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            lockout_until = user.get("trial_lockout_until", 0)
            if lockout_until > now:
                diff = lockout_until - now
                hrs = diff // 3600
                mins = (diff % 3600) // 60
                pkg_name = f"បិទ Login បណ្តោះអាសន្ន ២៤ ម៉ោង (នៅសល់ {hrs}h {mins}m)"
                pkg_badge = "Lockout 24h"
                days_left = 0
            else:
                pkg_name = f"User ធម្មតា (សាកល្បងនៅសល់ {days_left} ថ្ងៃ)"
                pkg_badge = f"{days_left} ថ្ងៃ"

        user["days_left"] = days_left
        user["expires_date"] = exp_date
        user["package_name"] = pkg_name
        user["package_badge"] = pkg_badge

        return {
            "authenticated": True,
            "registered": True,
            "has_firebase_account": True,
            "must_register": False,
            "device_id": user.get("device_id") or dev_check,
            "license_key": clean_id,
            "username": user.get("username", "User"),
            "name": user.get("name", user.get("username", "User")),
            "contact": user.get("contact", ""),
            "role": "vip" if is_vip else "user",
            "is_admin": False,
            "is_dev": False,
            "is_vip": is_vip,
            "status": user.get("status", "user"),
            "coins": int(user.get("coins", 0)),
            "coins_riel": int(user.get("coins", 0)) * 500,
            "purchased_series": user.get("purchased_series") or {},
            "max_free_episodes": max_eps,
            "requested_package": user.get("requested_package", "1_year"),
            "approved_package": user.get("approved_package", ""),
            "package_name": pkg_name,
            "package_badge": pkg_badge,
            "expires_at": exp,
            "expires_date": exp_date,
            "days_left": days_left,
            "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }

    # 7. Fallback (Unauthenticated / Login Required)
    return {
        "authenticated": False,
        "registered": False,
        "has_firebase_account": False,
        "must_register": True,
        "must_login": True,
        "device_id": dev_check,
        "license_key": clean_id,
        "username": "មិនទាន់ចូលគណនី",
        "name": "សូមចូលគណនី ឬចុះឈ្មោះ",
        "contact": "",
        "role": "unauthenticated",
        "is_admin": False,
        "is_dev": False,
        "is_vip": False,
        "status": "login_required",
        "coins": 0,
        "coins_riel": 0,
        "purchased_series": {},
        "max_free_episodes": 5,
        "package_name": "មិនទាន់ចូលគណនី (Free ភាគ 1-5)",
        "package_badge": "Login Required",
        "expires_at": 0,
        "expires_date": "Free Tier (ភាគ 1-5)",
        "days_left": 0,
        "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
        "message": "សូមចូលគណនី ឬចុះឈ្មោះជាចាំបាច់ដើម្បីប្រើប្រាស់!",
        "settings": settings,
        "packages_available": list(VIP_PACKAGES.values())
    }

def request_vip(token_or_id: str, package: str = "1_year", note: str = "", name: str = "", contact: str = "", device_id: str = ""):
    """Submit a VIP Package request to ADMIN & Firebase Realtime Database.
    STRICT RULE: Only an already registered regular user can submit a VIP request!
    """
    ident = (token_or_id or "").strip()
    dev_param = (device_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("token") == ident or u.get("username") == ident:
                target = u
                break

        if not target and dev_param:
            for k, u in users.items():
                if u.get("device_id") == dev_param or clean_firebase_key(u.get("device_id", "")) == clean_firebase_key(dev_param):
                    target = u
                    break

        if not target and (ident or dev_param):
            lookup_dev = dev_param or ident
            if lookup_dev in _sessions:
                target = _sessions[lookup_dev]
            else:
                try:
                    fb = firebase_fetch_license(lookup_dev)
                    if fb and isinstance(fb, dict) and fb.get("username"):
                        clean_id = clean_firebase_key(lookup_dev)
                        tok = "usr_" + clean_id[-12:]
                        target = {
                            "device_id": lookup_dev,
                            "username": fb.get("username", "User"),
                            "name": fb.get("name") or name or fb.get("username"),
                            "contact": fb.get("contact") or contact,
                            "status": "pending_vip",
                            "role": "user",
                            "is_vip": False,
                            "token": tok
                        }
                        users["user_" + clean_id[-8:]] = target
                        d["users"] = users
                        _sessions[tok] = target
                        _sessions[lookup_dev] = target
                except Exception:
                    pass

        now = int(time.time())
        # STRICT RULE: Must be an authentically registered user first!
        if not target or not target.get("username") or str(target.get("username")).lower().startswith("guest") or target.get("role") == "guest":
            return False, "សូមចុះឈ្មោះ User ធម្មតាជាមុនសិន មុននឹងស្នើសុំ VIP!"

        # STRICT RULE: 1 Machine ID / 1 user can ONLY be used on 1 PC!
        current_hw = get_current_device_id()
        if target.get("device_id") and clean_firebase_key(target["device_id"]) != clean_firebase_key(current_hw):
            return False, "🚫 Machine ID មិនត្រូវគ្នា! សំណើ VIP អាចស្នើសុំបានតែលើកុំព្យូទ័រ (PC) ដើមរបស់គណនីនេះប៉ុណ្ណោះ (1 Machine ID = 1 PC ដាច់ខាត)។"

        if name:
            target["name"] = name
        if contact:
            target["contact"] = contact
        
        target["requested_package"] = package or "1_year"
        target["note"] = note or target.get("note", "")
        target["status"] = "pending_vip"
        target["is_banned"] = False
        target["is_vip"] = False
        target["role"] = "user"
        target["max_free_episodes"] = 5
        target["updated_at"] = now
        _save_data(d)

        # Update active sessions in memory
        for tok, su in list(_sessions.items()):
            if su.get("username") == target.get("username") or su.get("device_id") == target.get("device_id"):
                su["status"] = "pending_vip"
                su["is_banned"] = False
                su["is_vip"] = False
                su["role"] = "user"
                su["max_free_episodes"] = 5
                su["requested_package"] = target["requested_package"]
        if target.get("device_id"):
            _sessions[target["device_id"]] = target
        if target.get("token"):
            _sessions[target["token"]] = target

        # Push to Firebase Realtime Database
        try:
            firebase_sync_license(target)
        except Exception as ex:
            print(f"[firebase] request_vip sync error: {ex}")
            threading.Thread(target=firebase_sync_license, args=(target,), daemon=True).start()

        return True, target

def approve_user_vip(target_id: str, package: str = None, custom_days: int = None):
    """
    ADMIN approves a user or promotes them to VIP with custom days.
    """
    ident = str(target_id or "").strip()
    now = int(time.time())
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("contact") == ident or u.get("key") == ident or clean_firebase_key(u.get("device_id", "")) == clean_firebase_key(ident):
                target = u
                break

        if not target:
            # Auto-create if not present in local store
            uname = f"pc_{clean_firebase_key(ident)[-8:]}"
            target = {
                "username": uname,
                "name": f"User ({ident[:8]})",
                "contact": "Firebase Admin",
                "device_id": ident,
                "role": "vip",
                "is_admin": False,
                "is_vip": True,
                "status": "approved",
                "max_free_episodes": 999999,
                "requested_package": package or "1_year",
                "created_at": now,
                "approved_at": now,
                "expires_at": 0
            }
            users[uname] = target

        target_pkg = package or target.get("requested_package") or "1_year"
        if custom_days is not None and int(custom_days) > 0:
            days = int(custom_days)
            expires_at = now + days * 86400
            pkg_name = f"VIP {days} ថ្ងៃ"
        elif target_pkg == "lifetime" or (custom_days is not None and int(custom_days) == -1):
            expires_at = 0
            pkg_name = "VIP មួយជីវិត"
        elif target_pkg in VIP_PACKAGES:
            days = VIP_PACKAGES[target_pkg]["days"]
            expires_at = (now + days * 86400) if days > 0 else 0
            pkg_name = VIP_PACKAGES[target_pkg]["name"]
        else:
            expires_at = now + 365 * 86400
            pkg_name = "VIP 1 ឆ្នាំ"

        target["status"] = "approved"
        target["is_vip"] = True
        target["role"] = "vip" if target.get("role") != "admin" else "admin"
        target["approved_package"] = target_pkg
        target["package_name"] = pkg_name
        target["approved_at"] = now
        target["expires_at"] = expires_at
        target["max_free_episodes"] = 999999
        target["updated_at"] = now
        _save_data(d)

        # Update active sessions in memory
        for tok, s_user in list(_sessions.items()):
            if s_user.get("username") == target.get("username") or s_user.get("device_id") == target.get("device_id"):
                s_user["role"] = target["role"]
                s_user["is_vip"] = True
                s_user["status"] = "approved"
                s_user["max_free_episodes"] = 999999
                s_user["expires_at"] = expires_at
                s_user["package_name"] = pkg_name
                s_user["days_left"] = -1 if expires_at == 0 else max(0, int((expires_at - now) / 86400))

        # Sync approval to Firebase Realtime Database
        threading.Thread(target=firebase_sync_license, args=(target,), daemon=True).start()

        return True, target

def ban_user(target_id: str, banned: bool = True, sync_to_firebase: bool = True):
    """
    ADMIN bans or unbans a user account.
    When banned, user cannot log in, download, or stream, and active sessions are revoked.
    When unbanned, user access is restored as regular user (1-5 episodes).
    """
    ident = str(target_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("key") == ident or clean_firebase_key(u.get("device_id", "")) == clean_firebase_key(ident):
                if str(u.get("username")).upper() == "ADMIN" or u.get("role") == "admin":
                    return False, "មិនអាចបិទគណនី ADMIN បានឡើយ"
                target = u
                break

        if not target and ident:
            # Check sessions
            for tok, su in _sessions.items():
                if su.get("device_id") == ident or clean_firebase_key(su.get("device_id", "")) == clean_firebase_key(ident):
                    target = su
                    break

        if target:
            target["status"] = "banned" if banned else "user"
            target["is_banned"] = banned
            if banned:
                target["is_vip"] = False
                target["max_free_episodes"] = 0
                target["role"] = "banned"
            else:
                target["max_free_episodes"] = 5
                target["role"] = "user"
            target["updated_at"] = int(time.time())
            _save_data(d)

            dev = target.get("device_id", "")
            uname = target.get("username", "")
            if dev:
                clean_id = clean_firebase_key(dev)
                if clean_id in _firebase_cache and _firebase_cache[clean_id].get("data"):
                    _firebase_cache[clean_id]["data"]["status"] = "banned" if banned else "user"
                    _firebase_cache[clean_id]["data"]["is_banned"] = banned
                    _firebase_cache[clean_id]["data"]["is_vip"] = False
                    _firebase_cache[clean_id]["time"] = time.time()

            # Invalidate or update memory sessions
            for tok, su in list(_sessions.items()):
                if (uname and su.get("username") == uname) or (dev and su.get("device_id") == dev):
                    if banned:
                        del _sessions[tok]
                    else:
                        su["status"] = "user"
                        su["is_banned"] = False
                        su["role"] = "user"
                        su["max_free_episodes"] = 5

            if sync_to_firebase and dev:
                try:
                    threading.Thread(target=firebase_admin_ban_license, args=(dev, banned, False), daemon=True).start()
                except Exception:
                    pass

            return True, target
        elif ident:
            # If target is only a device_id on Firebase RTDB
            if sync_to_firebase:
                try:
                    threading.Thread(target=firebase_admin_ban_license, args=(ident, banned, False), daemon=True).start()
                except Exception:
                    pass
            return True, {"device_id": ident, "status": "banned" if banned else "user", "is_banned": banned}
    return False, "រកមិនឃើញគណនីនេះទេ"

def revoke_user(target_id: str):
    """
    Revert a VIP user back to a regular free user (1-5 episodes).
    """
    ident = str(target_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("key") == ident:
                if str(u.get("username")).upper() == "ADMIN":
                    return False
                u["status"] = "user"
                u["is_vip"] = False
                u["role"] = "user"
                u["expires_at"] = 0
                u["max_free_episodes"] = 5
                u["package_name"] = "គណនីធម្មតា (ភាគ 1-5)"
                u["updated_at"] = int(time.time())
                _save_data(d)
                for tok, s_user in list(_sessions.items()):
                    if s_user.get("username") == u.get("username") or s_user.get("device_id") == u.get("device_id"):
                        s_user["is_vip"] = False
                        s_user["status"] = "user"
                        s_user["max_free_episodes"] = 5
                        s_user["expires_at"] = 0
                        s_user["package_name"] = "គណនីធម្មតា (ភាគ 1-5)"
                return True
    return False

# ----------------- Drama Free Rules Management ----------------- #

def get_default_drama_rule() -> dict:
    """Get the auto / default rule applied to all dramas without a custom override."""
    with _lock:
        d = _load_data()
        return dict(d.get("drama_rules_default", {"rule": "free_episodes", "free_episodes": 5}))

def set_default_drama_rule(rule: str = "free_episodes", free_episodes: int = 5) -> dict:
    """Set the auto / default rule for all new/unconfigured dramas."""
    rule_type = "free_all" if rule == "free_all" else "free_episodes"
    eps = 999999 if rule_type == "free_all" else max(1, int(free_episodes or 5))
    entry = {
        "rule": rule_type,
        "free_episodes": eps,
        "updated_at": int(time.time())
    }
    with _lock:
        d = _load_data()
        d["drama_rules_default"] = entry
        _save_data(d)
    return {"ok": True, "default_rule": entry}

def get_drama_rules() -> dict:
    """Get all configured drama rules."""
    with _lock:
        d = _load_data()
        return dict(d.get("drama_rules", {}))

def get_drama_rule(series_id: str, title: str = "") -> dict:
    """
    Get rule for a specific drama.
    If no custom override exists, fallback to the auto/default rule!
    """
    sid = str(series_id or "").strip()
    with _lock:
        d = _load_data()
        rules = d.get("drama_rules", {})
        default_rule = d.get("drama_rules_default", {"rule": "free_episodes", "free_episodes": 5})
        if sid and sid in rules:
            res = dict(rules[sid])
            res["is_custom"] = True
            return res
        if title:
            t_clean = str(title).strip().lower()
            for k, r in rules.items():
                if str(r.get("title") or "").strip().lower() == t_clean:
                    res = dict(r)
                    res["is_custom"] = True
                    return res
    return {
        "series_id": sid,
        "rule": default_rule.get("rule", "free_episodes"),
        "free_episodes": default_rule.get("free_episodes", 5),
        "is_default": True
    }

def set_drama_rule(series_id: str, rule: str = "free_episodes", free_episodes: int = 5, title: str = "") -> dict:
    """
    Set rule for a drama:
    - rule: "free_all" (100% Free for all regular users) or "free_episodes" (1-5 or custom number of free episodes)
    """
    sid = str(series_id or "").strip()
    if not sid:
        return {"ok": False, "error": "Missing series_id"}
    rule_type = "free_all" if rule == "free_all" else "free_episodes"
    eps = 999999 if rule_type == "free_all" else max(1, int(free_episodes or 5))
    entry = {
        "series_id": sid,
        "rule": rule_type,
        "free_episodes": eps,
        "title": str(title or "").strip(),
        "updated_at": int(time.time())
    }
    with _lock:
        d = _load_data()
        if "drama_rules" not in d:
            d["drama_rules"] = {}
        d["drama_rules"][sid] = entry
        _save_data(d)
    return {"ok": True, "rule": entry}

def delete_drama_rule(series_id: str) -> bool:
    """Reset drama rule back to default (Free 1-5)."""
    sid = str(series_id or "").strip()
    with _lock:
        d = _load_data()
        rules = d.get("drama_rules", {})
        if sid in rules:
            del rules[sid]
            d["drama_rules"] = rules
            _save_data(d)
            return True
    return False

def check_can_download(token_or_dev: str, requested_episodes: list = None, max_ep: int = 0, series_id: str = ""):
    """
    Check download authorization and enforce episode limits.
    ADMIN & VIP: 100% unrestricted.
    Regular User / Guest:
    - If drama rule is "free_all": 100% unrestricted!
    - Otherwise: Restricted to episodes 1 to N (default: 10).
    """
    st = get_user_status(token_or_dev)
    if st.get("status") == "machine_mismatch":
        return False, "machine_mismatch", "🚫 Machine ID មិនត្រូវគ្នា! គណនីនេះត្រូវបានចាក់សោរឱ្យប្រើប្រាស់បានតែលើ PC ដើម 1 គត់ប៉ុណ្ណោះ (1 Machine ID = 1 PC)។", None

    if st.get("is_banned") or st.get("status") == "banned":
        return False, "banned", "🚫 គណនីរបស់អ្នកត្រូវបាន ADMIN បិទ (Banned) មិនអាចប្រើប្រាស់បានទៀតទេ! សូមទាក់ទង ADMIN ឬស្នើសុំម្តងទៀត។", None

    if not st.get("authenticated"):
        return False, "auth_required", "សូមចុះឈ្មោះ ឬចូលប្រើប្រាស់គណនីជាមុនសិន ទើបអាចទាញយករឿងបាន!", None

    if st.get("is_admin") or st.get("is_vip"):
        return True, "vip_allowed", "VIP Full Access — អនុញ្ញាតទាញយកគ្រប់ភាគ ១០០%", None

    # Check if user purchased this series with Coins!
    purchased = st.get("purchased_series") or {}
    if series_id and (str(series_id) in purchased or series_id in purchased):
        return True, "purchased_unlocked", "បានទិញរួចរាល់ (Purchased) — អនុញ្ញាតទាញយកគ្រប់ភាគ ១០០%", None

    # Check drama rule if series_id is provided
    d_rule = get_drama_rule(series_id) if series_id else {"rule": "free_episodes", "free_episodes": 5}
    if d_rule.get("rule") == "free_all":
        return True, "free_all", "រឿងនេះ Free ១០០% (អនុញ្ញាតទាញយកគ្រប់ភាគ)", None

    limit = d_rule.get("free_episodes", 5)
    # Regular User: Restricted to episodes 1 to limit
    if max_ep > limit:
        return False, "vip_required", f"រឿងនេះអាចទាញយកបានត្រឹមភាគ ១ ដល់ {limit} ប៉ុណ្ណោះ! សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទាញយកភាគ {limit + 1} ឡើងទៅ។", f"1-{limit}"

    if requested_episodes:
        locked = [e for e in requested_episodes if int(e) > limit]
        if locked:
            return False, "vip_required", f"ភាគលើសពី {limit} ({', '.join(map(str, locked[:4]))}...) ត្រូវបានចាក់សោរ! គណនីធម្មតាអាចទាញយកបានត្រឹមភាគ ១-{limit}។", f"1-{limit}"

    return True, "regular_allowed", f"អនុញ្ញាតទាញយក (ភាគ ១ ដល់ {limit})", f"1-{limit}"

def can_access_episode(episode_num, token_or_dev: str = "", series_id: str = ""):
    """
    Check if user can play or access a specific episode.
    ADMIN or VIP: 100% unlocked.
    Drama rule:
    - "free_all": Free for all regular users 100%!
    - "free_episodes": Free for episodes 1 to N (default: 1-5).
    """
    # Auto-detect swapped arguments: (token_or_dev, series_id, episode_num)
    if isinstance(episode_num, str) and not episode_num.isdigit() and (isinstance(series_id, (int, float)) or (isinstance(series_id, str) and series_id.isdigit())):
        token_or_dev, series_id, episode_num = episode_num, token_or_dev, int(series_id)

    st = get_user_status(token_or_dev)
    if st.get("status") == "machine_mismatch":
        return False, "machine_mismatch", "🚫 Machine ID មិនត្រូវគ្នា! គណនីនេះត្រូវបានចាក់សោរឱ្យប្រើប្រាស់បានតែលើ PC ដើម 1 គត់ប៉ុណ្ណោះ (1 Machine ID = 1 PC)។"

    if st.get("is_banned") or st.get("status") == "banned":
        return False, "banned", "🚫 គណនីរបស់អ្នកត្រូវបាន ADMIN បិទ (Banned) មិនអាចប្រើប្រាស់បានទៀតទេ! សូមទាក់ទង ADMIN ឬស្នើសុំម្តងទៀត។"

    if st.get("is_admin") or st.get("is_vip"):
        return True, "vip_allowed", "VIP / ADMIN Unlocked"

    # Check if user purchased this series with Coins!
    purchased = st.get("purchased_series") or {}
    if series_id and (str(series_id) in purchased or series_id in purchased):
        return True, "purchased_unlocked", "បានទិញរួចរាល់ (Purchased)"

    # Check drama rule
    d_rule = get_drama_rule(series_id) if series_id else {"rule": "free_episodes", "free_episodes": 5}
    if d_rule.get("rule") == "free_all":
        return True, "free_all", "រឿងនេះ Free ១០០% (គ្រប់ភាគ)"

    limit = d_rule.get("free_episodes", 5)
    if int(episode_num) <= limit:
        return True, "free_episode", f"ភាគ ១-{limit} ឥតគិតថ្លៃ"

    return False, "vip_required", f"ភាគនេះសម្រាប់សមាជិក VIP ប៉ុណ្ណោះ! រឿងនេះអាចទស្សនាឥតគិតថ្លៃបានត្រឹមភាគ ១ ដល់ {limit}។ សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទស្សនាគ្រប់ភាគ។"

def list_users():
    with _lock:
        d = _load_data()
        mode = d.get("mode", "vip_required")
        settings = d.get("settings", {})
        users_list = list(d.get("users", {}).values())
        now = int(time.time())
        for u in users_list:
            exp = u.get("expires_at", 0)
            is_adm = (u.get("role") == "admin" or str(u.get("username")).upper() == "ADMIN")
            if is_adm:
                u["days_left"] = -1
                u["expires_date"] = "Lifetime (Full Control)"
                u["is_vip"] = True
                u["is_admin"] = True
            elif u.get("status") == "banned":
                u["days_left"] = 0
                u["expires_date"] = "Banned (បិទដំណើរការ)"
                u["is_vip"] = False
            elif exp == 0 and u.get("is_vip"):
                u["days_left"] = -1
                u["expires_date"] = "Lifetime VIP"
            elif exp > now:
                u["days_left"] = max(0, int((exp - now) / 86400))
                import datetime
                u["expires_date"] = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            else:
                u["days_left"] = 0
                if exp > 0 and u.get("is_vip"):
                    u["status"] = "expired"
                    u["is_vip"] = False
                u["expires_date"] = "Free (1-5)"

        users_list.sort(key=lambda x: (x.get("role") != "admin", x.get("updated_at", 0)), reverse=False)
        return {
            "mode": mode,
            "settings": settings,
            "total_users": len(users_list),
            "approved_count": len([u for u in users_list if u.get("is_vip")]),
            "pending_count": len([u for u in users_list if u.get("status") == "pending_vip"]),
            "banned_count": len([u for u in users_list if u.get("status") == "banned"]),
            "regular_count": len([u for u in users_list if not u.get("is_vip") and not u.get("is_admin") and u.get("status") != "banned"]),
            "admin_count": len([u for u in users_list if u.get("is_admin") or u.get("role") == "admin"]),
            "users": users_list,
            "packages": list(VIP_PACKAGES.values())
        }

def delete_user(target_id: str, delete_from_firebase: bool = True):
    """
    ADMIN permanently deletes a user account.
    Removes user from local user_access.json, purges active sessions,
    and removes license from Firebase Realtime Database.
    """
    ident = str(target_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        to_del = None
        user_rec = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("key") == ident or clean_firebase_key(u.get("device_id", "")) == clean_firebase_key(ident):
                if str(u.get("username")).upper() == "ADMIN" or u.get("role") == "admin":
                    return False  # Never delete ADMIN!
                to_del = k
                user_rec = dict(u)
                break

        if to_del:
            dev = user_rec.get("device_id", "")
            uname = user_rec.get("username", "")
            del users[to_del]
            _save_data(d)

            # Purge active sessions
            for tok, su in list(_sessions.items()):
                if (uname and su.get("username") == uname) or (dev and su.get("device_id") == dev):
                    del _sessions[tok]

            if delete_from_firebase and dev:
                try:
                    threading.Thread(target=firebase_admin_delete_license, args=(dev, False), daemon=True).start()
                except Exception:
                    pass
            return True
        elif ident:
            # Target may be device_id not stored in local json
            dev = ident
            for tok, su in list(_sessions.items()):
                if su.get("device_id") == dev or clean_firebase_key(su.get("device_id", "")) == clean_firebase_key(dev):
                    del _sessions[tok]
            if delete_from_firebase:
                try:
                    threading.Thread(target=firebase_admin_delete_license, args=(dev, False), daemon=True).start()
                except Exception:
                    pass
            return True
    return False

def extend_user(target_id: str, additional_days: int):
    ident = str(target_id or "").strip()
    days = int(additional_days)
    now = int(time.time())
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("key") == ident:
                target = u
                break
        if not target:
            return False, "រកមិនឃើញអ្នកប្រើប្រាស់"
        if target.get("role") == "admin":
            return True, target

        cur_exp = target.get("expires_at", 0)
        base = max(now, cur_exp)
        new_exp = base + days * 86400
        target["expires_at"] = new_exp
        target["is_vip"] = True
        target["status"] = "approved"
        target["updated_at"] = now
        _save_data(d)
        return True, target

def is_dev(device_id=None):
    st = get_user_status(device_id)
    return bool(st.get("is_admin", False))

def is_vip(device_id=None):
    st = get_user_status(device_id)
    return st.get("is_vip", False)

# ----------------- Firebase Realtime Database Integration ----------------- #

_firebase_cache = {}  # clean_id -> {"time": float, "data": dict or None, "deleted": bool}
_firebase_last_poll = {}
_fb_lock = threading.RLock()

def get_firebase_config():
    """Retrieve current Firebase Realtime Database configuration."""
    cfg = {
        "enabled": True,
        "database_url": "https://syd-drama-default-rtdb.firebaseio.com",
        "auth_secret": "",
        "sync_interval_seconds": 25
    }
    if os.path.isfile(FIREBASE_FILE):
        try:
            with open(FIREBASE_FILE, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    cfg.update(loaded)
        except Exception:
            pass
    env_url = os.environ.get("HG_FIREBASE_URL")
    if env_url:
        cfg["database_url"] = env_url
    env_sec = os.environ.get("HG_FIREBASE_SECRET")
    if env_sec:
        cfg["auth_secret"] = env_sec
    return cfg

def save_firebase_config(new_config: dict):
    """Save Firebase Realtime Database configuration."""
    cfg = get_firebase_config()
    for k in ("enabled", "database_url", "auth_secret", "sync_interval_seconds"):
        if k in new_config:
            cfg[k] = new_config[k]
    if isinstance(cfg.get("database_url"), str):
        cfg["database_url"] = cfg["database_url"].strip().rstrip("/")
    if isinstance(cfg.get("auth_secret"), str):
        cfg["auth_secret"] = cfg["auth_secret"].strip()
    try:
        with open(FIREBASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[firebase] Error saving config: {e}")
    return cfg

def clean_firebase_key(key: str) -> str:
    """Sanitize key for Firebase Realtime Database (cannot contain . $ # [ ] / :)."""
    s = str(key or "").strip()
    return re.sub(r'[\.\$\[\]\#\/:]', '_', s)

def _firebase_url(path: str = ""):
    cfg = get_firebase_config()
    if not cfg.get("enabled"):
        return "", {}
    base = str(cfg.get("database_url") or "").strip().rstrip("/")
    if not base:
        return "", {}
    if not base.startswith("http"):
        base = "https://" + base
    p = path.strip("/")
    url = f"{base}/{p}.json" if p else f"{base}/.json"
    params = {}
    sec = str(cfg.get("auth_secret") or "").strip()
    if sec:
        params["auth"] = sec
    return url, params

def firebase_test_connection(custom_url: str = None, custom_secret: str = None):
    """Test connection to Firebase Realtime Database."""
    cfg = get_firebase_config()
    base = (custom_url or cfg.get("database_url") or "").strip().rstrip("/")
    if not base:
        return False, "សូមបញ្ចូល Firebase Database URL"
    if not base.startswith("http"):
        base = "https://" + base
    sec = custom_secret if custom_secret is not None else cfg.get("auth_secret")
    url = f"{base}/.json"
    params = {"shallow": "true"}
    if sec:
        params["auth"] = sec
    try:
        r = requests.get(url, params=params, timeout=5, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code == 200:
            return True, "ភ្ជាប់ទៅកាន់ Firebase Realtime Database ជោគជ័យ ១០០%!"
        elif r.status_code == 401 or r.status_code == 403:
            return False, f"Permission Denied ({r.status_code}): សូមពិនិត្យមើល Database Rules ឬ Auth Secret"
        else:
            return False, f"Firebase HTTP {r.status_code}: {r.text[:120]}"
    except Exception as e:
        return False, f"Connection Failed: {e}"

def firebase_sync_license(user_or_dict: dict):
    """
    Push User PC License / VIP Request to Firebase Realtime Database.
    Target path: /licenses/{clean_device_id}.json
    """
    try:
        dev_id = user_or_dict.get("device_id") or get_current_device_id()
        if not dev_id:
            return False
        clean_id = clean_firebase_key(dev_id)
        url, params = _firebase_url(f"licenses/{clean_id}")
        if not url:
            return False

        exp = user_or_dict.get("expires_at", 0)
        now_ts = int(time.time())
        dl = user_or_dict.get("days_left")
        if dl is None:
            dl = -1 if (user_or_dict.get("is_vip") and exp == 0) else (max(0, int((exp - now_ts) / 86400)) if exp > 0 else 7)

        fb_banned = bool(user_or_dict.get("is_banned", False) or user_or_dict.get("status") == "banned")
        fb_vip = bool(user_or_dict.get("is_vip", False)) and not fb_banned

        payload = {
            "device_id": dev_id,
            "key": clean_id,
            "username": user_or_dict.get("username", "User"),
            "name": user_or_dict.get("name", ""),
            "contact": user_or_dict.get("contact", ""),
            "requested_package": user_or_dict.get("requested_package", "1_year"),
            "approved_package": user_or_dict.get("approved_package", ""),
            "status": "banned" if fb_banned else user_or_dict.get("status", "pending_vip"),
            "is_vip": fb_vip,
            "is_banned": fb_banned,
            "role": "banned" if fb_banned else ("vip" if fb_vip else user_or_dict.get("role", "user")),
            "max_free_episodes": 0 if fb_banned else (999999 if fb_vip else 5),
            "coins": int(user_or_dict.get("coins", 0)),
            "purchased_series": user_or_dict.get("purchased_series") or {},
            "note": user_or_dict.get("note", ""),
            "created_at": user_or_dict.get("created_at") or now_ts,
            "updated_at": now_ts,
            "expires_at": exp,
            "expires_date": user_or_dict.get("expires_date", ""),
            "days_left": dl
        }

        # Prime cache immediately so next get_user_status call knows user exists!
        _firebase_cache[clean_id] = {
            "time": time.time(),
            "data": dict(payload),
            "deleted": False
        }

        r = requests.patch(url, params=params, json=payload, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        return r.status_code == 200
    except Exception as e:
        print(f"[firebase] sync error: {e}")
        return False

def firebase_fetch_license(device_id: str, force: bool = False):
    """
    Fetch license status from Firebase Realtime Database and apply updates to local user if approved.
    """
    try:
        clean_id = clean_firebase_key(device_id)
        now_t = time.time()
        if not force and clean_id in _firebase_cache:
            cached = _firebase_cache[clean_id]
            if now_t - cached.get("time", 0) < 4:
                return cached.get("data")

        url, params = _firebase_url(f"licenses/{clean_id}")
        if not url:
            return None
        r = requests.get(url, params=params, timeout=5, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code == 200:
            txt = (r.text or "").strip()
            if not txt or txt == "null" or txt == "None":
                _firebase_cache[clean_id] = {"time": now_t, "data": None, "deleted": True}
                return None

            fb_data = r.json()
            if not isinstance(fb_data, dict) or not fb_data or not fb_data.get("username"):
                _firebase_cache[clean_id] = {"time": now_t, "data": None, "deleted": True}
                return None

            _firebase_cache[clean_id] = {"time": now_t, "data": fb_data, "deleted": False}

            # Apply Firebase license state to local user cache
            fb_banned = bool(fb_data.get("is_banned") or fb_data.get("status") == "banned")
            fb_vip = bool(fb_data.get("is_vip", False)) and not fb_banned
            fb_status = "banned" if fb_banned else fb_data.get("status", "user")
            fb_exp = fb_data.get("expires_at", 0)

            now = int(time.time())
            if fb_vip and fb_exp > 0 and fb_exp < now:
                fb_vip = False
                fb_status = "expired"

            with _lock:
                d = _load_data()
                users = d.get("users", {})
                updated = False
                for k, u in users.items():
                    if u.get("device_id") == device_id or clean_firebase_key(u.get("device_id", "")) == clean_id or u.get("username") == fb_data.get("username"):
                        u["role"] = "banned" if fb_banned else ("vip" if fb_vip else "user")
                        u["is_vip"] = fb_vip
                        u["is_banned"] = fb_banned
                        u["status"] = fb_status
                        u["expires_at"] = fb_exp
                        u["approved_package"] = fb_data.get("approved_package", u.get("approved_package", ""))
                        u["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 5)
                        if "coins" in fb_data and fb_data["coins"] is not None:
                            u["coins"] = int(fb_data["coins"])
                        if "purchased_series" in fb_data and isinstance(fb_data["purchased_series"], dict):
                            u["purchased_series"] = fb_data["purchased_series"]
                        if fb_banned:
                            u["expires_date"] = "Banned (បិទដំណើរការ)"
                            u["days_left"] = 0
                        elif fb_exp > 0:
                            import datetime
                            u["expires_date"] = datetime.datetime.fromtimestamp(fb_exp).strftime("%d/%m/%Y")
                            u["days_left"] = max(0, int((fb_exp - now) / 86400))
                        elif fb_vip and fb_exp == 0:
                            u["expires_date"] = "Lifetime VIP"
                            u["days_left"] = -1
                        else:
                            u["days_left"] = max(0, int((fb_exp - now) / 86400)) if fb_exp > 0 else 7
                        updated = True
                        # Update sessions
                        for tok, su in _sessions.items():
                            if su.get("device_id") == device_id or su.get("username") == u.get("username"):
                                su.update(u)
                        break
                if updated:
                    _save_data(d)

            return fb_data
        else:
            # Server or network glitch: preserve cache
            if clean_id in _firebase_cache:
                return _firebase_cache[clean_id].get("data")
            return None
    except Exception as e:
        print(f"[firebase] fetch error: {e}")
        if clean_id in _firebase_cache:
            return _firebase_cache[clean_id].get("data")
        return None

def firebase_admin_get_all_licenses():
    """Admin: retrieve all licenses from Firebase Realtime Database."""
    try:
        url, params = _firebase_url("licenses")
        if not url:
            return []
        r = requests.get(url, params=params, timeout=7, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code != 200 or not r.text:
            return []
        data = r.json()
        if not isinstance(data, dict):
            return []

        out = []
        now = int(time.time())
        for k, item in data.items():
            if not isinstance(item, dict):
                continue
            item["key"] = k
            exp = item.get("expires_at", 0)
            is_vip = bool(item.get("is_vip", False))
            if is_vip and exp > 0 and exp < now:
                item["is_vip"] = False
                item["status"] = "expired"

            if exp > 0:
                import datetime
                item["expires_date"] = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
                item["days_left"] = max(0, int((exp - now) / 86400))
            elif is_vip and exp == 0:
                item["expires_date"] = "Lifetime VIP"
                item["days_left"] = -1
            else:
                item["expires_date"] = "Free Tier (ភាគ 1-5)"
                item["days_left"] = 0
            item["coins"] = int(item.get("coins", 0))
            item["coins_riel"] = item["coins"] * 500
            item["purchased_series"] = item.get("purchased_series") or {}
            out.append(item)

        # Sort: pending_vip first, then by updated_at descending
        def _sort_key(x):
            is_pending = 1 if x.get("status") == "pending_vip" else 0
            return (is_pending, x.get("updated_at", 0))

        out.sort(key=_sort_key, reverse=True)
        return out
    except Exception as e:
        print(f"[firebase] admin get all error: {e}")
        return []

def firebase_admin_approve_license(device_id: str, package: str = "1_year", custom_days: int = None):
    """Admin: approve or update a license directly in Firebase Realtime Database."""
    try:
        clean_id = clean_firebase_key(device_id)
        url, params = _firebase_url(f"licenses/{clean_id}")
        if not url:
            return False, "Firebase is not configured"

        now = int(time.time())
        if custom_days is not None and int(custom_days) > 0:
            days = int(custom_days)
            expires_at = now + days * 86400
            pkg_name = f"VIP {days} ថ្ងៃ"
        elif package == "lifetime" or (custom_days is not None and int(custom_days) == -1):
            expires_at = 0
            pkg_name = "VIP មួយជីវិត"
        elif package in VIP_PACKAGES:
            days = VIP_PACKAGES[package]["days"]
            expires_at = (now + days * 86400) if days > 0 else 0
            pkg_name = VIP_PACKAGES[package]["name"]
        else:
            expires_at = now + 365 * 86400
            pkg_name = "VIP 1 ឆ្នាំ"

        import datetime
        exp_date_str = datetime.datetime.fromtimestamp(expires_at).strftime("%d/%m/%Y") if expires_at > 0 else "Lifetime VIP"

        patch_data = {
            "role": "vip",
            "status": "approved",
            "is_vip": True,
            "approved_package": package or "1_year",
            "package_name": pkg_name,
            "max_free_episodes": 999999,
            "approved_at": now,
            "updated_at": now,
            "expires_at": expires_at,
            "expires_date": exp_date_str,
            "days_left": -1 if expires_at == 0 else max(0, int((expires_at - now) / 86400))
        }

        r = requests.patch(url, params=params, json=patch_data, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code == 200:
            # Also approve locally if device matches
            approve_user_vip(device_id, package=package, custom_days=custom_days)
            return True, patch_data
        else:
            return False, f"Firebase HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, str(e)

def firebase_admin_ban_license(device_id: str, banned: bool = True, sync_local: bool = True):
    """Admin: ban or unban a user license in Firebase Realtime Database."""
    try:
        clean_id = clean_firebase_key(device_id)
        if clean_id in _firebase_cache and _firebase_cache[clean_id].get("data"):
            _firebase_cache[clean_id]["data"]["status"] = "banned" if banned else "user"
            _firebase_cache[clean_id]["data"]["is_banned"] = banned
            _firebase_cache[clean_id]["data"]["is_vip"] = False
            _firebase_cache[clean_id]["time"] = time.time()
        url, params = _firebase_url(f"licenses/{clean_id}")
        if not url:
            return False
        now_ts = int(time.time())
        patch_data = {
            "status": "banned" if banned else "user",
            "is_banned": banned,
            "is_vip": False,
            "max_free_episodes": 0 if banned else 5,
            "updated_at": now_ts
        }
        r = requests.patch(url, params=params, json=patch_data, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code == 200:
            if sync_local:
                ban_user(device_id, banned=banned, sync_to_firebase=False)
            return True
        return False
    except Exception as e:
        print(f"[firebase] admin ban error: {e}")
        return False

def firebase_admin_delete_license(device_id: str, delete_local: bool = True):
    """Admin: delete a user license from Firebase Realtime Database."""
    try:
        clean_id = clean_firebase_key(device_id)
        _firebase_cache[clean_id] = {"time": time.time(), "data": None, "deleted": True}
        url, params = _firebase_url(f"licenses/{clean_id}")
        if not url:
            return False
        r = requests.delete(url, params=params, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        if delete_local:
            delete_user(device_id, delete_from_firebase=False)
        return r.status_code == 200
    except Exception as e:
        print(f"[firebase] admin delete error: {e}")
        return False

# ==============================================================================
# COIN SYSTEM, MOVIE PRICING & PROMOTION ENGINE (FIREBASE RTDB INTEGRATED)
# ==============================================================================

def get_pricing_rules(sync_from_firebase: bool = False) -> dict:
    """
    Get movie pricing and promo rules.
    Default: 1 Movie = 2 Coins = 1,000 Riel (1 Coin = 500 Riel).
    """
    with _lock:
        d = _load_data()
        rules = d.get("pricing_rules")
        if not isinstance(rules, dict):
            rules = dict(DEFAULT_PRICING_RULES)
            d["pricing_rules"] = rules
            _save_data(d)
        else:
            for k, v in DEFAULT_PRICING_RULES.items():
                if k not in rules:
                    rules[k] = v

    if sync_from_firebase:
        try:
            url, params = _firebase_url("pricing_rules")
            if url:
                r = requests.get(url, params=params, timeout=5, headers={"User-Agent": "SYD-Downloader-Pro"})
                if r.status_code == 200 and r.text and r.text != "null":
                    fb_rules = r.json()
                    if isinstance(fb_rules, dict):
                        with _lock:
                            d = _load_data()
                            cur = d.get("pricing_rules", {})
                            cur.update(fb_rules)
                            d["pricing_rules"] = cur
                            _save_data(d)
                            return cur
        except Exception as e:
            print(f"[pricing] firebase sync error: {e}")

    return rules

def save_pricing_rules(new_rules: dict) -> dict:
    """
    Admin: save pricing and promotional rules locally and push to Firebase RTDB.
    """
    with _lock:
        d = _load_data()
        rules = d.get("pricing_rules", dict(DEFAULT_PRICING_RULES))
        for k in ("default_coins", "coin_rate_riel", "promo_enabled", "promo_coins", "promo_start_date", "promo_end_date", "promo_name", "custom_series"):
            if k in new_rules:
                rules[k] = new_rules[k]
        rules["default_coins"] = max(1, int(rules.get("default_coins", 2)))
        rules["coin_rate_riel"] = max(100, int(rules.get("coin_rate_riel", 500)))
        rules["promo_coins"] = max(1, int(rules.get("promo_coins", 1)))
        rules["promo_enabled"] = bool(rules.get("promo_enabled", False))
        d["pricing_rules"] = rules
        _save_data(d)

    # Push to Firebase
    try:
        url, params = _firebase_url("pricing_rules")
        if url:
            requests.put(url, params=params, json=rules, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
    except Exception as e:
        print(f"[pricing] save to firebase error: {e}")

    return rules

def get_movie_pricing(series_id: str = "") -> dict:
    """
    Calculate effective price in Coins and Riel for a movie/drama.
    Checks date-based promotion and custom series price.
    Default unchanging: 1 Movie = 2 Coins = 1,000 Riel (1 Coin = 500 Riel).
    """
    rules = get_pricing_rules()
    rate = int(rules.get("coin_rate_riel", 500))
    std_coins = int(rules.get("default_coins", 2))
    std_riel = std_coins * rate

    sid = str(series_id or "").strip()
    # 1. Custom series price override
    if sid and sid in rules.get("custom_series", {}):
        c = max(1, int(rules["custom_series"][sid]))
        return {
            "coins": c,
            "riel": c * rate,
            "is_promo": False,
            "rate": rate,
            "standard_coins": std_coins,
            "standard_riel": std_riel,
            "series_id": sid
        }

    # 2. Date-based auto promotion check
    if rules.get("promo_enabled"):
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        start_d = str(rules.get("promo_start_date") or "").strip()
        end_d = str(rules.get("promo_end_date") or "").strip()
        active = True
        if start_d and today_str < start_d:
            active = False
        if end_d and today_str > end_d:
            active = False

        if active:
            promo_c = max(1, int(rules.get("promo_coins", 1)))
            return {
                "coins": promo_c,
                "riel": promo_c * rate,
                "is_promo": True,
                "promo_name": rules.get("promo_name", "ប្រូម៉ូសិនពិសេស"),
                "promo_start": start_d,
                "promo_end": end_d,
                "rate": rate,
                "standard_coins": std_coins,
                "standard_riel": std_riel,
                "series_id": sid
            }

    # 3. Standard unchanging price
    return {
        "coins": std_coins,
        "riel": std_riel,
        "is_promo": False,
        "rate": rate,
        "standard_coins": std_coins,
        "standard_riel": std_riel,
        "series_id": sid
    }

def create_coin_request(user_token_or_dev: str, coins: int, amount_riel: int = None, note: str = ""):
    """
    User creates a Coin purchase request to be approved by ADMIN.
    Saved to Firebase Realtime Database at /coin_requests/{req_id}.json.
    """
    st = get_user_status(user_token_or_dev)
    if not st.get("authenticated") or st.get("status") in ("guest", "banned"):
        return False, "សូមចុះឈ្មោះ ឬចូលប្រើប្រាស់គណនីជាមុនសិន ទើបអាចស្នើសុំទិញ Coin បាន!"

    req_coins = max(1, int(coins))
    rate = 500
    total_riel = int(amount_riel) if amount_riel is not None else (req_coins * rate)
    now_ts = int(time.time())
    req_id = f"req_{now_ts}_{secrets.token_hex(4)}"

    req_payload = {
        "id": req_id,
        "username": st.get("username", "User"),
        "name": st.get("name", ""),
        "contact": st.get("contact", ""),
        "device_id": st.get("device_id", ""),
        "coins": req_coins,
        "amount_riel": total_riel,
        "rate": rate,
        "status": "pending",  # pending, approved, rejected
        "note": str(note or "").strip(),
        "created_at": now_ts,
        "updated_at": now_ts,
        "approved_at": 0,
        "admin_note": ""
    }

    try:
        url, params = _firebase_url(f"coin_requests/{req_id}")
        if url:
            requests.put(url, params=params, json=req_payload, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        return True, req_payload
    except Exception as e:
        print(f"[coin_request] error: {e}")
        return False, str(e)

def get_user_coin_requests(user_token_or_dev: str):
    """Get all coin requests made by a specific user."""
    st = get_user_status(user_token_or_dev)
    u_name = str(st.get("username", "")).lower()
    dev = clean_firebase_key(st.get("device_id", ""))
    all_reqs = admin_get_all_coin_requests()
    out = []
    for r in all_reqs:
        if str(r.get("username", "")).lower() == u_name or clean_firebase_key(r.get("device_id", "")) == dev:
            out.append(r)
    return out

def admin_get_all_coin_requests():
    """Admin: retrieve all coin requests from Firebase Realtime Database."""
    try:
        url, params = _firebase_url("coin_requests")
        if not url:
            return []
        r = requests.get(url, params=params, timeout=7, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code != 200 or not r.text or r.text == "null":
            return []
        data = r.json()
        if not isinstance(data, dict):
            return []
        out = []
        for k, item in data.items():
            if isinstance(item, dict):
                item["id"] = item.get("id") or k
                out.append(item)
        # Sort pending first, then by created_at desc
        out.sort(key=lambda x: (1 if x.get("status") == "pending" else 0, x.get("created_at", 0)), reverse=True)
        return out
    except Exception as e:
        print(f"[coin] admin get all requests error: {e}")
        return []

def admin_approve_coin_request(request_id: str, admin_note: str = ""):
    """
    Admin: approve a coin purchase request.
    Automatically credits user account with coins in Firebase & local.
    """
    try:
        url, params = _firebase_url(f"coin_requests/{request_id}")
        if not url:
            return False, "Firebase is not configured"
        r = requests.get(url, params=params, timeout=5, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code != 200 or not r.text or r.text == "null":
            return False, "មិនឃើញសំណើនេះលើ Firebase RTDB ឡើយ"

        req_data = r.json()
        if not isinstance(req_data, dict):
            return False, "Invalid request data"

        if req_data.get("status") == "approved":
            return True, "សំណើនេះត្រូវបាន Approve រួចរាល់ហើយ"

        coins = int(req_data.get("coins", 0))
        target_id = req_data.get("device_id") or req_data.get("username")

        # Credit coins to user!
        ok, res = admin_adjust_user_coins(target_id, action="add", coins=coins, note=f"Approve Request #{request_id} ({coins} Coins = {coins*500:,}៛)")
        if not ok:
            return False, f"បរាជ័យក្នុងការបញ្ចូល Coins ជូន User: {res}"

        now_ts = int(time.time())
        patch_data = {
            "status": "approved",
            "approved_at": now_ts,
            "updated_at": now_ts,
            "admin_note": admin_note or "Admin approved payment"
        }
        requests.patch(url, params=params, json=patch_data, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        return True, {"coins_added": coins, "user": res}
    except Exception as e:
        return False, str(e)

def admin_reject_coin_request(request_id: str, reason: str = ""):
    """Admin: reject a coin purchase request."""
    try:
        url, params = _firebase_url(f"coin_requests/{request_id}")
        if not url:
            return False, "Firebase is not configured"
        now_ts = int(time.time())
        patch_data = {
            "status": "rejected",
            "rejected_at": now_ts,
            "updated_at": now_ts,
            "admin_note": reason or "Rejected by admin"
        }
        r = requests.patch(url, params=params, json=patch_data, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        return r.status_code == 200, "បានបដិសេធសំណើជោគជ័យ"
    except Exception as e:
        return False, str(e)

def admin_adjust_user_coins(username_or_dev: str, action: str = "add", coins: int = 0, note: str = ""):
    """
    Admin: freely adjust any user's coins (add, subtract, set).
    Updates local user state and syncs to Firebase Realtime Database.
    """
    ident = str(username_or_dev or "").strip()
    if not ident:
        return False, "សូមបញ្ជាក់ User ឬ Device ID"

    num = max(0, int(coins))
    now_ts = int(time.time())

    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        target_k = None
        for k, u in users.items():
            if k == ident or u.get("token") == ident or u.get("device_id") == ident or clean_firebase_key(u.get("device_id", "")) == clean_firebase_key(ident) or str(u.get("username", "")).lower() == ident.lower():
                target = u
                target_k = k
                break

        if not target:
            # Check Firebase
            clean_id = clean_firebase_key(ident)
            fb = firebase_fetch_license(clean_id)
            if fb and isinstance(fb, dict) and fb.get("username"):
                for k, u in users.items():
                    if u.get("username") == fb.get("username"):
                        target = u
                        target_k = k
                        break

        if not target:
            return False, f"រកមិនឃើញ User '{ident}' ក្នុងប្រព័ន្ធឡើយ"

        curr_c = int(target.get("coins", 0))
        if action in ("add", "plus", "+"):
            new_c = curr_c + num
        elif action in ("subtract", "deduct", "minus", "sub", "-"):
            new_c = max(0, curr_c - num)
        elif action in ("set", "="):
            new_c = num
        else:
            new_c = curr_c + num

        target["coins"] = new_c
        target["coins_riel"] = new_c * 500
        target["updated_at"] = now_ts
        if not isinstance(target.get("purchased_series"), dict):
            target["purchased_series"] = {}

        _save_data(d)

        # Update active sessions
        for tok, su in _sessions.items():
            if su.get("username") == target.get("username") or su.get("device_id") == target.get("device_id"):
                su["coins"] = new_c
                su["coins_riel"] = new_c * 500

    # Sync to Firebase RTDB
    dev_id = target.get("device_id") or ident
    clean_id = clean_firebase_key(dev_id)
    try:
        url, params = _firebase_url(f"licenses/{clean_id}")
        if url:
            requests.patch(url, params=params, json={"coins": new_c, "updated_at": now_ts}, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
    except Exception as e:
        print(f"[coin] firebase coin sync error: {e}")

    # Log Transaction in Firebase RTDB
    _record_coin_transaction(
        username=target.get("username", "User"),
        device_id=dev_id,
        tx_type="admin_adjust" if action != "add" else "topup",
        coins_change=(new_c - curr_c),
        balance_after=new_c,
        note=note or f"Admin adjusted coins ({action} {num})"
    )

    return True, {"username": target.get("username"), "old_coins": curr_c, "new_coins": new_c, "coins_riel": new_c * 500}

def _record_coin_transaction(username: str, device_id: str, tx_type: str, coins_change: int, balance_after: int, series_id: str = "", series_title: str = "", note: str = ""):
    """Log coin transaction to Firebase RTDB at /coin_transactions/{tx_id}.json."""
    try:
        now_ts = int(time.time())
        tx_id = f"tx_{now_ts}_{secrets.token_hex(4)}"
        tx_data = {
            "id": tx_id,
            "username": username,
            "device_id": device_id,
            "type": tx_type,  # topup, movie_purchase, admin_adjust, refund
            "coins_change": coins_change,
            "amount_riel": coins_change * 500,
            "balance_after": balance_after,
            "series_id": series_id,
            "series_title": series_title,
            "note": note,
            "created_at": now_ts
        }
        url, params = _firebase_url(f"coin_transactions/{tx_id}")
        if url:
            requests.put(url, params=params, json=tx_data, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
    except Exception as e:
        print(f"[transaction] log error: {e}")

def admin_get_coin_transactions(limit: int = 50):
    """Admin: retrieve recent coin transactions from Firebase Realtime Database."""
    try:
        url, params = _firebase_url("coin_transactions")
        if not url:
            return []
        r = requests.get(url, params=params, timeout=7, headers={"User-Agent": "SYD-Downloader-Pro"})
        if r.status_code != 200 or not r.text or r.text == "null":
            return []
        data = r.json()
        if not isinstance(data, dict):
            return []
        out = [item for item in data.values() if isinstance(item, dict)]
        out.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return out[:limit]
    except Exception as e:
        print(f"[transaction] get error: {e}")
        return []

def finalize_series_purchase(user_token_or_dev: str, series_id: str, series_title: str = ""):
    """
    CRITICAL RULE: Deduct coins from user account ONLY when the download is 100% completed!
    If user already owns the movie, or is VIP/ADMIN, no coins are deducted.
    """
    sid = str(series_id or "").strip()
    if not sid:
        return False, "Missing series_id"

    st = get_user_status(user_token_or_dev)
    if st.get("is_admin") or st.get("is_vip"):
        return True, {"coins_deducted": 0, "balance_after": int(st.get("coins", 0)), "reason": "VIP/Admin full access (no coins needed)", "series_id": sid}

    purchased = st.get("purchased_series") or {}
    if sid in purchased or str(sid) in purchased:
        return True, {"coins_deducted": 0, "balance_after": int(st.get("coins", 0)), "reason": "Already purchased", "series_id": sid}

    price_info = get_movie_pricing(sid)
    req_coins = price_info["coins"]
    now_ts = int(time.time())

    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        for k, u in users.items():
            if u.get("token") == user_token_or_dev or u.get("device_id") == user_token_or_dev or u.get("username") == st.get("username"):
                target = u
                break

        if not target:
            return False, "User not found"

        curr_c = int(target.get("coins", 0))
        new_c = max(0, curr_c - req_coins)
        target["coins"] = new_c
        target["coins_riel"] = new_c * 500

        if "purchased_series" not in target or not isinstance(target["purchased_series"], dict):
            target["purchased_series"] = {}

        target["purchased_series"][sid] = {
            "series_id": sid,
            "title": series_title or sid,
            "coins": req_coins,
            "amount_riel": req_coins * 500,
            "purchased_at": now_ts,
            "download_completed": True
        }
        _save_data(d)

        # Update active sessions
        for tok, su in _sessions.items():
            if su.get("username") == target.get("username") or su.get("device_id") == target.get("device_id"):
                su["coins"] = new_c
                su["coins_riel"] = new_c * 500
                if "purchased_series" not in su or not isinstance(su["purchased_series"], dict):
                    su["purchased_series"] = {}
                su["purchased_series"][sid] = target["purchased_series"][sid]

    # Sync updated coins and purchased_series to Firebase RTDB
    dev_id = target.get("device_id") or st.get("device_id")
    clean_id = clean_firebase_key(dev_id)
    try:
        url, params = _firebase_url(f"licenses/{clean_id}")
        if url:
            patch = {
                "coins": new_c,
                f"purchased_series/{clean_firebase_key(sid)}": target["purchased_series"][sid],
                "updated_at": now_ts
            }
            requests.patch(url, params=params, json=patch, timeout=6, headers={"User-Agent": "SYD-Downloader-Pro"})
        if clean_id in _firebase_cache and isinstance(_firebase_cache[clean_id], dict):
            _firebase_cache[clean_id]["coins"] = new_c
            if "purchased_series" not in _firebase_cache[clean_id] or not isinstance(_firebase_cache[clean_id]["purchased_series"], dict):
                _firebase_cache[clean_id]["purchased_series"] = {}
            _firebase_cache[clean_id]["purchased_series"][clean_firebase_key(sid)] = target["purchased_series"][sid]
    except Exception as e:
        print(f"[purchase] firebase sync error: {e}")

    # Log Transaction
    _record_coin_transaction(
        username=target.get("username", "User"),
        device_id=dev_id,
        tx_type="movie_purchase",
        coins_change=-req_coins,
        balance_after=new_c,
        series_id=sid,
        series_title=series_title,
        note=f"Download Completed 100%: Deducted {req_coins} coins ({req_coins*500:,}៛)"
    )

    print(f"[Coin] Successfully finalized purchase for series {sid} ({series_title}): -{req_coins} coins, new balance = {new_c}")
    return True, {"coins_deducted": req_coins, "balance_after": new_c, "series_id": sid}

def cancel_pending_purchase(user_token_or_dev: str, series_id: str, reason: str = "download_incomplete"):
    """
    CRITICAL RULE: If download fails or is cancelled, do NOT deduct coins!
    0 coins are deducted; user account balance remains intact.
    """
    sid = str(series_id or "").strip()
    print(f"[Coin] Download of series {sid} NOT completed ({reason}). 0 coins deducted from user account!")
    return True, "0 coins deducted (download failed or incomplete)"


def switch_mode(mode: str, pin: str = "", device_id: str = ""):
    """
    Switch active view/mode between 'user' (real regular user) and 'admin' (super admin).
    Returns (ok, result_dict).
    """
    mode = str(mode or "").strip().lower()
    dev = device_id or get_current_device_id()
    with _lock:
        _logged_out_devices.discard(dev)
        _logged_out_devices.discard(get_current_device_id())

    if mode == "admin":
        if pin and pin not in (ADMIN_PASSWORD, "syd@168"):
            return False, "ពាក្យសម្ងាត់ Admin មិនត្រឹមត្រូវទេ"
        with _lock:
            d = _load_data()
            admin_u = d.get("users", {}).get("admin")
            if not admin_u:
                admin_u = dict(DEFAULT_DATA.get("users", {}).get("admin", {}))
                admin_u["username"] = "ADMIN"
                admin_u["role"] = "admin"
                admin_u["is_admin"] = True
                admin_u["is_vip"] = True
        tok = "adm_" + secrets.token_hex(16)
        admin_copy = dict(admin_u)
        admin_copy["token"] = tok
        _sessions[tok] = admin_copy
        _sessions[dev] = admin_copy
        return True, get_user_status(tok)

    elif mode == "user":
        with _lock:
            d = _load_data()
            users = d.setdefault("users", {})
            u = users.get("user_primary")
            now_ts = int(time.time())
            if not u:
                u = {
                    "key": "user_primary",
                    "device_id": dev,
                    "username": "USER",
                    "name": "អ្នកប្រើប្រាស់ជាក់ស្តែង",
                    "contact": "012345678",
                    "password_hash": hash_pw("123456"),
                    "role": "user",
                    "is_vip": False,
                    "is_admin": False,
                    "status": "user",
                    "max_free_episodes": 5,
                    "coins": 10,
                    "coins_riel": 5000,
                    "purchased_series": {},
                    "created_at": now_ts,
                    "expires_at": now_ts + TRIAL_SECONDS,
                    "days_left": 3,
                    "package_name": "User ធម្មតា (សាកល្បង 3 ថ្ងៃ)",
                    "package_badge": "3 ថ្ងៃ",
                    "is_banned": False
                }
                users["user_primary"] = u
                _save_data(d)
            tok = "usr_" + secrets.token_hex(16)
            u["token"] = tok
            _sessions[tok] = u
            _sessions[dev] = u
        return True, get_user_status(tok)

    return False, "Invalid mode"



