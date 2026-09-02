# 리뷰 관점 도출 (에이전트 B)

리뷰 대상: `20260902_SW_branch_LLR_matrix.md`(이하 상위 문서)와 `code_diff.md`.
두 문서는 코드 수정 계획이며 실제 소스는 아직 바뀌지 않았다. 아래 관점은 "어디를 무엇과 대조해야 하는지"만 적는다. 문제 판정은 다음 라운드가 한다.

줄 번호는 `0_LDPC_original/src/` 현재 파일 기준이다. 작성자 요청 7건은 관점 1, 3, 4, 5, 6, 7, 8에 들어 있다.

## 관점 표

| # | 관점명 | 확인 항목 | 대상 파일/범위 |
|---|--------|-----------|----------------|
| 1 | 파일 해석 정합 (요청 1) | 상위 문서 2장, 3장 표를 파일 원문과 헤더 읽기 순서에 대조 | `LLR_MATRIX_1.txt` 전체, 상위 2장 3장, `local_opt.cpp:61-115` |
| 2 | 분기 의미론과 배경 메모 정합 | 분기 index가 어느 SW 구간을 뜻하는지, BF 프레임이 매트릭스를 받는지 | 루트 `msg1.md`, 상위 2장 4장, code_diff 4장 5장, `decoder.cpp:2082-2130` |
| 3 | 그룹 선택의 순서 독립성 (요청 2) | 분기 필터가 들어간 역방향 탐색이 겹침 상황에서 유일한 답을 주는지 | code_diff 6.1, `decoder.cpp:6973-7073`, `decoder.cpp:1118-1145` |
| 4 | 구간 번호 계산의 반례 (요청 3) | `prev_branch != 0` 규칙이 깨지는 헤더 배열이 있는지, 상한 검사가 있는지 | code_diff 3.2, 상위 2장 읽는 규칙, 상위 4장 |
| 5 | Select_BF와 문턱 배열 (요청 4) | span 0 분기를 SW로 고르는 것의 근거, 문턱 상수의 출처와 방향, Corner 이벤트 | code_diff 4장 5장, `decoder.cpp:452-493`, `decoder.cpp:2082-2130`, `common.h:200-252`, `corner.h:69-87` |
| 6 | ITER_MAX_HBF 딸린 곳 전수 (요청 5) | 상위 5.5 표와 실제 사용처 전체를 대조 | 상위 5.5, code_diff 1.2 7장, `decoder.cpp`, `main.cpp:719`, `TV_Dec_Inter.cpp` |
| 7 | `__AUTO_LLR_OPT__` 분류 재검토 (요청 6) | 6.3 "손대지 않아도 되는 곳" 중 로직에 걸리는 것, 6.1 중 수정 후 코드가 없는 것 | 상위 6장, `decoder.cpp:505-510, 1137-1141, 1917-1921, 8109-8113`, `main.cpp:706` |
| 8 | MPI 구조 (요청 7) | 각 rank가 파일을 따로 읽는지, Bcast의 목적 | `main.cpp:47-98, 115-120`, `local_opt.cpp:27-51, 133`, code_diff 3.7 |
| 9 | 비 AUTO 빌드 경로 안전성 | `#ifdef` 갈래를 지운 뒤 비 AUTO 빌드에서 `m_param_LLR`이 유효한지, 죽은 코드 여부 | code_diff 5장 6장 8장, `main.cpp:102-130`, `ecc_top.cpp:197-230`, `decoder.cpp:431-436, 1137-1141, 6566-6596` |
| 10 | 삭제 멤버와 enum의 잔여 참조 | 지우는 이름이 문서 밖 어디서 쓰이는지, 새 배열 초기화 위치 | `decoder.cpp:583, 606-616`, `decoder.h:296-306`, `common.h:717-725`, `corner.cpp:174-176` |
| 11 | 컴파일 스위치 조합 | 수정 후 코드가 스위치 조합마다 빌드되고 뜻이 유지되는지 | `common.h:200-252`, `mode.h:22-26`, `decoder.cpp` 각 `#if` 블록 |
| 12 | MN 배열과 iteration 번호 체계 | `ITER_MAX_HBF` 0에서 4로 갈 때 MN 배열의 값과 소비처 | `local_opt.cpp:116-131`, code_diff 3.5, `decoder.cpp:564, 1118-1120, 1976, 2097-2098, 7583`, `main.cpp:704-725` |
| 13 | 파서 견고성과 구 포맷 호환 | 새 헤더 줄이 필수가 될 때 구 파일 처리, 오류 검사의 실효성 | `local_opt.cpp:52-132`, code_diff 3장, `Prime_ECC_2.4/.../LLR_MATRIX_0.txt` |
| 14 | DAO 쪽 도구 영향 | 파일 포맷 변경이 Python 파서, 유효성 규칙, Mock에 미치는 영향과 문서의 의존 기록 | `5_DAO/SRC/DAO_LLR_MATRIX.py:476-537, 282-283, 344-345`, `DAO_spec.md`, `Util/Mock_ECC.py:80-95` |
| 15 | 프레임 간 상태와 restart 상호작용 | 분기 상태 초기화 시점, restart와 분기 구간의 겹침, SD 모드 처리 | code_diff 5장 8장, `decoder.cpp:606-616, 1966-1970, 6538-6626, 8055-8113` |
| 16 | 두 문서 사이의 상호 정합 | 장 링크, 줄 번호, 이름, 미결정 사항과 전제의 대응 | 상위 5장 7장, code_diff 전제와 각 장 앵커 |
| 17 | 소스 인용 정확성 | "수정 전" 블록과 상위 문서의 줄 번호 인용이 실제 소스와 같은지 | code_diff 각 장 수정 전 블록, 상위 3장 4장 5장 표 |
| 18 | 적용 순서(9장)의 단계별 성립 | 각 단계에서 빌드가 되는지, "기존과 같아야 한다"의 기준이 무엇인지 | code_diff 9장, 2.2, 5장, `decoder.cpp:467-492, 612-613, 2090-2123, 7002-7016` |
| 19 | 변경 금지 대상, 변경 등급, 문장 규칙 | TV 출력 시점과 PCRC 종료 시점 영향, Decision 등급 표시, 문장 규칙 위반 | 루트 `CLAUDE.md`, `0_LDPC_original/CLAUDE.md`, 두 문서 전체 |

## 관점별 확인 항목

### 1. 파일 해석 정합 (요청 1)

- ㉮ `LLR_MATRIX_1.txt` 1~18줄의 헤더 순서(4, 4, dv_from, dv_to, 12, num_set 12개, `20 20 21 20 21 21 1 1 1 1 1 1`, restart_num 0, max 4개, min 4개)를 `local_opt.cpp:61-100`의 `fscanf` 순서와 한 줄씩 맞춰 본다. restart_num이 0이라 restart_iter 줄이 없다는 점이 상위 4장 ㉮의 예시 헤더(신규 줄이 `type_each_group` 바로 아래)와 code_diff 3.2의 읽는 위치(같은 자리)에서 일관되는지 본다
- ㉯ 상위 2장 표의 그룹별 row 수, iteration, 마지막 칸을 파일 18~105줄과 대조한다. 그룹 0은 18줄 1행, 그룹 1은 20~26줄 7행, 그룹 2는 28~33줄, 그룹 3은 35~40줄, 그룹 4는 42줄, 그룹 5는 44~48줄, 그룹 6~11은 50~105줄이다. row 수 합이 77인지, 각 그룹 안에서 iter_start와 iter_end가 표와 같은지, 마지막 칸이 헤더의 `y`와 같은지 본다
- ㉰ 상위 3장 표의 CSW 나열(그룹 1: -1, 400, 120, 40, 32, 24, 16 등)을 파일 각 row의 끝에서 네 번째 칸과 대조한다
- ㉱ 상위 2장 "읽는 규칙" ㉮~㉱이 파일에서 실제로 성립하는지 본다. 특히 그룹 2(분기 1)가 1~4를 한 덩어리로 덮고 그룹 4, 5(분기 1)가 5~5와 6~8로 나뉘는 것이 규칙 ㉱(분기마다 내부 분할이 달라도 됨)의 사례로 맞게 서술됐는지 본다
- ㉲ `{x}{y}` 해석(두 자리를 한 자리씩 끊어 읽음, 상한 9)이 파일 제공자의 의도인지 확인할 근거가 문서에 있는지 본다. `msg1.md` 26~36줄은 row 마지막 칸(-1, 0, 1, 2)만 말하고 헤더 표기는 말하지 않는다

### 2. 분기 의미론과 배경 메모 정합

- ㉮ `msg1.md` 13~16줄은 SW 구간을 BF(SW < BF 문턱), normal0, normal1, normal2로 나눈다. 19~22줄은 BF를 타면 iteration 0, 1, 2, ...로, 안 타면 0, 5, 6, ...으로 세고, "BF라면 LLR matrix에서 threshold를 받지 않고 -1로 처리"하며 "BF 구간은 딱 1~4"라고 적었다. 30~34줄 예시는 `1/4/-1, 5/8/0, 5/8/1, 5/8/2`다. 이 서술과 `LLR_MATRIX_1.txt`의 iteration 1~4 분기(그룹 0, 1이 분기 0, 그룹 2가 분기 1)가 어떤 관계인지, 상위 문서가 이 차이를 다루는지 본다
- ㉯ code_diff 5장 ㉯(BF 진입 시 span 0 분기를 SW로 고름)가 메모의 "BF는 threshold를 받지 않음"과 양립하는지 본다. BF 1bit 모드(`decoder.cpp:4055-4075`, `2373-2379`)에서 `Get_VNU_LLR_SET_FILE`(`decoder.cpp:3985-3990`)이 돌려준 값 중 무엇이 실제로 쓰이는지 따라가면 span 0 분기의 실효성이 드러난다
- ㉰ 분기 index 0이 SW가 낮은 쪽인지 높은 쪽인지 방향을 확정한다. code_diff `Select_SW_Branch`(540-548)는 오름차순 문턱에서 낮은 SW를 index 0으로 준다. 기존 `decoder.cpp:2099-2106`(`syn_weight < syn_th_5_8_Set_0`이면 TYPE_0)과 같은 방향인지, 파일의 그룹 3(분기 0, CSW 616부터)과 그룹 5(분기 1, CSW 984부터)의 CSW 문턱 범위가 그 방향과 어울리는지 본다
- ㉱ 분기(프레임 시작 SW로 결정)와 row 선택(직전 iteration의 CSW로 결정, `decoder.cpp:7059-7068`)이 둘 다 신드롬 계열 값을 쓰는 구조에서 역할이 겹치지 않는지, 문서가 두 축의 관계를 설명하는지 본다

### 3. 그룹 선택의 순서 독립성 (요청 2)

- ㉮ code_diff 6.1 수정 후 코드(688-710)는 뒤에서 앞으로 훑으며 분기가 맞지 않는 그룹을 건너뛴 뒤 iteration 범위를 본다. 같은 분기 안에서 iteration 범위가 겹치는 그룹이 둘 이상일 수 있는지(상위 2장 ㉱가 분기 내부 분할을 허용하므로 파일 작성 실수로 가능), 그때 뒤쪽 그룹이 이기는 것이 의도인지 본다
- ㉯ 분기 없음(-1) 그룹과 분기 그룹의 iteration 범위가 겹치는 파일(예: 1~8을 덮는 -1 그룹과 5~8 분기 그룹이 공존)에서 결과가 배치 순서에 따라 달라지는지 본다
- ㉰ `start_idx`, `end_idx`는 그룹의 첫 row `iter_start`와 마지막 row `iter_end`로 범위를 잡는다(6.1의 697-706). `GROUP_TYPE_ITER` 그룹에서 row가 iteration 오름차순이 아닐 때 범위가 어긋나는지 본다
- ㉱ `cur_sw_branch_idx[span]` 접근(693)에서 `span`이 `MAX_SW_SPAN`(4) 이상이면 배열 밖이다. `num_sw_span`과 `MAX_SW_SPAN`을 대조하는 검사가 파서나 선택 로직에 있는지 본다
- ㉲ 6.1의 표(720-728) 다섯 사례를 손으로 재현하고, iter 1(그룹 0 단일 row), iter 5(그룹 4 단일 row), iter 9(분기 구간 밖 첫 iteration) 사례를 보탠다
- ㉳ BF 미진입 프레임은 `mn`이 5부터 시작한다(`decoder.cpp:2097-2098`과 `1118-1120`). span 0 그룹이 후보가 되지 않는지, `cur_sw_branch_idx[0]`이 기본값 0으로 남아도 무해한지 본다
- ㉴ `Get_Cur_LLR_Idx_FILE`은 `mn > 0`에서만 불린다(`decoder.cpp:1136-1145`). iteration 0의 `cur_set_idx = 0`이 분기 구조에서 어느 row를 뜻하는지 본다

### 4. 구간 번호 계산의 반례 (요청 3)

- ㉮ code_diff 3.2(236-253)의 규칙은 "분기 index가 0이고 직전이 0이 아닐 때 새 구간"이다. 다음 배열에서 기대와 다른 답이 나오는지 본다. ㉠ 분기 그룹 사이에 -1 그룹이 끼는 경우(`0 0 -1 0 1`), `prev_branch`가 -1이 되어 다음 0이 새 구간으로 세어지는데 그것이 의도인지. ㉡ 같은 구간에서 분기 0 그룹이 분기 1 그룹 뒤에 다시 나오는 경우(`0 1 0`). ㉢ 분기가 하나뿐인 구간(`0 0`)이 두 구간 연속(`0 0 0 0`)이면 하나로 합쳐지는 경우. ㉣ 첫 분기 그룹이 0이 아닌 값으로 시작하는 경우(`1 0`). ㉤ 한 구간 안에서 index가 건너뛰는 경우(`0 2`)
- ㉯ 상위 2장 ㉯㉰(y가 1 늘면 되돌아감, 0으로 되돌아가면 새 구간)와 파서 규칙이 같은 것인지 본다. 파서는 iteration 범위를 전혀 보지 않으므로, 상위 4장의 "같은 iteration 구간을 덮는 서로 다른 분기 index의 개수로 x를 센다"는 서술과 대응하는 코드가 있는지 본다
- ㉰ 구간별 분기 개수(파일에서 센 값)와 `Init_Dec_Option`의 `num_sw_branch[]`(code_diff 4.1)를 대조하는 검사가 실제 코드로 있는지 본다. code_diff 473-477은 제안만 적었다
- ㉱ `num_sw_span`이 `MAX_SW_SPAN`을 넘거나 분기 index가 `MAX_SW_BRANCH` 이상일 때의 처리가 있는지 본다

### 5. Select_BF와 문턱 배열 (요청 4)

- ㉮ code_diff 5.1 수정 후(552-584)와 수정 전 `decoder.cpp:2082-2130`을 대조한다. 기존은 BF 진입 시 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 모두 TYPE_0으로 못박았다. 수정 후는 span 0, span 1을 각각 SW로 고른다. BF 진입 조건 `syn_weight < syn_th_BF0`(680)인 프레임에서 span 1 문턱 1100(`SW_TH_5_8_SET0_512B_TLC_OFF`)은 항상 분기 0이 되므로 기존과 같은지, span 0 문턱 130(`SW_TH_BF1_512B_TLC_OFF`, `common.h:237`)의 출처와 뜻(`decoder.h:303` 주석 "S-4 Set")을 문서가 근거로 대는지 본다
- ㉯ code_diff 4.1의 `default` 갈래(464-469)는 `num_sw_branch[0] = 1`이다. 파일은 span 0에 분기 2개를 두므로 `matrix_sel`이 `LAYOUT_PRIME_512B_TLC_VSS_OFF`가 아닐 때 어긋난다. 이 조합이 실제로 쓰이는지, 어긋날 때 어떻게 되는지 본다
- ㉰ `common.h:230-251`(비 `__12META__`)에서 `SW_TH_5_8_SET1_512B_TLC_OFF`(950)가 `SW_TH_5_8_SET0_512B_TLC_OFF`(1100)보다 작다. code_diff 447-449의 "문턱은 오름차순" 전제와 이 상수를 `syn_th_sw_branch[1][1]`에 넣겠다는 473줄 서술이 맞물리는지 본다
- ㉱ `MODE_DEC_1_5SD` 갈래(572-577)는 `psyn_weight`로 span 1을 고른다. 기존 `decoder.cpp:2113-2128`과 같은지 본다. HD도 1.5SD도 아닌 모드(578-580)는 `flag_BF_on`만 내리고 `mn` 이동이 없는데 기존 코드도 그런지 본다
- ㉲ Corner 이벤트(581-583)는 기존에 HD와 1.5SD 갈래 안에서만 발생했다. 수정 후는 모든 모드에서 발생한다. `corner.h:78-81`의 `IDX_FLAG_HD_5_8_SET_TYPE_0/1/2` 연속성, `corner.cpp:174-176` 라벨, `IDX_FLAG_HBF_ON` 이벤트가 어디서 발생하는지(BF 진입 이벤트가 유지되는지) 본다
- ㉳ `Select_BF` 호출 시점(`decoder.cpp:1966-1970`, `mn == 0` 루프 끝)과 `syn_weight`, `psyn_weight` 계산 시점(`decoder.cpp:3440-3444`, iteration 0의 마지막 column)의 순서가 분기 결정에 필요한 값을 보장하는지 본다

### 6. ITER_MAX_HBF 딸린 곳 전수 (요청 5)

- ㉮ 상위 5.5 표(12곳)와 `ITER_MAX_HBF`의 실제 사용처 전체를 대조한다. 표에 없는 사용처 후보: `decoder.cpp:1448`, `1622`(`__RUN_PARITY_SKIP__`), `1821`, `1828`(clock 계산), `2169`, `2190`(PCRC termination point, `__DUAL_UPDATE__` 양쪽), `7717`부터 `8018`까지 `MN_size` 계산 17곳, `main.cpp:719`(비 AUTO MN 설정), `TV_Dec_Inter.cpp:1077`, `1221`, `1295`, `1487`, `1535`(`mn == 4 + ITER_MAX_HBF`). 각각이 code_diff 1.2의 "같은 값으로 돌아간다"는 주장 안에 들어가는지, 0에서 4로 바뀔 때 동작이 의도대로 바뀌는지 본다
- ㉯ 상위 5.5 두 번째 표(`iter <= 4` 네 곳)와 code_diff 7장을 대조한다. 줄 범위 표기(`2374-2378` 대 `2373-2379`)가 같은 곳을 가리키는지 본다
- ㉰ `decoder.cpp:1973-1979`(`iter_num -= ITER_MAX_HBF`)는 `matrix_sel` 조건이 붙어 있다. 다른 `matrix_sel`에서 iteration 수 집계가 어떻게 되는지 본다
- ㉱ `decoder.cpp:6450-6458`(`__RUN_ITER34_HIGH_DV_SKIP__`)의 `mn == 4 + ITER_MAX_HBF`가 0에서 4로 바뀌면 skip 시점이 iteration 3, 4에서 7, 8로 옮겨진다. BF 진입 프레임에서 이것이 의도인지 본다

### 7. `__AUTO_LLR_OPT__` 분류 재검토 (요청 6)

- ㉮ 6.3 목록 중 로직에 걸릴 수 있는 곳: `decoder.cpp:505-510`(power stopping OFF 고정, `Jump_Iter` `1961-1964`와 `mn` 이동의 상호작용), `8109-8113`(`state_hd_error_floor_set` 초기화), `1917-1921`(CSW 로그 수집, 분기 index가 로그에 없으면 DAO가 분기별 성과를 구분 못 함), `main.cpp:706`(`Set_Ref_C_Iteration`이 AUTO에서 비어 있어 MN 설정을 `local_opt.cpp:116-131`이 대신함, 관점 12와 연결), `ecc_data.h:143-146`
- ㉯ 6.2 다섯 곳(`decoder.cpp:3985-3990` 등): BF 1bit 모드에서 `Get_VNU_LLR_SET_FILE`이 돌려준 값 중 실제로 쓰이는 것이 무엇인지 본다. 관점 2 ㉯와 연결
- ㉰ 6.1에 있으나 code_diff에 수정 후 코드가 없는 곳: `decoder.cpp:1137-1141`(갈림 자체를 유지하는지), `6609-6626`(8.2는 서술만 있음). 문서가 "고쳐야 하는 곳"과 "고치는 곳"을 일치시키는지 본다
- ㉱ 개수 대조: grep으로 세면 87건(common.h 3, decoder.cpp 36, decoder.h 3, ecc_data.h 1, ecc_top.cpp 17, ecc_top.h 2, main.cpp 21, mode.h 2, random.cpp 1, random.h 1)이다. 문서의 86곳과 세는 법(정의, `#if`, `#ifdef`, `#endif` 주석 포함 여부)을 맞춰 본다

### 8. MPI 구조 (요청 7)

- ㉮ `main.cpp:47-98`에서 모든 rank가 `Run_Simulation`, `Run_Simulation_Local_Opt`(`115-120`), `Run_Local_Opt`(`local_opt.cpp:27-36`), `Read_LLR_info_Auto`를 차례로 부르는지 본다. `ID_ROOT` 조건은 `local_opt.cpp:133`(로그 기록)에만 있다. 각 rank가 같은 작업 디렉토리의 같은 파일을 읽는 구조인지 `5_DAO/3_run_DAO_mpi.bat`, `Util/supercom/*.sh`의 실행 형태로 확인한다
- ㉯ `local_opt.cpp:38-44` Bcast의 목적을 확인한다. `Run_Simu_Curr_LLR`이 한 번만 불리고 C++ 안에서 매트릭스를 바꾸는 경로가 없으면 Bcast는 각 rank가 읽은 값을 덮어쓰는 것이고, 있으면 root가 바꾼 값을 뿌리는 것이다. code_diff 3.7의 "어느 쪽인지 확인한 뒤 맞춘다"에 답이 되는지 본다
- ㉰ code_diff 3.7 추가 Bcast의 형식(`num_sw_span`은 스칼라, 배열은 `&x[0]`), Barrier 위치, `mpi.h:14-16`과 `mpi.cpp`의 스텁 시그니처와 맞는지 본다
- ㉱ 헤더 나머지(`type_each_group`, `iter_start`, `iter_end`, `restart_iter`)를 Bcast하지 않는 기존 코드와 새 배열만 Bcast하는 수정 후 코드의 일관성을 본다

### 9. 비 AUTO 빌드 경로 안전성

- ㉮ code_diff 5장, 6장, 8장은 `#if defined(__AUTO_LLR_OPT__)` 갈래를 지우고 한 갈래로 만든다. 비 AUTO 빌드는 `main.cpp:105`, `127`에서 `PARAM_LLR` 없는 `Init_ECC_Top`(`ecc_top.cpp:197-210`)을 부르고, `208`줄이 `m_param_LLR`을 그대로 `Init_Dec`(`decoder.cpp:431-436`)에 넘긴다. `ecc_top.h:94`의 `m_param_LLR`이 생성자에서 초기화되는지, 아니면 미정의 값인지 본다
- ㉯ 8.1, 8.2 수정 후 코드는 `m_param_LLR->restart_num`을 무조건 읽는다. 비 AUTO 빌드에서 이 포인터가 유효한지, 문서가 "AUTO 빌드만 살린다"인지 "두 빌드 모두 유지"인지 범위를 밝히는지(상위 1장, 7장 ㉱) 본다
- ㉰ `Get_Cur_LLR_Idx_FILE`은 `decoder.cpp:1137-1141`에서 AUTO에서만 불린다. `7001-7047`의 `#else` 갈래가 현재 죽은 코드인지, 상위 5.3-4와 7장 ㉱(두 경로 통일 여부)가 이 사실을 반영하는지 본다
- ㉱ 비 AUTO의 `Is_Iter_Type_Edge_Clear` `#else` 갈래(`decoder.cpp:6566-6596`)는 2SD, 3SD에서 `RSP1_*` 상수를 쓴다. 수정 후 코드는 `restart_iter`로 대체하므로 비 AUTO 빌드에서 2SD, 3SD 동작이 바뀌는지 본다

### 10. 삭제 멤버와 enum의 잔여 참조

- ㉮ `flag_HD_1_4_Set`, `flag_HD_5_8_Set`: `decoder.cpp:612-613`(`Clear_Flag`), `2090-2123`, `7002-7016`, `decoder.h:297-298`. code_diff가 `612-613`을 다루는지 본다
- ㉯ `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_1`: `decoder.cpp:460-472`, `485-492`, `583`(주석 안), `decoder.h:301-306`. code_diff 2.2의 "대입만 되고 읽히는 곳이 없다"를 grep으로 확인한다
- ㉰ `FLAG_HD_1_4_SET_TYPE_*`, `FLAG_HD_5_8_SET_TYPE_*`(`common.h:717-725`)의 사용처 전체와 code_diff 597-598의 삭제 서술을 대조한다. `corner.h:79-81`의 `IDX_FLAG_HD_5_8_SET_TYPE_*`는 남긴다는 점이 분명한지 본다
- ㉱ `floor_flag`: `local_opt.cpp:105`, `114`, `178`, `ecc_data.h:197`. 문서 목록과 grep을 대조한다
- ㉲ `cur_sw_branch_idx[]`, `num_sw_branch[]`, `syn_th_sw_branch[][]`의 초기화 위치: `Select_BF`(code_diff 554-556)와 `Init_Dec_Option`(4.1)뿐인지, `Clear_Flag`(`decoder.cpp:606-616`)나 생성자에도 필요한지 본다. `Select_BF`는 `mn == 0` 루프 끝에서 불리므로 그 전에 `cur_sw_branch_idx`를 읽는 곳이 있는지 본다

### 11. 컴파일 스위치 조합

- ㉮ `__12META__`(`common.h:200-227`) 갈래에는 `SW_TH_BF0_512B_TLC_OFF`, `SW_TH_BF1_512B_TLC_OFF`가 없다. code_diff 4.1이 이 갈래에서 빌드되는지, 기존 `decoder.cpp:467-468`도 같은 문제를 갖는지 본다
- ㉯ `__CORNER_CHECKER__`(code_diff 581-583), `__RUN_MPI__`(3.7), `__RUN_PREPROCESSING__`(8.3, `decoder.cpp:1146-1156`), `__HD_FLOOR_SET__`(`decoder.cpp:494` 이후), `__RUN_PARITY_SKIP__`(`1446-1454`, `1620-1626`), `__DUAL_UPDATE__`(`2168-2200`), `__RUN_ITER34_HIGH_DV_SKIP__`(`6450-6458`), `__LOG_VNU_IN_OUT__`(`1925-1933`), `__4_BIT_LLR__`(`common.h:409-414`) 각각을 켜고 끌 때 수정 후 코드가 성립하는지 본다
- ㉰ `mode.h:22-26`의 AUTO 스위치 조건(`__PROGRAM_MODE_REF_C__`이고 Windows가 아닐 때)과 문서의 적용 환경 서술이 맞는지 본다

### 12. MN 배열과 iteration 번호 체계

- ㉮ `local_opt.cpp:116-131`: code_diff 3.5로 `MN_num`이 전체 최댓값이 된 뒤, `124-131`에서 HD와 1_SSD일 때 모든 원소에서 `ITER_MAX_HBF`를 빼고 `MN[0]`을 `ITER_MAX_HBF`로 둔다. 4일 때 배열이 어떤 값(음수 포함 여부)이 되는지, 소비처 `decoder.cpp:1118`(`MN = MN[MN_num - 1]`), `1120`(루프 상한), `564`(`MN_max`), `587`, `7583`과 `7717` 이후(`MN_size`), `Jump_Iter`(power stopping), `1976`(`iter_num` 보정)에서 뜻이 맞는지 본다
- ㉯ 비 AUTO의 `main.cpp:704-725`는 MN을 5칸(구간 상한)으로 쓰고 AUTO는 iteration마다 한 칸으로 쓴다. 두 체계에서 `ITER_MAX_HBF`가 같은 역할인지 본다
- ㉰ 상위 5.5 표에 `local_opt.cpp:126-130`이 있으나 code_diff에는 수정 후 코드가 없다. 0에서 4로 바뀔 때 이 블록이 무엇을 바꾸는지 문서가 서술하는지 본다
- ㉱ BF 미진입 시 `MN = MN + 4`(`decoder.cpp:2097-2098`)로 최대 iteration이 파일의 124를 넘는지, 로그 배열 크기(`7583`: `MN[last] + ITER_MAX_HBF + 1`)와 맞는지 본다
- ㉲ `mn`(BF 미진입 시 5부터)과 파일의 `iter_start`, `iter_end`의 대응, `1973-1979`의 `iter_num` 보정이 분기 구조에서도 성립하는지 본다

### 13. 파서 견고성과 구 포맷 호환

- ㉮ `local_opt.cpp:52-132`: `matrix_in`의 NULL 검사가 `fscanf` 뒤(`139`)에 있고, `err`(`56`)는 반환되지 않는다. code_diff 3.4의 `err = TRUE`가 실제 효과를 갖는지(함수 반환형 void) 본다
- ㉯ 새 헤더 줄이 필수가 되면 구 포맷(`5_DAO/Input/Ref_C/Prime_ECC_2.3`과 `2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt`, `type_each_group` 다음이 `restart_num`)은 `restart_num` 줄이 분기 줄로 읽힌다. 하위 호환 정책(구 파일 거부, 자동 감지, 변환 도구)을 문서가 정하는지 본다
- ㉰ `restart_num`이 0인 파일(`LLR_MATRIX_1.txt` 13줄)에서 `new int[0]`과 뒤이은 루프가 안전한지 본다
- ㉱ 3.4 대조 검사에서 row 마지막 칸 -1과 헤더 -1의 일치, 분기 index 값 범위(0 이상 `MAX_SW_BRANCH` 미만 또는 -1), 한 구간 안 index 연속성(0, 1, 2 빠짐 없음) 검사가 있는지 본다
- ㉲ `fscanf` 반환값을 보지 않는 상태에서 줄이 하나 빠진 파일이 어떻게 오독되는지, 문서가 파일 검증 책임을 어느 쪽(C++ 또는 DAO)에 두는지 본다

### 14. DAO 쪽 도구 영향

- ㉮ `5_DAO/SRC/DAO_LLR_MATRIX.py:476-537`은 헤더를 줄 index로 읽고(`483` `type_each_group`, `485` `num_restart`) row의 마지막 칸을 `floor_flag`로 둔다(`528`). `282-283`(H3 규칙), `344-345`(RW2: `floor_flag == -1` 강제), `384-397`(CSW 규칙)과 `DAO_spec.md:37, 51, 67, 94`가 새 포맷을 거부하는지 본다
- ㉯ `Util/Mock_ECC.py:80-95`(줄 건너뛰기), `Util/collect_llr_matrices.py`, `Util/rename_llr_idx.py`가 헤더 줄 수에 의존하는지 본다. `5_DAO/reference/`는 수정 금지이므로 대상에서 뺀다
- ㉰ 상위 1장은 DAO 대응을 범위 밖으로 두었다. 4장 ㉮(새 줄 추가)를 택하면 DAO 파서가 같은 줄을 써야 한다는 의존을 문서가 기록하는지, `5_DAO/_pm/TODO.md`에 후속 작업으로 이어지는지 본다
- ㉱ C++ 로그의 뜻 변화: `decoder.cpp:7868`(`m_log_LLR_idx = row index + 1`), `local_opt.cpp:133-183`(`Ref_C_result`)의 row index가 분기 구조에서 무엇을 가리키는지, DAO가 이 파일을 파싱하는지(`DAO_Constants.py:119-129`) 본다

### 15. 프레임 간 상태와 restart 상호작용

- ㉮ `cur_sw_branch_idx` 초기화 시점(code_diff 554-556, 프레임마다 `mn == 0` 끝)과 `Clear_Flag`(`decoder.cpp:606-616`) 호출 시점, 첫 프레임 이전 값이 정해지는지 본다
- ㉯ `restart_iter`가 분기 구간(1~8) 안에 있을 때 `Is_Iter_Type_Edge_Clear`(code_diff 8.1)와 그룹 선택이 어떻게 맞물리는지 본다. 구 파일 `LLR_MATRIX_0.txt` 22줄(전부 -1인 restart row, iteration 2~2)이 새 구조에서 어떻게 표현되는지 본다
- ㉰ `Is_Iter_Type_Init`(8.2)가 HD에서 `iter == 0`만 보는 것(`decoder.cpp:6604` 주석)과 BF 미진입 시 `mn`이 5로 뛰어 Edge clear가 5에서 일어나는 것(8.1 끝 서술)이 맞물리는지 본다
- ㉱ 2SD, 3SD 모드에서 `Select_BF`가 분기를 정하지 않아 `cur_sw_branch_idx`가 모두 0이다. 분기 그룹이 있는 파일을 SD 모드로 돌릴 때 분기 0만 쓰는 것이 의도인지, 문서가 모드별 동작을 적는지 본다
- ㉲ `Adjust_HD_Floor_Type`(`decoder.cpp:6980-6982`, `8055-8113`)과 `state_hd_error_floor_set`이 AUTO 그룹 선택에 관여하지 않고 로그에만 나가는지 확인한다

### 16. 두 문서 사이의 상호 정합

- ㉮ 장 링크: 상위 5.1은 ch3, 5.2는 ch2, 5.3은 ch6, 5.4는 ch5와 ch4, 5.5는 ch1_2와 ch7, 5.6은 ch8을 가리킨다. code_diff의 앵커(`31`, `56`, `81`, `193`, `409`, `481`, `602`, `810`, `880`, `993`줄)와 맞는지 본다
- ㉯ 줄 번호 표기 차이: 상위 5.4 `2084-2130` 대 code_diff 5.1 `2082-2130`, 상위 5.2-3 `36-44` 대 code_diff 3.7 `38-44`, 상위 5.2-4 `14-15` 대 code_diff 3.6 `10-26`, 상위 5.5 `2374-2378` 대 code_diff 7.1 `2373-2379`, 상위 5.3 `6973-7073`과 `6984-6999` 대 code_diff 6.1 `6973-6999`와 6.2 `7048-7071`, 상위 5.6 `6541-6565` 대 code_diff 8.1 `6538-6598`. 같은 곳을 가리키는지 본다
- ㉰ 이름 표(code_diff 15-28)와 상위 5.2, 5.4의 서술(5.4-2 "정수 index로 일반화" 대 code_diff 2.2 배열, 5.4-4 "배열로 바꾼다" 대 `syn_th_BF0` 낱개 유지)이 대응하는지 본다
- ㉱ 상위 7장 미결정 ㉮㉯㉰㉱과 code_diff 전제 ㉮㉯㉰, 6장 ㉮(두 경로 통일을 이미 반영)의 관계를 본다. 미결정이라 적은 항목을 diff가 한쪽으로 택한 것이 문서에 분명히 표시되는지 본다
- ㉲ 상위 5.5 "12곳" 세는 법(표는 13행, `2097-2098`과 `2114-2115`는 묶음)과 code_diff 1.2의 "12곳"이 같은 셈인지 본다
- ㉳ 상위 5.1-4(`num_row`의 뜻 변화 확인)에 대응하는 code_diff 항목이 있는지 본다
- ㉴ 상위 5.3-3(`decoder.cpp:7048` 오류 검사에 "두 갈래 어디에도 안 걸린 경우" 추가)과 code_diff 6.2 ㉯(오류 3)가 같은 내용인지 본다
- ㉵ code_diff 3.2 표(261-267)의 그룹 번호와 상위 2장 표의 그룹 번호가 같은 그룹을 가리키는지 본다

### 17. 소스 인용 정확성

- ㉮ code_diff "수정 전" 블록을 실제 소스와 대조한다. 1.1 `common.h:756-757`, 1.2 `common.h:403-407`, 2.1 `ecc_data.h:179-198`, 2.2 `decoder.h:296-306`, 2.3 `decoder.h:156`, 3.1 `local_opt.cpp:74`, 3.2 `81-84`, 3.3 `105`와 `114`, 3.5 `116-123`, 3.6 `10-26`, 3.7 `38-44`, 4.1 `decoder.cpp:459-493`(주석 줄 생략 여부), 5.1 `2082-2130`(`...`로 생략한 Corner 이벤트), 6.1 `6973-6999`, 6.2 `7048-7072`, 7.1 `2373-2379`, 7.2 `2796-2802`, 7.3 `4055-4059`와 `4274-4278`, 8.1 `6538-6598`, 8.2 `6606-6626`, 8.3 `1146-1156`
- ㉯ 상위 문서 인용: 3장 `decoder.cpp:6974`, `7069`, 4장 `local_opt.cpp:105`, `114`, `178`, 5.4 `decoder.cpp:1968-1970`, `2085`, 5.5 표 각 줄, 5.6 표 각 줄
- ㉰ 인용에서 `...`로 생략한 부분이 수정 후 코드에 빠짐없이 반영됐는지 본다(5.1의 508-513에 생략된 Corner 이벤트, 6.1의 660에 생략된 탐색 본체)

### 18. 적용 순서(9장)의 단계별 성립

- ㉮ 1단계(1장, 2장)만 넣은 상태에서 빌드가 되는지 본다. 2.2가 `flag_HD_*`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_*`를 지우면 5장 이전의 `Select_BF`(`decoder.cpp:2090-2123`), `Clear_Flag`(`612-613`), `Init_Dec_Option`(`467-492`), `Get_Cur_LLR_Idx_FILE` `#else`(`7002-7016`)가 깨진다. "빌드가 깨지는 곳이 이름 변경 지점"이라는 서술이 이것을 뜻하는지, 단계 안에서 어디까지 고쳐야 빌드되는지 본다
- ㉯ 3단계 "Select_BF가 그대로라 `cur_sw_branch_idx[]`가 모두 0"은 초기화 코드가 5장에 있으므로 3단계에서는 미초기화다. 주장이 성립하는 조건을 본다
- ㉰ 3단계 "기존 동작과 결과가 같아야 한다"의 기준을 본다. 기존 AUTO는 `20`, `21` 파일로 항상 첫 row를 썼다(상위 3장). 구 포맷 파일 기준인지 새 파일 기준인지, 새 파일이면 기존 결과가 무엇인지 본다
- ㉱ 5단계에서 `ITER_MAX_HBF`가 4가 되면 `local_opt.cpp:124-131`이 MN을 바꾼다(관점 12). 이 단계의 기대 결과 서술이 있는지 본다

### 19. 변경 금지 대상, 변경 등급, 문장 규칙

- ㉮ 변경 금지(루트 `CLAUDE.md` 공통 규칙 ㉯): TV 출력 hex 포맷은 그대로여도 출력 시점이 `ITER_MAX_HBF`에 걸려 있다(`TV_Dec_Inter.cpp:1077` 등). PCRC termination 시점(`decoder.cpp:2169`, `2190`)도 같다. 문서가 이 영향을 표기하는지 본다
- ㉯ 변경 등급: 파일 포맷, 구조체, 분기 체계 변경은 설계 변경이므로 Decision 등급이다. 문서가 등급을 밝히고 상위 7장 미결정 사항을 사용자 확인으로 넘기는지 본다
- ㉰ 문장 규칙: 줄표(U+2014)와 가운뎃점(U+00B7)을 두 문서에서 검색한다. 규칙 ㉲(입력 파일의 성격 서술 금지)에 비추어 상위 3장 87~97줄("파일 자체가 이 필드의 원래 값을 잃었다", "`20`, `21`이 그 값을 덮었다")이 파일의 출처나 성격 서술에 해당하는지 본다. 규칙 ㉮(과거와 현재 서술 금지)에 비추어 code_diff 136줄 주석 `(옛 floor_flag)`와 `172`, `372`줄의 "지금도" 서술이 코드 주석과 문서 중 어디에 남는지 본다
- ㉱ 용어 첫 등장 풀어쓰기: SW, BF, HD, CSW, MPI, rank, span, VNU, 1.5SD, PCRC, Corner가 두 문서에서 처음 나올 때 풀어 쓰였는지 본다
- ㉲ 나열 기호: 본문 나열은 ㉮㉯㉰, 주소 받는 갈래는 `- 1.`이다. 두 문서의 나열이 이 규칙을 따르는지 본다
- ㉳ 링크: 상위 문서의 `../../../../0_LDPC_original/src/...`가 `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/`에서 저장소 루트로 올라가는지, code_diff의 `#ch9` 등 앵커가 존재하는지, `corner.h#L79-L81` 형식이 VSCode에서 동작하는지 본다
- ㉴ 작성 시각 형식(`2026-09-02 23:13:58`)과 두 문서의 시각 일치를 본다
