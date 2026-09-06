
/* Display size — scale the whole UI to fit the user's monitor / Windows display scaling
   (125%, 150%, 200%, small laptops). Applied via CSS zoom on the root; persisted per device. */
(function(){
  var KEY='hg_uiscale', STEPS=[60,70,80,90,100,110,125,150,175,200];
  function cur(){ var v=parseInt(localStorage.getItem(KEY)||'100',10); return STEPS.indexOf(v)>-1?v:100; }
  function apply(v){ try{ document.documentElement.style.zoom = v/100; }catch(e){}
    var el=document.getElementById('uiZoomVal'); if(el) el.textContent=v+'%'; }
  function set(v){ localStorage.setItem(KEY,String(v)); apply(v); }
  apply(cur());
  document.addEventListener('click',function(e){
    var t=e.target; if(!t||!t.id) return;
    if(t.id==='uiZoomIn'){ var i=STEPS.indexOf(cur()); if(i<STEPS.length-1) set(STEPS[i+1]); }
    else if(t.id==='uiZoomOut'){ var i=STEPS.indexOf(cur()); if(i>0) set(STEPS[i-1]); }
  });
})();

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
