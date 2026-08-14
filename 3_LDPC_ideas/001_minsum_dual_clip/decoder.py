"""minsum_dual_clip: CNU min1/min2 이중 상한 클리핑 (ieee:9496601, IEEE TCAD 2022).

재정의: _c2v_reconstruct (C++ 대응: C2V_Cal)
실물 C++ 이식 지점: decoder.cpp CNU_Update_New_Mag() (min1/min2 확정 직후 clip 2줄)

min1은 CLIP_P로, min2는 CLIP_Q로 클리핑한다 (1 <= CLIP_P <= CLIP_Q).
저장 상태(min1/min2)는 그대로 두고 C2V 재구성 시점에 클리핑한다.
상태를 클리핑하면 증분 갱신(remove old)의 min1/min2 추적이 오염되기 때문이며,
재구성 시점 클리핑이 논문의 식(3) 대입 직전 클리핑과 등가다.
"""
import numpy as np

from src.decoder import BaseDecoder


class MinSumDualClipDecoder(BaseDecoder):
    CLIP_P = 2  # min1 상한
    CLIP_Q = 3  # min2 상한

    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix)
        if not 1 <= self.CLIP_P <= self.CLIP_Q:
            raise ValueError(
                f"CLIP_P({self.CLIP_P})는 1 이상 CLIP_Q({self.CLIP_Q}) 이하여야 함")

    def _c2v_reconstruct(self, iteration, edge, min1_row, min2_row, min1_pos_row,
                         syndrome_row, check_sum_row, edge_sgn_row):
        min1_clipped = np.minimum(min1_row, np.float32(self.CLIP_P))
        min2_clipped = np.minimum(min2_row, np.float32(self.CLIP_Q))
        check_out = np.where(min1_pos_row == edge, min2_clipped, min1_clipped)
        c2v_sgn = (syndrome_row ^ check_sum_row ^ edge_sgn_row).astype(bool)
        return np.where(c2v_sgn, -check_out, check_out)
