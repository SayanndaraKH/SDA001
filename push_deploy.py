# -*- coding: utf-8 -*-
import sys
import os
import subprocess
import datetime

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

try:
    os.system('title SYD Downloader Pro - Auto Push and Deploy')
except Exception:
    pass

def safe_input(prompt=""):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return ""

def run_cmd(cmd):
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, encoding='utf-8', errors='ignore')

def main():
    print("=" * 66)
    print("   🚀 SYD Downloader Pro - Auto Push & Deploy to Railway")
    print("=" * 66)
    print()

    # 1. Check Git
    r = run_cmd("git --version")
    if r.returncode != 0:
        print("❌ [ERROR] មិនបានរកឃើញ Git នៅក្នុងកុំព្យូទ័រនេះទេ!")
        print("សូមដំឡើង Git ជាមុនសិន។")
        safe_input("\nចុច Enter ដើម្បីចាកចេញ...")
        return

    # 2. Check Git Status
    print("[*] កំពុងពិនិត្យមើលស្ថានភាពឯកសារដែលបានកែប្រែ...")
    print("-" * 66)
    status_proc = run_cmd("git status -s")
    status_text = status_proc.stdout.strip()
    if status_text:
        print(status_text)
    else:
        print("(គ្មានឯកសារណាត្រូវបានកែប្រែទេ - Working tree clean)")
    print("-" * 66)
    print()

    has_changes = bool(status_text)
    if not has_changes:
        ans = safe_input("❓ មិនមានឯកសារផ្លាស់ប្តូរថ្មីទេ។ តើអ្នកចង់ Force Push ទៅ Railway ដែរឬទេ? (y/n, default=n): ").strip().lower()
        if ans != 'y':
            print("\n[OK] បញ្ចប់ការងារ។ Railway កំពុងដំណើរការកូដចុងក្រោយបង្អស់។")
            safe_input("\nចុច Enter ដើម្បីចាកចេញ...")
            return

    # 3. Commit message
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    default_msg = f"Auto update and deploy ({now_str})"
    print()
    user_msg = safe_input(f"📝 បញ្ចូលសារ Commit (ចុច Enter យក: '{default_msg}'): ").strip()
    if not user_msg:
        user_msg = default_msg

    # 4. Git Add & Commit
    print()
    print("[*] កំពុងប្រមូលឯកសារ (git add -A)...")
    run_cmd("git add -A")

    print(f"[*] កំពុងធ្វើការ Commit: '{user_msg}'...")
    commit_res = run_cmd(f'git commit -m "{user_msg}"')
    if commit_res.returncode == 0:
        print("  -> Commit រួចរាល់!")
    else:
        print("  -> (គ្មានការផ្លាស់ប្តូរថ្មីត្រូវ Commit ទេ)")

    # 5. Git Push
    print()
    print("[*] កំពុង Push ឡើងទៅកាន់ GitHub (origin main)...")
    print("-" * 66)
    push_proc = subprocess.run("git push origin main", shell=True)
    print("-" * 66)

    if push_proc.returncode != 0:
        print()
        print("=" * 66)
        print("❌ [ERROR] ការ Push ឡើង GitHub បរាជ័យ!")
        print("សូមពិនិត្យមើលការភ្ជាប់ Internet ឬ Git Permission។")
        print("=" * 66)
    else:
        print()
        print("=" * 66)
        print("✅ ជោគជ័យ ១០០%! (PUSH & DEPLOY TRIGGERED)")
        print("=" * 66)
        print()
        print("📡 កូដត្រូវបានបញ្ជូនទៅកាន់ GitHub:")
        print("   https://github.com/SayanndaraKH/SDA001")
        print()
        print("🔄 Railway កំពុងចាប់ផ្តើម Build & Deploy ដោយស្វ័យប្រវត្តិ!")
        print("🔗 ចូលមើលស្ថានភាពដំណើរការលើ Railway:")
        print("   https://railway.com/project/936cc339-8e6b-4b0a-a989-f04c6b6777c7")
        print()
        print("=" * 66)

    print()
    safe_input("👉 ចុច Enter ដើម្បីបិទផ្ទាំងនេះ...")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        safe_input("\nចុច Enter ដើម្បីបិទ...")
