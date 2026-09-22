# Round 2 결과: 분석

> 작성: 2026-09-22 10:27:52
> 구성: lv1, 에이전트 4개 (fable). 배정은 Round 1 report의 표를 따름
> 대상: `5_DAO/SRC/DAO_Main.py` 수정 3곳 (Delete_Own_Uncors 인자 추가, Set_Test_Environment의 redecode 파일 삭제, Update_Optimal_LLR의 `not is_initial`)

발견: 8건 (CRITICAL 0, HIGH 0, MEDIUM 2, LOW 6). 이번 diff 자체의 결함은 0건이고, MEDIUM 1건은 diff의 실패 처리 보강, 나머지는 기존 동작이나 문서 정합이다.

| # | 심각도 | 문제 | 위치 | 지적 에이전트 | 처리 |
|---|--------|------|------|--------------|------|
| 1 | MEDIUM | worker의 redecode 파일 unlink 실패가 root 전용 로그 탓에 기록 없이 지나가고, 그 rank에서 누적이 조용히 되살아난다 | Delete_Own_Uncors (DAO_Main.py 1541~1545), Write_Log_Lines (10039) | agent_1 | 반영. unlink 실패를 MPI_Abort로 멈춤 (풀 파일 쓰기 실패와 같은 정책) |
| 2 | MEDIUM (기존 결함, diff 무관) | graceful stop 신호 뒤에도 다음 trial 테스트가 실행되어, 그 stage가 Partial 허용 모드면 빈 Partial 풀로 Test_LLR이 돌아 "All cores failed to produce results"로 MPI_Abort. 프리셋 시퀀스 [22, 10, 11, 22]의 초기 0개 경로는 정상 종료 | Run_Optimization 종료 플래그 읽기 (8108~8118), Test_Trial_LLR (9597), Gather_Ref_C_Results (1887~1888) | agent_3 | 별도 작업 등록: `_pm/tasks/20260922_graceful_stop_empty_partial_test/` (설계 후보 ㉮㉯ 중 사용자 결정) |
| 3 | LOW (기존 제약) | 채널 파라미터가 같은 두 채널은 uncor 파일 이름이 겹쳐 결과가 섞인다 (입력 풀과 working copy도 같은 규칙) | Get_Uncor_File_Name (2098~2102), Validate_Config (9979~9996) | agent_1 | 기록만. 필요 시 Validate_Config에 채널 파라미터 중복 검사 추가 |
| 4 | LOW (기존 동작) | load seed 계열에서 worker가 root의 종료 플래그를 먼저 읽으면 Ref-C를 건너뛴다. Barrier 직후 읽기와 Ref-C 실행 시간 차이가 커서 실제 발생 가능성은 매우 낮음 | Test_LLR while 첫머리 (9051~9056), Check_Test_End (1072~1075) | agent_1 | 기록만 |
| 5 | LOW (기존 동작) | Gather_And_Archive_Uncors가 Partial 재구성용 Gather에서도 total_num_uncors(Full 수용 변수)를 실패 수로 덮어쓴다. FER은 Ref-C 결과의 total_tests로 계산하고 소비자는 Setup 검증과 로그뿐이라 결과 영향 없음 | Gather_And_Archive_Uncors (2160), _Build_Initial_Partial_Pool (9406), Rebuild_Partial_Pool (9493) | agent_2 | 기록만. 필요 시 Gather가 값을 반환만 하고 호출처가 용도별 변수에 담도록 정리 |
| 6 | LOW (문서) | 태스크 문서 5장 ㉱ "결과는 같다"가 REDECODE의 multi-matrix 경로에서는 개선(앞 매트릭스 실패 seed가 섞이지 않음)으로 달라짐 | 태스크 문서 39행 | agent_4, agent_2 메모 | 반영. 범위를 나눠 다시 씀 |
| 7 | LOW (문서) | "수정 2건"과 표 3행의 불일치 | 태스크 문서 4행, 20행, TODO 진행 메모 | agent_4 | 반영. "수정 2건, 코드 변경 3곳"으로 씀 |
| 8 | LOW (문서) | 7장 검증에서 N과 비교할 초기 Full 실패 수의 출처(채널별 "(seed_errors/tests): X/Y"의 X 합)를 적지 않음 | 태스크 문서 49행 | agent_4 | 반영. 출처와 합산 단위를 적고 "[Rebuild_Partial_Pool]" 줄이 초기에 없어야 함을 추가 |

### 통과 관점

- 1 삭제 파일 이름과 Ref-C 기록 이름: ch_type 1, 2, 3 서식 글자 단위 일치, mode_init_seed = rank (agent_1)
- 2 삭제 폴더와 Ref-C 실행 폴더: 배치 cd와 Run_ECC cwd가 local_session_dir (agent_1)
- 3 seed 모드 확정 시점: Set_Ref_C_Parameters의 bcast 뒤, mode 12 보존 규칙 유지, 복원 뒤 새 elif 미도달 (agent_1)
- 4 채널 축: 채널별 E 값으로 이름 분리, early channel exit와 mode 12 조합 없음 (agent_1)
- 5 한 채널 안 반복 실행: load seed 계열은 Check_Test_End가 한 번만 돌게 함. 메모리 재시도 중복은 이론상 가능하나 기존과 같은 범위 (agent_1)
- 7 root Gather 읽기와 worker 삭제: 채널마다 _Setup_Uncor_Pool_For_Channel의 Barrier로 분리 (agent_2)
- 8 제외, 복귀, 배분 0개 코어: 묵은 파일은 삭제되거나 Gather에서 건너뜀 (agent_2)
- 9 집단 호출 대칭: 새 코드에 집단 통신 없음, `not is_initial` 생략은 전 rank 대칭 (agent_2)
- 10 아카이브와 풀 배분: dest unlink, copy2 덮어쓰기, 풀 파일 "w", mtime 최신 폴더 선택 유지 (agent_2)
- 11 초기 Rebuild 생략 등가성: 부수효과 11개 항목 모두 초기 경로에서 같은 값 (agent_3)
- 12 초기 실패 0개 경로: 두 번째 Rebuild와 신호 제거, 집단 통신 대칭 (agent_3). 신호 뒤 종료는 발견 2
- 13 is_initial 호출처 1곳, mode 12 진입점 4곳 모두 새 elif 경유, Determine_Update_Decision의 나머지 효과 유지 (agent_3)
- 14 실행 모드별 회귀: Two-Stage 꺼짐, HBF, SAVE_UNCOR, TEST_FER, GEN_SINGLE_ROW 무영향. REDECODE multi-matrix는 발견 6 (agent_4)
- 15 시그니처 호환: 호출처 전수 확인, 기본값 호환, reference/ 미수정, 문장 규칙 통과, README 3.2절 정합 (agent_4)
- 16 대안 비교: Ref-C "w" 변경, HEADER_TO_REMOVE 추가, Gather 직후 root 삭제, Determine_Update_Decision 수정 모두 열세이거나 동작 불가. 두 수정은 각각 독립적으로 필요 (agent_4)

## 다음 단계 결정

→ 라이트 리뷰 종료 (트리거 "리뷰 라이트")
  사유: CRITICAL, HIGH 0건. MEDIUM 1건은 처방이 자명해 반영했고, MEDIUM 1건은 diff 밖 기존 결함이라 별도 작업으로 넘김.

### 종합 판정

커밋 가능. 수정 3곳에 결함 없음. 리뷰 반영으로 Delete_Own_Uncors의 삭제 실패를 MPI_Abort로 바꾸고 태스크 문서 3곳을 고쳤다. 남은 검증은 사용자 환경 MPI 재실행 (태스크 문서 7장).
