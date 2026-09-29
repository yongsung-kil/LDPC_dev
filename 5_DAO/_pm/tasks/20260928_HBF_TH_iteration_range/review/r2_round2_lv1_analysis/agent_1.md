# Round 2 에이전트 1: 값 규칙과 값 생성 (P1~P6)

> 작성: 2026-09-29 13:52:26
> 읽은 범위: `git diff dff3dba..2e34036 -- 5_DAO/SRC`의 `DAO_LLR_MATRIX.py`, `DAO_Main.py`, `DAO_Config.py`, `DAO_Constants.py` 전체. 현재 소스의 `LLR_MATRIX.__init__`(36~52), `Is_Row_In_HBF_Iterations`(98~106), `Is_LLR_Valid`(401~617), `Read_Input_LLR_Matrix`(619~717), `Correct_LLR_Matrix`와 `Correct_Ch_Th_In_Row`(731~835), `DAO_Main.py`의 `Update_RefC_Configs`(450~451), `_generate_random_row`(766~797), `Gen_Trial_LLR`(1964~2040), `Initialize_LLR_Matrix`(2338~2363), `Insert_Random_Row`(2383~2494), `Gen_LLR_Insert_Random_Group`(2609~2790), `Gen_LLR_Gen_Initial_Group`(3606~3677), `Gen_LLR_Insert_Random_Row`(3679~3723), `Gen_LLR_Mutate_Matrix`와 조정 단계(3755~3915), `Gen_LLR_Regen_DV`(3917~4065), `Gen_LLR_Regen_Row`(4067~4191), `Generate_Random_Mutation`(7067~7131), `Validate_LLR_Matrix`(10067~10078), `Build_Single_Row_Matrix`(10363~10400), 디코더 `0_LDPC_original/src/decoder.cpp` 4039~4080.
> 실행 확인: OS 임시 폴더의 임시 스크립트 두 개로 `LLR_MATRIX`와 `LLR_OPT.__new__(LLR_OPT)`를 써서 확인했다 (검사 매트릭스는 `_test/20260928_hbf_th_iteration_range/`의 것과 같은 3그룹 매트릭스: 그룹 0 iteration 1~1, 그룹 1 iteration 2~4, 그룹 2 iteration 5~8).

## 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 이번 변경이 만든 것인가 | 확인 방법 |
|---|--------|------|------|------|------------------------|----------|
| 1 | LOW | P4, P3 | 새 row를 만드는 모드(INSERT_RANDOM_ROW, INSERT_RANDOM_GROUP, GEN_INITIAL_GROUP)의 로그가 보정 전 값을 찍어, HBF 구간 row의 dv_idx 0 TH가 난수로 보인다. 그 뒤 보정이 0으로 바꾸지만 보정 로그에 남지 않는다 | [DAO_Main.py:795](../../../../../SRC/DAO_Main.py#L795), [DAO_Main.py:3715](../../../../../SRC/DAO_Main.py#L3715), [DAO_Main.py:2782](../../../../../SRC/DAO_Main.py#L2782), [DAO_LLR_MATRIX.py:829](../../../../../SRC/DAO_LLR_MATRIX.py#L829) | 로그 어긋남은 이번 변경이 만듦 (고치기 전에는 `_generate_random_row`가 이미 0으로 고정). 보정 로그에 안 남는 것은 예전부터 | 실행 |
| 2 | LOW | P5 | REGEN_DV의 재사용 모드가 HBF 구간 row의 dv_idx 0 조각(TH가 0 0 0)을 같은 row의 다른 DV에 그대로 옮겨, dv_idx 1 이상의 TH가 모두 0인 trial을 만든다 | [DAO_Main.py:3986~4022](../../../../../SRC/DAO_Main.py#L3986) | 예전부터 (고치기 전에는 모든 row가 그랬고, 이번 변경으로 HBF 구간 row로 줄었다) | 실행 |
| 3 | LOW | P2 | 한 row가 규칙 두 개를 함께 어길 때 나오는 오류 문구가 원인과 다르다. ㉮ dv_idx 0 TH가 비증가도 아니고 0도 아니면 비증가 문구(RW5)가 나온다 ㉯ iteration이 거꾸로인 row(예: 7~3)는 iteration 문구보다 HBF1 문구가 먼저 나온다 | [DAO_LLR_MATRIX.py:521~533](../../../../../SRC/DAO_LLR_MATRIX.py#L521), [DAO_LLR_MATRIX.py:578](../../../../../SRC/DAO_LLR_MATRIX.py#L578) | ㉮는 예전부터, ㉯는 이번 변경이 만듦 (HBF1이 row의 iteration을 보게 되면서) | 실행 |
| 4 | LOW | P1 | `self.HBF_max_iteration`은 만들 때 한 번 저장되지만 읽는 곳이 없고, 판단은 모두 `HBF_OPT_CONFIG.HBF_MAX_ITERATION`을 부를 때마다 읽는다 | [DAO_LLR_MATRIX.py:42](../../../../../SRC/DAO_LLR_MATRIX.py#L42), [DAO_LLR_MATRIX.py:106](../../../../../SRC/DAO_LLR_MATRIX.py#L106), [DAO_LLR_MATRIX.py:492](../../../../../SRC/DAO_LLR_MATRIX.py#L492) | 예전부터 (예전에도 읽는 곳 없음) | 읽기 (Grep) |

CRITICAL 0건, HIGH 0건, MEDIUM 0건, LOW 4건.

## 발견별 상세

### 1. 새 row를 만드는 모드의 로그가 보정 전 값을 찍는다 (LOW)

- 재현 조건: `IS_HBF_OPT=True`, 타겟 그룹이 HBF 구간(iteration 끝이 4 이하)이고 모드가 INSERT_RANDOM_ROW, INSERT_RANDOM_GROUP(삽입 그룹이 iteration 4 이하일 때), GEN_INITIAL_GROUP(`GEN_INITIAL_GROUP_CONFIG.ITERATION` 4 이하일 때) 중 하나
- 코드 근거: `_generate_random_row`는 [DAO_Main.py:795](../../../../../SRC/DAO_Main.py#L795)에서 `Correct_Ch_Th_In_Row(raw_array)`를 `is_row_in_HBF_iterations=False`로 불러 dv_idx 0 TH를 난수로 둔다 (태스크 문서 3절의 의도대로). 모드 함수가 이 값을 로그에 찍고([DAO_Main.py:3715](../../../../../SRC/DAO_Main.py#L3715), [DAO_Main.py:2782](../../../../../SRC/DAO_Main.py#L2782)), `Gen_Trial_LLR`의 `Correct_LLR_Matrix`([DAO_Main.py:2022](../../../../../SRC/DAO_Main.py#L2022))가 [DAO_LLR_MATRIX.py:829~831](../../../../../SRC/DAO_LLR_MATRIX.py#L829)에서 0으로 덮는다. 이 덮어쓰기는 `correct_msg`에 아무것도 넣지 않는다 (Truncated만 적는다)
- 실행 확인: 검사 매트릭스, `current_target_group_idx=1`, `current_trial_idx=2`, `random.seed(3)`로 `Gen_LLR_Insert_Random_Row`를 부름. 로그 `Ch, Th: [15, 30, 23, 8, 4, 30, 16, 0]` (dv_idx 0 TH가 30 23 8). 이어 `Correct_LLR_Matrix()`의 메시지는 `[]`이고 보정 뒤 그룹 1의 row는 `[15, 0, 0, 0]`, `[15, 0, 0, 0]`, `[5, 0, 0, 0]`, 유효성 `(True, '')`
- 결과에는 영향이 없다 (측정과 저장은 보정 뒤 값으로 한다). 사용자가 로그의 삽입 row 값을 보고 HBF 규칙이 깨졌다고 읽을 수 있다
- 고칠 방향: ㉮ `Correct_Ch_Th_In_Row`가 상수 고정으로 값이 바뀐 칸을 `(HBF fixed)`로 `correct_msg`에 적게 하거나 ㉯ 모드 함수의 로그 문구에 "보정 전 값"임을 적는다

### 2. REGEN_DV 재사용 모드가 dv_idx 0 조각을 다른 DV로 옮긴다 (LOW)

- 재현 조건: `IS_HBF_OPT=True`, 타겟 그룹이 HBF 구간, REGEN_DV에서 dv_idx 0을 다시 만든 trial이 갱신된 다음 trial들
- 코드 근거: 갱신 다음 trial은 `gen_DV_idx=0`, 재사용 모드로 들어가고([DAO_Main.py:3996~3998](../../../../../SRC/DAO_Main.py#L3996)), 그 뒤 trial마다 `gen_DV_idx`를 1씩 늘리며([DAO_Main.py:3987~3990](../../../../../SRC/DAO_Main.py#L3987)) `previous_dv_segment`를 다음 (row, DV) 자리에 그대로 쓴다([DAO_Main.py:4021~4022](../../../../../SRC/DAO_Main.py#L4021)). dv_idx 0 조각의 TH는 0 0 0이므로 dv_idx 1 이상에 TH 0 0 0이 들어간다. 이 값은 유효성 규칙에 맞아 보정이 바꾸지 않는다
- 실행 확인: 검사 매트릭스, 타겟 그룹 1, `REGEN_DV_CONFIG.ENABLE_FIX_IDX=False`, `random.seed(1)`. trial 1(보통 모드) 조각 `[8, 0, 0, 0]`. trial 2(갱신 뒤, `gen_DV_idx=0`) row 0 `[8, 0, 0, 0, 14, 14, 9, 5]`. trial 3(`gen_DV_idx=1`) row 0 `[15, 0, 0, 0, 8, 0, 0, 0]`, 보정 뒤에도 같고 유효성 `(True, '')`
- 반대 방향(dv_idx 1 조각이 HBF 구간 row의 dv_idx 0에 들어감)은 보정이 TH를 0으로 고치므로 규칙은 지켜진다
- HBF 구간 row의 dv_idx 0 조각은 CH만 의미가 있으므로, 다른 DV로 옮기는 trial은 TH를 모두 0으로 둔 시험이 되어 쓸모가 적다. 재사용 모드는 예전부터 조각을 DV 사이로 옮겼고, 이번 변경은 이 일이 생기는 row를 HBF 구간으로 줄였다
- 고칠 방향: 재사용할 조각이 HBF 구간 row의 dv_idx 0에서 나왔으면 다른 DV로 옮길 때 CH만 옮기고 TH는 새로 뽑거나, 재사용 대상을 같은 dv_idx로 한정한다

### 3. 규칙 두 개를 함께 어긴 row의 오류 문구 (LOW)

- ㉮ 비증가 검사(RW5, [DAO_LLR_MATRIX.py:521](../../../../../SRC/DAO_LLR_MATRIX.py#L521))가 HBF1([DAO_LLR_MATRIX.py:526](../../../../../SRC/DAO_LLR_MATRIX.py#L526))보다 앞에 있다
  - 실행 확인: 그룹 1 row 0의 dv_idx 0 TH를 `[0, 5, 0]`으로 둠. 결과 `Group 1 Row 0 DV 0 TH values ([0 5 0]) must be non-increasing.` (HBF1 문구가 아님)
  - 초기 매트릭스는 보정 없이 검사하므로([DAO_Main.py:2361](../../../../../SRC/DAO_Main.py#L2361)) 사용자가 이 문구를 먼저 보고 정렬만 고치면 다음 실행에서 HBF1 문구를 다시 만난다
- ㉯ iteration 순서 검사(`ends[0] < starts[0]`, [DAO_LLR_MATRIX.py:578](../../../../../SRC/DAO_LLR_MATRIX.py#L578))는 row 반복 뒤의 그룹 검사다. `Is_Row_In_HBF_Iterations`는 끝 iteration만 보므로 거꾸로 된 row(예: 7~3)를 HBF 구간으로 판단하고, HBF2(`7 <= 4` 거짓)는 통과시킨다
  - 실행 확인: 그룹 2의 iteration을 7~3으로 둠. 결과 `In HD_HBF_OPT mode, Group 2 Row 0 DV 0 invalid TH values: expected all 0 for iteration 7~3 (HBF iterations are 1~4), got [15, 10, 0]`
  - 두 경우 모두 매트릭스는 거부되므로 결과는 바르다. 문구만 원인을 가린다
- 고칠 방향: HBF1을 비증가 검사 앞으로 옮기고, row 반복 안에서 `iter_end < iter_start`를 HBF2보다 먼저 검사한다

### 4. 저장만 하고 읽지 않는 `HBF_max_iteration` (LOW)

- `LLR_MATRIX.__init__`이 `self.HBF_max_iteration`을 저장하지만([DAO_LLR_MATRIX.py:42](../../../../../SRC/DAO_LLR_MATRIX.py#L42)) `5_DAO/SRC` 어디서도 읽지 않는다 (Grep 확인). HBF1, HBF2, 보정, 변이 모두 `HBF_OPT_CONFIG.HBF_MAX_ITERATION`을 부를 때 읽는다
- `HBF_MAX_ITERATION`에 값을 넣는 자리는 [DAO_Config.py:374](../../../../../SRC/DAO_Config.py#L374) 하나이므로 실행 중 두 값이 갈라지지 않는다. 검사 스크립트가 클래스 값을 바꾸면 이미 만든 매트릭스의 저장 값과 판단 값이 달라지지만 저장 값은 쓰이지 않아 동작에는 영향이 없다
- 고칠 방향: 속성을 지우거나, `Is_Row_In_HBF_Iterations`와 HBF2가 이 속성을 읽게 해 판단 기준을 매트릭스에 묶는다

## 통과 관점

- P1 HBF 구간 판단 기준과 경계값: 문제 없음 (LOW 4 제외)
  - ㉮ 경계를 걸친 row(실행 확인: 그룹 1을 2~6, 그룹 2를 7~8로 둠)는 `Is_Row_In_HBF_Iterations`가 False라 보정이 dv_idx 0 TH `[9, 5, 1]`을 그대로 두고, 이어지는 `Is_LLR_Valid`가 HBF2 문구로 거부한다. 보정, 변이, 다시 만들기는 모두 `Gen_Trial_LLR`의 결과가 HBF2를 지나야 쓰이므로 경계를 걸친 row의 값은 측정에 쓰이지 않는다
  - ㉯ HBF1(`iter_end <= 4`), HBF2(`iter_start <= 4 < iter_end`), 디코더([decoder.cpp:4056~4058](../../../../../../0_LDPC_original/src/decoder.cpp#L4056)의 `iter <= 4`)가 모두 iteration 4를 HBF 구간에 넣는다. 디코더 iteration 눈금과 매트릭스 iteration의 대응은 P14(에이전트 4) 범위라 여기서 확인하지 않았다
  - ㉱ init_n 2, 3에서 `Update_RefC_Configs`([DAO_Main.py:450~451](../../../../../SRC/DAO_Main.py#L450))와 `LLR_MATRIX.__init__`([DAO_LLR_MATRIX.py:43~50](../../../../../SRC/DAO_LLR_MATRIX.py#L43))이 둘 다 HBF를 끈다. 매트릭스를 만드는 두 자리([DAO_Main.py:2605](../../../../../SRC/DAO_Main.py#L2605), [DAO_Main.py:4339](../../../../../SRC/DAO_Main.py#L4339))가 모두 `DAO_CONFIG.IS_HBF_OPT`를 넘기므로, 고치기 전 `Generate_Random_Mutation`이 읽던 `DAO_CONFIG.IS_HBF_OPT`와 지금 읽는 `matrix.is_HBF_OPT`는 같다
- P2 HBF1, HBF2의 검사 순서와 적용 대상: 문제 없음 (LOW 3 제외). restart row는 [DAO_LLR_MATRIX.py:457~476](../../../../../SRC/DAO_LLR_MATRIX.py#L457)에서 HBF1, HBF2 전에 빠지고 `iter_start == iter_end`라 경계를 걸칠 수 없다. 한 그룹 안 row의 iteration이 다르면 HBF 판단은 row마다 따로 하지만 [DAO_LLR_MATRIX.py:572~577](../../../../../SRC/DAO_LLR_MATRIX.py#L572)에서 그룹이 거부되므로 결과는 같다
- P3 보정과 유효성 검사의 순서: 문제 없음 (LOW 1 제외)
  - ㉮ trial 경로는 보정([DAO_Main.py:2022](../../../../../SRC/DAO_Main.py#L2022)) 뒤 검사([DAO_Main.py:2508](../../../../../SRC/DAO_Main.py#L2508)), 초기 매트릭스는 보정 없이 검사([DAO_Main.py:2361](../../../../../SRC/DAO_Main.py#L2361))라 입력의 HBF 규칙 위반은 오류로 멈춘다 (사용자 요구와 맞음)
  - ㉯ 헤더 TH min_value를 2로 둔 매트릭스(실행 확인)에서 보정은 dv_idx 0 TH를 `[0, 0, 0]`으로, dv_idx 1 TH는 `[11, 5, 4]`로 두고 유효성 `(True, '')`. 유효성 검사가 min_value를 보지 않으므로 둘이 부딪히지 않는다
  - ㉱ 보정 실패(ValueError)는 `generate_LLR_success=False`로 trial 실패가 된다
  - 입력 매트릭스 `LLR_MATRIX_1.txt`, `LLR_MATRIX_2.txt`를 `is_HBF_OPT=True`로 읽으면(실행 확인) 둘 다 유효하고 HBF 구간 그룹은 각각 `[0, 1, 2]`, `[0, 1]`, 보정이 CH와 TH 값을 바꾸지 않는다
- P4 iteration이 정해지기 전의 row 생성: 문제 없음 (LOW 1 제외). `_generate_random_row`를 부르는 네 자리(`Insert_Random_Row` 2414, `Gen_LLR_Insert_Random_Group` 2690, `Generate_Initial_Random_Row` 2074를 거치는 `Gen_LLR_Gen_Initial_Group` 3648, `Build_Single_Row_Matrix` 10372)는 모두 `Gen_Trial_LLR`의 `Correct_LLR_Matrix`나 [DAO_Main.py:10390](../../../../../SRC/DAO_Main.py#L10390)의 보정을 거친 뒤 측정과 저장으로 간다. 보정 전에 도는 것은 `_Protected_Groups_Changed` 비교([DAO_Main.py:2009](../../../../../SRC/DAO_Main.py#L2009))뿐이고 새 row는 타겟 그룹에 들어가므로 보호 그룹 비교에 걸리지 않는다 (보호 범위 자체는 P10, 에이전트 2 범위)
- P5 값 재사용과 조정 단계: 문제 없음 (LOW 2 제외)
  - ㉮ REGEN_DV와 REGEN_ROW의 재사용은 stage 안에서 타겟 그룹 하나의 row 사이로만 옮기고, 그룹 안 row는 iteration이 같으므로([DAO_LLR_MATRIX.py:572~577](../../../../../SRC/DAO_LLR_MATRIX.py#L572)) HBF 구간 안과 밖 사이로 값이 옮겨지지 않는다. trial 1에서 재사용 상태를 지운다([DAO_Main.py:3982](../../../../../SRC/DAO_Main.py#L3982), [DAO_Main.py:4120](../../../../../SRC/DAO_Main.py#L4120))
  - ㉯ 미세 조정과 거친 조정은 `prev_generated_mutation`의 (그룹, row, column)만 쓰고, 그 column은 `Generate_Random_Mutation`이 이미 제외 column을 뺀 것이다. 조정 결과도 `Correct_LLR_Matrix`를 거치므로 HBF 구간 row의 dv_idx 0 TH는 어떤 경우에도 0으로 남는다. trial 1의 변이가 비었을 때 앞 stage의 `prev_generated_mutation`이 남는 경로는 있으나, 빈 변이 trial이 갱신될 조건을 확인하지 못해 "확인 못 함"으로 둔다 (확인하려면 `Update_Optimal_LLR`의 갱신 판정에서 FER이 같은 trial이 갱신되는 설정, 예: `ENABLE_AVG_ITER_UPDATE`를 봐야 함)
- P6 변이 후보와 제외 column: 문제 없음. `HBF_immutable_col_range = (ch_length, num_parameter_each_set)`이고 init_n 1에서 `ch_length = 1`이므로 column 1~3, 곧 dv_idx 0의 TH 칸과 같다. dv_idx 0의 CH(column 0)는 후보에 남는다 (디코더 [decoder.cpp:4039~4045](../../../../../../0_LDPC_original/src/decoder.cpp#L4039)에서 sum_t가 채널 값을 쓰므로 CH는 변이할 의미가 있다). HBF 구간 뒤의 row는 제외 없이 모든 column이 후보다. 후보가 비는 경우는 `skip_max_row_idx`가 모든 row를 건너뛸 때뿐이고 HBF와 무관하게 예전부터 빈 변이 trial로 흐른다
