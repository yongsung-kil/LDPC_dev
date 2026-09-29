import os, random, datetime, shutil, sys, subprocess, time, traceback, itertools, inspect, pickle, base64, threading
import numpy as np
from enum import Enum
from typing import Optional, Union, Any, NoReturn
from pprint import pformat
from dataclasses import is_dataclass, fields, dataclass
from pathlib import Path
from DAO_LLR_MATRIX import LLR_MATRIX, LLR_Row
from DAO_Config import *
from DAO_Constants import *

def _summarize_ndarray(array: np.ndarray) -> str:
    """ndarray 요약 문자열을 생성한다.
    배열의 크기와 일부 값을 간략히 표현하여 로그 출력 시 가독성을 높이기 위한 도우미 함수다.
    Args:
        array (np.ndarray): 요약할 대상 배열.
    Returns:
        str: 배열의 형태와 미리보기 값을 포함한 요약 문자열.
    """
    array = np.asarray(array)
    if array.size == 0:
        return f"ndarray(shape={array.shape}, empty)"
    if array.ndim == 1 and array.size <= MAX_COLLECTION_PREVIEW:
        preview = np.array2string(array, separator=", ", max_line_width=1_000_000)
        return f"ndarray({preview})"

    # 큰 배열은 일부만 표시
    flat = array.ravel()
    if flat.size > MAX_COLLECTION_PREVIEW:
        preview_flat = flat[:MAX_COLLECTION_PREVIEW]
        preview_str = np.array2string(preview_flat, separator=", ", max_line_width=1_000_000)
        return f"ndarray(shape={array.shape}, size={flat.size}, preview={preview_str}...)"
    else:
        preview_str = np.array2string(flat, separator=", ", max_line_width=1_000_000)
        return f"ndarray(shape={array.shape}, preview={preview_str})"

def _format_elapsed(seconds: float) -> str:
    """초 단위 시간을 '1d 2h 3m 4s' 형식으로 변환한다."""
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts)

def _summarize_value(value: Any, depth: int = 0) -> Any:
    """임의의 값을 간략히 요약한다.
    값의 유형에 따라 재귀적으로 축약된 표현을 만들어 로그와 디버그 출력에 활용한다.
    Args:
        value (Any): 요약할 대상 객체.
        depth (int): 재귀 요약 깊이, 최대 요약 수준 제어에 사용한다.

    Returns:
        Any: 원본 값 또는 요약 문자열.
    """
    if depth >= MAX_SUMMARY_DEPTH:
        return f"<{type(value).__name__}>"

    # Enum 타입은 이름과 값을 모두 표시 (IntEnum 포함)
    if isinstance(value, Enum):
        return f"<{type(value).__name__}.{value.name}: {value.value}>"

    if isinstance(value, (str, int, float, bool, type(None))):
        return value

    if isinstance(value, np.ndarray):
        return _summarize_ndarray(value)

    if isinstance(value, (list, tuple, set)):
        sequence = list(value)
        preview = sequence[:MAX_COLLECTION_PREVIEW]
        summarized = [_summarize_value(item, depth + 1) for item in preview]
        suffix = "..." if len(sequence) > MAX_COLLECTION_PREVIEW else ""
        container_name = type(value).__name__
        return f"{container_name}({summarized}{suffix})"

    if isinstance(value, dict):
        items = list(value.items())[:MAX_COLLECTION_PREVIEW]
        summarized = {
            str(key): _summarize_value(val, depth + 1) for key, val in items
        }
        suffix = "..." if len(value) > MAX_COLLECTION_PREVIEW else ""
        return f"dict({summarized}{suffix})"

    if isinstance(value, LLR_MATRIX):
        header = value.header
        header_summary = {
            "num_parameter_each_set": header.num_parameter_each_set,
            "num_dv": header.num_dv,
            "num_group": header.num_group,
            "dv_from": _summarize_value(header.dv_from, depth + 1),
            "dv_to": _summarize_value(header.dv_to, depth + 1),
            "num_row_each_group": _summarize_value(header.num_row_each_group, depth + 1),
            "type_each_group": _summarize_value(header.type_each_group, depth + 1),
            "num_restart": header.num_restart,
            "restart_iter": _summarize_value(header.restart_iter, depth + 1),
            "max_value": _summarize_value(header.max_value, depth + 1),
            "min_value": _summarize_value(header.min_value, depth + 1),
        }

        groups_preview = []
        for group_idx, group in enumerate(value.groups[:MAX_COLLECTION_PREVIEW]):
            row_preview = []
            for row in group[:MAX_COLLECTION_PREVIEW]:
                row_summary = {
                    "ch_th_values": _summarize_value(row.ch_th_values, depth + 1),
                    "CSW": row.CSW,
                    "iter_start": row.iter_start,
                    "iter_end": row.iter_end,
                    "floor_flag": row.floor_flag,
                    "is_group_restart": row.is_group_restart,
                }
                row_preview.append(row_summary)
            group_info = {
                "group_index": group_idx,
                "row_count": len(group),
                "rows_preview": row_preview,
            }
            if len(group) > MAX_COLLECTION_PREVIEW:
                group_info["more_rows"] = len(group) - MAX_COLLECTION_PREVIEW
            groups_preview.append(group_info)

        groups_summary: dict[str, Any] = {
            "total_groups": len(value.groups),
            "preview": groups_preview,
        }
        if len(value.groups) > MAX_COLLECTION_PREVIEW:
            groups_summary["more_groups"] = len(value.groups) - MAX_COLLECTION_PREVIEW

        return {
            "class": "LLR_MATRIX",
            "matrix_idx": value.matrix_idx,
            "groups": len(value.groups),
            "th_length": getattr(value, "th_length", None),
            "ch_length": getattr(value, "ch_length", None),
            "header": header_summary,
            "groups_summary": groups_summary,
        }

    if is_dataclass(value):
        summary = {}
        for field in fields(value):
            try:
                field_value = getattr(value, field.name)
            except Exception as error:
                field_value = f"<access failed: {error!r}>"
            summary[field.name] = _summarize_value(field_value, depth + 1)
        return {f"dataclass:{type(value).__name__}": summary}

    if hasattr(value, "__dict__"):
        attributes = {}
        for idx, (key, val) in enumerate(value.__dict__.items()):
            if idx >= MAX_COLLECTION_PREVIEW:
                attributes["..."] = f"<{len(value.__dict__) - MAX_COLLECTION_PREVIEW} more attributes>"
                break
            attributes[key] = _summarize_value(val, depth + 1)
        return {f"object:{type(value).__name__}": attributes}

    if callable(value):
        # callable은 간단히 이름만 표시
        name = getattr(value, '__name__', type(value).__name__)
        return f"<callable: {name}>"

    return repr(value)

def _write_error_log(
    process_idx: int,
    exc: BaseException,
    state_text: Optional[str] = None,
    error_dir: Optional[str] = None,
) -> None:
    """
    처리되지 않은 예외를 Error_Log/error_logs_{process_idx}.txt에 기록한다.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if error_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        error_dir = os.path.join(base_dir, ERROR_LOG_DIR_NAME)
    os.makedirs(error_dir, exist_ok=True)
    log_path = os.path.join(error_dir, ERROR_LOG_FILE_TEMPLATE.format(process_idx=process_idx))

    # 지역 변수는 크기 제한 없이 찍히므로 담지 않는다 (uncor 목록 하나가 수 MB). 상태는 state_text 요약이 담는다
    traceback_lines = "".join(
        traceback.TracebackException.from_exception(exc, capture_locals=False).format()
    )

    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write("=" * 80 + "\n")
            log_file.write(f"[{timestamp}] Unhandled exception on process {process_idx}\n")
            log_file.write("-" * 80 + "\n")
            log_file.write(traceback_lines)
            if state_text:
                log_file.write("\nCaptured LLR_OPT state snapshot:\n")
                log_file.write(state_text)
                if not state_text.endswith("\n"):
                    log_file.write("\n")
            log_file.write("=" * 80 + "\n\n")
    except OSError as e:
        print(f"[Rank {process_idx}] _write_error_log failed: {e}", flush=True)

@dataclass
class ReorderState:
    """REORDER_GROUP 모드 상태 관리 (반복문 기반)

    MPI 동기화를 간소화하기 위해 reorder 관련 변수를 하나의 클래스로 묶음.
    comm.bcast() 한 번으로 모든 상태를 전송 가능.

    **생명주기:**
    - 초기화: Initialize_Stage에서 Init_Reorder_Group_Mode() 호출하여 설정
    - 유지: Stage 전체 동안 유지 (Trial 간 초기화 없음)
    - 종료: 모든 Round 완료 후 is_active=False

    **Round 기반 구조:**
    - 각 Round에서 current_donor_pool의 모든 후보를 테스트
    - Best를 선택하여 fixed_order에 추가, current_donor_pool에서 제거
    - 모든 Round 완료 후 Final Verification

    **변수 설명:**
    - is_active: REORDER_GROUP 모드 활성화 여부
    - current_round: 현재 Round (0-based)
    - total_rounds: 전체 Round 수 (사용되지않음)

    - fixed_order: 확정된 그룹 인덱스 순서 [g3, g5, ...]
    - final_restart_flags: 각 그룹의 restart 여부 [True, False, ...]

    - base_donor_pool: Stage 시작 시 초기 donor (불변, restart 제외)
    - current_donor_pool: 현재 Round의 남은 donor (Round마다 하나씩 제거)
    - current_donor_idx: current_donor_pool 내 현재 테스트 중인 인덱스

    - current_with_restart: 현재 trial의 restart 여부 (SD: 홀수면 True)

    - round_best_donor_idx: 이번 Round의 best (current_donor_pool 내 인덱스)
    - round_best_with_restart: Best의 restart 여부
    - round_best_FER: Best의 FER (사용되지않음)
    - round_best_avg_iter: Best의 avg_iter (사용되지않음)
    - round_best_matrix: Best의 matrix 복사본

    - round_trial_count: 현재 Round 내 trial 수
    - total_expected_trials: 전체 예상 trial 수
    """
    # === 모드 활성화 ===
    is_active: bool = False

    # === Round 관리 ===
    current_round: int = 0

    # === 확정된 순서 ===
    fixed_order: list[int] = None
    final_restart_flags: list[bool] = None

    # === Donor Pool ===
    base_donor_pool: list[int] = None
    current_donor_pool: list[int] = None
    current_donor_idx: int = 0

    # === 현재 Trial 상태 ===
    current_with_restart: bool = False

    # === 현재 Round의 Best ===
    round_best_donor_idx: int = -1
    round_best_with_restart: bool = False
    round_best_matrix: Optional['LLR_MATRIX'] = None

    # === Trial 카운팅 ===
    round_trial_count: int = 0
    total_expected_trials: int = 0

    def __post_init__(self):
        """default mutable arguments 처리"""
        if self.fixed_order is None:
            self.fixed_order = []
        if self.final_restart_flags is None:
            self.final_restart_flags = []
        if self.base_donor_pool is None:
            self.base_donor_pool = []
        if self.current_donor_pool is None:
            self.current_donor_pool = []

@dataclass
class AdjustIterState:
    """ADJUST_ITERATION 모드의 상태를 관리하는 클래스

    MPI 동기화를 간소화하기 위해 iteration 조정 관련 변수를 하나의 클래스로 묶음.
    comm.bcast() 한 번으로 모든 상태를 전송 가능.

    **생명주기:**
    - 초기화: Initialize_Stage에서 Init_Adjust_Iteration_Mode() 호출하여 설정
    - 유지: Stage 전체 동안 유지 (Trial 간 초기화 없음)
    - 종료: 모든 target group 테스트 완료 후 is_active=False

    **동작 원리:**
    - Target groups(restart 제외)를 순차적으로 focus로 선택
    - 각 focus에 대해: focus와 restart를 제외한 모든 그룹(donor)이 동시에 iteration을 줄임
    - 줄인 iteration의 합을 focus에 추가 (총 iteration은 동일하게 유지)
    - 표준 temp_optimal 흐름으로 최적 추적 (is_update_at_last_trial=True)

    **변수 설명:**
    - is_active: ADJUST_ITERATION 모드 활성화 여부
    - target_groups: 최적화 대상 그룹 인덱스 리스트 (restart 제외)
    - current_target_idx: 다음 trial의 target group 인덱스 (target_groups 내 position)
    - current_testing_target_idx: 현재 테스트 중인 target group 인덱스
    - iter_transfer_ratio: Iteration 전달 비율 (예: 0.1 = donor들의 각각 10%를 focus에 전달)
    - total_expected_trials: 예상 총 trial 수 (= len(target_groups))
    - completed_trials: 완료된 trial 수 (전체 누적)
    """
    is_active: bool = False
    target_groups: Optional[list[int]] = None
    current_target_idx: int = 0
    current_testing_target_idx: int = -1  # 현재 테스트 중인 target
    iter_transfer_ratio: float = 0.1

    total_expected_trials: int = 0
    completed_trials: int = 0

    def __post_init__(self):
        """default mutable arguments 처리"""
        if self.target_groups is None:
            self.target_groups = []

@dataclass
class DeleteRowState:
    """DELETE_ROW 모드 상태 관리

    MPI 동기화를 간소화하기 위해 delete row 관련 변수를 하나의 클래스로 묶음.
    comm.bcast() 한 번으로 모든 상태를 전송 가능.

    **생명주기:**
    - 초기화: Initialize_Stage에서 Init_Delete_Row_Mode() 호출하여 설정
    - 유지: Stage 전체 동안 유지 (Trial 간 초기화 없음)
    - 종료: Round에서 개선 없거나, 삭제 가능한 row 없으면 is_active=False

    **Multi-round greedy deletion:**
    - 각 Round: 삭제 가능한 모든 row를 하나씩 삭제 후 테스트 → best 선택
    - best가 baseline보다 개선되면 삭제 확정, 다음 Round 진행
    - 개선 없으면 종료

    **변수 설명:**
    - is_active: DELETE_ROW 모드 활성화 여부
    - current_round: 현재 Round (0-based)
    - deletable_rows: 현재 Round의 삭제 후보 [(group_idx, row_idx), ...]
    - current_candidate_idx: deletable_rows 내 현재 테스트 중인 인덱스
    - round_best_candidate_idx: 이번 Round의 best (deletable_rows 내 인덱스)
    - round_best_matrix: Best의 matrix 복사본
    - round_baseline_matrix: 현재 Round의 baseline (삭제 전 상태)
    - round_trial_count: 현재 Round 내 trial 수
    - total_expected_trials: 전체 예상 trial 수 (N*(N+1)/2 상한)
    """
    # === 모드 활성화 ===
    is_active: bool = False

    # === Round 관리 ===
    current_round: int = 0

    # === 삭제 후보 ===
    deletable_rows: Optional[list] = None      # list[tuple[int, int]]
    current_candidate_idx: int = 0

    # === 현재 Round의 Best ===
    round_best_candidate_idx: int = -1
    round_best_matrix: Optional['LLR_MATRIX'] = None

    # === Baseline ===
    round_baseline_matrix: Optional['LLR_MATRIX'] = None

    # === Trial 카운팅 ===
    round_trial_count: int = 0
    total_expected_trials: int = 0

    def __post_init__(self):
        """default mutable arguments 처리"""
        if self.deletable_rows is None:
            self.deletable_rows = []

@dataclass
class InsertRestartGroupState:
    """INSERT_RESTART_GROUP 모드 상태 관리

    Multi-round greedy insertion:
    - 각 Round: 유효한 모든 위치에 restart group 삽입 후 테스트 → best 선택
    - best가 baseline보다 개선되면 삽입 확정, 다음 Round 진행
    - 개선 없으면 종료
    """
    is_active: bool = False
    current_round: int = 0
    insertable_positions: Optional[list] = None   # list[int] (group index)
    current_candidate_idx: int = 0
    round_best_candidate_idx: int = -1
    round_best_matrix: Optional['LLR_MATRIX'] = None
    round_baseline_matrix: Optional['LLR_MATRIX'] = None
    round_trial_count: int = 0
    total_expected_trials: int = 0

    def __post_init__(self):
        if self.insertable_positions is None:
            self.insertable_positions = []

def Update_Exit_After_Run_Configs():
    """RUN_DAO_MODE에 따라 UNCOR_CONFIG를 자동 설정한다."""
    if DAO_CONFIG.RUN_DAO_MODE != RunDAOMode.RUN_OPTIMIZATION:
        # Note: UNCOR_MATRIX_IDX(Full/non-2-stage 공용)는 Set_Configs_Manually에서 설정됨

        if DAO_CONFIG.RUN_DAO_MODE in [RunDAOMode.TEST_FER, RunDAOMode.SAVE_UNCOR]:
            UNCOR_CONFIG.LOAD_UNCOR_MODE = DAOLoadUncorMode.LOAD_NONE
        elif DAO_CONFIG.RUN_DAO_MODE in [RunDAOMode.REDECODE, RunDAOMode.GEN_SINGLE_ROW]:
            UNCOR_CONFIG.LOAD_UNCOR_MODE = DAOLoadUncorMode.LOAD_SEED
    else:
        if UNCOR_CONFIG.ENABLE_LOAD_VECTOR:
            UNCOR_CONFIG.LOAD_UNCOR_MODE = DAOLoadUncorMode.LOAD_VECTOR          # 최적화 모드에서는 수정 필요
        else:
            UNCOR_CONFIG.LOAD_UNCOR_MODE = DAOLoadUncorMode.LOAD_SEED

def Update_RefC_Configs():
    """RefCConfig의 종속 변수들을 재계산한다."""
    if REFC_CONFIG.ch_type == 1:
        REFC_CONFIG.NUM_TARGET_CHANNELS = len(REFC_CONFIG.RBERs)
        REFC_CONFIG.num_fixed_errs = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_SCRs = [0.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_SERs = [0.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_erasure_ratios = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
    elif REFC_CONFIG.ch_type == 2:
        REFC_CONFIG.NUM_TARGET_CHANNELS = len(REFC_CONFIG.num_fixed_errs)
        REFC_CONFIG.RBERs = [0.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_SCRs = [0.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_SERs = [0.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_erasure_ratios = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
    elif REFC_CONFIG.ch_type == 3:
        REFC_CONFIG.NUM_TARGET_CHANNELS = len(REFC_CONFIG.num_fixed_errs)
        REFC_CONFIG.RBERs = [0.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        REFC_CONFIG.fixed_erasure_ratios = [0] * REFC_CONFIG.NUM_TARGET_CHANNELS
        # SCR과 SER은 채널별 값이다. 값이 하나뿐이면 모든 채널에 같은 값을 쓰고, 개수가 다르면 시작 시점에 바로 알린다
        for field_name in ("fixed_SCRs", "fixed_SERs"):
            values = list(getattr(REFC_CONFIG, field_name))
            if len(values) == 1:
                values = values * REFC_CONFIG.NUM_TARGET_CHANNELS
            if len(values) != REFC_CONFIG.NUM_TARGET_CHANNELS:
                raise ValueError(
                    f"Update_RefC_Configs: {field_name} has {len(values)} values; ch_type 3 needs 1 or NUM_TARGET_CHANNELS ({REFC_CONFIG.NUM_TARGET_CHANNELS})"
                )
            setattr(REFC_CONFIG, field_name, values)
    else:
        raise ValueError(f"Update_RefC_Configs: Unsupported ch_type={REFC_CONFIG.ch_type}. Valid: 1, 2, 3")

    if REFC_CONFIG.init_n != 1:
        DAO_CONFIG.IS_HBF_OPT = False

    if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:
        if UNCOR_CONFIG.IS_TLC:
            UNCOR_CONFIG.LEN_NO_PS = 36864
        else:
            UNCOR_CONFIG.LEN_NO_PS = 37632
        UNCOR_CONFIG.NUM_LINES_PER_UNCOR = int(REFC_CONFIG.init_n * (UNCOR_CONFIG.LEN_NO_PS / 64 / 4))
    SPEED_TEST_REFC_CONFIG.str_matrix_name = REFC_CONFIG.str_matrix_name

def Update_Path_Configs():
    """PATHConfig의 종속 변수들을 재계산한다."""
    PATH_CONFIG.ECC_NAME = ECC_NAME_TEMPLATE.format(ecc_ver=REFC_CONFIG.ECC_VER)
    PATH_CONFIG.ECC_DIR_NAME = PATH_CONFIG.ECC_NAME
    PATH_CONFIG.ECC_EXE_NAME = f"{PATH_CONFIG.ECC_NAME}.exe" if CURRENT_OS is OperatingSystem.WINDOWS else PATH_CONFIG.ECC_NAME

    PATH_CONFIG.BATCH_FILE_TEMPLATE = f"run_ecc_{REFC_CONFIG.matrix_sel}_{REFC_CONFIG.init_n}_{{process_idx}}{PATH_CONFIG.BATCH_EXT}"

    PATH_CONFIG.INPUT_ECC_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_REF_C_DIR_PATH, PATH_CONFIG.ECC_DIR_NAME)
    PATH_CONFIG.INPUT_LLR_MATRIX_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, INITIAL_LLR_MATRIX_DIR_NAME, MODE_MAP[REFC_CONFIG.init_n])
    PATH_CONFIG.INPUT_SINGLE_ROW_LLR_MATRIX_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, SINGLE_ROW_LLR_MATRIX_DIR_NAME, MODE_MAP[REFC_CONFIG.init_n])
    PATH_CONFIG.INPUT_UNCOR_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, INPUT_UNCOR_DIR_NAME)
    PATH_CONFIG.INPUT_ECC_EXE_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, REF_C_EXE_DIR_NAME)
    PATH_CONFIG.INPUT_ECC_EXE_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_EXE_DIR_PATH, PATH_CONFIG.ECC_EXE_NAME)

    PATH_CONFIG.INPUT_ECC_SRC_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, REF_C_SRC_DIR_NAME)
    PATH_CONFIG.INPUT_H_MATRIX_DIR_PATH = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, H_MATRIX_DIR_NAME)
    PATH_CONFIG.WORK_SPACE_DIR = os.path.join(PATH_CONFIG.BASE_DIR_PATH, WORK_SPACE_DIR_NAME, MODE_MAP[REFC_CONFIG.init_n])

def Update_Insert_Group_Configs():
    """INSERT_RANDOM/MUTATED_GROUP_CONFIG의 종속 변수들을 재계산한다."""
    enable = (REFC_CONFIG.init_n != 1)
    INSERT_RANDOM_GROUP_CONFIG.ENABLE_INSERT_RESTART = enable
    INSERT_MUTATED_GROUP_CONFIG.ENABLE_INSERT_RESTART = enable

def Update_Configs():
    # LOAD_UNCOR_MODE를 먼저 정해야 Update_RefC_Configs가 벡터 길이(LEN_NO_PS, NUM_LINES_PER_UNCOR)를 맞게 계산한다
    Update_Exit_After_Run_Configs()
    Update_RefC_Configs()
    Update_Insert_Group_Configs()
    Update_Path_Configs()
    
class LLR_OPT:
    def __init__(self):
        self.input_args = sys.argv[1:]
        self.output_dir: str = ""
        self.current_LLR_matrix_idx: int = 0
        self._current_initial_matrix_idx: int = -1  # multi-matrix 루프에서 현재 처리 중인 매트릭스 인덱스
        self.optimal_output_dir: str = ""
        self.simulation_start: Optional[datetime.datetime] = None
        self.session_timestamp: str = ""
        self.work_space_dir: str = ""
        self.session_dir: str = ""
        self.trial_output_dir: str = ""
        self.session_error_dir: str = ""
        self.session_logs_dir: str = ""
        self.session_debug_snapshot_dir: str = ""
        self.session_uncor_dir: str = ""
        self.log_file_path: str = ""
        self.update_log_file_path: str = ""
        self.log_line_count: int = 0
        self.log_create_time: datetime.datetime = datetime.datetime.now()
        self.log_start_matrix_idx: int = 0
        self.barrier_count: int = 0
        self._in_mpi_abort: bool = False

        self.comm = comm
        self.rank = rank
        self.num_process = num_process
        self.is_root = self.rank == 0
        self.base_seed: int = 0
        self.local_session_dir: str = ""
        self.has_uncor: list[bool] = [False] * REFC_CONFIG.NUM_TARGET_CHANNELS  # 현재 프로세스가 uncor를 받았는지 여부

        # per-matrix 상태 초기화 (_Reset_For_Next_Matrix와 공용)
        self._init_per_matrix_state()

        self.is_replace_DV_in_Ch_Th_reuse_mode = False
        self.is_gen_row_reuse_mode = False

        self.current_gen_trial_LLR_mode_name: Optional[str] = None
        self.insert_group_add_restart = False

        # Stage별 시간 제한 활성화 여부 (REORDER_GROUP 모드에서는 비활성화)
        self.is_current_stage_enable_max_stage_time_limit: bool = TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS < SIM_MAX_TIME_OUT

        # Uncor pool 상태 추적
        # pool_has_uncor[test_mode][ch_idx]: 현재 프로세스가 해당 모드/채널의 pool uncor를 보유하는지
        self.pool_has_uncor: dict[TestMode, list[bool]] = {
            TestMode.PARTIAL: [False] * REFC_CONFIG.NUM_TARGET_CHANNELS,
            TestMode.FULL: [False] * REFC_CONFIG.NUM_TARGET_CHANNELS,
        }

        self.debug_is_init = True
        self.debug_cnt = 0

        self.ecc_start_time: float = 0.0
        self.ecc_end_time: float = 0.0
        self.ecc_elapsed_time: float = 0.0

        # Core 속도 테스트 결과 (느린 코어 제외용)
        self.excluded_cores: list[int] = []  # 테스트에서 제외할 느린 코어 rank 목록
        self.core_elapsed_times: list[float] = []  # 코어별 speed test 소요시간 (allgather)

        self.is_current_core_excluded: bool = False  # 현재 코어가 제외 대상인지 여부
        self._last_speed_test_time: float = 0.0     # 마지막 speed test 완료 시각 (time.time())

        # ========== REORDER_GROUP 전용 상태 ==========
        # 12개 변수를 ReorderState 클래스로 통합하여 MPI bcast 최적화
        self.reorder_state: ReorderState = ReorderState()

        # ========== ADJUST_ITERATION 전용 상태 ==========
        self.adjust_iter_state: AdjustIterState = AdjustIterState()

        # ========== DELETE_ROW 전용 상태 ==========
        self.delete_row_state: DeleteRowState = DeleteRowState()

        # ========== INSERT_RESTART_GROUP 전용 상태 ==========
        self.insert_restart_group_state: InsertRestartGroupState = InsertRestartGroupState()

        # ========== 런타임 할당 변수 명시적 초기화 ==========
        self.current_stage_idx: int = 0
        self.current_seed_mode = SeedMode.DEFAULT
        self.enable_print_CSW_log: int = 0
        self.is_test_end: bool = False
        self.max_error: int = 0
        self.update_mode = None
        self.generate_LLR_success: bool = False
        self.batch_path: str = ""
        self.end_flag_dir: str = ""
        self.log_has_update: bool = False
        self.single_row_candidates_dir: str = ""

    def _init_per_matrix_state(self):
        """per-matrix 상태를 초기화한다. __init__과 _Reset_For_Next_Matrix에서 공용.

        리셋 대상: LLR matrix, test 결과 누적값, test mode, trial 상태, save tracking
        유지 대상: session 경로, MPI 설정, excluded_cores, pool_has_uncor, 로그 파일
        """
        # 1. LLR Matrix 상태
        self.initial_LLR_matrix: Optional[LLR_MATRIX] = None
        self.current_LLR_matrix: Optional[LLR_MATRIX] = None
        self.optimal_LLR_matrix: Optional[LLR_MATRIX] = None
        self.temp_optimal_LLR_matrix: Optional[LLR_MATRIX] = None
        self.previous_optimal_LLR_matrix: Optional[LLR_MATRIX] = None
        self.target_group_indices: list[int] = []

        # 2. Test 결과 누적값 (Gather_Ref_C_Results가 누적 합산하므로 반드시 초기화)
        num_ch = REFC_CONFIG.NUM_TARGET_CHANNELS
        self.total_num_tests: list[int] = [0] * num_ch
        self.total_num_errors: list[int] = [0] * num_ch
        self.total_num_iterations: list[int] = [0] * num_ch
        # 각 채널마다 독립적인 배열 생성 (얕은 복사 버그 방지)
        self.total_num_error_per_iters: list[np.ndarray] = [np.zeros(1) for _ in range(num_ch)]
        self.total_FER_per_iters: list[np.ndarray] = [np.zeros(1) for _ in range(num_ch)]
        self.total_num_raw_tests = [0] * num_ch
        self.total_num_raw_errors = [0] * num_ch
        self.total_num_seed_tests = [0] * num_ch
        self.total_num_seed_errors = [0] * num_ch
        self.total_raw_FERs = [0.0] * num_ch
        self.total_seed_FERs = [0.0] * num_ch
        self.total_num_uncors: list[int] = [0] * num_ch
        # Dynamic Partial: Partial uncor 수 별도 추적 (Full용 total_num_uncors와 분리)
        self.total_num_partial_uncors: list[int] = [0] * num_ch

        # 3. Test mode / trial 상태
        self.current_test_mode = TestMode.FULL
        self.current_target_group_idx: int = -1
        self.current_target_group_list_index: int = -1
        self.current_trial_idx: int = 0
        self.is_update_at_last_trial: bool = False
        self.is_previous_trial_updated: bool = False
        self.current_gen_trial_LLR_mode = None
        self.current_gen_trial_LLR_mode_index: int = -1
        self.max_modification_trial: int = 0

        # 4. Uncor pool 상태 (pool_has_uncor는 세션 유지이므로 여기서 초기화 안 함)
        self.current_loaded_test_mode: Optional[TestMode] = None
        self.is_uncor_pool_ready: bool = False

        # 5. Copy 캐시
        self.copy_row_candidates: list = []
        self.copy_group_candidates: list = []
        self._external_row_cache: Optional[list] = None  # 외부 후보 캐시 (Set_Gen_Trial_LLR_Mode에서 로드)

        # 6. Save tracking
        self._last_saved_local_matrix_idx: int = -1

    # ========== 프로퍼티 ==========

    @property
    def is_load_seed_mode(self) -> bool:
        """LOAD_UNCOR_SEED, LOAD_UNCOR_VECTOR, LOAD_UNCOR_SEED_SAVE_UNCOR_SEED 중 하나인지"""
        return self.current_seed_mode in [
            SeedMode.LOAD_UNCOR_SEED,
            SeedMode.LOAD_UNCOR_VECTOR,
            SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED
        ]

    @property
    def is_load_uncor_seed_file_mode(self) -> bool:
        """uncor seed 파일을 로드하는 모드인지 (LOAD_UNCOR_VECTOR 제외)"""
        return self.current_seed_mode in [
            SeedMode.LOAD_UNCOR_SEED,
            SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED
        ]

    @property
    def active_cores(self) -> list[int]:
        """excluded_cores를 제외한 활성 코어 목록"""
        return [proc for proc in range(self.num_process) if proc not in self.excluded_cores]

    def _collect_error_state_snapshot(self, include_stack: bool = True) -> str:
        """
        예외 발생 시 참고할 수 있도록 주요 속성 값을 문자열로 정리한다.

        Args:
            include_stack: True면 호출 스택 로컬 변수도 수집 (기본값: True).
                           MPI_Abort에서 이미 스택을 수집한 경우 False로 호출하여 중복 방지.
        """
        snapshot: dict[str, str] = {}
        for key, value in self.__dict__.items():
            if key in {"comm"}:
                continue
            if callable(value):
                continue
            try:
                snapshot[key] = _summarize_value(value)
            except Exception as error:
                snapshot[key] = f"<summary failed: {error!r}>"

        result = "=== Instance Variables ===\n"
        result += pformat(snapshot, sort_dicts=True, width=200)

        # 호출 스택의 로컬 변수 수집 (옵션)
        if include_stack:
            local_vars_snapshot: dict[str, dict[str, str]] = {}
            for frame_info in inspect.stack()[1:]:  # [0]은 현재 함수이므로 제외
                frame = frame_info.frame
                func_name = frame_info.function
                filename = os.path.basename(frame_info.filename)
                lineno = frame_info.lineno
                frame_key = f"{filename}:{func_name}:{lineno}"

                frame_locals: dict[str, str] = {}
                for key, value in frame.f_locals.items():
                    if key == "self":
                        continue
                    if callable(value):
                        continue
                    try:
                        frame_locals[key] = _summarize_value(value)
                    except Exception as error:
                        frame_locals[key] = f"<summary failed: {error!r}>"

                if frame_locals:
                    local_vars_snapshot[frame_key] = frame_locals

            result += "\n\n=== Local Variables (Call Stack) ===\n"
            result += pformat(local_vars_snapshot, sort_dicts=True, width=200)

        return result

    def _write_debug_snapshot(self, msg: str) -> None:
        """디버그 스냅샷 파일을 생성한다.

        현재 프로세스 상태 요약과 메시지를 포함한 텍스트 파일을 세션 디렉터리에 저장한다.

        Args:
            msg (str): 스냅샷에 기록할 설명 메시지.

        Returns:
            None
        """

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_name = f"Snapshot_{timestamp}_rank{self.rank}.txt"
            snapshot_path = os.path.join(self.session_debug_snapshot_dir, file_name)

            snapshot_lines = [
                f"[Debug Snapshot] {msg}",
                f"Timestamp: {datetime.datetime.now().isoformat()}",
                f"Process rank: {self.rank} / {self.num_process}",
                "",
                self._collect_error_state_snapshot(),
            ]

            with open(snapshot_path, "w", encoding="utf-8") as snapshot_file:
                snapshot_file.write("\n".join(snapshot_lines))
        except Exception as error:
            self.Write_Log_Lines(f"[WARN] Failed to write debug snapshot: {error}")

    def _get_new_CSW(self, min_val: int, max_val: int) -> tuple[Optional[int], Optional[str]]:
        """CSW thr를 무작위로 선택한다.

        허용 범위와 단계 값을 바탕으로 새로운 CSW 임계값 후보를 골라 반환한다.

        Args:
            min_val (int): 허용 최소 임계값.
            max_val (int): 허용 최대 임계값.

        Returns:
            tuple[Optional[int], Optional[str]]: 선택된 임계값과 실패 시 오류 메시지.
        """
        if min_val > max_val:
            return None, f"_get_new_CSW fail(min_val:{min_val}, max_val:{max_val})"

        possible = np.arange(min_val, max_val + STEP_CSW, STEP_CSW, dtype=int)
        possible = possible[(possible >= min_val) & (possible <= max_val)]
        if possible.size == 0:
            return None, f"_get_new_CSW fail(min_val:{min_val}, max_val:{max_val}, step:{STEP_CSW})"

        return int(random.choice(possible.tolist())), None

    def _generate_random_row(self, matrix:LLR_MATRIX, iter_end: Optional[int] = None) -> np.ndarray:
        """헤더 범위에 맞는 랜덤 행을 생성한다.

        매트릭스 헤더의 최소/최대 값을 활용해 각 row를 난수로 채우고 정렬 규칙을 적용한다.
        row가 HD 복호의 HBF 구간에 들어가면 dv_idx 0의 TH는 HBF_OPT_TH_CONSTANT_VAL로 채운다
        (LLR_MATRIX.Get_Columns_Fixed_In_HBF_Iterations).

        Args:
            matrix (LLR_MATRIX): 기준이 되는 LLR 매트릭스 인스턴스.
            iter_end (Optional[int]): 만든 row가 들어갈 자리의 끝 iteration. 아직 모르면 None (모든 column을 난수로 채운다).

        Returns:
            np.ndarray: 정렬된 CH/TH 값을 담은 배열.

        Raises:
            ValueError: 헤더의 min/max 길이가 파라미터 개수와 일치하지 않을 때.
        """
        num_parameter_each_set = matrix.header.num_parameter_each_set
        num_dv = matrix.header.num_dv
        min_values = matrix.header.min_value.astype(int)
        max_values = matrix.header.max_value.astype(int)

        if len(min_values) != num_parameter_each_set or len(max_values) != num_parameter_each_set:
            error_msg = f"_generate_random_row: Header min/max value length mismatch with num_parameter_each_set. min: {len(min_values)}, max: {len(max_values)}, num_parameter_each_set: {num_parameter_each_set}"
            self.MPI_Abort(error_msg)

        raw_values = [
            random.randint(int(min_values[param_idx]), int(max_values[param_idx]))
            for _ in range(num_dv)
            for param_idx in range(num_parameter_each_set)
        ]
        raw_array = np.array(raw_values, dtype=np.int32)
        is_row_in_HBF_iterations = iter_end is not None and len(matrix.Get_Columns_Fixed_In_HBF_Iterations(iter_end)) > 0
        ch_th_values, tmp_msg = matrix.Correct_Ch_Th_In_Row(raw_array, is_row_in_HBF_iterations=is_row_in_HBF_iterations)

        return ch_th_values

    def _append_lines_without_rotation(self, lines: list[str]):
        """로그 파일에 줄 교체 없이 내용을 추가한다.
        로그 회전 조건을 확인하기 전에 루트 프로세스만 직접 파일에 문자열을 덧붙인다.

        Args:
            lines (list[str]): 기록할 로그 문자열 목록.

        Returns:
            None

        Raises:
            OSError: 파일 쓰기 과정에서 입출력 오류가 발생한 경우.
        """
        if not self.is_root or self.log_file_path is None:
            return

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as log_file:
                for line in lines:
                    log_file.write(f"{line}\n")
            self.log_line_count += len(lines)
        except OSError as error:
            # 파일 쓰기 실패 시 에러 메시지 출력 후 프로그램 종료
            error_msg = f"Failed to write log file {self.log_file_path}: {error}"
            if self._in_mpi_abort:
                # MPI_Abort 중 로그 쓰기 실패 → 재귀 차단, 직접 종료
                _write_error_log(self.rank, error)
                self.comm.Abort(1)
                return
            self.MPI_Abort(error_msg)

    def Bcast_Trial_LLR_Mode(self):
        try:
            mode_info = self._mpi_comm_with_timeout(
                self.comm.bcast,
                (
                    self.current_gen_trial_LLR_mode,
                    self.current_gen_trial_LLR_mode_name,
                    self.current_gen_trial_LLR_mode_index,
                    self.max_modification_trial,
                    self.current_target_group_idx,
                    self.current_target_group_list_index,
                ) if self.is_root else None,
                comm_name="Bcast_Trial_LLR_Mode"
            )

            (
                self.current_gen_trial_LLR_mode,
                self.current_gen_trial_LLR_mode_name,
                self.current_gen_trial_LLR_mode_index,
                self.max_modification_trial,
                self.current_target_group_idx,
                self.current_target_group_list_index,
            ) = mode_info
        except Exception as e:
            self.Write_MPI_Error_Snapshot(e, "Bcast_Trial_LLR_Mode")
            error_msg = f"Bcast_Trial_LLR_Mode failed: {type(e).__name__}: {e}"
            self.MPI_Abort(error_msg)

    def Build_ECC(self):
        """ECC 실행 파일을 빌드한다.
        리눅스 환경에서, build된 파일이 없을 때만 수행한다.
        루트 프로세스에서 조건을 확인한 뒤 Makefile을 복사하고 `make`를 실행한다.

        Args:
            없음.

        Returns:
            None

        Raises:
            SystemExit: 필수 파일이 없거나 빌드가 실패한 경우.
        """

        if not self.is_root:
            return

        if os.path.exists(PATH_CONFIG.INPUT_ECC_EXE_PATH):
            self.Write_Log_Lines(f"[Skipping ECC build] Existing executable found: {PATH_CONFIG.INPUT_ECC_EXE_PATH}")
            return
        if CURRENT_OS is not OperatingSystem.LINUX:
            self.Write_Log_Lines("[Skipping ECC build] Supported only on Linux hosts.")
            return
        if not os.path.exists(PATH_CONFIG.INPUT_ECC_SRC_DIR_PATH):
            self.Write_Log_Lines(f"[Skipping ECC build] INPUT_ECC_SRC_DIR_PATH does not exist. {PATH_CONFIG.INPUT_ECC_SRC_DIR_PATH}")
            return
        
        makefile_src_dir = PATH_CONFIG.UTIL_DIR_PATH
        makefile_name = MAKEFILE_NAME
        makefile_src_path = os.path.join(makefile_src_dir, makefile_name)
        if not os.path.isdir(makefile_src_dir) or not os.path.isfile(makefile_src_path):
            self.MPI_Abort(f"Makefile not found: {makefile_src_path}")

        makefile_target_dir = PATH_CONFIG.INPUT_ECC_DIR_PATH
        makefile_target_path = os.path.join(makefile_target_dir, makefile_name)
        if not os.path.exists(makefile_target_path):
            shutil.copy2(makefile_src_path, makefile_target_path)
        if CURRENT_OS is not OperatingSystem.WINDOWS:
            os.chmod(makefile_target_path, 0o777)

        self.Write_Log_Lines(f"[Build_ECC] Start ECC build process...")

        env = os.environ.copy()
        env.update(
            {
                "PROJECT_DIR": PATH_CONFIG.INPUT_ECC_DIR_PATH,
                "EXEC_NAME": PATH_CONFIG.ECC_EXE_NAME,
            }
        )

        try:
            result = subprocess.run(
                ["make"],
                cwd=makefile_target_dir,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

        except FileNotFoundError as error:
            self.MPI_Abort(f"Failed to start make: {error}")
        except subprocess.CalledProcessError as error:
            if error.stdout:
                for line in error.stdout.splitlines():
                    self.Write_Log_Lines(line)
            if error.stderr:
                for line in error.stderr.splitlines():
                    self.Write_Log_Lines(line)
            stderr_hint = f" stderr: {error.stderr[:300]}" if error.stderr else ""
            self.MPI_Abort(f"ECC build failed with exit code {error.returncode}.{stderr_hint}")

        # 출력 로그 처리
        for stream_data in [result.stdout, result.stderr]:
            if stream_data:
                for line in stream_data.splitlines():
                    self.Write_Log_Lines(f"- {line}")

        object_dir_path = os.path.join(PATH_CONFIG.INPUT_ECC_DIR_PATH, OBJECT_DIR_NAME)
        if os.path.isdir(object_dir_path):
            try:
                shutil.rmtree(object_dir_path)
                self.Write_Log_Lines(f"[Build_ECC] Removed intermediate object directory: {object_dir_path}")
            except OSError as error:
                self.Write_Log_Lines(f"[WARNING] Failed to remove object directory {object_dir_path}: {error}")

        self.Write_Log_Lines(f"[Build_ECC] ECC build completed successfully. {PATH_CONFIG.INPUT_ECC_EXE_PATH}")

    def Cleanup_Test_Environment(self) -> None:
        """trial 실행 후 테스트 산출물을 정리한다.

        각 프로세스가 자신의 local_session_dir 하위 임시 파일을 제거해 다음 시도가 깨끗한 환경에서 시작되도록 보장한다.

        Args:
            없음.

        Returns:
            None
        """
        removed_files = []
        for root, dirs, files in os.walk(self.local_session_dir):
            for file in files:
                # 확장자 또는 이름 헤더로 필터링
                if (
                    any(file.endswith(ext) for ext in EXTENSIONS_TO_REMOVE)
                    or any(file.lower().startswith(prefix.lower()) for prefix in HEADER_TO_REMOVE)
                ):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        removed_files.append(file)
                    except OSError as error:
                        self.Write_Log_Lines(f"[WARN] Failed to remove {file_path}: {error}")

        if DEBUG_CONFIG.ENABLE_PRINT_CLEAN_HISTORY:
            self.Write_Log_Lines(
                f"[Removed execution artifacts]: {removed_files} @ {self.Get_Timestamp()}"
            )

    def _Cleanup_LLR_Matrix_Files(self) -> None:
        """local_session_dir에서 LLR_MATRIX 파일을 삭제하고 save 플래그를 초기화한다."""
        for file in os.listdir(self.local_session_dir):
            if file.lower().startswith("llr_matrix"):
                file_path = os.path.join(self.local_session_dir, file)
                try:
                    os.remove(file_path)
                except OSError as e:
                    self.Write_Log_Lines(f"[WARN] Cleanup failed: {e}")
        self._last_saved_local_matrix_idx = -1

    def Cleanup_Session(self) -> None:
        """세션 디렉터리에서 최종 산출물을 제거한다.

        테스트 후 남은 실행 파일과 프로세스별 작업 디렉터리를 삭제해 스토리지 사용량을 통제한다.

        Args:
            없음.

        Returns:
            None
        """
        if not self.is_root:
            return
        removed_files = []
        removed_dirs = []

        extensions_to_remove = [".exe", ".bat", ".sh", ".tmp"]
        dir_header_to_remove = [PROCESS_DIR_NAME_HEAD]  # 이 이름으로 시작하는 디렉토리 삭제

        for root, dirs, files in os.walk(self.session_dir):
            for file in files:
                if any(file.endswith(ext) for ext in extensions_to_remove):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        removed_files.append(file_path)
                    except OSError as error:
                        self.Write_Log_Lines(f"[WARN] Failed to remove {file_path}: {error}")

            # 디렉토리 삭제
            for dir_name in dirs:
                if any(dir_name.lower().startswith(prefix.lower()) for prefix in dir_header_to_remove):
                    dir_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(dir_path)
                        removed_dirs.append(dir_path)
                    except OSError as error:
                        self.Write_Log_Lines(f"[WARN] Failed to remove directory {dir_path}: {error}")

        if removed_files:
            self.Write_Log_Lines(
                f"[Removed execution artifacts]: {removed_files} @ {self.Get_Timestamp()}",
                )
        self.Write_Log_Separator("Simulation Ends", SEPARATOR_TYPE2)
        
    def Count_Gathered_Uncors(self, file_path) -> int :
        """uncor 수를 재계산한다.(seed, vector 구분)

        병합된 시드 파일에서 공백이 아닌 라인 수를 세어 누적 시드 개수를 갱신한다.

        Args:
            file_path (pathlib.Path): 집계할 시드 파일 경로.

        Returns:
            num_uncor_seeds
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                non_empty_line_count = sum(1 for line in f if line.strip())
        except FileNotFoundError:
            return 0  # 파일이 없으면 0개

        if UNCOR_CONFIG.NUM_LINES_PER_UNCOR == 0:
            return 0  # ZeroDivisionError 방지

        num_uncor_seeds = int(non_empty_line_count / UNCOR_CONFIG.NUM_LINES_PER_UNCOR)
        return num_uncor_seeds

    def Check_Test_End(self, ch_idx:int=0):
        """테스트 종료 여부를 결정한다.

        먼저 외부에서 설정한 종료 플래그를 확인하고, 설정되어 있으면 즉시 종료한다.
        그렇지 않으면 시드 모드와 누적 에러수를 확인해 추가 실행이 필요한지 판단한다.

        Args:
            ch_idx (int): 채널 인덱스. 기본값 0.

        Returns:
            None
        """
        if self.is_load_seed_mode:
            self.is_test_end = True
            self.Write_Run_ECC_End_Flag(True)
            return

        self.Read_Run_ECC_End_Flag()
        if self.is_test_end:
            return

        if self.is_root:
            if self.total_num_errors[ch_idx] >= self.max_error:
                self.Write_Run_ECC_End_Flag(True)
        self.Read_Run_ECC_End_Flag()

    def _Write_End_Flag(self, file_path: str, flag: bool = False):
        """종료 플래그 파일에 값을 쓴다. (root 전용)"""
        if not self.is_root:
            return
        try:
            with open(file_path, "w") as f:
                f.write("1" if flag else "0")
        except OSError as e:
            self.MPI_Abort(f"_Write_End_Flag failed at {file_path}: {e}")

    def _Write_End_Flag_Count(self, file_path: str, count: int):
        """종료 플래그 파일에 정수 값을 쓴다. (root 전용)"""
        if not self.is_root:
            return
        try:
            with open(file_path, "w") as f:
                f.write(str(count))
        except OSError as e:
            self.MPI_Abort(f"_Write_End_Flag_Count failed at {file_path}: {e}")

    def _Read_End_Flag(self, file_path: str) -> bool:
        """종료 플래그 파일을 읽어 bool로 반환한다."""
        try:
            with open(file_path, "r") as f:
                return f.read().strip() == "1"
        except FileNotFoundError:
            return False

    def Write_Run_ECC_End_Flag(self, flag: bool = False):
        self._Write_End_Flag(PATH_CONFIG.RUN_ECC_END_FLAG_FILE_PATH, flag)

    def Read_Run_ECC_End_Flag(self):
        self.is_test_end = self._Read_End_Flag(PATH_CONFIG.RUN_ECC_END_FLAG_FILE_PATH)

    def _Read_End_Flag_Count(self, file_path: str) -> int:
        """종료 플래그 파일의 값을 정수로 읽는다. 0이면 정상, N>0이면 스킵."""
        try:
            with open(file_path, "r") as f:
                value = f.read().strip()
                if value.isdigit():
                    return int(value)
                self.Write_Log_Lines(f"[WARN] _Read_End_Flag_Count: Invalid value '{value}' in {file_path}, using 0")
                return 0
        except (FileNotFoundError, ValueError):
            return 0

    def Read_Trial_End_Flag(self) -> int:
        """Trial 종료 플래그를 읽는다. 0이면 정상, N>0이면 N개 stage 스킵."""
        return self._Read_End_Flag_Count(PATH_CONFIG.TRIAL_END_FLAG_FILE_PATH)

    def Read_DAO_End_Flag(self) -> bool:
        """DAO 종료 플래그를 읽는다. True면 현재 DAO 실행을 중단한다."""
        return self._Read_End_Flag(PATH_CONFIG.DAO_END_FLAG_FILE_PATH)

    def _Write_Stop_Idx(self, stop_idx: int):
        """GEN_SINGLE_ROW graceful stop 인덱스를 파일에 기록한다. (root 전용)"""
        if not self.is_root:
            return
        file_path = os.path.join(self.end_flag_dir, GEN_SINGLE_ROW_STOP_IDX_FILE_NAME)
        try:
            with open(file_path, "w") as f:
                f.write(str(stop_idx))
        except OSError as e:
            self.MPI_Abort(f"_Write_Stop_Idx failed at {file_path}: {e}")

    def _Read_Stop_Idx(self) -> Optional[int]:
        """GEN_SINGLE_ROW stop 인덱스를 읽는다. 파일 없으면 None 반환."""
        file_path = os.path.join(self.end_flag_dir, GEN_SINGLE_ROW_STOP_IDX_FILE_NAME)
        try:
            with open(file_path, "r") as f:
                value = f.read().strip()
                return int(value) if value.isdigit() else None
        except (FileNotFoundError, ValueError):
            return None

    def _Get_Compare_Target(self):
        """현재 비교 대상 매트릭스를 반환한다. (early channel exit용)

        Check_Partial_Improvement 및 Determine_Update_Decision과 동일한 비교 대상:
        - is_update_at_last_trial=True: temp_optimal (있으면) / optimal
        - is_update_at_last_trial=False: 항상 optimal (temp_optimal 미사용)
        """
        if self.is_update_at_last_trial and self.temp_optimal_LLR_matrix is not None:
            return self.temp_optimal_LLR_matrix
        return self.optimal_LLR_matrix

    def _Is_Channel_Degraded(self, matrix, ch_idx: int) -> bool:
        """테스트 완료된 채널의 FER이 비교 대상보다 나빠졌는지 확인한다.

        Args:
            matrix: 현재 테스트 중인 매트릭스
            ch_idx: 테스트 완료된 채널 인덱스

        Returns:
            bool: 열화 발생 시 True
        """
        compare_target = self._Get_Compare_Target()
        if compare_target is None:
            return False

        if self.current_test_mode == TestMode.PARTIAL:
            current_fer = matrix.FERs_partial[ch_idx]
            target_fer = compare_target.FERs_partial[ch_idx]
        else:
            current_fer = matrix.FERs[ch_idx]
            target_fer = compare_target.FERs[ch_idx]

        return current_fer > target_fer

    def _Fill_Untested_Channels(self, matrix, start_ch_idx: int):
        """미테스트 채널의 FER/avg_iter/num_errors/num_tests를 초기화한다. (early channel exit 시)

        FER=1.0으로 설정하여 Is_List_A_Strictly_Better가 정확히 False를 반환하도록 보장.
        """
        is_partial = (self.current_test_mode == TestMode.PARTIAL)
        for ch_idx in range(start_ch_idx, REFC_CONFIG.NUM_TARGET_CHANNELS):
            if is_partial:
                matrix.FERs_partial[ch_idx] = 1.0
                matrix.avg_iterations_partial[ch_idx] = -1.0
                matrix.num_errors_partial[ch_idx] = 0
                matrix.num_tests_partial[ch_idx] = 0
            else:
                matrix.FERs[ch_idx] = 1.0
                matrix.avg_iterations[ch_idx] = -1.0
                matrix.num_errors[ch_idx] = 0
                matrix.num_tests[ch_idx] = 0

    def _Write_Run_ECC_End_Ack(self):
        """Run ECC 종료 플래그 감지 시 ack 파일을 생성한다. (모든 프로세스)"""
        ack_dir = os.path.join(self.end_flag_dir, "run_ecc_ack")
        os.makedirs(ack_dir, exist_ok=True)
        ack_path = os.path.join(ack_dir, f"run_ecc_end_ack_rank{self.rank}.txt")
        excluded_str = " (excluded)" if self.is_current_core_excluded else ""
        try:
            with open(ack_path, "w") as f:
                f.write(f"rank {self.rank} ack{excluded_str}")
        except OSError as e:
            # 진단용 ack 파일이므로 MPI_Abort 대신 경고만 기록
            _write_error_log(self.rank, e)

    def _Report_Missing_Acks(self):
        """ack 파일을 작성하지 않은 프로세스 목록을 별도 폴더에 기록한다. (root 전용)

        excluded_cores는 ack 대상에서 제외하며, 미작성 프로세스가 없으면 파일을 생성하지 않는다.
        """
        if not self.is_root:
            return

        ack_dir = os.path.join(self.end_flag_dir, "run_ecc_ack")
        status_dir = os.path.join(self.end_flag_dir, "run_ecc_ack_status")
        os.makedirs(status_dir, exist_ok=True)

        # ack 파일이 존재하는 rank 수집
        acked_ranks = set()
        if os.path.isdir(ack_dir):
            for fname in os.listdir(ack_dir):
                # run_ecc_end_ack_rank0.txt → 0
                if fname.startswith("run_ecc_end_ack_rank") and fname.endswith(".txt"):
                    try:
                        rank_str = fname[len("run_ecc_end_ack_rank"):-len(".txt")]
                        acked_ranks.add(int(rank_str))
                    except ValueError as e:
                        self.Write_Log_Lines(f"[WARN] ACK parse failed: {e}")

        # 대상 rank = 전체 - excluded
        expected_ranks = set(range(self.num_process)) - set(self.excluded_cores)
        missing_ranks = sorted(expected_ranks - acked_ranks)

        status_path = os.path.join(status_dir, "missing_acks.txt")
        if missing_ranks:
            with open(status_path, "w") as f:
                f.write(f"Missing acks: {', '.join(f'rank {r}' for r in missing_ranks)}\n")
                if self.excluded_cores:
                    f.write(f"Excluded cores: {sorted(self.excluded_cores)}\n")
        elif os.path.exists(status_path):
            os.remove(status_path)

    def Copy_Uncors(self, ch_idx: int = 0, is_uncor_type_seed: bool = True, test_mode: TestMode = TestMode.FULL):
        """Input 디렉토리에 있는 uncor seed를 세션 디렉터리로 복사한다.

        Args:
            ch_idx (int): 채널 인덱스.
            is_uncor_type_seed (bool): True면 seed, False면 vector.
            test_mode (TestMode): TestMode.FULL. (Partial은 Dynamic Partial에서 동적 생성)

        디렉토리 구조:
            - UNCOR_MATRIX_IDX=-1: HD/ → Copied_uncors/
            - UNCOR_MATRIX_IDX>=0: HD/{llr_name}/ → Copied_uncors/{llr_name}/

        Returns:
            Optional[pathlib.Path]: 복사한 대상 파일 경로.

        Raises:
            ValueError: 입력 시드 파일이 존재하지 않을 때.
        """
        if not self.is_root:
            return

        uncor_matrix_idx = UNCOR_CONFIG.UNCOR_MATRIX_IDX

        # Input 경로 결정
        base_uncor_dir = os.path.join(PATH_CONFIG.INPUT_UNCOR_DIR_PATH, MODE_MAP[REFC_CONFIG.init_n])

        if uncor_matrix_idx == -1:
            src_dir = base_uncor_dir
        else:
            LLR_matrix_file_name = PATH_CONFIG.LLR_MATRIX_FILE_NAME_TEMPLATE.format(matrix_idx=uncor_matrix_idx)
            src_dir = os.path.join(base_uncor_dir, LLR_matrix_file_name)

        file_name = self.Get_Uncor_File_Name(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
        src_path = Path(src_dir) / file_name

        # Output 경로: Input과 동일한 구조로 Copied_uncors 하위에 생성
        if uncor_matrix_idx == -1:
            dest_dir = Path(self.session_uncor_dir) / "Copied_uncors"
        else:
            dest_dir = Path(self.session_uncor_dir) / "Copied_uncors" / LLR_matrix_file_name

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / file_name
        
        # src 파일 존재 확인 후 복사
        if not src_path.exists():
            error_msg = f"[Copy_Uncors] Error: Missing input uncor file: src_path:{src_path}"
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
        
        # 기존 파일 있으면 삭제
        if dest_path.exists():
            dest_path.unlink()

        shutil.copy2(src_path, dest_path)
        self.total_num_uncors[ch_idx] = self.Count_Gathered_Uncors(file_path=dest_path)
        self.Write_Log_Lines(f"[Input Uncor Seeds Copied]: total_num_uncors[{ch_idx}]: {self.total_num_uncors[ch_idx]}\n\t{src_path.name} → {dest_path}.")
        return dest_path
    
    def Copy_ECC_EXE(self):
        """ECC 실행 파일을 로컬 세션으로 복사한다.

        Args:
            없음.

        Returns:
            None

        Raises:
            SystemExit: 실행 파일이 없거나 복사에 실패할 때.
        """
        self.MPI_Barrier()
        exe_source_path = PATH_CONFIG.INPUT_ECC_EXE_PATH
        exe_target_path = os.path.join(self.local_session_dir, PATH_CONFIG.ECC_EXE_NAME)
        try:
            if not os.path.exists(exe_source_path):
                error_msg = f"Set_Run_ECC_Environment: ECC executable not found. exe_source_path: {exe_source_path}"
                self.MPI_Abort(error_msg)
            if not os.path.exists(exe_target_path):
                shutil.copy2(exe_source_path, exe_target_path)
                self.Write_Log_Lines(f"[Copy ECC] success.")
            if CURRENT_OS is not OperatingSystem.WINDOWS:
                os.chmod(exe_target_path, 0o777)
        except (FileNotFoundError, OSError) as error:
            self.MPI_Abort(f"Set_Run_ECC_Environment error: {error}")

    def Copy_H_Matrix(self):
        source_dir = PATH_CONFIG.INPUT_H_MATRIX_DIR_PATH
        target_dir = os.path.join(self.local_session_dir, H_MATRIX_DIR_NAME)
        try:
            if not os.path.isdir(source_dir):
                error_msg = f"Copy_H_Matrix: Source directory not found. source_dir: {source_dir}"
                self.MPI_Abort(error_msg)
            shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
            self.Write_Log_Lines(f"[Copy H-matrix] success.")
        except (FileNotFoundError, OSError) as error:
            self.MPI_Abort(f"Failed to copy H_Matrix: {error}")
    
    def Debug_Pause(self, msg: str = "") -> None:
        """
        지정된 세션 디렉터리 내 debug 플래그 파일을 감시하며,

        파일이 없으면 "0"으로 초기화해 생성한 뒤 대기 상태를 유지한다.
        """
        if not DEBUG_CONFIG.ENABLE_FILE_BREAKPOINT:
            return
        
        self.MPI_Barrier()
        display_msg = msg or "Debug pause"
        self.Write_Log_Lines(display_msg)
        if DEBUG_CONFIG.IS_DEBUG_PAUSE_PRINT_SNAPSHOT:
            self._write_debug_snapshot(display_msg)
        
        sleep_interval = 1
        default_value = "0"
        debug_control_path = os.path.join(self.work_space_dir, DEBUG_DIR_NAME, DEBUG_FILE_NAME)

        if self.is_root:
            display_str = f"[PAUSE] {display_msg}. Waiting for value change {debug_control_path} from '{default_value}'."
            print(display_str, flush=True)
            self.Write_Log_Lines(display_str)

        while True:
            if self.debug_is_init:
                if self.is_root:
                    with open(debug_control_path, "w", encoding="utf-8") as f:
                        f.write(f"{default_value}")
                    display_str = f"[PAUSE] {display_msg}. Created '{debug_control_path}' with default '{default_value}'."
                    print(display_str, flush=True)
                    self.Write_Log_Lines(display_str)                    
                self.debug_is_init = False
            else:
                with open(debug_control_path, "r", encoding="utf-8") as f:
                    flag = f.read().strip()
                if flag != default_value:
                    break
            time.sleep(sleep_interval)
            self.MPI_Barrier()
        self.MPI_Barrier()
        
        display_str = f"[Rank: {self.comm.rank}, cnt: {self.debug_cnt}]"
        print(display_str, flush=True)
        self.Write_Log_Lines(display_str)                    
        self.debug_cnt += 1

        time.sleep(sleep_interval * 3)
        if self.is_root:
            with open(debug_control_path, "w", encoding="utf-8") as f:
                f.write(f"{default_value}")

    def Determine_Update_Decision(self, is_initial: bool, is_forced_last_trial: bool = False):
        if is_initial:
            return True, UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT

        # 시간 제한으로 인한 강제 종료 또는 실제 마지막 trial
        is_last_trial = is_forced_last_trial or (self.current_trial_idx == self.max_modification_trial)

        if self.is_update_at_last_trial:
            if not is_last_trial:
                # 중간 trial: temp_optimal만 업데이트
                if self.temp_optimal_LLR_matrix is None:
                    # REORDER_GROUP: 초기 테스트에서 temp_optimal 강제 초기화
                    # (current = optimal이라 Is_Matrix_Better가 False 반환하므로 특별 처리)
                    if self.current_gen_trial_LLR_mode == GenLLRMode.REORDER_GROUP:
                        return True, UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT
                    if self.Is_Matrix_Better(self.current_LLR_matrix, self.optimal_LLR_matrix):
                        return True, UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT
                else:
                    if self.Is_Matrix_Better(self.current_LLR_matrix, self.temp_optimal_LLR_matrix):
                        return True, UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT
            else:
                # 마지막 trial: optimal 업데이트
                # best_candidate를 global optimal과 비교하여 업데이트 여부 결정
                if self.temp_optimal_LLR_matrix is None:
                    if self.Is_Matrix_Better(self.current_LLR_matrix, self.optimal_LLR_matrix):
                        return True, UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT
                else:
                    # temp_optimal이 있는 경우
                    # 1. current vs temp_optimal 중 더 좋은 것 선택
                    if self.Is_Matrix_Better(self.current_LLR_matrix, self.temp_optimal_LLR_matrix):
                        best_candidate = self.current_LLR_matrix
                        update_mode = UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT
                    else:
                        best_candidate = self.temp_optimal_LLR_matrix
                        update_mode = UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL

                    # 2. best_candidate vs global optimal 비교
                    if self.Is_Matrix_Better(best_candidate, self.optimal_LLR_matrix):
                        return True, update_mode
            return False, None
        else:
            if self.Is_Matrix_Better(self.current_LLR_matrix, self.optimal_LLR_matrix):
                return True, UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT

        return False, None

    def Check_Partial_Improvement(self) -> tuple[bool, bool, bool]:
        """Partial 테스트 결과가 개선되었는지 확인한다.

        Two-stage 모드에서 Full 테스트를 수행할지 결정하기 위한 1차 필터링.
        Partial vs Partial 비교로 동일 조건에서 개선 여부 판단.

        should_proceed 조건: 개선 시에만 Full 진행 (strictly better)
        - 모든 채널 A[i] <= B[i]이고 하나 이상 strictly better이면 Full 테스트 진행
        - 동일하거나 열화이면 Full 스킵

        Returns:
            tuple[bool, bool, bool]: (should_proceed, is_actually_improved, is_last_trial)
                - should_proceed: Full 테스트 진행 여부 (개선 시에만 True)
                - is_actually_improved: 실제 Partial FER strictly better 여부
                - is_last_trial: 마지막 trial 여부
        """
        # is_update_at_last_trial 로직 적용
        if self.is_update_at_last_trial:
            is_last_trial = (self.current_trial_idx == self.max_modification_trial)

            # 비교 대상 결정
            if self.temp_optimal_LLR_matrix is None:
                compare_target = self.optimal_LLR_matrix
            else:
                compare_target = self.temp_optimal_LLR_matrix

            # 실제 개선 여부 확인 (strictly better)
            is_actually_improved = self.Is_List_A_Strictly_Better(
                self.current_LLR_matrix.FERs_partial,
                compare_target.FERs_partial
            )

            if is_last_trial:
                # 마지막 trial: 개선 여부와 상관없이 Full 테스트 진행
                return True, is_actually_improved, True
            else:
                # 중간 trial: 개선 시에만 Full 테스트 진행
                return is_actually_improved, is_actually_improved, False
        else:
            # is_update_at_last_trial=False: 매번 optimal의 Partial FER과 비교
            is_actually_improved = self.Is_List_A_Strictly_Better(
                self.current_LLR_matrix.FERs_partial,
                self.optimal_LLR_matrix.FERs_partial
            )
            return is_actually_improved, is_actually_improved, False

    def Delete_Uncors(self, ch_idx: int = 0, is_uncor_type_seed: bool = True):
        """로컬 세션에 남은 uncor 시드를 삭제한다.

        모든 프로세스별 세션 디렉터리에서 시드 파일을 제거해 다음 배포 전에 환경을 초기화한다.

        Args:
            ch_idx (int): 채널 인덱스.
            is_uncor_type_seed (bool): seed 타입 여부.

        Returns:
            None
        """
        if not self.is_root:
            return
        for proc in range(self.num_process):
            target_dir = self.Get_Local_Session_Dir(proc)
            target_file_name = self.Get_Uncor_File_Name(process_idx=proc, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
            target_path = Path(target_dir) / target_file_name
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception as e:
                    self.Write_Log_Lines(f"⚠️ Failed to delete {target_path.name}: {e}")
        self.Write_Log_Lines(f"[Delete all local uncor seeds]")

    def Delete_Own_Uncors(self, ch_idx: int = 0, is_uncor_type_seed: bool = True, is_redecoded_uncor: bool = False):
        """현재 프로세스의 uncor 파일만 삭제한다 (병렬 실행용).

        SAVE_UNCOR_SEED 모드에서는 자신의 working copy를, LOAD_UNCOR_SEED_SAVE_UNCOR_SEED 모드에서는
        자신의 redecode 파일(is_redecoded_uncor=True)을 Ref-C 실행 전에 지울 때 사용한다.
        제외된 코어는 삭제를 시도하지 않는다.
        """
        if self.is_current_core_excluded:
            return
        target_file_name = self.Get_Uncor_File_Name(process_idx=self.rank, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, is_redecoded_uncor=is_redecoded_uncor)
        target_path = Path(self.local_session_dir) / target_file_name
        if target_path.exists():
            try:
                target_path.unlink()
            except OSError as e:
                # 남은 파일은 다음 Ref-C 실행분과 섞여 uncor 수를 틀리게 하므로 멈춘다 (root 전용 로그로는 worker의 실패가 보이지 않는다)
                self.MPI_Abort(f"Delete_Own_Uncors: uncor 파일 삭제 실패, {target_path}: {e}")

    def Distribute_Uncors_To_Local_Session(self, src_path, ch_idx: int = 0, is_uncor_type_seed: bool = True):
        """uncor 시드를 프로세스별 세션으로 배포한다.

        수집된 시드 목록을 라운드로빈 방식으로 나누어 각 프로세스 디렉터리에 저장한다.
        제외된 코어(excluded_cores)는 건너뛰고 활성 코어들에게만 분배한다.

        Args:
            src_path (pathlib.Path): 분배할 시드 파일 경로.

        Returns:
            None
        """
        # root에서 uncor 분배 계산
        if self.is_root:
            has_uncor_list = [False] * self.num_process

            if not src_path.exists():
                self.Write_Log_Lines(f"Uncor dir not found: {src_path}")
            else:
                # 기존 파일 삭제
                self.Delete_Uncors(ch_idx=ch_idx)

                # 모든 라인 읽기
                with src_path.open("r", encoding="utf-8") as f:
                    all_lines = [line.rstrip("\n") for line in f if line.strip()]

                if not all_lines:
                    self.Write_Log_Lines(f"No seeds to distribute.")
                else:
                    # 활성 코어 목록 생성 (제외된 코어 제외)
                    active_cores = self.active_cores

                    if not active_cores:
                        self.Write_Log_Lines(f"⚠️  No active cores available for uncor distribution.")
                    else:
                        # round robin 분배 (활성 코어에만)
                        num_uncors = int(len(all_lines) / UNCOR_CONFIG.NUM_LINES_PER_UNCOR)

                        for uncor_idx in range(num_uncors):
                            # 활성 코어들 사이에서만 round-robin
                            target_proc = active_cores[uncor_idx % len(active_cores)]
                            has_uncor_list[target_proc] = True

                            dest_dir = self.Get_Local_Session_Dir(target_proc)
                            dest_file_name = self.Get_Uncor_File_Name(process_idx=target_proc, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
                            dest_path = Path(dest_dir) / dest_file_name

                            with dest_path.open("a", encoding="utf-8") as f:
                                for line_idx in range(UNCOR_CONFIG.NUM_LINES_PER_UNCOR):
                                    f.write(all_lines[uncor_idx * UNCOR_CONFIG.NUM_LINES_PER_UNCOR + line_idx] + "\n")

                        excluded_info = f" (제외된 코어: {len(self.excluded_cores)}개)" if self.excluded_cores else ""
                        self.Write_Log_Lines(f"[Distributed {num_uncors} uncors to {len(active_cores)} active cores for channel idx: {ch_idx}{excluded_info}]")
        else:
            has_uncor_list = None

        # 모든 process에게 uncor 수신 여부 전달
        self.MPI_Barrier()
        has_uncor_list = self._safe_bcast(has_uncor_list, "Bcast_has_uncor_list")
        self.has_uncor[ch_idx] = has_uncor_list[self.rank]

    def Get_CSW_Log_File_Name(self, process_idx:int):
        """CSW 로그 파일 이름을 생성한다.

        Args:
            process_idx (int): 로그 파일을 생성한 프로세스 인덱스.

        Returns:
            str: CSW 로그 파일 이름.
        """
        csw_log_file_name = f"log_CSW_{process_idx}.txt"
        return csw_log_file_name

    def Get_Result_File_Name(self, process_idx:int, ch_idx:int = 0):
        """Ref-C 결과 파일 이름을 생성한다.

        채널 및 시나리오 설정을 반영해 프로세스별 결과 파일 이름을 구성한다.

        Args:s
            process_idx (int): 결과 파일을 생성한 프로세스 인덱스.

        Returns:
            str: 결과 파일 이름.
        """
        if REFC_CONFIG.ECC_VER == "2.4":
            result_file_name = f"result_4KB_H_{REFC_CONFIG.matrix_sel}_CH_{REFC_CONFIG.ch_type}_E"
        else:
            result_file_name = f"result_4KB_S_{REFC_CONFIG.mode_scenario}_H_{REFC_CONFIG.matrix_sel}_CH_{REFC_CONFIG.ch_type}_E"

        if REFC_CONFIG.ch_type == 1:
            result_file_name = result_file_name + f'{REFC_CONFIG.RBERs[ch_idx]:.2e}_'
        elif REFC_CONFIG.ch_type == 2:
            result_file_name = result_file_name + f'{REFC_CONFIG.num_fixed_errs[ch_idx]:d}_'
        elif REFC_CONFIG.ch_type == 3:
            result_file_name = result_file_name + f'{REFC_CONFIG.num_fixed_errs[ch_idx]:d}_SC_{REFC_CONFIG.fixed_SCRs[ch_idx]:.2f}_SE_{REFC_CONFIG.fixed_SERs[ch_idx]:.2f}_'
        
        result_file_name = result_file_name + f'init_n_{REFC_CONFIG.init_n}_seed_{process_idx}.txt'
        return result_file_name

    def Get_Channel_Param_String(self, ch_idx: int, include_brackets: bool = False) -> str:
        """채널 인덱스에 대한 파라미터 문자열을 반환한다.

        Args:
            ch_idx: 채널 인덱스
            include_brackets: True면 대괄호로 감싼 형태 반환

        Returns:
            str: 채널 파라미터 문자열
                - ch_type=1: "RBER=0.01" 또는 "[RBER: 0.0100]"
                - ch_type=2: "E=5" 또는 "[num_fixed_err: 5]"
                - ch_type=3: "E=5, SCR=0.50, SER=0.30" 또는 "[SCR:0.50, SER: 0.30, num_fixed_err: 5]"
        """
        if include_brackets:
            if REFC_CONFIG.ch_type == 1:
                return f"[RBER: {REFC_CONFIG.RBERs[ch_idx]:.4f}]"
            elif REFC_CONFIG.ch_type == 2:
                return f"[num_fixed_err: {REFC_CONFIG.num_fixed_errs[ch_idx]:d}]"
            elif REFC_CONFIG.ch_type == 3:
                return f"[SCR:{REFC_CONFIG.fixed_SCRs[ch_idx]:.2f}, SER: {REFC_CONFIG.fixed_SERs[ch_idx]:.2f}, num_fixed_err: {REFC_CONFIG.num_fixed_errs[ch_idx]:d}]"
            else:
                return f"[ch{ch_idx}]"
        else:
            if REFC_CONFIG.ch_type == 1:
                return f"RBER={REFC_CONFIG.RBERs[ch_idx]}"
            elif REFC_CONFIG.ch_type == 2:
                return f"E={REFC_CONFIG.num_fixed_errs[ch_idx]}"
            elif REFC_CONFIG.ch_type == 3:
                return f"E={REFC_CONFIG.num_fixed_errs[ch_idx]}, SCR={REFC_CONFIG.fixed_SCRs[ch_idx]:.2f}, SER={REFC_CONFIG.fixed_SERs[ch_idx]:.2f}"
            else:
                return f"ch{ch_idx}"

    def Get_Test_Mode_String(self, test_mode: Optional['TestMode'] = None) -> str:
        """테스트 모드 문자열을 반환한다.

        Args:
            test_mode: 테스트 모드. None이면 current_test_mode 사용.

        Returns:
            str: "Full" 또는 "Partial"
        """
        if test_mode is None:
            test_mode = self.current_test_mode
        return "Partial" if test_mode == TestMode.PARTIAL else "Full"

    def Gather_CSW_Logs(self, matrix = None, ch_idx:int = 0):
        """모든 프로세스의 CSW 로그를 모아 저장한다.

        log_CSW와 uncor_seed를 별도 파일로 저장 (동일 line index 보장).
        제외된 코어(excluded_cores)는 건너뛴다.
        Two-stage 모드 시 Partial/Full 하위 디렉토리로 분리.
        """

        if self.is_root:
            CSW_all_lines = []
            uncor_seed_all_lines = []
            missing_procs = []
            for proc in range(self.num_process):
                # 제외된 코어는 건너뜀
                if proc in self.excluded_cores:
                    continue

                process_CSW_file_name = self.Get_CSW_Log_File_Name(process_idx=proc)
                process_session_dir = self.Get_Local_Session_Dir(proc)
                CSW_file_path = os.path.join(process_session_dir, process_CSW_file_name)
                try:
                    with open(CSW_file_path, 'r') as f:
                        CSW_lines = f.readlines()
                        CSW_all_lines.append(CSW_lines)
                    if self.is_load_uncor_seed_file_mode:
                        uncor_seed_file_name = self.Get_Uncor_File_Name(process_idx=proc, ch_idx=ch_idx, is_uncor_type_seed=True)
                        uncorseed_file_path = os.path.join(process_session_dir, uncor_seed_file_name)
                        if os.path.exists(uncorseed_file_path):
                            with open(uncorseed_file_path, 'r') as f:
                                uncor_seed_lines = [line.rstrip("\n") for line in f.readlines()]
                        else:
                            uncor_seed_lines = []
                        uncor_seed_all_lines.append(uncor_seed_lines)
                except FileNotFoundError:
                    self.Write_Log_Lines(f"[WARNING] Gather_CSW_Logs: rank {proc} CSW 파일 누락 — {CSW_file_path}")
                    missing_procs.append(proc)
                    CSW_all_lines.append([])
                    if self.is_load_uncor_seed_file_mode:
                        uncor_seed_all_lines.append([])

            active_procs = self.num_process - len(self.excluded_cores)
            if missing_procs:
                self.Write_Log_Lines(
                    f"[WARNING] Gather_CSW_Logs: {len(missing_procs)}/{active_procs}개 프로세스 CSW 누락 (ranks: {missing_procs})"
                )
            
            if REFC_CONFIG.ch_type == 1:
                str_ch = f"{REFC_CONFIG.RBERs[ch_idx]}"
            elif REFC_CONFIG.ch_type == 2:
                str_ch = f"{REFC_CONFIG.num_fixed_errs[ch_idx]}"
            elif REFC_CONFIG.ch_type == 3:
                str_ch = f'SC_{REFC_CONFIG.fixed_SCRs[ch_idx]:.2f}_SE_{REFC_CONFIG.fixed_SERs[ch_idx]:.2f}_{REFC_CONFIG.num_fixed_errs[ch_idx]}'
            else:
                self.MPI_Abort(f"Gather_CSW_Logs: Unsupported ch_type={REFC_CONFIG.ch_type}")

            # Two-stage Partial 모드: Partial/ 하위 디렉토리로 분리 저장 (Full은 루트)
            if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST and self.current_test_mode == TestMode.PARTIAL:
                csw_output_dir = os.path.join(self.optimal_output_dir, "Partial")
                os.makedirs(csw_output_dir, exist_ok=True)
            else:
                csw_output_dir = self.optimal_output_dir

            # uncor_seed와 log_CSW를 별도 파일로 저장 (동일 line index 보장)
            log_CSW_file_name = f"{LOG_CSW_FILE_NAME_HEAD}{matrix.LLR_matrix_file_name}_{str_ch}.txt"
            log_CSW_file_path = os.path.join(csw_output_dir, log_CSW_file_name)
            max_lines = max(len(lines) for lines in CSW_all_lines) if CSW_all_lines else 0

            try:
                with open(log_CSW_file_path, 'w') as csw_f:
                    for line_idx in range(max_lines):
                        for list_idx in range(len(CSW_all_lines)):
                            if line_idx < len(CSW_all_lines[list_idx]):
                                csw_f.write(CSW_all_lines[list_idx][line_idx])
            except OSError as e:
                self.MPI_Abort(f"Gather_CSW_Logs: CSW 로그 병합 쓰기 실패 — {log_CSW_file_path}: {e}")

            # uncor_seed 파일 별도 저장
            if uncor_seed_all_lines:
                uncor_seed_out_name = f"uncor_seed_{matrix.LLR_matrix_file_name}_{str_ch}.txt"
                uncor_seed_out_path = os.path.join(csw_output_dir, uncor_seed_out_name)
                try:
                    with open(uncor_seed_out_path, 'w') as seed_f:
                        for line_idx in range(max_lines):
                            for list_idx in range(len(uncor_seed_all_lines)):
                                if line_idx < len(uncor_seed_all_lines[list_idx]):
                                    seed_f.write(uncor_seed_all_lines[list_idx][line_idx] + '\n')
                except OSError as e:
                    self.MPI_Abort(f"Gather_CSW_Logs: uncor_seed 쓰기 실패 — {uncor_seed_out_path}: {e}")

    def Delete_CSW_Logs(self):
        if self.is_root:
            deleted_proc = []
            for proc in range(self.num_process):
                # 제외된 코어는 건너뜀
                if proc in self.excluded_cores:
                    continue

                file_name = self.Get_CSW_Log_File_Name(process_idx=proc)
                process_session_dir = self.Get_Local_Session_Dir(proc)
                file_path = os.path.join(process_session_dir, file_name)

                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_proc.append(proc)
                    except OSError as e:
                        self.MPI_Abort(f"Failed to delete CSW log file {file_path}: {e}")


    def Gather_Ref_C_Results(self, matrix = None, ch_idx:int = 0, is_test_end: bool = False):
        """Ref-C 결과를 집계해 매트릭스에 반영한다.

        각 프로세스의 결과 파일을 모아 전역 테스트/오류 통계를 계산하고 매트릭스의 FER 값을 갱신한다.

        Args:
            matrix (Optional[LLR_MATRIX]): 결과를 기록할 매트릭스 객체.

        Returns:
            None

        Raises:
            ValueError: 매트릭스가 제공되지 않은 경우.
        """
        if matrix is None:
            error_msg = "Gather_Ref_C_Results: Matrix must not be None when gathering results."
            self.MPI_Abort(error_msg)

        is_load_seed_mode = self.is_load_seed_mode

        if not is_test_end:
            # === while 루프 중: root만 순차 읽기 (기존 로직) ===
            if not self.is_root:
                return

            max_iteration = matrix.max_iteration
            total_tests = 0
            total_errors = 0
            total_iterations = 0.0
            total_error_per_iter = np.zeros(max_iteration, dtype="f8")

            for proc in range(self.num_process):
                if proc in self.excluded_cores:
                    continue

                file_name = self.Get_Result_File_Name(process_idx=proc, ch_idx=ch_idx)
                process_session_dir = self.Get_Local_Session_Dir(proc)
                file_path = os.path.join(process_session_dir, file_name)

                if os.path.exists(file_path):
                    sum_test, sum_error, sum_iteration, sum_error_per_iter = self.Read_Ref_C_Result(file_path)
                else:
                    continue

                total_tests += sum_test
                total_errors += sum_error
                total_iterations += sum_iteration
                if sum_error_per_iter is not None:
                    if len(sum_error_per_iter) != max_iteration:
                        min_len = min(len(sum_error_per_iter), max_iteration)
                        total_error_per_iter[:min_len] += sum_error_per_iter[:min_len]
                    else:
                        total_error_per_iter += sum_error_per_iter

        else:
            # === 테스트 종료: 각 rank가 자기 파일 읽고 MPI Reduce로 합산 ===
            self.MPI_Barrier()

            max_iteration = matrix.max_iteration
            buf_size = 3 + max_iteration  # [tests, errors, iterations, err_per_iter...]

            # 각 rank가 자기 result 파일 읽어서 sendbuf에 pack
            sendbuf = np.zeros(buf_size, dtype='f8')
            if not self.is_current_core_excluded:
                file_name = self.Get_Result_File_Name(process_idx=self.rank, ch_idx=ch_idx)
                file_path = os.path.join(self.local_session_dir, file_name)
                if os.path.exists(file_path):
                    s_test, s_error, s_iter, s_err_per_iter = self.Read_Ref_C_Result(file_path)
                    sendbuf[0] = s_test
                    sendbuf[1] = s_error
                    sendbuf[2] = s_iter
                    if s_err_per_iter is not None:
                        arr_len = min(len(s_err_per_iter), max_iteration)
                        sendbuf[3:3+arr_len] = s_err_per_iter[:arr_len]

            # MPI Reduce: 모든 rank의 sendbuf를 root에서 합산 (tree reduction)
            recvbuf = np.zeros(buf_size, dtype='f8') if self.is_root else None
            self.comm.Reduce(sendbuf, recvbuf, op=MPI.SUM, root=0)

            self.Finalize_ECC_Time()
            self.MPI_Barrier()

            # root가 recvbuf에서 unpack
            if self.is_root:
                total_tests = int(recvbuf[0])
                total_errors = int(recvbuf[1])
                total_iterations = float(recvbuf[2])
                total_error_per_iter = recvbuf[3:].copy()
                packed = (total_tests, total_errors, total_iterations, total_error_per_iter.tolist())
            else:
                packed = None

            self.MPI_Barrier()
            total_tests, total_errors, total_iterations, total_error_per_iter = self._safe_bcast(packed if self.is_root else None, "Bcast_ECC_results")

        # --- Array 변환 ---
        total_error_per_iter = np.array(total_error_per_iter, dtype="f8")
        total_FER_per_iter = (total_error_per_iter / total_tests) if total_tests else np.zeros_like(total_error_per_iter)

        if total_tests == 0:
            self.MPI_Abort(f"Gather_Ref_C_Results: total_tests=0 for ch_idx={ch_idx}. All cores failed to produce results.")
        FER_value = total_errors / total_tests
        avg_iteration = total_iterations / total_tests

        self.total_num_tests[ch_idx] = total_tests
        self.total_num_errors[ch_idx] = total_errors
        self.total_num_iterations[ch_idx] = total_iterations
        self.total_num_error_per_iters[ch_idx] = total_error_per_iter
        self.total_FER_per_iters[ch_idx] = total_FER_per_iter
        # Two-stage 모드: partial/full 구분하여 저장
        # self.current_test_mode: "full" (기본, Update 판단용) 또는 "partial" (1차 필터링용)
        is_partial_test = (UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST and self.current_test_mode == TestMode.PARTIAL)

        if is_load_seed_mode:
            self.total_num_seed_tests[ch_idx] = total_tests
            self.total_num_seed_errors[ch_idx] = total_errors
            self.total_seed_FERs[ch_idx] = FER_value
            if is_partial_test:
                matrix.seed_FERs_partial[ch_idx] = FER_value
                matrix.num_errors_partial[ch_idx] = total_errors
                matrix.num_tests_partial[ch_idx] = total_tests
            else:
                matrix.seed_FERs[ch_idx] = FER_value
                matrix.num_errors[ch_idx] = total_errors
                matrix.num_tests[ch_idx] = total_tests
        else:
            self.total_num_raw_tests[ch_idx] = total_tests
            self.total_num_raw_errors[ch_idx] = total_errors
            self.total_raw_FERs[ch_idx] = FER_value
            if is_partial_test:
                matrix.raw_FERs_partial[ch_idx] = FER_value
                matrix.num_errors_partial[ch_idx] = total_errors
                matrix.num_tests_partial[ch_idx] = total_tests
            else:
                matrix.raw_FERs[ch_idx] = FER_value
                matrix.num_errors[ch_idx] = total_errors
                matrix.num_tests[ch_idx] = total_tests

        # FERs에 raw_FER 또는 seed_FER 직접 저장 (effective_FER 불필요 - 한쪽이 항상 1.0)
        if is_partial_test:
            if is_load_seed_mode:
                matrix.FERs_partial[ch_idx] = matrix.seed_FERs_partial[ch_idx]
            else:
                matrix.FERs_partial[ch_idx] = matrix.raw_FERs_partial[ch_idx]
        else:
            if is_load_seed_mode:
                matrix.FERs[ch_idx] = matrix.seed_FERs[ch_idx]
            else:
                matrix.FERs[ch_idx] = matrix.raw_FERs[ch_idx]

        if is_partial_test:
            matrix.avg_iterations_partial[ch_idx] = avg_iteration
        else:
            matrix.avg_iterations[ch_idx] = avg_iteration

    def Get_Timestamp(self):
        """현재 시간을 문자열로 반환한다.

        Args:
            없음.

        Returns:
            str: `%Y-%m-%d %H:%M:%S` 형식의 타임스탬프.
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def Gen_Trial_LLR(self):
        if self.is_root:
            # Trial용 matrix 생성: FER 값은 테스트 후 새로 설정되므로 모두 리셋
            input_LLR_matrix = self.optimal_LLR_matrix.Deep_Copy(self.current_LLR_matrix_idx, copy_raw_FER=False, copy_seed_FER=False)
            new_LLR_matrix = None

            if self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_RANDOM_ROW:
                new_LLR_matrix = self.Gen_LLR_Insert_Random_Row(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.MUTATE_MATRIX:
                new_LLR_matrix = self.Gen_LLR_Mutate_Matrix(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.MUTATE_CSW:
                new_LLR_matrix = self.Gen_LLR_Mutate_CSW(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_RANDOM_GROUP:
                new_LLR_matrix = self.Gen_LLR_Insert_Random_Group(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_MUTATED_GROUP:
                new_LLR_matrix = self.Gen_LLR_Insert_Mutated_Group(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_MUTATED_ROW:
                new_LLR_matrix = self.Gen_LLR_Insert_Mutated_Row(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.GEN_INITIAL_GROUP:
                new_LLR_matrix = self.Gen_LLR_Gen_Initial_Group(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.REGEN_DV:
                new_LLR_matrix = self.Gen_LLR_Regen_DV(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.REGEN_ROW:
                new_LLR_matrix = self.Gen_LLR_Regen_Row(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.COPY_ROWS:
                new_LLR_matrix = self.Gen_LLR_Copy_Rows(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.COPY_GROUP:
                new_LLR_matrix = self.Gen_LLR_Copy_Group(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.SWAP_ROW:
                new_LLR_matrix = self.Gen_LLR_Swap_Row(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.REORDER_GROUP:
                new_LLR_matrix = self.Gen_LLR_Reorder_Group(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.ADJUST_ITERATION:
                new_LLR_matrix = self.Gen_LLR_Adjust_Iteration(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.DELETE_ROW:
                new_LLR_matrix = self.Gen_LLR_Delete_Row(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_RESTART_GROUP:
                new_LLR_matrix = self.Gen_LLR_Insert_Restart_Group(input_matrix=input_LLR_matrix)
            elif self.current_gen_trial_LLR_mode == GenLLRMode.SPLIT_GROUP:
                new_LLR_matrix = self.Gen_LLR_Split_Group(input_matrix=input_LLR_matrix)
            else:
                self.MPI_Abort(f"Gen_Trial_LLR: Unhandled GenLLRMode={self.current_gen_trial_LLR_mode}")

            # SW 분기 보호: 타겟 앞의 그룹(분기 구간)을 바꾼 trial은 버린다 (MUTATE 두 모드는 타겟 그룹만 만지므로 제외)
            if new_LLR_matrix is not None and int(self.current_gen_trial_LLR_mode) not in {int(mode) for mode in SW_BRANCH_ALLOWED_MODES}:
                protected_change = self._Protected_Groups_Changed(self.optimal_LLR_matrix, new_LLR_matrix)
                if protected_change is not None:
                    self.Write_Log_Lines(f"[SW branch] {self.current_gen_trial_LLR_mode_name} changed groups before the target: {protected_change}. Trial discarded")
                    new_LLR_matrix = None

            # LLR Matrix 생성 실패
            if new_LLR_matrix is None:
                self.generate_LLR_success = False
            
            # LLR Matrix 생성 성공
            else:
                self.generate_LLR_success = True
                try:
                    correct_msg = new_LLR_matrix.Correct_LLR_Matrix()
                    if correct_msg:
                        self.Write_Log_Lines(f"[Corrected LLR Matrix]")
                        for msg in correct_msg:
                            self.Write_Log_Lines(msg)
                except ValueError as e:
                    self.Write_Log_Lines(f"[WARN] Correct_LLR_Matrix failed: {e}")
                    self.generate_LLR_success = False
                if self.generate_LLR_success:
                    self.Update_Current_LLR(new_LLR_matrix)
                    self.Print_LLR_Matrix(self.current_LLR_matrix)
                    if DEBUG_CONFIG.ENABLE_SAVE_ALL_TRIAL_LLR_MATRIX:
                        self.Save_LLR_Matrix(self.current_LLR_matrix, target_dir=self.trial_output_dir)

        self.generate_LLR_success = self._safe_bcast(self.generate_LLR_success if self.is_root else None, "Bcast_generate_LLR_success")
        if self.generate_LLR_success:
            self.current_LLR_matrix = self._safe_bcast(self.current_LLR_matrix if self.is_root else None, "Bcast_current_LLR_matrix")
            # target_group_indices도 함께 동기화 (INSERT_RANDOM_GROUP에서 업데이트될 수 있음)
            self.target_group_indices = self._safe_bcast(self.target_group_indices if self.is_root else None, "Bcast_target_group_indices")

            # Multi-round 모드: 상태 변수 동기화 (공용)
            if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
                state_attr = MULTI_ROUND_MODES[self.current_gen_trial_LLR_mode]
                state = getattr(self, state_attr)
                state = self._safe_bcast(state if self.is_root else None, f"Bcast_{state_attr}")
                setattr(self, state_attr, state)

            # COPY_ROWS 모드: Trial 1에서 후보 리스트 동기화
            if self.current_gen_trial_LLR_mode == GenLLRMode.COPY_ROWS and self.current_trial_idx == 1:
                self.copy_row_candidates = self._safe_bcast(self.copy_row_candidates if self.is_root else None, "Bcast_copy_row_candidates")

            # COPY_GROUP 모드: Trial 1에서 후보 리스트 동기화
            if self.current_gen_trial_LLR_mode == GenLLRMode.COPY_GROUP and self.current_trial_idx == 1:
                self.copy_group_candidates = self._safe_bcast(self.copy_group_candidates if self.is_root else None, "Bcast_copy_group_candidates")

    def Generate_Initial_Random_Row(self):
        """초기 매트릭스에서 random row를 생성한다.

        초기 LLR 매트릭스를 기준으로 랜덤 행을 구성해 추가 변형 작업에 활용한다.

        Args:
            없음.

        Returns:
            np.ndarray: 생성된 CH/TH 값 배열.

        Raises:
            ValueError: 초기 매트릭스가 준비되지 않은 상태에서 호출된 경우.
        """
        if self.initial_LLR_matrix is None:
            error_msg = "Generate_Initial_Random_Row: Initial LLR matrix is not initialized."
            self.MPI_Abort(error_msg)
        return self._generate_random_row(self.initial_LLR_matrix)

    def Get_Decoder_Mode_Str(self) -> str:
        """디코더 모드를 문자열로 반환한다.

        Args:
            없음.

        Returns:
            str: 디코더 모드 식별 문자열.

        Raises:
            ValueError: 지원되지 않는 `init_n` 값이 설정된 경우.
        """
        if REFC_CONFIG.init_n not in MODE_MAP:
            error_msg = f"Get_Decoder_Mode_Str: init_n must be 1 (HD), 2 (2SD), or 3 (3SD). init_n: {REFC_CONFIG.init_n}"
            self.MPI_Abort(error_msg)
        return MODE_MAP[REFC_CONFIG.init_n]

    def Get_Uncor_File_Name(self, process_idx:int = 0, ch_idx:int = 0, is_uncor_type_seed: bool = True, is_redecoded_uncor: bool = False):
        if is_uncor_type_seed:
            redecode_header = "redecode_" if is_redecoded_uncor else ""
            uncor_type = "seed"
            extension = "txt"
        else:
            redecode_header = ""
            uncor_type = "vector"
            extension = "dat"
        if REFC_CONFIG.ch_type == 1:
            file_name = f"{redecode_header}uncor_{uncor_type}_H_{REFC_CONFIG.matrix_sel}_CH_{REFC_CONFIG.ch_type}_E{REFC_CONFIG.RBERs[ch_idx]:.2e}_init_n_{REFC_CONFIG.init_n}_{process_idx}.{extension}"
        elif REFC_CONFIG.ch_type == 2:
            file_name = f"{redecode_header}uncor_{uncor_type}_H_{REFC_CONFIG.matrix_sel}_CH_{REFC_CONFIG.ch_type}_E{REFC_CONFIG.num_fixed_errs[ch_idx]}_init_n_{REFC_CONFIG.init_n}_{process_idx}.{extension}"
        elif REFC_CONFIG.ch_type == 3:
            file_name = f"{redecode_header}uncor_{uncor_type}_H_{REFC_CONFIG.matrix_sel}_CH_{REFC_CONFIG.ch_type}_E{REFC_CONFIG.num_fixed_errs[ch_idx]}_SC_{REFC_CONFIG.fixed_SCRs[ch_idx]:.2f}_SE_{REFC_CONFIG.fixed_SERs[ch_idx]:.2f}_init_n_{REFC_CONFIG.init_n}_{process_idx}.{extension}"
        return file_name

    def Gather_And_Archive_Uncors(self, matrix: LLR_MATRIX, ch_idx: int = 0, is_uncor_type_seed: bool = False, is_redecoded_uncor: bool = False, test_mode: TestMode = TestMode.FULL):
        """각 프로세스의 uncor seed를 병합하고 그 uncor를 만든 LLR 매트릭스와 함께 아카이빙한다.

        모든 프로세스의 uncor seed 파일을 하나로 병합하고, 병합 결과 폴더에 matrix 파일도
        저장하여 재현 가능한 아카이브를 생성한다. 폴더 이름은 matrix의 파일 이름을 따른다.

        Args:
            matrix (LLR_MATRIX): 이 uncor를 만든 테스트 대상 매트릭스.
            ch_idx (int): 채널 인덱스. 기본값 0.
            is_uncor_type_seed (bool): uncor 타입이 seed인지 여부. 기본값 False.
            is_redecoded_uncor (bool): 재디코딩된 uncor인지 여부. 기본값 False.
            test_mode (TestMode): TestMode.FULL 또는 TestMode.PARTIAL. Two-stage 모드에서 사용.

        Returns:
            Optional[pathlib.Path]: 병합 결과 파일 경로. root 프로세스만 반환, 나머지는 None.
        """
        if not self.is_root:
            return
        # Output 경로 결정 (Partial만 서브디렉토리, Full은 루트)
        LLR_matrix_file_name = matrix.Get_LLR_Matrix_File_Name()
        dest_dir = Path(self.session_uncor_dir) / "Redecoded_uncors" / LLR_matrix_file_name
        if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST and test_mode == TestMode.PARTIAL:
            dest_dir = dest_dir / "Partial"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file_name = self.Get_Uncor_File_Name(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, is_redecoded_uncor=False)
        dest_path = dest_dir / dest_file_name

        if dest_path.exists():
            dest_path.unlink()

        last_src_path = None  # 마지막으로 처리한 src_path 추적
        with dest_path.open("a", encoding="utf-8") as dest_file:
            for proc in range(self.num_process):
                # 제외된 코어는 건너뜀 (uncor 파일 미생성)
                if proc in self.excluded_cores:
                    continue

                src_dir = self.Get_Local_Session_Dir(proc)
                src_file_name = self.Get_Uncor_File_Name(process_idx=proc, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, is_redecoded_uncor=is_redecoded_uncor)
                src_path = Path(src_dir) / src_file_name
                if not src_path.exists():
                    continue

                with src_path.open("r", encoding="utf-8") as src_file:
                    content = src_file.read().strip()  # 앞뒤 공백/개행 제거
                    if not content:
                        continue

                # 개행 보장 후 append
                dest_file.write(content)
                if not content.endswith("\n"):
                    dest_file.write("\n")
                dest_file.flush()
                last_src_path = src_path

        self.total_num_uncors[ch_idx] = self.Count_Gathered_Uncors(file_path=dest_path)
        src_name = last_src_path.name if last_src_path else "(no source)"
        self.Write_Log_Lines(f"[Input Uncor Seeds Copied]: total_num_uncors[ch_idx]: {self.total_num_uncors[ch_idx]}\n\t{src_name} → {dest_path}.")

        # uncor를 만든 matrix를 dest_dir에 함께 저장
        self.Save_LLR_Matrix(matrix, target_dir=str(dest_dir))
        self.Write_Log_Lines(f"[LLR Matrix Archived]: {dest_dir / LLR_matrix_file_name}")

        return dest_path
    
    def Get_Local_Session_Dir(self, process_idx:int):
        """프로세스별 로컬 세션 디렉터리를 반환한다.

        Args:
            process_idx (int): 프로세스 인덱스.

        Returns:
            str: 로컬 세션 디렉터리 경로.
        """
        return os.path.join(self.session_dir, PATH_CONFIG.LOCAL_SESSION_DIR_NAME_TEMPLATE.format(process_idx=process_idx))
        
    def Initialize_Run_ECC_End_Flag(self):
        """Run ECC 종료 플래그 파일을 초기화한다.
        """
        PATH_CONFIG.RUN_ECC_END_FLAG_FILE_PATH = os.path.join(self.end_flag_dir, RUN_ECC_END_FLAG_FILE_NAME)
        if self.is_root:
            self._Write_End_Flag(PATH_CONFIG.RUN_ECC_END_FLAG_FILE_PATH, False)
            # 지난 채널 테스트의 ack 파일을 비워 이번 테스트의 응답만 센다 (호출처는 배리어 사이라 안전)
            ack_dir = os.path.join(self.end_flag_dir, "run_ecc_ack")
            if os.path.isdir(ack_dir):
                for fname in os.listdir(ack_dir):
                    try:
                        os.remove(os.path.join(ack_dir, fname))
                    except OSError as e:
                        self.Write_Log_Lines(f"[WARN] ack 파일 삭제 실패: {fname}: {e}")

    def Initialize_End_Flags(self):
        """Trial/DAO 종료 플래그 파일을 초기화한다. (세션 시작 시 1회)
        """
        PATH_CONFIG.TRIAL_END_FLAG_FILE_PATH = os.path.join(self.end_flag_dir, TRIAL_END_FLAG_FILE_NAME)
        PATH_CONFIG.DAO_END_FLAG_FILE_PATH = os.path.join(self.end_flag_dir, DAO_END_FLAG_FILE_NAME)
        if self.is_root:
            self._Write_End_Flag(PATH_CONFIG.TRIAL_END_FLAG_FILE_PATH, False)
            self._Write_End_Flag(PATH_CONFIG.DAO_END_FLAG_FILE_PATH, False)

    def Get_Log_File_Name(self, create_time: datetime.datetime, start_idx: int, end_idx: Optional[int] = None, has_update: bool = False) -> str:
        """로그 파일명을 생성한다.

        Args:
            create_time: 로그 파일 생성 시간
            start_idx: 시작 LLR matrix idx
            end_idx: 종료 LLR matrix idx (None이면 진행 중)
            has_update: 해당 로그 구간에서 optimal update가 있었는지 여부

        Returns:
            str: 로그 파일명 (예: 2026.02.15__15.20.30___LLR_MATRIX_from_0_to_150_updated.txt)
        """
        time_str = create_time.strftime("%Y.%m.%d__%H.%M.%S")
        updated_suffix = "_updated" if has_update else ""
        if end_idx is None:
            return f"{time_str}___LLR_MATRIX_from_{start_idx}.txt"
        else:
            return f"{time_str}___LLR_MATRIX_from_{start_idx}_to_{end_idx}{updated_suffix}.txt"

    def Initialize_Log(self):
        """로그 파일을 초기화한다.

        루트 프로세스에서 세션 로그 경로를 준비하고 기본 실행 정보를 기록한다.

        Args:
            없음.

        Returns:
            None

        Raises:
            RuntimeError: 로그 디렉터리가 초기화되지 않은 상태에서 호출된 경우.
        """
        if not self.is_root:
            self.log_file_path = ""
            return
        if self.session_logs_dir == "":
            error_msg = "Initialize_Log: Session logs directory is not initialized."
            self.MPI_Abort(error_msg)

        # 로그 파일 생성 시간 및 시작 matrix idx 저장
        self.log_line_count = 0
        self.log_has_update = False
        self.log_create_time = datetime.datetime.now()
        self.log_start_matrix_idx = DAO_CONFIG.Get_Initial_Matrix_Idx_List()[0]

        # 파일명 형식: 2026.02.15__15.20.30___LLR_MATRIX_from_0.txt
        log_file_name = self.Get_Log_File_Name(self.log_create_time, self.log_start_matrix_idx)
        self.log_file_path = os.path.join(self.session_logs_dir, log_file_name)

        if DEBUG_CONFIG.ENABLE_UPDATE_LOG:
            self.update_log_file_path = os.path.join(
                self.session_logs_dir, f"update_logs_{self.session_timestamp}.txt"
            )
        else:
            self.update_log_file_path = ""
    
        if self.log_file_path is None:
            return

        self.start_time_str = (
            self.simulation_start.strftime("%Y-%m-%d %H:%M:%S")
            if self.simulation_start
            else ""
        )

    def Initialize_Stage(self, stage_idx: int):
        """최적화 단계를 초기화한다.

        단계 인덱스를 갱신하고 trial 생성 모드와 로그 출력을 준비한다.

        Args:
            stage_idx (int): 시작할 단계 인덱스.

        Returns:
            None
        """
        self.MPI_Barrier()
        self.Check_Barrier_Sync(f"Stage {stage_idx} start")
        self.current_stage_idx = stage_idx
        self.temp_optimal_LLR_matrix = None

        # Stage 시작 시 target_group_indices 재설정 (optimal_LLR_matrix 기준, 규칙은 Build_Target_Group_Indices)
        # - Restart group 포함 (조건에 따라 skip)
        if self.optimal_LLR_matrix is not None:
            self.target_group_indices = self.Build_Target_Group_Indices(self.optimal_LLR_matrix)
            target_source = "FIXED_TARGET_GROUP_IDX_LIST" if DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST is not None else "INITIAL_TARGET_GROUP_IDX"
            self.Write_Log_Lines(f"\t- Updated target_group_indices: {self.target_group_indices} (from optimal_LLR_matrix and {target_source})")

        # 모드와 타겟 그룹은 갱신된 target_group_indices 위에서 정한다
        self.Set_Gen_Trial_LLR_Mode()

        # current_target_idx 계산 (이전 값 기준으로 +1, 모듈로 연산)
        if not hasattr(self, 'current_target_idx') or self.current_target_idx is None:
            self.current_target_idx = 0
        else:
            self.current_target_idx = (self.current_target_idx + 1) % len(self.target_group_indices)

        # SKIP_RESTART_GROUP 모드에서 restart group이면 다음으로 skip (연속된 restart도 처리)
        if self.optimal_LLR_matrix is not None and self.current_gen_trial_LLR_mode in SKIP_RESTART_GROUP:
            skip_count = 0
            max_skip = len(self.target_group_indices)  # 무한 루프 방지
            while skip_count < max_skip:
                group_idx = self.target_group_indices[self.current_target_idx]
                group = self.optimal_LLR_matrix.groups[group_idx]
                if group and len(group) > 0 and group[0].is_group_restart:
                    self.Write_Log_Lines(f"\t- Skipping restart group g{group_idx}")
                    self.current_target_idx = (self.current_target_idx + 1) % len(self.target_group_indices)
                    skip_count += 1
                else:
                    break  # 비-restart group 발견

        self.Write_Log_Lines(f"\t- Current target index: {self.current_target_idx} (g{self.target_group_indices[self.current_target_idx]})")

        # 모드별 상태 초기화 및 설정 (target_group_indices 설정 이후, 공용)
        init_func_name = MULTI_ROUND_INIT_FUNC.get(self.current_gen_trial_LLR_mode) if self.current_gen_trial_LLR_mode is not None else None
        if init_func_name:
            getattr(self, init_func_name)()

        # Multi-round 모드: stage 시간 제한 비활성화 (공용)
        if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
            self.is_current_stage_enable_max_stage_time_limit = False
        else:
            self.is_current_stage_enable_max_stage_time_limit = TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS < 100*60*60

        self.Set_Update_Flags()
        self.Print_Stage_Info()

    def Initialize_LLR_Matrix(self):
        """초기 LLR 매트릭스를 준비한다.

        루트 프로세스에서 초기 매트릭스를 로드하거나 생성하고 모든 프로세스에 배포한 뒤 저장·검증을 수행한다.

        Args:
            없음.

        Returns:
            None
        """
        if self.is_root:
            self.Load_Initial_LLR_Matrix()

        self.initial_LLR_matrix = self._safe_bcast(self.initial_LLR_matrix if self.is_root else None, "Bcast_initial_LLR_matrix")

        self.target_group_indices = self.Build_Target_Group_Indices(self.initial_LLR_matrix)

        self.Update_Current_LLR(self.initial_LLR_matrix)
        self.Print_LLR_Matrix(self.current_LLR_matrix)
        self.Save_LLR_Matrix(self.current_LLR_matrix, target_dir=self.trial_output_dir)
        # Speed test를 위해 local_session_dir에도 저장 (각 프로세스가 독립적으로 사용)
        self.Save_LLR_Matrix(self.current_LLR_matrix, target_dir=self.local_session_dir, save_root_only=False)
        self.Validate_LLR_Matrix()
        if not self.is_current_LLR_valid:
            self.MPI_Abort("Initial LLR matrix validation failed.")

    def Initialize_Trial(self, trial_idx: int) -> None:
        self.MPI_Barrier()
        self.Check_Barrier_Sync(f"Stage {self.current_stage_idx}, Trial {trial_idx} start")
        self.current_trial_idx = trial_idx
        self.current_LLR_matrix_idx += 1

        self.Write_Log_Separator(
            f"Stage: {self.current_stage_idx} / {DAO_CONFIG.MAX_OPTIMIZATION_STAGE}, Trial: {self.current_trial_idx} / {self.max_modification_trial}, Matrix idx: {self.current_LLR_matrix_idx} ",
            SEPARATOR_TYPE1
            )
        self.Print_Mode_Target_Info()

        # Random state 로깅 (디버깅 재현용) - base64 인코딩으로 압축
        rng_state = random.getstate()
        state_bytes = pickle.dumps(rng_state)
        state_b64 = base64.b64encode(state_bytes).decode("ascii")
        self.Write_Log_Lines(f"[Random state (base64)]: {state_b64}")

    def Insert_Random_Row(self, matrix, row_idx: int, group_idx: int = -1):
        """
        타겟 group의 row_idx 위치에 새로운 random row를 삽입.
        타겟 그룹은 group_idx로 결정됩니다 (-1이면 마지막 그룹).
        - matrix 값은 header의 max/min 범위 기반 랜덤 생성
        - CSW는 위치 규칙에 따라 결정
        - iter_start, iter_end, floor_flag는 기존 row와 동일하게 복사
        - num_row_each_group 값은 자동 업데이트
        """

        if not matrix.groups:
            error_msg = "Insert_Random_Row: Matrix must contain at least one group."
            return None, error_msg

        if group_idx == -1:
            group_idx = len(matrix.groups) - 1

        target_group = matrix.groups[group_idx]
        num_rows = len(target_group)

        if num_rows == 0:
            error_msg = f"Insert_Random_Row: Target group must not be empty. numrows: {num_rows}"
            return None, error_msg

        if row_idx > num_rows:
            msg = f"Error 6: row idx:{row_idx}, cannot be greater than num_rows:{num_rows}"
            return None, msg

        CSWs = [row.CSW for row in target_group]

        # 기존 행들의 기본 속성 복사
        iter_start = target_group[0].iter_start
        iter_end = target_group[0].iter_end
        floor_flag = target_group[0].floor_flag

        # matrix 랜덤 생성
        row_values = self._generate_random_row(matrix, iter_end=iter_end)

        # 새로운 CSW 결정
        if row_idx == 0:
            if num_rows >= 2:
                if CSWs[1] == MAX_CSW:
                    return None, f"Error 0: Current CSWs[1]:{CSWs[1]} is MAX_CSW: {MAX_CSW}"
            # 새로 추가되는 row(0번째)는 항상 -1
            new_CSW = -1

        elif row_idx == 1:
            if num_rows == 1:
                min_possible_CSW = MIN_CSW
            else:
                min_possible_CSW = CSWs[row_idx] + STEP_CSW
                if min_possible_CSW > MAX_CSW:
                    return None, f"Error 1-1: min_possible_CSW:{min_possible_CSW} should not be greater than MAX_CSW:{MAX_CSW}"
            max_possible_CSW = MAX_CSW
            new_CSW, msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_CSW is None:
                return None, f"Error 1-2: {msg}"

        elif row_idx == num_rows:
            prev_CSW = CSWs[-1]
            min_possible_CSW = MIN_CSW
            max_possible_CSW = prev_CSW - STEP_CSW
            if max_possible_CSW < MIN_CSW:
                return None, f"Error 2-1: max_possible_CSW:{max_possible_CSW} should not be smaller than MIN_CSW:{MIN_CSW}"
            
            new_CSW, msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_CSW is None:
                return None, f"Error 2-2: {msg}"
        
        else:
            prev_CSW = CSWs[row_idx - 1]
            next_csw = CSWs[row_idx]
            diff = prev_CSW - next_csw
            if diff < STEP_CSW:
                msg = f"Error 3-1: Difference between prev_csw:{prev_CSW} and next_csw:{next_csw} should be greater than or equal to STEP_CSW: {STEP_CSW}"
                return None, msg

            min_possible_CSW = next_csw + STEP_CSW
            max_possible_CSW = prev_CSW - STEP_CSW

            new_CSW, msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_CSW is None:
                return None, f"Error 3-2: {msg}"

        # 새 row 생성, 삽입
        new_row = LLR_Row(
            ch_th_values=row_values,
            CSW=new_CSW,
            iter_start=iter_start,
            iter_end=iter_end,
            floor_flag=floor_flag,
            is_group_restart=False
        )
        target_group.insert(row_idx, new_row)

        # 기존 첫 row의 CSW 갱신 (맨 앞 삽입 시에만)
        if row_idx == 0:
            old_csw = target_group[1].CSW
            if len(target_group) == 2:    # 원래 1개였다면 (삽입 후 2개)
                min_possible_CSW = MIN_CSW
            elif len(target_group) > 2:   # 원래 2개 이상인 경우 (삽입 후 3개 이상)
                min_possible_CSW = target_group[2].CSW + STEP_CSW
            max_possible_CSW = MAX_CSW

            new_first_CSW, msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_first_CSW is None:
                return None, f"Error 5-2: {msg}"

            target_group[1].CSW = new_first_CSW
        # header.num_row_each_group 업데이트 (항상 수행)
        matrix.header.num_row_each_group[group_idx] += 1
        return matrix, None

    def Is_Current_LLR_Valid(self):
        """현재 생성된 LLR 매트릭스의 유효성을 확인한다.

        생성 성공 여부를 확인하고 필요한 경우 검증을 수행한 뒤 결과를 로그에 남긴다.

        Args:
            없음.

        Returns:
            bool: 매트릭스가 유효하면 True, 그렇지 않으면 False.
        """
        if self.generate_LLR_success:
            self.Validate_LLR_Matrix()
        else:
            self.is_current_LLR_valid = False

        if self.is_current_LLR_valid:
            return True
        else:
            if self.generate_LLR_success:
                self.Write_Log_Lines(f"[Gen_Trial_LLR failed] Matrix idx: {self.current_LLR_matrix_idx} — 검증 실패 (상세는 위 로그 참조)")
            else:
                self.Write_Log_Lines(f"[Gen_Trial_LLR failed] Matrix idx: {self.current_LLR_matrix_idx} — 생성 실패 (generate_LLR_success=False)")
            return False

    def Is_List_A_Strictly_Better(self, A: list, B: list) -> bool:
        """
        Return True if:
        - For all i: A[i] <= B[i]
        - And at least one i: A[i] < B[i]
        Otherwise return False.
        """
        if len(A) != len(B):
            error_msg = f"Is_List_A_Strictly_Better: A and B must have the same length.A: {len(A)}, B: {len(B)}"
            self.MPI_Abort(error_msg)

        le_all = all(a <= b for a, b in zip(A, B))
        lt_one = any(a < b for a, b in zip(A, B))

        return le_all and lt_one

    def Is_Matrix_Better(self, matrix_A: Optional[LLR_MATRIX], matrix_B: Optional[LLR_MATRIX]) -> bool:
        """
        matrix_A가 matrix_B보다 나은지 판단한다.

        1. FER이 strictly better이면 True
        2. FER이 모든 채널에서 같으면 avg iteration을 비교 (낮을수록 좋음)
        3. 그 외 False

        Args:
            matrix_A: 비교 대상 매트릭스 A
            matrix_B: 비교 기준 매트릭스 B

        Returns:
            bool: matrix_A가 matrix_B보다 나으면 True
        """
        # None 체크
        if matrix_A is None or matrix_B is None:
            return False

        # 1. FER strictly better 확인
        if self.Is_List_A_Strictly_Better(matrix_A.FERs, matrix_B.FERs):
            return True

        # 2. FER이 모든 채널에서 같고, avg_iteration 업데이트가 활성화된 경우
        if DAO_CONFIG.ENABLE_AVG_ITER_UPDATE:
            if all(abs(a - b) < 1e-15 for a, b in zip(matrix_A.FERs, matrix_B.FERs)):
                # avg iteration 비교 (낮을수록 좋음). 미테스트 채널(-1.0)은 가장 나쁜 값으로 본다
                avg_A = [float("inf") if avg < 0 else avg for avg in matrix_A.avg_iterations]
                avg_B = [float("inf") if avg < 0 else avg for avg in matrix_B.avg_iterations]
                return self.Is_List_A_Strictly_Better(avg_A, avg_B)

        # 3. FER이 더 나쁨 (또는 avg_iteration 업데이트 비활성화)
        return False

    def Log_Unhandled_Exception(self, exc: BaseException) -> None:
        """
        처리되지 않은 예외를 Error_Log 디렉터리에 기록한다.
        """
        error_dir = None
        if getattr(self, "session_dir", None):
            error_dir = os.path.join(self.session_dir, ERROR_LOG_DIR_NAME)

        try:
            state_text = self._collect_error_state_snapshot()
        except Exception as error:
            state_text = f"<state collection failed: {error!r}>"
        _write_error_log(self.rank, exc, state_text, error_dir=error_dir)

    def Load_Initial_LLR_Matrix(self):
        """초기 LLR 매트릭스를 파일에서 읽어온다.

        설정된 인덱스를 기반으로 입력 디렉터리의 매트릭스 파일을 로드하고 로그를 남긴다.

        Args:
            없음.

        Returns:
            None

        Raises:
            SystemExit: 파일을 로드하지 못했을 때.
        """
        input_path = os.path.join(
            PATH_CONFIG.INPUT_LLR_MATRIX_DIR_PATH,
            f"LLR_MATRIX_{self._current_initial_matrix_idx}.txt",
        )
        self.Write_Log_Lines(f"[Load initial matrix from] {input_path}")
        try:
            self.initial_LLR_matrix = LLR_MATRIX(init_n=REFC_CONFIG.init_n, matrix_idx=self._current_initial_matrix_idx, is_HBF_OPT=DAO_CONFIG.IS_HBF_OPT)
        except (FileNotFoundError, ValueError, IndexError) as error:
            self.MPI_Abort(f"Initial LLR matrix load failed: input_path={input_path}, error={error}")

    def Gen_LLR_Insert_Random_Group(self, input_matrix: Optional[LLR_MATRIX]):
        """
        current_target_group_idx로 지정된 그룹의 바로 뒤에 random 값으로 새 그룹을 삽입하고, 필요하면 restart 그룹도 함께 추가한다.
        current_target_group_idx = -1: 마지막 그룹 뒤에 삽입
        current_target_group_idx >= 0: 해당 그룹 뒤에 삽입
        """
        num_rows = INSERT_RANDOM_GROUP_CONFIG.INSERT_GROUP_NUM_ROWS

        if input_matrix is None:
            error_msg = "Gen_LLR_Insert_Random_Group: Matrix must not be None."
            self.MPI_Abort(error_msg)
        if num_rows <= 0:
            error_msg = f"Gen_LLR_Insert_Random_Group: num_rows must be positive. num_rows: {num_rows}"
            self.MPI_Abort(error_msg)
        if not input_matrix.groups:
            error_msg = "Gen_LLR_Insert_Random_Group: Matrix must contain at least one existing group."
            self.MPI_Abort(error_msg)

        # 1. 삽입 위치 결정
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            insert_position = len(input_matrix.groups)  # 마지막 뒤
            reference_group_idx = len(input_matrix.groups) - 1
        else:
            if target_group_idx >= len(input_matrix.groups):
                error_msg = f"Gen_LLR_Insert_Random_Group: target_group_idx {target_group_idx} out of range (num_groups: {len(input_matrix.groups)})"
                self.MPI_Abort(error_msg)
            insert_position = target_group_idx + 1  # 해당 그룹 뒤
            reference_group_idx = target_group_idx

        reference_group = input_matrix.groups[reference_group_idx]
        if not reference_group:
            error_msg = f"Gen_LLR_Insert_Random_Group: Reference group at index {reference_group_idx} must not be empty."
            self.MPI_Abort(error_msg)

        ref_iter_end = reference_group[-1].iter_end
        floor_flag = reference_group[0].floor_flag
        header = input_matrix.header
        len_row = header.num_parameter_each_set * header.num_dv

        # 2. 그룹 생성 (RESTART + 일반 그룹)
        groups_to_insert: list[tuple[list[LLR_Row], bool]] = []
        next_iter_start = ref_iter_end + 1

        self.insert_group_add_restart = False
        if INSERT_RANDOM_GROUP_CONFIG.ENABLE_INSERT_RESTART:
            if self.current_trial_idx > (self.max_modification_trial / 2):
                self.insert_group_add_restart = True

        if self.insert_group_add_restart:
            restart_values = np.full(len_row, -1, dtype=np.int32)
            restart_row = LLR_Row(
                ch_th_values=restart_values,
                CSW=-1,
                iter_start=next_iter_start,
                iter_end=next_iter_start,
                floor_flag=floor_flag,
                is_group_restart=True,
            )
            groups_to_insert.append(([restart_row], True))
            next_iter_start = restart_row.iter_end + 1

        csw_values: list[int] = [-1]
        if num_rows > 1:
            candidate_csw = np.arange(MIN_CSW, MAX_CSW + STEP_CSW, STEP_CSW, dtype=int)
            if candidate_csw.size < num_rows - 1:
                error_msg = f"Error A2: Not enough CSW candidates between MIN_CSW {MIN_CSW} "
                error_msg += f"and MAX_CSW {MAX_CSW} to fill {num_rows - 1} rows."
                self.Write_Log_Lines("[Insert_Group_LLR_Matrix failed]")
                self.Write_Log_Lines(f"\t- {error_msg}")
                return None

            chosen = random.sample(candidate_csw.tolist(), num_rows - 1)
            chosen.sort(reverse=True)
            csw_values.extend(chosen)

        new_iter_start = next_iter_start
        new_iter_end = new_iter_start + INSERT_RANDOM_GROUP_CONFIG.INSERT_GROUP_NUM_ITERATION - 1

        new_group_rows: list[LLR_Row] = []
        for row_idx in range(num_rows):
            row_values = self._generate_random_row(input_matrix, iter_end=new_iter_end)
            csw_value = csw_values[row_idx]

            new_group_rows.append(
                LLR_Row(
                    ch_th_values=row_values,
                    CSW=csw_value,
                    iter_start=new_iter_start,
                    iter_end=new_iter_end,
                    floor_flag=floor_flag,
                    is_group_restart=False,
                )
            )

        groups_to_insert.append((new_group_rows, False))

        # 3. 뒷 그룹 Iteration 재계산 (핵심 차이점)
        total_inserted_iterations = 0
        for group_rows, is_restart in groups_to_insert:
            if is_restart:
                total_inserted_iterations += 1
            else:
                total_inserted_iterations += (group_rows[0].iter_end - group_rows[0].iter_start + 1)

        # 삽입 위치 이후의 모든 그룹의 iteration 증가
        for group_idx in range(insert_position, len(input_matrix.groups)):
            group = input_matrix.groups[group_idx]
            for row in group:
                row.iter_start += total_inserted_iterations
                row.iter_end += total_inserted_iterations

        # restart_iter 배열도 동일하게 업데이트
        for i in range(len(header.restart_iter)):
            if header.restart_iter[i] > ref_iter_end:
                header.restart_iter[i] += total_inserted_iterations

        # 4. 그룹 삽입 및 Header 업데이트
        num_groups_inserted = len(groups_to_insert)
        for offset, (group_rows, is_restart) in enumerate(groups_to_insert):
            actual_insert_position = insert_position + offset

            # 그룹 삽입 (append 대신 insert 사용)
            input_matrix.groups.insert(actual_insert_position, group_rows)

            # Header 업데이트 (concatenate 대신 insert 사용)
            header.num_group += 1
            header.num_row_each_group = np.insert(header.num_row_each_group, actual_insert_position, len(group_rows))
            header.type_each_group = np.insert(header.type_each_group, actual_insert_position, 1)

            # restart_iter 업데이트 (restart 그룹인 경우)
            if is_restart:
                restart_iter_value = group_rows[0].iter_start
                if restart_iter_value not in header.restart_iter:
                    header.restart_iter = np.append(header.restart_iter, np.array([restart_iter_value], dtype=np.int32))
                    header.restart_iter = np.sort(header.restart_iter)
                    header.num_restart = int(header.num_restart) + 1

        # 5. restart_groups 인덱스 보정
        adjusted_restart_groups = []
        for restart_idx in input_matrix.restart_groups:
            if restart_idx - 1 >= insert_position:  # 0-based 비교
                adjusted_restart_groups.append(restart_idx + num_groups_inserted)
            else:
                adjusted_restart_groups.append(restart_idx)

        # 새 restart 그룹 추가
        for offset, (_, is_restart) in enumerate(groups_to_insert):
            if is_restart:
                new_idx_1based = insert_position + offset + 1
                if new_idx_1based not in adjusted_restart_groups:
                    adjusted_restart_groups.append(new_idx_1based)

        input_matrix.restart_groups = sorted(adjusted_restart_groups)

        # 6. max_iteration 업데이트
        input_matrix.max_iteration = input_matrix.groups[-1][-1].iter_end

        # Print results
        output_matrix = input_matrix
        inserted_group = output_matrix.groups[insert_position + len(groups_to_insert) - 1]
        CSW_values = ", ".join(str(row.CSW) for row in inserted_group)
        log_lines = [
            f"\t- inserted group index (0-based/1-based): {insert_position + len(groups_to_insert) - 1}/{insert_position + len(groups_to_insert)}",
            f"\t- insert position after group (0-based): {reference_group_idx}",
            f"\t- rows: {len(inserted_group)}, iter_start: {inserted_group[0].iter_start}, iter_end: {inserted_group[0].iter_end}",
            f"\t- CSW: [{CSW_values}]",
            f"\t- total groups after insertion: {len(output_matrix.groups)}",
        ]

        # 삽입된 그룹의 각 row별 상세 정보 출력
        log_lines.append(f"\t- Inserted group detailed rows:")
        for row_idx, row in enumerate(inserted_group):
            ch_th_str = ", ".join(map(str, row.ch_th_values.tolist()))
            log_lines.append(f"\t  [Row {row_idx}] CSW: {row.CSW:4d}, Ch/Th: [{ch_th_str}]")

        if self.insert_group_add_restart:
            restart_group = output_matrix.groups[insert_position]
            restart_info = [
                f"\t- restart group index (0-based/1-based): {insert_position}/{insert_position + 1}, iter: {restart_group[0].iter_start}"
            ]
            log_lines.extend(restart_info)

        self.Write_Log_Lines(log_lines)

        # 7. target_group_indices 자동 업데이트
        # 삽입 위치 이후 인덱스 보정 (+num_groups_inserted)
        adjusted_indices = [
            idx + num_groups_inserted if idx >= insert_position else idx
            for idx in self.target_group_indices
        ]

        # 새로 삽입된 그룹 인덱스들을 맨 뒤에 추가
        # (일반 그룹만 추가, restart 그룹은 최적화 대상 아님)
        for offset, (_, is_restart) in enumerate(groups_to_insert):
            if not is_restart:
                new_group_idx = insert_position + offset
                adjusted_indices.append(new_group_idx)

        # 업데이트
        self.target_group_indices = adjusted_indices

        # 로깅
        self.Write_Log_Lines(f"\t- Updated target_group_indices: {adjusted_indices}")

        return input_matrix

    def Gen_LLR_Insert_Mutated_Group(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """기존 그룹을 복사 후 mutation을 적용하여 타겟 그룹 뒤에 삽입한다.

        INSERT_RANDOM_GROUP과 유사하지만, 랜덤 생성 대신 기존 그룹을 선택하여
        mutation(값 변이)을 적용한 뒤 삽입한다.

        Args:
            input_matrix (Optional[LLR_MATRIX]): 삽입 대상 매트릭스.

        Returns:
            Optional[LLR_MATRIX]: 삽입 성공 시 수정된 매트릭스, 실패 시 None.
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Insert_Mutated_Group: Matrix must not be None."
            self.MPI_Abort(error_msg)
        if not input_matrix.groups:
            error_msg = "Gen_LLR_Insert_Mutated_Group: Matrix must contain at least one existing group."
            self.MPI_Abort(error_msg)

        # 1. 삽입 위치 결정
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            insert_position = len(input_matrix.groups)
            reference_group_idx = len(input_matrix.groups) - 1
        else:
            if target_group_idx >= len(input_matrix.groups):
                error_msg = f"Gen_LLR_Insert_Mutated_Group: target_group_idx {target_group_idx} out of range (num_groups: {len(input_matrix.groups)})"
                self.MPI_Abort(error_msg)
            insert_position = target_group_idx + 1
            reference_group_idx = target_group_idx

        reference_group = input_matrix.groups[reference_group_idx]
        if not reference_group:
            error_msg = f"Gen_LLR_Insert_Mutated_Group: Reference group at index {reference_group_idx} must not be empty."
            self.MPI_Abort(error_msg)

        ref_iter_end = reference_group[-1].iter_end
        floor_flag = reference_group[0].floor_flag
        header = input_matrix.header

        # 2. 복사할 소스 그룹 랜덤 선택 (restart 그룹 제외)
        non_restart_group_indices = [
            idx for idx in range(len(input_matrix.groups))
            if idx + 1 not in input_matrix.restart_groups  # restart_groups는 1-based
        ]
        if not non_restart_group_indices:
            self.Write_Log_Lines("\t- No non-restart groups available to copy.")
            return None

        source_group_idx = random.choice(non_restart_group_indices)
        source_group = input_matrix.groups[source_group_idx]
        num_rows = len(source_group)

        self.Write_Log_Lines(f"\t- Source group index (0-based): {source_group_idx}, num_rows: {num_rows}")

        # 3. 그룹 생성 (RESTART + mutated 그룹)
        groups_to_insert: list[tuple[list[LLR_Row], bool]] = []
        next_iter_start = ref_iter_end + 1

        self.insert_group_add_restart = False
        if INSERT_MUTATED_GROUP_CONFIG.ENABLE_INSERT_RESTART:
            if self.current_trial_idx > (self.max_modification_trial / 2):
                self.insert_group_add_restart = True

        len_row = header.num_parameter_each_set * header.num_dv

        # 3-1. Iteration 동적 계산 (MAX_DECODING_ITERATION 제약 적용)
        requested_iteration = INSERT_MUTATED_GROUP_CONFIG.INSERT_GROUP_NUM_ITERATION
        restart_overhead = 1 if self.insert_group_add_restart else 0  # restart 그룹은 iteration 1 사용

        current_max_iter = input_matrix.max_iteration
        remaining_iter = REFC_CONFIG.MAX_DECODING_ITERATION - current_max_iter - restart_overhead

        # 십시일반 로직: INITIAL_TARGET_GROUP_IDX부터 끝까지 그룹에서 빌려오기
        borrowed_iteration = 0
        donor_adjustments: list[tuple[int, int]] = []  # [(group_idx, delta), ...]

        if remaining_iter >= requested_iteration:
            # Case 1: 충분한 공간 있음 - 설정대로 사용
            actual_iteration = requested_iteration
            self.Write_Log_Lines(f"\t- Iteration: {actual_iteration} (sufficient space, remaining: {remaining_iter})")
        elif remaining_iter > 0:
            # Case 2: 부족하지만 공간 있음 - 남은 만큼만 사용
            actual_iteration = remaining_iter
            self.Write_Log_Lines(f"\t- Iteration: {actual_iteration} (limited by MAX_DECODING_ITERATION, requested: {requested_iteration})")
        else:
            # Case 3: 꽉 차있음 - 십시일반 (INITIAL_TARGET_GROUP_IDX부터 끝까지에서 빌려오기)
            needed_iteration = requested_iteration - remaining_iter  # remaining_iter <= 0이므로 양수
            self.Write_Log_Lines(f"\t- Iteration borrowing needed: {needed_iteration} (current_max: {current_max_iter}, limit: {REFC_CONFIG.MAX_DECODING_ITERATION})")

            # INITIAL_TARGET_GROUP_IDX부터 끝까지, restart 제외한 그룹에서 빌려오기
            donor_group_indices = [
                idx for idx in range(DAO_CONFIG.INITIAL_TARGET_GROUP_IDX, len(input_matrix.groups))
                if idx + 1 not in input_matrix.restart_groups  # restart_groups는 1-based
            ]

            if not donor_group_indices:
                self.Write_Log_Lines("\t- No donor groups available for borrowing iteration.")
                return None

            # 각 donor에서 빌릴 양 계산 (균등 분배 후 부족분 추가 차용)
            iter_per_donor = max(1, needed_iteration // len(donor_group_indices))
            remaining_to_borrow = needed_iteration

            # 각 donor의 현재 iteration과 이미 빌린 양 추적
            donor_borrowed: dict[int, int] = {idx: 0 for idx in donor_group_indices}

            # 1차 패스: 균등 분배
            for donor_idx in donor_group_indices:
                donor_group = input_matrix.groups[donor_idx]
                if not donor_group:
                    continue
                donor_iter = donor_group[0].iter_end - donor_group[0].iter_start + 1

                # 최소 1 iteration은 남겨야 함
                max_borrowable = donor_iter - 1
                if max_borrowable <= 0:
                    continue

                borrow_amount = min(iter_per_donor, max_borrowable, remaining_to_borrow)
                if borrow_amount > 0:
                    donor_borrowed[donor_idx] = borrow_amount
                    borrowed_iteration += borrow_amount
                    remaining_to_borrow -= borrow_amount
                    self.Write_Log_Lines(f"\t  - Borrowing {borrow_amount} from g{donor_idx} (had {donor_iter})")

                if remaining_to_borrow <= 0:
                    break

            # 2차 패스: 부족분을 상위 10% iteration 보유 donor에서 추가 차용
            if remaining_to_borrow > 0:
                # donor들을 남은 iteration 기준 내림차순 정렬
                donor_remaining_iter: list[tuple[int, int]] = []
                for donor_idx in donor_group_indices:
                    donor_group = input_matrix.groups[donor_idx]
                    if not donor_group:
                        continue
                    donor_iter = donor_group[0].iter_end - donor_group[0].iter_start + 1
                    already_borrowed = donor_borrowed[donor_idx]
                    remaining = donor_iter - 1 - already_borrowed  # 추가로 빌릴 수 있는 양
                    if remaining > 0:
                        donor_remaining_iter.append((donor_idx, remaining))

                # 남은 iteration 기준 내림차순 정렬 후 상위 10% 선택 (최소 1개)
                donor_remaining_iter.sort(key=lambda x: x[1], reverse=True)
                top_donor_count = max(1, len(donor_remaining_iter) // 10)
                top_donors = donor_remaining_iter[:top_donor_count]

                self.Write_Log_Lines(f"\t  - 2nd pass: top {top_donor_count} donors from {len(donor_remaining_iter)}")

                for donor_idx, available in top_donors:
                    additional_borrow = min(available, remaining_to_borrow)
                    if additional_borrow > 0:
                        donor_borrowed[donor_idx] += additional_borrow
                        borrowed_iteration += additional_borrow
                        remaining_to_borrow -= additional_borrow
                        self.Write_Log_Lines(f"\t  - Additional borrowing {additional_borrow} from g{donor_idx}")

                    if remaining_to_borrow <= 0:
                        break

            # donor_adjustments 생성 (실제 빌린 양 기준)
            for donor_idx, amount in donor_borrowed.items():
                if amount > 0:
                    donor_adjustments.append((donor_idx, -amount))

            if borrowed_iteration == 0:
                self.Write_Log_Lines("\t- Failed to borrow any iteration from donors.")
                return None

            # 빌린 양에서 적자(remaining_iter는 음수 또는 0)를 상쇄하여 실제 사용 가능한 iteration 계산
            # 예: remaining_iter=-10, borrowed=60 → actual=50 (10은 적자 복구, 50은 신규 그룹용)
            actual_iteration = min(requested_iteration, borrowed_iteration + remaining_iter)
            if actual_iteration <= 0:
                self.Write_Log_Lines(f"\t- Insufficient borrowed iteration after deficit compensation (borrowed: {borrowed_iteration}, deficit: {-remaining_iter})")
                return None
            self.Write_Log_Lines(f"\t- Total borrowed: {borrowed_iteration}, deficit compensation: {-remaining_iter}, actual iteration: {actual_iteration}")

        # 3-2. Donor 그룹 iteration 조정 (십시일반 적용 시)
        if donor_adjustments:
            for donor_idx, delta in donor_adjustments:
                donor_group = input_matrix.groups[donor_idx]
                old_iter_end = donor_group[0].iter_end
                new_iter_end_donor = old_iter_end + delta  # delta는 음수
                for row in donor_group:
                    row.iter_end = new_iter_end_donor

            # 뒷 그룹들의 iteration 재계산 필요
            # donor 그룹 이후의 모든 그룹 iter_start/end를 순차적으로 재조정
            self._recalculate_group_iterations(input_matrix)
            # 재계산 후 ref_iter_end 업데이트
            ref_iter_end = input_matrix.groups[reference_group_idx][-1].iter_end

        # 3-3. Restart 그룹 추가 (필요 시)
        next_iter_start = ref_iter_end + 1

        if self.insert_group_add_restart:
            restart_values = np.full(len_row, -1, dtype=np.int32)
            restart_row = LLR_Row(
                ch_th_values=restart_values,
                CSW=-1,
                iter_start=next_iter_start,
                iter_end=next_iter_start,
                floor_flag=floor_flag,
                is_group_restart=True,
            )
            groups_to_insert.append(([restart_row], True))
            next_iter_start = restart_row.iter_end + 1

        new_iter_start = next_iter_start
        new_iter_end = new_iter_start + actual_iteration - 1

        # 4. 소스 그룹 복사 후 mutation 적용
        new_group_rows: list[LLR_Row] = []
        for row_idx, source_row in enumerate(source_group):
            # row 값 복사 (새 그룹이 HD 복호의 HBF 구간에 들어가면 dv_idx 0의 TH는 상수)
            new_ch_th_values = source_row.ch_th_values.copy()
            input_matrix.Fill_Columns_Fixed_In_HBF_Iterations(new_ch_th_values, new_iter_end)

            # CSW 유지 (첫 번째 row는 -1, 나머지는 원본 CSW)
            if row_idx == 0:
                new_csw = -1
            else:
                new_csw = source_row.CSW

            new_group_rows.append(
                LLR_Row(
                    ch_th_values=new_ch_th_values,
                    CSW=new_csw,
                    iter_start=new_iter_start,
                    iter_end=new_iter_end,
                    floor_flag=floor_flag,
                    is_group_restart=False,
                )
            )

        # 5. Mutation 적용 (새 그룹에 대해)
        mutations = self._generate_mutation_for_group(
            input_matrix,
            new_group_rows,
            num_elements=INSERT_MUTATED_GROUP_CONFIG.NUM_ELEMENTS_TO_MUTATE_CHTH,
            mutation_range=INSERT_MUTATED_GROUP_CONFIG.MUTATION_RANGE,
            allow_zero=INSERT_MUTATED_GROUP_CONFIG.ALLOW_ZERO_MUTATION
        )

        if mutations:
            for row_idx, col_idx, old_value, new_value in mutations:
                new_group_rows[row_idx].ch_th_values[col_idx] = new_value
                delta = new_value - old_value
                self.Write_Log_Lines(f"\t- Mutation: row {row_idx}, col {col_idx}: {old_value} -> {new_value} ({delta:+d})")
        else:
            self.Write_Log_Lines("\t- No mutations applied (copied as-is).")

        groups_to_insert.append((new_group_rows, False))

        # 6. 뒷 그룹 Iteration 재계산
        total_inserted_iterations = 0
        for group_rows, is_restart in groups_to_insert:
            if is_restart:
                total_inserted_iterations += 1
            else:
                total_inserted_iterations += (group_rows[0].iter_end - group_rows[0].iter_start + 1)

        for group_idx in range(insert_position, len(input_matrix.groups)):
            group = input_matrix.groups[group_idx]
            for row in group:
                row.iter_start += total_inserted_iterations
                row.iter_end += total_inserted_iterations

        for i in range(len(header.restart_iter)):
            if header.restart_iter[i] > ref_iter_end:
                header.restart_iter[i] += total_inserted_iterations

        # 7. 그룹 삽입 및 Header 업데이트
        num_groups_inserted = len(groups_to_insert)
        for offset, (group_rows, is_restart) in enumerate(groups_to_insert):
            actual_insert_position = insert_position + offset
            input_matrix.groups.insert(actual_insert_position, group_rows)

            header.num_group += 1
            header.num_row_each_group = np.insert(header.num_row_each_group, actual_insert_position, len(group_rows))
            header.type_each_group = np.insert(header.type_each_group, actual_insert_position, 1)

            if is_restart:
                restart_iter_value = group_rows[0].iter_start
                if restart_iter_value not in header.restart_iter:
                    header.restart_iter = np.append(header.restart_iter, np.array([restart_iter_value], dtype=np.int32))
                    header.restart_iter = np.sort(header.restart_iter)
                    header.num_restart = int(header.num_restart) + 1

        # 8. restart_groups 인덱스 보정
        adjusted_restart_groups = []
        for restart_idx in input_matrix.restart_groups:
            if restart_idx - 1 >= insert_position:
                adjusted_restart_groups.append(restart_idx + num_groups_inserted)
            else:
                adjusted_restart_groups.append(restart_idx)

        for offset, (_, is_restart) in enumerate(groups_to_insert):
            if is_restart:
                new_idx_1based = insert_position + offset + 1
                if new_idx_1based not in adjusted_restart_groups:
                    adjusted_restart_groups.append(new_idx_1based)

        input_matrix.restart_groups = sorted(adjusted_restart_groups)

        # 9. max_iteration 업데이트
        input_matrix.max_iteration = input_matrix.groups[-1][-1].iter_end

        # Print results
        output_matrix = input_matrix
        inserted_group = output_matrix.groups[insert_position + len(groups_to_insert) - 1]
        CSW_values = ", ".join(str(row.CSW) for row in inserted_group)
        log_lines = [
            f"\t- inserted group index (0-based/1-based): {insert_position + len(groups_to_insert) - 1}/{insert_position + len(groups_to_insert)}",
            f"\t- insert position after group (0-based): {reference_group_idx}",
            f"\t- rows: {len(inserted_group)}, iter_start: {inserted_group[0].iter_start}, iter_end: {inserted_group[0].iter_end}",
            f"\t- CSW: [{CSW_values}]",
            f"\t- total groups after insertion: {len(output_matrix.groups)}",
        ]
        self.Write_Log_Lines(log_lines)

        if self.insert_group_add_restart:
            restart_group = output_matrix.groups[insert_position]
            restart_info = [
                f"\t- restart group index (0-based/1-based): {insert_position}/{insert_position + 1}, iter: {restart_group[0].iter_start}"
            ]
            log_lines.extend(restart_info)
            self.Write_Log_Lines(restart_info)

        # 10. target_group_indices 자동 업데이트
        adjusted_indices = [
            idx + num_groups_inserted if idx >= insert_position else idx
            for idx in self.target_group_indices
        ]

        for offset, (_, is_restart) in enumerate(groups_to_insert):
            if not is_restart:
                new_group_idx = insert_position + offset
                adjusted_indices.append(new_group_idx)

        self.target_group_indices = adjusted_indices
        self.Write_Log_Lines(f"\t- Updated target_group_indices: {adjusted_indices}")

        return input_matrix

    def Gen_LLR_Insert_Mutated_Row(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """기존 row를 복사 후 mutation을 적용하여 타겟 그룹에 삽입한다.

        INSERT_RANDOM_ROW와 유사하지만, 랜덤 생성 대신 기존 row를 선택하여
        mutation(값 변이)을 적용한 뒤 삽입한다.

        Args:
            input_matrix (Optional[LLR_MATRIX]): 삽입 대상 매트릭스.

        Returns:
            Optional[LLR_MATRIX]: 삽입 성공 시 수정된 매트릭스, 실패 시 None.
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Insert_Mutated_Row: Matrix must not be None."
            self.MPI_Abort(error_msg)

        # 타겟 그룹 결정
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(input_matrix.groups) - 1

        target_group = input_matrix.groups[target_group_idx]
        if not target_group:
            self.Write_Log_Lines(f"\t- Target group {target_group_idx} is empty.")
            return None

        # 삽입 위치 결정
        row_idx = (self.current_trial_idx - 1) % (len(target_group) + 1)

        # 복사할 소스 row 랜덤 선택 (전체 그룹에서, restart 그룹 제외)
        candidate_rows: list[tuple[int, int, LLR_Row]] = []  # (group_idx, row_idx, row)
        for g_idx in range(len(input_matrix.groups)):
            if g_idx + 1 in input_matrix.restart_groups:  # restart_groups는 1-based
                continue
            for r_idx, row in enumerate(input_matrix.groups[g_idx]):
                candidate_rows.append((g_idx, r_idx, row))

        if not candidate_rows:
            self.Write_Log_Lines("\t- No candidate rows available to copy.")
            return None

        source_group_idx, source_row_idx, source_row = random.choice(candidate_rows)

        self.Write_Log_Lines(f"\t- Target group: {target_group_idx}, insert at row: {row_idx}, source: g{source_group_idx}/r{source_row_idx}")

        # 새 row 생성 (소스 row 복사. 타겟 그룹이 HD 복호의 HBF 구간이면 dv_idx 0의 TH는 상수)
        target_iter_end = target_group[0].iter_end
        new_ch_th_values = source_row.ch_th_values.copy()
        input_matrix.Fill_Columns_Fixed_In_HBF_Iterations(new_ch_th_values, target_iter_end)

        # Mutation 적용
        mutations = self._generate_mutation_for_row(
            new_ch_th_values,
            fixed_columns=input_matrix.Get_Columns_Fixed_In_HBF_Iterations(target_iter_end),
            num_elements=INSERT_MUTATED_ROW_CONFIG.NUM_ELEMENTS_TO_MUTATE_CHTH,
            mutation_range=INSERT_MUTATED_ROW_CONFIG.MUTATION_RANGE,
            allow_zero=INSERT_MUTATED_ROW_CONFIG.ALLOW_ZERO_MUTATION
        )

        if mutations:
            for col_idx, old_value, new_value in mutations:
                new_ch_th_values[col_idx] = new_value
                delta = new_value - old_value
                self.Write_Log_Lines(f"\t- Mutation: col {col_idx}: {old_value} -> {new_value} ({delta:+d})")
        else:
            self.Write_Log_Lines("\t- No mutations applied (copied as-is).")

        # CSW 결정 (Insert_Random_Row 로직과 동일)
        num_rows = len(target_group)
        CSWs = [row.CSW for row in target_group]

        if row_idx == 0:
            if num_rows >= 2:
                if CSWs[1] == MAX_CSW:
                    self.Write_Log_Lines(f"[Insert_Mutated_Row failed] Current CSWs[1]:{CSWs[1]} is MAX_CSW: {MAX_CSW}")
                    return None
            new_csw = -1

        elif row_idx == 1:
            if num_rows == 1:
                min_possible_CSW = MIN_CSW
            else:
                min_possible_CSW = CSWs[row_idx] + STEP_CSW
                if min_possible_CSW > MAX_CSW:
                    self.Write_Log_Lines(f"[Insert_Mutated_Row failed] min_possible_CSW:{min_possible_CSW} > MAX_CSW:{MAX_CSW}")
                    return None
            max_possible_CSW = MAX_CSW
            new_csw, error_msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_csw is None:
                self.Write_Log_Lines(f"[Insert_Mutated_Row failed] {error_msg}")
                return None

        elif row_idx == num_rows:
            prev_CSW = CSWs[-1]
            min_possible_CSW = MIN_CSW
            max_possible_CSW = prev_CSW - STEP_CSW
            if max_possible_CSW < MIN_CSW:
                self.Write_Log_Lines(f"[Insert_Mutated_Row failed] max_possible_CSW:{max_possible_CSW} < MIN_CSW:{MIN_CSW}")
                return None
            new_csw, error_msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_csw is None:
                self.Write_Log_Lines(f"[Insert_Mutated_Row failed] {error_msg}")
                return None

        else:
            prev_CSW = CSWs[row_idx - 1]
            next_csw = CSWs[row_idx]
            diff = prev_CSW - next_csw
            if diff < STEP_CSW:
                self.Write_Log_Lines(f"[Insert_Mutated_Row failed] Diff between prev_csw:{prev_CSW} and next_csw:{next_csw} < STEP_CSW:{STEP_CSW}")
                return None
            min_possible_CSW = next_csw + STEP_CSW
            max_possible_CSW = prev_CSW - STEP_CSW
            new_csw, error_msg = self._get_new_CSW(min_possible_CSW, max_possible_CSW)
            if new_csw is None:
                self.Write_Log_Lines(f"[Insert_Mutated_Row failed] {error_msg}")
                return None

        # 새 row 생성
        new_row = LLR_Row(
            ch_th_values=new_ch_th_values,
            CSW=new_csw,
            iter_start=target_group[0].iter_start,
            iter_end=target_group[0].iter_end,
            floor_flag=target_group[0].floor_flag,
            is_group_restart=False,
        )

        # row 삽입
        if row_idx == 0:
            # 첫 번째 위치에 삽입 시 기존 첫 row의 CSW 재할당
            old_first_row = target_group[0]
            if num_rows == 1:
                reassign_min = MIN_CSW
            else:
                reassign_min = CSWs[1] + STEP_CSW if num_rows >= 2 else MIN_CSW
            reassign_max = MAX_CSW
            reassigned_csw, err = self._get_new_CSW(reassign_min, reassign_max)
            if reassigned_csw is None:
                self.Write_Log_Lines(f"[Insert_Mutated_Row failed] Cannot reassign CSW: {err}")
                return None
            old_first_row.CSW = reassigned_csw

        target_group.insert(row_idx, new_row)
        input_matrix.header.num_row_each_group[target_group_idx] += 1

        # 결과 출력
        row_values = ", ".join(map(str, new_row.ch_th_values.tolist()))
        self.Write_Log_Lines([
            f"\t- Ch, Th: [{row_values}]",
            f"\t- CSW: {new_row.CSW}, iter_start: {new_row.iter_start}, iter_end: {new_row.iter_end}",
        ])

        return input_matrix

    def _recalculate_group_iterations(self, matrix: LLR_MATRIX) -> None:
        """모든 그룹의 iteration을 순차적으로 재계산한다.

        각 그룹의 iter_range(iter_end - iter_start + 1)를 보존하면서,
        iter_start와 iter_end를 이전 그룹의 iter_end + 1부터 연속 배치한다.
        단, 각 그룹 내의 모든 row는 동일한 iter_start, iter_end를 가져야 함.

        Args:
            matrix: 재계산할 LLR_MATRIX
        """
        current_iter = 1
        for group in matrix.groups:
            if not group:
                continue

            # 그룹의 iteration 범위 계산
            group_iter_range = group[0].iter_end - group[0].iter_start + 1

            new_iter_start = current_iter
            new_iter_end = current_iter + group_iter_range - 1

            # 그룹 내 모든 row 업데이트
            for row in group:
                row.iter_start = new_iter_start
                row.iter_end = new_iter_end

            current_iter = new_iter_end + 1

        # max_iteration 업데이트
        if matrix.groups and matrix.groups[-1]:
            matrix.max_iteration = matrix.groups[-1][-1].iter_end

        # restart_iter 배열도 업데이트
        new_restart_iter = []
        for group in matrix.groups:
            if group and group[0].is_group_restart:
                new_restart_iter.append(group[0].iter_start)
        matrix.header.restart_iter = np.array(new_restart_iter, dtype=np.int32)

    def Gen_LLR_Split_Group(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """타겟 그룹의 iteration을 분할하여 front/back 두 그룹을 생성한다.

        타겟 그룹의 iteration 범위를 SPLIT_RATIO에 따라 front/back으로 분할하고,
        back 그룹의 ch_th_values에 mutation을 적용한다.
        총 iteration은 변화 없음.

        Args:
            input_matrix: 분할 대상 매트릭스

        Returns:
            분할 성공 시 수정된 매트릭스, 실패 시 None
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Split_Group: Matrix must not be None."
            self.MPI_Abort(error_msg)

        # 1. 타겟 그룹 결정
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(input_matrix.groups) - 1

        if target_group_idx >= len(input_matrix.groups):
            error_msg = f"Gen_LLR_Split_Group: target_group_idx {target_group_idx} out of range (num_groups: {len(input_matrix.groups)})"
            self.MPI_Abort(error_msg)

        target_group = input_matrix.groups[target_group_idx]
        if not target_group:
            self.Write_Log_Lines(f"\t- Target group g{target_group_idx} is empty.")
            return None

        if target_group[0].is_group_restart:
            self.Write_Log_Lines(f"\t- Target group g{target_group_idx} is a restart group, cannot split.")
            return None

        # 2. Iteration 분할 계산
        original_iter_start = target_group[0].iter_start
        original_iter_end = target_group[0].iter_end
        total_iterations = original_iter_end - original_iter_start + 1

        if total_iterations < 2:
            self.Write_Log_Lines(f"\t- Target group g{target_group_idx} has only {total_iterations} iteration(s), cannot split.")
            return None

        split_ratio = SPLIT_GROUP_CONFIG.SPLIT_RATIO
        front_iterations = max(1, round(total_iterations * split_ratio))
        front_iterations = min(front_iterations, total_iterations - 1)
        back_iterations = total_iterations - front_iterations

        front_iter_start = original_iter_start
        front_iter_end = front_iter_start + front_iterations - 1
        back_iter_start = front_iter_end + 1
        back_iter_end = back_iter_start + back_iterations - 1

        self.Write_Log_Lines(f"\t- Splitting g{target_group_idx}: total_iter={total_iterations}, "
                             f"front={front_iterations} [{front_iter_start}-{front_iter_end}], "
                             f"back={back_iterations} [{back_iter_start}-{back_iter_end}]")

        # 3. Front 그룹 생성 (원본 복사)
        header = input_matrix.header
        floor_flag = target_group[0].floor_flag

        front_group_rows: list[LLR_Row] = []
        for row in target_group:
            front_group_rows.append(LLR_Row(
                ch_th_values=row.ch_th_values.copy(),
                CSW=row.CSW,
                iter_start=front_iter_start,
                iter_end=front_iter_end,
                floor_flag=floor_flag,
                is_group_restart=False,
            ))

        # 4. Back 그룹 생성 (복사 후 mutation)
        back_group_rows: list[LLR_Row] = []
        for row in target_group:
            back_group_rows.append(LLR_Row(
                ch_th_values=row.ch_th_values.copy(),
                CSW=row.CSW,
                iter_start=back_iter_start,
                iter_end=back_iter_end,
                floor_flag=floor_flag,
                is_group_restart=False,
            ))

        mutations = self._generate_mutation_for_group(
            input_matrix,
            back_group_rows,
            num_elements=SPLIT_GROUP_CONFIG.NUM_ELEMENTS_TO_MUTATE_CHTH,
            mutation_range=SPLIT_GROUP_CONFIG.MUTATION_RANGE,
            allow_zero=SPLIT_GROUP_CONFIG.ALLOW_ZERO_MUTATION,
        )

        if mutations:
            for row_idx, col_idx, old_value, new_value in mutations:
                back_group_rows[row_idx].ch_th_values[col_idx] = new_value
                delta = new_value - old_value
                self.Write_Log_Lines(f"\t- Back mutation: row {row_idx}, col {col_idx}: {old_value} -> {new_value} ({delta:+d})")
        else:
            self.Write_Log_Lines("\t- No mutations applied to back group (identical to front).")

        # 5. 그룹 교체/삽입
        input_matrix.groups[target_group_idx] = front_group_rows
        insert_position = target_group_idx + 1
        input_matrix.groups.insert(insert_position, back_group_rows)

        # 6. Header 업데이트
        header.num_group += 1
        header.num_row_each_group = np.insert(
            header.num_row_each_group, insert_position, len(back_group_rows)
        )
        original_type = header.type_each_group[target_group_idx]
        header.type_each_group = np.insert(
            header.type_each_group, insert_position, original_type
        )

        # 7. restart_groups 인덱스 보정 (1-based)
        adjusted_restart_groups = []
        for restart_idx in input_matrix.restart_groups:
            if restart_idx - 1 >= insert_position:
                adjusted_restart_groups.append(restart_idx + 1)
            else:
                adjusted_restart_groups.append(restart_idx)
        input_matrix.restart_groups = sorted(adjusted_restart_groups)

        # 8. max_iteration 검증 (총 iteration 불변)
        input_matrix.max_iteration = input_matrix.groups[-1][-1].iter_end

        # 9. target_group_indices 보정
        adjusted_indices = [
            idx + 1 if idx >= insert_position else idx
            for idx in self.target_group_indices
        ]
        adjusted_indices.append(insert_position)
        self.target_group_indices = adjusted_indices

        # 10. 로그 출력
        self.Write_Log_Lines([
            f"\t- Front group: g{target_group_idx}, rows: {len(front_group_rows)}, iter: [{front_iter_start}-{front_iter_end}]",
            f"\t- Back group: g{insert_position}, rows: {len(back_group_rows)}, iter: [{back_iter_start}-{back_iter_end}]",
            f"\t- Total groups after split: {len(input_matrix.groups)}",
            f"\t- Updated target_group_indices: {self.target_group_indices}",
        ])

        return input_matrix

    def _generate_mutation_for_group(
        self,
        matrix: LLR_MATRIX,
        group_rows: list[LLR_Row],
        num_elements: int,
        mutation_range: int,
        allow_zero: bool = True
    ) -> list[tuple[int, int, int, int]]:
        """그룹 내 row들에 대한 mutation을 생성한다.

        HD 복호의 HBF 구간 row는 dv_idx 0의 TH를 변이 후보에서 뺀다 (LLR_MATRIX.Get_Columns_Fixed_In_HBF_Iterations).

        Args:
            matrix: group_rows가 들어갈 매트릭스 (값이 고정되는 column을 묻는 데 쓴다)
            group_rows: mutation 대상 row 리스트
            num_elements: 변이할 최대 요소 수
            mutation_range: 변이 범위 (-range ~ +range)
            allow_zero: True면 mutation 개수 0 허용 (빈 리스트 반환 가능)

        Returns:
            list[tuple[int, int, int, int]]: (row_idx, col_idx, old_value, new_value) 리스트
        """
        if mutation_range == 0:
            return []

        element_pool = []
        for row_idx, row in enumerate(group_rows):
            fixed_columns = matrix.Get_Columns_Fixed_In_HBF_Iterations(row.iter_end)
            for col_idx in range(len(row.ch_th_values)):
                if col_idx in fixed_columns:
                    continue
                element_pool.append((row_idx, col_idx))

        if not element_pool:
            return []

        # allow_zero=True면 0~num_elements 중 랜덤 선택, False면 1~num_elements
        if allow_zero:
            actual_num = random.randint(0, min(num_elements, len(element_pool)))
        else:
            actual_num = random.randint(1, min(num_elements, len(element_pool)))

        if actual_num == 0:
            return []

        chosen = random.sample(element_pool, actual_num)

        mutations: list[tuple[int, int, int, int]] = []
        for row_idx, col_idx in chosen:
            delta = random.randint(-mutation_range, mutation_range)
            if delta == 0:
                delta = random.choice([-1, 1])  # 0이면 방향 랜덤 선택
            old_value = int(group_rows[row_idx].ch_th_values[col_idx])
            new_value = old_value + delta
            mutations.append((row_idx, col_idx, old_value, new_value))

        return mutations

    def _generate_mutation_for_row(
        self,
        ch_th_values: np.ndarray,
        fixed_columns: list[int],
        num_elements: int,
        mutation_range: int,
        allow_zero: bool = True
    ) -> list[tuple[int, int, int]]:
        """단일 row에 대한 mutation을 생성한다.

        Args:
            ch_th_values: mutation 대상 값 배열
            fixed_columns: 변이 후보에서 빼는 column (LLR_MATRIX.Get_Columns_Fixed_In_HBF_Iterations의 결과)
            num_elements: 변이할 최대 요소 수
            mutation_range: 변이 범위 (-range ~ +range)
            allow_zero: True면 mutation 개수 0 허용 (빈 리스트 반환 가능)

        Returns:
            list[tuple[int, int, int]]: (col_idx, old_value, new_value) 리스트
        """
        if mutation_range == 0:
            return []

        col_indices = [col_idx for col_idx in range(len(ch_th_values)) if col_idx not in fixed_columns]
        if not col_indices:
            return []

        # allow_zero=True면 0~num_elements 중 랜덤 선택, False면 1~num_elements
        if allow_zero:
            actual_num = random.randint(0, min(num_elements, len(col_indices)))
        else:
            actual_num = random.randint(1, min(num_elements, len(col_indices)))

        if actual_num == 0:
            return []

        chosen = random.sample(col_indices, actual_num)

        mutations: list[tuple[int, int, int]] = []
        for col_idx in chosen:
            delta = random.randint(-mutation_range, mutation_range)
            if delta == 0:
                delta = random.choice([-1, 1])
            old_value = int(ch_th_values[col_idx])
            new_value = old_value + delta
            mutations.append((col_idx, old_value, new_value))

        return mutations

    def _Replace_With_Single_Group(self, matrix, rows: list, iteration: int):
        """매트릭스의 모든 그룹을 단일 그룹으로 교체하고 header를 업데이트한다."""
        matrix.groups = [rows]
        matrix.restart_groups = []
        header = matrix.header
        header.num_group = 1
        header.num_row_each_group = np.array([len(rows)], dtype=np.int32)
        header.type_each_group = np.array([1], dtype=np.int32)
        header.restart_iter = np.array([], dtype=np.int32)
        header.num_restart = 0
        matrix.max_iteration = iteration

    def Gen_LLR_Gen_Initial_Group(self, input_matrix: Optional[LLR_MATRIX]):
        """
        GenInitialGroupConfig를 활용하여 새로운 초기 그룹을 생성하고, 
        기존 매트릭스의 모든 그룹을 대체하여 LLR 매트릭스를 반환한다.
        새 그룹은 iter_start=1부터 시작한다.
        """
        num_rows = GEN_INITIAL_GROUP_CONFIG.NUM_ROWS
        iteration = GEN_INITIAL_GROUP_CONFIG.ITERATION

        if input_matrix is None:
            error_msg = "Gen_LLR_Gen_Initial_Group: Matrix must not be None."
            self.MPI_Abort(error_msg)
        if num_rows <= 0:
            error_msg = f"Gen_LLR_Gen_Initial_Group: num_rows must be positive. num_rows: {num_rows}"
            self.MPI_Abort(error_msg)
        if iteration <= 0:
            error_msg = f"Gen_LLR_Gen_Initial_Group: iteration must be positive. iteration: {iteration}"
            self.MPI_Abort(error_msg)
        
        # 1. 새 그룹에 사용할 CSW 값 생성 및 정렬
        csw_values: list[int] = [-1]
        if num_rows > 1:
            candidate_csw = np.arange(MIN_CSW, MAX_CSW + STEP_CSW, STEP_CSW, dtype=int)
            if candidate_csw.size < num_rows - 1:
                error_msg = f"Error G2: Not enough CSW candidates between MIN_CSW {MIN_CSW} and MAX_CSW {MAX_CSW} to fill {num_rows - 1} rows."
                self.Write_Log_Lines("[Gen_LLR_Gen_Initial_Group failed]")
                self.Write_Log_Lines(f"\t- {error_msg}")
                return None
            
            chosen = random.sample(candidate_csw.tolist(), num_rows - 1)
            chosen.sort(reverse=True)
            csw_values.extend(chosen)
        
        new_iter_start = 1
        new_iter_end = new_iter_start + iteration - 1
        # floor_flag는 기존 매트릭스에서 가져옴
        floor_flag = input_matrix.groups[0][0].floor_flag if (input_matrix.groups and input_matrix.groups[0]) else 0 
        
        # 2. 새 그룹 행 생성
        new_group_rows: list[LLR_Row] = []
        for row_idx in range(num_rows):
            # 행 값은 초기 매트릭스 기준으로 랜덤 생성
            row_values = self.Generate_Initial_Random_Row() 
            csw_value = csw_values[row_idx]

            new_group_rows.append(
                LLR_Row(
                    ch_th_values=row_values,
                    CSW=csw_value,
                    iter_start=new_iter_start,
                    iter_end=new_iter_end,
                    floor_flag=floor_flag,
                    is_group_restart=False,
                )
            )

        # 3. 기존 그룹 제거 → 새 단일 그룹으로 교체
        self._Replace_With_Single_Group(input_matrix, new_group_rows, new_iter_end)
        
        # 새로운 그룹 정보를 로그 출력
        output_matrix = input_matrix
        newly_added_group = output_matrix.groups[0]
        CSW_values = ", ".join(str(row.CSW) for row in newly_added_group)
        log_lines = [
            f"\t- All previous groups removed. New single initial group (index 0) created.",
            f"\t- rows: {len(newly_added_group)}, iter_start: {newly_added_group[0].iter_start}, iter_end: {newly_added_group[0].iter_end}",
            f"\t- CSW: [{CSW_values}]",
            f"\t- Header num_group set to 1, num_row_each_group set to {len(newly_added_group)}."
        ]
        self.Write_Log_Lines(log_lines)
        
        return input_matrix
    
    def Gen_LLR_Insert_Random_Row(self, input_matrix: Optional[LLR_MATRIX]):
        """타겟 그룹에 random 행을 삽입한다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).

        현재 trial index 기준으로 행 위치를 결정하고 랜덤 행을 추가한 뒤 요약을 기록한다.

        Args:
            input_matrix (Optional[LLR_MATRIX]): 행을 삽입할 매트릭스.

        Returns:
            Optional[LLR_MATRIX]: 삽입 성공 시 매트릭스, 실패 시 None.
        """

        # Set_Gen_Trial_LLR_Mode에서 계산된 target_group_idx 사용
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(input_matrix.groups) - 1

        row_idx = (self.current_trial_idx - 1) % (input_matrix.header.num_row_each_group[target_group_idx]+1)
        self.Write_Log_Lines(f"\t- target group: {target_group_idx}, target row index: {row_idx}")

        output_matrix, error_msg = self.Insert_Random_Row(matrix=input_matrix, row_idx=row_idx, group_idx=target_group_idx)

        if output_matrix is None:
            self.Write_Log_Lines(f"[Insert_Row_LLR_Matrix failed]")
            self.Write_Log_Lines(f"\t- {error_msg}")
            return None

        if not output_matrix.groups:
            self.Write_Log_Lines(f"[Insert_Row_LLR_Matrix failed]")
            self.Write_Log_Lines(f"\t- Matrix must contain at least one group after insertion.")
            return None

        target_group = output_matrix.groups[target_group_idx]
        inserted_index = min(row_idx, len(target_group) - 1)
        inserted_row = target_group[inserted_index]
        row_values = ", ".join(map(str, inserted_row.ch_th_values.tolist()))
        self.Write_Log_Lines(
            [
                f"\t- Ch, Th: [{row_values}]",
                f"\t- CSW: {inserted_row.CSW}, iter_start: {inserted_row.iter_start}, iter_end: {inserted_row.iter_end}, floor_flag: {inserted_row.floor_flag}",
            ]
        )

        return output_matrix

    def Gen_LLR_Mutate_CSW(self, input_matrix: Optional[LLR_MATRIX]) -> LLR_MATRIX:
        """LLR 매트릭스 마지막 그룹의 CSW를 변화시킨다.

        지정된 매트릭스의 마지막 그룹을 수정하고 변경 사항을 로그로 출력한다.

        Args:
            input_matrix (Optional[LLR_MATRIX]): 변이 대상 매트릭스.

        Returns:
            LLR_MATRIX: CSW상 변이가 적용된 동일 객체.

        Raises:
            ValueError: 입력 매트릭스가 None인 경우.
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Mutate_CSW: Source matrix must not be None."
            self.MPI_Abort(error_msg)

        modifications = self.Mutate_CSW(matrix=input_matrix)

        if modifications:
            for group_idx, row_idx, old_csw, new_csw in modifications:
                delta = new_csw - old_csw
                if delta != 0:
                    self.Write_Log_Lines(f"\t- group {group_idx} row {row_idx}: {old_csw} -> {new_csw} ({delta:+d})")
        else:
            self.Write_Log_Lines("\t- No mutations were applied.")

        return input_matrix

    def Gen_LLR_Mutate_Matrix(self, input_matrix: Optional[LLR_MATRIX]) -> LLR_MATRIX:
        """LLR 매트릭스의 Ch, Th를 변화시킨다.

        HD_HBF mode라면 전 영역에 걸쳐 수정하며, 그밖이라면 마지막 그룹의 Ch, Th를 변화시킨다.

        지정된 매트릭스의 마지막 그룹을 수정하고 변경 사항을 로그로 출력한다.

        Args:
            input_matrix (Optional[LLR_MATRIX]): 변이 대상 매트릭스.

        Returns:
            LLR_MATRIX: Ch, Th 변이가 적용된 동일 객체.

        Raises:
            ValueError: 입력 매트릭스가 None인 경우.
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Mutate_Matrix: Source matrix must not be None."
            self.MPI_Abort(error_msg)

        if self.current_trial_idx == 1:
            # 초기화
            self.is_mutate_matrix_tuning_phase = False
            self.tuning_mutation_count = 0

        elif self.is_mutate_matrix_tuning_phase:
            # 튜닝 모드 진행 중
            self.tuning_mutation_count += 1
            if self.tuning_mutation_count > self.max_possible_tuning_mutation_count:
                # 모든 튜닝 완료 → 일반 모드 복귀
                self.is_mutate_matrix_tuning_phase = False
                self.tuning_mutation_count = 0

        else:
            # 일반 모드
            if self.is_previous_trial_updated:
                # 이전 trial 성공 → 튜닝 모드 진입
                self.is_mutate_matrix_tuning_phase = True
                self.tuning_mutation_count = 1
                if MUTATE_CONFIG.ENABLE_FINE_TUNING_AFTER_UPDATE:
                    self.tuning_mutations = self.Generate_All_Fine_Tuning_Mutations(self.prev_generated_mutation)
                else:
                    self.tuning_mutations = self.Generate_All_Coarse_Tuning_Mutations(self.prev_generated_mutation)
                self.max_possible_tuning_mutation_count = len(self.tuning_mutations)
                if self.max_possible_tuning_mutation_count == 0:
                    # 튜닝할 mutation이 없으면 일반 모드 유지
                    self.is_mutate_matrix_tuning_phase = False
                    self.tuning_mutation_count = 0

        if self.is_mutate_matrix_tuning_phase:
            tuning_type = "Fine" if MUTATE_CONFIG.ENABLE_FINE_TUNING_AFTER_UPDATE else "Coarse"
            self.Write_Log_Lines(f"\t- {tuning_type}-tuning mutation phase [{self.tuning_mutation_count}/{self.max_possible_tuning_mutation_count}].")
            current_mutation = self.tuning_mutations[self.tuning_mutation_count - 1]
        else:
            self.Mutate_Matrix_Setup()
            current_mutation = self.Generate_Random_Mutation(matrix=input_matrix)
            if current_mutation:
                self.prev_generated_mutation = current_mutation

        if current_mutation:
            for group_idx, row_idx, col_idx, old_value, new_value in current_mutation:
                row = input_matrix.groups[group_idx][row_idx]
                row.ch_th_values[col_idx] = new_value
                delta = new_value - old_value
                if delta != 0:
                    self.Write_Log_Lines(f"\t- group {group_idx} row {row_idx}, column {col_idx}: {old_value} -> {new_value} ({delta:+d})")
        else:
            self.Write_Log_Lines("\t- No mutations were applied to the last group.")

        return input_matrix

    def Generate_All_Fine_Tuning_Mutations(
        self,
        modifications: list[tuple[int, int, int, int, int]]
    ) -> list[list[tuple[int, int, int, int, int]]]:
        """
        기존 modifications 기반으로 가능한 모든 조합 mutation을 생성한다.
        예: [(g,r,c,5,8), (g,r,c,10,8)] → Δ(+3, -2)
        => (1,0),(2,0),(3,0),(0,-1),(0,-2),(1,-1),(1,-2),(2,-1),(2,-2),(3,-1),(3,-2)
        
        반환형:
            list of list
            각 element은 하나의 modification case set
            [
                [(g,r,c, old, new_case_value), (g2,r2,c2, old2, new_case_value2)], ...
            ]
        """

        if not modifications:
            return []

        deltas = []  # 각 mutation에서 가능한 delta step 집합 저장
        base_values = []

        for (group_idx, row_idx, col_idx, old_value, new_value) in modifications:
            delta = new_value - old_value

            # delta 방향에 따라 step 가능한 범위 생성
            step_range = range(1, abs(delta) + 1)
            if delta < 0:
                step_range = (-s for s in step_range)

            deltas.append(list(step_range))
            base_values.append((group_idx, row_idx, col_idx, old_value))

        all_cases = []

        # 모든 조합 생성
        for delta_combo in itertools.product(*deltas):
            case_mods = []
            for i, d in enumerate(delta_combo):
                group_idx, row_idx, col_idx, old_value = base_values[i]
                new_case_value = old_value + d
                case_mods.append((group_idx, row_idx, col_idx, old_value, new_case_value))
            all_cases.append(case_mods)

        return all_cases

    def Generate_All_Coarse_Tuning_Mutations(
        self,
        modifications: list[tuple[int, int, int, int, int]]
    ) -> list[list[tuple[int, int, int, int, int]]]:
        """
        기존 modifications에서 불필요한 mutation을 제거하기 위해
        전체를 제외한 모든 부분집합을 생성한다.

        예: [1, 2, 3] → [1], [2], [3], [1,2], [1,3], [2,3]
        (전체 [1,2,3]은 이미 테스트되었으므로 제외)

        선택되지 않은 mutation은 old_value로 롤백하여 포함한다.
        예: 원본 [(g,r,c1,10,11), (g,r,c2,20,22), (g,r,c3,30,33)]
            [1]만 선택 → [(g,r,c1,10,11), (g,r,c2,20,20), (g,r,c3,30,30)]

        Args:
            modifications: 원본 mutation 리스트 [(group_idx, row_idx, col_idx, old_value, new_value), ...]

        Returns:
            전체를 제외한 모든 부분집합 리스트 (선택되지 않은 항목은 old_value로 롤백)
        """
        if not modifications:
            return []

        n = len(modifications)
        all_subsets = []

        # 크기 1부터 n-1까지의 모든 부분집합 생성 (전체 집합 제외)
        for r in range(1, n):
            for subset in itertools.combinations(range(n), r):
                # subset은 선택된 인덱스들
                selected_indices = set(subset)
                case = []
                for i, (group_idx, row_idx, col_idx, old_value, new_value) in enumerate(modifications):
                    if i in selected_indices:
                        # 선택된 mutation: new_value 적용
                        case.append((group_idx, row_idx, col_idx, old_value, new_value))
                    else:
                        # 선택되지 않은 mutation: old_value로 롤백
                        case.append((group_idx, row_idx, col_idx, old_value, old_value))
                all_subsets.append(case)

        return all_subsets

    def Gen_LLR_Regen_DV(self, input_matrix: LLR_MATRIX) -> LLR_MATRIX:
        """
        LLR 매트릭스의 타겟 그룹에 대해, 행과 DV를 순차적으로 선택하여
        선택된 DV의 CH/TH 쌍 전체를 랜덤한 값으로 대체합니다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).

        Args:
            matrix (LLR_MATRIX): 수정 대상 매트릭스 객체 (수정 후 이 객체가 반환됨)

        Returns:
            LLR_MATRIX: DV 교체 변이가 적용된 동일 객체.
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Regen_DV: Source matrix must not be None."
            self.MPI_Abort(error_msg)

        h = input_matrix.header

        # Set_Gen_Trial_LLR_Mode에서 계산된 target_group_idx 사용
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(input_matrix.groups) - 1

        target_group = input_matrix.groups[target_group_idx]

        modifications: list[tuple[int, int, int, int, int]] = []

        if not target_group:
            self.Write_Log_Lines("\t- No rows in the target group for DV replacement.")
            return input_matrix

        num_rows_in_target_group = len(target_group)
        num_dv = h.num_dv
        num_params = h.num_parameter_each_set

        # ENABLE_FIX_IDX 처리하여 row_indices와 dv_indices 먼저 결정
        if REGEN_DV_CONFIG.ENABLE_FIX_IDX:
            # FIXED_ROW_IDX 처리
            if isinstance(REGEN_DV_CONFIG.FIXED_ROW_IDX, list):
                row_indices = REGEN_DV_CONFIG.FIXED_ROW_IDX
            elif REGEN_DV_CONFIG.FIXED_ROW_IDX != -1:
                row_indices = [REGEN_DV_CONFIG.FIXED_ROW_IDX]
            else:
                row_indices = list(range(num_rows_in_target_group))

            # FIXED_DV_IDX 처리
            if isinstance(REGEN_DV_CONFIG.FIXED_DV_IDX, list):
                dv_indices = REGEN_DV_CONFIG.FIXED_DV_IDX
            elif REGEN_DV_CONFIG.FIXED_DV_IDX != -1:
                dv_indices = [REGEN_DV_CONFIG.FIXED_DV_IDX]
            else:
                dv_indices = list(range(num_dv))
        else:
            row_indices = list(range(num_rows_in_target_group))
            dv_indices = list(range(num_dv))

        num_row_dv_pairs = len(row_indices) * len(dv_indices)

        if num_row_dv_pairs == 0:
            self.Write_Log_Lines("\t- No valid row/DV pairs available for REGEN_DV")
            return None

        # 현재 모드 결정 (이번 trial에서 사용할 모드)
        last_trial_reuse_mode = self.is_replace_DV_in_Ch_Th_reuse_mode

        if self.current_trial_idx == 1:
            self.previous_dv_segment = np.array([], dtype=np.int32)
            self.gen_DV_idx = 0
            current_trial_reuse_mode = False
        elif last_trial_reuse_mode:
            if self.gen_DV_idx < (num_row_dv_pairs - 1):
                # 다음 위치로 이동
                self.gen_DV_idx += 1
                current_trial_reuse_mode = True
            elif self.gen_DV_idx == (num_row_dv_pairs - 1):
                # 재사용 모드 종료
                self.gen_DV_idx = 0
                current_trial_reuse_mode = False
        else:
            if self.is_previous_trial_updated:
                self.gen_DV_idx = 0
                current_trial_reuse_mode = True
            else:
                self.gen_DV_idx = (self.gen_DV_idx + 1) % num_row_dv_pairs
                current_trial_reuse_mode = False

        self.is_replace_DV_in_Ch_Th_reuse_mode = current_trial_reuse_mode

        # 순차적으로 변경할 row_idx와 dv_idx 계산
        row_idx_to_change = row_indices[self.gen_DV_idx // len(dv_indices)]
        dv_idx_to_change = dv_indices[self.gen_DV_idx % len(dv_indices)]

        # FIXED_ROW_IDX 범위 검증
        if row_idx_to_change >= len(target_group):
            self.Write_Log_Lines(f"\t- REGEN_DV: Row index {row_idx_to_change} out of bounds (group size: {len(target_group)})")
            return None

        row_to_change = target_group[row_idx_to_change]
        
        # 변경할 DV 구간 인덱스 계산
        start_col_idx = dv_idx_to_change * num_params
        end_col_idx = start_col_idx + num_params
        
        # 새로운 CH/TH 쌍 값 생성 (다른 DV 자리에 다시 쓸 수 있도록 TH까지 난수로 만들어 둔다)
        if self.is_replace_DV_in_Ch_Th_reuse_mode:
            generated_dv_segment = self.previous_dv_segment
        else:
            new_ch_values = [
                random.randint(h.min_value[i], h.max_value[i])
                for i in range(input_matrix.ch_length)
            ]
            new_ch_values.sort(reverse=True)

            new_th_values = [
                random.randint(h.min_value[input_matrix.ch_length + i], h.max_value[input_matrix.ch_length + i])
                for i in range(input_matrix.th_length)
            ]
            new_th_values.sort(reverse=True)

            generated_dv_segment = np.array(new_ch_values + new_th_values, dtype=np.int32)
            self.previous_dv_segment = generated_dv_segment

        # 쓰는 자리가 HD 복호의 HBF 구간 row의 dv_idx 0이면 TH는 상수
        fixed_columns = input_matrix.Get_Columns_Fixed_In_HBF_Iterations(row_to_change.iter_end)
        new_dv_segment = np.array(generated_dv_segment, dtype=np.int32, copy=True)
        for i, col_idx in enumerate(range(start_col_idx, end_col_idx)):
            if col_idx in fixed_columns:
                new_dv_segment[i] = HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL

        # 기존 값 저장 및 새 값으로 교체
        old_dv_segment = []
        for i, col_idx in enumerate(range(start_col_idx, end_col_idx)):
            old_value = int(row_to_change.ch_th_values[col_idx])
            new_value = new_dv_segment[i]

            # 값 변경 (매트릭스 수정)
            row_to_change.ch_th_values[col_idx] = new_value

            # 변경 내역 기록
            modifications.append((target_group_idx, row_idx_to_change, col_idx, old_value, new_value))


        if modifications:
            old_dv_array = np.array(old_dv_segment, dtype=np.int32)

            self.Write_Log_Lines(f"\t- DV Replacement Reuse: {self.is_replace_DV_in_Ch_Th_reuse_mode}")
            self.Write_Log_Lines(f"\t- DV Replacement: Group {target_group_idx}, Row {row_idx_to_change}, DV {dv_idx_to_change}")
            self.Write_Log_Lines(f"\t    - Old values: {old_dv_array.tolist()}")
            self.Write_Log_Lines(f"\t    - New values: {new_dv_segment.tolist()}")
        else:
            self.Write_Log_Lines("\t- No DV replacement mutations were applied.")
        return input_matrix

    def Gen_LLR_Regen_Row(self, input_matrix: LLR_MATRIX) -> LLR_MATRIX:
        """
        LLR 매트릭스의 타겟 그룹에 대해, 행을 순차적으로 선택하여
        선택된 row의 모든 DV(CH/TH 쌍 전체)를 랜덤한 값으로 대체합니다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).

        Args:
            input_matrix (LLR_MATRIX): 수정 대상 매트릭스 객체

        Returns:
            LLR_MATRIX: Row 교체 변이가 적용된 동일 객체
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Regen_Row: Source matrix must not be None."
            self.MPI_Abort(error_msg)

        h = input_matrix.header

        # Set_Gen_Trial_LLR_Mode에서 계산된 target_group_idx 사용
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(input_matrix.groups) - 1

        target_group = input_matrix.groups[target_group_idx]

        if not target_group:
            self.Write_Log_Lines("\t- No rows in the target group for row replacement.")
            return input_matrix

        num_rows_in_target_group = len(target_group)
        num_dv = h.num_dv

        # ENABLE_FIX_IDX 처리하여 row_indices 먼저 결정
        if REGEN_ROW_CONFIG.ENABLE_FIX_IDX:
            # FIXED_ROW_IDX 처리
            if isinstance(REGEN_ROW_CONFIG.FIXED_ROW_IDX, list):
                row_indices = REGEN_ROW_CONFIG.FIXED_ROW_IDX
            elif REGEN_ROW_CONFIG.FIXED_ROW_IDX != -1:
                row_indices = [REGEN_ROW_CONFIG.FIXED_ROW_IDX]
            else:
                row_indices = list(range(num_rows_in_target_group))
        else:
            row_indices = list(range(num_rows_in_target_group))

        num_rows = len(row_indices)

        if num_rows == 0:
            self.Write_Log_Lines("\t- No valid row indices available for REGEN_ROW")
            return None

        # 현재 모드 결정 (이번 trial에서 사용할 모드)
        last_trial_reuse_mode = self.is_gen_row_reuse_mode

        if self.current_trial_idx == 1:
            self.previous_gen_row = None
            self.gen_row_idx = 0
            current_trial_reuse_mode = False
        elif last_trial_reuse_mode:
            if self.gen_row_idx < (num_rows - 1):
                # 다음 위치로 이동
                self.gen_row_idx += 1
                current_trial_reuse_mode = True
            elif self.gen_row_idx == (num_rows - 1):
                # 재사용 모드 종료
                self.gen_row_idx = 0
                current_trial_reuse_mode = False
        else:
            if self.is_previous_trial_updated:
                self.gen_row_idx = 0
                current_trial_reuse_mode = True
            else:
                self.gen_row_idx = (self.gen_row_idx + 1) % num_rows
                current_trial_reuse_mode = False

        self.is_gen_row_reuse_mode = current_trial_reuse_mode

        # 순차적으로 변경할 row_idx 계산
        row_idx_to_change = row_indices[self.gen_row_idx]

        # FIXED_ROW_IDX 범위 검증
        if row_idx_to_change >= len(target_group):
            self.Write_Log_Lines(f"\t- REGEN_ROW: Row index {row_idx_to_change} out of bounds (group size: {len(target_group)})")
            return None

        row_to_change = target_group[row_idx_to_change]

        # 새로운 row 전체 생성 (모든 DV)
        if self.is_gen_row_reuse_mode and self.previous_gen_row is not None:
            generated_row_values = self.previous_gen_row
        else:
            generated_row_values = []
            for dv_idx in range(num_dv):
                # 각 DV에 대해 CH 값 생성
                new_ch_values = [
                    random.randint(int(h.min_value[i]), int(h.max_value[i]))
                    for i in range(input_matrix.ch_length)
                ]
                new_ch_values.sort(reverse=True)

                # TH 값 생성
                new_th_values = [
                    random.randint(int(h.min_value[input_matrix.ch_length + i]), int(h.max_value[input_matrix.ch_length + i]))
                    for i in range(input_matrix.th_length)
                ]
                new_th_values.sort(reverse=True)

                generated_row_values.extend(new_ch_values + new_th_values)

            generated_row_values = np.array(generated_row_values, dtype=np.int32)
            self.previous_gen_row = generated_row_values

        # 쓰는 row가 HD 복호의 HBF 구간에 있으면 dv_idx 0의 TH는 상수
        new_row_values = generated_row_values.copy()
        input_matrix.Fill_Columns_Fixed_In_HBF_Iterations(new_row_values, row_to_change.iter_end)

        # 기존 값 저장 및 새 값으로 교체
        old_row_values = np.array(row_to_change.ch_th_values, dtype=np.int32)
        row_to_change.ch_th_values = new_row_values.copy()

        self.Write_Log_Lines(f"\t- Row Replacement Reuse: {self.is_gen_row_reuse_mode}")
        self.Write_Log_Lines(f"\t- Row Replacement: Group {target_group_idx}, Row {row_idx_to_change}")
        self.Write_Log_Lines(f"\t    - Old values (first 10): {old_row_values[:10].tolist()}")
        self.Write_Log_Lines(f"\t    - New values (first 10): {new_row_values[:10].tolist()}")

        return input_matrix

    def Gen_LLR_Copy_Rows(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """
        타겟 그룹의 Row를 대상으로, 수집된 후보 Row들과 순차적으로 교체(Copy)를 수행합니다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).

        순서:
        1. 타겟 그룹의 0번 Row에 대해 후보 0, 1, 2... 와 교체
        2. 타겟 그룹의 1번 Row에 대해 후보 0, 1, 2... 와 교체
        ...
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Copy_Rows: Source matrix must not be None."
            self.MPI_Abort(error_msg)

        if self.current_trial_idx == 1:
            self.copy_row_candidates = self.Get_Copy_Row_Candidates(input_matrix)
        num_candidates = len(self.copy_row_candidates)

        if num_candidates == 0:
            self.Write_Log_Lines(f"\t- No copy row candidates available")
            return None

        # Inner Loop: Candidate, Outer Loop: Target Row
        target_row_idx = (self.current_trial_idx - 1) // num_candidates
        candidate_idx = (self.current_trial_idx - 1) % num_candidates

        # 타겟 그룹 범위 검사
        target_group_idx = self.current_target_group_idx if self.current_target_group_idx != -1 else len(input_matrix.groups) - 1
        target_group = input_matrix.groups[target_group_idx]
        if target_row_idx >= len(target_group):
            # 범위 초과 시 None 반환 (trial 스킵)
            return None

        # Copy 실행
        self.Copy_Row(input_matrix, target_row_idx, candidate_idx)
        return input_matrix

    def Gen_LLR_Copy_Group(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """
        타겟 그룹을 수집된 후보 그룹들과 순차적으로 교체(Copy)를 수행합니다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).

        각 trial마다 후보 그룹 하나씩 타겟 그룹에 복사합니다.
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Copy_Group: Source matrix must not be None."
            self.MPI_Abort(error_msg)

        # 첫 trial에서 후보 그룹 수집
        if self.current_trial_idx == 1:
            self.copy_group_candidates = self.Get_Copy_Group_Candidates(input_matrix)

        num_candidates = len(self.copy_group_candidates)
        if num_candidates == 0:
            self.Write_Log_Lines(f"\t- No copy group candidates available")
            return None

        # 현재 trial에 해당하는 후보 그룹 선택
        candidate_idx = (self.current_trial_idx - 1) % num_candidates

        # Copy 실행
        success = self.Copy_Group(input_matrix, candidate_idx)
        if not success:
            return None

        return input_matrix

    def Get_Mutate_Matrix_Skip_Row_Idx(self, group):
        skip_row = 0
        if len(group)>1:
            for row_idx, row in enumerate(group):
                if row_idx == 0:
                    continue
                if row.CSW < self.CSW_update_limit_value:
                    skip_row = row_idx
        return skip_row

    @staticmethod
    def _List_LLR_Matrix_Files(dir_path: str) -> list[tuple[str, int]]:
        """디렉토리 내 LLR_MATRIX_*.txt 파일 목록과 matrix_idx를 반환한다."""
        results = []
        if not os.path.isdir(dir_path):
            return results
        for f in sorted(os.listdir(dir_path)):
            if f.startswith("LLR_MATRIX_") and f.endswith(".txt"):
                idx_str = f[len("LLR_MATRIX_"):-len(".txt")]
                try:
                    results.append((f, int(idx_str)))
                except ValueError:
                    continue
        return results

    def _Check_Header_Compatibility(self, ext_h: 'LLR_Header', cur_h: 'LLR_Header') -> list[str]:
        """외부 매트릭스의 고정 header 필드가 현재 매트릭스와 일치하는지 검사한다."""
        mismatches = []
        if ext_h.num_parameter_each_set != cur_h.num_parameter_each_set:
            mismatches.append(f"num_parameter_each_set(ext={ext_h.num_parameter_each_set}, cur={cur_h.num_parameter_each_set})")
        if ext_h.num_dv != cur_h.num_dv:
            mismatches.append(f"num_dv(ext={ext_h.num_dv}, cur={cur_h.num_dv})")
        if not np.array_equal(ext_h.dv_from, cur_h.dv_from):
            mismatches.append("dv_from")
        if not np.array_equal(ext_h.dv_to, cur_h.dv_to):
            mismatches.append("dv_to")
        if not np.array_equal(ext_h.max_value, cur_h.max_value):
            mismatches.append("max_value")
        if not np.array_equal(ext_h.min_value, cur_h.min_value):
            mismatches.append("min_value")
        return mismatches

    def _Load_External_Single_Row_Candidates(self, current_matrix: LLR_MATRIX) -> list:
        """EXTERNAL_SINGLE_ROW_DIRS에 지정된 디렉토리들에서 LLR_MATRIX 파일을 로드하여
        candidate dict 리스트로 반환한다. 캐시가 있으면 재사용하여 파일 I/O를 1회로 제한한다.
        """
        if not COPY_ROWS_CONFIG.ENABLE_EXTERNAL_SINGLE_ROW:
            return []
        if not COPY_ROWS_CONFIG.EXTERNAL_SINGLE_ROW_DIRS:
            return []

        # 캐시가 있으면 재사용
        if self._external_row_cache is not None:
            return self._external_row_cache

        cur_h = current_matrix.header
        expected_len = cur_h.num_parameter_each_set * cur_h.num_dv
        candidates = []
        base_dir = PATH_CONFIG.INPUT_SINGLE_ROW_LLR_MATRIX_DIR_PATH

        for dir_name in COPY_ROWS_CONFIG.EXTERNAL_SINGLE_ROW_DIRS:
            dir_path = os.path.join(base_dir, dir_name)
            if not os.path.isdir(dir_path):
                self.Write_Log_Lines(f"\t- [WARNING] External Single Row 디렉토리 없음: {dir_path}")
                continue

            file_entries = self._List_LLR_Matrix_Files(dir_path)
            if not file_entries:
                self.Write_Log_Lines(f"\t- [WARNING] {dir_name}/ 내 LLR_MATRIX 파일 없음")
                continue

            dir_loaded = 0
            dir_failed = 0
            for file_name, matrix_idx in file_entries:

                try:
                    ext_matrix = LLR_MATRIX(
                        init_n=REFC_CONFIG.init_n,
                        matrix_idx=matrix_idx,
                        is_HBF_OPT=DAO_CONFIG.IS_HBF_OPT,
                        input_dir=dir_path
                    )
                except (FileNotFoundError, ValueError, IndexError) as e:
                    dir_failed += 1
                    self.Write_Log_Lines(f"\t- [WARNING] {dir_name}/{file_name} 로드 실패: {e}")
                    continue

                # 첫 파일에서만 header 호환성 검증 (같은 디렉토리 = 같은 GEN_SINGLE_ROW 결과)
                if dir_loaded == 0:
                    mismatches = self._Check_Header_Compatibility(ext_matrix.header, cur_h)
                    if mismatches:
                        self.Write_Log_Lines(
                            f"\t- [WARNING] {dir_name}/ header mismatch: {', '.join(mismatches)}. 디렉토리 전체 스킵."
                        )
                        break

                # non-restart 그룹의 row 수집
                for g_idx, group in enumerate(ext_matrix.groups):
                    if (g_idx + 1) in ext_matrix.restart_groups:
                        continue
                    for row in group:
                        if len(row.ch_th_values) != expected_len:
                            continue
                        candidates.append({
                            'ch_th_values': np.array(row.ch_th_values, copy=True),
                            'orig_group': -1,
                            'orig_row': -1
                        })
                        if len(candidates) >= COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES:
                            break
                    if len(candidates) >= COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES:
                        break
                dir_loaded += 1

                if len(candidates) >= COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES:
                    break

            if dir_loaded > 0 or dir_failed > 0:
                self.Write_Log_Lines(f"\t- [COPY_ROWS] {dir_name}/: {dir_loaded} loaded, {dir_failed} failed (총 {len(file_entries)}개)")
            if len(candidates) >= COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES:
                break

        self.Write_Log_Lines(
            f"\t- [COPY_ROWS] External candidates total: {len(candidates)} rows "
            f"from {len(COPY_ROWS_CONFIG.EXTERNAL_SINGLE_ROW_DIRS)} dirs"
        )
        if len(candidates) == 0:
            self.Write_Log_Lines(f"\t- [WARNING] No valid external rows found. Using internal candidates only.")

        self._external_row_cache = candidates
        return candidates

    def Get_Copy_Row_Candidates(self, matrix: LLR_MATRIX) -> list:
        """
        매트릭스의 모든 그룹 내 Row 정보를 수집하여 Copy 후보군으로 저장
        Restart 그룹의 Row는 제외한다.
        타겟 그룹의 Row도 포함 (같은 그룹 내 row 복제 허용, 중복 row 의도적 허용).
        """
        copy_row_candidates = []

        for g_idx, group in enumerate(matrix.groups):
            # Restart 그룹 제외
            if (g_idx + 1) in matrix.restart_groups:
                continue

            for r_idx, row in enumerate(group):
                # 값의 깊은 복사를 위해 numpy array 복사
                candidate_data = {
                    'ch_th_values': np.array(row.ch_th_values, copy=True),
                    'orig_group': g_idx,
                    'orig_row': r_idx
                }
                copy_row_candidates.append(candidate_data)

        internal_count = len(copy_row_candidates)

        # 외부 Single Row 후보 추가
        if COPY_ROWS_CONFIG.ENABLE_EXTERNAL_SINGLE_ROW:
            external = self._Load_External_Single_Row_Candidates(matrix)
            copy_row_candidates.extend(external)
            self.Write_Log_Lines(
                f"\t- Copy Candidates Collected: {len(copy_row_candidates)} rows "
                f"(internal: {internal_count}, external: {len(external)})"
            )
        else:
            self.Write_Log_Lines(f"\t- Copy Candidates Collected: {internal_count} rows found (target group included).")

        return copy_row_candidates

    def Get_Copy_Group_Candidates(self, matrix: LLR_MATRIX) -> list:
        """
        매트릭스의 모든 그룹 정보를 수집하여 Copy 후보군으로 저장
        Restart 그룹과 타겟 그룹은 제외한다 (타겟 그룹이 destination이므로).
        """
        copy_group_candidates = []
        # 타겟 그룹 인덱스 결정 (-1이면 마지막 그룹)
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(matrix.groups) - 1

        for g_idx, group in enumerate(matrix.groups):
            # Restart 그룹 제외
            if (g_idx + 1) in matrix.restart_groups:
                continue
            # 타겟 그룹 제외 (자기 자신과 copy 불필요)
            if g_idx == target_group_idx:
                self.Write_Log_Lines(f"\t- Skipped target group (Group {g_idx}) from candidates")
                continue

            # 그룹 전체를 후보로 추가 (모든 rows의 깊은 복사)
            candidate_rows = []
            for row in group:
                candidate_rows.append({
                    'ch_th_values': np.array(row.ch_th_values, copy=True),
                    'CSW': row.CSW,
                    'floor_flag': row.floor_flag,
                    'iter_start': row.iter_start,
                    'iter_end': row.iter_end
                })

            candidate_data = {
                'rows': candidate_rows,
                'orig_group_idx': g_idx,
                'group_type': matrix.header.type_each_group[g_idx]
            }
            copy_group_candidates.append(candidate_data)

        self.Write_Log_Lines(f"\t- Copy Group Candidates Collected: {len(copy_group_candidates)} groups found (excluding target group {target_group_idx}).")
        return copy_group_candidates

    def Init_Reorder_Group_Mode(self):
        """
        REORDER_GROUP 모드 초기화 - Round 기반 반복문 구조

        **Round 기반 구조:**
        - 각 Round에서 current_donor_pool의 모든 후보를 테스트
        - Best를 선택하여 fixed_order에 추가, current_donor_pool에서 제거
        - 모든 Round 완료 후 Final Verification

        **donor_pool 설정:**
        - base_donor_pool: current_target_idx부터 끝까지 (restart group 제외)
        - current_donor_pool: 각 Round에서 남은 donor (Round마다 하나씩 제거)

        **Trial 수 계산:**
        - HD 모드 (init_n == 1): n*(n+1)/2 + 1 (restart 테스트 안함)
        - SD 모드 (init_n > 1): n*(n+1) + 1 (각 donor마다 restart O/X 2회)
        """
        # base_donor_pool 설정: 모든 target group (restart group 제외)
        # REORDER_GROUP은 모든 target group을 재배열하므로 current_target_idx와 무관
        base_matrix = self.optimal_LLR_matrix
        base_donor_pool = []

        for idx in self.target_group_indices:
            # 경계 검사
            if idx >= len(base_matrix.groups):
                continue
            group = base_matrix.groups[idx]
            # restart group 제외
            if group and len(group) > 0 and group[0].is_group_restart:
                continue
            base_donor_pool.append(idx)

        if len(base_donor_pool) == 0:
            error_msg = "Init_Reorder_Group_Mode: No donor groups available (all are restart or out of bounds)"
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return

        # Trial 수 계산
        # 맨 앞 +1: 초기 테스트 (temp_optimal 초기화용)
        # SD는 모든 case에 대해 restart 까지 테스트해서 HD 대비 *2
        n = len(base_donor_pool)
        is_hd_mode = (REFC_CONFIG.init_n == 1)
        if is_hd_mode:
            # HD: 1 + n + (n-1) + ... + 1 + 1 = 1 + n*(n+1)/2 + 1
            total_trials = 1 + sum(range(n, 0, -1)) + 1
        else:
            # SD: 1 + (n + (n-1) + ... + 1) * 2 + 1 = 1 + n*(n+1) + 1
            total_trials = 1 + sum(range(n, 0, -1)) * 2 + 1

        # State 초기화
        self.reorder_state.is_active = True
        self.reorder_state.current_round = 0
        self.reorder_state.fixed_order = []
        self.reorder_state.final_restart_flags = []
        self.reorder_state.base_donor_pool = base_donor_pool
        self.reorder_state.current_donor_pool = list(base_donor_pool)  # 복사
        self.reorder_state.current_donor_idx = 0
        self.reorder_state.current_with_restart = False
        self.reorder_state.round_best_donor_idx = -1
        self.reorder_state.round_best_with_restart = False
        self.reorder_state.round_best_matrix = None
        self.reorder_state.round_trial_count = 0
        self.reorder_state.total_expected_trials = total_trials

        # 로그 출력
        log_msg = (
            f"\n{'='*80}\n"
            f"REORDER_GROUP 모드 초기화 (Round 기반)\n"
            f"{'='*80}\n"
            f"  - Current target index: {self.current_target_idx}\n"
            f"  - Base donor pool: {base_donor_pool} ({n} groups)\n"
            f"  - HD 모드 (init_n=1): {is_hd_mode}\n"
            f"  - 예상 총 trial 수: {total_trials}\n"
            f"    (초기 테스트: 1 + Round당 테스트 + Final verification: 1)\n"
            f"{'='*80}\n"
        )
        self.Write_Log_Lines(log_msg)

    def Init_Adjust_Iteration_Mode(self):
        """
        ADJUST_ITERATION 모드 초기화

        **ADJUST_ITERATION 전체 동작 구조:**

        1. Stage-Trial 관계:
           - 다른 모드: Stage 내에서 독립적인 여러 trial 실행
           - ADJUST_ITERATION: Stage 내에서 target group별로 순차적으로 진행
             * Trial이 target별 최적화에 종속적
             * State가 Trial 간 유지됨

        2. Iteration 재분배 최적화:
           - Target groups(restart 제외) 중 하나를 focus로 선택
           - focus와 restart를 제외한 모든 그룹(donor)이 동시에 iteration을 transfer_ratio만큼 줄임
           - 줄인 iteration의 합을 focus에 추가 (총 iteration은 동일하게 유지)
           - 모든 target을 테스트 → 최적 target 선정
           - Final verification: 최적 target으로 전체 테스트

        3. State 관리:
           - 초기화: Init_Adjust_Iteration_Mode()에서 AdjustIterState 설정
           - 유지: Stage 전체 동안 유지 (Trial 간 초기화 없음)
           - target 진행: 각 trial마다 current_target_idx 업데이트
           - 종료: 모든 target 완료 시 is_active=False

        4. Trial 수 계산:
           - target별 테스트: len(target_groups)
           - Final verification: 1
           - 총 trial 수: len(target_groups) + 1

        **초기화 작업:**
        - Target groups 설정 (target_group_indices에서 restart 제외)
        - Transfer ratio 설정 (DAO_CONFIG.ITER_TRANSFER_RATIO)
        - 예상 trial 수 계산
        """
        # 타겟 그룹들 선정 (restart group 제외)
        # restart group은 iteration이 1로 고정되어 있으므로 focus 대상에서 제외
        base_matrix = self.optimal_LLR_matrix
        target_groups = []
        for idx in self.target_group_indices:
            # 경계 검사
            if idx >= len(base_matrix.groups):
                continue
            group = base_matrix.groups[idx]
            # restart group 제외
            if group and len(group) > 0 and group[0].is_group_restart:
                continue
            target_groups.append(idx)
        num_target_groups = len(target_groups)

        if num_target_groups == 0:
            error_msg = "Init_Adjust_Iteration_Mode: target_group_indices가 비어있습니다 (또는 모두 restart group)."
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return

        # 상태 초기화
        self.adjust_iter_state.is_active = True
        self.adjust_iter_state.target_groups = target_groups
        self.adjust_iter_state.current_target_idx = 0
        self.adjust_iter_state.iter_transfer_ratio = ADJUST_ITERATION_CONFIG.ITER_TRANSFER_RATIO

        # Trial 수 계산: target 수 (표준 temp_optimal 흐름 사용)
        self.adjust_iter_state.total_expected_trials = num_target_groups
        self.adjust_iter_state.completed_trials = 0

        log_msg = (
            f"\n{'='*80}\n"
            f"ADJUST_ITERATION 모드 초기화\n"
            f"{'='*80}\n"
            f"  - Target groups: {target_groups} (count: {num_target_groups})\n"
            f"  - Transfer ratio: {self.adjust_iter_state.iter_transfer_ratio:.2%}\n"
            f"  - 동작: 각 target에 대해, target과 restart를 제외한 모든 그룹이 동시에 iteration 감소\n"
            f"  - 예상 총 trial 수: {num_target_groups}\n"
            f"  - 업데이트 방식: is_update_at_last_trial (temp_optimal → optimal on last trial)\n"
            f"{'='*80}\n"
        )
        self.Write_Log_Lines(log_msg)

    def Build_Adjusted_Iteration_Matrix(
        self,
        input_matrix: LLR_MATRIX,
        target_group_idx: int,
        transfer_ratio: float
    ) -> Optional[LLR_MATRIX]:
        """
        target_group_indices 내에서 target과 restart를 제외한 그룹(donor)이 동시에
        iteration을 줄여서 target에 추가한 매트릭스를 생성한다.

        총 iteration은 변형 전/후가 동일하게 유지된다.
        그룹 순서는 동일하고, iteration start와 end만 달라진다.
        target_group_indices 외의 그룹은 영향받지 않는다.

        Args:
            input_matrix: 입력 매트릭스 (optimal_LLR_matrix)
            target_group_idx: Iteration을 받을 그룹 인덱스
            transfer_ratio: 전달 비율 (예: 0.1 = 각 donor의 10%를 줄여서 target에 전달)

        Returns:
            Iteration이 재분배된 새 매트릭스 (FER 없음)
            None: 에러 발생 시

        Example:
            target_group_indices = [1, 2, 3]
            변형 전: g0[1-100], g1[101-200], g2[201-201](restart), g3[202-300]
            target=g1, ratio=10%일 때:
            - donor: g3만 (target_group_indices 내에서 g1과 restart인 g2 제외)
            - g0: 100 (target_group_indices 외, unchanged)
            - g3: 99 → 89 (-10)
            - g1: 100 → 110 (+10, g3에서 줄인 양)
            변형 후: g0[1-100], g1[101-210], g2[211-211], g3[212-300]
            (총 iteration 300 동일)
        """
        # 매트릭스 복사
        new_matrix = input_matrix.Deep_Copy(copy_raw_FER=False, copy_seed_FER=False)
        groups = new_matrix.groups
        num_groups = len(groups)

        if target_group_idx >= num_groups:
            error_msg = f"Build_Adjusted_Iteration_Matrix: target_group_idx {target_group_idx} out of range (total groups: {num_groups})"
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return None

        target_group = groups[target_group_idx]
        if len(target_group) == 0:
            self.Write_Log_Lines(f"\t    Warning: Target group {target_group_idx} is empty")
            return new_matrix

        # ========== 1. 각 그룹의 새로운 iteration 범위 계산 ==========
        # 구조: [(group_idx, new_range), ...] - range는 iteration 수 (end - start + 1)
        # restart group은 range=1 고정
        # target_group_indices 외의 그룹은 변경하지 않음
        group_new_ranges: list[int] = []
        total_transfer = 0

        # donor 후보: target_group_indices 내에서 target과 restart 제외
        donor_candidates = set(self.target_group_indices) - {target_group_idx}

        self.Write_Log_Lines(f"\t    Calculating new iteration ranges (target=g{target_group_idx}, ratio={transfer_ratio:.1%})")

        for g_idx in range(num_groups):
            group = groups[g_idx]
            if len(group) == 0:
                group_new_ranges.append(0)
                continue

            old_range = group[0].iter_end - group[0].iter_start + 1

            if group[0].is_group_restart:
                # restart group: range 고정
                group_new_ranges.append(old_range)
            elif g_idx == target_group_idx:
                # target group: 나중에 증가분 추가
                group_new_ranges.append(old_range)  # 임시, 나중에 업데이트
            elif g_idx in donor_candidates:
                # donor group (target_group_indices 내): transfer_ratio만큼 감소
                transfer_amount = max(1, int(old_range * transfer_ratio)) if old_range >= 2 else 0
                new_range = old_range - transfer_amount
                if new_range < 1:
                    new_range = 1
                    transfer_amount = old_range - 1
                group_new_ranges.append(new_range)
                total_transfer += transfer_amount
            else:
                # target_group_indices 외의 그룹: 변경 없음
                group_new_ranges.append(old_range)

        if total_transfer == 0:
            self.Write_Log_Lines(f"\t    Warning: Total transfer is 0, no iteration redistribution")
            return new_matrix

        # target group에 total_transfer 추가
        target_old_range = groups[target_group_idx][0].iter_end - groups[target_group_idx][0].iter_start + 1
        target_new_range = target_old_range + total_transfer
        group_new_ranges[target_group_idx] = target_new_range

        # ========== 2. 연속적인 iteration 범위 재계산 ==========
        # 그룹 순서는 동일, start/end만 재계산
        current_iter = 1
        self.Write_Log_Lines(f"\t    Recalculating iteration ranges (donors={sorted(donor_candidates)}):")

        for g_idx in range(num_groups):
            group = groups[g_idx]
            if len(group) == 0:
                continue

            new_range = group_new_ranges[g_idx]
            old_start = group[0].iter_start
            old_end = group[0].iter_end

            new_start = current_iter
            new_end = current_iter + new_range - 1

            for row in group:
                row.iter_start = new_start
                row.iter_end = new_end

            old_range = old_end - old_start + 1
            delta = new_range - old_range
            delta_str = f"+{delta}" if delta >= 0 else f"{delta}"
            self.Write_Log_Lines(f"\t      g{g_idx}: [{old_start}-{old_end}] → [{new_start}-{new_end}] ({delta_str})")

            current_iter = new_end + 1

        # ========== 3. 총 iteration 검증 ==========
        original_total = input_matrix.groups[-1][0].iter_end if len(input_matrix.groups[-1]) > 0 else 0
        new_total = new_matrix.groups[-1][0].iter_end if len(new_matrix.groups[-1]) > 0 else 0
        self.Write_Log_Lines(f"\t    Total iteration: {original_total} → {new_total} (should be same)")

        return new_matrix

    def Update_Reorder_Round_Result(self, tested_matrix: LLR_MATRIX):
        """
        REORDER_GROUP: 현재 Round의 Best 업데이트 (Round 기반 구조)

        Is_Matrix_Better와 동일한 로직 사용 (모든 채널 비교):
        1. FER이 strictly better이면 True (모든 채널 <=, 하나 이상 <)
        2. 모든 채널 FER 동점이면 avg_iter strictly better 비교
        3. 완전 동점이면 낮은 group idx 우선

        Args:
            tested_matrix: 테스트 완료된 매트릭스 (FER 포함)
        """
        if not self.reorder_state.is_active:
            return

        state = self.reorder_state

        # 결과 로그 출력 (모든 채널)
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            ch_param = self.Get_Channel_Param_String(ch_idx)
            self.Write_Log_Lines(
                f"\t  → Result ch{ch_idx}({ch_param}): FER={tested_matrix.FERs[ch_idx]:.6e}, avg_iter={tested_matrix.avg_iterations[ch_idx]:.2f}"
            )

        # 비교 로직: Is_Matrix_Better와 동일
        is_better = False

        if state.round_best_donor_idx == -1:
            # 첫 후보
            is_better = True
        elif state.round_best_matrix is None:
            # round_best_matrix가 없으면 현재가 best
            is_better = True
        else:
            # Is_Matrix_Better 로직 사용 (모든 채널 비교)
            if self.Is_Matrix_Better(tested_matrix, state.round_best_matrix):
                is_better = True
            else:
                # 완전 동점 체크: 모든 채널의 FER과 avg_iter가 동일
                is_equal = (
                    all(abs(a - b) < 1e-15 for a, b in zip(tested_matrix.FERs, state.round_best_matrix.FERs)) and
                    all(abs(a - b) < 1e-15 for a, b in zip(tested_matrix.avg_iterations, state.round_best_matrix.avg_iterations))
                )
                if is_equal:
                    # 완전 동점 → 낮은 idx 우선
                    current_group_idx = state.current_donor_pool[state.current_donor_idx]
                    best_group_idx = state.current_donor_pool[state.round_best_donor_idx]
                    if current_group_idx < best_group_idx:
                        is_better = True

        if is_better:
            state.round_best_donor_idx = state.current_donor_idx
            state.round_best_with_restart = state.current_with_restart
            state.round_best_matrix = tested_matrix.Deep_Copy(
                copy_raw_FER=True,
                copy_seed_FER=True
            )

            # 로그
            group_idx = state.current_donor_pool[state.current_donor_idx]
            restart_str = "with restart" if state.current_with_restart else "without restart"
            self.Write_Log_Lines(f"\t  ✓ New round best: g{group_idx} ({restart_str})")

    def Finalize_Reorder_Round(self):
        """
        REORDER_GROUP: 현재 Round 완료 처리 (Round 기반 구조)

        현재 Round의 best를 fixed_order에 추가하고 다음 Round 준비
        """
        if not self.reorder_state.is_active:
            return

        state = self.reorder_state

        if state.round_best_donor_idx == -1:
            error_msg = f"Finalize_Reorder_Round: No best selected for round {state.current_round}"
            self.MPI_Abort(error_msg)
            return

        # best 그룹 확정 (current_donor_pool 내 인덱스 → 실제 group index)
        best_group = state.current_donor_pool[state.round_best_donor_idx]

        # Best 확정
        state.fixed_order.append(best_group)
        state.final_restart_flags.append(state.round_best_with_restart)
        state.current_donor_pool.remove(best_group)

        # 로그
        restart_str = "with restart" if state.round_best_with_restart else "without restart"
        self.Write_Log_Lines("")
        self.Write_Log_Lines(f"\t══════════════════════════════════════════════════════════")
        self.Write_Log_Lines(f"\t Round {state.current_round} Finalized")
        self.Write_Log_Lines(f"\t Selected group: g{best_group} ({restart_str})")
        # 모든 채널의 FER/avg_iter 출력
        if state.round_best_matrix is not None:
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                ch_param = self.Get_Channel_Param_String(ch_idx)
                self.Write_Log_Lines(f"\t ch{ch_idx}({ch_param}) FER: {state.round_best_matrix.FERs[ch_idx]:.6e}, Avg_iter: {state.round_best_matrix.avg_iterations[ch_idx]:.2f}")
        self.Write_Log_Lines(f"\t══════════════════════════════════════════════════════════")
        self.Write_Log_Lines(f"\t- Fixed order: {state.fixed_order}")
        self.Write_Log_Lines(f"\t- Restart flags: {state.final_restart_flags}")
        self.Write_Log_Lines(f"\t- Remaining donor pool: {state.current_donor_pool}")
        self.Write_Log_Lines("")

        # 다음 Round 준비
        state.current_round += 1
        state.round_trial_count = 0
        state.current_donor_idx = 0
        state.round_best_donor_idx = -1
        state.round_best_with_restart = False
        state.round_best_matrix = None

    def Build_Reordered_Matrix(
        self,
        group_order: list[int],
        is_position_test: Optional[bool] = None,
        candidate_restart_flag: bool = False
    ) -> LLR_MATRIX:
        """
        주어진 그룹 순서로 LLR 매트릭스를 재구성

        동작:
        1. Non-target 그룹들 (인덱스 < INITIAL_TARGET_GROUP_IDX) 유지
        2. Target position부터 group_order의 그룹들 배치
        3. group_order에 없는 target 그룹들을 원래 순서대로 뒤에 배치
        4. Target 그룹들의 iteration을 재계산:
           - Position별 테스트:
             * Fixed 그룹들: 순차적으로 iteration 할당 (31~40, 41~50, ...)
             * Candidate 그룹: 현재 position의 iteration 할당 (공정한 비교)
             * Candidate의 is_group_restart 플래그를 candidate_restart_flag에 따라 설정
             * 예: Position 1에서 fixed(31~40) + candidate(41~50)
           - Final verification: 전체 그룹이 순차적으로 등분된 iteration 사용
             * 각 그룹의 is_group_restart는 final_restart_flags에 저장된 정보 사용
        5. Header 정보 업데이트

        Args:
            group_order: 재배열할 target 그룹 인덱스 순서 (예: [2, 1])
            is_position_test: Position별 테스트인지 Final verification인지
                             None이면 group_order 길이로 자동 판단
            candidate_restart_flag: Position test 시 candidate 그룹의 restart 여부
                                   (is_position_test=True일 때만 사용)

        Returns:
            재배열된 LLR_MATRIX
        """
        if self.optimal_LLR_matrix is None:
            error_msg = "Build_Reordered_Matrix: optimal_LLR_matrix가 None입니다."
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return None

        # Optimal 매트릭스 복사 (current_LLR_matrix_idx 전달)
        new_matrix = self.optimal_LLR_matrix.Deep_Copy(self.current_LLR_matrix_idx, copy_raw_FER=False, copy_seed_FER=False)
        original_groups = new_matrix.groups.copy()

        # ========== 1. 그룹 재배열 ==========
        # Non-target 그룹들 (INITIAL_TARGET_GROUP_IDX 이전)
        target_start_idx = DAO_CONFIG.INITIAL_TARGET_GROUP_IDX
        non_target_groups = original_groups[:target_start_idx]

        # Target 그룹들
        all_target_indices = self.target_group_indices.copy()

        # group_order에 지정된 그룹들
        reordered_target_groups = []
        for group_idx in group_order:
            if 0 <= group_idx < len(original_groups):
                reordered_target_groups.append(original_groups[group_idx])
            else:
                error_msg = f"Build_Reordered_Matrix: 잘못된 그룹 인덱스 {group_idx} (전체 그룹 수: {len(original_groups)})"
                self.Write_Log_Lines(error_msg)
                self.MPI_Abort(error_msg)
                return None

        # 최종 그룹 순서: [Non-target] + [Reordered target만]
        # Position별 테스트 시 remaining은 제외!
        new_groups = non_target_groups + reordered_target_groups
        new_matrix.groups = new_groups

        # ========== 1-1. Restart 그룹 생성 및 삽입 ==========
        # is_position_test 자동 판단 (파라미터가 None이면)
        num_original_target_groups = len(self.target_group_indices)
        if is_position_test is None:
            is_position_test = len(group_order) < num_original_target_groups

        # restart 그룹 삽입 여부 추적 (iteration 계산에서 사용)
        restart_inserted_for_candidate = False

        if is_position_test:
            # Position별 테스트: candidate 앞에 restart 그룹 삽입 (candidate_restart_flag=True인 경우)
            if candidate_restart_flag and len(reordered_target_groups) > 0:
                # Restart 그룹 생성을 위한 정보 수집
                candidate_group = reordered_target_groups[-1]
                if candidate_group:
                    floor_flag = candidate_group[0].floor_flag
                    num_parameters = len(candidate_group[0].ch_th_values)

                    # Restart 그룹 생성 (iter_start는 나중에 설정)
                    restart_group = self._create_restart_group(
                        iter_start=1,  # placeholder, 아래에서 재설정
                        floor_flag=floor_flag,
                        num_parameters=num_parameters
                    )

                    # Candidate 앞에 restart 그룹 삽입
                    # reordered_target_groups: [..., restart_group, candidate_group]
                    reordered_target_groups.insert(-1, restart_group)

                    # new_groups 재구성
                    new_groups = non_target_groups + reordered_target_groups
                    new_matrix.groups = new_groups

                    restart_inserted_for_candidate = True
                    self.Write_Log_Lines(f"\t    Restart group inserted before candidate")
        else:
            # Final verification: final_restart_flags에 따라 각 그룹 앞에 restart 삽입
            if self.reorder_state.final_restart_flags is not None:
                # 역순으로 처리 (인덱스 변경 방지)
                for i in range(len(reordered_target_groups) - 1, -1, -1):
                    if i < len(self.reorder_state.final_restart_flags):
                        if self.reorder_state.final_restart_flags[i]:
                            group = reordered_target_groups[i]
                            if group:
                                floor_flag = group[0].floor_flag
                                num_parameters = len(group[0].ch_th_values)
                                restart_group = self._create_restart_group(
                                    iter_start=1,  # placeholder
                                    floor_flag=floor_flag,
                                    num_parameters=num_parameters
                                )
                                reordered_target_groups.insert(i, restart_group)

                # new_groups 재구성
                new_groups = non_target_groups + reordered_target_groups
                new_matrix.groups = new_groups

        # ========== 2. Iteration 재계산 ==========
        if target_start_idx >= len(original_groups):
            error_msg = f"Build_Reordered_Matrix: target_start_idx {target_start_idx} out of range (num_groups: {len(original_groups)})"
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return None

        first_target_group = original_groups[target_start_idx]
        if not first_target_group:
            error_msg = "Build_Reordered_Matrix: first_target_group is empty"
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return None

        # Target 영역의 시작 iteration
        target_iter_start = first_target_group[0].iter_start

        # num_original_target_groups는 이미 위에서 선언됨

        # 마지막 원래 target 그룹의 끝 iteration
        # (target_start_idx부터 num_original_target_groups개)
        last_original_target_idx = target_start_idx + num_original_target_groups - 1
        if last_original_target_idx >= len(original_groups):
            last_original_target_idx = len(original_groups) - 1

        last_target_group = original_groups[last_original_target_idx]
        if not last_target_group:
            error_msg = "Build_Reordered_Matrix: last_target_group is empty"
            self.Write_Log_Lines(error_msg)
            self.MPI_Abort(error_msg)
            return None
        target_iter_end = last_target_group[0].iter_end

        # 전체 target 영역을 원래 그룹 수로 등분
        total_iterations = target_iter_end - target_iter_start + 1
        iter_per_group = total_iterations // num_original_target_groups

        # is_position_test는 이미 위에서 결정됨
        if is_position_test:
            # ===== Position별 테스트 =====
            # Fixed 그룹들: 순차적으로 iteration 할당
            # Candidate 그룹: 현재 position의 iteration 할당 (같은 position 내 candidate들은 동일)
            # Restart 그룹 (있으면): candidate 앞에 1 iteration

            num_fixed = len(group_order) - 1  # 마지막이 candidate
            candidate_position = num_fixed

            # Candidate position의 iteration 범위 계산
            position_iter_start = target_iter_start + candidate_position * iter_per_group
            position_iter_end = position_iter_start + iter_per_group - 1

            if restart_inserted_for_candidate:
                # Restart가 있으면: restart 1 iteration + candidate iter_per_group
                restart_iter = position_iter_start
                candidate_iter_start = position_iter_start + 1
                candidate_iter_end = position_iter_start + iter_per_group  # restart 1개 + candidate iter_per_group개
                self.Write_Log_Lines(
                    f"\t[Position Test] Position {candidate_position} (WITH restart): "
                    f"Restart: [{restart_iter}, {restart_iter}], "
                    f"Candidate: [{candidate_iter_start}, {candidate_iter_end}]"
                )
            else:
                # Restart가 없으면: candidate만 iter_per_group
                candidate_iter_start = position_iter_start
                candidate_iter_end = position_iter_end
                self.Write_Log_Lines(
                    f"\t[Position Test] Position {candidate_position} (NO restart): "
                    f"Candidate: [{candidate_iter_start}, {candidate_iter_end}]"
                )

            current_iter = target_iter_start

            # Target 그룹들에 iteration 할당
            target_groups_in_new = new_groups[len(non_target_groups):]
            num_target_groups_in_new = len(target_groups_in_new)

            for i, group in enumerate(target_groups_in_new):
                if i < num_fixed:
                    # Fixed 그룹: 순차적으로 iteration 할당
                    group_start = current_iter
                    group_end = current_iter + iter_per_group - 1
                    current_iter = group_end + 1
                elif restart_inserted_for_candidate and i == num_target_groups_in_new - 2:
                    # Restart 그룹 (candidate 바로 앞)
                    group_start = restart_iter
                    group_end = restart_iter
                elif restart_inserted_for_candidate and i == num_target_groups_in_new - 1:
                    # Candidate 그룹 (restart 뒤)
                    group_start = candidate_iter_start
                    group_end = candidate_iter_end
                else:
                    # Candidate 그룹 (restart 없음)
                    group_start = candidate_iter_start
                    group_end = candidate_iter_end

                for row in group:
                    row.iter_start = group_start
                    row.iter_end = group_end
        else:
            # ===== Final verification =====
            # 각 그룹에 순차적으로 iteration 할당
            # - restart 그룹: 1 iteration
            # - 일반 그룹: iter_per_group iterations
            current_iter = target_iter_start

            self.Write_Log_Lines(
                f"\t[Final Verification] Assigning iterations to all groups "
                f"(start: {target_iter_start}, iter_per_group: {iter_per_group})"
            )

            for group_idx in range(len(non_target_groups), len(new_groups)):
                group = new_groups[group_idx]

                # restart 그룹인지 확인 (is_group_restart 플래그로)
                is_restart_group = group and group[0].is_group_restart

                group_start = current_iter
                if is_restart_group:
                    # Restart 그룹: 1 iteration
                    group_end = current_iter
                else:
                    # 일반 그룹: iter_per_group iterations
                    group_end = current_iter + iter_per_group - 1

                for row in group:
                    row.iter_start = group_start
                    row.iter_end = group_end

                current_iter = group_end + 1

            self.Write_Log_Lines(
                f"\t[Final Verification] Final iteration range: [{target_iter_start}, {current_iter - 1}]"
            )

        # ========== 3. Header 정보 업데이트 ==========
        new_matrix.header.num_group = len(new_groups)
        new_matrix.header.num_row_each_group = np.array([len(g) for g in new_groups], dtype=np.int32)

        # type_each_group 재배열
        # 1. Non-target 그룹들의 type
        new_type_each_group = list(new_matrix.header.type_each_group[:target_start_idx])
        # 2. Target 그룹들의 type (restart 그룹 포함)
        original_type_each_group = new_matrix.header.type_each_group
        group_order_idx = 0  # group_order 순회용 인덱스
        for group in reordered_target_groups:
            if group and group[0].is_group_restart:
                # Restart 그룹: type = 1 (Restart는 항상 type 1)
                new_type_each_group.append(1)
            else:
                # 일반 그룹: 원래 type 사용
                if group_order_idx < len(group_order):
                    original_group_idx = group_order[group_order_idx]
                    if original_group_idx < len(original_type_each_group):
                        new_type_each_group.append(original_type_each_group[original_group_idx])
                    else:
                        new_type_each_group.append(0)
                    group_order_idx += 1
                else:
                    new_type_each_group.append(0)
        new_matrix.header.type_each_group = np.array(new_type_each_group, dtype=np.int32)

        # restart_iter 업데이트 (restart 그룹들의 iteration)
        restart_iters = []
        for group_idx, group in enumerate(new_groups):
            for row in group:
                if row.is_group_restart:
                    restart_iters.append(row.iter_start)
                    # Position test일 때만 로그 출력
                    if is_position_test:
                        self.Write_Log_Lines(f"\t  → Restart detected at group {group_idx}, iteration {row.iter_start}")
                    break  # 그룹당 하나만

        if len(restart_iters) > 0:
            new_matrix.header.num_restart = len(restart_iters)
            new_matrix.header.restart_iter = np.array(restart_iters, dtype=np.int32)
        else:
            new_matrix.header.num_restart = 0
            new_matrix.header.restart_iter = np.array([], dtype=np.int32)

        # restart_groups 업데이트 (1-based 인덱스 리스트)
        # 새로 생성된 그룹 구조에 맞게 재계산
        new_matrix.restart_groups = []
        for g_idx, group in enumerate(new_groups):
            if group and len(group) > 0 and group[0].is_group_restart:
                new_matrix.restart_groups.append(g_idx + 1)  # 1-based

        return new_matrix

    def Gen_LLR_Reorder_Group(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """
        REORDER_GROUP 모드 - Round 기반 반복문 구현

        **동작 방식:**
        - Initialize_Stage에서 Init_Reorder_Group_Mode() 호출하여 초기화
        - 각 Round: current_donor_pool의 모든 후보 테스트 → best 선택 → fixed_order에 추가
        - 모든 Round 완료: Final verification

        **Round 구조:**
        - HD 모드: 각 donor당 1회 테스트 (restart 없음)
        - SD 모드: 각 donor당 2회 테스트 (짝수=without restart, 홀수=with restart)

        **반환:**
        - 이번 trial에서 테스트할 매트릭스 (FER 없음)
        - None: 에러 또는 스킵
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Reorder_Group: Matrix must not be None."
            self.MPI_Abort(error_msg)

        # ========== 1. round_best_matrix 초기화 (첫 호출 시) ==========
        # Init_Reorder_Group_Mode는 Initialize_Stage에서 호출됨
        if self.reorder_state.round_best_matrix is None:
            self.reorder_state.round_best_matrix = input_matrix.Deep_Copy(
                copy_raw_FER=False,
                copy_seed_FER=False
            )
        state = self.reorder_state

        # ========== 1.5. 초기 테스트 (temp_optimal 초기화용) ==========
        # target group 직전까지만 포함된 matrix 테스트 (예: target_idx=2면 [g0, g1])
        if self.current_trial_idx == 1:
            self.Write_Log_Separator("REORDER_GROUP Initial Test", "─"*50)
            self.Write_Log_Lines(f"\t- Testing base matrix before reordering (non-target groups only)")
            self.Write_Log_Lines(f"\t- This will be temp_optimal initial value")

            # target group 직전까지만 포함된 matrix 생성 (fixed_order가 빈 상태)
            initial_matrix = self.Build_Reordered_Matrix(
                group_order=state.fixed_order,  # [] - 빈 리스트
                is_position_test=False
            )
            return initial_matrix

        # ========== 2. Round 완료 체크 + 전체 완료 체크 (재귀 대신 while) ==========
        is_hd_mode = REFC_CONFIG.init_n == 1
        while True:
            num_donors = len(state.current_donor_pool)
            if num_donors == 0:
                # 모든 Round 완료 → Final verification
                self.Write_Log_Separator("REORDER_GROUP Final Verification", "="*50)
                self.Write_Log_Lines(f"\t- All rounds finalized: {state.fixed_order}")
                self.Write_Log_Lines(f"\t- Restart flags: {state.final_restart_flags}")
                self.Write_Log_Lines(f"\t- Final verification test starting...")

                state.is_active = False
                final_matrix = self.Build_Reordered_Matrix(
                    group_order=state.fixed_order,
                    is_position_test=False
                )
                return final_matrix.Deep_Copy(
                    copy_raw_FER=False,
                    copy_seed_FER=False
                )

            trials_this_round = num_donors if is_hd_mode else num_donors * 2
            if state.round_trial_count >= trials_this_round:
                # 현재 Round 완료 → Finalize 후 다음 Round 체크
                self.Finalize_Reorder_Round()
                continue  # while 루프 상단으로 (재귀 대신)
            break  # round 진행 중 → candidate 생성으로

        # ========== 4. 새 Round 시작 로그 ==========
        num_donors = len(state.current_donor_pool)
        if state.round_trial_count == 0:
            self.Write_Log_Separator(
                f"REORDER_GROUP Round {state.current_round}",
                "─"*50
            )
            self.Write_Log_Lines(f"\t- Fixed order so far: {state.fixed_order}")
            self.Write_Log_Lines(f"\t- Current donor pool: {state.current_donor_pool}")
            self.Write_Log_Lines(f"\t- Candidates to test: {state.current_donor_pool} ({num_donors} groups)")
            if is_hd_mode:
                self.Write_Log_Lines(f"\t- HD mode (init_n=1): restart test disabled")
            else:
                self.Write_Log_Lines(f"\t- Each candidate will be tested with/without restart")

        # ========== 5. Candidate 생성 ==========
        trial_idx = state.round_trial_count

        if is_hd_mode:
            donor_idx = trial_idx
            with_restart = False
        else:
            # SD: 짝수 trial = without restart, 홀수 trial = with restart
            donor_idx = trial_idx // 2
            with_restart = (trial_idx % 2 == 1)

        group_idx = state.current_donor_pool[donor_idx]

        # 테스트 정보 저장 (Update에서 사용)
        state.current_donor_idx = donor_idx
        state.current_with_restart = with_restart

        # 로그
        restart_label = "WITH restart" if with_restart else "WITHOUT restart"
        trial_total = state.total_expected_trials - 1  # Final verification 제외
        current_trial = sum(range(len(state.base_donor_pool), len(state.current_donor_pool), -1))
        if is_hd_mode:
            current_trial += trial_idx + 1
        else:
            current_trial = current_trial * 2 + trial_idx + 1

        self.Write_Log_Lines(
            f"\t[Trial {current_trial}/{trial_total}] "
            f"Testing group g{group_idx} ({restart_label})"
        )

        # 카운터 증가
        state.round_trial_count += 1

        # Matrix 생성
        test_order = state.fixed_order + [group_idx]
        candidate_matrix = self.Build_Reordered_Matrix(
            group_order=test_order,
            is_position_test=True,
            candidate_restart_flag=with_restart
        )

        if candidate_matrix is None:
            self.Write_Log_Lines(f"\t    ✗ Failed to create candidate matrix")
            return None

        # FER 제거하고 반환 (Test_LLR에서 측정)
        return candidate_matrix.Deep_Copy(
            copy_raw_FER=False,
            copy_seed_FER=False
        )

    def Gen_LLR_Adjust_Iteration(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """
        Iteration 재분배 방식으로 그룹 최적화를 수행한다.

        **동작 방식:**
        - Initialize_Stage에서 Init_Adjust_Iteration_Mode() 호출하여 초기화
        - 각 호출: 이번 trial에서 테스트할 매트릭스를 반환
        - 각 target group에 대해:
          * target과 restart를 제외한 모든 그룹(donor)이 동시에 iteration을 줄임
          * 줄인 iteration의 합을 target에 추가 (총 iteration 동일)
        - 표준 temp_optimal 흐름으로 최적 추적 (is_update_at_last_trial=True)
        - 모든 target 완료: adjust_iter_state.is_active = False

        **상태 변수 활용:**
        - adjust_iter_state.is_active: ADJUST_ITERATION 모드 활성화 여부
        - adjust_iter_state.target_groups: 테스트할 target group 후보들 (restart 제외)
        - adjust_iter_state.current_target_idx: 현재 target group index (target_groups 내)

        **반환:**
        - 이번 trial에서 테스트할 매트릭스 (FER 없음)
        - None: 모든 target 완료 또는 에러
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Adjust_Iteration: Matrix must not be None."
            self.MPI_Abort(error_msg)

        # ========== 1. 초기화 확인 ==========
        # Init_Adjust_Iteration_Mode는 Initialize_Stage에서 호출됨

        # ========== 2. 모든 target 완료 확인 ==========
        # Type check (Init에서 이미 초기화됨)
        if self.adjust_iter_state.target_groups is None:
            self.MPI_Abort("Gen_LLR_Adjust_Iteration: target_groups is None")

        num_targets = len(self.adjust_iter_state.target_groups)

        if self.adjust_iter_state.completed_trials >= num_targets:
            # 모든 target 완료 - 표준 temp_optimal 흐름으로 이미 처리됨
            # (마지막 trial에서 is_update_at_last_trial로 temp_optimal → optimal 전환)
            self.Write_Log_Separator("ADJUST_ITERATION Completed", "="*50)
            self.Write_Log_Lines(f"\t- All targets tested: {self.adjust_iter_state.completed_trials} trials")
            if self.temp_optimal_LLR_matrix is not None:
                ch_idx = 0
                self.Write_Log_Lines(f"\t- Improvement found (stored in temp_optimal)")
                self.Write_Log_Lines(f"\t- FER: {self.temp_optimal_LLR_matrix.FERs[ch_idx]:.6e}")
                self.Write_Log_Lines(f"\t- avg_iter: {self.temp_optimal_LLR_matrix.avg_iterations[ch_idx]:.2f}")
            else:
                self.Write_Log_Lines(f"\t- No improvement found, optimal unchanged")

            # 모드 완료
            self.adjust_iter_state.is_active = False
            return None  # 더 이상 테스트할 matrix 없음

        # ========== 3. 다음 target 생성 ==========
        target_idx = self.adjust_iter_state.current_target_idx

        # 현재 테스트 target 저장 (Update에서 사용)
        self.adjust_iter_state.current_testing_target_idx = target_idx

        target_group = self.adjust_iter_state.target_groups[target_idx]

        # 로그
        self.Write_Log_Lines(
            f"\t[Trial {self.adjust_iter_state.completed_trials + 1}/{num_targets}] "
            f"Testing target=g{target_group} "
            f"(transfer {self.adjust_iter_state.iter_transfer_ratio:.1%} from all donors to target)"
        )

        # 조합 매트릭스 생성
        adjusted_matrix = self.Build_Adjusted_Iteration_Matrix(
            input_matrix,
            target_group,
            self.adjust_iter_state.iter_transfer_ratio
        )

        if adjusted_matrix is None:
            self.Write_Log_Lines(f"\t    ✗ Failed to create adjusted matrix")
            return None

        # ========== 4. 다음 target으로 진행 ==========
        self.adjust_iter_state.completed_trials += 1
        self.adjust_iter_state.current_target_idx += 1

        # FER 제거하고 반환 (Test_LLR에서 측정)
        adjusted_matrix_no_fer = adjusted_matrix.Deep_Copy(
            copy_raw_FER=False,
            copy_seed_FER=False
        )

        return adjusted_matrix_no_fer

    # ======================== DELETE_ROW 모드 ========================

    def Init_Delete_Row_Mode(self):
        """DELETE_ROW 모드 초기화.

        optimal_LLR_matrix 기준으로 삭제 후보 리스트를 생성하고 상태를 초기화한다.
        max_modification_trial을 N*(N+1)/2 (최악 상한)으로 설정한다.
        """
        base_matrix = self.optimal_LLR_matrix
        total_rows = sum(len(g) for g in base_matrix.groups)

        if total_rows <= 1:
            self.delete_row_state = DeleteRowState(is_active=False)
            self.Write_Log_Lines(f"\t- DELETE_ROW: Only {total_rows} row(s), skipping")
            return

        deletable = self._Build_Delete_Row_Candidates(base_matrix)

        if len(deletable) == 0:
            self.delete_row_state = DeleteRowState(is_active=False)
            self.Write_Log_Lines(f"\t- DELETE_ROW: No deletable rows, skipping")
            return

        N = len(deletable)
        max_trials = N * (N + 1) // 2

        self.delete_row_state = DeleteRowState(
            is_active=True,
            current_round=0,
            deletable_rows=deletable,
            current_candidate_idx=0,
            round_best_candidate_idx=-1,
            round_best_matrix=None,
            round_baseline_matrix=base_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True),
            total_expected_trials=max_trials,
        )
        self.max_modification_trial = max_trials

        self.Write_Log_Lines(f"\t- DELETE_ROW: {N} deletable rows, max {max_trials} trials")
        self.Write_Log_Lines(f"\t- Candidates: {deletable}")

    def _Build_Delete_Row_Candidates(self, matrix: LLR_MATRIX) -> list:
        """삭제 가능한 (group_idx, row_idx) 리스트 생성.

        - target_group_indices 범위 내의 모든 row (restart group 포함)
        - 전체 matrix에 최소 1개 row는 남아야 함
        """
        total_rows = sum(len(g) for g in matrix.groups)
        if total_rows <= 1:
            return []

        result = []
        for g_idx in self.target_group_indices:
            if g_idx >= len(matrix.groups):
                continue
            group = matrix.groups[g_idx]
            for r_idx in range(len(group)):
                result.append((g_idx, r_idx))

        return result

    def Gen_LLR_Delete_Row(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """DELETE_ROW 모드 - 재귀 없는 while 기반 구현

        **동작 방식:**
        - 각 Round: deletable_rows의 모든 후보를 하나씩 삭제 후 테스트 → best 선택
        - Round 완료 시 Finalize → 개선 있으면 다음 Round, 없으면 종료
        - 종료 시 baseline을 final verification으로 반환

        **반환:**
        - 이번 trial에서 테스트할 매트릭스 (FER 없음)
        - None: 에러 또는 이미 종료된 상태
        """
        if input_matrix is None:
            self.MPI_Abort("Gen_LLR_Delete_Row: Matrix must not be None.")

        state = self.delete_row_state
        if not state.is_active:
            return None

        # Round 완료 체크 → Finalize → 다음 Round 준비 (재귀 대신 while)
        while state.current_candidate_idx >= len(state.deletable_rows):
            self._Finalize_Delete_Row_Round()
            if not state.is_active:
                # 종료: baseline을 final verification으로 반환
                self.Write_Log_Separator("DELETE_ROW Final Verification", "="*50)
                self.Write_Log_Lines(f"\t- Total rounds completed: {state.current_round}")
                return state.round_baseline_matrix.Deep_Copy(
                    input_matrix_idx=input_matrix.matrix_idx,
                    copy_raw_FER=False, copy_seed_FER=False
                )

        # 새 Round 시작 로그
        if state.round_trial_count == 0:
            self.Write_Log_Separator(
                f"DELETE_ROW Round {state.current_round}",
                "─"*50
            )
            self.Write_Log_Lines(f"\t- Baseline total rows: {sum(len(g) for g in state.round_baseline_matrix.groups)}")
            self.Write_Log_Lines(f"\t- Candidates to test: {len(state.deletable_rows)} rows")

        # 현재 후보 삭제하여 candidate matrix 생성
        (target_g_idx, target_r_idx) = state.deletable_rows[state.current_candidate_idx]

        candidate = self._Build_Deleted_Row_Matrix(
            state.round_baseline_matrix, target_g_idx, target_r_idx
        )

        # 로그: group 정보 출력
        if target_g_idx < len(state.round_baseline_matrix.groups):
            group = state.round_baseline_matrix.groups[target_g_idx]
            is_restart = group[0].is_group_restart if group else False
            group_type = " (restart)" if is_restart else ""
            is_group_delete = len(group) == 1
            delete_type = "group" if is_group_delete else "row"
        else:
            group_type = ""
            delete_type = "row"
        self.Write_Log_Lines(
            f"\t[Trial {state.round_trial_count + 1}/{len(state.deletable_rows)}] "
            f"Deleting {delete_type} g{target_g_idx} r{target_r_idx}{group_type}"
        )

        state.current_candidate_idx += 1
        state.round_trial_count += 1

        if candidate is None:
            return None

        return candidate.Deep_Copy(input_matrix_idx=input_matrix.matrix_idx, copy_raw_FER=False, copy_seed_FER=False)

    def _Build_Deleted_Row_Matrix(self, base_matrix: LLR_MATRIX, del_g_idx: int, del_r_idx: int) -> Optional[LLR_MATRIX]:
        """row 하나를 삭제한 새 matrix 생성.

        Case A: group에 row 2개 이상 → row만 제거, CSW 보정
        Case B: group에 row 1개 → group 전체 삭제, iteration 재분배
        """
        new_matrix = base_matrix.Deep_Copy(copy_raw_FER=False, copy_seed_FER=False)

        if del_g_idx >= len(new_matrix.groups):
            return None

        group = new_matrix.groups[del_g_idx]
        if del_r_idx >= len(group):
            return None

        if len(group) >= 2:
            # Case A: row만 제거
            group.pop(del_r_idx)
            if del_r_idx == 0:
                group[0].CSW = -1  # 새 0번 row의 CSW를 -1로 (C1 규칙)
            new_matrix.header.num_row_each_group[del_g_idx] -= 1
        else:
            # Case B: group 전체 삭제 + iteration 재분배
            new_matrix = self._Delete_Entire_Group(new_matrix, del_g_idx)
            if new_matrix is None:
                return None

        return new_matrix

    def _Delete_Entire_Group(self, matrix: LLR_MATRIX, del_g_idx: int) -> Optional[LLR_MATRIX]:
        """group 전체를 삭제하고 iteration을 전후 non-restart group에 재분배.

        재분배 규칙:
        - 삭제된 group의 iteration을 반씩 나눠 prev/next non-restart group에 분배
        - prev 없으면 next에 전부, next 없으면 prev에 전부
        - 둘 다 없으면 iteration 소실 (max_iteration 감소)
        - 홀수면 prev에 ceiling, next에 floor
        """
        num_groups = len(matrix.groups)
        if num_groups <= 1:
            return None  # 유일한 group은 삭제 불가

        deleted_group = matrix.groups[del_g_idx]
        deleted_duration = deleted_group[0].iter_end - deleted_group[0].iter_start + 1

        # 인접 non-restart group 찾기 (restart group에 iteration 추가 시 R2 위반 방지)
        prev_g_idx = None
        for i in range(del_g_idx - 1, -1, -1):
            if not matrix.groups[i][0].is_group_restart:
                prev_g_idx = i
                break

        next_g_idx = None
        for i in range(del_g_idx + 1, num_groups):
            if not matrix.groups[i][0].is_group_restart:
                next_g_idx = i
                break

        # 분배량 계산
        if prev_g_idx is None and next_g_idx is None:
            give_to_prev, give_to_next = 0, 0  # iteration 소실 (나머지가 전부 restart)
        elif prev_g_idx is None:
            give_to_prev, give_to_next = 0, deleted_duration
        elif next_g_idx is None:
            give_to_prev, give_to_next = deleted_duration, 0
        else:
            give_to_prev = (deleted_duration + 1) // 2  # ceiling
            give_to_next = deleted_duration // 2         # floor

        # 각 group의 duration 기록 (삭제 대상 제외)
        durations = []
        for g_idx, group in enumerate(matrix.groups):
            if g_idx == del_g_idx:
                continue
            duration = group[0].iter_end - group[0].iter_start + 1
            if g_idx == prev_g_idx:
                duration += give_to_prev
            elif g_idx == next_g_idx:
                duration += give_to_next
            durations.append(duration)

        # group 삭제
        matrix.groups.pop(del_g_idx)

        # iteration 재빌드 (G2 연속성 보장)
        current_iter = 1
        for g_idx, group in enumerate(matrix.groups):
            duration = durations[g_idx]
            iter_start = current_iter
            iter_end = current_iter + duration - 1
            for row in group:
                row.iter_start = iter_start
                row.iter_end = iter_end
            current_iter = iter_end + 1

        # header 업데이트
        matrix.header.num_group -= 1
        matrix.header.num_row_each_group = np.array([len(g) for g in matrix.groups])
        matrix.header.type_each_group = np.delete(matrix.header.type_each_group, del_g_idx)

        # restart_groups 업데이트 (1-based → 인덱스 시프트)
        new_restart_groups = []
        for rg in matrix.restart_groups:
            rg_0based = rg - 1
            if rg_0based == del_g_idx:
                continue  # 삭제된 group
            elif rg_0based > del_g_idx:
                new_restart_groups.append(rg - 1)
            else:
                new_restart_groups.append(rg)
        matrix.restart_groups = sorted(new_restart_groups)

        # restart_iter 재빌드
        new_restart_iter = []
        for rg_1based in matrix.restart_groups:
            g = matrix.groups[rg_1based - 1]
            new_restart_iter.append(g[0].iter_start)
        matrix.header.restart_iter = np.array(new_restart_iter, dtype=np.int32) if new_restart_iter else np.array([], dtype=np.int32)
        matrix.header.num_restart = len(new_restart_iter)

        # max_iteration 업데이트
        matrix.max_iteration = matrix.groups[-1][-1].iter_end

        return matrix

    def Update_Delete_Row_Round_Result(self, tested_matrix: LLR_MATRIX):
        """DELETE_ROW: 현재 Round의 Best 업데이트.

        round_baseline_matrix 대비 개선된 경우만 best로 채택.
        기존 round best보다도 더 좋아야 갱신.

        Args:
            tested_matrix: 테스트 완료된 매트릭스 (FER 포함)
        """
        state = self.delete_row_state
        if not state.is_active:
            return

        # 결과 로그
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            ch_param = self.Get_Channel_Param_String(ch_idx)
            self.Write_Log_Lines(
                f"\t  → Result ch{ch_idx}({ch_param}): FER={tested_matrix.FERs[ch_idx]:.6e}, "
                f"avg_iter={tested_matrix.avg_iterations[ch_idx]:.2f}"
            )

        # baseline 대비 개선 여부 확인
        if not self.Is_Matrix_Better(tested_matrix, state.round_baseline_matrix):
            return

        # 기존 round best와 비교
        is_better = False
        if state.round_best_candidate_idx == -1:
            is_better = True
        elif state.round_best_matrix is None:
            is_better = True
        elif self.Is_Matrix_Better(tested_matrix, state.round_best_matrix):
            is_better = True

        if is_better:
            state.round_best_candidate_idx = state.current_candidate_idx - 1
            state.round_best_matrix = tested_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True)
            (g_idx, r_idx) = state.deletable_rows[state.round_best_candidate_idx]
            self.Write_Log_Lines(f"\t  ✓ New round best: delete g{g_idx} r{r_idx}")

    def _Finalize_Delete_Row_Round(self):
        """현재 Round 완료 처리. 개선 없으면 종료, 있으면 다음 Round 준비."""
        state = self.delete_row_state

        if state.round_best_candidate_idx == -1:
            # 개선 없음 → 종료
            self.Write_Log_Lines(f"\t DELETE_ROW Round {state.current_round}: No improvement, stopping")
            state.is_active = False
            return

        # best 삭제 확정
        (g_idx, r_idx) = state.deletable_rows[state.round_best_candidate_idx]
        self.Write_Log_Separator(f"DELETE_ROW Round {state.current_round} Finalized", "═"*50)
        self.Write_Log_Lines(f"\t Selected deletion: g{g_idx} r{r_idx}")
        if state.round_best_matrix is not None:
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                ch_param = self.Get_Channel_Param_String(ch_idx)
                self.Write_Log_Lines(f"\t ch{ch_idx}({ch_param}) FER: {state.round_best_matrix.FERs[ch_idx]:.6e}, Avg_iter: {state.round_best_matrix.avg_iterations[ch_idx]:.2f}")

        # 새 baseline = round best matrix
        state.round_baseline_matrix = state.round_best_matrix.Deep_Copy(
            copy_raw_FER=True, copy_seed_FER=True
        )

        # 다음 Round의 후보 재빌드
        new_candidates = self._Build_Delete_Row_Candidates(state.round_baseline_matrix)
        if len(new_candidates) == 0:
            self.Write_Log_Lines(f"\t No more rows to delete, stopping")
            state.is_active = False
            return

        # 다음 Round 준비
        state.current_round += 1
        state.deletable_rows = new_candidates
        state.current_candidate_idx = 0
        state.round_best_candidate_idx = -1
        state.round_best_matrix = None
        state.round_trial_count = 0

        self.Write_Log_Lines(f"\t Next round candidates: {len(new_candidates)} rows")

    def _create_restart_group(
        self,
        iter_start: int,
        floor_flag: int,
        num_parameters: int
    ) -> list[LLR_Row]:
        """
        restart 그룹 생성 (1개의 row).

        Args:
            iter_start: restart의iteration 시작 (= 종료)
            floor_flag: floor flag 값
            num_parameters: ch_th_values 배열 길이

        Returns:
            restart row 1개를 포함한 그룹
        """
        restart_values = np.full(num_parameters, -1, dtype=np.int32)
        restart_row = LLR_Row(
            ch_th_values=restart_values,
            CSW=-1,
            iter_start=iter_start,
            iter_end=iter_start,  # duration = 1
            floor_flag=floor_flag,
            is_group_restart=True
        )
        return [restart_row]

    # ======================== INSERT_RESTART_GROUP 모드 ========================

    def Init_Insert_Restart_Group_Mode(self):
        """INSERT_RESTART_GROUP 모드 초기화.

        optimal_LLR_matrix 기준으로 유효 삽입 위치를 생성하고 상태를 초기화한다.
        """
        base_matrix = self.optimal_LLR_matrix
        candidates = self._Build_Insert_Restart_Candidates(base_matrix)

        if len(candidates) == 0:
            self.insert_restart_group_state = InsertRestartGroupState(is_active=False)
            self.Write_Log_Lines(f"\t- INSERT_RESTART_GROUP: No insertable positions, skipping")
            return

        N = len(candidates)
        max_trials = N * (N + 1) // 2

        self.insert_restart_group_state = InsertRestartGroupState(
            is_active=True,
            current_round=0,
            insertable_positions=candidates,
            round_baseline_matrix=base_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True),
            total_expected_trials=max_trials,
        )
        self.max_modification_trial = max_trials

        self.Write_Log_Lines(f"\t- INSERT_RESTART_GROUP: {N} insertable positions, max {max_trials} trials")
        self.Write_Log_Lines(f"\t- Candidates: {candidates}")

    def _Build_Insert_Restart_Candidates(self, matrix: LLR_MATRIX) -> list:
        """유효한 restart group 삽입 위치 리스트 생성.

        - insert_pos ∈ [1, N-1] (맨 처음/끝 제외)
        - groups[insert_pos - 1]이 restart → 제외
        - groups[insert_pos]이 restart → 제외
        - target_group_indices 범위 내만 허용
        """
        num_groups = len(matrix.groups)
        if num_groups < 2:
            return []

        result = []
        for insert_pos in range(1, num_groups):
            # target 범위 체크: 직전 또는 직후가 target 범위 내
            if insert_pos - 1 not in self.target_group_indices and \
               insert_pos not in self.target_group_indices:
                continue

            prev_group = matrix.groups[insert_pos - 1]
            next_group = matrix.groups[insert_pos]

            if prev_group[0].is_group_restart:
                continue
            if next_group[0].is_group_restart:
                continue

            result.append(insert_pos)

        return result

    def Gen_LLR_Insert_Restart_Group(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """INSERT_RESTART_GROUP 모드 - while 기반

        각 Round: 유효 위치에 restart group 삽입 후 테스트 → best 선택
        Round 완료 시 Finalize → 개선 있으면 다음 Round, 없으면 종료
        """
        if input_matrix is None:
            self.MPI_Abort("Gen_LLR_Insert_Restart_Group: Matrix must not be None.")

        state = self.insert_restart_group_state
        if not state.is_active:
            return None

        # Round 완료 체크 → Finalize → 다음 Round 준비
        while state.current_candidate_idx >= len(state.insertable_positions):
            self._Finalize_Insert_Restart_Group_Round()
            if not state.is_active:
                self.Write_Log_Separator("INSERT_RESTART_GROUP Final Verification", "="*50)
                self.Write_Log_Lines(f"\t- Total rounds completed: {state.current_round}")
                return state.round_baseline_matrix.Deep_Copy(
                    input_matrix_idx=input_matrix.matrix_idx,
                    copy_raw_FER=False, copy_seed_FER=False
                )

        # 새 Round 시작 로그
        if state.round_trial_count == 0:
            self.Write_Log_Separator(
                f"INSERT_RESTART_GROUP Round {state.current_round}",
                "─"*50
            )
            self.Write_Log_Lines(f"\t- Baseline groups: {len(state.round_baseline_matrix.groups)}")
            self.Write_Log_Lines(f"\t- Candidates to test: {len(state.insertable_positions)} positions")

        # 현재 후보 위치에 restart group 삽입하여 candidate matrix 생성
        insert_pos = state.insertable_positions[state.current_candidate_idx]

        candidate = self._Build_Inserted_Restart_Matrix(
            state.round_baseline_matrix, insert_pos
        )

        self.Write_Log_Lines(
            f"\t[Trial {state.round_trial_count + 1}/{len(state.insertable_positions)}] "
            f"Insert restart at pos {insert_pos} (between g{insert_pos-1} and g{insert_pos})"
        )

        state.current_candidate_idx += 1
        state.round_trial_count += 1

        if candidate is None:
            return None

        return candidate.Deep_Copy(input_matrix_idx=input_matrix.matrix_idx, copy_raw_FER=False, copy_seed_FER=False)

    def _Build_Inserted_Restart_Matrix(self, base_matrix: LLR_MATRIX, insert_pos: int) -> Optional[LLR_MATRIX]:
        """restart group을 삽입한 새 matrix 생성.

        1. 각 group의 duration 기록
        2. restart group 생성 (1 row, 1 iteration)
        3. group 삽입
        4. iteration 재빌드 (G2 연속성 보장)
        5. header 업데이트 (num_group, num_row_each_group, type_each_group)
        6. restart_groups 업데이트 (1-based 인덱스 shift)
        7. restart_iter 재빌드
        8. max_iteration 업데이트
        """
        new_matrix = base_matrix.Deep_Copy(copy_raw_FER=False, copy_seed_FER=False)

        # 1. 각 group의 duration 기록
        durations = [g[0].iter_end - g[0].iter_start + 1 for g in new_matrix.groups]

        # 2. restart group 생성
        len_row = new_matrix.header.num_parameter_each_set * new_matrix.header.num_dv
        floor_flag = new_matrix.groups[0][0].floor_flag
        restart_group = self._create_restart_group(
            iter_start=0,  # 재빌드 예정
            floor_flag=floor_flag,
            num_parameters=len_row,
        )

        # 3. group 삽입
        new_matrix.groups.insert(insert_pos, restart_group)
        durations.insert(insert_pos, 1)  # restart = 1 iteration

        # 4. iteration 재빌드 (G2 연속성 보장)
        current_iter = 1
        for g_idx, group in enumerate(new_matrix.groups):
            duration = durations[g_idx]
            iter_start = current_iter
            iter_end = current_iter + duration - 1
            for row in group:
                row.iter_start = iter_start
                row.iter_end = iter_end
            current_iter = iter_end + 1

        # 5. header 업데이트
        new_matrix.header.num_group += 1
        new_matrix.header.num_row_each_group = np.array([len(g) for g in new_matrix.groups])
        new_matrix.header.type_each_group = np.insert(
            new_matrix.header.type_each_group, insert_pos, 1  # restart group은 항상 type 1
        )

        # 6. restart_groups 업데이트 (1-based)
        new_restart_groups = []
        for rg in new_matrix.restart_groups:
            if rg - 1 >= insert_pos:
                new_restart_groups.append(rg + 1)
            else:
                new_restart_groups.append(rg)
        new_restart_groups.append(insert_pos + 1)  # 새 restart (1-based)
        new_matrix.restart_groups = sorted(new_restart_groups)

        # 7. restart_iter 재빌드
        new_restart_iter = []
        for rg_1based in new_matrix.restart_groups:
            g = new_matrix.groups[rg_1based - 1]
            new_restart_iter.append(g[0].iter_start)
        new_matrix.header.restart_iter = np.array(new_restart_iter, dtype=np.int32) if new_restart_iter else np.array([], dtype=np.int32)
        new_matrix.header.num_restart = len(new_restart_iter)

        # 8. max_iteration 업데이트
        new_matrix.max_iteration = new_matrix.groups[-1][-1].iter_end

        return new_matrix

    def Update_Insert_Restart_Group_Round_Result(self, tested_matrix: LLR_MATRIX):
        """INSERT_RESTART_GROUP: 현재 Round의 Best 업데이트.

        round_baseline_matrix 대비 개선된 경우만 best로 채택.
        기존 round best보다도 더 좋아야 갱신.
        """
        state = self.insert_restart_group_state
        if not state.is_active:
            return

        # 결과 로그
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            ch_param = self.Get_Channel_Param_String(ch_idx)
            self.Write_Log_Lines(
                f"\t  → Result ch{ch_idx}({ch_param}): FER={tested_matrix.FERs[ch_idx]:.6e}, "
                f"avg_iter={tested_matrix.avg_iterations[ch_idx]:.2f}"
            )

        # baseline 대비 개선 여부 확인
        if not self.Is_Matrix_Better(tested_matrix, state.round_baseline_matrix):
            return

        # 기존 round best와 비교
        is_better = False
        if state.round_best_candidate_idx == -1:
            is_better = True
        elif state.round_best_matrix is None:
            is_better = True
        elif self.Is_Matrix_Better(tested_matrix, state.round_best_matrix):
            is_better = True

        if is_better:
            state.round_best_candidate_idx = state.current_candidate_idx - 1
            state.round_best_matrix = tested_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True)
            insert_pos = state.insertable_positions[state.round_best_candidate_idx]
            self.Write_Log_Lines(f"\t  ✓ New round best: insert restart at pos {insert_pos}")

    def _Finalize_Insert_Restart_Group_Round(self):
        """현재 Round 완료 처리. 개선 없으면 종료, 있으면 다음 Round 준비."""
        state = self.insert_restart_group_state

        if state.round_best_candidate_idx == -1:
            self.Write_Log_Lines(f"\t INSERT_RESTART_GROUP Round {state.current_round}: No improvement, stopping")
            state.is_active = False
            return

        # best 삽입 확정
        insert_pos = state.insertable_positions[state.round_best_candidate_idx]
        self.Write_Log_Separator(f"INSERT_RESTART_GROUP Round {state.current_round} Finalized", "═"*50)
        self.Write_Log_Lines(f"\t Selected insertion: pos {insert_pos}")
        if state.round_best_matrix is not None:
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                ch_param = self.Get_Channel_Param_String(ch_idx)
                self.Write_Log_Lines(f"\t ch{ch_idx}({ch_param}) FER: {state.round_best_matrix.FERs[ch_idx]:.6e}, Avg_iter: {state.round_best_matrix.avg_iterations[ch_idx]:.2f}")

        # 새 baseline = round best matrix
        state.round_baseline_matrix = state.round_best_matrix.Deep_Copy(
            copy_raw_FER=True, copy_seed_FER=True
        )

        # 다음 Round의 후보 재빌드
        new_candidates = self._Build_Insert_Restart_Candidates(state.round_baseline_matrix)
        if len(new_candidates) == 0:
            self.Write_Log_Lines(f"\t No more insertable positions, stopping")
            state.is_active = False
            return

        # 다음 Round 준비
        state.current_round += 1
        state.insertable_positions = new_candidates
        state.current_candidate_idx = 0
        state.round_best_candidate_idx = -1
        state.round_best_matrix = None
        state.round_trial_count = 0

        self.Write_Log_Lines(f"\t Next round candidates: {len(new_candidates)} positions")

    def _is_reorder_candidate_better(
        self,
        candidate: Optional[LLR_MATRIX],
        current_best: Optional[LLR_MATRIX]
    ) -> bool:
        """
        REORDER_GROUP 모드에서 candidate 매트릭스가 current_best보다 나은지 판단.

        우선순위:
        1. FER (채널 우선순위 고려)
           - ch_type=1 (RBER): 큰 RBER 값의 채널 우선순위
           - ch_type=2 or 3: 큰 num_fixed_errs 값의 채널 우선순위
        2. FER이 동일한 경우: 큰 avg_iteration이 좋음

        Args:
            candidate: 비교 대상 매트릭스
            current_best: 현재 최적 매트릭스 (None이면 candidate가 자동 선택)

        Returns:
            bool: candidate가 더 나으면 True
        """
        # current_best가 None이면 candidate가 자동 선택
        if current_best is None:
            return True

        if candidate is None:
            return False

        # 채널 우선순위 결정 (내림차순: 큰 값이 높은 우선순위)
        num_channels = REFC_CONFIG.NUM_TARGET_CHANNELS
        if REFC_CONFIG.ch_type == ChType.RBER:
            # RBER 모드: 큰 RBER 값이 우선순위
            channel_priorities = sorted(
                range(num_channels),
                key=lambda i: REFC_CONFIG.RBERs[i] if i < len(REFC_CONFIG.RBERs) else 0,
                reverse=True
            )
        else:  # FIXED_ERROR or STRONG_ERROR
            # num_fixed_errs가 큰 채널이 우선순위
            channel_priorities = sorted(
                range(num_channels),
                key=lambda i: REFC_CONFIG.num_fixed_errs[i] if i < len(REFC_CONFIG.num_fixed_errs) else 0,
                reverse=True
            )

        # 우선순위 순서대로 FER 비교
        for ch_idx in channel_priorities:
            candidate_fer = candidate.FERs[ch_idx]
            best_fer = current_best.FERs[ch_idx]

            if candidate_fer < best_fer:
                return True
            elif candidate_fer > best_fer:
                return False
            # 같으면 다음 채널로

        # 모든 채널의 FER이 동일 → avg_iteration 비교 (큰 값이 좋음)
        # 우선순위 채널부터 비교
        for ch_idx in channel_priorities:
            candidate_avg = candidate.avg_iterations[ch_idx]
            best_avg = current_best.avg_iterations[ch_idx]

            if candidate_avg > best_avg:
                return True
            elif candidate_avg < best_avg:
                return False

        # 완전히 동일
        return False

    def _is_reorder_candidate_equal(
        self,
        candidate: Optional[LLR_MATRIX],
        current_best: Optional[LLR_MATRIX]
    ) -> bool:
        """
        REORDER_GROUP 모드에서 candidate와 current_best가 동점인지 판단.

        Args:
            candidate: 비교 대상 매트릭스
            current_best: 현재 최적 매트릭스

        Returns:
            bool: 완전히 동일하면 True
        """
        if candidate is None or current_best is None:
            return False

        # 모든 채널의 FER이 동일한지 확인
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            if abs(candidate.FERs[ch_idx] - current_best.FERs[ch_idx]) > 1e-15:
                return False

        # 모든 채널의 avg_iteration이 동일한지 확인
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            if abs(candidate.avg_iterations[ch_idx] - current_best.avg_iterations[ch_idx]) > 1e-15:
                return False

        return True

    def _recalculate_iterations_for_reorder(
        self,
        groups: list[list[LLR_Row]],
        start_idx: int,
        total_available_iterations: int
    ) -> None:
        """
        start_idx부터의 그룹들에 대해 iteration 범위를 재계산하여 등분 배분.
        restart 그룹은 항상 1 iteration만 사용하고, 일반 그룹들만 나머지를 등분.

        Args:
            groups: 전체 그룹 리스트
            start_idx: 재계산 시작 그룹 인덱스
            total_available_iterations: 배분할 총 iteration 수
        """
        num_groups = len(groups) - start_idx
        if num_groups <= 0:
            return

        # 이전 그룹의 마지막 iteration 찾기
        if start_idx > 0:
            prev_group = groups[start_idx - 1]
            if not prev_group:
                prev_iter_end = 0  # 빈 그룹인 경우 기본값
            else:
                prev_iter_end = prev_group[0].iter_end
        else:
            prev_iter_end = 0

        next_iter_start = prev_iter_end + 1

        # restart 그룹 수 계산 (빈 그룹은 건너뜀)
        num_restart_groups = sum(1 for i in range(start_idx, len(groups))
                                 if groups[i] and groups[i][0].is_group_restart)

        # 일반 그룹 수 (restart 제외)
        num_normal_groups = num_groups - num_restart_groups

        if num_normal_groups <= 0:
            # 모든 그룹이 restart인 경우 (일어나지 않아야 함)
            return

        # restart 그룹들이 사용할 총 iteration (각 restart는 1)
        restart_iterations = num_restart_groups

        # 일반 그룹들에 배분할 iteration
        remaining_iterations = total_available_iterations - restart_iterations

        # 등분 배분
        base_duration = remaining_iterations // num_normal_groups
        extra = remaining_iterations % num_normal_groups
        normal_group_counter = 0

        for i in range(num_groups):
            group_idx = start_idx + i
            group = groups[group_idx]

            # 빈 그룹은 건너뜀
            if not group:
                continue

            # restart 그룹은 항상 1 iteration
            if group[0].is_group_restart:
                duration = 1
            else:
                duration = base_duration + (1 if normal_group_counter < extra else 0)
                normal_group_counter += 1

            iter_end = next_iter_start + duration - 1

            # 그룹의 모든 row에 대해 iteration 업데이트
            for row in group:
                row.iter_start = next_iter_start
                row.iter_end = iter_end

            next_iter_start = iter_end + 1

    def _create_reorder_test_matrix(
        self,
        base_matrix: Optional[LLR_MATRIX],
        target_idx: int,
        fixed_order: list,
        candidate_group_idx: int,
        remaining_pool: list,
        original_reorder_indices: list,
        with_restart: bool = False
    ) -> Optional[LLR_MATRIX]:
        """
        재배열 테스트용 매트릭스를 생성한다.

        Args:
            base_matrix: 기준 매트릭스
            target_idx: 재배열 시작 위치
            fixed_order: 이미 고정된 그룹 인덱스 리스트
            candidate_group_idx: 현재 위치에 시도할 그룹 인덱스
            remaining_pool: 아직 배치 안 된 그룹 인덱스 리스트
            original_reorder_indices: 원래 재배열 대상 그룹 인덱스 리스트
            with_restart: True일 경우 candidate 그룹 앞에 restart 그룹 추가 (2SD/3SD)

        Returns:
            재배열된 매트릭스
        """
        if base_matrix is None:
            return None

        # 매트릭스 복사
        test_matrix = base_matrix.Deep_Copy(
            base_matrix.matrix_idx,
            copy_raw_FER=True,
            copy_seed_FER=True
        )

        # 새로운 그룹 순서 구성
        # 1. 재배열 대상이 아닌 영역 (first_reorder_idx 이전): 모든 그룹 유지 (restart 포함)
        # 2. 재배열 영역: fixed_order + [restart (선택)] + candidate + remaining

        new_groups = []
        new_types = []
        restart_group_indices = []  # 1-based indices

        # 첫 번째 재배열 대상 그룹의 실제 인덱스 (0-based)
        first_reorder_idx = original_reorder_indices[0]

        # 유지 영역의 모든 그룹 (normal + restart) 복사
        for i in range(first_reorder_idx):
            new_groups.append(base_matrix.groups[i])
            new_types.append(base_matrix.header.type_each_group[i])
            # 기존 restart 그룹 위치 기록
            if (i + 1) in base_matrix.restart_groups:
                restart_group_indices.append(len(new_groups))  # 1-based

        # 재배열 영역: fixed_order 그룹들 추가
        for group_idx in fixed_order:
            new_groups.append(base_matrix.groups[group_idx])
            new_types.append(base_matrix.header.type_each_group[group_idx])

        # restart 그룹 추가 (with_restart=True일 때만)
        restart_inserted_idx = None
        if with_restart:
            # 이전 그룹의 iter_end 확인
            if new_groups:
                prev_group = new_groups[-1]
                prev_iter_end = prev_group[0].iter_end
                floor_flag = prev_group[0].floor_flag
            else:
                prev_iter_end = 0
                floor_flag = -1

            # restart 그룹 생성
            len_row = base_matrix.header.num_parameter_each_set * base_matrix.header.num_dv
            restart_group = self._create_restart_group(
                iter_start=prev_iter_end + 1,
                floor_flag=floor_flag,
                num_parameters=len_row
            )
            new_groups.append(restart_group)
            new_types.append(0)  # restart 그룹의 type
            restart_inserted_idx = len(new_groups)  # 1-based

        # candidate 그룹 추가
        new_groups.append(base_matrix.groups[candidate_group_idx])
        new_types.append(base_matrix.header.type_each_group[candidate_group_idx])

        # remaining에서 candidate를 제외한 나머지 (원래 순서대로)
        remaining_in_original_order = [
            idx for idx in original_reorder_indices
            if idx in remaining_pool and idx != candidate_group_idx
        ]
        for group_idx in remaining_in_original_order:
            new_groups.append(base_matrix.groups[group_idx])
            new_types.append(base_matrix.header.type_each_group[group_idx])

        # 그룹 배열 교체
        test_matrix.groups = new_groups

        # iteration 범위 재계산
        # first_reorder_idx부터의 모든 그룹에 대해 iteration을 재계산
        if first_reorder_idx < len(new_groups):
            # 이전 그룹의 마지막 iteration
            if first_reorder_idx > 0:
                prev_iter_end = new_groups[first_reorder_idx - 1][0].iter_end
            else:
                prev_iter_end = 0

            # 마지막 그룹의 원래 iter_end (전체 범위)
            original_last_group = base_matrix.groups[-1]
            total_iter_end = original_last_group[0].iter_end

            total_available = total_iter_end - prev_iter_end

            self._recalculate_iterations_for_reorder(
                new_groups,
                first_reorder_idx,
                total_available
            )

        # restart_groups 리스트 업데이트
        # restart_group_indices에 이미 유지 영역의 restart들이 기록되어 있음
        # 새로 추가된 restart 그룹만 추가
        if restart_inserted_idx is not None:
            restart_group_indices.append(restart_inserted_idx)

        test_matrix.restart_groups = sorted(restart_group_indices)

        # 헤더 정보 업데이트
        test_matrix.header.num_row_each_group = np.array([len(g) for g in new_groups])
        test_matrix.header.type_each_group = np.array(new_types)
        test_matrix.header.num_group = len(new_groups)

        return test_matrix

    def Gen_LLR_Swap_Row(self, input_matrix: Optional[LLR_MATRIX]) -> Optional[LLR_MATRIX]:
        """
        Target group 내의 두 row를 선택하여 ch_th_values만 swap한다.
        - csw, iteration은 고정
        - restart group은 Initialize_Stage에서 이미 skip됨 (SKIP_RESTART_GROUP)
        - trial 수는 target group 내 C(m, 2)
        """
        if input_matrix is None:
            error_msg = "Gen_LLR_Swap_Row: Matrix must not be None."
            self.MPI_Abort(error_msg)

        # 1. Target group에서 row pair 수집

        # Target group 인덱스 가져오기 (current_target_group_idx 사용)
        group_idx = self.current_target_group_idx
        if group_idx == -1:
            group_idx = len(input_matrix.groups) - 1
        group = input_matrix.groups[group_idx]

        if len(group) < 2:
            error_msg = f"Gen_LLR_Swap_Row: Target group {group_idx} has less than 2 rows"
            self.Write_Log_Lines(f"\t- {error_msg}")
            return None

        # Target group 내의 모든 row pair 조합
        all_row_pairs = list(itertools.combinations(range(len(group)), 2))  # [(row_i, row_j), ...]

        if not all_row_pairs:
            error_msg = "Gen_LLR_Swap_Row: No valid row pairs found"
            self.Write_Log_Lines(f"\t- {error_msg}")
            return None

        total_combinations = len(all_row_pairs)

        if self.current_trial_idx > total_combinations:
            self.Write_Log_Lines(f"\t- Trial {self.current_trial_idx} exceeds available row pairs {total_combinations}")
            return None

        # 2. current_trial_idx에 해당하는 pair 선택
        row_i_idx, row_j_idx = all_row_pairs[self.current_trial_idx - 1]

        group = input_matrix.groups[group_idx]
        row_i = group[row_i_idx]
        row_j = group[row_j_idx]

        # 3. Swap 전 정보 저장 (로그용)
        old_row_i_ch_th = np.array(row_i.ch_th_values, copy=True)
        old_row_j_ch_th = np.array(row_j.ch_th_values, copy=True)

        # 4. ch_th_values만 swap (HD 복호의 HBF 구간 row는 dv_idx 0의 TH를 빼고 바꾼다)
        new_row_i_ch_th = np.array(row_j.ch_th_values, copy=True)
        new_row_j_ch_th = np.array(row_i.ch_th_values, copy=True)
        for col_idx in input_matrix.Get_Columns_Fixed_In_HBF_Iterations(row_i.iter_end):
            new_row_i_ch_th[col_idx] = row_i.ch_th_values[col_idx]
            new_row_j_ch_th[col_idx] = row_j.ch_th_values[col_idx]
        row_i.ch_th_values = new_row_i_ch_th
        row_j.ch_th_values = new_row_j_ch_th

        # 5. 로그 출력
        log_lines = [
            f"\t- Swapped rows in Group {group_idx} (1-based: {group_idx + 1})",
            f"\t- Row {row_i_idx} <-> Row {row_j_idx}",
            f"\t- CSW and iteration preserved",
            f"\t- Trial {self.current_trial_idx}/{total_combinations} combinations"
        ]

        # Row i 상세 정보 (Before -> After)
        old_i_str = ", ".join(map(str, old_row_i_ch_th.tolist()))
        new_i_str = ", ".join(map(str, row_i.ch_th_values.tolist()))
        log_lines.append(f"\t- Row {row_i_idx} BEFORE: CSW: {row_i.CSW:4d}, Ch/Th: [{old_i_str}]")
        log_lines.append(f"\t- Row {row_i_idx} AFTER:  CSW: {row_i.CSW:4d}, Ch/Th: [{new_i_str}]")

        # Row j 상세 정보 (Before -> After)
        old_j_str = ", ".join(map(str, old_row_j_ch_th.tolist()))
        new_j_str = ", ".join(map(str, row_j.ch_th_values.tolist()))
        log_lines.append(f"\t- Row {row_j_idx} BEFORE: CSW: {row_j.CSW:4d}, Ch/Th: [{old_j_str}]")
        log_lines.append(f"\t- Row {row_j_idx} AFTER:  CSW: {row_j.CSW:4d}, Ch/Th: [{new_j_str}]")

        self.Write_Log_Lines(log_lines)

        return input_matrix

    def Get_Ref_C_Args(self, matrix_idx: int, ch_idx: int = 0):
        if REFC_CONFIG.ECC_VER == "2.4":
            args = [
                REFC_CONFIG.matrix_sel,              #1
                REFC_CONFIG.init_n,                  #2
                REFC_CONFIG.ch_type,                 #3
                REFC_CONFIG.RBERs[ch_idx],           #4
                REFC_CONFIG.num_fixed_errs[ch_idx],  #5
                REFC_CONFIG.fixed_SCRs[ch_idx],      #6
                REFC_CONFIG.fixed_SERs[ch_idx],      #7
                REFC_CONFIG.fixed_erasure_ratios[ch_idx],   #8
                REFC_CONFIG.fn,                      #9
                REFC_CONFIG.max_num_test,            #10
                self.current_seed_mode.value,       #11
                self.rank,                          #12
                REFC_CONFIG.CRC_Option_F_P,          #13
                REFC_CONFIG.mode_iter,               #14
                REFC_CONFIG.CRC_skip_mode,           #15
                REFC_CONFIG.HighDV_skip_mode,        #16
                matrix_idx,                         #17
                self.enable_print_CSW_log,          #18
            ]
            if REFC_CONFIG.str_matrix_name:
                args.append(REFC_CONFIG.str_matrix_name)  #19
        else:
            args = [
                REFC_CONFIG.matrix_sel,    #1
                REFC_CONFIG.init_n,        #2
                REFC_CONFIG.ch_type, #3
                REFC_CONFIG.RBERs[ch_idx],
                REFC_CONFIG.num_fixed_errs[ch_idx],
                REFC_CONFIG.fixed_SCRs[ch_idx],     #6
                REFC_CONFIG.fixed_SERs[ch_idx],     #7
                REFC_CONFIG.fixed_erasure_ratios[ch_idx],   #8
                REFC_CONFIG.fn,            #9
                REFC_CONFIG.max_num_test,  #10
                self.current_seed_mode.value,   #11
                self.rank,    #12
                REFC_CONFIG.mode_all_one_cw,   #13
                REFC_CONFIG.CRC_Option_F_P,    #14
                REFC_CONFIG.mode_iter,         #15
                REFC_CONFIG.mode_scenario,     #16
                matrix_idx,                   #17
                self.enable_print_CSW_log,    #18
            ]
            if REFC_CONFIG.str_matrix_name:
                args.append(REFC_CONFIG.str_matrix_name)  #19
        return args

    def Get_Ref_C_Args_For_Speed_Test(self, matrix_idx: int, ch_idx: int = 0):
        """코어 속도 테스트용 인자 생성 (SPEED_TEST_REFC_CONFIG 사용, 고정 시드)"""
        if SPEED_TEST_REFC_CONFIG.ECC_VER == "2.4":
            args = [
                SPEED_TEST_REFC_CONFIG.matrix_sel,              #1
                SPEED_TEST_REFC_CONFIG.init_n,                  #2
                SPEED_TEST_REFC_CONFIG.ch_type,                 #3
                SPEED_TEST_REFC_CONFIG.RBERs[ch_idx],           #4
                SPEED_TEST_REFC_CONFIG.num_fixed_errs[ch_idx],  #5
                SPEED_TEST_REFC_CONFIG.fixed_SCRs[ch_idx],      #6
                SPEED_TEST_REFC_CONFIG.fixed_SERs[ch_idx],      #7
                SPEED_TEST_REFC_CONFIG.fixed_erasure_ratios[ch_idx],   #8
                SPEED_TEST_REFC_CONFIG.fn,                      #9
                SPEED_TEST_REFC_CONFIG.max_num_test,            #10
                SPEED_TEST_REFC_CONFIG.mode_seed,           #11 
                SPEED_TEST_REFC_CONFIG.mode_init_seed,          #12 (고정 시드, 모든 rank 동일)
                SPEED_TEST_REFC_CONFIG.CRC_Option_F_P,          #13
                SPEED_TEST_REFC_CONFIG.mode_iter,               #14
                SPEED_TEST_REFC_CONFIG.CRC_skip_mode,           #15
                SPEED_TEST_REFC_CONFIG.HighDV_skip_mode,        #16
                matrix_idx,                         #17
                0,                                  #18 (CSW 로그 비활성화)
            ]
            if SPEED_TEST_REFC_CONFIG.str_matrix_name:
                args.append(SPEED_TEST_REFC_CONFIG.str_matrix_name)  #19
        else:
            args = [
                SPEED_TEST_REFC_CONFIG.matrix_sel,    #1
                SPEED_TEST_REFC_CONFIG.init_n,        #2
                SPEED_TEST_REFC_CONFIG.ch_type, #3
                SPEED_TEST_REFC_CONFIG.RBERs[ch_idx],
                SPEED_TEST_REFC_CONFIG.num_fixed_errs[ch_idx],
                SPEED_TEST_REFC_CONFIG.fixed_SCRs[ch_idx],     #6
                SPEED_TEST_REFC_CONFIG.fixed_SERs[ch_idx],     #7
                SPEED_TEST_REFC_CONFIG.fixed_erasure_ratios[ch_idx],   #8
                SPEED_TEST_REFC_CONFIG.fn,            #9
                SPEED_TEST_REFC_CONFIG.max_num_test,  #10
                SPEED_TEST_REFC_CONFIG.mode_seed,               #11
                SPEED_TEST_REFC_CONFIG.mode_init_seed,          #12 (고정 시드, 모든 rank 동일)
                SPEED_TEST_REFC_CONFIG.mode_all_one_cw,   #13
                SPEED_TEST_REFC_CONFIG.CRC_Option_F_P,    #14
                SPEED_TEST_REFC_CONFIG.mode_iter,         #15
                SPEED_TEST_REFC_CONFIG.mode_scenario,     #16
                matrix_idx,                   #17
                0,                            #18 (CSW 로그 비활성화)
            ]
            if SPEED_TEST_REFC_CONFIG.str_matrix_name:
                args.append(SPEED_TEST_REFC_CONFIG.str_matrix_name)  #19
        return args

    def Make_Batch_File_For_Speed_Test(self, matrix, ch_idx: int = 0):
        """코어 속도 테스트용 배치 파일 생성 (고정 시드 사용)"""
        batch_dir = self.local_session_dir
        batch_file_name = f"speed_test_{self.rank}.bat" if CURRENT_OS is OperatingSystem.WINDOWS else f"speed_test_{self.rank}.sh"
        batch_path = os.path.join(batch_dir, batch_file_name)
        args = self.Get_Ref_C_Args_For_Speed_Test(matrix_idx=matrix.matrix_idx, ch_idx=ch_idx)

        arg_lst = [str(arg) for arg in args]
        if CURRENT_OS is OperatingSystem.WINDOWS:
            exe_command = f"\"{PATH_CONFIG.ECC_EXE_NAME}\""
        else:
            exe_command = f"./{PATH_CONFIG.ECC_EXE_NAME}"
        command_line = f"{exe_command} {' '.join(arg_lst)}"

        try:
            with open(batch_path, "w", encoding="utf-8", newline="\n") as batch_file:
                if CURRENT_OS is OperatingSystem.WINDOWS:
                    batch_file.write("@echo off\n\n")
                    batch_file.write('cd /d "%~dp0"\n')
                    batch_file.write(f"{command_line}\n")
                else:
                    batch_file.write("#!/usr/bin/env bash\n")
                    batch_file.write("set -euo pipefail\n")
                    batch_file.write('cd "$(dirname "$0")"\n')
                    batch_file.write(f"{command_line}\n")
            if CURRENT_OS is not OperatingSystem.WINDOWS:
                os.chmod(batch_path, 0o755)
        except OSError as error:
            self.MPI_Abort(f"Failed to create speed test batch file: {error}")

        self.batch_path = batch_path

    def Make_Batch_File(self, matrix, ch_idx :int = 0):
        batch_dir = self.local_session_dir
        batch_file_name = PATH_CONFIG.BATCH_FILE_TEMPLATE.format(
            matrix_sel=REFC_CONFIG.matrix_sel,
            init_n=REFC_CONFIG.init_n,
            process_idx=self.rank,
        )
        batch_path = os.path.join(batch_dir, batch_file_name)
        args = self.Get_Ref_C_Args(matrix_idx=matrix.matrix_idx, ch_idx=ch_idx)

        arg_lst = [str(arg) for arg in args]
        if CURRENT_OS is OperatingSystem.WINDOWS:
            exe_command = f"\"{PATH_CONFIG.ECC_EXE_NAME}\""
        else:
            exe_command = f"./{PATH_CONFIG.ECC_EXE_NAME}"
        command_line = f"{exe_command} {' '.join(arg_lst)}"

        try:
            with open(batch_path, "w", encoding="utf-8", newline="\n") as batch_file:
                if CURRENT_OS is OperatingSystem.WINDOWS:
                    batch_file.write("@echo off\n\n")
                    batch_file.write('cd /d "%~dp0"\n')
                    batch_file.write(f"{command_line}\n")
                else:
                    batch_file.write("#!/usr/bin/env bash\n")
                    batch_file.write("set -euo pipefail\n")
                    batch_file.write('cd "$(dirname "$0")"\n')
                    batch_file.write(f"{command_line}\n")
            if CURRENT_OS is not OperatingSystem.WINDOWS:
                os.chmod(batch_path, 0o755)
        except OSError as error:
            self.MPI_Abort(f"Failed to create batch file: {error}")

        self.batch_path = batch_path

    def Make_Dirs(self):
        """세션에 필요한 디렉터리를 생성한다.
        """
        if PATH_CONFIG.WORK_SPACE_DIR is None:
            error_msg = "Make_Dirs: WORK_SPACE_DIR is not set."
            self.MPI_Abort(error_msg)
        self.work_space_dir = PATH_CONFIG.WORK_SPACE_DIR

        args_suffix = "".join(f"_{arg}" for arg in self.input_args)
        self.session_dir = os.path.join(
            self.work_space_dir,
            f"DAO_{self.session_timestamp}_{self.Get_Decoder_Mode_Str()}{args_suffix}",
        )

        self.trial_output_dir = os.path.join(self.session_dir, TRIAL_LLR_MATRIX_DIR_NAME)
        self.optimal_output_dir = os.path.join(self.session_dir, OPTIMAL_LLR_MATRIX_DIR_NAME)
        self.session_logs_dir = os.path.join(self.session_dir, LOG_DIR_NAME)
        self.session_error_dir = os.path.join(self.session_dir, ERROR_LLR_MATRIX_DIR_NAME)
        if DEBUG_CONFIG.IS_DEBUG_PAUSE_PRINT_SNAPSHOT:
            self.session_debug_snapshot_dir = os.path.join(self.session_dir, DEBUG_DIR_NAME)
        self.src_backup_dir = os.path.join(self.session_dir, SRC_BACKUP_DIR_NAME)
        self.session_uncor_dir = os.path.join(self.session_dir, SESSION_UNCOR_DIR_NAME)
        self.local_session_dir = os.path.join(self.session_dir, PATH_CONFIG.LOCAL_SESSION_DIR_NAME_TEMPLATE.format(process_idx=self.rank))
        self.end_flag_dir = os.path.join(self.session_dir, END_FLAG_DIR_NAME)
    
        if self.is_root:
            os.makedirs(self.work_space_dir, exist_ok=True)
            os.makedirs(self.session_dir, exist_ok=True)
            os.makedirs(self.trial_output_dir, exist_ok=True)
            os.makedirs(self.optimal_output_dir, exist_ok=True)
            os.makedirs(self.session_logs_dir, exist_ok=True)
            os.makedirs(self.session_error_dir, exist_ok=True)
            os.makedirs(self.src_backup_dir, exist_ok=True)
            os.makedirs(self.session_uncor_dir, exist_ok=True)
            os.makedirs(self.end_flag_dir, exist_ok=True)
            os.makedirs(PATH_CONFIG.INPUT_ECC_EXE_DIR_PATH, exist_ok=True)
            if DEBUG_CONFIG.IS_DEBUG_PAUSE_PRINT_SNAPSHOT:
                if self.session_debug_snapshot_dir is not None:
                    os.makedirs(self.session_debug_snapshot_dir, exist_ok=True)

        self.MPI_Barrier()
        os.makedirs(self.local_session_dir, exist_ok=True)
        os.makedirs(self.session_uncor_dir, exist_ok=True)

        # Trial/DAO 종료 플래그 초기화 (세션 시작 시 1회, "0"으로 생성)
        self.Initialize_End_Flags()
        self.MPI_Barrier()

    def Make_Log_Backup(self):
        """로그 파일 백업을 만든다.

        최대 라인 수를 초과한 경우 현재 로그 파일을 rename(종료 idx 추가)���고 새 파일로 전환한다.
        파일명 형식: 2026.02.15__15.20.30___LLR_MATRIX_from_0_to_150.txt

        Args:
            없음.

        Returns:
            None
        """
        if (not self.is_root) or self.log_file_path is None or not os.path.exists(self.log_file_path):
            return

        # 이전 로그 파일 rename (종료 idx 추가 + update 여부 반영)
        end_idx = self.current_LLR_matrix_idx
        new_name = self.Get_Log_File_Name(self.log_create_time, self.log_start_matrix_idx, end_idx, has_update=self.log_has_update)
        renamed_log_path = os.path.join(self.session_logs_dir, new_name)
        try:
            os.rename(self.log_file_path, renamed_log_path)
        except OSError as e:
            if self._in_mpi_abort:
                _write_error_log(self.rank, e)
                self.comm.Abort(1)
                return
            self.MPI_Abort(f"Make_Log_Backup: os.rename failed: {e}")

        # 새 로그 파일 생성
        self.log_line_count = 0
        self.log_has_update = False
        self.log_create_time = datetime.datetime.now()
        self.log_start_matrix_idx = self.current_LLR_matrix_idx

        log_file_name = self.Get_Log_File_Name(self.log_create_time, self.log_start_matrix_idx)
        self.log_file_path = os.path.join(self.session_logs_dir, log_file_name)
        self.Write_Log_Lines(f"[LLR_OPT] Previous log archived to {renamed_log_path}")

    def Finalize_Log(self):
        """프로그램 종료 시 마지막 로그 파일을 rename한다.

        현재 로그 파일에 종료 matrix idx를 추가하여 최종 파일명으로 변경한다.
        파일명 형식: 2026.02.15__15.20.30___LLR_MATRIX_from_0_to_150.txt

        Args:
            없음.

        Returns:
            None
        """
        if (not self.is_root) or self.log_file_path is None or not os.path.exists(self.log_file_path):
            return

        # 마지막 로그 파일 rename (종료 idx 추가 + update 여부 반영)
        end_idx = self.current_LLR_matrix_idx
        new_name = self.Get_Log_File_Name(self.log_create_time, self.log_start_matrix_idx, end_idx, has_update=self.log_has_update)
        renamed_log_path = os.path.join(self.session_logs_dir, new_name)
        try:
            os.rename(self.log_file_path, renamed_log_path)
        except OSError as e:
            _write_error_log(self.rank, e)
            return
        self.log_file_path = renamed_log_path

    def MPI_Barrier(self) -> None:
        """
        Synchronize all ranks while tracking and logging how many MPI barriers each
        process has passed so far.
        """
        self._mpi_comm_with_timeout(
            self.comm.Barrier,
            timeout_seconds=TIME_CONFIG.MPI_TEST_BARRIER_TIMEOUT_SECONDS,
            comm_name=f"MPI_Barrier[{self.barrier_count}]"
        )
        self.barrier_count += 1  # 성공 후에만 증가


    def Check_Barrier_Sync(self, tag: str = "") -> None:
        """
        모든 프로세스의 barrier count가 동기화되어 있는지 확인한다.

        bcast를 사용하여 rank 0의 barrier_count를 모든 프로세스에 전송하고,
        각 프로세스가 동일한 barrier_count를 가지고 있는지 확인한다.
        불일치 시 MPI_Abort로 종료한다.

        Args:
            tag (str): 로그 식별을 돕는 추가 태그 (예: "Stage start", "Trial start")

        Returns:
            None
        """
        # rank 0의 barrier_count를 모든 프로세스에 broadcast
        root_barrier_count = self._mpi_comm_with_timeout(
            self.comm.bcast,
            self.barrier_count if self.is_root else None,
            root=0,
            comm_name=f"Check_Barrier_Sync[{tag}]"
        )

        # 각 프로세스의 barrier_count와 비교
        if self.barrier_count != root_barrier_count:
            error_msg = (
                f"Barrier count mismatch detected at {tag}!\n"
                f"\t- rank {self.rank} barrier_count: {self.barrier_count}\n"
                f"\t- root barrier_count: {root_barrier_count}\n"
                f"\t- Difference: {self.barrier_count - root_barrier_count}"
            )
            self.MPI_Abort(error_msg)

        # Debug 모드일 때만 상세 로그 출력
        if DEBUG_CONFIG.ENABLE_MPI_DEBUG_LOGGING:
            counts: list[int] = self._mpi_comm_with_timeout(
                self.comm.allgather,
                self.barrier_count,
                comm_name=f"Check_Barrier_Sync_AllGather[{tag}]"
            )
            if self.is_root:
                tag_suffix = f"[{tag}]" if tag else ""
                counts_lines = "\n".join(f"\t-rank {idx}: {count}" for idx, count in enumerate(counts))
                message = f"{tag_suffix} Barrier count synchronized:\n{counts_lines}"
                self.Write_Log_Lines(message)

    def Write_MPI_Error_Snapshot(self, exception: Exception, context: str):
        """MPI 에러 발생 시 현재 상태 snapshot을 error_logs에 기록한다.

        root는 항상 기록하고, 워커는 MPI 통신 오류 시에만 기록한다. (Hybrid 방식)

        Args:
            exception (Exception): 발생한 예외 객체
            context (str): 에러 발생 위치/컨텍스트 (함수명 등)
        """
        if not self.is_root:
            comm_keywords = ["bcast", "gather", "barrier", "comm"]
            if not any(kw in context.lower() for kw in comm_keywords):
                return

        try:
            os.makedirs(self.session_error_dir, exist_ok=True)
            error_log_path = os.path.join(self.session_error_dir, f"error_snapshot_rank{self.rank}.log")

            with open(error_log_path, "a", encoding="utf-8") as log_file:
                log_file.write("=" * 80 + "\n")
                log_file.write(f"MPI ERROR SNAPSHOT - {self.Get_Timestamp()}\n")
                log_file.write("=" * 80 + "\n\n")

                log_file.write(f"Context: {context}\n")
                log_file.write(f"Exception Type: {type(exception).__name__}\n")
                log_file.write(f"Exception Message: {exception}\n\n")

                log_file.write(f"--- Current State (Rank {self.rank}) ---\n")
                log_file.write(f"current_stage_idx: {getattr(self, 'current_stage_idx', 'NOT SET')}\n")
                log_file.write(f"current_trial_idx: {getattr(self, 'current_trial_idx', 'NOT SET')}\n")
                log_file.write(f"current_LLR_matrix_idx: {getattr(self, 'current_LLR_matrix_idx', 'NOT SET')}\n")
                log_file.write(f"is_root: {self.is_root}\n")
                log_file.write(f"rank: {self.rank}\n")
                log_file.write(f"num_process: {self.num_process}\n")
                log_file.write(f"barrier_count: {getattr(self, 'barrier_count', 'NOT SET')}\n\n")

                log_file.write(f"--- Trial LLR Mode State ---\n")
                log_file.write(f"current_gen_trial_LLR_mode: {getattr(self, 'current_gen_trial_LLR_mode', 'NOT SET')}\n")
                log_file.write(f"current_gen_trial_LLR_mode (type): {type(getattr(self, 'current_gen_trial_LLR_mode', None))}\n")
                log_file.write(f"current_gen_trial_LLR_mode_name: {getattr(self, 'current_gen_trial_LLR_mode_name', 'NOT SET')}\n")
                log_file.write(f"max_modification_trial: {getattr(self, 'max_modification_trial', 'NOT SET')}\n")
                log_file.write(f"current_target_group_idx: {getattr(self, 'current_target_group_idx', 'NOT SET')}\n\n")

                log_file.write(f"--- Matrix State ---\n")
                if hasattr(self, 'optimal_LLR_matrix') and self.optimal_LLR_matrix:
                    log_file.write(f"optimal_LLR_matrix exists: True\n")
                    log_file.write(f"optimal_LLR_matrix.groups count: {len(self.optimal_LLR_matrix.groups) if hasattr(self.optimal_LLR_matrix, 'groups') else 'NO GROUPS'}\n")
                    log_file.write(f"optimal_LLR_matrix.FERs: {self.optimal_LLR_matrix.FERs if hasattr(self.optimal_LLR_matrix, 'FERs') else 'NO FERs'}\n")
                else:
                    log_file.write(f"optimal_LLR_matrix: NOT SET or None\n")

                log_file.write("\n" + "=" * 80 + "\n\n")

        except Exception as log_error:
            # snapshot 기록 실패 시에도 계속 진행
            print(f"[Warning] Failed to write error snapshot: {log_error}", flush=True)

    def MPI_Abort(self, error_msg: str, error_code: int = 1) -> NoReturn:
        """MPI 환경에서 에러 발생 시 모든 프로세스를 강제 종료한다.

        Args:
            error_msg (str): 에러 메시지
            error_code (int): 종료 코드 (기본값: 1)
        """
        if self._in_mpi_abort:
            # 재진입 방지: MPI_Abort → Write_Log_Lines → MPI_Abort 무한 재귀 차단
            print(f"[Rank {self.rank}] MPI_Abort re-entered: {error_msg}", flush=True)
            self.comm.Abort(error_code)
            return  # comm.Abort() 이후 도달 불가이나 방어적 배치
        self._in_mpi_abort = True

        error_prefix = f"[Rank {self.rank}] MPI_Abort: "
        full_error_msg = error_prefix + error_msg

        # 에러 메시지를 로그에 기록 (가능한 경우)
        try:
            self.Write_Log_Lines(full_error_msg)
        except Exception as e:
            _write_error_log(self.rank, e)

        # 콘솔에도 출력
        print(full_error_msg, flush=True)

        # 에러 상태를 상세 로그로 기록 (호출 스택 포함)
        try:
            error_dir = None
            if getattr(self, "session_dir", None):
                error_dir = os.path.join(self.session_dir, ERROR_LOG_DIR_NAME)
            else:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
                error_dir = os.path.join(base_dir, ERROR_LOG_DIR_NAME)

            os.makedirs(error_dir, exist_ok=True)
            log_path = os.path.join(error_dir, ERROR_LOG_FILE_TEMPLATE.format(process_idx=self.rank))
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 호출 스택 정보 수집 (MPI_Abort를 호출한 위치부터)
            stack_info = []
            for frame_info in inspect.stack()[1:]:  # [0]은 MPI_Abort 자신이므로 제외
                filename = os.path.basename(frame_info.filename)
                func_name = frame_info.function
                lineno = frame_info.lineno
                code_context = frame_info.code_context[0].strip() if frame_info.code_context else ""

                # 로컬 변수 수집
                frame_locals = {}
                for key, value in frame_info.frame.f_locals.items():
                    if key == "self":
                        continue
                    if callable(value):
                        continue
                    try:
                        frame_locals[key] = _summarize_value(value)
                    except Exception as error:
                        frame_locals[key] = f"<summary failed: {error!r}>"

                stack_info.append({
                    "file": filename,
                    "function": func_name,
                    "line": lineno,
                    "code": code_context,
                    "locals": frame_locals
                })

            # 클래스 인스턴스 상태 수집 (스택은 이미 위에서 수집했으므로 제외)
            state_text = self._collect_error_state_snapshot(include_stack=False)

            # 로그 파일에 작성
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write("=" * 80 + "\n")
                log_file.write(f"[{timestamp}] MPI_Abort called on process {self.rank}\n")
                log_file.write("-" * 80 + "\n")
                log_file.write(f"Error Message: {full_error_msg}\n\n")

                log_file.write("Call Stack (most recent call first):\n")
                for idx, frame in enumerate(stack_info):
                    log_file.write(f"\n  [{idx}] File \"{frame['file']}\", line {frame['line']}, in {frame['function']}\n")
                    log_file.write(f"      {frame['code']}\n")
                    if frame['locals']:
                        log_file.write(f"      Local variables:\n")
                        for var_name, var_value in frame['locals'].items():
                            log_file.write(f"        {var_name} = {var_value}\n")

                log_file.write(f"\n{state_text}\n")
                log_file.write("=" * 80 + "\n\n")

        except Exception as log_error:
            # 로깅 실패 시에도 MPI_Abort는 계속 진행
            print(f"[Warning] Failed to write error log: {log_error}", flush=True)

        # 모든 MPI 프로세스 강제 종료
        self.comm.Abort(error_code)

    def _mpi_comm_with_timeout(self, comm_func, *args, timeout_seconds=None, comm_name="MPI communication", **kwargs):
        """MPI 통신 함수를 타임아웃과 함께 실행한다.

        별도의 watchdog thread를 사용하여 타임아웃을 감시하고,
        지정된 시간 내에 완료되지 않으면 MPI_Abort를 호출한다.

        Args:
            comm_func: 실행할 MPI 통신 함수 (예: self.comm.bcast, self.comm.gather)
            *args: comm_func에 전달할 positional arguments
            timeout_seconds (float, optional): 타임아웃 시간(초). None이면 설정값 사용
            comm_name (str): 통신 이름 (로그용)
            **kwargs: comm_func에 전달할 keyword arguments

        Returns:
            MPI 통신 함수의 반환값
        """
        # 타임아웃 시간 설정
        if timeout_seconds is None:
            timeout_seconds = TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS

        # 결과 저장용
        result: list[Any] = [None]
        exception: list[Optional[Exception]] = [None]
        completed = threading.Event()

        def comm_thread():
            """MPI 통신을 실행하는 thread"""
            try:
                result[0] = comm_func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
            finally:
                completed.set()

        # 통신 thread 시작
        thread = threading.Thread(target=comm_thread, daemon=True)
        thread.start()

        # 타임아웃까지 대기
        if not completed.wait(timeout=timeout_seconds):
            # 타임아웃 발생
            error_msg = f"{comm_name} timed out after {timeout_seconds} seconds. This usually indicates a deadlock or network issue."
            self.MPI_Abort(error_msg)

        # 예외 발생 시 재발생
        if exception[0] is not None:
            raise exception[0]

        return result[0]

    def _safe_bcast(self, data, comm_name: str = "bcast", root: int = 0):
        """MPI bcast를 예외 처리와 함께 실행한다.

        예외 발생 시 root에서 상태 스냅샷을 기록하고 MPI_Abort를 호출한다.

        Args:
            data: broadcast할 데이터 (root에서만 유효한 값, worker는 None)
            comm_name: 통신 이름 (로그/디버깅용)
            root: broadcast의 root 프로세스 (기본값: 0)

        Returns:
            broadcast된 데이터
        """
        try:
            return self._mpi_comm_with_timeout(
                self.comm.bcast,
                data,
                root=root,
                comm_name=comm_name
            )
        except Exception as e:
            self.Write_MPI_Error_Snapshot(e, comm_name)
            error_msg = f"{comm_name} failed: {type(e).__name__}: {e}"
            self.MPI_Abort(error_msg)

    def _safe_gather(self, data, comm_name: str = "gather", root: int = 0):
        """MPI gather를 예외 처리와 함께 실행한다.

        각 rank의 데이터를 root에 수집한다. numpy 호환성 문제 방지를 위해
        데이터는 Python 기본 자료형(int, float, list)으로 전달해야 한다.

        Args:
            data: 각 rank가 전송할 데이터
            comm_name: 통신 이름 (로그/디버깅용)
            root: 수집 대상 root 프로세스 (기본값: 0)

        Returns:
            root: 모든 rank의 데이터 리스트, non-root: None
        """
        try:
            return self._mpi_comm_with_timeout(
                self.comm.gather,
                data,
                root=root,
                comm_name=comm_name
            )
        except Exception as e:
            self.Write_MPI_Error_Snapshot(e, comm_name)
            error_msg = f"{comm_name} failed: {type(e).__name__}: {e}"
            self.MPI_Abort(error_msg)

    def _safe_allgather(self, data, comm_name: str):
        """모든 rank의 데이터를 모든 rank에 모은다. 타임아웃 감시를 거친다.

        Args:
            data: 각 rank가 전송할 데이터
            comm_name: 통신 이름 (로그/디버깅용)

        Returns:
            모든 rank의 데이터 리스트 (rank 순서)
        """
        try:
            return self._mpi_comm_with_timeout(
                self.comm.allgather,
                data,
                timeout_seconds=TIME_CONFIG.MPI_TEST_BARRIER_TIMEOUT_SECONDS,
                comm_name=comm_name
            )
        except Exception as e:
            self.Write_MPI_Error_Snapshot(e, comm_name)
            error_msg = f"{comm_name} failed: {type(e).__name__}: {e}"
            self.MPI_Abort(error_msg)

    def MPI_Debug_Logging(self, tag: str = ""):
        """MPI debug용이며 barrier count를 출력한다.

        디버그 모드가 활성화된 경우 각 프로세스의 배리어 호출 횟수를 수집해 루트 로그에 기록한다.

        Args:
            tag (str): 로그 식별을 돕는 추가 태그.

        Returns:
            None
        """
        if not DEBUG_CONFIG.ENABLE_MPI_DEBUG_LOGGING:
            return
        
        counts: list[int] = self._safe_allgather(self.barrier_count, "Allgather_barrier_count")
        if not self.is_root:
            return

        tag_suffix = f"[{tag}]" if tag else ""
        counts_lines = "\n".join(f"\t-rank {idx}: {count}" for idx, count in enumerate(counts))
        message = f"{tag_suffix}\n{counts_lines}"

        self.Write_Log_Lines(message)

    def _Get_Target_Group_Idx(self, matrix: LLR_MATRIX) -> Optional[int]:
        """변이할 타겟 그룹의 index. -1과 그룹 수 이상의 값은 마지막 그룹을 뜻한다. 그룹이 없으면 None"""
        if not matrix.groups:
            return None
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1 or target_group_idx >= len(matrix.groups):
            target_group_idx = len(matrix.groups) - 1
        return target_group_idx

    def Generate_Random_Mutation(self, matrix: LLR_MATRIX) -> list[tuple[int, int, int, int, int]]:
        """
        LLR 매트릭스에 적용할 랜덤 mutation을 생성하는 함수.
        - Gen_LLR_Mode_SEQUENCE 한 바퀴당 target_group_indices에서 하나씩 순환하여 타겟 그룹 선택
        - -1이면 마지막 그룹만 대상, 아니면 지정된 그룹만 대상
        - 각 element는 -MUTATION_RANGE ~ +MUTATION_RANGE 범위 내에서 랜덤 delta 생성.
        - 실제 적용은 호출자가 수행한다.

        Args:
            matrix (LLR_MATRIX): mutation 대상 매트릭스 객체

        Returns:
            list[tuple[int, int, int, int, int]]: (group_idx, row_idx, col_idx, old_value, new_value)
        """

        # 타겟 그룹에서 NUM_ELEMENTS_TO_MUTATE_CHTH개까지 고른다
        target_group_idx = self._Get_Target_Group_Idx(matrix)
        if target_group_idx is None:
            return []
        group = matrix.groups[target_group_idx]
        skip_max_row_idx = 0
        if self.now_enable_CSW_update_limit:
            skip_max_row_idx = self.Get_Mutate_Matrix_Skip_Row_Idx(group)

        element_pool = []
        for row_idx, row in enumerate(group):
            if row_idx < skip_max_row_idx:
                continue
            # HD 복호의 HBF 구간 row는 값이 고정되는 column(dv_idx 0의 TH)을 변이 후보에서 뺀다
            fixed_columns = matrix.Get_Columns_Fixed_In_HBF_Iterations(row.iter_end)
            for col_idx in range(len(row.ch_th_values)):
                if col_idx in fixed_columns:
                    continue
                element_pool.append((target_group_idx, row_idx, col_idx))

        num_changes = min(MUTATE_CONFIG.NUM_ELEMENTS_TO_MUTATE_CHTH, len(element_pool))
        if num_changes == 0:
            return []
        chosen = random.sample(element_pool, num_changes)

        # MUTATION_RANGE=0이면 mutation 불가
        if MUTATE_CONFIG.MUTATION_RANGE == 0:
            return []

        # === mutation 생성 (적용은 호출자가 수행) ===
        mutations: list[tuple[int, int, int, int, int]] = []
        for (group_idx, row_idx, col_idx) in chosen:
            delta = 0
            while delta == 0:
                delta = random.randint(-MUTATE_CONFIG.MUTATION_RANGE, MUTATE_CONFIG.MUTATION_RANGE)
            row = matrix.groups[group_idx][row_idx]
            old_value = int(row.ch_th_values[col_idx])
            new_value = old_value + delta
            mutations.append((group_idx, row_idx, col_idx, old_value, new_value))

        return mutations

    def Mutate_Matrix_Setup(self):
        self.Set_CSW_Update_Limit()

    def Mutate_CSW(self, matrix: LLR_MATRIX):
        """
        Gen_LLR_Mode_SEQUENCE 한 바퀴당 target_group_indices에서 하나씩 순환하여 선택된 group의 CSW를
        최대 K개까지 -J ~ +J 범위 내에서 랜덤하게 변경하는 함수
        """

        # 타겟 그룹에서 NUM_ELEMENTS_TO_MUTATE_CSW개까지 row를 고른다. 첫 row(CSW -1)는 제외
        target_group_idx = self._Get_Target_Group_Idx(matrix)
        if target_group_idx is None:
            return []
        element_pool = [(target_group_idx, row_idx) for row_idx in range(1, len(matrix.groups[target_group_idx]))]
        max_changes = min(MUTATE_CONFIG.NUM_ELEMENTS_TO_MUTATE_CSW, len(element_pool))
        if max_changes == 0:
            return []
        num_changes = random.randint(1, max_changes)
        chosen = random.sample(element_pool, num_changes)

        # MUTATION_RANGE=0이면 mutation 불가
        if MUTATE_CONFIG.MUTATION_RANGE == 0:
            return []

        modifications: list[tuple[int, int, int, int]] = []
        for (group_idx, row_idx) in chosen:
            row = matrix.groups[group_idx][row_idx]
            old_CSW = int(row.CSW)
            delta_CSW = 0
            while delta_CSW == 0:
                delta_CSW = random.randint(-MUTATE_CONFIG.MUTATION_RANGE, MUTATE_CONFIG.MUTATION_RANGE) * STEP_CSW
            new_CSW = old_CSW + delta_CSW

            # CSW 값 검증 및 보정
            # 1. 8의 배수로 반올림 (방어적 코딩)
            new_CSW = round(new_CSW / STEP_CSW) * STEP_CSW

            # 2. MIN_CSW(8) ~ MAX_CSW(1024) 범위로 clamp
            new_CSW = max(MIN_CSW, min(new_CSW, MAX_CSW))

            # 3. Decreasing order 유지: prev_row >= new_CSW >= next_row
            # row_idx > 1: prev_row는 row_idx >= 1 (CSW >= 8, row_idx == 0은 CSW = -1이므로 제외)
            if row_idx > 1:
                prev_row = matrix.groups[group_idx][row_idx - 1]
                if new_CSW >= prev_row.CSW:
                    # prev보다 한 단계 아래로 내린다 (엄격 감소 유지)
                    new_CSW = prev_row.CSW - STEP_CSW

            if row_idx < len(matrix.groups[group_idx]) - 1:
                next_row = matrix.groups[group_idx][row_idx + 1]
                if new_CSW <= next_row.CSW:
                    # next보다 한 단계 위로 올린다 (엄격 감소 유지)
                    new_CSW = next_row.CSW + STEP_CSW

            # 4. 최종 범위 재확인
            new_CSW = max(MIN_CSW, min(new_CSW, MAX_CSW))

            row.CSW = new_CSW
            modifications.append((group_idx, row_idx, old_CSW, new_CSW))
        return modifications

    def Get_Mode_Sequence_Str(self) -> str:
        """현재 모드 시퀀스를 문자열로 반환한다. 현재 모드는 따옴표로 강조."""
        sequence = DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE if DAO_CONFIG.IS_HBF_OPT else DAO_CONFIG.Gen_LLR_Mode_SEQUENCE
        current_idx = self.current_gen_trial_LLR_mode_index
        parts = []
        for i, mode in enumerate(sequence):
            if i == current_idx:
                parts.append(f"'{mode}'")
            else:
                parts.append(str(mode))
        return f"({current_idx + 1}/{len(sequence)}) [" + ", ".join(parts) + "]"

    def Get_Target_Group_Indices_Str(self) -> str:
        """타겟 그룹 인덱스 리스트를 문자열로 반환한다. 현재 타겟은 따옴표로 강조."""
        current_list_idx = self.current_target_group_list_index
        parts = []
        for i, idx in enumerate(self.target_group_indices):
            if i == current_list_idx:
                parts.append(f"'{idx}'")
            else:
                parts.append(str(idx))
        return "[" + ", ".join(parts) + "]"

    def Print_Initial_Setup(self):
        self.Write_Log_Separator("Simulation Context", SEPARATOR_TYPE2)
        self.Write_Log_Lines(f"[MPI Process] Total: {self.num_process}")
        self.Print_Configs(CONFIGS)
        self.Write_Log_Separator("Simulation Context Ends", SEPARATOR_TYPE2)

    def Print_Mode_Target_Info(self):
        """현재 모드, 타겟 그룹, 업데이트 플래그 정보를 로그로 출력한다.

        Stage 시작과 Trial 시작에서 공통으로 호출하여 일관된 포맷으로 출력한다.
        """
        self.Write_Log_Lines(f"[current_gen_trial_LLR_mode]: {self.current_gen_trial_LLR_mode_name} ({self.current_gen_trial_LLR_mode})  {self.Get_Mode_Sequence_Str()}")
        self.Write_Log_Lines(f"[target_group_indices]: {self.current_target_group_idx}  {self.Get_Target_Group_Indices_Str()}")
        self.Write_Log_Lines(f"[is_update_at_last_trial]: {self.is_update_at_last_trial}")

    def Print_Stage_Info(self):
        """현재 최적화 단계 정보를 로그로 출력한다.

        단계 번호와 trial 모드, 단계별 주요 매개변수를 정리해 기록한다.

        Args:
            없음.

        Returns:
            None
        """
        self.Write_Log_Separator(
            f"Stage: {self.current_stage_idx} / {DAO_CONFIG.MAX_OPTIMIZATION_STAGE}, {self.current_gen_trial_LLR_mode_name}",
            SEPARATOR_TYPE2
            )
        self.Print_Mode_Target_Info()
        if self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_RANDOM_GROUP:
            self.Print_Config(INSERT_RANDOM_GROUP_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_RANDOM_ROW:
            self.Print_Config(INSERT_RANDOM_ROW_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_MUTATED_GROUP:
            self.Print_Config(INSERT_MUTATED_GROUP_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.INSERT_MUTATED_ROW:
            self.Print_Config(INSERT_MUTATED_ROW_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.MUTATE_MATRIX:
            self.Print_Config(MUTATE_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.MUTATE_CSW:
            self.Print_Config(MUTATE_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.SPLIT_GROUP:
            self.Print_Config(SPLIT_GROUP_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.GEN_INITIAL_GROUP:
            self.Print_Config(GEN_INITIAL_GROUP_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.COPY_GROUP:
            self.Print_Config(COPY_GROUP_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.REGEN_DV:
            self.Print_Config(REGEN_DV_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.REGEN_ROW:
            self.Print_Config(REGEN_ROW_CONFIG)
        elif self.current_gen_trial_LLR_mode == GenLLRMode.COPY_ROWS:
            self.Print_Config(COPY_ROWS_CONFIG)

    def Print_Config(self, config_class):
        """
        주어진 클래스의 모든 상수형 변수를 자동으로 로그 출력
        """
        self.Write_Log_Separator(f"{config_class.__name__}", SEPARATOR_TYPE1)
        for key, value in vars(config_class).items():
            if not key.startswith("__") and not callable(value):
                self.Write_Log_Lines(f"- {key}: {value}")

    def Print_Configs(self, config_classes):
        """
        주어진 클래스들의 모든 상수형 변수를 자동으로 로그 출력
        """
        for cls in config_classes:
            self.Write_Log_Separator(f"{cls.__name__}", SEPARATOR_TYPE1)
            for key, value in vars(cls).items():
                if not key.startswith("__") and not callable(value):
                    self.Write_Log_Lines(f"- {key}: {value}")

    def Print_Final_Optimal_LLR_Results(self):
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            self.Write_Log_Lines(f"[Final optimal LLR matrix] FER: {self.optimal_LLR_matrix.FERs[ch_idx]:.2e}, Avg it.: {self.optimal_LLR_matrix.avg_iterations[ch_idx]:.2f}")

    def Print_LLR_Matrix(self, matrix: Optional[LLR_MATRIX] = None, is_print_optimal: Optional[bool] = False):
        """LLR 매트릭스 내용을 로그파일에 출력한다.

        루트 프로세스에서 파일 이름과 직렬화된 행 내용을 기록해 디버깅 정보를 제공한다.
        optimal_LLR_matrix가 있으면 비교해서 차이 부분에 * 표시

        Args:
            matrix (Optional[LLR_MATRIX]): 출력할 LLR 매트릭스.

        Returns:
            None
        """
        if not self.is_root:
            return
        if is_print_optimal:
            self.Write_Log_Lines(f"\n[Optimal LLR_matrix_file_name]: {matrix.LLR_matrix_file_name}")
        else:
            self.Write_Log_Lines(f"\n[LLR_matrix_file_name]: {matrix.LLR_matrix_file_name}")

        # optimal_LLR_matrix와 비교 (단, 자기 자신을 출력하는 경우는 제외)
        compare_with = None
        if hasattr(self, 'optimal_LLR_matrix') and self.optimal_LLR_matrix:
            # matrix가 optimal_LLR_matrix와 다른 객체일 때만 비교
            if matrix is not self.optimal_LLR_matrix:
                compare_with = self.optimal_LLR_matrix

        lines = matrix.Build_LLR_Matrix_Output_Lines(compare_with=compare_with)
        self.Write_Log_Lines(lines)

    def Process_Uncors(self, is_setup_stage: bool = False, is_uncor_type_seed: bool = True, is_redecoded_uncor: bool = False, should_distribute_uncors=False, test_mode: TestMode = TestMode.FULL, matrix: Optional[LLR_MATRIX] = None):
        """초기 uncor load 혹은 항상 save uncor일때만 동작.
        Uncor seed를 gather 후 분배한다.

        초기 단계와 일반 단계를 구분해 소스 파일을 준비하고 각 프로세스 세션에 동일하게 배포한다.

        Args:
            is_setup_stage (bool): 초기 setup 단계 여부 (INPUT에서 복사).
            is_uncor_type_seed (bool): seed 타입 여부.
            is_redecoded_uncor (bool): redecoded uncor 여부.
            should_distribute_uncors (bool): uncor 분배 여부.
            test_mode (TestMode): TestMode.FULL 또는 TestMode.PARTIAL. Two-stage 모드에서 사용.
                - ENABLE_TWO_STAGE_TEST=False: 무시됨 (UNCOR_MATRIX_IDX 사용)
                - ENABLE_TWO_STAGE_TEST=True, PARTIAL: Dynamic Partial (Partial/ 서브디렉토리)
                - ENABLE_TWO_STAGE_TEST=True, FULL: UNCOR_MATRIX_IDX 사용 (루트)
            matrix (Optional[LLR_MATRIX]): gather 단계에서 uncor를 만든 매트릭스. is_setup_stage=True면 사용하지 않는다.

        Returns:
            None
        """

        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            if is_setup_stage:
                src_path = self.Copy_Uncors(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, test_mode=test_mode)
                self.Write_Log_Lines(f"[Process_Uncors] Copy uncors ({self.Get_Test_Mode_String(test_mode)}) for initial test. ch_idx: {ch_idx}")
            else:
                src_path = self.Gather_And_Archive_Uncors(matrix=matrix, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, is_redecoded_uncor=is_redecoded_uncor, test_mode=test_mode)
                self.Write_Log_Lines(f"[Process_Uncors] Gather local uncors ({self.Get_Test_Mode_String(test_mode)}). ch_idx: {ch_idx}")                
            if should_distribute_uncors:
                self.Distribute_Uncors_To_Local_Session(src_path, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
                self.Write_Log_Lines(f"[Process_Uncors] Distribute uncors for initial test. ch_idx: {ch_idx}")
        self.MPI_Barrier()
        self.total_num_uncors = self._safe_bcast(self.total_num_uncors if self.is_root else None, "Bcast_total_num_uncors")

    def Ensure_Uncors_Loaded(self, test_mode: TestMode):
        """요청한 test_mode에 맞는 uncor가 로드되어 있는지 확인하고, 필요시 로드한다.

        Two-stage 모드에서 partial/full uncor 간 전환을 효율적으로 처리한다.
        - 이미 올바른 uncor가 로드되어 있으면 스킵 (불필요한 복사 방지)
        - 다른 test_mode의 uncor가 필요하면 Process_Uncors 호출하여 전환

        Args:
            test_mode (TestMode): 필요한 uncor 타입 (TestMode.PARTIAL 또는 TestMode.FULL)

        Returns:
            None
        """
        if not UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
            # Two-stage 모드가 아니면 항상 FULL 사용
            if self.current_loaded_test_mode is None:
                # Setup에서 이미 로드되었음
                self.current_loaded_test_mode = TestMode.FULL
            return

        # Two-stage 모드: uncor 전환 필요 여부 확인
        if self.current_loaded_test_mode == test_mode:
            # 이미 올바른 uncor가 로드되어 있음
            return

        # 다른 test_mode의 uncor 로드 필요
        mode_name = self.Get_Test_Mode_String(test_mode)
        prev_mode_name = self.Get_Test_Mode_String(self.current_loaded_test_mode) if self.current_loaded_test_mode else "None"
        self.Write_Log_Lines(f"[Ensure_Uncors_Loaded] Switching uncor: {prev_mode_name} → {mode_name}")

        if self.is_uncor_pool_ready:
            self.Load_Uncors_From_Pool(test_mode)
        else:
            # Fallback: 기존 직렬 방식
            is_uncor_type_seed = (UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED)
            self.Process_Uncors(is_setup_stage=True, is_uncor_type_seed=is_uncor_type_seed,
                               should_distribute_uncors=True, test_mode=test_mode)
            self.current_loaded_test_mode = test_mode

    def _Setup_Uncor_Pool_For_Channel(self, ch_idx: int, is_uncor_type_seed: bool, test_mode: TestMode, src_path: Path):
        """단일 채널/모드에 대해 uncor pool을 생성한다.

        Root가 소스 파일을 읽어 각 active core의 pool 디렉토리에 순차 분배한다.
        예: uncor 39개, active core 5개 → core0~3은 8개, core4는 7개 (앞에서부터 순차 할당).
        코어당 파일을 1회만 열어 한번에 기록한다.

        Args:
            ch_idx: 채널 인덱스.
            is_uncor_type_seed: seed 타입 여부.
            test_mode: PARTIAL 또는 FULL.
            src_path: Copy_Uncors가 반환한 소스 파일 경로.
        """
        if self.is_root:
            pool_has_uncor_list = [False] * self.num_process

            mode_name = self.Get_Test_Mode_String(test_mode)
            # Pool 서브디렉토리: Partial만 별도, Full은 루트
            pool_subdir = "Partial" if test_mode == TestMode.PARTIAL else ""

            if not src_path or not src_path.exists():
                self.Write_Log_Lines(f"[Setup_Uncor_Pool] Uncor source not found for {mode_name} ch_idx={ch_idx}")
            else:
                with src_path.open("r", encoding="utf-8") as f:
                    all_lines = [line.rstrip("\n") for line in f if line.strip()]

                if not all_lines:
                    self.Write_Log_Lines(f"[Setup_Uncor_Pool] No seeds to distribute for {mode_name} ch_idx={ch_idx}")
                else:
                    active_cores = self.active_cores

                    if not active_cores:
                        self.Write_Log_Lines(f"⚠️ No active cores for uncor pool distribution.")
                    else:
                        num_uncors = int(len(all_lines) / UNCOR_CONFIG.NUM_LINES_PER_UNCOR)
                        lines_per_uncor = UNCOR_CONFIG.NUM_LINES_PER_UNCOR
                        num_active = len(active_cores)
                        base_count = num_uncors // num_active
                        remainder = num_uncors % num_active

                        uncor_offset = 0
                        for core_idx, target_proc in enumerate(active_cores):
                            count = base_count + (1 if core_idx < remainder else 0)
                            if count == 0:
                                continue

                            pool_has_uncor_list[target_proc] = True

                            pool_base = Path(self.Get_Local_Session_Dir(target_proc)) / UNCOR_POOL_DIR_NAME
                            dest_dir = pool_base / pool_subdir if pool_subdir else pool_base
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest_file_name = self.Get_Uncor_File_Name(process_idx=target_proc, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
                            dest_path = dest_dir / dest_file_name

                            start_line = uncor_offset * lines_per_uncor
                            end_line = (uncor_offset + count) * lines_per_uncor
                            try:
                                with dest_path.open("w", encoding="utf-8") as f:
                                    for line in all_lines[start_line:end_line]:
                                        f.write(line + "\n")
                            except OSError as e:
                                self.MPI_Abort(f"_Setup_Uncor_Pool_For_Channel: 풀 파일 쓰기 실패 — {dest_path}: {e}")

                            uncor_offset += count

                        excluded_info = f" (제외된 코어: {len(self.excluded_cores)}개)" if self.excluded_cores else ""
                        self.Write_Log_Lines(f"[Setup_Uncor_Pool] {mode_name} ch_idx={ch_idx}: {num_uncors} uncors → {num_active} active cores{excluded_info}")
        else:
            pool_has_uncor_list = None

        self.MPI_Barrier()
        pool_has_uncor_list = self._safe_bcast(pool_has_uncor_list, f"Bcast_pool_has_uncor_{self.Get_Test_Mode_String(test_mode)}_{ch_idx}")
        self.pool_has_uncor[test_mode][ch_idx] = pool_has_uncor_list[self.rank]

    def Setup_Uncor_Pool(self):
        """Speed test 이후 각 active core의 uncor_pool 디렉토리에 1회 사전 분배한다.

        이후 모드 전환 시 각 코어가 자신의 pool에서 병렬 복사하여 직렬 병목을 제거한다.
        LOAD_NONE이면 즉시 return한다.
        """
        if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED:
            is_uncor_type_seed = True
        elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:
            is_uncor_type_seed = False
        else:
            return

        # Dynamic Partial: 항상 Full만 pool 생성
        # Partial pool은 Rebuild_Partial_Pool / _Build_Initial_Partial_Pool에서 동적 구성
        modes = [TestMode.FULL]

        for test_mode in modes:
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                # Root: Copy_Uncors로 소스 파일 확보
                src_path = None
                if self.is_root:
                    src_path = self.Copy_Uncors(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, test_mode=test_mode)
                self.MPI_Barrier()
                self._Setup_Uncor_Pool_For_Channel(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed, test_mode=test_mode, src_path=src_path)

        self.is_uncor_pool_ready = True
        self.total_num_uncors = self._safe_bcast(self.total_num_uncors if self.is_root else None, "Bcast_total_num_uncors_pool")
        self.MPI_Barrier()
        self.Write_Log_Lines(f"[Setup_Uncor_Pool] Pool 생성 완료.")

    def _Get_Tmp_Partial_Uncor_Dir(self, matrix: LLR_MATRIX) -> Path:
        """Dynamic Partial uncor 임시 저장 디렉토리 경로를 반환한다.

        경로: 5_Uncors/tmp_partial_uncors/{matrix 파일 이름}/

        Args:
            matrix (LLR_MATRIX): 이 Partial uncor를 만든 테스트 대상 매트릭스.

        Returns:
            Path: tmp_partial_uncors 디렉토리 경로
        """
        LLR_matrix_file_name = matrix.Get_LLR_Matrix_File_Name()
        return Path(self.session_uncor_dir) / TMP_PARTIAL_UNCORS_DIR_NAME / LLR_matrix_file_name

    def Load_Uncors_From_Pool(self, test_mode: TestMode):
        """각 코어가 자신의 pool에서 working directory로 복사한다 (완전 병렬).

        Excluded core는 복사를 시도하지 않고 has_uncor=False로 설정한다.

        Args:
            test_mode: 로드할 uncor의 TestMode (PARTIAL 또는 FULL).
        """
        is_uncor_type_seed = (UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED)
        mode_name = self.Get_Test_Mode_String(test_mode)
        pool_subdir = "Partial" if test_mode == TestMode.PARTIAL else ""

        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            if self.is_current_core_excluded:
                self.has_uncor[ch_idx] = False
                continue
            if not self.pool_has_uncor[test_mode][ch_idx]:
                self.has_uncor[ch_idx] = False
                continue

            dest_file_name = self.Get_Uncor_File_Name(process_idx=self.rank, ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
            dest_path = Path(self.local_session_dir) / dest_file_name

            # 기존 working copy 삭제
            if dest_path.exists():
                dest_path.unlink()

            # Pool에서 복사
            pool_base = Path(self.local_session_dir) / UNCOR_POOL_DIR_NAME
            pool_path = (pool_base / pool_subdir / dest_file_name) if pool_subdir else (pool_base / dest_file_name)
            if pool_path.exists():
                shutil.copy2(pool_path, dest_path)
                self.has_uncor[ch_idx] = True
            else:
                self.has_uncor[ch_idx] = False

        self.MPI_Barrier()
        self.current_loaded_test_mode = test_mode
        self.Write_Log_Lines(f"[Load_Uncors_From_Pool] {mode_name} 로드 완료.")

    def Print_Test_Result(self, matrix: Optional[LLR_MATRIX] = None, is_test_optimal: Optional[bool] = False, ch_idx: int = 0, is_test_end: bool = False):
        """테스트 결과를 로그로 출력한다.

        채널 설정과 오류 집계, FER 수치를 포맷팅해 루트 로그 파일에 기록한다.

        Args:
            matrix (Optional[LLR_MATRIX]): 결과를 표시할 매트릭스 객체.
            is_test_optimal (Optional[bool]): 최적 테스트 여부.

        Returns:
            None
        """
        if not self.is_root:
            return

        self.Calc_Loop_Elapsed_Time()

        if is_test_end:
            str_tmp = "\n[Results] "
        else:
            str_tmp = "- "
        if REFC_CONFIG.ch_type == 1:
            str_tmp += f"RBER: {REFC_CONFIG.RBERs[ch_idx]:.4f}, "
        elif REFC_CONFIG.ch_type == 2:
            str_tmp += f"Fixed Error: {REFC_CONFIG.num_fixed_errs[ch_idx]:d}, "
        elif REFC_CONFIG.ch_type == 3:
            str_tmp += f"SCR, SER, Fixed Error: {REFC_CONFIG.fixed_SCRs[ch_idx]:.2f}, {REFC_CONFIG.fixed_SERs[ch_idx]:.2f}, {REFC_CONFIG.num_fixed_errs[ch_idx]:d}, "
        if self.is_load_seed_mode:
            error_label = "seed_errors/tests"
        else:
            error_label = "raw_errors/tests"

        if self.is_load_seed_mode:
            num_errors = self.total_num_seed_errors[ch_idx]
            num_tests = self.total_num_seed_tests[ch_idx]
        else:
            num_errors = self.total_num_raw_errors[ch_idx]
            num_tests = self.total_num_raw_tests[ch_idx]
        str_tmp += f"({error_label}): {num_errors:d}/{num_tests:d}, "
        # Two-stage 모드에서 partial 테스트일 경우 *_partial 필드 사용
        is_partial_result = (UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST and self.current_test_mode == TestMode.PARTIAL)
        is_load_seed_mode = self.is_load_seed_mode
        if is_partial_result:
            fer = matrix.FERs_partial[ch_idx]
            avg_iter = matrix.avg_iterations_partial[ch_idx]
        else:
            fer = matrix.FERs[ch_idx]
            avg_iter = matrix.avg_iterations[ch_idx]
        fer_type = "seed" if is_load_seed_mode else "raw"
        str_tmp += f"FER({fer_type}): {fer:.2e}, "
        str_tmp += f"Avg it.: {avg_iter:.2f}\t"
        if PRINT_LOG_CONFIG.ENABLE_PRINT_ALL_ITER_FERs:
                total_errors_per_iter = ", ".join(f"{errors:.0f}" for errors in self.total_num_error_per_iters[ch_idx])
                total_FER_per_iter = ", ".join(f"{fer:.2e}" for fer in self.total_FER_per_iters[ch_idx])
                str_tmp += f"\n\t\t\t\t\t\t\tErrors per it.: [{total_errors_per_iter}]"
                str_tmp += f"\n\t\t\t\t\t\t\tFER per it.: [{total_FER_per_iter}]"
        if self.loop_elapsed_time is not None:
            hours, remainder = divmod(int(self.loop_elapsed_time), 3600)
            minutes, seconds = divmod(remainder, 60)
            str_tmp += f"\n\t\t\t\t\t\t\tLoop time: {hours:02d}:{minutes:02d}:{seconds:02d}"

            if hasattr(self, 'total_elapsed_time'):
                total_hours, total_remainder = divmod(int(self.total_elapsed_time), 3600)
                total_minutes, total_seconds = divmod(total_remainder, 60)
                str_tmp += f"\n\t\t\t\t\t\t\tTotal time: {total_hours:02d}:{total_minutes:02d}:{total_seconds:02d}"

            # Current time을 읽기 쉬운 형식으로 변환 (YYYYMMDD_HHMMSS -> YYYY/MM/DD HH:MM:SS)
            current_time_readable = self.loop_end_time.strftime("%Y/%m/%d %H:%M:%S")
            str_tmp += f"\n\t\t\t\t\t\t\tCurrent time: {current_time_readable}"

        self.Write_Log_Lines(str_tmp)

    def Print_Test_Summary(self):
        """테스트 결과 요약을 출력한다.

        Partial/Full 모드별, 채널별로 Initial → Optimal → Current 순서로 seed_FER 요약 출력.
        Update 발생 시 Previous Optimal → New Optimal 변화도 표시.
        Partial 결과가 있으면 Partial 먼저, 그 다음 Full 순서.
        각 matrix의 파일명도 출력.
        """
        if not self.is_root:
            return

        if self.initial_LLR_matrix is None or self.optimal_LLR_matrix is None or self.current_LLR_matrix is None:
            return

        # is_update_at_last_trial 모드 여부 확인
        is_last_trial_mode = self.current_gen_trial_LLR_mode in [
            GenLLRMode.INSERT_RANDOM_ROW,
            GenLLRMode.INSERT_RANDOM_GROUP,
            GenLLRMode.INSERT_MUTATED_GROUP,
            GenLLRMode.INSERT_MUTATED_ROW,
            GenLLRMode.GEN_INITIAL_GROUP,
            GenLLRMode.COPY_GROUP,
            GenLLRMode.REORDER_GROUP,
            GenLLRMode.ADJUST_ITERATION,
            GenLLRMode.DELETE_ROW,
            GenLLRMode.SPLIT_GROUP,
        ]
        has_temp_optimal = is_last_trial_mode and self.temp_optimal_LLR_matrix is not None

        self.Write_Log_Lines("\n" + "=" * 70)
        self.Write_Log_Lines("[Test Summary]")
        self.Write_Log_Lines(f"  Initial  : {self.initial_LLR_matrix.LLR_matrix_file_name}")

        # Update 발생 여부 확인
        is_optimal_updated = self.update_mode in (UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT,
                                                   UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL)
        is_temp_optimal_updated = self.update_mode == UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT

        # Optimal 업데이트 시 이전 optimal 표시
        if is_optimal_updated and self.previous_optimal_LLR_matrix is not None:
            self.Write_Log_Lines(f"  Prev Opt : {self.previous_optimal_LLR_matrix.LLR_matrix_file_name}")
        if is_optimal_updated:
            self.Write_Log_Lines(f"  Optimal  : {self.optimal_LLR_matrix.LLR_matrix_file_name} [UPDATED]")
        else:
            self.Write_Log_Lines(f"  Optimal  : {self.optimal_LLR_matrix.LLR_matrix_file_name}")

        # Temp Optimal 출력 (is_update_at_last_trial 모드)
        if has_temp_optimal:
            # Temp Optimal 업데이트 시 이전 temp_optimal 표시
            if is_temp_optimal_updated and self.previous_optimal_LLR_matrix is not None:
                self.Write_Log_Lines(f"  Prev Temp: {self.previous_optimal_LLR_matrix.LLR_matrix_file_name}")
            if is_temp_optimal_updated:
                self.Write_Log_Lines(f"  Temp Opt : {self.temp_optimal_LLR_matrix.LLR_matrix_file_name} [UPDATED]")
            else:
                self.Write_Log_Lines(f"  Temp Opt : {self.temp_optimal_LLR_matrix.LLR_matrix_file_name}")

        self.Write_Log_Lines(f"  Current  : {self.current_LLR_matrix.LLR_matrix_file_name}")
        self.Write_Log_Lines("=" * 70)

        # FER 타입 결정 (load_seed_mode 여부)
        is_load_seed_mode = self.is_load_seed_mode
        fer_type = "seed" if is_load_seed_mode else "raw"

        # Partial 결과 존재 여부 확인 (FERs_partial이 1.0 미만인 값이 있는지)
        has_partial = any(
            self.initial_LLR_matrix.FERs_partial[ch] < 1.0 or
            self.optimal_LLR_matrix.FERs_partial[ch] < 1.0 or
            self.current_LLR_matrix.FERs_partial[ch] < 1.0
            for ch in range(REFC_CONFIG.NUM_TARGET_CHANNELS)
        )

        # 출력할 모드 목록 (Partial이 있으면 Partial 먼저)
        modes = []
        if has_partial:
            modes.append(("Partial", True))
        modes.append(("Full", False))

        for mode_name, is_partial in modes:
            self.Write_Log_Lines(f"\n[{mode_name}]")

            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                ch_param = self.Get_Channel_Param_String(ch_idx)

                if is_partial:
                    init_fer = self.initial_LLR_matrix.FERs_partial[ch_idx]
                    init_avg = self.initial_LLR_matrix.avg_iterations_partial[ch_idx]
                    init_errs = self.initial_LLR_matrix.num_errors_partial[ch_idx]
                    init_tests = self.initial_LLR_matrix.num_tests_partial[ch_idx]
                    prev_opt_fer = self.previous_optimal_LLR_matrix.FERs_partial[ch_idx] if self.previous_optimal_LLR_matrix else None
                    prev_opt_avg = self.previous_optimal_LLR_matrix.avg_iterations_partial[ch_idx] if self.previous_optimal_LLR_matrix else None
                    prev_opt_errs = self.previous_optimal_LLR_matrix.num_errors_partial[ch_idx] if self.previous_optimal_LLR_matrix else None
                    prev_opt_tests = self.previous_optimal_LLR_matrix.num_tests_partial[ch_idx] if self.previous_optimal_LLR_matrix else None
                    opt_fer = self.optimal_LLR_matrix.FERs_partial[ch_idx]
                    opt_avg = self.optimal_LLR_matrix.avg_iterations_partial[ch_idx]
                    opt_errs = self.optimal_LLR_matrix.num_errors_partial[ch_idx]
                    opt_tests = self.optimal_LLR_matrix.num_tests_partial[ch_idx]
                    temp_opt_fer = self.temp_optimal_LLR_matrix.FERs_partial[ch_idx] if has_temp_optimal else None
                    temp_opt_avg = self.temp_optimal_LLR_matrix.avg_iterations_partial[ch_idx] if has_temp_optimal else None
                    temp_opt_errs = self.temp_optimal_LLR_matrix.num_errors_partial[ch_idx] if has_temp_optimal else None
                    temp_opt_tests = self.temp_optimal_LLR_matrix.num_tests_partial[ch_idx] if has_temp_optimal else None
                    cur_fer = self.current_LLR_matrix.FERs_partial[ch_idx]
                    cur_avg = self.current_LLR_matrix.avg_iterations_partial[ch_idx]
                    cur_errs = self.current_LLR_matrix.num_errors_partial[ch_idx]
                    cur_tests = self.current_LLR_matrix.num_tests_partial[ch_idx]
                else:
                    init_fer = self.initial_LLR_matrix.FERs[ch_idx]
                    init_avg = self.initial_LLR_matrix.avg_iterations[ch_idx]
                    init_errs = self.initial_LLR_matrix.num_errors[ch_idx]
                    init_tests = self.initial_LLR_matrix.num_tests[ch_idx]
                    prev_opt_fer = self.previous_optimal_LLR_matrix.FERs[ch_idx] if self.previous_optimal_LLR_matrix else None
                    prev_opt_avg = self.previous_optimal_LLR_matrix.avg_iterations[ch_idx] if self.previous_optimal_LLR_matrix else None
                    prev_opt_errs = self.previous_optimal_LLR_matrix.num_errors[ch_idx] if self.previous_optimal_LLR_matrix else None
                    prev_opt_tests = self.previous_optimal_LLR_matrix.num_tests[ch_idx] if self.previous_optimal_LLR_matrix else None
                    opt_fer = self.optimal_LLR_matrix.FERs[ch_idx]
                    opt_avg = self.optimal_LLR_matrix.avg_iterations[ch_idx]
                    opt_errs = self.optimal_LLR_matrix.num_errors[ch_idx]
                    opt_tests = self.optimal_LLR_matrix.num_tests[ch_idx]
                    temp_opt_fer = self.temp_optimal_LLR_matrix.FERs[ch_idx] if has_temp_optimal else None
                    temp_opt_avg = self.temp_optimal_LLR_matrix.avg_iterations[ch_idx] if has_temp_optimal else None
                    temp_opt_errs = self.temp_optimal_LLR_matrix.num_errors[ch_idx] if has_temp_optimal else None
                    temp_opt_tests = self.temp_optimal_LLR_matrix.num_tests[ch_idx] if has_temp_optimal else None
                    cur_fer = self.current_LLR_matrix.FERs[ch_idx]
                    cur_avg = self.current_LLR_matrix.avg_iterations[ch_idx]
                    cur_errs = self.current_LLR_matrix.num_errors[ch_idx]
                    cur_tests = self.current_LLR_matrix.num_tests[ch_idx]

                # avg_iterations < 0 이면 미테스트 → N/A 표시
                error_label = "seed_errors/tests" if is_load_seed_mode else "raw_errors/tests"
                def fmt_result(fer, avg, errs, tests, suffix=""):
                    if avg is not None and avg < 0:
                        return f"N/A{suffix}"
                    return f"FER({fer_type})={fer:.2e}, Avg_it={avg:.2f}, ({error_label})={errs:d}/{tests:d}{suffix}"

                self.Write_Log_Lines(f"  ch{ch_idx}({ch_param}):")
                self.Write_Log_Lines(f"    Initial  : {fmt_result(init_fer, init_avg, init_errs, init_tests)}")
                # Optimal 업데이트 시 이전 optimal 표시
                if is_optimal_updated and prev_opt_fer is not None:
                    self.Write_Log_Lines(f"    Prev Opt : {fmt_result(prev_opt_fer, prev_opt_avg, prev_opt_errs, prev_opt_tests)}")
                if is_optimal_updated:
                    self.Write_Log_Lines(f"    Optimal  : {fmt_result(opt_fer, opt_avg, opt_errs, opt_tests, ' [UPDATED]')}")
                else:
                    self.Write_Log_Lines(f"    Optimal  : {fmt_result(opt_fer, opt_avg, opt_errs, opt_tests)}")
                if has_temp_optimal and temp_opt_fer is not None:
                    # Temp Optimal 업데이트 시 이전 temp_optimal 표시
                    if is_temp_optimal_updated and prev_opt_fer is not None:
                        self.Write_Log_Lines(f"    Prev Temp: {fmt_result(prev_opt_fer, prev_opt_avg, prev_opt_errs, prev_opt_tests)}")
                    if is_temp_optimal_updated:
                        self.Write_Log_Lines(f"    Temp Opt : {fmt_result(temp_opt_fer, temp_opt_avg, temp_opt_errs, temp_opt_tests, ' [UPDATED]')}")
                    else:
                        self.Write_Log_Lines(f"    Temp Opt : {fmt_result(temp_opt_fer, temp_opt_avg, temp_opt_errs, temp_opt_tests)}")
                self.Write_Log_Lines(f"    Current  : {fmt_result(cur_fer, cur_avg, cur_errs, cur_tests)}")

        self.Write_Log_Lines("=" * 70)

    def Run_Initial_Test(self):
        """초기 매트릭스 테스트와 최적 결과 갱신을 수행한다.

        초기 매트릭스를 test한 뒤 초기 기준으로 최적 매트릭스를 설정하고 환경을 정리한다.

        Args:
            없음.

        Returns:
            None
        """
        self.Test_Initial_LLR()

        # initial_LLR_matrix의 FER/avg_iterations를 current_LLR_matrix에서 복사 (테스트 후 값 반영)
        # Full 테스트 결과
        self.initial_LLR_matrix.FERs = self.current_LLR_matrix.FERs[:]
        self.initial_LLR_matrix.raw_FERs = self.current_LLR_matrix.raw_FERs[:]
        self.initial_LLR_matrix.seed_FERs = self.current_LLR_matrix.seed_FERs[:]
        self.initial_LLR_matrix.avg_iterations = self.current_LLR_matrix.avg_iterations[:]
        self.initial_LLR_matrix.num_errors = self.current_LLR_matrix.num_errors[:]
        self.initial_LLR_matrix.num_tests = self.current_LLR_matrix.num_tests[:]
        # Partial 테스트 결과 (Two-stage 모드 시 사용)
        self.initial_LLR_matrix.FERs_partial = self.current_LLR_matrix.FERs_partial[:]
        self.initial_LLR_matrix.raw_FERs_partial = self.current_LLR_matrix.raw_FERs_partial[:]
        self.initial_LLR_matrix.seed_FERs_partial = self.current_LLR_matrix.seed_FERs_partial[:]
        self.initial_LLR_matrix.avg_iterations_partial = self.current_LLR_matrix.avg_iterations_partial[:]
        self.initial_LLR_matrix.num_errors_partial = self.current_LLR_matrix.num_errors_partial[:]
        self.initial_LLR_matrix.num_tests_partial = self.current_LLR_matrix.num_tests_partial[:]

        self.Update_Optimal_LLR(is_initial=True)

        if self.current_seed_mode == SeedMode.SAVE_UNCOR_SEED:
            # Gather_And_Archive_Uncors는 Test_LLR 채널 루프에서 채널별로 이미 호출됨
            # total_num_uncors 동기화만 수행 (root → worker)
            self.MPI_Barrier()
            self.total_num_uncors = self._safe_bcast(self.total_num_uncors if self.is_root else None, "Bcast_total_num_uncors")
        elif self.current_seed_mode == SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED:
            self.Process_Uncors(is_setup_stage=False, is_uncor_type_seed=True, is_redecoded_uncor=True, should_distribute_uncors=False, test_mode=self.current_test_mode, matrix=self.current_LLR_matrix)

        # SAVE_UNCOR 또는 REDECODE 모드일 때 Input으로 uncor 업데이트
        if DAO_CONFIG.RUN_DAO_MODE in [
            RunDAOMode.SAVE_UNCOR,
            RunDAOMode.REDECODE
        ]:
            self.Update_Uncors_To_Input()

    def Update_Uncors_To_Input(self):
        """현재 매트릭스의 Redecoded uncors를 Input 디렉토리에 타임스탬프별로 저장한다.

        Output/{session}/5_Uncors/Redecoded_uncors/{현재_LLR_MATRIX.txt}/ 하위의 uncor 파일을
        Input/Ref_C/{ECC_DIR_NAME}/Uncors/{MODE}/{현재_LLR_MATRIX.txt}/Recoded_uncors_{YYYYMMDD_HHMMSS}/
        에 저장한다. 원본 uncor 파일은 유지되며, 각 redecoding 결과는 별도 타임스탬프 디렉토리로 관리된다.
        uncor_log.txt에 업데이트 이력을 기록한다.
        Multi-matrix 모드에서는 현재 매트릭스의 서브디렉토리만 대상으로 하여 이전 매트릭스 중복 복사를 방지한다.

        Args:
            없음.

        Returns:
            None
        """
        if not self.is_root:
            return

        # 경로 설정: 현재 매트릭스의 서브디렉토리만 대상으로 함 (multi-matrix 시 이전 매트릭스 중복 복사 방지)
        current_matrix_file_name = self.optimal_LLR_matrix.Get_LLR_Matrix_File_Name()
        redecoded_uncors_base_dir = os.path.join(self.session_dir, "5_Uncors", "Redecoded_uncors")
        redecoded_uncors_dir = os.path.join(redecoded_uncors_base_dir, current_matrix_file_name)
        input_uncor_base_dir = os.path.join(
            PATH_CONFIG.INPUT_UNCOR_DIR_PATH,
            MODE_MAP[REFC_CONFIG.init_n]
        )

        if not os.path.exists(redecoded_uncors_dir):
            self.Write_Log_Lines(f"[Update_Uncors_To_Input] Redecoded_uncors 디렉토리가 없습니다: {redecoded_uncors_dir}")
            return

        self.Write_Log_Separator("Update Uncors To Input", "="*50)
        self.Write_Log_Lines(f"소스 디렉토리: {redecoded_uncors_dir}")
        self.Write_Log_Lines(f"대상 디렉토리: {input_uncor_base_dir}")

        timestamp_for_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamp_for_log = self.Get_Timestamp()
        recoded_subdir = f"Recoded_uncors_{timestamp_for_filename}"

        # 현재 매트릭스의 Redecoded_uncors/{LLR_MATRIX_xx.txt}/ 하위만 순회
        for root, dirs, files in os.walk(redecoded_uncors_dir):
            # 상대 경로 계산 (Redecoded_uncors 기준, 매트릭스 서브디렉토리 포함)
            rel_dir = os.path.relpath(root, redecoded_uncors_base_dir)

            # 대상 디렉토리 경로 (rel_dir은 항상 "LLR_MATRIX_xx.txt" 이상의 경로)
            target_dir = os.path.join(input_uncor_base_dir, rel_dir)

            # Recoded_uncors_{timestamp} 서브디렉토리에 저장
            recoded_dir = os.path.join(target_dir, recoded_subdir)

            # 각 파일 처리
            for filename in files:
                # uncor_log.txt 자체는 복사하지 않음
                if filename == "uncor_log.txt":
                    continue

                src_file = os.path.join(root, filename)
                dst_file = os.path.join(recoded_dir, filename)

                try:
                    os.makedirs(recoded_dir, exist_ok=True)
                    shutil.copy2(src_file, dst_file)

                    # 새 파일 정보 수집
                    try:
                        with open(dst_file, 'r', encoding='utf-8') as f:
                            new_line_count = sum(1 for _ in f)
                    except UnicodeDecodeError:
                        new_line_count = -1  # 바이너리 파일
                    except IOError as e:
                        self.Write_Log_Lines(f"[WARNING] uncor 파일 라인 수 읽기 실패 — {dst_file}: {e}")
                        new_line_count = -1

                    # uncor_log.txt에 append (target_dir 레벨에 기록)
                    log_file = os.path.join(target_dir, "uncor_log.txt")
                    log_entry = []
                    log_entry.append(f"[{timestamp_for_log} 업데이트]")
                    log_entry.append(f"- 저장 위치: {recoded_subdir}/{filename}")
                    if new_line_count >= 0:
                        log_entry.append(f"- Line 수: {new_line_count}")
                    else:
                        log_entry.append(f"- Line 수: (바이너리 파일)")
                    log_entry.append(f"- 소스: {src_file}")
                    log_entry.append("---")
                    log_entry.append("")

                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write('\n'.join(log_entry) + '\n')

                    self.Write_Log_Lines(f"복사 완료: {recoded_subdir}/{filename}")

                except Exception as e:
                    self.Write_Log_Lines(f"[오류] {filename} 처리 실패: {e}")

        self.Write_Log_Separator("Update Uncors To Input Completed", "="*50)

    def Run_ECC(self, ch_idx: int) -> None:
        """ECC 실행 파일을 호출한다.

        생성된 배치 스크립트를 운영체제에 맞는 방식으로 실행해 ECC 시뮬레이션을 수행한다.

        Args:
            없음.

        Returns:
            None

        Raises:
            SystemExit: 외부 명령 실행이 실패한 경우.
        """
        # 코어 속도 테스트에서 제외된 코어는 skip
        if self.is_current_core_excluded:
            return

        # LOAD_UNCOR 모드에서 uncor가 없으면 skip
        if self.is_load_uncor_seed_file_mode:
            if not self.has_uncor[ch_idx]:
                return
        ecc_start = time.time()
        for attempt in range(1, TIME_CONFIG.MAX_ECC_MEMORY_RETRY + 1):
            try:
                if os.name == "nt":  # Windows
                    subprocess.run(["cmd", "/c", os.path.basename(self.batch_path)], cwd=os.path.dirname(self.batch_path), check=True, timeout=SIM_MAX_TIME_OUT)
                else:  # Linux or macOS
                    subprocess.run(["bash", os.path.basename(self.batch_path)], cwd=os.path.dirname(self.batch_path), check=True, timeout=SIM_MAX_TIME_OUT)
                time.sleep(0.5)
                return
            except subprocess.TimeoutExpired:
                self.MPI_Abort(f"[Run_ECC] ECC timeout ({SIM_MAX_TIME_OUT}s) - rank {self.rank}, batch: {self.batch_path}")
            except OSError as error:
                if error.errno == 12:  # Cannot allocate memory
                    delay = random.uniform(0, TIME_CONFIG.MAX_ECC_MEMORY_RETRY_DELAY)
                    self.Write_Log_Lines(f"[Run_ECC] 메모리 할당 실패 (시도 {attempt}/{TIME_CONFIG.MAX_ECC_MEMORY_RETRY}), {delay:.1f}초 후 재시도...")
                    time.sleep(delay)
                else:
                    self.MPI_Abort(f"ECC execution failed: {error}")
            except (subprocess.CalledProcessError, FileNotFoundError) as error:
                self.MPI_Abort(f"ECC execution failed: {error}")
        self.MPI_Abort(f"ECC execution failed: 메모리 할당 실패 {TIME_CONFIG.MAX_ECC_MEMORY_RETRY}회 재시도 후에도 실패")

    def Reset_Optimal_Results(self):
        """Optimal llr matrix의 fer를 초기화

        Args:
            없음.

        Returns:
            None
        """
        if self.current_seed_mode in [SeedMode.SAVE_UNCOR_SEED, SeedMode.DEFAULT]:
            self.optimal_LLR_matrix.FERs = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            self.optimal_LLR_matrix.raw_FERs = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS
            self.optimal_LLR_matrix.seed_FERs = [1.0] * REFC_CONFIG.NUM_TARGET_CHANNELS

    def Read_FER_From_File(self, result_file: str) -> float:
        """결과 파일에서 FER 값을 읽는다.

        파일의 마지막 유효 라인을 파싱해 FER 값을 추출하고 검증한다.

        Args:
            result_file (str): FER 정보를 담은 결과 파일 경로.

        Returns:
            float: 파싱된 FER 값.

        Raises:
            SystemExit: 파일 읽기 또는 파싱에 실패한 경우.
        """

        try:
            with open(result_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except OSError as error:
            self.MPI_Abort(f"Failed to open {result_file}: {error}")

        if not lines:
            self.MPI_Abort(f"Empty result file: {result_file}")

        parts = lines[-1].split()

        try:
            FER = float(parts[-1])
        except (ValueError, IndexError) as error:
            self.MPI_Abort(f"Invalid FER in {result_file}: {error}")
        return FER

    def Run_Optimization(self) -> None:
        """메인 최적화 루프를 수행한다.

        단계별로 trial 매트릭스를 생성하고 검증·테스트·갱신 절차를 반복해 최적 LLR을 탐색한다.

        Args:
            없음.

        Returns:
            None
        """
        self.Restore_Random_State_If_Configured()
        consecutive_failed_stages = 0

        for stage_idx in range(1, DAO_CONFIG.MAX_OPTIMIZATION_STAGE + 1):

            self.Periodic_Recheck(stage_idx)
            self.Initialize_Stage(stage_idx)

            stage_start_time = time.time()
            stage_had_any_success = False  # 유효 LLR 생성 여부 추적 (연속 실패 판정용)
            for trial_idx in range(1, self.max_modification_trial + 1):

                self.Initialize_Trial(trial_idx)

                # 한 trial당 최대 재시도 횟수만큼 LLR 생성 시도
                gen_success = False
                for gen_retry in range(DAO_CONFIG.MAX_GEN_RETRY_PER_TRIAL):
                    self.Gen_Trial_LLR()

                    if self.Is_Current_LLR_Valid():
                        gen_success = True
                        stage_had_any_success = True
                        break

                if not gen_success:
                    continue

                # Trial LLR 테스트
                # Two-stage 모드: Partial → (개선 시) Full 순차 테스트
                # 기존 모드: Full 테스트만 수행
                should_check_update = self.Test_Trial_LLR()

                # Multi-round 모드: Test 후 결과 수집 + state 동기화 (공용)
                if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
                    state_attr = MULTI_ROUND_MODES[self.current_gen_trial_LLR_mode]
                    # Round result update (해당 모드만)
                    update_func_name = MULTI_ROUND_UPDATE_FUNC.get(self.current_gen_trial_LLR_mode)
                    if update_func_name and self.is_root and self.current_LLR_matrix is not None:
                        getattr(self, update_func_name)(self.current_LLR_matrix)
                    # State 동기화
                    state = getattr(self, state_attr)
                    state = self._safe_bcast(state if self.is_root else None, f"Bcast_{state_attr}_after_update")
                    setattr(self, state_attr, state)

                # Stage 시간 제한 체크 (root에서만 계산 후 bcast로 동기화)
                # - 각 rank가 독립적으로 계산하면 time.time() 차이로 desync 발생 가능
                # - root가 break하고 worker가 다음 trial 진입 시 MPI timeout 발생
                if self.is_root:
                    stage_elapsed_time = time.time() - stage_start_time
                    is_time_exceeded = (self.is_current_stage_enable_max_stage_time_limit and
                                    stage_elapsed_time > TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS)
                else:
                    stage_elapsed_time = 0.0
                    is_time_exceeded = False
                is_time_exceeded = self._safe_bcast(is_time_exceeded if self.is_root else None, "Bcast_is_time_exceeded")

                # end_flag 체크 (root가 읽고 bcast로 동기화 — time_exceeded와 동일 패턴)
                if self.is_root:
                    is_dao_end = self.Read_DAO_End_Flag()
                    trial_skip_count = self.Read_Trial_End_Flag()
                else:
                    is_dao_end = False
                    trial_skip_count = 0
                is_dao_end = self._safe_bcast(is_dao_end if self.is_root else None, "Bcast_dao_end_flag")
                trial_skip_count = self._safe_bcast(trial_skip_count if self.is_root else None, "Bcast_trial_end_flag")
                is_trial_end = trial_skip_count > 0
                is_forced_termination = is_time_exceeded or is_dao_end or is_trial_end

                # Trial end_flag count 감소 처리 (root만)
                if is_trial_end and self.is_root:
                    remaining = trial_skip_count - 1
                    if remaining == 0:
                        self._Write_End_Flag(PATH_CONFIG.TRIAL_END_FLAG_FILE_PATH, False)
                    else:
                        self._Write_End_Flag_Count(PATH_CONFIG.TRIAL_END_FLAG_FILE_PATH, remaining)

                # Full 테스트 완료된 경우만 Update 검사
                # ENABLE_TWO_STAGE_TEST=False: 항상 True (기존 동작)
                # ENABLE_TWO_STAGE_TEST=True: Partial 개선 시만 True
                # 예외: 강제 종료 시 temp_optimal과 optimal 비교를 위해 강제 진행
                if not should_check_update and is_forced_termination:
                    # 강제 종료인데 Partial 개선 없어서 Full 스킵된 경우
                    # → 마지막 trial이므로 Full 테스트 강제 수행 후 Update
                    self.Write_Log_Lines("[Forced termination] Forcing full test for final temp_optimal vs optimal comparison")
                    self.current_test_mode = TestMode.FULL
                    self.Ensure_Uncors_Loaded(TestMode.FULL)
                    self.Test_LLR(self.current_LLR_matrix)
                    self._Cleanup_LLR_Matrix_Files()
                    should_check_update = True  # Update 진행하도록 변경

                if should_check_update:
                    # Multi-round 모드: is_active=False이면 강제 마지막 trial (공용)
                    if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
                        state_attr = MULTI_ROUND_MODES[self.current_gen_trial_LLR_mode]
                        state = getattr(self, state_attr)
                        is_final = not state.is_active
                        self.Update_Optimal_LLR(is_initial=False, is_forced_last_trial=(is_forced_termination or is_final))
                    else:
                        # 다른 모드는 기존대로
                        self.Update_Optimal_LLR(is_initial=False, is_forced_last_trial=is_forced_termination)
                else:
                    # Partial test에서 개선 없음 → Update 스킵
                    # is_previous_trial_updated를 False로 명시적 설정 (다음 trial tuning 방지)
                    self.is_previous_trial_updated = False
                    # update_mode 초기화 (Print_Test_Summary에서 [UPDATED] 표시 방지)
                    self.update_mode = None

                # 테스트 결과 요약은 출력
                self.Print_Test_Summary()

                # 시간 기반 주기적 Speed Test (root 판단 + bcast 동기화)
                # 강제 종료 확정 시 스킵 (결과를 활용하지 못하는 시간 낭비 방지)
                if (not is_forced_termination
                        and SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST
                        and SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS > 0):
                    if self.is_root:
                        should_recheck_speed = (time.time() - self._last_speed_test_time) >= SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS
                    else:
                        should_recheck_speed = False
                    should_recheck_speed = self._safe_bcast(should_recheck_speed if self.is_root else None, "Bcast_should_recheck_speed")
                    if should_recheck_speed:
                        self.Write_Log_Lines(f"[Periodic Speed Test] {SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS}초 경과 — speed test 재실행  {self.Get_Mode_Sequence_Str()}")
                        excluded_changed = self._Recheck_Speed_Test()
                        if excluded_changed:
                            self._Redistribute_Uncor_Pool_Uniform()
                        else:
                            self.Write_Log_Lines(f"[Periodic Speed Test] excluded_cores 변경 없음, 균일 재분배 스킵")

                if is_forced_termination:
                    if is_time_exceeded:
                        self.Write_Log_Lines(f"[Stage {stage_idx} time limit exceeded: {stage_elapsed_time:.1f}s / {TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS}s]")
                    if is_dao_end:
                        self.Write_Log_Lines(f"[DAO end flag detected] Breaking trial loop at trial {trial_idx}")
                    if is_trial_end:
                        self.Write_Log_Lines(f"[Trial end flag detected] Skipping stage {stage_idx} (remaining skips: {trial_skip_count - 1})")
                    break

                # Multi-round 모드: final verification 완료 후 루프 종료
                if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
                    state_attr = MULTI_ROUND_MODES[self.current_gen_trial_LLR_mode]
                    state = getattr(self, state_attr)
                    if not state.is_active:
                        self.Write_Log_Lines(f"[{self.current_gen_trial_LLR_mode_name}] Final verification complete, ending trials")
                        break

            # Trial 루프 종료 후 안전망: gen_success=False로 마지막 trial이 스킵된 경우 처리
            self._Promote_Temp_Optimal_On_Stage_Exit()

            # log_has_update bcast (로그 파일명용, root 전용이므로 동기화)
            self.log_has_update = self._safe_bcast(
                self.log_has_update if self.is_root else None, "Bcast_log_has_update")
            # 유효 LLR 생성 여부로 연속 실패 판정 (gen_success 기반, 모든 rank 동일)
            if stage_had_any_success:
                consecutive_failed_stages = 0
            else:
                consecutive_failed_stages += 1
                seq_len = len(DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE if DAO_CONFIG.IS_HBF_OPT
                              else DAO_CONFIG.Gen_LLR_Mode_SEQUENCE)
                if consecutive_failed_stages >= seq_len * 2:
                    self.Write_Log_Lines(
                        f"[WARNING] {consecutive_failed_stages} consecutive stages without valid LLR generation. Terminating.")
                    break

            # 외부 DAO 종료 플래그 체크 (root가 읽고 bcast로 동기화)
            if self.is_root:
                is_dao_end_stage = self.Read_DAO_End_Flag()
            else:
                is_dao_end_stage = False
            is_dao_end_stage = self._safe_bcast(is_dao_end_stage if self.is_root else None, "Bcast_dao_end_flag_stage")
            if is_dao_end_stage:
                self.Write_Log_Lines(f"[DAO end flag detected] Terminating optimization at stage {stage_idx}")
                break

        self.Print_Final_Optimal_LLR_Results()
    
    def Read_Ref_C_Result(self, file_path: str, max_retries: int = 3, retry_delay: float = 0.1):
        """Ref-C 결과 파일을 파싱한다.

        반복별 테스트/오류 집계를 합산해 전체 테스트 수와 iteration별 오류 분포를 계산한다.
        파일이 작성 중일 경우 파싱 오류가 발생할 수 있으므로 재시도 로직 포함.

        Args:
            file_path (str): 결과 파일 경로.
            max_retries (int): 파싱 실패 시 최대 재시도 횟수.
            retry_delay (float): 재시도 전 대기 시간 (초).
        """
        if REFC_CONFIG.ch_type in (1, 2):
            base_offset = 1
        elif REFC_CONFIG.ch_type == 3:
            base_offset = 3
        else:
            self.MPI_Abort(f"Read_Ref_C_Result: Unsupported ch_type={REFC_CONFIG.ch_type}")

        for attempt in range(max_retries + 1):
            try:
                # 파일 크기 안정화 대기 (작성 완료 확인)
                prev_size = -1
                for _ in range(5):  # 최대 5회 체크
                    curr_size = os.path.getsize(file_path)
                    if curr_size == prev_size:
                        break  # 크기 안정화됨
                    prev_size = curr_size
                    time.sleep(0.02)  # 20ms 대기

                with open(file_path, 'r', encoding='utf8') as file:
                    lines = [line.strip() for line in file.readlines() if line.strip()]

                sum_test = 0
                sum_error = 0
                sum_iteration = 0
                sum_error_per_iter = None

                for line in lines:
                    parts = line.split()
                    result_offset = base_offset
                    if len(parts) <= base_offset:
                        continue

                    try:
                        num_test = int(parts[result_offset]); result_offset += 1
                        num_error = int(parts[result_offset]); result_offset += 1
                        avg_iteration = float(parts[result_offset]); result_offset += 1
                    except (ValueError, IndexError):
                        # 불완전한 라인 - 파일이 아직 작성 중일 수 있음
                        raise ValueError(f"Incomplete line in {file_path}: {line[:50]}...")

                    num_iteration = avg_iteration * num_test

                    # parts 슬라이싱 검증: result_offset:-3 범위가 유효한지 확인
                    if len(parts) < result_offset + 3:
                        continue  # 파일 형식 오류, 이 라인 스킵

                    arr = np.array(parts[result_offset:-3], dtype='f8')
                    if len(arr) == 0:
                        continue  # 빈 배열이면 스킵

                    num_error_per_iteration = np.round(arr * num_test).astype('f8')

                    sum_test += num_test
                    sum_error += num_error
                    sum_iteration += num_iteration

                    if sum_error_per_iter is None:
                        sum_error_per_iter = num_error_per_iteration.copy()
                    else:
                        # 배열 크기가 같을 때만 더함
                        if len(num_error_per_iteration) == len(sum_error_per_iter):
                            sum_error_per_iter += num_error_per_iteration

                return sum_test, sum_error, sum_iteration, sum_error_per_iter

            except ValueError as e:
                if attempt < max_retries:
                    time.sleep(retry_delay)
                    continue  # 재시도
                else:
                    # 최대 재시도 초과 - 빈 결과 반환 (sum_test=0으로 유효 데이터 없음 표시)
                    self.Write_Log_Lines(f"[WARNING] Read_Ref_C_Result: {max_retries}회 재시도 후 파싱 실패, 결과 무시됨 — {file_path} ({e})")
                    return 0, 0, 0, None

        # fallback (도달하지 않아야 함)
        return 0, 0, 0, None
    
    def Save_LLR_Matrix(self, matrix: Optional[LLR_MATRIX] = None, target_dir: str = "", save_root_only: bool = True):
        if save_root_only:
            if not self.is_root:
                return
        matrix.Save_Matrix(target_dir)
        if DEBUG_CONFIG.ENABLE_LLR_MATRIX_SAVE_LOGGING:
            self.Write_Log_Lines(f"[Saved to]: {target_dir}")

    def Set_CSW_Update_Limit(self):
        if MUTATE_CONFIG.ENABLE_CSW_UPDATE_LIMIT:
            self.now_enable_CSW_update_limit = True
            self.CSW_update_limit_value = MUTATE_CONFIG.CSW_UPDATE_LIMIT_VALUE
        else:
            self.now_enable_CSW_update_limit = False
            self.CSW_update_limit_value = MAX_CSW
    
    @staticmethod
    def _Is_Group_Index_Value(value) -> bool:
        """그룹 index로 쓸 수 있는 정수 값인지 본다 (True와 False는 정수로 치지 않는다)."""
        return isinstance(value, (int, np.integer)) and not isinstance(value, bool)

    def Build_Target_Group_Indices(self, matrix: LLR_MATRIX) -> list[int]:
        """설정에서 opt 타겟 그룹 목록을 만든다. 목록의 값은 그룹 하나하나의 index다 (SW 분기 그룹도 같다).

        FIXED_TARGET_GROUP_IDX_LIST가 있으면 그 목록을 적힌 순서대로 쓰고, None이면 INITIAL_TARGET_GROUP_IDX부터
        마지막 그룹까지를 쓴다 (그 범위가 비면 마지막 그룹 하나).
        FIXED_TARGET_GROUP_IDX_LIST에서는 매트릭스에 있는 그룹 번호만 고른다. 잘못 적은 값을 알리는 일은
        Validate_Config의 Check_Fixed_Target_Group_Idx_List가 맡는다.
        """
        num_groups = len(matrix.groups)
        fixed_list = DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST
        if fixed_list is not None:
            listed_values = fixed_list if isinstance(fixed_list, (list, tuple)) else []
            return [int(idx) for idx in listed_values if self._Is_Group_Index_Value(idx) and 0 <= idx < num_groups]

        target_group_indices = list(range(DAO_CONFIG.INITIAL_TARGET_GROUP_IDX, num_groups))
        if not target_group_indices:
            target_group_indices = [num_groups - 1]
        return target_group_indices

    def Check_Fixed_Target_Group_Idx_List(self, matrix: LLR_MATRIX) -> list[str]:
        """FIXED_TARGET_GROUP_IDX_LIST의 값과, 함께 쓰는 모드 시퀀스를 검사한다.

        목록의 index는 매트릭스의 그룹 번호에 묶여 있으므로, 그룹 수와 순서와 iteration 구간을 그대로 두는 모드
        (FIXED_TARGET_GROUP_ALLOWED_MODES)만 함께 쓴다. 검사 대상은 지금 쓰는 시퀀스 하나다
        (IS_HBF_OPT이면 Gen_LLR_Mode_HBF_SEQUENCE, 아니면 Gen_LLR_Mode_SEQUENCE).

        Returns:
            list[str]: 오류 문구 목록. FIXED_TARGET_GROUP_IDX_LIST가 None이거나 문제가 없으면 빈 목록
        """
        fixed_list = DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST
        if fixed_list is None:
            return []
        if not isinstance(fixed_list, (list, tuple)):
            return [f"FIXED_TARGET_GROUP_IDX_LIST must be a list of group indices such as [0, 1] (current: {fixed_list!r})."]
        if len(fixed_list) == 0:
            return ["FIXED_TARGET_GROUP_IDX_LIST must not be empty. Use None to target every group from INITIAL_TARGET_GROUP_IDX."]

        errors: list[str] = []
        num_groups = len(matrix.groups)
        non_integers = [idx for idx in fixed_list if not self._Is_Group_Index_Value(idx)]
        if non_integers:
            errors.append(f"FIXED_TARGET_GROUP_IDX_LIST must contain integers only (found: {non_integers!r}).")
            return errors
        out_of_range = [int(idx) for idx in fixed_list if not (0 <= idx < num_groups)]
        if out_of_range:
            errors.append(f"FIXED_TARGET_GROUP_IDX_LIST contains {out_of_range}, out of range. Must be in [0, {num_groups - 1}] (the initial matrix has {num_groups} groups).")
        duplicates = sorted({int(idx) for idx in fixed_list if list(fixed_list).count(idx) > 1})
        if duplicates:
            errors.append(f"FIXED_TARGET_GROUP_IDX_LIST contains {duplicates} more than once.")

        sequence_name = "Gen_LLR_Mode_HBF_SEQUENCE" if DAO_CONFIG.IS_HBF_OPT else "Gen_LLR_Mode_SEQUENCE"
        allowed_values = {int(mode) for mode in FIXED_TARGET_GROUP_ALLOWED_MODES}
        valid_mode_values = {int(mode) for mode in GenLLRMode}
        blocked_modes: list[int] = []
        for mode_value in getattr(DAO_CONFIG, sequence_name):
            mode_value = int(mode_value)
            if mode_value in valid_mode_values and mode_value not in allowed_values and mode_value not in blocked_modes:
                blocked_modes.append(mode_value)
        if blocked_modes:
            blocked_names = ", ".join(f"{GenLLRMode(value).name} ({value})" for value in blocked_modes)
            allowed_names = ", ".join(f"{GenLLRMode(value).name} ({value})" for value in sorted(allowed_values))
            errors.append(
                f"{sequence_name} contains {blocked_names}, which change the number, order or iteration of groups, "
                f"so they cannot run with FIXED_TARGET_GROUP_IDX_LIST. Allowed modes: {allowed_names}."
            )
        return errors

    def Check_SW_Branch_Mode_Allowed(self, matrix: LLR_MATRIX, selected_mode: int, target_group_indices: list[int]) -> Optional[str]:
        """SW 분기가 있는 매트릭스에서 이 모드가 타겟 목록과 함께 허용되는지 본다.

        ㉮ GEN_INITIAL_GROUP은 모든 그룹을 새 그룹 하나로 바꾸므로 분기 그룹이 있으면 허용하지 않는다
        ㉯ 타겟 그룹에 분기 그룹이 들어 있으면 SW_BRANCH_ALLOWED_MODES(MUTATE_MATRIX, MUTATE_CSW)만 허용한다.
           타겟이 전부 분기 구간 뒤의 보통 그룹이면 다른 모드도 허용하되, 타겟 앞의 그룹을 바꾼 trial은
           Gen_Trial_LLR의 _Protected_Groups_Changed가 버린다
        어느 분기의 그룹을 바꿀지는 타겟 목록이 정한다. 분기 그룹은 분기 index와 상관없이 타겟이 된다.

        Returns:
            Optional[str]: 막는 이유. 허용되면 None
        """
        matrix.Build_SW_Branch_Layout()
        if not matrix.has_sw_branch:
            return None
        mode_name = GenLLRMode(selected_mode).name
        if int(selected_mode) == int(GenLLRMode.GEN_INITIAL_GROUP):
            return f"mode {mode_name} replaces every group, so it is not allowed while the matrix has SW branch groups"

        target_groups = [idx for idx in target_group_indices if 0 <= idx < len(matrix.groups)]
        branch_targets = sorted({g for g in target_groups if matrix.group_branch_idx[g] != SW_BRANCH_NONE})

        allowed_values = {int(mode) for mode in SW_BRANCH_ALLOWED_MODES}
        if branch_targets and int(selected_mode) not in allowed_values:
            allowed_names = ", ".join(GenLLRMode(value).name for value in sorted(allowed_values))
            return (
                f"target groups {branch_targets} are SW branch groups, so mode {mode_name} ({int(selected_mode)}) is not allowed. "
                f"Allowed modes there: {allowed_names}. Point the targets (INITIAL_TARGET_GROUP_IDX or FIXED_TARGET_GROUP_IDX_LIST) "
                f"at the plain groups after the branch groups to use other modes"
            )
        return None

    def _Protected_Groups_Changed(self, base_matrix: LLR_MATRIX, new_matrix: LLR_MATRIX) -> Optional[str]:
        """타겟 앞의 그룹(분기 구간을 담는 보호 구간)이 trial 생성으로 바뀌었는지 본다.

        보호 구간은 target_group_indices의 최소 index 앞까지다. 그룹 수, row 수, iteration, CSW, 분기 index, 값 가운데
        하나라도 다르면 바뀐 것이다.

        Returns:
            Optional[str]: 바뀐 내용. 그대로면 None
        """
        base_matrix.Build_SW_Branch_Layout()
        if not base_matrix.has_sw_branch or not self.target_group_indices:
            return None
        num_protected = min(self.target_group_indices)
        if num_protected <= 0:
            return None
        if len(new_matrix.groups) < num_protected:
            return f"protected groups g0~g{num_protected - 1} were reduced to {len(new_matrix.groups)} groups"
        for g in range(num_protected):
            base_rows = base_matrix.groups[g]
            new_rows = new_matrix.groups[g]
            if len(base_rows) != len(new_rows):
                return f"protected g{g} row count changed {len(base_rows)} -> {len(new_rows)}"
            for r, (base_row, new_row) in enumerate(zip(base_rows, new_rows)):
                base_tail = (int(base_row.iter_start), int(base_row.iter_end), int(base_row.CSW), int(base_row.floor_flag))
                new_tail = (int(new_row.iter_start), int(new_row.iter_end), int(new_row.CSW), int(new_row.floor_flag))
                if base_tail != new_tail:
                    return f"protected g{g} row {r} (iteration, CSW, branch) changed {base_tail} -> {new_tail}"
                if not np.array_equal(base_row.ch_th_values, new_row.ch_th_values):
                    return f"protected g{g} row {r} values changed"
        return None

    def Set_Gen_Trial_LLR_Mode(self):
        if self.is_root:
            if DAO_CONFIG.IS_HBF_OPT:
                all_modes = DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE
            else:
                all_modes = DAO_CONFIG.Gen_LLR_Mode_SEQUENCE

            if not all_modes:
                error_msg = "Set_Current_Gen_Trial_LLR_Mode: Gen_LLR_Mode_SEQUENCE must define at least one mode."
                self.MPI_Abort(error_msg)

            mode_index = (self.current_stage_idx - 1) % len(all_modes)
            selected_mode = all_modes[mode_index]

            self.current_gen_trial_LLR_mode_index = mode_index
            self.current_gen_trial_LLR_mode = selected_mode
            self.current_gen_trial_LLR_mode_name = GenLLRMode(selected_mode).name

            # Gen_LLR_Mode_SEQUENCE 한 바퀴당 target_group_idx 하나씩 순환
            # (max_modification_trial 계산 전에 먼저 설정)
            sequence_cycle_count = (self.current_stage_idx - 1) // len(all_modes)

            # TARGET_GROUP_IDX 결정: target_group_indices 사용
            target_group_list = self.target_group_indices

            if not target_group_list:
                error_msg = "Set_Gen_Trial_LLR_Mode: target_group_indices must define at least one index."
                self.MPI_Abort(error_msg)
            self.current_target_group_list_index = sequence_cycle_count % len(target_group_list)
            self.current_target_group_idx = target_group_list[self.current_target_group_list_index]

            # 안전 검증: current_target_group_idx가 현재 매트릭스의 그룹 수를 초과하는 경우
            if self.optimal_LLR_matrix and self.current_target_group_idx >= len(self.optimal_LLR_matrix.groups):
                self.Write_Log_Lines(f"\t- WARNING: current_target_group_idx ({self.current_target_group_idx}) exceeds group count ({len(self.optimal_LLR_matrix.groups)}), using last group")
                self.current_target_group_idx = len(self.optimal_LLR_matrix.groups) - 1

            # SW 분기: 타겟에 분기 그룹이 있을 때 허용되지 않는 모드를 막는다
            if self.optimal_LLR_matrix is not None:
                sw_error = self.Check_SW_Branch_Mode_Allowed(self.optimal_LLR_matrix, selected_mode, self.target_group_indices)
                if sw_error is not None:
                    self.MPI_Abort(f"Set_Gen_Trial_LLR_Mode: {sw_error}")

            # Stage skip 조건 체크
            is_skip_this_stage = False

            # 1. GEN_INITIAL_GROUP은 stage 1에서만 동작
            if selected_mode == GenLLRMode.GEN_INITIAL_GROUP and self.current_stage_idx > 1:
                self.Write_Log_Lines(f"\t- GEN_INITIAL_GROUP only runs in stage 1, skipping (current stage: {self.current_stage_idx})")
                is_skip_this_stage = True

            # 2. SKIP_RESTART_GROUP 모드에서 restart group이면 skip
            if not is_skip_this_stage and self.optimal_LLR_matrix is not None and selected_mode in SKIP_RESTART_GROUP:
                group_idx = self.current_target_group_idx
                if group_idx < len(self.optimal_LLR_matrix.groups):
                    group = self.optimal_LLR_matrix.groups[group_idx]
                    if group and len(group) > 0 and group[0].is_group_restart:
                        self.Write_Log_Lines(f"\t- Target g{group_idx} is restart group, skipping this stage")
                        is_skip_this_stage = True

            # Note: INSERT_MUTATED_ROW는 기존 그룹에 row만 추가하므로 iteration을 증가시키지 않음 (제약 불필요)
            # INSERT_MUTATED_GROUP은 십시일반으로 iteration 확보 가능하므로 제약 불필요

            if is_skip_this_stage:
                # restart group이 target이면 이 stage 전체를 skip
                self.max_modification_trial = 0
            elif selected_mode == GenLLRMode.COPY_ROWS:
                if not self.optimal_LLR_matrix.groups:
                    error_msg = "Set_Gen_Trial_LLR_Mode: optimal_LLR_matrix must contain at least one group for COPY_ROWS mode."
                    self.MPI_Abort(error_msg)
                # current_target_group_idx 사용 (-1이면 마지막 그룹)
                target_group_idx = self.current_target_group_idx
                if target_group_idx == -1:
                    target_group_idx = len(self.optimal_LLR_matrix.groups) - 1
                # 후보 row 수 = 전체 row 수 - restart row 수 - 타겟 그룹 row 수
                num_candidate_rows = np.sum(self.optimal_LLR_matrix.header.num_row_each_group) - self.optimal_LLR_matrix.header.num_restart - len(self.optimal_LLR_matrix.groups[target_group_idx])
                # 외부 후보 수 추가 (캐시에 로드하여 Get_Copy_Row_Candidates에서 재사용)
                if COPY_ROWS_CONFIG.ENABLE_EXTERNAL_SINGLE_ROW:
                    external = self._Load_External_Single_Row_Candidates(self.optimal_LLR_matrix)
                    num_candidate_rows += len(external)
                self.max_modification_trial = len(self.optimal_LLR_matrix.groups[target_group_idx]) * num_candidate_rows
            elif selected_mode == GenLLRMode.COPY_GROUP:
                if not self.optimal_LLR_matrix.groups:
                    error_msg = "Set_Gen_Trial_LLR_Mode: optimal_LLR_matrix must contain at least one group for COPY_GROUP mode."
                    self.MPI_Abort(error_msg)
                # current_target_group_idx 사용 (-1이면 마지막 그룹)
                target_group_idx = self.current_target_group_idx
                if target_group_idx == -1:
                    target_group_idx = len(self.optimal_LLR_matrix.groups) - 1
                # 후보 그룹 수 = 전체 그룹 수 - restart 그룹 수 - 타겟 그룹 1개
                num_restart_groups = len(self.optimal_LLR_matrix.restart_groups) if hasattr(self.optimal_LLR_matrix, 'restart_groups') else 0
                num_candidate_groups = len(self.optimal_LLR_matrix.groups) - num_restart_groups - 1
                if num_candidate_groups <= 0:
                    error_msg = f"Set_Gen_Trial_LLR_Mode: COPY_GROUP requires at least 1 candidate group, got {num_candidate_groups}"
                    self.MPI_Abort(error_msg)
                # target group은 1개 고정, candidate groups만큼만 trial 수행
                self.max_modification_trial = num_candidate_groups
            elif selected_mode == GenLLRMode.SWAP_ROW:
                # Target group 내의 C(m, 2) 조합 수
                # (SWAP_ROW는 target group 내에서만 row pair swap)
                # current_target_group_idx 사용 (다른 모드들과 일관성)
                target_group_idx = self.current_target_group_idx
                if target_group_idx == -1:
                    target_group_idx = len(self.optimal_LLR_matrix.groups) - 1
                group = self.optimal_LLR_matrix.groups[target_group_idx]
                m = len(group)
                if m >= 2:
                    self.max_modification_trial = m * (m - 1) // 2
                else:
                    error_msg = f"Set_Gen_Trial_LLR_Mode: SWAP_ROW requires target group with 2+ rows, got {m}"
                    self.MPI_Abort(error_msg)
            elif selected_mode == GenLLRMode.REORDER_GROUP:
                # REORDER_GROUP: restart 제외한 그룹 수 기준으로 계산
                # - HD 모드: n*(n+1)/2 + 1
                # - SD 모드: n*(n+1) + 1 (각 후보마다 restart O/X 2회)
                num_non_restart = 0
                for idx in self.target_group_indices:
                    if idx < len(self.optimal_LLR_matrix.groups):
                        group = self.optimal_LLR_matrix.groups[idx]
                        if group and len(group) > 0 and not group[0].is_group_restart:
                            num_non_restart += 1
                is_hd_mode = (REFC_CONFIG.init_n == 1)
                trials_per_round = sum(range(num_non_restart, 0, -1))
                # Init_Reorder_Group_Mode의 total_trials와 같은 식: 초기 테스트 1 + 라운드 trial + 최종 검증 1
                if is_hd_mode:
                    self.max_modification_trial = 1 + trials_per_round + 1
                else:
                    self.max_modification_trial = 1 + trials_per_round * 2 + 1
            elif selected_mode == GenLLRMode.ADJUST_ITERATION:
                # ADJUST_ITERATION: target_groups(restart 제외) 수
                # 마지막 trial에서 temp_optimal → optimal 자동 전환 (is_update_at_last_trial)
                num_non_restart = 0
                for idx in self.target_group_indices:
                    if idx < len(self.optimal_LLR_matrix.groups):
                        group = self.optimal_LLR_matrix.groups[idx]
                        if group and len(group) > 0 and not group[0].is_group_restart:
                            num_non_restart += 1
                self.max_modification_trial = num_non_restart
            elif selected_mode == GenLLRMode.DELETE_ROW:
                # DELETE_ROW: Init_Delete_Row_Mode에서 max_modification_trial 설정
                # 여기서는 임시값, Init에서 덮어씀
                self.max_modification_trial = 1
            else:
                # config 직접 사용 모드: 모드별 MAX_TRIAL 적용
                MODE_MAX_TRIAL_MAP = {
                    GenLLRMode.GEN_INITIAL_GROUP: GEN_INITIAL_GROUP_CONFIG.MAX_TRIAL,
                    GenLLRMode.MUTATE_MATRIX: MUTATE_CONFIG.MAX_TRIAL,
                    GenLLRMode.MUTATE_CSW: MUTATE_CONFIG.MAX_TRIAL,
                    GenLLRMode.INSERT_RANDOM_GROUP: INSERT_RANDOM_GROUP_CONFIG.MAX_TRIAL,
                    GenLLRMode.INSERT_RANDOM_ROW: INSERT_RANDOM_ROW_CONFIG.MAX_TRIAL,
                    GenLLRMode.INSERT_MUTATED_GROUP: INSERT_MUTATED_GROUP_CONFIG.MAX_TRIAL,
                    GenLLRMode.INSERT_MUTATED_ROW: INSERT_MUTATED_ROW_CONFIG.MAX_TRIAL,
                    GenLLRMode.REGEN_DV: REGEN_DV_CONFIG.MAX_TRIAL,
                    GenLLRMode.REGEN_ROW: REGEN_ROW_CONFIG.MAX_TRIAL,
                    GenLLRMode.SPLIT_GROUP: SPLIT_GROUP_CONFIG.MAX_TRIAL,
                }
                mode_max_trial = MODE_MAX_TRIAL_MAP.get(selected_mode, -1)
                if mode_max_trial > 0:
                    self.max_modification_trial = mode_max_trial
                else:
                    self.max_modification_trial = DAO_CONFIG.MAX_OPTIMIZATION_TRIALS

        self.Bcast_Trial_LLR_Mode()

    def Set_Test_Environment(self, matrix, ch_idx:int = 0):
        """테스트 실행을 위한 환경을 준비한다.

        매트릭스를 저장하고 배치 파일을 생성하며 현재 시드 모드에 맞춰 사전 정리를 수행한다.

        Args:
            matrix (Optional[LLR_MATRIX]): 테스트 대상 매트릭스.

        Returns:
            None
        """
        self.MPI_Barrier()

        if matrix.matrix_idx > self._last_saved_local_matrix_idx:
            self.Save_LLR_Matrix(matrix=matrix, target_dir=self.local_session_dir, save_root_only=False)
            self._last_saved_local_matrix_idx = matrix.matrix_idx

        self.Make_Batch_File(matrix=matrix, ch_idx=ch_idx)
        
        self.Initialize_Run_ECC_End_Flag()

        if self.current_seed_mode == SeedMode.SAVE_UNCOR_SEED:
            self.Delete_Own_Uncors(ch_idx=ch_idx)
        elif self.current_seed_mode == SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED:
            # Ref-C는 실패 seed를 redecode 파일에 이어쓰기로 붙이므로, 이번 실행분만 남도록 이전 파일을 먼저 지운다
            self.Delete_Own_Uncors(ch_idx=ch_idx, is_redecoded_uncor=True)

        self.is_test_end = False
        self.ecc_start_time = time.time()

        # flag 초기화가 모든 프로세스에 반영된 후 while 루프 진입하도록 동기화
        # (이전 채널의 flag "1"이 남아있을 때, non-root가 root보다 먼저 Read_Run_ECC_End_Flag하는 race condition 방지)
        self.MPI_Barrier()

    def Finalize_ECC_Time(self):
        """ECC 수행 종료 시간 및 총 소요 시간을 계산한다.

        Set_Test_Environment에서 기록한 시작 시간을 바탕으로 종료 시간과 소요 시간을 계산한다.

        Returns:
            None
        """
        self.ecc_end_time = time.time()
        self.ecc_elapsed_time = self.ecc_end_time - self.ecc_start_time

    def Set_Seed_Mode(self, is_test_initial: Optional[bool] = False, is_test_optimal: Optional[bool] = None):
        """테스트에 사용할 시드 모드를 설정한다.

        초기/최적 테스트 여부와 누적 시드 정보를 바탕으로 시드 로딩·저장 모드를 결정한다.

        Args:
            is_test_initial (Optional[bool]): 초기 테스트 여부.
            is_test_optimal (Optional[bool]): 최적 매트릭스 테스트 여부.

        Returns:
            None
        """
        if self.is_root:
            # Dynamic Partial: 외부에서 LOAD_UNCOR_SEED_SAVE_UNCOR_SEED로 설정된 경우 보존
            if self.current_seed_mode == SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED:
                pass  # 기존 설정 유지, 분기 스킵
            else:
                if is_test_initial:
                    if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.TEST_FER:
                        self.current_seed_mode = SeedMode.DEFAULT
                    elif DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.SAVE_UNCOR:
                        self.current_seed_mode = SeedMode.SAVE_UNCOR_SEED
                    elif DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.REDECODE:
                        self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED
                    elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_NONE:
                        self.current_seed_mode = SeedMode.DEFAULT
                    elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED:
                        self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED
                    elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:
                        self.current_seed_mode = SeedMode.LOAD_UNCOR_VECTOR
                    else:
                        error_msg = f"Set_Seed_Mode(is_test_initial=True): Invalid initial_load_uncor_mode. initial_load_uncor_mode: {UNCOR_CONFIG.LOAD_UNCOR_MODE}"
                        self.MPI_Abort(error_msg)
                else:
                    if self.current_gen_trial_LLR_mode == GenLLRMode.GEN_INITIAL_GROUP:
                        if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_NONE:
                            self.current_seed_mode = SeedMode.DEFAULT
                        elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED:
                            self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED
                        elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:
                            self.current_seed_mode = SeedMode.LOAD_UNCOR_VECTOR
                        else:
                            error_msg = f"Set_Seed_Mode(GEN_INITIAL_GROUP): Invalid initial_load_uncor_mode. initial_load_uncor_mode: {UNCOR_CONFIG.LOAD_UNCOR_MODE}"
                            self.MPI_Abort(error_msg)
                    else:
                        if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED:
                            self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED
                        elif UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:
                            self.current_seed_mode = SeedMode.LOAD_UNCOR_VECTOR
                        else:
                            error_msg = f"Set_Seed_Mode(other mode): Invalid initial_load_uncor_mode. initial_load_uncor_mode: {UNCOR_CONFIG.LOAD_UNCOR_MODE}"
                            self.MPI_Abort(error_msg)

            if DAO_CONFIG.RUN_DAO_MODE != RunDAOMode.GEN_SINGLE_ROW:
                self.Write_Log_Lines(f"[current_seed_mode]: {self.current_seed_mode.name}")
        self.current_seed_mode = self._safe_bcast(self.current_seed_mode if self.is_root else None, "Bcast_current_seed_mode")

    def Set_Max_Error(self):
        """테스트 시 최대 error 수 한도를 설정한다.

        Args:
            없음.

        Returns:
            None

        Raises:
            ValueError: 지원되지 않는 시드 모드가 선택된 경우.
        """
        if self.is_root:
            self.max_error = DAO_CONFIG.MAX_RUN_ECC_ERRORS
            
            if self.current_seed_mode in [SeedMode.SAVE_UNCOR_SEED, SeedMode.DEFAULT]:
                self.Write_Log_Lines(f"[max_error]: {self.max_error}")
            elif self.is_load_seed_mode:
                pass
            else:
                error_msg = f"Set_Max_Error: Invalid current_seed_mode. current_seed_mode: {self.current_seed_mode}"
                self.MPI_Abort(error_msg)
        
        self.max_error = self._safe_bcast(self.max_error if self.is_root else None, "Bcast_max_error")

    def Set_Enable_Print_CSW_LOG(self, is_test_initial: Optional[bool] = False, is_test_optimal: Optional[bool] = False):
        """CSW 로그 출력 활성화 여부를 설정한다.
        """
        self.enable_print_CSW_log = 0
        if self.is_root:
            if is_test_optimal or \
                (is_test_initial and \
                    DAO_CONFIG.RUN_DAO_MODE not in [RunDAOMode.TEST_FER, RunDAOMode.SAVE_UNCOR]):
                if self.is_load_seed_mode:
                    self.enable_print_CSW_log = 1
                else:
                    self.enable_print_CSW_log = 0

            if DAO_CONFIG.RUN_DAO_MODE != RunDAOMode.GEN_SINGLE_ROW:
                self.Write_Log_Lines(f"[enable_print_CSW_log]: {self.enable_print_CSW_log}")

        self.enable_print_CSW_log = self._safe_bcast(self.enable_print_CSW_log if self.is_root else None, "Bcast_enable_print_CSW_log")

    def Set_Ref_C_Parameters(self, is_test_initial: Optional[bool] = False, is_test_optimal: Optional[bool] = False):
        """Ref-C 실행에 필요한 파라미터를 설정한다.

        시드 모드와 max_error를 갱신하고 최적 테스트 시 결과를 초기화한다.

        Args:
            is_test_initial (Optional[bool]): 초기 테스트 여부.
            is_test_optimal (Optional[bool]): 최적 테스트 여부.

        Returns:
            None
        """
        self.Set_Seed_Mode(is_test_initial=is_test_initial, is_test_optimal=is_test_optimal)
        self.Set_Max_Error()
        self.Set_Enable_Print_CSW_LOG(is_test_initial=is_test_initial, is_test_optimal=is_test_optimal)
        if is_test_optimal:
            self.Reset_Optimal_Results()

    def Set_Update_Flags(self) -> None:
        """최종 trial에서 업데이트 여부를 설정한다.

        현재 trial 생성 모드에 따라 마지막 트라이얼에서 최적화 결과를 반영할지 결정한다.

        Args:
            없음.

        Returns:
            None
        """
        if self.is_root:
            if self.current_gen_trial_LLR_mode in [
                GenLLRMode.INSERT_RANDOM_ROW,
                GenLLRMode.INSERT_RANDOM_GROUP,
                GenLLRMode.INSERT_MUTATED_GROUP,
                GenLLRMode.INSERT_MUTATED_ROW,
                GenLLRMode.GEN_INITIAL_GROUP,
                GenLLRMode.COPY_GROUP,
                GenLLRMode.REORDER_GROUP,
                GenLLRMode.ADJUST_ITERATION,
                GenLLRMode.DELETE_ROW,
                GenLLRMode.INSERT_RESTART_GROUP,
                GenLLRMode.SPLIT_GROUP,
                ]:
                self.is_update_at_last_trial = True
            else:
                self.is_update_at_last_trial = False

        self.is_update_at_last_trial = self._safe_bcast(self.is_update_at_last_trial if self.is_root else None, "Bcast_is_update_at_last_trial")

    def Set_Optimal_Matrix(self):
        """최적 매트릭스 상태를 갱신한다.

        이전 최적 매트릭스를 보관한 뒤 선택된 업데이트 모드에 따라 현재 최적 매트릭스를 재설정한다.

        Args:
            없음.

        Returns:
            None
        """
        self.Set_Previous_Optimal_Matrix()
        self.Set_Current_Optimal_Matrix()

    def Set_Previous_Optimal_Matrix(self):
        """이전 최적 매트릭스를 보관한다.

        Args:
            없음.

        Returns:
            None
        """
        if self.update_mode == UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT:
            if self.optimal_LLR_matrix is not None:
                self.previous_optimal_LLR_matrix = self.optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
        elif self.update_mode == UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL:
            if self.temp_optimal_LLR_matrix is not None:
                self.previous_optimal_LLR_matrix = self.temp_optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
            elif self.optimal_LLR_matrix is not None:
                self.previous_optimal_LLR_matrix = self.optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
        elif self.update_mode == UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT:
            if self.temp_optimal_LLR_matrix is None:
                if self.optimal_LLR_matrix is not None:
                    self.previous_optimal_LLR_matrix = self.optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
            else:
                self.previous_optimal_LLR_matrix = self.temp_optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
        else:
            self.MPI_Abort(f"Set_Previous_Optimal_Matrix: Unknown update_mode={self.update_mode}")

    def Set_Current_Optimal_Matrix(self):
        """현재 최적 또는 임시 최적 매트릭스를 설정한다.

        Change iteration mode의 경우, threshold를 활용하여 max iteration을 설정한다.

        Args:
            없음.

        Returns:
            None
        """
        if self.update_mode == UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT:
            self.optimal_LLR_matrix = self.current_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
        elif self.update_mode == UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL:
            self.optimal_LLR_matrix = self.temp_optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
        elif self.update_mode == UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT:
            self.temp_optimal_LLR_matrix = self.current_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
        else:
            self.MPI_Abort(f"Set_Current_Optimal_Matrix: Unknown update_mode={self.update_mode}")

    def Setup(self):
        self.simulation_start = datetime.datetime.now()
        timestamp = self.simulation_start.strftime("%Y_%m_%d_%H_%M_%S")
        self.session_timestamp = self._safe_bcast(timestamp if self.is_root else None, "Bcast_session_timestamp")
        self.Set_Work_Space()
        self._current_initial_matrix_idx = DAO_CONFIG.Get_Initial_Matrix_Idx_List()[0]
        self.Initialize_LLR_Matrix()
        self.Set_Python_Seed()
        self.Validate_Config()
        self.Write_Log_Separator("Simulation Log", SEPARATOR_TYPE2)

    def Setup_Uncors(self):
        """Uncor pool을 생성하고 초기 uncor를 로드한다.

        Core speed test 이후에 호출되어야 excluded_cores가 반영된 분배가 이루어진다.
        LOAD_UNCOR_MODE가 DISABLED이면 아무 동작도 하지 않는다.

        흐름:
        1. Setup_Uncor_Pool: 각 active core의 uncor_pool/ 디렉토리에 1회 사전 분배
        2. Load_Uncors_From_Pool: 초기 test_mode의 uncor를 pool에서 working directory로 복사
        3. total_num_uncors 검증
        """
        # Pool 생성 (Input → 각 코어의 uncor_pool/)
        self.Setup_Uncor_Pool()

        if not self.is_uncor_pool_ready:
            return

        # 초기 test_mode 결정: Dynamic Partial에서 초기에는 항상 FULL 로드 (Partial pool은 아직 없음)
        initial_test_mode = TestMode.FULL

        # Pool에서 초기 uncor 로드
        self.Load_Uncors_From_Pool(initial_test_mode)

        # Uncor 분배 후 검증 (total_num_uncors가 채워진 뒤 수행)
        if not all(cnt > 0 for cnt in self.total_num_uncors):
            error_msgs = []
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                error_msgs.append(f"total_num_uncors must not be zero. Found {self.total_num_uncors[ch_idx]} for channel {ch_idx}.")
            self.MPI_Abort("\n".join(error_msgs))

    def Set_Python_Seed(self):
        if DEBUG_CONFIG.ENABLE_DEBUG_MODE:
            base_seed = 0
        else:
            base_seed = int(time.time()) if self.is_root else None
        self.base_seed = self._safe_bcast(base_seed if self.is_root else None, "Bcast_base_seed")
        local_init_seed = self.base_seed + self.rank * 10000

        random.seed(local_init_seed)
        np.random.seed(local_init_seed)
        self.Write_Log_Lines(f"[Base seed] {base_seed}")

    def Restore_Random_State_If_Configured(self) -> None:
        """디버깅 재현을 위해 설정에서 Random state를 복원한다.

        DebugConfig.ENABLE_GET_RANDOM_STATE_FROM_CONFIG가 True인 경우,
        base64로 인코딩된 random state를 디코딩하여 복원한다.

        Args:
            없음.

        Returns:
            None
        """
        if not DEBUG_CONFIG.ENABLE_GET_RANDOM_STATE_FROM_CONFIG:
            return

        if DEBUG_CONFIG.RANDOM_STATE_TO_SET is None:
            error_msg = "ENABLE_GET_RANDOM_STATE_FROM_CONFIG is True but RANDOM_STATE_TO_SET is None. Please set RANDOM_STATE_TO_SET in DebugConfig."
            self.MPI_Abort(error_msg)

        try:
            state_bytes = base64.b64decode(DEBUG_CONFIG.RANDOM_STATE_TO_SET)
            rng_state = pickle.loads(state_bytes)
            random.setstate(rng_state)
            self.Write_Log_Lines(f"[Random state restored from base64]")
        except Exception as e:
            error_msg = f"Failed to restore random state from base64: {e}"
            self.MPI_Abort(error_msg)

    def Set_Work_Space(self):
        self.Make_Dirs()
        self.Initialize_Log()
        self.BACKUP_SRC()
        self.Print_Initial_Setup()
        self.Build_ECC()
        self.Copy_ECC_EXE()
        self.Copy_H_Matrix()

    def BACKUP_SRC(self):
        if not self.is_root:
            return

        src_files = [
            f for f in os.listdir(PATH_CONFIG.SRC_DIR_PATH)
            if f.endswith(".py") and os.path.isfile(os.path.join(PATH_CONFIG.SRC_DIR_PATH, f))
        ]

        for file_name in src_files:
            src_path = os.path.join(PATH_CONFIG.SRC_DIR_PATH, file_name)
            shutil.copy2(src_path, self.src_backup_dir)

        self.Write_Log_Lines(
            f"[Source files backed up] count={len(src_files)} → {self.src_backup_dir}"
        )

    def Copy_Row(self, matrix: LLR_MATRIX, target_row_idx: int, candidate_idx: int):
        """
        지정된 타겟 그룹의 타겟 Row를 후보 Row의 값으로 교체(Copy)합니다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).
        """
        if not matrix.groups:
            self.Write_Log_Lines(f"\t- [Error] Matrix must contain at least one group.")
            return

        # 타겟 그룹 인덱스 결정
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(matrix.groups) - 1

        if target_group_idx >= len(matrix.groups):
            self.Write_Log_Lines(f"\t- [Error] Target group index {target_group_idx} out of range.")
            return

        target_group = matrix.groups[target_group_idx]

        if not target_group:
            self.Write_Log_Lines(f"\t- [Error] Target group {target_group_idx} must not be empty.")
            return

        if target_row_idx >= len(target_group):
            self.Write_Log_Lines(f"\t- [Error] Target row index {target_row_idx} out of range (group {target_group_idx} has {len(target_group)} rows).")
            return

        if candidate_idx >= len(self.copy_row_candidates):
            self.Write_Log_Lines(f"\t- [Error] Candidate index {candidate_idx} out of range (max: {len(self.copy_row_candidates) - 1}).")
            return

        target_row = target_group[target_row_idx]
        candidate_data = self.copy_row_candidates[candidate_idx]

        # 교체 전 값 (처음 10개만)
        old_values = target_row.ch_th_values[:10].tolist() if len(target_row.ch_th_values) >= 10 else target_row.ch_th_values.tolist()

        # 교체 수행 (타겟 row가 HD 복호의 HBF 구간에 있으면 dv_idx 0의 TH는 상수)
        target_row.ch_th_values = np.array(candidate_data['ch_th_values'], copy=True)
        matrix.Fill_Columns_Fixed_In_HBF_Iterations(target_row.ch_th_values, target_row.iter_end)

        # 교체 후 값 (처음 10개만)
        new_values = target_row.ch_th_values[:10].tolist() if len(target_row.ch_th_values) >= 10 else target_row.ch_th_values.tolist()

        orig_g = candidate_data['orig_group']
        orig_r = candidate_data['orig_row']
        if orig_g == -1:
            self.Write_Log_Lines(f"\t- Row Copy: Target Group {target_group_idx} Row {target_row_idx} <== External Single Row Candidate")
        else:
            self.Write_Log_Lines(f"\t- Row Copy: Target Group {target_group_idx} Row {target_row_idx} <== Candidate (Group {orig_g}, Row {orig_r})")
        self.Write_Log_Lines(f"\t    - Before (first 10): {old_values}")
        self.Write_Log_Lines(f"\t    - After  (first 10): {new_values}")

    def Copy_Group(self, matrix: LLR_MATRIX, candidate_idx: int) -> bool:
        """
        지정된 타겟 그룹을 후보 그룹의 모든 rows로 교체(Copy)합니다.
        타겟 그룹은 current_target_group_idx로 결정됩니다 (-1이면 마지막 그룹).

        Returns:
            bool: 성공하면 True, 실패하면 False
        """
        if not matrix.groups:
            self.Write_Log_Lines(f"\t- [Error] Matrix must contain at least one group.")
            return False

        # 타겟 그룹 인덱스 결정
        target_group_idx = self.current_target_group_idx
        if target_group_idx == -1:
            target_group_idx = len(matrix.groups) - 1

        if target_group_idx >= len(matrix.groups):
            self.Write_Log_Lines(f"\t- [Error] Target group index {target_group_idx} out of range.")
            return False

        if candidate_idx >= len(self.copy_group_candidates):
            self.Write_Log_Lines(f"\t- [Error] Candidate index {candidate_idx} out of range (max: {len(self.copy_group_candidates) - 1}).")
            return False

        target_group = matrix.groups[target_group_idx]
        candidate_data = self.copy_group_candidates[candidate_idx]
        orig_group_idx = candidate_data['orig_group_idx']

        # 타겟 그룹의 iteration 정보 저장 (유지해야 함)
        if target_group:
            target_iter_start = target_group[0].iter_start
            target_iter_end = target_group[0].iter_end
        else:
            self.Write_Log_Lines(f"\t- [Error] Target group {target_group_idx} is empty.")
            return False

        # 타겟 그룹 비우기
        target_group.clear()

        # 후보 그룹의 모든 rows를 타겟 그룹에 복사
        for row_data in candidate_data['rows']:
            new_row = LLR_Row(
                ch_th_values=np.array(row_data['ch_th_values'], copy=True),
                CSW=row_data['CSW'],
                floor_flag=row_data['floor_flag'],
                iter_start=target_iter_start,  # 타겟 그룹의 iteration 사용
                iter_end=target_iter_end,
                is_group_restart=False
            )
            # 타겟 그룹이 HD 복호의 HBF 구간에 있으면 dv_idx 0의 TH는 상수
            matrix.Fill_Columns_Fixed_In_HBF_Iterations(new_row.ch_th_values, target_iter_end)
            target_group.append(new_row)

        # Header 업데이트
        matrix.header.num_row_each_group[target_group_idx] = len(target_group)
        matrix.header.type_each_group[target_group_idx] = candidate_data['group_type']

        self.Write_Log_Lines(f"\t- Group Copy: Target Group {target_group_idx} <== Candidate Group {orig_group_idx}")
        self.Write_Log_Lines(f"\t    - Copied {len(target_group)} rows from Group {orig_group_idx} to Group {target_group_idx}")
        self.Write_Log_Lines(f"\t    - Iteration: [{target_iter_start}, {target_iter_end}]")

        return True

    def Set_Loop_Start_Time(self):
        if self.is_root:
            self.loop_start_time = time.time()
    def Calc_Loop_Elapsed_Time(self):
        if self.is_root:
            self.loop_elapsed_time = time.time() - self.loop_start_time
            self.total_elapsed_time = time.time() - self.ecc_start_time
            self.loop_end_time = datetime.datetime.now()
            self.loop_end_time_stamp = self.loop_end_time.strftime("%Y%m%d_%H%M%S")

    def Test_LLR(self, matrix, is_test_initial: Optional[bool] = False, is_test_optimal: Optional[bool] = False,
                 enable_early_channel_exit: bool = False):
        """LLR 매트릭스에 대한 전체 테스트 루프를 실행한다.

        Ref-C 구성과 테스트 환경을 설정한 뒤 FER 결과를 얻을 때까지 ECC 실행과 결과 수집을 반복한다.

        Args:
            matrix (Optional[LLR_MATRIX]): 테스트 대상 매트릭스.
            is_test_initial (Optional[bool]): 초기 테스트 여부.
            is_test_optimal (Optional[bool]): 최적 테스트 여부.
            enable_early_channel_exit (bool): 채널별 열화 감지 시 나머지 채널 스킵.

        Returns:
            None
        """
        
        self.Set_Ref_C_Parameters(is_test_initial=is_test_initial, is_test_optimal=is_test_optimal)
        test_mode_str = "Partial" if self.current_test_mode == TestMode.PARTIAL else "Full"
        is_load_seed_mode = self.is_load_seed_mode

        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            
            self.Write_Log_Separator(
                f"{test_mode_str} Test: ch {ch_idx} [{ch_idx + 1}/{REFC_CONFIG.NUM_TARGET_CHANNELS}]",
                SEPARATOR_TYPE1
                )
            self.Set_Test_Environment(matrix=matrix, ch_idx=ch_idx)

            # while 루프 카운트 (동기화 불필요, 추적용)
            loop_count = 0

            while not self.is_test_end:
                # root가 이전 iteration에서 플래그를 쓴 경우, worker가 불필요한 Run_ECC 실행 방지
                self.Read_Run_ECC_End_Flag()
                if self.is_test_end:
                    self._Write_Run_ECC_End_Ack()
                    break
                loop_count += 1
                self.Set_Loop_Start_Time()
                self.Run_ECC(ch_idx=ch_idx)
                # load_seed_mode: while 1회만 실행되므로 루프 밖 Gather(True)가 동일 결과 덮어씀 → 스킵
                if not is_load_seed_mode:
                    self.Gather_Ref_C_Results(matrix=matrix, ch_idx=ch_idx, is_test_end=False)
                self.Check_Test_End(ch_idx=ch_idx)

                # is_test_initial: while 내 첫 1회만 출력
                # is_test_initial 아님: while 내 출력 안 함
                if self.current_seed_mode in [SeedMode.DEFAULT, SeedMode.SAVE_UNCOR_SEED]:
                    self.Print_Test_Result(matrix=matrix, is_test_optimal=is_test_optimal, ch_idx=ch_idx, is_test_end=False)

            # while 루프 탈출 경로와 무관하게 모든 프로세스가 ack 작성
            self._Write_Run_ECC_End_Ack()

            self.Gather_Ref_C_Results(matrix=matrix, ch_idx=ch_idx, is_test_end=True)
            # Gather 안의 배리어를 지난 뒤에 세어야 아직 ECC 중인 정상 rank를 미응답으로 적지 않는다
            self._Report_Missing_Acks()
            self.Print_Test_Result(matrix=matrix, is_test_optimal=is_test_optimal, ch_idx=ch_idx, is_test_end=True)

            self.Process_CSW_Logs(matrix=matrix, ch_idx=ch_idx, is_test_initial=is_test_initial)

            # SAVE_UNCOR 모드: 채널 테스트 직후 즉시 uncor 취합 (root-only 파일 I/O, MPI 통신 없음)
            if self.current_seed_mode == SeedMode.SAVE_UNCOR_SEED:
                self.Gather_And_Archive_Uncors(
                    matrix=matrix, ch_idx=ch_idx, is_uncor_type_seed=True,
                    is_redecoded_uncor=False, test_mode=self.current_test_mode
                )

            # 채널별 열화 감지 시 나머지 채널 스킵
            if enable_early_channel_exit and self._Is_Channel_Degraded(matrix, ch_idx):
                self.Write_Log_Lines(f"[Early channel exit] ch{ch_idx} degraded, skipping remaining channels")
                self._Fill_Untested_Channels(matrix, ch_idx + 1)
                break

        self.Cleanup_Test_Environment()

    def Process_CSW_Logs(self, matrix, ch_idx, is_test_initial: Optional[bool] = False):
        if not self.enable_print_CSW_log:
            return
        self.Gather_CSW_Logs(matrix=matrix, ch_idx=ch_idx)
        self.Write_Log_Lines(f"[Gathered Ref-C Results] CSW logs are gathered.")
        self.Delete_CSW_Logs()
        # root의 CSW 파일 읽기 완료 후 non-root가 Cleanup에서 삭제하는 race condition 방지
        self.MPI_Barrier()

    def Test_Core_Speed(self):
        """각 코어의 속도를 사전 측정하여 느린 코어를 식별한다.

        모든 프로세스가 동일한 시드(CORE_SPEED_TEST_SEED)로 짧은 테스트를 실행하고,
        소요 시간을 측정하여 평균 대비 CORE_SPEED_CUTOFF_RATIO배 이상 느린 코어를 제외한다.

        Args:
            없음.

        Returns:
            None
        """
        if not SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST:
            return

        self.Write_Log_Separator("Core Speed Test", SEPARATOR_TYPE2)

        # Speed test용 seed mode 설정 (이후 Set_Seed_Mode에서 자동으로 재설정됨)
        self.current_seed_mode = SeedMode.DEFAULT

        # 배치 파일 생성 (SPEED_TEST_REFC_CONFIG 사용, 고정 시드)
        self.Make_Batch_File_For_Speed_Test(matrix=self.current_LLR_matrix, ch_idx=0)

        # 속도 측정 실행
        start_time = time.time()
        self.Run_ECC(ch_idx=0)
        elapsed_time = time.time() - start_time

        # 모든 프로세스의 소요 시간 수집 (allgather: 모든 rank가 결과 받음)
        all_elapsed_times = self._safe_allgather(elapsed_time, "Allgather_core_elapsed_times")
        self.core_elapsed_times = all_elapsed_times

        if self.is_root:
            # 각 코어별로 자신을 제외한 평균 계산 및 판단
            excluded_cores = []
            for rank_idx, current_time in enumerate(all_elapsed_times):
                other_times = [t for i, t in enumerate(all_elapsed_times) if i != rank_idx]
                mean_time = sum(other_times) / len(other_times) if other_times else 0.0

                if mean_time > 0 and current_time > mean_time * SPEED_TEST_REFC_CONFIG.CORE_SPEED_CUTOFF_RATIO:
                    excluded_cores.append(rank_idx)

            # Root(rank 0) 보호: root는 파일 I/O, 결과 집계, 매트릭스 생성 등 핵심 역할 담당
            if 0 in excluded_cores:
                excluded_cores.remove(0)
                self.Write_Log_Lines(
                    f"[Core Speed Test] ⚠️ Root(rank 0)가 느린 코어로 감지되었으나, "
                    f"orchestration 역할 때문에 제외 목록에서 복원합니다."
                )

            self.excluded_cores = excluded_cores
            overall_mean = sum(all_elapsed_times) / len(all_elapsed_times)
            self.Write_Log_Lines(
                f"[Core Speed Test] 전체 평균: {overall_mean:.2f}초, "
                f"제외 코어 수: {len(excluded_cores)}/{len(all_elapsed_times)}"
            )
            if excluded_cores:
                for rank_idx in excluded_cores:
                    current_time = all_elapsed_times[rank_idx]
                    other_times = [t for i, t in enumerate(all_elapsed_times) if i != rank_idx]
                    mean_time = sum(other_times) / len(other_times)
                    self.Write_Log_Lines(
                        f"  ⚠️  Rank {rank_idx}: {current_time:.2f}초 (평균: {mean_time:.2f}초, "
                        f"비율: {current_time/mean_time:.2f}x)"
                    )

        # 제외 코어 목록을 모든 프로세스에 broadcast
        self.excluded_cores = self._safe_bcast(self.excluded_cores if self.is_root else None, "Bcast_excluded_cores")
        self.is_current_core_excluded = self.rank in self.excluded_cores

        if self.is_current_core_excluded:
            self.Write_Log_Lines(f"[Core Speed Test] ⚠️  현재 코어(Rank {self.rank})는 느려서 이후 테스트에서 제외됩니다.")

        # 테스트 환경 정리 (배치 파일, result 파일 등 삭제)
        self.Cleanup_Test_Environment()

        self.MPI_Barrier()
        self._last_speed_test_time = time.time()
        self.Write_Log_Separator("Core Speed Test Complete", SEPARATOR_TYPE2)

    def Periodic_Recheck(self, stage_idx: int):
        """N stage마다 speed test + uncor 재분배를 수행한다.

        Phase 1: Speed test 재실행 → excluded_cores, core_elapsed_times 갱신
        Phase 2: Setup_Uncor_Pool → 새 active cores 반영 균일 분배
        """
        interval = SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_STAGES
        if interval <= 0:
            return
        if not SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST:
            return
        if stage_idx == 1 or stage_idx % interval != 0:
            return

        self.Write_Log_Separator(f"Periodic Recheck (Stage {stage_idx})", SEPARATOR_TYPE2)

        # Phase 1: Speed test
        excluded_changed = self._Recheck_Speed_Test()

        # Phase 2: 균일 분배 (excluded_cores 변경 시에만 — 복귀/제외된 코어에 uncor 재배분)
        if excluded_changed:
            self._Redistribute_Uncor_Pool_Uniform()
        else:
            self.Write_Log_Lines("[Periodic_Recheck] excluded_cores 변경 없음, 균일 재분배 스킵")

        self.Write_Log_Separator(f"Periodic Recheck Complete (Stage {stage_idx})", SEPARATOR_TYPE2)

    def _Recheck_Speed_Test(self) -> bool:
        """모든 코어가 참여하여 speed test를 재실행하고 excluded_cores를 갱신한다.

        Returns:
            bool: excluded_cores가 변경되었으면 True, 동일하면 False.
        """
        prev_excluded = list(self.excluded_cores)

        # 모든 코어가 speed test에 참여하도록 임시 리셋
        self.is_current_core_excluded = False

        # 현재 매트릭스를 local_session_dir에 저장 (speed test batch에서 필요)
        self.Save_LLR_Matrix(
            matrix=self.current_LLR_matrix,
            target_dir=self.local_session_dir,
            save_root_only=False
        )

        # Speed test 재실행 (core_elapsed_times도 갱신됨)
        self.Test_Core_Speed()

        # 변경 여부 판정 + 로그
        excluded_changed = set(self.excluded_cores) != set(prev_excluded)
        if excluded_changed:
            self.Write_Log_Lines(
                f"[Periodic_Recheck] excluded_cores 변경: {prev_excluded} → {self.excluded_cores}"
            )
        else:
            self.Write_Log_Lines(f"[Periodic_Recheck] excluded_cores 변경 없음.")
        return excluded_changed

    def _Redistribute_Uncor_Pool_Uniform(self):
        """pool 상태를 리셋하고 새 active cores 기준으로 균일 재분배한다.

        Phase 1에서 excluded→active로 복귀한 코어에 uncor을 배분하기 위해 수행한다.
        Dynamic Partial 모드에서는 tmp_partial_uncors에 저장된 fail uncor를 Partial pool로 재분배한다.
        """
        self.Write_Log_Lines("[Periodic_Recheck] Uncor pool 균일 재분배 시작")

        # Pool 상태 리셋
        self.pool_has_uncor = {
            TestMode.PARTIAL: [False] * REFC_CONFIG.NUM_TARGET_CHANNELS,
            TestMode.FULL: [False] * REFC_CONFIG.NUM_TARGET_CHANNELS,
        }
        self.is_uncor_pool_ready = False
        self.current_loaded_test_mode = None

        # 새 active cores 기준 균일 분배 (Full만)
        self.Setup_Uncor_Pool()

        # Dynamic Partial: tmp_partial_uncors에서 Partial pool 재구성
        if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
            is_uncor_type_seed = (UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED)

            # root에서 소스 경로 결정 후 bcast (MPI 동기화)
            partial_src_dir = None
            if self.is_root:
                tmp_partial_base = Path(self.session_uncor_dir) / TMP_PARTIAL_UNCORS_DIR_NAME
                if tmp_partial_base.exists():
                    subdirs = [d for d in tmp_partial_base.iterdir() if d.is_dir()]
                    if subdirs:
                        partial_src_dir = str(max(subdirs, key=lambda d: d.stat().st_mtime))
            partial_src_dir = self._safe_bcast(
                partial_src_dir if self.is_root else None,
                "Bcast_partial_src_dir"
            )

            if partial_src_dir:
                partial_src_path = Path(partial_src_dir)
                for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                    file_name = self.Get_Uncor_File_Name(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
                    src_path = partial_src_path / file_name
                    # src_path는 root만 실제 파일을 가지고 있음 — _Setup_Uncor_Pool_For_Channel이 처리
                    self._Setup_Uncor_Pool_For_Channel(
                        ch_idx=ch_idx,
                        is_uncor_type_seed=is_uncor_type_seed,
                        test_mode=TestMode.PARTIAL,
                        src_path=src_path if self.is_root else None
                    )
                self.Write_Log_Lines(f"[Periodic_Recheck] Partial pool 재분배 완료 (소스: {partial_src_path.name})")
            else:
                self.Write_Log_Lines("[Periodic_Recheck] tmp_partial_uncors 없음, Partial pool 스킵")

        # 항상 Load 수행
        initial_test_mode = TestMode.PARTIAL if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST else TestMode.FULL
        self.Load_Uncors_From_Pool(initial_test_mode)

        self.Write_Log_Lines("[Periodic_Recheck] Uncor pool 균일 재분배 완료")


    def _Run_Test_Stage(self, test_mode: TestMode, matrix, **kwargs):
        """test mode 설정 → uncor 로드 → Test_LLR 실행을 일괄 수행한다."""
        self.current_test_mode = test_mode
        self.Ensure_Uncors_Loaded(test_mode)
        self.Test_LLR(matrix, **kwargs)

    def Test_Initial_LLR(self):
        """초기 매트릭스를 대상으로 테스트한다.

        ENABLE_TWO_STAGE_TEST에 따라 동작이 달라진다:
        - False (기존 모드): Full 테스트만 수행
        - True (Dynamic Partial 모드): Full 테스트(SAVE 모드) + fail uncor 추출 → Partial pool 동적 생성

        Args:
            없음.

        Returns:
            None
        """
        if not UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
            # 기존 모드: Full 테스트만
            self._Run_Test_Stage(TestMode.FULL, self.current_LLR_matrix, is_test_initial=True)
            self._Cleanup_LLR_Matrix_Files()
            return

        # ===== Dynamic Partial 모드 =====

        # Step 1: Full 테스트 (LOAD_UNCOR_SEED_SAVE_UNCOR_SEED로 fail seed 저장)
        self.Write_Log_Lines(f"\n[Initial Full Test] Testing with full uncors (SAVE mode)")
        self.current_test_mode = TestMode.FULL
        # Seed mode 강제 설정 (Set_Seed_Mode 우회)
        if self.is_root:
            self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED
        self.current_seed_mode = self._safe_bcast(
            self.current_seed_mode if self.is_root else None,
            "Bcast_initial_save_seed_mode"
        )
        self.Ensure_Uncors_Loaded(TestMode.FULL)
        self.Test_LLR(self.current_LLR_matrix, is_test_initial=True)

        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            self.Write_Log_Lines(
                f"[Initial Full Result] ch{ch_idx} FER: {self.current_LLR_matrix.FERs[ch_idx]:.2e}"
            )

        # Step 2: Gather fail uncors → Partial pool 동적 구성
        has_partial = self._Build_Initial_Partial_Pool()
        if not has_partial:
            # Partial=0: graceful stop (WP-E)
            self._Signal_Graceful_Stop_No_Partial()

        # Step 3: Partial FER = 1.0 설정 (Partial pool은 정의상 모두 fail → FER=1.0)
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            self.current_LLR_matrix.FERs_partial[ch_idx] = 1.0
            self.Write_Log_Lines(
                f"[Initial Partial Result] ch{ch_idx} FER: 1.00e+00 (dynamic, {self.total_num_partial_uncors[ch_idx]} fail uncors)"
            )

        # Step 4: Seed mode 복원
        if self.is_root:
            self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED
        self.current_seed_mode = self._safe_bcast(
            self.current_seed_mode if self.is_root else None,
            "Bcast_restore_initial_seed_mode"
        )

        self._Cleanup_LLR_Matrix_Files()

    def _Build_Initial_Partial_Pool(self) -> bool:
        """초기 Full test의 fail uncor를 수집하여 Partial pool을 구성한다.

        Test_Initial_LLR에서 LOAD_UNCOR_SEED_SAVE_UNCOR_SEED 모드로 테스트 후 호출.
        각 프로세스의 redecoded uncor(= fail codeword)를 Gather하고 Partial pool로 분배.

        Returns:
            bool: True면 Partial pool 구성 성공, False면 fail uncor 없음 (0개)
        """
        is_uncor_type_seed = (UNCOR_CONFIG.LOAD_UNCOR_MODE != DAOLoadUncorMode.LOAD_VECTOR)

        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            # Gather redecoded uncors (root only: 파일 병합)
            src_path = self.Gather_And_Archive_Uncors(
                matrix=self.current_LLR_matrix,
                ch_idx=ch_idx,
                is_uncor_type_seed=is_uncor_type_seed,
                is_redecoded_uncor=True,
                test_mode=TestMode.FULL
            )

            # Partial pool용 tmp_partial_uncors에 저장
            if self.is_root and src_path and src_path.exists():
                tmp_partial_dir = self._Get_Tmp_Partial_Uncor_Dir(matrix=self.current_LLR_matrix)
                tmp_partial_dir.mkdir(parents=True, exist_ok=True)
                dest_file_name = self.Get_Uncor_File_Name(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
                tmp_dest = tmp_partial_dir / dest_file_name
                shutil.copy2(src_path, tmp_dest)

            # Partial pool로 분배 (root: 파일 기록, all: pool_has_uncor 동기화)
            self._Setup_Uncor_Pool_For_Channel(
                ch_idx=ch_idx,
                is_uncor_type_seed=is_uncor_type_seed,
                test_mode=TestMode.PARTIAL,
                src_path=src_path
            )

        # total_num_partial_uncors 동기화 (Gather_And_Archive_Uncors가 total_num_uncors를 갱신했으므로 복사)
        self.MPI_Barrier()
        self.total_num_uncors = self._safe_bcast(
            self.total_num_uncors if self.is_root else None,
            "Bcast_total_num_uncors_initial_partial"
        )
        # Partial 수를 별도 변수에 저장
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            self.total_num_partial_uncors[ch_idx] = self.total_num_uncors[ch_idx]

        # 전체 Partial count 확인
        total_partial = 0
        if self.is_root:
            total_partial = sum(self.total_num_partial_uncors)
        total_partial = self._safe_bcast(
            total_partial if self.is_root else None,
            "Bcast_total_partial_initial"
        )

        if total_partial == 0:
            self.Write_Log_Lines("[Initial Partial] No fail uncors found. All uncors decoded successfully.")
            return False

        self.Write_Log_Lines(
            f"[Initial Partial] Dynamic partial pool created: {total_partial} fail uncors"
        )
        return True

    def Rebuild_Partial_Pool(self) -> bool:
        """optimal LLR 갱신 후 Full uncor을 재decoding하여 Partial pool을 동적 재구성한다.

        흐름:
        1. Full uncor을 optimal matrix로 LOAD_UNCOR_SEED_SAVE_UNCOR_SEED 테스트
        2. 각 프로세스의 redecoded uncor(= fail codeword)를 Gather
        3. Gather된 fail uncor를 tmp_partial_uncors에 저장 + Partial pool로 분배
        4. pool 상태 변수 갱신 및 MPI 동기화
        5. Partial FER = 1.0 설정

        Returns:
            bool: True면 Partial pool 재구성 성공, False면 Partial=0 (종료 필요)
        """
        self.Write_Log_Lines("[Rebuild_Partial_Pool] Starting dynamic partial reconstruction")

        # ─── Step 1: Seed mode 설정 (전 rank 동기화) ───
        prev_seed_mode = self.current_seed_mode
        if self.is_root:
            self.current_seed_mode = SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED
        self.current_seed_mode = self._safe_bcast(
            self.current_seed_mode if self.is_root else None,
            "Bcast_rebuild_seed_mode"
        )

        # ─── Step 2: Full uncor를 working directory에 로드 ───
        prev_test_mode = self.current_test_mode
        self.current_test_mode = TestMode.FULL
        self.Load_Uncors_From_Pool(TestMode.FULL)

        # ─── Step 3: optimal matrix로 Test_LLR (LOAD_UNCOR_SEED_SAVE_UNCOR_SEED) ───
        self.Test_LLR(self.optimal_LLR_matrix)

        # ─── Step 4: Gather redecoded uncors (fail codeword) → Partial pool 재구성 ───
        is_uncor_type_seed = (UNCOR_CONFIG.LOAD_UNCOR_MODE != DAOLoadUncorMode.LOAD_VECTOR)
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            src_path = self.Gather_And_Archive_Uncors(
                matrix=self.optimal_LLR_matrix,
                ch_idx=ch_idx,
                is_uncor_type_seed=is_uncor_type_seed,
                is_redecoded_uncor=True,
                test_mode=TestMode.FULL
            )

            # tmp_partial_uncors에 저장 (Periodic Recheck 재분배 시 소스로 사용)
            if self.is_root and src_path and src_path.exists():
                tmp_partial_dir = self._Get_Tmp_Partial_Uncor_Dir(matrix=self.optimal_LLR_matrix)
                tmp_partial_dir.mkdir(parents=True, exist_ok=True)
                dest_file_name = self.Get_Uncor_File_Name(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)
                tmp_dest = tmp_partial_dir / dest_file_name
                shutil.copy2(src_path, tmp_dest)

            # Partial pool로 분배
            self._Setup_Uncor_Pool_For_Channel(
                ch_idx=ch_idx,
                is_uncor_type_seed=is_uncor_type_seed,
                test_mode=TestMode.PARTIAL,
                src_path=src_path
            )

        # ─── Step 5: 총 Partial uncor 수 확인 ───
        self.MPI_Barrier()
        self.total_num_uncors = self._safe_bcast(
            self.total_num_uncors if self.is_root else None,
            "Bcast_total_num_uncors_rebuild"
        )
        # Partial 수를 별도 변수에 저장
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            self.total_num_partial_uncors[ch_idx] = self.total_num_uncors[ch_idx]

        total_partial_count = 0
        if self.is_root:
            total_partial_count = sum(self.total_num_partial_uncors)
        total_partial_count = self._safe_bcast(
            total_partial_count if self.is_root else None,
            "Bcast_total_partial_count"
        )

        if total_partial_count == 0:
            self.Write_Log_Lines("[Rebuild_Partial_Pool] Partial count = 0. All uncors decoded successfully.")
            self._Restore_State_After_Partial_Rebuild(prev_test_mode, prev_seed_mode)
            return False

        self.Write_Log_Lines(
            f"[Rebuild_Partial_Pool] Partial pool reconstructed: {total_partial_count} fail uncors"
        )

        # ─── Step 6: Partial FER = 1.0 설정 ───
        if self.is_root:
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                self.optimal_LLR_matrix.FERs_partial[ch_idx] = 1.0
        self.optimal_LLR_matrix = self._safe_bcast(
            self.optimal_LLR_matrix if self.is_root else None,
            "Bcast_optimal_after_rebuild"
        )

        # ─── Step 7: 상태 복원 ───
        self._Restore_State_After_Partial_Rebuild(prev_test_mode, prev_seed_mode)

        return True

    def _Restore_State_After_Partial_Rebuild(self, prev_test_mode, prev_seed_mode) -> None:
        """Rebuild_Partial_Pool이 바꾼 테스트 모드, 적재 상태, seed 모드를 진입 시점 값으로 되돌린다. (전 rank 동기화)"""
        self.current_test_mode = prev_test_mode
        self.current_loaded_test_mode = None  # 다음 Ensure_Uncors_Loaded에서 재로드 강제
        if self.is_root:
            self.current_seed_mode = prev_seed_mode
        self.current_seed_mode = self._safe_bcast(
            self.current_seed_mode if self.is_root else None,
            "Bcast_restore_seed_mode"
        )

    def _Signal_Graceful_Stop_No_Partial(self):
        """Partial uncor가 0개일 때 graceful stop을 시그널한다.

        기존 DAO_END_FLAG 메커니즘을 활용하여 optimization loop에서
        자연스럽게 탈출하도록 한다.

        모든 rank에서 호출되어야 한다 (flag 파일은 root만 기록).
        """
        self.Write_Log_Lines(
            "=" * 70 + "\n"
            "[GRACEFUL STOP] All Full uncors decoded successfully.\n"
            "[GRACEFUL STOP] No remaining fail codewords → Partial pool empty.\n"
            "[GRACEFUL STOP] Optimization target achieved. Terminating.\n"
            + "=" * 70
        )

        # root만 DAO end flag 기록
        if self.is_root:
            self._Write_End_Flag(PATH_CONFIG.DAO_END_FLAG_FILE_PATH, True)

        self.MPI_Barrier()

    def Test_Trial_LLR(self) -> bool:
        """현재 trial LLR 매트릭스를 테스트한다.

        ENABLE_TWO_STAGE_TEST에 따라 동작이 달라진다:
        - False (기존 모드): Full 테스트만 수행
        - True (Two-stage 모드): Partial → (개선 시) Full 순차 테스트

        예외:
        - REORDER_GROUP, ADJUST_ITERATION 모드: 항상 Full 테스트만 수행
        - Multi-round final verification(is_active=False): Full 강제

        Returns:
            bool: Full 테스트가 완료되었으면 True, Partial에서 개선 없어 Full 스킵하면 False
                    ENABLE_TWO_STAGE_TEST=False일 때는 항상 True (기존 동작 유지)
        """
        # REORDER_GROUP, ADJUST_ITERATION: Full 테스트만 수행 (Partial 결과가 Full과 괴리 가능)
        # DELETE_ROW, INSERT_RESTART_GROUP: Partial 필터링 허용 (행 추가/삭제는 Partial로 선별 가능)
        #   단, final verification(is_active=False)에서는 Full 강제 (temp_optimal→optimal 승격 판정 보장)
        is_multi_round_final = False
        if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
            state_attr = MULTI_ROUND_MODES[self.current_gen_trial_LLR_mode]
            state = getattr(self, state_attr)
            is_multi_round_final = not state.is_active

        if self.current_gen_trial_LLR_mode in MULTI_ROUND_FULL_ONLY_MODES or is_multi_round_final or not UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
            should_test_partial = False
        else:
            should_test_partial = True

        if should_test_partial:
            # ===== 1단계: Partial 테스트 =====
            self.Write_Log_Lines(f"\n[Partial Test Start] Testing trial LLR with partial uncors")
            self._Run_Test_Stage(TestMode.PARTIAL, self.current_LLR_matrix, enable_early_channel_exit=True)

            # Partial 결과 로그 출력
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                ch_param = self.Get_Channel_Param_String(ch_idx)
                self.Write_Log_Lines(f"[Partial Test Result] ch{ch_idx}({ch_param}) FER: {self.current_LLR_matrix.FERs_partial[ch_idx]:.2e}, Avg_Iter: {self.current_LLR_matrix.avg_iterations_partial[ch_idx]:.1f}")

            # ===== Partial 개선 확인 =====
            should_proceed, is_actually_improved, is_last_trial = self.Check_Partial_Improvement()

            if not should_proceed:
                # Partial에서 개선 없음 → Full 테스트 스킵
                self.Write_Log_Lines(f"[Partial Test] No improvement detected. Skipping full test to save time.")
                self._Cleanup_LLR_Matrix_Files()
                return False  # should_check_update = False
            else:
                # Full 테스트 진행 (개선됨 또는 마지막 trial)
                if is_last_trial and not is_actually_improved:
                    self.Write_Log_Lines(f"\n[Full Test Start] Last trial - proceeding to full test (partial not improved)")
                else:
                    self.Write_Log_Lines(f"\n[Full Test Start] Partial improved! Testing with full uncors")

        # ===== 2단계: Full 테스트 =====
        self._Run_Test_Stage(TestMode.FULL, self.current_LLR_matrix, enable_early_channel_exit=True)

        # Full 결과 로그 출력
        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
            ch_param = self.Get_Channel_Param_String(ch_idx)
            self.Write_Log_Lines(f"[Full Test Result] ch{ch_idx}({ch_param}) FER: {self.current_LLR_matrix.FERs[ch_idx]:.2e}, Avg_Iter: {self.current_LLR_matrix.avg_iterations[ch_idx]:.1f}")

        self._Cleanup_LLR_Matrix_Files()
        return True  # should_check_update = True (Full 테스트 완료)

    def Update_Current_LLR(self, matrix):
        self.current_LLR_matrix_idx = matrix.matrix_idx
        self.current_LLR_matrix = matrix.Deep_Copy(self.current_LLR_matrix_idx, copy_raw_FER=True, copy_seed_FER=True)

    def Update_Optimal_LLR(self, is_initial: bool = False, is_forced_last_trial: bool = False) -> None:
        """최적 LLR 매트릭스를 갱신한다.

        업데이트 조건을 평가해 최적 또는 임시 최적 매트릭스를 저장하고 로그에 변경 사항을 기록한다.

        Args:
            is_initial (bool): 초기 단계 업데이트 여부.
            is_forced_last_trial (bool): 시간 제한으로 인해 강제로 마지막 trial로 간주할지 여부.

        Returns:
            None

        Raises:
            ValueError: 지원되지 않는 업데이트 모드가 선택된 경우.
        """

        self.update_mode = None
        now_optimal_LLR_update = None
        self.is_previous_trial_updated = False
        if self.is_root:
            now_optimal_LLR_update, self.update_mode = self.Determine_Update_Decision(is_initial, is_forced_last_trial)
            self.is_previous_trial_updated = now_optimal_LLR_update
            if now_optimal_LLR_update:
                self.Set_Optimal_Matrix()

                # target_group_indices 정리: 현재 optimal 매트릭스의 그룹 수를 초과하는 인덱스 제거
                num_groups = len(self.optimal_LLR_matrix.groups)
                self.target_group_indices = [
                    idx for idx in self.target_group_indices
                    if idx < num_groups
                ]
                if not self.target_group_indices:
                    # 모두 제거된 경우 설정에서 다시 만든다
                    self.target_group_indices = self.Build_Target_Group_Indices(self.optimal_LLR_matrix)

                self.log_has_update = True
                if self.update_mode in (UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT, UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL):
                    self.Save_LLR_Matrix(self.optimal_LLR_matrix, target_dir=self.optimal_output_dir)
                    self.Write_Log_Lines(f"[Update optimal LLR matrix!]")
                elif self.update_mode == UpdateMode.TEMP_OPTIMAL_MATRIX_FROM_CURRENT:
                    self.Save_LLR_Matrix(self.temp_optimal_LLR_matrix, target_dir=self.optimal_output_dir)
                    self.Write_Log_Lines(f"[Update temporal optimal LLR matrix!]")
                else:
                    error_msg = f"Update_Optimal_LLR_Matrix: Unexpected update mode. update_mode: {self.update_mode!r}"
                    self.MPI_Abort(error_msg)

        self.update_mode = self._safe_bcast(self.update_mode if self.is_root else None, "Bcast_update_mode")
        self.optimal_LLR_matrix = self._safe_bcast(self.optimal_LLR_matrix if self.is_root else None, "Bcast_optimal_LLR_matrix")
        self.temp_optimal_LLR_matrix = self._safe_bcast(self.temp_optimal_LLR_matrix if self.is_root else None, "Bcast_temp_optimal_LLR_matrix")
        self.is_previous_trial_updated = self._safe_bcast(self.is_previous_trial_updated if self.is_root else None, "Bcast_is_previous_trial_updated")

        # Dynamic Partial Reconstruction: optimal 갱신 시에만 실행.
        # 초기 매트릭스의 Partial 풀은 Test_Initial_LLR이 이미 만들었으므로 is_initial이면 건너뛴다
        if (UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST
                and not is_initial
                and self.update_mode in (UpdateMode.OPTIMAL_MATRIX_FROM_CURRENT,
                                          UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL)):
            has_partial = self.Rebuild_Partial_Pool()
            if not has_partial:
                self._Signal_Graceful_Stop_No_Partial()

    def _Promote_Temp_Optimal_On_Stage_Exit(self):
        """Trial 루프 종료 후 temp_optimal → optimal 안전망.

        gen_success=False로 마지막 trial이 스킵되어 Update_Optimal_LLR이
        is_forced_last_trial=True로 호출되지 못한 경우를 처리한다.
        current_LLR_matrix는 유효하지 않을 수 있으므로 참조하지 않는다.
        """
        promoted = False
        if self.is_root:
            if (self.is_update_at_last_trial
                    and self.temp_optimal_LLR_matrix is not None
                    and self.Is_Matrix_Better(self.temp_optimal_LLR_matrix, self.optimal_LLR_matrix)):
                # temp_optimal → optimal 승격
                self.previous_optimal_LLR_matrix = self.temp_optimal_LLR_matrix.Deep_Copy(
                    copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
                self.optimal_LLR_matrix = self.temp_optimal_LLR_matrix.Deep_Copy(
                    copy_raw_FER=True, copy_seed_FER=True, copy_partial_FER=True)
                self.update_mode = UpdateMode.OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL
                self.Save_LLR_Matrix(self.optimal_LLR_matrix, target_dir=self.optimal_output_dir)
                self.log_has_update = True
                self.Write_Log_Lines("[temp_optimal → optimal 승격 (stage exit 안전망)]")
                promoted = True

        # MPI 동기화
        promoted = self._safe_bcast(promoted if self.is_root else None, "Bcast_stage_exit_promoted")
        if promoted:
            self.optimal_LLR_matrix = self._safe_bcast(
                self.optimal_LLR_matrix if self.is_root else None, "Bcast_optimal_after_promotion")
            self.temp_optimal_LLR_matrix = self._safe_bcast(
                self.temp_optimal_LLR_matrix if self.is_root else None, "Bcast_temp_optimal_after_promotion")

            # Dynamic Partial Reconstruction: promoted 후 Partial pool 재구성
            if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
                has_partial = self.Rebuild_Partial_Pool()
                if not has_partial:
                    self._Signal_Graceful_Stop_No_Partial()

    def Validate_Config(self):
        errors: list[str] = []

        # 모드 시퀀스의 값이 GenLLRMode에 있는지 (없는 값은 stage 1의 GenLLRMode(값)에서 ValueError로 전체가 중단된다)
        valid_mode_values = {int(mode) for mode in GenLLRMode}
        for seq_name in ("Gen_LLR_Mode_SEQUENCE", "Gen_LLR_Mode_HBF_SEQUENCE"):
            for mode_value in getattr(DAO_CONFIG, seq_name):
                if int(mode_value) not in valid_mode_values:
                    errors.append(f"{seq_name} contains {mode_value}, which is not a GenLLRMode value {sorted(valid_mode_values)}.")

        if INSERT_RANDOM_GROUP_CONFIG.INSERT_GROUP_NUM_ROWS <= 0:
            errors.append("InsertGroupConfig.NUM_ROWS must be greater than 0.")

        if MAX_CSW <= MIN_CSW:
            errors.append(f"MAX_CSW ({MAX_CSW}) must be greater than MIN_CSW ({MIN_CSW}).")

        if STEP_CSW <= 0:
            errors.append(f"STEP_CSW must be positive (current: {STEP_CSW}).")

        if (MAX_CSW - MIN_CSW) % STEP_CSW != 0:
            errors.append(
                f"(MAX_CSW - MIN_CSW) must be divisible by STEP_CSW "
                f"(values: MAX_CSW={MAX_CSW}, MIN_CSW={MIN_CSW}, STEP_CSW={STEP_CSW})."
            )

        max_insertable_rows = ((MAX_CSW - MIN_CSW) // STEP_CSW) + 1
        if INSERT_RANDOM_GROUP_CONFIG.INSERT_GROUP_NUM_ROWS - 1 > max_insertable_rows:
            errors.append(
                f"InsertGroupConfig.NUM_ROWS={INSERT_RANDOM_GROUP_CONFIG.INSERT_GROUP_NUM_ROWS} is too large. "
                f"At most {max_insertable_rows + 1} rows (including the -1 entry) "
                "can fit within the CSW range."
            )

        matrix_idx_list = DAO_CONFIG.Get_Initial_Matrix_Idx_List()
        for idx in matrix_idx_list:
            if idx < 0:
                source = "INITIAL_MATRIX_IDX_LIST" if DAO_CONFIG.INITIAL_MATRIX_IDX_LIST is not None else "INITIAL_MATRIX_IDX"
                errors.append(f"{source} contains negative value: {idx}.")
        if DAO_CONFIG.INITIAL_MATRIX_IDX_LIST is not None:
            if len(DAO_CONFIG.INITIAL_MATRIX_IDX_LIST) == 0:
                errors.append("INITIAL_MATRIX_IDX_LIST must not be empty.")
            if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.RUN_OPTIMIZATION:
                errors.append("INITIAL_MATRIX_IDX_LIST is only supported in TEST_FER/SAVE_UNCOR/REDECODE modes.")
            if len(DAO_CONFIG.INITIAL_MATRIX_IDX_LIST) != len(set(DAO_CONFIG.INITIAL_MATRIX_IDX_LIST)):
                duplicates = [idx for idx in set(DAO_CONFIG.INITIAL_MATRIX_IDX_LIST) if DAO_CONFIG.INITIAL_MATRIX_IDX_LIST.count(idx) > 1]
                self.Write_Log_Lines(f"[WARN] INITIAL_MATRIX_IDX_LIST에 중복 인덱스가 있습니다: {duplicates}")

        if REFC_CONFIG.max_num_test <= 0:
            errors.append(f"max_num_test must be positive (current: {REFC_CONFIG.max_num_test}).")

        # REGEN_DV_Config 검증
        if REGEN_DV_CONFIG.ENABLE_FIX_IDX:
            if self.initial_LLR_matrix is None:
                errors.append("REGEN_DV_Config.ENABLE_FIX_IDX is True, but initial_LLR_matrix is not loaded yet.")
            else:
                num_dv = self.initial_LLR_matrix.header.num_dv

                # INITIAL_TARGET_GROUP_IDX 검증
                if DAO_CONFIG.INITIAL_TARGET_GROUP_IDX < 0:
                    errors.append(f"INITIAL_TARGET_GROUP_IDX must be non-negative (current: {DAO_CONFIG.INITIAL_TARGET_GROUP_IDX}).")
                elif DAO_CONFIG.INITIAL_TARGET_GROUP_IDX >= len(self.initial_LLR_matrix.groups):
                    errors.append(f"INITIAL_TARGET_GROUP_IDX is out of range. Must be in [0, {len(self.initial_LLR_matrix.groups) - 1}] (current: {DAO_CONFIG.INITIAL_TARGET_GROUP_IDX}).")

                if not self.target_group_indices:
                    errors.append("REGEN_DV_Config.ENABLE_FIX_IDX is True, but no valid target groups found.")
                else:
                    # 각 타겟 그룹에 대해 검증
                    for tg_idx in set(self.target_group_indices):  # 중복 제거
                        if tg_idx < 0 or tg_idx >= len(self.initial_LLR_matrix.groups):
                            errors.append(f"target_group_indices contains {tg_idx} which is out of range. Must be in [0, {len(self.initial_LLR_matrix.groups) - 1}].")
                            continue

                        target_group = self.initial_LLR_matrix.groups[tg_idx]
                        num_rows_in_target_group = len(target_group)

                        if num_rows_in_target_group == 0:
                            errors.append(f"REGEN_DV_Config: Target group {tg_idx} is empty.")
                            continue

                        # FIXED_ROW_IDX 검증
                        row_values_to_check = []
                        if isinstance(REGEN_DV_CONFIG.FIXED_ROW_IDX, list):
                            row_values_to_check = REGEN_DV_CONFIG.FIXED_ROW_IDX
                        elif REGEN_DV_CONFIG.FIXED_ROW_IDX != -1:
                            row_values_to_check = [REGEN_DV_CONFIG.FIXED_ROW_IDX]

                        for row_val in row_values_to_check:
                            if row_val < 0 or row_val >= num_rows_in_target_group:
                                errors.append(
                                    f"REGEN_DV_Config.FIXED_ROW_IDX contains {row_val} which is out of range for target group {tg_idx}. "
                                    f"Must be in [0, {num_rows_in_target_group - 1}] (target group {tg_idx} has {num_rows_in_target_group} rows)."
                                )

                # FIXED_DV_IDX 검증 (모든 그룹 공통)
                dv_values_to_check = []
                if isinstance(REGEN_DV_CONFIG.FIXED_DV_IDX, list):
                    dv_values_to_check = REGEN_DV_CONFIG.FIXED_DV_IDX
                elif REGEN_DV_CONFIG.FIXED_DV_IDX != -1:
                    dv_values_to_check = [REGEN_DV_CONFIG.FIXED_DV_IDX]

                for dv_val in dv_values_to_check:
                    if dv_val < 0 or dv_val >= num_dv:
                        errors.append(
                            f"REGEN_DV_Config.FIXED_DV_IDX contains {dv_val} which is out of range. "
                            f"Must be in [0, {num_dv - 1}] (num_dv={num_dv})."
                        )

        # REGEN_ROW_Config 검증
        if REGEN_ROW_CONFIG.ENABLE_FIX_IDX:
            if self.initial_LLR_matrix is None:
                errors.append("REGEN_ROW_Config.ENABLE_FIX_IDX is True, but initial_LLR_matrix is not loaded yet.")
            else:
                # INITIAL_TARGET_GROUP_IDX 검증
                if DAO_CONFIG.INITIAL_TARGET_GROUP_IDX < 0:
                    errors.append(f"INITIAL_TARGET_GROUP_IDX must be non-negative (current: {DAO_CONFIG.INITIAL_TARGET_GROUP_IDX}).")
                elif DAO_CONFIG.INITIAL_TARGET_GROUP_IDX >= len(self.initial_LLR_matrix.groups):
                    errors.append(f"INITIAL_TARGET_GROUP_IDX is out of range for REGEN_ROW. Must be in [0, {len(self.initial_LLR_matrix.groups) - 1}] (current: {DAO_CONFIG.INITIAL_TARGET_GROUP_IDX}).")

                if not self.target_group_indices:
                    errors.append("REGEN_ROW_Config.ENABLE_FIX_IDX is True, but no valid target groups found.")
                else:
                    # 각 타겟 그룹에 대해 검증
                    for tg_idx in set(self.target_group_indices):  # 중복 제거
                        if tg_idx < 0 or tg_idx >= len(self.initial_LLR_matrix.groups):
                            errors.append(f"target_group_indices contains {tg_idx} which is out of range for REGEN_ROW. Must be in [0, {len(self.initial_LLR_matrix.groups) - 1}].")
                            continue

                        target_group = self.initial_LLR_matrix.groups[tg_idx]
                        num_rows_in_target_group = len(target_group)

                        if num_rows_in_target_group == 0:
                            errors.append(f"REGEN_ROW_Config: Target group {tg_idx} is empty.")
                            continue

                        # FIXED_ROW_IDX 검증
                        row_values_to_check = []
                        if isinstance(REGEN_ROW_CONFIG.FIXED_ROW_IDX, list):
                            row_values_to_check = REGEN_ROW_CONFIG.FIXED_ROW_IDX
                        elif REGEN_ROW_CONFIG.FIXED_ROW_IDX != -1:
                            row_values_to_check = [REGEN_ROW_CONFIG.FIXED_ROW_IDX]

                        for row_val in row_values_to_check:
                            if row_val < 0 or row_val >= num_rows_in_target_group:
                                errors.append(
                                    f"REGEN_ROW_Config.FIXED_ROW_IDX contains {row_val} which is out of range for target group {tg_idx}. "
                                    f"Must be in [0, {num_rows_in_target_group - 1}] (target group {tg_idx} has {num_rows_in_target_group} rows)."
                                )

        # REDECODE 모드는 Two-Stage 모드와 함께 사용할 수 없음
        if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.REDECODE:
            if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
                errors.append(
                    "REDECODE 모드는 Two-Stage 모드와 함께 사용할 수 없습니다. "
                    "UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST를 False로 설정하세요."
                )

        # Two-Stage 모드 조합 검증
        if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
            if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_NONE:
                errors.append(
                    "Two-Stage 모드는 LOAD_UNCOR_MODE=LOAD_NONE과 함께 사용할 수 없습니다. "
                    "LOAD_SEED 또는 LOAD_VECTOR를 설정하세요."
                )
            if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:
                errors.append(
                    "Two-Stage 모드는 현재 LOAD_UNCOR_MODE=LOAD_VECTOR를 지원하지 않습니다. "
                    "LOAD_SEED를 사용하세요."
                )
            if DAO_CONFIG.IS_HBF_OPT:
                errors.append(
                    "Two-Stage 모드는 IS_HBF_OPT=True와 함께 사용할 수 없습니다."
                )

        # GEN_SINGLE_ROW 모드는 LOAD_VECTOR와 함께 사용할 수 없음
        if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.GEN_SINGLE_ROW:
            if UNCOR_CONFIG.ENABLE_LOAD_VECTOR:
                errors.append(
                    "GEN_SINGLE_ROW 모드는 ENABLE_LOAD_VECTOR=True와 함께 사용할 수 없습니다. "
                    "UNCOR_CONFIG.ENABLE_LOAD_VECTOR를 False로 설정하세요."
                )
            if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST:
                errors.append(
                    "GEN_SINGLE_ROW 모드는 ENABLE_TWO_STAGE_TEST=True와 함께 사용할 수 없습니다. "
                    "UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST를 False로 설정하세요."
                )

        if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.RUN_OPTIMIZATION:
            if DAO_CONFIG.MAX_OPTIMIZATION_TRIALS <= 0:
                errors.append(f"MAX_OPTIMIZATION_TRIALS must be > 0 (current: {DAO_CONFIG.MAX_OPTIMIZATION_TRIALS})")
            # 모드별 MAX_TRIAL 검증: -1 또는 양의 정수만 허용
            for config_name, config_cls in [
                ("GEN_INITIAL_GROUP_CONFIG", GEN_INITIAL_GROUP_CONFIG),
                ("MUTATE_CONFIG", MUTATE_CONFIG),
                ("INSERT_RANDOM_GROUP_CONFIG", INSERT_RANDOM_GROUP_CONFIG),
                ("INSERT_RANDOM_ROW_CONFIG", INSERT_RANDOM_ROW_CONFIG),
                ("INSERT_MUTATED_GROUP_CONFIG", INSERT_MUTATED_GROUP_CONFIG),
                ("INSERT_MUTATED_ROW_CONFIG", INSERT_MUTATED_ROW_CONFIG),
                ("REGEN_DV_CONFIG", REGEN_DV_CONFIG),
                ("REGEN_ROW_CONFIG", REGEN_ROW_CONFIG),
                ("SPLIT_GROUP_CONFIG", SPLIT_GROUP_CONFIG),
            ]:
                if config_cls.MAX_TRIAL != -1 and config_cls.MAX_TRIAL <= 0:
                    errors.append(f"{config_name}.MAX_TRIAL must be -1 or > 0 (current: {config_cls.MAX_TRIAL})")
            if DAO_CONFIG.MAX_GEN_RETRY_PER_TRIAL <= 0:
                errors.append(f"MAX_GEN_RETRY_PER_TRIAL must be > 0 (current: {DAO_CONFIG.MAX_GEN_RETRY_PER_TRIAL})")
            if self.initial_LLR_matrix is not None:
                num_groups = len(self.initial_LLR_matrix.groups)
                if DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST is not None:
                    errors.extend(self.Check_Fixed_Target_Group_Idx_List(self.initial_LLR_matrix))
                elif DAO_CONFIG.INITIAL_TARGET_GROUP_IDX >= num_groups:
                    errors.append(
                        f"INITIAL_TARGET_GROUP_IDX({DAO_CONFIG.INITIAL_TARGET_GROUP_IDX}) >= "
                        f"num_groups({num_groups}). target_group_indices will be empty.")

        if SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS < 0:
            errors.append(f"SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS must be >= 0 (current: {SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS})")

        if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.GEN_SINGLE_ROW:
            if SINGLE_ROW_CONFIG.NUM_GEN_TRIALS <= 0:
                errors.append(f"SINGLE_ROW_CONFIG.NUM_GEN_TRIALS must be > 0 (current: {SINGLE_ROW_CONFIG.NUM_GEN_TRIALS})")
            if SINGLE_ROW_CONFIG.CANDIDATE_ITERATION <= 0:
                errors.append(f"SINGLE_ROW_CONFIG.CANDIDATE_ITERATION must be > 0 (current: {SINGLE_ROW_CONFIG.CANDIDATE_ITERATION})")
            if SINGLE_ROW_CONFIG.SPEED_TEST_RECHECK_INTERVAL_SECONDS < 0:
                errors.append(f"SINGLE_ROW_CONFIG.SPEED_TEST_RECHECK_INTERVAL_SECONDS must be >= 0 (current: {SINGLE_ROW_CONFIG.SPEED_TEST_RECHECK_INTERVAL_SECONDS})")

        if COPY_ROWS_CONFIG.ENABLE_EXTERNAL_SINGLE_ROW:
            if not COPY_ROWS_CONFIG.EXTERNAL_SINGLE_ROW_DIRS:
                errors.append("ENABLE_EXTERNAL_SINGLE_ROW=True이지만 EXTERNAL_SINGLE_ROW_DIRS가 비어 있습니다.")
            else:
                base_dir = PATH_CONFIG.INPUT_SINGLE_ROW_LLR_MATRIX_DIR_PATH
                for dir_name in COPY_ROWS_CONFIG.EXTERNAL_SINGLE_ROW_DIRS:
                    dir_path = os.path.join(base_dir, dir_name)
                    if not os.path.isdir(dir_path):
                        errors.append(f"외부 후보 디렉토리가 존재하지 않습니다: {dir_path}")
            if COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES <= 0:
                errors.append(f"MAX_EXTERNAL_CANDIDATES must be > 0 (current: {COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES})")

        if errors:
            joined = "\n".join(f"- {msg}" for msg in errors)
            self.MPI_Abort(f"[Validate_Config] Invalid configuration detected:\n{joined}")
        else:
            self.Write_Log_Lines(f"[Config validation] No error.")

        if (REFC_CONFIG.ch_type == 1):
            if (len(REFC_CONFIG.RBERs) != REFC_CONFIG.NUM_TARGET_CHANNELS):
                error_msg = f"Validate_Config: RBERs length mismatch. len(RBERs): {len(REFC_CONFIG.RBERs)}, NUM_TARGET_CHANNELS: {REFC_CONFIG.NUM_TARGET_CHANNELS}"
                self.MPI_Abort(error_msg)
        elif (REFC_CONFIG.ch_type == 2):
            if (len(REFC_CONFIG.num_fixed_errs) != REFC_CONFIG.NUM_TARGET_CHANNELS):
                error_msg = f"Validate_Config: num_fixed_errs length mismatch. len(num_fixed_errs): {len(REFC_CONFIG.num_fixed_errs)}, NUM_TARGET_CHANNELS: {REFC_CONFIG.NUM_TARGET_CHANNELS}"
                self.MPI_Abort(error_msg)
        elif (REFC_CONFIG.ch_type == 3):
            if (len(REFC_CONFIG.num_fixed_errs) != REFC_CONFIG.NUM_TARGET_CHANNELS):
                error_msg = f"Validate_Config: num_fixed_errs length mismatch. len(num_fixed_errs): {len(REFC_CONFIG.num_fixed_errs)}, NUM_TARGET_CHANNELS: {REFC_CONFIG.NUM_TARGET_CHANNELS}"
                self.MPI_Abort(error_msg)
            elif (len(REFC_CONFIG.fixed_SCRs) != REFC_CONFIG.NUM_TARGET_CHANNELS):
                error_msg = f"Validate_Config: fixed_SCRs length mismatch. len(fixed_SCRs): {len(REFC_CONFIG.fixed_SCRs)}, NUM_TARGET_CHANNELS: {REFC_CONFIG.NUM_TARGET_CHANNELS}"
                self.MPI_Abort(error_msg)
            elif(len(REFC_CONFIG.fixed_SERs) != REFC_CONFIG.NUM_TARGET_CHANNELS):
                error_msg = f"Validate_Config: fixed_SERs length mismatch. len(fixed_SERs): {len(REFC_CONFIG.fixed_SERs)}, NUM_TARGET_CHANNELS: {REFC_CONFIG.NUM_TARGET_CHANNELS}"
                self.MPI_Abort(error_msg)
        else:
            self.MPI_Abort(f"Validate_Config: Unsupported ch_type={REFC_CONFIG.ch_type}. Valid: 1, 2, 3")

    def Validate_LLR_Matrix(self):
        # current_LLR_matrix가 LLR_MATRIX 객체인지 확인
        if not isinstance(self.current_LLR_matrix, LLR_MATRIX):
            error_msg = f"Validate_LLR_Matrix: current_LLR_matrix is not LLR_MATRIX type. Got: {type(self.current_LLR_matrix)}"
            self.Write_Log_Lines(error_msg)
            self.is_current_LLR_valid = False
            return

        self.is_current_LLR_valid, validate_msg = self.current_LLR_matrix.Is_LLR_Valid()
        if not self.is_current_LLR_valid:
            self.Write_Log_Lines(validate_msg)
            self.Save_LLR_Matrix(self.current_LLR_matrix, target_dir=self.session_error_dir)

    def Write_Log_Separator(self, log_msg:str, separator):
        """로그 파일에 구분선을 출력한다.

        Args:
            log_msg (str): 구분선에 포함할 메시지.
            separator (str): 앞뒤에 배치할 구분선 문자열.

        Returns:
            None
        """
        self.Write_Log_Lines(f"\n{separator} [{log_msg} @ {self.Get_Timestamp()}] {separator}\n")

    def Write_Log_Lines(self, lines: Union[str, list[str]], write_update_log: bool = False):
        """로그 파일에 문자열을 기록한다.

        단일 문자열 또는 문자열 목록을 받아 루트 프로세스의 로그 파일에 추가한다.

        Args:
            lines (Union[str, list[str]]): 기록할 로그 메시지 또는 메시지 목록.
            write_update_log (bool): True일 경우 update 전용 로그 파일에도 기록. 기본값: False.

        Returns:
            None

        Raises:
            OSError: 파일 쓰기 과정에서 입출력 오류가 발생한 경우.
        """
        if not self.is_root or self.log_file_path is None:
            return

        if isinstance(lines, str):
            lines = [lines]

        self._append_lines_without_rotation(lines)

        # Update 전용 로그 파일에도 기록
        if write_update_log and DEBUG_CONFIG.ENABLE_UPDATE_LOG and self.update_log_file_path:
            try:
                with open(self.update_log_file_path, "a", encoding="utf-8") as update_log_file:
                    for line in lines:
                        update_log_file.write(f"{line}\n")
            except OSError as e:
                _write_error_log(self.rank, e)

        if self.log_line_count >= LOG_MAX_LINES:
            self.Make_Log_Backup()


    def _Reset_For_Next_Matrix(self):
        """다음 매트릭스 테스트를 위해 per-matrix 상태를 리셋한다.

        _init_per_matrix_state()로 30개 필드 초기화 후 MPI 동기화.
        """
        self._init_per_matrix_state()

        # MPI 동기화 (모든 프로세스가 리셋 완료 후 진행)
        self.MPI_Barrier()

    def _Run_Exit_After_Multi_Matrix(self):
        """TEST_FER/SAVE_UNCOR/REDECODE 모드에서 여러 초기 매트릭스를 순차 테스트한다.

        첫 번째 매트릭스는 Setup()에서 이미 로드된 상태.
        두 번째 이후는 상태 리셋 → 로드 → 테스트를 반복한다.

        Args:
            없음.

        Returns:
            None
        """
        matrix_idx_list = DAO_CONFIG.Get_Initial_Matrix_Idx_List()

        for loop_idx, matrix_idx in enumerate(matrix_idx_list):
            self.Write_Log_Separator(
                f"Multi-Matrix [{loop_idx + 1}/{len(matrix_idx_list)}]: LLR_MATRIX_{matrix_idx}",
                SEPARATOR_TYPE2
            )

            if loop_idx > 0:
                # 두 번째 이후: 상태 리셋 + 새 매트릭스 로드
                self._current_initial_matrix_idx = matrix_idx
                self._Reset_For_Next_Matrix()
                self.Initialize_LLR_Matrix()

            self.Run_Initial_Test()

    def Main(self):
        self.Setup()

        # 코어 속도 사전 테스트 (느린 코어 식별 및 제외)
        self.Test_Core_Speed()

        # Uncor 분배 (Core speed test 이후 → excluded_cores 반영)
        self.Setup_Uncors()

        if DAO_CONFIG.RUN_DAO_MODE == RunDAOMode.GEN_SINGLE_ROW:
            self.Run_Single_Row_Generation()
        elif DAO_CONFIG.RUN_DAO_MODE != RunDAOMode.RUN_OPTIMIZATION:
            # TEST_FER / SAVE_UNCOR / REDECODE 모드: multi-matrix 지원
            self._Run_Exit_After_Multi_Matrix()
        else:
            # 기존 최적화 경로
            self.Run_Initial_Test()
            self.Run_Optimization()

        self.Finalize_Log()
        # 모든 프로세스가 작업 완료 후 root가 디렉토리를 삭제하도록 동기화
        # (non-root가 아직 MPI finalize 중일 때 rmtree 실패 방지)
        self.MPI_Barrier()
        self.Cleanup_Session()
        self.MPI_Barrier()

    def Run_Single_Row_Generation(self):
        """단일 row 후보 매트릭스를 N개 생성, 테스트, ranking하는 GEN_SINGLE_ROW 모드.

        흐름:
        1. initial matrix 로드 + initial test
        2. N개 single-row 매트릭스 생성 → Test_LLR → CSW 파싱 → scoring
        3. FER/CSW threshold 기준 Top-K ranking → 파일 저장
        """
        # 1. 출력 디렉토리 생성 (Initial test/Rebalance 불필요 — Setup_Uncors에서 균일 분배 완료)
        self.single_row_candidates_dir = os.path.join(self.session_dir, SINGLE_ROW_CANDIDATES_DIR_NAME)
        if self.is_root:
            os.makedirs(self.single_row_candidates_dir, exist_ok=True)
        self.MPI_Barrier()

        # 2. 후보 결과 저장용 리스트 (root에서만 관리)
        # 각 항목: { 'idx': int, 'matrix': LLR_MATRIX, 'FERs': list, 'avg_iters': list,
        #            'csw_threshold_counts': {ch_idx: {threshold: count}} }
        candidates = []

        num_candidates = SINGLE_ROW_CONFIG.NUM_GEN_TRIALS
        self.Write_Log_Lines(f"[GEN_SINGLE_ROW] Starting: {num_candidates} candidates, "
                             f"TOP_K={SINGLE_ROW_CONFIG.TOP_K}, CSW_THRESHOLDS={SINGLE_ROW_CONFIG.CSW_THRESHOLDS}")

        self._gen_single_row_stop_idx = None

        gen_start_time = time.time()
        for candidate_idx in range(num_candidates):
            # N번마다 DAO end flag 체크 (MPI_Barrier로 전 rank 동기화 후 읽기)
            end_flag_interval = SINGLE_ROW_CONFIG.END_FLAG_CHECK_INTERVAL
            if end_flag_interval > 0 and candidate_idx % end_flag_interval == 0:
                self.MPI_Barrier()
                # root만 플래그 파일을 읽고 bcast로 전파한다 (rank마다 따로 읽으면 판정이 갈려 집단 통신이 어긋난다)
                if self.is_root:
                    is_dao_end = self._gen_single_row_stop_idx is None and self.Read_DAO_End_Flag()
                else:
                    is_dao_end = False
                is_dao_end = self._safe_bcast(is_dao_end if self.is_root else None, "Bcast_single_row_dao_end")
                if is_dao_end:
                    self._gen_single_row_stop_idx = candidate_idx + end_flag_interval
                    self._Write_Stop_Idx(self._gen_single_row_stop_idx)
                    self.Write_Log_Lines(
                        f"[GEN_SINGLE_ROW] DAO end flag detected, will stop at candidate {self._gen_single_row_stop_idx}")

                if self._gen_single_row_stop_idx is not None and candidate_idx >= self._gen_single_row_stop_idx:
                    self.Write_Log_Lines(
                        f"[GEN_SINGLE_ROW] Graceful stop at candidate {candidate_idx}")
                    break

            candidate_start_time = time.time()
            # 3. Root에서 single-row 매트릭스 생성
            if self.is_root:
                candidate_matrix = self.Build_Single_Row_Matrix(matrix_idx=candidate_idx)
            else:
                candidate_matrix = None
            candidate_matrix = self._safe_bcast(candidate_matrix, f"Bcast_single_row_{candidate_idx}")

            # 생성 실패 시 스킵
            if candidate_matrix is None:
                self.Write_Log_Lines(f"[GEN_SINGLE_ROW] [{candidate_idx + 1}/{num_candidates}] Candidate {candidate_idx} generation failed, skipping")
                continue

            # 4. 테스트 (LOAD_UNCOR 모드, CSW 로그 강제 활성화)
            self.current_test_mode = TestMode.FULL
            self.Ensure_Uncors_Loaded(TestMode.FULL)
            self._last_saved_local_matrix_idx = -1  # 강제 저장

            self.Set_Ref_C_Parameters(is_test_initial=False, is_test_optimal=False)
            # CSW 로그 강제 활성화 (Set_Ref_C_Parameters에서 비활성화되므로 이후 재설정)
            self.enable_print_CSW_log = 1

            csw_threshold_counts = {}
            total_uncors = {}
            for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                self.Set_Test_Environment(matrix=candidate_matrix, ch_idx=ch_idx)

                while not self.is_test_end:
                    self.Read_Run_ECC_End_Flag()
                    if self.is_test_end:
                        self._Write_Run_ECC_End_Ack()
                        break
                    self.Run_ECC(ch_idx=ch_idx)
                    self.Check_Test_End(ch_idx=ch_idx)

                self._Write_Run_ECC_End_Ack()

                self.Gather_Ref_C_Results(matrix=candidate_matrix, ch_idx=ch_idx, is_test_end=True)
                self._Report_Missing_Acks()

                # 5. CSW 파싱 (채널별, 다음 채널 ECC가 CSW 파일을 덮어쓰기 전에 파싱)
                if self.is_root:
                    min_csws = self.Parse_CSW_Min_Values(ch_idx)
                    total_uncors[ch_idx] = len(min_csws)
                    csw_threshold_counts[ch_idx] = {}
                    for threshold in SINGLE_ROW_CONFIG.CSW_THRESHOLDS:
                        csw_threshold_counts[ch_idx][threshold] = sum(1 for csw in min_csws if csw <= threshold)

                # CSW 로그 수집 + 삭제 (채널별)
                self.Gather_CSW_Logs(matrix=candidate_matrix, ch_idx=ch_idx)
                self.Delete_CSW_Logs()
                self.MPI_Barrier()

            self.Cleanup_Test_Environment()

            # 6. 이전 candidate matrix 파일 삭제 (프로세스별)
            matrix_file = os.path.join(self.local_session_dir, candidate_matrix.LLR_matrix_file_name)
            if os.path.exists(matrix_file):
                os.remove(matrix_file)

            # 7. 후보 기록 (root)
            if self.is_root:
                candidate_info = {
                    'idx': candidate_idx,
                    'matrix': candidate_matrix,
                    'FERs': list(candidate_matrix.FERs),
                    'avg_iters': list(candidate_matrix.avg_iterations),
                    'csw_threshold_counts': csw_threshold_counts,
                    'total_uncors': total_uncors,
                }
                candidates.append(candidate_info)

                # 진행 로그
                fer_str = ", ".join(f"{fer:.4e}" for fer in candidate_matrix.FERs)
                csw_parts = []
                for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
                    ch_total = total_uncors.get(ch_idx, 0)
                    ch_csw = ", ".join(
                        f"#uncor(csw≤{t})={csw_threshold_counts.get(ch_idx, {}).get(t, 0)}/{ch_total}"
                        for t in SINGLE_ROW_CONFIG.CSW_THRESHOLDS
                    )
                    csw_parts.append(f"ch{ch_idx}:[{ch_csw}]")
                csw_str = " ".join(csw_parts)
                candidate_elapsed = time.time() - candidate_start_time
                total_elapsed = time.time() - gen_start_time
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.Write_Log_Lines(
                    f"[GEN_SINGLE_ROW] [{candidate_idx + 1}/{num_candidates}] [{now_str}] Candidate {candidate_idx}: "
                    f"FER=[{fer_str}], {csw_str} "
                    f"({candidate_elapsed:.1f}s, total: {_format_elapsed(total_elapsed)})")

                # 중간 ranking 갱신 (RANKING_UPDATE_INTERVAL마다)
                if (SINGLE_ROW_CONFIG.RANKING_UPDATE_INTERVAL > 0
                        and (candidate_idx + 1) % SINGLE_ROW_CONFIG.RANKING_UPDATE_INTERVAL == 0):
                    self.Write_Log_Lines(f"[GEN_SINGLE_ROW] [{candidate_idx + 1}/{num_candidates}] Intermediate ranking update")
                    self.Rank_And_Save_Single_Row_Candidates(candidates)

            # 시간 기반 주기적 Speed Test + Uncor 재분배 (root 판단 + bcast 동기화)
            if (SINGLE_ROW_CONFIG.ENABLE_PERIODIC_SPEED_TEST
                    and SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST
                    and SINGLE_ROW_CONFIG.SPEED_TEST_RECHECK_INTERVAL_SECONDS > 0):
                if self.is_root:
                    should_recheck_speed = (time.time() - self._last_speed_test_time) >= SINGLE_ROW_CONFIG.SPEED_TEST_RECHECK_INTERVAL_SECONDS
                else:
                    should_recheck_speed = False
                should_recheck_speed = self._safe_bcast(should_recheck_speed if self.is_root else None, "Bcast_should_recheck_speed_single_row")
                if should_recheck_speed:
                    self.Write_Log_Lines(f"[GEN_SINGLE_ROW] [{candidate_idx + 1}/{num_candidates}] Periodic speed test ({SINGLE_ROW_CONFIG.SPEED_TEST_RECHECK_INTERVAL_SECONDS}초 경과)  {self.Get_Mode_Sequence_Str()}")
                    excluded_changed = self._Recheck_Speed_Test()
                    if excluded_changed:
                        self._Redistribute_Uncor_Pool_Uniform()
                    else:
                        self.Write_Log_Lines(f"[GEN_SINGLE_ROW] excluded_cores 변경 없음, 균일 재분배 스킵")

        # 8. 최종 Ranking + 저장
        if self.is_root:
            self.Rank_And_Save_Single_Row_Candidates(candidates)

            # 9. 채널별 workspace를 Input 경로로 복사 (COPY_ROWS 외부 후보용)
            self._Export_Workspace_To_Input(candidates)

        self.MPI_Barrier()

    def Build_Single_Row_Matrix(self, matrix_idx: int) -> LLR_MATRIX:
        """Initial matrix 헤더 기반으로 1-group, 1-row 매트릭스를 생성한다."""
        if self.initial_LLR_matrix is None:
            self.MPI_Abort("Build_Single_Row_Matrix: initial_LLR_matrix is None")

        src = self.initial_LLR_matrix
        new_matrix = src.Deep_Copy(matrix_idx, copy_raw_FER=False, copy_seed_FER=False)

        # 랜덤 row 생성
        row_values = self._generate_random_row(new_matrix)
        iteration = SINGLE_ROW_CONFIG.CANDIDATE_ITERATION
        floor_flag = src.groups[0][0].floor_flag if src.groups and src.groups[0] else SW_BRANCH_NONE

        new_row = LLR_Row(
            ch_th_values=row_values,
            CSW=-1,
            iter_start=1,
            iter_end=iteration,
            floor_flag=floor_flag,
            is_group_restart=False,
        )

        # 그룹 교체: 1-group, 1-row
        self._Replace_With_Single_Group(new_matrix, [new_row], iteration)

        # 자동 보정
        try:
            new_matrix.Correct_LLR_Matrix()
        except ValueError as e:
            self.Write_Log_Lines(f"[WARN] Correct_LLR_Matrix failed in Build_Single_Row: {e}")
            return None

        is_valid, msg = new_matrix.Is_LLR_Valid()
        if not is_valid:
            self.Write_Log_Lines(f"[Build_Single_Row_Matrix] Invalid matrix {matrix_idx}: {msg}")
            return None

        return new_matrix

    def Parse_CSW_Min_Values(self, ch_idx: int) -> list[int]:
        """CSW 로그에서 uncor별 min CSW 값을 파싱한다. (root 전용)

        Returns:
            uncor별 min CSW 값 리스트. 디코딩 실패 시 해당 uncor는 제외.
        """
        all_min_csws = []
        for proc in range(self.num_process):
            if proc in self.excluded_cores:
                continue
            csw_file_name = self.Get_CSW_Log_File_Name(process_idx=proc)
            process_session_dir = self.Get_Local_Session_Dir(proc)
            csw_file_path = os.path.join(process_session_dir, csw_file_name)

            if not os.path.exists(csw_file_path):
                continue
            with open(csw_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) > 2:
                        csw_vals = [int(v) for v in parts[2:] if v.strip() != '-1']
                        if csw_vals:
                            all_min_csws.append(min(csw_vals))
        return all_min_csws

    def _Save_Top_K_Matrices(self, save_dir: str, top_candidates: list[dict]):
        """Top-K 매트릭스를 diff 기반으로 저장한다. 탈락한 파일만 삭제, 새 진입만 저장."""
        os.makedirs(save_dir, exist_ok=True)

        new_names = {c['matrix'].LLR_matrix_file_name for c in top_candidates}
        # 기존 파일 중 Top-K에서 탈락한 것만 삭제
        for f, _ in self._List_LLR_Matrix_Files(save_dir):
            if f not in new_names:
                os.remove(os.path.join(save_dir, f))
        # Top-K 중 아직 없는 것만 저장
        for c in top_candidates:
            file_path = os.path.join(save_dir, c['matrix'].LLR_matrix_file_name)
            if not os.path.exists(file_path):
                c['matrix'].Save_Matrix(save_dir)

    def Rank_And_Save_Single_Row_Candidates(self, candidates: list[dict]):
        """후보들을 채널별 FER/CSW 기준으로 ranking하고 Top-K를 기준별 폴더에 저장한다. (root 전용)"""
        top_k = SINGLE_ROW_CONFIG.TOP_K
        num_channels = REFC_CONFIG.NUM_TARGET_CHANNELS

        for ch_idx in range(num_channels):
            ch_dir = os.path.join(self.single_row_candidates_dir, f"ch{ch_idx}")

            os.makedirs(ch_dir, exist_ok=True)

            # 공통 성능 문자열 생성 헬퍼
            def _format_all_metrics(c, ch):
                total = c['total_uncors'].get(ch, 0)
                parts = [f"FER={c['FERs'][ch]:.6e}", f"avg_iter={c['avg_iters'][ch]:.2f}", f"total_uncor={total}"]
                ch_csw = c['csw_threshold_counts'].get(ch, {})
                for t in SINGLE_ROW_CONFIG.CSW_THRESHOLDS:
                    parts.append(f"#uncor(csw≤{t})={ch_csw.get(t, 0)}/{total}")
                return ", ".join(parts)

            # workspace 후보 수집용 (모든 ranking의 Top-K를 중복 없이 병합)
            workspace_candidates = {}  # LLR_matrix_file_name -> candidate

            # --- FER 기준 ranking ---
            fer_dir = os.path.join(ch_dir, "FER")
            # FER=1.0 (미측정/최악)은 제외
            valid_fer = [c for c in candidates if c['FERs'][ch_idx] < 1.0]
            sorted_by_fer = sorted(valid_fer, key=lambda c: c['FERs'][ch_idx])
            top_fer = sorted_by_fer[:top_k]

            summary_path = os.path.join(ch_dir, "summary_by_FER.txt")
            try:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Top-{top_k} candidates by FER (ch {ch_idx})\n")
                    f.write(f"# Ranking metric: FER — Frame Error Rate (낮을수록 상위)\n")
                    f.write(f"# Total candidates: {len(candidates)}, valid (FER<1.0): {len(valid_fer)}\n\n")
                    for rank, c in enumerate(top_fer, 1):
                        f.write(f"[Rank {rank}] Candidate {c['idx']}: {_format_all_metrics(c, ch_idx)}\n")
            except OSError as e:
                self.MPI_Abort(f"Rank_And_Save_Single_Row_Candidates: FER 요약 쓰기 실패 — {summary_path}: {e}")
            self._Save_Top_K_Matrices(fer_dir, top_fer)
            self.Write_Log_Lines(f"[GEN_SINGLE_ROW] ch{ch_idx}/FER ranking saved ({len(top_fer)} matrices)")
            for c in top_fer:
                workspace_candidates[c['matrix'].LLR_matrix_file_name] = c

            # --- CSW threshold별 ranking ---
            for threshold in SINGLE_ROW_CONFIG.CSW_THRESHOLDS:
                csw_dir = os.path.join(ch_dir, f"CSW_T{threshold}")
                # 해당 threshold count가 0인 후보는 제외
                valid_csw = [c for c in candidates if c['csw_threshold_counts'].get(ch_idx, {}).get(threshold, 0) > 0]
                sorted_by_csw = sorted(
                    valid_csw,
                    key=lambda c, t=threshold: c['csw_threshold_counts'].get(ch_idx, {}).get(t, 0),
                    reverse=True
                )
                top_csw = sorted_by_csw[:top_k]

                summary_path = os.path.join(ch_dir, f"summary_by_CSW_T{threshold}.txt")
                try:
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Top-{top_k} candidates by CSW threshold T={threshold} (ch {ch_idx})\n")
                        f.write(f"# Ranking metric: #uncor(csw≤{threshold}) — uncorrectable 중 min_csw ≤ {threshold}인 개수 (많을수록 상위)\n")
                        f.write(f"# Total candidates: {len(candidates)}, valid (#uncor(csw≤{threshold})>0): {len(valid_csw)}\n\n")
                        for rank, c in enumerate(top_csw, 1):
                            f.write(f"[Rank {rank}] Candidate {c['idx']}: {_format_all_metrics(c, ch_idx)}\n")
                except OSError as e:
                    self.MPI_Abort(f"Rank_And_Save_Single_Row_Candidates: CSW T={threshold} 요약 쓰기 실패 — {summary_path}: {e}")
                self._Save_Top_K_Matrices(csw_dir, top_csw)
                self.Write_Log_Lines(f"[GEN_SINGLE_ROW] ch{ch_idx}/CSW_T{threshold} ranking saved ({len(top_csw)} matrices)")
                for c in top_csw:
                    workspace_candidates[c['matrix'].LLR_matrix_file_name] = c

            # --- Collected_ch: 모든 ranking Top-K를 중복 없이 병합 저장 ---
            collected_ch_dir = os.path.join(ch_dir, f"collected_ch{ch_idx}")
            self._Save_Top_K_Matrices(collected_ch_dir, list(workspace_candidates.values()))
            self.Write_Log_Lines(f"[GEN_SINGLE_ROW] ch{ch_idx}/collected_ch{ch_idx} saved ({len(workspace_candidates)} unique matrices)")

        # --- Collected: 전 채널 collected_ch를 중복 없이 단일 폴더에 취합 ---
        all_candidates = {}  # LLR_matrix_file_name -> src_path
        for ch_idx in range(num_channels):
            collected_ch_dir = os.path.join(self.single_row_candidates_dir, f"ch{ch_idx}", f"collected_ch{ch_idx}")
            if not os.path.isdir(collected_ch_dir):
                continue
            for f, _ in self._List_LLR_Matrix_Files(collected_ch_dir):
                if f not in all_candidates:
                    all_candidates[f] = os.path.join(collected_ch_dir, f)

        collected_dir = os.path.join(self.single_row_candidates_dir, "collected")
        os.makedirs(collected_dir, exist_ok=True)
        # diff 기반: 탈락 파일 삭제, 신규만 복사
        for f, _ in self._List_LLR_Matrix_Files(collected_dir):
            if f not in all_candidates:
                os.remove(os.path.join(collected_dir, f))
        for file_name, src_path in all_candidates.items():
            dst_path = os.path.join(collected_dir, file_name)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
        self.Write_Log_Lines(f"[GEN_SINGLE_ROW] collected saved ({len(all_candidates)} unique matrices across all channels)")

        self.Write_Log_Lines(f"[GEN_SINGLE_ROW] Ranking update complete: {len(candidates)} candidates evaluated")

    def _Export_Workspace_To_Input(self, candidates: list[dict]):
        """collected 폴더(전 채널 취합)를 Input Single_Row_LLR_Matrix 경로로 복사한다.
        폴더명은 현재 시각 (YYYYMMDD_HHMMSS). root 전용.
        """
        if not candidates:
            return

        collected_dir = os.path.join(self.single_row_candidates_dir, "collected")
        if not os.path.isdir(collected_dir):
            return

        file_list = self._List_LLR_Matrix_Files(collected_dir)
        if not file_list:
            return

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = os.path.join(PATH_CONFIG.INPUT_SINGLE_ROW_LLR_MATRIX_DIR_PATH, timestamp)
        os.makedirs(export_dir, exist_ok=True)

        for file_name, _ in file_list:
            shutil.copy2(os.path.join(collected_dir, file_name), os.path.join(export_dir, file_name))

        self.Write_Log_Lines(
            f"[GEN_SINGLE_ROW] collected → {export_dir} ({len(file_list)} files exported)"
        )
        self.Write_Log_Lines(
            f"[GEN_SINGLE_ROW] Export 완료. COPY_ROWS_CONFIG.EXTERNAL_SINGLE_ROW_DIRS에 "
            f'"{timestamp}" 추가하여 사용 가능'
        )

def Main():
    
    LLR_opt: Optional[LLR_OPT] = None
    try:
        LLR_opt = LLR_OPT()
        LLR_opt.Main()
    except Exception as exc:
        if LLR_opt is not None:
            try:
                LLR_opt.Log_Unhandled_Exception(exc)
            except Exception as log_error:
                log_dir = os.path.join(LLR_opt.session_dir, ERROR_LOG_DIR_NAME) if getattr(LLR_opt, "session_dir", None) else None
                _write_error_log(rank, log_error, None, error_dir=log_dir)
                _write_error_log(rank, exc, None, error_dir=log_dir)
            LLR_opt.MPI_Abort(f"Unhandled exception: {type(exc).__name__}: {exc}")
        else:
            _write_error_log(rank, exc, None, error_dir=None)
            comm.Abort(1)

if __name__ == "__main__":
    try:
        Set_Configs_Manually()
        Update_Configs()
    except Exception as e:
        # LLR_OPT 미생성 상태이므로 comm.Abort() 직접 호출
        _write_error_log(rank, e)
        comm.Abort(1)
    Main()
