"""메시지 생성 + 인코딩.

encode()는 아직 실제 구현 없이 자리만 잡아둔 임시 함수다: all-zero codeword
확정(사용자 결정 2026-07-30, README 확정 결정 기록)에 따라 msg 내용과 무관하게
all-zero를 반환한다.
성공 판정(genie)도 정답을 all-zero로 전제하므로(decoder.py의 에러 판정),
인코딩을 실제로 수행하게 바꿀 때는 이 함수와 함께 디코더의 정답 참조와 sim.py의
BER 집계도 같이 바꿔야 한다.
"""
import numpy as np


def generate_message(code, batch, random_generator):
    """정보 bit K개 무작위 생성. shape (batch, K), {0,1} uint8."""
    return random_generator.integers(0, 2, size=(batch, code.K), dtype=np.uint8)


def encode(msg, code):
    """임시 인코더 (실제 인코딩 미구현): all-zero codeword 반환 (msg 내용 무시).
    반환 shape (batch, N_b, z), {0,1} uint8."""
    return np.zeros((msg.shape[0], code.N_b, code.z), dtype=np.uint8)
