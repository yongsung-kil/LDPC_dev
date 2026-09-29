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
| 3 | `FIXED_TARGET_GROUP_ALLOWED_MODES` (`DAO_Constants.py`) | 목록과 함께 쓰는 모드. 그룹 수, 순서, iteration 구간을 그대로 두는 10개 (MUTATE_MATRIX, MUTATE_CSW, SWAP_ROW, COPY_ROWS, COPY_GROUP, INSERT_RANDOM_ROW, INSERT_MUTATED_ROW, REGEN_DV, REGEN_ROW, DELETE_ROW). DELETE_ROW는 3.11절에서 더했다 |
| 4 | `LLR_OPT.Check_Fixed_Target_Group_Idx_List` (새 함수) | 목록의 꼴, 범위, 중복과 지금 쓰는 모드 시퀀스를 검사. `Validate_Config`가 시작할 때 부른다 |

허용 모드를 가른 기준은 코드에서 확인한 두 가지다. ㉮ 그룹을 넣거나 빼거나 순서를 바꾸는가 (`groups.insert`, `groups.pop`, `groups =`) ㉯ row의 `iter_start`나 `iter_end`를 바꾸는가. GEN_INITIAL_GROUP, REORDER_GROUP, INSERT_RANDOM_GROUP, INSERT_MUTATED_GROUP, SPLIT_GROUP, ADJUST_ITERATION, INSERT_RESTART_GROUP이 여기에 걸린다. 이 모드들이 그룹 번호를 밀면 목록의 index가 다른 그룹을 가리키게 된다. DELETE_ROW는 row가 하나 남은 그룹을 지울 때만 ㉮와 ㉯에 걸리므로, 목록을 쓰는 실행에서 그 그룹을 건너뛰게 하고 허용했다 (3.11절).

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

그대로 둔 것: 분기 구간의 iteration 검사(G2, G10), 헤더와 꼬리의 대조(H8), 분기 그룹이 타겟일 때의 모드 제한(허용 모드는 3.11절).

여러 분기로 갈라진 구간에서 마지막 분기만 갱신하던 규칙은 없앴다 (사용자 관측 2026-09-29: 타겟이 그룹 2가 되는 stage에서 "target g2 is SW branch 0 of the span iteration 5~8 (2 branches); DAO updates only the last branch (1)"로 중단). 바꿀 그룹을 타겟 목록으로 직접 고르므로 어느 분기를 바꿀지도 목록이 정한다. 이 규칙이 타겟 목록에서 마지막이 아닌 분기를 빼지 않아 기본 설정으로 중단되던 문제(2026-09-22 라이트 리뷰의 C1)도 함께 없어진다.

| `LLR_MATRIX_2.txt`에 준 목록 | 타겟 목록 | stage마다 바뀌는 그룹 |
|------|------|------|
| `[0, 1]` | `[0, 1]` | 그룹 0, 다음 바퀴에 그룹 1 |
| `[1, 4]` | `[1, 4]` | 그룹 1, 다음 바퀴에 그룹 4 |
| `[2, 3]` | `[2, 3]` | 그룹 2(구간 5~8의 분기 0), 다음 바퀴에 그룹 3(분기 1) |

### 3.4 HD 복호의 HBF 구간에서 trial을 만드는 모드가 dv_idx 0의 TH를 건드리지 않게 (사용자 요청 2026-09-29)

사용자 관측: MUTATE_MATRIX가 iteration 1~4 그룹의 dv_idx 0 TH를 바꾸려 한다. HD 복호의 iteration 1~4는 언제나 HBF 구간이고 dv_idx 0의 TH는 0이어야 한다.

원인은 dv_idx 0의 TH를 빼는 규칙이 HBF 최적화 모드(`IS_HBF_OPT`)에 묶여 있던 것이다. `IS_HBF_OPT`의 기본값은 False이고 켜는 코드가 없어, 설정에서 직접 켜지 않은 HD 실행은 규칙 없이 돈다. 확인은 `LLR_MATRIX_2.txt`의 그룹 0(iteration 1)과 그룹 1(iteration 2~4)에서 경우마다 2000회 돌려 셌다.

| 경로 | `IS_HBF_OPT` True | `IS_HBF_OPT` False |
|------|------|------|
| MUTATE_MATRIX (조정 단계 포함)가 dv_idx 0의 TH를 고른 횟수 | 0 | 622~787 |
| 그룹 변이 공용 함수(`_generate_mutation_for_group`)가 고른 횟수 | 767 (뒤에 보정이 0으로 되돌림) | 737 |

범위는 사용자가 두 번에 나눠 정했다. 첫 지시는 HBF 시퀀스(`Gen_LLR_Mode_HBF_SEQUENCE`)의 모드였고(표의 1~5번, 커밋 f843c7a), 이어진 결정(6절 ㉯의 선택지 가운데 나머지 모드까지, 유효성 검사와 보정은 그대로)으로 값을 쓰는 나머지 모드를 더했다(표의 6~11번).

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_MATRIX.Get_Columns_Fixed_In_HBF_Iterations` (새 함수) | HD 복호(`init_n == 1`)이고 끝 iteration이 `HBF_MAX_ITERATION` 이하면 dv_idx 0의 TH column 목록, 아니면 빈 목록. `IS_HBF_OPT`를 보지 않음 |
| 2 | `LLR_OPT.Generate_Random_Mutation` (MUTATE_MATRIX) | 위 목록의 column을 변이 후보에서 뺌 |
| 3 | `LLR_OPT._generate_mutation_for_group` (SPLIT_GROUP, INSERT_MUTATED_GROUP) | 인자로 매트릭스를 받아 같은 column을 변이 후보에서 뺌 |
| 4 | `LLR_OPT._generate_random_row` (INSERT_RANDOM_GROUP, INSERT_RANDOM_ROW) | 끝 iteration을 받아 같은 column을 `HBF_OPT_TH_CONSTANT_VAL`로 채움 |
| 5 | `LLR_MATRIX.HBF_immutable_col_range` | 읽는 자리가 1번 함수로 옮겨 가 속성을 없앰 |
| 6 | `LLR_MATRIX.Fill_Columns_Fixed_In_HBF_Iterations` (새 함수) | 받은 값 배열에서 1번 함수의 column을 `HBF_OPT_TH_CONSTANT_VAL`로 채움 |
| 7 | `LLR_OPT.Gen_LLR_Insert_Mutated_Row`, `_generate_mutation_for_row` (INSERT_MUTATED_ROW) | 복사해 온 값을 6번 함수로 채우고, 변이 후보에서 같은 column을 뺌 (`fixed_columns` 인자) |
| 8 | `LLR_OPT.Gen_LLR_Insert_Mutated_Group` (INSERT_MUTATED_GROUP) | 복사해 온 값을 6번 함수로 채움 |
| 9 | `LLR_OPT.Gen_LLR_Regen_DV`, `Gen_LLR_Regen_Row` (REGEN_DV, REGEN_ROW) | 값은 TH까지 난수로 만들어 두고, 쓰는 자리가 HBF 구간 row의 dv_idx 0이면 TH를 상수로 바꿔 씀. 다시 쓰는 흐름(재사용 모드)도 같음 |
| 10 | `LLR_OPT.Copy_Row`, `Copy_Group` (COPY_ROWS, COPY_GROUP) | 복사한 값을 6번 함수로 채움 |
| 11 | `LLR_OPT.Gen_LLR_Swap_Row` (SWAP_ROW) | 1번 함수의 column을 빼고 맞바꿈 |

9번은 REGEN_DV가 HBF 구간 row의 dv_idx 0 자리에 만든 값(TH 0 0 0)을 다른 DV 자리로 옮기던 동작도 함께 없앤다 (라이트 리뷰의 LOW 발견). 10번은 `Copy_Group`이 복사한 값을 다루는 규칙이고, 분기 표시를 다루는 규칙은 3.9절에 있다.

그대로 둔 것: 유효성 검사(HBF1, HBF2)와 보정(`Correct_LLR_Matrix`)은 `IS_HBF_OPT`가 켜져 있을 때만 규칙을 건다. 그룹의 iteration을 옮기는 모드(REORDER_GROUP, ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP)는 값을 쓰지 않아 이 규칙이 걸리지 않는다. 이 모드가 iteration 5 이상의 그룹을 HBF 구간으로 옮기면 `IS_HBF_OPT`가 꺼진 실행에서는 그 그룹의 dv_idx 0 TH가 그대로 남는다.

### 3.5 HBF 최적화 모드에서 2단계 테스트 사용 (사용자 요청 2026-09-29)

사용자 결정: HBF 최적화 모드는 uncor 사용과 테스트 방식에서 보통 모드와 똑같이 동작한다.

`Validate_Config`는 2단계 테스트(`ENABLE_TWO_STAGE_TEST`: trial을 Partial uncor로 먼저 돌리고 개선된 trial만 Full uncor로 다시 돌리는 방식)와 `IS_HBF_OPT`를 함께 켜면 "Two-Stage 모드는 IS_HBF_OPT=True와 함께 사용할 수 없습니다."로 멈췄다. 이 검사는 반입 커밋(2811bff)부터 있었고, 2단계 테스트 개발 기록(`reference/_dev_log/20260406_two_stage_test/two_stage_test.md`)에는 까닭이 "HBF 최적화와 비호환" 한 줄뿐이다.

코드에서 찾은 충돌은 3.2절의 HBF 전용 seed 갈래 하나다. `HBF_OPT_USING_UNCOR`가 False면 seed 모드가 DEFAULT(난수 프레임)가 되어 Partial 테스트가 Partial 풀을 읽지 않는다. 보통 모드는 uncor 로드 모드가 LOAD_NONE일 때 2단계 테스트를 막는 검사로 이 경우를 거르는데, HBF 전용 갈래는 uncor 로드 모드를 보지 않아 그 검사에 걸리지 않았다. 갈래가 없어진 지금은 HBF 최적화 모드도 그 검사로 걸러진다.

| 확인한 것 | 결과 |
|------|------|
| 2단계 테스트 흐름의 함수(`Test_Initial_LLR`, `_Build_Initial_Partial_Pool`, `Rebuild_Partial_Pool`, `_Restore_State_After_Partial_Rebuild`, `Test_Trial_LLR`, `Check_Partial_Improvement`, `Determine_Update_Decision`)가 `IS_HBF_OPT`를 읽는지 | 읽는 자리 없음 |
| seed 모드 (초기 Full 테스트, trial의 Partial과 Full 테스트, Partial 풀 다시 만들기) | `IS_HBF_OPT`를 켠 채와 끈 채가 같음 |
| trial 테스트가 도는 순서 (Partial 개선 시 Partial 다음 Full, 아니면 Partial만) | `IS_HBF_OPT`를 켠 채와 끈 채가 같음 |

수정은 `Validate_Config`에서 그 검사를 없앤 것 하나다. 2단계 테스트의 나머지 제한(REDECODE, GEN_SINGLE_ROW, LOAD_NONE, LOAD_VECTOR)은 그대로이고 `IS_HBF_OPT`와 상관없이 걸린다.

`IS_HBF_OPT`가 바꾸는 것은 세 가지가 남는다. ㉮ 모드 시퀀스(`Gen_LLR_Mode_HBF_SEQUENCE`) ㉯ 유효성 검사 HBF1과 HBF2 ㉰ 보정이 HBF 구간 row의 dv_idx 0 TH를 상수로 덮어쓰는 것.

### 3.6 iteration 구간 경계와 시작 검사 (라이트 리뷰 F1, F2, F6, 사용자 결정 2026-09-29)

사용자 결정: ㉮ iteration 8과 9 사이 경계도 검사한다 ㉯ 모드 시퀀스의 SW 분기 제한을 시작할 때 검사한다 ㉰ 문서에 HBF 최적화 모드의 사용 조건을 적는다. 라이트 리뷰의 F4와 F5는 3.8절, F3은 3.9절에서 다룬다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `HBF_OPT_CONFIG.ITERATION_SPAN_ENDS` | row가 걸칠 수 없는 경계의 목록. 기본값 4와 8 (구간 1~4, 5~8, 9 이후). 값 e는 iteration e와 e + 1 사이를 뜻한다 |
| 2 | `LLR_MATRIX.Get_Iteration_Span_Ends` (새 함수) | `HBF_MAX_ITERATION`과 `ITERATION_SPAN_ENDS`를 합친 경계 목록. `HBF_MAX_ITERATION`은 설정에 없어도 언제나 경계다 |
| 3 | `LLR_MATRIX.Get_Iteration_Span_End_Crossed_By_Row` (새 함수) | HBF 최적화 모드에서 row가 걸치는 첫 경계. 걸치지 않으면 None |
| 4 | `LLR_MATRIX.Is_LLR_Valid`의 HBF2 | 3번으로 판단. 오류 문구에 걸친 경계와 경계 목록을 적음 |
| 5 | `LLR_OPT.Check_Mode_Sequence_With_SW_Branch` (새 함수) | 지금 쓰는 시퀀스의 모드마다 `Check_SW_Branch_Mode_Allowed`를 돌려 막히는 모드를 모음 |
| 6 | `LLR_OPT.Validate_Config` | 최적화 실행이고 초기 매트릭스가 있으면 5번을 부름. 목록을 준 실행과 주지 않은 실행 모두 |

경계 검사는 HBF 최적화 모드에서만 건다 (HBF1, HBF2와 같은 조건). 달라지는 동작은 하나다: SW 분기가 없는 매트릭스에서 INSERT_RANDOM_GROUP이 iteration 2~4 그룹 뒤에 붙이는 새 그룹(5~24)이 8과 9 사이를 걸쳐 버려진다. iteration 5~8 그룹 뒤에 붙이는 새 그룹(9~28)은 통과한다.

시작 검사는 stage 검사(`Set_Gen_Trial_LLR_Mode`)와 같은 함수로 같은 타겟 목록을 본다. 타겟 목록과 분기 배치가 시작할 때 정해지므로 두 검사의 결과가 같고, 달라지는 것은 알리는 때다. stage 검사는 그대로 둔다.

### 3.7 모드 시퀀스를 이름으로 적고 쓸 수 있는 모드를 모두 담음 (사용자 요청 2026-09-29)

사용자 요청: `Gen_LLR_Mode_HBF_SEQUENCE`의 값을 숫자 대신 이름(`GenLLRModeHBF.MUTATE_MATRIX` 꼴)으로 적고 쓸 수 있는 모드를 모두 담는다. `Gen_LLR_Mode_SEQUENCE`도 똑같이 한다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `DAO_CONFIG.Gen_LLR_Mode_SEQUENCE` | `GenLLRMode`의 멤버 17개를 모두 이름으로 적음 (전에는 숫자 12개) |
| 2 | `DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE` | `GenLLRModeHBF`의 멤버를 이름으로 적음 (전에는 숫자 5개). 담는 모드는 3.12절에서 정한 10개. 순서: INSERT_RANDOM_ROW, INSERT_MUTATED_ROW, MUTATE_MATRIX, MUTATE_CSW, COPY_GROUP, SWAP_ROW, COPY_ROWS, REGEN_DV, REGEN_ROW, DELETE_ROW |
| 3 | `Set_Configs_Manually`의 프리셋 세 곳 (SIM_IDX 10, 20, 30) | 값은 그대로 두고 이름으로 적음 (REORDER_GROUP, MUTATE_MATRIX, MUTATE_CSW, REORDER_GROUP) |
| 4 | `LLR_OPT.Set_Gen_Trial_LLR_Mode` | 시퀀스의 원소를 `GenLLRMode`의 멤버로 읽음. 원소가 `GenLLRMode`의 멤버든 `GenLLRModeHBF`의 멤버든 숫자든 `current_gen_trial_LLR_mode`는 `GenLLRMode`의 멤버 |
| 5 | `LLR_OPT.Get_Mode_Sequence_Str` | 로그에 찍는 시퀀스를 값(숫자)으로 고정 |
| 6 | `GenLLRModeHBF` (`DAO_Constants.py`) | COPY_ROWS, REGEN_DV, REGEN_ROW 멤버를 더함 (값은 같은 이름의 `GenLLRMode` 값). 사용자 결정(2026-09-29)이고, 이때 넣지 않은 모드는 REORDER_GROUP, INSERT_MUTATED_GROUP, INSERT_MUTATED_ROW, ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP. 멤버의 최종 구성은 3.12절 |

두 목록은 돌릴 모드를 고르는 바탕이다. 보통 목록은 GEN_INITIAL_GROUP을 맨 앞에 두었다. 이 모드는 stage 1에서만 돌고 다른 stage에서는 건너뛰므로, 맨 앞이 아니면 목록에 있어도 돌지 않는다. 보통 목록의 나머지는 값이 작은 순서이고, HBF 목록은 `GenLLRModeHBF`에 적힌 순서다.

5번의 까닭: 파이썬 3.11 미만에서 `str(IntEnum 멤버)`는 "GenLLRMode.MUTATE_MATRIX" 꼴이고 3.11부터는 "10"이다. 실행 환경의 파이썬 판과 상관없이 로그가 같도록 `int()`로 바꿔 찍는다. 시퀀스를 읽는 다른 자리(`Validate_Config`, `Check_Fixed_Target_Group_Idx_List`, `Check_Mode_Sequence_With_SW_Branch`)는 이미 `int(값)`으로 읽는다.

기본 목록을 그대로 둔 실행에서 달라지는 것 (프리셋 SIM_IDX 10, 20, 30은 자기 시퀀스를 쓰므로 그대로다):

| 경우 | 결과 |
|------|------|
| 매트릭스에 SW 분기 그룹이 있음, 보통 모드 | 시작 검사에서 멈춤. 목록에 GEN_INITIAL_GROUP이 있기 때문 (문구: "mode GEN_INITIAL_GROUP replaces every group, so it is not allowed while the matrix has SW branch groups"). 전의 보통 목록에는 이 모드가 없었음 |
| 타겟에 SW 분기 그룹이 있음 | 시작 검사에서 멈춤. MUTATE_MATRIX와 MUTATE_CSW만 남겨야 함 (전의 기본 목록도 같았음) |
| `FIXED_TARGET_GROUP_IDX_LIST`를 씀 | 시작 검사에서 멈춤. `FIXED_TARGET_GROUP_ALLOWED_MODES`의 모드만 남겨야 함 (전의 기본 목록도 같았음) |
| SW 분기가 없는 매트릭스, 보통 모드 | stage 1이 GEN_INITIAL_GROUP (전에는 MUTATE_MATRIX). 모든 그룹을 난수 그룹 하나로 바꾼 trial을 만듦 |
| SW 분기가 없는 매트릭스, HBF 최적화 모드 | GEN_INITIAL_GROUP(iteration 1~20)과 INSERT_RANDOM_GROUP(20칸)을 목록에 적으면 기본 설정값으로는 trial이 경계 검사(HBF2)로 모두 버려짐 (40회씩 돌려 확인). 기본 목록은 두 모드를 뺀 9개 (3.10절) |

HBF 최적화 모드에서 SW 분기가 없는 4그룹 매트릭스(iteration 1~1, 2~4, 5~8, 9~20)의 타겟 그룹 1(2~4)에 모드마다 trial을 만들어 본 결과: INSERT_RANDOM_ROW, MUTATE_MATRIX, MUTATE_CSW, SPLIT_GROUP, COPY_GROUP, SWAP_ROW, COPY_ROWS, REGEN_DV, REGEN_ROW는 유효한 trial이 나오고, GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP은 기본 설정값에서 모두 무효다. COPY_ROWS, REGEN_DV, REGEN_ROW는 trial 4개씩 만들어 모두 유효했고 dv_idx 0의 TH가 0 0 0으로 남았다.

### 3.8 헛도는 실행을 미리 막기 (라이트 리뷰 F4, F5, 사용자 결정 2026-09-29)

사용자 결정: ㉮ 타겟 그룹의 row가 하나뿐이면 MUTATE_CSW stage를 건너뛴다 ㉯ GEN_SINGLE_ROW와 HBF 최적화 모드를 함께 쓰면 시작할 때 오류를 내고 멈춘다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_OPT.Set_Gen_Trial_LLR_Mode` | 모드가 MUTATE_CSW이고 타겟 그룹의 row가 2개 미만이면 그 stage의 trial 수를 0으로 둔다 (restart 그룹을 건너뛰는 것과 같은 방식). 로그에 "Target g{번호} has a single row (no CSW to mutate), skipping this stage"를 남긴다 |
| 2 | `LLR_OPT.Validate_Config` | 실행 모드가 GEN_SINGLE_ROW이고 `IS_HBF_OPT`가 켜져 있으며 후보 row(iteration 1~`CANDIDATE_ITERATION`)가 구간 경계를 걸치면 오류. 문구에 걸치는 경계를 적는다 |

1번의 까닭: 그룹의 첫 row는 CSW가 -1로 고정이라 row가 하나뿐이면 바꿀 CSW가 없다. `Gen_LLR_Mutate_CSW`는 바뀌지 않은 매트릭스를 돌려주고 `Gen_Trial_LLR`은 이것을 생성 성공으로 보아, 그 stage의 trial이 모두 같은 매트릭스를 측정했다. 건너뛴 stage는 유효한 trial이 없는 stage로 세어지고, 이런 stage가 시퀀스 길이의 두 배만큼 이어지면 최적화가 끝난다 (restart 그룹과 같은 규칙).

2번의 조건: `CANDIDATE_ITERATION`이 첫 경계(4) 이하이면 후보 row가 구간 1~4 안에 있어 걸치지 않으므로 오류가 아니다. 기본값 50은 경계 4와 8을 걸친다.

### 3.9 COPY_GROUP이 타겟 그룹의 분기 표시를 그대로 둠 (라이트 리뷰 F3, 사용자 결정 2026-09-29)

COPY_GROUP은 타겟 그룹의 row를 후보 그룹의 row로 통째로 바꾸는 모드다. 후보의 값과 CSW뿐 아니라 SW 분기 표시(row의 `floor_flag`와 헤더 `type_each_group`)까지 타겟에 옮겼다. `LLR_MATRIX_2.txt`에서 보통 그룹 5(iteration 9~24)에 분기 그룹 0을 복사하면 그룹 5의 헤더가 1에서 10으로, row 꼬리가 -1에서 0으로 바뀌어 iteration 9~24에 새 분기 구간이 생겼고, 이 매트릭스가 유효성 검사를 지났다.

사용자 결정: 값과 CSW만 복사하고 타겟 그룹의 분기 표시는 그대로 둔다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_OPT.Copy_Group`의 row | 새 row의 `floor_flag`는 타겟 그룹의 값. iteration도 타겟 그룹의 값 |
| 2 | `LLR_OPT.Copy_Group`의 헤더 | 타겟과 후보가 모두 보통 그룹(row 꼬리 -1)이면 그룹 유형(10 미만의 값)은 후보의 것을 따름. 타겟이나 후보가 분기 그룹이면 타겟의 헤더 값을 그대로 둠 |

후보 목록(`Get_Copy_Group_Candidates`)은 그대로다. 분기 그룹도 후보가 되어 값과 CSW를 내준다.

`LLR_MATRIX_2.txt`에서 복사 뒤 타겟 그룹의 헤더와 row 꼬리를 수정 전 소스(커밋 a615e94)와 수정 후 소스로 견준 결과다. 타겟 그룹의 iteration은 두 소스 모두 그대로다.

| 타겟 (헤더, 꼬리, iteration) | 후보 (헤더, 꼬리) | 수정 전의 타겟 | 수정 후의 타겟 |
|------|------|------|------|
| 그룹 5 (1, -1, 9~24) | 그룹 0 (10, 0) | 10, 0. 유효 (iteration 9~24에 분기 구간이 생김) | 1, -1. 유효 |
| 그룹 5 (1, -1, 9~24) | 그룹 2 (20, 0) | 20, 0. 무효 (trial이 버려짐) | 1, -1. 유효 |
| 그룹 5 (1, -1, 9~24) | 그룹 3 (21, 1) | 21, 1. 무효 (trial이 버려짐) | 1, -1. 유효 |
| 그룹 3 (21, 1, 5~5) | 그룹 6 (1, -1) | 1, -1. 무효 (trial이 버려짐) | 21, 1. 유효 |

### 3.10 HBF 기본 시퀀스에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 뺌 (사용자 결정 2026-09-29)

두 모드는 새 그룹을 만든다. GEN_INITIAL_GROUP은 모든 그룹을 iteration 1~20짜리 그룹 하나로 바꾸고, INSERT_RANDOM_GROUP은 타겟 그룹 뒤에 iteration 20칸짜리 그룹을 넣는다 (둘 다 기본 설정값). HBF 최적화 모드에서는 이 그룹이 구간 경계(4와 8)를 걸쳐 trial이 버려진다. GEN_INITIAL_GROUP의 trial은 언제나 버려지고, INSERT_RANDOM_GROUP의 trial은 타겟이 iteration 1~8 안에 있을 때 버려진다 (3.7절의 표).

사용자 결정: HBF 기본 시퀀스에서 두 모드를 뺀다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE` | `GenLLRModeHBF`에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 뺀 9개 (최종 구성은 3.12절) |
| 2 | `GenLLRModeHBF` (`DAO_Constants.py`) | 이 시점에는 멤버 11개 그대로. 3.12절에서 두 모드를 멤버에서도 뺐다 |

기본 목록을 그대로 둔 HBF 최적화 모드의 실행에서 달라지는 것:

| 경우 | 결과 |
|------|------|
| stage 1의 모드 | INSERT_RANDOM_ROW (전에는 GEN_INITIAL_GROUP) |
| 시퀀스 한 바퀴 | 9 stage (전에는 11). 타겟은 한 바퀴마다 다음 그룹으로 넘어가므로 9 stage마다 바뀜 |
| 유효한 trial이 없는 stage가 이어질 때의 종료 | 18 stage (시퀀스 길이의 두 배. 전에는 22) |
| `LLR_MATRIX_2.txt`, 타겟이 분기 구간 뒤의 보통 그룹(그룹 5 이후) | 시작 검사 통과 (전에는 GEN_INITIAL_GROUP 때문에 멈춤) |
| `LLR_MATRIX_2.txt`, 타겟에 분기 그룹이 있음 | 이 시점에는 시작 검사에서 멈춤 (SPLIT_GROUP). 3.12절의 기본 목록으로는 통과 |

### 3.11 분기 그룹 타겟에 그룹 배치를 그대로 두는 모드를 허용 (사용자 관측과 설명 2026-09-29)

사용자 관측: `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`과 HBF 시퀀스(INSERT_RANDOM_ROW, COPY_ROWS, REGEN_DV, REGEN_ROW, DELETE_ROW 포함)로 돌리면 시작 검사가 아래 두 가지로 멈춘다.

```
Gen_LLR_Mode_HBF_SEQUENCE contains DELETE_ROW (70), which change the number, order or iteration of groups, so they cannot run with FIXED_TARGET_GROUP_IDX_LIST.
Gen_LLR_Mode_HBF_SEQUENCE: target groups [0, 1] are SW branch groups, so mode INSERT_RANDOM_ROW (41) is not allowed.
```

사용자 설명: 모드 제한의 까닭은 SW 분기가 아니다. 디코더 실행 파일이 HBF 최적화가 다루는 구간에서 ㉮ 그룹 수가 바뀌는 것 ㉯ iteration이 바뀌는 것 ㉰ SW 분기가 더해지는 것을 받지 않는 것이 까닭이다. 그룹 안의 row 수가 바뀌는 것은 받는다. SW 분기 지원(2026-09-21)은 이 제한을 분기 그룹이 있을 때의 규칙으로 넣었다.

사용자 결정: REGEN_DV, REGEN_ROW, COPY_ROWS, DELETE_ROW, INSERT_RANDOM_ROW를 이 구간에서 쓴다. DELETE_ROW는 row 1개짜리 그룹을 건너뛴다 (MUTATE_CSW와 같은 방식).

| # | 위치 | 내용 |
|---|------|------|
| 1 | `GROUP_LAYOUT_KEEPING_MODES` (`DAO_Constants.py`, 새 상수) | 그룹 배치(그룹 수, 그룹 순서, iteration 구간, SW 분기 표시)를 그대로 두는 모드 10개: MUTATE_MATRIX, MUTATE_CSW, SWAP_ROW, COPY_ROWS, COPY_GROUP, INSERT_RANDOM_ROW, INSERT_MUTATED_ROW, REGEN_DV, REGEN_ROW, DELETE_ROW |
| 2 | `SW_BRANCH_ALLOWED_MODES`, `FIXED_TARGET_GROUP_ALLOWED_MODES` | 둘 다 1번의 모드 (전에는 앞의 것이 2개, 뒤의 것이 DELETE_ROW를 뺀 9개) |
| 3 | `MODES_EXEMPT_FROM_PROTECTED_GROUP_CHECK` (새 상수) | 타겟 앞 그룹의 보호 검사를 거치지 않는 모드. MUTATE_MATRIX와 MUTATE_CSW (전과 같은 두 모드) |
| 4 | `LLR_OPT.Is_Group_Layout_Kept` (새 함수) | 그룹 배치를 그대로 두는 실행인지 판단. HBF 최적화 모드, `FIXED_TARGET_GROUP_IDX_LIST`로 타겟을 지정한 실행, 타겟에 분기 그룹이 있는 실행 |
| 5 | `LLR_OPT._Build_Delete_Row_Candidates` | 4번이 참이면 row가 하나인 그룹을 후보에서 뺌 |
| 6 | `LLR_OPT.Init_Delete_Row_Mode` | 후보가 없으면 그 stage의 trial 수를 0으로 둠 |
| 7 | `LLR_OPT.Set_Gen_Trial_LLR_Mode` | 모드가 SWAP_ROW이고 타겟 그룹의 row가 2개 미만이면 그 stage의 trial 수를 0으로 둠 (전에는 오류로 멈춤) |
| 8 | `LLR_OPT.Check_SW_Branch_Mode_Allowed` | 오류 문구에 허용 모드가 지키는 것(그룹 수, 순서, iteration, SW 분기)을 적음 |

2번에 SWAP_ROW, COPY_GROUP, INSERT_MUTATED_ROW를 함께 넣은 까닭: 사용자가 든 다섯 모드와 같은 기준(그룹 배치를 그대로 둠)을 지난다. COPY_GROUP은 3.9절로 분기 표시를 그대로 둔다.

5번의 까닭: DELETE_ROW는 row가 하나 남은 그룹을 만나면 그룹째 지우고 그 iteration을 앞뒤 그룹에 나눠 준다 (`_Build_Deleted_Row_Matrix`의 Case B). 그룹 수와 iteration이 함께 바뀌므로, 그룹 배치를 그대로 두는 실행에서는 그 그룹을 후보에서 뺀다. 후보는 round마다 다시 만들므로 row가 줄어 하나 남은 그룹도 다음 round에서 빠진다.

7번의 까닭: `LLR_MATRIX_2.txt`의 그룹 0과 3, `LLR_MATRIX_1.txt`의 그룹 0과 4는 row가 하나다. SWAP_ROW를 분기 그룹 타겟에 허용하면 이 그룹이 타겟인 stage에서 "SWAP_ROW requires target group with 2+ rows"로 실행이 멈춘다.

분기 그룹에 모드마다 trial을 6개씩 만들어 본 결과 (모드 제한 검사를 거치지 않고 생성 함수를 직접 부름, `LLR_MATRIX_1.txt`의 그룹 0~5와 `LLR_MATRIX_2.txt`의 그룹 0~4):

| 모드 | 결과 |
|------|------|
| INSERT_RANDOM_ROW, INSERT_MUTATED_ROW | 만들어진 trial은 모두 유효하고 그룹 배치가 그대로 (CSW를 넣을 자리가 없어 trial이 나오지 않은 경우가 그룹마다 0~2회) |
| COPY_ROWS, COPY_GROUP, REGEN_DV, REGEN_ROW | 6개 모두 유효하고 그룹 배치가 그대로 |
| SWAP_ROW | row가 2개 이상인 그룹에서 6개 모두 유효하고 그룹 배치가 그대로 |
| DELETE_ROW | `LLR_MATRIX_2.txt`의 타겟 0과 1에서 후보 7개(그룹 1의 row)가 모두 유효하고 그룹 배치가 그대로 |
| SPLIT_GROUP | 그룹 수가 바뀜 (막는 모드) |

### 3.12 HBF 최적화 모드의 모드 제한을 SW 분기와 떼어 놓고 기본 시퀀스를 허용 모드 10개로 맞춤 (사용자 결정 2026-09-29)

3.11절의 사용자 설명대로면 모드 제한의 까닭은 디코더 실행 파일이 HBF 최적화가 다루는 구간에서 그룹 배치의 변화를 받지 않는 것이다. 그런데 3.11절까지의 제한은 타겟에 SW 분기 그룹이 있을 때만 걸려, SW 분기가 없는 매트릭스는 HBF 최적화 모드에서도 SPLIT_GROUP처럼 그룹 수를 바꾸는 모드가 돌았다. 그리고 HBF 기본 시퀀스에 SPLIT_GROUP이 남아 있어 `LLR_MATRIX_2.txt`의 분기 그룹을 타겟으로 두면 기본 목록 그대로는 시작 검사에서 멈췄다.

사용자 결정: ㉮ `IS_HBF_OPT`가 켜져 있으면 SW 분기가 있든 없든 그룹 배치를 그대로 두는 모드 10개만 허용한다 ㉯ HBF 기본 시퀀스에서 SPLIT_GROUP을 빼고 DELETE_ROW와 INSERT_MUTATED_ROW를 넣는다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_OPT.Check_HBF_Optimization_Mode_Allowed` (새 함수) | `IS_HBF_OPT`가 켜져 있고 모드가 `GROUP_LAYOUT_KEEPING_MODES` 밖이면 막는 이유를 돌려줌. SW 분기의 유무와 타겟 목록은 보지 않음 |
| 2 | `LLR_OPT.Check_Mode_Sequence_In_HBF_Optimization` (새 함수) | `Gen_LLR_Mode_HBF_SEQUENCE`의 모드마다 1번을 돌려 막히는 모드를 모음 |
| 3 | `LLR_OPT.Validate_Config` | 최적화 실행이면 2번을 부름 (T6). SW 분기 검사(T5)와 타겟 목록 검사(T4)는 그대로 |
| 4 | `LLR_OPT.Set_Gen_Trial_LLR_Mode` | stage마다 1번으로 그 stage의 모드를 검사 (SW 분기 검사 다음) |
| 5 | `GenLLRModeHBF` (`DAO_Constants.py`) | 그룹 배치를 그대로 두는 모드 10개와 같게 맞춤. INSERT_MUTATED_ROW와 DELETE_ROW를 더하고 GEN_INITIAL_GROUP, INSERT_RANDOM_GROUP, SPLIT_GROUP을 뺌 |
| 6 | `DAO_CONFIG.Gen_LLR_Mode_HBF_SEQUENCE` | `GenLLRModeHBF`의 모드 10개를 모두 적은 목록. 순서는 3.7절의 표 2번 |

5번에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 멤버에서도 뺀 까닭: ㉮로 HBF 최적화 모드에서 돌 수 없는 모드가 되어, 시퀀스에 이름을 적어도 시작 검사에서 멈춘다. `GenLLRModeHBF`는 HBF 최적화 모드에 쓰는 모드의 목록이므로 돌 수 없는 모드를 담지 않는다. 사용자가 든 것은 SPLIT_GROUP 하나이고 두 모드는 같은 기준으로 뺐다.

오류 문구 (새 문구): `Gen_LLR_Mode_HBF_SEQUENCE: mode SPLIT_GROUP (60) changes the number, order or iteration of groups, which the decoder does not accept in the iterations HBF optimization covers (IS_HBF_OPT=True). Allowed modes: ...`

HBF 최적화 모드의 실행에서 달라지는 것:

| 경우 | 결과 |
|------|------|
| SW 분기가 없는 매트릭스, 시퀀스에 그룹 배치를 바꾸는 모드가 있음 | 시작 검사에서 멈춤 (전에는 돌았음) |
| 기본 목록을 그대로 둔 실행의 시퀀스 한 바퀴 | 10 stage (전에는 9). 유효한 trial이 없는 stage가 이어질 때의 종료는 20 stage |
| 기본 목록을 그대로 둔 실행의 stage 2 | INSERT_MUTATED_ROW (전에는 MUTATE_MATRIX). stage 1은 전과 같이 INSERT_RANDOM_ROW |
| `LLR_MATRIX_2.txt`, 타겟에 분기 그룹이 있음, 기본 목록 | 시작 검사 통과 (전에는 SPLIT_GROUP 때문에 멈춤) |
| `IS_HBF_OPT`를 끈 실행 | 같음 |

SW 분기가 없는 4그룹 매트릭스의 타겟 그룹 1(iteration 2~4, row 2개)에 새로 들어간 두 모드로 trial을 만들어 본 결과: INSERT_MUTATED_ROW는 trial 3개가 모두 유효하고 그룹 배치가 그대로이며 dv_idx 0의 TH가 0 0 0으로 남았다. DELETE_ROW는 후보 2개(그룹 1의 row)로 만든 trial 2개가 모두 유효하고 그룹 배치가 그대로이며 남은 row의 CSW가 -1이다.

## 4. 수정 대상 파일

- `SRC/DAO_Main.py` (3.12절의 1~4번), `SRC/DAO_Constants.py` (GenLLRModeHBF, GROUP_LAYOUT_KEEPING_MODES 주석), `SRC/DAO_Config.py` (Gen_LLR_Mode_HBF_SEQUENCE와 시퀀스 주석), `DAO_spec.md` (3.6절 HBF4와 ㉸, 3.7절 ㉲㉳, 3.8절 ㉰와 T6), `README.md` (GenLLRMode 시퀀스, 3.4절 ㉮, 4.1.1절)
- `SRC/DAO_Constants.py` (3.11절의 1~3번), `SRC/DAO_Main.py` (3.11절의 4~8번과 Gen_Trial_LLR의 보호 검사 조건), `SRC/DAO_Config.py` (시퀀스 주석), `DAO_spec.md` (3.6절 ㉵, 3.7절 ㉯㉲㉳, 3.8절 ㉯와 T5, 5.4절, 5.16절, 6.2절), `README.md` (타겟 그룹 설정, 3.1.3절, 3.4절 ㉮, 4.1.1절)

- `SRC/DAO_Config.py` (Gen_LLR_Mode_HBF_SEQUENCE와 시퀀스 주석), `README.md` (GenLLRMode 시퀀스, 4.1.1절의 HBF 시퀀스)
- `SRC/DAO_Main.py` (Copy_Group), `DAO_spec.md` (5.7절)
- `SRC/DAO_Constants.py` (GenLLRModeHBF), `SRC/DAO_Config.py` (Gen_LLR_Mode_HBF_SEQUENCE), `README.md` (4.1.1절의 HBF 시퀀스)
- `SRC/DAO_Main.py` (Set_Gen_Trial_LLR_Mode의 stage 건너뛰기, Validate_Config의 GEN_SINGLE_ROW 갈래), `DAO_spec.md` (3.6절 ㉷, 5.3절 특수 로직, 6.2절 표), `README.md` (4.1.1절 IS_HBF_OPT 설명)
- `SRC/DAO_Config.py` (두 시퀀스와 프리셋 세 곳), `SRC/DAO_Main.py` (Set_Gen_Trial_LLR_Mode, Get_Mode_Sequence_Str), `README.md` (GenLLRMode 시퀀스, 4.1.1절, 4.3.1절, 4.3.2절)
- `SRC/DAO_Config.py` (ITERATION_SPAN_ENDS, Gen_LLR_Mode_HBF_SEQUENCE 주석), `SRC/DAO_LLR_MATRIX.py` (3.6절의 2~4번), `SRC/DAO_Main.py` (3.6절의 5, 6번), `DAO_spec.md` (3.6절 HBF2와 ㉲㉶, 3.7절 ㉯㉲, 3.8절 ㉯㉰와 T5), `README.md` (타겟 그룹 설정, 3.4절 ㉮, 4.1.1절)

- `SRC/DAO_Main.py` (Validate_Config의 2단계 테스트 조합 검사), `README.md` (3.2.2절, 4.1.1절 IS_HBF_OPT 설명)
- `SRC/DAO_LLR_MATRIX.py`, `SRC/DAO_Main.py` (3.4절의 표), `DAO_spec.md` (3.6절 HBF3, 5.2절)
- `SRC/DAO_LLR_MATRIX.py`, `SRC/DAO_Main.py` (3.3절의 표), `_pm/tasks/20260921_SW_branch_DAO_support/review/checks/check_sw_branch.py`
- `SRC/DAO_LLR_MATRIX.py` (Is_Row_In_HBF_Iterations, Is_LLR_Valid, Read_Input_LLR_Matrix 주석, Correct_LLR_Matrix, Correct_Ch_Th_In_Row)
- `SRC/DAO_Main.py` (Gen_LLR_Regen_DV, Gen_LLR_Regen_Row, Generate_Random_Mutation, Build_Target_Group_Indices, Check_Fixed_Target_Group_Idx_List, Initialize_Stage, Initialize_LLR_Matrix, Update_Optimal_LLR, Validate_Config, Check_SW_Branch_Mode_Allowed 오류 문구)
- `SRC/DAO_Main.py` (Set_Seed_Mode), `SRC/DAO_Config.py` (HBF_OPT_CONFIG)
- `SRC/DAO_Config.py` (FIXED_TARGET_GROUP_IDX_LIST), `SRC/DAO_Constants.py` (FIXED_TARGET_GROUP_ALLOWED_MODES)
- `DAO_spec.md` (3.6절, 3.7절 최적화 규칙, 3.8절, 5.2절 특수 로직, 6.3절), `README.md` (타겟 그룹 설정, 3.4절, 4.1.1절)

## 5. 안전성 체크리스트

- ㉮ `IS_HBF_OPT`이 False인 실행은 `Is_Row_In_HBF_Iterations`가 항상 False라 유효성 검사와 보정의 동작이 같다. HD 복호에서 달라지는 것은 3.4절의 모드가 자기가 쓴 HBF 구간 row의 dv_idx 0 TH를 그대로 두거나 상수로 채우는 것 하나다. 2SD와 3SD는 `Get_Columns_Fixed_In_HBF_Iterations`가 빈 목록이라 동작이 같다
- ㉴ `IS_HBF_OPT`이 True인 실행에서 3.4절로 달라지는 것은 REGEN_DV가 다른 DV 자리에 다시 쓰는 값의 TH 하나다 (상수 0 0 0 대신 난수). 나머지 모드는 보정이 뒤에서 같은 값으로 채우므로 trial 매트릭스가 같다
- ㉵ 2단계 테스트를 끈 실행과 `IS_HBF_OPT`를 끈 실행은 3.5절로 달라지는 것이 없다. 두 설정을 함께 켠 실행만 시작 검사를 지나 보통 모드와 같은 흐름으로 돈다. 이 조합의 MPI 실행은 아직 해 보지 않았다
- ㉯ max_iteration이 4 이하인 HBF 매트릭스는 모든 row가 HBF 구간에 있으므로 동작이 같다
- ㉰ restart row는 유효성 검사와 보정 모두 HBF 규칙보다 앞에서 건너뛴다
- ㉱ `Correct_Ch_Th_In_Row`의 `is_row_in_HBF_iterations` 인자는 기본값이 False이고, row 없이 부르는 자리는 `_generate_random_row` 하나다. 끝 iteration을 받으면 3.4절의 규칙으로 값을 정하고, 받지 않으면(GEN_INITIAL_GROUP, GEN_SINGLE_ROW) False다. 그 결과는 `Gen_Trial_LLR`과 `Build_Single_Row_Matrix`에서 `Correct_LLR_Matrix`를 거친다
- ㉲ `FIXED_TARGET_GROUP_IDX_LIST`가 None인 실행은 타겟 목록이 `INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지다. 시작 직후(`Initialize_LLR_Matrix`), stage 시작(`Initialize_Stage`), 목록이 비었을 때의 복원(`Update_Optimal_LLR`)이 같은 함수로 만든다
- ㉳ `Build_Target_Group_Indices`는 잘못 적은 값(정수가 아닌 값, 범위 밖)을 건너뛰고, 알리는 일은 뒤이어 도는 `Validate_Config`가 맡는다. `Setup`이 `Initialize_LLR_Matrix` 다음에 `Validate_Config`를 부르기 때문이다
- ㉷ SW 분기가 없는 매트릭스는 모든 그룹이 보통 그룹이라 COPY_GROUP의 결과가 3.9절 앞뒤로 같다 (row 꼬리는 -1, 헤더의 그룹 유형은 후보의 것)
- ㉸ MUTATE_CSW의 stage 건너뛰기는 타겟 그룹의 row가 하나일 때만 걸린다. row가 둘 이상인 타겟의 stage는 trial 수와 흐름이 같다
- ㉹ GEN_SINGLE_ROW의 시작 검사는 `IS_HBF_OPT`가 켜져 있을 때만 걸린다. `IS_HBF_OPT`를 끈 GEN_SINGLE_ROW 실행은 같은 설정으로 시작 검사를 지난다
- ㉺ 3.10절로 달라지는 실행은 HBF 최적화 모드에서 기본 목록을 그대로 둔 실행 하나다. 보통 모드의 실행과, `Gen_LLR_Mode_HBF_SEQUENCE`를 직접 적은 실행은 같다
- ㉶ 3.11절의 모드 허용은 전에 시작 검사에서 멈추던 설정(분기 그룹 타겟과 row 단위 모드, 타겟 목록과 DELETE_ROW)을 돌게 한다. 전에 돌던 설정은 같은 모드가 같은 검사를 지난다. 타겟 앞 그룹의 보호 검사를 거치는 모드와 거치지 않는 모드도 전과 같다
- ㉻ 보통 모드이고 타겟을 직접 지정하지 않았으며 타겟에 분기 그룹이 없는 실행은 DELETE_ROW의 후보가 전과 같다 (row 1개짜리 그룹도 후보이고 그룹째 지움). 이 실행에서 3.11절로 달라지는 것은 둘이다: DELETE_ROW의 후보가 없는 stage가 trial 없이 지나가고(전에는 trial 1개가 생성에 5회 실패), SWAP_ROW의 row 1개짜리 타겟 stage가 trial 없이 지나간다(전에는 오류로 멈춤)
- ㉼ 3.12절의 검사는 `IS_HBF_OPT`가 켜져 있을 때만 걸린다. 보통 모드의 실행은 시퀀스와 검사가 그대로다. HBF 최적화 모드에서 시퀀스를 직접 적은 실행은 허용 모드 10개만 적었으면 그대로 돈다

## 6. 미결정 사항

- ㉮ 그룹 수를 바꾸는 모드(INSERT_RANDOM_GROUP, SPLIT_GROUP 등)를 `FIXED_TARGET_GROUP_IDX_LIST`와 함께 쓰게 할지. 지금은 시작할 때 오류로 막는다. 함께 쓰려면 그룹이 늘거나 줄 때 목록의 index를 따라 옮기는 기능이 필요하다
- ㉯ HD 복호의 HBF 구간 규칙(dv_idx 0의 TH는 0)을 유효성 검사와 보정에도 `IS_HBF_OPT`와 상관없이 걸지. 사용자 결정(2026-09-29)은 값을 쓰는 모드까지이고 유효성 검사와 보정은 그대로다. 걸면 HBF 구간 row의 dv_idx 0 TH가 0이 아닌 HD 입력 매트릭스는 시작할 때 검증에서 멈춘다
- ㉰ 실행 파일의 디코더가 HBF 구간에서 dv_idx 0의 TH를 읽지 않는지, 읽되 0이라 같은 출력을 내는지 (라이트 리뷰 F7). 그리고 부호의 열 차수가 11, 4, 3, 2뿐인지 (F8). 규칙의 결론은 어느 쪽이든 같고 문서의 설명이 달라진다
- ㉱ 그룹 배치를 바꿔도 되는 실행(3.11절의 4번이 거짓인 실행)에서 DELETE_ROW가 row 1개짜리 그룹을 그룹째 지우는 동작을 그대로 둘지

## 7. 검증

- 검사: `_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py` 11건 (유효성 4, 보정 1, 변이 2, row 다시 만들기 2, DV 다시 만들기 2)
  - 첫 수정 전 소스(커밋 dff3dba의 SRC): 처음 쓴 9건 가운데 5건 실패. 유효성 검사 실패 문구가 사용자 관측과 같음
  - 수정 후 소스: 11건 통과
- 검사: `_test/20260928_fixed_target_group_idx_list/test_fixed_target_group_idx_list.py` 22건 (타겟 목록 만들기 7, stage마다 고르는 타겟 5, 설정 검사 10). 구현 전에는 모두 오류였고, 3.3절을 반영하기 전에는 분기 그룹을 하나씩 다루는 4건이 실패. 분기 0과 분기 1을 차례로 도는 2건은 마지막 분기 규칙을 없애기 전에 사용자 관측과 같은 문구로 중단. 지금 22건 통과
- 검사: `_test/20260929_target_group_one_by_one/test_target_group_one_by_one.py` 8건 (MUTATE_MATRIX 4, MUTATE_CSW 2, 모드 허용 검사 2). 3.3절을 반영하기 전에는 4건 실패, 지금 8건 통과
- 검사: `check_sw_branch.py`를 3.3절에 맞게 고침 (41건 통과)
- 검사: `_test/20260928_hbf_seed_mode/test_hbf_seed_mode.py` 3건 (조건 9가지를 HBF 최적화 모드를 끈 채와 켠 채로 비교). 갈래를 없애기 전에는 HBF 쪽 조건 6가지가 보통 모드와 달랐고, 없앤 뒤 3건 통과
- 검사: `_test/20260929_hd_hbf_dv0_th_untouched/test_hd_hbf_dv0_th_untouched.py` 33건 (`IS_HBF_OPT`를 끈 HD 복호. 고정 column 5, MUTATE_MATRIX 3, 그룹 변이와 SPLIT_GROUP 3, INSERT_MUTATED_GROUP 2, INSERT_MUTATED_ROW 3, INSERT_RANDOM_ROW 2, INSERT_RANDOM_GROUP 2, 끝 iteration을 모르는 row 1, REGEN_ROW 2, REGEN_DV 4, COPY_ROWS 2, COPY_GROUP 2, SWAP_ROW 2). 3.4절의 1~5번을 반영하기 전에는 처음 쓴 14건 가운데 10건 실패, 6~11번을 반영하기 전에는 더한 19건 가운데 11건 실패, 지금 33건 통과
- 검사: `_test/20260929_hbf_two_stage_allowed/test_hbf_two_stage_allowed.py` 6건 (시작 검사 5, trial 테스트가 도는 순서 1). 3.5절을 반영하기 전에는 시작 검사 2건이 "Two-Stage 모드는 IS_HBF_OPT=True와 함께 사용할 수 없습니다"로 실패, 지금 6건 통과. trial 테스트 순서 1건은 반영 전에도 통과했다 (그 흐름이 `IS_HBF_OPT`를 읽지 않음을 보이는 검사)
- 검사: `_test/20260929_hbf_iteration_span_ends/test_hbf_iteration_span_ends.py` 9건 (구간 안의 row 1, 경계를 걸친 row 3, HBF 최적화 모드를 끈 경우 1, 경계 설정 1, 입력 매트릭스 1, INSERT_RANDOM_GROUP 2). 3.6절을 반영하기 전에는 9건 모두 오류(설정 없음), 지금 9건 통과
- 검사: `_test/20260929_mode_sequence_start_check/test_mode_sequence_start_check.py` 9건 (시퀀스 검사 7, `Validate_Config` 2). 3.6절을 반영하기 전에는 8건이 실패하거나 오류. 분기 그룹 타겟에서 막히는 모드의 예를 3.11절에 맞게 INSERT_RANDOM_ROW에서 SPLIT_GROUP으로 바꿨다 (6건). 지금 9건 통과
- 검사: `_test/20260929_mode_sequence_by_name/test_mode_sequence_by_name.py` 12건 (기본 시퀀스 5, 프리셋 1, 시퀀스를 읽는 자리 5, HBF 최적화 모드에서 만든 trial 1). 3.7절의 1~5번을 반영하기 전에는 처음 쓴 10건 가운데 6건이 실패하거나 오류였고, 그때도 통과한 4건은 HBF 모드의 값이 같은 이름의 보통 모드와 같은지, 로그 글, 시작 검사, pickle 왕복이다. 6번과 함께 더한 2건 가운데 목록 구성 검사는 6번을 반영하기 전에 실패했고 trial 검사는 그때도 통과했다. 기본 시퀀스 검사 2건(HBF 목록의 구성, stage 1에서만 도는 모드의 자리)은 3.10절에 맞게 고쳤고, 3.12절에서 이 2건과 `GenLLRModeHBF`의 구성 검사, 로그 글 검사(SPLIT_GROUP을 REGEN_DV로)를 다시 고쳤다. 지금 12건 통과
- 검사: `_test/20260929_hbf_default_sequence/test_hbf_default_sequence.py` 7건. 3.10절 시점에는 HBF 기본 목록이 9개인지를 보는 7건이었고 반영 전에 4건 실패. 3.12절에서 10개 목록에 맞게 다시 썼다 (HBF 기본 목록의 구성 3, stage가 도는 순서 1, 시작 검사 1, `GenLLRModeHBF`에 없는 모드를 적은 시퀀스 1, 보통 목록 1). 지금 7건 통과
- 검사: `_test/20260929_hbf_mode_restriction/test_hbf_mode_restriction.py` 11건 (목록의 구성 2, 시작 검사와 stage 검사 6, 새로 들어간 두 모드의 trial 3). 3.12절을 반영하기 전에는 11건 가운데 10건이 실패하고 1건이 오류, 지금 11건 통과
- 검사: `_test/20260929_skip_and_stop_checks/test_skip_and_stop_checks.py` 8건 (MUTATE_CSW stage 건너뛰기 4, GEN_SINGLE_ROW 시작 검사 4). 3.8절을 반영하기 전에는 3건 실패, 지금 8건 통과
- 검사: `_test/20260929_copy_group_keeps_branch_marks/test_copy_group_keeps_branch_marks.py` 7건 (입력 매트릭스의 표시 1, 분기 그룹을 복사한 보통 타겟 1, 값과 CSW 1, 다른 그룹 1, 복사 뒤의 모드 허용 1, 보통 그룹을 복사한 분기 타겟 1, 보통 그룹끼리의 그룹 유형 1). 3.9절을 반영하기 전에는 3건 실패 (분기 그룹을 복사한 보통 타겟, 복사 뒤의 모드 허용, 보통 그룹을 복사한 분기 타겟), 지금 7건 통과
- 검사: `_test/20260929_row_modes_on_branch_groups/test_row_modes_on_branch_groups.py` 14건 (모드 허용 7, DELETE_ROW 5, SWAP_ROW 2). 3.11절을 반영하기 전에는 11건이 실패하거나 오류였고, 그때도 통과한 3건은 막는 모드 6개, GEN_INITIAL_GROUP, 그룹 배치를 바꿔도 되는 실행의 DELETE_ROW 후보다. 지금 14건 통과
- 사용자 관측의 재현: `LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`, `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`, HBF 시퀀스 INSERT_RANDOM_ROW, MUTATE_MATRIX, MUTATE_CSW, COPY_ROWS, REGEN_DV, REGEN_ROW, DELETE_ROW. 3.11절을 반영하기 전(커밋 723b8e8)에는 시작 검사가 사용자 관측과 같은 문구로 멈췄고, 지금은 통과
- `LLR_MATRIX_2.txt`에 HBF 기본 목록 10개를 그대로 두고 `INITIAL_TARGET_GROUP_IDX`를 1(타겟에 분기 그룹 1~4가 들어감)과 5로 둔 실행 모두 시작 검사를 통과 (3.12절 반영 뒤)
- 기존 검사: `check_dao_fixes.py`, `check_sw_branch.py`, `_test/20260921_gather_uncors_matrix_arg/` 모두 통과. 검사는 모두 224건
- 입력 매트릭스 `Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`(max_iteration 124)를 `is_HBF_OPT=True`로 읽으면 유효하고, 보정이 dv_idx 0의 CH와 TH를 바꾸지 않음. `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`이면 두 파일 모두 타겟 목록이 `[0, 1]`
- 라이트 리뷰 (2026-09-29 13:39 ~ 13:58, 기준 커밋 2e34036, 기록: `review/`): Round 1 관점 38개를 18개로 통합, Round 2 lv1 에이전트 5개. 발견 21건 (CRITICAL 0, HIGH 3, MEDIUM 3, LOW 15). 종합 판정은 수정 필요
  - HIGH: F1 시작 검사에 SW 분기 모드 제한이 없어 시작을 통과한 설정이 중간 stage에서 멈춤, F2 경계 검사가 4와 5 사이만 봄, F3 COPY_GROUP이 후보의 분기 표시를 타겟에 복사함
  - MEDIUM: F4 row 하나짜리 타겟의 MUTATE_CSW가 바뀌지 않은 매트릭스를 되풀이 측정함, F5 GEN_SINGLE_ROW와 HBF 최적화 모드의 조합을 시작할 때 막지 않음, F6 문서에 HBF 최적화 모드의 사용 조건이 빠짐
  - 값 규칙, seed 모드, 타겟 목록, MPI로 옮기는 값에서는 결함을 찾지 못함
  - 3.4절의 수정은 리뷰 뒤에 들어갔다. 1~5번(커밋 f843c7a)으로 F15 가운데 `_generate_mutation_for_group`과 F9 가운데 INSERT_RANDOM_ROW, INSERT_RANDOM_GROUP의 로그가 풀렸고, 6~11번으로 F15의 나머지(`_generate_mutation_for_row`)와 REGEN_DV가 dv_idx 0 자리의 값을 다른 DV로 옮기던 발견이 풀렸다
  - 3.6절의 수정으로 F1, F2, F6이 풀렸고, 3.8절로 F4와 F5가, 3.9절로 F3이 풀렸다 (커밋 dde34bd). HIGH와 MEDIUM 발견 6건이 모두 풀렸다
- 남은 확인: 사용자 환경 MPI 실행에서 초기 매트릭스 검증 통과 여부, stage 로그의 `[target_group_indices]` 줄이 지정한 그룹만 도는지 (같은 자리의 "Current target index" 줄은 별도 카운터라 실제 타겟과 다른 그룹을 적는다, 라이트 리뷰 F17)
