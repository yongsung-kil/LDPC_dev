# 2_LDPC_light 계획 문서 리뷰 — Round 1 관점 도출 (agent_1)

> 대상: `docs/2_LDPC_light/plan.md` (주), `TODO.md` 백로그 "2_LDPC_light" 항목 (부)
> 성격: 코드가 아직 없는 **설계 계획 문서** 리뷰. 이 문서는 "어디를 봐야 하는가"만 정리하며, 문제 판정은 하지 않는다.
> 리뷰 라운드: 라이트 리뷰 Round 1 (관점 도출)

---

## 0. 이 계획의 리스크 지형 (관점 선정 근거)

이 문서가 다른 문서 리뷰와 다른 점은 세 가지다.

1. **대조군이 존재한다** — Python 구현 결과의 신뢰도는 C++ vanilla(`ldpc_vanilla/`)와의 calibration으로만 확보된다. 따라서 "계획이 기술한 C++ 동작 서술이 실제 C++ 코드와 맞는가"가 곧 구현 성패다.
2. **제거 결정이 FER(Frame Error Rate, 프레임 오류율)을 움직인다** — 계획은 "제거해도 FER 무관"인 항목과 "FER이 바뀌지만 양쪽 다 제거하므로 동조건"인 항목을 섞어 다룬다. 두 부류의 근거 강도가 다르므로 분리 검증이 필요하다.
3. **정량 목표가 암묵적이다** — FER 1e-2~1e-4 영역 스크리닝이라는 목표가 병렬화 설계·배치 크기와 연결되어야 하는데, 계획에는 처리량/시간 예산 수치가 없다.

아래 관점은 이 세 축을 따라 배치했다.

---

## 1. 관점 목록

### P1. 사실 정확성 — C++ 대응 인용 검증

계획 곳곳의 "C++ 대응" 표기(파일명·함수명·구조체명)가 실제 소스와 일치하는지.

| 확인 항목 | 대상 |
|---|---|
| `pcm.py` 행의 C++ 대응이 `ecc_top.cpp Load_PCM()`, `input.cpp` 두 곳으로 적혀 있음 — H-matrix 파일을 실제로 읽는 코드가 어디인지, `input.cpp`의 실제 역할이 무엇인지 | plan.md §3.1 표 / `LDPC/ecc_top.cpp` `ECC_Top::Load_PCM()` (파일 오픈 지점 포함) / `LDPC/input.cpp` / `CLAUDE.md` 파일 목록 표 / `docs/paper_screening_profile.md` §6 |
| `channel.py` 행이 `Set_R_Offset()` / `Set_LLR_Th()`를 "AWGN + 양자화 → 채널 LLR"의 대응으로 지목 — 이 두 함수가 실제로 담당하는 범위(오프셋 설정 / 임계값 계산)와 실제 양자화 수행 함수(`Get_Mag_2SD` / `Get_Mag_3SD` 계열), 잡음 생성·RBER↔분산 변환 함수(`SNR_from_RBER`, `dev_from_RBER`)가 계획에 포함되는지 | plan.md §3.1 표 / `LDPC/channel.cpp` 전체, `LDPC/channel.h` |
| `decoder.py` 행의 `VN_Cal_*()` 총칭이 실제 변종 수(HD / CD / SD / 각 HCU 버전)를 어떻게 커버하는지, light에서 어느 변종을 구현 대상으로 삼는지 명시되어 있는지 | plan.md §3.1 표 / `LDPC/decoder.cpp` `VN_Cal_Pre` / `VN_Cal_HD` / `VN_Cal_CD` / `VN_Cal_SD` (및 `_HCU` 변종) |
| `mpi_runner.py` 행이 "에러 카운트 Allreduce", §3.3이 "C++ `__RUN_MPI__`와 동일 패턴"이라고 서술 — C++이 실제로 사용하는 집계 연산이 무엇인지 | plan.md §3.1, §3.3 / `LDPC/mpi.h`·`LDPC/mpi.cpp` 선언 목록 / `LDPC/ecc_top.cpp`의 `__RUN_MPI__` 블록(약 515, 646, 672, 935, 2290행) |
| §3.2가 인용한 "C++ 4-3의 CN_STATE" 필드 구성과 계획이 적은 필드 목록(min1, min2, min1_idx, sign)의 대응 | plan.md §3.2 / `docs/speed_opt/4-3_cn_state_struct.md` / `1_LDPC_revised/decoder.h`의 `struct CN_STATE` |

### P2. 파라미터·상수 정합성

부호 크기·rate 관련 수치가 문서들 사이에서 일관되는지, 그리고 코드가 그 값을 어떻게 정의하는지.

| 확인 항목 | 대상 |
|---|---|
| `N_b = 129`, `M_b`, rate의 관계. 계획 §3.1b는 `M_b ≈ 13`, rate ≈ 0.9로 잡고, `CLAUDE.md` 상수표는 `M_b = 129`(= parity block 수)로 적고 있음 — 어느 쪽이 코드의 정의와 맞는지 | plan.md §3.1b / `CLAUDE.md` 핵심 상수 표 / `LDPC/ecc_data.h:150-158` (`N_b`, `M_b`, `z_sb`, `N = N_b*z_sb`, `M = M_b*z_sb`) / `LDPC/ecc_top.cpp` `Load_PCM()`의 `punct_col_idx = N_b - M_b - punct_col_num + k` / `docs/paper_screening_profile.md` §2의 "N_b/M_b 표기 내부 불일치" 주석 |
| "codeword = 129 × 256 = 33,024 bit ≈ 4KB"의 4KB가 codeword 길이인지 정보 비트(payload) 길이인지, 그리고 C++의 4KB 표기(`LDPC_encoder_4KB`, `str_result_name_4KB`)가 무엇을 가리키는지 | plan.md §1 결정 6 / `LDPC/encoder.cpp` `LDPC_encoder_4KB()` / `LDPC/ecc_data.h` |
| `z_sb`를 32 → 256으로 바꿀 때 C++ vanilla 쪽에서 함께 확인해야 할 것 — `z_sb`는 H-matrix 파일 헤더에서 읽어오는 런타임 값인지, 코드에 `z_sb` 종속 컴파일 상수/고정 크기 배열이 남아 있는지. 계획 §7-3은 "파라미터만 맞추면 됨"으로 서술 | plan.md §1 결정 6, §7-3 / `LDPC/ecc_top.cpp` `Load_PCM()` 헤더 파싱부(`N_b M_b J K z_sb` 5개 필드) / `LDPC/common.h` 상수 / `docs/speed_opt/2-1_shift_mem.md`(shift 값 범위 0~z_sb-1 전제) |
| `max_iter`(고정 iteration 수)의 구체값이 계획에 없음 — 계획 §3.1 `config.py` 항목과 §7-5 "열린 항목"이 이를 포함하는지 | plan.md §3.1, §7 |

### P3. 제거 항목의 FER 영향 분류 타당성

§2 유지/제거 대응표에서 "FER 무관(HW 전용)"과 "FER은 바뀌지만 양쪽 동일하게 제거(동조건 비교)"가 섞여 있다. 각 행이 어느 부류이고 근거가 그 부류에 맞는지.

| 확인 항목 | 대상 |
|---|---|
| "제거 — FER 무관" 주장 행들: 파이프라인(col_M1~P4) / SRAM / PMU / overall_clk / TV 출력 / GT(Graph Thinning). 특히 **GT(MUX 기반 edge 선택)가 정말로 스케줄링만 바꾸고 메시지 값은 바꾸지 않는지** — GT가 처리 edge를 "축소"한다는 서술과 "클록당 edge 스케줄링일 뿐"이라는 근거가 양립하는지 | plan.md §2 / `LDPC/GT.cpp` `Make_GT_HW()` / `docs/paper_screening_profile.md` §3 "MUX 기반 edge 선택으로 클록당 처리 edge 축소" / `LDPC/CLAUDE.md` §HCU·GT 관련 서술 / `CLAUDE.md` "MUX 경계(8) ≠ SEPARATE_V_DEG(9/7)" 항목 |
| "파이프라인 제거가 FER 무관"이 성립하려면 pipeline stage 간 지연이 메시지 갱신 순서(같은 iteration 안에서 뒤 컬럼이 앞 컬럼의 갱신값을 보는지)를 바꾸지 않아야 함 — column-layered 스케줄의 semantic이 파이프라인 유무로 달라지는지 | plan.md §2, §3.2 / `LDPC/decoder.cpp` `LDPC_Decoder()` 컬럼 루프(약 5690-5770행), `C2V_Cal()`(2341행~) / `LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` |
| "쇼트닝/펑처링 제거"가 H-matrix 구조 자체에 미치는 영향 — punctured column은 `N_b - M_b - punct_col_num` 위치로 정의되고 puncturing recovery가 별도 로직을 가짐. 제거 시 해당 컬럼을 "전송되는 일반 컬럼"으로 취급하는지, 코드 길이·rate가 바뀌는지 | plan.md §2, §1 결정 3 / `LDPC/ecc_top.cpp` `__RUN_PUNCT_RECOVERY__` 블록 / `CLAUDE.md` `punct_col_num` |
| "XOR25 난수 생성기 → numpy RNG 교체"가 채널 잡음 통계에 미치는 영향과, C1 bit-exact 대조 시 난수원이 달라도 되는 이유가 명시되어 있는지 | plan.md §2, §4 C1 / `LDPC/random.cpp`, `1_LDPC_revised/random.cpp` / `docs/speed_opt/5-6_xor25_no_double.md` |

### P4. 성공 판정 기준(genie 판정)의 정의와 대조군 동조건성

계획은 조기종료를 제거하고 고정 iteration으로 돌리되(§2), 매 iteration hard decision을 정답과 비교해 일치하면 그 프레임을 성공 확정한다(§7-1). 이 두 결정의 결합이 만드는 FER 정의를 확인해야 한다.

| 확인 항목 | 대상 |
|---|---|
| "매 iteration 비교 후 일치 시 성공 확정"은 사실상 **genie(정답을 아는) 조기종료**다. "고정 iteration 끝까지 돌린 뒤 최종 hard decision만 비교"와 결과가 달라지는 경우(중간에 정답에 도달했다가 이후 iteration에서 이탈하는 진동 케이스)가 존재하는지, 계획이 어느 정의를 FER로 삼는지 명시되어 있는지 | plan.md §1 결정 4, §2 "조기종료 제거 — 고정 iteration", §7-1 |
| C++ vanilla(`ldpc_vanilla/`)도 **동일한 genie 판정**을 쓰도록 §4 C0에 지시되어 있는지. C0는 "조기종료 제거"만 적고 있어, C++ 쪽 판정 시점(최종 iteration만 / 매 iteration)이 미지정인지 | plan.md §4 C0, §7-3 / `LDPC/decoder.cpp` 판정·수렴 처리부, `LDPC/partial_CRC.cpp`·`full_CRC.cpp` 호출 지점 |
| C3(수렴 프로파일: iteration별 평균 미충족 체크 수)를 측정하려면 성공 프레임도 끝까지 돌려야 하는데, genie 판정으로 조기 종료하면 그 이후 iteration 통계가 비게 됨 — C3 측정 방식과 genie 판정의 양립 여부 | plan.md §4 C3, §7-1 |
| C++이 이미 가진 `MODE_ALL_ZERO_CODEWORD` / `MODE_ALL_ONE_CODEWORD` 설정과 계획의 all-zero 결정이 어떻게 맞물리는지(C++ vanilla에서 별도 개조 없이 설정만으로 되는지) | plan.md §3.1, §7-2 / `LDPC/common.h:104-111` / `LDPC/decoder.cpp:1056-1063`, `4892-4915` / `LDPC/ecc_top.cpp:810-813` |

### P5. all-zero codeword 대칭성 논거의 성립 조건

§3.1은 "대칭 채널 + 대칭 복호기에서는 all-zero로 FER 측정 가능 → 인코더 불필요"라고 단언한다. 이 조건이 이 코드의 채널·양자화·복호기에서 실제로 성립하는지가 확인 대상이다.

| 확인 항목 | 대상 |
|---|---|
| 채널 대칭성: AWGN 자체는 대칭이나, soft read 임계값이 0을 중심으로 대칭 배치되는지. `Set_R_Offset()`의 오프셋 값들(2SD는 0.35, 3SD는 0.15/0.35/0.55, 1.5SD는 0.15/-0.15)과 `Get_Mag_*` 함수가 크기(magnitude)를 받는지 부호 있는 값을 받는지 | plan.md §3.1 / `LDPC/channel.cpp:11-70` (`Set_R_Offset`, `Set_LLR_Th`, `Get_Mag_2SD`, `Get_Mag_3SD`, `Get_Mag_1_5SD`) |
| 복호기 대칭성: 양자화된 min-sum의 LLR 매핑값(`Ch_LLR_*`)과 임계값 테이블(`table_*`)이 부호에 대해 대칭인지, 포화(saturation) 처리가 양/음 동일한지 | plan.md §3.1 / `LDPC/decoder.cpp` `Mapper_2bit_SD` / `Mapper_3bit_SD` (약 5308-5414행) / `LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` §1.1 |
| NAND 특유의 비대칭(프로그램/이레이즈 상태별 오류율 차이)을 이 시뮬레이터가 모델링하는지, 안 한다면 all-zero 가정이 안전한지 | `LDPC/channel.cpp` 전체 / `docs/paper_screening_profile.md` §2 "채널: AWGN / RBER / fixed-error 패턴" |
| all-zero를 쓰면 인코더가 불필요하다는 귀결과, §3.1b의 예시 부호 생성 도구가 **dual-diagonal parity 구조**를 만드는 목적(인코딩이 필요 없다면 dual-diagonal 구조가 왜 요구되는지)의 정합성 | plan.md §3.1, §3.1b |

### P6. 알고리즘 재현 명세의 충실성 (배열/상태 설계)

§3.2는 "C++의 remove-old/add-new 갱신 방식을 그대로 재현"을 스펙으로 삼는다. 재현에 필요한 상태가 빠짐없이 열거되어 있는지.

| 확인 항목 | 대상 |
|---|---|
| §3.2가 열거한 CN 상태는 (min1, min2, min1_idx, sign) — C++이 실제로 유지하는 상태는 `min1_pos` / `min1_value` / `min2_value` / `check_sum` / `syndrome`. 여기에 더해 **edge 단위 sign 메모리**(`Check_SRAM_sgn`, 이전 V2C 부호)가 remove-old 연산의 핵심 입력임. 계획의 배열 설계에 edge 메모리 축이 포함되어 있는지 | plan.md §3.2 / `1_LDPC_revised/decoder.h` `struct CN_STATE` / `docs/speed_opt/4-3_cn_state_struct.md` / `LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` §1.2 (`C2V_Cal_New_Sgn`의 `Syndrome + check_sum + edge_sgn` XOR 구조) |
| magnitude 쪽 remove-old의 정확한 의미 — min1/min2는 XOR처럼 제거가 불가능하므로 C++이 실제로 어떤 방식(누적 갱신 / 컬럼 패스마다 재계산 / old·new 2세트 교대)으로 처리하는지, 계획의 "old/new 2세트"가 그 방식과 같은지 | plan.md §3.2 / `LDPC/decoder.cpp` `C2V_Cal()`(2341행~), `CNU_Update_New_Mag()`, `CNU_Remove_Old_Sgn()`, `V2C_Store` 계열 / `docs/speed_opt/2-2_iter_invariant_hoist.md`(clear 판정이 (iter, col, mode)의 함수라는 전제 서술) |
| "edge clear iteration"(iteration 경계에서 edge sign을 0으로 초기화) 같은 iteration 초기화 규칙이 계획에 반영되어 있는지 | `LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` §1.2 (a) / plan.md §3.2 |
| circulant shift 처리(`np.roll` 또는 사전 계산 인덱스)가 C++의 shift 방향·기준과 일치하는지 확인할 근거가 계획에 있는지 | plan.md §3.2 / `LDPC/ecc_top.cpp` `Load_PCM()`의 `shift_mem(z_mem_shift, z_sb, s, 1)` 및 `C_net` 구성 / `docs/speed_opt/2-1_shift_mem.md` |
| §3.2가 스펙으로 지목한 L2 문서 링크(`../../LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md`)가 계획에서 필요한 범위(C2V / VN / 스케줄 전 구간)를 실제로 담고 있는지, 그 문서 자체가 최신 `1_LDPC_revised` 구조(4-3 CN_STATE 통합 이후)와 어긋나지 않는지 | plan.md §3.2 링크 / 해당 L2 문서 / `docs/speed_opt/commits.md` |

### P7. LLR 테이블·양자화 도메인 이식 가능성

계획 §1-5는 "기 최적화 값 사용", §3.1은 "2-9 포맷 파일 로드"로 처리한다. 로드 대상 값이 실재하는지와, 테이블 인덱싱 규칙까지 이식되는지가 확인 대상이다.

| 확인 항목 | 대상 |
|---|---|
| `llr_tables_template.txt`는 **값이 비어 있는 템플릿**이며, 헤더 주석은 "CH_3SD/TH_* 는 소스 손상으로 코드 내장값이 소실됨(기본 0) — 반드시 원본 값으로 채울 것"이라고 적고 있음. 계획이 전제하는 "기 최적화 값"의 실물 출처와 확보 계획이 문서에 있는지 | plan.md §1 결정 5, §3.1 `llr_tables.py` / `1_LDPC_revised/llr_tables_template.txt` 전문 / `docs/speed_opt/2-9_llr_table_parameterize.md` / `TODO.md` 백로그 "llr_tables.txt에 HW 원본 값 공급" 항목 |
| 테이블 로드만으로는 부족하고 **행 인덱스(table_idx) 선택 규칙**과 **열 인덱스(dv_idx: degree 구간)** 매핑이 함께 필요함. 계획이 이 두 규칙의 이식을 다루는지 | plan.md §3.1 / `LDPC/decoder.cpp` `Get_VNU_Table_Idx(int iter)`(7207행), `Get_Cur_LLR_Idx_FILE()`, `Get_VNU_Ch_LLR_Adaptive()`, `Get_VNU_Th_Adaptive()` / `1_LDPC_revised/llr_tables_template.txt`의 인덱싱 의미 주석 |
| 테이블 행/열 크기가 빌드 상수(`PRIME_HD_LLR_TABLE_NUM_ROW`, `PRIME_LLR_TABLE_NUM_DEGREE`, `NUM_TH`)와 3bit/4bit 빌드 스위치(`__4_BIT_LLR__`, `__AUTO_LLR_OPT__`)에 종속됨 — Python이 어느 빌드 프로파일을 가정하는지 명시되어 있는지 | plan.md §1 결정 5 / `LDPC/common.h` 관련 상수 / `LDPC/mode.h` |
| 양자화 비트폭·포화 규칙(EDGE_MAG_*, EDGE_MAX_* 등 3-bit precision 상수)과 1-bit precision 분기(BF 모드, `ITER_MAX_HBF`)의 처리 방침이 계획에 있는지 | plan.md §2 "Quantized LLR 도메인 유지" / `LDPC/common.h` EDGE_MAG/EDGE_MAX 상수 / L2 문서 §1.2 (b) / `docs/speed_opt/2-3_1bit_precision_hoist.md` |
| §3.1b가 예시 실행에서 쓰겠다는 "기본 양자화 프로파일"의 정의가 문서에 있는지 | plan.md §3.1b 두 번째 불릿 |

### P8. Calibration 절차의 실행 가능성

§4는 아이디어 투입 전 필수 관문으로 C0~C3을 둔다. 각 단계가 **실제로 수행 가능한 입출력 수단**을 갖는지가 확인 대상이다.

| 확인 항목 | 대상 |
|---|---|
| C1의 "C++에서 채널 LLR을 파일로 덤프" — 현재 C++에 그런 덤프 수단이 있는지, 없다면 누가 언제 만드는지가 §5 진행 순서에 들어 있는지. 또한 이 프로젝트는 **이 환경에서 C++ 빌드·실행 금지** 규칙이 있어 덤프 실행 주체가 사용자여야 함 | plan.md §4 C1, §5, §6 / `CLAUDE.md` 빌드 섹션 / `LDPC/TV_Dec_Inter.cpp`(중간 신호 출력 수단이 대안이 되는지) |
| C1의 비교 대상이 "iteration별 hard decision"인데, HW 파이프라인이 있는 C++에서 "iteration 경계"의 스냅샷 시점이 어디인지(어느 pipeline stage 기준인지) 정의되어 있는지 | plan.md §4 C1 / `CLAUDE.md` "col_P1~P4 구분" 주의 항목 / `LDPC/CLAUDE.md` §파이프라인 |
| C2의 "통계 오차(95% 신뢰구간) 내 일치" — 필요한 프레임 수, 비교할 SNR 포인트 선정 기준, 판정 실패 시 처리(재현 조건 축소 등)가 정의되어 있는지 | plan.md §4 C2 |
| C3의 "iteration별 평균 미충족 체크 수"를 C++에서 뽑을 수단이 있는지(기존 로그: `log_iter_histogram.dat`, `log_csw2.dat` 등이 이 지표에 해당하는지) | plan.md §4 C3 / `LDPC/ecc_top.cpp:2820-2860` 로그 파일 생성부 / `docs/speed_opt/2-10_init_log_data_guard.md` |
| C0(`ldpc_vanilla/` 준비)가 §5 진행 순서 목록에는 항목으로 등장하지 않고 §4 표에만 "별도 작업"으로 적혀 있음 — 선후 관계와 담당이 어디에 기록되는지 | plan.md §4 C0, §5 / `TODO.md` 2_LDPC_light 서브태스크 목록 |
| C1이 "전 iteration 일치"를 요구하는데, Python은 부동소수 채널 → 양자화 정수 도메인, C++은 자체 RNG 기반 — **채널 LLR을 주입하면 이후 경로는 완전 정수 연산인지**(즉 bit-exact 일치가 원리적으로 가능한지) | plan.md §4 C1 / `LDPC/decoder.cpp` 양자화 도메인 연산부 / L2 문서 |

### P9. 예시 부호 생성 도구(§3.1b)의 출력 규격·설계 타당성

| 확인 항목 | 대상 |
|---|---|
| "기존 입력 포맷"으로 H-matrix를 쓰겠다고 했으므로, 그 포맷의 실제 필드 구성을 계획이 알고 있는지 — 헤더 5개 필드(`N_b M_b J K z_sb`)와 `J`(컬럼당 최대 degree) / `K`(로우당 최대 degree)의 의미, 이어지는 M_b×N_b shift 값 배열(`EMPTY`/-1 표기) | plan.md §3.1b, §3.1 `pcm.py` / `LDPC/ecc_top.cpp` `Load_PCM()` 파싱부 / `CLAUDE.md` "절대 건드리면 안 되는 것" 4번(H-matrix 파일 포맷) |
| `Load_PCM()`이 H-matrix 외에 MUX 행렬 파일도 다루는지(코드에 `mux_matrix_in` 변수 존재) — 생성한 예시 부호를 C++ vanilla가 읽으려면 그 파일도 필요한지 | `LDPC/ecc_top.cpp` `Load_PCM()` 지역 변수 및 사용 여부 / `LDPC/GT.cpp` |
| PEG(Progressive Edge Growth)를 정보부 컬럼에만 적용하고 parity부는 dual-diagonal 고정이라는 설계에서, 전체 girth(최단 사이클 길이) 보장 논리가 성립하는지, lifting 단계의 "짧은 사이클 회피 검사"가 어느 사이클 길이(4-cycle / 6-cycle)를 대상으로 하는지 | plan.md §3.1b 표 / `docs/adr/ADR-003-dual-diagonal-encoding.md` |
| 예시 부호 파라미터(N_b=129, M_b≈13, z_sb=256, rate≈0.9)가 P2의 rate 정의와 정합하는지, 그리고 VN degree 분포(실물은 최대 17) 목표가 명시되어 있는지 | plan.md §3.1b / `CLAUDE.md` `MAX_DV_GLOBAL` / `docs/paper_screening_profile.md` §2 |
| "정정능력 커브"의 x축 정의(SNR / RBER 중 무엇, 어떤 변환식)와 C++ 결과와의 축 정합 — C++은 RBER↔표준편차 변환에 `SNR_from_RBER`, `dev_from_RBER`를 씀 | plan.md §3.1b `examples/fer_curve.py` / `LDPC/channel.cpp:68-90` |
| 도구 산출물의 저장 위치(`2_LDPC_light/tools/`, `examples/`)와 §6 안전성 체크리스트("신규 폴더 `2_LDPC_light/`만 생성")의 정합, 생성 파일의 `.gitignore` 정책 | plan.md §3.1b, §6 / 루트 `.gitignore` |

### P10. 병렬화 구조와 처리량 예산의 타당성

| 확인 항목 | 대상 |
|---|---|
| "코어 수 × 배치 벡터화(10~30배)"라는 곱셈 모델에서, 배치 벡터화 이득 10~30배의 근거가 제시되어 있는지 | plan.md §1 결정 7, §3.3 |
| Python 루프 횟수 예산: 컬럼 루프 129회 × iteration 수 × (컬럼당 numpy 호출 수)가 프레임 배치당 몇 회의 인터프리터 왕복인지, 배치 크기 B=32~128과 z_sb=256에서 배열 크기가 캐시/메모리 대역에 어떻게 걸리는지 | plan.md §3.2, §3.3 |
| 목표 FER 영역(1e-2~1e-4) 도달에 필요한 프레임 수와 가용 코어 수 → **실제 소요 시간 추정치**가 문서에 있는지. 없다면 스크리닝 회전율(아이디어 1건당 판정 시간)을 무엇으로 판단할지 | plan.md §1 결정 1, §3.3, §5 |
| numba 미사용 결정(§7-6)과 위 처리량 목표의 정합, 재검토 트리거 조건이 정의되어 있는지 | plan.md §7-6 |
| mpi4py 미설치 시 단일 프로세스 fallback 요구가 있는데, rank별 시드 분할 규칙(재현성)이 단일/다중 프로세스에서 동일한 결과를 주는지 명시되어 있는지 | plan.md §3.3 / `LDPC/ecc_top.cpp`의 `__RUN_MPI__` 시드/집계 블록 |

### P11. 범위 완전성 — FER에 영향을 주는데 계획에 없는 요소

"계획에 없는 것"을 찾는 관점. 아래 후보를 대조 목록으로 삼아 §2·§3에 대응 항목이 있는지 훑는다.

| 확인 후보 | 확인 근거 |
|---|---|
| iteration 최대 횟수(`max_iter`)와 그 값의 C++ 대조군 일치 | plan.md 전체에 수치 없음 여부 확인 |
| 컬럼 처리 **순서**(0→128 오름차순인지, dual-update off일 때의 순서, 컬럼 재배치 여부) | `LDPC/encoder.cpp` `Column_Reordering_Dual_Update()` / plan.md §2 Dual-Update off 행 |
| 메시지 포화(saturation) / 클리핑 규칙, 음수 표현(2의 보수 vs 부호-크기) | L2 문서 §1.2 / `LDPC/common.h` |
| 초기화 상태(첫 iteration의 CN 상태·edge sign 초기값, syndrome 초기 계산 유무) | `LDPC/decoder.cpp` `Clear_CN_REG` / `Clear_Syndrome` / `Clear_REG_min_*` 계열, `docs/speed_opt/2-15_clear_memset.md`, `2-16_clear_reg_min_branch.md` |
| min-sum scaling / offset factor의 존재 여부(코드상 명시 미확인으로 기록됨) | `docs/paper_screening_profile.md` §3 첫 항목 |
| 디코딩 모드(HD / 2SD / 3SD / 1.5SD) 중 light가 지원할 범위 | plan.md §2 "HD/2SD/3SD 유지" vs `LDPC/channel.cpp` `Get_Mag_1_5SD`, `LDPC/decoder.cpp` `VN_Cal_CD` |
| BF(bit-flipping) 모드 / `ITER_MAX_HBF` 이하 iteration의 1-bit precision 분기 | L2 문서 §1.2 (b) / `docs/speed_opt/2-3_1bit_precision_hoist.md` |
| 실패 프레임 재현·저장(uncorrectable seed 기록) 같은 스크리닝 운영 기능의 필요 여부 | `LDPC/ecc_top.cpp` uncor seed 파일 처리(615-630, 1177-1283행) / plan.md §2 "corner 추적 제거" |
| 아이디어 훅(§3.1 마지막 불릿, §5-7)의 구체적 인터페이스 — 어떤 함수가 교체 지점인지, 훅 추가가 vanilla 결과를 바꾸지 않음을 어떻게 보장하는지 | plan.md §3.1, §5 |

### P12. 문서 구조·상호참조 일관성

| 확인 항목 | 대상 |
|---|---|
| §1 "배경 — 확정된 결정 사항"과 §7 "확정 사항"의 역할 분리. 두 표가 같은 항목(제거 범위, 성공 판정, Dual-Update, 파라미터)을 서로 다른 표현으로 중복 서술하는지, 충돌하는 서술이 있는지(예: §1-4 "bitwise 비교" vs §7-1 "매 iteration genie 판정", §1-5 "필요 시 약간 튜닝" vs §7-5 "유일한 열린 항목") | plan.md §1, §7 |
| 문서 머리말의 "생성일: 2026-07-29"와 본문의 2026-07-30 결정 반영 — 갱신일/개정 이력 표기 유무 | plan.md 머리말, §2 Dual-Update 행, §3.1b, §7 |
| §2 표의 Dual-Update 행 근거가 "사용자 결정(2026-07-30)"으로 §7-4와 중복 기록되는 구조가 의도된 것인지 | plan.md §2, §7 |
| 링크 유효성: `../paper_screening_profile.md`, `../../1_LDPC_revised/llr_tables_template.txt`, `../../LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` (상대경로 기준점이 `docs/2_LDPC_light/`) | plan.md 머리말, §1-5, §3.2 |
| §5 진행 순서(7단계)와 `TODO.md` 2_LDPC_light 서브태스크 목록의 순서·항목 대응(특히 C++ vanilla 준비의 위치가 서로 다른지) | plan.md §5 / `TODO.md:129-141` |
| 프로젝트 문서 관례와의 정합 — 표 중심 서술, 한글 용어 사용, 약어 첫 등장 시 풀어쓰기(PEG, QC, FER, RBER, HCU, PMU, TV 등) | plan.md 전체 / `CLAUDE.md` / `docs/speed_opt/README.md`·`checklist.md` 스타일 / 글로벌 규칙 "용어를 임의로 줄이거나 만들지 않기" |
| `docs/2_LDPC_light/`에 계획 외 문서(README/인덱스)가 필요한지, `CLAUDE.md` 참조 문서 목록·`docs/` 인덱스에 2_LDPC_light가 등록되어야 하는지 | `CLAUDE.md` §참조 문서 / `docs/` 디렉토리 구성 |

### P13. 안전성·작업 격리 체크리스트(§6)의 충분성

| 확인 항목 | 대상 |
|---|---|
| `ldpc_vanilla/`를 "별도 파생 폴더"로 두겠다는데 위치(루트 형제 폴더인지)와 생성 주체가 §6·§4 C0 사이에 일관되게 적혀 있는지. §6 첫 줄은 "신규 폴더 `2_LDPC_light/`만 생성"이라 적고 둘째 줄은 `ldpc_vanilla/`도 만든다고 함 | plan.md §6, §4 C0, §7-3 |
| `1_LDPC_revised/`가 이미 원본 대비 다수 최적화가 적용된 상태(4-3 CN_STATE 통합, 4-4 int8_t 축소, 5-6 RNG 변경 등)이며 **사후 검증이 아직 미완**(TODO 백로그)임 — 이를 calibration 기준으로 삼는 결정의 전제가 문서에 기록되어 있는지 | plan.md §7-3 / `TODO.md:118-123` 특히 "사후 검증: 원본 빌드 복구 후 동일 seed golden diff" 미완 항목 / `docs/speed_opt/commits.md` |
| Python 신규 프로젝트에 필요한 기본 인프라(의존성 명세, 시드 재현성 기록, 결과 파일 위치, `.gitignore`)가 §6 또는 §3에 언급되는지 | plan.md §3, §6 / 루트 `.gitignore` / 글로벌 규칙 `_test/` 관례 |
| "이 환경에서 C++ 빌드/실행하지 않음" 규칙과 C1/C2가 요구하는 C++ 실행의 역할 분담(사용자 실행 전제)이 명시되어 있는지 | plan.md §6, §4 / `CLAUDE.md` 빌드 섹션 |

---

## 2. 관점 우선순위 (라이트 리뷰 배분 제안)

| 우선 | 관점 | 이유 |
|------|------|------|
| ★★★ | P4, P5, P8 | 판정 기준·대칭성 가정·calibration 실행 가능성은 틀리면 프로젝트 전체 결과가 무효가 되는 축 |
| ★★★ | P2, P7 | 파라미터/테이블 값이 확보되지 않으면 §5의 3번 단계 이후가 멈춤 |
| ★★☆ | P1, P3, P6 | 구현 착수 시 바로 부딪히는 정확성 항목 |
| ★★☆ | P11 | 누락은 구현 후반에 발견될수록 비용이 큼 |
| ★☆☆ | P9, P10, P12, P13 | 계획 보완으로 흡수 가능한 범위 |
