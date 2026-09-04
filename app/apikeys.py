# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\apikeys.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-07-28 06:30:27 UTC (1785220227)

"""API 密钥存储: 文件持久化(apikeys.json), 支持生成/吊销/删除/校验, 运行时即时生效。"""
import json
import os
import secrets
import threading
import time
HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.environ.get('APIKEYS_PATH', os.path.join(HERE, 'apikeys.json'))
class KeyStore:
    def __init__(self, path=STORE_PATH):
        # ***<module>.KeyStore.__init__: Failure: Different control flow
        self.path = path
        self.lock = threading.Lock()
        self._load()
        env = [k.strip() for k in (os.environ.get('API_KEYS') or '').split(',') if k.strip()]
        if not self.data['keys'] and env:
            for k in env:
                self.data['keys'].append(self._mk(k, '迁移自API_KEYS'))
            self._save()
    def _load(self):
        try:
            self.data = json.load(open(self.path, encoding='utf-8'))
            if 'keys' not in self.data:
                self.data = {'keys': []}
        except Exception:
            self.data = {'keys': []}
    def _save(self):
        tmp = self.path + '.tmp'
        json.dump(self.data, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)
    @staticmethod
    def _mk(key, note):
        return {'key': key, 'note': note, 'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'enabled': True, 'last_used': ''}
    def generate(self, note=''):
        with self.lock:
            key = 'hg_' + secrets.token_hex(16)
            self.data['keys'].append(self._mk(key, note or ''))
            self._save()
            return key
    def revoke(self, key, enabled=False):
        with self.lock:
            found = False
            for k in self.data['keys']:
                if k['key'] == key:
                    k['enabled'] = bool(enabled)
                    found = True
            if found:
                self._save()
            return found
    def delete(self, key):
        with self.lock:
            n = len(self.data['keys'])
            self.data['keys'] = [k for k in self.data['keys'] if k['key'] != key]
            if len(self.data['keys']) != n:
                self._save()
                return True
            else:
                return False
    def is_valid(self, key):
        if not key:
            return False
        else:
            with self.lock:
                for k in self.data['keys']:
                    if k['key'] == key and k.get('enabled'):
                        k['last_used'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        return True
                return False
    def list(self):
        with self.lock:
            return [dict(k) for k in self.data['keys']]
    def count_enabled(self):
        with self.lock:
            return sum((1 for k in self.data['keys'] if k.get('enabled')))