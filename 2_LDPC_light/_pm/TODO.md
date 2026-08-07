# TODO — 2_LDPC_light (Project 2: 경량 Python 시뮬레이터)

> Claude 마지막 확인: 2026-08-07 15:42:04

> 목표: 외부의 H-matrix와 최적화된 파라미터를 넣어도 동작하게 만들고, 외부에서 pull하여 성능을 확인한다.
> py는 아이디어 상대 비교 전용, 유효 아이디어의 최종 검증은 실물 C++ 이식으로 수행 (`docs/plan.md` §4).

---

## 작업 목록

- [ ] config checker 키별 허용값 확장 (리뷰 후속 수정의 잔여분 — 사용자 정의 예정)
- [ ] 2SD/3SD 디코딩 구현 (2026-08-07 TODO 점검에서 등록)
  - 현재 rber 2SD/3SD와 strong_error 채널은 **채널 출력까지만** 준비 — 디코더가 HD 전용이라 실행 불가 (명시적 에러)
  - 선행: 실물 2SD/3SD LLR_MATRIX 반입 (ch 2개/4개 구성), decoder의 sd/cc region → 채널 LLR 매핑 구현
- [ ] LLR matrix 최적화 시 dv range 상한 고려 (사용자 지시 2026-08-07)
  - 반전 가능 조건 `ch ≤ 7·dv` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)를 최적화 탐색 범위에 반영
  - 현 토이 파일의 dv=2 ch=28 위반은 파라미터 수정 시점에 함께 처리 (벤더 참고값: dv=2 ch=10)
- [ ] `tools/H_mat_gen/select_irregular.py`를 새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질
  - 현재 실행 불가 (구 API 기준, import만 LDPC_base로 보정된 상태)
  - irregular 재현 시드(103)는 `done/20260807_리뷰후속수정/` 문서 §6에 기록됨
- [ ] mpi_runner 재설계 (사용자 확정 2026-08-07: 나중에 진행)
  - 구버전은 본체 반영 때 삭제 — 새 구조(LDPC_base.run) 기준으로 새로 설계
- [ ] LDPC_base 후순위 분석 로그 항목 (2026-08-07 핵심 세트 구현 시 잔류분)
  - bit_err_by_col, flip_count_per_iter, table_row_history, min_sum_stats,
    fail_frame_positions, fail_frame_seed, channel_stats
  - 상세: `_pm/done/20260807_출력폴더_로그기능/` 후보표 참조
- [ ] H-matrix와 LLR 테이블 실물 파일 확인 (z_sb=256 대상) 후 실물 파라미터로 교체 (외부 반입 필요, 저장소에 없음)
  - 3-bit internal precision 잔여 갭은 소실된 HW TH/CH 실값 없이는 추정 튜닝 한계. 실값 반입 시 재검증
- [ ] mpi_runner 슈퍼컴 반입 (재설계 완료 후)
- [ ] 논문 아이디어 스크리닝 시작 (교체 지점 구조는 2026-08-07 완료 — DONE.md 참조.
      교체 지점 = 아이디어 버전이 함수만 갈아끼울 수 있게 분리해 둔 자리, 업계 용어 hook.
      실물 H-matrix, LLR_MATRIX 반입 후 vanilla reference 커브 확보가 선행 단계)
- [ ] 유효 아이디어의 실물 C++ 이식과 최종 검증

## 새 작업 추가

(비어 있음)

---

## 참조

- 계획과 결정 사항: `docs/plan.md` (미결정 사항 확정 이력 포함)
- 리뷰 기록: `docs/review/`
- 완료 이력: `_pm/DONE.md`
