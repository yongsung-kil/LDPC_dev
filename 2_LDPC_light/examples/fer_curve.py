"""예시 부호 정정능력 커브: FER vs RBER (BSC hard) / FER vs Eb/N0 (AWGN soft).

실행: python -m 2_LDPC_light.examples.fer_curve
출력: 2_LDPC_light/examples/out/{fer_bsc.csv, fer_awgn.csv, fer_curves.png}

측정 조건: all-zero codeword, genie 판정, offset min-sum(beta=1), max 20 iter.
0-error 포인트는 FER < 1/frames 상한으로 open marker 표시.
"""
import os

import numpy as np

from ..pcm import QCCode
from ..decoder import MinSumDecoder
from .. import channel as chan
from ..sim import sweep, save_csv

HERE = os.path.dirname(__file__)
CODE_FILE = os.path.join(HERE, "example_18x147_z256.qc")
OUT = os.path.join(HERE, "out")
MAX_ITER = 120   # 사용자 지정 (2026-07-30)

# dataviz 기본 팔레트 (light) slot1/slot2
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"


def measure(code, dec):
    bsc_points = [0.0105, 0.0100, 0.0095, 0.0090, 0.0085, 0.0080, 0.0075, 0.0070]
    awgn_points = [3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 4.0]
    common = dict(target_errors=40, max_frames=3000, batch=128, stop_below=5e-4)

    print("== BSC (hard-decision read) ==")
    bsc = sweep(code, dec, bsc_points,
                lambda p: (lambda b, rg: chan.bsc_llr(code, p, b, rg)),
                seed=20260730, **common)
    print("== AWGN (soft read) ==")
    awgn = sweep(code, dec, awgn_points,
                 lambda p: (lambda b, rg: chan.awgn_llr(code, p, b, rg)),
                 seed=20260731, **common)
    return bsc, awgn


def plot(code, bsc, awgn, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=150)
    fig.patch.set_facecolor("#fcfcfb")

    def draw(ax, results, color, xlabel, xfmt=lambda v: v):
        xs = [xfmt(r["param"]) for r in results]
        fer = [r["fer"] if r["errors"] else 0.5 / r["frames"] for r in results]
        solid = [r["errors"] > 0 for r in results]
        ax.plot([x for x, s in zip(xs, solid) if s], [f for f, s in zip(fer, solid) if s],
                "-o", color=color, linewidth=2, markersize=7, zorder=3)
        for x, f, s in zip(xs, fer, solid):
            if not s:   # 0-error 상한 포인트
                ax.plot(x, f, "v", markerfacecolor="white", markeredgecolor=color,
                        markersize=8, markeredgewidth=2, zorder=3)
        ax.set_yscale("log")
        ax.set_xlabel(xlabel, color=INK)
        ax.set_ylabel("FER", color=INK)
        ax.grid(True, which="both", color=GRID, linewidth=0.7, linestyle="--", zorder=0)
        ax.set_facecolor("#fcfcfb")
        for sp in ax.spines.values():
            sp.set_color(GRID)
        ax.tick_params(colors=INK2)

    draw(axes[0], bsc, BLUE, "RBER (raw bit error rate)")
    axes[0].set_title("BSC hard-decision read", color=INK)
    draw(axes[1], awgn, ORANGE, "Eb/N0 (dB)")
    axes[1].set_title("AWGN soft read (0.5-step quantized LLR)", color=INK)

    fig.suptitle(
        f"Correction capability — example QC-LDPC {code.M_b}x{code.N_b}, z={code.z}, "
        f"rate {code.rate:.3f}, offset min-sum (b=1), max {MAX_ITER} iter, genie termination",
        color=INK, fontsize=11)
    fig.text(0.99, 0.01, "open marker = 0 errors observed (FER upper bound)",
             ha="right", color=INK2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(path, facecolor=fig.get_facecolor())
    print(f"plot saved: {path}")


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(CODE_FILE):
        from ..tools.gen_example_code import build_example
        build_example().save(CODE_FILE)
    code = QCCode.load(CODE_FILE)
    print(code.summary())
    dec = MinSumDecoder(code, max_iter=MAX_ITER)

    bsc, awgn = measure(code, dec)
    save_csv(bsc, os.path.join(OUT, "fer_bsc.csv"), param_name="rber")
    save_csv(awgn, os.path.join(OUT, "fer_awgn.csv"), param_name="ebn0_db")
    plot(code, bsc, awgn, os.path.join(OUT, "fer_curves.png"))

    print("\n== summary ==")
    for name, rs, fmt in (("BSC", bsc, "{:.4f}"), ("AWGN", awgn, "{:.1f}dB")):
        for r in rs:
            bound = "" if r["errors"] else " (upper bound)"
            print(f"  {name} {fmt.format(r['param'])}: "
                  f"FER={max(r['fer'], 0.5 / r['frames']):.3e}{bound} "
                  f"[{r['errors']}/{r['frames']}]")


if __name__ == "__main__":
    main()
