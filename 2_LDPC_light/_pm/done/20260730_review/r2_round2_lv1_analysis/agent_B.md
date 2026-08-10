# Agent B — 기술적 타당성 검토 (라이트 리뷰 Round 2, lv1)

> 대상: `docs/2_LDPC_light/plan.md`
> 검토 일시: 2026-07-30 00:40:17
> 검토 방식: 코드/문서 직접 확인만 (추측 배제). 수정 없음, 읽기 전용.

## 확인 범위

`1_LDPC_revised/decoder.cpp` (C2V_Cal 2407-2540, V2C_Store 2760-2890, CNU_* 3538-3610, VN_Cal_Pre 3616-3670,
VN_Cal_HD 4045-4188, Mapper/Make_LLR 4834-4925, PMU_Read/Write 5806-5905, Clk_Manager 6243-6290,
Is_Iter_Type_* 6547-6640, 클럭 루프 1460-1870, Alloc_Dec 140-210), `LDPC/channel.cpp` 전체,
`LDPC/ecc_top.cpp` 260-340 / 1795-1822, `LDPC/common.h`, `LDPC/ecc_data.h`,
`LDPC/docs/20260413_ldpc_decoder_understanding/` L0L1·L2 전문, `docs/speed_opt/` 2-1·2-8·2-19·4-3·6-1_6-2,
`docs/guide/algorithms.md`.

## 심각도 요약

| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 4 |
| MEDIUM | 5 |
| LOW | 5 |

---

## HIGH

### H1. §2 표 — 파이프라인을 "timing 전용, 알고리즘 무관"으로 분류한 것은 사실과 다릅니다

plan.md §2 표: `col_M1~P4 파이프라인 / SRAM / PMU / overall_clk | 제거 | timing 전용, 알고리즘 무관`

실제로는 **CN 레지스터 반영이 2 컬럼 지연**되며, 이는 layered 스케줄의 유효 순서를 바꿉니다.

근거:
- `1_LDPC_revised/decoder.cpp:1547` — 한 clk 안에서 `C2V_cal(col_P2)` → `V2C_Cal(col_P2)`가 먼저 실행되고,
  `1_LDPC_revised/decoder.cpp:1683-1760`의 `V2C_Store(prev_variable_node2, ...)`가 **그 뒤에** 실행됩니다.
  `prev_variable_node2`는 col_P2를 2 clk 지연시킨 값입니다 (`decoder.cpp:743,749`).
- `Delay_2clk()`가 `VNU_out → VNU_out2 → VNU_out3`, `pre_exist_sgn_reg → 2 → 3`의 3단 시프트를 수행하고
  (`docs/speed_opt/2-8_delay_2clk_memcpy.md`), `V2C_Store`는 `VNU_out3`/`pre_exist_sgn_reg3`를 읽습니다
  (`decoder.cpp:2820, 2838`).
- 결과: clk t에서 `C2V_Cal(jj)`가 읽는 `cn->check_sum`/`min1_value`/`min2_value`/`min1_pos`
  (`decoder.cpp:2442-2458`)에는 **컬럼 jj-3까지의 store만 반영**되어 있습니다. 컬럼 jj-2, jj-1은 아직 in-flight입니다.
- L2 문서 `_ldpc_00_L2_단계별상세.md` §2.3 "Column 간 의존성 — 의존성이 있는 부분" 3번이 이 지연을
  **명시적으로 데이터 의존성으로** 기술합니다 ("column jj의 V2C 결과가 CN 레지스터에 반영되기까지 2 클럭의 지연").

영향: py를 지연 없는 교과서식 layered로 짜면 C2V가 보는 CN 상태가 달라져 **FER이 달라지고 §4의 C1(bit-exact 추적)은
반드시 실패**합니다. C1이 최우선 관문으로 잡혀 있으므로, 원인 미상의 불일치로 계획 전체가 막힐 수 있습니다.

조치 제안: §2 표에서 "파이프라인"을 "SRAM/PMU/overall_clk"과 분리하고, **컬럼 store 2단 지연은 유지 대상**으로
재분류하거나, 최소한 "C++ vanilla에서도 지연을 제거해 양쪽을 동일하게 맞춘다"를 명시해야 합니다
(후자를 택하면 `ldpc_vanilla/`의 FER이 현행 Ref-C와 달라진다는 점을 함께 기록해야 합니다).

### H2. §3.2 CN 상태 명세가 틀렸고, edge별 sign 메모리가 누락되어 있습니다

plan.md §3.2: `CN 상태: C++ 4-3의 CN_STATE와 동일 정보 (min1, min2, min1_idx, sign) × old/new 2세트`

세 가지 오류가 있습니다.

**(a) 필드 누락** — `CN_STATE`는 5필드입니다: `min1_pos, min1_value, min2_value, check_sum, syndrome`
(`docs/speed_opt/4-3_cn_state_struct.md` L21). `syndrome`과 `check_sum`은 **동시에 살아 있는 별개 필드**로,
`decoder.cpp:2442-2446`에서 함께 읽힙니다:
```cpp
synd      = cn->syndrome;
check_sum = cn->check_sum;
edge_sgn  = Check_SRAM_sgn[row_idx_r][position_c];
new_sgn = (synd + check_sum + (b_c2v_keep_old_sgn ? edge_sgn : 0)) & 1;
```
plan의 4개 항목("sign" 하나)으로는 이 둘을 표현할 수 없습니다.

**(b) "min × old/new 2세트"는 존재하지 않습니다** — min 레지스터는 **1세트**만 있고 in-place 갱신됩니다
(`decoder.cpp:2859-2876`). `old_min1_value`/`old_min2_value`(`decoder.cpp:2772-2773`)는 2862-2863에서 대입만 되고
**읽는 곳이 없는 데드 변수**입니다(grep 결과 사용처 0건). 실제 old/new 쌍은 `syndrome`(직전 iteration의 전체 패리티)
대 `check_sum`(현 iteration 누적 diff) 하나뿐입니다.

**(c) edge별 V2C sign 메모리 `Check_SRAM_sgn[M][K]`가 §3.2 배열 설계에서 통째로 빠져 있습니다** — 검토 항목 3의 지적이
맞습니다. 할당 `decoder.cpp:140`, C2V에서 읽기 `decoder.cpp:2444`, V2C_Store에서 쓰기 `decoder.cpp:2852/2855`.
이것 없이는 remove-old가 불가능합니다. 배치 벡터화에서는 `(B, M, K)`(= B × M_b·z_sb × dv) 크기로,
채널 LLR `(B, N_b, z_sb)`보다 **훨씬 큰 지배적 메모리 항**입니다(예: B=128, M_b=17, z_sb=256, K=17 → 약 152 M원소).
§3.2 배열 목록에 명시하지 않으면 설계 단계에서 메모리 산정이 어긋납니다.

### H3. §7 #1의 genie 판정과 §2의 "고정 iteration"이 서로 모순이고, FER 정의가 C++ vanilla와 달라집니다

- §2 표: `조기종료 (Partial/Full CRC) | 제거 — 고정 iteration | ... 판정은 bitwise 비교`
- §7 #1: `매 iteration hard decision을 정답과 비교, 일치 시 그 프레임 성공 확정 (genie 판정)`

두 서술이 같은 문서 안에서 충돌합니다. 그리고 **C++ vanilla에도 genie를 적용하는지**가 명시되어 있지 않습니다.

기술적으로 두 판정은 같지 않습니다:
- genie = "어느 iteration에서든 한 번 일치하면 성공" → 성공 확률이 단조 증가
- 고정 iteration = "마지막 iteration에서만 판정"
조기종료가 없는 이 디코더는 정답을 지나쳤다가 이탈할 수 있으므로(수렴점 이탈), **py FER ≤ C++ vanilla FER**의
계통 편차가 생깁니다. §4의 C2("통계 오차 내 일치")가 이 편차를 구현 버그로 오인하게 됩니다.

더 심각한 것은 **§4 C3("iteration별 평균 미충족 체크 수")입니다.** py가 genie로 조기 종료하면 성공한 프레임이
이후 iteration의 평균에서 빠지고, C++는 계속 돌아 평균에 남습니다. 두 곡선은 **모집단이 달라 비교 자체가 무의미**해집니다.
C3는 "FER보다 민감한 지표"로 계획에 잡혀 있으므로 이대로면 관문이 작동하지 않습니다.

참고: C++에는 이미 genie 모드가 있습니다 — `Check_Genie_PCRC()` (`decoder.cpp:2322-2352`). 단 이 함수는
(i) **정보부만** 비교하고(`for q < m_PCM->N - m_PCM->M`), (ii) iteration 경계가 아니라 **4개 termination column**에서만
평가합니다. py의 "매 iteration 전체 codeword 비교"와 조건이 다르므로, 양쪽을 맞추려면 어느 정의를 쓸지 확정해야 합니다.

### H4. §7 #3 / §5-3 — z_sb=256은 "파라미터만 맞추면 되는" 변경이 아닙니다

plan.md §7 #3: `decoder 동작은 검증 완료 상태이므로 파라미터(z_sb=256 대상 H-matrix, LLR 테이블 값)만 맞추면 됨`

`1_LDPC_revised`의 검증·최적화는 **z_sb=32 전제**로 수행되었고, z_sb=256에서는 지금까지 한 번도 실행된 적 없는 경로가
동시에 켜집니다.

- `factor = z_sb / PMU_UNIT_SIZE` (`decoder.cpp:5817`). z_sb=32 → **0**, z_sb=256 → **2**.
- `docs/speed_opt/2-19_pmu_noop_skip.md` L14, L31: "현 구성(z_sb=32): 복사·호출 스킵", "z_sb ≥ 128인 미래 구성:
  기존과 동일하게 실행". 즉 PMU_Read/PMU_Write 본체가 z_sb=256에서 처음 활성화됩니다.
- `docs/speed_opt/6-1_6-2_oob_fixes.md`: `MAIN_SRAM_read_rq`를 읽는 `Clk_Manager`/`Clk_Delay_REG`의 루프 상한이
  `factor × MAX_DV_GLOBAL_HALF = 0`이라 "idle cycle 삽입이 구조적으로 불가능"했다고 명시. z_sb=256이면 상한이 20이 되어
  `Clk_Manager`의 FIFO/`insert_idle`/`cnt_idle_cycle` 로직(`decoder.cpp:6258-6290`)이 처음 동작합니다.
- 6-1이 고친 하드코딩 상수도 "z_sb 256 시절의 fragment 수"라는 주석(`decoder.cpp:5814`)이 붙어 있어, 이 구성이
  현재 코드의 검증 범위 밖임을 스스로 밝히고 있습니다.

영향: idle cycle 삽입은 파이프라인 버블이므로 최소한 `overall_clk`가 바뀌고, H1의 컬럼 정렬에까지 영향을 줄 수
있는지 확인이 필요합니다. **C1/C2의 기준(golden)이 되는 C++ vanilla 자체가 미검증 구성에서 돌게 됩니다.**

참고(반대 방향 확인): PMU 자체는 알고리즘에 무관한 것이 맞습니다. `PMU_Read`는 `MAIN_SRAM_read_rq[n] = TRUE`
타이밍 플래그만 세우고 메시지/레지스터를 건드리지 않습니다(`decoder.cpp:5834-5879`). 즉 §2의 "PMU 제거 = 알고리즘 무관"은
타당하나, PMU가 먹이는 `Clk_Manager` idle 삽입은 별개로 확인해야 합니다.

---

## MEDIUM

### M1. §1 #6 — "codeword = 129 × 256"은 오해입니다. 129는 **정보부 block 수**입니다

`HCU_start = m_PCM->N_b - m_PCM->M_b - m_PCM->punct_col_num` (`decoder.cpp:205`).
프로젝트 CLAUDE.md 상수표의 `HCU_start = 127`, `punct_col_num = 2`를 대입하면 **N_b - M_b = 129**입니다.
따라서 129는 `N_b`가 아니라 정보부 column block 수이고, codeword는 `(129 + M_b) × z_sb`입니다.
(z_sb=32일 때 129×32 = 4128 bit ≈ 512B — 코드의 `LAYOUT_PRIME_512B_TLC_VSS_OFF`(`decoder.cpp:6636`)와 일치합니다.)

프로젝트 CLAUDE.md 상수표는 `N_b=129`와 `M_b=129`를 동시에 적고 있어 자체 모순이며(둘 다 129면 rate=0),
plan.md가 그 값을 그대로 인용해 "codeword = 129 × 256 = 33,024 bit ≈ 4KB"로 적었습니다.
실제로는 129 × z_sb가 정보 길이(≈4KB)에 해당합니다. 부호율이 통째로 달라지므로 FER 커브 자체가 다른 부호의 것이 됩니다.
`N_b`/`M_b`/`z_sb`는 H-matrix 파일 헤더에서 런타임으로 읽습니다(`ecc_top.cpp:264-269`) — §5-3에서 실물 파일을 확인할 때
반드시 이 세 값을 직접 읽어 §1 #6을 정정하시기 바랍니다.

### M2. §3.1b — "M_b≈13, rate≈0.9"는 실물의 최대 column degree와 양립하지 않습니다

`MAX_DV_GLOBAL = 17` (`LDPC/common.h:291`). degree 17인 column은 서로 다른 row block 17개에 연결되어야 하므로
**M_b ≥ 17**이 필요합니다. M_b=13이면 최대 degree가 13으로 제한되어, §3.1b의 "실물과 동일 스케일"이라는 목적이
달성되지 않습니다. M_b ≥ 17 (rate ≤ 129/146 ≈ 0.88)로 잡거나, 예시 부호의 최대 dv를 낮추고 그 사실을 명시해야 합니다.

### M3. 스펙으로 지정한 L2 문서에 실제 코드와 다른 부분이 있습니다

plan.md §3.2는 `_ldpc_00_L2_단계별상세.md`를 "스펙으로 삼는다"고 선언했는데, 그 문서의 min 갱신 의사코드에 오류가 있습니다.

L2 문서 L353-356:
```
if v2c_mag <= min1_value: ...
elif v2c_mag < min2_value:      ← "<"
    min2_value = v2c_mag
```
실제 코드 `CNU_Update_New_Mag` (`decoder.cpp:3589, 3599`):
```cpp
if (v2c_mag <= *min1_value) { ... }
else if (v2c_mag <= *min2_value) { ... }   // "<=" 입니다
```
동률(`v2c_mag == min2_value`)에서 갱신 여부가 갈리므로 bit-exact가 깨집니다.
L2 문서만 보고 구현하면 C1에서 재현 불가한 미세 불일치가 남습니다.
**스펙의 최종 권위는 L2 문서가 아니라 `decoder.cpp`임을 §3.2에 명시**하시기 바랍니다.

(같은 절의 나머지 — `new_sgn = (Syndrome + check_sum + edge_sgn) % 2`, min1_pos==cur_pos 시 min1←min2 / min2 리셋 —
은 코드와 일치함을 확인했습니다.)

### M4. §2 유지/제거 표에 분류되지 않은 알고리즘 요소가 남아 있습니다

HCU·쇼트닝/펑처링·조기종료를 제거해도 다음은 살아 있고, 전부 FER에 영향을 줍니다. 유지/제거 결정이 필요합니다.

| 요소 | 위치 | 비고 |
|------|------|------|
| Edge clear(restart) iteration | `Is_Iter_Type_Edge_Clear` `decoder.cpp:6547-6572`, 적용부 `2380-2398`, `3560-3568` | 지정 iteration에서 `edge_sgn=0`/`pre_v2c_sgn=0`으로 강제. **restart_iter는 plan이 로드하기로 한 2-9 LLR 테이블 파일에서 옵니다** (`m_param_LLR->restart_iter[]`) — 파일만 읽고 로직을 빼면 테이블 의미가 달라집니다 |
| Parity skip | `decoder.cpp:1515-1530`, L2 §4.8 | mn==0 / ITER_MAX_HBF+1에서 parity 컬럼의 C2V/V2C를 건너뛰고 checksum만 store |
| BF(HBF) 1-bit precision + `Select_BF` | `decoder.cpp:2434-2453`, `2803-2806`, `4062-4064` | HD 모드 전용. §2가 채널로 HD를 유지한다고 했으므로 HD를 구현하면 딸려옵니다 |
| Power stopping | `decoder.cpp:4073` (`Force_stopping >= POWER_STOPPING_DELAY` → `channel_llr = CH_LLR_MAX`) | 강제 수렴 유도. 조기종료와 별개 기능 |

### M5. §3.1 all-zero 근거가 실제 근거와 달라, 구현 도메인 선택을 그르칠 수 있습니다

**결론부터: all-zero 사용은 타당합니다(오히려 계획보다 강한 근거가 있습니다).** 다만 근거 서술이 틀려 위험합니다.

plan.md §3.1은 "대칭 채널 + 대칭 복호기"를 근거로 듭니다. 확인 결과:
- 양자화는 실제로 대칭입니다. `ecc_top.cpp:1802-1815`에서 `Lq_ini_m = fabs(Lq_ini)`로 **크기에만** 임계값을 적용하고
  부호는 `cwr[n] >= 0 → HD=0`으로 분리합니다. 임계값은 `channel.cpp:33-38`의 `2*r_offset/var` 계열로 0 기준 대칭
  구간을 만듭니다. `Mapper_2bit_SD`/`Mapper_3bit_SD`(`decoder.cpp:4834-4880`)도 (sd,cc)로 크기를, hd로 부호를 줍니다.
  → 음/양 레벨 수가 같고 0 기준 비대칭이 없습니다. (`cwr==0` 동률만 HD=0으로 치우치나 측도 0입니다.)
- **그런데 더 근본적인 이유가 있습니다.** 이 디코더는 signed LLR 도메인이 아니라 **수신 경판정 기준의 flip/syndrome
  도메인**에서 동작합니다. `VN_Cal_HD`(`decoder.cpp:4087, 4105`):
  ```cpp
  sum_t = channel_llr;              // ch1 등 항상 양수
  ... sum_t += VNU_in[...];
  if (sum_t > 0) cwc[bit_pos] = Variable_mem[bit_pos];
  else           cwc[bit_pos] = Variable_mem[bit_pos] ^ 1;
  ```
  채널 LLR은 **부호 없는 양수**이고, syndrome은 `H·HD = H·(c⊕e) = H·e`라 송신 부호어 c와 무관합니다.
  즉 복호 동작이 (오류패턴 e, SD, CC)에만 의존하므로 all-zero는 **통계적 등가가 아니라 정확히 등가**입니다.

위험: 이 사실이 문서에 없으면 py를 교과서식 signed-LLR min-sum(`Λ = ±ch`)으로 구현하기 쉽고, 그러면 FER은 비슷해도
**C1 bit-exact는 원리적으로 불가능**합니다. §3.1 또는 §3.2에 "flip/syndrome-aided 도메인 유지"를 명시하십시오.

---

## LOW

### L1. 1.5SD 양자화기는 0 기준 비대칭이므로 all-zero 전제가 성립하지 않습니다 (현재 범위 밖)

`channel.cpp:60-68` `Get_Mag_1_5SD`는 `Lq_ini >= LLR_th(=2·0.15/var)`일 때만 `hd=0`이고, erasure 구간
(-0.15 ~ +0.15)에서는 **부호와 무관하게 hd=1**입니다. all-zero에서는 이 구간이 전부 오류가 되고 all-one에서는 전부
정답이 되어, 오류패턴 통계가 부호어에 의존합니다. plan §2는 채널을 "HD/2SD/3SD"로 한정하고 있어 현재는 문제가 없으나,
"1.5SD는 all-zero 전제에서 제외"를 명시해 두시길 권합니다.

### L2. §3.2 "circulant shift ... (또는 np.roll)" — 순열은 **2종(서로 역)**입니다

`decoder.cpp:150-151`:
```cpp
shift_tbl_C2V[i] = ...; shift_mem(shift_tbl_C2V[i], z_sb, i, 0);   // dir=0
shift_tbl_V2C[i] = ...; shift_mem(shift_tbl_V2C[i], z_sb, i, 1);   // dir=1
```
C2V는 `row_idx_r = idx_offset + z_mem_shift[j]`로 **CN 인덱스를** 치환하고(`decoder.cpp:2439`),
V2C_Store는 `VNU_out3[mux_idx][z_mem_shift[j]]`로 **메시지 인덱스를** 치환합니다(`decoder.cpp:2820`, `bit_pos`는 j 그대로).
방향이 반대이므로 `np.roll` 한 방향으로 처리하면 틀립니다. `docs/speed_opt/2-1_shift_mem.md`가 이 2종 테이블을 다룹니다.

### L3. §4 C1의 "채널 LLR을 파일로 덤프"는 표현이 부정확합니다

HD 모드에는 비트별 채널 LLR이 없습니다. `channel_llr`은 (iteration, dv)로 LLR 테이블에서 조회한 `ch1`이고
(`decoder.cpp:4069, 4073, 4085`), 비트별 채널 입력은 `HD/SD/CC`입니다(SD 모드는 `|Soft_LLR_PRIME|` 등급으로
ch1~ch4 중 택일, L2 §1.3.3). 덤프 대상은 **HD/SD/CC 배열**(또는 `Soft_LLR_PRIME`)로 적어야 구현자가 헤매지 않습니다.

### L4. §3.1b FER vs RBER 축 — C++와 py의 RBER↔σ 변환이 달라질 수 있습니다

`channel.cpp:110-136` `qfunc_inv`는 유리함수 근사이고 `Q_fn`(93-106)은 5항 근사식입니다.
py에서 `scipy.stats.norm.isf` 등 정확한 함수를 쓰면 같은 RBER에 대해 σ가 미세하게 달라져 §4 C2의 두 곡선이
x축 방향으로 어긋납니다. C2 비교를 하려면 **`dev_from_RBER`/`qfunc_inv`를 그대로 포팅**해야 합니다.

### L5. §3.3 "10~30배"의 근거가 없습니다 (구조 자체는 §2·§4와 모순 없음)

구조 타당성은 확인했습니다: 한 컬럼 안에서 z_sb개 원소는 **서로 다른 CN**(`row_idx*z_sb + shift[j]`)에,
dv개 edge는 **서로 다른 row block**(`V_net_b[jj][ii]`)에 대응하므로 `(B, dv, z_sb)`는 완전 데이터 병렬이고,
순차 의존은 컬럼 축뿐입니다 — "col 루프는 Python 유지"와 정합합니다.

다만 배치는 **numpy 호출 횟수를 줄이지 않고 호출당 비용만 분산**시키므로, 배열이 compute-bound가 되는 지점
(z_sb=256이면 B ≈ 16~32)을 넘으면 이득이 급감합니다. B=128에서 30배는 낙관적입니다.
수치를 지우거나 "B=32 기준 추정, 측정 후 갱신"으로 완화하시길 권합니다.

---

## 문제 없음으로 확인한 항목

- **all-zero codeword 사용 자체** — 타당합니다(M5 참조). 양자화 레벨은 0 기준 대칭이며, 디코더가 flip/syndrome
  도메인이라 송신 부호어와 무관합니다. 단 쇼트닝/펑처링 경로는 절대 도메인 가정(`VN_Cal_Pre` `decoder.cpp:3629-3634`의
  shortened → `+EDGE_MAG_7`, `BIT_REGION_SH` → `CH_LLR_MAX` `decoder.cpp:4079`)을 갖고 있으므로,
  plan대로 제거하는 것이 all-zero 전제와도 정합합니다.
- **"column-layered이지 flooding이 아니다"** — 맞습니다. `check_sum`/min 레지스터가 컬럼 순회 중 in-place 갱신되고
  (`decoder.cpp:2847, 2873-2875`) 이후 컬럼의 C2V가 같은 iteration 안에서 읽습니다(`decoder.cpp:2442-2458`).
  `syndrome`은 직전 iteration 값의 스냅샷이지만 `check_sum`과 함께 XOR되어 현재 패리티를 만들므로 flooding이 아닙니다.
  (단 H1의 2컬럼 지연 때문에 "col 순서 유지"만으로는 서술이 부족합니다.)
- **PMU 제거 = 알고리즘 무관** — 맞습니다(H4 참조 단서 포함).
- **정정능력 커브를 all-zero로 뽑는 것** — 기술적 문제 없습니다. genie 판정 부분만 H3 해결 필요.
