import os
import copy
import numpy as np
from dataclasses import dataclass
from typing import Optional
from DAO_Config import *
from DAO_Constants import *

@dataclass
class LLR_Header:
    num_parameter_each_set: int     # DV가 하나가 보유하는 파라미터 수
    num_dv: int                     # DV 개수
    dv_from: np.ndarray             # DV 시작 인덱스 목록
    dv_to: np.ndarray               # DV 종료 인덱스 목록
    num_group: int                  # 그룹 총 개수
    num_row_each_group: np.ndarray  # 그룹별 행 개수
    type_each_group: np.ndarray     # 그룹별 유형 식별자
    num_restart: int                # 재시작 지점 수
    restart_iter: np.ndarray        # 재시작 반복 번호 배열
    max_value: np.ndarray           # 파라미터별 최대 허용값
    min_value: np.ndarray           # 파라미터별 최소 허용값

@dataclass
class LLR_Row:
    """LLR 매트릭스의 한 행을 보관한다.
    """
    ch_th_values: np.ndarray  # DV별 CH/TH 값 묶음
    CSW: int
    iter_start: int
    iter_end: int
    floor_flag: int           # SW 분기 index. -1은 분기 없음, 0 이상은 그 구간 안의 분기 번호. 같은 값이 이어지는 그룹들은 한 묶음으로 변이한다
    is_group_restart: bool = False

class LLR_MATRIX:

    def __init__(self, init_n: int, matrix_idx: int, is_HBF_OPT: bool, input_dir: Optional[str] = None):
        self.init_n = init_n
        self.is_HBF_OPT: Optional[bool] = None
        if init_n == 1:
            self.decoder_mode_str = "HD"
            self.is_HBF_OPT = is_HBF_OPT
            self.HBF_max_iteration = HBF_OPT_CONFIG.HBF_MAX_ITERATION
        elif init_n == 2:
            self.decoder_mode_str = "2SD"
            self.is_HBF_OPT = False
            self.HBF_max_iteration = None
        elif init_n == 3:
            self.decoder_mode_str = "3SD"
            self.is_HBF_OPT = False
            self.HBF_max_iteration = None
        else:
            raise ValueError("init_n must be 1 (HD), 2 (2SD), or 3 (3SD)")

        self.matrix_idx = matrix_idx
        self.header: LLR_Header
        self.groups: list[list[LLR_Row]] = []  # 그룹별 행 컨테이너
        self.restart_groups: list[int] = []

        # SW 분기 배치 (Build_SW_Branch_Layout이 groups에서 계산한다. 헤더는 보지 않는다)
        self.group_branch_idx: list[int] = []                      # 그룹별 분기 index (첫 row의 floor_flag)
        self.bundle_of_group: list[list[int]] = []                 # 그룹별 묶음 (같은 분기 index가 이어지는 그룹 index 목록)
        self.span_of_group: list[Optional[tuple[int, int, int]]] = []  # 그룹별 (구간 시작, 구간 끝, 분기 수). 분기 없으면 None
        self.has_sw_branch: bool = False
        self.sw_layout_error: Optional[str] = None

        # ===== FER 변수 설명 =====
        # - raw_FER:  LOAD_NONE 모드에서 측정됨 (seed 없이 ECC 테스트), 다른 모드에서는 1.0
        # - seed_FER: LOAD_SEED/LOAD_VECTOR 모드에서 측정됨 (seed로 ECC 테스트), 다른 모드에서는 1.0
        # - FERs:     비교에 사용되는 값 (load_seed_mode → seed_FER, otherwise → raw_FER)
        # - 초기값 1.0 = 아직 테스트되지 않음 (worst case)

        # Full 테스트 결과 (Update 판단 기준)
        self.FERs: list[float] = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS      # 비교용 FER (raw 또는 seed)
        self.raw_FERs: list[float] = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS  # LOAD_NONE 모드에서 측정
        self.seed_FERs: list[float] = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS # LOAD_SEED 모드에서 측정

        # Partial 테스트 결과 (Two-stage 모드 전용, 1차 필터링 기준)
        self.FERs_partial: list[float] = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.raw_FERs_partial: list[float] = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.seed_FERs_partial: list[float] = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS

        # 평균 디코딩 반복 횟수 (FER 동일 시 tie-breaker, -1.0 = 미테스트)
        self.avg_iterations: list[float] = [-1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.avg_iterations_partial: list[float] = [-1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS

        # 에러/테스트 카운트 (Test Summary 출력용)
        self.num_errors: list[int] = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.num_tests: list[int] = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.num_errors_partial: list[int] = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.num_tests_partial: list[int] = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        self.Read_Input_LLR_Matrix(input_dir=input_dir)

    @staticmethod
    def _is_non_increasing(values: np.ndarray) -> bool:
        if len(values) <= 1:
            return True
        return bool(np.all(values[:-1] >= values[1:]))

    def Is_Row_In_HBF_Iterations(self, row: LLR_Row) -> bool:
        """HBF 최적화 모드에서 row가 HBF 구간(iteration 1 ~ HBF_MAX_ITERATION) 안에 있는지 알려준다.

        HBF 구간에서 디코더는 dv_idx 0(가장 높은 DV, row의 첫 CH와 TH 묶음)을 1 bit 정밀도로 처리해 그 TH를 읽지 않는다.
        그래서 HBF 구간의 row는 dv_idx 0의 TH를 HBF_OPT_TH_CONSTANT_VAL로 고정하고 변이와 난수 생성 대상에서 뺀다.
        HBF 구간 뒤의 row는 dv_idx 0의 TH도 다른 DV처럼 다룬다.
        row는 HBF 구간의 경계를 걸치지 않으므로(Is_LLR_Valid의 HBF2 규칙) 끝 iteration으로 판단한다.
        """
        return bool(self.is_HBF_OPT) and row.iter_end <= HBF_OPT_CONFIG.HBF_MAX_ITERATION

    def Build_SW_Branch_Layout(self) -> Optional[str]:
        """groups에서 SW 분기 배치(그룹별 분기 index, 묶음, 구간)를 다시 계산한다.

        분기 index는 각 row의 마지막 칸(floor_flag)이다. 헤더 type_each_group이 10 이상이면 {분기 수}{분기 index}
        표시이고(10은 분기 1개짜리 묶음, 20과 21은 분기 2개), 10 미만이면 보통 그룹이다. 구간은 분기 index 0으로
        시작해 index가 0으로 되돌아가거나 -1이 나오기 전까지의 그룹들이 덮는 iteration 범위다. 분기 0이 그대로
        이어지는 두 구간은 헤더 표시 값이 바뀌는 자리(예: 10 뒤에 20)에서 갈린다. 구간 안에서 index가 1 늘면
        iteration은 구간 시작으로 되돌아가고, 모든 분기는 구간의 시작과 끝을 똑같이 덮는다. 묶음은 한 구간 안에서
        분기 index가 같은 그룹들이고, 분기가 없는 그룹은 그룹 하나가 묶음 하나다.

        Returns:
            Optional[str]: 배치가 규칙에 어긋나면 그 이유 (sw_layout_error에도 남는다). 문제 없으면 None
        """
        num_groups = len(self.groups)
        self.group_branch_idx = [int(group[0].floor_flag) if group else SW_BRANCH_NONE for group in self.groups]
        self.has_sw_branch = any(idx != SW_BRANCH_NONE for idx in self.group_branch_idx)
        self.bundle_of_group = [[g] for g in range(num_groups)]
        self.span_of_group = [None] * num_groups
        self.sw_layout_error = None
        if self.groups and all(self.groups):
            self.max_iteration = max(group[-1].iter_end for group in self.groups)

        header_types = list(self.header.type_each_group) if len(self.header.type_each_group) == num_groups else [0] * num_groups

        def header_marker(g: int) -> Optional[int]:
            """헤더의 분기 표시 값 전체 ({분기 수}{분기 index}). 10 미만이면 표시 없음"""
            type_value = int(header_types[g])
            return type_value if type_value >= 10 else None

        def fail(message: str) -> str:
            self.sw_layout_error = message
            return message

        span_members: list[int] = []
        span_start = None
        span_end = None
        current_branch = None          # None이면 구간 밖
        current_bundle: list[int] = []
        prev_end = None
        prev_group_idx = None

        def close_span() -> Optional[str]:
            nonlocal span_end
            if current_branch == 0:
                span_end = prev_end
            elif prev_end != span_end:
                return f"SW branch {current_branch} ends at iteration {prev_end} but its span ends at {span_end}"
            for member in span_members:
                self.span_of_group[member] = (span_start, span_end, current_branch + 1)
            return None

        for g_idx, group in enumerate(self.groups):
            if not group:
                continue
            branch = self.group_branch_idx[g_idx]
            start = int(group[0].iter_start)
            end = int(group[-1].iter_end)

            if branch == SW_BRANCH_NONE:
                if current_branch is not None:
                    error = close_span()
                    if error is not None:
                        return fail(error)
                    expected_start = span_end + 1
                    span_members = []
                    current_branch = None
                else:
                    expected_start = start if prev_end is None else prev_end + 1
                current_bundle = [g_idx]
            else:
                if current_branch is None:
                    starts_new_span = True
                elif branch == 0 and current_branch > 0:
                    starts_new_span = True
                elif branch == 0 and current_branch == 0 and header_marker(g_idx) != header_marker(prev_group_idx):
                    # 분기 0이 이어지지만 헤더의 분기 표시 값이 바뀌면 새 구간이다 (예: 10인 묶음 뒤에 20인 분기 구간)
                    starts_new_span = True
                else:
                    starts_new_span = False

                if starts_new_span:
                    if branch != 0:
                        return fail(f"Group {g_idx} opens an SW span with branch {branch}; a span must start with branch 0")
                    if current_branch is not None:
                        error = close_span()
                        if error is not None:
                            return fail(error)
                        expected_start = span_end + 1
                    else:
                        expected_start = start if prev_end is None else prev_end + 1
                    span_start = start
                    span_end = None
                    current_branch = 0
                    span_members = []
                    current_bundle = []
                elif branch == current_branch:
                    expected_start = prev_end + 1
                elif branch == current_branch + 1:
                    if branch > MAX_SW_BRANCH:
                        return fail(f"Group {g_idx} branch {branch} exceeds MAX_SW_BRANCH {MAX_SW_BRANCH}")
                    if current_branch == 0:
                        span_end = prev_end
                    elif prev_end != span_end:
                        return fail(f"SW branch {current_branch} ends at iteration {prev_end} but its span ends at {span_end}")
                    expected_start = span_start
                    current_branch = branch
                    current_bundle = []
                else:
                    return fail(
                        f"Group {g_idx} branch {branch} follows branch {current_branch}; "
                        f"the branch index must stay, increase by 1, or return to 0"
                    )
                span_members.append(g_idx)
                current_bundle.append(g_idx)

            if start != expected_start:
                return fail(f"Group {g_idx} iter_start must be {expected_start} (SW branch {branch}), got {start}")
            self.bundle_of_group[g_idx] = current_bundle
            prev_end = end
            prev_group_idx = g_idx

        if current_branch is not None:
            error = close_span()
            if error is not None:
                return fail(error)
        return None

    def Build_LLR_Matrix_Output_Lines(self, compare_with: Optional['LLR_MATRIX'] = None) -> list[str]:
        """LLR 매트릭스를 파일 저장용 문자열로 변환한다.

        Args:
            compare_with (Optional[LLR_MATRIX]): 비교할 optimal 매트릭스. 있으면 차이 부분에 * 표시
        """
        h = self.header
        opt_h = compare_with.header if compare_with else None

        # Header 비교 함수
        def format_with_diff(value, opt_value, suffix=""):
            if opt_value is not None and value != opt_value:
                return f"{value}*{suffix}"
            return f"{value}{suffix}"

        # num_row_each_group 비교 (배열)
        def format_array_with_diff(arr, opt_arr):
            if opt_arr is None:
                return "\t".join(map(str, arr))
            result = []
            for i, val in enumerate(arr):
                if i < len(opt_arr):
                    if val != opt_arr[i]:
                        result.append(f"{val}*")
                    else:
                        result.append(str(val))
                else:
                    result.append(f"{val}*")  # 추가된 부분
            return "\t".join(result)

        lines = [
            str(h.num_parameter_each_set),
            "",
            str(h.num_dv),
            "",
            "\t".join(map(str, h.dv_from)),
            "\t".join(map(str, h.dv_to)),
            "",
            format_with_diff(h.num_group, opt_h.num_group if opt_h else None),
            "",
            format_array_with_diff(h.num_row_each_group, opt_h.num_row_each_group if opt_h else None),
            format_array_with_diff(h.type_each_group, opt_h.type_each_group if opt_h else None),
            "",
            str(h.num_restart),
            "",
        ]

        if h.num_restart > 0:
            lines.append("\t".join(map(str, h.restart_iter)))
            lines.append("")

        lines.append("\t".join(map(str, h.max_value)))
        lines.append("\t".join(map(str, h.min_value)))
        lines.append("")

        # Groups와 rows 비교
        for g_idx, group in enumerate(self.groups):
            opt_group = None
            if compare_with and g_idx < len(compare_with.groups):
                opt_group = compare_with.groups[g_idx]

            for r_idx, row in enumerate(group):
                opt_row = None
                if opt_group and r_idx < len(opt_group):
                    opt_row = opt_group[r_idx]

                # ch_th_values 비교 (compare_with가 있을 때만)
                matrix_parts = []
                for i, value in enumerate(row.ch_th_values):
                    if compare_with and opt_row and i < len(opt_row.ch_th_values):
                        if int(value) != int(opt_row.ch_th_values[i]):
                            matrix_parts.append(f"{int(value):2d}*")
                        else:
                            matrix_parts.append(f"{int(value):2d}")
                    elif compare_with:
                        # compare_with는 있지만 opt_row 없거나 인덱스 범위 밖
                        matrix_parts.append(f"{int(value):2d}*")
                    else:
                        # compare_with 없으면 그냥 출력
                        matrix_parts.append(f"{int(value):2d}")

                matrix_part = "\t".join(matrix_parts)

                # CSW, iter_start, iter_end, floor_flag 비교
                if compare_with and not opt_row:
                    # compare_with는 있지만 opt_row가 없으면 (추가된 row) 모든 필드에 * 추가
                    csw_str = f"{row.CSW:4d}*"
                    iter_start_str = f"{row.iter_start:4d}*"
                    iter_end_str = f"{row.iter_end:4d}*"
                    floor_flag_str = f"{row.floor_flag}*"
                elif compare_with and opt_row:
                    # compare_with와 opt_row 둘 다 있으면 값 비교
                    csw_str = f"{row.CSW:4d}*" if row.CSW != opt_row.CSW else f"{row.CSW:4d}"
                    iter_start_str = f"{row.iter_start:4d}*" if row.iter_start != opt_row.iter_start else f"{row.iter_start:4d}"
                    iter_end_str = f"{row.iter_end:4d}*" if row.iter_end != opt_row.iter_end else f"{row.iter_end:4d}"
                    floor_flag_str = f"{row.floor_flag}*" if row.floor_flag != opt_row.floor_flag else f"{row.floor_flag}"
                else:
                    # compare_with 없으면 그냥 출력
                    csw_str = f"{row.CSW:4d}"
                    iter_start_str = f"{row.iter_start:4d}"
                    iter_end_str = f"{row.iter_end:4d}"
                    floor_flag_str = f"{row.floor_flag}"

                line = (
                    f"{matrix_part}\t"
                    f"{csw_str}\t"
                    f"{iter_start_str}\t"
                    f"{iter_end_str}\t"
                    f"{floor_flag_str}"
                )
                lines.append(line)
            lines.append("")

        return lines

    def Change_Max_Iteration(self, input_max_iteration: int):
        if not self.groups:
            raise ValueError("Change_Max_Iteration: No groups in matrix")
        last_group = self.groups[-1]
        if not last_group:
            raise ValueError("Change_Max_Iteration: Last group is empty")
        last_group_start_iteration = last_group[0].iter_start
        if input_max_iteration < last_group_start_iteration:
            raise ValueError(f"New max iteration ({input_max_iteration}) should be greater than last_group_start_iteration ({last_group_start_iteration})")
        self.max_iteration = input_max_iteration
        for row in last_group:
            row.iter_end = input_max_iteration

    def Deep_Copy(self, input_matrix_idx: Optional[int] = None, copy_raw_FER: bool = False, copy_seed_FER: bool = False, copy_partial_FER: bool = False):
        """LLR 매트릭스 객체를 깊은 복사한다.

        FER 관련 필드를 선택적으로 초기화하거나 유지하면서 동일한 구조의 새 객체를 만든다.

        Args:
            input_matrix_idx (Optional[int]): 복사본에 부여할 매트릭스 인덱스. None이면 기존 인덱스를 유지한다.
            copy_raw_FER (bool): True면 원본의 raw FER 값을 복사하고, False면 1.0으로 초기화한다.
            copy_seed_FER (bool): True면 원본의 seed FER 값을 복사하고, False면 1.0으로 초기화한다.
            copy_partial_FER (bool): True면 원본의 Partial 테스트 결과를 복사하고, False면 초기화한다.

        Returns:
            LLR_MATRIX: 설정이 적용된 새로운 LLR 매트릭스 인스턴스.
        """
        new_matrix = copy.deepcopy(self)
        new_matrix_idx = input_matrix_idx if input_matrix_idx is not None else self.matrix_idx

        new_matrix.matrix_idx = new_matrix_idx
        new_matrix.LLR_matrix_file_name = new_matrix.Get_LLR_Matrix_File_Name()

        if not copy_raw_FER:
            new_matrix.raw_FERs = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        if not copy_seed_FER:
            new_matrix.seed_FERs = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        # FERs는 raw/seed 중 하나라도 리셋되면 함께 리셋 (일관성 유지)
        if (not copy_raw_FER) or (not copy_seed_FER):
            new_matrix.FERs = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.avg_iterations = [-1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.num_errors = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.num_tests = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS

        # Partial FER 복사 또는 초기화
        if not copy_partial_FER:
            new_matrix.FERs_partial = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.raw_FERs_partial = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.seed_FERs_partial = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.avg_iterations_partial = [-1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.num_errors_partial = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            new_matrix.num_tests_partial = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        # copy_partial_FER=True면 deepcopy된 값이 그대로 유지됨

        return new_matrix

    def Get_LLR_Matrix_File_Name(self):
        return PATH_CONFIG.LLR_MATRIX_FILE_NAME_TEMPLATE.format(matrix_idx=self.matrix_idx)
    
    def Is_LLR_Valid(self):
        """LLR 매트릭스의 유효성을 검사한다.

        헤더와 그룹 데이터를 순회하며 길이, 단조성, 반복 구간 등 규격을 확인하고 문제 시 메시지를 제공한다.

        Returns:
            tuple[bool, Optional[str]]: (검증 성공 여부, 실패 시 오류 메시지).
        """
        output_msg = "[Validate error!] "
        h = self.header
        if h.num_restart != len(h.restart_iter):
            output_msg = f"num_restart mismatch: {h.num_restart} vs {len(h.restart_iter)}"
            return False, output_msg
        if h.num_group != len(h.num_row_each_group):
            output_msg = "num_group mismatch with num_row_each_group length"
            return False, output_msg
        if h.num_group != len(h.type_each_group):
            output_msg = "num_group mismatch with type_each_group length"
            return False, output_msg
        if len(h.max_value) != h.num_parameter_each_set:
            output_msg = "max_value length mismatch"
            return False, output_msg
        if len(h.min_value) != h.num_parameter_each_set:
            output_msg = "min_value length mismatch"
            return False, output_msg
        if h.num_group != len(self.groups):
            output_msg = f"num_group mismatch with groups: header {h.num_group}, actual {len(self.groups)}"
            return False, output_msg

        total_row_count = 0
        for g_idx, group in enumerate(self.groups):
            total_row_count += len(group)
            starts = [row.iter_start for row in group]
            ends = [row.iter_end for row in group]

            # 빈 그룹 검사
            if len(group) == 0:
                output_msg = f"Group {g_idx} is empty"
                return False, output_msg

            # 헤더의 그룹별 행 수와 실제 행 수 대조
            if len(group) != int(h.num_row_each_group[g_idx]):
                output_msg = f"Group {g_idx} row count mismatch: header {int(h.num_row_each_group[g_idx])}, actual {len(group)}"
                return False, output_msg

            # 그룹 안 모든 row의 분기 index(floor_flag)가 같아야 한 묶음으로 다룰 수 있다 (G9)
            branch_values = {int(row.floor_flag) for row in group}
            if len(branch_values) != 1:
                output_msg = f"Group {g_idx} rows carry different SW branch index (floor_flag): {sorted(branch_values)}"
                return False, output_msg

            # Restart group 판단: restart_groups 리스트 또는 is_group_restart 플래그
            is_restart_group = (g_idx + 1) in self.restart_groups
            if not is_restart_group and len(group) > 0:
                is_restart_group = group[0].is_group_restart

            if is_restart_group:
                if len(group) != 1:
                    output_msg = f"Restart Group {g_idx} must have exactly 1 row, got {len(group)}"
                    return False, output_msg

                if group[0].iter_start != group[0].iter_end:
                    output_msg = (
                        f"Restart Group {g_idx} row must have iter_start == iter_end. "
                        f"Got start={group[0].iter_start}, end={group[0].iter_end}"
                    )
                    return False, output_msg
                # Restart row도 길이와 CSW 규격을 지켜야 파일이 바르게 쓰인다
                expected_len = h.num_parameter_each_set * h.num_dv
                if len(group[0].ch_th_values) != expected_len:
                    output_msg = f"Restart Group {g_idx} row length mismatch. Expected {expected_len}, got {len(group[0].ch_th_values)}"
                    return False, output_msg
                if group[0].CSW != -1:
                    output_msg = f"Restart Group {g_idx} row CSW must be -1, got {group[0].CSW}"
                    return False, output_msg
                continue

            for r, row in enumerate(group):
                expected_len = h.num_parameter_each_set * h.num_dv
                
                # Row 길이 mismatch여부
                if len(row.ch_th_values) != expected_len:
                    output_msg = f"Group {g_idx} Row {r} length mismatch. Expected {expected_len}"
                    return False, output_msg
                
                # SW 분기 index: -1(분기 없음) 또는 0 이상 MAX_SW_BRANCH 이하 (RW2)
                if row.floor_flag != SW_BRANCH_NONE and not (0 <= row.floor_flag <= MAX_SW_BRANCH):
                    output_msg = f"Group {g_idx} Row {r} invalid SW branch index (floor_flag) {row.floor_flag}"
                    return False, output_msg

                # HBF 최적화 모드의 row는 HBF 구간 안에서 끝나거나 HBF 구간 뒤에서 시작한다 (HBF2)
                if self.is_HBF_OPT and row.iter_start <= HBF_OPT_CONFIG.HBF_MAX_ITERATION < row.iter_end:
                    output_msg = (
                        f"In HD_HBF_OPT mode, Group {g_idx} Row {r} iteration {row.iter_start}~{row.iter_end} crosses the HBF boundary: "
                        f"a row must end within iteration 1~{HBF_OPT_CONFIG.HBF_MAX_ITERATION} or start after it"
                    )
                    return False, output_msg

                for dv_idx in range(h.num_dv):
                    start_idx = dv_idx * h.num_parameter_each_set
                    end_idx = start_idx + h.num_parameter_each_set
                    segment = row.ch_th_values[start_idx:end_idx]

                    #각 dv의  ch, th 길이
                    if len(segment) != h.num_parameter_each_set:
                        output_msg = f"Group {g_idx} Row {r} DV {dv_idx} segment length mismatch."
                        return False, output_msg

                    ch_part = segment[:self.ch_length]
                    th_part = segment[self.ch_length:]

                    if self.ch_length > 0 and not np.all(ch_part >= 0): # <-- 추가 검사 로직
                        output_msg = f"Group {g_idx} Row {r} DV {dv_idx} CH values must be positive."
                        return False, output_msg

                    if self.th_length > 0 and not np.all(th_part >= 0): # <-- 추가 검사 로직
                        output_msg = f"Group {g_idx} Row {r} DV {dv_idx} TH values must be positive."
                        return False, output_msg
                    
                    # Th 내림차순정렬
                    if self.th_length > 0 and not self._is_non_increasing(th_part):
                        output_msg = f"Group {g_idx} Row {r} DV {dv_idx} TH values ({th_part}) must be non-increasing."
                        return False, output_msg

                    # HBF 구간의 row는 dv_idx 0의 TH가 HBF_OPT_TH_CONSTANT_VAL이어야 한다
                    if dv_idx == 0 and self.Is_Row_In_HBF_Iterations(row):
                        if not np.all(th_part == HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL):
                            output_msg = (
                                f"In HD_HBF_OPT mode, Group {g_idx} Row {r} DV {dv_idx} invalid TH values: "
                                f"expected all {HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL} for iteration {row.iter_start}~{row.iter_end} "
                                f"(HBF iterations are 1~{HBF_OPT_CONFIG.HBF_MAX_ITERATION}), got {th_part.tolist()}"
                            )
                            return False, output_msg

            CSW_values = [row.CSW for row in group]
            if CSW_values:
                if CSW_values[0] != -1:
                    output_msg = f"Group {g_idx} first CSW must be -1, got {CSW_values[0]}"
                    return False, output_msg
                minus_one_count = sum(1 for value in CSW_values if value == -1)
                if minus_one_count != 1:
                    output_msg = f"Group {g_idx} must have exactly one CSW == -1, found {minus_one_count}"
                    return False, output_msg

                prev_CSW = CSW_values[0]
                for idx in range(1, len(CSW_values)):
                    current_CSW = CSW_values[idx]

                    # 1. 범위 체크: MIN_CSW <= CSW <= MAX_CSW
                    if current_CSW < MIN_CSW or current_CSW > MAX_CSW:
                        output_msg = (
                            f"Group {g_idx} Row {idx} CSW {current_CSW} out of range [{MIN_CSW}, {MAX_CSW}]"
                        )
                        return False, output_msg

                    # 2. STEP_CSW의 배수 체크
                    if current_CSW % STEP_CSW != 0:
                        output_msg = (
                            f"Group {g_idx} Row {idx} CSW {current_CSW} must be a multiple of {STEP_CSW}"
                        )
                        return False, output_msg

                    # 3. Non-increasing 체크 (decreasing order 유지)
                    if prev_CSW != -1 and prev_CSW <= current_CSW:
                        output_msg = (
                            f"Group {g_idx} CSW values must be decreasing: {prev_CSW} <= {current_CSW}"
                        )
                        return False, output_msg

                    prev_CSW = current_CSW

            if not all(s == starts[0] for s in starts):
                output_msg = f"Group {g_idx} iteration_start mismatch: {starts}"
                return False, output_msg
            if not all(e == ends[0] for e in ends):
                output_msg = f"Group {g_idx} iteration_end mismatch: {ends}"
                return False, output_msg
            if ends[0] < starts[0]:
                output_msg = f"Group {g_idx} iteration_end < iteration_start"
                return False, output_msg

        expected_rows = int(np.sum(h.num_row_each_group))
        if total_row_count != expected_rows:
            output_msg = f"Total row count mismatch. Expected {expected_rows}, got {total_row_count}"
            return False, output_msg

        # 빈 매트릭스 검사 (groups가 비어있는 경우)
        if not self.groups or not self.groups[-1]:
            output_msg = "Matrix has no groups or last group is empty"
            return False, output_msg

        # SW 분기 배치: iteration 이어짐(G2), 분기 순서, 구간 덮기(G10)
        layout_error = self.Build_SW_Branch_Layout()
        if layout_error is not None:
            return False, layout_error

        # 헤더 type_each_group과 row 꼬리의 대조 (H8). 10 미만은 보통 그룹이라 꼬리가 -1이어야 하고,
        # 10 이상은 {분기 수}{분기 index} 표시라 일의 자리가 꼬리와, 십의 자리가 구간의 분기 수와 같아야 한다
        for g_idx in range(len(self.groups)):
            type_value = int(h.type_each_group[g_idx])
            branch = self.group_branch_idx[g_idx]
            if type_value < 10:
                if branch != SW_BRANCH_NONE:
                    output_msg = f"Group {g_idx} header type {type_value} is a plain group but rows carry SW branch index {branch}; use header 10 for a single-branch bundle"
                    return False, output_msg
                continue
            span = self.span_of_group[g_idx]
            if branch != type_value % 10:
                output_msg = f"Group {g_idx} header type {type_value} says branch {type_value % 10} but rows carry {branch}"
                return False, output_msg
            if span is None or span[2] != type_value // 10:
                output_msg = f"Group {g_idx} header type {type_value} says {type_value // 10} branches but the span has {span[2] if span else 0}"
                return False, output_msg

        self.max_iteration = max(group[-1].iter_end for group in self.groups)

        return True, ""

    def Read_Input_LLR_Matrix(self, input_dir: Optional[str] = None):
        self.LLR_matrix_file_name = PATH_CONFIG.LLR_MATRIX_FILE_NAME_TEMPLATE.format(matrix_idx=self.matrix_idx)

        base_dir = input_dir if input_dir is not None else PATH_CONFIG.INPUT_LLR_MATRIX_DIR_PATH
        self.input_LLR_matrix_file_path = os.path.join(base_dir, self.LLR_matrix_file_name)
        if not os.path.exists(self.input_LLR_matrix_file_path):
            raise FileNotFoundError(f"[Read_Input_LLR_Matrix] File not found: {self.input_LLR_matrix_file_path}")

        with open(self.input_LLR_matrix_file_path, "r", encoding="utf-8") as f:
            # 빈 줄과 공백을 제거해야 헤더 오프셋 계산 오류 없앰
            lines = [line.strip() for line in f if line.strip()]

        parsed = [
            np.array(list(map(int, line.split())), dtype=np.int32) for line in lines
        ]

        def get_line(idx: int, field_name: str) -> np.ndarray:
            """파싱된 라인을 안전하게 가져오기. 범위 초과 시 ValueError 발생."""
            if idx >= len(parsed):
                raise ValueError(
                    f"[Read_Input_LLR_Matrix] Unexpected end of file while reading '{field_name}'. "
                    f"Expected line {idx + 1}, but file has only {len(parsed)} lines."
                )
            return parsed[idx]

        idx_line = 0
        num_parameter_each_set = int(get_line(idx_line, "num_parameter_each_set")[0]); idx_line += 1
        num_dv = int(get_line(idx_line, "num_dv")[0]); idx_line += 1
        dv_from = get_line(idx_line, "dv_from"); idx_line += 1
        dv_to = get_line(idx_line, "dv_to"); idx_line += 1
        num_group = int(get_line(idx_line, "num_group")[0]); idx_line += 1
        num_row_each_group = get_line(idx_line, "num_row_each_group"); idx_line += 1
        type_each_group = get_line(idx_line, "type_each_group"); idx_line += 1

        num_restart = int(get_line(idx_line, "num_restart")[0]); idx_line += 1
        if num_restart > 0:
            restart_iter = get_line(idx_line, "restart_iter"); idx_line += 1
        else:
            restart_iter = np.array([], dtype=np.int32)

        max_value = get_line(idx_line, "max_value"); idx_line += 1
        min_value = get_line(idx_line, "min_value"); idx_line += 1

        self.header = LLR_Header(
            num_parameter_each_set,
            num_dv,
            dv_from,
            dv_to,
            num_group,
            num_row_each_group,
            type_each_group,
            num_restart,
            restart_iter,
            max_value,
            min_value,
        )

        total_rows = int(np.sum(num_row_each_group))
        
        matrix_rows = parsed[idx_line: idx_line + total_rows]
        if len(matrix_rows) != total_rows:
            raise ValueError(
                f"[Read_Input_LLR_Matrix] Expected {total_rows} rows, got {len(matrix_rows)}"
            )

        row_offset = 0
        for g in range(num_group):
            group_size = int(num_row_each_group[g])
            group_rows = matrix_rows[row_offset: row_offset + group_size]
            row_offset += group_size

            group_data = []
            for row in group_rows:
                matrix = row[:-4]
                CSW = int(row[-4])
                iter_start = int(row[-3])
                iter_end = int(row[-2])
                floor_flag = int(row[-1])

                is_restart = iter_start in list(self.header.restart_iter)
                if is_restart and (g + 1) not in self.restart_groups:
                    self.restart_groups.append(g + 1)

                group_data.append(
                    LLR_Row(matrix, CSW, iter_start, iter_end, floor_flag, is_restart)
                )
            self.groups.append(group_data)

        self.ch_length = 2 ** (self.init_n - 1)
        self.th_length = num_parameter_each_set - self.ch_length

        # HBF 구간의 row에서 값이 고정되는 column 범위 (dv_idx 0의 TH)
        if self.is_HBF_OPT:
            self.HBF_immutable_col_range = (self.ch_length, num_parameter_each_set)

        else:
            self.HBF_immutable_col_range = None

        self.Build_SW_Branch_Layout()

    def Save_Matrix(self, save_dir: str) -> None:
        lines = self.Build_LLR_Matrix_Output_Lines()
        save_path = os.path.join(save_dir, self.LLR_matrix_file_name)
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(save_dir, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as file:
                for line in lines:
                    file.write(f"{line}\n")
        except OSError as e:
            raise OSError(f"Save_Matrix failed: {save_path} - {e}") from e

    def Correct_LLR_Matrix(self) -> list:
        """
        각 row의 CH/TH 구간을 비증가(내림차순) 순서로 정렬해 보정한다.
        각 CSW를 비증가(내림차순) 순서로 정렬해 보정한다.

        Ch/Th 정렬: 모든 그룹에 적용 (restart row 제외)
        CSW 정렬: 모든 그룹에 적용 (각 그룹의 첫 row인 CSW=-1 제외)

        Restart row 제외 이유:
        - Restart row는 iteration이 1로 고정된 특수 row
        - 값 변이 대상이 아니므로 정렬/truncation 불필요
        """
        h = self.header
        correct_msg = []

        # 모든 그룹에 대해 Ch/Th 정렬 적용 (restart row 제외)
        for g_idx, group in enumerate(self.groups):
            for r_idx, row in enumerate(group):
                # Restart row는 정렬/truncation 제외
                if row.is_group_restart:
                    continue
                row.ch_th_values, tmp_msg = self.Correct_Ch_Th_In_Row(
                    row.ch_th_values, g_idx, r_idx, is_row_in_HBF_iterations=self.Is_Row_In_HBF_Iterations(row)
                )
                correct_msg.extend(tmp_msg)

        # 모든 그룹에 대해 CSW 정렬 적용 (각 그룹의 첫 row인 CSW=-1 제외)
        for g_idx, group in enumerate(self.groups):
            if len(group) <= 1:
                continue  # 그룹에 row가 1개 이하면 정렬 불필요

            CSW_else_rows = [row for row in group if row.CSW == -1]
            if len(CSW_else_rows) == 0:
                raise ValueError(f"[Sort_Matrix] Group {g_idx} has no row with CSW == -1.")
            if len(CSW_else_rows) > 1:
                raise ValueError(f"[Sort_Matrix] Group {g_idx} has multiple rows with CSW == -1.")

            CSW_else = CSW_else_rows[0]
            remaining_rows = [row for row in group if row is not CSW_else]
            # 범위 안의 STEP_CSW 배수로 맞춘 뒤 내림차순으로 세우고, 같아진 값은 한 단계씩 내려 서로 다르게 만든다
            for row in remaining_rows:
                corrected_CSW = int(round(row.CSW / STEP_CSW)) * STEP_CSW
                corrected_CSW = max(MIN_CSW, min(corrected_CSW, MAX_CSW))
                if corrected_CSW != row.CSW:
                    correct_msg.append(f"\t- group {g_idx} CSW {row.CSW} -> {corrected_CSW} (Truncated)")
                    row.CSW = corrected_CSW
            remaining_rows.sort(key=lambda r: r.CSW, reverse=True)
            for prev_row, row in zip(remaining_rows, remaining_rows[1:]):
                if row.CSW >= prev_row.CSW:
                    lowered_CSW = prev_row.CSW - STEP_CSW
                    if lowered_CSW < MIN_CSW:
                        raise ValueError(f"[Correct_LLR_Matrix] Group {g_idx} has more CSW rows than the range [{MIN_CSW}, {MAX_CSW}] can keep distinct.")
                    correct_msg.append(f"\t- group {g_idx} CSW {row.CSW} -> {lowered_CSW} (Deduplicated)")
                    row.CSW = lowered_CSW
            group[:] = [CSW_else] + remaining_rows

        return correct_msg

    def Correct_Ch_Th_In_Row(self, values: np.ndarray, group_idx: int = -1, row_idx: int = -1, is_row_in_HBF_iterations: bool = False) -> tuple[np.ndarray, list]:
        """
        DV별로 CH/TH 구간을 보정한 새 행을 반환한다.

        처리 순서:
        1. Max/Min Truncation: Header의 max/min value에 맞춰 값을 클램핑
        2. Ch/Th 정렬: 내림차순 정렬 (truncation 후 정렬해야 정렬 순서 유지)

        is_row_in_HBF_iterations가 True면 dv_idx 0의 TH를 HBF_OPT_TH_CONSTANT_VAL로 고정한다
        (판단 기준은 Is_Row_In_HBF_Iterations). iteration이 정해지기 전의 row는 False로 두고,
        매트릭스에 들어간 뒤 Correct_LLR_Matrix가 row의 iteration을 보고 고정한다.
        """
        correct_msg = []
        expected_len = self.header.num_parameter_each_set * self.header.num_dv
        if len(values) != expected_len:
            raise ValueError(f"[Gen_Row] Row length mismatch. Expected {expected_len}, got {len(values)}")

        sorted_values = np.array(values, dtype=np.int32, copy=True)
        for dv_idx in range(self.header.num_dv):
            start_idx = dv_idx * self.header.num_parameter_each_set
            end_idx = start_idx + self.header.num_parameter_each_set
            segment = sorted_values[start_idx:end_idx]

            # 1. Max/Min Truncation 먼저 수행 (정렬 전에 범위 제한)
            temp_segment = segment.copy()
            np.minimum(segment, self.header.max_value, out=segment)
            np.maximum(segment, self.header.min_value, out=segment)

            # 변경 사항이 있는지 확인 (로그용)
            if not np.array_equal(temp_segment, segment):
                diff_indices = np.where(temp_segment != segment)[0]
                for local_idx in diff_indices:
                    old_val = temp_segment[local_idx]
                    new_val = segment[local_idx]
                    correct_msg.append(
                        f"\t- group {group_idx} row {row_idx} (DV {dv_idx}, idx {local_idx}): {old_val} -> {new_val} (Truncated)"
                    )

            # 2. Ch/Th 정렬 (truncation 후 정렬해야 정렬 순서가 유지됨)
            segment[:self.ch_length] = np.sort(segment[:self.ch_length])[::-1]
            if is_row_in_HBF_iterations and dv_idx == 0:
                # HBF 구간의 row는 dv_idx 0의 TH만 상수로 고정한다 (Is_LLR_Valid의 HBF1 규칙과 같은 범위)
                segment[self.ch_length:] = HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL
            else:
                segment[self.ch_length:] = np.sort(segment[self.ch_length:])[::-1]

        return sorted_values, correct_msg