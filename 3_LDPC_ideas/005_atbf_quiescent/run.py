"""이 폴더의 config.json으로 시뮬레이션을 실행하는 런처.

실행: python run.py [config1.json config2.json ...] (기본은 형제 config.json)
본체 import와 디코더 선택 방식: 3_LDPC_ideas/README.md 폴더 규칙 참조.
"""
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

from decoder import ATBFLadderDecoder

DECODER_CLASS = ATBFLadderDecoder
# 사다리 단과 파라미터는 decoder.py의 클래스 기본값 (scan.py 선정 조합).
# 격자와 자체 지표 수집은 scan.py가 수행한다.

if __name__ == "__main__":
    config_paths = sys.argv[1:] or [os.path.join(EXPERIMENT_DIR, "config.json")]
    for config_path in config_paths:
        main([config_path], decoder_class=DECODER_CLASS)
