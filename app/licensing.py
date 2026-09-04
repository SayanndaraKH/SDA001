"""License Bypass Module: Connect directly without requiring a License Key.
Permanent Unlimited Mode — No Supabase calls, no device limits, no activation needed.
"""
import os
import sys
import json
import time
import socket

HERE = os.path.dirname(os.path.abspath(__file__))

def _machine_guid():
    if sys.platform.startswith('win'):
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Cryptography', 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                val, _ = winreg.QueryValueEx(k, 'MachineGuid')
                return 'mg:' + str(val) if val else None
        except Exception:
            pass
    return None

def device_id():
    g = _machine_guid()
    if g:
        import hashlib
        return 'd1:' + hashlib.sha256(g.encode('utf-8')).hexdigest()[:32]
    return 'direct_device_unlocked'

def device_label():
    host = ''
    try:
        host = socket.gethostname()
    except Exception:
        pass
    user = os.environ.get('USERNAME') or os.environ.get('USER') or ''
    return (host + (' / ' + user if user else '')).strip() or 'Direct PC'

_status = {
    'configured': True,
    'enforced': False,
    'active': True,
    'licensed': True,
    'unlimited': True,
    'reason': 'active',
    'plan': 'Permanent Unlimited (Direct Mode)',
    'key_masked': 'DIRECT-UNLOCKED',
    'device_label': device_label(),
    'expires_at': 'Permanent',
    'cooldown_until': None,
    'checked_at': time.time(),
}

def enforced():
    """Always return False so licensing gate is disabled."""
    return False

def is_active_cached():
    """Always active."""
    return True

def ensure_checked():
    pass

def activate(key=None):
    return {
        'ok': True,
        'active': True,
        'licensed': True,
        'plan': 'Permanent Unlimited (Direct Mode)',
        'message': 'Direct mode is permanently active'
    }

def deactivate():
    return {'ok': True, 'active': True}

def status():
    s = dict(_status)
    s['device_label'] = device_label()
    s['checked_at'] = time.time()
    return s

def check_download(series_id):
    """Authorise all downloads unconditionally."""
    return {
        'allowed': True,
        'licensed': True,
        'unlimited': True,
        'reason': 'direct_unlimited'
    }

def usage():
    return {
        'configured': True,
        'licensed': True,
        'unlimited': True,
        'plan': 'Permanent Unlimited (Direct Mode)',
        'free_limit': 999999,
        'free_used': 0,
        'remaining': 999999,
        'key_masked': 'DIRECT-UNLOCKED',
        'device_label': device_label(),
        'expires_at': 'Permanent'
    }

def init():
    """No background Supabase polling needed."""
    pass