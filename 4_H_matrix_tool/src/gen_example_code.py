"""예시 QC-LDPC 생성: PEG(정보부) + dual-diagonal(패리티부) + greedy lifting.

실물과 동일 치수 (README 확정 결정 기록): base M_b=18 × N_b=147, z=256, rate≈0.878.
패리티부 구조 (dual-diagonal, 802.16e 계열):
  - anchor column (첫 패리티 col): row {0, M/2, M-1}, shift {s0, 0, s0} (재귀 인코딩 가능 조건)
  - 나머지 M-1개: bidiagonal로 col P_k가 row {k-1, k}에 shift 0

실행: python 4_H_matrix_tool/src/gen_example_code.py [출력경로]
"""
import os
import sys

import numpy as np

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_root = TOOL_ROOT
while not os.path.isdir(os.path.join(_root, "2_LDPC_base", "src")):
    _parent = os.path.dirname(_root)
    if _parent == _root:
        raise SystemExit("상위 폴더에서 2_LDPC_base/src를 찾지 못함 "
                         "(이 파일은 LDPC_dev 하위에 있어야 함)")
    _root = _parent
_base_root = os.path.join(_root, "2_LDPC_base")
if _base_root not in sys.path:
    sys.path.insert(0, _base_root)

from src.pcm import QCCode

from peg import peg_base
from lifting import lift_greedy


def build_code(z, M, N, info_col_degrees, seed):
    """dual-diagonal parity + PEG 정보부 QC-LDPC 생성 (임의 degree 분포).

    info_col_degrees: 길이 N-M. PEG 품질을 위해 오름차순 배치 권장 (낮은 degree 먼저).
    """
    K = N - M
    assert len(info_col_degrees) == K
    assert max(info_col_degrees) <= M, "base column degree는 M_b를 넘을 수 없음"
    rng = np.random.default_rng(seed)

    # 패리티부 고정 edge (dual-diagonal)
    fixed_edges = [(0, K), (M // 2, K), (M - 1, K)]
    fixed_shifts = {}
    s0 = int(rng.integers(1, z))
    fixed_shifts[(0, K)] = s0
    fixed_shifts[(M // 2, K)] = 0
    fixed_shifts[(M - 1, K)] = s0
    for k in range(1, M):
        for i in (k - 1, k):
            fixed_edges.append((i, K + k))
            fixed_shifts[(i, K + k)] = 0

    col_degrees = list(info_col_degrees) + [0] * M   # 패리티부는 fixed edge로만 연결
    conn = peg_base(M, col_degrees, rng, fixed_edges=fixed_edges)
    base = lift_greedy(conn, z, rng, fixed_shifts=fixed_shifts)
    return QCCode(base, z)


def build_example(z=256, M=18, N=147, dv_info=4, seed=20260730):
    return build_code(z, M, N, [dv_info] * (N - M), seed)


def main():
    default_out = os.path.join(TOOL_ROOT, "out", "example_18x147_z256.qc")
    out = sys.argv[1] if len(sys.argv) > 1 else default_out
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    code = build_example()
    code.save(out)
    print(code.summary())
    print(f"  lifted 4-cycles: {code.count_cycles4()}")
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
