# TODO — 5_DAO (Project 5: Decoder Auto Optimizer)

> Claude 마지막 확인: 2026-09-03 01:27:08

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

## 새 작업 추가

(비어 있음)

---

## 참조

- 사용 설명서와 반입 내역: `README.md`
- 원형 스냅샷: `reference/` (참조 전용, 수정 금지)
- 스펙: `DAO_spec.md`
