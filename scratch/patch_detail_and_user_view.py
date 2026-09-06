import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_patch():
    file_path = os.path.join('app', 'web', 'downloader.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add topbar mode switcher buttons before #topUserCtrlBtn
    old_top_btns = '<button class="btn ghost sm" id="topUserCtrlBtn"'
    new_top_btns = '''<!-- Direct Switch between Real User & Admin Mode -->
      <button class="btn ghost sm" id="topBtnSwitchToUser" onclick="switchActiveMode('user')" style="display:none;border-radius:20px;font-weight:800;font-size:12px;color:var(--accent);border-color:rgba(255,106,43,0.5);align-items:center;gap:6px" title="ប្តូរទៅមើល និងអនុវត្តផ្ទាល់ជា User ជាក់ស្តែង (ភាគ 1-5 Free, ភាគ 6+ Coin)">
        <span>👤</span> <span>មើលជា User ជាក់ស្តែង</span>
      </button>
      <button class="btn ghost sm" id="topBtnSwitchToAdmin" onclick="switchActiveMode('admin')" style="display:none;border-radius:20px;font-weight:800;font-size:12px;color:#c084fc;border-color:rgba(192,132,252,0.5);align-items:center;gap:6px" title="ត្រឡប់ទៅផ្ទាំងគ្រប់គ្រង ADMIN">
        <span>🛡️</span> <span>ចូល Admin</span>
      </button>
      <button class="btn ghost sm" id="topUserCtrlBtn"'''

    if old_top_btns in html and 'id="topBtnSwitchToUser"' not in html:
        html = html.replace(old_top_btns, new_top_btns, 1)
        print('1. Added topbar mode switcher buttons')
    else:
        print('1. Topbar switcher already present or target not found')

    # 2. Upgrade renderDramaDetailEpisodes to display both locked and unlocked episode counts and render all chips
    old_render_start = 'function renderDramaDetailEpisodes(){'
    old_render_end = 'async function translateDramaTitle('
    p1 = html.find(old_render_start)
    p2 = html.find(old_render_end, p1)

    new_render_func = '''function renderDramaDetailEpisodes(){
  const eps = ddAllEps || [];
  const countEl = $("#ddEpSelectedCount");
  if(countEl) countEl.textContent = `${ddSelectedEps.size}`;

  const isStream = ddMode === 'stream';
  const modeStreamBtn = $("#ddModeStream");
  const modeSelectBtn = $("#ddModeSelect");
  if(modeStreamBtn) modeStreamBtn.classList.toggle("on", isStream);
  if(modeSelectBtn) modeSelectBtn.classList.toggle("on", !isStream);

  const selToolbar = $("#ddSelectToolbar");
  if(selToolbar) selToolbar.hidden = isStream;

  const rangesEl = $("#ddEpRanges");
  const gridEl = $("#ddEpGrid");
  const totHint = $("#ddEpTotalHint");

  if(!eps.length){
    if(totHint) totHint.textContent = `សរុប 0 ភាគ`;
    gridEl.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--muted);font-family:var(--font-km)">⏳ កំពុងទាញយកបញ្ជីភាគ...</div>';
    if(rangesEl) rangesEl.innerHTML = '';
    return;
  }

  const isFull = isUserFullAccess();
  let userEpLimit = 5;
  let isDramaFreeAll = false;
  const currSid = (ddCurrentDrama ? (ddCurrentDrama.id || ddCurrentDrama.series_id) : null);
  if (currSid && typeof getDramaRuleForSeries === 'function') {
    const dr = getDramaRuleForSeries(currSid);
    if (dr && dr.rule === 'free_all') isDramaFreeAll = true;
    else if (dr && dr.free_episodes != null) userEpLimit = Number(dr.free_episodes);
    else userEpLimit = 5;
  } else {
    userEpLimit = 5;
  }

  // Calculate episode statistics (ទាំងភាគ Lock និងភាគអត់ Lock)
  let freeEpCount = 0;
  let lockedEpCount = 0;
  if(isFull || isDramaFreeAll){
    freeEpCount = eps.length;
    lockedEpCount = 0;
  } else {
    freeEpCount = Math.min(eps.length, userEpLimit);
    lockedEpCount = Math.max(0, eps.length - freeEpCount);
  }

  // Update Episode Statistics Badges in UI (បង្ហាញចំនួនភាគទាំងភាគ Lock និងភាគអត់ Lock)
  if(totHint){
    totHint.innerHTML = `
      <span style="display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap">
        <span style="font-size:11px;font-weight:800;padding:2px 8px;border-radius:6px;background:rgba(34,197,94,0.18);color:#22c55e;border:1px solid rgba(34,197,94,0.4)" title="ភាគដែលអាចទស្សនា និងដោនឡូតបានដោយសេរី ឥតគិតថ្លៃ">
          🔓 អត់ Lock: ${freeEpCount} ភាគ
        </span>
        <span style="font-size:11px;font-weight:800;padding:2px 8px;border-radius:6px;background:rgba(234,179,8,0.18);color:#eab308;border:1px solid rgba(234,179,8,0.4)" title="ភាគដែលត្រូវប្រើ 2 Coins (1,000៛) ឬ VIP">
          🔒 ជាប់ Lock: ${lockedEpCount} ភាគ
        </span>
        <span style="font-size:11.5px;font-weight:800;color:var(--muted)">
          (សរុប ${eps.length} ភាគ)
        </span>
      </span>
    `;
  }

  // Update Drama Rule Badge in info bar
  const ruleBadge = $("#ddDramaRuleBadge");
  if(ruleBadge){
    if(isDramaFreeAll || isFull){
      ruleBadge.innerHTML = `🟢 Free គ្រប់ភាគទាំងអស់ (${eps.length} ភាគ)`;
      ruleBadge.style.color = "var(--good)";
      ruleBadge.style.background = "rgba(34,197,94,0.15)";
      ruleBadge.style.borderColor = "rgba(34,197,94,0.4)";
    } else {
      ruleBadge.innerHTML = `🔓 Free (អត់ Lock): ភាគ 1-${userEpLimit} (${freeEpCount} ភាគ) · 🔒 ជាប់ Lock: ភាគ ${userEpLimit+1}+ (${lockedEpCount} ភាគ)`;
    }
  }

  // Update VIP Episode Alert Banner text with exact breakdown
  const vipBanner = $("#ddVipEpisodeBanner");
  if(vipBanner){
    vipBanner.style.display = (isFull || isDramaFreeAll) ? 'none' : 'flex';
    const vipSpan = vipBanner.querySelector('div span');
    if(vipSpan){
      vipSpan.innerHTML = `<b>គណនីធម្មតា:</b> ឥតគិតថ្លៃ (អត់ Lock) <b>${freeEpCount} ភាគ</b> (ភាគ 1 ដល់ ${userEpLimit}) · ជាប់ Lock <b>${lockedEpCount} ភាគ</b> (ភាគ ${userEpLimit+1} ឡើងទៅ តម្រូវការ 2 Coins ឬ VIP)`;
    }
  }

  // Range Switcher Tabs (e.g. ទាំងអស់, 1-30, 31-60, 61-90, 91-94)
  if(eps.length > DD_RANGE_SIZE){
    rangesEl.hidden = false;
    const numRanges = Math.ceil(eps.length / DD_RANGE_SIZE);
    let rHtml = `<button type="button" class="dd-range-tab ${ddActiveRange===-1?'on':''}" data-range="-1">ទាំងអស់ (${eps.length})</button>`;
    for(let r=0; r<numRanges; r++){
      const start = r * DD_RANGE_SIZE + 1;
      const end = Math.min((r + 1) * DD_RANGE_SIZE, eps.length);
      rHtml += `<button type="button" class="dd-range-tab ${ddActiveRange===r?'on':''}" data-range="${r}">${start}-${end}</button>`;
    }
    rangesEl.innerHTML = rHtml;
  } else {
    rangesEl.hidden = false;
    rangesEl.innerHTML = `<span style="font-size:12.5px;font-weight:700;color:var(--muted)">ភាគ 1 - ${eps.length}</span>`;
  }

  // Slice visible episodes based on active range
  let visibleEps = eps;
  if(eps.length > DD_RANGE_SIZE && ddActiveRange >= 0){
    const startIdx = ddActiveRange * DD_RANGE_SIZE;
    visibleEps = eps.slice(startIdx, startIdx + DD_RANGE_SIZE);
  }

  // Render Episode Chips for both locked and unlocked episodes
  let chipsHtml = visibleEps.map(n => {
    const epNum = Number(n);
    const isSel = ddSelectedEps.has(n);
    const isPlaying = (ddInlinePlayingEp === n);
    const isLocked = isEpisodeLocked(n, currSid);
    let cls = "dd-epchip-item";
    if(isPlaying) cls += " active-playing";
    else if(!isStream && isSel) cls += " selected-for-dl";
    if(isLocked) cls += " locked-vip";
    
    let epLabel = `${n}`;
    let titleHint = '';
    if(isLocked){
      titleHint = `ភាគទី ${n} · 🔒 ជាប់ Lock (2 Coins = 1,000៛ ឬ VIP · ចុចដើម្បីដោះសោរ)`;
      epLabel = `<span style="display:inline-flex;align-items:center;justify-content:center;gap:3px"><span>${n}</span><span style="font-size:10px;opacity:0.9">🔒</span></span>`;
    } else {
      titleHint = `ភាគទី ${n} · 🔓 អត់ Lock (ឥតគិតថ្លៃ Free · ចុចដើម្បី ${isStream ? 'Live Stream មើល' : 'ជ្រើសរើសដោនឡូត'})`;
      epLabel = `<span style="display:inline-flex;align-items:center;justify-content:center;gap:3px"><span>${n}</span><span style="font-size:8.5px;color:var(--good);font-weight:900">Free</span></span>`;
    }

    return `<button type="button" class="${cls}" data-dei="${n}" aria-pressed="${isSel}" title="${titleHint}">${epLabel}</button>`;
  }).join("");

  gridEl.innerHTML = chipsHtml;
}

'''

    if p1 != -1 and p2 != -1:
        html = html[:p1] + new_render_func + html[p2:]
        print('2. Upgraded renderDramaDetailEpisodes successfully')
    else:
        print('2. ERROR: renderDramaDetailEpisodes bounds not found', p1, p2)

    # 3. CSS rule: "ផ្ទាំងរបស់ user គ្មានប៊ូតុង Restart ដាច់ខាត"
    restart_css = '''
  /* Strictly hide Restart button and Admin controls on User view */
  :root:not([data-user-role="admin"]) #topAdminRestartBtn,
  :root:not([data-user-role="admin"]) #topUserCtrlBtn,
  :root:not([data-user-role="admin"]) #heroLiveDataBadge,
  :root:not([data-user-role="admin"]) #heroLiveSyncBtn,
  :root:not([data-user-role="admin"]) #tabLiveData,
  :root:not([data-user-role="admin"]) #ddAdminRuleBar {
    display: none !important;
  }
'''
    if '</style>' in html and '/* Strictly hide Restart button' not in html:
        html = html.replace('</style>', restart_css + '\n</style>', 1)
        print('3. Added strict CSS rule: ផ្ទាំងរបស់ user គ្មានប៊ូតុង Restart ដាច់ខាត')

    # 4. In updateAccessUI: enforce data-user-role and strictly hide restart button
    old_update_ui = 'function updateAccessUI(data){'
    new_update_ui = '''function updateAccessUI(data){
  const isAdmin = !!(data && (data.is_admin || data.role === 'admin'));
  document.documentElement.dataset.userRole = isAdmin ? "admin" : "user";
'''
    if old_update_ui in html and 'document.documentElement.dataset.userRole' not in html:
        html = html.replace(old_update_ui, new_update_ui, 1)
        print('4. Added data-user-role to updateAccessUI')

    # Ensure topRestart is explicitly hidden when not admin
    old_restart_logic = '''    const topRestart = $("#topAdminRestartBtn");
    if(topRestart) topRestart.style.display = "inline-flex";'''
    new_restart_logic = '''    const topRestart = $("#topAdminRestartBtn");
    if(topRestart) topRestart.style.display = isAdmin ? "inline-flex" : "none";'''
    if old_restart_logic in html:
        html = html.replace(old_restart_logic, new_restart_logic)
        print('5. Enforced topRestart display logic in JS')

    # 5. Add switchActiveMode function
    switch_mode_func = '''
window.switchActiveMode = async function(mode){
  try {
    let pin = '';
    if(mode === 'admin'){
      pin = localStorage.getItem('syd_auth_token') || sessionStorage.getItem('hg_admin_pin') || '';
      if(!pin || !pin.startsWith('syd')){
        pin = prompt("បញ្ចូលពាក្យសម្ងាត់ ADMIN PIN:", "syd@168");
        if(!pin) return;
      }
    }
    const devId = (window.userAccess && window.userAccess.device_id) || '';
    const res = await (await fetch('/dl/access/switch-mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: mode, pin: pin, device_id: devId })
    })).json();

    if(res.ok){
      if(res.token){
        localStorage.setItem('syd_auth_token', res.token);
      }
      if(mode === 'admin'){
        toast("🛡️ បានចូលទៅកាន់ ADMIN (Full Control)", false);
      } else {
        toast("👤 បានប្តូរទៅកាន់ User ជាក់ស្តែង (ភាគ 1-5 Free, ភាគ 6+ 2 Coins)", false);
      }
      await fetchAccessStatus();
    } else {
      toast("❌ " + (res.error || "មិនអាចប្តូរបានទេ"), true);
    }
  } catch(e){
    toast("⚠️ កំហុស: " + e, true);
  }
};
'''
    if 'window.switchActiveMode =' not in html:
        # Add right before </script>
        p_script = html.rfind('</script>')
        if p_script != -1:
            html = html[:p_script] + switch_mode_func + html[p_script:]
            print('6. Added switchActiveMode function')

    # 6. Update topbar buttons visibility in updateAccessUI
    old_btn_sw = 'const topLogout = $("#topLogoutBtn");'
    new_btn_sw = '''const topLogout = $("#topLogoutBtn");
  const btnSwitchToUser = $("#topBtnSwitchToUser");
  const btnSwitchToAdmin = $("#topBtnSwitchToAdmin");
  if(btnSwitchToUser) btnSwitchToUser.style.display = isAdmin ? "inline-flex" : "none";
  if(btnSwitchToAdmin) btnSwitchToAdmin.style.display = (!isAdmin) ? "inline-flex" : "none";
  const topRestartBtn = $("#topAdminRestartBtn");
  if(topRestartBtn) topRestartBtn.style.display = isAdmin ? "inline-flex" : "none";'''
    if old_btn_sw in html and 'btnSwitchToUser' not in html:
        html = html.replace(old_btn_sw, new_btn_sw, 1)
        print('7. Updated button visibility logic in updateAccessUI')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('ALL PATCHES APPLIED SUCCESSFULLY!')

if __name__ == '__main__':
    run_patch()
