import sys

def patch():
    path = 'app/web/downloader.html'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update CSS for pagination
    old_css = """  /* ============ Circular Centered Pagination (ស្ទាយរង្វង់មូលចំកណ្តាល ដូចរូបថត) ============ */
  .circle-pager{
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    gap:8px !important;
    width:100% !important;
    margin:22px auto 14px !important;
    padding:6px 0 !important;
    flex-wrap:wrap !important;
    user-select:none;
  }
  .circle-page-btn{
    width:38px;
    height:38px;
    border-radius:50%;
    border:none;
    background:#52525b;
    color:#ffffff;
    font-size:14px;
    font-weight:700;
    font-family:var(--font-mono), -apple-system, sans-serif;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    cursor:pointer;
    transition:all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow:0 2px 6px rgba(0, 0, 0, 0.3);
    outline:none;
  }
  .circle-page-btn:hover:not(:disabled):not(.active){
    background:#71717a;
    transform:scale(1.08);
    color:#ffffff;
  }
  .circle-page-btn.active{
    background:#38bdf8 !important;
    color:#090d16 !important;
    font-weight:800 !important;
    box-shadow:0 0 16px rgba(56, 189, 248, 0.6) !important;
    transform:scale(1.05);
  }
  .circle-page-btn:disabled{
    opacity:0.32;
    cursor:not-allowed;
    background:#3f3f46;
    pointer-events:none;
  }
  .circle-page-btn.nav-btn{
    font-size:16px;
    font-weight:800;
  }
  .circle-page-dots{
    width:38px;
    height:38px;
    border-radius:50%;
    background:#52525b;
    color:#ffffff;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    font-size:14px;
    font-weight:800;
    letter-spacing:1px;
    cursor:pointer;
    transition:all 0.18s ease;
    box-shadow:0 2px 6px rgba(0, 0, 0, 0.3);
  }
  .circle-page-dots:hover{
    background:#71717a;
    transform:scale(1.08);
    color:#38bdf8;
  }"""

    new_css = """  /* ============ Circular Centered & Top-Right Pagination (ស្ទាយរង្វង់មូល ដូចរូបថត) ============ */
  .circle-pager{
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
    gap:7px !important;
    width:100% !important;
    margin:22px auto 14px !important;
    padding:6px 0 !important;
    flex-wrap:wrap !important;
    user-select:none;
  }
  /* Top pagination placed on the right (ផ្នែកខាងលើដាក់នៅខាងស្តាំ) */
  .circle-pager.top-pager{
    justify-content:flex-end !important;
    margin:6px 0 12px auto !important;
    width:auto !important;
    padding:2px 0 !important;
  }
  .circle-page-btn{
    width:36px;
    height:36px;
    min-width:36px;
    border-radius:50%;
    border:none;
    background:#474b57;
    color:#ffffff;
    font-size:13.5px;
    font-weight:700;
    font-family:var(--font-mono), -apple-system, sans-serif;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    cursor:pointer;
    transition:all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow:0 2px 6px rgba(0, 0, 0, 0.35);
    outline:none;
    padding:0;
    line-height:1;
  }
  .circle-page-btn:hover:not(:disabled):not(.active){
    background:#646979;
    transform:scale(1.08);
    color:#ffffff;
  }
  .circle-page-btn.active{
    background:#38bdf8 !important;
    color:#090d16 !important;
    font-weight:800 !important;
    box-shadow:0 0 18px rgba(56, 189, 248, 0.75) !important;
    transform:scale(1.08);
  }
  .circle-page-btn:disabled{
    opacity:0.3;
    cursor:not-allowed;
    background:#2b2d35;
    pointer-events:none;
  }
  .circle-page-btn.nav-btn{
    font-size:16px;
    font-weight:800;
    background:#343741;
  }
  .circle-page-btn.nav-btn:hover:not(:disabled){
    background:#525665;
  }
  .circle-page-dots{
    width:36px;
    height:36px;
    min-width:36px;
    border-radius:50%;
    background:#474b57;
    color:#ffffff;
    display:inline-flex;
    align-items:center;
    justify-content:center;
    font-size:14px;
    font-weight:800;
    letter-spacing:1px;
    cursor:pointer;
    transition:all 0.18s ease;
    box-shadow:0 2px 6px rgba(0, 0, 0, 0.35);
    user-select:none;
    line-height:1;
  }
  .circle-page-dots:hover{
    background:#646979;
    transform:scale(1.08);
    color:#38bdf8;
  }
  @media (max-width: 768px){
    .circle-pager{
      gap:5px !important;
      overflow-x:auto;
      -webkit-overflow-scrolling:touch;
      flex-wrap:nowrap !important;
      justify-content:flex-start !important;
      padding-bottom:6px !important;
    }
    .circle-pager.top-pager{
      justify-content:flex-start !important;
      margin-left:0 !important;
      width:100% !important;
    }
    .circle-page-btn, .circle-page-dots{
      width:32px;
      height:32px;
      min-width:32px;
      font-size:12px;
    }
  }"""

    if old_css not in content:
        print("ERROR: old_css not found!")
        return False
    content = content.replace(old_css, new_css, 1)

    # 2. Add Top Pagination Row in HTML above #results
    old_grid = '    <div class="grid" id="results"></div>'
    new_grid = """    <!-- Top Pagination Row (Aligned to the Right ផ្នែកខាងលើដាក់នៅខាងស្តាំ) -->
    <div class="top-pager-bar" id="topPagerBar" style="display:flex;justify-content:flex-end;align-items:center;width:100%;margin:2px 0 10px">
      <div id="moreRowTop" class="circle-pager top-pager" hidden></div>
      <div id="explorerPagerTop" class="circle-pager top-pager" hidden></div>
    </div>
    <div class="grid" id="results"></div>"""

    if old_grid not in content:
        print("ERROR: old_grid not found!")
        return False
    content = content.replace(old_grid, new_grid, 1)

    # 3. Update renderCircularPagination and renderTrendControls
    old_render = """/* ============ Circular Centered Pagination (ស្ទាយរង្វង់មូលចំកណ្តាល ដូចរូបថត) ============ */
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
}"""

    new_render = """/* ============ Circular Centered & Top-Right Pagination (ស្ទាយរង្វង់មូល ដូចរូបថត) ============ */
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
  // User request: Show 10 to 20 pages! (e.g. 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20)
  const maxVisible = 20;
  if(totalPages <= maxVisible){
    for(let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    if(curPage <= 12){
      // First 20 pages + '...' + totalPages
      const end = Math.min(20, totalPages - 1);
      for(let i = 1; i <= end; i++) pages.push(i);
      if(end < totalPages - 1) pages.push('...');
      pages.push(totalPages);
    } else if(curPage >= totalPages - 11){
      // 1 + '...' + last 20 pages
      pages.push(1);
      const start = Math.max(2, totalPages - 19);
      if(start > 2) pages.push('...');
      for(let i = start; i <= totalPages; i++) pages.push(i);
    } else {
      // 1 + '...' + ~15 pages centered around curPage + '...' + totalPages
      pages.push(1);
      const start = curPage - 7;
      const end = curPage + 7;
      if(start > 2) pages.push('...');
      for(let i = start; i <= end; i++) pages.push(i);
      if(end < totalPages - 1) pages.push('...');
      pages.push(totalPages);
    }
  }

  const isTop = container.classList.contains("top-pager") || (container.id && container.id.endsWith("Top"));
  let innerButtons = '';
  const prevDisabled = curPage <= 1 ? 'disabled' : '';
  innerButtons += `<button type="button" class="circle-page-btn nav-btn" data-page="${curPage - 1}" ${prevDisabled} title="Previous Page">‹</button>`;

  for(const p of pages){
    if(p === '...'){
      innerButtons += `<span class="circle-page-dots" title="Jump to page (ចុចដើម្បីរំលងទំព័រ)">…</span>`;
    } else {
      const isActive = p === curPage ? 'active' : '';
      innerButtons += `<button type="button" class="circle-page-btn ${isActive}" data-page="${p}">${p}</button>`;
    }
  }

  const nextDisabled = curPage >= totalPages ? 'disabled' : '';
  innerButtons += `<button type="button" class="circle-page-btn nav-btn" data-page="${curPage + 1}" ${nextDisabled} title="Next Page">›</button>`;

  if(container.classList.contains("circle-pager")){
    container.innerHTML = innerButtons;
  } else {
    container.innerHTML = `<div class="circle-pager ${isTop ? 'top-pager' : ''}">${innerButtons}</div>`;
  }

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
  const rowTop=$("#moreRowTop");
  const estTotalPages = trendHasMore ? Math.max(trendPage + 5, 20) : trendPage;
  if(row){
    row.hidden=false;
    row.classList.add("trendctl-sticky");
    renderCircularPagination(row, trendPage, estTotalPages, (pg) => goToTrendPage(pg));
  }
  if(rowTop){
    rowTop.hidden=false;
    renderCircularPagination(rowTop, trendPage, estTotalPages, (pg) => goToTrendPage(pg));
  }
}"""

    if old_render not in content:
        print("ERROR: old_render not found!")
        return False
    content = content.replace(old_render, new_render, 1)

    # 4. Synchronize top pagers in loadExplorer, doSearch, loadLiveData, etc.
    # Replace renderCircularPagination($("#explorerPager"), j.page, j.pages, (pg) => loadExplorer(pg));
    old_exp_call = 'renderCircularPagination($("#explorerPager"), j.page, j.pages, (pg) => loadExplorer(pg));'
    new_exp_call = """renderCircularPagination($("#explorerPager"), j.page, j.pages, (pg) => loadExplorer(pg));
    const epTop = $("#explorerPagerTop");
    if(epTop) renderCircularPagination(epTop, j.page, j.pages, (pg) => loadExplorer(pg));"""
    if old_exp_call not in content:
        print("ERROR: old_exp_call not found!")
        return False
    content = content.replace(old_exp_call, new_exp_call, 1)

    # Replace $("#explorerPager").hidden=true; in loadExplorer (when count == 0)
    old_exp_zero = 'if(!(j.count>0)){\n      $("#explorerPager").hidden=true; $("#resCount").textContent="· 0";'
    new_exp_zero = 'if(!(j.count>0)){\n      $("#explorerPager").hidden=true; if($("#explorerPagerTop")) $("#explorerPagerTop").hidden=true; $("#resCount").textContent="· 0";'
    if old_exp_zero in content:
        content = content.replace(old_exp_zero, new_exp_zero, 1)

    # Replace $("#explorerPager").hidden=true; in loadExplorer catch
    old_exp_err = '$("#explorerPager").hidden=true;\n    box.innerHTML=\'<div class="empty"'
    new_exp_err = '$("#explorerPager").hidden=true; if($("#explorerPagerTop")) $("#explorerPagerTop").hidden=true;\n    box.innerHTML=\'<div class="empty"'
    if old_exp_err in content:
        content = content.replace(old_exp_err, new_exp_err, 1)

    # Replace $("#explorerPager").hidden=true; in loadExplorer top
    old_exp_start = 'sec.hidden=false; if($("#dramaDetailSec")) $("#dramaDetailSec").hidden=true; $("#resLabel").textContent="🎬 Catalog"; $("#boardTabs").hidden=false; $("#backHome").hidden=true; $("#moreRow").hidden=true; $("#trendCats").hidden=true;'
    new_exp_start = 'sec.hidden=false; if($("#dramaDetailSec")) $("#dramaDetailSec").hidden=true; $("#resLabel").textContent="🎬 Catalog"; $("#boardTabs").hidden=false; $("#backHome").hidden=true; $("#moreRow").hidden=true; if($("#moreRowTop")) $("#moreRowTop").hidden=true; $("#trendCats").hidden=true;'
    if old_exp_start in content:
        content = content.replace(old_exp_start, new_exp_start, 1)

    # Replace in doSearch:
    old_dosearch = '$("#boardTabs").hidden=true; $("#backHome").hidden=false; $("#moreRow").hidden=true; $("#trendCats").hidden=true; $("#explorerPager").hidden=true; $("#explorerControls").hidden=true;'
    new_dosearch = '$("#boardTabs").hidden=true; $("#backHome").hidden=false; $("#moreRow").hidden=true; if($("#moreRowTop")) $("#moreRowTop").hidden=true; $("#trendCats").hidden=true; $("#explorerPager").hidden=true; if($("#explorerPagerTop")) $("#explorerPagerTop").hidden=true; $("#explorerControls").hidden=true;'
    if old_dosearch in content:
        content = content.replace(old_dosearch, new_dosearch, 1)

    # Replace in loadLiveData:
    old_livedata = '  $("#moreRow").hidden = true;\n  $("#explorerPager").hidden = true;'
    new_livedata = '  $("#moreRow").hidden = true; if($("#moreRowTop")) $("#moreRowTop").hidden = true;\n  $("#explorerPager").hidden = true; if($("#explorerPagerTop")) $("#explorerPagerTop").hidden = true;'
    if old_livedata in content:
        content = content.replace(old_livedata, new_livedata, 1)

    # Replace in switchBoardTab trend:
    old_switch_trend = '  $("#boardTabs").hidden=false; $("#backHome").hidden=true; $("#explorerPager").hidden=true; $("#explorerControls").hidden=true; $("#resCount").textContent="";'
    new_switch_trend = '  $("#boardTabs").hidden=false; $("#backHome").hidden=true; $("#explorerPager").hidden=true; if($("#explorerPagerTop")) $("#explorerPagerTop").hidden=true; $("#explorerControls").hidden=true; $("#resCount").textContent="";'
    if old_switch_trend in content:
        content = content.replace(old_switch_trend, new_switch_trend, 1)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("SUCCESS: downloader.html patched with dual (top-right & bottom) pagination showing 10-20 pages!")
    return True

if __name__ == '__main__':
    patch()
