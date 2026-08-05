"""속도 측정용 15x145 z=256 irregular QC-LDPC 생성 (사용자 지정 분포, 2026-08-03).

목표 분포: Dv11:42 / Dv4:20 / Dv3:69 / Dv2:14 (합 145), rate = 130/145 ≈ 0.897
dual-diagonal parity(M=15)가 dv2×14(bidiagonal) + dv3×1(anchor)을 공급하므로
정보부 130 col = dv11×42 + dv4×20 + dv3×68.

컬럼 배치는 원본 H-matrix 대응: 정보부 degree 내림차순 (Dv11 앞쪽) + parity 뒤쪽.
column-wise 스케줄이 원본처럼 매 iteration을 고degree부터 복호하게 된다.
PEG 생성은 품질 권장대로 오름차순으로 하고, 생성 후 컬럼 순열로 재배열한다
(순열은 그래프 등가 — 성능 불변, 복호 순서만 변경).

FER 선별 없이 seed 1개로 생성 — 속도 측정은 부호 품질과 무관 (E/z/N_b만 결정 요인).
실행: python _pm/tasks/260803_iteration당속도측정/gen_code_15x145.py
출력: 같은 폴더의 irregular_15x145_z256.qc
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

from ldpc_light.pcm import QCCode                          # noqa: E402
from ldpc_light.tools.gen_example_code import build_code   # noqa: E402

M, N, Z = 15, 145, 256
N_DV3, N_DV4, N_DV11 = 68, 20, 42
INFO_DEGREES = [3] * N_DV3 + [4] * N_DV4 + [11] * N_DV11   # 오름차순 (PEG 처리 순서)
SEED = 20260803
OUT = os.path.join(HERE, "irregular_15x145_z256.qc")


def main():
    code = build_code(Z, M, N, INFO_DEGREES, SEED)
    # 정보부 재배열: [dv3, dv4, dv11] → [dv11, dv4, dv3]. parity(130~144)는 그대로.
    K_b = N - M
    perm = (list(range(N_DV3 + N_DV4, K_b))          # dv11 42개
            + list(range(N_DV3, N_DV3 + N_DV4))      # dv4 20개
            + list(range(0, N_DV3))                  # dv3 68개
            + list(range(K_b, N)))                   # parity 15개
    code = QCCode(code.base[:, perm], Z)
    code.save(OUT)
    print(code.summary())
    print(f"  col_deg 앞 5개: {code.col_deg[:5].tolist()} (Dv11 선두 확인)")
    print(f"  lifted 4-cycles: {code.count_cycles4()}")
    print(f"saved: {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
