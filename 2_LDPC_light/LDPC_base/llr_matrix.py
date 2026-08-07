"""DAO LLR_MATRIX 텍스트 포맷 로더 + iteration/CSW별 테이블 row 선택.

파일 포맷 (DAO_LLR_MATRIX.py Read_Input_LLR_Matrix와 동일, 빈 줄 무시):
  num_parameter_each_set / num_dv / dv_from / dv_to / num_group /
  num_row_each_group / type_each_group / num_restart / [restart_iter] /
  max_value / min_value / row들
row = [dv별 (ch..., th...) x num_dv] + CSW + iter_start + iter_end + floor_flag

디코딩 모드(HD/2SD/3SD)는 파일에 없으므로 파일명으로 판별한다 (사용자 결정 2026-08-06):
  LLR_MATRIX_HD_0.txt / LLR_MATRIX_2SD_0.txt / LLR_MATRIX_3SD_0.txt
ch 개수 = HD 1, 2SD 2, 3SD 4 (= 2^(init_n-1)), th 개수 = num_param - ch 개수.

런타임 선택 (decoder.cpp Get_Cur_LLR_Idx_FILE 대응):
- iteration이 속한 그룹 선택 → 그룹 타입 0(ITER)이면 iteration 서브구간으로,
  1(CSW)이면 직전 iteration의 check-sum weight를 row별 CSW 임계값과 비교해 row 선택
  (아래에서부터 처음으로 csw <= 임계값인 row, 없으면 그룹 첫 row)
- restart iteration: CN 상태 클리어(syndrome은 유지) 후 restart row의 값을 그대로 사용.
  restart row의 -1도 C++ 산술에 그대로 들어간다 — ch=-1(채널 기여 거의 0),
  th=-1(|V2C|가 항상 th1 이상 → 전부 최대 레벨) → 사실상 순수 syndrome bit-flip
  iteration이 된다. DAO가 이 동작 기준으로 최적화하므로 여기서도 동일하게 따른다
- 마지막 row의 iter_end가 곧 max_iteration (사용자 확인 2026-08-06)

dv 매핑: column degree가 어느 dv_from/dv_to 구간에도 없으면 에러 (사용자 결정 —
원본 C++의 조용한 col_idx=0 fallback은 재현하지 않음).

_validate의 형식 제약은 DAO 산출 규칙 기준이다 (사용자 확정 2026-08-07). DAO는 실제
운용용이라 C++ 로더보다 rule이 정확하며, C++(local_opt.cpp)에 검사가 없는 것은 검증을
생략한 것일 뿐이다. 검사 항목: 그룹 겹침 금지, 1..max_iter 커버리지(빈틈 금지),
restart 그룹은 단일 row/단일 iteration, restart 그룹은 마지막이면 안 됨.
"""
import os
import re
import warnings

import numpy as np

MODE_CH_LEN = {"HD": 1, "2SD": 2, "3SD": 4}
GROUP_TYPE_ITER, GROUP_TYPE_CSW = 0, 1          # common.h:756-757

_NAME_RE = re.compile(r"LLR_MATRIX_(HD|2SD|3SD)_", re.IGNORECASE)


class LLRMatrix:
    def __init__(self, mode, num_param, dv_from, dv_to, group_rows, group_type,
                 restart_iters, max_value, min_value, rows, name=""):
        """rows: (values(num_dv*num_param), csw, iter_start, iter_end, floor) 튜플 리스트."""
        self.name = name
        self.mode = mode
        self.ch_len = MODE_CH_LEN[mode]
        self.num_param = int(num_param)
        self.th_len = self.num_param - self.ch_len
        if self.th_len <= 0:
            raise ValueError(f"{name}: num_param {num_param}이 {mode} ch {self.ch_len}개 이하")
        self.dv_from = np.asarray(dv_from, np.int32)
        self.dv_to = np.asarray(dv_to, np.int32)
        self.num_dv = len(self.dv_from)
        self.group_rows = [int(n) for n in group_rows]
        self.group_type = [int(t) for t in group_type]
        self.restart_iters = set(int(i) for i in restart_iters)
        self.max_value = np.asarray(max_value, np.int32)
        self.min_value = np.asarray(min_value, np.int32)

        values_flat = np.array([r[0] for r in rows], np.float32)  # (R, num_dv*num_param)
        self.row_values = values_flat.reshape(len(rows), self.num_dv, self.num_param)
        self.row_ch = self.row_values[:, :, :self.ch_len]       # (R, num_dv, ch_len)
        self.row_th = self.row_values[:, :, self.ch_len:]       # (R, num_dv, th_len)
        self.row_csw = np.array([r[1] for r in rows], np.int64)
        self.row_iter = np.array([[r[2], r[3]] for r in rows], np.int32)  # (R, 2)
        self.max_iter = int(self.row_iter[-1, 1])

        # 그룹 → row 구간
        self.group_slices = []
        off = 0
        for n in self.group_rows:
            self.group_slices.append((off, off + n))
            off += n
        self._validate()

    def _validate(self):
        if len(self.dv_to) != self.num_dv:
            raise ValueError(f"{self.name}: dv_from/dv_to 길이 불일치")
        if len(self.group_type) != len(self.group_rows):
            raise ValueError(f"{self.name}: 그룹 수 불일치")
        if self.group_slices[-1][1] != len(self.row_csw):
            raise ValueError(f"{self.name}: 총 row 수가 그룹별 합과 불일치")
        # 겹침 금지 + 커버리지 검사 (DAO 규칙, 모듈 docstring 참조).
        # 겹침 금지는 _group_of_iter()의 정방향 첫 매칭 순회가 안전하기 위한 전제이기도
        # 하다 (제약과 순회 방향이 한 쌍 — 겹침을 허용하려면 순회를 C++처럼 역방향으로
        # 함께 바꿔야 함).
        covered_end = 0                      # 마지막으로 덮인 iteration
        for group_idx, (row_start, row_end) in enumerate(self.group_slices):
            iter_start = int(self.row_iter[row_start, 0])
            iter_end = int(self.row_iter[row_end - 1, 1])
            if iter_end < iter_start:
                raise ValueError(f"{self.name}: 그룹 {group_idx + 1} iter_end < iter_start")
            if covered_end > 0 and iter_start <= covered_end:
                raise ValueError(
                    f"{self.name}: 그룹 {group_idx + 1} 구간 [{iter_start},{iter_end}]이 "
                    f"이전 그룹과 겹침 (DAO 규칙 위반)")
            if max(iter_start, 1) > covered_end + 1:
                raise ValueError(
                    f"{self.name}: iteration {covered_end + 1}~{max(iter_start, 1) - 1}을 "
                    f"덮는 그룹 없음")
            covered_end = iter_end
            # ITER 타입 다중 row 그룹은 내부 row 구간도 같은 규칙(겹침·빈틈 금지)으로
            # 연속이어야 한다 — 어기면 row_index()가 시뮬 도중에야 실패한다
            if self.group_type[group_idx] == GROUP_TYPE_ITER and row_end - row_start > 1:
                prev_end = iter_start - 1
                for row in range(row_start, row_end):
                    r_start, r_end = int(self.row_iter[row, 0]), int(self.row_iter[row, 1])
                    if r_end < r_start:
                        raise ValueError(f"{self.name}: row {row + 1} iter_end < iter_start")
                    if r_start != prev_end + 1:
                        raise ValueError(
                            f"{self.name}: 그룹 {group_idx + 1} 내부 row 구간이 연속이 아님 "
                            f"(row {row + 1} iter_start {r_start}, 기대 {prev_end + 1})")
                    prev_end = r_end
        for iteration in self.restart_iters:
            group_idx = self._group_of_iter(iteration)
            row_start, row_end = self.group_slices[group_idx]
            if (row_end - row_start != 1
                    or self.row_iter[row_start, 0] != self.row_iter[row_start, 1]):
                raise ValueError(
                    f"{self.name}: restart iter {iteration} 그룹이 단일 iteration/row가 아님")
            if group_idx == len(self.group_slices) - 1:
                raise ValueError(f"{self.name}: restart 그룹 뒤에 그룹이 없음")
        # th 내림차순 점검 (경고만): C++ 소비부는 캐스케이드라 비단조 th도 그대로 소비
        # 하지만(디코더도 동일 캐스케이드로 맞춤), 작성 실수일 가능성이 높아 알린다.
        if not np.all(self.row_th[:, :, :-1] >= self.row_th[:, :, 1:]):
            warnings.warn(
                f"{self.name}: th가 내림차순이 아닌 row 존재 — 캐스케이드 의미"
                f"(th1부터 순서 비교)로 소비되며, 의도한 값인지 확인할 것")

    # ---------- 파일 입출력 ----------
    @classmethod
    def load(cls, path):
        m = _NAME_RE.search(os.path.basename(path))
        if not m:
            raise ValueError(
                f"{path}: 파일명에서 모드 판별 불가 — LLR_MATRIX_{{HD|2SD|3SD}}_*.txt 형식이어야 함")
        mode = m.group(1).upper()
        with open(path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        parsed = [np.array([int(v) for v in ln.split()], np.int64) for ln in lines]

        i = 0
        num_param = int(parsed[i][0]); i += 1
        num_dv = int(parsed[i][0]); i += 1
        dv_from = parsed[i]; i += 1
        dv_to = parsed[i]; i += 1
        num_group = int(parsed[i][0]); i += 1
        group_rows = parsed[i]; i += 1
        group_type = parsed[i]; i += 1
        num_restart = int(parsed[i][0]); i += 1
        restart_iters = parsed[i] if num_restart > 0 else np.array([], np.int64)
        if num_restart > 0:
            i += 1
        max_value = parsed[i]; i += 1
        min_value = parsed[i]; i += 1

        if len(dv_from) != num_dv or len(group_rows) != num_group:
            raise ValueError(f"{path}: 헤더 개수 필드와 배열 길이 불일치")
        total_rows = int(np.sum(group_rows))
        row_lines = parsed[i: i + total_rows]
        if len(row_lines) != total_rows:
            raise ValueError(f"{path}: row 수 {len(row_lines)} != 기대 {total_rows}")
        rows = []
        for row_line in row_lines:
            if len(row_line) != num_dv * num_param + 4:
                raise ValueError(f"{path}: row 길이 {len(row_line)} != {num_dv}*{num_param}+4")
            rows.append((row_line[:-4], int(row_line[-4]), int(row_line[-3]),
                         int(row_line[-2]), int(row_line[-1])))
        return cls(mode, num_param, dv_from, dv_to, group_rows, group_type,
                   restart_iters, max_value, min_value, rows,
                   name=os.path.basename(path))

    # ---------- 런타임 ----------
    def col_dv_idx(self, code):
        """column block별 dv 구간 인덱스 (N_b,). 미매칭 dv는 에러."""
        idx = np.full(code.N_b, -1, np.int32)
        for j, dv in enumerate(code.col_deg):
            hit = np.flatnonzero((dv >= self.dv_from) & (dv <= self.dv_to))
            if len(hit) == 0:
                raise ValueError(
                    f"{self.name}: dv={int(dv)} (col block {j})가 dv_from/dv_to "
                    f"{self.dv_from.tolist()}~{self.dv_to.tolist()} 어느 구간에도 없음")
            idx[j] = hit[0]
        return idx

    def is_restart(self, iteration):
        return iteration in self.restart_iters

    def _group_of_iter(self, iteration):
        for group_idx, (row_start, row_end) in enumerate(self.group_slices):
            if self.row_iter[row_start, 0] <= iteration <= self.row_iter[row_end - 1, 1]:
                return group_idx
        raise ValueError(
            f"{self.name}: iteration {iteration}을 덮는 그룹 없음 (max_iter={self.max_iter})")

    def row_index(self, iteration, prev_csw):
        """iteration과 직전 CSW (활성 프레임 수,) → 테이블 row 인덱스 (활성 프레임 수,).

        restart iteration도 자기 row(-1 값 포함)를 그대로 쓴다 (docstring 참조).
        """
        group_idx = self._group_of_iter(iteration)
        row_start, row_end = self.group_slices[group_idx]
        n_active = len(prev_csw)
        if self.group_type[group_idx] == GROUP_TYPE_ITER or row_end - row_start == 1:
            for row in range(row_start, row_end):
                if self.row_iter[row, 0] <= iteration <= self.row_iter[row, 1]:
                    return np.full(n_active, row, np.int64)
            raise ValueError(f"{self.name}: 그룹 {group_idx + 1} 내 iteration {iteration} row 없음")
        # CSW 타입: 아래에서부터 처음으로 prev_csw <= 임계값인 row (없으면 그룹 첫 row)
        selected = np.full(n_active, row_start, np.int64)
        for row in range(row_start + 1, row_end):
            selected = np.where(prev_csw <= self.row_csw[row], row, selected)
        return selected

    @property
    def needs_csw(self):
        """CSW 기반 row 선택이 실제로 쓰이는가 (multi-row CSW 그룹 존재 여부)."""
        return any(t == GROUP_TYPE_CSW and n > 1
                   for t, n in zip(self.group_type, self.group_rows))

    def summary(self):
        groups_str = ", ".join(
            f"g{i + 1}[{self.row_iter[row_start, 0]}~{self.row_iter[row_end - 1, 1]}]"
            f"{'R' if int(self.row_iter[row_start, 0]) in self.restart_iters else ''}"
            f"x{row_end - row_start}"
            for i, (row_start, row_end) in enumerate(self.group_slices))
        return (f"LLRMatrix {self.name}: mode={self.mode} (ch{self.ch_len}+th{self.th_len}), "
                f"dv={self.dv_from.tolist()}~{self.dv_to.tolist()}, max_iter={self.max_iter}, "
                f"groups: {groups_str}")
