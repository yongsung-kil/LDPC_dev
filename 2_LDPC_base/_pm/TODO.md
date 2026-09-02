# TODO — 2_LDPC_base (Project 2: 경량 Python 시뮬레이터)

> Claude 마지막 확인: 2026-08-13 16:23:33

> 목표: 외부의 H-matrix와 최적화된 파라미터를 넣어도 동작하게 만들고, 외부에서 pull하여 성능을 확인한다.
> py는 아이디어 상대 비교 전용이다 (`docs/plan.md` §4).

---

## 작업 목록

- [ ] 딥 리뷰 후속 처리: 마지막 리뷰(r4, ea88882) 이후 변경분 딥 리뷰 완료 (2026-08-08, Round 1~3)
  - 상세: `_pm/tasks/20260808_review/` (종합보고.md에 사용자 답변 반영 완료)
  - [x] 사용자 답변 반영: FER 1.0 조치 불필요, 배치 무관성은 문언 교정으로 종결, llr_tables와 llr_tune 폐기 (2026-08-09)
  - [x] 수리 1차: 문서 사실 교정 6건, frames_per_batch 문언 3곳, llr_tables.py 삭제 (2026-08-09)
  - [x] 결정 1, 2, 4 확정과 구현 (2026-08-09): 균일 레벨 최소 1(개선안, ch=top 공명 해소 실측),
        생성 LLR은 output.dir/_generated + 실행 폴더 사본 저장 선택(output.save_llr_matrix), 줄표 금지 규칙 등재
  - [x] 수리 2차 일부 (2026-08-09): 균일 판정 값 기반 교체, O(1) 등가식, summary.txt 저장 순서와
        그림 실패 보호, git 해시 dirty 표시, num_bits 상한 16, 파일명 dv_max, 고아 uniform 파일 삭제
  - [x] 줄표 일괄 수리 (2026-08-09): 22파일 149건, AST 대조로 로직 무변경 확인 (_pm/과 docs/review/ 이력물은 보존)
  - [x] 수리 3차 (2026-08-09): 판정비트 배열(성공 오판정 방어, 회귀 완전 일치 확인),
        Ideas 임포트 실패는 에러로 종료(사용자 확정), 2SD/3SD 사전 차단, LLR 파일 부재 안내,
        internal_quantize 분기 무관 검증, run 기본값 단일 출처, 교체 지점 규칙 문서화,
        requirements.txt 신설, 검증 강화(label/print_progress/중복 포인트), 요약에 공급 경로 추가
  - [x] 가운뎃점 나열 용법 제거, "계약" 등 용어 정리 (2026-08-09, 규칙 ㉱에 가운뎃점 포함)
  - [ ] floor flag 왕복 보존: 나중에 쓰일 수 있어 현행 유지 (사용자 확인 2026-08-09, 필요 시 재개)
  - [x] plan.md 처리 확정 (2026-08-09): 결정 기록만 README "확정 결정 기록" 절로 이전 후 삭제, 참조 정리
- [ ] config checker 키별 허용값 확장 (리뷰 후속 수정의 잔여분, 사용자 정의 예정)
- [ ] LLR matrix 최적화 시 dv range 상한 고려 (사용자 지시 2026-08-07)
  - 반전 가능 조건 `ch ≤ 7·dv` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)를 최적화 탐색 범위에 반영
  - 현 토이 파일의 dv=2 ch=28 위반은 파라미터 수정 시점에 함께 처리 (벤더 참고값: dv=2 ch=10)
- [ ] mpi_runner 재설계 (사용자 확정 2026-08-07: 나중에 진행)
  - 구버전은 본체 반영 때 삭제하고, 새 구조(src.run) 기준으로 새로 설계
- [ ] src 후순위 분석 로그 항목 (2026-08-07 핵심 세트 구현 시 잔류분)
  - bit_err_by_col, flip_count_per_iter, table_row_history, min_sum_stats,
    fail_frame_positions, fail_frame_seed, channel_stats
  - 상세: `_pm/done/20260807_출력폴더_로그기능/` 후보표 참조
- [ ] 평가 대상 H-matrix와 LLR 테이블(z_sb=256 대상)을 `Input/`에 넣고 config 기본값 교체
  - 3-bit internal precision 잔여 갭은 소실된 HW TH/CH 값 없이는 추정 튜닝 한계. 값을 받으면 재검증
  - 교체 후 minsum_dual_clip(ieee:9496601) 최종 판정은 3_LDPC_ideas TODO가 관리 (`3_LDPC_ideas/001_minsum_dual_clip/` 참조)
- [ ] mpi_runner 슈퍼컴 이관 (재설계 완료 후)

## 새 작업 추가

(비어 있음)

---

## 참조

- 확정 결정 기록: `README.md`의 "확정 결정 기록" 절
- 리뷰 기록: `_pm/done/` 아래 `{YYYYMMDD}_review/` 폴더
- 완료 이력: `_pm/DONE.md`
