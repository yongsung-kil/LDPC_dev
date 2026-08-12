"""FER 시뮬레이션 하니스: 배치 반복 → genie 판정 집계 → FER/평균 iteration/로그 집계."""
import numbers
import os
import sys
import time

import numpy as np

from .decoder import BaseDecoder, LOG_ITEMS


def _format_duration(seconds):
    """경과 시간을 hh:mm:ss로 표시. 100시간 이상이면 시 자릿수가 그대로 늘어난다
    (예: 123:45:06)."""
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _rewrite_file_tail(path, offset, text):
    """파일의 offset 이후를 text로 교체 (진행 줄을 제자리 갱신하는 용도)."""
    with open(path, "r+", encoding="utf-8") as f:
        f.seek(offset)
        f.truncate()
        f.write(text)


def run_fer_point(code, channel_fn, decoder: BaseDecoder, random_generator,
                  max_frame_errors=50, max_frames=20000, frames_per_batch=128,
                  print_progress=False, log=None, progress_label="",
                  progress_interval_frames=100, summary_path=None):
    """한 채널 조건의 FER 측정.

    channel_fn(batch, random_generator) -> 채널 출력 (channel.py dict).
    프레임 에러 수가 max_frame_errors에 도달하거나 max_frames 소진 시 종료.
    print_progress: 콘솔 출력 여부. 측정 중에는 progress_interval_frames 단위로
      진행 줄을 캐리지 리턴으로 같은 자리에 갱신하고 (터미널 출력일 때만),
      포인트가 끝나면 결과 한 줄을 남기고 줄바꿈한다.
    progress_label: 진행/결과 줄 머리의 "[채널 p=포인트]" 표기 내용
      (괄호는 이 함수가 붙이므로 내용만 전달, 예: "fixed_error p=200").
    progress_interval_frames: 진행 줄 갱신 간격 (프레임 단위, 기본 100).
    summary_path: 주면 진행 줄과 최종 결과 줄을 이 파일 끝에 실시간 반영한다
      (진행 줄은 갱신 간격마다 제자리 갱신되다가 최종 결과 줄로 대체된다).
    log: decoder.LOG_ITEMS 부분집합. 켠 항목만 iteration별로 집계 (속도 비용).

    반환 dict: frames, errors, fer, post_fec_ber (information bit 기준:
      정보 구간 잔여 에러 bit 합 / (frames * K)), avg_decoding_iteration
      (프레임당 평균 복호 iteration 수. 성공 프레임은 수렴 iteration, 실패 프레임은
      max_iter로 집계), sec, fps, ips (초당 합산 복호 iteration 수),
      summary_line (콘솔 결과 줄과 같은 문자열),
      iter_hist ((max_iter+1,) 배열로 [k]=iteration k에 성공한 프레임 수, [0]=실패 프레임 수),
      log 지정 시 iteration_totals {active_frames, csw_sum, bit_err_sum, bit_err_by_dv_sum}
      (iteration별 합계 배열이며, 평균은 합/active_frames로 소비측 계산),
      fail_detail 시 fail_frame_details
      [(프레임 번호, 잔여 에러 bit, 최종 CSW, dv별 잔여 에러), ...].
    """
    # run.py load_config 검증을 우회하는 직접 호출 대비 최소 가드
    # (frames_per_batch가 정수 0이면 무한 대기가 된다)
    for name, value in (("max_frame_errors", max_frame_errors),
                        ("max_frames", max_frames),
                        ("frames_per_batch", frames_per_batch),
                        ("progress_interval_frames", progress_interval_frames)):
        if isinstance(value, bool) or not isinstance(value, numbers.Integral) or value < 1:
            raise ValueError(f"{name}={value!r}: 1 이상의 정수여야 함")
    log = set() if log is None else set(log)
    unknown_log_items = log - LOG_ITEMS      # 허용 목록에 없는 항목 = 오타 검출
    if unknown_log_items:
        raise ValueError(
            f"log 항목 {sorted(unknown_log_items)} 미지원 (허용: {sorted(LOG_ITEMS)})")

    max_iter = decoder.max_iter
    num_dv = decoder.llr_matrix.num_dv
    frames = errors = 0
    success_iteration_sum = 0        # 성공 프레임의 수렴 iteration 합 (평균 계산용)
    total_residual_info_err_bits = 0  # 전 프레임 정보 구간 잔여 에러 bit 합 (post-FEC BER 분자)
    iter_hist = np.zeros(max_iter + 1, np.int64)
    # iteration별 합계 (배치를 넘어 누적하며, 평균은 합/활성 프레임 수로 소비측 계산)
    total_active_frames = np.zeros(max_iter, np.int64)
    total_csw = np.zeros(max_iter, np.int64)
    total_bit_err = np.zeros(max_iter, np.int64)
    total_bit_err_by_dv = np.zeros((max_iter, num_dv), np.int64)
    fail_frame_details = []          # 실패 프레임별 (번호, 잔여 에러, 최종 CSW, dv별)

    # 진행 줄 갱신(\r)은 터미널에서만 한다 (파일로 리다이렉트하면 최종 줄만 남긴다)
    show_live_progress = print_progress and sys.stdout.isatty()
    line_head = f" [{progress_label}] " if progress_label else "  "
    summary_offset = None
    if summary_path:
        if not os.path.exists(summary_path):
            open(summary_path, "w", encoding="utf-8").close()
        summary_offset = os.path.getsize(summary_path)
    next_progress_frames = progress_interval_frames
    start_time = time.time()
    while frames < max_frames and errors < max_frame_errors:
        batch = min(frames_per_batch, max_frames - frames)
        decode_result = decoder.decoder_main(channel_fn(batch, random_generator),
                                             log=log or None)
        success = decode_result["success"]
        errors += int((~success).sum())
        success_iteration_sum += int(decode_result["decode_success_iteration"].sum())
        total_residual_info_err_bits += int(decode_result["final_info_err_bits"].sum())
        np.add.at(iter_hist, decode_result["decode_success_iteration"], 1)  # 실패는 [0]
        if log:
            num_iterations_run = len(decode_result["log_active"])
            total_active_frames[:num_iterations_run] += decode_result["log_active"]
            if "csw" in log:
                total_csw[:num_iterations_run] += decode_result["log_csw_sum"]
            if "bit_err" in log:
                total_bit_err[:num_iterations_run] += decode_result["log_err_sum"]
            if "bit_err_by_dv" in log:
                total_bit_err_by_dv[:num_iterations_run] += \
                    decode_result["log_err_by_dv_sum"]
            if "fail_detail" in log:
                for k in np.flatnonzero(~success):
                    fail_frame_details.append(
                        (frames + int(k), int(decode_result["final_err_bits"][k]),
                         int(decode_result["final_csw"][k]),
                         decode_result["final_err_by_dv"][k].tolist()))
        frames += batch
        if (show_live_progress or summary_path) and frames >= next_progress_frames:
            elapsed_so_far = max(time.time() - start_time, 1e-9)
            iterations_so_far = success_iteration_sum + errors * max_iter
            progress_line = (
                f"{line_head}e/fr = {errors:4d}/{frames:<6d} "
                f"fer = {errors / frames:.2e} "
                f"ber = {total_residual_info_err_bits / (frames * code.K):.2e} "
                f"avg_iter = {iterations_so_far / frames:.1f} "
                f"({frames / elapsed_so_far:.1f} f/s, "
                f"{iterations_so_far / elapsed_so_far:.0f} it/s, "
                f"elapsed: {_format_duration(elapsed_so_far)})")
            if show_live_progress:
                print(f"\r{progress_line}", end="", flush=True)
            if summary_path:
                _rewrite_file_tail(summary_path, summary_offset, progress_line + "\n")
            next_progress_frames = ((frames // progress_interval_frames + 1)
                                    * progress_interval_frames)
    elapsed = time.time() - start_time
    fer = errors / frames
    # 합산 복호 iteration 수: 성공 프레임은 수렴 iteration, 실패 프레임은 max_iter
    total_decoding_iterations = success_iteration_sum + errors * max_iter
    point_result = {
        "frames": frames, "errors": errors, "fer": fer,
        "post_fec_ber": total_residual_info_err_bits / (frames * code.K),
        "avg_decoding_iteration": total_decoding_iterations / frames,
        "sec": elapsed, "fps": frames / max(elapsed, 1e-9),
        "ips": total_decoding_iterations / max(elapsed, 1e-9),
        "iter_hist": iter_hist,
    }
    if log:
        point_result["iteration_totals"] = {
            "active_frames": total_active_frames, "csw_sum": total_csw,
            "bit_err_sum": total_bit_err, "bit_err_by_dv_sum": total_bit_err_by_dv}
        if "fail_detail" in log:
            point_result["fail_frame_details"] = fail_frame_details
    point_result["summary_line"] = (
        f"{line_head}e/fr = {errors:4d}/{frames:<6d} fer = {fer:.2e} "
        f"ber = {point_result['post_fec_ber']:.2e} "
        f"avg_iter = {point_result['avg_decoding_iteration']:.1f} "
        f"({point_result['fps']:.1f} f/s, {point_result['ips']:.0f} it/s, "
        f"elapsed: {_format_duration(elapsed)})")
    if print_progress:
        print(("\r" if show_live_progress else "") + point_result["summary_line"])
    if summary_path:
        _rewrite_file_tail(summary_path, summary_offset,
                           point_result["summary_line"] + "\n")
    return point_result


def save_csv(point_results, path, param_name="param"):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([param_name, "fer", "post_fec_ber", "frames", "errors",
                         "avg_decoding_iteration", "sec"])
        for point_result in point_results:
            writer.writerow(
                [point_result["param"], f"{point_result['fer']:.6e}",
                 f"{point_result['post_fec_ber']:.6e}", point_result["frames"],
                 point_result["errors"],
                 f"{point_result['avg_decoding_iteration']:.3f}",
                 f"{point_result['sec']:.1f}"])
