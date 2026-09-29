# Round 2 에이전트 2: 모드와 trial 흐름 (P7~P10)

> 기준 커밋 2e34036. 줄 번호는 모두 `git archive 2e34036`으로 푼 복사본 기준이고, 실행 확인도 그 복사본의 SRC를 sys.path 맨 앞에 넣어 다시 돌렸다 (결과는 아래와 같음).
> 읽은 범위: `git diff dff3dba..2e34036 -- 5_DAO/SRC`, 현재 `5_DAO/SRC`의 모드 함수 17개(`Gen_Trial_LLR` 1964~2055의 분기와 각 `Gen_LLR_*`), `Set_Gen_Trial_LLR_Mode`(8440~8601), `Check_SW_Branch_Mode_Allowed`, `_Protected_Groups_Changed`, `Check_Fixed_Target_Group_Idx_List`, `Run_Optimization`(8015~8187), `Build_Single_Row_Matrix`, `Validate_Config`, `DAO_LLR_MATRIX.py`의 HBF1, HBF2, 보정. 고치기 전 동작은 `git show dff3dba:5_DAO/SRC/*`를 OS 임시 폴더에 꺼내 같은 입력으로 돌려 비교했다.
> 실행 확인은 모두 단일 프로세스(`LLR_OPT.__new__`)로 했다. 입력은 `LLR_MATRIX_1.txt`, `LLR_MATRIX_2.txt`와, 이 둘에서 메모리 안에서만 만든 두 매트릭스다: ㉮ "1~4 매트릭스" (`LLR_MATRIX_2.txt`의 그룹 0, 1만 남기고 분기 표시를 지운 것, iteration 1~1, 2~4) ㉯ "분기 없는 혼합 매트릭스" (`LLR_MATRIX_2.txt`에서 그룹 3, 4를 빼고 분기 표시를 지운 것, iteration 1~1, 2~4, 5~8, 9~24, ...)

## 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 이번 변경이 만든 것인가 | 확인 방법 |
|---|--------|------|------|------|------------------------|----------|
| 1 | HIGH | P7 | HBF 기본 시퀀스의 INSERT_RANDOM_GROUP이 iteration 5~24 그룹을 만들고, 그 trial이 이제 유효로 통과한다. 이 row는 8과 9 사이 경계를 걸친다 (사용자 요구 3 위반, 검사 없음) | [DAO_Main.py:2685](../../../../../SRC/DAO_Main.py#L2685), [DAO_Config.py:258](../../../../../SRC/DAO_Config.py#L258), [DAO_LLR_MATRIX.py:492](../../../../../SRC/DAO_LLR_MATRIX.py#L492) | 예 (max_iteration 상한 검사를 없애 막혀 있던 결과가 열림) | 실행 (새 소스와 dff3dba 비교) |
| 2 | MEDIUM | P10 | SW 분기가 iteration 1~8에 있는 입력 매트릭스에서 HBF 최적화 모드를 돌리면, 기본 시퀀스 `[40, 41, 10, 11, 60]`은 stage 1에서 MPI_Abort로 멈춘다. `FIXED_TARGET_GROUP_IDX_LIST`의 시작 검사(T4)는 SW 분기 제한을 보지 않아, 허용 모드 아홉 개 가운데 일곱 개가 시작 검사를 지나 중간 stage에서 멈춘다 | [DAO_Main.py:8360](../../../../../SRC/DAO_Main.py#L8360), [DAO_Main.py:8478](../../../../../SRC/DAO_Main.py#L8478) | 예 (고치기 전에는 이 매트릭스가 읽을 때 거부돼 이 경로에 닿지 않았고, T4 검사는 새로 넣은 것) | 실행 |
| 3 | MEDIUM | P8, P10 | COPY_GROUP이 후보 그룹의 `floor_flag`(SW 분기 index)와 헤더 `type_each_group`을 타겟 그룹에 복사한다. 분기 구간 뒤의 보통 그룹을 타겟으로 두면 새 SW 구간이 생기고 유효로 통과한다. 갱신되면 다음 stage가 멈춘다 | [DAO_Main.py:9061](../../../../../SRC/DAO_Main.py#L9061), [DAO_Main.py:9071](../../../../../SRC/DAO_Main.py#L9071) | 아니오 (예전부터). 이번 변경이 COPY_GROUP을 "그룹 구조를 그대로 두는 모드"로 허용 목록에 넣음 | 실행 |
| 4 | MEDIUM | P7, P10 | row가 하나뿐인 그룹이 타겟이면 MUTATE_CSW는 아무것도 바꾸지 않은 매트릭스를 성공으로 돌려준다. 그 stage 전체가 같은 매트릭스를 FER 측정으로 되풀이한다 (stage 시간 제한 1시간까지) | [DAO_Main.py:3743](../../../../../SRC/DAO_Main.py#L3743), [DAO_Main.py:7148](../../../../../SRC/DAO_Main.py#L7148) | 아니오 (예전부터). 이번 변경의 사용 예 `[0, 1]`, `[2, 3]`, `[4, 5]`가 이 그룹을 타겟으로 고른다 | 실행 |
| 5 | MEDIUM | P9 | GEN_SINGLE_ROW와 `IS_HBF_OPT = True`를 함께 쓰면 후보 row(iteration 1~50)가 모두 HBF2로 버려진다. `Validate_Config`가 막지 않아 후보 1,000,000개를 모두 건너뛰고 끝난다 | [DAO_Main.py:10363](../../../../../SRC/DAO_Main.py#L10363), [DAO_Config.py:401](../../../../../SRC/DAO_Config.py#L401), [DAO_Main.py:9977](../../../../../SRC/DAO_Main.py#L9977) | 아니오 (예전에는 max_iteration 상한으로 같은 결과. 버리는 규칙 이름만 바뀜) | 실행 (새 소스와 dff3dba 비교) |
| 6 | LOW | P7 | HBF 최적화 모드에서 모든 trial이 버려지는 stage: GEN_INITIAL_GROUP(iteration 1~20), iteration 4 전에 끝나는 그룹을 타겟으로 한 INSERT_RANDOM_GROUP. 한 stage가 `MAX_OPTIMIZATION_TRIALS`(9999) 곱하기 재시도 5번을 모두 버리고, 버릴 때마다 오류 매트릭스 파일을 쓴다 | [DAO_Main.py:3639](../../../../../SRC/DAO_Main.py#L3639), [DAO_Main.py:2651](../../../../../SRC/DAO_Main.py#L2651), [DAO_Main.py:10078](../../../../../SRC/DAO_Main.py#L10078) | 아니오 (예전에는 이 두 모드가 모든 타겟에서 버려졌다. 이번 변경으로 버려지는 경우가 줄었다) | 실행 |
| 7 | LOW | P7, P8 | SPLIT_GROUP의 back 그룹 변이와 INSERT_MUTATED_ROW의 변이가 HBF 구간 row의 dv_idx 0 TH column도 고른다. 보정이 0으로 되돌려 그 변이는 사라진다 (값은 맞고, trial이 덜 바뀔 뿐) | [DAO_Main.py:3517](../../../../../SRC/DAO_Main.py#L3517), [DAO_Main.py:3568](../../../../../SRC/DAO_Main.py#L3568) | 아니오 (예전부터) | 읽기, 실행 |
| 8 | LOW | P7 | INSERT_RANDOM_GROUP과 SPLIT_GROUP이 유효성 검사 전에 root의 `target_group_indices`를 고친다. 버려진 trial의 고침도 root에 남고 worker에는 가지 않는다 (stage 시작에 다시 만들어져 영향은 그 stage 안에 한정) | [DAO_Main.py:2809](../../../../../SRC/DAO_Main.py#L2809), [DAO_Main.py:3484](../../../../../SRC/DAO_Main.py#L3484), [DAO_Main.py:2040](../../../../../SRC/DAO_Main.py#L2040) | 아니오 (예전부터) | 읽기 |

심각도별: HIGH 1, MEDIUM 4, LOW 3 (모두 8건)

## 발견 상세

### 1. HIGH: INSERT_RANDOM_GROUP이 8과 9 사이 경계를 걸치는 그룹을 만들고 통과한다

- 재현 조건: `IS_HBF_OPT = True`, 시퀀스 기본값 `[40, 41, 10, 11, 60]`, 타겟 그룹의 끝 iteration이 4 (예: 1~4 매트릭스의 그룹 1, iteration 2~4)
- 코드 근거: [DAO_Main.py:2651](../../../../../SRC/DAO_Main.py#L2651)에서 새 그룹은 타겟 그룹 끝 다음 iteration에서 시작하고, [DAO_Main.py:2686](../../../../../SRC/DAO_Main.py#L2686)에서 `INSERT_GROUP_NUM_ITERATION`(20, [DAO_Config.py:258](../../../../../SRC/DAO_Config.py#L258)) 길이를 갖는다. HBF2([DAO_LLR_MATRIX.py:492](../../../../../SRC/DAO_LLR_MATRIX.py#L492))는 4와 5 사이 경계만 본다
- 실행 확인: 1~4 매트릭스, 타겟 1
  - ㉮ 새 소스: 그룹 `[(1,1), (2,4), (5,24)]`, `Correct_LLR_Matrix` 뒤 `Is_LLR_Valid()` = `(True, '')`. 새 그룹 dv_idx 0 TH는 `[30, 25, 15]`, `[25, 19, 2]`, `[27, 13, 8]` (난수, 허용됨). max_iteration 24, `target_group_indices`는 `[1, 2]`
  - ㉯ dff3dba 소스: 같은 매트릭스가 `input max iteration 24 is greater than HBF_MAX_ITERATION 4`로 버려짐
- 영향: HBF 최적화 실행이 iteration 1~4의 값을 다듬는 대신 20 iteration짜리 그룹을 붙여 나간다. iteration을 늘린 매트릭스는 FER이 좋아지기 쉬워 갱신될 가능성이 크고, 다음 INSERT_RANDOM_GROUP stage는 새 그룹 뒤에 또 붙인다. 결과 row는 iteration 5~24로 사용자 요구 3(구간 1~4, 5~8, 9 이후를 걸치지 않음)과 요구 4(앞부분과 뒷부분을 따로 최적화)에 어긋나지만 어떤 검사도 막지 않는다. 이어지는 SPLIT_GROUP도 5~14, 15~24처럼 경계를 걸친 채 나눈다
- 고칠 방향: ㉮ HBF 기본 시퀀스에서 40과 60을 빼거나, HBF 최적화 모드에서 INSERT_RANDOM_GROUP의 iteration을 HBF 구간 안에 머물게 한다 ㉯ 요구 3을 규칙으로 두려면 HBF2를 구간 경계 목록(4, 8)으로 넓힌다. 어느 쪽이든 설계 선택이라 사용자 판정이 필요하다

### 2. MEDIUM: HBF 기본 시퀀스와 SW 분기 입력의 결합, 그리고 시작 검사의 빈틈

- 재현 조건 ㉮: `IS_HBF_OPT = True`, `LLR_MATRIX_2.txt`, `INITIAL_TARGET_GROUP_IDX = 1`(기본), `FIXED_TARGET_GROUP_IDX_LIST = None`, 시퀀스 기본값. 타겟 목록은 `[1, 2, ..., 10]`이고 분기 그룹 1~4가 들어 있다. stage 1의 모드 40에서 `Check_SW_Branch_Mode_Allowed`가 오류를 돌려 [DAO_Main.py:8480](../../../../../SRC/DAO_Main.py#L8480)이 MPI_Abort를 부른다
- 재현 조건 ㉯: `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`, `Gen_LLR_Mode_HBF_SEQUENCE = [10, 11, 41]`. `Check_Fixed_Target_Group_Idx_List`는 빈 목록(문제 없음)을 돌려주고, stage 3(모드 41)에서 SW 검사가 멈춘다
- 실행 확인
  - `Check_SW_Branch_Mode_Allowed(LLR_MATRIX_2, 40, [1..10])`: 오류 문구 돌려줌
  - `Check_Fixed_Target_Group_Idx_List` (`[0, 1]`, 시퀀스 `[10, 11, 41]`): `[]`
  - `Check_SW_Branch_Mode_Allowed(LLR_MATRIX_2, 41, [0, 1])`: `target groups [0, 1] are SW branch groups, so mode INSERT_RANDOM_ROW (41) is not allowed`
  - 타겟 `[0, 1]`에서 모드 21, 30, 31, 41, 43, 50, 51 모두 같은 오류, 10과 11만 None
  - `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`과 기본 HBF 시퀀스: T4가 40과 60을 막음 (시작 시 오류, 정상)
- 영향: 이번 변경의 목표 입력(iteration 1~8이 분기 그룹인 매트릭스)에서 iteration 1~4 그룹을 바꾸는 HBF 실행은 시퀀스가 10과 11로만 이뤄져야 돈다. 이 조건은 시작 검사에 없고, `DAO_spec.md` 3.7절 ㉲는 "HBF 최적화 모드와 SW 분기의 결합은 다루지 않는다"고 적어 사용자가 알 길이 없다. 시퀀스 `[10, 11, 41]`이면 앞 두 stage(각각 최대 1시간)를 돈 뒤에 멈춘다
- 고칠 방향: `Validate_Config`의 RUN_OPTIMIZATION 갈래에서 지금 쓰는 시퀀스의 모드마다 `Check_SW_Branch_Mode_Allowed(initial_LLR_matrix, mode, Build_Target_Group_Indices(initial_LLR_matrix))`를 불러 시작할 때 알린다. `Check_SW_Branch_Mode_Allowed`는 타겟 목록 전체를 보므로 stage마다 결과가 같아 시작 검사로 옮길 수 있다

### 3. MEDIUM: COPY_GROUP이 SW 분기 index와 헤더 표시를 복사한다

- 재현 조건: SW 분기 매트릭스에서 타겟이 분기 구간 뒤의 보통 그룹 (예: `LLR_MATRIX_2.txt`, `FIXED_TARGET_GROUP_IDX_LIST = [5]`, 시퀀스에 31). 후보에는 분기 그룹 0~4가 들어간다 ([DAO_Main.py:4440](../../../../../SRC/DAO_Main.py#L4440)은 restart 그룹과 타겟만 뺀다)
- 코드 근거: [DAO_Main.py:9062](../../../../../SRC/DAO_Main.py#L9062)는 iteration은 타겟 값으로 두면서 `floor_flag=row_data['floor_flag']`로 후보 값을 쓰고, [DAO_Main.py:9071](../../../../../SRC/DAO_Main.py#L9071)은 `type_each_group`도 후보 값으로 바꾼다. `_Protected_Groups_Changed`는 타겟 앞 그룹만 보므로 잡지 않는다
- 실행 확인 (`LLR_MATRIX_2.txt`, 타겟 5, 보정 뒤 유효성)
  - g5 ← g0, g5 ← g1: 꼬리 0, 헤더 10, `(True, '')`. 그룹 5가 iteration 9~24의 분기 1개짜리 새 구간이 됨 (`span_of_group[5] = (9, 24, 1)`)
  - g5 ← g2: `Group 5 header type 20 says 2 branches but the span has 1`로 버려짐
  - g5 ← g3, g4: `SW branch 1 ends at iteration 24 but its span ends at 8`로 버려짐
  - 첫 경우가 갱신된 뒤 타겟 `[5]`로 모드 30, 31, 21, 50을 검사하면 모두 `target groups [5] are SW branch groups` 오류
- 영향: `DAO_spec.md` 3.7절의 "DAO는 분기를 만들거나 없애거나 옮기지 않는다"와 달리 분기가 생긴다. 디코더가 iteration 9~24에서 분기 구간으로 동작하는 매트릭스가 최적 매트릭스로 남을 수 있고, 다음 stage는 멈춘다. 분기 없는 매트릭스에서는 모든 꼬리가 -1이라 일어나지 않는다. HBF 값 규칙은 맞다 (아래 P8 통과 참고)
- 고칠 방향: `Copy_Group`이 iteration처럼 `floor_flag`와 `type_each_group`도 타겟 그룹의 값을 지킨다. 또는 후보를 타겟과 분기 index가 같은 그룹으로 한정한다

### 4. MEDIUM: row 하나짜리 타겟에서 MUTATE_CSW stage가 같은 매트릭스를 되풀이 측정한다

- 재현 조건: 타겟이 row 하나뿐인 그룹 (`LLR_MATRIX_2.txt`의 그룹 0, 3, `LLR_MATRIX_1.txt`의 그룹 0, 4). 이번 변경의 문서 예 `[0, 1]`(태스크 문서 3.3절), `[2, 3]`, spec 3.7절 ㉰의 `[4, 5]`가 이 그룹을 담는다. 문제 2 때문에 이 입력의 HBF 시퀀스는 `[10, 11]`이 사실상 유일하므로 목록 `[0, 1]`이면 stage 2가 곧 이 경우다
- 코드 근거: [DAO_Main.py:7146](../../../../../SRC/DAO_Main.py#L7146)의 후보는 row 1부터라 비고, [DAO_Main.py:7148](../../../../../SRC/DAO_Main.py#L7148)이 빈 목록을 돌려준다. `Gen_LLR_Mutate_CSW`([DAO_Main.py:3753](../../../../../SRC/DAO_Main.py#L3753))는 그래도 매트릭스를 돌려주고, `Gen_Trial_LLR`은 생성 성공으로 보고 측정으로 넘긴다. 같은 매트릭스를 걸러내는 자리는 없다
- 실행 확인: 네 경우 모두 `returned matrix, CSW [-1] -> [-1]`, 로그 `No mutations were applied.`
- 영향: stage가 `MAX_OPTIMIZATION_TRIALS` 또는 stage 시간 제한(`MAX_STAGE_TIMEOUT_SECONDS` 1시간, [DAO_Config.py:321](../../../../../SRC/DAO_Config.py#L321))까지 바뀌지 않은 매트릭스를 FER 측정한다. 결과가 틀리지는 않지만 시간을 버린다. 생성은 "성공"이라 연속 실패 종료에도 걸리지 않는다
- 고칠 방향: 바꾼 것이 없으면 `Gen_LLR_Mutate_CSW`가 None을 돌려주게 하거나, `Set_Gen_Trial_LLR_Mode`에서 SWAP_ROW처럼 row 2개 미만 타겟이면 그 stage를 건너뛴다 (`max_modification_trial = 0`)

### 5. MEDIUM: GEN_SINGLE_ROW와 HBF 최적화 모드

- 재현 조건: `RUN_DAO_MODE = GEN_SINGLE_ROW`, `init_n = 1`, `IS_HBF_OPT = True`
- 코드 근거: [DAO_Main.py:10380](../../../../../SRC/DAO_Main.py#L10380)이 row를 iteration 1~`CANDIDATE_ITERATION`(50)으로 만들고, HBF2가 걸린다. `Validate_Config`의 GEN_SINGLE_ROW 갈래([DAO_Main.py:9977](../../../../../SRC/DAO_Main.py#L9977), [DAO_Main.py:10020](../../../../../SRC/DAO_Main.py#L10020))는 이 조합을 보지 않는다
- 실행 확인: `Build_Single_Row_Matrix(0)`
  - 새 소스: 1~4 매트릭스와 `LLR_MATRIX_2.txt` 모두 None, `Group 0 Row 0 iteration 1~50 crosses the HBF boundary`
  - dff3dba: 1~4 매트릭스에서 `input max iteration 50 is greater than HBF_MAX_ITERATION 4`
  - 별개로, `LLR_MATRIX_2.txt`는 HBF를 끄더라도 `Group 0 header type 1 is a plain group but rows carry SW branch index 0`로 버려진다 (dff3dba에서 확인, 첫 그룹 꼬리를 복사하고 헤더는 1로 두기 때문. HBF와 무관하고 예전부터)
- 영향: 후보 생성이 모두 실패하고 `NUM_GEN_TRIALS`(1,000,000)번 건너뛴 뒤 빈 결과로 끝난다
- 고칠 방향: `Validate_Config`에서 GEN_SINGLE_ROW와 `IS_HBF_OPT`의 조합을 오류로 알리거나, GEN_SINGLE_ROW에서는 `IS_HBF_OPT`를 내린다

### 6. LOW: 모든 trial이 버려지는 HBF stage

- ㉮ GEN_INITIAL_GROUP: 새 그룹 iteration 1~20([DAO_Main.py:3639](../../../../../SRC/DAO_Main.py#L3639), [DAO_Config.py:243](../../../../../SRC/DAO_Config.py#L243)). 실행 확인: `crosses the HBF boundary`로 버려짐. `GenLLRModeHBF`에 들어 있어 HBF 시퀀스에 넣을 수 있다
- ㉯ INSERT_RANDOM_GROUP, 타겟 끝 iteration < 4: 실행 확인, 1~4 매트릭스 타겟 0에서 새 그룹 2~21이 버려짐
- 영향: stage 하나가 9999 trial 곱하기 재시도 5번을 모두 버리고, 버릴 때마다 [DAO_Main.py:10078](../../../../../SRC/DAO_Main.py#L10078)이 오류 매트릭스를 저장한다 (trial마다 파일 이름이 달라 약 9999개). 다른 모드 stage가 성공하면 연속 실패 카운터는 0으로 돌아가므로 실행은 계속된다. 연속 실패 종료(`seq_len * 2`, 기본 HBF 시퀀스에서 10 stage)에 닿으려면 모든 모드가 연달아 실패해야 한다
- 고칠 방향: HBF 최적화 모드에서 새 그룹 iteration이 HBF 경계를 걸치면 생성 단계에서 None을 돌려주고 그 stage를 건너뛴다 (파일 저장 없이)

### 7. LOW: HBF 구간 row의 dv_idx 0 TH를 고르는 변이

- `_generate_mutation_for_group`([DAO_Main.py:3517](../../../../../SRC/DAO_Main.py#L3517))과 `_generate_mutation_for_row`([DAO_Main.py:3568](../../../../../SRC/DAO_Main.py#L3568))는 모든 column을 후보로 둔다. `Generate_Random_Mutation`처럼 `HBF_immutable_col_range`를 빼지 않는다
- 실행 확인: 1~4 매트릭스에서 SPLIT_GROUP 타겟 1은 `[(1,1), (2,3), (4,4)]`로 유효, INSERT_MUTATED_ROW로 g5 row를 g1에 넣으면 dv_idx 0 TH가 보정 뒤 `[0, 0, 0]`이고 유효
- 영향: 값 규칙은 보정이 지킨다. 변이가 그 column에만 떨어지면 SPLIT_GROUP의 back 그룹이 front와 같아져 trial 하나를 버린다
- 고칠 방향: 두 함수에 제외 column 인자를 두고 HBF 구간 row에서는 `HBF_immutable_col_range`를 뺀다

### 8. LOW: 버려진 trial의 타겟 목록 고침이 root에 남음

- [DAO_Main.py:2809](../../../../../SRC/DAO_Main.py#L2809), [DAO_Main.py:3484](../../../../../SRC/DAO_Main.py#L3484)가 생성 함수 안에서 `self.target_group_indices`를 고친다. 그 뒤 SW 보호나 유효성 검사로 버려져도 되돌리지 않고, worker로 보내는 일은 성공일 때만([DAO_Main.py:2040](../../../../../SRC/DAO_Main.py#L2040)) 한다
- 영향: 같은 stage 안에서 root 목록이 trial마다 길어진다. `current_target_group_idx`는 stage 시작에 정해지고, `_Protected_Groups_Changed`의 최솟값은 삽입 위치(타겟 + 1) 앞이라 바뀌지 않으며, 다음 stage에서 다시 만들어지므로 지금 확인한 자리에서는 결과가 바뀌지 않는다. `FIXED_TARGET_GROUP_IDX_LIST`와는 T4가 두 모드를 막아 만나지 않는다
- 고칠 방향: 목록 고침을 `Gen_Trial_LLR`에서 생성 성공과 유효성 통과 뒤로 옮긴다

## 모드 17개 표

"타겟 밖 그룹"은 타겟 그룹 말고 다른 그룹의 값, CSW, row를 쓰는지다 (읽기만 하는 것은 아니오).

| 모드 | 그룹 수를 바꾸나 | 그룹 순서를 바꾸나 | iteration을 바꾸나 | 타겟 밖 그룹을 바꾸나 | 근거 줄 |
|------|----------------|------------------|------------------|-------------------|--------|
| GEN_INITIAL_GROUP (0), 막음 | 예 (그룹 하나로 교체) | 예 | 예 (1~20) | 예 (모두 지움) | [3663](../../../../../SRC/DAO_Main.py#L3663), [3596](../../../../../SRC/DAO_Main.py#L3596) |
| MUTATE_MATRIX (10), 허용 | 아니오 | 아니오 | 아니오 | 아니오 (후보가 타겟 그룹 하나, 튜닝 단계도 같은 stage의 이전 변이를 다시 씀) | [7092](../../../../../SRC/DAO_Main.py#L7092)~[7114](../../../../../SRC/DAO_Main.py#L7114), [3815](../../../../../SRC/DAO_Main.py#L3815) |
| MUTATE_CSW (11), 허용 | 아니오 | 아니오 | 아니오 | 아니오 | [7143](../../../../../SRC/DAO_Main.py#L7143)~[7151](../../../../../SRC/DAO_Main.py#L7151) |
| SWAP_ROW (21), 허용 | 아니오 | 아니오 | 아니오 (값만 교환) | 아니오 | [6367](../../../../../SRC/DAO_Main.py#L6367), [6403](../../../../../SRC/DAO_Main.py#L6403)~[6405](../../../../../SRC/DAO_Main.py#L6405) |
| REORDER_GROUP (22), 막음 | 아니오 | 예 | 예 (다시 계산) | 예 | [6315](../../../../../SRC/DAO_Main.py#L6315), [6214](../../../../../SRC/DAO_Main.py#L6214) |
| COPY_ROWS (30), 허용 | 아니오 | 아니오 | 아니오 | 아니오 (타겟 row 값만 교체, 외부 후보 포함) | [9003](../../../../../SRC/DAO_Main.py#L9003) |
| COPY_GROUP (31), 허용 | 아니오 | 아니오 | 아니오 (타겟 iteration 유지) | 아니오. 단 타겟의 분기 index와 헤더 표시를 후보 값으로 바꿈 (발견 3) | [9063](../../../../../SRC/DAO_Main.py#L9063)~[9064](../../../../../SRC/DAO_Main.py#L9064), [9062](../../../../../SRC/DAO_Main.py#L9062), [9071](../../../../../SRC/DAO_Main.py#L9071) |
| INSERT_RANDOM_GROUP (40), 막음 | 예 | 예 (뒤 그룹 index가 밀림) | 예 (뒤 그룹 +20) | 예 | [2732](../../../../../SRC/DAO_Main.py#L2732), [2718](../../../../../SRC/DAO_Main.py#L2718) |
| INSERT_RANDOM_ROW (41), 허용 | 아니오 | 아니오 | 아니오 (타겟 첫 row 값 복사) | 아니오 | [2417](../../../../../SRC/DAO_Main.py#L2417)~[2419](../../../../../SRC/DAO_Main.py#L2419), [2476](../../../../../SRC/DAO_Main.py#L2476) |
| INSERT_MUTATED_GROUP (42), 막음 | 예 | 예 | 예 (donor 축소, 뒤 그룹 이동) | 예 | [3091](../../../../../SRC/DAO_Main.py#L3091), [3001](../../../../../SRC/DAO_Main.py#L3001), [3080](../../../../../SRC/DAO_Main.py#L3080) |
| INSERT_MUTATED_ROW (43), 허용 | 아니오 | 아니오 | 아니오 (타겟 첫 row 값 복사) | 아니오 (소스 row는 읽기만) | [3279](../../../../../SRC/DAO_Main.py#L3279)~[3281](../../../../../SRC/DAO_Main.py#L3281), [3300](../../../../../SRC/DAO_Main.py#L3300) |
| REGEN_DV (50), 허용 | 아니오 | 아니오 | 아니오 | 아니오 | [4050](../../../../../SRC/DAO_Main.py#L4050) |
| REGEN_ROW (51), 허용 | 아니오 | 아니오 | 아니오 | 아니오 | [4184](../../../../../SRC/DAO_Main.py#L4184) |
| SPLIT_GROUP (60), 막음 | 예 | 예 (뒤 그룹 index +1) | 예 (타겟 구간을 둘로) | 아니오 | [3454](../../../../../SRC/DAO_Main.py#L3454), [3418](../../../../../SRC/DAO_Main.py#L3418) |
| ADJUST_ITERATION (62), 막음 | 아니오 | 아니오 | 예 (donor 전체와 뒤 그룹) | 예 | [4744](../../../../../SRC/DAO_Main.py#L4744)~[4745](../../../../../SRC/DAO_Main.py#L4745) |
| DELETE_ROW (70), 막음 | row 하나 남은 그룹을 지우면 예 | 예 (그룹 삭제 시) | 예 (그룹 삭제 시 1부터 다시 쌓음) | 예 (삭제 후보는 타겟 목록 전체의 row) | [5563](../../../../../SRC/DAO_Main.py#L5563), [5628](../../../../../SRC/DAO_Main.py#L5628), [5637](../../../../../SRC/DAO_Main.py#L5637), [5467](../../../../../SRC/DAO_Main.py#L5467) |
| INSERT_RESTART_GROUP (80), 막음 | 예 | 예 | 예 (다시 쌓음) | 예 | [5921](../../../../../SRC/DAO_Main.py#L5921), [5931](../../../../../SRC/DAO_Main.py#L5931) |

결론: 허용 아홉 모드는 모두 그룹 수, 그룹 순서, iteration을 바꾸지 않고 타겟 그룹 하나만 쓴다 (INSERT_RANDOM_ROW, INSERT_MUTATED_ROW는 타겟의 row 수만 늘린다). 예외는 COPY_GROUP이 타겟의 SW 분기 index와 헤더 표시를 바꾸는 것 하나다 (발견 3). 막은 여덟 모드는 모두 그룹 수, 순서, iteration 가운데 하나 이상을 바꾼다. DELETE_ROW는 row만 지우는 경우(그룹에 row 2개 이상)에는 구조를 바꾸지 않지만 row 하나 남은 그룹을 고르면 그룹을 지우므로 막는 것이 맞다.

## 통과 관점

- P7 ㉮ 경계 걸침 판정: SPLIT_GROUP은 한 그룹의 구간 안에서만 나누므로 입력 row가 경계를 걸치지 않으면 결과도 걸치지 않는다 (실행 확인: 1~4 매트릭스 타겟 1에서 2~3, 4~4로 유효). INSERT_RANDOM_GROUP과 GEN_INITIAL_GROUP이 4와 5 사이를 걸치면 HBF2가 버린다 (실행 확인). 뒤 그룹이 밀려 HBF 구간 밖으로 나가면 `Is_Row_In_HBF_Iterations`가 False가 되어 dv_idx 0 TH 0이 그대로 남는데, 이는 허용 값이다. 8과 9 사이 경계는 발견 1
- P7 ㉰ 연속 실패 종료: `seq_len`이 HBF 시퀀스 길이를 쓰고([DAO_Main.py:8182](../../../../../SRC/DAO_Main.py#L8182)), 성공한 stage가 하나라도 있으면 0으로 돌아간다. 버려지는 모드가 섞여 있어도 다른 모드가 성공하면 종료되지 않는다. 문제 없음 (낭비는 발견 6)
- P8 row를 옮기는 모드의 HBF 값: 분기 없는 혼합 매트릭스에서 실행 확인. COPY_ROWS g1 row 0 ← g3 row 1 (dv_idx 0 TH `[10, 7, 5]`)이 보정 뒤 `[0, 0, 0]`이고 유효, 반대 방향(g3 ← g1)은 `[0, 0, 0]` 그대로 유효. COPY_GROUP g1 ← g3는 iteration 2~4 유지와 TH 0, g3 ← g1은 9~24 유지로 유효. INSERT_MUTATED_ROW(소스 g5)도 보정 뒤 TH 0으로 유효. SWAP_ROW, INSERT_RANDOM_ROW, REGEN_DV(g1은 TH 0으로 생성), REGEN_ROW(g3은 `[30, 24, 17]`로 생성) 모두 유효. 보정이 row의 새 iteration으로 판단하므로 값 이동 방향과 상관없이 맞다. REGEN_DV와 REGEN_ROW의 재사용 값은 같은 stage, 같은 타겟 그룹 안에서만 쓰이고(trial 1에서 초기화) 한 그룹의 row는 iteration이 같아 HBF 판정도 같다. 외부 후보(`_Load_External_Single_Row_Candidates`)는 읽을 때 유효성 검사를 하지 않고 값만 가져오며 같은 보정을 거친다. 문제 없음
- P9 TEST_FER, SAVE_UNCOR, REDECODE: 매트릭스마다 `Initialize_LLR_Matrix`([DAO_Main.py:2338](../../../../../SRC/DAO_Main.py#L2338))가 `IS_HBF_OPT`로 다시 읽고 검사하며 `Build_Target_Group_Indices`로 목록을 다시 만든다. 이 실행 모드들은 타겟 목록을 쓰지 않고, T1~T4 검사는 RUN_OPTIMIZATION 갈래([DAO_Main.py:10010](../../../../../SRC/DAO_Main.py#L10010)) 안에만 있어 이 실행을 막지 않는다. 문제 없음 (GEN_SINGLE_ROW는 발견 5)
- P10 `_Protected_Groups_Changed`: 보호 범위는 목록 최솟값 앞이다. 허용 아홉 모드는 타겟 그룹만 쓰므로 목록이 떨어져 있어도(예: `[0, 6]`, 최솟값 0이라 보호 없음) 타겟 아닌 그룹을 바꾸지 않는다. 비교가 보정보다 앞서지만, `LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`는 HBF 최적화 모드에서 보정해도 바뀌는 row가 없어(실행 확인: 보정 메시지 0건, 바뀐 row 없음) 보호 구간이 보정으로 바뀌는 경우는 확인한 입력에서 없다. 이 부분 문제 없음 (모드 제한 결합은 발견 2, 3)
