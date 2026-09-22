# graceful stop 뒤 빈 Partial 풀로 테스트가 돌아 MPI_Abort 되는 결함

> 작성: 2026-09-22
> 등급: Review (종료 신호를 읽는 시점을 앞당기는 로직 수정). 두 가지 방법 중 선택은 사용자 결정
> 출처: [20260922_dynamic_partial_redecode_accumulation](../20260922_dynamic_partial_redecode_accumulation/20260922_dynamic_partial_redecode_accumulation.md) 라이트 리뷰 Round 2의 Agent 3 발견 (`review/r2_round2_lv1_analysis/agent_3.md`). 그 수정과 무관한 기존 결함이라 따로 등록한다

## 1. 목적

2단계 테스트(Dynamic Partial)에서 실패 uncor가 0개가 되어 graceful stop 신호를 보낸 뒤, 다음 trial의 테스트가 실행되지 않고 바로 정상 종료(Print_Final_Optimal_LLR_Results, Finalize_Log, Cleanup_Session)로 가게 한다.

## 2. 배경 (현상)

- ㉮ `_Signal_Graceful_Stop_No_Partial`은 DAO_END_FLAG 파일만 쓰고 돌아온다. Run_Optimization은 이 플래그를 trial의 테스트가 끝난 뒤에 읽는다 (DAO_Main.py 8108~8118 부근)
- ㉯ 그래서 신호 뒤에도 다음 trial의 Test_Trial_LLR이 한 번 실행된다. 그 stage의 모드가 Partial을 허용하면 빈 Partial 풀로 Test_LLR이 돌고(9597 부근), 전 rank가 has_uncor False로 Run_ECC를 건너뛰어 Gather_Ref_C_Results가 "All cores failed to produce results"로 MPI_Abort 한다 (1887~1888 부근)
- ㉰ 닿는 경우: 최적화 도중 Rebuild_Partial_Pool이 실패 0개를 돌려줄 때(다음 stage가 Partial 허용 모드), 또는 시퀀스 첫 항목이 Partial 허용 모드인데 초기 실패가 0개일 때. 프리셋 시퀀스 [22, 10, 11, 22]의 초기 0개 경로는 stage 1이 REORDER_GROUP(Full 전용)이라 정상 종료한다

## 3. 설계 후보 (사용자 결정)

- ㉮ Initialize_Trial 직후(또는 Test_Trial_LLR 앞)에 root가 DAO_END_FLAG를 읽어 bcast하고, True면 테스트 없이 trial 루프를 빠져나간다
- ㉯ `_Signal_Graceful_Stop_No_Partial`이 멤버 플래그를 세우고, Test_Trial_LLR이 그 플래그나 `sum(total_num_partial_uncors) == 0`이면 Partial 단계를 건너뛴다

㉮가 원인(신호를 늦게 읽는 것)을 직접 고치고 파일 기반 종료 절차와도 맞는다.

## 4. 수정 대상 파일

- `SRC/DAO_Main.py` (Run_Optimization의 종료 플래그 읽기 시점, 필요하면 Test_Trial_LLR)

## 5. 안전성 체크리스트

- ㉮ 종료 플래그 읽기와 bcast는 전 rank가 같은 횟수로 지나야 한다 (집단 통신 대칭)
- ㉯ 사용자가 손으로 DAO_END_FLAG를 쓰는 기존 종료 절차의 동작이 바뀌지 않아야 한다
- ㉰ 정상 종료 경로에서 optimal 저장과 로그 마무리가 그대로 실행되어야 한다

## 6. 미결정 사항

- 설계 후보 ㉮와 ㉯ 중 선택
