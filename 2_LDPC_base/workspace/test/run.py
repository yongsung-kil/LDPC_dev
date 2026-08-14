"""이 폴더의 config.json으로 시뮬레이션을 실행하는 런처.

실행: python run.py [config1.json config2.json ...] (기본은 형제 config.json)
본체 import(상위의 2_LDPC_base/src)와 디코더 선택 방식: workspace/README.md 참조.
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

DECODER_CLASS = None
# None이면 src 본체의 BaseDecoder (base_run 기준선).
# 변형 디코더는 이 폴더의 decoder.py에 BaseDecoder 자식으로 만들고 이렇게 지정한다:
#   from decoder import MyDecoder
#   DECODER_CLASS = MyDecoder

if __name__ == "__main__":
    config_paths = sys.argv[1:] or [os.path.join(EXPERIMENT_DIR, "config.json")]
    for config_path in config_paths:
        main([config_path], decoder_class=DECODER_CLASS)
