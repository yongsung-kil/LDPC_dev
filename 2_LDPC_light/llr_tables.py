"""LLR 파라미터 프로파일: 2_LDPC_light/llr/*.txt 파일에서 로드.

원본 C++ (3-bit 빌드, decoder.cpp Get_VNU_Ch_LLR_Adaptive / Get_VNU_Th_Adaptive)의
internal precision 구조를 1세트로 단순화한 포맷 (Get_VNU_Table_Idx()가 스텁이라
원본도 사실상 1세트 동작):

  CH_HD    21 14 12 10            # 채널 LLR magnitude, dv 그룹 [DV2, DV3, DV4, DV5+] 순
  TH_HD    24 14 6  24 14 6 ...   # VNU 출력 양자화 임계 (th1 th2 th3) x 4 그룹 = 12개
  EDGE_MAG 7 5 3 1                # VNU 출력 magnitude 레벨 (내림차순, |temp|>=th1 -> 첫 값)
  BETA     0                      # C2V offset (HW는 0 — threshold 양자화가 축소 역할)
  BF_ITERS 0                      # 1-bit precision 구간 (iter <= BF_ITERS, dv>5) — HW ITER_MAX_HBF=0/4

'#' 이후는 주석. 원본 TH_* 실값은 소실 상태라 시작값은 추정치 — 파일을 여러 개 만들어
튜닝한다 (사용자 지시 2026-07-31). HW 원본 값 입수 시 그대로 교체.
"""
import os

import numpy as np

_KEYS = {"CH_HD": 4, "TH_HD": 12, "EDGE_MAG": 4, "BETA": 1, "BF_ITERS": 1}


class LLRProfile:
    def __init__(self, name, ch, th, edge_mag, beta, bf_iters):
        self.name = name
        self.ch = np.asarray(ch, np.float32)                    # (4,) dv 그룹별
        self.th = np.asarray(th, np.float32).reshape(4, 3)      # (그룹, th1..th3)
        self.edge_mag = np.asarray(edge_mag, np.float32)        # (4,) 내림차순
        self.beta = float(beta)
        self.bf_iters = int(bf_iters)

    def __repr__(self):
        return (f"LLRProfile({self.name}: ch={self.ch.tolist()}, "
                f"th={self.th.tolist()}, mag={self.edge_mag.tolist()}, "
                f"beta={self.beta}, bf={self.bf_iters})")


def dv_group(dv):
    """C++ dv_idx 매핑 (3-bit 빌드): dv<=2 -> 0(DV2), 3 -> 1, 4 -> 2, >=5 -> 3(MID/MAX)."""
    if dv <= 2:
        return 0
    if dv == 3:
        return 1
    if dv == 4:
        return 2
    return 3


def ch_mag_by_col(code, profile):
    """column block별 채널 LLR magnitude (N_b,) — dv 그룹 → CH_HD 값."""
    return profile.ch[np.array([dv_group(int(d)) for d in code.col_deg])]


def load_profile(path):
    vals = {}
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.split("#", 1)[0].strip()
            if not ln:
                continue
            parts = ln.split()
            key, nums = parts[0].upper(), [float(x) for x in parts[1:]]
            if key not in _KEYS:
                raise ValueError(f"{path}: unknown key {key}")
            if len(nums) != _KEYS[key]:
                raise ValueError(f"{path}: {key} expects {_KEYS[key]} values, got {len(nums)}")
            vals[key] = nums
    missing = set(_KEYS) - set(vals)
    if missing:
        raise ValueError(f"{path}: missing keys {sorted(missing)}")
    return LLRProfile(os.path.splitext(os.path.basename(path))[0],
                      vals["CH_HD"], vals["TH_HD"], vals["EDGE_MAG"],
                      vals["BETA"][0], vals["BF_ITERS"][0])
