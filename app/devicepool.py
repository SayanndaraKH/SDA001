# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\devicepool.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-08-31 16:51:05 UTC (1788195065)

# ***<module>: Failure: Compilation Error
"""设备指纹池: 本地随机生成自洽的红果设备身份, 供多设备轮换降低风控。\n\n背景(实测): 红果 search / multi_video_model 对游客开放, 且不校验 device_id 是否注册\n——随机 device_id/iid + 签名即可 code=0。故\"多 token 轮换\"实为\"设备指纹池轮换\",\n纯本地生成, 无需账号/注册/token。\n\n一个设备身份 = {query: 覆盖 base_query 的字段, user_agent: 与机型/系统自洽的 UA}。\ndevice_id/iid/cdid 随机; 机型/系统/分辨率/UA/build 取自真实机型档案并保持一致。\n\n环境变量:\n  DEVICE_POOL_SIZE : >0 则首次启用时生成该数量设备并落盘; 0/未设 = 不启用(沿用 config.json 单设备)\n  DEVICE_POOL      : 设备池文件路径(默认 devices.json); 存在则直接加载\n"""
import json
import os
import random
import threading
import uuid
HERE = os.path.dirname(os.path.abspath(__file__))
POOL_PATH = os.environ.get('DEVICE_POOL', os.path.join(HERE, 'devices.json'))
PROFILES = [
    {'brand': 'Redmi', 'model': '22041211AC', 'build': 'TKQ1.220807.001', 'res': '1080*2400', 'os': '13', 'api': '33'},
    {'brand': 'Redmi', 'model': '23021RAA2Y', 'build': 'UKQ1.230804.001', 'res': '1080*2400', 'os': '14', 'api': '34'},
    {'brand': 'HUAWEI', 'model': 'ELS-AN00', 'build': 'HUAWEIELS-AN00', 'res': '1080*2340', 'os': '10', 'api': '29'},
    {'brand': 'OPPO', 'model': 'PEHM00', 'build': 'TP1A.220905.001', 'res': '1080*2412', 'os': '13', 'api': '33'},
    {'brand': 'vivo', 'model': 'V2218A', 'build': 'TP1A.220624.014', 'res': '1080*2400', 'os': '13', 'api': '33'},
    {'brand': 'samsung', 'model': 'SM-G9810', 'build': 'SP1A.210812.016', 'res': '1080*2400', 'os': '12', 'api': '31'},
    {'brand': 'OnePlus', 'model': 'PHB110', 'build': 'UKQ1.230924.001', 'res': '1240*2772', 'os': '14', 'api': '34'},
    {'brand': 'HONOR', 'model': 'FNE-AN00', 'build': 'HONORFNE-AN00', 'res': '1080*2412', 'os': '13', 'api': '33'}
]
APP_VC = '72232'
TTOK = '3.12.13.20'
def _digits(n):
    # ***<module>._digits: Failure detected at line number 7 and instruction offset 4: Different bytecode
    return str(random.randint(10 ** (n - 1), 10 ** n - 1))
def gen_device(template):
    """基于真实机型档案 + template(config.json 的 base_query)生成一个自洽设备身份。"""
    # ***<module>.gen_device: Failure detected at line number 10 and instruction offset 2: Different bytecode
    p = random.choice(PROFILES)
    did = _digits(len(str(template.get('device_id') or '')) or 16)
    iid = _digits(len(str(template.get('iid') or '')) or 16)
    ua = f"com.phoenix.read/{APP_VC} (Linux; U; Android {p['os']}; zh_CN; {p['model']}; Build/{p['build']};tt-ok/{TTOK})"
    query = {'device_id': did, 'iid': iid, 'cdid': str(uuid.uuid4()), 'device_brand': p['brand'], 'device_type': p['model'], 'resolution': p['res'], 'os_version': p['os'], 'os_api': p['api'], 'rom_version': f"{p['build']} release-keys"}
    return {'query': query, 'user_agent': ua}
class DevicePool:
    """两种模式:\n    - session=True (装机版 app): 进程启动时随机固定一台设备, 整个会话都用它; rotate() 在风控时\n      换到下一台(故障转移)。这样每次开 app 随机换设备, 全体用户把负载摊到整个设备池, 单台被风控\n      也只影响本次会话, 重开即换。\n    - session=False (爬虫): 线程内粘滞 + 线程间轮询, 各线程天然分散; rotate() 每次搜索换下一台。"""
    def __init__(self, devices, session=False):
        # ***<module>.DevicePool.__init__: Failure detected at line number 20 and instruction offset 12: Different bytecode
        self.devices = devices
        self._i = random.randrange(len(devices)) if devices else 0
        self._lock = threading.RLock()
        self._local = threading.local()
        self._session = session
        self._pin = random.choice(devices) if session and devices else None
    def _advance(self):
        with self._lock:
            d = self.devices[self._i % len(self.devices)]
            self._i += 1
            return d
    def current(self):
        if self._session:
            return self._pin
        else:
            d = getattr(self._local, 'dev', None)
            if d is None:
                d = self._advance()
                self._local.dev = d
            return d
    def rotate(self):
        if self._session:
            with self._lock:
                self._pin = self._advance()
            return self._pin
        else:
            self._local.dev = self._advance()
            return self._local.dev
    def __len__(self):
        return len(self.devices)
def load_pool(template):
    """加载/生成设备池。返回 DevicePool 或 None(未启用 → 保持原单设备行为)。"""
    if os.path.exists(POOL_PATH):
        try:
            devs = json.load(open(POOL_PATH, encoding='utf-8'))
            if devs:
                session = not bool(os.environ.get('DEVICE_POOL'))
                return DevicePool(devs, session=session)
        except Exception as e:
            print('[devicepool] 加载失败, 忽略:', e)
    size = int(os.environ.get('DEVICE_POOL_SIZE', '0') or '0')
    if size > 0:
        devs = [gen_device(template) for _ in range(size)]
        try:
            json.dump(devs, open(POOL_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print(f'[devicepool] 已生成 {size} 台设备 → {POOL_PATH}')
        except Exception as e:
            print('[devicepool] 落盘失败(仅内存):', e)
        return DevicePool(devs)
    return None