import sys
from py_mini_racer import MiniRacer

ctx = MiniRacer()
with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    text = f.read()

s0 = text[text.find('<script>') + len('<script>'):text.find('</script>')]
lines = s0.splitlines()

# Binary search or line-by-line test
for i in range(len(lines) - 350, len(lines)):
    chunk = "\n".join(lines[:i])
    try:
        ctx.eval(chunk)
    except Exception as e:
        err = str(e)
        if "SyntaxError: Unexpected end of input" in err:
            continue
        print(f"Error at line {i}: {err}")
        print("Line content:", lines[i-1])
        break
