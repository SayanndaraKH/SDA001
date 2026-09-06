import os

TARGET = r"C:\Users\Administrator\Desktop\SYD-8Move\app\gui.py"

with open(TARGET, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace font initialization in launch_app
old_font = 'font = QFont("Segoe UI", 10)'
new_font = '''font = QFont()
    font.setFamilies(["Kantumruy Pro", "Khmer OS Battambang", "Battambang", "Segoe UI", "sans-serif"])
    font.setPointSize(10)'''

if old_font in text:
    text = text.replace(old_font, new_font)
    with open(TARGET, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated font families in gui.py successfully.")
else:
    print("old_font not found")
