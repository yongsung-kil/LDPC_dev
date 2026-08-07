"""FER 시뮬레이션 하니스: 배치 반복 → genie 판정 집계 → FER/평균 iteration/로그 집계."""
import numbers
import time

import numpy as np

from .decoder import MinSumDecoder, LOG_ITEMS


def run_fer_point(code, channel_fn, dec: MinSumDecoder, rng, max_frame_errors=50,
                  max_frames=20000, frames_per_batch=128, verbose=False, log=None):
    """한 채널 조건의 FER 측정.

    channel_fn(batch, rng) -> 채널 출력 (channel.py dict).
    프레임 에러 수가 max_frame_errors에 도달하거나 max_frames 소진 시 종료.
    log: decoder.LOG_ITEMS 부분집합 — 켠 항목만 iteration별로 집계 (속도 비용).

    반환 dict: frames, errors, fer, post_fec_ber, avg_decode_success_iteration, sec, fps,
      iter_hist ((max_iter+1,) — [k]=iteration k에 성공한 프레임 수, [0]=실패 프레임 수),
      log 지정 시 log_agg {active, csw_sum, err_sum, err_by_dv_sum} (iteration별 합계
      배열 — 평균은 sum/active로 소비측 계산), fail_detail 시 fail_rows
      [(프레임 번호, 잔여 에러 bit, 최종 CSW, dv별 잔여 에러), ...].
    """
    # run.py load_config 검증을 우회하는 직접 호출 대비 최소 가드 (리뷰 F19 —
    # frames_per_batch가 정수 0이면 무한 대기가 된다)
    for name, v in (("max_frame_errors", max_frame_errors),
                    ("max_frames", max_frames), ("frames_per_batch", frames_per_batch)):
        if isinstance(v, bool) or not isinstance(v, numbers.Integral) or v < 1:
            raise ValueError(f"{name}={v!r} — 1 이상의 정수여야 함")
    log = frozenset() if log is None else frozenset(log)
    unknown = log - LOG_ITEMS
    if unknown:
        raise ValueError(f"log 항목 {sorted(unknown)} 미지원 — 허용: {sorted(LOG_ITEMS)}")

    max_iter = dec.max_iter
    num_dv = dec.llr_matrix.num_dv
    frames = errors = 0
    iter_sum = 0          # 성공 프레임의 수렴 iteration 합
    err_bit_total = 0     # 전 프레임 잔여 에러 bit 합 (post-FEC BER 분자)
    iter_hist = np.zeros(max_iter + 1, np.int64)
    agg_active = np.zeros(max_iter, np.int64)
    agg_csw = np.zeros(max_iter, np.int64)
    agg_err = np.zeros(max_iter, np.int64)
    agg_err_dv = np.zeros((max_iter, num_dv), np.int64)
    fail_rows = []

    t0 = time.time()
    while frames < max_frames and errors < max_frame_errors:
        b = min(frames_per_batch, max_frames - frames)
        res = dec.decoder_main(channel_fn(b, rng), log=log or None)
        success = res["success"]
        errors += int((~success).sum())
        iter_sum += int(res["decode_success_iteration"].sum())
        err_bit_total += int(res["final_err_bits"].sum())
        np.add.at(iter_hist, res["decode_success_iteration"], 1)   # 실패 프레임(0)은 [0]에 집계
        if log:
            n_it = len(res["log_active"])
            agg_active[:n_it] += res["log_active"]
            if "csw" in log:
                agg_csw[:n_it] += res["log_csw_sum"]
            if "bit_err" in log:
                agg_err[:n_it] += res["log_err_sum"]
            if "bit_err_by_dv" in log:
                agg_err_dv[:n_it] += res["log_err_by_dv_sum"]
            if "fail_detail" in log:
                for k in np.flatnonzero(~success):
                    fail_rows.append((frames + int(k), int(res["final_err_bits"][k]),
                                      int(res["final_csw"][k]),
                                      res["final_err_by_dv"][k].tolist()))
        frames += b
    elapsed = time.time() - t0
    fer = errors / frames
    point = {
        "frames": frames, "errors": errors, "fer": fer,
        "post_fec_ber": err_bit_total / (frames * code.N),
        "avg_decode_success_iteration": iter_sum / max(1, frames - errors),
        "sec": elapsed, "fps": frames / max(elapsed, 1e-9),
        "iter_hist": iter_hist,
    }
    if log:
        point["log_agg"] = {"active": agg_active, "csw_sum": agg_csw,
                            "err_sum": agg_err, "err_by_dv_sum": agg_err_dv}
        if "fail_detail" in log:
            point["fail_rows"] = fail_rows
    if verbose:
        print(f"  frames={frames:6d} errors={errors:4d} FER={fer:.3e} "
              f"BER={point['post_fec_ber']:.3e} "
              f"avg_decode_success_iteration={point['avg_decode_success_iteration']:.2f} ({point['fps']:.1f} f/s)")
    return point


def save_csv(results, path, param_name="param"):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([param_name, "fer", "post_fec_ber", "frames", "errors",
                    "avg_decode_success_iteration", "sec"])
        for r in results:
            w.writerow([r["param"], f"{r['fer']:.6e}", f"{r['post_fec_ber']:.6e}",
                        r["frames"], r["errors"], f"{r['avg_decode_success_iteration']:.3f}",
                        f"{r['sec']:.1f}"])
