# Round 2 에이전트 4: 디코더 근거와 요구 대응 (P14, P15)

> 작성: 2026-09-29 13:53:39
> 기준 커밋 2e34036. DAO 쪽 줄 번호와 실행 확인은 모두 `git archive 2e34036`으로 OS 임시 폴더에 푼 복사본 기준이다 (복사본의 SRC를 sys.path 맨 앞에 넣어 다시 돌렸고 결과가 같았다). 디코더 쪽은 작업 폴더의 `0_LDPC_original/src` 기준이다. 링크는 저장소 파일을 가리키므로 작업 폴더가 바뀌면 줄이 어긋날 수 있다
> 읽은 범위: `0_LDPC_original/src`의 `common.h` 403~407, `mode.h` 22, `decoder.cpp`(Select_BF 2082~2130, VN_Cal_HD 3973~4129, VN_Cal_HD_HCU 4268~4282, Get_Cur_LLR_Idx_FILE 6973~7073, Get_VNU_LLR_SET_FILE 7074~7102, 반복 루프 1136~1149, 1966~1979, VN 호출 5695~5750), `local_opt.cpp` 52~131. DAO 쪽은 `DAO_LLR_MATRIX.py`의 HBF 자리 전부, `DAO_Main.py`의 타겟 목록, 모드 검사, 변이 자리, `Validate_Config`, `Gen_Trial_LLR`, 입력 매트릭스 `LLR_MATRIX_1.txt`, `LLR_MATRIX_2.txt`.
> 실행 확인: 단일 프로세스 `LLR_OPT.__new__` 방식 스크립트(OS 임시 폴더)로 설정 6가지를 돌렸다 (5절).

## 2. 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 이번 변경이 만든 것인가 | 사용자 확인 필요 여부 |
|---|--------|------|------|------|------------------------|---------------------|
| 1 | MEDIUM | P15 요구 3 | 검사되는 경계는 iteration 4와 5 사이 하나뿐이다. iteration 8과 9 사이를 걸치는 row(예: 5~10)는 HBF 최적화 모드에서도 유효로 통과한다 | [DAO_LLR_MATRIX.py:491](../../../../../SRC/DAO_LLR_MATRIX.py#L491) | 이번 변경이 연 범위 (이전에는 max_iteration 4 이하 검사로 HBF 모드 매트릭스에 iteration 5 이상이 없었다) | 필요 (8과 9 사이도 검사할지) |
| 2 | MEDIUM | P15 요구 4 | 앞부분(분기 그룹 0~4)을 타겟으로 한 실행에서 `FIXED_TARGET_GROUP_ALLOWED_MODES`에 있는 모드(예: SWAP_ROW)를 시퀀스에 넣으면 시작 검사(`Validate_Config`)는 통과하고 그 모드 차례의 stage에서 `MPI_Abort`로 중단된다 | [DAO_Main.py:10010](../../../../../SRC/DAO_Main.py#L10010), [DAO_Main.py:8476](../../../../../SRC/DAO_Main.py#L8476) | 일부 (T4 검사는 이번 변경, 분기 모드 검사를 stage에서만 하는 것은 이전부터. Round 1 P10 ㉯와 겹침) | 불필요 |
| 3 | LOW | P14 ㉮㉯㉲ | 문서와 docstring이 "HBF 구간에서 디코더는 dv_idx 0의 TH를 읽지 않는다"고 적고 근거로 `decoder.cpp:4058`을 든다. 4058행은 `__AUTO_LLR_OPT__`가 꺼진 갈래다. 켜진 갈래(4056행)에서는 `flag_BF_on`이 늘 LOW라 1 bit 정밀도 갈래에 들어가지 않고 TH를 읽는다. TH가 모두 0이면 4 bit 정밀도 갈래의 출력이 1 bit 정밀도 갈래와 같아진다. 규칙의 결과는 같고 설명이 어긋난다 | [DAO_spec.md:123](../../../../../DAO_spec.md#L123), [DAO_LLR_MATRIX.py:101](../../../../../SRC/DAO_LLR_MATRIX.py#L101), [태스크 문서 27행](../../20260928_HBF_TH_iteration_range.md) | 이번 변경 | 필요 (실행 파일의 갈래가 소스와 같은지) |
| 4 | LOW | P14 ㉰ | 디코더의 1 bit 조건은 `v_deg > DV_5`(열 차수 6 이상)이고, DAO의 고정 대상은 헤더 첫 DV 칸(dv_idx 0)이다. 둘이 같으려면 부호의 열 차수 가운데 6 이상이 헤더 첫 칸의 범위(`11`~`11`)에만 있어야 하고, 헤더 첫 칸이 가장 높은 DV여야 한다. DAO는 헤더 순서를 검사하지 않는다 | [DAO_LLR_MATRIX.py:710](../../../../../SRC/DAO_LLR_MATRIX.py#L710), [decoder.cpp:7078](../../../../../../0_LDPC_original/src/decoder.cpp#L7078) | 이전부터 (dv_idx 0 고정 규칙 자체는 반입 때부터) | 필요 (열 차수 분포) |
| 5 | LOW | P15 요구 4 | 앞부분 실행의 권장 시퀀스 `[10, 11]`에서 MUTATE_CSW가 row 1개짜리 타겟(`LLR_MATRIX_2.txt`의 그룹 0, 그룹 3)을 만나면 바꿀 CSW가 없어 optimal과 같은 매트릭스를 trial로 내고 FER을 측정한다. 그 stage의 trial이 모두 헛돈다 | [DAO_Main.py:7146](../../../../../SRC/DAO_Main.py#L7146), [DAO_Main.py:3743](../../../../../SRC/DAO_Main.py#L3743) | 이전부터 있던 동작. 그룹 단위 타겟(64a07a9)과 목록 지정으로 이 매트릭스에서 드러남 | 불필요 |

## 3. 발견 상세

### 발견 1: iteration 8과 9 사이 경계는 검사되지 않는다 (MEDIUM)

- 코드 근거: HBF2는 `row.iter_start <= HBF_MAX_ITERATION < row.iter_end` 하나다 ([DAO_LLR_MATRIX.py:492](../../../../../SRC/DAO_LLR_MATRIX.py#L492)). `DAO_Main.py`와 `DAO_LLR_MATRIX.py`에 8이나 9를 경계로 보는 검사는 없다 (`HBF_MAX_ITERATION`을 읽는 자리는 `Is_Row_In_HBF_Iterations`와 HBF2 둘뿐)
- 실행 확인: 그룹 0(1~1), 그룹 1(2~4), 그룹 2(5~10), 그룹 3(11~20)인 매트릭스를 `is_HBF_OPT=True`로 읽으면 `Is_LLR_Valid()`가 `(True, '')`다. 같은 꼴에서 row를 2~6으로 바꾸면 HBF2 문구로 거부된다
- 영향: `LLR_MATRIX_2.txt`처럼 iteration 5~8이 분기 그룹이면 분기 모드 제한(`SW_BRANCH_ALLOWED_MODES`)과 보호 구간(`_Protected_Groups_Changed`)이 8과 9 사이를 사실상 지킨다. 분기가 없는 매트릭스에서 `FIXED_TARGET_GROUP_IDX_LIST = None`과 기본 HBF 시퀀스(`INSERT_RANDOM_GROUP`, `SPLIT_GROUP` 포함)를 쓰면 이 경계를 걸치는 row가 나올 수 있는지는 구조 변경 모드의 iteration 계산에 달려 있다 (Round 1 P7, 에이전트 2 범위. 여기서는 확인 못 함)
- 사용자에게 물을 것: 요구 3의 "구간 1~4, 5~8, 9 이후"를 DAO가 검사로 지켜야 하는지, 아니면 4와 5 사이만 지키면 되는지. 지켜야 한다면 HBF2 옆에 경계 목록(예: `[4, 8]`)을 두고 같은 식으로 검사하는 방향이다

### 발견 2: 분기 그룹 타겟의 모드 제한이 시작 검사에 없다 (MEDIUM)

- 코드 근거: `Validate_Config`는 목록이 있을 때 `Check_Fixed_Target_Group_Idx_List`만 부르고 ([DAO_Main.py:10010](../../../../../SRC/DAO_Main.py#L10010)), 이 함수는 `FIXED_TARGET_GROUP_ALLOWED_MODES` 9개만 본다 ([DAO_Main.py:8360](../../../../../SRC/DAO_Main.py#L8360)). 분기 그룹이 타겟에 있을 때의 제한(MUTATE_MATRIX, MUTATE_CSW만)은 `Set_Gen_Trial_LLR_Mode`에서 stage마다 검사한다 ([DAO_Main.py:8476](../../../../../SRC/DAO_Main.py#L8476))
- 실행 확인: `LLR_MATRIX_2.txt`, `IS_HBF_OPT=True`, 목록 `[0, 1, 2, 3, 4]`, 시퀀스 `[10, 11, 21]`이면 `Validate_Config`는 통과하고 stage 3(SWAP_ROW)에서 "target groups [0, 1, 2, 3, 4] are SW branch groups, so mode SWAP_ROW (21) is not allowed"로 중단된다
- 영향: `LLR_MATRIX_2.txt`는 iteration 1~8의 그룹 0~4가 모두 분기 그룹(헤더 10, 20, 21)이라, 앞부분 실행에 쓸 수 있는 모드는 사실상 MUTATE_MATRIX와 MUTATE_CSW 둘뿐이다. 시작 검사가 이것을 알리지 않으므로 사용자는 MPI 실행 도중에 알게 된다
- 고칠 방향: `Validate_Config`에서 지금 쓰는 시퀀스의 모드마다 `Check_SW_Branch_Mode_Allowed(initial_LLR_matrix, mode, target_group_indices)`를 불러 오류를 모은다

### 발견 3: 디코더 근거의 인용과 설명 (LOW, 사용자 확인 필요)

소스에서 읽히는 사실 (소스가 실행 파일과 같다는 가정 아래):

- ㉮ `mode.h:22`가 `__AUTO_LLR_OPT__`를 정의하고, 그 갈래에서 `ITER_MAX_HBF`는 0이다 ([common.h:403](../../../../../../0_LDPC_original/src/common.h#L403))
- ㉯ 1 bit 정밀도 조건은 갈래마다 따로 적혀 있다. `__AUTO_LLR_OPT__` 갈래는 상수 4를 쓴다: `(TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)` ([decoder.cpp:4056](../../../../../../0_LDPC_original/src/decoder.cpp#L4056), HCU 판 [4275](../../../../../../0_LDPC_original/src/decoder.cpp#L4275)). 4058행과 4277행은 `#else` 갈래다
- ㉰ `__AUTO_LLR_OPT__` 갈래에서 `flag_BF_on`이 HIGH가 되는 길은 없다. 초기화에서 LOW ([decoder.cpp:609](../../../../../../0_LDPC_original/src/decoder.cpp#L609)), `Select_BF`에서도 `BF_mode`와 SW 문턱을 보지 않고 LOW로 둔다 ([decoder.cpp:2084](../../../../../../0_LDPC_original/src/decoder.cpp#L2084)). HIGH로 두는 줄(2089)은 `#else` 갈래 안에 있다. `main.cpp:232`의 `BF_mode = MODE_BF_ON`은 이 갈래에서 쓰이지 않는다
- ㉱ 그래서 이 소스의 `__AUTO_LLR_OPT__` 판에서는 iteration 1~4에도 4 bit 정밀도 갈래로 가서 행렬의 TH를 읽는다. TH가 모두 0이면 `temp_m >= th1`이 늘 참이라 크기가 `EDGE_MAG_7`(4 bit LLR 판은 `EDGE_MAG_8`)이 되고, 부호 처리도 1 bit 갈래와 같다 ([decoder.cpp:4093](../../../../../../0_LDPC_original/src/decoder.cpp#L4093), [4112](../../../../../../0_LDPC_original/src/decoder.cpp#L4112)). 곧 dv_idx 0의 TH를 0으로 두는 것이 1 bit 정밀도를 흉내 낸다. CH는 `sum_t`에 들어가므로 두 갈래 모두 쓰인다 (DAO가 CH를 고정하지 않는 것과 맞다)

어긋나 보이는 점:

- spec 3.6절 ㉮, `Is_Row_In_HBF_Iterations` docstring, 태스크 문서 2절은 "TH를 읽지 않는다"와 "iter <= ITER_MAX_HBF(4)"를 근거로 든다. 소스의 `__AUTO_LLR_OPT__` 판에서는 TH를 읽되 0이라 1 bit와 같은 출력이 나오는 것이 정확한 설명이다. 규칙(iteration 1~4의 dv_idx 0 TH를 0으로)과 요구 1은 두 설명 어느 쪽에서도 같은 결론이다
- 고칠 방향: 문서의 근거를 "DAO가 돌리는 판(`__AUTO_LLR_OPT__`)은 TH를 읽으며, TH 0이 1 bit 정밀도와 같은 출력을 낸다 (decoder.cpp 4056, 4093)"로 다시 쓴다. 사용자가 쓰는 실행 파일이 다른 판이면 그 판의 조건을 인용한다

참고 사실 (DAO 결함이 아님, 판 차이의 근거): 이 소스의 `Get_Cur_LLR_Idx_FILE`은 iteration을 덮는 마지막 그룹 하나를 고르고 `floor_flag`를 읽지 않으며, 그룹 유형은 0(ITER)과 1(CSW)만 안다 ([decoder.cpp:6985](../../../../../../0_LDPC_original/src/decoder.cpp#L6985), [7051](../../../../../../0_LDPC_original/src/decoder.cpp#L7051)). `LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`의 헤더 유형 10, 20, 21은 두 갈래 어디에도 들지 않는다. 그러므로 SW 분기 매트릭스를 돌리는 실행 파일은 이 소스와 다른 판이다. 위 ㉮~㉱가 그 판에도 성립하는지는 이 환경에서 확인 못 함 (확인하려면 그 판의 `VN_Cal_HD`와 `Select_BF`를 본다).

### 발견 4: dv_idx 0과 `v_deg > DV_5`의 대응 (LOW, 사용자 확인 필요)

- 소스 사실: DV에서 칸을 고를 때 `dv_from[i] <= dv <= dv_to[i]`를 만족하는 첫 i를 쓰고, 어느 범위에도 들지 않으면 칸 0(dv_idx 0)을 쓴다 ([decoder.cpp:7078](../../../../../../0_LDPC_original/src/decoder.cpp#L7078)). 헤더는 `num_para_each_set`, `num_dv`, `dv_from` 목록, `dv_to` 목록 순서로 읽는다 ([local_opt.cpp:61](../../../../../../0_LDPC_original/src/local_opt.cpp#L61)). 두 입력 매트릭스는 `4`, `4`, `11 4 3 2`, `11 4 3 2`이므로 dv_idx 0은 열 차수 11 (그리고 범위 밖 차수)이다
- 어긋날 수 있는 점: 부호에 열 차수 5가 있으면 범위 밖이라 dv_idx 0 칸을 쓰지만 `v_deg > 5`가 아니므로 디코더의 1 bit 대상이 아니다. 그 열도 TH 0으로 1 bit처럼 처리된다. 열 차수 6~10이 있으면 반대로 둘이 맞는다. `Prime_ECC_3.0`의 H-matrix는 저장소에 없어(`Input/Ref_C/Prime_ECC_3.0`에는 `EXE`와 `Initial_LLR_matrix`만 있음) 확인 못 함
- 또 DAO는 헤더 첫 칸이 가장 높은 DV인지 검사하지 않는다. 요구 2가 "첫 DV"를 대상으로 정했으므로 코드는 요구대로다
- 사용자에게 물을 것: 이 부호의 열 차수 집합이 {11, 4, 3, 2}뿐인지

### 발견 5: row 1개짜리 타겟의 MUTATE_CSW (LOW)

- 코드 근거: `Mutate_CSW`는 첫 row(CSW -1)를 빼고 후보를 만든다. row가 1개면 후보가 비어 `[]`를 돌려주고 ([DAO_Main.py:7146](../../../../../SRC/DAO_Main.py#L7146)), `Gen_LLR_Mutate_CSW`는 "No mutations were applied."만 남기고 받은 매트릭스를 그대로 돌려준다 ([DAO_Main.py:3743](../../../../../SRC/DAO_Main.py#L3743)). `Gen_Trial_LLR`은 이것을 생성 성공으로 보고 측정한다
- 영향: 5절의 앞부분 설정에서 stage 2(MUTATE_CSW, 그룹 0)와 stage 8(MUTATE_CSW, 그룹 3)은 trial 전부가 optimal과 같은 매트릭스를 측정한다. 결과가 틀리지는 않고 시간만 쓴다
- 고칠 방향: 변경이 없으면 `None`을 돌려 생성 실패로 세거나, `Initialize_Stage`에서 row 1개짜리 타겟의 MUTATE_CSW stage를 건너뛴다

## 4. 요구 대응 표

| 요구 | 구현한 코드 자리 | 검사 | 빠진 것 |
|------|----------------|------|--------|
| 1. iteration 1~4에서만 dv_idx 0 TH 0 | 판단 [DAO_LLR_MATRIX.py:98](../../../../../SRC/DAO_LLR_MATRIX.py#L98), 유효성 HBF1 [525](../../../../../SRC/DAO_LLR_MATRIX.py#L525), 보정 [752](../../../../../SRC/DAO_LLR_MATRIX.py#L752) [829](../../../../../SRC/DAO_LLR_MATRIX.py#L829), DV 다시 만들기 [DAO_Main.py:4030](../../../../../SRC/DAO_Main.py#L4030), row 다시 만들기 [4167](../../../../../SRC/DAO_Main.py#L4167), 변이 후보 [7105](../../../../../SRC/DAO_Main.py#L7105) | `test_hbf_th_iteration_range.py` 11건. 5절 실행에서 HBF 구간 row는 그룹 0(1~1)과 그룹 1(2~4)뿐 | 없음 (발견 3은 설명의 문제) |
| 2. row 순서와 TH 0 대상은 첫 DV | 제외 칸 `(ch_length, num_parameter_each_set)` [DAO_LLR_MATRIX.py:710](../../../../../SRC/DAO_LLR_MATRIX.py#L710), HBF1과 보정은 `dv_idx == 0` 칸 | 입력 매트릭스 두 개에서 dv_idx 0 TH 칸이 1~3열 | 없음 (디코더 쪽 대응은 발견 4) |
| 3. row가 경계를 걸치지 않음 (1~4, 5~8, 9 이후) | HBF2 [DAO_LLR_MATRIX.py:491](../../../../../SRC/DAO_LLR_MATRIX.py#L491) | 4와 5 사이만 검사 (실행 확인) | 8과 9 사이 검사 없음 (발견 1). HBF 최적화 모드가 꺼지면 4와 5 사이도 검사하지 않음 |
| 4. 앞부분과 뒷부분을 따로 최적화 | 목록 `FIXED_TARGET_GROUP_IDX_LIST` [DAO_Config.py:136](../../../../../SRC/DAO_Config.py#L136), 목록 만들기 [DAO_Main.py:8310](../../../../../SRC/DAO_Main.py#L8310), 목록 검사 [8329](../../../../../SRC/DAO_Main.py#L8329), 분기 모드 제한 [8377](../../../../../SRC/DAO_Main.py#L8377), 보호 구간 [8409](../../../../../SRC/DAO_Main.py#L8409) | 5절: 앞부분과 뒷부분 설정 모두 시작 검사 통과, stage마다 지정 그룹만 타겟 | 분기 모드 제한이 시작 검사에 없음 (발견 2). 앞부분 실행의 모드가 둘로 좁음. 목록 없이 앞부분만 고르는 길은 없음 (`INITIAL_TARGET_GROUP_IDX`는 끝 그룹까지 잡는다) |
| 5. 타겟 값은 그룹 하나하나의 index, 분기 그룹도 하나씩 | [DAO_Main.py:8320](../../../../../SRC/DAO_Main.py#L8320), `_Get_Target_Group_Idx` [7067](../../../../../SRC/DAO_Main.py#L7067) | `test_fixed_target_group_idx_list.py` 22건, `test_target_group_one_by_one.py` 8건. 5절에서 목록 `[0, 1, 2, 3, 4]`가 그대로 타겟 목록 | 없음 |
| 6. 지정 그룹은 분기 index와 상관없이 바뀜 | 마지막 분기 규칙 없음, `Check_SW_Branch_Mode_Allowed`는 모드만 봄 [DAO_Main.py:8396](../../../../../SRC/DAO_Main.py#L8396) | 5절에서 분기 0인 그룹 2, 분기 1인 그룹 3과 4가 차례로 MUTATE_MATRIX 타겟이 되고 중단 없음 | 없음 |

## 5. 앞부분만 바꾸는 실행과 뒷부분만 바꾸는 실행의 설정 예 (`LLR_MATRIX_2.txt`)

그룹 배치: 그룹 0(1~1), 그룹 1(2~4)은 헤더 10(분기 1개), 그룹 2(5~8, 분기 0), 그룹 3(5~5, 분기 1), 그룹 4(6~8, 분기 1), 그룹 5~10은 iteration 9 이후 보통 그룹.

| 실행 | 설정 | 시작 검사 (`Is_LLR_Valid`, 타겟 목록, `Validate_Config`) | stage마다 (모드, 타겟) |
|------|------|------------------------------------------|----------------------|
| 앞부분 (iteration 1~8) | `IS_HBF_OPT = True`, `FIXED_TARGET_GROUP_IDX_LIST = [0, 1, 2, 3, 4]`, `Gen_LLR_Mode_HBF_SEQUENCE = [10, 11]` | 유효, `[0, 1, 2, 3, 4]`, 통과 | (MUTATE_MATRIX, 0) (MUTATE_CSW, 0) (MUTATE_MATRIX, 1) (MUTATE_CSW, 1) ... (MUTATE_CSW, 4). 10 stage 중단 없음 |
| 뒷부분 (iteration 9 이후) 가 | `IS_HBF_OPT = True`, `FIXED_TARGET_GROUP_IDX_LIST = [5, 6, 7, 8, 9, 10]`, `Gen_LLR_Mode_HBF_SEQUENCE = [10, 11, 21, 30, 31, 41, 43, 50, 51]` | 유효, `[5, ..., 10]`, 통과 | 9개 모드가 그룹 5에서 돌고 12번째 stage에 그룹 6으로 넘어감. 중단 없음 |
| 뒷부분 나 | `IS_HBF_OPT = False`, `FIXED_TARGET_GROUP_IDX_LIST = [5, 6, 7, 8, 9, 10]`, `Gen_LLR_Mode_SEQUENCE = [10, 11, 21, 30, 31, 41, 43, 50, 51]` | 유효, `[5, ..., 10]`, 통과 | 가와 같음 |
| 뒷부분 다 | `IS_HBF_OPT = False`, `FIXED_TARGET_GROUP_IDX_LIST = None`, `INITIAL_TARGET_GROUP_IDX = 5`, 기본 `Gen_LLR_Mode_SEQUENCE` | 유효, `[5, ..., 10]`, 통과 | 구조 변경 모드(40, 42, 70)도 그룹 5에서 돎. 중단 없음. 그룹 0~4는 `_Protected_Groups_Changed`가 지킴 |

막히는 설정 (확인용):

- ㉮ 앞부분에 기본 HBF 시퀀스 `[40, 41, 10, 11, 60]`: `Validate_Config`가 INSERT_RANDOM_GROUP(40), SPLIT_GROUP(60)을 알리며 중단 (T4)
- ㉯ 앞부분에 `[10, 11, 21]`: `Validate_Config` 통과 후 stage 3에서 중단 (발견 2)

모든 실행은 `REFC_CONFIG.init_n = 1`, `RUN_DAO_MODE = RUN_OPTIMIZATION`, 매트릭스 index 2로 확인했다. `IS_HBF_OPT`는 Ref-C 실행 인자로 넘어가지 않고 DAO 규칙에만 쓰이므로 (`DAO_CONFIG.IS_HBF_OPT`를 읽는 자리는 `DAO_Main.py` 2605, 4339, 7196, 8182, 8360, 8442, 9971), 뒷부분 실행에서 가와 나의 차이는 그룹 0~1 row에 HBF1과 HBF2를 계속 거는지 뿐이다. 그룹 0~4는 뒷부분 실행에서 타겟이 아니고 보호 구간이라 두 설정의 결과는 같다.

## 6. 통과 관점

- P14 ㉱ iteration 눈금: `__AUTO_LLR_OPT__`에서 `ITER_MAX_HBF`가 0이라 반복 번호 `mn`이 밀리지 않고, row 선택(`Get_Cur_LLR_Idx_FILE(mn)`, [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp#L1138))과 1 bit 조건의 `iter`(`VN_Cal_HD(..., mn)`, 5704행)가 같은 `mn`이다. `iter_start`, `iter_end`와 같은 눈금이고 iteration 1이 `mn` 1이다. 디코더의 `iter <= 4`와 DAO의 `iter_end <= HBF_MAX_ITERATION(4)`도 같은 쪽 부등호다. 문제 없음
- P14 ㉯ `flag_BF_on`: 이 소스의 `__AUTO_LLR_OPT__` 갈래에서는 참이 되는 길이 없다 (발견 3의 사실). DAO 규칙은 TH 0으로 같은 출력을 내므로 결론은 어긋나지 않는다
- P15 요구 1, 2, 5, 6: 코드 자리와 검사가 모두 있고 5절 실행으로 확인했다. 문제 없음
