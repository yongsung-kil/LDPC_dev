"""QC lifting — base graph의 각 edge에 circulant shift 부여.

4-cycle 조건: base 4-cycle (i1,j1)-(i1,j2)-(i2,j2)-(i2,j1)에서
  s(i1,j1) - s(i2,j1) + s(i2,j2) - s(i1,j2) ≡ 0 (mod z) 이면 lifted 4-cycle 발생.
greedy로 edge마다 금지 shift 집합을 피해서 선택한다 (불가능하면 위반 최소 shift).
"""
import numpy as np


def lift_greedy(conn, z, rng, fixed_shifts=None):
    """conn: (M, N) bool. fixed_shifts: {(i, j): s} 고정 shift (dual-diagonal 등).

    반환: base matrix (M, N) int32 (-1 = no edge), 잔여 4-cycle 수는 QCCode.count_cycles4로 확인.
    """
    M, N = conn.shape
    base = np.full((M, N), -1, np.int32)
    fixed_shifts = fixed_shifts or {}
    for (i, j), s in fixed_shifts.items():
        assert conn[i, j], f"fixed shift on non-edge ({i},{j})"
        base[i, j] = s % z

    edges = [(i, j) for j in range(N) for i in range(M)
             if conn[i, j] and (i, j) not in fixed_shifts]
    order = rng.permutation(len(edges))

    rows_of_col = [np.flatnonzero(conn[:, j]) for j in range(N)]
    for k in order:
        i1, j1 = edges[k]
        forbidden = set()
        # 이미 배정된 edge들과 이루는 base 4-cycle에서 금지 shift 도출
        for i2 in rows_of_col[j1]:
            if i2 == i1 or base[i2, j1] < 0:
                continue
            both = np.flatnonzero(conn[i1] & conn[i2] & (base[i1] >= 0) & (base[i2] >= 0))
            for j2 in both:
                if j2 == j1:
                    continue
                # s(i1,j1) ≡ s(i2,j1) - s(i2,j2) + s(i1,j2) (mod z) 금지
                forbidden.add(int(base[i2, j1] - base[i2, j2] + base[i1, j2]) % z)
        allowed = [s for s in range(z) if s not in forbidden]
        if allowed:
            base[i1, j1] = int(rng.choice(allowed))
        else:
            # 전부 금지면 위반 수 최소인 shift (희귀 케이스)
            counts = np.zeros(z, np.int64)
            for s in forbidden:
                counts[s] += 1
            base[i1, j1] = int(np.argmin(counts))
    return base
