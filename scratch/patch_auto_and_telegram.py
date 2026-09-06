import sys

def patch():
    path = 'app/web/downloader.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Topbar: Add Telegram Admin Contact Badge
    old_topbar_entry = '<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">\n      <button class="btn ghost sm" id="acctBtn"'
    new_topbar_entry = """<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <!-- Telegram Admin Direct Contact (Front Page) -->
      <a href="https://t.me/sydadmin168" target="_blank" rel="noopener" class="btn ghost sm" id="topTelegramAdminBtn" style="border-radius:20px;font-weight:800;font-size:12px;display:inline-flex;align-items:center;gap:6px;border-color:rgba(56,189,248,0.5);color:#38bdf8;text-decoration:none;background:rgba(56,189,248,0.08);padding:5px 12px;box-shadow:0 0 10px rgba(56,189,248,0.2)" title="ទំនាក់ទំនង ADMIN ផ្ទាល់តាម Telegram: https://t.me/sydadmin168">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
        <span>ទំនាក់ទំនង ADMIN</span>
      </a>
      <button class="btn ghost sm" id="acctBtn" """

    if old_topbar_entry not in content:
        print("ERROR: old_topbar_entry not found!")
        return False
    content = content.replace(old_topbar_entry, new_topbar_entry, 1)

    # 2. Hero Section: Add Telegram Admin Badge next to Live Data
    old_hero_live = '<span id="liveSyncTime" style="color:var(--muted);font-weight:600;font-size:11px">· ផ្សាយផ្ទាល់</span>\n      </div>'
    new_hero_live = """<span id="liveSyncTime" style="color:var(--muted);font-weight:600;font-size:11px">· ផ្សាយផ្ទាល់</span>
      </div>
      <!-- Front Page Prominent Telegram Admin Contact Link -->
      <a href="https://t.me/sydadmin168" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.36);border-radius:20px;padding:6px 14px;font:700 12px/1 var(--font-km),var(--font-ui);color:#38bdf8;text-decoration:none;box-shadow:var(--shadow-sm);transition:all .18s ease" title="ទំនាក់ទំនង ADMIN តាម Telegram">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
        <span>ទំនាក់ទំនង ADMIN: <b style="font-family:var(--font-mono)">https://t.me/sydadmin168</b></span>
      </a>"""

    if old_hero_live not in content:
        print("ERROR: old_hero_live not found!")
        return False
    content = content.replace(old_hero_live, new_hero_live, 1)

    # 3. Home VIP Promotion Banner: Add Telegram Admin Button
    old_vip_banner_btn = '<button type="button" class="btn primary" onclick="openUserRegisterModal(\'vip\')"'
    new_vip_banner_btn = """<a href="https://t.me/sydadmin168" target="_blank" rel="noopener" class="btn ghost" style="border-radius:24px;font-weight:800;font-size:12.5px;padding:8px 16px;border-color:rgba(56,189,248,0.5);color:#38bdf8;background:rgba(56,189,248,0.1);display:inline-flex;align-items:center;gap:7px;text-decoration:none" title="ទំនាក់ទំនង ADMIN តាម Telegram">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
      <span>ទំនាក់ទំនង ADMIN</span>
    </a>
    <button type="button" class="btn primary" onclick="openUserRegisterModal('vip')\""""

    if old_vip_banner_btn in content:
        content = content.replace(old_vip_banner_btn, new_vip_banner_btn, 1)

    # 4. Admin Dashboard: Add Auto Default Drama Rule Setting in ucTabDramaRulesSec
    old_rules_tab = """          <div style="font-size:12px;color:var(--ink-2);line-height:1.5">
            Admin អាចកំណត់រឿងណា <b>Free 100% (គ្រប់ភាគ)</b> ឬ <b>Free 1-10 ភាគ</b> សម្រាប់ User ធម្មតាបានដោយសេរីតាមចិត្តចង់។ (User VIP មើលបានគ្រប់ភាគទាំងអស់ជាស្វ័យប្រវត្តិ)។
          </div>

          <!-- Quick Rule Adder Card -->"""

    new_rules_tab = """          <div style="font-size:12px;color:var(--ink-2);line-height:1.5">
            Admin អាចកំណត់រឿងណា <b>Free 100% (គ្រប់ភាគ)</b> ឬ <b>Free 1-10 ភាគ</b> សម្រាប់ User ធម្មតាបានដោយសេរីតាមចិត្តចង់។ (User VIP មើលបានគ្រប់ភាគទាំងអស់ជាស្វ័យប្រវត្តិ)។
          </div>

          <!-- ⚡ Auto / Default Rule for All & New Dramas (កំណត់សិទ្ធិស្វ័យប្រវត្តិសម្រាប់រឿងថ្មី/ទាំងអស់) -->
          <div style="background:var(--surface);padding:14px;border-radius:12px;border:1.5px solid rgba(56,189,248,0.4);display:flex;flex-direction:column;gap:10px;box-shadow:0 2px 10px rgba(56,189,248,0.1)">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">
              <div style="font:800 13px var(--font-ui);color:#38bdf8;display:flex;align-items:center;gap:6px">
                <span>⚡</span> <span>កំណត់សិទ្ធិស្វ័យប្រវត្តិ (Auto) សម្រាប់រឿងថ្មី ឬរឿងទាំងអស់៖</span>
              </div>
              <span id="adminDrAutoStatusBadge" style="font-size:11.5px;font-weight:700;padding:3px 10px;border-radius:20px;background:rgba(255,106,43,0.15);color:var(--accent);border:1px solid rgba(255,106,43,0.3)">
                🟠 កំពុងប្រើ: Free 1-10 ភាគ
              </span>
            </div>
            <div style="font-size:12px;color:var(--muted);line-height:1.45">
              រាល់រឿងថ្មីៗទាំងអស់ក្នុងប្រព័ន្ធ ដែលមិនទាន់បានកំណត់ដោយឡែក នឹងទទួលបានសិទ្ធិ Auto នេះដោយស្វ័យប្រវត្តិ! Admin អាចផ្លាស់ប្តូរបានគ្រប់ពេល៖
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
              <select id="adminDrDefaultRuleType" onchange="toggleAdminDrDefaultCustomEps()" style="flex:2 1 200px;height:36px;background:var(--surface-2);border:1.5px solid var(--accent);border-radius:8px;padding:0 10px;color:var(--ink);font:700 12.5px var(--font-ui)">
                <option value="free_episodes">🟠 Free ភាគ 1-10 តាមធម្មតា (លំនាំដើម)</option>
                <option value="free_all">🎁 Free 100% គ្រប់ភាគទាំងអស់ (Auto Free All)</option>
                <option value="custom">⚙️ កំណត់ចំនួនភាគ Free ផ្ទាល់ (Auto Custom)</option>
              </select>
              <input type="number" id="adminDrDefaultCustomEps" placeholder="ចំនួនភាគ" min="1" max="999" value="10" style="width:110px;height:36px;background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:0 10px;color:var(--ink);font:700 12.5px var(--font-mono);display:none">
              <button type="button" class="btn primary sm" onclick="submitAdminDefaultDramaRule()" style="height:36px;padding:0 18px;font-weight:800;font-size:12.5px;background:linear-gradient(135deg,#0ea5e9,#0284c7);box-shadow:0 3px 12px rgba(14,165,233,0.35);border-radius:8px">
                💾 រក្សាទុក Auto
              </button>
            </div>
          </div>

          <!-- Quick Rule Adder Card -->"""

    if old_rules_tab not in content:
        print("ERROR: old_rules_tab not found!")
        return False
    content = content.replace(old_rules_tab, new_rules_tab, 1)

    # 5. JavaScript: Add defaultDramaRule and handlers
    old_js_rules = """/* ---------- Drama Free Rules Management (Admin & Episode Lock Engine) ---------- */
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
}"""

    new_js_rules = """/* ---------- Drama Free Rules Management (Admin & Episode Lock Engine) ---------- */
let cachedDramaRules = {};
let defaultDramaRule = { rule: "free_episodes", free_episodes: 10 };

async function fetchDramaRules(){
  try {
    const res = await fetch("/dl/drama/rules");
    if(res.ok){
      const data = await res.json();
      if(data.ok){
        if(data.rules) cachedDramaRules = data.rules;
        if(data.default_rule){
          defaultDramaRule = data.default_rule;
          updateAdminDefaultDramaRuleUI();
        }
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

function updateAdminDefaultDramaRuleUI(){
  const sel = $("#adminDrDefaultRuleType");
  const inp = $("#adminDrDefaultCustomEps");
  const badge = $("#adminDrAutoStatusBadge");
  const rule = defaultDramaRule.rule || 'free_episodes';
  const eps = defaultDramaRule.free_episodes || 10;
  if(sel){
    if(rule === 'free_all') sel.value = 'free_all';
    else if(eps === 10) sel.value = 'free_episodes';
    else {
      sel.value = 'custom';
      if(inp) inp.value = eps;
    }
    toggleAdminDrDefaultCustomEps();
  }
  if(badge){
    if(rule === 'free_all'){
      badge.innerHTML = "🎁 កំពុងប្រើ: Free 100% (គ្រប់ភាគ)";
      badge.style.background = "rgba(34,197,94,0.18)";
      badge.style.color = "#22c55e";
      badge.style.borderColor = "rgba(34,197,94,0.35)";
    } else {
      badge.innerHTML = `🟠 កំពុងប្រើ: Free ភាគ 1-${eps}`;
      badge.style.background = "rgba(255,106,43,0.18)";
      badge.style.color = "var(--accent)";
      badge.style.borderColor = "rgba(255,106,43,0.35)";
    }
  }
}

function toggleAdminDrDefaultCustomEps(){
  const sel = $("#adminDrDefaultRuleType");
  const inp = $("#adminDrDefaultCustomEps");
  if(!sel || !inp) return;
  inp.style.display = (sel.value === 'custom') ? 'inline-block' : 'none';
}

async function submitAdminDefaultDramaRule(){
  const sel = $("#adminDrDefaultRuleType");
  const inp = $("#adminDrDefaultCustomEps");
  let rule = sel ? sel.value : 'free_episodes';
  let freeEps = 10;
  if(rule === 'custom'){
    rule = 'free_episodes';
    freeEps = inp ? (parseInt(inp.value, 10) || 10) : 10;
    if(freeEps < 1) freeEps = 10;
  } else if(rule === 'free_all'){
    freeEps = 999999;
  }

  const pin = currentAdminPin || 'syd@168';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/admin/drama_rules/default", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin, token: tok, rule, free_episodes: freeEps
      })
    });
    const j = await res.json();
    if(j.ok && j.default_rule){
      defaultDramaRule = j.default_rule;
      updateAdminDefaultDramaRuleUI();
      toast(rule === 'free_all' ? "🎁 បានកំណត់សិទ្ធិ Auto សម្រាប់រឿងថ្មី/ទាំងអស់: Free 100% ជោគជ័យ!" : `🟠 បានកំណត់សិទ្ធិ Auto សម្រាប់រឿងថ្មី/ទាំងអស់: Free 1-${freeEps} ភាគ ជោគជ័យ!`);
      if(ddCurrentDrama){
        renderDramaDetailUI(ddCurrentDrama);
        renderDramaDetailEpisodes();
      }
    } else {
      toast("❌ " + (j.error || "បរាជ័យក្នុងការកំណត់ Auto"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ: " + e, true);
  }
}

function getDramaRuleForSeries(sid){
  if(sid && cachedDramaRules && cachedDramaRules[String(sid)]){
    return cachedDramaRules[String(sid)];
  }
  return defaultDramaRule;
}"""

    if old_js_rules not in content:
        print("ERROR: old_js_rules not found!")
        return False
    content = content.replace(old_js_rules, new_js_rules, 1)

    # 6. Update loadAdminDramaRules to also parse default_rule and update UI
    old_load_admin_rules = """    if(j.ok && j.rules){
      cachedDramaRules = j.rules;
      renderAdminDramaRulesList();"""
    new_load_admin_rules = """    if(j.ok){
      if(j.rules) cachedDramaRules = j.rules;
      if(j.default_rule){
        defaultDramaRule = j.default_rule;
        updateAdminDefaultDramaRuleUI();
      }
      renderAdminDramaRulesList();"""
    if old_load_admin_rules in content:
        content = content.replace(old_load_admin_rules, new_load_admin_rules, 1)

    # 7. Update renderDramaDetailUI to show Auto vs Custom badges
    old_detail_badge = """  // Update Drama Free Rule Badge & Admin Bar
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
  }"""

    new_detail_badge = """  // Update Drama Free Rule Badge & Admin Bar
  const ruleBadge = $("#ddDramaRuleBadge");
  const adminBar = $("#ddAdminRuleBar");
  const sid = String(item.id || '');
  const hasCustom = !!(cachedDramaRules && cachedDramaRules[sid]);
  const r = (typeof getDramaRuleForSeries === 'function') ? getDramaRuleForSeries(sid) : defaultDramaRule;
  const isFreeAll = (r && r.rule === 'free_all');
  if(ruleBadge){
    if(isFreeAll){
      ruleBadge.textContent = hasCustom ? "🟢 Free 100% (គ្រប់ភាគ)" : "🎁 Auto: Free 100% (គ្រប់ភាគ)";
      ruleBadge.style.background = "rgba(34,197,94,0.18)";
      ruleBadge.style.color = "#22c55e";
      ruleBadge.style.border = "1px solid rgba(34,197,94,0.4)";
    } else {
      const lim = (r && r.free_episodes) ? r.free_episodes : 10;
      ruleBadge.textContent = hasCustom ? `🟠 Free ភាគ 1-${lim}` : `⚡ Auto: Free ភាគ 1-${lim}`;
      ruleBadge.style.background = "rgba(255,106,43,0.16)";
      ruleBadge.style.color = "var(--accent)";
      ruleBadge.style.border = "1px solid rgba(255,106,43,0.35)";
    }
  }"""

    if old_detail_badge in content:
        content = content.replace(old_detail_badge, new_detail_badge, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: downloader.html patched with Auto Drama Rules and front-screen Telegram contact!")
    return True

if __name__ == '__main__':
    patch()
