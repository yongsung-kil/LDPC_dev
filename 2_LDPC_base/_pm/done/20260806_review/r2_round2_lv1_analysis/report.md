# Round 2 결과: 분석

> 에이전트: 6 (lv1, Opus). 상세: `agent_1.md`(V1) ~ `agent_6.md`(V6)
> 발견 원본 개수: V1 4건, V2 6건, V3 10건, V4 9건, V5 23건, V6 20건 — 중복 통합 후 아래 표

발견 (통합): CRITICAL 0, **HIGH 3 + 조건부 HIGH 4**, MEDIUM 약 24 (중복 통합), LOW 다수

## 주요 발견 (심각도순, 중복 통합)

| # | 심각도 | 문제 | 위치 | 지적 |
|---|--------|------|------|------|
| F1 | HIGH | `_rand_positions`(argpartition)가 뽑힌 k개의 순서 무작위성을 깨뜨려 strong_error 에러 위치가 특정 column block에 극단 편향 (상위 2블록 37.1%, 카이제곱 355만). 원본 rand_sel_ep는 부분 Fisher-Yates | `channel.py:71-73` | V2 |
| F2 | HIGH | matrix 경로에서 `\|C2V\| <= edge_mag[0]=7`이므로 `ch > 7·dv`인 dv 구간은 영구 반전 불가. 현재 LLR 파일 2개 모두 dv=2 ch=28 > 14 → 11.6% 비트 미정정, 현행 config 실험 FER ≡ 1.0. 원인 판정(C++ 도메인 vs 토이 데이터) 미확정, 검출 장치 부재 | `decoder.py:68,388,398` + `Input/LLR/*` | V4 |
| F3 | HIGH | `run` 하위 키가 `.get()`만 사용 — 구 키(`target_errors`, `stop_below`)와 오타가 조용히 무시되고 기본값으로 실행 | `run.py:109-114` | V5 |
| F4 | HIGH(반영 시) | `examples/fer_curve.json` 5개 키 + `fer_curve.py` 전면 파손 | 본체 examples/ | V6 |
| F5 | HIGH(반영 시) | 채널 함수 3종 삭제 → 스크립트 3개 + mpi_runner ImportError/AttributeError | 본체 examples/, mpi_runner.py | V6 |
| F6 | HIGH(반영 시) | `run_fer_point` 인자명 변경 → 호출부 4곳 TypeError | 본체 4곳 | V6 |
| F7 | HIGH(반영 시) | 구 포맷 .qc 2개 로드 불가. `irregular_17x144_z256.qc`는 재생성 경로도 함께 죽어 **자산 소실** | 본체 examples/*.qc, select_irregular.py | V6 |
| F8 | MEDIUM | `_mx_vnu_quantize`/`_vnu_quantize`가 지시함수 합이라 th 내림차순 전제. C++는 캐스케이드 — 비단조 th에서 조용히 갈림 (현재 파일은 전부 내림차순이라 미발현) | `decoder.py:81,94-96` | V1 |
| F9 | MEDIUM | ser/scr/rber 정의역 미검증 (음수 인덱스 조용한 오동작, NaN 전파) | `channel.py:31,89-112` | V2 |
| F10 | MEDIUM | LLR 파서가 줄 기반 — 원 포맷(fscanf 토큰 스트림)보다 좁음. 다중 restart 줄 배치 미검증 | `llr_matrix.py:105-121` | V3 |
| F11 | MEDIUM | `_validate` 제약 4종이 C++ 근거 없는 자체 가정, 합법 파일 거부. 단 겹침 금지 제약은 `_group_of_iter` 정방향 순회의 안전 근거 (제약-순회가 한 쌍) | `llr_matrix.py:73-94` | V3 |
| F12 | MEDIUM | 파일명 모드 판별이 실제 DAO 산출명(`LLR_MATRIX_%d.txt`)과 불일치 — 외부 파일 반입 시 로드 실패 | `llr_matrix.py:34` | V3 |
| F13 | MEDIUM | `cn_mag_fn`(논문 아이디어 훅)이 주 경로(matrix)에서 미호출, `alpha`/`msg_clip`/`quantize` 무경고 무시 | `decoder.py:392,43-70` | V4, V6 |
| F14 | MEDIUM | genie 동점 규칙 경로별 상이 (matrix `<=` vs signed `<`) — signed 경로는 all-zero 전제상 낙관. **V1(각자 도메인에 맞음)과 V4(계통 오차) 이견** | `decoder.py:170,268,398` | V1, V4 |
| F15 | MEDIUM | `assert` 3곳이 `python -O`에서 소멸 — shape 불일치 입력이 조용히 성공 판정 | `decoder.py:129,230,349` | V4 |
| F16 | MEDIUM | `max_iter` 금지가 llr_matrix 없는 설정에도 발동 — max_iter 지정 수단 소멸, plan.md §7 #4(120)와 충돌 | `run.py:48-50` | V5, V6 |
| F17 | MEDIUM | `schedule` 기본값이 llr_matrix 있을 때만 적용 — llr_matrix 한 줄 제거로 스케줄/채널LLR/max_iter 3가지가 무경고 동시 변경 | `run.py:76-82` | V5 |
| F18 | MEDIUM | strong_error는 어떤 설정으로도 실행 불가인데 config.json 기본 포함 + 에러 메시지가 막다른 길 안내. 채널 dict `sd`/`cc` 소비처 0건 | `config.json`, `run.py:89-93` | V5, V6 |
| F19 | MEDIUM | `batch<=0` 무한 hang, `max_frames<=0` ZeroDivisionError | `sim.py:17-24` | V5 |
| F20 | MEDIUM | CSV 무경고 덮어쓰기 + 재현성 메타(시드/설정) 전무, `param` 의미 채널별 상이 | `sim.py:36-43` | V5 |
| F21 | MEDIUM | config.json 기본값이 통계 무의미 (FER 포화 1.0, 첫 배치 종료). 개정본 주 경로가 비퇴화 FER를 한 번도 산출한 적 없음 | `config.json`, Sim_Output/ | V5, V6 |
| F22 | MEDIUM | 필수 키 부재 bare KeyError, 빈 points 조용 통과, 시드 파생 1e-6 접힘 | `run.py` | V5 |
| F23 | MEDIUM | llr_tables.py "제거 후보" 선언 vs decoder 6곳 의존 — 존치 여부 미결정 (Decision) | `decoder.py:50` 등 | V6 |
| F24 | MEDIUM | encoder 스텁 "교체만으로 끝" 서술 오류 — genie가 3경로 모두 all-zero 하드코딩, decode_batch에 cw 인자 없음 | `encoder.py:5-6`, `decoder.py` | V6 |
| F25 | MEDIUM | 문서 불일치: 본체 README 9곳, plan.md 6곳, channels→use 결정 뒤집힘 미기록(Decision), README 검증 수치 2/3 재현 불가, "재배열 완료" 허위, TODO 반영 절차 미등록 | 문서 전반 | V2, V6 |
| — | LOW | 각 agent 파일 참조 (V1 3건, V2 3건, V3 6건, V4 4건, V5 9건, V6 7건) | | |

## 통과 관점 (문제 미발견 확인 범위)

- **V1 C++ 대조 — 디코더**: 13개 대조 항목 전부 원문 행 단위 일치. flip 도메인, C2V sign 3항 XOR 정렬, Edge Clear 범위, CNU insert/remove(`<=`, min2=RESET, min1_pos 특이점까지), VNU 양자화, iteration 0 등가(H·r), CSW 시점, genie 등가성 확인
- **V2 C++ 대조 — 채널 산술**: qfunc_inv 계수 10개 자리까지, dev_from_RBER, HD 경계, R_OFFSET/LLR_th, Get_Mag_2SD/3SD 4-region 일대일, e1/e2/c1/c2 round 규칙, 슬라이스 경계 전부 일치. strong_error 개수 수치(90/22399) 정수 재현
- **V3 파서**: 포맷 정본 로더를 `local_opt.cpp:52-184`에서 발견 — 필드 순서, dv-major 배치(`decoder.cpp:7080` 확정), row 선택(비단조 임계값 포함 합성 대조), max_iter 식, 미사용 필드 처리 전부 원문 일치
- **V4 자체 정확성**: 배치 압축 상태 목록 3경로 전수 완전, 뷰/사본 안전, XOR 순서 정합, CSW×압축 불변, dtype 전반 — 독립 스칼라 레퍼런스 대조 불일치 0건
- **V6**: C++ 행 번호 인용 4건 전부 정확, 인용 심볼 12개 실존, 파손이 조용하지 않음(2개 키 제외), tools/ 무사

## 다음 단계 결정

→ **Round 3 진행 (lv2, 3팀)**
  사유: HIGH 3건(현행) + 조건부 HIGH 4건 존재. 코드 삭제/동작 변경을 요구하는 처방(F11 제약 제거, F1 순서 셔플 추가), 에이전트 간 이견(F14), 원인 미확정(F2) 존재 — 라이트 전환 기준 4행(Round 3 진행)에 해당.

### 검증 배분
- Team A (채널·실행 검증): F1 사실+처방, F3 사실+처방, F19 심각도 재평가
- Team B (디코더·데이터 검증): F2 원인 판정(C++ 도메인 대조)+처방, F8 처방, F11 처방, F14 이견 판정
- Team C (본체 반영 검증): F4~F7 전수성 독립 재확인 + 반영 순서 처방, F23 의존 목록 재확인

### 검증 생략 (Round 2 요약이 정본)
F9, F10, F12, F13, F15~F22, F24, F25 — 실행 실측/grep으로 근거 자명, 처방이 추가 방어 코드 수준이라 뒤집힐 여지 없음. LOW 전건 생략.
