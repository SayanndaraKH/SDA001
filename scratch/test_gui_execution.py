import sys
import os

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"
sys.path.insert(0, TARGET_DIR)

from PyQt6.QtWidgets import QApplication
from app.gui import MainWindow

app = QApplication([])
win = MainWindow()
print("MainWindow initialized successfully!")
print("Window title:", win.windowTitle())
print("Downloader output dir:", win.downloader.output_dir)
win.close()
app.quit()
print("Test completed successfully.")
