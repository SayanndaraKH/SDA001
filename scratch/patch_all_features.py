import sys, re
sys.stdout.reconfigure(encoding='utf-8')

FILE = 'app/web/downloader.html'
with open(FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update renderDramaDetailUI to call updateDramaDetailCoinUI(item)
target_rdd_end = '''  renderDramaDetailEpisodes();
  updateDdQueueBtn();
}'''

replacement_rdd_end = '''  renderDramaDetailEpisodes();
  updateDdQueueBtn();
  if(typeof updateDramaDetailCoinUI === 'function'){
    updateDramaDetailCoinUI(item);
  }
}'''

if target_rdd_end in text:
    text = text.replace(target_rdd_end, replacement_rdd_end, 1)
    print("1. Hooked updateDramaDetailCoinUI into renderDramaDetailUI")

# 2. Update promptVipModal
target_pvm = '''function promptVipModal(epNum){
  const vipReqEnabled = !!(window.userAccess && window.userAccess.settings && (window.userAccess.settings.vip_request_enabled === true || window.userAccess.settings.vip_request_enabled === 'true' || window.userAccess.settings.vip_request_enabled === 1));
  if(!vipReqEnabled){
    toast(`🔒 ភាគទី ${epNum} ត្រូវបានចាក់សោរ! បច្ចុប្បន្ន ADMIN បានបិទការស្នើសុំ VIP ជាបណ្តោះអាសន្ន។`, true);
    return;
  }
  const maxFree = (window.userAccess && window.userAccess.max_free_episodes) || 5;
  const banner = $("#authAlertBanner");
  const alertText = $("#authAlertText");
  if(banner && alertText){
    alertText.innerHTML = `🔒 <b>ភាគទី ${epNum} ត្រូវបានចាក់សោរ (Locked)!</b><br>គណនីធម្មតាអាចទស្សនា & ដោនឡូតបានត្រឹម <b>ភាគ 1 ដល់ ${maxFree}</b> ប៉ុណ្ណោះ។<br>👉 សូមស្នើសុំកញ្ចប់ VIP ពី ADMIN ដើម្បីទស្សនា និងដោនឡូតគ្រប់ភាគទាំងអស់ដោយគ្មានការ Lock!`;
    banner.style.display = 'block';
  }
  openUserRegisterModal('vip', false);
}'''

replacement_pvm = '''function promptVipModal(epNum){
  const isAuth = !!(window.userAccess && window.userAccess.authenticated);
  if(!isAuth){
    toast(`🔒 ភាគទី ${epNum} ត្រូវបានចាក់សោរ! សូមចូលគណនី ឬចុះឈ្មោះដើម្បីទស្សនា`, true);
    openUserRegisterModal('login', true);
    return;
  }

  const sid = ddCurrentDrama ? (ddCurrentDrama.id || ddCurrentDrama.series_id) : '';
  const title = ddCurrentDrama ? (ddCurrentDrama.title_km || ddCurrentDrama.title) : 'រឿងនេះ';
  const userCoins = Number((window.userAccess && window.userAccess.coins) || 0);

  const banner = $("#authAlertBanner");
  const alertText = $("#authAlertText");
  if(banner && alertText){
    alertText.innerHTML = `🔒 <b>ភាគទី ${epNum} នៃរឿង 《${esc(title)}》 ត្រូវបានចាក់សោរ!</b><br>
    🪙 <b>ទិញដោះសោររឿងនេះ៖</b> ត្រូវការត្រឹមតែ <b>2 Coins (1,000៛)</b> ដោះសោរគ្រប់ភាគទាំងអស់ជាអចិន្ត្រៃយ៍!<br>
    👑 <b>ឬស្នើសុំកញ្ចប់ VIP៖</b> ដោះសោរគ្រប់រឿងទាំងអស់ក្នុងកម្មវិធីដោយគ្មានការ Lock!`;
    banner.style.display = 'block';
  }

  if(sid && userCoins >= 2){
    if(confirm(`🔒 ភាគទី ${epNum} ត្រូវបានចាក់សោរ!\n\nសមតុល្យរបស់អ្នកមាន: ${userCoins} Coins\nរឿងនេះត្រូវការ: 2 Coins (1,000៛) ដើម្បីដោះសោរគ្រប់ភាគទាំងអស់។\n\nតើអ្នកចង់ទិញដោះសោររឿងនេះឥឡូវនេះទេ?`)){
      buyDramaWithCoins(sid, title);
      return;
    }
  } else if(sid && userCoins < 2){
    if(confirm(`🔒 ភាគទី ${epNum} ត្រូវបានចាក់សោរ!\n\nសមតុល្យ Coins របស់អ្នក: ${userCoins} Coins (មិនគ្រប់ 2 Coins ទេ)\n\nតើអ្នកចង់បើកកាបូប Coin ដើម្បីបញ្ចូល Coin (Top-up) ដែរឬទេ?`)){
      openCoinModal();
      return;
    }
  }

  openUserRegisterModal('vip', false);
}'''

if target_pvm in text:
    text = text.replace(target_pvm, replacement_pvm, 1)
    print("2. Updated promptVipModal with Coin prompt")

# 3. Update doExplicitLogout
target_logout = '''  toast("🚪 បានចាកចេញពីគណនីជោគជ័យ (Guest Mode)");

  window.userAccess = { authenticated: false, role: 'guest', status: 'guest' };
  updateAccessUI(window.userAccess);
  openUserRegisterModal('login', true);

  await fetchAccessStatus();'''

replacement_logout = '''  localStorage.removeItem('syd_auth_token');
  sessionStorage.removeItem('syd_auth_token');
  sessionStorage.removeItem('hg_admin_pin');

  toast("🚪 បានចាកចេញពីគណនីជោគជ័យ! សូមចូលគណនីដើម្បីបន្តប្រើប្រាស់");

  window.userAccess = { 
    authenticated: false, 
    role: 'unauthenticated', 
    status: 'login_required', 
    must_register: true, 
    must_login: true, 
    username: 'មិនទាន់ចូលគណនី' 
  };
  updateAccessUI(window.userAccess);
  isMandatoryAuth = true;
  openUserRegisterModal('login', true);'''

if target_logout in text:
    text = text.replace(target_logout, replacement_logout, 1)
    print("3. Updated doExplicitLogout to enforce strict mandatory login and remove guest mode")

# 4. In updateAccessUI: show/hide #topCoinBadge, update coins, replace guest labels
target_guest_badge = '''  } else if(isUser){
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
  }'''

replacement_guest_badge = '''  } else if(isUser){
    if(icon) icon.textContent = "👤";
    if(txt) txt.textContent = `${data.username} (ភាគ 1-5)`;
    if(badge){
      badge.style.borderColor = "rgba(255,106,43,0.5)";
      badge.style.color = "var(--accent)";
      badge.style.background = "rgba(255,106,43,0.1)";
      badge.style.boxShadow = "none";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--accent);font-weight:700">👤 ចូលជា: ${esc(data.username)} (ភាគ 1-5 ឥតគិតថ្លៃ)</span>`;
  } else {
    // Unauthenticated
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
    if(footUser) footUser.textContent = "មិនទាន់ចូលគណនី (សូមចូលគណនី ឬចុះឈ្មោះ)";
  }

  // Update Topbar Coins Badge
  const topCoinBadge = $("#topCoinBadge");
  const topCoinsVal = $("#topCoinsVal");
  const topCoinsRiel = $("#topCoinsRiel");
  if(topCoinBadge){
    const isAuth = !!(data && data.authenticated);
    if(isAuth){
      const coins = Number((data && data.coins) || 0);
      if(topCoinsVal) topCoinsVal.textContent = coins;
      if(topCoinsRiel) topCoinsRiel.textContent = (coins * 500).toLocaleString();
      topCoinBadge.style.display = "inline-flex";
    } else {
      topCoinBadge.style.display = "none";
    }
  }

  // Update Drama Detail Coin UI
  if(typeof updateDramaDetailCoinUI === 'function' && ddCurrentDrama){
    updateDramaDetailCoinUI(ddCurrentDrama);
  }'''

if target_guest_badge in text:
    text = text.replace(target_guest_badge, replacement_guest_badge, 1)
    print("4. Updated updateAccessUI for topbar coins badge and eliminated guest labels")

# 5. Append Coin Logic & Functions before closing </script>
coin_js_block = '''
// ====================================================
// SYD COIN WALLET & PURCHASE DRAMA LOGIC
// ====================================================

function updateDramaDetailCoinUI(item){
  const sid = item ? (item.id || item.series_id) : (ddCurrentDrama ? (ddCurrentDrama.id || ddCurrentDrama.series_id) : null);
  if(!sid) return;

  const coinBadge = $("#ddCoinPriceBadge");
  const buyBtn = $("#ddBuyDramaBtn");
  const isPurchased = !!(window.userAccess && window.userAccess.purchased_series && (window.userAccess.purchased_series[sid] || (Array.isArray(window.userAccess.purchased_series) && window.userAccess.purchased_series.includes(sid))));
  const isVipOrAdmin = !!(window.userAccess && (window.userAccess.is_vip || window.userAccess.is_admin || window.userAccess.role === 'admin' || window.userAccess.role === 'dev'));

  if(coinBadge){
    if(isPurchased){
      coinBadge.textContent = "✅ បានទិញរួចរាល់ (Unlocked)";
      coinBadge.style.background = "rgba(34,197,94,0.18)";
      coinBadge.style.color = "#22c55e";
      coinBadge.style.border = "1px solid rgba(34,197,94,0.4)";
      coinBadge.title = "អ្នកបានទិញរឿងនេះរួចរាល់ អាចទស្សនា & ដោនឡូតគ្រប់ភាគដោយសេរី";
    } else if(isVipOrAdmin){
      coinBadge.textContent = "🎁 Free សម្រាប់អ្នក (VIP)";
      coinBadge.style.background = "rgba(56,189,248,0.15)";
      coinBadge.style.color = "#38bdf8";
      coinBadge.style.border = "1px solid rgba(56,189,248,0.4)";
      coinBadge.title = "គណនី VIP/Admin មានសិទ្ធិទស្សនា & ដោនឡូតឥតគិត Coin";
    } else {
      coinBadge.textContent = "🪙 2 Coins (1,000៛)";
      coinBadge.style.background = "rgba(234,179,8,0.15)";
      coinBadge.style.color = "#eab308";
      coinBadge.style.border = "1px solid rgba(234,179,8,0.4)";
      coinBadge.title = "1 Coin = 500៛ | ដោះសោររឿងនេះគ្រប់ភាគទាំងអស់ជាអចិន្ត្រៃយ៍";
    }
  }

  if(buyBtn){
    if(isPurchased){
      buyBtn.style.display = "inline-flex";
      buyBtn.disabled = true;
      buyBtn.style.background = "rgba(34,197,94,0.2)";
      buyBtn.style.color = "#22c55e";
      buyBtn.style.boxShadow = "none";
      buyBtn.style.cursor = "default";
      buyBtn.innerHTML = "<span>✅ បានទិញរួចរាល់</span>";
      buyBtn.title = "រឿងនេះត្រូវបានដោះសោរគ្រប់ភាគរួចរាល់ហើយ";
    } else if(isVipOrAdmin){
      buyBtn.style.display = "none";
    } else {
      buyBtn.style.display = "inline-flex";
      buyBtn.disabled = false;
      buyBtn.style.background = "linear-gradient(135deg,#eab308,#ca8a04)";
      buyBtn.style.color = "#000";
      buyBtn.style.boxShadow = "0 3px 12px rgba(234,179,8,0.35)";
      buyBtn.style.cursor = "pointer";
      buyBtn.innerHTML = "<span>🛒 ទិញរឿងនេះ (2 Coins)</span>";
      buyBtn.title = "ទិញដោះសោររឿងនេះដោយប្រើ 2 Coins (1,000៛)";
    }
  }
}

window.openCoinModal = function(){
  if(!window.userAccess || !window.userAccess.authenticated){
    toast("សូមចូលគណនីជាមុនសិន ដើម្បីទិញ Coin!", true);
    if(typeof openUserRegisterModal === 'function') openUserRegisterModal('login', true);
    return;
  }
  const modal = $("#coinModal");
  if(!modal) return;
  const coins = Number((window.userAccess && window.userAccess.coins) || 0);
  const coinsEl = $("#coinModalUserCoins");
  const rielEl = $("#coinModalUserRiel");
  const nameEl = $("#coinModalUserAccountName");
  if(coinsEl) coinsEl.textContent = coins;
  if(rielEl) rielEl.textContent = (coins * 500).toLocaleString();
  if(nameEl) nameEl.textContent = `គណនី: ${window.userAccess.username || window.userAccess.name || window.userAccess.device_id || 'User'}`;
  
  modal.hidden = false;
  loadMyCoinRequests();
};

window.closeCoinModal = function(){
  const modal = $("#coinModal");
  if(modal) modal.hidden = true;
};

window.selectCoinPackage = function(coins, riel){
  const inp = $("#coinReqInput");
  const dsp = $("#coinReqRielDisplay");
  if(inp) inp.value = coins;
  if(dsp) dsp.value = Number(riel).toLocaleString() + ' ៛';
};

window.onCoinReqInputChange = function(){
  const inp = $("#coinReqInput");
  const dsp = $("#coinReqRielDisplay");
  if(!inp || !dsp) return;
  const coins = Math.max(1, parseInt(inp.value || '0', 10));
  dsp.value = (coins * 500).toLocaleString() + ' ៛';
};

window.submitCoinRequest = function(){
  if(!window.userAccess || !window.userAccess.authenticated){
    toast("សូមចូលគណនីជាមុនសិន!", true);
    if(typeof openUserRegisterModal === 'function') openUserRegisterModal('login', true);
    return;
  }
  const inp = $("#coinReqInput");
  const noteInp = $("#coinReqNoteInput");
  const msgEl = $("#coinReqStatusMsg");
  const btn = $("#coinReqSubmitBtn");
  const coins = parseInt((inp && inp.value) || '0', 10);
  const note = (noteInp && noteInp.value.trim()) || '';

  if(coins < 1){
    toast("សូមបញ្ចូលចំនួន Coin យ៉ាងតិច 1 Coin!", true);
    return;
  }

  if(btn) btn.disabled = true;
  if(msgEl){
    msgEl.style.display = "block";
    msgEl.style.background = "rgba(56,189,248,0.15)";
    msgEl.style.color = "#38bdf8";
    msgEl.textContent = "⏳ កំពុងផ្ញើសំណើទិញ Coin ទៅ Admin...";
  }

  const payload = {
    amount_coins: coins,
    note: note,
    device_id: window.userAccess.device_id || '',
    token: localStorage.getItem('syd_auth_token') || ''
  };

  fetch("/dl/coins/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(j => {
    if(btn) btn.disabled = false;
    if(j.ok){
      if(msgEl){
        msgEl.style.background = "rgba(46,204,113,0.15)";
        msgEl.style.color = "var(--good)";
        msgEl.textContent = `✅ បានផ្ញើសំណើទិញ ${coins} Coin រួចរាល់! Admin នឹងពិនិត្យនិងបញ្ចូលជូនភ្លាមៗ។`;
      }
      toast(`✅ បានផ្ញើសំណើទិញ ${coins} Coin!`, false);
      if(noteInp) noteInp.value = '';
      loadMyCoinRequests();
    } else {
      if(msgEl){
        msgEl.style.background = "rgba(255,46,99,0.15)";
        msgEl.style.color = "var(--bad)";
        msgEl.textContent = "❌ បរាជ័យ: " + (j.error || "មិនអាចផ្ញើសំណើបានទេ");
      }
      toast("❌ " + (j.error || "បរាជ័យ"), true);
    }
  })
  .catch(e => {
    if(btn) btn.disabled = false;
    if(msgEl){
      msgEl.style.background = "rgba(255,46,99,0.15)";
      msgEl.style.color = "var(--bad)";
      msgEl.textContent = "⚠️ កំហុស: " + e;
    }
    toast("⚠️ កំហុសបណ្តាញ: " + e, true);
  });
};

window.loadMyCoinRequests = function(){
  if(!window.userAccess || !window.userAccess.device_id) return;
  const list = $("#coinMyRequestsList");
  if(!list) return;
  const devId = window.userAccess.device_id;
  const tok = localStorage.getItem('syd_auth_token') || '';

  fetch(`/dl/coins/my_requests?device_id=${encodeURIComponent(devId)}&token=${encodeURIComponent(tok)}`)
  .then(r => r.json())
  .then(j => {
    if(!j.ok || !j.requests || !j.requests.length){
      list.innerHTML = '<div style="text-align:center;padding:12px;color:var(--muted);font-size:11.5px">មិនទាន់មានសំណើទិញ Coin ទេ</div>';
      return;
    }
    list.innerHTML = j.requests.map(r => {
      let stBadge = '';
      if(r.status === 'approved'){
        stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(46,204,113,0.2);color:var(--good)">✅ បានអនុម័ត (+${r.amount_coins} Coins)</span>`;
      } else if(r.status === 'rejected'){
        stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(255,46,99,0.2);color:var(--bad)">❌ បានបដិសេធ</span>`;
      } else {
        stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(241,196,15,0.2);color:var(--gold)">⏳ កំពុងរង់ចាំ Admin</span>`;
      }
      return `<div style="background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;display:flex;justify-content:space-between;align-items:center;font-size:11.5px">
        <div>
          <b style="color:#eab308;font-size:13px">${r.amount_coins} Coins</b>
          <span style="color:var(--muted);margin-left:6px">(${Number(r.amount_riel || 0).toLocaleString()} ៛)</span>
          <div style="color:var(--muted);font-size:10.5px;margin-top:2px">${r.note ? esc(r.note) + ' · ' : ''}${r.created_at ? r.created_at.slice(0, 16).replace('T', ' ') : ''}</div>
        </div>
        <div>${stBadge}</div>
      </div>`;
    }).join('');
  })
  .catch(e => {
    list.innerHTML = '<div style="text-align:center;padding:12px;color:var(--muted);font-size:11.5px">មិនអាចទាញយកប្រវត្តិសំណើបានទេ</div>';
  });
};

window.buyCurrentDramaWithCoins = function(){
  if(!ddCurrentDrama){
    toast("⚠️ សូមជ្រើសរើសរឿងជាមុនសិន!", true);
    return;
  }
  const sid = ddCurrentDrama.id || ddCurrentDrama.series_id;
  const title = ddCurrentDrama.title_km || ddCurrentDrama.title;
  buyDramaWithCoins(sid, title);
};

window.buyDramaWithCoins = async function(sid, title){
  if(!window.userAccess || !window.userAccess.authenticated){
    toast("សូមចូលគណនីជាមុនសិន ដើម្បីទិញរឿងដោះសោរ!", true);
    if(typeof openUserRegisterModal === 'function') openUserRegisterModal('login', true);
    return;
  }

  const sidStr = String(sid || '').trim();
  if(!sidStr){
    toast("⚠️ មិនមានលេខសម្គាល់រឿង (Series ID) ទេ!", true);
    return;
  }

  const dramaTitle = title || sidStr;
  const currentCoins = Number((window.userAccess && window.userAccess.coins) || 0);

  const purchased = window.userAccess.purchased_series || {};
  if(purchased[sidStr] || (Array.isArray(purchased) && purchased.includes(sidStr))){
    toast(`✅ អ្នកបានទិញរឿង 《${dramaTitle}》 រួចរាល់ហើយ!`, false);
    return;
  }

  if(!confirm(`🛒 តើអ្នកពិតជាចង់ប្រើ 2 Coins (1,000៛) ដើម្បីដោះសោររឿង 《${dramaTitle}》 គ្រប់ភាគទាំងអស់ជាអចិន្ត្រៃយ៍មែនទេ?\\n\\nសមតុល្យ Coin បច្ចុប្បន្ន: ${currentCoins} Coins`)){
    return;
  }

  if(currentCoins < 2){
    toast(`🪙 Coins មិនគ្រប់គ្រាន់ទេ! រឿងនេះត្រូវការ 2 Coins (1,000៛) ប៉ុន្តែអ្នកមានត្រឹម ${currentCoins} Coins។`, true);
    if(typeof openCoinModal === 'function') openCoinModal();
    return;
  }

  const tok = localStorage.getItem('syd_auth_token') || '';
  const devId = (window.userAccess && window.userAccess.device_id) || '';

  toast(`⏳ កំពុងដំណើរការទិញរឿង 《${dramaTitle}》...`, false);

  try {
    const res = await fetch("/dl/access/purchase-series", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: tok,
        device_id: devId,
        series_id: sidStr,
        series_title: dramaTitle
      })
    });
    const j = await res.json();
    if(j.ok){
      if(!window.userAccess.purchased_series) window.userAccess.purchased_series = {};
      window.userAccess.purchased_series[sidStr] = {
        series_id: sidStr,
        title: dramaTitle,
        coins: 2,
        purchased_at: Date.now() / 1000
      };
      if(j.coins !== undefined) window.userAccess.coins = Number(j.coins);
      if(j.coins_riel !== undefined) window.userAccess.coins_riel = Number(j.coins_riel);

      const topCoinsVal = $("#topCoinsVal");
      const topCoinsRiel = $("#topCoinsRiel");
      if(topCoinsVal) topCoinsVal.textContent = window.userAccess.coins;
      if(topCoinsRiel) topCoinsRiel.textContent = (window.userAccess.coins * 500).toLocaleString();

      if(typeof updateDramaDetailCoinUI === 'function' && ddCurrentDrama){
        updateDramaDetailCoinUI(ddCurrentDrama);
      }
      if(typeof renderDramaDetailEpisodes === 'function' && ddCurrentDrama){
        renderDramaDetailEpisodes();
      }

      toast(`🎉 ${j.message || "ទិញដោះសោររឿងជោគជ័យ! អ្នកអាចទស្សនា និងដោនឡូតគ្រប់ភាគទាំងអស់ដោយសេរី"}`, false);
    } else {
      if(j.reason === 'insufficient_coins'){
        toast(`❌ ${j.error || "Coins មិនគ្រប់គ្រាន់ទេ"}`, true);
        if(typeof openCoinModal === 'function') openCoinModal();
      } else if(j.reason === 'login_required'){
        toast(`⚠️ ${j.error || "សូមចូលគណនីជាមុនសិន!"}`, true);
        if(typeof openUserRegisterModal === 'function') openUserRegisterModal('login', true);
      } else {
        toast(`❌ បរាជ័យ: ${j.error || "មិនអាចទិញរឿងបានទេ"}`, true);
      }
    }
  } catch(e){
    toast(`⚠️ កំហុសបណ្តាញ: ${e.message}`, true);
  }
};
'''

idx_script_end = text.rfind('</script>')
if idx_script_end != -1 and 'updateDramaDetailCoinUI' not in text:
    text = text[:idx_script_end] + coin_js_block + '\n' + text[idx_script_end:]
    print("5. Appended SYD Coin Wallet & Purchase Drama JS functions")

# 6. Replace remaining "1-10" with "1-5"
count_1_10 = 0
replacements_1_10 = [
    ("គណនីធម្មតាអាចមើលបានត្រឹមភាគ 1-10", "គណនីធម្មតាអាចមើលបានត្រឹមភាគ 1-5"),
    ("🔒 ភាគនេះត្រូវបានចាក់សោរ (Locked)! គណនីធម្មតាអាចមើលបានត្រឹមភាគ 1-10 ប៉ុណ្ណោះ។", "🔒 ភាគនេះត្រូវបានចាក់សោរ (Locked)! គណនីធម្មតាអាចមើលបានត្រឹមភាគ 1-5 ប៉ុណ្ណោះ។"),
    ("ទស្សនា &amp; ដោនឡូតភាគ 1-10 ឥតគិតថ្លៃ", "ទស្សនា &amp; ដោនឡូតភាគ 1-5 ឥតគិតថ្លៃ"),
    ("🔒 VIP Required (គណនីធម្មតាមើលបានភាគ 1-10, VIP មើលបានគ្រប់ភាគ - Recommended)", "🔒 VIP Required (គណនីធម្មតាមើលបានភាគ 1-5, VIP មើលបានគ្រប់ភាគ - Recommended)"),
    ("អ្នកប្រើប្រាស់ធម្មតាអាចមើលនិងទាញយកបានត្រឹមភាគ 1-10។ ចាប់ពីភាគ 11 ឡើងទៅ តម្រូវឱ្យមានកញ្ចប់ VIP។", "អ្នកប្រើប្រាស់ធម្មតាអាចមើលនិងទាញយកបានត្រឹមភាគ 1-5។ ចាប់ពីភាគ 6 ឡើងទៅ តម្រូវឱ្យមានកញ្ចប់ VIP ឬ Coin។"),
    ("toast(`⬇️ គណនីធម្មតា៖ បានដាក់ភាគ 1-10 នៃរឿង 《${ddCurrentDrama.title}》 ចូលក្នុង Queue`);", "toast(`⬇️ គណនីធម្មតា៖ បានដាក់ភាគ 1-5 នៃរឿង 《${ddCurrentDrama.title}》 ចូលក្នុង Queue`);"),
    ("toast(\"💡 គណនីធម្មតាអាចជ្រើសរើសបានត្រឹមភាគ 1-10 ប៉ុណ្ណោះ。 សូមស្នើសុំ VIP ដើម្បីដោនឡូតគ្រប់ភាគ!\");", "toast(\"💡 គណនីធម្មតាអាចជ្រើសរើសបានត្រឹមភាគ 1-5 ប៉ុណ្ណោះ។ សូមទិញ Coin ឬស្នើសុំ VIP ដើម្បីដោនឡូតគ្រប់ភាគ!\");"),
    ("if(regExp) regExp.textContent = \"ទស្សនា & ដោនឡូតបានភាគ 1-10\";", "if(regExp) regExp.textContent = \"ទស្សនា & ដោនឡូតបានភាគ 1-5\";"),
    ("stBadge = `<span style=\"font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(255,106,43,0.2);color:var(--accent)\">👤 ធម្មតា (ភាគ 1-10)</span>`;", "stBadge = `<span style=\"font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(255,106,43,0.2);color:var(--accent)\">👤 ធម្មតា (ភាគ 1-5)</span>`;"),
    ("មិនទាន់ចូលគណនី (Guest)", "មិនទាន់ចូលគណនី (សូមចូលគណនី)")
]

for old, new in replacements_1_10:
    if old in text:
        text = text.replace(old, new)
        count_1_10 += 1

print(f"6. Replaced {count_1_10} occurrences of 1-10 / Guest with 1-5")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(text)
print("All patches saved successfully.")
