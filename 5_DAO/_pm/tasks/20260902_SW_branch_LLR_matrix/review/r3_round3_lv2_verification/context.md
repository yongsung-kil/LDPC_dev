# Verification Context (Round 3: 검증, lv2)

작성: 2026-09-03 01:27:08

리뷰 대상은 코드가 아니라 코드 수정 계획 문서 두 개다. 실제 C++ 소스는 수정되지 않았고 이 저장소에서는 C++ 빌드를 하지 않는다.

- 상위 문서: `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/20260902_SW_branch_LLR_matrix.md`
- code_diff: `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/code_diff.md` (수정 전후 코드, 앵커 `#ch3` 형태)
- 소스: `0_LDPC_original/src/`
- 새 형태 입력 파일: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`
- 구 형태 입력 파일: `5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt`
- 배경 메모: 루트 `msg1.md`
- Round 2 결과: `../r2_round2_lv2_analysis/report.md` (발견 R2-1 ~ R2-34). 각 발견의 상세 근거는 팀 요약 `team_P_summary.md`, `team_D_summary.md`, `team_I_summary.md`, `team_C_summary.md`에 있다

## Round 2 발견 요약

발견 34건 (CRITICAL 1, HIGH 7, MEDIUM 17, LOW 9). 전체 표는 Round 2 report를 본다. 아래는 검증 대상만 다시 적은 것이다.

## 검증 대상과 팀 배분

### 팀 V1: 빌드 성립과 갈래 통일

| # | 심각도 | 발견 | 처방 원문 | 검증 축 |
|---|--------|------|----------|--------|
| R2-1 | CRITICAL | 비AUTO 빌드에서 code_diff 8.1, 8.2가 `#else` 갈래를 지우면 `Is_Iter_Type_Edge_Clear`, `Is_Iter_Type_Init`이 미초기화 `m_param_LLR`을 매 iteration 역참조. 비AUTO 2SD와 3SD restart 지점 8개 소실. TV Gen에서 `matrix_sel` 가드 소실 | "두 함수의 `#if defined(__AUTO_LLR_OPT__)` 갈래를 유지하거나, 포인터를 NULL로 초기화하고 널 검사를 넣는다. 합친 갈래에 `matrix_sel` 조건을 유지한다" (code_diff 8.1, 8.2가 요구한 코드 삭제를 되돌린다) | 사실: `ECC_Top` 생성자(`ecc_top.cpp:6-34`)와 4인자 `Init_ECC_Top`(`197-210`)이 `m_param_LLR`을 세우지 않는가. 비AUTO 진입점 `main.cpp:105, 127`이 4인자를 부르는가. 두 함수가 컴파일 스위치 없이 매 iteration 불리는가. 저장소 `mode.h` 그대로 빌드하면 비AUTO인가. 처방: 갈래 유지가 계획의 목적(AUTO에서 분기 지원)과 충돌하지 않는가. 대안(비AUTO에서 `restart_iter`를 하드코딩 상수로 채우는 초기화)이 성립하는가 |
| R2-2 | HIGH | `Clear_Flag`(`decoder.cpp:612-613`)가 2.2에서 지우는 두 멤버에 대입. 수정 후 코드가 어느 장에도 없어 양쪽 빌드 컴파일 실패 | "612-613을 지우고 그 자리에 `cur_sw_branch_idx[]`를 0으로 두는 반복문을 넣는다" (코드 삭제) | 사실: 두 멤버의 참조 전수에서 code_diff가 다루지 않는 곳이 612-613뿐인가 (grep 재확인). 처방: 그 자리에 0 채우기를 넣으면 R2-4 ㉯의 미초기화도 함께 해결되는가, 최종 상태에서 `Select_BF`의 앞머리 초기화와 중복이 해가 없는가 |
| R2-4 | HIGH | 9장 적용 순서 불성립. ㉮ 1단계만 넣으면 대체 코드가 3.3, 4.1에 흩어져 빌드 실패. ㉯ 3단계 전제 "`cur_sw_branch_idx[]` 모두 0"이 거짓(채우는 곳은 5.1뿐, `Initialize_Dec`는 포인터만 NULL, `Decoder`는 `ECC_Top`의 값 멤버). ㉰ 0이어도 검증 기준이 뒤집힘(옛 AUTO 루프는 iteration 1~4 그룹 2, 5 그룹 4, 6~8 그룹 5, 새 루프는 그룹 0, 1, 3) | "1단계를 1.1, 2장, 3.3, 4.1을 함께 넣는 것으로 고치거나 2.2의 멤버 삭제를 4단계로 미룬다. 3단계 검증을 분기 줄이 모두 -1인 파일로 기존 결과와 비교하는 것으로 다시 쓴다" (문서 구조 변경) | 사실: 1단계 직후 깨지는 줄 목록(`local_opt.cpp:105, 114, 178`, `decoder.cpp:468, 472, 480, 483, 489, 492, 612, 613`)이 맞는가. `Decoder` 객체가 값 초기화되지 않는 경로가 맞는가. 옛 루프와 새 루프의 그룹 선택 손 실행이 맞는가. 처방: 제안된 단계 재배치로 각 단계가 빌드되는가, "분기 줄 전부 -1 파일"로 기존과 같은 결과가 나오는가(옛 AUTO 루프의 현 파일 결과는 "항상 첫 row"라 비교 기준이 될 수 있는가) |
| R2-12 | MEDIUM | 상위 6.1이 고칠 곳으로 든 `decoder.cpp:1137-1141`과 `6609-6626`에 수정 후 코드 없음. `Get_Cur_LLR_Idx_FILE` 호출은 1138 하나뿐이고 AUTO 안이라 비AUTO 갈래(7001-7047)는 실행되지 않는 코드. 7장 ㉱ 미결정이 실체를 잃음 | "5.3-4와 7장 ㉱에 실행되지 않는 코드임을 적는다. 1137-1141은 7장 ㉱ 결정에 따라 삭제 여부가 정해진다" | 사실: 호출처가 1138 하나뿐인가(grep). 비AUTO의 `Get_VNU_Table_Idx`(7207-7210)가 무조건 0을 돌려주는가. 처방: 1137-1141을 그대로 두면 R2-1 처방(비AUTO 갈래 유지)과 일관되는가 |
| R2-15 | MEDIUM | 3.5가 `local_opt.cpp:124-131`을 다루지 않음. 블록을 지우면 미진입 프레임이 mn 128까지 돎. 블록 안 `MODE_DEC_1_SSD`는 정의 없는 기존 손상 | "3.5에 124-131은 살린다고 적고, 조건 둘째 항을 `MODE_DEC_1_5SD`로 고친다" (식별자 변경) | 사실: `MODE_DEC_1_SSD`가 저장소 전체에서 124행 한 곳뿐인가. `local_opt.cpp`에 AUTO 가드가 없어 모든 빌드에 들어가는가. 처방: `MODE_DEC_1_5SD`로 고치면 1.5SD 프레임도 MN 보정을 받는데 `Select_BF`의 1.5SD 갈래(`mn += 4`)와 맞물려 의도된 동작인가 |

### 팀 V2: 분기 선택 의미론

| # | 심각도 | 발견 | 처방 원문 | 검증 축 |
|---|--------|------|----------|--------|
| R2-3 | HIGH | 구간 번호를 3.2 파서는 등장 순서로, 2.2, 4.1, 5.1은 iteration 1~4와 5~8 고정으로 쓴다. 메모 `msg1.md:31` 예시(1~4 분기 없음, 5~8 분기 셋)에서 5~8이 구간 0이 되어 BF 진입 프레임은 문턱 130으로 고르고 미진입 프레임은 분기 0 고정, 분기 2 영영 미선택, 오류 없음 | "구간을 iteration 범위로 정한다. 파서가 구간별 `iter_start`를 `PARAM_LLR`에 기록하고 `Select_BF`가 그 범위로 문턱 배열을 고르거나, 파서가 구간 0의 시작이 1이 아니면 오류를 낸다" (동작 변경, 두 갈래) | 사실: 메모 예시 헤더(`-1 0 1 2 -1 ...` 형태)를 3.2 파서에 손으로 넣어 span 번호를 계산하고 5.1, 6.1을 손 실행해 결과를 확정. `LLR_MATRIX_1.txt`에서는 우연히 맞는지. 처방: 두 갈래 각각이 메모 예시와 현 파일 양쪽에서 옳은 분기를 고르는가, 부작용(구간이 1~4가 아닌 곳에서 시작하는 파일)은 |
| R2-7 | HIGH | iteration 1~4 분기 존재와 문턱 130이 메모(1~4는 -1), 파일(분기 둘), 수정 전 코드(`TYPE_0` 고정, `TYPE_1` 선택 코드 없음, `syn_th_BF1` 읽는 곳 없음)에서 다르고 미결정에 없음 | "상위 7장에 Decision 항목을 추가하고 사용자 결정을 받는다" (문서) | 사실: `syn_th_BF1` 참조가 선언과 대입 두 곳뿐인가(grep). `FLAG_HD_1_4_SET_TYPE_1` 대입이 없는가. `decoder.h:302-303` 주석 `S-4 Set`이 유일한 단서인가. 처방: Decision으로 올리는 것 외에 문서가 지금 취해야 할 기본값(분기 둘을 유지하고 130을 쓸지, 메모대로 1~4를 분기 없음으로 볼지)에 대한 근거가 코드에 있는가 |
| R2-9 | MEDIUM | 파일의 구간별 분기 개수와 상수 `num_sw_branch[]` 대조 없음. default 갈래 `num_sw_branch[0] = 1`이면 그룹 2가 영영 미선택, 오류 없음. AUTO 빌드에서 `main.cpp:141-143`으로 도달 가능 | "파서가 구간별 분기 수를 세어 `PARAM_LLR`에 기록하고 `Init_Dec_Option` 끝에서 `num_sw_branch[]`, `num_sw_span <= MAX_SW_SPAN`, 문턱 양수 오름차순을 대조해 어긋나면 멈춘다" 또는 "파서가 세어 `num_sw_branch[]`를 채운다" (두 갈래) | 사실: `main.cpp:136-163`에서 `argc > 19`일 때 임의 `matrix_sel`이 들어오는가. `Init_Dec_Option`(`ecc_top.cpp:229`)이 `Read_LLR_info_Auto`(`local_opt.cpp:46`)보다 뒤에 불려 대조를 `Init_Dec_Option` 안에서 할 수 있는가. 처방: 두 갈래 중 어느 쪽이 문턱 개수(분기 수 - 1)와 일관되는가, 파서가 채우면 문턱 값의 출처는 |
| R2-10 | MEDIUM | 첫 분기 그룹 index가 0이 아니면 span이 -1이 되어 6.1이 `cur_sw_branch_idx[-1]`을 읽음(구 파일 `LLR_MATRIX_0.txt`의 `1 2 31`이 실제 사례). 분기 불연속 미검사 | "3.2에 첫 분기 그룹 index가 0이 아니면 오류, 같은 구간 안 index 역행 오류, `num_sw_span > MAX_SW_SPAN` 오류를 넣고 6.1에 `span < 0 || span >= MAX_SW_SPAN` 방어를 둔다" (코드 추가) | 사실: 구 파일 헤더를 3.2에 손으로 넣어 -1이 나오는가. 처방: 검사 셋으로 R2-3의 메모 예시(`-1 0 1 2`)가 오류 없이 통과하는가(통과해야 한다), `err`가 흐름을 바꾸지 않는 문제(R2-8)와 함께 멈추게 하는 처리가 무엇인가 |
| R2-11 | MEDIUM | "분기 일치를 넣으면 순서에 좌우되지 않는다"가 실제 범위를 넘음. 후보 집합 안 iteration 겹침, iteration 1~8 통째 -1 그룹과 5~8 분기 그룹 공존에서 뒤쪽 그룹이 이김 | "문서에 전제(후보 집합 안 iteration 범위 비겹침)를 적고 파서에 구간별, 분기별 범위 겹침 검사를 넣는다" | 사실: 6.1 수정 후 루프를 두 배치(㉮ 같은 분기 안 겹침, ㉯ 1~8 통째 -1 그룹 뒤에 5~8 분기 0 그룹)로 손 실행해 순서를 뒤집었을 때 결과가 바뀌는가. 수정 전 AUTO 갈래도 같은 성질인가 |
| R2-16 | MEDIUM | `ITER_MAX_HBF` 4에서 BF 미진입 프레임은 mn 0에서 5로 건너뛰어 `restart_iter`가 1~4에 있으면 그 프레임만 restart edge clear를 놓침 (현 파일은 `restart_num` 0) | "파서가 `restart_iter[i] <= ITER_MAX_HBF`를 오류로 잡거나 문서에 제약을 적는다" | 사실: `Clear_Edge_Restart`(`decoder.cpp:1133`)가 mn 루프 안에서 `iter == restart_iter[i]`를 그대로 비교하는가. 미진입 프레임의 mn 수열이 0, 5, 6, ...인가. 비AUTO 원본도 같은 성질인가(그렇다면 기존 동작이고 새 결함이 아니다) |

### 팀 V3: iteration 번호 체계, 결과 파일, 파일 변환

| # | 심각도 | 발견 | 처방 원문 | 검증 축 |
|---|--------|------|----------|--------|
| R2-5 | HIGH | `ITER_MAX_HBF` 4에서 `local_opt.cpp:124-131` 보정으로 `MN = [4, -3, -2, -1, 0, ..., 118, 120]`. 결과 파일 FER 열 1~3이 1.0 고정, 머리글 음수. 실행 iteration 124→120. BF 진입 프레임은 row 121~124 미도달. `iter_num -= ITER_MAX_HBF`가 DAO `avg_iteration` 척도를 바꿈. mn 0 종료 프레임 `iter_num` -4 (도달 가능성 미확정) | "㉮ 보정식을 음수가 안 나오게 고치거나 ㉯ AUTO에서도 검사점 5개로 바꾸거나 ㉰ 배열을 두고 열 배치를 문서에 적는다. mn 0 종료 경로에서 보정을 건너뛴다" (㉮㉯는 동작 변경, ㉯는 결과 파일 열 수 변경으로 DAO 파싱까지 영향) | 사실: `MN[]` 손계산이 맞는가. `ecc_top.cpp:877-879`의 비교로 열 1~3만 1.0 고정인가(열 4는 `MN[4] = 0`). `Check_End_Iter`가 mn 0에서 성공을 돌려줄 수 있는가(`decoder.cpp:1947-1949`가 mn 0을 건너뛰는지, `5315`의 `real_mn - 1` 색인). DAO가 결과 파일의 어느 값(`avg_iteration`, 마지막 줄 FER)을 읽는가(`DAO_Main.py:7969-7999`). 처방: 세 갈래 각각이 DAO 파싱을 깨는가, ㉮에서 음수를 막는 식이 무엇이고 BF 진입 프레임의 121~124 미도달을 고치는가 |
| R2-6 | HIGH | code_diff 표들이 변환된 파일을 전제하는데 변환 절차와 파일이 없음. 현 파일을 3.2 파서에 넣으면 분기 줄이 restart 줄부터 읽혀 밀림. DAO 파서는 두 형태 모두 통과 못 함 | "9장 2단계 앞에 파일 변환 단계를 넣고 변환된 파일을 함께 둔다. 6.2 ㉯를 '변환 전 파일은 파싱이 밀린 채 오류 셋이 섞여 나온다'로 다시 쓴다" (문서) | 사실: `LLR_MATRIX_1.txt` 11행 이후를 `fscanf("%d")` 토큰 순서로 3.2 파서에 손으로 넣어 어디까지 밀리는지. DAO 파서(`DAO_LLR_MATRIX.py:476-537`)가 줄 index 기반이라 새 줄을 `num_restart`로 읽는가. `Is_LLR_Valid` RW2(`DAO_LLR_MATRIX.py:344-345`)가 `floor_flag == -1`을 강제하는가. 처방: 두 파서(C++ 토큰 기반, DAO 줄 기반)가 동시에 받을 수 있는 헤더 배치가 있는가 |
| R2-8 | HIGH | 3.4의 `err = TRUE`가 무효(`local_opt.cpp:56` 선언, 140 대입만, void 함수). `printf`는 로그 파일에 안 남고 DAO는 stdout을 안 받으며(`DAO_Main.py:7937`) `main.cpp:69`가 return 0 고정 | "검사 실패 시 프로세스를 멈추거나 종료 코드를 바꾸고 DAO가 그것을 읽게 한다" (동작 변경) | 사실: `err`의 모든 참조(grep). `DAO_Main.py:7937` 부근 `subprocess.run` 인자. `main.cpp:69` 반환. 처방: `exit(1)`이나 종료 코드 반환이 DAO의 `check=True`에서 어떻게 보이는가, MPI 경로(각 rank 별도 프로세스)에서 한 rank의 종료가 어떻게 전파되는가 |

### 팀 B: 재탐색 (breadth)

이전 라운드가 보지 않은 영역을 독립 탐색한다. 이전 라운드의 결론은 공유하지 않는다. 탐색 범위만 공유한다.

이전 라운드가 분석한 파일과 영역: `decoder.cpp`의 `Init_Dec_Option`(452-529), `Clear_Flag`(606-616), 메인 루프 앞머리(1085-1160), `Select_BF` 호출과 정의(1940-1979, 2082-2130), 1bit 갈래(2373-2385, 2796-2804, 4055-4079, 4274-4278), `syn_weight` 계산(3439-3444), `VN_Cal_HD`(3973-4120), `Check_End_Iter`(5303-5362), `Is_Iter_Type_Edge_Clear`와 `Is_Iter_Type_Init`(6538-6676), `Get_Cur_LLR_Idx_FILE`과 `Get_VNU_LLR_SET_FILE`(6973-7123), CSW 로그(7522-7578, 7741-7938), `Adjust_HD_Floor_Type`(8055-8113). `local_opt.cpp` 전체. `common.h`의 모드 상수, SW 문턱, `ITER_MAX_HBF`, flag enum, `GROUP_TYPE_*`. `decoder.h:288-337`. `ecc_data.h:179-198`. `ecc_top.cpp`의 생성자, `Init_ECC_Top`, FER 집계(874-900), 결과 출력(2018-2056), histogram(2736-2811). `main.cpp:47-172, 232, 499-538, 704-781`. `mode.h` 전체. `corner.h`, `corner.cpp`. `mpi.h`, `mpi.cpp`. `TV_Dec_Inter.cpp`의 `ITER_MAX_HBF` 히트. `5_DAO/SRC/DAO_LLR_MATRIX.py:344-345, 476-537`, `DAO_Main.py:7937, 7969-7999`, `Util/Mock_ECC.py`.

이전 라운드가 보지 않은 영역 (이 팀의 탐색 대상):

- ㉮ `mode.h`에서 켜져 있는 `__RUN_PUNCT_RECOVERY__`(61행), `__SHUFFLED_DUAL_DIAG__`(65행), `__PMU_READ__`(66행), `__HALF_COL_UPDATE__`와 `__HALF_COL_MODIFIED__`(68-70행)가 code_diff 수정 후 코드(특히 `ITER_MAX_HBF` 4, BF 부활, `flag_BF_on` 경로)와 맞물리는 곳이 있는가
- ㉯ `MN[n]`(중간 원소)을 읽는 곳 전수 grep과, 값이 `[4, -3, -2, -1, 0, ...]`일 때 각 소비처의 동작
- ㉰ 2SD와 3SD 경로: 8.1 호출처 `decoder.cpp:2328`이 `iter - 1`을 넘기는 점과 파일 `restart_iter`의 한 칸 어긋남, 2SD와 3SD에서 SW 분기를 쓰지 않고 분기 0으로 고정하는 결정이 DAO 사용 방식(HD 위주)에서 문제가 없는가
- ㉱ 극단 입력: 그룹이 0개, 어느 그룹의 row가 0개, `num_row`가 `MN_num`보다 작은 파일에서 3.1, 3.5, 6.1, 6.2의 동작
- ㉲ BF 진입 프레임이 iteration 120까지만 돌아 파일의 121~124 row(그룹 11의 마지막 row들)를 미진입 프레임만 쓰는 비대칭이 그룹 선택과 CSW 기반 row 선택에 미치는 영향
- ㉳ `Get_VNU_LLR_SET_FILE`(`decoder.cpp:7075-7123`)이 `cur_set_idx`로 row를 읽는 경로에서 `num_col`, `num_para_each_set`, dv 그룹 경계가 새 파일(row 20칸, dv 그룹 4개)과 맞는가
- ㉴ 프레임 실패 후 다음 프레임으로 넘어갈 때 `cur_sw_branch_idx[]` 외에 분기와 관련해 초기화가 필요한 상태가 더 있는가 (`Clear_Flag`, `Clear_Iter_Start`, `Initialize_Dec` 전수)

## 검증 생략 항목 (Round 2 요약이 정본)

R2-13, R2-14, R2-17, R2-18, R2-19, R2-20, R2-21, R2-22, R2-23, R2-24, R2-25, R2-26, R2-27 ~ R2-34. 근거가 grep 확정이거나 손계산으로 실증되었고 처방이 문서 보강에 그치거나 현재 빌드에서 컴파일되지 않는 경로다.

## 기술 맥락

- C++ LDPC 디코더. `__AUTO_LLR_OPT__`가 켜지면 LLR 파라미터를 파일(`LOCAL_OPT::Read_LLR_info_Auto`, `local_opt.cpp:52-184`)에서 읽어 `Decoder::Get_Cur_LLR_Idx_FILE(iter)`(`decoder.cpp:6973-7073`)로 매 iteration의 row를 고른다. 호출은 `decoder.cpp:1136-1142`(`mn > 0`)
- BF(Bit Flipping): HD(Hard Decision) 복호 초기 iteration 1~4에서 1bit precision으로 도는 모드. `Select_BF`(`decoder.cpp:2082-2130`, 호출 `1968-1970`, mn 0 루프 끝)가 SW(Syndrome Weight, 신드롬 무게) 문턱으로 진입을 정한다. 미진입이면 `mn`과 `MN`에 `ITER_MAX_HBF`를 더해 iteration 5부터 돈다
- `ITER_MAX_HBF`(`common.h:403-407`): AUTO에서 0, 아니면 4. code_diff 1.2가 4로 통일한다
- 저장소의 `mode.h` 그대로는 `__PROGRAM_MODE_REF_C__`(8행)가 주석이라 `__AUTO_LLR_OPT__`가 정의되지 않는 비AUTO TV Gen 빌드다. DAO가 쓰는 빌드는 사용자가 외부에서 `__PROGRAM_MODE_REF_C__`를 켜고 비Windows로 빌드한 AUTO 빌드다. 두 빌드 모두 유효한 전제다
- SW 문턱 상수는 `common.h:230-251`(`__12META__` 미정의 갈래): `SW_TH_BF_DEFAULT` 630, `SW_TH_BF0_512B_TLC_OFF` 680, `SW_TH_BF1_512B_TLC_OFF` 130, `SW_TH_5_8_SET0_DEFAULT` 960, `SW_TH_5_8_SET0_512B_TLC_OFF` 1100, `SW_TH_5_8_SET1_*` 950
- `GROUP_TYPE_ITER` 0, `GROUP_TYPE_CSW` 1 (`common.h:756-757`). `FLAG_HD_*_SET_TYPE_*` enum은 `common.h:717-725`
- 파서는 `fscanf("%d")` 토큰 기반이라 빈 줄과 탭을 무시한다. DAO의 Python 파서(`DAO_LLR_MATRIX.py:476-537`)는 줄 index 기반이다
- 변경 금지 대상: TV 출력 hex 포맷, HCU 버퍼 레이아웃, Partial CRC 다항식, H-matrix 파일 포맷
- 문장 규칙과 파일 참조 규칙은 루트 `CLAUDE.md`를 따른다. 줄표와 가운뎃점 금지, 나열은 ㉮㉯㉰, 입력 파일의 성격(출처) 서술 금지

## 보고 규칙 (모든 팀 공통)

- 문서와 소스를 수정하지 않는다. 검증 결과만 기록한다
- 각 발견을 가설로 형식화하고("X 조건에서 Y 코드가 Z 동작을 하여 문제 P가 발생한다"), 처방이 붙어 있으면 처방도 가설로 형식화한다("처방 Q를 적용하면 P가 해결되고 새 문제가 생기지 않는다")
- 각 증거를 "확인됨 / 미확인 / 반박됨"으로 분류하고 코드 근거(파일:줄)를 반드시 명시한다
- 판정: 확인됨(증거가 코드에서 확인되고 반례 없음) / 부분 확인(일부 증거 미확인) / 반박됨(코드 근거로 false positive 판명). 처방은 별도로 처방 유효 / 처방 수정 필요(대안 제시) / 처방 반대(적용 금지 사유)
- 심각도 재판정이 필요하면 근거와 함께 적는다
