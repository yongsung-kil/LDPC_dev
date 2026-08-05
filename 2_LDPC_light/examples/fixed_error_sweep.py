"""fixed-error 채널 FER 스윕: error bits 300부터 20bit 단위 (사용자 지시 2026-07-30).

HD read (LLR ±8), 프레임마다 정확히 n_err개 비트를 무작위 위치에 주입.
실행: python -m 2_LDPC_light.examples.fixed_error_sweep [code.qc 경로]
출력: out/fixed_error_sweep.csv
"""
import csv
import os
import sys

import numpy as np

from ..pcm import QCCode
from ..decoder import MinSumDecoder
from ..channel import fixed_error_llr
from ..sim import run_fer_point

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "out")
DEFAULT_CODE = os.path.join(HERE, "irregular_17x144_z256.qc")

MAX_ITER = 120
ERR_START, ERR_STEP, ERR_MAX = 300, 20, 560
TARGET_ERRORS, MAX_FRAMES, BATCH = 40, 3000, 128


def main():
    code_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CODE
    code = QCCode.load(code_file)
    print(f"code: {os.path.basename(code_file)}")
    print(code.summary())
    print(f"max_iter={MAX_ITER}, error bits {ERR_START}~ step {ERR_STEP} "
          f"(N={code.N}, 300bit = RBER {300 / code.N:.4%})")

    dec = MinSumDecoder(code, max_iter=MAX_ITER)
    rows = []
    for n_err in range(ERR_START, ERR_MAX + 1, ERR_STEP):
        rng = np.random.default_rng([20260730, n_err])
        r = run_fer_point(code, lambda b, rg: fixed_error_llr(code, n_err, b, rg),
                          dec, rng, target_errors=TARGET_ERRORS,
                          max_frames=MAX_FRAMES, batch=BATCH)
        print(f"errors={n_err:4d} (RBER {n_err / code.N:.4%}): FER={r['fer']:.3e} "
              f"[{r['errors']}/{r['frames']}] avg_iter(ok)={r['avg_iter_ok']:.1f} "
              f"({r['fps']:.1f} f/s)")
        rows.append({"error_bits": n_err, "rber_equiv": f"{n_err / code.N:.6f}",
                     "fer": f"{r['fer']:.6e}", "frames": r["frames"],
                     "errors": r["errors"], "avg_iter_ok": f"{r['avg_iter_ok']:.2f}"})
        if r["fer"] >= 0.99:
            print("FER 포화 — 스윕 종료")
            break

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "fixed_error_sweep.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"saved: {path}")


if __name__ == "__main__":
    main()
