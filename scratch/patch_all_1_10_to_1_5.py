with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

replacements = [
    ("ភាគ 1-10", "ភាគ 1-5"),
    ("Free 1-10", "Free 1-5"),
    ("1-10 ភាគ", "1-5 ភាគ"),
    ("1-10 ឥតគិតថ្លៃ", "1-5 ឥតគិតថ្លៃ"),
    ("Free Tier 1-10", "Free Tier 1-5"),
    ("ភាគ 1 ដល់ 10", "ភាគ 1 ដល់ 5"),
    ("1 ដល់ 10", "1 ដល់ 5"),
    ("1-10)", "1-5)"),
    ("1-10 ·", "1-5 ·"),
    ("1-10 ប៉ុណ្ណោះ", "1-5 ប៉ុណ្ណោះ"),
]

for old, new in replacements:
    text = text.replace(old, new)

with open('app/web/downloader.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced all 1-10 with 1-5 in downloader.html successfully!")
