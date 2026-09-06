import sys
from py_mini_racer import MiniRacer

mr = MiniRacer()
mr.eval('function checkJs(src) { try { new Function(src); return "OK"; } catch(e) { return String(e); } }')

for idx in (0, 1):
    with open(f'scratch/script_{idx}.js', 'r', encoding='utf-8') as f:
        src = f.read()
    res = mr.call('checkJs', src)
    print(f'Script {idx} syntax status: {res}')
