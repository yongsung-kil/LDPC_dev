import os
from enum import Enum, IntEnum
from mpi4py import MPI

MODE_MAP = {1: "HD", 2: "2SD", 3: "3SD"}

class ChType(IntEnum):
    RBER = 1
    FIXED_ERROR = 2
    STRONG_ERROR = 3

class UpdateMode(IntEnum):
    OPTIMAL_MATRIX_FROM_CURRENT = 1
    OPTIMAL_MATRIX_FROM_TEMP_OPTIMAL = 2
    TEMP_OPTIMAL_MATRIX_FROM_CURRENT = 3

class SeedMode(IntEnum):
    DEFAULT = 0
    SAVE_UNCOR_SEED = 1
    LOAD_UNCOR_SEED = 2
    LOAD_UNCOR_VECTOR = 3
    LOAD_UNCOR_SEED_SAVE_UNCOR_SEED = 12    # Uncor를 불러와서 test 후 decoding fail seed만 저장

class GenLLRMode(IntEnum):
    GEN_INITIAL_GROUP = 0
    MUTATE_MATRIX = 10
    MUTATE_CSW = 11
    SWAP_ROW = 21
    REORDER_GROUP = 22
    COPY_ROWS = 30
    COPY_GROUP = 31
    INSERT_RANDOM_GROUP = 40
    INSERT_RANDOM_ROW = 41
    INSERT_MUTATED_GROUP = 42
    INSERT_MUTATED_ROW = 43
    REGEN_DV = 50
    REGEN_ROW = 51
    SPLIT_GROUP = 60
    ADJUST_ITERATION = 62
    DELETE_ROW = 70
    INSERT_RESTART_GROUP = 80

class GenLLRModeHBF(IntEnum):
    INSERT_RANDOM_GROUP = GenLLRMode.INSERT_RANDOM_GROUP
    INSERT_RANDOM_ROW = GenLLRMode.INSERT_RANDOM_ROW
    MUTATE_MATRIX = GenLLRMode.MUTATE_MATRIX
    MUTATE_CSW = GenLLRMode.MUTATE_CSW
    SPLIT_GROUP = GenLLRMode.SPLIT_GROUP
    GEN_INITIAL_GROUP = GenLLRMode.GEN_INITIAL_GROUP
    COPY_GROUP = GenLLRMode.COPY_GROUP
    SWAP_ROW = GenLLRMode.SWAP_ROW

class OperatingSystem(Enum):
    WINDOWS = "nt"
    LINUX = "posix"

class DAOLoadUncorMode(IntEnum):
    DEFAULT = -1
    LOAD_NONE = 0               # Do not load uncor seed/vector
    LOAD_SEED = 1     # Load uncor seed, no extension
    LOAD_VECTOR = 2   # Load uncor vector, no extension

class RunDAOMode(IntEnum):
    RUN_OPTIMIZATION = 0            # 정상 최적화 모드
    TEST_FER = 1                    # 초기 매트릭스 FER 테스트 후 종료
    SAVE_UNCOR = 2                  # 초기 매트릭스로 uncor 저장 후 종료
    REDECODE = 3                    # uncor 로드 후 다시 저장하고 종료
    GEN_SINGLE_ROW = 4              # 단일 row 후보 생성 + 테스트 + ranking

class TestMode(IntEnum):
    """Two-stage 테스트 모드"""
    PARTIAL = 1  # Partial 테스트 (빠른 스크리닝, 1차 필터링)
    FULL = 2     # Full 테스트 (정확한 평가, Update 판단 기준)

# TestMode와 디렉토리명 매핑 (Partial만 서브디렉토리 사용, Full은 루트)
TEST_MODE_DIR_NAME = {
    TestMode.PARTIAL: "Partial",
}

if os.name == OperatingSystem.WINDOWS.value:
    CURRENT_OS = OperatingSystem.WINDOWS
elif os.name == OperatingSystem.LINUX.value:
    CURRENT_OS = OperatingSystem.LINUX
else:
    CURRENT_OS = OperatingSystem.LINUX

DEBUG_DIR_NAME = "7_Debug"
DEBUG_FILE_NAME = "debug.txt"

WORK_SPACE_DIR_NAME = "Work_Space"
SRC_DIR_NAME = "SRC"
SRC_BACKUP_DIR_NAME = "0_SRC_BACKUP"
LOG_DIR_NAME = "1_Log"
INPUT_DIR_NAME = "Input"
REF_C_DIR_NAME = "Ref_C"
H_MATRIX_DIR_NAME = "H_Matrix"
INPUT_UNCOR_DIR_NAME = "Uncors"
SESSION_UNCOR_DIR_NAME = "5_Uncors"
PROCESS_DIR_NAME_HEAD = "Process"
END_FLAG_DIR_NAME = "8_End_flag"
RUN_ECC_END_FLAG_FILE_NAME = "run_ecc_end_flag.txt"
TRIAL_END_FLAG_FILE_NAME = "trial_end_flag.txt"
DAO_END_FLAG_FILE_NAME = "dao_end_flag.txt"
GEN_SINGLE_ROW_STOP_IDX_FILE_NAME = "gen_single_row_stop_idx.txt"
SINGLE_ROW_CANDIDATES_DIR_NAME = "9_Single_Row_Candidates"
UNCOR_POOL_DIR_NAME = "Uncor_Pool"
TMP_PARTIAL_UNCORS_DIR_NAME = "tmp_partial_uncors"  # Dynamic Partial: fail uncor 임시 저장 디렉토리

REF_C_EXE_DIR_NAME = "EXE"
REF_C_SRC_DIR_NAME = "SRC"
ECC_NAME_TEMPLATE = "Prime_ECC_{ecc_ver}"
UTIL_DIR_NAME = "Util"
INITIAL_LLR_MATRIX_DIR_NAME = "Initial_LLR_matrix"
SINGLE_ROW_LLR_MATRIX_DIR_NAME = "Single_Row_LLR_Matrix"

TRIAL_LLR_MATRIX_DIR_NAME = "3_Trial_LLR_matrix"
ERROR_LLR_MATRIX_DIR_NAME = "4_Error_LLR_matrix"
OPTIMAL_LLR_MATRIX_DIR_NAME = "2_Optimal_LLR_matrix"
LOG_CSW_FILE_NAME_HEAD = "log_CSW_"
MAKEFILE_NAME = "Makefile"
OBJECT_DIR_NAME = "object"

ERROR_LOG_DIR_NAME = "6_Error_Log"
ERROR_LOG_FILE_TEMPLATE = "error_logs_{process_idx}.txt"
MAX_COLLECTION_PREVIEW = 20
MAX_SUMMARY_DEPTH = 4

EXTENSIONS_TO_REMOVE = [".bat", ".sh", ".tmp"]
HEADER_TO_REMOVE = ["result", "log_CSW", "Ref_C_result"]

SEPARATOR_LENGTH = 20
SEPARATOR_TYPE1 = "-" * SEPARATOR_LENGTH
SEPARATOR_TYPE2 = "=" * SEPARATOR_LENGTH

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num_process = comm.Get_size()

LOG_MAX_LINES = 10000
MAX_CSW = 1408
MIN_CSW = 8
STEP_CSW = 8

SIM_MAX_TIME_OUT = 10 * 60 * 60

# Core 속도 테스트용 고정 시드 (모든 프로세스가 동일한 시드로 테스트하여 속도 측정)
CORE_SPEED_TEST_SEED = 9999

# Restart group을 skip하는 모드 목록
# 이 모드들은 Initialize_Stage에서 current_target_idx가 restart group을 가리키면 다음으로 넘어감
SKIP_RESTART_GROUP = [
    GenLLRMode.GEN_INITIAL_GROUP,
    GenLLRMode.MUTATE_MATRIX,
    GenLLRMode.MUTATE_CSW,
    GenLLRMode.SWAP_ROW,
    GenLLRMode.COPY_ROWS,
    GenLLRMode.COPY_GROUP,
    GenLLRMode.INSERT_RANDOM_ROW,
    GenLLRMode.INSERT_MUTATED_ROW,
    GenLLRMode.REGEN_DV,
    GenLLRMode.REGEN_ROW,
    GenLLRMode.SPLIT_GROUP,
    GenLLRMode.ADJUST_ITERATION,
    ]

# Multi-round 모드 공용 설정
# - 모드별 state 속성명 매핑
# - 메인 루프, Gen_Trial_LLR bcast, Initialize_Stage, Set_Update_Flags에서 공용 처리
MULTI_ROUND_MODES: dict[int, str] = {
    GenLLRMode.REORDER_GROUP: 'reorder_state',
    GenLLRMode.ADJUST_ITERATION: 'adjust_iter_state',
    GenLLRMode.DELETE_ROW: 'delete_row_state',
    GenLLRMode.INSERT_RESTART_GROUP: 'insert_restart_group_state',
}

# Multi-round 모드 중 Partial 테스트 스킵 → Full만 수행하는 모드
# - REORDER_GROUP: 순서만 바꾸므로 Partial 결과가 Full과 다를 수 있음
# - ADJUST_ITERATION: iteration 값 변경이 전체 성능에 영향
MULTI_ROUND_FULL_ONLY_MODES: set[int] = {
    GenLLRMode.REORDER_GROUP,
    GenLLRMode.ADJUST_ITERATION,
}

# Multi-round 모드 중 round result update 함수가 있는 모드
MULTI_ROUND_UPDATE_FUNC: dict[int, str] = {
    GenLLRMode.REORDER_GROUP: 'Update_Reorder_Round_Result',
    GenLLRMode.DELETE_ROW: 'Update_Delete_Row_Round_Result',
    GenLLRMode.INSERT_RESTART_GROUP: 'Update_Insert_Restart_Group_Round_Result',
}

# Multi-round 모드별 초기화 함수
MULTI_ROUND_INIT_FUNC: dict[int, str] = {
    GenLLRMode.REORDER_GROUP: 'Init_Reorder_Group_Mode',
    GenLLRMode.ADJUST_ITERATION: 'Init_Adjust_Iteration_Mode',
    GenLLRMode.DELETE_ROW: 'Init_Delete_Row_Mode',
    GenLLRMode.INSERT_RESTART_GROUP: 'Init_Insert_Restart_Group_Mode',
}

# SW(Syndrome Weight) 분기: 각 row의 마지막 칸(floor_flag)이 분기 index다
SW_BRANCH_NONE = -1          # 분기 없음
MAX_SW_BRANCH = 9            # 한 구간의 분기 index 상한 (파일 헤더가 한 자리씩 끊어 읽는다)

# 타겟 그룹에 SW 분기 그룹이 들어 있을 때 허용되는 모드. 나머지 모드는 이웃 그룹의 iteration을 빌리거나
# 재배치해 구간 정렬을 깨뜨리므로 Set_Gen_Trial_LLR_Mode가 오류로 멈춘다. 타겟이 분기 구간 뒤의 보통 그룹뿐이면
# 다른 모드도 쓸 수 있고, 그때 타겟 앞 그룹을 바꾼 trial은 Gen_Trial_LLR이 버린다
SW_BRANCH_ALLOWED_MODES: set[int] = {
    GenLLRMode.MUTATE_MATRIX,
    GenLLRMode.MUTATE_CSW,
}

# FIXED_TARGET_GROUP_IDX_LIST로 타겟 그룹을 직접 지정했을 때 허용되는 모드. 목록의 index는 그룹 번호에 묶여 있으므로
# 그룹 수, 그룹 순서, iteration 구간을 그대로 두고 타겟 그룹 안의 값과 row만 바꾸는 모드만 쓴다
FIXED_TARGET_GROUP_ALLOWED_MODES: set[int] = {
    GenLLRMode.MUTATE_MATRIX,
    GenLLRMode.MUTATE_CSW,
    GenLLRMode.SWAP_ROW,
    GenLLRMode.COPY_ROWS,
    GenLLRMode.COPY_GROUP,
    GenLLRMode.INSERT_RANDOM_ROW,
    GenLLRMode.INSERT_MUTATED_ROW,
    GenLLRMode.REGEN_DV,
    GenLLRMode.REGEN_ROW,
}
