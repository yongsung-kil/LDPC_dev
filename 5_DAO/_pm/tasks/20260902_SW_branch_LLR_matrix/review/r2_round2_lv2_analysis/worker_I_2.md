# 워커 I_2 결과: 관점 6 `ITER_MAX_HBF` 딸린 곳 전수 (작성자 요청 5)

> 작성: 2026-09-03 01:13:51
> 팀 I (iteration 번호 체계와 빌드 갈래), 관점 6

---

## 확인 범위

| 파일 | 읽은 줄 | 목적 |
|------|--------|------|
| [20260902_SW_branch_LLR_matrix.md](../../20260902_SW_branch_LLR_matrix.md) | 전체 (1-362) | 5.5장 두 표, 5.6장, 6장 |
| [code_diff.md](../../code_diff.md) | 전체 (1-1006) | 1.2장, 7장, 8장, 9장 |
| [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) | 1112-1166, 1410-1479, 1600-1649, 1790-1849, 1915-1984, 2098-2127, 2140-2209, 2298-2319, 2360-2399, 3478-3495, 6430-6478, 6536-6605, 7570-7614, 7700-7759 | 히트별 컴파일 스위치와 동작 |
| [common.h](../../../../../../0_LDPC_original/src/common.h) | 392-413 | `ITER_MAX_HBF` 정의 |
| [mode.h](../../../../../../0_LDPC_original/src/mode.h) | 전체 (1-83) | AUTO 빌드에서 켜지는 스위치 판정 |
| [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) | 108-147 | `MN[]` 채우기와 `ITER_MAX_HBF` 보정 |
| [main.cpp](../../../../../../0_LDPC_original/src/main.cpp) | 695-739 | `Set_Ref_C_Iteration` |
| [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) | 866-895, 2012-2060, 2730-2829 | `MN[]` 소비처 |
| [TV_Dec_Inter.cpp](../../../../../../0_LDPC_original/src/TV_Dec_Inter.cpp) | 1055-1099 | TV 출력 시점 |
| grep 전수 | `ITER_MAX_HBF`, `MN[`, `MN_size`, `iter/mn/MN` 과 상수 4 비교 | 히트 재계수 |

## 요청 5 판정 (한 줄)

**빠진 곳이 있다.** 실제로 컴파일되고 실행되는 누락 한 곳([decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp)), 스위치가 켜지면 살아나는 누락 다섯 곳(1448, 1622, 1821, 1828, 2190), 그리고 표에는 있으나 결과가 깨지는 것을 다루지 않은 한 곳(local_opt.cpp:126-130)이 있다.

---

## 1. 히트 재계수 (Round 1 수치 검증)

Grep 원자료를 주석과 주석 처리된 코드까지 포함해 다시 세었다.

| 파일 | grep 줄 수 | 주석/비활성 | 실제 코드 | Round 1 수치 | 판정 |
|------|-----------|------------|----------|-------------|------|
| common.h | 2 | 0 | 2 (정의 자체) | 세지 않음 | 정의라 제외한 것이 타당 |
| decoder.cpp | 45 | 4 (2312, 3489 주석문, 6452, 6453 주석 처리) | 41 | 41 | 일치 |
| local_opt.cpp | 2 | 0 | 2 | 2 | 일치 |
| main.cpp | 1 | 0 | 1 | 1 | 일치 |
| TV_Dec_Inter.cpp | 15 | 10 (주석 처리) | 5 | 5 | 일치 |

Round 1의 계수는 정확하다. `MN_size` 계열은 7583을 포함해 18곳이고, Round 1이 말한 "7717~8018의 17곳"은 7583을 뺀 수라 맞다.

## 2. 5.5장 첫 표와 grep 히트의 줄 단위 대조

### 2.1 표에 있는 줄

5.5장 첫 표는 **11행**이고 그 안에 담긴 소스 위치는 **13개**다 (`2097-2098`, `2114-2115`, `126-130`을 각각 한 곳으로 세고, `2310, 3487`과 `6545, 6571`을 두 곳씩으로 셀 때).

| 표의 위치 | grep에 있음 | 감싸는 스위치 | AUTO 빌드 실행 |
|-----------|-----------|--------------|---------------|
| decoder.cpp:564 | 있음 | 없음 | 실행 |
| decoder.cpp:1149 | 있음 | `__RUN_PREPROCESSING__` (mode.h:63 꺼짐) | 미컴파일 |
| decoder.cpp:1929 | 있음 | `__LOG_VNU_IN_OUT__` (mode.h:33 꺼짐) | 미컴파일 |
| decoder.cpp:1976 | 있음 | 없음 | 실행 |
| decoder.cpp:2097-2098 | 있음 | `#else` of `__AUTO_LLR_OPT__` | 지금은 미컴파일, code_diff 5.1이 살림 |
| decoder.cpp:2114-2115 | 있음 | 같음 | 같음 |
| decoder.cpp:2310 | 있음 | `__RUN_PREPROCESSING__` 꺼짐 | 미컴파일 |
| decoder.cpp:3487 | 있음 | `__RUN_PREPROCESSING__` 꺼짐 | 미컴파일 |
| decoder.cpp:6454 | 있음 | `__RUN_ITER34_HIGH_DV_SKIP__` (mode.h:78 꺼짐) | 미컴파일 |
| decoder.cpp:6545 | 있음 | `__AUTO_LLR_OPT__` 갈래 | 실행 |
| decoder.cpp:6571 | 있음 | `#else` 갈래 | 미컴파일 |
| decoder.cpp:7583 | 있음 | `__LOG_DECODING_STATUS__` (mode.h:32 꺼짐) | 미컴파일 |
| local_opt.cpp:126-130 | 있음 | 없음 | 실행 |

### 2.2 표에 없는 줄 (decoder.cpp 41곳 중 27곳)

| 줄 | 감싸는 스위치 | AUTO 빌드 | 0에서 4로 바뀔 때의 동작 | 표에 없어도 되는가 |
|----|--------------|-----------|------------------------|------------------|
| 1448 | `__RUN_PARITY_SKIP__` (mode.h:79 꺼짐) | 미컴파일 | `mn == 1` 하나뿐이던 parity skip 시점이 `mn == 1` 또는 `mn == 5` 둘로 갈림 | 아니오, 넣어야 함 |
| 1622 | `__RUN_PARITY_SKIP__` 꺼짐 | 미컴파일 | 1448과 짝을 이루는 `V2C_Store` 억제 시점이 같이 갈림 | 아니오 |
| 1821 | `__RUN_PREPROCESSING__` 꺼짐 | 미컴파일 | BF 미진입 프레임의 `CYCLE_FOR_PREPROCESSING` 클럭 가산 시점이 `mn == 1`에서 `mn == 5`로 이동 | 아니오, 같은 스위치의 1149, 2310, 3487은 표에 있음 |
| 1828 | `__RUN_PARITY_SKIP__` 꺼짐 | 미컴파일 | `overall_clk -= M_b - 2` 보정이 한 번에서 두 번(mn 1과 5)으로 늘어남 | 아니오 |
| **2169** | **`__DUAL_UPDATE__` (mode.h:64 켜짐)** | **컴파일되고 실행됨** | **PCRC 종료 제한 구간이 `mn == 1`에서 `mn == 1` 또는 `mn == 5`로 늘어남. mn 5에서 마지막 termination point에서만 종료 가능해짐** | **아니오, 반드시 넣어야 함** |
| 2190 | `#else` of `__DUAL_UPDATE__` | 미컴파일 | 2169와 같은 변화 | 아니오 |
| 2377 | `#else` of `__AUTO_LLR_OPT__` | 미컴파일 | 5.5장 둘째 표(2374-2378)의 `#else` 반쪽 | 예, 둘째 표가 덮음 |
| 2800 | 같음 | 미컴파일 | 둘째 표(2797-2801)의 `#else` 반쪽 | 예 |
| 4058 | 같음 | 미컴파일 | 둘째 표(4055-4059) | 예 |
| 4277 | 같음 | 미컴파일 | 둘째 표(4274-4278) | 예 |
| 7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018 (17곳) | 대부분 무가드, 일부 `__LOG_DECODING_STATUS__` | 일부 실행 | **값이 바뀌지 않는다** (아래 3.3 증명) | 예 |

### 2.3 다른 파일의 표 밖 히트

| 줄 | 감싸는 스위치 | AUTO 빌드 | 동작 변화 | 표에 없어도 되는가 |
|----|--------------|-----------|----------|------------------|
| main.cpp:719 | `#ifndef __AUTO_LLR_OPT__` (main.cpp:706) | 미컴파일 | AUTO에서 컴파일되지 않고, 비AUTO에서는 이미 4였으므로 변화 없음 | 예 |
| TV_Dec_Inter.cpp:1077, 1221, 1295, 1487, 1535 | `__RUN_ITER34_HIGH_DV_SKIP__` 꺼짐. 게다가 호출부가 `__ECC_TV__` (decoder.cpp:1840) 안에 있고 `__ECC_TV__`는 `__PROGRAM_MODE_REF_C__`가 꺼졌을 때만 정의됨 (mode.h:35-39) | 미컴파일 | AUTO에서는 TV 출력 자체가 없고, TV 빌드에서는 `ITER_MAX_HBF`가 이미 4라 변화 없음 | 예 |

---

## 3. 손으로 따진 동작 변화

### 3.1 `decoder.cpp:6454` skip 시점

`if ((mn == 4 + ITER_MAX_HBF) || (mn == 3 + ITER_MAX_HBF))`가 mn 3, 4에서 mn 7, 8로 옮겨진다. 옮겨진 값이 비AUTO 원본과 같으므로 방향은 맞다. `__RUN_ITER34_HIGH_DV_SKIP__`가 꺼져 있어 지금 빌드에서는 미컴파일이다.

### 3.2 PCRC(Partial CRC) 종료 시점

[decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp)의 `if (((mn == 1) || (mn == ITER_MAX_HBF + 1)))`이 유일하게 **AUTO 빌드에서 살아 있는 표 밖 히트**다. `__DUAL_UPDATE__`가 mode.h:64에서 켜져 있다.

- ㉮ 지금(`ITER_MAX_HBF` = 0): 두 항이 모두 `mn == 1`이라 mn 1에서만 마지막 termination point 제한이 걸린다
- ㉯ 4로 바꾼 뒤: mn 1과 mn 5 두 곳에서 걸린다. mn 5는 BF 미진입 프레임의 첫 iteration이므로 `stop_by_partial_crc`가 `idxTermination[3]`에서만 서게 된다
- ㉰ 결과: `out_last_column`, `stop_by_partial_crc`, `overall_clk`이 바뀐다. `overall_clk`은 throughput 지표이고 이번 변경의 목적이 throughput 최적화이므로 측정값에 직접 걸린다

방향은 비AUTO 원본과 같아 **동작 자체는 옳다**. 문제는 문서가 이 변화를 예고하지 않아, 3단계와 5단계 사이 결과 비교(code_diff 9장)에서 원인을 찾지 못하게 된다는 점이다.

### 3.3 TV 출력 시점 (변경 금지 대상 확인)

TV 출력 hex 포맷은 변경 금지 대상이다. 확인 결과 **포맷도 시점도 걸리지 않는다**.

- ㉮ `Print_TV_*` 호출부는 [decoder.cpp:1840](../../../../../../0_LDPC_original/src/decoder.cpp)에서 시작하는 `#if defined (__ECC_TV__)` 안에 있다
- ㉯ `__ECC_TV__`는 [mode.h:35-39](../../../../../../0_LDPC_original/src/mode.h)의 `#else` 갈래, 곧 `__PROGRAM_MODE_REF_C__`가 꺼졌을 때만 정의된다
- ㉰ `__AUTO_LLR_OPT__`는 [mode.h:21-22](../../../../../../0_LDPC_original/src/mode.h)에서 `__PROGRAM_MODE_REF_C__`가 켜졌을 때만 정의된다
- ㉱ 두 스위치는 함께 켜질 수 없다. AUTO 빌드에 TV 출력이 없고, TV 빌드에서 `ITER_MAX_HBF`는 이미 4다

### 3.4 `MN_size` 17곳이 불변인 이유

세 값이 함께 움직여 상쇄된다.

- ㉮ [local_opt.cpp:126](../../../../../../0_LDPC_original/src/local_opt.cpp)이 `MN[MN_num-1]`을 `ITER_MAX_HBF`만큼 줄인다. 4로 바꾸면 124에서 120이 된다
- ㉯ `MN_size = MN[MN_num-1] + ITER_MAX_HBF + 1`이므로 지금 `124 + 0 + 1 = 125`, 바꾼 뒤 `120 + 4 + 1 = 125`로 같다
- ㉰ [decoder.cpp:564](../../../../../../0_LDPC_original/src/decoder.cpp)의 `MN_max = MN[MN_num-1] + ITER_MAX_HBF`도 `124 + 0`에서 `120 + 4`로 124 그대로다
- ㉱ 루프 상한도 맞다. BF 미진입 프레임은 `Select_BF`가 `MN`에 4를 더해 mn 124까지 돌고, 진입 프레임은 mn 120까지 돈다. 둘 다 index 124 미만이라 로그 배열을 넘지 않는다

따라서 17곳과 564는 표에 없어도 결함이 아니다.

---

## 4. 발견

### F1 (HIGH, 수정 후 코드의 결함) `local_opt.cpp:124-131`이 `MN[]`에 음수를 만들어 FER 표가 깨진다

**근거**: [local_opt.cpp:118-131](../../../../../../0_LDPC_original/src/local_opt.cpp), [ecc_top.cpp:877-881](../../../../../../0_LDPC_original/src/ecc_top.cpp), [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp)

118-122가 `MN[i] = i`로 채우고, 124-131이 HD에서 전 원소에 `-= ITER_MAX_HBF`를 건 뒤 `MN[0]`만 `ITER_MAX_HBF`로 되돌린다.

- ㉮ 지금(0): `MN[0] = 0`, `MN[i] = i`, `MN[123] = 124`. 오름차순이고 모두 0 이상이다
- ㉯ 4로 바꾼 뒤: `MN[0] = 4`, `MN[1] = -3`, `MN[2] = -2`, `MN[3] = -1`, `MN[4] = 0`, `MN[i] = i - 4`, `MN[123] = 120`
- ㉰ [ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `if (o_iter_num > m_param_dec->MN[n]) fr_4KB[n]++`는 `o_iter_num`이 항상 0 이상이므로 n = 1, 2, 3에서 **모든 프레임을 센다**. 세 FER 칸이 1.0으로 고정된다
- ㉱ `MN[0] = 4`가 `MN[1] = -3`보다 커서 FER 곡선이 단조롭지 않게 된다
- ㉲ [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp)이 결과 파일 머리글에 `4 -3 -2 -1 0 1 2 ...`를 찍는다. DAO가 이 머리글로 iteration별 FER 칸을 짚으므로 DAO 쪽 해석도 어긋난다 (팀 P 관점 16과 겹침)

비AUTO 빌드에서는 `MN[]`이 [main.cpp:719-723](../../../../../../0_LDPC_original/src/main.cpp)에서 다섯 개의 실제 iteration 상한으로 채워지므로 음수가 나오지 않는다. 즉 이 결함은 AUTO 경로의 항등 채우기(118-122)와 보정(124-131)이 겹쳐야만 생기고, `ITER_MAX_HBF`가 0이라 지금까지 잠자고 있었다.

**문서 상태**: 5.5장 표에 `local_opt.cpp:126-130`이 "딸린 곳"으로 올라 있으나 결과가 어떻게 되는지는 적혀 있지 않다. [code_diff.md 3.5](../../code_diff.md#ch3)은 116-123만 다시 쓰고 124-131은 손대지 않는다. 9장 5단계에도 이 변화가 없다.

**처방**: 보정식을 `MN[i] = (i > ITER_MAX_HBF) ? (i - ITER_MAX_HBF) : 0` 꼴로 바꾸거나, 항등 채우기 자체를 iteration 번호 체계에 맞게 다시 설계한다. **코드 동작 변경을 요구한다** (관점 7과 함께 결정해야 함).

### F2 (MEDIUM, 문서 누락) 표 밖에 실행되는 히트가 하나 있다: `decoder.cpp:2169`

**근거**: [decoder.cpp:2168-2176](../../../../../../0_LDPC_original/src/decoder.cpp), [mode.h:64](../../../../../../0_LDPC_original/src/mode.h)

3.2절에 적은 대로 `__DUAL_UPDATE__`가 켜져 있어 AUTO 빌드에서 컴파일되고 실행된다. `ITER_MAX_HBF`를 4로 바꾸면 PCRC 조기 종료 가능 지점이 mn 5에서 좁아지고 `overall_clk`이 바뀐다. 5.5장 표에 없다.

**처방**: 5.5장 표에 `decoder.cpp:2169`(그리고 짝인 2190)를 "PCRC 종료 제한 iteration"으로 추가하고, 9장 5단계 기대 결과에 "throughput 수치가 바뀐다"를 적는다. **코드 변경은 필요 없다** (동작 자체는 비AUTO 원본과 같음).

### F3 (MEDIUM, 문서 누락) 같은 스위치 안의 형제 히트 넷이 빠졌다: 1448, 1622, 1821, 1828

**근거**: [decoder.cpp:1446-1448](../../../../../../0_LDPC_original/src/decoder.cpp) (`__RUN_PARITY_SKIP__`), [1620-1622](../../../../../../0_LDPC_original/src/decoder.cpp), [1814-1828](../../../../../../0_LDPC_original/src/decoder.cpp) (1821은 `__RUN_PREPROCESSING__`, 1828은 `__RUN_PARITY_SKIP__`)

표는 `__RUN_PREPROCESSING__` 갈래에서 1149, 2310, 3487을 잡았는데 같은 스위치 안의 1821(클럭 가산 시점)만 빠졌다. 표의 기준이 스위치별로 일관되지 않다. `__RUN_PARITY_SKIP__` 세 곳(1448, 1622, 1828)은 통째로 빠졌다.

지금 mode.h에서 두 스위치가 모두 꺼져 있어 당장은 무해하다. 다만 이 문서는 "코드 수정 계획"이고 사용자가 외부 환경에서 스위치 조합을 달리 잡을 수 있으므로, 전수 목록을 표방하는 표에서는 빠지면 안 된다.

**처방**: 5.5장 표에 네 줄을 추가하고 각 줄에 감싸는 스위치를 함께 적는다. **코드 변경은 필요 없다**.

### F4 (MEDIUM, 문서 서술 오류) code_diff 8.1의 edge clear 설명이 코드와 다르다

**근거**: [code_diff.md 8.1](../../code_diff.md#ch8) 끝줄 "BF에 진입하면 1에서, 진입하지 않으면 5에서 걸린다" 대 [decoder.cpp:6542-6547](../../../../../../0_LDPC_original/src/decoder.cpp)

조건은 `iter == 0 || iter == 1 || iter == ITER_MAX_HBF + 1`이고 `flag_BF_on`을 보지 않는다. 그러므로 BF 진입 프레임은 iteration 0, 1, **그리고 5** 세 곳에서 모두 edge clear를 한다. 미진입 프레임은 iteration 5부터 시작하므로 0과 1을 지나지 않아 5에서만 걸린다.

바로 앞줄 "`ITER_MAX_HBF`가 4로 돌아가므로 `iter == 1`과 `iter == 5` 두 지점에서 edge clear가 일어난다"는 맞다. 뒤이은 한 줄이 이를 "둘 중 하나"로 잘못 좁혔다. 코드는 비AUTO 원본([decoder.cpp:6569-6573](../../../../../../0_LDPC_original/src/decoder.cpp))과 같아 옳고, **틀린 것은 문장뿐이다**. 이 문장을 그대로 믿고 `flag_BF_on` 조건을 덧붙이면 비AUTO 빌드와 결과가 갈린다.

**처방**: "BF 진입 프레임은 1과 5 두 곳에서, 미진입 프레임은 5 한 곳에서 걸린다"로 다시 쓴다. **코드 변경은 필요 없다**.

### F5 (MEDIUM, 문서 서술 오류) "12곳" 셈법이 표와도 소스와도 맞지 않는다

**근거**: [code_diff.md 1.2](../../code_diff.md#ch1_2) 77줄 "이 상수를 쓰는 12곳(상위 문서 5.5장 표)", [상위 문서 5.5](../../20260902_SW_branch_LLR_matrix.md)

- ㉮ 표는 **11행**이고, 행 안의 위치를 풀면 **13곳**이다. 12는 어느 셈법으로도 나오지 않는다
- ㉯ 소스의 실제 코드 히트는 decoder.cpp 41곳, local_opt.cpp 2곳, main.cpp 1곳, TV_Dec_Inter.cpp 5곳으로 모두 49곳이다
- ㉰ "이 상수를 쓰는 곳"이라는 표현이 "값이 바뀌면 동작이 달라지는 곳"을 뜻한다면 17곳의 `MN_size`와 564는 3.4절대로 불변이므로 빠지는 것이 맞다. 그 기준을 문서가 밝히지 않아 독자가 전수인지 선별인지 알 수 없다

**처방**: 수를 13으로 고치고, 표 머리에 "값이 바뀌면 동작이 달라지는 곳만 싣는다. `MN_size` 계열 17곳과 564는 보정과 상쇄되어 불변이다"라는 선별 기준을 적는다. **코드 변경은 필요 없다**.

### F6 (MEDIUM, 수정 후 코드의 결함) `__PRINT_LOG_DATA__`를 켜면 histogram 배열이 넘친다

**근거**: [ecc_top.cpp:2760](../../../../../../0_LDPC_original/src/ecc_top.cpp) `size_histogram = MN[MN_num-1] * 4`, [ecc_top.cpp:2808-2809](../../../../../../0_LDPC_original/src/ecc_top.cpp) `idx = (iter - 1) * 4 + pcrc`

`Alloc_Log_Data`는 스위치 없이 늘 할당한다. `MN[MN_num-1]`이 124에서 120으로 줄면 크기가 496에서 480으로 줄지만, `iter`는 BF 미진입 프레임에서 여전히 124까지 올라가므로 `idx`는 495까지 간다. 지금은 496과 495로 딱 맞아떨어져 넘지 않는다.

`Update_Log_Iter_Histogram`이 `__PRINT_LOG_DATA__`(mode.h:31, 꺼짐)로 감싸여 있어 현재 조합에서는 발생하지 않는다. 스위치를 켜면 힙 15칸을 넘겨 쓴다.

**처방**: `size_histogram`을 `(MN[MN_num-1] + ITER_MAX_HBF) * 4`로 맞춘다. **코드 동작 변경을 요구한다** (할당 크기만 바뀌므로 결과에는 영향 없음).

### F7 (LOW, 문서 서술 정확성) `iter <= 4` 상수는 네 곳이 맞으나 다섯째가 따로 있다

**근거**: grep 결과 `iter <= 4`는 [decoder.cpp:2375, 2798, 4056, 4275](../../../../../../0_LDPC_original/src/decoder.cpp)와 [decoder.cpp:7005](../../../../../../0_LDPC_original/src/decoder.cpp) 다섯 곳이다.

- ㉮ 앞 네 곳은 모두 `#ifdef __AUTO_LLR_OPT__` 안이고 [code_diff.md 7장](../../code_diff.md#ch7)의 줄 범위(2373-2379, 2796-2802, 4055-4059, 4274-4278)와 일치한다. 5.5장 둘째 표의 줄 범위(2374-2378, 2797-2801)는 7장과 한 줄씩 다르나 가리키는 곳은 같다
- ㉯ 다섯째 7005는 `#else`(비AUTO) 그룹 선택의 `(iter >= 2) && (iter <= 4)`다. 5.5장 둘째 표에는 없지만 [상위 문서 5.3-4](../../20260902_SW_branch_LLR_matrix.md)가 하드코딩을 걷어내는 대상으로 따로 다루고, code_diff 6.1이 실제로 지운다. 누락이 아니다
- ㉰ `mn <= 4`, `MN == 4` 같은 다른 형태의 BF 구간 길이 하드코딩은 grep으로 찾지 못했다. 6454와 TV_Dec_Inter의 `4 + ITER_MAX_HBF`, `3 + ITER_MAX_HBF`는 BF 구간 길이가 아니라 정상 복호 3, 4번째 iteration을 가리키는 오프셋이다

**처방**: 5.5장 둘째 표의 서술을 "`__AUTO_LLR_OPT__` 갈래 안의 네 곳"으로 한정해 7005와 구별한다. **코드 변경은 필요 없다**.

### F8 (LOW, 확인 결과) BF 진입 프레임과 미진입 프레임의 iteration 예산이 4만큼 다르다

**근거**: [decoder.cpp:1118-1120](../../../../../../0_LDPC_original/src/decoder.cpp), [decoder.cpp:2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp), [local_opt.cpp:126](../../../../../../0_LDPC_original/src/local_opt.cpp)

`MN = MN[MN_num-1]`은 120이고, `Select_BF`가 미진입 프레임에만 4를 더한다. 그러므로 미진입 프레임은 mn 5부터 124까지, 진입 프레임은 mn 1부터 120까지 돈다. 진입 프레임은 파일이 정의한 iteration 121~124의 row에 닿지 않는다.

비AUTO 원본도 같은 구조이므로 새로 생기는 문제는 아니다. 다만 `msg1.md`가 "bf를 타면 iteration 0,1,2,3,4,5,6,7.. 안 타면 0,5,6,7.."이라고만 적어 두 갈래가 같은 번호에서 끝나는 것처럼 읽힌다. 두 문서 어디에도 이 4 차이가 적혀 있지 않다.

**처방**: 5.5장에 "BF 진입 프레임은 iteration 120까지, 미진입 프레임은 124까지 돈다"를 한 줄 적는다. 예산을 맞추는 것이 의도라면 관점 7과 함께 결정해야 한다. **문서에 적는 것만으로는 코드 변경을 요구하지 않는다**.

---

## 5. 요약

| 심각도 | 건수 | 항목 |
|--------|------|------|
| CRITICAL | 0 | 없음 |
| HIGH | 1 | F1 |
| MEDIUM | 4 | F2, F3, F4, F6 |
| LOW | 2 | F7, F8 |

수정 후 코드의 결함 2건(F1, F6), 문서 서술의 오류나 누락 5건(F2, F3, F4, F5, F7), 확인 결과 1건(F8)이다. F5는 셈법 오류라 MEDIUM 표에서는 F2~F4, F6과 함께 문서 오류로 묶었다 (총 MEDIUM 5건: F2, F3, F4, F5, F6).

**문제 없음으로 판정한 범위**: `MN_size` 계열 17곳과 `decoder.cpp:564`(3.4절에서 불변임을 증명), `main.cpp:719`(AUTO에서 미컴파일, 비AUTO에서 값 불변), `TV_Dec_Inter.cpp` 다섯 곳(AUTO와 TV 빌드가 배타적이라 TV 출력 hex 포맷과 시점 모두 영향 없음), `decoder.cpp` 둘째 표의 `#else` 반쪽 네 곳(2377, 2800, 4058, 4277).
