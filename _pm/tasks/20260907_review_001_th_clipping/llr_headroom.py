"""LLR matrix 파일의 dv별 ch와 edge 상한 여유 비율(ch / (edge상한 × dv))을 row별로 출력."""
import sys
import numpy as np

sys.path.insert(0, r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base")
from src.llr_matrix import LLRMatrix
from src.pcm import QCCode

LLR_DIR = r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\LLR"
H_DIR = r"D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_base\Input\H_matrix"


def report(llr_name, h_name):
    llr = LLRMatrix.load(f"{LLR_DIR}\\{llr_name}")
    code = QCCode.load(f"{H_DIR}\\{h_name}")
    print("=" * 100)
    print(llr.summary())
    print(code.summary())
    print("edge_mag(레벨) =", llr.edge_mag.tolist(), " edge 상한 =", float(llr.edge_mag[0]))
    edge_max = float(llr.edge_mag[0])
    dvs = llr.dv_from.tolist()
    col_dv = llr.col_dv_idx(code)
    counts = np.bincount(col_dv, minlength=llr.num_dv)
    print("dv 구간", dvs, " column block 수", counts.tolist())
    print("group_rows", llr.group_rows, " group_type", llr.group_type)
    print()
    print("row  iter      csw   | " + " | ".join(f"dv{d:<2d}: ch th(1,2,3) ratio" for d in dvs))
    for r in range(len(llr.row_csw)):
        parts = []
        for k, d in enumerate(dvs):
            ch = float(llr.row_ch[r, k, 0])
            th = [int(t) for t in llr.row_th[r, k]]
            parts.append(f"ch={int(ch):2d} th={th} r={ch / (edge_max * d):.2f}")
        print(f"{r + 1:3d}  {llr.row_iter[r].tolist()!s:9s} {int(llr.row_csw[r]):5d} | " + " | ".join(parts))
    print()
    for k, d in enumerate(dvs):
        ch = llr.row_ch[:, k, 0]
        print(f"dv={d:2d} (block {counts[k]:3d}개): ch min/중앙/max = {ch.min():.0f}/{np.median(ch):.0f}/{ch.max():.0f}"
              f"  |  dv×edge상한 = {edge_max * d:.0f}"
              f"  |  ratio ch/(edge상한×dv) min/중앙/max = {ch.min() / (edge_max * d):.2f}/{np.median(ch) / (edge_max * d):.2f}/{ch.max() / (edge_max * d):.2f}")


report("LLR_MATRIX_HD_matrix_sel_1.txt", "matrix_sel_1.txt")
report("LLR_MATRIX_HD_1.txt", "example_18x147_z256.qc")
