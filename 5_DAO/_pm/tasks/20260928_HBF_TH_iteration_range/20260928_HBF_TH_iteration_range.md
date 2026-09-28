# HBF 최적화 모드의 dv_idx 0 TH 고정을 HBF 구간의 row로 한정

> 작성: 2026-09-28 17:06:46
> 등급: Review (유효성 규칙과 값 고정 범위의 로직 수정). 사용자 지시로 수정을 적용했다.
> 관련: 규칙 정본은 [DAO_spec.md 3.6절](../../../DAO_spec.md)

## 1. 목적

HBF(Hybrid Bit Flipping) 최적화 모드(`IS_HBF_OPT`)에서 dv_idx 0의 TH를 상수 0으로 고정하는 규칙이 HBF 구간(iteration 1~4)의 row에만 걸리게 한다. iteration 5 이상의 row는 dv_idx 0의 TH에 0이 아닌 값을 가질 수 있다.

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

dv_idx 0의 위치: row는 `CH(dv 0) TH(dv 0) CH(dv 1) TH(dv 1) ...` 순서이고, 코드는 row를 `num_parameter_each_set` 칸씩 잘라 첫 묶음을 dv_idx 0으로 읽는다. 이 부분은 수정 없이 맞게 동작한다.

## 3. 설계

판단을 한 함수에 모으고 다섯 자리가 모두 그 함수를 쓴다.

| # | 위치 | 내용 |
|---|------|------|
| 1 | `LLR_MATRIX.Is_Row_In_HBF_Iterations` (새 함수) | `is_HBF_OPT`이고 row의 `iter_end <= HBF_MAX_ITERATION`이면 True |
| 2 | `LLR_MATRIX.Is_LLR_Valid` | HBF1을 HBF 구간의 row에만 검사. 오류 문구에 row의 iteration과 HBF 구간을 함께 적음. max_iteration 상한 검사(HBF2)는 없앰 |
| 3 | `LLR_MATRIX.Correct_LLR_Matrix`, `Correct_Ch_Th_In_Row` | row가 HBF 구간에 있을 때만 dv_idx 0 TH를 상수로 고정 (`is_row_in_HBF_iterations` 인자) |
| 4 | `LLR_OPT.Gen_LLR_Regen_DV`, `Gen_LLR_Regen_Row` | 바꿀 row가 HBF 구간에 있을 때만 dv_idx 0 TH를 상수로 만듦 |
| 5 | `LLR_OPT.Generate_Random_Mutation` | row가 HBF 구간에 있을 때만 dv_idx 0 TH column을 변이 후보에서 뺌 |

경계에 걸친 row(예: iteration 3~6)는 HBF 구간의 row로 보지 않는다. iteration 5와 6에서 디코더가 그 row의 dv_idx 0 TH를 읽기 때문이다.

`_generate_random_row`는 iteration이 정해지기 전의 row를 만들므로 dv_idx 0 TH도 난수로 채운다. row가 매트릭스에 들어간 뒤 `Correct_LLR_Matrix`가 iteration을 보고 고정한다.

## 4. 수정 대상 파일

- `SRC/DAO_LLR_MATRIX.py` (Is_Row_In_HBF_Iterations, Is_LLR_Valid, Read_Input_LLR_Matrix 주석, Correct_LLR_Matrix, Correct_Ch_Th_In_Row)
- `SRC/DAO_Main.py` (Gen_LLR_Regen_DV, Gen_LLR_Regen_Row, Generate_Random_Mutation)
- `DAO_spec.md` (3.6절, 5.2절 특수 로직, 6.3절)

## 5. 안전성 체크리스트

- ㉮ `IS_HBF_OPT`이 False인 실행은 `Is_Row_In_HBF_Iterations`가 항상 False라 동작이 같다
- ㉯ max_iteration이 4 이하인 HBF 매트릭스는 모든 row가 HBF 구간에 있으므로 동작이 같다
- ㉰ restart row는 유효성 검사와 보정 모두 HBF 규칙보다 앞에서 건너뛴다
- ㉱ `Correct_Ch_Th_In_Row`의 새 인자는 기본값이 False이고, row 없이 부르는 자리는 `_generate_random_row` 하나다. 그 결과는 `Gen_Trial_LLR`과 `Build_Single_Row_Matrix`에서 `Correct_LLR_Matrix`를 거친다

## 6. 미결정 사항

- ㉮ HBF 최적화 모드에서 iteration 5 이상의 그룹도 최적화 타겟에 넣을지. 지금은 `INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지가 타겟이라 iteration 5 이상의 그룹도 변이한다 ([DAO_Main.py](../../../SRC/DAO_Main.py)의 `Initialize_LLR_Matrix`와 stage 시작부의 `target_group_indices` 재설정)

## 7. 검증

- 검사: `_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py` 9건 (유효성 2, 보정 1, 변이 2, row 다시 만들기 2, DV 다시 만들기 2)
  - 수정 전 소스(커밋 dff3dba의 SRC): 5건 실패. 유효성 검사 실패 문구가 사용자 관측과 같음
  - 수정 후 소스: 9건 통과
- 기존 검사: `check_dao_fixes.py`, `check_sw_branch.py`, `_test/20260921_gather_uncors_matrix_arg/` 모두 통과
- 입력 매트릭스 `Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`(max_iteration 124)를 `is_HBF_OPT=True`로 읽으면 유효하고, 보정이 dv_idx 0 묶음을 바꾸지 않음
- 남은 확인: 사용자 환경 MPI 실행에서 초기 매트릭스 검증 통과 여부
