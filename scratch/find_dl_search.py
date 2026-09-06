with open('app/server.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if '/dl/search' in line:
            print(f"Line {i}: {line.strip()}")
