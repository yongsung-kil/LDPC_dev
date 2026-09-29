"""th가 사실상 클리핑으로 작용하는지 정량화.

V2C raw = ch + (다른 dv-1개 edge의 C2V 합). |raw| 최댓값 = ch + (dv-1)*7.
캐스케이드: |raw| >= th1 -> 7, >= th2 -> 5, >= th3 -> 3, else 1.
th_k > |raw| 최댓값이면 그 레벨은 도달 불가 -> V2C 실효 상한이 아래 레벨로 내려간다.

CN 출력: min1 = 연결 VN들의 V2C 최솟값. 각 VN의 V2C가 자기 dv의 실효 상한을 넘지
못하므로, CN row block별로 연결 column block들의 실효 상한 중 가장 작은 값이 min1
상한(실효 P)이다. min2 상한은 th와 무관하게 항상 EDGE_MAX다: 본체 _cnu_update가
min1 교체 시 min2를 RESET(= EDGE_MAX)으로 올리므로 (decoder.py 213~217행) 연결 VN
전부가 5 이하를 보내도 min2는 7이 된다. 따라서 실효 Q = EDGE_MAX 고정.
|raw| 최댓값은 ch >= 0일 때 ch + (dv-1)*EDGE_MAX이고, 일반형은 |ch| + (dv-1)*EDGE_MAX.
어느 dv의 실효 상한이 내려가도 다른 dv의 max_raw 안 (dv-1)*EDGE_MAX 항은 min1, min2가
EDGE_MAX 이하라는 사실에서 오므로 내려가지 않는다. 1회 통과가 곧 고정점이다.
"""
import sys
import numpy as np

sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix
from src.pcm import QCCode

llr = LLRMatrix.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt")
code = QCCode.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\H_matrix\matrix_sel_1.txt")
levels = [int(v) for v in llr.edge_mag]           # [7,5,3,1]
EDGE_MAX = levels[0]
dvs = llr.dv_from.tolist()
col_dv = llr.col_dv_idx(code)                     # column block -> dv 구간 index
R = len(llr.row_csw)

# --- 1. CN row block별 연결 column block의 dv 분포 ---
print("=== H 연결 구조: CN row block별 연결 column block 수 (dv별) ===")
conn = np.zeros((code.M_b, llr.num_dv), np.int64)
for e in range(code.E):
    conn[code.edge_row[e], col_dv[code.edge_col[e]]] += 1
print("dv:", dvs)
for i in range(code.M_b):
    print(f"  row block {i:2d}: {conn[i].tolist()}  (합 {conn[i].sum()})")
print("  dv별 최소 연결 수:", conn.min(axis=0).tolist())
print()

# --- 2. row×dv별 V2C 실효 상한 ---
def v2c_cap(ch, th, dv):
    max_raw = abs(ch) + (dv - 1) * EDGE_MAX
    for k, t in enumerate(th):              # th1..th3 -> level 7,5,3
        if max_raw >= t:
            return levels[k], max_raw
    return levels[-1], max_raw

print("=== row×dv별 V2C 실효 상한 (도달 가능한 최대 레벨) ===")
print("row  iter        csw | " + " | ".join(f"dv{d:<2d} cap(max_raw,th1)" for d in dvs) + " | CN 실효 (P,Q) 범위")
cap_table = np.zeros((R, llr.num_dv), np.int64)
pq_rows = []
for r in range(R):
    cells = []
    for k, d in enumerate(dvs):
        ch = int(llr.row_ch[r, k, 0]); th = [int(t) for t in llr.row_th[r, k]]
        cap, max_raw = v2c_cap(ch, th, d)
        cap_table[r, k] = cap
        cells.append(f"{cap} ({max_raw:2d},{th[0]:2d})")
    # CN row block별 실효 (P,Q). Q는 RESET 승격 때문에 항상 EDGE_MAX
    pq = []
    for i in range(code.M_b):
        caps = []
        for k in range(llr.num_dv):
            caps += [cap_table[r, k]] * int(conn[i, k])
        pq.append((min(caps), EDGE_MAX))
    p_set = sorted(set(p for p, _ in pq)); q_set = sorted(set(q for _, q in pq))
    pq_rows.append(pq)
    print(f"{r + 1:3d}  {llr.row_iter[r].tolist()!s:10s} {int(llr.row_csw[r]):5d} | " + " | ".join(cells)
          + f" | P{p_set} Q{q_set}")

print()
print("=== 요약: dv별로 V2C 상한이 7 미만인 row 수 (57 row 중) ===")
for k, d in enumerate(dvs):
    below = int(np.sum(cap_table[:, k] < EDGE_MAX))
    print(f"  dv{d:<2d}: 상한<7 인 row {below:2d}개, 상한 분포 " + str({int(v): int(c) for v, c in zip(*np.unique(cap_table[:, k], return_counts=True))}))
print()
print("=== 요약: row별 CN 실효 (P,Q) (전 CN row block 동일하면 한 값) ===")
from collections import Counter
cnt = Counter()
for r in range(R):
    key = tuple(sorted(set(pq_rows[r])))
    cnt[key] += 1
for key, n in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"  {key}: {n} row")
