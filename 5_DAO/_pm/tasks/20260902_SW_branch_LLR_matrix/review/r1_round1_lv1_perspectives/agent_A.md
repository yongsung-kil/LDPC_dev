# Round 1 관점 도출 (에이전트 A)

리뷰 대상은 `20260902_SW_branch_LLR_matrix.md`(이하 상위 문서)와 `code_diff.md` 두 문서다.
두 문서는 코드 수정 계획이며 실제 소스(`0_LDPC_original/src/`)는 아직 손대지 않았다.
아래 관점은 "무엇을 어디와 대조할지"만 적는다. 문제 판정은 다음 라운드가 한다.

context.md의 "작성자가 특히 확인을 요청한 곳" 1~7은 각각 관점 1, 4, 3, 5, 6, 12, 11에 들어 있다.

## 관점 표

| # | 관점명 | 확인 항목 | 대상 파일/범위 |
|---|--------|-----------|----------------|
| 1 | 파일 해석의 사실 정확성 (요청 1) | `LLR_MATRIX_1.txt`의 헤더 줄 순서, 그룹별 row 수, 각 row의 iter_start, iter_end, 마지막 칸을 상위 문서 2장 표와 3장 표에 하나씩 대조. fscanf 토큰 읽기 순서와 문서의 줄 해석이 같은지 | `LLR_MATRIX_1.txt` 전체, 상위 문서 2장, 3장, `local_opt.cpp:52-132` |
| 2 | 분기 모델과 사용자 의도의 정합 | 상위 문서가 세운 구간(span)과 분기 모델이 `msg1.md`의 디코더 동작 서술(BF 구간 1~4 고정, BF 미진입 시 iteration 5부터, BF에서는 LLR matrix 문턱을 받지 않음)과 맞는지. 파일의 그룹 2(분기 1, iteration 1~4)가 어느 프레임에서 쓰이는지 | `msg1.md`, 상위 문서 2장, 4장, `code_diff.md` 5장, `decoder.cpp:1966-1970`, `2082-2130` |
| 3 | 구간 번호 계산의 반례 (요청 3) | `code_diff.md` 3.2장의 `prev_branch != 0` 규칙에 헤더 배열을 여러 형태로 넣어 결과를 손으로 계산. 분기 없는 그룹이 구간 사이에 끼는 경우, 분기가 하나뿐인 구간, 0으로 시작하지 않는 구간, 구간 수가 `MAX_SW_SPAN`을 넘는 경우 | `code_diff.md` 3.2장, 상위 문서 2장 읽는 규칙 ㉮~㉱, 4장 ㉮ |
| 4 | 그룹 선택의 순서 독립성 (요청 2) | `code_diff.md` 6.1장 루프를 파일 그룹 배치를 바꿔 가며 손으로 실행. 같은 iteration을 분기 없는 그룹과 분기 그룹이 함께 덮는 경우, 그룹 순서가 뒤집힌 경우, `sw_span_idx_each_group`이 -1인 채 `cur_sw_branch_idx[span]`에 닿는 경우 | `code_diff.md` 6장, `decoder.cpp:6973-7073`, `LLR_MATRIX_1.txt` |
| 5 | `Select_BF`와 문턱 배열화의 타당성 (요청 4) | BF 진입 시 span 0 분기를 `syn_weight`로 고르는 근거, `SW_TH_BF1_512B_TLC_OFF`(130)를 span 0 문턱으로 쓰는 근거, 비교 방향과 기존 코드의 동치, `default` 갈래에서 `num_sw_branch[0]=1`인데 파일이 분기 2개인 경우, 2SD와 3SD 갈래, Corner 이벤트 인덱스 산술 | `code_diff.md` 4장, 5장, `decoder.cpp:459-493`, `2082-2130`, `common.h:200-252`, `decoder.h:296-306`, `corner.h:78-81`, `corner.cpp:174-176` |
| 6 | `ITER_MAX_HBF` 통일의 파급 범위 (요청 5) | 상위 문서 5.5장 표 12곳을 소스 grep 결과(decoder.cpp 39곳, local_opt.cpp 2곳, main.cpp 1곳, TV_Dec_Inter.cpp 5곳)와 대조. 빠진 줄이 `__AUTO_LLR_OPT__` 빌드에서 실행되는 경로인지 | 상위 문서 5.5장, `code_diff.md` 1.2장, 7장, `decoder.cpp` 전체 grep, `local_opt.cpp:124-131`, `main.cpp:719`, `TV_Dec_Inter.cpp:1077-1535` |
| 7 | `MN` 배열과 최대 iteration의 의미 | `ITER_MAX_HBF`가 4가 된 뒤 `local_opt.cpp:116-131`이 만드는 `MN[]`과 `main.cpp:704-725`가 만드는 `MN[]`의 형태 비교. 파일 최대 iteration 124와 루프 상한(`mn < MN + 1`), BF 진입과 미진입 각각의 마지막 iteration, `MN[]` 중간 원소를 읽는 곳 | `local_opt.cpp:116-131`, `main.cpp:704-725`, `decoder.cpp:564`, `1118-1120`, `2097-2098`, `2114-2115`, `7583` |
| 8 | `__AUTO_LLR_OPT__` 갈래 제거가 비AUTO 빌드에 미치는 영향 | `code_diff.md` 5장, 6장, 8장이 `#if defined(__AUTO_LLR_OPT__)` 갈래를 없앨 때, 비AUTO 빌드에서 `m_param_LLR`이 세팅되는 경로가 있는지. `Get_Cur_LLR_Idx_FILE`의 호출 지점이 AUTO 빌드에만 있는 것과 상위 5.3-4의 서술 | `decoder.cpp:1137-1141`, `431-448`, `2082-2130`, `6538-6660`, `ecc_top.cpp:197-230`, `main.cpp:87-131`, `mode.h:22-26`, 상위 문서 5.3, 7장 ㉱ |
| 9 | 이름 변경과 구조체 변경의 파급 (선언, 초기화, 해제, 로그) | 지우는 멤버(`flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0/1`)와 enum을 참조하는 모든 줄이 두 문서에 잡혀 있는지. 새 배열의 초기화 시점과 컴파일 스위치 조합(`__12META__`)에서 상수 존재 여부 | `decoder.cpp:452-616`, `583`, `decoder.h:296-306`, `common.h:200-252`, `717-725`, `ecc_data.h:179-198`, `local_opt.cpp:10-26`, `105`, `114`, `178` |
| 10 | 파일 읽기 함수의 견고성 | 새 줄의 위치가 상위 4장 ㉮ 예시와 `code_diff.md` 3.2장에서 같은지, 기존 형식 파일(분기 줄 없음)을 넣었을 때의 동작 방침, 3.4장 대조 검사의 `err` 처리, 3.5장 최대 iteration, 3.6장 소멸자, 로그 출력에 새 줄 반영 | `code_diff.md` 3장, `local_opt.cpp:52-183` |
| 11 | MPI 전파 구조 (요청 7) | 각 rank가 `Read_LLR_info_Auto`를 스스로 호출해 파일을 읽는지, `LLR_MATRIX`와 `CSW_thr`만 뿌리는 이유(root가 실행 중 바꾸는 값인지), 새 배열 Bcast의 필요성 | `local_opt.cpp:27-51`, `52-60`, `133`, `local_opt.h`, `mpi.cpp`, `5_DAO/3_run_DAO_mpi.bat`, `5_DAO/SRC/DAO_Main.py`(실행 방식) |
| 12 | `__AUTO_LLR_OPT__` 전수 목록의 완전성과 분류 재검토 (요청 6) | 상위 6장 목록을 grep 결과(10개 파일 87곳)와 대조. 6.3장 "손대지 않아도 되는 곳" 가운데 BF와 분기가 살아나면 뜻이 바뀌는 곳(power stopping, CSW 로그, 결과 출력, 인자 파싱, 문턱 출력) | 상위 문서 6장, `decoder.cpp:505-510`, `1917-1921`, `7339-7352`, `7522-7578`, `main.cpp:140-144`, `308`, `ecc_top.cpp:652`, `680`, `944-950` |
| 13 | 두 문서 사이의 상호 정합 | 상위 문서 5.x 항목과 `code_diff.md` 장 번호 링크와 앵커, 같은 주제를 두 문서가 다르게 적은 곳(MPI, 문턱 입력 방식, 비AUTO 경로 통일 여부, 분기 총수 x를 세는 주체, 추가되는 필드 목록, "12곳" 세기), 9장 적용 순서의 3단계 동치 주장 | 상위 문서 4장, 5장, 7장, `code_diff.md` 전제, 2장, 3.7장, 4장, 6장, 9장 |
| 14 | 수정 전 코드 인용의 사실 정확성 | `code_diff.md`의 "수정 전" 블록과 상위 문서의 줄 번호 인용을 실제 소스와 대조. 생략 표시(`...`)가 가린 부분에 동작이 있는지 | `code_diff.md` 1~8장 각 "수정 전", 상위 문서 3장, 5장의 줄 번호, 해당 소스 줄 |
| 15 | 문서 작성 규칙 준수 | 루트 `CLAUDE.md` 문장 규칙(줄표, 가운뎃점, 나열 기호, 과거 서술 금지, 입력 파일 성격 서술 금지, 용어 풀어쓰기)과 링크 상대경로 | 두 문서 전체, 루트 `CLAUDE.md` 문장 작성 규칙 ㉮~㉲ |
| 16 | DAO 쪽 도구와 파일 포맷의 정합 | 표기 안 ㉮(헤더 줄 추가)가 DAO의 줄 단위 파서와 유효성 규칙(`floor_flag == -1`)에 미치는 영향, 파일 생성 주체와 포맷 결정 주체, DAO의 "BF 없음" 가정과 새 iteration 셈법 | `5_DAO/SRC/DAO_LLR_MATRIX.py:476-537`, `5_DAO/DAO_spec.md` 2장 표, 3장 RW2, `5_DAO/Util/Mock_ECC.py`, `msg1.md`, 상위 문서 1장, 7장 |
| 17 | 프레임 안 상태 초기화 순서와 모드별 동작 | `cur_sw_branch_idx[]`가 세팅되는 시점(mn==0 끝)과 읽히는 시점(mn>=1 시작), `Clear_Flag()`와의 관계, iteration 0의 row 선택(`cur_set_idx=0`), 2SD와 3SD 모드에서 분기 파일을 넣었을 때, power stopping의 `Jump_Iter`가 mn을 바꿀 때 | `decoder.cpp:606-616`, `1118-1145`, `1960-1970`, `2082-2130`, `6973-7073` |

## 관점별 확인 항목

### 1. 파일 해석의 사실 정확성 (요청 1)

- ㉮ `LLR_MATRIX_1.txt` 1~16행을 `local_opt.cpp:61-100`의 fscanf 순서(num_para_each_set, num_dv, dv_from, dv_to, num_group, num_set_each_group, type_each_group, restart_num, restart_iter, max_value, min_value)에 한 토큰씩 맞춰 본다. 상위 문서 4장 ㉮의 예시 헤더가 이 순서와 같은지 본다
- ㉯ 상위 문서 2장 표의 12개 그룹 각각에 대해 row 수(`1 7 6 6 1 5 5 7 6 10 10 13`, 합 77), 첫 row와 마지막 row의 iter_start, iter_end, 마지막 칸을 파일 18~105행에서 직접 센다. 특히 그룹 0(1~1, row 1개)과 그룹 4(5~5, row 1개)를 본다
- ㉰ 상위 문서 3장 표의 CSW 나열(그룹 1, 2, 3, 5)을 파일의 해당 row 17번째 칸(`num_col=16` 다음 칸)과 대조한다
- ㉱ 상위 문서 2장 "읽는 규칙" ㉮~㉱이 파일의 실제 배치(`20 20 21 20 21 21 1 1 1 1 1 1`)에서 모두 한 번 이상 쓰이는지, 규칙 ㉰("y가 0으로 되돌아가면 새 구간")이 그룹 2에서 그룹 3으로 넘어갈 때 iteration이 4에서 5로 이어지는 것과 맞는지 본다
- ㉲ "최대 iteration은 124"와 "분기는 1~8에만"을 파일 전체 row에서 확인한다
- ㉳ 파일이 탭과 빈 줄로 구분되어 있는데 fscanf `%d`가 이를 무시하는 것과, DAO 파서(관점 16)가 줄 단위로 읽는 것의 차이를 기록해 둔다
- ㉴ iteration 0에서 `cur_set_idx = 0`(row 0, 그룹 0)이 쓰이는 것(`decoder.cpp:1143-1145`)이 상위 문서 2장 표에 어떻게 반영되어야 하는지 본다

### 2. 분기 모델과 사용자 의도의 정합

- ㉮ `msg1.md`의 서술을 항목별로 뽑는다. ㉠ BF는 iteration 1~4 전용이고 구간이 늘지 않는다, ㉡ BF 미진입이면 iteration 0, 5, 6, 7로 센다, ㉢ BF이면 LLR matrix에서 문턱을 받지 않고 -1로 처리한다, ㉣ SW 구간 예시(1/4/-1, 5/8/0, 5/8/1, 5/8/2), ㉤ DAO는 BF가 없다고 가정한다
- ㉯ 상위 문서 2장과 4장이 세운 모델(span 0 = 1~4에 분기 2개, span 1 = 5~8에 분기 2개)을 ㉮의 각 항목과 맞춰 본다. 특히 ㉢과 파일 그룹 2(분기 1, iteration 1~4, CSW 나열 있음)의 관계, 그리고 `code_diff.md` 5장이 BF 진입 프레임에서만 span 0 분기를 고르는 것(BF 미진입 프레임은 `mn += 4`로 1~4를 건너뜀)과 ㉡의 관계를 본다
- ㉰ `msg1.md`의 예시 ㉣은 5~8에 분기 셋(0, 1, 2)이고 1~4는 -1이다. 파일 `LLR_MATRIX_1.txt`는 1~4에도 분기 둘을 둔다. 두 형태가 같은 모델에서 나온 것인지, 문서가 어느 쪽을 정본으로 삼았는지 본다
- ㉱ 상위 문서가 `msg1.md`를 근거로 인용하지 않는데, context.md는 이를 배경 메모로 지목한다. 문서에 근거 링크가 필요한지 본다

### 3. 구간 번호 계산의 반례 (요청 3)

- ㉮ `code_diff.md` 3.2장 코드를 다음 헤더 배열에 손으로 돌려 `sw_span_idx_each_group`과 `num_sw_span`을 적는다. ㉠ `0 0 1 0 1 1 -1 ...`(파일 그대로), ㉡ `0 1 -1 0 1`(구간 사이에 분기 없는 그룹), ㉢ `0 0`(두 구간이 모두 분기 하나뿐), ㉣ `1 0`(오름차순 위반), ㉤ `-1 1 2`(0 없이 시작), ㉥ 구간이 5개(`MAX_SW_SPAN`=4 초과), ㉦ `0 1 0 1 0 1 0 1 0 1`
- ㉯ 각 결과가 상위 문서 2장 읽는 규칙 ㉮~㉱과 같은 답을 내는지, 다른 답이 나오는 입력을 파일 규격이 금지하는지(금지한다면 어디에 적혀 있는지) 본다
- ㉰ `sw_span_idx_each_group[i] = num_sw_span - 1`이 ㉤ 같은 입력에서 -1이 되어 관점 4의 `cur_sw_branch_idx[span]` 인덱스로 흘러가는 경로를 본다
- ㉱ 상위 문서 4장 ㉮은 "분기 총수 x는 읽는 쪽에서 센다"고 하는데, `code_diff.md` 3장은 세지 않고 4장은 `num_sw_branch[]`를 상수에서 채운다. 파일에서 센 값과 상수를 대조하는 검사(`code_diff.md` 4장 끝 문장)가 코드로 들어갔는지 본다
- ㉲ `code_diff.md` 3.4장 대조 검사는 헤더와 row의 분기 index 일치만 본다. 같은 구간 안 분기들의 iteration 시작과 끝이 맞는지(상위 2장 ㉱)는 어디서 검사하는지 본다

### 4. 그룹 선택의 순서 독립성 (요청 2)

- ㉮ `code_diff.md` 6.1장 표(iter 3, 6, 20)를 `LLR_MATRIX_1.txt`로 직접 재현한다. iter 1, 2, 4, 5, 8, 9, 124도 추가로 돌려 본다
- ㉯ 다음 배치에서 결과가 순서에 좌우되는지 본다. ㉠ 분기 없는 그룹(-1)이 iteration 1~8을 통째로 덮고 분기 그룹이 같은 구간을 덮는 경우, ㉡ 같은 분기 안에서 두 그룹의 iteration 구간이 겹치는 경우, ㉢ 그룹 순서를 뒤집은 파일, ㉣ 분기 그룹이 파일 뒤쪽(iteration 9 이후)에 있는 경우
- ㉰ 루프가 `iter_start[start_idx]`와 `iter_end[end_idx]`만 보므로 그룹 안 row가 iteration 오름차순이라는 전제가 있다. 이 전제가 어디에 적혀 있는지, GROUP_TYPE_CSW 그룹(row가 CSW 내림차순이고 iteration은 모두 같음)에서 성립하는지 본다
- ㉱ 수정 후 코드에서 `selected_group` 확정 뒤 `start_idx`, `end_idx`가 그 그룹 값으로 남아 있는지(루프 안에서 계산되고 `break`로 나오므로) 본다. 비AUTO 갈래의 `7038-7046` 재계산이 사라진 것이 영향을 주는지 본다
- ㉲ `cur_sw_branch_idx[span]`에서 `span`이 -1 또는 `MAX_SW_SPAN` 이상이 될 수 있는 입력(관점 3 ㉰)이 이 루프에 도달하는 경로를 본다
- ㉳ 6.2장의 `return 0`이 row 0(그룹 0, iteration 1~1, 분기 0)을 돌려주는 뜻이 되는데, 오류 시 이 row를 쓰는 것이 의도인지 본다

### 5. `Select_BF`와 문턱 배열화의 타당성 (요청 4)

- ㉮ 기존 코드(`decoder.cpp:2087-2095`)는 BF 진입 시 `flag_HD_1_4_Set`과 `flag_HD_5_8_Set`을 모두 TYPE_0으로 못박는다. 수정 후는 `Select_SW_Branch(0, syn_weight)`와 `Select_SW_Branch(1, syn_weight)`로 고른다. `LAYOUT_PRIME_512B_TLC_VSS_OFF`에서 `syn_th_BF0`(680) 미만인 프레임은 `syn_th_sw_branch[1][0]`(1100) 미만이므로 span 1은 항상 0이 되는지 계산으로 확인한다. span 0은 130 문턱으로 갈리므로 기존과 결과가 달라지는 프레임이 생기는데, 이것이 상위 문서 5.4-1의 의도와 같은지 본다
- ㉯ `SW_TH_BF1_512B_TLC_OFF`(130)을 span 0 문턱으로 쓰는 근거가 `decoder.h:302-303`의 주석("S-4 Set")과 `common.h:236-237`뿐인지, 다른 근거(문서, 커밋, msg1.md)가 있는지 본다
- ㉰ `Select_SW_Branch`의 비교(`weight < th` 이면 낮은 분기)와 기존 `syn_weight < syn_th_5_8_Set_0 → TYPE_0`의 방향이 같은지, 등호 처리가 같은지 본다
- ㉱ `default` 갈래는 `num_sw_branch[0] = 1`이다. 파일이 span 0에 분기 2개를 두면 `cur_sw_branch_idx[0]`은 항상 0이 되어 그룹 2가 쓰이지 않는다. 이 조합을 오류로 잡을지 허용할지가 어디에 적혀 있는지 본다
- ㉲ `MODE_DEC_1_5SD` 갈래가 `psyn_weight`를 쓰는 것이 유지되는지, 2SD와 3SD가 들어가는 `else` 갈래에서 `cur_sw_branch_idx[]`가 0으로 남는 것이 의도인지 본다
- ㉳ Corner 이벤트가 `IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]`로 바뀐다. `corner.h:79-81`의 세 값이 연속인지, `corner.cpp:174-176`의 헤더 출력과 맞는지, 기존에는 BF 진입 갈래에서도 이벤트를 기록했는데 새 코드가 모든 갈래(else 포함)에서 기록하는 것이 통계에 영향을 주는지 본다. 분기가 넷 이상이면 `IDX_FLAG_HD_FLOOR_TYPE_0`을 침범하는 것을 어디서 막는지 본다
- ㉴ `code_diff.md` 4.1장에서 `syn_th_BF`가 사라지고 `default` 갈래가 `syn_th_BF0`에 `SW_TH_BF_DEFAULT`를 넣는다. 기존에는 `default`에서 `syn_th_BF0`이 미초기화였으므로 동작이 바뀐다. 이 변화가 문서에 적혀 있는지 본다
- ㉵ `Init_Dec_Option`은 `Init_ECC_Top`(`ecc_top.cpp:229`)에서 불리고, `Read_LLR_info_Auto`(`local_opt.cpp:34`)는 그보다 앞서 불린다. 파일에서 센 분기 수와 `num_sw_branch[]`를 대조하려면 어느 시점이 맞는지 본다

### 6. `ITER_MAX_HBF` 통일의 파급 범위 (요청 5)

- ㉮ 소스 grep에서 `ITER_MAX_HBF`가 나오는 줄은 다음과 같다. `decoder.cpp` 564, 1149, 1448, 1622, 1821, 1828, 1929, 1976, 2097, 2098, 2114, 2115, 2169, 2190, 2310, 2377, 2800, 3487, 4058, 4277, 6454, 6545, 6571, 7583, 7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018, `local_opt.cpp` 126, 129, `main.cpp` 719, `TV_Dec_Inter.cpp` 1077, 1221, 1295, 1487, 1535. 상위 문서 5.5장 표와 하나씩 대조한다
- ㉯ 표에 없는 줄(1448, 1622, 1821, 1828, 2169, 2190, 7717 이후의 `MN_size` 계산, TV_Dec_Inter.cpp, main.cpp:719)이 각각 어떤 컴파일 스위치 아래에 있는지(`__RUN_PARITY_SKIP__`, `__RUN_PREPROCESSING__`, `__RUN_ITER34_HIGH_DV_SKIP__`, `__ECC_TV__`, `__AUTO_LLR_OPT__` 아님)와 AUTO 빌드에서 실행되는지 본다
- ㉰ 상위 문서 5.5장 표의 "12곳"과 `code_diff.md` 1.2장의 "12곳"이 같은 셈법인지(표는 11행이고 한 행에 두 줄이 묶인 곳이 있음) 본다
- ㉱ 상위 문서 5.5장 둘째 표의 `iter <= 4` 네 곳이 `code_diff.md` 7장 네 곳과 줄 번호까지 맞는지 본다

### 7. `MN` 배열과 최대 iteration의 의미

- ㉮ `local_opt.cpp:116-131`을 파일 값(최대 124, HD 모드)과 `ITER_MAX_HBF = 4`로 손으로 돌려 `MN_num`, `MN[0]`, `MN[1]`, `MN[MN_num-1]`을 적는다. `main.cpp:704-725`가 비AUTO에서 만드는 `MN[]`(`MN[0] = ITER_MAX_HBF`, `MN[4] = ITER_MAX_HD_PRIME`)과 형태를 비교한다
- ㉯ `decoder.cpp:1118-1120`의 루프 상한(`MN = m_param_dec->MN[MN_num-1]`, `mn < MN + 1`)과 `Select_BF`의 `MN += ITER_MAX_HBF`를 합쳐, BF 진입 프레임과 미진입 프레임 각각의 마지막 iteration 번호를 계산한다. 파일 row가 덮는 iteration(1~124)과 비교한다
- ㉰ `MN[]`의 중간 원소(`MN[1]` 등)를 읽는 곳을 grep(`m_param_dec->MN[`)으로 찾아, 음수나 어긋난 값이 들어갈 때 영향을 받는 곳이 있는지 본다
- ㉱ `decoder.cpp:564`의 `crc_dec_LFSR_iter` 크기와 `7583` 이후 `MN_size` 계산이 BF 미진입 프레임의 마지막 iteration까지 덮는지 본다
- ㉲ `code_diff.md` 3.5장이 `MN_num = max_iter_end`로 바꾸는데, 이후 `local_opt.cpp:124-131`의 보정이 그대로인 것이 문서에 적혀 있는지 본다

### 8. `__AUTO_LLR_OPT__` 갈래 제거가 비AUTO 빌드에 미치는 영향

- ㉮ 비AUTO 빌드의 진입(`main.cpp:87-131`)에서 `Init_ECC_Top`은 `PARAM_LLR` 없는 오버로드(`ecc_top.cpp:197-210`)를 타고, 이 오버로드는 `m_param_LLR` 멤버를 세팅하지 않은 채 `Init_Dec`에 넘긴다. `code_diff.md` 8.1장과 8.2장 수정 후 코드는 `m_param_LLR->restart_num`을 읽는다. 비AUTO 빌드가 어느 경로로 여기 도달하는지 본다
- ㉯ `Get_Cur_LLR_Idx_FILE`은 `decoder.cpp:1137-1141`에서 AUTO 빌드에서만 불린다. 따라서 그 함수의 `#else` 갈래(7001-7047)는 비AUTO 빌드에서 컴파일은 되지만 호출되지 않는다. 상위 문서 5.3-4와 7장 ㉱이 이 갈래를 살아 있는 경로로 서술하는지 본다
- ㉰ `Is_Iter_Type_Edge_Clear`와 `Is_Iter_Type_Init`의 비AUTO 갈래(`6567-6595`, `6627-6660`)는 2SD와 3SD의 restart 지점을 `RSP1_*` 상수로 박아 둔다. 수정 후 코드가 이를 파일의 `restart_iter`로 대체하는데, 비AUTO 빌드에서 그 파일이 없을 때의 방침이 문서에 있는지 본다
- ㉱ `mode.h:22-26`에서 `__AUTO_LLR_OPT__`가 켜지는 조건(Ref-C이고 Windows가 아닐 때)을 확인하고, 상위 문서 6.3장 첫 행의 서술과 맞는지 본다
- ㉲ 상위 문서 7장 ㉱은 "두 경로를 그대로 둘지"를 미결정으로 두고, `code_diff.md` 6장 ㉮은 합쳤다. 어느 쪽이 정본인지, 상위 문서 5.3-4 문장과 `code_diff.md` 전제 ㉮~㉰에 이 결정이 들어 있는지 본다

### 9. 이름 변경과 구조체 변경의 파급 (선언, 초기화, 해제, 로그)

- ㉮ `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 참조하는 줄(`decoder.h:297-298`, `decoder.cpp:612-613`, `2090-2123`, `7002-7016`) 가운데 두 문서에 없는 줄을 찾는다. 특히 `Clear_Flag()`(`decoder.cpp:606-616`)
- ㉯ `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1`을 참조하는 줄(`decoder.cpp:460-492`, `583` 주석, `2088-2116`, `decoder.h:301-306`)이 모두 다루어졌는지 본다
- ㉰ `FLAG_HD_1_4_SET_TYPE_*`, `FLAG_HD_5_8_SET_TYPE_*`(`common.h:717-725`)을 지울 때 남는 참조가 있는지 grep으로 본다
- ㉱ `SW_TH_BF0_512B_TLC_OFF`, `SW_TH_BF1_512B_TLC_OFF`는 `common.h:200-252`의 `#else`(비`__12META__`) 블록에만 있다. `code_diff.md` 4.1장 수정 후 코드가 `__12META__` 빌드에서 컴파일되는지 본다
- ㉲ `code_diff.md` 2.2장의 `MAX_SW_SPAN`=4인데 주석과 `Select_BF`는 span 0, 1만 채운다. span 2, 3이 0으로 남는 것이 파일의 구간 수(`num_sw_span`)와 어떻게 대조되는지 본다
- ㉳ `code_diff.md` 4.1장의 루프가 쓰는 `i`가 `Init_Dec_Option` 지역 변수(`decoder.cpp:454`)로 선언되어 있는지, `syn_th_sw_branch[i][j]` 초기값 0이 `Select_SW_Branch`에서 `weight < 0`으로 걸리지 않는 것이 의도인지 본다
- ㉴ `ecc_data.h` 수정 후 주석 "옛 floor_flag"가 루트 `CLAUDE.md` 문장 규칙 ㉮(과거 서술을 코드에 남기지 않음)과 맞는지 본다 (관점 15와 겹침)
- ㉵ `PARAM_LLR`에 새 필드를 넣는 위치가 구조체 중간이다. 이 구조체를 통째로 복사하거나 MPI로 보내는 곳이 있는지 grep(`PARAM_LLR`, `sizeof`)으로 본다

### 10. 파일 읽기 함수의 견고성

- ㉮ `code_diff.md` 3.2장이 새 줄을 `type_each_group` 다음, `restart_num` 앞에 넣는다. 상위 문서 4장 ㉮의 예시 헤더 순서와 같은지 본다
- ㉯ 기존 형식 파일(분기 줄 없음)을 새 코드에 넣으면 fscanf가 `restart_num` 줄을 분기 줄로 읽는다. 하위 호환 방침(기존 파일을 모두 바꾼다, 또는 파일 버전 표시를 둔다)이 두 문서 중 어디에 있는지 본다
- ㉰ 3.4장 대조 검사는 `err = TRUE`만 세운다. `local_opt.cpp:56`, `139-142`에서 `err`가 어디에 쓰이는지 보고, 오류 시 실행을 멈추는지 본다
- ㉱ 3.5장 `max_iter_end` 계산 뒤 `local_opt.cpp:124-131` 보정이 그대로 붙는지, `MN` 재할당(`main.cpp:108`의 `delete[] g_param_dec.MN`과의 관계)을 본다
- ㉲ 3.6장 "floor_flag는 지금도 해제되지 않고 있다"를 `local_opt.cpp:10-26`에서 확인한다
- ㉳ `local_opt.cpp:133-183`의 결과 로그(`Ref_C_result_*.txt`)에 새 헤더 줄(`sw_branch_idx_each_group`)을 찍는 수정이 문서에 있는지 본다. 이 로그를 DAO가 읽는지(관점 16)도 본다
- ㉴ `fopen` 실패 시 `matrix_in`이 NULL인 채 fscanf가 진행되는 기존 구조를 문서가 다루는지(범위 밖이면 범위 밖이라고 적혀 있는지) 본다

### 11. MPI 전파 구조 (요청 7)

- ㉮ `local_opt.cpp:27-35`에서 `Run_Local_Opt`가 rank 조건 없이 `Read_LLR_info_Auto`를 부르고, `52-60`에서 rank 조건 없이 `fopen`한다. `133`의 `ID_ROOT` 조건은 로그 쓰기에만 걸린다. 이 세 곳으로 "각 rank가 파일을 따로 읽는 구조"인지 판정할 수 있는지 본다
- ㉯ 그럼에도 `37-44`에서 `LLR_MATRIX`와 `CSW_thr`만 Bcast하는 이유를 찾는다. root가 실행 중 이 두 배열을 바꾸는 최적화 루프가 현재 `local_opt.cpp`, `local_opt.h`, `main.cpp`에 남아 있는지 grep(`opt_LLR_MATRIX`, `opt_CSW_thr`, `curr_value`)으로 본다. 루프가 DAO(python)로 옮겨 갔다면 Bcast가 과거 흔적인지 본다
- ㉰ `5_DAO/3_run_DAO_mpi.bat`와 `5_DAO/SRC/DAO_Main.py`에서 실행 파일이 어떤 작업 폴더에서 몇 rank로 뜨는지, 모든 rank가 같은 `LLR_MATRIX_%d.txt`를 보는지 본다
- ㉱ `code_diff.md` 3.7장은 "확인한 뒤 맞춘다"로 열어 두고, 상위 문서 5.2-3은 "함께 실어야 한다"로 닫혀 있다. 판정 결과에 따라 어느 문장을 고칠지 본다 (관점 13과 겹침)
- ㉲ 새 배열을 Bcast한다면 `num_sw_span`(int 멤버)의 주소 전달과, `MPI_Barrier`가 row마다 있는 기존 패턴을 따를지 본다

### 12. `__AUTO_LLR_OPT__` 전수 목록의 완전성과 분류 재검토 (요청 6)

- ㉮ grep 결과는 10개 파일 87곳이다(common.h 3, decoder.cpp 36, ecc_top.cpp 17, decoder.h 3, ecc_data.h 1, ecc_top.h 2, main.cpp 21, mode.h 2, random.cpp 1, random.h 1). 상위 문서 6.1, 6.2, 6.3장의 줄 번호를 모두 모아 87곳과 대조하고 빠진 줄과 세는 방식 차이(86 대 87)를 적는다
- ㉯ 6.3장 항목 가운데 BF와 분기가 살아난 뒤 뜻이 바뀌는 곳을 본다. ㉠ `decoder.cpp:505-510` power stopping OFF 고정(관점 17 ㉲과 연결), ㉡ `1917-1921`, `7339-7352`, `7574-7578` CSW 로그 수집과 출력(분기 index나 BF 진입 여부를 로그에 실어야 DAO가 분기별로 최적화할 수 있는지, `5_DAO/Util/Mock_ECC.py:221-233`의 로그 형식과 대조), ㉢ `main.cpp:140-144` 인자 파싱(상위 7장 ㉯의 "실행 인자로 받기"를 택하면 여기가 바뀜), ㉣ `main.cpp:308`의 `SW_TH_BF_DEFAULT` 출력(문턱이 배열화되면 표시가 어긋나는지), ㉤ `ecc_top.cpp:652`, `680`, `944-950` 결과 출력(분기별 통계가 필요한지), ㉥ `8109-8113` `state_hd_error_floor_set` 초기화
- ㉰ 6.2장 다섯 곳(`Get_VNU_LLR_SET_FILE` 갈림)이 BF 1bit 경로(`4055-4059` 등)와 같은 함수 안에 있으므로, BF가 살아날 때 `Get_VNU_LLR_SET_FILE`이 BF 프레임에서도 파일 row를 읽는 것이 `msg1.md`의 "BF이면 문턱을 받지 않는다"와 맞는지 본다 (관점 2와 연결)
- ㉱ `decoder.h:185-188`, `431-434`와 `ecc_data.h:143-146`이 새 함수 선언(`Select_SW_Branch`)과 충돌하지 않는지 본다

### 13. 두 문서 사이의 상호 정합

- ㉮ 상위 문서 5.1~5.6이 가리키는 `code_diff.md` 장 번호(5.1→3장, 5.2→2장, 5.3→6장, 5.4→5장과 4장, 5.5→1.2장과 7장, 5.6→8장)와 앵커(`#ch1`, `#ch1_2`, `#ch2`~`#ch9`)가 실제로 있는지, `code_diff.md`가 상위 문서로 돌아가는 링크가 맞는지 본다
- ㉯ 같은 주제를 두 문서가 다르게 적은 곳을 모은다. ㉠ MPI(상위 5.2-3 "실어야 한다" 대 `code_diff.md` 3.7 "필요 없을 수도"), ㉡ 문턱 입력(상위 5.4-3 "파일이나 실행 인자로" 대 `code_diff.md` 전제 ㉰ "기존 상수"), ㉢ 비AUTO 경로(상위 7장 ㉱ 미결정 대 `code_diff.md` 6장 ㉮ 통일), ㉣ 분기 총수 x(상위 4장 ㉮ "읽는 쪽에서 센다" 대 `code_diff.md` 4장 상수), ㉤ 추가 필드(상위 5.2-1은 `sw_branch_idx_each_group`만, `code_diff.md` 2.1은 `sw_span_idx_each_group`, `num_sw_span`도 추가), ㉥ `Is_Iter_Type_Init`(상위 5.6 "확인 필요" 대 `code_diff.md` 8.2 "의도로 보인다"), ㉦ 상위 문서 대상 파일 목록에 `mode.h`가 있으나 `code_diff.md`에 `mode.h` 변경이 없고, `corner.h`는 `code_diff.md` 5장에 나오나 목록에 없음
- ㉰ `code_diff.md` 머리의 "새로 쓰는 이름" 표가 본문에서 쓰는 이름과 일치하는지(`syn_th_sw_branch[][]`의 둘째 차원 `MAX_SW_BRANCH - 1` 등) 본다
- ㉱ `code_diff.md` 9장 적용 순서에서 "3단계까지는 기존 동작과 결과가 같아야 한다"는 주장을 본다. 6장은 `table_row_idx` 초기값을 -1로 바꾸고 오류 시 `return 0`을 넣으며 AUTO 갈래를 지우므로, 3단계에서 동치가 성립하는 조건(파일이 새 형식이고 오류가 없을 때)이 적혀 있는지 본다. 또 1장에서 `ITER_MAX_HBF`를 4로 바꾸는 1.2장을 5단계로 미루는데, 1장을 "먼저 넣는다"는 1단계 서술과 어긋나지 않는지 본다
- ㉲ 상위 문서 3장의 "`decoder.cpp:6974`에서 0으로 초기화", "`7069` 검사가 0을 통과", "`7048`"과 `code_diff.md` 6장의 줄 번호(6973-6999, 7048-7071)가 같은 소스를 가리키는지 본다

### 14. 수정 전 코드 인용의 사실 정확성

- ㉮ `code_diff.md`의 각 "수정 전" 블록을 소스와 글자 단위로 대조한다. 1.1(`common.h:756-757`), 1.2(`403-407`), 2.1(`ecc_data.h:179-198`), 2.2(`decoder.h:296-306`), 3.1(`local_opt.cpp:74`), 3.2(`81-84`), 3.3(`105`, `114`), 3.5(`116-123`), 3.6(`10-26`), 3.7(`38-44`), 4.1(`decoder.cpp:459-493`), 5.1(`2082-2130`), 6.1(`6973-7047`), 6.2(`7048-7073`), 7.1(`2373-2379`), 7.2(`2796-2802`), 7.3(`4055-4059`, `4274-4278`), 8.1(`6538-6598`), 8.2(`6606-6626`), 8.3(`1146-1156`)
- ㉯ `...`로 생략한 곳(5.1 수정 전의 Corner 이벤트, 6.1의 비AUTO 탐색 루프, 8.1의 비AUTO 갈래, 8.2 전체)에 수정 후 코드가 다루지 않는 동작이 있는지 본다
- ㉰ 상위 문서가 인용한 줄 번호(`decoder.cpp:1968-1970`, `2085`, `6974`, `7048`, `7069`, `common.h:202-251`, `717-725`, `decoder.h:301`, `local_opt.cpp:14-15`, `36-44`, `105`, `114`, `116`, `120`, `178`)가 실제 소스와 맞는지 본다
- ㉱ 상위 문서 3장의 "`GROUP_TYPE_CSW`(1): 직전 iteration의 CSW(`prev_CSW`)와 row의 CSW 문턱으로 고른다"를 `decoder.cpp:7059-7068`의 실제 비교(`prev_CSW <= CSW_thr`, 뒤에서 앞으로)와 대조한다

### 15. 문서 작성 규칙 준수

- ㉮ 두 문서 전체에서 줄표(U+2014)와 가운뎃점(U+00B7)을 grep한다
- ㉯ 나열 기호가 규칙(㉮㉯㉰, 하위 ㉠㉡, 주소 받는 갈래는 `- 1.`)을 따르는지, 표 칸 안 나열이 `<br>`인지 본다
- ㉰ 루트 `CLAUDE.md` 문장 규칙 ㉲(입력 파일의 성격을 서술하지 않는다)와 상위 문서 2장, 3장이 `LLR_MATRIX_1.txt`의 내용을 표로 푼 것의 관계를 본다. 파일을 이름과 치수로만 가리키는 범위 안인지 판정 기준을 적는다
- ㉱ 문장 규칙 ㉮(수리는 다시 쓰기, 과거 서술 금지)에 비추어 `code_diff.md` 수정 후 코드의 주석("옛 floor_flag", 1.2장 아래 "갈래를 없앤다" 설명은 문서 본문이므로 허용)을 본다
- ㉲ 업계 약어(SW, CSW, BF, HD, 1.5SD, MPI, rank, span, Corner, Preprocessing, edge clear)가 각 문서 첫 등장에서 풀어 쓰였는지 본다
- ㉳ 상대경로 링크(`../../../../0_LDPC_original/src/...`)가 `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/`에서 저장소 루트까지 네 단계인지, `corner.h#L79-L81` 같은 줄 앵커가 뷰어에서 동작하는지 본다

### 16. DAO 쪽 도구와 파일 포맷의 정합

- ㉮ `5_DAO/SRC/DAO_LLR_MATRIX.py:476-507`은 줄 단위로 헤더를 읽고 `type_each_group` 다음 줄을 `num_restart`로 읽는다. 표기 안 ㉮(헤더 줄 추가)를 택하면 이 파서가 어떻게 되는지, 안 ㉯와 ㉰는 어떤지 본다
- ㉯ `DAO_spec.md` 3장 RW2(`floor_flag == -1`)와 `DAO_LLR_MATRIX.py:344-345`가 row 마지막 칸을 -1로 못박는데, 파일은 0과 1을 쓴다. 이 규칙의 정본이 어느 쪽인지 본다
- ㉰ `LLR_MATRIX_1.txt`를 만든 도구가 무엇인지(DAO의 GenLLRMode인지 손으로 만든 것인지) 5_DAO README와 DAO_Main.py에서 찾는다. 포맷 결정(상위 7장 ㉮)의 주체가 DAO인지 C++인지 본다
- ㉱ 상위 문서 1장이 "DAO 쪽 대응은 다루지 않는다"고 선을 긋는데, 7장 미결정 사항에 DAO 연동(파서, 유효성, 로그 형식)을 후속 작업으로 등재해야 하는지 본다
- ㉲ `msg1.md`의 "DAO는 BF가 없다고 가정하고 0, 1, 2, 3, 4로 진행한다고 본다"와 새 C++의 iteration 셈법(BF 미진입 시 5부터)이 DAO의 결과 해석(`Mock_ECC.py:171`의 `max_iteration`, 결과 파일의 iteration 통계)에 영향을 주는지 본다

### 17. 프레임 안 상태 초기화 순서와 모드별 동작

- ㉮ `cur_sw_branch_idx[]`는 `Select_BF`(`decoder.cpp:1966-1970`, mn==0 루프 끝)에서 세팅되고 `Get_Cur_LLR_Idx_FILE(mn)`(`1136-1142`, mn>=1 루프 시작)에서 읽힌다. 이 순서가 모든 경로(power stopping의 `Jump_Iter`가 mn을 바꾸는 `1961-1964` 포함)에서 지켜지는지 본다
- ㉯ `Clear_Flag()`(`606-616`)가 프레임마다 `flag_BF_on`을 지우는데, 새 배열은 `Select_BF`에서만 지운다. `Select_BF`가 불리지 않는 프레임(예: mn==0에서 조기 종료)이 있으면 이전 프레임 값이 남는지 본다
- ㉰ iteration 0은 `cur_set_idx = 0`(row 0)이다. row 0이 그룹 0(iteration 1~1, 분기 0)인 파일에서 분기 1 프레임의 iteration 0이 분기 0의 row를 쓰는 것이 의도인지 본다
- ㉱ 2SD와 3SD 모드에서 분기 파일을 넣으면 `cur_sw_branch_idx[]`가 0으로 남아 분기 0 그룹만 쓰인다. 이 동작이 문서에 적혀 있는지 본다
- ㉲ `Is_Iter_Type_Edge_Clear`가 `iter == 1`과 `iter == 5`에서 edge clear를 하는데, BF 진입 프레임은 1에서, 미진입 프레임은 5에서 걸린다는 `code_diff.md` 8.1장의 설명을 `mn` 값의 흐름(미진입 시 mn이 0에서 5로 뜀)으로 확인한다. BF 진입 프레임이 iteration 5에서도 edge clear를 하는지 본다
- ㉳ `Preprocessing` 시점(`1146-1156`)과 `overall_clk` 보정(`1815-1831`)이 `flag_BF_on`과 `ITER_MAX_HBF`에 함께 걸리므로, BF 진입과 미진입 각각에서 한 번씩만 실행되는지 본다
