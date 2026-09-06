import re

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update initFrontCast to dynamically fetch /dl/actors
old_init_fc = """function initFrontCast() {
  window.allActorsList = [];
  window.allActorsMap = {};
  for (const a of INITIAL_FRONT_ACTORS) {
    window.allActorsMap[a.name] = a;
    window.allActorsList.push(a);
  }
  renderFrontCastList();
  initFrontCastDragScroll();
}"""

new_init_fc = """async function initFrontCast() {
  window.allActorsList = [];
  window.allActorsMap = {};
  for (const a of INITIAL_FRONT_ACTORS) {
    window.allActorsMap[a.name] = a;
    window.allActorsList.push(a);
  }
  renderFrontCastList();
  initFrontCastDragScroll();

  // Load all 137+ actors dynamically from https://hongguoduanju.com/
  try {
    const res = await fetch("/dl/actors");
    if (res.ok) {
      const data = await res.json();
      if (data && data.actors && data.actors.length) {
        window.allActorsList = [];
        window.allActorsMap = {};
        for (const a of data.actors) {
          window.allActorsMap[a.name] = a;
          window.allActorsList.push(a);
        }
        renderFrontCastList();
      }
    }
  } catch (e) {
    console.warn("Could not load /dl/actors:", e);
  }
}"""

html = html.replace(old_init_fc, new_init_fc)

# 2. Update loadDramasForActor to populate actor.dramas immediately
old_known_sid = """  if (knownSid && !seenIds.has(String(knownSid))) {
    seenIds.add(String(knownSid));
    localMatches.unshift({
      id: knownSid,
      series_id: knownSid,
      title: knownTitle || actorName,
      title_km: knownTitle || actorName,
      cover: actor.cover || (actor.avatar ? actor.avatar : ''),
      episode_cnt: 60,
      total: 60,
      score: '8.2'
    });
  }"""

new_known_sid = """  // Pre-load all dramas directly known from https://hongguoduanju.com/
  if (actor && actor.dramas && Array.isArray(actor.dramas)) {
    for (const d of actor.dramas) {
      const sid = String(d.series_id || '');
      if (sid && !seenIds.has(sid)) {
        seenIds.add(sid);
        localMatches.push({
          id: sid,
          series_id: sid,
          title: d.title || actorName,
          title_km: d.title_km || '',
          cover: d.cover || '',
          episode_cnt: d.episode_cnt || 60,
          total: d.episode_cnt || 60,
          score: '8.3'
        });
      }
    }
  }

  if (knownSid && !seenIds.has(String(knownSid))) {
    seenIds.add(String(knownSid));
    localMatches.unshift({
      id: knownSid,
      series_id: knownSid,
      title: knownTitle || actorName,
      title_km: knownTitle || actorName,
      cover: actor.cover || (actor.avatar ? actor.avatar : ''),
      episode_cnt: 60,
      total: 60,
      score: '8.2'
    });
  }"""

html = html.replace(old_known_sid, new_known_sid)

# 3. Update VIP banner in detail modal
old_vip_banner = """<span><b>គណនីធម្មតា:</b> ទស្សនា &amp; ដោនឡូតបានត្រឹមភាគ <b>1 ដល់ 10</b> (ភាគ 11+ ត្រូវបានចាក់សោរ) <span id="ddVipDaysHint" style="font-weight:700;color:var(--accent)"></span></span>"""
new_vip_banner = """<span><b>គណនីធម្មតា:</b> ទស្សនា &amp; ដោនឡូតបានត្រឹមភាគ <b>1 ដល់ 5</b> (ភាគ 6+ ត្រូវបានចាក់សោរ) <span id="ddVipDaysHint" style="font-weight:700;color:var(--accent)"></span></span>"""
html = html.replace(old_vip_banner, new_vip_banner)

html = html.replace('onclick="promptVipModal(11)"', 'onclick="promptVipModal(6)"')

# 4. Update ddSetFree10Btn to ddSetFree5Btn
html = html.replace('id="ddSetFree10Btn" onclick="doAdminSetDramaRule(\'free_episodes\', 10)"', 'id="ddSetFree5Btn" onclick="doAdminSetDramaRule(\'free_episodes\', 5)"')
html = html.replace('>🟠 Free 1-10<', '>🟠 Free 1-5<')
html = html.replace('const b10 = $("#ddSetFree10Btn");', 'const b10 = $("#ddSetFree5Btn");')

# 5. Update options
html = html.replace('<option value="free_episodes">🟠 Free ភាគ 1-10 តាមធម្មតា (លំនាំដើម)</option>', '<option value="free_episodes">🟠 Free ភាគ 1-5 តាមធម្មតា (លំនាំដើម)</option>')
html = html.replace('<option value="free_episodes">🟠 Free 1-10 ភាគ</option>', '<option value="free_episodes">🟠 Free 1-5 ភាគ</option>')

# 6. Update episode rendering for normal users in renderDramaDetailEpisodes
old_render_eps = """  // Filter episodes based on active range
  let visibleEps = eps;
  if(eps.length > DD_RANGE_SIZE && ddActiveRange >= 0){
    const startIdx = ddActiveRange * DD_RANGE_SIZE;
    visibleEps = eps.slice(startIdx, startIdx + DD_RANGE_SIZE);
  }

  gridEl.innerHTML = visibleEps.map(n => {
    const isSel = ddSelectedEps.has(n);
    const isPlaying = (ddInlinePlayingEp === n);
    const isLocked = isEpisodeLocked(n);
    let cls = "dd-epchip-item";
    if(isPlaying) cls += " active-playing";
    else if(!isStream && isSel) cls += " selected-for-dl";
    if(isLocked) cls += " locked-vip";
    
    const titleHint = isLocked
      ? `ភាគទី ${n} · 🔒 VIP Only (គណនីធម្មតាអាចមើលបានត្រឹមភាគ 1-10 · ចុចដើម្បីស្នើសុំ VIP)`
      : `ភាគទី ${n} · ចុចដើម្បី ${isStream ? 'Live Stream មើលភ្លាមៗ' : 'ជ្រើសរើសដោនឡូត'}`;

    return `<button type="button" class="${cls}" data-dei="${n}" aria-pressed="${isSel}" title="${titleHint}">${n}</button>`;
  }).join("");"""

new_render_eps = """  // For normal users, restrict display to free episodes (default 1-5) unless drama is free_all
  const isFull = isUserFullAccess();
  let userEpLimit = eps.length;
  let isDramaFreeAll = false;
  const currSid = (item && (item.id || item.series_id)) || (ddCurrentDrama ? ddCurrentDrama.id : null);
  if (currSid && typeof getDramaRuleForSeries === 'function') {
    const dr = getDramaRuleForSeries(currSid);
    if (dr && dr.rule === 'free_all') isDramaFreeAll = true;
    else if (dr && dr.free_episodes != null) userEpLimit = Number(dr.free_episodes);
    else userEpLimit = 5;
  } else {
    userEpLimit = 5;
  }

  let visibleEps = eps;
  if (!isFull && !isDramaFreeAll) {
    // Normal User: display only episodes 1 to 5
    visibleEps = eps.filter(n => Number(n) <= userEpLimit);
    if (rangesEl) {
      rangesEl.hidden = false;
      rangesEl.innerHTML = `<span style="font-size:12px;font-weight:700;color:var(--accent);background:rgba(255,106,43,0.15);border:1px solid rgba(255,106,43,0.3);padding:4px 12px;border-radius:20px">🟠 ភាគ 1 - ${userEpLimit} (Free សម្រាប់ User ធម្មតា)</span>`;
    }
  } else {
    if(eps.length > DD_RANGE_SIZE && ddActiveRange >= 0){
      const startIdx = ddActiveRange * DD_RANGE_SIZE;
      visibleEps = eps.slice(startIdx, startIdx + DD_RANGE_SIZE);
    }
  }

  let chipsHtml = visibleEps.map(n => {
    const isSel = ddSelectedEps.has(n);
    const isPlaying = (ddInlinePlayingEp === n);
    const isLocked = isEpisodeLocked(n, currSid);
    let cls = "dd-epchip-item";
    if(isPlaying) cls += " active-playing";
    else if(!isStream && isSel) cls += " selected-for-dl";
    if(isLocked) cls += " locked-vip";
    
    const titleHint = isLocked
      ? `ភាគទី ${n} · 🔒 VIP Only (គណនីធម្មតាអាចមើលបានត្រឹមភាគ 1-${userEpLimit} · ចុចដើម្បីស្នើសុំ VIP)`
      : `ភាគទី ${n} · ចុចដើម្បី ${isStream ? 'Live Stream មើលភ្លាមៗ' : 'ជ្រើសរើសដោនឡូត'}`;

    return `<button type="button" class="${cls}" data-dei="${n}" aria-pressed="${isSel}" title="${titleHint}">${n}</button>`;
  }).join("");

  if (!isFull && !isDramaFreeAll && eps.length > userEpLimit) {
    chipsHtml += `<button type="button" class="dd-epchip-item locked-vip" onclick="promptVipModal(${userEpLimit + 1})" title="ភាគ ${userEpLimit + 1} ឡើងទៅ សម្រាប់តែសមាជិក VIP (ចុចដើម្បីស្នើសុំ VIP)" style="grid-column:span 2;min-width:130px;background:linear-gradient(135deg,rgba(255,46,99,0.15),rgba(255,106,43,0.15));border:1.5px dashed rgba(255,46,99,0.5);color:#ff2e63;font-size:11.5px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:4px;border-radius:8px">🔒 ភាគ ${userEpLimit + 1}+ (VIP)</button>`;
  }

  gridEl.innerHTML = chipsHtml;"""

html = html.replace(old_render_eps, new_render_eps)

# 7. Update isEpisodeLocked default from 10 to 5
html = html.replace('return Number(epNum) > 10;', 'return Number(epNum) > 5;')

# 8. Update defaultDramaRule
html = html.replace('let defaultDramaRule = { rule: "free_episodes", free_episodes: 10 };', 'let defaultDramaRule = { rule: "free_episodes", free_episodes: 5 };')
html = html.replace('const eps = defaultDramaRule.free_episodes || 10;', 'const eps = defaultDramaRule.free_episodes || 5;')
html = html.replace('let limitText = "ភាគ 1 ដល់ 10";', 'let limitText = "ភាគ 1 ដល់ 5";')
html = html.replace('const curLimit = (r && r.free_episodes) ? r.free_episodes : 10;', 'const curLimit = (r && r.free_episodes) ? r.free_episodes : 5;')
html = html.replace('const lim = (r && r.free_episodes) ? r.free_episodes : 10;', 'const lim = (r && r.free_episodes) ? r.free_episodes : 5;')
html = html.replace('rule: rule, free_episodes: Number(freeEps) || 10', 'rule: rule, free_episodes: Number(freeEps) || 5')
html = html.replace('Number(freeEps) || 10', 'Number(freeEps) || 5')
html = html.replace('free_episodes: 10', 'free_episodes: 5')

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated app/web/downloader.html successfully!")
