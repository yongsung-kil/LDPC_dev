# 팀 T 요약: 테스트 파이프라인과 결과 집계

> 기록: 2026-09-21 15:26:00
> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 배정 관점: P4, P6, P7, P8, P9, P19 + Round 1 실마리 ㉳㉴㉻

핵심 질문: FER 측정 결과가 잘못 집계되거나, Two-stage와 temp_optimal 승격이 틀린 매트릭스를
최적으로 남기거나, uncor 파일 처리가 어긋나는 자리가 있는가.

워커 셋이 독립으로 44건을 냈고 겹치는 3쌍을 묶어 고유 발견 41건이 남았다.

| 심각도 | 건수 |
|--------|------|
| CRITICAL | 2 |
| HIGH | 6 |
| MEDIUM | 18 |
| LOW | 15 |

워커 문서: [worker_T_1.md](worker_T_1.md) (P4 결과 파싱과 집계),
[worker_T_2.md](worker_T_2.md) (P6 P7 P8 Two-stage와 승격),
[worker_T_3.md](worker_T_3.md) (P9 P19 uncor 파일과 세션 정리, Util)

---

## ㉮ 워커 결과 요약

### CRITICAL

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| 1 | CRITICAL | 한 채널의 uncor 풀만 비어도 그 채널에서 `total_tests=0`이 되어 MPI 작업 전체가 `MPI_Abort`로 끝난다. 빈 채널을 거르는 두 자리가 채널별이 아니라 전체 합만 본다 | [DAO_Main.py:1883](5_DAO/SRC/DAO_Main.py#L1883), [DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426), [DAO_Main.py:9341](5_DAO/SRC/DAO_Main.py#L9341) | `ENABLE_TWO_STAGE_TEST=True`이고 채널 하나의 fail uncor가 0개, 다른 채널은 1개 이상. 최적화가 잘 될수록 쉬운 채널부터 먼저 도달 | `Test_LLR` 채널 루프 머리에 `has_uncor[ch_idx]`가 거짓인 채널 건너뛰기를 넣고 `_Fill_Untested_Channels`와 같은 규칙으로 채운다. `Rebuild_Partial_Pool`과 `_Build_Initial_Partial_Pool`의 0개 판정을 채널별로 바꾼다 | T1 |
| 2 | CRITICAL | Partial uncor 0개 정상 종료가 `MPI_Abort`로 끝난다. `_Signal_Graceful_Stop_No_Partial`이 종료 플래그 파일만 쓰는데 `Run_Optimization`은 `Test_Trial_LLR` 뒤에야 읽고 `Main`은 `Run_Initial_Test`와 `Run_Optimization` 사이에서 읽지 않아, 빈 Partial 풀로 테스트가 한 번 더 돈다 | [DAO_Main.py:9457](5_DAO/SRC/DAO_Main.py#L9457), [DAO_Main.py:8070](5_DAO/SRC/DAO_Main.py#L8070), [DAO_Main.py:10017](5_DAO/SRC/DAO_Main.py#L10017) | `ENABLE_TWO_STAGE_TEST=True`, `RUN_DAO_MODE=RUN_OPTIMIZATION`이고 어떤 매트릭스가 Full uncor를 전부 복호할 때 | `self.is_graceful_stop` 속성을 두고 `_Signal_Graceful_Stop_No_Partial`이 전 rank에서 True로 세운다. trial 루프의 `Initialize_Trial` 직후, stage 루프의 `Periodic_Recheck` 앞, `Main`의 `Run_Initial_Test`와 `Run_Optimization` 사이 세 자리에서 검사해 빠져나간다 | T2 |

### HIGH

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| 3 | HIGH | 재디코딩 출력 `redecode_uncor_seed_*.txt`를 외부 ECC 실행 전에 지우는 자리가 없어 Partial 풀에 지난 라운드의 실패 프레임이 다시 섞인다. 외부 ECC의 `Print_Seed`가 추가 모드로 열고([random.cpp:209](0_LDPC_original/src/random.cpp#L209)), `Delete_Own_Uncors`는 `SAVE_UNCOR_SEED`일 때만, 그것도 재디코딩 접두사가 없는 이름만 지운다 | [DAO_Main.py:8469](5_DAO/SRC/DAO_Main.py#L8469), [DAO_Main.py:1515](5_DAO/SRC/DAO_Main.py#L1515) | `ENABLE_TWO_STAGE_TEST=True`, `LOAD_UNCOR_MODE=LOAD_SEED`, optimal이 2회 이상 갱신되어 `Rebuild_Partial_Pool`이 2회 이상 도는 경우 | `Delete_Own_Uncors`에 `is_redecoded_uncor` 인자를 더하고, `Set_Test_Environment` 8469줄의 조건을 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`까지 넓혀 `is_redecoded_uncor=True`로 부른다 | T3 |
| 4 | HIGH | 파싱 실패로 통째로 버려진 코어의 누적 결과가 "정상 0"과 구분되지 않아 표본이 줄어든 채 FER이 계산되고, 허용 오차 없는 비교가 그 차이를 개선이나 열화로 읽어 trial 채택이 뒤집힌다. 줄 하나가 깨지면 그 코어의 누적 결과 전부가 빠진다 | [DAO_Main.py:8265](5_DAO/SRC/DAO_Main.py#L8265), [DAO_Main.py:1823](5_DAO/SRC/DAO_Main.py#L1823), [DAO_Main.py:2510](5_DAO/SRC/DAO_Main.py#L2510) | 재시도 4회 안에 결과 파일이 안정되지 않는 코어가 하나라도 있을 때 | `Read_Ref_C_Result`가 실패를 성공과 구별되는 값으로 돌려주고, 집계가 실패 코어 수를 세어 하나라도 있으면 그 라운드 결과를 판정에서 뺀다 | T1 |
| 5 | HIGH | `Rebuild_Partial_Pool`이 Partial 0개로 조기 반환할 때 Step 7 상태 복원을 건너뛴다. `current_seed_mode`가 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로 고착하고(`Set_Seed_Mode`가 이 값을 보존한다), `current_test_mode`, `current_loaded_test_mode`, `optimal.FERs_partial`도 복원되지 않는다 | [DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426), [DAO_Main.py:9443](5_DAO/SRC/DAO_Main.py#L9443), [DAO_Main.py:8504](5_DAO/SRC/DAO_Main.py#L8504) | 발견 2와 같은 조건 | 진입 시점 값을 저장해 try와 finally로 복원한다. 복원값을 `SeedMode.LOAD_UNCOR_SEED` 상수로 고정하는 것도 저장값으로 바꾼다. Step 6을 조기 반환 앞으로 옮긴다 | T2 |
| 6 | HIGH | 미테스트 표시값 `avg_iterations = -1.0`이 "낮을수록 좋음" 비교에서 가장 좋은 값이 되어, 테스트하지 않은 매트릭스가 round best나 temp_optimal이 된다. 전부 제대로 측정한 매트릭스는 미테스트 채널을 가진 상대를 이기지 못한다 | [DAO_Main.py:1189](5_DAO/SRC/DAO_Main.py#L1189), [DAO_Main.py:1194](5_DAO/SRC/DAO_Main.py#L1194), [DAO_Main.py:2540](5_DAO/SRC/DAO_Main.py#L2540) | 입구 둘. ㉮ 조기 채널 중단으로 뒤쪽 채널이 채워진 매트릭스가 `REORDER_GROUP` 첫 후보가 되고 이후 후보들의 FER이 동률일 때 ㉯ Partial에서 걸러져 Full을 건너뛴 trial이 전 채널 FER 1.0인 baseline과 비교될 때 | `_Fill_Untested_Channels`가 `avg_iterations`에 `float("inf")`를 넣는다. 더해서 `Is_Matrix_Better`가 두 번째 단계에 들어가기 전에 `num_tests`에 0이 있으면 False를 돌려준다 | T1, T2 |
| 7 | HIGH | `Util/remote_server_sync.py`가 원격 스캔 실패를 오류로 집계하지 않아, 비거나 반쪽인 동기화 뒤에 이전 `server_sync_*` 폴더를 되돌릴 수 없게 지운다 | [remote_server_sync.py:96](5_DAO/Util/remote_server_sync.py#L96), [remote_server_sync.py:210](5_DAO/Util/remote_server_sync.py#L210) | 원격 하위 디렉토리 나열이 실패하거나 `remote_path`가 빈 상태로 주기 실행 | `_scan`의 두 except 절에서 오류 목록에 항목을 더하고, `delete_old_sync_folders` 호출 조건에 "내려받은 파일 수 > 0"과 "감지된 원격 파일 수 > 0"을 더한다 | T3 |
| 8 | HIGH | `Util/supercom/stop_after.sh`가 예제 Job ID(123456) 그대로 실행되면 그 번호 이상인 작업을 모두 정지시킨다 | [stop_after.sh:5](5_DAO/Util/supercom/stop_after.sh#L5) | 스크립트를 수정하지 않고 실행 | `MIN_JOBID`를 첫 인자로 받고 값이 없으면 사용법을 출력한 뒤 끝낸다. 정지 대상 목록을 먼저 출력하고 확인을 받는다 | T3 |

### MEDIUM (18건)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| 9 | MEDIUM | while 루프 중 집계가 다른 rank의 `Run_ECC` 완료를 기다리지 않는다 | [DAO_Main.py:8977](5_DAO/SRC/DAO_Main.py#L8977) | 코어 사이 속도 차가 있는 모든 실행 | `Run_ECC` 바로 뒤에 `MPI_Barrier`를 둔다. 루프 본문 안에는 집단 통신을 넣지 않는다 | T1 |
| 10 | MEDIUM | `Rebuild_Partial_Pool` Step 3의 `Test_LLR(self.optimal_LLR_matrix)`가 방금 승격된 optimal의 Full 측정값(`FERs`, `num_tests`, `avg_iterations`)을 재구성 실행 값으로 덮어써, 이후 모든 비교의 기준이 승격 시점 로그와 달라진다 | [DAO_Main.py:9379](5_DAO/SRC/DAO_Main.py#L9379), [DAO_Main.py:1898](5_DAO/SRC/DAO_Main.py#L1898) | Two-stage에서 optimal이 갱신될 때마다. 그 사이 `Periodic_Recheck`로 제외 코어가 바뀌면 분모가 달라진다 | Step 3 앞에서 optimal의 결과 필드를 보관하고 Step 6 앞에서 되돌린다 | T1 |
| 11 | MEDIUM | Partial에서 걸러져 Full을 건너뛴 trial이 멀티라운드 round result 갱신에 FER 1.0, avg_iter -1.0으로 들어가 로그에 측정값처럼 남고 baseline과 비교된다 | [DAO_Main.py:8047](5_DAO/SRC/DAO_Main.py#L8047), [DAO_Main.py:5670](5_DAO/SRC/DAO_Main.py#L5670) | `ENABLE_TWO_STAGE_TEST=True` + `DELETE_ROW` 또는 `INSERT_RESTART_GROUP`에서 Partial 개선이 없는 trial | `Test_Trial_LLR`의 반환값 `should_check_update`로 round result 갱신을 가드한다. state 동기화 bcast는 조건 밖에 둔다 | T1, T2 |
| 12 | MEDIUM | `Read_Ref_C_Result`의 재시도가 `ValueError`만 덮어 `OSError`는 설계 밖에서 프로세스를 끝낸다 | [DAO_Main.py:8265](5_DAO/SRC/DAO_Main.py#L8265) | 결과 파일이 읽기 도중 사라지거나 잠겼을 때 | `except (ValueError, OSError)`로 넓힌다 | T1 |
| 13 | MEDIUM | `LOAD_UNCOR_VECTOR`에서는 uncor 없는 코어가 `Run_ECC`를 건너뛰지 않는다 | [DAO_Main.py:7931](5_DAO/SRC/DAO_Main.py#L7931) | `LOAD_UNCOR_MODE=LOAD_VECTOR`이고 어떤 코어에 분배된 uncor가 0개 | 건너뛰기 조건을 `is_load_seed_mode`로 넓힌다 | T1 |
| 14 | MEDIUM | 초기 테스트 직후 `Update_Optimal_LLR(is_initial=True)`가 `Rebuild_Partial_Pool`을 불러 같은 매트릭스로 Full 테스트를 한 번 더 수행한다 (시작 비용 2배) | [DAO_Main.py:9603](5_DAO/SRC/DAO_Main.py#L9603) | `ENABLE_TWO_STAGE_TEST=True`로 최적화를 시작할 때마다 | Rebuild 조건에 `and not is_initial`을 더한다. 초기 풀은 `_Build_Initial_Partial_Pool`이 이미 만든다 | T2 |
| 15 | MEDIUM | `DELETE_ROW`와 `INSERT_RESTART_GROUP`의 `max_modification_trial`이 final verification trial 한 칸을 포함하지 않아, 모든 라운드가 개선되면 최종 검증이 실행되지 않는다 | [DAO_Main.py:5415](5_DAO/SRC/DAO_Main.py#L5415), [DAO_Main.py:5772](5_DAO/SRC/DAO_Main.py#L5772) | 후보 N개가 모두 라운드마다 개선을 낼 때 | 두 곳의 `max_trials`를 `N * (N + 1) // 2 + 1`로 고치고 `total_expected_trials`도 같은 값을 받게 한다 | T2 |
| 16 | MEDIUM | `Gather_And_Archive_Uncors`가 `total_num_uncors`를 실패 프레임 수로 덮어쓰고 Full 수를 복원하지 않아, 이후 Full uncor 수를 말하는 로그가 Partial 수를 가리킨다 | [DAO_Main.py:2144](5_DAO/SRC/DAO_Main.py#L2144), [DAO_Main.py:9410](5_DAO/SRC/DAO_Main.py#L9410) | `ENABLE_TWO_STAGE_TEST=True`로 `_Build_Initial_Partial_Pool`이 한 번이라도 돈 뒤의 모든 로그 | `Gather_And_Archive_Uncors`가 병합 개수를 반환값에 담고 호출처가 목적에 맞는 변수에 넣는다 | T2, T3 |
| 17 | MEDIUM | 강제 종료 시 Full 강제 수행 경로가 `_Run_Test_Stage`를 쓰지 않고 준비 세 단계를 손으로 복제한다. `enable_early_channel_exit`를 넘기지 않아 측정 조건이 다르다 | [DAO_Main.py:8098](5_DAO/SRC/DAO_Main.py#L8098), [DAO_Main.py:9217](5_DAO/SRC/DAO_Main.py#L9217) | 시간 제한, DAO 종료 플래그, trial 종료 플래그 가운데 하나가 Partial 스킵 trial에서 걸릴 때 | `self._Run_Test_Stage(TestMode.FULL, self.current_LLR_matrix, enable_early_channel_exit=True)` 한 줄로 바꾼다 | T2 |
| 18 | MEDIUM | `Copy_Uncors`가 `test_mode` 인자를 본문에서 쓰지 않아 Partial 요청에도 Full 입력 파일을 복사한다 | [DAO_Main.py:1248](5_DAO/SRC/DAO_Main.py#L1248) | `Ensure_Uncors_Loaded`의 풀 미준비 분기로 들어가는 경우 (현재 설정 공간에서는 도달하지 않음) | `test_mode` 인자를 지우고 docstring의 Partial 언급을 뺀다. `Setup_Uncor_Pool`과 `Process_Uncors`의 `test_mode=` 전달도 제거한다 | T3 |
| 19 | MEDIUM | 입력 uncor 디렉토리 이름에 `.txt`가 붙는데 README는 확장자 없는 이름으로 적어, 문서대로 폴더를 만들면 시작하자마자 중단된다 | [DAO_Main.py:1276](5_DAO/SRC/DAO_Main.py#L1276), [README.md:724](5_DAO/README.md#L724) | `UNCOR_MATRIX_IDX >= 0`으로 두고 README대로 폴더를 만든 경우 | README 3.2.3과 6장 경로 예시를 `LLR_MATRIX_102.txt/` 형태로 고친다 | T3 |
| 20 | MEDIUM | README 3.2.2부터 3.2.4까지가 없는 설정과 상수를 설명한다 (`PARTIAL_UNCOR_MATRIX_IDX`, `FULL_UNCOR_MATRIX_IDX`, `TEST_MODE_DIR_NAME`) | [README.md:697](5_DAO/README.md#L697), [DAO_Constants.py:76](5_DAO/SRC/DAO_Constants.py#L76) | 문서를 읽고 설정하려는 모든 경우 | README 3.2.2부터 3.2.4를 Dynamic Partial 실제 동작으로 다시 쓰고 `TEST_MODE_DIR_NAME`을 지운다 | T3 |
| 21 | MEDIUM | 아카이브용 매트릭스 저장이 실패하면 최적화 전체가 중단된다 (`Save_Matrix`만 `OSError`를 다시 올린다) | [DAO_Main.py:2148](5_DAO/SRC/DAO_Main.py#L2148), [DAO_LLR_MATRIX.py:549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549) | 세션 디스크가 차거나 아카이브 경로 권한이 없는 상태에서 uncor 병합에 도달 | 2148줄의 `Save_LLR_Matrix` 호출을 `try/except OSError`로 감싸고 경고만 남긴 뒤 계속 진행한다 | T3 |
| 22 | MEDIUM | `tmp_partial_uncors`와 `Redecoded_uncors`를 지우는 자리가 없어 optimal 갱신마다 하위 디렉토리가 늘어난다. `_Redistribute_Uncor_Pool_Uniform`은 수정 시각이 가장 늦은 디렉토리를 고른다 | [DAO_Main.py:7501](5_DAO/SRC/DAO_Main.py#L7501), [DAO_Main.py:2109](5_DAO/SRC/DAO_Main.py#L2109) | 장시간 최적화에서 optimal이 수십 회 갱신되는 경우 | `Rebuild_Partial_Pool`이 새 디렉토리를 만든 직후 `tmp_partial_uncors` 아래에서 최신 하나만 남긴다 | T3 |
| 23 | MEDIUM | `Distribute_Uncors_To_Local_Session`이 `Delete_Uncors`를 uncor 종류 없이 불러, vector 모드에서 지난 내용을 지우지 못한 채 추가 모드로 덧붙인다 | [DAO_Main.py:1551](5_DAO/SRC/DAO_Main.py#L1551) | 풀 미준비 분기에서 `LOAD_VECTOR`로 모드를 두 번 이상 전환 (현재 설정 공간에서는 도달하지 않음) | 1551줄을 `self.Delete_Uncors(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)`로 고친다. 이 분기 전체를 지우는 쪽이 낫다 (발견 27 참조) | T3 |
| 24 | MEDIUM | `Util/check_result_files.py`의 빈 경로가 현재 디렉토리로 해석되어 존재 확인 가드가 통과하고 엉뚱한 곳을 훑는다 | [check_result_files.py:13](5_DAO/Util/check_result_files.py#L13) | 경로를 채우지 않고 실행 | 빈 문자열 검사를 앞에 두고 사용법을 출력한 뒤 끝낸다. 경로는 첫 인자로 받는다 | T3 |
| 25 | MEDIUM | `Util/rename_llr_idx.py`가 확인 절차 없이 자기가 놓인 폴더의 LLR matrix 파일 이름을 한꺼번에 바꾼다 | [rename_llr_idx.py:15](5_DAO/Util/rename_llr_idx.py#L15) | 파일을 폴더에 넣고 실행 | 증가값을 인자로 받고, 바꿀 목록을 먼저 출력한 뒤 `--apply`가 있을 때만 `os.rename`을 부른다 | T3 |
| 26 | MEDIUM | `Util/merge_uecc.py`가 결과 파일을 추가 모드로 열어 반복 실행마다 같은 내용을 덧붙인다 | [merge_uecc.py:21](5_DAO/Util/merge_uecc.py#L21) | 두 번 이상 실행 | 시작할 때 결과 파일을 `"w"`로 한 번 열고 같은 핸들에 이어 쓴다. 대상 접두사는 인자로 받는다 | T3 |

### LOW (15건)

| # | 심각도 | 문제 | 위치 | 처방 | 지적 워커 |
|---|--------|------|------|------|----------|
| 27 | LOW | `Ensure_Uncors_Loaded`의 풀 미준비 분기가 도달하지 않는데 그 안에 결함 둘(발견 18, 23)이 들어 있다 | [DAO_Main.py:7377](5_DAO/SRC/DAO_Main.py#L7377) | 7377부터 7384까지의 else 분기와 함께 죽는 함수들을 지운다 | T3 |
| 28 | LOW | `Cleanup_Session`이 `os.walk` 순회 중 하위 디렉토리를 통째로 지우면서 `dirs`를 줄이지 않는다 (`onerror=None`이라 조용히 건너뛴다) | [DAO_Main.py:996](5_DAO/SRC/DAO_Main.py#L996) | 삭제 루프를 `for dir_name in list(dirs):`로 돌리고 지운 이름을 `dirs.remove(dir_name)`으로 뺀다 | T3 |
| 29 | LOW | 지울 확장자 목록이 상수와 함수 안 지역 변수 두 벌로 갈라져 있다 | [DAO_Constants.py:128](5_DAO/SRC/DAO_Constants.py#L128), [DAO_Main.py:993](5_DAO/SRC/DAO_Main.py#L993) | `SESSION_EXTENSIONS_TO_REMOVE`를 상수로 두고 993줄에서 그것을 쓴다 | T3 |
| 30 | LOW | `Print_Test_Summary`의 모드 목록에 `INSERT_RESTART_GROUP`이 빠져 `Set_Update_Flags` 목록과 어긋나고 그 stage에서 Temp Opt 줄이 나오지 않는다 | [DAO_Main.py:7632](5_DAO/SRC/DAO_Main.py#L7632), [DAO_Main.py:8625](5_DAO/SRC/DAO_Main.py#L8625) | `DAO_Constants.py`에 `UPDATE_AT_LAST_TRIAL_MODES`를 두고 두 곳이 참조한다 | T1, T2 |
| 31 | LOW | `_Promote_Temp_Optimal_On_Stage_Exit`가 `update_mode`를 root에만 세우고 `Update_Optimal_LLR`이 하는 `target_group_indices` 정리를 하지 않는다 | [DAO_Main.py:9610](5_DAO/SRC/DAO_Main.py#L9610), [DAO_Main.py:9570](5_DAO/SRC/DAO_Main.py#L9570) | 승격 후 뒷처리를 `_Apply_Optimal_Update(new_optimal, update_mode)`로 뽑아 양쪽에서 부른다 | T2 |
| 32 | LOW | 사용자가 종료 플래그를 세워 멈출 때도 `Rebuild_Partial_Pool`이 Full 테스트를 한두 번 더 수행한다 | [DAO_Main.py:9606](5_DAO/SRC/DAO_Main.py#L9606), [DAO_Main.py:9643](5_DAO/SRC/DAO_Main.py#L9643) | `is_forced_last_trial`이 참이면 Rebuild를 건너뛴다 | T2 |
| 33 | LOW | `Update_Uncors_To_Input`이 아카이브에 함께 저장된 LLR matrix 파일까지 uncor로 취급해 입력 트리에 복사한다 | [DAO_Main.py:7877](5_DAO/SRC/DAO_Main.py#L7877) | 건너뛸 이름 검사에 현재 매트릭스 파일 이름 조건을 더한다 | T3 |
| 34 | LOW | `Mock_ECC.py`가 uncor 파일을 읽지도 쓰지도 않아 두 단계 테스트 경로를 흉내 내지 못한다 | [Mock_ECC.py:224](5_DAO/Util/Mock_ECC.py#L224) | `seed_mode`가 uncor 저장을 뜻할 때 `uncor_seed_*`와 `redecode_uncor_seed_*`에 줄을 쓰게 한다 | T3 |
| 35 | LOW | `Util/split_file.py`가 원본 폴더 아래 같은 번호 폴더의 동명 파일을 말없이 덮어쓴다 | [split_file.py:47](5_DAO/Util/split_file.py#L47) | 출력 폴더를 `{원본이름}_split/{n}/`으로 두고 이미 있으면 안내 후 끝낸다 | T3 |
| 36 | LOW | `remote_server_sync.py`가 접속에 실패하면 만들어지지 않은 폴더에 로그를 쓰려다 주기 실행 루프가 죽는다 | [remote_server_sync.py:242](5_DAO/Util/remote_server_sync.py#L242) | `write_sync_log`에서 `log_path.parent.mkdir(parents=True, exist_ok=True)`를 먼저 부른다 | T3 |
| 37 | LOW | `remote_server_sync.py`가 호스트 키를 확인 없이 받아들이고 접속 정보와 키 경로를 소스에 담는다 | [remote_server_sync.py:29](5_DAO/Util/remote_server_sync.py#L29) | `CONFIG`를 설정 파일이나 환경 변수에서 읽고 정책을 `RejectPolicy`로 바꾼다 | T3 |
| 38 | LOW | 초기화 주석이 "누적 합산"이라 적혀 있으나 실제 집계는 대입이다 | [DAO_Main.py:586](5_DAO/SRC/DAO_Main.py#L586) | 주석을 "그 시점까지의 합을 덮어쓴다"로 다시 쓴다 | T1 |
| 39 | LOW | iteration별 오류 수를 한 자리 유효숫자 FER에서 역산해 표시값이 부정확하다 | [DAO_Main.py:8250](5_DAO/SRC/DAO_Main.py#L8250) | 표시값임을 로그 머리말에 밝힌다 | T1 |
| 40 | LOW | 호출자 없는 결과 읽기 함수 둘 (`Read_FER_From_File`, `Reset_Optimal_Results`) | [DAO_Main.py:7971](5_DAO/SRC/DAO_Main.py#L7971), [DAO_Main.py:7957](5_DAO/SRC/DAO_Main.py#L7957) | 지운다 | T1 |
| 41 | LOW | 재시도 횟수 로그 문구가 실제 시도 횟수와 하나 어긋난다 | [DAO_Main.py:8271](5_DAO/SRC/DAO_Main.py#L8271) | `max_retries + 1`을 쓰거나 문구를 고친다 | T1 |

---

## ㉯ 팀 내 교차 분석

### 확정 (워커 둘 이상이 독립으로 같은 자리를 짚음)

- ㉮ **발견 11 (Partial 스킵 trial의 미측정 값이 라운드 결과에 들어감)**: T1이 P4의 집계 쪽에서,
  T2가 P6의 상태 기계 쪽에서 각각 도달했고 처방도 같다 (`Test_Trial_LLR` 반환값으로 가드).
- ㉯ **발견 6 (`avg_iterations = -1.0` 센티널)**: T1은 조기 채널 중단으로 채워진 매트릭스가
  `REORDER_GROUP` 첫 후보가 되는 입구를, T2는 Partial에서 걸러진 trial이 전 채널 FER 1.0인
  baseline과 비교되는 입구를 찾았다. 도착점은 같은 자리
  ([DAO_Main.py:2540](5_DAO/SRC/DAO_Main.py#L2540))이고, 두 입구가 모두 "테스트하지 않은
  매트릭스가 최적 후보로 남는다"는 틀린 결과를 낸다. 두 워커가 각각 MEDIUM으로 적었으나
  독립된 도달 경로가 둘이므로 **팀 판정으로 HIGH로 올린다**.
- ㉰ **발견 16 (`total_num_uncors` 덮어쓰기)**: T2와 T3가 같은 자리를 짚었고, "지금 동작에
  직접 영향은 없고 로그 의미만 어긋난다"는 판정과 "반환값으로 넘기게 한다"는 처방이 일치한다.
- ㉱ **발견 30 (모드 목록 두 벌)**: T1과 T2가 같은 자리를 짚었다.

### 반박 (Round 1 실마리나 가설이 코드 확인으로 뒤집힘)

- ㉮ **실마리 ㉳ (`TEST_MODE_DIR_NAME`에 FULL 누락)**: 영향 없음. T3가 `5_DAO/SRC` 전체에서
  이 딕셔너리를 읽는 자리가 하나도 없음을 확인했다. `KeyError`도 `.get` 기본값도 생기지 않는다.
  남는 것은 죽은 상수와 그것을 살아 있는 것처럼 설명하는 README뿐이다 (발견 20).
- ㉯ **실마리 ㉴ (`Copy_Uncors`의 `test_mode` 미사용)**: 미사용은 사실이나 실질 위험은 낮다.
  PARTIAL을 넘길 수 있는 유일한 경로인 `Ensure_Uncors_Loaded`의 풀 미준비 분기가 현재 설정
  공간에서 도달하지 않는다 (발견 27). Round 1이 짐작한 "Partial 요청에 Full 파일이 실린다"는
  사고는 지금 일어나지 않는다.
- ㉰ **가설 "강제 종료 Full 경로가 `_Run_Test_Stage`의 준비 단계를 건너뛴다"** (agent_A B6-㉡,
  agent_C B10-㉰): T2가 두 경로를 줄 단위로 대조해 현재는 세 줄이 정확히 같고 빠뜨린 준비
  단계가 없음을 확인했다. 남는 것은 중복과 `enable_early_channel_exit` 인자 차이뿐이다 (발견 17).
- ㉱ **가설 "커밋 6e035e6의 새 `matrix` 인자를 안 넘기는 호출처가 있다"**: 호출처 네 곳이 모두
  넘긴다. `Process_Uncors`의 기본값 `None`도 gather 분기로 가는 호출처가 하나뿐이고 그 호출처가
  매트릭스를 넘긴다.
- ㉲ **가설 "`src_path=None`이 `_Setup_Uncor_Pool_For_Channel`에 그대로 넘어간다"**
  (agent_B B9-㉰): 막혀 있다. `None`이 나오는 경우는 root가 아닐 때뿐이고, 그 함수는 `src_path`를
  `if self.is_root:` 안에서만 만지며 한 번 더 검사한다. 형 표기를 `Optional[Path]`로 고치면 된다.
- ㉳ **가설 "`Rebuild_Partial_Pool`이 재진입한다"** (agent_B B9-㉤): 없다. 안의 `Test_LLR`은
  `Update_Optimal_LLR`을 부르지 않고, `Update_Optimal_LLR` 호출 자리는 `Run_Initial_Test`와
  `Run_Optimization` 두 곳뿐이다.
- ㉴ **가설 "`Cleanup_Session`의 `os.walk` 중 `rmtree`가 크래시를 낸다"**: 크래시가 아니라
  조용한 건너뜀이다 (`onerror=None`). CRITICAL이 아니라 LOW다 (발견 28).

### 한 워커를 다른 워커가 보완 (개별 처방만으로는 불완전)

- ㉮ **`Rebuild_Partial_Pool`은 세 방향의 상태 오염을 한꺼번에 안고 있다.** T2가 조기 반환의
  상태 복원 누락(발견 5, HIGH)을, T1이 optimal의 Full 측정값 덮어쓰기(발견 10)를, T2와 T3가
  `total_num_uncors` 덮어쓰기(발견 16)를 각각 찾았다. 세 발견이 모두 같은 함수를 가리키므로
  처방을 따로 넣으면 서로 덮어쓴다. **합친 처방**: 함수 진입부에서 `current_seed_mode`,
  `current_test_mode`, `current_loaded_test_mode`, `total_num_uncors`,
  `optimal_LLR_matrix`의 Full 결과 필드(`FERs`, `raw_FERs`, `seed_FERs`, `num_errors`,
  `num_tests`, `avg_iterations`)를 한 묶음으로 저장하고, Step 1부터 Step 6까지를 try에 넣고,
  finally에서 그 묶음을 되돌린 뒤 root 기준 값을 bcast한다. Step 6(Partial FER 1.0 설정)은
  조기 반환 앞으로 옮긴다.
- ㉯ **T2의 "문제 없음" 판정 하나에 조건을 붙여야 한다.** T2는 "Dynamic Partial에서 Partial
  풀은 optimal이 실패한 프레임 집합이므로 optimal의 partial FER이 1.0인 것이 정의상 맞다"고
  적었다. 이 전제는 T3-1(발견 3)이 맞으면 깨진다. 외부 ECC의 `Print_Seed`가 추가 모드로 열고
  ([random.cpp:209](0_LDPC_original/src/random.cpp#L209)) 재디코딩 출력을 지우는 자리가 없으므로,
  두 번째 이후 `Rebuild_Partial_Pool`에서 풀은 "현재 optimal이 실패한 프레임"이 아니라
  "지금까지 모든 optimal이 실패한 프레임의 누적"이 된다. 판정 자체가 뒤집히지는 않으나
  (optimal의 partial FER을 1.0으로 못박으므로 trial이 Partial을 통과하기만 쉬워진다) Partial
  선별이 라운드가 갈수록 무거워지고 목적을 잃는다. T2의 판정은 "발견 3을 고친 뒤에 성립"으로
  조건을 달아야 한다.
- ㉰ **수리 순서가 중요하다 (이번 교차 분석의 핵심 산출물).** 발견 3(재디코딩 출력 누적)을
  먼저 고치면 Partial 풀이 더 이상 누적되지 않으므로, 지금은 누적에 가려져 있던 두 CRITICAL의
  트리거가 훨씬 자주 온다. 곧 풀 전체가 비는 상황(발견 2)과 한 채널만 비는 상황(발견 1)이다.
  따라서 **발견 3을 단독으로 고치면 안 되고, 발견 1과 발견 2의 수리를 먼저 또는 함께 넣는다.**
  권장 순서는 ㉠ 발견 1(채널별 건너뛰기와 채널별 0개 판정) → ㉡ 발견 2(종료 플래그를 세 자리에서
  읽기) → ㉢ 발견 5와 발견 10과 발견 16을 합친 `Rebuild_Partial_Pool` 재작성 → ㉣ 발견 3
  (재디코딩 출력 삭제) 이다.
- ㉱ **두 CRITICAL은 같은 종착지의 두 입구다.** 발견 1과 발견 2는 트리거가 다르지만
  (한 채널만 빔 대 전체가 빔) 모두 `Gather_Ref_C_Results`의 `total_tests == 0` 분기
  ([DAO_Main.py:1883](5_DAO/SRC/DAO_Main.py#L1883))에서 `MPI_Abort`로 끝난다. 로그 문구가
  "All cores failed to produce results"라서 둘 다 원인을 가린다. 수리와 별개로 이 문구에
  제외 코어 수와 uncor 보유 코어 수를 함께 적어 "결과를 만든 코어가 없음"과 "시험할 프레임이
  없음"을 구분한다.

### 이견

워커 셋이 같은 자리를 서로 다르게 판단한 곳은 없다. 심각도가 갈린 곳도 발견 6 하나뿐이고,
그것은 두 워커가 서로 다른 절반씩만 보아 각각 MEDIUM으로 적은 결과이므로 이견이 아니라
합치면 올라가는 경우다.

---

## ㉰ 미커버 영역

- ㉮ **`Run_ECC`의 재시도와 `MAX_RUN_ECC_ERRORS` (P5)**는 팀 M 소관이라 다루지 않았다. 그런데
  발견 1과 발견 2의 `total_tests=0` 경로가 `Run_ECC`의 조기 반환에 기대고 있으므로, 팀 M의
  P5 결과와 합쳐 보아야 두 CRITICAL의 재현 조건이 완전해진다.
- ㉯ **`comm.Reduce`가 타임아웃 래퍼를 거치지 않는 점** ([DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861))은
  결과 집계 경로에 있으나 통신 관점이므로 팀 M(P2, 실마리 ㉱)에 넘겼다.
- ㉰ **`_Redistribute_Uncor_Pool_Uniform`과 `Test_Core_Speed`의 제외 코어 파급 (P13)**은 팀 M
  소관이다. 발견 10(제외 코어가 바뀌면 분모가 달라짐)과 발견 22(수정 시각이 가장 늦은 디렉토리를
  고름)가 그 함수를 스치지만 전면 분석은 하지 않았다.
- ㉱ **`GEN_SINGLE_ROW` 독립 경로 (P18)의 결과 집계**는 팀 L 소관이다. T1이 그 경로의
  `max_iteration` 설정 시점만 확인했고 Top-K 저장과 stop idx 파일은 보지 않았다.
- ㉲ **docstring과 로그 문구의 규칙 위반**(줄표, 이모지, `Raises` 표기와 실제 `MPI_Abort` 불일치)은
  이 팀에서 마주친 자리만 팀 R에 넘겼고 전수 조사는 하지 않았다.
- ㉳ **실행 검증이 없다.** `Mock_ECC.py`가 uncor 파일을 읽지도 쓰지도 않아(발견 34) 두 단계
  테스트 경로를 흉내 낼 수 없다. 이 팀의 발견은 모두 코드 읽기로만 확인했고, 특히 발견 1,
  발견 2, 발견 3의 재현은 Mock에 uncor 입출력을 더한 뒤에야 실제로 해 볼 수 있다.
- ㉴ **`Util/fer_plot/fer_plot.py`의 그림 생성 로직**은 부작용이 없다는 것만 확인했고 정확성은
  보지 않았다.
