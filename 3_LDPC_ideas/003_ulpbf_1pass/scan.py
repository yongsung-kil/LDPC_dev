"""ULPBF 1 pass 스크리닝 측정 스크립트.

t(프레임당 고정 에러 수) 격자에서 다음을 수집한다:
- 1단 단독 성공률 (CRC 판정 기준과 syndrome 0 기준, genie 기준)
- 1단 실패 프레임의 평균 오플립, 누락, 잔여 에러 비트 수 (genie 분해)
- CRC 거짓 통과 수 (CRC 통과인데 syndrome이 0이 아님)
- 2단 구성 FER 대 min-sum 단독 FER (같은 채널 실현을 양쪽에 공급)
- syndrome 갱신 생략 대리 지표: 2단 구성이 쓴 min-sum iteration 합 /
  min-sum 단독의 iteration 합 (실패 프레임은 max_iter로 집계)

실행: 이 폴더에서 python -X utf8 scan.py [config 경로]
- 기본 config는 형제 config.json (H-matrix, LLR matrix, seed, t 격자, 프레임 수)
- t마다 채널 출력을 한 번 만들어 모든 디코더에 같은 입력을 먹인다
- 결과: 콘솔 표 + Sim_Output/{시각}_ulpbf_scan/scan_results.csv
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
        raise SystemExit("상위 폴더에서 2_LDPC_base/src를 찾지 못함")
    _root = _parent
_base_root = os.path.join(_root, "2_LDPC_base")
if _base_root not in sys.path:
    sys.path.insert(0, _base_root)
if EXPERIMENT_DIR not in sys.path:
    sys.path.insert(0, EXPERIMENT_DIR)

from src import channel as chan
from src import encoder
from src.decoder import BaseDecoder
from src.llr_matrix import LLRMatrix
from src.pcm import QCCode
from src.run import load_config

from decoder import ULPBF1PassDecoder


class ULPBFOffset1Decoder(ULPBF1PassDecoder):
    THRESHOLD_OFFSET = 1


class ULPBFOffset2Decoder(ULPBF1PassDecoder):
    THRESHOLD_OFFSET = 2


class ULPBFMixADecoder(ULPBF1PassDecoder):
    """혼합 문턱: dv 11만 한 칸 낮춤 (검사 공유 충돌 1회까지 구제).
    작은 dv 열은 T=dv를 유지해 과플립을 막는다."""
    T_BY_DV = {11: 10}


class ULPBFMixBDecoder(ULPBF1PassDecoder):
    """혼합 문턱: dv 11은 10, dv 4는 3. dv 2와 3은 T=dv 유지."""
    T_BY_DV = {11: 10, 4: 3}


def _make_point_channel_outputs(code, t, seed, total_frames, frames_per_batch):
    """한 포인트의 채널 출력 배치 목록. 난수 스트림 파생은 src.run.run_experiment와
    같다 ([seed, 채널 인덱스 0, int(1e6*t)]) 그래서 같은 config의 표준 하니스
    실행과 같은 잡음 실현을 쓴다."""
    random_generator = np.random.default_rng([seed, 0, int(1e6 * t)])
    outputs = []
    remaining = total_frames
    while remaining > 0:
        batch = min(frames_per_batch, remaining)
        msg = encoder.generate_message(code, batch, random_generator)
        cw = encoder.encode(msg, code)
        outputs.append(chan.fixed_error_channel(code, cw, t, random_generator))
        remaining -= batch
    return outputs


def _run_decoder_over(decoder, channel_outputs, max_iter):
    """배치 목록 전체를 복호하고 (에러 수, iteration 합, 프레임 수)를 돌려준다.
    iteration 합은 성공 프레임의 수렴 iteration + 실패 프레임 수 * max_iter
    (sim.py의 집계 방식과 동일)."""
    errors = 0
    iteration_sum = 0
    frames = 0
    for channel_out in channel_outputs:
        result = decoder.decoder_main(channel_out)
        fail_count = int((~result["success"]).sum())
        errors += fail_count
        iteration_sum += (int(result["decode_success_iteration"].sum())
                          + fail_count * max_iter)
        frames += len(result["success"])
    return errors, iteration_sum, frames


def main(config_path=None):
    config_path = config_path or os.path.join(EXPERIMENT_DIR, "config.json")
    config = load_config(config_path)
    code = QCCode.load(config["H_matrix"])
    llr_matrix = LLRMatrix.load(config["decoder"]["llr_matrix"])
    seed = config["seed"]
    run_config = config["run"]
    total_frames = run_config["max_frames"]
    frames_per_batch = run_config["frames_per_batch"]
    t_grid = config["channels"][0]["points"]
    max_iter = llr_matrix.max_iter

    baseline = BaseDecoder(code, llr_matrix=llr_matrix)
    ulpbf_variants = {
        "T=dv": ULPBF1PassDecoder(code, llr_matrix=llr_matrix),
        "T=dv-1": ULPBFOffset1Decoder(code, llr_matrix=llr_matrix),
        "T=dv-2": ULPBFOffset2Decoder(code, llr_matrix=llr_matrix),
        "T=mixA": ULPBFMixADecoder(code, llr_matrix=llr_matrix),
        "T=mixB": ULPBFMixBDecoder(code, llr_matrix=llr_matrix),
    }

    print(f"code: base {code.M_b}x{code.N_b}, z={code.z}, N={code.N}, K={code.K}")
    print(f"LLR matrix: {os.path.basename(config['decoder']['llr_matrix'])} "
          f"(max_iter={max_iter})")
    print(f"seed={seed}, 포인트당 {total_frames} 프레임, "
          f"frames_per_batch={frames_per_batch}")
    for name, dec in ulpbf_variants.items():
        t_by_dv = {int(dv): int(dec._col_T[j])
                   for j, dv in enumerate(code.col_deg)}
        print(f"  {name}: T[dv] = {t_by_dv}")
    print()

    header = ["t", "decoder", "frames",
              "s1_crc_pass", "s1_syn_zero", "s1_genie_ok",
              "fail_frames", "fail_misflip_mean", "fail_missed_mean",
              "fail_residual_mean", "crc_false_pass", "crc_pass_syn_nonzero",
              "syn_zero_genie_fail",
              "two_stage_errors", "two_stage_fer",
              "baseline_errors", "baseline_fer",
              "fallback_iter_sum", "baseline_iter_sum", "minsum_iter_ratio"]
    rows = []
    for t in t_grid:
        point_start = time.time()
        channel_outputs = _make_point_channel_outputs(
            code, t, seed, total_frames, frames_per_batch)
        base_errors, base_iter_sum, frames = _run_decoder_over(
            baseline, channel_outputs, max_iter)
        print(f"[t={t:>3}] min-sum 단독: errors={base_errors}, "
              f"iter_sum={base_iter_sum} "
              f"({time.time() - point_start:.0f}s)")
        for name, dec in ulpbf_variants.items():
            dec.reset_stats()
            errors, _, _ = _run_decoder_over(dec, channel_outputs, max_iter)
            st = dec.stats
            fail_frames = st["fail_frames"]
            row = {
                "t": t, "decoder": name, "frames": frames,
                "s1_crc_pass": st["stage1_crc_pass"],
                "s1_syn_zero": st["stage1_syn_zero"],
                "s1_genie_ok": st["stage1_genie_ok"],
                "fail_frames": fail_frames,
                "fail_misflip_mean": (st["fail_misflip_sum"] / fail_frames
                                      if fail_frames else 0.0),
                "fail_missed_mean": (st["fail_missed_sum"] / fail_frames
                                     if fail_frames else 0.0),
                "fail_residual_mean": (st["fail_residual_sum"] / fail_frames
                                       if fail_frames else 0.0),
                "crc_false_pass": st["crc_false_pass"],
                "crc_pass_syn_nonzero": st["crc_pass_syn_nonzero"],
                "syn_zero_genie_fail": st["syn_zero_genie_fail"],
                "two_stage_errors": errors,
                "two_stage_fer": errors / frames,
                "baseline_errors": base_errors,
                "baseline_fer": base_errors / frames,
                "fallback_iter_sum": st["fallback_iter_sum"],
                "baseline_iter_sum": base_iter_sum,
                "minsum_iter_ratio": (st["fallback_iter_sum"] / base_iter_sum
                                      if base_iter_sum else 0.0),
            }
            rows.append(row)
            print(f"        {name:7s}: 1단 성공(CRC) {row['s1_crc_pass']:4d}"
                  f"/{frames} (syn0 {row['s1_syn_zero']}, "
                  f"genie {row['s1_genie_ok']}), "
                  f"실패 오플립/누락/잔여 = {row['fail_misflip_mean']:.2f}"
                  f"/{row['fail_missed_mean']:.2f}"
                  f"/{row['fail_residual_mean']:.2f}, "
                  f"거짓통과 {row['crc_false_pass']} "
                  f"(parity잔여수용 {row['crc_pass_syn_nonzero']}), "
                  f"2단 err {errors} (기준 {base_errors}), "
                  f"min-sum iter비 {row['minsum_iter_ratio']:.3f}")
        print(f"        포인트 소요 {time.time() - point_start:.0f}s")

    stamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    out_dir = os.path.join(EXPERIMENT_DIR, "Sim_Output", f"{stamp}_ulpbf_scan")
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "scan_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"\nsaved: {csv_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
