import re

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. In fetchAccessStatus: change preferTab to 'login' when unauthenticated
old_fetch_auth = '''      } else if(!data.authenticated || data.must_register || !data.has_firebase_account){
        openUserRegisterModal('register', true);
      } else {'''

new_fetch_auth = '''      } else if(!data.authenticated || data.must_register || !data.has_firebase_account){
        openUserRegisterModal('login', true);
      } else {'''

if old_fetch_auth in content:
    content = content.replace(old_fetch_auth, new_fetch_auth)
    print("1. Updated fetchAccessStatus unauthenticated modal call")
else:
    print("WARNING 1: old_fetch_auth not found")

# 2. In openUserRegisterModal: ensure isMandatoryAuth is strictly enforced
old_open_modal = '''function openUserRegisterModal(preferTab = 'login', isMandatory = false){
  const m = $("#userRegisterModal");
  if(!m) return;
  const isAuth = !!(window.userAccess && window.userAccess.authenticated);
  const isBanned = !!(window.userAccess && (window.userAccess.status === 'banned' || window.userAccess.is_banned));
  isMandatoryAuth = (!isAuth || isBanned) && !!isMandatory;
  const closeBtn1 = $("#regCloseBtn");
  const closeBtn2 = $("#regCloseBtn2");
  if(closeBtn1) closeBtn1.style.display = isMandatoryAuth ? 'none' : 'block';
  if(closeBtn2) closeBtn2.style.display = isMandatoryAuth ? 'none' : 'block';'''

new_open_modal = '''function openUserRegisterModal(preferTab = 'login', isMandatory = false){
  const m = $("#userRegisterModal");
  if(!m) return;
  const isAuth = !!(window.userAccess && window.userAccess.authenticated);
  const isBanned = !!(window.userAccess && (window.userAccess.status === 'banned' || window.userAccess.is_banned));
  // Mandatory Login/Register: Every time app is opened, user must login or register!
  isMandatoryAuth = (!isAuth || isBanned || !!isMandatory);
  const closeBtn1 = $("#regCloseBtn");
  const closeBtn2 = $("#regCloseBtn2");
  if(closeBtn1) closeBtn1.style.display = isMandatoryAuth ? 'none' : 'block';
  if(closeBtn2) closeBtn2.style.display = isMandatoryAuth ? 'none' : 'block';'''

if old_open_modal in content:
    content = content.replace(old_open_modal, new_open_modal)
    print("2. Updated openUserRegisterModal isMandatoryAuth logic")
else:
    print("WARNING 2: old_open_modal not found")

# 3. In closeUserRegisterModal: prevent closing if unauthenticated or isMandatoryAuth
old_close_modal = '''function closeUserRegisterModal(force = false){
  const isBanned = !!(window.userAccess && (window.userAccess.status === 'banned' || window.userAccess.is_banned));
  if(!force && isBanned){
    toast("🚫 គណនីត្រូវបាន Banned មិនអាចបិទផ្ទាំងនេះបានទេ។", true);
    return;
  }
  isMandatoryAuth = false;
  const m = $("#userRegisterModal");
  if(m) m.hidden = true;
  const banner = $("#authAlertBanner");
  if(banner) banner.style.display = 'none';
}'''

new_close_modal = '''function closeUserRegisterModal(force = false){
  const isAuth = !!(window.userAccess && window.userAccess.authenticated);
  const isBanned = !!(window.userAccess && (window.userAccess.status === 'banned' || window.userAccess.is_banned));
  if(!force){
    if(isBanned){
      toast("🚫 គណនីត្រូវបាន Banned មិនអាចបិទផ្ទាំងនេះបានទេ។", true);
      return;
    }
    if(!isAuth || isMandatoryAuth){
      toast("⚠️ គ្រប់ពេលបើកកម្មវិធីត្រូវតែ Login ជាដាច់ខាត ឬចុះឈ្មោះជាចាំបាច់ដើម្បីប្រើប្រាស់!", true);
      return;
    }
  }
  isMandatoryAuth = false;
  const m = $("#userRegisterModal");
  if(m) m.hidden = true;
  const banner = $("#authAlertBanner");
  if(banner) banner.style.display = 'none';
}'''

if old_close_modal in content:
    content = content.replace(old_close_modal, new_close_modal)
    print("3. Updated closeUserRegisterModal logic")
else:
    print("WARNING 3: old_close_modal not found")

# 4. In Backdrop click and Escape key listeners
old_backdrop_esc = '''const regCl = $("#regCloseBtn"); if(regCl) regCl.onclick = () => closeUserRegisterModal(true);
const regCl2 = $("#regCloseBtn2"); if(regCl2) regCl2.onclick = () => closeUserRegisterModal(true);
const regModal = $("#userRegisterModal");
if(regModal){
  regModal.addEventListener('click', e => {
    if(e.target === regModal) closeUserRegisterModal(true);
  });
}
document.addEventListener('keydown', e => {
  if(e.key === 'Escape'){
    const m = $("#userRegisterModal");
    if(m && !m.hidden) closeUserRegisterModal(true);
  }
});'''

new_backdrop_esc = '''const regCl = $("#regCloseBtn"); if(regCl) regCl.onclick = () => closeUserRegisterModal(false);
const regCl2 = $("#regCloseBtn2"); if(regCl2) regCl2.onclick = () => closeUserRegisterModal(false);
const regModal = $("#userRegisterModal");
if(regModal){
  regModal.addEventListener('click', e => {
    if(e.target === regModal){
      if(isMandatoryAuth || (!window.userAccess || !window.userAccess.authenticated)){
        toast("⚠️ គ្រប់ពេលបើកកម្មវិធីត្រូវតែ Login ជាដាច់ខាត ឬចុះឈ្មោះជាចាំបាច់ដើម្បីប្រើប្រាស់!", true);
        return;
      }
      closeUserRegisterModal(true);
    }
  });
}
document.addEventListener('keydown', e => {
  if(e.key === 'Escape'){
    const m = $("#userRegisterModal");
    if(m && !m.hidden){
      if(isMandatoryAuth || (!window.userAccess || !window.userAccess.authenticated)){
        toast("⚠️ គ្រប់ពេលបើកកម្មវិធីត្រូវតែ Login ជាដាច់ខាត ឬចុះឈ្មោះជាចាំបាច់ដើម្បីប្រើប្រាស់!", true);
        return;
      }
      closeUserRegisterModal(true);
    }
  }
});'''

if old_backdrop_esc in content:
    content = content.replace(old_backdrop_esc, new_backdrop_esc)
    print("4. Updated backdrop and escape listeners")
else:
    print("WARNING 4: old_backdrop_esc not found")

# 5. In authRegSubmitBtn: close modal cleanly upon successful registration
old_reg_success = '''        toast("🎉 ចុះឈ្មោះជោគជ័យ! អ្នកជា User ធម្មតា (ភាគ 1-10 ឥតគិតថ្លៃ)។ សូមស្នើសុំ VIP ដើម្បីដោះសោរគ្រប់ភាគ!", false);
        openUserRegisterModal('vip', false);'''

new_reg_success = '''        toast(`🎉 ចុះឈ្មោះជោគជ័យ! សូមស្វាគមន៍ ${j.user.name || username} (ទស្សនាភាគ 1 ដល់ 5 ឥតគិតថ្លៃ)`, false);
        closeUserRegisterModal(true);
        await fetchAccessStatus();'''

if old_reg_success in content:
    content = content.replace(old_reg_success, new_reg_success)
    print("5. Updated authRegSubmitBtn registration success handler")
else:
    print("WARNING 5: old_reg_success not found")

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("All mandatory auth patches written!")
