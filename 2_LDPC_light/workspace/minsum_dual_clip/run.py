"""이 폴더의 config.json으로 시뮬레이션을 실행하는 런처.

- 어느 위치에서 실행해도 상위로 올라가며 LDPC_base가 있는 폴더(2_LDPC_light)를
  찾아 검색 경로에 넣는다 (LDPC_base 복사 없이 공용 본체를 사용)
- 기본 config는 이 파일 옆의 config.json이고, 인자로 다른 config를 줄 수 있다:
  python run.py [config1.json config2.json ...]
- 디코더 선택은 아래 DECODER_CLASS 한 곳에서 한다
"""
import os
import sys

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))

_root = EXPERIMENT_DIR
while not os.path.isdir(os.path.join(_root, "LDPC_base")):
    _parent = os.path.dirname(_root)
    if _parent == _root:
        raise SystemExit("상위 폴더에서 LDPC_base를 찾지 못함 "
                         "(이 파일은 2_LDPC_light 하위 실험 폴더에 있어야 함)")
    _root = _parent
if _root not in sys.path:
    sys.path.insert(0, _root)

from LDPC_base.run import main

from decoder import MinSumDualClipDecoder
DECODER_CLASS = MinSumDualClipDecoder

if __name__ == "__main__":
    config_paths = sys.argv[1:] or [os.path.join(EXPERIMENT_DIR, "config.json")]
    for config_path in config_paths:
        main([config_path], decoder_class=DECODER_CLASS)
