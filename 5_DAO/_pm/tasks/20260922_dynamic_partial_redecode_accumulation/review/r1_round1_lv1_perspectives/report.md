# Round 1 결과: 관점 리스트업

> 작성: 2026-09-22
> 에이전트: 2개 (fable), 도출 관점 A 23개 + B 13개 = 36개. 중복을 합쳐 4개 묶음 16개 관점으로 정리

## 도출된 관점

| # | 관점명 | 확인 항목 | 대상 파일/범위 | 원본 |
|---|--------|----------|--------------|------|
| 1 | 삭제 파일 이름과 Ref-C 기록 이름의 일치 | ch_type 1, 2, 3 서식을 글자 단위로 대조(`.2e`, 정수, `.2f`, init_n, rank). mode_init_seed가 DAO 인자 #12의 rank인지. ch_type 4와 vector(is_uncor_type_seed=False) 조합이 닿는 경로가 있는지 | Get_Uncor_File_Name, Delete_Own_Uncors, Get_Ref_C_Args, Validate_Config, ecc_top.cpp 555~572 | A1, B4 |
| 2 | 삭제 위치와 Ref-C 실행 위치 | 배치 파일의 cd 위치와 Run_ECC의 cwd가 local_session_dir인지. 삭제가 같은 폴더 바로 아래를 지우는지 | Make_Batch_File, Run_ECC, Delete_Own_Uncors, Make_Dirs | A2, B(B4) |
| 3 | 삭제 판정 seed 모드가 전 rank에서 확정된 뒤인지 | Set_Ref_C_Parameters와 Set_Seed_Mode의 bcast 순서, mode 12 보존 규칙, Step 4와 _Restore_State_After_Partial_Rebuild 복원 뒤 새 elif가 타지 않는지 | Test_LLR, Set_Seed_Mode, Test_Initial_LLR, Rebuild_Partial_Pool | A3, B8㉲ |
| 4 | 채널 축 | 채널별 E 값으로 이름이 갈리는지, 같은 파라미터 두 채널의 이름 충돌, early channel exit와 mode 12의 조합, _Fill_Untested_Channels 뒤 Gather | Test_LLR 채널 루프, _Build_Initial_Partial_Pool, Rebuild_Partial_Pool, Run_Optimization 강제 Full 구간 | A4, B5 |
| 5 | 한 채널 안의 반복 실행 | Check_Test_End가 load seed 모드에서 한 번만 돌게 하는지, 메모리 재시도(errno 12)로 Ref-C가 다시 돌 때 이어쓰기 중복, end flag 조기 탈출 rank | Test_LLR while, Check_Test_End, Run_ECC, Read_Run_ECC_End_Flag | A5, B7 |
| 6 | 삭제 실패의 대응과 가시성 | unlink 실패 시 경고만 남기고 진행하는 것이 누적 재발을 부르는지, Windows 잠금(0.5초 sleep), worker 로그 가시성, 성공 로그 부재 | Delete_Own_Uncors, Run_ECC, Write_Log_Lines | A8 |
| 7 | root의 Gather 읽기와 worker 삭제 사이의 집단 통신 | Gather 뒤 _Setup_Uncor_Pool_For_Channel의 Barrier와 bcast, 다채널 순서, Run_Initial_Test REDECODE 경로, Rebuild 뒤 다음 Rebuild까지 파일이 남는 구간의 소비자 | Gather_And_Archive_Uncors, _Setup_Uncor_Pool_For_Channel, Set_Test_Environment, Process_Uncors, Run_Initial_Test | B1, B3 |
| 8 | 제외 코어와 복귀 코어, 배분 0개 코어 | 제외 코어의 옛 파일이 Gather에 섞이지 않는지, 복귀 코어의 첫 삭제, 새로 제외된 코어의 직전 파일, has_uncor False 코어 | Delete_Own_Uncors, Run_ECC, Gather_And_Archive_Uncors, Test_Core_Speed, _Recheck_Speed_Test, _Redistribute_Uncor_Pool_Uniform | B2, B6 |
| 9 | 집단 호출 횟수의 rank 간 대칭 | 새 코드에 집단 통신이 없는지, `not is_initial`로 빠지는 Rebuild의 bcast와 Barrier가 전 rank에서 같이 빠지는지, 승격 경로 조건 불변 | Update_Optimal_LLR, _Promote_Temp_Optimal_On_Stage_Exit, Rebuild_Partial_Pool | B3, B9㉰ |
| 10 | 아카이브와 풀 배분이 이번 실행분만 반영하는지, 뒤늦은 소비자 | Gather의 dest unlink, tmp_partial copy2 덮어쓰기, 풀 파일 "w", Count 단위, _Redistribute_Uncor_Pool_Uniform의 mtime 최신 폴더 선택, Cleanup_Session의 뒷정리 | Gather_And_Archive_Uncors, _Setup_Uncor_Pool_For_Channel, Count_Gathered_Uncors, _Redistribute_Uncor_Pool_Uniform, Cleanup_Session | D2, D3, B10 |
| 11 | 초기 Rebuild 생략 뒤 상태 등가성 | Rebuild의 부수효과(optimal.FERs_partial 1.0과 bcast, current_loaded_test_mode None, current_test_mode 복원, seed 모드 복원, tmp_partial과 Redecoded_uncors 폴더, total_num_partial_uncors, pool_has_uncor[PARTIAL], 로그 줄)를 항목별로 초기 경로와 대조 | Test_Initial_LLR, _Build_Initial_Partial_Pool, Rebuild_Partial_Pool, _Restore_State_After_Partial_Rebuild, Update_Optimal_LLR, Set_Current_Optimal_Matrix, Ensure_Uncors_Loaded, Deep_Copy | A6, B1 |
| 12 | 초기 실패 uncor 0개 경로 | graceful stop 신호 뒤 Step 3, 4와 Update_Optimal_LLR까지 진행, 두 번째 Rebuild와 신호 제거, Run_Optimization의 end flag 읽기 시점, 빈 Partial 풀의 Ensure_Uncors_Loaded, rank별 집단 통신 횟수 | _Build_Initial_Partial_Pool, _Signal_Graceful_Stop_No_Partial, Update_Optimal_LLR, Run_Optimization, Load_Uncors_From_Pool | A7, B2 |
| 13 | is_initial 호출처와 mode 12 진입점 전수 | is_initial=True 호출이 Run_Initial_Test뿐인지, mode 12 진입점 세 곳 모두 새 elif를 타는지, Determine_Update_Decision의 나머지 효과(Set_Optimal_Matrix, target_group_indices, Save) 유지 | Update_Optimal_LLR, Determine_Update_Decision, Run_Initial_Test, Test_Initial_LLR, _Promote_Temp_Optimal_On_Stage_Exit | C1, B9 |
| 14 | 실행 모드별 회귀 | Two-Stage 꺼짐, HBF, SAVE_UNCOR, TEST_FER, GEN_SINGLE_ROW에서 무영향인지. REDECODE의 multi-matrix 경로에서 이전 매트릭스 redecode 파일이 지워져 Update_Uncors_To_Input 결과가 달라지는지(태스크 문서 5장 ㉱ 서술 범위) | Set_Seed_Mode, Update_Exit_After_Run_Configs, Validate_Config, Run_Multi_Matrix_Initial_Tests, _Reset_For_Next_Matrix, Update_Uncors_To_Input, Run_Single_Row_Generation | C2, C3, C4, C5, B8 |
| 15 | 시그니처 호환과 문서 정합 | Delete_Own_Uncors 호출처 전수, 키워드 기본값 호환, reference/ 미수정, docstring과 주석의 문장 규칙, README 3.2.4와 3.2.5, 태스크 문서 3장 제목("수정 2건" 대 표 3행), 검증 로그 문자열과 Count 단위 | Delete_Own_Uncors 호출처, README 3.2절, 태스크 문서 3장과 7장 | D1, E1, E2, B11, B12 |
| 16 | 대안 접근과 두 수정의 독립성 | Ref-C "w" 변경, HEADER_TO_REMOVE 추가, Gather 직후 root 삭제, Determine_Update_Decision 수정과 비교. 삭제만 있을 때와 조건만 있을 때 각각 무엇이 남는지 | Cleanup_Test_Environment, Delete_Uncors, Set_Test_Environment, Determine_Update_Decision | E3, B13 |

## 다음 단계 결정

→ Round 2 (lv1, 에이전트 4개, fable)
  사유: 변경이 3곳으로 작고 관점이 4개 축(삭제 정확성, MPI와 코어, 초기 경로 등가성, 모드별 회귀와 문서)으로 자연스럽게 묶인다. 팀 교차분석(lv2)이 필요할 만큼 넓지 않다.

| 에이전트 | 배정 관점 |
|----------|----------|
| R2-1 삭제 정확성 | 1, 2, 3, 4, 5, 6 |
| R2-2 MPI 순서와 코어, 아카이브 | 7, 8, 9, 10 |
| R2-3 초기 경로 등가성 | 11, 12, 13 |
| R2-4 모드별 회귀와 문서, 대안 | 14, 15, 16 |
