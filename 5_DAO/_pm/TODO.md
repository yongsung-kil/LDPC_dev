# TODO — 5_DAO (Project 5: Decoder Auto Optimizer)

> Claude 마지막 확인: 2026-10-21 18:05:22

> 목표: SSS에서 반입한 DAO 원형(`reference/`)을 기반으로 새 구조로 발전시킨다.

---

## 작업 목록

- [ ] uncor 하나씩 row를 쌓아 고치는 LLR matrix 탐색기 (새 DAO 방식, Decision 등급)
  - 상세: `_pm/tasks/20261021_uncor별_row누적_탐색/`
  - [x] 요구 정리, 설계 문서, 시간 측정 (2026-10-21 18:05. 후보 row 하나의 시험이 2.8초, 측정 기록: `2_LDPC_base/_test/20261021_단일프레임_복호시간/`)
  - [ ] 판정요청 2건 (새 row의 CSW 문턱 규칙, "n번 반복"의 n의 뜻)
  - [ ] 구현 계획 작성 → 2_LDPC_base에 seed 채널 함수와 seed 목록 복호 함수 추가 → `5_DAO/RowStack/` 도구 → 단일 프로세스 검사
  - [ ] 사용자 환경 MPI 실행 확인

- [ ] 집단 통신 타임아웃 메시지에 도착하지 않은 rank를 적고, ECC를 돌린 rank의 result가 없으면 멈춤
  - 상세: `_pm/tasks/20261005_barrier_timeout_and_missing_result/`
  - [x] 원인 확인과 재현 (2026-10-05 13:28, 사용자 관측 2건. 타임아웃 메시지의 rank는 기다리던 rank이고 root가 아닌 rank가 먼저 대기 상한에 닿으면 메인 로그에 줄이 남지 않음. result 파일이 없는 rank는 테스트 0회로 합산되어 rank 4개 재현에서 FER이 530/4000 대신 30/3000으로 계산됨)
  - [x] 수정과 검사 (2026-10-05 13:50, 사용자 결정: result가 없으면 멈춤. 60초 넘게 기다린 rank가 `8_End_flag/mpi_wait/`에 대기 기록을 남기고, 대기 상한에 닿은 rank가 그 기록으로 도착하지 않은 rank를 메시지에 적음. `MPI_Barrier`의 이름에 부른 함수 이름을 넣음. 테스트 종료 집계에서 ECC를 돌린 rank의 result 파일이 없거나 읽은 테스트 수가 0이면 root가 `MPI_Abort`. rank 4개 mpiexec 검사 10건 통과(수정 전 소스에서는 6건 실패), 기존 검사 163건 통과. 소스 커밋 a0d6e54. README 부록 A와 TIME_CONFIG, DAO_spec.md 6.1절 반영)
  - [x] 소스를 수정 전 내용으로 되돌림 (2026-10-05 19:51, 사용자 지시. 사용자 환경의 MPI 실행이 `Gather_result_file_problems timed out after 1200 seconds`로 중단됨. 테스트 종료 배리어를 지난 뒤 result 문제를 모으는 gather에 어떤 rank가 20분 동안 오지 않은 것. `SRC`의 세 파일은 a0d6e54 이전과 같은 내용이고, README 부록 A와 TIME_CONFIG, DAO_spec.md 6.1절에서 해당 설명을 뺌)
  - [ ] 다시 설계 (태스크 문서 7절. 먼저 중단 메시지의 `Ranks not waiting in this call` 부분으로 늦은 rank와 원인을 확인)

- [ ] HBF 최적화 모드의 dv_idx 0 TH 고정을 HBF 구간(iteration 1~4)의 row로 한정
  - 상세: `_pm/tasks/20260928_HBF_TH_iteration_range/`
  - [x] 원인 확인과 수정 (2026-09-28 17:06, 판단을 `Is_Row_In_HBF_Iterations`에 모으고 유효성 검사, 보정, 변이, row와 DV 다시 만들기가 이 함수를 씀. max_iteration 상한 검사는 없앰. 검사 9건 통과, 수정 전 소스에서는 5건 실패)
  - [x] DAO_spec.md 3.6절, 5.2절, 6.3절 반영 (2026-09-28 17:06)
  - [x] HBF 구간의 경계를 걸치는 row를 유효성 검사로 막음 (2026-09-28 17:48, HBF2 규칙. 사용자 확인: 입력과 결과 모두 경계를 걸치지 않고 HBF 구간 안은 1, 2~3, 4처럼 나눌 수 있음. 검사 11건 통과)
  - [x] 타겟 그룹을 직접 지정하는 `FIXED_TARGET_GROUP_IDX_LIST` 추가 (2026-09-28 17:48, 사용자 요청. None이면 `INITIAL_TARGET_GROUP_IDX`를 따름. 타겟 목록은 `Build_Target_Group_Indices` 한 곳에서 만들고, 값과 함께 쓰는 모드는 `Validate_Config`가 시작할 때 검사. 검사 18건 통과. DAO_spec.md 3.8절과 README 반영)
  - [x] HBF 최적화 모드의 seed 모드를 보통 모드와 같은 규칙으로 정함 (2026-09-28 20:48, 사용자 요청. `Set_Seed_Mode`의 HBF 전용 갈래와 `HBF_OPT_USING_UNCOR` 삭제. 검사 3건 통과)
  - [x] 타겟 그룹을 그룹 하나씩 다루도록 되돌림 (2026-09-29 13:26, 사용자 요청. SW 분기 그룹을 한 단위로 함께 타겟하고 함께 변이하던 처리를 없앰. 타겟 목록의 값은 그룹 하나하나의 index이고 MUTATE_MATRIX와 MUTATE_CSW는 타겟 그룹 하나만 바꿈. 새 검사 8건, 고친 검사 20건과 42건 통과. DAO_spec.md 3.7절과 3.8절, README 3.4절 반영)
  - [x] 여러 분기로 갈라진 구간에서 마지막 분기만 갱신하던 규칙을 없앰 (2026-09-29 13:38, 사용자 관측: 타겟 g2에서 "DAO updates only the last branch"로 중단. 분기 그룹은 분기 index와 상관없이 타겟이 됨. 검사 22건, 8건, 41건 통과)
  - [x] HD 복호의 HBF 구간 row에서 변이와 난수 생성이 dv_idx 0의 TH를 건드리지 않게 함 (2026-09-29 14:01, 사용자 관측: MUTATE_MATRIX가 dv_idx 0의 TH를 바꾸려 함. 원인은 제외 규칙이 `IS_HBF_OPT`에 묶여 있던 것. `Get_Columns_Fixed_In_HBF_Iterations`를 넣어 HBF 시퀀스의 모드 10, 40, 41, 60이 `IS_HBF_OPT`와 상관없이 따름. 검사 14건 통과. DAO_spec.md 3.6절 HBF3 반영)
  - [x] HBF3을 값을 쓰는 나머지 모드에도 걸음 (2026-09-29 14:12, 사용자 결정: 나머지 모드까지, 유효성 검사와 보정은 그대로. INSERT_MUTATED_ROW, INSERT_MUTATED_GROUP의 복사 값, REGEN_DV, REGEN_ROW, COPY_ROWS, COPY_GROUP은 dv_idx 0의 TH를 상수로 채우고 SWAP_ROW는 빼고 맞바꿈. `Fill_Columns_Fixed_In_HBF_Iterations` 추가. 검사 33건 통과. DAO_spec.md 3.6절 반영)
  - [x] HBF 최적화 모드에서 2단계 테스트를 쓸 수 있게 함 (2026-09-29 14:20, 사용자 결정: HBF 최적화 모드도 uncor 사용과 테스트 방식은 보통 모드와 같게. `Validate_Config`의 "Two-Stage 모드는 IS_HBF_OPT=True와 함께 사용할 수 없습니다" 검사 삭제. 검사 6건 통과. README 3.2.2절과 4.1.1절 반영)
  - [x] HBF 관련 부분 라이트 리뷰 (2026-09-29 13:39 ~ 13:58, Opus 에이전트, 대상 dff3dba..2e34036의 HBF 관련 코드와 문서, 기록: `_pm/tasks/20260928_HBF_TH_iteration_range/review/`)
    - Round 1 관점 38개를 18개로 통합, Round 2 lv1 5개. 발견 21건 (CRITICAL 0, HIGH 3, MEDIUM 3, LOW 15). 종합 판정: 수정 필요. HIGH 3건과 MEDIUM 2건은 기준 커밋의 복사본으로 재현해 확인
    - HIGH: 시작 검사에 SW 분기 모드 제한이 없어 시작을 통과한 설정이 중간 stage에서 멈춤(F1), 경계 검사가 iteration 4와 5 사이만 봄(F2), COPY_GROUP이 후보의 분기 표시를 타겟에 복사함(F3)
  - [x] 리뷰 발견 F1 F2 F6 수정 (2026-09-29 14:27, 사용자 결정. F2: row가 걸칠 수 없는 경계를 `ITERATION_SPAN_ENDS`로 두고 기본 4와 8, HBF2가 이 경계를 모두 검사. F1: `Validate_Config`가 시작할 때 시퀀스의 모든 모드에 SW 분기 제한을 검사. F6: DAO_spec.md 3.6~3.8절과 README에 HBF 최적화 모드의 사용 조건 반영. 새 검사 9건과 9건 통과, 전체 165건 통과)
  - [x] 모드 시퀀스를 이름으로 적고 쓸 수 있는 모드를 모두 담음 (2026-09-29 14:36, 사용자 요청. `Gen_LLR_Mode_SEQUENCE`는 `GenLLRMode` 17개, `Gen_LLR_Mode_HBF_SEQUENCE`는 `GenLLRModeHBF` 8개, 프리셋 세 곳은 값 그대로 이름으로. GEN_INITIAL_GROUP은 stage 1에서만 돌아 맨 앞에 둠. `Set_Gen_Trial_LLR_Mode`가 원소를 `GenLLRMode`의 멤버로 읽고 로그는 숫자로 찍음. 검사 10건 통과. README 반영)
  - [x] HBF 최적화 모드의 목록에 COPY_ROWS, REGEN_DV, REGEN_ROW를 더함 (2026-09-29 14:42, 사용자 결정: 이 셋은 넣고 REORDER_GROUP, INSERT_MUTATED_GROUP, INSERT_MUTATED_ROW, ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP은 넣지 않음. `GenLLRModeHBF`에 멤버 3개, `Gen_LLR_Mode_HBF_SEQUENCE`에 3줄 추가. 검사 12건 통과. README 4.1.1절 반영)
  - [x] 태스크 문서 3.7절에 위 결정 반영 (2026-09-29 15:03, 3.7절 표와 마지막 문단, 4절, 7절. 결정이 난 6절의 항목은 뺌)
  - [x] 리뷰 발견 F3 F4 F5 수정 (2026-09-29 15:03, 사용자 결정. F3: COPY_GROUP은 후보의 값과 CSW만 가져오고 타겟 그룹의 iteration과 SW 분기 표시는 그대로 둠. F4: 타겟 그룹의 row가 하나이면 MUTATE_CSW stage를 건너뜀. F5: GEN_SINGLE_ROW의 후보 row가 HBF 최적화 모드의 구간 경계를 걸치면 시작할 때 오류로 멈춤. 새 검사 7건과 8건 통과, 전체 192건 통과. 소스 커밋 dde34bd. DAO_spec.md 3.6절, 5.3절, 5.7절, 6.2절과 README 4.1.1절 반영)
  - [x] HBF 기본 시퀀스에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 뺌 (2026-09-29 18:07, 사용자 결정. 기본 설정값에서는 두 모드의 trial이 iteration 1~8의 그룹 뒤에서 경계 검사로 모두 버려짐. `Gen_LLR_Mode_HBF_SEQUENCE`는 9개, `GenLLRModeHBF`의 멤버 11개는 그대로. 새 검사 7건 통과, 전체 199건 통과. 소스 커밋 e128e63. README 반영, 태스크 문서 3.10절)
  - [x] 분기 그룹 타겟에 그룹 배치를 그대로 두는 모드를 허용 (2026-09-29 20:41, 사용자 관측: 타겟 [0, 1]과 INSERT_RANDOM_ROW, COPY_ROWS, REGEN_DV, REGEN_ROW, DELETE_ROW로 시작 검사가 멈춤. 사용자 설명: 제한의 까닭은 SW 분기가 아니라 디코더 실행 파일이 HBF 최적화가 다루는 구간에서 그룹 수, iteration, SW 분기의 변화를 받지 않는 것이고 row 수의 변화는 받음. 허용 모드를 `GROUP_LAYOUT_KEEPING_MODES` 10개로 모으고 분기 그룹 타겟과 타겟 목록이 함께 씀. DELETE_ROW는 그룹 배치를 그대로 두는 실행에서 row 1개짜리 그룹을 건너뛰고, SWAP_ROW는 row 1개짜리 타겟 stage를 건너뜀. 새 검사 14건 통과, 전체 213건 통과. 소스 커밋 d645567. DAO_spec.md 3.6~3.8절, 5.4절, 5.16절, 6.2절과 README 반영, 태스크 문서 3.11절)
  - [x] HBF 최적화 모드의 모드 제한을 SW 분기와 떼어 놓고 기본 시퀀스를 허용 모드 10개로 맞춤 (2026-09-29 21:16, 사용자 결정 1-1과 2-1. `IS_HBF_OPT`가 켜져 있으면 SW 분기가 있든 없든 `GROUP_LAYOUT_KEEPING_MODES` 밖의 모드를 시작할 때와 stage마다 오류로 막음 (`Check_HBF_Optimization_Mode_Allowed`). `GenLLRModeHBF`를 그 10개와 같게 맞춤 (INSERT_MUTATED_ROW, DELETE_ROW 추가. GEN_INITIAL_GROUP, INSERT_RANDOM_GROUP, SPLIT_GROUP 제거). `Gen_LLR_Mode_HBF_SEQUENCE`는 10개 모두. 새 검사 11건 통과, 전체 224건 통과. 소스 커밋 a4263bc. DAO_spec.md 3.6절 HBF4, 3.7절, 3.8절 T6과 README 반영, 태스크 문서 3.12절)
  - [x] 그룹 배치를 바꿔도 되는 실행에서 DELETE_ROW가 row 1개짜리 그룹을 그룹째 지우는 동작은 그대로 둠 (2026-09-29 21:50, 사용자 결정. 지운 매트릭스를 테스트해 좋아진 것만 가져가므로 그룹이 없어지는 것은 개선됐을 때뿐. 태스크 문서 3.11절에 기록)
  - [x] 사용자 확인: 실행 파일의 디코더가 HBF 구간에서 dv_idx 0의 TH를 읽는지와 부호의 열 차수 (2026-09-29 22:03, 리뷰 F7 F8. F7: 읽지 않음, 문서 그대로. F8: 열 차수와 dv_idx 0 칸의 대응이 맞아 정상 동작. 태스크 문서 7절에 기록)
  - [ ] 사용자 환경 MPI 실행 확인 (초기 매트릭스 검증 통과, 로그의 `[target_group_indices]` 줄이 지정한 그룹만 도는지, `[current_seed_mode]`가 LOAD_UNCOR_SEED인지, `IS_HBF_OPT`와 2단계 테스트를 함께 켰을 때 `[Initial Partial]`과 `[Partial Test Start]` 줄이 나오는지)

- [ ] Dynamic Partial의 redecode uncor 누적 수정
  - 상세: `_pm/tasks/20260922_dynamic_partial_redecode_accumulation/`
  - [x] 원인 확인과 수정 2건(코드 변경 3곳) 적용 (2026-09-22 10:06, Set_Test_Environment에서 mode 12 실행 전 redecode 파일 삭제, 초기 update의 Rebuild_Partial_Pool 생략)
  - [x] 라이트 리뷰 (2026-09-22 10:27, fable 에이전트, Round 1 관점 36개를 16개로 통합, Round 2 lv1 4개. 발견 CRITICAL 0, HIGH 0, MEDIUM 2, LOW 6. diff 결함 0건. 반영: 삭제 실패를 MPI_Abort로, 태스크 문서 3곳. 기존 결함 1건은 별도 작업 등록, LOW 3건은 기존 동작으로 기록만. 기록: `_pm/tasks/20260922_dynamic_partial_redecode_accumulation/review/`)
  - [ ] 사용자 환경 MPI 재실행으로 Partial 수가 그 회차 실패 수와 같은지 확인 (검증 방법은 태스크 문서 7장)

- [ ] graceful stop 뒤 빈 Partial 풀로 테스트가 돌아 MPI_Abort 되는 기존 결함 (Review 등급, 설계 후보 ㉮㉯ 중 사용자 결정 대기)
  - 상세: `_pm/tasks/20260922_graceful_stop_empty_partial_test/`

- [ ] SW 분기가 있는 LLR matrix 지원
  - 상세: `_pm/tasks/20260902_SW_branch_LLR_matrix/`
  - [x] 새 파일 형태 파악과 0_LDPC_original 수정 리스트업 (2026-09-02)
  - [x] 수정 리스트 문서 딥 리뷰 (기록: `_pm/tasks/20260902_SW_branch_LLR_matrix/review/`, 2026-09-02 23:52:38 ~ 2026-09-03 01:57:43)
    - Round 1 관점 17개, Round 2 lv2 4팀 발견 34건, Round 3 검증 14건(확인 11, 부분 3, 반박 0)과 재탐색 추가 8건
    - 종합 판정: 수정 필요. 사용자 결정 8건은 `review/r3_round3_lv2_verification/report.md` 끝 절
  - [ ] 리뷰 결과 반영: 사용자 결정 8건 받은 뒤 두 문서 다시 쓰기
  - [ ] 표기 방식 확정 (분기 전용 줄 추가 여부)
  - [ ] 0_LDPC_original 반영 (외부에서 수행, 피드백 반영)
  - [ ] DAO 매트릭스 모델과 유효성 규칙 확장 (DAO 쪽 설계는 `_pm/tasks/20260921_SW_branch_DAO_support/`에서 진행)

- [ ] DAO 파이썬 스크립트 가독성과 문제점 라이트 리뷰
  - 상세: `_pm/tasks/20260921_DAO_readability_review/`
  - [x] Round 1 관점 도출 (2026-09-21 15:02, 에이전트 3개, 관점 90개를 30개로 통합, 기록: `_pm/tasks/20260921_DAO_readability_review/review/r1_round1_lv1_perspectives/`)
  - [x] Round 2 분석 (2026-09-21 15:35, lv2 4팀 리더 4개와 워커 12개, 기록: `_pm/tasks/20260921_DAO_readability_review/review/r2_round2_lv2_analysis/`)
    - 문제점 129건 (CRITICAL 11, HIGH 21, MEDIUM 61, LOW 36, 팀 간 중복 정리 뒤 CRITICAL 9), 가독성 개선안 60건 (상 26, 중 29, 하 5), 8단계 적용 순서
    - 종합 판정: 수정 필요. 라이트 리뷰라 Round 3 검증은 생략, 수리 전 검증 확장 권고. 사용자 결정 4건은 `r2_round2_lv2_analysis/report.md` 끝 절
  - [x] 자명한 오류 21건 수정 (2026-09-21 18:37, CRITICAL 6: C1 C2 C3 C4 C7 C8, HIGH 13: H1 H2 H4 H5 H9 H11 H12 H16 H17 H18 H19 H20 H21, 그 밖에 Mutate_CSW 요소 수 설정 혼용과 같은 값 경계 2건. 검증은 단일 프로세스 실행 검사 20건)
    - 보류: C5 C6 C9 (설계 필요), H3 H7 H8 H10 H13 H14 H15 (설계나 검증 필요)
  - [ ] 사용자 결정 (HBF 경로 존폐는 C1 수정으로 살리는 쪽 선택, 남은 것: 매트릭스 모델 정리 4건의 선행 여부, Prime_ECC_3.0 규격, 후속 작업 갈래)
  - [ ] 결정에 따라 수리 태스크와 가독성 태스크 등록

- [ ] SW 분기 LLR matrix의 DAO 지원 (현재 수준: 읽기, 그룹 단위 변이, 모드 제한)
  - 상세: `_pm/tasks/20260921_SW_branch_DAO_support/` (Decision 등급, 미결정 5건)
  - [x] 요구 정리와 설계 문서 작성 (2026-09-21 18:39)
  - [x] 사용자 결정 5건 (2026-09-21 20:38: 구조 변경 모드 전부 금지, 헤더 10 이상만 대조, 묶음 단위 타겟, 이름 floor_flag 유지, 이 세션 구현)
  - [x] 구현과 단일 프로세스 검사 30건 통과 (2026-09-21 20:38). 구간 경계에 헤더 분기 표시 변화가 필요함을 구현 중 확인해 설계에 반영
  - [x] DAO_spec.md 3.7절과 README.md 3.4절 반영 (2026-09-21 20:38)
  - [x] 헤더 규약 확정과 반영 (2026-09-22 11:10: 1은 보통 그룹, 10은 분기 1개짜리 묶음, 20과 21은 분기 2개. 헤더와 꼬리 양방향 대조, LLR_MATRIX_2.txt 그룹 0과 1 헤더를 10으로. 검사 33건 통과)
  - [x] 모드 제한을 타겟 기준으로 좁힘 (2026-09-22 22:37: 타겟에 분기 그룹이 있을 때만 MUTATE 두 모드로 제한, 타겟이 분기 구간 뒤면 다른 모드 허용, 타겟 앞 그룹을 바꾼 trial은 버림. 검사 40건 통과)
  - [x] 변경 코드 라이트 리뷰 (2026-09-22 22:39 ~ 2026-09-22 23:14, 대상 6e035e6..15ab8e3의 SRC, 기록: `_pm/tasks/20260921_SW_branch_DAO_support/review/`)
    - Round 1 관점 16개, Round 2 lv1 4개 발견 28건 (CRITICAL 2, HIGH 2, MEDIUM 10, LOW 14). 종합 판정: 수정 필요
    - CRITICAL: 타겟 목록에서 마지막이 아닌 분기를 빼지 않아 파일 1이 기본 설정으로 첫 stage에서 중단(C1), SW 허용 검사가 stage 건너뛰기보다 먼저 돌아 GEN_INITIAL_GROUP이 stage 2 이상에서 중단(C2)
  - [ ] 리뷰 발견 수정 (C2 H1 H2 M1 M3 M4 M6 M9 M10은 작은 수정, M2 전면 재번호는 중간 규모. C1은 2026-09-29에 마지막 분기 규칙을 없애면서 함께 없어짐)
  - [x] 타겟 단위를 그룹 하나로 바꿈 (2026-09-29 13:26, 사용자 결정. 2026-09-21 결정 3번의 "묶음 단위 타겟"을 대신함. 기록은 `_pm/tasks/20260928_HBF_TH_iteration_range/` 3.3절)
  - [ ] 사용자 환경에서 MPI 실행 검증 (LLR_MATRIX_2.txt, 시퀀스 [10, 11], FIXED_TARGET_GROUP_IDX_LIST로 그룹 지정)

## 새 작업 추가

(비어 있음)

---

## 참조

- 사용 설명서와 반입 내역: `README.md`
- 원형 스냅샷: `reference/` (참조 전용, 수정 금지)
- 스펙: `DAO_spec.md`
