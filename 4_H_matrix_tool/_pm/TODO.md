# TODO: 4_H_matrix_tool (Project 4: H-matrix 설계 툴)

> Claude 마지막 확인: 2026-10-21 18:19:27

> 목표: H-matrix 설계 도구를 발전시켜 원하는 조건의 부호를 설계하고, 결과를 Ref-C 포맷으로 공급한다.

---

## 작업 목록

- [ ] `src/select_irregular.py`를 새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질
  - 현재 실행 불가 (구 API 기준, import만 현행 경로로 보정된 상태)
  - irregular 재현 시드(103)는 `2_LDPC_base/_pm/done/20260807_리뷰후속수정/` 문서 §6에 기록됨
  - 2026-08-14에 2_LDPC_base TODO에서 이전된 항목

- [ ] H-matrix 사이클과 trapping set 조사 도구 (실패한 codeword를 가둔 원인 구조 식별, H의 사이클과 유해 구조 조사)
  - 상세: `_pm/tasks/20261021_cycle_trapping_tool/`
  - [x] 논문 조사와 기반 논문 선정 (2026-10-21, `논문조사.md`)
  - [x] 설계 문서 작성 (2026-10-22, `설계.md`. 미결정 4건 중 3건은 설계자가 정함, 탐색 방식 1건은 `판정요청_설계_261022.md` 대기)
  - [ ] 구현과 검증 (소형 H 교차 검증, 평가 대상 파라미터 실측)

## 새 작업 추가

(비어 있음)

---

## 참조

- 도구 구성과 실행 방법: `README.md`
- 완료 이력: `_pm/DONE.md`
