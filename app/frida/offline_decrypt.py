# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\frida\\offline_decrypt.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-07-28 06:30:27 UTC (1785220227)

"""红果视频纯离线解密器: spadeA(base64) + 密文 mp4 -> 明文 mp4。\n\n全程无 app / 无网络 / 无 frida / 无 KEK:\n  content key = unwrap_spade(spadeA)           # 纯字节变换(§16.10)\n  base_iv64   = 密文 senc 盒首样本高8字节       # 纯文件(§8.1-1)\n  明文        = AES-128-CTR(key, iv=((base_iv+idx)<<64)) 逐样本解密\n\n用法:\n  python frida/offline_decrypt.py <spadeA_base64> <密文.mp4> [输出.mp4] [flag]\n  # flag = 播放器 opt 0x97 值(默认0; 不确定时自动两种都试)\n"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unwrap_spade
import oracle
from decutil import senc_iv8, decrypt_full, decrypt_av, remux_playable, tenc_kid
def offline_decrypt(spade_a_b64, ct_path, out_path=None, flag=0):
    # irreducible cflow, using cdg fallback
    # ***<module>.offline_decrypt: Failure: Compilation Error
    out_path = out_path or os.path.splitext(ct_path)[0] + '.dec.mp4'
    key = unwrap_spade.spade_to_key(spade_a_b64, flag)
    if not key or not len(key) == 32 or (not all((c in '0123456789abcdef' for c in key))):
        alt = unwrap_spade.spade_to_key(spade_a_b64, 1 - flag)
        if alt and len(alt) == 32 and all((c in '0123456789abcdef' for c in alt)):
            print(f'[i] flag={flag} 输出异常, 改用 flag={1 - flag}')
            key, flag = (alt, 1 - flag)
        else:
            print(f'[X] unwrap 失败 (spade 可能是 ver2/AES-GCM 或格式异常): {key!r}')
            return
    print(f'[1/3] content key = {key}   (flag={flag})')
    ivs = senc_iv8(ct_path)
    print(f'[2/3] senc base_iv 候选 = {ivs}   tenc.kid = {tenc_kid(ct_path)}')
    if not ivs:
        print('[X] 密文无 senc base_iv')
        return
    kh, ivh = oracle.verify_key_iv(ct_path, [key], ivs)
    if not kh:
        print('[X] key 与密文不匹配 (spade 与该密文不对应? 或 ver2 视频?)')
        return
    print(f'[3/3] key={kh} 校验通过 -> 全轨解密(视频+音频, 各用自身 senc base_iv)...')
    raw = os.path.splitext(out_path)[0] + '.raw.mp4'
    stats = decrypt_av(ct_path, kh, raw)
    v = stats.get('vide')
    a = stats.get('soun')
    clean = remux_playable(raw, out_path)
    if clean:
        try:
            os.remove(raw)
        except OSError:
            pass
    else:
        out_path = raw
    note = []
    if v:
        note.append(f'视频 {v[0]}/{v[1]} NAL 合法')
    if a:
        note.append(f'音频 {a[1]} 样本已解')
    flag_ok = not v or v[0] == v[1]
    print(f"\n{('✅ 纯离线解密成功' if flag_ok else '⚠ 视频部分样本 NAL 异常')}: {out_path}  ({'; '.join(note)})")
    return out_path
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    spade = sys.argv[1]
    ct = sys.argv[2]
    out = None
    flag = 0
    for a in sys.argv[3:]:
        if a.isdigit():
            flag = int(a)
        else:
            out = a
    offline_decrypt(spade, ct, out, flag)