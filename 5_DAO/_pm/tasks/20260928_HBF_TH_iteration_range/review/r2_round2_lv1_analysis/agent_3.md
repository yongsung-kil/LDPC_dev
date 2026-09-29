# Round 2 에이전트 3: 타겟 목록, seed 모드, 설정과 MPI (P11, P12, P13)

> 작성: 2026-09-29 13:52:35
> 읽은 범위: `git diff dff3dba..2e34036 -- 5_DAO/SRC`, 현재 `DAO_Main.py`의 `Update_Exit_After_Run_Configs`, `Update_RefC_Configs`, `Bcast_Trial_LLR_Mode`, `Initialize_Stage`, `Initialize_LLR_Matrix`, `Gen_Trial_LLR`의 방송 구간(2036~2047), `Setup_Uncor_Pool`, `Build_Target_Group_Indices`, `Check_Fixed_Target_Group_Idx_List`, `Check_SW_Branch_Mode_Allowed`, `Set_Gen_Trial_LLR_Mode`, `Set_Seed_Mode`, `Set_Max_Error`, `Setup`, `Update_Optimal_LLR`, `Validate_Config`, 진입부(10591~10599). `DAO_LLR_MATRIX.py`의 `__init__`, `Is_Row_In_HBF_Iterations`, `Deep_Copy`, `Read_Input_LLR_Matrix` 끝부분. `DAO_Config.py`의 `Set_Configs_Manually`, `DAO_CONFIG`, `HBF_OPT_CONFIG`.
> 실행 확인: `dff3dba`의 SRC를 OS 임시 폴더에 꺼내 현재 SRC와 같은 스크립트로 비교했다 (`LLR_OPT.__new__`, 단일 프로세스, `MPI_Barrier`와 `Bcast_Trial_LLR_Mode`를 빈 함수로 바꿈). 입력은 `LLR_MATRIX_1.txt`, `LLR_MATRIX_2.txt`, `IS_HBF_OPT = True`.

## 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 이번 변경이 만든 것인가 | 확인 방법 |
|---|--------|------|------|------|------|------|
| 1 | MEDIUM | P11 | `FIXED_TARGET_GROUP_IDX_LIST`의 시작 검사가 SW(Syndrome Weight) 분기 모드 제한을 보지 않아, 시작 검사를 통과한 설정이 실행 중간 stage에서 중단된다 | [DAO_Main.py:8329](../../../../../SRC/DAO_Main.py#L8329), [DAO_Main.py:8478](../../../../../SRC/DAO_Main.py#L8478) | 예 (새 설정의 검사 범위). 모드 제한이 stage에서만 도는 것 자체는 예전부터 | 실행 |
| 2 | LOW | P11 | stage 로그의 "Current target index"가 실제 타겟과 다른 그룹을 적는다 (별도 카운터 `current_target_idx`) | [DAO_Main.py:2302](../../../../../SRC/DAO_Main.py#L2302), [DAO_Main.py:2322](../../../../../SRC/DAO_Main.py#L2322), [DAO_Main.py:8468](../../../../../SRC/DAO_Main.py#L8468) | 아니오 (예전부터). 다만 태스크 문서 7절의 남은 확인이 이 로그를 보게 되어 있어 영향이 커졌다 | 실행 |
| 3 | LOW | P11 | `REGEN_DV_CONFIG.ENABLE_FIX_IDX`나 `REGEN_ROW_CONFIG.ENABLE_FIX_IDX`가 켜져 있으면, 목록을 준 실행에서도 쓰이지 않는 `INITIAL_TARGET_GROUP_IDX`의 범위를 검사한다 | [DAO_Main.py:9861](../../../../../SRC/DAO_Main.py#L9861), [DAO_Main.py:9916](../../../../../SRC/DAO_Main.py#L9916) | 아니오 (예전 검사가 새 설정을 모름) | 읽기 |
| 4 | 정보 | P11 | 목록을 주지 않은(None) 실행의 타겟 목록이 SW 분기 매트릭스에서 `dff3dba`와 다르다 (의도한 변경. 아래 상세에 달라지는 경우를 적음) | [DAO_Main.py:8310](../../../../../SRC/DAO_Main.py#L8310), [DAO_Main.py:2295](../../../../../SRC/DAO_Main.py#L2295) | 예 (의도) | 실행 |

## 발견 상세

### 1. 목록 시작 검사가 SW 분기 모드 제한을 빠뜨림 (MEDIUM)

- 재현 조건: `LLR_MATRIX_2.txt`(그룹 0~4가 SW 분기 그룹), `IS_HBF_OPT = True`, `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`, `Gen_LLR_Mode_HBF_SEQUENCE = [10, 11, 41]` (MUTATE_MATRIX, MUTATE_CSW, INSERT_RANDOM_ROW)
- 실행 확인 결과
  - `Check_Fixed_Target_Group_Idx_List`가 오류 없음(`[]`)을 돌려준다. INSERT_RANDOM_ROW(41)는 `FIXED_TARGET_GROUP_ALLOWED_MODES`에 들어 있기 때문이다
  - stage 1(MUTATE_MATRIX, g0)과 stage 2(MUTATE_CSW, g0)는 돈다
  - stage 3에서 `Set_Gen_Trial_LLR_Mode: target groups [0, 1] are SW branch groups, so mode INSERT_RANDOM_ROW (41) is not allowed ...`로 `MPI_Abort`가 불린다
- 코드 근거: 허용 모드 집합이 둘이다. `FIXED_TARGET_GROUP_ALLOWED_MODES`(9개)는 `Validate_Config`가 시작할 때 보고([DAO_Main.py:10010](../../../../../SRC/DAO_Main.py#L10010)), `SW_BRANCH_ALLOWED_MODES`(2개)는 stage마다 `Set_Gen_Trial_LLR_Mode`에서만 본다([DAO_Main.py:8478](../../../../../SRC/DAO_Main.py#L8478)). 목록은 실행 내내 고정이고 목록을 쓰는 동안 그룹 수와 순서가 바뀌지 않으므로, 분기 그룹이 목록에 있는지는 시작할 때 이미 정해진다
- 영향: 앞 stage들의 측정 시간을 쓴 뒤 멈춘다. 결과가 틀리지는 않는다. `SWAP_ROW`, `COPY_ROWS`, `COPY_GROUP`, `INSERT_RANDOM_ROW`, `INSERT_MUTATED_ROW`, `REGEN_DV`, `REGEN_ROW` 모두 같은 경로다
- 고칠 방향: `Check_Fixed_Target_Group_Idx_List`에서 초기 매트릭스로 `Build_SW_Branch_Layout`을 부르고, 목록에 분기 그룹이 있으면 지금 쓰는 시퀀스의 모드마다 `Check_SW_Branch_Mode_Allowed`를 불러 오류를 모은다. None 실행도 같은 검사를 시작 시점에 두면 기본 HBF 시퀀스 중단(아래 통과 관점의 P11 ㉮)도 시작 직후에 알린다

### 2. "Current target index" 로그와 실제 타겟의 어긋남 (LOW, 예전부터)

- 재현 조건: `LLR_MATRIX_2.txt`, `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`, `Gen_LLR_Mode_HBF_SEQUENCE = [10, 11]`
- 실행 확인 결과 (stage, 모드, 실제 타겟 `current_target_group_idx`, 로그 줄)
  - stage 1: MUTATE_MATRIX, g0, `Current target index: 0 (g0)`
  - stage 2: MUTATE_CSW, g0, `Current target index: 1 (g1)`
  - stage 3: MUTATE_MATRIX, g1, `Current target index: 0 (g0)`
  - stage 4: MUTATE_CSW, g1, `Current target index: 1 (g1)`
- 코드 근거: 실제 타겟은 `Set_Gen_Trial_LLR_Mode`가 시퀀스 한 바퀴마다 하나씩 고른다([DAO_Main.py:8468](../../../../../SRC/DAO_Main.py#L8468)). `Initialize_Stage`의 `current_target_idx`는 stage마다 1씩 늘고([DAO_Main.py:2306](../../../../../SRC/DAO_Main.py#L2306)) 로그([DAO_Main.py:2322](../../../../../SRC/DAO_Main.py#L2322))와 restart 그룹 건너뛰기 반복([DAO_Main.py:2309](../../../../../SRC/DAO_Main.py#L2309))만 쓴다. 변이에는 영향이 없다. `Print_Mode_Target_Info`의 `[target_group_indices]` 줄([DAO_Main.py:7229](../../../../../SRC/DAO_Main.py#L7229))은 실제 타겟을 적는다
- 영향: 태스크 문서 7절의 "stage 로그의 `target_group_indices`가 지정한 그룹만 도는지" 확인에서 이 줄을 보면 지정한 그룹이 매 stage 바뀌는 것처럼 읽힌다. 모드가 하나뿐인 시퀀스에서는 두 카운터가 같아 드러나지 않는다
- 고칠 방향: 로그 줄을 `current_target_group_idx` 기준으로 바꾸거나, `current_target_idx`를 `current_target_group_list_index`와 같은 규칙으로 계산한다 (restart 건너뛰기 반복이 쓰는 값이라 함께 봐야 한다)

### 3. 목록을 준 실행에서 쓰이지 않는 INITIAL_TARGET_GROUP_IDX 검사 (LOW, 예전부터)

- 재현 조건: `FIXED_TARGET_GROUP_IDX_LIST`를 주고 `REGEN_DV_CONFIG.ENABLE_FIX_IDX = True`(또는 REGEN_ROW 쪽), `INITIAL_TARGET_GROUP_IDX`가 그룹 수 이상 (예: 그룹 1개 매트릭스와 기본값 1)
- 코드 근거: [DAO_Main.py:9861](../../../../../SRC/DAO_Main.py#L9861)~9864, [DAO_Main.py:9916](../../../../../SRC/DAO_Main.py#L9916)~9919가 `FIXED_TARGET_GROUP_IDX_LIST`를 보지 않고 `INITIAL_TARGET_GROUP_IDX` 범위 오류를 낸다. 그 아래 `self.target_group_indices` 검사는 `Build_Target_Group_Indices`가 만든 목록을 보므로 맞다
- 영향: 쓰지 않는 설정 때문에 시작 검사에서 멈춘다. 드문 조합이다
- 고칠 방향: 두 자리의 `INITIAL_TARGET_GROUP_IDX` 검사를 `FIXED_TARGET_GROUP_IDX_LIST is None`일 때만 한다

### 4. None 실행의 타겟 목록이 dff3dba와 달라지는 경우 (정보)

실행 확인 (시퀀스 `[10]`, stage 1~11, `IS_HBF_OPT = True`)

| 매트릭스, INITIAL_TARGET_GROUP_IDX | dff3dba: 시작 목록 / stage 목록 / 결과 | 현재: 시작 목록 = stage 목록 / 결과 |
|------|------|------|
| `LLR_MATRIX_1`(그룹 12개, 분기 index `[0,0,1,0,1,1,-1,...]`), 0 | `[0..11]` / 만들기 전 중단 / stage 1 중단 (g0은 마지막 분기가 아님) | `[0..11]` / g0부터 차례로 돎 |
| `LLR_MATRIX_1`, 1 | `[1..11]` / 중단 / stage 1 중단 (stage 목록이 묶음 머리 g0으로 당겨짐) | `[1..11]` / g1부터 돎 |
| `LLR_MATRIX_1`, 2 | `[2..11]` / `[2,3,4,6,...,11]`(g5 빠짐) / stage 2 중단 (g3) | `[2..11]` / 돎 |
| `LLR_MATRIX_2`(그룹 11개, 분기 index `[0,0,0,1,1,-1,...]`), 1 | `[1..10]` / `[0,2,3,5,...,10]`(g0이 들어가고 g1, g4 빠짐) / stage 2 중단 (g2) | `[1..10]` / g1부터 돎 |
| `LLR_MATRIX_2`, 3 | `[3..10]` / `[3,5,...,10]`(g4 빠짐) / 돎 | `[3..10]` / 돎 (g4 포함) |

- ㉮ 달라지는 조건: 매트릭스에 SW 분기 그룹이 있을 때만이다. `dff3dba`의 `Initialize_Stage`는 분기 index가 같은 연속 그룹(묶음)을 첫 그룹 하나로 줄였고, 시작 index가 묶음 중간이면 묶음의 첫 그룹으로 당겼다. 그래서 `INITIAL_TARGET_GROUP_IDX = 1`인데 g0이 타겟이 되기도 했다. 지금은 `INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지 하나하나가 타겟이다
- ㉯ `dff3dba`에서는 `Initialize_LLR_Matrix`의 목록(묶음을 줄이지 않음)과 `Initialize_Stage`의 목록(줄임)이 서로 달랐다. 지금은 세 자리가 같은 함수로 같은 목록을 만든다
- ㉰ SW 분기가 없는 매트릭스는 묶음이 모두 그룹 하나라 목록이 같다. 달라지는 곳은 `INITIAL_TARGET_GROUP_IDX >= 그룹 수`일 때 `Initialize_LLR_Matrix`와 `Update_Optimal_LLR`의 복원이 이제 마지막 그룹 하나를 담는다는 점뿐인데, 최적화 실행에서는 [DAO_Main.py:10012](../../../../../SRC/DAO_Main.py#L10012)가 시작 때 막으므로 실제 동작 차이는 없다
- ㉱ 변이 단위도 바뀌었다: 예전에는 묶음 전체의 그룹마다 변이를 골랐고, 지금은 타겟 그룹 하나에서만 고른다 (context.md 요구 5, 6과 같음)

## 통과 관점

- P11 타겟 목록의 생성, 검사, 순환
  - 문제 없음 (발견 1~3 제외). `Build_Target_Group_Indices`는 설정 값과 `len(matrix.groups)`만 읽는다. 잘못 적은 목록은 `Initialize_LLR_Matrix`에서 조용히 걸러진 뒤 바로 다음 `Validate_Config`에서 `MPI_Abort`로 멈춘다 (`Setup` 순서 8863 → 8865). 그 사이에 목록을 쓰는 자리는 없다 (`Print_LLR_Matrix`, `Save_LLR_Matrix`, `Validate_LLR_Matrix`, `Set_Python_Seed`는 목록을 읽지 않음). 목록 검사는 최적화 실행에서만 돌지만 다른 실행 모드는 목록을 쓰지 않는다
  - ㉮ 기본 HBF 시퀀스 `[40, 41, 10, 11, 60]`과 None, `INITIAL_TARGET_GROUP_IDX = 1`을 `LLR_MATRIX_2`에 주면 stage 1에서 INSERT_RANDOM_GROUP(40)이 분기 그룹 제한으로 중단된다. `dff3dba`도 같은 조건에서 stage 1에 중단한다 (실행 확인). 예전부터 있던 것이고 P10 범위다
  - 그룹 수 초과 시 마지막 그룹 대체([DAO_Main.py:8472](../../../../../SRC/DAO_Main.py#L8472))는 목록을 쓰는 실행에서 닿지 않는다. 허용 모드 9개가 그룹 수를 바꾸지 않기 때문이다. 구조 변경 모드가 root에서 고친 목록(2794, 3144, 3478)은 다음 `Initialize_Stage`가 설정에서 다시 만든다 (변경 전과 같음)
  - 목록이 전부 restart 그룹이라 모든 stage가 건너뛰어져도 `max_modification_trial = 0`인 stage가 연속 실패로 세어져 `seq_len * 2`에서 끝난다 ([DAO_Main.py:8184](../../../../../SRC/DAO_Main.py#L8184))
- P12 seed 모드와 uncor 풀
  - 문제 없음. `Update_Exit_After_Run_Configs`가 최적화 실행에서는 LOAD_SEED나 LOAD_VECTOR만 두므로 `Set_Seed_Mode`의 최적화 갈래가 LOAD_NONE으로 중단되는 경로는 설정으로 닿지 않는다. 실행 모드마다 풀(`Setup_Uncor_Pool`)과 seed 모드가 같은 `LOAD_UNCOR_MODE`에서 정해진다 (최적화 seed/vector, TEST_FER와 SAVE_UNCOR는 풀 없이 DEFAULT와 SAVE_UNCOR_SEED, REDECODE는 LOAD_UNCOR_SEED_SAVE_UNCOR_SEED). `Set_Max_Error`는 LOAD_UNCOR_VECTOR를 `is_load_seed_mode`로 받는다. `HBF_OPT_USING_UNCOR`를 읽는 자리는 `reference/` 밖에 남지 않았다. 기존 검사 `test_hbf_seed_mode.py` 3건 통과 (실행 확인)
  - 2단계 테스트 금지 검사([DAO_Main.py:9971](../../../../../SRC/DAO_Main.py#L9971))는 반입 커밋(2811bff)부터 있었고 없앤 seed 갈래와 연결되지 않는다 (Dynamic Partial의 seed 모드 보존이 HBF 갈래보다 앞에 있었음). 금지 이유는 코드에서 찾지 못했다 (확인 못 함. 원형 저장소의 이력이나 작성자 확인이 필요)
- P13 설정 출처와 MPI로 옮기는 값
  - 문제 없음. `Bcast_Trial_LLR_Mode`의 보내는 튜플과 받는 튜플이 6칸, 같은 순서다 ([DAO_Main.py:834](../../../../../SRC/DAO_Main.py#L834)~852). `current_target_bundle`을 읽는 자리는 SRC에 남지 않았다
  - `IS_HBF_OPT`는 진입부에서 `Set_Configs_Manually` 다음 `Update_Configs`(`Update_RefC_Configs`의 내리기)로 모든 rank가 같게 정하고, 그 뒤에 `LLR_MATRIX` 생성과 `Validate_Config`가 온다. `HBF_OPT_CONFIG.__init__`은 부르는 자리가 없다
  - 모든 rank가 부르는 `Initialize_LLR_Matrix`와 `Initialize_Stage`에서 `Build_Target_Group_Indices`는 방송된 `initial_LLR_matrix`와 `optimal_LLR_matrix`의 그룹 수와 설정만 읽으므로 root만 아는 값을 새로 읽지 않는다. 변경 전 `Initialize_Stage`가 각 rank에서 부르던 `Build_SW_Branch_Layout`은 빠졌지만, 분기 배치를 읽는 `Check_SW_Branch_Mode_Allowed`와 `_Protected_Groups_Changed`가 스스로 다시 계산한다 (8389, 8418). root만 목록을 고치는 `Update_Optimal_LLR`의 정리와 복원은 다음 `Initialize_Stage`에서 모든 rank가 같은 값으로 다시 만든다
  - `Deep_Copy`(`copy.deepcopy`)와 pickle 방송 뒤 `is_HBF_OPT`, `HBF_immutable_col_range`, `group_branch_idx`가 보존된다. `LLR_MATRIX_2`로 실행 확인: 원본, 복사본, pickle 왕복 모두 `True (1, 4)`. `__getstate__`나 `__deepcopy__` 정의는 없다
