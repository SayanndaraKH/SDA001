
const $ = s => document.querySelector(s);
const esc = s => (s==null?"":String(s)).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let cart = {};                 // { id: {title, total, cover} }
let lastStatus = { running:false, series:[], log:[] };
let DEMO = false;
// Always use real backend and real data whether running on localhost, Docker, or Railway
const ALLOW_DEMO = false;

try { cart = JSON.parse(localStorage.getItem("hg-cart")||"{}") || {}; } catch(e){ cart = {}; }
const saveCart = () => { const c={}; for(const k in cart){ if(!(cart[k]&&cart[k].unavailable)) c[k]=cart[k]; } localStorage.setItem("hg-cart", JSON.stringify(c)); };  // #4: don't persist "unavailable" placeholders

/* ---------- theme ---------- */
function applyTheme(t){ document.documentElement.setAttribute("data-theme", t);
  localStorage.setItem("hg-theme", t); $("#themeBtn").textContent = t==="dark" ? "☀" : "☾"; }
applyTheme(localStorage.getItem("hg-theme") || (matchMedia("(prefers-color-scheme:dark)").matches ? "dark" : "light"));
$("#themeBtn").onclick = () => applyTheme(document.documentElement.getAttribute("data-theme")==="dark" ? "light" : "dark");

/* ---------- toast ---------- */
let toastT;
function toast(msg, err){ const t=$("#toast"); t.textContent=msg; t.classList.toggle("err",!!err); t.classList.add("show");
  clearTimeout(toastT); toastT=setTimeout(()=>t.classList.remove("show"), 2600); }

/* ---------- gradient poster (covers-less fallback + demo) ---------- */
function hue(s){ let h=0; for(let i=0;i<(s||"").length;i++) h=(h*31+s.charCodeAt(i))>>>0; return h%360; }
function gradFor(title){ const h=hue(title); const h2=(h+34)%360;
  return `background:linear-gradient(155deg,hsl(${h} 62% 46%),hsl(${h2} 68% 30%))`; }
function getPosterUrl(cover, title, id){
  if(!cover){
    if(title) return `/dl/poster?name=${encodeURIComponent(title)}`;
    if(id) return `/dl/history/poster?series_id=${encodeURIComponent(id)}`;
    return '';
  }
  if(cover.startsWith('/dl/') || cover.startsWith('data:') || cover.startsWith('blob:') || cover.includes('workers.dev')){
    return cover;
  }
  return `/img?url=${encodeURIComponent(cover)}`;
}
function handlePosterError(img, title, id){
  if(!img) return;
  if(img.dataset.triedLocal !== '1'){
    img.dataset.triedLocal = '1';
    if(title){
      img.src = `/dl/poster?name=${encodeURIComponent(title)}&t=${Date.now()}`;
      return;
    } else if(id){
      img.src = `/dl/history/poster?series_id=${encodeURIComponent(id)}&t=${Date.now()}`;
      return;
    }
  }
  img.remove();
}
function posterArt(x, big, raw){
  const t = x.title||"";
  const grad = `<div class="grad" style="${gradFor(t)}">${big?esc(t):''}</div>`;
  if (x.cover && !DEMO){
    const src = raw || x.cover.includes('workers.dev') ? x.cover : `/img?url=${encodeURIComponent(x.cover)}`;
    return `<img src="${src}" alt="" loading="lazy" onerror="this.remove()">` + grad;
  }
  return grad;
}

/* ---------- omni: search vs link ---------- */
const looksLikeLink = t => /https?:\/\/|novelquickapp|novelapp|hongguoduanju|\/s\/|fqnovel|\.com\/|reading\//i.test(t) || /\n/.test(t.trim());
$("#omni").addEventListener("input", e=>{
  const link = looksLikeLink(e.target.value);
  const m=$("#omniMode"); m.textContent = link?"តំណភ្ជាប់":"ស្វែងរក"; m.classList.toggle("link",link);
});
function omniGo(){
  const v=$("#omni").value.trim(); if(!v) return;
  if (looksLikeLink(v)) addLinks(v); else doSearch(v);
}
$("#omniGo").onclick=omniGo;
$("#omni").addEventListener("keydown",e=>{ if(e.key==="Enter") omniGo(); });

/* ---------- search & catalog cards ---------- */
let dlHistory = {};
async function loadHistory(){
  try{
    const j = await (await fetch("/dl/history")).json();
    dlHistory = j.history || {};
  }catch(e){}
}

function getLibMap(){
  const map = {};
  // 1. Persistent download memory (survives moved/deleted folders and drive changes)
  for(const sid in dlHistory){
    const h = dlHistory[sid];
    map[String(sid)] = {
      series_id: String(sid),
      title: h.title,
      title_km: h.title_km || '',
      name: h.title,
      local: h.downloaded || h.total || 0,
      total: h.total || h.downloaded || 0,
      completed: !!h.completed,
      historyOnly: true,
      hasPoster: !!h.has_poster,
      cover: h.cover_url || ''
    };
    if(h.title) map[h.title.trim()] = map[String(sid)];
  }
  // 2. Current live library files on disk
  (libItems || []).forEach(x => {
    const entry = {
      series_id: String(x.series_id || ''),
      title: x.title,
      title_km: x.title_km || (map[String(x.series_id)]||{}).title_km || '',
      name: x.name,
      local: x.local,
      total: x.total,
      completed: x.total > 0 && x.local >= x.total,
      inLibraryNow: true,
      historyOnly: false,
      cover: x.poster || ''
    };
    if(x.series_id) map[String(x.series_id)] = entry;
    if(x.title) map[x.title.trim()] = entry;
    if(x.name) map[x.name.trim()] = entry;
  });
  return map;
}

function getDramaTimestamp(x){
  if(!x) return 0;
  if(x.create_time){
    const n = Number(x.create_time);
    if(!isNaN(n) && n > 0) return n > 1e11 ? Math.floor(n / 1000) : n;
  }
  if(x.created_at){
    const s = String(x.created_at).trim();
    if(s.match(/^\d{4}-\d{2}-\d{2}/)){
      const d = new Date(s.substring(0, 10) + 'T00:00:00');
      if(!isNaN(d.getTime())) return Math.floor(d.getTime() / 1000);
    }
  }
  if(x.series_id){
    try {
      const b = BigInt(String(x.series_id).trim());
      const ts = Number(b >> 32n);
      if(ts >= 1577836800 && ts <= 2000000000){
        return ts;
      }
    } catch(e){}
  }
  return 0;
}

function formatDramaDate(x){
  if(!x) return '';
  if(x.created_at && String(x.created_at).match(/^\d{4}-\d{2}-\d{2}/)){
    return String(x.created_at).substring(0, 10);
  }
  const ts = getDramaTimestamp(x);
  if(ts > 0){
    const d = new Date(ts * 1000);
    if(!isNaN(d.getTime())){
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    }
  }
  return '';
}

function getDramaType(x){
  if(!x) return '';
  const tabType = (x.tab_type || '').toLowerCase();
  const cat = (x.category || '').toLowerCase();
  const cats = Array.isArray(x.categories) ? x.categories.join(' ').toLowerCase() : '';
  const title = (x.title || '').toLowerCase();
  if(tabType === 'ai' || cat.includes('ai') || cats.includes('ai') || title.includes('ai') || currentTab === 'ai' || (trendCategory === 'ai' && (currentTab === 'trend' || currentTab === 'ai'))){
    return 'ai';
  }
  if(tabType === 'comic' || cat.includes('漫剧') || cats.includes('漫剧') || (trendCategory === 'comic' && currentTab === 'trend')){
    return 'comic';
  }
  if(tabType === 'human' || cat.includes('真人') || cat.includes('都市') || cat.includes('爱情') || currentTab === 'human' || (trendCategory === 'human' && (currentTab === 'trend' || currentTab === 'human'))){
    return 'human';
  }
  return '';
}

let currentDateSort = "none"; // 'none', 'asc', 'desc'
let currentExplorerItems = [];
let lastSearchResults = [];

function applyDateSort(list){
  if(!list || !list.length) return [];
  if(currentDateSort === "none") return [...list];
  return [...list].sort((a, b) => {
    const tA = getDramaTimestamp(a);
    const tB = getDramaTimestamp(b);
    if(tA === 0 && tB === 0) return 0;
    if(tA === 0) return 1;
    if(tB === 0) return -1;
    if(currentDateSort === "asc"){
      return tA - tB; // ពីមុន មក បច្ចុប្បន្ន (ចាស់ ទៅ ថ្មី)
    } else {
      return tB - tA; // ពីថ្មី ទៅ ចាស់ (ថ្មីបំផុត)
    }
  });
}

function onDateSortChange(newSort){
  currentDateSort = newSort;
  const ind = $("#dateSortIndicator");
  if(ind){
    if(newSort === "asc"){
      ind.innerHTML = "✅ បានតម្រៀបតាមថ្ងៃ៖ <b>ពីមុន មក បច្ចុប្បន្ន (ចាស់ → ថ្មី)</b>";
      ind.style.color = "var(--accent)";
    } else if(newSort === "desc"){
      ind.innerHTML = "✅ បានតម្រៀបតាមថ្ងៃ៖ <b>ពីថ្មី ទៅ ចាស់ (ថ្មីបំផុត)</b>";
      ind.style.color = "var(--accent)";
    } else {
      ind.innerHTML = "💡 ចុចជ្រើសរើសដើម្បីតម្រៀបថ្ងៃនីមួយៗ ពីមុនមកបច្ចុប្បន្ន ឬពីថ្មីទៅចាស់";
      ind.style.color = "var(--muted)";
    }
  }
  if(currentTab === "livedata"){
    renderLiveDramas();
  } else if(currentTab === "explorer"){
    if(currentExplorerItems && currentExplorerItems.length){
      const box = $("#results");
      box.innerHTML = resultCards(applyDateSort(currentExplorerItems), true);
      syncResultButtons();
    }
  } else if(currentTab === "search"){
    if(lastSearchResults && lastSearchResults.length){
      const box = $("#results");
      box.innerHTML = resultCards(applyDateSort(lastSearchResults));
      syncResultButtons();
    }
  } else {
    renderTrending();
  }
}

function resultCards(res, raw, startRank){
  const libMap = getLibMap();
  return res.map((x,idx)=>{
    const sid = String(x.series_id || '');
    const libEntry = libMap[sid] || (x.title ? libMap[x.title.trim()] : null);
    const isDownloaded = !!(libEntry && (libEntry.local > 0 || libEntry.completed));
    const isComplete = isDownloaded && (libEntry.completed || (libEntry.total > 0 && libEntry.local >= libEntry.total));
    const isHistoryOnly = isDownloaded && libEntry.historyOnly;
    const kmTitle = x.title_km || (libEntry ? libEntry.title_km : '') || (x.title ? getCachedTrans(x.title) : '') || '';
    const on = !!cart[x.series_id];
    const rkVal = (typeof startRank==='number') ? (startRank+idx) : (idx+1);
    const rk = (typeof startRank==='number') ? `<span class="rankno${(startRank+idx)<=3?' top':''}">${startRank+idx}</span>` : '';
    
    let dlBadge = '';
    if(isDownloaded){
      if(isHistoryOnly){
        dlBadge = `<span class="dl-badge partial ${rk?'with-rk':''}" title="Previously downloaded and remembered in history: ${libEntry.local} episodes">💾 ធ្លាប់ទាញយក</span>`;
      } else {
        dlBadge = `<span class="dl-badge ${isComplete?'complete':'partial'} ${rk?'with-rk':''}" title="In current Library: ${libEntry.local} of ${libEntry.total||libEntry.local} episodes">${isComplete?'✅ បានទាញយក':`⏳ ${libEntry.local}/${libEntry.total}`}</span>`;
      }
    }

    const dateStr = formatDramaDate(x);
    const dateBadge = dateStr ? `<span class="poster-date-badge" title="កាលបរិច្ឆេទចេញផ្សាយ: ${dateStr}">📅 ${dateStr}</span>` : '';

    return `<div class="poster ${isDownloaded?'is-downloaded':''}" data-id="${x.series_id}" data-t="${esc(x.title)}" data-tkm="${esc(kmTitle)}" data-n="${x.episode_cnt||0}" data-cov="${esc(x.cover||'')}" data-sc="${esc(x.score||'')}" data-rk="${rkVal}" data-dt="${esc(dateStr||x.created_at||'')}" data-dl="${isDownloaded?'1':'0'}" aria-pressed="${on}">
      <div class="art">${posterArt(x,true,raw)}<div class="scrim"></div>
        ${rk}
        ${dlBadge}
        ${dateBadge}
        ${x.score?`<span class="score">★ ${esc(x.score)}</span>`:''}
        <div class="eps">
          <span>${x.episode_cnt ? (x.episode_cnt + ' ភាគ') : ''}</span>
        </div>
      </div>
      <div class="ttl" title="${esc(x.title)}">${esc(x.title)}</div>
      <div class="posteractions">
        <button type="button" class="btn-p-dl ${on?'in-queue':''}" data-pdl="${x.series_id}" title="${on?'ចុចដើម្បីដកចេញពី Queue':'ទាញយកចូល Queue list'}">
          ${on ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><polyline points="20 6 9 17 4 12"></polyline></svg><span>✓ ក្នុង Queue</span>`
               : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg><span>ទាញយក</span>`}
        </button>
      </div>
    </div>`;
  }).join("");
}

/* populate the main page with a live "Trending" row on open (real posters, no login) */
function trendRows(){ const g=$("#results"); if(!g) return 12; const cols=getComputedStyle(g).gridTemplateColumns.split(" ").filter(x=>x&&x!=="0px").length; return Math.max(1,cols)*2; }
let trendData=[], trendBoard="new", trendCategory="all", trendExpanded=true, trendPage=1, trendHasMore=false, trendOffsets={1:0}, trendLoading=false;
let currentTab = (location.hash==='#catalog' || location.hash==='#explorer') ? 'explorer' : (location.hash==='#human' ? 'human' : (location.hash==='#ai' ? 'ai' : (location.hash==='#livedata' ? 'livedata' : 'trend')));
let trendSeq = 0;

async function loadTrending(board, page, force=false){
  if(DEMO || ALLOW_DEMO) return;
  const seq = ++trendSeq;
  if(trendCategory === "human") currentTab = "human";
  else if(trendCategory === "ai") currentTab = "ai";
  else currentTab = "trend";
  const boardChanged = !!board && board!==trendBoard;
  if(board) trendBoard=board;
  // NEVER reset trendPage to 1 when refreshing or loading unless board explicitly changed!
  if(boardChanged){ trendPage=1; trendOffsets={1:0}; }
  if(page && typeof page === 'number' && page >= 1) trendPage=page;
  
  const sec=$("#resultsSec"), box=$("#results");
  sec.hidden=false; if($("#dramaDetailSec")) $("#dramaDetailSec").hidden=true;
  if(trendCategory === "human"){
    $("#resLabel").textContent="👤 រឿងមនុស្សពិតសម្តែង (Live-Action)";
  } else if(trendCategory === "ai"){
    $("#resLabel").textContent="🤖 រឿង AI (AI Series Dramas)";
  } else {
    $("#resLabel").textContent="🏆 Leaderboard";
  }
  $("#boardTabs").hidden=false; $("#backHome").hidden=true; $("#explorerPager").hidden=true; $("#explorerControls").hidden=true; $("#resCount").textContent="";
  $("#trendCats").hidden=false;
  if($("#liveCats")) $("#liveCats").hidden=true;
  document.querySelectorAll("#boardTabs .tab").forEach(t=>{
    if(currentTab === "human") t.classList.toggle("on", t.dataset.board==="human");
    else if(currentTab === "ai") t.classList.toggle("on", t.dataset.board==="ai");
    else t.classList.toggle("on", t.dataset.board==="trend");
  });
  document.querySelectorAll("#trendCats .exchip").forEach(c=>c.classList.toggle("on", c.dataset.cat===trendCategory));
  
  if(force) box.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="sm">Loading fresh dramas from Hongguo…</div></div>';
  
  const off = (trendPage - 1) * 100;
  trendLoading=true;
  try{
    const refParam = force ? "&refresh=1" : "";
    const j = await (await fetch(`/dl/rank?board=${encodeURIComponent(trendBoard)}&category=${encodeURIComponent(trendCategory)}&offset=${off}&size=100${refParam}`,{cache:"no-store"})).json();
    if(seq !== trendSeq || (currentTab !== "trend" && currentTab !== "human" && currentTab !== "ai")) return;
    trendData = j.results||[];
    trendHasMore = !!j.has_more;
    trendLoading = false;
    
    if(!trendData.length && trendPage===1){
      sec.hidden=false;
      box.innerHTML='<div class="empty" style="grid-column:1/-1;padding:32px"><div class="big">No dramas returned from leaderboard</div><div class="sm" style="margin-top:8px"><button class="btn primary sm" onclick="loadTrending(null,1,true)">🔄 Reload Leaderboard</button></div></div>';
      return;
    }
    sec.hidden=false;
    renderTrending();
  }catch(e){
    if(seq !== trendSeq || (currentTab !== "trend" && currentTab !== "human" && currentTab !== "ai")) return;
    trendLoading=false;
    sec.hidden=false;
    box.innerHTML='<div class="empty" style="grid-column:1/-1;padding:32px"><div class="big">Connecting to drama catalog…</div><div class="sm" style="margin-top:8px"><button class="btn primary sm" onclick="loadTrending(null,trendPage,true)">🔄 Retry Loading Dramas</button></div></div>';
  }
}

function goToTrendPage(targetPage){
  const p = parseInt(targetPage, 10);
  if(!p || p < 1) return;
  trendPage = p;
  trendExpanded = true;
  loadTrending(null, p).then(trendTop);
}

function renderTrending(){
  if(currentTab !== "trend" && currentTab !== "human" && currentTab !== "ai") return;
  const box=$("#results");
  const displayList = applyDateSort(trendData);
  if(!trendExpanded){
    box.innerHTML = resultCards(displayList.slice(0, trendRows()), false, 1);
    $("#resCount").textContent = "";
  } else {
    const sortNote = currentDateSort === 'asc' ? ' (📅 ពីមុនមកបច្ចុប្បន្ន)' : (currentDateSort === 'desc' ? ' (📅 ពីថ្មីទៅចាស់)' : '');
    box.innerHTML = resultCards(displayList, false, (trendPage-1)*100+1)
      + `<div class="trend-bottom" style="grid-column:1/-1;display:flex;justify-content:center;padding:6px 0 2px"><button class="btn ghost sm" id="trendCollapseB">↑ Collapse</button></div>`;
    $("#resCount").textContent = "· page "+trendPage + sortNote;
    const cb=$("#trendCollapseB"); if(cb) cb.onclick=collapseTrend;
  }
  renderTrendControls();
  syncResultButtons();
  autoTranslateCatalog(trendData);
}

/* ============ Circular Centered Pagination (ស្ទាយរង្វង់មូលចំកណ្តាល ដូចរូបថត) ============ */
function renderCircularPagination(container, curPage, totalPages, onPageClick){
  if(!container) return;
  curPage = Math.max(1, parseInt(curPage, 10) || 1);
  totalPages = Math.max(1, parseInt(totalPages, 10) || 1);
  if(totalPages <= 1){
    container.innerHTML = '';
    container.hidden = true;
    return;
  }
  container.hidden = false;

  let pages = [];
  if(totalPages <= 7){
    for(let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    if(curPage <= 3){
      pages = [1, 2, 3, 4, '...', totalPages];
    } else if(curPage === 4){
      pages = [1, 2, 3, 4, 5, '...', totalPages];
    } else if(curPage >= totalPages - 2){
      pages = [1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    } else if(curPage === totalPages - 3){
      pages = [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    } else {
      pages = [1, '...', curPage - 1, curPage, curPage + 1, '...', totalPages];
    }
  }

  let html = `<div class="circle-pager">`;
  const prevDisabled = curPage <= 1 ? 'disabled' : '';
  html += `<button type="button" class="circle-page-btn nav-btn" data-page="${curPage - 1}" ${prevDisabled} title="Previous Page">‹</button>`;

  for(const p of pages){
    if(p === '...'){
      html += `<span class="circle-page-dots" title="Jump to page (ចុចដើម្បីរំលងទំព័រ)">…</span>`;
    } else {
      const isActive = p === curPage ? 'active' : '';
      html += `<button type="button" class="circle-page-btn ${isActive}" data-page="${p}">${p}</button>`;
    }
  }

  const nextDisabled = curPage >= totalPages ? 'disabled' : '';
  html += `<button type="button" class="circle-page-btn nav-btn" data-page="${curPage + 1}" ${nextDisabled} title="Next Page">›</button>`;
  html += `</div>`;

  container.innerHTML = html;

  container.querySelectorAll(".circle-page-btn").forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      const pg = parseInt(btn.dataset.page, 10);
      if(pg && pg >= 1 && pg <= totalPages && pg !== curPage){
        onPageClick(pg);
      }
    };
  });

  container.querySelectorAll(".circle-page-dots").forEach(dot => {
    dot.onclick = (e) => {
      e.preventDefault();
      const input = prompt(`បញ្ចូលលេខទំព័រដែលចង់ទៅ (1 - ${totalPages}):`, curPage);
      if(input){
        const pg = parseInt(input.trim(), 10);
        if(pg && pg >= 1 && pg <= totalPages && pg !== curPage){
          onPageClick(pg);
        }
      }
    };
  });
}

function renderTrendControls(){
  const row=$("#moreRow");
  row.hidden=false;
  row.classList.add("trendctl-sticky");
  const estTotalPages = trendHasMore ? Math.max(trendPage + 5, 20) : trendPage;
  renderCircularPagination(row, trendPage, estTotalPages, (pg) => goToTrendPage(pg));
}

function trendTop(){ try{ $("#resultsSec").scrollIntoView({block:"start"}); }catch(e){} }
function collapseTrend(){
  trendExpanded=false;
  renderTrending();
  trendTop();
}

/* Explorer: the full ~20k verified catalogue, served from the Cloudflare Worker (D1 + covers).
   Paged, with genre tabs / in-catalogue search / sort / status filter. */
const EXPLORER_API = "https://hongguo-explorer.aly201514.workers.dev";
let expPage=1, expPages=1;   // Catalog shows a fixed 100 cards per page (rows selector removed)
let exGenre="", exSort="popular", exStatus="", exQ="", exGenresLoaded=false, exSeq=0;
const GENRE_TRANSLATIONS = {
  "All": { km: "ទាំងអស់", en: "All" },
  "Animated": { km: "គំនូរជីវចល", en: "Animated" },
  "AI": { km: "រឿង AI", en: "AI" },
  "Urban": { km: "ទីក្រុងសម័យ", en: "Urban" },
  "Modern": { km: "សម័យទំនើប", en: "Modern" },
  "Underdog": { km: "តស៊ូជីវិត", en: "Underdog" },
  "Male Lead": { km: "តួឯកប្រុស", en: "Male Lead" },
  "Romance": { km: "មនោសញ្ចេតនា", en: "Romance" },
  "Historical": { km: "បុរាណសម័យ", en: "Historical" },
  "CEO": { km: "អគ្គនាយក", en: "CEO" },
  "Time Travel": { km: "ឆ្លងភព", en: "Time Travel" },
  "Payback": { km: "ការសងសឹក", en: "Payback" },
  "Urban Romance": { km: "ស្នេហាក្នុងក្រុង", en: "Urban Romance" },
  "Slow Burn": { km: "ស្នេហាផ្អែមល្ហែម", en: "Slow Burn" },
  "System": { km: "ប្រព័ន្ធវេទមន្ត", en: "System" },
  "Rags to Riches": { km: "ពីក្រទៅមាន", en: "Rags to Riches" },
  "Plot": { km: "សាច់រឿងជក់ចិត្ត", en: "Plot" },
  "Female Growth": { km: "ការវិវត្តតួស្រី", en: "Female Growth" },
  "Female Lead": { km: "តួឯកស្រី", en: "Female Lead" },
  "Urban Fantasy": { km: "អភូតហេតុទីក្រុង", en: "Urban Fantasy" },
  "Rural": { km: "ជនបទស្រុកស្រែ", en: "Rural" },
  "Truth Revealed": { km: "លាតត្រដាងការពិត", en: "Truth Revealed" },
  "Coming of Age": { km: "វ័យជំទង់", en: "Coming of Age" },
  "Love": { km: "សេចក្តីស្រឡាញ់", en: "Love" },
  "Rebirth": { km: "ចាប់ជាតិថ្មី", en: "Rebirth" },
  "Conspiracy": { km: "ល្បិចកលក្បត់", en: "Conspiracy" },
  "3D": { km: "រឿង 3D", en: "3D Animation" },
  "Action": { km: "វាយប្រហារ", en: "Action" },
  "Suspense": { km: "អាថ៌កំបាំង", en: "Suspense" },
  "Comedy": { km: "កំប្លែង", en: "Comedy" },
  "Live-action": { km: "មនុស្សពិតសម្តែង", en: "Live-action" },
  "年代": { km: "សម័យកាល", en: "Period Era" },
  "都市日常": { km: "ជីវិតប្រចាំថ្ងៃ", en: "Daily Life" },
  "女强": { km: "ស្រីរឹងមាំ", en: "Strong Female" },
  "奇幻脑洞": { km: "ស្រមើស្រមៃចម្លែក", en: "Fantasy Twist" },
  "情感觉醒": { km: "ភ្ញាក់រលឹកចិត្ត", en: "Emotional Wake" },
  "架空": { km: "ភពស្រមើស្រមៃ", en: "Alt Universe" },
  "先婚后爱": { km: "ការសិនស្នេហ៍ក្រោយ", en: "Married First" },
  "反转": { km: "បត់បែនភ្ញាក់ផ្អើល", en: "Plot Twist" },
  "异界": { km: "ពិភពដទៃ", en: "Otherworld" },
  "异能": { km: "សមត្ថភាពពិសេស", en: "Superpowers" },
  "脑洞": { km: "គំនិតច្នៃប្រឌិត", en: "Wild Ideas" },
  "忠诚男主": { km: "តួប្រុសស្មោះស្ម័គ្រ", en: "Loyal Hero" },
  "玄幻": { km: "ទេវកថាចិន", en: "High Fantasy" },
  "古风": { km: "រចនាបថបុរាណ", en: "Ancient Style" },
  "虐渣": { km: "ផ្តន្ទាទោសមនុស្សអាក្រក់", en: "Scum Bashing" },
  "豪门": { km: "គ្រួសារអភិជន", en: "Tycoon Family" },
  "奇幻爱情": { km: "ស្នេហាមន្តអាគម", en: "Fantasy Romance" },
  "古装": { km: "បុរាណចិន", en: "Costume Drama" },
  "马甲文": { km: "លាក់អត្តសញ្ញាណ", en: "Secret Identity" },
  "种田": { km: "កសិកម្មជីវិតសាមញ្ញ", en: "Farming Life" },
  "家庭": { km: "គ្រួសារ", en: "Family Life" },
  "隐藏大佬": { km: "កំពូលអ្នកលាក់មុខ", en: "Hidden Boss" },
  "重生逆袭": { km: "ចាប់ជាតិសងសឹក", en: "Rebirth Payback" },
  "穿书": { km: "ធ្លាក់ចូលក្នុងសៀវភៅ", en: "Transmigration" },
  "Drama": { km: "រឿងភាគ", en: "Drama" },
  "Fantasy": { km: "ស្រមើស្រមៃ", en: "Fantasy" },
  "Thriller": { km: "រន្ធត់ញាប់ញ័រ", en: "Thriller" },
  "Family": { km: "គ្រួសារ", en: "Family" },
  "Mystery": { km: "អាថ៌កំបាំង", en: "Mystery" },
  "Youth": { km: "យុវវ័យ", en: "Youth" },
  "Campus": { km: "សាលារៀន", en: "Campus" },
  "School": { km: "សាលារៀន", en: "School" },
  "Sweet": { km: "ស្នេហាផ្អែមល្ហែម", en: "Sweet Romance" },
  "Revenge": { km: "ការសងសឹក", en: "Revenge" },
  "Martial Arts": { km: "ក្បាច់គុន", en: "Martial Arts" },
  "Wuxia": { km: "យុទ្ធសិល្ប៍", en: "Wuxia" },
  "Sci-Fi": { km: "វិទ្យាសាស្ត្រ", en: "Sci-Fi" },
  "Adventure": { km: "ផ្សងព្រេង", en: "Adventure" },
  "Crime": { km: "ឧក្រិដ្ឋកម្ម", en: "Crime" },
  "Magic": { km: "មន្តអាគម", en: "Magic" }
};

function getGenreInfo(raw) {
  if (!raw) return { km: "ទាំងអស់", en: "All" };
  const found = GENRE_TRANSLATIONS[raw];
  if (found) return found;
  return { km: raw, en: raw };
}

function renderGenreChipHtml(genreName, isSelected) {
  const info = getGenreInfo(genreName || "All");
  const onClass = isSelected ? " on" : "";
  const val = genreName || "";
  const km = info.km || (genreName ? genreName : "ទាំងអស់");
  const en = info.en || (genreName ? genreName : "All");
  return `<button class="exchip${onClass}" data-g="${esc(val)}" title="${esc(km)} · ${esc(en)}"><span class="km-label">${esc(km)}</span><span class="en-sub">${esc(en)}</span></button>`;
}

const DEFAULT_CATALOG_GENRES = [
  "Animated", "AI", "Urban", "Modern", "Underdog", "Male Lead", "Romance", 
  "Historical", "CEO", "Time Travel", "Payback", "Urban Romance", "Slow Burn", 
  "System", "Rags to Riches", "Plot", "Female Growth", "Female Lead", 
  "Urban Fantasy", "Rural", "Truth Revealed", "Coming of Age", "Love"
];

function renderGenresList(list){
  const chips = list.map(g => renderGenreChipHtml(g, g === exGenre)).join("");
  $("#exGenres").innerHTML = renderGenreChipHtml("", !exGenre) + chips;
  $("#exGenres").querySelectorAll(".exchip").forEach(c=>{
    c.onclick=()=>{
      exGenre=c.dataset.g;
      // When user clicks any genre category, clear any stray search text like 'ADMIN'
      if(exQ){
        exQ = "";
        if($("#exQ")) $("#exQ").value = "";
        if($("#exQClear")) $("#exQClear").style.display = "none";
      }
      $("#exGenres").querySelectorAll(".exchip").forEach(x=>x.classList.toggle("on", x===c));
      loadExplorer(1);
    };
  });
}

async function ensureGenres(){
  if(!exGenresLoaded){
    renderGenresList(DEFAULT_CATALOG_GENRES);
  }
  if(exGenresLoaded) return; exGenresLoaded=true;
  try{
    const j = await (await fetch(EXPLORER_API+"/genres?limit=30", {cache:"no-store"})).json();
    const list = (j.genres||[]).map(x=>x.genre).filter(g => g && !g.includes("?") && /^[a-zA-Z0-9\s]+$/.test(g));
    if(list.length >= 10){
      renderGenresList(list);
    }
  }catch(e){ }
}
async function loadExplorer(page){
  if(DEMO || ALLOW_DEMO) return;
  currentTab = "explorer";
  const seq=++exSeq;
  const sec=$("#resultsSec"), box=$("#results");
  const hero=document.querySelector(".hero"); if(hero) hero.hidden=true;
  sec.hidden=false; if($("#dramaDetailSec")) $("#dramaDetailSec").hidden=true; $("#resLabel").textContent="🎬 Catalog"; $("#boardTabs").hidden=false; $("#backHome").hidden=true; $("#moreRow").hidden=true; $("#trendCats").hidden=true;
  $("#explorerControls").hidden=false;
  document.querySelectorAll("#boardTabs .tab").forEach(t=>t.classList.toggle("on", t.dataset.board==="explorer"));
  ensureGenres();
  box.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="sm" style="font-family:\'Khmer OS Battambang\',sans-serif">កំពុងទាញយកទិន្នន័យកាតាឡុក (Loading catalogue)…</div></div>';
  try{
    // Auto-clean: if exQ accidentally contains 'admin' or 'ADMIN', discard it!
    if(exQ && exQ.trim().toLowerCase() === 'admin'){
      exQ = "";
      if($("#exQ")) $("#exQ").value = "";
      if($("#exQClear")) $("#exQClear").style.display = "none";
    }
    const p = new URLSearchParams({ page:page||1, size:100, sort:exSort });
    if(exGenre) p.set("genre", exGenre);
    if(exStatus) p.set("status", exStatus);
    if(exQ) p.set("q", exQ);
    const j = await (await fetch(EXPLORER_API+"/explorer?"+p.toString(), {cache:"no-store"})).json();   // fresh (catalog grows weekly; avoids stale browser cache)
    if(seq!==exSeq || currentTab !== "explorer") return;   // a newer request superseded this one — drop the stale result
    const res=j.items||[];
    if(!(j.count>0)){
      $("#explorerPager").hidden=true; $("#resCount").textContent="· 0";
      const hasQ = !!(exQ && exQ.trim());
      box.innerHTML=`<div class="empty" style="grid-column:1/-1">
        <div class="big" style="font-family:'Khmer OS Battambang',sans-serif">រកមិនឃើញទិន្នន័យ (No matches)</div>
        <div class="sm" style="font-family:'Khmer OS Battambang',sans-serif">
          ${hasQ ? `ដោយសារមានពាក្យស្វែងរក <b style="color:var(--accent)">"${esc(exQ)}"</b> ក្នុងប្រអប់ស្វែងរក។` : 'សូមសាកល្បងជ្រើសរើសប្រភេទរឿង ឬពាក្យស្វែងរកផ្សេងទៀត។'}
        </div>
        ${hasQ ? `<button class="btn primary sm" id="clearExQBtn" style="margin-top:14px;border-radius:20px;font-weight:700">🔄 សម្អាតពាក្យស្វែងរក "${esc(exQ)}" ដើម្បីបង្ហាញរឿងទាំងអស់</button>` : ''}
      </div>`;
      if(hasQ && $("#clearExQBtn")){
        $("#clearExQBtn").onclick = () => {
          exQ = "";
          if($("#exQ")) $("#exQ").value = "";
          if($("#exQClear")) $("#exQClear").style.display = "none";
          loadExplorer(1);
        };
      }
      return;
    }
    expPage=j.page; expPages=j.pages;
    currentExplorerItems = res;
    box.innerHTML = resultCards(applyDateSort(res), true); syncResultButtons();
    autoTranslateCatalog(res);
    $("#resCount").textContent = "· "+j.count;
    renderCircularPagination($("#explorerPager"), j.page, j.pages, (pg) => loadExplorer(pg));
  }catch(e){
    if(seq!==exSeq || currentTab !== "explorer") return;
    try{
      const fb = await (await fetch("/dl/rank?board=recommend&size=100", {cache:"no-store"})).json();
      if(fb && fb.results && fb.results.length > 0 && currentTab === "explorer"){
        const res = fb.results;
        currentExplorerItems = res;
        box.innerHTML = resultCards(applyDateSort(res), false); syncResultButtons();
        autoTranslateCatalog(res);
        $("#resCount").textContent = "· " + res.length;
        return;
      }
    }catch(err2){}
    $("#explorerPager").hidden=true;
    box.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="big" style="font-family:\'Khmer OS Battambang\',sans-serif">មិនអាចភ្ជាប់ទៅកាន់កាតាឡុកបានទេ</div><div class="sm" style="font-family:\'Khmer OS Battambang\',sans-serif">សូមពិនិត្យមើលការភ្ជាប់អ៊ីនធឺណិតរបស់អ្នក។</div></div>';
  }
}

async function doSearch(q){
  currentTab = "search";
  const sec=$("#resultsSec"), box=$("#results");
  sec.hidden=false; if($("#dramaDetailSec")) $("#dramaDetailSec").hidden=true; $("#resLabel").textContent="លទ្ធផលស្វែងរក"; $("#resCount").textContent=""; $("#boardTabs").hidden=true; $("#backHome").hidden=false; $("#moreRow").hidden=true; $("#trendCats").hidden=true; $("#explorerPager").hidden=true; $("#explorerControls").hidden=true;
  box.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="sm">កំពុងស្វែងរក “'+esc(q)+'”…</div></div>';
  try{
    const j = DEMO ? demoSearch(q) : await (await fetch("/dl/search?q="+encodeURIComponent(q))).json();
    if(currentTab !== "search") return;
    const res=j.results||[];
    lastSearchResults = res;
    $("#resCount").textContent = res.length?("· "+res.length):"";
    if(!res.length){ box.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="big">រកមិនឃើញរឿងនេះទេ</div><div class="sm">'+(j.error?esc(j.error):'សូមសាកល្បងបញ្ចូលចំណងជើងរឿងផ្សេងទៀត ឬបិទភ្ជាប់តំណរឿង។')+'</div></div>'; return; }
    box.innerHTML = resultCards(applyDateSort(res)); syncResultButtons();
    autoTranslateCatalog(res);
  }catch(e){
    if(currentTab !== "search") return;
    box.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="big">មិនអាចស្វែងរកបានទេ</div><div class="sm">សូមពិនិត្យមើលថាតើ Signer និង Server កំពុងដំណើរការដែរឬទេ? '+esc(""+e)+'</div></div>';
  }
}

/* ---------- resolve pasted links ---------- */
async function addLinks(text){
  const go=$("#omniGo"); go.disabled=true; go.innerHTML="<span>កំពុងស្វែងរក…</span>";
  try{
    const j = DEMO ? demoResolve(text) : await (await fetch("/dl/resolve",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})})).json();
    let ok=0, bad=[], unavail=[];
    (j.resolved||[]).forEach(x=>{
      if(x.series_id){ addToCart(x.series_id,x.title,x.total,x.cover,true); ok++; }
      else if(x.unavailable){ addUnavailCard(x.hg_id||x.title, x.title); unavail.push(x.title||"?"); }  // #4: toast + a dismissible 🚫 card
      else bad.push(x.title||"?");
    });
    if(ok||unavail.length){ renderQueue(); saveCart(); syncResultButtons(); openSideQueue(); }           // working links + 下架 cards appear in the queue
    if(ok||unavail.length){ $("#omni").value=""; $("#omniMode").textContent="ស្វែងរក"; $("#omniMode").classList.remove("link"); }
    if(unavail.length) toast(`⚠️ 《${unavail[0]}》 មិនមាននៅលើ Platform ទៀតទេ`+(unavail.length>1?` (+${unavail.length-1} more)`:''), true);
    else toast(ok?`បានបន្ថែម ${ok} ចូលក្នុងបញ្ជីទាញយក`+(bad.length?`, ${bad.length} មិនអាចទាញយកបាន`:""):"មិនអាចដំណើរការតំណភ្ជាប់នេះបានទេ", !ok);
  }catch(e){ toast("ការដោះស្រាយតំណភ្ជាប់បានបរាជ័យ: "+e, true); }
  go.disabled=false; go.innerHTML="<span>🔍 ស្វែងរក</span>";
}

/* ---------- right-side queue drawer functions ---------- */
function openSideQueue(){
  const drawer = $("#sideQueueDrawer");
  const backdrop = $("#sideQueueBackdrop");
  if(drawer){
    drawer.classList.add("open");
    drawer.setAttribute("aria-hidden", "false");
  }
  document.body.classList.add("queue-drawer-open");
  if(backdrop && window.innerWidth < 900){
    backdrop.classList.add("show");
  } else if(backdrop){
    backdrop.classList.remove("show");
  }
  updateSideQueueFloat();
}
function closeSideQueue(){
  const drawer = $("#sideQueueDrawer");
  const backdrop = $("#sideQueueBackdrop");
  if(drawer){
    drawer.classList.remove("open");
    drawer.setAttribute("aria-hidden", "true");
  }
  document.body.classList.remove("queue-drawer-open");
  if(backdrop){
    backdrop.classList.remove("show");
  }
  updateSideQueueFloat();
}
function toggleSideQueue(){
  const drawer = $("#sideQueueDrawer");
  if(drawer && drawer.classList.contains("open")){
    closeSideQueue();
  } else {
    openSideQueue();
  }
}
function updateSideQueueFloat(){
  const allIds = Object.keys(cart).filter(id=>!(cart[id]&&cart[id].unavailable));
  const flt = $("#sideQueueFloatBtn");
  const fltCnt = $("#sideQueueFloatCount");
  if(flt && fltCnt){
    fltCnt.textContent = allIds.length;
    flt.hidden = (allIds.length === 0);
  }
}

/* ---------- cart ---------- */
function addToCart(id,title,total,cover,defer,score,rank,dt,title_km){
  if(!id) return;
  const resolvedKm = title_km || getCachedTrans(title) || "";
  cart[id]={
    title: title||id,
    title_km: resolvedKm,
    total: total||0,
    cover: cover||"",
    score: score||"",
    rank: rank||0,
    dt: dt||"",
    checked: true
  };
  if(!defer){
    saveCart();
    renderQueue();
    syncResultButtons();
    openSideQueue();
  }
}
function addUnavailCard(key,title){ if(!key) key="x"+Date.now(); cart[key]={title:title||"?",total:0,unavailable:true,checked:false}; }
function removeFromCart(id){ delete cart[id]; saveCart(); renderQueue(); syncResultButtons(); }
function syncResultButtons(){
  document.querySelectorAll(".poster").forEach(p=>{
    const on = !!cart[p.dataset.id];
    const isDl = p.dataset.dl === '1';
    p.setAttribute("aria-pressed", on);
    const c = p.querySelector(".check");
    if(c){
      c.textContent = on ? '✓' : (isDl ? '✅' : '+');
      c.classList.toggle("dl-chk", isDl && !on);
    }
    const dlBtn = p.querySelector(".btn-p-dl");
    if(dlBtn){
      dlBtn.classList.toggle("in-queue", on);
      dlBtn.innerHTML = on 
        ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><polyline points="20 6 9 17 4 12"></polyline></svg><span>✓ ក្នុង Queue</span>`
        : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg><span>ទាញយក</span>`;
      dlBtn.title = on ? 'ចុចដើម្បីដកចេញពី Queue' : 'ទាញយកចូល Queue list';
    }
  });
}

/* ---------- queue render ---------- */
function renderQueue(){
  let cartDirty = false;
  const smap={}; (lastStatus.series||[]).forEach(s=>smap[s.sid]=s);
  const libMap = getLibMap();
  const ids=Object.keys(cart);
  const qc = $("#queueCount"); if(qc) qc.textContent=ids.length;
  updateSideQueueFloat();
  const el=$("#queue");
  if(!ids.length){
    if(el) el.innerHTML='<div class="empty sq-empty"><div class="big">គ្មានរឿងក្នុង Queue ទេ</div><div class="sm">ចុចលើ Poster ឬប៊ូតុងទាញយកដើម្បីបន្ថែមរឿងចូលក្នុង Queue</div></div>';
    updateDock();
    return;
  }

  // Smooth in-place updates: if the rows in the DOM already match cart keys, update only dynamic data
  // to avoid screen flicker/jitter ("ញាក់") during downloads:
  const existingRows = el.querySelectorAll(".row[data-qid]");
  if(existingRows.length === ids.length){
    let allMatch = true;
    for(let i=0; i<ids.length; i++){
      if(existingRows[i].dataset.qid !== ids[i]){ allMatch = false; break; }
    }
    if(allMatch){
      ids.forEach(id=>{
        const row = el.querySelector(`.row[data-qid="${id}"]`);
        if(!row) return;
        const c=cart[id], s=smap[id];
        if(!c || c.unavailable) return;
        const title = (s && s.title) || c.title || '';
        const total = (s && s.total) || c.total || 0;
        const isDone = s ? (s.status === "done" || (total > 0 && s.done >= total)) : false;
        const pct = total ? Math.round((s ? s.done : 0) * 100 / total) : (isDone ? 100 : 0);
        const st = s ? (s.status || "queued") : "queued";
        const cls = isDone ? "done" : (st === "downloading" ? "downloading" : (st === "failed" ? "failed" : "queued"));
        const hasSpeed = s && (st === "downloading" || (s.done > 0 && !isDone)) && s.speed;

        // Update chip (single state: DONE, DOWNLOADING, QUEUED, etc. - NO speed badge on upper row!)
        const chipEl = row.querySelector(".chip");
        if(chipEl){
          chipEl.className = `chip ${cls}`;
          chipEl.textContent = isDone ? "DONE" : (st === "downloading" ? "DOWNLOADING" : st.toUpperCase());
        }

        // Update or insert Khmer title
        const kmTitle = c.title_km || (s && s.title_km) || (title ? getCachedTrans(title) : '') || (dlHistory[id] && dlHistory[id].title_km) || '';
        if(!c.title_km && kmTitle){ c.title_km = kmTitle; cartDirty = true; }
        let rttlKm = row.querySelector(".rttl-km");
        if(kmTitle){
          if(rttlKm){
            rttlKm.textContent = `🇰🇭 ${kmTitle}`;
          } else {
            const r1 = row.querySelector(".r1");
            if(r1){
              rttlKm = document.createElement("div");
              rttlKm.className = "rttl-km";
              rttlKm.style.cssText = "font-size:11.5px;font-weight:600;color:var(--accent);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
              rttlKm.textContent = `🇰🇭 ${kmTitle}`;
              r1.insertAdjacentElement("afterend", rttlKm);
            }
          }
        }

        // Update rmeta (single clean speed display: x/y episodes · pct% · ⚡ speed)
        const rmetaEl = row.querySelector(".rmeta");
        if(rmetaEl){
          if(s){
            rmetaEl.innerHTML = `${s.done}/${total || "?"} episodes · ${pct}%${hasSpeed ? ` · <b style="color:var(--accent);font-family:var(--font-mono)">⚡ ${esc(s.speed)}</b>` : ''}`;
          } else {
            const partial = c.sel && c.sel.length && total && c.sel.length < total;
            rmetaEl.innerHTML = partial ? `<b>${c.sel.length}</b> of ${total} episodes` : `${total || "?"} episodes`;
          }
        }

        // Update or insert progress track - ALWAYS visible!
        let track = row.querySelector(".track");
        if(!track){
          const body = row.querySelector(".body");
          const actions = row.querySelector(".q-actions");
          track = document.createElement("div");
          track.className = "track";
          track.innerHTML = `<div class="fill ${isDone ? 'done' : ''} ${cls === 'downloading' ? 'live' : ''}" style="width:${pct}%"></div>`;
          if(actions && body){
            body.insertBefore(track, actions);
          } else if(body){
            body.appendChild(track);
          }
        } else {
          const trackFill = track.querySelector(".fill");
          if(trackFill){
            trackFill.style.width = pct + "%";
            trackFill.className = `fill ${isDone ? 'done' : ''} ${cls === 'downloading' ? 'live' : ''}`;
          }
        }

        // Fast-path: dynamically update q-actions to add direct PC folder open button!
        const actions = row.querySelector(".q-actions");
        if(actions){
          const hasOpen = actions.querySelector(".q-open-folder");
          if((isDone || (s && s.done > 0)) && !hasOpen){
            const sName = title || id;
            const openBtn = document.createElement("button");
            openBtn.type = "button";
            openBtn.className = "q-btn q-open-folder";
            openBtn.setAttribute("data-open-folder", sName);
            openBtn.style.cssText = "display:inline-flex;align-items:center;gap:4px;color:var(--accent,#ff9800);font-weight:700";
            openBtn.title = "បើកទីតាំង Folder នៃរឿងនេះនៅលើ PC Local";
            openBtn.innerHTML = `📁 បើកថតរឿង`;
            actions.appendChild(openBtn);
          }
        }
      });
      if(cartDirty) saveCart();
      updateDock();
      return;
    }
  }

  cartDirty = false;
  el.innerHTML = ids.map(id=>{
    const c=cart[id], s=smap[id];
    const title=(s&&s.title)||c.title, total=(s&&s.total)||c.total||0;
    const isTicked = c.checked !== false;
    const kmTitle = c.title_km || (s&&s.title_km) || getCachedTrans(title) || (dlHistory[id]&&dlHistory[id].title_km) || '';
    if(!c.title_km && kmTitle){ c.title_km = kmTitle; cartDirty = true; }
    
    // Resolve cover from all available sources
    let cov = c.cover || (s&&s.cover) || (libMap[id]&&libMap[id].cover) || (dlHistory[id]&&dlHistory[id].cover_url) || '';
    if(!cov){
      const libMatch = (libItems||[]).find(x => x.series_id === id || (x.title && x.title === title) || (x.name && x.name === title));
      if(libMatch && libMatch.poster) cov = `/dl/poster?name=${encodeURIComponent(libMatch.name||title)}`;
    }
    if(!c.cover && cov){
      c.cover = cov;
      cartDirty = true;
    }
    
    if(c.unavailable){
      return `<div class="row unavail ${isTicked?'':'unticked'}">
        <div class="q-tick-box"><input type="checkbox" class="q-tick" data-tick="${id}" ${isTicked?'checked':''} title="Tick to include/exclude"></div>
        <div class="thumb"><div class="grad" style="${gradFor(title)}"></div></div>
        <div class="body">
          <div class="r1">
            <span class="rttl" title="${esc(title)}">${esc(title)}</span>
            <div style="display:flex;align-items:center;gap:6px">
              <span class="chip unavail">🚫 Unavailable</span>
              <button class="q-rm" data-rm="${id}" title="Remove from queue">✕</button>
            </div>
          </div>
          <div class="rmeta">Series is no longer available on the platform</div>
        </div>
      </div>`;
    }

    const posterSrc = getPosterUrl(cov, title, id);
    const thumb = (posterSrc && !DEMO)
      ? `<img src="${esc(posterSrc)}" alt="" onerror="handlePosterError(this, '${esc(title)}', '${esc(id)}')"><div class="grad" style="${gradFor(title)}"></div>`
      : `<div class="grad" style="${gradFor(title)}"></div>`;
    
    let chip = '', meta = '', pct = 0, cls = '';
    const isDone = s ? (s.status === "done" || (total > 0 && s.done >= total)) : false;
    
    if(s){
      pct = total ? Math.round(s.done * 100 / total) : (s.status === "done" ? 100 : 0);
      const st = s.status || "queued";
      cls = isDone ? "done" : (st === "downloading" ? "downloading" : (st === "failed" ? "failed" : "queued"));
      const hasSpeed = (st === "downloading" || (s.done > 0 && !isDone)) && s.speed;
      chip = `<span class="chip ${cls}">${isDone ? 'DONE' : (st === 'downloading' ? 'DOWNLOADING' : st.toUpperCase())}</span>`;
      meta = `${s.done}/${total || "?"} episodes · ${pct}%${hasSpeed ? ` · <b style="color:var(--accent);font-family:var(--font-mono)">⚡ ${esc(s.speed)}</b>` : ''}`;
    } else {
      const partial = c.sel && c.sel.length && total && c.sel.length < total;
      pct = partial ? Math.round(c.sel.length * 100 / total) : 0;
      chip = `<span class="chip queued">QUEUED</span>`;
      meta = partial ? `<b>${c.sel.length}</b> of ${total} episodes` : `${total || "?"} episodes`;
    }
    
    return `<div class="row ${isTicked?'':'unticked'}" data-qid="${id}">
      <div class="q-tick-box">
        <input type="checkbox" class="q-tick" data-tick="${id}" ${isTicked?'checked':''} title="Tick to select this drama for download">
      </div>
      <div class="thumb">${thumb}</div>
      <div class="body">
        <div class="r1">
          <span class="rttl" title="${esc(title)}">${esc(title)}</span>
          <div style="display:flex;align-items:center;gap:8px">
            ${chip}
            <button class="q-rm" data-rm="${id}" title="Remove from queue (លុបចេញពី Queue)">✕</button>
          </div>
        </div>
        ${kmTitle ? `<div class="rttl-km" style="font-size:11.5px;font-weight:600;color:var(--accent);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">🇰🇭 ${esc(kmTitle)}</div>` : ''}
        <div class="rmeta">${meta}</div>
        <div class="track"><div class="fill ${isDone?'done':''} ${cls==='downloading'?'live':''}" style="width:${pct}%"></div></div>
        <div class="q-actions" style="display:flex;align-items:center;gap:8px;margin-top:7px;flex-wrap:wrap">
          <button class="q-btn q-redl" data-redl="${id}" title="Re-download this drama (ទាញយកម្តងទៀត)">🔄 Redownload</button>
          ${(!s || isDone) ? `<button class="q-btn" data-ep="${id}">☰ Choose episodes</button>` : ''}
          ${(s && s.done > 0) ? `
            <button type="button" class="q-btn q-open-folder" data-open-folder="${esc(title || id)}" style="display:inline-flex;align-items:center;gap:4px;color:var(--accent,#ff9800);font-weight:700" title="បើកទីតាំង Folder នៃរឿងនេះនៅលើ PC Local">
              📁 បើកថតរឿង
            </button>
          ` : ''}
        </div>
      </div>
    </div>`;
  }).join("");
  if(cartDirty) saveCart();
  updateDock();
  autoTranslateQueue();
}

function clearDoneFromQueue(){
  const smap={}; (lastStatus.series||[]).forEach(s=>smap[s.sid]=s);
  const ids = Object.keys(cart);
  let cleared = 0;
  ids.forEach(id => {
    const c = cart[id];
    const s = smap[id];
    const total = (s && s.total) || (c && c.total) || 0;
    const isDone = (s && (s.status === 'done' || (total > 0 && s.done >= total))) ||
                   (c && c.total > 0 && s && s.done >= c.total);
    if(isDone){
      delete cart[id];
      cleared++;
    }
  });
  if(cleared > 0){
    saveCart();
    renderQueue();
    syncResultButtons();
    toast(`🧹 បានលុបរឿងដែលទាញយកចប់ចំនួន ${cleared} ចេញពី Queue (រឿងមិនទាន់ចប់ត្រូវបានរក្សាទុក)`);
  } else {
    toast("មិនមានរឿងដែលទាញយកចប់ 100% សម្រាប់លុបទេ");
  }
}

function clearAllQueue(){
  const count = Object.keys(cart).length;
  if(!count){ toast("Queue is already empty"); return; }
  if(confirm("តើអ្នកពិតជាចង់លុបរឿងទាំងអស់ចេញពី Queue មែនទេ? (Clear all items from queue?)")){
    cart = {};
    saveCart();
    renderQueue();
    syncResultButtons();
    toast("🧹 Queue cleared.");
  }
}

function toggleAllTicks(){
  const ids = Object.keys(cart);
  if(!ids.length) return;
  const anyUnticked = ids.some(id => cart[id].checked === false);
  ids.forEach(id => { cart[id].checked = anyUnticked; });
  saveCart();
  renderQueue();
  toast(anyUnticked ? "☑️ បាន Tick ជ្រើសរើសទាំងអស់" : "⬜ បានដោះ Tick ទាំងអស់");
}

async function redownloadQueueItem(id){
  const c = cart[id];
  if(!c) return;
  if(lastStatus && lastStatus.series){
    lastStatus.series = lastStatus.series.filter(s => s.sid !== id);
  }
  c.checked = true;
  saveCart();
  renderQueue();
  
  if(!lastStatus.running){
    if(confirm(`តើអ្នកចង់ចាប់ផ្តើមទាញយករឿង 《${c.title}》 ឡើងវិញឥឡូវនេះទេ?`)){
      const origTicks = {};
      Object.keys(cart).forEach(k => { origTicks[k] = cart[k].checked; cart[k].checked = (k === id); });
      await start();
      Object.keys(cart).forEach(k => { cart[k].checked = origTicks[k] !== false; });
      saveCart();
      renderQueue();
    } else {
      toast(`🔄 បានត្រៀមរឿង 《${c.title}》 ក្នុង Queue រួចរាល់!`);
    }
  } else {
    toast(`🔄 បាន Tick រឿង 《${c.title}》 ក្នុង Queue រួចរាល់!`);
  }
}

/* ---------- dock ---------- */
function updateDock(){
  const allIds = Object.keys(cart).filter(id=>!(cart[id]&&cart[id].unavailable));
  const tickedIds = allIds.filter(id => cart[id].checked !== false);
  const dock = $("#dock");
  if(dock) dock.classList.toggle("show", allIds.length > 0);
  const dockN = $("#dockN"); if(dockN) dockN.textContent = `${tickedIds.length}/${allIds.length}`;
  const eps = tickedIds.reduce((a,id)=>{const c=cart[id]||{}; return a+((c.sel&&c.sel.length)?c.sel.length:(c.total||0));},0);
  const epsText = allIds.length ? (eps? (`≈ ${eps} episodes (${tickedIds.length} ticked)`) : "episodes counted after resolve") : "nothing queued yet";
  const dockEps = $("#dockEps"); if(dockEps) dockEps.textContent = epsText;
  const running=!!lastStatus.running;
  if(dock) dock.classList.toggle("running", running);
  const startBtn = $("#startBtn"); const cancelBtn = $("#cancelBtn");
  if(startBtn){
    startBtn.style.display = running?"none":"";
    startBtn.disabled = tickedIds.length===0;
    if(!running){
      startBtn.textContent = tickedIds.length ? `Start Download (${tickedIds.length})` : "Start Download (0 ticked)";
    }
  }
  if(cancelBtn) cancelBtn.style.display = running?"":"none";

  // Sync controls inside right-side drawer #sideQueueDrawer
  const sqDockN = $("#sqDockN"); if(sqDockN) sqDockN.textContent = `${tickedIds.length}/${allIds.length}`;
  const sqDockEps = $("#sqDockEps"); if(sqDockEps) sqDockEps.textContent = epsText;
  const sqStart = $("#sqStartBtn"); const sqCancel = $("#sqCancelBtn");
  if(sqStart){
    sqStart.style.display = running ? "none" : "";
    sqStart.disabled = tickedIds.length === 0;
    sqStart.textContent = tickedIds.length ? `🚀 ចាប់ផ្តើមទាញយក (${tickedIds.length})` : "🚀 ចាប់ផ្តើមទាញយក (0 ticked)";
  }
  if(sqCancel){
    sqCancel.style.display = running ? "" : "none";
  }

  const sqProgBox = $("#sqProgBox");
  if(sqProgBox) sqProgBox.style.display = running ? "" : "none";

  if(running){
    let d=0,t=0;
    let totalSpeedBytes = 0;
    (lastStatus.series||[]).forEach(s=>{
      d+=s.done||0; t+=s.total||0;
      if(s.speed){
        const m = String(s.speed).match(/([\d.]+)\s*([KkMmGg]?B\/s)/i);
        if(m){
          let v = parseFloat(m[1]);
          const u = (m[2]||'').toUpperCase();
          if(u.startsWith('M')) v *= 1024 * 1024;
          else if(u.startsWith('K')) v *= 1024;
          else if(u.startsWith('G')) v *= 1024 * 1024 * 1024;
          totalSpeedBytes += v;
        }
      }
    });
    const pct=t?Math.round(d*100/t):0;
    const dockFill = $("#dockFill"); if(dockFill) dockFill.style.width=pct+"%";
    const dockPct = $("#dockPct"); if(dockPct) dockPct.textContent=pct+"%";
    // Upper row does NOT show speed per user request:
    if(dockEps){
      dockEps.textContent = `Downloading (${tickedIds.length} dramas selected · ${epsText})`;
    }
    const sqFill = $("#sqProgFill"); if(sqFill) sqFill.style.width = pct + "%";
    const sqPct = $("#sqProgPct"); if(sqPct) sqPct.textContent = pct + "%";
    let cleanTotalSpeed = '⚡ 0 MB/s';
    if(totalSpeedBytes > 0){
      if(totalSpeedBytes >= 1024 * 1024) cleanTotalSpeed = `⚡ ${(totalSpeedBytes / (1024 * 1024)).toFixed(1)} MB/s`;
      else if(totalSpeedBytes >= 1024) cleanTotalSpeed = `⚡ ${Math.round(totalSpeedBytes / 1024)} KB/s`;
      else cleanTotalSpeed = `⚡ ${Math.round(totalSpeedBytes)} B/s`;
    }
    const sqSpd = $("#sqProgSpeed"); if(sqSpd) sqSpd.textContent = cleanTotalSpeed;
  }

  updateSideQueueFloat();
}

/* ---------- start / cancel ---------- */
async function start(){
  const allValid = Object.keys(cart).filter(id=>!(cart[id]&&cart[id].unavailable));
  const ids = allValid.filter(id => cart[id].checked !== false);
  if(!ids.length){
    if(allValid.length){
      toast("⚠️ សូម Tick (☑️) ជ្រើសរើសរឿងណាមួយក្នុង Queue ដើម្បី Download!", true);
    }
    return;
  }
  const startBtn = $("#startBtn"); if(startBtn) startBtn.disabled=true;
  const sqStartBtn = $("#sqStartBtn"); if(sqStartBtn) sqStartBtn.disabled=true;
  const ranges={};
  ids.forEach(id=>{ const c=cart[id]; if(c && c.sel && c.total && c.sel.length && c.sel.length<c.total){ ranges[id]=compressRange(c.sel); } });
  const scores={}; ids.forEach(id=>{ const sc=(cart[id]||{}).score; if(sc) scores[id]=String(sc); });
  const ranks={}; ids.forEach(id=>{ const rk=(cart[id]||{}).rank; if(rk) ranks[id]=Number(rk); });
  const titles_km={};
  ids.forEach(id=>{
    const c=cart[id];
    if(c){
      const km = c.title_km || getCachedTrans(c.title) || '';
      if(km) titles_km[id] = km;
    }
  });
  const qual = ($("#sqQuality") && $("#sqQuality").value) || ($("#quality") && $("#quality").value) || "1080p";
  const conc = Number(($("#sqConc") && $("#sqConc").value) || ($("#conc") && $("#conc").value)) || 4;
  const sao = Number(($("#sqSeriesAtOnce") && $("#sqSeriesAtOnce").value) || ($("#seriesAtOnce") && $("#seriesAtOnce").value)) || 2;
  const devId = (window.userAccess && window.userAccess.device_id) || '';
  const authTok = localStorage.getItem('syd_auth_token') || '';
  const payload={series_ids:ids,quality:qual,concurrency:conc,series_at_once:sao,ranges,scores,ranks,titles_km,device_id:devId,token:authTok};
  try{
    const j = DEMO ? demoStart(payload) : await (await fetch("/dl/submit",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)})).json();
    if(!j.ok){
      if(j.reason==='vip_required' || j.reason==='vip_pending' || j.reason==='vip_expired'){
        toast(j.error || "⚡ កំពុងរៀបចំការទាញយក...", false);
      }
      else if(j.reason==='free_limit') promptActivate(j);
      else if(/already running/i.test(j.error||"")){
        toast("⚡ ការទាញយកកំពុងដំណើរការរួចរាល់ហើយ! (Download is running)", false);
        try{ await poll(); }catch(e){}
        if(confirm("ការទាញយកកំពុងដំណើរការរួចជាស្រេច!\n\nតើអ្នកចង់បញ្ឈប់ការងារបច្ចុប្បន្ន ដើម្បីចាប់ផ្តើមឡើងវិញទេ?")){
          try{ await fetch("/dl/cancel",{method:"POST"}); toast("បានស្នើសុំបញ្ឈប់ — សូមចុចទាញយកម្តងទៀតបន្ទាប់ពីបន្តិច"); }
          catch(e){ toast("មិនអាចបញ្ឈប់បានទេ", true); }
        }
      }
      else toast(j.error||"Couldn't start", true);
      if(startBtn) startBtn.disabled=false;
      if(sqStartBtn) sqStartBtn.disabled=false;
    } else {
      if(j.need_license){ toast("Some series need a license — activate to get them", true); promptActivate(j); }
      else {
        toast("🚀 Download started");
      }
      if(!(DEMO||ALLOW_DEMO)){ refreshAccount(); }
    }
  }catch(e){
    toast("Start failed: "+e, true);
    if(startBtn) startBtn.disabled=false;
    if(sqStartBtn) sqStartBtn.disabled=false;
  }
}
async function cancel(){ $("#cancelBtn").disabled=true;
  try{ if(DEMO) demoCancel(); else await fetch("/dl/cancel",{method:"POST"}); toast("Stopping…"); }catch(e){}
  setTimeout(()=>$("#cancelBtn").disabled=false,800); }

/* ---------- translation cache & batch helper ---------- */
const _transCache = (function(){
  try{ return JSON.parse(localStorage.getItem("hg_trans_cache")||"{}"); }catch(e){ return {}; }
})();
function getCachedTrans(t){
  if(!t) return '';
  return _transCache[t.trim()] || '';
}
function setCachedTrans(t, km){
  if(!t || !km) return;
  _transCache[t.trim()] = km.trim();
  try{ localStorage.setItem("hg_trans_cache", JSON.stringify(_transCache)); }catch(e){}
}
let _translatingSeq = 0;
async function autoTranslateCatalog(items){
  const seq = ++_translatingSeq;
  const missing = [];
  (items||[]).forEach(x=>{
    if(x && x.title){
      const t = x.title.trim();
      if(!x.title_km && !_transCache[t] && !missing.includes(t)){
        missing.push(t);
      }
    }
  });
  if(!missing.length) return;
  const CHUNK_SIZE = 25;
  for(let i=0; i<missing.length; i+=CHUNK_SIZE){
    if(seq !== _translatingSeq) return;
    const chunk = missing.slice(i, i+CHUNK_SIZE);
    try{
      const res = await fetch("/dl/translate_batch", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({texts: chunk})
      });
      const j = await res.json();
      const map = j.translations || {};
      Object.keys(map).forEach(cn => {
        const km = (map[cn]||'').trim();
        if(km){
          setCachedTrans(cn, km);
          const nodes = document.querySelectorAll(`.ttl-km[data-need-trans="${CSS.escape(cn)}"]`);
          nodes.forEach(el => {
            el.innerHTML = `<span class="kh-prefix">KH</span> ${esc(km)}`;
            el.title = km;
            el.removeAttribute("data-need-trans");
            const p = el.closest(".poster");
            if(p) p.dataset.tkm = km;
          });
        }
      });
    }catch(err){
      console.warn("Auto translate chunk error:", err);
    }
  }
}

let _qTranslating = false;
async function autoTranslateQueue(){
  if(_qTranslating) return;
  const missing = [];
  const ids = Object.keys(cart);
  ids.forEach(id => {
    const c = cart[id];
    if(c && c.title && !c.unavailable){
      const t = c.title.trim();
      const cached = getCachedTrans(t);
      if(cached){
        if(!c.title_km){ c.title_km = cached; }
      } else if(!missing.includes(t)){
        missing.push(t);
      }
    }
  });
  if(!missing.length) return;
  _qTranslating = true;
  try {
    const res = await fetch("/dl/translate_batch", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({texts: missing.slice(0, 25)})
    });
    const j = await res.json();
    const map = j.translations || {};
    let anyUpdated = false;
    ids.forEach(id => {
      const c = cart[id];
      if(c && c.title && map[c.title.trim()]){
        const km = map[c.title.trim()].trim();
        if(km){
          c.title_km = km;
          setCachedTrans(c.title.trim(), km);
          anyUpdated = true;
          const row = document.querySelector(`.row[data-qid="${id}"]`);
          if(row){
            let rttlKm = row.querySelector(".rttl-km");
            if(rttlKm){
              rttlKm.textContent = `🇰🇭 ${km}`;
            } else {
              const r1 = row.querySelector(".r1");
              if(r1){
                rttlKm = document.createElement("div");
                rttlKm.className = "rttl-km";
                rttlKm.style.cssText = "font-size:11.5px;font-weight:600;color:var(--accent);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
                rttlKm.textContent = `🇰🇭 ${km}`;
                r1.insertAdjacentElement("afterend", rttlKm);
              }
            }
          }
        }
      }
    });
    if(anyUpdated) saveCart();
  } catch(e){
  } finally {
    _qTranslating = false;
  }
}

/* ---------- episode picker (pick a subset per series; default = whole series) ---------- */
const epCache={};             // series_id -> [episode indices]
let epCur=null, epSel=null;   // current series id + working Set of selected indices
function compressRange(arr){  // [1,2,3,5,7,8] -> "1-3,5,7-8"
  const a=[...arr].sort((x,y)=>x-y); const out=[]; let i=0;
  while(i<a.length){ let j=i; while(j+1<a.length && a[j+1]===a[j]+1) j++;
    out.push(i===j? ""+a[i] : a[i]+"-"+a[j]); i=j+1; }
  return out.join(",");
}
async function openEpModal(id){
  let c = cart[id];
  const p = document.querySelector(`.poster[data-id="${id}"]`);
  if(!c){
    c = {
      title: (p && p.dataset.t) || id,
      title_km: (p && p.dataset.tkm) || (p && p.dataset.t ? getCachedTrans(p.dataset.t) : '') || '',
      total: (p && Number(p.dataset.n)) || 0,
      cover: (p && p.dataset.cov) || '',
      checked: true,
      fromPoster: true
    };
  }
  epCur = id;
  const dispTitle = c.title || id;
  const km = c.title_km ? ` · 🇰🇭 ${c.title_km}` : '';
  $("#epTitle").textContent = dispTitle + km;
  $("#epSub").textContent = "⏳ កំពុងទាញយកភាគទាំងអស់ (Loading episodes)...";
  $("#epGrid").innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:30px;color:var(--muted);font-family:var(--font-km)">⏳ កំពុងទាញយកបញ្ជីភាគទាំងអស់ពី Hongguo...</div>';
  $("#epModal").hidden = false;

  let eps = epCache[id];
  if(!eps || !eps.length){
    if(DEMO){
      eps = Array.from({length: c.total || 24}, (_, i) => i + 1);
    } else {
      try {
        const j = await (await fetch("/dl/episodes?series_id=" + encodeURIComponent(id))).json();
        eps = j.episodes || [];
        if(j.total) c.total = j.total;
        if(j.title && !c.title) c.title = j.title;
        if(j.cover && !c.cover) c.cover = j.cover;
      } catch(e) {
        eps = [];
      }
    }
    const totCount = c.total || (p && Number(p.dataset.n)) || 0;
    if((!eps || !eps.length) && totCount > 0){
      eps = Array.from({length: totCount}, (_, i) => i + 1);
    }
    epCache[id] = eps;
  }

  epSel = (c.sel && c.sel.length) ? new Set(c.sel) : new Set(eps); // default: all selected
  const actualTot = eps.length || c.total || 0;
  $("#epSub").textContent = `${actualTot} ភាគសរុប · ចុចលើលេខភាគដើម្បីជ្រើសរើស`;
  renderEpGrid(eps);
}

function renderEpGrid(eps){
  if(!eps || !eps.length){
    $("#epGrid").innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:25px;color:var(--bad);font-family:var(--font-km)">⚠️ មិនមានទិន្នន័យភាគសម្រាប់រឿងនេះទេ</div>';
    $("#epCount").textContent = '0 បានជ្រើសរើស';
    return;
  }
  $("#epGrid").innerHTML = eps.map(n => `<button class="epchip" data-ei="${n}" aria-pressed="${epSel.has(n)}">${n}</button>`).join("");
  $("#epCount").textContent = `${epSel.size} / ${eps.length} បានជ្រើសរើស`;
}

function closeEp(){ $("#epModal").hidden=true; epCur=null; epSel=null; }
$("#epGrid").addEventListener("click", e => {
  const b = e.target.closest("[data-ei]"); if(!b || !epSel) return;
  const n = Number(b.dataset.ei);
  if(epSel.has(n)){ epSel.delete(n); b.setAttribute("aria-pressed","false"); }
  else { epSel.add(n); b.setAttribute("aria-pressed","true"); }
  $("#epCount").textContent = `${epSel.size} / ${(epCache[epCur]||[]).length} បានជ្រើសរើស`;
});
$("#epAll").onclick = () => { const eps = epCache[epCur]||[]; epSel = new Set(eps); renderEpGrid(eps); };
$("#epNone").onclick = () => { epSel = new Set(); renderEpGrid(epCache[epCur]||[]); };
$("#epClose").onclick = closeEp; $("#epCancel").onclick = closeEp;
$("#epModal").addEventListener("click", e => { if(e.target.id==="epModal") closeEp(); });
$("#epDone").onclick = () => {
  let c = cart[epCur];
  const eps = epCache[epCur] || [];
  const p = document.querySelector(`.poster[data-id="${epCur}"]`);
  if(!c){
    if(p){
      addToCart(epCur, p.dataset.t, Number(p.dataset.n)||eps.length, p.dataset.cov, true, p.dataset.sc, Number(p.dataset.rk)||0, p.dataset.dt||'', p.dataset.tkm||'');
      c = cart[epCur];
    }
  }
  if(!c){ closeEp(); return; }
  delete c.fromPoster;
  if(epSel.size === 0){
    toast("មិនបានជ្រើសភាគទេ — រក្សាទុករឿងទាំងមូល (All episodes)");
    delete c.sel;
  } else if(epSel.size >= eps.length){
    delete c.sel;
  } else {
    c.sel = [...epSel].sort((a,b)=>a-b);
  }
  saveCart();
  renderQueue();
  syncResultButtons();
  closeEp();
  openSideQueue();
  const cnt = c.sel ? c.sel.length : (eps.length || c.total || 'ទាំងអស់');
  toast(`✅ បានជ្រើសរើស ${cnt} ភាគ ចូលក្នុង Queue`);
};

/* ============ Drama Detail View (ទំព័រព័ត៌មានលម្អិត និងភាគ) ============ */
let dramaDetailHistory = [];
let preDetailScroll = 0;
let ddCurrentDrama = null;
let ddSelectedEps = new Set();
let ddAllEps = [];
let ddActiveRange = 0;
const DD_RANGE_SIZE = 30;
let ddMode = 'stream'; // 'stream' (default for live preview) | 'select' (for multi-download)

function formatPlayCount(num){
  const n = Number(num) || 0;
  if(n >= 100000000) return (n / 100000000).toFixed(1) + " 亿 views";
  if(n >= 10000) return (n / 10000).toFixed(1) + " 万 views";
  if(n >= 1000) return (n / 1000).toFixed(1) + "k views";
  return n ? (n.toLocaleString() + " views") : "";
}

function updateDdQueueBtn(){
  if(!ddCurrentDrama) return;
  const inQ = !!cart[ddCurrentDrama.id];
  const hqBtn = $("#ddHeaderQueueBtn");
  const heroQBtn = $("#ddHeroQueueBtn");
  if(hqBtn){
    hqBtn.textContent = inQ ? "✓ ក្នុង Queue" : "➕ ដាក់ចូល Queue";
    hqBtn.classList.toggle("in-queue", inQ);
  }
  if(heroQBtn){
    heroQBtn.textContent = inQ ? "✓ បានដាក់ចូល Queue រួចរាល់" : "➕ ដាក់ចូល Queue";
    heroQBtn.classList.toggle("primary", inQ);
    heroQBtn.classList.toggle("ghost", !inQ);
  }
}

function posterCoverUrl(cover, title, id){
  return getPosterUrl(cover, title, id);
}

function getAvatarUrl(rawUrl){
  if(!rawUrl) return '';
  rawUrl = String(rawUrl).trim();
  if(!rawUrl) return '';
  if(rawUrl.startsWith('/img?') || rawUrl.startsWith('/dl/') || rawUrl.startsWith('data:') || rawUrl.startsWith('blob:') || rawUrl.startsWith('/logo.png')){
    return rawUrl;
  }
  return `/img?url=${encodeURIComponent(rawUrl)}`;
}

const CATEGORY_MAP_KM = {
  '爱情': 'ស្នេហា', '都市爱情': 'ស្នេហាក្នុងក្រុង', '都市': 'ទីក្រុង', '现代': 'សម័យទំនើប',
  '闪婚': 'រៀបការភ្លាមៗ', '先婚后爱': 'ការរួចទើបស្រឡាញ់', '日久生情': 'នៅយូរស្រឡាញ់គ្នា',
  '女强': 'នារីរឹងមាំ', '总裁': 'អគ្គនាយក/ថៅកែ', '豪门': 'គ្រួសារអភិជន', '逆袭': 'វាយបកយកឈ្នះ',
  '战神': 'ស្ដេចសង្គ្រាម', '穿越': 'ឆ្លងភព', '重生': 'ចាប់ជាតិថ្មី', '古装': 'រឿងបុរាណ',
  '复仇': 'សងសឹក', '甜宠': 'ស្នេហាផ្អែមល្ហែម', '虐恋': 'ស្នេហាឈឺចាប់', '家庭': 'គ្រួសារ',
  '伦理': 'សីលធម៌គ្រួសារ', '悬疑': 'អាថ៌កំបាំង', '动作': 'វាយប្រហារ', '喜剧': 'កំប្លែង',
  '短剧': 'រឿងខ្លី', '极品亲戚': 'សាច់ញាតិអាក្រក់', '神豪': 'សេដ្ឋីលាក់មុខ', '热血': 'រំភើបញាប់ញ័រ',
  '青春': 'យុវវ័យ', '校园': 'សាលារៀន'
};

function getCategoryKm(cat){
  if(!cat) return 'រឿងខ្លី';
  if(CATEGORY_MAP_KM[cat]) return CATEGORY_MAP_KM[cat];
  const cached = getCachedTrans(cat);
  if(cached) return cached;
  return cat;
}

async function openDramaDetail(id, pEl = null, isNavBack = false){
  if(!id) return;
  closeInlinePlayer();
  ddInlinePlayingEp = 1;
  ddMode = 'stream';
  ddActiveRange = 0;

  const currentSec = $("#resultsSec");
  const detailSec = $("#dramaDetailSec");
  
  if(!isNavBack){
    if(ddCurrentDrama && String(ddCurrentDrama.id) !== String(id)){
      dramaDetailHistory.push(ddCurrentDrama.id);
    }
    if(detailSec.hidden){
      preDetailScroll = window.scrollY || document.documentElement.scrollTop;
    }
  }

  currentSec.hidden = true;
  detailSec.hidden = false;
  window.scrollTo({top: detailSec.offsetTop - 20, behavior: "smooth"});

  // Get fast preliminary info from DOM poster card if available
  const p = pEl || document.querySelector(`.poster[data-id="${CSS.escape(String(id))}"]`);
  const t = (p && p.dataset.t) || String(id);
  const tkm = (p && p.dataset.tkm) || getCachedTrans(t) || '';
  const cov = (p && p.dataset.cov) || '';
  const n = (p && Number(p.dataset.n)) || 0;
  const sc = (p && p.dataset.sc) || '';

  ddAllEps = (epCache[id] && epCache[id].length) ? epCache[id] : (n ? Array.from({length: n}, (_, i) => i + 1) : []);

  ddCurrentDrama = {
    id: String(id),
    title: t,
    title_km: tkm,
    total: n,
    cover: cov,
    score: sc,
    intro: '',
    category: [],
    celebrities: [],
    status: '',
    play_cnt: 0
  };

  // Render fast initial state immediately
  renderDramaDetailUI(ddCurrentDrama);

  // Fetch full details & episodes from /dl/episodes?series_id=...
  try {
    const res = await (await fetch("/dl/episodes?series_id=" + encodeURIComponent(id))).json();
    if(res){
      if(res.title) ddCurrentDrama.title = res.title;
      if(res.title_km) ddCurrentDrama.title_km = res.title_km;
      if(res.cover) ddCurrentDrama.cover = res.cover;
      if(res.total) ddCurrentDrama.total = res.total;
      if(res.intro) ddCurrentDrama.intro = res.intro;
      if(res.intro_km) ddCurrentDrama.intro_km = res.intro_km;
      if(res.category) ddCurrentDrama.category = res.category;
      if(res.category_km) ddCurrentDrama.category_km = res.category_km;
      if(res.celebrities) ddCurrentDrama.celebrities = res.celebrities;
      if(res.status) ddCurrentDrama.status = res.status;
      if(res.play_cnt) ddCurrentDrama.play_cnt = res.play_cnt;
      if(res.score) ddCurrentDrama.score = res.score;
      
      const eps = (res.episodes && res.episodes.length) ? res.episodes : (ddAllEps.length ? ddAllEps : Array.from({length: ddCurrentDrama.total || 24}, (_, i) => i + 1));
      epCache[id] = eps;
      ddAllEps = eps;
    }
  } catch(e){
    if(!ddAllEps.length){
      ddAllEps = (epCache[id] && epCache[id].length) ? epCache[id] : Array.from({length: ddCurrentDrama.total || 24}, (_, i) => i + 1);
    }
  }

  // Update UI with rich metadata
  renderDramaDetailUI(ddCurrentDrama);

  // Auto-translate title if needed
  if(!ddCurrentDrama.title_km && ddCurrentDrama.title){
    translateDramaTitle(ddCurrentDrama);
  }

  // Auto-translate intro if needed
  if(!ddCurrentDrama.intro_km && ddCurrentDrama.intro){
    translateDramaIntro(ddCurrentDrama);
  }

  // Load Related Dramas
  loadRelatedDramas(ddCurrentDrama);
}

function renderDramaDetailUI(item){
  // Video poster & initial stream ready
  const covUrl = getPosterUrl(item.cover, item.title, item.id) || '/logo.png';
  const vid = $("#ddInlineVideo");
  if(vid){
    vid.poster = covUrl;
    if(!vid.src || !vid.src.includes(`series_id=${encodeURIComponent(item.id)}`)){
      vid.src = `/dl/stream?series_id=${encodeURIComponent(item.id)}&ep=1`;
    }
  }
  showPlayPosterOverlay();
  const loading = $("#ddInlineLoading");
  if(loading) loading.hidden = true;
  
  // Title (Display Khmer prominently)
  if(item.title_km){
    $("#ddTitle").textContent = item.title_km;
    $("#ddTitleKm").textContent = item.title ? `🇨🇳 ចំណងជើងដើម: ${item.title}` : '';
  } else if(item.title && getCachedTrans(item.title)){
    item.title_km = getCachedTrans(item.title);
    $("#ddTitle").textContent = item.title_km;
    $("#ddTitleKm").textContent = item.title ? `🇨🇳 ចំណងជើងដើម: ${item.title}` : '';
  } else {
    $("#ddTitle").textContent = item.title || item.id;
    $("#ddTitleKm").textContent = '⏳ កំពុងបកប្រែចំណងជើងជាភាសាខ្មែរ...';
  }

  // Breadcrumbs
  const bCat = $("#ddBreadCat");
  const cats = (item.category_km && item.category_km.length) 
    ? item.category_km 
    : ((item.category && item.category.length) ? item.category.map(c => getCategoryKm(c)) : ['រឿងខ្លី']);
  if(bCat) bCat.textContent = cats[0] || 'រឿងខ្លី';
  const bTitle = $("#ddBreadTitle");
  if(bTitle) bTitle.textContent = `《${item.title_km || item.title}》 ភាគទី ${ddInlinePlayingEp || 1}`;

  // Tags (100% Khmer)
  const tagsEl = $("#ddTags");
  tagsEl.innerHTML = cats.map((ckm, idx) => {
    const orig = (item.category && item.category[idx]) || '';
    return `<span class="dd-tag" title="${esc(orig)}">${esc(ckm)}</span>`;
  }).join("");
  tagsEl.hidden = false;

  // Meta badges & Likes
  $("#ddScoreBadge").textContent = item.score ? `★ ${item.score}` : '★ 8.5';
  const tot = ddAllEps.length || item.total || 0;
  $("#ddTotalEps").textContent = tot ? `${tot} ភាគ` : 'ច្រើនភាគ';

  const pc = formatPlayCount(item.play_cnt);
  const pcEl = $("#ddPlayCnt");
  if(pc){ pcEl.textContent = pc; } else { pcEl.textContent = "85.7万"; }

  const likesEl = $("#ddLikes");
  if(likesEl){
    const cnt = Number(item.play_cnt) || 85700;
    const lk = Math.round(cnt * 0.058) || 4941;
    likesEl.textContent = lk > 10000 ? (lk/10000).toFixed(1) + '万' : (lk > 1000 ? (lk/1000).toFixed(1) + 'k' : lk);
  }

  const curNumText = $("#ddCurrentEpNumText");
  if(curNumText) curNumText.textContent = `ភាគទី ${ddInlinePlayingEp || 1}`;
  const dlCurBtn = $("#ddInlineDlCur");
  if(dlCurBtn) dlCurBtn.textContent = `⬇️ ដោនឡូតភាគ ${ddInlinePlayingEp || 1}`;

  const statusEl = $("#ddStatusBadge");
  const st = item.status || '完结';
  statusEl.textContent = (st === '完结' || st.includes('完')) ? 'ចប់ពេញលេញ (Completed)' : (st.includes('连载') ? 'កំពុងចាក់ផ្សាយ (Ongoing)' : st);

  // Intro / synopsis (100% Khmer)
  const introEl = $("#ddIntro");
  if(item.intro_km){
    introEl.textContent = item.intro_km;
  } else if(item.intro && getCachedTrans(item.intro)){
    item.intro_km = getCachedTrans(item.intro);
    introEl.textContent = item.intro_km;
  } else if(item.intro){
    introEl.innerHTML = '<span style="color:var(--muted);font-style:italic">⏳ កំពុងបកប្រែខ្លឹមសាររឿងជាភាសាខ្មែរ...</span>';
    translateDramaIntro(item);
  } else {
    introEl.textContent = "កំពុងទាញយកព័ត៌មានលម្អិតពីរឿង...";
  }

  // Cast
  const castSec = $("#ddCastSec");
  const castList = $("#ddCastList");
  if(item.celebrities && item.celebrities.length){
    castList.innerHTML = item.celebrities.map(c => {
      const name = c['演员'] || c['nickname'] || c['name'] || '';
      const role = c['角色'] || c['role_name'] || c['role'] || '';
      const rawPic = c['头像'] || c['avatar'] || c['avatar_url'] || '';
      const picUrl = getAvatarUrl(rawPic);
      const initial = (name || 'ត').charAt(0).toUpperCase();
      return `
        <div class="cast-item" title="${esc(name)}${role ? ' (' + esc(role) + ')' : ''}">
          <div style="position:relative;width:58px;height:58px;display:flex;align-items:center;justify-content:center">
            ${picUrl ? `
              <img class="cast-avatar" src="${esc(picUrl)}" 
                   onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='flex';" 
                   alt="${esc(name)}" loading="lazy">
              <div class="cast-avatar" style="display:none;align-items:center;justify-content:center;background:linear-gradient(135deg,#0284c7,#38bdf8);color:#ffffff;font-size:22px;font-weight:800;border:2px solid rgba(56,189,248,0.6)">
                ${esc(initial)}
              </div>
            ` : `
              <div class="cast-avatar" style="display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#0284c7,#38bdf8);color:#ffffff;font-size:22px;font-weight:800;border:2px solid rgba(56,189,248,0.6)">
                ${esc(initial)}
              </div>
            `}
          </div>
          <div class="cast-name">${esc(name || 'តួអង្គ')}</div>
          <div class="cast-role">${role ? esc(role) : 'តួសម្តែង'}</div>
        </div>
      `;
    }).join("");
    castSec.hidden = false;
  } else {
    castSec.hidden = true;
  }

  // Episodes
  const existingCart = cart[item.id];
  if(existingCart && existingCart.sel && existingCart.sel.length){
    ddSelectedEps = new Set(existingCart.sel);
  } else {
    ddSelectedEps = new Set(ddAllEps);
  }
  renderDramaDetailEpisodes();
  updateDdQueueBtn();
}

function renderDramaDetailEpisodes(){
  const eps = ddAllEps || [];
  const countEl = $("#ddEpSelectedCount");
  if(countEl) countEl.textContent = `${ddSelectedEps.size}`;

  const isStream = ddMode === 'stream';
  const modeStreamBtn = $("#ddModeStream");
  const modeSelectBtn = $("#ddModeSelect");
  if(modeStreamBtn) modeStreamBtn.classList.toggle("on", isStream);
  if(modeSelectBtn) modeSelectBtn.classList.toggle("on", !isStream);

  const selToolbar = $("#ddSelectToolbar");
  if(selToolbar) selToolbar.hidden = isStream;

  const rangesEl = $("#ddEpRanges");
  const gridEl = $("#ddEpGrid");
  const totHint = $("#ddEpTotalHint");

  if(!eps.length){
    if(totHint) totHint.textContent = `សរុប 0 ភាគ`;
    gridEl.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:20px;color:var(--muted);font-family:var(--font-km)">⏳ កំពុងទាញយកបញ្ជីភាគ...</div>';
    if(rangesEl) rangesEl.innerHTML = '';
    return;
  }

  const isFull = isUserFullAccess();
  let userEpLimit = 5;
  let isDramaFreeAll = false;
  const currSid = (ddCurrentDrama ? (ddCurrentDrama.id || ddCurrentDrama.series_id) : null);
  if (currSid && typeof getDramaRuleForSeries === 'function') {
    const dr = getDramaRuleForSeries(currSid);
    if (dr && dr.rule === 'free_all') isDramaFreeAll = true;
    else if (dr && dr.free_episodes != null) userEpLimit = Number(dr.free_episodes);
    else userEpLimit = 5;
  } else {
    userEpLimit = 5;
  }

  // Calculate episode statistics (ទាំងភាគ Lock និងភាគអត់ Lock)
  let freeEpCount = 0;
  let lockedEpCount = 0;
  if(isFull || isDramaFreeAll){
    freeEpCount = eps.length;
    lockedEpCount = 0;
  } else {
    freeEpCount = Math.min(eps.length, userEpLimit);
    lockedEpCount = Math.max(0, eps.length - freeEpCount);
  }

  // Update Episode Statistics Badges in UI (បង្ហាញចំនួនភាគទាំងភាគ Lock និងភាគអត់ Lock)
  if(totHint){
    totHint.innerHTML = `
      <span style="display:inline-flex;align-items:center;gap:6px;flex-wrap:wrap">
        <span style="font-size:11px;font-weight:800;padding:2px 8px;border-radius:6px;background:rgba(34,197,94,0.18);color:#22c55e;border:1px solid rgba(34,197,94,0.4)" title="ភាគដែលអាចទស្សនា និងដោនឡូតបានដោយសេរី ឥតគិតថ្លៃ">
          🔓 អត់ Lock: ${freeEpCount} ភាគ
        </span>
        <span style="font-size:11px;font-weight:800;padding:2px 8px;border-radius:6px;background:rgba(234,179,8,0.18);color:#eab308;border:1px solid rgba(234,179,8,0.4)" title="ភាគដែលត្រូវប្រើ 2 Coins (1,000៛) ឬ VIP">
          🔒 ជាប់ Lock: ${lockedEpCount} ភាគ
        </span>
        <span style="font-size:11.5px;font-weight:800;color:var(--muted)">
          (សរុប ${eps.length} ភាគ)
        </span>
      </span>
    `;
  }

  // Update Drama Rule Badge in info bar
  const ruleBadge = $("#ddDramaRuleBadge");
  if(ruleBadge){
    if(isDramaFreeAll || isFull){
      ruleBadge.innerHTML = `🟢 Free គ្រប់ភាគទាំងអស់ (${eps.length} ភាគ)`;
      ruleBadge.style.color = "var(--good)";
      ruleBadge.style.background = "rgba(34,197,94,0.15)";
      ruleBadge.style.borderColor = "rgba(34,197,94,0.4)";
    } else {
      ruleBadge.innerHTML = `🔓 Free (អត់ Lock): ភាគ 1-${userEpLimit} (${freeEpCount} ភាគ) · 🔒 ជាប់ Lock: ភាគ ${userEpLimit+1}+ (${lockedEpCount} ភាគ)`;
    }
  }

  // Update VIP Episode Alert Banner text with exact breakdown
  const vipBanner = $("#ddVipEpisodeBanner");
  if(vipBanner){
    vipBanner.style.display = (isFull || isDramaFreeAll) ? 'none' : 'flex';
    const vipSpan = vipBanner.querySelector('div span');
    if(vipSpan){
      vipSpan.innerHTML = `<b>គណនីធម្មតា:</b> ឥតគិតថ្លៃ (អត់ Lock) <b>${freeEpCount} ភាគ</b> (ភាគ 1 ដល់ ${userEpLimit}) · ជាប់ Lock <b>${lockedEpCount} ភាគ</b> (ភាគ ${userEpLimit+1} ឡើងទៅ តម្រូវការ 2 Coins ឬ VIP)`;
    }
  }

  // Range Switcher Tabs (e.g. ទាំងអស់, 1-30, 31-60, 61-90, 91-94)
  if(eps.length > DD_RANGE_SIZE){
    rangesEl.hidden = false;
    const numRanges = Math.ceil(eps.length / DD_RANGE_SIZE);
    let rHtml = `<button type="button" class="dd-range-tab ${ddActiveRange===-1?'on':''}" data-range="-1">ទាំងអស់ (${eps.length})</button>`;
    for(let r=0; r<numRanges; r++){
      const start = r * DD_RANGE_SIZE + 1;
      const end = Math.min((r + 1) * DD_RANGE_SIZE, eps.length);
      rHtml += `<button type="button" class="dd-range-tab ${ddActiveRange===r?'on':''}" data-range="${r}">${start}-${end}</button>`;
    }
    rangesEl.innerHTML = rHtml;
  } else {
    rangesEl.hidden = false;
    rangesEl.innerHTML = `<span style="font-size:12.5px;font-weight:700;color:var(--muted)">ភាគ 1 - ${eps.length}</span>`;
  }

  // Slice visible episodes based on active range
  let visibleEps = eps;
  if(eps.length > DD_RANGE_SIZE && ddActiveRange >= 0){
    const startIdx = ddActiveRange * DD_RANGE_SIZE;
    visibleEps = eps.slice(startIdx, startIdx + DD_RANGE_SIZE);
  }

  // Render Episode Chips for both locked and unlocked episodes
  let chipsHtml = visibleEps.map(n => {
    const epNum = Number(n);
    const isSel = ddSelectedEps.has(n);
    const isPlaying = (ddInlinePlayingEp === n);
    const isLocked = isEpisodeLocked(n, currSid);
    let cls = "dd-epchip-item";
    if(isPlaying) cls += " active-playing";
    else if(!isStream && isSel) cls += " selected-for-dl";
    if(isLocked) cls += " locked-vip";
    
    let epLabel = `${n}`;
    let titleHint = '';
    if(isLocked){
      titleHint = `ភាគទី ${n} · 🔒 ជាប់ Lock (2 Coins = 1,000៛ ឬ VIP · ចុចដើម្បីដោះសោរ)`;
      epLabel = `<span style="display:inline-flex;align-items:center;justify-content:center;gap:3px"><span>${n}</span><span style="font-size:10px;opacity:0.9">🔒</span></span>`;
    } else {
      titleHint = `ភាគទី ${n} · 🔓 អត់ Lock (ឥតគិតថ្លៃ Free · ចុចដើម្បី ${isStream ? 'Live Stream មើល' : 'ជ្រើសរើសដោនឡូត'})`;
      epLabel = `<span style="display:inline-flex;align-items:center;justify-content:center;gap:3px"><span>${n}</span><span style="font-size:8.5px;color:var(--good);font-weight:900">Free</span></span>`;
    }

    return `<button type="button" class="${cls}" data-dei="${n}" aria-pressed="${isSel}" title="${titleHint}">${epLabel}</button>`;
  }).join("");

  gridEl.innerHTML = chipsHtml;
}

async function translateDramaTitle(item){
  if(!item || !item.title) return;
  const titleText = item.title.trim();
  if(!titleText) return;
  
  const cached = getCachedTrans(titleText);
  if(cached){
    item.title_km = cached;
    if(ddCurrentDrama && ddCurrentDrama.id === item.id){
      $("#ddTitle").textContent = cached;
      $("#ddTitleKm").textContent = item.title ? `🇨🇳 ចំណងជើងដើម: ${item.title}` : '';
    }
    return;
  }

  let translated = '';
  try {
    const res = await fetch("/dl/translate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: titleText})
    });
    if(res.ok){
      const j = await res.json();
      translated = j.translated || j.km || '';
    }
  } catch(e){}

  if(!translated){
    try {
      const gtxUrl = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=km&dt=t&q=" + encodeURIComponent(titleText);
      const gtxRes = await fetch(gtxUrl);
      if(gtxRes.ok){
        const gtxData = await gtxRes.json();
        if(gtxData && gtxData[0]){
          translated = gtxData[0].map(p => p && p[0] ? p[0] : '').join('').trim();
        }
      }
    } catch(e){}
  }

  if(translated){
    item.title_km = translated;
    setCachedTrans(titleText, translated);
    if(ddCurrentDrama && ddCurrentDrama.id === item.id){
      $("#ddTitle").textContent = translated;
      $("#ddTitleKm").textContent = item.title ? `🇨🇳 ចំណងជើងដើម: ${item.title}` : '';
    }
  }
}

async function translateDramaIntro(item){
  if(!item || !item.intro) return;
  const introText = item.intro.trim();
  if(!introText) return;
  
  const cached = getCachedTrans(introText);
  if(cached){
    item.intro_km = cached;
    if(ddCurrentDrama && ddCurrentDrama.id === item.id){
      const introEl = $("#ddIntro");
      if(introEl) introEl.textContent = cached;
    }
    return;
  }

  let translated = '';
  try {
    const res = await fetch("/dl/translate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text: introText})
    });
    if(res.ok){
      const j = await res.json();
      translated = j.translated || j.km || '';
    }
  } catch(e){}

  if(!translated){
    try {
      const gtxUrl = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-CN&tl=km&dt=t&q=" + encodeURIComponent(introText);
      const gtxRes = await fetch(gtxUrl);
      if(gtxRes.ok){
        const gtxData = await gtxRes.json();
        if(gtxData && gtxData[0]){
          translated = gtxData[0].map(part => part && part[0] ? part[0] : '').join('').trim();
        }
      }
    } catch(e){}
  }

  if(translated){
    item.intro_km = translated;
    setCachedTrans(introText, translated);
    if(ddCurrentDrama && ddCurrentDrama.id === item.id){
      const introEl = $("#ddIntro");
      if(introEl) introEl.textContent = translated;
    }
  } else {
    if(ddCurrentDrama && ddCurrentDrama.id === item.id){
      const introEl = $("#ddIntro");
      if(introEl) introEl.textContent = item.intro;
    }
  }
}

async function loadRelatedDramas(item){
  const box = $("#ddRelatedGrid");
  const headEl = $("#ddRelatedTitle");
  if(headEl) headEl.textContent = "🎬 រឿងពាក់ព័ន្ធ ឬស្រដៀងគ្នា (ប្រភេទដូចគ្នា - យ៉ាងច្រើន 10 រឿង)";
  box.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:25px;color:var(--muted);font-family:var(--font-km)">⏳ កំពុងស្វែងរករឿងប្រភេទស្រដៀងគ្នា...</div>';
  
  let relatedItems = [];
  const seenIds = new Set([String(item.id || item.series_id || '')]);

  // Extract categories & tags of current drama
  const rawCats = [
    ...((item.category && item.category.length) ? item.category : []),
    ...(item.theme ? [item.theme] : []),
    ...(item.genre ? [item.genre] : []),
    ...((item.tags && item.tags.length) ? item.tags : [])
  ];
  const kmCats = (item.category_km && item.category_km.length) ? item.category_km : [];
  const catSet = new Set([
    ...rawCats.map(c => String(c).trim().toLowerCase()),
    ...kmCats.map(c => String(c).trim().toLowerCase())
  ]);

  const matchesCategory = (it) => {
    if(!it) return false;
    const itCats = [
      ...((it.category && it.category.length) ? it.category : []),
      ...((it.category_km && it.category_km.length) ? it.category_km : []),
      ...(it.theme ? [it.theme] : []),
      ...(it.genre ? [it.genre] : []),
      ...((it.tags && it.tags.length) ? it.tags : [])
    ].map(c => String(c).trim().toLowerCase());
    
    // STRICT RULE: Must share at least one category or genre tag!
    if(catSet.size > 0){
      return itCats.some(c => catSet.has(c));
    }
    return false;
  };

  const addItems = (items) => {
    if(!items || !items.length) return;
    for(const it of items){
      if(relatedItems.length >= 10) break;
      const sid = String(it.series_id || it.id || '');
      if(sid && !seenIds.has(sid)){
        if(matchesCategory(it)){
          seenIds.add(sid);
          relatedItems.push(it);
        }
      }
    }
  };

  // 1. Fetch specifically from Explorer for this drama's genres
  if(!DEMO && rawCats.length){
    for(const c of rawCats.slice(0, 3)){
      if(relatedItems.length >= 10) break;
      try {
        const j = await (await fetch(EXPLORER_API + "/explorer?size=15&genre=" + encodeURIComponent(c), {cache:"no-store"})).json();
        if(j && j.items) addItems(j.items);
      } catch(e){}
    }
  }

  // 2. If fewer than 10, check trendData for items strictly matching the same category
  if(relatedItems.length < 10 && trendData && trendData.length){
    addItems(trendData);
  }

  // 3. If still fewer than 10, check in-memory catalog for strictly matching category
  if(relatedItems.length < 10 && window.dramaCatalogCache){
    addItems(window.dramaCatalogCache);
  }

  // STRICT RULE: Exactly maximum 10 posters of similar category only
  relatedItems = relatedItems.slice(0, 10);

  if(!relatedItems.length){
    box.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:15px;color:var(--muted);font-family:var(--font-km)">មិនមានរឿងប្រភេទស្រដៀងគ្នាផ្សេងទៀតនៅឡើយទេ</div>';
    if(headEl) headEl.textContent = "🎬 រឿងពាក់ព័ន្ធ ឬស្រដៀងគ្នា (0 រឿង)";
    return;
  }

  if(headEl) headEl.textContent = `🎬 រឿងពាក់ព័ន្ធ ឬស្រដៀងគ្នា (ប្រភេទដូចគ្នា - ${relatedItems.length} រឿង)`;
  box.innerHTML = resultCards(relatedItems, true);
  syncResultButtons();
  autoTranslateCatalog(relatedItems);
}

function closeDramaDetail(){
  closeInlinePlayer();
  if(dramaDetailHistory.length > 0){
    const prevId = dramaDetailHistory.pop();
    openDramaDetail(prevId, null, true);
    return;
  }
  $("#dramaDetailSec").hidden = true;
  $("#resultsSec").hidden = false;
  ddCurrentDrama = null;
  window.scrollTo({top: preDetailScroll, behavior: "smooth"});
}

// Event Bindings for Drama Detail
$("#ddBackBtn").onclick = closeDramaDetail;

document.addEventListener("keydown", e => {
  if(e.key === "Escape" && !$("#dramaDetailSec").hidden){
    closeDramaDetail();
  }
});

$("#ddCopyLinkBtn").onclick = () => {
  if(!ddCurrentDrama) return;
  const link = "https://novelquickapp.com/series/" + ddCurrentDrama.id;
  navigator.clipboard.writeText(link).then(() => {
    toast("📋 បានចម្លង Link រឿងនេះទុក");
  }).catch(() => {
    toast(`Link: ${link}`);
  });
};

$("#ddDlAllBtn").onclick = $("#ddHeroDlBtn").onclick = () => {
  if(!ddCurrentDrama) return;
  const id = ddCurrentDrama.id;
  const eps = ddAllEps || [];
  addToCart(id, ddCurrentDrama.title, ddCurrentDrama.total || eps.length, ddCurrentDrama.cover, false, ddCurrentDrama.score, 0, '', ddCurrentDrama.title_km);
  if(!isUserFullAccess() && cart[id]){
    const allowed = eps.filter(n => n <= 10);
    cart[id].sel = allowed.length ? allowed : [1];
    saveCart();
    renderQueue();
    toast(`⬇️ គណនីធម្មតា៖ បានដាក់ភាគ 1-10 នៃរឿង 《${ddCurrentDrama.title}》 ចូលក្នុង Queue`);
  } else {
    toast(`⬇️ បានដាក់រឿង 《${ddCurrentDrama.title}》 ចូលក្នុង Queue`);
  }
  updateDdQueueBtn();
};

$("#ddHeaderQueueBtn").onclick = $("#ddHeroQueueBtn").onclick = () => {
  if(!ddCurrentDrama) return;
  const id = ddCurrentDrama.id;
  if(cart[id]){
    removeFromCart(id);
    toast(`លុបរឿង 《${ddCurrentDrama.title}》 ចេញពី Queue`);
  } else {
    const eps = ddAllEps || [];
    addToCart(id, ddCurrentDrama.title, ddCurrentDrama.total || eps.length, ddCurrentDrama.cover, false, ddCurrentDrama.score, 0, '', ddCurrentDrama.title_km);
    toast(`⬇️ បានដាក់រឿង 《${ddCurrentDrama.title}》 ចូលក្នុង Queue`);
  }
  updateDdQueueBtn();
};

$("#ddEpSelectAll").onclick = () => {
  if(!isUserFullAccess()){
    const allowed = (ddAllEps || []).filter(n => n <= 10);
    ddSelectedEps = new Set(allowed);
    renderDramaDetailEpisodes();
    toast("💡 គណនីធម្មតាអាចជ្រើសរើសបានត្រឹមភាគ 1-10 ប៉ុណ្ណោះ។ សូមស្នើសុំ VIP ដើម្បីដោនឡូតគ្រប់ភាគ!");
    return;
  }
  ddSelectedEps = new Set(ddAllEps);
  renderDramaDetailEpisodes();
};

$("#ddEpSelectNone").onclick = () => {
  ddSelectedEps = new Set();
  renderDramaDetailEpisodes();
};

$("#ddEpDlSelected").onclick = () => {
  if(!ddCurrentDrama) return;
  const id = ddCurrentDrama.id;
  const selArr = Array.from(ddSelectedEps);
  if(!isUserFullAccess()){
    const locked = selArr.filter(n => n > 10);
    if(locked.length){
      promptVipModal(locked[0]);
      return;
    }
  }
  if(!selArr.length){
    toast("⚠️ សូមជ្រើសរើសយ៉ាងហោចណាស់ ១ ភាគ");
    return;
  }
  const eps = ddAllEps || [];
  addToCart(id, ddCurrentDrama.title, ddCurrentDrama.total || eps.length, ddCurrentDrama.cover, false, ddCurrentDrama.score, 0, '', ddCurrentDrama.title_km);
  if(cart[id]){
    cart[id].sel = selArr.sort((a,b)=>a-b);
    saveCart();
    renderQueue();
  }
  updateDdQueueBtn();
  toast(`⬇️ បានដាក់ ${selArr.length} ភាគ នៃរឿង 《${ddCurrentDrama.title}》 ចូល Queue`);
};

let ddInlinePlayingEp = 1;

function hidePlayPosterOverlay(){
  const po = $("#ddPlayPosterOverlay");
  if(po){
    po.hidden = true;
    po.classList.add('hidden-play');
    po.style.setProperty('display', 'none', 'important');
    po.style.setProperty('visibility', 'hidden', 'important');
    po.style.setProperty('opacity', '0', 'important');
    po.style.pointerEvents = 'none';
  }
}

function showPlayPosterOverlay(){
  const video = $("#ddInlineVideo");
  // STRICT RULE: If video is playing or has playback progress (currentTime > 0), NEVER show overlay!
  if(video && (!video.paused || video.currentTime > 0)){
    hidePlayPosterOverlay();
    return;
  }
  const po = $("#ddPlayPosterOverlay");
  if(po){
    po.hidden = false;
    po.classList.remove('hidden-play');
    po.style.removeProperty('display');
    po.style.removeProperty('visibility');
    po.style.removeProperty('opacity');
    po.style.display = 'flex';
    po.style.pointerEvents = 'auto';
  }
}

function openInlineLivePlayer(epNum, autoPlay = true){
  if(!ddCurrentDrama) return;
  const drama = ddCurrentDrama;
  const num = Number(epNum) || 1;
  if(isEpisodeLocked(num)){
    promptVipModal(num);
    return;
  }
  ddInlinePlayingEp = num;

  // Update Breadcrumb & Heading
  const bTitle = $("#ddBreadTitle");
  if(bTitle) bTitle.textContent = `《${drama.title_km || drama.title}》 ភាគទី ${num}`;

  const curNumText = $("#ddCurrentEpNumText");
  if(curNumText) curNumText.textContent = `ភាគទី ${num}`;

  const dlCurBtn = $("#ddInlineDlCur");
  if(dlCurBtn) dlCurBtn.textContent = `⬇️ ដោនឡូតភាគ ${num}`;

  // Video element & overlays
  const video = $("#ddInlineVideo");
  const loading = $("#ddInlineLoading");
  const loadText = $("#ddInlineLoadText");

  if(loadText) loadText.textContent = `📺 កំពុងរៀបចំ និងផ្សាយបន្តផ្ទាល់ភាគទី ${num}...`;
  if(loading) loading.hidden = false;
  hidePlayPosterOverlay();

  if(video){
    const tok = localStorage.getItem('syd_auth_token') || '';
    const dev = (window.userAccess && window.userAccess.device_id) || '';
    const streamUrl = `/dl/stream?series_id=${encodeURIComponent(drama.id)}&ep=${num}&token=${encodeURIComponent(tok)}&device_id=${encodeURIComponent(dev)}`;
    video.src = streamUrl;
    video.load();
    if(autoPlay){
      const p = video.play();
      if(p !== undefined){
        p.catch(err => {
          console.log("Autoplay notice:", err);
          if(loading) loading.hidden = true;
          // STRICT RULE: If video is playing or currentTime > 0, NEVER show overlay!
          if(video.paused && video.currentTime === 0){
            showPlayPosterOverlay();
          } else {
            hidePlayPosterOverlay();
          }
        });
      }
    }
  }

  // Update Prev / Next buttons
  const prevBtn = $("#ddInlinePrev");
  const nextBtn = $("#ddInlineNext");
  const maxEp = (ddAllEps && ddAllEps.length) ? Math.max(...ddAllEps) : (drama.total || 9999);
  if(prevBtn) prevBtn.disabled = (num <= 1);
  if(nextBtn) nextBtn.disabled = (num >= maxEp);

  // Switch range tab if necessary
  if(ddAllEps.length > DD_RANGE_SIZE && ddActiveRange !== -1){
    const expRange = Math.floor((num - 1) / DD_RANGE_SIZE);
    if(ddActiveRange !== expRange){
      ddActiveRange = expRange;
      renderDramaDetailEpisodes();
      return;
    }
  }

  // Highlight active chip in grid
  $("#ddEpGrid").querySelectorAll(".dd-epchip-item").forEach(c => {
    const isThis = Number(c.dataset.dei) === num;
    c.classList.toggle("active-playing", isThis);
  });
}

function closeInlinePlayer(){
  const video = $("#ddInlineVideo");
  if(video){
    video.pause();
    video.removeAttribute('src');
    video.load();
  }
  const loading = $("#ddInlineLoading");
  if(loading) loading.hidden = true;
  showPlayPosterOverlay();
}

// Episode Grid Click Handler
$("#ddEpGrid").addEventListener("click", e => {
  const b = e.target.closest("[data-dei]");
  if(!b) return;
  const n = Number(b.dataset.dei);
  if(isEpisodeLocked(n)){
    promptVipModal(n);
    return;
  }
  if(ddMode === 'stream'){
    // Stream mode: immediately play in left video player!
    openInlineLivePlayer(n, true);
    return;
  }
  // Select mode: toggle selection for download
  if(ddSelectedEps.has(n)){
    ddSelectedEps.delete(n);
  } else {
    ddSelectedEps.add(n);
  }
  b.classList.toggle("selected-for-dl", ddSelectedEps.has(n));
  b.setAttribute("aria-pressed", ddSelectedEps.has(n) ? "true" : "false");
  const countEl = $("#ddEpSelectedCount");
  if(countEl) countEl.textContent = `${ddSelectedEps.size}`;
});

// Range Tabs Click Handler
$("#ddEpRanges").addEventListener("click", e => {
  const b = e.target.closest("[data-range]");
  if(!b) return;
  ddActiveRange = Number(b.dataset.range);
  renderDramaDetailEpisodes();
});

// Mode Switchers
const mStreamBtn = $("#ddModeStream");
const mSelectBtn = $("#ddModeSelect");
const selToolbar = $("#ddSelectToolbar");

if(mStreamBtn) mStreamBtn.onclick = () => {
  ddMode = 'stream';
  if(selToolbar) selToolbar.hidden = true;
  renderDramaDetailEpisodes();
};

if(mSelectBtn) mSelectBtn.onclick = () => {
  ddMode = 'select';
  if(selToolbar) selToolbar.hidden = false;
  renderDramaDetailEpisodes();
};

// Video Controls & Events
const inlineVid = $("#ddInlineVideo");
if(inlineVid){
  const eventsToHide = ['play', 'playing', 'timeupdate', 'progress', 'canplay', 'canplaythrough', 'loadeddata', 'seeking', 'seeked'];
  eventsToHide.forEach(ev => {
    inlineVid.addEventListener(ev, () => {
      const l = $("#ddInlineLoading");
      if(l && (ev === 'playing' || ev === 'play' || (ev === 'timeupdate' && inlineVid.currentTime > 0.1))){
        l.hidden = true;
      }
      if(!inlineVid.paused || inlineVid.currentTime > 0){
        hidePlayPosterOverlay();
      }
    });
  });
  inlineVid.addEventListener('pause', () => {
    // When paused mid-video, keep overlay hidden so actor/subtitles aren't blocked!
    const l = $("#ddInlineLoading");
    if(l) l.hidden = true;
    if(inlineVid.currentTime === 0 && !inlineVid.src){
      showPlayPosterOverlay();
    } else {
      hidePlayPosterOverlay();
    }
  });
  inlineVid.addEventListener('error', () => {
    const l = $("#ddInlineLoading");
    if(l) l.hidden = true;
    toast("⚠️ មិនអាចចាក់វីដេអូបានទេ សូមសាកល្បងចុចលេខភាគម្តងទៀត ឬបើកលើ PotPlayer");
  });
  inlineVid.addEventListener('ended', () => {
    if(!ddCurrentDrama || !ddInlinePlayingEp) return;
    const maxEp = (ddAllEps && ddAllEps.length) ? Math.max(...ddAllEps) : (ddCurrentDrama.total || 0);
    if(ddInlinePlayingEp < maxEp){
      openInlineLivePlayer(ddInlinePlayingEp + 1, true);
    }
  });
}

// Poster Click to Play
const playPoster = $("#ddPlayPosterOverlay");
if(playPoster) playPoster.onclick = (e) => {
  e.stopPropagation();
  hidePlayPosterOverlay();
  const video = $("#ddInlineVideo");
  if(video && video.src){
    const p = video.play();
    if(p !== undefined){
      p.catch(err => console.log("Play error:", err));
    }
  } else {
    openInlineLivePlayer(ddInlinePlayingEp || 1, true);
  }
};

// Video Close / Reset Button
const vidCloseBtn = $("#ddVideoCloseBtn");
if(vidCloseBtn) vidCloseBtn.onclick = () => {
  closeInlinePlayer();
};

// Prev / Next Buttons
const inlinePrevBtn = $("#ddInlinePrev");
if(inlinePrevBtn) inlinePrevBtn.onclick = () => {
  if(ddInlinePlayingEp > 1) openInlineLivePlayer(ddInlinePlayingEp - 1, true);
};
const inlineNextBtn = $("#ddInlineNext");
if(inlineNextBtn) inlineNextBtn.onclick = () => {
  const maxEp = (ddAllEps && ddAllEps.length) ? Math.max(...ddAllEps) : (ddCurrentDrama ? ddCurrentDrama.total : 9999);
  if(ddInlinePlayingEp < maxEp) openInlineLivePlayer(ddInlinePlayingEp + 1, true);
};

// Fullscreen
const inlineFsBtn = $("#ddInlineFs");
if(inlineFsBtn) inlineFsBtn.onclick = () => {
  const v = $("#ddInlineVideo");
  if(!v) return;
  if(document.fullscreenElement) document.exitFullscreen();
  else if(v.requestFullscreen) v.requestFullscreen();
  else if(v.webkitRequestFullscreen) v.webkitRequestFullscreen();
};

// PotPlayer / VLC External Player
const inlineSysPlayBtn = $("#ddInlineSysPlay");
if(inlineSysPlayBtn) inlineSysPlayBtn.onclick = async () => {
  if(!ddCurrentDrama || !ddInlinePlayingEp) return;
  toast(`🚀 កំពុងបើកចាក់ភាគទី ${ddInlinePlayingEp} លើ PotPlayer / VLC ខាងក្រៅ...`);
  try {
    const res = await fetch("/dl/stream/play", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ series_id: ddCurrentDrama.id, ep: ddInlinePlayingEp })
    });
    const j = await res.json();
    if(j.ok) toast(`✅ បានបើកភាគទី ${ddInlinePlayingEp} លើ External Player`);
    else toast(`⚠️ ${j.error || "មិនអាចបើកកម្មវិធីខាងក្រៅបានទេ"}`);
  } catch(e) {
    toast(`⚠️ កំហុស: ${e.message}`);
  }
};

// Download Current Episode Button
const inlineDlCurBtn = $("#ddInlineDlCur");
if(inlineDlCurBtn) inlineDlCurBtn.onclick = () => {
  if(!ddCurrentDrama || !ddInlinePlayingEp) return;
  const ep = ddInlinePlayingEp;
  if(isEpisodeLocked(ep)){
    promptVipModal(ep);
    return;
  }
  const id = ddCurrentDrama.id;
  addToCart(id, ddCurrentDrama.title, ddCurrentDrama.total || (ddAllEps && ddAllEps.length) || 1, ddCurrentDrama.cover, false, ddCurrentDrama.score, 0, '', ddCurrentDrama.title_km);
  if(cart[id]){
    cart[id].sel = [ep];
    saveCart();
    renderQueue();
  }
  updateDdQueueBtn();
  toast(`⬇️ បានដាក់ភាគទី ${ep} នៃរឿង 《${ddCurrentDrama.title_km || ddCurrentDrama.title}》 ចូល Queue!`);
};

/* ---------- output folder ---------- */
async function loadDir(){ /* library folder is set via the native picker now — no path input to populate */ }
async function setDir(){
  const p=$("#outdir").value.trim();
  try{
    const j = DEMO ? {ok:true,output_dir:p||"D:\\Dramas"} : await (await fetch("/dl/config",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({output_dir:p})})).json();
    if(j.ok){ $("#dirNote").innerHTML='Saved → <span class="path">'+esc(j.output_dir)+'</span> — episodes land here.'; $("#outdir").value=j.output_dir; toast("Folder saved"); }
    else $("#dirNote").innerHTML='<span class="err">'+esc(j.error||"Couldn't save")+'</span>';
  }catch(e){ $("#dirNote").innerHTML='<span class="err">'+esc(""+e)+'</span>'; }
}
async function openDir(){
  if(DEMO){ toast("Preview mode — on the live app this opens the folder in your file browser"); return; }
  try{
    const j = await (await fetch("/dl/open",{method:"POST"})).json();
    if(j && j.ok && !j.is_cloud && j.action !== 'web_explorer'){
      toast("📁 បានបើកថតវីដេអូលើកុំព្យូទ័រ (PC) រួចរាល់!");
    } else {
      openStorageExplorerModal();
    }
  }catch(e){
    openStorageExplorerModal();
  }
}
async function pickDir(){
  openFolderPickerModal();
}

/* ---------- Library (local downloaded series + active downloading) ---------- */
function getCombinedLibItems(){
  const map = new Map();
  (libItems || []).forEach(x => {
    const key = (x.series_id || x.name || x.title || '').trim();
    if(key) map.set(key, { ...x });
  });

  // Automatically include any series currently downloading/queued in lastStatus or cart:
  if(lastStatus && lastStatus.series){
    const sList = Array.isArray(lastStatus.series) ? lastStatus.series : Object.values(lastStatus.series);
    sList.forEach(s => {
      const sid = String(s.sid || s.series_id || '');
      const c = (typeof cart !== 'undefined' && cart[sid]) ? cart[sid] : {};
      const title = s.title || c.title || sid;
      const total = s.total || c.total || 0;
      const done = s.done || 0;
      const cover = s.cover || c.cover || '';
      const isAct = lastStatus.running && (s.status === 'downloading' || s.status === 'queued');

      let found = null;
      for(const it of map.values()){
        if((it.series_id && String(it.series_id) === sid) || (it.name === title || it.title === title)){
          found = it; break;
        }
      }
      if(found){
        found.series_id = sid;
        found.downloading = isAct;
        found.dlStatus = s.status;
        found.local = Math.max(found.local || 0, done);
        found.total = total || found.total;
        if(!found.cover && cover) found.cover = cover;
      } else if(isAct || done > 0){
        map.set(sid || title, {
          name: title,
          title: title,
          series_id: sid,
          total: total,
          local: done,
          cover: cover,
          downloading: isAct,
          dlStatus: s.status || 'downloading',
          updated: Date.now() / 1000
        });
      }
    });
  }
  return Array.from(map.values());
}

function libCards(items){
  return items.map(x=>{
    const name=x.name, title=x.title||name;
    const total=x.total||0, local=x.local||0;
    const revDeg = total>0 ? Math.max(0,Math.min(1,local/total))*360 : 360;   // completeness reveal (App Store clockwork)
    const grad=`<div class="grad" style="${gradFor(title)}"></div>`;
    let img="";
    if(x.poster) img=`<img src="/dl/poster?name=${encodeURIComponent(name)}" alt="" loading="lazy" onerror="this.remove()">`;
    else if(x.cover) img=`<img src="/img?url=${encodeURIComponent(x.cover)}" alt="" loading="lazy" onerror="this.remove()">`;
    const eps = x.total ? `${x.local}/${x.total}` : `${x.local} eps`;
    const avail = x.new>0 ? `<span class="newbadge" title="${x.new} more episode(s) available — press Update">+${x.new}</span>` : "";
    const isDl = !!x.downloading;
    const fresh = isDl ? `<span class="freshbadge" style="position:absolute;top:8px;left:8px;z-index:6;background:linear-gradient(135deg,#ff6b00,#ff8800);color:#fff;font:800 11px/1 var(--font-km);padding:5px 9px;border-radius:20px;box-shadow:0 4px 12px rgba(255,107,0,.45);display:inline-flex;align-items:center;gap:4px"><span class="spin">⚡</span> កំពុងដោន ${x.local||0}/${x.total||'?'}</span>`
                 : (x.fresh>0 ? `<span class="freshbadge" title="${x.fresh} newly downloaded episode(s) — click to view">${x.fresh} new</span>` : "");
    const score = x.score ? `<span class="score" title="rating">★ ${esc(String(x.score))}</span>` : "";
    return `<div class="poster libcard ${isDl?'act st-'+(x.dlStatus||'downloading'):''}" data-name="${esc(name)}" data-sid="${esc(String(x.series_id||''))}" data-total="${total}" title="Click to see episodes">
      <div class="art">${grad}${img}<div class="dim" style="--rev:${revDeg.toFixed(1)}deg"></div><div class="scrim"></div>
        <div class="dlstate">${isDl ? `${x.local||0} / ${x.total||'?'}` : ''}</div>
        <span class="eps"><span>${eps}</span></span>${avail}${fresh}${score}
      </div>
      <div class="ttl">${esc(title)}</div>
      <div class="libactions">
        <button data-lib-play="${esc(name)}">▶ Play</button>
        <button data-lib-open="${esc(name)}" style="color:var(--accent,#ff9800);font-weight:700" title="បើកទីតាំង Folder នៃរឿងនេះនៅលើ PC Local">📁 បើកថតរឿង</button>
        <button data-lib-update="${esc(name)}">↻ Update</button>
      </div>
    </div>`;
  }).join("");
}
let libItems=[], libSortMode='recent';   // default: Newest downloaded
function _score(x){ const n=parseFloat(x.score); return isNaN(n)?-1:n; }
function sortLibItems(items, mode){
  const arr=items.slice();
  const cmp={
    new:        (a,b)=> (b.fresh-a.fresh) || (b.updated-a.updated),
    recent:     (a,b)=> (b.updated-a.updated),
    rating:     (a,b)=> (_score(b)-_score(a)) || (b.updated-a.updated),
    rating_asc: (a,b)=>{ const x=_score(a),y=_score(b), ax=x<0, ay=y<0; if(ax!==ay) return ax?1:-1; return (x-y)||(b.updated-a.updated); },
    az:         (a,b)=> String(a.title||a.name).localeCompare(String(b.title||b.name)),
  }[mode];
  if(cmp) arr.sort(cmp);
  return arr;
}
function renderLib(){
  const grid=$("#libGrid");
  const all = getCombinedLibItems();
  $("#libCount").textContent = all.length ? ("· "+all.length) : "";
  if(!all.length){ grid.innerHTML='<div class="empty" style="grid-column:1/-1"><div class="big">No downloads yet</div><div class="sm">Download a series and it shows up here.</div></div>'; return; }
  grid.innerHTML = libCards(sortLibItems(all, libSortMode));
}
function sortLib(mode){ libSortMode=mode; renderLib(); }
async function loadLibrary(){
  if(DEMO || ALLOW_DEMO) return;
  try{
    const j = await (await fetch("/dl/library")).json();
    libItems = j.items||[];
    renderLib();
    if(currentTab === "trend" && trendData && trendData.length) renderTrending();
    syncResultButtons();
  }catch(e){}
}
let activeLibSeries = null;
let libEpPollTimer = null;
let currentVpSeries = null;
let currentVpSeriesId = null;
let currentVpTitleKm = '';
let currentVpEp = 1;
let currentVpDownloaded = [];
let currentVpAllEps = [];
let currentVpIsStream = false;
let currentVpTotal = 0;
let currentVpCover = '';
let currentVpScore = '';

async function refreshLibEpisodesLive(){
  if(!activeLibSeries || $("#libEpModal").hidden) return;
  try{
    const j = await (await fetch("/dl/library/episodes?name="+encodeURIComponent(activeLibSeries))).json();
    if(j && !j.error) renderLibEpisodeGrid(j, activeLibSeries);
  }catch(e){}
}

function renderLibEpisodeGrid(j, name){
  $("#libEpTitle").textContent = j.title || name;
  const total = j.total || 0;
  const have = new Set(j.downloaded || []);
  const freshSet = new Set((j.episodes || []).filter(e => e.fresh).map(e => e.index));
  const max = total || (j.downloaded && j.downloaded.length ? Math.max.apply(null, j.downloaded) : 0);
  const zipBtnHtml = dlCount > 0 ? `<a href="/dl/library/zip?name=${encodeURIComponent(name)}" download class="btn accent sm" style="padding:2px 8px;font-size:11px;text-decoration:none;display:inline-flex;align-items:center;gap:4px;margin-left:8px">📦 ទាញយកទាំងអស់ (.ZIP)</a> <button type="button" class="btn primary sm" id="libEpSavePcBtn" style="padding:2px 8px;font-size:11px;display:inline-flex;align-items:center;gap:4px;margin-left:4px">💾 Save ចូល PC</button>` : '';
  $("#libEpSub").innerHTML = `<b>${dlCount}</b> of <b>${total || max || '?'}</b> downloaded ${j.fresh ? (' · <span style="color:var(--good);font-weight:700">+' + j.fresh + ' new</span>') : ''} · <span style="color:var(--accent)">Click episode to play</span> ${zipBtnHtml}`;
  const savePcBtn = $("#libEpSavePcBtn");
  if(savePcBtn){
    savePcBtn.onclick = () => saveSeriesToPc(name, j.title || name);
  }
  
  let html = '';
  for(let i = 1; i <= max; i++){
    const isHave = have.has(i);
    const isFresh = freshSet.has(i);
    const cls = isFresh ? 'libep fresh' : (isHave ? 'libep have' : 'libep miss');
    const title = (isHave || isFresh) ? `Episode ${i} · Click to play` : `Episode ${i} · Not downloaded`;
    html += `<div class="${cls}" data-ep="${i}" title="${title}">${i}</div>`;
  }
  $("#libEpGrid").innerHTML = html || '<div class="sm" style="grid-column:1/-1;padding:24px">No episodes found.</div>';
}

async function openLibEpisodes(name){
  activeLibSeries = name;
  const modal = $("#libEpModal"), grid = $("#libEpGrid");
  $("#libEpTitle").textContent = name;
  $("#libEpSub").textContent = 'Loading episodes…';
  grid.innerHTML = '<div class="sm" style="grid-column:1/-1;color:var(--muted);padding:24px;text-align:center">Loading episodes…</div>';
  modal.hidden = false;
  
  if(libEpPollTimer) clearInterval(libEpPollTimer);
  libEpPollTimer = setInterval(refreshLibEpisodesLive, 1800);
  
  try{
    const j = await (await fetch("/dl/library/episodes?name=" + encodeURIComponent(name))).json();
    if(j.error){ grid.innerHTML = '<div class="sm" style="grid-column:1/-1;padding:24px">' + esc(j.error) + '</div>'; return; }
    renderLibEpisodeGrid(j, name);
    if(j.fresh){
      try{ await fetch("/dl/library/seen", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name }) }); }catch(e){}
      loadLibrary();
    }
  }catch(e){
    grid.innerHTML = '<div class="sm" style="grid-column:1/-1;padding:24px">Couldn\'t load episodes.</div>';
  }
}

function closeLibEp(){
  activeLibSeries = null;
  if(libEpPollTimer){ clearInterval(libEpPollTimer); libEpPollTimer = null; }
  $("#libEpModal").hidden = true;
}
async function scanLib(){ const b=$("#scanLib"); b.disabled=true; await loadLibrary(); b.disabled=false; toast("Library scanned"); }
/* Library Update settings — independent of the new-series download config; persisted locally */
const UB_KEY="hg_ub";
function ubVals(){ return { quality:($("#ubQuality")&&$("#ubQuality").value)||"1080p",
                            speed:Number($("#ubSpeed")&&$("#ubSpeed").value)||2,
                            series:Number($("#ubSeries")&&$("#ubSeries").value)||6 }; }
function loadUB(){ try{ const u=JSON.parse(localStorage.getItem(UB_KEY)||"{}");
  if(u.quality&&$("#ubQuality")) $("#ubQuality").value=u.quality;
  if(u.speed&&$("#ubSpeed")) $("#ubSpeed").value=String(u.speed);
  if(u.series&&$("#ubSeries")) $("#ubSeries").value=String(u.series);
}catch(e){} }
function saveUB(){ try{ localStorage.setItem(UB_KEY, JSON.stringify(ubVals())); }catch(e){} }

async function updateAll(){
  const u=ubVals();
  try{ const j=await (await fetch("/dl/library/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({quality:u.quality,speed:u.speed,series:u.series})})).json();
    toast(j.ok?"Checking your whole library for new episodes…":(j.error||"Couldn't start"), !j.ok);
  }catch(e){ toast("Update failed: "+e, true); }
}
async function updateOne(name){
  const u=ubVals();
  try{ const j=await (await fetch("/dl/library/update",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({names:[name],quality:u.quality,speed:u.speed,series:u.series})})).json();
    toast(j.ok?("Checking “"+name+"” for new episodes…"):(j.error||"Couldn't start"), !j.ok);
  }catch(e){ toast("Update failed: "+e, true); }
}

/* Live per-card progress during a Library update: the iOS clockwork poster reveal + state chip.
   Updates cards in place (no re-render) so the reveal animates smoothly across polls. */
function applyLiveToLibrary(status){
  const grid=$("#libGrid"); if(!grid) return;
  (status.series||[]).forEach(s=>{
    const sid=String(s.sid||""); if(!sid) return;
    const card=grid.querySelector('.libcard[data-sid="'+(window.CSS&&CSS.escape?CSS.escape(sid):sid)+'"]');
    if(!card) return;
    card.classList.add('act');
    const dim=card.querySelector('.dim');
    if(dim) dim.style.setProperty('--rev',(Math.max(0,Math.min(1,s.frac||0))*360).toFixed(1)+'deg');
    const st=s.state||s.status||'';
    ['st-queued','st-downloading','st-done','st-error'].forEach(c=>card.classList.remove(c));
    if(st) card.classList.add('st-'+st);
    const total=Number(card.dataset.total)||s.total||0;
    const ds=card.querySelector('.dlstate');
    if(ds) ds.textContent = st==='downloading' ? (s.done+' / '+(total||'?'))
                          : st==='queued' ? 'Queued'
                          : st==='done' ? '✓ Updated'
                          : st==='error' ? 'Failed' : st;
    const epsEl=card.querySelector('.eps > span');
    if(epsEl && total) epsEl.textContent = s.done+'/'+total;
  });
}
async function openSeries(name){
  if(!name) return;
  try{
    toast(`⏳ កំពុងបើកថតរឿង...`);
    const j = await (await fetch("/dl/library/open",{
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    })).json();
    if(j && j.ok){
      toast(`📁 បានបើកថតរឿង: ${j.folder || name}`);
    } else {
      toast(`⚠️ ${j.error || "រកមិនឃើញថតរឿងនេះទេ"}`, true);
      openLibEpisodes(name);
    }
  }catch(e){
    toast("បរាជ័យក្នុងការបើកថត: " + (e.message || e), true);
    openLibEpisodes(name);
  }
}
async function playSeriesExternal(name, ep){
  try{
    const body = { name };
    if(ep != null) body.ep = Number(ep);
    const j = await (await fetch("/dl/library/play", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })).json();
    if(j.ok) toast("Playing in system player: " + (j.file || name));
    else toast(j.error || "Couldn't play this series", true);
  }catch(e){ toast("Play failed: " + e, true); }
}

async function playSeries(name){
  openVideoPlayer(name, 1);
}

async function openVideoPlayer(seriesName, epNum, opts = {}){
  const modal = $("#videoPlayerModal");
  const video = $("#vpVideo");
  const loadOverlay = $("#vpLoadingOverlay");
  const loadText = $("#vpLoadText");
  const loadSub = $("#vpLoadSub");
  
  const isStream = (opts && (opts.isStream || opts.seriesId)) ? true : false;
  currentVpIsStream = isStream;
  currentVpSeries = seriesName || (ddCurrentDrama ? ddCurrentDrama.title : '') || '';
  if(opts && opts.seriesId) currentVpSeriesId = opts.seriesId;
  if(opts && opts.titleKm !== undefined) currentVpTitleKm = opts.titleKm;
  if(opts && opts.allEps) currentVpAllEps = opts.allEps;
  if(opts && opts.total) currentVpTotal = opts.total;
  if(opts && opts.cover) currentVpCover = opts.cover;
  if(opts && opts.score) currentVpScore = opts.score;

  if(!currentVpIsStream){
    try{
      const j = await (await fetch("/dl/library/episodes?name=" + encodeURIComponent(seriesName))).json();
      currentVpDownloaded = (j.downloaded || []).sort((a,b) => a - b);
    }catch(e){
      currentVpDownloaded = [];
    }
  }

  if(!epNum || isNaN(epNum)){
    if(currentVpIsStream){
      epNum = (currentVpAllEps && currentVpAllEps.length) ? currentVpAllEps[0] : 1;
    } else {
      epNum = currentVpDownloaded.length ? currentVpDownloaded[0] : 1;
    }
  }
  currentVpEp = Number(epNum);

  updateVpControls();

  let streamUrl = '';
  if(currentVpIsStream){
    streamUrl = `/stream?series_id=${encodeURIComponent(currentVpSeriesId || '')}&ep=${currentVpEp}&quality=1080p`;
    if(loadOverlay){
      loadOverlay.hidden = false;
      if(loadText) loadText.textContent = `📺 កំពុងរៀបចំ និងផ្សាយបន្តផ្ទាល់ភាគទី ${currentVpEp}...`;
      if(loadSub) loadSub.innerHTML = `⚡ Server កំពុង Decrypt និងបញ្ជូនវីដេអូកម្រិត 1080p Full HD (សូមរង់ចាំបន្តិច)`;
    }
  } else {
    streamUrl = `/dl/library/video?name=${encodeURIComponent(seriesName)}&ep=${currentVpEp}`;
    if(loadOverlay) loadOverlay.hidden = true;
  }

  video.src = streamUrl;
  modal.hidden = false;
  video.load();
  video.play().catch(e => console.log('Autoplay:', e));
}

function updateVpControls(){
  const dispTitle = currentVpTitleKm || currentVpSeries || 'Video';
  const origTitle = (currentVpTitleKm && currentVpSeries && currentVpTitleKm !== currentVpSeries) ? ` (${currentVpSeries})` : '';

  $("#vpTitle").textContent = `《${dispTitle}》 ភាគទី ${currentVpEp}${origTitle}`;

  const dlAllBtn = $("#vpDlAllBtn");
  const dlCurBtn = $("#vpDlCurBtn");
  const queueBtn = $("#vpQueueBtn");
  const fixPicBtn = $("#vpFixPic");

  let epList = [];
  if(currentVpIsStream){
    const tot = currentVpTotal || (currentVpAllEps && currentVpAllEps.length) || 0;
    $("#vpSub").innerHTML = `<span style="display:inline-flex;align-items:center;gap:6px"><span style="color:#ef4444;animation:vpPulse 1.5s infinite">●</span> <strong>ផ្សាយផ្ទាល់អនឡាញ (Online Live Stream · 1080p)</strong> · ភាគ ${currentVpEp} ${tot ? `នៃ ${tot}` : ''}</span>`;
    if(dlAllBtn) dlAllBtn.hidden = false;
    if(dlCurBtn){ dlCurBtn.hidden = false; dlCurBtn.textContent = `⬇️ ដោនឡូតភាគ ${currentVpEp}`; }
    if(queueBtn) queueBtn.hidden = false;
    if(fixPicBtn) fixPicBtn.hidden = true;
    epList = (currentVpAllEps && currentVpAllEps.length) ? currentVpAllEps : (currentVpTotal ? Array.from({length: currentVpTotal}, (_, i) => i + 1) : [currentVpEp]);
  } else {
    $("#vpSub").textContent = `💾 1080p Playback · Episode ${currentVpEp}`;
    if(dlAllBtn) dlAllBtn.hidden = true;
    if(dlCurBtn){
      dlCurBtn.hidden = false;
      dlCurBtn.textContent = `⬇️ ទាញយកភាគ ${currentVpEp} ទៅ PC`;
      dlCurBtn.title = "ទាញយកឯកសារ MP4 មកកាន់កុំព្យូទ័ររបស់អ្នក";
      dlCurBtn.onclick = () => {
        window.open(`/dl/library/video?name=${encodeURIComponent(currentVpSeries)}&ep=${currentVpEp}&download=1`, '_blank');
      };
    }
    if(queueBtn) queueBtn.hidden = true;
    if(fixPicBtn) fixPicBtn.hidden = false;
    epList = currentVpDownloaded || [];
  }

  const curIdx = epList.indexOf(currentVpEp);
  const prevIdx = curIdx - 1;
  const nextIdx = (curIdx >= 0 && curIdx < epList.length - 1) ? curIdx + 1 : -1;

  const prevBtn = $("#vpPrev");
  const nextBtn = $("#vpNext");
  if(prevBtn) prevBtn.disabled = curIdx <= 0;
  if(nextBtn) nextBtn.disabled = nextIdx < 0;

  const sel = $("#vpEpSelector");
  if(sel){
    sel.innerHTML = epList.map(i => {
      const isCur = i === currentVpEp;
      const bg = isCur ? 'linear-gradient(120deg,var(--accent),var(--accent-2))' : 'var(--surface-2)';
      const col = isCur ? 'var(--on-accent)' : 'var(--ink-2)';
      const weight = isCur ? '700' : '500';
      return `<button type="button" class="btn sm vp-ep-btn" data-vpep="${i}" style="padding:4px 9px;font-size:11.5px;min-width:34px;background:${bg};color:${col};font-weight:${weight};border-radius:6px;flex-shrink:0;cursor:pointer">${i}</button>`;
    }).join('');
    setTimeout(() => {
      const act = sel.querySelector(`button[data-vpep="${currentVpEp}"]`);
      if(act) act.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }, 80);
  }
}

function closeVideoPlayer(){
  const modal = $("#videoPlayerModal");
  const video = $("#vpVideo");
  if(video){
    video.pause();
    video.removeAttribute('src');
    video.load();
  }
  const loadOverlay = $("#vpLoadingOverlay");
  if(loadOverlay) loadOverlay.hidden = true;
  modal.hidden = true;
}

/* ---------- poll ---------- */
let _wasRunning=false;
let _dlTick=0;
async function poll(){
  try{
    lastStatus = DEMO ? demoStatus() : await (await fetch("/dl/status")).json();
    try{ renderQueue(); }catch(e_q){ console.error("renderQueue error:", e_q); }
    // Immediate Library: while downloads or updates run, live update the Library so posters show up automatically!
    if(lastStatus.running){
      applyLiveToLibrary(lastStatus);
      if(lastStatus.mode==="download"){
        if(++_dlTick % 2 === 0) renderLib();
        if(!$("#libEpModal").hidden && activeLibSeries){ refreshLibEpisodesLive(); }
      }
    } else { _dlTick=0; }
    // Library update: scan notice board
    const libScan=$("#libScan");
    if(lastStatus.mode==="library" && lastStatus.running){
      if(libScan){ libScan.hidden=false;
        libScan.innerHTML='<span class="lsdot"></span>Checking library… <b>'+(lastStatus.checked||0)+'/'+(lastStatus.to_check||0)+'</b> checked · <b>'+(lastStatus.found||0)+'</b> with new episodes'; }
    } else if(libScan){ libScan.hidden=true; }
    const log=(lastStatus.log||[]);
    const logEl=$("#log"); if(logEl){ logEl.textContent = log.join("\n")||"—"; logEl.scrollTop=logEl.scrollHeight; }
    const logHint=$("#logHint"); if(logHint) logHint.textContent = lastStatus.running ? "running" : (log.length?log.length+" lines":"");
    $("#cancelBtn").disabled=!lastStatus.running;
    const running=!!lastStatus.running;                        // background-activity animation
    $("#bgWork").classList.toggle("on", running);
    $("#bgBar").hidden = !running;
    if(_wasRunning && !lastStatus.running){
      loadLibrary();
      toast("✅ ការទាញយកបានបញ្ចប់ដោយជោគជ័យ! វីដេអូត្រូវបានរក្សាទុកក្នុង Folder រួចរាល់។");
    }
    _wasRunning = !!lastStatus.running;
  }catch(e){ if(!DEMO && ALLOW_DEMO){ DEMO=true; seedDemo(); } }   // localhost: keep retrying the real backend
}

/* ---------- events ---------- */
document.addEventListener("click", e=>{
  const lsp = e.target.closest("[data-lib-save-pc]");
  if(lsp){
    const sname = lsp.dataset.libSavePc;
    const item = (libItems || []).find(x => (x.name === sname || x.title === sname));
    saveSeriesToPc(sname, item ? (item.title || item.title_km || sname) : sname);
    return;
  }
  const qsp = e.target.closest("[data-q-save-pc]");
  if(qsp){
    const id = qsp.dataset.qSavePc;
    const c = cart[id] || {};
    const smap = {}; ((lastStatus && lastStatus.series) || []).forEach(s => smap[s.sid] = s);
    const s = smap[id];
    const sName = (s && (s.title || s.name)) || c.title || id;
    const tkm = c.title_km || (s && s.title_km) || sName;
    saveSeriesToPc(sName, tkm);
    return;
  }
  const pep = e.target.closest("[data-pep]");
  if(pep){
    e.stopPropagation();
    const p = pep.closest(".poster");
    openDramaDetail(pep.dataset.pep, p);
    return;
  }
  const pdl = e.target.closest("[data-pdl]");
  if(pdl){
    e.stopPropagation();
    const p = pdl.closest(".poster");
    if(!p) return;
    const id = p.dataset.id;
    if(cart[id]){
      removeFromCart(id);
      toast(`លុបរឿង 《${p.dataset.t}》 ចេញពី Queue`);
    } else {
      const libMap = getLibMap();
      const libEntry = libMap[id] || (p.dataset.t ? libMap[p.dataset.t.trim()] : null);
      if(libEntry && (libEntry.local > 0 || libEntry.completed) && !e.shiftKey){
        showAlreadyDownloadedModal(p, libEntry);
      } else {
        addToCart(id, p.dataset.t, Number(p.dataset.n), p.dataset.cov, false, p.dataset.sc, Number(p.dataset.rk)||0, p.dataset.dt||'', p.dataset.tkm||'');
        toast(`⬇️ បានដាក់រឿង 《${p.dataset.t}》 ចូល Queue`);
      }
    }
    return;
  }
  const lu=e.target.closest("[data-lib-update]"), lo=e.target.closest("[data-lib-open]"), lp=e.target.closest("[data-lib-play]");
  const qof=e.target.closest("[data-open-folder]");
  if(qof){ e.stopPropagation(); openSeries(qof.dataset.openFolder); return; }
  if(lp){ playSeries(lp.dataset.libPlay); return; }
  if(lu){ updateOne(lu.dataset.libUpdate); return; }
  if(lo){ openSeries(lo.dataset.libOpen); return; }
  const p=e.target.closest(".poster"); const rm=e.target.closest("[data-rm]"); const ep=e.target.closest("[data-ep]");
  if(ep){
    const pParent = ep.closest(".poster");
    openDramaDetail(ep.dataset.ep, pParent);
    return;
  }
  if(p && p.classList.contains("libcard") && !e.target.closest(".libactions")){ openLibEpisodes(p.dataset.name); return; }
  if(p && !p.classList.contains("libcard") && !e.target.closest(".posteractions")){
    openDramaDetail(p.dataset.id, p);
    return;
  }
  const redl = e.target.closest("[data-redl]");
  if(redl){ redownloadQueueItem(redl.dataset.redl); return; }
  if(rm){ removeFromCart(rm.dataset.rm); }
});

document.addEventListener("change", e => {
  const tick = e.target.closest(".q-tick");
  if(tick && tick.dataset.tick){
    const id = tick.dataset.tick;
    if(cart[id]){
      cart[id].checked = tick.checked;
      saveCart();
      const row = tick.closest(".row");
      if(row) row.classList.toggle("unticked", !tick.checked);
      updateDock();
    }
  }
});

const clDone = $("#clearDoneBtn"); if(clDone) clDone.onclick = clearDoneFromQueue;
const clAll = $("#clearQueue"); if(clAll) clAll.onclick = clearAllQueue;
const tgTicks = $("#toggleAllTicks"); if(tgTicks) tgTicks.onclick = toggleAllTicks;

/* #2 diagnostics / troubleshoot console (Ctrl+Shift+D) */
async function openDiag(){
  const m=$("#diagModal"), body=$("#diagBody"); m.hidden=false; body.textContent="Loading…";
  try{
    const d=await (await fetch("/dl/diag")).json();
    const lines=[
      "Hongguo Downloader — diagnostics", "time: "+new Date().toISOString(),
      "server pid: "+d.pid+"   web port: "+d.web_port+" ("+(d.bind_host||"?")+")   python: "+d.python,
      "signer: "+(d.sign_server||"?")+"   healthy: "+(d.signer_healthy?"YES":"NO"),
      "output dir: "+d.output_dir,
      "output writable: "+(d.output_writable?"YES":"NO — "+(d.output_write_error||"read-only?")),
      "state dir: "+d.state_dir, "data dir: "+d.data_dir,
      "download running: "+(d.running?("yes ("+(d.mode||"")+")"):"no"),
      "", "── launch / app.log ──", ...((d.app_log)||[]),
      "", "── download log ──", ...((d.dl_log)||[]),
    ];
    body.textContent=lines.join("\n");
  }catch(e){ body.textContent="Couldn't load diagnostics: "+e; }
}
$("#diagClose").onclick=()=>{ $("#diagModal").hidden=true; };
$("#diagRefresh").onclick=openDiag;
$("#diagCopy").onclick=()=>{ try{ navigator.clipboard.writeText($("#diagBody").textContent); toast("Diagnostics copied"); }catch(e){ toast("Copy failed",true); } };
document.addEventListener("keydown",e=>{ if((e.ctrlKey||e.metaKey)&&e.shiftKey&&(e.key==="D"||e.key==="d")){ e.preventDefault(); openDiag(); } });
$("#startBtn").onclick=start; $("#cancelBtn").onclick=cancel;

// Side queue drawer controls
const sqClose = $("#sideQueueCloseBtn"); if(sqClose) sqClose.onclick = closeSideQueue;
const sqBdrop = $("#sideQueueBackdrop"); if(sqBdrop) sqBdrop.onclick = closeSideQueue;
const sqFloat = $("#sideQueueFloatBtn"); if(sqFloat) sqFloat.onclick = toggleSideQueue;
const sqStart = $("#sqStartBtn"); if(sqStart) sqStart.onclick = start;
const sqCancel = $("#sqCancelBtn"); if(sqCancel) sqCancel.onclick = cancel;

// Quality / speed / series sync between dock and side drawer
const sqQ = $("#sqQuality");
if(sqQ){
  sqQ.onchange = () => { if($("#quality")) $("#quality").value = sqQ.value; };
  if($("#quality")) $("#quality").addEventListener("change", () => { sqQ.value = $("#quality").value; });
}
const sqC = $("#sqConc");
if(sqC){
  sqC.onchange = () => { if($("#conc")) $("#conc").value = sqC.value; };
  if($("#conc")) $("#conc").addEventListener("change", () => { sqC.value = $("#conc").value; });
}
const sqSAO = $("#sqSeriesAtOnce");
if(sqSAO){
  sqSAO.onchange = () => { if($("#seriesAtOnce")) $("#seriesAtOnce").value = sqSAO.value; };
  if($("#seriesAtOnce")) $("#seriesAtOnce").addEventListener("change", () => { sqSAO.value = $("#seriesAtOnce").value; });
}

// Side queue drawer save folder buttons
const sqPickF = $("#sqPickFolderBtn"); if(sqPickF) sqPickF.onclick = pickDir;
const sqOpenF = $("#sqOpenFolderBtn"); if(sqOpenF) sqOpenF.onclick = openDir;
async function syncSqFolder(){
  const savedPcPath = localStorage.getItem("syd_user_pc_path") || "F:\\Hongguo";
  const el = $("#sqFolderPath");
  if(el){
    el.textContent = savedPcPath;
    el.title = `ទីតាំង Folder លើ PC: ${savedPcPath}`;
  }
  if($("#dirPath")) $("#dirPath").textContent = savedPcPath;
  if($("#ucFolderPath")) $("#ucFolderPath").textContent = savedPcPath;

  try{
    const res = await (await fetch("/dl/config")).json();
    if(res){
      IS_CLOUD = false;
      if(!localStorage.getItem("syd_user_pc_path") && res.output_dir && !res.output_dir.startsWith('/app')){
        localStorage.setItem("syd_user_pc_path", res.output_dir);
        if(el) el.textContent = res.output_dir;
        if($("#dirPath")) $("#dirPath").textContent = res.output_dir;
        if($("#ucFolderPath")) $("#ucFolderPath").textContent = res.output_dir;
      }
    }
  }catch(e){}
}
syncSqFolder();

// Close drawer on Escape
document.addEventListener("keydown", e => {
  if(e.key === "Escape"){
    const drawer = $("#sideQueueDrawer");
    if(drawer && drawer.classList.contains("open")) closeSideQueue();
  }
});
if($("#openDir")) $("#openDir").onclick=openDir;
if($("#setFolderToggle")) $("#setFolderToggle").onclick=pickDir;
$("#scanLib").onclick=scanLib; $("#updateLib").onclick=updateAll;
["ubQuality","ubSpeed","ubSeries"].forEach(id=>{ const el=$("#"+id); if(el) el.onchange=saveUB; });
/* ⚙ Settings toggle removed — Quality/Speed/Series are always visible in the library header now. */
$("#libEpClose").onclick=$("#libEpCloseB").onclick=closeLibEp;
$("#libEpModal").addEventListener('click',e=>{ if(e.target===$("#libEpModal")) closeLibEp(); });

$("#libEpGrid").addEventListener('click', e => {
  const epEl = e.target.closest(".libep");
  if(!epEl) return;
  const epNum = Number(epEl.dataset.ep);
  if(epEl.classList.contains("have") || epEl.classList.contains("fresh")){
    if(activeLibSeries && epNum){
      openVideoPlayer(activeLibSeries, epNum);
    }
  } else {
    toast(`Episode ${epNum} is not downloaded yet`, true);
  }
});

const libPlayBtn = $("#libEpPlayBtn");
if(libPlayBtn) libPlayBtn.onclick = () => { if(activeLibSeries) openVideoPlayer(activeLibSeries, 1); };

$("#vpClose").onclick = $("#vpCloseB").onclick = closeVideoPlayer;
$("#videoPlayerModal").addEventListener('click', e => {
  if(e.target === $("#videoPlayerModal")) closeVideoPlayer();
});

$("#vpSysPlay").onclick = async () => {
  if(currentVpIsStream && currentVpSeriesId){
    toast(`🚀 កំពុងបើកភាគ ${currentVpEp} លើ External Player (PotPlayer/VLC)...`);
    try {
      const res = await (await fetch("/dl/stream/play", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ series_id: currentVpSeriesId, ep: currentVpEp })
      })).json();
      if(!res.ok) toast("External Player: " + (res.error || "មិនអាចបើកបាន"), true);
      else toast("កំពុងចាក់ផ្សាយលើ External Player: " + (res.file || ""));
    } catch(e){
      toast("Launch external failed: " + e, true);
    }
  } else if(currentVpSeries){
    playSeriesExternal(currentVpSeries, currentVpEp);
  }
};

function getActiveVpEpList(){
  if(currentVpIsStream){
    return (currentVpAllEps && currentVpAllEps.length) ? currentVpAllEps : (currentVpTotal ? Array.from({length: currentVpTotal}, (_, i) => i + 1) : [currentVpEp]);
  }
  return currentVpDownloaded || [];
}

$("#vpPrev").onclick = () => {
  const epList = getActiveVpEpList();
  const curIdx = epList.indexOf(currentVpEp);
  if(curIdx > 0){
    openVideoPlayer(currentVpSeries, epList[curIdx - 1], {
      isStream: currentVpIsStream,
      seriesId: currentVpSeriesId,
      titleKm: currentVpTitleKm,
      allEps: currentVpAllEps,
      total: currentVpTotal,
      cover: currentVpCover,
      score: currentVpScore
    });
  }
};

$("#vpNext").onclick = () => {
  const epList = getActiveVpEpList();
  const curIdx = epList.indexOf(currentVpEp);
  if(curIdx >= 0 && curIdx < epList.length - 1){
    openVideoPlayer(currentVpSeries, epList[curIdx + 1], {
      isStream: currentVpIsStream,
      seriesId: currentVpSeriesId,
      titleKm: currentVpTitleKm,
      allEps: currentVpAllEps,
      total: currentVpTotal,
      cover: currentVpCover,
      score: currentVpScore
    });
  }
};

$("#vpEpSelector").addEventListener('click', e => {
  const btn = e.target.closest("[data-vpep]");
  if(btn && (currentVpSeries || currentVpSeriesId)){
    openVideoPlayer(currentVpSeries, Number(btn.dataset.vpep), {
      isStream: currentVpIsStream,
      seriesId: currentVpSeriesId,
      titleKm: currentVpTitleKm,
      allEps: currentVpAllEps,
      total: currentVpTotal,
      cover: currentVpCover,
      score: currentVpScore
    });
  }
});

const vpDlAll = $("#vpDlAllBtn");
if(vpDlAll) vpDlAll.onclick = () => {
  if(!currentVpSeriesId) return;
  const eps = (currentVpAllEps && currentVpAllEps.length) ? currentVpAllEps : Array.from({length: currentVpTotal || 24}, (_, i) => i + 1);
  addToCart(currentVpSeriesId, currentVpSeries, currentVpTotal || eps.length, currentVpCover, false, currentVpScore, 0, '', currentVpTitleKm);
  if(cart[currentVpSeriesId]){
    cart[currentVpSeriesId].sel = eps;
    saveCart();
    renderQueue();
  }
  toast(`⬇️ បានដាក់រឿង 《${currentVpTitleKm || currentVpSeries}》 គ្រប់ភាគទាំងអស់ចូល Queue រួចរាល់!`);
};

const vpDlCur = $("#vpDlCurBtn");
if(vpDlCur) vpDlCur.onclick = () => {
  if(!currentVpSeriesId) return;
  addToCart(currentVpSeriesId, currentVpSeries, currentVpTotal || 1, currentVpCover, false, currentVpScore, 0, '', currentVpTitleKm);
  if(cart[currentVpSeriesId]){
    cart[currentVpSeriesId].sel = [currentVpEp];
    saveCart();
    renderQueue();
  }
  toast(`⬇️ បានដាក់ភាគទី ${currentVpEp} នៃរឿង 《${currentVpTitleKm || currentVpSeries}》 ចូល Queue!`);
};

const vpQueue = $("#vpQueueBtn");
if(vpQueue) vpQueue.onclick = () => {
  if(!currentVpSeriesId) return;
  const eps = (currentVpAllEps && currentVpAllEps.length) ? currentVpAllEps : Array.from({length: currentVpTotal || 24}, (_, i) => i + 1);
  addToCart(currentVpSeriesId, currentVpSeries, currentVpTotal || eps.length, currentVpCover, false, currentVpScore, 0, '', currentVpTitleKm);
  toast(`➕ បានដាក់រឿង 《${currentVpTitleKm || currentVpSeries}》 ចូល Queue!`);
};

const vpVid = $("#vpVideo");
if(vpVid){
  vpVid.addEventListener('canplay', () => {
    const loadOverlay = $("#vpLoadingOverlay");
    if(loadOverlay) loadOverlay.hidden = true;
  });
  vpVid.addEventListener('playing', () => {
    const loadOverlay = $("#vpLoadingOverlay");
    if(loadOverlay) loadOverlay.hidden = true;
  });
  vpVid.addEventListener('error', () => {
    const loadOverlay = $("#vpLoadingOverlay");
    if(loadOverlay && currentVpIsStream){
      loadOverlay.hidden = false;
      const loadText = $("#vpLoadText");
      const loadSub = $("#vpLoadSub");
      if(loadText) loadText.textContent = `⚠️ មិនអាចចាក់ផ្សាយភាគទី ${currentVpEp} បានទេ`;
      if(loadSub) loadSub.innerHTML = `<button class="btn accent sm" onclick="openVideoPlayer(currentVpSeries, currentVpEp, {isStream:true, seriesId:currentVpSeriesId, titleKm:currentVpTitleKm, allEps:currentVpAllEps, total:currentVpTotal, cover:currentVpCover, score:currentVpScore})" style="margin-top:8px">🔄 ព្យាយាមម្តងទៀត (Retry)</button>`;
    }
  });
  vpVid.addEventListener('ended', () => {
    const epList = getActiveVpEpList();
    const curIdx = epList.indexOf(currentVpEp);
    if(curIdx >= 0 && curIdx < epList.length - 1){
      const nextEp = epList[curIdx + 1];
      toast(`▶️ កំពុងចាក់ផ្សាយភាគទី ${nextEp} បន្ត...`);
      setTimeout(() => {
        openVideoPlayer(currentVpSeries, nextEp, {
          isStream: currentVpIsStream,
          seriesId: currentVpSeriesId,
          titleKm: currentVpTitleKm,
          allEps: currentVpAllEps,
          total: currentVpTotal,
          cover: currentVpCover,
          score: currentVpScore
        });
      }, 500);
    }
  });
}

document.addEventListener('keydown', e => {
  const vpModal = $("#videoPlayerModal");
  if(!vpModal || vpModal.hidden) return;
  const video = $("#vpVideo");
  if(e.key === 'Escape'){ closeVideoPlayer(); return; }
  if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if(e.code === 'Space'){ e.preventDefault(); if(video.paused) video.play(); else video.pause(); }
  else if(e.key === 'ArrowRight'){ e.preventDefault(); video.currentTime = Math.min(video.duration || 0, video.currentTime + 5); }
  else if(e.key === 'ArrowLeft'){ e.preventDefault(); video.currentTime = Math.max(0, video.currentTime - 5); }
  else if(e.key === 'f' || e.key === 'F'){ e.preventDefault(); if(document.fullscreenElement) document.exitFullscreen(); else video.requestFullscreen().catch(()=>{}); }
  else if(e.key === 'n' || e.key === 'N'){ e.preventDefault(); $("#vpNext").click(); }
  else if(e.key === 'p' || e.key === 'P'){ e.preventDefault(); $("#vpPrev").click(); }
});

/* ---------- Refresh, Restart & User Control Handlers ---------- */
async function doAppRefresh() {
  toast("🔄 Fetching latest dramas & posters from Hongguo live…");
  try {
    const refreshTask = currentTab === "explorer"
      ? loadExplorer(expPage || 1)
      : loadTrending(null, trendPage, true);
    await Promise.all([
      refreshTask,
      loadLibrary(),
      loadHistory(),
      poll()
    ]);
    toast(currentTab === "explorer" ? "✅ Catalog refreshed!" : `✅ Live refresh complete on Page ${trendPage}!`);
  } catch(e) {
    toast("Refresh error: " + e, true);
  }
}
const topRef = $("#topRefreshBtn"); if(topRef) topRef.onclick = doAppRefresh;
const ucRef = $("#ucRefreshApp"); if(ucRef) ucRef.onclick = doAppRefresh;

const ucRestartBtn = $("#ucAdminRestartUpdate");
if(ucRestartBtn){
  ucRestartBtn.onclick = async function() {
    if(!confirm("តើអ្នកពិតជាចង់ទាញយកកូដថ្មីពី Git (Git Pull) និង Restart App ឡើងវិញមែនទេ?")) return;
    ucRestartBtn.disabled = true;
    ucRestartBtn.innerHTML = "⏳ កំពុងទាញកូដថ្មី & Restart...";
    toast("⏳ កំពុងទាញយកកូដថ្មីពី Git និង Restart App...", "good");
    try {
      const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || '8888';
      const token = (window.userAccess && window.userAccess.token) || '';
      const res = await fetch('/dl/restart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin: pin, token: token, action: 'update_restart' })
      });
      const data = await res.json();
      if(data.ok){
        toast("🚀 " + (data.message || "Restart ជោគជ័យ!"), "good");
        setTimeout(() => { window.location.reload(); }, 2500);
      } else {
        toast("❌ " + (data.error || "បរាជ័យ"), true);
        ucRestartBtn.disabled = false;
        ucRestartBtn.innerHTML = "🚀 Restart App & ទាញកូដថ្មី (Update Code & Restart)";
      }
    } catch(e) {
      toast("🚀 កំពុងដំណើរការ Restart... ទំព័រនឹងផ្ទុកឡើងវិញក្នុងពេលបន្តិចទៀត", "good");
      setTimeout(() => { window.location.reload(); }, 3000);
    }
  };
}

let _hasAlertedNewVersion = false;
async function checkAppAutoUpdate() {
  try {
    const res = await fetch('/dl/update-check');
    if(!res.ok) return;
    const d = await res.json();
    _lastUpdateData = d;
    const btn = $("#topAutoUpdateBtn");
    const txt = $("#topAutoUpdateText");
    if(!btn) return;
    
    if(d.has_update) {
      btn.style.display = "inline-flex";
      if(txt) txt.textContent = d.latest_commit ? `Auto Update (${d.latest_commit})` : 'Auto Update ថ្មី';
      btn.title = `មានកំណែថ្មីនៅលើ GitHub!\nCommit: ${d.latest_commit}\nសារ: ${d.commit_message || 'New update'}\nកាលបរិច្ឆេទ: ${d.commit_date || ''}\nចុចដើម្បីទាញយក និង Replace កូដថ្មីដោយស្វ័យប្រវត្តិ`;
      
      if(!_hasAlertedNewVersion){
        _hasAlertedNewVersion = true;
        toast(`🚀 មានកំណែថ្មីនៅលើ GitHub (${d.latest_commit || 'New'})! សូមចុចប៊ូតុង "Auto Update" ដើម្បីទាញយកដោយស្វ័យប្រវត្តិ`, false);
      }
    } else {
      btn.style.display = "none";
      _hasAlertedNewVersion = false;
    }
  } catch(e) {
    // Ignore offline/network errors
  }
}

const topAutoUpdateBtn = $("#topAutoUpdateBtn");
if(topAutoUpdateBtn) {
  topAutoUpdateBtn.onclick = async function() {
    const info = _lastUpdateData || {};
    const commitMsg = info.commit_message ? `\n\n📌 កំណែថ្មី: "${info.commit_message}" (${info.latest_commit || ''})` : '';
    const dateStr = info.commit_date ? `\n📅 កាលបរិច្ឆេទ: ${info.commit_date}` : '';
    const confirmMsg = `តើអ្នកពិតជាចង់ធ្វើបច្ចុប្បន្នភាព (Auto Update) កម្មវិធីឥឡូវនេះមែនទេ?${commitMsg}${dateStr}\n\n⚙️ ប្រព័ន្ធនឹងទាញយកកូដថ្មីពី GitHub Replace ឯកសារដោយស្វ័យប្រវត្តិ រួច Restart App ឡើងវិញ។`;
    
    if(!confirm(confirmMsg)) return;
    
    topAutoUpdateBtn.disabled = true;
    topAutoUpdateBtn.innerHTML = `⏳ កំពុង Update...`;
    toast("⏳ កំពុងទាញយកកូដថ្មីពី GitHub និង Replace Files...", "good");
    
    try {
      const res = await fetch('/dl/update-apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'auto_update' })
      });
      const data = await res.json();
      if(data.ok) {
        toast("🚀 " + (data.message || "Update ជោគជ័យ! កំពុង Restart App..."), "good");
        topAutoUpdateBtn.innerHTML = `✅ Update រួចរាល់`;
        setTimeout(() => { window.location.reload(); }, 3500);
      } else {
        toast("❌ " + (data.error || "Update បរាជ័យ"), true);
        topAutoUpdateBtn.disabled = false;
        topAutoUpdateBtn.innerHTML = `⚡ Auto Update ថ្មី`;
      }
    } catch(err) {
      toast("🚀 កំពុង Restart App... ទំព័រនឹងដំណើរការឡើងវិញក្នុងពេលបន្តិចទៀត", "good");
      setTimeout(() => { window.location.reload(); }, 4000);
    }
  };
}

// Check for update on load and every 15 seconds
checkAppAutoUpdate();
setInterval(checkAppAutoUpdate, 15000);

/* ---------- Admin PUSH & DEPLOY Handlers ---------- */
function openPushDeployModal(){
  const m = $("#pushDeployModal");
  if(!m) return;
  m.hidden = false;
  const msgInp = $("#pushDeployMsgInput");
  if(msgInp && !msgInp.value){
    const d = new Date();
    msgInp.value = `Auto Deploy Updates - ${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
  }
}
function closePushDeployModal(){
  const m = $("#pushDeployModal");
  if(m) m.hidden = true;
}
const pdCl = $("#pushDeployCloseBtn"); if(pdCl) pdCl.onclick = closePushDeployModal;
const pdCl2 = $("#pushDeployCloseBtn2"); if(pdCl2) pdCl2.onclick = closePushDeployModal;
const pdMod = $("#pushDeployModal"); if(pdMod) pdMod.addEventListener('click', e => { if(e.target === pdMod) closePushDeployModal(); });

const clDeployLogBtn = $("#clearDeployLogBtn");
if(clDeployLogBtn){
  clDeployLogBtn.onclick = () => {
    const box = $("#pushDeployLogBox");
    if(box) box.textContent = "⚡ Terminal log cleared.\n";
  };
}

const startDeployBtn = $("#startPushDeployBtn");
if(startDeployBtn){
  startDeployBtn.onclick = async () => {
    const msg = ($("#pushDeployMsgInput") && $("#pushDeployMsgInput").value.trim()) || '';
    const pin = currentAdminPin || '8888';
    const tok = localStorage.getItem('syd_auth_token') || '';
    const box = $("#pushDeployLogBox");
    const spin = $("#pushDeploySpinner");
    const succ = $("#pushDeploySuccessCard");
    const shaDisp = $("#pushDeployShaDisplay");

    if(succ) succ.style.display = "none";
    startDeployBtn.disabled = true;
    startDeployBtn.innerHTML = `<span>⏳ កំពុង Push &amp; Deploy...</span>`;
    if(spin) spin.style.display = "inline-block";

    if(box){
      box.textContent = `🚀 [${new Date().toLocaleTimeString()}] ចាប់ផ្តើមដំណើរការ PUSH & DEPLOY TO GITHUB...\n`;
      box.textContent += `📍 Repository: SayanndaraKH/SDA001 (branch: main)\n`;
      box.textContent += `⏳ កំពុងដំណើរការ git status, git add, git commit & git push origin main...\n`;
    }

    try {
      const res = await fetch("/dl/admin/push-deploy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, token: tok, message: msg })
      });
      const data = await res.json();
      if(spin) spin.style.display = "none";

      if(box && data.logs && data.logs.length){
        box.textContent = data.logs.join("\n") + "\n";
        box.scrollTop = box.scrollHeight;
      }

      if(data.ok){
        if(succ) succ.style.display = "block";
        if(shaDisp) shaDisp.textContent = data.commit || 'main';
        toast("🎉 PUSH & DEPLOY ជោគជ័យ ១០០%! User PC នឹងឃើញ Auto Update ភ្លាមៗ", false);
        // Force check update locally
        checkAppAutoUpdate();
      } else {
        toast("❌ " + (data.error || "Deploy failed"), true);
        if(box) box.textContent += `\n❌ ERROR: ${data.error || 'Failed'}\n`;
      }
    } catch(err){
      if(spin) spin.style.display = "none";
      toast("❌ កំហុសបណ្តាញ៖ " + err.message, true);
      if(box) box.textContent += `\n❌ Network Error: ${err.message}\n`;
    } finally {
      startDeployBtn.disabled = false;
      startDeployBtn.innerHTML = `<span>🚀 Push &amp; Deploy ឥឡូវនេះ</span>`;
    }
  };
}

/* ---------- Admin BUILD.EXE Handlers ---------- */
async function fetchBuildInfo(){
  try {
    const res = await fetch("/dl/admin/build-info");
    const d = await res.json();
    if(d.ok){
      const curEl = $("#buildCurVerDisplay");
      const nextEl = $("#buildNextVerDisplay");
      if(curEl) curEl.textContent = d.current_version_tag || `V${d.current_version}`;
      if(nextEl) nextEl.textContent = d.next_version_tag || `V${d.next_version}`;
      renderBuildHistory(d.builds || []);
    }
  } catch(e){
    console.error("fetchBuildInfo error:", e);
  }
}

function renderBuildHistory(builds){
  const el = $("#buildHistoryList");
  if(!el) return;
  if(!builds || !builds.length){
    el.innerHTML = `<div style="font-size:11.5px;color:var(--muted);text-align:center;padding:10px">មិនទាន់មាន File EXE ក្នុង folder output/ នៅឡើយទេ</div>`;
    return;
  }
  el.innerHTML = builds.map(b => `
    <div style="background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;gap:8px">
      <div style="display:flex;flex-direction:column;gap:2px">
        <div style="font-weight:700;font-size:12px;color:var(--ink)">📦 ${esc(b.name)}</div>
        <div style="font-size:10.5px;color:var(--muted)">ទំហំ: <span style="color:#38bdf8">${b.size_mb} MB</span> &nbsp;•&nbsp; កាលបរិច្ឆេទ: ${b.mtime}</div>
      </div>
      <div style="display:flex;gap:6px">
        <a class="btn ghost sm" href="/dl/admin/download-exe?file=${encodeURIComponent(b.name)}" download style="font-size:11px;padding:2px 8px;color:var(--good);border-color:var(--good)">⬇️ Download</a>
      </div>
    </div>
  `).join('');
}

function openBuildExeModal(){
  const m = $("#buildExeModal");
  if(!m) return;
  m.hidden = false;
  fetchBuildInfo();
}
function closeBuildExeModal(){
  const m = $("#buildExeModal");
  if(m) m.hidden = true;
}

const bldCl = $("#buildExeCloseBtn"); if(bldCl) bldCl.onclick = closeBuildExeModal;
const bldCl2 = $("#buildExeCloseBtn2"); if(bldCl2) bldCl2.onclick = closeBuildExeModal;
const bldMod = $("#buildExeModal"); if(bldMod) bldMod.addEventListener('click', e => { if(e.target === bldMod) closeBuildExeModal(); });

const clBldLogBtn = $("#clearBuildLogBtn");
if(clBldLogBtn){
  clBldLogBtn.onclick = () => {
    const box = $("#buildExeLogBox");
    if(box) box.textContent = "⚡ Build terminal log cleared.\n";
  };
}

const rfBldListBtn = $("#refreshBuildListBtn");
if(rfBldListBtn) rfBldListBtn.onclick = fetchBuildInfo;

async function dlAdminOpenOutputFolder(){
  try {
    const res = await fetch("/dl/admin/open-output-folder", { method: "POST" });
    const d = await res.json();
    if(d.ok){
      toast("📂 បានបើក Folder output/ ក្នុង Windows Explorer", false);
    } else {
      toast("❌ " + (d.error || "Cannot open folder"), true);
    }
  } catch(e){
    toast("❌ " + e.message, true);
  }
}
const bldOpenFldBtn = $("#buildOpenFolderBtn");
if(bldOpenFldBtn) bldOpenFldBtn.onclick = dlAdminOpenOutputFolder;

const startBldBtn = $("#startBuildExeBtn");
if(startBldBtn){
  startBldBtn.onclick = async () => {
    const pin = currentAdminPin || '8888';
    const tok = localStorage.getItem('syd_auth_token') || '';
    const box = $("#buildExeLogBox");
    const spin = $("#buildExeSpinner");
    const icon = $("#buildExeBtnIcon");
    const txt = $("#buildExeBtnText");
    const succ = $("#buildExeSuccessCard");
    const sDot = $("#buildExeStatusDot");
    const sTxt = $("#buildExeStatusText");

    if(succ) succ.style.display = "none";
    startBldBtn.disabled = true;
    if(txt) txt.textContent = "កំពុងដំណើរការ Build Standalone EXE...";
    if(icon) icon.style.display = "none";
    if(spin) spin.style.display = "inline-block";
    if(sDot) sDot.style.background = "#f59e0b";
    if(sTxt) sTxt.textContent = "កំពុង Compile Bytecode...";

    if(box){
      box.textContent = `🚀 [${new Date().toLocaleTimeString()}] ចាប់ផ្តើមបញ្ជាដំណើរការ BUILD.EXE...\n`;
      box.textContent += `⚙️ Compiling and packaging standalone single EXE with bytecode protection...\n`;
    }

    try {
      const res = await fetch("/dl/admin/build-exe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin, token: tok })
      });

      if(!res.ok){
        const errJson = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
        throw new Error(errJson.error || `HTTP ${res.status}`);
      }

      // Read streaming NDJSON response
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while(true){
        const { value, done } = await reader.read();
        if(done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep partial

        for(const line of lines){
          const trimmed = line.trim();
          if(!trimmed) continue;
          try {
            const data = JSON.parse(trimmed);
            if(data.type === "log"){
              if(box){
                box.textContent += data.text + "\n";
                box.scrollTop = box.scrollHeight;
              }
            } else if(data.type === "done"){
              if(data.ok){
                if(sDot) sDot.style.background = "#10b981";
                if(sTxt) sTxt.textContent = "Build ជោគជ័យ ១០០%";
                if(succ){
                  succ.style.display = "block";
                  const nameEl = $("#buildSuccessExeName");
                  const sizeEl = $("#buildSuccessExeSize");
                  const dlBtn = $("#buildDownloadExeBtn");
                  if(nameEl) nameEl.textContent = data.exe_name || 'SYD-Downloader-Pro.exe';
                  if(sizeEl) sizeEl.textContent = `${data.size_mb || 0} MB`;
                  if(dlBtn) dlBtn.href = `/dl/admin/download-exe?file=${encodeURIComponent(data.exe_name || '')}`;
                }
                toast(`🎉 Build ${data.version_tag || ''} ជោគជ័យជាស្ថាពរ! (${data.size_mb || 0} MB)`, false);
                fetchBuildInfo();
              } else {
                if(sDot) sDot.style.background = "#ef4444";
                if(sTxt) sTxt.textContent = "Build បរាជ័យ";
                toast("❌ " + (data.error || "Build failed"), true);
                if(box) box.textContent += `\n❌ ERROR: ${data.error || 'Failed'}\n`;
              }
            }
          } catch(pe){
            if(box){
              box.textContent += trimmed + "\n";
              box.scrollTop = box.scrollHeight;
            }
          }
        }
      }
    } catch(err){
      if(sDot) sDot.style.background = "#ef4444";
      if(sTxt) sTxt.textContent = "កំហុសបណ្តាញ";
      toast("❌ កំហុស Build: " + err.message, true);
      if(box) box.textContent += `\n❌ Exception: ${err.message}\n`;
    } finally {
      startBldBtn.disabled = false;
      if(txt) txt.textContent = "ចាប់ផ្តើម BUILD.EXE ឥឡូវនេះ";
      if(icon) icon.style.display = "inline";
      if(spin) spin.style.display = "none";
    }
  };
}

/* ---------- Admin / DEV Restart Handler ---------- */
async function doAdminRestart(){
  if(!confirm("⚡ តើអ្នកពិតជាចង់ Restart កម្មវិធី (Server & App) ឡើងវិញមែនទេ? (ADMIN / DEV Only)")) return;
  const pin = currentAdminPin || (window.userAccess && window.userAccess.pin) || '8888';
  const token = localStorage.getItem('syd_auth_token') || (window.userAccess && window.userAccess.token) || '';
  toast("⚡ កំពុង Restart App... សូមរង់ចាំបន្តិច", false);
  try {
    const res = await fetch('/dl/restart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin, token, action: 'admin_restart' })
    });
    const d = await res.json();
    if(d.ok){
      toast("🚀 " + (d.message || "Restart ជោគជ័យ!"), false);
      let count = 0;
      const pollTimer = setInterval(async () => {
        count++;
        try {
          const chk = await fetch('/dl/status', { cache: 'no-store' });
          if(chk.ok){
            clearInterval(pollTimer);
            toast("✅ Server ដំណើរការឡើងវិញជាប្រក្រតី!", false);
            setTimeout(() => { window.location.reload(); }, 800);
          }
        } catch(e) {
          if(count > 15){
            clearInterval(pollTimer);
            window.location.reload();
          }
        }
      }, 1000);
    } else {
      toast("❌ " + (d.error || "Restart failed"), true);
    }
  } catch(e){
    toast("⚡ កំពុង Restart Server... ទំព័រនឹងផ្ទុកឡើងវិញដោយស្វ័យប្រវត្តិ", false);
    setTimeout(() => { window.location.reload(); }, 3000);
  }
}

/* ---------- Auth, User Registration, VIP & Access Control ---------- */
let currentAdminPin = sessionStorage.getItem('hg_admin_pin') || '';


function isUserFullAccess(){
  if(!window.userAccess) return false;
  return !!(window.userAccess.is_admin || window.userAccess.is_vip || window.userAccess.role === 'admin' || window.userAccess.role === 'dev' || window.userAccess.mode === 'free_all');
}

function isEpisodeLocked(epNum, seriesId){
  if(isUserFullAccess()) return false;
  const num = Number(epNum);
  const sid = seriesId || (window.ddCurrentDrama ? (window.ddCurrentDrama.id || window.ddCurrentDrama.series_id) : null);

  // Check if series is already purchased with coins
  if(sid && window.userAccess && window.userAccess.purchased_series && window.userAccess.purchased_series[sid]){
    return false;
  }

  let freeLimit = (window.userAccess && window.userAccess.max_free_episodes !== undefined) ? Number(window.userAccess.max_free_episodes) : 5;
  if(sid && typeof getDramaRuleForSeries === 'function'){
    const dr = getDramaRuleForSeries(sid);
    if(dr){
      if(dr.rule === 'free_all') return false;
      if(dr.free_episodes !== undefined && dr.free_episodes !== null){
        freeLimit = Number(dr.free_episodes);
      }
    }
  }

  return num > freeLimit;
}

function switchAuthTab(tab){
  const isAuth = !!(window.userAccess && window.userAccess.authenticated);
  const isPendingVip = !!(window.userAccess && window.userAccess.status === 'pending_vip');
  const isBanned = !!(window.userAccess && (window.userAccess.status === 'banned' || window.userAccess.is_banned));

  const btnL = $("#tabBtnLogin"), btnR = $("#tabBtnRegister"), btnV = $("#tabBtnVip");
  const secL = $("#authTabLoginSec"), secR = $("#authTabRegisterSec"), secV = $("#authTabVipSec"), secB = $("#authTabBannedSec");
  if(btnL) btnL.classList.toggle('on', tab === 'login');
  if(btnR) btnR.classList.toggle('on', tab === 'register');
  if(btnV) btnV.classList.toggle('on', tab === 'vip');
  if(secL) secL.style.display = (tab === 'login') ? 'flex' : 'none';
  if(secR) secR.style.display = (tab === 'register') ? 'flex' : 'none';
  if(secV) secV.style.display = (tab === 'vip') ? 'flex' : 'none';
  if(secB) secB.style.display = (tab === 'banned') ? 'flex' : 'none';

  if(tab === 'login'){
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
  }

  if(tab === 'vip'){
    const guestWarn = $("#vipGuestWarningBanner");
    const regSubBtn = $("#regSubmitBtn");
    const pendBanner = $("#vipPendingBanner");
    const pkgCard = $("#tabPanelVip");
    const submitCard = $("#vipSubmitFormCard");

    if(!isAuth && !isBanned){
      if(guestWarn) guestWarn.style.display = 'flex';
      if(pendBanner) pendBanner.style.display = 'none';
      if(pkgCard) pkgCard.style.display = 'flex';
      if(submitCard) submitCard.style.display = 'flex';
      if(regSubBtn) {
        regSubBtn.innerHTML = "<span>📝 សូមចុះឈ្មោះគណនីជាមុនសិន ដើម្បីស្នើសុំ VIP</span>";
        regSubBtn.onclick = () => { switchAuthTab('register'); };
      }
    } else {
      if(guestWarn) guestWarn.style.display = 'none';
      if(isPendingVip){
        if(pendBanner) pendBanner.style.display = 'block';
        if(pkgCard) pkgCard.style.display = 'none';
        if(submitCard) submitCard.style.display = 'none';
      } else {
        if(pendBanner) pendBanner.style.display = 'none';
        if(pkgCard) pkgCard.style.display = 'flex';
        if(submitCard) submitCard.style.display = 'flex';
        if(regSubBtn) {
          regSubBtn.innerHTML = isBanned 
            ? "<span>🔄 ផ្ញើសំណើសុំ ADMIN បើកគណនីឡើងវិញ</span>"
            : "<span>🚀 ផ្ញើសំណើសុំកញ្ចប់ VIP ទៅកាន់ Admin</span>";
          regSubBtn.onclick = doSubmitVipRequest;
        }
      }
    }
  }
}

function openReRequestVipForm(){
  switchAuthTab('vip');
  const noteInput = $("#regNoteInput");
  if(noteInput){
    noteInput.value = "[ស្នើសុំ ADMIN មេត្តាជួយបើកដំណើរការគណនីឡើងវិញ]";
  }
  toast("💡 សូមជ្រើសរើសកញ្ចប់ VIP និងចុច 'ផ្ញើសំណើ' ដើម្បីស្នើសុំ Admin បើកគណនីឡើងវិញ!", false);
}

let isMandatoryAuth = false;

function promptVipModal(epNum){
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
}

function openUserRegisterModal(preferTab = 'login', isMandatory = false){
  const m = $("#userRegisterModal");
  if(!m) return;
  const isAuth = !!(window.userAccess && window.userAccess.authenticated);
  const isBanned = !!(window.userAccess && (window.userAccess.status === 'banned' || window.userAccess.is_banned));
  isMandatoryAuth = (!isAuth || isBanned) && !!isMandatory;
  const closeBtn1 = $("#regCloseBtn");
  const closeBtn2 = $("#regCloseBtn2");
  if(closeBtn1) closeBtn1.style.display = isMandatoryAuth ? 'none' : 'block';
  if(closeBtn2) closeBtn2.style.display = isMandatoryAuth ? 'none' : 'block';

  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin' || window.userAccess.role === 'dev'));
  const isVip = !!(window.userAccess && window.userAccess.is_vip);
  const isPendingVip = !!(window.userAccess && window.userAccess.status === 'pending_vip');
  const vipReqEnabled = !!(window.userAccess && window.userAccess.settings && (window.userAccess.settings.vip_request_enabled === true || window.userAccess.settings.vip_request_enabled === 'true' || window.userAccess.settings.vip_request_enabled === 1));

  // Tab VIP button: ONLY VISIBLE if Admin enabled it in Firebase RTDB and user is not Admin/VIP
  const tabVipBtn = $("#tabBtnVip");
  if(tabVipBtn){
    if(isAdmin || isVip || !vipReqEnabled){
      tabVipBtn.style.display = 'none';
    } else {
      tabVipBtn.style.display = 'block';
    }
  }

  const sub = $("#regModalSub");
  if(sub){
    if(isBanned){
      sub.textContent = "🚫 គណនីត្រូវបាន ADMIN បិទ (Banned) · សូមស្នើសុំបើកឡើងវិញ ឬទាក់ទង ADMIN";
      sub.style.color = "var(--bad)";
    } else if(!isAuth){
      sub.textContent = "សូមចូលគណនី ឬចុះឈ្មោះគណនីធម្មតាដើម្បីទស្សនា និងប្រើប្រាស់";
      sub.style.color = "var(--accent)";
    } else if(isPendingVip){
      sub.textContent = "⏳ សំណើសុំ VIP របស់អ្នកកំពុងរង់ចាំ Admin អនុម័ត";
      sub.style.color = "var(--gold)";
    } else if(isVip){
      sub.textContent = "👑 គណនី VIP (ដោះសោរគ្រប់ភាគទាំងអស់ គ្មានដែនកំណត់)";
      sub.style.color = "var(--good)";
    } else {
      sub.textContent = vipReqEnabled 
        ? "👤 គណនីធម្មតា (ស្នើសុំ VIP ដើម្បីដោះសោរគ្រប់ភាគ)"
        : "👤 គណនីធម្មតា (អ្នកប្រើប្រាស់ជាក់ស្តែង)";
      sub.style.color = "var(--ink-2)";
    }
  }

  // Update Telegram admin link on banned card
  const bannedTg = $("#bannedTgAdminLink");
  if(bannedTg && window.userAccess && window.userAccess.settings && window.userAccess.settings.telegram_admin){
    const tg = window.userAccess.settings.telegram_admin.replace(/^@/, '');
    bannedTg.href = `https://t.me/${tg}`;
  }

  m.hidden = false;
  
  let targetTab = preferTab || 'login';
  if(isBanned && targetTab !== 'vip'){
    targetTab = 'banned';
  } else if(isAdmin || isVip || !vipReqEnabled){
    if(targetTab === 'vip') targetTab = 'login';
  }
  switchAuthTab(targetTab);
}

function closeUserRegisterModal(){
  if(!window.userAccess || !window.userAccess.authenticated){
    toast("⚠️ ដាច់ខាតត្រូវតែចុះឈ្មោះ User ធម្មតា ឬ Login ជាមុនសិន!", true);
    return;
  }
  const m = $("#userRegisterModal");
  if(m) m.hidden = true;
  const banner = $("#authAlertBanner");
  if(banner) banner.style.display = 'none';
}

function selectVipPackage(pkgVal){
  const radio = document.querySelector(`input[name="vipPackageRadio"][value="${pkgVal}"]`);
  if(radio) radio.checked = true;
  
  document.querySelectorAll('.vip-pkg-card').forEach(c => {
    c.classList.toggle('active', c.getAttribute('data-pkg') === pkgVal);
  });
  
  prepareAdminTgHref();
}

function prepareAdminTgHref(){
  const link = $("#vipTgAdminLink");
  if(!link) return;
  const settings = (window.userAccess && window.userAccess.settings) || {};
  const tgAdmin = (settings.telegram_admin || '').trim();
  const devId = (window.userAccess && window.userAccess.device_id) || 'Unknown';
  const uname = (window.userAccess && (window.userAccess.username || window.userAccess.name)) || 'User';
  
  const checkedPkg = document.querySelector('input[name="vipPackageRadio"]:checked');
  const pkgVal = (checkedPkg && checkedPkg.value) || '1_year';
  const pkgLabels = {
    '1_month': 'VIP 1 ខែ (30 ថ្ងៃ)',
    '3_months': 'VIP 3 ខែ (90 ថ្ងៃ)',
    '6_months': 'VIP 6 ខែ (180 ថ្ងៃ)',
    '1_year': 'VIP 1 ឆ្នាំ (365 ថ្ងៃ)',
    'lifetime': 'VIP មួយជីវិត (Lifetime)'
  };
  const pkgName = pkgLabels[pkgVal] || pkgVal;

  if(!tgAdmin){
    link.href = "javascript:void(0)";
    link.onclick = (e) => {
      e.preventDefault();
      if(devId && navigator.clipboard){
        navigator.clipboard.writeText(devId).catch(()=>{});
      }
      toast("📋 បានចម្លង Device ID: " + devId);
    };
    return;
  }

  let username = tgAdmin;
  if(username.startsWith('https://t.me/')) username = username.replace('https://t.me/', '');
  else if(username.startsWith('http://t.me/')) username = username.replace('http://t.me/', '');
  if(username.startsWith('@')) username = username.substring(1);
  username = username.split('/')[0].split('?')[0];

  const msg = `សួស្តី Admin! ខ្ញុំចង់ស្នើសុំកញ្ចប់ ${pkgName}
- គណនី: ${uname}
- Device ID: ${devId}
សូម Admin ជួយពិនិត្យ និងបើកសិទ្ធិ VIP ជូនខ្ញុំផង។ អរគុណ!`;

  link.href = `https://t.me/${username}?text=${encodeURIComponent(msg)}`;
  link.onclick = () => {
    if(devId && navigator.clipboard){
      navigator.clipboard.writeText(devId).catch(()=>{});
    }
    toast("📋 បានចម្លង Device ID & កំពុងបើក Telegram Admin...");
  };
}

function updateVipPortalSettings(settings, userAccess){
  if(!settings) return;
  prepareAdminTgHref();

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
  const submitCard = $("#vipSubmitFormCard");
  const topSubmitCard = $("#vipTopSubmitCard");
  if(isPendingVip){
    if(pendBanner) pendBanner.style.display = "block";
    if(pkgForm) pkgForm.style.display = "none";
    if(submitCard) submitCard.style.display = "none";
    if(topSubmitCard) topSubmitCard.style.display = "none";
  } else {
    if(pendBanner) pendBanner.style.display = "none";
    if(pkgForm) pkgForm.style.display = "flex";
    if(submitCard) submitCard.style.display = "flex";
    if(topSubmitCard) topSubmitCard.style.display = "flex";
  }
}

async function fetchAccessStatus(){
  try {
    const urlParams = new URLSearchParams(window.location.search);
    let tok = urlParams.get('auth_token') || localStorage.getItem('syd_auth_token') || '';
    if(urlParams.get('auth_token')){
      localStorage.setItem('syd_auth_token', urlParams.get('auth_token'));
    }
    const res = await fetch(`/dl/access/status?token=${encodeURIComponent(tok)}`);
    if(res.ok){
      const data = await res.json();
      const prevWasNotVip = window.userAccess && !window.userAccess.is_vip;
      window.userAccess = data;
      updateAccessUI(data);

      // DEV & ADMIN check: Completely exempt from registration, login, and all modals
      const isDevOrAdmin = !!(data.is_dev || data.role === 'dev' || data.is_admin || data.role === 'admin');
      if(isDevOrAdmin){
        isMandatoryAuth = false;
        closeUserRegisterModal();
      } else if(data.is_banned || data.status === 'banned' || data.status === 'machine_mismatch'){
        isMandatoryAuth = true;
        openUserRegisterModal('banned', true);
        if(data.status === 'machine_mismatch'){
          const bTitle = $("#authBannedTitle");
          const bDesc = $("#authBannedDesc");
          if(bTitle) bTitle.textContent = "🚫 Machine ID មិនត្រូវគ្នា (1 PC = 1 User ប៉ុណ្ណោះ)";
          if(bDesc) bDesc.innerHTML = `<span style="color:#f87171;font-weight:bold">គណនីនេះត្រូវបានភ្ជាប់ជាមួយកុំព្យូទ័រ (PC) ផ្សេងរួចហើយ!</span><br>ប្រព័ន្ធកំណត់ដាច់ខាត 1 Machine ID ប្រើប្រាស់បានតែលើ 1 PC ប៉ុណ្ណោះ មិនអាចប្រើលើកុំព្យូទ័រនេះបានឡើយ។`;
        }
      } else if(!data.authenticated || data.must_register || !data.has_firebase_account){
        openUserRegisterModal('register', true);
      } else {
        isMandatoryAuth = false;
        if(prevWasNotVip && data.is_vip){
          toast(`👑 អបអរសាទរ! ADMIN បានអនុម័តកញ្ចប់ VIP ជូន ${data.name || data.username} រួចរាល់ហើយ! (ដោះសោរគ្រប់ភាគទាំងអស់)`, false);
          closeUserRegisterModal();
        }
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
  const isAdmin = !!(data && (data.is_admin || data.role === 'admin'));
  document.documentElement.dataset.userRole = isAdmin ? "admin" : "user";

  const badge = $("#userAccessBadge");
  const icon = $("#uabIcon");
  const txt = $("#uabText");
  const reqVipBtn = $("#topReqVipBtn");
  const topUc = $("#topUserCtrlBtn");
  const topLogout = $("#topLogoutBtn");
  const topLoginBtn = $("#topLoginBtn");
  if(topLoginBtn) topLoginBtn.style.display = isAdmin ? "none" : "inline-flex";
  const btnSwitchToUser = $("#topBtnSwitchToUser");
  const btnSwitchToAdmin = $("#topBtnSwitchToAdmin");
  if(btnSwitchToUser) btnSwitchToUser.style.display = isAdmin ? "inline-flex" : "none";
  if(btnSwitchToAdmin) btnSwitchToAdmin.style.display = (!isAdmin) ? "inline-flex" : "none";
  const topRestartBtn = $("#topAdminRestartBtn");
  if(topRestartBtn) topRestartBtn.style.display = isAdmin ? "inline-flex" : "none";
  const isVip = !!(data && data.is_vip);
  const isPendingVip = (data && data.status === 'pending_vip');
  const isBanned = (data && (data.status === 'banned' || data.is_banned));
  const isUser = !!(data && data.username && !isAdmin);

  // VIP Request feature toggle from Firebase Realtime Database
  const vipReqEnabled = !!(data && data.settings && (data.settings.vip_request_enabled === true || data.settings.vip_request_enabled === 'true' || data.settings.vip_request_enabled === 1));

  // Home VIP Promotion Banner Visibility: strictly hide if Admin disabled VIP requests in Firebase RTDB
  const homeVipBanner = $("#homeVipPromoBanner");
  if(homeVipBanner){
    homeVipBanner.style.display = (isAdmin || isVip || !vipReqEnabled) ? "none" : "flex";
  }

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
  }

  if(isAdmin){
    const isDevRole = !!(data.is_dev || data.role === 'dev');
    if(icon) icon.textContent = isDevRole ? "⚡" : "🛡️";
    if(txt) txt.textContent = isDevRole ? "DEV (Dara - សេរី)" : "ADMIN (Full Control)";
    if(badge){
      badge.style.borderColor = isDevRole ? "#38bdf8" : "#c084fc";
      badge.style.color = isDevRole ? "#38bdf8" : "#c084fc";
      badge.style.background = isDevRole ? "rgba(56,189,248,0.16)" : "rgba(192,132,252,0.14)";
      badge.style.boxShadow = isDevRole ? "0 0 14px rgba(56,189,248,0.4)" : "0 0 12px rgba(192,132,252,0.3)";
    }
    if(topUc) topUc.style.display = "inline-flex";
    const topRestart = $("#topAdminRestartBtn");
    if(topRestart) topRestart.style.display = isAdmin ? "inline-flex" : "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:${isDevRole ? '#38bdf8' : '#c084fc'};font-weight:700">⚡ ចូលជា: ${isDevRole ? 'DEV MASTER (សេរី គ្មានដែនកំណត់)' : 'ADMIN (Full Control)'}</span>`;
    currentAdminPin = localStorage.getItem('syd_auth_token') || '8888';
    sessionStorage.setItem('hg_admin_pin', '8888');
    const pinBox = $("#adminPinBox"); if(pinBox) pinBox.hidden = true;
    const unPanel = $("#adminUnlockedPanel"); if(unPanel) unPanel.hidden = false;
    const lockBadge = $("#adminLockBadge");
    if(lockBadge){
      lockBadge.textContent = isDevRole ? "⚡ DEV MASTER (UNLOCKED)" : "🔓 UNLOCKED (ADMIN)";
      lockBadge.style.color = isDevRole ? "#38bdf8" : "var(--good)";
      lockBadge.style.background = isDevRole ? "rgba(56,189,248,0.18)" : "rgba(46,204,113,0.15)";
    }
    refreshAdminUsersList();

  } else if(isBanned || data.status === 'machine_mismatch'){
    if(icon) icon.textContent = "🚫";
    if(txt) txt.textContent = data.status === 'machine_mismatch' ? "Machine Lock (1 PC)" : "Banned (បិទគណនី)";
    if(badge){
      badge.style.borderColor = "var(--bad)";
      badge.style.color = "var(--bad)";
      badge.style.background = "rgba(255,46,99,0.18)";
      badge.style.boxShadow = "0 0 10px rgba(255,46,99,0.3)";
    }
    if(topUc) topUc.style.display = "none";
    if(topLogout) topLogout.style.display = "inline-flex";
    if(footUser) footUser.innerHTML = `<span style="color:var(--bad);font-weight:700">🚫 ${data.status === 'machine_mismatch' ? 'Machine ID មិនត្រូវគ្នា (1 PC Only)' : 'គណនីត្រូវបាន ADMIN បិទ (Banned)'}</span>`;
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

  const vipUserDisp = $("#vipUsernameDisplay");
  if(vipUserDisp){
    if(data.username){
      vipUserDisp.textContent = `គណនី: ${data.username}${data.name ? ' (' + data.name + ')' : ''}`;
    } else {
      vipUserDisp.textContent = "មិនទាន់ចូលគណនី (Guest)";
    }
  }

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

  // Update Top Navigation Bar Days Remaining Badge
  const topDlBadge = $("#topDaysLeftBadge");
  const topDlIcon = $("#topDaysLeftIcon");
  const topDlText = $("#topDaysLeftText");
  if(topDlBadge){
    if(isAdmin){
      const isDevRole = !!(data.is_dev || data.role === 'dev');
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = isDevRole ? "rgba(56,189,248,0.18)" : "rgba(192,132,252,0.18)";
      topDlBadge.style.border = isDevRole ? "1.5px solid rgba(56,189,248,0.55)" : "1.5px solid rgba(192,132,252,0.55)";
      topDlBadge.style.color = isDevRole ? "#38bdf8" : "#c084fc";
      topDlBadge.style.boxShadow = isDevRole ? "0 0 12px rgba(56,189,248,0.35)" : "0 0 10px rgba(192,132,252,0.25)";
      if(topDlIcon) topDlIcon.textContent = isDevRole ? "⚡" : "♾️";
      if(topDlText) topDlText.textContent = isDevRole ? "DEV MASTER (សេរី)" : "គ្មានដែនកំណត់ (ADMIN)";
      topDlBadge.title = isDevRole ? "Developer Machine (ប្រើប្រាស់បានដោយសេរី គ្មានដែនកំណត់ មិនបាច់ Login)" : "គណនី Super Admin (Full Control - គ្មានដែនកំណត់)";
    } else if(isBanned || data.status === 'machine_mismatch'){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(255,46,99,0.22)";
      topDlBadge.style.border = "1.5px solid rgba(255,46,99,0.7)";
      topDlBadge.style.color = "var(--bad)";
      topDlBadge.style.boxShadow = "0 0 12px rgba(255,46,99,0.4)";
      if(topDlIcon) topDlIcon.textContent = "🚫";
      if(topDlText) topDlText.textContent = data.status === 'machine_mismatch' ? "Machine Lock (1 PC)" : "គណនីត្រូវបានបិទ (Banned)";
      topDlBadge.title = data.status === 'machine_mismatch' ? "គណនីខុសកុំព្យូទ័រ (1 Machine ID / 1 PC Only)" : "គណនីត្រូវបាន ADMIN បិទដំណើរការ";
    } else if(isVip){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(46,204,113,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(46,204,113,0.55)";
      topDlBadge.style.color = "var(--good)";
      topDlBadge.style.boxShadow = "0 0 10px rgba(46,204,113,0.25)";
      if(topDlIcon) topDlIcon.textContent = "👑";
      const vipDays = data.days_left < 0 ? "គ្មានដែនកំណត់" : `${data.days_left} ថ្ងៃ`;
      if(topDlText) topDlText.textContent = `VIP: នៅសល់ ${vipDays}`;
      topDlBadge.title = `គណនី VIP Member (នៅសល់ ${vipDays}) កាលបរិច្ឆេទផុតកំណត់៖ ${data.expires_date || ''}`;
    } else if(isPendingVip){
      topDlBadge.style.display = "inline-flex";
      topDlBadge.style.background = "rgba(245,158,11,0.18)";
      topDlBadge.style.border = "1.5px solid rgba(245,158,11,0.55)";
      topDlBadge.style.color = "#f59e0b";
      topDlBadge.style.boxShadow = "0 0 10px rgba(245,158,11,0.25)";
      if(topDlIcon) topDlIcon.textContent = "⏳";
      if(topDlText) topDlText.textContent = `រង់ចាំ VIP (${data.days_left !== undefined ? data.days_left : 7} ថ្ងៃ)`;
      topDlBadge.title = "សំណើ VIP កំពុងរង់ចាំ Admin អនុម័ត";
    } else if(isUser){
      topDlBadge.style.display = "inline-flex";
      const uDays = (data.days_left !== undefined && data.days_left !== null) ? data.days_left : 7;
      if(uDays <= 2){
        topDlBadge.style.background = "rgba(239,68,68,0.22)";
        topDlBadge.style.border = "1.5px solid rgba(239,68,68,0.7)";
        topDlBadge.style.color = "#ef4444";
        topDlBadge.style.boxShadow = "0 0 12px rgba(239,68,68,0.4)";
        if(topDlIcon) topDlIcon.textContent = "⚠️";
        if(topDlText) topDlText.textContent = `នៅសល់តែ ${uDays} ថ្ងៃ (ប្រញាប់ស្នើ VIP!)`;
      } else {
        topDlBadge.style.background = "rgba(255,106,43,0.16)";
        topDlBadge.style.border = "1.5px solid rgba(255,106,43,0.5)";
        topDlBadge.style.color = "var(--accent)";
        topDlBadge.style.boxShadow = "0 0 10px rgba(255,106,43,0.2)";
        if(topDlIcon) topDlIcon.textContent = "⏳";
        if(topDlText) topDlText.textContent = `User: នៅសល់ ${uDays} ថ្ងៃ (សាកល្បង)`;
      }
      topDlBadge.title = `User ធម្មតាមានរយៈពេល 7 ថ្ងៃសាកល្បង (នៅសល់ ${uDays} ថ្ងៃ)។ បើមិនស្នើសុំ VIP ទេ គណនីនឹងត្រូវលុបចោលចេញពីប្រព័ន្ធដាច់ខាត!`;
    } else {
      topDlBadge.style.display = "none";
    }
  }

  // Update Modal Days Remaining Badge & 7-Day Trial Notice
  const mDaysBadge = $("#modalDaysRemainingBadge");
  const mDaysIcon = $("#modalDaysIcon");
  const mNotice = $("#modalTrialRuleNotice");
  if(mDaysBadge){
    if(isAdmin){
      mDaysBadge.textContent = "♾️ គ្មានដែនកំណត់ (ADMIN Full Control)";
      mDaysBadge.style.background = "rgba(192,132,252,0.2)";
      mDaysBadge.style.color = "#c084fc";
      if(mDaysIcon) mDaysIcon.textContent = "♾️";
      if(mNotice) mNotice.style.display = "none";
    } else if(isVip){
      const vDays = data.days_left < 0 ? "គ្មានដែនកំណត់" : `${data.days_left} ថ្ងៃ`;
      mDaysBadge.textContent = `👑 នៅសល់ ${vDays} (ផុតកំណត់: ${data.expires_date || ''})`;
      mDaysBadge.style.background = "rgba(46,204,113,0.18)";
      mDaysBadge.style.color = "var(--good)";
      if(mDaysIcon) mDaysIcon.textContent = "👑";
      if(mNotice) mNotice.style.display = "none";
    } else if(isPendingVip){
      const pDays = data.days_left !== undefined ? data.days_left : 7;
      mDaysBadge.textContent = `⏳ សំណើ VIP កំពុងរង់ចាំ Admin (នៅសល់ ${pDays} ថ្ងៃ)`;
      mDaysBadge.style.background = "rgba(245,158,11,0.18)";
      mDaysBadge.style.color = "#f59e0b";
      if(mDaysIcon) mDaysIcon.textContent = "⏳";
      if(mNotice) mNotice.style.display = "none";
    } else if(isUser){
      const uDays = (data.days_left !== undefined && data.days_left !== null) ? data.days_left : 7;
      mDaysBadge.textContent = `⏳ នៅសល់ ${uDays} ថ្ងៃ (ផុតកំណត់: ${data.expires_date || ''})`;
      mDaysBadge.style.background = uDays <= 2 ? "rgba(239,68,68,0.2)" : "rgba(255,106,43,0.15)";
      mDaysBadge.style.color = uDays <= 2 ? "#ef4444" : "var(--accent)";
      if(mDaysIcon) mDaysIcon.textContent = uDays <= 2 ? "⚠️" : "⏳";
      if(mNotice) mNotice.style.display = "block";
    } else {
      mDaysBadge.textContent = "មិនទាន់ចុះឈ្មោះ (Guest)";
      mDaysBadge.style.background = "rgba(255,255,255,0.08)";
      mDaysBadge.style.color = "var(--muted)";
      if(mDaysIcon) mDaysIcon.textContent = "👤";
      if(mNotice) mNotice.style.display = "none";
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
  if(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin' || window.userAccess.role === 'dev')){
    openUserControl();
  } else {
    openUserRegisterModal('login', false);
  }
};

const topVipBtn = $("#topReqVipBtn");
if(topVipBtn) topVipBtn.onclick = () => {
  openUserRegisterModal('vip');
};

window.doExplicitLogout = async function(){
  if(!confirm("តើអ្នកពិតជាចង់ចាកចេញពីគណនីមែនទេ?")) return;
  localStorage.setItem('syd_auth_token', 'guest');
  localStorage.removeItem('syd_auth_user');
  sessionStorage.removeItem('hg_admin_pin');
  currentAdminPin = '';

  try {
    const devId = (window.userAccess && window.userAccess.device_id) || '';
    await fetch('/dl/access/logout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: 'guest', device_id: devId })
    });
  } catch(e){}

  if(window.history && window.history.replaceState){
    const cleanUrl = window.location.pathname + window.location.hash;
    window.history.replaceState({}, document.title, cleanUrl);
  }

  toast("🚪 បានចាកចេញពីគណនីជោគជ័យ (Guest Mode)");

  window.userAccess = { authenticated: false, role: 'guest', status: 'guest' };
  updateAccessUI(window.userAccess);
  openUserRegisterModal('login', true);

  await fetchAccessStatus();
};

const topLogoutBtn = $("#topLogoutBtn");
if(topLogoutBtn) topLogoutBtn.onclick = window.doExplicitLogout;

const regCl = $("#regCloseBtn"); if(regCl) regCl.onclick = closeUserRegisterModal;
const regCl2 = $("#regCloseBtn2"); if(regCl2) regCl2.onclick = closeUserRegisterModal;
const regMod = $("#userRegisterModal"); if(regMod) regMod.addEventListener('click', e => { if(e.target === regMod && !isMandatoryAuth) closeUserRegisterModal(); });

const regCopyBtn = $("#regCopyDevId");
if(regCopyBtn){
  regCopyBtn.onclick = () => {
    const dev = (window.userAccess && window.userAccess.device_id) || '';
    if(dev){
      navigator.clipboard.writeText(dev).then(() => {
        toast("📋 បានចម្លង Device ID រួចរាល់!");
      }).catch(() => {
        toast("Device ID: " + dev);
      });
    }
  };
}

// Enter key listeners for Login & Register forms
const loginPassInput = $("#authLoginPass");
if(loginPassInput){
  loginPassInput.addEventListener("keydown", e => {
    if(e.key === "Enter"){
      e.preventDefault();
      const u = ($("#authLoginUser") && $("#authLoginUser").value) || '';
      const p = loginPassInput.value || '';
      executeLogin(u, p);
    }
  });
}
const regPassInput = $("#authRegPass");
if(regPassInput){
  regPassInput.addEventListener("keydown", e => {
    if(e.key === "Enter"){
      e.preventDefault();
      const btn = $("#authRegSubmitBtn");
      if(btn) btn.click();
    }
  });
}

// Login Submit Handler
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
}

const authLoginSubmitBtn = $("#authLoginSubmitBtn");
if(authLoginSubmitBtn){
  authLoginSubmitBtn.onclick = () => {
    const u = ($("#authLoginUser") && $("#authLoginUser").value) || '';
    const p = ($("#authLoginPass") && $("#authLoginPass").value) || '';
    executeLogin(u, p);
  };
}

// Register Submit Handler
const authRegSubmitBtn = $("#authRegSubmitBtn");
if(authRegSubmitBtn){
  authRegSubmitBtn.onclick = async () => {
    const username = ($("#authRegUser") && $("#authRegUser").value.trim()) || '';
    const name = ($("#authRegName") && $("#authRegName").value.trim()) || '';
    const contact = ($("#authRegContact") && $("#authRegContact").value.trim()) || '';
    const password = ($("#authRegPass") && $("#authRegPass").value.trim()) || '';
    const note = ($("#authRegNote") && $("#authRegNote").value.trim()) || '';

    if(!username){
      toast("⚠️ សូមបញ្ចូលឈ្មោះគណនី (Username)!", true);
      if($("#authRegUser")) $("#authRegUser").focus();
      return;
    }
    if(!name){
      toast("⚠️ សូមបញ្ចូលឈ្មោះពេញ!", true);
      if($("#authRegName")) $("#authRegName").focus();
      return;
    }
    if(!contact){
      toast("⚠️ សូមបញ្ចូលលេខទូរស័ព្ទ ឬ Telegram!", true);
      if($("#authRegContact")) $("#authRegContact").focus();
      return;
    }
    if(!password || password.length < 4){
      toast("⚠️ ពាក្យសម្ងាត់ត្រូវមានយ៉ាងតិច ៤ ខ្ទង់!", true);
      if($("#authRegPass")) $("#authRegPass").focus();
      return;
    }

    authRegSubmitBtn.disabled = true;
    authRegSubmitBtn.innerHTML = "<span>កំពុងបង្កើតគណនី...</span>";
    try {
      const res = await fetch("/dl/access/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username, name, contact, password, note, package: '1_year',
          device_id: (window.userAccess && window.userAccess.device_id) || ''
        })
      });
      const j = await res.json();
      if(j.ok){
        localStorage.setItem('syd_auth_token', j.token || '');
        localStorage.setItem('syd_auth_user', JSON.stringify(j.user || {}));
        isMandatoryAuth = false;
        window.userAccess = j.user;
        await fetchAccessStatus();

        // Pre-populate VIP fields with registered credentials
        if($("#regNameInput")) $("#regNameInput").value = j.user.name || name;
        if($("#regContactInput")) $("#regContactInput").value = j.user.contact || contact;

        toast("🎉 ចុះឈ្មោះជោគជ័យ! អ្នកជា User ធម្មតា (ភាគ 1-10 ឥតគិតថ្លៃ)។ សូមស្នើសុំ VIP ដើម្បីដោះសោរគ្រប់ភាគ!", false);
        openUserRegisterModal('vip', false);
      } else {
        toast("⚠️ " + (j.error || "បរាជ័យក្នុងការចុះឈ្មោះ"), true);
      }
    } catch(e){
      toast("⚠️ កំហុសបណ្តាញ៖ " + e, true);
    } finally {
      authRegSubmitBtn.disabled = false;
      authRegSubmitBtn.innerHTML = "<span>🎉 ចុះឈ្មោះប្រើប្រាស់ (Register Free)</span>";
    }
  };
}

// VIP Request Submission
async function doSubmitVipRequest() {
  if(!window.userAccess || !window.userAccess.authenticated){
    toast("⚠️ ដាច់ខាតត្រូវតែចុះឈ្មោះ User ធម្មតាជាមុនសិន មុនការស្នើសុំ VIP!", true);
    openUserRegisterModal('register', true);
    return;
  }

  const name = ($("#regNameInput") && $("#regNameInput").value.trim()) || (window.userAccess && (window.userAccess.name || window.userAccess.username)) || '';
  const contact = ($("#regContactInput") && $("#regContactInput").value.trim()) || (window.userAccess && window.userAccess.contact) || '';
  const note = ($("#regNoteInput") && $("#regNoteInput").value.trim()) || '';
  const checkedPkg = document.querySelector('input[name="vipPackageRadio"]:checked');
  const packageVal = (checkedPkg && checkedPkg.value) || '1_year';

  if(!name){
    toast("⚠️ សូមបញ្ចូលឈ្មោះរបស់អ្នក!", true);
    if($("#regNameInput")) $("#regNameInput").focus();
    return;
  }
  if(!contact){
    toast("⚠️ សូមបញ្ចូលលេខទូរស័ព្ទ ឬ Telegram!", true);
    if($("#regContactInput")) $("#regContactInput").focus();
    return;
  }
  const regSubBtn = $("#regSubmitBtn");
  if(regSubBtn){
    regSubBtn.disabled = true;
    regSubBtn.innerHTML = "<span>កំពុងផ្ញើសំណើ...</span>";
  }
  try {
    const tok = localStorage.getItem('syd_auth_token') || '';
    const res = await fetch("/dl/access/request-vip", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: tok,
        package: packageVal,
        note: note,
        name: name,
        contact: contact,
        device_id: (window.userAccess && window.userAccess.device_id) || ''
      })
    });
    const j = await res.json();
    if(j.ok){
      toast("✅ សំណើសុំ VIP ត្រូវបានបញ្ជូនតាមរយៈ Firebase Realtime Database រួចរាល់! សូមរង់ចាំ Admin អនុម័ត...", false);
      await fetchAccessStatus();
      if(currentAdminPin) refreshAdminUsersList();
    } else {
      toast("⚠️ " + (j.error || "បរាជ័យក្នុងការផ្ញើសំណើ"), true);
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ៖ " + e, true);
  } finally {
    if(regSubBtn){
      regSubBtn.disabled = false;
      regSubBtn.innerHTML = "<span>🚀 ផ្ញើសំណើសុំកញ្ចប់ VIP ទៅកាន់ Admin</span>";
    }
  }
}

const regSubBtn = $("#regSubmitBtn");
if(regSubBtn){
  regSubBtn.onclick = doSubmitVipRequest;
}

/* ---------- Admin Access Panel Handlers ---------- */
async function checkAndUnlockAdmin(pin){
  if(!pin) return false;
  try {
    const tok = localStorage.getItem('syd_auth_token') || '';
    const res = await fetch(`/dl/access/admin/users?pin=${encodeURIComponent(pin)}&token=${encodeURIComponent(tok)}`);
    const j = await res.json();
    if(j.ok){
      currentAdminPin = pin;
      sessionStorage.setItem('hg_admin_pin', pin);
      const pinBox = $("#adminPinBox"); if(pinBox) pinBox.hidden = true;
      const unPanel = $("#adminUnlockedPanel"); if(unPanel) unPanel.hidden = false;
      const lockBadge = $("#adminLockBadge");
      if(lockBadge){
        lockBadge.textContent = "🔓 UNLOCKED";
        lockBadge.style.color = "var(--good)";
        lockBadge.style.background = "rgba(46,204,113,0.15)";
      }
      renderAdminMode(j.mode);
      renderAdminUserList(j.users || []);
      return true;
    } else {
      toast("⚠️ PIN មិនត្រឹមត្រូវ!", true);
      return false;
    }
  } catch(e){
    toast("⚠️ កំហុសបណ្តាញ៖ " + e, true);
    return false;
  }
}

/* ---------- Tab Switcher for Admin Dashboard ---------- */
window.switchUcTab = function(tab){
  const bUsers = $("#ucTabBtnUsers"), bSet = $("#ucTabBtnSettings"), bSys = $("#ucTabBtnSys"), bFb = $("#ucTabBtnFirebase");
  const sUsers = $("#ucTabUsersSec"), sSet = $("#ucTabSettingsSec"), sSys = $("#ucTabSysSec"), sFb = $("#ucTabFirebaseSec");
  if(bUsers) bUsers.classList.toggle('on', tab === 'users');
  if(bSet) bSet.classList.toggle('on', tab === 'settings');
  if(bSys) bSys.classList.toggle('on', tab === 'system');
  if(bFb) bFb.classList.toggle('on', tab === 'firebase');
  if(sUsers) sUsers.style.display = (tab === 'users') ? 'flex' : 'none';
  if(sSet) sSet.style.display = (tab === 'settings') ? 'flex' : 'none';
  if(sSys) sSys.style.display = (tab === 'system') ? 'flex' : 'none';
  if(sFb) sFb.style.display = (tab === 'firebase') ? 'flex' : 'none';

  if(tab === 'firebase'){
    loadFirebaseConfig();
    refreshFirebaseLicenses();
  }
};

let cachedAdminUsers = [];
let currentAdminFilter = 'all';
let currentAdminSearch = '';

function renderAdminMode(mode){
  const radios = document.querySelectorAll('input[name="adminModeRadio"]');
  radios.forEach(r => {
    r.checked = (r.value === mode);
  });
}

function renderAdminSettings(settings){
  if(!settings) return;
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
        toast("✅ បានរក្សាទុកការកំណត់ Telegram & System Mode ដោយជោគជ័យ!");
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

/* ---------- Firebase Realtime Database Handlers ---------- */
let cachedFirebaseLicenses = [];

async function loadFirebaseConfig(){
  try {
    const pin = currentAdminPin || '8888';
    const tok = localStorage.getItem('syd_auth_token') || '';
    const res = await fetch(`/dl/firebase/config?pin=${encodeURIComponent(pin)}&token=${encodeURIComponent(tok)}`);
    const j = await res.json();
    if(j.ok && j.config){
      if($("#fbDbUrlInput")) $("#fbDbUrlInput").value = j.config.database_url || '';
      if($("#fbAuthSecretInput")) $("#fbAuthSecretInput").value = j.config.auth_secret || '';
    }
  } catch(e){}
}

async function testFirebaseConnection(){
  const url = ($("#fbDbUrlInput") && $("#fbDbUrlInput").value.trim()) || '';
  const secret = ($("#fbAuthSecretInput") && $("#fbAuthSecretInput").value.trim()) || '';
  const btn = $("#fbTestConnBtn");
  const msgEl = $("#fbTestMsg");
  const badge = $("#fbLiveStatusBadge");
  if(btn){ btn.disabled = true; btn.textContent = "⏳ កំពុងតេស្ត..."; }
  if(msgEl){ msgEl.style.display = "none"; }
  try {
    const res = await fetch("/dl/firebase/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ database_url: url, auth_secret: secret })
    });
    const j = await res.json();
    if(j.ok){
      toast("✅ " + j.message);
      if(badge){
        badge.textContent = "🟢 Connected";
        badge.style.color = "var(--good)";
        badge.style.background = "rgba(46,204,113,0.15)";
      }
      if(msgEl){
        msgEl.textContent = "✅ " + j.message;
        msgEl.style.display = "block";
        msgEl.style.background = "rgba(46,204,113,0.15)";
        msgEl.style.color = "var(--good)";
      }
      refreshFirebaseLicenses();
    } else {
      toast("❌ " + (j.message || "ភ្ជាប់មិនបាន"), true);
      if(badge){
        badge.textContent = "🔴 Error";
        badge.style.color = "var(--bad)";
        badge.style.background = "rgba(255,46,99,0.15)";
      }
      if(msgEl){
        msgEl.textContent = "❌ " + j.message;
        msgEl.style.display = "block";
        msgEl.style.background = "rgba(255,46,99,0.15)";
        msgEl.style.color = "var(--bad)";
      }
    }
  } catch(e){
    toast("❌ " + e, true);
  } finally {
    if(btn){ btn.disabled = false; btn.textContent = "🔌 តេស្តភ្ជាប់ (Test Connection)"; }
  }
}

async function saveFirebaseConfig(){
  const url = ($("#fbDbUrlInput") && $("#fbDbUrlInput").value.trim()) || '';
  const secret = ($("#fbAuthSecretInput") && $("#fbAuthSecretInput").value.trim()) || '';
  const pin = currentAdminPin || '8888';
  const tok = localStorage.getItem('syd_auth_token') || '';
  const btn = $("#fbSaveConfigBtn");
  if(btn){ btn.disabled = true; btn.textContent = "⏳ កំពុងរក្សាទុក..."; }
  try {
    const res = await fetch("/dl/firebase/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pin,
        token: tok,
        config: {
          enabled: true,
          database_url: url,
          auth_secret: secret,
          sync_interval_seconds: 25
        }
      })
    });
    const j = await res.json();
    if(j.ok){
      toast("✅ បានរក្សាទុកការកំណត់ Firebase Realtime Database ជោគជ័យ!");
      refreshFirebaseLicenses();
    } else {
      toast("⚠️ " + (j.error || "បរាជ័យក្នុងការរក្សាទុក"), true);
    }
  } catch(e){
    toast("⚠️ " + e, true);
  } finally {
    if(btn){ btn.disabled = false; btn.textContent = "💾 រក្សាទុក Config"; }
  }
}

async function refreshFirebaseLicenses(){
  const cont = $("#fbLicensesContainer");
  const countEl = $("#fbLicensesCount");
  const pin = currentAdminPin || '8888';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch(`/dl/firebase/admin/licenses?pin=${encodeURIComponent(pin)}&token=${encodeURIComponent(tok)}`);
    const j = await res.json();
    if(j.ok){
      cachedFirebaseLicenses = j.licenses || [];
      if(countEl) countEl.textContent = cachedFirebaseLicenses.length;
      renderFirebaseLicensesList(cachedFirebaseLicenses);
    }
  } catch(e){
    if(cont) cont.innerHTML = `<div style="text-align:center;padding:16px;color:var(--bad)">⚠️ បរាជ័យក្នុងការទាញយកបញ្ជីពី Firebase: ${esc(e)}</div>`;
  }
}

function renderFirebaseLicensesList(licenses){
  const cont = $("#fbLicensesContainer");
  if(!cont) return;
  if(!licenses || !licenses.length){
    cont.innerHTML = `
      <div style="text-align:center;padding:32px 16px;background:var(--surface);border:1px dashed var(--line);border-radius:12px;color:var(--muted)">
        <div style="font-size:24px;margin-bottom:6px">☁️</div>
        <div style="font-weight:700;color:var(--ink-2)">មិនទាន់មានសំណើលើ Firebase Realtime នៅឡើយទេ</div>
        <div style="font-size:11.5px;margin-top:4px">នៅពេល User PC ចុច &quot;ស្នើសុំ VIP&quot; សំណើនឹងធ្លាក់ចូលទីនេះភ្លាមៗ!</div>
      </div>
    `;
    return;
  }

  let html = "";
  licenses.forEach(item => {
    const isVip = Boolean(item.is_vip);
    const isPending = (item.status === 'pending_vip');
    const isBanned = (item.status === 'banned');
    const isExpired = (item.status === 'expired');

    let badgeBg = "rgba(255,255,255,0.06)", badgeColor = "var(--muted)", statusText = "User ធម្មតា";
    if(isPending){
      badgeBg = "rgba(241,196,15,0.2)"; badgeColor = "var(--gold)"; statusText = "⏳ ស្នើសុំ VIP (Pending)";
    } else if(isBanned){
      badgeBg = "rgba(255,46,99,0.2)"; badgeColor = "var(--bad)"; statusText = "🚫 BANNED";
    } else if(isExpired){
      badgeBg = "rgba(230,126,34,0.2)"; badgeColor = "#e67e22"; statusText = "⌛ EXPIRED";
    } else if(isVip){
      badgeBg = "rgba(46,204,113,0.2)"; badgeColor = "var(--good)"; statusText = `👑 VIP (${item.package_name || item.approved_package || 'Active'})`;
    }

    const devId = item.device_id || item.key || '';
    const displayName = item.name || item.username || 'User PC';
    const contact = item.contact || 'គ្មានទំនាក់ទំនង';
    const note = item.note ? `<div style="font-size:11px;color:var(--muted);margin-top:2px;font-style:italic">📝 ចំណាំ៖ ${esc(item.note)}</div>` : '';
    const expText = item.expires_date ? `ផុតកំណត់៖ ${item.expires_date} (${item.days_left >= 0 ? item.days_left + ' ថ្ងៃទៀត' : 'Lifetime'})` : '';

    html += `
      <div style="background:var(--surface);border:1px solid ${isPending ? 'rgba(241,196,15,0.4)' : 'var(--line)'};padding:12px 14px;border-radius:12px;display:flex;flex-direction:column;gap:8px;box-shadow:${isPending ? '0 0 12px rgba(241,196,15,0.1)' : 'none'}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;flex-wrap:wrap">
          <div>
            <div style="display:flex;align-items:center;gap:8px">
              <span style="font-weight:800;font-size:13.5px;color:var(--ink)">${esc(displayName)}</span>
              <span style="font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:10px;background:${badgeBg};color:${badgeColor}">${statusText}</span>
            </div>
            <div style="font-size:11.5px;color:var(--muted);margin-top:2px">
              📞 ទំនាក់ទំនង: <b style="color:var(--ink-2)">${esc(contact)}</b>
              ${item.requested_package ? ` | កញ្ចប់ស្នើសុំ: <b style="color:var(--accent)">${esc(item.requested_package)}</b>` : ''}
            </div>
            <div style="font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-top:2px">
              💻 Device ID: <span style="color:var(--ink-2);user-select:all">${esc(devId)}</span>
            </div>
            ${note}
            ${expText ? `<div style="font-size:11px;color:var(--good);margin-top:3px;font-weight:600">⏳ ${expText}</div>` : ''}
          </div>

          <!-- Action Buttons -->
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
            <button class="btn primary sm" onclick="firebaseApproveLicense('${esc(devId)}', '1_year')" style="font-size:11px;font-weight:700;padding:4px 10px;background:linear-gradient(135deg,#ff6a2b,#ff2e63)">
              ✅ Approve 1 ឆ្នាំ
            </button>
            <button class="btn ghost sm" onclick="firebaseApproveLicense('${esc(devId)}', '1_month')" style="font-size:11px;padding:4px 8px">
              1 ខែ
            </button>
            <button class="btn ghost sm" onclick="firebaseApproveLicense('${esc(devId)}', 'lifetime')" style="font-size:11px;padding:4px 8px;color:var(--gold)">
              👑 Lifetime
            </button>
            <button class="btn ghost sm" onclick="firebaseCustomDaysApprove('${esc(devId)}')" style="font-size:11px;padding:4px 8px">
              ⏳ ថ្ងៃផ្ទាល់
            </button>
            ${isBanned ? `
              <button class="btn ghost sm" onclick="firebaseUnbanLicense('${esc(devId)}')" style="font-size:11px;padding:4px 8px;color:var(--good);border:1px solid rgba(46,204,113,0.4)">
                🟢 Unban
              </button>
            ` : `
              <button class="btn ghost sm" onclick="firebaseBanLicense('${esc(devId)}')" style="font-size:11px;padding:4px 8px;color:var(--bad)">
                🚫 Ban
              </button>
            `}
            <button class="btn ghost sm" onclick="firebaseDeleteLicense('${esc(devId)}')" style="font-size:11px;padding:4px 8px;color:var(--muted)" title="Delete from Firebase">
              🗑️
            </button>
          </div>
        </div>
      </div>
    `;
  });
  cont.innerHTML = html;
}

window.firebaseApproveLicense = async function(devId, pkg, customDays = null){
  if(!devId) return;
  const pin = currentAdminPin || '8888';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/firebase/admin/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin, token: tok, device_id: devId, package: pkg, custom_days: customDays })
    });
    const j = await res.json();
    if(j.ok){
      toast(`✅ បានបើកសិទ្ធិ VIP ជូន ${devId.substring(0,8)}... ក្នុង Firebase ដោយជោគជ័យ!`);
      refreshFirebaseLicenses();
      refreshAdminUsersList();
    } else {
      toast("⚠️ " + (j.error || "Approval Failed"), true);
    }
  } catch(e){
    toast("⚠️ " + e, true);
  }
};

window.firebaseCustomDaysApprove = function(devId){
  const daysStr = prompt("សូមបញ្ចូលចំនួនថ្ងៃ VIP (ឧ. 30, 60, 180 ឬ -1 សម្រាប់ Lifetime):", "30");
  if(daysStr === null) return;
  const d = parseInt(daysStr);
  if(isNaN(d) || (d <= 0 && d !== -1)){
    alert("សូមបញ្ចូលចំនួនថ្ងៃត្រឹមត្រូវ");
    return;
  }
  firebaseApproveLicense(devId, 'custom', d);
};

window.firebaseBanLicense = async function(devId){
  if(!confirm(`តើអ្នកពិតជាចង់ Ban ឧបករណ៍ ${devId.substring(0,8)}... នេះមែនទេ?`)) return;
  const pin = currentAdminPin || '8888';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/firebase/admin/ban", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin, token: tok, device_id: devId, banned: true })
    });
    const j = await res.json();
    if(j.ok){
      toast("🚫 ឧបករណ៍ត្រូវបាន Ban លើ Firebase រួចរាល់");
      refreshFirebaseLicenses();
      refreshAdminUsersList();
    }
  } catch(e){
    toast("⚠️ " + e, true);
  }
};

window.firebaseUnbanLicense = async function(devId){
  if(!confirm(`តើអ្នកពិតជាចង់បើកសិទ្ធិ (Unban) ឧបករណ៍ ${devId.substring(0,8)}... នេះឡើងវិញមែនទេ?`)) return;
  const pin = currentAdminPin || '8888';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/firebase/admin/ban", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin, token: tok, device_id: devId, banned: false })
    });
    const j = await res.json();
    if(j.ok){
      toast("🟢 បានបើកដំណើរការឧបករណ៍ឡើងវិញ (Unbanned)");
      refreshFirebaseLicenses();
      refreshAdminUsersList();
    }
  } catch(e){
    toast("⚠️ " + e, true);
  }
};

window.firebaseDeleteLicense = async function(devId){
  if(!confirm(`តើអ្នកពិតជាចង់លុបទិន្នន័យ ${devId.substring(0,8)}... ចេញពី Firebase Realtime Database នេះមែនទេ?`)) return;
  const pin = currentAdminPin || '8888';
  const tok = localStorage.getItem('syd_auth_token') || '';
  try {
    const res = await fetch("/dl/firebase/admin/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pin, token: tok, device_id: devId })
    });
    const j = await res.json();
    if(j.ok){
      toast("🗑️ បានលុបទិន្នន័យពី Firebase រួចរាល់");
      refreshFirebaseLicenses();
    }
  } catch(e){
    toast("⚠️ " + e, true);
  }
};

// Bind Firebase Buttons
const fbTestBtn = $("#fbTestConnBtn");
if(fbTestBtn) fbTestBtn.onclick = testFirebaseConnection;
const fbSaveBtn = $("#fbSaveConfigBtn");
if(fbSaveBtn) fbSaveBtn.onclick = saveFirebaseConfig;
const fbRefLicBtn = $("#fbRefreshLicensesBtn");
if(fbRefLicBtn) fbRefLicBtn.onclick = refreshFirebaseLicenses;

// Background Firebase Sync Loop (Every 25 seconds for User PC Auto-Unlock)
let lastKnownVipState = null;
async function backgroundFirebaseSync(){
  try {
    const tok = localStorage.getItem('syd_auth_token') || '';
    const devId = (window.userAccess && window.userAccess.device_id) || '';
    if(!tok && !devId) return;
    
    // Only poll if not already confirmed admin
    if(window.userAccess && window.userAccess.is_admin) return;

    const res = await fetch("/dl/firebase/sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: tok, device_id: devId })
    });
    const j = await res.json();
    if(j.ok && j.user){
      const wasVip = (lastKnownVipState === true || (window.userAccess && window.userAccess.is_vip === true));
      const isNowVip = (j.user.is_vip === true);
      lastKnownVipState = isNowVip;

      if(!wasVip && isNowVip){
        // INSTANT VIP UNLOCK CELEBRATION!
        window.userAccess = j.user;
        renderUserStatusBanner(j.user);
        toast(`🎉 អបអរសាទរ! Admin បានបើកសិទ្ធិ ${j.user.package_name || 'VIP'} ជូនលោកអ្នករួចរាល់តាមរយៈ Firebase Cloud!`);
        // Refresh episode buttons to unlock 11-N
        if(typeof renderEpisodes === 'function' && window.currentDrama){
          renderEpisodes(window.currentDrama);
        }
      }
    }
  } catch(e){}
}
setInterval(backgroundFirebaseSync, 25000);
setTimeout(backgroundFirebaseSync, 4000);

function openUserControl() {
  const m = $("#userCtrlModal");
  if(!m) return;
  const q = $("#ubQuality"), s = $("#ubSeries");
  if(q && $("#ucQuality")) $("#ucQuality").value = q.value;
  if(s && $("#ucSeries")) $("#ucSeries").value = s.value;
  if($("#dirPath") && $("#ucFolderPath")) $("#ucFolderPath").textContent = $("#dirPath").textContent || (IS_CLOUD ? CLOUD_DIR : "Downloads/Hongguo");
  
  // If user is ADMIN, auto unlock control panel immediately!
  if(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin')){
    currentAdminPin = localStorage.getItem('syd_auth_token') || '8888';
    const pinBox = $("#adminPinBox"); if(pinBox) pinBox.hidden = true;
    const unPanel = $("#adminUnlockedPanel"); if(unPanel) unPanel.hidden = false;
    const lockBadge = $("#adminLockBadge");
    if(lockBadge){
      lockBadge.textContent = "🔓 UNLOCKED (ADMIN)";
      lockBadge.style.color = "var(--good)";
      lockBadge.style.background = "rgba(46,204,113,0.15)";
    }
    refreshAdminUsersList();
  } else if(currentAdminPin) {
    checkAndUnlockAdmin(currentAdminPin);
  }
  m.hidden = false;

}
function closeUserControl() {
  const m = $("#userCtrlModal");
  if(m) m.hidden = true;
}
const topUc = $("#topUserCtrlBtn"); if(topUc) topUc.onclick = openUserControl;
const ucCl = $("#userCtrlClose"); if(ucCl) ucCl.onclick = closeUserControl;
const ucClB = $("#userCtrlCloseB"); if(ucClB) ucClB.onclick = closeUserControl;
const ucMod = $("#userCtrlModal"); if(ucMod) ucMod.addEventListener('click', e => { if(e.target === ucMod) closeUserControl(); });

const ucQ = $("#ucQuality");
if(ucQ) ucQ.onchange = e => {
  if($("#ubQuality")) $("#ubQuality").value = e.target.value;
  saveUB();
  toast("Quality set to " + e.target.value);
};
const ucS = $("#ucSeries");
if(ucS) ucS.onchange = e => {
  if($("#ubSeries")) $("#ubSeries").value = e.target.value;
  saveUB();
  toast("Parallel series set to " + e.target.value);
};
const ucOpenF = $("#ucOpenFolder"); if(ucOpenF) ucOpenF.onclick = openDir;
const ucChF = $("#ucChangeFolder"); if(ucChF) ucChF.onclick = pickDir;

/* ---------- Universal PC Local Storage Engine & Folder Picker Logic ---------- */
let IS_CLOUD = false;
let CLOUD_DIR = '/app/data/downloads';

const DEFAULT_CLIENT_DRIVES = [
  { letter: 'C', drive: 'C:\\', free_gb: '128.8' },
  { letter: 'D', drive: 'D:\\', free_gb: '145.8' },
  { letter: 'E', drive: 'E:\\', free_gb: '240.2' },
  { letter: 'F', drive: 'F:\\', free_gb: '149.7' },
  { letter: 'J', drive: 'J:\\', free_gb: '327.1' }
];

const PC_DB_NAME = "syd_pc_storage_db";
const PC_STORE_NAME = "handles";
let activePcDirHandle = null;
let isSavingToPcLocal = false;
const pcSaveQueue = [];
const savedToPcLocalSet = new Set();

try {
  const arr = JSON.parse(localStorage.getItem("syd_pc_saved_episodes") || "[]");
  arr.forEach(k => savedToPcLocalSet.add(k));
} catch(e){}

function openPcStorageDb(){
  return new Promise((resolve) => {
    if(!window.indexedDB) return resolve(null);
    try {
      const req = indexedDB.open(PC_DB_NAME, 1);
      req.onupgradeneeded = () => { req.result.createObjectStore(PC_STORE_NAME); };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    } catch(e){ resolve(null); }
  });
}

async function getStoredPcDirHandle(){
  try {
    const db = await openPcStorageDb();
    if(!db) return null;
    return new Promise((resolve) => {
      const tx = db.transaction(PC_STORE_NAME, "readonly");
      const st = tx.objectStore(PC_STORE_NAME);
      const req = st.get("local_dir");
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => resolve(null);
    });
  } catch(e){
    return null;
  }
}

async function setStoredPcDirHandle(handle){
  try {
    const db = await openPcStorageDb();
    if(!db) return false;
    return new Promise((resolve) => {
      const tx = db.transaction(PC_STORE_NAME, "readwrite");
      const st = tx.objectStore(PC_STORE_NAME);
      const req = st.put(handle, "local_dir");
      req.onsuccess = () => resolve(true);
      req.onerror = () => resolve(false);
    });
  } catch(e){
    return false;
  }
}

async function verifyPcDirPermission(handle, mode = "readwrite"){
  if(!handle) return false;
  try {
    const q = await handle.queryPermission({ mode });
    if(q === "granted") return true;
    const r = await handle.requestPermission({ mode });
    return r === "granted";
  } catch(e){
    return false;
  }
}

async function getValidPcDirHandle(){
  if(activePcDirHandle) return activePcDirHandle;
  const stored = await getStoredPcDirHandle();
  if(stored){
    activePcDirHandle = stored;
    return activePcDirHandle;
  }
  return null;
}

// Stream downloaded episode directly to local PC
async function saveEpisodeToPc(seriesName, epNum, titleKm){
  const cleanSeries = (titleKm || seriesName || "Hongguo_Drama").replace(/[\\/:*?"<>|]/g, "_").trim();
  const filename = `${cleanSeries}_Ep${String(epNum).padStart(2, '0')}.mp4`;
  const url = `/dl/library/video?name=${encodeURIComponent(seriesName)}&ep=${epNum}&download=1`;

  const dirHandle = await getValidPcDirHandle();
  if(dirHandle){
    try {
      const hasPerm = await verifyPcDirPermission(dirHandle);
      if(hasPerm){
        const subDir = await dirHandle.getDirectoryHandle(cleanSeries, { create: true });
        const fileHandle = await subDir.getFileHandle(filename, { create: true });
        const writable = await fileHandle.createWritable();
        
        const resp = await fetch(url);
        if(!resp.ok) throw new Error(`HTTP ${resp.status}`);
        
        if(resp.body && resp.body.pipeTo){
          await resp.body.pipeTo(writable);
        } else {
          const blob = await resp.blob();
          await writable.write(blob);
          await writable.close();
        }
        return true;
      }
    } catch(err){
      console.warn("Direct file write failed, falling back to browser download:", err);
    }
  }

  // Fallback: trigger standard browser download to Downloads folder
  triggerBrowserDownload(seriesName, epNum, cleanSeries);
  return true;
}

function triggerBrowserDownload(seriesName, epNum, cleanSeriesTitle){
  const cleanSeries = cleanSeriesTitle || (seriesName || "Hongguo_Drama").replace(/[\\/:*?"<>|]/g, "_").trim();
  const filename = `${cleanSeries}_Ep${String(epNum).padStart(2, '0')}.mp4`;
  const a = document.createElement('a');
  a.href = `/dl/library/video?name=${encodeURIComponent(seriesName)}&ep=${epNum}&download=1`;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => a.remove(), 1000);
}

// 1-Click Save Entire Series to PC Local
async function saveSeriesToPc(seriesName, titleKm){
  const dispTitle = titleKm || seriesName;
  toast(`⏳ កំពុងរៀបចំរក្សាទុក 《${dispTitle}》 ចូលក្នុង PC Local...`);
  try {
    const res = await (await fetch(`/dl/library/episodes?name=${encodeURIComponent(seriesName)}`)).json();
    if(!res || !res.downloaded || !res.downloaded.length){
      toast(`⚠️ មិនទាន់មានភាគដែលបានដោនឡូតរួចសម្រាប់រឿងនេះទេ!`, true);
      return;
    }
    const eps = res.downloaded;
    const totalEps = eps.length;
    
    // Check if dirHandle is available (user selected a directory via File System Access API)
    const dirHandle = await getValidPcDirHandle();
    if(dirHandle){
      let doneEps = 0;
      for(const ep of eps){
        doneEps++;
        toast(`💾 កំពុង Save ចូល PC Folder: ភាគ ${ep} (${doneEps}/${totalEps})...`, false);
        await saveEpisodeToPc(seriesName, ep, titleKm);
        const key = `${seriesName}_${ep}`;
        savedToPcLocalSet.add(key);
      }
      try {
        localStorage.setItem("syd_pc_saved_episodes", JSON.stringify(Array.from(savedToPcLocalSet)));
      }catch(e){}
      toast(`✅ រក្សាទុករឿង 《${dispTitle}》 ទាំង ${totalEps} ភាគ ចូល PC Local រួចរាល់!`);
      return;
    }

    // Direct Browser Download as complete ZIP to PC (Instant, 100% reliable, 0 annoying popups)
    toast(`📥 កំពុងទាញយករឿង 《${dispTitle}》 ទាំង ${totalEps} ភាគជា ZIP ដាក់ចូល PC របស់អ្នក...`);
    const cleanFile = (dispTitle || seriesName).replace(/[\\/:*?"<>|]/g, '_').trim();
    const a = document.createElement('a');
    a.href = `/dl/library/zip?name=${encodeURIComponent(seriesName)}`;
    a.download = `${cleanFile}_All_Episodes.zip`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => a.remove(), 1500);
    toast(`✅ បានចាប់ផ្តើមទាញយករឿង 《${dispTitle}》 ចូលក្នុង PC រួចរាល់!`);
  } catch(e){
    toast(`បរាជ័យក្នុងការ Save ចូល PC: ${e.message}`, true);
  }
}

// Background auto-save queue processor
async function processPcSaveQueue(){
  if(isSavingToPcLocal || !pcSaveQueue.length) return;
  const autoSaveOn = $("#sqAutoSavePc") ? $("#sqAutoSavePc").checked : true;
  if(!autoSaveOn) return;

  isSavingToPcLocal = true;
  const statusEl = $("#sqPcSaveStatus");
  try {
    while(pcSaveQueue.length > 0){
      const item = pcSaveQueue.shift();
      const key = `${item.series}_${item.ep}`;
      if(savedToPcLocalSet.has(key)) continue;

      if(statusEl) statusEl.textContent = `💾 PC: Ep ${item.ep}...`;
      await saveEpisodeToPc(item.series, item.ep, item.titleKm);
      savedToPcLocalSet.add(key);
      try {
        localStorage.setItem("syd_pc_saved_episodes", JSON.stringify(Array.from(savedToPcLocalSet)));
      }catch(e){}
    }
    if(statusEl) statusEl.textContent = `✓ រួចរាល់ (${savedToPcLocalSet.size} ភាគ)`;
  } catch(e){
    console.warn("Auto-save queue error:", e);
    if(statusEl) statusEl.textContent = `⚠️ បញ្ហា Save`;
  } finally {
    isSavingToPcLocal = false;
  }
}

async function syncActiveDownloadsToPc(st){
  // មិនបាច់ trigger browser download ឡើយ ដោយសារ Backend បាន Save វីដេអូ .mp4 ចូល PC Folder ដោយផ្ទាល់រួចហើយ
  return;
}

async function autoDeliverCompletedDownloadsToPc(){
  // មិនបាច់ trigger browser .zip download ឡើយ ដោយសារវីដេអូមានក្នុង PC Folder រួចជាស្រេច
  return;
}

/* ---------- Folder Picker Modal & Drive Selection Logic ---------- */
async function openFolderPickerModal(){
  const m = $("#folderPickerModal");
  if(!m) return;
  m.hidden = false;
  try {
    const [cfg, drv] = await Promise.all([
      fetch("/dl/config").then(r => r.json()).catch(()=>({})),
      fetch("/dl/drives").then(r => r.json()).catch(()=>({}))
    ]);
    if(cfg){
      IS_CLOUD = false;
    }
    
    // Pre-fill user's PC local path (matching screenshot, e.g. F:\Hongguo)
    const savedPcPath = localStorage.getItem("syd_user_pc_path") || (cfg && cfg.output_dir && !cfg.output_dir.startsWith('/app') ? cfg.output_dir : "F:\\Hongguo");
    if($("#fpPathInput")){
      $("#fpPathInput").value = savedPcPath;
    }

    // Always render available Windows drives (matching user's screenshot C:, D:, E:, F:, J:)
    let drives = (drv && drv.drives && drv.drives.length > 1) ? drv.drives : DEFAULT_CLIENT_DRIVES;
    renderFpDrives(drives);

    // Quick presets
    const fpPreVid = $("#fpPresetVideos");
    if(fpPreVid) fpPreVid.onclick = () => { $("#fpPathInput").value = "C:\\Users\\Administrator\\Videos\\Hongguo"; };
    const fpPreDl = $("#fpPresetDownloads");
    if(fpPreDl) fpPreDl.onclick = () => { $("#fpPathInput").value = "C:\\Users\\Administrator\\Downloads\\Hongguo"; };
  } catch(e){
    console.error("Folder picker error:", e);
    renderFpDrives(DEFAULT_CLIENT_DRIVES);
  }
}

function renderFpDrives(drives){
  const grid = $("#fpDrivesGrid");
  if(!grid) return;
  const list = (drives && drives.length && drives.length > 1) ? drives : DEFAULT_CLIENT_DRIVES;
  grid.innerHTML = list.map(d => {
    return `<button type="button" class="btn ghost sm fp-drv-btn" data-path="${d.drive}Hongguo" style="display:flex;flex-direction:column;align-items:center;padding:7px 4px;text-align:center;border-radius:8px">
      <b style="font-size:13.5px;color:var(--accent)">${d.letter}:</b>
      <span style="font-size:10px;color:var(--good);margin-top:2px">${d.free_gb} GB free</span>
    </button>`;
  }).join('');
}

function closeFolderPickerModal(){
  const m = $("#folderPickerModal");
  if(m) m.hidden = true;
}

const fpCl = $("#fpClose"); if(fpCl) fpCl.onclick = closeFolderPickerModal;
const fpCan = $("#fpCancel"); if(fpCan) fpCan.onclick = closeFolderPickerModal;
const fpMod = $("#folderPickerModal"); if(fpMod) fpMod.addEventListener('click', e => { if(e.target === fpMod) closeFolderPickerModal(); });

const fpDGrid = $("#fpDrivesGrid");
if(fpDGrid){
  fpDGrid.addEventListener('click', e => {
    const btn = e.target.closest(".fp-drv-btn");
    if(btn && btn.dataset.path){
      $("#fpPathInput").value = btn.dataset.path;
      toast("Selected: " + btn.dataset.path);
    }
  });
}

const fpOpenCurr = $("#fpOpenCurrent");
if(fpOpenCurr) fpOpenCurr.onclick = () => { openDir(); };

async function handleNativeBrowse(){
  const fpNat = $("#fpNativeBrowse");
  if(fpNat) fpNat.disabled = true;
  
  // Use modern File System Access API on user's PC (Chrome, Edge, Brave):
  if(window.showDirectoryPicker){
    try {
      const handle = await window.showDirectoryPicker({
        id: "syd_downloader_pc_folder",
        mode: "readwrite",
        startIn: "videos"
      });
      if(handle){
        activePcDirHandle = handle;
        await setStoredPcDirHandle(handle);
        const folderName = handle.name;
        let pcPath = localStorage.getItem("syd_user_pc_path") || "F:\\Hongguo";
        if(pcPath.includes("\\")){
          const parts = pcPath.split("\\");
          parts[parts.length - 1] = folderName;
          pcPath = parts.join("\\");
        } else {
          pcPath = "F:\\" + folderName;
        }
        localStorage.setItem("syd_user_pc_path", pcPath);
        localStorage.setItem("syd_local_pc_folder_name", folderName);
        if($("#fpPathInput")) $("#fpPathInput").value = pcPath;
        syncSqFolder();
        toast(`✅ បានជ្រើសរើស Folder លើ PC: 📁 ${folderName}`);
        if(fpNat) fpNat.disabled = false;
        return true;
      }
    } catch(e){
      if(e.name === 'AbortError'){
        if(fpNat) fpNat.disabled = false;
        return false;
      }
      console.warn("showDirectoryPicker fallback:", e);
    }
  }

  // Fallback on localhost Windows:
  if(!IS_CLOUD){
    try {
      const j = await (await fetch("/dl/pick", { method: "POST" })).json();
      if(j.ok && j.path){
        if($("#fpPathInput")) $("#fpPathInput").value = j.path;
        localStorage.setItem("syd_user_pc_path", j.path);
        syncSqFolder();
        toast("Folder chosen: " + j.path);
        if(fpNat) fpNat.disabled = false;
        return true;
      }
    } catch(e){}
  }
  
  if(fpNat) fpNat.disabled = false;
  return false;
}

const fpNat = $("#fpNativeBrowse");
if(fpNat) fpNat.onclick = handleNativeBrowse;

const fpSave = $("#fpSave");
if(fpSave){
  fpSave.onclick = async () => {
    const newPath = ($("#fpPathInput").value || "").trim();
    if(!newPath){ toast("Please enter a folder path", true); return; }
    fpSave.disabled = true;
    fpSave.textContent = "Saving...";
    try {
      localStorage.setItem("syd_user_pc_path", newPath);
      localStorage.setItem("syd_local_pc_folder_name", newPath.split("\\").pop() || newPath);
      syncSqFolder();

      // Inform backend (backend on cloud safely sanitizes)
      try {
        await fetch("/dl/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ output_dir: newPath })
        });
      } catch(e){}

      toast("✅ Folder saved: " + newPath);
      closeFolderPickerModal();
    } catch(e){
      toast("Save failed: " + e, true);
    } finally {
      fpSave.disabled = false;
      fpSave.textContent = "💾 Save Location";
    }
  };
}

/* ---------- Web Storage Explorer Logic ---------- */
let seCachedData = null;

async function openStorageExplorerModal(){
  const m = $("#storageExplorerModal");
  if(!m) return;
  m.hidden = false;
  await refreshStorageExplorer();
}

function closeStorageExplorerModal(){
  const m = $("#storageExplorerModal");
  if(m) m.hidden = true;
}

const seCl = $("#seClose"); if(seCl) seCl.onclick = closeStorageExplorerModal;
const seDn = $("#seDoneBtn"); if(seDn) seDn.onclick = closeStorageExplorerModal;
const seMod = $("#storageExplorerModal"); if(seMod) seMod.addEventListener('click', e => { if(e.target === seMod) closeStorageExplorerModal(); });
const seRef = $("#seRefreshBtn"); if(seRef) seRef.onclick = () => { refreshStorageExplorer(); };

const seSearch = $("#seSearchInput");
if(seSearch){
  seSearch.oninput = () => {
    filterStorageExplorer(seSearch.value);
  };
}

const seSaveAll = $("#seSaveAllPcBtn");
if(seSaveAll){
  seSaveAll.onclick = async () => {
    if(!seCachedData || !seCachedData.series || !seCachedData.series.length){
      toast("មិនទាន់មានវីដេអូសម្រាប់ Save ទេ");
      return;
    }
    toast(`💾 កំពុងចាប់ផ្តើមទាញយកវីដេអូទាំងអស់ចូល PC...`);
    for(const s of seCachedData.series){
      const dispTitle = s.title_km || s.title || s.folder_name;
      await saveSeriesToPc(s.folder_name, dispTitle);
      await new Promise(r => setTimeout(r, 1200));
    }
  };
}

async function refreshStorageExplorer(){
  const container = $("#seSeriesContainer");
  if(!container) return;
  container.innerHTML = '<div style="text-align:center;color:var(--muted);padding:40px 20px;font-size:13px">⏳ កំពុងទាញយកបញ្ជីឯកសារវីដេអូ...</div>';
  try {
    const data = await (await fetch("/dl/storage/files")).json();
    if(!data || !data.ok){
      container.innerHTML = `<div style="text-align:center;color:var(--bad,#ef4444);padding:30px">❌ មិនអាចទាញយកទិន្នន័យបានទេ: ${esc((data && data.error) || 'Unknown error')}</div>`;
      return;
    }
    seCachedData = data;
    const pcPath = localStorage.getItem("syd_user_pc_path") || "F:\\Hongguo";
    if($("#seCurrentPath")) $("#seCurrentPath").textContent = pcPath;
    if($("#seDiskFree")) $("#seDiskFree").textContent = "MP4 រួចរាល់ (" + (data.free_gb || '—') + " GB ទំនេរ)";
    if($("#seStatsChip")) $("#seStatsChip").textContent = `${data.total_series || 0} រឿង · ${data.total_videos || 0} ភាគ`;
    if($("#seTotalStorage")) $("#seTotalStorage").textContent = data.total_bytes_str || '0 MB';
    renderStorageExplorer(data.series || []);
  } catch(e){
    container.innerHTML = `<div style="text-align:center;color:var(--bad,#ef4444);padding:30px">❌ បរាជ័យក្នុងការតភ្ជាប់: ${esc(e)}</div>`;
  }
}

function filterStorageExplorer(query){
  if(!seCachedData || !seCachedData.series) return;
  const q = (query || "").trim().toLowerCase();
  if(!q){
    renderStorageExplorer(seCachedData.series);
    return;
  }
  const filtered = seCachedData.series.filter(s => {
    return (s.title && s.title.toLowerCase().includes(q)) ||
           (s.title_km && s.title_km.toLowerCase().includes(q)) ||
           (s.folder_name && s.folder_name.toLowerCase().includes(q));
  });
  renderStorageExplorer(filtered);
}

function renderStorageExplorer(seriesList){
  const container = $("#seSeriesContainer");
  if(!container) return;
  if(!seriesList || seriesList.length === 0){
    container.innerHTML = `
      <div style="text-align:center;padding:40px 20px;color:var(--muted)">
        <div style="font-size:36px;margin-bottom:8px">📭</div>
        <div style="font-weight:700;font-size:15px;color:var(--ink)">មិនទាន់មានវីដេអូដែលបានទាញយកនៅឡើយទេ</div>
        <div style="font-size:12.5px;margin-top:4px">សូមជ្រើសរើសរឿង និងចុចដោនឡូត នោះវីដេអូនឹងបង្ហាញនៅទីនេះ!</div>
      </div>
    `;
    return;
  }

  container.innerHTML = seriesList.map((s, idx) => {
    const dispTitle = s.title_km || s.title || s.folder_name;
    const origTitle = (s.title && s.title !== dispTitle) ? `<small style="color:var(--muted);font-weight:400;margin-left:4px">(${esc(s.title)})</small>` : '';
    const coverHtml = s.cover ? `<img src="/img?url=${encodeURIComponent(s.cover)}" style="width:48px;height:64px;object-fit:cover;border-radius:6px;flex-shrink:0" alt="">` : `<div style="width:48px;height:64px;background:var(--surface-3);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">🎬</div>`;

    return `
      <div class="se-card" style="background:var(--surface-2);border:1px solid var(--line);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:10px">
        <div style="display:flex;gap:12px;align-items:center">
          ${coverHtml}
          <div style="flex:1;min-width:0">
            <div style="font-weight:700;font-size:14.5px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
              ${esc(dispTitle)} ${origTitle}
            </div>
            <div style="display:flex;gap:8px;align-items:center;margin-top:4px;flex-wrap:wrap">
              <span class="chip" style="font-size:11px;padding:2px 7px;background:rgba(59,130,246,0.15);color:#60a5fa;border:1px solid rgba(59,130,246,0.25)">
                ⚡ ${s.ep_count} ភាគ
              </span>
              <span class="chip" style="font-size:11px;padding:2px 7px;background:rgba(255,255,255,0.06);color:var(--ink-2)">
                💾 ${s.folder_size_str}
              </span>
            </div>
          </div>
          <div style="display:flex;gap:6px;align-items:center;flex-shrink:0">
            <button class="btn accent sm se-play-btn" data-sname="${esc(s.folder_name)}" style="padding:4px 10px;font-size:12px">🎬 ទស្សនា</button>
            <button class="btn primary sm se-save-pc-btn" data-sname="${esc(s.folder_name)}" data-stitle="${esc(dispTitle)}" style="padding:4px 10px;font-size:12px">💾 Save ចូល PC</button>
            <button class="btn ghost sm se-expand-btn" data-sidx="${idx}" style="padding:4px 10px;font-size:12px">📂 ភាគ & ទាញយក</button>
            <a href="/dl/library/zip?name=${encodeURIComponent(s.folder_name)}" download class="btn ghost sm" title="ទាញយកភាគទាំងអស់ជា ZIP ដាក់កុំព្យូទ័រ" style="padding:4px 10px;font-size:12px;text-decoration:none;display:inline-flex;align-items:center;gap:4px">📦 ZIP</a>
          </div>
        </div>

        <!-- Collapsible Episode List -->
        <div class="se-eps-panel" id="seEpsPanel_${idx}" hidden style="border-top:1px solid var(--line);padding-top:10px;margin-top:2px">
          <div style="font-size:12px;font-weight:700;color:var(--ink-2);margin-bottom:8px;display:flex;justify-content:space-between;align-items:center">
            <span>បញ្ជីភាគដែលបានដោនឡូតរួច (ចុចលើប៊ូតុង ដើម្បី Download មក PC):</span>
            <div style="display:flex;gap:6px">
              <button class="btn primary sm se-panel-save-pc" data-sname="${esc(s.folder_name)}" data-stitle="${esc(dispTitle)}" style="padding:2px 8px;font-size:11px">💾 Save គ្រប់ភាគចូល PC</button>
              <a href="/dl/library/zip?name=${encodeURIComponent(s.folder_name)}" download class="btn accent sm" style="padding:2px 8px;font-size:11px;text-decoration:none">⬇️ ទាញយកទាំងអស់ (.ZIP)</a>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:6px;max-height:200px;overflow-y:auto;padding-right:4px">
            ${(s.episodes || []).map(ep => `
              <div style="background:var(--surface-3);border:1px solid var(--line);border-radius:6px;padding:6px 8px;display:flex;align-items:center;justify-content:space-between;gap:4px">
                <div style="min-width:0">
                  <b style="font-size:12px;color:var(--ink)">ភាគ ${ep.ep}</b>
                  <div style="font-size:10px;color:var(--muted)">${ep.size_str}</div>
                </div>
                <div style="display:flex;gap:3px">
                  <button type="button" class="btn ghost sm se-ep-play-btn" data-sname="${esc(s.folder_name)}" data-ep="${ep.ep}" title="ទស្សនា" style="padding:2px 6px;font-size:11px">🎬</button>
                  <a href="/dl/library/video?name=${encodeURIComponent(s.folder_name)}&ep=${ep.ep}&download=1" download class="btn accent sm" title="ទាញយក MP4 មកកាន់កុំព្យូទ័រ" style="padding:2px 6px;font-size:11px;text-decoration:none">⬇️</a>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.se-play-btn').forEach(b => {
    b.onclick = () => {
      const sName = b.dataset.sname;
      closeStorageExplorerModal();
      openVideoPlayer(sName, 1);
    };
  });

  container.querySelectorAll('.se-save-pc-btn, .se-panel-save-pc').forEach(b => {
    b.onclick = () => {
      saveSeriesToPc(b.dataset.sname, b.dataset.stitle);
    };
  });

  container.querySelectorAll('.se-ep-play-btn').forEach(b => {
    b.onclick = () => {
      const sName = b.dataset.sname;
      const ep = Number(b.dataset.ep) || 1;
      closeStorageExplorerModal();
      openVideoPlayer(sName, ep);
    };
  });

  container.querySelectorAll('.se-expand-btn').forEach(b => {
    b.onclick = () => {
      const idx = b.dataset.sidx;
      const panel = $(`#seEpsPanel_${idx}`);
      if(panel){
        panel.hidden = !panel.hidden;
        b.textContent = panel.hidden ? "📂 ភាគ & ទាញយក" : "▲ បិទវិញ";
      }
    };
  });
}

/* ---------- Already Downloaded Choice Modal Handlers ---------- */
let pendingAdItem = null;
function showAlreadyDownloadedModal(p, libEntry){
  pendingAdItem = {
    id: p.dataset.id,
    title: p.dataset.t,
    titleKm: p.dataset.tkm || '',
    total: Number(p.dataset.n) || 0,
    cover: p.dataset.cov || '',
    score: p.dataset.sc || '',
    rank: Number(p.dataset.rk) || 0,
    dt: p.dataset.dt || '',
    libName: libEntry.name || libEntry.title
  };
  
  if($("#adTitle")) $("#adTitle").textContent = p.dataset.t;
  if($("#adTitleKm")) $("#adTitleKm").textContent = p.dataset.tkm ? `🇰🇭 ${p.dataset.tkm}` : '';
  const inLib = !libEntry.historyOnly;
  if($("#adModalSub")) $("#adModalSub").textContent = inLib ? `មានក្នុង Library ចំនួន ${libEntry.local} ភាគ` : `ធ្លាប់បាន Download រួចរាល់កាលពីមុន (${libEntry.local} ភាគ)`;
  if($("#adDetails")) $("#adDetails").innerHTML = inLib ? `<b>${libEntry.local}</b> នៃ <b>${libEntry.total || libEntry.local}</b> ភាគមានក្នុង Library` : `<b>${libEntry.local}</b> ភាគបានកត់ត្រាក្នុង Memory History`;
  if($("#adDate")) $("#adDate").textContent = p.dataset.dt ? `📅 កាលបរិច្ឆេទ: ${p.dataset.dt}` : '';
  if($("#adOpenPlay")) $("#adOpenPlay").hidden = !inLib;
  
  const thumbBox = $("#adThumb");
  if(thumbBox){
    thumbBox.innerHTML = p.dataset.cov ? `<img src="/img?url=${encodeURIComponent(p.dataset.cov)}" style="width:100%;height:100%;object-fit:cover" alt="">` : `<div class="grad" style="width:100%;height:100%;background:var(--accent);display:flex;align-items:center;justify-content:center;color:#fff;font-size:20px">🎬</div>`;
  }
  
  const m = $("#alreadyDownloadedModal");
  if(m) m.hidden = false;
}

function closeAlreadyDownloadedModal(){
  const m = $("#alreadyDownloadedModal");
  if(m) m.hidden = true;
  pendingAdItem = null;
}

const adCl = $("#adClose"); if(adCl) adCl.onclick = closeAlreadyDownloadedModal;
const adCa = $("#adCancel"); if(adCa) adCa.onclick = closeAlreadyDownloadedModal;
const adM = $("#alreadyDownloadedModal"); if(adM) adM.addEventListener('click', e => { if(e.target === adM) closeAlreadyDownloadedModal(); });

const adOp = $("#adOpenPlay");
if(adOp) adOp.onclick = () => {
  if(pendingAdItem && pendingAdItem.libName){
    const sName = pendingAdItem.libName;
    closeAlreadyDownloadedModal();
    openLibEpisodes(sName);
  }
};

const adRq = $("#adRequeue");
if(adRq) adRq.onclick = () => {
  if(pendingAdItem){
    const it = pendingAdItem;
    closeAlreadyDownloadedModal();
    addToCart(it.id, it.title, it.total, it.cover, false, it.score, it.rank, it.dt, it.titleKm);
    toast("បានបញ្ចូលទៅក្នុង Queue សម្រាប់ទាញយកឡើងវិញ");
  }
};

const vpFix = $("#vpFixPic");
if(vpFix) {
  vpFix.onclick = async () => {
    if(!currentVpSeries || !currentVpEp) return;
    vpFix.disabled = true;
    const oldText = vpFix.textContent;
    vpFix.textContent = "⏳ Converting (GPU)...";
    toast("Converting Episode " + currentVpEp + " with RTX 5060 GPU…");
    try {
      const res = await (await fetch("/dl/library/transcode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: currentVpSeries, ep: currentVpEp })
      })).json();
      if(res.ok) {
        toast("Video converted to universal H.264! Picture restored.");
        const video = $("#vpVideo");
        const curTime = video.currentTime || 0;
        video.src = `/dl/library/video?name=${encodeURIComponent(currentVpSeries)}&ep=${currentVpEp}&t=${Date.now()}`;
        video.load();
        video.currentTime = curTime;
        video.play().catch(()=>{});
      } else {
        toast("Convert error: " + (res.error || "Unknown"), true);
      }
    } catch(e) {
      toast("Transcode failed: " + e, true);
    } finally {
      vpFix.disabled = false;
      vpFix.textContent = oldText;
    }
  };
}

$("#clearQueue").onclick=()=>{ cart={}; saveCart(); renderQueue(); syncResultButtons(); };

/* ---------- Live Data & Posters Sync from https://hongguoduanju.com/ ---------- */
let liveDataCache = null;
let liveCategory = "all";

async function loadLiveData(force = false, cat = 'all'){
  currentTab = "livedata";
  if(cat) liveCategory = cat;
  const sec = $("#resultsSec"), box = $("#results");
  sec.hidden = false;
  if($("#dramaDetailSec")) $("#dramaDetailSec").hidden = true;
  $("#resLabel").innerHTML = `⚡ Live Data (<a href="https://hongguoduanju.com/" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:underline;font-size:15px">hongguoduanju.com</a>)`;
  $("#boardTabs").hidden = false;
  $("#backHome").hidden = true;
  $("#moreRow").hidden = true;
  $("#explorerPager").hidden = true;
  $("#explorerControls").hidden = true;
  $("#trendCats").hidden = true;
  if($("#liveCats")) $("#liveCats").hidden = false;
  
  document.querySelectorAll("#boardTabs .tab").forEach(t => t.classList.toggle("on", t.dataset.board === "livedata"));
  document.querySelectorAll("#liveCats .exchip").forEach(c => c.classList.toggle("on", c.dataset.livecat === liveCategory));

  if(force || !liveDataCache){
    box.innerHTML = '<div class="empty" style="grid-column:1/-1"><div class="sm" style="font-family:var(--font-km)">⏳ កំពុងទាញយក Poster និងទិន្នន័យផ្សាយផ្ទាល់ពី https://hongguoduanju.com/…</div></div>';
  }

  try {
    const syncIcon = $("#heroSyncIcon");
    if(syncIcon) syncIcon.style.transform = "rotate(360deg)";

    const res = await fetch(`/dl/livedata${force ? '?force=1' : ''}`, {cache: "no-store"});
    const j = await res.json();
    if(syncIcon) setTimeout(() => { syncIcon.style.transform = "none"; }, 500);

    if(j && j.ok){
      liveDataCache = j;
      if(j.total_formatted){
        const totEl = $("#heroTotalPosters");
        if(totEl) totEl.textContent = j.total_formatted;
      }
      if(j.last_sync){
        const timeEl = $("#liveSyncTime");
        if(timeEl) timeEl.textContent = `· ធ្វើបច្ចុប្បន្នភាព: ${j.last_sync}`;
      }
      (j.dramas || []).forEach(d => {
        if(d.title && d.title_km){
          setCachedTrans(d.title, d.title_km);
        }
      });
      renderLiveDramas();
    } else {
      box.innerHTML = `<div class="empty" style="grid-column:1/-1"><div class="sm" style="color:var(--bad)">⚠️ មិនអាចទាញយកទិន្នន័យពី hongguoduanju.com បានទេ (${esc((j&&j.error)||"Error")})</div></div>`;
    }
  } catch(e){
    box.innerHTML = `<div class="empty" style="grid-column:1/-1"><div class="sm" style="color:var(--bad)">⚠️ Error: ${esc(e.message)}</div></div>`;
  }
}

function renderLiveDramas(){
  if(!liveDataCache || !liveDataCache.dramas) return;
  const box = $("#results");
  let list = liveDataCache.dramas || [];
  if(liveCategory !== "all"){
    list = list.filter(d => d.tab_type === liveCategory);
  }
  list = applyDateSort(list);
  const sortNote = currentDateSort === 'asc' ? ' (📅 ពីមុនមកបច្ចុប្បន្ន)' : (currentDateSort === 'desc' ? ' (📅 ពីថ្មីទៅចាស់)' : '');
  $("#resCount").textContent = `· ${list.length} រឿងផ្សាយផ្ទាល់` + sortNote;
  if(!list.length){
    box.innerHTML = '<div class="empty" style="grid-column:1/-1"><div class="sm">មិនមានរឿងក្នុងប្រភេទនេះទេ</div></div>';
    return;
  }
  box.innerHTML = resultCards(list, true);
  syncResultButtons();
}

async function fetchLiveStatsOnly(){
  try {
    const res = await fetch("/dl/livedata", {cache: "no-store"});
    const j = await res.json();
    if(j && j.ok){
      liveDataCache = j;
      const totEl = $("#heroTotalPosters");
      if(totEl && j.total_formatted) totEl.textContent = j.total_formatted;
      const timeEl = $("#liveSyncTime");
      if(timeEl && j.last_sync) timeEl.textContent = `· ធ្វើបច្ចុប្បន្នភាព: ${j.last_sync}`;
      (j.dramas || []).forEach(d => {
        if(d.title && d.title_km){
          setCachedTrans(d.title, d.title_km);
        }
      });
      if(currentTab === "livedata"){
        renderLiveDramas();
      }
    }
  } catch(e){}
}

const heroSyncBtn = $("#heroLiveSyncBtn");
if(heroSyncBtn){
  heroSyncBtn.onclick = async () => {
    toast("🔄 កំពុង Update Posters និងទិន្នន័យពី https://hongguoduanju.com/...");
    await loadLiveData(true, liveCategory);
    toast("🟢 បាន Update Posters ថ្មីៗពី https://hongguoduanju.com/ ដោយជោគជ័យ!");
  };
}

document.querySelectorAll("#liveCats .exchip").forEach(c => {
  c.onclick = () => {
    if(c.dataset.livecat === liveCategory) return;
    liveCategory = c.dataset.livecat;
    document.querySelectorAll("#liveCats .exchip").forEach(x => x.classList.toggle("on", x === c));
    renderLiveDramas();
  };
});

/* ---------- Live Speed Dynamic Adjustment ---------- */
async function setLiveDownloadSpeed(val){
  const num = Math.max(1, Math.min(16, Number(val) || 8));
  const sqC = $("#sqConc"); if(sqC) sqC.value = String(num);
  const c = $("#conc"); if(c) c.value = String(num);
  localStorage.setItem("hg-speed", String(num));
  try {
    const res = await fetch("/dl/speed", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({concurrency: num})
    });
    const j = await res.json();
    if(j && j.ok){
      toast(`⚡ បានកំណត់ Speed ទៅ ${num}x រួចរាល់! (Download នឹងប្តូរភ្លាមៗ)`);
    }
  } catch(e){}
}

const sqConcEl = $("#sqConc");
if(sqConcEl) sqConcEl.addEventListener('change', e => setLiveDownloadSpeed(e.target.value));
const concEl = $("#conc");
if(concEl) concEl.addEventListener('change', e => setLiveDownloadSpeed(e.target.value));

const savedSpeed = localStorage.getItem("hg-speed");
if(savedSpeed){
  const sqC = $("#sqConc"); if(sqC) sqC.value = savedSpeed;
  const c = $("#conc"); if(c) c.value = savedSpeed;
  fetch("/dl/speed", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({concurrency: Number(savedSpeed)})}).catch(()=>{});
}

function switchBoardTab(board){
  const hero = document.querySelector(".hero");
  if(board === "livedata"){
    currentTab = "livedata";
    location.hash = "#livedata";
    if(hero) hero.hidden = false;
    document.querySelectorAll("#boardTabs .tab").forEach(t=>t.classList.toggle("on", t.dataset.board==="livedata"));
    loadLiveData();
  } else if(board === "human"){
    currentTab = "human";
    trendCategory = "human";
    trendPage = 1;
    trendOffsets = {1:0};
    location.hash = "#human";
    if(hero) hero.hidden = false;
    if($("#liveCats")) $("#liveCats").hidden = true;
    document.querySelectorAll("#boardTabs .tab").forEach(t=>t.classList.toggle("on", t.dataset.board==="human"));
    loadTrending(trendBoard, 1);
  } else if(board === "ai"){
    currentTab = "ai";
    trendCategory = "ai";
    trendPage = 1;
    trendOffsets = {1:0};
    location.hash = "#ai";
    if(hero) hero.hidden = false;
    if($("#liveCats")) $("#liveCats").hidden = true;
    document.querySelectorAll("#boardTabs .tab").forEach(t=>t.classList.toggle("on", t.dataset.board==="ai"));
    loadTrending(trendBoard, 1);
  } else if(board === "explorer"){
    currentTab = "explorer";
    location.hash = "#catalog";
    if(hero) hero.hidden = true;
    if($("#liveCats")) $("#liveCats").hidden = true;
    document.querySelectorAll("#boardTabs .tab").forEach(t=>t.classList.toggle("on", t.dataset.board==="explorer"));
    loadExplorer(expPage || 1);
  } else {
    currentTab = "trend";
    if(trendCategory === "human" || trendCategory === "ai") trendCategory = "all";
    if(location.hash === "#catalog" || location.hash === "#explorer" || location.hash === "#livedata" || location.hash === "#human" || location.hash === "#ai"){
      history.replaceState(null, "", location.pathname);
    }
    if(hero) hero.hidden = false;
    if($("#liveCats")) $("#liveCats").hidden = true;
    document.querySelectorAll("#boardTabs .tab").forEach(t=>t.classList.toggle("on", t.dataset.board==="trend"));
    loadTrending(trendBoard, trendPage);
  }
}
const dss = $("#dateSortSelect");
if(dss){
  dss.addEventListener("change", e => onDateSortChange(e.target.value));
}
document.querySelectorAll("#boardTabs .tab").forEach(t=>t.onclick=()=>{ switchBoardTab(t.dataset.board); });
document.querySelectorAll("#trendCats .exchip").forEach(c=>c.onclick=()=>{        // leaderboard category switch
  if(c.dataset.cat===trendCategory) return;
  trendCategory=c.dataset.cat; trendPage=1; trendOffsets={1:0};
  loadTrending().then(()=>{ if(trendExpanded) trendTop(); });
});
$("#backHome").onclick=()=>{ $("#omni").value=""; $("#omniMode").textContent="ស្វែងរក"; $("#omniMode").classList.remove("link"); switchBoardTab("trend"); };  // return from search results to the Trending home
const expP = $("#expPrev"); if(expP) expP.onclick=()=>{ if(expPage>1) loadExplorer(expPage-1); };
const expN = $("#expNext"); if(expN) expN.onclick=()=>{ if(expPage<expPages) loadExplorer(expPage+1); };
function expGoto(){ const ep = $("#expPage"); let n=ep?parseInt(ep.value,10):1; if(!n||n<1)n=1; if(n>expPages)n=expPages; loadExplorer(n); }
const expG = $("#expGo"); if(expG) expG.onclick=expGoto;
const epInput = $("#expPage"); if(epInput) epInput.addEventListener("keydown",e=>{ if(e.key==="Enter"){ e.preventDefault(); expGoto(); } });
/* Rows selector removed — Catalog is a fixed 100 cards/page. */
let exQTimer=null;
const exQInput = $("#exQ");
const exQClear = $("#exQClear");
function updateExQClearBtn(){
  if(exQClear){
    exQClear.style.display = (exQInput && exQInput.value) ? "flex" : "none";
  }
}
if(exQInput){
  exQInput.addEventListener("input", e=>{
    exQ = e.target.value.trim();
    updateExQClearBtn();
    clearTimeout(exQTimer);
    exQTimer = setTimeout(()=>loadExplorer(1), 300);
  });
  exQInput.addEventListener("keydown", e=>{
    if(e.key==="Enter"){
      e.preventDefault();
      clearTimeout(exQTimer);
      loadExplorer(1);
    }
  });
}
if(exQClear){
  exQClear.onclick = ()=>{
    exQ = "";
    if(exQInput) exQInput.value = "";
    updateExQClearBtn();
    loadExplorer(1);
  };
}
$("#exSort").addEventListener("change",e=>{ exSort=e.target.value; loadExplorer(1); });
$("#exStatus").addEventListener("change",e=>{ exStatus=e.target.value; loadExplorer(1); });
window.addEventListener("resize",()=>{ clearTimeout(window._trTimer); window._trTimer=setTimeout(()=>{ if(currentTab==='trend' && !trendExpanded && trendData.length && !DEMO && $("#resLabel").textContent==="🏆 Leaderboard") renderTrending(); },200); });

/* ============ DEMO MODE (self-contained; used when /dl backend is unreachable, e.g. shared preview) ============ */
const SAMPLE=[
  {series_id:"d1",title:"错嫁豪门：夫人马甲藏不住",episode_cnt:98,score:"8.6"},
  {series_id:"d2",title:"重生之最强千金归来",episode_cnt:76,score:"8.4"},
  {series_id:"d3",title:"龙王殿：都市至尊归来",episode_cnt:120,score:"8.9"},
  {series_id:"d4",title:"闪婚老公竟是隐形首富",episode_cnt:64,score:"8.2"},
  {series_id:"d5",title:"天降萌宝：总裁爹地宠上天",episode_cnt:110,score:"8.7"},
  {series_id:"d6",title:"我在古代当神医",episode_cnt:88,score:"8.5"},
  {series_id:"d7",title:"顾少的隐婚新娘",episode_cnt:70,score:"8.3"},
  {series_id:"d8",title:"离婚后前妻惊艳全球",episode_cnt:82,score:"8.1"},
];
let demoState={running:false, series:[], log:["[demo] preview mode — backend not connected"]};
let demoTimer=null;
function demoSearch(q){ const s=(q||"").toLowerCase();
  return {results: SAMPLE.filter(x=> !s || x.title.toLowerCase().includes(s) || true).slice(0,8)}; }
function demoResolve(text){ const pick=SAMPLE[Math.floor(Math.random()*SAMPLE.length)];
  return {resolved:[{series_id:pick.series_id,title:pick.title,total:pick.episode_cnt}]}; }
function demoStatus(){ return demoState; }
function demoStart(p){
  demoState.running=true;
  demoState.series=(p.series_ids||[]).map((id,i)=>{ const c=cart[id]||{};
    const tot=(c.sel&&c.sel.length)?c.sel.length:(c.total||60);
    return {sid:id,title:c.title||id,total:tot,done:i===0?Math.round(tot*0.34):0,status:i===0?"downloading":"queued"}; });
  demoState.log=["[demo] queued "+demoState.series.length+" dramas","[demo] downloading @ "+p.quality+" ×"+p.concurrency];
  if(demoTimer) clearInterval(demoTimer);
  demoTimer=setInterval(demoTick,650);
  return {ok:true};
}
function demoCancel(){ demoState.running=false; if(demoTimer) clearInterval(demoTimer);
  demoState.log.push("[demo] stopped"); }
function demoTick(){
  let active=demoState.series.find(s=>s.status==="downloading");
  if(!active){ const nx=demoState.series.find(s=>s.status==="queued"); if(nx){ nx.status="downloading"; active=nx; } }
  if(!active){ demoState.running=false; clearInterval(demoTimer); demoState.log.push("[demo] all done ✓"); poll(); return; }
  active.done=Math.min(active.total, active.done + Math.max(1,Math.round(active.total/28)));
  if(active.done>=active.total){ active.status="done"; demoState.log.push("[demo] ✓ "+active.title+" ("+active.total+" eps)"); }
  poll();
}
function seedDemo(){
  document.documentElement.setAttribute("data-demo","1");
  $("#dockEps").textContent="preview mode";
  /* no folder input in the new UI (folder is set via the native picker) */
  if(!Object.keys(cart).length){
    addToCart("d3","龙王殿：都市至尊归来",120); addToCart("d1","错嫁豪门：夫人马甲藏不住",98); addToCart("d6","我在古代当神医",88);
  }
  demoState.series=[
    {sid:"d3",title:"龙王殿：都市至尊归来",total:120,done:41,status:"downloading"},
    {sid:"d1",title:"错嫁豪门：夫人马甲藏不住",total:98,done:0,status:"queued"},
    {sid:"d6",title:"我在古代当神医",total:88,done:88,status:"done"},
  ];
  demoState.running=true;
  if(demoTimer) clearInterval(demoTimer); demoTimer=setInterval(demoTick,700);
  doSearch("");
  renderQueue();
  toast("Preview mode — sample data (backend not connected)");
}

/* ---------- license (key activation) ---------- */
function licReason(r){
  return ({
    not_found:"That key doesn't exist — check for typos.",
    revoked:"This key has been turned off. Contact the owner.",
    expired:"This key has expired.",
    bound_other:"This key is already active on another PC. Release it there first, or ask the owner to reset it.",
    network:"Couldn't reach the server. Check your internet connection.",
    not_configured:"Licensing isn't set up yet.",
    empty:"Enter your key.",
    no_key:"No key on this PC yet.",
    offline_no_grace:"You've been offline too long — connect to the internet to continue."
  })[r] || ("Couldn't activate ("+(r||"unknown")+").");
}
function fmtDate(iso){ try{ return new Date(iso).toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'}); }catch(e){ return iso; } }
async function licStatus(){ try{ return await (await fetch('/dl/license/status')).json(); }catch(e){ return null; } }
async function licUsage(){ try{ return await (await fetch('/dl/license/usage')).json(); }catch(e){ return null; } }
let LICENSED=false;

function renderAccount(u){
  const btn=$("#acctBtn");
  if(!btn){ LICENSED=true; return; }
  
  // USER REQUIREMENT:
  // ចំពោះមុខងារ License User ធម្មតា ឬ VIP មិនអនុញ្ញាតអោយឃើញឡើយ (Only Admin can see it)
  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  if(!isAdmin){
    btn.hidden = true;
    btn.style.display = 'none';
    LICENSED = true;
    return;
  }

  if(!u || u.configured===false){ btn.hidden=true; btn.style.display='none'; LICENSED=true; return; }  // dev/unconfigured -> unlimited, no chip
  btn.hidden=false;
  btn.style.display='inline-flex';
  LICENSED = !!u.licensed;
  $("#acctDevice").textContent = u.device_label || 'this PC';
  if(u.licensed){
    btn.textContent='Licensed';
    $("#acctSub").textContent='Licensed';
    $("#acctPlan").textContent='Licensed — unlimited';
    $("#rowUsed").hidden=true;
    $("#rowKey").hidden=false; $("#acctKey").textContent=u.key_masked||'—';
    $("#activateBox").hidden=true; $("#licensedBox").hidden=false; $("#acctDeact").hidden=false;
  } else {
    const used=(u.free_used==null?'?':u.free_used), lim=(u.free_limit==null?'?':u.free_limit);
    btn.textContent='Free '+used+'/'+lim;
    $("#acctSub").textContent='Free plan';
    $("#acctPlan").textContent='Free — '+lim+' series / day';
    $("#rowUsed").hidden=false; $("#acctUsed").textContent=used+' of '+lim+' used today';
    $("#rowKey").hidden=true;
    $("#activateBox").hidden=false; $("#licensedBox").hidden=true; $("#acctDeact").hidden=true;
  }
  $("#plansBox").hidden = !!u.licensed;
  const rExp=$("#rowExpiry"); if(u.expires_at){ rExp.hidden=false; $("#acctExpiry").textContent=fmtDate(u.expires_at); } else { rExp.hidden=true; }
  const rDev=$("#rowDevices"), md=u.max_devices, du=(u.devices_used!=null?u.devices_used:u.device_count);
  if(u.licensed && md){ rDev.hidden=false; $("#acctDevices").textContent=(du!=null?(du+" of "+md):(md+" max")); } else { rDev.hidden=true; }
  if(u.licensed && u.plan){ $("#acctPlan").textContent=u.plan; }
}
async function refreshAccount(){ const u=await licUsage(); renderAccount(u); return u; }
function openAccount(){
  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  if(!isAdmin) return;
  $("#licMsg").textContent=''; $("#licMsg").className='lic-msg'; $("#acctMsg").textContent=''; $("#acctMsg").className='lic-msg'; $("#acctModal").hidden=false;
}
function closeAccount(){ $("#acctModal").hidden=true; }
function promptActivate(){
  const isAdmin = !!(window.userAccess && (window.userAccess.is_admin || window.userAccess.role === 'admin'));
  if(!isAdmin){
    openUserRegisterModal('vip');
    return;
  }
  toast("Daily free limit reached (2/day) — activate for unlimited, or try again tomorrow", true);
  refreshAccount().then(()=>{ openAccount(); setTimeout(()=>$("#licKey").focus(),200); });
}

async function activateKey(){
  const key=$("#licKey").value.trim(), msg=$("#licMsg"); msg.className='lic-msg';
  if(!key){ msg.textContent='Enter your key.'; return; }
  const btn=$("#licGo"); btn.disabled=true; btn.textContent='Activating…';
  let r; try{ r=await (await fetch('/dl/license/activate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key})})).json(); }
  catch(e){ r={ok:false,reason:'network'}; }
  btn.disabled=false; btn.textContent='Activate';
  if(r.ok || r.active){ msg.className='lic-msg ok'; msg.textContent='Activated — unlimited unlocked!'; $("#licKey").value=''; await refreshAccount(); }
  else { msg.textContent=licReason(r.reason); }
}
async function deactivateLicense(){
  if(!confirm('Release this PC? You can then activate the same key on another PC — but only once every 7 days.')) return;
  const msg=$("#acctMsg"); msg.className='lic-msg'; const btn=$("#acctDeact"); btn.disabled=true;
  let r; try{ r=await (await fetch('/dl/license/deactivate',{method:'POST'})).json(); }
  catch(e){ r={ok:false,reason:'network'}; }
  btn.disabled=false;
  if(r.ok){ toast("Released — you can now activate on another PC"); await refreshAccount(); }
  else if(r.reason==='cooldown'){ msg.textContent='You can move to another PC on '+fmtDate(r.next_move_allowed_at)+'.'; }
  else { msg.textContent=licReason(r.reason); }
}
$("#licGo").onclick=activateKey;
$("#licKey").addEventListener('keydown',e=>{ if(e.key==='Enter') activateKey(); });
const acctB=$("#acctBtn"); if(acctB) acctB.onclick=()=>{ openAccount(); };
$("#acctClose").onclick=$("#acctCloseB").onclick=closeAccount;
$("#acctDeact").onclick=deactivateLicense;
$("#acctModal").addEventListener('click',e=>{ if(e.target===$("#acctModal")) closeAccount(); });

/* ---------- plans, purchase links, update check ---------- */
// Purchases go through the Telegram sales bot; each tier deep-links to its own ?start=.
const LINKS = { telegram:"https://t.me/HongguoDownloaderBot" };
function buyUrl(start){ return LINKS.telegram + (start?("?start="+start):""); }
const PLANS = [
  { name:"1 year",   dev:"1 device",  stars:"1,500", usd:"25.99", start:"year" },
  { name:"Lifetime", dev:"1 device",  stars:"2,500", usd:"42.99", start:"life", tag:"Best value" },
  { name:"Lifetime", dev:"3 devices", stars:"5,000", usd:"85.99", start:"life3" },
];
function renderPlans(){
  $("#planList").innerHTML = PLANS.map(p=>`
    <div class="plan${p.tag?" best":""}" data-start="${p.start}">
      <div>
        <div class="pn">${p.name}${p.tag?` <span class="tag">${p.tag}</span>`:""}</div>
        <div class="pd">Unlimited · ${p.dev}</div>
      </div>
      <div class="pp"><div class="stars">★ ${p.stars}</div><div class="usd">or $${p.usd}</div></div>
    </div>`).join("");
}
function openExt(u){ if(!u) return; try{ window.open(u,"_blank","noopener"); }catch(e){ location.href=u; } }
let UPDATE_INFO=null;
const _UPD_DISMISS="hg_upd_dismiss";
function _updDismissed(v){ try{ return !!v && localStorage.getItem(_UPD_DISMISS)===v; }catch(e){ return false; } }
function _setUpdDismissed(v){ try{ v?localStorage.setItem(_UPD_DISMISS,v):localStorage.removeItem(_UPD_DISMISS); }catch(e){} }

// Reflect the latest check into the UI: Account version + dot always tell the truth;
// the top banner is dismissable per-version so it never nags after being closed.
function renderUpdate(){
  const r=UPDATE_INFO;
  if(r&&r.current) $("#acctVersion").textContent = "v"+r.current;
  const has = !!(r&&r.update&&r.url);
  const aBtn=$("#acctBtn"); if(aBtn) aBtn.classList.toggle("hasupd", has);
  $("#updRow").hidden = !has;
  if(has){
    $("#ubText").innerHTML = `<b>Update available</b> — ${esc(r.latest||"")}`;
    $("#ubGet").onclick = ()=>openUpdate();
  }
  $("#updBanner").hidden = !(has && !_updDismissed(r.latest));
  if(has) $("#updBannerSub").textContent =
    ` — version ${r.latest} is ready` + (r.current?` (you have v${r.current})`:"");
}

// Background checker: polls the GitHub-backed /dl/update-check (cached ~30 min server-side).
async function checkUpdate(){
  let r; try{ r=await (await fetch("/dl/update-check")).json(); }catch(e){ return; }
  if(!r) return;
  UPDATE_INFO=r;
  renderUpdate();
}

function openUpdate(){
  const r=UPDATE_INFO; if(!r||!r.update||!r.url) return;
  $("#updFrom").textContent = "v"+(r.current||"—");
  $("#updTo").textContent   = "v"+(r.latest||"—");
  $("#updName").textContent = (r.name && r.name!==r.latest) ? r.name : "";
  $("#updNotes").textContent = r.notes || "No release notes were provided.";
  const st=$("#updStatus"); st.hidden=true; st.className="upd-status"; st.textContent="";
  const dl=$("#updDownload"); dl.disabled=false; dl.textContent="Download & verify"; dl.onclick=downloadAndVerify;
  const pg=$("#updPage");
  if(r.page){ pg.hidden=false; pg.onclick=()=>openExt(r.page); } else { pg.hidden=true; }
  $("#updModal").hidden=false;
}
function closeUpdate(){ $("#updModal").hidden=true; }

function _shortPub(s){ const m=/CN=([^,]+)/i.exec(s||""); return (m?m[1]:(s||"")).trim().slice(0,48); }
async function downloadAndVerify(){
  // C7: the app downloads the installer and checks its Authenticode signature so a compromised
  // GitHub release can't hand you a malicious .exe. Graceful while the build isn't code-signed yet.
  const r=UPDATE_INFO; if(!r) return;
  const st=$("#updStatus"), dl=$("#updDownload");
  st.hidden=false; st.className="upd-status"; st.textContent="Downloading and verifying the installer…";
  dl.disabled=true;
  let v=null; try{ v=await (await fetch("/dl/update-download",{method:"POST"})).json(); }catch(e){}
  dl.disabled=false;
  if(!v||!v.ok){
    st.className="upd-status warn"; st.textContent="Couldn't download automatically — get it from the website.";
    dl.textContent="Download in browser"; dl.onclick=()=>openExt(r.url); return;
  }
  const pub=_shortPub(v.publisher);
  if(v.signed && !v.valid){
    st.className="upd-status bad"; st.textContent="⚠ The installer's signature is INVALID. Don't run it — get it from the website.";
    dl.textContent="Open website"; dl.onclick=()=>openExt(r.page||r.url); return;
  }
  if(v.expected_publisher && v.valid && !v.trusted){
    st.className="upd-status bad"; st.textContent="⚠ Signed by an UNEXPECTED publisher ("+(pub||"?")+"). Don't run it — get it from the website.";
    dl.textContent="Open website"; dl.onclick=()=>openExt(r.page||r.url); return;
  }
  if(v.trusted){
    st.className="upd-status ok"; st.textContent="✓ Verified"+(pub?" — signed by "+esc(pub):"")+". Safe to run.";
  } else {
    st.className="upd-status warn"; st.textContent="Downloaded from GitHub over HTTPS (not code-signed yet). SHA-256 "+(v.sha256||"").slice(0,16)+"…";
  }
  dl.textContent="Run installer"; dl.onclick=()=>runInstaller(v.path);
}
async function runInstaller(path){
  try{ const j=await (await fetch("/dl/update-run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({path})})).json();
       toast(j&&j.ok?"Starting the installer…":"Couldn't launch the installer", !(j&&j.ok)); }
  catch(e){ toast("Couldn't launch the installer", true); }
}

$("#updWhats").onclick=()=>openUpdate();
/* License-section buttons: Check update / Website / Support */
$("#acctCheckUpd").onclick=async ()=>{
  const b=$("#acctCheckUpd"), old=b.textContent; b.disabled=true; b.textContent="Checking…";
  await checkUpdate();
  b.disabled=false; b.textContent=old;
  const r=UPDATE_INFO;
  if(r && r.update && r.url){ openUpdate(); }
  else { toast("You’re on the latest version"+((r&&r.current)?" (v"+r.current+")":"")); }
};
$("#acctWebsite").onclick=()=>openExt("https://hongguodownloader.com/");
$("#acctSupport").onclick=()=>openExt("https://t.me/M4st3r0");
/* Bug report: save a redacted logs/screenshot zip, open its folder + the support chat to attach */
$("#brSend").onclick=async ()=>{
  const b=$("#brSend"), old=b.innerHTML, m=$("#brMsg");
  const logs=$("#brLogs").checked, shot=$("#brShot").checked;
  if(!logs && !shot){ m.textContent="Pick app logs and/or a screenshot first."; return; }
  b.disabled=true; b.textContent="Preparing…"; m.textContent="";
  let r=null; try{ r=await (await fetch("/dl/bugreport",{method:"POST",headers:{"Content-Type":"application/json"},
                    body:JSON.stringify({logs,screenshot:shot})})).json(); }catch(e){}
  b.disabled=false; b.innerHTML=old;
  if(r&&r.ok){ m.textContent="Report saved — the folder opened with it selected. Drag it into the Telegram chat.";
               openExt("https://t.me/M4st3r0"); }
  else { m.textContent="Couldn't create the report"+((r&&r.error)?(": "+r.error):"")+"."; toast("Bug report failed", true); }
};
$("#updNow").onclick=()=>{ const r=UPDATE_INFO; if(r&&r.url) openExt(r.url); };
$("#updDismiss").onclick=()=>{ const r=UPDATE_INFO; if(r) _setUpdDismissed(r.latest); $("#updBanner").hidden=true; };
$("#updModalClose").onclick=$("#updLater").onclick=closeUpdate;
$("#updModal").addEventListener('click',e=>{ if(e.target===$("#updModal")) closeUpdate(); });
$("#buyTg").onclick=()=>openExt(buyUrl());
$("#planList").onclick=(e)=>{ const p=e.target.closest(".plan"); openExt(buyUrl(p&&p.dataset.start)); };
renderPlans();

/* ---------- total posters stat loader & live data auto-sync ---------- */
async function loadTotalPosterStats(){
  try{
    await fetchLiveStatsOnly();
  }catch(e){
    try{
      const j = await (await fetch(EXPLORER_API + "/explorer?page=1&size=1", {cache:"no-store"})).json();
      if(j && j.count){
        const formatted = Number(j.count).toLocaleString();
        const el1 = $("#heroTotalPosters");
        if(el1) el1.textContent = `${formatted} រឿង (Posters)`;
        const el2 = $("#topPosterCountBadge");
        if(el2) el2.textContent = `🎬 ${formatted} Posters`;
      }
    }catch(err){}
  }
}

/* ---------- boot ---------- */
let _appStarted=false;
function startApp(){
  loadUB(); loadDir(); poll(); loadHistory();
  const hash = location.hash;
  if(hash === "#human") switchBoardTab("human");
  else if(hash === "#ai") switchBoardTab("ai");
  else if(hash === "#livedata") switchBoardTab("livedata");
  else if(hash === "#trend") switchBoardTab("trend");
  else switchBoardTab("explorer");
  loadLibrary(); loadTotalPosterStats();
  fetchAccessStatus();
  // Live poll access status from Firebase Realtime Database every 5 seconds
  setInterval(fetchAccessStatus, 5000);
  // Auto-sync live posters from https://hongguoduanju.com/ every 5 minutes in background
  setInterval(fetchLiveStatsOnly, 5 * 60 * 1000);
  // adaptive poll: ~1s while a job runs (smooth live poster reveal), relaxed to 2s when idle
  (function tick(){ const ms=(lastStatus && lastStatus.running)?900:2000;
    setTimeout(()=>{ if(!DEMO) poll(); tick(); }, ms); })();
  if(!(DEMO||ALLOW_DEMO)) refreshAccount();     // populate the Account chip (free vs licensed)
  if(!(DEMO||ALLOW_DEMO)){                        // background update checker (banner + modal)
    checkUpdate();                               // on launch
    setInterval(checkUpdate, 3*60*60*1000);      // and every 3h for long-running sessions
    document.addEventListener('visibilitychange',()=>{ if(!document.hidden) checkUpdate(); });
  }
}
const tokenParam = new URLSearchParams(location.search).get("token");
if(tokenParam){
  localStorage.setItem('syd_auth_token', tokenParam);
}
renderQueue();
startApp();
if(new URLSearchParams(location.search).has("open_queue")){
  setTimeout(() => { if(typeof openSideQueue === 'function') openSideQueue(); }, 350);
}
const authParam = new URLSearchParams(location.search).get("auth");
if(authParam){
  setTimeout(() => { if(typeof openUserRegisterModal === 'function') openUserRegisterModal(authParam); }, 350);
}
const scrollModalParam = new URLSearchParams(location.search).get("scroll_modal");
if(scrollModalParam){
  setTimeout(() => {
    const el = document.querySelector('.modal-scroll');
    if(el) el.scrollTop = parseInt(scrollModalParam, 10);
  }, 700);
}
if(new URLSearchParams(location.search).has("user_control")){
  if(typeof openUserControl === 'function') openUserControl();
}



const dramaParam = new URLSearchParams(location.search).get("drama");
if(dramaParam){
  setTimeout(() => { if(typeof openDramaDetail === 'function') openDramaDetail(dramaParam); }, 450);
}
if(new URLSearchParams(location.search).has("open_first_drama")){
  const checkCard = setInterval(() => {
    const c = document.querySelector(".poster, .result-card");
    if(c){
      clearInterval(checkCard);
      c.click();
    }
  }, 100);
}




