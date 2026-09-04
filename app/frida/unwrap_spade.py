# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: 'D:\\code\\Hongguo-App\\installer\\_stage\\app\\frida\\unwrap_spade.py'
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2026-07-28 06:30:27 UTC (1785220227)

"""红果 spade_a -> content key 纯离线 unwrap (§9 终极: 无 app/无播放/无 frida)。\n\n逆向自 libttmplayer.so FUN_001c4550 (ver1 路径, flag=opt0x97)。\n算法 = 纯字节变换(XOR + POPCOUNT + 位置相关), 无 KEK、无 AES。\n已用 5 组运行时真值 100% 验证 (见 __main__ 自测)。\n\n链路: API video_model.encryptInfo.spadeA(base64)\n      -> base64_decode -> unwrap_v1 -> content key(16B, 32 hex)\n      -> 配合密文 senc 首样本 base_iv -> AES-128-CTR 解密。\n\n注: ver2(spade type \"app_v2\"/\"web_v2\") 走 libttmplayer FUN_00271a50\n    (base64 + MD5(KEK) + AES-GCM-256), 当前红果视频未见使用, 见 §16.10。\n"""
import base64
def _popcount(x):
    return bin(x & 4294967295).count('1')
def _s8(v):
    v &= 255
    return v - 256 if v >= 128 else v
def _strncmp0(a, b, n):
    for k in range(n):
        ca = a[k] if k < len(a) else 0
        cb = b[k] if k < len(b) else 0
        if ca != cb:
            return False
        else:
            if ca == 0:
                return True
    return True
def unwrap_v1(spade, flag=0):
    # irreducible cflow, using cdg fallback
    """spade(37B bytes 或 hex 字符串) -> content key(32 hex 字符串) 或 None。\n    flag = 播放器 option 0x97 的值(实测为 0); flag!=0 时变换方向相反。"""
    # ***<module>.unwrap_v1: Failure: Different control flow
    if isinstance(spade, str):
        spade = bytes.fromhex(spade)
    L = len(spade)
    if L < 3:
        return
    bVar5 = spade[0] ^ spade[1] ^ spade[2]
    iVar9 = bVar5 - 48
    if iVar9 < 1:
        return
    uVar1 = L - bVar5 + 47
    if uVar1 < 1 or 1 + uVar1 > L:
        return None
    dest = bytearray(spade[1:1 + uVar1])
    s1 = bytearray(iVar9)
    b16 = spade[L - iVar9 - 2]
    b14 = spade[L - iVar9 - 1]
    for i in range(iVar9):
        s1[i] = b14 ^ b16 ^ spade[i + (L - iVar9)]
    if _strncmp0(s1, b'app_v2', iVar9) or _strncmp0(s1, b'web_v2', iVar9):
        return None
    b14, b16 = (85, 250)
    for i in range(uVar1):
        b6 = dest[i]
        u18 = _popcount(i)
        b3, b7 = (b6, b14)
        if i & 1:
            b3, b7, b16 = (b16, b6, b14)
        cVar4 = u18 + 21 if flag else _s8((-21) - u18)
        dest[i] = cVar4 + (b16 ^ b6) & 255
        b14, b16 = (b7, b3)
    b0 = dest[0]
    if 48 <= b0 <= 57:
        u11 = b0 - 48
    elif 97 <= b0 <= 122:
        u11 = b0 - 87
    else:
        return None
    iv9 = uVar1 - (u11 & 255)
    if iv9 < 2:
        return None
    return bytes(dest[1:iv9]).decode('latin1', 'replace')
def spade_to_key(spade_a_b64, flag=0):
    """video_model 的 spadeA(base64) -> content key(32 hex)。一步到位。"""
    return unwrap_v1(base64.b64decode(spade_a_b64), flag)
_TRUTH = [('93bc1df253ba1bf7618b19c448b806f64d810afc45b715fe5eb925f26cbf12f541ba098282', '287216bfa89e662a0f748120c305e199'), ('a1bc2ff164b91df04dbf00f17dba00f47cbb35c27b922aec67a628eb52972fdc7ea036a7a7', 'd742b28967e4e6c92b699f4375add27f'), ('9cbc12fb588721cd69b739f977b70be7429c08e074990ec847843dcc738638cf76b33ebcbc', '113fb30d9767d80e3edbb905b052204f'), ('a3bc2df760ba2bc27b8b34c04a8907f557be19f249be35c748ba03f64fbc1ff161ba29a2a2', 'b5674a8384f25d757585dadf343274d5'), ('9cbc12f45aba11f76fb814f444bd15f459b225cb5e8c15dd459a0fd170ac0ad358aa108b8b', '121846f9d5829130ebc0397023feaf8c')]
def _selftest():
    ok = 0
    for sp, exp in _TRUTH:
        got = unwrap_v1(sp, 0)
        hit = got == exp
        ok += hit
        print(f"{('OK ' if hit else 'FAIL')} {got} == {exp}")
    print(f'{ok}/{len(_TRUTH)} passed')
    return ok == len(_TRUTH)
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        sp = sys.argv[1]
        flag = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        try:
            key = spade_to_key(sp, flag) if not all((c in '0123456789abcdefABCDEF' for c in sp)) else unwrap_v1(sp, flag)
        except Exception:
            key = unwrap_v1(sp, flag)
        print(key)
    else:
        _selftest()