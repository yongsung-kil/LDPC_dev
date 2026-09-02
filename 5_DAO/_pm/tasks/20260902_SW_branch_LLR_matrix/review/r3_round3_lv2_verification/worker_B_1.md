# Round 3 팀 B 재탐색 워커 1 결과

작성: 2026-09-03 01:44:35

담당 영역 두 가지.

- ㉮ [mode.h](../../../../../../0_LDPC_original/src/mode.h)에서 켜져 있는 스위치 다섯 개와 수정 후 코드의 맞물림
- ㉯ [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp)의 `Get_VNU_LLR_SET_FILE` 경로와 새 파일 치수

읽은 범위는 문서 맨 끝 "확인한 범위"에 적었다.

---

## 1. 스위치 다섯 개: 전수 히트 목록과 판정

### 1.1 `__RUN_PUNCT_RECOVERY__` (mode.h:61, 켜짐)

히트 목록.

- 정의: [mode.h:61](../../../../../../0_LDPC_original/src/mode.h)
- decoder.cpp:1158 (`/* */` 주석 블록 1157-1395 안, 죽은 코드)
- decoder.cpp:3013-3215 (살아있음. 바깥 조건이 `if (iter == 0)` decoder.cpp:3011)
- decoder.cpp:3219-3374 (`/* */` 주석 블록 안, 죽은 코드. 3217행 "Col_Blk 0, 1일 때 version" 아래)
- decoder.cpp:3577, 3586, 3611, 3641, 3652, 3672 (`VN_Cal_Pre`, decoder.cpp:3554)
- decoder.cpp:3802, 3811, 3861, 3872 (`VN_Cal_Pre_HCU`, decoder.cpp:3760)
- ecc_top.cpp:83 (punct 배열 해제), ecc_top.cpp:328 (punct 배열 할당)

판정: **맞물림 없음**.

- ㉮ 살아있는 본체는 `if (iter == 0)` 하나로 묶여 있다 (decoder.cpp:3011). `Select_BF`는 mn 0의 몸통 끝(decoder.cpp:1968-1970)에서 불리므로 punct recovery는 mn 도약 전에 이미 끝난다
- ㉯ `VN_Cal_Pre`와 `VN_Cal_Pre_HCU`의 punct 갈래는 iteration 번호를 보지 않는다. 이 두 함수는 `Is_Iter_Type_Init(mn)`이 TRUE일 때만 불리고(decoder.cpp:5699-5701, 5738-5740), AUTO의 HD와 1.5SD에서 그 조건은 `iter == 0`뿐이다(decoder.cpp:6606-6626). `ITER_MAX_HBF`가 4가 되어도 mn 0은 그대로 돈다
- ㉰ `ITER_MAX_HBF`, `flag_BF_on`, `mn`, `MN`, `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `iter <= 4`, `v_deg`, `DV_5` 중 어느 것도 이 스위치의 가드 안에 나타나지 않는다

### 1.2 `__SHUFFLED_DUAL_DIAG__` (mode.h:65, 켜짐)

히트 목록: [mode.h:65](../../../../../../0_LDPC_original/src/mode.h), encoder.cpp:60, encoder.cpp:87. 그것이 전부다.

판정: **맞물림 없음**. 두 곳 모두 `Encoder::LDPC_encoder_4KB`의 지역 변수 `shuffled_dual_diag`를 TRUE로 세우는 것뿐이고, 복호기와 LLR matrix에 닿지 않는다.

### 1.3 `__PMU_READ__` (mode.h:66, 켜짐)

히트 목록.

- 정의: [mode.h:66](../../../../../../0_LDPC_original/src/mode.h)
- decoder.cpp:593-597 (`printf("* PMU Read : on")`. 바깥이 `#ifdef __WIN_OS__` + `#ifndef __AUTO_LLR_OPT__`이므로 AUTO 빌드에서는 죽어 있다)
- decoder.cpp:1413-1437 (clock 루프 안의 `PMU_Read` 배차)

판정: **맞물림 없음**. iteration별 전력 계수를 배열 index로 잡지 않는다.

- ㉮ `PMU_SRAM`은 column 축으로만 색인된다. `PMU_SRAM[jj][offset]`, `PMU_SRAM[jj + punct_col_num][offset]`(decoder.cpp:5836-5865), `PMU_SRAM[jj + 2*(jj - HCU_start) + current_G_idx][offset]`(decoder.cpp:6071, 6170). 크기는 `new int*[N_b + punct_col_num]`(decoder.cpp:179-180)이고 `offset = n * PMU_UNIT_WIDTH`로 edge 축이다. iteration 축이 없다
- ㉯ `FIFO_level`, `MAIN_SRAM_read_rq`, `MAIN_SRAM_write_rq`도 `factor * MAX_DV_GLOBAL_HALF` 크기의 edge 축 배열이다(decoder.cpp:181-184, 6470-6474, 6518-6522)
- ㉰ `PMU_Read_HCU`(decoder.cpp:6055)와 `PMU_Write_HCU`(decoder.cpp:6122)는 `current_G_idx = (G_idx + mn) % 2`로 mn 패리티를 쓴다. 아래 1.4 ㉰의 패리티 논증이 그대로 적용되어 값이 바뀌지 않는다

### 1.4 `__HALF_COL_UPDATE__`(mode.h:68)와 `__HALF_COL_MODIFIED__`(mode.h:70), 둘 다 켜짐

히트 목록 (`__HALF_COL_UPDATE__`).

- 정의: mode.h:68, 69, 71
- decoder.cpp: 96, 175, 229, 246, 339, 395, 773, 814, 1095, 1422, 1485, 1526, 1544, 1567, 1592, 1632, 1654, 1675, 1763, 1877, 1886, 1893, 1899, 2478, 2868, 2882, 2890, 2946, 2954, 2962, 2970, 2979, 2985, 5776, 5811, 5833, 5850, 5888, 5927, 5948, 5983, 6241, 6351, 6378, 6470, 6518
- decoder.h:392
- TV_Dec_Inter.h: 40, 106, 153
- TV_Dec_Inter.cpp: 42, 115, 131, 148, 176, 193, 222, 239, 269, 342, 362, 402, 447, 1130, 1377, 1611

히트 목록 (`__HALF_COL_MODIFIED__`): mode.h:70, common.h:378, common.h:383 (`HCU_COL_1_IDX` 127, `HCU_COL_2_IDX` 128, `SEPARATE_V_DEG_1` 9, `SEPARATE_V_DEG_2` 7), decoder.cpp:2482, decoder.cpp:2562.

판정: **1bit precision 조건과 겹친다. 다만 code_diff 7장이 그 겹침을 이미 덮고 있고, mn 도약이 패리티를 보존하므로 결함은 아니다.** 근거 셋.

- ㉮ VN 갱신 경로는 HCU 여부로 갈린다. `V2C_Cal`(decoder.cpp:5691)이 비HCU column을 `VN_Cal_HD`(decoder.cpp:3973)로 보내고, `V2C_Cal_HCU`(decoder.cpp:5731)가 column 127, 128을 `VN_Cal_HD_HCU`(decoder.cpp:4136)로 보낸다. 배차는 decoder.cpp:1526-1534 (`col_P2 >= HCU_start && col_P2 < HCU_end + 1`)
- ㉯ 1bit precision 조건은 두 함수에 각각 하나씩 있다. decoder.cpp:4056(`VN_Cal_HD`)과 decoder.cpp:4275(`VN_Cal_HD_HCU`). 두 곳 모두 `(TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)`이고 `v_deg`는 `m_PCM->ColW[jj]`(전체 column 차수)다. `DV_5`는 5(common.h:295). HCU column의 반쪽 차수가 9와 7(common.h:381-382)이므로 전체 차수는 확실히 5를 넘고, BF를 살리면 HCU column도 1bit precision을 탄다. code_diff 7.3이 이 두 곳을 함께 다루므로 누락은 없다
- ㉰ HCU 그룹 교번은 `(G_idx + mn) % 2` 또는 `(G_idx + iter) % 2`(iter 인자에 mn이 그대로 들어간다, decoder.cpp:5704, 5744)로 계산되며 여덟 곳 모두 같은 식이다. decoder.cpp:2481, 2601, 2648, 3777, 4157, 4670, 6055, 6122. `ITER_MAX_HBF`가 짝수 4이므로 `Select_BF`의 `mn = mn + ITER_MAX_HBF`(decoder.cpp:2097)가 만드는 mn 수열 0, 5, 6, 7, ...은 지금의 0, 1, 2, 3, ...과 패리티가 같다. `Sum_t_OLD_G0`, `Sum_t_OLD_G1`(decoder.cpp:4235-4248)의 반쪽 누적도 바로 앞 실행 iteration에서 이어받으므로 도약 전후가 같다

한 가지 덧붙일 사실. `MN`은 포인터가 아니라 `int` 스칼라다([decoder.h:328](../../../../../../0_LDPC_original/src/decoder.h)). 본문 루프에서 `MN = m_param_dec->MN[m_param_dec->MN_num - 1]`(decoder.cpp:1118)로 최대 iteration 값을 받고, `MN = MN + ITER_MAX_HBF`(decoder.cpp:2098)는 루프 상한을 4 늘린다. 과업 지시문의 "`mn`, `MN` 포인터 이동"이라는 표현은 실제 코드와 맞지 않는다.

---

## 2. 영역 ㉮에서 나온 발견

### B1-1 (MEDIUM, 문서 서술 오류) 5.5, 5.6 표의 `ITER_MAX_HBF` 소비처 세 항목은 어느 빌드에도 들어가지 않는다

가설: 상위 문서 5.5장 표와 5.6장 표가 "`ITER_MAX_HBF`를 4로 되돌리면 딸려 온다"고 든 위치 중 셋은 mode.h에서 꺼진 스위치 안이라 컴파일되지 않는다.

증거 (확인됨).

- ㉮ decoder.cpp:1146이 `#if defined (__RUN_PREPROCESSING__)`이고, `Preprocessing()` 호출과 decoder.cpp:1149의 `mn == ITER_MAX_HBF + 1` 조건이 통째로 그 안에 있다. [mode.h:63](../../../../../../0_LDPC_original/src/mode.h)은 `//#define __RUN_PREPROCESSING__`으로 주석이며, `__PROGRAM_MODE_REF_C__` 여부와 무관한 위치다. 두 빌드 모두 `Preprocessing()`을 실행하지 않는다
- ㉯ decoder.cpp:2310과 decoder.cpp:3487(5.5 표의 "Preprocessing column read 표시")도 각각 decoder.cpp:2303, decoder.cpp:3480의 `#if defined (__RUN_PREPROCESSING__)` 안이다
- ㉰ decoder.cpp:6454(5.5 표의 "특정 iteration 판정")는 decoder.cpp:6450의 `#if defined (__RUN_ITER34_HIGH_DV_SKIP__)` 안이고 [mode.h:78](../../../../../../0_LDPC_original/src/mode.h)이 주석이다
- ㉱ code_diff 8.3장은 decoder.cpp:1146-1156을 "수정 전후 모두 그대로 둔다. `flag_BF_on`이 살아나면 조건이 저절로 맞는다"고 적는다. 조건은 맞아도 블록이 컴파일되지 않으므로 Preprocessing은 여전히 일어나지 않는다

처방: 5.5 표와 5.6 표, code_diff 8.3에 이 세 곳이 꺼진 스위치 안임을 적고, BF 부활의 효과 목록에서 Preprocessing을 뺀다. 코드 삭제나 동작 변경을 요구하지 않는다.

### B1-2 (MEDIUM, 문서 누락) 5.5 표에 빠진 살아있는 `ITER_MAX_HBF` 소비처

가설: 5.5장 표가 12곳을 든다고 하지만, AUTO 빌드에서 실제로 컴파일되는 소비처가 표 밖에 더 있다.

증거 (확인됨). 전수 grep(`ITER_MAX_HBF`, 소스 전체) 결과 중 표에 없고 살아있는 것.

- ㉮ **decoder.cpp:2169** (`Cal_PCRC`, 함수 시작 decoder.cpp:2135). `#if defined(__DUAL_UPDATE__)` 안이고 [mode.h:64](../../../../../../0_LDPC_original/src/mode.h)에서 `__DUAL_UPDATE__`가 켜져 있다. 조건은 `if (((mn == 1) || (mn == ITER_MAX_HBF + 1)))`이고, 참이면 그 iteration에서는 마지막 termination point(`idxTermination[3]`)에서만 partial CRC 조기 종료를 허용한다. 지금 AUTO에서는 `ITER_MAX_HBF`가 0이라 두 항이 mn 1로 겹쳐 한 지점이지만, 4로 바꾸면 mn 1과 mn 5 두 지점이 된다. BF에 진입한 프레임은 iteration 1과 5 양쪽에서 종료 제한을 받는다. `MODE_CRC_PARTIAL`을 쓰는 실행에서 종료 시점이 달라진다
- ㉯ decoder.cpp:2190은 같은 조건의 `#else` 갈래(`__DUAL_UPDATE__` 미정의)라 죽어 있다
- ㉰ 로그 배열 크기 계산 `MN_size = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF + 1`이 열다섯 곳에 있다. decoder.cpp:7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018. 5.5 표는 decoder.cpp:7583 하나만 든다. 이 중 decoder.cpp:7931(`Print_Log_CSW_Auto`)은 `#ifdef __AUTO_LLR_OPT__` 전용이고, 배열 `m_log_CSW_auto`는 decoder.cpp:7774에서 같은 `MN_size`로 잡히며 decoder.cpp:1919에서 `m_log_CSW_auto[mn]`으로 쓰인다

경계 검산 (넘치지 않음을 확인했다). code_diff 3.5를 적용하면 `MN_num = max_iter_end = 124`, `MN[123] = 124`, 나머지 `MN[i] = i`. 이어서 local_opt.cpp:124-131이 전 원소에서 4를 빼므로 `MN[123] = 120`. 따라서 `MN_size = 120 + 4 + 1 = 125`.

- BF 진입 프레임: 루프 상한 `MN = 120`, mn 최대 120. `m_log_CSW_auto[120]` 안전
- BF 미진입 프레임: `Select_BF`가 `MN`을 124로 올리므로 mn 최대 124. `m_log_CSW_auto[124]`는 크기 125의 마지막 칸이다. 안전
- `crc_dec_LFSR_iter`(decoder.cpp:565, 크기 `MN_max * CRC_LEN`, `MN_max = 120 + 4 = 124`)도 `real_mn - 1` 색인(decoder.cpp:5315)의 최대가 119라 안전

처방: 5.5 표에 decoder.cpp:2169와 로그 배열 크기 계산 열다섯 곳을 넣고, decoder.cpp:2169가 partial CRC 조기 종료 시점을 바꾼다는 것을 적는다. 배열 경계는 문제가 없으므로 코드 변경은 필요 없다.

### B1-3 (MEDIUM, 문서 서술 오류) code_diff 8.1의 "BF에 진입하면 1에서, 진입하지 않으면 5에서 걸린다"가 사실과 다르다

가설: BF에 진입한 프레임도 iteration 5에서 edge clear를 맞는다.

증거 (확인됨).

- ㉮ `Is_Iter_Type_Edge_Clear`(decoder.cpp:6538)는 `flag_BF_on`을 전혀 보지 않는다. HD와 1.5SD 갈래의 조건은 `iter == 0 || iter == 1 || iter == ITER_MAX_HBF + 1`(decoder.cpp:6543-6545)로 셋을 OR한 것이다
- ㉯ `ITER_MAX_HBF`가 4가 되면 이 집합은 {0, 1, 5}가 된다. BF에 진입한 프레임은 mn을 0, 1, 2, 3, 4, 5, ...로 돌므로 0, 1, 5 세 지점 모두에 걸린다. BF에 진입하지 않은 프레임은 mn을 0, 5, 6, ...로 돌아 1을 건너뛰므로 0과 5에 걸린다
- ㉰ 이때 `Clear_Edge_Restart`(decoder.cpp:709-724)가 `Clear_REG_min_pos`, `Clear_REG_min_value`, `Clear_CN_REG(IDX_CHECK_SUM)`, `Clear_Edge_SRAM_Sgn`, `Clear_PMU`, `Clear_Sum_t_OLD`를 모두 부른다. 즉 BF 프레임은 iteration 1에서 4까지 1bit precision으로 쌓은 edge를 iteration 5에서 통째로 지우고 다시 시작한다
- ㉱ 이 동작 자체는 비AUTO 원본과 같다(비AUTO는 이미 `ITER_MAX_HBF`가 4다). 코드 결함이 아니라 문서 서술의 오류다

처방: code_diff 8.1의 설명 문장을 "iteration 0, 1, 5 세 지점에서 edge clear가 일어난다. BF에 진입하지 않은 프레임은 iteration 1을 돌지 않으므로 0과 5에서만 걸린다"로 다시 쓴다. 코드 변경을 요구하지 않는다.

### B1-4 (MEDIUM, 계획이 놓친 결과 변화) BF를 살리면 iteration 1에서 4의 문턱 파라미터 일부가 무효가 된다

가설: BF에 진입한 프레임에서, iteration 1에서 4 동안 차수가 5를 넘는 column은 파일에서 읽은 `th1`, `th2`, `th3`를 쓰지 않는다. 그 파라미터를 담은 row가 DAO의 탐색 대상에서 사실상 don't care가 된다.

증거 (확인됨).

- ㉮ decoder.cpp:4056과 decoder.cpp:4275의 1bit precision 갈래는 `temp`를 `±EDGE_MAG_7`로 고정하고 `th1`, `th2`, `th3`를 쓰지 않는다(decoder.cpp:4060-4079, 4279-4297). 이 갈래는 `flag_BF_on`이 TRUE이고 `iter <= 4`이고 `v_deg > DV_5`일 때 탄다
- ㉯ `ch1`(channel LLR)은 decoder.cpp:4019에서 여전히 쓰인다. 무효가 되는 것은 문턱 세 개뿐이다
- ㉰ `Get_VNU_LLR_SET_FILE`이 `th1`, `th2`, `th3`를 row의 `table_col_idx + 1, +2, +3`에서 읽는다(decoder.cpp:7093-7095). `table_col_idx = i * num_para_each_set`이고 `num_para_each_set`이 4이므로, 차수 11 그룹(i = 0)에서는 row의 1, 2, 3번 칸이다
- ㉱ 새 파일의 dv 그룹은 `dv_from` = `dv_to` = {11, 4, 3, 2}다([LLR_MATRIX_1.txt](../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 5행과 6행). 차수가 5를 넘는 것은 11 그룹뿐이고, 아래 B1-6에서 보듯 어느 그룹에도 걸리지 않는 차수는 조용히 그룹 0(즉 11 그룹)으로 떨어진다. 그러므로 무효가 되는 것은 row의 1, 2, 3번 칸이다
- ㉲ 분기가 걸린 구간의 row는 그룹 0, 1, 2로 14개다(1 + 7 + 6). 즉 14 * 3 = 42개 파라미터가 BF 진입 프레임에서 don't care가 된다
- ㉳ 두 문서 어디에도 이 결과가 적혀 있지 않다. 상위 문서 5.5장은 네 곳이 "BF를 살리면 살아난다"고만 적는다

처방: 상위 문서 5.5장 아래에 이 결과를 적는다. DAO가 iteration 1에서 4 구간 row의 문턱을 탐색해도 BF 진입 프레임에는 반영되지 않는다는 사실이 최적화 설계에 필요하다. 코드 변경을 요구하지 않는다.

### B1-5 (MEDIUM, 문서 서술 오류) code_diff 3.7의 MPI 전파는 이 저장소에서 컴파일될 수 없는 갈래다

가설: `__RUN_MPI__`는 저장소의 mode.h로는 정의될 수 없고, 링크할 MPI 구현도 없다.

증거 (확인됨).

- ㉮ [mode.h:10](../../../../../../0_LDPC_original/src/mode.h)의 `//#define __RUN_MPI__`는 주석이다
- ㉯ mode.h:21-26의 나머지 정의 자리는 `#ifdef __PROGRAM_MODE_REF_C__` 안에서 `#define __AUTO_LLR_OPT__`(22행) **바로 다음에** `#if !defined(__AUTO_LLR_OPT__)`(23행)를 두고 그 안에서 `__RUN_MPI__`를 정의한다(24행). 앞 줄에서 방금 정의했으므로 이 조건은 항상 거짓이고 `__RUN_MPI__`는 결코 정의되지 않는다
- ㉰ [mpi.cpp](../../../../../../0_LDPC_original/src/mpi.cpp)는 mpi.h를 그대로 복사한 선언만 담고 있고 정의가 하나도 없다. `__RUN_MPI__`를 켜면 `MPI_Bcast`가 미해결 심볼이 된다
- ㉱ 따라서 local_opt.cpp:38-44의 기존 Bcast 블록도, code_diff 3.7이 거기 더하는 네 줄도 이 저장소에서는 들어가지 않는다. code_diff 3.7의 "각 rank가 파일을 따로 읽는 구조라면 이 추가는 필요 없다. 어느 쪽인지 확인한 뒤 맞춘다"는 물음은 이 저장소 안에서 답이 정해져 있지 않다

처방: code_diff 3.7에 `__RUN_MPI__`가 저장소의 mode.h로는 켜지지 않는다는 사실과, 켜는 빌드에서 확인이 필요하다는 것을 적는다. 코드 변경을 요구하지 않는다.

---

## 3. `Get_VNU_LLR_SET_FILE` 경로와 새 파일 치수

### 3.1 파일 헤더와 row 칸 수 (직접 셈)

[LLR_MATRIX_1.txt](../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)를 `fscanf("%d")` 토큰 순서로 읽으면 다음과 같다.

| 순서 | 필드 | 값 | 파일 위치 |
|------|------|-----|----------|
| 1 | `num_para_each_set` | 4 | 1행 |
| 2 | `num_dv` | 4 | 3행 |
| (계산) | `num_col` | 16 (= 4 * 4) | local_opt.cpp:63 |
| 3 | `dv_from[4]` | 11 4 3 2 | 5행 |
| 4 | `dv_to[4]` | 11 4 3 2 | 6행 |
| 5 | `num_group` | 12 | 8행 |
| 6 | `num_set_each_group[12]` | 1 7 6 6 1 5 5 7 6 10 10 13 | 10행 |
| (계산) | `num_row` | 77 | local_opt.cpp:79 |
| 7 | `type_each_group[12]` | 20 20 21 20 21 21 1 1 1 1 1 1 | 11행 |
| 8 | `restart_num` | 0 | 13행 |
| 9 | `restart_iter[]` | 없음 | |
| 10 | `max_value[4]` | 31 31 31 31 | 15행 |
| 11 | `min_value[4]` | 0 0 0 0 | 16행 |
| 12 | row 77개 | 각 20칸 | 18행부터 105행까지 |

row 한 줄의 20칸은 local_opt.cpp:106-115의 읽기 순서와 정확히 맞는다.

- ㉮ 0번에서 15번 칸: `LLR_MATRIX[i][0..15]` (local_opt.cpp:107-110, `num_col`만큼)
- ㉯ 16번 칸: `CSW_thr[i]` (local_opt.cpp:111)
- ㉰ 17번 칸: `iter_start[i]` (local_opt.cpp:112)
- ㉱ 18번 칸: `iter_end[i]` (local_opt.cpp:113)
- ㉲ 19번 칸: `floor_flag[i]`, 문서가 `sw_branch_idx`로 바꾸려는 칸 (local_opt.cpp:114)

그룹별 row 수를 파일에서 직접 세었다. 18행 1개, 20행에서 26행 7개, 28행에서 33행 6개, 35행에서 40행 6개, 42행 1개, 44행에서 48행 5개, 50행에서 54행 5개, 56행에서 62행 7개, 64행에서 69행 6개, 71행에서 80행 10개, 82행에서 91행 10개, 93행에서 105행 13개. 합 77로 `num_set_each_group`의 합과 일치한다. 상위 문서 2장 표(그룹별 헤더 값, 분기 index, row 수, iteration, row 마지막 칸)의 12줄 전부가 파일과 일치했고, 3장 표의 CSW 나열 네 줄도 일치했다.

참고로 구 형태 파일 [LLR_MATRIX_0.txt](../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt)도 `num_para_each_set` 4, `num_dv` 4, row 20칸으로 같다. row 형식은 바뀌지 않았고 바뀐 것은 헤더의 `type_each_group` 줄과 마지막 칸의 뜻뿐이다.

### 3.2 `Get_VNU_LLR_SET_FILE`이 읽는 col 범위

decoder.cpp:7074-7132. `table_col_idx = i * num_para_each_set`(decoder.cpp:7080)이고 i는 `dv`가 `[dv_from[i], dv_to[i]]`에 드는 dv 그룹 번호다. 이 파일에서 `num_para_each_set = 4`, `num_dv = 4`이므로 `table_col_idx`는 0, 4, 8, 12 중 하나다.

| 모드 | 읽는 오프셋 | 마지막 dv 그룹(`table_col_idx` 12)에서의 최대 index | `num_col` 16과 대조 |
|------|-------------|------------------------------------|------------------|
| HD, 1.5SD | +0, +1, +2, +3 (decoder.cpp:7089-7095) | 15 | 안전 (딱 맞음) |
| HD, 1.5SD + `__4_BIT_LLR__` | +0 에서 +7 (decoder.cpp:7096-7101) | 19 | 4칸 초과 |
| 2SD | +0 에서 +4 (decoder.cpp:7104-7110) | 16 | 1칸 초과 |
| 2SD + `__4_BIT_LLR__` | +0 에서 +8 | 20 | 5칸 초과 |
| 3SD | +0 에서 +6 (decoder.cpp:7119-7125) | 18 | 3칸 초과 |
| 3SD + `__4_BIT_LLR__` | +0 에서 +10 | 22 | 7칸 초과 |

`LLR_MATRIX[i]`는 `new int[num_col]`, 즉 16칸이다(local_opt.cpp:101). local_opt.cpp가 채우는 칸 수도 정확히 16이다(local_opt.cpp:107-110). 즉 채우는 칸 수와 읽는 칸 수는 HD와 1.5SD에서 정확히 맞고, 다른 조합에서는 읽는 쪽이 더 많다.

### B1-6 (MEDIUM) dv 그룹에 걸리지 않는 column 차수가 조용히 dv 그룹 0을 쓴다

가설: `dv`가 어느 dv 그룹에도 들지 않으면 `table_col_idx`가 초기값 0으로 남아, 오류 없이 dv 그룹 0(차수 11 그룹)의 파라미터가 쓰인다.

증거 (확인됨).

- ㉮ `table_col_idx`는 함수 앞머리에서 0으로 초기화되고(decoder.cpp:7075) 탐색 반복문(decoder.cpp:7078-7083)은 못 찾아도 오류를 내지 않는다. `Get_Cur_LLR_Idx_FILE`의 `table_row_idx`와 똑같은 형태의 조용한 통과이며, code_diff 6.2가 row 쪽에는 초기값을 -1로 바꾸고 검사를 넣으면서 col 쪽에는 아무것도 넣지 않는다
- ㉯ 이 파일의 dv 그룹은 `dv_from[i] == dv_to[i]`인 단일값 넷, 즉 {11}, {4}, {3}, {2}다. 그 밖의 차수는 모두 걸리지 않는다
- ㉰ `dv`로 넘어가는 값은 매핑 없는 원 column 차수다. `V2C_Cal`이 `VN_Cal_HD(m_PCM->ColW[jj], ...)`(decoder.cpp:5704), `V2C_Cal_HCU`가 `VN_Cal_HD_HCU(m_PCM->ColW[jj], ...)`(decoder.cpp:5744)로 넘기고, 두 함수가 그대로 `Get_VNU_LLR_SET_FILE(v_deg, ...)`에 전달한다(decoder.cpp:3986, 4161)
- ㉱ [common.h:291-293](../../../../../../0_LDPC_original/src/common.h)의 `MAX_DV_GLOBAL` 17, `MAX_DV_GLOBAL_2ND` 13, `MAX_DV_GLOBAL_HALF` 10이 dv 그룹 최대값 11을 넘는다. 차수 12에서 17인 column이 있으면 이 조용한 대체가 일어난다. 이 저장소에는 해당 H-matrix가 없어 실제로 그런 차수가 쓰이는지는 미확인이다

심각도: 실제 차수 분포에 따라 갈리므로 MEDIUM. 처방: code_diff 3장의 파서 검사에 "모든 column 차수가 어느 dv 그룹에 드는가"를 넣기는 어렵다(파서는 H-matrix를 모른다). 대신 `Get_VNU_LLR_SET_FILE`의 탐색 반복문 뒤에 못 찾은 경우의 오류 출력을 넣는 것이 맞다. 코드 추가를 요구한다.

### B1-7 (MEDIUM) 2SD, 3SD 모드로 AUTO 빌드를 돌리면 `LLR_MATRIX[row]` 행 밖을 읽는다

가설: `num_para_each_set = 4`인 파일에서 2SD는 dv 그룹당 5칸, 3SD는 7칸을 요구하므로 마지막 dv 그룹에서 배열 끝을 넘는다.

증거 (확인됨).

- ㉮ 위 3.2 표의 계산. 2SD는 `LLR_MATRIX[row][16]`, 3SD는 `[16]`, `[17]`, `[18]`을 읽는다. 행 크기는 16이다(local_opt.cpp:101)
- ㉯ 이 경로는 AUTO 빌드에서 도달 가능하다. `Get_VNU_LLR_SET_FILE`의 2SD 갈래(decoder.cpp:7103)와 3SD 갈래(decoder.cpp:7118)는 `m_param_dec->init_n`으로만 갈리고, 상위 문서 6.2절이 든 다섯 곳 중 `VN_Cal_SD`(decoder.cpp:4493)와 `VN_Cal_SD_HCU`(decoder.cpp:4649)가 2SD, 3SD 경로다. `V2C_Cal`의 배차가 decoder.cpp:5715-5721에 있다
- ㉰ 읽은 값은 힙의 다음 행이나 무관한 메모리라 `th3`가 무작위 값이 된다. 오류 출력도 크래시도 없다
- ㉱ 이것은 계획이 만드는 결함이 아니라 기존 상태다. 다만 code_diff 6.1이 `__AUTO_LLR_OPT__` 갈래를 없애고 한 갈래로 합치면서 2SD, 3SD도 같은 그룹 선택 코드를 타게 되므로, 문서가 이 제약을 적어야 한다

처방: 상위 문서에 "이 형태의 파일은 HD와 1.5SD 전용이며, 2SD는 `num_para_each_set >= 5`, 3SD는 `>= 7`이 필요하다"는 제약을 적고, `Init_Dec_Option`이나 파서에서 `init_n`과 `num_para_each_set`을 대조해 어긋나면 멈추게 한다. 코드 추가를 요구한다.

### B1-8 (LOW) `__4_BIT_LLR__`를 켜면 HD 경로도 행 밖을 읽는다

증거 (확인됨). decoder.cpp:7096-7101이 `table_col_idx + 4`에서 `+7`까지 읽는다. `num_para_each_set = 4`이면 마지막 dv 그룹에서 index 16에서 19가 되어 4칸 초과다. [mode.h:12](../../../../../../0_LDPC_original/src/mode.h)의 `//#define __4_BIT_LLR__`가 주석이라 지금은 일어나지 않는다.

처방: B1-7의 제약 문장에 `__4_BIT_LLR__`를 켤 때 `num_para_each_set >= 8`이 필요하다는 것을 함께 적는다. 문서만 고치면 된다.

### B1-9 (문제 없음) `PARAM_LLR` 구조체에 멤버 셋을 끼워 넣어도 레이아웃이 깨지지 않는다

가설(반증 대상): code_diff 2.1이 `type_each_group` 뒤와 `restart_num` 앞에 멤버 셋을 끼우면, 구조체를 통째로 복사하거나 전송하는 곳이 깨진다.

증거 (반박됨).

- ㉮ `sizeof(PARAM_LLR)`, `sizeof(m_param_LLR)`, `memcpy(&m_param_LLR ...)`, `memcpy(m_param_LLR ...)`를 소스 전체에서 grep한 결과 히트 0건이다
- ㉯ 전달은 전부 포인터다. `LOCAL_OPT::m_param_LLR`이 값 멤버지만(local_opt.h:30) 주소만 넘긴다. `Init_ECC_Top(..., &m_param_LLR, ...)`(local_opt.cpp:46), `ECC_Top::m_param_LLR`이 포인터(ecc_top.h:94), `Init_Dec(..., m_param_LLR, ...)`(ecc_top.cpp:208, 228), `Decoder::m_param_LLR`이 포인터(decoder.h:210)
- ㉰ 전송도 구조체 단위가 아니다. 소스 전체의 `MPI_Bcast` 히트는 ecc_top.cpp:516(`seed` 한 개), local_opt.cpp:41, local_opt.cpp:43뿐이고 모두 개별 배열을 원소 수를 명시해 보낸다. `MPI_Send`, `MPI_Recv`는 0건, `fwrite`는 common.cpp:149, 165, 169, 175로 모두 1바이트 단위 파일 출력이며 구조체와 무관하다
- ㉱ `PARAM_LLR`의 정의는 ecc_data.h:179 한 곳뿐이다

판정: 멤버 삽입은 안전하다. code_diff 2.1은 이 점에서 문제가 없다.

### B1-10 (문제 없음) 6.2절이 든 다섯 곳은 정말 같은 형태이고 수정 후에도 갈림이 그대로다

다섯 곳을 모두 읽었다. 함수 이름을 확인하기 위해 정의 위치를 함께 적는다.

| 상위 문서 6.2 표의 줄 | 실제 위치 | 함수 (정의 위치) |
|--------------------|----------|----------------|
| 3985-3990 | decoder.cpp:3985-3990 | `VN_Cal_HD` (decoder.cpp:3973) |
| 4160-4165 | decoder.cpp:4160-4165 | `VN_Cal_HD_HCU` (decoder.cpp:4136) |
| 4366-4371 | decoder.cpp:4366-4371 | `VN_Cal_CD` (decoder.cpp:4354) |
| 4505-4510 | decoder.cpp:4505-4510 | `VN_Cal_SD` (decoder.cpp:4493) |
| 4673-4678 | decoder.cpp:4673-4678 | `VN_Cal_SD_HCU` (decoder.cpp:4649) |

다섯 곳 모두 문자 그대로 같은 형태다.

```
#if defined(__AUTO_LLR_OPT__)
    Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, ..., &th7);
#else
    Get_VNU_Ch_LLR_Adaptive(v_deg, col_idx, cur_set_idx, &ch1, &ch2, &ch3, &ch4);
    Get_VNU_Th_Adaptive(v_deg, col_idx, cur_set_idx, &th1, ..., &th7);
#endif
```

갈림은 `__AUTO_LLR_OPT__` 하나에만 걸린 컴파일 시점 갈림이고 `flag_BF_on`이나 `ITER_MAX_HBF`를 보지 않는다. code_diff 어느 장도 이 다섯 곳을 건드리지 않으므로 갈림 자체는 수정 후에도 그대로다. 바뀌는 것은 넘어가는 `cur_set_idx` 값과, 같은 함수 안 1bit precision 갈래가 살아나는 것(B1-4)뿐이다. 상위 문서 6.2절의 "다섯 곳 모두 형태가 같다"와 "분기 지원 자체와는 무관, 확인만"은 맞다.

### B1-11 (LOW) `Adjust_HD_Floor_Type`에 미초기화 멤버가 넘어간다

증거 (확인됨). `Get_Cur_LLR_Idx_FILE`이 HD에서 매 iteration `Adjust_HD_Floor_Type(Floor_Detect_CSW_TH1, Floor_Detect_CSW_TH2)`를 부른다(decoder.cpp:6982). 두 멤버(decoder.h:336-337)에 값을 넣는 곳은 decoder.cpp:498-501뿐이고 그 블록은 `#if defined(__HD_FLOOR_SET__)`(decoder.cpp:494) 안이며 [mode.h:73](../../../../../../0_LDPC_original/src/mode.h)이 주석이다. 생성자(decoder.cpp:20-90)에도 초기화가 없다.

영향은 없다. `__HD_FLOOR_SET__`이 꺼진 빌드에서 `Adjust_HD_Floor_Type`의 본체는 인자를 쓰지 않고 `state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0`만 대입한다(decoder.cpp:8108-8113). 계획과 무관한 기존 상태이므로 LOW로 적는다.

부수 확인: code_diff 4.1이 갈아 끼우는 범위는 decoder.cpp:459-493이고 `__HD_FLOOR_SET__` 블록은 494행부터다. 실수로 지워지지 않는다.

---

## 4. 확인한 범위

읽은 소스.

- [mode.h](../../../../../../0_LDPC_original/src/mode.h) 전체 (82행)
- [common.h](../../../../../../0_LDPC_original/src/common.h) 285-300, 354-357, 370-410, 691
- [decoder.h](../../../../../../0_LDPC_original/src/decoder.h) 280-355, 392, 429-437
- [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) 440-530, 540-620, 690-790, 1085-1205, 1380-1620, 1860-1990, 2140-2200, 2285-2330, 3000-3030, 3205-3230, 3370-3380, 3462-3501, 3570-3690, 3960-4140, 4136-4320, 4355-4380, 4495-4520, 4660-4690, 5690-5750, 6012-6045, 6099-6125, 6410-6560, 6973-7132, 7700-7790
- [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) 전체 (185행)
- [local_opt.h](../../../../../../0_LDPC_original/src/local_opt.h) 23, 30
- [ecc_data.h](../../../../../../0_LDPC_original/src/ecc_data.h) 179-198
- [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) 78-95, 208-230, 320-340
- [ecc_top.h](../../../../../../0_LDPC_original/src/ecc_top.h) 94, 152
- [encoder.cpp](../../../../../../0_LDPC_original/src/encoder.cpp) 50-100
- [mpi.h](../../../../../../0_LDPC_original/src/mpi.h), [mpi.cpp](../../../../../../0_LDPC_original/src/mpi.cpp) 전체

전수 grep (소스 트리 전체).

- `__RUN_PUNCT_RECOVERY__|__SHUFFLED_DUAL_DIAG__|__PMU_READ__|__HALF_COL_UPDATE__|__HALF_COL_MODIFIED__` (히트 전량을 1장에 실었다)
- `ITER_MAX_HBF` (전량, 문맥 3줄)
- `flag_BF_on|iter <= 4|iter<=4` (전량, 문맥 2줄)
- `flag_HD_1_4_Set|flag_HD_5_8_Set|o_BF_on|BF_on` (전량)
- `PMU_Read|PMU_READ|Clear_PMU|PMU_` (전량)
- `syn_th_5_8_Set_0|syn_th_5_8_Set_1|syn_th_BF|syn_th_BF0|syn_th_BF1` (전량)
- `PARAM_LLR|m_param_LLR` (전량)
- `sizeof(PARAM|sizeof(m_param|sizeof(LLR|memcpy(&m_param|memcpy(m_param` (히트 0건)
- `MPI_Bcast|MPI_Send|MPI_Recv|fwrite` (전량)
- `crc_dec_LFSR_iter|m_log_CSW_auto` (전량)
- `current_G_idx\s*=\s*\(` (전량, 8건)
- `VN_Cal_HD_HCU|VN_Cal_HD\(|V2C_Cal_HCU|Clear_Sum_t_OLD|Sum_t_OLD_G` (전량)
- `Floor_Detect_CSW_TH1|Floor_Detect_CSW_TH2` (전량)

읽은 데이터 파일.

- [LLR_MATRIX_1.txt](../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 전체 (105행), 그룹별 row 수와 row 칸 수를 손으로 셌다
- [LLR_MATRIX_0.txt](../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt) 앞 20행

확인하지 못한 것.

- ㉮ 실제 H-matrix가 없어 `m_PCM->ColW[jj]`의 차수 분포를 알 수 없다. B1-6의 조용한 dv 대체가 실제로 일어나는지는 미확인이다
- ㉯ DAO가 2SD나 3SD 모드로 AUTO 빌드를 돌리는지 확인하지 않았다. B1-7의 발생 여부가 그 조건에 달려 있다
