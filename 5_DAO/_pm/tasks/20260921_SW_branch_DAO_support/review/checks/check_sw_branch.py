"""SW 분기 지원 검사: 설계 문서 5절 안전성 체크리스트 ㉮~㉵를 단일 프로세스로 확인한다."""
import os, sys, io, random
sys.path.insert(0, "D:/OneDrive/My_Projects/LDPC_dev/5_DAO/SRC")
os.chdir("D:/OneDrive/My_Projects/LDPC_dev/5_DAO/SRC")

import DAO_Config as C
import DAO_Main as M
from DAO_Constants import *
from DAO_LLR_MATRIX import LLR_MATRIX
import numpy as np

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))
    if not cond:
        fails.append(name)

C.REFC_CONFIG.init_n = 1
C.REFC_CONFIG.ch_type = 2
C.REFC_CONFIG.num_fixed_errs = [400]
M.Update_Configs()

NEW_DIR = "D:/OneDrive/My_Projects/LDPC_dev/5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix"
OLD_DIR = "D:/OneDrive/My_Projects/LDPC_dev/5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix"

def tokens_of_file(path):
    return [int(t) for line in io.open(path, encoding="utf-8") for t in line.split()]

def tokens_of_matrix(m):
    return [int(t.replace("*", "")) for line in m.Build_LLR_Matrix_Output_Lines() for t in line.split()]

# ㉮ 옛 형식 회귀
old = LLR_MATRIX(init_n=1, matrix_idx=0, is_HBF_OPT=False, input_dir=OLD_DIR)
ok, msg = old.Is_LLR_Valid()
check("㉮ 옛 형식 매트릭스 유효", ok, msg)
check("㉮ 옛 형식 왕복 일치", tokens_of_matrix(old) == tokens_of_file(os.path.join(OLD_DIR, "LLR_MATRIX_0.txt")))
check("㉮ 옛 형식은 분기 없음, 묶음은 그룹 하나씩", (not old.has_sw_branch) and all(b == [g] for g, b in enumerate(old.bundle_of_group)))

# ㉯ 새 형식 두 파일
m1 = LLR_MATRIX(init_n=1, matrix_idx=1, is_HBF_OPT=False, input_dir=NEW_DIR)
m2 = LLR_MATRIX(init_n=1, matrix_idx=2, is_HBF_OPT=False, input_dir=NEW_DIR)
ok1, msg1 = m1.Is_LLR_Valid(); ok2, msg2 = m2.Is_LLR_Valid()
check("㉯ LLR_MATRIX_1 유효", ok1, msg1)
check("㉯ LLR_MATRIX_2 유효", ok2, msg2)
check("㉯ LLR_MATRIX_1 왕복 일치 (헤더 20/21/1과 꼬리 보존)", tokens_of_matrix(m1) == tokens_of_file(os.path.join(NEW_DIR, "LLR_MATRIX_1.txt")))
check("㉯ LLR_MATRIX_2 왕복 일치", tokens_of_matrix(m2) == tokens_of_file(os.path.join(NEW_DIR, "LLR_MATRIX_2.txt")))
check("㉯ max_iteration 124", m1.max_iteration == 124 and m2.max_iteration == 124, f"{m1.max_iteration} {m2.max_iteration}")

# ㉰ 묶음
b1 = [m1.bundle_of_group[g] for g in range(len(m1.groups))]
check("㉰ 파일 1 묶음", b1[0] == [0, 1] and b1[1] == [0, 1] and b1[2] == [2] and b1[3] == [3] and b1[4] == [4, 5] and b1[5] == [4, 5] and all(b1[g] == [g] for g in range(6, 12)), str(b1))
b2 = [m2.bundle_of_group[g] for g in range(len(m2.groups))]
check("㉰ 파일 2 묶음", b2[0] == [0, 1] and b2[2] == [2] and b2[3] == [3, 4] and all(b2[g] == [g] for g in range(5, 11)), str(b2))

# ㉱ 구간
s1 = m1.span_of_group
check("㉱ 파일 1 구간", s1[0] == (1, 4, 2) and s1[1] == (1, 4, 2) and s1[2] == (1, 4, 2) and s1[3] == (5, 8, 2) and s1[4] == (5, 8, 2) and s1[5] == (5, 8, 2) and all(s1[g] is None for g in range(6, 12)), str(s1))
s2 = m2.span_of_group
check("㉱ 파일 2 구간 (그룹 0, 1은 분기 하나짜리 구간)", s2[0] == (1, 4, 1) and s2[1] == (1, 4, 1) and s2[2] == (5, 8, 2) and s2[3] == (5, 8, 2) and s2[4] == (5, 8, 2) and all(s2[g] is None for g in range(5, 11)), str(s2))

# ㉲ 틀린 파일 거부
def invalid(name, mutate, expect_substring):
    t = m1.Deep_Copy()
    mutate(t)
    ok, msg = t.Is_LLR_Valid()
    check(f"㉲ 거부: {name}", (not ok) and expect_substring in msg, f"ok={ok} msg={msg}")

def set_flag(t, g, v):
    for row in t.groups[g]:
        row.floor_flag = v
invalid("분기 index 0에서 2로 건너뜀", lambda t: set_flag(t, 2, 2), "must stay, increase by 1")
def shrink_branch1(t):
    for row in t.groups[2]:
        row.iter_end = 3
invalid("분기 1이 구간 끝을 덮지 않음", shrink_branch1, "ends at iteration 3 but its span ends at 4")
def mixed(t):
    t.groups[1][3].floor_flag = 1
invalid("한 그룹 안에서 꼬리가 다름", mixed, "different SW branch index")
def header_mismatch(t):
    t.header.type_each_group = np.array([20, 20, 20, 20, 21, 21, 1, 1, 1, 1, 1, 1])
invalid("헤더 20인데 꼬리 1", header_mismatch, "header type 20 says branch 0 but rows carry 1")
def wrong_start(t):
    for row in t.groups[3]:
        row.iter_start = 6
invalid("분기 0의 새 구간이 앞 구간 끝 + 1에서 시작하지 않음", wrong_start, "iter_start must be 5")
def span_starts_with_1(t):
    set_flag(t, 7, 1)
invalid("구간이 분기 1로 시작", span_starts_with_1, "must start with branch 0")
def plain_header_with_branch_tail(t):
    t.header.type_each_group = np.array([1, 1, 21, 20, 21, 21, 1, 1, 1, 1, 1, 1])
invalid("헤더 1(보통 그룹)인데 꼬리 0", plain_header_with_branch_tail, "is a plain group but rows carry SW branch index 0")
# 헤더 10 규약: 파일 2와 같은 구조를 헤더 1 1 로 쓰면 무효, 10 10 이면 유효
t = m2.Deep_Copy(); t.header.type_each_group = np.array([1, 1, 20, 21, 21, 1, 1, 1, 1, 1, 1])
check("㉲ 거부: 묶음을 헤더 1로 쓰면 무효 (10을 써야 함)", not t.Is_LLR_Valid()[0])
check("㉯ 파일 2 헤더가 10 10 20 21 21", list(m2.header.type_each_group[:5]) == [10, 10, 20, 21, 21], str(list(m2.header.type_each_group[:5])))

# ㉳ 묶음 변이
class Fake:
    now_enable_CSW_update_limit = False
    current_target_group_idx = 0
    Get_Mutate_Matrix_Skip_Row_Idx = M.LLR_OPT.Get_Mutate_Matrix_Skip_Row_Idx
    _Get_Target_Bundle_Groups = M.LLR_OPT._Get_Target_Bundle_Groups
    Generate_Random_Mutation = M.LLR_OPT.Generate_Random_Mutation
    Mutate_CSW = M.LLR_OPT.Mutate_CSW
    Check_SW_Branch_Mode_Allowed = M.LLR_OPT.Check_SW_Branch_Mode_Allowed
    def MPI_Abort(self, msg): raise RuntimeError(msg)

random.seed(1)
C.DAO_CONFIG.IS_HBF_OPT = False
f = Fake(); f.current_target_group_idx = 0
t = m2.Deep_Copy()
muts = f.Generate_Random_Mutation(t)
groups_touched = {g for g, r, c, o, n in muts}
per_group = {g: sum(1 for x in muts if x[0] == g) for g in groups_touched}
check("㉳ MUTATE_MATRIX가 묶음 {0,1} 두 그룹 모두 변이", groups_touched == {0, 1}, str(groups_touched))
check("㉳ 그룹마다 NUM_ELEMENTS_TO_MUTATE_CHTH개", all(v == C.MUTATE_CONFIG.NUM_ELEMENTS_TO_MUTATE_CHTH for v in per_group.values()), str(per_group))
t = m2.Deep_Copy()
mods = f.Mutate_CSW(t)
check("㉳ MUTATE_CSW는 묶음 안 row가 있는 그룹 1만 (그룹 0은 row 하나)", {g for g, r, o, n in mods} == {1}, str(mods))
ok, msg = t.Is_LLR_Valid()
t.Correct_LLR_Matrix(); ok2, msg2 = t.Is_LLR_Valid()
check("㉳ CSW 변이 뒤 보정하면 유효", ok2, msg2)
f.current_target_group_idx = 10
t = m2.Deep_Copy(); muts = f.Generate_Random_Mutation(t)
check("㉳ 분기 없는 그룹은 그룹 하나만 변이", {g for g, *_ in muts} == {10}, str({g for g, *_ in muts}))

# ㉴ ㉵ 모드 허용 검사
check("㉴ 파일 1 타겟 g3(분기 0)은 마지막 분기가 아니라 오류", "only the last branch" in (f.Check_SW_Branch_Mode_Allowed(m1, GenLLRMode.MUTATE_MATRIX, 3, [3, 4, 6, 7, 8, 9, 10, 11]) or ""))
check("㉴ 파일 1 타겟 g4(분기 1)는 허용", f.Check_SW_Branch_Mode_Allowed(m1, GenLLRMode.MUTATE_CSW, 4, [4, 6, 7, 8, 9, 10, 11]) is None)
check("㉴ 파일 2 타겟 g0(분기 하나짜리 구간)은 허용", f.Check_SW_Branch_Mode_Allowed(m2, GenLLRMode.MUTATE_MATRIX, 0, [0, 2, 3, 5, 6, 7, 8, 9, 10]) is None)
check("㉵ 타겟에 분기 그룹이 있으면 REORDER_GROUP은 오류", "not allowed" in (f.Check_SW_Branch_Mode_Allowed(m1, GenLLRMode.REORDER_GROUP, 4, [4, 6, 7, 8, 9, 10, 11]) or ""))
check("㉵ 타겟이 분기 구간 뒤(g6~)뿐이면 REORDER_GROUP 허용", f.Check_SW_Branch_Mode_Allowed(m1, GenLLRMode.REORDER_GROUP, 6, list(range(6, 12))) is None)
check("㉵ 타겟이 분기 구간 뒤여도 DELETE_ROW 허용", f.Check_SW_Branch_Mode_Allowed(m1, GenLLRMode.DELETE_ROW, 6, list(range(6, 12))) is None)
check("㉵ GEN_INITIAL_GROUP은 분기 그룹이 있으면 언제나 오류", "replaces every group" in (f.Check_SW_Branch_Mode_Allowed(m1, GenLLRMode.GEN_INITIAL_GROUP, 6, list(range(6, 12))) or ""))
check("㉵ 옛 형식에 REORDER_GROUP은 허용", f.Check_SW_Branch_Mode_Allowed(old, GenLLRMode.REORDER_GROUP, 1, [1, 2]) is None)
# 보호 구간 안전망
class FakeGuard:
    target_group_indices = list(range(6, 12))
    _Protected_Groups_Changed = M.LLR_OPT._Protected_Groups_Changed
fg = FakeGuard()
same = m1.Deep_Copy()
check("보호 구간: 그대로면 None", fg._Protected_Groups_Changed(m1, same) is None)
touched = m1.Deep_Copy(); touched.groups[5][0].iter_end = 9
check("보호 구간: 분기 그룹의 iteration이 바뀌면 검출", "protected g5" in (fg._Protected_Groups_Changed(m1, touched) or ""))
touched = m1.Deep_Copy(); touched.groups[2][1].ch_th_values[0] += 1
check("보호 구간: 분기 그룹의 값이 바뀌면 검출", "values changed" in (fg._Protected_Groups_Changed(m1, touched) or ""))
touched = m1.Deep_Copy(); touched.groups[7][0].iter_end += 0; touched.groups[8][1].ch_th_values[0] += 1
check("보호 구간: 타겟 그룹(g8)이 바뀐 것은 검출 대상 아님", fg._Protected_Groups_Changed(m1, touched) is None)

# 타겟 목록: Initialize_Stage와 같은 계산
heads = []
for idx in range(0, len(m2.groups)):
    h = m2.bundle_of_group[idx][0]
    if h not in heads: heads.append(h)
check("타겟 목록이 묶음 대표만 담음 (파일 2, 시작 0)", heads == [0, 2, 3] + list(range(5, 11)), str(heads))
heads = []
for idx in range(1, len(m2.groups)):
    h = m2.bundle_of_group[idx][0]
    if h not in heads: heads.append(h)
check("시작 index가 묶음 중간이면 첫 그룹으로 당김 (파일 2, 시작 1)", heads[0] == 0, str(heads))

print("\nFAILED:", fails if fails else "none")
