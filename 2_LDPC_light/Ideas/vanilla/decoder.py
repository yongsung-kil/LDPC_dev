"""vanilla: 원본 C++ vanilla 대응 reference 디코더.

어떤 교체용 함수도 재정의하지 않는다 (LDPC_base 정본 그대로). 모든 아이디어의
비교 기준선(reference)이며, reference 실험은 이 폴더의 config.json으로 실행한다.
"""
from LDPC_base.decoder import MinSumDecoder


class VanillaDecoder(MinSumDecoder):
    """재정의 없이 정본과 동일 동작 (원본 C++ vanilla 대응)."""
