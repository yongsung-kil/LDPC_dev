# TODO — 2_LDPC_light (Project 2: 경량 Python 시뮬레이터)

> Claude 마지막 확인: 2026-08-07 13:34:48

> 목표: 외부의 H-matrix와 최적화된 파라미터를 넣어도 동작하게 만들고, 외부에서 pull하여 성능을 확인한다.
> py는 아이디어 상대 비교 전용, 유효 아이디어의 최종 검증은 실물 C++ 이식으로 수행 (`docs/plan.md` §4).

---

## 작업 목록

- [ ] `_test/20260806_setup_구성_실험/LDPC_base/` 개정본 코드 딥 리뷰
  - 상세: `_pm/tasks/20260806_review/`
  - 2026-08-06 리뷰 실행 완료 (Round 1→2→3, 최종 판정: 수정 필요)
  - 2026-08-07 사용자 확정 회신 → 후속 수정 작업으로 이관 (`_pm/tasks/20260807_리뷰후속수정/`)
  - Decision 해소: ㉮ llr_profile **제거 확정** ㉯ 채널 설정 **리스트 복원 확정** (단일 항목도 실행 가능) ㉰ dv는 **H-matrix 기준**, LLR_MATRIX 미커버 시 에러 (현행 유지) ㉱ .gitignore는 아래 반영 절차 항목으로
- [x] LDPC_base 리뷰 후속 수정 (사용자 확정 2026-08-07) — **구현 완료** (사용자 지시로 즉시 수행)
  - 상세: `_pm/tasks/20260807_리뷰후속수정/` — 키맵+필수값+config checker, strong_error 2단계 추출,
    F8 캐스케이드 교체, F11 제약 정리(사용자 확정판: 겹침 거부·restart 제약 유지, DAO 규칙 정본),
    F14 주석·문서화, llr_profile 제거(llr_tables.py 삭제), 채널 리스트 복원
  - 2026-08-07 자동 검증 51건 통과 + 라이트 재리뷰(r4) 수리 4건 반영 완료 (`_pm/tasks/20260806_review/r4_round2_lv1_fix_review/`)
  - 잔여: ㉮ config checker 키별 허용값 확장 (사용자 정의 예정) ㉯ F14 legacy 경로 존폐 (가독성 리팩토링에서 재검토)
  - 주의: 코드는 `_test/` 아래라 git 미추적 — 본체 반영 시 조치 항목 참조
- [ ] LLR matrix 최적화 시 dv range 상한 고려 (사용자 지시 2026-08-07)
  - 반전 가능 조건 `ch ≤ 7·dv` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)를 최적화 탐색 범위에 반영
  - 현 토이 파일의 dv=2 ch=28 위반은 파라미터 수정 시점에 함께 처리 (벤더 참고값: dv=2 ch=10)
- [ ] 본체 반영 시 조치 (반영 시점에 실행)
  - 기존 자산(examples, mpi_runner, llr/, 구 포맷 .qc)은 수리하지 않고 전부 아카이빙
  - `.gitignore` `H_Matrix/`를 `0_LDPC_original/` 한정으로 축소 (미수행 시 `Input/H_matrix/`가 git 무추적으로 빠짐)
  - 개정본을 git 추적으로 올린 뒤 이동. irregular 재현 시드(103)는 후속수정 문서 §6에 기록됨
- [ ] LDPC_base 후순위 분석 로그 항목 (2026-08-07 핵심 세트 구현 시 잔류분)
  - bit_err_by_col, flip_count_per_iter, table_row_history, min_sum_stats,
    fail_frame_positions, fail_frame_seed, channel_stats
  - 상세: `_pm/done/20260807_출력폴더_로그기능/` 후보표 참조
- [ ] H-matrix와 LLR 테이블 실물 파일 확인 (z_sb=256 대상) 후 실물 파라미터로 교체 (외부 반입 필요, 저장소에 없음)
  - 3-bit internal precision 잔여 갭은 소실된 HW TH/CH 실값 없이는 추정 튜닝 한계. 실값 반입 시 재검증
- [ ] mpi_runner 슈퍼컴 반입
- [ ] 논문 아이디어 훅 설계 후 스크리닝 시작
- [ ] 유효 아이디어의 실물 C++ 이식과 최종 검증

## 새 작업 추가

(비어 있음)

---

## 참조

- 계획과 결정 사항: `docs/plan.md` (미결정 사항 확정 이력 포함)
- 리뷰 기록: `docs/review/`
- 완료 이력: `_pm/DONE.md`
