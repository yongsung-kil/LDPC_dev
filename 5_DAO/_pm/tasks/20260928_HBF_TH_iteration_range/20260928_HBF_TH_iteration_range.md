# HBF 최적화 모드의 dv_idx 0 TH 고정을 HBF 구간의 row로 한정

> 작성: 2026-09-28 17:06:46
> 등급: Review (유효성 규칙과 값 고정 범위의 로직 수정). 사용자 지시로 수정을 적용했다.
> 관련: 규칙 정본은 [DAO_spec.md 3.6절](../../../DAO_spec.md)

## 1. 목적

HBF(Hybrid Bit Flipping) 최적화 모드(`IS_HBF_OPT`)에서 dv_idx 0의 TH를 상수 0으로 고정하는 규칙이 HBF 구간(iteration 1~4)의 row에만 걸리게 한다. iteration 5 이상의 row는 dv_idx 0의 TH에 0이 아닌 값을 가질 수 있다. 아울러 바꿀 그룹을 사용자가 직접 고르는 설정을 둔다 (3.1절).

## 2. 배경 (관측과 원인)

사용자 관측: 그룹 2(iteration 5 이상)의 dv_idx 0 TH가 15 10 0인 매트릭스를 HBF 최적화 모드로 넣으면 아래 오류로 멈춘다.

```
In HD_HBF_OPT mode, Group 2 Row 0 DV 0 invalid TH values: expected all 0, got [15, 10, 0]
```

원인은 HBF 규칙을 쓰는 자리들이 row의 iteration을 보지 않고 매트릭스 전체에 규칙을 건 것이다.

- ㉮ `Is_LLR_Valid`가 모든 그룹의 dv_idx 0 TH에 상수를 요구했다 (HBF1)
- ㉯ `Is_LLR_Valid`가 매트릭스의 max_iteration이 `HBF_MAX_ITERATION`(4) 이하일 것을 요구했다 (HBF2). iteration 5 이상의 그룹을 가진 매트릭스는 ㉮를 지나도 여기서 걸린다
- ㉰ `Correct_Ch_Th_In_Row`가 모든 row의 dv_idx 0 TH를 상수로 덮어썼다. iteration 5 이상 row의 TH 값이 보정 때마다 0이 된다
- ㉱ `Gen_LLR_Regen_DV`와 `Gen_LLR_Regen_Row`가 타겟 그룹의 iteration과 무관하게 dv_idx 0 TH를 상수로 만들었다
- ㉲ `Generate_Random_Mutation`이 모든 그룹에서 dv_idx 0 TH를 변이 후보에서 뺐다

디코더 쪽 근거: [decoder.cpp:4058](../../../../0_LDPC_original/src/decoder.cpp)은 BF가 켜져 있고 `iter <= ITER_MAX_HBF`(4)이며 DV가 가장 높은 등급일 때 1 bit 정밀도로 처리해 TH를 읽지 않는다. iteration 5부터는 TH를 읽는다.

dv_idx 0의 위치: row는 `CH(dv 0) TH(dv 0) CH(dv 1) TH(dv 1) ...` 순서이고, 코드는 row를 `num_parameter_each_set` 칸씩 잘라 맨 앞 칸들을 dv_idx 0으로 읽는다. 이 부분은 수정 없이 맞게 동작한다.

## 3. 설계

판단을 한 함수에 모으고 다섯 자리가 모두 그 함수를 쓴다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_MATRIX.Is_Row_In_HBF_Iterations` (새 함수) | `is_HBF_OPT`이고 row의 `iter_end <= HBF_MAX_ITERATION`이면 True |
| 2 | `LLR_MATRIX.Is_LLR_Valid` | HBF1(dv_idx 0 TH 상수)을 HBF 구간의 row에만 검사. 오류 문구에 row의 iteration과 HBF 구간을 함께 적음. HBF2는 row가 HBF 구간의 경계를 걸치는지 검사 (매트릭스의 max_iteration에는 상한을 두지 않음) |
| 3 | `LLR_MATRIX.Correct_LLR_Matrix`, `Correct_Ch_Th_In_Row` | row가 HBF 구간에 있을 때만 dv_idx 0 TH를 상수로 고정 (`is_row_in_HBF_iterations` 인자) |
| 4 | `LLR_OPT.Gen_LLR_Regen_DV`, `Gen_LLR_Regen_Row` | 바꿀 row가 HBF 구간에 있을 때만 dv_idx 0 TH를 상수로 만듦 |
| 5 | `LLR_OPT.Generate_Random_Mutation` | row가 HBF 구간에 있을 때만 dv_idx 0 TH column을 변이 후보에서 뺌 |

row는 HBF 구간의 경계를 걸치지 않는다 (사용자 확인 2026-09-28: 입력과 결과 모두 iteration 1~4, 5~8, 9 이후처럼 구간 안에 머물고, HBF 구간 안은 1, 2~3, 4처럼 나눌 수 있다). HBF2가 입력 매트릭스와 trial 매트릭스에 똑같이 걸리므로, 경계를 걸치는 row(예: iteration 3~6)를 만든 trial은 유효하지 않은 매트릭스로 버려진다.

`_generate_random_row`는 iteration이 정해지기 전의 row를 만들므로 dv_idx 0 TH도 난수로 채운다. row가 매트릭스에 들어간 뒤 `Correct_LLR_Matrix`가 iteration을 보고 고정한다.

### 3.1 타겟 그룹을 직접 지정하는 설정 (사용자 요청 2026-09-28)

HBF 최적화 모드도 타겟 그룹은 보통 모드와 똑같이 고른다 (`INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지를 모드 시퀀스 한 바퀴마다 하나씩). 그래서 iteration 5 이상의 그룹도 타겟이 된다. 바꿀 그룹만 고르도록 `DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST`를 둔다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST` | 기본값 None (`INITIAL_TARGET_GROUP_IDX`를 따름). 목록이면 적은 그룹만, 적은 순서대로 타겟 |
| 2 | `LLR_OPT.Build_Target_Group_Indices` (새 함수) | 설정과 매트릭스에서 타겟 목록을 만드는 한 곳. `Initialize_LLR_Matrix`, `Initialize_Stage`, `Update_Optimal_LLR`이 쓴다. 목록의 값은 그룹 하나하나의 index다 (3.3절) |
| 3 | `FIXED_TARGET_GROUP_ALLOWED_MODES` (`DAO_Constants.py`) | 목록과 함께 쓰는 모드. 그룹 수, 순서, iteration 구간을 그대로 두는 9개 (MUTATE_MATRIX, MUTATE_CSW, SWAP_ROW, COPY_ROWS, COPY_GROUP, INSERT_RANDOM_ROW, INSERT_MUTATED_ROW, REGEN_DV, REGEN_ROW) |
| 4 | `LLR_OPT.Check_Fixed_Target_Group_Idx_List` (새 함수) | 목록의 꼴, 범위, 중복과 지금 쓰는 모드 시퀀스를 검사. `Validate_Config`가 시작할 때 부른다 |

허용 모드를 가른 기준은 코드에서 확인한 두 가지다. ㉮ 그룹을 넣거나 빼거나 순서를 바꾸는가 (`groups.insert`, `groups.pop`, `groups =`) ㉯ row의 `iter_start`나 `iter_end`를 바꾸는가. GEN_INITIAL_GROUP, REORDER_GROUP, INSERT_RANDOM_GROUP, INSERT_MUTATED_GROUP, SPLIT_GROUP, ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP이 여기에 걸린다. 이 모드들이 그룹 번호를 밀면 목록의 index가 다른 그룹을 가리키게 된다.

### 3.2 HBF 최적화 모드의 seed 모드 (사용자 요청 2026-09-28)

`Set_Seed_Mode`에는 HBF 최적화 모드 전용 갈래가 있었다. `HBF_OPT_CONFIG.HBF_OPT_USING_UNCOR`가 True면 언제나 LOAD_UNCOR_SEED, False면 언제나 DEFAULT를 골랐고, 실행 모드와 uncor 로드 모드는 보지 않았다. 이 갈래와 설정 값은 반입 커밋(2811bff, 2026-08-14)부터 있었고 `reference/`의 원형에도 같은 줄이 있다. `HBF_OPT_USING_UNCOR`를 읽는 자리는 이 갈래 하나였다.

갈래를 없애 HBF 최적화 모드도 보통 모드와 같은 규칙을 따르게 하고, 읽는 자리가 없어진 `HBF_OPT_USING_UNCOR`도 없앴다.

| 조건 (HBF 최적화 모드) | 갈래가 있을 때 (기본값 True) | 보통 모드와 같은 규칙 |
|------|------|------|
| 최적화, uncor seed 로드 | LOAD_UNCOR_SEED | LOAD_UNCOR_SEED (같음) |
| 최적화, uncor vector 로드 (`ENABLE_LOAD_VECTOR`) | LOAD_UNCOR_SEED (풀에는 vector가 있어 어긋남) | LOAD_UNCOR_VECTOR |
| TEST_FER | LOAD_UNCOR_SEED (풀이 없음) | DEFAULT |
| SAVE_UNCOR | LOAD_UNCOR_SEED (uncor가 저장되지 않음) | SAVE_UNCOR_SEED |
| REDECODE | LOAD_UNCOR_SEED (실패 seed가 저장되지 않음) | LOAD_UNCOR_SEED_SAVE_UNCOR_SEED |

uncor 풀은 `LOAD_UNCOR_MODE`로 준비되므로(`Setup_Uncor_Pool`), seed 모드도 같은 값에서 정해져야 둘이 어긋나지 않는다. 없어지는 기능은 하나다: `HBF_OPT_USING_UNCOR = False`로 uncor 없이 난수 프레임으로 최적화하는 실행.

### 3.3 타겟과 변이의 단위를 그룹 하나로 (사용자 요청 2026-09-29)

SW 분기 지원(2026-09-21)은 한 구간 안에서 분기 index가 같은 그룹들을 한 단위로 다뤘다. 타겟 목록에는 그 첫 그룹만 들어갔고, MUTATE_MATRIX와 MUTATE_CSW는 그 그룹들을 함께 바꿨다. 그래서 `LLR_MATRIX_2.txt`에 `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`을 주면 타겟 목록이 `[0]`이 되고 그룹 0(iteration 1)과 그룹 1(iteration 2~4)이 매번 함께 바뀌었다.

사용자 결정: 타겟 목록의 값은 그룹 하나하나의 index이고, 변이는 타겟 그룹 하나에만 들어간다 (SW 분기 지원 이전과 같은 방식).

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_MATRIX.Build_SW_Branch_Layout` | 그룹별 분기 index와 구간만 계산 |
| 2 | `LLR_OPT.Build_Target_Group_Indices` | 설정의 index를 그대로 타겟 목록에 담음 |
| 3 | `LLR_OPT._Get_Target_Group_Idx` | 변이할 타겟 그룹 하나의 index. `Generate_Random_Mutation`과 `Mutate_CSW`가 씀 |
| 4 | `LLR_OPT.Check_SW_Branch_Mode_Allowed` | 타겟 목록에 적힌 그룹만 보고 분기 그룹이 있는지 판단. 분기 그룹은 분기 index와 상관없이 타겟이 됨 |
| 5 | `LLR_OPT.Set_Gen_Trial_LLR_Mode`, `Bcast_Trial_LLR_Mode`, `Print_Mode_Target_Info`, `Initialize_Stage` | 타겟 그룹 하나만 정하고 알림 |

그대로 둔 것: 분기 구간의 iteration 검사(G2, G10), 헤더와 꼬리의 대조(H8), 분기 그룹이 타겟일 때의 모드 제한(MUTATE_MATRIX, MUTATE_CSW).

여러 분기로 갈라진 구간에서 마지막 분기만 갱신하던 규칙은 없앴다 (사용자 관측 2026-09-29: 타겟이 그룹 2가 되는 stage에서 "target g2 is SW branch 0 of the span iteration 5~8 (2 branches); DAO updates only the last branch (1)"로 중단). 바꿀 그룹을 타겟 목록으로 직접 고르므로 어느 분기를 바꿀지도 목록이 정한다. 이 규칙이 타겟 목록에서 마지막이 아닌 분기를 빼지 않아 기본 설정으로 중단되던 문제(2026-09-22 라이트 리뷰의 C1)도 함께 없어진다.

| `LLR_MATRIX_2.txt`에 준 목록 | 타겟 목록 | stage마다 바뀌는 그룹 |
|------|------|------|
| `[0, 1]` | `[0, 1]` | 그룹 0, 다음 바퀴에 그룹 1 |
| `[1, 4]` | `[1, 4]` | 그룹 1, 다음 바퀴에 그룹 4 |
| `[2, 3]` | `[2, 3]` | 그룹 2(구간 5~8의 분기 0), 다음 바퀴에 그룹 3(분기 1) |

### 3.4 HD 복호의 HBF 구간에서 변이와 난수 생성이 dv_idx 0의 TH를 건드리지 않게 (사용자 요청 2026-09-29)

사용자 관측: MUTATE_MATRIX가 iteration 1~4 그룹의 dv_idx 0 TH를 바꾸려 한다. HD 복호의 iteration 1~4는 언제나 HBF 구간이고 dv_idx 0의 TH는 0이어야 한다.

원인은 dv_idx 0의 TH를 빼는 규칙이 HBF 최적화 모드(`IS_HBF_OPT`)에 묶여 있던 것이다. `IS_HBF_OPT`의 기본값은 False이고 켜는 코드가 없어, 설정에서 직접 켜지 않은 HD 실행은 규칙 없이 돈다. 확인은 `LLR_MATRIX_2.txt`의 그룹 0(iteration 1)과 그룹 1(iteration 2~4)에서 경우마다 2000회 돌려 셌다.

| 경로 | `IS_HBF_OPT` True | `IS_HBF_OPT` False |
|------|------|------|
| MUTATE_MATRIX (조정 단계 포함)가 dv_idx 0의 TH를 고른 횟수 | 0 | 622~787 |
| 그룹 변이 공용 함수(`_generate_mutation_for_group`)가 고른 횟수 | 767 (뒤에 보정이 0으로 되돌림) | 737 |

사용자 지시에 따라 범위는 HBF 시퀀스(`Gen_LLR_Mode_HBF_SEQUENCE`)의 모드로 한정했다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_MATRIX.Get_Columns_Fixed_In_HBF_Iterations` (새 함수) | HD 복호(`init_n == 1`)이고 끝 iteration이 `HBF_MAX_ITERATION` 이하면 dv_idx 0의 TH column 목록, 아니면 빈 목록. `IS_HBF_OPT`를 보지 않음 |
| 2 | `LLR_OPT.Generate_Random_Mutation` (MUTATE_MATRIX) | 위 목록의 column을 변이 후보에서 뺌 |
| 3 | `LLR_OPT._generate_mutation_for_group` (SPLIT_GROUP, INSERT_MUTATED_GROUP) | 인자로 매트릭스를 받아 같은 column을 변이 후보에서 뺌 |
| 4 | `LLR_OPT._generate_random_row` (INSERT_RANDOM_GROUP, INSERT_RANDOM_ROW) | 끝 iteration을 받아 같은 column을 `HBF_OPT_TH_CONSTANT_VAL`로 채움 |
| 5 | `LLR_MATRIX.HBF_immutable_col_range` | 읽는 자리가 1번 함수로 옮겨 가 속성을 없앰 |

그대로 둔 것: 유효성 검사(HBF1, HBF2), 보정(`Correct_LLR_Matrix`), REGEN_DV, REGEN_ROW는 `IS_HBF_OPT`가 켜져 있을 때만 규칙을 건다. INSERT_MUTATED_ROW의 변이(`_generate_mutation_for_row`), COPY_ROWS, COPY_GROUP, SWAP_ROW는 HBF 구간 row의 dv_idx 0 TH를 바꿀 수 있다.

## 4. 수정 대상 파일

- `SRC/DAO_LLR_MATRIX.py`, `SRC/DAO_Main.py` (3.4절의 표), `DAO_spec.md` (3.6절 HBF3, 5.2절)
- `SRC/DAO_LLR_MATRIX.py`, `SRC/DAO_Main.py` (3.3절의 표), `_pm/tasks/20260921_SW_branch_DAO_support/review/checks/check_sw_branch.py`
- `SRC/DAO_LLR_MATRIX.py` (Is_Row_In_HBF_Iterations, Is_LLR_Valid, Read_Input_LLR_Matrix 주석, Correct_LLR_Matrix, Correct_Ch_Th_In_Row)
- `SRC/DAO_Main.py` (Gen_LLR_Regen_DV, Gen_LLR_Regen_Row, Generate_Random_Mutation, Build_Target_Group_Indices, Check_Fixed_Target_Group_Idx_List, Initialize_Stage, Initialize_LLR_Matrix, Update_Optimal_LLR, Validate_Config, Check_SW_Branch_Mode_Allowed 오류 문구)
- `SRC/DAO_Main.py` (Set_Seed_Mode), `SRC/DAO_Config.py` (HBF_OPT_CONFIG)
- `SRC/DAO_Config.py` (FIXED_TARGET_GROUP_IDX_LIST), `SRC/DAO_Constants.py` (FIXED_TARGET_GROUP_ALLOWED_MODES)
- `DAO_spec.md` (3.6절, 3.7절 최적화 규칙, 3.8절, 5.2절 특수 로직, 6.3절), `README.md` (타겟 그룹 설정, 3.4절, 4.1.1절)

## 5. 안전성 체크리스트

- ㉮ `IS_HBF_OPT`이 False인 실행은 `Is_Row_In_HBF_Iterations`가 항상 False라 유효성 검사, 보정, REGEN_DV, REGEN_ROW의 동작이 같다. HD 복호에서 달라지는 것은 3.4절의 모드가 HBF 구간 row의 dv_idx 0 TH를 그대로 두는 것 하나다. 2SD와 3SD는 `Get_Columns_Fixed_In_HBF_Iterations`가 빈 목록이라 동작이 같다
- ㉯ max_iteration이 4 이하인 HBF 매트릭스는 모든 row가 HBF 구간에 있으므로 동작이 같다
- ㉰ restart row는 유효성 검사와 보정 모두 HBF 규칙보다 앞에서 건너뛴다
- ㉱ `Correct_Ch_Th_In_Row`의 `is_row_in_HBF_iterations` 인자는 기본값이 False이고, row 없이 부르는 자리는 `_generate_random_row` 하나다. 끝 iteration을 받으면 3.4절의 규칙으로 값을 정하고, 받지 않으면(GEN_INITIAL_GROUP, GEN_SINGLE_ROW) False다. 그 결과는 `Gen_Trial_LLR`과 `Build_Single_Row_Matrix`에서 `Correct_LLR_Matrix`를 거친다
- ㉲ `FIXED_TARGET_GROUP_IDX_LIST`가 None인 실행은 타겟 목록이 `INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지다. 시작 직후(`Initialize_LLR_Matrix`), stage 시작(`Initialize_Stage`), 목록이 비었을 때의 복원(`Update_Optimal_LLR`)이 같은 함수로 만든다
- ㉳ `Build_Target_Group_Indices`는 잘못 적은 값(정수가 아닌 값, 범위 밖)을 건너뛰고, 알리는 일은 뒤이어 도는 `Validate_Config`가 맡는다. `Setup`이 `Initialize_LLR_Matrix` 다음에 `Validate_Config`를 부르기 때문이다

## 6. 미결정 사항

- ㉮ 그룹 수를 바꾸는 모드(INSERT_RANDOM_GROUP, SPLIT_GROUP 등)를 `FIXED_TARGET_GROUP_IDX_LIST`와 함께 쓰게 할지. 지금은 시작할 때 오류로 막는다. 함께 쓰려면 그룹이 늘거나 줄 때 목록의 index를 따라 옮기는 기능이 필요하다
- ㉯ HD 복호의 HBF 구간 규칙(dv_idx 0의 TH는 0)을 `IS_HBF_OPT`와 상관없이 어디까지 걸지. 지금은 3.4절의 모드만 따른다. 남은 자리는 ㉠ 나머지 모드(INSERT_MUTATED_ROW, REGEN_DV, REGEN_ROW, COPY_ROWS, COPY_GROUP, SWAP_ROW) ㉡ 유효성 검사와 보정이다. ㉡을 걸면 HBF 구간 row의 dv_idx 0 TH가 0이 아닌 HD 입력 매트릭스는 시작할 때 검증에서 멈춘다

## 7. 검증

- 검사: `_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py` 11건 (유효성 4, 보정 1, 변이 2, row 다시 만들기 2, DV 다시 만들기 2)
  - 첫 수정 전 소스(커밋 dff3dba의 SRC): 처음 쓴 9건 가운데 5건 실패. 유효성 검사 실패 문구가 사용자 관측과 같음
  - 수정 후 소스: 11건 통과
- 검사: `_test/20260928_fixed_target_group_idx_list/test_fixed_target_group_idx_list.py` 20건 (타겟 목록 만들기 7, stage마다 고르는 타겟 3, 설정 검사 10). 구현 전에는 모두 오류였고, 3.3절을 반영하기 전에는 분기 그룹을 하나씩 다루는 4건이 실패. 지금 22건 통과 (분기 0과 분기 1을 차례로 도는 2건 포함. 마지막 분기 규칙을 없애기 전에는 이 2건이 사용자 관측과 같은 문구로 중단)
- 검사: `_test/20260929_target_group_one_by_one/test_target_group_one_by_one.py` 8건 (MUTATE_MATRIX 4, MUTATE_CSW 2, 모드 허용 검사 2). 3.3절을 반영하기 전에는 4건 실패, 지금 8건 통과
- 검사: `check_sw_branch.py`를 3.3절에 맞게 고침 (41건 통과)
- 검사: `_test/20260928_hbf_seed_mode/test_hbf_seed_mode.py` 3건 (조건 9가지를 HBF 최적화 모드를 끈 채와 켠 채로 비교). 갈래를 없애기 전에는 HBF 쪽 조건 6가지가 보통 모드와 달랐고, 없앤 뒤 3건 통과
- 검사: `_test/20260929_hd_hbf_dv0_th_untouched/test_hd_hbf_dv0_th_untouched.py` 14건 (`IS_HBF_OPT`를 끈 HD 복호. 고정 column 3, MUTATE_MATRIX 3, 그룹 변이와 SPLIT_GROUP 3, INSERT_RANDOM_ROW 2, INSERT_RANDOM_GROUP 2, 끝 iteration을 모르는 row 1). 3.4절을 반영하기 전에는 10건 실패, 지금 14건 통과
- 기존 검사: `check_dao_fixes.py`, `check_sw_branch.py`, `_test/20260921_gather_uncors_matrix_arg/` 모두 통과
- 입력 매트릭스 `Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`(max_iteration 124)를 `is_HBF_OPT=True`로 읽으면 유효하고, 보정이 dv_idx 0의 CH와 TH를 바꾸지 않음. `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`이면 두 파일 모두 타겟 목록이 `[0, 1]`
- 남은 확인: 사용자 환경 MPI 실행에서 초기 매트릭스 검증 통과 여부, stage 로그의 `target_group_indices`가 지정한 그룹만 도는지
