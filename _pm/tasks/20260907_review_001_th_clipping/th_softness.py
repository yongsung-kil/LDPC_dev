"""th의 '부드러운 압축' 정도: 레벨 7(그리고 5)을 내보내려면 채널 ch 외에 얼마나 큰
순(net) extrinsic 지지가 필요한지. need7 = th1 - ch, need5 = th2 - ch.
비율 = need / ((dv-1)*7)  (0 이하: 채널만으로 충분, 1 초과: 도달 불가).
균일 기준선 th=[7,5,3] (make_internal_uniform_matrix 기본)과 비교."""
import sys
import numpy as np

sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix

llr = LLRMatrix.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt")
dvs = llr.dv_from.tolist()
R = len(llr.row_csw)
print("dv별 (57 row) : need7=th1-ch 의 min/중앙/max, 비율 need7/((dv-1)*7) 중앙, "
      "need5=th2-ch 중앙, 균일 기준선(th1=7)의 need7 중앙")
for k, d in enumerate(dvs):
    ch = llr.row_ch[:, k, 0].astype(float)
    th1 = llr.row_th[:, k, 0].astype(float)
    th2 = llr.row_th[:, k, 1].astype(float)
    need7 = th1 - ch
    need5 = th2 - ch
    ext_max = (d - 1) * 7.0
    base_need7 = 7.0 - ch
    print(f"dv{d:<2d}: need7 {need7.min():+.0f}/{np.median(need7):+.0f}/{need7.max():+.0f}"
          f"  비율(중앙) {np.median(need7) / ext_max:+.2f}"
          f"  need5(중앙) {np.median(need5):+.0f}"
          f"  | 균일 기준선 need7(중앙) {np.median(base_need7):+.0f}"
          f"  | need7>0 인 row {int(np.sum(need7 > 0))}개, need5>0 인 row {int(np.sum(need5 > 0))}개")
