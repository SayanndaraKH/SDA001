import os

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"

gui_code = r'''# -*- coding: utf-8 -*-
"""
SYD 8MOVIE PRO - Native Desktop GUI Application (PyQt6)
-------------------------------------------------------
100% Native Windows Form (No web server, no browser, zero connection errors).
"""

import os
import sys
import time
import json
import hashlib
import urllib.request
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QGridLayout,
    QProgressBar, QDialog, QCheckBox, QFileDialog, QMessageBox, QFrame,
    QSizePolicy, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QThreadPool, QRunnable, QObject
from PyQt6.QtGui import QPixmap, QImage, QFont, QIcon, QColor, QPalette, QCursor

# Import backend modules
try:
    from .scraper_8movie import search_dramas, get_catalog, get_drama_detail, CATEGORIES
    from .downloader import DownloaderManager
    from .translator import translate_to_khmer, translate_batch
except ImportError:
    from scraper_8movie import search_dramas, get_catalog, get_drama_detail, CATEGORIES
    from downloader import DownloaderManager
    from translator import translate_to_khmer, translate_batch

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, 'data')
POSTER_CACHE_DIR = os.path.join(DATA_DIR, 'poster_cache')
CONFIG_FILE = os.path.join(HERE, 'config.json')

os.makedirs(POSTER_CACHE_DIR, exist_ok=True)

HEADERS_IMG = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Referer': 'https://8movie.com/'
}

# ----------------- Configuration Helpers -----------------
def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "output_dir": os.path.join(os.path.expanduser("~"), "Videos", "SYD-8Movie"),
        "max_concurrent_downloads": 3,
        "auto_translate": True
    }

def save_config(cfg: Dict[str, Any]):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

# ----------------- Async Image Loader -----------------
class ImageSignals(QObject):
    loaded = pyqtSignal(str, QPixmap)

class ImageLoadWorker(QRunnable):
    def __init__(self, url: str, target_size: QSize, signals: ImageSignals):
        super().__init__()
        self.url = url.strip()
        self.target_size = target_size
        self.signals = signals

    def run(self):
        if not self.url:
            return
        full_url = self.url if self.url.startswith("http") else f"https://8movie.com{self.url}"
        h = hashlib.md5(full_url.encode()).hexdigest() + ".jpg"
        cache_path = os.path.join(POSTER_CACHE_DIR, h)

        pixmap = None
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
            pixmap = QPixmap(cache_path)
        else:
            try:
                req = urllib.request.Request(full_url, headers=HEADERS_IMG)
                with urllib.request.urlopen(req, timeout=12) as r:
                    data = r.read()
                    if len(data) > 100:
                        with open(cache_path, 'wb') as f:
                            f.write(data)
                        img = QImage()
                        if img.loadFromData(data):
                            pixmap = QPixmap.fromImage(img)
            except Exception:
                pass

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.target_size,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.signals.loaded.emit(self.url, scaled)

# ----------------- Async Data Fetcher Threads -----------------
class CatalogWorker(QThread):
    finished = pyqtSignal(list, int)
    error = pyqtSignal(str)

    def __init__(self, cat_id: str, page: int, auto_translate: bool):
        super().__init__()
        self.cat_id = cat_id
        self.page = page
        self.auto_translate = auto_translate

    def run(self):
        try:
            items = get_catalog(self.cat_id, page=self.page)
            if self.auto_translate:
                titles = [c["title"] for c in items if not c.get("title_km")]
                if titles:
                    t_map = translate_batch(titles[:35])
                    for c in items:
                        if not c.get("title_km"):
                            c["title_km"] = t_map.get(c["title"], "")
            self.finished.emit(items, self.page)
        except Exception as e:
            self.error.emit(str(e))

class SearchWorker(QThread):
    finished = pyqtSignal(list, int)
    error = pyqtSignal(str)

    def __init__(self, keyword: str, page: int, auto_translate: bool):
        super().__init__()
        self.keyword = keyword
        self.page = page
        self.auto_translate = auto_translate

    def run(self):
        try:
            items = search_dramas(self.keyword, page=self.page)
            if self.auto_translate:
                titles = [c["title"] for c in items if not c.get("title_km")]
                if titles:
                    t_map = translate_batch(titles[:35])
                    for c in items:
                        if not c.get("title_km"):
                            c["title_km"] = t_map.get(c["title"], "")
            self.finished.emit(items, self.page)
        except Exception as e:
            self.error.emit(str(e))

class DetailWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, drama_id: str):
        super().__init__()
        self.drama_id = drama_id

    def run(self):
        try:
            detail = get_drama_detail(self.drama_id)
            if detail.get("title") and not detail.get("title_km"):
                detail["title_km"] = translate_to_khmer(detail["title"])
            self.finished.emit(detail)
        except Exception as e:
            self.error.emit(str(e))

# ----------------- Drama Card Widget -----------------
class DramaCardWidget(QFrame):
    def __init__(self, item: Dict[str, Any], main_window: 'MainWindow'):
        super().__init__()
        self.item = item
        self.main_window = main_window
        self.setObjectName("DramaCard")
        self.setFixedWidth(210)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Poster Image Label
        self.poster_lbl = QLabel()
        self.poster_lbl.setFixedSize(190, 270)
        self.poster_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_lbl.setStyleSheet("background-color: #211812; border-radius: 12px; border: 1px solid #352a20;")
        self.poster_lbl.setText("⏳ កំពុងផ្ទុក...")
        self.poster_lbl.mousePressEvent = lambda e: self.main_window.open_drama_detail(self.item["id"])

        # Overlay badges simulation: Rating & Eps
        meta_row = QHBoxLayout()
        self.rating_lbl = QLabel(f"★ {item.get('rating', 8.8)}")
        self.rating_lbl.setStyleSheet("color: #e0ad45; font-weight: bold; font-size: 11px; background: rgba(21,16,13,0.85); padding: 2px 6px; border-radius: 6px;")
        self.eps_lbl = QLabel(f"{item.get('episodes_count', '??')} ភាគ")
        self.eps_lbl.setStyleSheet("color: #d3c3b4; font-size: 11px; background: rgba(21,16,13,0.85); padding: 2px 6px; border-radius: 6px;")
        meta_row.addWidget(self.rating_lbl)
        meta_row.addStretch()
        meta_row.addWidget(self.eps_lbl)

        # Titles
        self.title_zh = QLabel(item.get("title", ""))
        self.title_zh.setStyleSheet("color: #f7efe7; font-weight: bold; font-size: 13px;")
        self.title_zh.setWordWrap(False)
        self.title_zh.setToolTip(item.get("title", ""))

        self.title_km = QLabel(item.get("title_km") or item.get("title", ""))
        self.title_km.setStyleSheet("color: #ffb14a; font-size: 12px; font-weight: 600;")
        self.title_km.setWordWrap(True)
        self.title_km.setFixedHeight(34)
        self.title_km.setToolTip(self.title_km.text())

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)

        self.btn_view = QPushButton("≡ ភាគ")
        self.btn_view.setStyleSheet("background: #ff6a2b; color: #fff; font-weight: bold; border-radius: 6px; padding: 5px;")
        self.btn_view.clicked.connect(lambda: self.main_window.open_drama_detail(self.item["id"]))

        self.btn_poster = QPushButton("🖼 Poster")
        self.btn_poster.setStyleSheet("background: rgba(36,221,207,0.18); color: #24ddcf; font-weight: bold; border-radius: 6px; padding: 5px;")
        self.btn_poster.clicked.connect(self.download_poster)

        self.btn_dl_all = QPushButton("⬇ ទាញ")
        self.btn_dl_all.setStyleSheet("background: #2a1f17; color: #f7efe7; font-weight: bold; border-radius: 6px; padding: 5px;")
        self.btn_dl_all.clicked.connect(self.quick_download)

        btn_row.addWidget(self.btn_view)
        btn_row.addWidget(self.btn_poster)
        btn_row.addWidget(self.btn_dl_all)

        layout.addWidget(self.poster_lbl)
        layout.addLayout(meta_row)
        layout.addWidget(self.title_zh)
        layout.addWidget(self.title_km)
        layout.addLayout(btn_row)

        # Request Async Image
        self.main_window.request_image(self.item.get("poster", ""), QSize(190, 270), self.set_pixmap)

    def set_pixmap(self, pixmap: QPixmap):
        self.poster_lbl.setPixmap(pixmap)
        self.poster_lbl.setText("")

    def download_poster(self):
        p_url = self.item.get("poster", "")
        if p_url:
            self.main_window.downloader.submit_poster(
                self.item["id"], self.item["title"], self.item.get("title_km", ""), p_url
            )
            self.main_window.show_toast(f"បានបន្ថែម Poster '{self.item['title']}' ទៅក្នុងបញ្ជីទាញយក!")

    def quick_download(self):
        self.main_window.open_drama_detail(self.item["id"], auto_download=True)

# ----------------- Episode Detail Dialog -----------------
class DramaDetailDialog(QDialog):
    def __init__(self, detail: Dict[str, Any], main_window: 'MainWindow', auto_download: bool = False):
        super().__init__(main_window)
        self.detail = detail
        self.main_window = main_window
        self.setWindowTitle(f"ព័ត៌មានលម្អិត & ភាគ - {detail.get('title', '')}")
        self.resize(880, 640)
        self.setStyleSheet("""
            QDialog { background-color: #1c1511; color: #f7efe7; }
            QLabel { color: #f7efe7; }
            QCheckBox { color: #f7efe7; font-size: 12px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)

        # Left Column: Poster & Quick Action
        left_col = QVBoxLayout()
        self.poster_lbl = QLabel()
        self.poster_lbl.setFixedSize(240, 340)
        self.poster_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.poster_lbl.setStyleSheet("background-color: #211812; border-radius: 12px; border: 1px solid #352a20;")
        self.poster_lbl.setText("⏳ កំពុងផ្ទុក...")
        left_col.addWidget(self.poster_lbl)

        btn_dl_poster = QPushButton("🖼 ទាញយក Poster HD")
        btn_dl_poster.setStyleSheet("background: #24ddcf; color: #08201c; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_dl_poster.clicked.connect(self.download_poster)
        left_col.addWidget(btn_dl_poster)

        btn_dl_all = QPushButton("⬇ ទាញយកគ្រប់ភាគទាំងអស់")
        btn_dl_all.setStyleSheet("background: #ff6a2b; color: #fff; font-weight: bold; padding: 10px; border-radius: 8px;")
        btn_dl_all.clicked.connect(self.download_all)
        left_col.addWidget(btn_dl_all)

        left_col.addStretch()
        main_layout.addLayout(left_col, stretch=1)

        # Right Column: Info & Episodes
        right_col = QVBoxLayout()

        title_zh = QLabel(detail.get("title", ""))
        title_zh.setStyleSheet("font-size: 20px; font-weight: bold; color: #f7efe7;")
        right_col.addWidget(title_zh)

        title_km = QLabel(detail.get("title_km") or detail.get("title", ""))
        title_km.setStyleSheet("font-size: 15px; font-weight: 600; color: #ffb14a; margin-bottom: 8px;")
        right_col.addWidget(title_km)

        tags_txt = " · ".join(detail.get("tags", [])) or "8Movie"
        meta_lbl = QLabel(f"ពិន្ទុ: ★ {detail.get('rating', 8.8)}  |  ចំនួនភាគ: {detail.get('episodes_count', len(detail.get('episodes', [])))} ភាគ  |  {tags_txt}")
        meta_lbl.setStyleSheet("color: #9c8a7b; font-size: 12px; margin-bottom: 8px;")
        right_col.addWidget(meta_lbl)

        desc_lbl = QLabel(detail.get("description") or "មិនមានការពិពណ៌នាសង្ខេបឡើយ។")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #d3c3b4; font-size: 12px; line-height: 1.4; max-height: 80px;")
        right_col.addWidget(desc_lbl)

        # Episode Controls Header
        ep_hdr = QHBoxLayout()
        ep_title = QLabel("បញ្ជីភាគ (ជ្រើសរើសភាគដែលចង់ទាញយក):")
        ep_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #f7efe7;")
        ep_hdr.addWidget(ep_title)
        ep_hdr.addStretch()

        btn_sel_all = QPushButton("ជ្រើសទាំងអស់")
        btn_sel_all.setStyleSheet("background: #2a1f17; color: #f7efe7; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        btn_sel_all.clicked.connect(self.select_all)
        ep_hdr.addWidget(btn_sel_all)

        btn_desel_all = QPushButton("ដោះការជ្រើស")
        btn_desel_all.setStyleSheet("background: #2a1f17; color: #f7efe7; padding: 4px 8px; border-radius: 4px; font-size: 11px;")
        btn_desel_all.clicked.connect(self.deselect_all)
        ep_hdr.addWidget(btn_desel_all)

        btn_dl_sel = QPushButton("⬇ ទាញភាគដែលបានជ្រើស")
        btn_dl_sel.setStyleSheet("background: #ff6a2b; color: #fff; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px;")
        btn_dl_sel.clicked.connect(self.download_selected)
        ep_hdr.addWidget(btn_dl_sel)

        right_col.addLayout(ep_hdr)

        # Episode Grid Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #15100d; border: 1px solid #352a20; border-radius: 8px; }")

        scroll_content = QWidget()
        self.ep_grid = QGridLayout(scroll_content)
        self.ep_grid.setSpacing(6)

        self.ep_checkboxes = []
        episodes = detail.get("episodes", [])
        cols = 6
        for i, ep in enumerate(episodes):
            ep_num = ep.get("episode", i + 1)
            cb = QCheckBox(f"Ep {ep_num}")
            cb.setProperty("ep_data", ep)
            self.ep_checkboxes.append(cb)
            self.ep_grid.addWidget(cb, i // cols, i % cols)

        scroll.setWidget(scroll_content)
        right_col.addWidget(scroll)

        main_layout.addLayout(right_col, stretch=2)

        # Load HD Poster
        self.main_window.request_image(detail.get("poster", ""), QSize(240, 340), self.set_poster_pixmap)

        if auto_download and episodes:
            self.download_all()

    def set_poster_pixmap(self, pixmap: QPixmap):
        self.poster_lbl.setPixmap(pixmap)
        self.poster_lbl.setText("")

    def download_poster(self):
        p_url = self.detail.get("poster", "")
        if p_url:
            self.main_window.downloader.submit_poster(
                self.detail["id"], self.detail["title"], self.detail.get("title_km", ""), p_url
            )
            self.main_window.show_toast(f"បានបន្ថែម Poster '{self.detail['title']}' ទៅក្នុងបញ្ជីទាញយក!")

    def select_all(self):
        for cb in self.ep_checkboxes:
            cb.setChecked(True)

    def deselect_all(self):
        for cb in self.ep_checkboxes:
            cb.setChecked(False)

    def download_selected(self):
        selected = [cb.property("ep_data") for cb in self.ep_checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "ដំណឹង", "សូមជ្រើសរើសភាគដែលចង់ទាញយកជាមុនសិន!")
            return
        self.main_window.downloader.submit_batch(
            self.detail["id"], self.detail["title"], self.detail.get("title_km", ""),
            selected, self.detail.get("poster", "")
        )
        self.main_window.show_toast(f"បានបន្ថែម {len(selected)} ភាគ ទៅក្នុងបញ្ជីទាញយក!")
        self.accept()

    def download_all(self):
        episodes = self.detail.get("episodes", [])
        if not episodes:
            return
        self.main_window.downloader.submit_batch(
            self.detail["id"], self.detail["title"], self.detail.get("title_km", ""),
            episodes, self.detail.get("poster", "")
        )
        self.main_window.show_toast(f"បានបន្ថែម {len(episodes)} ភាគ ទៅក្នុងបញ្ជីទាញយក!")
        self.accept()

# ----------------- Settings Dialog -----------------
class SettingsDialog(QDialog):
    def __init__(self, main_window: 'MainWindow'):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("ការកំណត់កម្មវិធី (Settings)")
        self.resize(520, 240)
        self.setStyleSheet("""
            QDialog { background-color: #1c1511; color: #f7efe7; }
            QLabel { color: #f7efe7; font-size: 13px; font-weight: bold; }
            QLineEdit { background: #211812; border: 1px solid #352a20; color: #f7efe7; padding: 8px; border-radius: 6px; }
            QPushButton { background: #2a1f17; color: #f7efe7; border: 1px solid #352a20; padding: 8px 14px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { border-color: #ff6a2b; color: #ff6a2b; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Output Folder
        layout.addWidget(QLabel("ទីតាំងរក្សាទុកវីដេអូ & Poster (Download Directory):"))
        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit(self.main_window.cfg.get("output_dir", ""))
        self.dir_input.setReadOnly(True)
        btn_browse = QPushButton("ជ្រើសរើស...")
        btn_browse.clicked.connect(self.browse_folder)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(btn_browse)
        layout.addLayout(dir_row)

        # Auto Translate Checkbox
        self.cb_trans = QCheckBox("បកប្រែចំណងជើងជាភាសាខ្មែរស្វ័យប្រវត្ត (Auto-Translate to Khmer)")
        self.cb_trans.setChecked(self.main_window.cfg.get("auto_translate", True))
        self.cb_trans.setStyleSheet("color: #f7efe7; font-size: 13px;")
        layout.addWidget(self.cb_trans)

        layout.addStretch()

        # Save Button
        btn_save = QPushButton("រក្សាទុកការកំណត់")
        btn_save.setStyleSheet("background: #ff6a2b; color: #fff; font-size: 14px; padding: 10px; border-radius: 8px;")
        btn_save.clicked.connect(self.save)
        layout.addWidget(btn_save)

    def browse_folder(self):
        new_dir = QFileDialog.getExistingDirectory(self, "ជ្រើសរើស Folder រក្សាទុក", self.dir_input.text())
        if new_dir:
            self.dir_input.setText(new_dir)

    def save(self):
        self.main_window.cfg["output_dir"] = self.dir_input.text()
        self.main_window.cfg["auto_translate"] = self.cb_trans.isChecked()
        save_config(self.main_window.cfg)
        self.main_window.downloader.output_dir = self.dir_input.text()
        QMessageBox.information(self, "ជោគជ័យ", "បានរក្សាទុកការកំណត់ដោយជោគជ័យ!")
        self.accept()

# ----------------- MAIN WINDOW (Main Form) -----------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SYD 8MOVIE PRO - កម្មវិធីដោនឡូតរឿង & Poster (Native Main Form)")
        self.resize(1380, 920)
        self.setMinimumSize(1080, 720)

        self.cfg = load_config()
        self.downloader = DownloaderManager(output_dir=self.cfg.get("output_dir"))
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(8)

        self.current_cat = "1"
        self.current_page = 1
        self.is_search_mode = False
        self.current_query = ""
        self.loaded_dramas: List[Dict[str, Any]] = []
        self.image_callbacks: Dict[str, List[Any]] = {}

        self.img_signals = ImageSignals()
        self.img_signals.loaded.connect(self.on_image_loaded)

        self.init_ui()
        self.apply_dark_theme()

        # Start timer for download status update
        self.startTimer(1000)

        # Load initial category
        self.load_catalog("1", 1)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #15100d; }
            QWidget#CentralWidget { background-color: #15100d; }
            QFrame#DramaCard {
                background-color: #211812;
                border: 1px solid #352a20;
                border-radius: 16px;
            }
            QFrame#DramaCard:hover {
                border: 1px solid #ff6a2b;
                background-color: #261c15;
            }
            QLineEdit#OmniSearch {
                background-color: #211812;
                border: 1px solid #352a20;
                border-radius: 20px;
                padding: 10px 18px;
                color: #f7efe7;
                font-size: 15px;
            }
            QLineEdit#OmniSearch:focus {
                border: 1px solid #ff6a2b;
            }
            QPushButton.chip {
                background-color: #211812;
                color: #d3c3b4;
                border: 1px solid #352a20;
                border-radius: 16px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton.chip:hover {
                border-color: #ff6a2b;
                color: #ff6a2b;
            }
            QPushButton.chip[active="true"] {
                background-color: #ff6a2b;
                color: #ffffff;
                border: none;
            }
            QPushButton#PrimaryBtn {
                background: #ff6a2b;
                color: #ffffff;
                border-radius: 20px;
                padding: 10px 22px;
                font-size: 13.5px;
                font-weight: bold;
                border: none;
            }
            QPushButton#PrimaryBtn:hover {
                background: #ff854a;
            }
            QPushButton#TealBtn {
                background: #24ddcf;
                color: #08201c;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 13.5px;
                font-weight: bold;
                border: none;
            }
            QPushButton#TealBtn:hover {
                background: #39e6d9;
            }
            QPushButton#GhostBtn {
                background: #211812;
                color: #f7efe7;
                border: 1px solid #352a20;
                border-radius: 20px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#GhostBtn:hover {
                border-color: #ff6a2b;
                color: #ff6a2b;
            }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #15100d; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #352a20; border-radius: 5px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff6a2b;
            }
        """)

    def init_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 16, 24, 12)
        main_layout.setSpacing(12)

        # 1. Topbar Header
        topbar = QHBoxLayout()
        topbar.setSpacing(14)

        title_box = QVBoxLayout()
        app_title = QLabel("SYD 8MOVIE PRO")
        app_title.setStyleSheet("font-size: 22px; font-weight: 900; color: #ff6a2b;")
        app_sub = QLabel("កម្មវិធីដោនឡូតរឿង & POSTER 8MOVIE (Native Form 100%)")
        app_sub.setStyleSheet("font-size: 11.5px; font-weight: bold; color: #9c8a7b; text-transform: uppercase;")
        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)

        topbar.addLayout(title_box)
        topbar.addStretch()

        badge_live = QLabel("● Online 8movie.com")
        badge_live.setStyleSheet("color: #43d98a; font-weight: bold; font-size: 12px; background: rgba(67,217,138,0.12); padding: 5px 12px; border-radius: 12px; border: 1px solid rgba(67,217,138,0.3);")
        topbar.addWidget(badge_live)

        btn_batch_posters = QPushButton("🖼 ទាញយក Poster ទាំងអស់")
        btn_batch_posters.setObjectName("TealBtn")
        btn_batch_posters.clicked.connect(self.download_all_visible_posters)
        topbar.addWidget(btn_batch_posters)

        btn_folder = QPushButton("📂 បើក Folder")
        btn_folder.setObjectName("GhostBtn")
        btn_folder.clicked.connect(self.open_folder)
        topbar.addWidget(btn_folder)

        btn_settings = QPushButton("⚙️ កំណត់")
        btn_settings.setObjectName("GhostBtn")
        btn_settings.clicked.connect(self.open_settings)
        topbar.addWidget(btn_settings)

        main_layout.addLayout(topbar)

        # 2. Search Omni Bar
        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("OmniSearch")
        self.search_input.setPlaceholderText("ស្វែងរកចំណងជើងរឿងភាគ 8movie.com (វាយឈ្មោះ រួចចុច Enter)...")
        self.search_input.returnPressed.connect(lambda: self.do_search(1))

        btn_search = QPushButton("🔍 ស្វែងរក")
        btn_search.setObjectName("PrimaryBtn")
        btn_search.clicked.connect(lambda: self.do_search(1))

        search_row.addWidget(self.search_input)
        search_row.addWidget(btn_search)
        main_layout.addLayout(search_row)

        # 3. Category Chips Row
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        self.chip_buttons = {}

        for c in CATEGORIES:
            btn = QPushButton(c["name_km"])
            btn.setProperty("class", "chip")
            btn.setProperty("cat_id", c["id"])
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda ch, cid=c["id"]: self.on_category_click(cid))
            chips_row.addWidget(btn)
            self.chip_buttons[c["id"]] = btn

        chips_row.addStretch()
        main_layout.addLayout(chips_row)

        # 4. Status Bar & Section Header
        sec_header = QHBoxLayout()
        self.sec_title = QLabel("🎬 រឿងភាគឆ្លងភពបុរាណ")
        self.sec_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #f7efe7;")
        self.count_badge = QLabel("0 រឿង")
        self.count_badge.setStyleSheet("color: #9c8a7b; font-weight: bold; background: #211812; padding: 4px 10px; border-radius: 8px; border: 1px solid #352a20;")

        sec_header.addWidget(self.sec_title)
        sec_header.addWidget(self.count_badge)
        sec_header.addStretch()

        btn_refresh = QPushButton("🔄 ផ្ទុកឡើងវិញ")
        btn_refresh.setObjectName("GhostBtn")
        btn_refresh.clicked.connect(self.refresh_data)
        sec_header.addWidget(btn_refresh)
        main_layout.addLayout(sec_header)

        # 5. Cards Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_grid = QGridLayout(self.cards_container)
        self.cards_grid.setSpacing(18)
        self.cards_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 6. Load More Bottom Button
        self.load_more_btn = QPushButton("➕ បង្ហាញរឿង និង Poster បន្ថែមទៀត (ទំព័របន្ទាប់)")
        self.load_more_btn.setObjectName("PrimaryBtn")
        self.load_more_btn.setFixedHeight(46)
        self.load_more_btn.clicked.connect(self.load_next_page)
        main_layout.addWidget(self.load_more_btn)

        # 7. Bottom Download Status Bar
        dl_bar = QFrame()
        dl_bar.setStyleSheet("background: #211812; border: 1px solid #352a20; border-radius: 12px; padding: 6px 14px;")
        dl_bar_layout = QHBoxLayout(dl_bar)
        dl_bar_layout.setContentsMargins(8, 4, 8, 4)

        self.dl_status_lbl = QLabel("ការទាញយក: ទំនេរ (Idle)")
        self.dl_status_lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #f7efe7;")
        self.dl_progress = QProgressBar()
        self.dl_progress.setFixedHeight(12)
        self.dl_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #352a20; border-radius: 6px; text-align: center; background: #15100d; }
            QProgressBar::chunk { background: #ff6a2b; border-radius: 6px; }
        """)
        self.dl_progress.setValue(0)
        self.dl_progress.setFixedWidth(220)

        self.dl_speed_lbl = QLabel("0.0 MB/s")
        self.dl_speed_lbl.setStyleSheet("color: #24ddcf; font-weight: bold; font-size: 12px;")

        btn_clear_dl = QPushButton("🧹 សម្អាត")
        btn_clear_dl.setObjectName("GhostBtn")
        btn_clear_dl.clicked.connect(self.downloader.clear_completed)

        dl_bar_layout.addWidget(self.dl_status_lbl)
        dl_bar_layout.addStretch()
        dl_bar_layout.addWidget(self.dl_progress)
        dl_bar_layout.addWidget(self.dl_speed_lbl)
        dl_bar_layout.addWidget(btn_clear_dl)
        main_layout.addWidget(dl_bar)

    # ----------------- Image Loader -----------------
    def request_image(self, url: str, size: QSize, callback):
        if not url:
            return
        if url in self.image_callbacks:
            self.image_callbacks[url].append(callback)
            return
        self.image_callbacks[url] = [callback]
        worker = ImageLoadWorker(url, size, self.img_signals)
        self.thread_pool.start(worker)

    def on_image_loaded(self, url: str, pixmap: QPixmap):
        callbacks = self.image_callbacks.pop(url, [])
        for cb in callbacks:
            try:
                cb(pixmap)
            except Exception:
                pass

    # ----------------- Category & Search Logic -----------------
    def on_category_click(self, cat_id: str):
        self.is_search_mode = False
        self.search_input.setText("")
        self.load_catalog(cat_id, 1)

    def update_chips_active(self):
        for cid, btn in self.chip_buttons.items():
            btn.setProperty("active", "true" if (cid == self.current_cat and not self.is_search_mode) else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def load_catalog(self, cat_id: str, page: int = 1):
        self.current_cat = cat_id
        self.current_page = page
        self.is_search_mode = False
        self.update_chips_active()

        cat_obj = next((c for c in CATEGORIES if c["id"] == cat_id), None)
        cat_name = cat_obj["name_km"] if cat_obj else "🎬 រឿងភាគ 8Movie"
        self.sec_title.setText(f"{cat_name} (ទំព័រ {page})")

        if page == 1:
            self.clear_cards()
            self.loaded_dramas = []
            self.count_badge.setText("⏳ កំពុងទាញទិន្នន័យ...")

        self.worker = CatalogWorker(cat_id, page, self.cfg.get("auto_translate", True))
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.error.connect(lambda err: QMessageBox.warning(self, "កំហុស", f"មិនអាចទាញទិន្នន័យបានទេ: {err}"))
        self.worker.start()

    def do_search(self, page: int = 1):
        q = self.search_input.text().strip()
        if not q:
            return self.load_catalog(self.current_cat, 1)

        self.is_search_mode = True
        self.current_query = q
        self.current_page = page
        self.update_chips_active()

        self.sec_title.setText(f"🔍 លទ្ធផលស្វែងរក: '{q}' (ទំព័រ {page})")
        if page == 1:
            self.clear_cards()
            self.loaded_dramas = []
            self.count_badge.setText("⏳ កំពុងស្វែងរក...")

        self.worker = SearchWorker(q, page, self.cfg.get("auto_translate", True))
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.error.connect(lambda err: QMessageBox.warning(self, "កំហុស", f"ស្វែងរកបរាជ័យ: {err}"))
        self.worker.start()

    def load_next_page(self):
        if self.is_search_mode:
            self.do_search(self.current_page + 1)
        else:
            self.load_catalog(self.current_cat, self.current_page + 1)

    def refresh_data(self):
        if self.is_search_mode:
            self.do_search(self.current_page)
        else:
            self.load_catalog(self.current_cat, self.current_page)

    def on_data_loaded(self, items: List[Dict[str, Any]], page: int):
        if page == 1:
            self.loaded_dramas = items
            self.clear_cards()
        else:
            existing_ids = {d["id"] for d in self.loaded_dramas}
            for it in items:
                if it["id"] not in existing_ids:
                    self.loaded_dramas.append(it)

        self.render_cards(self.loaded_dramas)
        self.count_badge.setText(f"{len(self.loaded_dramas)} រឿង")

        if len(items) < 15:
            self.load_more_btn.setText("អស់រឿងភាគសម្រាប់បង្ហាញហើយ")
            self.load_more_btn.setEnabled(False)
        else:
            self.load_more_btn.setText(f"➕ បង្ហាញរឿង និង Poster បន្ថែមទៀត (ទំព័រ {self.current_page + 1})")
            self.load_more_btn.setEnabled(True)

    def clear_cards(self):
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def render_cards(self, dramas: List[Dict[str, Any]]):
        cols = max(4, self.width() // 230)
        # Re-layout cards
        self.clear_cards()
        for idx, item in enumerate(dramas):
            card = DramaCardWidget(item, self)
            self.cards_grid.addWidget(card, idx // cols, idx % cols)

    def open_drama_detail(self, drama_id: str, auto_download: bool = False):
        self.show_toast("⏳ កំពុងទាញយកព័ត៌មានលម្អិត និងបញ្ជីភាគ...")
        self.det_worker = DetailWorker(drama_id)
        self.det_worker.finished.connect(lambda detail: self.show_detail_dialog(detail, auto_download))
        self.det_worker.error.connect(lambda err: QMessageBox.warning(self, "កំហុស", f"មិនអាចទាញព័ត៌មានរឿងបានទេ: {err}"))
        self.det_worker.start()

    def show_detail_dialog(self, detail: Dict[str, Any], auto_download: bool):
        dlg = DramaDetailDialog(detail, self, auto_download=auto_download)
        dlg.exec()

    def download_all_visible_posters(self):
        if not self.loaded_dramas:
            QMessageBox.information(self, "ដំណឹង", "មិនទាន់មាន Poster សម្រាប់ទាញយកឡើយ!")
            return
        count = 0
        for d in self.loaded_dramas:
            p_url = d.get("poster", "")
            if p_url:
                self.downloader.submit_poster(d["id"], d["title"], d.get("title_km", ""), p_url)
                count += 1
        self.show_toast(f"បានបន្ថែម Poster ទាំងអស់ចំនួន {count} រឿង ទៅក្នុងបញ្ជីទាញយក!")

    def open_folder(self):
        self.downloader.open_folder()

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def show_toast(self, msg: str):
        self.statusBar().showMessage(msg, 5000)

    def timerEvent(self, a0):
        # Update download status bar
        st = self.downloader.get_status()
        active = st.get("active_count", 0)
        queued = st.get("queued_count", 0)
        completed = st.get("completed_count", 0)

        tasks = st.get("tasks", [])
        active_task = next((t for t in tasks if t["status"] == "downloading"), None)

        if active_task:
            ep_str = f"ភាគ {active_task['ep_num']}" if active_task["task_type"] == "episode" else "🖼 Poster"
            self.dl_status_lbl.setText(f"កំពុងទាញយក: {active_task['drama_title']} ({ep_str}) - នៅសល់ {active+queued} កិច្ចការ")
            self.dl_progress.setValue(int(active_task.get("progress", 0)))
            self.dl_speed_lbl.setText(active_task.get("speed", "0 MB/s"))
        elif queued > 0:
            self.dl_status_lbl.setText(f"រង់ចាំក្នុង Queue ({queued} កិច្ចការ)...")
            self.dl_progress.setValue(0)
            self.dl_speed_lbl.setText("")
        else:
            self.dl_status_lbl.setText(f"ការទាញយក: ទំនេរ (រួចរាល់ {completed} កិច្ចការ)")
            self.dl_progress.setValue(100 if completed > 0 else 0)
            self.dl_speed_lbl.setText("")

    def resizeEvent(self, a0):
        super().resizeEvent(a0)
        if self.loaded_dramas:
            # Re-arrange columns on resize
            cols = max(4, self.width() // 230)
            # Re-assign grid positions without re-creating
            for idx in range(self.cards_grid.count()):
                item = self.cards_grid.itemAt(idx)
                if item and item.widget():
                    self.cards_grid.addWidget(item.widget(), idx // cols, idx % cols)

def launch_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_app()
'''

# ==========================================
# main.py (Single Entry Point)
# ==========================================
main_code = r'''# -*- coding: utf-8 -*-
"""
SYD 8MOVIE PRO - Pure Native Windows Application
------------------------------------------------
Standalone native Main Form desktop GUI.
No web server, no browser, zero connection refused errors.
"""

import os
import sys

# Ensure local app directory is in sys.path
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from app.gui import launch_app

if __name__ == "__main__":
    launch_app()
'''

# ==========================================
# run.bat (Clean Launcher)
# ==========================================
run_bat = r'''@echo off
chcp 65001 >nul
title SYD 8MOVIE PRO
cd /d "%~dp0"

echo [SYD 8Movie] Starting Native Main Form Application...
start "" pythonw main.py
exit
'''

# ==========================================
# start_downloader.bat
# ==========================================
start_bat = r'''@echo off
chcp 65001 >nul
cd /d "%~dp0"
python main.py
'''

with open(os.path.join(TARGET_DIR, 'app', 'gui.py'), 'w', encoding='utf-8') as f:
    f.write(gui_code)
print("Written: app/gui.py")

with open(os.path.join(TARGET_DIR, 'main.py'), 'w', encoding='utf-8') as f:
    f.write(main_code)
print("Written: main.py")

with open(os.path.join(TARGET_DIR, 'run.bat'), 'w', encoding='utf-8') as f:
    f.write(run_bat)
print("Written: run.bat")

with open(os.path.join(TARGET_DIR, 'start_downloader.bat'), 'w', encoding='utf-8') as f:
    f.write(start_bat)
print("Written: start_downloader.bat")
