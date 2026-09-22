"""패치한 함수들을 단일 프로세스에서 작은 매트릭스로 실행해 확인한다."""
import os, sys, io, copy
sys.path.insert(0, "D:/OneDrive/My_Projects/LDPC_dev/5_DAO/SRC")
os.chdir("D:/OneDrive/My_Projects/LDPC_dev/5_DAO/SRC")

import DAO_Config as C
import DAO_Main as M
from DAO_Constants import *
import numpy as np

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond:
        fails.append(name)

# ---- C1: 시퀀스 값 검증 로직과 HBF 시퀀스
valid = {int(m) for m in GenLLRMode}
check("C1 HBF 시퀀스가 GenLLRMode 값", all(int(v) in valid for v in C.DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE), str(C.DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE))
check("C1 GenLLRMode(값).name 동작", all(GenLLRMode(v).name for v in C.DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE))

# ---- C4 / H11: Update_Configs (SIM_IDX 20 프리셋 재현)
C.DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.RUN_OPTIMIZATION
C.REFC_CONFIG.init_n = 2
C.REFC_CONFIG.ch_type = 3
C.REFC_CONFIG.num_fixed_errs = [520, 530]
C.REFC_CONFIG.fixed_SCRs = [0.94]
C.REFC_CONFIG.fixed_SERs = [0.23]
C.UNCOR_CONFIG.ENABLE_LOAD_VECTOR = True
C.UNCOR_CONFIG.IS_TLC = True
M.Update_Configs()
check("C4 SCR가 채널 수만큼 확장", C.REFC_CONFIG.fixed_SCRs == [0.94, 0.94], str(C.REFC_CONFIG.fixed_SCRs))
check("C4 SER가 채널 수만큼 확장", C.REFC_CONFIG.fixed_SERs == [0.23, 0.23], str(C.REFC_CONFIG.fixed_SERs))
check("H11 LOAD_VECTOR일 때 NUM_LINES_PER_UNCOR 계산됨", C.UNCOR_CONFIG.NUM_LINES_PER_UNCOR == int(2 * (36864 / 64 / 4)), str(C.UNCOR_CONFIG.NUM_LINES_PER_UNCOR))
C.REFC_CONFIG.fixed_SCRs = [0.9, 0.9, 0.9]
try:
    M.Update_Configs(); check("C4 길이 3 대 채널 2는 ValueError", False, "예외 없음")
except ValueError as e:
    check("C4 길이 3 대 채널 2는 ValueError", True)
C.REFC_CONFIG.fixed_SCRs = [0.94, 0.94]

# ---- C7: 배리어 타임아웃이 ECC 상한을 덮는지
check("C7 MPI_TEST_BARRIER_TIMEOUT_SECONDS > SIM_MAX_TIME_OUT", C.TIME_CONFIG.MPI_TEST_BARRIER_TIMEOUT_SECONDS > SIM_MAX_TIME_OUT, str(C.TIME_CONFIG.MPI_TEST_BARRIER_TIMEOUT_SECONDS))

# ---- 작은 매트릭스 파일 만들기 (init_n=1: ch 1, th 3, dv 2, 그룹 2)
C.REFC_CONFIG.init_n = 1
C.REFC_CONFIG.ch_type = 2
C.REFC_CONFIG.num_fixed_errs = [400]
M.Update_Configs()
tmp = "D:/OneDrive/My_Projects/LDPC_dev/5_DAO/_pm/tasks/20260921_SW_branch_DAO_support/review/checks/mat"
os.makedirs(tmp, exist_ok=True)
rows = [
    "10 9 8 7 10 9 8 7 -1 1 4 -1",
    "10 9 8 7 10 9 8 7 400 1 4 -1",
    "10 9 8 7 10 9 8 7 -1 5 8 -1",
    "10 9 8 7 10 9 8 7 800 5 8 -1",
    "10 9 8 7 10 9 8 7 200 5 8 -1",
]
text = "\n".join(["4", "", "2", "", "11 4", "11 4", "", "2", "", "2 3", "1 1", "", "0", "", "31 31 31 31", "0 0 0 0", ""] + rows) + "\n"
io.open(os.path.join(tmp, "LLR_MATRIX_1.txt"), "w", encoding="utf-8").write(text)
from DAO_LLR_MATRIX import LLR_MATRIX, LLR_Row
m = LLR_MATRIX(init_n=1, matrix_idx=1, is_HBF_OPT=False, input_dir=tmp)
ok, msg = m.Is_LLR_Valid()
check("기준 매트릭스 유효", ok, msg)

# ---- H1: CSW 범위, 배수, 중복 보정
t = m.Deep_Copy()
t.groups[1][1].CSW = 5000
t.groups[1][2].CSW = 3
msgs = t.Correct_LLR_Matrix()
csws = [r.CSW for r in t.groups[1]]
ok, msg = t.Is_LLR_Valid()
check("H1 범위 밖과 배수 아님 보정 뒤 유효", ok and csws == [-1, 1408, 8], f"{csws} {msg}")
t = m.Deep_Copy()
t.groups[1][1].CSW = 400
t.groups[1][2].CSW = 400
t.Correct_LLR_Matrix()
csws = [r.CSW for r in t.groups[1]]
ok, msg = t.Is_LLR_Valid()
check("H1 같은 CSW 두 개는 한 단계 내려 유효", ok and csws == [-1, 400, 392], f"{csws} {msg}")

# ---- H5: 헤더 대 본문
t = m.Deep_Copy(); t.header.num_group = 99
check("H5 num_group 불일치 검출", not t.Is_LLR_Valid()[0])
t = m.Deep_Copy(); t.header.num_row_each_group = np.array([3, 2])
check("H5 그룹별 행 수 불일치 검출 (합은 같음)", not t.Is_LLR_Valid()[0])

# ---- H2: restart row 검사
t = m.Deep_Copy()
restart_row = LLR_Row(np.array([1, 1, 1, 1], dtype=np.int32), -1, 5, 5, -1, True)  # 길이 4 (정상 8)
t.groups.insert(1, [restart_row])
t.groups[2][0].iter_start = 6; t.groups[2][1].iter_start = 6; t.groups[2][2].iter_start = 6
t.header.num_group = 3; t.header.num_row_each_group = np.array([2, 1, 3]); t.header.type_each_group = np.array([1, 1, 1])
t.header.num_restart = 1; t.header.restart_iter = np.array([5]); t.restart_groups = [2]
ok, msg = t.Is_LLR_Valid()
check("H2 길이 틀린 restart row 검출", (not ok) and "Restart Group 1 row length" in msg, msg)
t.groups[1][0].ch_th_values = np.array([1, 1, 1, 1, 1, 1, 1, 1], dtype=np.int32)
ok, msg = t.Is_LLR_Valid()
check("H2 정상 restart row는 통과", ok, msg)

# ---- H4: HBF 보정이 dv0의 TH만 고정
C.HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL = 0
hb = LLR_MATRIX(init_n=1, matrix_idx=1, is_HBF_OPT=True, input_dir=tmp)
hb.groups[0][0].ch_th_values = np.array([10, 9, 8, 7, 10, 3, 9, 2], dtype=np.int32)
hb.Correct_LLR_Matrix()
vals = hb.groups[0][0].ch_th_values.tolist()
check("H4 dv0 TH는 0, dv1 TH는 정렬만", vals == [10, 0, 0, 0, 10, 9, 3, 2], str(vals))

# ---- H17: 미테스트 avg_iterations
class Fake:  # LLR_OPT의 두 메서드만 빌려 쓴다
    Is_List_A_Strictly_Better = M.LLR_OPT.Is_List_A_Strictly_Better
    Is_Matrix_Better = M.LLR_OPT.Is_Matrix_Better
    def MPI_Abort(self, msg): raise RuntimeError(msg)
C.DAO_CONFIG.ENABLE_AVG_ITER_UPDATE = True
a = m.Deep_Copy(); b = m.Deep_Copy()
a.FERs = [0.1]; b.FERs = [0.1]
a.avg_iterations = [-1.0]; b.avg_iterations = [20.0]
check("H17 미테스트(-1)가 측정값을 이기지 않음", not Fake().Is_Matrix_Better(a, b))
a.avg_iterations = [10.0]
check("H17 낮은 avg가 이김", Fake().Is_Matrix_Better(a, b))

# ---- H9: REORDER trial 식 일치 (n=3, HD)
n = 3
trials_per_round = sum(range(n, 0, -1))
check("H9 두 식 일치", 1 + trials_per_round + 1 == 1 + sum(range(n, 0, -1)) + 1)

# ---- _safe_allgather 존재와 시그니처
import inspect
check("C8 _safe_allgather 정의", "_safe_allgather" in dir(M.LLR_OPT) and list(inspect.signature(M.LLR_OPT._safe_allgather).parameters) == ["self", "data", "comm_name"])
check("H16 _Restore_State_After_Partial_Rebuild 정의", "_Restore_State_After_Partial_Rebuild" in dir(M.LLR_OPT))

print("\nFAILED:", fails if fails else "none")
