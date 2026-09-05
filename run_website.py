# -*- coding: utf-8 -*-
"""
SYD DOWNLOADER PRO - Website Launcher (run_website.py)
------------------------------------------------------
- Starts Offline Signer (port 9099) if not already running.
- Starts FastAPI Server (port 8000, bound to 0.0.0.0 for LAN & Localhost access).
- Automatically opens default Web Browser to http://localhost:8000/.
- Prints Localhost and Wi-Fi LAN IP for access on phones and other computers.
- Keeps web server active until Ctrl+C is pressed.
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
import atexit
import shutil

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, 'app')
SIGN_DIR = os.path.join(APP_DIR, 'sign')
SIGN_JAR = os.path.join(SIGN_DIR, 'unidbg-sign.jar')
DEFAULT_OUT = os.path.join(os.path.expanduser('~'), 'Videos', 'Hongguo')
DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', ROOT_DIR), 'HongguoDownloader')

SIGN_PORT = int(os.environ.get('HG_SIGN_PORT', '9099'))
WEB_PORT = int(os.environ.get('HG_PORT', '8000'))
CREATE_NO_WINDOW = 0x08000000

_spawned_procs = []

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

def _find_python():
    cands = [
        os.path.join(ROOT_DIR, 'python', 'python.exe'),
        os.path.join(ROOT_DIR, 'python', 'pythonw.exe'),
        sys.executable,
        shutil.which('python')
    ]
    for c in cands:
        if c and os.path.isfile(c):
            return c
    return sys.executable

def port_open(port, host='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((host, port)) == 0

def wait_port(port, timeout=25):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if port_open(port):
            return True
        time.sleep(0.4)
    return False

def get_primary_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def _cleanup():
    for p in _spawned_procs:
        try:
            p.terminate()
        except Exception:
            pass

atexit.register(_cleanup)

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DEFAULT_OUT, exist_ok=True)

    print("====================================================================", flush=True)
    print("  🚀 SYD DOWNLOADER PRO - WEBSITE MODE (ដំណើការ Website)", flush=True)
    print("====================================================================", flush=True)

    env = dict(os.environ)
    env['HG_LICENSE_DISABLED'] = '1'
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'
    env['SIGN_SERVER'] = f'http://127.0.0.1:{SIGN_PORT}'
    env['BIND_HOST'] = '0.0.0.0'  # Accept both Localhost and LAN/WiFi connections
    env['PORT'] = str(WEB_PORT)
    env['HG_OUT'] = DEFAULT_OUT
    cfg_file = os.path.join(DATA_DIR, 'dlconfig.json')
    if os.path.exists(cfg_file):
        try:
            import json
            saved_cfg = json.load(open(cfg_file, encoding='utf-8'))
            if saved_cfg.get('output_dir'):
                env['HG_OUT'] = saved_cfg['output_dir']
        except Exception:
            pass

    # 1. Start Offline Signer on port 9099 if not running
    if port_open(SIGN_PORT):
        print(f"  [✓] Signer Service កំពុងដំណើរការលើ Port {SIGN_PORT}", flush=True)
    else:
        print(f"  [*] កំពុងចាប់ផ្តើម Signer Service (Port {SIGN_PORT})...", flush=True)
        java_exe = _find_java()
        if java_exe and os.path.isfile(SIGN_JAR):
            p = subprocess.Popen([
                java_exe,
                '-Xmx512m',
                '-XX:+ExitOnOutOfMemoryError',
                '--add-opens', 'java.base/java.lang=ALL-UNNAMED',
                '-cp', 'unidbg-sign.jar',
                'com.hongguo.sign.FqTrace', 'serve', str(SIGN_PORT)
            ], cwd=SIGN_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            _spawned_procs.append(p)
            if wait_port(SIGN_PORT, 25):
                print(f"  [✓] Signer Service ដំណើរការបានជោគជ័យ។", flush=True)
            else:
                print(f"  [!] ការព្រមាន: Signer មិនឆ្លើយតបក្នុងពេលកំណត់។", flush=True)
        else:
            print("  [!] រកមិនឃើញ Java ឬ unidbg-sign.jar ឡើយ។", flush=True)

    # 2. Start FastAPI Server on port 8000 if not running
    if port_open(WEB_PORT):
        print(f"  [✓] Web Server កំពុងដំណើរការលើ Port {WEB_PORT}", flush=True)
    else:
        print(f"  [*] កំពុងចាប់ផ្តើម Web Server (Port {WEB_PORT})...", flush=True)
        py_exe = _find_python()
        server_script = os.path.join(APP_DIR, 'server.py')
        p = subprocess.Popen([py_exe, server_script], cwd=APP_DIR, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
        _spawned_procs.append(p)
        if wait_port(WEB_PORT, 25):
            print(f"  [✓] Web Server ដំណើរការបានជោគជ័យ។", flush=True)
        else:
            print(f"  [X] បរាជ័យ: Web Server មិនអាចចាប់ផ្តើមបានទេ។", flush=True)
            return 1

    # 3. Obtain Addresses
    lan_ip = get_primary_lan_ip()
    local_url = f"http://localhost:{WEB_PORT}/"
    lan_url = f"http://{lan_ip}:{WEB_PORT}/"
    docs_url = f"http://localhost:{WEB_PORT}/docs"

    print("====================================================================", flush=True)
    print(f"  🌐 WEBSITE ADDRESSES (អាសយដ្ឋាន Website):", flush=True)
    print(f"     👉 លើកុំព្យូទ័រផ្ទាល់ (Local PC):   {local_url}", flush=True)
    print(f"     👉 លើទូរស័ព្ទ / ឧបករណ៍ផ្សេង (WiFi): {lan_url}", flush=True)
    print(f"     👉 API Documentation:            {docs_url}", flush=True)
    print(f"     📁 ថតរក្សាទុកវីដេអូ:              {DEFAULT_OUT}", flush=True)
    print("====================================================================", flush=True)
    print("  ✓ កំពុងបើក Web Browser ទៅកាន់ Website ដោយស្វ័យប្រវត្តិ...", flush=True)
    
    try:
        webbrowser.open(local_url)
    except Exception:
        pass

    print("  ✓ Website កំពុងដំណើរការជាប់ជានិច្ច (Active)!", flush=True)
    print("  ⚠️  សូមកុំបិទផ្ទាំង CMD នេះ ដើម្បីកុំឱ្យ Website ដាច់។", flush=True)
    print("  (ចុច Ctrl + C លើផ្ទាំងនេះ នៅពេលអ្នកចង់បញ្ឈប់ Website)", flush=True)
    print("====================================================================", flush=True)

    try:
        while True:
            time.sleep(1)
            for p in _spawned_procs:
                if p.poll() is not None:
                    print(f"  [!] សេវាកម្មមួយបានឈប់ដំណើរការ។")
                    break
    except KeyboardInterrupt:
        print("\n  កំពុងបិទ Website... សូមរង់ចាំ។")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
