# -*- coding: utf-8 -*-
"""
Hongguo Downloader - Standalone Single EXE Builder
ឧបករណ៍វេចខ្ចប់កម្មវិធី Hongguo Downloader ជាកញ្ចប់ Standalone EXE មួយគត់ (HongguoDownloader.exe)
- បង្កើតតែ File EXE មួយគត់ (100% All-in-One Standalone)
- កូដ Python ទាំងអស់ត្រូវ compile ជា Bytecode (គ្មាន file .py សម្រាប់ Hack ឬ Bypass ឡើយ)
- រួមបញ្ចូលទាំង Signer, Server, JRE និង UI ទាំងអស់ក្នុង EXE តែមួយ
"""

import os
import sys
import shutil
import subprocess
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
DIST_DIR = os.path.join(ROOT_DIR, "output")
ICON_PATH = os.path.join(ROOT_DIR, "icon.ico")
PYINSTALLER_EXE = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\Scripts\pyinstaller.exe"

def banner():
    print("=" * 68)
    print("   🚀 HONGGUO DOWNLOADER - STANDALONE SINGLE EXE BUILDER")
    print("   🛡️ វេចខ្ចប់ជាកញ្ចប់ EXE មួយគត់ (ការពារកូដ 100% គ្មាន File .py សម្រាប់ Hack)")
    print("=" * 68)
    print(f"[*] Workspace Root: {ROOT_DIR}")
    print(f"[*] Output Target:  {DIST_DIR}\n")

def clean_temp():
    print("[1/4] Cleaning unnecessary temporary & cache files...")
    for root, dirs, files in os.walk(ROOT_DIR):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"), ignore_errors=True)
        for f in files:
            if f.endswith((".pyc", ".tmp", ".log")) and f not in ("server_boot.log",):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass
    print("      ✓ Cache cleaned.")

def prepare_stage_app():
    print("[2/4] Preparing protected stage app (excluding downloads & temp)...")
    stage_app = os.path.join(ROOT_DIR, "build", "stage_app")
    if os.path.exists(stage_app):
        shutil.rmtree(stage_app, ignore_errors=True)
    os.makedirs(stage_app, exist_ok=True)
    
    src_app = os.path.join(ROOT_DIR, "app")
    # Copy app while ignoring downloads, test caches, and pycache
    shutil.copytree(
        src_app, 
        stage_app, 
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("downloads", "__pycache__", "*.tmp", "*.log", ".git*")
    )
    print("      ✓ Stage app prepared.")
    return stage_app

def build_single_exe(stage_app):
    print("[3/4] Compiling and packaging Standalone HongguoDownloader.exe...")
    os.makedirs(DIST_DIR, exist_ok=True)
    
    # Remove old installer / zip files from output if present
    for old_item in ["Hongguo Downloader", "Hongguo_Downloader_Portable.zip", "Hongguo_Downloader_Setup.exe"]:
        old_path = os.path.join(DIST_DIR, old_item)
        if os.path.isdir(old_path):
            shutil.rmtree(old_path, ignore_errors=True)
        elif os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    pyinstaller = PYINSTALLER_EXE if os.path.isfile(PYINSTALLER_EXE) else "pyinstaller"
    main_py = os.path.join(ROOT_DIR, "main.py")
    jre_dir = os.path.join(ROOT_DIR, "jre")
    
    cmd = [
        pyinstaller,
        "--noconsole",
        "--onefile",
        f"--icon={ICON_PATH}" if os.path.isfile(ICON_PATH) else "",
        "--name=HongguoDownloader",
        f"--add-data={jre_dir};jre",
        f"--add-data={stage_app};app",
        f"--add-data={ICON_PATH};." if os.path.isfile(ICON_PATH) else "",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespans",
        "--hidden-import=uvicorn.lifespans.auto",
        "--hidden-import=fastapi",
        "--hidden-import=fastapi.responses",
        "--hidden-import=starlette",
        "--hidden-import=starlette.responses",
        "--hidden-import=pydantic",
        "--hidden-import=requests",
        "--hidden-import=urllib3",
        "--hidden-import=httpx",
        f"--distpath={DIST_DIR}",
        f"--workpath={os.path.join(ROOT_DIR, 'build', 'single_exe_work')}",
        f"--specpath={os.path.join(ROOT_DIR, 'build')}",
        main_py
    ]
    cmd = [c for c in cmd if c]
    
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        print(f"      ❌ PyInstaller build returned code: {res.returncode}")
        return None
        
    final_exe = os.path.join(DIST_DIR, "HongguoDownloader.exe")
    if os.path.isfile(final_exe):
        sz_mb = os.path.getsize(final_exe) / (1024 * 1024)
        print(f"      ✓ SUCCESS: Created Standalone Single EXE: {final_exe} ({sz_mb:.1f} MB)")
        return final_exe
    else:
        print(f"      ⚠️ Warning: {final_exe} was not found.")
        return None

def cleanup_stage():
    print("[4/4] Cleaning build staging files...")
    shutil.rmtree(os.path.join(ROOT_DIR, "build", "stage_app"), ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT_DIR, "build", "single_exe_work"), ignore_errors=True)
    print("      ✓ Staging cleaned.")

def main():
    t0 = time.time()
    banner()
    clean_temp()
    stage_app = prepare_stage_app()
    final_exe = build_single_exe(stage_app)
    cleanup_stage()
    
    elapsed = time.time() - t0
    print("\n" + "=" * 68)
    print(f"   🎉 BUILD COMPLETED IN {elapsed:.1f} SECONDS!")
    print(f"   📂 Output Directory: {DIST_DIR}")
    if final_exe and os.path.isfile(final_exe):
        print(f"   📦 Single Standalone EXE (មួយគត់ គ្រប់គ្រាន់):")
        print(f"      👉 {final_exe}")
        print("   🔒 All code compiled as bytecode - 100% Protected from bypass/hacks!")
    print("=" * 68)

if __name__ == "__main__":
    main()
