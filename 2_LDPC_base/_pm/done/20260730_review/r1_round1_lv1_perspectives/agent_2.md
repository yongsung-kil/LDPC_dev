# Round 1 — 리뷰 관점 도출 (agent_2)

> 대상: `docs/2_LDPC_light/plan.md` (주), `TODO.md` §백로그 "2_LDPC_light" (부)
> 성격: 코드 없음 / 설계 계획 문서 리뷰. 아래는 "어디를 봐야 하는지"만 정리 (문제 지적 아님).

---

## P1. 사실 정확성 — 인용한 C++ 심볼·파일·경로

**왜 보나**: 계획 문서 §3.1 대응표와 §2 유지/제거 대응표가 C++ 코드의 함수명·파일명·구조체명을 근거로 삼고 있다. 이 이름들이 실제와 다르면 구현자가 잘못된 곳을 포팅한다.

**확인 항목**
- §3.1 표의 "C++ 대응" 칸에 적힌 이름이 실존하는가: `ecc_data.h`의 `PARAM_DEC`/`PARAM_LLR`, `ecc_top.cpp`의 `Load_PCM()`, `input.cpp`, `channel.cpp`의 `Set_R_Offset()`/`Set_LLR_Th()`, `decoder.cpp`의 `LDPC_Decoder()`/`C2V_Cal()`/`VN_Cal_*()`
- "`decoder.cpp` LLR 테이블 로드"가 실제로 `decoder.cpp`에 있는지 (2-9 항목이 `decoder.h`/`decoder.cpp` 양쪽을 건드렸음)
- §3.2가 인용한 "C++ 4-3의 CN_STATE" 필드 구성(min1, min2, min1_idx, sign)이 실제 `CN_STATE` 정의와 일치하는가 — 특히 필드명 `min1_idx` vs 코드상 `REG_min1_pos` 계열
- §2의 "min1/min2 + sign", "col_M1~P4", "punct_col_num=2", "HCU 127/128" 등 상수·명칭이 프로젝트 `CLAUDE.md` 상수표 및 코드와 일치하는가
- **대상**: `LDPC/decoder.{h,cpp}`, `LDPC/ecc_top.cpp`, `LDPC/channel.h`, `LDPC/ecc_data.h`, `docs/speed_opt/4-3_cn_state_struct.md`, `docs/speed_opt/2-9_llr_table_parameterize.md`

---

## P2. 사실 정확성 — "제거해도 FER 무관"이라는 분류 근거

**왜 보나**: §2 대응표의 핵심 주장은 "제거 대상은 HW 구조 요소라 FER에 영향 없다"는 것이다. 이 분류가 틀리면 calibration 자체가 성립하지 않는다. 각 행의 "근거"가 코드 동작으로 뒷받침되는지 개별 확인이 필요하다.

**확인 항목**
- `col_M1~P4` 파이프라인 제거: 파이프라인 지연이 단순 timing인지, 아니면 **layered 갱신 시점의 데이터 해저드(직전 column 결과가 몇 clock 뒤에 반영되는가)를 만들어 실제 메시지 값에 영향을 주는지**. 영향이 있으면 "timing 전용, 알고리즘 무관"이라는 근거가 흔들린다.
- `GT` 제거: 계획은 "클록당 edge 스케줄링 = HW 전용"이라 적었다. GT가 (a) 처리 순서만 바꾸는 MUX 스케줄인지 (b) 실제로 edge를 솎아내어 메시지 일부를 버리는지 확인 필요. 후자면 FER에 직접 영향.
- `PMU` / `Delay_2clk` / `overall_clk` 계열이 복호 결과 경로에 값을 되먹이는 곳이 있는지 (6-1 항목에서 PMU가 `factor`를 반영한다는 기록이 있음)
- `Dual-Update` off: parity even/odd 교대 스케줄을 끄면 **수렴 특성이 바뀌므로 FER이 달라진다**는 점이 문서에 명시돼 있는지, "실제 적용 형태와의 격차는 최종 C++ 검증에서 흡수"라는 처리가 스크리닝 판정 신뢰도에 어떤 조건을 거는지
- **대상**: `plan.md` §2 표 전체, `LDPC/CLAUDE.md`, `docs/paper_screening_profile.md` §3, `LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md`, `docs/speed_opt/6-1_6-2_oob_fixes.md`

---

## P3. 기술적 타당성 — all-zero codeword 대칭성 논거

**왜 보나**: §3.1과 §7 #2가 "대칭 채널 + 대칭 복호기에서는 all-zero로 FER 측정 가능 → 인코더 불필요"라고 단정한다. 이 정리(all-zero assumption)는 성립 조건이 있고, 이 코드의 양자화 구조가 그 조건을 만족하는지가 관건이다.

**확인 항목**
- 문서가 "대칭"의 성립 조건을 명시했는가 (채널 대칭성 + 복호 갱신 규칙의 부호 대칭성 + 판정 tie-break 규칙)
- 양자화가 대칭성을 깨지 않는가: `Set_R_Offset()`의 offset, HD/2SD/3SD threshold 배치, `Ch_LLR_*` 테이블이 0을 중심으로 대칭인지 (비대칭 offset이 있으면 all-zero 결과가 평균적 FER과 어긋날 수 있음)
- Min-Sum의 `min1_value <= v2c_mag` 형태 tie 처리, magnitude 포화(saturation) 등 **부호에 따라 비대칭이 되는 지점**이 있는지
- all-zero를 쓰면 §3.1b의 예시 부호(dual-diagonal)에서 **인코더 정확성 자체는 전혀 검증되지 않는다**는 점을 문서가 인지·기록했는가
- **대상**: `plan.md` §3.1 마지막 불릿 / §7 #2, `LDPC/channel.cpp`, `LDPC/decoder.cpp` VNU 양자화 경로, `1_LDPC_revised/llr_tables_template.txt`

---

## P4. 기술적 타당성 — 성공 판정(genie) 정의와 FER 정의의 정합

**왜 보나**: §1 #4는 "송신 codeword와 bitwise 비교", §7 #1은 "매 iteration hard decision을 정답과 비교, 일치 시 그 프레임 성공 확정(genie)"이다. 조기종료를 제거해 "고정 iteration"이라고 한 §2와 함께 읽으면 세 서술이 같은 것을 말하는지 확인이 필요하다.

**확인 항목**
- "고정 iteration"(§2)과 "일치 시 즉시 성공 확정"(§7 #1)이 모순되지 않는가 — 후자는 사실상 genie 조기종료이며, **최종 iteration의 hard decision만 보는 FER과 값이 다르다**
- C++ vanilla 쪽 판정도 동일하게 genie로 맞출 것인지 (§4 C2 FER 곡선 비교의 전제) — C++는 Partial/Full CRC 판정을 쓰므로 판정 기준이 다르면 C2가 성립하지 않음
- FER 분모 정의(프레임 수), 신뢰구간(§4 C2 "95% 신뢰구간") 계산식·필요 에러 개수 기준이 문서에 있는가
- 정정능력 커브(§3.1b `examples/fer_curve.py`)의 x축이 SNR인지 RBER인지, C++의 `MODE_CH_RBER` → `dev_from_RBER()` 변환과 동일 규약인지
- **대상**: `plan.md` §1 #4 / §2 조기종료 행 / §4 / §7 #1, `LDPC/ecc_top.cpp` (RBER→dev 경로), `LDPC/channel.h`

---

## P5. 기술적 타당성 — 배열 축 설계와 column-layered 스케줄의 정합

**왜 보나**: §3.2가 벡터화 축을 `(B, N_b, z_sb)` / `(B, dv, z_sb)`로 잡고, column 루프는 Python 루프로 남긴다고 했다. layered 스케줄은 **column 간 순차 의존**이 있으므로 어떤 축이 실제로 병렬화 가능한지가 성능·정확성 양쪽에 직결된다.

**확인 항목**
- CN 상태 배열의 축이 명시돼 있는가 — 채널 LLR은 `(B, N_b, z_sb)`로 적혀 있으나 **CN 상태는 행(M_b × z_sb) 기준**이라 축이 다르다. old/new 2세트라는 서술만 있고 shape가 없음
- circulant shift 처리를 "사전 계산 인덱스 배열 또는 `np.roll`"로 적었는데, **column-layered에서 shift가 CN 축과 VN 축 중 어디에 적용되는지**, 두 방식 중 무엇을 쓸지 확정돼 있는가
- 한 column을 처리할 때 갱신되는 CN 집합이 z_sb 방향으로 서로 독립인지 (독립하지 않으면 `(B, dv, z_sb)` 일괄 연산이 순차 의존을 건너뛴다)
- "remove-old / add-new 갱신 방식을 그대로 재현"이 min1/min2 레지스터에서 **정보 손실 없이 numpy로 재현 가능한지** (min1 제거 시 min2로 대체하는 근사가 벡터화 시에도 동일 결과를 주는가)
- 스펙 소스로 지목한 L2 문서가 그 수준의 상세를 실제로 담고 있는가
- **대상**: `plan.md` §3.2, `LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` (§min REG 갱신, checksum old/new), `docs/speed_opt/2-1_shift_mem.md`

---

## P6. 기술적 타당성 — 병렬화·처리량 목표의 현실성

**왜 보나**: 목표 FER 영역이 1e-2~1e-4(§첫머리)인데, codeword 33,024 bit + column 129회 × iteration의 Python 루프다. 처리량 산정 근거가 없으면 계획 전체가 실행 불가 규모일 수 있다.

**확인 항목**
- "코어 수 × 배치 벡터화(10~30배)"라는 §3.3 수식의 근거 — 배치 크기 32~128(§3.2)에서 왜 10~30배인지, 측정인지 추정인지 표기돼 있는가
- FER 1e-4 관측에 필요한 프레임 수 × 프레임당 연산량으로 본 **예상 소요 시간 추정치가 문서에 있는가** (없으면 스크리닝 실효성 판단 불가)
- Python 루프 횟수(129 col × max_iter × 프레임 배치 반복)가 numpy 호출 오버헤드 대비 타당한지 — 배치를 키워 상쇄하는 구조인지
- numba 미사용(§7 #6) 결정과 위 처리량 목표가 양립하는가, 재검토 트리거 조건이 적혀 있는가
- mpi4py fallback(§3.3)의 동작 정의 — 단일 프로세스 경로에서 시드 분할 규약이 어떻게 되는가 (재현성)
- **대상**: `plan.md` §3.2 / §3.3 / §7 #6

---

## P7. 실행 가능성 — Calibration 절차(C0~C3)의 선행 조건과 수단

**왜 보나**: §4는 "아이디어 투입 전 필수 관문"이라고 못 박았다. 이 절차가 실제로 수행 가능하려면 필요한 입출력 수단(덤프 기능, 빌드/실행 환경)이 존재해야 한다.

**확인 항목**
- **C1의 "C++에서 채널 LLR을 파일로 덤프"** — 그런 덤프 기능이 현재 C++에 있는가, 없다면 `ldpc_vanilla/`에 신규 추가해야 하는 작업으로 §5 진행 순서에 잡혀 있는가
- **C1의 "iteration별 hard decision 비교"** — C++ 쪽에서 iteration별 hard decision을 뽑는 수단이 무엇인가 (TV 출력은 제거 대상이고, `__ECC_TV_ITER__`는 TV Gen 모드 전용일 수 있음)
- **빌드·실행 주체** — 프로젝트 `CLAUDE.md`는 "현재 빌드 불가(소스 손상)", §6 안전성 체크리스트는 "이 환경에서 C++ 빌드/실행하지 않음"이라고 적혀 있다. 그러면 C0~C3를 **누가 어디서 실행하는지**가 문서에 명시돼 있는가
- C0가 "별도 작업"으로만 적혀 있는데, `ldpc_vanilla/` 파생 범위(제거할 컴파일 스위치·코드 목록)가 정의돼 있는가
- **`1_LDPC_revised/`는 수정된 파일만 담긴 부분 복사본**(README 명시)이다. "1_LDPC_revised 최신 상태 기반 `ldpc_vanilla/`"를 만들려면 `LDPC/` 원본과의 병합이 선행되는데, 그 단계가 계획에 있는가
- C1 실패 시 무엇을 하는지(디버깅 절차/중단 기준)가 있는가
- **대상**: `plan.md` §4, §5, §6, §7 #3, `1_LDPC_revised/README.md`, `CLAUDE.md` §빌드 방법, `LDPC/mode.h`

---

## P8. 실행 가능성 — 입력 자산(H-matrix, LLR 테이블) 확보 가능성

**왜 보나**: §1 #5·#6과 §5 3단계가 "실물 파일 확인 후"에 의존한다. 그 파일이 실제로 존재하지 않으면 계획의 절반이 blocked 된다.

**확인 항목**
- **z_sb=256 대상 H-matrix가 repo/환경에 실제로 있는가** — §7 #5가 "유일한 열린 항목"이라 했는데, 없을 경우의 대안(§3.1b 예시 부호로 대체)이 명시돼 있는가
- **LLR 테이블 실물 값** — `1_LDPC_revised/llr_tables_template.txt` 헤더는 "CH_3SD/TH_* 는 소스 손상으로 코드 내장값이 소실됨(기본 0) — 반드시 원본 값으로 채울 것"이라 적고 있고, `TODO.md` 사후 검증 항목도 "llr_tables.txt에 HW 원본 값 공급"을 미완으로 둔다. 계획 §1 #5의 "기 최적화 값 사용"이 이 상태와 정합하는가
- 템플릿의 행/열 크기(CH_HD 63×4, CH_2SD 36×8, CH_3SD 66×16, TH_* ×12)가 **빌드 상수(common.h) 의존**이라고 적혀 있는데, Python 로더가 이 상수를 어디서 얻는지 계획에 있는가
- H-matrix 파일 헤더가 `N_b, M_b, J, K, z_sb` 5개 정수로 시작하는 포맷인데, §3.1b 생성 도구가 이 포맷을 정확히 따르도록 스펙이 적혀 있는가 (프로젝트 `CLAUDE.md` "절대 건드리면 안 되는 것" 4번 = H-matrix 파일 포맷)
- 2-1 주의사항("shift 값이 0~z_sb-1 범위 전제")이 생성 도구에도 적용되는지
- **대상**: `plan.md` §1 #5·#6, §3.1b, §5 3단계, §7 #5, `1_LDPC_revised/llr_tables_template.txt`, `LDPC/ecc_top.cpp:251-273` (`Load_PCM`), `TODO.md` 주의사항

---

## P9. 범위 완전성 — FER에 영향 주는데 계획에 없는 요소

**왜 보나**: §2 표가 "유지/제거" 이분법으로 정리했는데, 표에 아예 등장하지 않는 항목이 있으면 py와 C++ vanilla가 조용히 달라진다.

**확인 항목 (표에 없거나 서술이 없는 것 위주로 점검)**
- **HCU 제거 후 127/128 column을 어떻게 처리하는가** — 그 column들은 degree가 9/7로 비대칭이다. 일반 column과 동일 처리인지, H-matrix 자체를 바꾸는지 명시 필요
- **쇼트닝/펑처링 제거가 code rate·codeword 길이·정보 비트 수를 바꾼다** — 바뀐 rate 기준으로 SNR/RBER를 어떻게 정의하는지 (rate 보정 여부)
- **max_iter 값**, iteration 정의(전체 iter vs mini-iter `mn`), **LLR 테이블의 iteration 구간 매핑**(`Get_VNU_Table_Idx`가 decoding status 기반이라면 조기종료 제거가 테이블 인덱스에도 영향)
- **양자화 비트수 / 포화(clipping) 규칙 / 오버플로 처리** — §3.1 `config.py`에 "양자화 비트"만 있고 규칙은 없음
- **VN degree 분포·시작 LLR 초기화** 규약
- 2SD/3SD의 `CC`/`CD` 채널 신호(C++ `Make_Dec_Input_AWGN`이 `HD/SD/CC/CD` 4종을 만든다)가 py에서 어떻게 대응되는가
- 재현성 자산: 시드 기록·결과 저장 포맷·실험 메타데이터(부호/테이블/파라미터 해시) 규약
- **대상**: `plan.md` §2, §3.1 `config.py` 행, `LDPC/ecc_top.cpp` `Make_Dec_Input_AWGN*`, `LDPC/decoder.cpp` `Get_VNU_Table_Idx()`

---

## P10. 범위 완전성 — 예시 부호 생성 도구(§3.1b)의 스펙 완결성

**왜 보나**: 나중에 추가된 절이라 다른 절과의 결합이 느슨할 수 있고, 이 도구의 산출물이 §5 2단계 end-to-end 자가 검증의 유일한 근거다.

**확인 항목**
- 예시 부호 파라미터 "N_b=129, M_b≈13, z_sb=256, rate≈0.9"의 **내부 정합** — rate ≈ (N_b−M_b)/N_b 로 보면 (129−13)/129 ≈ 0.90. 이 계산이 맞는지, 그리고 프로젝트 `CLAUDE.md` 상수표의 `M_b = 129`(= N_b)와의 관계를 문서가 설명하는가 (`paper_screening_profile.md` §2도 "N_b/M_b 표기에 내부 불일치 있어 정확값 미검증"이라고 이미 경고하고 있음)
- **dual-diagonal parity 구조**를 PEG 결과 위에 어떻게 얹는지 — PEG는 정보부만 만든다고 적혀 있는데, parity부 결합 시 girth 보장이 유지되는지
- lifting의 "짧은 사이클 회피 검사" 기준(ACE, girth 목표값)이 정해져 있는가
- 생성 도구의 **검증 방법** — 만든 H-matrix가 full rank인지, rate가 목표대로인지, 디코더가 로드 가능한지 확인 단계가 있는가
- 예시 실행의 "기본 양자화 프로파일"이 무엇인지 정의돼 있는가 (실물 테이블 없을 때 커브가 무엇을 의미하는지)
- 정정능력 커브의 출력 포맷·그래프 라이브러리 의존성(matplotlib 등)이 명시돼 있는가
- **대상**: `plan.md` §3.1b, §5 2단계, `docs/paper_screening_profile.md` §2

---

## P11. 구조 일관성 — 절 구성·중복·날짜

**왜 보나**: 두 차례(07-29, 07-30)에 걸쳐 갱신된 문서라 결정 사항이 여러 절에 흩어져 있다.

**확인 항목**
- **§1 "확정된 결정 사항"과 §7 "확정 사항"의 중복·충돌** — §1 #4(bitwise 비교) vs §7 #1(genie 매 iteration), §4 C0 vs §7 #3(`ldpc_vanilla/` 기반) 등 같은 주제가 두 곳에 있다. 어느 쪽이 최신인지 독자가 판단 가능한가
- 문서 머리말 "생성일: 2026-07-29"와 본문의 07-30 갱신 내용 — 갱신일 표기 규약
- **§3.1b라는 절 번호** — 다른 절은 정수/소수 번호인데 문자 접미사를 쓴다. 프로젝트 다른 문서(`docs/speed_opt/*`, `docs/architecture.md`)의 절 번호 관례와 일치하는가
- §2 표의 Dual-Update 행에만 결정일(2026-07-30)이 붙고 다른 행에는 없음 — 표기 통일
- §6 안전성 체크리스트가 전부 미체크 `[ ]`인데, 이 문서 시점에 체크 가능한 항목이 있는지 (체크박스 의미가 "계획 단계 확인"인지 "구현 후 확인"인지)
- 표 열 구성·용어(제거/유지/off) 표기 통일
- **대상**: `plan.md` 전체, 비교군 `docs/speed_opt/checklist.md`, `docs/architecture.md`

---

## P12. 상호참조 — 링크 유효성·TODO 정합·용어 통일

**왜 보나**: 계획 문서가 4개 외부 문서를 상대경로로 참조하고, `TODO.md`에도 동일 계획이 요약돼 있다.

**확인 항목**
- 링크 4건의 경로 유효성: `../paper_screening_profile.md`, `../../1_LDPC_revised/llr_tables_template.txt`, `../../LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` — 실재 여부와 상대 깊이
- **`TODO.md` §백로그 2_LDPC_light 항목의 서브태스크 목록이 `plan.md` §5 진행 순서와 1:1 대응하는가** (TODO에는 "계획 문서 라이트 리뷰" 항목이 있으나 plan §5에는 없음 등)
- TODO 요약문("HCU/쇼트닝·펑처링/조기종료/timing·SRAM·PMU·TV 제거, bitwise 판정, z_sb=256")이 §7 확정 사항(genie 판정, Dual-Update off)까지 반영하는가
- **용어 불일치**: `GT`를 이 문서는 "Graph Thinning"이라 쓰는데 `LDPC/CLAUDE.md`는 "Gaussian Trick"으로 적고 있다. 어느 쪽이 맞는지, 문서 간 통일 필요 여부
- 전역 규칙(글로벌 CLAUDE.md) "**약어·조어를 임의로 쓰지 말고 처음 쓸 때 풀어서 정의**" 준수 여부 — 현재 문서에서 정의 없이 등장하는 것: `genie`, `PEG`(괄호 설명 있음), `lifting`, `circulant shift`, `girth`(괄호 설명 있음), `Allreduce`, `fallback`, `waterfall`, `bit-exact`, `vanilla`, `hook/훅`
- 프로젝트 `CLAUDE.md` §네이밍 표(`jj`, `mn`, `G_idx` 등)와 계획 문서가 쓰는 이름의 정합
- **대상**: `plan.md` 머리말·§2·§3.2, `TODO.md:129-141`, `LDPC/CLAUDE.md`, `CLAUDE.md` §네이밍, 글로벌 `CLAUDE.md` §상호작용 규칙

---

## P13. 프로젝트 규칙·리스크 관리

**왜 보나**: 이 repo는 "절대 건드리면 안 되는 것" 목록과 변경 등급 체계, 문서 공개 전제(타인 열람 가능)를 갖고 있다.

**확인 항목**
- §6 안전성 체크리스트가 프로젝트 `CLAUDE.md` "절대 건드리면 안 되는 것" 4개 항목(TV hex 포맷 / HCU 버퍼 레이아웃 / Partial CRC 다항식 / H-matrix 파싱)을 모두 커버하는가 — 특히 §3.1b 생성 도구가 **H-matrix 파일 포맷을 새로 쓰는(write) 쪽**이라는 점이 "읽기만"이라는 서술과 맞는가
- 새 폴더 `2_LDPC_light/`, `ldpc_vanilla/`가 `.gitignore`·저장소 정책과 충돌하지 않는가 (`_test/` 규칙과의 관계, 산출 데이터/그래프 파일의 커밋 여부)
- **변경 등급 판정** — 신규 폴더 2개 + 병렬 실행 인프라는 Decision 급인지 Review 급인지 문서가 밝히고 있는가
- 문서 공개 전제상 부적절한 내용(개인 경로, 사내 비공개 정보, 외부 프로젝트 언급)이 없는가
- **미결정/리스크 추적** — §7 #5(시뮬 파라미터)만 열린 항목으로 남았다고 했는데, P7~P8에서 나온 선행 조건들(덤프 기능 존재, 실물 파일 존재, 빌드 주체)이 미결정 목록에 반영돼 있는가. calibration 실패·자산 부재 시 폴백 경로가 있는가
- **대상**: `plan.md` §6, §7, `CLAUDE.md` §절대 건드리면 안 되는 것 / §변경 등급, `.gitignore`, `TODO.md`

---

## 우선순위 제안

| 순위 | 관점 | 이유 |
|------|------|------|
| 1 | P7 실행 가능성(Calibration) | 성립 안 하면 계획 전체가 멈춤. 필수 관문이라고 문서 스스로 규정 |
| 2 | P2 제거 항목 FER 무관 근거 | 틀리면 py/C++ 비교의 전제가 무너짐 |
| 3 | P8 입력 자산 확보 | LLR 실물 값·z_sb=256 H-matrix 부재 리스크가 문서상 이미 시사됨 |
| 4 | P4 판정 정의 정합 | §1/§2/§7 서술이 서로 다른 것을 가리킬 여지 |
| 5 | P9 범위 완전성 | HCU 제거 후 처리·rate 변경 등 미기재 가능성 |
| 6 | P3, P5, P6, P10 | 기술적 타당성 (구현 착수 전 확정 필요) |
| 7 | P1, P11, P12, P13 | 정확성·일관성·규칙 (수정 비용 낮음) |
