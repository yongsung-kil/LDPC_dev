from __future__ import annotations
import os, sys
from typing import Optional
from DAO_Constants import *


"""
== Quick Config Setting ==

- SIM_IDX=10: HD opt
- SIM_IDX=11: HD Save UECC
- SIM_IDX=12: HD redecoding
- SIM_IDX=20: 2SD opt
- SIM_IDX=21: 2SD Save UECC
- SIM_IDX=22: 2SD redecoding
- SIM_IDX=30: 3SD opt
- SIM_IDX=31: 3SD Save UECC
- SIM_IDX=32: 3SD redecoding

"""

def Set_Configs_Manually():
    """ args를 입력받는 경우 이 함수에서 mapping
    """
    args = sys.argv

    if len(args) > 1:
        SIM_IDX = int(args[1])
    else:
        return

    if SIM_IDX == 10:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 100
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.RUN_OPTIMIZATION
        DAO_CONFIG.Gen_LLR_Mode_SEQUENCE = [GenLLRMode.REORDER_GROUP, GenLLRMode.MUTATE_MATRIX, GenLLRMode.MUTATE_CSW, GenLLRMode.REORDER_GROUP]
        REFC_CONFIG.init_n = 1
        REFC_CONFIG.ch_type = 2
        REFC_CONFIG.num_fixed_errs = [370, 410]
        REFC_CONFIG.MAX_DECODING_ITERATION = 200
        UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST = True
        UNCOR_CONFIG.UNCOR_MATRIX_IDX = 102
        
    elif SIM_IDX == 11:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 100
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.SAVE_UNCOR
        REFC_CONFIG.init_n = 1
        REFC_CONFIG.ch_type = 2
        REFC_CONFIG.num_fixed_errs = [370, 410]

    elif SIM_IDX == 12:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 100
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.REDECODE
        REFC_CONFIG.init_n = 1
        REFC_CONFIG.ch_type = 2
        REFC_CONFIG.num_fixed_errs = [370, 410]
        UNCOR_CONFIG.UNCOR_MATRIX_IDX=103

    elif SIM_IDX == 20:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 200
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.RUN_OPTIMIZATION
        DAO_CONFIG.Gen_LLR_Mode_SEQUENCE = [GenLLRMode.REORDER_GROUP, GenLLRMode.MUTATE_MATRIX, GenLLRMode.MUTATE_CSW, GenLLRMode.REORDER_GROUP]
        REFC_CONFIG.init_n = 2
        REFC_CONFIG.ch_type = 3
        REFC_CONFIG.num_fixed_errs = [520, 530]
        REFC_CONFIG.fixed_SCRs = [0.94]
        REFC_CONFIG.fixed_SERs = [0.23]
        REFC_CONFIG.MAX_DECODING_ITERATION = 700
        UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST = True
        UNCOR_CONFIG.UNCOR_MATRIX_IDX = 202
    
    elif SIM_IDX == 21:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 200
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.SAVE_UNCOR
        REFC_CONFIG.init_n = 2
        REFC_CONFIG.ch_type = 3
        REFC_CONFIG.num_fixed_errs = [520, 530]
        REFC_CONFIG.fixed_SCRs = [0.94]
        REFC_CONFIG.fixed_SERs = [0.23]

    elif SIM_IDX == 22:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 200
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.REDECODE
        REFC_CONFIG.init_n = 2
        REFC_CONFIG.ch_type = 3
        REFC_CONFIG.num_fixed_errs = [520, 530]
        REFC_CONFIG.fixed_SCRs = [0.94]
        REFC_CONFIG.fixed_SERs = [0.23]
        UNCOR_CONFIG.UNCOR_MATRIX_IDX = 203

    elif SIM_IDX == 30:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 300
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.RUN_OPTIMIZATION
        DAO_CONFIG.Gen_LLR_Mode_SEQUENCE = [GenLLRMode.REORDER_GROUP, GenLLRMode.MUTATE_MATRIX, GenLLRMode.MUTATE_CSW, GenLLRMode.REORDER_GROUP]
        REFC_CONFIG.init_n = 3
        REFC_CONFIG.ch_type = 1
        REFC_CONFIG.RBERs = [0.017, 0.018]
        REFC_CONFIG.MAX_DECODING_ITERATION = 1400
        UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST = True
        UNCOR_CONFIG.UNCOR_MATRIX_IDX = 302

    elif SIM_IDX == 31:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 300
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.SAVE_UNCOR
        REFC_CONFIG.init_n = 3
        REFC_CONFIG.ch_type = 1
        REFC_CONFIG.RBERs = [0.017, 0.018]

    elif SIM_IDX == 32:
        DAO_CONFIG.INITIAL_MATRIX_IDX = 300
        DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.REDECODE
        REFC_CONFIG.init_n = 3
        REFC_CONFIG.ch_type = 1
        REFC_CONFIG.RBERs = [0.017, 0.018]
        UNCOR_CONFIG.UNCOR_MATRIX_IDX = 303

    else:
        raise ValueError(f"Set_Configs_Manually: 미정의 SIM_IDX={SIM_IDX}. 유효 값: 10~12, 20~22, 30~32")


class DAO_CONFIG:
    INITIAL_MATRIX_IDX: int = 999        # 초기 LLR 매트릭스 인덱스 (단일)
    INITIAL_MATRIX_IDX_LIST: Optional[list] = None  # 복수 매트릭스 인덱스 (TEST_FER/SAVE_UNCOR/REDECODE 모드 전용, None이면 INITIAL_MATRIX_IDX 사용)
    MAX_RUN_ECC_ERRORS: int = 9999               # RUN_ECC 오류 수
    MAX_OPTIMIZATION_STAGE: int = 9999         # 최대 최적화 Stage 수
    MAX_OPTIMIZATION_TRIALS: int = 9999         # 각 모드별 기본 시도 횟수 (특정 모드에서는 모드에 따라 max trial 설정됨)
    MAX_GEN_RETRY_PER_TRIAL: int = 5          # 한 trial당 LLR 생성 최대 재시도 횟수
    IS_HBF_OPT:bool = False                # HBF 최적화 여부. init_n == 1인 경우에만 True 가능

    # DAO 실행 모드 설정
    RUN_DAO_MODE: RunDAOMode = RunDAOMode.RUN_OPTIMIZATION

    # LLR 생성 모드 순서 설정. stage마다 목록의 다음 모드를 돌고, 끝까지 가면 처음으로 돌아간다
    # 두 목록에서 돌릴 모드만 남기고 순서를 정한다
    # - 타겟에 SW 분기 그룹이 있으면 MUTATE_MATRIX와 MUTATE_CSW만 남긴다 (Validate_Config가 시작할 때 검사)
    # - FIXED_TARGET_GROUP_IDX_LIST를 쓰면 FIXED_TARGET_GROUP_ALLOWED_MODES의 모드만 남긴다 (Validate_Config가 시작할 때 검사)
    # 보통 모드의 시퀀스. GenLLRMode의 모드를 모두 적은 목록이다
    Gen_LLR_Mode_SEQUENCE = [
        GenLLRMode.GEN_INITIAL_GROUP,      # stage 1에서만 돈다 (맨 앞에 둔다)
        GenLLRMode.MUTATE_MATRIX,
        GenLLRMode.MUTATE_CSW,
        GenLLRMode.SWAP_ROW,
        GenLLRMode.REORDER_GROUP,
        GenLLRMode.COPY_ROWS,
        GenLLRMode.COPY_GROUP,
        GenLLRMode.INSERT_RANDOM_GROUP,
        GenLLRMode.INSERT_RANDOM_ROW,
        GenLLRMode.INSERT_MUTATED_GROUP,
        GenLLRMode.INSERT_MUTATED_ROW,
        GenLLRMode.REGEN_DV,
        GenLLRMode.REGEN_ROW,
        GenLLRMode.SPLIT_GROUP,
        GenLLRMode.ADJUST_ITERATION,
        GenLLRMode.DELETE_ROW,
        GenLLRMode.INSERT_RESTART_GROUP,
    ]
    # HBF 최적화 모드(IS_HBF_OPT)의 시퀀스. GenLLRModeHBF에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 뺀 목록이다
    # 두 모드가 만드는 그룹은 기본 설정값(iteration 20칸)에서 iteration 구간 경계(4, 8)를 걸쳐 trial이 버려진다
    Gen_LLR_Mode_HBF_SEQUENCE = [
        GenLLRModeHBF.INSERT_RANDOM_ROW,
        GenLLRModeHBF.MUTATE_MATRIX,
        GenLLRModeHBF.MUTATE_CSW,
        GenLLRModeHBF.SPLIT_GROUP,
        GenLLRModeHBF.COPY_GROUP,
        GenLLRModeHBF.SWAP_ROW,
        GenLLRModeHBF.COPY_ROWS,
        GenLLRModeHBF.REGEN_DV,
        GenLLRModeHBF.REGEN_ROW,
    ]
    INITIAL_TARGET_GROUP_IDX: int = 1  # 이 인덱스부터 끝까지를 opt 타겟 그룹으로 설정. 예: 1이면 [1, 2, 3, ...], 0이면 [0, 1, 2, ...]
    FIXED_TARGET_GROUP_IDX_LIST: Optional[list] = None  # opt 타겟 그룹을 직접 지정. 예: [0, 1]이면 그룹 0과 1만 변경. None이면 INITIAL_TARGET_GROUP_IDX부터 끝까지. 함께 쓸 수 있는 모드는 FIXED_TARGET_GROUP_ALLOWED_MODES
    ENABLE_AVG_ITER_UPDATE: bool = False  # FER 동일 시 avg_iteration 개선으로도 update 허용 여부

    @staticmethod
    def  Get_Initial_Matrix_Idx_List() -> list[int]:
        """INITIAL_MATRIX_IDX_LIST가 설정되면 그것을, 아니면 [INITIAL_MATRIX_IDX]를 반환한다."""
        if DAO_CONFIG.INITIAL_MATRIX_IDX_LIST is not None:
            return list(DAO_CONFIG.INITIAL_MATRIX_IDX_LIST)
        return [DAO_CONFIG.INITIAL_MATRIX_IDX]

    # 참고
    """
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
    """

# Core experiment selection
class REFC_CONFIG:
    """RefC 실행 관련 설정"""
    ECC_VER = "3.0"
    matrix_sel = 1
    init_n = 1
    ch_type = 2
    RBERs = [0.0135]
    num_fixed_errs = [400]
    fixed_SCRs = [0.94, 0.95]
    fixed_SERs = [0.23, 0.17]
    fixed_erasure_ratios = [0, 0]
    fn = 3
    max_num_test = 1000
    mode_seed = 0
    mode_init_seed = 0
    mode_all_one_cw = 1
    CRC_Option_F_P = 4
    mode_iter = 0
    mode_scenario = 0
    LLR_matrix_idx = 1
    CRC_skip_mode = 1
    HighDV_skip_mode = 1
    str_matrix_name = "H_402091"
    """추가 설정들"""
    NUM_TARGET_CHANNELS: int = 0         # MULTI_FER_OPTIMIZATION이 True인 경우 채널 수 자동 설정
    MAX_DECODING_ITERATION: int = 1500        # LDPC code max iteration


class UNCOR_CONFIG:
    """Uncor 관련 설정"""
    # Two-Stage Test 설정 (Partial → Full)
    # False: 기존 방식 (Full 테스트만 수행, UNCOR_MATRIX_IDX 사용)
    # True: Partial 테스트 후 개선 시에만 Full 테스트 수행 (Partial은 Full uncor 재decoding으로 동적 생성)
    ENABLE_TWO_STAGE_TEST: bool = False

    # Uncor seed경로 설정
    # -1 : HD/ 경로에서 사용
    # >= 0 : HD/{llr_name}/ 경로에서 사용
    # Two-stage=True일 때: Full uncor 경로(루트), Two-stage=False일 때: 유일한 uncor 경로
    UNCOR_MATRIX_IDX: int = -1

    # Load Vector 설정
    ENABLE_LOAD_VECTOR = False           # Load uncor vector 활성화 여부
    IS_TLC = True                        # TLC 여부
    LEN_NO_PS: int = 0

    # 종속성 있는 변수들 (기본값만 설정, Update 함수에서 재계산됨)
    NUM_LINES_PER_UNCOR: int = 1
    LOAD_UNCOR_MODE: DAOLoadUncorMode = DAOLoadUncorMode.DEFAULT    # 초기 uncor 로드 모드


class SPEED_TEST_REFC_CONFIG(REFC_CONFIG):
    """Core 속도 측정용 RefC 설정

    REFC_CONFIG를 상속받아 기본값은 유지하되,
    speed test에 필요한 파라미터만 override한다.
    """
    ENABLE_CORE_SPEED_TEST = True           # True: 코어 속도 테스트 활성화, False: 비활성화
    CORE_SPEED_CUTOFF_RATIO = 2.0           # 평균 대비 몇 배 느리면 제외할지 (2.0 = 평균의 2배)
    RECHECK_INTERVAL_STAGES: int = 0        # 0: 비활성화, N: N stage마다 speed test 재실행
    RECHECK_INTERVAL_SECONDS: int = 0       # 0: 비활성화, N: N초마다 trial 내부에서 speed test 재실행

    fn = 1
    max_num_test = 1
    ch_type = 1  # RBER 모드
    RBERs = [0.1]
    num_fixed_errs = [0]
    fixed_SCRs = [0.94]
    fixed_SERs = [0.23]
    mode_seed = 0
    mode_init_seed = CORE_SPEED_TEST_SEED

class GEN_INITIAL_GROUP_CONFIG:
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    NUM_ROWS = 3
    ITERATION = 20

class MUTATE_CONFIG:
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    NUM_ELEMENTS_TO_MUTATE_CHTH = 2
    NUM_ELEMENTS_TO_MUTATE_CSW = 1
    MUTATION_RANGE = 5
    ENABLE_FINE_TUNING_AFTER_UPDATE = False
    ENABLE_CSW_UPDATE_LIMIT = False # True일 경우, CSW이 CSW_update_limit_value 미만인 row에 대해서만 mutation 수행
    if ENABLE_CSW_UPDATE_LIMIT:
        CSW_UPDATE_LIMIT_VALUE = 128

class INSERT_RANDOM_GROUP_CONFIG:
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    INSERT_GROUP_NUM_ROWS = 3
    INSERT_GROUP_NUM_ITERATION = 20
    if REFC_CONFIG.init_n == 1:
        ENABLE_INSERT_RESTART = False
    else:
        ENABLE_INSERT_RESTART = True    # True 시 trials 절반 이후부터 restart 추가

class INSERT_MUTATED_GROUP_CONFIG:
    """INSERT_MUTATED_GROUP 모드 설정

    기존 그룹을 복사 후 mutation을 적용하여 삽입하는 모드.
    INSERT_RANDOM_GROUP과 유사하지만 랜덤 생성 대신 기존 그룹을 mutate하여 사용.
    """
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    INSERT_GROUP_NUM_ITERATION: int = 20
    if REFC_CONFIG.init_n == 1:
        ENABLE_INSERT_RESTART = False
    else:
        ENABLE_INSERT_RESTART = True    # True 시 refresh 유/무 둘 다 검사

    # Mutation 설정 (MUTATE_CONFIG와 동일 구조, fine/coarse tuning 없음)
    NUM_ELEMENTS_TO_MUTATE_CHTH: int = 5     # 변이할 CH/TH 요소 수
    MUTATION_RANGE = 3                   # 변이 범위 (-MUTATION_RANGE ~ +MUTATION_RANGE)
    ALLOW_ZERO_MUTATION = True           # True: mutation 개수 0 허용 (그대로 복사)

class INSERT_MUTATED_ROW_CONFIG:
    """INSERT_MUTATED_ROW 모드 설정

    기존 row를 복사 후 mutation을 적용하여 삽입하는 모드.
    INSERT_RANDOM_ROW와 유사하지만 랜덤 생성 대신 기존 row를 mutate하여 사용.
    """
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    # Mutation 설정 (MUTATE_CONFIG와 동일 구조, fine/coarse tuning 없음)
    NUM_ELEMENTS_TO_MUTATE_CHTH = 2     # 변이할 CH/TH 요소 수
    MUTATION_RANGE = 2                   # 변이 범위 (-MUTATION_RANGE ~ +MUTATION_RANGE)
    ALLOW_ZERO_MUTATION = True           # True: mutation 개수 0 허용 (그대로 복사)

class REGEN_DV_CONFIG:
    """
    타겟 그룹의 특정 row, 특정 DV만 랜덤 재생성하는 모드 설정
    예: row_idx=1, dv_idx=2 위치의 DV(CH/TH 쌍)만 교체
    """
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    ENABLE_FIX_IDX: bool = False              # True일 때 고정 인덱스 사용. True시 아래 변수 사용(FIXED_ROW_IDX, FIXED_DV_IDX)
    FIXED_ROW_IDX: int | list[int] = -1  # -1: 전체 순회 | 정수: 단일 row 고정 (예: 0) | 리스트: 특정 rows만 순회 (예: [0, 2])
    FIXED_DV_IDX: int | list[int] = -1   # -1: 전체 순회 | 정수: 단일 dv 고정 (예: 1) | 리스트: 특정 dvs만 순회 (예: [0, 1, 3])

class REGEN_ROW_CONFIG:
    """
    타겟 그룹의 특정 row 전체(모든 DV)를 랜덤 재생성하는 모드 설정
    예: row_idx=1의 모든 DV(CH/TH 쌍 전체)를 한번에 교체
    """
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    ENABLE_FIX_IDX: bool = False      # True일 때 고정 인덱스 사용
    FIXED_ROW_IDX: int | list[int] = -1  # -1: 전체 순회 | 정수: 단일 row 고정 (예: 2) | 리스트: 특정 rows만 순회 (예: [1, 2])

class PRINT_LOG_CONFIG:
    """로그 출력 관련 설정"""
    # Default: True
    ENABLE_TEST_OPTIMAL_LLR_MATRIX_PRINT_CSW_LOG = True  # 최적 LLR 매트릭스 test 시 CSW 로그 출력 여부
    ENABLE_PRINT_ALL_ITER_FERs = True                    # True 시 모든 iteration의 FER 출력

class TIME_CONFIG:
    """시간 제한 관련 설정"""
    MAX_STAGE_TIMEOUT_SECONDS = 1 * 60 * 60    # Stage별 최대 실행 시간 (초 단위, 기본값: 1시간). 100시간 이상이면 제한 없음과 동일
    MAX_ECC_MEMORY_RETRY = 10             # ECC 실행 메모리 에러(Errno 12) 최대 재시도 횟수
    MAX_ECC_MEMORY_RETRY_DELAY = 60       # 메모리 에러 재시도 시 최대 대기 시간 (초, 0~이 값 사이 랜덤)
    MPI_COMM_TIMEOUT_SECONDS = 2*int(MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY)  # 짧은 집단 통신(bcast, gather)의 대기 상한. 메모리 재시도 최대 소요시간의 2배
    MPI_TEST_BARRIER_TIMEOUT_SECONDS = SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY + MPI_COMM_TIMEOUT_SECONDS  # ECC 실행을 사이에 둔 배리어와 allgather의 대기 상한. ECC 1회 허용 시간과 재시도 대기를 모두 덮는다

# Debug / logging toggles
class DEBUG_CONFIG:
    ENABLE_DEBUG_MODE = False            # 디버그 모드 활성화 여부

    if ENABLE_DEBUG_MODE:
        ENABLE_MPI_DEBUG_LOGGING = True
        ENABLE_FILE_BREAKPOINT = True
        ENABLE_PRINT_CLEAN_HISTORY = False
        ENABLE_LLR_MATRIX_SAVE_LOGGING = False
        IS_DEBUG_PAUSE_PRINT_SNAPSHOT = True
        ENABLE_UPDATE_LOG = True                    # Update 전용 로그 파일 생성 여부
        ENABLE_SAVE_ALL_TRIAL_LLR_MATRIX = True    # Try한 모든 LLR 매트릭스 출력 여부

    else:
        ENABLE_MPI_DEBUG_LOGGING = False
        ENABLE_FILE_BREAKPOINT = False
        ENABLE_PRINT_CLEAN_HISTORY = False
        ENABLE_LLR_MATRIX_SAVE_LOGGING = False
        IS_DEBUG_PAUSE_PRINT_SNAPSHOT = False
        ENABLE_UPDATE_LOG = False                   # Update 전용 로그 파일 생성 여부
        ENABLE_SAVE_ALL_TRIAL_LLR_MATRIX = False   # Try한 모든 LLR 매트릭스 출력 여부

    # Random state 재현을 위한 설정
    ENABLE_GET_RANDOM_STATE_FROM_CONFIG = False  # True일 경우 random state를 입력받은 값으로 설정
    if ENABLE_GET_RANDOM_STATE_FROM_CONFIG:
        # 사용법: 로그 파일에서 [Random state (base64)]를 복사하여 아래에 설정
        # 예시: RANDOM_STATE_TO_SET = "gANjcmFuZG9tAl9SQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQ..."
        RANDOM_STATE_TO_SET = "gANjcmFuZG9"  # base64로 인코딩된 random state 문자열
    else:
        RANDOM_STATE_TO_SET = None

class COPY_ROWS_CONFIG:
    """COPY_ROWS 모드 설정"""
    # 외부 Single Row 후보 활용
    ENABLE_EXTERNAL_SINGLE_ROW: bool = False
    EXTERNAL_SINGLE_ROW_DIRS: list[str] = []    # GEN_SINGLE_ROW 결과 폴더명 리스트 (예: ["20260330_143025", "20260331_091500"])
    MAX_EXTERNAL_CANDIDATES: int = 50          # 로드 상한 (trial 폭발 방지)

class INSERT_RANDOM_ROW_CONFIG:
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용

class HBF_OPT_CONFIG:
    def __init__(self):
        if REFC_CONFIG.init_n == 1:
            DAO_CONFIG.IS_HBF_OPT = True
        else:
            DAO_CONFIG.IS_HBF_OPT = False
    HBF_MAX_ITERATION = 4
    HBF_OPT_TH_CONSTANT_VAL = 0
    ITERATION_SPAN_ENDS = [4, 8]  # HBF 최적화 모드에서 row가 걸칠 수 없는 경계. 값 e는 iteration e와 e + 1 사이를 뜻한다 (4와 8이면 구간은 1~4, 5~8, 9 이후). HBF_MAX_ITERATION은 여기 없어도 언제나 경계다

class ADJUST_ITERATION_CONFIG:
    ITER_TRANSFER_RATIO: float = 0.1  # Iteration 전달 비율 (0.1 = donor group의 10%를 focus group에 전달)

class SPLIT_GROUP_CONFIG:
    """SPLIT_GROUP 모드 설정
    기존 그룹의 iteration을 분할하여 front/back 두 그룹으로 나누고,
    back 그룹의 ch_th_values에 mutation을 적용하는 모드.
    """
    MAX_TRIAL: int = -1  # -1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용
    SPLIT_RATIO: float = 0.5   # Front 그룹 iteration 비율 (0.0~1.0)

    # Mutation 설정 (back 그룹에 적용, MUTATE_CONFIG와 동일 구조)
    NUM_ELEMENTS_TO_MUTATE_CHTH: int = 3
    MUTATION_RANGE: int = 5
    ALLOW_ZERO_MUTATION: bool = True

class COPY_GROUP_CONFIG:
    pass

class SINGLE_ROW_CONFIG:
    """GEN_SINGLE_ROW 모드 설정"""
    NUM_GEN_TRIALS: int = 1000000               # 생성할 후보 row 수 (N)
    TOP_K: int = 200                         # 각 기준별 상위 K개 보관
    CSW_THRESHOLDS: list[int] = [200, 400, 600]  # CSW threshold 리스트 (min CSW <= T인 uncor 수 기준)
    CANDIDATE_ITERATION: int = 50           # 단일 row 매트릭스의 iteration 수
    RANKING_UPDATE_INTERVAL: int = 100      # N번마다 중간 ranking 저장 (Top-K 갱신 + 하위 삭제)
    ENABLE_PERIODIC_SPEED_TEST: bool = True  # True: 주기적 speed test + uncor 재분배
    SPEED_TEST_RECHECK_INTERVAL_SECONDS: int = 7200  # speed test 재실행 주기 (초, 기본 2시간, 0=비활성)
    END_FLAG_CHECK_INTERVAL: int = 10       # N번마다 DAO end flag 체크 (MPI_Barrier 동기화 후 읽기)

CONFIGS = [
    DAO_CONFIG,
    REFC_CONFIG,
    GEN_INITIAL_GROUP_CONFIG,
    MUTATE_CONFIG,
    INSERT_RANDOM_GROUP_CONFIG,
    INSERT_RANDOM_ROW_CONFIG,
    INSERT_MUTATED_GROUP_CONFIG,
    INSERT_MUTATED_ROW_CONFIG,
    HBF_OPT_CONFIG,
    REGEN_DV_CONFIG,
    REGEN_ROW_CONFIG,
    SPLIT_GROUP_CONFIG,
    COPY_ROWS_CONFIG,
    COPY_GROUP_CONFIG,
    SINGLE_ROW_CONFIG,
    UNCOR_CONFIG,
    PRINT_LOG_CONFIG,
    TIME_CONFIG,
    DEBUG_CONFIG,
    ]

class PATH_CONFIG:
    # 기본 경로 (종속성 없음, import 시점에 즉시 계산 가능)
    BASE_DIR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SRC_DIR_PATH = os.path.join(BASE_DIR_PATH, SRC_DIR_NAME)
    INPUT_DIR_PATH = os.path.join(BASE_DIR_PATH, INPUT_DIR_NAME)
    UTIL_DIR_PATH = os.path.join(BASE_DIR_PATH, UTIL_DIR_NAME)
    INPUT_REF_C_DIR_PATH = os.path.join(INPUT_DIR_PATH, REF_C_DIR_NAME)

    # 파일명 템플릿 (종속성 없음)
    BATCH_EXT = ".bat" if CURRENT_OS is OperatingSystem.WINDOWS else ".sh"
    LLR_MATRIX_FILE_NAME_TEMPLATE = "LLR_MATRIX_{matrix_idx}.txt"
    LOCAL_SESSION_DIR_NAME_TEMPLATE = f"{PROCESS_DIR_NAME_HEAD}_{{process_idx}}"

    # 종속성 있는 변수들 (기본값만 설정, Update_Path_Configs()에서 재계산됨)
    ECC_NAME: str = ""
    ECC_DIR_NAME: str = ""
    ECC_EXE_NAME: str = ""
    BATCH_FILE_TEMPLATE: str = ""
    INPUT_ECC_DIR_PATH: str = ""
    INPUT_LLR_MATRIX_DIR_PATH: str = ""
    INPUT_SINGLE_ROW_LLR_MATRIX_DIR_PATH: str = ""
    INPUT_UNCOR_DIR_PATH: str = ""
    INPUT_ECC_EXE_DIR_PATH: str = ""
    INPUT_ECC_EXE_PATH: str = ""
    INPUT_ECC_SRC_DIR_PATH: str = ""
    INPUT_H_MATRIX_DIR_PATH: str = ""
    WORK_SPACE_DIR: str = ""
    RUN_ECC_END_FLAG_FILE_PATH: str = ""
    TRIAL_END_FLAG_FILE_PATH: str = ""
    DAO_END_FLAG_FILE_PATH: str = ""
