# TODO — 5_DAO (Project 5: Decoder Auto Optimizer)

> Claude 마지막 확인: 2026-09-22 10:27:52

> 목표: SSS에서 반입한 DAO 원형(`reference/`)을 기반으로 새 구조로 발전시킨다.

---

## 작업 목록

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

- [ ] SW 분기 LLR matrix의 DAO 지원 (현재 수준: 읽기, 묶음 변이, 모드 제한)
  - 상세: `_pm/tasks/20260921_SW_branch_DAO_support/` (Decision 등급, 미결정 5건)
  - [x] 요구 정리와 설계 문서 작성 (2026-09-21 18:39)
  - [x] 사용자 결정 5건 (2026-09-21 20:38: 구조 변경 모드 전부 금지, 헤더 10 이상만 대조, 묶음 단위 타겟, 이름 floor_flag 유지, 이 세션 구현)
  - [x] 구현과 단일 프로세스 검사 30건 통과 (2026-09-21 20:38). 구간 경계에 헤더 분기 표시 변화가 필요함을 구현 중 확인해 설계에 반영
  - [x] DAO_spec.md 3.7절과 README.md 3.4절 반영 (2026-09-21 20:38)
  - [ ] 사용자 환경에서 MPI 실행 검증 (LLR_MATRIX_2.txt, 시퀀스 [10, 11], INITIAL_TARGET_GROUP_IDX로 묶음 지정)

## 새 작업 추가

(비어 있음)

---

## 참조

- 사용 설명서와 반입 내역: `README.md`
- 원형 스냅샷: `reference/` (참조 전용, 수정 금지)
- 스펙: `DAO_spec.md`
