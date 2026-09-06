import os

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"

# ==========================================
# 1. main.py
# ==========================================
main_code = r'''# -*- coding: utf-8 -*-
"""
SYD 8MOVIE PRO - Native Desktop Application Launcher (main.py)
--------------------------------------------------------------
- Launches FastAPI backend server on 127.0.0.1:8008.
- Closes/hides CMD console window on Windows for clean look.
- Opens native Edge App Mode window (chromeless desktop experience).
"""

import os
import sys
import time
import socket
import subprocess
import threading
import webbrowser
import ctypes

PORT = 8008
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}/"

def hide_console():
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0) # SW_HIDE
        except Exception:
            pass

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0

def run_server():
    import uvicorn
    # Make sure app directory is in sys.path
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    from app.server import app
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")

def find_edge_path():
    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None

def main():
    # 1. Start server if not running
    if not is_port_in_use(PORT):
        t = threading.Thread(target=run_server, daemon=True)
        t.start()

        # Wait for port to become available
        t0 = time.time()
        while time.time() - t0 < 10:
            if is_port_in_use(PORT):
                break
            time.sleep(0.3)

    # 2. Hide console if requested
    if "--no-hide" not in sys.argv:
        hide_console()

    # 3. Launch UI window
    edge_exe = find_edge_path()
    if edge_exe:
        app_args = [
            edge_exe,
            f"--app={URL}",
            "--window-size=1360,900",
            "--window-position=120,60"
        ]
        try:
            p = subprocess.Popen(app_args)
            p.wait()
            sys.exit(0)
        except Exception:
            webbrowser.open(URL)
    else:
        webbrowser.open(URL)

if __name__ == "__main__":
    main()
'''

# ==========================================
# 2. run.bat
# ==========================================
run_bat = r'''@echo off
chcp 65001 >nul
title SYD 8MOVIE PRO
cd /d "%~dp0"

python -c "import fastapi, uvicorn, requests" 2>nul
if %errorlevel% neq 0 (
    echo [SYD 8Movie] Installing dependencies...
    pip install -r requirements.txt
)

echo [SYD 8Movie] Starting SYD 8Movie Pro...
start "" pythonw main.py
exit
'''

# ==========================================
# 3. start_downloader.bat
# ==========================================
start_bat = r'''@echo off
chcp 65001 >nul
cd /d "%~dp0"
python main.py
pause
'''

# ==========================================
# 4. README.md
# ==========================================
readme_md = r'''# SYD 8MOVIE PRO (កម្មវិធីដោនឡូតរឿង & Poster 8Movie)

កម្មវិធីកម្រិតខ្ពស់សម្រាប់ទាញយក Poster និងវីដេអូរឿងភាគ Full HD ពីគេហទំព័រ **https://8movie.com** (八影短劇網) ដោយផ្ទាល់ ជាមួយទម្រង់រចនាដូចគ្នាទៅនឹង SYD-Downloader Pro។

## របៀបដំណើរការ (How to Run)
1. ចុចពីរដង (Double-click) លើ `run.bat` ឬ `start_downloader.bat`
2. កម្មវិធីនឹងបើកបង្អួច Native App ដោយស្វ័យប្រវត្ត ឬចូលទៅកាន់: `http://127.0.0.1:8008/`

## លក្ខណៈពិសេសចម្បង (Key Features)
- **ទម្រង់ដូច SYD-Downloader Pro 100%**:
  - Dark Mode ប្រណិត ជាមួយពណ៌ទឹកក្រូចមាស (Orange & Gold Glow)
  - ពុម្ពអក្សរខ្មែរស្រស់ស្អាត (Kantumruy Pro & Battambang)
  - ប៊ូតុង Category Chips រាងមូល: ឆ្លងភពបុរាណ, ស្នេហាទីក្រុង, សងសឹកបោកផ្ទុះ, ក្បាច់គុនអភិនីហារ, អាថ៌កំបាំងវេទមន្ត, រឿងថ្មីៗ, ចំណាត់ថ្នាក់កំពូល
  - Poster Cards ជាមួយពិន្ទុ Rating (★ 8.8), ចំនួនភាគ (55 ភាគ), ចំណងជើងដើម និងចំណងជើងបកប្រែជាភាសាខ្មែរ
- **ការទាញយក Poster HD (High-Resolution Poster Download)**:
  - ប៊ូតុង `🖼 Poster` លើកាតនីមួយៗ ទាញយករូប Poster ច្បាស់ត្រដែតភ្លាមៗ
  - រក្សាទុកដោយស្វ័យប្រវត្តក្នុង Folder នៃរឿងនីមួយៗ
- **ការទាញយកវីដេអូកម្រិត Full HD (1080p)**:
  - ប្រើប្រាស់ `ffmpeg` បច្ចេកវិទ្យា Stream Concatenation ដោយផ្ទាល់ លឿនរហ័ស និងរក្សាគុណភាព 100%
  - អាចទាញយកគ្រប់ភាគទាំងអស់ (Download All) ឬរើសភាគដែលចង់បាន (Download Selected)
- **កម្មវិធីចាក់វីដេអូសាកល្បងក្នុង App (In-App Video Player)**:
  - អាចចុចចាក់មើលភាគណាមួយភ្លាមៗដោយមិនចាំបាច់រង់ចាំ Download រួចរាល់ឡើយ
- **ប្រព័ន្ធគ្រប់គ្រងការ Download (Queue & Speed Indicator)**:
  - បង្ហាញភាគរយ %, ល្បឿន Download (MB/s), និងទំហំឯកសារ
  - ប៊ូតុង `📂 បើក Folder` ចូលទៅកាន់ទីតាំងរក្សាទុកក្នុងកុំព្យូទ័រ
- **បណ្ណាល័យមូលដ្ឋាន (Local Library)**:
  - ស្កេន និងបង្ហាញរឿងភាគដែលបានទាញយករួចជាស្រេចនៅលើម៉ាស៊ីន។
'''

with open(os.path.join(TARGET_DIR, 'main.py'), 'w', encoding='utf-8') as f:
    f.write(main_code)
print("Written: main.py")

with open(os.path.join(TARGET_DIR, 'run.bat'), 'w', encoding='utf-8') as f:
    f.write(run_bat)
print("Written: run.bat")

with open(os.path.join(TARGET_DIR, 'start_downloader.bat'), 'w', encoding='utf-8') as f:
    f.write(start_bat)
print("Written: start_downloader.bat")

with open(os.path.join(TARGET_DIR, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme_md)
print("Written: README.md")
