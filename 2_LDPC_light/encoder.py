"""메시지 생성 + 인코딩.

encode()는 현재 스텁이다: all-zero codeword 확정(plan.md §7 #2)에 따라 msg 내용과
무관하게 all-zero를 반환한다. 실물 인코더가 필요해지면 이 함수만 교체하면 되고,
channel.py는 이미 cw를 그대로 받아 처리하므로 다른 곳은 손댈 필요가 없다.
"""
import numpy as np


def generate_message(code, batch, rng):
    """정보 bit K개 무작위 생성. shape (batch, K), {0,1} uint8."""
    return rng.integers(0, 2, size=(batch, code.K), dtype=np.uint8)


def encode(msg, code):
    """스텁 인코더: 실제 인코딩 없이 all-zero codeword 반환 (msg 내용 무시).
    반환 shape (batch, N_b, z), {0,1} uint8."""
    return np.zeros((msg.shape[0], code.N_b, code.z), dtype=np.uint8)
