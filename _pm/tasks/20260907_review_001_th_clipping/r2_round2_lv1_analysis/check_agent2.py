"""Round 2 에이전트 2 검증: 수치 재현, row 선택 대표성, 반전 조건, 사전 지표.

디코딩 시뮬레이션은 하지 않는다 (파일 로드와 산술만).
"""
import sys

import numpy as np

sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix, edge_quantization_levels
from src.pcm import QCCode

LLR = r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt"
H = r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\H_matrix\matrix_sel_1.txt"

llr = LLRMatrix.load(LLR)
code = QCCode.load(H)
dvs = llr.dv_from.tolist()
R = len(llr.row_csw)
col_dv = llr.col_dv_idx(code)

print("### 1. row 선택 창 (row_index 정방향 덮어쓰기 결과)")
print("group | rows | iter 범위 | 각 row가 선택되는 prev_csw 구간")
for g, (rs, re_) in enumerate(llr.group_slices):
    it = (int(llr.row_iter[rs, 0]), int(llr.row_iter[re_ - 1, 1]))
    th = [int(llr.row_csw[r]) for r in range(rs, re_)]
    wins = []
    for k, r in enumerate(range(rs, re_)):
        if k == 0:
            lo = th[1] if len(th) > 1 else -1
            wins.append(f"row{r + 1}: csw > {lo}")
        else:
            nxt = th[k + 1] if k + 1 < len(th) else None
            wins.append(f"row{r + 1}: {'' if nxt is None else str(nxt) + ' < '}csw <= {th[k]}")
    print(f"  g{g + 1} | {rs + 1}~{re_} | {it} | " + " ; ".join(wins))
    if sorted(th[1:], reverse=True) != th[1:]:
        print("    !! 임계값이 내림차순이 아님 (정방향 덮어쓰기 전제 깨짐)")

print()
print("### 2. iteration 1 진입 시 prev_csw = |syndrome| 기댓값 (해석식, 디코딩 없음)")
row_deg = np.array([int(v) for v in code.row_deg])
M = code.M_b * code.z
N = code.N
for E in (420, 400, 390, 380, 370):
    p = 2.0 * E / N
    odd = np.mean(0.5 * (1.0 - (1.0 - p) ** row_deg))
    print(f"  E={E}: 체크당 홀수오류 확률 {odd:.4f} → 기대 CSW {odd * M:8.0f} (전체 체크 {M})")
print("  그룹별 최상단 임계값:", [int(llr.row_csw[rs + 1]) if re_ - rs > 1 else None
                                 for rs, re_ in llr.group_slices])

print()
print("### 3. 반전 불능 조건의 경계 (_vn_decide: sum_t <= 0 이면 반전)")
print("  반전 조건 ch - max_ext <= 0  →  반전 가능 iff max_ext >= ch")
print("  즉 반전 불능은 max_ext < ch. flip_check.py는 max_ext <= ch 로 센다")
pairs = [(7, 7), (5, 7), (3, 7), (3, 5), (2, 5), (2, 3), (1, 3)]
for formula_name, f in (("Q+(dv-1)P", lambda P, Q, d: Q + (d - 1) * P),
                        ("dv*P", lambda P, Q, d: d * P),
                        ("dv*Q", lambda P, Q, d: d * Q)):
    print(f"  -- max_ext = {formula_name}")
    for P, Q in pairs:
        cells = []
        for k, d in enumerate(dvs):
            ch = llr.row_ch[:, k, 0]
            m = f(P, Q, d)
            strict = int(np.sum(m < ch))          # 올바른 반전 불능
            loose = int(np.sum(m <= ch))          # flip_check.py 방식
            cells.append(f"dv{d}: {strict}/{loose}(m={m})")
        print(f"     ({P},{Q}) " + " | ".join(cells))
print("  (값 = 엄밀 기준 / flip_check.py 기준 반전 불능 row 수)")

print()
print("### 4. 001 관측을 세 식이 맞히는가 (LLR_MATRIX_HD_1 dv4 ch=10, 비율복원 dv4 ch=16)")
obs = [("HD_1 dv4 ch10", 4, 10, [((7, 7), "0.484 생존"), ((5, 7), "0.516 생존"),
                                 ((5, 5), "0.938 생존"), ((3, 7), "0.859 생존"),
                                 ((3, 5), "0.938 생존"), ((3, 3), "1.00 사망"),
                                 ((2, 5), "0.969 생존"), ((2, 3), "1.00 사망"),
                                 ((1, 3), "1.00 사망"), ((1, 1), "1.00 사망")]),
       ("비율복원 dv4 ch16", 4, 16, [((15, 15), "0.00 생존"), ((8, 15), "?"), ((4, 8), "1.00 사망")])]
for name, d, ch, rows in obs:
    print(f"  -- {name}")
    for (P, Q), got in rows:
        a = Q + (d - 1) * P
        b = d * P
        c = d * Q
        def verdict(m):
            return "사망예측" if m < ch else ("동률" if m == ch else "생존예측")
        print(f"     ({P},{Q}) 관측 {got:12s} | Q+(dv-1)P={a:3d} {verdict(a):5s}"
              f" | dv*P={b:3d} {verdict(b):5s} | dv*Q={c:3d} {verdict(c):5s}")

print()
print("### 5. 정보 구간(앞 N_b-M_b개 column block)의 dv 분포 (genie 판정 범위)")
n_info = code.N_b - code.M_b
info_counts = np.bincount(col_dv[:n_info], minlength=llr.num_dv)
par_counts = np.bincount(col_dv[n_info:], minlength=llr.num_dv)
print(f"  정보 column block {n_info}개: " + ", ".join(f"dv{d}:{int(c)}" for d, c in zip(dvs, info_counts)))
print(f"  패리티 column block {code.N_b - n_info}개: " + ", ".join(f"dv{d}:{int(c)}" for d, c in zip(dvs, par_counts)))

print()
print("### 6. 사전 지표 ch/(edge상한*dv): 대상 파일과 001 세 환경을 같은 축에 놓기")
print("  대상 파일 (edge 레벨 {7,5,3,1}, 최소 레벨 1)")
for k, d in enumerate(dvs):
    ch = llr.row_ch[:, k, 0]
    r = ch / (7.0 * d)
    print(f"    dv{d:<2d} (col block {int(np.sum(col_dv == k)):3d}, 정보구간 {int(info_counts[k]):3d}): "
          f"min/중앙/max = {r.min():.2f}/{np.median(r):.2f}/{r.max():.2f}")
mag15, th15 = edge_quantization_levels(3, 15)
print(f"  001 상한 여유/비율 복원 환경 edge 레벨 {mag15}, th {th15} (최소 레벨 {mag15[-1]})")
for ch_u, env in ((8, "상한 여유"), (16, "비율 복원")):
    print(f"    {env} (전 dv 공통 ch={ch_u}): " +
          ", ".join(f"dv{d}: {ch_u / (15.0 * d):.2f}" for d in (2, 3, 4, 11)))
llr1 = LLRMatrix.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_1.txt")
code1 = QCCode.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\H_matrix\example_18x147_z256.qc")
cd1 = llr1.col_dv_idx(code1)
n_info1 = code1.N_b - code1.M_b
ic1 = np.bincount(cd1[:n_info1], minlength=llr1.num_dv)
print("    LLR_MATRIX_HD_1 환경 (edge 레벨 {7,5,3,1}): " +
      ", ".join(f"dv{d}: {float(llr1.row_ch[:, k, 0].max()) / (7.0 * d):.2f}"
                f"(정보구간 col {int(ic1[k])})" for k, d in enumerate(llr1.dv_from.tolist())))

print()
print("### 7. row 균등 취급 대 그룹 iteration 폭 가중")
span = [int(llr.row_iter[re_ - 1, 1]) - int(llr.row_iter[rs, 0]) + 1
        for rs, re_ in llr.group_slices]
print("  그룹 iteration 폭:", span, " 그룹 row 수:", llr.group_rows)
w_row = np.ones(R)
w_iter = np.zeros(R)
for g, (rs, re_) in enumerate(llr.group_slices):
    w_iter[rs:re_] = span[g] / (re_ - rs)
for k, d in enumerate(dvs):
    ch = llr.row_ch[:, k, 0]
    r = np.sort(ch / (7.0 * d))
    o = np.argsort(ch / (7.0 * d))
    def wmed(w):
        ww = w[o]
        c = np.cumsum(ww) / ww.sum()
        return float(r[np.searchsorted(c, 0.5)])
    print(f"    dv{d:<2d}: row 균등 중앙 {wmed(w_row):.2f}, 그룹 iteration 폭 가중 중앙 {wmed(w_iter):.2f}")

print()
print("### 8. min2 = RESET 승격이 실효 Q 상한 모델에 미치는 영향")
print(f"  _cnu_update: min1 교체 시 min2 = RESET = {float(llr.edge_mag[0])}")
print("  → min2 상한은 연결 VN의 둘째 실효 상한이 아니라 항상 RESET까지 올라간다")
print("  → th_as_clip.py의 (P,Q) 계산에서 Q는 상한이 아니다 (row2, row57의 Q=5 주장 무효)")
