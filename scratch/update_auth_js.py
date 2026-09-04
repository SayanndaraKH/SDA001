# -*- coding: utf-8 -*-
import sys

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update openUserRegisterModal & updateAccessUI up to topLogoutBtn
start_marker_1 = 'function openUserRegisterModal('
end_marker_1 = 'const topLogoutBtn = $("#topLogoutBtn");'

if start_marker_1 not in content or end_marker_1 not in content:
    print("ERROR: marker 1 not found")
    sys.exit(1)

part1 = content[:content.index(start_marker_1)]
rest_after_1 = content[content.index(end_marker_1):]

new_js_1 = '''function openUserRegisterModal(preferTab = 'login', isMandatory = false){
  const m = $("#userRegisterModal");
  if(!m) return;
  isMandatoryAuth = !!isMandatory;
  const closeBtn1 = $("#regCloseBtn");
  const closeBtn2 = $("#regCloseBtn2");
  if(closeBtn1) closeBtn1.style.display = isMandatory ? 'none' : 'block';
  if(closeBtn2) closeBtn2.style.display = isMandatory ? 'none' : 'block';

  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  const isVip = !!(window.userAccess && window.userAccess.is_vip);
  const isPendingVip = !!(window.userAccess && window.userAccess.status === 'pending_vip');

  // USER REQUIREMENT:
  // "ការស្នើសុំ VIP មើលឃើញតែ User ធម្មតា ដែលពុំទាន់ស្នើសុំVIP ប៉ុណ្ណោះ"
  // (VIP request tab MUST ONLY be visible to regular users who have NOT yet requested VIP)
  const tabVipBtn = $("#tabBtnVip");
  if(tabVipBtn){
    if(isMandatory || isAdmin || isVip || isPendingVip){
      tabVipBtn.style.display = 'none';
    } else {
      tabVipBtn.style.display = 'block';
    }
  }

  const sub = $("#regModalSub");
  if(sub){
    if(isMandatory){
      sub.textContent = "សូមធ្វើការ Login ចូលគណនី ឬចុះឈ្មោះប្រើប្រាស់ជាមុនសិន ដើម្បីចាប់ផ្តើមប្រើប្រាស់កម្មវិធី";
      sub.style.color = "var(--accent)";
    } else {
      sub.textContent = "ចូលគណនី, ចុះឈ្មោះ ឬស្នើសុំកញ្ចប់ VIP ពី Admin";
      sub.style.color = "var(--accent)";
    }
  }

  m.hidden = false;
  
  let targetTab = preferTab;
  if(isMandatory || isAdmin || isVip){
    if(targetTab === 'vip') targetTab = 'login';
  }
  switchAuthTab(targetTab);
}

function closeUserRegisterModal(){
  if(isMandatoryAuth && (!window.userAccess || !window.userAccess.authenticated)){
    toast("⚠️ សូមធ្វើការ Login ឬចុះឈ្មោះប្រើប្រាស់ជាមុនសិន!", true);
    return;
  }
  const m = $("#userRegisterModal");
  if(m) m.hidden = true;
  const banner = $("#authAlertBanner");
  if(banner) banner.style.display = 'none';
}

function updateVipPortalSettings(settings, userAccess){
  if(!settings) return;
  const khqrCard = $("#vipKhqrCard");
  const khqrImg = $("#vipKhqrImg");
  if(settings.khqr_image){
    if(khqrImg) khqrImg.src = settings.khqr_image;
    if(khqrCard) khqrCard.style.display = "flex";
  } else {
    if(khqrCard) khqrCard.style.display = "none";
  }

  const tgAdminLink = $("#vipTgAdminLink");
  if(settings.telegram_admin && settings.telegram_admin.trim()){
    let url = settings.telegram_admin.trim();
    if(url.startsWith('@')) url = 'https://t.me/' + url.substring(1);
    else if(!url.startsWith('http://') && !url.startsWith('https://')) url = 'https://t.me/' + url;
    if(tgAdminLink){
      tgAdminLink.href = url;
      tgAdminLink.style.display = "inline-flex";
    }
  } else {
    if(tgAdminLink) tgAdminLink.style.display = "none";
  }

  const tgGroupLink = $("#vipTgGroupLink");
  if(settings.telegram_group && settings.telegram_group.trim()){
    let url = settings.telegram_group.trim();
    if(url.startsWith('@')) url = 'https://t.me/' + url.substring(1);
    else if(!url.startsWith('http://') && !url.startsWith('https://')) url = 'https://t.me/' + url;
    if(tgGroupLink){
      tgGroupLink.href = url;
      tgGroupLink.style.display = "inline-flex";
    }
  } else {
    if(tgGroupLink) tgGroupLink.style.display = "none";
  }

  // Update pending banner & package form visibility
  const isPendingVip = !!(userAccess && userAccess.status === 'pending_vip');
  const pendBanner = $("#vipPendingBanner");
  const pkgForm = $("#tabPanelVip");
  if(isPendingVip){
    if(pendBanner) pendBanner.style.display = "block";
    if(pkgForm) pkgForm.style.display = "none";
  } else {
    if(pendBanner) pendBanner.style.display = "none";
    if(pkgForm) pkgForm.style.display = "flex";
  }
}

async function fetchAccessStatus(){
  try {
    const tok = localStorage.getItem('syd_auth_token') || '';
    const res = await fetch(`/dl/access/status?token=${encodeURIComponent(tok)}`);
    if(res.ok){
      const data = await res.json();
      window.userAccess = data;
      updateAccessUI(data);

      // Enforce mandatory Login or Register on startup
      if(!data.authenticated){
        openUserRegisterModal('login', true);
      } else {
        isMandatoryAuth = false;
        closeUserRegisterModal();
      }

      if(typeof renderDramaDetailEpisodes === 'function' && ddCurrentDrama){
        renderDramaDetailEpisodes();
      }
    }
  } catch(e){
    console.error("fetchAccessStatus error", e);
  }
}

function updateAccessUI(data){
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
  const isBanned = (data.status === 'banned' || data.is_banned);
  const isUser = !!(data.username && !isAdmin);

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

  // USER REQUIREMENT:
  // "ការស្នើសុំ VIP មើលឃើញតែ User ធម្មតា ដែលពុំទាន់ស្នើសុំVIP ប៉ុណ្ណោះ"
  // Top bar "👑 ស្នើសុំ VIP" button: ONLY visible to regular users who have NOT yet requested VIP
  if(reqVipBtn){
    if(isAdmin || isVip || isPendingVip || isBanned){
      reqVipBtn.style.display = "none";
    } else {
      reqVipBtn.style.display = "inline-flex";
    }
  }

  const tabVipBtn = $("#tabBtnVip");
  if(tabVipBtn){
    if(isAdmin || isVip || isPendingVip || isBanned){
      tabVipBtn.style.display = "none";
    } else {
      tabVipBtn.style.display = "block";
    }
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
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:#c084fc;font-weight:700">🛡️ ចូលជា: ADMIN (Full Control)</span>`;
    currentAdminPin = localStorage.getItem('syd_auth_token') || '8888';
    sessionStorage.setItem('hg_admin_pin', '8888');
    const pinBox = $("#adminPinBox"); if(pinBox) pinBox.hidden = true;
    const unPanel = $("#adminUnlockedPanel"); if(unPanel) unPanel.hidden = false;
    const lockBadge = $("#adminLockBadge");
    if(lockBadge){
      lockBadge.textContent = "🔓 UNLOCKED (ADMIN)";
      lockBadge.style.color = "var(--good)";
      lockBadge.style.background = "rgba(46,204,113,0.15)";
    }
    refreshAdminUsersList();

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
  } else {
    openUserRegisterModal('login');
  }
};

const topVipBtn = $("#topReqVipBtn");
if(topVipBtn) topVipBtn.onclick = () => {
  openUserRegisterModal('vip');
};

'''

intermediate_content = part1 + new_js_1 + rest_after_1

# 2. Update Admin Panel logic starting at 'function renderAdminMode(' up to 'function openUserControl()'
start_marker_2 = 'function renderAdminMode('
end_marker_2 = 'function openUserControl()'

if start_marker_2 not in intermediate_content or end_marker_2 not in intermediate_content:
    print("ERROR: marker 2 not found")
    sys.exit(1)

part2_1 = intermediate_content[:intermediate_content.index(start_marker_2)]
part2_2 = intermediate_content[intermediate_content.index(end_marker_2):]

new_js_2 = '''/* ---------- Tab Switcher for Admin Dashboard ---------- */
window.switchUcTab = function(tab){
  const bUsers = $("#ucTabBtnUsers"), bSet = $("#ucTabBtnSettings"), bSys = $("#ucTabBtnSys");
  const sUsers = $("#ucTabUsersSec"), sSet = $("#ucTabSettingsSec"), sSys = $("#ucTabSysSec");
  if(bUsers) bUsers.classList.toggle('on', tab === 'users');
  if(bSet) bSet.classList.toggle('on', tab === 'settings');
  if(bSys) bSys.classList.toggle('on', tab === 'system');
  if(sUsers) sUsers.style.display = (tab === 'users') ? 'flex' : 'none';
  if(sSet) sSet.style.display = (tab === 'settings') ? 'flex' : 'none';
  if(sSys) sSys.style.display = (tab === 'system') ? 'flex' : 'none';
};

let cachedAdminUsers = [];
let currentAdminFilter = 'all';
let currentAdminSearch = '';
let currentKhqrBase64 = '';

function renderAdminMode(mode){
  const radios = document.querySelectorAll('input[name="adminModeRadio"]');
  radios.forEach(r => {
    r.checked = (r.value === mode);
  });
}

function renderAdminSettings(settings){
  if(!settings) return;
  currentKhqrBase64 = settings.khqr_image || '';
  const preview = $("#adminKhqrPreview");
  const placeholder = $("#adminKhqrPlaceholder");
  if(currentKhqrBase64){
    if(preview){ preview.src = currentKhqrBase64; preview.style.display = "block"; }
    if(placeholder) placeholder.style.display = "none";
  } else {
    if(preview){ preview.src = ""; preview.style.display = "none"; }
    if(placeholder) placeholder.style.display = "block";
  }

  if($("#adminTgAdminInput")) $("#adminTgAdminInput").value = settings.telegram_admin || '';
  if($("#adminTgGroupInput")) $("#adminTgGroupInput").value = settings.telegram_group || '';
  
  if(window.userAccess){
    updateVipPortalSettings(settings, window.userAccess);
  }
}

function applyAdminUserFilterAndRender(){
  const query = (currentAdminSearch || '').trim().toLowerCase();
  
  let totalAll = cachedAdminUsers.length;
  let totalVip = 0, totalPend = 0, totalReg = 0, totalBan = 0;

  cachedAdminUsers.forEach(u => {
    const isBan = (u.status === 'banned');
    const isVip = !isBan && (u.is_vip || u.role === 'admin' || u.status === 'approved');
    const isPend = !isBan && !isVip && (u.status === 'pending' || u.status === 'pending_vip');
    const isReg = !isBan && !isVip && !isPend;
    if(isBan) totalBan++;
    else if(isVip) totalVip++;
    else if(isPend) totalPend++;
    else if(isReg) totalReg++;
  });

  if($("#cntAll")) $("#cntAll").textContent = totalAll;
  if($("#cntVip")) $("#cntVip").textContent = totalVip;
  if($("#cntPend")) $("#cntPend").textContent = totalPend;
  if($("#cntReg")) $("#cntReg").textContent = totalReg;
  if($("#cntBan")) $("#cntBan").textContent = totalBan;

  const filtered = cachedAdminUsers.filter(u => {
    const isBan = (u.status === 'banned');
    const isVip = !isBan && (u.is_vip || u.role === 'admin' || u.status === 'approved');
    const isPend = !isBan && !isVip && (u.status === 'pending' || u.status === 'pending_vip');
    const isReg = !isBan && !isVip && !isPend;

    if(currentAdminFilter === 'vip' && !isVip) return false;
    if(currentAdminFilter === 'pending' && !isPend) return false;
    if(currentAdminFilter === 'regular' && !isReg) return false;
    if(currentAdminFilter === 'banned' && !isBan) return false;

    if(query){
      const matchName = String(u.name || '').toLowerCase().includes(query);
      const matchUser = String(u.username || '').toLowerCase().includes(query);
      const matchCnt = String(u.contact || '').toLowerCase().includes(query);
      const matchDev = String(u.device_id || '').toLowerCase().includes(query);
      if(!matchName && !matchUser && !matchCnt && !matchDev) return false;
    }
    return true;
  });

  renderAdminUserList(filtered);
}

function renderAdminUserList(users){
  const container = $("#adminUserListContainer");
  if(!container) return;
  if(!users || !users.length){
    container.innerHTML = '<div style="text-align:center;padding:24px;color:var(--muted);font-size:12.5px">មិនមានទិន្នន័យគណនីក្នុងលក្ខខណ្ឌនេះទេ</div>';
    return;
  }
  container.innerHTML = users.map(u => {
    const isBan = (u.status === 'banned');
    const isDev = (u.role === 'dev' || u.role === 'admin');
    const isApp = !isBan && (u.status === 'approved' || u.is_vip);
    const isPend = !isBan && !isApp && (u.status === 'pending' || u.status === 'pending_vip');
    
    let stBadge = '';
    if(isBan){
      stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(255,46,99,0.25);color:var(--bad)">🚫 BANNED (បានបិទគណនី)</span>`;
    } else if(u.role === 'admin'){
      stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(192,132,252,0.25);color:#c084fc">🛡️ ADMIN</span>`;
    } else if(isApp){
      const daysTxt = u.days_left === -1 ? 'Lifetime' : `សល់ ${u.days_left} ថ្ងៃ`;
      stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(46,204,113,0.2);color:var(--good)">👑 VIP [${esc(u.package_name || u.approved_package || 'VIP')}] (${daysTxt})</span>`;
    } else if(isPend){
      stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(241,196,15,0.2);color:var(--gold)">⏳ PENDING VIP [${esc(u.requested_package || '1_year')}]</span>`;
    } else {
      stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(255,106,43,0.2);color:var(--accent)">👤 ធម្មតា (ភាគ 1-10)</span>`;
    }
    
    const reqPkg = u.requested_package || '1_year';
    const targetKey = u.username || u.device_id || u.key;

    return `<div style="background:var(--surface);padding:12px 14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px;box-shadow:0 2px 8px rgba(0,0,0,0.2)">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap">
            <b style="font-size:13.5px;color:var(--ink)">${esc(u.name || u.username || 'Unknown')}</b>
            ${stBadge}
            ${u.username ? `<span style="font-size:11.5px;color:var(--muted)">(@${esc(u.username)})</span>` : ''}
            ${u.contact ? `<span style="font-size:12px;color:var(--accent);font-weight:600">📞 ${esc(u.contact)}</span>` : ''}
          </div>
          <div style="display:flex;align-items:center;gap:10px;margin-top:4px;font-size:11px;color:var(--muted);font-family:var(--font-mono);flex-wrap:wrap">
            <span>Device: ${esc(u.device_id || 'Web Client')}</span>
            ${u.expires_date ? `<span>ផុតកំណត់: ${esc(u.expires_date)}</span>` : ''}
          </div>
          ${u.note ? `<div style="font-size:11.5px;color:var(--muted);margin-top:3px;font-style:italic">📝 "${esc(u.note)}"</div>` : ''}
        </div>
        ${u.role !== 'admin' ? `<button class="btn ghost sm" style="padding:2px 8px;font-size:11.5px;color:var(--muted)" title="Delete record" onclick="adminDeleteUser('${esc(targetKey)}')">🗑️</button>` : ''}
      </div>

      <!-- Action Controls Row for Admin -->
      ${u.role !== 'admin' ? `
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;border-top:1px dashed var(--line);padding-top:8px">
        <!-- Package / Custom Days Selector -->
        <select id="pkgSel_${esc(targetKey)}" onchange="onAdminPkgChange('${esc(targetKey)}')" style="height:30px;background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:0 6px;color:var(--ink);font:600 11.5px var(--font-ui)">
          <option value="1_month" ${reqPkg==='1_month'?'selected':''}>VIP 1 ខែ (30 ថ្ងៃ)</option>
          <option value="3_months" ${reqPkg==='3_months'?'selected':''}>VIP 3 ខែ (90 ថ្ងៃ)</option>
          <option value="6_months" ${reqPkg==='6_months'?'selected':''}>VIP 6 ខែ (180 ថ្ងៃ)</option>
          <option value="1_year" ${reqPkg==='1_year'?'selected':''}>VIP 1 ឆ្នាំ (365 ថ្ងៃ)</option>
          <option value="lifetime" ${reqPkg==='lifetime'?'selected':''}>VIP មួយជីវិត (Lifetime)</option>
          <option value="custom">កំណត់ថ្ងៃផ្ទាល់...</option>
        </select>
        <input type="number" id="customDays_${esc(targetKey)}" placeholder="ថ្ងៃ (Days)" min="1" max="9999" style="width:80px;height:30px;background:var(--surface-2);border:1px solid var(--line);border-radius:6px;padding:0 6px;color:var(--ink);font:600 11.5px var(--font-mono);display:none">

        <button class="btn primary sm" style="padding:2px 12px;height:30px;font-size:11.5px;font-weight:700" onclick="adminApproveUser('${esc(targetKey)}')">✅ អនុញ្ញាត VIP</button>

        <!-- Ban / Unban Account -->
        ${isBan ? `
          <button class="btn sm" style="height:30px;padding:2px 10px;font-size:11.5px;font-weight:700;background:rgba(46,204,113,0.18);color:var(--good);border:1px solid rgba(46,204,113,0.35)" onclick="adminBanUser('${esc(targetKey)}', false)">✅ បើកគណនី (Unban)</button>
        ` : `
          <button class="btn sm" style="height:30px;padding:2px 10px;font-size:11.5px;font-weight:700;background:rgba(255,46,99,0.15);color:var(--bad);border:1px solid rgba(255,46,99,0.35)" onclick="adminBanUser('${esc(targetKey)}', true)">🚫 បិទគណនី (Ban)</button>
        `}

        <!-- Revoke VIP -->
        ${isApp ? `
          <button class="btn ghost sm" style="height:30px;padding:2px 10px;font-size:11.5px;color:var(--accent);border-color:rgba(255,106,43,0.35)" onclick="adminRevokeUser('${esc(targetKey)}')">⛔ ដកសិទ្ធិ VIP</button>
        ` : ''}
      </div>` : ''}
    </div>`;
  }).join('');
}

window.onAdminPkgChange = function(targetKey){
  const sel = $(`#pkgSel_${targetKey}`);
  const inp = $(`#customDays_${targetKey}`);
  if(sel && inp){
    if(sel.value === 'custom'){
      inp.style.display = 'inline-block';
      inp.focus();
    } else {
      inp.style.display = 'none';
    }
  }
};

const manualPkgSel = $("#adminManualPkg");
if(manualPkgSel){
  manualPkgSel.onchange = e => {
    const daysInp = $("#adminManualDaysInput");
    if(daysInp){
      if(e.target.value === 'custom'){
        daysInp.style.display = 'inline-block';
        daysInp.focus();
      } else {
        daysInp.style.display = 'none';
      }
    }
  };
}

// User Search & Filter Listeners
const ucSearchInp = $("#ucUserSearchInput");
if(ucSearchInp){
  ucSearchInp.addEventListener('input', e => {
    currentAdminSearch = e.target.value;
    applyAdminUserFilterAndRender();
  });
}

document.querySelectorAll(".uc-filter-btn").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".uc-filter-btn").forEach(b => b.classList.remove('on'));
    btn.classList.add('on');
    currentAdminFilter = btn.dataset.filter || 'all';
    applyAdminUserFilterAndRender();
  };
});

async function refreshAdminUsersList(){
  const tok = localStorage.getItem('syd_auth_token') || '';
  const pin = currentAdminPin || '8888';
  try {
    const res = await fetch(`/dl/access/admin/users?pin=${encodeURIComponent(pin)}&token=${encodeURIComponent(tok)}`);
    const j = await res.json();
    if(j.ok){
      renderAdminMode(j.mode);
      if(j.settings) renderAdminSettings(j.settings);
      cachedAdminUsers = j.users || [];
      applyAdminUserFilterAndRender();
    }
  } catch(e){}
}

window.adminApproveUser = async function(targetKey, explicitPkg, customDays){
  const sel = $(`#pkgSel_${targetKey}`);
  const daysInp = $(`#customDays_${targetKey}`);
  
  let pkg = explicitPkg || (sel && sel.value) || '1_year';
  let days = customDays || (daysInp && daysInp.value ? parseInt(daysInp.value, 10) : null);
  if(pkg === 'custom' && !days){
    toast("⚠️ សូមបញ្ចូលចំនួនថ្ងៃសម្រាប់ Custom Days", true);
    if(daysInp) daysInp.focus();
    return;
  }

  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/access/admin/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin: currentAdminPin || '8888',
        token: tok,
        target_id: targetKey,
        package: pkg,
        custom_days: days
      })
    });
    const j = await res.json();
    if(j.ok){
      toast(`✅ បានអនុម័ត VIP ជូន ${targetKey} រួចរាល់!`);
      refreshAdminUsersList();
      fetchAccessStatus();
    } else {
      toast("⚠️ " + (j.error || "បរាជ័យ"), true);
    }
  } catch(e){
    toast("Error: " + e, true);
  }
};

window.adminBanUser = async function(targetKey, banned){
  const actionText = banned ? "បិទគណនី (Ban)" : "បើកដំណើរការគណនីឡើងវិញ (Unban)";
  if(!confirm(`តើអ្នកពិតជាចង់ ${actionText} របស់ ${targetKey} មែនទេ?`)) return;
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/access/admin/ban", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin: currentAdminPin || '8888',
        token: tok,
        target_id: targetKey,
        banned: !!banned
      })
    });
    const j = await res.json();
    if(j.ok){
      toast(banned ? `🚫 បានបិទគណនី ${targetKey} រួចរាល់!` : `✅ បានបើកគណនី ${targetKey} ឡើងវិញរួចរាល់!`);
      refreshAdminUsersList();
      fetchAccessStatus();
    } else {
      toast("⚠️ " + (j.error || "បរាជ័យ"), true);
    }
  } catch(e){
    toast("Error: " + e, true);
  }
};

window.adminRevokeUser = async function(targetKey){
  if(!confirm(`តើអ្នកពិតជាចង់ដកសិទ្ធិ VIP របស់ ${targetKey} ត្រឡប់មកគណនីធម្មតាមែនទេ?`)) return;
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/access/admin/revoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: currentAdminPin || '8888', token: tok, target_id: targetKey })
    });
    const j = await res.json();
    if(j.ok){
      toast(`⛔ បានដកសិទ្ធិ VIP របស់ ${targetKey} រួចរាល់!`);
      refreshAdminUsersList();
      fetchAccessStatus();
    } else {
      toast("⚠️ " + (j.error || "បរាជ័យ"), true);
    }
  } catch(e){
    toast("Error: " + e, true);
  }
};

window.adminDeleteUser = async function(targetKey){
  if(!confirm(`តើអ្នកពិតជាចង់លុបទិន្នន័យគណនី ${targetKey} មែនទេ?`)) return;
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/access/admin/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin: currentAdminPin || '8888', token: tok, target_id: targetKey })
    });
    const j = await res.json();
    if(j.ok){
      toast("🗑️ បានលុបទិន្នន័យរួចរាល់!");
      refreshAdminUsersList();
    } else {
      toast("⚠️ " + (j.error || "បរាជ័យ"), true);
    }
  } catch(e){
    toast("Error: " + e, true);
  }
};

// Admin Manual Approver Button
const adminManAppBtn = $("#adminManualApproveBtn");
if(adminManAppBtn){
  adminManAppBtn.onclick = async () => {
    const devInput = $("#adminManualDevId");
    const devId = (devInput && devInput.value.trim()) || '';
    const pkg = ($("#adminManualPkg") && $("#adminManualPkg").value) || '1_year';
    const daysInp = $("#adminManualDaysInput");
    const days = (daysInp && daysInp.value ? parseInt(daysInp.value, 10) : null);
    if(!devId){
      toast("⚠️ សូមបញ្ចូល Device ID ឬ Username", true);
      return;
    }
    await window.adminApproveUser(devId, pkg, days);
    if(devInput) devInput.value = '';
    if(daysInp) daysInp.value = '';
  };
}

// KHQR File Upload Handlers
const khqrUploadBtn = $("#adminKhqrUploadBtn");
const khqrFileInput = $("#adminKhqrFileInput");
if(khqrUploadBtn && khqrFileInput){
  khqrUploadBtn.onclick = () => khqrFileInput.click();
  khqrFileInput.onchange = e => {
    const file = e.target.files && e.target.files[0];
    if(!file) return;
    if(file.size > 3 * 1024 * 1024){
      toast("⚠️ រូបភាព KHQR ធំពេក (សូមជ្រើសរើសទំហំក្រោម 3MB)", true);
      return;
    }
    const reader = new FileReader();
    reader.onload = ev => {
      currentKhqrBase64 = ev.target.result;
      const preview = $("#adminKhqrPreview");
      const ph = $("#adminKhqrPlaceholder");
      if(preview){
        preview.src = currentKhqrBase64;
        preview.style.display = "block";
      }
      if(ph) ph.style.display = "none";
      toast("📷 បានជ្រើសរើសរូបភាព KHQR! សូមចុច 'រក្សាទុកការកំណត់ទាំងអស់'");
    };
    reader.readAsDataURL(file);
  };
}

const khqrRemoveBtn = $("#adminKhqrRemoveBtn");
if(khqrRemoveBtn){
  khqrRemoveBtn.onclick = () => {
    currentKhqrBase64 = '';
    const preview = $("#adminKhqrPreview");
    const ph = $("#adminKhqrPlaceholder");
    if(preview){
      preview.src = "";
      preview.style.display = "none";
    }
    if(ph) ph.style.display = "block";
    if(khqrFileInput) khqrFileInput.value = '';
    toast("🗑️ បានលុបរូបភាព KHQR ចេញ! សូមចុច 'រក្សាទុកការកំណត់ទាំងអស់'");
  };
}

// Save All Admin Settings
const adminSaveAllSettingsBtn = $("#adminSaveAllSettingsBtn");
if(adminSaveAllSettingsBtn){
  adminSaveAllSettingsBtn.onclick = async () => {
    adminSaveAllSettingsBtn.disabled = true;
    adminSaveAllSettingsBtn.innerHTML = "<span>⏳ កំពុងរក្សាទុក...</span>";
    const pin = currentAdminPin || '8888';
    const tok = localStorage.getItem('syd_auth_token') || '';
    const tgAdmin = ($("#adminTgAdminInput") && $("#adminTgAdminInput").value.trim()) || '';
    const tgGroup = ($("#adminTgGroupInput") && $("#adminTgGroupInput").value.trim()) || '';
    
    const checkedMode = document.querySelector('input[name="adminModeRadio"]:checked');
    const mode = checkedMode ? checkedMode.value : 'vip_required';

    const settingsPayload = {
      khqr_image: currentKhqrBase64 || '',
      telegram_admin: tgAdmin,
      telegram_group: tgGroup
    };

    try {
      const res = await fetch("/dl/access/admin/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, token: tok, settings: settingsPayload })
      });
      const j = await res.json();
      if(j.ok){
        await fetch("/dl/access/admin/mode", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ pin, token: tok, mode })
        });
        toast("✅ បានរក្សាទុកការកំណត់ KHQR, Telegram & System Mode ដោយជោគជ័យ!");
        await fetchAccessStatus();
      } else {
        toast("⚠️ " + (j.error || "បរាជ័យក្នុងការរក្សាទុក"), true);
      }
    } catch(e){
      toast("⚠️ កំហុសបណ្តាញ: " + e, true);
    } finally {
      adminSaveAllSettingsBtn.disabled = false;
      adminSaveAllSettingsBtn.innerHTML = "<span>💾 រក្សាទុកការកំណត់ទាំងអស់ (Save All Settings)</span>";
    }
  };
}

const adminPinBtn = $("#adminPinBtn");
if(adminPinBtn){
  adminPinBtn.onclick = async () => {
    const pin = ($("#adminPinInput") && $("#adminPinInput").value.trim()) || '';
    if(!pin){
      toast("⚠️ សូមបញ្ចូល Admin PIN", true);
      return;
    }
    await checkAndUnlockAdmin(pin);
  };
}

const adminRefUsersBtn = $("#adminRefreshUsersBtn");
if(adminRefUsersBtn) adminRefUsersBtn.onclick = refreshAdminUsersList;

'''

final_content = part2_1 + new_js_2 + part2_2

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("Updated Auth and Admin JS successfully!")
