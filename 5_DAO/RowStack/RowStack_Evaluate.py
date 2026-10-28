"""후보 하나의 평가 (1판 설계 4.2절, 탐색 규칙 2판 3.3절의 개선 판정).

매트릭스 후보로 uncor 프레임 1개를 주어진 iteration 예산만큼 복호하고, 성공 여부와 iteration 중 최소 잔여 에러
bit 수(codeword 전체), 그 iteration과 그때의 CSW를 요약한다. 디코더 호출은 UncorDecoder.evaluate 한 곳이다
(뒤에 Ref-C 실행 파일을 끼울 자리). 빈 매트릭스(아직 row가 없음)의 성능은 받은 프레임 자체다 (empty_result).
"""
from dataclasses import dataclass

import numpy as np

import RowStack_Config  # noqa: F401  (sys.path 등록)
from RowStack_Matrix import MatrixTemplate, build_base_llr_matrix
from src import channel as chan
from src.decoder import BaseDecoder
from src.sim import decode_frame_seeds


@dataclass
class CandidateResult:
    success: bool                 # 이 매트릭스로 uncor가 고쳐졌는지 (decoding success)
    success_iteration: int        # 고친 iteration. 실패 0
    min_err: int                  # iteration 중 최소 잔여 에러 bit 수
    min_err_iteration: int        # i* (1부터, 가장 이른 것). 빈 매트릭스는 0
    csw_at_min_err: int           # i*가 끝난 시점의 CSW
    err_per_iter: np.ndarray      # int64, 돈 iteration 수만큼
    csw_per_iter: np.ndarray
    initial_csw: int = 0          # iteration 1이 row를 고를 때 보는 CSW (받은 프레임의 syndrome 무게)
    initial_err: int = 0          # 받은 프레임의 에러 bit 수


def result_from_decode(decode: dict, initial_csw: int = 0, initial_err: int = 0) -> CandidateResult:
    """decode_frame_seeds(seed 1개, log={"bit_err", "csw"})의 반환을 요약한다."""
    err = np.asarray(decode["log_err_sum"], np.int64)
    csw = np.asarray(decode["log_csw_sum"], np.int64)
    success = bool(decode["success"][0])
    success_iteration = int(decode["decode_success_iteration"][0]) if success else 0
    if len(err) == 0:
        return CandidateResult(success, success_iteration, 0, 0, 0, err, csw, int(initial_csw), int(initial_err))
    best = int(np.argmin(err)) + 1
    return CandidateResult(success, success_iteration, int(err[best - 1]), best, int(csw[best - 1]), err, csw,
                           int(initial_csw), int(initial_err))


def candidate_sort_key(result: CandidateResult) -> tuple:
    """작을수록 좋다. 성공은 (0, 성공 iteration, 0, 0), 실패는 (1, 최소 잔여 에러, 그때 CSW, i*)."""
    if result.success:
        return (0, result.success_iteration, 0, 0)
    return (1, result.min_err, result.csw_at_min_err, result.min_err_iteration)


def is_improvement(child: CandidateResult, parent: CandidateResult) -> bool:
    """자식이 부모보다 나아졌는지 (탐색 규칙 2판 ㉱). 성공은 실패보다 낫고, 성공끼리는 고친 iteration이 더 빠를 때,
    실패끼리는 최소 잔여 에러 bit 수가 더 작을 때만 개선이다. 같으면 개선이 아니다 (CSW나 iteration 동점 차이는 보지 않는다)."""
    if child.success and parent.success:
        return child.success_iteration < parent.success_iteration
    if child.success != parent.success:
        return child.success
    return child.min_err < parent.min_err


class UncorDecoder:
    """매트릭스 후보(row 목록)와 seed 하나를 받아 Python 디코더로 복호한다."""

    def __init__(self, code, template: MatrixTemplate, channel_type: str, point: float, channel_extra: dict):
        self.code = code
        self.template = template
        self.channel_type = channel_type
        self.point = point
        self.channel_extra = dict(channel_extra)
        self._frame_stats_by_seed = {}

    def frame_stats(self, seed: int) -> tuple:
        """받은 프레임의 (syndrome 무게, 에러 bit 수). 매트릭스와 무관하게 seed마다 하나이며 한 번만 계산한다."""
        seed = int(seed)
        if seed not in self._frame_stats_by_seed:
            frame = chan.channel_output_from_frame_seeds(self.code, self.channel_type, self.point, [seed],
                                                         mode=self.template.mode, **self.channel_extra)
            self._frame_stats_by_seed[seed] = (int(self.code.syndrome(frame["hd"]).sum()), int(frame["hd"].sum()))
        return self._frame_stats_by_seed[seed]

    def initial_csw(self, seed: int) -> int:
        return self.frame_stats(seed)[0]

    def empty_result(self, seed: int) -> CandidateResult:
        """row가 없는 매트릭스의 성능: 받은 프레임 자체 (에러 bit 수, 초기 CSW, iteration 0)."""
        initial_csw, initial_err = self.frame_stats(seed)
        empty = np.zeros(0, np.int64)
        return CandidateResult(False, 0, initial_err, 0, initial_csw, empty, empty, initial_csw, initial_err)

    def evaluate(self, rows: list, seed: int, max_iter: int) -> CandidateResult:
        llr_matrix = build_base_llr_matrix(self.template, rows, max_iter=max_iter, name=f"stacked_{len(rows)}")
        decoder = BaseDecoder(self.code, llr_matrix=llr_matrix)
        decode = decode_frame_seeds(self.code, decoder, self.channel_type, self.point, [int(seed)],
                                    frames_per_batch=1, log={"bit_err", "csw"}, **self.channel_extra)
        initial_csw, initial_err = self.frame_stats(seed)
        return result_from_decode(decode, initial_csw, initial_err)
