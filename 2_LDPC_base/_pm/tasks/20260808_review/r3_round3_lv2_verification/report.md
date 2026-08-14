# Round 3 결과: 검증 (lv2, 3팀)

검증 대상 17건 (HIGH 13 + 등급 재판정 2 + 재확인 지정 1 + 처방 묶음 1). 상세는 `team_a_verification.md`, `team_b_verification.md`, `team_c_verification.md`.

## 발견 판정

| # | 원래 심각도 | 문제 | 판정 | 근거 요약 |
|---|-----------|------|------|----------|
| A-1 | HIGH | ch 공명 → FER 1.0 붕괴 | 부분 확인 (HIGH 유지) | 기전·무경고 완주 확인. 발동 조건 서술 반박 — 정확 조건은 `ch=k·top_level`이고 `\|k\|<=dv-1`, `k≡dv-1(mod 2)`인 dv 존재. 이 부호에선 `ch=top_level`(k=1)만 파국. "ch=14도 공명"은 오귀인. 추가 발견: `ch=1` 파국, `ch>dv·top_level` flip 불가 기전(TD-1과 동일 뿌리) |
| A-2 | HIGH | uniform 부분문자열 오탐 | 확인됨 (HIGH 유지) | 6개 이름 전부 조용히 `[3,2,1,0]`, FER 0.8906 대 0.9688. DAO 매트릭스는 본질이 non-uniform이라 `nonuniform` 작명이 자연스러워 위험이 과소평가였음 |
| A-3 | HIGH | 3-bit 생성 파일 개명 시 조용한 대체 | 확인됨, 도달 경로 반박 (HIGH 유지, A-2와 병합) | num_bits=3만 조용히 통과. 단 생성 파일명은 항상 uniform 포함이라 사람 개명이 필요 — "사용자 실수만이 아니다"는 A-2 한정 |
| A-4 | MEDIUM | -0.0 부호 소실 | 확인됨, **HIGH 승격** | csw_mean 30/30행, final_csw 64/64행이 실사용 CSV에서 틀림(최대 8.7%). 단서: FER/BER/수렴 iteration은 정확 — CSW 계열 로그만 틀림. "복호 결과 불변"은 기본 column 순서 한정 |
| A-5 | MEDIUM | mag 0의 min1 점유 → CN 침묵 | 확인됨 (MEDIUM 유지) | 손상은 2중(다른 edge 0 + min1_pos edge가 근거 없는 RESET 수신). 워터폴 구간 FER 1.2~1.9배 손해 재현. Round 2의 "iter5 7.97%"는 미재현(실측 최대 iter4 4.6~4.8%) |
| A-11 | MEDIUM | 균일 모드 dv별 ch 미표현 | 재판정: 차등이 유의미 이득 (MEDIUM 유지) | DAO 비율 보정 재실험: 최선 공통 ch 대비 dv 차등이 FER 9.3배 개선. 단 이득 방향은 DAO 비율의 정반대. Round 2 실험 근거는 무효 확정(flip 불가 영역 실험이었음). 균일 모드 수치를 파일 매트릭스와 나란히 비교하지 말 것 |
| B-1 | HIGH | frames_per_batch가 결과 변경 | 확인됨 (HIGH 유지) | end-to-end 실측 FER 3.867e-1(b128) 대 3.750e-1(b64). 연쇄 발견 V-1: 난수 정렬 후에도 `max_frame_errors` 종료 규칙이 배치 경계로 양자화 — 난수 처방만으로 "배치 무관" 회복 불가 |
| C1-F1 | MEDIUM | _column_order 재정의 시 성공 오판정 | 확인됨 (MEDIUM 유지) | 빈 스케줄 64/64, col 1개 생략 49건 오판정 재현. 스케줄 아이디어 유입 시 HIGH 조건부 유지 |
| C2-3 | MEDIUM (CRITICAL 경계) | matplotlib 부재 시 summary.txt 유실 | 확인됨, **HIGH 상향** | 의존성 선언 파일 전무 + 두 config 모두 fer_curve_png 기본 on이라 새 환경 첫 실행이 곧 이 경로(엣지케이스 아님). 재실행 없이 복구 불가 2건(커밋 해시, 실제 사용 디코더 클래스). CRITICAL은 과대(측정 완주 후 사망, 재실행 8.3초) |
| Input/LLR 계열 | MEDIUM (Decision) | 추적 폴더 오염·무경고 덮어쓰기 | 확인됨 (MEDIUM Decision 유지) | 3처방 상호 배타 아님(H16 반박). ㉰(Sim_Output 계열 이동)가 최광범위. S4(3-bit 개명 시 조용한 대체)는 어느 처방도 못 닫음 — 별도 Decision |
| TD-1 | HIGH | 기본 config → FER 1.0 | 부분 확인 (HIGH 유지) | 하한식 독립 재유도·실측 도달·원본 실행 FER 1.000 재현·반증 실험 2건 전부 성립. "어디에도 기록 없음"만 반박 — r4 리뷰 보고서에 기록 있음. "실행자가 읽는 문서(README, docs/, _desc)에 경고 없음"으로 축소 |
| TD-2 | HIGH | README "3-bit 전용" 거짓 | 확인됨 (HIGH 유지) | 32레벨 복호 성공 + 같은 문서 자기모순 |
| TD-3 | HIGH | 차이.md #9 한정 조건 누락 | 확인됨 (HIGH 유지) | false positive 반증 실패. `llr_matrix.py:70` 에러 문구도 동일 오류(병합) |
| TD-4 | HIGH | "llr_matrix 무시" 서술 거짓 | 부분 확인 (HIGH 유지, 범위 축소) | 온전한 결함은 README:69-70 한 곳. run.py:19와 config.json:20은 다음 문장이 정정하므로 표현 결함 |
| TD-5 | HIGH | 비존재 _test 경로 안내 | 확인됨 (HIGH 유지) | 따라 하면 ModuleNotFoundError 실증 |
| TD-6 | HIGH | tools README 미래 시제 | 확인됨 (HIGH 유지) | 커밋 순서(3f596ef 12분 뒤 2e600ea)가 원인 확정 |
| TD-7 | HIGH | plan.md 단서가 틀린 정보 보증 | 부분 확인, **MEDIUM 하향** | 핵심 증거(§7 #4 max_iter=120 충돌) 반박 — 값 결정이며 config.json:33에 존속, run.py는 키 이름만 금지. 결론은 §1 #5(2-9 포맷 서술, plan.md:22)와 규칙 ㉮ 덧대기로만 성립 |
| TD-8 | HIGH | DONE.md "llr_tables.py 삭제" 허위 | **반박됨** | 동명이물 오판 — DONE.md 기록은 _test 개정본의 파일이며 실제 삭제됨(태스크 문서에 경로 명시). 재구성: "구 코드 삭제 커밋(2e600ea) 누락분 `llr_tables.py` 사문화 존속" MEDIUM |
| TD-9 | HIGH | llr_tune.py 탐색 기능 유실 미등록 | 확인됨 (HIGH 유지) | 후보 비교 축 5항목 대체 부재 반증 실패, TODO 미등록 확인. 표현 수정 2건("동일 조건 비교와 FER 표 산출", "이 저장소 안에 대체 없음"). 처방은 복구가 아니라 결정 요청 |

## 처방 판정

| 처방 | 판정 | 내용 |
|------|------|------|
| P1: 균일 edge_mag 0 레벨 제거 (A-1·A-5) | **처방 수정 필요** (Decision) | 원문(`[top..1]`)은 즉시 ValueError. 안 ㉮ `[top..2,1,1]` 권고 — 파일 포맷·커밋 파일·왕복 전부 불변, A-1·A-5 동시 해소 실측. 안 ㉯는 호환성 파괴로 반대. C++ 정합 주장은 확인됨 |
| P2: `np.signbit` 부호 판정 (A-4) | **처방 유효** | 3-bit 파일 경로 2억+ 원소 전수 비트 보존. dtype은 `.astype(np.uint8)` 권장. 단 P1 채택 시 A-4 자체가 소멸해 불필요 |
| P3: 균일 경로 O(1) 대체 (A-6) | **처방 수정 필요** | "정수 raw 한정" 명시, 균일 판정은 파일명이 아니라 값 기반(LLRMatrix 속성화), 구현은 별도 함수+조건부 호출(안 ㉰). `__init__` 바인딩(안 ㉯)은 서브클래스 재정의를 무력화해 채택 불가 |
| P1·P2·P3 상호작용 | **P1 먼저 결정** | P2+P3 동시 적용 시 raw==0에서 조용히 갈림. P1 채택 시 P2 불필요, P3는 `sgn·max(min(\|raw\|,top),1)` 형태 |
| B-1: generate_message 호출 제거 | **처방 수정 필요** | strong_error 미해결 + 실물 인코더 도입 시 재발. 프레임 단위 스트림 파생 권장(비용 1.0배). 종료 규칙 배치 종속(V-1)은 별도 Decision |
| C1-F1: 에러 집계 루프 밖 이동 | **처방 반대** (두 해석 모두) | (가)는 오판정 잔존, (나)는 본체 수치 변경 +7.8% 비용. 대안 (ㄴ) 판정비트 배열 권장 — 본체 수치 완전 보존, 오판정 0, 비용 -0.1%, C++ 원본 구조 그 자체 |
| C2-3: 그림 저장 순서 이동 / try-except | **처방 유효 (A+B 병용 권장)** | A만으로는 exit 1 유지. B는 `except Exception`이어야 함 |
| Input/LLR: ㉮ gitignore ㉯ 파일명 dv_max ㉰ 생성 위치 이동 | **셋 다 유효, 배타 아님** | ㉰가 최광범위(두 갈래: run 디렉터리 안 = 구조 변경+재현성 향상 / 고정 폴더 = 변경 최소+㉯ 병행 필요). ㉮는 커밋된 파일에 무효, 플랫폼 종속 단서 |

## 검증 중 신규 발견

| # | 내용 | 심각도 |
|---|------|--------|
| N-1 | `ch = 1`도 파국 (A-1 조건식 밖, 처방 후에도 잔존·악화) | A-1에 병합 |
| N-2 | `ch > dv·top_level`이면 해당 dv column이 영원히 flip 불가 (TD-1·A-11과 동일 뿌리의 일반식) | A-1에 병합 |
| N-3 | `encoder.py:5-6` "이 함수만 채우면 된다" 서술 거짓 — genie가 all-zero 하드코딩, 실물 인코더 도입은 디코더 시그니처·BER 집계까지 파급 | HIGH급 서술 오류 (신규) |
| N-4 | `max_frame_errors` 종료가 배치 경계로 양자화 — 난수 처방과 별개의 배치 종속 | Decision |
| N-5 | `plan.md:22` §1 #5의 2-9 포맷 서술이 현행(DAO 전용)과 어긋남 | TD-7의 실질 근거 |
| N-6 | num_bits 상한 부재로 num_bits=1000이 load_config 통과 후 메모리 폭주 | A-6/B-8에 병합 |
| N-7 | .gitignore 대소문자 매칭 플랫폼 종속 | LOW |

### 종합 판정

**수정 필요.**
확인된 문제: 12건 (부분 확인 4건 포함) / 반박된 문제: 1건 (TD-8) / 부분 확인: 4건 (A-1, TD-1, TD-4, TD-7)
심각도 이동: A-4 HIGH 승격, C2-3 HIGH 상향, TD-7 MEDIUM 하향, TD-8 반박 후 MEDIUM 재구성.
검증 후 HIGH 확정: 13건 (A-1, A-2+A-3, A-4, B-1, C2-3, TD-1, TD-2, TD-3, TD-4, TD-5, TD-6, TD-9, N-3).
동작 변경을 수반하는 수리는 전부 Decision 등급으로 사용자 확인 필요 (P1 채택 여부가 첫 결정).
