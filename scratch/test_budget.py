import subprocess, os

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
out = os.path.abspath("scratch/test_budget.png")
target_html = os.path.abspath("scratch/test_auth_modal.html").replace(os.sep, "/")

cmd = [
    chrome,
    "--headless",
    "--disable-gpu",
    "--window-size=1280,900",
    "--virtual-time-budget=6000",
    f"--screenshot={out}",
    f"file:///{target_html}"
]
subprocess.run(cmd, timeout=20)
print("Saved:", os.path.exists(out), os.path.getsize(out) if os.path.exists(out) else 0)
