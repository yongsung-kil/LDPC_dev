# Round 2 분석: 에이전트 2 (MPI 순서, 코어 제외와 복귀, 아카이브와 풀 배분)

> 작성: 2026-09-22 10:24:48
> 배정 관점: Round 1 통합 관점 7, 8, 9, 10 (원본 agent_A B1, B2, B3, D2, D3와 agent_B 3, 6, 10)
> 대상: `5_DAO/SRC/DAO_Main.py` 의 수정 3곳 (Delete_Own_Uncors 인자 추가 L1530, Set_Test_Environment 의 redecode 파일 삭제 L8550~8552, Update_Optimal_LLR 의 `not is_initial` L9691)

## 읽은 범위

- ㉮ 문서: 루트 CLAUDE.md, README 3.3절(MPI 구조), 태스크 문서 전체, Round 1 report.md 와 agent_A.md, agent_B.md 의 배정 항목
- ㉯ DAO_Main.py: diff 3곳과 Cleanup_Test_Environment, Cleanup_Session, Count_Gathered_Uncors, Check_Test_End, Determine_Update_Decision, Delete_Uncors, Delete_Own_Uncors, Distribute_Uncors_To_Local_Session, Gather_Ref_C_Results, Get_Uncor_File_Name, Gather_And_Archive_Uncors, Make_Dirs, Make_Batch_File_For_Speed_Test, MPI_Barrier, Check_Barrier_Sync, Initialize_Trial, Process_Uncors, Ensure_Uncors_Loaded, _Setup_Uncor_Pool_For_Channel, Setup_Uncor_Pool, Load_Uncors_From_Pool, Run_Initial_Test, Update_Uncors_To_Input, Run_ECC, Run_Optimization, Set_Test_Environment, Set_Seed_Mode, Setup_Uncors, Set_Current_Optimal_Matrix, Test_LLR, Test_Core_Speed, Periodic_Recheck, _Recheck_Speed_Test, _Redistribute_Uncor_Pool_Uniform, Test_Initial_LLR, _Build_Initial_Partial_Pool, Rebuild_Partial_Pool, _Restore_State_After_Partial_Rebuild, _Signal_Graceful_Stop_No_Partial, Test_Trial_LLR, Update_Optimal_LLR, _Promote_Temp_Optimal_On_Stage_Exit, _Run_Exit_After_Multi_Matrix, Main, Get_Ref_C_Args 의 인자 #11 #12, 프로퍼티 is_load_seed_mode, is_load_uncor_seed_file_mode, active_cores
- ㉰ DAO_LLR_MATRIX.py 의 Deep_Copy 와 Get_LLR_Matrix_File_Name, DAO_Constants.py 의 EXTENSIONS_TO_REMOVE 와 HEADER_TO_REMOVE 와 디렉토리 이름 상수, DAO_Config.py 의 NUM_LINES_PER_UNCOR 와 SPEED_TEST_REFC_CONFIG 의 mode_seed
- ㉱ Ref-C: random.cpp 의 Print_Seed(L207~216, "a" 이어쓰기), ecc_top.cpp 의 redecode 파일 이름 조립(L560~572)과 실패 시드 기록(L928~930, mode 12 에서만 2nd_decode 파일에 기록)

## 사전 확인 사실

- ㉮ Process_N 의 redecode 파일을 읽는 코드는 `Gather_And_Archive_Uncors(is_redecoded_uncor=True)` 하나이며, 호출처는 `_Build_Initial_Partial_Pool` L9380, `Rebuild_Partial_Pool` L9467, `Process_Uncors(is_setup_stage=False)` L7377 (호출처는 `Run_Initial_Test` L7846 뿐) 세 곳이다. `_Redistribute_Uncor_Pool_Uniform` 은 `tmp_partial_uncors` 를 읽고(L9266~9270), `Update_Uncors_To_Input` 은 세션 아카이브 `5_Uncors/Redecoded_uncors` 를 읽는다(L7875~7877). Process_N 의 redecode 파일을 읽는 다른 소비자는 없다
- ㉯ redecode 파일을 만드는 것은 mode 12 의 Ref-C 뿐이다(ecc_top.cpp L928~930). 속도 테스트 배치는 `SPEED_TEST_REFC_CONFIG.mode_seed = 0` 과 고정 `mode_init_seed` 를 쓰므로(DAO_Config.py L236~237, DAO_Main.py L6510~6511) redecode 파일을 만들지 않는다
- ㉰ 파일 이름의 마지막 rank 자리에는 DAO 인자 #12 로 넘긴 `self.rank` 가 들어간다(L6461, L6484). 각 rank 가 자기 이름의 파일만 만들고 지운다
- ㉱ `Cleanup_Test_Environment` 의 삭제 규칙(확장자 .bat .sh .tmp, 머리말 result, log_CSW, Ref_C_result)에 redecode 파일은 걸리지 않으므로, Test_LLR 끝의 정리가 Gather 전에 파일을 지우지 않는다
- ㉲ `Write_Log_Lines` 는 root 만 파일에 쓰고 MPI 통신이 없다(L10037). `Delete_Own_Uncors` 는 파일 조작과 로그뿐이다

## 관점별 확인 결과 표

| # | 관점 | 확인 내용 | 결과 |
|---|------|----------|------|
| 7㉠ | root 의 Gather 읽기와 worker 삭제 사이의 집단 통신 | `_Build_Initial_Partial_Pool` 과 `Rebuild_Partial_Pool` 의 채널 루프는 채널마다 root 의 Gather(L9380, L9467) 바로 뒤에 `_Setup_Uncor_Pool_For_Channel` 을 부르고, 그 안의 `MPI_Barrier` L7494 와 bcast L7495 를 모든 rank 가 지난다. root 는 해당 채널의 모든 rank 파일을 다 읽은 뒤에야 이 Barrier 에 닿으므로 worker 는 그 전에 다음 코드로 갈 수 없다. 다음 삭제는 다음 Rebuild(또는 승격 경로) 안 Test_LLR 의 Set_Test_Environment L8552 에서 일어나며, 그 사이에 Step 5 의 Barrier L9492 와 bcast 3개, `_Restore_State_After_Partial_Rebuild` 의 bcast, Update_Optimal_LLR 의 bcast 4개, Initialize_Trial 의 Barrier 와 Check_Barrier_Sync(L2382~2383)가 더 있다 | 문제 없음 |
| 7㉡ | 다채널 순서 | 채널 k 의 Gather 는 채널 k 의 `_Setup_Uncor_Pool_For_Channel` Barrier 앞에 온다. Test_LLR 안의 채널 루프에서 Set_Test_Environment 는 채널 파라미터가 들어간 자기 채널 파일만 지우고(L2098~2102), 그 시점에 root 는 같은 Set_Test_Environment 의 Barrier L8538 에 있어 아무 파일도 읽지 않는다. Gather 는 Test_LLR 전체가 끝난 뒤(Step 4)에만 있다 | 문제 없음 |
| 7㉢ | Run_Initial_Test 의 REDECODE 경로 | REDECODE(2단계 꺼짐)에서 Test_LLR 이 mode 12 로 돌아 Set_Test_Environment 에서 삭제한 뒤 Ref-C 가 새로 쓰고, `Process_Uncors` L7846 이 root Gather 뒤 Barrier L7382 와 bcast L7383 을 지난다. `Update_Uncors_To_Input` 은 root 전용이며 세션 아카이브만 읽고(L7875~7877) Process_N 파일을 읽지 않는다. 다음 매트릭스로 갈 때 `_Reset_For_Next_Matrix` 의 Barrier(L10066)에서 worker 가 기다리므로 root 의 아카이브 읽기와 worker 의 다음 삭제가 겹치지 않는다. 2단계 켜짐에서는 Test_Initial_LLR Step 4(L9359) 가 seed 모드를 LOAD_UNCOR_SEED 로 되돌리므로 L7845 분기를 타지 않는다 | 문제 없음 |
| 7㉣ | Rebuild 뒤 다음 Rebuild 까지 파일이 남는 구간의 소비자 | 그 사이의 Partial 테스트와 trial Full 테스트, 강제 종료 Full 테스트(L8137~8140)는 seed 모드가 LOAD_UNCOR_SEED 라 redecode 파일을 읽지도 쓰지도 않는다(사전 확인 ㉮, ㉯). Periodic Recheck 는 `tmp_partial_uncors` 만 읽는다 | 문제 없음 |
| 8㉠ | 제외 코어의 옛 파일 | `Delete_Own_Uncors` L1537 은 제외 코어에서 바로 반환하고, `Run_ECC` L7966 도 반환하며, Gather L2139 는 `excluded_cores` 를 건너뛴다. `excluded_cores` 와 `is_current_core_excluded` 는 Test_Core_Speed 의 같은 bcast(L9169~9170)에서 나오므로 root 의 건너뜀 판정과 worker 의 삭제 생략 판정이 같은 값에 기반한다. 옛 파일은 남지만 읽히지 않는다 | 문제 없음 |
| 8㉡ | Periodic Recheck 로 복귀한 코어의 첫 삭제 | 복귀 뒤 `_Redistribute_Uncor_Pool_Uniform` 이 새 active 집합으로 Full 풀을 다시 만들고(L9257), 다음 Rebuild 의 Step 2 `Load_Uncors_From_Pool(FULL)` L9459 가 has_uncor 를 세운다. Test_LLR 의 Set_Test_Environment 에서 `is_current_core_excluded` 가 False 이므로 L8552 삭제가 실행되어 제외 이전의 묵은 파일이 지워진 뒤 Ref-C 가 새로 쓴다. 복귀와 다음 Rebuild 사이에 redecode 파일을 읽는 Gather 는 없다(사전 확인 ㉮) | 문제 없음 |
| 8㉢ | Recheck 에서 새로 제외된 코어의 직전 파일 | stage 시작 Recheck(L8057)와 시간 기반 Recheck(L8174~8176)는 모두 Rebuild 바깥에 있고, 그 뒤의 Gather 는 갱신된 `excluded_cores` 로 건너뛴다. 직전 Rebuild 파일은 Process_N 에 남지만 읽히지 않고, 세션 끝에 Cleanup_Session 이 디렉토리째 지운다 | 문제 없음 |
| 8㉣ | has_uncor False 로 Run_ECC 를 건너뛴 코어 | Set_Test_Environment 의 삭제(L8552)는 has_uncor 검사보다 앞에 있어 실행되고, `Run_ECC` L7971 이 반환해 새 파일이 없다. Gather L2145 는 `src_path.exists()` 가 거짓이면 건너뛰므로 없는 파일을 정상 처리한다. 수정 전에는 이 코어의 옛 파일이 그대로 Gather 에 섞였으므로 수정으로 이 경우도 함께 바로잡힌다 | 문제 없음 |
| 9㉠ | 새 코드의 집단 통신 유무 | L1530~1547 과 L8550~8552 에는 파일 조작과 root 전용 로그뿐이며 MPI 호출이 없다. 제외 코어의 조기 반환은 집단 통신을 건너뛰지 않는다 | 문제 없음 |
| 9㉡ | `not is_initial` 로 빠지는 Rebuild 의 집단 통신 대칭 | `is_initial` 은 호출처 두 곳(L7838 `True`, L8148 과 L8151 `False`)에서 모든 rank 가 같은 리터럴로 받는다. `update_mode` 는 조건문 앞 L9683 에서 bcast 된다. `ENABLE_TWO_STAGE_TEST` 는 모든 rank 가 같은 명령행 인자로 같은 프리셋을 적용한 값이다. 따라서 Rebuild 안의 Barrier 2개와 bcast 7개, `_Signal_Graceful_Stop_No_Partial` 의 Barrier L9563 이 전 rank 에서 똑같이 빠진다. Initialize_Trial 의 Check_Barrier_Sync(L2383)가 Barrier 수 불일치를 잡는 안전망도 유지된다 | 문제 없음 |
| 9㉢ | 승격 경로 조건 불변 | `_Promote_Temp_Optimal_On_Stage_Exit` L9698~9733 은 diff 에 없고, bcast 된 `promoted` 와 `ENABLE_TWO_STAGE_TEST` 로만 Rebuild 를 부른다 | 문제 없음 |
| 10㉠ | Gather 의 dest unlink 뒤 "a" 쓰기 | L2132~2133 에서 dest 를 먼저 지우고 L2136 에서 "a" 로 열므로 세션 아카이브 파일에는 이번 Gather 분만 남는다. dest 이름은 `is_redecoded_uncor=False` 와 process_idx 0 으로 만든 `uncor_seed_..._0.txt` 라 Process_0 의 `redecode_uncor_seed_..._0.txt` 와 겹치지 않는다 | 문제 없음 |
| 10㉡ | tmp_partial copy2 와 풀 파일 "w" | `shutil.copy2` (L9394, L9481)는 대상이 있으면 덮어쓴다. `_Setup_Uncor_Pool_For_Channel` 은 풀 파일을 "w" 로 연다(L7481). 배분 0개 코어(L7467 `continue`)의 직전 풀 파일은 남지만 `pool_has_uncor` 가 False 라 `Load_Uncors_From_Pool` L7560 이 has_uncor 를 False 로 두고 Run_ECC 가 건너뛴다 | 문제 없음 |
| 10㉢ | Count 단위와 로그의 N, M | `NUM_LINES_PER_UNCOR = 1` (DAO_Config.py L214), Print_Seed 는 실패 1건에 1줄을 쓴다(random.cpp L209~215). Gather 는 각 rank 파일을 `strip()` 뒤 개행을 보장해 붙이므로 내부 줄 수가 보존되고, `Count_Gathered_Uncors` 가 비지 않은 줄 수를 세어 채널별 실패 수가 된다. `[Initial Partial] ... created: N` (L9427)과 `[Rebuild_Partial_Pool] ... reconstructed: M` (L9514)은 그 채널 합이다 | 문제 없음. 부수 관찰 1건은 발견 목록 참조 |
| 10㉣ | `_Redistribute_Uncor_Pool_Uniform` 의 mtime 최신 폴더 선택과 초기 Rebuild 생략 | 폴더 이름은 `matrix.Get_LLR_Matrix_File_Name()` 즉 matrix_idx 다. optimal 은 `Deep_Copy` 에 idx 를 주지 않아(L8778, L8780) 원본 idx 를 유지하고(DAO_LLR_MATRIX.py L367), trial idx 는 Initialize_Trial L2385 에서 단조 증가하므로 Rebuild 마다 새 폴더가 생겨 최신 mtime 폴더가 현재 optimal 의 것이다. 수정 전 초기 Rebuild 는 optimal 의 idx 가 current 와 같아 `_Build_Initial_Partial_Pool` 이 만든 같은 폴더를 덮어썼을 뿐이므로, 초기 Rebuild 를 빼도 첫 optimal 갱신 전 Recheck 가 고르는 폴더(초기 매트릭스 폴더)는 같다 | 문제 없음 |
| 10㉤ | Cleanup_Session 의 뒷정리와 세션 격리 | Main 의 Barrier L10118 뒤 root 가 `Process` 로 시작하는 디렉토리를 rmtree 하므로(L1009, L1023~1025) 남은 redecode 파일과 Uncor_Pool 이 세션 끝에 지워진다. 세션 디렉토리는 root 가 bcast 한 timestamp 로 이름 짓고(L8789, L6622~6625) 비정상 종료 세션의 파일이 다음 세션과 섞이지 않는다. "실행 전 삭제"만 두는 선택은 Process_N redecode 파일의 뒤늦은 소비자가 없으므로(사전 확인 ㉮) 충분하고, 복귀 코어의 묵은 파일까지 한 자리에서 처리한다 | 문제 없음 |

## 발견 목록

### LOW 1건

- 1. `DAO_Main.py:2160` `Gather_And_Archive_Uncors` 가 Partial 재구성용 Gather 에서도 `self.total_num_uncors[ch_idx]` (Full 수용 변수)를 실패 수로 덮어쓴다. `_Build_Initial_Partial_Pool` L9406 과 `Rebuild_Partial_Pool` L9493 이 그 값을 bcast 한 뒤 `total_num_partial_uncors` 로 복사하므로 이후 `total_num_uncors` 에는 Full 수가 아니라 Partial 수가 남는다. L613 주석("Full용 total_num_uncors와 분리")과 어긋난다. 이번 diff 밖의 기존 동작이고, FER 은 Ref-C 결과 파일의 total_tests 로 계산하며(L1902) `total_num_uncors` 의 소비자는 Setup_Uncors 의 검증(L8821, Partial 구성 전)과 로그뿐이라 결과에는 영향이 없다. 처방(선택): Gather 가 값을 반환만 하고 호출처가 용도별 변수에 담도록 바꾸면 주석과 코드가 맞는다

### 다른 관점 담당에게 넘기는 메모 (심각도 없음)

- ㉮ 관점 14: REDECODE 의 multi-matrix 경로에서, 수정 전에는 두 번째 매트릭스의 Ref-C 가 첫 매트릭스의 실패 seed 가 남은 redecode 파일에 이어썼으므로 `Redecoded_uncors/{두 번째 매트릭스}/` 아카이브에 앞 매트릭스 실패분이 섞였다. 수정 후에는 Set_Test_Environment 의 삭제로 매트릭스별 실패분만 남는다. 태스크 문서 5장 ㉱의 "결과는 같다"는 단일 매트릭스에서만 성립하고 multi-matrix 에서는 결과가 달라진다(개선 방향). 문서 문구의 수정 여부는 관점 14 에서 판단한다

## 결론

관점 7~10 범위에서 CRITICAL, HIGH, MEDIUM 은 없다. LOW 1건은 diff 밖의 기존 상태 변수 정리 문제이며 결과에 영향이 없다. 수정 3곳은 집단 통신을 추가하거나 제거하지 않고, root 의 Gather 읽기와 worker 의 삭제는 채널마다 `_Setup_Uncor_Pool_For_Channel` 의 Barrier 로 분리되며, 제외 코어와 복귀 코어와 배분 0개 코어의 묵은 파일은 삭제되거나 Gather 에서 건너뛰어진다.
