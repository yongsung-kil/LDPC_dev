# Round 3 결과: 검증

> 팀: 3 (lv2, Opus 리더 + 워커 9). 상세: `team_a_verification.md`, `team_b_verification.md`, `team_c_verification.md`, `worker_*.md`
> 검증 대상 12건 (CRITICAL/HIGH 전건 + 처방 검증 필요 + 이견 항목). 나머지는 Round 2 요약이 정본.

## 발견별 판정

| # | 원 심각도 | 문제 | 판정 | 심각도 조정 | 처방 판정 |
|---|-----------|------|------|-------------|-----------|
| F1 | HIGH | argpartition 순서 편향 → strong_error 위치 쏠림 | **확인됨** (독립 재현, 카이제곱 2.44M, 원문 rand_sel_ep 대조) | **HIGH(2SD 디코딩 구현 시)** 조건 병기 — 현재는 도달 불가 경로 | **처방 수정 필요**: `_rand_positions` 내부 permuted는 fixed_error 비트 재현성을 깨뜨림(배치 1부터). `strong_error_channel`에서만 `rng.permuted(p, axis=1)` 적용(1순위) 또는 argsort 전면 교체(2순위, 4.5배 비용) |
| F2 | HIGH | matrix 경로 dv=2 영구 미정정, 현행 config FER≡1 | **부분 확인** — 현상 확인("전량"은 과장, 실측 88.9~96.6%), 원인 재분류: **도메인 불일치 반박** (C++도 5-bit ch + 3-bit EDGE 혼합 가산, `decoder.cpp:4026,4041,2402-2410`; 벤더 3-bit 테이블 63 row 전부 `{21,14,12,10}`으로 dv=2 ch=10 ≤ 14 → `ch <= 7·dv`가 암묵 설계 불변식, 토이 파일이 위반) | **HIGH 유지** (토이 데이터 + 검출 장치 부재) | **처방 유효 + 보강 2건**: 경계는 `>` (ch=7·dv는 반전 가능, 실측), `self._col_dv`×`code.col_deg`로 column 단위 검사. 데이터 조치 병행(dv=2 ch를 벤더 참고값 10 수준으로), README:114-117 4곳 수정 |
| F3 | HIGH | run 하위 키 조용한 무시 | **확인됨** (설정 변형 30종 재현, 합법 키 6개 확정) | HIGH 유지 | **처방 부분 유효**: run 화이트리스트는 누수 7종 중 1종만 차단. **신규 발견 — `decoder` 블록 이름 오타 시 디코더 통째 교체 후 조용히 완주** (FER 0.9844→0.0000, `run.py:47` setdefault). 최상위 키 화이트리스트 병행 + 기본값 dict 단일 정본 방식 권고 |
| F4 | HIGH(반영 시) | fer_curve.json+py 파손 | **확인됨** (허위 0건, 조용한 무시가 결과 바꾸는 것까지 실증) | 유지 | 유효. fer_curve.py는 키 교체로 못 살림 — 2패널 설계 자체가 단일 채널 반환과 충돌, 재설계 필요 |
| F5 | HIGH(반영 시) | 채널 함수 3종 삭제 파손 | **확인됨** (순서 1건 정정: select_irregular/mpi_runner는 TypeError가 AttributeError보다 먼저 — 두 결함 동시 수리 필요) | 유지 | 유효 |
| F6 | HIGH(반영 시) | run_fer_point 인자명 TypeError 4곳 | **확인됨** | 유지 | 유효. mpi_runner 수리 시 `my_frames==0` 랭크 스킵 함께 (`frames // size` 0 가능 — 신규) |
| F7 | HIGH(반영 시) | .qc 로드 불가 + irregular 자산 소실 | 로드 불가 **확인**, **자산 소실 반박** — git 추적 중(`git ls-files`), 헤더 3줄 재작성으로 변환, `build_code(seed=103)` 바이트 재현까지 3중 복구 가능 | **HIGH → MEDIUM** | **처방 수정 필요**: 본체 pcm.load가 양 포맷 수용이므로 **덮어쓰기가 정답**(사본 방식 반대), ".qc 변환 최우선" 근거 소멸. 수정된 순서: ① `.gitignore` `H_Matrix/` 범위 축소 ② 개정본 커밋 ③ Decision 3건 병렬 ④ 코드 이동 ⑤ .qc 덮어쓰기 변환 ⑥ examples/mpi_runner 갱신 ⑦ 문서·Sim_Output |
| F8 | MEDIUM | VNU 양자화 th 내림차순 전제 | **확인됨** (C++는 정렬 검사 없이 캐스케이드 소비 — 비단조 th에서 v2c 14.5~56.2% 상이 실증) | 유지 | **처방 수정**: 검사·거부(갈래1)는 C++이 받는 파일을 거부 → 반대. **캐스케이드 교체(갈래2)** 채택하되 np.select(1.34배 느림) 대신 **중첩 np.where**(0.50배, 전체 9.1% 단축). `_vnu_quantize`/`_mx_vnu_quantize` 양쪽. 검사는 경고까지만 |
| F11 | MEDIUM | _validate 제약 4종 근거 없음 | **부분 확인** (사실 확인, 처방 방향 2곳 오류) | 유지 | **처방 수정**: ㉮ 겹침 금지 **유지**(C++ 역방향 순회와 한 쌍, 주석 필수) ㉯ iter1 강제는 제거 아닌 **1..max_iter 커버리지 검사로 교체**(iter_start=0 허용) ㉰ restart 단일화 **제거** ㉱ restart 마지막 금지는 **경고로 완화**(restart iteration 자체가 512중 445프레임 성공 판정 실증) |
| F14 | MEDIUM | genie 동점 규칙 경로별 상이 | **반박됨 (결함 아님)** — C++ VN 판정 5곳 전부 `sum_t > 0`(동점 반전), signed 도메인 원문 부재 → V1 판정이 옳음. V4 우려(계통 오차)는 실측으로 크기 확인(워터폴 FER 상대 7%) — 양립 | 결함 목록에서 제외 | **현행 유지 + 문서화** (`<=` 통일 반대 — 편향 방향만 뒤집힘: 무작위 기준선 0.1536이 `<` 0.1458과 `<=` 0.1562 사이). 근본 해법은 실제 인코더 도입(별건) |
| F19 | MEDIUM | batch<=0 무한 hang | **부분 확인** — hang 재현되나 유발값은 **정수 0 하나뿐**(음수/실수/None은 즉시 예외) | **CRITICAL(batch=정수 0)** 조건 병기 (기준표 문언 충실). 수정 순위는 F1~F3 뒤 (즉시 가시적, Ctrl+C 복구, 데이터 무손상) | 유효 + 확장: 가드는 **sim.py 진입부 필수**(직접 호출 4곳이 load_config 우회), 타입 검사 선행, max_frames/max_frame_errors 묶음 처리 |
| F23 | MEDIUM | llr_tables 제거 불가 (6곳 의존) | **부분 확인 + 결론 반박** — 허위 0건이나 인용 2곳 부정확 + 3곳 누락(실제 9곳). 모듈 import는 `decoder.py:50` 1곳, 심볼 `dv_group` 하나 → "제거 불가" 인과 불성립 | 유지 | 실제 안건은 **`llr_profile` 모드 존폐 단일 Decision**. 폐기 시 `llr/_hw_orig_ch.txt`의 원본 실값(CH_HD 21/14/12/10) 문서 이관 선행 필수 |

## Round 3 신규 발견

| # | 내용 | 출처 | 성격 |
|---|------|------|------|
| N-A1 | `decoder` 블록 이름 오타 → 디코더 통째 교체 조용히 완주 (F3에 통합, 파급은 F3 본체보다 큼) | team_a | HIGH급 |
| N-A2 | `mpi_runner.py:55` `frames // size`가 0이 되는 실 경로 (F6 수리 시 함께) | team_a | MEDIUM |
| N-B1 | `mode.h:8` 주석 처리 + build.bat MSVC → **저장소 현 상태로는 `__AUTO_LLR_OPT__` 빌드가 만들어지지 않음** — "AUTO 빌드가 정확성 기준"이라는 전제에 직접 걸림 | team_b | 별도 항목 등록 권고 |
| N-C1 | `1_LDPC_revised/.../measure_speed.py` 동적 임포트 의존 (일부는 개정 전부터 파손 — 오인 금지) | team_c | MEDIUM(반영 시) |
| N-C2 | `output.dir` 기본값 조용한 이동 (본체 `base_dir` → 개정본 `base_dir/Sim_Output`) | team_c | LOW |
| N-C3 | **`.gitignore:40` `H_Matrix/` + `core.ignorecase=true`가 `Input/H_matrix/`를 삼킴** — 반영 절차가 새 자산 소실을 만듦 | team_c | HIGH(반영 시) |
| N-C4 | irregular dv=10 vs LLR_MATRIX dv 구간 `[11,4,3,2]` 싱글턴 → 변환해도 주 경로 사용 불가 | team_c | Decision |
| N-C5 | DV 내림차순 전제 미강제 (`pcm.py:15` 선언만, 위반 시 완전 조용) | team_c | MEDIUM |
| N-C6 | 재현 시드(103) 기록처가 미추적 CSV뿐 — 문서 이관 권고 | team_c | LOW |

### 종합 판정

**수정 필요** (커밋/본체 반영 전 조치 필요)
확인된 문제: 6건 / 부분 확인: 5건 / 반박된 문제: 1건 (F14) + 부분 반박 2건 (F7 자산 소실, F23 제거 불가 인과)
