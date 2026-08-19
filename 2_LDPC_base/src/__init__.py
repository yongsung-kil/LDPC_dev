"""2_LDPC_base: 논문 아이디어 스크리닝용 QC-LDPC 시뮬레이터 본체.

확정 결정 기록: 2_LDPC_base/README.md 참조. 상대 비교(아이디어 on/off) 전용이라
C++ Ref-C와의 절대 FER 일치는 보장하지 않는다.
"""
from .pcm import QCCode
from .decoder import BaseDecoder
from . import channel, encoder, sim

__all__ = ["QCCode", "BaseDecoder", "channel", "encoder", "sim"]
