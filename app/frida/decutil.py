# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\frida\\decutil.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-08-15 07:19:43 UTC (1786778383)

"""纯文件/纯算法解密工具(从 Mac 逆向成果整合): senc base_iv 读取 + AES-128-CTR 全解。\n不依赖 app/frida/keybox。配合 unwrap_spade 实现纯离线解密。"""
import os
import re
import sys
import shutil
import subprocess
from Crypto.Cipher import AES
from Crypto.Util import Counter as CTRCounter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle
def senc_iv8(ct_path):
    """密文 mp4 的 senc 盒首样本 IV 高8字节 = base_iv 候选(各 track 不同, 全作候选)。"""
    d = open(ct_path, 'rb').read()
    ivs = []
    for m in re.finditer(b'senc', d):
        o = m.start() + 8 + 4
        if o + 8 > len(d):
            continue
        else:
            h = d[o:o + 8].hex()
            if h not in ivs:
                ivs.append(h)
    return ivs
def tenc_kid(ct_path):
    """密文 tenc 盒 default_KID(核对用)。"""
    d = open(ct_path, 'rb').read()
    m = re.search(b'tenc', d)
    if not m:
        return
    else:
        o = m.start() + 8
        return d[o + 4:o + 20].hex() if o + 20 <= len(d) else None
def decrypt_full(ct_path, key_hex, base_iv64, out_path):
    K = bytes.fromhex(key_hex)
    biv = int(base_iv64, 16)
    data, sizes, offs = oracle.parse_video_samples(ct_path)
    data = bytearray(data)
    ok = 0
    for idx, (co, sz) in enumerate(zip(offs, sizes)):
        iv = biv + idx << 64
        pt = AES.new(K, AES.MODE_CTR, counter=CTRCounter.new(128, initial_value=iv)).decrypt(bytes(data[co:co + sz]))
        if oracle._nal_ok(pt, sz):
            ok += 1
        data[co:co + sz] = pt
    open(out_path, 'wb').write(data)
    print(f'  解密完成: {out_path}  (视频样本 NAL合法 {ok}/{len(sizes)})')
    return (ok, len(sizes))
def _trak_senc_iv8(d, lo, hi):
    """在 trak 字节范围 [lo,hi) 内找 senc 盒, 返回首样本 base_iv 高8字节hex(无则 None)。"""
    for m in re.finditer(b'senc', d):
        if lo <= m.start() < hi:
                o = m.start() + 8 + 4
                if o + 8 <= len(d):
                    return d[o:o + 8].hex()
def _decrypt_track(buf, K, base_iv64, sizes, offs):
    biv = int(base_iv64, 16)
    for idx, (co, sz) in enumerate(zip(offs, sizes)):
        iv = biv + idx << 64
        buf[co:co + sz] = AES.new(K, AES.MODE_CTR, counter=CTRCounter.new(128, initial_value=iv)).decrypt(bytes(buf[co:co + sz]))
def decrypt_av(ct_path, key_hex, out_path):
    """解密 mp4 全部加密轨(视频+音频): 每轨用自身 senc base_iv, 同一 content key, AES-128-CTR。\n    返回 {\'vide\': (ok,total), \'soun\': (None,total)}。视频按 NAL 自证统计, 音频无 NAL 不统计 ok。"""
    d = open(ct_path, 'rb').read()
    buf = bytearray(d)
    K = bytes.fromhex(key_hex)
    mv = oracle._find(d, [b'moov'])
    if not mv:
        raise RuntimeError('无 moov')
    else:
        stats = {}
        for t, o, sz, hs in oracle._ib(d, *mv):
            if t != b'trak':
                continue
            else:
                h = oracle._find(d, [b'mdia', b'hdlr'], o + hs, o + sz)
                handler = d[h[0] + 8:h[0] + 12] if h else None
                if handler not in (b'vide', b'soun'):
                    continue
                else:
                    iv8 = _trak_senc_iv8(d, o, o + sz)
                    if not iv8:
                        continue
                    else:
                        sizes, offs = oracle.parse_track_samples(d, handler)
                        if not sizes:
                            continue
                        else:
                            _decrypt_track(buf, K, iv8, sizes, offs)
                            if handler == b'vide':
                                ok = sum((1 for co, s in zip(offs, sizes) if oracle._nal_ok(bytes(buf[co:co + s]), s)))
                                stats['vide'] = (ok, len(sizes))
                            else:
                                stats['soun'] = (None, len(sizes))
        open(out_path, 'wb').write(buf)
        v = stats.get('vide')
        a = stats.get('soun')
        msg = []
        if v:
            msg.append(f'视频 NAL合法 {v[0]}/{v[1]}')
        if a:
            msg.append(f'音频 {a[1]} 样本')
        print(f"  全轨解密: {out_path}  ({'; '.join(msg)})")
        return stats
def strip_cenc(in_path, out_path):
    """无 ffmpeg 纯 Python 去 CENC 信令: 在 moov 内把 encv→hvc1 / enca→mp4a, 并把\n    sinf/senc/saiz/saio 盒改名成 free(中和)。全部是等长改名, 不移动任何字节, 故 mdat\n    偏移不变、stco 无需重算。样本须已解密(本工程 decrypt_av 已解)。返回 out_path 或 None。\n    修复\"有画面无声音\"(播放器跳过 enca 音轨)。"""
    # ***<module>.strip_cenc: Failure: Compilation Error
    import struct as _s
    buf = bytearray(open(in_path, 'rb').read())
    o = 0
    moov = None
    while o + 8 <= len(buf):
        sz = _s.unpack('>I', buf[o:o + 4])[0]
        typ = bytes(buf[o + 4:o + 8])
        if sz == 1:
            sz = _s.unpack('>Q', buf[o + 8:o + 16])[0]
        if sz < 8:
            break
        if typ == b'moov':
            moov = (o + 8, o + sz)
            break
        o += sz
    if not moov:
        return
    else:
        CONTAINERS = {b'mvex', b'dinf', b'minf', b'moov', b'wave', b'udta', b'mdia', b'stbl', b'gmhd', b'edts', b'trak'}
        RENAME = {b'encv': b'hvc1', b'enca': b'mp4a', b'sinf': b'free', b'senc': b'free', b'saiz': b'free', b'saio': b'free'}
        n = [0]
        def kids(p, cstart, cend):
            """若 cstart 处是合法盒头就当容器递归, 否则退回在 [p,cend) 内找 sinf 改名。"""
            # ***<module>.strip_cenc.kids: Failure: Different control flow
            if cstart + 8 <= cend:
                csz = _s.unpack('>I', buf[cstart:cstart + 4])[0]
                if 8 <= csz <= cend - cstart:
                        walk(cstart, cend)
            si = buf.find(b'sinf', p, cend)
            if si != (-1):
                buf[si:si + 4] = b'free'
                n[0] += 1
        def walk(start, end):
            # ***<module>.strip_cenc.walk: Failure detected at line number 121 and instruction offset 16: Different bytecode
            p = start
            while p + 8 <= end:
                sz = _s.unpack('>I', buf[p:p + 4])[0]
                typ = bytes(buf[p + 4:p + 8])
                hdr = 8
                if sz == 1:
                    sz = _s.unpack('>Q', buf[p + 8:p + 16])[0]
                    hdr = 16
                else:
                    if sz == 0:
                        sz = end - p
                if sz < 8 or p + sz > end:
                    return None
                else:
                    if typ in CONTAINERS:
                        walk(p + hdr, p + sz)
                    else:
                        if typ == b'stsd':
                            walk(p + hdr + 8, p + sz)
                        else:
                            if typ == b'encv':
                                kids(p, p + hdr + 78, p + sz)
                            else:
                                if typ == b'enca':
                                    kids(p, p + hdr + 28, p + sz)
                    if typ in RENAME:
                        buf[p + 4:p + 8] = RENAME[typ]
                        n[0] += 1
                    p += sz
        walk(*moov)
        if not n[0]:
            return
        else:
            open(out_path, 'wb').write(buf)
            return out_path
def remux_playable(in_path, out_path):
    """剥离 CENC 信令(encv→hvc1 / enca→mp4a, 中和 senc/sinf/saiz/saio), 使严格播放器可播且有声音。\n    优先 ffmpeg(-c copy 不重编码); 无 ffmpeg 则纯 Python strip_cenc(等长改名, 同样有效)。"""
    ff = shutil.which('ffmpeg')
    if ff:
        _flags = 134217728 if sys.platform.startswith('win') else 0
        r = subprocess.run([ff, '-y', '-loglevel', 'error', '-i', in_path, '-c', 'copy', '-tag:v', 'hvc1', out_path], capture_output=True, text=True, creationflags=_flags)
        if r.returncode == 0 and os.path.exists(out_path):
            return out_path
        else:
            print(f'  [!] ffmpeg 重封装失败, 改用纯 Python 去 CENC: {r.stderr[:150]}')
    try:
        res = strip_cenc(in_path, out_path)
    except Exception as ex:
        print(f'  [!] strip_cenc 异常: {ex}')
        res = None
    if res:
        print('  [i] 已纯 Python 去 CENC(encv→hvc1/enca→mp4a), 视频+音频均可播')
    else:
        print('  [!] 去 CENC 失败(无 moov?), 文件残留 encv/enca 盒')
    return res