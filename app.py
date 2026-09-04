# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-08-31 16:05:02 UTC (1788192302)

global _job
global _singleton
# ***<module>: Failure: Different bytecode
"""Hongguo Downloader - native desktop app launcher (windowless).\n\nRuns everything hidden - the offline signer (javaw, no console) and the API\nserver (pythonw, no console, logs to a file) - and shows the UI in its OWN\nchromeless app-mode window using the WebView engine built into Windows\n(Edge/WebView2, always present). No browser tabs, no address bar, no console\nwindows. The app\'s own \'Console\' panel is the log view.\n\nLaunched via pythonw.exe so the launcher itself has no console either.\n"""
import os
import sys
import time
import socket
import subprocess
import ctypes
import atexit
import shutil
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, 'app')
JAVAW = os.path.join(HERE, 'jre', 'bin', 'javaw.exe')
PYW = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
SIGN_DIR = os.path.join(APP, 'sign')
SIGN_PORT = int(os.environ.get('HG_SIGN_PORT', '9099'))
WEB_PORT = int(os.environ.get('HG_PORT', '8000'))
DEFAULT_OUT = os.path.join(os.path.expanduser('~'), 'Videos', 'Hongguo')
DATA = os.path.join(os.environ.get('LOCALAPPDATA', HERE), 'HongguoDownloader')
CREATE_NO_WINDOW = 134217728
NO_WINDOW = os.environ.get('HG_NO_WINDOW') == '1'
def _msgbox(text, title='Hongguo Downloader'):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, title, 16)
    except Exception:
        return None
def port_open(port, host='127.0.0.1'):
    with socket.socket() as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0
def wait_port(port, timeout):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if port_open(port):
            return True
        time.sleep(0.4)
    return False
def _dlog(logf, msg):
    try:
        logf.write('[launch] %s\n' % msg)
        logf.flush()
    except Exception:
        return None
def _probe_web(port):
    """Our server answers /dl/status with a JSON object carrying \'running\'."""
    try:
        import urllib.request
        import json as _json
        with urllib.request.urlopen('http://127.0.0.1:%d/dl/status' % port, timeout=3) as r:
            d = _json.loads(r.read().decode('utf-8', 'ignore'))
        return isinstance(d, dict) and 'running' in d
    except Exception:
        return False
def _probe_sign(port):
    """A healthy signer returns signed headers (no \'error\') for a canned /sign request."""
    try:
        import urllib.request
        import json as _json
        body = _json.dumps({'url': 'https://api5-normal-sinfonlinec.fqnovel.com/reading/bookapi/search/page/v/?query=probe&aid=8662', 'headers': {'user-agent': 'com.phoenix.read.oversea.gp/72932'}}).encode()
        req = urllib.request.Request('http://127.0.0.1:%d/sign' % port, data=body, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=8) as r:
            d = _json.loads(r.read().decode('utf-8', 'ignore'))
        return isinstance(d, dict) and 'error' not in d
    except Exception:
        return False
def _port_pid(port):
    try:
        out = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=6).stdout
        for ln in out.splitlines():
            p = ln.split()
            if len(p) >= 5 and p[0].upper() == 'TCP' and (p[3].upper() == 'LISTENING') and p[1].endswith(':%d' % port):
                return int(p[(-1)])
    except Exception:
        pass
    return 0
def _proc_image(pid):
    try:
        import csv
        import io as _io
        out = subprocess.run(['tasklist', '/FI', 'PID eq %d' % pid, '/NH', '/FO', 'CSV'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=6).stdout
        for row in csv.reader(_io.StringIO(out)):
            if row and row[0].lower().endswith('.exe'):
                return row[0]
    except Exception:
        pass
    return ''
def _kill_pid(pid):
    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], capture_output=True, creationflags=CREATE_NO_WINDOW, timeout=6)
    except Exception:
        return None
def _free_port(start):
    for p in range(start, start + 80):
        try:
            with socket.socket() as s:
                s.bind(('127.0.0.1', p))
                return p
        except Exception:
            continue
    return start

def _resolve_port(port, kind, our_images, logf):
    """Return (port_to_use, healthy_already). If a HEALTHY instance of ours already holds the default
    port -> reuse it. If an UNHEALTHY process of ours holds it (a zombie) -> kill it and keep the port.
    If a FOREIGN process holds it -> fall back to the next free port."""
    probe = _probe_web if kind == 'web' else _probe_sign
    if not port_open(port):
        return (port, False)
    if probe(port):
        _dlog(logf, '%s: healthy instance already on %d -> reuse' % (kind, port))
        return (port, True)
    pid = _port_pid(port)
    img = _proc_image(pid) if pid else ''
    if img and img.lower() in our_images:
        _dlog(logf, '%s: unhealthy zombie %s (pid %d) on %d -> killing' % (kind, img, pid, port))
        _kill_pid(pid)
        for _ in range(25):
            if not port_open(port):
                break
            time.sleep(0.3)
        if not port_open(port):
            return (port, False)
    newp = _free_port(port + 1)
    _dlog(logf, '%s: port %d held by %s (pid %s) -> falling back to %d' % (kind, port, img or '?', pid or '?', newp))
    return (newp, False)

_singleton = None

def _acquire_singleton():
    """Take a session-scoped Windows named mutex. Returns the handle if we're the FIRST instance,
    None if another instance already holds it, or a truthy sentinel if the check can't run (never
    block startup on an error). Windows releases the mutex automatically when this process exits,
    so a crash can never leave a stale lock (unlike a lock file)."""
    try:
        k = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183
        h = k.CreateMutexW(None, False, 'HongguoDownloader.SingleInstance')
        if not h:
            return 'nomutex'
        if k.GetLastError() == ERROR_ALREADY_EXISTS:
            k.CloseHandle(h)
            return None
        return h
    except Exception:
        return 'nomutex'

def _focus_existing():
    """Bring the already-running app's chromeless window to the foreground. Prefers a window titled
    'Hongguo Downloader'; falls back to the localhost host title (the --app window is renamed to the
    URL host on reload). Best-effort -- if the window isn't up yet, the first instance shows it soon."""
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
                    if 'Hongguo Downloader' in title:
                        matches.append((0, hwnd))
                    elif '127.0.0.1' in title or 'localhost' in title:
                        matches.append((1, hwnd))
            return True
        u.EnumWindows(WNDENUMPROC(_enum), 0)
        matches.sort(key=lambda x: x[0])
        if matches:
            hwnd = matches[0][1]
            u.ShowWindow(hwnd, 9)
            u.SetForegroundWindow(hwnd)
            return True
    except Exception:
        pass
    return False

_job = None

def _make_job():
    global _job
    try:
        import ctypes.wintypes as wt
        k = ctypes.windll.kernel32
        _job = k.CreateJobObjectW(None, None)
        class BASIC(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64), ('LimitFlags', wt.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t), ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wt.DWORD), ('Affinity', ctypes.c_size_t), ('PriorityClass', wt.DWORD), ('SchedulingClass', wt.DWORD)]
        class IOC(ctypes.Structure):
            _fields_ = [('a', ctypes.c_uint64)] * 6
        class EXT(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', BASIC), ('IoInfo', IOC), ('ProcessMemoryLimit', ctypes.c_size_t), ('JobMemoryLimit', ctypes.c_size_t), ('PeakProcessMemoryUsed', ctypes.c_size_t), ('PeakJobMemoryUsed', ctypes.c_size_t)]
        info = EXT()
        info.BasicLimitInformation.LimitFlags = 8192
        k.SetInformationJobObject(_job, 9, ctypes.byref(info), ctypes.sizeof(info))
    except Exception:
        _job = None

def _assign(pid):
    if not _job:
        return None
    try:
        k = ctypes.windll.kernel32
        h = k.OpenProcess(2035711, False, pid)
        if h:
            k.AssignProcessToJobObject(_job, h)
            k.CloseHandle(h)
            return None
        return None
    except Exception:
        return None

_procs = []

def _spawn(cmd, cwd, env, logf):
    p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=logf, stderr=logf, creationflags=CREATE_NO_WINDOW)
    _procs.append(p)
    _assign(p.pid)
    return p

def _shutdown_all():
    global _procs
    for p in list(_procs):
        try:
            p.terminate()
        except Exception:
            pass
    time.sleep(0.3)
    for p in list(_procs):
        try:
            if p.poll() is None:
                p.kill()
        except Exception:
            pass

@atexit.register
def _cleanup():
    _shutdown_all()

_WIN_MARKERS = ('Hongguo Downloader', '127.0.0.1', 'localhost')
_BROWSER_IMAGES = ('chrome.exe', 'msedge.exe')

def _window_present():
    """True = our app window exists, False = it's gone, None = couldn't tell.
    None is returned on any tasklist failure so a transient hiccup is never
    mistaken for the window closing."""
    try:
        out = subprocess.run(['tasklist', '/v', '/fo', 'csv', '/nh'], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, encoding='utf-8', errors='ignore').stdout
        if not out:
            return None
        import csv
        import io
        rows = list(csv.reader(io.StringIO(out)))
        for r in rows:
            if len(r) >= 9:
                image, title = (r[0].lower(), r[-1])
                if image in _BROWSER_IMAGES and title and (title != 'N/A') and any((m in title for m in _WIN_MARKERS)):
                    return True
        return False
    except Exception:
        return None

def _screen_fit(pref_w=1240, pref_h=860, margin_w=24, margin_h=48):
    """Compute an --app window size + position (in DIP — the unit Chrome/Edge use) that always
    fits the primary monitor's WORK AREA. Keeps the UI from being clipped on displays scaled to
    125/150/200% or on small laptops. Returns ("W,H", "X,Y"), or (None, None) if detection fails."""
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
    try:
        if not u.SystemParametersInfoW(48, 0, ctypes.byref(r), 0):
            return (None, None)
        phys_w, phys_h = (r.right - r.left, r.bottom - r.top)
        try:
            scale = u.GetDpiForSystem() / 96.0
        except Exception:
            scale = 1.0
        if scale <= 0:
            scale = 1.0
        dip_w, dip_h = (int(phys_w / scale), int(phys_h / scale))
        w = max(360, min(pref_w, dip_w - margin_w))
        h = max(480, min(pref_h, dip_h - margin_h))
        x = max(0, (dip_w - w) // 2)
        y = max(0, (dip_h - h) // 2)
        return ('%d,%d' % (w, h), '%d,%d' % (x, y))
    except Exception:
        return (None, None)
def _find_browser():
    cands = [os.path.expandvars('%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe'), os.path.expandvars('%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe'), shutil.which('msedge'), os.path.expandvars('%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe'), os.path.expandvars('%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe'), shutil.which('chrome')]
    for c in cands:
        if c and os.path.exists(c):
            return c
def main():
    global _singleton
    os.makedirs(DATA, exist_ok=True)
    _singleton = _acquire_singleton()
    if _singleton is None:
        if _focus_existing() and _probe_web(WEB_PORT):
            return 0
        for _ in range(6):
            time.sleep(0.5)
            _singleton = _acquire_singleton()
            if _singleton is not None:
                break
            if _focus_existing() and _probe_web(WEB_PORT):
                return 0
        if _singleton is None:
            if _focus_existing():
                return 0
            if _probe_web(WEB_PORT):
                url = 'http://127.0.0.1:%d/dl' % WEB_PORT
                browser = _find_browser()
                if browser:
                    prof = os.path.join(DATA, 'window')
                    size, pos = _screen_fit()
                    args = [browser, '--app=' + url, '--window-size=' + (size or '1240,860')]
                    if pos:
                        args.append('--window-position=' + pos)
                    args += ['--user-data-dir=' + prof, '--no-first-run', '--no-default-browser-check', '--disable-features=Translate']
                    subprocess.Popen(args)
                    return 0
                else:
                    import webbrowser
                    webbrowser.open(url)
                    return 0
            for port in (WEB_PORT, SIGN_PORT):
                pid = _port_pid(port)
                if pid:
                    _kill_pid(pid)
            time.sleep(0.5)
    if not os.path.exists(os.path.join(SIGN_DIR, 'unidbg-sign.jar')):
        _msgbox('The app is incomplete: missing sign\\unidbg-sign.jar.')
        return 1
    if not os.path.exists(JAVAW):
        _msgbox('The app is incomplete: missing jre\\bin\\javaw.exe.')
        return 1
    _make_job()
    logf = open(os.path.join(DATA, 'app.log'), 'a', encoding='utf-8', errors='ignore')
    logf.write('\n===== %s launch =====\n' % time.strftime('%Y-%m-%d %H:%M:%S'))
    logf.flush()
    sign_port, sign_ok = _resolve_port(SIGN_PORT, 'sign', ('javaw.exe', 'java.exe'), logf)
    web_port, web_ok = _resolve_port(WEB_PORT, 'web', ('pythonw.exe', 'python.exe'), logf)
    env = dict(os.environ)
    env['HG_LICENSE_DISABLED'] = '1'
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    env['SIGN_SERVER'] = 'http://127.0.0.1:%d' % sign_port
    env['BIND_HOST'] = '127.0.0.1'
    env['PORT'] = str(web_port)
    env.setdefault('HG_OUT', DEFAULT_OUT)
    try:
        os.makedirs(env['HG_OUT'], exist_ok=True)
    except Exception:
        pass
    if not sign_ok:
        _spawn([JAVAW, '-Xmx512m', '-XX:+ExitOnOutOfMemoryError', '--add-opens', 'java.base/java.lang=ALL-UNNAMED', '-cp', 'unidbg-sign.jar', 'com.hongguo.sign.FqTrace', 'serve', str(sign_port)], SIGN_DIR, env, logf)
        if not wait_port(sign_port, 90):
            _msgbox('The signer did not start. See app.log in\n%s' % DATA)
            return 1
    if not web_ok:
        _server = os.path.join(APP, 'server.py')
        if not os.path.exists(_server):
            _server = os.path.join(APP, 'server.pyc')
        _spawn([PYW, _server], APP, env, logf)
        if not wait_port(web_port, 45):
            _msgbox('The app server did not start. See app.log in\n%s' % DATA)
            return 1
    url = 'http://127.0.0.1:%d/dl' % web_port
    if NO_WINDOW:
        try:
            while _procs and _procs[-1].poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        _shutdown_all()
        return 0
    browser = _find_browser()
    if browser:
        prof = os.path.join(DATA, 'window')
        size, pos = _screen_fit()
        args = [browser, '--app=' + url, '--window-size=' + (size or '1240,860')]
        if pos:
            args.append('--window-position=' + pos)
        args += ['--user-data-dir=' + prof, '--no-first-run', '--no-default-browser-check', '--disable-features=Translate']
        bproc = subprocess.Popen(args)
        appeared = False
        for _ in range(60):
            if bproc.poll() is not None:
                break
            if _window_present() is True:
                appeared = True
                break
            time.sleep(0.5)
        if appeared:
            misses = 0
            while True:
                time.sleep(1)
                st = _window_present()
                if st is False:
                    misses += 1
                    if misses >= 2:
                        break
                else:
                    misses = 0
        else:
            import webbrowser
            webbrowser.open(url)
            while _procs and _procs[-1].poll() is None:
                time.sleep(1)
    else:
        import webbrowser
        webbrowser.open(url)
        while _procs and _procs[-1].poll() is None:
            time.sleep(1)
    _shutdown_all()
    return 0
if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        _msgbox('Hongguo Downloader failed to start:\n%s' % e)
        sys.exit(1)