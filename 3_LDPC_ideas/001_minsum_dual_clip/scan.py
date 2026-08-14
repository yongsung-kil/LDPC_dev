"""(P,Q) 정수 스캔 실행기.

config를 바탕으로 label만 dualclip_p{P}q{Q}로 바꾼 임시 config를 만들어
쌍마다 순차 실행한다. 실행 (이 폴더에서):
    python scan.py                          기본 config.json + 기본 쌍 목록
    python scan.py config_headroom.json     다른 config + 기본 쌍 목록
    python scan.py config_headroom.json 15,15 8,11 4,8    쌍 목록 지정
"""
import json
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

from src.run import main

from decoder import MinSumDualClipDecoder

# (P, Q) 쌍. (7,7)은 클리핑 무효과 조건이라 base_run 기준선과 수치가 일치해야 한다
# (구현 동등성 검증용). P=Q 쌍은 이중 상한 효과 분리용 대조군.
PAIRS = [(7, 7), (5, 7), (5, 5), (3, 7), (3, 5), (3, 3), (2, 5), (2, 3), (1, 3), (1, 1)]

if __name__ == "__main__":
    config_name = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    if len(sys.argv) > 2:
        PAIRS = [tuple(int(v) for v in arg.split(",")) for arg in sys.argv[2:]]
    with open(os.path.join(EXPERIMENT_DIR, config_name), encoding="utf-8") as f:
        base_config = json.load(f)
    scan_config_path = os.path.join(EXPERIMENT_DIR, "config_scan.json")
    try:
        for clip_p, clip_q in PAIRS:
            MinSumDualClipDecoder.CLIP_P = clip_p
            MinSumDualClipDecoder.CLIP_Q = clip_q
            base_config["output"]["label"] = f"dualclip_p{clip_p}q{clip_q}"
            with open(scan_config_path, "w", encoding="utf-8") as f:
                json.dump(base_config, f, ensure_ascii=False, indent=2)
            main([scan_config_path], decoder_class=MinSumDualClipDecoder)
    finally:
        if os.path.exists(scan_config_path):
            os.remove(scan_config_path)
