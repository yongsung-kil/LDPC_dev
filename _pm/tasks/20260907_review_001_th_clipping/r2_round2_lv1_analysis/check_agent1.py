"""Round 2 에이전트 1 확인용: 본체 코드 규칙 대 스크립트 정적 모델 대조.

시뮬레이션은 돌리지 않는다. LLR 파일과 H-matrix 파일의 값 계산, 그리고
decoder._cnu_update 갱신 규칙 자체를 그대로 옮긴 상태기계 검사만 한다.
"""
import sys
import warnings
import numpy as np

sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix
from src.pcm import QCCode

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    llr = LLRMatrix.load(
        r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt")
code = QCCode.load(
    r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\H_matrix\matrix_sel_1.txt")

dvs = llr.dv_from.tolist()
col_dv = llr.col_dv_idx(code)
R = len(llr.row_csw)
EDGE_MAX = int(llr.edge_mag[0])

print("### 0. 로더 경고와 기본 사실")
print("  로더 경고:", [str(w.message)[:90] for w in caught] or "없음")
print("  th_nonmonotonic 플래그:", llr.th_nonmonotonic)
print("  restart_iters:", sorted(llr.restart_iters))
print("  max_iter:", llr.max_iter, " 그룹수:", len(llr.group_rows),
      " row수:", R, " edge_mag:", llr.edge_mag.tolist())
print("  group_type:", llr.group_type, " group_rows:", llr.group_rows)
print()

print("### A1-1. row_ch 부호 (|raw| 최댓값 = ch + (dv-1)*7 의 성립 조건)")
ch = llr.row_ch[:, :, 0]
neg = np.argwhere(ch < 0)
print("  row_ch min/max:", float(ch.min()), float(ch.max()))
print("  ch < 0 인 (row, dv) 칸 수:", len(neg))
for r, k in neg:
    print(f"    row {r+1} dv{dvs[k]}: ch={int(ch[r,k])}, "
          f"스크립트 max_raw={int(ch[r,k])+(dvs[k]-1)*EDGE_MAX}, "
          f"실제 |raw| 최댓값={abs(int(ch[r,k]))+(dvs[k]-1)*EDGE_MAX}")
print()

print("### A1-2. th 값 범위와 restart row의 th")
th = llr.row_th
print("  row_th min/max:", float(th.min()), float(th.max()))
for r in range(R):
    if np.any(th[r] < 0):
        print(f"    row {r+1} iter{llr.row_iter[r].tolist()} csw={int(llr.row_csw[r])}: "
              f"ch={ch[r].astype(int).tolist()} th={th[r].astype(int).tolist()}")
print()

print("### A4. 하위 임계값 분포 (228칸 = 57 row x 4 dv)")
th1, th2, th3 = th[:, :, 0], th[:, :, 1], th[:, :, 2]
print(f"  th3 <= 0 (|raw|>=th3 항상 참 -> 최소 레벨 1 도달 불가) 칸: "
      f"{int(np.sum(th3 <= 0))} / {R*llr.num_dv}")
for k, d in enumerate(dvs):
    print(f"    dv{d:<2d}: th3<=0 {int(np.sum(th3[:,k]<=0))} row, "
          f"th2<=ch(채널만으로 레벨5 이상) {int(np.sum(th2[:,k]<=ch[:,k]))} row, "
          f"th1<=ch(채널만으로 레벨7) {int(np.sum(th1[:,k]<=ch[:,k]))} row, "
          f"th3<=ch(채널만으로 레벨3 이상) {int(np.sum(th3[:,k]<=ch[:,k]))} row")
print("  th 비단조 (th1<th2 또는 th2<th3) 칸:")
nonmono = np.argwhere((th1 < th2) | (th2 < th3))
for r, k in nonmono:
    print(f"    row {r+1} dv{dvs[k]}: th={th[r,k].astype(int).tolist()} ch={int(ch[r,k])}")
if len(nonmono) == 0:
    print("    없음")
print()

print("### A5. 균일 기준선 비교에 ch 차이가 섞이는가")
print("  th_softness.py base_need7 = 7.0 - ch (파일 ch 그대로) -> th1만 바꾼 비교다")
for k, d in enumerate(dvs):
    print(f"    dv{d:<2d}: th1 중앙 {np.median(th1[:,k]):+.0f}, ch 중앙 {np.median(ch[:,k]):+.0f}, "
          f"th1-7 중앙 {np.median(th1[:,k]-7):+.0f}, th2 중앙 {np.median(th2[:,k]):+.0f} (균일 기준선 th2=5), "
          f"th3 중앙 {np.median(th3[:,k]):+.0f} (균일 기준선 th3=3)")
print()

print("### B3. 정보 구간 대 패리티 구간의 column degree 배치")
num_info = code.N_b - code.M_b
print(f"  N_b={code.N_b}, M_b={code.M_b}, 정보 구간 column block = 0..{num_info-1}, "
      f"패리티 구간 = {num_info}..{code.N_b-1}")
for k, d in enumerate(dvs):
    cols = np.flatnonzero(col_dv == k)
    print(f"    dv{d:<2d}: column block {cols.min()}..{cols.max()} ({len(cols)}개), "
          f"정보 구간 {int(np.sum(cols < num_info))}개, 패리티 구간 {int(np.sum(cols >= num_info))}개")
print("  패리티 구간 column block별 degree:",
      {int(c): int(code.col_deg[c]) for c in range(num_info, code.N_b)})
print()

print("### A2-1. CN row block별 마지막으로 처리되는 edge의 column dv")
print("  (_process_column은 column 0..N_b-1 순서, 각 CN의 min2는 마지막 갱신에 좌우된다)")
last_dv = {}
for i in range(code.M_b):
    edges = np.flatnonzero(code.edge_row == i)
    cols_i = code.edge_col[edges]
    last_col = int(cols_i.max())
    last_dv[i] = (last_col, dvs[col_dv[last_col]])
print("  row block -> (마지막 column block, 그 dv):", last_dv)
print()

print("### A2-2. _cnu_update 규칙을 그대로 옮긴 상태기계 검사")
RESET = EDGE_MAX


def cnu_pass(mags, init_min1, init_min2, init_pos):
    """한 iteration의 column 루프에서 CN 하나가 겪는 remove-old + insert 시퀀스.
    decoder._cnu_update와 같은 규칙 (edge_clear=False)."""
    min1, min2, pos = init_min1, init_min2, init_pos
    for e, m in enumerate(mags):
        if pos == e:                       # remove old
            min1, min2 = min2, RESET
        if m <= min1:                      # insert new
            min1, min2, pos = m, RESET, e
        elif m <= min2:
            min2 = m
    return min1, min2, pos


LEVELS = [7, 5, 3, 1]
# (가) min1은 이번 iteration 메시지의 최솟값 이하인가 (스크립트의 min1 상한 모델)
bad_min1 = 0
# (나) min2가 전 메시지의 최댓값(=연결 VN 실효 상한)을 넘는 사례가 있는가
min2_over = []
rng = np.random.default_rng(0)
for trial in range(200000):
    d = int(rng.integers(2, 7))
    mags = [int(rng.choice(LEVELS)) for _ in range(d)]
    i1 = int(rng.choice(LEVELS)); i2 = int(rng.choice(LEVELS))
    if i2 < i1:
        i1, i2 = i2, i1
    p = int(rng.integers(-1, d))
    m1, m2, _ = cnu_pass(mags, i1, i2, p)
    if m1 > min(mags):
        bad_min1 += 1
    if m2 > max(mags) and len(min2_over) < 3:
        min2_over.append((mags, i1, i2, p, m1, m2))
print(f"  min1 > min(이번 메시지) 인 사례: {bad_min1}건 (0이면 min1 상한 모델 유효)")
print(f"  min2 > max(이번 메시지) 인 사례 예시 (있으면 min2 상한 모델 무효):")
for s in min2_over:
    print(f"    mags={s[0]} 초기(min1,min2,pos)=({s[1]},{s[2]},{s[3]}) -> min1={s[4]}, min2={s[5]}")
if not min2_over:
    print("    없음")

# (다) 모든 메시지가 5 이하인데 min2 = 7 (RESET)이 되는가 (row 2 / row 57 모델 반증)
demo = cnu_pass([5, 5, 5, 5], 5, 5, -1)
print(f"  전 메시지 5, 초기 (5,5,-1) -> (min1,min2)={demo[:2]}")
demo2 = cnu_pass([5, 3, 5, 5], 7, 7, -1)
print(f"  메시지 [5,3,5,5], 초기 (7,7,-1) -> (min1,min2)={demo2[:2]}")

# (라) min1 == 7 이면 반드시 min2 == 7 인가 (메모 C10 ㉯ 전제)
viol = 0
for trial in range(200000):
    d = int(rng.integers(2, 7))
    mags = [int(rng.choice(LEVELS)) for _ in range(d)]
    i1 = int(rng.choice(LEVELS)); i2 = int(rng.choice(LEVELS))
    if i2 < i1:
        i1, i2 = i2, i1
    p = int(rng.integers(-1, d))
    m1, m2, _ = cnu_pass(mags, i1, i2, p)
    if m1 == RESET and m2 != RESET:
        viol += 1
print(f"  min1==7 인데 min2!=7 인 사례: {viol}건 (0이면 C10 ㉯ 전제 성립)")
print()

print("### A3. 상한 하락 연쇄를 1회 통과가 반영하는가 (row 2 예)")
r = 1     # row 2 (0-base)
for k, d in enumerate(dvs):
    print(f"  dv{d:<2d}: ch={int(ch[r,k])} th={th[r,k].astype(int).tolist()} "
          f"1회통과 max_raw={int(ch[r,k])+(d-1)*EDGE_MAX}")
print("  C2V 절대 상한은 min1/min2 <= RESET=7 이므로 dv별 max_raw의 (dv-1)*7 항은 낮아지지 않는다")
