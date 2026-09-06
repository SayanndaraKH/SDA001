import sys

def patch():
    path = 'app/web/downloader.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update hero live data badge to have id="heroLiveDataBadge" and style="display:none"
    old_live_badge = """      <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.32);border-radius:20px;padding:6px 14px;font:700 12px/1 var(--font-km),var(--font-ui);color:var(--good);box-shadow:var(--shadow-sm)">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 8px var(--good);animation:freshPulse 1.5s infinite"></span>
        <span>🟢 Live Data: <a href="https://hongguoduanju.com/" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;font-family:var(--font-mono)">https://hongguoduanju.com/</a></span>
        <span id="liveSyncTime" style="color:var(--muted);font-weight:600;font-size:11px">· ផ្សាយផ្ទាល់</span>
      </div>"""

    new_live_badge = """      <!-- Live Data Source Badge (Admin Only: លាក់កុំអោយ USER ឃើញ ឃើញបានតែ ADMIN ប៉ុណ្ណោះ) -->
      <div id="heroLiveDataBadge" style="display:none;align-items:center;gap:8px;background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.32);border-radius:20px;padding:6px 14px;font:700 12px/1 var(--font-km),var(--font-ui);color:var(--good);box-shadow:var(--shadow-sm)">
        <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 8px var(--good);animation:freshPulse 1.5s infinite"></span>
        <span>🟢 Live Data: <a href="https://hongguoduanju.com/" target="_blank" rel="noopener" style="color:inherit;text-decoration:underline;font-family:var(--font-mono)">https://hongguoduanju.com/</a></span>
        <span id="liveSyncTime" style="color:var(--muted);font-weight:600;font-size:11px">· ផ្សាយផ្ទាល់</span>
      </div>"""

    if old_live_badge not in content:
        print("ERROR: old_live_badge not found!")
        return False
    content = content.replace(old_live_badge, new_live_badge, 1)

    # 2. Update heroLiveSyncBtn to be hidden by default
    old_sync_btn = '<button type="button" class="btn ghost sm" id="heroLiveSyncBtn" title="Update posters directly from https://hongguoduanju.com/" style="font-family:var(--font-km);font-size:12px;font-weight:700;padding:6px 14px;border-radius:20px;border-color:rgba(255,106,43,0.4);color:var(--accent);display:inline-flex;align-items:center;gap:6px;cursor:pointer">'
    new_sync_btn = '<button type="button" class="btn ghost sm" id="heroLiveSyncBtn" title="Update posters directly from https://hongguoduanju.com/" style="display:none;font-family:var(--font-km);font-size:12px;font-weight:700;padding:6px 14px;border-radius:20px;border-color:rgba(255,106,43,0.4);color:var(--accent);align-items:center;gap:6px;cursor:pointer">'

    if old_sync_btn not in content:
        print("ERROR: old_sync_btn not found!")
        return False
    content = content.replace(old_sync_btn, new_sync_btn, 1)

    # 3. Update tab Live Data in boardTabs to be hidden by default
    old_live_tab = '<button class="tab" data-board="livedata" title="Live data &amp; posters directly from https://hongguoduanju.com/">⚡ Live Data</button>'
    new_live_tab = '<button class="tab" id="tabLiveData" data-board="livedata" style="display:none" title="Live data &amp; posters">⚡ Live Data</button>'

    if old_live_tab not in content:
        print("ERROR: old_live_tab not found!")
        return False
    content = content.replace(old_live_tab, new_live_tab, 1)

    # 4. In updateAccessUI(data), toggle heroLiveDataBadge, heroLiveSyncBtn, and tabLiveData based on isAdmin
    old_access_code = """  const isAdmin = !!(data.is_admin || data.role === 'admin');
  const isVip = !!(data.is_vip);
  const isPendingVip = (data.status === 'pending_vip');
  const isLocked24h = (data.status === 'trial_locked_24h');
  const isBanned = (data.status === 'banned' || data.is_banned);
  const isUser = !!(data.username && !isAdmin);"""

    new_access_code = """  const isAdmin = !!(data.is_admin || data.role === 'admin');
  const isVip = !!(data.is_vip);
  const isPendingVip = (data.status === 'pending_vip');
  const isLocked24h = (data.status === 'trial_locked_24h');
  const isBanned = (data.status === 'banned' || data.is_banned);
  const isUser = !!(data.username && !isAdmin);

  // Live Data Source & Upstream link: STRICTLY ADMIN ONLY! (លាក់កុំអោយ USER ឃើញ ឃើញបានតែ ADMIN)
  const heroLiveBadge = $("#heroLiveDataBadge");
  if(heroLiveBadge){
    heroLiveBadge.style.display = isAdmin ? "inline-flex" : "none";
  }
  const heroSyncBtn = $("#heroLiveSyncBtn");
  if(heroSyncBtn){
    heroSyncBtn.style.display = isAdmin ? "inline-flex" : "none";
  }
  const tabLiveData = $("#tabLiveData") || document.querySelector('#boardTabs .tab[data-board="livedata"]');
  if(tabLiveData){
    tabLiveData.style.display = isAdmin ? "inline-block" : "none";
  }"""

    if old_access_code not in content:
        print("ERROR: old_access_code not found!")
        return False
    content = content.replace(old_access_code, new_access_code, 1)

    # 5. In switchBoardTab(board), prevent non-admin from entering livedata tab
    old_switch_board = """function switchBoardTab(board){
  const hero = document.querySelector(".hero");
  if(board === "livedata"){"""

    new_switch_board = """function switchBoardTab(board){
  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  if(board === "livedata" && !isAdmin){
    board = "explorer";
  }
  const hero = document.querySelector(".hero");
  if(board === "livedata"){"""

    if old_switch_board not in content:
        print("ERROR: old_switch_board not found!")
        return False
    content = content.replace(old_switch_board, new_switch_board, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: Live Data link is now strictly hidden for USER and only visible to ADMIN!")
    return True

if __name__ == '__main__':
    patch()
