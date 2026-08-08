"""JSON 설정 기반 실험 진입점 (파라미터와 코드를 분리).

main()은 4단계로 구성된다:
  1. load_config    — JSON 파라미터 읽기 + 검증 (키맵, 필수값, 값 제약)
  2. setup          — H-matrix 로드, LLR matrix 로드, 디코더 구성
  3. run_experiment — msg 생성 -> encode(임시: all-zero 반환) -> channel -> decode 반복
  4. report         — 실행 폴더 생성 + 요약/CSV/로그/그림 저장

실행: 2_LDPC_light/에서 python -m LDPC_base.run config.json

JSON 구조:
  H_matrix: {"dir": 폴더, "file": 파일명} — 폴더와 파일명 분리 (Ref-C 포맷,
    폴더는 Input/H_matrix 고정 운용)
  decoder.type: 사용할 디코더 이름 (기본 "vanilla", Ideas/registry.py 등록 이름)
  decoder.use_input_llr_matrix: true(기본)면 LLR matrix 파일을 사용,
    false면 내부 균일 n-bit 양자화로 디코딩 (internal_quantize 설정 사용,
    llr_matrix 키는 있어도 무시)
  decoder.llr_matrix: {"dir": 폴더, "file": 파일명} — DAO LLR_MATRIX
    (use_input_llr_matrix=true일 때 필수).
    max_iter는 이 파일의 마지막 iter_end가 결정 (JSON에 max_iter를 두면 에러)
  decoder.internal_quantize: use_input_llr_matrix=false일 때 필수 —
    {"num_bits": 메시지 양자화 bit 수(sign 포함, 예: 6), "channel_llr": 채널 LLR
    magnitude(전 dv 공통), "max_iter": 최대 iteration(파일이 없으므로 여기서 지정),
    "mode": "HD"(기본)}
  seed: 실험 전체 난수 seed 하나 (기본 0). 채널·포인트별 난수 스트림은 여기서 파생
  channels: 채널 리스트 — 각 항목 {"type": rber|fixed_error|strong_error,
    "points": [...]}. strong_error는 "SER"/"SCR" 추가, 선택 키 "label"
  run.max_frame_errors: 이 프레임 에러 수에 도달하면 해당 포인트 측정 종료
  run.frames_per_batch: 한 번에 동시 복호하는 프레임 수 (속도와 메모리 조절용,
    결과에 영향 없음)
  run.stop_below_fer: 측정 FER가 이 값 미만이면 남은 포인트 측정 중단 (선택)
  run.print_progress: 진행 상황 콘솔 출력 여부 (기본 true)
  log: 분석 로그 선택 (전부 선택, 기본 꺼짐 — 켜면 속도 비용):
    csw_per_iter / bit_err_per_iter / bit_err_by_dv — iteration별 집계 CSV
    iter_histogram / fer_vs_iter — 수렴 iteration 분포와 "max_iter를 k로 줄였다면"의 FER
    fail_frame_detail — 실패 프레임별 잔여 에러·최종 CSW·dv별 분해
    fer_curve_png — FER 커브 그림 저장
  output.dir 하위에 실행마다 YYMMDD_HHMMSS_{라벨} 폴더를 만들어 결과 일체
  (config 사본, summary.txt, CSV, 로그)를 저장한다. 라벨은 output.label
  (없으면 첫 채널 type)

설정 검증: 키맵(허용 키 밖이면 에러) + 필수값 + 값 제약. "_"로 시작하는
키(예: _desc)는 설명용으로 검사에서 무시한다.
"""
import datetime
import json
import os
import shutil
import subprocess
import sys

import numpy as np

from . import channel as chan
from . import encoder
from .decoder import MinSumDecoder
from .llr_matrix import LLRMatrix
from .pcm import QCCode
from .sim import run_fer_point, save_csv

# 섹션별 허용 키 (키맵). "_" 시작 키는 설명용이라 검사 대상에서 제외된다.
_TOP_KEYS = {"H_matrix", "decoder", "channels", "run", "output", "seed", "log"}
_DECODER_KEYS = {"llr_matrix", "type", "use_input_llr_matrix", "internal_quantize"}
_INTERNAL_QUANTIZE_KEYS = {"num_bits", "channel_llr", "max_iter", "mode"}
_RUN_KEYS = {"max_frame_errors", "max_frames", "frames_per_batch",
             "stop_below_fer", "print_progress"}
_OUTPUT_KEYS = {"dir", "csv_prefix", "label"}
_LOG_KEYS = {"csw_per_iter", "bit_err_per_iter", "bit_err_by_dv",
             "iter_histogram", "fer_vs_iter", "fail_frame_detail", "fer_curve_png"}
_CHANNEL_KEYS = {
    "rber": {"type", "points", "label"},
    "fixed_error": {"type", "points", "label"},
    "strong_error": {"type", "points", "label", "SER", "SCR"},
}
# JSON log 키 → decoder/sim 로그 항목
_LOG_TO_ITEM = {"csw_per_iter": "csw", "bit_err_per_iter": "bit_err",
                "bit_err_by_dv": "bit_err_by_dv", "fail_frame_detail": "fail_detail"}


def _visible(d):
    """'_'로 시작하는 설명용 키(예: _desc)를 제외한 키 집합."""
    return {k for k in d if not k.startswith("_")}


def _check_keys(section, d, allowed):
    unknown_keys = _visible(d) - allowed
    if unknown_keys:
        raise ValueError(
            f"config [{section}]에 알 수 없는 키 {sorted(unknown_keys)} — "
            f"허용 키: {sorted(allowed)}")


def _require(section, d, key):
    if key not in d or d[key] is None:
        raise ValueError(f"config [{section}] {key} 없음 또는 null — 필수 값")
    return d[key]


def _check_int(section, key, value, min_value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"config [{section}] {key}={value!r} — 정수여야 함")
    if value < min_value:
        raise ValueError(f"config [{section}] {key}={value} — {min_value} 이상이어야 함")
    return value


def _path_pair(section, d, base_dir):
    """{"dir": 폴더, "file": 파일명} 객체를 경로로 결합 (폴더와 파일명 분리 수용).
    상대경로는 config 파일 위치 기준."""
    if not isinstance(d, dict):
        raise ValueError(
            f'config [{section}] — {{"dir": 폴더, "file": 파일명}} 객체여야 함 (현재 {d!r})')
    _check_keys(section, d, {"dir", "file"})
    path = os.path.join(_require(section, d, "dir"), _require(section, d, "file"))
    return path if os.path.isabs(path) else os.path.join(base_dir, path)


def _check_channel(index, channel_config):
    """channels[index] 항목 검증: 키맵, 필수값(type/points, strong_error는 SER/SCR),
    포인트 값 제약 (rber: 0<p<0.5 실수, 그 외: 0 이상 정수)."""
    section = f"channels[{index}]"
    if not isinstance(channel_config, dict):
        raise ValueError(f"config [{section}] — 객체여야 함")
    channel_type = _require(section, channel_config, "type")
    if channel_type not in chan.CHANNELS:
        raise ValueError(
            f"config [{section}] type={channel_type!r} — "
            f"{sorted(chan.CHANNELS)} 중 하나여야 함")
    _check_keys(section, channel_config, _CHANNEL_KEYS[channel_type])
    points = _require(section, channel_config, "points")
    if not isinstance(points, list):
        points = [points]
        channel_config["points"] = points
    if not points or any(p is None for p in points):
        raise ValueError(f"config [{section}] points — 비어 있지 않아야 하고 null 불가")
    for point in points:
        if channel_type == "rber":
            if (isinstance(point, bool) or not isinstance(point, (int, float))
                    or not 0.0 < point < 0.5):
                raise ValueError(
                    f"config [{section}] points의 {point!r} — RBER는 0 < p < 0.5 실수여야 함")
        else:
            if isinstance(point, bool) or not isinstance(point, int) or point < 0:
                raise ValueError(
                    f"config [{section}] points의 {point!r} — 에러 비트 수는 0 이상 정수여야 함")
    if channel_type == "strong_error":
        for key in ("SER", "SCR"):
            value = _require(section, channel_config, key)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not 0.0 <= value <= 1.0):
                raise ValueError(f"config [{section}] {key}={value!r} — 0~1 범위 수여야 함")


def load_config(path):
    """실험 파라미터 JSON 로드 + 검증 (키맵/필수값/값 제약 — 모듈 docstring 참조).
    상대경로는 config 파일 위치 기준으로 해석. channels[].points는 스칼라도
    허용하며 리스트로 정규화한다."""
    with open(path, encoding="utf-8") as f:
        config = json.load(f)

    base_dir = os.path.dirname(os.path.abspath(path))

    if not isinstance(config, dict):
        raise ValueError(f"{path}: config 최상위가 객체가 아님")
    _check_keys("최상위", config, _TOP_KEYS)

    for section in ("decoder", "run", "output", "log"):  # 섹션이 null이면 여기서 지목
        if section in config and not isinstance(config[section], dict):
            raise ValueError(f"config [{section}] — 객체여야 함 (현재 {config[section]!r})")

    config["H_matrix"] = _path_pair("H_matrix", _require("최상위", config, "H_matrix"),
                                    base_dir)

    decoder_config = config.setdefault("decoder", {})
    if "max_iter" in decoder_config:
        raise ValueError(
            "decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(또는 "
            "internal_quantize.max_iter)이 결정")
    _check_keys("decoder", decoder_config, _DECODER_KEYS)
    use_input_llr_matrix = decoder_config.setdefault("use_input_llr_matrix", True)
    if not isinstance(use_input_llr_matrix, bool):
        raise ValueError(
            f"config [decoder] use_input_llr_matrix={use_input_llr_matrix!r} — true/false여야 함")
    if use_input_llr_matrix:
        decoder_config["llr_matrix"] = _path_pair(
            "decoder.llr_matrix", _require("decoder", decoder_config, "llr_matrix"), base_dir)
    else:
        internal_quantize = _require("decoder", decoder_config, "internal_quantize")
        if not isinstance(internal_quantize, dict):
            raise ValueError("config [decoder.internal_quantize] — 객체여야 함")
        _check_keys("decoder.internal_quantize", internal_quantize, _INTERNAL_QUANTIZE_KEYS)
        _check_int("decoder.internal_quantize", "num_bits",
                   _require("decoder.internal_quantize", internal_quantize, "num_bits"), 2)
        _check_int("decoder.internal_quantize", "channel_llr",
                   _require("decoder.internal_quantize", internal_quantize, "channel_llr"), 1)
        _check_int("decoder.internal_quantize", "max_iter",
                   _require("decoder.internal_quantize", internal_quantize, "max_iter"), 1)
        mode = internal_quantize.setdefault("mode", "HD")
        if mode not in ("HD", "2SD", "3SD"):
            raise ValueError(
                f"config [decoder.internal_quantize] mode={mode!r} — HD/2SD/3SD 중 하나여야 함")
    decoder_type = decoder_config.setdefault("type", "vanilla")
    if not isinstance(decoder_type, str) or not decoder_type:
        raise ValueError(
            f"config [decoder] type={decoder_type!r} — 아이디어 이름 문자열이어야 함")

    config["seed"] = _check_int("최상위", "seed", config.get("seed", 0), 0)

    output_config = config.setdefault("output", {})
    _check_keys("output", output_config, _OUTPUT_KEYS)
    output_config.setdefault("dir", os.path.join(base_dir, "Sim_Output"))
    if not os.path.isabs(output_config["dir"]):
        output_config["dir"] = os.path.join(base_dir, output_config["dir"])

    run_config = config.setdefault("run", {})
    _check_keys("run", run_config, _RUN_KEYS)
    _check_int("run", "max_frame_errors", run_config.get("max_frame_errors", 50), 1)
    _check_int("run", "max_frames", run_config.get("max_frames", 20000), 1)
    _check_int("run", "frames_per_batch", run_config.get("frames_per_batch", 128), 1)
    stop_below_fer = run_config.get("stop_below_fer")
    if stop_below_fer is not None and (isinstance(stop_below_fer, bool)
                                       or not isinstance(stop_below_fer, (int, float))
                                       or stop_below_fer <= 0):
        raise ValueError(
            f"config [run] stop_below_fer={stop_below_fer!r} — 0보다 큰 수 또는 null")

    log_config = config.setdefault("log", {})
    _check_keys("log", log_config, _LOG_KEYS)
    for key in _visible(log_config):
        if not isinstance(log_config[key], bool):
            raise ValueError(f"config [log] {key}={log_config[key]!r} — true/false여야 함")

    channels = _require("최상위", config, "channels")
    if isinstance(channels, dict):          # 단일 항목은 리스트로 정규화
        channels = [channels]
        config["channels"] = channels
    if not isinstance(channels, list) or not channels:
        raise ValueError("config channels — 비어 있지 않은 리스트여야 함")
    for index, channel_config in enumerate(channels):
        _check_channel(index, channel_config)
    return config


def _resolve_decoder_class(decoder_type):
    """decoder.type → 디코더 클래스 (Ideas/registry.py 조회).

    Ideas 패키지는 실행 위치 기준으로 import되므로 2_LDPC_light/에서
    `python -m LDPC_base.run ...`으로 실행한다. Ideas가 없는 환경에서는
    "vanilla"가 정본(MinSumDecoder)으로 동작한다."""
    import importlib
    try:
        registry = importlib.import_module("Ideas.registry")
    except ImportError:
        if decoder_type == "vanilla":
            return MinSumDecoder
        raise ValueError(
            f"decoder.type={decoder_type!r} — Ideas 패키지를 찾을 수 없음 "
            "(2_LDPC_light/에서 실행했는지 확인)")
    if decoder_type not in registry.DECODERS:
        raise ValueError(
            f"decoder.type={decoder_type!r} — Ideas/registry.py 미등록 "
            f"(등록된 이름: {sorted(registry.DECODERS)})")
    module_name, class_name = registry.DECODERS[decoder_type].split(":")
    return getattr(importlib.import_module(module_name), class_name)


def setup(config):
    """H-matrix를 로드하고 LLR matrix를 준비(파일 로드 또는 내부 합성)한 뒤
    decoder.type의 디코더를 구성한다. 파일이 없으면 준비하라는 에러를 낸다
    (이 함수는 생성하지 않음)."""
    h_matrix_path = config["H_matrix"]
    if not os.path.exists(h_matrix_path):
        raise FileNotFoundError(f"{h_matrix_path} 없음 — H-matrix를 먼저 준비할 것")
    code = QCCode.load(h_matrix_path)
    if config["decoder"]["use_input_llr_matrix"]:
        llr_matrix = LLRMatrix.load(config["decoder"]["llr_matrix"])
    else:
        internal_quantize = config["decoder"]["internal_quantize"]
        llr_matrix = LLRMatrix.make_internal_uniform_matrix(
            num_bits=internal_quantize["num_bits"],
            channel_llr=internal_quantize["channel_llr"],
            max_iter=internal_quantize["max_iter"],
            dv_max=int(code.col_deg.max()),
            mode=internal_quantize["mode"])
    decoder_class = _resolve_decoder_class(config["decoder"]["type"])
    decoder = decoder_class(code, llr_matrix=llr_matrix)
    return code, decoder


def _experiment_summary_lines(code, decoder, config):
    """실험 요약 (setup 직후 콘솔과 summary.txt 공용):
    부호 정보, LLR matrix 정보, 디코더 정보, 읽은 config 정보."""
    channels_desc = ", ".join(
        f"{channel_config['type']}{channel_config['points']}"
        for channel_config in config["channels"])
    log_on = sorted(key for key in _LOG_KEYS if config["log"].get(key))
    run_config = config["run"]
    return [
        code.summary(),
        decoder.llr_matrix.summary(),
        f"decoder: {config['decoder']['type']} "
        f"({type(decoder).__module__}.{type(decoder).__name__}), "
        f"max_iter={decoder.max_iter}",
        f"config: seed={config['seed']} | channels: {channels_desc}",
        f"run: max_frame_errors={run_config.get('max_frame_errors', 50)}, "
        f"max_frames={run_config.get('max_frames', 20000)}, "
        f"frames_per_batch={run_config.get('frames_per_batch', 128)}, "
        f"stop_below_fer={run_config.get('stop_below_fer')}",
        f"log: {', '.join(log_on) if log_on else '(전부 꺼짐)'}",
    ]


def _check_channel_mode(decoder, channel_type):
    """디코딩 모드(HD/2SD/3SD)와 채널의 호환 확인. 측정 시작 전에 전 채널에 대해
    호출한다 (뒤 채널의 불일치로 앞 채널 측정이 버려지는 일 방지)."""
    mode = decoder.llr_matrix.mode
    if mode not in chan.CHANNEL_MODES[channel_type]:
        raise ValueError(
            f"channel {channel_type}은 {chan.CHANNEL_MODES[channel_type]} 전용 — "
            f"현재 디코딩 모드 {mode} (LLR matrix 파일명 확인)")
    return mode


def _make_channel_fn(code, decoder, channel_config, point):
    """채널 함수 생성: msg 생성 -> encode -> 채널. 디코딩 모드(HD/2SD/3SD)는
    LLR matrix에서 오고, 채널이 그 모드를 지원하는지 확인한다."""
    channel_type = channel_config["type"]
    mode = _check_channel_mode(decoder, channel_type)
    extra_args = {}
    if channel_type == "strong_error":
        extra_args = {"scr": channel_config["SCR"], "ser": channel_config["SER"]}

    def channel_fn(batch, random_generator):
        msg = encoder.generate_message(code, batch, random_generator)
        cw = encoder.encode(msg, code)
        return chan.CHANNELS[channel_type](code, cw, point, random_generator,
                                           mode=mode, **extra_args)

    return channel_fn


def run_experiment(code, decoder, config):
    """channels 리스트의 각 채널에 대해 각 포인트를 max_frame_errors 도달 또는
    max_frames 소진까지 측정한다. 반환: [(라벨, [포인트별 결과, ...]), ...].

    난수: 최상위 seed 하나에서 [seed, 채널 인덱스, 포인트]로 스트림을 파생 —
    포인트 간, 채널 간 독립이며 같은 seed면 재현된다."""
    run_config = config["run"]
    max_frame_errors = run_config.get("max_frame_errors", 50)
    max_frames = run_config.get("max_frames", 20000)
    frames_per_batch = run_config.get("frames_per_batch", 128)
    stop_below_fer = run_config.get("stop_below_fer")
    print_progress = run_config.get("print_progress", True)
    seed = config["seed"]
    log_config = config["log"]
    log_items = {item for key, item in _LOG_TO_ITEM.items() if log_config.get(key)}

    for channel_config in config["channels"]:    # 전 채널 모드 호환 사전 확인
        _check_channel_mode(decoder, channel_config["type"])

    results = []
    used_labels = set()
    for channel_index, channel_config in enumerate(config["channels"]):
        channel_type = channel_config["type"]
        # 라벨은 CSV 파일명에 쓰인다. 같은 type의 채널이 여러 개면 파일명이 겹쳐
        # 덮어쓰므로 번호 접미사(_2, _3, ...)로 구분한다.
        label = channel_config.get("label", channel_type)
        if label in used_labels:
            suffix = 2
            while f"{label}_{suffix}" in used_labels:
                suffix += 1
            label = f"{label}_{suffix}"
        used_labels.add(label)
        if print_progress:
            print(f"== channel={channel_type} ({label}) ==")
        point_results = []
        for point in channel_config["points"]:
            random_generator = np.random.default_rng([seed, channel_index, int(1e6 * point)])
            channel_fn = _make_channel_fn(code, decoder, channel_config, point)
            point_result = run_fer_point(
                code, channel_fn, decoder, random_generator,
                max_frame_errors=max_frame_errors, max_frames=max_frames,
                frames_per_batch=frames_per_batch, print_progress=print_progress,
                log=log_items or None)
            point_result["param"] = point
            point_results.append(point_result)
            if stop_below_fer is not None and point_result["fer"] < stop_below_fer:
                break
        results.append((label, point_results))
    return results


def _git_commit_hash():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=10).stdout.strip() or "(git 없음)"
    except OSError:
        return "(git 없음)"


def _dv_labels(llr_matrix):
    """dv 구간별 열 이름: dv_from==dv_to면 dv{값}, 아니면 dv{from}-{to}."""
    return [f"dv{f}" if f == t else f"dv{f}-{t}"
            for f, t in zip(llr_matrix.dv_from, llr_matrix.dv_to)]


def _write_iter_log(path, point_result, log_config, dv_labels):
    """iteration별 집계 CSV: 켠 항목만 열로 (평균 = 합/활성 프레임 수)."""
    import csv
    totals = point_result["iteration_totals"]
    active_frames = totals["active_frames"]
    num_rows = int(np.max(np.nonzero(active_frames)[0])) + 1 if active_frames.any() else 0
    header = ["iter", "active_frames"]
    if log_config.get("csw_per_iter"):
        header.append("csw_mean")
    if log_config.get("bit_err_per_iter"):
        header.append("bit_err_mean")
    if log_config.get("bit_err_by_dv"):
        header += [f"bit_err_{name}_mean" for name in dv_labels]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for k in range(num_rows):
            active = int(active_frames[k])
            row = [str(k + 1), str(active)]
            if log_config.get("csw_per_iter"):
                row.append(f"{totals['csw_sum'][k] / max(active, 1):.2f}")
            if log_config.get("bit_err_per_iter"):
                row.append(f"{totals['bit_err_sum'][k] / max(active, 1):.2f}")
            if log_config.get("bit_err_by_dv"):
                row += [f"{totals['bit_err_by_dv_sum'][k][d] / max(active, 1):.3f}"
                        for d in range(len(dv_labels))]
            writer.writerow(row)


def _write_iter_hist_log(path, point_result, log_config):
    """수렴 iteration 히스토그램 + fer_vs_iter (max_iter를 k로 줄였다면의 FER)."""
    import csv
    hist = point_result["iter_hist"]
    frames = point_result["frames"]
    header = ["iter"]
    if log_config.get("iter_histogram"):
        header.append("success_at_iter")
    if log_config.get("fer_vs_iter"):
        header.append("fer_if_max_iter_k")
    cumulative = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for k in range(1, len(hist)):
            cumulative += int(hist[k])
            row = [str(k)]
            if log_config.get("iter_histogram"):
                row.append(str(int(hist[k])))
            if log_config.get("fer_vs_iter"):
                row.append(f"{1.0 - cumulative / frames:.6e}")
            writer.writerow(row)


def _write_fail_log(path, point_result, dv_labels):
    """실패 프레임 상세: 프레임 번호, 잔여 에러 bit, 최종 CSW, dv별 잔여 에러."""
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "final_err_bits", "final_csw"]
                        + [f"err_{name}" for name in dv_labels])
        for frame, err_bits, csw, by_dv in point_result["fail_frame_details"]:
            writer.writerow([str(frame), str(err_bits), str(csw)]
                            + [str(v) for v in by_dv])


def _plot_fer_curves(path, results):
    """FER 커브 그림 (라벨별 한 줄, 0-error 포인트는 상한 마커)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for label, point_results in results:
        xs = [r["param"] for r in point_results]
        fer = [r["fer"] if r["errors"] else 0.5 / r["frames"] for r in point_results]
        ax.plot(xs, fer, "-o", label=label)
        for x, f, point_result in zip(xs, fer, point_results):
            if not point_result["errors"]:
                ax.plot(x, f, "v", markerfacecolor="white", markersize=8)
    ax.set_yscale("log")
    ax.set_xlabel("point")
    ax.set_ylabel("FER")
    ax.grid(True, which="both", linewidth=0.5, linestyle="--")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def report(results, config, config_path, code, decoder):
    """실행 폴더 생성(YYMMDD_HHMMSS_{라벨}) 후 결과 일체 저장:
    config 사본, summary.txt(실험 요약 + 결과 + git 커밋 해시), FER CSV, 로그 CSV,
    FER 커브 그림."""
    output_config = config["output"]
    log_config = config["log"]
    run_label = output_config.get("label", config["channels"][0]["type"])
    stamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    run_dir = os.path.join(output_config["dir"], f"{stamp}_{run_label}")
    os.makedirs(run_dir, exist_ok=True)
    shutil.copy(config_path, os.path.join(run_dir, "config.json"))

    dv_labels = _dv_labels(decoder.llr_matrix)
    lines = [f"run: {stamp}_{run_label}", f"code commit: {_git_commit_hash()}", ""]
    lines += _experiment_summary_lines(code, decoder, config)
    lines.append("")
    prefix = output_config.get("csv_prefix", "fer")
    for label, point_results in results:
        csv_path = os.path.join(run_dir, f"{prefix}_{label}.csv")
        save_csv(point_results, csv_path, param_name="param")
        print(f"saved: {csv_path}")
        for point_result in point_results:
            lines.append(
                f"{label} point={point_result['param']}: FER={point_result['fer']:.3e} "
                f"BER={point_result['post_fec_ber']:.3e} "
                f"[{point_result['errors']}/{point_result['frames']}] "
                f"avg_decode_success_iteration="
                f"{point_result['avg_decode_success_iteration']:.2f} "
                f"({point_result['sec']:.1f}s)")
            if "iteration_totals" in point_result and (
                    log_config.get("csw_per_iter") or log_config.get("bit_err_per_iter")
                    or log_config.get("bit_err_by_dv")):
                _write_iter_log(
                    os.path.join(run_dir, f"log_iter_{label}_p{point_result['param']}.csv"),
                    point_result, log_config, dv_labels)
            if log_config.get("iter_histogram") or log_config.get("fer_vs_iter"):
                _write_iter_hist_log(
                    os.path.join(run_dir,
                                 f"log_iter_hist_{label}_p{point_result['param']}.csv"),
                    point_result, log_config)
            if "fail_frame_details" in point_result:
                _write_fail_log(
                    os.path.join(run_dir, f"log_fail_{label}_p{point_result['param']}.csv"),
                    point_result, dv_labels)
    if log_config.get("fer_curve_png"):
        png_path = os.path.join(run_dir, "fer_curves.png")
        _plot_fer_curves(png_path, results)
        print(f"saved: {png_path}")
    with open(os.path.join(run_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"run dir: {run_dir}")
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("usage: python -m LDPC_base.run <config.json>")

    config = load_config(argv[0])
    code, decoder = setup(config)
    for line in _experiment_summary_lines(code, decoder, config):
        print(line)
    results = run_experiment(code, decoder, config)
    report(results, config, argv[0], code, decoder)


if __name__ == "__main__":
    main()
