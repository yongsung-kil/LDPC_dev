"""matrix_sel_1 LLR 파일에서 (P,Q) 후보별로 반전 불능인 row×dv 칸 수를 센다.

반전 조건: 본체 _vn_decide는 sum_t <= 0에서 반전하고 flip 도메인의 채널 항은 항상 +ch이므로
반전 가능은 extrinsic 합 >= ch, 반전 불능은 extrinsic 합 < ch (동점은 반전 가능).

extrinsic 합의 상한 두 가지를 함께 센다.
- dv·P: 굳은 열(잘못된 판정에 확신이 쌓인 VN)은 자기 V2C가 커서 어느 CN에서도 min1 위치가
  되기 어렵고 모든 edge에서 min(min1, P) <= P만 받는다. 반전 불능 판정의 실효 상한이며
  001의 사망 관측(HD_1 dv4 ch10에서 (2,3) (1,3) 사망, 비율 복원 dv4 ch16에서 (4,8) 사망)과 맞는다
- dv·Q: 한 VN이 dv개 CN 전부에서 min1 위치일 때의 절대 상한. 001 사망 관측을 맞히지 못하므로
  판정에는 쓰지 않고 참고로만 낸다
"""
import sys
import numpy as np

sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix

llr = LLRMatrix.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt")
dvs = llr.dv_from.tolist()
R = len(llr.row_csw)
pairs = [(7, 7), (5, 7), (3, 7), (3, 5), (2, 5), (2, 3), (1, 3)]
print(f"row 수 {R}, dv {dvs}. 값 = 반전 불능 row 수 / {R}  (조건: 상한 < ch, 동점은 반전 가능)")
print("(P,Q) | " + " | ".join(f"dv{d} [dv·P 기준 / dv·Q 기준]" for d in dvs))
for P, Q in pairs:
    cells = []
    for k, d in enumerate(dvs):
        ch = llr.row_ch[:, k, 0]
        dead_p = int(np.sum(d * P < ch))
        dead_q = int(np.sum(d * Q < ch))
        cells.append(f"{dead_p:2d} / {dead_q:2d}  (dv·P={d * P}, dv·Q={d * Q})")
    print(f"({P},{Q}) | " + " | ".join(cells))
