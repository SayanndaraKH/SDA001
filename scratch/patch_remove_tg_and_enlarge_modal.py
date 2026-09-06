import sys

def patch():
    path = 'app/web/downloader.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Enlarge Admin Modal Card Form & update subtitle
    old_modal_card = '<div class="modal-card" style="max-width:760px;width:95vw;padding:22px;background:var(--surface,#18110b);border:1px solid var(--line,#3a2c20);border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,0.85);max-height:90vh;display:flex;flex-direction:column">'
    new_modal_card = '<div class="modal-card" style="max-width:1040px;width:min(1040px,96vw);min-height:680px;height:min(90vh,840px);padding:24px 26px;background:var(--surface,#18110b);border:1.5px solid var(--line,#3a2c20);border-radius:20px;box-shadow:0 28px 70px rgba(0,0,0,0.9);display:flex;flex-direction:column;overflow:hidden">'

    if old_modal_card not in content:
        print("ERROR: old_modal_card not found!")
        return False
    content = content.replace(old_modal_card, new_modal_card, 1)

    old_sub = '<div class="modal-sub" style="color:var(--accent);font-weight:600;margin-top:3px">គ្រប់គ្រងគណនីអ្នកប្រើប្រាស់, សិទ្ធិ VIP &amp; Telegram Settings</div>'
    new_sub = '<div class="modal-sub" style="color:var(--accent);font-weight:600;margin-top:3px">គ្រប់គ្រងគណនីអ្នកប្រើប្រាស់ &amp; កំណត់សិទ្ធិរឿង (Admin Dashboard)</div>'
    if old_sub in content:
        content = content.replace(old_sub, new_sub, 1)

    # 2. Remove Telegram Settings Tab Button from Tab Switcher
    old_tg_btn = """        <button type="button" class="btn sm uc-tab-btn" id="ucTabBtnSettings" onclick="switchUcTab('settings')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px">
          💬 Telegram Settings
        </button>"""
    if old_tg_btn not in content:
        print("ERROR: old_tg_btn not found!")
        return False
    content = content.replace(old_tg_btn + "\n", "", 1)

    # 3. Remove ucTabSettingsSec and move System Access Mode into ucTabDramaRulesSec
    old_tg_sec_and_rules = """      <!-- TAB 2: TELEGRAM SETTINGS -->
      <div id="ucTabSettingsSec" class="modal-scroll" style="display:none;flex-direction:column;gap:14px;padding-right:2px">
        <!-- Card 1: Personal Telegram & Group Telegram Links -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="font:700 13px var(--font-ui);color:var(--accent);display:flex;align-items:center;gap:6px">
            <span>💬</span> <span>Link Telegram ទំនាក់ទំនង &amp; Link Group Telegram</span>
          </div>

          <div>
            <label style="font:600 12px var(--font-ui);color:var(--ink-2);display:block;margin-bottom:4px">1. Link Telegram ផ្ទាល់ខ្លួន Admin (សម្រាប់ User ទំនាក់ទំនង):</label>
            <input type="text" id="adminTgAdminInput" placeholder="ឧ. https://t.me/syd_support ឬ @syd_support" style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 12.5px var(--font-mono)">
            <div style="font-size:11px;color:var(--muted);margin-top:2px">ប៊ូតុង &quot;💬 ទាក់ទង Admin (Telegram)&quot; លើ VIP Portal នឹងបើកទៅកាន់ Link នេះ</div>
          </div>

          <div style="margin-top:4px">
            <label style="font:600 12px var(--font-ui);color:var(--ink-2);display:block;margin-bottom:4px">2. Link Telegram Group (សម្រាប់សមាជិកជជែក &amp; ទទួលដំណឹង):</label>
            <input type="text" id="adminTgGroupInput" placeholder="ឧ. https://t.me/syd_community" style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 12.5px var(--font-mono)">
            <div style="font-size:11px;color:var(--muted);margin-top:2px">ប៊ូតុង &quot;👥 ចូលរួម Group Telegram&quot; លើ VIP Portal នឹងបើកទៅកាន់ Link នេះ</div>
          </div>
        </div>

        <!-- Card 3: System Mode Selection -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:8px">
          <div style="font:700 13px var(--font-ui);color:var(--accent);display:flex;align-items:center;gap:6px">
            <span>🛡️</span> <span>របៀបដំណើរការប្រព័ន្ធ (System Access Mode)</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-top:4px">
            <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-size:12.5px;color:var(--ink);padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line)">
              <input type="radio" name="adminModeRadio" value="vip_required" style="margin-top:2px">
              <div>
                <b style="color:var(--accent)">🔒 VIP Required (គណនីធម្មតាមើលបានភាគ 1-10, VIP មើលបានគ្រប់ភាគ - Recommended)</b>
                <div style="font-size:11.5px;color:var(--muted);margin-top:2px">អ្នកប្រើប្រាស់ធម្មតាអាចមើលនិងទាញយកបានត្រឹមភាគ 1-10។ ចាប់ពីភាគ 11 ឡើងទៅ តម្រូវឱ្យមានកញ្ចប់ VIP។</div>
              </div>
            </label>
            <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-size:12.5px;color:var(--ink);padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line)">
              <input type="radio" name="adminModeRadio" value="free_all" style="margin-top:2px">
              <div>
                <b style="color:var(--good)">🟢 Free 100% (បើកទូលាយសេរីទាំងអស់ គ្មានការ Lock)</b>
                <div style="font-size:11.5px;color:var(--muted);margin-top:2px">អ្នកប្រើប្រាស់ទាំងអស់អាចមើលនិងទាញយកគ្រប់ភាគដោយឥតគិតថ្លៃ។</div>
              </div>
            </label>
          </div>
        </div>

        <!-- Save Settings Button -->
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
          </div>"""

    new_tg_sec_and_rules = """      <!-- TAB: DRAMA FREE RULES MANAGEMENT (ADMIN ONLY) -->
      <div id="ucTabDramaRulesSec" class="modal-scroll" style="display:none;flex-direction:column;gap:12px;padding-right:4px">
        <!-- Global System Access Mode Selection Card -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
            <div style="font:800 13px var(--font-ui);color:var(--accent);display:flex;align-items:center;gap:6px">
              <span>🛡️</span> <span>របៀបដំណើរការប្រព័ន្ធទូទៅ (System Access Mode)៖</span>
            </div>
            <span id="adminModeStatusBadge" style="font-size:11px;font-weight:700;padding:3px 10px;border-radius:12px;background:rgba(255,106,43,0.18);color:var(--accent)">
              🔒 VIP Required Mode
            </span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:8px;margin-top:2px">
            <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-size:12px;color:var(--ink);padding:9px 12px;border-radius:8px;background:var(--surface);border:1px solid var(--line)">
              <input type="radio" name="adminModeRadio" value="vip_required" style="margin-top:2px">
              <div>
                <b style="color:var(--accent)">🔒 VIP Required (លំនាំដើម)</b>
                <div style="font-size:11px;color:var(--muted);margin-top:2px">គណនីធម្មតាមើលបានភាគ 1-10, VIP មើលបានគ្រប់ភាគ។</div>
              </div>
            </label>
            <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-size:12px;color:var(--ink);padding:9px 12px;border-radius:8px;background:var(--surface);border:1px solid var(--line)">
              <input type="radio" name="adminModeRadio" value="free_all" style="margin-top:2px">
              <div>
                <b style="color:var(--good)">🟢 Free 100% (បើកទូលាយទាំងអស់)</b>
                <div style="font-size:11px;color:var(--muted);margin-top:2px">អ្នកប្រើប្រាស់ទាំងអស់អាចមើលនិងទាញយកគ្រប់ភាគដោយឥតគិតថ្លៃ។</div>
              </div>
            </label>
          </div>
        </div>

        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
            <div style="font:800 13px var(--font-ui);color:#22c55e;display:flex;align-items:center;gap:6px">
              <span>🎬</span> <span>កំណត់សិទ្ធិរឿង (Drama Free Rules)</span>
            </div>
            <button type="button" class="btn ghost sm" onclick="loadAdminDramaRules()" style="height:32px;font-weight:700;font-size:11.5px">🔄 ផ្ទុកបញ្ជីឡើងវិញ</button>
          </div>
          <div style="font-size:12px;color:var(--ink-2);line-height:1.5">
            Admin អាចកំណត់រឿងណា <b>Free 100% (គ្រប់ភាគ)</b> ឬ <b>Free 1-10 ភាគ</b> សម្រាប់ User ធម្មតាបានដោយសេរីតាមចិត្តចង់។ (User VIP មើលបានគ្រប់ភាគទាំងអស់ជាស្វ័យប្រវត្តិ)។
          </div>"""

    if old_tg_sec_and_rules not in content:
        print("ERROR: old_tg_sec_and_rules not found!")
        return False
    content = content.replace(old_tg_sec_and_rules, new_tg_sec_and_rules, 1)

    # 4. Update switchUcTab in JavaScript to remove settings references
    old_switch_tab = """window.switchUcTab = function(tab){
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
  if(sFb) sFb.style.display = (tab === 'firebase') ? 'flex' : 'none';"""

    new_switch_tab = """window.switchUcTab = function(tab){
  const bUsers = $("#ucTabBtnUsers"), bRules = $("#ucTabBtnDramaRules"), bSys = $("#ucTabBtnSys"), bFb = $("#ucTabBtnFirebase");
  const sUsers = $("#ucTabUsersSec"), sRules = $("#ucTabDramaRulesSec"), sSys = $("#ucTabSysSec"), sFb = $("#ucTabFirebaseSec");
  if(bUsers) bUsers.classList.toggle('on', tab === 'users');
  if(bRules) bRules.classList.toggle('on', tab === 'drama_rules');
  if(bSys) bSys.classList.toggle('on', tab === 'system');
  if(bFb) bFb.classList.toggle('on', tab === 'firebase');
  if(sUsers) sUsers.style.display = (tab === 'users') ? 'flex' : 'none';
  if(sRules) sRules.style.display = (tab === 'drama_rules') ? 'flex' : 'none';
  if(sSys) sSys.style.display = (tab === 'system') ? 'flex' : 'none';
  if(sFb) sFb.style.display = (tab === 'firebase') ? 'flex' : 'none';"""

    if old_switch_tab not in content:
        print("ERROR: old_switch_tab not found!")
        return False
    content = content.replace(old_switch_tab, new_switch_tab, 1)

    # 5. Wire up radio change on adminModeRadio so mode changes automatically upon selection
    old_render_admin_mode = """function renderAdminMode(mode){
  const radios = document.querySelectorAll('input[name="adminModeRadio"]');
  radios.forEach(r => {
    r.checked = (r.value === mode);
  });
}"""

    new_render_admin_mode = """function renderAdminMode(mode){
  const radios = document.querySelectorAll('input[name="adminModeRadio"]');
  radios.forEach(r => {
    r.checked = (r.value === mode);
  });
  const badge = $("#adminModeStatusBadge");
  if(badge){
    if(mode === 'free_all'){
      badge.textContent = "🟢 Free 100% Mode";
      badge.style.background = "rgba(34,197,94,0.18)";
      badge.style.color = "#22c55e";
    } else {
      badge.textContent = "🔒 VIP Required Mode";
      badge.style.background = "rgba(255,106,43,0.18)";
      badge.style.color = "var(--accent)";
    }
  }
}

// Auto-save when admin toggles mode radio
document.querySelectorAll('input[name="adminModeRadio"]').forEach(radio => {
  radio.addEventListener('change', async (e) => {
    const pin = currentAdminPin || 'syd@168';
    const tok = localStorage.getItem('syd_auth_token') || '';
    const mode = e.target.value;
    try {
      const res = await fetch("/dl/access/admin/mode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, token: tok, mode })
      });
      const j = await res.json();
      if(j && j.ok){
        renderAdminMode(mode);
        toast(mode === 'free_all' ? "🟢 បានប្តូរ System Mode: Free 100% ទាំងអស់!" : "🔒 បានប្តូរ System Mode: VIP Required (ភាគ 1-10 Free)!");
        await fetchAccessStatus();
      }
    } catch(err){
      toast("⚠️ កំហុសបណ្តាញ: " + err, true);
    }
  });
});"""

    if old_render_admin_mode not in content:
        print("ERROR: old_render_admin_mode not found!")
        return False
    content = content.replace(old_render_admin_mode, new_render_admin_mode, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: Telegram Settings removed and Admin Dashboard enlarged cleanly!")
    return True

if __name__ == '__main__':
    patch()
