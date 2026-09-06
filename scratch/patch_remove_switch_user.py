import re

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove topBtnSwitchToUser and topBtnSwitchToAdmin from HTML
top_buttons_pattern = r'<!-- Direct Switch between Real User & Admin Mode -->\s*<button[^>]*id="topBtnSwitchToUser"[^>]*>.*?</button>\s*(?:<button[^>]*id="topBtnSwitchToAdmin"[^>]*>.*?</button>\s*)?'
content = re.sub(top_buttons_pattern, '', content, flags=re.DOTALL)

# In case topBtnSwitchToAdmin is separated after topAdminVipToggleBtn
admin_btn_pattern = r'<button[^>]*id="topBtnSwitchToAdmin"[^>]*>.*?</button>\s*'
content = re.sub(admin_btn_pattern, '', content, flags=re.DOTALL)

# 2. Remove loginCurrentActiveCard from HTML
active_card_pattern = r'<!-- Active logged-in user summary card \(shown if user already logged in\) -->\s*<div id="loginCurrentActiveCard".*?</div>\s*</div>'
content = re.sub(active_card_pattern, '', content, flags=re.DOTALL)

# 3. Remove btnSwitchToUser & btnSwitchToAdmin in updateAccessUI
js_switch_btns = '''  const btnSwitchToUser = $("#topBtnSwitchToUser");
  const btnSwitchToAdmin = $("#topBtnSwitchToAdmin");
  if(btnSwitchToUser) btnSwitchToUser.style.display = isAdmin ? "inline-flex" : "none";
  if(btnSwitchToAdmin) btnSwitchToAdmin.style.display = (!isAdmin) ? "inline-flex" : "none";'''
if js_switch_btns in content:
    content = content.replace(js_switch_btns, '')

# 4. Clean up switchAuthTab for 'login'
old_tab_login = '''  if(tab === 'login'){
    const card = $("#loginCurrentActiveCard");
    const nameEl = $("#loginCurrentUsername");
    const detailEl = $("#loginCurrentDetail");
    const heading = $("#authLoginFormHeading");
    if(card && nameEl && detailEl){
      if(isAuth && window.userAccess && window.userAccess.username){
        card.style.display = 'flex';
        nameEl.textContent = window.userAccess.username || 'USER';
        detailEl.textContent = `${window.userAccess.name || 'អ្នកប្រើប្រាស់'} · សមតុល្យ ${window.userAccess.coins || 0} Coins (${(window.userAccess.coins || 0) * 500}៛)`;
        if(heading) heading.textContent = "ប្តូរគណនី / ចូលគណនីផ្សេង (Switch Account / Login)";
      } else {
        card.style.display = 'none';
        if(heading) heading.textContent = "ចូលប្រើប្រាស់គណនី (Login)";
      }
    }
    setTimeout(() => {
      const inp = $("#authLoginUser");
      if(inp) inp.focus();
    }, 150);
  }'''

new_tab_login = '''  if(tab === 'login'){
    const heading = $("#authLoginFormHeading");
    if(heading) heading.textContent = "ចូលប្រើប្រាស់គណនី (Login)";
    setTimeout(() => {
      const inp = $("#authLoginUser");
      if(inp) inp.focus();
    }, 150);
  }'''

if old_tab_login in content:
    content = content.replace(old_tab_login, new_tab_login)
else:
    print("WARNING: old_tab_login exact match not found")

# 5. Clean up executeLogin with timeout and closeUserRegisterModal(true)
old_execute_login = '''// Login Submit Handler
async function executeLogin(user, pass){
  const ident = user.trim();
  const pw = pass.trim();
  if(!ident){
    toast("⚠️ សូមបញ្ចូល Username ឬ Phone!", true);
    if($("#authLoginUser")) $("#authLoginUser").focus();
    return;
  }
  if(!pw){
    toast("⚠️ សូមបញ្ចូលពាក្យសម្ងាត់ (Password)!", true);
    if($("#authLoginPass")) $("#authLoginPass").focus();
    return;
  }
  const btn = $("#authLoginSubmitBtn");
  if(btn){ btn.disabled = true; btn.innerHTML = "<span>កំពុងពិនិត្យ...</span>"; }
  try {
    const res = await fetch("/dl/access/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identity: ident,
        password: pw,
        device_id: (window.userAccess && window.userAccess.device_id) || ''
      })
    });
    const j = await res.json();
    if(j.ok){
      localStorage.setItem('syd_auth_token', j.token || '');
      localStorage.setItem('syd_auth_user', JSON.stringify(j.user || {}));
      if(j.user && (j.user.is_admin || j.user.role === 'admin')){
        sessionStorage.setItem('hg_admin_pin', '8888');
        currentAdminPin = (j.token || '8888');
        toast("🛡️ ស្វាគមន៍ការចូលប្រើប្រាស់ ADMIN (Full Control គ្មានការ Lock)!", false);
        closeUserRegisterModal();
        await fetchAccessStatus();
      } else if(j.user && j.user.is_vip){
        toast(`👑 ស្វាគមន៍ VIP! ${j.user.name || j.user.username} (ដោះសោរគ្រប់ភាគ)`);
        closeUserRegisterModal();
        await fetchAccessStatus();
      } else {
        // REGULAR USER (Free Tier 1-10)
        // USER REQUIREMENT:
        // user ធម្មតា Login ចូលទៅ ប្រព័ន្ធនឹងបង្ហាញ ការស្នើសុំ កញ្ចប់ VIP
        toast(`✅ ចូលប្រើប្រាស់ជោគជ័យ! សូមស្វាគមន៍ ${j.user.name || j.user.username}`);
        await fetchAccessStatus();
        openUserRegisterModal('vip', false);
      }
    } else {
      toast("⚠️ " + (j.error || "ឈ្មោះគណនី ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ៖ " + e, true);
  } finally {
    if(btn){ btn.disabled = false; btn.innerHTML = "<span>🚀 ចូលគណនី (Login)</span>"; }
  }
}'''

new_execute_login = '''// Login Submit Handler
async function executeLogin(user, pass){
  const ident = user.trim();
  const pw = pass.trim();
  if(!ident){
    toast("⚠️ សូមបញ្ចូល Username ឬ Phone!", true);
    if($("#authLoginUser")) $("#authLoginUser").focus();
    return;
  }
  if(!pw){
    toast("⚠️ សូមបញ្ចូលពាក្យសម្ងាត់ (Password)!", true);
    if($("#authLoginPass")) $("#authLoginPass").focus();
    return;
  }
  const btn = $("#authLoginSubmitBtn");
  if(btn){ btn.disabled = true; btn.innerHTML = "<span>កំពុងពិនិត្យ...</span>"; }
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    const res = await fetch("/dl/access/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        identity: ident,
        password: pw,
        device_id: (window.userAccess && window.userAccess.device_id) || ''
      })
    });
    clearTimeout(timeoutId);
    const j = await res.json();
    if(j.ok){
      localStorage.setItem('syd_auth_token', j.token || '');
      localStorage.setItem('syd_auth_user', JSON.stringify(j.user || {}));
      if(j.user && (j.user.is_admin || j.user.role === 'admin')){
        sessionStorage.setItem('hg_admin_pin', '8888');
        currentAdminPin = (j.token || '8888');
        toast("🛡️ ស្វាគមន៍ការចូលប្រើប្រាស់ ADMIN (Full Control គ្មានការ Lock)!", false);
        closeUserRegisterModal(true);
        await fetchAccessStatus();
      } else if(j.user && j.user.is_vip){
        toast(`👑 ស្វាគមន៍ VIP! ${j.user.name || j.user.username} (ដោះសោរគ្រប់ភាគ)`);
        closeUserRegisterModal(true);
        await fetchAccessStatus();
      } else {
        // REGULAR USER (Free Tier 1-5)
        toast(`✅ ចូលប្រើប្រាស់ជោគជ័យ! សូមស្វាគមន៍ ${j.user.name || j.user.username}`);
        closeUserRegisterModal(true);
        await fetchAccessStatus();
      }
    } else {
      toast("⚠️ " + (j.error || "ឈ្មោះគណនី ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវ"), true);
    }
  } catch(e){
    if(e.name === 'AbortError'){
      toast("⚠️ ការតភ្ជាប់យឺតពេក (Network Timeout) សូមព្យាយាមម្តងទៀត!", true);
    } else {
      toast("⚠️ កំហុសបណ្តាញ៖ " + e, true);
    }
  } finally {
    if(btn){ btn.disabled = false; btn.innerHTML = "<span>🚀 ចូលគណនី (Login)</span>"; }
  }
}'''

if old_execute_login in content:
    content = content.replace(old_execute_login, new_execute_login)
else:
    print("WARNING: old_execute_login exact match not found")

# 6. Remove window.switchActiveMode
switch_mode_pattern = r'window\.switchActiveMode\s*=\s*async\s*function\(mode\)\{.*?\};\s*'
content = re.sub(switch_mode_pattern, '', content, flags=re.DOTALL)

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("downloader.html updated successfully!")
