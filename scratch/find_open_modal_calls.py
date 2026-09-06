with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'openUserRegisterModal' in line:
            print(f"Line {i}: {line.strip()[:100]}")
