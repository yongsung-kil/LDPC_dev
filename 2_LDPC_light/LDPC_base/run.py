"""JSON 설정 기반 실험 진입점 (파라미터와 코드를 분리).

main()은 4단계로만 구성된다:
  1. load_config    — JSON 파라미터 읽기 + 검증 (키맵, 필수값, 값 제약)
  2. setup          — H-matrix 로드, LLR matrix 로드, 디코더 구성
  3. run_experiment — msg 생성 -> encode(임시: all-zero 반환) -> channel -> decode 반복
  4. report         — 실행 폴더 생성 + 요약/CSV/로그/그림 저장

실행: python -m LDPC_base.run <config.json>

JSON 구조 (2026-08-07 개편 2차 — 폴더/파일 분리, seed 단일화, log 섹션):
  H_matrix: {"dir": 폴더, "file": 파일명} — 폴더와 파일명 분리 (Ref-C 포맷,
    폴더는 Input/H_matrix 고정 운용)
  decoder.llr_matrix: {"dir": 폴더, "file": 파일명} — DAO LLR_MATRIX (필수).
    max_iter는 이 파일의 마지막 iter_end가 결정 (JSON에 max_iter를 두면 에러)
  seed: 실험 전체 난수 seed 하나 (기본 0). 채널·포인트별 스트림은 여기서 파생
  channels: 채널 리스트 — 각 항목 {"type": rber|fixed_error|strong_error,
    "points": [...]}. strong_error는 "SER"/"SCR" 추가, 선택 키 "label"
  run.max_frame_errors: 이 프레임 에러 수에 도달하면 해당 포인트 측정 종료
  run.frames_per_batch: 한 번에 동시 복호하는 프레임 수 (속도와 메모리 조절용,
    결과에 영향 없음)
  run.stop_below_fer: 측정 FER가 이 값 미만이면 남은 포인트 측정 중단 (선택)
  log: 분석 로그 선택 (전부 선택, 기본 꺼짐 — 켜면 속도 비용):
    csw_per_iter / bit_err_per_iter / bit_err_by_dv — iteration별 집계 CSV
    iter_histogram / fer_vs_iter — 수렴 iteration 분포와 "max_iter를 k로 줄였다면"의 FER
    fail_frame_detail — 실패 프레임별 잔여 에러·최종 CSW·dv별 분해
    fer_curve_png — FER 커브 그림 저장
  output.dir 하위에 실행마다 YYMMDD_HHMMSS_{라벨} 폴더를 만들어 결과 일체
  (config 사본, summary.txt, CSV, 로그)를 저장한다. 라벨은 output.label
  (없으면 첫 채널 type)

설정 검증: 키맵(허용 키 밖이면 에러) + 필수값 + 값 제약. "_"로 시작하는
키(예: _desc)는 설명용으로 검사에서 무시 (리뷰 F3/F19 후속, 사용자 확정).
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
_DECODER_KEYS = {"llr_matrix", "type"}
_RUN_KEYS = {"max_frame_errors", "max_frames", "frames_per_batch",
             "stop_below_fer", "verbose"}
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
    unknown = _visible(d) - allowed
    if unknown:
        raise ValueError(
            f"config [{section}]에 알 수 없는 키 {sorted(unknown)} — "
            f"허용 키: {sorted(allowed)}")


def _require(section, d, key):
    if key not in d or d[key] is None:
        raise ValueError(f"config [{section}] {key} 없음 또는 null — 필수 값")
    return d[key]


def _check_int(section, key, v, min_value):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"config [{section}] {key}={v!r} — 정수여야 함")
    if v < min_value:
        raise ValueError(f"config [{section}] {key}={v} — {min_value} 이상이어야 함")
    return v


def _path_pair(section, d, base_dir):
    """{"dir": 폴더, "file": 파일명} 객체를 경로로 결합 (폴더/파일 분리 수용 —
    사용자 확정 2026-08-07). 상대경로는 config 파일 위치 기준."""
    if not isinstance(d, dict):
        raise ValueError(
            f'config [{section}] — {{"dir": 폴더, "file": 파일명}} 객체여야 함 (현재 {d!r})')
    _check_keys(section, d, {"dir", "file"})
    path = os.path.join(_require(section, d, "dir"), _require(section, d, "file"))
    return path if os.path.isabs(path) else os.path.join(base_dir, path)


def _check_channel(i, ch):
    """channels[i] 항목 검증: 키맵, 필수값(type/points, strong_error는 SER/SCR),
    포인트 값 제약 (rber: 0<p<0.5 실수, 그 외: 0 이상 정수)."""
    section = f"channels[{i}]"
    if not isinstance(ch, dict):
        raise ValueError(f"config [{section}] — 객체여야 함")
    ch_type = _require(section, ch, "type")
    if ch_type not in chan.CHANNELS:
        raise ValueError(
            f"config [{section}] type={ch_type!r} — {sorted(chan.CHANNELS)} 중 하나여야 함")
    _check_keys(section, ch, _CHANNEL_KEYS[ch_type])
    points = _require(section, ch, "points")
    if not isinstance(points, list):
        points = [points]
        ch["points"] = points
    if not points or any(p is None for p in points):
        raise ValueError(f"config [{section}] points — 비어 있지 않아야 하고 null 불가")
    for p in points:
        if ch_type == "rber":
            if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0.0 < p < 0.5:
                raise ValueError(
                    f"config [{section}] points의 {p!r} — RBER는 0 < p < 0.5 실수여야 함")
        else:
            if isinstance(p, bool) or not isinstance(p, int) or p < 0:
                raise ValueError(
                    f"config [{section}] points의 {p!r} — 에러 비트 수는 0 이상 정수여야 함")
    if ch_type == "strong_error":
        for key in ("SER", "SCR"):
            v = _require(section, ch, key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0.0 <= v <= 1.0:
                raise ValueError(f"config [{section}] {key}={v!r} — 0~1 범위 수여야 함")


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

    for sec in ("decoder", "run", "output", "log"):      # 섹션이 null이면 여기서 지목
        if sec in config and not isinstance(config[sec], dict):
            raise ValueError(f"config [{sec}] — 객체여야 함 (현재 {config[sec]!r})")

    config["H_matrix"] = _path_pair("H_matrix", _require("최상위", config, "H_matrix"),
                                    base_dir)

    dec_cfg = config.setdefault("decoder", {})
    if "max_iter" in dec_cfg:
        raise ValueError(
            "decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일의 마지막 iter_end가 결정")
    _check_keys("decoder", dec_cfg, _DECODER_KEYS)
    dec_cfg["llr_matrix"] = _path_pair(
        "decoder.llr_matrix", _require("decoder", dec_cfg, "llr_matrix"), base_dir)
    dec_type = dec_cfg.setdefault("type", "vanilla")
    if not isinstance(dec_type, str) or not dec_type:
        raise ValueError(f"config [decoder] type={dec_type!r} — 아이디어 이름 문자열이어야 함")

    config["seed"] = _check_int("최상위", "seed", config.get("seed", 0), 0)

    out = config.setdefault("output", {})
    _check_keys("output", out, _OUTPUT_KEYS)
    out.setdefault("dir", os.path.join(base_dir, "Sim_Output"))
    if not os.path.isabs(out["dir"]):
        out["dir"] = os.path.join(base_dir, out["dir"])

    run_cfg = config.setdefault("run", {})
    _check_keys("run", run_cfg, _RUN_KEYS)
    _check_int("run", "max_frame_errors", run_cfg.get("max_frame_errors", 50), 1)
    _check_int("run", "max_frames", run_cfg.get("max_frames", 20000), 1)
    _check_int("run", "frames_per_batch", run_cfg.get("frames_per_batch", 128), 1)
    sbf = run_cfg.get("stop_below_fer")
    if sbf is not None and (isinstance(sbf, bool)
                            or not isinstance(sbf, (int, float)) or sbf <= 0):
        raise ValueError(f"config [run] stop_below_fer={sbf!r} — 0보다 큰 수 또는 null")

    log_cfg = config.setdefault("log", {})
    _check_keys("log", log_cfg, _LOG_KEYS)
    for k in _visible(log_cfg):
        if not isinstance(log_cfg[k], bool):
            raise ValueError(f"config [log] {k}={log_cfg[k]!r} — true/false여야 함")

    channels = _require("최상위", config, "channels")
    if isinstance(channels, dict):          # 단일 항목은 리스트로 정규화
        channels = [channels]
        config["channels"] = channels
    if not isinstance(channels, list) or not channels:
        raise ValueError("config channels — 비어 있지 않은 리스트여야 함")
    for i, ch in enumerate(channels):
        _check_channel(i, ch)
    return config


def _resolve_decoder_class(dec_type):
    """decoder.type → 디코더 클래스 (Ideas/registry.py 조회).

    Ideas 패키지는 실행 루트(config가 있는 실험 폴더) 기준으로 import되므로
    실험 루트에서 `python -m LDPC_base.run ...`으로 실행해야 한다.
    Ideas가 없는 환경에서는 "vanilla"만 정본(MinSumDecoder)으로 동작한다."""
    import importlib
    try:
        registry = importlib.import_module("Ideas.registry")
    except ImportError:
        if dec_type == "vanilla":
            return MinSumDecoder            # Ideas 없이도 정본 실행 가능
        raise ValueError(
            f"decoder.type={dec_type!r} — Ideas 패키지를 찾을 수 없음 "
            "(실험 루트에서 실행했는지 확인)")
    if dec_type not in registry.DECODERS:
        raise ValueError(
            f"decoder.type={dec_type!r} — Ideas/registry.py 미등록 "
            f"(등록된 이름: {sorted(registry.DECODERS)})")
    module_name, class_name = registry.DECODERS[dec_type].split(":")
    return getattr(importlib.import_module(module_name), class_name)


def setup(config):
    """H-matrix와 LLR matrix를 로드하고 decoder.type의 디코더를 구성한다.
    파일이 없으면 준비하라는 에러를 낸다 (이 함수는 생성하지 않음)."""
    h_path = config["H_matrix"]
    if not os.path.exists(h_path):
        raise FileNotFoundError(f"{h_path} 없음 — H-matrix를 먼저 준비할 것")
    code = QCCode.load(h_path)
    mx = LLRMatrix.load(config["decoder"]["llr_matrix"])
    print(mx.summary())
    decoder_cls = _resolve_decoder_class(config["decoder"]["type"])
    print(f"decoder: {config['decoder']['type']} ({decoder_cls.__module__}.{decoder_cls.__name__})")
    dec = decoder_cls(code, llr_matrix=mx)
    return code, dec


def _check_channel_mode(dec, ch_type):
    """디코딩 모드(HD/2SD/3SD)와 채널의 호환 확인. 측정 시작 전에 전 채널에 대해
    호출한다 (뒤 채널의 불일치로 앞 채널 측정이 버려지는 일 방지)."""
    mode = dec.llr_matrix.mode
    if mode not in chan.CHANNEL_MODES[ch_type]:
        raise ValueError(
            f"channel {ch_type}은 {chan.CHANNEL_MODES[ch_type]} 전용 — "
            f"현재 디코딩 모드 {mode} (LLR matrix 파일명 확인)")
    return mode


def _make_channel_fn(code, dec, ch, point):
    """채널 함수 생성: msg -> encode -> 채널. 디코딩 모드(HD/2SD/3SD)는
    LLR matrix에서 오고, 채널이 그 모드를 지원하는지 확인한다."""
    ch_type = ch["type"]
    mode = _check_channel_mode(dec, ch_type)
    extra = {}
    if ch_type == "strong_error":
        extra = {"scr": ch["SCR"], "ser": ch["SER"]}

    def channel_fn(batch, rng):
        msg = encoder.generate_message(code, batch, rng)
        cw = encoder.encode(msg, code)
        return chan.CHANNELS[ch_type](code, cw, point, rng, mode=mode, **extra)

    return channel_fn


def run_experiment(code, dec, config):
    """channels 리스트의 각 채널에 대해 각 포인트를 max_frame_errors 도달 또는
    max_frames 소진까지 측정한다. 반환: [(라벨, [point_result, ...]), ...].

    난수: 최상위 seed 하나에서 [seed, 채널 인덱스, 포인트]로 스트림을 파생 —
    포인트 간, 채널 간 독립이며 같은 seed면 재현된다."""
    run_cfg = config["run"]
    max_frame_errors = run_cfg.get("max_frame_errors", 50)
    max_frames = run_cfg.get("max_frames", 20000)
    frames_per_batch = run_cfg.get("frames_per_batch", 128)
    stop_below_fer = run_cfg.get("stop_below_fer")
    verbose = run_cfg.get("verbose", True)
    seed = config["seed"]
    log_cfg = config["log"]
    log_items = {item for key, item in _LOG_TO_ITEM.items() if log_cfg.get(key)}

    for ch in config["channels"]:                # 전 채널 모드 호환 사전 확인
        _check_channel_mode(dec, ch["type"])

    results = []
    used_labels = set()
    for ch_idx, ch in enumerate(config["channels"]):
        ch_type = ch["type"]
        label = ch.get("label", ch_type)
        if label in used_labels:            # 같은 라벨은 번호 접미사로 구분
            n = 2
            while f"{label}_{n}" in used_labels:
                n += 1
            label = f"{label}_{n}"
        used_labels.add(label)
        if verbose:
            print(f"== channel={ch_type} ({label}) ==")
        points = []
        for p in ch["points"]:
            rng = np.random.default_rng([seed, ch_idx, int(1e6 * p)])
            r = run_fer_point(code, _make_channel_fn(code, dec, ch, p),
                              dec, rng, max_frame_errors=max_frame_errors,
                              max_frames=max_frames, frames_per_batch=frames_per_batch,
                              verbose=verbose, log=log_items or None)
            r["param"] = p
            points.append(r)
            if stop_below_fer is not None and r["fer"] < stop_below_fer:
                break
        results.append((label, points))
    return results


def _git_commit_hash():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True, text=True, timeout=10).stdout.strip() or "(git 없음)"
    except OSError:
        return "(git 없음)"


def _dv_labels(matrix):
    """dv 구간별 열 이름: dv_from==dv_to면 dv{값}, 아니면 dv{from}-{to}."""
    return [f"dv{f}" if f == t else f"dv{f}-{t}"
            for f, t in zip(matrix.dv_from, matrix.dv_to)]


def _write_iter_log(path, point, log_cfg, dv_labels):
    """iteration별 집계 CSV: 켠 항목만 열로 (평균 = 합/활성 프레임 수)."""
    import csv
    agg = point["log_agg"]
    active = agg["active"]
    n_it = int(np.max(np.nonzero(active)[0])) + 1 if active.any() else 0
    header = ["iter", "active_frames"]
    if log_cfg.get("csw_per_iter"):
        header.append("csw_mean")
    if log_cfg.get("bit_err_per_iter"):
        header.append("bit_err_mean")
    if log_cfg.get("bit_err_by_dv"):
        header += [f"bit_err_{name}_mean" for name in dv_labels]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for k in range(n_it):
            a = int(active[k])
            row = [str(k + 1), str(a)]
            if log_cfg.get("csw_per_iter"):
                row.append(f"{agg['csw_sum'][k] / max(a, 1):.2f}")
            if log_cfg.get("bit_err_per_iter"):
                row.append(f"{agg['err_sum'][k] / max(a, 1):.2f}")
            if log_cfg.get("bit_err_by_dv"):
                row += [f"{agg['err_by_dv_sum'][k][d] / max(a, 1):.3f}"
                        for d in range(len(dv_labels))]
            w.writerow(row)


def _write_iter_hist_log(path, point, log_cfg):
    """수렴 iteration 히스토그램 + fer_vs_iter (max_iter를 k로 줄였다면의 FER)."""
    import csv
    hist = point["iter_hist"]
    frames = point["frames"]
    header = ["iter"]
    if log_cfg.get("iter_histogram"):
        header.append("success_at_iter")
    if log_cfg.get("fer_vs_iter"):
        header.append("fer_if_max_iter_k")
    cum = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for k in range(1, len(hist)):
            cum += int(hist[k])
            row = [str(k)]
            if log_cfg.get("iter_histogram"):
                row.append(str(int(hist[k])))
            if log_cfg.get("fer_vs_iter"):
                row.append(f"{1.0 - cum / frames:.6e}")
            w.writerow(row)


def _write_fail_log(path, point, dv_labels):
    """실패 프레임 상세: 프레임 번호, 잔여 에러 bit, 최종 CSW, dv별 잔여 에러."""
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frame", "final_err_bits", "final_csw"]
                   + [f"err_{name}" for name in dv_labels])
        for frame, err_bits, csw, by_dv in point["fail_rows"]:
            w.writerow([str(frame), str(err_bits), str(csw)]
                       + [str(v) for v in by_dv])


def _plot_fer_curves(path, results):
    """FER 커브 그림 (라벨별 한 줄, 0-error 포인트는 상한 마커)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    for label, points in results:
        xs = [r["param"] for r in points]
        fer = [r["fer"] if r["errors"] else 0.5 / r["frames"] for r in points]
        ax.plot(xs, fer, "-o", label=label)
        for x, f, r in zip(xs, fer, points):
            if not r["errors"]:
                ax.plot(x, f, "v", markerfacecolor="white", markersize=8)
    ax.set_yscale("log")
    ax.set_xlabel("point")
    ax.set_ylabel("FER")
    ax.grid(True, which="both", linewidth=0.5, linestyle="--")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def report(results, config, config_path, dec):
    """실행 폴더 생성(YYMMDD_HHMMSS_{라벨}) 후 결과 일체 저장:
    config 사본, summary.txt, FER CSV, 로그 CSV, FER 커브 그림."""
    out_cfg = config["output"]
    log_cfg = config["log"]
    label_all = out_cfg.get("label", config["channels"][0]["type"])
    stamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    run_dir = os.path.join(out_cfg["dir"], f"{stamp}_{label_all}")
    os.makedirs(run_dir, exist_ok=True)
    shutil.copy(config_path, os.path.join(run_dir, "config.json"))

    dv_labels = _dv_labels(dec.llr_matrix)
    lines = [f"run: {stamp}_{label_all}", f"code commit: {_git_commit_hash()}", ""]
    prefix = out_cfg.get("csv_prefix", "fer")
    for label, points in results:
        csv_path = os.path.join(run_dir, f"{prefix}_{label}.csv")
        save_csv(points, csv_path, param_name="param")
        print(f"saved: {csv_path}")
        for r in points:
            lines.append(
                f"{label} point={r['param']}: FER={r['fer']:.3e} "
                f"BER={r['post_fec_ber']:.3e} [{r['errors']}/{r['frames']}] "
                f"avg_decode_success_iteration={r['avg_decode_success_iteration']:.2f} ({r['sec']:.1f}s)")
            if "log_agg" in r and (log_cfg.get("csw_per_iter")
                                   or log_cfg.get("bit_err_per_iter")
                                   or log_cfg.get("bit_err_by_dv")):
                _write_iter_log(os.path.join(run_dir, f"log_iter_{label}_p{r['param']}.csv"),
                                r, log_cfg, dv_labels)
            if log_cfg.get("iter_histogram") or log_cfg.get("fer_vs_iter"):
                _write_iter_hist_log(
                    os.path.join(run_dir, f"log_iter_hist_{label}_p{r['param']}.csv"),
                    r, log_cfg)
            if "fail_rows" in r:
                _write_fail_log(
                    os.path.join(run_dir, f"log_fail_{label}_p{r['param']}.csv"),
                    r, dv_labels)
    if log_cfg.get("fer_curve_png"):
        png = os.path.join(run_dir, "fer_curves.png")
        _plot_fer_curves(png, results)
        print(f"saved: {png}")
    with open(os.path.join(run_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"run dir: {run_dir}")
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("usage: python -m LDPC_base.run <config.json>")

    config = load_config(argv[0])
    code, dec = setup(config)
    print(code.summary())
    results = run_experiment(code, dec, config)
    report(results, config, argv[0], dec)


if __name__ == "__main__":
    main()
