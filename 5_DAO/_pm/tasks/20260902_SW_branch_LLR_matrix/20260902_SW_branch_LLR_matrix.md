# SW 분기 LLR matrix 지원: 0_LDPC_original 수정 리스트

> 작성: 2026-09-02 23:13:58

## 1. 목적

LLR matrix가 iteration 구간 안에서 Syndrome Weight(SW)에 따라 여러 분기를 갖는 형태로 바뀌었다.
`0_LDPC_original`이 이 형태를 읽고 복호에 반영하도록 고칠 곳을 정리한다.
DAO 쪽 대응(매트릭스 모델, 유효성 규칙, GenLLRMode)은 이 문서에서 다루지 않는다.

**각 항목의 코드 수정 전후는 [code_diff.md](code_diff.md)에 있다.**
이 문서는 무엇을 왜 고치는지, code_diff.md는 어떻게 고치는지를 담는다.

대상 파일:
[common.h](../../../../0_LDPC_original/src/common.h),
[mode.h](../../../../0_LDPC_original/src/mode.h),
[ecc_data.h](../../../../0_LDPC_original/src/ecc_data.h),
[decoder.h](../../../../0_LDPC_original/src/decoder.h),
[decoder.cpp](../../../../0_LDPC_original/src/decoder.cpp),
[local_opt.cpp](../../../../0_LDPC_original/src/local_opt.cpp),
[ecc_top.cpp](../../../../0_LDPC_original/src/ecc_top.cpp)

---

## 2. 새 파일 형태

헤더의 그룹별 값 한 줄에 `{x}{y}` 표기가 들어간다.

- ㉮ `x`는 그 iteration 구간이 몇 개의 분기로 나뉘는지
- ㉯ `y`는 그 안에서 몇 번째 분기인지 (0부터, 오름차순)
- ㉰ 분기가 없으면 `1` 한 글자
- ㉱ `y`는 각 row의 마지막 칸과 같은 값이며, 분기가 없으면 row 마지막 칸은 `-1`
- ㉲ 분기 수 상한은 9 (한 자리씩 끊어 읽으므로)

`x`는 iteration 구간마다 따로 센다. 1~4가 분기 2개이고 5~8이 분기 3개이면
`20 20 21 30 31 32 1 1 ...` 처럼 섞여 나온다.

읽는 규칙:

- ㉮ 같은 `{x}{y}`가 연속하면 그 분기 안에서 iteration이 이어붙는다
- ㉯ `y`가 1 늘면 iteration이 그 구간의 시작으로 되돌아간다
- ㉰ `y`가 0으로 되돌아가면 새 구간이 시작되고 iteration은 앞 구간에서 이어진다
- ㉱ 분기마다 내부 iteration 분할이 달라도 된다. 구간의 시작과 끝만 모든 분기가 맞춘다

`Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`를 푼 결과:

| 그룹 | 헤더 값 | 분기 수 | 분기 index | row 수 | iteration | row 마지막 칸 |
|------|---------|---------|-----------|--------|-----------|--------------|
| 0 | 20 | 2 | 0 | 1 | 1~1 | 0 |
| 1 | 20 | 2 | 0 | 7 | 2~4 | 0 |
| 2 | 21 | 2 | 1 | 6 | 1~4 | 1 |
| 3 | 20 | 2 | 0 | 6 | 5~8 | 0 |
| 4 | 21 | 2 | 1 | 1 | 5~5 | 1 |
| 5 | 21 | 2 | 1 | 5 | 6~8 | 1 |
| 6 | 1 | 없음 | -1 | 5 | 9~24 | -1 |
| 7 | 1 | 없음 | -1 | 7 | 25~44 | -1 |
| 8 | 1 | 없음 | -1 | 6 | 45~64 | -1 |
| 9 | 1 | 없음 | -1 | 10 | 65~84 | -1 |
| 10 | 1 | 없음 | -1 | 10 | 85~104 | -1 |
| 11 | 1 | 없음 | -1 | 13 | 105~124 | -1 |

분기는 iteration 1~8에만 쓰이고 9 이후는 분기가 없다. 최대 iteration은 124다.

---

## 3. 먼저 풀어야 할 충돌: 그 줄은 이미 쓰이는 필드다

`{x}{y}`가 들어간 헤더 줄은 `PARAM_LLR::type_each_group`이다.
이 필드는 이미 뜻을 갖고 있다.

```
common.h:756    #define GROUP_TYPE_ITER     0
common.h:757    #define GROUP_TYPE_CSW      1
```

`decoder.cpp:7051-7068`이 이 값으로 **그룹 안에서 row를 무엇으로 고를지** 정한다.

- ㉮ `GROUP_TYPE_ITER`(0): row의 `iter_start`, `iter_end`로 고른다
- ㉯ `GROUP_TYPE_CSW`(1): 직전 iteration의 CSW(`prev_CSW`)와 row의 CSW 문턱으로 고른다

즉 `LLR_MATRIX_1.txt`의 `1`은 "분기 없음"이 아니라 `GROUP_TYPE_CSW`다. 값이 우연히 겹쳤다.

`20`, `21`을 넣으면 두 갈래 어디에도 걸리지 않는다. `table_row_idx`는 함수 앞머리에서 0으로
초기화되고(`decoder.cpp:6974`), 아래 검사(`decoder.cpp:7069`)는 `table_row_idx < 0` 또는
`>= num_row`만 보므로 0을 통과시킨다. 결과는 오류 없이 **항상 첫 번째 row의 파라미터를 쓰는 것**이다.

파일 자체가 이 필드의 원래 값을 잃었다는 것도 확인된다. 분기가 붙은 그룹들은
그룹 안 모든 row의 iteration 구간이 같아서 iteration으로는 row를 고를 수 없다.

| 그룹 | 헤더 값 | row 수 | 그룹 안 iteration | CSW 나열 |
|------|---------|--------|------------------|----------|
| 1 | 20 | 7 | 전부 2~4 | -1, 400, 120, 40, 32, 24, 16 |
| 2 | 21 | 6 | 전부 1~4 | -1, 272, 192, 120, 64, 8 |
| 3 | 20 | 6 | 전부 5~8 | -1, 616, 256, 72, 16, 8 |
| 5 | 21 | 5 | 전부 6~8 | -1, 984, 352, 96, 32 |

CSW가 내림차순이므로 이 그룹들은 모두 `GROUP_TYPE_CSW`(1)이어야 한다. `20`, `21`이 그 값을 덮었다.

---

## 4. 표기 개선 제안

분기 정보와 그룹 타입은 서로 직교하는 정보다. 분기가 있어도 그 분기 안의 그룹은
여전히 iteration으로 row를 고를지 CSW로 고를지 정해야 한다. 한 칸에 겹쳐 쓸 수 없다.

**㉮ 분기 전용 줄을 새로 넣는다 (추천)**

`type_each_group` 줄은 원래 뜻(0 또는 1)으로 되돌리고, 그 아래에 그룹별 분기 index 줄을 새로 둔다.

```
12                                  <- num_group
1 7 6 6 1 5 5 7 6 10 10 13          <- num_set_each_group
1 1 1 1 1 1 1 1 1 1 1 1             <- type_each_group (원래 뜻)
0 0 1 0 1 1 -1 -1 -1 -1 -1 -1       <- sw_branch_idx_each_group (신규)
```

분기 총수 `x`는 파일에 적지 않아도 된다. 읽는 쪽에서 "같은 iteration 구간을 덮는 서로 다른 분기
index의 개수"로 세면 나온다. 헤더만 보고 구조가 읽히고, 자릿수 제한이 없어 분기 수 상한이
사라지며, row 마지막 칸과 대조하는 검사도 그대로 가능하다.

**㉯ 자리를 늘려 `{x}{y}{type}` 세 자리로 쓴다**

`201` 같은 형태가 된다. 사람이 읽기 어렵고, 분기 수가 두 자리가 되면 표기가 무너진다.

**㉰ row 마지막 칸만 정본으로 삼는다**

헤더에서 분기 정보를 빼고 row의 마지막 칸만 남긴다. 그룹의 분기 index는 그 그룹 첫 row에서 읽는다.
중복이 사라져 어긋날 여지가 없지만, 헤더만 보고 구조를 파악할 수 없다.

**분기 없음을 -1로 두는 것에 대하여**

-1이 맞다. 0을 쓰면 "분기 없음"과 "0번 분기"가 구별되지 않는다.

row 마지막 칸을 쓰는 것도 안전하다. 이 칸은 `PARAM_LLR::floor_flag`로 읽히지만
(`local_opt.cpp:105`, `local_opt.cpp:114`), 복호에는 전혀 쓰이지 않고 로그 출력에만 나간다
(`local_opt.cpp:178`). 용도를 SW 분기 index로 바꿔도 깨질 동작이 없다.
다만 이름이 뜻과 맞지 않으므로 `sw_branch_idx`로 바꾼다.

---

## 5. 수정 대상

각 항목의 코드 수정 전후는 [code_diff.md](code_diff.md)에 같은 순서로 실려 있다.
적용 순서 제안은 [code_diff.md 9장](code_diff.md#ch9)에 있다.

### 5.1 파일 읽기: `LOCAL_OPT::Read_LLR_info_Auto`

`local_opt.cpp:52-132` (수정 전후: [code_diff.md 3장](code_diff.md#ch3))

- 1. 분기 index 줄을 읽는 반복문 추가 (4장 ㉮를 택할 경우)
- 2. `floor_flag`를 `sw_branch_idx`로 이름 변경 (`local_opt.cpp:105`, `114`, `178`)
- 3. 최대 iteration 계산 수정. 지금은 마지막 row의 `iter_end`를 최대값으로 쓴다.

```
local_opt.cpp:116    m_param_dec->MN_num = LLR_info->iter_end[LLR_info->num_row - 1];
```

분기가 생기면 마지막 row가 최대 iteration을 갖는다는 보장이 없다. 전체 row의 `iter_end`
최대값으로 바꾼다. `local_opt.cpp:120`의 같은 표현도 함께 고친다.

- 4. `num_row`의 뜻이 달라진 것을 확인한다. 분기가 붙으면 같은 iteration을 여러 row가 덮으므로
     row 수가 iteration 수와 무관해진다. `num_row`로 배열을 잡는 곳은 그대로 두어도 되지만,
     `num_row`를 iteration 수로 간주하는 곳이 있으면 고쳐야 한다

### 5.2 구조체: `PARAM_LLR`

`ecc_data.h:179-198` (수정 전후: [code_diff.md 2장](code_diff.md#ch2))

- 1. `int* sw_branch_idx_each_group` 추가 (그룹 단위)
- 2. `int* floor_flag` 를 `int* sw_branch_idx` 로 이름 변경 (row 단위)
- 3. MPI로 매트릭스를 뿌리는 곳(`local_opt.cpp:38-44`)은 손대지 않는다. AUTO 빌드에서는 `__RUN_MPI__`가 정의되지 않아 그 블록이 컴파일되지 않고, 각 rank가 파일을 따로 읽는다 (code_diff.md 3.7장)
- 4. 소멸자에서 새 배열 해제 (`local_opt.cpp:14-15` 부근)

### 5.3 그룹 선택: `Decoder::Get_Cur_LLR_Idx_FILE`

`decoder.cpp:6973-7073`. 여기가 축이다.
(수정 전후: [code_diff.md 6장](code_diff.md#ch6))

`__AUTO_LLR_OPT__` 경로(`decoder.cpp:6984-6999`)는 iteration 범위만 본다.

```
for (g = num_group - 1; g >= 0; g--) {
    ... start_idx, end_idx 계산 ...
    if ((iter >= iter_start[start_idx]) && (iter <= iter_end[end_idx])) {
        selected_group = g;
        break;
    }
}
```

- 1. 분기 조건을 추가한다. 그룹의 분기 index가 -1이거나 현재 프레임의 분기와 같을 때만 고른다
- 2. 지금은 뒤에서 앞으로 훑으며 처음 맞는 것을 잡는다. 분기가 생기면 같은 iteration을
     여러 그룹이 덮으므로 이 순서 의존이 위험하다. 분기 일치를 선택 조건에 넣어야
     결과가 순서에 좌우되지 않는다
- 3. `decoder.cpp:7048`의 오류 검사에 "두 갈래 어디에도 걸리지 않은 경우"를 추가한다.
     지금은 `table_row_idx`가 초기값 0으로 남아 조용히 통과한다.
     `type_each_group`이 `GROUP_TYPE_ITER`도 `GROUP_TYPE_CSW`도 아니면 오류로 잡는다
- 4. `__AUTO_LLR_OPT__`가 아닌 경로(`decoder.cpp:7001-7020`)는 iteration과 분기 조합을
     그룹 번호로 못박아 두었다. 분기 개수가 가변이면 이 하드코딩을 걷어내고
     `__AUTO_LLR_OPT__` 경로와 같은 탐색으로 통일한다

```
decoder.cpp:7001    iter == 1,   1_4_Set == TYPE_0  ->  group 0
decoder.cpp:7005    iter 2~4,    1_4_Set == TYPE_0  ->  group 1
decoder.cpp:7009    iter == 5,   5_8_Set == TYPE_0  ->  group 2, 아니면 group 4
decoder.cpp:7015    iter 6~8,    5_8_Set == TYPE_0  ->  group 3, 아니면 group 5
```

`1_4_Set`이 `TYPE_1`인 경우 `selected_group`이 -1로 남아 오류 출력으로 빠지는 것도
같이 정리해야 한다.

### 5.4 분기 결정: `Decoder::Select_BF`

`decoder.cpp:2084-2130`. `decoder.cpp:1968-1970`에서 `mn == 0`일 때 불린다.
(수정 전후: [code_diff.md 5장](code_diff.md#ch5),
문턱 배열화는 [code_diff.md 4장](code_diff.md#ch4))

지금 `__AUTO_LLR_OPT__` 경로는 한 줄이 전부다.

```
decoder.cpp:2085    flag_BF_on = FLAG_LOW;
```

- 1. SW로 분기를 정하고 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 세우는 부분이
     `__AUTO_LLR_OPT__` 경로에도 필요하다
- 2. 분기 개수가 가변이므로 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 값 두 개짜리 enum이 아니라
     정수 index로 일반화한다 (`common.h:717-725`)
- 3. SW 문턱이 지금은 컴파일 상수다 (`common.h:202-251`). 분기 개수가 가변이면
     구간별 문턱 배열로 바꾸고 파일이나 실행 인자로 받아야 한다.
     문턱을 읽어 넣는 곳은 `decoder.cpp:459-493`이다
- 4. `syn_th_BF`, `syn_th_BF0`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1`은
     `decoder.h:301` 부근에 낱개 변수로 선언되어 있다. 배열로 바꾼다

### 5.5 iteration 번호 체계: `ITER_MAX_HBF`

수정 전후: [code_diff.md 1.2장](code_diff.md#ch1_2)과
[code_diff.md 7장](code_diff.md#ch7)

```
common.h:403    #ifdef __AUTO_LLR_OPT__
common.h:404    #define ITER_MAX_HBF                0
common.h:405    #else
common.h:406    #define ITER_MAX_HBF                4
common.h:407    #endif
```

`__AUTO_LLR_OPT__`에서 0이라, BF가 없다는 가정이 이 상수로도 굳어 있다.
BF를 살리려면 4로 맞춰야 하고, 아래가 모두 딸려 온다.

| 위치 | 내용 |
|------|------|
| decoder.cpp:564 | `MN_max = MN[MN_num-1] + ITER_MAX_HBF` |
| decoder.cpp:1149 | Preprocessing 시점 (`mn == 1` 또는 `mn == ITER_MAX_HBF + 1`) |
| decoder.cpp:1929 | VNU 로그 출력 조건 |
| decoder.cpp:1976 | BF 미진입 시 `iter_num -= ITER_MAX_HBF` |
| decoder.cpp:2097-2098 | BF 미진입 시 `mn`, `MN`을 4씩 밀기 |
| decoder.cpp:2114-2115 | 같음 (HD가 아닌 모드) |
| decoder.cpp:2310, 3487 | Preprocessing column read 표시 |
| decoder.cpp:6454 | 특정 iteration 판정 |
| decoder.cpp:6545, 6571 | Edge clear 시점 |
| decoder.cpp:7583 | 로그 버퍼 크기 |
| local_opt.cpp:126-130 | `MN[i] -= ITER_MAX_HBF`, `MN[0] = ITER_MAX_HBF` |

`__AUTO_LLR_OPT__` 경로에 `iter <= 4`로 상수를 박아 둔 곳이 네 군데 있다.
`ITER_MAX_HBF`가 0이라 생긴 우회이므로, 4로 되돌리면 지우고 `ITER_MAX_HBF`로 통일한다.

| 위치 | 내용 |
|------|------|
| decoder.cpp:2374-2378 | C2V 1bit precision 조건 |
| decoder.cpp:2797-2801 | V2C 저장 1bit 모드 조건 |
| decoder.cpp:4055-4059 | VN 1bit precision 조건 |
| decoder.cpp:4274-4278 | 같음 (다른 VN 경로) |

이 네 곳은 모두 `flag_BF_on`으로 먼저 걸러진다. `__AUTO_LLR_OPT__`에서 `flag_BF_on`이
항상 `FLAG_LOW`이므로 지금은 실행되지 않는 경로다. BF를 살리면 살아난다.

### 5.6 초기화 시점

수정 전후: [code_diff.md 8장](code_diff.md#ch8)

| 위치 | 함수 | 내용 |
|------|------|------|
| decoder.cpp:6541-6565 | `Is_Iter_Type_Edge_Clear` | `iter == 0 \|\| iter == 1 \|\| iter == ITER_MAX_HBF + 1`. `ITER_MAX_HBF`가 0이면 1과 1로 겹친다. 4로 되돌리면 1과 5 두 지점이 된다 |
| decoder.cpp:6609-6626 | `Is_Iter_Type_Init` | `__AUTO_LLR_OPT__` 경로가 HD에서 `iter == 0`만 본다. restart 처리가 빠져 있는 것이 의도인지 확인 필요 |
| decoder.cpp:1146-1156 | Preprocessing | `flag_BF_on`에 따라 `mn == 1` 또는 `mn == ITER_MAX_HBF + 1`. 지금은 앞의 조건으로 굳어 있다 |

---

## 6. `__AUTO_LLR_OPT__` 전수 목록

### 6.1 고쳐야 하는 곳

| 파일 | 줄 | 내용 |
|------|-----|------|
| common.h | 403-407 | `ITER_MAX_HBF` 0 또는 4 |
| decoder.cpp | 1137-1141 | `Get_Cur_LLR_Idx_FILE` 대 `Get_VNU_Table_Idx` 갈림 |
| decoder.cpp | 2084-2129 | `Select_BF`. AUTO에서 `flag_BF_on = FLAG_LOW` 고정 |
| decoder.cpp | 2374-2378 | 1bit precision 조건에 `iter <= 4` 상수 |
| decoder.cpp | 2797-2801 | 같음 |
| decoder.cpp | 4055-4059 | 같음 |
| decoder.cpp | 4274-4278 | 같음 |
| decoder.cpp | 6541-6565 | `Is_Iter_Type_Edge_Clear` |
| decoder.cpp | 6609-6626 | `Is_Iter_Type_Init` |
| decoder.cpp | 6984-7047 | 그룹 선택 본체 |

### 6.2 파라미터를 가져오는 갈림길 (분기 지원 자체와는 무관, 확인만)

`Get_VNU_LLR_SET_FILE`(파일에서 읽은 매트릭스)과 `Get_VNU_Ch_LLR_Adaptive` 및
`Get_VNU_Th_Adaptive`(소스에 박힌 표)를 고르는 지점이다. 다섯 곳 모두 형태가 같다.

| 파일 | 줄 |
|------|-----|
| decoder.cpp | 3985-3990 |
| decoder.cpp | 4160-4165 |
| decoder.cpp | 4366-4371 |
| decoder.cpp | 4505-4510 |
| decoder.cpp | 4673-4678 |

### 6.3 손대지 않아도 되는 곳

최적화 실행 배선(시드 관리, uncor 파일, 결과 출력, 로그, 콘솔 출력 억제)이다.

| 파일 | 줄 | 내용 |
|------|-----|------|
| mode.h | 22-26 | 스위치 정의. `__PROGRAM_MODE_REF_C__`이고 Windows가 아닐 때만 켜진다 |
| common.h | 49-53 | `DISPLAY_UNIT` |
| ecc_data.h | 143-146 | `flag_print_CSW_log`, `rank_supercom` |
| decoder.h | 185-188 | `Compute_CSW_Auto`, `Print_Log_CSW_Auto` 선언 |
| decoder.h | 431-434 | `fp_log_CSW_auto`, `m_log_CSW_auto` |
| decoder.cpp | 505-510 | power stopping을 OFF로 고정 |
| decoder.cpp | 526-534 | 콘솔 출력 억제 |
| decoder.cpp | 548-562 | 콘솔 출력 억제 |
| decoder.cpp | 570-599 | 콘솔 출력 억제 |
| decoder.cpp | 1917-1921 | CSW 로그 수집 |
| decoder.cpp | 7339-7352 | `Compute_CSW_Auto` 정의 |
| decoder.cpp | 7522-7528 | CSW 로그 파일 열기 |
| decoder.cpp | 7549-7553 | CSW 로그 파일 닫기 |
| decoder.cpp | 7574-7578 | CSW 로그 출력 |
| decoder.cpp | 8109-8113 | `state_hd_error_floor_set` 초기화. 양쪽 갈래가 같은 값이다 |
| ecc_top.cpp | 322 | PCM 출력 억제 |
| ecc_top.cpp | 496 | 시드 초기화 |
| ecc_top.cpp | 532, 595, 624, 699, 783, 927, 965 | uncor 시드와 벡터 파일 관리 |
| ecc_top.cpp | 652, 680, 944-950 | 결과 출력 |
| ecc_top.cpp | 2166-2170, 2219 | 결과 파일 열고 닫기 |
| ecc_top.cpp | 2562-2566, 2567 | uncor 시드 읽기와 결과 기록 |
| ecc_top.h | 161-165 | 멤버 |
| main.cpp | 12-15, 54, 92, 140, 259, 313, 324, 593, 609, 637, 650, 706, 922-925, 966-969 | 진입점과 `LOCAL_OPT` 배선 |
| random.cpp | 222 | 시드 |
| random.h | 31 | 시드 선언 |

---

## 7. 미결정 사항

- ㉮ 표기를 4장 ㉮(분기 전용 줄 추가), ㉯(세 자리), ㉰(row 마지막 칸만) 중 무엇으로 갈지
- ㉯ SW 문턱을 컴파일 상수로 둘지, 파일이나 실행 인자로 받을지.
     후자면 `PARAM_DEC` 또는 LLR matrix 파일에 자리를 만들어야 한다
- ㉰ 분기가 있는 구간을 iteration 1~8로 못박을지, 임의 구간을 허용할지.
     `LLR_MATRIX_1.txt`는 1~8만 쓰지만 형태 자체는 어디든 허용한다
- ㉱ `__AUTO_LLR_OPT__`가 아닌 경로(`decoder.cpp:7001-7020`)의 하드코딩을 걷어내고
     한 갈래로 통일할지, 두 경로를 그대로 둘지
