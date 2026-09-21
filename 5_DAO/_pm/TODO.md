# TODO — 5_DAO (Project 5: Decoder Auto Optimizer)

> Claude 마지막 확인: 2026-09-21 14:45:59

> 목표: SSS에서 반입한 DAO 원형(`reference/`)을 기반으로 새 구조로 발전시킨다.

---

## 작업 목록

- [ ] SW 분기가 있는 LLR matrix 지원
  - 상세: `_pm/tasks/20260902_SW_branch_LLR_matrix/`
  - [x] 새 파일 형태 파악과 0_LDPC_original 수정 리스트업 (2026-09-02)
  - [x] 수정 리스트 문서 딥 리뷰 (기록: `_pm/tasks/20260902_SW_branch_LLR_matrix/review/`, 2026-09-02 23:52:38 ~ 2026-09-03 01:57:43)
    - Round 1 관점 17개, Round 2 lv2 4팀 발견 34건, Round 3 검증 14건(확인 11, 부분 3, 반박 0)과 재탐색 추가 8건
    - 종합 판정: 수정 필요. 사용자 결정 8건은 `review/r3_round3_lv2_verification/report.md` 끝 절
  - [ ] 리뷰 결과 반영: 사용자 결정 8건 받은 뒤 두 문서 다시 쓰기
  - [ ] 표기 방식 확정 (분기 전용 줄 추가 여부)
  - [ ] 0_LDPC_original 반영 (외부에서 수행, 피드백 반영)
  - [ ] DAO 매트릭스 모델과 유효성 규칙 확장

- [ ] DAO 파이썬 스크립트 가독성과 문제점 라이트 리뷰
  - 상세: `_pm/tasks/20260921_DAO_readability_review/`
  - [x] Round 1 관점 도출 (2026-09-21 15:02, 에이전트 3개, 관점 90개를 30개로 통합, 기록: `_pm/tasks/20260921_DAO_readability_review/review/r1_round1_lv1_perspectives/`)
  - [x] Round 2 분석 (2026-09-21 15:35, lv2 4팀 리더 4개와 워커 12개, 기록: `_pm/tasks/20260921_DAO_readability_review/review/r2_round2_lv2_analysis/`)
    - 문제점 129건 (CRITICAL 11, HIGH 21, MEDIUM 61, LOW 36, 팀 간 중복 정리 뒤 CRITICAL 9), 가독성 개선안 60건 (상 26, 중 29, 하 5), 8단계 적용 순서
    - 종합 판정: 수정 필요. 라이트 리뷰라 Round 3 검증은 생략, 수리 전 검증 확장 권고. 사용자 결정 4건은 `r2_round2_lv2_analysis/report.md` 끝 절
  - [ ] 사용자 결정 4건 (HBF 경로 존폐, 매트릭스 모델 정리 4건의 선행 여부, Prime_ECC_3.0 규격, 후속 작업 갈래)
  - [ ] 결정에 따라 수리 태스크와 가독성 태스크 등록

## 새 작업 추가

(비어 있음)

---

## 참조

- 사용 설명서와 반입 내역: `README.md`
- 원형 스냅샷: `reference/` (참조 전용, 수정 금지)
- 스펙: `DAO_spec.md`
