import os
import json
import time
import secrets
import hashlib
import threading
import licensing as LIC

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(HERE, 'user_access.json')

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
        "khqr_image": "",
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
                    "khqr_image": "",
                    "telegram_admin": "",
                    "telegram_group": ""
                }
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
        return d.get("settings", {
            "khqr_image": "",
            "telegram_admin": "",
            "telegram_group": ""
        })

def save_settings(new_settings: dict):
    with _lock:
        d = _load_data()
        st = d.get("settings", {})
        if not isinstance(st, dict):
            st = {}
        for k in ("khqr_image", "telegram_admin", "telegram_group"):
            if k in new_settings:
                st[k] = str(new_settings[k] or "").strip()
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

        max_eps = 999999 if is_vip else 10
        target["is_vip"] = is_vip
        target["is_admin"] = is_admin
        target["max_free_episodes"] = max_eps
        target["token"] = token
        target["device_id"] = dev
        target["last_login"] = now

        if exp > 0:
            import datetime
            target["expires_date"] = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            target["days_left"] = max(0, int((exp - now) / 86400))
        elif exp == 0 and is_vip:
            target["expires_date"] = "Lifetime VIP"
            target["days_left"] = -1
        else:
            target["expires_date"] = "Free (1-10 ភាគ)"
            target["days_left"] = 0

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

        now = int(time.time())
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
            "expires_at": 0,
            "token": token,
            "package_name": "គណនីធម្មតា (ភាគ 1-10)",
            "package_badge": "ភាគ 1-10",
            "expires_date": "Free Tier (ភាគ 1-10)",
            "days_left": 0
        }

        users[user_key] = user_record
        d["users"] = users
        _save_data(d)

        _sessions[token] = user_record
        if dev:
            _sessions[dev] = user_record

        return True, user_record

def get_user_status(token_or_device_id: str = ""):
    """
    Returns the user's status, settings, and allowed episode boundaries.
    """
    ident = (token_or_device_id or "").strip()
    user = None

    # Check active memory sessions
    if ident and ident in _sessions:
        user = _sessions[ident]

    if not user and ident:
        # Check database
        with _lock:
            d = _load_data()
            for k, u in d.get("users", {}).items():
                if k == ident or u.get("device_id") == ident or u.get("token") == ident or u.get("username") == ident:
                    user = u
                    break

    settings = get_settings()

    if user:
        if user.get("status") == "banned":
            return {
                "authenticated": False,
                "registered": True,
                "is_banned": True,
                "device_id": user.get("device_id") or ident,
                "username": user.get("username", "User"),
                "status": "banned",
                "error": "🚫 គណនីនេះត្រូវបានបិទមិនឱ្យប្រើប្រាស់ដោយ Admin!",
                "settings": settings,
                "packages_available": list(VIP_PACKAGES.values())
            }

        role = user.get("role", "user")
        is_admin = (role == "admin") or (str(user.get("username")).upper() == "ADMIN")
        is_vip = is_admin or (role == "dev") or (user.get("status") == "approved" and user.get("is_vip", False))

        now = int(time.time())
        exp = user.get("expires_at", 0)
        if is_vip and not is_admin and role != "dev" and exp > 0 and exp < now:
            is_vip = False
            user["status"] = "expired"

        max_eps = 999999 if is_vip else 10

        exp_date = "Lifetime Full Access" if is_admin else ("Lifetime VIP" if exp == 0 and is_vip else "Free Tier (ភាគ 1-10)")
        days_left = -1 if (is_admin or (is_vip and exp == 0)) else (max(0, int((exp - now) / 86400)) if exp > 0 else 0)
        if exp > 0:
            import datetime
            exp_date = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")

        return {
            "authenticated": True,
            "registered": True,
            "device_id": user.get("device_id") or ident,
            "username": user.get("username", "User"),
            "name": user.get("name", user.get("username", "User")),
            "contact": user.get("contact", ""),
            "role": "admin" if is_admin else ("vip" if is_vip else "user"),
            "is_admin": is_admin,
            "is_dev": is_admin or (role == "dev"),
            "is_vip": is_vip,
            "status": "approved" if is_vip else user.get("status", "user"),
            "max_free_episodes": max_eps,
            "requested_package": user.get("requested_package", "1_year"),
            "approved_package": user.get("approved_package", "lifetime" if is_admin else ""),
            "package_name": "Full Control (គ្មានការ Lock)" if is_admin else ("VIP Member (ដោះសោរគ្រប់ភាគ)" if is_vip else "គណនីធម្មតា (ទស្សនាភាគ 1-10)"),
            "package_badge": "ADMIN" if is_admin else ("VIP" if is_vip else "ភាគ 1-10"),
            "expires_at": exp,
            "expires_date": exp_date,
            "days_left": days_left,
            "settings": settings,
            "packages_available": list(VIP_PACKAGES.values())
        }

    # Guest / Unauthenticated
    return {
        "authenticated": False,
        "registered": False,
        "device_id": ident or get_current_device_id(),
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
        "settings": settings,
        "packages_available": list(VIP_PACKAGES.values())
    }

def request_vip(token_or_id: str, package: str = "1_year", note: str = ""):
    """Submit a VIP Package request to ADMIN."""
    ident = (token_or_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        target = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("token") == ident or u.get("username") == ident:
                target = u
                break
        if not target:
            return False, "រកមិនឃើញគណនីអ្នកប្រើប្រាស់ (សូម Login ជាមុនសិន)"
        
        target["requested_package"] = package or "1_year"
        target["note"] = note or target.get("note", "")
        target["status"] = "pending_vip"
        target["is_vip"] = False
        target["updated_at"] = int(time.time())
        _save_data(d)

        # Update active sessions in memory
        for tok, su in list(_sessions.items()):
            if su.get("username") == target.get("username") or su.get("device_id") == target.get("device_id"):
                su["status"] = "pending_vip"
                su["is_vip"] = False
                su["requested_package"] = target["requested_package"]

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
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("contact") == ident or u.get("key") == ident:
                target = u
                break

        if not target:
            return False, "រកមិនឃើញអ្នកប្រើប្រាស់នេះទេ"

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
                s_user["is_vip"] = True
                s_user["status"] = "approved"
                s_user["max_free_episodes"] = 999999
                s_user["expires_at"] = expires_at
                s_user["package_name"] = pkg_name

        return True, target

def ban_user(target_id: str, banned: bool = True):
    """
    ADMIN bans or unbans a user account.
    When banned, user cannot log in and active sessions are revoked.
    """
    ident = str(target_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("key") == ident:
                if str(u.get("username")).upper() == "ADMIN":
                    return False, "មិនអាចបិទគណនី ADMIN បានឡើយ"
                u["status"] = "banned" if banned else "user"
                if banned:
                    u["is_vip"] = False
                    u["max_free_episodes"] = 0
                else:
                    u["max_free_episodes"] = 10
                u["updated_at"] = int(time.time())
                _save_data(d)
                # Invalidate memory session if banned
                if banned:
                    for tok, su in list(_sessions.items()):
                        if su.get("username") == u.get("username") or su.get("device_id") == u.get("device_id"):
                            if tok in _sessions:
                                del _sessions[tok]
                return True, u
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
    if st.get("is_banned"):
        return False, "banned", "គណនីរបស់អ្នកត្រូវបានបិទមិនឱ្យប្រើប្រាស់ដោយ Admin!", None

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
    if st.get("is_banned"):
        return False, "banned", "គណនីរបស់អ្នកត្រូវបានបិទមិនឱ្យប្រើប្រាស់ដោយ Admin!"

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

def delete_user(target_id: str):
    ident = str(target_id or "").strip()
    with _lock:
        d = _load_data()
        users = d.get("users", {})
        to_del = None
        for k, u in users.items():
            if k == ident or u.get("device_id") == ident or u.get("username") == ident or u.get("key") == ident:
                if str(u.get("username")).upper() == "ADMIN":
                    return False  # Never delete ADMIN!
                to_del = k
                break
        if to_del:
            del users[to_del]
            _save_data(d)
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
