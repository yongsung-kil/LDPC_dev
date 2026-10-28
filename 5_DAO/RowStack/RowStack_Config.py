"""RowStack(uncor 하나씩 row를 쌓아 고치는 LLR matrix 탐색기)의 경로와 설정.

설정값의 뜻은 5_DAO/_pm/tasks/20261021_uncor별_row누적_탐색/ 의 탐색 규칙 2판 3.9절(탐색)과 1판 4.8절(모으기)에 있다.
실행은 run_RowStack_mpi.bat 또는 mpiexec -n N python RowStack_Main.py 이고, 값은 아래 CONFIG 자리에서 고친다.
이 모듈을 import하면 2_LDPC_base와 5_DAO/SRC가 sys.path에 들어가 src.*와 DAO_Constants를 import할 수 있다.
"""
import os
import sys
from dataclasses import dataclass
from typing import Optional

ROWSTACK_DIR = os.path.dirname(os.path.abspath(__file__))
LDPC_DEV_ROOT = os.path.dirname(os.path.dirname(ROWSTACK_DIR))
BASE_DIR = os.path.join(LDPC_DEV_ROOT, "2_LDPC_base")
BASE_INPUT_H_DIR = os.path.join(BASE_DIR, "Input", "H_matrix")
BASE_INPUT_LLR_DIR = os.path.join(BASE_DIR, "Input", "LLR")
DAO_SRC_DIR = os.path.join(LDPC_DEV_ROOT, "5_DAO", "SRC")
DEFAULT_OUTPUT_ROOT = os.path.join(LDPC_DEV_ROOT, "5_DAO", "Output_RowStack")


def add_import_paths():
    """2_LDPC_base(src 패키지)와 5_DAO/SRC(DAO_Constants)를 sys.path 앞에 넣는다."""
    for path in (DAO_SRC_DIR, BASE_DIR):
        if path not in sys.path:
            sys.path.insert(0, path)


add_import_paths()


@dataclass
class RowStackConfig:
    """실행 설정."""
    # 입력
    H_MATRIX_FILE: str = "example_18x147_z256.qc"          # 2_LDPC_base/Input/H_matrix/ 아래 파일 이름
    INITIAL_LLR_MATRIX_FILE: str = "LLR_MATRIX_HD_1.txt"   # 2_LDPC_base/Input/LLR/ 아래. 이름의 HD/2SD/3SD가 복호 모드
    CHANNEL_TYPE: str = "fixed_error"                      # fixed_error, rber, strong_error
    CHANNEL_POINT: float = 400                             # fixed_error와 strong_error는 프레임당 에러 bit 수, rber는 RBER
    STRONG_SCR: float = 0.94                               # strong_error일 때만 쓴다
    STRONG_SER: float = 0.23
    # uncor 모으기
    NUM_UNCORS_TO_COLLECT: int = 100                       # 모을 uncor 수 K
    COLLECT_MAX_FRAMES: int = 1000000                      # 모으기에서 돌릴 프레임 상한 (rank 전체 합)
    COLLECT_FRAMES_PER_BATCH: int = 64
    UNCOR_SEED_DIR: Optional[str] = None                   # 지난 실행의 collected_uncors 폴더. 주면 모으기를 건너뛰고 읽는다
    # 탐색 (탐색 규칙 2판)
    MAX_ROWS: int = 6                                      # row 수 상한 (stage 수 상한)
    NUM_MATRICES_TO_KEEP: int = 3                          # t. round마다 들고 가는 매트릭스 후보 수 (gen과 mut 공통)
    CANDIDATES_PER_RANK_PER_BLOCK: int = 20                # n. gen 블록에서 코어마다 만드는 후보 row 수
    MAX_GEN_BLOCKS_PER_ROW: int = 3                        # k_gen. 개선이 없을 때 gen 블록을 다시 도는 상한
    MUTANTS_PER_RANK_PER_BLOCK: int = 10                   # m. mut 블록에서 코어마다 만드는 변이 수 (0이면 변이 없음)
    MAX_MUT_BLOCKS_PER_ROW: int = 2                        # k_mut. 개선이 없을 때 mut 블록을 다시 도는 상한
    MUTATION_NUM_ELEMENTS: int = 3                         # 변이에서 바꾸는 CH/TH 자리 수 (매트릭스 전체에서 고름)
    MUTATION_RANGE: int = 5                                # 변이 폭 (±)
    INIT_DECODING_ITERATION: int = 30                      # 첫 row의 복호 iteration 수
    STEP_ITERATION_PER_ROW: int = 5                        # row가 하나 붙을 때마다 더하는 iteration 수
    MAX_DECODING_ITERATION: int = 50                       # 복호 iteration 상한 (HW 제약)
    CSW_MARGIN_ABOVE_MIN: int = 32                         # 새 row 문턱을 궤적의 최소 CSW보다 얼마나 위에 두는지 (CSW 단위)
    MAX_MATRIX_ATTEMPTS_PER_UNCOR: int = 1                 # 큰 반복 (후보가 모두 끝나면 빈 매트릭스부터 다시 시작하는 횟수)
    TRY_FOUND_MATRICES_FIRST: bool = True                  # 새 uncor를 먼저 찾은 매트릭스들로 복호해 보는지
    RANDOM_SEED: int = 0                                   # 후보 생성 난수의 뿌리
    # 출력
    SAVE_TESTED_MATRICES: bool = True                      # 시험한 후보 매트릭스를 tested_matrices/rank_N/에 파일로 남기는지
    OUTPUT_ROOT: str = DEFAULT_OUTPUT_ROOT

    def channel_extra(self) -> dict:
        """채널 함수의 추가 인자. strong_error만 scr, ser를 쓴다."""
        if self.CHANNEL_TYPE == "strong_error":
            return {"scr": self.STRONG_SCR, "ser": self.STRONG_SER}
        return {}

    def h_matrix_path(self) -> str:
        return os.path.join(BASE_INPUT_H_DIR, self.H_MATRIX_FILE)

    def initial_llr_matrix_path(self) -> str:
        return os.path.join(BASE_INPUT_LLR_DIR, self.INITIAL_LLR_MATRIX_FILE)

    def iteration_budget(self, num_rows: int) -> int:
        """row가 num_rows개인 매트릭스의 복호 iteration 수 (탐색 규칙 2판 3.5절)."""
        return min(self.MAX_DECODING_ITERATION,
                   self.INIT_DECODING_ITERATION + (int(num_rows) - 1) * self.STEP_ITERATION_PER_ROW)

    def validate(self) -> None:
        """값의 범위를 검사한다. 어기면 ValueError."""
        from src import channel as chan
        if self.CHANNEL_TYPE not in chan.CHANNELS:
            raise ValueError(f"CHANNEL_TYPE={self.CHANNEL_TYPE!r}: {sorted(chan.CHANNELS)} 가운데 하나여야 함")
        if not self.CHANNEL_POINT > 0:
            raise ValueError(f"CHANNEL_POINT={self.CHANNEL_POINT!r}: 0보다 커야 함")
        at_least_one = ("NUM_UNCORS_TO_COLLECT", "COLLECT_MAX_FRAMES", "COLLECT_FRAMES_PER_BATCH", "MAX_ROWS",
                        "NUM_MATRICES_TO_KEEP", "CANDIDATES_PER_RANK_PER_BLOCK", "MAX_GEN_BLOCKS_PER_ROW",
                        "MAX_MUT_BLOCKS_PER_ROW", "MUTATION_NUM_ELEMENTS", "MUTATION_RANGE",
                        "INIT_DECODING_ITERATION", "MAX_DECODING_ITERATION", "MAX_MATRIX_ATTEMPTS_PER_UNCOR")
        for name in at_least_one:
            self._require_int(name, minimum=1)
        for name in ("MUTANTS_PER_RANK_PER_BLOCK", "STEP_ITERATION_PER_ROW", "CSW_MARGIN_ABOVE_MIN"):
            self._require_int(name, minimum=0)
        if self.INIT_DECODING_ITERATION > self.MAX_DECODING_ITERATION:
            raise ValueError(f"INIT_DECODING_ITERATION={self.INIT_DECODING_ITERATION}은 "
                             f"MAX_DECODING_ITERATION={self.MAX_DECODING_ITERATION} 이하여야 함")

    def _require_int(self, name: str, minimum: int) -> None:
        value = getattr(self, name)
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name}={value!r}: {minimum} 이상의 정수여야 함")


CONFIG = RowStackConfig()   # 실행 설정은 여기서 고친다
