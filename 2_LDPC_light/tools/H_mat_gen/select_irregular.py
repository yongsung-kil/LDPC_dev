"""Irregular QC-LDPC 후보 다중 생성 → FER 기준 선별 (사용자 지시 2026-07-30).

목표 분포 (base 17×144, z=256):  Dv10:31 / Dv4:31 / Dv3:66 / Dv2:16  (합 144)
dual-diagonal parity(M=17)가 dv2×16(bidiagonal) + dv3×1(anchor)을 공급하므로
정보부 127 col = dv3×65 + dv4×31 + dv10×31 로 배치하면 분포가 정확히 일치한다.

절차: 후보 SEEDS개 생성 → 스크리닝 포인트(FER≈1e-2)에서 전수 비교 →
상위 2개를 딥 포인트(FER≈1e-3 부근)에서 재측정 → 승자 저장.
실행: python -m 2_LDPC_light.tools.H_mat_gen.select_irregular
출력: 이 폴더의 out/ 하위 (irregular_17x144_z256.qc, select_irregular.csv)

주의 (2026-08-07): 이 스크립트는 구 본체 API 기준이라 **현재 실행 불가** — 새 구조
(채널 dict, decoder_main, LLR matrix 필수)로 손질 필요 (TODO 등록됨). import만
LDPC_base로 돌려놓은 상태다.
"""
import csv
import math
import os
import time

import numpy as np

from ...LDPC_base.decoder import MinSumDecoder
from ...LDPC_base import channel as chan
from ...LDPC_base.sim import run_fer_point
from .gen_example_code import build_code

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
WINNER_FILE = os.path.join(OUT, "irregular_17x144_z256.qc")

M, N, Z = 17, 144, 256
INFO_DEGREES = [3] * 65 + [4] * 31 + [10] * 31   # 오름차순 (PEG 처리 순서)
SEEDS = [101, 102, 103, 104, 105, 106]
MAX_ITER = 120   # 사용자 지정 (2026-07-30)


def fer_at(code, rber, seed, target_errors, max_frames, batch=128):
    dec = MinSumDecoder(code, max_iter=MAX_ITER)
    rng = np.random.default_rng([seed, int(rber * 1e7)])
    zero_cw = lambda b: np.zeros((b, code.N_b, code.z), np.uint8)   # all-zero (인코더 미사용)
    return run_fer_point(code, lambda b, rg: chan.bsc_llr(code, zero_cw(b), rber, rg),
                         dec, rng, target_errors=target_errors,
                         max_frames=max_frames, batch=batch)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []

    print("== 1) 후보 생성 ==")
    cands = []
    for sd in SEEDS:
        t0 = time.time()
        code = build_code(Z, M, N, INFO_DEGREES, seed=sd)
        c4 = code.count_cycles4()
        cands.append((sd, code))
        print(f"seed {sd}: E={code.E}, lifted 4-cycles={c4} ({time.time()-t0:.1f}s)")
        rows.append({"stage": "gen", "seed": sd, "rber": "", "fer": "", "note": f"4cyc={c4}"})

    print("== 2) 스크리닝 포인트 탐색 (seed 101 기준) ==")
    probe = []
    for rber in (0.012, 0.011, 0.010, 0.0095, 0.009, 0.0085, 0.008, 0.0075):
        r = fer_at(cands[0][1], rber, seed=7, target_errors=30, max_frames=512)
        probe.append((rber, r["fer"]))
        print(f"  probe RBER={rber}: FER={r['fer']:.3e} [{r['errors']}/{r['frames']}]")
        if r["fer"] < 5e-3:
            break
    # FER 1.5e-2에 가장 가까운 측정점을 스크리닝 포인트로
    meas = [(rb, f) for rb, f in probe if f > 0]
    rber_screen = min(meas, key=lambda x: abs(math.log10(x[1]) - math.log10(1.5e-2)))[0]
    print(f"→ 스크리닝 포인트: RBER={rber_screen}")

    print("== 3) 전 후보 스크리닝 ==")
    screen = []
    for sd, code in cands:
        r = fer_at(code, rber_screen, seed=11, target_errors=40, max_frames=3000)
        screen.append((sd, code, r["fer"]))
        print(f"  seed {sd}: FER={r['fer']:.3e} [{r['errors']}/{r['frames']}]")
        rows.append({"stage": "screen", "seed": sd, "rber": rber_screen,
                     "fer": f"{r['fer']:.4e}", "note": f"{r['errors']}/{r['frames']}"})
    screen.sort(key=lambda x: x[2])
    top2 = screen[:2]
    print(f"→ 상위 2개: seed {top2[0][0]}, seed {top2[1][0]}")

    # 딥 포인트: 스크리닝이 이미 1e-3 영역이면 그 자리, 아니면 probe 기울기로 외삽
    fer_med = sorted(x[2] for x in screen)[len(screen) // 2]
    slope_pts = [(rb, f) for rb, f in probe if f > 0]
    if fer_med <= 5e-3:
        rber_deep = rber_screen
    elif len(slope_pts) >= 2:
        (r1, f1), (r2, f2) = slope_pts[-2], slope_pts[-1]
        slope = (math.log10(f2) - math.log10(f1)) / (r2 - r1)   # dex per RBER
        rber_deep = rber_screen + (math.log10(1e-3) - math.log10(fer_med)) / slope
        rber_deep = round(max(min(rber_deep, rber_screen), rber_screen * 0.9), 4)
    else:
        rber_deep = round(rber_screen * 0.95, 4)
    print(f"== 4) 딥 테스트 (RBER={rber_deep}, FER~1e-3 목표) ==")
    deep = []
    for sd, code, _ in top2:
        r = fer_at(code, rber_deep, seed=13, target_errors=25, max_frames=15000)
        deep.append((sd, code, r["fer"], r))
        print(f"  seed {sd}: FER={r['fer']:.3e} [{r['errors']}/{r['frames']}] ({r['fps']:.1f} f/s)")
        rows.append({"stage": "deep", "seed": sd, "rber": rber_deep,
                     "fer": f"{r['fer']:.4e}", "note": f"{r['errors']}/{r['frames']}"})
    deep.sort(key=lambda x: x[2])
    win_sd, win_code = deep[0][0], deep[0][1]

    print(f"== 5) 승자 seed {win_sd} 저장 + 1000-frame 소요 시간 측정 ==")
    win_code.save(WINNER_FILE)
    print(win_code.summary())
    for label, rber in (("딥(~1e-3)", rber_deep), ("스크리닝(~1e-2)", rber_screen)):
        r = fer_at(win_code, rber, seed=17, target_errors=10 ** 9, max_frames=1000)
        print(f"  1000 frames @ RBER={rber} ({label}): {r['sec']:.1f}s "
              f"({r['fps']:.1f} f/s), FER={r['fer']:.3e}")
        rows.append({"stage": "timing1000", "seed": win_sd, "rber": rber,
                     "fer": f"{r['fer']:.4e}", "note": f"{r['sec']:.1f}s"})

    with open(os.path.join(OUT, "select_irregular.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["stage", "seed", "rber", "fer", "note"])
        w.writeheader()
        w.writerows(rows)
    print(f"winner saved: {WINNER_FILE}")


if __name__ == "__main__":
    main()
