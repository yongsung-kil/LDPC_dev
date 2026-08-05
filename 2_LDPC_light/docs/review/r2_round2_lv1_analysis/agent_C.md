# Round 2 — 축 C: 실행 가능성 · 범위 완전성

> 대상: `docs/2_LDPC_light/plan.md`
> 검토 시각: 2026-07-30 00:40:09
> 방식: plan.md 서술을 `LDPC/` 원본 소스·`1_LDPC_revised/`·`TODO.md`와 대조. 코드 수정 없음(읽기만).

## 확인 범위

`LDPC/`의 `main.cpp`, `ecc_top.cpp`, `decoder.cpp`, `encoder.cpp`, `channel.cpp`, `input.cpp`,
`common.h`, `mode.h`, `ecc_data.h`, `TV_Dec.{cpp,h}` 및 `1_LDPC_revised/{README.md, decoder.cpp, llr_tables_template.txt}`,
`TODO.md`, 저장소 전체 파일 목록(비-md/비-obj 88개).

---

## 발견 요약

| # | 심각도 | 한 줄 |
|---|--------|-------|
| C-1 | CRITICAL | 필수 관문 C0~C3가 저장소에 없는 3개 외부 산출물에 동시 의존하는데 계획이 이를 전제로 명시하지 않음 |
| C-2 | HIGH | z_sb=256용은커녕 **H-matrix 파일이 저장소에 하나도 없음** — §5-3은 "확인"이 아니라 외부 반입 |
| C-3 | HIGH | `llr_tables_template.txt`는 값이 비어 있고 CH_3SD/TH_* 원본값은 소스 손상으로 소실 — §1 #5 성립 불가 |
| C-4 | HIGH | `Get_VNU_Table_Idx()`가 `return 0` 스텁 — "iteration별 LLR 테이블" 세트 선택 규칙이 소스에 없음 |
| C-5 | HIGH | `1_LDPC_revised/`는 11개 파일 부분 복사본 + 원본 빌드 BLOCKED → `ldpc_vanilla/` 파생·빌드 주체가 계획에 없음. §7 #3의 "검증 완료" 서술도 부정확 |
| C-6 | HIGH | N_b=129는 오기 — 129는 `N_b − M_b`(정보 블록 수). codeword 길이·배열 축·rate·예시 스케일이 모두 어긋남 |
| C-7 | HIGH | `channel.py`의 역할 오배치 — 채널은 양자화 영역만 산출하고 LLR 크기는 VN 단계에서 (dv, col region, set) 테이블로 결정됨 |
| C-8 | MEDIUM | C1의 "iteration별 hard decision" 덤프 수단이 Ref-C에 없음(오류 **개수**만 존재), 계획도 이 추가 작업을 누락 |
| C-9 | MEDIUM | §2 표 누락 FER 영향 요소 5종 (Power stopping, BF 모드, HD 5/8 Set, `__SHUFFLED_DUAL_DIAG__`, punct recovery) |
| C-10 | MEDIUM | HCU 컬럼(=펑처링된 정보 컬럼 2개)을 vanilla에서 어떻게 다루는지 미기재. 9/7 분할은 H 속성이 아니라 하드코딩 상수 |
| C-11 | MEDIUM | 쇼트닝/펑처링 제거 시 rate·정보길이 변화 정리 규칙 없음 |
| C-12 | MEDIUM | §3.1b 생성 부호의 유효성 수용 기준(girth 목표, 랭크, shift 범위)이 없음 |
| C-13 | LOW | §3.1 표 `pcm.py ← input.cpp` 오기 — H-matrix 파싱은 `ECC_Top::Load_PCM`에만 존재 |
| C-14 | LOW | §3.3 MPI fallback이 요구사항 문장뿐, 모듈 소유권 규정이 없어 설계로 못 박히지 않음 |

**문제 없음으로 확인한 항목**: H-matrix 텍스트 포맷의 z_sb=256 표현 가능성(§3.1b-a), dual-diagonal과 M_b≈13 조합 가능성(§3.1b-b), 참조 문서 링크 4건 실존.

---

## 상세

### C-1 (CRITICAL) — Calibration 전 단계가 저장소에 없는 외부 산출물 3종에 동시 의존

plan.md:91-100(§4)은 Calibration을 "아이디어 투입 전 **필수 관문**"으로 선언하고,
plan.md:104-110(§5)의 진행 순서 3~5단계 전부가 여기에 걸려 있다.
그런데 C0~C3를 실행하려면 아래 셋이 모두 필요한데, 저장소에는 셋 다 없다.

| 필요물 | 현 상태 | 근거 |
|--------|---------|------|
| z_sb=256 H-matrix 실물 | 저장소에 H-matrix 파일 0개 | C-2 |
| LLR 테이블 실값(ch/th) | 템플릿만 존재, 값 비어 있음 + 원본 소실 | C-3, C-4 |
| 빌드 가능한 C++ Ref-C | 원본 빌드 BLOCKED, revised는 부분 복사본 | C-5 |

plan.md:112-117(§6 안전성 체크리스트)은 "이 환경에서 C++ 빌드/실행하지 않음"만 적고 있어,
"그럼 누가 어디서 빌드하는가"와 "위 3종을 누가 언제 반입하는가"가 계획 어디에도 없다.
§7의 열린 항목도 "#5 시뮬 파라미터"뿐으로 적혀 있는데(plan.md:127), 실제로는 위 3종 확보가
그보다 앞선 미해결 선행조건이다. 최소한 §5 진행 순서에 **0단계: 외부 산출물 반입(사용자/HW 팀)**을
추가하고, 반입 실패 시 §5-1,2(예시 부호 기반 자가 검증)까지만 진행 가능함을 명시해야 한다.

### C-2 (HIGH) — H-matrix 파일이 저장소에 존재하지 않음 (§5-3, §7 #5)

저장소 전체(.git 제외, .md/.obj 제외) 파일 목록에 H-matrix 후보가 없다.
데이터 파일은 `1_LDPC_revised/llr_tables_template.txt`와 `docs/speed_opt/patches/*.patch`, `_test/.../check_registry.py`가 전부다.

로드 경로:
- `LDPC/ecc_top.cpp:259` — `matrix_in = fopen(ecc_info->str_matrix_name, "r");`
- `LDPC/main.cpp:586-632` `Set_H_Filename()` — Windows 기본 경로 `H_Matrix\` + 파일명
  `H_402091.txt`(기본, main.cpp:629) 또는 `H_4203_1~4.txt`(`__SHPUNC_PATTERN_*__` 시), `__3_BLK_PUNCT__` 시 하위 폴더 `18_by_147_DvMax3\`(main.cpp:601)

`H_Matrix/` 폴더 자체가 없다. 따라서 plan.md:106 "H-matrix / LLR 테이블 **실물 파일 확인**"은
"확인"으로 표현돼 있지만 실제로는 **외부 반입**이며, plan.md:127(§7 #5) "H-matrix 실물 확인 후 제안 → 확정"도
이 반입에 블록된다. 계획에 이 사실이 드러나 있지 않다.

### C-3 (HIGH) — LLR 테이블 실값이 없고 일부는 소스 손상으로 소실 (§1 #5)

plan.md:19(§1 #5)은 "quantization/ch/th 매핑은 **기 최적화 값 사용** … 2-9의 텍스트 파일 포맷을 그대로 로드"라고 적고
`1_LDPC_revised/llr_tables_template.txt`를 가리킨다. 그러나 그 파일은 값이 하나도 없는 템플릿이다.

- `1_LDPC_revised/llr_tables_template.txt:26-42` — 6개 섹션 모두 `# (여기에 N행 × M열 값 붙여넣기)` 주석뿐
- 같은 파일 :24 — "**CH_3SD/TH_\* 는 소스 손상으로 코드 내장값이 소실됨(기본 0)** — 반드시 원본 값으로 채울 것"
- `1_LDPC_revised/decoder.cpp:7006` — `static const int Ch_LLR_3SD[...][...] = {0};  // 원본 초기화 리스트 소실`
- `TODO.md:123` — 미완료 항목 "llr_tables.txt에 HW 원본 값 공급"

즉 "기 최적화 값"은 현재 저장소에 존재하지 않는다. 3SD 모드를 쓰려면 HW 팀 원본 값 반입이 선행돼야 하고,
그 전에는 py/C++ 어느 쪽도 실물 조건 FER를 낼 수 없다.

### C-4 (HIGH) — iteration별 LLR 세트 선택 규칙이 소스에 없음 (§2 3행)

plan.md:31(§2)은 "Quantized LLR 도메인 + **iteration별 LLR 테이블** — 유지 (2-9 파일 로드)"라고 적었다.
2-9 파일이 공급하는 것은 **테이블 값**이고, "몇 번째 iteration에 몇 번 행을 쓰는가"라는 **선택 규칙**은 별개인데,
비-`__AUTO_LLR_OPT__` 빌드에서 그 함수가 스텁이다.

- `LDPC/decoder.cpp:7207-7210` / `1_LDPC_revised/decoder.cpp:7288-7291`
  ```cpp
  int Decoder::Get_VNU_Table_Idx(int iter)
  {
      return 0;
  }
  ```
- 호출부 `LDPC/decoder.cpp:1136-1145` — `__AUTO_LLR_OPT__`면 `Get_Cur_LLR_Idx_FILE(mn)`, 아니면 위 스텁
- `Get_Cur_LLR_Idx_FILE`(decoder.cpp:6973~)은 `m_param_LLR`(외부 LLR matrix 파일)과 `Adjust_HD_Floor_Type` 의존

따라서 현 소스만으로 py에 "iteration별 LLR 테이블"을 이식할 수 없다(모든 iteration이 행 0이 됨).
계획은 이 규칙의 출처를 명시하고, 없다면 "고정 세트로 단순화"를 §2에 명시적 제거 항목으로 올려야 한다.

### C-5 (HIGH) — `ldpc_vanilla/` 파생·빌드의 실현 주체가 계획에 없음 + §7 #3 서술 부정확

plan.md:97(§4 C0) "`1_LDPC_revised` 최신 상태 기반 `ldpc_vanilla/`", plan.md:125(§7 #3)
"decoder 동작은 **검증 완료 상태**이므로 파라미터만 맞추면 됨" — 두 서술 모두 사실과 맞지 않는다.

1. `1_LDPC_revised/`는 **수정된 파일만** 있는 부분 복사본이다(`1_LDPC_revised/README.md:3`).
   실제 내용은 11개 파일뿐(decoder.{h,cpp}, ecc_top.cpp, encoder.{h,cpp}, full_CRC.cpp, partial_CRC.cpp,
   random.{h,cpp}, llr_tables_template.txt, README.md). `main.cpp`, `common.{cpp,h}`, `channel.{cpp,h}`,
   `input.{cpp,h}`, `mode.h`, `ecc_data.h`, `ecc_top.h`, `decoder.h` 외 헤더, TV/GT/corner/local_opt/mpi 등
   나머지 ~23개 파일은 `LDPC/`에서 가져와야 빌드 단위가 완성된다.
2. 그 `LDPC/` 원본이 현재 빌드 불가다 — `TODO.md:13` "[BLOCKED] 소스 파일 일부 손상 (GT.cpp, partial_CRC.cpp 등)".
   `CLAUDE.md:43`도 동일. 실제로 `main.cpp:442,444`, `decoder.cpp:464-465,477-479` 등에 `\case`, `\  fprintf` 같은
   깨진 토큰이 남아 있다.
3. "검증 완료"는 **코드 리뷰 완료**를 뜻하며 빌드·실행 검증이 아니다 —
   `1_LDPC_revised/README.md:6` "이 환경에서는 빌드/실행하지 않는다",
   `TODO.md:123` 미완료 "사후 검증: **원본 빌드 복구 후** 동일 seed golden diff".

→ 계획은 (a) `ldpc_vanilla/`가 `1_LDPC_revised` 11파일 + `LDPC` 나머지 파일의 **합성**임을 명시하고,
(b) 원본 빌드 복구(TODO Phase 0)를 C0의 선행조건으로 걸고, (c) 빌드·실행이 사용자 환경에서만 가능함을 적어야 한다.

### C-6 (HIGH) — N_b=129 오기: 129는 `N_b − M_b`(정보 블록 수)

plan.md:20(§1 #6) "z_sb = 256, **codeword = 129 × 256 = 33,024 bit ≈ 4KB**",
plan.md:30(§2) "Column-layered 순차 스케줄(**129 col** 순서)",
plan.md:77(§3.2) 배열 축 `(B, N_b, z_sb)`,
plan.md:72(§3.1b) "예시 부호 파라미터: N_b=129, M_b≈13 … **실물과 동일 스케일**" 이 모두 이 값에 기대고 있다.

그러나 129는 codeword 블록 수가 아니라 정보 블록 수다.

- `LDPC/decoder.cpp:185-186`
  ```cpp
  HCU_start = m_PCM->N_b - m_PCM->M_b - m_PCM->punct_col_num;
  HCU_end   = m_PCM->N_b - m_PCM->M_b - 1;
  ```
  `CLAUDE.md`/`LDPC/CLAUDE.md`의 HCU_start=127, HCU_end=128, punct_col_num=2를 대입하면 `N_b − M_b = 129`.
  `LDPC/CLAUDE.md`도 "N_b - M_b = 129"라고 직접 적고 있다.
- 반면 같은 상수표는 N_b=129, M_b=129라고 적어 놓았는데, 그러면 `N_b − M_b = 0`이 되어 HCU_start = −2가 된다(모순).
- 방증: H-matrix 폴더명 `18_by_147_DvMax3`(main.cpp:601) → 147 − 18 = 129.
- 방증: 정보 컬럼 129 × z_sb에서 shortened 4B(32bit, common.h:701) + punctured info 60B(480bit, common.h:709) = 512bit
  = 정확히 `punct_col_num(2) × 256` → z_sb=256 가정과 정합.

영향:
- codeword 길이는 `N_b × z_sb`로 33,024보다 크다(N_b가 147 계열이면 ≈37,632 bit). 33,024은 **정보 길이**다.
- rate는 1.0이 아니라 `129/N_b ≈ 0.88`. plan.md:72의 "rate≈0.9, 실물과 동일 스케일"은 M_b≈13/N_b=129 조합에서만
  성립하고 실물(M_b≈18, N_b≈147)과 컬럼 수가 다르다.
- §3.2의 `(B, N_b, z_sb)`에서 N_b를 129로 잡으면 패리티 블록이 통째로 빠진다.

→ `N_b`, `M_b`, `N_b − M_b`를 분리해 기술하고, 실물 값은 H-matrix 반입 후 확정으로 넘겨야 한다.
(부수적으로 루트 `CLAUDE.md:51-53` 상수표의 N_b/M_b도 잘못돼 있음 — 계획이 이를 승계했다.)

### C-7 (HIGH) — `channel.py`의 역할 오배치 (§3.1, §4 C1)

plan.md:53(§3.1)은 `channel.py` = "AWGN + HD/2SD/3SD 양자화 → **채널 LLR**", C++ 대응 = `channel.cpp Set_R_Offset()/Set_LLR_Th()`라고 적었다.
그러나 실제 코드에서 채널이 만드는 것은 **양자화 영역(HD/SD/CC 비트)**뿐이고, LLR **크기**는 VN 업데이트 시점에
`(VN degree, column region, LLR set index)`로 인덱싱된 테이블에서 결정된다.

- `LDPC/channel.cpp:42-56` — `Get_Mag_2SD`/`Get_Mag_3SD`는 임계값 비교로 `sd`, `cc` 비트만 출력. LLR 값 없음.
- `LDPC/decoder.cpp:3988-3989` — `Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1..&ch4)`
- `LDPC/decoder.cpp:4019` (HD) — `channel_llr = ch1;` (부호는 `Variable_mem`의 hard decision에서)
- `LDPC/decoder.cpp:4539-4553` (SD) — `mag = abs(Soft_LLR_PRIME[bit_pos]);` 후 `EDGE_MAG_7/5/3/1 → ch1/ch2/ch3/ch4` 매핑
- `LDPC/decoder.cpp:3995-4016` — bit region별 override: shortening → `CH_LLR_MAX`, puncturing → `CH_LLR_MIN`

즉 채널 LLR은 **degree 의존·컬럼 영역 의존·iteration 세트 의존**이다.
`channel.py`가 비트당 단일 LLR을 만들어 넘기는 구조로 구현하면 이 세 의존성이 사라져 C1/C2가 통과할 수 없다.
파생 문제로, §4 C1의 "**채널 LLR**을 파일로 덤프 → py에 주입"도 정확히는
"HD/SD/CC(및 CD) 양자화 결과를 덤프"여야 한다 — 그래야 py가 동일 테이블로 LLR을 재구성해 비교할 수 있다.

### C-8 (MEDIUM) — C1에 필요한 덤프 수단이 없고, 계획도 절반만 언급

- **채널 입력 덤프**: Ref-C에는 없다. `ecc_top.cpp:911-930`의 `Print_Seed(...)`는 실패 프레임의 **RNG 시드**만 기록한다
  (`uncor_seed_*.txt` / `uncor_vector_*.dat`, ecc_top.cpp:535-590). 원시 HD/SD/CD를 쓰는 경로는
  `TV_Dec::Print_TV_Dec_In(...)`(TV_Dec.cpp:235, 호출 ecc_top.cpp:1119/1250/1340)뿐인데 이는 TV Gen 전용이다 —
  `__ECC_TV__`가 `mode.h:35-39`의 `#else`(= `__PROGRAM_MODE_REF_C__` 미정의) 블록에서만 정의된다.
  plan.md:37(§2)은 "TV 출력 전체 제거"이므로 vanilla에는 이 경로가 없다. → **C++ vanilla에 신규 덤프 추가 필요**.
  plan.md:107(§5-4)이 "C++ vanilla 채널 덤프 필요"라고 적은 것은 맞다.
- **iteration별 hard decision 덤프**: 계획에 언급이 없는데, 이것도 없다.
  Ref-C에서 얻을 수 있는 것은 `__LOG_DECODING_STATUS__` 하의 mini-iteration별 **오류 개수**뿐이다
  (`decoder.cpp:7509-7526` `log_bit_err.dat`/`log_bit_err_column.dat`/`log_SW.dat`/`log_CSW.dat`,
  `m_log_bit_err[mn]`, `m_log_bit_err_col[mn][jj]`). 비트 벡터 자체는 출력되지 않는다.
  → C1의 "iteration별 hard decision 비교"를 하려면 `cwc[]`(또는 `Variable_mem[]`) 덤프도 추가해야 하며,
  이 작업이 §5-4에 빠져 있다. (참고: 오류 개수 로그는 C3 "iteration별 평균 미충족 체크 수"에는 그대로 쓸 수 있다.)

### C-9 (MEDIUM) — §2 표에서 빠진 FER 영향 요소

plan.md:27-40(§2)은 "FER에 영향을 주는 것은 알고리즘 요소"라며 제거 대상을 열거하지만,
아래 요소들은 FER에 직접 영향을 주면서 유지/제거 어느 쪽으로도 표에 없다.

| 요소 | 근거 | FER 영향 |
|------|------|----------|
| Power stopping (Part 2) | `decoder.cpp:4018-4024`, 4207-4213, 4404-4410, 4538-4544, 4711-4717 — 조건 성립 시 `channel_llr = CH_LLR_MAX` 강제 | 채널 LLR을 덮어씀 → 직접 영향. `m_param_dec->stopping_criteria`(decoder.cpp:512,521)로 켜짐 |
| BF(bit-flipping) 모드 | `decoder.cpp:2085-2091` `flag_BF_on` / `MODE_BF_ON` / `syn_th_BF0`, `decoder.cpp:1148-1150` `ITER_MAX_HBF` 전 Preprocessing | 초기 iteration 동작 자체가 달라짐 |
| HD 5/8 Set 선택 | `decoder.cpp:2099-2123` `flag_HD_5_8_Set` (syndrome weight 임계 `syn_th_5_8_Set_0/1`) | LLR 세트를 바꿈 |
| `__SHUFFLED_DUAL_DIAG__` | `mode.h:65` 기본 ON, `encoder.cpp:60-69, 245-335` — 패리티 컬럼 순서를 재배열 | column-layered 순서가 바뀜. plan.md:40에서 Dual-Update만 off로 결정했는데 이 스위치는 별개 |
| punct recovery | `mode.h:61` `__RUN_PUNCT_RECOVERY__`(decoder.cpp에 15곳), `ecc_top.cpp:328-358` punct_vote 구조 | 펑처링 제거로 자연 소멸하나 §2에 명시가 없어 "제거 완전성" 판정이 불가 |

특히 **`__SHUFFLED_DUAL_DIAG__`**는 py(all-zero)에는 영향이 없지만 C++ vanilla에는 영향이 있어,
켜둔 채로 두면 py와 컬럼 순서가 달라 C1이 통과하지 못한다. §2 표에 명시 결정이 필요하다.

### C-10 (MEDIUM) — HCU 컬럼의 vanilla 처리 미기재 (§2 5행)

- HCU 대상 컬럼은 코드에서 `HCU_start = N_b − M_b − punct_col_num`, `HCU_end = N_b − M_b − 1`로 계산된다
  (`decoder.cpp:185-186`). 즉 **정보부 마지막 2개 컬럼 = 펑처링된 컬럼**이다.
- 9/7 분할은 H-matrix 속성이 아니라 **하드코딩 상수**다 — `common.h:381-382`
  `#define SEPARATE_V_DEG_1 9` / `#define SEPARATE_V_DEG_2 7`, 사용처 `decoder.cpp:2596,2599,2651,2654,3772,3775,4151,4154,4664,4667,6125,6129`.
  즉 "half column" 분할 자체는 코드 처리이고, 두 컬럼이 갖는 실제 degree는 H-matrix에 있다.
- 따라서 vanilla에서 HCU를 빼면 두 컬럼은 **full degree(추정 18/17)로 일반 컬럼처럼 매 iteration 전체 업데이트**된다.
  동시에 펑처링도 제거되므로 두 컬럼에 `CH_LLR_MIN`(decoder.cpp:4001,4005) 대신 정상 채널값을 줘야 한다.

plan.md:33(§2)은 "HCU (127/128 half-column) 제거"만 적고 위 두 처리(전체 degree 처리 / 채널값 부여)를 규정하지 않는다.
또 이 컬럼 인덱스는 상수 127/128이 아니라 `N_b − M_b − 2`, `N_b − M_b − 1`로 파라미터화해야
z_sb·M_b가 바뀌어도 유지된다(계획은 127/128을 리터럴로 서술).

### C-11 (MEDIUM) — 쇼트닝/펑처링 제거 시 rate·정보길이 변화 정리 없음

현 설정: shortened info 4B = 32 bit(`common.h:701`), punctured info 60B = 480 bit(`common.h:709`),
punctured parity 0(`common.h:715`). 적용 지점은 `ecc_top.cpp:2632-2648`(bit_pos 구간)과
`decoder.cpp:1072-1089`(Variable_mem 고정), `decoder.cpp:3995-4016`(채널 LLR override).

이걸 제거하면 전송 길이·정보 길이·rate가 모두 달라진다.
plan.md:34(§2)은 "C++ vanilla도 동일하게 제거하므로 동조건 비교"라고만 하는데,
plan.md:16(§1 #2)은 "아이디어가 유효하면 **실제 형태(펑처링 포함)로 적용해 재비교**"를 예고하고 있다.
vanilla rate와 실제 rate가 다르면 두 비교의 기준선이 달라지므로, 최소한
"vanilla rate = 129/N_b, 실제 rate = (정보 − 쇼트닝 − 펑처)/(전송 길이)"를 명시하고
어느 축(동일 rate / 동일 정보길이 / 동일 SNR)에서 비교할지를 정해 둬야 한다.

### C-12 (MEDIUM) — §3.1b 생성 부호의 유효성 수용 기준 없음

plan.md:61-73(§3.1b)은 PEG → lifting → dual-diagonal 조립 → FER 커브까지 적었지만,
"생성된 H가 제대로 만들어졌는가"의 판정 기준이 `tools/lifting.py`의 "짧은 사이클 회피 검사" 한 줄뿐이다.
FER 커브만으로는 생성기 버그(예: 4-cycle 잔존, degree 분포 붕괴)를 걸러내지 못한다.
최소 다음이 수용 기준으로 필요하다.

- girth 목표치(≥6 등)와 실제 girth 측정값 보고
- 컬럼/로우 차수 분포가 목표대로 나왔는지
- H의 랭크(패리티 부 dual-diagonal이 실제로 풀리는지) — all-zero 사용이면 복호 자체는 되지만 rate 계산이 틀어짐
- **shift 값 범위 `0 ~ z_sb-1`** — `TODO.md:125`(2-1 주의사항)이 "범위 밖 값이 오면 out-of-bounds
  (기존 shift_mem은 s = z_sb도 동작했음)"라고 경고. 생성기가 z_sb를 내보내면 `1_LDPC_revised` 디코더에서 OOB.
  py 생성기가 이 제약을 지키는지 검증 항목에 넣어야 한다.

관련해서 §3.1b (a)/(b)는 **문제 없음**으로 확인했다.
- (a) 포맷: `ecc_top.cpp:264-268`이 헤더 5정수 `N_b M_b J K z_sb`를 파일에서 읽고, :281-293이 `M_b × N_b`개의
  shift 값(`EMPTY = -1`, `common.h:42`)을 읽는다. z_sb는 파일 값이므로 256 표현에 제약 없음.
- (b) dual-diagonal: `encoder.cpp:101-152`가 `kb = N_b − M_b` 정보 블록 + 마지막 `M_b` 패리티 블록을 가정하므로
  N_b=129/M_b=13(kb=116) 조합은 구조상 성립. (다만 plan.md:58에서 all-zero를 쓰므로 py 인코더는 불필요.)

### C-13 (LOW) — §3.1 표의 C++ 대응 오기

plan.md:51은 `pcm.py`의 C++ 대응을 "`ecc_top.cpp` `Load_PCM()`, **`input.cpp`**"로 적었다.
`input.cpp`(전체 243줄)에는 H-matrix 파싱이 없다 — `Get_Sector_Num`, `Get_DIN_noPS`, `Get_MSG_noS`,
`Get_Char_to_Hex`뿐이며 모두 DIN/MSG **16진 데이터 입력** 파서다.
H-matrix 파싱은 `ECC_Top::Load_PCM`(ecc_top.cpp:251-319)에만 있다.
(루트 `CLAUDE.md:99`가 input.cpp를 "H-matrix 파일 로드"로 잘못 적어 놓았고 계획이 이를 승계한 것으로 보인다.)
구현자가 input.cpp를 참조 스펙으로 삼으면 엉뚱한 포맷을 만들게 된다.

### C-14 (LOW) — §3.3 MPI fallback의 설계 반영도

plan.md:89 "로컬(Windows) 개발 시에는 MPI 없이 단일 프로세스로 동작해야 함 (mpi4py 미설치 시 fallback)"은
요구사항 문장이고, §3.1 모듈 표에서 `mpi_runner.py`가 `sim.py`와 분리돼 있어 구조적으로 반영은 **가능**하다.
다만 "시드 분할/카운트 집계의 소유권이 어디인가"가 규정돼 있지 않아, 그대로 구현하면
`sim.py`가 `mpi4py`를 직접 import하는 형태가 나오기 쉽다.
"`sim.py`는 rank/size를 인자로만 받고 MPI를 import하지 않는다, `mpi_runner.py`가 유일한 mpi4py 의존점,
미설치 시 `rank=0, size=1`로 직접 `sim.py` 호출" 정도의 한 줄이면 설계로 못 박힌다.
참고로 C++도 같은 패턴이다(`mpi.cpp`는 Windows용 더미 stub).

---

## 참고: 검증했으나 문제 없던 항목

| 항목 | 결과 |
|------|------|
| §3.1b(a) 기존 H-matrix 포맷의 z_sb=256 표현 | 가능 (ecc_top.cpp:264-293, z_sb는 파일 헤더 값) |
| §3.1b(b) dual-diagonal과 M_b≈13 조합 | 가능 (encoder.cpp:101-152, kb = N_b − M_b 가정만 필요) |
| §3.2 참조 링크 `_ldpc_00_L2_단계별상세.md` | 실존 (`LDPC/docs/20260413_ldpc_decoder_understanding/`) |
| 최상단 링크 `paper_screening_profile.md` | 실존 (`docs/`) |
| §1 #5 링크 `llr_tables_template.txt` | 실존 (내용은 C-3 참조) |
| §7 #2 all-zero codeword의 C++ 측 지원 | 존재 (`MODE_ALL_ZERO_CODEWORD`, common.h:104, decoder.cpp:1063-1068, 4895) |
| §7 #1 genie 판정의 C++ 측 대응 | 존재 (`m_genie_inv_cw`, decoder.cpp:1045, `Count_Error_Bit_Column` decoder.cpp:7255-7267) |
