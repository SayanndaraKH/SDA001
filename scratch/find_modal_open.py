with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'userRegisterModal' in line and ('.show' in line or 'style.display' in line or 'openUserRegisterModal' in line):
            print(f"Line {i}: {line.strip()[:100]}")
