# Round 2 팀 R (가독성) 종합: R1~R11

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 워커 3개 병렬 (모델 Opus). 원본은 [worker_R_1.md](worker_R_1.md) (구조, 850줄), [worker_R_2.md](worker_R_2.md) (이름과 설정과 상태와 함수, 363줄), [worker_R_3.md](worker_R_3.md) (문구와 문서, 380줄)

## 워커 분담과 조사 방법

| 워커 | 관점 | 조사 방법 |
|------|------|----------|
| 1 | R1 책임 경계와 파일 분할, R2 모드 정보 분산, R7 전역 반입과 모듈 의존, R8 데이터 모델 확장 | `ast` 파싱으로 `LLR_OPT` 메서드 212개의 줄 범위, 메서드별 `self` 속성 읽기와 쓰기, 호출 관계를 전수로 뽑아 책임군 16개를 배정하고 군 사이 공유 속성을 기계로 셈 |
| 2 | R3 이름 규약, R4 설정 계층, R5 인스턴스 상태 생성 위치, R6 함수 길이와 반복 관용구 | 이름 전수 집계, `__init__` 밖 속성 21개 추적, 설정 4단계 추적, 함수 길이와 중첩 깊이 측정 |
| 3 | R9 docstring과 주석과 로그와 매직 넘버, R10 문서 이름 정합, R11 Util 사용법 | `ast`로 함수 229개의 Args, Returns, Raises 절을 시그니처와 기계 대조. 문서 식별자 토큰을 전부 뽑아 코드 낱말 집합과 전수 대조. 링크 33개 경로 존재 확인 |

개선안 **60개** (워커 1이 15개, 워커 2가 20개, 워커 3이 25개). 우선순위 상이 **26개**다.

---

## ㉮ 워커 결과 요약 (개선안 목록, 우선순위별)

### 우선순위 상

| # | 우선순위 | 개선안 | 위치 | 처방 | 위험 | 지적 워커 |
|---|---------|--------|------|------|------|----------|
| 1 | 상 | `Is_LLR_Valid`의 floor_flag 규칙을 이름 붙인 함수로 뽑는다 | [DAO_LLR_MATRIX.py:344](5_DAO/SRC/DAO_LLR_MATRIX.py#L344) | `_Check_Row_Tail_Fields(row, group_idx, row_idx) -> Optional[str]`로 뽑고 `FLOOR_FLAG_UNUSED = -1` 상수를 만든다. `floor_flag`를 이웃에서 베끼는 11곳을 `LLR_Row`의 기본값으로 바꾼다 | 동작 변경 없음. **현재 규칙이 옆 세션 SW 분기와 정면 충돌**한다 (마지막 칸이 분기 index가 되면 분기 매트릭스가 전부 무효 판정). 옆 세션 작업 전에 넣어야 이득 | 1 (R8-4) |
| 2 | 상 | row 꼬리 칸을 이름으로 읽는다 | [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py) 파서와 출력 | `ROW_TAIL_FIELD_NAMES = ("CSW", "iter_start", "iter_end", "floor_flag")`를 두고 파서와 출력이 같은 목록을 돈다. 음수 인덱스 5줄(`row[:-4]`~`row[-1]`)이 사라진다 | 동작 변경 없음. 먼저 넣으면 SW 분기 쪽이 목록에 이름 하나를 더하는 것으로 읽기와 쓰기가 동시에 맞는다 | 1 (R8-1) |
| 3 | 상 | 출력 줄의 차이 표시 3갈래 18줄을 도우미 하나로 묶는다 | [DAO_LLR_MATRIX.py:176-193](5_DAO/SRC/DAO_LLR_MATRIX.py#L176) | `_format_row_field(value, opt_value, has_compare_target, width=4)`. 호출부가 `ROW_TAIL_FIELD_NAMES`를 돈다 | 동작 변경 없음 (세 갈래 결과가 한 식과 같음을 확인). 출력 파일 대조 시험 1회 권고 | 1 (R8-2) |
| 4 | 상 | 그룹 구조 변경을 헤더 도우미 세 개로 모은다 | DAO_Main 8자리 ([2711](5_DAO/SRC/DAO_Main.py#L2711), [3069](5_DAO/SRC/DAO_Main.py#L3069), [3433](5_DAO/SRC/DAO_Main.py#L3433), [3575](5_DAO/SRC/DAO_Main.py#L3575), [5108](5_DAO/SRC/DAO_Main.py#L5108), [5618](5_DAO/SRC/DAO_Main.py#L5618), [5912](5_DAO/SRC/DAO_Main.py#L5912), [6323](5_DAO/SRC/DAO_Main.py#L6323)) | `LLR_MATRIX`에 `Insert_Group_Into_Header`, `Delete_Group_From_Header`, `Rebuild_Header_Group_Arrays` 세 메서드. 그룹당 배열이 하나 늘 때 고칠 자리가 8곳에서 3곳으로 | **동작 변경 가능**. 여덟 자리가 `type_each_group`에 넣는 값이 서로 다르다 (상수 1, 원본 복사, 목록 재조립, 별도 계산). 옮기기 전에 여덟 자리를 표로 대조해야 한다. 옆 세션과 순서 협의 필요 | 1 (R8-3) |
| 5 | 상 | 인프라 10개 군을 메서드 묶음 클래스로 떼어낸다 | `LLR_OPT` 전체 | LOG, FLAG, CSWLOG, MPI, PATH, ECC+SPEED, RESULT, UNCOR, PRINT, SINGLEROW를 새 파일 10개로. 3,762줄이 옮겨가 `DAO_Main.py`가 6,600줄대가 된다 | 동작 변경 없음 (메서드 이름 212개가 전부 고유해 상속 순서 무관, `self` 그대로). 옆 세션 충돌 없음 | 1 (R1-1 1~10) |
| 6 | 상 | 모드 정보를 `GEN_LLR_MODE_SPECS` 표 하나로 모은다 | [DAO_Constants.py:148-196](5_DAO/SRC/DAO_Constants.py#L148) 외 | 모드 추가 시 손대는 **15곳을 5곳**으로 줄인다. spec 7.1 체크리스트는 6곳만 적고 있다 | 동작 변경 없음. L팀의 `INSERT_RESTART_GROUP` 목록 판정이 선행 | 1 (R2-1) |
| 7 | 상 | MPI 초기화를 상수 모듈에서 꺼낸다 | [DAO_Constants.py:135-137](5_DAO/SRC/DAO_Constants.py#L135) | 상수 모듈 import만으로 MPI가 뜨는 지금 구조를 `DAO_MPI_Communication.py`로 옮긴다 | 동작 변경 가능 (초기화 시점 이동). 5번의 4단계 뒤에 한다 | 1 (R7-1) |
| 8 | 상 | `Update_Configs` 호출 순서를 고친다 | [DAO_Main.py:442](5_DAO/SRC/DAO_Main.py#L442) 대 [405](5_DAO/SRC/DAO_Main.py#L405) | `Update_RefC_Configs`가 아직 정해지지 않은 `UNCOR_CONFIG.LOAD_UNCOR_MODE`를 먼저 읽어 `NUM_LINES_PER_UNCOR`가 1로 남는다 | **동작 변경 (결함 수리)**. L팀 심각도 판정 필요 | 2 (R4-4) |
| 9 | 상 | `HBF_OPT_CONFIG` 생성자 부수효과를 `Update_RefC_Configs`로 옮긴다 | [DAO_Config.py:366-375](5_DAO/SRC/DAO_Config.py#L366) | 인스턴스를 만드는 자리가 저장소에 없어 `DAO_CONFIG.IS_HBF_OPT`가 항상 False다. HBF 경로 전체가 죽어 있다 | **동작 변경 (Decision 등급)**. 살리면 검증 경로가 깨어난다. L팀 판정 필요 | 2 (R4-3) |
| 10 | 상 | `LLR_MATRIX.Get_Channel_Result` 접근자로 Partial/Full 쌍둥이 40줄을 없앤다 | [DAO_Main.py:7700-7741](5_DAO/SRC/DAO_Main.py#L7700) | `ChannelResult` dataclass와 `Get_Channel_Result(ch_idx, is_partial)`. `Print_Test_Summary`의 10단 중첩(파일 최대)이 8단으로, `_partial` 필드 접근 52곳 중 30곳이 사라진다 | 동작 변경 없음. `DAO_LLR_MATRIX.py`를 건드려 옆 세션과 같은 파일 (범위는 FER 필드라 작음) | 2 (R6-2) |
| 11 | 상 | 300줄 넘는 함수 2개를 구획대로 쪼갠다 | [Gen_LLR_Insert_Mutated_Group:2792](5_DAO/SRC/DAO_Main.py#L2792) 344줄, [Build_Reordered_Matrix:4849](5_DAO/SRC/DAO_Main.py#L4849) 312줄 | 내부 구획 주석이 그대로 경계가 된다. `Borrow_Iterations_From_Donor_Groups`, `Insert_Group_And_Fix_Header`, `Shift_Target_Group_Numbers_After_Insert`, `Arrange_Groups_For_Reorder`, `Assign_Iterations_For_Position_Test`, `Assign_Iterations_For_Final_Verification` 6개 | 동작 변경 없음. 4번과 경계가 겹친다 (아래 교차 분석 ㉠) | 2 (R6-1) |
| 12 | 상 | `current_target_idx`를 로그 전용임이 드러나는 이름으로 바꾼다 | 19곳 | 같은 목록 위에서 회전 규칙이 다른 포인터 2개가 동시에 돈다. 이 속성은 실제 타겟 선택에 쓰이지 않고 로그 한 줄만 만든다 | 동작 변경 없음 | 2 (R3-2) |
| 13 | 상 | `LLR_OPT` 클래스 docstring에 속성 수명 4층 표를 적는다 | [DAO_Main.py:481](5_DAO/SRC/DAO_Main.py#L481) | `__init__` 밖에서 생기는 속성 21개가 어느 층에서 생기는지 못 박는다 | 동작 변경 없음 | 2 (R5-5) |
| 14 | 상 | `Mutate_Matrix_Setup` 껍데기를 없앤다 | [DAO_Main.py:7097](5_DAO/SRC/DAO_Main.py#L7097) | 본문 한 줄로 `Set_CSW_Update_Limit()`만 부른다. [3785](5_DAO/SRC/DAO_Main.py#L3785)가 직접 부르게 한다. Round 1 실마리 ㉶의 원인이 이 껍데기다 | 동작 변경 없음. 5번 분할의 군 사이 역방향 호출 2곳 중 하나가 사라진다 | 2 (R3-4) |
| 15 | 상 | `Raises:` 절 17곳을 `종료:` 절로 다시 쓴다 | SRC 전체 | **17곳 전수가 거짓이다.** 16곳은 파이썬 예외를 던진다고 적었으나 실제는 `MPI_Abort`(잡을 수 없음), 1곳(`Write_Log_Lines`)은 예외를 삼킨다 | 동작 변경 없음 | 3 |
| 16 | 상 | `ReorderState` docstring의 허깨비 필드 3줄을 지운다 | `ReorderState` | `total_rounds`, `round_best_FER`, `round_best_avg_iter`는 저장소 어디에도 없다 (실마리 ㉸ 확인) | 동작 변경 없음 | 3 |
| 17 | 상 | Args 절 8곳과 `Set_Current_Optimal_Matrix` 설명 1곳을 시그니처에 맞춘다 | `Run_ECC`, `Gather_Ref_C_Results`, `Distribute_Uncors_To_Local_Session`, `Get_Result_File_Name`, `Print_Test_Result`, `Set_Test_Environment`, `Print_LLR_Matrix`, `Gen_LLR_Regen_DV` | `Run_ECC`는 "Args: 없음"인데 `ch_idx`를 받는다 (실마리 ㉹ 확인) | 동작 변경 없음 | 3 |
| 18 | 상 | 줄표 22곳, 가운뎃점 4개, U+FFFD 3개, 이모지 12줄을 고친다 | SRC 17곳 + Util 5곳 | 프로젝트 문장 규칙 위반. [Make_Log_Backup:6624](5_DAO/SRC/DAO_Main.py#L6624) docstring은 "하" 한 글자가 깨져 있다 (실마리 ㉺ 확인) | 동작 변경 없음 (로그 문구만) | 3 |
| 19 | 상 | 과거를 서술하는 주석 12곳을 다시 쓴다 | `기존 로직`, `기존 모드`, `기존 동작 유지`, `(사용되지않음)` | 프로젝트 규칙 "수리는 덧대기가 아니라 다시 쓰기" 위반 | 동작 변경 없음 | 3 |
| 20 | 상 | 문서 링크 33개를 고친다 | README 34개 중 33개 | **전부 없는 경로 `DAO/SRC/...`를 가리킨다.** 붙은 줄 번호도 대부분 어긋난다 (`LLR_OPT` 255 대 481, `Test_Core_Speed` 5313 대 9020). `DAO/SRC/`를 `SRC/`로 바꾸고 함수 단위 링크에서 줄 번호를 뺀다 | 동작 변경 없음. 줄 번호를 빼면 5번 분할 뒤에도 깨지지 않는다 | 3 |
| 21 | 상 | README와 spec의 이름 20건, 값 14건을 코드에 맞춘다 | README 1.2, 2.2, 3.2, 4.1절, spec 3장과 8장 | 실마리 ㉮의 8개를 확인하고 12건을 더 찾았다. 값 어긋남: `MAX_OPTIMIZATION_STAGE` 500 대 9999, `MAX_RUN_ECC_ERRORS` 5 대 9999, `ENABLE_TWO_STAGE_TEST` True 대 False 등 | 동작 변경 없음 | 3 |
| 22 | 상 | 매직 넘버 4종을 상수로 뽑는다 | `100*60*60` [2307](5_DAO/SRC/DAO_Main.py#L2307), `3600` [6692](5_DAO/SRC/DAO_Main.py#L6692), `1e-15` 5곳, `"Partial"` 7곳 | `STAGE_TIME_LIMIT_DISABLED_SECONDS`, `MPI_BARRIER_MIN_TIMEOUT_SECONDS`, `FER_TIE_TOLERANCE`, `PARTIAL_DIR_NAME` | 값이 같아 동작 변경 없음. `"Partial"`은 T팀 실마리 ㉳ 결론 대기 | 3 |
| 23 | 상 | `Util/README.md`를 새로 쓰고 `5_DAO/README.md`에서 링크한다 | `Util/` 8개 | 지금은 `README_Mock_ECC.md` 하나뿐이라 나머지 7개는 파일을 열어야 무엇인지 안다 | 동작 변경 없음 | 3 |
| 24 | 상 | `check_result_files.py`가 경로를 인자로 받게 한다 | [Util/check_result_files.py:14](5_DAO/Util/check_result_files.py#L14) | `dao_dir_path = r""`가 빈 문자열이라 고치지 않으면 언제나 실패한다 (실마리 ㉻ 확인) | 동작 변경 있음 (지금은 언제나 실패) | 3 |
| 25 | 상 | `remote_server_sync.py` docstring에 사용법 절을 더한다 | [Util/remote_server_sync.py](5_DAO/Util/remote_server_sync.py) | `CONFIG` 값은 자리표시(`your-server.com`)라 실제 접속 정보가 박혀 있지는 않다. 문제는 `CONFIG`를 고쳐야 한다는 안내도, CLI 인자가 있다는 안내도 없는 것 | 동작 변경 없음 | 3 |
| 26 | 상 | `merge_uecc.py`에 docstring을 새로 쓰고 이름을 바꾼다 | [Util/merge_uecc.py](5_DAO/Util/merge_uecc.py) | docstring이 아예 없고 출력을 덧쓰기 모드로 열어 두 번 돌리면 겹친다. `merge_text_files_by_prefix`로 이름을 바꾼다 | 동작 변경 없음 (문서만 먼저) | 3 |

### 우선순위 중

| # | 우선순위 | 개선안 | 위치 | 처방 | 위험 | 지적 워커 |
|---|---------|--------|------|------|------|----------|
| 27 | 중 | `MULTIROUND`와 `GEN` 군을 파일로 떼어낸다 | 1,826줄 + 2,394줄 | `DAO_Gen_Multi_Round_Modes.py`, `DAO_Gen_Single_Round_Modes.py`. 끝나면 `DAO_Main.py`가 약 2,200줄 | 동작 변경 없음이되 **옆 세션과 정면 충돌**. SW 분기 작업 완료 후 | 1 (R1-1 11~12) |
| 28 | 중 | 멀티라운드 상태를 협력 객체로 뽑는다 | 상태 dataclass 4개 | 각 상태가 자기 `Init`, `Update_Round_Result`, `Finalize_Round`, `Build_Matrix`를 갖게 하면 문자열 디스패치 3개가 통째로 사라진다 | **동작 변경 가능**. 상태를 객체로 옮기면 MPI bcast 대상이 바뀐다. bcast 전후 값 대조 필요 | 1 (R1-2) |
| 29 | 중 | 문자열 대신 함수 객체로 디스패치한다 | `getattr`/`setattr` 8곳 | `Init_*` 4개와 `Update_*_Round_Result` 3개는 직접 호출 지점이 **0건**이라 편집기 사용처 찾기가 통하지 않는다 | 동작 변경 없음. 6번 뒤 | 1 (R2-2) |
| 30 | 중 | 모드 시퀀스를 열거형 목록으로 선언한다 | `Gen_LLR_Mode_SEQUENCE`, `Gen_LLR_Mode_HBF_SEQUENCE` | L팀이 `[7, 8, 1, 2, 12]`의 올바른 값을 정한 뒤 | 동작 변경 가능 | 1 (R2-3) |
| 31 | 중 | 별표 import 두 줄을 명시 import로 바꾼다 | [DAO_Main.py:1-10](5_DAO/SRC/DAO_Main.py#L1) | 이름 102개가 반입되고 `__all__`이 없다 | 동작 변경 없음. 7번 뒤 | 1 (R7-2) |
| 32 | 중 | 순위 루프 변수 이름을 바꾼다 | [10306](5_DAO/SRC/DAO_Main.py#L10306), [10333](5_DAO/SRC/DAO_Main.py#L10333) | `for rank, c in enumerate(...)`가 전역 MPI `rank`를 가린다. `candidate_rank`로 | 동작 변경 없음 (지역 변수). 독립, 언제든 | 1 (R7-3) |
| 33 | 중 | 데이터 모델이 설정을 인자로 받게 한다 | `DAO_LLR_MATRIX.py` 32곳 | 설정 클래스를 직접 읽는 자리가 32곳인데 생성 지점은 2곳이라 인자 주입이 싸다 | 동작 변경 없음. 옆 세션 완료 후 | 1 (R7-4) |
| 34 | 중 | 로그 요약 도우미가 필드를 자동으로 돌게 한다 | [DAO_Main.py:93-118](5_DAO/SRC/DAO_Main.py#L93) | `header_summary` 11필드와 `row_summary` 6필드 손 나열을 `dataclasses.fields()` 순회로 | 출력 형식만 변경 (결과는 같음을 확인). 독립 | 1 (R8-5) |
| 35 | 중 | copy 후보를 dict 대신 dataclass로 담는다 | `Get_Copy_Row_Candidates`, `Get_Copy_Group_Candidates`, `_Load_External_Single_Row_Candidates` | `Row_Copy_Candidate`, `Group_Copy_Candidate`. row에 칸이 늘어도 `Copy_Group`이 고칠 것이 없어진다 | 동작 변경 가능 (bcast pickle 대상 변경) | 1 (R8-6) |
| 36 | 중 | 멀티라운드 greedy 두 벌을 공용 상태와 함수 2개로 합친다 | `Update_Delete_Row_Round_Result` + `_Finalize_Delete_Row_Round` 대 `Update_Insert_Restart_Group_Round_Result` + `_Finalize_Insert_Restart_Group_Round` | **두 벌이 87% 동일** (81줄 대 77줄, 다른 줄 22줄). 상태 dataclass 2벌은 필드 9개 중 8개가 같다 | 동작 변경 없음. 28번과 이름이 겹친다 (교차 분석 ㉢) | 2 (R6-3) |
| 37 | 중 | `Decide_On_Root` 도우미로 root 판정 후 bcast 관용구를 줄인다 | `_safe_bcast` 46곳 중 **43곳이 같은 모양** (`Run_Optimization` 한 함수에만 7곳) | `Decide_On_Root(decide, tag, default)`. 부작용이 있는 자리는 그대로 두고 값 계산만 하는 자리부터 | 동작 변경 없음 (부작용 자리 제외). M팀의 집단 통신 정합 결론과 맞춰야 한다 | 2 (R6-3) |
| 38 | 중 | `loop_*` 4개를 `__init__`에 선언하고 죽은 속성 5개를 지운다 | `loop_start_time`, `prev_generated_mutation` 외 | `Test_LLR` while 본문이 한 번도 안 돌면 `Print_Test_Result`에서 AttributeError. 죽은 속성: `total_raw_FERs`, `total_seed_FERs`, `total_num_iterations`, `loop_end_time_stamp`, `start_time_str` (대입만 있고 읽는 자리 0) | 동작 변경 없음 | 2 (R5-2, R5-4) |
| 39 | 중 | 클래스 본문 조건 분기 4자리를 `Update_*_Configs`로 옮긴다 | `DAO_Config.py` | 설정 값의 정본 위치가 흩어진다 | 동작 변경 없음 | 2 (R4-2) |
| 40 | 중 | `CONFIGS`에 빠진 3클래스를 넣는다 | `SPEED_TEST_REFC_CONFIG`, `ADJUST_ITERATION_CONFIG`, `PATH_CONFIG` | 22개 클래스 중 19개만 들어 있어 세션 로그에 속도 테스트 설정, iteration 전달 비율, 경로가 남지 않는다 (실마리 ㉷ 확인) | 동작 변경 있음 (로그만 늘어남) | 1, 2 (R4-6) |
| 41 | 중 | `SPEED_TEST_REFC_CONFIG` 상속을 끊는다 | `DAO_Config.py` | 읽는 사람이 두 클래스를 대조해야 값을 안다. `Print_Config`이 `vars(cls)`를 써서 상속 필드를 찍지 않는 점도 같은 뿌리 | 동작 변경 없음 (34곳 확인 필요) | 2 (R4-5) |
| 42 | 중 | `Deep_Copy`를 이름 붙은 세 갈래 메서드로 감싼다 | 호출 33곳 | 조합이 셋뿐이다. `Copy_With_All_Results`, `Copy_With_Full_Results_Only`, `Copy_Structure_Only`. **기본값 뒤집기는 금지** (9곳의 동작이 조용히 뒤집힌다) | 잘못 고치면 동작 변경. `DAO_LLR_MATRIX.py`라 옆 세션 뒤 | 2 (R6-3) |
| 43 | 중 | `Validate_Config`을 검사 함수 4개로 나눈다 | [9647](5_DAO/SRC/DAO_Main.py#L9647) 255줄, 7단 중첩 | REGEN 고정 인덱스 검사 2벌(각 40줄)을 `_Validate_Regen_Fixed_Index` 하나로 | 동작 변경 없음 | 2 (R6-1, R6-3) |
| 44 | 중 | `BACKUP_SRC` 이름을 규약에 맞춘다 | 2곳 | 대소문자 규약 혼재 | 동작 변경 없음 | 2 (R3-1) |
| 45 | 중 | 중첩 깊이 상위 함수 5개를 편다 | `Update_Optimal_LLR` 8단, `_Setup_Uncor_Pool_For_Channel` 8단, `Run_Optimization` 7단, `Gather_CSW_Logs` 7단 | root 전용 블록을 함수로 빼면 `if self.is_root:` 한 겹이 사라진다 | 동작 변경 없음 | 2 (R6-4) |
| 46 | 중 | 채널별 FER 로그 27곳 중 같은 모양 5곳을 묶는다 | [4834](5_DAO/SRC/DAO_Main.py#L4834), [5704](5_DAO/SRC/DAO_Main.py#L5704), [5994](5_DAO/SRC/DAO_Main.py#L5994), [9516](5_DAO/SRC/DAO_Main.py#L9516), [9539](5_DAO/SRC/DAO_Main.py#L9539) | `Write_Channel_FER_Lines(matrix, prefix, is_partial)`. 10번의 `Get_Channel_Result`와 짝 | 동작 변경 없음 | 2 (R6-3) |
| 47 | 중 | `Print_Stage_Info`의 13갈래 elif를 표 조회로 바꾼다 | [7236-7259](5_DAO/SRC/DAO_Main.py#L7236) | 13갈래가 모두 `self.Print_Config(XXX_CONFIG)` 한 줄이다 | 동작 변경 없음. 6번의 표에 흡수 (교차 분석 ㉣) | 2 (R6-3) |
| 48 | 중 | 매직 넘버 8종을 상수로 뽑는다 | `errno==12`, `seq_len*2`, `rank*10000`, `0.5`, `sleep_interval*3`, `"llr_matrix"`, `"collected"`, `"Copied_uncors"` | 값이 같아 동작은 유지된다. `errno`는 `import errno`로 바꾸면 옆 주석이 필요 없어진다 | 동작 변경 없음 | 3 |
| 49 | 중 | 구분선 3갈래와 로그 머리표 4갈래를 하나로 모은다 | 구분선 상수 13곳, ASCII 18곳, 상자 문자 13곳 / `[WARNING]` 11, `[WARN]` 10, `[Warning]` 2, `[Error]` 9 | 상수 하나를 정본으로 정하고 나머지를 그 상수로 바꾼다 | 로그 문구 변경. 외부 파싱 여부 확인 필요 (미커버 ㉱) | 3 |
| 50 | 중 | 코드에 있고 문서에 없는 설정 13묶음을 문서에 더한다 | `RunDAOMode.GEN_SINGLE_ROW`와 `SINGLE_ROW_CONFIG` 전체, `MULTI_ROUND_*` 표 4개, `ENABLE_AVG_ITER_UPDATE`, `INITIAL_MATRIX_IDX_LIST`, `Set_Configs_Manually`의 `SIM_IDX` 표 | README에 절을 더한다 | 동작 변경 없음 | 3 |
| 51 | 중 | 문서 안의 변경 이력 서술 8묶음을 지운다 | `(신규)`, `(1024 → 1408로 변경)`, README 끝 "업데이트" 목록 12줄 | 프로젝트 규칙 "변경 이력은 `_pm/DONE.md`와 git이 담당" 위반 | 동작 변경 없음 | 3 |
| 52 | 중 | `Mock_ECC.py`의 `MAX_CSW`를 정합시킨다 | [Util/Mock_ECC.py:59](5_DAO/Util/Mock_ECC.py#L59) 1024 대 [DAO_Constants.py:140](5_DAO/SRC/DAO_Constants.py#L140) 1408 | 값을 맞추거나, 일부러 다르면 이유를 옆 주석에 적는다 | **값이 다르다.** Mock 출력이 달라지므로 T팀 확인 필요 | 3 |
| 53 | 중 | Util 3개가 대상 폴더를 인자로 받게 한다 | `merge_uecc.py`, `rename_llr_idx.py`, `collect_llr_matrices.py` | 셋 다 "이 파일을 대상 폴더에 옮겨 놓고 실행"이 전제다. `sys.argv[1]`을 받게 하면 저장소 파일을 옮기지 않아도 된다 | 동작 변경 없음 (인자가 없으면 지금처럼) | 3 |
| 54 | 중 | `collect_llr_matrices.py`의 `--move`와 `--dry-run`을 열어 준다 | [Util/collect_llr_matrices.py](5_DAO/Util/collect_llr_matrices.py) | 안전한 예행 기능이 코드에 이미 있는데 `main()`이 둘 다 False로 고정해 사용자가 쓸 수 없다 | 동작 변경 없음 (기본값 유지) | 3 |
| 55 | 중 | `split_file.py`와 `fer_plot.py`에 모듈 docstring을 더한다 | Util 2개 | 사용법이 함수 docstring에만 있거나 `sample_data.txt`를 봐야 안다 | 동작 변경 없음 | 3 |

### 우선순위 하

| # | 우선순위 | 개선안 | 위치 | 처방 | 위험 | 지적 워커 |
|---|---------|--------|------|------|------|----------|
| 56 | 하 | `Print_Configs` 본문을 `Print_Config` 반복으로 줄이고 이름을 `Print_Config_Group`으로 바꾼다 | [7261](5_DAO/SRC/DAO_Main.py#L7261), [7270](5_DAO/SRC/DAO_Main.py#L7270) | 두 벌이 본문 동일하고 이름이 한 글자 차이라 호출자가 눈으로 구분하기 어렵다 | 동작 변경 없음 | 2 (R3-4, R6-3) |
| 57 | 하 | `prev_generated_mutation`을 `_init_per_matrix_state`에 선언한다 | 1곳 | 같은 함수 안에서 `is not None`과 `hasattr` 두 방식으로 방어하는 것이 순서 위험의 증거 | 동작 변경 없음 | 2 (R5-3) |
| 58 | 하 | `Finalize_Reorder_Round`에 `_` 접두사를 붙인다 | 3곳 | 같은 짝의 다른 셋은 `_` 접두사를 갖는다 | 동작 변경 없음 | 2 (R3-1) |
| 59 | 하 | `InsertRestartGroupState`에 "변수 설명" 절을 더한다 | 상태 dataclass | 나머지 3개는 갖고 있다 | 동작 변경 없음 | 3 |
| 60 | 하 | 매직 넘버 3종(결과 파싱 재시도, 파일 크기 안정 확인)을 `TIME_CONFIG`로 옮긴다 | [8189](5_DAO/SRC/DAO_Main.py#L8189), [8211](5_DAO/SRC/DAO_Main.py#L8211), [8216](5_DAO/SRC/DAO_Main.py#L8216) | `RESULT_PARSE_MAX_RETRIES`, `RESULT_SIZE_STABLE_CHECK_COUNT` 등 | 동작 변경 없음 | 3 |

---

## ㉯ 팀 내 교차 분석

### 충돌 (같은 코드에 서로 다른 처방)

- ㉠ **헤더 재구성 함수의 이름과 소속이 갈린다.** 워커 1은 [5108-5132](5_DAO/SRC/DAO_Main.py#L5108)를 `LLR_MATRIX.Rebuild_Header_Group_Arrays`로 옮기자고 하고(3자리를 한 곳으로), 워커 2는 같은 자리를 품은 [5107-5160](5_DAO/SRC/DAO_Main.py#L5107)을 `LLR_OPT.Rebuild_Header_After_Reorder(matrix, new_groups)`로 뽑자고 한다. 같은 줄에 두 이름이 붙는다. **판정: 워커 1 안을 채택한다** (`LLR_MATRIX`의 메서드여야 세 자리가 한 곳으로 모이고, 옆 세션이 고칠 자리가 8곳에서 3곳으로 준다). 워커 2의 추출은 그 메서드를 부르는 껍데기로 남긴다
- ㉡ **그룹 삽입 함수도 같은 모양으로 갈린다.** 워커 1의 `Insert_Group_Into_Header`(헤더 배열만, [3069-3078](5_DAO/SRC/DAO_Main.py#L3069) 등 4자리)를 워커 2의 `Insert_Group_And_Fix_Header`([3063-3098](5_DAO/SRC/DAO_Main.py#L3063), 헤더 + restart_groups 보정 + max_iteration)가 통째로 감싼다. 두 이름이 한 낱말 차이라 읽는 사람이 어느 쪽인지 모른다. **판정: 두 겹으로 두되 바깥 이름을 `Insert_Group_And_Renumber_Restart_Groups`로 바꾼다.** 안쪽(`LLR_MATRIX.Insert_Group_Into_Header`)이 헤더 배열만, 바깥(`LLR_OPT`)이 restart 번호 보정까지
- ㉢ **멀티라운드 공통 상태 dataclass의 이름이 둘이다.** 워커 1은 `Round_Based_Mode_State`, 워커 2는 `GreedyRoundState`. **판정: `Round_Based_Mode_State`를 쓴다** (greedy는 업계 용어라 프로젝트 규칙 "축약어와 업계 용어는 풀어 쓴다"에 걸린다). 방향도 다르다. 워커 2는 dataclass는 그대로 두고 공용 함수 2개를 만드는 작은 단계, 워커 1은 상태가 자기 메서드를 갖게 해 문자열 디스패치를 없애는 큰 단계다. **순서: 워커 2 먼저(36번), 워커 1 나중(28번).**
- ㉣ **모드 정보 표가 둘로 갈릴 위험이 있다.** 워커 1의 `GEN_LLR_MODE_SPECS`(15곳을 5곳으로)와 워커 2의 `MODE_CONFIG_CLASS: dict[int, type]`이 둘 다 `DAO_Constants.py`에 새 표를 만든다. **따로 만들면 흩어진 자리가 15곳에서 16곳이 된다.** 판정: `MODE_CONFIG_CLASS`를 `GEN_LLR_MODE_SPECS`의 한 열로 넣는다
- ㉤ **`DAO_LLR_MATRIX.py`에 대해 순서 권고가 반대다.** 워커 1은 R8-1~R8-4를 옆 세션 SW 분기 작업 **전에** 하라고 하고(그래야 옆 세션이 고칠 자리가 29곳에서 10곳으로 준다), 워커 2와 워커 3은 자기 처방을 옆 세션 **뒤에** 하라고 한다. **정면 충돌은 아니다.** 손대는 부분이 다르기 때문이다. R8-1~R8-4는 row 꼬리와 헤더 배열과 유효성 규칙(옆 세션이 고치는 바로 그 자리)이고, 워커 2의 `Get_Channel_Result`와 `Deep_Copy`, 워커 3의 docstring은 FER 결과 필드와 복사 인자(옆 세션과 무관한 자리)다. 판정: **R8-1~R8-4만 옆 세션과 순서를 협의해 먼저 넣고, 같은 파일의 나머지 처방은 전부 뒤로 미룬다**

### 중복 (같은 것을 두 워커가 따로 지적)

- ㉠ `CONFIGS`에 3클래스 누락: 워커 1(모드 등록 교차표)과 워커 2(R4-6)가 같은 것을 지적했다. 처방이 같으므로 한 번에 고친다 (40번)
- ㉡ `Set_Gen_Trial_LLR_Mode`의 13갈래 elif: 워커 2가 `Calculate_Max_Modification_Trial`로 뽑자고 하고, 워커 1이 같은 자리를 표 조회로 바꾸자고 한다. **겹침이지 충돌이 아니다.** 순서는 워커 2가 먼저(함수로 뽑고), 워커 1이 나중(본문을 표 조회로)
- ㉢ `Print_Config` 대 `Print_Configs`: 워커 2가 R3-4(이름)와 R6-3(중복 본문) 두 관점에서 따로 지적했다. 한 번에 고친다 (56번)
- ㉣ `TEST_MODE_DIR_NAME`이 정의만 있고 미사용: 워커 3의 매직 넘버 표와 T팀 실마리 ㉳이 같은 대상이다

### 시너지 (한쪽이 다른 쪽을 쉽게 만듦)

- ㉠ 워커 2의 `Mutate_Matrix_Setup` 껍데기 제거(14번)가 워커 1이 찾은 "책임군 사이 역방향 호출 2곳" 중 하나를 없앤다. 분할(5번)이 더 깨끗해진다
- ㉡ 워커 3의 "함수 단위 링크에서 줄 번호를 뺀다"(20번)가 워커 1의 파일 분할(5번) 뒤에도 문서 링크가 깨지지 않게 한다. **다만 파일 경로 자체는 바뀌므로**(`SRC/DAO_Main.py` → `SRC/DAO_Uncor_Pool.py` 등) 분할 뒤 링크를 한 번 더 손봐야 한다. 이 후속 작업이 워커 3 문서에 빠져 있다
- ㉢ 워커 1의 `Get_Channel_Result`(10번)와 워커 2의 `Write_Channel_FER_Lines`(46번)가 짝을 이룬다. 접근자가 먼저다

### 다른 팀 판정에 걸린 것

- ㉠ **L팀 → 6번, 30번, 40번**: `HBF_OPT_CONFIG` 부수효과가 실행되지 않아 `IS_HBF_OPT`가 항상 False이고 HBF 경로 전체가 죽어 있다(9번). 워커 1의 모드 등록 교차표와 워커 3의 "미사용 상수" 목록이 모두 이 죽은 경로를 전제로 세어졌다. **L팀이 HBF 경로를 살릴지 지울지 정하기 전에는 모드 표(6번)와 미사용 상수 처리를 확정할 수 없다.** `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`의 올바른 값도 L팀 몫이다
- ㉡ **L팀 → 6번**: `Set_Update_Flags`(11개)와 `Print_Test_Summary`(10개)의 모드 목록이 `INSERT_RESTART_GROUP`에서 갈린다. 어느 쪽이 맞는지 정해야 표로 합칠 수 있다
- ㉢ **T팀 → 22번, 52번**: `"Partial"` 문자열 7곳과 미사용 `TEST_MODE_DIR_NAME`을 어느 쪽으로 정리할지, `Mock_ECC.MAX_CSW`를 1408로 맞출지
- ㉣ **M팀 → 37번, 49번**: `Decide_On_Root` 도우미가 집단 통신 정합을 해치지 않는지, `MPI_COMM_TIMEOUT_SECONDS` 문서 값
- ㉤ **L팀 → 8번, 9번**: 워커 2가 찾은 동작 결함 2건의 심각도 판정. 가독성 처방이 아니라 수리 대상이다

---

## ㉰ 미커버 영역

- ㉮ **회귀 확인 수단이 없다.** `5_DAO`에 시험 코드가 하나도 없다 (`find`와 `grep`으로 확인, `pytest`와 `unittest` import 0건). 개선안 60개 가운데 "동작 변경 없음"이라고 적은 것이 40개 남짓인데, 이를 확인할 방법을 세 워커 누구도 처방하지 않았다. [Util/Mock_ECC.py](5_DAO/Util/Mock_ECC.py)가 외부 ECC 실행 파일을 흉내 내므로, 이것을 써서 "매트릭스 하나를 넣고 출력 파일을 대조하는" 최소 회귀 시험을 만드는 것이 분할 작업(5번, 27번)의 전제가 되어야 한다
- ㉯ **`Util/` 8개 스크립트의 내부 가독성** (합계 1,278줄). 워커 3은 사용법과 실행 전제만 보았고, 함수 구조와 이름과 중복은 아무도 보지 않았다
- ㉰ **타입 표기의 유무와 일관성.** "타입 힌트와 실제 값이 다른 곳"(P17)은 L팀 몫이지만, "메서드 212개 가운데 반환 타입 표기가 있는 것이 몇 개인가"라는 가독성 질문은 세지 않았다
- ㉱ **로그 문구가 사람용인지 기계 파싱용인지.** 49번(구분선과 머리표 통일)과 18번(이모지 제거)이 로그 문구를 바꾸는데, 외부 도구나 [Util/fer_plot/fer_plot.py](5_DAO/Util/fer_plot/fer_plot.py)가 이 로그를 파싱하는지 확인하지 않았다. 파싱한다면 문구 변경이 동작 변경이 된다
- ㉲ **분할 뒤의 import 그래프.** 워커 1이 현재 모듈 4개 사이에 순환이 없음을 확인했으나, 메서드 묶음 클래스 12개로 나눈 뒤의 import 그래프는 그리지 않았다. 새 파일이 `DAO_LLR_MATRIX`와 설정 클래스를 각자 반입하므로 분할 설계 시 한 번 그려야 한다

---

## ㉱ 팀 종합 처방 (적용 순서)

10,428줄을 읽을 수 있게 만드는 길은 **㉠ 먼저 위험 0인 문구와 이름을 정리해 뒤 단계의 diff를 읽기 쉽게 만들고 ㉡ 옆 세션이 곧 손댈 매트릭스 모델을 먼저 손봐 그쪽 비용을 줄이고 ㉢ 충돌 없는 인프라부터 파일로 떼어내고 ㉣ 나머지는 옆 세션이 끝난 뒤에 한다**는 네 마디로 요약된다.

| 단계 | 하는 일 | 개선안 번호 | 왜 이 자리인가 |
|------|--------|-----------|--------------|
| 0 | **회귀 확인 수단 만들기.** `Util/Mock_ECC.py`로 매트릭스 하나를 돌려 출력 파일을 저장하고, 각 단계 뒤 같은 입력으로 돌려 대조한다 | 미커버 ㉮ | 이후 40개 처방의 "동작 변경 없음"을 확인할 방법이 지금 없다. 이것 없이는 분할이 검증 불가능한 변경이 된다 |
| 1 | **동작 결함 2건 판정** (L팀으로 넘김) | 8, 9 | HBF 경로가 살아나는지에 따라 모드 표(6번)의 내용과 미사용 상수 처리가 달라진다. 뒤 단계 전체의 전제다 |
| 2 | **코드 안 문구와 이름 정리.** docstring 불일치, `Raises:` 절, 줄표와 이모지, 과거 서술 주석, 매직 넘버, 껍데기 함수 제거, 이름 바꾸기 | 13~19, 22, 44, 48, 56~60, 14, 12 | 위험 0이고 파일 하나 안에서 끝난다. 여기서 이름을 확정해야 뒤의 분할 diff가 "옮기기"만 담아 읽기 쉬워진다. 12번(19곳)과 14번은 분할 전에 하는 것이 grep 범위가 좁다 |
| 3 | **매트릭스 모델 정리** (옆 세션과 순서 협의) | 1, 2, 3, 4 | 옆 세션 SW 분기 작업 **전에** 들어가야 이득이 있다. 넷이 먼저 들어가면 그쪽이 고칠 자리가 row 29곳에서 약 10곳으로, header 22곳에서 약 12곳으로 준다. 늦으면 이득이 사라진다. 특히 1번은 `floor_flag != -1` 규칙이 분기 매트릭스를 전부 무효 판정하는 자리라 그쪽 작업의 진입점이다. 4번은 여덟 자리의 현재 값을 표로 대조한 뒤에 옮긴다 |
| 4 | **인프라 10개 군 분리** | 5, 7, 31, 32 | 충돌 위험이 없고 3,762줄이 옮겨가 `DAO_Main.py`가 6,600줄대가 된다. 5번의 4단계(MPI 군)가 끝나야 7번(MPI 초기화 이동)이 가능하고, 7번이 끝나야 31번(별표 import 정리)이 의미를 갖는다 |
| 5 | **긴 함수와 반복 관용구 정리** | 10, 11, 36, 37, 38, 39, 41, 43, 45, 46, 34 | 4단계로 파일이 갈린 뒤에 하면 각 처방의 diff가 한 파일 안에 담긴다. 11번은 3단계의 4번과 경계가 겹치므로 4번이 먼저다. 37번은 M팀의 집단 통신 결론을 받은 뒤 |
| 6 | **모드 정보 표 하나로 모으기** | 6, 29, 30, 47 | 1단계의 L팀 판정이 필요하다. 모드 추가 비용을 15곳에서 5곳으로 줄이는 가장 큰 효과이면서, 전제가 가장 많다 |
| 7 | **옆 세션 완료 후: 생성 모드 군 분리와 상태 객체화** | 27, 28, 33, 35, 42 | 전부 옆 세션이 고치는 파일과 정면으로 겹친다. 먼저 하면 diff가 통째로 어긋난다. 끝나면 `DAO_Main.py`가 약 2,200줄이 된다 |
| 8 | **문서 마무리** | 20, 21, 23, 24, 25, 26, 50, 51, 53, 54, 55 | 코드 이름과 파일 경로가 다 정해진 뒤 한 번에 고친다. 4단계와 7단계로 파일 경로가 바뀌므로 20번(링크)은 여기서 한 번 더 손본다. Util 처방(23~26, 53~55)은 코드 단계와 독립이라 언제든 가능하다 |

**가장 급한 하나**를 고르라면 3단계의 1번(`floor_flag` 규칙을 이름 붙인 함수로 뽑기)이다. 옆 세션이 SW 분기 필드를 넣는 순간 지금 규칙이 분기 매트릭스를 전부 무효로 판정하고, 그 규칙은 184줄짜리 유효성 함수 한가운데 한 줄로 박혀 있어 찾기 어렵다.
