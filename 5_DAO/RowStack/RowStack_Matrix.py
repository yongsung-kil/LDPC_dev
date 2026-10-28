"""쌓는 매트릭스의 모델과 규칙 (1판 설계 4.3절, 탐색 규칙 2판 3.5-3.7절).

- MatrixTemplate: 기존 LLR matrix의 헤더(모드, dv 구간, 값 범위)와 복호 iteration 상한
- StackedRow: row 하나 (값 배열과 CSW 문턱). 첫 row의 문턱은 -1, 그 뒤는 8의 배수이며 아래로 갈수록 엄격히 작아진다
- 값 규칙: 헤더 min/max로 자르고 dv마다 CH 구간과 TH 구간을 각각 내림차순 정렬 (DAO Correct_Ch_Th_In_Row와 같은 결과)
- 변이: 매트릭스의 모든 row 값 가운데 몇 자리를 골라 ±폭 안에서 바꾼다 (mutate_matrix_values)
- CSW 문턱 규칙(new_row_csw_threshold): 부모 궤적의 최소 CSW에 margin을 더해 8의 배수로 올린 값.
  앞 row 문턱보다 8 이상 작아야 하고, 초기 CSW보다 작아야 하며, 새 예산 안에서 처음 닿는 iteration이 있어야 한다
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
    max_iter: int             # 복호 iteration 상한 (MAX_DECODING_ITERATION)

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


def _add_random_deltas(flat: np.ndarray, rng: np.random.Generator, num_elements: int, mutation_range: int) -> np.ndarray:
    out = np.array(flat, np.int64).reshape(-1)
    count = min(int(num_elements), out.size)
    positions = rng.choice(out.size, size=count, replace=False)
    magnitudes = rng.integers(1, int(mutation_range) + 1, size=count)
    signs = rng.choice(np.array([-1, 1]), size=count)
    out[positions] += magnitudes * signs
    return out


def mutate_row_values(values, template: MatrixTemplate, rng: np.random.Generator,
                      num_elements: int, mutation_range: int) -> np.ndarray:
    """row 하나의 서로 다른 num_elements개 자리에 ±(1..mutation_range)를 더한 뒤 정렬 규칙을 적용한 값."""
    return correct_row_values(_add_random_deltas(values, rng, num_elements, mutation_range), template)


def mutate_matrix_values(rows: list, template: MatrixTemplate, rng: np.random.Generator,
                         num_elements: int, mutation_range: int) -> list:
    """매트릭스 전체(모든 row의 CH, TH 값)에서 서로 다른 num_elements개 자리를 골라 ±(1..mutation_range)를 더하고
    row마다 정렬 규칙을 적용한 새 row 목록. CSW 문턱은 그대로다."""
    flat = np.concatenate([np.asarray(row.values, np.int64).reshape(-1) for row in rows])
    mutated = _add_random_deltas(flat, rng, num_elements, mutation_range)
    length = template.row_length
    return [StackedRow(correct_row_values(mutated[index * length:(index + 1) * length], template), row.csw)
            for index, row in enumerate(rows)]


def build_base_llr_matrix(template: MatrixTemplate, rows: list, max_iter: Optional[int] = None,
                          name: str = "stacked") -> LLRMatrix:
    """row 목록을 그룹 1개(CSW 선택, iteration 1-max_iter, restart 없음)짜리 2_LDPC_base LLRMatrix로 만든다.
    max_iter를 생략하면 템플릿의 상한을 쓴다."""
    iterations = template.max_iter if max_iter is None else int(max_iter)
    row_tuples = [(np.asarray(row.values, np.int64), int(row.csw), 1, iterations, -1) for row in rows]
    return LLRMatrix(template.mode, template.num_param, template.dv_from, template.dv_to,
                     [len(rows)], [GROUP_TYPE_CSW], [], template.max_value, template.min_value,
                     row_tuples, name=name)


def save_stacked_matrix(template: MatrixTemplate, rows: list, path: str, max_iter: Optional[int] = None) -> None:
    """DAO 형식 텍스트 파일로 저장한다 (2_LDPC_base가 읽으려면 이름에 LLR_MATRIX_{모드}_가 있어야 한다)."""
    build_base_llr_matrix(template, rows, max_iter=max_iter).save(path)


def _ceil_to_step(value: int) -> int:
    return int(math.ceil(int(value) / STEP_CSW)) * STEP_CSW


def ceil_to_csw_step(value: int) -> int:
    """8의 배수로 올림한 뒤 [MIN_CSW, MAX_CSW]로 자른다."""
    return max(MIN_CSW, min(_ceil_to_step(value), MAX_CSW))


def takeover_iteration(csw_per_iter, threshold: int, initial_csw: int) -> Optional[int]:
    """row가 이어받는 첫 iteration. 초기 CSW가 문턱 이하이면 1, 아니면 문턱 이하의 CSW가 처음 나오는 iteration j의
    다음 iteration (j + 1). 없으면 None."""
    if int(initial_csw) <= int(threshold):
        return 1
    hits = np.flatnonzero(np.asarray(csw_per_iter) <= int(threshold))
    if len(hits) == 0:
        return None
    return int(hits[0]) + 2


def new_row_csw_threshold(csw_per_iter, prev_threshold: Optional[int], initial_csw: int, margin: int,
                          new_max_iter: int) -> Optional[tuple]:
    """새 row의 CSW 문턱과 이어받는 iteration (탐색 규칙 2판 3.6절).

    문턱 = ceil8(부모 궤적의 최소 CSW + margin). 앞 row 문턱(prev_threshold, 첫 row이면 None)보다 8 이상 작아야 하므로
    크면 prev_threshold - 8로 내리고, MAX_CSW(1408)도 넘지 않는다. 문턱이 MIN_CSW 아래이거나 초기 CSW 이상이면 None.
    이어받는 iteration은 궤적에서 CSW가 처음 문턱 이하가 되는 iteration의 다음이며 새 예산(new_max_iter) 안이어야 한다.
    """
    csw = np.asarray(csw_per_iter)
    if csw.size == 0:
        return None
    upper = MAX_CSW if prev_threshold is None else int(prev_threshold) - STEP_CSW
    threshold = min(_ceil_to_step(int(csw.min()) + int(margin)), upper)
    if threshold < MIN_CSW or threshold >= int(initial_csw):
        return None
    takeover = takeover_iteration(csw, threshold, initial_csw)
    if takeover is None or takeover > int(new_max_iter):
        return None
    return threshold, takeover
