# Round 2 결과: 분석 (lv2, 4팀)

발견: 원발견 97건 (팀 A 19, 팀 B 24, 팀 C 23, 팀 D 31). 팀 간 중복 통합 후 고유 발견 기준 **CRITICAL 0, HIGH 13, MEDIUM 33, LOW 40 내외**.
상세는 각 팀 요약(`team_a_summary.md`, `team_b_summary.md`, `team_c_summary.md`, `team_d_summary.md`) 참조. 아래 표는 HIGH 전건과 Round 3 관련 MEDIUM만 싣는다.

## HIGH 발견 (13건)

| # | 심각도 | 문제 | 위치 | 지적 팀 |
|---|--------|------|------|--------|
| A-1 | HIGH | `channel_llr = k·top_level`이면 iteration 1 공명으로 raw=0 → magnitude 0 → CN 침묵 → FER 1.0 붕괴 (경고 없이 완주) | `llr_matrix.py:222-231`, `run.py:197-198` | A |
| A-2 | HIGH | 파일명 `uniform` 부분문자열 오탐 — 사람 제작 파일이 균일 레벨로 오해석되어 조용히 다른 결과 (`nonuniform`도 True) | `llr_matrix.py:170` | A |
| A-3 | HIGH | 생성된 3-bit uniform 파일 개명 시 `th_len==3` 검사를 통과해 `edge_mag`가 조용히 `[7,5,3,1]`로 대체 | `llr_matrix.py:170, 67-72` | A |
| B-1 | HIGH | `frames_per_batch` 변경이 난수 스트림을 어긋내 같은 seed에서도 결과가 달라짐. 문서 3곳은 "결과 영향 없음" 단언 | `run.py:353-357`, `encoder.py:11-19` | B |
| TD-1 | HIGH | 기본 config가 가리키는 `LLR_MATRIX_HD_1.txt`의 dv=2 ch=28이 반전 상한 7·dv=14 초과 → 비트 11.6% 영구 고정, 기본 실행 FER 1.0 | `Input/LLR/LLR_MATRIX_HD_1.txt`, `config.json` | D (+C 독립 재확인) |
| TD-2 | HIGH | README "VNU 출력 레벨 {7,5,3,1} 고정 (3-bit 전용)" 서술이 균일 n-bit 도입 후 거짓 | `README.md:162` | D |
| TD-3 | HIGH | 차이.md #9 "3-bit 전용 (th 3개 아니면 에러)"의 한정 조건 누락 | `docs/차이.md:25` | D |
| TD-4 | HIGH | "false면 `llr_matrix` 키 무시" 서술이 거짓 — `dir`을 생성 위치로 실제 사용 | `README.md:70`, `run.py:17-19` | D (+B B-13 동일) |
| TD-5 | HIGH | 실행 안내가 비존재 `_test/...` 경로를 실험 루트로 지목 | `Ideas/vanilla/README.md:13` | D |
| TD-6 | HIGH | tools README가 이미 끝난 반영을 미래 시제로 서술 + 비존재 경로 참조 | `tools/H_mat_gen/README.md:15-17` | D |
| TD-7 | HIGH | plan.md 머리 단서가 "§7 유효"를 보증하나 §7 #4 max_iter=120이 현행 규약(JSON decoder.max_iter 금지)과 충돌 | `docs/plan.md:4-6, 129` | D |
| TD-8 | HIGH | DONE.md "llr_tables.py 삭제" 기록이 사실과 다름 (파일 추적 중, import 0곳) | `_pm/DONE.md:70`, `llr_tables.py` | D |
| TD-9 | HIGH | `llr_tune.py` LLR 파라미터 탐색 기능이 대체 없이 삭제되고 TODO 미등록 | 삭제 파일, `_pm/TODO.md` | D |

## Round 3 관련 MEDIUM (등급 재판정·처방 검증 대상)

| # | 심각도 | 문제 | 위치 | 지적 팀 |
|---|--------|------|------|--------|
| A-4 | MEDIUM (HIGH 승격 후보) | mag 0 메시지 sign이 `-0.0`으로 항상 양 기록 — csw 로그·final_csw 이미 오염, 교체 지점 재정의 시 복호 결과까지 | `decoder.py:295, 163` | A |
| A-5 | MEDIUM | mag 0이 min1 점유 → CN 침묵, FER 상대 35% 악화. C++은 C2V 최소 1 보장 | `decoder.py:179-184` | A |
| A-11 | MEDIUM (재확인 지정) | 균일 모드의 dv별 ch 미표현 — 실측은 정확하나 ch/top 비율이 DAO와 어긋나 인과 해석 무효 | `llr_matrix.py:226, 229` | A |
| A-6 | MEDIUM | num_bits 상한 부재 + 캐스케이드 선형 비용. 처방: 균일 경로 `sign·min(|raw|,top)` O(1) 대체 (등가 실측) | `run.py:195-196`, `decoder.py:156-157` | A (+B, C 동일) |
| C2-3 | MEDIUM (CRITICAL 경계) | matplotlib 미설치 시 완주한 실험의 summary.txt 유실 (그림 저장이 summary보다 앞, exit 1) | `run.py:496, 561-566` | C |
| C1-F1 | MEDIUM | `_column_order` 재정의 시 성공 오판정 (에러 집계가 column 루프 안) — 교체 지점 표의 과잉 커버 주장과 한 뿌리 | `decoder.py:258-259, 283-288` | C |

## 통과 관점 (문제 미발견 확인 범위)

- 리팩토링 동작 보존: 산출물 바이트 대조 + 독립 참조 구현 + log 16조합 전수 — 이상 없음 (팀 C)
- save/load 왕복: 12조합×19필드 일치, 커밋 uniform 파일 재생성 바이트/md5 일치 (팀 A, C, D 3중 확인)
- 캐스케이드 C++ 등가성: 20만 건 대조 불일치 0 (팀 A)
- 의견1 이름 수정: 18항목 중 16 완료, 치환 후유증 0건 (팀 B)
- config 키맵 커버리지·요약 출력 정확성: 어긋남 0건 (팀 B)
- Input 데이터 자기 정합: _validate 5제약·H-matrix 헤더·dv 매칭 전수 통과 (팀 D)
- % 마커 0건, 저장소 오염 없음 (팀 C, D)

## 다음 단계 결정

→ Round 3 (lv2, 3팀) 진행
  사유: 라이트 전환 기준 4행 매칭 — HIGH 13건 존재, 수정 처방(동작 변경 요구 포함: 0 레벨 제거, generate_message 호출 제거, O(1) 대체)이 붙은 발견 존재, 재확인 지정 발견(A-11, A-4 승격, C2-3 등급) 존재.
  검증 팀 배분:
  - 검증팀 a (numeric): A-1, A-2, A-3 사실 검증 + A-4 승격 판정·np.signbit 처방 + A-5 0 레벨 처방 + A-11 DAO 비율 재실험 + A-6 O(1) 처방
  - 검증팀 b (config_exec): B-1 사실·크기 실측 + 처방 검증, C2-3 등급 재판정, C1-F1 사실·처방, Input/LLR 오염 계열(A-10, B-4, C3-1, TD-10) 처방 방향 검증
  - 검증팀 c (docs_data): TD-1 대수 근거 재확인, TD-2~TD-9 문서 사실성 전건 검증
  검증 생략: MEDIUM 이하 중 실측·grep으로 근거가 자명한 발견 (Round 2 요약을 정본 유지)
