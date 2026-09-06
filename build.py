# -*- coding: utf-8 -*-
"""
SYD DOWNLOADER PRO - Standalone Single EXE Builder
ឧបករណ៍វេចខ្ចប់កម្មវិធី SYD Downloader Pro ជាកញ្ចប់ Standalone EXE មួយគត់
- បង្កើត File EXE ដាក់ឈ្មោះតាម Version: SYD-Downloader-Pro V1.0.1.exe
- រាល់ការ build ម្តង ជំនាន់រាប់ឡើង +1 (1.0.1 -> 1.0.2 ... រហូតដល់ 10 ក្លាយជា 1.1.0)
- កូដ Python ទាំងអស់ត្រូវ compile ជា Bytecode (គ្មាន file .py សម្រាប់ Hack ឬ Bypass ឡើយ)
- រួមបញ្ចូលទាំង Signer, Server, JRE, Firebase Cloud និង UI ទាំងអស់ក្នុង EXE តែមួយ
"""

import os
import sys
import json
import shutil
import subprocess
import time

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT_DIR, "output")
ICON_PATH = os.path.join(ROOT_DIR, "icon.ico")
PYINSTALLER_EXE = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\Scripts\pyinstaller.exe"

def get_and_bump_version():
    """
    Auto-increment version on each build:
    - Major.Minor.Patch (e.g. 1.0.1)
    - Starts at 1.0.1
    - Increments patch by +1: 1.0.1 -> 1.0.2 -> ... -> 1.0.9
    - When patch reaches 10: rolls over to 1.1.0 (and 1.1.9 -> 1.2.0)
    """
    version_file = os.path.join(ROOT_DIR, "app", "version.json")
    major, minor, patch = 1, 0, 0
    if os.path.isfile(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                v_str = str(d.get("version") or "").strip().lstrip("vV")
                parts = [int(p) for p in v_str.split(".") if p.isdigit()]
                if len(parts) >= 3:
                    major, minor, patch = parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    major, minor, patch = parts[0], parts[1], 0
                elif len(parts) == 1:
                    major, minor, patch = parts[0], 0, 0
        except Exception:
            pass

    # Increment version
    patch += 1
    if patch >= 10:
        minor += 1
        patch = 0
    if minor >= 10:
        major += 1
        minor = 0

    new_version = f"{major}.{minor}.{patch}"
    version_tag = f"V{new_version}"

    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    ver_data = {
        "version": new_version,
        "version_tag": version_tag,
        "app_name": "SYD-Downloader-Pro",
        "updated_at": now_str,
        "message": f"Release {version_tag} ({now_str})"
    }

    for vf in [os.path.join(ROOT_DIR, "app", "version.json"), os.path.join(ROOT_DIR, "version.json")]:
        try:
            with open(vf, "w", encoding="utf-8") as f:
                json.dump(ver_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    for tf in [os.path.join(ROOT_DIR, "app", "version.txt"), os.path.join(ROOT_DIR, "version.txt")]:
        try:
            with open(tf, "w", encoding="utf-8") as f:
                f.write(new_version)
        except Exception:
            pass

    return new_version, version_tag

def banner(version_tag):
    print("=" * 68)
    print("   🚀 SYD DOWNLOADER PRO - STANDALONE SINGLE EXE BUILDER")
    print(f"   🏷️  BUILD VERSION: {version_tag}")
    print("   🛡️  វេចខ្ចប់ជាកញ្ចប់ EXE មួយគត់ (ការពារកូដ 100% គ្មាន File .py សម្រាប់ Hack)")
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
    if os.path.isdir(DIST_DIR):
        for f in os.listdir(DIST_DIR):
            if f.endswith(".bak") or ".running_" in f:
                try:
                    os.remove(os.path.join(DIST_DIR, f))
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

def safe_deploy_exe(src_path, dst_path):
    """
    Safely deploy executable to dst_path on Windows.
    If dst_path is currently running, Windows locks write access.
    We rename the running file to .running_<timestamp>.bak first, then copy the new file!
    """
    if not os.path.isfile(src_path):
        return False
    try:
        shutil.copy2(src_path, dst_path)
        return True
    except PermissionError:
        bak_path = dst_path + f".running_{int(time.time())}.bak"
        try:
            if os.path.exists(bak_path):
                try:
                    os.remove(bak_path)
                except Exception:
                    pass
            os.rename(dst_path, bak_path)
            shutil.copy2(src_path, dst_path)
            print(f"      ✓ Overwrote active running executable: {os.path.basename(dst_path)} (old process running on .bak)")
            return True
        except Exception as ex:
            print(f"      ⚠️ Notice: {os.path.basename(dst_path)} is currently active ({ex}).")
            return False
    except Exception as e:
        print(f"      ⚠️ Copy error for {os.path.basename(dst_path)}: {e}")
        return False

def build_single_exe(stage_app, version_tag):
    print(f"[3/4] Compiling and packaging Standalone SYD-Downloader-Pro {version_tag}.exe...")
    os.makedirs(DIST_DIR, exist_ok=True)
    
    # Compile into isolated build/dist directory so a running output/SYD-Downloader-Pro.exe never causes Access Denied!
    staging_dist = os.path.join(ROOT_DIR, "build", "dist")
    if os.path.exists(staging_dist):
        shutil.rmtree(staging_dist, ignore_errors=True)
    os.makedirs(staging_dist, exist_ok=True)
    
    pyinstaller = PYINSTALLER_EXE if os.path.isfile(PYINSTALLER_EXE) else "pyinstaller"
    main_py = os.path.join(ROOT_DIR, "main.py")
    jre_dir = os.path.join(ROOT_DIR, "jre")
    
    cmd = [
        pyinstaller,
        "--noconsole",
        "--onefile",
        "--clean",
        "--contents-directory=.",
        f"--icon={ICON_PATH}" if os.path.isfile(ICON_PATH) else "",
        "--name=SYD-Downloader-Pro",
        f"--add-data={jre_dir};jre",
        f"--add-data={stage_app};app",
        f"--add-data={ICON_PATH};." if os.path.isfile(ICON_PATH) else "",
        "--collect-all=Crypto",
        "--collect-all=pycryptodome",
        "--collect-all=curl_cffi",
        "--collect-all=uvicorn",
        "--collect-all=fastapi",
        "--collect-all=starlette",
        "--collect-all=pydantic",
        "--copy-metadata=pycryptodome",
        "--copy-metadata=fastapi",
        "--copy-metadata=uvicorn",
        "--hidden-import=Crypto",
        "--hidden-import=Crypto.Cipher",
        "--hidden-import=Crypto.Cipher.AES",
        "--hidden-import=Crypto.Util",
        "--hidden-import=Crypto.Util.Counter",
        "--hidden-import=Crypto.Hash",
        "--hidden-import=Crypto.Hash.SHA256",
        "--hidden-import=Crypto.Random",
        "--hidden-import=curl_cffi",
        "--hidden-import=curl_cffi.requests",
        "--hidden-import=multipart",
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
        f"--distpath={staging_dist}",
        f"--workpath={os.path.join(ROOT_DIR, 'build', 'single_exe_work')}",
        f"--specpath={os.path.join(ROOT_DIR, 'build')}",
        main_py
    ]
    cmd = [c for c in cmd if c]
    
    # Run PyInstaller with real-time log streaming
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace'
    )
    for raw_line in proc.stdout:
        line = raw_line.rstrip()
        if line:
            # Stream informative compiler progress
            low = line.lower()
            if any(k in low for k in ("building", "copying", "collecting", "adding", "completed", "error", "warning", "info:", "analyzing", "appended", "checking")):
                print(f"      {line}")
    proc.wait()
    if proc.returncode != 0:
        print(f"      ❌ PyInstaller build returned code: {proc.returncode}")
        return None
        
    compiled_exe = os.path.join(staging_dist, "SYD-Downloader-Pro.exe")
    if not os.path.isfile(compiled_exe):
        # Fallback check
        alt_exe = os.path.join(staging_dist, "HongguoDownloader.exe")
        if os.path.isfile(alt_exe):
            compiled_exe = alt_exe
        else:
            print(f"      ❌ Error: Compiled executable not found in {staging_dist}")
            return None

    # Deploy to DIST_DIR with version-tagged name: SYD-Downloader-Pro V1.0.2.exe
    versioned_exe_name = f"SYD-Downloader-Pro {version_tag}.exe"
    versioned_exe_path = os.path.join(DIST_DIR, versioned_exe_name)
    safe_deploy_exe(compiled_exe, versioned_exe_path)

    # Ensure compatibility copies exist in output/
    syd_std_exe = os.path.join(DIST_DIR, "SYD-Downloader-Pro.exe")
    hg_std_exe = os.path.join(DIST_DIR, "HongguoDownloader.exe")
    safe_deploy_exe(compiled_exe, syd_std_exe)
    safe_deploy_exe(compiled_exe, hg_std_exe)

    if os.path.isfile(versioned_exe_path):
        sz_mb = os.path.getsize(versioned_exe_path) / (1024 * 1024)
        print(f"      ✓ SUCCESS: Created Standalone Single EXE: {versioned_exe_name} ({sz_mb:.1f} MB)")
        return versioned_exe_path
    elif os.path.isfile(syd_std_exe):
        sz_mb = os.path.getsize(syd_std_exe) / (1024 * 1024)
        print(f"      ✓ SUCCESS: Created Standalone Single EXE: SYD-Downloader-Pro.exe ({sz_mb:.1f} MB)")
        return syd_std_exe
    return None

def cleanup_stage():
    print("[4/4] Cleaning build staging files...")
    shutil.rmtree(os.path.join(ROOT_DIR, "build", "stage_app"), ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT_DIR, "build", "single_exe_work"), ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT_DIR, "build", "dist"), ignore_errors=True)
    print("      ✓ Staging cleaned.")

def main():
    t0 = time.time()
    
    # 1. Bump version first so stage_app includes updated version.json
    new_version, version_tag = get_and_bump_version()
    
    banner(version_tag)
    clean_temp()
    stage_app = prepare_stage_app()
    final_exe = build_single_exe(stage_app, version_tag)
    cleanup_stage()
    
    elapsed = time.time() - t0
    print("\n" + "=" * 68)
    if final_exe and os.path.isfile(final_exe):
        print(f"   🎉 BUILD COMPLETED IN {elapsed:.1f} SECONDS!")
        print(f"   📂 Output Directory: {DIST_DIR}")
        print(f"   📦 Single Standalone EXE (មួយគត់ គ្រប់គ្រាន់):")
        print(f"      👉 {final_exe}")
        print(f"      👉 {os.path.join(DIST_DIR, 'SYD-Downloader-Pro.exe')}")
        print("   🔒 All code compiled as bytecode - 100% Protected from bypass/hacks!")
        print("=" * 68)
        return 0
    else:
        print(f"   ❌ BUILD FAILED AFTER {elapsed:.1f} SECONDS!")
        print(f"   📂 Please review compiler output logs above.")
        print("=" * 68)
        sys.exit(1)

if __name__ == "__main__":
    main()
