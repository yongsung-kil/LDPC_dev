# Round 2 / agent_1 — [V1. C++ 대조: syndrome-aided 디코더] 분석

> 작성: 2026-08-06 23:07:59
> 관점: Round 1 agent_1 "P1. C++ 대응 정확성 — syndrome-aided HD 디코딩 본체" 13개 항목 전체 +
> Round 1 agent_2 "P1. 원본 C++ 원문과의 산술 대조" ㉮~㉴, "P2. flip 도메인 상태 갱신과 genie 판정" ㉮~㉲
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/decoder.py` `_decode_matrix()`(319-446),
> `_mx_vnu_quantize()`(90-102), `pcm.py` `syndrome()`(78-85)
> 대조 원본: `0_LDPC_original/decoder.cpp`, `common.h`, `mode.h`, `local_opt.cpp` (읽기 전용, 빌드 안 함)

---

## 0. 결론

**핵심 산술은 원문과 일치한다.** 13개 대조 항목과 agent_2의 12개 항목을 원문 행 단위로 짝지어
확인한 결과, `_decode_matrix()`의 flip/magnitude 도메인 재현은 정확하다. 틀린 결과를 내는
HIGH 이상 결함은 발견하지 못했다. 다만 **입력 데이터 가정에 의존하는 MEDIUM 1건**과
**빌드 스위치 의존을 코드에 드러내지 않은 LOW 3건**을 지적한다.

발견: MEDIUM 1건, LOW 4건. (CRITICAL 0, HIGH 0)

---

## 1. 확인한 빌드 전제 (대조의 기준선)

Python이 재현 대상으로 삼은 것은 `__AUTO_LLR_OPT__` 빌드다. 이 전제가 성립하는지 먼저 확인했다.

| 스위치 | 상태 | 근거 |
|---|---|---|
| `__AUTO_LLR_OPT__` | `__PROGRAM_MODE_REF_C__` + 비Windows에서 정의 | `mode.h:18-27` |
| `__4_BIT_LLR__` | 주석 처리 (3-bit 경로) | `mode.h:12` |
| `__RUN_PREPROCESSING__` | 주석 처리 | `mode.h:63` |
| `__HD_FLOOR_SET__` | 주석 처리 | `mode.h:73` |
| `__LLR_TWO_DV3__` | 주석 처리 | `mode.h:9` |
| `ITER_MAX_HBF` | AUTO 빌드에서 **0** | `common.h:403-407` |
| `flag_BF_on` | AUTO 빌드에서 `Select_BF()`가 **무조건 FLAG_LOW** | `decoder.cpp:2082-2085` |
| `Adjust_HD_Floor_Type` | `__HD_FLOOR_SET__` 없으면 `state_hd_error_floor_set = TYPE_0` 대입만 | `decoder.cpp:8108-8113` |
| `store_checksum_REG/min_REG/edge_SRAM` | 일반 경로 호출은 전부 `TRUE` | `decoder.cpp:2627` |

→ `차이.md` §1 #2(BF 비활성), #3(floor 상태머신 무영향)의 근거는 **소스에서 확인된다**.
`Adjust_HD_Floor_Type`이 갱신하는 `state_hd_error_floor_set`은 AUTO 경로의 그룹/row 선택
(`decoder.cpp:6984-6999`, `7051-7068`)에서 **에러 printf 인자로만** 쓰이므로 선택 결과에 영향이 없다
(`decoder.cpp:7049`, `7070`).

---

## 2. 항목별 대조 결과 (agent_1 P1 표 13개)

### ㉮ flip 도메인 채널 항이 "항상 +ch"인가 — **일치**

- C++ `decoder.cpp:4026` `sum_t = channel_llr;` — `channel_llr`은 `bTable` 경로에서
  `ch1`(테이블 값)이며(`decoder.cpp:4017-4020`), read bit `Variable_mem`의 부호가 실리지 않는다.
- Python `decoder.py:387-388` `total = np.broadcast_to(ch_cur[:, dvmap[j], None], ...)` — 부호 없음.
- read bit는 판정에만 쓰인다: C++ `decoder.cpp:4044-4045`
  `if (sum_t > 0) cwc = Variable_mem; else cwc = (Variable_mem + 1) % 2;`
  ↔ Python `decoder.py:398-399` `flip = total <= 0; bit_err = r_bit[:, j, :] ^ flip`.

### ㉯ VN 판정 `total <= 0` 동점 반전 — **일치**

`decoder.cpp:4044`는 `sum_t > 0`일 때만 유지, 즉 `sum_t == 0`이면 반전이다.
Python `decoder.py:398` `flip = total <= 0`. 등호 위치까지 같다.

### ㉰ C2V sign = `synd ^ csum ^ esgn`과 세 피연산자 정렬 — **일치**

- C++ `decoder.cpp:2367-2371`: `synd = Syndrome[row_idx_r]`, `check_sum = Check_REG[row_idx_r][IDX_CHECK_SUM]`,
  `edge_sgn = Check_SRAM_sgn[row_idx_r][position_c]` — **셋 다 같은 `row_idx_r`(CN lane)** 로 인덱싱한 뒤
  `decoder.cpp:2333` `t = (synd + check_sum + edge_sgn) % 2`로 합성하고, 결과를
  `VNU_in[mux_index][j]`(VN lane)에 넣는다. 즉 CN 정렬에서 XOR → VN 정렬로 이동.
- Python `decoder.py:393-394`:
  `sgn = (synd[:, i, :] ^ csum[:, i, :] ^ esgn[:, e, :])` (전부 CN 정렬) →
  `np.roll(..., s, axis=-1)`로 VN 정렬. **동일 구조.**
- `iter` 인자의 역할: `C2V_Cal_New_Sgn`(`decoder.cpp:2299`)에서 `iter`는
  `Is_Iter_Type_Edge_Clear(iter)`일 때 `edge_sgn = 0`으로 강제하는 데만 쓰인다(`2321-2324`).
  Python은 edge clear iteration에서 `esgn`이 0으로 유지되므로 자동으로 같은 결과다.
  (C++ 쪽도 `Clear_Edge_SRAM_Sgn()`으로 이미 0이라 이 강제는 중복 방어다.)

### ㉱ Edge Clear 조건과 remove-old 생략 범위 — **일치 (조건식은 상수 접힘에 의존, LOW-2 참조)**

- 호출 시점: `decoder.cpp:1133` `Clear_Edge_Restart();` — **iteration 진입 직후, column 루프 전**.
  Python `decoder.py:373-379`도 column 루프 전. 일치.
- 조건: `Is_Iter_Type_Edge_Clear`(`decoder.cpp:6538-6553`)는 AUTO+HD에서
  `iter == 0 || iter == 1 || iter == ITER_MAX_HBF + 1 || iter ∈ restart_iter[]`.
  `ITER_MAX_HBF = 0`(`common.h:404`)이므로 `ITER_MAX_HBF+1 == 1`로 접혀
  실질 조건은 `iter ∈ {0, 1} ∪ restart_iter`. Python `decoder.py:373` `it == 1 or mx.is_restart(it)`와
  (iteration 0을 별도 처리하므로) 등가.
- 클리어 범위: `Clear_Edge_Restart`(`decoder.cpp:711-724`)는 HD에서
  `Clear_REG_min_pos` / `Clear_REG_min_value(TRUE,TRUE)` / `Clear_CN_REG(IDX_CHECK_SUM)` /
  `Clear_Edge_SRAM_Sgn`만 수행하고 **`Clear_Syndrome`은 호출하지 않는다**(717행 주석 명시).
  Python `decoder.py:374-379`가 `min1/min2/pos/csum/esgn`만 지우고 `synd`는 유지하는 것과 일치.
- remove-old 생략 범위: **그 iteration 전체**다. `CNU_Remove_Old_Sgn`(`decoder.cpp:3498-3500`)이
  `Is_Iter_Type_Edge_Clear(iter)`면 `pre_v2c_sgn = 0`으로 두므로 iteration 내내 check_sum 제거가 없다.
  Python `decoder.py:413` `if not edge_clear:`가 iteration 전체를 감싸는 것과 일치.
- 다만 C++는 min 쪽 제거(`min1_pos == cur_pos_p2` 분기)를 **edge clear iteration에서도 실행한다**
  (`CNU_Update_New_Mag` 안에 있고 `iter` 가드가 없음, `decoder.cpp:3518-3526`). Python은 통째로 건너뛴다.
  → 등가성 근거: 클리어 직후 `min1 = min2 = V_VERY_STRONG`이라 `min1 = min2; min2 = V_VERY_STRONG`이
  수치적 무연산이다. **결과 동일.** (LOW-3 참조)

### ㉲ RESET 값과 min_pos 기본값 — **일치 (단조 일대일 대응)**

- `Clear_REG_min_value`(`decoder.cpp:926-953`): HD에서 min1, min2 모두 `V_VERY_STRONG`.
- `common.h:338-346`: `V_VERY_STRONG = 3`, `EDGE_MAG_7 = 7`.
  min1/min2는 **V 도메인 코드 {0,1,2,3}** 를 저장하고, `C2V_Cal`(`decoder.cpp:2402-2405`)에서
  `V_VERY_STRONG→EDGE_MAG_7 / V_NORMAL_STRONG→5 / V_NORMAL_WEAK→3 / else→1`로 변환해 쓴다.
  반대로 `V2C_Store`(`decoder.cpp:2766-2769`)가 EDGE→V로 되돌려 저장한다.
- Python `decoder.py:353`은 EDGE 값 7을 직접 저장한다. 두 도메인의 사상은
  0↔1, 1↔3, 2↔5, 3↔7의 **순서 보존 전단사**이므로 `<=` 비교와 min 선택 결과가 동일하고,
  합(`sum_t`)에 실리는 값은 양쪽 모두 EDGE 값이다. → `차이.md` §2 #11 주장 **검증됨**.
- `Get_Default_Min_Pos`(`decoder.cpp:5453-5457`)는 **0을 반환한다** (-1이 아니다).
  Python은 -1을 쓴다. 등가 조건은 위 ㉱의 무연산 논거와 동일하며 성립한다.
  → `차이.md` §2 #12 주장 **검증됨** (단, 근거는 "min1=min2=RESET"만이 아니라
  "edge clear iteration에서 min 제거 분기가 무연산"까지 필요하다 — LOW-3).

### ㉳ insert-new `<=` 비교와 min1 교체 시 min2=RESET — **일치**

C++ `CNU_Update_New_Mag`(`decoder.cpp:3514-3544`) 원문:

```c
if (*min1_pos == cur_pos_p2) { *min1_value = *min2_value; *min2_value = V_VERY_STRONG; }
if (v2c_mag <= *min1_value)  { *min1_value = v2c_mag; *min1_pos = cur_pos_p2; *min2_value = V_VERY_STRONG; }
else if (v2c_mag <= *min2_value) { *min2_value = v2c_mag; }
```

Python `decoder.py:415-423`:

```python
was1 = p == e
m1 = np.where(was1, m2, m1);  m2 = np.where(was1, RESET, m2)
le1 = mag_new <= m1;  le2 = mag_new <= m2
min2[:, i, :] = np.where(le1, RESET, np.where(le2, mag_new, m2))
min1[:, i, :] = np.where(le1, mag_new, m1)
pos[:, i, :]  = np.where(le1, e, p)
```

- `<=` 비교 방향, 제거 후 갱신된 `m1`으로 비교하는 순서, min1 교체 시 min2를 RESET으로 되돌리는
  (기존 min1을 min2로 내리지 않는) HW 근사까지 모두 일치.
- **min1_pos 갱신의 원문 특이점까지 재현되어 있다**: C++는 제거 분기에서 `min1_pos`를 건드리지 않으므로,
  제거만 일어나고 삽입이 min1을 잡지 못하면 `min1_pos`가 `cur_pos`를 가리킨 채 `min1_value`는
  다른 edge의 값이 되는 상태가 남는다. Python도 `p`를 제거 분기에서 갱신하지 않아 동일하게 동작한다.
- `update_flag` / `cur_pos_p2`는 재현 대상에서 빠져도 무방하다:
  `update_flag`는 `__ECC_TV__` 출력에만 쓰이고(`decoder.cpp:2816-2821`),
  호출부(`decoder.cpp:2807`)가 `cur_pos`와 `cur_pos_p2`에 **같은 `position_c`** 를 넘긴다.

### ㉴ remove-old의 min2 복원 값과 `col_idx` 인자 — **일치**

- 복원 값은 `V_VERY_STRONG`(= RESET). `decoder.cpp:3523`. Python `decoder.py:417` `RESET`. 일치.
- `CNU_Remove_Old_Sgn`(`decoder.cpp:3476`)의 `col_idx`는 `__RUN_PREPROCESSING__` 블록
  (`decoder.cpp:3480-3496`)에서만 쓰이며, 그 스위치는 `mode.h:63`에서 주석 처리되어 있다.
  → 재현 불필요. `#else` 경로(`decoder.cpp:3497-3501`)만 유효하고 Python이 그것과 같다.
- 제거에 쓰는 값의 출처: C++는 `pre_exist_sgn_reg3[mux_idx][j]`(C2V 시점에 읽은 edge_sgn의
  3클록 지연 사본, `decoder.cpp:2411`, `2772`), Python은 `esgn[:, e, :]`.
  edge e의 `esgn` 쓰기(`decoder.py:425`)는 같은 iteration의 C2V 읽기(`393`)와 제거 읽기(`414`)
  **뒤에** 일어나므로 값이 같다. 정렬도 양쪽 다 CN lane이다
  (`pre_exist_sgn_reg[mux][z_mem_shift[j]]` 쓰기 ↔ `[mux][j]` 읽기, 둘 다 CN lane 인덱스).

### ㉵ VNU 양자화 (`raw = total − c2v`, `|raw|` vs th, `raw == 0`이면 sign은 c2v) — **일치 (단 LOW→MEDIUM-1 참조)**

C++ `VN_Cal_HD`(`decoder.cpp:4050-4120`):

```c
temp = sum_t - VNU_in[mux_idx][j];   temp_m = abs(temp);
if (temp_m == 0) {                                  // decoder.cpp:4082
    if      (temp_m >= th1) temp_m = EDGE_MAG_7;    // 4093-4096
    else if (temp_m >= th2) temp_m = EDGE_MAG_5;
    else if (temp_m >= th3) temp_m = EDGE_MAG_3;
    else                    temp_m = EDGE_MAG_1;
    if (VNU_in[mux_idx][j] > 0) temp = temp_m; else temp = -temp_m;   // 4098-4099
} else {
    ... 동일 캐스케이드 ...                          // 4112-4115
    if (temp > 0) temp = temp_m; else temp = -temp_m; // 4117-4118
}
```

Python `decoder.py:406-407`, `90-102`:
`raw = total - c2v` ↔ `sum_t - VNU_in` (`decoder.cpp:4052`) — 일치.
`m = np.abs(raw)` ↔ `temp_m = abs(temp)` — 일치.
`raw == 0`일 때 `sgn_z = np.where(c2v > 0, +1, -1)` ↔ `if (VNU_in > 0) + else −` — 일치
(`c2v == 0`이면 양쪽 다 음수). 0이 아닐 때 `raw > 0`으로 부호 결정 — 일치.
`raw == 0`인 경우에도 C++가 magnitude 캐스케이드를 **`temp_m = 0`으로 그대로 타는** 점까지
Python이 그대로 따른다(별도 분기 없음). 일치.
`th = -1`(restart row)일 때 `0 >= -1`이 참 → EDGE_MAG_7 ↔ Python `0 < -1`이 거짓 → lvl 0 → 7. 일치.

**주의**: Python은 캐스케이드 대신 지시함수 합(`decoder.py:94-96`)을 쓴다. th 내림차순 전제 필요. → MEDIUM-1.

### ㉶ CSW 정의와 갱신 시점 — **일치**

- `Compute_CSW`(`decoder.cpp:7293-7304`)와 `Compute_CSW_Auto`(`decoder.cpp:7340-7351`)는
  **본문이 완전히 동일하다** (`Σ_{i<M} ((Check_REG[i][IDX_CHECK_SUM] + Syndrome[i]) % 2)`).
  차이는 `Compute_CSW_Auto`가 `#ifdef __AUTO_LLR_OPT__`로 감싸여 있고 로그용
  (`decoder.cpp:1917-1921`, `flag_print_CSW_log`)이라는 점뿐이다.
  실제 row 선택에 쓰이는 `prev_CSW`를 세팅하는 것은 **`Compute_CSW` 쪽**이다(`decoder.cpp:3464-3465`).
- 갱신 시점: `decoder.cpp:3462-3465` — `jj == N_b-1 && ii == ColW[jj]-1`, 즉
  **마지막 column의 마지막 edge를 store한 직후 = iteration 종료 시점**.
  Python `decoder.py:427`은 column 루프 종료 직후. 일치.
- 범위도 `m_PCM->M`(= M_b × z) 전체 ↔ `(csum ^ synd).sum(axis=(-2,-1))`. 일치.

### ㉷ `prev_csw` 초기값과 `Get_Cur_LLR_Idx_FILE` 호출 시점의 선후 — **일치**

- 호출 시점: `decoder.cpp:1136-1145` — iteration 루프 맨 앞에서
  `if (mn > 0) cur_set_idx = Get_Cur_LLR_Idx_FILE(mn); else cur_set_idx = 0;`.
  `Set_CSW`(`decoder.cpp:6680-6682` `prev_CSW = w;`)는 직전 iteration의 끝(`decoder.cpp:3465`)에서
  호출되므로, iteration `k`는 **iteration `k-1`의 CSW**를 쓴다.
  Python `decoder.py:380` `row_idx = mx.row_index(it, prev_csw)`가 iteration 시작에서
  직전 iteration 말미(`427`)의 값을 쓰는 것과 일치.
- iteration 1 진입 시 `prev_CSW = |synd|`의 근거: iteration 0에서
  `Syndrome[j] = Check_REG[j][IDX_CHECK_SUM]` 복사 후 **`Check_REG[j] = 0`으로 리셋**하고
  (`decoder.cpp:2996-3008`), 같은 `V2C_Store` 호출의 뒷부분(`decoder.cpp:3462-3465`)에서
  `Compute_CSW()`가 `Σ((0 + Syndrome[i]) % 2) = |Syndrome|`을 계산한다.
  Python `decoder.py:355` `prev_csw = synd.sum(...)`와 **정확히 일치**.
  두 블록이 같은 `(jj, ii)` 조건에서 순차 실행되는 것을 행 번호(2996 < 3462)로 확인했다.

### ㉸ iteration 0을 `H·r` 직접 계산으로 대체한 등가성 — **일치**

- `VN_Cal_Pre`(`decoder.cpp:3554`)의 HD 경로는 일반 bit 위치에서
  `VNU_out[mux_idx][i] = int((Variable_mem[bit_pos] * (-2) + 1) * EDGE_MAG_3)`
  (`decoder.cpp:3598`, `3606`) — 즉 **부호만 read bit `r`이고 magnitude는 EDGE_MAG_3 고정**이다.
  채널 magnitude가 섞이지 않는다.
- `V2C_Store`가 이 부호를 `v2c_sgn`으로 뽑아(`decoder.cpp:2754-2755`)
  `CNU_Update_New_Sgn`으로 check_sum에 누적하고(`decoder.cpp:2776`, `3545-3548`),
  iteration 0은 edge clear이므로 제거 항이 0이다(`decoder.cpp:3498-3500`).
  결과적으로 check_sum = `Σ_edges r` = `H·r`. 이를 `Syndrome[]`로 복사한다(`decoder.cpp:2998`).
- `Is_Iter_Type_Init`(`decoder.cpp:6609-6614`)는 AUTO+HD에서 **iter == 0에서만 TRUE**이므로
  syndrome은 restart iteration에서도 재계산되지 않고 유지된다. Python `decoder.py:354`가
  1회 계산 후 고정하는 것과 일치.
- 정렬 정합도 확인했다. `pcm.py:84` `syn[..., i, :] ^= np.roll(bits[..., j, :], -s, axis=-1)`는
  CN lane k ← VN lane (k+s)이고, `decoder.py:408` `v2c = np.roll(v2c, -s, axis=-1)`도 같은 방향이다.
  따라서 `csum`이 누적하는 lane 정렬과 `synd`의 lane 정렬이 같다.
  (`decoder.py:394`의 C2V는 역방향 `+s`로 VN 정렬 복귀 — 짝이 맞는다.)
- iteration 0에서 min/pos에 쌓인 값(EDGE_MAG_3 → V_NORMAL_WEAK)은 iteration 1의 edge clear에서
  전부 지워지므로(`Is_Iter_Type_Edge_Clear(1) == TRUE`) Python이 min을 RESET에서 시작하는 것과 일치.
- read bit `r`(= `Variable_mem`)은 디코딩 중 갱신되지 않는다. `Variable_mem[...] =` 대입은
  입력 설정(`decoder.cpp:1056-1088`), genie puncture recovery(`1177`, `3016`), HCU/puncture 복구
  (`1293-1386`, `3202` 등)에만 있고, 판정 결과는 **`cwc[]`에 따로 쓴다**(`decoder.cpp:4044-4045`).
  → agent_2 P2 ㉮ 확인 완료: Python이 `r_bit`을 고정하는 것이 원본과 같다.
  (단 `__RUN_PUNCT_RECOVERY__`가 `mode.h:61`에서 **정의되어 있어** 펑처링 bit에 대해서는
  `Variable_mem`이 갱신된다. 펑처링은 명시적 비교 제외 대상이므로 스코프 내에서는 무관.)

### ㉹ genie 판정이 column 루프 도중 누적되는 정의 — **원본과 등가 (문제 없음)**

Round 1이 "앞 column에서 에러였다가 뒤 column 처리로 정정된 프레임"을 우려했는데,
원문과 대조하면 **오히려 등가**다.

- C++는 `cwc[bit_pos]`를 각 column의 VN 처리 시점에 1회 기록하고(`decoder.cpp:4044-4045`),
  iteration 종료 후 `Check_End_Iter`(`decoder.cpp:1951`) 또는 genie PCRC
  (`Check_Genie_PCRC`, `decoder.cpp:2256-2266`, `cwc[q] != m_genie_inv_cw[q]` 전수 비교)로
  **`cwc[]` 배열 전체**를 본다.
- iteration 종료 시점의 `cwc[]`는 "각 column이 자기 처리 시점에 내린 판정"의 모음이다.
  따라서 `cwc[] 전부 정답` ≡ `모든 column이 자기 처리 시점에 정답` ≡
  Python의 `~frame_err` (`decoder.py:400`, `431`).
- 즉 column 루프 도중 OR 누적은 "중간 상태를 낙관/비관적으로 본 것"이 아니라
  원본의 iteration-종료 스냅샷과 **정확히 같은 집합**을 만든다.
- `n_iter`도 1-base로 일치한다 (`iter_num = mn`, `decoder.cpp:4965`; Python `decoder.py:434`).
- 배치 압축(`decoder.py:435-441`)은 프레임 독립이므로 결과 불변이다.
  `row_index`도 프레임별 `prev_csw`만 보고 배치 인덱스에 의존하지 않는다(`llr_matrix.py:160-177`).

### ㉺ `cn_mag_fn()`이 `_decode_matrix()`에서 호출되지 않음 — **원본 대조상 올바름**

`C2V_Cal`(`decoder.cpp:2386-2406`)의 AUTO/3-bit 경로에는 offset/normalization이 없다.
min 값을 V→EDGE로 사상할 뿐이다. 따라서 `decoder.py:392`가 `cn_mag_fn`을 부르지 않는 것이
**원문에 맞다**. (다른 두 경로에는 훅이 있어 논문 아이디어 진입점이 경로별로 다르다는 점은
설계 관점 지적이며 정확성 결함은 아니다 — LOW-4.)

---

## 3. agent_2 P1/P2 추가 항목

| 항목 | 결과 |
|---|---|
| P1 ㉮ 세 피연산자 정렬 | 일치 (§2 ㉰) |
| P1 ㉯ `sum_t <= 0` 동점 | 일치 (§2 ㉯) |
| P1 ㉰ 클리어 범위, 직후 magnitude | 일치. 클리어 직후 C2V magnitude는 `V_VERY_STRONG → EDGE_MAG_7`(`decoder.cpp:2402`) |
| P1 ㉱ `V_VERY_STRONG` 도메인 | `common.h:338`에서 **3**. EDGE 도메인 7과 다른 값이나 단조 사상으로 등가 (§2 ㉲). 채널 LLR 도메인(0~31, `common.h:375-376`)과는 섞이지 않는다 — 채널은 `sum_t` 초기값으로만 들어가고 min 레지스터에는 안 들어간다 |
| P1 ㉲ `<=`와 min2=RESET | 일치 (§2 ㉳) |
| P1 ㉳ iteration 0 대체 | 일치 (§2 ㉸) |
| P1 ㉴ `Compute_CSW` 참조 시점 | iteration 종료 후 (§2 ㉶) |
| P2 ㉮ `r_bit` 불변 | 일치 (§2 ㉸ 말미) |
| P2 ㉯㉰ genie 정의 | 원본과 등가 (§2 ㉹). 세 경로 정의는 동일 형태이나 비교 대상이 다르다: `_decode_matrix`는 `r ^ (total<=0)`, 다른 두 경로는 `total < 0` (signed 도메인) — 각자 도메인에 맞음 |
| P2 ㉱ `n_iter`와 배치 제외 | 일관 (§2 ㉹) |
| P2 ㉲ 실패 프레임 `n_iter=0` | `sim.py` 소관 (다른 관점) |

---

## 4. 지적 사항

### MEDIUM-1. `_mx_vnu_quantize`의 임계 비교가 "th 내림차순" 입력 가정에 의존

- 위치: `decoder.py:94-96` (동일 문제가 `decoder.py:81` `_vnu_quantize`에도 있음)
- 원문: `decoder.cpp:4112-4115`는 **캐스케이드**다.
  `if (temp_m >= th1) 7; else if (>= th2) 5; else if (>= th3) 3; else 1;`
- Python:
  ```python
  lvl = ((m < th[:, 0, None]).astype(np.int8) + (m < th[:, 1, None]) + (m < th[:, 2, None]))
  mag = self._edge_mag[lvl]
  ```
  이는 **th1 >= th2 >= th3일 때만** 캐스케이드와 같다.
- 반례: th = (5, 10, 3), m = 7 → C++는 `7 >= 5` → EDGE_MAG_7. Python은 `(7<5)+(7<10)+(7<3) = 1` → EDGE 5.
- 현재 입력 2개(`Input/LLR/LLR_MATRIX_HD_0.txt`, `HD_1.txt`)는 네 dv 구간 모두 내림차순
  ((28,9,5) / (10,9,4) / (31,10,7) / (12,10,8))이라 재현되지 않는다. restart row의 (-1,-1,-1)도
  전부 같은 값이라 무해하다.
- 위험: DAO 최적화기는 파라미터를 개별 섭동하므로 비단조 th가 산출될 수 있고, 그때 **에러 없이
  FER만 달라진다**. 실물 LLR matrix 반입 시 최초로 드러날 수 있는 유형이다.
- 제안: `llr_matrix.LLRMatrix._validate()`에서 `row_th`의 dv별 내림차순(또는 -1 전부 동일)을 검사해
  위반 시 에러를 내거나, `_mx_vnu_quantize`를 `np.select` 캐스케이드로 바꾼다.

### LOW-2. Edge clear 조건이 `ITER_MAX_HBF` 상수 접힘에 의존하는데 코드에 드러나지 않음

- 위치: `decoder.py:373` `edge_clear = it == 1 or mx.is_restart(it)`
- 원문: `decoder.cpp:6543-6545`는 `iter == 0 || iter == 1 || iter == ITER_MAX_HBF + 1 || iter ∈ restart_iter`.
- AUTO 빌드에서 `ITER_MAX_HBF = 0`(`common.h:404`)이므로 지금은 등가다. 비AUTO 빌드는 4라서
  iteration 5에도 edge clear가 추가된다(`common.h:406`).
- `차이.md` §1 #2가 이 사실을 서술하고 있으나 코드에는 주석이 없다. BF 구간을 나중에 넣을 때
  이 조건을 함께 고쳐야 한다는 표시를 `decoder.py:373`에 남길 것을 제안한다.

### LOW-3. `차이.md` §2 #12(min1_pos 초기값 등가)의 근거가 불완전

- `차이.md`는 "클리어 직후 min1=min2=RESET이라 어느 쪽을 읽어도 결과 동일"이라고만 적었다.
- 실제로는 근거가 하나 더 필요하다. `Get_Default_Min_Pos`는 **-1이 아니라 0을 반환하고**
  (`decoder.cpp:5453-5457`), 0은 유효한 `position_c`다. 따라서 edge clear iteration에서
  각 row의 `position_c == 0`인 edge를 처리할 때 C++는 `CNU_Update_New_Mag`의 제거 분기
  (`decoder.cpp:3518-3526`)에 **실제로 진입한다**. Python은 이 분기를 통째로 건너뛴다
  (`decoder.py:413`).
- 등가가 성립하는 이유는 그 시점에 min1 = min2 = `V_VERY_STRONG`이라 `min1 = min2; min2 = V_VERY_STRONG`이
  수치적 무연산이기 때문이다. 결론은 같으나 문서의 논거는 보강이 필요하다.
- 같은 맥락에서 `차이.md` §2 #4의 "`V_VERY_STRONG=EDGE 7`" 표기는 부정확하다.
  `V_VERY_STRONG`은 상수값 **3**이고, C2V에서 EDGE_MAG_7로 **사상**된다(`decoder.cpp:2402`).
  "V_VERY_STRONG(=3)의 EDGE 도메인 상 = 7"로 적는 편이 안전하다.
  `decoder.py:353`의 주석 `RESET = ... # V_VERY_STRONG 대응`도 같은 혼동 여지가 있다.

### LOW-4. 모듈 docstring이 `_decode_matrix`의 도메인을 잘못 서술

- `decoder.py:8` "LLR 도메인: 수학적 등가인 signed 표현 (원본 C++는 flip/magnitude 도메인)"
- 현재 주 경로인 `_decode_matrix`(`decoder.py:319-446`)는 **flip/magnitude 도메인**이다.
  모듈 docstring이 legacy 두 경로만 서술하고 있어, 이 파일을 처음 읽는 사람이 주 경로를
  오해할 수 있다. (agent_1 P8, agent_2 P13 ㉮와 중복되나 C++ 대조 관점에서도 오독 위험이 있어 기재.)

### 참고 — 지적하지 않은 항목 (스코프 밖 또는 명시적 제외로 확인)

| 원문 기능 | 위치 | 판단 |
|---|---|---|
| 파이프라인 3클록 지연 (`pre_exist_sgn_reg2/3`, `VNU_out2/3`) | `decoder.cpp:680-689`, `2729`, `2751` | 명시적 비교 제외 (README "남은 근사/제한"), 확인만 |
| Power stopping (`Force_stopping`, `CH_LLR_MAX` 치환) | `decoder.cpp:4018-4024` | `차이.md` #5, 스코프 밖 |
| 쇼트닝/펑처링 채널 LLR 특례 | `decoder.cpp:3995-4016` | 부호에 쇼트닝/펑처링 없음 (`pcm.py:32`), 스코프 밖 |
| `Set_CSW(CSW_VALUE_JUMP)` 발산 감지 | `decoder.cpp:4972-4982` | `LAYOUT_PRIME_512B_TLC_VSS_OFF` 한정 + `diverse_th` 파라미터 의존. 스코프 밖이나 실물 반입 시 재확인 대상 |
| SD 모드의 `Is_Iter_Type_Edge_Clear(iter - 1)` (restart **다음** iteration에서 old_sgn 미사용) | `decoder.cpp:2328-2331` | HD는 `iter` 기준이고 Python이 HD 규칙을 따르므로 현재 정확. 2SD/3SD 확장 시 반드시 반영해야 함 |
| LLR_MATRIX 파일 포맷 | `local_opt.cpp:52-115` `Read_LLR_info_Auto` | **저장소에 원문 리더가 있다.** 필드 순서, 조건부 restart 줄, `max_value`/`min_value` 개수(= num_para_each_set), row 말미 4개(CSW_thr / iter_start / iter_end / floor_flag) 모두 `llr_matrix.py:108-133`과 일치. `max_value`/`min_value`/`floor_flag`는 C++ 디코더 산술에서 쓰이지 않는다(grep 결과 `local_opt.cpp` 내부 전용) → Python이 읽고 안 쓰는 것이 맞다. `max_iter = 마지막 iter_end`도 `local_opt.cpp:116-120` + `decoder.cpp:1118-1120`으로 확인 |
| row 선택 방향 | `decoder.cpp:6985-6999`, `7051-7068` | ITER 타입은 오름차순 첫 매칭 ↔ `llr_matrix.py:169-171` 동일. CSW 타입은 `for (i = num_candidate-1; i > 0; i--)` 내림차순 첫 매칭 = **조건을 만족하는 최대 index** ↔ `llr_matrix.py:175-176`의 오름차순 마지막 덮어쓰기와 **같은 답**. 그룹 첫 row(index 0)가 후보에서 빠지고 fallback인 것도 동일. `num_candidate == 1`이면 C++ 루프 미실행 → `start_idx` ↔ Python `b - a == 1` 단락 → `a`. 동일. (그룹 선택 방향 차이는 `_validate`의 연속성 강제로 무해 — 상세 검증은 P3/P5 담당) |

---

## 5. 검토 범위

읽고 대조한 원본 행: `decoder.cpp` 680-760, 905-955, 1040-1240, 1900-2100, 2230-2470, 2570-2830,
2960-3010, 3415-3620, 3973-4130, 4960-5010, 5445-5460, 5691-5730, 6530-6630, 6960-7130, 7285-7355,
8055-8115 / `common.h` 290-420 / `mode.h` 전체 / `local_opt.cpp` 50-130.
Python: `decoder.py` 전체, `pcm.py` 전체, `llr_matrix.py` 전체, `channel.py` 40-75,
입력 파일 `Input/LLR/LLR_MATRIX_HD_0.txt`, `HD_1.txt`.
2SD/3SD 경로, 채널 3종의 수치, `run.py`/`sim.py` 계약, LLR matrix 파서의 방어 로직은
다른 관점 담당이므로 필요한 최소 범위만 확인했다.
