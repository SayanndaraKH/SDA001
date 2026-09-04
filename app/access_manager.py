import os
import json
import time
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

# Master Keys for DEV unrestricted access
DEV_KEYS = {"DEV8888", "DEV-MASTER", "8888"}

DEFAULT_DATA = {
    "mode": "free_all",  # "vip_required", "free_all"
    "admin_pin": "8888",
    "dev_key": "DEV8888",
    "users": {}
}

def _load_data():
    if not os.path.exists(DATA_FILE):
        _save_data(DEFAULT_DATA)
        return dict(DEFAULT_DATA)
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data["mode"] = "free_all"
            if "users" not in data:
                data["users"] = {}
            if "admin_pin" not in data:
                data["admin_pin"] = "8888"
            if "dev_key" not in data:
                data["dev_key"] = "DEV8888"
            return data
    except Exception:
        return dict(DEFAULT_DATA)

def _save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[access_manager] save error: {e}")

def get_mode():
    return "free_all"

def set_mode(mode):
    return "free_all"

def verify_pin(pin):
    with _lock:
        d = _load_data()
        expected = str(d.get("admin_pin", "8888"))
        return str(pin).strip() == expected

def set_pin(new_pin):
    with _lock:
        d = _load_data()
        d["admin_pin"] = str(new_pin).strip()
        _save_data(d)
        return True

def get_current_device_id():
    return LIC.device_id()

def is_dev(device_id=None):
    return True

def is_vip(device_id=None):
    return True

def get_user_status(device_id=None):
    dev = str(device_id or get_current_device_id()).strip()
    return {
        "mode": "free_all",
        "device_id": dev,
        "registered": True,
        "status": "approved",
        "role": "dev",
        "is_dev": True,
        "is_vip": True,
        "package": "lifetime",
        "package_name": "VIP មួយជីវិត (Full Access)",
        "package_badge": "មួយជីវិត",
        "expires_at": 0,
        "expires_date": "Lifetime",
        "days_left": -1,
        "user_info": {"name": "VIP Member", "role": "dev", "status": "approved"},
        "label": LIC.device_label(),
        "packages_available": list(VIP_PACKAGES.values())
    }

def register_user(name, contact, note="", package="1_year", device_id=None):
    dev = str(device_id or get_current_device_id()).strip()
    pkg = str(package).strip()
    if pkg not in VIP_PACKAGES:
        pkg = "1_year"
    with _lock:
        d = _load_data()
        existing = d.get("users", {}).get(dev, {})
        status = existing.get("status", "pending")
        role = existing.get("role", "user")
        if status not in ("approved", "pending"):
            status = "pending"
        
        now = int(time.time())
        d["users"][dev] = {
            "device_id": dev,
            "name": str(name).strip(),
            "contact": str(contact).strip(),
            "note": str(note).strip(),
            "requested_package": pkg,
            "approved_package": existing.get("approved_package", ""),
            "role": role,
            "device_label": LIC.device_label(),
            "status": status,
            "updated_at": now,
            "created_at": existing.get("created_at", now),
            "approved_at": existing.get("approved_at", 0),
            "expires_at": existing.get("expires_at", 0)
        }
        _save_data(d)
        return d["users"][dev]

def dev_login(key, device_id=None):
    dev = str(device_id or get_current_device_id()).strip()
    key_str = str(key).strip()
    with _lock:
        d = _load_data()
        stored_dev_key = str(d.get("dev_key", "DEV8888"))
        if key_str not in DEV_KEYS and key_str != stored_dev_key and key_str != str(d.get("admin_pin", "8888")):
            return False, "DEV Key មិនត្រឹមត្រូវ"
        
        existing = d.get("users", {}).get(dev, {})
        now = int(time.time())
        d["users"][dev] = {
            "device_id": dev,
            "name": existing.get("name") or "Developer",
            "contact": existing.get("contact") or "DEV Team",
            "note": "Developer Master Account",
            "requested_package": "lifetime",
            "approved_package": "lifetime",
            "role": "dev",
            "device_label": LIC.device_label(),
            "status": "approved",
            "updated_at": now,
            "created_at": existing.get("created_at", now),
            "approved_at": now,
            "expires_at": 0  # 0 means Lifetime / No expiry
        }
        _save_data(d)
        return True, d["users"][dev]

def approve_user(device_id, package=None, role="user", custom_days=None):
    dev = str(device_id).strip()
    now = int(time.time())
    with _lock:
        d = _load_data()
        existing = d.get("users", {}).get(dev, {})
        
        target_pkg = package or existing.get("requested_package") or "1_year"
        is_target_dev = (role == "dev" or target_pkg == "dev")
        
        if is_target_dev:
            expires_at = 0
            approved_pkg = "lifetime"
            final_role = "dev"
        else:
            final_role = "user"
            approved_pkg = target_pkg
            if custom_days is not None and int(custom_days) > 0:
                expires_at = now + int(custom_days) * 86400
            elif target_pkg in VIP_PACKAGES:
                days = VIP_PACKAGES[target_pkg]["days"]
                expires_at = (now + days * 86400) if days > 0 else 0
            else:
                expires_at = now + 365 * 86400

        d["users"][dev] = {
            "device_id": dev,
            "name": existing.get("name") or "Approved Device",
            "contact": existing.get("contact") or "",
            "note": existing.get("note") or "",
            "requested_package": existing.get("requested_package") or approved_pkg,
            "approved_package": approved_pkg,
            "role": final_role,
            "device_label": existing.get("device_label") or LIC.device_label(),
            "status": "approved",
            "approved_at": now,
            "expires_at": expires_at,
            "updated_at": now,
            "created_at": existing.get("created_at", now)
        }
        _save_data(d)
        return True, d["users"][dev]

def extend_user(device_id, additional_days):
    dev = str(device_id).strip()
    days = int(additional_days)
    now = int(time.time())
    with _lock:
        d = _load_data()
        if dev not in d.get("users", {}):
            return False, "រកមិនឃើញអ្នកប្រើប្រាស់"
        u = d["users"][dev]
        if u.get("role") == "dev":
            return True, u  # Already unlimited
        
        cur_exp = u.get("expires_at", 0)
        if cur_exp == 0 and u.get("status") == "approved":
            return True, u  # Already lifetime
        
        base_time = max(now, cur_exp)
        new_exp = base_time + days * 86400
        u["expires_at"] = new_exp
        u["status"] = "approved"
        u["updated_at"] = now
        _save_data(d)
        return True, u

def set_dev_role(device_id, is_dev_flag=True):
    dev = str(device_id).strip()
    now = int(time.time())
    with _lock:
        d = _load_data()
        if dev not in d.get("users", {}):
            d["users"][dev] = {
                "device_id": dev,
                "name": "Developer",
                "contact": "",
                "note": "",
                "requested_package": "lifetime",
                "approved_package": "lifetime",
                "role": "dev" if is_dev_flag else "user",
                "device_label": LIC.device_label(),
                "status": "approved",
                "approved_at": now,
                "expires_at": 0,
                "updated_at": now,
                "created_at": now
            }
        else:
            d["users"][dev]["role"] = "dev" if is_dev_flag else "user"
            if is_dev_flag:
                d["users"][dev]["status"] = "approved"
                d["users"][dev]["expires_at"] = 0
            d["users"][dev]["updated_at"] = now
        _save_data(d)
        return True

def revoke_user(device_id):
    dev = str(device_id).strip()
    with _lock:
        d = _load_data()
        if dev in d.get("users", {}):
            d["users"][dev]["status"] = "rejected"
            d["users"][dev]["revoked_at"] = int(time.time())
            _save_data(d)
            return True
    return False

def delete_user(device_id):
    dev = str(device_id).strip()
    with _lock:
        d = _load_data()
        if dev in d.get("users", {}):
            del d["users"][dev]
            _save_data(d)
            return True
    return False

def list_users():
    with _lock:
        d = _load_data()
        mode = d.get("mode", "vip_required")
        users_list = list(d.get("users", {}).values())
        now = int(time.time())
        for u in users_list:
            exp = u.get("expires_at", 0)
            if u.get("role") == "dev":
                u["days_left"] = -1
            elif exp == 0:
                u["days_left"] = -1  # Lifetime
            elif exp > now:
                u["days_left"] = max(0, int((exp - now) / 86400))
            else:
                u["days_left"] = 0
                if u.get("status") == "approved":
                    u["status"] = "expired"

            if exp > 0:
                import datetime
                u["expires_date"] = datetime.datetime.fromtimestamp(exp).strftime("%d/%m/%Y")
            elif exp == 0 and (u.get("role") == "dev" or u.get("approved_package") == "lifetime"):
                u["expires_date"] = "Lifetime"
            else:
                u["expires_date"] = ""

        users_list.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return {
            "mode": mode,
            "total_users": len(users_list),
            "approved_count": len([u for u in users_list if u.get("status") == "approved"]),
            "pending_count": len([u for u in users_list if u.get("status") == "pending"]),
            "dev_count": len([u for u in users_list if u.get("role") == "dev"]),
            "users": users_list,
            "packages": list(VIP_PACKAGES.values())
        }

def check_can_download(device_id=None):
    """
    Check if the user/device is permitted to download.
    VIP is automatically unlocked for all users.
    Returns: (allowed: bool, reason: str, message: str, effective_range: str or None)
    """
    return True, "free_all", "ទាញយកឥតគិតថ្លៃ ១០០% (VIP Auto Unlocked)", None
