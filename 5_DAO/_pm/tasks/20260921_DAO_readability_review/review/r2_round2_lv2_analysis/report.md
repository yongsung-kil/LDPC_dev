# Round 2 결과: 분석 (lv2, 4팀)

> 기록: 2026-09-21 15:35:07
> 시작 시점 커밋: 6e035e6 (`5_DAO/SRC`). 팀 리더 4개, 워커 12개, 모두 Opus.
> 팀 요약: [team_R_summary.md](team_R_summary.md), [team_M_summary.md](team_M_summary.md), [team_L_summary.md](team_L_summary.md), [team_T_summary.md](team_T_summary.md). 워커 기록 12개는 같은 폴더의 `worker_{팀}_{N}.md`.

## 집계

문제점 3팀(M, L, T)의 발견과 가독성 팀(R)의 개선안을 따로 센다.

| 갈래 | 팀 | CRITICAL | HIGH | MEDIUM | LOW | 합 |
|------|----|----------|------|--------|-----|-----|
| 문제점 | M (MPI 통신과 프로세스 수명) | 5 | 2 | 24 | 8 | 39 |
| 문제점 | L (매트릭스 모델, 생성 모드, 설정) | 4 | 13 | 19 | 13 | 49 |
| 문제점 | T (테스트 파이프라인과 결과 집계) | 2 | 6 | 18 | 15 | 41 |
| 문제점 | 합 (팀 간 중복 정리 전) | 11 | 21 | 61 | 36 | 129 |

| 갈래 | 팀 | 상 | 중 | 하 | 합 |
|------|----|----|----|----|-----|
| 가독성 개선안 | R | 26 | 29 | 5 | 60 |

팀 간 중복: CRITICAL 2건이 두 팀에서 같은 자리를 짚었다 (GEN_SINGLE_ROW 종료 플래그 rank별 읽기는 L-3과 M-02, Partial 0개 정상 종료가 MPI_Abort로 끝나는 것은 T-2와 M-03). 중복을 빼면 **CRITICAL 9건**이다. MEDIUM과 LOW의 팀 간 중복은 세지 않았다 (예: `TEST_MODE_DIR_NAME` 죽은 상수는 L과 T가 함께 지적).

## CRITICAL 9건 (프로세스 중단이나 hang)

| # | 문제 | 위치 | 처방 | 지적 팀 |
|---|------|------|------|--------|
| C1 | `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`의 다섯 값이 모두 `GenLLRMode`에 없다. HBF 최적화를 켜면 stage 1의 `GenLLRMode(selected_mode).name`에서 `ValueError`가 나고 `MPI_Abort`로 전체가 죽는다. 뜻을 담은 `GenLLRModeHBF` 열거형은 정의만 있고 읽는 자리가 없다 | [DAO_Config.py:134](5_DAO/SRC/DAO_Config.py#L134), [DAO_Constants.py:43](5_DAO/SRC/DAO_Constants.py#L43) | 시퀀스를 `GenLLRModeHBF` 멤버 값(`[40, 41, 10, 11, 60]` 꼴)으로 다시 쓰고, `Validate_Config`에 두 시퀀스의 원소가 `GenLLRMode` 값 집합에 있는지 보는 검사를 더한다. HIGH H4(HBF 보정)와 한 묶음으로 고친다 | L |
| C2 | `Initialize_Stage`가 `Set_Gen_Trial_LLR_Mode`를 먼저 부르고 `target_group_indices`를 나중에 다시 만든다. 빈 목록 검사는 앞쪽에만 있어서 직전 stage에서 그룹 수가 줄어 목록이 비면 `% len(...)`에서 `ZeroDivisionError`가 난다 | [DAO_Main.py:2263](5_DAO/SRC/DAO_Main.py#L2263), [DAO_Main.py:2280](5_DAO/SRC/DAO_Main.py#L2280) | `Set_Gen_Trial_LLR_Mode()` 호출을 목록 재설정(2274) 다음으로 옮기고, 재설정 블록 끝에 빈 목록 방어를 둔다. 옮기면 HIGH H6, H7도 함께 낫는다 | L |
| C3 | GEN_SINGLE_ROW 루프에서 각 rank가 DAO 종료 플래그 파일을 스스로 읽고 `break` 한다. 배리어 통과와 각 rank의 `open()` 사이에 사용자가 플래그 파일을 만들면 rank마다 판정이 갈려 한쪽은 Barrier, 다른 쪽은 bcast에 들어가 hang이 난다 | [DAO_Main.py:10055-10068](5_DAO/SRC/DAO_Main.py#L10055) | root만 `Read_DAO_End_Flag()`를 부르고 `_safe_bcast`로 내리는 본 루프 관용구([8071-8077](5_DAO/SRC/DAO_Main.py#L8071))로 다시 쓴다 | L, M |
| C4 | 2SD 빠른 설정 프리셋 3개(SIM_IDX 20, 21, 22)가 시작 직후 `MPI_Abort`로 죽는다. `ch_type = 3`인데 `num_fixed_errs`는 채널 2개분, `fixed_SCRs`와 `fixed_SERs`는 1개분이라 길이 검사에 걸린다 | [DAO_Config.py:65](5_DAO/SRC/DAO_Config.py#L65), [DAO_Main.py:433](5_DAO/SRC/DAO_Main.py#L433) | `Update_RefC_Configs`의 ch_type 3 분기에서 `fixed_SCRs`와 `fixed_SERs`를 `NUM_TARGET_CHANNELS` 길이로 맞춘다 (세 분기가 같은 규칙을 쓰게) | L |
| C5 | 한 채널의 uncor 풀만 비어도 그 채널에서 `total_tests=0`이 되어 MPI 작업 전체가 `MPI_Abort`로 끝난다. 빈 채널을 거르는 두 자리가 채널별이 아니라 전체 합만 본다. 최적화가 잘 될수록 쉬운 채널의 실패 프레임이 먼저 0이 되므로 성공 경로에서 만난다 | [DAO_Main.py:1883](5_DAO/SRC/DAO_Main.py#L1883), [DAO_Main.py:9341](5_DAO/SRC/DAO_Main.py#L9341), [DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426) | `Test_LLR` 채널 루프 머리에 `has_uncor[ch_idx]`가 거짓인 채널 건너뛰기를 넣고 `_Fill_Untested_Channels`와 같은 규칙으로 채운다. `Rebuild_Partial_Pool`과 `_Build_Initial_Partial_Pool`의 0개 판정을 채널별로 바꾼다 | T |
| C6 | Partial uncor 0개 정상 종료가 `MPI_Abort`로 끝난다. `_Signal_Graceful_Stop_No_Partial`은 플래그 파일만 쓰는데 trial 루프는 그 플래그를 `Test_Trial_LLR()` 뒤에서 읽고 `Main`은 `Run_Initial_Test`와 `Run_Optimization` 사이에서 읽지 않아, 빈 Partial 풀로 테스트가 한 번 더 돌아 `total_tests=0` 중단에 걸린다. 진단 문구도 "All cores failed"라 원인과 맞지 않는다 | [DAO_Main.py:9457](5_DAO/SRC/DAO_Main.py#L9457), [DAO_Main.py:8070](5_DAO/SRC/DAO_Main.py#L8070), [DAO_Main.py:10017](5_DAO/SRC/DAO_Main.py#L10017) | rank 공용 속성 `is_graceful_stop_requested`를 두고 `_Signal_Graceful_Stop_No_Partial`이 전 rank에서 True로 세운다. trial 루프의 `Initialize_Trial` 직후, stage 루프의 `Periodic_Recheck` 앞, `Main`의 두 호출 사이에서 검사해 빠져나간다. 1884의 중단 메시지에 "Partial 풀 고갈"과 "코어 실패"를 구분해 적는다 | T, M |
| C7 | 배리어 타임아웃 하한 3600초가 Ref_C 1회 실행 허용 시간 36000초(`SIM_MAX_TIME_OUT`)보다 짧다. `Test_LLR`의 while 루프 안에는 집단 통신이 없어 rank들이 다시 만나는 첫 지점이 `Gather_Ref_C_Results`의 배리어인데, 느린 코어 하나의 `Run_ECC`가 1시간을 넘기면 먼저 도착한 rank가 정상 동작 중에 job 전체를 중단시킨다. 코어 제외 문턱이 평균의 2.0배라 1.99배까지 느린 코어가 활성으로 남는다 | [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692), [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323), [DAO_Constants.py:144](5_DAO/SRC/DAO_Constants.py#L144) | `TIME_CONFIG`에 `MPI_TEST_BARRIER_TIMEOUT_SECONDS = SIM_MAX_TIME_OUT + 재시도 여유`를 새로 두고 6692의 `max(MPI_COMM_TIMEOUT_SECONDS, 3600)`을 이 값으로 바꾼다. 계산식을 설정 한 곳에 모은다 | M (세 워커 독립 확인) |
| C8 | `Test_Core_Speed`의 `comm.allgather`가 타임아웃 감시를 거치지 않는다. 바로 앞이 `Run_ECC`라 rank 사이 도달 시각 편차가 가장 큰 자리인데, 한 rank가 멈추면 전 rank가 로그 한 줄 없이 영구 대기한다. `Periodic_Recheck`도 같은 함수를 다시 부른다 | [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049) | `_safe_bcast`와 같은 모양의 `_safe_allgather`를 추가하고 이 자리를 교체한다. 타임아웃 값은 C7의 배리어 전용 값을 쓴다 | M |
| C9 | `_Redistribute_Uncor_Pool_Uniform`이 Partial 소스 디렉토리를 찾지 못하면 `pool_has_uncor[PARTIAL]`이 전 rank에서 False로 남는데, `Load_Uncors_From_Pool`은 `current_loaded_test_mode`를 PARTIAL로 세워 버려 다음 `Ensure_Uncors_Loaded`가 재로드를 건너뛴다. 모든 rank가 `Run_ECC`를 건너뛰고 `total_tests=0` 중단으로 끝난다 | [DAO_Main.py:9182](5_DAO/SRC/DAO_Main.py#L9182), [DAO_Main.py:7521](5_DAO/SRC/DAO_Main.py#L7521) | `Load_Uncors_From_Pool`이 실제로 적재한 파일이 0개면 `current_loaded_test_mode`를 세우지 않고 실패를 돌려준다. `_Redistribute_Uncor_Pool_Uniform`은 소스 부재를 발견하면 즉시 진단을 남기고 중단한다 | M |

C5, C6, C9는 입구가 다르고 종착지가 같다 ([DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884)의 `total_tests=0` 중단). 처방은 각각 따로 필요하다.

## HIGH 21건 (틀린 결과를 내지만 프로세스는 계속됨)

| # | 문제 | 위치 | 처방 | 지적 팀 |
|---|------|------|------|--------|
| H1 | `Correct_LLR_Matrix`가 `Is_LLR_Valid` 통과를 보장하지 않는다. CSW 범위(C3), 8배수(C4), 같은 값 중복(C5)을 보정하지 않아 spec 7.2와 6.3의 자동 보정 약속이 깨진다 (실측 확인) | [DAO_LLR_MATRIX.py:561](5_DAO/SRC/DAO_LLR_MATRIX.py#L561) | 585~599의 CSW 정렬 블록을 보정 블록으로 넓힌다: 클램프, `STEP_CSW` 배수 반올림, 내림차순 정렬, 같아진 항목을 한 단계 내리기 | L |
| H2 | restart 그룹의 row가 RW1~RW5, C1~C5, G3~G5를 전부 건너뛴다. 길이가 틀린 restart row도 유효로 판정된다 (실측 확인) | [DAO_LLR_MATRIX.py:333](5_DAO/SRC/DAO_LLR_MATRIX.py#L333) | restart 분기의 `continue` 앞에 restart 전용 검사(길이, `floor_flag == -1`, `CSW == -1`)를 넣고 spec 3.3에 R3~R5로 적는다 | L |
| H3 | restart 그룹 판정이 두 갈래(`restart_groups` 목록, `is_group_restart` 플래그)라 어긋날 수 있고, 어긋나면 `Correct_LLR_Matrix`가 restart row를 조용히 망가뜨린다. restart 헤더 재빌드도 목록 기준 두 곳과 플래그 기준 두 곳으로 갈려 있다 | [DAO_LLR_MATRIX.py:318](5_DAO/SRC/DAO_LLR_MATRIX.py#L318), [DAO_LLR_MATRIX.py:580](5_DAO/SRC/DAO_LLR_MATRIX.py#L580) | `_Rebuild_Restart_Header_From_Groups(matrix)` 한 메서드로 모으고 다섯 곳이 그것을 부르게 한다. 회귀 방지로 `Is_LLR_Valid`에 "목록과 플래그가 같은 그룹 집합"(G8) 검사를 더한다 | L |
| H4 | HBF 모드 보정이 dv_idx 0뿐 아니라 모든 DV의 TH를 0으로 지운다. HBF 모드에서 DV 1 이상의 TH 탐색이 매 trial 무효가 된다. 지금은 C1 때문에 드러나지 않으며 C1만 고치면 곧바로 살아난다 | [DAO_LLR_MATRIX.py:641](5_DAO/SRC/DAO_LLR_MATRIX.py#L641) | 덮어쓰기를 `HBF_immutable_col_range`가 가리키는 dv_idx 0 구간으로 한정하고 상수값을 `HBF_OPT_TH_CONSTANT_VAL`에서 읽는다. C1과 한 묶음으로 고친다 | L |
| H5 | 헤더의 `num_group`과 `num_row_each_group`을 실제 `groups`와 대조하지 않아 헤더와 본문이 어긋난 파일이 유효로 판정된다 (실측 확인) | [DAO_LLR_MATRIX.py:279](5_DAO/SRC/DAO_LLR_MATRIX.py#L279), [DAO_LLR_MATRIX.py:431](5_DAO/SRC/DAO_LLR_MATRIX.py#L431) | H2 뒤에 `num_group == len(groups)`(H6), 그룹 루프 안에 그룹별 행 수 대조(G7), restart 정합(H7)을 넣는다 | L |
| H6 | `Set_Gen_Trial_LLR_Mode`가 낡은 `target_group_indices`로 타겟 그룹과 `max_modification_trial`을 정한다 (C2와 같은 순서 문제) | [DAO_Main.py:2263](5_DAO/SRC/DAO_Main.py#L2263), [DAO_Main.py:8316](5_DAO/SRC/DAO_Main.py#L8316) | C2의 호출 순서 교체로 함께 낫는다 | L |
| H7 | INSERT_RANDOM_GROUP, INSERT_MUTATED_GROUP, SPLIT_GROUP이 `target_group_indices`를 trial마다 누적해서 바꾼다. 매트릭스는 trial마다 optimal에서 새로 복사되는데 목록은 되돌아가지 않는다 | [DAO_Main.py:2770](5_DAO/SRC/DAO_Main.py#L2770), [DAO_Main.py:3120](5_DAO/SRC/DAO_Main.py#L3120), [DAO_Main.py:3454](5_DAO/SRC/DAO_Main.py#L3454) | 세 자리의 목록 보정을 지우고, trial마다 바뀌는 목록은 후보 매트릭스에만 실어 보낸다. 영구 상태는 `Initialize_Stage` 한 곳에서만 만든다 | L |
| H8 | ADJUST_ITERATION의 `Build_Adjusted_Iteration_Matrix`가 iteration을 재배치하면서 `header.restart_iter`를 갱신하지 않는다. 저장 파일의 restart 줄이 실제 위치와 어긋나고 재읽기에서 restart 그룹이 다른 자리로 옮겨간다 | [DAO_Main.py:4604](5_DAO/SRC/DAO_Main.py#L4604), [DAO_Main.py:4701](5_DAO/SRC/DAO_Main.py#L4701) | 4727 뒤에 H3의 `_Rebuild_Restart_Header_From_Groups(matrix)`를 부른다 | L |
| H9 | REORDER_GROUP의 `max_modification_trial`이 필요한 trial 수보다 정확히 1 작다. 마지막 Round의 `Finalize_Reorder_Round`와 Final Verification이 실행되지 않는다 | [DAO_Main.py:8409](5_DAO/SRC/DAO_Main.py#L8409), [DAO_Main.py:4503](5_DAO/SRC/DAO_Main.py#L4503) | 두 자리가 같은 값을 따로 계산하므로 `Init_Reorder_Group_Mode`가 정한 값을 `Set_Gen_Trial_LLR_Mode`가 읽게 한 곳으로 모은다 | L |
| H10 | REORDER_GROUP의 iteration 등분이 restart 그룹까지 센 개수로 나눠 총 iteration이 줄어든다 | [DAO_Main.py:4918](5_DAO/SRC/DAO_Main.py#L4918), [DAO_Main.py:5015](5_DAO/SRC/DAO_Main.py#L5015) | 4918의 분모를 `len(base_donor_pool)`로 바꾸고 5015의 나머지를 마지막 그룹에 얹어 총량을 보존한다 | L |
| H11 | `Update_Configs`가 `Update_RefC_Configs`를 먼저 부르는데 그 안에서 아직 정해지지 않은 `UNCOR_CONFIG.LOAD_UNCOR_MODE`를 읽는다. `ENABLE_LOAD_VECTOR=True`여도 `LEN_NO_PS`가 0, `NUM_LINES_PER_UNCOR`가 1로 남아 uncor 벡터 한 줄을 uncor 한 개로 세고 쪼갠다 | [DAO_Main.py:475](5_DAO/SRC/DAO_Main.py#L475) | `Update_Exit_After_Run_Configs`를 `Update_RefC_Configs`보다 앞으로 옮긴다 | L (R팀 8번과 같은 자리) |
| H12 | 코어 속도 테스트가 rank마다 다른 초기 시드로 돈다. 인자 12번 자리에 `self.rank`가 들어가고 `SPEED_TEST_REFC_CONFIG.mode_init_seed`를 읽는 자리가 없다. 서로 다른 프레임을 복호한 시간을 비교하므로 정상 코어가 느린 코어로 제외될 수 있다 | [DAO_Main.py:6471](5_DAO/SRC/DAO_Main.py#L6471), [DAO_Main.py:6494](5_DAO/SRC/DAO_Main.py#L6494) | 두 자리의 `self.rank`를 `SPEED_TEST_REFC_CONFIG.mode_init_seed`로 바꾼다 | L |
| H13 | GEN_SINGLE_ROW의 `candidates` 리스트가 `LLR_MATRIX` 객체 전체를 담은 채 끝없이 자란다(기본 `NUM_GEN_TRIALS` 1,000,000). root가 메모리 고갈로 죽으면 `MPI_Abort` 없이 통신이 멎어 전체가 매달린다 | [DAO_Main.py:10027](5_DAO/SRC/DAO_Main.py#L10027) | 순위 갱신 뒤 `candidates`를 상위 `TOP_K`만 남기고 자른다. 후보 객체 대신 (FER, CSW, 행 값) 요약만 보관하고 저장 시점에만 매트릭스를 만든다 | L |
| H14 | 재디코딩 출력 `redecode_uncor_seed_*.txt`를 외부 ECC 실행 전에 지우는 자리가 없어 Partial 풀에 지난 라운드의 실패 프레임이 다시 섞인다. 외부 ECC의 `Print_Seed`가 추가 모드로 연다 | [DAO_Main.py:8469](5_DAO/SRC/DAO_Main.py#L8469), [DAO_Main.py:1515](5_DAO/SRC/DAO_Main.py#L1515) | `Delete_Own_Uncors`에 `is_redecoded_uncor` 인자를 더하고 `Set_Test_Environment` 8469의 조건을 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`까지 넓힌다. 이것을 단독으로 고치면 가려져 있던 C5, C6이 자주 발현하므로 CRITICAL 둘을 먼저 또는 함께 넣는다 | T |
| H15 | 파싱 실패로 통째로 버려진 코어의 누적 결과가 "정상 0"과 구분되지 않아 표본이 줄어든 채 FER이 계산되고, 허용 오차 없는 비교가 그 차이를 개선이나 열화로 읽어 trial 채택이 뒤집힌다 | [DAO_Main.py:8265](5_DAO/SRC/DAO_Main.py#L8265), [DAO_Main.py:1823](5_DAO/SRC/DAO_Main.py#L1823), [DAO_Main.py:2510](5_DAO/SRC/DAO_Main.py#L2510) | `Read_Ref_C_Result`가 실패를 성공과 구별되는 값으로 돌려주고, 집계가 실패 코어 수를 세어 하나라도 있으면 그 라운드 결과를 판정에서 뺀다 | T |
| H16 | `Rebuild_Partial_Pool`이 Partial 0개로 조기 반환할 때 Step 7 상태 복원을 건너뛴다. `current_seed_mode`가 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로 고착하고 `current_test_mode`, `current_loaded_test_mode`, `optimal.FERs_partial`도 복원되지 않는다 | [DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426), [DAO_Main.py:9443](5_DAO/SRC/DAO_Main.py#L9443), [DAO_Main.py:8504](5_DAO/SRC/DAO_Main.py#L8504) | 진입 시점 값을 저장해 try와 finally로 복원한다. 복원값을 상수로 고정하는 것도 저장값으로 바꾼다. Step 6을 조기 반환 앞으로 옮긴다 | T |
| H17 | 미테스트 표시값 `avg_iterations = -1.0`이 "낮을수록 좋음" 비교에서 가장 좋은 값이 되어, 테스트하지 않은 매트릭스가 round best나 temp_optimal이 된다 (두 워커가 반쪽씩 발견, 팀 판정으로 MEDIUM에서 HIGH 승격) | [DAO_Main.py:1189](5_DAO/SRC/DAO_Main.py#L1189), [DAO_Main.py:1194](5_DAO/SRC/DAO_Main.py#L1194), [DAO_Main.py:2540](5_DAO/SRC/DAO_Main.py#L2540) | `_Fill_Untested_Channels`가 `avg_iterations`에 `float("inf")`를 넣는다. `Is_Matrix_Better`가 두 번째 단계에 들어가기 전에 `num_tests`에 0이 있으면 False를 돌려준다 | T |
| H18 | `Util/remote_server_sync.py`가 원격 스캔 실패를 오류로 집계하지 않아, 비거나 반쪽인 동기화 뒤에 이전 `server_sync_*` 폴더를 되돌릴 수 없게 지운다 | [remote_server_sync.py:96](5_DAO/Util/remote_server_sync.py#L96), [remote_server_sync.py:210](5_DAO/Util/remote_server_sync.py#L210) | `_scan`의 두 except 절에서 오류 목록에 항목을 더하고, 삭제 조건에 "내려받은 파일 수 > 0"과 "감지된 원격 파일 수 > 0"을 더한다 | T |
| H19 | `Util/supercom/stop_after.sh`가 예제 Job ID(123456) 그대로 실행되면 그 번호 이상인 작업을 모두 정지시킨다 | [stop_after.sh:5](5_DAO/Util/supercom/stop_after.sh#L5) | `MIN_JOBID`를 첫 인자로 받고 값이 없으면 사용법을 출력한 뒤 끝낸다. 정지 대상 목록을 먼저 출력하고 확인을 받는다 | T |
| H20 | `Run_ECC` 종료 확인 응답(ack) 판정이 두 방향으로 틀린다. `_Report_Missing_Acks`가 동기화 배리어보다 앞에서 돌아 아직 ECC 중인 정상 rank를 미응답으로 적고, `run_ecc_ack/`를 비우는 코드가 없어 한 번 ack한 rank는 이후 어느 채널에서도 응답한 것으로 집계된다. 첫 채널 뒤로는 무조건 "이상 없음"이 된다 | [DAO_Main.py:8989](5_DAO/SRC/DAO_Main.py#L8989) | `_Report_Missing_Acks` 호출을 동기화 배리어 뒤로 옮기고, `Initialize_Run_ECC_End_Flag`에서 `run_ecc_ack/` 폴더를 비운다 | M |
| H21 | `_write_error_log`가 `capture_locals=True`로 traceback을 만들면서 지역 변수 크기를 제한하지 않는다. uncor 원본 전체를 리스트로 쥔 프레임이 둘 있어 수백 MB 로그가 나올 수 있다 | [DAO_Main.py:188](5_DAO/SRC/DAO_Main.py#L188), [DAO_Main.py:7410](5_DAO/SRC/DAO_Main.py#L7410) | `_summarize_value`와 같은 상한을 쓰도록 프레임별 지역 변수 요약을 거쳐 기록한다 | M |

## MEDIUM 61건, LOW 36건

목록과 처방은 각 팀 요약의 MEDIUM, LOW 절과 워커 문서에 있다. 눈에 띄는 것만 적는다.

- ㉮ **Decision 등급 1건** (L, MEDIUM): 새 입력 `Input/Ref_C/Prime_ECC_3.0`의 매트릭스가 현재 유효성 규칙 RW2(`floor_flag == -1`)와 G2(그룹 iteration 연속)를 위반해 로드되지 않는다. SW 분기 세션과 규격을 맞춰야 한다
- ㉯ CSW 같은 값 허용 여부: 코드의 엄격 감소가 정본이다. 삽입 경로가 엄격 감소를 강제하고 같은 CSW는 뒤 row를 고를 수 없게 만든다. 고칠 자리는 spec 3.5 문구와 `Mutate_CSW`의 두 줄(7167, 7173)이다 (L)
- ㉰ `Initialize_Stage`의 `current_target_idx`와 restart 건너뛰기 루프가 실제 타겟 선택에 영향을 주지 않는다. 실제 타겟은 `Set_Gen_Trial_LLR_Mode` 8322~8323의 `current_target_group_idx`이고 건너뛰기는 8337~8343이 따로 한다 (L). R팀 12번(이름 변경)과 같은 자리
- ㉱ 타임아웃 없는 집단 통신 3곳은 자리별로 위험이 다르다: 9049 CRITICAL(C8), 7011 MEDIUM, 1861 LOW(앞에 배리어가 있음) (M)
- ㉲ MPI 스레드 지원 수준: 로컬(MS MPI 10.1, mpi4py 4.1.1)에서는 MULTIPLE을 실측했으나 실행 클러스터는 확인 불가. 시작 시 점검 한 줄을 넣는다 (M)
- ㉳ `MPI_Abort`가 `NoReturn`으로 표기되었으나 복귀할 수 있고, 복귀하면 깨지는 호출부 두 곳(7988, 6966)이 있다 (M)

## 반박된 Round 1 실마리와 통과 관점

| 실마리 | 판정 | 근거 |
|--------|------|------|
| ㉶ `Set_CSW_Update_Limit` 미호출 | 반박 | 3785에서 7098을 거쳐 8285로 이어지는 호출 사슬이 있다. 실제 위험은 `CSW_UPDATE_LIMIT_VALUE`의 조건부 정의(MEDIUM)로 좁혀진다. 호출 사슬 가운데 `Mutate_Matrix_Setup`(7097)은 한 줄짜리 껍데기다 (R팀 14번) |
| ㉳ `TEST_MODE_DIR_NAME` FULL 누락 | 반박 | 이 상수를 읽는 자리가 없는 죽은 상수다 (L, T 동일 판정) |
| ㉴ `Copy_Uncors`의 `test_mode` 미사용 | 하향 | 도달 불가 분기라 동작 영향 없음 (T) |
| ㉵ `current_target_idx` 생성 순서로 `AttributeError` | 반박 | `Init_Reorder_Group_Mode`는 속성 생성보다 뒤에서만 불린다. 대신 그 값이 타겟 선택에 쓰이지 않는 더 큰 문제가 있다 (L) |
| ㉷ `HBF_OPT_CONFIG.__init__` 부수효과 | 범위 축소 | 인스턴스를 만드는 자리가 없어 `__init__`이 돌지 않는다. `IS_HBF_OPT`는 기본값 False와 `Update_RefC_Configs`의 하향 조정으로만 정해진다. `CONFIGS` 누락은 확인되었으나 소비처가 로그 하나뿐이라 MEDIUM (L, R 동일 판정) |
| ㉰ CSW 같은 값 금지 대 spec C5 | 코드가 정본 | 위 MEDIUM ㉯ |
| ㉱ Reduce와 allgather 타임아웃 미적용 | 사실, 자리별 심각도 상이 | 위 MEDIUM ㉱ |
| ㉲ 타임아웃 값 1200초 대 3600초 | 사실이며 실마리보다 무거움 | 두 값 모두 `SIM_MAX_TIME_OUT` 36000초보다 훨씬 작다 (C7) |
| ㉮ README 이름과 링크 | 사실이며 확장 | 링크 34개 중 33개가 없는 경로, 이름 20건과 값 14건 어긋남 (R팀 20, 21번) |
| ㉸ `ReorderState` docstring 허깨비 필드 | 사실 | R팀 16번 |
| ㉹ docstring과 실제 동작 불일치 | 사실이며 확장 | `Raises:` 절 17곳 전수가 거짓 (R팀 15번), Args 절 8곳 불일치 (17번) |
| ㉺ 줄표, 이모지, U+FFFD | 사실 | 줄표 22곳, 가운뎃점 4개, U+FFFD 3개, 이모지 12줄 (R팀 18번) |
| ㉻ Util 하드코딩 | 부분 사실 | `check_result_files.py`는 빈 경로로 언제나 실패 (R팀 24번). `remote_server_sync.py`의 접속 정보는 자리표시자이고 실제 위험은 빈 동기화 뒤 폴더 삭제(H18) |

통과한 관점 (문제 미발견, 확인 범위):
- ㉮ P1 가운데 "root 전용 블록 안의 집단 통신": `if self.is_root:` 블록 약 95곳 전수 스캔과 AST 전수 검사 모두 없음 (M)
- ㉯ P1 가운데 "`Test_LLR` while 루프 안의 집단 통신": 없음. 반복 횟수가 rank마다 달라도 짝은 깨지지 않으며 그 차이를 흡수해야 할 것이 C7의 배리어 타임아웃이다 (M)
- ㉰ P3 종료 신호 파일: 세션 디렉토리 아래라 세션 사이 오염 없음, 플래그 초기화는 배리어 사이에 제대로 놓임, 숫자 카운트 파일의 비정상 내용은 0으로 안전 처리 (M)
- ㉱ P16 난수: rank별 시드가 겹치지 않고(간격 10000), 매트릭스 생성은 전부 root 블록 안이라 worker의 난수 사용으로 매트릭스가 갈리지 않음 (M)
- ㉲ P14 `except Exception` 약 20곳: 삼킨 뒤 상태가 깨지는 곳 없음. 로그 회전 재진입은 1회로 끝남 (M)
- ㉳ `excluded_cores`와 `is_current_core_excluded`가 다르게 정해진다는 Round 1 관찰: 사실 아님, 9087~9088에서 함께 정해짐 (M)

## 가독성 개선 처방 (팀 R, 60건)

우선순위 상 26건의 머리: `floor_flag` 규칙 함수화(옆 세션 SW 분기 작업과 정면으로 맞닿는 자리), row 꼬리 칸 이름화, 헤더 도우미 3개, 인프라 10개 군 파일 분리(3,762줄), 모드 정보 표 하나로 모으기(모드 추가 시 손대는 자리 15곳을 5곳으로), `Raises:` 절 17곳 전수 거짓, 문서 링크 34개 중 33개 깨짐. 전체 목록은 [team_R_summary.md](team_R_summary.md) ㉮ 절.

워커 간 처방 충돌 5건은 리더가 판정했다 (헤더 재구성 함수는 `LLR_MATRIX.Rebuild_Header_Group_Arrays`, 멀티라운드 공통 상태는 `Round_Based_Mode_State`, 모드 표는 `GEN_LLR_MODE_SPECS` 하나에 `MODE_CONFIG_CLASS`를 열로 넣기 등).

**8단계 적용 순서** (요지, 상세는 team_R_summary.md ㉱ 절):

| 단계 | 하는 일 | 비고 |
|------|--------|------|
| 0 | 회귀 확인 수단 만들기: `Util/Mock_ECC.py`로 매트릭스 하나를 돌려 출력 파일을 저장하고 각 단계 뒤 대조 | 시험 코드가 0개라 "동작 변경 없음" 처방 40여 개를 확인할 방법이 지금 없다 |
| 1 | 동작 결함 2건 판정 (H11 `Update_Configs` 순서, HBF 경로를 살릴지 지울지) | 뒤 단계의 전제 |
| 2 | 코드 안 문구와 이름 정리 (docstring, `Raises:` 절, 줄표와 이모지, 과거 서술 주석, 매직 넘버, 껍데기 함수, 이름) | 위험 0, 분할 전에 해야 뒤의 diff가 "옮기기"만 담는다 |
| 3 | 매트릭스 모델 정리 4건 (`floor_flag` 규칙 함수화, row 꼬리 이름화, 출력 도우미, 헤더 도우미) | **옆 세션 SW 분기 작업 전에** 넣어야 그쪽이 고칠 자리가 row 29곳에서 약 10곳, header 22곳에서 약 12곳으로 준다. 늦으면 이득이 사라진다 |
| 4 | 인프라 10개 군 파일 분리 (LOG, FLAG, CSWLOG, MPI, PATH, ECC+SPEED, RESULT, UNCOR, PRINT, SINGLEROW) | 충돌 위험 없음. 메서드 이름 212개가 전부 고유해 `self` 그대로 옮긴다. `DAO_Main.py`가 6,600줄대가 된다 |
| 5 | 긴 함수와 반복 관용구 정리 (300줄 넘는 함수 2개 분할, Partial/Full 쌍둥이 접근자, root 판단 뒤 bcast 도우미) | 4단계 뒤에 하면 diff가 한 파일 안에 담긴다. bcast 도우미는 M팀 결론(root 블록 안 통신 없음)과 어긋나지 않는다 |
| 6 | 모드 정보 표 하나로 모으기 | 1단계의 HBF 판정이 필요 |
| 7 | 옆 세션 완료 후: 생성 모드 군 분리와 멀티라운드 상태 객체화 | 옆 세션이 고치는 파일과 정면으로 겹친다. 끝나면 `DAO_Main.py`가 약 2,200줄 |
| 8 | 문서 마무리 (README 링크 33개, 이름 20건과 값 14건, `Util/README.md` 신설, Util 4개 스크립트 사용법) | 파일 경로가 다 정해진 뒤 한 번에 |

## 팀 간 연계

- ㉮ **HBF 경로**: C1(시퀀스 값)과 H4(HBF 보정)는 한 묶음이다. R팀 6번(모드 표)과 미사용 상수 처리는 HBF 경로를 살릴지 지울지 정해야 확정된다
- ㉯ **`Update_Configs` 순서**: H11(L)과 R팀 8번이 같은 자리다. 결함 수리로 먼저 처리한다
- ㉰ **`total_tests=0` 종착지**: C5(T), C6(T, M), C9(M)가 같은 중단 지점으로 간다. 진단 메시지 구분(C6 처방)을 함께 넣는다
- ㉱ **restart 헤더 재빌드**: H3(L)의 `_Rebuild_Restart_Header_From_Groups`와 R팀 4번(헤더 도우미 3개)이 같은 방향이다. 하나로 설계한다
- ㉲ **수리 순서 제약**: `max_iteration`을 `__init__`에서 초기화하기 전에 REORDER와 ADJUST 두 모드에 명시 대입을 먼저 넣는다 (두 모드가 `Is_LLR_Valid`의 부수 대입에 의존). H14를 단독으로 고치면 C5, C6이 자주 발현하므로 CRITICAL 둘을 먼저 넣는다

## 미커버 영역 (다음 리뷰 후보)

- ㉮ 값만 바꾸고 헤더를 건드리지 않는 모드(`Mutate_Matrix`, `Regen_DV`, `Regen_Row`, `Swap_Row`, `Copy_Rows`)가 값 범위 규칙을 지키는지 (L)
- ㉯ `Get_Ref_C_Args`와 `Get_Ref_C_Args_For_Speed_Test`의 인자 순서 전수 대조 (L)
- ㉰ 멀티라운드 상태 dataclass의 rank 사이 bcast 정합 (L, M 경계)
- ㉱ 회귀 시험 수단 부재, `Util/` 8개 스크립트 내부 구조, 로그를 파싱하는 외부 도구 유무, 분할 뒤 import 그래프 (R)
- ㉲ 팀 M과 T의 미커버 절은 각 요약 문서 ㉰ 절

## 종합 판정

**수정 필요.** CRITICAL 9건 가운데 C5(한 채널 uncor 고갈), C7(배리어 타임아웃이 ECC 상한보다 짧음)은 정상 최적화 경로에서 만나는 중단이다. C1과 C4는 특정 설정(HBF, SIM_IDX 20~22)을 켜면 시작 직후 죽는다. 나머지 다섯은 종료 신호나 풀 재분배의 경쟁 조건과 엣지케이스다.

라이트 리뷰이므로 Round 3(검증)은 하지 않았다. CRITICAL과 HIGH 30건은 팀 리더의 교차 분석과 일부 실측(팀 L의 `python -c` 실행, 팀 M의 AST 전수 검사)을 거쳤으나 독립 검증 라운드는 거치지 않았다. 수리에 들어가기 전에 Round 3 검증(딥 리뷰 확장)을 권한다.

## 사용자 결정 항목

- 1. HBF(Hybrid Bit Flipping) 최적화 경로를 살릴지 지울지 (C1, H4, R팀 6번의 전제)
- 2. 매트릭스 모델 정리 4건(R팀 3단계)을 옆 세션의 SW 분기 작업 **전에** 넣을지. 넣으려면 옆 세션과 순서 협의가 필요하다
- 3. 새 입력 `Prime_ECC_3.0` 매트릭스가 현재 규칙 RW2, G2를 위반하는 것을 어느 쪽에서 맞출지 (Decision 등급, 옆 세션 몫)
- 4. 이 리뷰 결과를 어떤 작업으로 옮길지: ㉮ CRITICAL 9건과 HIGH 21건 수리 태스크, ㉯ 가독성 8단계 태스크(0단계 회귀 수단 포함), ㉰ 수리 전 Round 3 검증 확장
