"""(P,Q,알파low%,알파high%,격차T) 조합 스캔 실행기.

config를 바탕으로 label만 dynnorm_p{P}q{Q}_al{low}ah{high}_t{T}로 바꾼 임시
config를 만들어 조합마다 순차 실행한다. 알파는 백분율 정수로 받는다
(75 = 0.75). 실행 (이 폴더에서):
    python scan.py                              기본 config.json + 기본 조합 목록
    python scan.py config_headroom.json         다른 config + 기본 조합 목록
    python scan.py config_headroom.json 15,15,100,100,1 4,8,50,100,1    조합 지정

(P=Q=edge 상한, 알파 100,100) 조합은 정규화와 클리핑이 전부 무효과라
base_run 기준선과 수치가 일치해야 한다 (구현 동등성 검증용).
알파 low=high 조합은 동적 선택을 끈 고정 정규화 대조군이다.
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

from decoder import MinSumDynamicNormalizationDecoder

# (P, Q, 알파low%, 알파high%, 격차T). 기본 목록은 LLR_MATRIX_HD_1 환경(edge 상한 7)용:
# 동등성 검증 1개 + 고정 정규화 대조군 + 동적 정규화 변형
COMBOS = [
    (7, 7, 100, 100, 1),   # 무효과 = base_run 동등성 검증
    (7, 7, 75, 75, 1),     # 고정 정규화 (동적 선택 off 대조군)
    (7, 7, 75, 100, 1),    # 동적 정규화 (약)
    (7, 7, 50, 100, 1),    # 동적 정규화 (강)
    (7, 7, 50, 100, 2),    # 격차 임계 대조
]

if __name__ == "__main__":
    config_name = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    if len(sys.argv) > 2:
        COMBOS = [tuple(int(v) for v in arg.split(",")) for arg in sys.argv[2:]]
    with open(os.path.join(EXPERIMENT_DIR, config_name), encoding="utf-8") as f:
        base_config = json.load(f)
    scan_config_path = os.path.join(EXPERIMENT_DIR, "config_scan.json")
    try:
        for clip_p, clip_q, alpha_low_pct, alpha_high_pct, gap_threshold in COMBOS:
            decoder_class = MinSumDynamicNormalizationDecoder
            decoder_class.CLIP_P = clip_p
            decoder_class.CLIP_Q = clip_q
            decoder_class.ALPHA_LOW = alpha_low_pct / 100.0
            decoder_class.ALPHA_HIGH = alpha_high_pct / 100.0
            decoder_class.GAP_THRESHOLD = gap_threshold
            label = (f"dynnorm_p{clip_p}q{clip_q}"
                     f"_al{alpha_low_pct}ah{alpha_high_pct}_t{gap_threshold}")
            base_config["output"]["label"] = label
            with open(scan_config_path, "w", encoding="utf-8") as f:
                json.dump(base_config, f, ensure_ascii=False, indent=2)
            decoder_class.reset_stats()
            main([scan_config_path], decoder_class=decoder_class)
            print(f"[{label}] {decoder_class.stats_summary()}")
    finally:
        if os.path.exists(scan_config_path):
            os.remove(scan_config_path)
