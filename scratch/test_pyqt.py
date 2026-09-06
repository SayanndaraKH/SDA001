import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

app = QApplication(sys.argv)
win = QMainWindow()
win.setWindowTitle("Test Native GUI")
win.resize(400, 200)

lbl = QLabel("Native PyQt6 GUI Test OK", win)
lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
win.setCentralWidget(lbl)
print("PyQt6 basic window created successfully.")
app.quit()
