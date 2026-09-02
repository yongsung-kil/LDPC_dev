# 워커 D_3 보고: 관점 9 (제거, 개명 멤버의 참조 전수와 새 배열 초기화), 관점 13 (프레임 상태 초기화와 restart, edge clear 상호작용)

## 1. 확인 범위

읽은 문서

- ㉮ `review/r2_round2_lv2_analysis/context.md` 전체
- ㉯ 상위 문서 `20260902_SW_branch_LLR_matrix.md` 5.4, 5.5, 5.6, 7장
- ㉰ `code_diff.md` 1.1, 2.1, 2.2, 2.3, 3.2~3.7, 4.1, 5.1, 6.1, 6.2, 8.1~8.3, 9장

읽은 소스 (`0_LDPC_original/src/`)

| 파일 | 줄 | 확인한 내용 |
|------|----|------------|
| decoder.cpp | 1-30 | 생성자, `Initialize_Dec` (포인터만 NULL로 채움) |
| decoder.cpp | 425-440 | `Init_Dec` 5인자 판 (`m_param_LLR` 포인터 대입 436행) |
| decoder.cpp | 452-602 | `Init_Dec_Option` (루프 변수 `i` 454행, SW 문턱 459-493행, power stopping 강제 OFF 505-510행, `MN_max` 564행) |
| decoder.cpp | 604-616 | `Clear_Flag` |
| decoder.cpp | 709-739 | `Clear_Edge_Restart` |
| decoder.cpp | 956-1156 | `LDPC_Decoder` 프레임 시작부터 Preprocessing 자리까지 (`Clear_Flag` 1091행, mn 루프 1120행, row 선택 1136-1142행) |
| decoder.cpp | 1805-1839 | clk 루프 탈출과 클럭 집계 |
| decoder.cpp | 1943-1979 | mn 루프 끝 (CRC 판정, Jump_Iter, `Select_BF` 호출) |
| decoder.cpp | 2082-2130 | `Select_BF` 수정 전 |
| decoder.cpp | 2299-2335 | `C2V_Cal_New_Sgn` |
| decoder.cpp | 2572-2614, 2783, 2993-3008 | `Is_Iter_Type_Init` 사용처 |
| decoder.cpp | 3440-3444 | `syn_weight`, `psyn_weight` 계산 시점 |
| decoder.cpp | 3476-3509 | `CNU_Remove_Old_Sgn` |
| decoder.cpp | 4954-4971, 5297-5362 | `Jump_Iter`, `Check_End_Iter` |
| decoder.cpp | 5691-5762 | `V2C_Cal` (Init이면 `VN_Cal_Pre`) |
| decoder.cpp | 6538-6632 | `Is_Iter_Type_Edge_Clear`, `Is_Iter_Type_Init` 양 갈래 |
| decoder.cpp | 6973-7073 | `Get_Cur_LLR_Idx_FILE` 수정 전 |
| decoder.cpp | 8055-8115 | `Adjust_HD_Floor_Type` |
| decoder.h | 24-26, 125-159, 210, 296-306, 331 | 선언부 |
| local_opt.cpp | 전체 (1-184) | 소멸자, `Run_Local_Opt`, MPI 전파, `Read_LLR_info_Auto` |
| local_opt.h | 29-30 | `g_pECC`, `m_param_LLR` 값 멤버 |
| ecc_top.cpp | 6, 197-247 | 생성자 존재, `Init_ECC_Top` 세 판 |
| ecc_top.h | 28-29, 94, 97 | 생성자 선언, `m_param_LLR` 포인터, `Decoder m_dec` 값 멤버 |
| main.cpp | 34, 102-130 | `g_pECC` 생성 |
| ecc_data.h | 175-202 | `PARAM_LLR` |
| common.h | 196-255, 398-409, 717-732, 756-757 | SW 문턱 상수, `ITER_MAX_HBF`, enum |
| corner.h | 66-90 | `IDX_FLAG_*` enum (`IDX_FLAG_HD_5_8_SET_TYPE_0`은 9번째, `IDX_FLAG_LEN`은 16) |
| corner.cpp | 43, 119-126, 174-176 | `m_flag` 할당, `Event_Flag` (범위 검사 없음), Print_Head 문자열 |
| mode.h | 전체 | 스위치 상태 (`__RUN_PREPROCESSING__` 63행 OFF, `__HD_FLOOR_SET__` 73행 OFF, `__CORNER_CHECKER__` 75행 OFF, `__RUN_PARITY_SKIP__` 79행 OFF, `__RUN_MPI__` 23-25행은 `__AUTO_LLR_OPT__` 정의 직후 `#if !defined(__AUTO_LLR_OPT__)`라 죽은 갈래) |

Grep으로 전수 확인한 식별자: `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_BF`, `syn_th_BF0`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1`, `FLAG_HD_1_4_SET_TYPE_*`, `FLAG_HD_5_8_SET_TYPE_*`, `IDX_FLAG_HD_5_8_SET_TYPE_*`, `floor_flag`, `Get_Cur_LLR_Idx_FILE`, `Select_BF()`, `Clear_Flag()`, `Init_Dec_Option(`, `new ECC_Top`, `ECC_Top::ECC_Top`, `MN_num`.

---

## 2. 관점 9: 제거, 개명 멤버의 참조 전수와 새 배열 초기화

### 2.1 ㉮ 참조 전수 표

"수록"은 code_diff.md의 수정 전후 코드나 본문이 그 줄을 다루는지를 뜻한다. "성격"은 그 줄을 그대로 두면 컴파일이 깨지는지(코드), 주석이라 무해한지를 뜻한다.

| 멤버 | 파일:줄 | 내용 | 수록 | 성격 |
|------|--------|------|------|------|
| `flag_HD_1_4_Set` | decoder.h:297 | 선언 | 2.2 (삭제) | 코드 |
| | decoder.cpp:612 | `Clear_Flag`에서 `FLAG_LOW` 대입 | **미수록** | 코드, 컴파일 깨짐 |
| | decoder.cpp:2090 | `Select_BF` 대입 | 5.1 (함수 통째 교체) | 코드 |
| | decoder.cpp:7002, 7006 | 비AUTO 갈래 비교 | 6.1 (갈래 삭제) | 코드 |
| `flag_HD_5_8_Set` | decoder.h:298 | 선언 | 2.2 (삭제) | 코드 |
| | decoder.cpp:613 | `Clear_Flag`에서 `FLAG_LOW` 대입 | **미수록** | 코드, 컴파일 깨짐 |
| | decoder.cpp:2091, 2100, 2106, 2117, 2123 | `Select_BF` 대입 | 5.1 | 코드 |
| | decoder.cpp:7010, 7016 | 비AUTO 갈래 비교 | 6.1 | 코드 |
| `syn_th_BF` | decoder.h:301 | 선언 | 2.2 (삭제) | 코드 |
| | decoder.cpp:460-465 | 주석 처리된 case 여섯 줄 | 미수록 | 주석, 무해 |
| | decoder.cpp:472 | default 갈래 대입 | 4.1 | 코드 |
| `syn_th_BF1` | decoder.h:303 | 선언 | 2.2 (삭제) | 코드 |
| | decoder.cpp:468 | 512B_TLC_OFF 갈래 대입 | 4.1 | 코드 |
| `syn_th_BF2` | decoder.h:304, decoder.cpp:469 | 주석 | 미수록 (2.2 수정 후 코드에 없으므로 함께 사라짐) | 주석, 무해 |
| `syn_th_5_8_Set_0` | decoder.h:305 | 선언 | 2.2 (삭제) | 코드 |
| | decoder.cpp:477-479, 481-482 | 주석 처리된 case | 미수록 | 주석, 무해 |
| | decoder.cpp:480, 483 | 대입 | 4.1 | 코드 |
| | decoder.cpp:583 | 주석 처리된 printf | 미수록 | 주석, 무해 |
| | decoder.cpp:2099, 2116 | `Select_BF` 비교 | 5.1 | 코드 |
| `syn_th_5_8_Set_1` | decoder.h:306 | 선언 | 2.2 (삭제) | 코드 |
| | decoder.cpp:486-488, 490-491 | 주석 처리된 case | 미수록 | 주석, 무해 |
| | decoder.cpp:489, 492 | 대입 | 4.1 | 코드 |
| | decoder.cpp:583 | 주석 처리된 printf | 미수록 | 주석, 무해 |
| `FLAG_HD_1_4_SET_TYPE_0/1` | common.h:718-719 | enum | 5.1 본문 (삭제 명시) | 코드 |
| | decoder.cpp:2090, 7002, 7006 | 사용 | 5.1, 6.1 | 코드 |
| `FLAG_HD_5_8_SET_TYPE_0/1` | common.h:723-724 | enum | 5.1 본문 (삭제 명시) | 코드 |
| | decoder.cpp:2091, 2100, 2106, 2117, 2123, 7010, 7016 | 사용 | 5.1, 6.1 | 코드 |
| `floor_flag` | ecc_data.h:197 | 선언 | 2.1 (`sw_branch_idx`로 개명) | 코드 |
| | local_opt.cpp:105, 114 | 할당, 읽기 | 3.3 | 코드 |
| | local_opt.cpp:178 | 로그 출력 | 3.3 본문 ("178행의 로그 출력도 같은 이름으로") | 코드 |
| `IDX_FLAG_HD_5_8_SET_TYPE_0/1/2` | corner.h:79-81 | enum (유지) | 5.1 ㉰ (재사용) | 코드 |
| | corner.cpp:174-176 | Print_Head 문자열 (유지) | 미수록 | 코드, 컴파일 무관 |
| | decoder.cpp:2093, 2102, 2108, 2119, 2125 | `Event_Flag` 호출 | 5.1 | 코드 |

전수 결과

- ㉠ 컴파일에 걸리는 곳 가운데 code_diff.md가 다루지 않는 곳은 `decoder.cpp:612-613` 두 줄뿐이다 (발견 2)
- ㉡ 나머지 미수록은 모두 주석이라 무해하다
- ㉢ `flag_HD_*`, `syn_th_*`, `FLAG_HD_*_SET_TYPE_*`, `floor_flag`를 다른 파일(ecc_top, main, mpi, TV_Dec_Inter, corner)에서 쓰는 곳은 없다

### 2.2 ㉯ `PARAM_LLR` 구조체 복사와 MPI 경로

- ㉮ 실체는 `LOCAL_OPT::m_param_LLR` 값 멤버 하나다 (local_opt.h:30). `Init_ECC_Top(..., &m_param_LLR, ...)` (local_opt.cpp:46)가 주소를 넘기고, ecc_top.cpp:222가 `ECC_Top::m_param_LLR` 포인터(ecc_top.h:94)에 담고, `Init_Dec` 5인자 판(ecc_top.cpp:228, decoder.cpp:436)이 `Decoder::m_param_LLR` 포인터(decoder.h:210)에 담는다
- ㉯ 구조체 값 복사, `memcpy`, `sizeof(PARAM_LLR)`는 소스 어디에도 없다. 필드 위치가 바뀌어도(2.1이 구조체 중간에 세 필드를 넣음) 깨지는 곳이 없다
- ㉰ MPI는 local_opt.cpp:37-51에서 `LLR_MATRIX` row들과 `CSW_thr`만 `MPI_Bcast`한다. 3.7이 새 배열 네 개를 추가 전파하는 안을 적었고, "각 rank가 파일을 따로 읽는 구조라면 필요 없다"라고 유보했다. `Read_LLR_info_Auto`는 rank를 가리지 않고 모든 rank가 부르므로(local_opt.cpp:34, `m_myrank` 조건 없음) 헤더 배열은 각자 읽은 값이 채워진다 (rank별 파일 읽기 구조는 팀 P 관점 11 영역)
- ㉱ mode.h:23-25의 `__RUN_MPI__`는 `__AUTO_LLR_OPT__`를 정의한 바로 뒤에서 `#if !defined(__AUTO_LLR_OPT__)`로 감싸여 있어 AUTO 빌드에서 켜지지 않는다. 따라서 3.7의 추가 코드는 현재 빌드 조합에서 컴파일되지 않는다

판정: 문제 없음. 구조체를 통째로 복사하거나 크기에 의존하는 경로가 없다.

### 2.3 ㉰ 새 배열 초기화 위치와 `Init_Dec_Option`, `Read_LLR_info_Auto` 호출 순서

호출 순서 (AUTO 경로)

| 순서 | 위치 | 하는 일 |
|------|------|--------|
| 1 | local_opt.cpp:34 `Read_LLR_info_Auto` | 파일을 읽어 `m_param_LLR`과 `m_param_dec->MN[]`를 채운다 |
| 2 | local_opt.cpp:35 `Run_Simu_Curr_LLR` → 45 `new ECC_Top()` | `Decoder` 객체 생성. ecc_top.cpp:6에 사용자 정의 생성자가 있으므로 `new ECC_Top()`은 멤버를 0으로 채우지 않는다. `Decoder::Initialize_Dec`(decoder.cpp:19-30)는 포인터만 NULL로 채운다 |
| 3 | local_opt.cpp:46 `Init_ECC_Top` → ecc_top.cpp:228 `Init_Dec` | decoder.cpp:436에서 `m_param_LLR` 포인터 확보 |
| 4 | ecc_top.cpp:229 `Init_Dec_Option` | 4.1의 `num_sw_branch[]`, `syn_th_sw_branch[][]` 초기화. `ECC_Top` 하나에 한 번, 프레임마다 부르지 않는다 |
| 5 | decoder.cpp:1091 `Clear_Flag` | 프레임마다 |
| 6 | decoder.cpp:1969 `Select_BF` | 프레임마다 mn 0 끝에서 `cur_sw_branch_idx[]`를 0으로 채우고 다시 고른다 (5.1 554-556행) |

확인 결과

- ㉮ 4.1의 이중 루프는 `MAX_SW_SPAN` × (`MAX_SW_BRANCH` - 1) 전 원소를 채우므로 `num_sw_branch[]`, `syn_th_sw_branch[][]`에 미초기화 원소가 없다
- ㉯ `cur_sw_branch_idx[]`는 생성자(decoder.cpp:19-30), `Clear_Flag`(606-616), 4.1 어디에서도 채우지 않는다. 채우는 곳은 5.1 `Select_BF`뿐이다. 5.1까지 적용된 뒤에는 읽기(1138행, mn > 0)가 항상 쓰기(1969행, mn 0) 뒤에 오므로 정상이다. 5.1을 넣기 전 단계(9장 3단계)에서는 미정의 값이다 (발견 1)
- ㉰ 4.1 끝 문장 "num_sw_branch[]를 파일에서 읽은 값과 대조하는 검사를 넣으면"의 자리는 `Init_Dec_Option` 안이 맞다. 4단계 시점에 `m_param_LLR`이 이미 채워져 있고(1단계, 3단계), `Init_Dec_Option`은 한 번만 불리므로 비용도 없다. 다만 문서는 검사 코드를 싣지 않고 제안만 했다 (발견 3)

### 2.4 ㉱ 4.1 루프 변수 `i` 선언과 `syn_th_sw_branch` 초기값 0의 의미

- ㉮ `int i;`가 decoder.cpp:454에 함수 지역으로 선언되어 있어 4.1의 `for (i = 0; ...)`는 그대로 컴파일된다. 안쪽 `int j`는 루프 안 선언이다
- ㉯ 초기값 0의 의미: `Select_SW_Branch`(5.1 540-548행)는 `i < num_sw_branch[span] - 1` 동안 `weight < syn_th_sw_branch[span][i]`를 본다. `num_sw_branch`가 1이면 루프를 돌지 않고 0을 돌려주므로 문턱 0은 읽히지 않는다. `num_sw_branch`가 2 이상인데 문턱이 0으로 남아 있으면 `weight < 0`이 거짓이라 항상 마지막 분기가 고정된다. 이 상태는 오류 없이 조용히 지나간다 (4.1이 실제로 채우는 문턱은 span 0, 1의 첫 칸뿐이므로, 4.1을 확장해 `num_sw_branch`만 올리고 문턱을 빠뜨리면 이 경우가 된다. 발견 3 ㉢)

### 2.5 ㉲ `MAX_SW_SPAN`이 4인데 span 0, 1만 채우는 문제

- ㉮ 4.1은 span 0, 1만 채운다. span 2, 3은 `num_sw_branch` 1, 문턱 0, `cur_sw_branch_idx` 0(5.1)이다
- ㉯ 파일이 세 번째 구간(span 2)에 분기 0, 1을 두면 3.2 파서는 `num_sw_span` 3으로 읽어 들이고, 6.1은 `cur_sw_branch_idx[2]`(항상 0)와 비교한다. 분기 1 그룹은 어떤 프레임에서도 후보가 되지 않는다. 그 iteration을 분기 0 그룹이 덮으면 오류 출력 없이 분기 0으로만 돈다
- ㉰ 파일이 다섯 번째 구간(span 4)을 두면 6.1의 `cur_sw_branch_idx[span]`이 배열 밖(`cur_sw_branch_idx[4]`)을 읽는다. 클래스 안에서 `num_sw_branch[0]`이 바로 뒤에 놓이지만 정의된 동작이 아니다. 3.2 파서와 4.1 어디에도 `num_sw_span <= MAX_SW_SPAN` 검사가 없다
- ㉱ 두 문서 모두 이 제약을 적지 않았다. 상위 문서 7장 ㉰(1~8로 못박을지 임의 구간을 허용할지)이 미결정으로 남아 있으나, 코드는 "구간 수는 파서가 세는 대로, 문턱은 두 구간만"이라는 어긋난 상태다

판정: MEDIUM 엣지케이스 (발견 3)

### 2.6 ㉳ `syn_th_BF` 삭제와 4.1 default 갈래의 일관성

- ㉮ 2.2가 `syn_th_BF`를 지우고, 4.1 default 갈래가 `syn_th_BF0 = SW_TH_BF_DEFAULT`로 바꾸고, 5.1이 `syn_th_BF0`만 읽는다. 세 곳이 맞는다
- ㉯ 수정 전 소스(decoder.cpp:466-472)는 512B_TLC_OFF가 아닌 layout에서 `syn_th_BF`에만 대입하고 `syn_th_BF0`는 채우지 않는다. 비AUTO 빌드의 2088행은 그 미정의 `syn_th_BF0`로 BF 진입을 판정해 왔다. 4.1을 넣으면 그 layout들의 BF 진입 판정이 미정의 값 비교에서 630 문턱 비교로 바뀐다. 개선이지만 동작 변경이고 문서가 이를 말하지 않는다 (발견 6)

판정: 일관성은 문제 없음. 동작 변경 미기재는 LOW.

---

## 3. 관점 13: 프레임 상태 초기화와 restart, edge clear 상호작용

### 3.1 ㉴ `cur_sw_branch_idx` 세팅과 읽기 순서, mn 0 조기 종료 경로

프레임 한 번의 흐름 (decoder.cpp)

| 순서 | 줄 | 내용 |
|------|----|------|
| 1 | 1091 | `Clear_Flag` |
| 2 | 1120 | `for (mn = 0; mn < MN + 1; mn++)` |
| 3 | 1133 | `Clear_Edge_Restart` (안에서 `Is_Iter_Type_Edge_Clear(mn)`) |
| 4 | 1136-1145 | mn 0이면 `cur_set_idx = 0`, mn > 0이면 `Get_Cur_LLR_Idx_FILE(mn)` (읽기) |
| 5 | 1396~1805 | clk 루프. 3440-3444행에서 iteration 0 마지막 column에 `syn_weight`, `psyn_weight` 확정 |
| 6 | 1947-1949 | mn 0은 `CRC_flag = HIGH`만 하고 `Check_End_Iter`를 부르지 않는다 (`break` 1957행은 mn > 0 전용) |
| 7 | 1961-1965 | `Jump_Iter`의 `break`(1963행)는 `power_index == ON`일 때만. `Init_Dec_Option` 505-510행이 두 갈래 모두 OFF로 굳힌다 |
| 8 | 1968-1970 | mn 0이면 `Select_BF` (쓰기) |

- ㉮ mn 루프 본문에 `continue`는 없고, `break`는 1805행(clk 루프 안), 1957행(mn > 0), 1963행(power ON)뿐이다. mn 0에서 8번 전에 빠져나가는 경로가 없다
- ㉯ 읽기(4번)는 mn > 0에서만, 쓰기(8번)는 mn 0 끝에서 한 번이므로 프레임 안에서 읽기가 쓰기보다 앞서는 일이 없다. `syn_weight`도 5번에서 확정된 뒤 8번에서 읽힌다
- ㉰ `Get_Cur_LLR_Idx_FILE` 호출처는 1138행 하나, `Select_BF` 호출처는 1969행 하나다 (Grep)

판정: 문제 없음. 5.1 적용 후 세팅과 읽기의 순서는 프레임 안에서 고정이다.

### 3.2 ㉵ `Select_BF` 미호출 프레임과 `Clear_Flag`

- ㉮ 3.1에 따라 `Select_BF`를 거치지 않고 mn 1로 가는 프레임은 없다. `MN`이 0이어도 mn 0은 돌고 `Select_BF`가 불린다
- ㉯ mn 루프가 끝난 뒤 `cur_sw_branch_idx`를 읽는 곳은 없다. 1973-1979행과 2025행은 `flag_BF_on`만 본다
- ㉰ 다음 프레임은 1091행 `Clear_Flag` 뒤 mn 0 끝 5.1의 554-556행이 배열을 0으로 채우고 다시 고른다. 따라서 `Clear_Flag`에 배열 초기화를 넣지 않아도 프레임 사이 값이 새지 않는다
- ㉱ 다만 `Clear_Flag`의 612-613행이 지워지는 멤버를 대입하고 있어 그대로 두면 컴파일이 깨진다 (발견 2). 이 두 줄을 `cur_sw_branch_idx[]` 0 채우기로 바꾸면 발견 1(적용 순서 3단계의 미초기화)도 함께 닫힌다

판정: 최종 상태에서는 문제 없음. 중간 단계와 컴파일 누락은 발견 1, 2.

### 3.3 ㉶ edge clear 횟수 손 계산과 비AUTO 대조

`Is_Iter_Type_Edge_Clear` 호출처

| 위치 | 인자 | 모드 |
|------|------|------|
| decoder.cpp:709-739 `Clear_Edge_Restart` | `mn` | 전 모드, iteration마다 한 번 |
| decoder.cpp:2314, 2321 `C2V_Cal_New_Sgn` | `iter` | HD, 1.5SD |
| decoder.cpp:2328 `C2V_Cal_New_Sgn` | `iter - 1` | 2SD, 3SD 전용 |
| decoder.cpp:3491, 3498, 3504 `CNU_Remove_Old_Sgn` | `iter` | 전 모드 |

`iter - 1`은 SD 갈래(2327-2332행)에만 있다. HD와 1.5SD는 세 호출처 모두 `iter`를 그대로 넘기므로 아래 표의 mn 값이 곧 edge clear가 걸리는 iteration이다.

손 계산 (`ITER_MAX_HBF` = 4, 파일의 `restart_iter`가 있으면 그 지점이 더해진다)

| 경우 | 프레임 안 mn 수열 | `bClear == TRUE`인 mn | 횟수 | 근거 |
|------|------------------|----------------------|------|------|
| 수정 후 AUTO, HD, BF 진입 | 0, 1, 2, 3, 4, 5, 6, ..., MN | 0, 1, 5 | 3 | 8.1 923-925행 (6543-6545행과 동일). BF 진입은 mn을 밀지 않으므로 5도 지난다 |
| 수정 후 AUTO, HD 미진입 | 0, 5, 6, 7, ..., MN + 4 | 0, 5 | 2 | 5.1 566-567행이 mn 0을 4로 밀고 루프 증가로 5. 1은 지나지 않는다 |
| 수정 후 AUTO, 1.5SD | 0, 5, 6, 7, ... | 0, 5 | 2 | 5.1 574-575행 |
| 수정 후 AUTO, 2SD, 3SD | 0, 1, 2, ... | 0 | 1 | 8.1 936-938행 (6556-6558행과 동일) |
| 현재 AUTO (`ITER_MAX_HBF` 0, `Select_BF` 한 줄) | 0, 1, 2, ... | 0, 1 | 2 | `iter == 1`과 `iter == ITER_MAX_HBF + 1`이 겹침 |
| 비AUTO, 512B_TLC_OFF, HD, BF 진입 | 0, 1, ..., MN | 0, 1, 5 | 3 | 6569-6571행 |
| 비AUTO, 512B_TLC_OFF, HD 미진입 또는 1.5SD | 0, 5, 6, ... | 0, 5 | 2 | 6569-6571행, 2097-2098행, 2114-2115행 |

대조 결과

- ㉮ 512B_TLC_OFF의 HD, 1.5SD에서 수정 후 AUTO와 비AUTO의 edge clear 집합은 {0, 1, 5}(BF 진입) 또는 {0, 5}(미진입)로 같다. AUTO 갈래는 여기에 파일의 `restart_iter`를 더한다 (6549-6552행). 비AUTO는 HD에서 restart를 보지 않는다
- ㉯ 8.1 마지막 문장 "BF에 진입하면 1에서, 진입하지 않으면 5에서 걸린다"는 표와 다르다. BF 진입 프레임은 1과 5 양쪽에서 걸리고, 두 경우 모두 0에서도 걸린다. 코드는 그대로 옮긴 것이라 결과에는 영향이 없고 서술만 불완전하다 (발견 4)
- ㉰ 비AUTO 갈래(6567행)는 `matrix_sel`이 512B_TLC_OFF일 때만 판정하고 다른 layout은 iteration 0을 포함해 한 번도 clear하지 않는다. AUTO 갈래는 layout을 가리지 않는다. 이 차이는 수정 전부터 있던 것으로 팀 I 관점 8 영역이라 기록만 한다

### 3.4 ㉷ 8.2 `Is_Iter_Type_Init`과 restart

- ㉮ HD, 1.5SD 조건은 AUTO 갈래(6610-6614행)와 비AUTO 갈래(6628-6632행)가 `iter == 0`으로 같다. 8.2가 AUTO 갈래만 남겨도 비AUTO와 다르지 않다
- ㉯ `Is_Iter_Type_Init`이 하는 일은 Pre-update다. TRUE이면 2572-2614행에서 C2V 계산을 건너뛰고, 2783행에서 `Check_SRAM_sgn`을 0으로 두고, 2993-3008행에서 Syndrome을 복사하고, 5691-5762행에서 `VN_Cal_HD` 대신 `VN_Cal_Pre`를 부른다. restart 시점의 min 레지스터, CN 레지스터, edge SRAM sgn, PMU, `Sum_t_OLD` 비우기는 `Clear_Edge_Restart`(709-739행)가 `Is_Iter_Type_Edge_Clear`로 판정해 따로 수행하고, 그 판정에는 `restart_iter`가 들어 있다(6549-6552행)
- ㉰ 따라서 HD에서 restart iteration은 "edge는 비우되 Pre-update는 하지 않는" 동작이 되며, 6603-6604행 주석 "HD는 Edge clear를 수행할때 초기화 과정이 필요없기에 mn==0에서만 초기화 작업 (Pre-update) 수행"과 맞는다. 8.2의 "의도로 보인다"는 근거가 충분하다

판정: 문제 없음.

### 3.5 ㉸ 8.3 Preprocessing, 클럭 집계, `Intentional_Blank` 실행 횟수

- ㉮ `__RUN_PREPROCESSING__`은 mode.h:63에서 꺼져 있다. 1146-1156행(Preprocessing 호출), 1814-1825행(클럭 집계), 2303-2313행과 3480-3490행(`Intentional_Blank`)은 모두 이 스위치 안이라 현재 빌드에서 컴파일되지 않는다. 8.3의 "그대로 둔다"는 이 상태에서 결과에 영향이 없다
- ㉯ 스위치를 켠 경우의 횟수: BF 진입 프레임은 mn 수열이 0, 1, 2, ...이고 `flag_BF_on == TRUE && mn == 1`이 mn 1에서 한 번 참이다. 미진입 프레임은 mn 수열이 0, 5, 6, ...이고 `flag_BF_on == FALSE && mn == 5`가 mn 5에서 한 번 참이다. 어느 프레임도 Preprocessing을 두 번 부르지 않는다. 클럭 집계(1814-1825행)는 같은 조건이라 같은 횟수다
- ㉰ `Intentional_Blank`(2304-2313행, 3481-3490행)의 조건도 같은 두 지점이고, BF 진입 프레임의 mn 5는 `FALSE == flag_BF_on` 조건에 걸리지 않아 2314행의 `Is_Iter_Type_Edge_Clear(5)`로 떨어져 `edge_sgn = 0`이 된다. Preprocessing 지점과 edge clear 지점이 어긋나지 않는다
- ㉱ 상위 문서 5.6 표와 code_diff.md 8.3 모두 이 스위치가 꺼져 있다는 사실을 적지 않았다. "지금은 앞의 조건으로 굳어 있다"(상위 5.6), "mn == 1로 굳어 있다"(8.3)는 스위치가 켜졌을 때의 서술이다 (발견 5)

판정: 코드 영향 없음. 서술 보완은 LOW.

### 3.6 ㉹ `Adjust_HD_Floor_Type` 간섭

- ㉮ 6.1 수정 후 코드(685-687행)가 HD, iter > 0에서 `Adjust_HD_Floor_Type`을 그룹 탐색 전에 부른다. `__HD_FLOOR_SET__`이 mode.h:73에서 꺼져 있어 몸통은 8109-8113행만 남고 `state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0`만 한다
- ㉯ 스위치가 켜져도 이 함수는 `mn`, `prev_CSW`, `cnt_hd_error_floor`, `state_hd_error_floor_set`만 다루고 `cur_sw_branch_idx`, `num_sw_branch`, `syn_th_sw_branch`, `flag_BF_on`을 건드리지 않는다
- ㉰ `state_hd_error_floor_set`을 `Get_Cur_LLR_Idx_FILE`이 읽는 곳은 수정 전(7049, 7070행)과 수정 후(6.2 767-768, 794행) 모두 오류 printf 인자뿐이다. 그룹 선택 조건에는 쓰이지 않는다

판정: 간섭 없음.

---

## 4. 발견 목록

### 발견 1. HIGH, 결함 (적용 순서 3단계), 9장 3단계 전제 "cur_sw_branch_idx[]가 모두 0"이 거짓이다

- ㉮ 문제: 9장 3단계는 "Select_BF가 그대로라 cur_sw_branch_idx[]가 모두 0이므로 분기 0만 쓰인다. 기존 동작과 결과가 같아야 한다"라고 전제한다. 그러나 `cur_sw_branch_idx[]`를 0으로 채우는 코드는 5.1 `Select_BF`(4단계)뿐이다. 3단계 시점에는 ㉠ 2.2가 선언만 추가하고, ㉡ `Decoder`는 `ECC_Top`의 값 멤버(ecc_top.h:97)이며 `ECC_Top`에 사용자 정의 생성자(ecc_top.cpp:6)가 있어 `new ECC_Top()`(local_opt.cpp:45)이 멤버를 0으로 채우지 않고, ㉢ `Initialize_Dec`(decoder.cpp:19-30)는 포인터만 NULL로 채우며, ㉣ `Clear_Flag`(606-616)와 4.1(4단계)도 이 배열을 건드리지 않는다. 6.1의 `group_branch != cur_sw_branch_idx[span]`(693행)이 미정의 값과 비교한다
- ㉯ 결과: 값이 우연히 0이 아니면 iteration 1~8의 분기 그룹이 모두 후보에서 빠져 `selected_group == -1`이 되고, 6.2가 `[Error] @Cur_LLR_IDX (1)`을 찍고 row 0을 돌려준다. 프로세스는 계속 돌지만 결과가 틀리고, 문서의 "3단계에서 기존과 결과가 달라지면 파일 읽기나 그룹 선택에 문제가 있는 것이다"라는 진단 기준이 사용자를 파서 쪽으로 오도한다
- ㉰ 위치: `code_diff.md 9장` 3단계, `code_diff.md 6.1` 693행, `code_diff.md 2.2`
- ㉱ 처방: 2.2를 넣는 1단계에서 `Clear_Flag`의 612-613행을 `for (i...) cur_sw_branch_idx[i] = 0;`으로 바꿔 넣는다 (발견 2와 같은 자리). 5.1이 들어온 뒤에도 mn 0에서 다시 0으로 채우므로 중복은 무해하다. 대안은 9장 순서를 "4장, 5장 뒤에 6장"으로 바꾸는 것이다. 코드 삭제 없음, 최종 동작 변경 없음 (중간 단계의 미정의 값만 제거)
- ㉲ 덧붙임: 3단계의 비교 기준 "기존 동작"은 분기 없는 파일로만 성립한다. `LLR_MATRIX_1.txt`로는 기존 코드가 항상 row 0을 고른다고 상위 문서 3장이 말하므로, 분기 0 그룹을 고르는 3단계와 어차피 다르다. 이 서술의 성립 여부는 팀 C 관점 15 영역이라 여기서는 지적만 한다

### 발견 2. MEDIUM, 서술 누락 (컴파일 깨짐), `Clear_Flag`의 `flag_HD_1_4_Set`, `flag_HD_5_8_Set` 대입이 code_diff.md에 없다

- ㉮ 문제: decoder.cpp:612-613이 2.2에서 지우는 두 멤버에 `FLAG_LOW`를 대입한다. code_diff.md의 어느 장도 이 두 줄을 다루지 않는다. 9장 1단계 "빌드가 깨지는 곳이 이름 변경 지점이다"는 컴파일러가 찾아 주기를 기대한 서술이나, 문서가 수정 전후를 전수로 싣는 형식이므로 누락이다
- ㉯ 위치: `code_diff.md 2.2` (수정 대상 목록), `code_diff.md 9장` 1단계. 소스 decoder.cpp:612-613
- ㉰ 처방: 두 줄을 지우거나(코드 삭제) `cur_sw_branch_idx[]` 0 채우기로 바꾼다(발견 1의 처방과 동일). 동작 변경 없음

### 발견 3. MEDIUM, 엣지케이스 (수정 후 코드), 구간 수와 분기 수가 파일과 `Init_Dec_Option` 사이에서 대조되지 않는다

- ㉮ 문제 ㉠: 파일의 구간 수(`num_sw_span`, 3.2가 계산)가 `MAX_SW_SPAN`(4)을 넘으면 6.1의 `cur_sw_branch_idx[span]`(693행)이 배열 밖을 읽는다. 3.2와 4.1 어디에도 상한 검사가 없다
- ㉯ 문제 ㉡: 4.1은 span 0, 1만 채우므로 span 2, 3에 분기 1 이상을 둔 그룹은 어느 프레임에서도 후보가 되지 않는다. 같은 iteration을 분기 0 그룹이 덮으면 오류 출력 없이 조용히 분기 0으로 돈다
- ㉰ 문제 ㉢: 파일의 어느 그룹 분기 index가 그 구간의 `num_sw_branch[span] - 1`을 넘어도 같은 방식으로 조용히 빠진다. `num_sw_branch`가 2 이상인데 문턱이 0으로 남은 칸은 `weight < 0`이 거짓이라 마지막 분기로 고정된다. 4.1 끝 문장은 "대조하는 검사를 넣으면 막을 수 있다"라고 제안만 하고 코드를 싣지 않았다
- ㉱ 위치: `code_diff.md 4.1` 끝 문장, `code_diff.md 3.2`, `code_diff.md 6.1` 692-693행, `상위 문서 7장 ㉰`
- ㉲ 처방: `Init_Dec_Option`의 4.1 코드 끝에 (`m_param_LLR`은 decoder.cpp:436에서 이미 확보됨) ㉠ `m_param_LLR->num_sw_span <= MAX_SW_SPAN`, ㉡ 각 그룹의 `sw_branch_idx_each_group[g] < num_sw_branch[sw_span_idx_each_group[g]]`, ㉢ `num_sw_branch[span] - 1`개의 문턱이 0보다 큰 오름차순인지를 검사해 어긋나면 오류를 찍고 멈춘다. 또는 상위 문서 7장 ㉰를 "1~8로 못박는다"로 결정하고 `MAX_SW_SPAN`을 2로 줄여 파서가 그 이상을 오류로 잡게 한다. `LLR_MATRIX_1.txt`(구간 2개, 분기 2개씩)에서는 동작 변경 없음

### 발견 4. LOW, 서술 오류, 8.1 마지막 문장의 edge clear 지점이 불완전하다

- ㉮ 문제: "BF에 진입하면 1에서, 진입하지 않으면 5에서 걸린다"는 3.3 표와 다르다. BF 진입 프레임은 0, 1, 5 세 곳, 미진입 프레임은 0, 5 두 곳에서 걸린다. 코드는 기존 AUTO 갈래를 그대로 두는 것이라 결과에 영향은 없다
- ㉯ 위치: `code_diff.md 8.1` 950-951행, `상위 문서 5.6` 표 첫 행("4로 되돌리면 1과 5 두 지점이 된다")
- ㉰ 처방: 문장을 "BF 진입 프레임은 0, 1, 5에서, 미진입 프레임은 0, 5에서 걸린다 (미진입은 mn이 0에서 5로 건너뛴다)"로 고친다. 코드 변경 없음

### 발견 5. LOW, 서술 누락, `__RUN_PREPROCESSING__`이 꺼져 있다는 사실이 없다

- ㉮ 문제: 상위 문서 5.6 표의 Preprocessing 행과 code_diff.md 8.3은 mode.h:63에서 스위치가 꺼져 있어 1146-1156행이 컴파일되지 않는다는 사실을 적지 않았다. "지금은 앞의 조건으로 굳어 있다", "mn == 1로 굳어 있다"는 켜졌을 때의 서술이다. 사용자가 8.3을 읽고 Preprocessing이 실제로 도는 것으로 오해할 수 있다
- ㉯ 위치: `상위 문서 5.6` 표 셋째 행, `code_diff.md 8.3` 988행
- ㉰ 처방: 두 곳에 "이 블록은 `__RUN_PREPROCESSING__`(mode.h:63) 안이며 현재 꺼져 있다. 켜면 BF 진입 프레임 mn 1, 미진입 프레임 mn 5에서 각각 한 번 돈다"를 적는다. 코드 변경 없음

### 발견 6. LOW, 서술 누락 (동작 변경 미기재), 4.1 default 갈래가 `syn_th_BF0`를 새로 초기화한다

- ㉮ 문제: 수정 전 decoder.cpp:472는 `syn_th_BF`에만 대입해 512B_TLC_OFF가 아닌 layout에서 `syn_th_BF0`가 미정의로 남고, 비AUTO 빌드의 2088행이 그 값으로 BF 진입을 판정해 왔다. 4.1은 이를 `SW_TH_BF_DEFAULT`(630)로 채운다. 개선이지만 그 layout들의 비AUTO 동작이 바뀌는 것이며, 2.2는 "syn_th_BF는 대입만 되고 읽히는 곳이 없으므로 지운다"라고만 적었다
- ㉯ 위치: `code_diff.md 2.2` 172행, `code_diff.md 4.1` 444행
- ㉰ 처방: 4.1 아래에 "수정 전 default 갈래는 `syn_th_BF0`를 채우지 않아 512B_TLC_OFF 밖의 layout에서 BF 진입 판정이 미정의 값에 의존했다. 수정 후 630으로 판정한다"를 적고 변경 등급을 Review로 표시한다. 코드 변경 없음, 동작 변경은 4.1 자체에 이미 포함

### 발견 7. LOW, 엣지케이스 (수정 후 코드, 현재 빌드에서는 컴파일 제외), 5.1의 `Event_Flag` index가 분기 수에 따라 배열 밖으로 나간다

- ㉮ 문제: 5.1 582행 `Event_Flag(IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1])`에서 `IDX_FLAG_HD_5_8_SET_TYPE_0`은 9, `IDX_FLAG_LEN`은 16(corner.h:69-87)이고 `Event_Flag`(corner.cpp:119-126)는 범위 검사 없이 `m_flag[index]`(할당 크기 `IDX_FLAG_LEN`, corner.cpp:43)에 쓴다. `cur_sw_branch_idx[1]`이 3~6이면 `IDX_FLAG_HD_FLOOR_TYPE_*` 자리를 덮어쓰고, 7~8이면 배열 밖에 쓴다. `MAX_SW_BRANCH`가 9라 index 8까지 허용된다. 5.1 ㉰가 "넷 이상이면 자리를 늘려야 한다"라고 인지했으나 코드에 가드가 없다. `__CORNER_CHECKER__`는 mode.h:75에서 꺼져 있고, 4.1이 주는 `num_sw_branch[1]`은 2라 현재 값으로는 걸리지 않는다
- ㉯ 위치: `code_diff.md 5.1` 581-583행, ㉰ 항목
- ㉰ 처방: `if (cur_sw_branch_idx[1] < 3)`으로 감싸거나 `IDX_FLAG_HD_5_8_SET_TYPE_*` 자리를 `MAX_SW_BRANCH`개로 늘린다. 현재 빌드 동작 변경 없음

---

## 5. 결론

- ㉮ 관점 9: 참조 전수는 `decoder.cpp:612-613`(컴파일 깨짐, 미수록) 한 곳이 빠졌고, 새 배열 초기화는 최종 상태에서는 닫히나 9장 3단계 시점에 `cur_sw_branch_idx[]`가 미정의라 그 단계의 검증 기준이 성립하지 않으며(HIGH), 구간 수와 분기 수의 상한, 파일과의 대조가 코드에 없다(MEDIUM)
- ㉯ 관점 13: `Select_BF`는 모든 프레임의 mn 0 끝에서 반드시 불리고 읽기는 mn > 0에서만 일어나므로 순서 문제가 없고, edge clear는 512B_TLC_OFF의 HD, 1.5SD에서 비AUTO와 같은 집합({0, 1, 5} 또는 {0, 5})이며 `Is_Iter_Type_Init`, Preprocessing, `Adjust_HD_Floor_Type`은 간섭하지 않는다. 남는 것은 8.1 문장의 불완전함과 `__RUN_PREPROCESSING__` OFF 미기재(LOW)뿐이다
