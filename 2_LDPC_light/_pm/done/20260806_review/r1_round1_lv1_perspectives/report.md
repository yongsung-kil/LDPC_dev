# Round 1 결과: 관점 리스트업

> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/` (`LDPC_base/*.py`, `config.json`, `Input/`)
> 에이전트: 2 (lv1, Opus). 상세: `agent_1.md`, `agent_2.md`

## 도출된 관점 (통합, MECE 정리)

| # | 관점명 | 확인 항목 (요약) | 대상 파일/범위 | 출처 |
|---|--------|----------------|--------------|------|
| V1 | C++ 대조 — syndrome-aided 디코더 | flip 도메인 산술, Edge Clear/restart, CNU remove/insert, VNU 양자화, C2V sign 합성, CSW 계산 시점, iteration 0 등가(H·r), genie 판정 타이밍 | `decoder.py:319-446` ↔ `0_LDPC_original/decoder.cpp` | A-P1, B-P1, B-P2 |
| V2 | C++ 대조 — 채널 3종 | qfunc_inv 계수, dev_from_rber 식, HD/2SD/3SD region 판정 부등호, fixed/strong error 슬라이스 배치, C++ round 등가, 검증 수치 재현 | `channel.py` ↔ `channel.cpp`, `ecc_top.cpp` | A-P2, B-P3 |
| V3 | LLR_MATRIX 파서와 row 선택 | 포맷 해석 근거(dv-major 가정), 미사용 필드(max/min_value, floor, needs_csw), row 선택 순회 방향, CSW 경로 미검증, _validate 제약의 근거, 데이터 파일 정합 | `llr_matrix.py`, `Input/LLR/*.txt`, `Input/H_matrix/*.qc` ↔ `decoder.cpp` Get_Cur_LLR_Idx_FILE/Get_VNU_LLR_SET_FILE | A-P3, A-P6, B-P5, B-P6, B-P12 |
| V4 | 디코더 자체 정확성 | 3경로 일관성(two_set/column_wise/matrix), 배치 압축 상태 슬라이싱 전수, 뷰/사본(in-place fill, 슬라이스 재대입), dtype/수치 경계, sim.py 집계 정합, 성능 관찰 | `decoder.py` 전체, `pcm.py`, `sim.py` | A-P5, A-P9, A-P10, B-P7, B-P11, B-P15 |
| V5 | 실행 흐름·설정·인터페이스 계약 | load_config 검증 범위, 필수 키 부재 동작, max_iter 금지의 비-matrix 적용, 채널↔디코더 dict 계약, strong_error 실행 불가 조합, 데드 경로, 시드 파생, 에러 처리 견고성 | `run.py`, `sim.py`, `config.json`, `channel.py`↔`decoder.py` 계약 | A-P4, A-P12, B-P4, B-P8, B-P14 |
| V6 | 본체 반영 파손·스코프·문서 일치 | 본체 examples/tools/mpi_runner 파손 목록, 구 포맷/구 API 의존처 전수, llr_tables 제거 영향, README·plan.md·docstring 사실 일치, C++ 행 번호 인용 정확성, 미구현 항목의 명시적 차단 여부 | `2_LDPC_light/` 본체 전체 grep, 실험 README, `docs/plan.md`, docstring | A-P7, A-P8, A-P11, B-P9, B-P10, B-P13 |

주요 사전 실측 (agent_2):
- 예시 부호 col degree 히스토그램 {2:17, 3:1, 4:129}, LLR matrix dv 구간 [11,4,3,2] → dv=11 그룹 미사용
- 예시 LLR matrix 2개 모두 CSW 다중 row 그룹 없음 → **CSW row 선택 경로는 현재 데이터로 한 번도 실행되지 않음**
- 포맷 정본(DAO_LLR_MATRIX.py)은 저장소에 없음 → 파싱 가정 자체가 검토 대상

## 다음 단계 결정

→ Round 2 (lv1, 에이전트 6개, Opus)
  사유: Round 1 산출물이 이미 파일:라인 수준의 체크리스트와 C++ 앵커(agent_1.md §3)를 제공하므로, 팀 위임(lv2) 없이 관점별 직접 분석(lv1)이 효율적. C++ 대조 2개(V1, V2), 파서 1개(V3), 자체 정확성 1개(V4), 계약 1개(V5), 본체 반영·문서 1개(V6)로 배정.
