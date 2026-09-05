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

_lock = threading.Lock()

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
DEV_KEYS = {"DEV8888", "DEV-MASTER", "8888", "syd@168"}

def get_current_device_id():
    return LIC.device_id()

def clean_firebase_key(key: str) -> str:
    """Sanitize key for Firebase Realtime Database (cannot contain . $ # [ ] / :)."""
    s = str(key or "").strip()
    return re.sub(r'[\.\$\[\]\#\/:]', '_', s)

# DEVELOPER MACHINE IDS (Permanently exempt from Login/Register, 100% full unrestricted access)
DEV_MACHINE_IDS = {
    "d1:c32730ad5cd271421a6c7d52bc81952e",  # Primary Developer PC (PC-1 / Dara)
    clean_firebase_key("d1:c32730ad5cd271421a6c7d52bc81952e")
}

def is_dev_machine(device_id_str: str = "") -> bool:
    dev = (device_id_str or get_current_device_id()).strip()
    clean_dev = clean_firebase_key(dev)
    if dev in DEV_MACHINE_IDS or clean_dev in DEV_MACHINE_IDS:
        return True
    try:
        d = _load_data()
        dev_list = d.get("dev_machines", [])
        for dm in dev_list:
            if dm == dev or clean_firebase_key(dm) == clean_dev:
                return True
    except Exception:
        pass
    return False

# In-memory Active Sessions: token -> user_dict
_sessions = {}

def hash_pw(pw: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256((pw or "").strip().encode('utf-8')).hexdigest()

DEFAULT_DATA = {
    "mode": "vip_required",  # "vip_required", "free_all"
    "admin_pin": "8888",
    "admin_user": "ADMIN",
    "admin_pass": "syd@168",
    "dev_key": "DEV8888",
    "settings": {
        "telegram_admin": "",
        "telegram_group": ""
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
                data["admin_pin"] = "8888"
            if "dev_key" not in data:
                data["dev_key"] = "DEV8888"
            if "settings" not in data:
                data["settings"] = {
                    "telegram_admin": "",
                    "telegram_group": ""
                }
            elif isinstance(data.get("settings"), dict) and "khqr_image" in data["settings"]:
                data["settings"].pop("khqr_image", None)
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
                    "status": "approved",
                    "max_free_episodes": 999999,
                    "created_at": int(time.time()),
                    "approved_at": int(time.time()),
                    "expires_at": 0
                }
            return data
    except Exception:
        return dict(DEFAULT_DATA)

def _save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[access_manager] save error: {e}")

def get_settings():
    with _lock:
        d = _load_data()
        st = dict(d.get("settings", {
            "telegram_admin": "",
            "telegram_group": ""
        }))
        st.pop("khqr_image", None)
        return st

def save_settings(new_settings: dict):
    with _lock:
        d = _load_data()
        st = d.get("settings", {})
        if not isinstance(st, dict):
            st = {}
        for k in ("telegram_admin", "telegram_group"):
            if k in new_settings:
                st[k] = str(new_settings[k] or "").strip()
        st.pop("khqr_image", None)
        d["settings"] = st
        _save_data(d)
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
        expected = str(d.get("admin_pin", "8888"))
        p = str(pin or "").strip()
        return p == expected or p == "syd@168" or p == "DEV8888"

def set_pin(new_pin):
    with _lock:
        d = _load_data()
        d["admin_pin"] = str(new_pin).strip()
        _save_data(d)
        return True

def get_current_device_id():
    return LIC.device_id()

# ----------------- Authentication & User Management ----------------- #

def login(identity: str, password: str, device_id: str = ""):
    """
    Login handler for ADMIN and Regular Users.
    ADMIN credentials: ADMIN / syd@168
    """
    ident = (identity or "").strip()
    pw = (password or "").strip()
    dev = (device_id or get_current_device_id()).strip()

    # 0. DEV MACHINE check: Developer PC has permanent full unrestricted access
    if is_dev_machine(dev) or is_dev_machine(ident) or is_dev_machine(get_current_device_id()):
        token = "dev_master_" + clean_firebase_key(dev)[-12:]
        dev_user = {
            "token": token,
            "device_id": dev,
            "username": "DEV (Dara)",
            "name": "Developer Master (PC-1)",
            "contact": "Dev System Direct",
            "role": "dev",
            "is_admin": True,
            "is_dev": True,
            "is_vip": True,
            "status": "approved",
            "max_free_episodes": 999999,
            "package": "lifetime",
            "package_name": "Developer Master (សេរី គ្មានដែនកំណត់)",
            "package_badge": "DEV MASTER",
            "expires_at": 0,
            "expires_date": "Permanent Developer Access",
            "days_left": -1
        }
        with _lock:
            _sessions[token] = dev_user
            if dev:
                _sessions[dev] = dev_user
        return True, dev_user

    # 1. ADMIN Account check (Case-insensitive username)
    if (ident.upper() == "ADMIN" and pw == ADMIN_PASSWORD) or (pw == ADMIN_PASSWORD and ident in DEV_KEYS) or (ident in DEV_KEYS and pw in DEV_KEYS):
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
            "status": "approved",
            "max_free_episodes": 999999,
            "package": "lifetime",
            "package_name": "Full Control (គ្មានការ Lock)",
            "package_badge": "Full Control",
            "expires_at": 0,
            "expires_date": "Lifetime Full Access",
            "days_left": -1
        }
        with _lock:
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
            return False, "រកមិនឃើញគណនីនេះទេ (សូមពិនិត្យមើល Username ឬលេខទូរស័ព្ទ)"

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
        is_admin = (role == "admin")
        is_vip = is_admin or (role == "dev") or (target.get("status") == "approved" and target.get("is_vip", False))

        # Check expiration
        exp = target.get("expires_at", 0)
        if is_vip and not is_admin and role != "dev" and exp > 0 and exp < now:
            is_vip = False
            target["status"] = "expired"
            target["is_vip"] = False
            target["role"] = "user"

        # Check 7-day trial expiration for regular user without VIP request
        if not is_vip and not is_admin and role != "dev":
            if exp == 0:
                exp = (target.get("created_at") or now) + (7 * 86400)
                target["expires_at"] = exp
            if now >= exp and target.get("status") != "pending_vip":
                del users[target_key]
                _save_data(d)
                try:
                    if dev:
                        firebase_admin_delete_license(dev)
                except Exception:
                    pass
                return False, "⚠️ គណនីធម្មតានេះបានផុតកំណត់រយៈពេល 7 ថ្ងៃ ដោយមិនបានស្នើសុំ VIP! គណនីត្រូវបានលុបចេញពីប្រព័ន្ធដាច់ខាត។ សូមចុះឈ្មោះបង្កើតគណនីថ្មី!"

        max_eps = 999999 if is_vip else 10
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
            target["expires_date"] = "User ធម្មតា (សាកល្បង 7 ថ្ងៃ)"
            target["days_left"] = 7

        _save_data(d)
        _sessions[token] = target
        if dev:
            _sessions[dev] = target

        return True, target

def register_user(username: str, name: str, contact: str, password: str, note: str = "", package: str = "1_year", device_id: str = ""):
    """
    Register a new regular user account.
    Regular user gets free access to episodes 1-10.
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
        trial_seconds = 7 * 86400
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
            "max_free_episodes": 10,
            "created_at": now,
            "updated_at": now,
            "approved_at": 0,
            "expires_at": expires_at,
            "token": token,
            "package_name": "User ធម្មតា (សាកល្បង 7 ថ្ងៃ)",
            "package_badge": "7 ថ្ងៃ",
            "expires_date": exp_date_str,
            "days_left": 7
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
    STRICT RULE: Regular users (role == 'user') have a 7-day trial period.
    Within these 7 days, they must submit a VIP request (status == 'pending_vip').
    If 7 days elapse without submitting a VIP request, they MUST be completely deleted
    from both the local database (user_access.json) and Firebase Realtime Database.
    """
    now = int(time.time())
    purged_keys = []
    purged_devices = []
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        for k, u in list(users.items()):
            # Only apply to regular user who is NOT VIP and NOT ADMIN
            if u.get("role") == "user" and not u.get("is_vip") and not u.get("is_admin"):
                exp = u.get("expires_at", 0)
                if exp == 0:
                    created = u.get("created_at") or now
                    exp = created + (7 * 86400)
                    u["expires_at"] = exp

                st = u.get("status", "user")
                # If status is 'pending_vip', user HAS submitted a VIP request! Keep them alive for admin review.
                if st == "pending_vip":
                    continue

                # If expired without VIP request: PURGE
                if now >= exp:
                    purged_keys.append(k)
                    dev = u.get("device_id")
                    if dev:
                        purged_devices.append(dev)
                    del users[k]

        if purged_keys:
            d["users"] = users
            _save_data(d)
            # Remove from active sessions
            for tok in list(_sessions.keys()):
                su = _sessions.get(tok, {})
                if su.get("key") in purged_keys or su.get("device_id") in purged_devices:
                    del _sessions[tok]

    # Delete purged users from Firebase Realtime Database
    for dev in purged_devices:
        try:
            firebase_admin_delete_license(dev)
            print(f"[purge] deleted expired 7-day trial user without VIP request: {dev}")
        except Exception as ex:
            print(f"[purge] firebase delete error for {dev}: {ex}")

    return len(purged_keys)

def get_user_status(token_or_device_id: str = ""):
    """
    Returns the user's status, settings, and allowed episode boundaries.
    Startup check: Queries Firebase Realtime Database (https://syd-drama-default-rtdb.firebaseio.com)
    for License Key / Account.
    - If NO account in Firebase: Requires mandatory registration as regular user (Free Tier 1-10).
    - If account in Firebase: Returns regular user (episodes 1-10) or VIP (episodes 1-all if approved by ADMIN).
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

    # 0. DEV MACHINE check: Developer PC is 100% exempt from registration/login, permanent full unrestricted access!
    if is_dev_machine(dev_check) or is_dev_machine(current_hw_id) or is_dev_machine(ident):
        dev_token = "dev_master_" + clean_firebase_key(current_hw_id)[-12:]
        dev_user_obj = {
            "token": dev_token,
            "authenticated": True,
            "registered": True,
            "has_firebase_account": True,
            "must_register": False,
            "device_id": current_hw_id,
            "license_key": clean_firebase_key(current_hw_id),
            "username": "DEV (Dara)",
            "name": "Developer Master (PC-1)",
            "contact": "Dev System Direct",
            "role": "dev",
            "is_admin": True,
            "is_dev": True,
            "is_vip": True,
            "status": "approved",
            "max_free_episodes": 999999,
            "requested_package": "lifetime",
            "approved_package": "lifetime",
            "package_name": "Developer Master (សេរី គ្មានដែនកំណត់)",
            "package_badge": "DEV MASTER",
            "expires_at": 0,
            "expires_date": "Permanent Developer Access",
            "days_left": -1,
            "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }
        _sessions[dev_token] = dev_user_obj
        _sessions[dev_check] = dev_user_obj
        _sessions[current_hw_id] = dev_user_obj
        return dev_user_obj

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
            "is_dev": True,
            "is_vip": True,
            "status": "approved",
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
                "username": user.get("username", "Guest"),
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
            "is_deleted": True,
            "can_download": False,
            "device_id": dev_check,
            "license_key": clean_id,
            "username": "ភ្ញៀវ (Guest)",
            "name": "Guest Visitor",
            "contact": "",
            "role": "guest",
            "is_admin": False,
            "is_dev": False,
            "is_vip": False,
            "status": "guest",
            "max_free_episodes": 10,
            "package_name": "ភ្ញៀវមិនទាន់ចុះឈ្មោះ (ភាគ 1-10)",
            "package_badge": "Guest",
            "expires_at": 0,
            "expires_date": "Free Tier (ភាគ 1-10)",
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
            user["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 10)
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
                "max_free_episodes": 0 if fb_banned else (999999 if fb_vip else 10),
                "created_at": fb_data.get("created_at", now_sec),
                "package_name": "VIP Member (ដោះសោរគ្រប់ភាគ)" if fb_vip else "User ធម្មតា (សាកល្បង 7 ថ្ងៃ)",
                "package_badge": "VIP" if fb_vip else "7 ថ្ងៃ"
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
        max_eps = 999999 if is_vip else 10
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
                exp = (user.get("created_at") or now) + (7 * 86400)
                user["expires_at"] = exp
            days_left = _calc_days_left(exp, now, False)
            exp_date = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            pkg_name = f"សំណើ VIP កំពុងរង់ចាំ (នៅសល់ {days_left} ថ្ងៃ)"
            pkg_badge = "Pending VIP"
        else:
            # Regular user 7-day trial
            if exp == 0:
                exp = (user.get("created_at") or now) + (7 * 86400)
                user["expires_at"] = exp
            days_left = _calc_days_left(exp, now, False)
            exp_date = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
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

    # 7. Fallback (Guest)
    return {
        "authenticated": False,
        "registered": False,
        "has_firebase_account": False,
        "must_register": True,
        "device_id": dev_check,
        "license_key": clean_id,
        "username": "ភ្ញៀវ (Guest)",
        "name": "Guest Visitor",
        "contact": "",
        "role": "guest",
        "is_admin": False,
        "is_dev": False,
        "is_vip": False,
        "status": "guest",
        "max_free_episodes": 10,
        "package_name": "ភ្ញៀវមិនទាន់ Login (ភាគ 1-10)",
        "package_badge": "Guest",
        "expires_at": 0,
        "expires_date": "Free Tier (ភាគ 1-10)",
        "days_left": 0,
        "firebase_database": "https://syd-drama-default-rtdb.firebaseio.com",
        "message": "",
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
        target["max_free_episodes"] = 10
        target["updated_at"] = now
        _save_data(d)

        # Update active sessions in memory
        for tok, su in list(_sessions.items()):
            if su.get("username") == target.get("username") or su.get("device_id") == target.get("device_id"):
                su["status"] = "pending_vip"
                su["is_banned"] = False
                su["is_vip"] = False
                su["role"] = "user"
                su["max_free_episodes"] = 10
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
    When unbanned, user access is restored as regular user (1-10 episodes).
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
                target["max_free_episodes"] = 10
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
                        su["max_free_episodes"] = 10

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
    Revert a VIP user back to a regular free user (1-10 episodes).
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
                u["max_free_episodes"] = 10
                u["package_name"] = "គណនីធម្មតា (ភាគ 1-10)"
                u["updated_at"] = int(time.time())
                _save_data(d)
                for tok, s_user in list(_sessions.items()):
                    if s_user.get("username") == u.get("username") or s_user.get("device_id") == u.get("device_id"):
                        s_user["is_vip"] = False
                        s_user["status"] = "user"
                        s_user["max_free_episodes"] = 10
                        s_user["expires_at"] = 0
                        s_user["package_name"] = "គណនីធម្មតា (ភាគ 1-10)"
                return True
    return False

def check_can_download(token_or_dev: str, requested_episodes: list = None, max_ep: int = 0):
    """
    Check download authorization and enforce episode limits.
    ADMIN & VIP: 100% unrestricted.
    Regular User / Guest: Restricted to episodes 1 to 10.
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

    # Regular User: Restricted to episodes 1 to 10
    if max_ep > 10:
        return False, "vip_required", "គណនីធម្មតាអាចទាញយកបានត្រឹមភាគ ១ ដល់ ១០ ប៉ុណ្ណោះ! សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទាញយកភាគ ១១ ឡើងទៅ។", "1-10"

    if requested_episodes:
        locked = [e for e in requested_episodes if int(e) > 10]
        if locked:
            return False, "vip_required", f"ភាគលើសពី ១០ ({', '.join(map(str, locked[:4]))}...) ត្រូវបានចាក់សោរ! គណនីធម្មតាអាចទាញយកបានត្រឹមភាគ ១-១០។", "1-10"

    return True, "regular_allowed", "អនុញ្ញាតទាញយក (ភាគ ១ ដល់ ១០)", "1-10"

def can_access_episode(episode_num: int, token_or_dev: str = ""):
    """
    Check if user can play or access a specific episode.
    Episodes 1 to 10: Free for all.
    Episodes 11+: ADMIN or VIP only.
    """
    st = get_user_status(token_or_dev)
    if st.get("status") == "machine_mismatch":
        return False, "machine_mismatch", "🚫 Machine ID មិនត្រូវគ្នា! គណនីនេះត្រូវបានចាក់សោរឱ្យប្រើប្រាស់បានតែលើ PC ដើម 1 គត់ប៉ុណ្ណោះ (1 Machine ID = 1 PC)។"

    if st.get("is_banned") or st.get("status") == "banned":
        return False, "banned", "🚫 គណនីរបស់អ្នកត្រូវបាន ADMIN បិទ (Banned) មិនអាចប្រើប្រាស់បានទៀតទេ! សូមទាក់ទង ADMIN ឬស្នើសុំម្តងទៀត។"

    if int(episode_num) <= 10:
        return True, "free_episode", "ភាគ ១-១០ ឥតគិតថ្លៃ"

    if st.get("is_admin") or st.get("is_vip"):
        return True, "vip_allowed", "VIP / ADMIN Unlocked"

    return False, "vip_required", "ភាគនេះសម្រាប់សមាជិក VIP ប៉ុណ្ណោះ! គណនីធម្មតាអាចទស្សនាបានត្រឹមភាគ ១ ដល់ ១០។ សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទស្សនាគ្រប់ភាគ។"

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
                u["expires_date"] = "Free (1-10)"

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
    return st.get("is_admin") or st.get("is_dev", False)

def is_vip(device_id=None):
    st = get_user_status(device_id)
    return st.get("is_vip", False)

# ----------------- Firebase Realtime Database Integration ----------------- #

_firebase_cache = {}  # clean_id -> {"time": float, "data": dict or None, "deleted": bool}
_firebase_last_poll = {}
_fb_lock = threading.Lock()

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
            "max_free_episodes": 0 if fb_banned else (999999 if fb_vip else 10),
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
                        u["max_free_episodes"] = 0 if fb_banned else (999999 if fb_vip else 10)
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
                item["expires_date"] = "Free Tier (ភាគ 1-10)"
                item["days_left"] = 0
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
            "max_free_episodes": 0 if banned else 10,
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

