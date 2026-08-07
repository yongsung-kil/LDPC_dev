# TODO — 2_LDPC_light (Project 2: 경량 Python 시뮬레이터)

> Claude 마지막 확인: 2026-08-07 11:47:35

> 목표: 외부의 H-matrix와 최적화된 파라미터를 넣어도 동작하게 만들고, 외부에서 pull하여 성능을 확인한다.
> py는 아이디어 상대 비교 전용, 유효 아이디어의 최종 검증은 실물 C++ 이식으로 수행 (`docs/plan.md` §4).

---

## 작업 목록

- [ ] `_test/20260806_setup_구성_실험/LDPC_base/` 개정본 코드 딥 리뷰
  - 상세: `_pm/tasks/20260806_review/`
  - 2026-08-06 리뷰 실행 완료 (Round 1→2→3, 최종 판정: 수정 필요)
  - 2026-08-07 사용자 확정 회신 → 후속 수정 작업으로 이관 (`_pm/tasks/20260807_리뷰후속수정/`)
  - Decision 해소: ㉮ llr_profile **제거 확정** ㉯ 채널 설정 **리스트 복원 확정** (단일 항목도 실행 가능) ㉰ dv는 **H-matrix 기준**, LLR_MATRIX 미커버 시 에러 (현행 유지) ㉱ .gitignore는 아래 반영 절차 항목으로
- [ ] LDPC_base 리뷰 후속 수정 (사용자 확정 2026-08-07)
  - 상세: `_pm/tasks/20260807_리뷰후속수정/` — 키맵+필수값+config checker, strong_error 2단계 추출,
    F8 캐스케이드 교체, F11 제약 정리, F14 주석·문서화, llr_profile 제거, 채널 리스트 복원
  - **착수 조건**: 외부 LDPC 동작 확인 작업 완료 후 (다른 LDPC_base 수정과 동일)
- [ ] LLR matrix 최적화 시 dv range 상한 고려 (사용자 지시 2026-08-07)
  - 반전 가능 조건 `ch ≤ 7·dv` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)를 최적화 탐색 범위에 반영
  - 현 토이 파일의 dv=2 ch=28 위반은 파라미터 수정 시점에 함께 처리 (벤더 참고값: dv=2 ch=10)
- [ ] 본체 반영 시 조치 (반영 시점에 실행)
  - 기존 자산(examples, mpi_runner, llr/, 구 포맷 .qc)은 수리하지 않고 전부 아카이빙
  - `.gitignore` `H_Matrix/`를 `0_LDPC_original/` 한정으로 축소 (미수행 시 `Input/H_matrix/`가 git 무추적으로 빠짐)
  - 개정본을 git 추적으로 올린 뒤 이동. irregular 재현 시드(103)는 후속수정 문서 §6에 기록됨
- [ ] LDPC_base 변수명·가독성 리팩토링 (짧아서 부정확한 변수명 풀어 쓰기, 원본 C++ 용어와 정합)
  - **착수 조건**: 외부에서 진행 중인 LDPC 동작 확인 작업 완료 후
  - 상세: `_pm/tasks/20260806_가독성리팩토링/` (개선 후보 사전 조사 포함)
- [ ] LDPC_base JSON 설정에서 폴더명과 파일명 분리 수용 (사용자 지시 2026-08-06, 지금 수정하지 않고 대기)
  - 대상 키: `H_matrix`, `decoder.llr_matrix` — `{"dir": 폴더, "file": 파일명}` 형태로 변경
  - H_matrix 폴더는 `Input/H_matrix` 고정 운용이지만 형태는 분리해서 받는다
  - JSON 설명 key 규칙 추가 (사용자 논의 2026-08-07): `_`로 시작하는 key(예: `_desc`)는
    설명용으로 코드가 무시. config.json 각 섹션에 설명 달기
  - `run.batch` → `run.frames_per_batch`로 개명 (사용자 확정 2026-08-07). `_desc`:
    "한 번에 동시 복호하는 프레임 수, 속도와 메모리 조절용이며 결과에 영향 없음"
  - seed는 채널별(`rber.seed` 등)에서 한 단계 위(`channel.seed`)로 올려 하나만 두고,
    기본값 0 (사용자 확정 2026-08-07). `run.seed` fallback도 제거하고 단일화
  - 수정 파일: `LDPC_base/run.py` load_config와 run_experiment, `config.json`, README 스키마 절
  - **착수 조건**: 위 리팩토링과 동일 (외부 LDPC 동작 확인 작업 완료 후)
- [ ] LDPC_base 결과 폴더 구조화 + 분석 로그 출력 기능 (사용자 지시 2026-08-06, 착수 대기)
  - Sim_Output 하위에 실행마다 `YYMMDD_HHMMSS_{라벨}/` 폴더 생성, config 사본 저장
  - JSON `log` 섹션으로 항목별 로그 선택 (iteration별 CSW, bit error 전체·DV별 등)
  - C++에 없는 통상 항목은 3개만 추가 확정 (post-FEC BER, FER vs iteration, FER 커브 PNG)
  - 상세: `_pm/tasks/20260806_출력폴더_로그기능/`
  - **착수 조건**: 위와 동일 (외부 LDPC 동작 확인 작업 완료 후)
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
