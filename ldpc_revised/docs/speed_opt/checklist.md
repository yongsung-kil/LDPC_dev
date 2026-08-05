# 속도 최적화 체크리스트 (Ref-C 실행 시간 단축)

> 목적: 실행 로직(연산 결과)을 바꾸지 않고 Ref-C FER 시뮬레이션 속도를 개선한다.
> 원칙: **한 항목 = 한 커밋**. 각 항목 적용 후 동일 seed 실행 결과가 이전과 동일한지 확인한다.
> 표기: [bit-exact] = 결과 비트 단위 동일 보장 / [검증 필요] = 이론상 동일하나 적용 후 결과 비교 필수.
> 주의: HCU 버퍼 매핑 블록 2개(C2V_Cal / V2C_Store 내 `__ECC_TV__` 가드 안쪽)는 이 체크리스트에서 일절 건드리지 않는다.
> 범위: `__PROGRAM_MODE_REF_C__` 빌드의 속도만 개선한다 (TV Gen / log 모드의 성능은 대상 아님).
> 진행 방식: `ldpc_revised/`에 수정 대상 파일 사본을 두고 **한 번에 한 항목** 수정 → 사용자 검토 → 다음 항목. 이 환경에서는 빌드/실행하지 않는다. 주의사항은 TODO.md에 기록.
> 상세 근거: 적용된 항목마다 같은 폴더의 `{ID}_이름.md` reference 문서에 왜/어떻게/주의/검토 상태를 기록한다. 참고 diff는 `patches/{ID}.patch`.
> 이 문서는 전달 패키지 `docs/speed_opt/`의 일부 — 패키지 사용법은 [README.md](README.md).

---

## Phase 2 — 디코더 핫루프 (`decoder.cpp`)

효과가 가장 큰 코드 수정. 실행 빈도: element 레벨 1줄 = 프레임당 수십만~수백만 회.

- [x] **2-1. `shift_mem` 순열 사전 계산** [bit-exact / 위험 낮음] — 상세: [2-1_shift_mem.md](2-1_shift_mem.md)
  - 함수: `common.cpp shift_mem()` ← 호출: `C2V_Cal()`, `V2C_Store()`
  - 바꿀 부분: 두 함수가 edge 처리 시작부에서 `s = PCM_b[행][열]`을 읽은 뒤 `shift_mem(z_mem_shift, z_sb, s, dir)`로 32-원소 순열을 매번 재계산하는 부분
  - 방법: shift 값은 H-matrix 고정이고 가능한 조합은 방향(2) × shift(z_sb=32)뿐. Decoder 초기화(버퍼 할당부)에서 `shift_table[2][32][32]`을 1회 생성하고, 핫루프에서는 `const int* z_mem_shift = shift_table[dir][s];` 포인터 대입으로 교체. (`z_mem_shift`는 이후 읽기 전용임 — 확인됨)

- [x] **2-2. iteration 판정 함수의 element 루프 탈출** [bit-exact / 위험 낮음] — 상세: [2-2_iter_invariant_hoist.md](2-2_iter_invariant_hoist.md)
  - 함수: `C2V_Cal()`과 `V2C_Store()`의 z_sb(32) 원소 루프 내부에서 호출되는 `C2V_Cal_New_Sgn()` / `CNU_Remove_Old_Sgn()` / `Is_Iter_Type_Init()`
  - 바꿀 부분: 이 함수들 내부의 `Is_Iter_Type_Edge_Clear(iter)` 판정, `init_n` 모드 비교는 iteration 동안 완전 불변인데 원소마다 재평가됨
  - 방법: iteration(mini-iter) 시작 지점에서 `m_bEdgeClear` / `m_bInit` 같은 bool 멤버로 1회 계산해 캐시. element 루프에서는 캐시된 bool로 직접 분기 (예: `edge_sgn = m_bEdgeClear ? 0 : Check_SRAM_sgn[...]`).

- [x] **2-3. 1bit-precision 판정 hoisting** [bit-exact / 위험 낮음] — 상세: [2-3_1bit_precision_hoist.md](2-3_1bit_precision_hoist.md)
  - 함수: `C2V_Cal()`, `V2C_Store()`, VN_Cal 계열(HD, HD-HCU)
  - 바꿀 부분: element 루프 안에서 매번 평가하는 `flag_BF_on && iter <= ITER_MAX_HBF && v_deg > DV_5` 3항 조건
  - 방법: 함수 서두에서 `const int b1bit = ...;` 1회 계산 후 루프에서는 `b1bit`만 검사. (또는 루프를 1bit/3bit 두 버전으로 분리)

- [x] **2-4. stopping_criteria 판정 hoisting** [bit-exact / 위험 낮음] — 상세: [2-4_stopping_criteria_hoist.md](2-4_stopping_criteria_hoist.md)
  - 함수: VN_Cal 계열 5종(HD / HD-HCU / CD / SD / SD-HCU)
  - 바꿀 부분: element 루프 안의 `stopping_criteria` 모드 비교 + `Force_stopping` 비교로 `channel_llr = ch1 or CH_LLR_MAX`를 고르는 분기 — 두 값 모두 루프 동안 불변
  - 방법: 함수 서두에서 `const int table_llr = (조건) ? ch1 : CH_LLR_MAX;` 1회 계산, 루프에서는 대입만.

- [x] **2-5. `before_BS` dead code 제거** [bit-exact / 위험 낮음] — V2C_Store 최내곽의 ~1/3 — 상세: [2-5_before_BS_dead_code.md](2-5_before_BS_dead_code.md)
  - 함수: `V2C_Store()`
  - 바꿀 부분: element 루프 내 `check_in_before_BS` / `check_in_before_BS_nq` / `check_in_before_BS_mag` / `v2c_sgn_before_BS` / `pre_v2c_sgn_before_BS` 계산 블록. 유일한 소비처가 `__ECC_TV__` 가드 안의 tv 버퍼 쓰기임 (전수 확인됨)
  - 방법: 계산 블록 전체를 `#if defined(__ECC_TV__)`로 감싼다. `v2c_mag_before_BS`는 **어느 모드에서도 읽는 곳이 없는 완전 사장 코드**이므로 삭제.

- [x] **2-6. `_nq` 배열 체인을 TV 전용으로 가드** [bit-exact / 위험 낮음] — 상세: [2-6_nq_arrays_tv_guard.md](2-6_nq_arrays_tv_guard.md)
  - 함수: VN_Cal 계열의 `VNU_out_nq[...] = temp_nq;` 쓰기, `Delay_2clk()`의 `VNU_out3_nq ← VNU_out2_nq ← VNU_out_nq` 시프트 복사, Decoder 버퍼 할당부의 `_nq` 3종 할당/해제/클리어
  - 바꿀 부분: `_nq`(양자화 전 값) 체인의 최종 소비처는 TV 출력뿐 — Ref-C에서는 전부 낭비
  - 방법: 선언·할당·쓰기·복사 전체를 `#if defined(__ECC_TV__)` 가드.

- [x] **2-7. `pre_exist_sgn_reg_BS` 3종을 TV 전용으로 가드** [bit-exact / 위험 낮음] — 상세: [2-7_sgn_reg_BS_tv_guard.md](2-7_sgn_reg_BS_tv_guard.md)
  - 함수: `C2V_Cal()`의 `pre_exist_sgn_reg_BS[...] = edge_sgn;` 쓰기, `Delay_2clk()`의 2개 배열 시프트 복사, 할당부
  - 방법: 2-6과 동일하게 `__ECC_TV__` 가드.

- [x] **2-8. `Delay_2clk()` 원소별 복사 → 행 단위 memcpy** [bit-exact / 위험 낮음] — 상세: [2-8_delay_2clk_memcpy.md](2-8_delay_2clk_memcpy.md)
  - 함수: `Delay_2clk()`
  - 바꿀 부분: clk마다 8개 배열(J×z_sb)을 이중 루프 원소별 대입으로 시프트하는 부분 (2-6/2-7 적용 후엔 4개)
  - 방법: 배열·행별 `memcpy(dst[ii], src[ii], z_sb * sizeof(int))`로 치환.
  - **금지**: 포인터 회전(swap) 방식은 HCU 컬럼의 부분 갱신 때문에 잔존 값 의미가 달라져 결과가 바뀔 수 있음 — memcpy까지만.

- [x] **2-9. LLR 테이블 파라미터화 (텍스트 파일 로드) + 호출당 스택 재구성 제거** [동일 값 로드 시 bit-exact / 위험 낮음] — 상세: [2-9_llr_table_parameterize.md](2-9_llr_table_parameterize.md)
  - 함수: `Get_VNU_Ch_LLR_Adaptive()`, `Get_VNU_Th_Adaptive()`
  - 바꿀 부분: 함수 로컬로 선언된 대형 초기화 배열(`Ch_LLR_HD`, `Ch_LLR_2SD`, `Ch_LLR_3SD`, `table_HD/2SD/3SD`) — MSVC는 호출마다(컬럼당 × 129 × iteration) 2~3KB를 스택에 재구성. 3SD/threshold 테이블은 현재 초기화 리스트가 소실된 상태
  - 방법 (파라미터화 결정 반영): 테이블 값을 텍스트 파일(예: `llr_tables.txt`)로 분리하고, Setup 단계(H-matrix 로드와 같은 시점)에서 1회 파싱해 Decoder 멤버 배열(heap)에 저장. 두 함수는 로컬 배열 대신 멤버 배열을 조회. 파싱은 init 1회라 성능 무관하고, 호출당 스택 복사가 사라져 `static const`와 동일한 속도 효과 + 재컴파일 없이 값 변경 가능.
  - 주의: (1) 인덱싱 구조(행/열 의미: 모드 × set × dv 구간)를 기존 배열과 동일하게 유지할 것 (2) 로드 시 값 개수/범위 sanity check (3) 재현성을 위해 결과 출력에 사용한 테이블 파일명 기록 (4) 소실된 초기화 리스트는 복원할 필요 없이 파일이 진실 소스가 됨 — 파일 내용은 원본(HW 팀) 값으로 채울 것

- [x] **2-10. `Init_Log_Data()` 가드** [bit-exact / 위험 낮음] — 프레임당 최대 ~45만 대입 제거 — 상세: [2-10_init_log_data_guard.md](2-10_init_log_data_guard.md)
  - 함수: `LDPC_Decoder()` 서두의 `Init_Log_Data()` 호출, `Alloc_Log_Data()`, `Padding_Zero_Log()`
  - 바꿀 부분: 로그 비활성 빌드에서도 매 프레임 로그 배열 전체(MN_size × (N_b + M_b + 2×z_sb + α))를 초기화
  - 방법: 호출부와 본체를 `#if defined(__LOG_DECODING_STATUS__)`(및 관련 로그 매크로)로 가드. `__AUTO_LLR_OPT__`용 CSW 로그만 별도 유지 확인.

- [x] **2-11. magnitude 도메인 변환 분기 체인 → 산술식** [bit-exact / 위험 낮음] — 상세: [2-11_mag_domain_arith.md](2-11_mag_domain_arith.md)
  - 함수: `C2V_Cal()`의 V→EDGE 변환(if V_VERY_STRONG → EDGE_MAG_7 식 3분기), `V2C_Store()`의 EDGE→V 역변환 2곳
  - 바꿀 부분: {0,1,2,3} ↔ {1,3,5,7} 고정 사상을 element마다 분기 체인으로 처리
  - 방법: 정방향 `check_out = (check_out_temp << 1) | 1;`, 역방향 `v2c_mag = check_in_mag >> 1;`. 유한 도메인 전수 일치 확인됨.
  - 주의: `__4_BIT_LLR__` 빌드는 도메인이 다르므로 해당 빌드용 식 별도 확인.

- [x] **2-12. `% 2` → `& 1` / `^ 1`** [bit-exact / 위험 낮음] — 상세: [2-12_mod2_to_bitand.md](2-12_mod2_to_bitand.md)
  - 함수: `C2V_Cal_New_Sgn()`의 `t = (synd + check_sum + edge_sgn) % 2`, CNU check_sum 갱신 2곳, VN_Cal 계열의 `(Variable_mem[...] + 1) % 2`, `Compute_CSW()` 등
  - 바꿀 부분: 피연산자가 전부 0/1(비음수)인데 signed `% 2` 사용 — MSVC가 음수 보정 시퀀스를 생성
  - 방법: `% 2` → `& 1`, `(v + 1) % 2` → `v ^ 1`, `new_sgn % 2 == 1`(new_sgn이 이미 0/1) → `new_sgn != 0`.

- [x] **2-13. VN_Cal 계열의 `Mux_idx` 재조회 제거** [bit-exact / 위험 낮음] — 상세: [2-13_mux_idx_cache.md](2-13_mux_idx_cache.md)
  - 함수: VN_Cal 계열 5종
  - 바꿀 부분: j(z_sb) × ii(v_deg) 이중 루프에서 매 반복 `mux_idx = m_PCM->Mux_idx[ii][col_idx]` 조회 — 합산 루프와 출력 루프에서 같은 값을 총 2×z_sb회 재조회, 게다가 `[dv][N_b]` 레이아웃이라 ii 증가마다 ~516B stride 점프
  - 방법: j 루프 진입 전에 `int mux[MAX_DV_GLOBAL]; for (ii...) mux[ii] = Mux_idx[ii][col_idx];` 1회 복사 후 루프에서는 `mux[ii]` 사용.

- [x] **2-14. bit_pos 영역 분류 테이블화** [bit-exact / 위험 낮음] — 상세: [2-14_bit_region_table.md](2-14_bit_region_table.md)
  - 함수: VN_Cal 계열 5종 + `VN_Cal_Pre()`
  - 바꿀 부분: element마다 최대 6구간 × 2비교로 shortening/puncturing/normal을 분류하는 if 체인 — 구간 경계는 시뮬레이션 전체 고정
  - 방법: Decoder 초기화에서 `uint8_t bit_region[N]` 테이블 1회 생성 → 루프에서는 `bit_region[bit_pos]` 조회(switch 또는 값 직접 사용).

- [x] **2-15. Clear 계열 memset화** [bit-exact / 위험 낮음] — 상세: [2-15_clear_memset.md](2-15_clear_memset.md)
  - 함수: `Clear_Edge_SRAM()` / `Clear_Edge_SRAM_Sgn()`(M×K), `Clear_Syndrome()`, `Clear_CN_REG()`, `Clear_Delay_REG()`, lfsr 4종 클리어
  - 바꿀 부분: 이중 루프 원소별 `= 0` 대입
  - 방법: 행별 `memset(ptr, 0, len * sizeof(int))` (0 채우기는 int에서 안전).

- [x] **2-16. `Clear_REG_min_value()` 무의미 분기 제거** [bit-exact / 위험 낮음] — 상세: [2-16_clear_reg_min_branch.md](2-16_clear_reg_min_branch.md)
  - 바꿀 부분: M 루프 안에서 HD/SD 모드를 비교하지만 양쪽 분기가 동일하게 `V_VERY_STRONG` 대입
  - 방법: 분기 제거 후 단일 채움 루프(또는 `Set_Array`).

- [x] **2-17. `VN_Cal_Pre()` cwc hard-decision 분기 축소** [bit-exact / 위험 낮음] — 상세: [2-17_vn_cal_pre_cwc.md](2-17_vn_cal_pre_cwc.md)
  - 바꿀 부분: `Variable_mem` 0/1 판정 후 puncture 구간 if 체인 3개가 전부 동일한 대입을 반복
  - 방법: `cwc[bit_pos] = Variable_mem[bit_pos];` 한 줄로 축소.
  - 주의: HCU판의 같은 패턴은 한 분기가 `cwc = 1`로 **다르므로 유지**.

- [x] **2-18. `Check_REG` 평탄화** [bit-exact / 위험 중간] — 상세: [2-18_check_reg_flatten.md](2-18_check_reg_flatten.md)
  - 바꿀 부분: 할당부의 `Check_REG = new int*[M]; 행마다 new int[2]` — M(4128)개의 8byte 힙 블록이 산재, 실사용 슬롯은 `IDX_CHECK_SUM` 하나뿐(`IDX_WEAK_NUM` 사용처 0건 확인)
  - 방법: `int* Check_REG` 단일 연속 배열(int[M])로 교체하고 접근부(`C2V_Cal`/`V2C_Store`/`Compute_CSW` 등) 치환.
  - 주의: TV Gen 모드의 `Print_TV_check_sum(int**, ...)` 시그니처는 변경 금지 — TV 빌드에서는 기존 구조 유지(#ifdef 분리)하거나 어댑터 유지.

- [x] **2-19. `V2C_Store()` wrapper의 `VNU_out3_temp` 복사 + no-op `PMU_Write()`** [현 파라미터에서 bit-exact / 위험 중간] — 상세: [2-19_pmu_noop_skip.md](2-19_pmu_noop_skip.md)
  - 바꿀 부분: 컬럼마다 J×z_sb 원소별 복사 후 `PMU_Write()` 호출 — `factor = z_sb / PMU_UNIT_SIZE = 32/128 = 0`이라 fragment 루프가 0회 실행되는 no-op
  - 방법: 최소한 복사를 memcpy화. 나아가 `z_sb < PMU_UNIT_SIZE`인 구성에서는 복사+호출 자체를 조기 return으로 스킵 (factor=0이면 Clk_Manager FIFO 루프도 0회라 overall_clk 영향 없음 — 적용 시 재확인).
  - 주의: HW 타이밍 시뮬 경로이므로 파라미터(z_sb, PMU_UNIT_SIZE) 변경 가능성을 주석으로 남길 것.

- [~] **2-20. V2C_Store 말미의 마지막-edge 검사를 호출자로 이동** — **제외 결정** (2026-07-23 일괄 진행 중)
  - 사유: 이득이 edge당 정수 비교 2회 수준으로 미미한 반면, 호출 경로가 일반/HCU 두 갈래라 이동 시 실수 위험이 더 큼. 효과/위험 비 불충족으로 스킵.

---

## Phase 3 — 프레임당 오버헤드 (CRC / 인코더 / 난수 / 프레임 루프)

- [x] **3-1. `partial_crc_HW_T4()`의 호출당 new/delete 제거** [bit-exact / 위험 낮음] — **효과 큼** — 상세: [3-1_partial_crc_stack.md](3-1_partial_crc_stack.md)
  - 함수: `partial_CRC.cpp partial_crc_HW_T4()`
  - 바꿀 부분: 함수 진입마다 `new int[CRC_LEN]` ×2 + `new int[DEC_D_LEN]` 할당, 종료 시 delete 3회 — 이 함수는 iteration당 column마다 호출되어 프레임당 수만 회 heap 연산 발생
  - 방법: 크기가 컴파일 타임 상수(80/256)이므로 지역 고정 배열 `int tmp1[CRC_LEN];`으로 교체 (스택 ~1.6KB). division 함수들(HW 생성 코드)은 일절 수정하지 않음.

- [x] **3-2. full CRC의 프레임당 517회 할당 제거** [bit-exact / 위험 낮음] — 상세: [3-2_full_crc_buffer_reuse.md](3-2_full_crc_buffer_reuse.md)
  - 함수: `full_CRC.cpp CRC_encoder()`, `CRC_decoder()` (두 오버로드)
  - 바꿀 부분: 호출마다 `msg = new int*[516]` + 행별 `new int[ZSB_CRC]` 516회 → 채우기 → `GEN_CRC80()` → 516회 delete
  - 방법: 버퍼를 1회 할당 후 재사용(static 또는 호출자 보유 멤버). 다항식·비트 순서는 불변.
  - 추가(선택, [검증 필요]): `GEN_CRC80()`이 user_data를 직접 순회하는 오버로드 추가 — 선두 80개 zero-bit는 all-zero LFSR 상태에서 no-op이므로 스킵 가능(수학적 동치). 적용 시 CRC 값 전수 비교.

- [x] **3-3. 인코더의 프레임마다 PCM 전처리 제거** [bit-exact / 위험 낮음] — 상세: [3-3_encoder_pcm_init.md](3-3_encoder_pcm_init.md)
  - 함수: `encoder.cpp LDPC_encoder_4KB()` (및 오버로드)
  - 바꿀 부분: 매 프레임 `Generate_PCM_encoding(PCM_b, PCM_b_enc, ...)` 호출 — PCM_b는 불변인데 M_b×N_b(수만 int) 복사+재배열을 반복
  - 방법: 호출을 `Init_Enc()`로 이동해 1회만 수행. (PCM_b가 런타임 중 변경되는 지점 없음 — 확인됨)

- [x] **3-4. 인코더 P 행렬(z_sb×z_sb) 사전 계산** [bit-exact(동일 로직 이동) / 위험 중간 → **인코더 출력 전수 비교 필수**] — 상세: [3-4_encoder_p_precompute.md](3-4_encoder_p_precompute.md)
  - 함수: `encoder.cpp LDPC_encoder_dual_diagonal()` (두 오버로드)
  - 바꿀 부분: 프레임마다 column j별로 32×32 P 행렬을 clear → 129행 스캔으로 재구축 → 32×32 곱 — P는 PCM만의 함수(메시지 무관)인데 매번 재구축
  - 방법(택1): (a) Init에서 column별 P를 전부 사전 계산(약 0.5MB) 후 프레임에서는 곱만. (b) column별 유효 shift 목록을 전처리하고 `Parity[r] ^= Msg[j*z_sb + (r+s) % z_sb]` 직접 XOR (중복 shift는 mod 2 상쇄 반영).

- [x] **3-5. 인코더 `% 2` → XOR** [bit-exact / 위험 낮음] — 상세: [3-5_encoder_xor.md](3-5_encoder_xor.md)
  - 함수: `LDPC_encoder_dual_diagonal()`의 parity 누적/back-substitution 루프 (두 오버로드 모두)
  - 바꿀 부분: `Parity[r] = (Parity[r] + x) % 2` 패턴 (값이 항상 0/1)
  - 방법: `Parity[r] ^= x;`, `(x + 1) % 2` → `x ^ 1`.

- [x] **3-6. `xor_r25()` 상태 시프트 제거** [bit-exact / 위험: memmove 낮음, circular 중간] — 상세: [3-6_xor25_memmove.md](3-6_xor25_memmove.md) (1단계 memmove만 적용, circular는 보류)
  - 함수: `random.cpp xor_r25()`
  - 바꿀 부분: 난수 1개 생성마다 `for (i=0..23) a[i] = a[i+1];` 24회 원소 이동 — 메시지 bit당 + AWGN bit당 호출되어 프레임당 수십만 회 이동
  - 방법: 1단계(안전): 루프를 `memmove(a, a+1, 24*sizeof(unsigned int))`로. 2단계(더 빠름): 내부를 circular index로 바꾸되 `Get_Random_Seed()`/`Set_Random_Seed()`에서 선형 배열로 정규화해 seed 파일 포맷·출력 시퀀스 완전 동일 유지. seed save/load 모드 전부 검증.

- [x] **3-7. `rand_sel_ep()`의 매 프레임 identity 재초기화 제거** [bit-exact / 위험 중간] — 상세: [3-7_rand_sel_ep_restore.md](3-7_rand_sel_ep_restore.md)
  - 함수: `random.cpp rand_sel_ep()`
  - 바꿀 부분: 부분 Fisher-Yates를 위해 매 프레임 len_noPS(수만) 크기 배열을 0..N-1로 재초기화 — 실제 섞이는 원소는 n_err_len개뿐
  - 방법: 사용한 swap 인덱스를 기록해 두었다가 역순으로 되돌려 identity 복원 → 다음 프레임 초기화 생략. 난수 소비 순서·선택 결과 동일. 복원 실수 시 이후 프레임이 오염되므로 단위 검증 필수.

- [x] **3-8. 프레임 루프의 5개 버퍼 원소별 복사 → memcpy** [bit-exact / 위험 낮음] — 상세: [3-8_frame_copy_memcpy.md](3-8_frame_copy_memcpy.md)
  - 함수: `ecc_top.cpp Run_Simulation()` (Ref-C/TV 경로 6곳의 동일 패턴)
  - 바꿀 부분: `for (n...) { m_HD_input[n] = m_HD_channel[n]; m_SD_input[n] = ...; }` — 5개 배열을 한 루프에서 동시 복사
  - 방법: 배열별 `memcpy` 5회로 분리. (복사 자체는 필요 — 디코더가 input을 파괴적으로 수정)

- [x] **3-9. SD 양자화 루프의 모드 분기 hoisting** [bit-exact / 위험 낮음] — 상세: [3-9_quantize_mode_hoist.md](3-9_quantize_mode_hoist.md)
  - 함수: `ecc_top.cpp Make_Dec_Input_AWGN_Quantize()`
  - 바꿀 부분: bit당 `init_n`(2SD/3SD/1.5SD) if-체인 + `Get_Mag_*()` 함수 호출 — `init_n`은 루프 불변
  - 방법: 분기를 루프 밖으로 꺼내 모드별 전용 루프로 분리. 추가로 `Get_Mag_*`를 `channel.h`로 옮겨 인라인화(자유 함수라 시그니처 무변경).

- [x] **3-10. 에러 주입 flip `% 2` 제거** [bit-exact / 위험 낮음] — 상세: [3-10_error_flip_xor.md](3-10_error_flip_xor.md)
  - 함수: `ecc_top.cpp Make_Dec_Input_Fixed_4KB()`
  - 바꿀 부분: `HD_input[pos] = (HD_input[pos] + 1) % 2` — 이중 인덱싱 2회 + add/mod
  - 방법: `HD_input[m_err_position[n]] ^= 1;`

- [x] **3-11. `Print_Seed()` 파일 핸들 유지** [bit-exact(파일 내용 동일) / 위험 낮음] — 상세: [3-11_print_seed_handle.md](3-11_print_seed_handle.md)
  - 함수: `random.cpp Print_Seed()` + 호출부 `Run_Simulation()`
  - 바꿀 부분: 이벤트마다 `fopen(..., "a")` → fprintf ~26회 → `fclose` — `MODE_SEED_SAVE_ALL_SEED`에서는 **매 프레임** open/close
  - 방법: 시뮬레이션 시작 시 1회 open해 핸들 유지(이미 인자로 받는 `fp_uncor_seed`가 있으나 무시되고 있음), 주기적 `fflush`로 크래시 대비.

- [x] **3-12. `__SHOW_RBER_DIST__` 경로 fopen 제거** [bit-exact / 위험 낮음] — 상세: [3-12_14_ecc_top_misc.md](3-12_14_ecc_top_misc.md)

- [x] **3-13. `Load_Dec_Input_Vector_Format()` 임시 버퍼 승격** [bit-exact / 위험 낮음] — 상세: [3-12_14_ecc_top_misc.md](3-12_14_ecc_top_misc.md)

- [x] **3-14. 메시지 invert/copy 루프 정리** [bit-exact / 위험 낮음] — 상세: [3-12_14_ecc_top_misc.md](3-12_14_ecc_top_misc.md)
  - 함수: `Run_Simulation()`의 `m_inv_msg[n] = (m_msg[n] + 1) % 2` 및 all-zero codeword 모드의 원소별 copy
  - 방법: `^ 1` 및 memcpy로 치환.

---

## Phase 4 — 메모리 레이아웃 (수정 범위 큼, 효과 중간 — 선택 적용)

- [x] **4-3. CN 상태 struct 묶음** [bit-exact / 위험 중간] — 상세: [4-3_cn_state_struct.md](4-3_cn_state_struct.md)
  - 대상: `REG_min1_pos` / `REG_min1_value` / `REG_min2_value` / `Syndrome` / `Check_REG` — C2V_Cal의 z 루프 1회에 같은 row로 5~6개 배열을 각각 접근(캐시 라인 6개 터치)
  - 방법: `struct CN_STATE { min1_pos; min1_value; min2_value; check_sum; syndrome; }` 단일 배열로 통합 (Clear 계열 포함 전면 치환 필요). TV 시그니처는 뷰 어댑터 2종 추가로 보존.
  - 부수 수정: `Print_TV_Cycle_Based` 본문 `__ECC_TV__` 가드 — 2-18부터 있던 비TV 빌드 컴파일 회귀 해소.

- [x] **4-4. 0/1 값 배열의 int → int8_t 축소** [bit-exact(산술은 int 승격) / 위험 중간] — 상세: [4-4_int8_narrowing.md](4-4_int8_narrowing.md)
  - 대상: `Check_SRAM_sgn`(429KB→107KB), `Variable_mem`, `cwc` — 전 대입 지점 0/1 확인 완료
  - 제외: `Syndrome`(4-3 struct 필드 — 패딩 때문에 이득 0), `prev_cwc`(사용처 0건)
  - 방법: `int8_t` 축소 + int 표현식 대입만 명시 캐스트. CRC/TV `int*` 경계는 뷰 어댑터(`Get_Cwc_View` 등)로 시그니처 보존. `Init_Buf` 혼용 0건 확인.

---

## Phase 5 — 별도 분류: 결과(난수열/비트 시퀀스)가 달라질 수 있음 (적용 = Decision, 사용자 결정)
- [x] **5-6. `xor_r25` double 왕복 제거** — **전 범위(2^32) 전수 검증 통과 → bit-exact 승격, 적용 완료** — 상세: [5-6_xor25_no_double.md](5-6_xor25_no_double.md)
  - 검증: w = 0~2^32-1 전부에서 `(unsigned)(w/4294967295.0 * 4294967295) == w` 확인 (mismatch 0, MSVC x64 /O2 /fp:precise). 수학적 근거: M=2^32-1 < 2^32이라 왕복 오차가 ½ulp 미만 → 항상 정확 복귀
  - 방법: 정수 경로 `xor_r25_u32()` 신설, 정수 소비처 3곳 + 시드 전진 1곳 교체. `Gaussian_xor25`(실수 소비처)는 유지.

---

## Phase 6 — 성능과 별개로 발견된 잠재 버그 (수정 = Decision, 사용자 확인 필요)

- [x] **6-1. `PMU_Read()` 범위 밖 읽기** — **적용 완료** — 상세: [6-1_6-2_oob_fixes.md](6-1_6-2_oob_fixes.md)
  - `sram_inst_num`의 하드코딩 2(z_sb=256 시절 fragment 수)를 factor로 교체 → 현 파라미터(factor=0)에서 루프 0회로 자연 해소 + clk당 낭비 제거
  - 적용 중 발견: `MAIN_SRAM_read_rq[n]` **OOB 쓰기**(길이 0 배열)도 동반하던 상태였고, `PMU_Read_HCU()`에도 동일 버그 존재 → 함께 수정
- [x] **6-2. `DU_Manager()` 범위 밖 읽기** — **적용 완료** — 상세: [6-1_6-2_oob_fixes.md](6-1_6-2_oob_fixes.md)
  - 6개 블록 모두 범위 검사 `(col >= 0) && (col+1 < N_b)`를 ColW 접근 앞으로 이동. 범위 밖 col은 기존 의도대로 결정적 FALSE. (DU_ok 테이블화는 미적용 — 버그 수정만)

---

## 권장 적용 순서

> **원칙: 결과가 바뀔 수 없는 항목을 전부 끝낸 뒤, 맨 마지막에 UB 수정(6-1/6-2)을 얹는다.**
>
> 이유 — 1단계 항목은 전부 bit-exact라 **golden과 1비트라도 다르면 100% 적용 실수**다. 반면 6-1/6-2는
> 기존 코드의 미정의 동작(범위 밖 접근)을 없애는 수정이라 **golden과 달라지는 것이 정상일 수 있다**.
> 두 종류를 섞어서 적용하면 불일치가 났을 때 "내 실수"인지 "원래 코드가 UB였던 것"인지 구분이 불가능해진다.

### 1단계 — 순수 최적화 (golden과 **완전 일치**해야 함)

1. **Phase 2 (2-1 ~ 2-19)** — 핫루프. 효과가 가장 큼. 항목마다 커밋 + Ref-C diff 검증.
   TV 근처 항목(2-5·2-6·2-7·2-18)은 **TV Gen hex diff까지** 추가로 확인
2. **Phase 3 (3-1 ~ 3-14)** — 프레임당 heap/전처리 제거. 3-1·3-2·3-3 효과가 큼
3. **Phase 4 (4-3, 4-4)** — 메모리 레이아웃. 수정 범위가 넓으므로 프로파일링으로 병목 확인 후 선택 적용
4. **5-6** — 정수 경로 분리. 적용 전 문서의 왕복 전수 검증 프로그램을 **대상 환경에서 1회 재실행**

**이 시점에서 반드시 golden 완전 일치를 확인하고 넘어갈 것.** 여기까지가 "결과 불변" 보증 구간이다.

### 2단계 — UB 수정 (golden과 **달라질 수 있음**, 차이가 나면 새 값이 정답)

5. **6-1 / 6-2** — 범위 밖 접근 해소. 상세: [6-1_6-2_oob_fixes.md](6-1_6-2_oob_fixes.md)
   - 1단계와 **반드시 커밋을 분리**할 것. 이 저장소에서는 `96509fe`(5-6까지)가 1단계 경계, `ef4238e`가 2단계
   - 차이가 발생하면 6-1과 6-2를 **각각 따로** 얹어 원인을 분리
   - 판단 기준: 기존 코드가 읽던 값이 쓰레기값이었으므로, 새 결과가 올바른 값이다

### 검증 시 함께 볼 것

FER뿐 아니라 **프레임별 iteration 수 / uncor 프레임 번호 / `o_overall_clk`(HW 타이밍) / TV hex**까지 비교한다.
최종 FER가 같아도 중간값이 다르면 HW 검증용으로 못 쓴다.
