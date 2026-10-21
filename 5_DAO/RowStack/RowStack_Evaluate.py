"""후보 하나의 평가 (설계 문서 4.2절).

prefix와 후보 row를 합친 매트릭스로 uncor 프레임 1개를 복호하고, 성공 여부와 iteration 중 최소 잔여 에러
bit 수(codeword 전체), 그 iteration과 그때의 CSW를 요약한다. 디코더 호출은 UncorDecoder.evaluate 한 곳이다
(뒤에 Ref-C 실행 파일을 끼울 자리).
"""
from dataclasses import dataclass

import numpy as np

import RowStack_Config  # noqa: F401  (sys.path 등록)
from RowStack_Matrix import MatrixTemplate, build_base_llr_matrix
from src.decoder import BaseDecoder
from src.sim import decode_frame_seeds


@dataclass
class CandidateResult:
    success: bool
    success_iteration: int        # 실패 0
    min_err: int                  # iteration 중 최소 잔여 에러 bit 수
    min_err_iteration: int        # i* (1부터, 가장 이른 것)
    csw_at_min_err: int           # i*가 끝난 시점의 CSW
    err_per_iter: np.ndarray      # int64, 돈 iteration 수만큼
    csw_per_iter: np.ndarray


def result_from_decode(decode: dict) -> CandidateResult:
    """decode_frame_seeds(seed 1개, log={"bit_err", "csw"})의 반환을 요약한다."""
    err = np.asarray(decode["log_err_sum"], np.int64)
    csw = np.asarray(decode["log_csw_sum"], np.int64)
    success = bool(decode["success"][0])
    success_iteration = int(decode["decode_success_iteration"][0]) if success else 0
    if len(err) == 0:
        return CandidateResult(success, success_iteration, 0, 0, 0, err, csw)
    best = int(np.argmin(err)) + 1
    return CandidateResult(success, success_iteration, int(err[best - 1]), best, int(csw[best - 1]), err, csw)


def candidate_sort_key(result: CandidateResult) -> tuple:
    """작을수록 좋다. 성공은 (0, 성공 iteration, 0, 0), 실패는 (1, 최소 잔여 에러, 그때 CSW, i*)."""
    if result.success:
        return (0, result.success_iteration, 0, 0)
    return (1, result.min_err, result.csw_at_min_err, result.min_err_iteration)


class UncorDecoder:
    """row 목록과 seed 하나를 받아 Python 디코더로 복호한다."""

    def __init__(self, code, template: MatrixTemplate, channel_type: str, point: float, channel_extra: dict):
        self.code = code
        self.template = template
        self.channel_type = channel_type
        self.point = point
        self.channel_extra = dict(channel_extra)

    def evaluate(self, rows: list, seed: int) -> CandidateResult:
        llr_matrix = build_base_llr_matrix(self.template, rows, name=f"stacked_{len(rows)}")
        decoder = BaseDecoder(self.code, llr_matrix=llr_matrix)
        decode = decode_frame_seeds(self.code, decoder, self.channel_type, self.point, [int(seed)],
                                    frames_per_batch=1, log={"bit_err", "csw"}, **self.channel_extra)
        return result_from_decode(decode)
