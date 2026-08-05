"""LLR 프로파일 튜닝: llr/ 폴더의 프로파일들을 fixed-error 포인트에서 비교.

HW-근사 3-bit internal precision(VNU 출력 {7,5,3,1} + dv별 채널 LLR)의 TH_HD
시작값 후보들을 비교해 좋은 것을 고른다 (TH 원본 소실 — plan.md 참조).
비교 기준선: 프로파일 없는 기존 6-bit 선형 모드.

실행: python -m 2_LDPC_light.examples.llr_tune
출력: out/llr_tune.csv
"""
import csv
import glob
import os

import numpy as np

from ..pcm import QCCode
from ..decoder import MinSumDecoder
from ..channel import fixed_error_llr
from ..llr_tables import load_profile, ch_mag_by_col
from ..sim import run_fer_point

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
CODE_FILE = os.path.join(HERE, "irregular_17x144_z256.qc")
LLR_DIR = os.path.join(os.path.dirname(HERE), "llr")

import sys

MAX_ITER = 120
SCHEDULE = sys.argv[1] if len(sys.argv) > 1 else "column_wise"   # 원본 대응 기본
POINTS = [300, 340, 360, 380]
TARGET_ERRORS, MAX_FRAMES, BATCH = 25, 512, 128


def measure(code, dec, mag, label):
    row = {"profile": label}
    for n_err in POINTS:
        rng = np.random.default_rng([20260731, n_err])
        r = run_fer_point(code, lambda b, rg: fixed_error_llr(code, n_err, b, rg, mag=mag),
                          dec, rng, target_errors=TARGET_ERRORS,
                          max_frames=MAX_FRAMES, batch=BATCH)
        row[str(n_err)] = f"{r['fer']:.3e}[{r['errors']}/{r['frames']}]"
        print(f"  {label} @ {n_err}bit: FER={r['fer']:.3e} [{r['errors']}/{r['frames']}] "
              f"({r['fps']:.1f} f/s)")
    return row


def main():
    code = QCCode.load(CODE_FILE)
    print(code.summary())
    rows = []

    print(f"== schedule={SCHEDULE} / 기준선: 6-bit 선형 (프로파일 없음, ch=±8) ==")
    rows.append(measure(code, MinSumDecoder(code, max_iter=MAX_ITER, schedule=SCHEDULE),
                        8.0, "baseline_6bit"))

    for path in sorted(glob.glob(os.path.join(LLR_DIR, "*.txt"))):
        if os.path.basename(path).startswith("_"):
            continue
        prof = load_profile(path)
        print(f"== {prof.name} ==")
        dec = MinSumDecoder(code, max_iter=MAX_ITER, llr_profile=prof, schedule=SCHEDULE)
        rows.append(measure(code, dec, ch_mag_by_col(code, prof), prof.name))

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "llr_tune.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["profile"] + [str(p) for p in POINTS])
        w.writeheader()
        w.writerows(rows)
    print(f"saved: {path}")


if __name__ == "__main__":
    main()
