# 팀 P 워커 2: 관점 10 (파서 견고성과 구 포맷 호환), 관점 11 (MPI rank별 파일 읽기 구조)

리뷰 대상은 상위 문서 `20260902_SW_branch_LLR_matrix.md`와 `code_diff.md`이며, 코드와 문서는 수정하지 않고 발견만 기록한다.

---

## 1. 확인 범위

| 구분 | 읽은 것 | 확인한 내용 |
|------|---------|------------|
| 리뷰 대상 문서 | 상위 문서 4장, 5.1, 5.2, 7장. code_diff.md 1장(상수), 2.1, 3.1~3.7, 4.1, 6.1, 6.2, 9장 | 삽입 위치, 수정 후 코드, 검사 범위, MPI 서술 |
| 파서 소스 | `0_LDPC_original/src/local_opt.cpp` 1~184행 전체, `local_opt.h` 전체 | 생성자, 소멸자, `Run_Local_Opt`, `Run_Simu_Curr_LLR`, `Read_LLR_info_Auto`, `err` 흐름, 로그 블록 |
| 실행 경로 | `main.cpp` 33~120행, 927~975행 | 전역 rank 초기값, MPI 초기화, AUTO 경로 분기, 결과 파일 헤더 출력 |
| 컴파일 스위치 | `mode.h` 1~40행, `common.h` 21행과 32~34행, `build.bat` | `__RUN_MPI__`와 `__AUTO_LLR_OPT__`가 정의되는 조건, `mpi.h` 포함 조건, `-D` 유무 |
| MPI 스텁 | `mpi.h` 전체(23행), `mpi.cpp` 전체(21행) | 선언만 있고 본문이 없는 것, `MPI_Bcast` 시그니처 |
| 상위 호출 | `ecc_top.h:30`, `ecc_top.cpp:216-230`, `ecc_top.cpp:515-516` | rank와 `PARAM_LLR*`가 Decoder로 전달되는 경로 |
| 입력 파일 | `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt` (그룹 12, row 77, 토큰 1584개), `5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt` (그룹 3, row 3, 토큰 87개), `Prime_ECC_2.3`의 같은 이름 파일 (2.4와 내용 동일) | 수정 후 파서로 읽을 때의 토큰 밀림 손 추적. 토큰 흐름을 그대로 흉내 낸 스크립트로 손 추적을 교차 확인했다 |
| DAO 실행 구조 | `5_DAO/3_run_DAO_mpi.bat`, `DAO_Main.py` 506-508, 952-956, 1616-1628, 2340, 6409-6456, 6540-6573, 6597, 7911-7953, 8187-8270, 8461행. `DAO_Constants.py:129`, `DAO_Config.py:438` | Python rank가 각자 파일을 쓰고 EXE를 단일 프로세스로 띄우는 구조, EXE 인자에 rank가 들어가는 자리, 결과 파일을 읽는 방식 |
| 저장소 전체 | `Makefile` 검색 (0_LDPC_original, 5_DAO, 5_DAO/reference, Util) | 저장소 안에 Makefile 없음. `-D__RUN_MPI__`를 주는 빌드 스크립트 없음 |

---

## 2. 관점 10 판정: 파서 견고성과 구 포맷 호환

### 2.1 삽입 위치 대조 (code_diff 3장 대 local_opt.cpp)

| code_diff 절 | 문서가 가리키는 행 | 소스 실제 내용 | 일치 | 비고 |
|------|------|------|------|------|
| 3.1 | 74행 | `num_set_each_group`, `type_each_group` 할당 | 일치 | 새 배열 두 개를 같은 `num_group` 크기로 잡는다 |
| 3.2 | 81~84행 | `type_each_group` 읽는 반복문 | 일치 | 그 뒤, 85행 `restart_num` 앞에 분기 줄 읽기와 구간 계산이 들어간다. 상위 4장 ㉮의 줄 배치(type 줄 아래)와 맞는다 |
| 3.3 | 105, 114, 178행 | `floor_flag` 할당, 읽기, 로그 출력 | 일치 | 178행은 상위 5.1이 인용한 `52-132` 범위 밖이다 (발견 8) |
| 3.4 | 115행 뒤 | row 반복문 닫는 중괄호 | 일치 | 3.5(116행)보다 앞에 온다. 3.4는 `sw_branch_idx`와 `sw_branch_idx_each_group`만 읽고 3.5는 `iter_end`만 읽으므로 두 블록 사이에 자료 의존이 없다 |
| 3.5 | 116~123행 | `MN_num`, `MN` 계산 | 일치 | 124~131행 `ITER_MAX_HBF` 보정은 그대로 둔다 (팀 I 범위) |
| 3.6 | 10~26행 | 소멸자 | 일치 | `floor_flag`가 해제되지 않고 있다는 서술은 사실이다 (12~25행에 없음) |
| 3.7 | 38~44행 | `Run_Simu_Curr_LLR` 안의 `#if defined(__RUN_MPI__)` 블록 | 일치 | 상위 5.2-3은 `36-44` 부근이라 적었고 실제 블록은 38~44행이다. 부근 표기이므로 오류로 보지 않는다 |

파일 이름 형식 `LLR_MATRIX_%d.txt`(59행)는 바뀌지 않는다. DAO의 `LLR_MATRIX_FILE_NAME_TEMPLATE = "LLR_MATRIX_{matrix_idx}.txt"`(`DAO_Config.py:438`)와 계속 맞는다.

### 2.2 `err` 흐름

| 위치 | 내용 | `err`가 읽히는가 |
|------|------|------|
| `local_opt.cpp:56` | `int err = FALSE;` 지역 변수 선언 | 선언 |
| `local_opt.cpp:139-140` | `fclose` 뒤에 `NULL == matrix_in`이면 `err = TRUE` | 쓰기만 |
| code_diff 3.4 | 헤더와 row의 분기 index가 다르면 `printf` 후 `err = TRUE` | 쓰기만 |
| `local_opt.cpp:184` | 함수 끝. 반환형 `void`, `err`를 검사하는 문장 없음 | 읽는 곳 없음 |
| `local_opt.cpp:34-35` | `Read_LLR_info_Auto` 직후 조건 없이 `Run_Simu_Curr_LLR` 호출 | 호출자도 오류를 알 수 없음 |
| `main.cpp:69` | `return 0;` 고정 | 종료 코드로도 전달되지 않음 |

따라서 3.4의 검사는 화면에 `[Error]` 한 줄을 찍을 뿐이고, 어긋난 파일 그대로 복호가 진행된다. DAO 쪽 관찰 가능성도 확인했다.

| DAO 관찰 경로 | 위치 | 결과 |
|------|------|------|
| 표준 출력 | `DAO_Main.py:7937` `subprocess.run([...], check=True)`에 `capture_output`이나 `stdout` 지정 없음 | 화면에만 나가고 DAO는 보지 않는다 |
| 종료 코드 | `check=True`이므로 0이 아니면 `CalledProcessError`로 `MPI_Abort`(7951-7952) | EXE가 항상 0을 돌려주므로(`main.cpp:69`) 발동하지 않는다 |
| 결과 파일 | DAO가 읽는 것은 `result_4KB_..._seed_{rank}.txt`(1616-1628, 8187-8270)이고 숫자 줄만 해석한다 | `Ref_C_result_%d.txt`는 읽지 않으며 정리 시 삭제 대상이다 (`DAO_Constants.py:129`, `DAO_Main.py:952-956`) |

3.4의 `[Error]`는 `printf`이므로 root rank의 로그 파일(`Ref_C_result_%d.txt`, 133~183행)에도 남지 않는다. 9장 2단계의 "대조 검사(3.4장)로 파일이 제대로 읽히는지 본다"는 사용자가 화면을 직접 볼 때만 성립한다.

### 2.3 구 형태 파일 토큰 밀림 추적

파서는 `fscanf("%d")` 토큰 기반이므로 줄 구분은 의미가 없다. 파일의 토큰을 t1부터 번호 매겨 수정 후 파서가 어느 토큰을 어느 칸에 넣는지 추적했다. EOF에 닿으면 `fscanf`가 `c`를 바꾸지 않으므로 직전 값이 그대로 들어간다.

#### 2.3.1 `LLR_MATRIX_0.txt` (그룹 3, row 3, 토큰 87개)

수정 전 해석: t1~t17 헤더(`num_para` 4, `num_dv` 4, `dv_from`, `dv_to`, `num_group` 3, `num_set` 1 1 1, `type` 1 1 1), t18 `restart_num`=1, t19 `restart_iter`=2, t20~t23 `max` 31×4, t24~t27 `min` 0×4, t28~t47 row0, t48~t67 row1, t68~t87 row2.

| 수정 후 파서가 읽는 칸 | 토큰 | 들어가는 값 | 수정 전 해석에서의 뜻 |
|------|------|------|------|
| `sw_branch_idx_each_group[0..2]` | t18~t20 | 1, 2, 31 | `restart_num`, `restart_iter[0]`, `max_value[0]` |
| 구간 계산 | | `num_sw_span`=0, `sw_span_idx_each_group`={-1, -1, -1} | 첫 분기가 0이 아니므로 구간이 하나도 열리지 않은 채 -1이 들어간다 |
| `restart_num` | t21 | 31 | `max_value[1]` |
| `restart_iter[0..30]` | t22~t52 | 31 31 0 0 0 0 + row0 20개 + row1 앞 5개 | 남은 `max`, `min`, row0 전체, row1 일부 |
| `max_value[0..3]` | t53~t56 | -1 -1 -1 -1 | row1의 6~9번째 |
| `min_value[0..3]` | t57~t60 | -1 -1 -1 -1 | row1의 10~13번째 |
| 파서 row0 | t61~t80 | LLR = row1의 14~20번째(-1 -1 -1 -1 2 2 -1) + row2의 1~9번째(5 28 9 5 10 10 9 4 13), CSW 31, iter 10~7, 분기 28 | row1 꼬리와 row2 머리 |
| 파서 row1 | t81~t87, 이후 EOF 13회 | LLR = 12 10 8 -1 3 5 -1 뒤 -1×9, CSW -1, iter -1~-1, 분기 -1 | row2 꼬리, 나머지는 EOF로 -1 유지 |
| 파서 row2 | EOF 20회 | 전부 -1 | |
| 3.4 대조 | | 그룹0 헤더 1 대 row 28, 그룹1 2 대 -1, 그룹2 31 대 -1 → 3건 모두 어긋남 | `[Error]` 3줄 출력 후 계속 진행 |
| 3.5 `max_iter_end` | | 7 (수정 전 해석은 5) | `MN_num`이 달라진다 |

그 뒤 code_diff 6.1에서 세 그룹 모두 `group_branch != SW_BRANCH_NONE`이고 `span = -1`이므로 `cur_sw_branch_idx[-1]`을 읽는다 (배열 앞 메모리 읽기, 미정의 동작). 값이 우연히 맞지 않으면 세 그룹이 전부 건너뛰어져 `selected_group = -1`이 되고, 6.2의 오류 (1)로 `return 0` 하여 매 iteration row 0을 쓴다. 프로세스는 계속된다.

#### 2.3.2 `LLR_MATRIX_1.txt` (그룹 12, row 77, 토큰 1584개)

이 파일은 `type_each_group` 자리에 `{x}{y}` 값(20, 21)을 쓴 형태이고, 4장 ㉮의 분기 전용 줄이 없다. code_diff 3장은 4장 ㉮ 형태를 전제하므로 이 파일도 밀린다.

수정 전 해석: t1~t35 헤더(`num_group` 12, `num_set` 12개, `type` 12개), t36 `restart_num`=0, t37~t40 `max` 31×4, t41~t44 `min` 0×4, t45부터 row 77개 × 20.

| 수정 후 파서가 읽는 칸 | 토큰 | 들어가는 값 | 수정 전 해석에서의 뜻 |
|------|------|------|------|
| `sw_branch_idx_each_group[0..11]` | t36~t47 | 0 31 31 31 31 0 0 0 0 21 0 0 | `restart_num`, `max` 4개, `min` 4개, row0의 1~3번째 |
| 구간 계산 | | `num_sw_span`=3, `sw_span_idx_each_group`={0 0 0 0 0 1 1 1 1 1 2 2} | 분기 31, 21은 `MAX_SW_BRANCH`(9) 밖이지만 걸러지지 않는다 |
| `restart_num` | t48 | 0 | row0의 4번째 |
| `max_value` | t49~t52 | 16 11 5 4 | row0의 5~8번째 |
| `min_value` | t53~t56 | 11 8 4 2 | row0의 9~12번째 |
| 파서 row i (i=0..75) | | LLR = 파일 row i의 13~20번째 + row i+1의 1~8번째, CSW = row i+1의 9번째, iter = row i+1의 10~11번째, 분기 = row i+1의 12번째 | 12토큰씩 밀림. 파서 row0은 CSW 27, iter 16~11, 분기 4 |
| 파서 row76 | | 파일 row76의 13~20번째 뒤 EOF 12회로 -1 | |
| 3.4 대조 | | 77건 중 75건 어긋남 (2건은 우연히 일치) | `[Error]` 75줄 출력 후 계속 진행 |
| 3.5 `max_iter_end` | | 11 (수정 전 해석은 124) | |
| 6.2 | | 그룹 0~5의 `type` 20, 21은 오류 (3)에 걸려 `return 0` | |

결론: code_diff 3장을 적용하면 저장소에 있는 두 형태의 파일 모두 헤더 이후가 밀려 읽힌다. 3장이 성립하려면 4장 ㉮ 형태로 다시 만든 파일이 있어야 하는데, 두 문서 어디에도 구 파일 처리 방침(버전 표시, 변환 도구, 거부 조건)이 없다. code_diff 3.2의 "`LLR_MATRIX_1.txt`에 넣으면 이렇게 나온다" 표와 4.1의 "`LLR_MATRIX_1.txt`는 구간마다 분기 2개이므로 위 값과 맞는다"는 ㉮ 형태로 변환된 파일을 가정한 서술이며, 실제 파일 이름과 맞지 않는다. 9장 2단계와 3단계("기존 동작과 결과가 같아야 한다")도 변환된 파일이 준비된 뒤에만 성립하며, 9장에는 그 준비 단계가 없다.

### 2.4 3.4 검사 범위

3.4는 "헤더의 그룹별 분기 index"와 "row의 분기 index"의 같음만 본다. 아래 조건은 검사되지 않으며, 각각 수정 후 코드가 어디에서 어떻게 무너지는지 확인했다.

| 검사되지 않는 조건 | 통과했을 때 도달하는 곳 | 결과 |
|------|------|------|
| 첫 분기가 0이 아닌 값(예: 1)으로 시작 | code_diff 3.2 구간 계산에서 `num_sw_span`이 오르지 않아 `sw_span_idx = -1` | 6.1 `cur_sw_branch_idx[-1]` 읽기 (미정의 동작) |
| -1 아닌 음수 (예: -2) | `b == SW_BRANCH_NONE`이 거짓이라 분기로 취급, `span = -1` | 위와 같음 |
| 분기 값이 `MAX_SW_BRANCH`(9) 이상 | 4.1의 `num_sw_branch`가 최대 2이므로 `cur_sw_branch_idx[span]`과 영원히 다름 | 그 그룹은 항상 건너뛰어짐. 그 iteration을 덮는 다른 그룹이 없으면 `selected_group = -1` → 6.2 (1) `return 0` → row 0 사용 |
| 분기가 0, 2처럼 건너뜀 | 위와 같음 | 분기 2는 `num_sw_branch`가 3 이상일 때만 선택 가능 |
| `num_sw_span > MAX_SW_SPAN`(4) (분기 index가 0으로 다섯 번 이상 되돌아감) | `sw_span_idx`가 4 이상 | 6.1 `cur_sw_branch_idx[4]` 이상 읽기 (배열 밖, 미정의 동작) |
| 구간 2, 3 (`Select_BF`는 구간 0, 1만 정한다, code_diff 5.1) | `cur_sw_branch_idx[2]`, `[3]`는 초기값 0 | 분기 0만 선택되고 분기 1 이상 그룹은 건너뛰어짐 |
| 같은 구간에 속한 그룹들의 분기 개수와 4.1 `num_sw_branch[span]` 대조 | 4.1이 "검사를 넣으면 막을 수 있다"고 제안만 함 | 파일이 분기 3개를 적어도 문턱은 2분기용이라 분기 2가 선택되지 않음 |
| `type_each_group`이 0, 1 밖 | 3장에서는 통과 | 6.2 오류 (3) `return 0` → row 0 사용 (매 iteration 출력) |
| `iter_start > iter_end` | 3장에서는 통과 | 6.1 범위 검사에 걸리지 않아 후보 탈락. 다른 후보가 없으면 row 0 |
| `num_group`, `num_set_each_group`, `restart_num`, `num_row`가 0 | `new int[0]`은 합법이고 `delete[]`도 합법 | `num_row`=0이면 3.5 `max_iter_end`=0, `MN_num`=0. `iter_end[-1]` 접근은 3.5 수정으로 사라진다 (수정 전 116행은 `iter_end[num_row - 1]`이라 `num_row`=0에서 배열 밖) |
| 위 값이 음수 | `new int[음수]`는 `std::bad_array_new_length` 예외 | 잡는 곳이 없어 프로세스 종료 (기존과 동일) |
| `fopen` 실패 | `local_opt.cpp:61` `fscanf(NULL, ...)` | 크래시. 139행의 NULL 검사는 `fclose` 뒤라 도달하지 못한다 (기존 결함, 두 문서 모두 범위 밖이라 밝히지 않음) |

### 2.5 소멸자

| 확인 항목 | 근거 | 판정 |
|------|------|------|
| `m_param_LLR`의 포인터 초기화 | `local_opt.cpp:3-9` 생성자는 `g_pECC`, `m_ref_c`, `m_ecc_info`, `m_param_dec`만 NULL로 둔다 | `m_param_LLR` 포인터 멤버는 초기화되지 않는다 |
| 읽기 전에 소멸자에 이르는 경로 | `main.cpp:117-119`가 유일한 생성과 삭제 지점이며 그 사이에 `Run_Local_Opt`가 반드시 `Read_LLR_info_Auto`를 호출한다(`local_opt.cpp:34`). `fopen` 실패 시 61행에서 먼저 크래시하므로 소멸자에 이르지 못한다 | 3.6이 추가하는 세 `delete[]`는 항상 할당된 포인터를 받는다. 새 위험 없음 |
| `floor_flag` 미해제 서술 | 12~25행에 `floor_flag` 없음 | 사실. 3.6이 `sw_branch_idx`로 해제하는 것이 맞다 |
| `m_param_dec->MN` | `Run_Simulation_Local_Opt`(`main.cpp:115-120`)는 `MN`을 해제하지 않는다 (`Run_Simulation_Ref_C` 108행은 해제) | 기존 누수. 이번 변경과 무관하며 범위 밖 |

### 2.6 로그 출력

`local_opt.cpp:133-183` root rank 로그 블록은 `num_set_each_group`, `type_each_group`, `restart_num`, `min~max_value`, row 전체를 찍는다. code_diff 3장은 178행의 이름 변경만 언급하고 `sw_branch_idx_each_group`, `sw_span_idx_each_group`, `num_sw_span`을 찍는 줄을 추가하지 않는다. 파서가 계산한 구간 번호는 로그 어디에도 남지 않으므로, 9장 2단계에서 "파일이 제대로 읽혔는지"를 로그로 확인할 수단이 row의 마지막 칸뿐이다.

### 2.7 판정 요약

㉮ 삽입 위치는 3.1~3.7 모두 소스와 일치한다.
㉯ 3.4의 `err = TRUE`는 효과가 없어 검사가 경고에 그친다. DAO는 그 경고를 볼 수 없다 (발견 1).
㉰ 첫 분기가 0이 아니면 `sw_span_idx = -1`이 되어 6.1에서 배열 밖을 읽는다. 구 형태 파일이 정확히 이 경우다 (발견 2).
㉱ 구 파일과 현재 `LLR_MATRIX_1.txt` 모두 밀려 읽히며, 변환 방침이 문서에 없다 (발견 3).
㉲ 3.4 외의 값 범위 검사가 없다 (발견 4).
㉳ 소멸자는 문제 없음. 로그는 새 배열을 찍지 않는다 (발견 5).

---

## 3. 관점 11 판정: MPI rank별 파일 읽기 구조 (작성자 요청 7)

### 3.1 호출 흐름

| 단계 | 위치 | 내용 | rank 조건 |
|------|------|------|------|
| 1 | `main.cpp:36-37` | `g_myrank = ID_ROOT(0)`, `g_num_process = 1` 초기값 | 없음 |
| 2 | `main.cpp:49-53` | `MPI_Init`, `MPI_Comm_size`, `MPI_Comm_rank` | `__RUN_MPI__`일 때만 컴파일 |
| 3 | `main.cpp:54-55` | `Print_Mode_Define_File_Auto(atoi(argv[12]))`: `Ref_C_result_%d.txt`를 "w"로 열어 스위치 상태를 적음 (956-975행) | `__AUTO_LLR_OPT__` |
| 4 | `main.cpp:61-63`, `92-93` | `Setup` 뒤 `Run_Simulation` → `Run_Simulation_Local_Opt` | `__AUTO_LLR_OPT__` |
| 5 | `main.cpp:117-118` | `new LOCAL_OPT`, `Run_Local_Opt(..., g_myrank, g_num_process, TRUE)` | 없음 |
| 6 | `local_opt.cpp:27-34` | rank 저장 후 `Read_LLR_info_Auto` 호출 | rank 검사 없음. 모든 rank가 실행 |
| 7 | `local_opt.cpp:59-131` | `LLR_MATRIX_%d.txt`를 열어 헤더와 row 전체를 `m_param_LLR`에 채우고 `MN`을 계산 | 없음. 모든 rank가 같은 파일을 각자 읽는다 |
| 8 | `local_opt.cpp:133-183` | `Ref_C_result_%d.txt`에 읽은 값을 "a"로 기록 | `ID_ROOT == m_my_rank`만 |
| 9 | `local_opt.cpp:35`, `38-44` | `Run_Simu_Curr_LLR`: `LLR_MATRIX` row별 `MPI_Barrier` + `MPI_Bcast`, `CSW_thr` `MPI_Bcast` | `__RUN_MPI__`일 때만 컴파일 |
| 10 | `local_opt.cpp:45-47` | `Init_ECC_Top(..., &m_param_LLR, m_my_rank, m_num_process)` → `ecc_top.cpp:216-229`가 rank와 `PARAM_LLR*`를 Decoder에 전달 | 없음 |

확정 결론 (1): 각 rank가 파일을 따로 읽는 구조다. 7단계에 rank 검사가 없고, 읽은 값은 그 rank의 `m_param_LLR`에 바로 들어가며, 9단계 Bcast는 이미 같은 값이 든 배열에 root의 값을 덮어쓴다.

### 3.2 `__RUN_MPI__`가 켜지는 조건

| 경로 | `mode.h` | 결과 |
|------|------|------|
| 10행 | `//#define __RUN_MPI__` 주석 | 미정의 |
| Windows (`_WIN32`, `_WIN64`) | 18~19행에서 `__WIN_OS__`만 정의 | `__RUN_MPI__` 미정의. `__AUTO_LLR_OPT__`도 `mode.h`에서는 정의되지 않는다 |
| 비Windows, `__PROGRAM_MODE_REF_C__` 정의 | 21~25행: 22행에서 `__AUTO_LLR_OPT__`를 정의한 직후 23행 `#if !defined(__AUTO_LLR_OPT__)` 안에서 24행 `__RUN_MPI__`를 정의 | 23행 조건이 항상 거짓이라 `__RUN_MPI__` 미정의. AUTO와 MPI는 `mode.h`에서 상호 배타 |
| 비Windows, REF_C 미정의 | 21행 건너뜀 | 둘 다 미정의 |
| 컴파일러 옵션 | `build.bat`에 `-D` 없음, 저장소 안에 Makefile 없음 (DAO가 기대하는 `Util/Makefile`도 없음, `DAO_Constants.py:120`) | `-D__RUN_MPI__`를 주는 빌드 스크립트가 저장소에 없다. 외부 빌드는 확인 범위 밖 |
| 실행 시 확인 수단 | `main.cpp:971-975`가 `Ref_C_result_%d.txt` 첫머리에 `__RUN_MPI__\tON` 또는 `OFF`를 적는다 | 외부 빌드 산출물의 이 줄로 판정할 수 있다 (단, DAO는 정리 시 이 파일을 지운다, `DAO_Main.py:952-956`) |

`mpi.h`(23행)와 `mpi.cpp`(21행)는 둘 다 include guard `ECCTG_MPI_H` 아래 `MPI_COMM_WORLD 0`, `MPI_INT 0` 정의와 함수 선언만 담고 있으며 본문이 하나도 없다. 머리 주석 "ONLY FOR COMPILE IN WINDOWS / REMOVE FOR SUPERCOM"대로, `__RUN_MPI__`를 켠 채 이 스텁으로 빌드하면 컴파일은 되어도 링크에서 `MPI_Init` 등이 미해결 외부 기호가 된다. 실제 MPI 실행은 스텁을 걷어내고 진짜 MPI 헤더와 라이브러리로 빌드하는 환경에서만 가능하다.

### 3.3 DAO 실행 구조

| 단계 | 위치 | 내용 |
|------|------|------|
| MPI 시작 | `5_DAO/3_run_DAO_mpi.bat`: `mpiexec -n 4 python DAO_Main.py 1 2 3 4` | MPI는 Python 프로세스 4개 사이에서만 돈다 (mpi4py) |
| rank | `DAO_Main.py:506-508` `self.rank`, `self.is_root = rank == 0` | Python 쪽 rank |
| 파일 쓰기 | `DAO_Main.py:2340`, `8461` `Save_LLR_Matrix(target_dir=self.local_session_dir, save_root_only=False)` | rank마다 자기 `Process_{rank}` 디렉터리(6597행)에 `LLR_MATRIX_{idx}.txt`를 쓴다 |
| EXE 인자 | `DAO_Main.py:6409-6456` `Get_Ref_C_Args` | 12번째 인자가 `self.rank`, 17번째가 `matrix_idx`. 프로세스 수를 주는 인자는 없다 |
| 배치 | `DAO_Main.py:6540-6573` `Make_Batch_File`: `cd /d "%~dp0"` 뒤 `"EXE" 인자들` | `mpiexec`로 감싸지 않은 단일 프로세스 실행 |
| 실행 | `DAO_Main.py:7937` `subprocess.run(["cmd","/c",batch], cwd=Process_{rank}, check=True)` | rank마다 EXE 한 개. EXE 안에서는 `g_myrank = 0`, `g_num_process = 1` |
| EXE 안에서 rank의 쓰임 | `main.cpp:237` `mode_init_seed = argv[12]`, `265` `Ref_C_result_%d.txt` 이름, `local_opt.cpp:135` 같은 이름 | 시드와 결과 파일 이름에만 쓰인다 |

즉 DAO 환경에서 EXE는 rank마다 독립 프로세스이고, 각 프로세스가 자기 디렉터리의 `LLR_MATRIX_{idx}.txt`를 읽는다. C++ 안의 `__RUN_MPI__` 경로는 이 구조에서 쓰이지 않는다.

### 3.4 Bcast 형식 대조

code_diff 3.7이 추가하는 네 줄을 `mpi.h:21` 시그니처 `void MPI_Bcast(int* src, int size, int type, int root, int communicator)`와 할당 크기에 대조했다.

| 추가 줄 | 첫 인자 형 | 크기 인자 | 할당 크기 (code_diff 3.1, 3.3) | 판정 |
|------|------|------|------|------|
| `&m_param_LLR.sw_branch_idx[0]` | `int*` | `num_row` | `new int[num_row]` | 맞음 |
| `&m_param_LLR.sw_branch_idx_each_group[0]` | `int*` | `num_group` | `new int[num_group]` | 맞음 |
| `&m_param_LLR.sw_span_idx_each_group[0]` | `int*` | `num_group` | `new int[num_group]` | 맞음 |
| `&m_param_LLR.num_sw_span` | `int*` | 1 | 스칼라 멤버 | 맞음 |

기존 코드가 row마다 `MPI_Barrier`를 두는 것은 스타일이며, 추가 줄에 Barrier가 없어도 `MPI_Bcast`는 집합 통신이라 순서가 어긋나지 않는다. `num_row`, `num_group`은 각 rank가 파일에서 같은 값을 읽으므로 크기 불일치도 없다.

기존 Bcast가 `LLR_MATRIX`와 `CSW_thr`만 뿌리는 이유도 확인했다. `PARAM_OPT`(`ecc_data.h:200-224`)에 `opt_LLR_MATRIX`, `opt_CSW_thr`, `curr_value`, `curr_row_idx` 등 최적화 루프용 멤버가 남아 있고 지금은 `matrix_idx`, `curr_FER`, `curr_Avit`만 참조된다 (`local_opt.cpp:33, 49-50`). 뿌리는 두 배열이 정확히 그 멤버와 대응하므로, 이 Bcast는 root가 행렬을 바꿔 가며 다른 rank에 배포하던 옛 루프의 잔재다. 지금 코드에는 root가 값을 바꾸는 곳이 없다.

### 3.5 확정 결론

- 1. 각 rank가 파일을 따로 읽는 구조다. `Read_LLR_info_Auto`에 rank 조건이 없고(`local_opt.cpp:27-34`), 모든 rank가 같은 이름의 파일을 열어 헤더와 row 전체를 자기 `m_param_LLR`에 넣는다. root만 다른 것은 로그 출력(133행)뿐이다.
- 2. code_diff 3.7의 Bcast 추가는 필수가 아니다. ㉮ `mode.h` 18~27행의 어느 경로에서도 `__RUN_MPI__`가 정의되지 않고 `__AUTO_LLR_OPT__`와 상호 배타이므로, `-D`로 강제하지 않는 한 3.7은 컴파일되지 않는 죽은 코드다. ㉯ 진짜 MPI 환경에서 `-D__RUN_MPI__`로 켜더라도 모든 rank가 이미 같은 값을 읽은 뒤이므로 무해한 중복이다. 넣어도 틀리지 않고(형식과 크기 모두 맞음) 빼도 동작이 같다. ㉰ DAO 환경에서는 EXE가 rank마다 단일 프로세스로 돌기 때문에 이 경로 자체가 쓰이지 않는다.
- 3. 문서 정합: code_diff 3.7은 "각 rank가 파일을 따로 읽는 구조라면 이 추가는 필요 없다 ... 확인한 뒤 맞춘다"고 조건부로 적었고, 상위 5.2-3은 "함께 실어야 한다"고 단정했다. 확인 결과는 조건부 서술 쪽의 "필요 없다"에 해당하므로 두 문서를 "선택 사항, 넣는다면 형식은 3.7과 같다"로 맞추면 된다 (발견 7).
- 4. 확인 범위: `main.cpp`, `local_opt.cpp`, `mode.h`, `common.h`, `mpi.h`, `mpi.cpp`, `build.bat`, `ecc_top.cpp:216-230`, DAO 실행 경로(`3_run_DAO_mpi.bat`, `DAO_Main.py`의 파일 저장, 인자 구성, 배치 생성, 실행, 결과 읽기). 외부 빌드 환경의 컴파일 옵션은 저장소에 없어 확인하지 못했으며, `Ref_C_result_*.txt`의 `__RUN_MPI__` 줄로 판정할 수 있다.

---

## 4. 발견 목록

| 번호 | 심각도 | 구분 | 문제 | 근거 | 처방 | 처방 성격 |
|------|------|------|------|------|------|------|
| 1 | HIGH | 수정 후 코드 결함 | code_diff 3.4의 `err = TRUE`는 아무 효과가 없다. `err`는 `local_opt.cpp:56`에서 선언되어 140행과 3.4에서 쓰이기만 하고 읽히는 곳이 없으며, 함수는 `void`이고 `Run_Local_Opt`(34~35행)는 조건 없이 복호를 시작한다. 어긋난 파일이 그대로 복호에 쓰인다. `[Error]`는 `printf`라 root 로그 파일에도 남지 않고, DAO는 표준 출력을 받지 않고(`DAO_Main.py:7937`) 종료 코드는 항상 0(`main.cpp:69`)이라 감지할 수 없다. 상위 5.1과 code_diff 9장 2단계는 이 한계를 적지 않는다 | `local_opt.cpp:34-35, 56, 140, 184`, `main.cpp:69`, `DAO_Main.py:7937, 7951-7952`, code_diff 3.4, 9장 2단계 | 3.4에서 어긋남을 발견하면 `fp_auto_result`에 같은 줄을 남기고 `exit(1)` 또는 반환값으로 `Run_Simu_Curr_LLR` 호출을 막는다. DAO는 `check=True`이므로 0이 아닌 종료 코드를 받으면 `MPI_Abort`로 멈춘다는 점을 문서에 함께 적는다 | 동작 변경 (오류 시 복호를 하지 않음). 코드 삭제 없음 |
| 2 | HIGH | 수정 후 코드 결함 (관점 3과 겹침) | code_diff 3.2의 구간 계산은 첫 유효 분기가 0이 아니거나(-1 아닌 음수 포함) 분기 index가 0에서 시작하지 않으면 `num_sw_span`을 올리지 않아 `sw_span_idx_each_group = -1`을 남긴다. 6.1은 `group_branch != SW_BRANCH_NONE`인 그룹에 대해 `cur_sw_branch_idx[span]`을 읽으므로 index -1 접근이 된다. 구 형태 파일(2.3.1 추적: 분기 줄이 1, 2, 31로 읽힘)이 정확히 이 경우다. `num_sw_span > MAX_SW_SPAN`(4)이면 반대쪽으로 배열 밖이다 | code_diff 3.2, 6.1 (`span = sw_span_idx_each_group[g]; if (group_branch != cur_sw_branch_idx[span])`), code_diff 1장 `MAX_SW_SPAN 4` | 3.4에 ㉮ `b != -1`이면 `0 <= b < MAX_SW_BRANCH`, ㉯ 계산된 `span`이 `-1`이 아니면서 `b != -1`인 그룹이 없을 것, ㉰ `num_sw_span <= MAX_SW_SPAN` 검사를 추가하고 발견 1의 처리로 넘긴다 | 검사 추가 (동작 변경: 잘못된 파일을 거부). 코드 삭제 없음 |
| 3 | MEDIUM | 문서 서술 누락 | 구 포맷 처리 방침이 두 문서 어디에도 없다. 2.3의 추적대로 저장소의 두 형태 파일 모두 수정 후 파서에서 헤더 이후가 밀려 읽힌다. code_diff 3.2의 "`LLR_MATRIX_1.txt`에 넣으면 이렇게 나온다" 표와 4.1의 "`LLR_MATRIX_1.txt`는 구간마다 분기 2개이므로"는 4장 ㉮로 변환된 파일을 가정한 서술이며 실제 파일과 다르다. 9장 3단계 "기존 동작과 결과가 같아야 한다"는 변환된 파일이 있어야 성립하는데 9장에 파일 준비 단계가 없다 | 2.3.1, 2.3.2 추적표. code_diff 3.2 표, 4.1, 9장. 상위 4장 ㉮, 7장 | 문서에 ㉮ 새 파서는 4장 ㉮ 형태만 읽는다는 것, ㉯ 현재 `LLR_MATRIX_1.txt`와 구 파일을 누가 어떻게 변환하는지(DAO 저장기 또는 별도 도구), ㉰ 9장 1단계 앞에 "변환된 파일 준비"를 넣는다. 구 파일을 자동 감지하는 것은 토큰 기반 파서에서 불가능하므로 방침은 "변환"이어야 한다 | 문서 보강. 코드 변경 없음 |
| 4 | MEDIUM | 수정 후 코드 결함 (누락 커버리지) | 3.4는 헤더와 row의 같음만 본다. 2.4 표의 조건(분기 범위, 연속성, `type` 값 범위, `iter_start <= iter_end`, 구간 수 상한, 4.1 `num_sw_branch`와 파일의 분기 개수 대조)이 검사되지 않고, 대부분 6.2의 `return 0`으로 row 0을 조용히 쓰는 결과가 된다. 4.1의 "`num_sw_branch[]`를 파일에서 읽은 값과 대조하는 검사를 넣으면"은 제안만 있고 코드가 없다 | 2.4 표, code_diff 3.4, 4.1 마지막 문단, 6.2 | 발견 2의 검사에 더해 `type ∈ {0, 1}`, `iter_start <= iter_end`, 구간별 분기 개수와 `num_sw_branch[span]` 일치를 3.4에 넣는다. 구간별 분기 개수 대조는 `Init_Dec_Option`이 `LOCAL_OPT`보다 뒤에 돌므로(`local_opt.cpp:46` → `ecc_top.cpp:229`) 검사 위치를 `Init_Dec_Option` 끝으로 옮기거나 파일 쪽 값을 Decoder에 넘겨 대조해야 한다는 점을 문서에 적는다 | 검사 추가 (동작 변경: 잘못된 파일을 거부). 코드 삭제 없음 |
| 5 | LOW | 문서 서술 누락 | `local_opt.cpp:133-183` 로그에 `sw_branch_idx_each_group`, `sw_span_idx_each_group`, `num_sw_span`을 찍는 줄이 없다. 파서가 계산한 구간 번호를 확인할 유일한 출력이 없어 9장 2단계의 확인이 row 마지막 칸(178행)에만 의존한다 | `local_opt.cpp:143-168`, code_diff 3.3 "178행의 로그 출력도 같은 이름으로 바꾼다" | 3.3 또는 3.4에 `type_each_group` 출력(151~155행) 뒤로 세 항목의 `fprintf`를 추가한다 | 로그 추가 (Safe). 코드 삭제 없음 |
| 6 | LOW | 문서 서술 누락 (기존 결함, 범위 표시 없음) | `fopen` 실패 시 61행 `fscanf(NULL, ...)`에서 크래시하며 139행의 NULL 검사는 `fclose`(132행) 뒤라 도달하지 못한다. 3장은 이 구간을 그대로 두면서 범위 밖이라 밝히지 않는다 | `local_opt.cpp:60-61, 132, 139-142` | 3장 머리에 "`fopen` 실패 처리는 이번 범위 밖"이라 적거나, 발견 1의 처리와 함께 60행 뒤에 NULL 검사를 옮긴다 | 문서 보강 또는 검사 이동 (동작 변경: 크래시 대신 종료). 코드 삭제 없음 |
| 7 | LOW | 문서 상충 | code_diff 3.7은 Bcast 추가를 조건부("확인한 뒤 맞춘다")로, 상위 5.2-3은 필수("함께 실어야 한다")로 적었다. 3장 확인 결과 각 rank가 파일을 따로 읽고, `__RUN_MPI__`는 `mode.h`의 어느 경로에서도 `__AUTO_LLR_OPT__`와 함께 켜지지 않으며, 켜더라도 무해한 중복이다. `mpi.cpp`에 함수 본문이 없어 스텁으로는 링크되지 않는다 | `local_opt.cpp:27-35, 38-44`, `mode.h:18-27`, `mpi.h:21`, `mpi.cpp` 전체, `main.cpp:36-37, 49-53`, `DAO_Main.py:6540-6573, 7937` | 상위 5.2-3을 "각 rank가 파일을 따로 읽으므로 선택 사항. 넣는다면 code_diff 3.7의 형식"으로 바꾸고, code_diff 3.7의 마지막 문단을 확인 결과로 확정한다 | 문서 수정. 코드 변경 없음 |
| 8 | LOW | 문서 인용 오류 | 상위 5.1이 `Read_LLR_info_Auto`를 `local_opt.cpp:52-132`로 인용했으나 함수는 52~184행이고, 5.1-2가 함께 가리키는 178행(로그 출력)은 인용 범위 밖이다 | `local_opt.cpp:52, 184`, 상위 5.1 | `52-184`로 고친다 | 문서 수정. 코드 변경 없음 |
| 9 | LOW | 확인 정보 (문제 없음) | ㉮ `num_group`, `restart_num`, `num_row`가 0이면 `new int[0]`과 `delete[]` 모두 합법이며, 3.5 수정으로 `num_row`=0에서의 `iter_end[-1]` 접근(수정 전 116행)이 사라진다. 음수는 `std::bad_array_new_length`로 종료되며 기존과 같다. ㉯ 3.6의 `delete[]` 추가는 새 위험이 없다 (생성부터 소멸까지 경로가 하나이고 그 사이에 반드시 할당된다). ㉰ `m_param_dec->MN` 누수(`main.cpp:115-120`)는 기존 것으로 범위 밖 | 2.4 표 하단, 2.5 표 | 없음 | 없음 |
