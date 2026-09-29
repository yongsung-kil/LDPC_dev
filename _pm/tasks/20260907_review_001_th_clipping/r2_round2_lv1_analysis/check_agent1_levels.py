import sys, numpy as np
sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix
llr = LLRMatrix.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt")
dvs = llr.dv_from.tolist(); th = llr.row_th; ch = llr.row_ch[:,:,0]; R=len(llr.row_csw)
t1,t2,t3 = th[:,:,0],th[:,:,1],th[:,:,2]
maxraw = ch + (np.array(dvs)-1)*7
# 레벨별 도달 불가 칸 (228칸)
l7 = t1 > maxraw                       # 레벨 7 도달 불가
l5 = (t2 >= t1) | (t2 > maxraw)        # 레벨 5 구간 [th2, th1) 이 빈 경우
l3 = (t3 >= t2) | (t3 > maxraw)        # 레벨 3 구간 [th3, th2) 이 빈 경우
l1 = t3 <= 0                           # 레벨 1 구간 [0, th3) 이 빈 경우
print("228칸 중 도달 불가:  레벨7 %d, 레벨5 %d, 레벨3 %d, 레벨1 %d" % (l7.sum(),l5.sum(),l3.sum(),l1.sum()))
for k,d in enumerate(dvs):
    print(f"  dv{d:<2d}: L7 {int(l7[:,k].sum())}, L5 {int(l5[:,k].sum())}, L3 {int(l3[:,k].sum())}, L1 {int(l1[:,k].sum())}")
n_levels = 4 - (l7.astype(int)+l5.astype(int)+l3.astype(int)+l1.astype(int))
print("칸별 실제 사용 레벨 수 분포:", dict(zip(*np.unique(n_levels, return_counts=True))))
rows_any = np.flatnonzero((l7|l5|l3|l1).any(axis=1))
print("도달 불가 레벨이 하나라도 있는 row 수:", len(rows_any))
print("그 row들:", [(int(r+1), int(llr.row_csw[r]), llr.row_iter[r].tolist()) for r in rows_any])
