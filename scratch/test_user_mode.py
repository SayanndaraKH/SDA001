# -*- coding: utf-8 -*-
import re
from py_mini_racer import MiniRacer

with open('app/web/downloader.html', 'r', encoding='utf-8') as f:
    content = f.read()

scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', content, re.DOTALL)

mock_env = '''
var window = this;
window.addEventListener = function(e, fn){};
var localStorage = {
    getItem: function(k){ return null; },
    setItem: function(k, v){},
    removeItem: function(k){}
};
var sessionStorage = localStorage;
var navigator = { userAgent: 'Chrome' };
var location = { search: '', href: 'http://127.0.0.1:8000/', origin: 'http://127.0.0.1:8000' };
var URLSearchParams = function(s){
    return {
        get: function(k){ return null; },
        has: function(k){ return false; }
    };
};
var matchMedia = function(q){ return { matches: false }; };
function makeEl(){
    return {
        style: {},
        setAttribute: function(){},
        getAttribute: function(){ return null; },
        appendChild: function(){},
        classList: { add: function(){}, remove: function(){}, contains: function(){ return false; }, toggle: function(){} },
        addEventListener: function(){},
        querySelectorAll: function(){ return []; }
    };
}
var document = {
    getElementById: function(id){ return makeEl(); },
    querySelector: function(sel){ return makeEl(); },
    querySelectorAll: function(sel){ return []; },
    addEventListener: function(e, fn){},
    documentElement: makeEl(),
    createElement: function(t){ return makeEl(); },
    body: makeEl()
};
function setTimeout(fn, ms){ return 1; }
function clearTimeout(id){}
function setInterval(fn, ms){ return 1; }
function clearInterval(id){}
function fetch(url, opt){ return Promise.resolve({ json: function(){ return Promise.resolve({}); } }); }
'''

ctx = MiniRacer()
ctx.eval(mock_env)
ctx.eval(scripts[0])

# Test toggleUserTestMode
ctx.eval('toggleUserTestMode();')
is_mode = ctx.eval('window.isUserTestMode')
print('Entered test mode:', is_mode)
coins = ctx.eval('window.userAccess.coins')
print('Simulated coins:', coins)
role = ctx.eval('window.userAccess.role')
print('Simulated role:', role)
assert is_mode is True
assert coins == 15
assert role == 'user'

# Test profile change to user_zero
ctx.eval("changeUserTestProfile('user_zero');")
print('User zero coins:', ctx.eval('window.userAccess.coins'))
assert ctx.eval('window.userAccess.coins') == 0

# Test profile change to user_vip
ctx.eval("changeUserTestProfile('user_vip');")
print('User VIP status is_vip:', ctx.eval('window.userAccess.is_vip'))
assert ctx.eval('window.userAccess.is_vip') is True

# Test exitUserTestMode
ctx.eval('exitUserTestMode();')
print('Exited test mode, isUserTestMode:', ctx.eval('window.isUserTestMode'))
assert ctx.eval('window.isUserTestMode') is False

print('\n>>> ALL USER TEST MODE CHECKS PASSED! <<<')
