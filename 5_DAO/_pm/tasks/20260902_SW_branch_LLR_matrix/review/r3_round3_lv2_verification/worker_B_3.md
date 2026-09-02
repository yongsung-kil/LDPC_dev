# Round 3 팀 B 워커 3: 재탐색 결과

작성: 2026-09-03 01:44:18

탐색 영역 세 가지를 소스에서 직접 읽어 확인했다. 이전 라운드 결과는 읽지 않았다.

대상 문서 (수정하지 않음): [상위 문서](../../20260902_SW_branch_LLR_matrix.md), [code_diff.md](../../code_diff.md)

---

## 0. 읽은 범위

| 파일 | 읽은 줄 |
|------|--------|
| [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) | 1-185 (전체) |
| [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) | 1-120, 440-660, 700-750, 1075-1185, 1930-2140, 2280-2400, 3425-3520, 5300-5365, 6530-6690, 6940-7160, 8050-8116 |
| [decoder.h](../../../../../../0_LDPC_original/src/decoder.h) | 1-20, 280-350 |
| [ecc_data.h](../../../../../../0_LDPC_original/src/ecc_data.h) | 175-200 |
| [common.h](../../../../../../0_LDPC_original/src/common.h) | 225-255, 395-415, 675-690, 710-760 |
| [mode.h](../../../../../../0_LDPC_original/src/mode.h) | 1-83 (전체) |
| [corner.h](../../../../../../0_LDPC_original/src/corner.h) | 60-100 |
| [corner.cpp](../../../../../../0_LDPC_original/src/corner.cpp) | Event_Flag 정의 |
| [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) | 868-900 |
| [ecc_top.h](../../../../../../0_LDPC_original/src/ecc_top.h) | Decoder 멤버 선언 |
| [main.cpp](../../../../../../0_LDPC_original/src/main.cpp) | 40-200, 704-800 |
| [DAO_Config.py](../../../../../SRC/DAO_Config.py) | 1-200 |
| [DAO_LLR_MATRIX.py](../../../../../SRC/DAO_LLR_MATRIX.py) | 30-70, 300-400, 470-560, 620-690 |
| [DAO_Main.py](../../../../../SRC/DAO_Main.py) | 6395-6505 |
| [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) | 전체 (헤더 + row 77개) |

Grep 전수 히트는 각 발견 안에 적었다.

---

## 1. 파일 구조 확정 (이후 손실행의 근거)

[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 헤더:
`num_group` 12, `num_set_each_group` = `1 7 6 6 1 5 5 7 6 10 10 13` (합 77),
`type_each_group` = `20 20 21 20 21 21 1 1 1 1 1 1`, `restart_num` 0.

row 번호는 파서가 붙이는 0부터의 통번호다.

| 그룹 | row 범위 | `iter_start[start_idx]` | `iter_end[end_idx]` | row 마지막 칸 |
|------|---------|------------------------|--------------------|--------------|
| 0 | 0 | 1 | 1 | 0 |
| 1 | 1-7 | 2 | 4 | 0 |
| 2 | 8-13 | 1 | 4 | 1 |
| 3 | 14-19 | 5 | 8 | 0 |
| 4 | 20 | 5 | 5 | 1 |
| 5 | 21-25 | 6 | 8 | 1 |
| 6 | 26-30 | 9 | 24 | -1 |
| 7 | 31-37 | 25 | 44 | -1 |
| 8 | 38-43 | 45 | 64 | -1 |
| 9 | 44-53 | 65 | 84 | -1 |
| 10 | 54-63 | 85 | 104 | -1 |
| 11 | 64-76 | 105 | 124 | -1 |

---

## 2. 영역 ㉰: 2SD와 3SD 경로

### B3-1 [HIGH] AUTO 빌드의 2SD와 3SD에서 고르는 그룹이 뒤집히고 row 12개가 도달 불가가 된다

가설: 2SD와 3SD에서 `cur_sw_branch_idx[]`가 0으로 고정되면, 수정 후 [code_diff 6.1](../../code_diff.md#ch6)의 분기 필터가 분기 1 그룹을 전부 걸러내어, 수정 전 AUTO 갈래가 고르던 그룹과 다른 그룹을 고른다.

증거 (확인됨):

- ㉮ 수정 후 [code_diff 5.1](../../code_diff.md#ch5)의 `Select_BF`는 `MODE_DEC_HD`와 `MODE_DEC_1_5SD`만 다루고, 나머지 모드는 마지막 `else`에서 `flag_BF_on = FLAG_LOW`만 세운다. 함수 앞머리의 `for (i = 0; i < MAX_SW_SPAN; i++) cur_sw_branch_idx[i] = 0;`만 걸리므로 2SD와 3SD에서는 전부 0이다
- ㉯ `Select_BF`는 모드 조건 없이 불린다 (`decoder.cpp:1968-1970`, `if (mn == 0) Select_BF();`). 모드 상수는 `common.h:75-78` (`MODE_DEC_HD` 1, `MODE_DEC_2SD` 2, `MODE_DEC_3SD` 3, `MODE_DEC_1_5SD` 4)
- ㉰ 수정 전 AUTO 갈래(`decoder.cpp:6985-6999`)는 `g = num_group - 1`부터 내려오며 iteration 범위만 보고 처음 맞는 그룹에서 멈춘다. 1절 표로 손실행하면 iteration 1~4는 그룹 2, iteration 5는 그룹 4, iteration 6~8은 그룹 5가 잡힌다 (뒤에서 훑으므로 분기 1 그룹이 먼저 걸린다)
- ㉱ 수정 후 6.1은 `group_branch != SW_BRANCH_NONE`인 그룹에서 `group_branch != cur_sw_branch_idx[span]`이면 `continue`한다. 분기 1인 그룹 2, 4, 5가 전부 걸러진다. 남는 후보로 손실행하면 iteration 1은 그룹 0, iteration 2~4는 그룹 1, iteration 5~8은 그룹 3이 잡힌다

결과: 2SD와 3SD에서 그룹 2(row 6개), 그룹 4(row 1개), 그룹 5(row 5개), 합 12개 row가 영영 선택되지 않는다. 오류 출력도 없다. 77개 row 중 12개다.

판정: 확인됨. 심각도 HIGH (틀린 파라미터로 복호가 계속된다).

처방 (동작 변경 또는 문서 결정 요구): 두 갈래 중 하나를 문서가 골라야 한다.

- ㉮ 2SD와 3SD도 SW로 분기를 고른다 (`syn_weight`는 모드와 무관하게 `decoder.cpp:3443`에서 계산되므로 값은 있다)
- ㉯ 2SD와 3SD는 분기 0 고정으로 두되, 그것이 결정임을 문서에 적고 분기 1 그룹이 SD 파일에 들어가지 않도록 파서에서 막는다

### B3-2 [MEDIUM] 두 문서 어디에도 "2SD와 3SD는 분기 0 고정"이 적혀 있지 않다

증거 (확인됨):

- ㉮ [상위 문서 5.4](../../20260902_SW_branch_LLR_matrix.md)는 `Select_BF`를 "SW로 분기를 정하고"라고만 쓰고 어느 복호 모드에 적용되는지 말하지 않는다
- ㉯ [code_diff 5.1](../../code_diff.md#ch5)의 "바뀐 점" 세 항목(㉮㉯㉰)은 모두 BF와 iteration 1~4, 5~8만 말한다. `else` 갈래가 무엇을 뜻하는지 설명이 없다
- ㉰ [code_diff 2.2](../../code_diff.md#ch2)의 주석은 "span 0 = iteration 1~4, span 1 = iteration 5~8"뿐이고 모드를 말하지 않는다
- ㉱ 상위 문서 7장 미결정 사항 네 항목(㉮ 표기, ㉯ 문턱 출처, ㉰ 구간 고정 여부, ㉱ 비AUTO 하드코딩)에 모드별 적용 범위가 없다

판정: 확인됨. 심각도 MEDIUM (누락).

처방 (문서): 상위 문서 7장에 결정 항목으로 올린다.

### B3-3 [MEDIUM] DAO는 2SD와 3SD를 실제로 돌린다. "HD 위주라 위험이 없다"는 성립하지 않는다

증거 (확인됨):

- ㉮ [DAO_Config.py:13-18](../../../../../SRC/DAO_Config.py)의 SIM_IDX 표에 `20: 2SD opt`, `21: 2SD Save UECC`, `22: 2SD redecoding`, `30: 3SD opt`, `31: 3SD Save UECC`, `32: 3SD redecoding`이 있다
- ㉯ `DAO_Config.py:62, 74, 83`이 `REFC_CONFIG.init_n = 2`를, `94, 104, 111`이 `= 3`을 세운다
- ㉰ `DAO_Constants.py:5` `MODE_MAP = {1: "HD", 2: "2SD", 3: "3SD"}`
- ㉱ `DAO_Main.py:6413`(ECC_VER 2.4 갈래)과 `6436`(그 외 갈래)이 `REFC_CONFIG.init_n`을 Ref-C 실행 인자 #2로 넣는다. `main.cpp:167` `g_param_dec.init_n = atoi(argv[2]);`가 그것을 받고 `main.cpp:168`이 1 이상 4 이하만 통과시킨다
- ㉲ `DAO_LLR_MATRIX.py:43-50`은 2SD와 3SD에서 `is_HBF_OPT`를 False로 못박는다. BF 최적화 자체는 HD 전용이라는 신호다. 다만 SD의 LLR matrix도 같은 C++ 파서를 지난다

판정: 확인됨. 심각도 MEDIUM (B3-1의 심각도를 HIGH로 유지시키는 근거다).

### B3-4 [MEDIUM] 3.2 파서가 분기 줄을 모드와 무관하게 무조건 읽는다. 2SD와 3SD 파일에도 그 줄이 필요하다는 서술이 없다

증거 (확인됨):

- ㉮ 수정 후 [code_diff 3.2](../../code_diff.md#ch3)가 넣는 반복문은 `type_each_group` 반복문 바로 뒤에 조건 없이 `num_group`개의 정수를 더 읽는다. `Read_LLR_info_Auto`(`local_opt.cpp:52-184`) 전체에 복호 모드로 갈라지는 곳은 `local_opt.cpp:124` 하나뿐이고 그것은 MN 보정이다
- ㉯ 파서는 `fscanf(matrix_in, "%d", &c)` 토큰 기반이라, 분기 줄이 없는 파일을 넣으면 `restart_num` 자리부터 뒤가 통째로 밀린다
- ㉰ DAO의 Python 파서(`DAO_LLR_MATRIX.py:476-491`)는 줄 index를 하나씩 올리며 `type_each_group` 다음을 바로 `num_restart`로 읽고, 이 순서에 모드 조건이 없다. 즉 DAO가 쓰는 파일에는 아직 분기 줄이 없고, 있게 하려면 세 모드 전부에 넣어야 한다

판정: 확인됨. 심각도 MEDIUM (누락 커버리지).

처방 (문서): 3.2에 "모든 복호 모드의 LLR matrix 파일이 분기 줄을 갖는다"를 전제로 적는다.

### B3-5 [반박됨] `decoder.cpp:2328`의 `iter - 1`은 파일 `restart_iter`와 한 칸 어긋나는 결함이 아니다

`Is_Iter_Type_Edge_Clear` 호출처 전수 (8곳):

| 줄 | 함수 | 넘기는 인자 | 모드 갈래 |
|----|------|-----------|----------|
| `decoder.cpp:712` | `Clear_Edge_Restart` | `mn` | HD, 1.5SD |
| `decoder.cpp:726` | `Clear_Edge_Restart` | `mn` | 2SD, 3SD |
| `decoder.cpp:2314` | `C2V_Cal_New_Sgn` | `iter` | HD, 1.5SD (`__RUN_PREPROCESSING__` 갈래) |
| `decoder.cpp:2321` | `C2V_Cal_New_Sgn` | `iter` | HD, 1.5SD (`#else` 갈래) |
| `decoder.cpp:2328` | `C2V_Cal_New_Sgn` | `iter - 1` | 2SD, 3SD |
| `decoder.cpp:3491` | `CNU_Remove_Old_Sgn` | `iter` | HD, 1.5SD (`__RUN_PREPROCESSING__` 갈래) |
| `decoder.cpp:3498` | `CNU_Remove_Old_Sgn` | `iter` | HD, 1.5SD (`#else` 갈래) |
| `decoder.cpp:3504` | `CNU_Remove_Old_Sgn` | `iter` | 그 외 모드 |

증거 (확인됨):

- ㉮ `decoder.cpp:2290-2291`의 함수 머리 주석이 "SD: Restart 다음 iteration에서 old_sgn을 읽어 오지 않음. HD: Restart iteration에서 old_sgn을 읽어 오지 않음"이라고 두 모드의 시점 차이를 명시한다. `iter - 1`은 그 설계를 그대로 옮긴 것이다
- ㉯ 실제 edge clear는 `Clear_Edge_Restart`(`decoder.cpp:726`)가 `mn`으로 하고, `iter - 1` 비교는 그 다음 iteration에서 읽기를 막는다. 두 지점이 한 칸 차이 나는 것이 의도다
- ㉰ 수정 후 [code_diff 8.1](../../code_diff.md#ch8)을 적용해도 2SD와 3SD가 타는 `else` 갈래는 `iter == 0`과 `restart_iter[i]`만 본다. `iter - 1 == restart_iter[i]`이므로 `iter == restart_iter[i] + 1`에서 걸린다. 파일 값과 한 칸 어긋나는 새 경로는 생기지 않는다
- ㉱ `mn == 0`에서 `Is_Iter_Type_Edge_Clear(-1)`이 불리지만, `iter == 0` 조건이 거짓이고 `restart_num` 반복문도 -1과 같은 값을 담지 않는 한 FALSE다. 배열 밖 접근은 없다

판정: 반박됨 (설계대로다).

곁가지 (확인됨, MEDIUM): 8.1이 `#else` 갈래를 지우면 비AUTO 2SD의 restart 지점 `RSP1_2SD_PRIME_1` 241과 `RSP1_2SD_PRIME_2` 581, 비AUTO 3SD의 171, 312, 653, 844, 1035, 1301 (`common.h:679-686`)이 사라지고, 대신 파일의 `restart_iter[]`를 쓰게 된다. [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)는 `restart_num`이 0이므로 2SD와 3SD의 restart edge clear가 `iter == 0` 하나로 줄어든다.

### B3-6 [LOW] 수정 후 5.1의 Corner 이벤트가 모드 갈래 밖에 있어 2SD와 3SD에서도 켜진다

증거 (확인됨):

- ㉮ 수정 전(`decoder.cpp:2092-2094, 2101-2103, 2107-2109, 2118-2120, 2124-2126`)의 `Event_Flag` 호출은 모두 HD 또는 1.5SD 갈래 안에 있다
- ㉯ 수정 후 [code_diff 5.1](../../code_diff.md#ch5)은 `m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]);`을 함수 끝, 모든 모드 갈래 밖에 둔다. 2SD와 3SD 프레임도 `IDX_FLAG_HD_5_8_SET_TYPE_0`(`corner.h:79`)을 켠다
- ㉰ `CornerChecker::Event_Flag`(`corner.cpp:119-126`)는 한 번 켜면 그대로 두는 플래그다. SD 통계에 HD 전용 플래그가 섞인다
- ㉱ `__CORNER_CHECKER__`는 `mode.h:75`에서 주석이라 지금은 컴파일되지 않는다

판정: 확인됨. 심각도 LOW (컴파일 스위치가 꺼져 있다).

처방 (동작 변경): 이벤트 호출을 HD와 1.5SD 갈래 안으로 되돌린다.

---

## 3. 영역 ㉱: 극단 입력에서 3.1, 3.5, 6.1, 6.2

파서([local_opt.cpp:52-184](../../../../../../0_LDPC_original/src/local_opt.cpp)) 전체를 먼저 읽고 손실행했다. 할당 순서는 `num_set_each_group`, `type_each_group`(74행), `restart_iter`(86행), `max_value`, `min_value`(91-92행), `LLR_MATRIX`, `CSW_thr`, `iter_start`, `iter_end`, `floor_flag`(101-105행)다.

### B3-7 [CRITICAL] `num_row`가 0인 파일에서 6.2의 `return 0`이 안전하지 않다

가설: 6.2가 오류 시 0을 돌려주면 뒤쪽 배열 접근이 안전하다.

증거 (반박됨):

- ㉮ `num_group`이 0이면 `local_opt.cpp:75-80`의 누적 반복문이 안 돌아 `num_row`가 0으로 남는다. `num_row`가 0이면 `local_opt.cpp:101` `LLR_MATRIX = new int*[0]`이다
- ㉯ 수정 후 6.1의 `for (g = num_group - 1; g >= 0; g--)`가 `g = -1`로 시작해 한 번도 안 돌고 `selected_group`이 -1로 남는다. 수정 후 6.2의 첫 검사가 오류를 찍고 `return 0`한다
- ㉰ 호출자는 `decoder.cpp:1138` `cur_set_idx = Get_Cur_LLR_Idx_FILE(mn);` 하나뿐이다 (`mn > 0`일 때). 그 값은 `Get_VNU_LLR_SET_FILE`의 `table_row_idx`로 들어간다. 호출처 다섯 곳: `decoder.cpp:3986, 4161, 4367, 4506, 4674`
- ㉱ `Get_VNU_LLR_SET_FILE`(`decoder.cpp:7089` 이하)은 `m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx]`를 조건 없이 읽는다. 크기 0 배열의 원소 0을 읽어 얻은 미정의 포인터를 역참조한다

판정: [code_diff 6.2](../../code_diff.md#ch6)의 "바뀐 점 ㉰: 오류일 때 0을 돌려주어 뒤쪽 배열 접근이 안전하게 한다"는 `num_row >= 1`일 때만 참이다. 심각도 CRITICAL (프로세스 중단).

처방 (코드 추가): 파서에서 `num_group <= 0` 또는 `num_row <= 0`을 오류로 잡고 멈춘다.

### B3-8 [CRITICAL] 3.5 수정 후 `max_iter_end`가 0이면 `MN_num`이 0이 되고 `MN[MN_num - 1]`을 읽는 곳이 22곳이다

발생 조건 두 가지 (확인됨):

- ㉮ `num_row`가 0이면 3.5의 `for (i = 0; i < LLR_info->num_row; i++)`가 안 돌아 `max_iter_end`가 0으로 남는다
- ㉯ 모든 row의 `iter_end`가 0 이하이면 `if (LLR_info->iter_end[i] > max_iter_end)`가 한 번도 참이 아니라 역시 0이다

이어지는 동작 (확인됨):

- ㉠ `m_param_dec->MN_num = 0`, `m_param_dec->MN = new int[0]`. 채우는 반복문도 안 돈다
- ㉡ `local_opt.cpp:128` `if (m_param_dec->MN_num > 1)`이 거짓이라 `MN[0] = ITER_MAX_HBF` 되돌림도 걸리지 않는다
- ㉢ `MN[MN_num - 1]`, 즉 `MN[-1]`을 읽는 곳 전수: `decoder.cpp:564, 587, 1118, 7583, 7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018`, `corner.cpp:103`
- ㉣ `decoder.cpp:564` `MN_max = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF;` 다음 줄이 `crc_dec_LFSR_iter = new int[MN_max * CRC_LEN];`이다. 읽은 쓰레기 값이 음수면 `std::bad_array_new_length`가 던져져 프로세스가 끝난다
- ㉤ `ecc_top.cpp:638` `fr_4KB = new int[m_param_dec->MN_num];`(크기 0) 뒤에 `ecc_top.cpp:875` `fr_4KB[m_param_dec->MN_num - 1]++;`가 -1 index에 쓴다. 같은 형태가 `ecc_top.cpp:690, 771, 2120, 2201, 2272`에도 있다

판정: 확인됨. 심각도 CRITICAL (힙 손상 또는 프로세스 중단).

곁가지 (확인됨, MEDIUM): `max_iter_end`가 1이면 `MN_num = 1`, `MN[0] = 1`이 되고, `local_opt.cpp:125-127`의 HD 보정이 `MN[0] = 1 - 4 = -3`을 남긴다. `MN_num > 1`이 거짓이라 `MN[0] = ITER_MAX_HBF` 되돌림이 없다. 그러면 `decoder.cpp:1118` `MN = -3`, `decoder.cpp:1120` `for (mn = 0; mn < MN + 1; mn++)`가 `0 < -2`로 한 번도 안 돈다. 복호가 통째로 건너뛰어진다.

처방 (코드 추가): 3.5 뒤에 `if (max_iter_end <= 0)`을 오류로 잡고 멈춘다. 3.5는 마지막 row 의존을 없앤 개선이지만 이 구멍은 닫지 않는다.

### B3-9 [HIGH] 어느 그룹의 `num_set_each_group[i]`가 0이면 `end_idx = start_idx - 1`이 되어 앞 그룹 값을 읽거나 배열 밖을 읽는다

증거 (확인됨):

- ㉮ 수정 후 [code_diff 6.1](../../code_diff.md#ch6)의 start_idx, end_idx 계산은 수정 전(`decoder.cpp:6986-6994`)과 같다. 빈 그룹이면 두 누적합이 같아져 `end_idx = end_idx - 1 = start_idx - 1`이다
- ㉯ 빈 그룹이 그룹 0이면 `start_idx = 0`, `end_idx = -1`이 되어 `m_param_LLR->iter_end[-1]`을 읽는다. 배열 밖이다
- ㉰ 빈 그룹이 중간이면 `iter_end[start_idx - 1]`은 바로 앞 그룹의 마지막 row 값이다. 빈 그룹이 앞 그룹의 iteration 상한을 물려받아 후보로 잡힐 수 있다
- ㉱ 빈 그룹이 마지막이면 `start_idx == num_row`가 되어 `iter_start[num_row]`를 읽는다. 배열 밖이다

빈 그룹이 `selected_group`이 되었을 때 6.2의 동작 (확인됨):

- ㉠ `GROUP_TYPE_ITER`이면 `for (i = start_idx; i <= end_idx; i++)`가 `end_idx < start_idx`라 안 돈다. `table_row_idx`가 수정 후 초기값 -1로 남고 아래 검사가 잡아 `return 0`한다. 수정 후가 초기값을 0에서 -1로 바꾼 것이 여기서는 이롭게 작동한다
- ㉡ `GROUP_TYPE_CSW`이면 `table_row_idx = start_idx`를 먼저 대입하고, `num_candidate = 0`이라 `for (i = -1; i > 0; i--)`가 안 돈다. `table_row_idx = start_idx`가 남는다. `start_idx < num_row`이면 `table_row_idx < 0 || >= num_row` 검사를 통과해 **다음 그룹의 첫 row**를 오류 표시 없이 쓴다
- ㉢ 3.4의 헤더와 row 대조 검사도 빈 그룹에서는 안쪽 `for (int r = 0; r < num_set_each_group[i]; r++)`가 안 돌아 아무것도 잡지 않는다

곁가지 (확인됨): DAO의 `Is_LLR_Valid`(`DAO_LLR_MATRIX.py:300-302`)는 빈 그룹을 거부한다. DAO가 만든 파일에서는 안 일어나지만 C++ 쪽 방어는 없다.

판정: 확인됨. 심각도 HIGH (㉡ 경로는 틀린 row로 복호가 조용히 계속된다).

처방 (코드 추가): 파서에서 `num_set_each_group[i] <= 0`을 오류로 잡는다.

### B3-10 [문제 없음] `num_row`가 `MN_num`보다 작은 파일과 그 반대는 둘 다 문제가 없다

증거 (확인됨):

- ㉮ `MN`은 `MN_num`으로(`local_opt.cpp:117`), `LLR_MATRIX`, `CSW_thr`, `iter_start`, `iter_end`, `floor_flag`는 `num_row`로(`local_opt.cpp:101-105`) 따로 잡는다
- ㉯ `num_row` 전수 히트: `decoder.cpp:6981`(주석), `decoder.cpp:7069`(경계 검사), `ecc_data.h:182`(선언), `local_opt.cpp:22, 39, 43, 75, 79, 101, 102, 103, 104, 105, 106, 116, 120, 170`. `num_row`를 iteration 수로 쓰는 곳은 없다
- ㉰ 현 파일이 이미 `num_row` 77, `MN_num` 124다

판정: [상위 문서 5.1-4](../../20260902_SW_branch_LLR_matrix.md)의 "`num_row`를 iteration 수로 간주하는 곳이 있으면 고쳐야 한다"는 실체가 없다. 심각도 LOW (문서에 "그런 곳은 없다"로 확정해 두면 이후 작업이 줄어든다).

---

## 4. 영역 ㉴: 프레임 간 초기화가 필요한 상태 전수

### B3-11 [사실 확인] 세 함수의 내용과 호출처

`Initialize_Dec` (`decoder.cpp:19-113`): 포인터만 NULL로 채운다 (`m_ecc_info`, `m_PCM`, `m_param_dec`, `REG_min1_pos`부터 `m_log_ch_llr`까지). 값 멤버는 하나도 건드리지 않는다. `m_TV_cycle_based_on = TRUE`만 예외다.
호출처 전수: `decoder.cpp:7` (생성자) 하나. `Decoder m_dec;`는 `ECC_Top`의 값 멤버(`ecc_top.h:97`)라 `ECC_Top` 하나당 한 번만 돈다. **프레임마다 돌지 않는다.**

`Clear_Flag` (`decoder.cpp:606-616`): `real_mn`, `flag_BF_on`, `flag_dec_1iter`, `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `state_hd_error_floor_set`, `cnt_hd_error_floor`.
호출처 전수: `decoder.cpp:1091` 하나 (`LDPC_Decoder` 안, 프레임마다 한 번).

`Clear_Iter_Start` (`decoder.cpp:621-631`): `Force_stopping`, `pre_Force_stopping`, `Error_count_reg`, `cur_variable_node`, `prev_variable_node`, `prev_variable_node2`, `prev_variable_node2_print`, `stop_by_partial_crc`.
호출처 전수: `decoder.cpp:1131` 하나 (mn 루프 앞머리, iteration마다).

### B3-12 [HIGH] `Clear_Flag`의 두 줄을 code_diff 어느 장도 다루지 않아 양쪽 빌드가 컴파일되지 않는다

`flag_HD_1_4_Set` 전수 히트 (5곳): `decoder.cpp:612`, `decoder.cpp:2090`, `decoder.cpp:7002`, `decoder.cpp:7006`, `decoder.h:297`.
`flag_HD_5_8_Set` 전수 히트 (9곳): `decoder.cpp:613`, `decoder.cpp:2091`, `decoder.cpp:2100`, `decoder.cpp:2106`, `decoder.cpp:2117`, `decoder.cpp:2123`, `decoder.cpp:7010`, `decoder.cpp:7016`, `decoder.h:298`.
`local_opt.cpp`, `ecc_top.cpp`, `corner.cpp`, `TV_Dec.cpp`, `TV_Dec_Inter.cpp`, `TV_Enc.cpp`에는 히트가 없다.

code_diff가 덮는 범위: 2.2가 `decoder.h:296-306`, 5.1이 `decoder.cpp:2082-2130`, 6.1이 `decoder.cpp:6973-6999`와 `#else` 갈래 `7001-7020`.
덮이지 않는 곳: `decoder.cpp:612`, `decoder.cpp:613` 두 줄뿐이다. 2.2가 멤버를 지우면 이 두 줄이 미정의 식별자를 참조한다.

판정: 확인됨. 심각도 HIGH (빌드 불가).

처방 (코드 삭제와 추가): 612-613을 지우고 그 자리에 `for (int i = 0; i < MAX_SW_SPAN; i++) cur_sw_branch_idx[i] = 0;`을 넣는다. B3-16의 처방과 같은 자리다.

### B3-13 [문제 없음] `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1` 참조는 모두 덮인다

| 이름 | 전수 히트 | 덮는 장 |
|------|----------|--------|
| `syn_th_BF` | `decoder.h:301`, `decoder.cpp:472`. `decoder.cpp:460-465`는 주석 | 2.2, 4.1 |
| `syn_th_BF1` | `decoder.h:303`, `decoder.cpp:468` | 2.2, 4.1 |
| `syn_th_5_8_Set_0` | `decoder.h:305`, `decoder.cpp:480`, `483`, `2099`, `2116`. `477-479`, `481-482`, `583`은 주석 | 2.2, 4.1, 5.1 |
| `syn_th_5_8_Set_1` | `decoder.h:306`, `decoder.cpp:489`, `492`. `486-488`, `490-491`, `583`은 주석 | 2.2, 4.1 |

`local_opt.cpp`, `ecc_top.cpp`, `corner.cpp`, `TV_*`에는 히트가 없다.
곁가지 (확인됨): 4.1 수정 후가 쓰는 반복 변수 `i`는 `Init_Dec_Option` 앞머리 `decoder.cpp:454` `int i;`로 이미 있고, `j`는 안쪽에서 선언한다. 성립한다.

판정: 문제 없음.

### B3-14 [반박됨] `mn`과 `MN`은 포인터가 아니며 프레임마다 원래 자리로 돌아온다

가설: `Select_BF`의 `mn += ITER_MAX_HBF`, `MN += ITER_MAX_HBF`가 포인터를 밀고, 되돌리는 곳이 없어 프레임이 거듭될수록 계속 밀린다.

증거 (반박됨):

- ㉮ `decoder.h:327-328`이 `int mn;`, `int MN;`이다. 포인터가 아니다. 배열은 `m_param_dec->MN`이고 이름만 겹친다
- ㉯ `decoder.cpp:1118` `MN = m_param_dec->MN[m_param_dec->MN_num - 1];`이 프레임마다 `MN`을 다시 세운다
- ㉰ `decoder.cpp:1120` `for (mn = 0; mn < MN + 1; mn++)`가 프레임마다 `mn`을 0으로 다시 세운다
- ㉱ `Select_BF`의 이동은 그 프레임 안에서만 유효하다

판정: 반박됨.

### B3-15 [반박됨] `syn_weight`, `psyn_weight`, `prev_CSW`는 `Clear_Flag`가 지우지 않지만 프레임마다 새로 정해진다

증거 (확인됨):

- ㉮ `syn_weight`와 `psyn_weight`는 `decoder.cpp:3443-3444`에서 `V2C_Store`(`decoder.cpp:2690`) 안, `iter == 0 && jj == m_PCM->N_b - 1 && ii == m_PCM->ColW[jj] - 1` 조건으로 계산된다. 복호 모드 조건이 없으므로 2SD와 3SD에서도 값이 채워진다
- ㉯ `prev_CSW`는 `decoder.cpp:3464-3465` `cur_chk_sum_weight = Compute_CSW(); Set_CSW(cur_chk_sum_weight);`에서 iteration마다 갱신된다. `Set_CSW` 정의는 `decoder.cpp:6680-6683`
- ㉰ `Select_BF`는 mn 루프 본문 **끝**(`decoder.cpp:1968-1970`)에서 `mn == 0`일 때 불린다. 위 계산보다 뒤다
- ㉱ `Get_Cur_LLR_Idx_FILE`는 `mn > 0`일 때만 불린다(`decoder.cpp:1136-1142`). `mn == 0`에서는 `decoder.cpp:1144` `cur_set_idx = 0;`이다. 즉 `cur_sw_branch_idx[]`가 정해지기 전에 읽히는 경로가 없다

판정: 반박됨 (앞 프레임 값이 새는 경로가 아니다).

같은 방식으로 확인한 나머지: `flag_BF_on`은 `decoder.cpp:609`가, `state_hd_error_floor_set`은 `decoder.cpp:614`가, `cnt_hd_error_floor`는 `decoder.cpp:615`가 프레임마다 지운다. `num_sw_branch[]`와 `syn_th_sw_branch[][]`는 `Init_Dec_Option`이 한 번만 채우는 상수라 프레임 초기화가 필요 없다. `MN_old`는 `Clear_Flag`가 지우지 않지만 읽는 곳(`decoder.cpp:4963`, `5353`)이 모두 `flag_dec_1iter == FLAG_HIGH` 안이고, 그 플래그를 켜는 곳(`decoder.cpp:5000`부터 `5266`까지 24곳)이 같은 자리에서 `MN_old = MN`을 함께 하므로 앞 프레임 값을 읽지 않는다.

### B3-16 [MEDIUM] `cur_sw_branch_idx[]`의 프레임 초기화가 `Select_BF` 안에만 있다

증거 (확인됨):

- ㉮ 수정 후 5.1은 `Select_BF` 앞머리에서만 `cur_sw_branch_idx[]`를 0으로 채운다. `Clear_Flag`(`decoder.cpp:606-616`)에는 없다
- ㉯ `Select_BF`가 안 불릴 수 있는 경로는 `decoder.cpp:1962-1965`의 `if (MODE_POWER_STOPPING_ON == m_param_dec->power_index) { if (TRUE == Jump_Iter(&mn)) break; }`뿐이다. 이것이 `Select_BF` 호출(`decoder.cpp:1968-1970`)보다 앞에 있다
- ㉰ AUTO에서는 `decoder.cpp:505-506`이 `m_param_dec->power_index = MODE_POWER_STOPPING_OFF;`로 못박아 그 갈래에 안 들어간다. [code_diff 1.2](../../code_diff.md#ch1_2)가 `ITER_MAX_HBF`의 갈래를 없애도 `decoder.cpp:505`의 `#if defined(__AUTO_LLR_OPT__)`는 그대로다

판정: 지금은 안전하되 근거가 컴파일 스위치 하나에 달려 있다. 심각도 MEDIUM.

처방 (코드 이동): 초기화를 `Clear_Flag`로 옮긴다. B3-12의 처방과 같은 자리이므로 한 번에 처리된다. 그러면 `Select_BF` 앞머리의 초기화는 남겨도 해가 없다.

### B3-17 [MEDIUM] `iter_num`은 프레임마다 초기화되지 않는다

증거 (확인됨):

- ㉮ `decoder.h:324` 선언. `Clear_Flag`에 없다
- ㉯ 대입은 `decoder.cpp:4965, 5077, 5105, 5205, 5273, 5344, 5355`뿐이고, 5344와 5355는 `Check_End_Iter` 안이다
- ㉰ 정상 흐름에서는 `Check_End_Iter`가 반드시 `iter_num = mn`을 하므로 문제가 없다. 그러나 `MN`이 음수가 되어 mn 루프(`decoder.cpp:1120`)가 한 번도 안 돌면 앞 프레임 값이 그대로 `decoder.cpp:1998` `*o_iter_num = iter_num;`으로 나간다. 그 앞 `decoder.cpp:1975-1977`의 `iter_num -= ITER_MAX_HBF;`까지 앞 프레임 값에 걸린다
- ㉱ `MN`이 음수가 되는 길은 B3-8의 곁가지에 적었다

판정: 확인됨. 심각도 MEDIUM (극단 입력에서만 도달한다).

### B3-18 [MEDIUM] code_diff 8.3이 다루는 블록은 저장소 상태로 컴파일되지 않는다

증거 (확인됨):

- ㉮ `decoder.cpp:1146`이 `#if defined (__RUN_PREPROCESSING__)`이고 `decoder.cpp:1156`이 그 `#endif`다. code_diff 8.3이 인용한 `decoder.cpp:1148-1150`이 그 안에 있다
- ㉯ `mode.h:63`이 `//#define __RUN_PREPROCESSING__`이다. 정의되지 않는다
- ㉰ [code_diff 8.3](../../code_diff.md#ch8)은 "`flag_BF_on`이 살아나면 조건이 저절로 맞는다"고만 적고 스위치가 꺼져 있다는 것을 말하지 않는다. [상위 문서 5.6](../../20260902_SW_branch_LLR_matrix.md) 표의 `decoder.cpp:1146-1156` 항목도 마찬가지다
- ㉱ 같은 스위치에 걸린 곳이 더 있다: `decoder.cpp:2303-2325`(`C2V_Cal_New_Sgn`의 `__RUN_PREPROCESSING__` 갈래, 꺼지면 `decoder.cpp:2320-2325`의 `#else`가 살아난다), `decoder.cpp:3480-3501`(`CNU_Remove_Old_Sgn`)

판정: 확인됨. 심각도 MEDIUM (문서 서술이 사실과 다르다).

처방 (문서): 8.3에 이 블록이 `__RUN_PREPROCESSING__`에 걸려 있고 저장소 `mode.h`에서는 꺼져 있음을 적는다.

---

## 5. 요약

| # | 심각도 | 영역 | 내용 | 처방이 요구하는 것 |
|---|--------|------|------|------------------|
| B3-1 | HIGH | ㉰ | AUTO 2SD와 3SD에서 고르는 그룹이 분기 1에서 분기 0으로 뒤집히고 row 12개가 도달 불가 | 동작 변경 또는 문서 결정 |
| B3-2 | MEDIUM | ㉰ | "2SD와 3SD는 분기 0 고정" 결정이 두 문서 어디에도 없음 | 문서 |
| B3-3 | MEDIUM | ㉰ | DAO가 2SD와 3SD를 실제로 돌린다 (B3-1의 위험이 실재) | 없음 (사실 확정) |
| B3-4 | MEDIUM | ㉰ | 3.2 파서가 분기 줄을 모드 무관하게 읽는다. 모든 모드 파일에 필요 | 문서 |
| B3-5 | 반박됨 | ㉰ | `iter - 1`은 설계다. 다만 8.1 병합으로 비AUTO SD restart 8곳 소실 | 없음 |
| B3-6 | LOW | ㉰ | Corner 이벤트가 모드 갈래 밖이라 SD에서도 켜진다 (스위치 꺼짐) | 동작 변경 |
| B3-7 | CRITICAL | ㉱ | `num_row` 0에서 6.2의 `return 0` 뒤 `LLR_MATRIX[0]` 역참조 | 코드 추가 |
| B3-8 | CRITICAL | ㉱ | `max_iter_end` 0에서 `MN_num` 0, `MN[-1]` 읽는 곳 22곳, `fr_4KB[-1]` 쓰기 | 코드 추가 |
| B3-9 | HIGH | ㉱ | 빈 그룹에서 `end_idx = start_idx - 1`, CSW 그룹은 다음 그룹 첫 row를 조용히 씀 | 코드 추가 |
| B3-10 | LOW | ㉱ | `num_row`와 `MN_num`의 대소는 무해. 상위 문서 5.1-4의 우려는 실체 없음 | 문서 |
| B3-11 | 사실 | ㉴ | 세 초기화 함수의 내용과 호출처 확정 | 없음 |
| B3-12 | HIGH | ㉴ | `Clear_Flag`의 612-613을 code_diff가 안 다뤄 빌드 불가 | 코드 삭제와 추가 |
| B3-13 | 문제 없음 | ㉴ | `syn_th_*` 네 이름의 참조는 모두 2.2와 4.1이 덮는다 | 없음 |
| B3-14 | 반박됨 | ㉴ | `mn`과 `MN`은 int이며 프레임마다 되돌아온다 | 없음 |
| B3-15 | 반박됨 | ㉴ | `syn_weight`, `psyn_weight`, `prev_CSW`는 프레임마다 새로 정해진다 | 없음 |
| B3-16 | MEDIUM | ㉴ | `cur_sw_branch_idx[]` 초기화가 `Select_BF` 안에만 있다 | 코드 이동 |
| B3-17 | MEDIUM | ㉴ | `iter_num`이 프레임마다 초기화되지 않는다 | 코드 추가 |
| B3-18 | MEDIUM | ㉴ | 8.3이 다루는 블록이 `__RUN_PREPROCESSING__`에 걸려 꺼져 있다 | 문서 |

CRITICAL 2, HIGH 3, MEDIUM 7, LOW 2, 반박됨 3, 사실 확인 1, 문제 없음 1.
