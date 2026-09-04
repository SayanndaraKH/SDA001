# -*- coding: utf-8 -*-
import sys

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '      <!-- TAB 3: REQUEST VIP FORM -->'
end_marker = '<!-- Dedicated Folder Picker Modal -->'

if start_marker not in content:
    print("ERROR: start_marker not found")
    sys.exit(1)
if end_marker not in content:
    print("ERROR: end_marker not found")
    sys.exit(1)

part1 = content[:content.index(start_marker)]
part2 = content[content.index(end_marker):]

new_middle = '''      <!-- TAB 3: REQUEST VIP FORM -->
      <div id="authTabVipSec" style="display:none;flex-direction:column;gap:12px">
        <!-- Current User Status Card -->
        <div id="regStatusBanner" style="background:var(--surface-2);padding:12px 14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:8px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:12px;color:var(--muted);font-weight:600">ស្ថានភាពគណនីរបស់អ្នក:</span>
            <span id="regCurrentStatusBadge" style="font-size:11.5px;font-weight:800;padding:3px 10px;border-radius:6px;background:rgba(255,255,255,0.1);color:var(--ink)">មិនទាន់ចូលគណនី</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:12px;color:var(--muted);font-weight:600">សិទ្ធិទស្សនា &amp; ដោនឡូត:</span>
            <span id="regExpiryText" style="font-size:12px;font-weight:700;color:var(--ink-2)">ភាគ 1-10 ឥតគិតថ្លៃ</span>
          </div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2px">
            <span style="font-size:11.5px;color:var(--muted);font-weight:600">Device ID:</span>
            <div style="display:flex;align-items:center;gap:6px">
              <code id="regDeviceId" style="font:700 11px var(--font-mono);color:var(--ink);background:var(--surface);padding:2px 6px;border-radius:4px;border:1px solid var(--line)">...</code>
              <button class="btn ghost sm" id="regCopyDevId" style="padding:1px 6px;font-size:10px" title="Copy Device ID">📋 ចម្លង</button>
            </div>
          </div>
        </div>

        <!-- Pending Notice (Shown only when status is pending_vip) -->
        <div id="vipPendingBanner" style="display:none;background:rgba(241,196,15,0.12);border:1px solid rgba(241,196,15,0.4);border-radius:12px;padding:14px;text-align:center">
          <div style="font-size:24px;margin-bottom:4px">⏳</div>
          <div style="font-weight:800;font-size:13.5px;color:var(--gold);margin-bottom:4px">សំណើសុំកញ្ចប់ VIP របស់អ្នកបានផ្ញើរួចរាល់ហើយ!</div>
          <div style="font-size:12px;color:var(--ink-2);line-height:1.5">គណនីរបស់អ្នកកំពុងស្ថិតក្នុងការត្រួតពិនិត្យដោយ Admin។<br>សូមទំនាក់ទំនង Admin តាមរយៈ Telegram ខាងក្រោម ដើម្បីឱ្យ Admin បើកសិទ្ធិ VIP ជូនភ្លាមៗ។</div>
        </div>

        <!-- KHQR Payment & Telegram Contact Section (Loaded from Admin Settings) -->
        <div id="vipKhqrSection" style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <!-- KHQR Card -->
          <div id="vipKhqrCard" style="display:none;flex-direction:column;align-items:center;text-align:center;padding:12px;background:var(--surface);border:1px solid var(--line);border-radius:10px">
            <div style="font-weight:700;font-size:12.5px;color:var(--ink);margin-bottom:8px">📲 ស្កេនទូទាត់ប្រាក់តាម KHQR (Bakong / គ្រប់ធនាគារ)</div>
            <img id="vipKhqrImg" src="" alt="KHQR Payment" style="max-width:210px;width:100%;border-radius:10px;border:1.5px solid var(--accent);box-shadow:0 6px 20px rgba(0,0,0,0.5)">
          </div>

          <!-- Telegram Contact Row -->
          <div id="vipTgLinksRow" style="display:flex;gap:8px;flex-wrap:wrap">
            <a id="vipTgAdminLink" href="#" target="_blank" class="btn primary sm" style="flex:1 1 180px;height:36px;text-decoration:none;display:none;align-items:center;justify-content:center;gap:6px;background:#0088cc;font-weight:700;font-size:12px">
              <span>💬 ទាក់ទង Admin (Telegram)</span>
            </a>
            <a id="vipTgGroupLink" href="#" target="_blank" class="btn ghost sm" style="flex:1 1 180px;height:36px;text-decoration:none;display:none;align-items:center;justify-content:center;gap:6px;border-color:#0088cc;color:#29b6f6;font-weight:700;font-size:12px">
              <span>👥 ចូលរួម Group Telegram</span>
            </a>
          </div>
        </div>

        <!-- VIP Package Selection Form (Hidden when user is already pending_vip) -->
        <div id="tabPanelVip" style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:12px">
          <div style="font:700 13px var(--font-ui);color:var(--ink-2)">ជ្រើសរើសកញ្ចប់ VIP ដើម្បីមើលគ្រប់ភាគ (Unlock All Episodes)</div>
          
          <!-- Package Radios -->
          <div style="display:flex;flex-direction:column;gap:6px">
            <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line);cursor:pointer">
              <input type="radio" name="vipPackageRadio" value="1_month">
              <div style="flex:1;display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700;font-size:12.5px;color:var(--ink)">🌟 VIP 1 ខែ</span>
                <span style="font-size:11.5px;color:var(--accent);font-weight:600">30 ថ្ងៃ</span>
              </div>
            </label>
            <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line);cursor:pointer">
              <input type="radio" name="vipPackageRadio" value="3_months">
              <div style="flex:1;display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700;font-size:12.5px;color:var(--ink)">🔥 VIP 3 ខែ</span>
                <span style="font-size:11.5px;color:var(--accent);font-weight:600">90 ថ្ងៃ</span>
              </div>
            </label>
            <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line);cursor:pointer">
              <input type="radio" name="vipPackageRadio" value="6_months">
              <div style="flex:1;display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700;font-size:12.5px;color:var(--ink)">💎 VIP 6 ខែ</span>
                <span style="font-size:11.5px;color:var(--accent);font-weight:600">180 ថ្ងៃ</span>
              </div>
            </label>
            <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line);cursor:pointer">
              <input type="radio" name="vipPackageRadio" value="1_year" checked>
              <div style="flex:1;display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700;font-size:12.5px;color:var(--ink)">👑 VIP 1 ឆ្នាំ (ពេញនិយម)</span>
                <span style="font-size:11.5px;color:var(--accent);font-weight:600">365 ថ្ងៃ</span>
              </div>
            </label>
            <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line);cursor:pointer">
              <input type="radio" name="vipPackageRadio" value="lifetime">
              <div style="flex:1;display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:700;font-size:12.5px;color:var(--ink)">♾️ VIP មួយជីវិត (Lifetime)</span>
                <span style="font-size:11.5px;color:var(--good);font-weight:700">គ្មានដែនកំណត់</span>
              </div>
            </label>
          </div>

          <div>
            <label style="font:600 11.5px var(--font-ui);color:var(--muted);display:block;margin-bottom:4px">ឈ្មោះអ្នកប្រើប្រាស់ (Name) <span style="color:var(--accent)">*</span></label>
            <input type="text" id="regNameInput" placeholder="ឧ. សុខ ដារ៉ា / Sok Dara" style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 13px var(--font-ui)">
          </div>
          <div>
            <label style="font:600 11.5px var(--font-ui);color:var(--muted);display:block;margin-bottom:4px">លេខទូរស័ព្ទ ឬ Telegram (Phone / Telegram) <span style="color:var(--accent)">*</span></label>
            <input type="text" id="regContactInput" placeholder="ឧ. 012 345 678 / @sokdara" style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 13px var(--font-ui)">
          </div>
          <div>
            <label style="font:600 11.5px var(--font-ui);color:var(--muted);display:block;margin-bottom:4px">ចំណាំបន្ថែម (Note / Optional)</label>
            <input type="text" id="regNoteInput" placeholder="ឧ. ស្នើសុំប្រើប្រាស់លើកុំព្យូទ័រធ្វើការ..." style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 13px var(--font-ui)">
          </div>
          <button class="btn primary" id="regSubmitBtn" style="height:38px;margin-top:4px;font-weight:700;font-size:13.5px;display:flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#ff6a2b,#ff2e63)">
            <span>🚀 ផ្ញើសំណើសុំកញ្ចប់ VIP</span>
          </button>

          <div style="padding:10px 12px;background:rgba(255,106,43,0.08);border:1px solid rgba(255,106,43,0.25);border-radius:10px;font:11.5px/1.5 var(--font-ui);color:var(--ink-2)">
            💡 <b>ចំណាំ៖</b> បន្ទាប់ពីផ្ញើសំណើរួច Admin នឹងពិនិត្យនិងបើកសិទ្ធិ VIP ជូនលោកអ្នក ដើម្បីដោះសោរគ្រប់ភាគទាំងអស់!
          </div>
        </div>
      </div>
    </div>
    <div class="modal-foot" style="margin-top:14px;padding-top:12px;border-top:1px solid var(--line,#3a2c20);display:flex;justify-content:space-between;align-items:center">
      <div id="authFootUserLabel" style="font-size:11.5px;color:var(--muted)"></div>
      <button class="btn ghost sm" id="regCloseBtn2">បិទ</button>
    </div>
  </div>
</div>

<!-- User Control / Management Modal (Admin Dashboard) -->
<div class="modal" id="userCtrlModal" hidden style="z-index:110;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px)">
  <div class="modal-card" style="max-width:760px;width:95vw;padding:22px;background:var(--surface,#18110b);border:1px solid var(--line,#3a2c20);border-radius:18px;box-shadow:0 24px 60px rgba(0,0,0,0.85);max-height:90vh;display:flex;flex-direction:column">
    <div class="modal-head" style="padding-bottom:12px;margin-bottom:14px;border-bottom:1px solid var(--line,#3a2c20)">
      <div>
        <div class="modal-title" style="font-size:18px;font-weight:800;color:var(--ink);display:flex;align-items:center;gap:8px">
          <span>🛡️ SYD ADMIN DASHBOARD</span>
        </div>
        <div class="modal-sub" style="color:var(--accent);font-weight:600;margin-top:3px">គ្រប់គ្រងគណនីអ្នកប្រើប្រាស់, សិទ្ធិ VIP, KHQR &amp; Telegram</div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <span id="adminLockBadge" style="font-size:11px;font-weight:700;padding:3px 10px;border-radius:6px;background:rgba(255,255,255,0.08);color:var(--muted)">🔒 LOCKED</span>
        <button class="x" id="userCtrlClose" title="Close">✕</button>
      </div>
    </div>

    <!-- Locked State: Enter PIN -->
    <div id="adminPinBox" style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
      <input type="password" id="adminPinInput" autocomplete="new-password" placeholder="បញ្ចូល Admin PIN (Default: 8888)" style="flex:1;height:38px;background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:700 13px var(--font-mono)">
      <button class="btn primary sm" id="adminPinBtn" style="height:38px;padding:0 18px;white-space:nowrap;font-weight:700">🔓 ដោះសោរ Admin</button>
    </div>

    <!-- Unlocked State: Tab Switcher & Panels -->
    <div id="adminUnlockedPanel" hidden style="display:flex;flex-direction:column;flex:1;min-height:0;gap:12px">
      <!-- Admin Tab Switcher -->
      <div style="display:flex;gap:6px;background:var(--surface-2);padding:4px;border-radius:10px;border:1px solid var(--line)">
        <button type="button" class="btn sm uc-tab-btn on" id="ucTabBtnUsers" onclick="switchUcTab('users')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px">
          👥 គ្រប់គ្រងអ្នកប្រើប្រាស់ &amp; VIP
        </button>
        <button type="button" class="btn sm uc-tab-btn" id="ucTabBtnSettings" onclick="switchUcTab('settings')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px">
          ⚙️ KHQR &amp; Telegram
        </button>
        <button type="button" class="btn sm uc-tab-btn" id="ucTabBtnSys" onclick="switchUcTab('system')" style="flex:1;font-weight:700;font-size:12px;border-radius:8px;padding:7px 6px">
          🎬 Download &amp; Storage
        </button>
      </div>

      <!-- TAB 1: USER MANAGEMENT -->
      <div id="ucTabUsersSec" class="modal-scroll" style="display:flex;flex-direction:column;gap:12px;padding-right:2px">
        <!-- Search & Filter Bar -->
        <div style="background:var(--surface-2);padding:12px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="display:flex;gap:8px;align-items:center">
            <input type="text" id="ucUserSearchInput" placeholder="🔍 ស្វែងរកតាមឈ្មោះ, Username, លេខទូរស័ព្ទ ឬ Device ID..." style="flex:1;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 12.5px var(--font-ui)">
            <button class="btn ghost sm" id="adminRefreshUsersBtn" style="height:36px;padding:0 12px;font-size:11.5px;font-weight:700" title="Refresh Users">🔄 ផ្ទុកឡើងវិញ</button>
          </div>
          <!-- Filter Buttons -->
          <div style="display:flex;gap:6px;flex-wrap:wrap">
            <button type="button" class="btn ghost sm uc-filter-btn on" data-filter="all" style="font-size:11px;padding:3px 10px;border-radius:20px">ទាំងអស់ (<span id="cntAll">0</span>)</button>
            <button type="button" class="btn ghost sm uc-filter-btn" data-filter="vip" style="font-size:11px;padding:3px 10px;border-radius:20px;color:var(--good);border-color:rgba(46,204,113,0.3)">👑 VIP (<span id="cntVip">0</span>)</button>
            <button type="button" class="btn ghost sm uc-filter-btn" data-filter="pending" style="font-size:11px;padding:3px 10px;border-radius:20px;color:var(--gold);border-color:rgba(241,196,15,0.3)">⏳ រង់ចាំ (<span id="cntPend">0</span>)</button>
            <button type="button" class="btn ghost sm uc-filter-btn" data-filter="regular" style="font-size:11px;padding:3px 10px;border-radius:20px;color:var(--accent);border-color:rgba(255,106,43,0.3)">👤 ធម្មតា (<span id="cntReg">0</span>)</button>
            <button type="button" class="btn ghost sm uc-filter-btn" data-filter="banned" style="font-size:11px;padding:3px 10px;border-radius:20px;color:var(--bad);border-color:rgba(255,46,99,0.3)">🚫 Banned (<span id="cntBan">0</span>)</button>
          </div>
        </div>

        <!-- Manual Device ID / Username VIP Approver Card -->
        <div style="background:var(--surface-2);padding:12px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:8px">
          <div style="font:700 12px var(--font-ui);color:var(--ink-2)">⚡ បើកសិទ្ធិ VIP ផ្ទាល់ (Manual Approval):</div>
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
            <input type="text" id="adminManualDevId" placeholder="បញ្ចូល Device ID ឬ Username..." style="flex:1 1 180px;height:34px;background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:0 10px;color:var(--ink);font:12px var(--font-mono)">
            <select id="adminManualPkg" style="height:34px;background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:0 8px;color:var(--ink);font:600 11.5px var(--font-ui)">
              <option value="1_month">VIP 1 ខែ (30 ថ្ងៃ)</option>
              <option value="3_months">VIP 3 ខែ (90 ថ្ងៃ)</option>
              <option value="6_months">VIP 6 ខែ (180 ថ្ងៃ)</option>
              <option value="1_year" selected>VIP 1 ឆ្នាំ (365 ថ្ងៃ)</option>
              <option value="lifetime">VIP មួយជីវិត (Lifetime)</option>
              <option value="custom">កំណត់ថ្ងៃផ្ទាល់ (Custom Days)</option>
            </select>
            <input type="number" id="adminManualDaysInput" placeholder="ចំនួនថ្ងៃ (ឧ. 45)" min="1" max="9999" style="width:105px;height:34px;background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:0 8px;color:var(--ink);font:600 12px var(--font-mono);display:none">
            <button class="btn primary sm" id="adminManualApproveBtn" style="height:34px;white-space:nowrap;font-size:12px;font-weight:700;padding:0 14px">+ បើកសិទ្ធិ VIP</button>
          </div>
        </div>

        <!-- User List Container -->
        <div id="adminUserListContainer" style="display:flex;flex-direction:column;gap:10px;min-height:100px">
          <div style="text-align:center;padding:24px;color:var(--muted);font-size:12.5px">កំពុងផ្ទុកបញ្ជីអ្នកប្រើប្រាស់...</div>
        </div>
      </div>

      <!-- TAB 2: KHQR & TELEGRAM SETTINGS -->
      <div id="ucTabSettingsSec" class="modal-scroll" style="display:none;flex-direction:column;gap:14px;padding-right:2px">
        <!-- Card 1: KHQR Payment Image Upload -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="font:700 13px var(--font-ui);color:var(--accent);display:flex;align-items:center;gap:6px">
            <span>📲</span> <span>រូបភាព KHQR សម្រាប់ទូទាត់ប្រាក់ (Payment QR Code)</span>
          </div>
          <div style="font-size:12px;color:var(--muted);line-height:1.4">
            Upload រូបភាព QR Code (Bakong / ABA / ACLEDA KHQR)។ រូបភាពនេះនឹងបង្ហាញនៅលើទំព័រ VIP សម្រាប់ User ស្កេនទូទាត់ប្រាក់។
          </div>
          
          <div style="display:flex;gap:16px;align-items:center;margin-top:4px;flex-wrap:wrap">
            <div id="adminKhqrPreviewWrap" style="width:140px;height:140px;border-radius:12px;border:2px dashed var(--line);background:var(--surface);display:flex;align-items:center;justify-content:center;overflow:hidden;position:relative">
              <img id="adminKhqrPreview" src="" alt="KHQR Preview" style="width:100%;height:100%;object-fit:contain;display:none">
              <div id="adminKhqrPlaceholder" style="font-size:11px;color:var(--muted);text-align:center;padding:10px">គ្មានរូបភាព KHQR</div>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px">
              <input type="file" id="adminKhqrFileInput" accept="image/*" style="display:none">
              <button type="button" class="btn primary sm" id="adminKhqrUploadBtn" style="font-weight:700;font-size:12px">📁 ជ្រើសរើសរូបភាព QR</button>
              <button type="button" class="btn ghost sm" id="adminKhqrRemoveBtn" style="font-size:11.5px;color:var(--bad);border-color:rgba(255,46,99,0.3)">🗑️ លុបរូប QR</button>
              <div style="font-size:11px;color:var(--muted)">ទម្រង់ PNG, JPG ឬ WebP (ទំហំ &lt; 3MB)</div>
            </div>
          </div>
        </div>

        <!-- Card 2: Personal Telegram & Group Telegram Links -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:10px">
          <div style="font:700 13px var(--font-ui);color:var(--accent);display:flex;align-items:center;gap:6px">
            <span>💬</span> <span>Link Telegram ទំនាក់ទំនង &amp; Link Group Telegram</span>
          </div>

          <div>
            <label style="font:600 12px var(--font-ui);color:var(--ink-2);display:block;margin-bottom:4px">1. Link Telegram ផ្ទាល់ខ្លួន Admin (សម្រាប់ User ទំនាក់ទំនង):</label>
            <input type="text" id="adminTgAdminInput" placeholder="ឧ. https://t.me/syd_support ឬ @syd_support" style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 12.5px var(--font-mono)">
            <div style="font-size:11px;color:var(--muted);margin-top:2px">ប៊ូតុង &quot;💬 ទាក់ទង Admin (Telegram)&quot; លើ VIP Portal នឹងបើកទៅកាន់ Link នេះ</div>
          </div>

          <div style="margin-top:4px">
            <label style="font:600 12px var(--font-ui);color:var(--ink-2);display:block;margin-bottom:4px">2. Link Telegram Group (សម្រាប់សមាជិកជជែក &amp; ទទួលដំណឹង):</label>
            <input type="text" id="adminTgGroupInput" placeholder="ឧ. https://t.me/syd_community" style="width:100%;height:36px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:0 12px;color:var(--ink);font:600 12.5px var(--font-mono)">
            <div style="font-size:11px;color:var(--muted);margin-top:2px">ប៊ូតុង &quot;👥 ចូលរួម Group Telegram&quot; លើ VIP Portal នឹងបើកទៅកាន់ Link នេះ</div>
          </div>
        </div>

        <!-- Card 3: System Mode Selection -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line);display:flex;flex-direction:column;gap:8px">
          <div style="font:700 13px var(--font-ui);color:var(--accent);display:flex;align-items:center;gap:6px">
            <span>🛡️</span> <span>របៀបដំណើរការប្រព័ន្ធ (System Access Mode)</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;margin-top:4px">
            <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-size:12.5px;color:var(--ink);padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line)">
              <input type="radio" name="adminModeRadio" value="vip_required" style="margin-top:2px">
              <div>
                <b style="color:var(--accent)">🔒 VIP Required (គណនីធម្មតាមើលបានភាគ 1-10, VIP មើលបានគ្រប់ភាគ - Recommended)</b>
                <div style="font-size:11.5px;color:var(--muted);margin-top:2px">អ្នកប្រើប្រាស់ធម្មតាអាចមើលនិងទាញយកបានត្រឹមភាគ 1-10។ ចាប់ពីភាគ 11 ឡើងទៅ តម្រូវឱ្យមានកញ្ចប់ VIP។</div>
              </div>
            </label>
            <label style="display:flex;align-items:flex-start;gap:8px;cursor:pointer;font-size:12.5px;color:var(--ink);padding:8px 10px;border-radius:8px;background:var(--surface);border:1px solid var(--line)">
              <input type="radio" name="adminModeRadio" value="free_all" style="margin-top:2px">
              <div>
                <b style="color:var(--good)">🟢 Free 100% (បើកទូលាយសេរីទាំងអស់ គ្មានការ Lock)</b>
                <div style="font-size:11.5px;color:var(--muted);margin-top:2px">អ្នកប្រើប្រាស់ទាំងអស់អាចមើលនិងទាញយកគ្រប់ភាគដោយឥតគិតថ្លៃ។</div>
              </div>
            </label>
          </div>
        </div>

        <!-- Save Settings Button -->
        <button class="btn primary" id="adminSaveAllSettingsBtn" style="height:40px;font-weight:800;font-size:13.5px;display:flex;align-items:center;justify-content:center;gap:8px;background:linear-gradient(135deg,#ff6a2b,#ff2e63)">
          <span>💾 រក្សាទុកការកំណត់ទាំងអស់ (Save All Settings)</span>
        </button>
      </div>

      <!-- TAB 3: DOWNLOAD & STORAGE -->
      <div id="ucTabSysSec" class="modal-scroll" style="display:none;flex-direction:column;gap:12px;padding-right:2px">
        <!-- Download Controls -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line)">
          <div style="font:700 13px var(--font-ui);color:var(--ink-2);margin-bottom:10px">Download Controls</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
            <div>
              <label style="font:600 11.5px var(--font-ui);color:var(--muted);display:block;margin-bottom:4px">Quality</label>
              <select id="ucQuality" style="width:100%;height:34px;background:var(--surface);border:1px solid var(--line);border-radius:8px;color:var(--ink);padding:0 8px;font:600 12.5px var(--font-ui)">
                <option value="1080p">1080p Full HD (Best)</option>
                <option value="720p">720p HD</option>
                <option value="540p">540p SD</option>
              </select>
            </div>
            <div>
              <label style="font:600 11.5px var(--font-ui);color:var(--muted);display:block;margin-bottom:4px">Parallel Series</label>
              <select id="ucSeries" style="width:100%;height:34px;background:var(--surface);border:1px solid var(--line);border-radius:8px;color:var(--ink);padding:0 8px;font:600 12.5px var(--font-ui)">
                <option value="1">1 series at a time</option>
                <option value="2">2 series at a time</option>
                <option value="3">3 series at a time</option>
                <option value="4">4 series at a time</option>
                <option value="6">6 series (Max Speed)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Storage Folder -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line)">
          <div style="font:700 13px var(--font-ui);color:var(--ink-2);margin-bottom:10px">Storage &amp; Folders</div>
          <div style="font:11.5px/1.4 var(--font-mono);color:var(--muted);word-break:break-all;margin-bottom:10px" id="ucFolderPath">C:\\Users\\Administrator\\Videos\\Hongguo</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn ghost sm" id="ucOpenFolder" style="flex:1">📂 Open Folder</button>
            <button class="btn ghost sm" id="ucChangeFolder" style="flex:1">📁 Change Folder</button>
          </div>
        </div>

        <!-- System Operations -->
        <div style="background:var(--surface-2);padding:14px;border-radius:12px;border:1px solid var(--line)">
          <div style="font:700 13px var(--font-ui);color:var(--ink-2);margin-bottom:10px">System Operations</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <button class="btn ghost sm" id="ucRefreshApp" style="flex:1">🔄 Refresh Data</button>
          </div>
        </div>
      </div>
    </div>

    <div class="modal-foot" style="margin-top:14px;padding-top:12px;border-top:1px solid var(--line,#3a2c20);display:flex;justify-content:flex-end">
      <button class="btn primary sm" id="userCtrlCloseB">Done</button>
    </div>
  </div>
</div>

'''

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(part1 + new_middle + part2)

print("Updated HTML successfully!")
