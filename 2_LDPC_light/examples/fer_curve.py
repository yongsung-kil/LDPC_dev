"""예시 부호 정정능력 커브: FER vs RBER (BSC hard) / FER vs Eb/N0 (AWGN soft).

파라미터는 코드가 아니라 fer_curve.json에 있다 (run.py 참조).
H-matrix 준비: python -m 2_LDPC_light.tools.gen_example_code (최초 1회, 파일 없을 때만)
실행: python -m 2_LDPC_light.examples.fer_curve
출력: 2_LDPC_light/examples/out/{fer_bsc.csv, fer_awgn.csv, fer_curves.png}

측정 조건: all-zero codeword(encoder 스텁), genie 판정, offset min-sum(beta=1).
0-error 포인트는 FER < 1/frames 상한으로 open marker 표시.
"""
import os

from .. import run as runner

HERE = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(HERE, "fer_curve.json")

# dataviz 기본 팔레트 (light) slot1/slot2
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"


def plot(code, bsc, awgn, path, max_iter):
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
        f"rate {code.rate:.3f}, offset min-sum (b=1), max {max_iter} iter, genie termination",
        color=INK, fontsize=11)
    fig.text(0.99, 0.01, "open marker = 0 errors observed (FER upper bound)",
             ha="right", color=INK2, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(path, facecolor=fig.get_facecolor())
    print(f"plot saved: {path}")


def main():
    config = runner.load_config(CONFIG_FILE)
    code, dec = runner.setup(config)
    print(code.summary())

    results = runner.run_experiment(code, dec, config)
    runner.report(results, config)
    bsc, awgn = results["bsc"], results["awgn"]
    plot(code, bsc, awgn, os.path.join(config["output"]["dir"], "fer_curves.png"),
         max_iter=dec.max_iter)

    print("\n== summary ==")
    for name, rs, fmt in (("BSC", bsc, "{:.4f}"), ("AWGN", awgn, "{:.1f}dB")):
        for r in rs:
            bound = "" if r["errors"] else " (upper bound)"
            print(f"  {name} {fmt.format(r['param'])}: "
                  f"FER={max(r['fer'], 0.5 / r['frames']):.3e}{bound} "
                  f"[{r['errors']}/{r['frames']}]")


if __name__ == "__main__":
    main()
