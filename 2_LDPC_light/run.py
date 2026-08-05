"""JSON 설정 기반 실험 진입점 (파라미터와 코드를 분리).

main()은 4단계로만 구성된다:
  1. load_config    — JSON 파라미터 읽기
  2. setup          — H-matrix 로드, 디코더 구성 (H-matrix 생성 자체는 tools/gen_example_code.py에서
                       별도 실행 — 이 흐름은 생성을 하지 않고, 파일이 없으면 안내만 한다)
  3. run_experiment — msg 생성 -> encode(스텁) -> channel -> decode 반복.
                       config["channels"]는 리스트이므로 채널 1개/여러 개, 포인트 1개/여러 개가
                       모두 동일한 코드 경로로 자연히 처리된다 ("sweep" 개념을 별도로 분기하지 않음)
  4. report         — 요약 출력 + 채널별 CSV 저장

실행: python -m 2_LDPC_light.run <config.json>
"""
import json
import os
import sys

import numpy as np

from . import channel as chan
from . import encoder
from .decoder import MinSumDecoder
from .pcm import QCCode
from .sim import run_fer_point, save_csv

_CHANNEL_FNS = {
    "bsc": lambda code, cw, param, rng: chan.bsc_llr(code, cw, param, rng),
    "awgn": lambda code, cw, param, rng: chan.awgn_llr(code, cw, param, rng),
}


def load_config(path):
    """실험 파라미터 JSON 로드. code_file/output.dir 상대경로는 config 파일 위치 기준으로
    해석한다. channels[].points는 스칼라도 허용하며 내부에서 리스트로 정규화한다
    (단일 채널·단일 포인트도 다중 채널·다중 포인트와 같은 구조로 표현)."""
    with open(path, encoding="utf-8") as f:
        config = json.load(f)

    base_dir = os.path.dirname(os.path.abspath(path))
    if not os.path.isabs(config["code_file"]):
        config["code_file"] = os.path.join(base_dir, config["code_file"])
    out = config.setdefault("output", {})
    out.setdefault("dir", base_dir)
    if not os.path.isabs(out["dir"]):
        out["dir"] = os.path.join(base_dir, out["dir"])

    for ch in config["channels"]:
        if ch["type"] not in _CHANNEL_FNS:
            raise ValueError(f"unknown channel type: {ch['type']!r}")
        if not isinstance(ch["points"], list):
            ch["points"] = [ch["points"]]
    return config


def setup(config):
    """code_file로부터 QCCode를 로드하고 decoder를 구성한다.
    H-matrix 파일이 없으면 생성/반입을 먼저 하라는 에러를 낸다 (이 함수는 생성하지 않음)."""
    code_file = config["code_file"]
    if not os.path.exists(code_file):
        raise FileNotFoundError(
            f"{code_file} 없음 — H-matrix를 먼저 준비할 것 "
            "(예: python -m 2_LDPC_light.tools.gen_example_code, 또는 실물 파일 반입)")
    code = QCCode.load(code_file)
    dec = MinSumDecoder(code, **config.get("decoder", {}))
    return code, dec


def _make_channel_fn(code, ch_type, param):
    fn = _CHANNEL_FNS[ch_type]

    def channel_fn(batch, rng):
        msg = encoder.generate_message(code, batch, rng)
        cw = encoder.encode(msg, code)
        return fn(code, cw, param, rng)

    return channel_fn


def run_experiment(code, dec, config):
    """config["channels"]의 각 채널에 대해 각 포인트를 target_errors 도달 또는
    max_frames 소진까지 측정한다. 반환: {channel_type: [point_result, ...]}."""
    run_cfg = config.get("run", {})
    target_errors = run_cfg.get("target_errors", 50)
    max_frames = run_cfg.get("max_frames", 20000)
    batch = run_cfg.get("batch", 128)
    stop_below = run_cfg.get("stop_below")
    default_seed = run_cfg.get("seed", 12345)
    verbose = run_cfg.get("verbose", True)

    results = {}
    for ch in config["channels"]:
        ch_type, seed = ch["type"], ch.get("seed", default_seed)
        if verbose:
            print(f"== channel={ch_type} ==")
        points = []
        for p in ch["points"]:
            rng = np.random.default_rng([seed, int(1e6 * p)])
            r = run_fer_point(code, _make_channel_fn(code, ch_type, p), dec, rng,
                              target_errors=target_errors, max_frames=max_frames,
                              batch=batch, verbose=verbose)
            r["param"] = p
            points.append(r)
            if stop_below is not None and r["fer"] < stop_below:
                break
        results[ch_type] = points
    return results


def report(results, config):
    """요약 출력 + 채널별 CSV 저장."""
    out_cfg = config.get("output", {})
    out_dir = out_cfg.get("dir", ".")
    os.makedirs(out_dir, exist_ok=True)
    for ch_type, points in results.items():
        csv_path = os.path.join(out_dir, f"{out_cfg.get('csv_prefix', 'fer')}_{ch_type}.csv")
        save_csv(points, csv_path, param_name="param")
        print(f"saved: {csv_path}")
    return results


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        raise SystemExit("usage: python -m 2_LDPC_light.run <config.json>")

    config = load_config(argv[0])
    code, dec = setup(config)
    print(code.summary())
    results = run_experiment(code, dec, config)
    report(results, config)


if __name__ == "__main__":
    main()
