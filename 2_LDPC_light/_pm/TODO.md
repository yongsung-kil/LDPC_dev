# TODO — 2_LDPC_light (Project 2: 경량 Python 시뮬레이터)

> Claude 마지막 확인: 2026-08-06 23:11:36

> 목표: 외부의 H-matrix와 최적화된 파라미터를 넣어도 동작하게 만들고, 외부에서 pull하여 성능을 확인한다.
> py는 아이디어 상대 비교 전용, 유효 아이디어의 최종 검증은 실물 C++ 이식으로 수행 (`docs/plan.md` §4).

---

## 작업 목록

- [ ] `_test/20260806_setup_구성_실험/LDPC_base/` 개정본 코드 딥 리뷰
  - 상세: `_pm/tasks/20260806_review/`
- [ ] LDPC_base 변수명·가독성 리팩토링 (짧아서 부정확한 변수명 풀어 쓰기, 원본 C++ 용어와 정합)
  - **착수 조건**: 외부에서 진행 중인 LDPC 동작 확인 작업 완료 후
  - 상세: `_pm/tasks/20260806_가독성리팩토링/` (개선 후보 사전 조사 포함)
- [ ] LDPC_base JSON 설정에서 폴더명과 파일명 분리 수용 (사용자 지시 2026-08-06, 지금 수정하지 않고 대기)
  - 대상 키: `H_matrix`, `decoder.llr_matrix` — `{"dir": 폴더, "file": 파일명}` 형태로 변경
  - H_matrix 폴더는 `Input/H_matrix` 고정 운용이지만 형태는 분리해서 받는다
  - 수정 파일: `LDPC_base/run.py` load_config, `config.json`, README 스키마 절
  - **착수 조건**: 위 리팩토링과 동일 (외부 LDPC 동작 확인 작업 완료 후)
- [ ] LDPC_base 결과 폴더 구조화 + 분석 로그 출력 기능 (사용자 지시 2026-08-06, 착수 대기)
  - Sim_Output 하위에 실행마다 `YYMMDD_HHMMSS_{라벨}/` 폴더 생성, config 사본 저장
  - JSON `log` 섹션으로 항목별 로그 선택 (iteration별 CSW, bit error 전체·DV별 등)
  - C++에 없는 통상 항목도 포함 (post-FEC BER, FER 신뢰구간, miscorrection 분리, FER vs iteration 등)
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
