"""RowStack(uncor 하나씩 row를 쌓아 고치는 LLR matrix 탐색기)의 경로와 설정.

설계와 설정값의 뜻은 5_DAO/_pm/tasks/20261021_uncor별_row누적_탐색/ (설계 문서 4.8절)에 있다.
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
    """실행 설정. 이름과 뜻은 설계 문서 4.8절과 같다."""
    H_MATRIX_FILE: str = "example_18x147_z256.qc"          # 2_LDPC_base/Input/H_matrix/ 아래 파일 이름
    INITIAL_LLR_MATRIX_FILE: str = "LLR_MATRIX_HD_1.txt"   # 2_LDPC_base/Input/LLR/ 아래. 이름의 HD/2SD/3SD가 복호 모드
    CHANNEL_TYPE: str = "fixed_error"                      # fixed_error, rber, strong_error
    CHANNEL_POINT: float = 400                             # fixed_error와 strong_error는 프레임당 에러 bit 수, rber는 RBER
    STRONG_SCR: float = 0.94                               # strong_error일 때만 쓴다
    STRONG_SER: float = 0.23
    NUM_UNCORS_TO_COLLECT: int = 100                       # 모을 uncor 수 K
    COLLECT_MAX_FRAMES: int = 1000000                    # 모으기에서 돌릴 프레임 상한 (rank 전체 합)
    COLLECT_FRAMES_PER_BATCH: int = 64
    UNCOR_SEED_DIR: Optional[str] = None                   # collected_uncors 폴더 경로. 주면 모으기를 건너뛰고 읽는다
    MAX_ITERATION_OF_STACKED_GROUP: int = 50               # 쌓는 그룹의 iteration 수
    CANDIDATES_PER_RANK_PER_STAGE: int = 20                # n, 작은 반복 (stage마다 rank당 후보 수)
    MAX_ROWS: int = 6                                      # R_max (stage 수 상한)
    MUTANTS_PER_RANK_PER_FIXED_ROW: int = 10               # m (rank마다 변이 후보 수. 0이면 변이 없음)
    MUTATION_NUM_ELEMENTS: int = 3                         # 변이에서 바꾸는 CH/TH 원소 수
    MUTATION_RANGE: int = 5                                # 변이 폭 (±)
    MAX_MATRIX_ATTEMPTS_PER_UNCOR: int = 1                 # 큰 반복 (R_max까지 실패하면 row 1부터 다시 시작하는 횟수)
    TRY_FOUND_MATRICES_FIRST: bool = True                  # 새 uncor를 먼저 찾은 매트릭스들로 복호해 보는지
    RANDOM_SEED: int = 0                                   # 후보 생성 난수의 뿌리
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

    def validate(self) -> None:
        """값의 범위를 검사한다. 어기면 ValueError."""
        from src import channel as chan
        if self.CHANNEL_TYPE not in chan.CHANNELS:
            raise ValueError(f"CHANNEL_TYPE={self.CHANNEL_TYPE!r}: {sorted(chan.CHANNELS)} 가운데 하나여야 함")
        if not self.CHANNEL_POINT > 0:
            raise ValueError(f"CHANNEL_POINT={self.CHANNEL_POINT!r}: 0보다 커야 함")
        at_least_one = ("NUM_UNCORS_TO_COLLECT", "COLLECT_MAX_FRAMES", "COLLECT_FRAMES_PER_BATCH",
                        "MAX_ITERATION_OF_STACKED_GROUP", "CANDIDATES_PER_RANK_PER_STAGE", "MAX_ROWS",
                        "MUTATION_NUM_ELEMENTS", "MUTATION_RANGE", "MAX_MATRIX_ATTEMPTS_PER_UNCOR")
        for name in at_least_one:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name}={value!r}: 1 이상의 정수여야 함")
        if isinstance(self.MUTANTS_PER_RANK_PER_FIXED_ROW, bool) or not isinstance(self.MUTANTS_PER_RANK_PER_FIXED_ROW, int) \
                or self.MUTANTS_PER_RANK_PER_FIXED_ROW < 0:
            raise ValueError(f"MUTANTS_PER_RANK_PER_FIXED_ROW={self.MUTANTS_PER_RANK_PER_FIXED_ROW!r}: 0 이상의 정수여야 함")


CONFIG = RowStackConfig()   # 실행 설정은 여기서 고친다
