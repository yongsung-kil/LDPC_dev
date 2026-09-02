# Worker C_1: 소스 인용 정확성 (팀 C, 관점 14)

> 작성: 2026-09-03
> 대상: 상위 문서 `20260902_SW_branch_LLR_matrix.md`, `code_diff.md`
> 대조 소스: `0_LDPC_original/src/` (decoder.cpp, local_opt.cpp, common.h, decoder.h, ecc_data.h, corner.h, main.cpp)

## 확인 범위

- ㉮ code_diff.md의 "수정 전" 블록 22개를 소스 줄과 글자 단위로 대조했다 (A절)
- ㉯ `...` 생략 부분 4곳의 실제 내용을 소스에서 전부 확인하고 수정 후 코드와 비교했다 (B절)
- ㉰ 상위 문서가 인용한 줄 번호 50여 곳을 소스로 판정했다 (C절)
- ㉱ 두 문서가 같은 곳을 다른 줄로 적은 8건을 판정했다 (D절)
- ㉲ `GROUP_TYPE_CSW` 선택 서술을 `decoder.cpp:7059-7068`과 `prev_CSW` 갱신 지점으로 검증했다 (E절)
- ㉳ 상위 2장, 3장의 파일 해석 표는 `LLR_MATRIX_1.txt`를 직접 파싱해 대조했다 (77 row, 12 group, 표의 CSW 나열과 iteration 범위가 모두 일치)

발견은 "수정 후 코드를 그대로 적용하면 생기는 결함"(코드 결함)과 "문서 서술 자체의 오류"(문서 오류)로 구분해 적는다.

---

## A. code_diff "수정 전" 블록 대조

| 블록 | 문서가 적은 줄 | 실제 줄 | 일치 | 차이 내용 |
|------|--------------|---------|------|----------|
| 1.1 `GROUP_TYPE_*` | common.h 757 부근 | 756-757 | 일치 | 없음 |
| 1.2 `ITER_MAX_HBF` | common.h 403-407 | 403-407 | 거의 일치 | 407은 `#endif // __AUTO_LLR_OPT__`인데 인용은 `#endif`만 적음 (꼬리 주석 생략) |
| 2.1 `PARAM_LLR` | ecc_data.h 179-198 | 179-198 | 일치 | 필드 18개의 순서와 이름 전부 같음 |
| 2.2 문턱 변수 | decoder.h 296-306 | 296-306 | 일치 | 주석 문구와 들쭉날쭉한 들여쓰기까지 같음 |
| 2.3 `Select_BF` 선언 | decoder.h (부근) | 156 | 일치 | `    void    Select_BF();` |
| 3.1 배열 할당 | local_opt.cpp 74 | 74 | 일치 | 한 줄에 두 문장 (`num_set_each_group` 할당, 공백 5개, `type_each_group` 할당) 맞음 |
| 3.2 type 줄 읽기 | local_opt.cpp 81-84 | 81-84 | 일치 | 없음 |
| 3.3 `floor_flag` | local_opt.cpp 105, 114 | 105, 114 | 일치 | 178의 로그 출력 `fprintf(fp_auto_result, "%2d ", LLR_info->floor_flag[i]);`도 확인. `floor_flag` 참조는 src 전체에서 ecc_data.h:197, local_opt.cpp:105, 114, 178 네 곳뿐 |
| 3.5 최대 iteration | local_opt.cpp 116-123 | 116-123 | 일치 | 124-131은 아래 A-1 참고 |
| 3.6 소멸자 | local_opt.cpp 10-26 | 10-26 | 일치 | 14-15 인용 맞음. `delete[] m_param_LLR.floor_flag`는 소멸자에 없음 (문서 서술 "해제되지 않고 있다" 맞음) |
| 3.7 MPI | local_opt.cpp 38-44 | 38-44 | 일치 | 없음. 36은 `Run_Local_Opt`의 닫는 괄호, 37은 `Run_Simu_Curr_LLR` 함수 머리 |
| 4.1 switch 세 개 | decoder.cpp 459-493 | 459-493 | 코드 줄은 일치, 주석 줄 생략 | 주석 처리된 case 줄 14개(460-465, 469, 477-479, 481-482, 486-488, 490-491)를 표시 없이 뺌. 코드 줄(459, 466-468, 470-476, 480, 483-485, 489, 492-493)은 글자 단위 일치. 루프 변수 `i`는 `Init_Dec_Option` 머리(454)에 `int i;`로 선언되어 있어 수정 후 `for (i = 0; ...)` 사용 가능 |
| 5.1 `Select_BF` | decoder.cpp 2082-2130 | 2082-2130 | 일치 (`...` 제외) | 함수 시작 2082 (`void Decoder::Select_BF()`), 끝 2130 (`}`). `#if` 2084, `#endif` 2129. 인용된 줄은 모두 소스와 같고 `else{`(2105, 공백 없음)까지 같음. `...` 내용은 B절 |
| 6.1 AUTO 앞부분 | decoder.cpp 6973-6999 | 6973-6999 | 코드 줄은 일치, 주석 줄 생략 | 6981의 주석 `//Adjust_HD_Floor_Type(m_param_LLR->CSW_thr[...], ...);` 한 줄을 표시 없이 뺌. 나머지 글자 단위 일치 |
| 6.1 `#else` 갈래 | (제목에 없음) | 7000-7047 | 일치 (`...` 제외) | 7001-7020, 7021-7022, 7036-7046 글자 단위 일치. `...`는 7023-7035이며 B절에서 확인. 제목 "6973-6999행"이 인용 범위(7047까지)를 덮지 못함 |
| 6.2 오류 검사 | decoder.cpp 7048-7071 | 7048-7073 | 일치 | 인용에 `return table_row_idx;`(7072)와 `}`(7073)가 있으므로 실제 범위는 7048-7073. 함수 끝은 7073 |
| 7.1 C2V 1bit | decoder.cpp 2373-2379 | 2373-2379 | 일치 | 없음 |
| 7.2 V2C 저장 1bit | decoder.cpp 2796-2802 | 2796-2802 | 일치 | 없음 |
| 7.3 VN 1bit 두 곳 | decoder.cpp 4055-4059, 4274-4278 | 4055-4059, 4274-4278 | 일치 | 두 곳이 글자 단위로 같음 (문서 서술 맞음) |
| 8.1 Edge clear | decoder.cpp 6538-6598 | 6538-6598 | 일치 (`...` 제외) | 함수 시작 6538, 끝 6598. `#if` 6541, `#else` 6566, `#endif` 6596. 인용된 6538-6554 글자 단위 일치 |
| 8.2 Init | decoder.cpp 6606-6626 | 6606-6676 (함수) | 일치 (`...` 제외) | 함수는 6606-6676. `#if` 6609, `#else` 6626, `#endif` 6674. 인용된 6609-6614 일치. 주석은 6604에 있고 원문은 "HD는 Edge clear를 수행할때 초기화 과정이 필요없기에 mn==0에서만 초기화 작업 (Pre-update) 수행" (문서 인용은 "(Pre-update)"를 뺌) |
| 8.3 Preprocessing | decoder.cpp 1146-1156 | 1146-1156 | 일치 | 인용된 1148-1150 글자 단위 일치. `#if defined (__RUN_PREPROCESSING__)` 1146, `#endif` 1156 |

### A-1. 3.5가 언급하지 않은 local_opt.cpp:124-131

```
124    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_SSD == m_param_dec->init_n)) {
125        for (i = 0; i < m_param_dec->MN_num; i++) {
126            m_param_dec->MN[i] -= ITER_MAX_HBF;
127        }
128        if (m_param_dec->MN_num > 1) {
129            m_param_dec->MN[0] = ITER_MAX_HBF;
130        }
131    }
```

- ㉮ HD 또는 `MODE_DEC_1_SSD`일 때 `MN[]` 전체에서 `ITER_MAX_HBF`를 빼고 `MN[0]`을 `ITER_MAX_HBF`로 둔다. 지금 AUTO 빌드는 `ITER_MAX_HBF`가 0이라 이 블록이 아무 효과가 없고, 1.2를 적용하면 살아난다. 상위 5.5 표는 이 블록(126-130)을 딸린 곳으로 적었으나 code_diff 3.5는 바로 위 116-123만 다루고 이 블록을 언급하지 않는다 (팀 I 관점 7과 겹침)
- ㉯ 124의 `MODE_DEC_1_SSD`는 src 전체에서 이 줄 한 곳에만 나오고 정의가 없다. 정의된 이름은 `common.h:78`의 `MODE_DEC_1_5SD`다. 원본 손상이나 오타로 보이며 두 문서 모두 언급이 없다 (사전 존재, 이 작업의 수정 범위 밖)

---

## B. `...` 생략 부분과 수정 후 반영 여부

### B-1. 5.1 `Select_BF` (decoder.cpp:2082-2130)

`...` 네 곳의 실제 내용은 모두 `#if defined(__CORNER_CHECKER__)` 로 감싼 Corner 이벤트 한 줄씩이다.

| 위치 | 실제 내용 |
|------|----------|
| 2101-2103 (HD, BF 미진입, `syn_weight < syn_th_5_8_Set_0`) | `m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0);` |
| 2107-2109 (HD, BF 미진입, 그 외) | `m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_1);` |
| 2118-2120 (1.5SD, `psyn_weight < syn_th_5_8_Set_0`) | `m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0);` |
| 2124-2126 (1.5SD, 그 외) | `m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_1);` |

확인 결과:

- ㉮ `IDX_FLAG_HD_1_4_SET_TYPE_*` 계열 이벤트는 소스에 없다 (corner.h:79-81에 `IDX_FLAG_HD_5_8_SET_TYPE_0/1/2`만 있음). 수정 전 코드가 발화하는 이벤트는 `IDX_FLAG_HD_5_8_SET_TYPE_0`(2093, 2102, 2119)과 `IDX_FLAG_HD_5_8_SET_TYPE_1`(2108, 2125) 둘뿐이다
- ㉯ 수정 후의 `IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]` 한 줄은 HD와 1.5SD 갈래의 이벤트 다섯 곳을 값으로는 덮는다. BF 진입 갈래(2093)는 원본이 TYPE_0을 고정 발화하는데, 수정 후는 `Select_SW_Branch(1, syn_weight)`의 결과를 더한다. 현재 상수로는 `syn_weight < syn_th_BF0`(680 또는 630)이면 반드시 `SW_TH_5_8_SET0_*`(1100 또는 960)보다 작으므로 0이 되어 같은 이벤트가 나간다. 상수가 바뀌면 달라질 수 있는 구조적 차이다 (팀 D 관점 5)
- ㉰ 수정 전 코드에는 HD도 1.5SD도 아닌 모드를 위한 `else` 갈래가 없다. 그 모드에서는 Corner 이벤트가 발화하지 않고 `flag_BF_on`도 대입하지 않는다. 수정 후는 `else { flag_BF_on = FLAG_LOW; }` 뒤에 `#if defined(__CORNER_CHECKER__)` 블록이 모든 갈래 공통으로 놓여 있어, 2SD, 3SD 등 다른 모드에서도 `cur_sw_branch_idx[1]`(초기값 0)로 `IDX_FLAG_HD_5_8_SET_TYPE_0`이 발화한다. 원본에 없던 이벤트다 (발견 3)
- ㉱ `flag_BF_on = FLAG_LOW` 대입은 원본에서 `#if defined (__AUTO_LLR_OPT__)` 갈래(2085)에만 있다. `#else` 갈래는 `flag_BF_on`을 `FLAG_HIGH`로만 올리고 내리는 곳이 없으며, 프레임 시작의 `Clear_Flag()`(decoder.cpp:606-616, 호출 1091)가 `flag_BF_on = FLAG_LOW`(609)로 초기화한다. 따라서 수정 후의 세 `FLAG_LOW` 대입은 중복이지만 해가 없다
- ㉲ `Clear_Flag`는 612-613에서 `flag_HD_1_4_Set = FLAG_LOW; flag_HD_5_8_Set = FLAG_LOW;`를 대입한다. code_diff 2.2가 이 두 멤버를 지우는데, code_diff 어디에도 `Clear_Flag` 수정이 없다. 그대로 적용하면 컴파일이 깨진다 (발견 1). src 전체에서 두 멤버의 참조는 decoder.h:297-298, decoder.cpp:612-613, 2090-2091, 2100, 2106, 2117, 2123, 7002, 7006, 7010, 7016이며 code_diff는 612-613만 빠뜨렸다
- ㉳ `cur_sw_branch_idx[]`는 수정 후 `Select_BF` 안에서만 0으로 초기화된다. `Decoder` 생성자(decoder.cpp:5-8)는 `Initialize_Dec()`로 포인터만 NULL로 두고, `Clear_Flag`(606-616)도 이 배열을 건드리지 않는다. code_diff 9장 3단계("`Select_BF`가 그대로라 `cur_sw_branch_idx[]`가 모두 0")는 근거가 없다. 그 단계에서는 미초기화 값이다 (발견 5, 팀 C 관점 15와 팀 D 관점 9에 걸침)

### B-2. 6.1 `... (위와 같은 iteration 범위 탐색) ...` (decoder.cpp:7023-7035)

AUTO 루프(6986-6998)와 글자 단위로 같다 (들여쓰기만 한 단계 깊음). 문서 서술 맞음.

### B-3. 8.1 `Is_Iter_Type_Edge_Clear` 생략 두 곳

- ㉮ `... (restart만 보는 갈래) ...` = 6555-6565. 실제 내용은 `iter == 0`이면 TRUE, 아니면 `restart_iter[]`와 대조. "restart만"이 아니라 `iter == 0`도 본다. 수정 후 코드의 `else` 갈래(문서 935-945행)는 이 내용과 글자 단위로 같다 (소스는 탭과 공백 4칸이 섞여 있고 문서는 탭만 씀. 내용 동일)
- ㉯ `... (matrix_sel별 하드코딩) ...` = 6566-6596. `LAYOUT_PRIME_512B_TLC_VSS_OFF`일 때만 HD/1.5SD(`iter == 0 || 1 || ITER_MAX_HBF + 1`), 2SD(`RSP1_2SD_PRIME_1/2`), 3SD(`RSP1_3SD_PRIME_1~6`)를 본다. 다른 matrix_sel은 항상 FALSE. 서술 맞음

### B-4. 8.2 `Is_Iter_Type_Init` 생략 두 곳

- ㉮ 첫 `...` = 6615-6625. `else` 갈래로, 8.1의 `else`와 같은 형태 (`iter == 0`이면 TRUE, 아니면 `restart_iter[]` 대조, 변수만 `bInit`)
- ㉯ 둘째 `...` = 6626-6674. `#else` 갈래로 8.1처럼 matrix_sel 하드코딩이며 `__4_BIT_LLR__` 여부로 RSP1 상수 개수가 달라진다
- ㉰ 수정 후 코드가 없고 "같은 방식으로 갈래만 남긴다"라고만 적혀 있다. 8.1과 같은 기계적 작업(`#if` 줄 삭제, `#else`부터 `#endif`까지 삭제)이라 적용은 가능하나, 남기는 `else` 갈래(6615-6625)가 문서 어디에도 없어 적용자가 소스를 열어야만 결과를 확인할 수 있다 (발견 8)

---

## C. 상위 문서 인용 줄 번호 판정

| 상위 문서 위치 | 인용 | 판정 | 비고 |
|--------------|------|------|------|
| 3장 | common.h:756-757 | 맞음 | |
| 3장 | decoder.cpp:7051-7068 두 갈래 | 맞음 | 7051 `GROUP_TYPE_ITER`, 7059 `GROUP_TYPE_CSW` |
| 3장 | 6974 `table_row_idx = 0` | 맞음 | |
| 3장 | 7069 `< 0 || >= num_row` 검사 | 맞음 | |
| 4장 | local_opt.cpp:105, 114, 178 | 맞음 | |
| 5.1 | local_opt.cpp:52-132 | 부분 | 함수 `Read_LLR_info_Auto`는 52-184. 132는 `fclose` 줄이고 133-183은 로그 출력(문서가 인용한 178 포함). context.md도 52-132로 적음 |
| 5.1-3 | local_opt.cpp:116, 120 | 맞음 | |
| 5.2-3 | local_opt.cpp:36-44 부근 | 부분 | MPI 블록은 38-44 |
| 5.2-4 | local_opt.cpp:14-15 부근 | 맞음 | |
| 5.3 | decoder.cpp:6973-7073 | 맞음 | 함수 전체 |
| 5.3 | 6984-6999 AUTO 루프 | 맞음 | |
| 5.3-3 | 7048 오류 검사 | 맞음 | |
| 5.3-4 | 7001-7020, 표의 7001, 7005, 7009, 7015 | 맞음 | 각 줄이 `if`, `else if` 머리 |
| 5.4 | decoder.cpp:2084-2130 | 부분 | 함수는 2082-2130, AUTO 갈래는 2084-2129 |
| 5.4 | 1968-1970 `mn == 0` 호출 | 맞음 | 1968 `if (mn == 0) {`, 1969 `Select_BF();` |
| 5.4 | 2085 `flag_BF_on = FLAG_LOW` | 맞음 | |
| 5.4-2 | common.h:717-725 | 맞음 | 717-720, 722-725 두 enum |
| 5.4-3 | common.h:202-251 | 맞음 | `#define` 줄 범위. `#if defined(__12META__)` 200, `#endif` 252 (context.md의 200-252도 맞음) |
| 5.4-3 | decoder.cpp:459-493 | 맞음 | |
| 5.4-4 | decoder.h:301 부근 | 맞음 | 301-306 |
| 5.5 | common.h:403-407 | 맞음 | |
| 5.5 표 | 564 | 맞음 | `MN_max = m_param_dec->MN[m_param_dec->MN_num - 1] + ITER_MAX_HBF;` (표는 축약) |
| 5.5 표 | 1149 | 맞음 | |
| 5.5 표 | 1929 | 맞음 | `__LOG_VNU_IN_OUT__` 안 |
| 5.5 표 | 1976 | 맞음 | |
| 5.5 표 | 2097-2098, 2114-2115 | 맞음 | 2114-2115는 "HD가 아닌 모드"가 아니라 1.5SD 갈래 |
| 5.5 표 | 2310, 3487 | 맞음 | `Intentional_Blank()` 조건 |
| 5.5 표 | 6454 | 맞음 | `__RUN_ITER34_HIGH_DV_SKIP__` 안 |
| 5.5 표 | 6545, 6571 | 맞음 | |
| 5.5 표 | 7583 | 맞음 | `Padding_Zero_Log`의 `MN_size` |
| 5.5 표 | local_opt.cpp:126-130 | 맞음 | |
| 5.5 표 전체 | "딸려 오는 곳" | 누락 | 발견 2 참고 |
| 5.5 | 2374-2378, 2797-2801, 4055-4059, 4274-4278 | 맞음 | `#ifdef`부터 `#endif`까지 |
| 5.6 표 | 6541-6565 | 맞음 | AUTO 갈래 (`#if` 6541, `#else` 6566) |
| 5.6 표 | 6609-6626 | 한 줄 어긋남 | AUTO 갈래는 6609-6625. 6626은 `#else` |
| 5.6 표 | 1146-1156 | 맞음 | |
| 6.1 표 | 1137-1141 | 맞음 | |
| 6.1 표 | 2084-2129 | 맞음 | AUTO 갈래 기준 |
| 6.1 표 | 6984-7047 | 맞음 | |
| 6.2 표 | 3985-3990, 4160-4165, 4366-4371, 4505-4510, 4673-4678 | 맞음 | 다섯 곳 모두 열어 확인. `#if defined(__AUTO_LLR_OPT__)` / `Get_VNU_LLR_SET_FILE(...)` / `#else` / `Get_VNU_Ch_LLR_Adaptive(...)` / `Get_VNU_Th_Adaptive(...)` / `#endif` 여섯 줄이 글자 단위로 같음 |
| 6.3 표 | decoder.cpp 항목 | 누락 | `m_log_CSW_auto` 관련 7741-7743, 7773-7775, 7803-7805, 7928-7938 네 곳이 빠짐 (Grep `__AUTO_LLR_OPT__` 결과 대조). 팀 I 관점 12 |
| code_diff 5.1 ㉰ | corner.h:79-81 | 맞음 | `IDX_FLAG_HD_5_8_SET_TYPE_0/1/2` 연속 |
| code_diff 2.2 | "`syn_th_BF`, `syn_th_BF1`은 대입만 되고 읽히는 곳 없음" | 맞음 | `syn_th_BF` 대입 472(주석 460-465), `syn_th_BF1` 대입 468. 읽는 곳 없음. `syn_th_5_8_Set_1`도 대입(489, 492)과 주석 처리된 printf(583)뿐 |
| code_diff 8.2 | 주석 decoder.cpp:6604 | 맞음 | 문구에서 "(Pre-update)" 생략 |

---

## D. 줄 번호 차이 8건 판정

| 건 | 상위 문서 | code_diff | 소스 판정 |
|----|----------|-----------|----------|
| 1 | 5.4 `2084-2130` | 5.1 `2082-2130`, 6.1 표 `2084-2129` | 함수 2082-2130, AUTO 갈래 2084-2129. 5.1과 6.1 표는 각각 정확하고, 5.4는 `#if`에서 시작해 함수 끝에서 끝나는 섞인 범위. 같은 함수를 세 숫자로 적어 5.4를 2082-2130으로 맞추는 것이 좋다 |
| 2 | 5.2-3 `36-44` | 3.7 `38-44` | 38-44가 맞다. 36-37은 앞 함수의 닫는 괄호와 함수 머리. 상위는 "부근"이라 허용 범위 |
| 3 | 5.2-4 `14-15` | 3.6 `10-26` | 둘 다 맞다 (두 줄 대 소멸자 전체) |
| 4 | 5.5 `2374-2378` | 7.1 `2373-2379` | 둘 다 맞다 (`#ifdef`부터 `#endif` 대 조건식 전체) |
| 5 | 5.3 `6973-7073` | 6.1 `6973-6999`, 6.2 `7048-7071` | 5.3이 맞다 (함수 전체). 6.1 제목은 인용이 7047까지 이어지므로 덮지 못하고, 6.2는 인용이 7073까지 있으므로 7048-7073이 맞다 |
| 6 | 5.6 `6541-6565` | 8.1 `6538-6598` | 둘 다 맞다 (AUTO 갈래 대 함수 전체) |
| 7 | 5.6 `6609-6626` | 8.2 `6606-6626` | AUTO 갈래 6609-6625, 함수 6606-6676. 둘 다 끝 줄이 `#else`(6626)에 걸려 있다. 갈래면 6609-6625, 함수면 6606-6676으로 적는 것이 맞다 |
| 8 | 5.1-3 `local_opt.cpp:120` | 3.5 `116-123` | 둘 다 맞다 (한 줄 대 블록) |

---

## E. `GROUP_TYPE_CSW` 선택 서술과 소스 비교

decoder.cpp:7059-7068 실제 코드:

```
7059	else if (GROUP_TYPE_CSW == m_param_LLR->type_each_group[selected_group]) {
7060	    table_row_idx = start_idx;
7061	    num_candidate = m_param_LLR->num_set_each_group[selected_group];
7062	    for (i = num_candidate - 1; i > 0; i--) {
7063	        if (prev_CSW <= m_param_LLR->CSW_thr[start_idx + i]) {
7064	            table_row_idx = start_idx + i;
7065	            break;
7066	        }
7067	    }
7068	}
```

- ㉮ 비교식은 `prev_CSW <= CSW_thr[start_idx + i]`이다. code_diff 6.2 인용과 같다
- ㉯ `i`는 `num_candidate - 1`에서 1까지 내려가며 훑고, 처음 맞는 row에서 멈춘다. `i = 0`(그룹 첫 row)은 훑지 않고 7060에서 기본값으로 둔다. 첫 row의 `CSW_thr = -1`은 어떤 `prev_CSW`와도 `<=`로 맞지 않으므로 기본값 자리로만 쓰인다
- ㉰ 문턱이 내림차순(뒤로 갈수록 작음)이면, 뒤에서 앞으로 훑을 때 처음 `prev_CSW <= thr`이 되는 row는 "`prev_CSW` 이상인 문턱 중 가장 작은 것"이고, 결과는 `thr[k+1] < prev_CSW <= thr[k]`이면 row k, 모든 문턱보다 크면 row 0이 된다. 상위 3장 "CSW가 내림차순이므로 이 그룹들은 모두 `GROUP_TYPE_CSW`(1)이어야 한다"는 이 동작과 맞는다. `LLR_MATRIX_1.txt`를 파싱해 확인한 그룹 1, 2, 3, 5의 CSW 나열도 상위 3장 표와 같다 (그룹 1: -1, 400, 120, 40, 32, 24, 16 등)
- ㉱ `prev_CSW`는 `Set_CSW(int w)`(decoder.cpp:6680-6683)에서만 대입된다. 호출은 3465(`V2C_Store` 안, `jj == N_b - 1`이고 마지막 edge일 때 `Compute_CSW()` 결과)와 4981, 4992, 5120, 5288(`CSW_VALUE_JUMP`)이다. `Get_Cur_LLR_Idx_FILE(mn)`은 iteration 시작(1136-1138)에서 불리므로 그때의 `prev_CSW`는 직전 iteration의 마지막 column에서 계산된 값이다. 상위 3장 ㉯ "직전 iteration의 CSW(`prev_CSW`)"는 맞다
- ㉲ 상위 3장의 "`20`, `21`을 넣으면 ... 항상 첫 번째 row의 파라미터를 쓴다"도 맞다. `table_row_idx`가 0으로 남으면 파일 전체의 row 0(그룹 0의 유일한 row)이다

판정: 문제 없음.

---

## 발견 목록

### 발견 1 (HIGH, 코드 결함, 문서 누락): `Clear_Flag`의 지워지는 멤버 참조

- 위치: code_diff.md 2.2, 5.1, 9장 1단계. 근거 decoder.cpp:612-613
- 내용: 2.2가 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 지우는데 `Clear_Flag()`(decoder.cpp:606-616)의 612-613이 두 멤버에 `FLAG_LOW`를 대입한다. code_diff에 이 함수의 수정이 없어 9장 1단계에서 컴파일이 깨진다. 9장은 "빌드가 깨지는 곳이 이름 변경 지점"이라 예고하지만 이 지점을 목록에 넣지 않았다
- 처방: `Clear_Flag`의 612-613을 지우고 그 자리에 `cur_sw_branch_idx[]`를 0으로 두는 반복문을 넣는다 (코드 삭제 요구. 동작은 원본 유지). 발견 5와 처방이 같다
- 팀 D 관점 9와 겹침

### 발견 2 (MEDIUM, 문서 누락): `ITER_MAX_HBF` 딸린 곳 표가 전수가 아님

- 위치: 상위 문서 5.5 표, code_diff.md 1.2 ("이 상수를 쓰는 12곳")
- 내용: Grep으로 확인한 `ITER_MAX_HBF` 사용처는 common.h 정의 2줄을 빼고 decoder.cpp 37줄, local_opt.cpp 2줄, main.cpp 1줄, TV_Dec_Inter.cpp 5줄이다. 상위 5.5 표는 decoder.cpp 13줄과 local_opt.cpp 2줄만 적었고, code_diff 1.2의 "12곳"은 표의 행 수(11행)와도 줄 수(15줄)와도 맞지 않는다. 표에서 빠진 곳:
  - ㉮ decoder.cpp 1448, 1622, 1828 (`__RUN_PARITY_SKIP__`의 `mn == 1 || mn == ITER_MAX_HBF + 1`)
  - ㉯ decoder.cpp 1821 (Preprocessing clock 가산)
  - ㉰ decoder.cpp 2169, 2190 (`__DUAL_UPDATE__` 양 갈래의 PCRC termination 제어)
  - ㉱ decoder.cpp 7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018 (로그 함수들의 `MN_size`. 표는 7583 하나만 적음)
  - ㉲ main.cpp:719 `g_param_dec.MN[0] = ITER_MAX_HBF;`
  - ㉳ TV_Dec_Inter.cpp 1077, 1221, 1295, 1487, 1535
- 처방: 표를 보강하고 1.2의 개수를 고친다. 코드 삭제나 동작 변경 없음. 각 줄이 4로 바뀌었을 때 안전한지는 팀 I 관점 6의 몫이다

### 발견 3 (MEDIUM, 코드 결함, 문서 미고지): 수정 후 `Select_BF`의 Corner 이벤트가 모든 모드에서 발화

- 위치: code_diff.md 5.1 수정 후 (문서 578-583행). 근거 decoder.cpp:2087-2128 (원본은 HD, 1.5SD 갈래 안에서만 발화)
- 내용: 수정 후는 `else { flag_BF_on = FLAG_LOW; }` 뒤에 `#if defined(__CORNER_CHECKER__)` 블록을 갈래 밖에 두었다. HD도 1.5SD도 아닌 모드에서 `cur_sw_branch_idx[1]`이 0이므로 `IDX_FLAG_HD_5_8_SET_TYPE_0`이 원본에 없이 발화한다. `__CORNER_CHECKER__`를 켠 빌드에서만 Corner 통계가 달라진다
- 처방: `Event_Flag` 호출을 HD 갈래와 1.5SD 갈래 안으로 옮기거나 `if (MODE_DEC_HD == ... || MODE_DEC_1_5SD == ...)`로 감싼다 (동작 변경 아님, 원본 동작 복원)

### 발견 4 (MEDIUM, 문서 미고지 동작 변경): 4.1 수정 후 default 갈래가 `syn_th_BF0`을 새로 대입

- 위치: code_diff.md 4.1 수정 후 (문서 444행). 근거 decoder.cpp:467, 472, 2088
- 내용: 원본은 `LAYOUT_PRIME_512B_TLC_VSS_OFF`에서만 `syn_th_BF0`을 대입하고(467) default는 읽히지 않는 `syn_th_BF`에 대입한다(472). 즉 다른 layout에서는 `syn_th_BF0`이 미초기화 상태로 2088의 `syn_weight < syn_th_BF0` 비교에 쓰인다. 수정 후는 default에서 `syn_th_BF0 = SW_TH_BF_DEFAULT`를 대입해 이 동작을 바꾼다. 개선이지만 문서 전제 ㉰("값은 기존 상수에서 가져온다")와 4.1 본문 어디에도 이 변경이 적혀 있지 않다
- 처방: 4.1 "바뀐 점"에 명시한다. 코드 변경 없음 (문서 보강)

### 발견 5 (MEDIUM, 코드 결함, 적용 순서): 9장 3단계에서 `cur_sw_branch_idx[]`가 미초기화

- 위치: code_diff.md 9장 3단계, 2.2, 6.1. 근거 decoder.cpp:5-8(생성자), 19 이하(`Initialize_Dec`, 포인터만 NULL), 606-616(`Clear_Flag`), ecc_top.h:97(`Decoder m_dec;` 값 멤버), local_opt.cpp:45(`new ECC_Top()`)
- 내용: 3단계 서술 "`Select_BF`가 그대로라 `cur_sw_branch_idx[]`가 모두 0"은 근거가 없다. 배열을 0으로 두는 코드는 5.1 수정 후 `Select_BF` 안에만 있고 4단계에서 들어간다. 3단계에서 6.1 수정 후의 `group_branch != cur_sw_branch_idx[span]` 비교는 미초기화 값을 읽는다. "기존 동작과 결과가 같아야 한다"는 검증 기준이 성립하지 않는다
- 처방: 2.2와 함께 `Clear_Flag`에 배열 초기화를 넣는다 (발견 1 처방과 동일). 코드 추가, 동작 변경 없음
- 팀 C 관점 15, 팀 D 관점 9와 겹침

### 발견 6 (LOW, 문서 오류): "그대로 옮긴 것"이라는 전제와 다른 생략

- 위치: code_diff.md 전제, 1.2, 4.1, 6.1
- 내용:
  - ㉮ 4.1 수정 전이 주석 처리된 case 줄 14개(decoder.cpp:460-465, 469, 477-479, 481-482, 486-488, 490-491)를 표시 없이 뺐다
  - ㉯ 6.1 수정 전이 decoder.cpp:6981의 주석 줄을 표시 없이 뺐다
  - ㉰ 1.2 수정 전이 common.h:407의 꼬리 주석 `// __AUTO_LLR_OPT__`를 뺐다
- 처방: 생략한 곳에 `...` 표시를 넣거나 원문대로 싣는다. 뜻은 바뀌지 않는다

### 발견 7 (LOW, 문서 오류): 줄 범위 표기가 인용 내용이나 소스와 어긋남

- 위치와 내용:
  - ㉮ code_diff 6.1 제목 "6973-6999행"이지만 인용은 `#else` 갈래 7047까지 이어진다
  - ㉯ code_diff 6.2 제목 "7048-7071행"이지만 인용은 7073(함수 끝)까지다
  - ㉰ 상위 5.4 "2084-2130"은 `#if`에서 시작해 함수 끝에서 끝난다. 5.1의 2082-2130(함수)이나 6.1 표의 2084-2129(갈래) 중 하나로 맞춘다
  - ㉱ 상위 5.6 "6609-6626"과 code_diff 8.2 "6606-6626"의 끝 줄 6626은 `#else`다. 갈래는 6609-6625, 함수는 6606-6676
  - ㉲ 상위 5.2-3 "36-44"는 38-44가 맞다
  - ㉳ 상위 5.1과 context.md의 "local_opt.cpp:52-132"는 파싱 부분이고 함수는 52-184다. 문서가 인용하는 178(로그 출력)이 이 함수 안이다
- 처방: 표기 수정. 코드 변경 없음

### 발견 8 (LOW, 문서 누락): 8.1, 8.2의 생략 서술과 수정 후 코드 부재

- 위치: code_diff.md 8.1, 8.2
- 내용:
  - ㉮ 8.1의 `... (restart만 보는 갈래) ...`는 실제로 `iter == 0`도 본다 (decoder.cpp:6556-6558)
  - ㉯ 8.2는 수정 후 코드가 없고 남길 `else` 갈래(6615-6625)와 지울 `#else` 갈래(6626-6674)가 문서에 없다. 적용자는 소스를 직접 열어야 결과를 확인할 수 있다
  - ㉰ 8.2가 인용한 6604 주석에서 "(Pre-update)"가 빠졌다
- 처방: 8.2에 수정 후 코드를 싣는다. 코드 변경 없음

### 발견 9 (LOW, 문서 누락): 상위 6.3 "손대지 않아도 되는 곳" 표에 빠진 `__AUTO_LLR_OPT__` 네 곳

- 위치: 상위 문서 6.3 표. 근거 Grep `__AUTO_LLR_OPT__` decoder.cpp
- 내용: 7741-7743(`m_log_CSW_auto[i] = -1`), 7773-7775(`new int[MN_size]`), 7803-7805(`delete[]`), 7928-7938(`Print_Log_CSW_Auto` 정의)이 표에 없다. 모두 CSW 로그 배선이라 6.3 분류가 맞고 손댈 필요는 없다
- 처방: 표 보강. 팀 I 관점 12와 겹침

### 발견 10 (LOW, 사전 존재, 범위 밖 참고): 인용 구간 안의 원본 문제

- ㉮ local_opt.cpp:124의 `MODE_DEC_1_SSD`는 src 어디에도 정의가 없다 (정의된 이름은 common.h:78 `MODE_DEC_1_5SD`). 상위 5.5 표가 딸린 곳으로 적은 126-130이 이 조건 블록 안이다. 이 줄이 그대로면 AUTO 빌드가 애초에 컴파일되지 않으므로 외부 환경의 소스가 다를 수 있다. 두 문서 모두 언급이 없다
- ㉯ `SW_TH_BF0_512B_TLC_OFF`, `SW_TH_BF1_512B_TLC_OFF`는 `__12META__`가 아닐 때만 정의된다 (common.h:236-237). 원본 decoder.cpp:467-468과 code_diff 4.1 수정 후가 모두 이 상수를 쓰므로 `__12META__` 빌드에서는 원본과 같은 이유로 컴파일되지 않는다. 새 결함은 아니다
- 처방: 문서에 전제로 적어 두면 적용자가 헤매지 않는다. 코드 변경 요구 없음

### 참고 (LOW, 팀 D 관점 5): BF 진입 갈래의 span 1 분기 결정 방식 변화

- 원본 2091은 BF 진입 시 `flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0`으로 고정한다. 수정 후는 `Select_SW_Branch(1, syn_weight)`로 고른다. 현재 상수로는 `syn_weight < syn_th_BF0`(680 또는 630)이면 반드시 `SW_TH_5_8_SET0_*`(1100 또는 960)보다 작아 0이 되므로 결과가 같다. code_diff 5.1 ㉯는 span 0만 설명하고 span 1의 이 구조 변화는 적지 않았다

---

## 문제 없음으로 확인한 항목

- ㉮ code_diff 수정 전 블록 중 1.1, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.5, 3.6, 3.7, 7.1, 7.2, 7.3, 8.3은 소스와 글자 단위로 일치
- ㉯ 5.1, 6.1, 8.1의 인용된 줄(생략 표시 밖)은 소스와 글자 단위로 일치
- ㉰ 6.1의 `...`(7023-7035)는 AUTO 루프와 같음. 8.1 수정 후 `else` 갈래는 소스 6555-6565와 내용 동일
- ㉱ 7.3의 두 곳(4055-4059, 4274-4278)이 같다는 서술 맞음
- ㉲ 상위 6.2 표의 다섯 곳은 형태가 같음
- ㉳ 4.1 수정 후의 루프 변수 `i`는 함수 머리(454)에 선언되어 있음
- ㉴ `floor_flag`가 소멸자에서 해제되지 않는다는 서술 맞음. `floor_flag`가 복호에 쓰이지 않고 로그(178)에만 나간다는 서술 맞음
- ㉵ `syn_th_BF`, `syn_th_BF1`이 대입만 되고 읽히지 않는다는 서술 맞음
- ㉶ E절: `GROUP_TYPE_CSW` 비교식, 훑는 방향, 첫 row 기본값, `prev_CSW` 갱신 시점 모두 상위 3장과 code_diff 6.2 서술과 일치
- ㉷ 상위 2장, 3장의 `LLR_MATRIX_1.txt` 해석 표(그룹별 헤더 값, row 수, iteration 범위, CSW 나열, row 마지막 칸)는 파일과 일치

---

## 발견 요약

| 번호 | 심각도 | 구분 | 문제 한 줄 | 위치 |
|------|--------|------|-----------|------|
| 1 | HIGH | 코드 결함 (문서 누락) | `Clear_Flag`(decoder.cpp:612-613)가 2.2에서 지우는 두 멤버를 대입해 1단계에서 컴파일 실패 | code_diff 2.2, 5.1, 9장 1단계 |
| 2 | MEDIUM | 문서 누락 | `ITER_MAX_HBF` 딸린 곳 표가 전수가 아님 (decoder.cpp 24줄, main.cpp 1줄, TV_Dec_Inter.cpp 5줄 누락). "12곳" 개수도 표와 불일치 | 상위 5.5 표, code_diff 1.2 |
| 3 | MEDIUM | 코드 결함 (문서 미고지) | 수정 후 `Select_BF`의 Corner 이벤트가 HD, 1.5SD 외 모드에서도 발화 (원본은 두 모드에서만) | code_diff 5.1 수정 후 |
| 4 | MEDIUM | 문서 미고지 동작 변경 | 4.1 수정 후 default 갈래가 원본에서 미초기화였던 `syn_th_BF0`을 대입 | code_diff 4.1 |
| 5 | MEDIUM | 코드 결함 (적용 순서) | 9장 3단계 "`cur_sw_branch_idx[]`가 모두 0"은 근거 없음. 초기화 코드가 4단계(5.1)에만 있음 | code_diff 9장 3단계, 2.2, 6.1 |
| 6 | LOW | 문서 오류 | 4.1(주석 14줄), 6.1(6981), 1.2(407 꼬리 주석)를 표시 없이 생략. "그대로 옮긴 것" 전제와 어긋남 | code_diff 전제, 1.2, 4.1, 6.1 |
| 7 | LOW | 문서 오류 | 줄 범위 표기 6건이 인용 내용이나 소스와 어긋남 (6.1 제목, 6.2 제목, 5.4, 5.6과 8.2의 6626, 5.2-3의 36, 5.1의 52-132) | 상위 5.1, 5.2-3, 5.4, 5.6, code_diff 6.1, 6.2, 8.2 |
| 8 | LOW | 문서 누락 | 8.1 "restart만"은 `iter == 0`도 봄. 8.2 수정 후 코드 없음. 6604 주석 인용에서 "(Pre-update)" 빠짐 | code_diff 8.1, 8.2 |
| 9 | LOW | 문서 누락 | 6.3 표에 `m_log_CSW_auto` 관련 네 곳(7741, 7773, 7803, 7928-7938) 빠짐 | 상위 6.3 표 |
| 10 | LOW | 사전 존재 (범위 밖) | local_opt.cpp:124 `MODE_DEC_1_SSD` 정의 없음. `SW_TH_BF0/BF1_512B_TLC_OFF`는 `__12META__` 아닐 때만 정의 | local_opt.cpp:124, common.h:236-237 |

처방 중 코드 삭제를 요구하는 것은 발견 1(`Clear_Flag` 두 줄 삭제 후 초기화로 대체)뿐이며, 동작 변경을 요구하는 것은 없다 (발견 3의 처방은 원본 동작 복원).
