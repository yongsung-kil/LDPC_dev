"""쌓는 매트릭스의 모델과 규칙 (설계 문서 4.3절).

- MatrixTemplate: 기존 LLR matrix의 헤더(모드, dv 구간, 값 범위)와 쌓는 그룹의 iteration 수
- StackedRow: row 하나 (값 배열과 CSW 문턱). 첫 row의 문턱은 -1, 그 뒤는 8의 배수이며 아래로 갈수록 엄격히 작아진다
- 값 규칙: 헤더 min/max로 자르고 dv마다 CH 구간과 TH 구간을 각각 내림차순 정렬 (DAO Correct_Ch_Th_In_Row와 같은 결과)
- CSW 문턱 규칙(new_row_csw_threshold): prefix가 최소 잔여 에러에 닿은 iteration의 CSW를 8의 배수로 올린 값.
  쓸 수 없으면(마지막 iteration이거나 앞 row 문턱 이상) 닿을 수 있는 iteration 가운데 잔여 에러가 가장 작은 것, 없으면 None
파일은 2_LDPC_base LLRMatrix.save로 DAO 형식으로 쓴다. 저장 파일의 유효성은 검사 코드가 DAO Is_LLR_Valid로 본다.
"""
import math
from dataclasses import dataclass
from typing import Optional

import numpy as np

import RowStack_Config  # noqa: F401  (sys.path 등록)
from DAO_Constants import MAX_CSW, MIN_CSW, STEP_CSW
from src.llr_matrix import GROUP_TYPE_CSW, LLRMatrix


@dataclass(frozen=True)
class MatrixTemplate:
    mode: str                 # HD, 2SD, 3SD
    num_param: int            # dv 하나의 파라미터 수 (CH 개수 + TH 개수)
    ch_len: int               # CH 개수
    dv_from: np.ndarray
    dv_to: np.ndarray
    max_value: np.ndarray     # 파라미터별 최대값 (길이 num_param)
    min_value: np.ndarray
    max_iter: int             # 쌓는 그룹의 iteration 수

    @property
    def num_dv(self) -> int:
        return len(self.dv_from)

    @property
    def row_length(self) -> int:
        return self.num_dv * self.num_param

    @classmethod
    def from_base_llr_matrix(cls, llr_matrix: LLRMatrix, max_iter: int) -> "MatrixTemplate":
        return cls(mode=llr_matrix.mode, num_param=llr_matrix.num_param, ch_len=llr_matrix.ch_len,
                   dv_from=np.array(llr_matrix.dv_from, np.int32), dv_to=np.array(llr_matrix.dv_to, np.int32),
                   max_value=np.array(llr_matrix.max_value, np.int32), min_value=np.array(llr_matrix.min_value, np.int32),
                   max_iter=int(max_iter))


@dataclass
class StackedRow:
    values: np.ndarray        # int32, 길이 num_dv * num_param
    csw: int                  # 첫 row -1, 그 뒤 8의 배수 (8-1408)


def correct_row_values(values, template: MatrixTemplate) -> np.ndarray:
    """헤더 min/max로 자르고 dv마다 CH 구간과 TH 구간을 각각 내림차순으로 정렬한 새 배열을 돌려준다."""
    values = np.asarray(values)
    if values.size != template.row_length:
        raise ValueError(f"row 길이 {values.size} != {template.num_dv} x {template.num_param}")
    out = np.array(values, np.int32).reshape(template.num_dv, template.num_param)
    out = np.minimum(out, template.max_value)
    out = np.maximum(out, template.min_value)
    out[:, :template.ch_len] = -np.sort(-out[:, :template.ch_len], axis=1)
    out[:, template.ch_len:] = -np.sort(-out[:, template.ch_len:], axis=1)
    return out.reshape(-1).astype(np.int32)


def generate_random_row_values(template: MatrixTemplate, rng: np.random.Generator) -> np.ndarray:
    """헤더 범위에서 난수로 채운 뒤 정렬 규칙을 적용한 row 값."""
    raw = rng.integers(template.min_value, template.max_value + 1, size=(template.num_dv, template.num_param))
    return correct_row_values(raw.reshape(-1), template)


def mutate_row_values(values, template: MatrixTemplate, rng: np.random.Generator,
                      num_elements: int, mutation_range: int) -> np.ndarray:
    """서로 다른 num_elements개 위치에 ±(1..mutation_range)를 더한 뒤 정렬 규칙을 적용한 row 값."""
    out = np.array(values, np.int64).reshape(-1)
    count = min(int(num_elements), out.size)
    positions = rng.choice(out.size, size=count, replace=False)
    magnitudes = rng.integers(1, int(mutation_range) + 1, size=count)
    signs = rng.choice(np.array([-1, 1]), size=count)
    out[positions] += magnitudes * signs
    return correct_row_values(out, template)


def build_base_llr_matrix(template: MatrixTemplate, rows: list, name: str = "stacked") -> LLRMatrix:
    """row 목록을 그룹 1개(CSW 선택, iteration 1-max_iter, restart 없음)짜리 2_LDPC_base LLRMatrix로 만든다."""
    row_tuples = [(np.asarray(row.values, np.int64), int(row.csw), 1, template.max_iter, -1) for row in rows]
    return LLRMatrix(template.mode, template.num_param, template.dv_from, template.dv_to,
                     [len(rows)], [GROUP_TYPE_CSW], [], template.max_value, template.min_value,
                     row_tuples, name=name)


def save_stacked_matrix(template: MatrixTemplate, rows: list, path: str) -> None:
    """DAO 형식 텍스트 파일로 저장한다 (2_LDPC_base가 읽으려면 이름에 LLR_MATRIX_{모드}_가 있어야 한다)."""
    build_base_llr_matrix(template, rows).save(path)


def _ceil_to_step(value: int) -> int:
    return int(math.ceil(int(value) / STEP_CSW)) * STEP_CSW


def ceil_to_csw_step(value: int) -> int:
    """8의 배수로 올림한 뒤 [MIN_CSW, MAX_CSW]로 자른다."""
    return max(MIN_CSW, min(_ceil_to_step(value), MAX_CSW))


def new_row_csw_threshold(err_per_iter, csw_per_iter, prev_threshold: Optional[int],
                          max_iter: int) -> Optional[tuple]:
    """새 row의 CSW 문턱과 그 출처 iteration (설계 4.3 ㉰).

    prev_threshold가 None이면(앞 row가 문턱 -1인 첫 row) 상한은 MAX_CSW, 아니면 prev_threshold - STEP_CSW.
    iteration j(1부터)는 j <= min(돈 iteration 수, max_iter - 1)이고 올림한 CSW가 [MIN_CSW, 상한] 안이면 쓸 수 있다.
    최소 잔여 에러가 처음 나오는 iteration i*가 쓸 수 있으면 그것, 아니면 쓸 수 있는 iteration 가운데
    잔여 에러가 가장 작은(같으면 이른) 것, 없으면 None.
    """
    err = np.asarray(err_per_iter)
    csw = np.asarray(csw_per_iter)
    count = min(len(err), len(csw))
    upper = MAX_CSW if prev_threshold is None else int(prev_threshold) - STEP_CSW
    if count == 0 or upper < MIN_CSW:
        return None
    last_usable = min(count, int(max_iter) - 1)

    def usable(iteration: int) -> bool:
        rounded = _ceil_to_step(csw[iteration - 1])
        return MIN_CSW <= rounded <= upper

    best_iteration = int(np.argmin(err[:count])) + 1
    if best_iteration <= last_usable and usable(best_iteration):
        return _ceil_to_step(csw[best_iteration - 1]), best_iteration
    candidates = [j for j in range(1, last_usable + 1) if usable(j)]
    if not candidates:
        return None
    chosen = min(candidates, key=lambda j: (int(err[j - 1]), j))
    return _ceil_to_step(csw[chosen - 1]), chosen


def takeover_iteration(csw_per_iter, threshold: int) -> Optional[int]:
    """문턱 이하의 CSW가 처음 나오는 iteration j의 다음 iteration (j + 1). 없으면 None."""
    hits = np.flatnonzero(np.asarray(csw_per_iter) <= int(threshold))
    if len(hits) == 0:
        return None
    return int(hits[0]) + 2
