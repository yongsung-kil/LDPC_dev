# 워커 D_2 보고: 관점 5, `Select_BF`와 문턱 배열 (작성자 요청 4)

팀 D(디코더 분기 로직) 워커 2. 코드와 문서는 읽기만 했고 수정하지 않았다.

---

## 1. 확인 범위

- ㉮ 문서: 루트 `CLAUDE.md`, `context.md`, 상위 문서 `20260902_SW_branch_LLR_matrix.md`(2장 그룹표, 5.4, 7장 미결정), `code_diff.md`(2.2, 2.3, 3.2, 4.1, 5.1, 6.1), 루트 `msg1.md`
- ㉯ 소스: `decoder.cpp` 452-529(`Init_Dec_Option`), 606-631(`Clear_Flag`, `Clear_Iter_Start`), 1120-1156(mn 루프 시작과 `Get_Cur_LLR_Idx_FILE` 호출), 1766-1807(clk 루프 끝), 1944-1979(CRC 검사, 파워 스토핑, `Select_BF` 호출), 2082-2130(현재 `Select_BF`), 2618-2686(`V2C_Store`, `V2C_Store_HCU`), 3439-3444(`syn_weight` 대입), 4954-4993(`Jump_Iter`), 6359-6390(HCU 열 순회), 6973-7020(`Get_Cur_LLR_Idx_FILE`), 7310-7338(`Compute_SW`)
- ㉰ 소스: `common.h` 75-87(복호 모드, BF_mode), 193(`LAYOUT_PRIME_512B_TLC_VSS_OFF`), 200-252(SW 문턱 상수), 403-407(`ITER_MAX_HBF`), 717-732(flag enum). `decoder.h` 296-306. `corner.h` 69-87. `corner.cpp` 43, 119-126, 173-180, 225-227. `mode.h` 전체. `main.cpp` 139-162, 232, 499-508, 538, 586-632. `ecc_top.cpp` 208-229. `local_opt.cpp` 52-132
- ㉱ 입력 파일: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt` (12그룹, 헤더 3줄, 분기 줄 `0 0 1 0 1 1 -1 ...`)
- ㉲ 상수 값 (`common.h`, `__12META__` 미정의 갈래): `SW_TH_BF_DEFAULT` 630(231행), `SW_TH_BF0_512B_TLC_OFF` 680(236행), `SW_TH_BF1_512B_TLC_OFF` 130(237행), `SW_TH_5_8_SET0_DEFAULT` 960(240행), `SW_TH_5_8_SET0_512B_TLC_OFF` 1100(244행), `SW_TH_5_8_SET1_DEFAULT` 950(247행), `SW_TH_5_8_SET1_512B_TLC_OFF` 950(251행)
- ㉳ 활성 스위치 (`mode.h`): `__AUTO_LLR_OPT__`는 21-22행에서 `__PROGRAM_MODE_REF_C__`이고 Windows가 아닐 때만 정의. `__CORNER_CHECKER__`(75행), `__12META__`(11행), `__RUN_PREPROCESSING__`(63행)은 주석 처리되어 미정의

---

## 2. syn_weight 구간별 분기 표

수정 후 코드(`code_diff.md` 4.1, 5.1)를 HD 모드에 손으로 넣은 결과이다. 수정 전 열은 현재 소스의 비AUTO 갈래(`decoder.cpp:2086-2128`)를 따른다. 현재 AUTO 갈래는 `flag_BF_on = FLAG_LOW`만 하고(`decoder.cpp:2084-2085`) 분기를 고르지 않으므로 비교 대상은 비AUTO 갈래이다. 수정 전 `flag_HD_1_4_Set`이 "미대입"인 행은 `Clear_Flag`(`decoder.cpp:612`)가 넣은 `FLAG_LOW`(=0)가 남아 있으며, `FLAG_HD_1_4_SET_TYPE_0`도 0이라(`common.h:718`) 값으로는 구분되지 않는다.

`Select_SW_Branch(span, w)`는 `i = 0..num-2`에서 `w < th[span][i]`인 첫 `i`를 돌려주고, 없으면 `num-1`을 돌려준다.

### 2.1 `LAYOUT_PRIME_512B_TLC_VSS_OFF` 갈래 (matrix_sel = 1)

설정값: `syn_th_BF0` = 680, `num_sw_branch` = {2, 2}, `th[0][0]` = 130, `th[1][0]` = 1100.

| syn_weight | BF 진입 (`w < 680`) | span 0 분기 (`w < 130 ? 0 : 1`) | span 1 분기 (`w < 1100 ? 0 : 1`) | 수정 전 `flag_BF_on` / `flag_HD_1_4_Set` / `flag_HD_5_8_Set` | 갈림 |
|---|---|---|---|---|---|
| 0 ~ 129 | 진입 | 0 | 0 | HIGH / TYPE_0 / TYPE_0 | 없음 |
| 130 ~ 679 | 진입 | 1 | 0 | HIGH / TYPE_0 / TYPE_0 | span 0 분기가 0에서 1로 바뀜 (iteration 1~4에서 그룹 2를 씀) |
| 680 ~ 1099 | 미진입, mn과 MN에 4를 더함 | 0 (초기값, 건너뛰는 구간이라 안 읽힘) | 0 | LOW / 미대입 / TYPE_0 | 없음 |
| 1100 이상 | 미진입, mn과 MN에 4를 더함 | 0 (초기값, 안 읽힘) | 1 | LOW / 미대입 / TYPE_1 | 없음 |
| BF_mode OFF, 모든 w | 미진입, mn과 MN에 4를 더함 | 0 (안 읽힘) | `w < 1100 ? 0 : 1` | LOW / 미대입 / `w < 1100 ? TYPE_0 : TYPE_1` | 없음 |

### 2.2 default 갈래 (matrix_sel이 1이 아닌 값)

설정값: `syn_th_BF0` = 630, `num_sw_branch` = {1, 2}, `th[0][0]` = 0(초기화 값, 분기가 하나라 안 읽힘), `th[1][0]` = 960.

| syn_weight | BF 진입 (`w < 630`) | span 0 분기 (분기 1개, 항상 0) | span 1 분기 (`w < 960 ? 0 : 1`) | 수정 전 `flag_BF_on` / `flag_HD_1_4_Set` / `flag_HD_5_8_Set` | 갈림 |
|---|---|---|---|---|---|
| 0 ~ 629 | 진입 | 0 | 0 | 판정 불가 (`syn_th_BF0` 미대입, 아래 ㉱) / TYPE_0 / TYPE_0 | 수정 전은 불확정, 수정 후는 진입으로 확정 |
| 630 ~ 959 | 미진입 | 0 (안 읽힘) | 0 | 판정 불가 / 미대입 / TYPE_0 | 위와 같음 |
| 960 이상 | 미진입 | 0 (안 읽힘) | 1 | 판정 불가 / 미대입 / TYPE_1 | 위와 같음 |
| BF_mode OFF, 모든 w | 미진입 | 0 (안 읽힘) | `w < 960 ? 0 : 1` | LOW / 미대입 / `w < 960 ? TYPE_0 : TYPE_1` | 없음 |

이 갈래에서 `LLR_MATRIX_1.txt`(iteration 1~4에 분기 0과 1)를 읽으면 `cur_sw_branch_idx[0]`이 항상 0이라 그룹 2(분기 1, iteration 1~4)는 어떤 프레임도 고르지 못한다. 오류 검사(`code_diff.md` 6.2)는 "고른 그룹이 없음"만 잡으므로 이 상황은 조용히 지나간다.

---

## 3. 근거 검토

### ㉯ 130(`SW_TH_BF1_512B_TLC_OFF`)을 span 0 문턱으로 쓰는 근거

- ㉠ 사실 확인: `syn_th_BF1`은 `decoder.h:303` 선언과 `decoder.cpp:468` 대입 두 곳뿐이고 읽는 곳이 없다. `FLAG_HD_1_4_SET_TYPE_1`(`common.h:719`)은 대입하는 곳이 없다. `decoder.h:302-303`의 주석 `// S-4 Set`이 iteration 1~4용 문턱임을 시사하는 유일한 단서다. 따라서 `code_diff.md` 2.2의 "준비해 둔 것으로 보인다"는 추정이며, 문서도 "보인다"로 적어 추정임을 드러내고 있다
- ㉡ 동작 변경 여부: 2.1 표의 130~679 행에서 드러난다. 수정 전은 BF 진입 프레임의 iteration 1~4가 항상 `FLAG_HD_1_4_SET_TYPE_0`(그룹 0, 1)이고, 수정 후는 syn_weight가 130 이상이면 분기 1(그룹 2)을 쓴다. `LLR_MATRIX_1.txt`가 그 구간에 분기 둘을 두었으므로 고르는 동작 자체는 필요하지만, 문턱 값 130을 그 자리에 쓰는 것은 코드 어디에도 없던 동작이다. `code_diff.md` 5.1 바뀐 점 ㉯는 "고르는 동작이 필요하다"까지만 말하고 130이 새 동작임은 말하지 않는다
- ㉢ 배경 메모와의 관계: `msg1.md` 21-22행은 "bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리하는거야", 예시는 `1/4/-1`이다. 즉 배경 메모는 iteration 1~4에 분기가 없다고 말한다. 반면 `LLR_MATRIX_1.txt` 11행은 iteration 1~4에 분기 0, 0, 1을 둔다. 두 근거가 어긋나는데 상위 문서 7장 미결정에는 이 항목이 없다
- ㉣ 파일이 낮은 SW 쪽 분기를 알려주는가: `LLR_MATRIX_1.txt`의 헤더(10-11행)와 row 마지막 4칸(CSW, iter_start, iter_end, 분기)에 SW 방향을 나타내는 칸은 없다. 분기 0이 낮은 SW 쪽이라는 것은 관례이며, 기존 span 1 동작(`syn_weight < syn_th_5_8_Set_0`이면 TYPE_0, `decoder.cpp:2099-2100`)과 `msg1.md` 13-16행의 오름차순 나열이 그 관례를 뒷받침한다. 파일 자체로는 확인할 수 없다

### ㉰ "문턱은 오름차순" 전제와 실제 상수

- ㉠ 활성 갈래(`common.h:230-251`)의 값은 SET0 1100 > SET1 950(TLC_OFF), SET0 960 > SET1 950(DEFAULT)이다. 두 갈래 모두 내림차순이다. `__12META__` 갈래(`common.h:200-227`)는 620 < 870, 950 < 1270으로 오름차순이지만 미정의다
- ㉡ 현재 소스에서는 `syn_th_5_8_Set_1`이 대입만 되고(`decoder.cpp:489, 492`) 읽히지 않으므로(583행 주석 처리된 printf뿐) 내림차순이어도 동작에 영향이 없다. 수정 후 코드도 분기가 둘이라 `th[1][0]`만 읽는다. 지금은 문제가 없다
- ㉢ `code_diff.md` 4.1의 "SW_TH_5_8_SET1_*은 분기가 셋 이상일 때 syn_th_sw_branch[1][1]에 들어간다"를 그대로 따라 3분기를 만들면 아래와 같이 분기 1이 죽는다 (`th[1]` = {1100, 950}, `num_sw_branch[1]` = 3)

| syn_weight | i=0: `w < 1100` | i=1: `w < 950` | 반환 | 기대(오름차순이었다면 950, 1100) |
|---|---|---|---|---|
| 900 | 참 | 안 봄 | 0 | 0 |
| 1000 | 참 | 안 봄 | 0 | 1 |
| 1200 | 거짓 | 거짓 | 2 | 2 |

분기 1을 돌려주는 syn_weight가 없다. `i=1` 검사에 도달하려면 `w >= 1100`이어야 하는데 그때 `w < 950`은 항상 거짓이다. SET1 값을 `[1][1]`에 넣으려면 값을 오름차순으로 바꾸거나 넣는 자리를 바꿔야 하며, 문서의 한 문장만으로는 성립하지 않는다

### ㉱ default 갈래의 분기 수와 실제 matrix_sel

- ㉠ `num_sw_branch[0] = 1`(`code_diff.md` 4.1 465행)이면 `Select_SW_Branch(0, w)`는 루프를 돌지 않고 0을 돌려준다. 파일이 iteration 1~4에 분기 둘을 두어도 분기 1 그룹은 후보에서 빠진다(6.1의 `group_branch != cur_sw_branch_idx[span]`). 문서는 이 갈래에서 파일과 어긋난다는 말을 하지 않는다
- ㉡ 대조 검사: `code_diff.md` 4.1의 "num_sw_branch[]를 파일에서 읽은 값과 대조하는 검사를 넣으면"은 제안 문장이고 코드가 없다. `PARAM_LLR`(2.1)에는 구간별 분기 수 필드가 없어서 대조할 값 자체가 아직 없다. 3.4의 헤더와 row 대조 검사는 그룹 수와 row 수를 맞추는 것이라 분기 수는 다루지 않는다
- ㉢ default 갈래 도달 여부: `main.cpp:139`에서 `matrix_sel = atoi(argv[1])`. AUTO 갈래(`main.cpp:141-153`)는 `argc > 19`이면 `Get_H_Filename(argv[19])`로 임의 `matrix_sel`을 허용하고, 아니면 1만 허용한다. 비AUTO(`main.cpp:155-162`)와 `Set_H_Filename`(586-632)은 1만 채운다. TV_Gen(499-508)은 1 이상을 받는다. 따라서 AUTO 빌드에서 H 파일 인자를 주면 default 갈래에 들어갈 수 있다. `Jump_Iter`(`decoder.cpp:4972`)와 출력 보정(1973)도 `matrix_sel == 1`을 조건으로 하므로 default 갈래는 BF 관련 동작이 원래부터 일관되지 않은 갈래다
- ㉣ 수정 전 `syn_th_BF0`: default 갈래는 `syn_th_BF`(`decoder.cpp:472`)만 대입하고 `syn_th_BF0`는 대입하지 않는다. `syn_th_BF0` 대입은 467행 한 곳뿐이므로 default 갈래에서는 값이 불확정인 채 2088행에서 읽힌다. 수정 후는 `SW_TH_BF_DEFAULT`(630)를 넣어 확정한다. 이것은 동작 변경(불확정을 확정으로)이며 문서에 서술이 없다

### ㉲ 비HD 모드

- ㉠ 1.5SD: 수정 전(`decoder.cpp:2113-2128`)과 수정 후(5.1 572-577행)가 같다. `psyn_weight`로 span 1을 고르고 mn과 MN에 `ITER_MAX_HBF`를 더한다. 단 `syn_th_5_8_Set_0` 대신 `th[1][0]`을 읽으므로 값은 2.1, 2.2 표와 같다. 문제 없음
- ㉡ 2SD, 3SD: 수정 후는 `cur_sw_branch_idx[]`를 모두 0으로 두고 `flag_BF_on = FLAG_LOW`만 한다. mn은 옮기지 않으므로 iteration 1부터 돈다(수정 전과 같음). 수정 전 AUTO 갈래는 flag를 보지 않고 iteration 범위만으로 그룹을 골랐으므로(`decoder.cpp:6980-6999`), 분기가 있는 파일에서는 뒤에서부터 훑는 순서가 결과를 정했다. 수정 후는 분기 0으로 고정된다. 2SD, 3SD에서 SW 분기를 쓰지 않는다는 결정은 타당하지만 `code_diff.md` 5.1 바뀐 점에는 이 모드의 동작이 적혀 있지 않다
- ㉢ 2SD, 3SD에서 `Event_Flag(IDX_FLAG_HD_5_8_SET_TYPE_0)`이 새로 찍힌다 (아래 ㉳)

### ㉳ Corner enum과 `Event_Flag`

- ㉠ 연속성: `corner.h:69-87`에서 `IDX_FLAG_HBF_ON` = 8, `IDX_FLAG_HD_5_8_SET_TYPE_0` = 9, `_1` = 10, `_2` = 11, `IDX_FLAG_HD_FLOOR_TYPE_0` = 12, `_1` = 13, `_2` = 14, `_3` = 15, `IDX_FLAG_LEN` = 16. `Print_Head`(`corner.cpp:173-180`)의 이름 순서도 같다. 분기 0, 1, 2까지는 문서 말대로 그대로 쓸 수 있다
- ㉡ 모든 모드에서 호출: 수정 후 5.1 581-583행은 조건 없이 `Event_Flag(IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1])`을 부른다. 수정 전은 HD와 1.5SD에서만 부르고 2SD, 3SD, 그리고 AUTO 빌드에서는 부르지 않는다(`decoder.cpp:2084-2085`). 수정 후는 2SD, 3SD, BF_mode OFF에서도 TYPE_0을 찍으므로 Corner 통계의 의미가 바뀐다. `__CORNER_CHECKER__`가 미정의라 지금은 컴파일에 들어가지 않는다
- ㉢ 분기 넷 이상: `cur_sw_branch_idx[1]`이 3~6이면 12~15, 즉 `IDX_FLAG_HD_FLOOR_TYPE_0~3`에 겹친다. 7 이상이면 16 이상이 되어 `m_flag = new int[IDX_FLAG_LEN]`(`corner.cpp:43`, 16칸) 밖에 쓴다. `Event_Flag`(`corner.cpp:119-126`)는 범위 검사가 없다. `MAX_SW_BRANCH` = 9라 분기 index는 8까지 가능하다. 문서는 "넷 이상이면 자리를 늘려야 한다"고 적었지만 코드에 상한 검사가 없다. 지금 상수 설정(분기 2)에서는 도달하지 않는다
- ㉣ AUTO 빌드에서의 `__CORNER_CHECKER__`: `mode.h:75`가 주석이라 어느 빌드에서도 미정의다. `Event_Flag` 호출은 모두 `#if defined(__CORNER_CHECKER__)` 안에 있다

### ㉴ 호출 순서와 `syn_weight` 재설정

- ㉠ `syn_weight` 대입: `decoder.cpp:3439-3444`, `V2C_Store(jj, ii, iter, ...)` 안에서 `iter == 0`, `jj == N_b - 1`, `ii == ColW[jj] - 1`일 때 `syn_weight = Compute_SW(TRUE)`로 대입한다. 누적이 아니라 대입이므로 프레임마다 재설정할 필요가 없다. `Clear_Iter_Start`(621-631)와 `Clear_Flag`(606-616)에 `syn_weight`가 없는 것이 문제가 되지 않는다
- ㉡ HCU 열 128(`N_b - 1`)은 G0, G1 두 번 방문한다(`Clk_Inc`, `decoder.cpp:6359-6363, 6386-6390`). `V2C_Store_HCU`(2646-2686)의 G1 갈래가 `ii = separate_v_deg .. ColW-1`을 덮으므로 `ii == ColW[jj] - 1` 조건은 mn 0의 G1 통과에서 만족한다. 이 시점은 clk 루프(1807행에서 끝) 안이다
- ㉢ `Select_BF` 호출: `decoder.cpp:1968-1970`, mn 0의 clk 루프가 끝난 뒤이다. 앞에 있는 `Check_End_Iter`는 mn 0에서 `CRC_flag = FLAG_HIGH`(1947-1948)로 건너뛰고, 파워 스토핑 `Jump_Iter`(1961-1964)는 AUTO에서 `MODE_POWER_STOPPING_OFF`(506행)라 `Select_BF`를 건너뛰는 break가 없다. 비AUTO도 509행에서 OFF다
- ㉣ `Get_Cur_LLR_Idx_FILE` 호출: `decoder.cpp:1136-1142`, `mn > 0`일 때 mn 루프 시작이다. 미진입이면 `Select_BF`에서 mn이 4가 되고 `for`의 `mn++`로 5가 되어 iteration 5의 그룹을 고른다. 순서는 syn_weight 계산 → `Select_BF` → `Get_Cur_LLR_Idx_FILE`로 성립한다. 문제 없음

### ㉵ `__12META__` 갈래

- ㉠ `common.h:200-227`에는 `SW_TH_BF0_512B_TLC_OFF`, `SW_TH_BF1_512B_TLC_OFF`가 없다(`SW_TH_BF_512B_TLC_OFF` 530만 있음). 현재 소스 `decoder.cpp:467-468`이 이미 이 두 이름을 쓰므로 `__12META__`를 켜면 지금도 컴파일이 깨진다. 수정 후 4.1은 같은 이름을 쓰므로 새로 깨지는 곳은 없다
- ㉡ `__12META__`는 `mode.h:11`에서 주석 처리되어 미정의다. 문제 없음 (기존과 같은 상태)

### ㉶ 4.1 루프 변수 `i`

- ㉠ `Init_Dec_Option`은 `decoder.cpp:454`에서 `int i;`를 선언한다. 4.1의 `for (i = 0; i < MAX_SW_SPAN; i++)`는 이 지역 변수를 쓴다. 안쪽 `for (int j = ...)`는 블록 안에서 선언한다. 문제 없음

---

## 4. 발견 목록

| 번호 | 심각도 | 구분 | 문제 | 위치 | 처방과 동작 변경 여부 |
|---|---|---|---|---|---|
| 1 | HIGH | 수정 후 코드의 결함 | 파서(3.2)는 구간 번호를 등장 순서로 매기고(첫 분기 0이 구간 0), `Select_BF`(5.1)와 `decoder.h` 주석(2.2)은 구간 0을 iteration 1~4, 구간 1을 iteration 5~8로 못박는다. 두 규칙이 묶여 있지 않다. `msg1.md` 31-34행 형태의 파일(`1/4/-1`, `5/8/0`, `5/8/1`, `5/8/2`)을 넣으면 iteration 5~8 그룹이 구간 0이 된다. 미진입 프레임은 `cur_sw_branch_idx[0]`이 초기값 0이라 syn_weight와 무관하게 항상 분기 0을 고르고, 진입 프레임은 문턱 130으로 분기를 고르며 분기 2는 어떤 프레임도 고르지 못한다. 오류 없이 틀린 row를 쓴다. 관점 3(팀 P)과 겹치지만 문턱 배열 쪽에서도 드러나므로 적는다 | `code_diff.md` 3.2 236-253행, 5.1 560-569행, 2.2 165행, `msg1.md:31-34` | 구간을 iteration 범위로 묶는다. 파서가 구간별 `iter_start`를 기록하고 `Select_BF`가 `iter_start <= ITER_MAX_HBF`인 구간을 BF 구간으로 삼거나, 파서가 "구간 0의 `iter_start`가 1이 아니면 오류"를 내게 한다. 코드 변경 필요, 동작 변경 있음(잘못된 선택을 오류나 올바른 선택으로 바꿈) |
| 2 | MEDIUM | 문서 서술 오류 (결정 누락) | 130을 iteration 1~4 분기 문턱으로 쓰는 것은 코드 어디에도 없던 새 동작이며 근거는 주석 `// S-4 Set` 하나뿐이다(3장 ㉯). `msg1.md` 21-22행은 iteration 1~4에 분기가 없다고 하고, `LLR_MATRIX_1.txt`는 그 구간에 분기 둘을 둔다. 이 상충과 130의 채택은 상위 문서 7장 미결정에 없다 | `code_diff.md` 2.2 172-174행, 4.1 459행, 5.1 바뀐 점 ㉯, 상위 문서 7장, `msg1.md:21-22, 31` | 7장에 "iteration 1~4 구간의 분기 존재 여부와 문턱 값(130 여부)"을 Decision 항목으로 올린다. 문서 수정, 코드 변경 없음. 결정에 따라 코드가 바뀔 수 있음 |
| 3 | MEDIUM | 문서 서술 오류 | "문턱은 오름차순이고"(4.1 449행, 5.1 538행)는 활성 상수와 어긋난다(1100 > 950, 960 > 950). "SET1은 분기가 셋 이상일 때 [1][1]에 들어간다"(4.1 473행)를 따르면 3장 ㉰의 표대로 분기 1이 죽는다. 지금 분기 2 설정에서는 `[1][0]`만 읽어 영향이 없다 | `code_diff.md` 4.1 449, 473-474행, 5.1 538행, `common.h:240, 244, 247, 251` | 오름차순은 배열에 넣는 값의 조건임을 밝히고, SET1 상수를 그대로 `[1][1]`에 넣을 수 있다는 문장을 지우거나 "값을 오름차순으로 다시 정해야 한다"로 고친다. 문서 수정. 3분기 도입 시에는 상수 값 변경(동작 변경) 필요 |
| 4 | MEDIUM | 수정 후 코드의 결함 (누락 커버리지) | default 갈래는 `num_sw_branch[0] = 1`인데 파일은 iteration 1~4에 분기 둘이다. 분기 1 그룹이 조용히 후보에서 빠진다. 4.1의 "대조하는 검사"는 코드가 없고, `PARAM_LLR`에 구간별 분기 수가 없어 대조할 값도 없다. default 갈래는 AUTO 빌드에서 `argc > 19`이면 도달한다(`main.cpp:141-153`) | `code_diff.md` 4.1 464-469, 476-477행, 2.1, 6.1 691-695행, `main.cpp:141-153` | 파서가 구간별 최대 분기 index + 1을 `PARAM_LLR`에 기록하고, `Init_Dec_Option` 뒤나 `Get_Cur_LLR_Idx_FILE` 진입 시 `num_sw_branch[span]`과 대조해 어긋나면 오류로 멈춘다. 코드 추가, 동작 변경(조용한 오선택을 오류로) |
| 5 | MEDIUM | 문서 서술 오류 (누락) | 수정 전 default 갈래는 `syn_th_BF0`를 대입하지 않아(`decoder.cpp:472`는 `syn_th_BF`) 2088행에서 불확정 값을 읽는다. 수정 후는 630을 넣는다. 불확정을 확정으로 바꾸는 것은 옳지만 동작 변경이며 문서에 서술이 없다 | `code_diff.md` 4.1 444행, `decoder.cpp:467, 472, 2088` | 4.1 설명에 "default 갈래의 `syn_th_BF0`는 지금 대입되지 않으며 630으로 확정한다"를 적는다. 문서 수정, 코드는 그대로 |
| 6 | LOW | 문서 서술 오류 (누락) | 2SD, 3SD에서 `cur_sw_branch_idx[]`가 모두 0으로 고정되어 분기 0 그룹만 후보가 되는 동작이 5.1 바뀐 점에 없다. 수정 전 AUTO는 flag를 보지 않고 훑는 순서로 골랐으므로 분기 파일에서는 결과가 달라질 수 있다 | `code_diff.md` 5.1 554-556, 578-580행, 바뀐 점 ㉮㉯㉰, `decoder.cpp:6980-6999` | 바뀐 점에 "2SD, 3SD는 분기 0으로 고정한다"를 적는다. 문서 수정, 코드는 그대로 |
| 7 | LOW | 수정 후 코드의 결함 (엣지) | `Event_Flag(IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1])`이 모든 모드에서 호출되어 2SD, 3SD, BF_mode OFF에서도 TYPE_0을 찍는다(통계 의미 변경). 분기 index 3~6은 `IDX_FLAG_HD_FLOOR_TYPE_*`에 겹치고 7 이상은 `m_flag[16]` 밖에 쓴다. `__CORNER_CHECKER__` 미정의라 지금은 비활성 | `code_diff.md` 5.1 581-583행, 바뀐 점 ㉰, `corner.h:69-87`, `corner.cpp:43, 119-126` | HD와 1.5SD 갈래 안으로 호출을 옮기고, `cur_sw_branch_idx[1] < 3`일 때만 찍거나 enum에 분기 전용 자리를 `MAX_SW_BRANCH`만큼 늘린다. 코드 변경, Corner 통계 외 동작 변경 없음 |

문제 없음으로 확인한 항목: ㉴ 호출 순서와 `syn_weight` 재설정, ㉵ `__12META__` 갈래 컴파일, ㉶ 루프 변수 `i`, ㉲ 중 1.5SD 등가성, ㉳ 중 enum 연속성과 이름 순서(분기 0~2 범위).

---

## 5. 작성자 요청 4 판정

**조건부 타당.**

문턱을 상수에서 배열로 옮기고 `Select_SW_Branch`로 첫 문턱 미만을 고르는 구조, 호출 순서(syn_weight 계산 → `Select_BF` → `Get_Cur_LLR_Idx_FILE`), 1.5SD 등가성, 기존 span 1 동작의 보존은 소스로 확인했고 타당하다. 다음 조건을 채워야 그대로 적용할 수 있다.

- ㉮ 구간 번호와 iteration 범위를 코드로 묶는다 (발견 1). 지금은 파일의 그룹 순서가 바뀌면 오류 없이 틀린 row를 쓴다
- ㉯ iteration 1~4 구간의 분기 존재와 문턱 130 채택을 Decision 항목으로 올려 결정을 받는다 (발견 2). `msg1.md`와 `LLR_MATRIX_1.txt`가 어긋난다
- ㉰ "문턱은 오름차순" 서술과 "SET1을 [1][1]에 넣는다" 서술을 실제 상수 값에 맞게 고친다 (발견 3)
- ㉱ 구간별 분기 수를 파일에서 읽어 `num_sw_branch[]`와 대조하는 검사를 제안이 아니라 코드로 넣는다 (발견 4)
- ㉲ default 갈래의 `syn_th_BF0` 확정과 2SD, 3SD의 분기 0 고정을 문서에 적는다 (발견 5, 6)
