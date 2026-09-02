# 리뷰 관점 도출 (에이전트 C)

> 대상: `20260902_SW_branch_LLR_matrix.md`(이하 상위 문서)와 `code_diff.md`
> 이 문서는 "어디를 무엇과 대조해야 하는지"만 적는다. 문제 판정은 다음 라운드가 한다.

## 관점 표

| # | 관점명 | 확인 항목 | 대상 파일/범위 |
|---|--------|-----------|----------------|
| 1 | 파일 해석 정합 | `LLR_MATRIX_1.txt`의 헤더와 row를 상위 문서 2장, 3장 표와 code_diff 3.2 표에 한 칸씩 대조. C++ 파서의 토큰 읽기 순서와 파일 줄 순서 대조 | `LLR_MATRIX_1.txt` 전체, 상위 2장, 3장, code_diff 3.2, `local_opt.cpp:52-115` |
| 2 | 배경 메모와 설계 방향 정합 | 루트 `msg1.md`가 말하는 BF 구간의 LLR matrix 취급, iteration 번호 셈법, 분기 구간 고정 여부가 문서의 설계와 같은 방향인지 | `msg1.md:9-36`, 상위 2장, 5.4, 7장 ㉰, code_diff 5.1 |
| 3 | 그룹 선택의 순서 독립성 | code_diff 6.1 루프에 분기 필터를 넣은 뒤에도 그룹 배치 순서를 바꾸면 결과가 달라지는 경우가 있는지. 표 5행을 손으로 재계산 | code_diff 6.1, `decoder.cpp:6973-7047` |
| 4 | 구간 번호 계산의 반례 | code_diff 3.2의 `prev_branch != 0` 규칙을 여러 헤더 배열에 적용해 구간 번호가 의도와 다르게 나오는 배열이 있는지 | code_diff 3.2, 상위 2장 읽는 규칙 ㉮㉯㉰㉱ |
| 5 | Select_BF와 분기 문턱 | BF 진입 시 span 0을 SW로 고르는 새 로직이 기존 `TYPE_0` 고정과 어떤 입력에서 갈리는지. 문턱 상수의 실제 값과 오름차순 가정 대조. 호출 시점 순서 | code_diff 4.1, 5.1, `decoder.cpp:459-493, 2082-2130, 1968-1970, 3443-3444`, `common.h:230-251` |
| 6 | ITER_MAX_HBF 딸림 목록 완전성 | 상위 5.5 표 12곳과 소스 grep 결과를 대조. 표 밖 히트가 AUTO 빌드에서 살아있는 코드인지, 0에서 4로 바뀌면 동작이 달라지는지 | 상위 5.5, code_diff 1.2, 7장, `decoder.cpp`, `local_opt.cpp`, `main.cpp`, `TV_Dec_Inter.cpp` 의 `ITER_MAX_HBF` 전 히트 |
| 7 | iteration 번호 체계와 MN 배열 | 파일의 iter 1~124가 디코더 `mn`과 어떻게 대응하는지. `MN[]` 보정과 `mn` 점프가 4로 바뀔 때 끝 iteration과 row 도달 범위 | `local_opt.cpp:116-131`, code_diff 3.5, `decoder.cpp:564, 1118-1120, 2097-2098, 2114-2115, 7583` |
| 8 | 제거되거나 개명되는 멤버의 참조 전수 | `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_*`, `floor_flag`, `FLAG_HD_*_SET_TYPE_*` enum을 참조하는 모든 곳이 code_diff에 들어 있는지 grep으로 대조 | code_diff 2.1, 2.2, 3.3, 5장 끝, `decoder.cpp:606-616, 459-493, 583`, `decoder.h:296-306`, `common.h:717-725`, `corner.h:79-81`, `corner.cpp:173-176` |
| 9 | 컴파일 스위치 조합별 영향 | `__AUTO_LLR_OPT__` 갈래를 없앤 함수들이 AUTO가 꺼진 빌드(Windows, TV_Gen)에서 어떤 포인터와 상수를 읽게 되는지. `__12META__`, `__RUN_MPI__`, `__HD_FLOOR_SET__`, `__CORNER_CHECKER__`, `__RUN_PREPROCESSING__` 조합 | `mode.h:18-27`, code_diff 5.1, 6.1, 8.1, 8.2, `ecc_top.cpp:197-230`, `main.cpp:102-131`, `common.h:200-252`, `decoder.cpp:1137-1141` |
| 10 | MPI rank별 파일 읽기 구조 | 각 rank가 `Read_LLR_info_Auto`를 직접 부르는지, Bcast가 `LLR_MATRIX`와 `CSW_thr`만 뿌리는 이유, code_diff 3.7 추가가 필요한지 무해한지 | `local_opt.cpp:27-51`, `local_opt.h`, `main.cpp:115-120`, `mode.h:21-26`, `mpi.cpp`, `5_DAO/DAO_spec.md` MPI 절, `5_DAO/3_run_DAO_mpi.bat` |
| 11 | `__AUTO_LLR_OPT__` 분류 검증 | 상위 6.3 "손대지 않아도 되는 곳" 각 항목을 열어 BF 부활과 분기 지원에 무관한지. 6.1 항목 중 code_diff에 장이 없는 것. 총 개수 대조 | 상위 6.1, 6.2, 6.3, `mode.h`, `common.h`, `ecc_data.h`, `decoder.h`, `decoder.cpp`, `ecc_top.cpp`, `ecc_top.h`, `main.cpp`, `random.cpp`, `random.h` 의 `__AUTO_LLR_OPT__` 전 히트 |
| 12 | 파일 읽기와 오류 처리의 견고성 | code_diff 3장 삽입 위치, `err` 변수의 후속 처리, 소멸자와 로그 출력의 새 필드 반영, code_diff 6.2의 `return 0` 의미 | code_diff 3.1~3.7, 6.2, `local_opt.cpp:10-26, 52-184`, `decoder.cpp:7048-7073` |
| 13 | 초기화 시점의 동작 | edge clear가 1과 5 두 지점이 될 때 BF 진입 프레임과 미진입 프레임 각각에서 무엇이 일어나는지. `Is_Iter_Type_Init`의 restart 미반영. 호출처의 인자 형태 | code_diff 8.1~8.3, `decoder.cpp:6538-6626, 1146-1156, 1821, 2310-2328, 3487-3504, 6454`, 호출처 `712, 726, 2578-2993, 5700-6139` |
| 14 | 상위 문서와 code_diff 상호 정합 | 줄 번호, 장 앵커, 같은 항목에 대한 두 문서의 서술이 일치하는지. 미결정 사항으로 남긴 것을 code_diff가 확정한 것처럼 쓰지 않았는지 | 상위 5.1~5.6, 7장, code_diff 서두 전제, 이름 표, 각 장 |
| 15 | 적용 순서의 단계별 정합 | code_diff 9장의 각 단계가 단독으로 빌드되는지, 3단계에서 "기존과 결과가 같아야 한다"는 주장이 성립하는지 | code_diff 9장, 2.2, 5.1, 6.1, `decoder.cpp:606-616, 6984-6999` |
| 16 | DAO 쪽 파급의 인지 | 상위 1장이 DAO 대응을 제외했는데, 4장 ㉮ 표기가 DAO가 읽고 쓰는 파일 포맷을 바꾼다. 영향 지점이 후속 작업으로 남겨졌는지 | 상위 1장, 4장, `5_DAO/SRC/DAO_LLR_MATRIX.py:476-536, 344`, `5_DAO/DAO_spec.md:37, 51, 94`, `5_DAO/Util/Mock_ECC.py:86-88`, `5_DAO/_pm/TODO.md` |
| 17 | 문서 작성 규칙 준수 | 줄표와 가운뎃점, 번호 기호, 약어 첫 등장 풀어쓰기, 긍정문, 입력 파일 성격 서술 금지, 링크 경로 유효성 | 두 문서 전체, 루트 `CLAUDE.md` 문장 작성 규칙, 글로벌 규칙 |

---

## 관점별 확인 항목

### 1. 파일 해석 정합 (작성자 요청 1)

- `LLR_MATRIX_1.txt` 1~16행을 `local_opt.cpp:61-100`의 `fscanf` 순서(num_para_each_set, num_dv, dv_from, dv_to, num_group, num_set_each_group, type_each_group, restart_num, restart_iter, max_value, min_value)에 한 토큰씩 맞춰 본다. 13행의 `0`이 `restart_num`으로 읽혀 `restart_iter` 루프가 0회 도는지 확인한다
- 파일 18~105행의 row 수(12개 그룹 합계 77)와 각 그룹의 row 수(`1 7 6 6 1 5 5 7 6 10 10 13`)가 상위 2장 표의 "row 수" 열과 같은지 센다
- 각 그룹의 첫 row와 마지막 row의 `iter_start`, `iter_end`(row의 뒤에서 세 번째, 두 번째 칸)가 상위 2장 표의 "iteration" 열과 같은지 본다. 그룹 0(1~1)과 그룹 2(1~4)처럼 같은 iteration을 덮는 그룹 쌍을 모두 찾아 표에 빠진 것이 없는지 본다
- row 마지막 칸(뒤에서 첫 번째)이 헤더 11행의 `{x}{y}` 중 `y`와 같은지 77개 row 전부 대조한다
- 상위 3장 표의 "CSW 나열" 열이 파일의 뒤에서 네 번째 칸과 같은지 대조한다. 그룹 0, 4, 6~11의 CSW 나열도 같은 방식으로 뽑아 3장의 "모두 GROUP_TYPE_CSW여야 한다"는 서술이 12개 그룹 전체에 성립하는지 본다
- 상위 2장의 읽는 규칙 ㉮~㉱(같은 값 연속, y 증가, y가 0으로 복귀, 분기별 내부 분할 자유)를 파일에 적용했을 때 code_diff 3.2 표의 구간 번호가 나오는지 재현한다
- C++ 파서는 `fscanf("%d")` 토큰 기반이고 `5_DAO/SRC/DAO_LLR_MATRIX.py:476-492`는 줄 index 기반이다. 빈 줄(파일 2, 4, 7, 9, 12, 14, 17, 19행 및 그룹 사이의 공백 행)이 두 파서에서 각각 어떻게 처리되는지 대조한다

### 2. 배경 메모와 설계 방향 정합

- `msg1.md:21`은 "bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리하는거야"라고 적고, `msg1.md:30-34`의 예시는 iteration 1~4가 `-1`, 5~8이 `0/1/2`다. 반면 `LLR_MATRIX_1.txt`와 상위 2장은 iteration 1~4에 분기 두 개(그룹 0, 1이 분기 0, 그룹 2가 분기 1)를 둔다. 두 자료 중 어느 쪽이 설계의 정본인지, 문서가 이 차이를 인지하고 있는지 본다
- `msg1.md:19-20`의 iteration 셈법(BF 진입 시 0,1,2,3,4,5..., 미진입 시 0,5,6,7...)이 code_diff 5.1의 `mn = mn + ITER_MAX_HBF` 처리와 `Get_Cur_LLR_Idx_FILE(mn)`의 인자와 맞는지 본다
- `msg1.md:13-17`의 SW 구간 정의(BF, normal0, normal1, normal2로 구간 개수 가변)와 code_diff 4.1의 `num_sw_branch[]`, `syn_th_sw_branch[][]` 구조가 대응하는지 본다. 특히 `msg1.md:14`는 normal0의 하한이 BF 문턱이므로, BF 미진입 프레임에서 span 1의 분기 0이 "BF 문턱 이상 SET0 미만"을 뜻하는지 code_diff 5.1의 `Select_SW_Branch(1, syn_weight)`와 대조한다
- `msg1.md:22`의 "bf 구간은 늘어나지 않아. 딱 1~4야"와 상위 7장 ㉰(분기 구간을 1~8로 못박을지 임의 구간을 허용할지)의 관계를 본다

### 3. 그룹 선택의 순서 독립성 (작성자 요청 2)

- code_diff 6.1 루프는 `g = num_group - 1`부터 내려오며 분기 필터를 통과한 첫 그룹을 잡는다. 다음 배치를 만들어 결과를 손으로 낸다
  - ㉮ `LLR_MATRIX_1.txt`의 그룹 순서를 뒤집은 파일 (그룹 11이 0번이 되게)
  - ㉯ 같은 분기, 같은 iteration 구간을 덮는 그룹이 둘 있는 파일 (파일 규약 위반이지만 파서가 막지 않는 경우)
  - ㉰ 분기 없는 그룹(-1)이 분기 있는 그룹과 같은 iteration을 덮는 파일 (예: 그룹 A가 1~8 분기 -1, 그룹 B가 5~8 분기 0)
  - ㉱ iteration 1에서 그룹 0(1~1, 분기 0)과 그룹 2(1~4, 분기 1) 중 `cur_sw_branch_idx[0]` 값별로 무엇이 잡히는지
- 필터의 `cur_sw_branch_idx[span]`에서 `span`이 `sw_span_idx_each_group[g]`다. 분기가 -1인 그룹은 필터를 건너뛰므로 `span = -1`을 index로 쓰는 경로가 없는지, 분기가 있는데 `span`이 `MAX_SW_SPAN` 이상이 되는 파일(구간이 5개 이상)에서 어떻게 되는지 본다
- 그룹의 분기 index가 `num_sw_branch[span]` 이상인 파일(헤더에 분기 3개, 문턱 배열은 2개)에서 그 그룹이 영원히 선택되지 않는지, 그것을 알리는 검사가 있는지 본다 (code_diff 4.1 마지막 문단은 검사를 "넣으면"이라고만 적었다)
- code_diff 6.1 표의 5행(iter 3, 6, 20)을 필터 순서대로 g=11부터 다시 따라가 "근거" 열의 서술과 맞는지 본다. iter 1, 5, 8, 9, 124의 경계도 같은 방식으로 추가한다

### 4. 구간 번호 계산의 반례 (작성자 요청 3)

- code_diff 3.2의 규칙(`b == 0 && prev_branch != 0`이면 새 구간)을 아래 헤더 배열에 적용해 나오는 구간 번호를 상위 2장 읽는 규칙에서 기대되는 값과 대조한다
  - ㉮ `0 0 1 0 1 1 -1 ...` (현재 파일)
  - ㉯ `0 -1 0 1` (분기 0 그룹 사이에 분기 없는 그룹이 끼는 경우)
  - ㉰ `0 1 1 0 0 1` (두 구간이 이어지고 각 분기가 여러 그룹으로 쪼개진 경우)
  - ㉱ `0 2` 또는 `1 2` (분기 index가 0에서 시작하지 않거나 건너뛰는 경우, 파일 규약 위반)
  - ㉲ `-1 -1 0 1` (분기 없는 그룹이 앞에 오는 경우)
  - ㉳ `0 1 -1 0 1` 에서 두 구간이 같은 iteration 범위를 덮는 경우 (구간 번호는 다르지만 iteration은 겹침)
- 상위 2장 ㉰ "y가 0으로 되돌아가면 새 구간이 시작되고 iteration은 앞 구간에서 이어진다"는 iteration 기반 정의이고, code_diff 3.2는 분기 index만 보고 iteration을 보지 않는다. 두 정의가 어긋나는 배열이 있는지 본다
- `num_sw_span`이 `MAX_SW_SPAN`(4)을 넘을 때 파서가 무엇을 하는지 본다
- 헤더의 `x`(분기 총수)를 파일에서 뺀 대신 "같은 iteration 구간을 덮는 서로 다른 분기 index의 개수"로 센다고 상위 4장 ㉮가 적었는데, code_diff에 그 셈이 실제로 들어 있는지, 아니면 `num_sw_branch[]`가 `Init_Dec_Option`의 상수에서만 오는지 본다

### 5. Select_BF와 분기 문턱 (작성자 요청 4)

- 기존 `decoder.cpp:2087-2095`는 BF 진입 시 `flag_HD_1_4_Set = TYPE_0`, `flag_HD_5_8_Set = TYPE_0`으로 고정한다. code_diff 5.1은 `cur_sw_branch_idx[0] = Select_SW_Branch(0, syn_weight)`, `[1] = Select_SW_Branch(1, syn_weight)`다. `common.h:236-244`의 값(`SW_TH_BF0_512B_TLC_OFF` 680, `SW_TH_BF1_512B_TLC_OFF` 130, `SW_TH_5_8_SET0_512B_TLC_OFF` 1100)을 넣어 `syn_weight`가 0~679일 때 두 span의 분기가 어떻게 갈리는지 표로 만들고, 기존 고정값과 다른 `syn_weight` 범위를 짚는다
- 상위 문서 4장과 code_diff 2.2가 `syn_th_BF1`(130)을 "iteration 1~4 구간의 분기 문턱으로 준비해 둔 것으로 보인다"고 추정한다. `decoder.h:302-303` 주석(`S-4 Set`)과 `decoder.cpp:460-472`의 주석 처리된 갈래에서 이 추정을 뒷받침하거나 반박하는 단서를 찾는다
- code_diff 4.1 주석은 "문턱은 오름차순"이라 적었다. `common.h:240-251`에서 `SW_TH_5_8_SET0_512B_TLC_OFF`(1100)와 `SW_TH_5_8_SET1_512B_TLC_OFF`(950), `SW_TH_5_8_SET0_DEFAULT`(960)와 `SW_TH_5_8_SET1_DEFAULT`(950)의 대소를 확인하고, `Select_SW_Branch`가 분기 셋 이상에서 이 값들로 어떻게 동작하는지 본다
- 기존 `decoder.cpp:472`의 `default` 갈래는 `syn_th_BF`에 대입하고 `syn_th_BF0`는 대입하지 않는다. code_diff 4.1은 `default`에서 `syn_th_BF0 = SW_TH_BF_DEFAULT`로 바꾼다. `LAYOUT_PRIME_512B_TLC_VSS_OFF`가 아닌 레이아웃에서 BF 진입 판정이 수정 전후로 같은지 본다
- code_diff 5.1의 `MODE_DEC_1_5SD` 갈래는 `psyn_weight`를, HD 갈래는 `syn_weight`를 쓴다. 기존 코드 `decoder.cpp:2099, 2116`과 같은 배정인지 본다. 그 밖의 모드(2SD, 3SD)에서 `else { flag_BF_on = FLAG_LOW; }`만 하고 `mn`을 밀지 않는 것이 기존 코드(해당 갈래 없음)와 같은 동작인지 본다
- 호출 순서: `syn_weight`는 `decoder.cpp:3443-3444`에서 iter 0의 마지막 column에서 계산되고, `Select_BF`는 `decoder.cpp:1968-1970`에서 `mn == 0` 루프 끝에 불리며, `Get_Cur_LLR_Idx_FILE(mn)`은 `decoder.cpp:1136-1138`에서 `mn > 0`일 때 루프 앞에서 불린다. `cur_sw_branch_idx[]`가 첫 사용 전에 확정되는지, BF 미진입 시 `mn`이 0에서 4로 밀린 뒤 `mn++`로 5가 되어 `Get_Cur_LLR_Idx_FILE(5)`가 불리는지 따라간다
- `Clear_Flag()`(`decoder.cpp:606-616`)가 프레임마다 불려 `flag_HD_*`를 지운다. code_diff 5.1은 `cur_sw_branch_idx[]`를 `Select_BF` 앞머리에서 0으로 지운다. 프레임 사이에 값이 남아 다음 프레임의 iter 0 동안 읽히는 경로가 있는지 본다
- Corner 이벤트: code_diff 5.1 끝의 `IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]`이 `corner.h:79-81`의 세 값과 `corner.cpp:173-176` 헤더 출력에 맞는지, 기존에는 BF 진입과 미진입에서 이벤트를 각각 냈는데 새 코드는 모드와 무관하게 한 번 내는 것이 corner 로그 해석을 바꾸는지 본다. `IDX_FLAG_HBF_ON`(`decoder.cpp:2074`)은 그대로인지 본다

### 6. ITER_MAX_HBF 딸림 목록 완전성 (작성자 요청 5)

- 상위 5.5 표의 12곳과 소스에서 `ITER_MAX_HBF`를 grep한 결과를 한 줄씩 대조한다. grep에서 표 밖에 잡히는 위치는 다음과 같다. 각 위치가 AUTO 빌드에서 컴파일되는 코드인지(감싸는 `#if` 확인), 0이 4로 바뀔 때 동작이 달라지는지 본다
  - `decoder.cpp:1448, 1622, 1828` (`__RUN_PARITY_SKIP__` 아래, `mn == ITER_MAX_HBF + 1`)
  - `decoder.cpp:1821` (Preprocessing 클럭 가산)
  - `decoder.cpp:2169, 2190` (`__DUAL_UPDATE__` 양쪽 갈래)
  - `decoder.cpp:7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018` (`MN_size` 계산, 표에는 7583만 있음)
  - `main.cpp:719` (`#ifndef __AUTO_LLR_OPT__` 아래)
  - `TV_Dec_Inter.cpp:1077, 1221, 1295, 1487, 1535`
  - `local_opt.cpp:126, 129` (표에 있음, 값 변화의 효과는 관점 7)
- 상위 5.5 두 번째 표의 `iter <= 4` 네 곳이 code_diff 7장의 네 곳과 같은 줄인지, 그 밖에 `iter <= 4`나 `mn <= 4` 같은 상수가 AUTO 갈래에 더 있는지 grep한다
- `decoder.cpp:6454`(`mn == 4 + ITER_MAX_HBF || mn == 3 + ITER_MAX_HBF`)와 `TV_Dec_Inter.cpp`의 같은 식이 4로 바뀌면 skip column read 시점이 iteration 7, 8로 옮겨지는데, 이것이 BF 미진입 프레임(mn이 5부터)과 진입 프레임에서 각각 의도된 iteration인지 본다

### 7. iteration 번호 체계와 MN 배열

- `local_opt.cpp:116-123`(code_diff 3.5)은 `MN_num = 최대 iter_end`(124), `MN[i] = i`, `MN[MN_num-1] = 124`로 채운다. 이어서 `local_opt.cpp:124-131`이 HD와 1_SSD에서 `MN[i] -= ITER_MAX_HBF`, `MN[0] = ITER_MAX_HBF`를 한다. `ITER_MAX_HBF`가 4가 되면 `MN[MN_num-1]`이 120이 된다. `decoder.cpp:1118-1120`은 `MN = m_param_dec->MN[MN_num-1]`로 루프 상한을 잡고, `Select_BF`는 BF 미진입 시 `MN += 4`한다. BF 진입 프레임은 mn 1~120, 미진입 프레임은 mn 5~124를 도는지 계산하고, 파일의 row 121~124가 어느 프레임에서 쓰이는지 본다
- `main.cpp:704-724`의 `MN[]`은 단계별 최대 iteration(5개 원소)이고 `local_opt.cpp`의 `MN[]`은 `MN[i] = i`다. 두 의미가 다른 채로 `decoder.cpp:564, 587, 1118, 7583`이 같은 식 `MN[MN_num-1]`을 쓰는데, 이 문서 범위에서 그 의미 차이가 영향을 주는 곳이 있는지 본다
- `local_opt.cpp:124`의 조건은 `MODE_DEC_HD || MODE_DEC_1_SSD`이고 `Select_BF`의 `mn` 밀기 조건은 `MODE_DEC_HD || MODE_DEC_1_5SD`다. `1_SSD`와 `1_5SD`가 같은 상수인지 `common.h`에서 확인한다
- `decoder.cpp:1973-1979`는 BF 미진입 시 `iter_num -= ITER_MAX_HBF`로 통계를 보정한다. 4가 되면 결과 파일의 평균 iteration(`local_opt.cpp:50`, `ecc_top.cpp` 결과 출력)이 바뀌는데 상위 6.3이 이 영향을 "손대지 않아도 되는 곳"으로 둔 근거를 본다

### 8. 제거되거나 개명되는 멤버의 참조 전수

- 다음 이름을 소스 전체에서 grep해 code_diff에 수정 전후가 실린 줄과 대조한다. 실리지 않은 참조를 목록으로 만든다
  - `flag_HD_1_4_Set`, `flag_HD_5_8_Set`: `decoder.h:297-298`, `decoder.cpp:612-613`(`Clear_Flag`), `2090-2123`, `7002-7016`
  - `FLAG_HD_1_4_SET_TYPE_*`, `FLAG_HD_5_8_SET_TYPE_*`: `common.h:717-725`, `decoder.cpp:2090-2123, 7002-7016`
  - `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1`: `decoder.h:301-306`, `decoder.cpp:459-493, 583`(주석)
  - `floor_flag`: `ecc_data.h:197`, `local_opt.cpp:105, 114, 178`
  - `IDX_FLAG_HD_5_8_SET_TYPE_*`: `corner.h:79-81`, `corner.cpp:174-176`, `decoder.cpp:2093-2125`
- `PARAM_LLR`에 추가되는 `num_sw_span`(스칼라)과 두 배열이 `decoder.h:210`의 포인터를 통해 `Decoder`에서 읽히는 경로 외에 `ecc_top.h:94`, `ecc_top.cpp`에서 구조체를 복사하거나 크기를 가정하는 곳이 있는지 본다
- `Decoder`에 추가되는 `cur_sw_branch_idx[]`, `num_sw_branch[]`, `syn_th_sw_branch[][]`가 `Init_Dec_Option`(code_diff 4.1) 외에 생성자나 `Alloc_Dec`에서 초기화가 필요한 위치가 있는지, `Init_Dec_Option`이 `Select_BF`보다 먼저 불리는지 `ecc_top.cpp:208-209, 228-229`에서 본다

### 9. 컴파일 스위치 조합별 영향

- `mode.h:18-27`: Windows에서는 `__AUTO_LLR_OPT__`가 정의되지 않고, 비Windows이면서 `__PROGRAM_MODE_REF_C__`일 때만 정의된다. `__RUN_MPI__`는 `mode.h:23-25`가 AUTO가 정의된 직후 `!defined(__AUTO_LLR_OPT__)`를 검사하므로 이 파일 안에서는 켜지지 않는다. 실제 빌드가 다른 곳(컴파일 인자)에서 `__RUN_MPI__`를 켜는지 본다 (관점 10과 연결)
- code_diff 8.1, 8.2가 `#else` 갈래(matrix_sel별 하드코딩)를 지우고 AUTO 갈래만 남긴다. 남는 코드는 `m_param_LLR->restart_num`을 읽는다. AUTO가 꺼진 빌드의 진입점 `main.cpp:105, 127`은 4인자 `Init_ECC_Top`(`ecc_top.cpp:197-210`)을 부르고, 이 함수는 `m_param_LLR`을 대입하지 않은 채 `m_dec.Init_Dec(..., m_param_LLR, ...)`에 넘긴다. 통일본이 이 빌드에서 어떤 포인터를 역참조하는지 본다
- code_diff 6.1이 `Get_Cur_LLR_Idx_FILE`의 `#else` 갈래를 지우는데, `decoder.cpp:1137-1141`에서 이 함수는 AUTO에서만 불리고 그 밖에는 `Get_VNU_Table_Idx`(`decoder.cpp:7207-7210`, `return 0`)가 불린다. 하드코딩 제거가 AUTO가 꺼진 빌드의 동작을 바꾸는지, 상위 7장 ㉱의 미결정이 실제로 무엇을 가르는지 본다
- code_diff 5.1이 `Select_BF`의 `#if AUTO` 갈래를 없애므로 AUTO가 꺼진 빌드도 새 `Select_BF`를 탄다. 그 빌드에서 `num_sw_branch[]`와 `syn_th_sw_branch[][]`가 `Init_Dec_Option`에서 채워지는지(code_diff 4.1은 스위치 없이 삽입) 본다
- `common.h:200-252`: `__12META__`가 켜지면 `SW_TH_BF0_512B_TLC_OFF`, `SW_TH_BF1_512B_TLC_OFF`가 정의되지 않는다. code_diff 4.1이 이 두 이름을 쓴다. `__12META__` 조합에서의 빌드를 본다
- `__HD_FLOOR_SET__`이 꺼져 있을 때 `Adjust_HD_Floor_Type`(`decoder.cpp:8108-8114`)이 양쪽 갈래에서 같은 값이므로 상위 6.3이 제외했다. `__HD_FLOOR_SET__`이 켜진 빌드에서 `Get_Cur_LLR_Idx_FILE` 앞머리의 호출(`decoder.cpp:6980-6983`)이 분기 선택에 간섭하는지 본다
- `__RUN_PREPROCESSING__`(code_diff 8.3), `__CORNER_CHECKER__`(code_diff 5.1), `__DUAL_UPDATE__`(`decoder.cpp:2169, 2190`) 각각 켜짐과 꺼짐에서 수정 후 코드가 빌드되고 의도대로 도는지 본다

### 10. MPI rank별 파일 읽기 구조 (작성자 요청 7)

- `local_opt.cpp:27-35`: `Run_Local_Opt`가 rank 검사 없이 `Read_LLR_info_Auto`를 부르고, `Read_LLR_info_Auto`(`local_opt.cpp:59-60`)는 rank와 무관하게 `fopen`한다. 결과 로그만 `ID_ROOT`가 쓴다(`local_opt.cpp:133`). 각 rank가 파일을 따로 읽는 구조인지 이 흐름으로 판정한다
- 그럼에도 `local_opt.cpp:38-44`가 `LLR_MATRIX`와 `CSW_thr`만 Bcast하는 이유를 찾는다. `Run_Simu_Curr_LLR`의 호출자가 `Run_Local_Opt` 하나뿐인지 grep하고, `local_opt.h`에 root가 매트릭스를 고쳐 다시 도는 루프(옛 최적화기)의 흔적이 있는지 본다. root만 매트릭스를 바꾸고 재전파하는 설계였다면 새 헤더 배열도 같이 실어야 하는지, 각 rank가 파일을 다시 읽는 설계라면 3.7이 무해한 중복인지 결론을 낸다
- `5_DAO/DAO_spec.md`의 MPI 절과 `5_DAO/3_run_DAO_mpi.bat`: 지금 DAO는 Python 쪽에서 rank를 나누고 C++ EXE를 rank마다 따로 띄운다. 이 구조에서 C++ 안의 `__RUN_MPI__`가 켜지는지(관점 9의 `mode.h:21-26`)와, 켜지지 않으면 code_diff 3.7 전체가 컴파일되지 않는 코드인지 본다
- `mpi.cpp`에서 `PARAM_LLR`이나 `PARAM_DEC`를 통째로 보내는 별도 경로가 있는지 grep한다

### 11. `__AUTO_LLR_OPT__` 분류 검증 (작성자 요청 6)

- 소스 전체에서 `__AUTO_LLR_OPT__`를 grep해 히트 수가 상위 6장이 말하는 86곳과 맞는지 센다. 6.1, 6.2, 6.3 세 표의 항목 수 합과도 맞춘다
- 6.3 표의 각 항목을 열어 다음 기준으로 다시 분류한다
  - ㉮ BF가 살아나면(`flag_BF_on`이 HIGH가 될 수 있으면) 동작이 바뀌는 곳인지 (예: `decoder.cpp:1917-1921` CSW 로그 수집이 BF iteration에서도 도는지, `decoder.cpp:1929` 로그 조건)
  - ㉯ `ITER_MAX_HBF`가 4가 되면 값이 바뀌는 곳인지 (예: `ecc_top.cpp:652, 680, 944-950` 결과 출력의 iteration 통계, `main.cpp:706` `Set_Ref_C_Iteration`이 AUTO에서 통째로 빠지는데 `MN` 배열은 어디서 채워지는지)
  - ㉰ `decoder.cpp:505-510` power stopping OFF 고정이 `Jump_Iter`(`decoder.cpp:1961-1964`)와 분기 선택의 상호작용을 끊는지
  - ㉱ `decoder.cpp:8109-8113` `Adjust_HD_Floor_Type`의 두 갈래가 같은 값이라는 서술이 `__HD_FLOOR_SET__` 꺼짐에서만 성립하는지
- 6.2의 다섯 곳(`decoder.cpp:3985-3990` 외)이 `Get_VNU_LLR_SET_FILE`에 `cur_set_idx`를 넘기는 형태가 같은지, 분기로 고른 row가 이 다섯 경로 모두에 닿는지 본다
- 6.1의 `decoder.cpp:1137-1141`(`Get_Cur_LLR_Idx_FILE` 대 `Get_VNU_Table_Idx` 갈림)은 "고쳐야 하는 곳"에 있지만 code_diff에 해당 장이 없다. 고치는 내용이 무엇인지, 아니면 분류가 6.2나 6.3으로 옮겨져야 하는지 본다

### 12. 파일 읽기와 오류 처리의 견고성

- code_diff 3.1의 할당이 `num_group`을 읽은 뒤(`local_opt.cpp:73-74`)인지, 3.2의 읽기가 `type_each_group` 루프 뒤이고 `restart_num` 읽기(`local_opt.cpp:85`) 앞인지, 3.4의 검사가 row 루프(`local_opt.cpp:106-115`)가 끝나 `sw_branch_idx[]`가 다 찬 뒤인지, 삽입 위치를 원본 줄 번호로 확정한다
- code_diff 3.4가 `err = TRUE`를 세우는데, 원본에서 `err`는 `local_opt.cpp:139-141`에서 파일 열기 실패에만 쓰이고 그 뒤 아무것도 하지 않는다. 새 검사가 걸렸을 때 실행이 멈추는지, 계속 진행하면 어느 값으로 복호하는지 본다
- 원본 `local_opt.cpp:60-61`은 `fopen` 결과를 검사하지 않고 바로 `fscanf`한다. 새 형태 파일이 아닌 옛 파일(분기 줄이 없는 파일)을 넣었을 때 3.2의 새 루프가 무엇을 읽어 가는지(`restart_num` 자리의 값이 분기 index로 들어가고 그 뒤가 한 줄씩 밀리는 흐름) 따라가고, 이를 잡는 검사가 있는지 본다
- 3.6 소멸자: 원본 `local_opt.cpp:10-26`에 없던 `floor_flag` 해제가 추가된다. `LOCAL_OPT`가 `Read_LLR_info_Auto`를 부르지 않고 소멸되는 경로(파일 열기 실패 등)에서 초기화되지 않은 포인터를 `delete[]`하는지 본다 (원본 생성자 `local_opt.cpp:3-9`는 `m_param_LLR` 포인터를 초기화하지 않는다)
- 3.3 끝의 "178행의 로그 출력도 같은 이름으로 바꾼다" 외에, `local_opt.cpp:151-155`의 `type_each_group` 출력 패턴처럼 새 헤더 줄(`sw_branch_idx_each_group`, `sw_span_idx_each_group`, `num_sw_span`)을 결과 로그에 내보내는 항목이 있는지 본다
- code_diff 6.2: `selected_group == -1`이면 `return 0`한다. 반환값 0은 "첫 row"라서 상위 3장이 지적한 "오류 없이 항상 첫 row를 쓰는 것"과 겉으로 같은 결과다. 오류 출력이 함께 나가므로 구별되는지, 호출자 `decoder.cpp:1138`이 반환값으로 오류를 알 수 있는지 본다. `table_row_idx = -1` 초기값으로 바뀐 뒤 `GROUP_TYPE_ITER` 갈래에서 어느 row도 안 맞을 때의 흐름도 본다

### 13. 초기화 시점의 동작

- code_diff 8.1 통일본에서 HD와 1.5SD는 `iter == 0, 1, ITER_MAX_HBF + 1`에서 edge clear다. `ITER_MAX_HBF`가 4일 때, BF 진입 프레임은 mn 1도 돌고 mn 5도 도니 두 번 clear되고, 미진입 프레임은 mn 5부터 도니 한 번 clear된다. 이것이 AUTO가 꺼진 원본 `decoder.cpp:6567-6576`(같은 조건, `ITER_MAX_HBF` 4)과 동일한 동작인지 확인해, "BF를 살리면 원래 동작으로 돌아간다"는 문서의 전제를 뒷받침한다
- code_diff 8.1은 `Is_Iter_Type_Edge_Clear`의 호출처 중 `decoder.cpp:2328`이 `iter - 1`을 넘긴다. `iter == 5`가 clear 지점이 되면 `iter == 6`에서 old_sgn을 읽지 않는 SD 규칙이 HD에도 걸리는지, 그 호출이 어느 모드 갈래 안에 있는지 본다
- code_diff 8.2 `Is_Iter_Type_Init`: HD와 1.5SD에서 `iter == 0`만 본다. `decoder.cpp:6604` 주석을 근거로 의도라 했는데, restart가 있는 파일(`restart_num > 0`)에서 HD 복호가 restart iteration에 min값과 sgn을 초기화하지 않아도 되는지, AUTO가 꺼진 원본 갈래(`decoder.cpp:6627-6640` 부근)가 어떻게 하는지 대조한다
- code_diff 8.3 Preprocessing: `decoder.cpp:1146-1156`은 `flag_BF_on`이 HIGH면 mn 1, LOW면 mn 5에 `Preprocessing()`을 부른다. `flag_BF_on`은 `Select_BF`(mn 0 끝)에서 정해지고 이 검사는 mn 루프 앞머리이므로 mn 1에서 이미 확정돼 있는지 본다. `decoder.cpp:1817-1823`(클럭 가산)과 `2310-2312, 3487-3489`(`Intentional_Blank`)가 같은 시점 규칙을 쓰는지 본다
- `decoder.cpp:6454`와 `TV_Dec_Inter.cpp:1077` 계열(`mn == 4 + ITER_MAX_HBF || mn == 3 + ITER_MAX_HBF`)이 `__RUN_ITER34_HIGH_DV_SKIP__` 같은 스위치 아래인지, 4가 되면 mn 7, 8이 되는 것이 BF 진입 프레임에서 iteration 7, 8을 뜻하는지 본다

### 14. 상위 문서와 code_diff 상호 정합

- 줄 번호: 상위 5.4는 `Select_BF`를 `2084-2130`, code_diff 5.1은 `2082-2130`. 상위 5.6은 `Is_Iter_Type_Edge_Clear`를 `6541-6565`, code_diff 8.1은 `6538-6598`. 상위 5.6은 `Is_Iter_Type_Init`을 `6609-6626`, code_diff 8.2는 `6606-6626`. 상위 5.3은 `Get_Cur_LLR_Idx_FILE`을 `6973-7073`, code_diff 6.1은 `6973-6999`와 6.2 `7048-7071`. 소스 실제 줄과 맞춘다
- 앵커: 상위 문서가 링크하는 `code_diff.md#ch1_2`, `#ch2`, `#ch3`, `#ch4`, `#ch5`, `#ch6`, `#ch7`, `#ch8`, `#ch9`가 code_diff의 `<a id>`와 모두 대응하는지 본다
- 서술 차이
  - ㉮ 상위 5.2-3 "MPI로 뿌리는 곳에 새 배열을 함께 실어야 한다" 대 code_diff 3.7 "각 rank가 따로 읽는 구조라면 필요 없다"
  - ㉯ 상위 5.4-3 "파일이나 실행 인자로 받아야 한다" 대 code_diff 전제 ㉰ "값은 기존 상수에서 가져온다"
  - ㉰ 상위 5.3-4와 7장 ㉱ "통일할지 그대로 둘지 미결정" 대 code_diff 6.1 ㉮ "한 갈래로 합쳤다"
  - ㉱ 상위 5.4-2 "정수 index로 일반화" 대 code_diff 2.2 "`cur_sw_branch_idx[MAX_SW_SPAN]` 배열"
  - ㉲ 상위 5.1-4 "`num_row`를 iteration 수로 간주하는 곳이 있으면 고쳐야 한다" 대 code_diff에 그런 위치의 목록이 있는지
  - ㉳ 상위 5.5 "딸려오는 12곳" 대 code_diff 1.2 "이 상수를 쓰는 12곳" (관점 6의 grep 결과와 세 번 맞춘다)
- 상위 4장 ㉮의 예시 헤더는 `type_each_group`을 `1 1 1 1 1 1 1 1 1 1 1 1`로 적었다. 상위 3장 표는 그룹 1, 2, 3, 5만 CSW 타입이라고 확인했다. 그룹 0, 4(row 1개)와 6~11의 타입을 파일에서 확인해 예시가 맞는지 본다 (관점 1과 연결)
- code_diff 서두의 새 이름 표 아홉 개가 본문에서 모두 쓰이는지, 본문에 표에 없는 새 이름(`Select_SW_Branch`, `max_iter_end`)이 있는지 본다
- 상위 5.1-3의 `local_opt.cpp:120` 언급과 code_diff 3.5의 수정 범위(`116-123`)가 같은 줄을 가리키는지 본다
- 상위 5.6 표의 세 항목과 code_diff 8.1~8.3이 하나씩 대응하는지 본다

### 15. 적용 순서의 단계별 정합

- code_diff 9장 1단계(1장, 2장)만 넣은 상태: `decoder.h`에서 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_*`가 사라지는데 `decoder.cpp:459-493, 606-616, 2082-2130, 7001-7020`의 옛 코드가 남아 있다. 이 단계에서 빌드가 되는지, 9장 1단계 문장 "빌드가 깨지는 곳이 이름 변경 지점이다"가 이것을 뜻하는지 본다
- 3단계(6장까지) 주장 "`Select_BF`가 그대로라 `cur_sw_branch_idx[]`가 모두 0이므로 분기 0만 쓰인다": 옛 `Select_BF`(`decoder.cpp:2084-2085`)는 `cur_sw_branch_idx[]`를 만지지 않는다. 이 단계에서 배열을 0으로 만드는 주체가 누구인지 본다
- 3단계 주장 "기존 동작과 결과가 같아야 한다": 옛 AUTO 경로(`decoder.cpp:6985-6999`)는 iteration만 보고 g가 큰 그룹부터 잡으므로 `LLR_MATRIX_1.txt`에서 iter 1~4는 그룹 2(분기 1), iter 5는 그룹 4(분기 1), iter 6~8은 그룹 5(분기 1)를 잡는다. 새 로직에서 분기 0만 쓰이면 그룹 0, 1, 3을 잡는다. 두 결과가 같은지 표로 만든다. 다만 옛 코드는 `type_each_group`이 20, 21이라 row 선택이 첫 row로 고정되는 점(상위 3장)도 함께 고려한다
- 4단계(4장, 5장)에서 `ITER_MAX_HBF`가 아직 0인 채 `Select_BF`가 `mn += 0`을 하는 상태가 의미 있는 중간 상태인지 본다
- 5단계(1.2장, 7장, 8장)가 마지막인 이유와, 8.1을 넣기 전까지 `Is_Iter_Type_Edge_Clear`의 `#else` 갈래가 남아도 AUTO 빌드에 영향이 없는지 본다

### 16. DAO 쪽 파급의 인지

- 상위 1장은 "DAO 쪽 대응(매트릭스 모델, 유효성 규칙, GenLLRMode)은 이 문서에서 다루지 않는다"고 범위를 자른다. 4장 ㉮가 채택되면 파일 헤더에 줄이 하나 늘어난다. 이 변경이 닿는 DAO 쪽 위치를 문서가 어디엔가(미결정, 후속 작업, `5_DAO/_pm/TODO.md`) 적어 두었는지 본다
  - `5_DAO/SRC/DAO_LLR_MATRIX.py:476-492` 줄 index 기반 헤더 파서 (`type_each_group` 다음 줄을 `num_restart`로 읽음)
  - `5_DAO/SRC/DAO_LLR_MATRIX.py:344-345`와 `5_DAO/DAO_spec.md:94` 유효성 규칙 RW2 (`floor_flag == -1`이 아니면 오류)
  - `5_DAO/SRC/DAO_LLR_MATRIX.py:524-535` row 파싱의 `floor_flag`
  - `5_DAO/DAO_spec.md:37, 51` 필드 설명 (`floor_flag` "현재 항상 -1")
  - `5_DAO/Util/Mock_ECC.py:86-88` (헤더 줄을 index로 건너뜀)
  - DAO가 LLR matrix를 쓰는 함수(`DAO_LLR_MATRIX.py`의 write 계열)가 새 줄을 내보내야 하는지
- `5_DAO/Input/Ref_C/Prime_ECC_3.0/EXE/`가 비어 있다. DAO가 부르는 C++ 실행 파일이 이 수정을 반영해 다시 빌드되어야 하는 관계가 문서 어딘가에 적혀 있는지 본다
- 상위 4장 ㉮ 예시가 새 줄을 `type_each_group` 바로 아래에 둔다. `restart_num` 앞에 두는 것과 `min_value` 뒤에 두는 것 중 DAO 파서와 C++ 파서 양쪽에서 옛 파일과의 구별이 쉬운 자리가 어디인지, 문서가 자리 선택의 근거를 적었는지 본다

### 17. 문서 작성 규칙 준수

- 루트 `CLAUDE.md` 문장 작성 규칙 ㉱: 두 문서에서 줄표(U+2014)와 가운뎃점(U+00B7)을 grep한다
- 글로벌 규칙 "번호 나열은 ㉮㉯㉰, 주소 받는 갈래는 `- 1.`": 상위 2장, 4장, 5.1~5.4, 7장, code_diff 5.1 "바뀐 점", 6.1 "바뀐 점", 9장의 나열 기호가 규칙과 맞는지 본다
- 약어 첫 등장 풀어쓰기: SW(Syndrome Weight)는 상위 1장에서 풀었다. CSW, BF, HD, 1.5SD, MPI, rank, span, row, Corner, HBF, VNU, TV가 각 문서에서 처음 나올 때 풀어 썼는지 본다. code_diff는 상위 문서와 별개 파일이므로 code_diff 안에서도 첫 등장을 본다
- 규칙 ㉮ "수리는 덧대기가 아니라 다시 쓰기"와 ㉯ "규칙은 긍정문": code_diff 2.2 "지금도 대입만 되고 읽히는 곳이 없으므로 지운다", 3.6 "지금도 해제되지 않고 있다", 8.3 "지금은 ... 굳어 있다" 같은 현재 상태 서술이 계획 문서에서 허용되는 배경 설명인지, 코드 주석으로 옮겨질 때 규칙에 걸리는지 본다
- 규칙 ㉲ "입력 파일의 성격을 서술하지 않는다": 두 문서가 `LLR_MATRIX_1.txt`를 이름과 내용으로만 가리키는지, 출처나 성격을 적은 문장이 있는지 본다. `Prime_ECC_3.0` 경로 표기가 이 규칙에 걸리는지 본다
- 링크: 상위 문서의 `../../../../0_LDPC_original/src/*.h` 상대경로와 code_diff 5.1의 `corner.h#L79-L81` 링크가 실제 파일에 닿는지 본다
- 작성 시각 형식(`2026-09-02 23:13:58`)이 글로벌 규칙의 `date` 형식과 같은지 본다

---

## 작성자 요청 7개와 관점의 대응

| 요청 | 관점 |
|------|------|
| 1. 파일 해석 | 1 (보조: 2, 14) |
| 2. 그룹 선택 순서 독립성 | 3 (보조: 15) |
| 3. 구간 번호 계산 반례 | 4 |
| 4. Select_BF 타당성 | 5 (보조: 2) |
| 5. ITER_MAX_HBF 12곳 누락 | 6 (보조: 7, 13) |
| 6. 86곳 분류 | 11 (보조: 9) |
| 7. MPI rank별 읽기 | 10 (보조: 9) |

작성자가 요청하지 않았으나 추가한 영역: 7 (iteration 번호 체계), 8 (멤버 제거 파급), 9 (컴파일 스위치 조합), 12 (읽기와 오류 처리), 14 (두 문서 상호 정합), 15 (적용 순서), 16 (DAO 파급), 17 (문서 규칙)
