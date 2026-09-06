import sys, re
sys.stdout.reconfigure(encoding='utf-8')

FILE = 'app/web/downloader.html'
with open(FILE, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add #topCoinBadge next to #topDaysLeftBadge
target_topbar = '''      <!-- Days Remaining Badge (Admin / VIP / User) -->
      <div id="topDaysLeftBadge" style="display:none;border-radius:20px;font-weight:800;font-size:11.5px;padding:4px 12px;align-items:center;gap:6px;cursor:pointer;box-shadow:var(--shadow-sm);transition:all .2s ease" onclick="openUserRegisterModal('info')" title="ចុចដើម្បីមើលព័ត៌មានលម្អិតគណនី">
        <span id="topDaysLeftIcon">⏳</span> <span id="topDaysLeftText">នៅសល់ 7 ថ្ងៃ</span>
      </div>'''

replacement_topbar = '''      <!-- Days Remaining Badge (Admin / VIP / User) -->
      <div id="topDaysLeftBadge" style="display:none;border-radius:20px;font-weight:800;font-size:11.5px;padding:4px 12px;align-items:center;gap:6px;cursor:pointer;box-shadow:var(--shadow-sm);transition:all .2s ease" onclick="openUserRegisterModal('info')" title="ចុចដើម្បីមើលព័ត៌មានលម្អិតគណនី">
        <span id="topDaysLeftIcon">⏳</span> <span id="topDaysLeftText">នៅសល់ 7 ថ្ងៃ</span>
      </div>
      <!-- User Coins Badge -->
      <div id="topCoinBadge" style="display:none;border-radius:20px;font-weight:800;font-size:12px;padding:4px 12px;align-items:center;gap:6px;cursor:pointer;box-shadow:0 0 10px rgba(234,179,8,0.25);background:rgba(234,179,8,0.12);border:1px solid rgba(234,179,8,0.5);color:#eab308;transition:all .2s ease" onclick="openCoinModal()" title="សមតុល្យ Coin របស់អ្នក (ចុចដើម្បីទិញ ឬមើលប្រវត្តិ)">
        <span>🪙</span> <span id="topCoinsVal">0</span> Coin (<span id="topCoinsRiel">0</span>៛)
        <span style="font-size:11px;background:#eab308;color:#000;padding:1px 6px;border-radius:10px;margin-left:4px;font-weight:900">+ ទិញ</span>
      </div>'''

if target_topbar in text and 'topCoinBadge' not in text:
    text = text.replace(target_topbar, replacement_topbar, 1)
    print("Added #topCoinBadge to topbar")
else:
    print("#topCoinBadge already in topbar or target not found")

# 2. Add #coinModal before #userCtrlModal
target_modal = '<!-- User Control / Management Modal (Admin Dashboard) -->'
coin_modal_html = '''<!-- User Coin Modal: Top-up / Buy Coins with 1 Coin = 500 Riel -->
<div class="modal" id="coinModal" hidden style="z-index:115;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px)">
  <div class="modal-card" style="max-width:620px;width:min(620px,95vw);max-height:90vh;padding:24px;background:var(--surface,#18110b);border:1.5px solid rgba(234,179,8,0.4);border-radius:20px;box-shadow:0 24px 70px rgba(0,0,0,0.9),0 0 25px rgba(234,179,8,0.15);display:flex;flex-direction:column;overflow:hidden">
    <div class="modal-head" style="padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid var(--line,#3a2c20);display:flex;justify-content:space-between;align-items:flex-start">
      <div>
        <div class="modal-title" style="font-size:18px;font-weight:800;color:var(--ink);display:flex;align-items:center;gap:8px">
          <span>🪙 កាបូប Coin (SYD COIN WALLET)</span>
        </div>
        <div class="modal-sub" style="color:#eab308;font-weight:600;margin-top:3px;font-size:12px">
          1 Coin = 500៛ | 1 រឿង = 2 Coins (1,000៛) | ដោះសោរគ្រប់ភាគទាំងអស់ជាអចិន្ត្រៃយ៍
        </div>
      </div>
      <button class="x" onclick="closeCoinModal()" title="Close">✕</button>
    </div>

    <div class="modal-scroll" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:16px;padding-right:4px">
      <!-- User Current Coin Balance Card -->
      <div style="background:linear-gradient(135deg,rgba(234,179,8,0.15),rgba(245,158,11,0.05));border:1px solid rgba(234,179,8,0.4);border-radius:14px;padding:16px;display:flex;align-items:center;justify-content:space-between;gap:12px">
        <div>
          <div style="font-size:11.5px;color:var(--muted);font-weight:700">សមតុល្យ COIN របស់អ្នក</div>
          <div style="display:flex;align-items:baseline;gap:8px;margin-top:4px">
            <span style="font-size:28px;font-weight:900;color:#eab308;font-family:var(--font-mono)" id="coinModalUserCoins">0</span>
            <span style="font-size:14px;font-weight:700;color:#eab308">Coins</span>
            <span style="font-size:13px;color:var(--muted)">≈ <span id="coinModalUserRiel">0</span> ៛</span>
          </div>
          <div style="font-size:11.5px;color:var(--ink-2);margin-top:2px" id="coinModalUserAccountName">គណនី: ...</div>
        </div>
        <div style="text-align:right">
          <a href="https://t.me/sydadmin168" target="_blank" class="btn ghost sm" style="font-size:11px;border-radius:20px;border-color:rgba(56,189,248,0.5);color:#38bdf8;padding:4px 10px;text-decoration:none;display:inline-flex;align-items:center;gap:4px">
            <span>✈️ Chat ជាមួយ Admin</span>
          </a>
        </div>
      </div>

      <!-- Quick Package Select -->
      <div>
        <div style="font-size:12.5px;font-weight:800;color:var(--ink);margin-bottom:8px">📦 ជ្រើសរើសកញ្ចប់ទិញ Coin:</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px">
          <div class="coin-pkg-card" onclick="selectCoinPackage(10, 5000)" style="cursor:pointer;padding:10px;background:var(--surface-2);border:1px solid var(--line);border-radius:10px;text-align:center;transition:all .2s ease">
            <div style="font-size:15px;font-weight:900;color:#eab308">10 Coins</div>
            <div style="font-size:12px;font-weight:700;color:var(--ink);margin-top:2px">5,000 ៛</div>
            <div style="font-size:10px;color:var(--muted);margin-top:2px">បាន 5 រឿង</div>
          </div>
          <div class="coin-pkg-card" onclick="selectCoinPackage(20, 10000)" style="cursor:pointer;padding:10px;background:rgba(234,179,8,0.08);border:1px solid rgba(234,179,8,0.4);border-radius:10px;text-align:center;transition:all .2s ease">
            <div style="font-size:15px;font-weight:900;color:#eab308">20 Coins</div>
            <div style="font-size:12px;font-weight:700;color:var(--ink);margin-top:2px">10,000 ៛</div>
            <div style="font-size:10px;color:#22c55e;font-weight:700;margin-top:2px">★ ពេញនិយម (10 រឿង)</div>
          </div>
          <div class="coin-pkg-card" onclick="selectCoinPackage(50, 25000)" style="cursor:pointer;padding:10px;background:var(--surface-2);border:1px solid var(--line);border-radius:10px;text-align:center;transition:all .2s ease">
            <div style="font-size:15px;font-weight:900;color:#eab308">50 Coins</div>
            <div style="font-size:12px;font-weight:700;color:var(--ink);margin-top:2px">25,000 ៛</div>
            <div style="font-size:10px;color:var(--muted);margin-top:2px">បាន 25 រឿង</div>
          </div>
          <div class="coin-pkg-card" onclick="selectCoinPackage(100, 50000)" style="cursor:pointer;padding:10px;background:var(--surface-2);border:1px solid var(--line);border-radius:10px;text-align:center;transition:all .2s ease">
            <div style="font-size:15px;font-weight:900;color:#eab308">100 Coins</div>
            <div style="font-size:12px;font-weight:700;color:var(--ink);margin-top:2px">50,000 ៛</div>
            <div style="font-size:10px;color:var(--muted);margin-top:2px">បាន 50 រឿង</div>
          </div>
        </div>
      </div>

      <!-- Payment & QR Code Section -->
      <div style="background:var(--surface-2);border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;gap:14px;flex-wrap:wrap;align-items:center">
        <div style="text-align:center;flex-shrink:0;margin:0 auto">
          <img src="/dl/qr_payment.png" alt="Admin QR Payment" style="width:140px;height:auto;border-radius:10px;border:1.5px solid rgba(255,255,255,0.15);box-shadow:0 4px 15px rgba(0,0,0,0.5)">
          <div style="font-size:10.5px;color:var(--muted);margin-top:4px;font-weight:700">QR ផ្លូវការរបស់ ADMIN</div>
        </div>
        <div style="flex:1;min-width:200px;display:flex;flex-direction:column;gap:6px;font-size:12px">
          <div style="font-weight:800;color:var(--accent);font-size:12.5px">📌 របៀបទូទាត់ប្រាក់ &amp; ទទួល Coin:</div>
          <div style="color:var(--ink);line-height:1.5">
            1. ស្កេន QR Code ខាងឆ្វេង ដើម្បីផ្ទេរប្រាក់ទៅកាន់ Admin<br>
            2. អត្រាប្តូរប្រាក់: <b>1 Coin = 500៛</b> (1 រឿង = 2 Coins = 1,000៛)<br>
            3. បន្ទាប់ពីផ្ទេរប្រាក់រួច បញ្ចូលព័ត៌មានខាងក្រោម រួចចុច "ផ្ញើសំណើទិញ Coin"<br>
            4. Admin នឹងពិនិត្យ និងបញ្ចូល Coin ជូនគណនីរបស់អ្នកភ្លាមៗ!
          </div>
        </div>
      </div>

      <!-- Coin Request Form -->
      <div style="display:flex;flex-direction:column;gap:10px">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div>
            <label style="font-size:11.5px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">ចំនួន Coin ចង់ទិញ:</label>
            <input type="number" id="coinReqInput" value="20" min="2" max="10000" oninput="onCoinReqInputChange()" style="width:100%;height:38px;background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:0 10px;color:#eab308;font:800 15px var(--font-mono)">
          </div>
          <div>
            <label style="font-size:11.5px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">ទឹកប្រាក់ត្រូវទូទាត់ (៛):</label>
            <input type="text" id="coinReqRielDisplay" value="10,000 ៛" readonly style="width:100%;height:38px;background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:0 10px;color:var(--good);font:800 15px var(--font-mono)">
          </div>
        </div>

        <div>
          <label style="font-size:11.5px;font-weight:700;color:var(--muted);display:block;margin-bottom:4px">ព័ត៌មានផ្ទេរប្រាក់ (លេខទូរស័ព្ទ / ឈ្មោះគណនីធនាគារ / ចំណាំ):</label>
          <input type="text" id="coinReqNoteInput" placeholder="ឧ. ផ្ទេរពីគណនី ABA ឈ្មោះ SOK DARA ឬលេខ 012345678" style="width:100%;height:38px;background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:0 10px;color:var(--ink);font:600 12.5px var(--font-ui)">
        </div>

        <div id="coinReqStatusMsg" style="display:none;font-size:12px;padding:8px 12px;border-radius:8px"></div>

        <button type="button" class="btn primary" id="coinReqSubmitBtn" onclick="submitCoinRequest()" style="height:40px;background:linear-gradient(135deg,#eab308,#ca8a04);color:#000;font-weight:800;font-size:13px;border-radius:8px;box-shadow:0 3px 12px rgba(234,179,8,0.35);display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer">
          <span>📤 ផ្ញើសំណើទិញ Coin ទៅ Admin</span>
        </button>
      </div>

      <!-- User's My Coin Requests History -->
      <div style="border-top:1px solid var(--line);padding-top:12px">
        <div style="font-size:12.5px;font-weight:800;color:var(--ink);display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <span>📋 ប្រវត្តិសំណើទិញ Coin របស់អ្នក</span>
          <button type="button" class="btn ghost sm" onclick="loadMyCoinRequests()" style="font-size:11px;padding:2px 8px">🔄 Refresh</button>
        </div>
        <div id="coinMyRequestsList" style="display:flex;flex-direction:column;gap:6px;max-height:160px;overflow-y:auto">
          <div style="text-align:center;padding:12px;color:var(--muted);font-size:11.5px">មិនទាន់មានសំណើទិញ Coin ទេ</div>
        </div>
      </div>
    </div>

    <div class="modal-foot" style="margin-top:12px;padding-top:10px;border-top:1px solid var(--line,#3a2c20);display:flex;justify-content:space-between;align-items:center">
      <div style="font-size:11px;color:var(--muted)">🔒 1 Coin = 500៛ | 1 រឿង = 2 Coins (1,000៛) ដោះសោរគ្រប់ភាគ</div>
      <button class="btn ghost sm" onclick="closeCoinModal()">បិទ</button>
    </div>
  </div>
</div>

'''
if target_modal in text and 'id="coinModal"' not in text:
    text = text.replace(target_modal, coin_modal_html + target_modal, 1)
    print("Added #coinModal before #userCtrlModal")
else:
    print("#coinModal already present or target not found")

# 3. Add #ddCoinPriceBadge and #ddBuyDramaBtn to Drama Detail Action row
target_dd_btns = '''          <button class="btn primary sm" id="ddVipUnlockBtn" onclick="promptVipModal(11)" style="font-family:var(--font-km);font-weight:800;font-size:12px;padding:7px 14px;background:linear-gradient(135deg,#ff6a2b,#ff2e63);box-shadow:0 3px 12px rgba(255,106,43,0.4);display:inline-flex;align-items:center;gap:6px" title="ស្នើសុំ VIP ដើម្បីដោះសោរគ្រប់ភាគ">
            <span>👑 ស្នើសុំ VIP (ដោះសោរគ្រប់ភាគ)</span>
          </button>'''

replacement_dd_btns = '''          <button class="btn primary sm" id="ddVipUnlockBtn" onclick="promptVipModal(6)" style="font-family:var(--font-km);font-weight:800;font-size:12px;padding:7px 14px;background:linear-gradient(135deg,#ff6a2b,#ff2e63);box-shadow:0 3px 12px rgba(255,106,43,0.4);display:inline-flex;align-items:center;gap:6px" title="ស្នើសុំ VIP ដើម្បីដោះសោរគ្រប់ភាគ">
            <span>👑 ស្នើសុំ VIP (ដោះសោរគ្រប់ភាគ)</span>
          </button>
          <span id="ddCoinPriceBadge" style="display:inline-flex;align-items:center;gap:4px;font-size:11.5px;font-weight:800;padding:6px 12px;border-radius:8px;background:rgba(234,179,8,0.15);color:#eab308;border:1px solid rgba(234,179,8,0.4)">
            🪙 2 Coins (1,000៛)
          </span>
          <button class="btn sm" id="ddBuyDramaBtn" onclick="buyCurrentDramaWithCoins()" style="font-family:var(--font-km);font-weight:800;font-size:12px;padding:7px 14px;background:linear-gradient(135deg,#eab308,#ca8a04);color:#000;border:none;border-radius:8px;box-shadow:0 3px 12px rgba(234,179,8,0.35);cursor:pointer;display:inline-flex;align-items:center;gap:6px" title="ទិញដោះសោររឿងនេះដោយប្រើ 2 Coins (1,000៛)">
            <span>🛒 ទិញរឿងនេះ (2 Coins)</span>
          </button>'''

if target_dd_btns in text and 'ddBuyDramaBtn' not in text:
    text = text.replace(target_dd_btns, replacement_dd_btns, 1)
    print("Added #ddCoinPriceBadge and #ddBuyDramaBtn to Drama Detail")
else:
    print("Drama Detail action row target not found or already has ddBuyDramaBtn")

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(text)
print("Phase 1 HTML updates applied successfully.")
