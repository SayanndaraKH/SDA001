// --- User Coin Modal Logic ---
window.openCoinModal = function(){
  if(!window.userAccess || !window.userAccess.authenticated){
    toast("សូមចូលគណនីជាមុនសិន ដើម្បីទិញ Coin!", true);
    if(typeof openUserRegisterModal === 'function') openUserRegisterModal('login');
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
      return `<div style="background:var(--surface);padding:8px 12px;border-radius:8px;border:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;font-size:12px">
        <div>
          <div style="font-weight:700;color:var(--ink)">🪙 ${r.amount_coins} Coins (${(r.total_riel || (r.amount_coins*500)).toLocaleString()}៛)</div>
          <div style="font-size:11px;color:var(--muted);margin-top:2px">${r.created_at ? r.created_at.slice(0, 19).replace('T', ' ') : ''} ${r.note ? '• ' + esc(r.note) : ''}</div>
        </div>
        <div>${stBadge}</div>
      </div>`;
    }).join('');
  })
  .catch(e => {
    list.innerHTML = '<div style="text-align:center;padding:12px;color:var(--muted);font-size:11.5px">មិនអាចទាញយកសំណើបានទេ</div>';
  });
};

// --- Admin Coin Dashboard Logic ---
window.adminRefreshAllCoinsData = function(){
  adminLoadPricingRules();
  adminRefreshCoinRequests();
  adminRefreshCoinTransactions();
};

window.adminLoadPricingRules = function(){
  fetch("/dl/coins/pricing")
  .then(r => r.json())
  .then(j => {
    if(j.ok && j.rules){
      const r = j.rules;
      const defCoins = $("#adminRuleDefaultCoins");
      const rateRiel = $("#adminRuleCoinRateRiel");
      const promoEn = $("#adminPromoEnabled");
      const promoCoins = $("#adminPromoCoins");
      const promoStart = $("#adminPromoStartDate");
      const promoEnd = $("#adminPromoEndDate");
      if(defCoins) defCoins.value = r.default_coins || 2;
      if(rateRiel) rateRiel.value = r.coin_rate_riel || 500;
      if(promoEn) promoEn.checked = !!r.promo_enabled;
      if(promoCoins) promoCoins.value = r.promo_coins || 1;
      if(promoStart) promoStart.value = r.promo_start_date || '';
      if(promoEnd) promoEnd.value = r.promo_end_date || '';
    }
  })
  .catch(e => console.warn("Load pricing rules failed", e));
};

window.adminSavePricingRules = function(){
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || 'syd@168';
  const defCoins = parseInt(($("#adminRuleDefaultCoins") && $("#adminRuleDefaultCoins").value) || '2', 10);
  const rateRiel = parseInt(($("#adminRuleCoinRateRiel") && $("#adminRuleCoinRateRiel").value) || '500', 10);
  const promoEn = !!($("#adminPromoEnabled") && $("#adminPromoEnabled").checked);
  const promoCoins = parseInt(($("#adminPromoCoins") && $("#adminPromoCoins").value) || '1', 10);
  const promoStart = ($("#adminPromoStartDate") && $("#adminPromoStartDate").value) || '';
  const promoEnd = ($("#adminPromoEndDate") && $("#adminPromoEndDate").value) || '';

  const payload = {
    admin_pin: pin,
    rules: {
      default_coins: defCoins,
      coin_rate_riel: rateRiel,
      promo_enabled: promoEn,
      promo_coins: promoCoins,
      promo_start_date: promoStart,
      promo_end_date: promoEnd
    }
  };

  const saveMsg = $("#adminPricingSaveMsg");
  fetch("/dl/admin/coins/pricing", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(j => {
    if(j.ok){
      toast("✅ បានរក្សាទុកតម្លៃរឿង & ប្រូម៉ូសិនរួចរាល់!", false);
      if(saveMsg){
        saveMsg.textContent = "✅ បានរក្សាទុក!";
        saveMsg.style.color = "var(--good)";
        saveMsg.style.display = "inline";
        setTimeout(() => { saveMsg.style.display = "none"; }, 3000);
      }
    } else {
      toast("❌ បរាជ័យ: " + (j.error || "មិនអាចរក្សាទុកបានទេ"), true);
    }
  })
  .catch(e => toast("⚠️ កំហុស: " + e, true));
};

window.adminRefreshCoinRequests = function(){
  const container = $("#adminCoinRequestsContainer");
  const badge = $("#adminCoinReqBadge");
  if(!container) return;
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || 'syd@168';

  fetch(`/dl/admin/coins/requests?admin_pin=${encodeURIComponent(pin)}`)
  .then(r => r.json())
  .then(j => {
    if(!j.ok || !j.requests || !j.requests.length){
      container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--muted);font-size:12px">មិនមានសំណើទិញ Coin ទេ</div>';
      if(badge) badge.textContent = '0';
      return;
    }
    const pendingCount = j.requests.filter(r => r.status === 'pending').length;
    if(badge) badge.textContent = String(pendingCount);

    container.innerHTML = j.requests.map(r => {
      const isPending = r.status === 'pending';
      const isApproved = r.status === 'approved';
      let stBadge = '';
      if(isApproved){
        stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(46,204,113,0.2);color:var(--good)">✅ បានអនុម័ត</span>`;
      } else if(r.status === 'rejected'){
        stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(255,46,99,0.2);color:var(--bad)">❌ បានបដិសេធ</span>`;
      } else {
        stBadge = `<span style="font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:4px;background:rgba(241,196,15,0.2);color:var(--gold)">⏳ PENDING</span>`;
      }

      return `<div style="background:var(--surface);padding:10px 14px;border-radius:10px;border:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <div style="display:flex;align-items:center;gap:6px">
            <b style="font-size:13px;color:var(--ink)">${esc(r.username || r.device_id || 'User')}</b>
            ${stBadge}
            <span style="font-size:11.5px;font-weight:800;color:#eab308">🪙 +${r.amount_coins} Coins (${(r.total_riel || (r.amount_coins*500)).toLocaleString()}៛)</span>
          </div>
          <div style="font-size:11px;color:var(--muted);margin-top:3px;font-family:var(--font-mono)">
            Device: ${esc(r.device_id || 'N/A')} • ${r.created_at ? r.created_at.slice(0, 19).replace('T', ' ') : ''}
          </div>
          ${r.note ? `<div style="font-size:11.5px;color:var(--accent);margin-top:3px">📝 "${esc(r.note)}"</div>` : ''}
        </div>
        ${isPending ? `
        <div style="display:flex;gap:6px;align-items:center">
          <button type="button" class="btn primary sm" onclick="adminApproveCoinReq('${esc(r.id)}')" style="font-size:11.5px;padding:3px 12px;background:linear-gradient(135deg,#22c55e,#16a34a);font-weight:700">
            ✅ អនុម័ត (+${r.amount_coins})
          </button>
          <button type="button" class="btn ghost sm" onclick="adminRejectCoinReq('${esc(r.id)}')" style="font-size:11.5px;padding:3px 10px;color:var(--bad);border-color:rgba(255,46,99,0.4)">
            ❌ បដិសេធ
          </button>
        </div>` : ''}
      </div>`;
    }).join('');
  })
  .catch(e => {
    container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--bad);font-size:12px">កំហុសក្នុងការទាញយកសំណើ: ' + e + '</div>';
  });
};
 
window.adminApproveCoinReq = function(reqId){
  if(!confirm("តើអ្នកពិតជាចង់អនុម័តសំណើនេះ និងបញ្ចូល Coin ជូនគណនីមែនទេ?")) return;
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || 'syd@168';
  fetch("/dl/admin/coins/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ request_id: reqId, admin_pin: pin })
  })
  .then(r => r.json())
  .then(j => {
    if(j.ok){
      toast(`✅ បានអនុម័តជោគជ័យ! បញ្ចូល ${j.credited_coins} Coins`, false);
      adminRefreshCoinRequests();
      adminRefreshCoinTransactions();
      refreshAdminUsersList();
    } else {
      toast("❌ បរាជ័យ: " + (j.error || "មិនអាចអនុម័តបានទេ"), true);
    }
  })
  .catch(e => toast("⚠️ កំហុស: " + e, true));
};
 
window.adminRejectCoinReq = function(reqId){
  const reason = prompt("បញ្ចូលមូលហេតុនៃការបដិសេធ (Option):", "មិនទាន់ឃើញទឹកប្រាក់ចូលក្នុងគណនី");
  if(reason === null) return;
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || 'syd@168';
  fetch("/dl/admin/coins/reject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ request_id: reqId, reason: reason, admin_pin: pin })
  })
  .then(r => r.json())
  .then(j => {
    if(j.ok){
      toast("✅ បានបដិសេធសំណើរួចរាល់", false);
      adminRefreshCoinRequests();
    } else {
      toast("❌ បរាជ័យ: " + (j.error || "មិនអាចបដិសេធបានទេ"), true);
    }
  })
  .catch(e => toast("⚠️ កំហុស: " + e, true));
};

window.adminPromptAdjustCoins = function(targetKey, currentCoins){
  const input = prompt(
    `🪙 កែប្រែ Coin សម្រាប់គណនី [${targetKey}]:\n\n` +
    `- បញ្ចូលលេខវិជ្ជមាន (ឧ. 10 ឬ +10) ដើម្បីបន្ថែម Coin\n` +
    `- បញ្ចូលលេខអវិជ្ជមាន (ឧ. -5) ដើម្បីកាត់បន្ថយ Coin\n` +
    `- បញ្ចូល =50 ដើម្បីកំណត់ចំនួនជាក់លាក់\n\n` +
    `Coin បច្ចុប្បន្ន: ${currentCoins || 0} Coins`,
    "+10"
  );
  if(!input) return;
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || 'syd@168';
  fetch("/dl/admin/coins/adjust", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_id: targetKey, adjustment: input, admin_pin: pin })
  })
  .then(r => r.json())
  .then(j => {
    if(j.ok){
      toast(`✅ បានកែប្រែ Coin ជោគជ័យ! សមតុល្យថ្មី: ${j.new_coins} Coins`, false);
      refreshAdminUsersList();
      adminRefreshCoinTransactions();
    } else {
      toast("❌ " + (j.error || "បរាជ័យ"), true);
    }
  })
  .catch(e => toast("⚠️ កំហុស: " + e, true));
};

window.adminRefreshCoinTransactions = function(){
  const container = $("#adminCoinTxContainer");
  if(!container) return;
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || 'syd@168';

  fetch(`/dl/admin/coins/transactions?admin_pin=${encodeURIComponent(pin)}`)
  .then(r => r.json())
  .then(j => {
    if(!j.ok || !j.transactions || !j.transactions.length){
      container.innerHTML = '<div style="text-align:center;padding:12px;color:var(--muted);font-size:11.5px">មិនទាន់មានប្រតិបត្តិការ Coin ទេ</div>';
      return;
    }
    container.innerHTML = j.transactions.map(t => {
      const isPlus = (t.amount || 0) > 0;
      const amtStr = isPlus ? `+${t.amount}` : `${t.amount}`;
      const color = isPlus ? 'var(--good)' : 'var(--bad)';
      return `<div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;border-bottom:1px solid rgba(255,255,255,0.05);font-size:11px">
        <div>
          <b style="color:var(--ink)">${esc(t.device_id || 'User')}</b>
          <span style="color:var(--muted)"> • ${esc(t.reason || t.type || '')}</span>
          <span style="color:var(--muted);margin-left:4px">(${t.timestamp ? t.timestamp.slice(0, 19).replace('T', ' ') : ''})</span>
        </div>
        <div style="font-weight:800;color:${color};