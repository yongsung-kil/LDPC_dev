"""ldpc_light — 논문 아이디어 스크리닝용 경량 QC-LDPC 시뮬레이터 (vanilla).

계획/제약: docs/ldpc_light/plan.md 참조. 상대 비교(아이디어 on/off) 전용 —
C++ Ref-C와의 절대 FER 일치는 보장하지 않으며, 최종 검증은 실물 C++ 이식으로 수행한다.
"""
from .pcm import QCCode
from .decoder import MinSumDecoder
from . import channel, sim

__all__ = ["QCCode", "MinSumDecoder", "channel", "sim"]
