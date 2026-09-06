# -*- coding: utf-8 -*-
import re
import sys

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', content, re.DOTALL)
for s_idx, js in enumerate(scripts):
    print(f"Checking Script {s_idx}...")
    stack = []
    lines = js.splitlines()
    in_str = None
    in_block_comment = False
    
    for l_num, line in enumerate(lines, 1):
        i = 0
        while i < len(line):
            ch = line[i]
            if in_block_comment:
                if line[i:i+2] == '*/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue
            if in_str:
                if ch == '\\':
                    i += 2
                    continue
                if in_str == '`':
                    if line[i:i+2] == '${':
                        stack.append(('${', l_num, i))
                        i += 2
                        in_str = None
                        continue
                if ch == in_str:
                    in_str = None
                i += 1
                continue
            
            if line[i:i+2] == '//':
                break
            if line[i:i+2] == '/*':
                in_block_comment = True
                i += 2
                continue
            if ch in ('"', "'", '`'):
                in_str = ch
                i += 1
                continue
                
            if ch in ('{', '(', '['):
                stack.append((ch, l_num, i))
            elif ch in ('}', ')', ']'):
                expected = {'}': '{', ')': '(', ']': '['}.get(ch)
                if not stack:
                    print(f"  [ERROR] Unmatched closing {ch} at line {l_num}:{i}")
                else:
                    top, t_line, t_col = stack.pop()
                    if top == '${' and ch == '}':
                        in_str = '`'
                    elif top != expected:
                        print(f"  [MISMATCH] Found {ch} at line {l_num}:{i}, expected closing for {top} from line {t_line}:{t_col}")
            i += 1

    if stack:
        print(f"  [UNCLOSED] {len(stack)} unclosed tokens remaining in Script {s_idx}:")
        for t, l, c in stack[-10:]:
            print(f"    Token {t} opened at line {l}:{c}")
    else:
        print(f"  Script {s_idx} is BALANCED!")
