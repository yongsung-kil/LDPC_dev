# C++ 원본의 2SD/3SD 디코딩 경로 분석

- 작성: 2026-08-09 14:15:41
- 대상: `0_LDPC_original/` (decoder.cpp, channel.cpp, common.h, ecc_data.h, ecc_top.cpp)
- 목적: `2_LDPC_light/LDPC_base/decoder.py`에 2SD/3SD 산술을 이식하기 위한 사실 확정
- 빌드 전제: 3-bit LLR (`__4_BIT_LLR__` 미정의), DAO 연동 빌드 (`__AUTO_LLR_OPT__` 정의).
  4-bit 경로는 사용자 확정(2026-08-06)에 따라 이식 범위 밖이므로 차이가 있는 곳만 각주로 남긴다
- 근거 표기: `파일:라인` 형식. 라인 번호는 원본 파일 기준

---

## 0. 한 줄 요약

2SD와 3SD는 HD와 같은 flip 도메인 산술을 쓰며 VN 판정식도 같다. 이식에서 실제로 바뀌는 것은
세 가지다.

- ㉮ 채널 항 `ch`가 dv별 스칼라에서 **비트별 region 선택값**으로 바뀐다
- ㉯ iteration 0(그리고 SD의 모든 restart iteration)이 **채널 magnitude를 CN에 심는 Pre 단계**가 된다
- ㉰ Edge Clear 대상 iteration 집합이 HD와 다르다 (SD는 iteration 1에서 클리어하지 않는다)

---

## 1. region 정의와 ch 인덱스 매핑

### 1.1 채널이 만드는 region 플래그

`Get_Mag_2SD` (channel.cpp:42-46), `Get_Mag_3SD` (channel.cpp:50-56)가 LLR 크기
`Lq_ini_m = |2·cwr/var|`를 임계값과 비교해 `sd`, `cc`를 만든다. 임계값은
`Set_R_Offset` (channel.cpp:11-29)의 r_offset에서 온다 (2SD는 0.35 하나, 3SD는 0.15, 0.35, 0.55).

### 1.2 플래그에서 magnitude로 (Make_LLR)

`Decoder::Make_LLR` (decoder.cpp:4884-4935)가 `Soft_LLR`과 `Soft_LLR_PRIME`을 만든다.

- ㉮ 2SD: `Mapper_2bit_SD(inv_hd, sd, EDGE_MAG_5, EDGE_MAG_1)` (decoder.cpp:4905-4906).
  `Mapper_2bit_SD` (decoder.cpp:4870-4880)는 `sd==1`이면 첫 인자, `sd==0`이면 둘째 인자를 쓰고,
  `hd==1`이면 부호를 뒤집는다
- ㉯ 3SD: `Mapper_3bit_SD(inv_hd, sd, cc, EDGE_MAG_7, EDGE_MAG_5, EDGE_MAG_3, EDGE_MAG_1)`
  (decoder.cpp:4924). `Mapper_3bit_SD` (decoder.cpp:4839-4853)의 분기는
  `(sd=1,cc=1)`, `(sd=1,cc=0)`, `(sd=0,cc=0)`, `(sd=0,cc=1)` 순서로 인자 1, 2, 3, 4를 쓴다

### 1.3 magnitude에서 ch 인덱스로 (VN_Cal_SD)

`VN_Cal_SD` (decoder.cpp:4537-4557)가 `mag = abs(Soft_LLR_PRIME[bit_pos])`를 보고 ch를 고른다.

```
2SD  (decoder.cpp:4542-4543)   mag > EDGE_MAG_3 → ch1,  그 외 → ch2
3SD  (decoder.cpp:4552-4555)   mag == EDGE_MAG_7 → ch1
                               mag == EDGE_MAG_5 → ch2
                               mag == EDGE_MAG_3 → ch3
                               그 외             → ch4
```

### 1.4 ch1~ch4가 파일의 몇 번째 열인가

`Get_VNU_LLR_SET_FILE` (decoder.cpp:7074-7133)이 LLR matrix 파일에서 읽는 순서다.
dv 구간 하나가 차지하는 열 묶음(`table_col_idx` 기준 오프셋)은 다음과 같다.

| 모드 | 오프셋 0 | 1 | 2 | 3 | 4 | 5 | 6 | 근거 |
|------|---------|---|---|---|---|---|---|------|
| HD | ch1 | th1 | th2 | th3 | | | | decoder.cpp:7089-7095 |
| 2SD | ch1 | ch2 | th1 | th2 | th3 | | | decoder.cpp:7104-7110 |
| 3SD | ch1 | ch2 | ch3 | ch4 | th1 | th2 | th3 | decoder.cpp:7119-7125 |

즉 파일의 ch 열 인덱스 0, 1, 2, 3이 그대로 ch1, ch2, ch3, ch4다.

### 1.5 확정된 매핑표

**2SD** (`|Soft_LLR|`는 sd=1이면 5, sd=0이면 1)

| ch 열 인덱스 | 이름 | sd | `\|Soft_LLR\|` |
|---|---|---|---|
| 0 | strong | 1 | EDGE_MAG_5 = 5 |
| 1 | weak | 0 | EDGE_MAG_1 = 1 |

**3SD**

| ch 열 인덱스 | 이름 | sd | cc | `\|Soft_LLR\|` |
|---|---|---|---|---|
| 0 | very strong | 1 | 1 | EDGE_MAG_7 = 7 |
| 1 | normal strong | 1 | 0 | EDGE_MAG_5 = 5 |
| 2 | normal weak | 0 | 0 | EDGE_MAG_3 = 3 |
| 3 | very weak | 0 | 1 | EDGE_MAG_1 = 1 |

즉 인덱스가 커질수록 신뢰도가 낮아지는 순서다. Python에서 쓸 수 있는 닫힌 식은 다음과 같다.

- ㉮ 2SD: `region = 1 - sd`
- ㉯ 3SD: `region = 2*(1 - sd) + (cc XOR sd)`

이름은 `Mapper_3bit_SD`의 원문 주석(decoder.cpp:4843-4849)에 적힌
very strong, normal strong, normal weak, very weak를 그대로 쓴다. 이 이름은
`channel.py` docstring(2_LDPC_light/LDPC_base/channel.py:11)의 표기와도 이미 일치한다.

---

## 2. VN 판정의 차이

전용 함수가 따로 있다. `VN_Cal_HD` (decoder.cpp:3973), `VN_Cal_SD` (decoder.cpp:4493),
`VN_Cal_CD` (decoder.cpp:4354, 1.5SD 전용), 그리고 HCU 짝인 `VN_Cal_HD_HCU` (4136),
`VN_Cal_SD_HCU` (4649)다. 분기는 `V2C_Cal` (decoder.cpp:5691-5725)에서 `init_n`으로 갈린다.

| 항목 | VN_Cal_HD | VN_Cal_SD | 판정 |
|------|-----------|-----------|------|
| 채널 항 부호 | `sum_t = channel_llr` (3973 기준 4026), 부호 없이 그대로 더한다 | 동일 (4566) | **같다** |
| 채널 항 값 | 항상 `ch1` (4019) | region으로 `ch1~ch4` 중 선택 (4540-4557) | **다르다** |
| C2V 합산 | `sum_t += VNU_in[mux][j]` (4039-4042) | 동일 (4572-4575) | **같다** |
| 반전 조건 | `sum_t > 0`이면 유지, 아니면 반전 (4044-4045) | 동일 (4577-4578) | **같다 (동점 반전 포함)** |
| VNU 출력 원값 | `temp = sum_t - VNU_in[mux][j]` (4052) | 동일 (4592) | **같다** |
| BF(1-bit precision) 분기 | 있다 (4056-4079) | **없다** | AUTO 빌드에서 `flag_BF_on`이 항상 LOW라 실효 차이 없음 |
| 양자화 캐스케이드 | th1~th3 → EDGE 7/5/3/1 (4112-4115) | 동일 (4626-4629) | **같다** |
| 원값 0일 때 부호 | `VNU_in` 부호를 쓴다 (4098-4099) | 동일 (4612-4613) | **같다** |
| 전력 절감 경로 | `stopping_criteria == CYCLE`이고 지연 경과면 `ch = CH_LLR_MAX` (4021-4024) | 동일 (4559-4562) | **같다** |

결론: **반전 조건 `sum_t <= 0`은 HD와 SD가 동일하다.** 채널 항도 부호 없이 더하는 flip 도메인이
그대로다. 산술에서 달라지는 것은 채널 항의 값을 고르는 방식 하나다.

각주: 4-bit 빌드에서만 `VN_Cal_SD`의 3SD 최상위 비교가 `mag >= EDGE_MAG_7` (4547)이고
`VN_Cal_SD_HCU`는 `mag == EDGE_MAG_7` (4720)이라 서로 다르다. 3-bit 빌드에서는 양쪽 모두
`==`라 차이가 없다.

---

## 3. Edge Clear와 restart의 SD 규칙

Python의 `decoder_main`이 "SD Edge Clear 규칙 구현 후 해제"라고 막아둔 근거가 여기다.
HD와 SD는 **클리어하는 iteration 집합**과 **클리어 대상**과 **그 iteration에 도는 VN 함수**가
모두 다르다.

### 3.1 클리어 대상 iteration 집합

`Is_Iter_Type_Edge_Clear` (decoder.cpp:6538-6598), AUTO 빌드 분기(6541-6565) 기준이다.

| 모드 | Edge Clear iteration |
|------|----------------------|
| HD, 1.5SD | `0`, `1`, `ITER_MAX_HBF + 1` (AUTO 빌드에서 `ITER_MAX_HBF = 0`이므로 실질 `0`, `1`), 그리고 restart_iter 전체 |
| 2SD, 3SD | `0`, 그리고 restart_iter 전체. **iteration 1은 포함되지 않는다** |

HD가 iteration 1을 클리어하는 이유는 원문 주석(decoder.cpp:6570)에 적혀 있다. iteration 0의
V2C_Store가 Ref-C에서는 동작하고 RTL에서는 동작하지 않아 그 차이를 없애려고 넣은 것이다.
SD에는 그 처리가 없으므로 **iteration 0에서 CN에 쌓인 채널 정보가 iteration 1로 그대로 넘어간다.**

### 3.2 클리어 대상 항목

`Clear_Edge_Restart` (decoder.cpp:709-739)

| 클리어 항목 | HD, 1.5SD | 2SD, 3SD |
|-------------|-----------|----------|
| `Clear_REG_min_pos` | 한다 | 한다 |
| `Clear_REG_min_value` | 한다 | 한다 |
| `Clear_CN_REG(IDX_CHECK_SUM)` | 한다 | 한다 |
| `Clear_Edge_SRAM_Sgn` | 한다 | 한다 |
| `Clear_Syndrome` | **하지 않는다** (원문 주석 717: HD는 syndrome을 계속 들고 간다) | **한다** (731) |
| `Clear_PMU`, `Clear_Sum_t_OLD` | 한다 | 한다 |

SD가 syndrome을 지워도 값은 되살아난다. 아래 3.3의 Pre 단계가 같은 iteration 안에서 syndrome을
다시 계산해 넣기 때문이다. `Variable_mem`(read bit)은 디코딩 중 바뀌지 않으므로
(decoder.cpp:1056-1089에서 한 번 설정, 이후 변경은 puncture recovery 경로뿐) 재계산 값은 항상
`H·read_bit`으로 같다.

### 3.3 restart iteration에 도는 함수

`Is_Iter_Type_Init` (decoder.cpp:6606-6676), AUTO 빌드 분기(6609-6625) 기준이다.

| 모드 | `Is_Iter_Type_Init`가 TRUE인 iteration |
|------|----------------------------------------|
| HD, 1.5SD | `0`만 |
| 2SD, 3SD | `0`과 restart_iter 전체 |

`V2C_Cal` (decoder.cpp:5715-5722)은 `Is_Iter_Type_Init`가 TRUE면 `VN_Cal_Pre`를, 아니면
`VN_Cal_SD`를 부른다. 따라서 **SD의 restart iteration은 일반 VN 계산을 하지 않고 Pre 단계를
다시 돈다.** 결과는 다음과 같다.

- ㉮ 그 iteration의 테이블 row에 담긴 ch, th 값은 읽히지 않는다.
  `cur_set_idx`는 계산되지만(decoder.cpp:1136-1142) 쓰이지 않는다.
  HD의 restart row가 -1 값을 산술에 그대로 쓰는 것(`docs/차이.md` 2절 5번)과 정반대다
- ㉯ 판정 비트는 `cwc = Variable_mem` (decoder.cpp:3733-3736), 즉 그 iteration에는 반전이
  일어나지 않고 에러 수가 원 채널 에러 수로 되돌아간다
- ㉰ CN의 min1, min2에 채널 magnitude가 다시 심긴다 (아래 3.4)

### 3.4 Pre 단계(iteration 0과 SD restart)가 CN에 남기는 것

`VN_Cal_Pre` (decoder.cpp:3554-3754)의 SD 분기(3624-3695)와 `V2C_Store`
(decoder.cpp:2690-3010)를 이어 보면 다음과 같다.

- ㉮ VNU 출력: 정보부, 패리티 비무천공부는 `VNU_out = Soft_LLR[bit_pos]` (3663, 3666).
  부호는 read bit, 크기는 region magnitude다. 이후 `±EDGE_MAG_7`로 클리핑한다 (3687-3688).
  HD는 같은 자리에서 `(Variable_mem·(-2)+1)·EDGE_MAG_3`, 즉 **크기가 상수** 3이다 (3598, 3606)
- ㉯ CN sign 누적: `v2c_sgn`(VNU 출력의 부호 = read bit)이 `check_sum`에 XOR 누적된다
  (`CNU_Update_New_Sgn`, decoder.cpp:3545-3548, 호출은 2776)
- ㉰ CN min 갱신: `v2c_mag`가 EDGE 값에서 V 코드로 변환되어(2766-2769: 7→3, 5→2, 3→1, 그 외→0)
  `CNU_Update_New_Mag` (3514-3544)로 min1, min2, min1_pos에 반영된다.
  `store_min_REG`는 항상 TRUE다 (2627에서 `V2C_Store(jj, ii, mn, TRUE, TRUE, TRUE)` 호출)
- ㉱ edge sign SRAM: Pre iteration에는 실제 부호 대신 **0을 쓴다** (2783-2785)
- ㉲ iteration 끝에서 syndrome 확정: 마지막 column의 마지막 edge에서
  `Syndrome[j] = Check_REG[j][IDX_CHECK_SUM]`를 복사하고 **check_sum을 0으로 리셋**한다
  (2993-3008)
- ㉳ CSW: 같은 함수 뒤쪽에서 `Compute_CSW()` (3464-3465)가 돈다. 이 시점에는 check_sum이 이미
  0이므로 `prev_CSW = |syndrome|`이 된다

즉 **Pre iteration을 지나면 CN에는 채널 magnitude로 만든 min1, min2, min1_pos만 남고
check_sum과 edge sign은 0이다.**

### 3.5 Pre 다음 iteration의 edge sign 처리

`C2V_Cal_New_Sgn` (decoder.cpp:2299-2335)

- ㉮ HD, 1.5SD: `Is_Iter_Type_Edge_Clear(iter)`이면 `edge_sgn = 0` (2321-2324).
  즉 **클리어하는 그 iteration**에서 안 읽는다
- ㉯ 2SD, 3SD: `Is_Iter_Type_Edge_Clear(iter - 1)`이면 `edge_sgn = 0` (2328-2331).
  즉 **클리어 다음 iteration**에서 안 읽는다 (원문 주석 그대로)

`CNU_Remove_Old_Sgn` (decoder.cpp:3476-3509)의 SD 분기(3503-3507)는 반대로
`Is_Iter_Type_Edge_Clear(iter)`을 본다. 이 둘이 어긋나 보이지만 결과는 일관된다.
Pre iteration이 edge sign SRAM에 0을 써 두었으므로(3.4 ㉱) 다음 iteration의 remove-old가
읽는 값도 0이고, check_sum도 0에서 시작하기 때문이다.

### 3.6 실제 restart iteration 번호

AUTO 빌드는 LLR matrix 파일의 `restart_iter[]`를 쓴다. 비 AUTO 빌드의 하드코딩 값은 참고용이다.

- ㉮ 2SD: `RSP1_2SD_PRIME_1 = 241`, `RSP1_2SD_PRIME_2 = 581` (common.h:679-680)
- ㉯ 3SD: `RSP1_3SD_PRIME_1~6 = 171, 312, 653, 844, 1035, 1301` (common.h:681-686)

---

## 4. read bit와 syndrome

- ㉮ read bit는 SD에서도 고정이다. `Variable_mem`은 `LDPC_Decoder` 진입 시 HD 입력에서 한 번
  채워지고(decoder.cpp:1056-1068) 쇼트닝, 펑처링 위치만 0으로 고정한다(1071-1089).
  SD 전용 갱신은 없다
- ㉯ syndrome 값은 HD와 같다. Pre 단계에서 누적되는 V2C sign이 HD는
  `(Variable_mem·(-2)+1)·EDGE_MAG_3`의 부호, SD는 `Soft_LLR`의 부호인데, `Soft_LLR`의 부호는
  `Mapper_*_SD`의 마지막 줄(decoder.cpp:4850-4851, 4877-4878)에서 `inv_hd`로 정해지고
  `inv_hd`는 all-zero codeword 모드에서 `hd_input`과 같다(4896, 4916). 따라서 양쪽 모두
  `H·read_bit`이 된다
- ㉰ 판정 비트(`cwc`)와 read bit의 관계도 같다. Pre iteration은 `cwc = Variable_mem` (3733-3736),
  일반 iteration은 `sum_t > 0`이면 유지, 아니면 반전(4577-4578)이다
- ㉱ syndrome 계산 시점과 CSW 초기값도 같다 (3.4 ㉲, ㉳)

결론: **SD의 syndrome과 read bit 처리는 HD와 동일하다.** 다만 SD는 restart마다 syndrome을
지웠다가 같은 값으로 다시 채운다는 점만 다르고, 관측 가능한 값은 변하지 않는다.

---

## 5. VNU 출력 양자화와 EDGE 레벨 소비

`VN_Cal_SD`의 양자화부(decoder.cpp:4590-4640)는 `VN_Cal_HD`의 4-bit precision 분기
(4080-4120)와 문장 단위로 동일하다.

- ㉮ 3-bit 빌드 캐스케이드: `>= th1 → EDGE_MAG_7`, `>= th2 → EDGE_MAG_5`, `>= th3 → EDGE_MAG_3`,
  그 외 `EDGE_MAG_1` (SD 4626-4629, HD 4112-4115)
- ㉯ 원값이 0일 때만 별도 분기를 타고 부호를 `VNU_in`에서 가져온다 (SD 4596-4614, HD 4082-4100).
  분기 안의 캐스케이드 자체는 동일하다
- ㉰ SD에는 `flag_BF_on` 1-bit precision 분기가 아예 없다. HD에는 있으나 AUTO 빌드에서
  `flag_BF_on`이 항상 LOW라 실효 차이가 없다
- ㉱ V2C_Store의 EDGE→V 코드 변환(2744-2749, 2765-2770)과 C2V_Cal의 V→EDGE 역변환
  (2401-2406)은 모드와 무관한 공통 경로다

결론: **양자화와 EDGE 레벨 소비는 HD와 같은 코드 경로다.** Python의 `_vnu_quantize`는
그대로 두면 된다.

---

## 6. CSW와 테이블 row 선택

- ㉮ `Compute_CSW` (decoder.cpp:7293-7304)는 `Σ(check_sum ⊕ Syndrome)`이며 모드 분기가 없다
- ㉯ `Get_Cur_LLR_Idx_FILE` (decoder.cpp:6973-7073)의 모드 의존 코드는 두 곳뿐이다.
  - ㉠ `init_n == MODE_DEC_HD && iter > 0`일 때만 `Adjust_HD_Floor_Type`을 부른다 (6980-6983).
    SD는 부르지 않는다
  - ㉡ 비 AUTO 빌드의 HD 하드코딩 그룹 선택(7001-7020). AUTO 빌드에는 없다
- ㉰ 그룹 선택 루프(7022-7037), ITER 타입 row 선택(7051-7058), CSW 타입 row 선택(7059-7068)은
  전부 모드 무관이다
- ㉱ dv 구간 선택(`Get_VNU_LLR_SET_FILE` 7078-7083)도 모드 무관이다. 모드에 따라 달라지는 것은
  구간 안에서 ch와 th를 읽는 오프셋뿐이다 (1.4의 표)

결론: **CSW 계산과 row 선택은 SD에서 달라지지 않는다.** Python의
`llr_matrix.row_index`, `Compute_CSW` 대응부는 그대로 쓴다.

주의할 점 하나. SD의 restart iteration은 Pre 단계를 돌기 때문에 그 iteration이 끝날 때
`prev_CSW`가 `|syndrome|`으로 되돌아간다 (3.4 ㉳). 다음 iteration의 CSW 타입 row 선택은 이
되돌아간 값을 본다.

---

## 7. 관련 상수

### 7.1 살아 있는 값

| 이름 | 값 | 위치 |
|------|----|------|
| `MODE_DEC_HD` / `MODE_DEC_2SD` / `MODE_DEC_3SD` / `MODE_DEC_1_5SD` | 1 / 2 / 3 / 4 | common.h:75-78 |
| r_offset (2SD) | 0.35 | channel.cpp:17 |
| r_offset (3SD) | 0.15, 0.35, 0.55 | channel.cpp:20-22 |
| `EDGE_MAG_7` / `_5` / `_3` / `_1` | 7 / 5 / 3 / 1 | common.h:343-346 |
| `V_VERY_STRONG` / `V_NORMAL_STRONG` / `V_NORMAL_WEAK` / `V_VERY_WEAK` | 3 / 2 / 1 / 0 | common.h:338-341 |
| `CH_LLR_MAX` / `CH_LLR_MIN` | 31 / 0 | common.h:375-376 |
| `PRIME_2SD_LLR_TABLE_NUM_ROW` | 36 (4-bit 빌드 48) | common.h:477, 437 |
| `PRIME_3SD_LLR_TABLE_NUM_ROW` | 66 (4-bit 빌드 116) | common.h:478, 438 |
| `PRIME_LLR_TABLE_NUM_DEGREE` / `PRIME_LLR_TABLE_NUM_TH` | 4 / 3 (4-bit 빌드 4 / 7) | common.h:483, 486 |
| `ITER_MAX_2SD_PRIME` / `ITER_MAX_3SD_PRIME` | 920 / 1400 | common.h:458, 474 |
| `ITER_MAX_REF_C_2SD_NUM` / `_3SD_NUM` | 9 / 15 | common.h:399-400 |
| `RSP1_2SD_PRIME_1` / `_2` | 241 / 581 | common.h:679-680 |
| `RSP1_3SD_PRIME_1`~`_6` | 171, 312, 653, 844, 1035, 1301 | common.h:681-686 |
| `SD_POWER_STOPPING_TH` | 999999 | common.h:188 |
| `MODE_CH_3SD_FIXED` | 5 | common.h:84 |

`CH_2SD_*`, `CH_3SD_*`라는 이름의 매크로는 존재하지 않는다. region 개수를 담은 상수도 없다.
region 개수는 `Get_VNU_Ch_LLR_Adaptive` (decoder.cpp:6956-6965)와
`Get_VNU_LLR_SET_FILE` (7104-7122)의 인덱스 산술에 숫자 2와 4로 박혀 있다.
Python의 `MODE_CH_LEN`(`llr_matrix.py:44`)과 `2^(init_n-1)` 공식은 Python 쪽에서 만든
표기이며 C++에는 대응 매크로가 없다.

### 7.2 소실된 값 (소스 손상)

비 AUTO 빌드가 쓰는 하드코딩 기본 테이블이 비었다. AUTO(DAO) 빌드는 파일에서 읽으므로
이식에는 영향이 없으나 toy 파일의 기본값 근거로는 쓸 수 없다.

| 배열 | 상태 | 위치 |
|------|------|------|
| `Ch_LLR_3SD` | **초기화식 자체가 없다** (선언만). 3SD 채널 LLR 기본표 전부 소실 | decoder.cpp:6932 |
| `table_HD`, `table_2SD`, `table_3SD` | **초기화식 자체가 없다** (선언만). VNU 임계값 기본표 전부 소실 | decoder.cpp:7143-7145 |
| `Ch_LLR_2SD` | 초기화식은 있으나 3-bit 분기(6894-6929)의 36개 row가 전부 `{15, 4, 15, 4, 17, 5, 13, 4}`로 동일하다. iteration별 변화가 사라진 자리표시 값 | decoder.cpp:6842-6931 |
| `Ch_LLR_HD` | 같은 형태. 3-bit 분기(6777 이후)의 row가 전부 `{21, 14, 12, 10}` | decoder.cpp:6693-6841 |

따라서 **toy 2SD/3SD 파일의 ch, th 값은 원본에서 가져올 수 없다.** 합리적 추정값을 쓰되
`Ch_LLR_2SD` 3-bit 자리표시 값(dv 구간별 `{15,4}`, `{15,4}`, `{17,5}`, `{13,4}`)은
strong이 weak의 3배가량이라는 크기 관계 참고 정도로만 쓴다.

---

## 8. SD 경로에만 있는 특이 동작

- ㉮ **restart iteration이 Pre 단계로 바뀐다.** 3절의 핵심이며 이식에서 가장 놓치기 쉬운 지점이다
- ㉯ **Jump_Iter의 SD 분기.** `Jump_Iter` (decoder.cpp:4954-5291)는
  `Error_count_reg > diverse_th`이면 다음 restart 지점으로 iteration을 건너뛴다
  (2SD는 5082-5108, 3SD는 5112 이하). 다만 이 함수는
  `MODE_POWER_STOPPING_ON == power_index`일 때만 호출되고(decoder.cpp:1961-1965),
  전력 절감 기능은 Python 이식 범위 밖이다 (`docs/차이.md` 1절 5번). SD의 임계값
  `SD_POWER_STOPPING_TH = 999999`(common.h:188)는 사실상 비활성 값이다
- ㉰ **Soft_LLR_weak_degree.** 3SD에서만 채워지는 보조 배열이다
  (`Mapper_3bit_SD_weak_degree`, decoder.cpp:4854-4866, 호출은 4925). region을
  3, 2, 1, 0으로 되돌려 담는 값이며 디코딩 산술에서는 읽히지 않는다. 로그와 TV 용도다
- ㉱ **Get_Err_Cnt의 SD 분기.** `i_SD_input`을 보고 strong error 수와 weak correct 수를
  따로 센다 (decoder.cpp:5388-5405). 통계 항목이며 디코딩 결과에는 영향이 없다
- ㉲ **strong_error 채널과의 연결.** `Make_Dec_Input_Ref_C_Fixed_4KB`
  (ecc_top.cpp:1828-1895)에서 `MODE_CH_STRONG_ERROR`는 `SD_input`을 초기값 1(strong)로 두고
  (1850) SER, SCR 비율만큼 weak으로 내린다. Python `strong_error_channel`
  (channel.py:91-135)이 이 구조를 이미 그대로 따르고 있다. 이 채널은 2SD 전용이며
  `CC_input`은 초기값 1로 두기만 하고(1851) 3SD 전용 분포는
  `MODE_CH_3SD_FIXED` (ecc_top.cpp:1896-1909)가 따로 만든다
- ㉳ **TV 출력의 iteration 하한이 다르다.** HD는 `mn > 0`, SD는 `mn > -1`부터 출력한다
  (decoder.cpp:1849-1851, 1907-1908). TV 전용이며 산술과 무관하다
- ㉴ **HCU 짝 함수.** `VN_Cal_SD_HCU` (4649)는 half column 분할과 `Sum_t_OLD` 누적만 다르고
  region 선택과 판정 산술은 `VN_Cal_SD`와 같다. HCU는 Python 이식 범위 밖이다

---

## 9. Python 이식 시 바뀌어야 할 지점

`2_LDPC_light/LDPC_base/decoder.py`와 `docs/차이.md` 기준이다.

### 9.1 채널 출력 해석 (`_read_channel_input`)

read bit 외에 **region 인덱스 배열** `(B, N_b, z)`를 함께 만든다.

- ㉮ 2SD: `region = 1 - sd`
- ㉯ 3SD: `region = 2*(1 - sd) + (cc ^ sd)`
- ㉰ HD: region 개념 없음 (현재대로)

### 9.2 채널 항 선택 (`_process_column`)

지금은 `state.cur_ch = self.llr_matrix.row_ch[table_row_idx, :, 0]`으로 dv별 스칼라를 쓰고
(decoder.py:261) column 안에서 브로드캐스트한다 (decoder.py:288-289).
SD에서는 `row_ch[table_row_idx]`가 `(활성 프레임, num_dv, ch_len)`이므로
**비트별 region으로 한 번 더 색인**해야 한다.

```
ch_per_bit = cur_ch[frame_idx, dv_idx, region[:, col, :]]   # (활성 프레임, z)
```

region 배열도 genie 마스킹 시 `read_bit`과 함께 압축 대상에 넣어야 한다
(`_check_errors`의 `keep` 슬라이싱, decoder.py:343-348).

### 9.3 CN 초기 상태 (`_init_state`)

HD는 `min1 = min2 = RESET`으로 시작한다 (decoder.py:228-230). SD는 C++ iteration 0의 Pre
단계를 재현해 **채널 magnitude를 CN에 심고 시작**해야 한다.

- ㉮ column을 0부터 `N_b-1`까지, 각 column 안에서 edge를 `ii` 순서대로 돌면서
  `new_mag = 채널 magnitude(region)`, `new_sgn = read_bit`으로 `_cnu_update`를
  `edge_clear=True`로 한 번씩 호출한다 (remove-old 없음)
- ㉯ 채널 magnitude는 3-bit 기준 2SD `[5, 1]`, 3SD `[7, 5, 3, 1]`이다.
  C++은 이 값을 `Make_LLR`에 `EDGE_MAG_*` 상수로 박아 두었고 LLR matrix 파일에서 읽지 않는다
  (decoder.cpp:4905, 4924)
- ㉰ 그 뒤 `check_sum`과 `edge_sgn`을 0으로 되돌린다 (C++ decoder.cpp:3007, 2783-2785 대응)
- ㉱ `syndrome`과 `prev_csw`는 지금처럼 `H·read_bit`과 그 무게로 두면 등가다
- ㉲ `min1_pos`는 갱신 순서에 따라 결정된다. 방문 순서가 결과에 영향을 주므로
  `_column_order`와 같은 순서를 써야 한다

주의: `edge_mag`가 균일 n-bit 합성 행렬일 때는 C++ 대응이 없다. 채널 magnitude를
`[5, 1]`, `[7, 5, 3, 1]` 고정으로 둘지 `edge_mag`의 상위 레벨에서 뽑을지 결정이 필요하다
(미결정 사항으로 태스크 문서에 올림).

### 9.4 Edge Clear 판정 (`_is_edge_clear_iter`)

지금은 `iteration == 1 or is_restart(iteration)` (decoder.py:118). 이것은 HD 규칙이다.
SD는 **`is_restart(iteration)`만** 이어야 한다 (3.1의 표).

### 9.5 restart iteration의 동작 (`_run_iteration`)

지금은 CN 상태를 RESET으로 클리어하고 그 iteration의 row 값을 그대로 산술에 쓴다
(decoder.py:253-259, `docs/차이.md` 2절 5번). SD는 다르다.

- ㉮ CN 상태를 클리어한 뒤 9.3과 같은 방식으로 **채널 magnitude를 다시 심는다**
- ㉯ 그 iteration의 column 루프는 일반 VN 계산을 하지 않는다.
  판정 비트는 `decision_bits = read_bit` (반전 없음)
- ㉰ 그 iteration의 row에 담긴 ch, th 값은 쓰이지 않는다
- ㉱ iteration 종료 시 `prev_csw = |syndrome|`이 된다

### 9.6 손대지 않아도 되는 곳

- ㉮ `_vn_decide` (반전 조건 `sum_t <= 0`, 2절)
- ㉯ `_vnu_quantize` (5절)
- ㉰ `_c2v_reconstruct`, `_cnu_update` (모드 무관 공통 경로)
- ㉱ `llr_matrix.row_index`와 CSW 계산 (6절)
- ㉲ `channel.py`의 region 플래그 생성 (1.1과 대조 완료, 일치)

### 9.7 `docs/차이.md`에 추가될 항목

- ㉮ 1절 1번 "지원 디코딩 모드"를 HD, 2SD, 3SD로 갱신
- ㉯ 2절 4번 "edge clear" 항목에 모드별 대상 iteration 차이를 명시
- ㉰ 2절 5번 "restart row"는 HD 전용 서술임을 명시하고, SD의 restart는 Pre 단계라는 항목을 신설
- ㉱ Jump_Iter(전력 절감 연동 iteration 점프)를 1절 미구현 항목에 추가

---

## 10. 확인 불가 항목

- ㉮ 비 AUTO 빌드가 쓰는 2SD, 3SD 기본 ch, th 테이블의 실제 값 (7.2 참조).
  `decoder.cpp`의 해당 배열 초기화식이 소실되었다. 파일은 `0_LDPC_original/decoder.cpp`
- ㉯ 원본 소스 전반에 한글 주석의 문자 인코딩이 깨진 구간이 있다
  (`channel.cpp:9, 31, 40, 48, 58, 70, 79`, `ecc_top.cpp:1792-1793, 1824-1825` 등).
  주석 내용은 읽을 수 없으나 코드 자체는 온전해 분석에 지장이 없었다
- ㉰ C++ 빌드와 실행은 하지 않았다 (저장소 공통 규칙). 위 결론은 전부 정적 독해 근거다
