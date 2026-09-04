# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\launcher.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-07-28 06:30:28 UTC (1785220228)

global _job
# ***<module>: Failure: Different bytecode
"""Hongguo Downloader — launcher.\n\nStarts the offline unidbg signer (bundled JRE) and the API server (this bundled\nPython), then opens the browser to the downloader UI. No emulator, no internet\nservice, no login required — signing is done locally on the JVM.\n\nLayout (all siblings of this file):\n    launcher.py\n    python/                 bundled embeddable CPython (runs this script)\n    jre/bin/java.exe        bundled Temurin 17\n    app/                    server.py, sign/unidbg-sign.jar, capture/fq_oversea/, web/, ...\n"""
import os
import sys
import time
import socket
import subprocess
import webbrowser
import ctypes
import atexit

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, 'app')
JAVA = os.path.join(HERE, 'jre', 'bin', 'java.exe')
SIGN_DIR = os.path.join(APP, 'sign')
SIGN_PORT = int(os.environ.get('HG_SIGN_PORT', '9099'))
WEB_PORT = int(os.environ.get('HG_PORT', '8000'))
DEFAULT_OUT = os.path.join(os.path.expanduser('~'), 'Videos', 'Hongguo')

def log(m):
    try:
        print(m, flush=True)
    except Exception:
        try:
            print(str(m).encode('ascii', 'replace').decode('ascii'), flush=True)
        except Exception:
            pass
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
            _fields_ = [('r', ctypes.c_uint64), ('w', ctypes.c_uint64), ('o', ctypes.c_uint64), ('rb', ctypes.c_uint64), ('wb', ctypes.c_uint64), ('ob', ctypes.c_uint64)]
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
CREATE_NO_WINDOW = 0x08000000
def _spawn(cmd, cwd, env):
    p = subprocess.Popen(cmd, cwd=cwd, env=env, creationflags=512 | CREATE_NO_WINDOW)
    _procs.append(p)
    _assign(p.pid)
    return p
@atexit.register
def _cleanup():
    for p in _procs:
        try:
            p.terminate()
        except Exception:
            pass
def main():
    if not os.path.exists(JAVA):
        log('[X] missing jre\\bin\\java.exe — the package is incomplete.')
        time.sleep(6)
        return 1
    else:
        if not os.path.exists(os.path.join(SIGN_DIR, 'unidbg-sign.jar')):
            log('[X] missing app\\sign\\unidbg-sign.jar — the package is incomplete.')
            time.sleep(6)
            return 1
        else:
            env = dict(os.environ)
            env['HG_LICENSE_DISABLED'] = '1'
            env['PYTHONUTF8'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            env['SIGN_SERVER'] = 'http://127.0.0.1:%d' % SIGN_PORT
            env['BIND_HOST'] = '127.0.0.1'
            env['PORT'] = str(WEB_PORT)
            env.setdefault('HG_OUT', DEFAULT_OUT)
            try:
                os.makedirs(env['HG_OUT'], exist_ok=True)
            except Exception:
                pass
            log('====================================================')
            log('   红果 · Hongguo Downloader')
            log('====================================================')
            if port_open(SIGN_PORT):
                log('[=] signer already running on :%d' % SIGN_PORT)
            else:
                log('[1/3] starting offline signer (first boot ~10-20s) ...')
                _spawn([JAVA, '-Xmx512m', '-XX:+ExitOnOutOfMemoryError', '--add-opens', 'java.base/java.lang=ALL-UNNAMED', '-cp', 'unidbg-sign.jar', 'com.hongguo.sign.FqTrace', 'serve', str(SIGN_PORT)], cwd=SIGN_DIR, env=env)
                if not wait_port(SIGN_PORT, 90):
                    log('[X] the signer did not come up in time.')
                    time.sleep(6)
                    return 1
            log('[2/3] starting the app ...')
            _spawn([sys.executable, os.path.join(APP, 'server.py')], cwd=APP, env=env)
            if not wait_port(WEB_PORT, 45):
                log('[X] the app server did not come up in time.')
                time.sleep(6)
                return 1
            else:
                url = 'http://127.0.0.1:%d/dl' % WEB_PORT
                log('[3/3] ready.')
                log('----------------------------------------------------')
                log('   Open:    %s' % url)
                log('   Videos:  %s' % env['HG_OUT'])
                log('----------------------------------------------------')
                log('Keep this window open while you download. Close it to stop.')
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                try:
                    while True:
                        time.sleep(1)
                        if _procs and _procs[(-1)].poll() is not None:
                                log('[!] the app server stopped.')
                                break
                except KeyboardInterrupt:
                    log('stopping ...')
    return 0
if __name__ == '__main__':
    sys.exit(main())