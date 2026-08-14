#!/usr/bin/env python3
"""
Mock ECC Simulator
==================
Prime_ECC_3.0.exe의 출력을 모사하는 도구입니다.
회사 외부에서 DAO 시스템의 동작을 검증할 때 사용합니다.

사용법:
    python Mock_ECC.py <args...>

    또는 PyInstaller로 exe 빌드 후:
    Mock_ECC.exe <args...>

인자 (ECC_VER 3.0 기준):
    1: matrix_sel
    2: init_n
    3: ch_type (1=RBER, 2=FIXED_ERROR, 3=STRONG_ERROR)
    4: RBER
    5: num_fixed_errs
    6: fixed_SCRs
    7: fixed_SERs
    8: fixed_erasure_ratios
    9: fn (파일 수)
    10: max_num_test (테스트 수)
    11: seed_mode
    12: rank (프로세스 번호)
    13: mode_all_one_cw
    14: CRC_Option_F_P
    15: mode_iter
    16: mode_scenario
    17: matrix_idx
    18: enable_print_CSW_log

출력:
    - result_4KB_S_{scenario}_H_{matrix_sel}_CH_{ch_type}_E...txt
    - log_CSW_{rank}.txt (enable_print_CSW_log=1인 경우)
"""

import sys
import os
import random
import numpy as np
from typing import Optional


class MockECCConfig:
    """Mock ECC 시뮬레이션 설정"""
    # FER 시뮬레이션 범위
    BASE_FER_MIN = 0.001
    BASE_FER_MAX = 0.1

    # Iteration별 FER 감소율 (더 나중 iteration일수록 FER이 낮아짐)
    ITERATION_DECAY_RATE = 0.85

    # 랜덤 노이즈 범위
    NOISE_RANGE = 0.2

    # CSW 범위
    MIN_CSW = 8
    MAX_CSW = 1024


class LLRMatrixReader:
    """LLR 매트릭스 파일을 읽어 max_iteration을 추출"""

    def __init__(self, matrix_path: str):
        self.matrix_path = matrix_path
        self.max_iteration = 50  # 기본값
        self.num_groups = 1

        if os.path.exists(matrix_path):
            self._read_matrix()

    def _read_matrix(self):
        """LLR 매트릭스 파일에서 필요한 정보 추출"""
        try:
            with open(self.matrix_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

            parsed = [list(map(int, line.split())) for line in lines]

            idx = 0
            num_parameter_each_set = parsed[idx][0]; idx += 1
            num_dv = parsed[idx][0]; idx += 1
            idx += 2  # dv_from, dv_to
            num_group = parsed[idx][0]; idx += 1
            num_row_each_group = parsed[idx]; idx += 1
            idx += 1  # type_each_group

            num_restart = parsed[idx][0]; idx += 1
            if num_restart > 0:
                idx += 1  # restart_iter

            idx += 2  # max_value, min_value

            # 마지막 그룹의 마지막 행에서 iter_end 추출
            total_rows = sum(num_row_each_group)
            matrix_rows = parsed[idx:idx + total_rows]

            if matrix_rows:
                last_row = matrix_rows[-1]
                # iter_end는 뒤에서 두 번째 값 (row[-2])
                self.max_iteration = last_row[-2]

            self.num_groups = num_group

        except Exception as e:
            print(f"[Mock_ECC] Warning: Could not read LLR matrix: {e}", file=sys.stderr)
            print(f"[Mock_ECC] Using default max_iteration={self.max_iteration}", file=sys.stderr)


class MockECC:
    """ECC 시뮬레이터 Mock 클래스"""

    def __init__(self, args: list):
        self.parse_args(args)
        self.result_lines = []
        self.csw_lines = []

    def parse_args(self, args: list):
        """명령줄 인자 파싱"""
        if len(args) < 18:
            raise ValueError(f"Expected 18 arguments, got {len(args)}")

        idx = 0
        self.matrix_sel = int(args[idx]); idx += 1           # 1
        self.init_n = int(args[idx]); idx += 1               # 2
        self.ch_type = int(args[idx]); idx += 1              # 3
        self.RBER = float(args[idx]); idx += 1               # 4
        self.num_fixed_errs = int(args[idx]); idx += 1       # 5
        self.fixed_SCRs = float(args[idx]); idx += 1         # 6
        self.fixed_SERs = float(args[idx]); idx += 1         # 7
        self.fixed_erasure_ratios = float(args[idx]); idx += 1  # 8
        self.fn = int(args[idx]); idx += 1                   # 9
        self.max_num_test = int(args[idx]); idx += 1         # 10
        self.seed_mode = int(args[idx]); idx += 1            # 11
        self.rank = int(args[idx]); idx += 1                 # 12
        self.mode_all_one_cw = int(args[idx]); idx += 1      # 13
        self.CRC_Option_F_P = int(args[idx]); idx += 1       # 14
        self.mode_iter = int(args[idx]); idx += 1            # 15
        self.mode_scenario = int(args[idx]); idx += 1        # 16
        self.matrix_idx = int(args[idx]); idx += 1           # 17
        self.enable_print_CSW_log = int(args[idx]); idx += 1 # 18

        # 시드 설정 (재현 가능한 결과를 위해)
        random.seed(self.rank * 1000 + self.matrix_idx)
        np.random.seed(self.rank * 1000 + self.matrix_idx)

    def get_result_file_name(self) -> str:
        """결과 파일 이름 생성"""
        result_file_name = f"result_4KB_S_{self.mode_scenario}_H_{self.matrix_sel}_CH_{self.ch_type}_E"

        if self.ch_type == 1:
            result_file_name += f'{self.RBER:.2e}_'
        elif self.ch_type == 2:
            result_file_name += f'{self.num_fixed_errs:d}_'
        elif self.ch_type == 3:
            result_file_name += f'{self.num_fixed_errs:d}_SC_{self.fixed_SCRs:.2f}_SE_{self.fixed_SERs:.2f}_'

        result_file_name += f'init_n_{self.init_n}_seed_{self.rank}.txt'
        return result_file_name

    def get_csw_log_file_name(self) -> str:
        """CSW 로그 파일 이름"""
        return f"log_CSW_{self.rank}.txt"

    def get_llr_matrix_path(self) -> str:
        """LLR 매트릭스 파일 경로"""
        return f"LLR_MATRIX_{self.matrix_idx}.txt"

    def generate_mock_results(self, max_iteration: int):
        """Mock 테스트 결과 생성"""
        num_tests = self.max_num_test * self.fn

        # 기본 FER 계산 (num_fixed_errs에 비례)
        if self.ch_type == 1:
            base_fer = self.RBER * 10
        elif self.ch_type == 2:
            base_fer = min(0.5, self.num_fixed_errs / 1000.0)
        else:
            base_fer = min(0.5, self.num_fixed_errs / 1000.0 * (1 - self.fixed_SCRs))

        base_fer = max(MockECCConfig.BASE_FER_MIN, min(MockECCConfig.BASE_FER_MAX, base_fer))

        # 랜덤 노이즈 추가
        noise = random.uniform(-MockECCConfig.NOISE_RANGE, MockECCConfig.NOISE_RANGE)
        base_fer = base_fer * (1 + noise)

        # 에러 수 계산
        num_errors = max(1, int(num_tests * base_fer))

        # 평균 iteration 계산
        avg_iteration = random.uniform(max_iteration * 0.3, max_iteration * 0.7)

        # Iteration별 FER 생성 (점점 감소)
        fer_per_iter = []
        cumulative_fer = base_fer
        for i in range(max_iteration):
            # 각 iteration에서의 에러율 (누적 감소)
            iter_fer = cumulative_fer * (MockECCConfig.ITERATION_DECAY_RATE ** i)
            iter_fer = max(0.0001, iter_fer)  # 최소값 보장
            fer_per_iter.append(iter_fer)

        # 결과 라인 생성
        # 형식: [prefix values] num_test num_error avg_iteration [fer_per_iter...] [suffix 3 values]
        if self.ch_type in (1, 2):
            prefix = f"{self.num_fixed_errs}"
        else:
            prefix = f"{self.num_fixed_errs}\t{self.fixed_SCRs:.2f}\t{self.fixed_SERs:.2f}"

        fer_str = "\t".join(f"{fer:.6f}" for fer in fer_per_iter)

        # 마지막 3개 값 (DAO 코드에서 무시됨, 형식 맞추기용)
        suffix = f"{base_fer:.6f}\t{avg_iteration:.2f}\t0"

        result_line = f"{prefix}\t{num_tests}\t{num_errors}\t{avg_iteration:.2f}\t{fer_str}\t{suffix}"
        self.result_lines.append(result_line)

        return num_errors

    def generate_mock_csw_log(self, num_errors: int, num_groups: int):
        """Mock CSW 로그 생성"""
        if not self.enable_print_CSW_log:
            return

        for _ in range(num_errors):
            # 각 에러에 대해 랜덤 CSW 값 생성
            csw_values = []
            for g in range(num_groups):
                csw = random.randint(MockECCConfig.MIN_CSW // 8, MockECCConfig.MAX_CSW // 8) * 8
                csw_values.append(str(csw))

            self.csw_lines.append("\t".join(csw_values))

    def run(self):
        """Mock ECC 시뮬레이션 실행"""
        # LLR 매트릭스에서 max_iteration 읽기
        llr_path = self.get_llr_matrix_path()
        llr_reader = LLRMatrixReader(llr_path)
        max_iteration = llr_reader.max_iteration
        num_groups = llr_reader.num_groups

        print(f"[Mock_ECC] Starting simulation...", file=sys.stderr)
        print(f"[Mock_ECC] matrix_idx={self.matrix_idx}, max_iteration={max_iteration}", file=sys.stderr)
        print(f"[Mock_ECC] ch_type={self.ch_type}, num_fixed_errs={self.num_fixed_errs}", file=sys.stderr)

        # Mock 결과 생성
        num_errors = self.generate_mock_results(max_iteration)
        self.generate_mock_csw_log(num_errors, num_groups)

        # 결과 파일 저장
        result_file = self.get_result_file_name()
        with open(result_file, 'w', encoding='utf-8') as f:
            for line in self.result_lines:
                f.write(line + '\n')
        print(f"[Mock_ECC] Result saved: {result_file}", file=sys.stderr)

        # CSW 로그 저장
        if self.enable_print_CSW_log and self.csw_lines:
            csw_file = self.get_csw_log_file_name()
            with open(csw_file, 'w', encoding='utf-8') as f:
                for line in self.csw_lines:
                    f.write(line + '\n')
            print(f"[Mock_ECC] CSW log saved: {csw_file}", file=sys.stderr)

        print(f"[Mock_ECC] Simulation completed.", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: No arguments provided.")
        print("Usage: python Mock_ECC.py <matrix_sel> <init_n> ... (18 arguments)")
        sys.exit(1)

    args = sys.argv[1:]

    try:
        mock_ecc = MockECC(args)
        mock_ecc.run()
    except Exception as e:
        print(f"[Mock_ECC] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
