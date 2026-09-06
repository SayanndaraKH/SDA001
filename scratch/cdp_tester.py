# -*- coding: utf-8 -*-
import asyncio, json, os, subprocess, sys, time, urllib.request
import websockets

sys.stdout.reconfigure(encoding='utf-8')

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
port = 9222
user_data_dir = os.path.abspath("scratch/chrome_debug_profile")

cmd = [
    chrome,
    f"--remote-debugging-port={port}",
    f"--user-data-dir={user_data_dir}",
    "--headless",
    "--disable-gpu",
    "about:blank"
]
proc = subprocess.Popen(cmd)
time.sleep(1.5)

async def run():
    try:
        # Get active targets
        pages = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read())
        ws_url = pages[0]["webSocketDebuggerUrl"]
        print("Connected to:", ws_url)
        
        async with websockets.connect(ws_url) as ws:
            # Enable Runtime and Console
            await ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
            await ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
            
            # Navigate to URL with auth_token
            token = "usr_a774fa0087246dc72db6dbe2136b6039"
            target_url = f"http://127.0.0.1:8000/?auth_token={token}"
            print("Navigating to:", target_url)
            await ws.send(json.dumps({"id": 3, "method": "Page.navigate", "params": {"url": target_url}}))
            
            # Listen to messages for 4 seconds
            t_end = time.time() + 4.0
            while time.time() < t_end:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                    data = json.loads(msg)
                    method = data.get("method", "")
                    if "exception" in method.lower() or "error" in method.lower():
                        print("EXCEPTION / ERROR:", data)
                    elif method == "Runtime.consoleAPICalled":
                        args = data.get("params", {}).get("args", [])
                        text = " ".join([str(a.get("value", a)) for a in args])
                        print("CONSOLE:", data.get("params", {}).get("type"), text)
                except asyncio.TimeoutError:
                    pass

            # Evaluate topCoinBadge
            eval_js = """(() => {
                const b = document.getElementById('topCoinBadge');
                const u = window.userAccess;
                const topLogin = document.getElementById('topLoginBtn');
                return {
                    userAccess: u,
                    topCoinBadge_display: b ? b.style.display : 'not_found',
                    topCoinBadge_innerHTML: b ? b.innerHTML : '',
                    topLoginBtn_display: topLogin ? topLogin.style.display : 'not_found'
                };
            })()"""
            await ws.send(json.dumps({
                "id": 10,
                "method": "Runtime.evaluate",
                "params": {"expression": eval_js, "returnByValue": True}
            }))
            
            res_eval = await ws.recv()
            print("EVAL RESULT:", res_eval)

            # Capture screenshot
            await ws.send(json.dumps({
                "id": 11,
                "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            }))
            res_shot = await ws.recv()
            shot_data = json.loads(res_shot).get("result", {}).get("data")
            if shot_data:
                import base64
                with open("scratch/cdp_auth_topbar.png", "wb") as f:
                    f.write(base64.b64decode(shot_data))
                print("Screenshot saved to scratch/cdp_auth_topbar.png")
    finally:
        proc.terminate()

asyncio.run(run())
