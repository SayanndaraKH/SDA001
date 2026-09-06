import os
import sys

target_file = r"c:\Users\Administrator\Desktop\SYD-Downloader Pro\app\web\downloader.html"

with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()

print("Original content length:", len(content))

# 1. Top Days Left Badge
old_top_badge = '<span id="topDaysLeftIcon">⏳</span> <span id="topDaysLeftText">នៅសល់ 7 ថ្ងៃ</span>'
new_top_badge = '<span id="topDaysLeftIcon">⏳</span> <span id="topDaysLeftText">នៅសល់ 3 ថ្ងៃ</span>'
assert old_top_badge in content, "old_top_badge not found"
content = content.replace(old_top_badge, new_top_badge)

# 2. Drama Detail Modal - Add Drama Free Rule Badge & Admin Bar
old_dd_intro = '''          <p id="ddIntro" style="font-family:var(--font-km),var(--font-ui);font-size:12.5px;line-height:1.6;color:var(--ink-2);margin:0;max-height:85px;overflow-y:auto"></p>
        </div>

        <!-- Action Buttons Row -->'''

new_dd_intro = '''          <p id="ddIntro" style="font-family:var(--font-km),var(--font-ui);font-size:12.5px;line-height:1.6;color:var(--ink-2);margin:0;max-height:85px;overflow-y:auto"></p>
        </div>

        <!-- Drama Free Rule Badge & Admin Setting Bar -->
        <div id="ddDramaRuleBar" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:8px 12px">
          <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:12px;font-weight:700;color:var(--muted)">សិទ្ធិទស្សនា៖</span>
            <span id="ddDramaRuleBadge" style="font-size:11.5px;font-weight:800;padding:3px 10px;border-radius:6px;background:rgba(255,106,43,0.15);color:var(--accent);border:1px solid rgba(255,106,43,0.35)">
              🟠 Free ភាគ 1-10
            </span>
          </div>
          <!-- Admin Quick Setting Buttons (Only visible to Admin) -->
          <div id="ddAdminRuleBar" style="display:none;align-items:center;gap:6px;flex-wrap:wrap">
            <span style="font-size:11px;font-weight:700;color:var(--ink-2)">ADMIN កំណត់៖</span>
            <button type="button" class="btn sm" id="ddSetFreeAllBtn" onclick="doAdminSetDramaRule('free_all')" style="font-weight:700;font-size:11px;padding:3px 8px;border-radius:6px;background:rgba(34,197,94,0.2);color:#22c55e;border:1px solid rgba(34,197,94,0.4);cursor:pointer">
              🟢 Free 100%
            </button>
            <button type="button" class="btn sm" id="ddSetFree10Btn" onclick="doAdminSetDramaRule('free_episodes', 10)" style="font-weight:700;font-size:11px;padding:3px 8px;border-radius:6px;background:rgba(255,106,43,0.2);color:var(--accent);border:1px solid rgba(255,106,43,0.4);cursor:pointer">
              🟠 Free 1-10
            </button>
            <button type="button" class="btn ghost sm" onclick="doAdminCustomDramaRule()" style="font-weight:700;font-size:11px;padding:3px 8px;border-radius:6px;cursor:pointer">
              ⚙️ ភាគផ្ទាល់
            </button>
          </div>
        </div>

        <!-- Action Buttons Row -->'''

assert old_dd_intro in content, "old_dd_intro not found"
content = content.replace(old_dd_intro, new_dd_intro)

# 3. Modal 3-Day Trial Notice
old_modal_notice = '''          <!-- 7-Day Trial Strict Rule Notice for Regular Users -->
          <div id="modalTrialRuleNotice" style="display:none;font-size:11.5px;color:#ef4444;background:rgba(239,68,68,0.1);padding:8px 12px;border-radius:8px;border:1px dashed rgba(239,68,68,0.4);line-height:1.5">
            ⚠️ <b>ច្បាប់ User ធម្មតា៖</b> លោកអ្នកមានរយៈពេល 7 ថ្ងៃដើម្បីស្នើសុំ VIP។ ប្រសិនបើហួស 7 ថ្ងៃដោយមិនបានស្នើសុំ VIP ទេ គណនីនឹងត្រូវលុបចោលចេញពីប្រព័ន្ធដាច់ខាត!
          </div>'''

new_modal_notice = '''          <!-- 3-Day Trial Strict Rule Notice for Regular Users -->
          <div id="modalTrialRuleNotice" style="display:none;font-size:11.5px;color:#ef4444;background:rgba(239,68,68,0.1);padding:8px 12px;border-radius:8px;border:1px dashed rgba(239,68,68,0.4);line-height:1.5">
            ⚠️ <b>ច្បាប់ User ធម្មតា៖</b> លោកអ្នកមានរយៈពេល 3 ថ្ងៃដើម្បីស្នើសុំ VIP។ ប្រសិនបើហួស 3 ថ្ងៃដោយមិនបានស្នើសុំ VIP ទេ ប្រព័ន្ធនឹងបិទការ Login រយៈពេល 24 ម៉ោង ជាបណ្តោះអាសន្ន!
          </div>'''

assert old_modal_notice in content, "old_modal_notice not found"
content = content.replace(old_modal_notice, new_modal_notice)

# 4. Admin PIN input placeholder
old_pin_inp = 'placeholder="បញ្ចូល Admin PIN (Default: 8888)"'
new_pin_inp = 'placeholder="បញ្ចូល Admin Password (Default: syd@168)"'
assert old_pin_inp in content, "old_pin_inp not found"
content = content.replace(old_pin_inp, new_pin_inp)

# 5. User Control Modal: Add Drama Rules Tab Button
old_uc_tab_btn = '''        <button type="button" class="btn sm uc-tab-btn on" id="ucTabBtnUsers" onclick="switchUcTab('users')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px">
          👥 គ្រប់គ្រងអ្នកប្រើប្រាស់ &amp; VIP
        </button>'''

new_uc_tab_btn = '''        <button type="button" class="btn sm uc-tab-btn on" id="ucTabBtnUsers" onclick="switchUcTab('users')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px">
          👥 គ្រប់គ្រងអ្នកប្រើប្រាស់ &amp; VIP
        </button>
        <button type="button" class="btn sm uc-tab-btn" id="ucTabBtnDramaRules" onclick="switchUcTab('drama_rules')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px;color:#22c55e">
          🎬 កំណត់សិទ្ធិរឿង (Free Rules)
        </button>'''

assert old_uc_tab_btn in content, "old_uc_tab_btn not found"
content = content.replace(old_uc_tab_btn, new_uc_tab_btn)

# 6. User Control Modal: Add Drama Rules Tab Panel
old_uc_sec_users_end = '''        <!-- Save Settings Button -->
        <button class="btn primary" id="adminSaveAllSettingsBtn" style="height:40px;font-weight:800;font-size:13.5px;display:flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#ff6a2b,#ff2e63)">
          <span>💾 រក្សាទុកការកំណត់ទាំងអស់ (Save All Settings)</span>
        </button>
      </div>

      <!-- TAB 3: DOWNLOAD & STORAGE -->'''

new_uc_sec_users_end = '''        <!-- Save Settings Button -->
        <button class="btn primary" id="adminSaveAllSettingsBtn" style="height:40px;font-weight:800;font-size:13.5px;display:flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#ff6a2b,#ff2e63)">
          <span>💾 រក្សាទុកការកំណត់ទាំងអស់ (Save All Settings)</span>
        </button>
      </div>

      <!-- TAB: DRAMA FREE RULES MANAGEMENT (ADMIN ONLY) -->
      <div id="ucTabDramaRulesSec" class="modal-scroll" style="display:none;flex-direction:column;gap:12px;padding-right:2px">
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
            <div style="font:800 13px var(--font-ui);color:#22c55e;display:flex;align-items:center;gap:6px">
              <span>🎬</span> <span>កំណត់សិទ្ធិរឿង (Drama Free Rules)</span>
            </div>
            <button type="button" class="btn ghost sm" onclick="loadAdminDramaRules()" style="height:32px;font-weight:700;font-size:11.5px">🔄 ផ្ទុកបញ្ជីឡើងវិញ</button>
          </div>
          <div style="font-size:12px;color:var(--ink-2);line-height:1.5">
            Admin អាចកំណត់រឿងណា <b>Free 100% (គ្រប់ភាគ)</b> ឬ <b>Free 1-10 ភាគ</b> សម្រាប់ User ធម្មតាបានដោយសេរីតាមចិត្តចង់។ (User VIP មើលបានគ្រប់ភាគទាំងអស់ជាស្វ័យប្រវត្តិ)។
          </div>

          <!-- Quick Rule Adder Card -->
          <div style="background:var(--surface);padding:12px;border-radius:10px;border:1px solid var(--line);display:flex;flex-direction:column;gap:8px">
            <div style="font:700 12px var(--font-ui);color:var(--accent)">➕ កំណត់សិទ្ធិរឿងថ្មី ឬកែប្រែ៖</div>
            <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
              <input type="text" id="adminDrSeriesId" placeholder="បញ្ចូល Series ID ឬ Title រឿង..." style="flex:2 1 180px;height:34px;background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:0 10px;color:var(--ink);font:12px var(--font-mono)">
              <select id="adminDrRuleType" onchange="toggleAdminDrCustomEps()" style="flex:1 1 140px;height:34px;background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:0 8px;color:var(--ink);font:600 12px var(--font-ui)">
                <option value="free_all" selected>🟢 Free 100% (គ្រប់ភាគ)</option>
                <option value="free_episodes">🟠 Free 1-10 ភាគ</option>
                <option value="custom">⚙️ កំណត់ភាគផ្ទាល់</option>
              </select>
              <input type="number" id="adminDrCustomEps" placeholder="ចំនួនភាគ Free" min="1" max="999" value="10" style="width:110px;height:34px;background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:0 8px;color:var(--ink);font:600 12px var(--font-mono);display:none">
              <button type="button" class="btn primary sm" onclick="submitAdminDramaRule()" style="height:34px;padding:0 16px;font-weight:700;font-size:12px;background:linear-gradient(135deg,#22c55e,#16a34a)">💾 រក្សាទុក</button>
            </div>
          </div>

          <!-- Configured Drama Rules Table / List -->
          <div style="font:700 12.5px var(--font-ui);color:var(--ink);margin-top:4px">📋 បញ្ជីរឿងដែលបានកំណត់សិទ្ធិរួចរាល់ (<span id="adminDrCount">0</span>)៖</div>
          <div id="adminDramaRulesContainer" style="display:flex;flex-direction:column;gap:8px;min-height:80px">
            <div style="text-align:center;padding:16px;color:var(--muted);font-size:12px">កំពុងផ្ទុកបញ្ជីកំណត់សិទ្ធិ...</div>
          </div>
        </div>
      </div>

      <!-- TAB 3: DOWNLOAD & STORAGE -->'''

assert old_uc_sec_users_end in content, "old_uc_sec_users_end not found"
content = content.replace(old_uc_sec_users_end, new_uc_sec_users_end)

# 7. renderDramaDetailUI updates (badge and admin quick setting bar)
old_render_ui_status = '''  const statusEl = $("#ddStatusBadge");
  const st = item.status || '完结';
  statusEl.textContent = (st === '完结' || st.includes('完')) ? 'ចប់ពេញលេញ (Completed)' : (st.includes('连载') ? 'កំពុងចាក់ផ្សាយ (Ongoing)' : st);'''

new_render_ui_status = '''  const statusEl = $("#ddStatusBadge");
  const st = item.status || '完结';
  statusEl.textContent = (st === '完结' || st.includes('完')) ? 'ចប់ពេញលេញ (Completed)' : (st.includes('连载') ? 'កំពុងចាក់ផ្សាយ (Ongoing)' : st);

  // Update Drama Free Rule Badge & Admin Bar
  const ruleBadge = $("#ddDramaRuleBadge");
  const adminBar = $("#ddAdminRuleBar");
  const sid = String(item.id || '');
  const r = (typeof getDramaRuleForSeries === 'function') ? getDramaRuleForSeries(sid) : null;
  const isFreeAll = (r && r.rule === 'free_all');
  if(ruleBadge){
    if(isFreeAll){
      ruleBadge.textContent = "🟢 Free 100% (គ្រប់ភាគ)";
      ruleBadge.style.background = "rgba(34,197,94,0.18)";
      ruleBadge.style.color = "#22c55e";
      ruleBadge.style.border = "1px solid rgba(34,197,94,0.4)";
    } else {
      const lim = (r && r.free_episodes) ? r.free_episodes : 10;
      ruleBadge.textContent = `🟠 Free ភាគ 1-${lim}`;
      ruleBadge.style.background = "rgba(255,106,43,0.16)";
      ruleBadge.style.color = "var(--accent)";
      ruleBadge.style.border = "1px solid rgba(255,106,43,0.35)";
    }
  }

  // Admin Quick Setting Bar
  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  if(adminBar){
    if(isAdmin){
      adminBar.style.display = "flex";
      const bAll = $("#ddSetFreeAllBtn");
      const b10 = $("#ddSetFree10Btn");
      if(bAll) bAll.style.outline = isFreeAll ? "2px solid #22c55e" : "none";
      if(b10) b10.style.outline = !isFreeAll ? "2px solid var(--accent)" : "none";
    } else {
      adminBar.style.display = "none";
    }
  }'''

assert old_render_ui_status in content, "old_render_ui_status not found"
content = content.replace(old_render_ui_status, new_render_ui_status)

# 8. isUserFullAccess, isEpisodeLocked, promptVipModal
old_access_fns = '''function isUserFullAccess(){
  if(!window.userAccess) return false;
  return !!(window.userAccess.is_admin || window.userAccess.is_vip || window.userAccess.role === 'admin' || window.userAccess.role === 'dev' || window.userAccess.mode === 'free_all');
}

function isEpisodeLocked(epNum){
  if(isUserFullAccess()) return false;
  return Number(epNum) > 10;
}'''

new_access_fns = '''function isUserFullAccess(){
  if(!window.userAccess) return false;
  return !!(window.userAccess.is_admin || window.userAccess.is_vip || window.userAccess.role === 'admin' || window.userAccess.mode === 'free_all');
}

function isEpisodeLocked(epNum, seriesId){
  if(isUserFullAccess()) return false;
  const sid = seriesId || (ddCurrentDrama ? ddCurrentDrama.id : null);
  if(sid && typeof getDramaRuleForSeries === 'function'){
    const r = getDramaRuleForSeries(sid);
    if(r){
      if(r.rule === 'free_all') return false;
      if(r.free_episodes != null) return Number(epNum) > Number(r.free_episodes);
    }
  }
  return Number(epNum) > 10;
}'''

assert old_access_fns in content, "old_access_fns not found"
content = content.replace(old_access_fns, new_access_fns)

old_prompt_vip = '''function promptVipModal(epNum){
  const banner = $("#authAlertBanner");
  const alertText = $("#authAlertText");
  if(banner && alertText){
    alertText.innerHTML = `🔒 <b>ភាគទី ${epNum} ត្រូវបានចាក់សោរ (Locked)!</b><br>គណនីធម្មតាអាចទស្សនា & ដោនឡូតបានត្រឹម <b>ភាគ 1 ដល់ 10</b> ប៉ុណ្ណោះ។<br>👉 សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទស្សនា និងដោនឡូតគ្រប់ភាគទាំងអស់ដោយគ្មានការ Lock!`;
    banner.style.display = 'block';
  }
  openUserRegisterModal('vip', false);
}'''

new_prompt_vip = '''function promptVipModal(epNum, seriesId){
  const banner = $("#authAlertBanner");
  const alertText = $("#authAlertText");
  const sid = seriesId || (ddCurrentDrama ? ddCurrentDrama.id : null);
  let limitText = "ភាគ 1 ដល់ 10";
  if(sid && typeof getDramaRuleForSeries === 'function'){
    const r = getDramaRuleForSeries(sid);
    if(r && r.free_episodes != null) limitText = `ភាគ 1 ដល់ ${r.free_episodes}`;
  }
  if(banner && alertText){
    alertText.innerHTML = `🔒 <b>ភាគទី ${epNum} ត្រូវបានចាក់សោរ (Locked)!</b><br>គណនីធម្មតាអាចទស្សនា & ដោនឡូតបានត្រឹម <b>${limitText}</b> ប៉ុណ្ណោះ។<br>👉 សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទស្សនា និងដោនឡូតគ្រប់ភាគទាំងអស់ដោយគ្មានការ Lock!`;
    banner.style.display = 'block';
  }
  openUserRegisterModal('vip', false);
}'''

assert old_prompt_vip in content, "old_prompt_vip not found"
content = content.replace(old_prompt_vip, new_prompt_vip)

# 9. fetchAccessStatus
old_fetch_status = '''async function fetchAccessStatus(){
  try {
    const urlParams = new URLSearchParams(window.location.search);
    let tok = urlParams.get('auth_token') || localStorage.getItem('syd_auth_token') || '';
    if(urlParams.get('auth_token')){
      localStorage.setItem('syd_auth_token', urlParams.get('auth_token'));
    }
    const res = await fetch(`/dl/access/status?token=${encodeURIComponent(tok)}`);
    if(res.ok){
      const data = await res.json();
      const prevWasNotVip = window.userAccess && !window.userAccess.is_vip;
      window.userAccess = data;
      updateAccessUI(data);

      // DEV & ADMIN check: Completely exempt from registration, login, and all modals
      const isDevOrAdmin = !!(data.is_dev || data.role === 'dev' || data.is_admin || data.role === 'admin');
      if(isDevOrAdmin){
        isMandatoryAuth = false;
        closeUserRegisterModal();
      } else if(data.is_banned || data.status === 'banned' || data.status === 'machine_mismatch'){
        isMandatoryAuth = true;
        openUserRegisterModal('banned', true);
        if(data.status === 'machine_mismatch'){
          const bTitle = $("#authBannedTitle");
          const bDesc = $("#authBannedDesc");
          if(bTitle) bTitle.textContent = "🚫 Machine ID មិនត្រូវគ្នា (1 PC = 1 User ប៉ុណ្ណោះ)";
          if(bDesc) bDesc.innerHTML = `<span style="color:#f87171;font-weight:bold">គណនីនេះត្រូវបានភ្ជាប់ជាមួយកុំព្យូទ័រ (PC) ផ្សេងរួចហើយ!</span><br>ប្រព័ន្ធកំណត់ដាច់ខាត 1 Machine ID ប្រើប្រាស់បានតែលើ 1 PC ប៉ុណ្ណោះ មិនអាចប្រើលើកុំព្យូទ័រនេះបានឡើយ។`;
        }
      } else if(!data.authenticated || data.must_register || !data.has_firebase_account){
        openUserRegisterModal('register', true);
      } else {
        isMandatoryAuth = false;
        if(prevWasNotVip && data.is_vip){
          toast(`👑 អបអរសាទរ! ADMIN បានអនុម័តកញ្ចប់ VIP ជូន ${data.name || data.username} រួចរាល់ហើយ! (ដោះសោរគ្រប់ភាគទាំងអស់)`, false);
          closeUserRegisterModal();
        }
      }

      if(typeof renderDramaDetailEpisodes === 'function' && ddCurrentDrama){
        renderDramaDetailEpisodes();
      }
    }
  } catch(e){
    console.error("fetchAccessStatus error", e);
  }
}'''

new_fetch_status = '''async function fetchAccessStatus(){
  try {
    const urlParams = new URLSearchParams(window.location.search);
    let tok = urlParams.get('auth_token') || localStorage.getItem('syd_auth_token') || '';
    if(urlParams.get('auth_token')){
      localStorage.setItem('syd_auth_token', urlParams.get('auth_token'));
    }
    if(typeof fetchDramaRules === 'function'){
      await fetchDramaRules();
    }
    const res = await fetch(`/dl/access/status?token=${encodeURIComponent(tok)}`);
    if(res.ok){
      const data = await res.json();
      const prevWasNotVip = window.userAccess && !window.userAccess.is_vip;
      window.userAccess = data;
      updateAccessUI(data);

      const isAdmin = !!(data.is_admin || data.role === 'admin');
      if(isAdmin){
        isMandatoryAuth = false;
        closeUserRegisterModal();
      } else if(data.status === 'trial_locked_24h'){
        isMandatoryAuth = true;
        openUserRegisterModal('banned', true);
        const bTitle = $("#authBannedTitle");
        const bDesc = $("#authBannedDesc");
        if(bTitle) bTitle.textContent = "⏳ ផុតកំណត់សាកល្បង 3 ថ្ងៃ (បិទ Login 24 ម៉ោង)";
        if(bDesc) bDesc.innerHTML = `<span style="color:#f87171;font-weight:bold">${data.error || "គណនីផុតកំណត់សាកល្បង 3 ថ្ងៃ!"}</span><br>ប្រព័ន្ធបិទការ Login រយៈពេល 24 ម៉ោង ជាបណ្តោះអាសន្ន។ បន្ទាប់ពីផុត 24 ម៉ោង ទើបអាច Login បានធម្មតាវិញ។ ឬទាក់ទង Admin ដើម្បីស្នើសុំកញ្ចប់ VIP។`;
      } else if(data.is_banned || data.status === 'banned' || data.status === 'machine_mismatch'){
        isMandatoryAuth = true;
        openUserRegisterModal('banned', true);
        if(data.status === 'machine_mismatch'){
          const bTitle = $("#authBannedTitle");
          const bDesc = $("#authBannedDesc");
          if(bTitle) bTitle.textContent = "🚫 Machine ID មិនត្រូវគ្នា (1 PC = 1 User ប៉ុណ្ណោះ)";
          if(bDesc) bDesc.innerHTML = `<span style="color:#f87171;font-weight:bold">គណនីនេះត្រូវបានភ្ជាប់ជាមួយកុំព្យូទ័រ (PC) ផ្សេងរួចហើយ!</span><br>ប្រព័ន្ធកំណត់ដាច់ខាត 1 Machine ID ប្រើប្រាស់បានតែលើ 1 PC ប៉ុណ្ណោះ មិនអាចប្រើលើកុំព្យូទ័រនេះបានឡើយ។`;
        }
      } else if(!data.authenticated || data.must_register){
        openUserRegisterModal('login', true);
      } else {
        isMandatoryAuth = false;
        if(prevWasNotVip && data.is_vip){
          toast(`👑 អបអរសាទរ! ADMIN បានអនុម័តកញ្ចប់ VIP ជូន ${data.name || data.username} រួចរាល់ហើយ! (ដោះសោរគ្រប់ភាគទាំងអស់)`, false);
          closeUserRegisterModal();
        }
      }

      if(typeof renderDramaDetailEpisodes === 'function' && ddCurrentDrama){
        renderDramaDetailEpisodes();
      }
    }
  } catch(e){
    console.error("fetchAccessStatus error", e);
  }
}'''

assert old_fetch_status in content, "old_fetch_status not found"
content = content.replace(old_fetch_status, new_fetch_status)

# 10. updateAccessUI (entire body)
old_update_ui = '''function updateAccessUI(data){
  const badge = $("#userAccessBadge");
  const icon = $("#uabIcon");
  const txt = $("#uabText");
  const reqVipBtn = $("#topReqVipBtn");
  const topUc = $("#topUserCtrlBtn");
  const topLogout = $("#topLogoutBtn");
  const footUser = $("#authFootUserLabel");

  const isAdmin = !!(data.is_admin || data.role === 'admin' || data.role === 'dev');
  const isVip = !!(data.is_vip);
  const isPendingVip = (data.status === 'pending_vip');
  const isBanned = (data.status === 'banned' || data.is_banned);
  const isUser = !!(data.username && !isAdmin);

  // Home VIP Promotion Banner Visibility
  const homeVipBanner = $("#homeVipPromoBanner");
  if(homeVipBanner){
    homeVipBanner.style.display = (isAdmin || isVip) ? "none" : "flex";
  }

  const acctBtn = $("#acctBtn");
  if(acctBtn){
    if(isAdmin){
      acctBtn.hidden = false;
      acctBtn.style.display = "inline-flex";
    } else {
      acctBtn.hidden = true;
      acctBtn.style.display = "none";
    }
  }

  // Top bar "👑 ស្នើសុំ VIP" button: Visible to anyone who is not already Admin or approved VIP!
  if(reqVipBtn){
    if(isAdmin || isVip || isBanned){
      reqVipBtn.style.display = "none";
    } else if(isPendingVip){
      reqVipBtn.style.display = "inline-flex";
      reqVipBtn.style.background = "linear-gradient(135deg,#f59e0b,#d97706)";
      reqVipBtn.style.boxShadow = "0 3px 10px rgba(245,158,11,0.35)";
      reqVipBtn.innerHTML = `<span>⏳ សំណើ VIP កំពុងរង់ចាំ</span>`;
      reqVipBtn.title = "សំណើ VIP កំពុងរង់ចាំ Admin អនុម័ត (ចុចដើម្បីមើល)";
    } else {
      reqVipBtn.style.display = "inline-flex";
      reqVipBtn.style.background = "linear-gradient(135deg,#ff6a2b,#ff2e63)";
      reqVipBtn.style.boxShadow = "0 3px 10px rgba(255,106,43,0.3)";
      reqVipBtn.innerHTML = `<span>👑 ស្នើសុំ VIP</span>`;
      reqVipBtn.title = "ស្នើសុំកញ្ចប់ VIP ដើម្បីទស្សនាគ្រប់ភាគ";
    }
  }

  const tabVipBtn = $("#tabBtnVip");
  if(tabVipBtn){
    if(isAdmin || isVip || isBanned){
      tabVipBtn.style.display = "none";
    } else {
      tabVipBtn.style.display = "block";
    }
  }

  // Drama Detail VIP Buttons
  const ddVipBtn = $("#ddVipUnlockBtn");
  const ddVipBanner = $("#ddVipEpisodeBanner");
  if(ddVipBtn){
    ddVipBtn.style.display = (isAdmin || isVip) ? "none" : "inline-flex";
  }
  if(ddVipBanner){
    ddVipBanner.style.display = (isAdmin || isVip) ? "none" : "flex";
  }

  if(isAdmin){
    const isDevRole = !!(data.is_dev || data.role === 'dev');
    if(icon) icon.textContent = isDevRole ? "⚡" : "🛡️";
    if(txt) txt.textContent = isDevRole ? "DEV (Dara - សេរី)" : "ADMIN (Full Control)";
    if(badge){
      badge.style.borderColor = isDevRole ? "#38bdf8" : "#c084fc";
      badge.style.color = isDevRole ? "#38bdf8" : "#c084fc";
      badge.style.background = isDevRole ? "rgba(56,189,248,0.16)" : "rgba(192,132,252,0.14)";
      badge.style.boxShadow = isDevRole ? "0 0 14px rgba(56,189,248,0.4)" : "0 0 12px rgba(192,132,252,0.3)";
    }
    if(topUc) topUc.style.display = "inline-flex";
    const topRestart = $("#topAdminRestartBtn");
    if(topRestart) topRestart.style.display = "inline-flex";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:${isDevRole ? '#38bdf8' : '#c084fc'};font-weight:700">⚡ ចូលជា: ${isDevRole ? 'DEV MASTER (សេរី គ្មានដែនកំណត់)' : 'ADMIN (Full Control)'}</span>`;
    currentAdminPin = localStorage.getItem('syd_auth_token') || '8888';
    sessionStorage.setItem('hg_admin_pin', '8888');
    const pinBox = $("#adminPinBox"); if(pinBox) pinBox.hidden = true;
    const unPanel = $("#adminUnlockedPanel"); if(unPanel) unPanel.hidden = false;
    const lockBadge = $("#adminLockBadge");
    if(lockBadge){
      lockBadge.textContent = isDevRole ? "⚡ DEV MASTER (UNLOCKED)" : "🔓 UNLOCKED (ADMIN)";
      lockBadge.style.color = isDevRole ? "#38bdf8" : "var(--good)";
      lockBadge.style.background = isDevRole ? "rgba(56,189,248,0.18)" : "rgba(46,204,113,0.15)";
    }
    refreshAdminUsersList();

  } else if(isBanned || data.status === 'machine_mismatch'){
    if(icon) icon.textContent = "🚫";
    if(txt) txt.textContent = data.status === 'machine_mismatch' ? "Machine Lock (1 PC)" : "Banned (បិទគណនី)";
    if(badge){
      badge.style.borderColor = "var(--bad)";
      badge.style.color = "var(--bad)";
      badge.style.background = "rgba(255,46,99,0.18)";
      badge.style.boxShadow = "0 0 10px rgba(255,46,99,0.3)";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--bad);font-weight:700">🚫 ${data.status === 'machine_mismatch' ? 'Machine ID មិនត្រូវគ្នា (1 PC Only)' : 'គណនីត្រូវបាន ADMIN បិទ (Banned)'}</span>`;
  } else if(isVip){
    if(icon) icon.textContent = "👑";
    if(txt) txt.textContent = `VIP: ${data.username || data.name || 'សមាជិក'}`;
    if(badge){
      badge.style.borderColor = "var(--good)";
      badge.style.color = "var(--good)";
      badge.style.background = "rgba(46, 204, 113, 0.12)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--good);font-weight:700">👑 ចូលជា: ${esc(data.username || data.name)} (VIP Active)</span>`;
  } else if(isPendingVip){
    if(icon) icon.textContent = "⏳";
    if(txt) txt.textContent = `${data.username} (រង់ចាំ VIP)`;
    if(badge){
      badge.style.borderColor = "var(--gold)";
      badge.style.color = "var(--gold)";
      badge.style.background = "rgba(241,196,15,0.12)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--gold);font-weight:700">⏳ ចូលជា: ${esc(data.username)} (រង់ចាំ Admin អនុម័ត VIP)</span>`;
  } else if(isUser){
    if(icon) icon.textContent = "👤";
    if(txt) txt.textContent = `${data.username} (ភាគ 1-10)`;
    if(badge){
      badge.style.borderColor = "rgba(255,106,43,0.5)";
      badge.style.color = "var(--accent)";
      badge.style.background = "rgba(255,106,43,0.1)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--accent);font-weight:700">👤 ចូលជា: ${esc(data.username)} (ភាគ 1-10 ឥតគិតថ្លៃ)</span>`;
  } else {
    // Guest
    if(icon) icon.textContent = "👤";
    if(txt) txt.textContent = "ចូលគណនី / ចុះឈ្មោះ";
    if(badge){
      badge.style.borderColor = "rgba(255,106,43,0.4)";
      badge.style.color = "var(--ink)";
      badge.style.background = "transparent";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "none";
    if(footUser) footUser.textContent = "មិនទាន់ចូលគណនី (Guest - ភាគ 1-10)";
  }

  // Update elements inside Modal Status Card
  const regDevId = $("#regDeviceId");
  if(regDevId) regDevId.textContent = data.device_id || "Unknown";

  const vipUserDisp = $("#vipUsernameDisplay");
  if(vipUserDisp){
    if(data.username){
      vipUserDisp.textContent = `គណនី: ${data.username}${data.name ? ' (' + data.name + ')' : ''}`;
    } else {
      vipUserDisp.textContent = "មិនទាន់ចូលគណនី (Guest)";
    }
  }

  const regStBadge = $("#regCurrentStatusBadge");
  const regExp = $("#regExpiryText");
  if(regStBadge){
    if(isAdmin){
      regStBadge.textContent = "🛡️ ADMIN (Full Control)";
      regStBadge.style.color = "#c084fc";
      regStBadge.style.background = "rgba(192,132,252,0.2)";
      if(regExp) regExp.textContent = "♾️ គ្មានការ Lock គ្រប់ភាគទាំងអស់";
    } else if(isVip){
      regStBadge.textContent = `👑 VIP Active (${data.package_badge || 'VIP'})`;
      regStBadge.style.color = "var(--good)";
      regStBadge.style.background = "rgba(46,204,113,0.18)";
      if(regExp) regExp.textContent = data.expires_date || "VIP Unlimited";
    } else if(isPendingVip){
      regStBadge.textContent = `⏳ កំពុងរង់ចាំ VIP (${data.requested_package || '1_year'})`;
      regStBadge.style.color = "var(--gold)";
      regStBadge.style.background = "rgba(241,196,15,0.18)";
      if(regExp) regExp.textContent = "រង់ចាំ Admin ត្រួតពិនិត្យ & បើកសិទ្ធិ";
    } else if(isUser){
      regStBadge.textContent = "👤 គណនីធម្មតា (Free Tier)";
      regStBadge.style.color = "var(--accent)";
      regStBadge.style.background = "rgba(255,106,43,0.15)";
      if(regExp) regExp.textContent = "ទស្សនា & ដោនឡូតបានភាគ 1-10";
    } else {
      regStBadge.textContent = "មិនទាន់ចូលគណនី";
      regStBadge.style.color = "var(--muted)";
      regStBadge.style.background = "rgba(255,255,255,0.08)";
      if(regExp) regExp.textContent = "ទស្សនា & ដោនឡូតបានភាគ 1-10";
    }
  }

  // Update Top Navigation Bar Days Remaining Badge
  const topDlBadge = $("#topDaysLeftBadge");
  const topDlIcon = $("#topDaysLeftIcon");
  const topDlText = $("#topDaysLeftText");
  if(topDlBadge){
    if(isAdmin){
      const isDevRole = !!(data.is_dev || data.role === 'dev');
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = isDevRole ? "rgba(56,189,248,0.18)" : "rgba(192,132,252,0.18)";
      topDlBadge.style.border = isDevRole ? "1.5px solid rgba(56,189,248,0.55)" : "1.5px solid rgba(192,132,252,0.55)";
      topDlBadge.style.color = isDevRole ? "#38bdf8" : "#c084fc";
      topDlBadge.style.boxShadow = isDevRole ? "0 0 12px rgba(56,189,248,0.35)" : "0 0 10px rgba(192,132,252,0.25)";
      if(topDlIcon) topDlIcon.textContent = isDevRole ? "⚡" : "♾️";
      if(topDlText) topDlText.textContent = isDevRole ? "DEV MASTER (សេរី)" : "គ្មានដែនកំណត់ (ADMIN)";
      topDlBadge.title = isDevRole ? "Developer Machine (ប្រើប្រាស់បានដោយសេរី គ្មានដែនកំណត់ មិនបាច់ Login)" : "គណនី Super Admin (Full Control - គ្មានដែនកំណត់)";
    } else if(isBanned || data.status === 'machine_mismatch'){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(255,46,99,0.22)";
      topDlBadge.style.border = "1.5px solid rgba(255,46,99,0.7)";
      topDlBadge.style.color = "var(--bad)";
      topDlBadge.style.boxShadow = "0 0 12px rgba(255,46,99,0.4)";
      if(topDlIcon) topDlIcon.textContent = "🚫";
      if(topDlText) topDlText.textContent = data.status === 'machine_mismatch' ? "Machine Lock (1 PC)" : "គណនីត្រូវបានបិទ (Banned)";
      topDlBadge.title = data.status === 'machine_mismatch' ? "គណនីខុសកុំព្យូទ័រ (1 Machine ID / 1 PC Only)" : "គណនីត្រូវបាន ADMIN បិទដំណើរការ";
    } else if(isVip){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(46,204,113,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(46,204,113,0.55)";
      topDlBadge.style.color = "var(--good)";
      topDlBadge.style.boxShadow = "0 0 10px rgba(46,204,113,0.25)";
      if(topDlIcon) topDlIcon.textContent = "👑";
      const vipDays = data.days_left < 0 ? "គ្មានដែនកំណត់" : `${data.days_left} ថ្ងៃ`;
      if(topDlText) topDlText.textContent = `VIP: នៅសល់ ${vipDays}`;
      topDlBadge.title = `គណនី VIP Member (នៅសល់ ${vipDays}) កាលបរិច្ឆេទផុតកំណត់៖ ${data.expires_date || ''}`;
    } else if(isPendingVip){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(245,158,11,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(245,158,11,0.55)";
      topDlBadge.style.color = "#f59e0b";
      topDlBadge.style.boxShadow = "0 0 10px rgba(245,158,11,0.25)";
      if(topDlIcon) topDlIcon.textContent = "⏳";
      if(topDlText) topDlText.textContent = `រង់ចាំ VIP (${data.days_left !== undefined ? data.days_left : 7} ថ្ងៃ)`;
      topDlBadge.title = "សំណើ VIP កំពុងរង់ចាំ Admin អនុម័ត";
    } else if(isUser){
      topDlBadge.style.display = "inline-flex";
      const uDays = (data.days_left !== undefined && data.days_left !== null) ? data.days_left : 7;
      if(uDays <= 2){
        topDlBadge.style.background = "rgba(239,68,68,0.22)";
        topDlBadge.style.border = "1.5px solid rgba(239,68,68,0.7)";
        topDlBadge.style.color = "#ef4444";
        topDlBadge.style.boxShadow = "0 0 12px rgba(239,68,68,0.4)";
        if(topDlIcon) topDlIcon.textContent = "⚠️";
        if(topDlText) topDlText.textContent = `នៅសល់តែ ${uDays} ថ្ងៃ (ប្រញាប់ស្នើ VIP!)`;
      } else {
        topDlBadge.style.background = "rgba(255,106,43,0.16)";
        topDlBadge.style.border = "1.5px solid rgba(255,106,43,0.5)";
        topDlBadge.style.color = "var(--accent)";
        topDlBadge.style.boxShadow = "0 0 10px rgba(255,106,43,0.2)";
        if(topDlIcon) topDlIcon.textContent = "⏳";
        if(topDlText) topDlText.textContent = `User: នៅសល់ ${uDays} ថ្ងៃ (សាកល្បង)`;
      }
      topDlBadge.title = `User ធម្មតាមានរយៈពេល 7 ថ្ងៃសាកល្បង (នៅសល់ ${uDays} ថ្ងៃ)។ បើមិនស្នើសុំ VIP ទេ គណនីនឹងត្រូវលុបចោលចេញពីប្រព័ន្ធដាច់ខាត!`;
    } else {
      topDlBadge.style.display = "none";
    }
  }

  // Update Modal Days Remaining Badge & 7-Day Trial Notice
  const mDaysBadge = $("#modalDaysRemainingBadge");
  const mDaysIcon = $("#modalDaysIcon");
  const mNotice = $("#modalTrialRuleNotice");
  if(mDaysBadge){
    if(isAdmin){
      mDaysBadge.textContent = "♾️ គ្មានដែនកំណត់ (ADMIN Full Control)";
      mDaysBadge.style.background = "rgba(192,132,252,0.2)";
      mDaysBadge.style.color = "#c084fc";
      if(mDaysIcon) mDaysIcon.textContent = "♾️";
      if(mNotice) mNotice.style.display = "none";
    } else if(isVip){
      const vDays = data.days_left < 0 ? "គ្មានដែនកំណត់" : `${data.days_left} ថ្ងៃ`;
      mDaysBadge.textContent = `👑 នៅសល់ ${vDays} (ផុតកំណត់: ${data.expires_date || ''})`;
      mDaysBadge.style.background = "rgba(46,204,113,0.18)";
      mDaysBadge.style.color = "var(--good)";
      if(mDaysIcon) mDaysIcon.textContent = "👑";
      if(mNotice) mNotice.style.display = "none";
    } else if(isPendingVip){
      const pDays = data.days_left !== undefined ? data.days_left : 7;
      mDaysBadge.textContent = `⏳ សំណើ VIP កំពុងរង់ចាំ Admin (នៅសល់ ${pDays} ថ្ងៃ)`;
      mDaysBadge.style.background = "rgba(245,158,11,0.18)";
      mDaysBadge.style.color = "#f59e0b";
      if(mDaysIcon) mDaysIcon.textContent = "⏳";
      if(mNotice) mNotice.style.display = "none";
    } else if(isUser){
      const uDays = (data.days_left !== undefined && data.days_left !== null) ? data.days_left : 7;
      mDaysBadge.textContent = `⏳ នៅសល់ ${uDays} ថ្ងៃ (ផុតកំណត់: ${data.expires_date || ''})`;
      mDaysBadge.style.background = uDays <= 2 ? "rgba(239,68,68,0.2)" : "rgba(255,106,43,0.15)";
      mDaysBadge.style.color = uDays <= 2 ? "#ef4444" : "var(--accent)";
      if(mDaysIcon) mDaysIcon.textContent = uDays <= 2 ? "⚠️" : "⏳";
      if(mNotice) mNotice.style.display = "block";
    } else {
      mDaysBadge.textContent = "មិនទាន់ចុះឈ្មោះ (Guest)";
      mDaysBadge.style.background = "rgba(255,255,255,0.08)";
      mDaysBadge.style.color = "var(--muted)";
      if(mDaysIcon) mDaysIcon.textContent = "👤";
      if(mNotice) mNotice.style.display = "none";
    }
  }

  if(data.name && $("#regNameInput") && !$("#regNameInput").value) $("#regNameInput").value = data.name;
  if(data.contact && $("#regContactInput") && !$("#regContactInput").value) $("#regContactInput").value = data.contact;

  if(data.settings){
    updateVipPortalSettings(data.settings, data);
  }
}

// User Action Handlers
const uabBtn = $("#userAccessBadge");
if(uabBtn) uabBtn.onclick = () => {
  if(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin' || window.userAccess.role === 'dev')){
    openUserControl();
  } else if(window.userAccess && window.userAccess.authenticated && !window.userAccess.is_vip){
    openUserRegisterModal('vip');
  } else {
    openUserRegisterModal('login');
  }
};'''

new_update_ui = '''function updateAccessUI(data){
  const badge = $("#userAccessBadge");
  const icon = $("#uabIcon");
  const txt = $("#uabText");
  const reqVipBtn = $("#topReqVipBtn");
  const topUc = $("#topUserCtrlBtn");
  const topLogout = $("#topLogoutBtn");
  const footUser = $("#authFootUserLabel");

  const isAdmin = !!(data.is_admin || data.role === 'admin');
  const isVip = !!(data.is_vip);
  const isPendingVip = (data.status === 'pending_vip');
  const isLocked24h = (data.status === 'trial_locked_24h');
  const isBanned = (data.status === 'banned' || data.is_banned);
  const isUser = !!(data.username && !isAdmin);

  // Home VIP Promotion Banner Visibility
  const homeVipBanner = $("#homeVipPromoBanner");
  if(homeVipBanner){
    homeVipBanner.style.display = (isAdmin || isVip) ? "none" : "flex";
  }

  const acctBtn = $("#acctBtn");
  if(acctBtn){
    if(isAdmin){
      acctBtn.hidden = false;
      acctBtn.style.display = "inline-flex";
    } else {
      acctBtn.hidden = true;
      acctBtn.style.display = "none";
    }
  }

  // Top bar "👑 ស្នើសុំ VIP" button: Visible to anyone who is not already Admin or approved VIP!
  if(reqVipBtn){
    if(isAdmin || isVip || isBanned || isLocked24h){
      reqVipBtn.style.display = "none";
    } else if(isPendingVip){
      reqVipBtn.style.display = "inline-flex";
      reqVipBtn.style.background = "linear-gradient(135deg,#f59e0b,#d97706)";
      reqVipBtn.style.boxShadow = "0 3px 10px rgba(245,158,11,0.35)";
      reqVipBtn.innerHTML = `<span>⏳ សំណើ VIP កំពុងរង់ចាំ</span>`;
      reqVipBtn.title = "សំណើ VIP កំពុងរង់ចាំ Admin អនុម័ត (ចុចដើម្បីមើល)";
    } else {
      reqVipBtn.style.display = "inline-flex";
      reqVipBtn.style.background = "linear-gradient(135deg,#ff6a2b,#ff2e63)";
      reqVipBtn.style.boxShadow = "0 3px 10px rgba(255,106,43,0.3)";
      reqVipBtn.innerHTML = `<span>👑 ស្នើសុំ VIP</span>`;
      reqVipBtn.title = "ស្នើសុំកញ្ចប់ VIP ដើម្បីទស្សនាគ្រប់ភាគ";
    }
  }

  const tabVipBtn = $("#tabBtnVip");
  if(tabVipBtn){
    if(isAdmin || isVip || isBanned || isLocked24h){
      tabVipBtn.style.display = "none";
    } else {
      tabVipBtn.style.display = "block";
    }
  }

  // Drama Detail VIP Buttons
  const ddVipBtn = $("#ddVipUnlockBtn");
  const ddVipBanner = $("#ddVipEpisodeBanner");
  if(ddVipBtn){
    ddVipBtn.style.display = (isAdmin || isVip) ? "none" : "inline-flex";
  }
  if(ddVipBanner){
    ddVipBanner.style.display = (isAdmin || isVip) ? "none" : "flex";
  }

  if(isAdmin){
    if(icon) icon.textContent = "🛡️";
    if(txt) txt.textContent = "ADMIN (Full Control)";
    if(badge){
      badge.style.borderColor = "#c084fc";
      badge.style.color = "#c084fc";
      badge.style.background = "rgba(192,132,252,0.14)";
      badge.style.boxShadow = "0 0 12px rgba(192,132,252,0.3)";
    }
    if(topUc) topUc.style.display = "inline-flex";
    const topRestart = $("#topAdminRestartBtn");
    if(topRestart) topRestart.style.display = "inline-flex";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:#c084fc;font-weight:700">🛡️ ចូលជា: ADMIN (Full Control)</span>`;
    currentAdminPin = localStorage.getItem('syd_auth_token') || 'syd@168';
    sessionStorage.setItem('hg_admin_pin', 'syd@168');
    const pinBox = $("#adminPinBox"); if(pinBox) pinBox.hidden = true;
    const unPanel = $("#adminUnlockedPanel"); if(unPanel) unPanel.hidden = false;
    const lockBadge = $("#adminLockBadge");
    if(lockBadge){
      lockBadge.textContent = "🔓 UNLOCKED (ADMIN)";
      lockBadge.style.color = "var(--good)";
      lockBadge.style.background = "rgba(46,204,113,0.15)";
    }
    refreshAdminUsersList();

  } else if(isLocked24h){
    if(icon) icon.textContent = "⏳";
    if(txt) txt.textContent = `បិទ 24 ម៉ោង (សល់ ${data.hours_left || 24}h)`;
    if(badge){
      badge.style.borderColor = "#f59e0b";
      badge.style.color = "#f59e0b";
      badge.style.background = "rgba(245,158,11,0.18)";
      badge.style.boxShadow = "0 0 10px rgba(245,158,11,0.3)";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:#f59e0b;font-weight:700">⏳ គណនីបិទ Login 24 ម៉ោង (សាកល្បង 3 ថ្ងៃផុតកំណត់)</span>`;
  } else if(isBanned || data.status === 'machine_mismatch'){
    if(icon) icon.textContent = "🚫";
    if(txt) txt.textContent = data.status === 'machine_mismatch' ? "Machine Lock (1 PC)" : "Banned (បិទគណនី)";
    if(badge){
      badge.style.borderColor = "var(--bad)";
      badge.style.color = "var(--bad)";
      badge.style.background = "rgba(255,46,99,0.18)";
      badge.style.boxShadow = "0 0 10px rgba(255,46,99,0.3)";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--bad);font-weight:700">🚫 ${data.status === 'machine_mismatch' ? 'Machine ID មិនត្រូវគ្នា (1 PC Only)' : 'គណនីត្រូវបាន ADMIN បិទ (Banned)'}</span>`;
  } else if(isVip){
    if(icon) icon.textContent = "👑";
    if(txt) txt.textContent = `VIP: ${data.username || data.name || 'សមាជិក'}`;
    if(badge){
      badge.style.borderColor = "var(--good)";
      badge.style.color = "var(--good)";
      badge.style.background = "rgba(46, 204, 113, 0.12)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--good);font-weight:700">👑 ចូលជា: ${esc(data.username || data.name)} (VIP Active)</span>`;
  } else if(isPendingVip){
    if(icon) icon.textContent = "⏳";
    if(txt) txt.textContent = `${data.username} (រង់ចាំ VIP)`;
    if(badge){
      badge.style.borderColor = "var(--gold)";
      badge.style.color = "var(--gold)";
      badge.style.background = "rgba(241,196,15,0.12)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--gold);font-weight:700">⏳ ចូលជា: ${esc(data.username)} (រង់ចាំ Admin អនុម័ត VIP)</span>`;
  } else if(isUser){
    if(icon) icon.textContent = "👤";
    if(txt) txt.textContent = `${data.username} (ភាគ 1-10)`;
    if(badge){
      badge.style.borderColor = "rgba(255,106,43,0.5)";
      badge.style.color = "var(--accent)";
      badge.style.background = "rgba(255,106,43,0.1)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--accent);font-weight:700">👤 ចូលជា: ${esc(data.username)} (ភាគ 1-10 ឥតគិតថ្លៃ)</span>`;
  } else {
    // Guest
    if(icon) icon.textContent = "👤";
    if(txt) txt.textContent = "ចូលគណនី / ចុះឈ្មោះ";
    if(badge){
      badge.style.borderColor = "rgba(255,106,43,0.4)";
      badge.style.color = "var(--ink)";
      badge.style.background = "transparent";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "none";
    if(footUser) footUser.textContent = "មិនទាន់ចូលគណនី (Guest - ភាគ 1-10)";
  }

  // Update elements inside Modal Status Card
  const regDevId = $("#regDeviceId");
  if(regDevId) regDevId.textContent = data.device_id || "Unknown";

  const vipUserDisp = $("#vipUsernameDisplay");
  if(vipUserDisp){
    if(data.username){
      vipUserDisp.textContent = `គណនី: ${data.username}${data.name ? ' (' + data.name + ')' : ''}`;
    } else {
      vipUserDisp.textContent = "មិនទាន់ចូលគណនី (Guest)";
    }
  }

  const regStBadge = $("#regCurrentStatusBadge");
  const regExp = $("#regExpiryText");
  if(regStBadge){
    if(isAdmin){
      regStBadge.textContent = "🛡️ ADMIN (Full Control)";
      regStBadge.style.color = "#c084fc";
      regStBadge.style.background = "rgba(192,132,252,0.2)";
      if(regExp) regExp.textContent = "♾️ គ្មានការ Lock គ្រប់ភាគទាំងអស់";
    } else if(isLocked24h){
      regStBadge.textContent = `⏳ បិទ Login 24 ម៉ោង (នៅសល់ ${data.hours_left || 24}h)`;
      regStBadge.style.color = "#f59e0b";
      regStBadge.style.background = "rgba(245,158,11,0.18)";
      if(regExp) regExp.textContent = "ផុតកំណត់ 3 ថ្ងៃ · រង់ចាំផុត 24 ម៉ោង ឬទាក់ទង Admin";
    } else if(isVip){
      regStBadge.textContent = `👑 VIP Active (${data.package_badge || 'VIP'})`;
      regStBadge.style.color = "var(--good)";
      regStBadge.style.background = "rgba(46,204,113,0.18)";
      if(regExp) regExp.textContent = data.expires_date || "VIP Unlimited";
    } else if(isPendingVip){
      regStBadge.textContent = `⏳ កំពុងរង់ចាំ VIP (${data.requested_package || '1_year'})`;
      regStBadge.style.color = "var(--gold)";
      regStBadge.style.background = "rgba(241,196,15,0.18)";
      if(regExp) regExp.textContent = "រង់ចាំ Admin ត្រួតពិនិត្យ & បើកសិទ្ធិ";
    } else if(isUser){
      regStBadge.textContent = "👤 គណនីធម្មតា (Free Tier)";
      regStBadge.style.color = "var(--accent)";
      regStBadge.style.background = "rgba(255,106,43,0.15)";
      if(regExp) regExp.textContent = "ទស្សនា & ដោនឡូតបានភាគ 1-10";
    } else {
      regStBadge.textContent = "មិនទាន់ចូលគណនី";
      regStBadge.style.color = "var(--muted)";
      regStBadge.style.background = "rgba(255,255,255,0.08)";
      if(regExp) regExp.textContent = "ទស្សនា & ដោនឡូតបានភាគ 1-10";
    }
  }

  // Update Top Navigation Bar Days Remaining Badge
  const topDlBadge = $("#topDaysLeftBadge");
  const topDlIcon = $("#topDaysLeftIcon");
  const topDlText = $("#topDaysLeftText");
  if(topDlBadge){
    if(isAdmin){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(192,132,252,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(192,132,252,0.55)";
      topDlBadge.style.color = "#c084fc";
      topDlBadge.style.boxShadow = "0 0 10px rgba(192,132,252,0.25)";
      if(topDlIcon) topDlIcon.textContent = "♾️";
      if(topDlText) topDlText.textContent = "គ្មានដែនកំណត់ (ADMIN)";
      topDlBadge.title = "គណនី Super Admin (Full Control - គ្មានដែនកំណត់)";
    } else if(isLocked24h){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(245,158,11,0.22)";
      topDlBadge.style.border = "1.5px solid rgba(245,158,11,0.7)";
      topDlBadge.style.color = "#f59e0b";
      topDlBadge.style.boxShadow = "0 0 12px rgba(245,158,11,0.4)";
      if(topDlIcon) topDlIcon.textContent = "⏳";
      if(topDlText) topDlText.textContent = `បិទ 24 ម៉ោង (នៅសល់ ${data.hours_left || 24}h)`;
      topDlBadge.title = "គណនីផុតកំណត់សាកល្បង 3 ថ្ងៃ ត្រូវបានបិទ Login បណ្តោះអាសន្ន 24 ម៉ោង";
    } else if(isBanned || data.status === 'machine_mismatch'){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(255,46,99,0.22)";
      topDlBadge.style.border = "1.5px solid rgba(255,46,99,0.7)";
      topDlBadge.style.color = "var(--bad)";
      topDlBadge.style.boxShadow = "0 0 12px rgba(255,46,99,0.4)";
      if(topDlIcon) topDlIcon.textContent = "🚫";
      if(topDlText) topDlText.textContent = data.status === 'machine_mismatch' ? "Machine Lock (1 PC)" : "គណនីត្រូវបានបិទ (Banned)";
      topDlBadge.title = data.status === 'machine_mismatch' ? "គណនីខុសកុំព្យូទ័រ (1 Machine ID / 1 PC Only)" : "គណនីត្រូវបាន ADMIN បិទដំណើរការ";
    } else if(isVip){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(46,204,113,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(46,204,113,0.55)";
      topDlBadge.style.color = "var(--good)";
      topDlBadge.style.boxShadow = "0 0 10px rgba(46,204,113,0.25)";
      if(topDlIcon) topDlIcon.textContent = "👑";
      const vipDays = data.days_left < 0 ? "គ្មានដែនកំណត់" : `${data.days_left} ថ្ងៃ`;
      if(topDlText) topDlText.textContent = `VIP: នៅសល់ ${vipDays}`;
      topDlBadge.title = `គណនី VIP Member (នៅសល់ ${vipDays}) កាលបរិច្ឆេទផុតកំណត់៖ ${data.expires_date || ''}`;
    } else if(isPendingVip){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(245,158,11,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(245,158,11,0.55)";
      topDlBadge.style.color = "#f59e0b";
      topDlBadge.style.boxShadow = "0 0 10px rgba(245,158,11,0.25)";
      if(topDlIcon) topDlIcon.textContent = "⏳";
      if(topDlText) topDlText.textContent = `រង់ចាំ VIP (${data.days_left !== undefined ? data.days_left : 3} ថ្ងៃ)`;
      topDlBadge.title = "សំណើ VIP កំពុងរង់ចាំ Admin អនុម័ត";
    } else if(isUser){
      topDlBadge.style.display = "inline-flex";
      const uDays = (data.days_left !== undefined && data.days_left !== null) ? data.days_left : 3;
      if(uDays <= 1){
        topDlBadge.style.background = "rgba(239,68,68,0.22)";
        topDlBadge.style.border = "1.5px solid rgba(239,68,68,0.7)";
        topDlBadge.style.color = "#ef4444";
        topDlBadge.style.boxShadow = "0 0 12px rgba(239,68,68,0.4)";
        if(topDlIcon) topDlIcon.textContent = "⚠️";
        if(topDlText) topDlText.textContent = `នៅសល់តែ ${uDays} ថ្ងៃ (ប្រញាប់ស្នើ VIP!)`;
      } else {
        topDlBadge.style.background = "rgba(255,106,43,0.16)";
        topDlBadge.style.border = "1.5px solid rgba(255,106,43,0.5)";
        topDlBadge.style.color = "var(--accent)";
        topDlBadge.style.boxShadow = "0 0 10px rgba(255,106,43,0.2)";
        if(topDlIcon) topDlIcon.textContent = "⏳";
        if(topDlText) topDlText.textContent = `User: នៅសល់ ${uDays} ថ្ងៃ (សាកល្បង)`;
      }
      topDlBadge.title = `User ធម្មតាមានរយៈពេល 3 ថ្ងៃសាកល្បង (នៅសល់ ${uDays} ថ្ងៃ)។ បើមិនស្នើសុំ VIP ទេ ប្រព័ន្ធនឹងបិទការ Login រយៈពេល 24 ម៉ោង!`;
    } else {
      topDlBadge.style.display = "none";
    }
  }

  // Update Modal Days Remaining Badge & Trial Notice
  const mDaysBadge = $("#modalDaysRemainingBadge");
  const mDaysIcon = $("#modalDaysIcon");
  const mNotice = $("#modalTrialRuleNotice");
  if(mDaysBadge){
    if(isAdmin){
      mDaysBadge.textContent = "♾️ គ្មានដែនកំណត់ (ADMIN Full Control)";
      mDaysBadge.style.background = "rgba(192,132,252,0.2)";
      mDaysBadge.style.color = "#c084fc";
      if(mDaysIcon) mDaysIcon.textContent = "♾️";
      if(mNotice) mNotice.style.display = "none";
    } else if(isLocked24h){
      mDaysBadge.textContent = `⏳ បិទ Login 24 ម៉ោង (នៅសល់ ${data.hours_left || 24}h)`;
      mDaysBadge.style.background = "rgba(245,158,11,0.2)";
      mDaysBadge.style.color = "#f59e0b";
      if(mDaysIcon) mDaysIcon.textContent = "⏳";
      if(mNotice) mNotice.style.display = "block";
    } else if(isVip){
      const vDays = data.days_left < 0 ? "គ្មានដែនកំណត់" : `${data.days_left} ថ្ងៃ`;
      mDaysBadge.textContent = `👑 នៅសល់ ${vDays} (ផុតកំណត់: ${data.expires_date || ''})`;
      mDaysBadge.style.background = "rgba(46,204,113,0.18)";
      mDaysBadge.style.color = "var(--good)";
      if(mDaysIcon) mDaysIcon.textContent = "👑";
      if(mNotice) mNotice.style.display = "none";
    } else if(isPendingVip){
      const pDays = data.days_left !== undefined ? data.days_left : 3;
      mDaysBadge.textContent = `⏳ សំណើ VIP កំពុងរង់ចាំ Admin (នៅសល់ ${pDays} ថ្ងៃ)`;
      mDaysBadge.style.background = "rgba(245,158,11,0.18)";
      mDaysBadge.style.color = "#f59e0b";
      if(mDaysIcon) mDaysIcon.textContent = "⏳";
      if(mNotice) mNotice.style.display = "none";
    } else if(isUser){
      const uDays = (data.days_left !== undefined && data.days_left !== null) ? data.days_left : 3;
      mDaysBadge.textContent = `⏳ នៅសល់ ${uDays} ថ្ងៃ (ផុតកំណត់: ${data.expires_date || ''})`;
      mDaysBadge.style.background = uDays <= 1 ? "rgba(239,68,68,0.2)" : "rgba(255,106,43,0.15)";
      mDaysBadge.style.color = uDays <= 1 ? "#ef4444" : "var(--accent)";
      if(mDaysIcon) mDaysIcon.textContent = uDays <= 1 ? "⚠️" : "⏳";
      if(mNotice) mNotice.style.display = "block";
    } else {
      mDaysBadge.textContent = "មិនទាន់ចុះឈ្មោះ (Guest)";
      mDaysBadge.style.background = "rgba(255,255,255,0.08)";
      mDaysBadge.style.color = "var(--muted)";
      if(mDaysIcon) mDaysIcon.textContent = "👤";
      if(mNotice) mNotice.style.display = "none";
    }
  }

  if(data.name && $("#regNameInput") && !$("#regNameInput").value) $("#regNameInput").value = data.name;
  if(data.contact && $("#regContactInput") && !$("#regContactInput").value) $("#regContactInput").value = data.contact;

  if(data.settings){
    updateVipPortalSettings(data.settings, data);
  }
}

// User Action Handlers
const uabBtn = $("#userAccessBadge");
if(uabBtn) uabBtn.onclick = () => {
  if(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin')){
    openUserControl();
  } else if(window.userAccess && window.userAccess.authenticated && !window.userAccess.is_vip){
    openUserRegisterModal('vip');
  } else {
    openUserRegisterModal('login');
  }
};'''

assert old_update_ui in content, "old_update_ui not found"
content = content.replace(old_update_ui, new_update_ui)

# 11. executeLogin admin handling
old_login_admin = '''      if(j.user && (j.user.is_admin || j.user.role === 'admin')){
        sessionStorage.setItem('hg_admin_pin', '8888');
        currentAdminPin = (j.token || '8888');'''

new_login_admin = '''      if(j.user && (j.user.is_admin || j.user.role === 'admin')){
        sessionStorage.setItem('hg_admin_pin', 'syd@168');
        currentAdminPin = (j.token || 'syd@168');'''

assert old_login_admin in content, "old_login_admin not found"
content = content.replace(old_login_admin, new_login_admin)

# 12. window.switchUcTab and Drama Free Rules
old_switch_tab = '''/* ---------- Tab Switcher for Admin Dashboard ---------- */
window.switchUcTab = function(tab){
  const bUsers = $("#ucTabBtnUsers"), bSet = $("#ucTabBtnSettings"), bSys = $("#ucTabBtnSys"), bFb = $("#ucTabBtnFirebase");
  const sUsers = $("#ucTabUsersSec"), sSet = $("#ucTabSettingsSec"), sSys = $("#ucTabSysSec"), sFb = $("#ucTabFirebaseSec");
  if(bUsers) bUsers.classList.toggle('on', tab === 'users');
  if(bSet) bSet.classList.toggle('on', tab === 'settings');
  if(bSys) bSys.classList.toggle('on', tab === 'system');
  if(bFb) bFb.classList.toggle('on', tab === 'firebase');
  if(sUsers) sUsers.style.display = (tab === 'users') ? 'flex' : 'none';
  if(sSet) sSet.style.display = (tab === 'settings') ? 'flex' : 'none';
  if(sSys) sSys.style.display = (tab === 'system') ? 'flex' : 'none';
  if(sFb) sFb.style.display = (tab === 'firebase') ? 'flex' : 'none';

  if(tab === 'firebase'){
    loadFirebaseConfig();
    refreshFirebaseLicenses();
  }
};'''

new_switch_tab = '''/* ---------- Drama Free Rules Management (Admin & Episode Lock Engine) ---------- */
let cachedDramaRules = {};

async function fetchDramaRules(){
  try {
    const res = await fetch("/dl/drama/rules");
    if(res.ok){
      const data = await res.json();
      if(data.ok && data.rules){
        cachedDramaRules = data.rules;
        if(ddCurrentDrama && typeof renderDramaDetailUI === 'function'){
          renderDramaDetailUI(ddCurrentDrama);
          if(typeof renderDramaDetailEpisodes === 'function'){
            renderDramaDetailEpisodes();
          }
        }
      }
    }
  } catch(e){
    console.error("fetchDramaRules error", e);
  }
}

function getDramaRuleForSeries(sid){
  if(!sid) return null;
  return cachedDramaRules[String(sid)] || null;
}

async function doAdminSetDramaRule(rule, freeEps = 10){
  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  if(!isAdmin){
    toast("⚠️ សិទ្ធិនេះសម្រាប់តែ ADMIN ប៉ុណ្ណោះ!", true);
    return;
  }
  if(!ddCurrentDrama || !ddCurrentDrama.id){
    toast("⚠️ រកមិនឃើញរឿងដែលកំពុងបើកឡើយ!", true);
    return;
  }
  const sid = String(ddCurrentDrama.id);
  const title = ddCurrentDrama.title_km || ddCurrentDrama.title || `Drama ${sid}`;
  const pin = currentAdminPin || 'syd@168';
  const tok = localStorage.getItem('syd_auth_token') || '';

  try {
    const res = await fetch("/dl/admin/drama_rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin, token: tok, series_id: sid, title,
        rule: rule, free_episodes: Number(freeEps) || 10
      })
    });
    const j = await res.json();
    if(j.ok){
      cachedDramaRules[sid] = j.rule || { rule, free_episodes: Number(freeEps) || 10, title };
      toast(rule === 'free_all' ? "🟢 បានកំណត់រឿងនេះ Free 100% (គ្រប់ភាគ) ជោគជ័យ!" : `🟠 បានកំណត់រឿងនេះ Free 1-${freeEps} ភាគ ជោគជ័យ!`);
      if(ddCurrentDrama){
        renderDramaDetailUI(ddCurrentDrama);
        renderDramaDetailEpisodes();
      }
    } else {
      toast("❌ " + (j.error || "បរាជ័យក្នុងការកំណត់"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ: " + e, true);
  }
}

function doAdminCustomDramaRule(){
  const sid = ddCurrentDrama && ddCurrentDrama.id ? String(ddCurrentDrama.id) : '';
  const r = sid ? getDramaRuleForSeries(sid) : null;
  const curLimit = (r && r.free_episodes) ? r.free_episodes : 10;
  const val = prompt("បញ្ចូលចំនួនភាគ Free សម្រាប់រឿងនេះ (ឧទាហរណ៍: 5, 10, 15, 20...):", String(curLimit));
  if(val === null) return;
  const num = parseInt(val, 10);
  if(isNaN(num) || num < 1){
    toast("⚠️ សូមបញ្ចូលចំនួនភាគត្រឹមត្រូវ (ធំជាង 0)", true);
    return;
  }
  doAdminSetDramaRule('free_episodes', num);
}

function toggleAdminDrCustomEps(){
  const sel = $("#adminDrRuleType");
  const inp = $("#adminDrCustomEps");
  if(!sel || !inp) return;
  inp.style.display = (sel.value === 'custom') ? 'inline-block' : 'none';
}

async function loadAdminDramaRules(){
  const container = $("#adminDramaRulesContainer");
  const countEl = $("#adminDrCount");
  if(container) container.innerHTML = '<div style="text-align:center;padding:16px;color:var(--muted);font-size:12px">⏳ កំពុងទាញយកបញ្ជីកំណត់សិទ្ធិ...</div>';
  const pin = currentAdminPin || 'syd@168';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch(`/dl/admin/drama_rules?pin=${encodeURIComponent(pin)}&token=${encodeURIComponent(tok)}`);
    const j = await res.json();
    if(j.ok && j.rules){
      cachedDramaRules = j.rules;
      renderAdminDramaRulesList();
    } else {
      if(container) container.innerHTML = `<div style="text-align:center;padding:14px;color:var(--bad);font-size:12px">❌ ${esc(j.error || "មិនអាចទាញយកទិន្នន័យបាន")}</div>`;
    }
  } catch(e){
    if(container) container.innerHTML = `<div style="text-align:center;padding:14px;color:var(--bad);font-size:12px">⚠️ កំហុសបណ្តាញ: ${esc(String(e))}</div>`;
  }
}

function renderAdminDramaRulesList(){
  const container = $("#adminDramaRulesContainer");
  const countEl = $("#adminDrCount");
  if(!container) return;

  const entries = Object.entries(cachedDramaRules || {});
  if(countEl) countEl.textContent = entries.length;

  if(!entries.length){
    container.innerHTML = `
      <div style="text-align:center;padding:24px 12px;color:var(--muted);font-size:12px;background:var(--surface);border-radius:8px;border:1px dashed var(--line)">
        <div>📂 មិនទាន់មានរឿងណាមួយត្រូវបានកំណត់ដោយឡែកនៅឡើយទេ។</div>
        <div style="margin-top:4px;color:var(--ink-2);font-size:11.5px">តាមធម្មតា រឿងទាំងអស់ Free ភាគ 1-10 សម្រាប់ User ធម្មតា។ Admin អាចជ្រើសកំណត់ Free 100% ឬកំណត់ភាគផ្ទាល់តាមចិត្តចង់។</div>
      </div>
    `;
    return;
  }

  let html = '';
  entries.forEach(([sid, r]) => {
    const isFreeAll = (r.rule === 'free_all');
    const badgeText = isFreeAll ? "🟢 Free 100% (គ្រប់ភាគ)" : `🟠 Free ភាគ 1-${r.free_episodes || 10}`;
    const badgeBg = isFreeAll ? "rgba(34,197,94,0.18)" : "rgba(255,106,43,0.16)";
    const badgeColor = isFreeAll ? "#22c55e" : "var(--accent)";
    const titleText = r.title || `Series ID: ${sid}`;

    html += `
      <div style="background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
        <div style="display:flex;flex-direction:column;gap:3px;flex:1;min-width:200px">
          <div style="font-weight:700;font-size:13px;color:var(--ink);display:flex;align-items:center;gap:6px">
            <span>🎬</span> <span>${esc(titleText)}</span>
          </div>
          <div style="font-size:11.5px;color:var(--muted);display:flex;gap:8px;align-items:center">
            <code>ID: ${esc(sid)}</code>
            <span>·</span>
            <span style="display:inline-block;padding:2px 8px;border-radius:6px;background:${badgeBg};color:${badgeColor};font-weight:700;font-size:11px">${badgeText}</span>
          </div>
        </div>
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
          <button type="button" class="btn sm" onclick="quickToggleAdminDramaRule('${esc(sid)}', '${isFreeAll ? 'free_episodes' : 'free_all'}')" style="font-weight:700;font-size:11px;padding:4px 10px;border-radius:6px;background:${isFreeAll ? 'rgba(255,106,43,0.15)' : 'rgba(34,197,94,0.15)'};color:${isFreeAll ? 'var(--accent)' : '#22c55e'}">
            ${isFreeAll ? '🟠 ប្តូរមក Free 1-10' : '🟢 ប្តូរមក Free 100%'}
          </button>
          <button type="button" class="btn ghost sm" onclick="quickDeleteAdminDramaRule('${esc(sid)}')" style="font-weight:700;font-size:11px;padding:4px 8px;border-radius:6px;color:var(--bad)" title="លុបចោលការកំណត់">
            🗑️ លុប
          </button>
        </div>
      </div>
    `;
  });

  container.innerHTML = html;
}

async function submitAdminDramaRule(){
  const sidInp = $("#adminDrSeriesId");
  const sid = (sidInp && sidInp.value.trim()) || '';
  if(!sid){
    toast("⚠️ សូមបញ្ចូល Series ID ឬ Title!", true);
    if(sidInp) sidInp.focus();
    return;
  }
  const typeSel = $("#adminDrRuleType");
  const ruleType = (typeSel && typeSel.value) || 'free_all';
  let freeEps = 10;
  let rule = ruleType;
  if(ruleType === 'custom'){
    rule = 'free_episodes';
    const cInp = $("#adminDrCustomEps");
    freeEps = cInp && cInp.value ? parseInt(cInp.value, 10) : 10;
    if(isNaN(freeEps) || freeEps < 1) freeEps = 10;
  } else if(ruleType === 'free_episodes'){
    freeEps = 10;
  }

  const pin = currentAdminPin || 'syd@168';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/admin/drama_rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin, token: tok, series_id: sid, rule, free_episodes: freeEps, title: sid
      })
    });
    const j = await res.json();
    if(j.ok){
      cachedDramaRules[sid] = j.rule || { rule, free_episodes: freeEps, title: sid };
      if(sidInp) sidInp.value = '';
      toast("✅ បានរក្សាទុកសិទ្ធិរឿងជោគជ័យ!");
      renderAdminDramaRulesList();
    } else {
      toast("❌ " + (j.error || "បរាជ័យក្នុងការកំណត់"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ: " + e, true);
  }
}

async function quickToggleAdminDramaRule(sid, newRule){
  const pin = currentAdminPin || 'syd@168';
  const tok = localStorage.getItem('syd_auth_token') || '';
  const cur = cachedDramaRules[sid] || {};
  try {
    const res = await fetch("/dl/admin/drama_rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin, token: tok, series_id: sid, rule: newRule, free_episodes: 10, title: cur.title || sid
      })
    });
    const j = await res.json();
    if(j.ok){
      cachedDramaRules[sid] = j.rule || { rule: newRule, free_episodes: 10, title: cur.title || sid };
      toast("✅ បានប្តូរសិទ្ធិរឿងជោគជ័យ!");
      renderAdminDramaRulesList();
      if(ddCurrentDrama && String(ddCurrentDrama.id) === sid){
        renderDramaDetailUI(ddCurrentDrama);
        renderDramaDetailEpisodes();
      }
    } else {
      toast("❌ " + (j.error || "បរាជ័យក្នុងការប្តូរ"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ: " + e, true);
  }
}

async function quickDeleteAdminDramaRule(sid){
  if(!confirm(`តើអ្នកពិតជាចង់លុបការកំណត់សិទ្ធិសម្រាប់រឿង ID ${sid} មែនទេ? (នឹងត្រឡប់មក default Free 1-10 ធម្មតាវិញ)`)){
    return;
  }
  const pin = currentAdminPin || 'syd@168';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch(`/dl/admin/drama_rules?series_id=${encodeURIComponent(sid)}&pin=${encodeURIComponent(pin)}&token=${encodeURIComponent(tok)}`, {
      method: "DELETE"
    });
    const j = await res.json();
    if(j.ok){
      delete cachedDramaRules[sid];
      toast("🗑️ បានលុបការកំណត់រួចរាល់!");
      renderAdminDramaRulesList();
      if(ddCurrentDrama && String(ddCurrentDrama.id) === sid){
        renderDramaDetailUI(ddCurrentDrama);
        renderDramaDetailEpisodes();
      }
    } else {
      toast("❌ " + (j.error || "បរាជ័យក្នុងការលុប"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ: " + e, true);
  }
}

/* ---------- Tab Switcher for Admin Dashboard ---------- */
window.switchUcTab = function(tab){
  const bUsers = $("#ucTabBtnUsers"), bRules = $("#ucTabBtnDramaRules"), bSet = $("#ucTabBtnSettings"), bSys = $("#ucTabBtnSys"), bFb = $("#ucTabBtnFirebase");
  const sUsers = $("#ucTabUsersSec"), sRules = $("#ucTabDramaRulesSec"), sSet = $("#ucTabSettingsSec"), sSys = $("#ucTabSysSec"), sFb = $("#ucTabFirebaseSec");
  if(bUsers) bUsers.classList.toggle('on', tab === 'users');
  if(bRules) bRules.classList.toggle('on', tab === 'drama_rules');
  if(bSet) bSet.classList.toggle('on', tab === 'settings');
  if(bSys) bSys.classList.toggle('on', tab === 'system');
  if(bFb) bFb.classList.toggle('on', tab === 'firebase');
  if(sUsers) sUsers.style.display = (tab === 'users') ? 'flex' : 'none';
  if(sRules) sRules.style.display = (tab === 'drama_rules') ? 'flex' : 'none';
  if(sSet) sSet.style.display = (tab === 'settings') ? 'flex' : 'none';
  if(sSys) sSys.style.display = (tab === 'system') ? 'flex' : 'none';
  if(sFb) sFb.style.display = (tab === 'firebase') ? 'flex' : 'none';

  if(tab === 'drama_rules'){
    loadAdminDramaRules();
  }
  if(tab === 'firebase'){
    loadFirebaseConfig();
    refreshFirebaseLicenses();
  }
};'''

assert old_switch_tab in content, "old_switch_tab not found"
content = content.replace(old_switch_tab, new_switch_tab)

# 13. Replace all remaining '8888' with 'syd@168'
# Check where 8888 exists
count_8888 = content.count("'8888'")
print("Found '8888' count:", count_8888)
content = content.replace("'8888'", "'syd@168'")

# Save patched file
with open(target_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully updated downloader.html! New length:", len(content))
