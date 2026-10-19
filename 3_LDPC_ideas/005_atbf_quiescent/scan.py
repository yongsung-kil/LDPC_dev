"""ATBF 사다리 스크리닝 실행기 (ieee:5671820).

phase 1: 소규모 훑기 세 단계 (BF 단계 성공률 기준, 폴백 없음)
         A) ATBF (λ0, θ, BF 창) 격자 → 좋은 조합 선정
         B) GDBF 고정 임계 훑기 → 기준 구현의 임계 선정
         C) 선정 조합에서 휴면 임계 φ1 훑기 → φ1 선정
phase 2: 선정 값으로 사다리 4단(gdbf, atbf, atbf_q, es_atbf)과 min-sum 단독
         기준선을 본 측정한다 (실패 프레임은 min-sum 폴백, 합산 FER)

실행 (이 폴더에서):
    python -X utf8 scan.py                        phase 1 후 phase 2 연속 실행
    python -X utf8 scan.py 1                      phase 1만
    python -X utf8 scan.py 2 -8 1 16 -2 -0.5      phase 2만
        (인자: λ0, d(θ=2^-d), 추가 창, gdbf 임계, φ1)

결과: Sim_Output/scan_{시각}/ 에 CSV와 요약 텍스트 (git 무시 영역이므로
수치는 README.md 표로 옮겨 적는다).
"""
import csv
import datetime
import os
import sys
import time

import numpy as np

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))

_root = EXPERIMENT_DIR
while not os.path.isdir(os.path.join(_root, "2_LDPC_base", "src")):
    _parent = os.path.dirname(_root)
    if _parent == _root:
        raise SystemExit("상위 폴더에서 2_LDPC_base/src를 찾지 못함 "
                         "(이 파일은 LDPC_dev 하위 실험 폴더에 있어야 함)")
    _root = _parent
_base_root = os.path.join(_root, "2_LDPC_base")
if _base_root not in sys.path:
    sys.path.insert(0, _base_root)

from src.channel import fixed_error_channel      # noqa: E402
from src.decoder import BaseDecoder              # noqa: E402
from src.llr_matrix import LLRMatrix             # noqa: E402
from src.pcm import QCCode                       # noqa: E402

from decoder import ATBFLadderDecoder            # noqa: E402

H_PATH = os.path.join(_base_root, "Input", "H_matrix", "matrix_sel_1.txt")
LLR_PATH = os.path.join(_base_root, "Input", "LLR", "LLR_MATRIX_HD_matrix_sel_1.txt")

SEED = 0
BATCH = 64

PHASE1_ERRORS = (50, 90, 130)
PHASE1_FRAMES = 128
PHASE1_LAMBDA0 = (-4.0, -8.0, -16.0)
PHASE1_THETA_D = (1, 2)              # θ = 2^-d
PHASE1_WINDOWS = (4, 8, 16)
PHASE1_GDBF_LAMBDA = (-1.0, -2.0, -4.0)   # 고정 임계 기준 구현의 임계 후보
PHASE1_PHI1 = (-1.0, -0.5, -0.25)         # 휴면 임계 후보

PHASE2_ERRORS = (10, 30, 50, 70, 90, 110, 130, 150)
PHASE2_FRAMES = 256
VARIANT_LADDER = ("gdbf", "atbf", "atbf_q", "es_atbf")


def build_decoder(code, llr_matrix, variant, window, lambda0, theta_d, fallback,
                  phi1=-0.5):
    """클래스 파라미터를 설정하고 인스턴스를 만든다 (002 scan 방식)."""
    cls = ATBFLadderDecoder
    cls.VARIANT = variant
    cls.BF_WINDOW = int(window)
    cls.LAMBDA0 = float(lambda0)
    cls.THETA = 2.0 ** (-int(theta_d))
    cls.PHI1 = float(phi1)
    cls.FALLBACK = fallback
    cls.ES_OBSERVE = True
    return cls(code, llr_matrix)


def run_point(decoder, code, n_err, frames):
    """한 에러 포인트 측정. 모든 디코더(사다리, 기준선)가 같은 seed 파생
    스트림과 같은 배치 크기를 쓰므로 프레임 단위로 같은 채널을 받는다."""
    rng = np.random.default_rng([SEED, int(n_err)])
    cw = np.zeros((BATCH, code.N_b, code.z), np.uint8)
    done = success = 0
    iter_sum = 0            # 성공은 수렴 iteration, 실패는 max_iter (기준선 집계용)
    while done < frames:
        batch = min(BATCH, frames - done)
        channel_out = fixed_error_channel(code, cw[:batch], n_err, rng)
        result = decoder.decoder_main(channel_out)
        ok = result["success"]
        success += int(ok.sum())
        iter_sum += int(np.where(ok, result["decode_success_iteration"],
                                 decoder.max_iter).sum())
        done += batch
    return {"frames": done, "success": success, "fer": 1.0 - success / done,
            "iter_sum": iter_sum}


def _sweep(code, llr_matrix, rows, combos, label_fn):
    """combos의 각 (variant, window, λ0, d, φ1)을 PHASE1_ERRORS에서 측정해
    rows에 쌓고 {combo: 성공률 합} 점수를 반환한다."""
    score = {}
    for combo in combos:
        variant, window, lambda0, theta_d, phi1 = combo
        decoder = build_decoder(code, llr_matrix, variant, window, lambda0,
                                theta_d, fallback=False, phi1=phi1)
        per_e = []
        for n_err in PHASE1_ERRORS:
            decoder.reset_bf_stats()
            run_point(decoder, code, n_err, PHASE1_FRAMES)
            stats = decoder.bf_stats
            bf_rate = stats["bf_success"] / stats["frames"]
            per_e.append(bf_rate)
            score[combo] = score.get(combo, 0.0) + bf_rate
            rows.append([variant, lambda0, f"2^-{theta_d}", window, phi1, n_err,
                         stats["frames"], f"{bf_rate:.4f}",
                         f"{stats['bf_iters_sum'] / stats['frames']:.2f}",
                         f"{stats['bit_evals_sum'] / stats['frames']:.0f}"])
        print(f"  {label_fn(combo)}  "
              + "  ".join(f"E={e}:{r:.3f}" for e, r in zip(PHASE1_ERRORS, per_e)))
    return score


def phase1(code, llr_matrix, out_dir):
    """소규모 훑기. 반환: (λ0, d, 창, gdbf 임계, φ1)."""
    rows = []
    print("=== phase 1-A: ATBF (λ0, θ, 창) 격자 훑기 ===")
    atbf_combos = [("atbf", w, l0, d, -1.0)
                   for l0 in PHASE1_LAMBDA0 for d in PHASE1_THETA_D
                   for w in PHASE1_WINDOWS]
    score = _sweep(code, llr_matrix, rows, atbf_combos,
                   lambda c: f"atbf l0={c[2]:+.0f} th=2^-{c[3]} W={c[1]:2d}")
    # 선정: 창별로 세 에러 포인트 BF 성공률 합 최대 (동률이면 λ0 큰 쪽),
    # 전체 최적 창은 성공률 합 최대 (동률이면 작은 창)
    best_by_window = {}
    for w in PHASE1_WINDOWS:
        best = max((c for c in score if c[1] == w),
                   key=lambda c: (score[c], c[2]))
        best_by_window[w] = (best[2], best[3])
        print(f"창 {w:2d} 최적: λ0={best[2]:+.0f}, θ=2^-{best[3]} "
              f"(성공률 합 {score[best]:.3f})")
    best = max(score, key=lambda c: (score[c], -c[1], c[2]))
    lambda0, theta_d, window = best[2], best[3], best[1]
    print(f"선정 조합: λ0={lambda0:+.0f}, θ=2^-{theta_d}, 창={window} "
          f"(성공률 합 {score[best]:.3f})")

    print("=== phase 1-B: GDBF 고정 임계 훑기 ===")
    gdbf_combos = [("gdbf", w, gl, 1, -1.0)
                   for gl in PHASE1_GDBF_LAMBDA for w in sorted({4, window})]
    score_gdbf = _sweep(code, llr_matrix, rows, gdbf_combos,
                        lambda c: f"gdbf l={c[2]:+.0f} W={c[1]:2d}")
    best_gdbf = max(score_gdbf, key=lambda c: (score_gdbf[c], c[2]))
    gdbf_lambda = best_gdbf[2]
    print(f"선정 gdbf 임계: {gdbf_lambda:+.0f} (성공률 합 {score_gdbf[best_gdbf]:.3f})")

    print("=== phase 1-C: 휴면 임계 φ1 훑기 (atbf_q, 선정 조합) ===")
    phi_combos = [("atbf_q", window, lambda0, theta_d, p) for p in PHASE1_PHI1]
    score_phi = _sweep(code, llr_matrix, rows, phi_combos,
                       lambda c: f"atbf_q phi1={c[4]:+.2f}")
    best_phi = max(score_phi, key=lambda c: (score_phi[c], c[4]))
    phi1 = best_phi[4]
    print(f"선정 φ1: {phi1:+.2f} (성공률 합 {score_phi[best_phi]:.3f})")

    best_by_window = {w: best_by_window[w] for w in sorted({4, window})}
    path = os.path.join(out_dir, "phase1_grid.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["variant", "lambda0", "theta", "window", "phi1", "E",
                         "frames", "bf_success_rate", "avg_bf_iters",
                         "bit_evals_per_frame"])
        writer.writerows(rows)
    print(f"saved: {path}")
    return best_by_window, gdbf_lambda, phi1


def phase2(code, llr_matrix, out_dir, best_by_window, gdbf_lambda, phi1):
    """사다리 4단 + min-sum 단독 기준선 본 측정 (창별 최적 조합 사용)."""
    N = code.N
    windows = sorted(best_by_window)
    summary_rows = []
    curve_rows = []
    combos_desc = ", ".join(f"창{w}: λ0={l0:+.0f} θ=2^-{d}"
                            for w, (l0, d) in best_by_window.items())
    print(f"=== phase 2: 사다리 본 측정 ({combos_desc}, "
          f"gdbf 임계={gdbf_lambda:+.0f}, φ1={phi1:+.2f}) ===")

    print("  [min-sum 단독 기준선]")
    base_decoder = BaseDecoder(code, llr_matrix)
    base_points = {}
    for n_err in PHASE2_ERRORS:
        t0 = time.time()
        point = run_point(base_decoder, code, n_err, PHASE2_FRAMES)
        avg_iter = point["iter_sum"] / point["frames"]
        base_points[n_err] = point
        summary_rows.append(["minsum", "-", n_err, point["frames"],
                             f"{point['fer']:.4e}", "-", f"{avg_iter:.2f}", "-",
                             f"{avg_iter * N:.0f}", f"{avg_iter * N:.0f}",
                             "-", "-", "-", "-"])
        print(f"    E={n_err:3d}  fer={point['fer']:.2e}  avg_iter={avg_iter:5.2f}"
              f"  ({time.time() - t0:.1f}s)")

    for window in windows:
        lambda0, theta_d = best_by_window[window]
        for variant in VARIANT_LADDER:
            decoder = build_decoder(
                code, llr_matrix, variant, window,
                gdbf_lambda if variant == "gdbf" else lambda0,
                theta_d, fallback=True, phi1=phi1)
            print(f"  [{variant} W={window}]")
            for n_err in PHASE2_ERRORS:
                decoder.reset_bf_stats()
                t0 = time.time()
                point = run_point(decoder, code, n_err, PHASE2_FRAMES)
                stats = decoder.bf_stats
                frames = stats["frames"]
                bf_rate = stats["bf_success"] / frames
                avg_bf_iters = stats["bf_iters_sum"] / frames
                bf_bits = stats["bit_evals_sum"] / frames
                blk_bits = stats["blockskip_bit_evals_sum"] / frames
                fb_bits = stats["fallback_iters_sum"] * N / frames
                base_bits = (base_points[n_err]["iter_sum"]
                             / base_points[n_err]["frames"]) * N
                # 전부 휴면 블록 비율: 마지막 활성 iteration 기준
                active_frames_per_iter = stats["iter_active_frames"]
                nonzero = np.flatnonzero(active_frames_per_iter)
                if len(nonzero) and variant in ("atbf_q", "es_atbf"):
                    last = nonzero[-1]
                    block_q_last = (stats["iter_full_q_blocks"][last]
                                    / (active_frames_per_iter[last] * code.N_b))
                else:
                    block_q_last = 0.0
                es_triggered = int(stats["es_trigger_hist"][1:].sum())
                misfire_rate = (stats["es_misfire"] / es_triggered
                                if es_triggered else 0.0)
                summary_rows.append([
                    variant, window, n_err, frames, f"{point['fer']:.4e}",
                    f"{bf_rate:.4f}", f"{avg_bf_iters:.2f}",
                    f"{stats['fallback_frames'] / frames:.4f}",
                    f"{bf_bits + fb_bits:.0f}", f"{base_bits:.0f}",
                    f"{bf_bits:.0f}", f"{blk_bits:.0f}",
                    f"{block_q_last:.4f}", f"{misfire_rate:.4f}"])
                for k in range(window):
                    if active_frames_per_iter[k] == 0:
                        continue
                    curve_rows.append([
                        variant, window, n_err, k + 1,
                        int(active_frames_per_iter[k]),
                        int(stats["iter_flips"][k]),
                        int(stats["iter_active_bits"][k]),
                        int(stats["iter_reach_bits"][k]),
                        int(stats["iter_full_q_blocks"][k])])
                print(f"    E={n_err:3d}  fer={point['fer']:.2e}  bf={bf_rate:.3f}"
                      f"  bf_it={avg_bf_iters:4.2f}"
                      f"  bits/fr={bf_bits:8.0f}+{fb_bits:8.0f}"
                      f"  blkq={block_q_last:.3f}  misfire={misfire_rate:.3f}"
                      f"  ({time.time() - t0:.1f}s)")

    path = os.path.join(out_dir, "phase2_ladder.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["variant", "window", "E", "frames", "fer_combined",
                         "bf_success_rate", "avg_bf_iters", "fallback_rate",
                         "total_bit_evals_per_frame", "minsum_only_bit_evals",
                         "bf_bit_evals_per_frame", "bf_blockskip_bit_evals",
                         "block_full_quiescent_ratio_last_iter",
                         "es_misfire_rate"])
        writer.writerows(summary_rows)
    print(f"saved: {path}")
    path = os.path.join(out_dir, "phase2_iter_curves.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["variant", "window", "E", "iter", "active_frames",
                         "flips", "active_bits", "reach_bits",
                         "full_quiescent_blocks"])
        writer.writerows(curve_rows)
    print(f"saved: {path}")


def main():
    stamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    out_dir = os.path.join(EXPERIMENT_DIR, "Sim_Output", f"scan_{stamp}")
    os.makedirs(out_dir, exist_ok=True)
    code = QCCode.load(H_PATH)
    llr_matrix = LLRMatrix.load(LLR_PATH)
    print(code.summary())
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("1", "all"):
        best = phase1(code, llr_matrix, out_dir)
    else:
        lambda0, theta_d, window = (float(sys.argv[2]), int(sys.argv[3]),
                                    int(sys.argv[4]))
        best_by_window = {w: (lambda0, theta_d) for w in sorted({4, window})}
        best = (best_by_window, float(sys.argv[5]), float(sys.argv[6]))
    if mode in ("2", "all"):
        phase2(code, llr_matrix, out_dir, *best)
    print(f"run dir: {out_dir}")


if __name__ == "__main__":
    main()
