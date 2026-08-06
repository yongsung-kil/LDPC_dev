# Verification Context

## 리뷰 대상

`2_LDPC_light/_test/20260806_setup_구성_실험/` — `LDPC_base/*.py`(본체 개정본), `config.json`, `Input/`.
원본 C++: `0_LDPC_original/` (읽기 전용, 빌드 금지. Python 실행은 스크래치패드에서 허용).
Round 2 상세: `../r2_round2_lv1_analysis/agent_1.md`(V1 디코더 C++ 대조) ~ `agent_6.md`(V6 본체 반영·문서).
통합 발견 목록: `../r2_round2_lv1_analysis/report.md` (F1~F25).

## Round 2 발견 요약 (검증 대상만)

| # | 심각도 | 문제 | 위치 | 처방 원문 |
|---|--------|------|------|-----------|
| F1 | HIGH | argpartition이 뽑힌 k개의 순서 무작위성을 깨뜨려 strong_error 에러 위치가 column block에 극단 편향 (상위 2블록 37.1%). 원본 rand_sel_ep(random.cpp:343-369)는 부분 Fisher-Yates | `channel.py:71-73` | "`p = np.argpartition(...)[:, :k]` 뒤에 `p = rng.permuted(p, axis=1)` 추가 (전체 argsort도 정확하나 비용 큼)" |
| F2 | HIGH | matrix 경로 \|C2V\|<=7 상한 vs dv=2 ch=28>14 → 영구 미정정 11.6%, 현행 config FER≡1.0. 원인 두 갈래 미확정: ㉮ 도메인 불일치(edge_mag {7,5,3,1} vs 테이블 5-bit max 31) ㉯ 토이 데이터 문제. README:114-117은 "C++도 동일할 산술, 구현 버그 아님"이라 서술 | `decoder.py:68,388,398` | "생성자에서 `ch_table[dv] > edge_mag[0]*dv`인 dv 구간 검사해 경고 또는 차단" |
| F3 | HIGH | run 하위 키가 .get()만 사용 — 구 키(target_errors/stop_below)와 오타가 조용히 무시되고 기본값 실행 | `run.py:109-114` | "run 하위 키 화이트리스트 검증" |
| F4 | HIGH(반영 시) | fer_curve.json 5개 키 + fer_curve.py 파손 | 본체 examples/ | 반영 전 재작성 |
| F5 | HIGH(반영 시) | bsc_llr/awgn_llr/fixed_error_llr 삭제 → 스크립트 3개+mpi_runner 즉사 | 본체 | 갱신 또는 폐기 |
| F6 | HIGH(반영 시) | run_fer_point 인자명 변경 → 호출부 4곳 TypeError | 본체 | 갱신 |
| F7 | HIGH(반영 시) | 구 포맷 .qc 2개 로드 불가, irregular_17x144는 재생성 경로도 죽어 자산 소실 | 본체 examples/ | "반영 전 .qc 2개를 Ref-C로 변환 (최우선), 이후 순서: llr_profile 결정 → plan.md 기록 → max_iter 확정 → 코드 이동 → examples 갱신 → 문서 → Sim_Output 정리" |
| F8 | MEDIUM | _mx_vnu_quantize/_vnu_quantize가 지시함수 합 — th 내림차순 전제, C++는 캐스케이드. 비단조 th에서 조용히 갈림 | `decoder.py:81,94-96` | "_validate에서 row_th 내림차순(또는 -1 동일) 검사, 또는 np.select 캐스케이드로 교체" |
| F11 | MEDIUM | _validate 제약 4종이 C++ 근거 없음 (그룹 연속성/iter1 시작/restart 단일/restart 마지막 금지), 합법 파일 거부. 단 "겹침 금지"는 _group_of_iter 정방향 순회의 안전 근거 | `llr_matrix.py:73-94` | "restart 마지막 금지와 iter1 시작 강제는 제거 권고, 제약-순회 한 쌍 관계를 주석으로" |
| F14 | MEDIUM | genie 동점 규칙 경로별 상이: matrix `total<=0`(반전), signed 두 경로 `total<0`(유지=정답). **V1은 "각자 도메인에 맞음"(agent_1.md §3), V4는 "경로 간 비교 계통 오차"(agent_4.md M-3) — 이견** | `decoder.py:170,268,398` | 판정 필요: 의도로 문서화 vs signed 경로 수정 |
| F19 | MEDIUM | batch<=0 무한 hang (25s timeout 실측) — 심각도 기준표상 hang은 CRITICAL인데 트리거가 비정상 설정이라 MEDIUM으로 분류됨 | `sim.py:17-22` | 가드 추가. 심각도 재평가 필요 |
| F23 | MEDIUM | llr_tables.py 제거 불가 — decoder.py 6곳 의존 (50, 48-55, 72-88, 233, 275-276, 178) | `decoder.py` | 존치 여부 Decision |

## 검증 생략 항목 (Round 2 요약이 정본)

F9, F10, F12, F13, F15~F18, F20~F22, F24, F25, LOW 전건 — 실행 실측/grep으로 근거 자명.

## 기술 맥락

- 이 개정본은 완성 시 본체(`2_LDPC_light/`)의 새 원본이 된다. 원본 C++ 대응(AUTO 빌드, `__AUTO_LLR_OPT__`, 3-bit, BF off)이 정확성의 기준
- C++ 원문 앵커: `../r1_round1_lv1_perspectives/agent_1.md` §3 표 참조
- Python 로컬 실행 가능 (스크래치패드에서만, 프로젝트 파일 수정 금지)
- V1이 확인한 사실 (F2 판정에 중요): C++ `decoder.cpp:4026` `sum_t = channel_llr`(= 테이블 ch1 그대로), C2V는 V→EDGE 사상 {7,5,3,1} (`decoder.cpp:2402-2405`) — 즉 C++의 sum_t 가산 도메인 구조 확인됨
