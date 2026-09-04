# -*- coding: utf-8 -*-
"""
SYD DOWNLOADER PRO - Native Desktop Application (main.py)
---------------------------------------------------------
- Pure native Python entry point (main.py).
- Closes/hides any CMD console window immediately on startup (Zero Console Flicker).
- No pywebview dependency (eliminates all CoreWebView2Controller COM crashes).
- Native chromeless Edge App Window with custom title, logo, and screen fitting.
- Offline Unidbg Signer (port 9099) & FastAPI Server (port 8000, 0.0.0.0 for LAN access).
- Windows Job Object ensures clean background service cleanup on window exit.
- Single Instance Named Mutex prevents duplicate windows.
"""

import os
import sys

# Ensure Python executable folder is in DLL search path
_py_dir = os.path.dirname(sys.executable)
if hasattr(os, 'add_dll_directory') and os.path.isdir(_py_dir):
    try:
        os.add_dll_directory(_py_dir)
    except Exception:
        pass
os.environ['PATH'] = _py_dir + os.pathsep + os.environ.get('PATH', '')

import time
import socket
import subprocess
import atexit
import shutil

# 1. HIDE ANY CMD CONSOLE WINDOW IMMEDIATELY
try:
    import ctypes
    if sys.platform == 'win32':
        _hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if _hwnd:
            ctypes.windll.user32.ShowWindow(_hwnd, 0)  # 0 = SW_HIDE
except Exception:
    ctypes = None

# Force UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Determine Directories
if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

APP_DIR = os.path.join(ROOT_DIR, 'app')
SIGN_DIR = os.path.join(APP_DIR, 'sign')
SIGN_JAR = os.path.join(SIGN_DIR, 'unidbg-sign.jar')
DEFAULT_OUT = os.path.join(os.path.expanduser('~'), 'Videos', 'Hongguo')
DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ROOT_DIR), 'HongguoDownloader')

SIGN_PORT = int(os.environ.get('HG_SIGN_PORT', '9099'))
WEB_PORT = int(os.environ.get('HG_PORT', '8000'))
CREATE_NO_WINDOW = 0x08000000

# Locate bundled JRE javaw (no console) or java inside SYD-Downloader Pro
def _find_java():
    cands = [
        os.path.join(ROOT_DIR, 'jre', 'bin', 'javaw.exe'),
        os.path.join(ROOT_DIR, 'jre', 'bin', 'java.exe'),
        shutil.which('javaw'),
        shutil.which('java')
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None

# Locate pythonw (windowless) or python inside SYD-Downloader Pro
def _find_pythonw():
    cands = [
        os.path.join(ROOT_DIR, 'python', 'pythonw.exe'),
        os.path.join(ROOT_DIR, 'python', 'python.exe'),
        os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'),
        sys.executable,
        shutil.which('pythonw'),
        shutil.which('python')
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return sys.executable

# Locate Edge or Chrome browser for native app-mode window
def _find_browser():
    cands = [
        os.path.expandvars('%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe'),
        os.path.expandvars('%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe'),
        shutil.which('msedge'),
        os.path.expandvars('%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe'),
        os.path.expandvars('%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe'),
        shutil.which('chrome')
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return None

def get_primary_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def port_open(port, host='127.0.0.1'):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0

def wait_port(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if port_open(port):
            return True
        time.sleep(0.3)
    return False

# Windows Job Object for automatic child process termination
_job = None
def _make_job():
    global _job
    try:
        import ctypes.wintypes as wt
        k = ctypes.windll.kernel32
        _job = k.CreateJobObjectW(None, None)
        class BASIC(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64),
                        ('LimitFlags', wt.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
                        ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wt.DWORD),
                        ('Affinity', ctypes.c_size_t), ('PriorityClass', wt.DWORD), ('SchedulingClass', wt.DWORD)]
        class IOC(ctypes.Structure):
            _fields_ = [('a', ctypes.c_uint64)] * 6
        class EXT(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', BASIC), ('IoInfo', IOC),
                        ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t),
                        ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
        info = EXT()
        info.BasicLimitInformation.LimitFlags = 8192  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        k.SetInformationJobObject(_job, 9, ctypes.byref(info), ctypes.sizeof(info))
    except Exception:
        _job = None

def _assign_process(pid):
    if not _job:
        return
    try:
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1F0FFF, False, pid)
        if h:
            k.AssignProcessToJobObject(_job, h)
            k.CloseHandle(h)
    except Exception:
        pass

_procs = []
def _spawn_hidden(cmd, cwd, env, logf=None):
    p = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdout=logf or subprocess.DEVNULL,
        stderr=logf or subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW
    )
    _procs.append(p)
    _assign_process(p.pid)
    return p

def _cleanup_procs():
    global _procs
    for p in list(_procs):
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(0.2)
    for p in list(_procs):
        try:
            if p.poll() is None:
                p.kill()
        except Exception:
            pass

atexit.register(_cleanup_procs)

# Single instance check via Windows Named Mutex
_singleton_handle = None
def _acquire_singleton():
    global _singleton_handle
    try:
        k = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183
        h = k.CreateMutexW(None, False, 'SYDDownloaderPro.Main.SingleInstance')
        if not h:
            return True
        if k.GetLastError() == ERROR_ALREADY_EXISTS:
            k.CloseHandle(h)
            return False
        _singleton_handle = h
        return True
    except Exception:
        return True

def _focus_existing():
    try:
        from ctypes import wintypes
        u = ctypes.windll.user32
        matches = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def _enum(hwnd, _l):
            if u.IsWindowVisible(hwnd):
                ln = u.GetWindowTextLengthW(hwnd)
                if ln > 0:
                    buf = ctypes.create_unicode_buffer(ln + 1)
                    u.GetWindowTextW(hwnd, buf, ln + 1)
                    title = buf.value or ''
                    if 'SYD DOWNLOADER' in title or 'Hongguo Downloader' in title or '127.0.0.1:8000' in title:
                        matches.append(hwnd)
            return True
        u.EnumWindows(WNDENUMPROC(_enum), 0)
        if matches:
            hwnd = matches[0]
            u.ShowWindow(hwnd, 9)  # SW_RESTORE
            u.SetForegroundWindow(hwnd)
            return True
    except Exception:
        pass
    return False

# Screen geometry calculation for Main Window
def _calculate_screen_fit(pref_w=1280, pref_h=850):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    u = ctypes.windll.user32
    class RECT(ctypes.Structure):
        _fields_ = [('left', ctypes.c_long), ('top', ctypes.c_long), ('right', ctypes.c_long), ('bottom', ctypes.c_long)]
    r = RECT()
    if u.SystemParametersInfoW(48, 0, ctypes.byref(r), 0):
        phys_w, phys_h = (r.right - r.left, r.bottom - r.top)
        try:
            scale = u.GetDpiForSystem() / 96.0
        except Exception:
            scale = 1.0
        scale = max(0.5, scale)
        dip_w, dip_h = (int(phys_w / scale), int(phys_h / scale))
        w = max(960, min(pref_w, dip_w - 30))
        h = max(620, min(pref_h, dip_h - 50))
        x = max(0, (dip_w - w) // 2)
        y = max(0, (dip_h - h) // 2)
        return w, h, x, y
    return pref_w, pref_h, 50, 50

# Check if application window is still open
def _window_is_active():
    try:
        from ctypes import wintypes
        u = ctypes.windll.user32
        active = [False]
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def _enum(hwnd, _l):
            if u.IsWindowVisible(hwnd):
                ln = u.GetWindowTextLengthW(hwnd)
                if ln > 0:
                    buf = ctypes.create_unicode_buffer(ln + 1)
                    u.GetWindowTextW(hwnd, buf, ln + 1)
                    title = buf.value or ''
                    if 'SYD DOWNLOADER' in title or 'Hongguo Downloader' in title or '127.0.0.1:8000' in title:
                        active[0] = True
                        return False
            return True
        u.EnumWindows(WNDENUMPROC(_enum), 0)
        return active[0]
    except Exception:
        return True

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DEFAULT_OUT, exist_ok=True)

    # Check for single instance
    if not _acquire_singleton():
        if _focus_existing():
            return 0
        time.sleep(1)
        if not _acquire_singleton():
            return 0

    _make_job()

    log_path = os.path.join(DATA_DIR, 'main.log')
    try:
        logf = open(log_path, 'a', encoding='utf-8', errors='ignore')
        logf.write(f"\n===== SYD Launch: {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
        logf.flush()
    except Exception:
        logf = None

    # Configure Environment
    env = dict(os.environ)
    env['HG_LICENSE_DISABLED'] = '1'
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    env['SIGN_SERVER'] = f'http://127.0.0.1:{SIGN_PORT}'
    env['BIND_HOST'] = '0.0.0.0'  # Support simultaneous Localhost and WiFi/LAN network access
    env['PORT'] = str(WEB_PORT)
    env['HG_OUT'] = DEFAULT_OUT

    # 1. Start Offline Signer silently if not running
    if not port_open(SIGN_PORT):
        java_exe = _find_java()
        if java_exe and os.path.isfile(SIGN_JAR):
            _spawn_hidden([
                java_exe,
                '-Xmx512m',
                '-XX:+ExitOnOutOfMemoryError',
                '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
                '-cp', 'unidbg-sign.jar',
                'com.hongguo.sign.FqTrace', 'serve', str(SIGN_PORT)
            ], SIGN_DIR, env, logf)
            wait_port(SIGN_PORT, 20)

    # 2. Start FastAPI Server silently if not running
    server_script = os.path.join(APP_DIR, 'server.py')
    if not port_open(WEB_PORT):
        python_exe = _find_pythonw()
        _spawn_hidden([python_exe, server_script], APP_DIR, env, logf)
        wait_port(WEB_PORT, 25)

    main_url = f"http://127.0.0.1:{WEB_PORT}/"
    w, h, x, y = _calculate_screen_fit(1280, 850)

    # 3. Launch Native Chromeless App Window (Edge / Chrome) - ZERO COM errors, ZERO pywebview
    browser = _find_browser()
    if browser:
        prof = os.path.join(DATA_DIR, 'app_profile')
        args = [
            browser,
            f'--app={main_url}',
            f'--window-size={w},{h}',
            f'--window-position={x},{y}',
            f'--user-data-dir={prof}',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-features=Translate'
        ]
        bproc = subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        _assign_process(bproc.pid)

        # Monitor window lifecycle - exit when user closes the app window
        time.sleep(2)
        while True:
            time.sleep(1)
            # If browser process terminated, or window is closed
            if bproc.poll() is not None:
                # Extra check in case Edge ran via background singleton
                if not _window_is_active():
                    break
            else:
                if not _window_is_active():
                    # Give user 1 grace second in case of modal reload
                    time.sleep(1)
                    if not _window_is_active():
                        break
    else:
        import webbrowser
        webbrowser.open(main_url)
        while port_open(WEB_PORT):
            time.sleep(1)

    _cleanup_procs()
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        try:
            ctypes.windll.user32.MessageBoxW(0, f"SYD Downloader Pro encountered an error:\n{e}", "SYD Downloader Pro", 16)
        except Exception:
            pass
        sys.exit(1)
