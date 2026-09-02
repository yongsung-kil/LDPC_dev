# 워커 I_3: 관점 12 `__AUTO_LLR_OPT__` 분류 재검토 (작성자 요청 6)

> 작성: 2026-09-03 01:15:26
> 팀 I(iteration 번호 체계와 빌드 갈래) / 관점 12

---

## 확인 범위

| 파일 | 읽은 줄 | 목적 |
|------|---------|------|
| [20260902_SW_branch_LLR_matrix.md](../../20260902_SW_branch_LLR_matrix.md) | 전체 (1-362), 특히 6장 289-350 | 분류 표 대조 |
| [code_diff.md](../../code_diff.md) | 전체 (1-1007) | 수정 후 코드 유무 확인 |
| [common.h](../../../../../../0_LDPC_original/src/common.h) | 45-56 | `DISPLAY_UNIT` 갈래 |
| [mode.h](../../../../../../0_LDPC_original/src/mode.h) | 12-33 | AUTO 정의 조건 |
| [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) | 450-629, 1110-1169, 1890-1999, 2080-2134, 2360-2389, 3970-4040, 4040-4169, 6598-6647, 7330-7369, 7510-7599, 7700-7829, 7900-7959, 8050-8115 | 6.3 후보 판정, 6.2 실제 사용값 |
| [main.cpp](../../../../../../0_LDPC_original/src/main.cpp) | 85-164, 225-244, 295-334, 695-734 | 인자 파싱, 결과 출력, `Set_Ref_C_Iteration` |
| [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) | 634-698, 760-775, 860-974, 2035-2060, 2149-2179, 2224-2269 | 결과 출력 경로, `fr_4KB` 갱신 |
| [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) | 100-144 | MN 배열 구성 |
| [Mock_ECC.py](../../../../../Util/Mock_ECC.py) | 200-249 | mock CSW 로그 형식 |
| grep `__AUTO_LLR_OPT__` | `0_LDPC_original/src` 전체 | 히트 87곳 재검증 |

---

## 1. 히트 수 재검증과 6장과의 차이

grep 결과는 Round 1이 센 것과 파일별로 완전히 같다. 총 87곳이다.

| 파일 | 히트 수 | 줄 |
|------|--------|-----|
| common.h | 3 | 49, 403, 407 |
| decoder.cpp | 36 | 505, 526, 548, 570, 1137, 1917, 1921, 2084, 2129, 2374, 2797, 3985, 4055, 4160, 4274, 4366, 4505, 4673, 6541, 6609, 6984, 7047, 7339, 7352, 7522, 7549, 7574, 7741, 7743, 7773, 7775, 7803, 7805, 7928, 7938, 8109 |
| decoder.h | 3 | 185, 188, 431 |
| ecc_data.h | 1 | 143 |
| ecc_top.h | 2 | 161, 165 |
| ecc_top.cpp | 17 | 322, 496, 532, 595, 624, 652, 680, 699, 783, 927, 944, 950, 965, 2166, 2219, 2562, 2567 |
| main.cpp | 21 | 12, 15, 54, 92, 140, 259, 313, 324, 329, 485, 593, 609, 637, 650, 706, 922, 923, 925, 966, 967, 969 |
| mode.h | 2 | 22, 23 |
| random.cpp | 1 | 222 |
| random.h | 1 | 31 |

상위 문서 6장의 줄 번호 항목은 6.1이 10개, 6.2가 5개, 6.3이 48개로 모두 63개이며,
이 항목들이 덮는 grep 히트는 77곳이다. Round 1이 적은 "86"은 어느 셈법으로도
재현되지 않으므로, 대조는 수가 아니라 **덮이지 않은 블록**으로 판정했다.

**6장 어디에도 없는 히트 (모두 decoder.cpp, 살아 있는 코드 8줄 = 4블록)**

| 줄 | 함수 | 내용 |
|-----|------|------|
| 7741-7743 | `Init_Log_Data` | `m_log_CSW_auto[i] = -1` |
| 7773-7775 | `Alloc_Log_Data` | `m_log_CSW_auto = new int[MN_size]` |
| 7803-7805 | `Release_Log_Data` | `delete[] m_log_CSW_auto` |
| 7928-7938 | `Print_Log_CSW_Auto` | 함수 정의 전체 |

`main.cpp:329`, `main.cpp:485`는 주석 처리된 `//#ifdef`, `//#endif`이므로 빠진 것이 맞다.

---

## 2. 작성자 요청 6 판정: 6.3으로 넘긴 것 중 실제로 고쳐야 하는 것

Round 1이 지목한 후보를 하나씩 판정했다. **판정 결과 한 곳이 조건부 오분류**이며,
나머지는 분류가 맞다.

| # | 후보 | 6.3 서술 | 판정 | 근거 |
|---|------|---------|------|------|
| 1 | `decoder.cpp:505-510` | power stopping OFF 고정 | **분류 맞음** | AUTO 갈래(506)와 비AUTO 갈래(509)가 모두 `MODE_POWER_STOPPING_OFF`다. 켜는 줄(508)은 주석이다. 따라서 `decoder.cpp:1961`의 `MODE_POWER_STOPPING_ON` 조건이 어느 빌드에서도 참이 되지 않아 `Jump_Iter`(1962)는 실행되지 않고, `Select_BF`(1968-1970)는 `mn == 0`에서 항상 도달한다. BF 부활이 이 블록에 요구하는 변경이 없다 |
| 2 | `decoder.cpp:1917-1921` | CSW 로그 수집 | **코드는 맞음, 로그 뜻은 바뀜** | 아래 발견 2 |
| 3 | `decoder.cpp:1929` | (6장 항목 아님) | **6장 대상이 아님** | 이 줄은 `ITER_MAX_HBF` 히트이지 `__AUTO_LLR_OPT__` 히트가 아니다. 상위 5.5 표에 "VNU 로그 출력 조건"으로 이미 올라 있다. 감싸는 스위치는 `__LOG_DECODING_STATUS__`가 아니라 `__LOG_VNU_IN_OUT__`(1925)이며 `mode.h:33`에서 주석 처리되어 있어 현재 빌드에 들어가지 않는다 |
| 4 | `decoder.cpp:7339-7352` | `Compute_CSW_Auto` 정의 | **분류 맞음** | 함수 본문(7342-7350)은 `Check_REG`와 `Syndrome`만 읽어 현재 프레임의 check sum weight를 센다. 분기나 BF 진입 여부와 무관하다. 고칠 것이 없다 |
| 5 | `decoder.cpp:7522-7528`, `7549-7553`, `7574-7578` | CSW 로그 파일 열기, 닫기, 출력 | **분류 맞음** | 세 곳 모두 `flag_print_CSW_log` 검사와 `fopen`, `fclose`, `Print_Log_CSW_Auto` 호출뿐이다. 다만 실제 출력 본체인 `Print_Log_CSW_Auto`(7928-7938)가 6장에서 빠져 있다 (발견 3) |
| 6 | `main.cpp:140-144` | 실행 인자 파싱 | **분류 맞음** | `argc > 19`이면 `argv[19]`에서 H-matrix 파일 이름을 받는 갈래다. BF, `ITER_MAX_HBF`, SW 분기 어느 것과도 닿지 않는다 |
| 7 | `main.cpp:308` | (6장 항목 아님) | **6장 대상이 아님, 별도 LOW** | `__AUTO_LLR_OPT__` 히트가 아니다 (`#ifdef`가 313에서 시작한다). 별도 문제로 발견 5에 적었다 |
| 8 | `main.cpp:706` | 진입점과 `LOCAL_OPT` 배선 | **이 줄은 분류 맞음, 다만 짝이 빠짐** | AUTO에서는 `Set_Ref_C_Iteration` 본문 전체가 `#ifndef`(706)로 빠지고 MN 설정을 `local_opt.cpp:116-131`이 대신한다. 비AUTO의 `main.cpp:719` `MN[0] = ITER_MAX_HBF`에 대응하는 AUTO 쪽 줄이 `local_opt.cpp:129`인데, code_diff 3.5가 116-123만 고치고 124-131을 손대지 않는다 (발견 1) |
| 9 | `ecc_top.cpp:652, 680, 944-950` | 결과 출력 | **조건부 오분류 (HIGH)** | 아래 발견 1 |
| 10 | `decoder.cpp:8109-8113` | 양쪽 갈래가 같은 값 | **분류 맞음** | 두 갈래(8110, 8112)가 `state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;`로 글자까지 같다. 이 히트는 `__HD_FLOOR_SET__`의 `#else` 안(8108-8114)에만 있으므로 "`__HD_FLOOR_SET__` 꺼짐에서만 동일"이 아니라 **이 히트가 존재하는 모든 조합에서 동일**하다. Round 1의 단서는 불필요하다 |

**요청 6 답**: 6.3의 27개 항목 가운데 `ecc_top.cpp:652, 680, 944-950`(결과 출력) 한 줄이
조건부 오분류다. 전처리기 갈래 자체는 고칠 것이 없으나, 그 갈래가 부르는 출력 함수가
`ITER_MAX_HBF`를 4로 되돌린 뒤에도 그대로면 결과 파일의 iteration별 FER 열이 망가진다.
나머지 후보(1, 4, 5, 6, 8, 10)는 분류가 맞다. 후보 3과 7은 애초에 6장 대상이 아니다.

---

## 3. 발견

### 발견 1 (HIGH, ㉮ 수정 후 코드를 적용하면 생기는 결함)

**`local_opt.cpp:124-131`이 code_diff에 없어서, `ITER_MAX_HBF`가 4가 되면 `MN[]`에 음수가 들어가고
결과 파일의 iteration별 FER 열이 전부 뒤집힌다.**

근거:

- `local_opt.cpp:124-131`
  ```
  if ((MODE_DEC_HD == init_n) || (MODE_DEC_1_SSD == init_n)) {
      for (i = 0; i < MN_num; i++) { MN[i] -= ITER_MAX_HBF; }
      if (MN_num > 1) { MN[0] = ITER_MAX_HBF; }
  }
  ```
- code_diff [3.5장](../../code_diff.md#ch3)은 `local_opt.cpp:116-123`만 바꾸고 124-131은 수정 전후 어디에도 없다.
  상위 5.5 표는 `local_opt.cpp:126-130`을 "딸려 오는 곳"으로 적어 두었으나 바뀔 모습을 적지 않았다
- `LLR_MATRIX_1.txt` 기준 `MN_num = 124`, 3.5 적용 후 `MN[i] = i` (i < 123), `MN[123] = 124`.
  여기에 `ITER_MAX_HBF = 4`가 들어가면 `MN = [4, -3, -2, -1, 0, 1, 2, ..., 118, 120]`이 된다
- `ecc_top.cpp:877-879`가 `if (o_iter_num > m_param_dec->MN[n]) fr_4KB[n]++;`로 iteration별 실패 수를 센다.
  `MN[1] = -3`이므로 모든 프레임이 `fr_4KB[1]`을 올린다. 열 1, 2, 3, 4의 FER이 전부 1.0이 된다
- `ecc_top.cpp:2052-2056` (`Print_Result_Part1_Auto`, 652에서 호출)이 열 머리글을
  `MN[n]` 그대로 찍는다. `Ref_C_result_*.txt`에 `FER (4 -3 -2 -1 0 1 ...)`이 남는다
- `ecc_top.cpp:2156-2157` (`Print_Result_Part2_Memory_Opt`, 680에서 호출)이
  `FER[i] = fr[i] / rn`을 `str_result_name_4KB` 파일에 찍는다

현재(`ITER_MAX_HBF = 0`)는 124-131이 아무것도 바꾸지 않아 드러나지 않는다.
이 결함은 DAO가 읽는 두 결과 파일에 동시에 나타나며, 프로세스는 계속 돈다.

**처방**: code_diff 3.5에 `local_opt.cpp:124-131`의 수정 후 코드를 넣고,
BF 진입 프레임과 미진입 프레임의 iteration 번호를 어느 기준으로 `MN[]`에 담을지 정한다.
이 처방은 **동작 변경을 요구한다** (MN 배열 구성 규칙이 바뀐다).
`decoder.cpp:1976`의 `iter_num -= ITER_MAX_HBF` 보정과 함께 정해야 하므로
관점 7(MN 배열과 iteration 번호 체계) 결과와 맞춰야 한다.

### 발견 2 (MEDIUM, ㉯ 문서 서술의 누락)

**CSW 로그에 프레임이 탄 분기 index가 없어, 분기별 row를 최적화할 근거가 로그에 남지 않는다.**

근거:

- `decoder.cpp:1918-1919`가 `m_log_CSW_auto[mn] = Compute_CSW_Auto();`로 iteration 자리에만 값을 넣는다
- `decoder.cpp:7929-7937` (`Print_Log_CSW_Auto`)가 `m_sector_idx` 하나와
  `MN_size`개의 값을 찍는다. 분기 index를 찍는 자리가 없다
- BF가 살아나면 같은 iteration 자리에 서로 다른 분기의 프레임이 섞인다.
  BF 미진입 프레임은 `Select_BF`(`decoder.cpp:2097-2098`)에서 `mn`이 0에서 4로 뛰므로
  자리 1~4가 `Init_Log_Data`(`decoder.cpp:7742`)가 넣은 -1로 남는다.
  BF 진입 프레임은 1~4가 채워진다. 한 열 안에 -1과 실제 CSW가 섞인다

상위 문서 1장이 DAO 대응을 범위 밖에 두었으나, 로그를 만드는 쪽은 이 문서의 범위 안이다.
6.3이 이 세 곳(`1917-1921`, `7522-7578`, 그리고 6장에 없는 `7928-7938`)을
"손대지 않아도 되는 곳"으로만 적어, 뜻이 바뀌는 사실이 문서 어디에도 남지 않았다.

**처방**: 로그 한 줄에 `cur_sw_branch_idx[]`를 함께 찍거나,
상위 6.3에 "코드는 그대로 두되 로그 해석이 바뀐다"를 명시한다.
앞쪽 처방은 **코드 추가를 요구하되 복호 동작은 바꾸지 않는다**.

### 발견 3 (MEDIUM, ㉯ 문서 서술의 누락)

**6장 제목이 "전수 목록"인데 `decoder.cpp`의 네 블록이 빠졌다.**

빠진 곳은 1절 표의 네 블록(`7741-7743`, `7773-7775`, `7803-7805`, `7928-7938`)이다.
넷 다 `m_log_CSW_auto` 배열의 초기화, 할당, 해제, 출력이며 6.3에 들어가는 성격이다.
셋(`Init_Log_Data`, `Alloc_Log_Data`, `Release_Log_Data`)은 `MN_size`를
`MN[MN_num - 1] + ITER_MAX_HBF + 1`로 잡으므로 `ITER_MAX_HBF`가 바뀔 때 크기가 달라진다.
`Decoder::Alloc_Log_Data`는 `decoder.cpp:261`에서 컴파일 스위치 없이 불리므로
AUTO 빌드에서 배열은 반드시 할당된다 (`m_log_CSW_auto`에 대한 널 접근 위험은 없다).

**처방**: 6.3 표에 네 블록을 추가한다. **코드 변경을 요구하지 않는다.**

### 발견 4 (MEDIUM, ㉯ 문서 서술의 누락)

**6.1이 "고쳐야 하는 곳"으로 적은 두 곳에 대응하는 수정 후 코드가 code_diff에 없다.**

- `decoder.cpp:1137-1141` (`Get_Cur_LLR_Idx_FILE` 대 `Get_VNU_Table_Idx` 갈림):
  code_diff 어느 장에도 나오지 않는다. code_diff 6장이 `Get_Cur_LLR_Idx_FILE`의
  `#if defined(__AUTO_LLR_OPT__)` 갈래를 없애 한 갈래로 합치는데,
  1137의 갈래를 그대로 두면 비AUTO 빌드에서 합쳐진 함수가 호출되지 않는다.
  이 갈래를 어떻게 할지가 상위 7장 ㉱(두 경로를 통일할지)의 미결정과 맞물린다
- `decoder.cpp:6609-6626` (`Is_Iter_Type_Init`): code_diff [8.2장](../../code_diff.md#ch8)에
  "같은 방식으로 `__AUTO_LLR_OPT__` 갈래만 남긴다. 조건은 그대로 둔다"는 산문만 있고
  수정 후 코드 블록이 없다. 8.1은 코드 블록이 있어 두 절의 형식이 어긋난다

**처방**: 두 곳의 수정 후 코드를 code_diff에 넣는다. `decoder.cpp:1137-1141`은
7장 ㉱ 결정에 따라 **코드 삭제(비AUTO 갈래 제거)를 요구할 수 있다**.

### 발견 5 (MEDIUM, ㉯ 문서 서술의 누락)

**6.2를 "분기 지원 자체와는 무관, 확인만"으로 적었으나, BF가 살아나면 이 다섯 곳이
iteration 1~4에서 실제로 파일 값을 쓴다.**

`decoder.cpp:3985-3990`을 포함한 다섯 곳은 `Get_VNU_LLR_SET_FILE`로
`ch1~ch4`, `th1~th7`을 한꺼번에 받는다. BF 구간에서 이 값들이 어떻게 쓰이는지 확인했다.

- ㉮ `ch1`은 BF 진입 여부와 무관하게 항상 쓰인다.
  `decoder.cpp:4019` `channel_llr = ch1;`은 1bit 갈래 밖에 있고 `sum_t`의 초기값이 된다 (`decoder.cpp:4026`)
- ㉯ `th1~th7`은 `v_deg > DV_5`인 column에서만 건너뛴다.
  1bit 갈래(`decoder.cpp:4056-4079`)는 `EDGE_MAG_7` 또는 `EDGE_MAG_8`로 크기를 고정하지만,
  이 갈래는 `(TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)` 셋을 모두 만족할 때만 탄다.
  `v_deg <= DV_5`인 column은 BF 구간에서도 4bit 갈래(`decoder.cpp:4080-4120`)로 가서 `th1~th7`을 쓴다
- ㉰ 따라서 BF 구간의 iteration 1~4가 어느 row를 고르는지가 복호 결과를 바꾼다.
  그 row는 `decoder.cpp:1138` `Get_Cur_LLR_Idx_FILE(mn)`이 정한다

`msg1.md`의 "bf라면 llr matrix에서 threshold를 받지 않아"는 row의 **분기 문턱 칸**이 -1이라는 뜻이지
LLR 파라미터를 안 쓴다는 뜻이 아니다. 문서가 이 구분을 적어 두지 않으면
"BF 구간은 파일과 무관하다"로 읽힐 여지가 있다.

**처방**: 6.2에 "BF가 살아나면 iteration 1~4에서도 파일 row가 쓰이며,
`ch1`은 모든 column에, `th1~th7`은 `v_deg <= DV_5` column에 적용된다"를 덧붙인다.
**코드 변경을 요구하지 않는다.**

### 발견 6 (LOW, ㉯ 문서 서술의 누락)

**결과 파일의 `SW_Threshold` 출력이 실제 BF 문턱과 다르다.**

`main.cpp:308`이 `SW_TH_BF_DEFAULT`(630)를 찍는데, `LAYOUT_PRIME_512B_TLC_VSS_OFF`에서
실제로 쓰이는 값은 `syn_th_BF0 = SW_TH_BF0_512B_TLC_OFF`(680)다 (`decoder.cpp:467`).
code_diff [4.1장](../../code_diff.md#ch4)을 적용해도 이 관계는 그대로다.
지금은 AUTO에서 BF가 돌지 않아 이 줄이 무해한 잡음이지만,
BF가 살아나면 결과 파일이 실제와 다른 문턱을 알린다.
`main.cpp:308`은 `__AUTO_LLR_OPT__` 갈래 안이 아니므로 6장 대상이 아니고,
5장 어디에도 없다.

**처방**: `main.cpp:308`이 `g_param_dec` 대신 실제 문턱을 찍게 하거나,
분기 문턱 배열을 찍도록 바꾼다. **동작(복호)은 바꾸지 않는다.**

### 발견 7 (LOW, 참고)

`Mock_ECC.py:221-233`(`generate_mock_csw_log`)은 CSW 로그 한 줄을
**그룹 수만큼**의 값으로 만든다. 실제 `Decoder::Print_Log_CSW_Auto`(`decoder.cpp:7929-7937`)는
`m_sector_idx` 하나와 **iteration 수(`MN_size`)만큼**의 값을 찍는다.
둘의 형식이 이미 어긋나 있으며 이번 변경이 만든 것은 아니다.
BF 부활로 실제 로그의 자리 1~4에 -1이 섞이면 차이가 더 벌어진다.
상위 문서가 DAO 대응을 범위 밖에 두었으므로 여기서는 사실만 적는다.

---

## 4. 심각도별 집계

| 심각도 | 건수 | 항목 |
|--------|------|------|
| CRITICAL | 0 | |
| HIGH | 1 | 발견 1 (`local_opt.cpp:124-131` 미수정으로 결과 파일 FER 열 손상) |
| MEDIUM | 4 | 발견 2 (CSW 로그에 분기 없음), 발견 3 (6장 전수 목록 4블록 누락), 발견 4 (6.1 두 곳의 수정 후 코드 없음), 발견 5 (6.2가 BF 구간 파일 사용을 안 적음) |
| LOW | 2 | 발견 6 (`SW_Threshold` 출력), 발견 7 (Mock_ECC 로그 형식) |

구분: 발견 1은 ㉮(수정 후 코드를 그대로 적용하면 생기는 결함),
발견 2~7은 ㉯(문서 서술 자체의 누락과 불일치)다.
