import os

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"

html_code = r'''<!doctype html>
<html lang="km" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SYD 8MOVIE PRO - កម្មវិធីដោនឡូតរឿង & Poster កម្រិតខ្ពស់</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Battambang:wght@400;700;900&family=Kantumruy+Pro:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.8/dist/hls.min.js"></script>

  <style>
    :root{
      --ground:#15100d; --ground-2:#100c09;
      --surface:#211812; --surface-2:#2a1f17; --surface-3:#352518;
      --ink:#f7efe7; --ink-2:#d3c3b4; --muted:#9c8a7b; --faint:#6f6155;
      --line:#352a20; --line-2:rgba(65,51,37,0.45);
      --accent:#ff6a2b; --accent-2:#ffb14a; --on-accent:#1c0e06;
      --spectrum:linear-gradient(100deg,#ff512b,#ff7a2a 18%,#ffb62f 38%,#ffdc3a 54%,#9be04e 70%,#3fe097 85%,#1fe0e0);
      --teal:#24ddcf; --teal-2:#22d6e6; --on-teal:#08201c;
      --glow:rgba(255,106,43,0.28); --glow-teal:rgba(31,214,228,0.22);
      --good:#43d98a; --gold:#e0ad45; --bad:#ff5d78;
      --ring:rgba(255,106,43,0.55);
      --shadow:0 26px 60px -24px rgba(0,0,0,0.7), 0 6px 18px -10px rgba(0,0,0,0.5);
      --shadow-sm:0 10px 24px -14px rgba(0,0,0,0.6);
      --font-km:"Kantumruy Pro","Battambang",system-ui,-apple-system,sans-serif;
    }
    :root[data-theme="light"]{
      --ground:#faf6f2; --ground-2:#f2ebe4;
      --surface:#ffffff; --surface-2:#f5eee7; --surface-3:#ece2d8;
      --ink:#241a13; --ink-2:#5c4d42; --muted:#998a7c; --faint:#b6a89b;
      --line:#ece1d7; --line-2:#e2d5c8;
      --accent:#f0521a; --accent-2:#ff9a2e; --on-accent:#fff;
      --glow:rgba(240,82,26,0.18);
      --shadow:0 18px 44px -18px rgba(94,45,20,0.30);
      --shadow-sm:0 6px 18px -10px rgba(94,45,20,0.25);
    }
    *{ box-sizing:border-box; margin:0; padding:0; }
    body{
      background:var(--ground); color:var(--ink);
      font-family:var(--font-km); font-size:15px; line-height:1.55;
      min-height:100vh; overflow-x:hidden; padding-bottom:90px;
    }
    .aura{ position:fixed; inset:0; z-index:-1; pointer-events:none; overflow:hidden; }
    .aura b{ position:absolute; border-radius:50%; filter:blur(80px); opacity:.85; }
    .aura b:nth-child(1){ width:50vw; height:50vw; top:-15vw; right:-10vw; background:radial-gradient(circle,var(--glow),transparent 70%); }
    .aura b:nth-child(2){ width:45vw; height:45vw; bottom:-15vw; left:-10vw; background:radial-gradient(circle,var(--glow-teal),transparent 70%); }

    .shell{ max-width:1440px; margin:0 auto; padding:20px 28px; }

    /* Topbar */
    .topbar{ display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; }
    .brand{ display:flex; align-items:center; gap:16px; cursor:pointer; }
    .mark{ width:54px; height:54px; border-radius:50%; object-fit:contain; filter:drop-shadow(0 4px 14px rgba(255,106,43,0.5)); transition:transform .2s; }
    .mark:hover{ transform:scale(1.06); }
    .brand-title{ font-size:22px; font-weight:800; letter-spacing:-.02em; }
    .logo-gradient{
      background:linear-gradient(115deg,#ff381e 0%,#ff6a17 38%,#ff8f1c 68%,#ffb82e 100%);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    }
    .brand-sub{ font-size:12px; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.06em; margin-top:2px; }

    .top-actions{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
    .btn{
      border:none; outline:none; cursor:pointer; font-family:var(--font-km); font-weight:700; font-size:13.5px;
      padding:9px 18px; border-radius:9999px; display:inline-flex; align-items:center; gap:8px;
      background:var(--surface-2); color:var(--ink); transition:all .18s ease; box-shadow:var(--shadow-sm);
    }
    .btn:hover{ filter:brightness(1.08); transform:translateY(-1px); }
    .btn:active{ transform:translateY(1px); }
    .btn.primary{
      background:linear-gradient(115deg,var(--accent),var(--accent-2)); color:var(--on-accent);
      box-shadow:0 8px 20px -6px var(--glow);
    }
    .btn.ghost{ background:var(--surface); border:1px solid var(--line); }
    .btn.ghost:hover{ border-color:var(--ring); color:var(--accent); }
    .badge{
      padding:5px 12px; border-radius:9999px; font-size:12px; font-weight:700;
      background:var(--surface-2); border:1px solid var(--line); color:var(--muted);
      display:inline-flex; align-items:center; gap:6px;
    }
    .badge.live{ color:var(--good); border-color:rgba(67,217,138,0.3); background:rgba(67,217,138,0.1); }
    .badge.live::before{ content:''; width:7px; height:7px; border-radius:50%; background:var(--good); box-shadow:0 0 8px var(--good); }

    /* Hero & Command Bar */
    .hero{ margin:30px 0 16px; }
    .hero-lead{ font-size:clamp(26px,3.2vw,42px); font-weight:800; line-height:1.15; }
    .hero-tag{ color:var(--muted); font-size:15px; margin-top:8px; }

    .omni{
      margin-top:20px; display:flex; gap:10px; align-items:center;
      background:var(--surface); border:1px solid var(--line); border-radius:9999px;
      padding:7px 8px 7px 18px; box-shadow:var(--shadow); transition:all .2s;
    }
    .omni:focus-within{ border-color:var(--ring); box-shadow:var(--shadow), 0 0 0 4px var(--glow); }
    .omni-mode{ font-size:12px; font-weight:700; color:var(--accent); background:var(--surface-2); padding:6px 14px; border-radius:9999px; }
    .omni input{
      flex:1; border:0; outline:0; background:transparent; color:var(--ink);
      font-family:var(--font-km); font-size:16px; padding:6px;
    }
    .omni input::placeholder{ color:var(--faint); }

    /* Category Chips */
    .chips-row{
      display:flex; gap:8px; overflow-x:auto; padding:16px 0 10px;
      scrollbar-width:none; -ms-overflow-style:none;
    }
    .chips-row::-webkit-scrollbar{ display:none; }
    .chip{
      flex:none; padding:8px 18px; border-radius:9999px; border:1px solid var(--line);
      background:var(--surface); color:var(--ink-2); font-size:13.5px; font-weight:700;
      cursor:pointer; transition:all .18s; display:inline-flex; align-items:center; gap:6px;
    }
    .chip:hover{ border-color:var(--ring); color:var(--accent); transform:translateY(-1px); }
    .chip.active{
      background:linear-gradient(115deg,var(--accent),var(--accent-2)); color:var(--on-accent);
      border-color:transparent; box-shadow:0 6px 16px -4px var(--glow);
    }

    /* Filter Bar */
    .filter-bar{
      display:flex; justify-content:space-between; align-items:center;
      margin:18px 0 22px; padding-bottom:12px; border-bottom:1px solid var(--line-2);
    }
    .section-title{ font-size:18px; font-weight:800; display:flex; align-items:center; gap:10px; }

    /* Drama Cards Grid */
    .grid{
      display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:22px;
    }
    .card{
      background:var(--surface); border:1px solid var(--line); border-radius:18px;
      overflow:hidden; display:flex; flex-direction:column; box-shadow:var(--shadow-sm);
      transition:transform .22s ease, border-color .22s ease, box-shadow .22s ease;
      position:relative;
    }
    .card:hover{
      transform:translateY(-5px); border-color:var(--ring);
      box-shadow:var(--shadow), 0 0 22px -6px var(--glow);
    }
    .card-poster-box{
      position:relative; width:100%; aspect-ratio:2/3; overflow:hidden; background:var(--surface-2);
    }
    .card-poster{
      width:100%; height:100%; object-fit:cover; transition:transform .35s ease;
    }
    .card:hover .card-poster{ transform:scale(1.06); }
    
    .card-badge-rating{
      position:absolute; top:10px; left:10px;
      background:rgba(21,16,13,0.85); backdrop-filter:blur(8px);
      padding:4px 9px; border-radius:9999px; font-size:12px; font-weight:800;
      color:var(--gold); border:1px solid rgba(224,173,69,0.3);
    }
    .card-badge-eps{
      position:absolute; top:10px; right:10px;
      background:rgba(21,16,13,0.85); backdrop-filter:blur(8px);
      padding:4px 9px; border-radius:9999px; font-size:12px; font-weight:700;
      color:var(--ink); border:1px solid var(--line);
    }
    .card-content{
      padding:14px; display:flex; flex-direction:column; flex:1; justify-content:space-between; gap:10px;
    }
    .card-title-zh{
      font-size:14px; font-weight:700; color:var(--ink); line-height:1.35;
      display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; overflow:hidden;
    }
    .card-title-km{
      font-size:13px; font-weight:600; color:var(--accent-2); line-height:1.35;
      display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height:36px;
    }
    .card-actions{ display:flex; gap:6px; margin-top:4px; }
    .card-btn{
      flex:1; border:none; outline:none; cursor:pointer; font-family:var(--font-km);
      font-size:12px; font-weight:700; padding:7px 8px; border-radius:10px;
      background:var(--surface-2); color:var(--ink-2); transition:all .15s;
      display:flex; align-items:center; justify-content:center; gap:4px;
    }
    .card-btn:hover{ background:var(--surface-3); color:var(--accent); }
    .card-btn.primary{
      background:linear-gradient(115deg,var(--accent),var(--accent-2)); color:var(--on-accent);
    }
    .card-btn.poster-btn{
      background:rgba(36,221,207,0.12); color:var(--teal); border:1px solid rgba(36,221,207,0.25);
    }
    .card-btn.poster-btn:hover{ background:var(--teal); color:var(--on-teal); }

    /* Modal / Drawer */
    .modal-overlay{
      position:fixed; inset:0; background:rgba(0,0,0,0.78); backdrop-filter:blur(10px);
      z-index:999; display:none; align-items:center; justify-content:center; padding:20px;
    }
    .modal-overlay.open{ display:flex; }
    .modal-card{
      background:var(--surface); border:1px solid var(--line); border-radius:24px;
      width:100%; max-width:960px; max-height:90vh; overflow-y:auto;
      box-shadow:var(--shadow); position:relative; padding:28px;
    }
    .modal-close{
      position:absolute; top:20px; right:20px; width:36px; height:36px; border-radius:50%;
      background:var(--surface-2); border:1px solid var(--line); color:var(--ink);
      display:grid; place-items:center; cursor:pointer; font-weight:800; transition:all .15s;
    }
    .modal-close:hover{ color:var(--bad); border-color:var(--bad); }

    .modal-grid{ display:grid; grid-template-columns:260px 1fr; gap:26px; }
    @media (max-width:768px){ .modal-grid{ grid-template-columns:1fr; } }
    .modal-poster-wrap img{ width:100%; border-radius:16px; aspect-ratio:2/3; object-fit:cover; }
    
    .player-box{
      width:100%; aspect-ratio:16/9; background:#000; border-radius:16px;
      overflow:hidden; margin-bottom:18px; border:1px solid var(--line);
    }
    .player-box video{ width:100%; height:100%; }

    .eps-grid{
      display:grid; grid-template-columns:repeat(auto-fill,minmax(64px,1fr)); gap:8px;
      max-height:220px; overflow-y:auto; margin:14px 0; padding-right:6px;
    }
    .ep-item{
      padding:8px 4px; border-radius:10px; border:1px solid var(--line);
      background:var(--surface-2); color:var(--ink); font-size:12px; font-weight:700;
      text-align:center; cursor:pointer; transition:all .15s;
    }
    .ep-item:hover{ border-color:var(--accent); color:var(--accent); }
    .ep-item.active{ background:var(--accent); color:var(--on-accent); border-color:transparent; }
    .ep-item.selected{ border-color:var(--gold); background:rgba(224,173,69,0.18); }

    /* Drawer for Downloads */
    .drawer{
      position:fixed; bottom:0; right:24px; width:440px; max-width:calc(100vw - 48px);
      background:var(--surface); border:1px solid var(--line); border-bottom:none;
      border-radius:20px 20px 0 0; box-shadow:var(--shadow); z-index:900;
      transform:translateY(calc(100% - 54px)); transition:transform .3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .drawer.open{ transform:translateY(0); }
    .drawer-header{
      padding:14px 20px; display:flex; justify-content:space-between; align-items:center;
      cursor:pointer; background:var(--surface-2); border-radius:20px 20px 0 0;
    }
    .drawer-body{ max-height:420px; overflow-y:auto; padding:16px 20px; }
    .dl-item{
      background:var(--surface-2); border:1px solid var(--line); border-radius:12px;
      padding:12px; margin-bottom:10px;
    }
    .dl-progress-bar{
      height:6px; border-radius:9999px; background:var(--line); overflow:hidden; margin:8px 0;
    }
    .dl-progress-fill{
      height:100%; border-radius:9999px; background:linear-gradient(90deg,var(--accent),var(--teal));
      width:0%; transition:width .25s ease;
    }

    /* Toast */
    .toast-box{
      position:fixed; bottom:24px; left:24px; z-index:9999; display:flex; flex-direction:column; gap:8px;
    }
    .toast{
      background:var(--surface-2); border:1px solid var(--ring); border-radius:12px;
      padding:12px 20px; box-shadow:var(--shadow); font-weight:700; font-size:14px;
      display:flex; align-items:center; gap:10px; animation:slideUp .2s ease;
    }
    @keyframes slideUp{ from{ opacity:0; transform:translateY(12px); } to{ opacity:1; transform:translateY(0); } }
  </style>
</head>
<body>
  <div class="aura"><b></b><b></b></div>

  <div class="shell">
    <!-- Topbar -->
    <header class="topbar">
      <div class="brand" onclick="loadCatalog('1')">
        <img src="/logo.png" class="mark" alt="SYD 8Movie" onerror="this.style.display='none'">
        <div>
          <div class="brand-title"><span class="logo-gradient">SYD 8MOVIE PRO</span></div>
          <div class="brand-sub">កម្មវិធីដោនឡូតរឿង & POSTER 8MOVIE កម្រិតខ្ពស់</div>
        </div>
      </div>

      <div class="top-actions">
        <span class="badge live">8Movie Live</span>
        <button class="btn ghost" onclick="openDownloadFolder()">📂 បើក Folder</button>
        <button class="btn ghost" onclick="toggleLibraryModal()">📚 បណ្ណាល័យ</button>
        <button class="btn ghost" onclick="toggleSettingsModal()">⚙️ កំណត់</button>
        <button class="btn primary" onclick="toggleDrawer()">
          ⬇ ការទាញយក (<span id="dlBadge">0</span>)
        </button>
      </div>
    </header>

    <!-- Hero / Search -->
    <section class="hero">
      <h1 class="hero-lead">ទាញយក Poster និងវីដេអូរឿងភាគ <em>8Movie</em> កម្រិត Full HD</h1>
      <p class="hero-tag">ស្វែងរករឿងភាគចិន 8movie.com រាប់ពាន់រឿង បកប្រែចំណងជើងជាភាសាខ្មែរស្វ័យប្រវត្ត</p>

      <div class="omni">
        <span class="omni-mode">8MOVIE</span>
        <input type="text" id="searchInput" placeholder="ស្វែងរកចំណងជើងរឿងភាគ 8movie (វាយឈ្មោះ ឬពាក្យគន្លឹះ រួចចុច Enter)..." onkeydown="if(event.key==='Enter') doSearch()">
        <button class="btn primary" onclick="doSearch()">🔍 ស្វែងរក</button>
      </div>

      <!-- Categories Chips -->
      <div class="chips-row" id="categoriesRow">
        <!-- populated by JS -->
      </div>
    </section>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="section-title">
        <span id="currentFeedTitle">🎬 រឿងភាគឆ្លងភពបុរាណ</span>
        <span class="badge" id="resultsCount">0 រឿង</span>
      </div>
      <div>
        <button class="btn ghost" onclick="refreshCurrentFeed()">🔄 Refresh</button>
      </div>
    </div>

    <!-- Cards Grid -->
    <main class="grid" id="dramasGrid">
      <!-- Cards rendered by JS -->
    </main>
  </div>

  <!-- Episode & Video Player Modal -->
  <div class="modal-overlay" id="dramaModal">
    <div class="modal-card">
      <button class="modal-close" onclick="closeDramaModal()">✕</button>
      <div class="modal-grid">
        <div class="modal-poster-wrap">
          <img id="modalPoster" src="" alt="Poster">
          <div style="margin-top:14px; display:flex; flex-direction:column; gap:8px;">
            <button class="btn primary" style="width:100%;" onclick="downloadCurrentPoster()">
              🖼 ទាញយក Poster HD
            </button>
            <button class="btn ghost" style="width:100%;" onclick="downloadAllEpisodes()">
              ⬇ ទាញយកគ្រប់ភាគទាំងអស់
            </button>
          </div>
        </div>

        <div>
          <h2 id="modalTitleZh" style="font-size:22px; font-weight:800; color:var(--ink);"></h2>
          <h3 id="modalTitleKm" style="font-size:16px; font-weight:600; color:var(--accent-2); margin-top:4px;"></h3>

          <div style="display:flex; gap:8px; margin:12px 0;">
            <span class="badge" id="modalRating">★ 8.8</span>
            <span class="badge" id="modalEpsCount">0 ភាគ</span>
            <span class="badge" id="modalTags">8Movie</span>
          </div>

          <p id="modalDesc" style="color:var(--muted); font-size:13.5px; margin-bottom:14px; line-height:1.5;"></p>

          <!-- Embedded Player -->
          <div class="player-box">
            <video id="previewPlayer" controls></video>
          </div>

          <!-- Episode Selector -->
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
            <span style="font-weight:700; font-size:14px;">បញ្ជីភាគ (ចុចដើម្បីចាក់ ឬទាញយក)</span>
            <div style="display:flex; gap:8px;">
              <button class="btn ghost" style="padding:4px 10px; font-size:12px;" onclick="selectAllEpisodes()">ជ្រើសទាំងអស់</button>
              <button class="btn ghost" style="padding:4px 10px; font-size:12px;" onclick="deselectAllEpisodes()">ដោះការជ្រើស</button>
              <button class="btn primary" style="padding:4px 12px; font-size:12px;" onclick="downloadSelectedEpisodes()">⬇ ទាញភាគដែលបានជ្រើស</button>
            </div>
          </div>

          <div class="eps-grid" id="episodesGrid">
            <!-- populated by JS -->
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Downloads Drawer -->
  <div class="drawer" id="downloadDrawer">
    <div class="drawer-header" onclick="toggleDrawer()">
      <div style="font-weight:800; font-size:15px;">
        ⬇ ការទាញយក (<span id="drawerCount">0</span> កំពុងដំណើរការ)
      </div>
      <div>
        <button class="btn ghost" style="padding:4px 10px; font-size:11px;" onclick="event.stopPropagation(); clearDownloads()">🧹 សម្អាត</button>
      </div>
    </div>
    <div class="drawer-body" id="drawerList">
      <div style="text-align:center; color:var(--muted); padding:20px;">មិនទាន់មានការទាញយកនៅឡើយទេ</div>
    </div>
  </div>

  <!-- Library Modal -->
  <div class="modal-overlay" id="libraryModal">
    <div class="modal-card" style="max-width:760px;">
      <button class="modal-close" onclick="toggleLibraryModal()">✕</button>
      <h2 style="font-size:20px; font-weight:800; margin-bottom:16px;">📚 បណ្ណាល័យរឿងដែលបានទាញយករួច</h2>
      <div id="libraryList" style="display:flex; flex-direction:column; gap:12px; max-height:60vh; overflow-y:auto;">
        <div style="text-align:center; color:var(--muted); padding:30px;">កំពុងស្កេន...</div>
      </div>
    </div>
  </div>

  <!-- Settings Modal -->
  <div class="modal-overlay" id="settingsModal">
    <div class="modal-card" style="max-width:540px;">
      <button class="modal-close" onclick="toggleSettingsModal()">✕</button>
      <h2 style="font-size:20px; font-weight:800; margin-bottom:16px;">⚙️ ការកំណត់កម្មវិធី (Settings)</h2>
      
      <div style="margin-bottom:16px;">
        <label style="display:block; font-size:13px; font-weight:700; margin-bottom:6px;">ទីតាំងរក្សាទុកវីដេអូ & Poster (Download Directory):</label>
        <div style="display:flex; gap:8px;">
          <input type="text" id="settingOutDir" style="flex:1; padding:8px 12px; border-radius:10px; border:1px solid var(--line); background:var(--surface-2); color:var(--ink);" readonly>
          <button class="btn ghost" onclick="openDownloadFolder()">បើកមើល</button>
        </div>
      </div>

      <div style="margin-bottom:16px;">
        <label style="display:block; font-size:13px; font-weight:700; margin-bottom:6px;">ចំនួនទាញយកដំណាលគ្នា (Concurrent Downloads):</label>
        <select id="settingThreads" style="width:100%; padding:8px 12px; border-radius:10px; border:1px solid var(--line); background:var(--surface-2); color:var(--ink);" onchange="updateSettings()">
          <option value="1">1 កិច្ចការ (Worker)</option>
          <option value="2">2 កិច្ចការ</option>
          <option value="3" selected>3 កិច្ចការ (ណែនាំ)</option>
          <option value="5">5 កិច្ចការ (ល្បឿនលឿន)</option>
        </select>
      </div>

      <div style="margin-bottom:16px; display:flex; align-items:center; justify-content:space-between;">
        <span style="font-size:13px; font-weight:700;">បកប្រែចំណងជើងជាភាសាខ្មែរស្វ័យប្រវត្ត:</span>
        <input type="checkbox" id="settingAutoTrans" checked onchange="updateSettings()">
      </div>

      <button class="btn primary" style="width:100%;" onclick="toggleSettingsModal()">រួចរាល់</button>
    </div>
  </div>

  <div class="toast-box" id="toastBox"></div>

  <script>
    let currentCat = '1';
    let currentDrama = null;
    let selectedEpisodes = new Set();
    let hlsInstance = null;

    const CATEGORIES = [
      { id: '1', name_km: '👑 ឆ្លងភពបុរាណ', name_zh: '穿越古代' },
      { id: '4', name_km: '❤️ ស្នេហាទីក្រុង', name_zh: '都市情愛' },
      { id: '5', name_km: '⚡ សងសឹកបោកផ្ទុះ', name_zh: '復仇爽劇' },
      { id: '2', name_km: '⚔️ ក្បាច់គុនអភិនីហារ', name_zh: '玄幻武俠' },
      { id: '3', name_km: '🔮 អាថ៌កំបាំងវេទមន្ត', name_zh: '奇幻懸疑' },
      { id: '6', name_km: '🎭 រឿងភាគផ្សេងៗ', name_zh: '其他短劇' },
      { id: 'update', name_km: '🔥 រឿងថ្មីៗ', name_zh: '最新更新' },
      { id: 'rank', name_km: '🏆 ចំណាត់ថ្នាក់', name_zh: '熱門排行' }
    ];

    function toast(msg, type='info'){
      const box = document.getElementById('toastBox');
      const t = document.createElement('div');
      t.className = 'toast';
      t.innerHTML = `<span>${type === 'success' ? '✅' : '🔔'}</span> <span>${msg}</span>`;
      box.appendChild(t);
      setTimeout(() => t.remove(), 4000);
    }

    function renderCategories(){
      const row = document.getElementById('categoriesRow');
      row.innerHTML = CATEGORIES.map(c => `
        <button class="chip ${c.id === currentCat ? 'active' : ''}" onclick="loadCatalog('${c.id}', '${c.name_km}')">
          ${c.name_km}
        </button>
      `).join('');
    }

    async function loadCatalog(catId, catName){
      currentCat = catId;
      renderCategories();
      const titleEl = document.getElementById('currentFeedTitle');
      titleEl.innerText = catName || '🎬 រឿងភាគ 8Movie';
      const grid = document.getElementById('dramasGrid');
      grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:60px; color:var(--muted);">កំពុងទាញទិន្នន័យពីរឿងភាគ 8movie.com...</div>';

      try {
        const res = await fetch(`/api/catalog?cat=${catId}`);
        const data = await res.json();
        renderCards(data.items || []);
      } catch(e){
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:60px; color:var(--bad);">មានបញ្ហាក្នុងការទាញយកទិន្នន័យ: ${e.message}</div>`;
      }
    }

    async function doSearch(){
      const q = document.getElementById('searchInput').value.trim();
      if(!q) return loadCatalog(currentCat);
      document.getElementById('currentFeedTitle').innerText = `🔍 លទ្ធផលស្វែងរក: "${q}"`;
      const grid = document.getElementById('dramasGrid');
      grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:60px; color:var(--muted);">កំពុងស្វែងរក...</div>';

      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        renderCards(data.items || []);
      } catch(e){
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:var(--bad);">ស្វែងរកមិនបានជោគជ័យ: ${e.message}</div>`;
      }
    }

    function renderCards(items){
      const grid = document.getElementById('dramasGrid');
      document.getElementById('resultsCount').innerText = `${items.length} រឿង`;

      if(!items.length){
        grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:60px; color:var(--muted);">មិនមានរឿងភាគណាមួយត្រូវបានរកឃើញឡើយ</div>';
        return;
      }

      grid.innerHTML = items.map(item => `
        <div class="card">
          <div class="card-poster-box">
            <img class="card-poster" src="${item.poster}" alt="${item.title}" loading="lazy" onerror="this.src='/logo.png'">
            <span class="card-badge-rating">★ ${item.rating || '8.8'}</span>
            <span class="card-badge-eps">${item.episodes_count ? item.episodes_count + ' ភាគ' : 'រឿងពេញ'}</span>
          </div>
          <div class="card-content">
            <div>
              <div class="card-title-zh" title="${item.title}">${item.title}</div>
              <div class="card-title-km" title="${item.title_km || item.title}">${item.title_km || item.title}</div>
            </div>
            <div class="card-actions">
              <button class="card-btn primary" onclick="openDrama('${item.id}')">≡ មើលភាគ</button>
              <button class="card-btn poster-btn" title="ទាញយក Poster HD" onclick="downloadPosterDirect('${item.id}', '${escapeAttr(item.title)}', '${escapeAttr(item.title_km)}', '${item.poster}')">🖼 Poster</button>
              <button class="card-btn" title="ទាញយកគ្រប់ភាគ" onclick="quickDownloadAll('${item.id}', '${escapeAttr(item.title)}', '${escapeAttr(item.title_km)}')">⬇</button>
            </div>
          </div>
        </div>
      `).join('');
    }

    function escapeAttr(str){
      return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    }

    async function openDrama(id){
      toast('កំពុងទាញយកព័ត៌មានលម្អិត និងបញ្ជីភាគ...');
      try {
        const res = await fetch(`/api/episodes?id=${id}`);
        const data = await res.json();
        currentDrama = data;
        selectedEpisodes.clear();

        document.getElementById('modalPoster').src = data.poster;
        document.getElementById('modalTitleZh').innerText = data.title;
        document.getElementById('modalTitleKm').innerText = data.title_km || data.title;
        document.getElementById('modalRating').innerText = `★ ${data.rating || '8.8'}`;
        document.getElementById('modalEpsCount').innerText = `${data.episodes_count || data.episodes.length} ភាគ`;
        document.getElementById('modalTags').innerText = (data.tags && data.tags.length) ? data.tags.join(' / ') : '8Movie';
        document.getElementById('modalDesc').innerText = data.description || 'មិនមានការពិពណ៌នាសង្ខេបឡើយ។';

        renderEpisodeButtons();

        // Autoplay first episode in preview player
        if(data.episodes && data.episodes.length > 0){
          playEpisode(data.episodes[0]);
        }

        document.getElementById('dramaModal').classList.add('open');
      } catch(e){
        toast('មិនអាចបើកព័ត៌មានរឿងបានទេ: ' + e.message, 'bad');
      }
    }

    function renderEpisodeButtons(){
      const epsGrid = document.getElementById('episodesGrid');
      if(!currentDrama.episodes || !currentDrama.episodes.length){
        epsGrid.innerHTML = '<div style="color:var(--muted); font-size:13px;">មិនទាន់មានភាគសម្រាប់ចាក់នៅឡើយទេ</div>';
        return;
      }
      epsGrid.innerHTML = currentDrama.episodes.map(ep => {
        const isSel = selectedEpisodes.has(ep.episode);
        return `
          <button class="ep-item ${isSel ? 'selected' : ''}" onclick="toggleSelectEp(${ep.episode})" oncontextmenu="event.preventDefault(); playEpisodeByNum(${ep.episode})">
            Ep ${ep.episode}
          </button>
        `;
      }).join('');
    }

    function toggleSelectEp(num){
      if(selectedEpisodes.has(num)) selectedEpisodes.delete(num);
      else selectedEpisodes.add(num);
      renderEpisodeButtons();
    }

    function selectAllEpisodes(){
      if(!currentDrama || !currentDrama.episodes) return;
      currentDrama.episodes.forEach(e => selectedEpisodes.add(e.episode));
      renderEpisodeButtons();
    }

    function deselectAllEpisodes(){
      selectedEpisodes.clear();
      renderEpisodeButtons();
    }

    function playEpisodeByNum(num){
      const ep = currentDrama.episodes.find(e => e.episode === num);
      if(ep) playEpisode(ep);
    }

    function playEpisode(ep){
      const video = document.getElementById('previewPlayer');
      const url = ep.hls_url;
      if(!url) return;

      if(Hls.isSupported()){
        if(hlsInstance) hlsInstance.destroy();
        hlsInstance = new Hls({
          xhrSetup: function(xhr, u){
            // Referer is set by server/proxy when needed, or direct
          }
        });
        hlsInstance.loadSource(url);
        hlsInstance.attachMedia(video);
        hlsInstance.on(Hls.Events.MANIFEST_PARSED, function(){
          video.play().catch(() => {});
        });
      } else if(video.canPlayType('application/vnd.apple.mpegurl')){
        video.src = url;
        video.play().catch(() => {});
      }
      toast(`កំពុងចាក់: ភាគ ${ep.episode}`);
    }

    function closeDramaModal(){
      document.getElementById('dramaModal').classList.remove('open');
      const video = document.getElementById('previewPlayer');
      video.pause();
      if(hlsInstance){ hlsInstance.destroy(); hlsInstance = null; }
    }

    async function downloadCurrentPoster(){
      if(!currentDrama || !currentDrama.poster) return;
      await downloadPosterDirect(currentDrama.id, currentDrama.title, currentDrama.title_km, currentDrama.poster);
    }

    async function downloadPosterDirect(id, title, title_km, posterUrl){
      toast('កំពុងចាប់ផ្តើមទាញយក Poster HD...');
      try {
        const res = await fetch('/api/download/poster', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            drama_id: id,
            drama_title: title,
            title_km: title_km,
            poster_url: posterUrl
          })
        });
        const d = await res.json();
        toast('បានបន្ថែម Poster ទៅក្នុងបញ្ជីទាញយក!', 'success');
        toggleDrawer(true);
      } catch(e){
        toast('ការទាញយក Poster បរាជ័យ: ' + e.message, 'bad');
      }
    }

    async function quickDownloadAll(id, title, title_km){
      toast('កំពុងរៀបចំទាញយកគ្រប់ភាគទាំងអស់...');
      try {
        const res = await fetch(`/api/episodes?id=${id}`);
        const data = await res.json();
        if(data.episodes && data.episodes.length){
          await fetch('/api/download/batch', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              drama_id: id,
              drama_title: title,
              title_km: title_km,
              episodes: data.episodes,
              poster_url: data.poster
            })
          });
          toast(`បានបន្ថែម ${data.episodes.length} ភាគទៅកាន់ Queue!`, 'success');
          toggleDrawer(true);
        }
      } catch(e){
        toast('បរាជ័យក្នុងការទាញយក: ' + e.message, 'bad');
      }
    }

    async function downloadAllEpisodes(){
      if(!currentDrama || !currentDrama.episodes) return;
      try {
        await fetch('/api/download/batch', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            drama_id: currentDrama.id,
            drama_title: currentDrama.title,
            title_km: currentDrama.title_km,
            episodes: currentDrama.episodes,
            poster_url: currentDrama.poster
          })
        });
        toast(`បានបន្ថែម ${currentDrama.episodes.length} ភាគទៅកាន់ Queue!`, 'success');
        toggleDrawer(true);
      } catch(e){
        toast('បរាជ័យ: ' + e.message, 'bad');
      }
    }

    async function downloadSelectedEpisodes(){
      if(!currentDrama || !selectedEpisodes.size){
        return toast('សូមជ្រើសរើសភាគដែលចង់ទាញយកជាមុនសិន!');
      }
      const toDl = currentDrama.episodes.filter(e => selectedEpisodes.has(e.episode));
      try {
        await fetch('/api/download/batch', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            drama_id: currentDrama.id,
            drama_title: currentDrama.title,
            title_km: currentDrama.title_km,
            episodes: toDl,
            poster_url: currentDrama.poster
          })
        });
        toast(`បានបន្ថែម ${toDl.length} ភាគទៅកាន់ Queue!`, 'success');
        toggleDrawer(true);
      } catch(e){
        toast('បរាជ័យ: ' + e.message, 'bad');
      }
    }

    function toggleDrawer(forceOpen=false){
      const dr = document.getElementById('downloadDrawer');
      if(forceOpen) dr.classList.add('open');
      else dr.classList.toggle('open');
    }

    async function pollDownloads(){
      try {
        const res = await fetch('/api/download/status');
        const data = await res.json();
        const activeCount = data.active_count || 0;
        const queuedCount = data.queued_count || 0;
        const totalPending = activeCount + queuedCount;

        document.getElementById('dlBadge').innerText = totalPending;
        document.getElementById('drawerCount').innerText = totalPending;

        const listEl = document.getElementById('drawerList');
        if(!data.tasks || !data.tasks.length){
          listEl.innerHTML = '<div style="text-align:center; color:var(--muted); padding:20px;">មិនទាន់មានការទាញយកនៅឡើយទេ</div>';
          return;
        }

        listEl.innerHTML = data.tasks.slice(0, 30).map(t => `
          <div class="dl-item">
            <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:700;">
              <span>${t.drama_title} ${t.task_type === 'poster' ? '🖼 Poster' : '· ភាគ ' + t.ep_num}</span>
              <span style="color:${t.status === 'completed' ? 'var(--good)' : t.status === 'downloading' ? 'var(--accent)' : 'var(--muted)'};">
                ${t.status === 'completed' ? 'រួចរាល់' : t.status === 'downloading' ? t.speed : t.status}
              </span>
            </div>
            <div class="dl-progress-bar">
              <div class="dl-progress-fill" style="width:${t.progress}%;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--muted);">
              <span>${t.size_mb ? t.size_mb + ' MB' : ''}</span>
              ${t.status === 'downloading' ? `<button class="btn ghost" style="padding:2px 8px; font-size:10px;" onclick="cancelTask('${t.task_id}')">បោះបង់</button>` : ''}
            </div>
          </div>
        `).join('');
      } catch(e){}
    }

    async function cancelTask(tid){
      await fetch('/api/download/cancel', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ task_id: tid })
      });
      pollDownloads();
    }

    async function clearDownloads(){
      await fetch('/api/download/clear', { method: 'POST' });
      pollDownloads();
      toast('បានសម្អាតបញ្ជីដែលបានរួចរាល់!');
    }

    async function openDownloadFolder(){
      await fetch('/api/open', { method: 'POST' });
      toast('បានបើក Folder ក្នុង Windows Explorer!');
    }

    async function toggleLibraryModal(){
      const m = document.getElementById('libraryModal');
      m.classList.toggle('open');
      if(m.classList.contains('open')){
        const listEl = document.getElementById('libraryList');
        listEl.innerHTML = '<div style="text-align:center; color:var(--muted); padding:30px;">កំពុងស្កេនបណ្ណាល័យ...</div>';
        try {
          const res = await fetch('/api/library');
          const data = await res.json();
          if(!data.dramas || !data.dramas.length){
            listEl.innerHTML = '<div style="text-align:center; color:var(--muted); padding:30px;">មិនទាន់មានរឿងដែលបានទាញយករួចនៅឡើយទេ</div>';
            return;
          }
          listEl.innerHTML = data.dramas.map(d => `
            <div style="background:var(--surface-2); border:1px solid var(--line); border-radius:14px; padding:14px; display:flex; justify-content:space-between; align-items:center;">
              <div>
                <div style="font-weight:800; font-size:15px;">${d.folder_name}</div>
                <div style="font-size:12px; color:var(--muted); margin-top:4px;">${d.episodes_count} ភាគបានទាញយក</div>
              </div>
              <button class="btn ghost" onclick="openFolderDirect('${d.folder_path.replace(/\\/g, '\\\\')}')">📂 បើក Folder</button>
            </div>
          `).join('');
        } catch(e){
          listEl.innerHTML = '<div style="color:var(--bad);">មិនអាចស្កេនបានទេ</div>';
        }
      }
    }

    async function openFolderDirect(p){
      await fetch('/api/open', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ path: p })
      });
    }

    async function toggleSettingsModal(){
      const m = document.getElementById('settingsModal');
      m.classList.toggle('open');
      if(m.classList.contains('open')){
        const res = await fetch('/api/config');
        const c = await res.json();
        document.getElementById('settingOutDir').value = c.output_dir || '';
        document.getElementById('settingThreads').value = c.max_concurrent_downloads || 3;
        document.getElementById('settingAutoTrans').checked = c.auto_translate !== false;
      }
    }

    async function updateSettings(){
      const threads = parseInt(document.getElementById('settingThreads').value);
      const autoTrans = document.getElementById('settingAutoTrans').checked;
      await fetch('/api/config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          max_concurrent_downloads: threads,
          auto_translate: autoTrans
        })
      });
      toast('បានរក្សាទុកការកំណត់!', 'success');
    }

    function refreshCurrentFeed(){
      loadCatalog(currentCat);
    }

    // Startup
    window.addEventListener('DOMContentLoaded', () => {
      renderCategories();
      loadCatalog('1');
      setInterval(pollDownloads, 2000);
    });
  </script>
</body>
</html>
'''

with open(os.path.join(TARGET_DIR, 'app', 'web', 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html_code)

print("Written: app/web/index.html")
