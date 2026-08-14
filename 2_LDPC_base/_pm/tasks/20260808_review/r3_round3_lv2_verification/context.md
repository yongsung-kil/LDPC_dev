# Verification Context

## Round 2 발견 요약

원발견 97건 → 고유 발견 CRITICAL 0, HIGH 13, MEDIUM 33, LOW 40 내외.
전체 목록: `../r2_round2_lv2_analysis/report.md`와 팀 요약 4종 (`team_a_summary.md`, `team_b_summary.md`, `team_c_summary.md`, `team_d_summary.md`).

## 검증 대상 (팀별 배분)

### 검증팀 a (numeric) — 수치 발견의 사실·처방 검증

| 발견 | 심각도 | 검증 성격 |
|------|--------|----------|
| A-1 (ch=k·top_level 공명 → FER 1.0) | HIGH | 사실 검증: 실측 재현과 대수 근거의 독립 재확인 |
| A-2 (uniform 부분문자열 오탐) | HIGH | 사실 검증 |
| A-3 (3-bit uniform 파일 개명 시 조용한 edge_mag 대체) | HIGH | 사실 검증 |
| A-4 (-0.0 부호 소실) | MEDIUM→HIGH 승격 판정 | 사실 검증(csw 로그 오염이 "이미 실사용 출력 오류"인가) + 처방 검증(`new_sgn = np.signbit(vnu_out)` 교체 시 3-bit 파일 경로 동작 완전 보존 여부) |
| A-5 (mag 0의 min1 점유 → CN 침묵) | MEDIUM | 처방 검증: "0 레벨 제거(최소 1)" 처방이 A-1·A-5를 동시에 해소하고 부작용이 없는가. C++ 대응(`C2V_Cal`의 `EDGE_MAG_1=1` 복원, `decoder.cpp:2405`, `common.h:338-341`) 근거 재확인 |
| A-11 (dv별 ch 미표현의 FER 영향) | MEDIUM 재확인 지정 | 재실험: DAO 파일과 같은 ch/top_level 비율(dv2 약 4.0, dv4 약 1.4)로 스윕해 인과 방향·크기 판정 |
| A-6 처방 (균일 경로 O(1) 대체) | MEDIUM | 처방 검증: `sign(raw)·min(|raw|,top_level)` 등가성이 균일 매트릭스의 전 유효 입력에서 성립하는가, 교체 지점 구조와 충돌 없는가 |

### 검증팀 b (config_exec) — 실행 재현·등급 재판정·처방 검증

| 발견 | 심각도 | 검증 성격 |
|------|--------|----------|
| B-1 (frames_per_batch가 난수 실현값 변경) | HIGH | 사실 검증: 실제 시뮬레이터로 같은 config에서 frames_per_batch만 128→64로 바꿔 FER/BER 차이 실측 (팀 B는 numpy 재현 실험까지만 수행). 처방 검증: "generate_message 호출 제거 또는 프레임 단위 스트림 파생" 처방의 타당성과 부작용 (실물 인코더 도입 시나리오 포함) |
| C2-3 (matplotlib 부재 시 summary.txt 유실) | MEDIUM, CRITICAL 경계 | 등급 재판정: 심각도 정의(CRITICAL=프로세스 중단/비가역 손상, HIGH=틀린 결과, MEDIUM=엣지케이스)에 따른 판정. 재현 확인 + "그림 저장을 summary 뒤로 이동 또는 try/except" 처방 검증 |
| C1-F1 (_column_order 재정의 시 성공 오판정) | MEDIUM | 사실 검증: 재현 스크립트 독립 재실행. 처방 검증: "에러 집계를 column 루프 밖으로" 이동이 기존 동작을 보존하는가 |
| Input/LLR 오염 계열 (A-10 = B-4 = C3-1 = TD-10 동일 사안) | MEDIUM (Decision) | 처방 검증: 3처방(㉮ .gitignore 추가 ㉯ 파일명에 dv_max ㉰ 생성 위치를 Sim_Output 계열로) 각각의 부작용과 상호 배타 여부 정리 — 사용자 결정에 올릴 선택지의 정확성 확보 |

### 검증팀 c (docs_data) — 문서·데이터 사실성 검증

| 발견 | 심각도 | 검증 성격 |
|------|--------|----------|
| TD-1 (기본 config → FER 1.0) | HIGH | 사실 검증: 대수 근거(`sum_t >= 28 - 2·7 = 14 > 0`)를 코드(`decoder.py:142, 266-279`)에서 독립 재유도 + 기본 config 실행 재현. "디코더 결함이 아니라 데이터-부호 정합 문제"라는 원인 판정 재확인 |
| TD-2 (README "3-bit 전용" 거짓) | HIGH | 사실 검증: 코드 근거와 32레벨 복호 성공 재확인 |
| TD-3 (차이.md #9 한정 조건 누락) | HIGH | 사실 검증 |
| TD-4 ("llr_matrix 무시" 서술 거짓) | HIGH | 사실 검증: `run.py:206-208` 동작 재확인 |
| TD-5 (_test 경로 안내, Ideas/vanilla/README.md) | HIGH | 사실 검증: 경로 부재 + 올바른 실행 루트 확인 |
| TD-6 (tools README 미래 시제) | HIGH | 사실 검증 |
| TD-7 (plan.md 단서가 틀린 정보 보증) | HIGH | 사실 검증: §7 #4와 `run.py:178-181` 충돌, §3.1b·§3.2·§5 어긋남 각각 재확인 |
| TD-8 (DONE.md "llr_tables.py 삭제" 허위) | HIGH | 사실 검증: git 추적 상태, import 0곳 재확인 |
| TD-9 (llr_tune.py 기능 유실 미등록) | HIGH | 사실 검증: 삭제 파일 내용과 균일 모드의 기능 범위 대조, TODO 전 항목에 부재 확인 |

## 검증 생략 항목 (Round 2 요약이 정본)

- MEDIUM 이하 중 실측·grep으로 근거가 자명한 발견 전부: A-7~A-19 (A-11 제외), B-2~B-24 (B-1 제외), C 팀 MEDIUM/LOW (C2-3, C1-F1 제외), TD-10~TD-21과 LOW 10건
- 사용자 결정 사안 D1~D6은 검증 대상이 아니라 최종 보고에 결정 요청으로 전달

## 기술 맥락

- Python 로컬 실행 가능. 실행 시 저장소 추적 파일을 수정·생성하지 말 것 — config 사본을 scratchpad(`C:\Users\yongs\AppData\Local\Temp\claude\d--OneDrive-My-Projects-LDPC-dev\96aaaa04-61b8-4b90-ac92-52ca7348de60\scratchpad`)에 만들어 출력·생성 경로를 scratchpad로 돌린다
- C++ 원본 참조: `0_LDPC_original/` (읽기 전용, 빌드 금지). 팀 A Round 2가 인용한 근거: `decoder.cpp:2405, 4102-4115`, `common.h:328-341`
- 심각도 정의: CRITICAL(프로세스 중단/비가역 손상) / HIGH(틀린 결과를 내지만 진행) / MEDIUM(엣지케이스 위험) / LOW(개선 제안)
- 처방 판정 표기: 처방 유효 / 처방 수정 필요(대안 제시) / 처방 반대(사유 명시)
