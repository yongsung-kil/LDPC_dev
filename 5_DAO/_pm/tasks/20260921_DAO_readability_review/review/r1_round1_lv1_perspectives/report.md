# Round 1 결과: 관점 리스트업

> 기록: 2026-09-21 15:02:00
> 에이전트 3개(A, B, C, 모델 Opus) 독립 도출. 원본은 [agent_A.md](agent_A.md), [agent_B.md](agent_B.md), [agent_C.md](agent_C.md)

세 에이전트가 낸 관점 90개(A 34, B 28, C 28)를 겹치는 것끼리 묶어 30개로 정리했다.
"출처" 열은 각 에이전트 문서의 관점 번호다. 확인 항목의 상세는 출처 문서의 해당 행에 있다.

## 축 ㉮ 가독성 관점 (R1~R11)

| # | 관점명 | 확인 항목 (요약) | 대상 파일/범위 | 출처 |
|---|--------|----------------|--------------|------|
| R1 | `LLR_OPT` 책임 경계와 파일 분할 축 | 메서드 약 200개를 책임군으로 분류하고 군별 `self` 속성 집합을 뽑아 공유 상태가 적은 순으로 분할 후보를 낸다. 호출 방향과 `DAO_LLR_MATRIX`와의 경계도 본다 | `DAO_Main.py` 클래스 전체, `__init__`과 `_init_per_matrix_state` | A:A1, B:A1 A2, C:A1 A2 |
| R2 | 생성 모드 정보의 분산과 문자열 디스패치 | 모드 하나를 추가할 때 손대는 자리 수(열거형, 시퀀스, `Gen_Trial_LLR` elif 사슬, `Set_Gen_Trial_LLR_Mode`, `MULTI_ROUND_*` 딕셔너리, `SKIP_RESTART_GROUP`, 설정 클래스), `getattr` 문자열 키 호출 | `DAO_Constants.py` 24~196, `DAO_Main.py` `Gen_Trial_LLR`, `Set_Gen_Trial_LLR_Mode`, `Run_Optimization` | A:A2 A3, B:A5, C:A5 A6 |
| R3 | 이름 규약과 같은 뜻의 다른 이름 | 대소문자 규약 혼재(`Gen_LLR_*`, `_safe_bcast`, `BACKUP_SRC`), target 인덱스 이름 4종, FER 이름 7종, 이름이 수단이 아니라 목적을 가리키는지 | `def` 목록 전체, `Initialize_Stage`, `Set_Gen_Trial_LLR_Mode`, 속성 목록 | A:A4, B:A4, C:A3 |
| R4 | 설정 계층과 설정 값이 확정되는 시점 | 클래스 속성 기본값, `Set_Configs_Manually`(argv), `Update_Configs`, `HBF_OPT_CONFIG.__init__` 부수효과, `SPEED_TEST_REFC_CONFIG` 상속의 순서와 정본 위치 | `DAO_Config.py` 22~118, 218~238, 366~375, `DAO_Main.py` 403~480 | A:A5, B:A6, C:A7 |
| R5 | 인스턴스 상태의 생성 위치 | `__init__` 밖에서 처음 생기는 속성(`hasattr` 검사, `Initialize_Stage`, `Make_Dirs`, `Set_CSW_Update_Limit`)과 읽는 쪽의 순서 의존 | `DAO_Main.py` 482~660, 2276~2296, 6593, 8285~8291 | A:A8, B:A3, C:B12 |
| R6 | 함수 길이, 중첩 깊이, 반복 관용구 | 300줄 넘는 함수의 구획, root 판단 뒤 `_safe_bcast` 관용구의 반복, 멀티라운드 모드 4개의 유사 코드, `Print_Config`와 `Print_Configs` 중복 | `Gen_LLR_Insert_Mutated_Group`, `Build_Reordered_Matrix`, `Run_Optimization`, `Validate_Config`, 4446~6328 | A:A6 A7, B:A7 A8, C:A4 A9 |
| R7 | 전역 이름 반입과 모듈 의존 방향 | `from X import *` 두 줄, `DAO_Constants`가 MPI `comm`/`rank`를 만드는 구조, `LLR_MATRIX`가 설정에 의존하는지 | `DAO_Main.py` 1~10, `DAO_Constants.py` 135~139, `DAO_LLR_MATRIX.py` 상단 | A:A9, B:A12, C:A8 |
| R8 | 매트릭스 데이터 모델의 확장 용이성 | `LLR_Header`/`LLR_Row`에 필드를 하나 더할 때 손대는 자리(읽기, 쓰기, `Deep_Copy`, `Is_LLR_Valid`, 출력 줄 구성, 생성 모드) | `DAO_LLR_MATRIX.py` 전체 | A:A10 |
| R9 | docstring, 주석, 로그 문구, 매직 넘버 | docstring과 실제 시그니처/동작 불일치, 과거와 현재를 서술하는 주석, 로그 문구의 한영 혼용과 이모지와 줄표, 문턱값 상수화 | `Run_ECC`, `Gather_Ref_C_Results`, `Read_FER_From_File`, `Copy_Uncors`, `Write_Log_Lines` 호출 전반 | A:A11 A12 A13, B:A9 A11, C:A10 A11 A12 |
| R10 | README와 DAO_spec의 이름과 링크 정합 | 문서가 쓰는 이름이 코드에 있는지, 링크 경로가 이 저장소에 맞는지 | `README.md` 1.2, 2.2, 3.2, 4.1절, `DAO_spec.md` 3장과 8장 | A:A14, B:A10, C:A13 |
| R11 | Util 스크립트의 사용법과 실행 전제 | 경로와 접속 정보 하드코딩, 사용법 안내 유무 | `Util/*.py`, `Util/fer_plot/fer_plot.py` | A:A15, B:A13 |

## 축 ㉯ 문제점 관점 (P1~P19)

| # | 관점명 | 확인 항목 (요약) | 대상 파일/범위 | 출처 |
|---|--------|----------------|--------------|------|
| P1 | 집단 통신의 rank 정합 | root 전용 블록의 탈출 경로(`MPI_Abort`, `return`, `continue`)가 bcast/gather/barrier 짝을 깨는지, Barrier 횟수가 rank마다 같은지, rank마다 다를 수 있는 값으로 분기하는 자리 | `Gen_Trial_LLR`, `Set_Gen_Trial_LLR_Mode`, `Test_LLR`, `Run_Optimization`, `Update_Optimal_LLR`, `Run_ECC` | A:B1, B:B1 B2 B3, C:B1 |
| P2 | 타임아웃 워치독과 미적용 통신 | `_mpi_comm_with_timeout` 스레드 안전성, `Reduce`/`allgather` 직접 호출 3곳, 타임아웃 값 불일치(1200초 대 3600초) | `DAO_Main.py` 6685~6996, 1861, 7011, 9049, `TIME_CONFIG` | A:B2, B:B4, C:B2 |
| P3 | 파일 종료 신호와 ack 경쟁 | end flag 읽기와 쓰기 순서, ack 누락 보고, 카운트 감소 재진입 | `DAO_Main.py` 1045~1247, 2165~2180, `Run_Optimization` | A:B3, B:B5, C:B3 |
| P4 | Ref-C 결과 파싱과 집계 두 경로 | 결과 파일 재시도와 실패 처리, 누적 통계 초기화 시점, `Reduce` 경로와 파일 경로의 의미 차이 | `Gather_Ref_C_Results`, `Read_Ref_C_Result`, `Read_FER_From_File`, 576~600 | A:B4 B5, B:B6 B7, C:B4 |
| P5 | 외부 ECC 실행 실패와 재시도 | `Run_ECC` 재시도가 동기화에 주는 영향, `MAX_RUN_ECC_ERRORS`, 타임아웃 | `Run_ECC`, `DAO_Config.py` 123, 318~323 | A:B14, C:B5 |
| P6 | Two-stage 상태 기계와 비교 대상 | Partial에서 Full로 넘어가는 조건, `_Get_Compare_Target`, 강제 종료 시 Full 강제 수행, `MULTI_ROUND_FULL_ONLY_MODES` | `Test_Trial_LLR`, `Check_Partial_Improvement`, `_Run_Test_Stage`, `Run_Optimization` 8094~8113 | A:B6, B:B8, C:B10 |
| P7 | optimal과 temp_optimal의 승격 경로 | `Determine_Update_Decision`, `Update_Optimal_LLR`, `_Promote_Temp_Optimal_On_Stage_Exit`, 멀티라운드 `is_final` | `DAO_Main.py` 1398~1489, 9548~9646 | A:B7, B:B8, C:B11 |
| P8 | Partial pool 동적 재구성 | `Rebuild_Partial_Pool` 상태 복원, 재진입, `_Signal_Graceful_Stop_No_Partial` | `DAO_Main.py` 9283~9475 | B:B9 |
| P9 | uncor 파일 입출력과 세션 정리 | `Copy_Uncors`(미사용 `test_mode` 인자), `Delete_Uncors`, `Distribute_Uncors_To_Local_Session`, `Cleanup_Session` 대상과 시점, 파일 예외 처리 일관성 | `DAO_Main.py` 935~1021, 1248~1591, `DAO_LLR_MATRIX.py` 549 | A:B12, B:B13, C:B6 |
| P10 | 유효성 규칙과 spec 3장 대조, 자동 보정 뒤 재검증 | `Is_LLR_Valid` 대 H1~HBF2, C5(같은 값 허용 여부), `Correct_LLR_Matrix` 뒤 헤더 정합과 재검증 | `DAO_LLR_MATRIX.py` 266~449, 561~645, `Gen_Trial_LLR` 1994~2016 | A:B8 B9, B:B10 B11, C:B8 B9 |
| P11 | 그룹 구조 변경 뒤 인덱스와 헤더 일관성, 타겟 그룹 순환 | insert/delete/split/reorder 뒤 `num_group`, `num_row_each_group`, `restart_groups`, `target_group_indices`, `current_target_idx` 갱신 | `Gen_LLR_Insert_Random_Group`, `_Delete_Entire_Group`, `Gen_LLR_Split_Group`, `Initialize_Stage`, 8313~8330 | A:B10 B11, C:B13 |
| P12 | 설정 검증 빈틈과 자기모순 | `Validate_Config` 사정권, `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`, `CSW_UPDATE_LIMIT_VALUE` 미정의, `CONFIGS` 누락, `TEST_MODE_DIR_NAME` FULL 누락, 파생값 재계산 누락 | `Validate_Config`, `DAO_Config.py`, `DAO_Constants.py` 76~80 | A:B16, B:B12, C:B7 |
| P13 | 코어 속도 테스트와 제외 코어 파급 | `excluded_cores`와 uncor 보유 상태, `_Redistribute_Uncor_Pool_Uniform`, `allgather` | `Test_Core_Speed`, `Periodic_Recheck`, `_Recheck_Speed_Test`, `active_cores` | A:B15, C:B14 |
| P14 | 예외 처리와 종료 경로 | `MPI_Abort`, `Log_Unhandled_Exception`, `_write_error_log`, `except Exception` 삼킴, 진단 비용 | `DAO_Main.py` 172~205, 2547~2560, 6800~6894, `Main` | A:B13, B:B15 |
| P15 | 로그 회전과 로그 백업 | `Write_Log_Lines` 회전의 재진입, rename 실패, `Make_Log_Backup` | `DAO_Main.py` 787~817, 6621~6684, 9911~9961 | B:B14 |
| P16 | 난수와 재현성 | `Set_Python_Seed`, `Restore_Random_State_If_Configured`, rank별 시드 | `DAO_Main.py` 8744~8785, 2352~2360 | A:B17 |
| P17 | 타입 표기와 실제 값 불일치 | 타입 힌트와 실제 대입 값이 다른 곳 | `DAO_Main.py` 596~600, 1868~1872 | A:B18 |
| P18 | GEN_SINGLE_ROW 독립 경로 | `Run_Single_Row_Generation`의 stop idx 파일, Top-K 저장, end flag 주기 검사 | `DAO_Main.py` 10027~10400, `SINGLE_ROW_CONFIG` | C:B15 |
| P19 | Util 스크립트의 위험 | 하드코딩 접속 정보와 빈 경로, 실행 시 부작용 | `Util/remote_server_sync.py`, `Util/check_result_files.py` | A:B19, C:참고 |

## Round 1에서 나온 실마리 (결론 아님, Round 2에서 확인)

세 에이전트가 관점을 정하다가 적어 둔 관찰이다. 검증 전이므로 발견으로 세지 않는다.

- ㉮ README 2장과 4장이 쓰는 이름 가운데 코드에 없는 것: `ExitAfterInitialMatrixMode`, `EXIT_AFTER_INITIAL_MATRIX_MODE`, `PARTIAL_UNCOR_MATRIX_IDX`, `FULL_UNCOR_MATRIX_IDX`, `MAX_STAGE_TIME_SECONDS`, `effective_FERs`, `Read_LLR_from_File`, `Write_To_File`. 링크는 모두 옛 `DAO/SRC/...` 경로 (A, B, C 공통)
- ㉯ `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`가 `GenLLRMode` 값 집합과 겹치지 않고, `GenLLRModeHBF` 열거형은 미사용 (A, B, C 공통)
- ㉰ `Is_LLR_Valid`의 CSW 검사가 같은 값을 금지하는데 spec C5는 non-increasing (B, C)
- ㉱ `comm.Reduce`(1861), `comm.allgather`(7011, 9049)가 `_mpi_comm_with_timeout`을 거치지 않음 (C)
- ㉲ `MPI_COMM_TIMEOUT_SECONDS` 실제 값 1200초, 주석은 "1시간 이상이면 타임아웃 없음", `MPI_Barrier`만 `max(값, 3600)` (B)
- ㉳ `TEST_MODE_DIR_NAME`에 `TestMode.FULL` 항목 없음 (B, C)
- ㉴ `Copy_Uncors`의 `test_mode` 인자 미사용, README 3.2.4의 Partial/Full 하위 디렉토리 설명과 경로 계산이 다름 (B)
- ㉵ `Init_Reorder_Group_Mode` 로그가 `current_target_idx`를 읽는데 이 속성은 `Initialize_Stage`에서 `hasattr`로 만들어짐. 호출 순서 확인 필요 (C)
- ㉶ `Set_CSW_Update_Limit`을 부르는 자리가 보이지 않음. `CSW_UPDATE_LIMIT_VALUE`는 `ENABLE_CSW_UPDATE_LIMIT`이 참일 때만 정의됨 (A, C)
- ㉷ `CONFIGS` 목록에 `SPEED_TEST_REFC_CONFIG`, `ADJUST_ITERATION_CONFIG`, `PATH_CONFIG` 누락. `HBF_OPT_CONFIG`는 `__init__`에서 `DAO_CONFIG.IS_HBF_OPT`를 바꾸는 부수효과 (A, B)
- ㉸ `ReorderState` docstring이 설명하는 `total_rounds`, `round_best_FER`, `round_best_avg_iter` 필드가 dataclass에 없음 (B)
- ㉹ `Run_ECC` docstring "Args: 없음"인데 `ch_idx`를 받음. `Gather_Ref_C_Results`, `Read_FER_From_File` docstring은 예외를 던진다고 적었으나 실제는 `MPI_Abort` (A)
- ㉺ 로그와 주석에 줄표(U+2014) 17곳, 이모지 10곳, `Make_Log_Backup` docstring에 유니코드 대체 문자(U+FFFD) 3개 (A, B, C)
- ㉻ `Util/check_result_files.py` 대상 경로가 빈 문자열, `Util/remote_server_sync.py`는 접속 정보를 본문에 적음 (A, B, C)

## 다음 단계 결정

→ Round 2 (lv2, 4팀)
  사유: 대상이 변경분이 아니라 10,428줄 코드 전체이고 관점이 30개다. lv1로는 에이전트 하나가 맡을 범위가 너무 넓어 메인 컨텍스트와 분석 깊이 모두 부족하다. 팀 리더가 워커 2~3개에 관점을 나누고 교차 분석한 요약만 받는다.

| 팀 | 이름 | 배정 관점 |
|----|------|----------|
| R | 가독성 | R1~R11 |
| M | MPI 통신과 프로세스 수명 | P1, P2, P3, P5, P13, P14, P15, P16 |
| L | 매트릭스 모델, 생성 모드, 설정 | P10, P11, P12, P17, P18 |
| T | 테스트 파이프라인과 결과 집계 | P4, P6, P7, P8, P9, P19 |

라이트 리뷰이므로 Round 2에서 종료한다.
