# Round 2 분석: R2-3 초기 경로 등가성 (관점 11, 12, 13)

> 작성: 2026-09-22 10:23:25
> 대상: `5_DAO/SRC/DAO_Main.py` (git diff HEAD, 3곳), `5_DAO/SRC/DAO_LLR_MATRIX.py`의 Deep_Copy (변경 없음, 참조)
> 검증 대상 주장: 태스크 문서 3장 "Partial 풀의 다른 상태는 Test_Initial_LLR과 _Build_Initial_Partial_Pool이 이미 채우므로 초기 Rebuild를 빼도 빠지는 값이 없다. optimal의 FERs_partial은 Deep_Copy가 1.0으로 두거나 current의 1.0을 복사한다"

## 1. 관점별 확인 결과

| 관점 | 확인 항목 | 결과 | 근거 |
|------|----------|------|------|
| 11 | Rebuild_Partial_Pool의 부수효과가 초기 경로에서 같은 값이 되는가 | 등가 (아래 2장 표) | 2장 |
| 12 | 초기 실패 uncor 0개 경로 | 수정 자체는 등가. 다만 graceful stop 뒤 첫 Partial 테스트가 MPI_Abort로 끝나는 기존 결함이 있음 (수정과 무관, 발견 1) | 3장 |
| 13 | is_initial 호출처와 mode 12 진입점 전수 | 문제 없음 | 4장 |

## 2. 관점 11: Rebuild 부수효과 항목별 대조

Rebuild_Partial_Pool(DAO_Main.py:9432~9530)이 바꾸는 상태를 항목별로 나열하고, 수정 전 흐름(초기 Full 테스트 뒤 Rebuild 한 번 더)과 수정 후 흐름(Rebuild 생략)에서 Run_Optimization 첫 trial 진입 시점의 값을 대조했다.

| # | 상태 | 수정 전 (Rebuild 경유) | 수정 후 (Rebuild 생략) | 판정 |
|---|------|----------------------|----------------------|------|
| ㉮ | `optimal_LLR_matrix.FERs_partial` | Rebuild Step 6에서 root가 1.0 대입 뒤 bcast (9515~9521) | Test_Initial_LLR Step 3이 전 rank에서 `current.FERs_partial[ch] = 1.0` (9352). Set_Current_Optimal_Matrix가 `current.Deep_Copy(copy_partial_FER=True)` (8776)로 그대로 복사하고 Update_Optimal_LLR이 optimal을 bcast (9683) | 등가. Deep_Copy는 copy_partial_FER=True면 deepcopy 값 유지 (DAO_LLR_MATRIX.py:384~391) |
| ㉯ | `optimal_LLR_matrix`의 Full 결과 (FERs, seed_FERs, num_errors, num_tests, avg_iterations) | Rebuild의 Test_LLR(optimal)이 같은 매트릭스, 같은 Full 풀로 다시 계산해 덮어씀 | 초기 Full 테스트 값이 current에서 Deep_Copy(copy_raw_FER=True, copy_seed_FER=True)로 복사됨 | 등가. Ref-C는 seed 파일을 "rt"로만 읽고(ecc_top.cpp:615, 626) 결정적이므로 같은 값 |
| ㉰ | `current_loaded_test_mode` | _Restore_State_After_Partial_Rebuild가 None 강제 (9535) | Setup_Uncors의 Load_Uncors_From_Pool(FULL)이 둔 FULL이 잔류 (7580) | 등가. 첫 trial의 Ensure_Uncors_Loaded(PARTIAL)은 FULL != PARTIAL이므로 Load_Uncors_From_Pool(PARTIAL)을 탄다 (7406, 7415). 첫 stage가 Full 전용 모드(REORDER_GROUP 22, 2단계 프리셋의 첫 항목)이면 Ensure_Uncors_Loaded(FULL)이 재적재를 건너뛰는데, Full working copy는 mode 12 실행에서 읽기만 되고(ecc_top.cpp:615) Cleanup_Test_Environment의 삭제 규칙에도 걸리지 않으므로 내용이 같다 |
| ㉱ | `current_test_mode` | prev_test_mode(FULL) 저장 뒤 FULL로 복원 | Test_Initial_LLR이 둔 FULL 잔류 (9329) | 등가. 첫 trial의 _Run_Test_Stage가 다시 설정한다 (9301) |
| ㉲ | `current_seed_mode` | prev_seed_mode(LOAD_UNCOR_SEED) 저장 뒤 bcast로 복원 (9536~9541) | Test_Initial_LLR Step 4가 LOAD_UNCOR_SEED로 두고 bcast (9358~9363) | 등가. 값과 bcast 여부 모두 같다 |
| ㉳ | `tmp_partial_uncors/{매트릭스 이름}/` | Rebuild Step 4가 optimal 이름 폴더에 copy2로 덮어씀 | _Build_Initial_Partial_Pool이 current 이름 폴더에 copy2 (9387~9392) | 등가. optimal = current.Deep_Copy(input_matrix_idx=None)이라 matrix_idx가 같고 Get_LLR_Matrix_File_Name은 matrix_idx만 쓴다 (DAO_LLR_MATRIX.py:367~370, 395~396). 같은 폴더이며 수정 후에는 이번 실행분(914)만 담긴다. _Redistribute_Uncor_Pool_Uniform의 mtime 최신 폴더 선택(9265~9269)도 이 폴더를 고른다 |
| ㉴ | `Redecoded_uncors/{매트릭스 이름}/` 아카이브와 매트릭스 저장 | Rebuild의 Gather_And_Archive_Uncors(optimal) | _Build_Initial_Partial_Pool의 Gather_And_Archive_Uncors(current) (9378~9384) | 등가 (같은 폴더 이름, 2126~2131). dest unlink 뒤 다시 쓰므로 누적 없음 (2134~2135) |
| ㉵ | `total_num_partial_uncors`, `total_num_uncors` | Rebuild Step 5가 bcast 뒤 복사 (9492~9499) | _Build_Initial_Partial_Pool이 같은 순서로 bcast 뒤 복사 (9405~9412) | 등가. 두 함수 모두 total_num_uncors를 Partial 수로 덮어쓰는 점까지 같다 |
| ㉶ | `pool_has_uncor[PARTIAL][ch]` | Rebuild Step 4의 _Setup_Uncor_Pool_For_Channel(PARTIAL) | _Build_Initial_Partial_Pool의 _Setup_Uncor_Pool_For_Channel(PARTIAL) (9395~9400) | 등가. 각 rank의 `uncor_pool/Partial/` 파일과 bcast된 보유 여부 모두 같은 코드 (7424~7496) |
| ㉷ | `update_mode`, `is_previous_trial_updated`, `log_has_update`, `target_group_indices`, Save_LLR_Matrix | Rebuild가 건드리지 않음 | Update_Optimal_LLR 본문이 그대로 실행 | 등가 (diff는 9689~9691의 조건만 바꿈) |
| ㉸ | 로그 줄 | "[Rebuild_Partial_Pool] Starting", "Partial pool reconstructed: N"이 초기에도 한 번 찍힘 | 초기에는 "[Initial Partial] Dynamic partial pool created: N"만 찍힘 (9425~9427) | 의도된 차이. 태스크 문서 7장의 검증 절차(초기는 [Initial Partial], 이후는 [Rebuild_Partial_Pool])와 맞는다 |
| ㉹ | CSW 로그 | Rebuild의 Test_LLR은 is_test_initial=False라 enable_print_CSW_log=0 (8663~8670) | 초기 테스트만 CSW 로그 수집 | 상태 영향 없음 (로그 파일만) |

결론: 태스크 문서 3장의 등가성 주장은 성립한다. 값이 달라지는 것은 Partial 풀 크기(1828에서 914로)와 로그 줄뿐이며, 둘 다 수정 목적 그 자체다.

## 3. 관점 12: 초기 실패 uncor 0개 경로

### 3.1 수정으로 달라지는 부분 (등가 확인)

- ㉮ `_Build_Initial_Partial_Pool`이 False를 돌려주면 `_Signal_Graceful_Stop_No_Partial`이 root에서 DAO_END_FLAG를 True로 쓰고 전 rank가 MPI_Barrier를 지난다 (9345~9348, 9560~9563). has_partial은 bcast된 total_partial에서 나오므로(9418~9422) 전 rank가 같은 분기를 탄다
- ㉯ 그 뒤 Step 3(로그에 "0 fail uncors"), Step 4(seed 모드 복원 bcast), Run_Initial_Test의 결과 복사, Update_Optimal_LLR(is_initial=True)까지 진행한다. 수정 후에는 9691의 `not is_initial`로 Rebuild와 두 번째 신호가 전 rank에서 함께 빠진다. 조건의 세 항(ENABLE_TWO_STAGE_TEST는 전역 설정, is_initial은 모든 rank가 같은 인자, update_mode는 9682에서 bcast)이 모두 rank 간 동일하므로 집단 통신 횟수가 어긋나지 않는다
- ㉰ 수정 전에는 두 번째 Rebuild가 mode 12 Full 테스트를 한 번 더 돌린 뒤 total 0으로 `_Restore_State_After_Partial_Rebuild`와 두 번째 신호를 냈다. 수정 후 이 구간이 사라지고, 남는 상태는 2장 표와 같이 등가다. DAO_END_FLAG는 이미 True다

### 3.2 Run_Optimization의 end flag 읽기 시점 (기존 결함, 발견 1)

Run_Optimization은 DAO_END_FLAG를 trial 안에서 Test_Trial_LLR이 끝난 뒤에 읽는다 (8108~8118). Periodic_Recheck(stage 1은 즉시 반환, 9189), Initialize_Stage(2271), Initialize_Trial(2381), Gen_Trial_LLR 어디에도 읽기가 없다 (Read_DAO_End_Flag 호출처는 8110, 8217, 10155뿐). 따라서 graceful stop 신호 뒤에도 첫 trial의 테스트는 실행된다.

그 테스트가 Partial 테스트이면 다음 순서로 MPI_Abort에 이른다.

- 1. Test_Trial_LLR이 _Run_Test_Stage(PARTIAL) 호출 (9597)
- 2. Ensure_Uncors_Loaded(PARTIAL)이 Load_Uncors_From_Pool(PARTIAL) 호출. pool_has_uncor[PARTIAL][ch]가 전 rank에서 False라 has_uncor[ch]=False (7559~7561)
- 3. Test_LLR의 Run_ECC가 is_load_uncor_seed_file_mode이고 has_uncor False라 전 rank에서 건너뜀 (7970~7972). 결과 파일이 하나도 없음
- 4. Gather_Ref_C_Results(is_test_end=True)가 Reduce로 합산한 total_tests가 0이라 `MPI_Abort("... total_tests=0 ... All cores failed to produce results.")` (1887~1888)

Partial 테스트가 실행되는지는 그 stage의 생성 모드에 달렸다. 2단계 프리셋(DAO_Config.py:35, 61, 93)의 Gen_LLR_Mode_SEQUENCE는 [22, 10, 11, 22]라 stage 1은 REORDER_GROUP(22, MULTI_ROUND_FULL_ONLY_MODES)이고 Full 테스트만 돌아(9589~9590) 정상 종료한다. 즉 프리셋 그대로면 초기 0개 경로는 graceful stop이 되고, 발견 1은 다음 두 경우에만 닿는다.

- ㉮ 사용자가 시퀀스 첫 항목을 Partial 허용 모드(10, 11, 30, 31, 40~43, 50, 51, 60, 70, 80)로 바꾼 경우의 초기 0개 경로
- ㉯ 최적화 도중 Update_Optimal_LLR의 Rebuild가 0개를 돌려 신호를 낸 경우 (9694~9696). 신호는 그 trial의 end flag 읽기(8110) 뒤에 나므로 다음 trial의 테스트까지 실행되며, 그 stage가 Partial 허용 모드(프리셋의 stage 2, 3)이면 위 순서로 abort된다

이 결함은 수정 전에도 같았고(두 번째 신호가 있어도 flag 읽기 시점은 같다) 이번 수정이 만들거나 고친 것이 아니다. 태스크 문서 5장 ㉲의 "graceful stop 경로가 그대로 동작"은 "수정 전과 같다"는 뜻으로는 맞지만, 그 경로가 실제로 정상 종료에 이르는지는 stage 모드에 달렸다는 점을 문서가 말하지 않는다.

### 3.3 집단 통신 횟수 대칭

초기 0개 경로에서 전 rank가 지나는 집단 호출: _Build_Initial_Partial_Pool(채널마다 _Setup_Uncor_Pool_For_Channel의 Barrier와 bcast, 뒤이어 Barrier, bcast 2개), _Signal_Graceful_Stop_No_Partial(Barrier 1개), Step 4(bcast 1개), Update_Optimal_LLR(bcast 4개). 모두 rank 조건 없이 호출되고 Write_Log_Lines는 root 전용 파일 쓰기라(10037) 집단 통신이 없다. 대칭이다.

## 4. 관점 13: is_initial 호출처와 mode 12 진입점 전수

| 항목 | 확인 결과 | 근거 |
|------|----------|------|
| is_initial=True 호출처 | Run_Initial_Test 한 곳뿐 (7838). 나머지 두 호출(8148, 8151)은 is_initial=False | `Update_Optimal_LLR(` 전수 검색 |
| Determine_Update_Decision(is_initial=True) | (True, OPTIMAL_MATRIX_FROM_CURRENT)를 그대로 돌려줌 (1414~1415). 이어지는 Set_Optimal_Matrix, target_group_indices 정리, log_has_update, Save_LLR_Matrix(optimal_output_dir), "[Update optimal LLR matrix!]" 로그는 diff 바깥이라 그대로 실행 (9654~9680) | 코드 읽기 |
| mode 12 진입점 ㉮ Test_Initial_LLR (2단계) | root가 12로 강제 뒤 bcast (9331~9337), Test_LLR(is_test_initial=True) → Set_Ref_C_Parameters → Set_Seed_Mode가 12를 보존하고 bcast (8586~8588, 8631) → 채널 루프의 Set_Test_Environment 새 elif 진입 (8550~8552) | 순서 확인. 삭제 판정 시점에 전 rank의 seed 모드가 확정돼 있다 |
| mode 12 진입점 ㉯ Update_Optimal_LLR의 Rebuild | Step 1 bcast(9450~9455) 뒤 Test_LLR(optimal) (9463) → 같은 경로로 새 elif 진입 | 코드 읽기 |
| mode 12 진입점 ㉰ _Promote_Temp_Optimal_On_Stage_Exit의 Rebuild | 조건(promoted and ENABLE_TWO_STAGE_TEST, 9729~9733) 변경 없음. Rebuild 경유라 ㉯와 같다 | diff에 없음 |
| mode 12 진입점 ㉱ RunDAOMode.REDECODE | Set_Seed_Mode(is_test_initial=True)가 12 설정 (8598~8599). Test_Initial_LLR의 비2단계 분기 _Run_Test_Stage(FULL) → Test_LLR → Set_Test_Environment 새 elif 진입 (9318~9322). REDECODE와 2단계 동시 사용은 Validate_Config가 막는다 (9884~9889) | 코드 읽기 |
| Set_Test_Environment의 다른 호출처 | Run_Single_Row_Generation (10195). Set_Ref_C_Parameters(is_test_initial=False)로 seed 모드는 LOAD_UNCOR_SEED 계열이고 GEN_SINGLE_ROW와 2단계 동시 사용은 Validate_Config가 막으므로(9915~9919) 새 elif를 타지 않는다 | 호출처 전수 검색 (9044, 10195) |
| 강제 종료(is_forced_termination) Full 테스트 | 8132~8139: Ensure_Uncors_Loaded(FULL) 뒤 Test_LLR(current). Set_Seed_Mode가 12가 아닌 값(LOAD_UNCOR_SEED)을 주므로(8620~8623) 삭제도 redecode 기록도 없다. 이어지는 Update_Optimal_LLR(is_forced_last_trial=True)에서 optimal 갱신 시 Rebuild가 12로 바꿔 삭제 뒤 기록한다 | 코드 읽기 |
| 트라이얼 중 seed 모드가 12로 남을 가능성 | Rebuild는 성공과 실패 두 반환 경로 모두 _Restore_State_After_Partial_Rebuild를 지나고(9508, 9526), Test_Initial_LLR은 Step 4에서 되돌린다. Set_Seed_Mode의 "12면 보존" 규칙이 예상 밖 시점에 켜질 경로는 없다 | 코드 읽기 |
| Delete_Own_Uncors 호출처 | Set_Test_Environment 두 곳뿐 (8549, 8552). 기존 호출은 키워드 기본값 is_redecoded_uncor=False로 같은 파일을 지운다 | 전수 검색 |

## 5. 발견 목록

| # | 심각도 | 위치 | 내용 | 처방 |
|---|--------|------|------|------|
| 1 | MEDIUM (엣지케이스, 기존 결함, 이번 수정과 무관) | DAO_Main.py:8108~8118 (end flag 읽기 시점), 9597 (빈 Partial 풀로 _Run_Test_Stage(PARTIAL)), 1887~1888 (total_tests=0 abort) | graceful stop 신호(_Signal_Graceful_Stop_No_Partial) 뒤에도 다음 trial의 테스트가 실행된다. 그 stage가 Partial 허용 모드이면 빈 Partial 풀로 Test_LLR이 돌아 전 rank가 Run_ECC를 건너뛰고 Gather_Ref_C_Results가 "All cores failed to produce results"로 MPI_Abort한다. 프리셋 시퀀스 [22, 10, 11, 22]에서는 초기 0개 경로가 stage 1(REORDER_GROUP, Full 전용)에서 정상 종료하지만, 최적화 도중 Rebuild가 0개를 돌리는 경우(stage 2, 3)와 시퀀스 첫 항목을 Partial 허용 모드로 바꾼 경우에 닿는다. Print_Final_Optimal_LLR_Results, Finalize_Log, Cleanup_Session이 실행되지 않는다 | 별도 작업으로 다룬다. 방법 예: ㉮ Initialize_Trial 직후(또는 Test_Trial_LLR 앞)에 root가 DAO_END_FLAG를 읽어 bcast하고 True면 테스트 없이 break, ㉯ _Signal_Graceful_Stop_No_Partial이 멤버 플래그를 세우고 Test_Trial_LLR이 그 플래그나 sum(total_num_partial_uncors)==0이면 Partial 단계를 건너뛰도록 함. 태스크 문서 5장 ㉲에는 "정상 종료 여부는 stage 모드에 달렸다"는 범위를 적는다 |

문제 없음으로 확인한 범위: 관점 11의 부수효과 11개 항목(2장 표), 관점 12의 수정 전후 등가와 집단 통신 대칭, 관점 13의 호출처와 진입점 전수(4장 표). 이번 diff 3곳 자체에서는 결함을 찾지 못했다.
