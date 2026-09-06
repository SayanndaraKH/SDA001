import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def run_patch():
    file_path = os.path.join('app', 'web', 'downloader.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add topbar admin VIP status toggle button right before #topUserCtrlBtn
    target_btn = '<button class="btn ghost sm" id="topBtnSwitchToAdmin"'
    new_top_toggle = '''<button class="btn ghost sm" id="topAdminVipToggleBtn" onclick="adminToggleVipRequestButton()" style="display:none;border-radius:20px;font-weight:800;font-size:11.5px;padding:4px 12px;align-items:center;gap:5px;cursor:pointer" title="គ្រប់គ្រងការបង្ហាញប៊ូតុងស្នើសុំ VIP សម្រាប់ User (Firebase RTDB)">
        <span>👑 VIP Button:</span> <span id="topAdminVipStatusLabel" style="color:#ef4444;font-weight:900">OFF</span>
      </button>
      '''
    if target_btn in html and 'id="topAdminVipToggleBtn"' not in html:
        html = html.replace(target_btn, new_top_toggle + target_btn, 1)
        print('1. Added topbar admin VIP status toggle button')
    else:
        print('1. Topbar toggle already present or target not found')

    # 2. Add VIP Button control card to User Control modal (TAB 2 Settings)
    target_settings_card = '<!-- Card 3: System Mode Selection -->'
    new_vip_card = '''<!-- Card: VIP Request Button Control (Firebase Realtime Database) -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap">
            <div style="font:700 13.5px var(--font-ui);color:#eab308;display:flex;align-items:center;gap:6px">
              <span>👑</span> <span>ប៊ូតុងស្នើសុំ VIP សម្រាប់ User (Firebase Realtime Database)</span>
            </div>
            <span id="adminVipToggleBadge" style="font-size:11px;font-weight:800;padding:3px 10px;border-radius:6px;background:rgba(239,68,68,0.18);color:#ef4444;border:1px solid rgba(239,68,68,0.4)">
              🔴 កំពុងបិទ (OFF)
            </span>
          </div>
          <div style="font-size:12px;color:var(--muted);line-height:1.5">
            លក្ខខណ្ឌ៖ <b>លុះត្រាតែ ADMIN បើក ទើប USER អាចឃើញប៊ូតុង "ស្នើសុំ VIP" បាន</b>។ ប្រសិនបើបិទ (OFF) ប៊ូតុង "ស្នើសុំ VIP" នឹងត្រូវលាក់ពីផ្ទាំងរបស់ User ទាំងអស់ក្នុង Realtime ដោយស្វ័យប្រវត្តិតាមរយៈ Firebase Realtime Database។
          </div>
          <div style="display:flex;align-items:center;gap:12px;margin-top:4px">
            <button type="button" class="btn primary sm" id="adminVipToggleBtn" onclick="adminToggleVipRequestButton()" style="font-weight:800;font-size:12px;padding:6px 18px;border-radius:20px;cursor:pointer;background:linear-gradient(135deg,#22c55e,#16a34a)">
              ⚡ ចុចដើម្បី បើក (Enable)
            </button>
            <span id="adminVipToggleStatusText" style="font-size:12px;font-weight:700;color:var(--ink-2)">
              ស្ថានភាពបច្ចុប្បន្ន៖ បិទ (User មិនឃើញប៊ូតុងស្នើសុំ VIP)
            </span>
          </div>
        </div>

        '''
    if target_settings_card in html and 'id="adminVipToggleBadge"' not in html:
        html = html.replace(target_settings_card, new_vip_card + target_settings_card, 1)
        print('2. Added VIP Request Button control card to User Control modal')
    else:
        print('2. VIP control card already present or target not found')

    # 3. Update updateAccessUI logic to enforce VIP button visibility based on Firebase RTDB setting
    old_vip_btn_logic = '''  // Top bar "👑 ស្នើសុំ VIP" button: Visible to anyone who is not already Admin or approved VIP!
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
  }'''

    new_vip_btn_logic = '''  // VIP Request feature toggle from Firebase Realtime Database
  const vipReqEnabled = !!(data && data.settings && (data.settings.vip_request_enabled === true || data.settings.vip_request_enabled === 'true' || data.settings.vip_request_enabled === 1));

  // Topbar Admin VIP Quick Status & Toggle
  const topVipToggle = $("#topAdminVipToggleBtn");
  const topVipStatus = $("#topAdminVipStatusLabel");
  if(topVipToggle){
    topVipToggle.style.display = isAdmin ? "inline-flex" : "none";
    if(topVipStatus){
      topVipStatus.textContent = vipReqEnabled ? "ON" : "OFF";
      topVipStatus.style.color = vipReqEnabled ? "var(--good)" : "var(--bad)";
    }
  }

  // Admin Modal Status & Controls
  const adminVipBadge = $("#adminVipToggleBadge");
  const adminVipBtn = $("#adminVipToggleBtn");
  const adminVipTxt = $("#adminVipToggleStatusText");
  if(adminVipBadge){
    if(vipReqEnabled){
      adminVipBadge.textContent = "🟢 កំពុងបើក (ON)";
      adminVipBadge.style.color = "#22c55e";
      adminVipBadge.style.background = "rgba(34,197,94,0.18)";
      adminVipBadge.style.borderColor = "rgba(34,197,94,0.4)";
    } else {
      adminVipBadge.textContent = "🔴 កំពុងបិទ (OFF)";
      adminVipBadge.style.color = "#ef4444";
      adminVipBadge.style.background = "rgba(239,68,68,0.18)";
      adminVipBadge.style.borderColor = "rgba(239,68,68,0.4)";
    }
  }
  if(adminVipBtn){
    adminVipBtn.textContent = vipReqEnabled ? "🛑 ចុចដើម្បី បិទ (Disable)" : "⚡ ចុចដើម្បី បើក (Enable)";
    adminVipBtn.style.background = vipReqEnabled ? "linear-gradient(135deg,#ef4444,#dc2626)" : "linear-gradient(135deg,#22c55e,#16a34a)";
  }
  if(adminVipTxt){
    adminVipTxt.textContent = vipReqEnabled 
      ? "ស្ថានភាពបច្ចុប្បន្ន៖ បើក (User អាចឃើញប៊ូតុងស្នើសុំ VIP បាន)"
      : "ស្ថានភាពបច្ចុប្បន្ន៖ បិទ (User មិនឃើញប៊ូតុងស្នើសុំ VIP)";
  }

  // STRICT RULE: "ប៊ូតុង ស្នើសុំVIP លុះត្រាតែ ADMIN បើក បាន USER ឃើញ" (Firebase Realtime Database)
  if(reqVipBtn){
    if(isAdmin || isVip || isBanned){
      reqVipBtn.style.display = "none";
    } else if(!vipReqEnabled){
      // Admin has turned OFF VIP Request button in Firebase RTDB: Hide from user!
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
    if(isAdmin || isVip || isBanned || !vipReqEnabled){
      tabVipBtn.style.display = "none";
    } else {
      tabVipBtn.style.display = "block";
    }
  }

  // Drama Detail VIP Buttons: Strictly hidden if Admin turned OFF VIP button
  const ddVipBtn = $("#ddVipUnlockBtn");
  const ddVipBanner = $("#ddVipEpisodeBanner");
  if(ddVipBtn){
    ddVipBtn.style.display = (isAdmin || isVip || !vipReqEnabled) ? "none" : "inline-flex";
  }
  if(ddVipBanner){
    ddVipBanner.style.display = (isAdmin || isVip || !vipReqEnabled) ? "none" : "flex";
  }'''

    if old_vip_btn_logic in html:
        html = html.replace(old_vip_btn_logic, new_vip_btn_logic, 1)
        print('3. Updated VIP button visibility logic in updateAccessUI')
    else:
        print('3. Could not find old_vip_btn_logic to replace')

    # 4. Add adminToggleVipRequestButton function
    toggle_func = '''
window.adminToggleVipRequestButton = async function(explicitState){
  try {
    const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || localStorage.getItem('syd_auth_token') || 'syd@168';
    const bodyObj = { pin: pin };
    if(explicitState !== undefined && explicitState !== null){
      bodyObj.enabled = explicitState;
    }
    const res = await (await fetch('/dl/access/admin/vip-button-toggle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bodyObj)
    })).json();

    if(res.ok){
      const isNowOn = !!res.vip_request_enabled;
      if(isNowOn){
        toast("🟢 បានបើកប៊ូតុង 'ស្នើសុំ VIP' ជូន User (បានរក្សាទុកក្នុង Firebase RTDB)", false);
      } else {
        toast("🔴 បានបិទប៊ូតុង 'ស្នើសុំ VIP' មិនឱ្យ User ឃើញទេ (បានរក្សាទុកក្នុង Firebase RTDB)", false);
      }
      await fetchAccessStatus();
    } else {
      toast("❌ " + (res.error || "មិនអាចកែប្រែបានទេ"), true);
    }
  } catch(e){
    toast("⚠️ កំហុស: " + e, true);
  }
};
'''
    if 'window.adminToggleVipRequestButton =' not in html:
        p_script = html.rfind('</script>')
        if p_script != -1:
            html = html[:p_script] + toggle_func + html[p_script:]
            print('4. Added adminToggleVipRequestButton function')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print('ALL VIP TOGGLE PATCHES APPLIED!')

if __name__ == '__main__':
    run_patch()
