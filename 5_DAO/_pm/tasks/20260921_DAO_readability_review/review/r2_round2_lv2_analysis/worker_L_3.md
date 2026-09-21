# Worker L-3: 설정 검증 빈틈과 자기모순(P12), GEN_SINGLE_ROW 독립 경로(P18)

> 작성: 2026-09-21
> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 확인 범위: [DAO_Config.py](5_DAO/SRC/DAO_Config.py) 전체 457줄, [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py) 전체 197줄,
> [DAO_Main.py](5_DAO/SRC/DAO_Main.py)의 `Update_Exit_After_Run_Configs`(403), `Update_RefC_Configs`(418),
> `Update_Path_Configs`(450), `Update_Insert_Group_Configs`(469), `Update_Configs`(475), `Validate_Config`(9647),
> `Run_Single_Row_Generation`(10027)부터 `_Export_Workspace_To_Input`(10371)까지, 그리고 이들이 부르는
> `Set_Gen_Trial_LLR_Mode`(8293), `Set_CSW_Update_Limit`(8285), `Test_Core_Speed`(9020),
> `Get_Ref_C_Args_For_Speed_Test`(6456), `Print_Configs`(7270), `Setup`(8705).
> 검증 방법: Python 3.11로 `DAO_Config`와 `DAO_Main`을 실제 import하여 `Set_Configs_Manually` + `Update_Configs`를
> SIM_IDX 값별로 돌리고 굳은 값을 찍어 확인. 코드는 읽기만 하고 수정하지 않음.

---

## 1절. 설정 값이 굳는 시점

클래스 본문에서 다른 설정이나 자기 자신의 앞선 필드를 읽어 계산하는 필드를 모두 뽑은 표다.
`Set_Configs_Manually`([DAO_Config.py:22](5_DAO/SRC/DAO_Config.py#L22))는 `REFC_CONFIG.init_n` 등을 바꾸고,
`Update_Configs`([DAO_Main.py:475](5_DAO/SRC/DAO_Main.py#L475))가 그 뒤에 한 번만 돈다.

| 설정 클래스.필드 | 계산에 쓰는 다른 설정 | 굳는 시점 | `Set_Configs_Manually` 뒤 재계산 |
|---|---|---|---|
| `INSERT_RANDOM_GROUP_CONFIG.ENABLE_INSERT_RESTART` ([258](5_DAO/SRC/DAO_Config.py#L258)) | `REFC_CONFIG.init_n` | import | 재계산됨 (`Update_Insert_Group_Configs` [471](5_DAO/SRC/DAO_Main.py#L471)) |
| `INSERT_MUTATED_GROUP_CONFIG.ENABLE_INSERT_RESTART` ([271](5_DAO/SRC/DAO_Config.py#L271)) | `REFC_CONFIG.init_n` | import | 재계산됨 (`Update_Insert_Group_Configs` [472](5_DAO/SRC/DAO_Main.py#L472)) |
| `MUTATE_CONFIG.CSW_UPDATE_LIMIT_VALUE` ([251](5_DAO/SRC/DAO_Config.py#L251)) | 자기 클래스의 `ENABLE_CSW_UPDATE_LIMIT` | import (거짓이면 **속성 자체가 생기지 않음**) | 재계산 없음 → 발견 L3-7 |
| `DEBUG_CONFIG`의 7개 토글 ([329](5_DAO/SRC/DAO_Config.py#L329)~[345](5_DAO/SRC/DAO_Config.py#L345)) | 자기 클래스의 `ENABLE_DEBUG_MODE` | import | 재계산 없음. 런타임에 `ENABLE_DEBUG_MODE=True`로 바꿔도 하위 7개는 거짓 그대로 |
| `DEBUG_CONFIG.RANDOM_STATE_TO_SET` ([349](5_DAO/SRC/DAO_Config.py#L349)) | 자기 클래스의 `ENABLE_GET_RANDOM_STATE_FROM_CONFIG` | import | 재계산 없음 |
| `TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS` ([323](5_DAO/SRC/DAO_Config.py#L323)) | 자기 클래스의 `MAX_ECC_MEMORY_RETRY`, `MAX_ECC_MEMORY_RETRY_DELAY` | import (값 1200) | 재계산 없음. 두 원재료를 런타임에 바꿔도 1200 고정 |
| `PATH_CONFIG.BATCH_EXT` ([437](5_DAO/SRC/DAO_Config.py#L437)) | `CURRENT_OS` (실행 중 바뀌지 않는 상수) | import | 재계산 불필요 |
| `SPEED_TEST_REFC_CONFIG.mode_init_seed` ([237](5_DAO/SRC/DAO_Config.py#L237)) | `CORE_SPEED_TEST_SEED` 상수 | import | 재계산 불필요. 다만 **읽는 자리가 없음** → 발견 L3-4 |
| `UNCOR_CONFIG.UNCOR_MATRIX_IDX` ([206](5_DAO/SRC/DAO_Config.py#L206)) | 없음 (평범한 값) | import 또는 `Set_Configs_Manually` | 재계산 대상 아님. SIM_IDX 11/21/31에서는 설정하지 않아 파일 기본값 -1이 그대로 쓰임 |
| `UNCOR_CONFIG.LEN_NO_PS`, `UNCOR_CONFIG.NUM_LINES_PER_UNCOR` ([211](5_DAO/SRC/DAO_Config.py#L211), [214](5_DAO/SRC/DAO_Config.py#L214)) | `UNCOR_CONFIG.LOAD_UNCOR_MODE`, `REFC_CONFIG.init_n` | `Update_RefC_Configs`([442](5_DAO/SRC/DAO_Main.py#L442)) | **재계산이 실패함**. `LOAD_UNCOR_MODE`를 정하는 `Update_Exit_After_Run_Configs`가 뒤에 돌기 때문 → 발견 L3-3 |
| `REFC_CONFIG.NUM_TARGET_CHANNELS` ([191](5_DAO/SRC/DAO_Config.py#L191)) | `REFC_CONFIG.ch_type`과 해당 채널 배열 | `Update_RefC_Configs` | 재계산됨 |
| `UNCOR_CONFIG.LOAD_UNCOR_MODE` ([215](5_DAO/SRC/DAO_Config.py#L215)) | `DAO_CONFIG.RUN_DAO_MODE`, `UNCOR_CONFIG.ENABLE_LOAD_VECTOR` | `Update_Exit_After_Run_Configs`([403](5_DAO/SRC/DAO_Main.py#L403)) | 재계산됨 |
| `PATH_CONFIG`의 경로 15개 ([442](5_DAO/SRC/DAO_Config.py#L442)~[457](5_DAO/SRC/DAO_Config.py#L457)) | `REFC_CONFIG.ECC_VER`, `matrix_sel`, `init_n` | `Update_Path_Configs`([450](5_DAO/SRC/DAO_Main.py#L450)) | 재계산됨 |
| `DAO_CONFIG.IS_HBF_OPT` ([127](5_DAO/SRC/DAO_Config.py#L127)) | `HBF_OPT_CONFIG.__init__`이 `REFC_CONFIG.init_n`으로 정하려는 구조 | **절대 계산되지 않음** | `HBF_OPT_CONFIG`를 인스턴스로 만드는 자리가 저장소 어디에도 없어 `__init__`([367](5_DAO/SRC/DAO_Config.py#L367))이 돌지 않는다. `Update_RefC_Configs`([440](5_DAO/SRC/DAO_Main.py#L440))는 거짓으로 내리기만 한다 → 발견 L3-2 참고 |

### 1-1. `HBF_OPT_CONFIG.__init__` 부수효과가 일어나는 시점

전 소스를 grep한 결과 `HBF_OPT_CONFIG`는 ㉮ `CONFIGS` 목록의 원소([DAO_Config.py:415](5_DAO/SRC/DAO_Config.py#L415)),
㉯ 클래스 속성 읽기 5곳([DAO_LLR_MATRIX.py:42](5_DAO/SRC/DAO_LLR_MATRIX.py#L42), [377](5_DAO/SRC/DAO_LLR_MATRIX.py#L377),
[443](5_DAO/SRC/DAO_LLR_MATRIX.py#L443), [DAO_Main.py:4008](5_DAO/SRC/DAO_Main.py#L4008), [4145](5_DAO/SRC/DAO_Main.py#L4145),
[8508](5_DAO/SRC/DAO_Main.py#L8508))로만 나타난다. `HBF_OPT_CONFIG()` 호출이 없으므로 `__init__`의
`DAO_CONFIG.IS_HBF_OPT` 대입은 한 번도 실행되지 않는다. 따라서 HBF 최적화를 켜는 길은
[DAO_Config.py:127](5_DAO/SRC/DAO_Config.py#L127)을 직접 `True`로 고치는 것뿐이고, 그렇게 켜면 발견 L3-2로 곧장 중단된다.

### 1-2. `SPEED_TEST_REFC_CONFIG` 상속 관계

| 갈래 | 필드 |
|---|---|
| 부모를 그대로 따라가는 필드 (부모가 바뀌면 따라 바뀜) | `ECC_VER`, `matrix_sel`, `init_n`, `fixed_erasure_ratios`, `mode_all_one_cw`, `CRC_Option_F_P`, `mode_iter`, `mode_scenario`, `CRC_skip_mode`, `HighDV_skip_mode`, `LLR_matrix_idx`, `MAX_DECODING_ITERATION`, `NUM_TARGET_CHANNELS` |
| 자식이 가리는 필드 | `fn`, `max_num_test`, `ch_type`, `RBERs`, `num_fixed_errs`, `fixed_SCRs`, `fixed_SERs`, `mode_seed`, `mode_init_seed` |
| 자식 전용 필드 | `ENABLE_CORE_SPEED_TEST`, `CORE_SPEED_CUTOFF_RATIO`, `RECHECK_INTERVAL_STAGES`, `RECHECK_INTERVAL_SECONDS` |
| `Update_RefC_Configs`가 자식에 덮어쓰는 필드 | `str_matrix_name` ([DAO_Main.py:448](5_DAO/SRC/DAO_Main.py#L448)). 이 대입이 자식 `__dict__`에 값을 만들어 상속 고리를 끊는다 |

**채널 수 어긋남 여부: 문제 없음.** 속도 테스트 인자를 만드는 `Get_Ref_C_Args_For_Speed_Test`
([DAO_Main.py:6456](5_DAO/SRC/DAO_Main.py#L6456))를 부르는 자리는 `Make_Batch_File_For_Speed_Test`
([6506](5_DAO/SRC/DAO_Main.py#L6506)) 하나이고, 그것을 부르는 `Test_Core_Speed`([9041](5_DAO/SRC/DAO_Main.py#L9041))는
언제나 `ch_idx=0`을 넘긴다. 길이 1짜리 배열에 0번만 접근하므로 IndexError가 생기지 않는다.
상속으로 받는 `fixed_erasure_ratios`도 `Update_RefC_Configs`가 채널 수만큼 채우므로 0번은 늘 있다.
다만 속도 테스트에서 실제로 쓰이는 시드가 어긋나는 별도 문제가 있다 (발견 L3-4).

---

## 2절. `Validate_Config`가 잡는 것과 놓치는 것

`Validate_Config`([DAO_Main.py:9647](5_DAO/SRC/DAO_Main.py#L9647))는 `Setup`([8705](5_DAO/SRC/DAO_Main.py#L8705))에서
`Set_Work_Space` → `Initialize_LLR_Matrix` → `Set_Python_Seed` 다음에 불린다.

### 2-1. 잡는 것

| 검사 대상 | 줄 | 실제로 걸러지는가 |
|---|---|---|
| `INSERT_RANDOM_GROUP_CONFIG.INSERT_GROUP_NUM_ROWS` 양수와 CSW 범위 수용량 | [9650](5_DAO/SRC/DAO_Main.py#L9650), [9665](5_DAO/SRC/DAO_Main.py#L9665) | 예 |
| `MAX_CSW`/`MIN_CSW`/`STEP_CSW` 관계 | [9652](5_DAO/SRC/DAO_Main.py#L9652)~[9662](5_DAO/SRC/DAO_Main.py#L9662) | 예 (상수라 사실상 고정) |
| 초기 매트릭스 인덱스 음수, 빈 목록, 최적화 모드와 목록 병용, 중복 경고 | [9673](5_DAO/SRC/DAO_Main.py#L9673)~[9686](5_DAO/SRC/DAO_Main.py#L9686) | 부분적. GEN_SINGLE_ROW가 빠져 있음 (발견 L3-9) |
| `REFC_CONFIG.max_num_test` 양수 | [9688](5_DAO/SRC/DAO_Main.py#L9688) | 예 |
| REGEN_DV / REGEN_ROW의 고정 인덱스 범위, 타겟 그룹 범위 | [9692](5_DAO/SRC/DAO_Main.py#L9692)~[9786](5_DAO/SRC/DAO_Main.py#L9786) | 예. 단 `ENABLE_FIX_IDX`가 참일 때만 |
| REDECODE + Two-stage 금지 | [9788](5_DAO/SRC/DAO_Main.py#L9788) | 예 |
| Two-stage + LOAD_NONE / LOAD_VECTOR / IS_HBF_OPT 금지 | [9796](5_DAO/SRC/DAO_Main.py#L9796)~[9812](5_DAO/SRC/DAO_Main.py#L9812) | 예 |
| GEN_SINGLE_ROW + ENABLE_LOAD_VECTOR / ENABLE_TWO_STAGE_TEST 금지 | [9815](5_DAO/SRC/DAO_Main.py#L9815)~[9827](5_DAO/SRC/DAO_Main.py#L9827) | 예 |
| 모드별 `MAX_TRIAL`이 -1 또는 양수 | [9833](5_DAO/SRC/DAO_Main.py#L9833)~[9845](5_DAO/SRC/DAO_Main.py#L9845) | 예. **누락 없음**. `MAX_TRIAL`을 가진 설정 클래스는 DAO_Config.py에 9개(240, 245, 255, 269, 287, 298, 308, 364, 384줄)이고 검증 목록도 같은 9개다 |
| `INITIAL_TARGET_GROUP_IDX >= 그룹 수` | [9848](5_DAO/SRC/DAO_Main.py#L9848) | 예. 단 최적화 모드에서만, 그리고 음수는 안 봄 (발견 L3-10) |
| `SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_SECONDS >= 0` | [9852](5_DAO/SRC/DAO_Main.py#L9852) | 예 |
| GEN_SINGLE_ROW의 `NUM_GEN_TRIALS`, `CANDIDATE_ITERATION`, `SPEED_TEST_RECHECK_INTERVAL_SECONDS` | [9855](5_DAO/SRC/DAO_Main.py#L9855)~[9861](5_DAO/SRC/DAO_Main.py#L9861) | 예 (하한만) |
| 외부 single row 후보 디렉토리 존재 여부, 상한 양수 | [9863](5_DAO/SRC/DAO_Main.py#L9863)~[9874](5_DAO/SRC/DAO_Main.py#L9874) | 예 |
| 채널 파라미터 길이 | [9881](5_DAO/SRC/DAO_Main.py#L9881)~[9902](5_DAO/SRC/DAO_Main.py#L9902) | 5개 검사 중 3개는 항진명제 (2-2 참고) |

### 2-2. 채널 길이 검사가 `Update_RefC_Configs` 뒤에 돌아 생기는 결과

`Update_RefC_Configs`([DAO_Main.py:418](5_DAO/SRC/DAO_Main.py#L418))가 `NUM_TARGET_CHANNELS`를 기준 배열의 길이로
정하고 나머지 배열을 그 길이만큼 다시 채우므로, 뒤이은 길이 검사 다섯 개 중 세 개는 결코 실패할 수 없다.

| ch_type | 검사 | 판정 |
|---|---|---|
| 1 (RBER) | `len(RBERs) != NUM_TARGET_CHANNELS` | 항진명제. `NUM_TARGET_CHANNELS = len(RBERs)`로 정의됨 |
| 2 (FIXED_ERROR) | `len(num_fixed_errs) != NUM_TARGET_CHANNELS` | 항진명제 |
| 3 (STRONG_ERROR) | `len(num_fixed_errs) != NUM_TARGET_CHANNELS` | 항진명제 |
| 3 | `len(fixed_SCRs) != NUM_TARGET_CHANNELS` | **실제로 걸림**. ch_type 3에서만 `fixed_SCRs`를 다시 채우지 않기 때문 |
| 3 | `len(fixed_SERs) != NUM_TARGET_CHANNELS` | **실제로 걸림** |

실행으로 확인한 SIM_IDX별 결과다.

| SIM_IDX | ch_type | 채널 수 | (RBER, nfe, SCR, SER, erasure) 길이 | 판정 |
|---|---|---|---|---|
| 없음 (파일 기본값) | 2 | 1 | (1,1,1,1,1) | 통과 |
| 10, 11, 12 | 2 | 2 | (2,2,2,2,2) | 통과 |
| **20, 21, 22** | 3 | 2 | (2,2,**1**,**1**,2) | **MPI_Abort** |
| 30, 31, 32 | 1 | 2 | (2,2,2,2,2) | 통과 |

### 2-3. 놓치는 것

| 놓치는 조합 | 터지는 자리와 시점 |
|---|---|
| `Gen_LLR_Mode_SEQUENCE` 원소가 `GenLLRMode` 값이 아님 | `GenLLRMode(selected_mode).name` ([DAO_Main.py:8309](5_DAO/SRC/DAO_Main.py#L8309))에서 ValueError. 초기 테스트를 다 마친 뒤 첫 stage에 터짐 |
| `Gen_LLR_Mode_HBF_SEQUENCE` 원소 전부가 잘못된 값 | 같은 자리. `IS_HBF_OPT=True`이면 100% 재현 (발견 L3-2) |
| `INITIAL_TARGET_GROUP_IDX` 음수 (`ENABLE_FIX_IDX`가 거짓일 때) | 예외 없이 통과. `range(-1, n)` ([DAO_Main.py:2329](5_DAO/SRC/DAO_Main.py#L2329), [2271](5_DAO/SRC/DAO_Main.py#L2271))가 -1을 목록에 넣어 마지막 그룹이 중복 타겟이 됨 (발견 L3-10) |
| `REFC_CONFIG.init_n`이 1, 2, 3이 아님 | `MODE_MAP[init_n]` KeyError가 `Update_Path_Configs`([DAO_Main.py:459](5_DAO/SRC/DAO_Main.py#L459))에서, 즉 `LLR_OPT`가 생기기도 전에 터짐. `__main__`의 except가 `comm.Abort(1)`만 부르므로 로그 파일도 남지 않음 |
| `REFC_CONFIG.ECC_VER`가 "2.4"도 "3.0"도 아님 | 검사 없음. `Get_Ref_C_Args`가 조용히 3.0 인자 배치를 씀 |
| `MUTATE_CONFIG.ENABLE_CSW_UPDATE_LIMIT=True`인데 `CSW_UPDATE_LIMIT_VALUE` 없음 | `Set_CSW_Update_Limit`([DAO_Main.py:8288](5_DAO/SRC/DAO_Main.py#L8288))에서 AttributeError (발견 L3-7) |
| `DAO_CONFIG.MAX_OPTIMIZATION_STAGE <= 0` | 검사 없음. stage 루프가 한 번도 안 돌고 정상 종료처럼 끝남 |
| `SINGLE_ROW_CONFIG.TOP_K <= 0` | 검사 없음. 0이면 아무 매트릭스도 저장되지 않고, 음수면 상위 후보만 버리고 나머지를 저장함 (발견 L3-12) |
| `SINGLE_ROW_CONFIG.END_FLAG_CHECK_INTERVAL <= 0` | 검사 없음. 종료 플래그 검사 블록이 통째로 건너뛰어져 사용자가 정상 종료를 시킬 수 없음 |
| `SINGLE_ROW_CONFIG.RANKING_UPDATE_INTERVAL <= 0` | 검사 없음. 중간 저장이 사라져 강제 종료 시 결과 전량 유실 |
| GEN_SINGLE_ROW + `INITIAL_MATRIX_IDX_LIST` | 검사에서 빠짐. 오류 문구 자체가 "TEST_FER/SAVE_UNCOR/REDECODE 전용"이라고 말하면서 GEN_SINGLE_ROW를 막지 않음 (발견 L3-9) |
| GEN_SINGLE_ROW + `IS_HBF_OPT=True` | 검사 없음. `CANDIDATE_ITERATION`(50)이 `HBF_MAX_ITERATION`(4)을 넘어 모든 후보가 무효 판정 (발견 L3-15) |
| 초기 매트릭스 로드가 먼저 실패하는 경우 | `Initialize_LLR_Matrix`가 `Validate_Config`보다 앞에 있어([DAO_Main.py:8710](5_DAO/SRC/DAO_Main.py#L8710)~[8712](5_DAO/SRC/DAO_Main.py#L8712)) 설정 오류 목록을 보지 못하고 `Load_Initial_LLR_Matrix`의 MPI_Abort([2581](5_DAO/SRC/DAO_Main.py#L2581))로 끝난다. 다만 이 자리는 경로와 원인을 포함한 메시지를 남기므로 진단 손실은 작다 |

---

## 3절. GEN_SINGLE_ROW 경로 확인 결과

### 3-1. stop idx 파일과 종료 플래그 주기 검사 (실마리 ㉶ 대응 항목)

| 항목 | 본 최적화 루프 | GEN_SINGLE_ROW | 판정 |
|---|---|---|---|
| DAO 종료 플래그 읽기 | root만 읽고 `_safe_bcast`로 전파 ([DAO_Main.py:8071](5_DAO/SRC/DAO_Main.py#L8071)~[8077](5_DAO/SRC/DAO_Main.py#L8077), [8178](5_DAO/SRC/DAO_Main.py#L8178)~[8183](5_DAO/SRC/DAO_Main.py#L8183)) | **모든 rank가 각자 파일을 읽음** ([10058](5_DAO/SRC/DAO_Main.py#L10058)) | 규칙이 다름 (발견 L3-5) |
| 배리어 | 플래그 읽기 앞뒤로 bcast가 동기화 | 읽기 직전 `MPI_Barrier` 한 번 ([10056](5_DAO/SRC/DAO_Main.py#L10056)) | 배리어는 읽기를 원자적으로 만들지 못함 |
| stop idx 기록 | 해당 개념 없음 | `_Write_Stop_Idx`([1125](5_DAO/SRC/DAO_Main.py#L1125))가 root 가드를 갖고 파일로 씀 | 기록 자체는 안전 |
| stop idx 읽기 | 해당 개념 없음 | `_Read_Stop_Idx`([1136](5_DAO/SRC/DAO_Main.py#L1136))를 부르는 자리가 없음 | 죽은 코드 (발견 L3-16) |

### 3-2. Top-K 저장과 하위 후보 삭제

- root 전용 여부: **맞다.** 중간 갱신([10164](5_DAO/SRC/DAO_Main.py#L10164))과 최종 갱신([10185](5_DAO/SRC/DAO_Main.py#L10185)) 모두 `if self.is_root:` 안에 있다.
- 하위 후보 삭제: **실제로 돈다.** `_Save_Top_K_Matrices`([10256](5_DAO/SRC/DAO_Main.py#L10256))가 디렉토리를 훑어 Top-K 이름에 없는 파일을 지우고 새 진입만 저장한다.
- 파일이 쌓이는가: **쌓이지 않는다.** 기준 디렉토리마다 파일 수가 `TOP_K`로 묶인다. `NUM_GEN_TRIALS`(기본 1,000,000)와 `RANKING_UPDATE_INTERVAL`(기본 100) 조합에서도 디스크 사용량은 유계다.
- 대신 **메모리가 쌓인다.** `candidates` 리스트([10044](5_DAO/SRC/DAO_Main.py#L10044), [10139](5_DAO/SRC/DAO_Main.py#L10139))는 후보마다 `LLR_MATRIX` 객체 전체를 담고 한 번도 줄지 않는다. 그리고 100회마다 이 전체 목록을 다시 정렬한다 (발견 L3-6).

### 3-3. `Build_Single_Row_Matrix`의 헤더 채움 (항목 ㉸)

`_Replace_With_Single_Group`([DAO_Main.py:3570](5_DAO/SRC/DAO_Main.py#L3570))이 `num_group=1`,
`num_row_each_group=[1]`, `type_each_group=[1]`, `restart_iter=[]`, `num_restart=0`, `max_iteration`을 채우고,
나머지 헤더(`num_parameter_each_set`, `num_dv`, `dv_from`, `dv_to`, `max_value`, `min_value`)는
`Deep_Copy`로 초기 매트릭스에서 그대로 온다. `Is_LLR_Valid`([DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py))가 보는
필드는 모두 채워진다. **정상 경로에서는 통과한다.**

한 가지 어긋남이 있다. `Is_LLR_Valid`는 `row.floor_flag != -1`을 오류로 잡는데,
`Build_Single_Row_Matrix`([10203](5_DAO/SRC/DAO_Main.py#L10203))의 방어용 기본값은 `0`이다 (발견 L3-17).

### 3-4. `_Export_Workspace_To_Input`이 Input을 덮어쓰는가 (항목 ㉹)

**덮어쓰지 않는다.** `_Export_Workspace_To_Input`([10371](5_DAO/SRC/DAO_Main.py#L10371))은
`INPUT_SINGLE_ROW_LLR_MATRIX_DIR_PATH` 아래에 초 단위 타임스탬프로 새 폴더를 만들고 거기에만 복사하며,
기존 파일을 지우지 않는다. `Cleanup_Session`([DAO_Main.py](5_DAO/SRC/DAO_Main.py))도 `.exe`, `.bat`, `.sh`, `.tmp`와
`Process*` 디렉토리만 지우므로 `9_Single_Row_Candidates`는 세션에 남는다.

금지 조합 확인: `ENABLE_LOAD_VECTOR`와 `ENABLE_TWO_STAGE_TEST`는 둘 다 `Validate_Config`
([9815](5_DAO/SRC/DAO_Main.py#L9815)~[9827](5_DAO/SRC/DAO_Main.py#L9827))에서 막혀 있다.
막히지 않은 조합은 `INITIAL_MATRIX_IDX_LIST`(발견 L3-9)와 `IS_HBF_OPT`(발견 L3-15) 둘이다.

### 3-5. 실마리 ㉳ 결론 한 줄 (팀 T와 겹침)

`TEST_MODE_DIR_NAME`([DAO_Constants.py:76](5_DAO/SRC/DAO_Constants.py#L76))에 `TestMode.FULL` 항목이 없는 것은 맞으나
이 표를 읽는 자리가 저장소 어디에도 없어 KeyError는 나지 않고, 실제 디렉토리명은
[DAO_Main.py:1673](5_DAO/SRC/DAO_Main.py#L1673), [7404](5_DAO/SRC/DAO_Main.py#L7404),
[7515](5_DAO/SRC/DAO_Main.py#L7515), [8954](5_DAO/SRC/DAO_Main.py#L8954)에서 문자열로 직접 만들어진다 (죽은 상수).

---

## 4절. 발견

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|---|---|---|---|---|
| L3-1 | CRITICAL | 2SD 빠른 설정 프리셋 3개(SIM_IDX 20, 21, 22)가 시작 직후 MPI_Abort로 죽는다. `ch_type=3`인데 `num_fixed_errs`는 채널 2개분, `fixed_SCRs`와 `fixed_SERs`는 1개분이라 길이 검사에 걸린다. `Update_RefC_Configs`의 ch_type 3 분기는 이 두 배열을 채널 수만큼 다시 채우지 않는다 | [DAO_Config.py:65](5_DAO/SRC/DAO_Config.py#L65), [77](5_DAO/SRC/DAO_Config.py#L77), [86](5_DAO/SRC/DAO_Config.py#L86) / 검사는 [DAO_Main.py:9893](5_DAO/SRC/DAO_Main.py#L9893) / 재계산 누락은 [DAO_Main.py:433](5_DAO/SRC/DAO_Main.py#L433) | `python DAO_Main.py 20` (21, 22도 같음). Python 실행으로 길이 (2,2,1,1,2)와 `NUM_TARGET_CHANNELS=2` 확인 | ㉮ 즉효: [DAO_Config.py:65](5_DAO/SRC/DAO_Config.py#L65), [66](5_DAO/SRC/DAO_Config.py#L66), [77](5_DAO/SRC/DAO_Config.py#L77), [78](5_DAO/SRC/DAO_Config.py#L78), [86](5_DAO/SRC/DAO_Config.py#L86), [87](5_DAO/SRC/DAO_Config.py#L87)의 `fixed_SCRs`, `fixed_SERs`를 채널 수에 맞춰 원소 2개로 적는다. ㉯ 근본: `Update_RefC_Configs`의 `elif REFC_CONFIG.ch_type == 3:` 블록([DAO_Main.py:433](5_DAO/SRC/DAO_Main.py#L433))에 길이 1이면 채널 수만큼 복제하는 두 줄을 넣는다 |
| L3-2 | CRITICAL | `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`의 다섯 값이 모두 `GenLLRMode`에 없다(유효 값은 0, 10, 11, 21, 22, 30, 31, 40~43, 50, 51, 60, 62, 70, 80). `IS_HBF_OPT=True`이면 root가 stage 1에서 `GenLLRMode(7)`로 ValueError를 내고, 예외가 `Main`까지 올라가 `MPI_Abort`로 전체 작업이 죽는다. 뜻을 담은 `GenLLRModeHBF` 열거형은 정의만 되어 있고 읽는 자리가 없다 | [DAO_Config.py:134](5_DAO/SRC/DAO_Config.py#L134), [DAO_Constants.py:43](5_DAO/SRC/DAO_Constants.py#L43) / 터지는 자리 [DAO_Main.py:8309](5_DAO/SRC/DAO_Main.py#L8309) | [DAO_Config.py:127](5_DAO/SRC/DAO_Config.py#L127)을 `True`로 두고 `init_n=1`로 최적화 실행. `python -c "from DAO_Constants import GenLLRMode; GenLLRMode(7)"`로 ValueError 확인 | ㉮ [DAO_Config.py:134](5_DAO/SRC/DAO_Config.py#L134)를 `GenLLRModeHBF` 멤버 값으로 다시 적는다 (예: `[10, 11, 21, 40, 41]`). ㉯ `Set_Gen_Trial_LLR_Mode`([DAO_Main.py:8295](5_DAO/SRC/DAO_Main.py#L8295))가 HBF 분기에서 `GenLLRModeHBF`로 이름을 뽑게 해 두 열거형의 쓰임을 잇는다. ㉰ `Validate_Config`에 두 시퀀스 원소가 열거형 값 집합에 드는지 보는 검사를 더한다 |
| L3-3 | HIGH | `Update_Configs`가 `Update_RefC_Configs`를 먼저, `Update_Exit_After_Run_Configs`를 나중에 부른다. 그런데 앞쪽이 뒤쪽이 정하는 `UNCOR_CONFIG.LOAD_UNCOR_MODE`를 읽는다. 그 결과 `ENABLE_LOAD_VECTOR=True`여도 `LEN_NO_PS`가 0, `NUM_LINES_PER_UNCOR`가 1로 남아 uncor 벡터 한 줄을 uncor 한 개로 세고 쪼갠다 | [DAO_Main.py:475](5_DAO/SRC/DAO_Main.py#L475)~[479](5_DAO/SRC/DAO_Main.py#L479), 읽는 자리 [442](5_DAO/SRC/DAO_Main.py#L442)~[447](5_DAO/SRC/DAO_Main.py#L447), 쓰는 자리 [414](5_DAO/SRC/DAO_Main.py#L414) / 잘못된 값이 쓰이는 곳 [1042](5_DAO/SRC/DAO_Main.py#L1042), [1567](5_DAO/SRC/DAO_Main.py#L1567), [1579](5_DAO/SRC/DAO_Main.py#L1579), [7420](5_DAO/SRC/DAO_Main.py#L7420) | [DAO_Config.py:209](5_DAO/SRC/DAO_Config.py#L209) `ENABLE_LOAD_VECTOR = True`로 최적화 실행. Python 실행으로 `LEN_NO_PS=0`, `NUM_LINES_PER_UNCOR=1` 확인. `Update_RefC_Configs()`를 한 번 더 부르면 36864와 144로 바뀌어 순서 문제임이 드러남 | `Update_Configs`([DAO_Main.py:475](5_DAO/SRC/DAO_Main.py#L475))에서 `Update_Exit_After_Run_Configs()`를 `Update_RefC_Configs()` 앞으로 옮긴다. 옮긴 뒤 `Update_Exit_After_Run_Configs`가 `REFC_CONFIG`의 값을 읽지 않음을 확인했으므로 새 순환 의존은 생기지 않는다 |
| L3-4 | HIGH | 코어 속도 테스트가 rank마다 다른 초기 시드로 돈다. `Test_Core_Speed`의 설명은 "모든 프로세스가 동일한 시드(CORE_SPEED_TEST_SEED)로"라고 적혀 있고 `SPEED_TEST_REFC_CONFIG.mode_init_seed = CORE_SPEED_TEST_SEED`도 있는데, 인자 12번 자리에 `self.rank`가 들어가고 `mode_init_seed`를 읽는 자리는 어디에도 없다. 서로 다른 프레임을 복호한 시간을 비교하므로 정상 코어가 느린 코어로 몰려 제외될 수 있다 | 설명 [DAO_Main.py:9022](5_DAO/SRC/DAO_Main.py#L9022), 인자 [6471](5_DAO/SRC/DAO_Main.py#L6471)과 [6494](5_DAO/SRC/DAO_Main.py#L6494), 설정 [DAO_Config.py:237](5_DAO/SRC/DAO_Config.py#L237) | `SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST=True`(기본값)로 2개 이상 rank 실행. `max_num_test=1`, `RBERs=[0.1]`이라 시드에 따라 복호 반복 수가 크게 흔들린다 | [DAO_Main.py:6471](5_DAO/SRC/DAO_Main.py#L6471)과 [6494](5_DAO/SRC/DAO_Main.py#L6494)의 `self.rank`를 `SPEED_TEST_REFC_CONFIG.mode_init_seed`로 바꾼다 (ECC_VER 두 분기 모두). 주석 `#12 (고정 시드)`도 값과 맞게 다시 쓴다 |
| L3-5 | CRITICAL | GEN_SINGLE_ROW의 종료 플래그 검사가 본 루프와 다른 규칙을 쓴다. 본 루프는 root만 읽고 bcast하는데, 여기서는 모든 rank가 각자 `Read_DAO_End_Flag()`로 파일을 연다. 배리어는 읽기 직전에 한 번 있을 뿐이라, 사용자가 배리어 통과와 각 rank의 `open()` 사이에 플래그 파일을 만들면 rank마다 판정이 갈린다. 참을 받은 rank는 `END_FLAG_CHECK_INTERVAL` 뒤 루프를 빠져나가 마지막 배리어로 가고, 거짓을 받은 rank는 다음 후보의 bcast로 들어가 집단 통신 횟수가 어긋난다 | [DAO_Main.py:10055](5_DAO/SRC/DAO_Main.py#L10055)~[10068](5_DAO/SRC/DAO_Main.py#L10068), 대조군 [8071](5_DAO/SRC/DAO_Main.py#L8071)~[8077](5_DAO/SRC/DAO_Main.py#L8077) | `RUN_DAO_MODE = GEN_SINGLE_ROW`로 여러 rank 실행 중 `8_End_flag/dao_end_flag.txt`를 만드는 순간이 배리어 직후와 겹칠 때 | `Run_Single_Row_Generation`의 플래그 블록을 본 루프와 같은 모양으로 다시 쓴다. `is_dao_end = self.Read_DAO_End_Flag() if self.is_root else False` 뒤 `self._safe_bcast(...)`로 전파하고, 그 값으로 `_gen_single_row_stop_idx`를 정한다. 배리어는 bcast가 대신하므로 [10056](5_DAO/SRC/DAO_Main.py#L10056)의 `MPI_Barrier`는 빼도 된다 |
| L3-6 | HIGH | GEN_SINGLE_ROW의 `candidates` 리스트가 끝없이 자란다. 후보마다 `LLR_MATRIX` 객체 전체를 담고 한 번도 비우지 않는데 기본 `NUM_GEN_TRIALS`가 1,000,000이다. 게다가 `RANKING_UPDATE_INTERVAL`(기본 100)마다 그 전체 목록을 채널 수 x (1 + CSW 문턱 수)번 다시 정렬하므로 후반부 갱신 한 번이 갈수록 오래 걸린다. root가 메모리 고갈로 죽으면 `MPI_Abort` 없이 통신이 멎어 전체가 매달린다 | [DAO_Main.py:10044](5_DAO/SRC/DAO_Main.py#L10044), [10139](5_DAO/SRC/DAO_Main.py#L10139), [10160](5_DAO/SRC/DAO_Main.py#L10160)~[10164](5_DAO/SRC/DAO_Main.py#L10164), `Rank_And_Save_Single_Row_Candidates` [10271](5_DAO/SRC/DAO_Main.py#L10271) / 기본값 [DAO_Config.py:397](5_DAO/SRC/DAO_Config.py#L397), [401](5_DAO/SRC/DAO_Config.py#L401) | 기본 설정 그대로 GEN_SINGLE_ROW를 오래 돌리면 후보 수에 비례해 root 메모리가 는다 | `Rank_And_Save_Single_Row_Candidates`가 끝난 뒤 `candidates`를 그 안에서 모은 `workspace_candidates` 합집합(채널별 Top-K의 합)으로 갈아 끼워 길이를 `채널 수 x (1 + 문턱 수) x TOP_K` 이하로 묶는다. 함수가 잘라낸 목록을 반환하고 [10164](5_DAO/SRC/DAO_Main.py#L10164)와 [10185](5_DAO/SRC/DAO_Main.py#L10185)에서 `candidates = self.Rank_And_Save_Single_Row_Candidates(candidates)`로 받으면 된다 |
| L3-7 | MEDIUM | `MUTATE_CONFIG.CSW_UPDATE_LIMIT_VALUE`가 `if ENABLE_CSW_UPDATE_LIMIT:` 안에서만 정의된다. 기본값이 거짓이므로 속성 자체가 없다. 나중에 코드나 `Set_Configs_Manually`에서 `ENABLE_CSW_UPDATE_LIMIT`만 참으로 바꾸면 `Set_CSW_Update_Limit`에서 AttributeError가 난다. 이 함수는 root의 `Gen_LLR_Mutate_Matrix` 경로에서 불리므로 root만 죽고 다른 rank는 bcast를 기다리다 타임아웃에 걸린다. (실마리 ㉶의 "`Set_CSW_Update_Limit` 미호출"은 사실과 다르다. [DAO_Main.py:3785](5_DAO/SRC/DAO_Main.py#L3785) → [7098](5_DAO/SRC/DAO_Main.py#L7098) → [8285](5_DAO/SRC/DAO_Main.py#L8285)로 불린다) | [DAO_Config.py:250](5_DAO/SRC/DAO_Config.py#L250)~[252](5_DAO/SRC/DAO_Config.py#L252), 읽는 자리 [DAO_Main.py:8288](5_DAO/SRC/DAO_Main.py#L8288) | `MUTATE_CONFIG.ENABLE_CSW_UPDATE_LIMIT = True`로 두고 `Gen_LLR_Mode_SEQUENCE`에 10(MUTATE_MATRIX)이 든 채 최적화 실행 | [DAO_Config.py:251](5_DAO/SRC/DAO_Config.py#L251)~[252](5_DAO/SRC/DAO_Config.py#L252)의 `if`를 없애고 `CSW_UPDATE_LIMIT_VALUE = 128`을 늘 정의한다. `ENABLE_CSW_UPDATE_LIMIT`가 이 값을 쓸지 말지를 정하는 역할은 `Set_CSW_Update_Limit`가 이미 맡고 있다 |
| L3-8 | MEDIUM | `CONFIGS` 목록에 `SPEED_TEST_REFC_CONFIG`, `ADJUST_ITERATION_CONFIG`, `PATH_CONFIG`가 빠져 있다. 이 목록을 읽는 자리는 `Print_Initial_Setup` → `Print_Configs(CONFIGS)` 하나뿐이므로 검증에는 영향이 없고, 대신 세션 로그의 Simulation Context에 코어 제외 설정(활성 여부, 배제 비율, 재검사 주기), iteration 전달 비율, 실제로 쓰인 ECC 버전과 경로가 남지 않는다. 지난 실험 로그만 보고 조건을 되살릴 수 없다 | [DAO_Config.py:406](5_DAO/SRC/DAO_Config.py#L406)~[426](5_DAO/SRC/DAO_Config.py#L426), 소비처 [DAO_Main.py:7208](5_DAO/SRC/DAO_Main.py#L7208) | 아무 실행에서나 Simulation Context 절을 보면 세 클래스가 없다 | 세 클래스를 `CONFIGS`에 더한다. 다만 `Print_Configs`가 `vars(cls)`를 쓰므로 `SPEED_TEST_REFC_CONFIG`는 자기 `__dict__`에 있는 13개만 찍힌다. 상속 필드까지 보이려면 [DAO_Main.py:7274](5_DAO/SRC/DAO_Main.py#L7274)의 `vars(cls)`를 `{k: getattr(cls, k) for k in dir(cls) if not k.startswith('__')}`로 바꾼다 |
| L3-9 | MEDIUM | `INITIAL_MATRIX_IDX_LIST`를 막는 검사가 `RUN_OPTIMIZATION`만 본다. 오류 문구는 "TEST_FER/SAVE_UNCOR/REDECODE 전용"이라고 말하면서 GEN_SINGLE_ROW를 통과시킨다. GEN_SINGLE_ROW는 `Get_Initial_Matrix_Idx_List()[0]`만 쓰므로 나머지 인덱스가 조용히 무시된다 | [DAO_Main.py:9681](5_DAO/SRC/DAO_Main.py#L9681)~[9682](5_DAO/SRC/DAO_Main.py#L9682), 소비처 [8710](5_DAO/SRC/DAO_Main.py#L8710) | `RUN_DAO_MODE = GEN_SINGLE_ROW`에 `INITIAL_MATRIX_IDX_LIST = [100, 101]` | [DAO_Main.py:9681](5_DAO/SRC/DAO_Main.py#L9681)의 조건을 `in (RunDAOMode.RUN_OPTIMIZATION, RunDAOMode.GEN_SINGLE_ROW)`로 넓힌다 |
| L3-10 | MEDIUM | `INITIAL_TARGET_GROUP_IDX` 음수가 `ENABLE_FIX_IDX`가 거짓일 때 검증을 통과한다. `range(-1, n)`이 -1을 타겟 목록 맨 앞에 넣고 `groups[-1]`이 마지막 그룹을 가리키므로, 마지막 그룹이 한 stage 안에서 두 번 타겟이 되고 로그의 그룹 번호도 -1로 찍힌다 | [DAO_Main.py:9846](5_DAO/SRC/DAO_Main.py#L9846)~[9851](5_DAO/SRC/DAO_Main.py#L9851) (상한만 봄), 쓰이는 자리 [2329](5_DAO/SRC/DAO_Main.py#L2329)과 [2271](5_DAO/SRC/DAO_Main.py#L2271) | `INITIAL_TARGET_GROUP_IDX = -1`, `REGEN_DV_CONFIG.ENABLE_FIX_IDX = False`로 최적화 실행 | `Validate_Config`에서 모드와 무관하게 `INITIAL_TARGET_GROUP_IDX < 0`을 오류로 올린다. 지금 `ENABLE_FIX_IDX` 블록 안([9698](5_DAO/SRC/DAO_Main.py#L9698), [9753](5_DAO/SRC/DAO_Main.py#L9753))에 있는 음수 검사를 블록 밖으로 끌어내 한 번만 두면 된다 |
| L3-11 | MEDIUM | stage 시간 제한을 켤지 말지를 정하는 같은 이름의 판정이 두 곳에서 다른 기준을 쓴다. `__init__`은 `SIM_MAX_TIME_OUT`(10시간), `Initialize_Stage`는 `100*60*60`(100시간)이다. 설정 주석은 100시간이라고 적혀 있으므로 `__init__` 쪽이 주석과 어긋난다. `MAX_STAGE_TIMEOUT_SECONDS`를 10시간과 100시간 사이로 두면 첫 stage 전에는 제한이 꺼진 것으로, 그 뒤에는 켜진 것으로 판정된다 | [DAO_Main.py:523](5_DAO/SRC/DAO_Main.py#L523)과 [2307](5_DAO/SRC/DAO_Main.py#L2307), 주석 [DAO_Config.py:320](5_DAO/SRC/DAO_Config.py#L320) | `TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS = 20*60*60` | 두 자리를 한 기준으로 모은다. 상수 `SIM_MAX_TIME_OUT`은 ECC subprocess 타임아웃([7939](5_DAO/SRC/DAO_Main.py#L7939))에 이미 쓰이므로 뜻이 다르다. `DAO_Constants.py`에 `STAGE_TIME_LIMIT_DISABLE_THRESHOLD_SECONDS = 100*60*60`을 새로 두고 [523](5_DAO/SRC/DAO_Main.py#L523)과 [2307](5_DAO/SRC/DAO_Main.py#L2307) 모두 그것을 보게 한다 |
| L3-12 | MEDIUM | `SINGLE_ROW_CONFIG`의 `TOP_K`, `RANKING_UPDATE_INTERVAL`, `END_FLAG_CHECK_INTERVAL`, `CSW_THRESHOLDS`가 검증을 받지 않는다. `TOP_K=0`이면 매 갱신이 기존 파일을 다 지우고 아무것도 저장하지 않아 긴 실행이 빈손으로 끝난다. 음수면 상위 후보만 빠지고 나머지가 저장된다. `END_FLAG_CHECK_INTERVAL <= 0`이면 검사 블록이 통째로 건너뛰어져 정상 종료를 시킬 수 없다 | [DAO_Config.py:395](5_DAO/SRC/DAO_Config.py#L395)~[404](5_DAO/SRC/DAO_Config.py#L404), 검증 [DAO_Main.py:9854](5_DAO/SRC/DAO_Main.py#L9854)~[9861](5_DAO/SRC/DAO_Main.py#L9861), 쓰이는 자리 [10273](5_DAO/SRC/DAO_Main.py#L10273), [10055](5_DAO/SRC/DAO_Main.py#L10055) | `SINGLE_ROW_CONFIG.TOP_K = 0` 또는 `END_FLAG_CHECK_INTERVAL = 0`으로 GEN_SINGLE_ROW 실행 | `Validate_Config`의 GEN_SINGLE_ROW 블록([9854](5_DAO/SRC/DAO_Main.py#L9854))에 `TOP_K > 0`, `RANKING_UPDATE_INTERVAL > 0`, `END_FLAG_CHECK_INTERVAL > 0`, `CSW_THRESHOLDS`가 비지 않고 원소가 `MIN_CSW`~`MAX_CSW` 범위인지를 더한다 |
| L3-13 | MEDIUM | `Gen_LLR_Mode_SEQUENCE`의 값이 검증되지 않는다. 오타 하나(예: 61)가 초기 테스트를 다 마친 뒤 첫 stage에서야 ValueError로 드러난다. 초기 테스트는 채널당 uncor 전량을 도는 작업이라 수 시간이 날아간다 | [DAO_Config.py:133](5_DAO/SRC/DAO_Config.py#L133), 터지는 자리 [DAO_Main.py:8309](5_DAO/SRC/DAO_Main.py#L8309) | `Gen_LLR_Mode_SEQUENCE`에 유효하지 않은 숫자를 하나 넣고 최적화 실행 | `Validate_Config`에 `valid = {m.value for m in GenLLRMode}`를 만들어 두 시퀀스의 원소를 검사하는 블록을 더한다. L3-2의 처방 ㉰과 같은 자리다 |
| L3-14 | MEDIUM | `REFC_CONFIG.init_n`이 1, 2, 3이 아니면 `MODE_MAP[init_n]` KeyError가 `Update_Path_Configs`에서 터진다. 이 함수는 `LLR_OPT`가 생기기 전 `__main__`에서 도는 `Update_Configs` 안이라 `MPI_Abort`의 진단 로그 경로를 타지 못하고 `comm.Abort(1)`로 끝난다 | [DAO_Main.py:459](5_DAO/SRC/DAO_Main.py#L459), [460](5_DAO/SRC/DAO_Main.py#L460), [467](5_DAO/SRC/DAO_Main.py#L467), 예외 처리 [10421](5_DAO/SRC/DAO_Main.py#L10421)~[10426](5_DAO/SRC/DAO_Main.py#L10426) | `REFC_CONFIG.init_n = 4` | `Update_RefC_Configs` 첫머리([DAO_Main.py:419](5_DAO/SRC/DAO_Main.py#L419))에 `if REFC_CONFIG.init_n not in MODE_MAP: raise ValueError(...)`를 두어 ch_type 검사([437](5_DAO/SRC/DAO_Main.py#L437))와 같은 방식으로 뜻이 통하는 메시지를 남긴다 |
| L3-15 | MEDIUM | GEN_SINGLE_ROW와 `IS_HBF_OPT=True`를 함께 쓰는 것을 막지 않았다. `CANDIDATE_ITERATION`(기본 50)이 `HBF_MAX_ITERATION`(기본 4)을 넘어 `Is_LLR_Valid`가 모든 후보를 무효로 돌려보내고, 루프가 `NUM_GEN_TRIALS`만큼 "generation failed, skipping"만 찍으며 헛돈다 | 검사 [DAO_Main.py:9814](5_DAO/SRC/DAO_Main.py#L9814)~[9827](5_DAO/SRC/DAO_Main.py#L9827), 무효 판정 [DAO_LLR_MATRIX.py:443](5_DAO/SRC/DAO_LLR_MATRIX.py#L443), 값 [DAO_Config.py:372](5_DAO/SRC/DAO_Config.py#L372)과 [400](5_DAO/SRC/DAO_Config.py#L400) | `IS_HBF_OPT=True`, `init_n=1`, `RUN_DAO_MODE=GEN_SINGLE_ROW` | GEN_SINGLE_ROW 검사 블록([9814](5_DAO/SRC/DAO_Main.py#L9814))에 `IS_HBF_OPT`일 때 `CANDIDATE_ITERATION <= HBF_OPT_CONFIG.HBF_MAX_ITERATION`을 요구하는 오류를 더한다 |
| L3-16 | LOW | `_Read_Stop_Idx`를 부르는 자리가 없다. `_Write_Stop_Idx`가 남긴 `gen_single_row_stop_idx.txt`를 아무도 읽지 않아, 멈출 지점을 파일로 알려 주려던 구조가 반쪽만 남았다 | [DAO_Main.py:1136](5_DAO/SRC/DAO_Main.py#L1136), 쓰는 자리 [1125](5_DAO/SRC/DAO_Main.py#L1125) | 소스 grep | 재시작 시 이어붙이는 쓰임이 없다면 `_Read_Stop_Idx`와 `_Write_Stop_Idx`, 상수 `GEN_SINGLE_ROW_STOP_IDX_FILE_NAME`([DAO_Constants.py:104](5_DAO/SRC/DAO_Constants.py#L104))을 함께 지운다. 진행 상황을 밖에서 보려던 목적이었다면 파일 이름을 `gen_single_row_progress.txt`처럼 목적이 읽히게 고치고 로그로만 남긴다 |
| L3-17 | LOW | `Build_Single_Row_Matrix`의 `floor_flag` 방어용 기본값 `0`이 `Is_LLR_Valid`의 규칙(`floor_flag`는 -1)과 어긋난다. 초기 매트릭스에 그룹이 없는 경우에만 쓰이므로 실제로는 닿지 않지만, 닿으면 모든 후보가 무효가 된다 | [DAO_Main.py:10203](5_DAO/SRC/DAO_Main.py#L10203), 규칙 [DAO_LLR_MATRIX.py:344](5_DAO/SRC/DAO_LLR_MATRIX.py#L344) | 초기 매트릭스의 `groups`가 빈 경우 | 기본값을 `-1`로 바꾼다 |
| L3-18 | LOW | GEN_SINGLE_ROW의 주기 속도 테스트 로그가 `Get_Mode_Sequence_Str()`로 최적화 모드 시퀀스를 찍는다. 이 모드는 `Set_Gen_Trial_LLR_Mode`를 부르지 않아 `current_gen_trial_LLR_mode_index`가 -1로 남고, 관계없는 `Gen_LLR_Mode_SEQUENCE`가 "(0/12) [...]" 꼴로 나온다 | [DAO_Main.py:10176](5_DAO/SRC/DAO_Main.py#L10176), 함수 [7182](5_DAO/SRC/DAO_Main.py#L7182) | GEN_SINGLE_ROW를 `SPEED_TEST_RECHECK_INTERVAL_SECONDS` 넘게 실행 | [10176](5_DAO/SRC/DAO_Main.py#L10176)의 `{self.Get_Mode_Sequence_Str()}`를 후보 진행 표시(`[{candidate_idx + 1}/{num_candidates}]`가 이미 같은 줄에 있음)로 두고 빼낸다 |
| L3-19 | LOW | 읽는 자리가 없는 설정 필드가 있다. `REFC_CONFIG.LLR_matrix_idx`([186](5_DAO/SRC/DAO_Config.py#L186))는 인자를 매개변수로 받으므로 쓰이지 않고, `REFC_CONFIG.mode_init_seed`([181](5_DAO/SRC/DAO_Config.py#L181))와 `SPEED_TEST_REFC_CONFIG.mode_init_seed`([237](5_DAO/SRC/DAO_Config.py#L237))도 그렇다. `CRC_skip_mode`와 `HighDV_skip_mode`는 `ECC_VER == "2.4"` 분기에서만 쓰이는데 기본값이 "3.0"이다 | [DAO_Config.py:181](5_DAO/SRC/DAO_Config.py#L181), [186](5_DAO/SRC/DAO_Config.py#L186), [187](5_DAO/SRC/DAO_Config.py#L187), [188](5_DAO/SRC/DAO_Config.py#L188), [237](5_DAO/SRC/DAO_Config.py#L237) | 소스 grep | `mode_init_seed`는 L3-4의 처방으로 살아나므로 남긴다. `LLR_matrix_idx`는 지운다. `CRC_skip_mode`와 `HighDV_skip_mode`는 2.4 전용임을 한 줄 주석으로 밝힌다 |
| L3-20 | LOW | `Update_RefC_Configs`가 `SPEED_TEST_REFC_CONFIG.str_matrix_name`에 값을 대입해 상속 고리를 끊는다. 이 대입이 없어도 자식이 부모 값을 그대로 읽으므로 하는 일이 없고, 대입 뒤에는 부모를 바꿔도 자식이 따라오지 않는다 | [DAO_Main.py:448](5_DAO/SRC/DAO_Main.py#L448) | 소스 읽기 | [DAO_Main.py:448](5_DAO/SRC/DAO_Main.py#L448)을 지운다 |
| L3-21 | LOW | `TEST_MODE_DIR_NAME`을 읽는 자리가 없다 (팀 T와 겹치므로 확인만) | [DAO_Constants.py:76](5_DAO/SRC/DAO_Constants.py#L76) | 소스 grep | 팀 T 판단에 맡긴다 |

---

## 5절. 설정 항목을 하나 더할 때 손대야 하는 자리

새 설정 클래스나 필드를 넣을 때 빠뜨리기 쉬운 자리를 순서대로 적는다.
L3-8이 보여 주듯 지금 `CONFIGS`에 세 클래스가 빠져 있는 것은 이 목록이 글로 남아 있지 않아서다.

### 5-1. 설정 클래스를 새로 만들 때

- 1. `DAO_Config.py`에 클래스를 정의한다. **클래스 본문에서 다른 설정을 읽어 값을 계산하지 않는다.**
  다른 설정에 기대는 값은 기본값만 적고 `Update_*` 함수에서 채운다 (1절 표의 오른쪽 열이 그 이유다).
- 2. `DAO_Config.py`의 `CONFIGS`([406](5_DAO/SRC/DAO_Config.py#L406))에 클래스를 더한다. 이 목록이
  `Print_Initial_Setup` → `Print_Configs`([DAO_Main.py:7270](5_DAO/SRC/DAO_Main.py#L7270))로 세션 로그에 실린다.
- 3. 모드별 설정이면 `Print_Stage_Info`([DAO_Main.py:7220](5_DAO/SRC/DAO_Main.py#L7220))의 모드 분기에
  `self.Print_Config(새_클래스)` 줄을 더한다.
- 4. `MAX_TRIAL` 필드를 두면 `Validate_Config`의 모드별 MAX_TRIAL 검증 목록
  ([DAO_Main.py:9835](5_DAO/SRC/DAO_Main.py#L9835)~[9844](5_DAO/SRC/DAO_Main.py#L9844))과
  `Set_Gen_Trial_LLR_Mode`의 `MODE_MAX_TRIAL_MAP`([8429](5_DAO/SRC/DAO_Main.py#L8429)~[8439](5_DAO/SRC/DAO_Main.py#L8439))
  양쪽에 항목을 더한다. 두 목록은 지금 서로 맞지만, 한쪽만 고치면 조용히 어긋난다.
- 5. `Validate_Config`([DAO_Main.py:9647](5_DAO/SRC/DAO_Main.py#L9647))에 값 범위 검사를 더한다.
  실행 뒤에야 드러나는 값(열거형 소속, 길이, 하한)일수록 여기에 둔다.

### 5-2. 기존 클래스에 필드를 더할 때

- 1. 다른 설정에서 값을 끌어오는 필드라면 `Update_Configs`([DAO_Main.py:475](5_DAO/SRC/DAO_Main.py#L475))의
  네 함수 가운데 맞는 곳에 계산을 넣고, **호출 순서가 의존 방향과 맞는지 본다** (L3-3이 어긋난 사례다).
  현재 순서는 `Update_RefC_Configs` → `Update_Insert_Group_Configs` → `Update_Path_Configs` →
  `Update_Exit_After_Run_Configs`이며, 뒤 함수가 정한 값을 앞 함수가 읽으면 첫 실행에서 낡은 값이 쓰인다.
- 2. `Set_Configs_Manually`([DAO_Config.py:22](5_DAO/SRC/DAO_Config.py#L22))의 SIM_IDX 분기에서 그 필드를 바꿀 수 있게
  할 것인지 정한다. 바꾸게 한다면 그 필드에서 파생되는 값이 모두 `Update_Configs`에서 다시 계산되는지 확인한다.
- 3. 채널별 배열 필드라면 `Update_RefC_Configs`([DAO_Main.py:418](5_DAO/SRC/DAO_Main.py#L418))의 ch_type 세 분기
  전부에서 `NUM_TARGET_CHANNELS` 길이로 맞춰지는지 확인한다 (L3-1이 ch_type 3에서 빠뜨린 사례다).
- 4. Ref_C 실행 인자로 넘어가는 값이라면 `Get_Ref_C_Args`([DAO_Main.py:6407](5_DAO/SRC/DAO_Main.py#L6407))와
  `Get_Ref_C_Args_For_Speed_Test`([6456](5_DAO/SRC/DAO_Main.py#L6456)) **두 함수의 ECC_VER 두 분기, 모두 네 자리**에
  같은 위치로 넣는다. 지금도 이 네 자리가 서로 어긋난 곳이 있다 (L3-4).
- 5. 조건부 정의(`if 플래그: 필드 = 값`)를 쓰지 않는다. 플래그가 거짓일 때 속성 자체가 사라져
  나중에 플래그만 켜면 AttributeError가 난다 (L3-7). 값은 늘 정의하고 플래그는 쓸지 말지만 정한다.

### 5-3. 새 실행 모드(`RunDAOMode`)를 더할 때

- 1. `DAO_Constants.py`의 `RunDAOMode`([63](5_DAO/SRC/DAO_Constants.py#L63))에 멤버를 더한다.
- 2. `Update_Exit_After_Run_Configs`([DAO_Main.py:403](5_DAO/SRC/DAO_Main.py#L403))에서 그 모드의
  `LOAD_UNCOR_MODE`를 정한다. 빠뜨리면 `DAOLoadUncorMode.DEFAULT`(-1)가 남는다.
- 3. `LLR_OPT.Main`([DAO_Main.py:10001](5_DAO/SRC/DAO_Main.py#L10001))의 분기에 실행 경로를 잇는다.
- 4. `Validate_Config`에 그 모드와 어울리지 않는 설정 조합을 막는 검사를 더한다.
  기존 모드에 걸린 제약(`INITIAL_MATRIX_IDX_LIST`, Two-stage, LOAD_VECTOR, IS_HBF_OPT)이 새 모드에도
  해당하는지 하나씩 본다. L3-9와 L3-15는 GEN_SINGLE_ROW를 더할 때 이 단계를 건너뛴 결과다.
- 5. 그 모드가 독립 루프를 갖는다면 종료 플래그 읽기를 **root만 읽고 `_safe_bcast`로 전파**하는
  본 루프의 관용구([DAO_Main.py:8071](5_DAO/SRC/DAO_Main.py#L8071)~[8077](5_DAO/SRC/DAO_Main.py#L8077))로 적는다.
  배리어만으로는 rank 사이 판정이 갈리는 것을 막지 못한다 (L3-5).
