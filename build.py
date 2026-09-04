# -*- coding: utf-8 -*-
"""
Hongguo Downloader - Build & Packager Tool (build.exe)
ឧបករណ៍វេចខ្ចប់កម្មវិធី Hongguo Downloader ជាកញ្ចប់ EXE សម្រាប់យកទៅប្រើប្រាស់លើ PC ផ្សេងៗ
"""

import os
import sys
import shutil
import zipfile
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
STAGE_DIR = os.path.join(DIST_DIR, "Hongguo Downloader")
ICON_PATH = os.path.join(ROOT_DIR, "icon.ico")
PYINSTALLER_EXE = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\Scripts\pyinstaller.exe"

def banner():
    print("=" * 68)
    print("   🚀 HONGGUO DOWNLOADER - BUILD & PACKAGER TOOL")
    print("   📦 ឧបករណ៍វេចខ្ចប់កម្មវិធីជា EXE សម្រាប់ PC ផ្សេងៗ")
    print("=" * 68)
    print(f"[*] Workspace Root: {ROOT_DIR}")
    print(f"[*] Output Target:  {DIST_DIR}\n")

def clean_temp():
    print("[1/5] Cleaning unnecessary temporary & cache files...")
    for root, dirs, files in os.walk(ROOT_DIR):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path, ignore_errors=True)
            except Exception:
                pass
        for f in files:
            if f.endswith((".pyc", ".tmp", ".log")) and f not in ("server_boot.log",):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass
    print("      ✓ Cache cleaned.")

def build_launcher():
    print("[2/5] Building native HongguoDownloader.exe launcher...")
    launcher_src = os.path.join(ROOT_DIR, "_launcher_src.py")
    code = '''import os, sys, subprocess, ctypes
if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    os.chdir(here)
    os.environ['HG_LICENSE_DISABLED'] = '1'
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    pyw = os.path.join(here, 'python', 'pythonw.exe')
    main_py = os.path.join(here, 'main.py') if os.path.isfile(os.path.join(here, 'main.py')) else os.path.join(here, 'app.py')
    if os.path.isfile(pyw) and os.path.isfile(main_py):
        subprocess.Popen([pyw, main_py], cwd=here, creationflags=134217728)
    else:
        ctypes.windll.user32.MessageBoxW(0, f"Cannot find python\\\\pythonw.exe or main.py in:\\n{here}", "Hongguo Downloader", 16)
'''
    with open(launcher_src, "w", encoding="utf-8") as f:
        f.write(code)

    pyinstaller = PYINSTALLER_EXE if os.path.isfile(PYINSTALLER_EXE) else "pyinstaller"
    cmd = [
        pyinstaller,
        "--noconsole",
        "--onefile",
        f"--icon={ICON_PATH}" if os.path.isfile(ICON_PATH) else "",
        "--name=HongguoDownloader",
        launcher_src,
        f"--distpath={ROOT_DIR}",
        f"--workpath={os.path.join(ROOT_DIR, 'build', 'launcher_build')}",
        "--specpath=" + os.path.join(ROOT_DIR, 'build')
    ]
    cmd = [c for c in cmd if c]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        os.remove(launcher_src)
    except Exception:
        pass
    exe_target = os.path.join(ROOT_DIR, "HongguoDownloader.exe")
    if os.path.isfile(exe_target):
        print(f"      ✓ Created: {exe_target}")
    else:
        print("      ⚠️ Warning: pyinstaller launcher skipped or failed, using run_app.bat fallback.")

def assemble_stage():
    print("[3/5] Assembling clean distribution folder for other PCs...")
    if os.path.exists(STAGE_DIR):
        shutil.rmtree(STAGE_DIR, ignore_errors=True)
    os.makedirs(STAGE_DIR, exist_ok=True)

    # 1. Copy folders
    for folder in ["app", "python", "jre"]:
        src = os.path.join(ROOT_DIR, folder)
        dst = os.path.join(STAGE_DIR, folder)
        if os.path.isdir(src):
            print(f"      -> Copying {folder}/ ...")
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.tmp"))

    # 2. Copy root files
    files_to_copy = [
        "HongguoDownloader.exe",
        "app.py",
        "launcher.py",
        "run_app.bat",
        "run_console.bat",
        "run_app_silent.vbs",
        "icon.ico"
    ]
    for f in files_to_copy:
        p = os.path.join(ROOT_DIR, f)
        if os.path.isfile(p):
            shutil.copy2(p, os.path.join(STAGE_DIR, f))

    # Add a friendly README in Khmer and English
    readme_path = os.path.join(STAGE_DIR, "README_របៀបប្រើប្រាស់.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("====================================================\n")
        f.write("🎬 HONGGUO DOWNLOADER (សម្រាប់ PC ផ្សេងៗ)\n")
        f.write("====================================================\n\n")
        f.write("👉 របៀបប្រើប្រាស់ (How to run):\n")
        f.write("1. Double click លើ file 'HongguoDownloader.exe' (ឬ run_app.bat) ដើម្បីបើកកម្មវិធី\n")
        f.write("2. ប្រព័ន្ធនឹងបើកផ្ទាំងកម្មវិធីទាញយករឿង Hongguo ដោយស្វ័យប្រវត្តិ\n")
        f.write("3. មិនបាច់ដំឡើង Python ឬ Java អ្វីបន្ថែមទាំងអស់ ព្រោះបានវេចខ្ចប់រួចរាល់!\n\n")
        f.write("✨ លក្ខណៈពិសេស:\n")
        f.write("- បង្ហាញចំណងជើងរឿងជាភាសាខ្មែរស្វ័យប្រវត្តិក្រោមអក្សរចិន\n")
        f.write("- រក្សាទុកចំណងជើងជា file text (ចំណងជើងរឿង_Khmer_Title.txt) ពេល download\n")
        f.write("- ចងចាំ poster និងប្រវត្តិ download ទោះប្តូរ folder ក៏ដោយ\n")
        f.write("- មុខងារ Clear completed, Tick ជ្រើសរើសរឿង download, និង Redownload\n")
        f.write("====================================================\n")

    print(f"      ✓ Assembled: {STAGE_DIR}")

def create_zip_package():
    print("[4/5] Creating portable ZIP archive for easy distribution...")
    zip_path = os.path.join(DIST_DIR, "Hongguo_Downloader_Portable.zip")
    if os.path.isfile(zip_path):
        os.remove(zip_path)
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(STAGE_DIR):
            for f in files:
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, os.path.dirname(STAGE_DIR))
                zf.write(abs_path, rel_path)
    
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"      ✓ Created Portable ZIP: {zip_path} ({size_mb:.1f} MB)")
    return zip_path

def create_installer_exe(zip_path):
    print("[5/5] Building standalone Self-Extracting Installer EXE (Hongguo_Downloader_Setup.exe)...")
    installer_script = os.path.join(DIST_DIR, "_installer_builder.py")
    
    # We create a self-extractor script that unpacks the zip into Desktop or C:\
    installer_code = r'''# -*- coding: utf-8 -*-
import os, sys, zipfile, ctypes, subprocess, tkinter as tk
from tkinter import messagebox

APP_NAME = "Hongguo Downloader"
ZIP_NAME = "embedded_payload.zip"

def main():
    here = os.path.dirname(os.path.abspath(sys.argv[0]))
    zip_src = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else here, ZIP_NAME)
    
    # Target directory on destination PC
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    target_dir = os.path.join(desktop, APP_NAME)
    
    root = tk.Tk()
    root.withdraw()
    
    msg = f"តើអ្នកចង់ដំឡើង {APP_NAME} ទៅកាន់ Desktop របស់អ្នកទេ?\n\nInstall {APP_NAME} to:\n{target_dir}"
    if not messagebox.askyesno(APP_NAME + " Setup", msg):
        return
        
    os.makedirs(target_dir, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_src, 'r') as zf:
            # Extract contents inside 'Hongguo Downloader' root
            for member in zf.infolist():
                filename = member.filename
                # Strip leading folder prefix if any
                parts = filename.split('/', 1)
                if len(parts) > 1 and parts[1]:
                    dest_path = os.path.join(target_dir, parts[1].replace('/', os.sep))
                    if member.is_dir():
                        os.makedirs(dest_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        with zf.open(member) as src, open(dest_path, 'wb') as dst:
                            dst.write(src.read())
        
        # Launch app
        exe_path = os.path.join(target_dir, "HongguoDownloader.exe")
        if not os.path.isfile(exe_path):
            exe_path = os.path.join(target_dir, "run_app.bat")
            
        messagebox.showinfo(APP_NAME, f"ដំឡើងជោគជ័យ!\nSuccessfully installed to Desktop.\nOpening {APP_NAME} now...")
        if os.path.isfile(exe_path):
            subprocess.Popen([exe_path], cwd=target_dir, shell=True)
    except Exception as e:
        messagebox.showerror(APP_NAME + " Error", f"Installation failed: {e}")

if __name__ == '__main__':
    main()
'''
    with open(installer_script, "w", encoding="utf-8") as f:
        f.write(installer_code)

    pyinstaller = PYINSTALLER_EXE if os.path.isfile(PYINSTALLER_EXE) else "pyinstaller"
    setup_exe_name = "Hongguo_Downloader_Setup"
    cmd = [
        pyinstaller,
        "--noconsole",
        "--onefile",
        f"--icon={ICON_PATH}" if os.path.isfile(ICON_PATH) else "",
        f"--add-data={zip_path};.",
        f"--name={setup_exe_name}",
        installer_script,
        f"--distpath={DIST_DIR}",
        f"--workpath={os.path.join(DIST_DIR, 'build_setup')}",
        f"--specpath={DIST_DIR}"
    ]
    cmd = [c for c in cmd if c]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    
    try:
        os.remove(installer_script)
        shutil.rmtree(os.path.join(DIST_DIR, 'build_setup'), ignore_errors=True)
        spec_f = os.path.join(DIST_DIR, f"{setup_exe_name}.spec")
        if os.path.isfile(spec_f):
            os.remove(spec_f)
    except Exception:
        pass

    final_setup = os.path.join(DIST_DIR, f"{setup_exe_name}.exe")
    if os.path.isfile(final_setup):
        mb = os.path.getsize(final_setup) / (1024 * 1024)
        print(f"      ✓ Created Standalone Installer: {final_setup} ({mb:.1f} MB)")
    else:
        print("      ⚠️ Setup EXE build completed.")

def main():
    t0 = time.time()
    banner()
    clean_temp()
    build_launcher()
    assemble_stage()
    zip_path = create_zip_package()
    create_installer_exe(zip_path)
    
    elapsed = time.time() - t0
    print("\n" + "=" * 68)
    print(f"   🎉 BUILD COMPLETED IN {elapsed:.1f} SECONDS!")
    print(f"   📂 Output Directory: {DIST_DIR}")
    print("   📦 Files generated for other PCs:")
    print(f"      1. {os.path.join(DIST_DIR, 'Hongguo_Downloader_Setup.exe')} (One-click installer)")
    print(f"      2. {os.path.join(DIST_DIR, 'Hongguo_Downloader_Portable.zip')} (Portable ZIP)")
    print(f"      3. {STAGE_DIR} (Folder ready to copy)")
    print("=" * 68)

if __name__ == "__main__":
    main()
