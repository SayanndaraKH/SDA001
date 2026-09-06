import os

TARGET_DIR = r"C:\Users\Administrator\Desktop\SYD-8Move"

# 1. requirements.txt
reqs = '''PyQt6>=6.6.0
requests>=2.31.0
pillow>=10.0.0
urllib3>=2.0.0
'''
with open(os.path.join(TARGET_DIR, 'requirements.txt'), 'w', encoding='utf-8') as f:
    f.write(reqs)

# 2. README.md
readme = '''# SYD 8MOVIE PRO (កម្មវិធីដោនឡូតរឿង & POSTER 8MOVIE - NATIVE MAIN FORM)

កម្មវិធីកុំព្យូទ័រ **Native Desktop Main Form** 100% (មិនប្រើប្រាស់ Web Browser / Web App ឬ Web Server ឡើយ) សម្រាប់ទាញយក Poster និងវីដេអូរឿងភាគ Full HD ពីគេហទំព័រ **https://8movie.com** (八影短劇網)។

---

## របៀបដំណើរការ (How to Run)
1. ចូលទៅកាន់ Folder: `C:\\Users\\Administrator\\Desktop\\SYD-8Move`
2. ចុចពីរដង (Double-click) លើ:
   - **`run.bat`** (បើក App ភ្លាមៗ គ្មានផ្ទាំងខ្មៅ CMD)
   - ឬ **`start_downloader.bat`** (បើកជាមួយ Console)
3. កម្មវិធី Main Form នឹងបើកបង្ហាញលើអេក្រង់ភ្លាមៗ ក្នុងរយៈពេលមិនដល់ 1 វិនាទី (គ្មានបញ្ហា ERR_CONNECTION_REFUSED ឡើយ)!

---

## លក្ខណៈពិសេសចម្បង (Key Features)

1. **Native Main Form 100% (គ្មាន Web App គ្មាន Browser)**:
   - សាងសង់ឡើងដោយប្រើប្រាស់ **PyQt6 GUI Framework**
   - ដំណើរការផ្ទាល់ជាកម្មវិធី Desktop Standalone មួយគត់
   - គ្មាន Server Local, គ្មាន Port Conflict, គ្មាន Connection Refused

2. **បង្ហាញ Poster គ្រប់ ១០០% (Async Disk Cached Image Loader)**:
   - ទាញយក Poster តាមរយៈ Background Threads មិនធ្វើឱ្យគាំង Window (No Freeze)
   - រក្សាទុករូបភាពក្នុង Disk Cache ធ្វើឱ្យការបើកមើលលើកក្រោយលឿនដូចផ្លេកបន្ទោរ
   - បង្ហាញរូបភាព Poster គ្រប់កាតទាំងអស់ដោយគ្មានបាត់បង់

3. **ប៊ូតុង "🖼 ទាញយក Poster ទាំងអស់" (1-Click Batch Download)**:
   - ចុចតែ ១ ដង អាចទាញយក Poster HD ទាំងអស់ដែលមានលើអេក្រង់ (៣០, ៦០, ៩០+ រឿង)
   - រក្សាទុកក្នុង: `C:\\Users\\Administrator\\Videos\\SYD-8Movie\\Posters\\`

4. **ប៊ូតុង "➕ បង្ហាញរឿង និង Poster បន្ថែមទៀត (ទំព័របន្ទាប់)"**:
   - ចុចដើម្បីទាញយករឿងភាគទំព័រទី 2, 3, 4, 5... មកបង្ហាញបន្តបន្ទាប់គ្នា

5. **ការទាញយកវីដេអូរឿងភាគ Full HD 1080p**:
   - ប្រើប្រាស់ `ffmpeg` បច្ចេកវិទ្យា Stream Copy លឿនរហ័ស និងរក្សាគុណភាពច្បាស់ 100%
   - អាចទាញយកគ្រប់ភាគ (Download All) ឬរើសភាគដែលចង់បាន (Download Selected)

6. **ការបកប្រែជាភាសាខ្មែរស្វ័យប្រវត្ត (Khmer Translation)**:
   - បកប្រែចំណងជើងរឿងចិនទៅជាភាសាខ្មែរភ្លាមៗនៅលើកាតនីមួយៗ
'''

with open(os.path.join(TARGET_DIR, 'README.md'), 'w', encoding='utf-8') as f:
    f.write(readme)

print("Updated requirements.txt and README.md.")
