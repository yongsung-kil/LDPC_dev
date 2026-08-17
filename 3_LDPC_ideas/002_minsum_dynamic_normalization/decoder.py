"""minsum_dynamic_normalization: min1/min2 격차 기반 동적 정규화 + 이중 상한 (ieee:6865103, 2014).

재정의: _c2v_reconstruct (C++ 대응: C2V_Cal)
실물 C++ 이식 지점: decoder.cpp C2V_Cal() (재구성 magnitude에 정규화와 클리핑 적용)

논문의 세 기법 중 FER에 작용하는 두 가지를 조합해 재정의한다:
  1. 동적 정규화: 격차(gap) = min2 - min1이 GAP_THRESHOLD보다 크면 min1이
     둘째 값과 확실히 구분되는 신뢰 상황이므로 높은 계수 ALPHA_HIGH(감쇠 적게),
     작으면 낮은 계수 ALPHA_LOW(감쇠 많이)를 곱한다
  2. 이중 상한: 정규화한 min1을 CLIP_P로, min2를 CLIP_Q로 클리핑한다
     (001_minsum_dual_clip과 같은 구조, 논문 순서대로 정규화 후 클리핑)
셋째 기법(저장 min2의 비균일 양자화)은 저장 비트 절감용 하드웨어 기법이라
py 스크리닝 범위 밖이다 (README 요약 참조).

정규화 결과는 반올림해 정수로 유지한다. 비정수 C2V가 sum_t로 흘러가면
VNU 양자화의 균일 등가식 전제가 깨지기 때문이다
(BaseDecoder._uniform_saturate docstring 참조). 001과 같은 이유로 저장
상태(min1/min2)는 건드리지 않고 재구성 시점에만 적용한다 (상태를 고치면
증분 갱신의 min1/min2 추적이 오염된다).

자체 수집 지표 (클래스 누적, scan.py가 실행 전 리셋하고 실행 후 판독):
  stat_total:      _c2v_reconstruct가 만든 C2V 원소 수
  stat_alpha_high: 그중 ALPHA_HIGH가 선택된 원소 수 (동적 선택 분포)
  stat_clip_hit:   정규화 후에도 min1이 CLIP_P를 넘어 클리핑된 원소 수
"""
import numpy as np

from src.decoder import BaseDecoder


class MinSumDynamicNormalizationDecoder(BaseDecoder):
    CLIP_P = 7          # 정규화 후 min1 상한
    CLIP_Q = 7          # 정규화 후 min2 상한
    ALPHA_LOW = 0.75    # 격차가 GAP_THRESHOLD 이하일 때의 정규화 계수
    ALPHA_HIGH = 1.0    # 격차가 GAP_THRESHOLD보다 클 때의 정규화 계수
    GAP_THRESHOLD = 1   # 격차 판정 임계값 (min2 - min1과 비교)

    stat_total = 0
    stat_alpha_high = 0
    stat_clip_hit = 0

    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix)
        if not 1 <= self.CLIP_P <= self.CLIP_Q:
            raise ValueError(
                f"CLIP_P({self.CLIP_P})는 1 이상 CLIP_Q({self.CLIP_Q}) 이하여야 함")
        if not 0.0 < self.ALPHA_LOW <= self.ALPHA_HIGH <= 1.0:
            raise ValueError(
                f"0 < ALPHA_LOW({self.ALPHA_LOW}) <= ALPHA_HIGH({self.ALPHA_HIGH}) <= 1"
                " 이어야 함")

    @classmethod
    def reset_stats(cls):
        cls.stat_total = 0
        cls.stat_alpha_high = 0
        cls.stat_clip_hit = 0

    @classmethod
    def stats_summary(cls):
        """자체 수집 지표 요약 문자열 (스캔 로그용)."""
        if cls.stat_total == 0:
            return "stats: (수집 없음)"
        return (f"stats: alpha_high 선택율 {cls.stat_alpha_high / cls.stat_total:.3f}, "
                f"min1 클리핑 발생율 {cls.stat_clip_hit / cls.stat_total:.3f} "
                f"(원소 {cls.stat_total:,}개)")

    def _c2v_reconstruct(self, iteration, edge, min1_row, min2_row, min1_pos_row,
                         syndrome_row, check_sum_row, edge_sgn_row):
        use_high = (min2_row - min1_row) > np.float32(self.GAP_THRESHOLD)
        alpha = np.where(use_high, np.float32(self.ALPHA_HIGH),
                         np.float32(self.ALPHA_LOW))
        # 반올림(내림 아님)으로 정수 유지: ALPHA=1.0이면 원값 그대로 (동등성 검증 조건)
        min1_normalized = np.floor(alpha * min1_row + np.float32(0.5))
        min2_normalized = np.floor(alpha * min2_row + np.float32(0.5))
        min1_out = np.minimum(min1_normalized, np.float32(self.CLIP_P))
        min2_out = np.minimum(min2_normalized, np.float32(self.CLIP_Q))

        cls = type(self)
        cls.stat_total += use_high.size
        cls.stat_alpha_high += int(use_high.sum())
        cls.stat_clip_hit += int((min1_normalized > np.float32(self.CLIP_P)).sum())

        check_out = np.where(min1_pos_row == edge, min2_out, min1_out)
        c2v_sgn = (syndrome_row ^ check_sum_row ^ edge_sgn_row).astype(bool)
        return np.where(c2v_sgn, -check_out, check_out)
