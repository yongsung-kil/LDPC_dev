# 워커 P_3: 관점 16 (DAO 쪽 도구 영향)

> 팀 P (파일 형식과 파서), Round 2 lv2 분석. 읽기만 했고 코드와 문서를 고치지 않았다. `5_DAO/reference/`는 대상에서 뺐다.

두 파일 형태의 정의는 다음과 같다.

- ㉮ 형태 (1): 현재 `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`. `type_each_group` 줄이 `20 20 21 20 21 21 1 1 1 1 1 1`, row 마지막 칸이 0, 1, -1
- ㉯ 형태 (2): 상위 문서 4장 ㉮ 추천안. `type_each_group` 줄이 전부 1, 그 바로 아래에 `sw_branch_idx_each_group` 줄(`0 0 1 0 1 1 -1 -1 -1 -1 -1 -1`)이 새로 들어감. row 마지막 칸은 그대로

---

## 1. 확인 범위

| 파일 | 읽은 줄 | 확인한 것 |
|------|---------|----------|
| `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/20260902_SW_branch_LLR_matrix.md` (상위 문서) | 1~100, 101~164, 234~289, 353~362 | 1장 범위 선언, 2장 그룹 표, 4장 ㉮ 예시 헤더, 5.1, 5.5, 7장 미결정 사항 |
| `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/code_diff.md` | 전제, 3장, 그리고 `DAO`, `Python`, `Mock` 검색 (0건) | DAO 언급 유무 |
| `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt` | 전체 (물리 105줄, 비어 있지 않은 줄 87줄) | 헤더 10줄, row 77줄, 공백 전용 구분 줄 위치 |
| `5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt` | 전체 | 구 형태(type 전부 1, restart 1개, flag 전부 -1) |
| `5_DAO/Input/Ref_C/Prime_ECC_3.0/` | 디렉토리 목록 | `EXE/` 비어 있음, `SRC/` 없음, `Initial_LLR_matrix/LLR_MATRIX_1.txt`만 존재 |
| `0_LDPC_original/src/local_opt.cpp` | 52~183 | `fscanf` 순서, `MN_num`, `MN[]` 보정, `Ref_C_result_%d.txt` 로그 |
| `0_LDPC_original/src/decoder.cpp` | 1040~1053, 1905~1999, 7712~7776, 7868, 7929~7937, 8007~8015 | `iter_num -= ITER_MAX_HBF`, `m_log_CSW_auto` 초기화 -1, `Print_Log_CSW_Auto` 열 수, `m_log_LLR_idx` |
| `0_LDPC_original/src/ecc_top.cpp` | 858~962, 2224~2289 | `fr_4KB[n]` 집계 조건 `o_iter_num > MN[n]`, 결과 줄 형식 |
| `5_DAO/SRC/DAO_LLR_MATRIX.py` | 92~218, 266~449, 455~545, 549~559 | 쓰기 함수, `Is_LLR_Valid`, 읽기 함수, `max_iteration` |
| `5_DAO/SRC/DAO_Main.py` | 454~465, 855~933, 1805~1892, 2314~2343, 2563~2585, 3572~3630, 5108~5134, 8187~8281, 9898~9909, 10227~10250, 그리고 `type_each_group`, `floor_flag`, `max_iteration`, `avg_iteration` 검색 | 경로 구성, 빌드 조건, 결과 취합, 초기화 순서, GenLLRMode의 헤더 조작, 결과 파일 파싱, CSW 로그 파싱 |
| `5_DAO/SRC/DAO_Constants.py` | 1~132 | 경로 이름 상수, `HEADER_TO_REMOVE`, GenLLRMode 목록 |
| `5_DAO/SRC/DAO_Config.py` | 121~143, 169, 그리고 경로 필드 검색 | `INITIAL_MATRIX_IDX` 기본값 999, `ECC_VER` 3.0 |
| `5_DAO/DAO_spec.md` | 1~200 | 헤더 필드표(27~41), row 필드표(45~52), 규칙 H1~H5, G1~G6, RW1~RW5 |
| `5_DAO/README.md` | 304~330, 895~908, 1184~1213, 그리고 `EXE`, `Ref_C/`, `0_LDPC_original` 검색 | 필드 목록, 초기 매트릭스 위치, 경로 설정, 실행 파일 배치 서술 유무 |
| `5_DAO/Util/Mock_ECC.py` | 전체 | 헤더 건너뛰기 index, `max_iteration` 출처 |
| `5_DAO/Util/README_Mock_ECC.md` | 110 | 매트릭스 읽기 서술 |
| `5_DAO/Util/collect_llr_matrices.py`, `5_DAO/Util/rename_llr_idx.py` | 전체 | 내용 해석 여부 |
| `5_DAO/_pm/TODO.md` | 전체 | DAO 후속 작업 항목 |
| `msg1.md` (루트) | 전체 | 생성 주체 서술 유무, "DAO는 BF가 없다고 가정" |

---

## 2. DAO 파서 줄 index 대조표

`DAO_LLR_MATRIX.py:459-465`는 파일을 읽어 `strip()` 후 비어 있지 않은 줄만 남긴다. 따라서 `LLR_MATRIX_1.txt`의 빈 줄과 탭만 있는 구분 줄(물리 2, 4, 7, 9, 12, 14, 17, 19, 27, 34, 41, 43, 49, 55, 63, 70, 81, 92줄)은 모두 사라지고, index는 남은 줄에 0부터 매겨진다. 각 줄은 `int` 변환하므로 `-1`도 문제 없이 읽힌다. `DAO_LLR_MATRIX.py:467-474`의 `get_line`은 index가 줄 수를 넘을 때만 `ValueError`를 낸다.

### 2.1 형태 (1): `LLR_MATRIX_1.txt` 그대로

| index | 줄 내용 | 읽는 코드 | 들어가는 필드 | 결과 |
|------:|---------|-----------|---------------|------|
| 0 | `4` | `DAO_LLR_MATRIX.py:477` | `num_parameter_each_set` = 4 | 정상 |
| 1 | `4` | `:478` | `num_dv` = 4 | 정상 |
| 2 | `11 4 3 2` | `:479` | `dv_from` | 정상 |
| 3 | `11 4 3 2` | `:480` | `dv_to` | 정상 |
| 4 | `12` | `:481` | `num_group` = 12 | 정상 |
| 5 | `1 7 6 6 1 5 5 7 6 10 10 13` | `:482` | `num_row_each_group` (합 77) | 정상 |
| 6 | `20 20 21 20 21 21 1 1 1 1 1 1` | `:483` | `type_each_group` | 값 검사 없이 그대로 보관. 20, 21이 0 또는 1이어야 한다는 검사는 파서에도 `Is_LLR_Valid`에도 없다 (`:282-284`는 길이만 본다) |
| 7 | `0` | `:485` | `num_restart` = 0, `restart_iter` = [] | 정상 |
| 8 | `31 31 31 31` | `:491` | `max_value` | 정상 |
| 9 | `0 0 0 0` | `:492` | `min_value` | 정상 |
| 10~86 | row 77줄 | `:508-537` | `row[:-4]` 16개, `CSW`, `iter_start`, `iter_end`, `floor_flag` | 정상. `floor_flag`에 0, 1, -1이 그대로 들어간다 |

`Is_LLR_Valid` 진행: H1~H5 통과(`:276-290`). 그룹 0 (row 1개, iteration 1~1, `floor_flag` 0)의 row 검사에서 `DAO_LLR_MATRIX.py:344-346` RW2가 `"Group 0 Row 0 invalid floor_flag 0"`으로 거부한다. RW2를 통과했다고 가정하면 다음은 G2(`:305-312`)가 그룹 2(iteration 1~4, 이전 그룹 끝 4)에서 `"Group 2 iter_start must be exactly one greater than previous group's iter_end: 1 vs 4"`로 거부하고, 그룹 4(5~5, 이전 끝 8)도 같은 이유로 거부한다. 그룹 5(6~8, 이전 끝 5)와 그룹 6(9~24, 이전 끝 8)은 우연히 이어진다.

호출 쪽: `DAO_Main.py:2325-2343` `Initialize_LLR_Matrix`가 `Save_LLR_Matrix`(`:2338`, `:2340`)를 먼저 하고 `Validate_LLR_Matrix`(`:2341`)를 한 뒤 `MPI_Abort("Initial LLR matrix validation failed.")`(`:2343`)로 멈춘다. 저장된 사본에는 20, 21과 0, 1이 그대로 남는다.

### 2.2 형태 (2): 4장 ㉮ 추천안 (신규 줄이 index 7에 끼어듦)

| index | 줄 내용 | 읽는 코드 | 들어가는 필드 | 결과 |
|------:|---------|-----------|---------------|------|
| 0~5 | (형태 (1)과 같음) | `:477-482` | 같음 | 정상 |
| 6 | `1 1 1 1 1 1 1 1 1 1 1 1` | `:483` | `type_each_group` | 정상 |
| 7 | `0 0 1 0 1 1 -1 -1 -1 -1 -1 -1` | `:485` | `num_restart` = 첫 토큰 0 | 오독. 첫 토큰만 쓰고 나머지 11개 토큰은 소리 없이 버린다. 값이 0이라 `restart_iter`를 읽지 않는다 |
| 8 | `0` (실제 `restart_num`) | `:491` | `max_value` = [0] | 오독 (길이 1) |
| 9 | `31 31 31 31` (실제 `max_value`) | `:492` | `min_value` | 오독 |
| 10 | `0 0 0 0` (실제 `min_value`) | `:523-528` | 그룹 0의 row 0: `ch_th_values` = [] (빈 배열), `CSW` 0, `iter_start` 0, `iter_end` 0, `floor_flag` 0 | 오독 |
| 11~86 | 실제 row 1~76 | `:510-537` | 그룹 경계가 한 줄씩 밀린다 (그룹 1이 실제 그룹 0의 row와 실제 그룹 1의 앞 6 row를 갖는 식) | 오독 |
| 87 | 실제 row 77 (마지막 그룹의 마지막 row) | 읽지 않음 | `parsed[10:87]`에서 빠짐 | 소실 |

`total_rows`(77)와 `len(matrix_rows)`(77)가 같으므로 `:511-514`의 row 수 검사는 통과하고 예외가 나지 않는다. `Is_LLR_Valid`는 H1(0 == 0), H2, H3(12)를 지나 H4(`:285-287`)에서 `"max_value length mismatch"`로 거부한다. 메시지가 실제 원인(헤더 줄 추가)을 가리키지 않는다. 거부 전에 `:2338`, `:2340`이 밀린 구조 그대로를 파일로 저장하고, 신규 줄은 어디에도 남지 않는다.

### 2.3 `Mock_ECC.py`의 같은 대조

`Mock_ECC.py:78-94`도 같은 방식(빈 줄 제거 후 index)이다. `:88`이 `type_each_group`을 건너뛰므로 형태 (1)은 값과 무관하게 정상이고, `max_iteration`은 `:101-103`에서 마지막 row의 `row[-2]` = 124. 형태 (2)는 index 7을 `num_restart`(0)로 읽고 8, 9를 `max_value`, `min_value`로 건너뛰어 row가 index 10부터 시작하므로 `matrix_rows[-1]`은 실제 row 76이 된다. 그 row의 `iter_end`가 124라 결과 값은 우연히 같다. 마지막 그룹의 row가 1개인 파일이었다면 앞 그룹의 값이 나온다.

---

## 3. 도구별 영향 표

| 도구 (근거) | 형태 (1) 영향 | 형태 (2) 영향 | 심각도 |
|------|--------------|--------------|--------|
| `Read_Input_LLR_Matrix` (`DAO_LLR_MATRIX.py:476-537`) | 예외 없이 읽힘. 20, 21을 검사 없이 보관 | 헤더 한 줄 밀림, `num_restart` 오독, `max_value` 길이 1, row 하나 소실, 예외 없음 | HIGH |
| `Is_LLR_Valid` (`:266-449`) | RW2(`:344-346`)가 그룹 0 row 0에서 거부. 통과 시 G2(`:305-312`)가 그룹 2와 4에서 거부 | H4(`:285-287`)가 거부. 메시지가 원인을 가리키지 않음 | HIGH |
| `Initialize_LLR_Matrix` (`DAO_Main.py:2325-2343`) | 사본 저장 후 `MPI_Abort` | 손상된 사본 저장 후 `MPI_Abort` | HIGH |
| `Build_LLR_Matrix_Output_Lines`, `Save_Matrix` (`DAO_LLR_MATRIX.py:122-145`, `195-201`, `549-559`) | 20, 21과 0, 1을 그대로 기록 | 신규 줄을 쓰는 코드가 없어 소실. 형태 (2)를 읽어 다시 쓰면 형태 (2)가 아니게 됨 | MEDIUM |
| GenLLRMode의 헤더 조작 (`DAO_Main.py:2715`, `3073`, `3579`, `5113-5134`는 `type_each_group`에 1 또는 0 삽입, `2399`, `2623`, `2831`, `3389`, `3620`, `4933`, `4962`는 `floor_flag`를 참조 그룹 첫 row에서 복사) | 검증 거부로 도달하지 못함. 도달한다면 삽입 그룹의 type은 1, `floor_flag`는 복사 | 같음. 신규 줄에 대응하는 필드가 없어 그룹을 넣고 빼도 분기 index 줄이 따라가지 않음 | MEDIUM |
| `max_iteration` 계산 (`DAO_LLR_MATRIX.py:441`, `207-218`, `DAO_Main.py:2743`, `3099`, `3320`, `3454`, `5645`, `5939`) | 마지막 그룹의 마지막 row `iter_end` = 124. 이 파일에서는 마지막 그룹이 105~124라 우연히 맞음 | 같음 | MEDIUM |
| 그룹 연속성과 분할 논리 (`Is_LLR_Valid` G2, `DAO_Main.py:3367-3383` 분할, `5009-5010` iteration 재배분) | 그룹 사슬이 일직선이라는 가정. 분기 그룹(1~4 뒤에 다시 1~4)을 표현할 수 없음 | 같음 | MEDIUM |
| `Mock_ECC.py` (`:78-103`) | 정상, `max_iteration` 124 | 줄 밀림. `max_iteration`은 실제 row 76에서 124 (우연히 일치) | LOW |
| `collect_llr_matrices.py` (`:23-30`, `:33-39`), `rename_llr_idx.py` (`:20-39`) | 파일명과 바이트 해시만 본다. 영향 없음 | 영향 없음 | 없음 |
| `Read_Ref_C_Result`, `Gather` (`DAO_Main.py:8187-8261`, `1809-1836`) | 파일 형태와 무관. `ITER_MAX_HBF`를 4로 바꾸면 결과 파일의 `avg_iteration`과 iteration별 FER 배열의 뜻이 바뀜 (5절 발견 7) | 같음 | MEDIUM |
| `Parse_CSW_Min_Values` (`DAO_Main.py:10243-10249`) | `-1`을 건너뜀. BF 미진입 프레임의 열 1~4는 `decoder.cpp:7742` 초기화값 -1이라 영향 없음. 열 수는 `decoder.cpp:7931` `MN[MN_num-1] + ITER_MAX_HBF + 1`로 지금(124+0+1)과 후(120+4+1) 모두 125 | 같음 | 없음 |
| `Ref_C_result_%d.txt` (`local_opt.cpp:133-183`, `:178` `floor_flag` 출력) | DAO는 파싱하지 않고 `HEADER_TO_REMOVE`(`DAO_Constants.py:129`)로 지운다 | 같음 | 없음 |
| `decoder.cpp:7868` `m_log_LLR_idx` | `__LOG_DECODING_STATUS__`에서만 기록되고 DAO가 읽는 파일이 아님 | 같음 | 없음 |
| `DAO_spec.md:37`, `:51`, `:67`, `:94`, 헤더 필드표 `:27-41`, `README.md:304`, `:319` | 20, 21과 0, 1을 설명하지 못함 (`floor_flag` "현재 항상 -1") | 신규 줄 항목이 없음 | MEDIUM (문서) |

---

## 4. 파일 생성 주체와 후속 작업 기록 여부 판정

### 4.1 생성 주체

- ㉮ DAO는 형태 (1)을 만들 수 없다. `type_each_group`에 값을 넣는 곳은 `DAO_Main.py:2715`, `3073`, `3579`(1 삽입), `5113-5134`(원래 값 복사 또는 0, restart는 1)뿐이라 20, 21이 생기지 않는다. row 마지막 칸은 `3620` 등 7곳이 모두 기존 매트릭스의 값을 복사하므로, `Is_LLR_Valid` RW2를 통과한 매트릭스(전부 -1)에서 출발하면 0, 1이 나올 수 없다
- ㉯ DAO는 형태 (2)도 만들 수 없다. `Build_LLR_Matrix_Output_Lines`(`DAO_LLR_MATRIX.py:122-145`)에 신규 줄을 쓰는 코드가 없다
- ㉰ `msg1.md`는 분기 표기의 뜻(`:26-36`)만 말하고 누가 어떤 도구로 파일을 만들었는지 적지 않는다. 상위 문서 2장(`:45`)도 "푼 결과"만 있고 생성 주체 서술이 없다. 따라서 생성 주체는 이 저장소 밖이며 문서에 기록되어 있지 않다
- ㉱ `5_DAO/Input/Ref_C/Prime_ECC_3.0/`에는 `EXE/`(비어 있음)와 `Initial_LLR_matrix/LLR_MATRIX_1.txt`만 있다. DAO는 실행 파일을 `Input/Ref_C/Prime_ECC_3.0/EXE/Prime_ECC_3.0.exe`(`DAO_Main.py:454-463`)에서 찾고, 없으면 Linux에서만 `Input/Ref_C/Prime_ECC_3.0/SRC/`와 `Util/Makefile`로 빌드한다(`:864-883`). 둘 다 없으므로 지금 이 폴더로는 DAO를 돌릴 수 없다. 또한 DAO의 초기 매트릭스 경로는 `Initial_LLR_matrix/HD/LLR_MATRIX_{INITIAL_MATRIX_IDX}.txt`(`DAO_Main.py:459`, `DAO_Constants.py:5`, `DAO_Config.py:121` 기본 999)라서 `Initial_LLR_matrix/LLR_MATRIX_1.txt`는 그 경로에도 맞지 않는다
- ㉲ "0_LDPC_original을 고쳐 빌드한 실행 파일을 `EXE/`에 둔다"는 관계는 상위 문서, `code_diff.md`, `5_DAO/_pm/TODO.md`(`:17`은 "0_LDPC_original 반영 (외부에서 수행)"까지만), `5_DAO/README.md`(검색 결과 `EXE/`, `0_LDPC_original` 언급 없음) 어디에도 없다

### 4.2 후속 작업 기록 여부

- ㉮ 상위 문서 1장(`:9`)은 "DAO 쪽 대응(매트릭스 모델, 유효성 규칙, GenLLRMode)은 이 문서에서 다루지 않는다"로 범위를 뺐다
- ㉯ 상위 문서 7장 미결정 사항(`:353-361`)은 ㉮ 표기 선택, ㉯ SW 문턱 입력, ㉰ 분기 구간 고정, ㉱ 비AUTO 경로 통일뿐이고 DAO 항목이 없다. `code_diff.md`에는 DAO, Python, Mock 언급이 0건이다
- ㉰ `5_DAO/_pm/TODO.md:18`에 "DAO 매트릭스 모델과 유효성 규칙 확장" 한 줄이 있다
- ㉱ 판정: 후속 작업의 존재는 TODO에 기록되어 있으나, 4장 ㉮를 채택하면 DAO의 읽기(파서 줄 추가), 검증(RW2, G2, H3의 값 검사), `max_iteration` 7곳, 쓰기(신규 줄 출력), GenLLRMode의 헤더 동기화, `Mock_ECC.py`, `DAO_spec.md`와 `README.md` 필드표, 실행 파일과 초기 매트릭스 배치 경로가 함께 바뀌어야 한다는 사실이 어디에도 없다. TODO 한 줄은 이 목록을 담지 않아 실행 가능한 항목이 아니다. 특히 4장 ㉮는 DAO가 읽고 쓰는 파일 형식 자체를 바꾸는 결정이므로, 상위 7장 ㉮(표기 선택)에 "DAO 파서와 쓰기 함수가 같이 바뀐다"는 파급이 붙어야 선택의 비용이 보인다. 누락으로 기록한다

---

## 5. 발견 목록

| 번호 | 심각도 | 구분 | 문제 | 근거 위치 | 처방 | 처방 성격 |
|------|--------|------|------|----------|------|----------|
| 1 | HIGH | 파급 범위 | 형태 (1)을 DAO에 넣으면 `Is_LLR_Valid` RW2가 그룹 0 row 0의 `floor_flag` 0에서 거부하고 `Initialize_LLR_Matrix`가 `MPI_Abort`로 멈춘다. 거부 자체는 의도된 검사이고 메시지가 원인을 가리키므로 CRITICAL로 올리지 않았다. 통과했더라도 G2가 그룹 2와 4의 분기 구조를 거부한다 | `DAO_LLR_MATRIX.py:344-346`, `:305-312`, `DAO_Main.py:2341-2343`. 문서: 상위 1장 `:9`, 7장 | 상위 7장 또는 TODO 상세에 "RW2를 `sw_branch_idx` 도메인 규칙(-1 또는 0 이상)으로, G2를 분기 구간을 허용하는 규칙으로 바꿔야 한다"를 기록한다 | DAO 동작 변경 필요 (검증 규칙 교체). 문서 처방은 추가 기록 |
| 2 | HIGH | 파급 범위 | 형태 (2)는 DAO 파서가 신규 줄을 `num_restart`로 읽어 헤더가 한 줄 밀리고 row 하나가 소실된다. 예외 없이 지나가고 H4 `"max_value length mismatch"`로 오진하며, 거부 전에 밀린 구조를 파일로 저장한다 | `DAO_LLR_MATRIX.py:485`, `:491-492`, `:510-514`, `:285-287`, `DAO_Main.py:2338-2343`. 문서: 상위 4장 ㉮ `:106-119` | 4장 ㉮ 채택 조건에 "DAO 파서(`:483` 뒤)에 줄 읽기를 추가하고, 구 형태 파일과의 구분 방법(헤더 줄 수 또는 `restart_num` 줄의 토큰 수)을 정한다"를 적는다. 구분 방법은 설계 선택이므로 Decision 등급으로 표시한다 | DAO 동작 변경 필요 (파서 확장, 구 형태 판별). 문서 처방은 추가 기록 |
| 3 | MEDIUM | 파급 범위 | DAO 쓰기 함수에 신규 줄이 없어, 파서만 확장하면 저장 시 분기 index 줄이 소리 없이 사라져 형태 (2)가 유지되지 않는다. GenLLRMode가 그룹을 넣고 빼는 7곳도 `type_each_group`만 갱신하고 분기 줄을 갱신하는 자리가 없다 | `DAO_LLR_MATRIX.py:122-145`, `:195-201`, `DAO_Main.py:2715`, `3073`, `3579`, `5113-5134`. 문서: 상위 4장 ㉮ | 후속 작업 목록에 "헤더 모델(`LLR_Header`)에 필드 추가, 쓰기 함수 출력, GenLLRMode 헤더 조작 7곳 동기화"를 한 묶음으로 적는다 | DAO 동작 변경 필요 (필드 추가, 출력 추가). 문서 처방은 추가 기록 |
| 4 | MEDIUM | 파급 범위 | 상위 5.1-3은 C++의 `MN_num = iter_end[num_row-1]`을 전체 row 최대값으로 바꾸라고 하는데, DAO에 같은 가정이 7곳 있다(`max_iteration = groups[-1][-1].iter_end`). `LLR_MATRIX_1.txt`는 마지막 그룹이 105~124라 우연히 맞는다. 그룹 분할과 iteration 재배분도 그룹 사슬이 일직선이라는 가정 위에 있다 | `DAO_LLR_MATRIX.py:441`, `:207-218`, `DAO_Main.py:2743`, `3099`, `3320`, `3454`, `5645`, `5939`, `3367-3383`, `5009-5010`. 문서: 상위 5.1-3 `:152-159` | 5.1-3 아래 또는 TODO 상세에 "DAO의 `max_iteration` 7곳과 그룹 분할 논리도 같은 수정이 필요하다"를 적는다 | DAO 동작 변경 필요 (최대값 계산 교체). 문서 처방은 추가 기록 |
| 5 | MEDIUM | 서술 오류 (누락) | `DAO_spec.md`와 `README.md`의 필드표가 형태 (1)의 20, 21과 0, 1을 설명하지 못하고(`floor_flag` "현재 항상 -1"), 형태 (2)의 신규 줄 항목이 없다. 상위 5.1-2는 C++ 쪽 `floor_flag`를 `sw_branch_idx`로 개명하는데 DAO 쪽 같은 이름의 필드와 규칙(RW2)에 대한 언급이 없다 | `DAO_spec.md:37`, `:51`, `:67`, `:94`, `:27-41`, `README.md:304`, `:319`. 문서: 상위 5.1-2 `:151`, 4장 `:134-137` | 후속 작업 목록에 "`DAO_spec.md` 2.2, 2.3, 3.1, 3.4와 `README.md` 필드 목록 갱신"을 적는다 | 문서 갱신만. 코드 변경 없음 |
| 6 | MEDIUM | 파급 범위 (문서 누락) | 후속 작업이 `TODO.md:18` 한 줄뿐이고, 상위 7장과 `code_diff.md`에는 DAO 언급이 없다. 4장 ㉮는 DAO가 읽고 쓰는 파일 형식을 바꾸는 결정인데 그 비용(발견 1~5, 7, 8)이 결정 항목(7장 ㉮)에 붙어 있지 않다. 실행 파일 배치(`EXE/` 비어 있음, `SRC/` 없음)와 초기 매트릭스 경로(`Initial_LLR_matrix/HD/LLR_MATRIX_999.txt` 기대)가 DAO 실행 조건과 맞지 않는데 이 관계도 기록이 없다 | `5_DAO/_pm/TODO.md:17-18`, 상위 1장 `:9`, 7장 `:353-361`, `DAO_Main.py:454-463`, `:459`, `:864-883`, `DAO_Config.py:121`, 디렉토리 `5_DAO/Input/Ref_C/Prime_ECC_3.0/` | 상위 7장 ㉮에 "채택 시 DAO 파서, 쓰기, 검증, spec 갱신이 따라온다"를 붙이고, TODO `:18`을 발견 1~5의 목록으로 펼친다. `:17`에 "빌드 산출물을 `Input/Ref_C/Prime_ECC_3.0/EXE/`에 두고 초기 매트릭스를 `Initial_LLR_matrix/HD/`에 둔다"를 적는다 | 문서 추가 기록만. 코드 변경 없음 |
| 7 | MEDIUM | 파급 범위 | 상위 5.5가 `ITER_MAX_HBF`를 4로 바꾸면서 `decoder.cpp:1976`과 `local_opt.cpp:126-130`을 "딸려 오는 곳"으로만 적고, DAO가 읽는 결과 파일의 뜻이 바뀌는 것을 적지 않았다. ㉮ `avg_iteration`: BF 진입 프레임은 iteration 1부터 세고, 미진입 프레임은 `iter_num -= ITER_MAX_HBF`(`matrix_sel`이 `LAYOUT_PRIME_512B_TLC_VSS_OFF`이고 HD 또는 1_5SD일 때)로 4를 뺀 값이 섞여 평균이 된다. DAO는 이 값을 FER 동률의 우열 판정에 쓴다. ㉯ iteration별 FER 배열: `fr_4KB[n]`은 `o_iter_num > MN[n]`으로 세고 `MN[i] = i - 4`, `MN[0] = 4`가 되므로 index i의 뜻이 4 밀리고 i = 1~3은 항상 1.0이 된다. DAO는 이를 "FER per it."로 로그에 찍는다. `msg1.md:24-25`가 "DAO는 BF가 없다고 가정"이라고 적었을 뿐 문서 어디에도 결과 해석 변화가 없다 | `decoder.cpp:1973-1978`, `:1998`, `ecc_top.cpp:877-881`, `:887-900`, `:2271-2276`, `local_opt.cpp:124-131`, `DAO_Main.py:2540-2546`, `6076-6115`, `7595-7598`, `8244-8248`. 문서: 상위 5.5 `:250-262`, `msg1.md:19-25` | 상위 5.5에 "결과 파일의 `avg_iteration`과 iteration별 FER 배열은 BF 진입 여부에 따라 척도가 달라지며 DAO의 우열 판정과 로그가 이를 그대로 받는다"를 적고, DAO 쪽에서 척도를 맞출지(예: 미진입 프레임에도 4를 빼지 않기)는 Decision으로 남긴다. 관점 7(팀 I)과 겹치는 C++ 부분은 그쪽 판정을 따른다 | 기록 시점에는 문서 추가만. 척도 통일을 택하면 C++ `decoder.cpp:1973-1978` 동작 변경 |
| 8 | LOW | 파급 범위 | `Mock_ECC.py`가 DAO 파서와 같은 줄 index 방식이라 형태 (2)에서 같은 밀림이 생긴다. `max_iteration`은 이 파일에서 우연히 124로 같지만 마지막 그룹이 1 row인 파일이면 앞 그룹 값이 나온다. `README_Mock_ECC.md:110`도 갱신 대상이다 | `Mock_ECC.py:82-103`, `README_Mock_ECC.md:110` | 후속 작업 목록에 `Mock_ECC.py` 헤더 건너뛰기 갱신을 포함한다 | 도구 동작 변경 필요 (index 1 추가). 문서 처방은 추가 기록 |
| 9 | LOW | 파급 범위 (문제 없음 확인) | `collect_llr_matrices.py`, `rename_llr_idx.py`는 파일명과 바이트 해시만 다루고, `Parse_CSW_Min_Values`는 -1을 건너뛰며 열 수도 변하지 않고, `Ref_C_result_%d.txt`와 `m_log_LLR_idx`는 DAO가 읽지 않는다. 기록 불필요 | `collect_llr_matrices.py:23-39`, `rename_llr_idx.py:20-39`, `DAO_Main.py:10243-10249`, `decoder.cpp:7742`, `:7931`, `DAO_Constants.py:129` | 없음 | 없음 |
