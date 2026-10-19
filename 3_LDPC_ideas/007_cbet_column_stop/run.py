"""007_cbet_column_stop 런처: config.json으로 그림자 측정을 실행하고 집계한다.

실행:
  python run.py            본 측정 (config.json의 포인트 전체, cbet_stats.csv 산출)
  python run.py --verify   동등성 검증만 (BaseDecoder와 같은 입력으로 결과 비교)

본체 import와 디코더 선택 방식: 3_LDPC_ideas/README.md 폴더 규칙 참조.
표준 런처와 달리 포인트 루프를 직접 돌린다 (run_fer_point 재사용). 포인트마다
디코더의 그림자 기록을 모아 세 종료 기준(iteration 경계, PCRC 모사, CB-ET)의
처리 column block 수와 절감률을 계산하고 run 폴더에 cbet_stats.csv로 남긴다.
"""
import csv
import os
import sys

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

import numpy as np

from src import channel as chan
from src import encoder
from src.decoder import BaseDecoder
from src.run import load_config, setup, create_run_dir, print_experiment_summary
from src.sim import run_fer_point

from decoder import CbEtShadowDecoder

DECODER_CLASS = CbEtShadowDecoder

# 집계 CSV 열 (표 머리와 포인트별 값의 순서 정본)
_STAT_COLUMNS = [
    "E", "frames", "errors", "fer", "avg_engine_iter",
    "colblk_boundary", "colblk_pcrc", "colblk_cbet",
    "iter_eq_boundary", "iter_eq_pcrc", "iter_eq_cbet",
    "save_pcrc_vs_boundary", "save_cbet_vs_boundary", "save_cbet_vs_pcrc",
    "false_stop_info", "false_stop_total",
    "nofire_boundary", "nofire_pcrc", "nofire_cbet", "pcrc_earlier_frames",
]


def aggregate_point(frames_rec, N_b, max_iter):
    """포인트 하나의 프레임별 그림자 기록 → 집계 dict.

    비용 = 종료까지 처리한 column block 수. 기준이 발화한 프레임은 발화 좌표까지,
    발화하지 못한 프레임(미수렴 실패 포함)은 엔진이 실제 돈 iteration 수 전체를
    하한값으로 쓴다 (nofire_* 수로 규모를 따로 보고)."""
    success = frames_rec["success"]
    genie_iter = frames_rec["genie_iter"].astype(np.int64)
    iters_run = np.where(success, genie_iter, max_iter).astype(np.int64)

    b_iter = frames_rec["boundary_hit_iter"].astype(np.int64)
    p_iter = frames_rec["pcrc_hit_iter"].astype(np.int64)
    p_col = frames_rec["pcrc_hit_col"].astype(np.int64)
    c_iter = frames_rec["cbet_hit_iter"].astype(np.int64)
    c_col = frames_rec["cbet_hit_col"].astype(np.int64)

    b_fired = b_iter > 0
    p_fired = p_iter > 0
    c_fired = c_iter > 0
    cost_boundary = np.where(b_fired, b_iter * N_b, iters_run * N_b)
    cost_pcrc = np.where(p_fired, (p_iter - 1) * N_b + p_col + 1, iters_run * N_b)
    cost_cbet = np.where(c_fired, (c_iter - 1) * N_b + c_col + 1, iters_run * N_b)

    mean_b = float(cost_boundary.mean())
    mean_p = float(cost_pcrc.mean())
    mean_c = float(cost_cbet.mean())
    both = p_fired & c_fired
    return {
        "frames": len(success),
        "errors": int((~success).sum()),
        "fer": float((~success).mean()),
        "avg_engine_iter": float(iters_run.mean()),
        "colblk_boundary": mean_b,
        "colblk_pcrc": mean_p,
        "colblk_cbet": mean_c,
        "iter_eq_boundary": mean_b / N_b,
        "iter_eq_pcrc": mean_p / N_b,
        "iter_eq_cbet": mean_c / N_b,
        "save_pcrc_vs_boundary": 1.0 - mean_p / mean_b,
        "save_cbet_vs_boundary": 1.0 - mean_c / mean_b,
        "save_cbet_vs_pcrc": 1.0 - mean_c / mean_p,
        "false_stop_info": int((c_fired & (frames_rec["cbet_info_err"] > 0)).sum()),
        "false_stop_total": int((c_fired & (frames_rec["cbet_total_err"] > 0)).sum()),
        "nofire_boundary": int((~b_fired).sum()),
        "nofire_pcrc": int((~p_fired).sum()),
        "nofire_cbet": int((~c_fired).sum()),
        "pcrc_earlier_frames": int((both & (cost_pcrc < cost_cbet)).sum()),
    }


def verify_fer_invariance(code, llr_matrix):
    """같은 채널 출력으로 BaseDecoder와 CbEtShadowDecoder의 결과 일치를 확인한다
    (그림자 측정이 판정에 개입하지 않음을 실측으로 보증)."""
    base_decoder = BaseDecoder(code, llr_matrix=llr_matrix)
    shadow_decoder = CbEtShadowDecoder(code, llr_matrix=llr_matrix)
    compare_keys = ("success", "decode_success_iteration",
                    "final_err_bits", "final_info_err_bits")
    for point, batch in ((50, 32), (150, 32), (390, 32)):
        rng = np.random.default_rng([99991, int(point)])
        msg = encoder.generate_message(code, batch, rng)
        cw = encoder.encode(msg, code)
        channel_out = chan.CHANNELS["fixed_error"](code, cw, point, rng,
                                                   mode=llr_matrix.mode)
        result_base = base_decoder.decoder_main(channel_out)
        result_shadow = shadow_decoder.decoder_main(channel_out)
        for key in compare_keys:
            if not np.array_equal(result_base[key], result_shadow[key]):
                raise AssertionError(f"E={point} {key} 불일치: 그림자 측정이 판정에 개입함")
        print(f"  E={point:4d} ({batch} frames): {', '.join(compare_keys)} 전부 일치")
    print("동등성 검증 통과: 그림자 디코더의 판정 결과가 BaseDecoder와 완전히 같음")


def main():
    config_path = os.path.join(EXPERIMENT_DIR, "config.json")
    config = load_config(config_path)
    code, decoder = setup(config, DECODER_CLASS)

    if "--verify" in sys.argv[1:]:
        verify_fer_invariance(code, decoder.llr_matrix)
        return

    print_experiment_summary(code, decoder, config)
    run_dir = create_run_dir(config, config_path, code, decoder)
    summary_path = os.path.join(run_dir, "summary.txt")
    run_config = config["run"]

    stat_rows = []
    for channel_index, channel_config in enumerate(config["channels"]):
        if channel_config["type"] != "fixed_error":
            raise SystemExit("이 실험은 fixed_error 채널 전용")
        for point in channel_config["points"]:
            rng = np.random.default_rng([config["seed"], channel_index, int(1e6 * point)])

            def channel_fn(batch, random_generator, point=point):
                msg = encoder.generate_message(code, batch, random_generator)
                cw = encoder.encode(msg, code)
                return chan.CHANNELS["fixed_error"](
                    code, cw, point, random_generator, mode=decoder.llr_matrix.mode)

            decoder.shadow_reset()
            run_fer_point(
                code, channel_fn, decoder, rng,
                max_frame_errors=run_config["max_frame_errors"],
                max_frames=run_config["max_frames"],
                frames_per_batch=run_config["frames_per_batch"],
                print_progress=run_config.get("print_progress", True),
                progress_label=f"fixed_error E={point}",
                progress_interval_frames=run_config["progress_interval_frames"],
                summary_path=summary_path)
            stats = aggregate_point(decoder.shadow_frames(), code.N_b, decoder.max_iter)
            stats["E"] = point
            stat_rows.append(stats)

    csv_path = os.path.join(run_dir, "cbet_stats.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_STAT_COLUMNS)
        for row in stat_rows:
            writer.writerow([f"{row[k]:.6g}" if isinstance(row[k], float) else row[k]
                             for k in _STAT_COLUMNS])
    print(f"saved: {csv_path}")

    header = (f"{'E':>4} {'avg_it':>6} {'blk_bnd':>8} {'blk_pcrc':>8} {'blk_cbet':>8} "
              f"{'sv_p/b':>7} {'sv_c/b':>7} {'sv_c/p':>7} {'fs':>3} {'nf_c':>4} {'p<c':>4}")
    print(header)
    for row in stat_rows:
        print(f"{row['E']:>4} {row['avg_engine_iter']:>6.2f} "
              f"{row['colblk_boundary']:>8.1f} {row['colblk_pcrc']:>8.1f} "
              f"{row['colblk_cbet']:>8.1f} "
              f"{row['save_pcrc_vs_boundary']:>6.1%} {row['save_cbet_vs_boundary']:>6.1%} "
              f"{row['save_cbet_vs_pcrc']:>6.1%} {row['false_stop_info']:>3} "
              f"{row['nofire_cbet']:>4} {row['pcrc_earlier_frames']:>4}")
    print(f"run dir: {run_dir}")


if __name__ == "__main__":
    main()
