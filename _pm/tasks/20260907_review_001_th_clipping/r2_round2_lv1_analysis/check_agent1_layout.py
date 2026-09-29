import sys, numpy as np
sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix
from src.pcm import QCCode
llr = LLRMatrix.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR\LLR_MATRIX_HD_matrix_sel_1.txt")
code = QCCode.load(r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\H_matrix\matrix_sel_1.txt")
deg = code.col_deg
print("column degree sequence (block index: degree), 변화점만:")
prev=None; runs=[]
for j,d in enumerate(deg):
    if d!=prev:
        runs.append([j,int(d),1]); prev=int(d)
    else: runs[-1][2]+=1
print(runs)
num_info = code.N_b - code.M_b
first_dv3 = int(np.flatnonzero(deg==3).min())
print("첫 dv3 column block:", first_dv3)
print("dv3 첫 등장 이후에 오는 dv11 column block 수:", int(np.sum((deg==11)&(np.arange(code.N_b)>first_dv3))))
print("dv3 첫 등장 이후에 오는 dv4 column block 수:", int(np.sum((deg==4)&(np.arange(code.N_b)>first_dv3))))
print("정보 구간(0..%d) degree 히스토그램:"%(num_info-1), dict(zip(*np.unique(deg[:num_info],return_counts=True))))
print("패리티 구간 degree 히스토그램:", dict(zip(*np.unique(deg[num_info:],return_counts=True))))
# 각 CN row block의 dv2 edge 수와 마지막 3개 edge의 column dv
col_dv_deg = deg
for i in range(code.M_b):
    e = np.flatnonzero(code.edge_row==i)
    cols = np.sort(code.edge_col[e])
    print(f"row {i:2d}: dv2 edge {int(np.sum(col_dv_deg[cols]==2))}개, 마지막 4 column의 degree {[int(col_dv_deg[c]) for c in cols[-4:]]}")
# row 2 / row 57 값
for r in (1,56):
    print(f"row {r+1}: csw={int(llr.row_csw[r])} iter={llr.row_iter[r].tolist()} ch={llr.row_ch[r,:,0].astype(int).tolist()} th={llr.row_th[r].astype(int).tolist()}")
# need7<=0 (채널만으로 레벨7) row 수 재확인 + 그 row들이 어느 iteration 구간인지
ch = llr.row_ch[:,:,0]; th1 = llr.row_th[:,:,0]
allk = np.all(th1<=ch, axis=1)
print("전 dv에서 th1<=ch 인 row 수:", int(allk.sum()), "->", [(r+1, llr.row_iter[r].tolist(), int(llr.row_csw[r])) for r in np.flatnonzero(allk)])
