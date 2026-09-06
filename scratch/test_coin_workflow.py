# -*- coding: utf-8 -*-
import sys
from py_mini_racer import MiniRacer

sys.stdout.reconfigure(encoding='utf-8')

ctx = MiniRacer()
s0 = open('app/web/downloader.html', 'r', encoding='utf-8').read()
s0 = s0[s0.find('<script>') + 8:s0.find('</script>')]

ctx.eval('''
window = { confirm: () => true, matchMedia: () => ({ matches: false, addEventListener: () => {} }), addEventListener: () => {} };
matchMedia = window.matchMedia;
setInterval = () => 1;
setTimeout = () => 1;
clearInterval = () => {};
clearTimeout = () => {};
URLSearchParams = class { get() { return null; } has() { return false; } };
document = { 
  querySelector: () => ({ style: {}, classList: { toggle: () => {} }, addEventListener: () => {} }),
  querySelectorAll: () => [],
  documentElement: { setAttribute: () => {}, dataset: {} },
  addEventListener: () => {}
};
localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
sessionStorage = localStorage;
location = { search: "" };
navigator = { clipboard: { writeText: () => Promise.resolve() } };
fetch = () => Promise.resolve({ json: () => Promise.resolve({ ok: true }) });
''')

ctx.eval(s0)

print("openCoinModal:", ctx.eval("typeof window.openCoinModal"))
print("closeCoinModal:", ctx.eval("typeof window.closeCoinModal"))
print("selectCoinPackage:", ctx.eval("typeof window.selectCoinPackage"))
print("onCoinReqInputChange:", ctx.eval("typeof window.onCoinReqInputChange"))
print("submitCoinRequest:", ctx.eval("typeof window.submitCoinRequest"))
print("loadMyCoinRequests:", ctx.eval("typeof window.loadMyCoinRequests"))
print("buyCurrentDramaWithCoins:", ctx.eval("typeof window.buyCurrentDramaWithCoins"))
print("buyDramaWithCoins:", ctx.eval("typeof window.buyDramaWithCoins"))
print("updateDramaDetailCoinUI:", ctx.eval("typeof updateDramaDetailCoinUI"))
