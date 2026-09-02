# SW 분기 LLR matrix 지원: 코드 수정 전후

> 작성: 2026-09-02 23:13:58
> 수정: 2026-09-03 02:18:03 (딥 리뷰 반영, 결정 대기 항목 표시)
> 상위 문서: [20260902_SW_branch_LLR_matrix.md](20260902_SW_branch_LLR_matrix.md)

## 이 문서의 전제

수정 전 코드는 `0_LDPC_original/src`를 옮긴 것이다. 주석 처리된 줄과 꼬리 주석은 뺐고, 생략한 코드는 `...`로 표시했다.
수정 후 코드는 아래 셋을 택했을 때의 모습이다. 다른 안을 고르면 5장과 6장이 달라진다.

- ㉮ 표기는 상위 문서 4장 ㉮(분기 전용 줄을 새로 넣는다)
- ㉯ 분기 없음은 `-1`, 이름은 `sw_branch_idx`
- ㉰ SW(Syndrome Weight, 신드롬 무게) 문턱은 배열로 바꾸되 값은 기존 상수에서 가져온다 (파일 입력은 나중 단계)

**결정 대기 표시**: `[결정 대기 N]`은 [리뷰 Round 3 report](review/r3_round3_lv2_verification/report.md)의 사용자 결정 항목 N에 따라 내용이 달라지는 곳이다. 그 밖의 코드는 결정과 무관하게 확정된 것이다.

| 결정 | 내용 |
|------|------|
| 1 | 비AUTO 갈래 통일을 철회할지 (8.1, 8.2 삭제 여부) |
| 2 | 구간(span)을 iteration 범위로 정할지 |
| 3 | iteration 1~4 구간에 분기를 둘지, 문턱 130을 쓸지 |
| 4 | 파일 형태 확정과 DAO 수정 범위 |
| 5 | `MN[]` 보정에 하한을 둘지, 보정식을 바꿀지 |
| 6 | 검사 실패 시 멈추는 수단 (`return err` 사슬 또는 `exit(1)`) |
| 7 | 2SD와 3SD의 적용 범위 |
| 8 | 분기 3개 이상 지원 여부 (문턱 입력 방식이 전제) |

새로 쓰는 이름:

| 이름 | 자리 | 뜻 |
|------|------|-----|
| `SW_BRANCH_NONE` | common.h | 분기 없음을 나타내는 값 (-1). 구간 번호에도 같은 값을 쓴다 |
| `MAX_SW_SPAN` | common.h | 분기를 가질 수 있는 iteration 구간의 최대 개수 |
| `MAX_SW_BRANCH` | common.h | 한 구간의 분기 최대 개수 |
| `sw_branch_idx_each_group` | PARAM_LLR | 그룹별 분기 index |
| `sw_span_idx_each_group` | PARAM_LLR | 그룹이 속한 구간 번호 (파서가 계산) |
| `num_sw_span` | PARAM_LLR | 분기가 걸린 구간의 개수 (파서가 계산) |
| `num_sw_branch_each_span` | PARAM_LLR | 구간별 분기 개수 (파서가 계산, 4.1의 상수와 대조) |
| `sw_branch_idx` | PARAM_LLR | row별 분기 index |
| `cur_sw_branch_idx[]` | Decoder | 이번 프레임이 구간별로 탄 분기 |
| `num_sw_branch[]` | Decoder | 구간별 분기 개수 (컴파일 상수) |
| `syn_th_sw_branch[][]` | Decoder | 구간별 분기 문턱 |
| `Select_SW_Branch` | Decoder | SW 문턱으로 한 구간의 분기 index를 고르는 함수 |

---

<a id="ch1"></a>

## 1. 상수 추가

### 1.1 common.h (`GROUP_TYPE_CSW` 아래, 757행 부근)

수정 전:

```cpp
#define GROUP_TYPE_ITER     0
#define GROUP_TYPE_CSW      1
```

수정 후:

```cpp
#define GROUP_TYPE_ITER     0
#define GROUP_TYPE_CSW      1

/* SW 분기 */
#define SW_BRANCH_NONE      (-1)    // 그 그룹은 SW와 무관하게 쓰인다
#define MAX_SW_SPAN         4       // 분기를 가질 수 있는 iteration 구간 수
#define MAX_SW_BRANCH       9       // 한 구간의 분기 수 상한
```

<a id="ch1_2"></a>

### 1.2 common.h 403-407행: `ITER_MAX_HBF`

수정 전:

```cpp
#ifdef __AUTO_LLR_OPT__
#define ITER_MAX_HBF                0
#else
#define ITER_MAX_HBF                4
#endif // __AUTO_LLR_OPT__
```

수정 후:

```cpp
#define ITER_MAX_HBF                4
```

`__AUTO_LLR_OPT__`에서 BF(Bit Flipping, HD 복호의 초기 iteration을 1bit precision으로 도는 모드)를 살리므로 갈래를 없앤다.
값이 0에서 4로 바뀌면 동작이 달라지는 곳은 다음과 같다.

- ㉮ 상위 문서 5.5장 표의 14줄
- ㉯ `decoder.cpp:2169` (`__DUAL_UPDATE__` 안, 켜져 있음). partial CRC로 조기 종료를 막는 지점이 mn 1 하나에서 mn 1과 5 둘로 늘어난다. `stop_by_partial_crc`와 throughput 지표 `overall_clk`이 바뀐다
- ㉰ 꺼진 스위치 안의 5곳 (`decoder.cpp:1448, 1622, 1828`의 `__RUN_PARITY_SKIP__`, `1821`의 `__RUN_PREPROCESSING__`, `2190`의 `__DUAL_UPDATE__` `#else`). 스위치를 켜면 살아난다
- ㉱ `local_opt.cpp:124-131`의 HD 보정 블록. 결과는 3.5장에 있다

값이 바뀌어도 동작이 그대로인 곳: `MN_size` 계열 17곳과 `decoder.cpp:564`는 `MN[MN_num-1]`이 4 줄고 이 상수가 4 늘어 합이 같다. `TV_Dec_Inter.cpp`의 5곳은 TV 빌드와 AUTO 빌드가 `mode.h`에서 배타라 영향이 없다.

---

<a id="ch2"></a>

## 2. 구조체와 멤버

### 2.1 ecc_data.h 179-198행: `PARAM_LLR`

수정 전:

```cpp
struct PARAM_LLR{
    int num_para_each_set;
    int num_dv;
    int num_row;
    int* dv_from;
    int* dv_to;
    int num_group;
    int* num_set_each_group;
    int num_col;
    int* type_each_group;
    int restart_num;
    int* restart_iter;
    int* max_value;
    int* min_value;
    int** LLR_MATRIX;
    int* CSW_thr;
    int* iter_start;
    int* iter_end;
    int* floor_flag;
};
```

수정 후:

```cpp
struct PARAM_LLR{
    int num_para_each_set;
    int num_dv;
    int num_row;
    int* dv_from;
    int* dv_to;
    int num_group;
    int* num_set_each_group;
    int num_col;
    int* type_each_group;
    int* sw_branch_idx_each_group;          // 그룹별 SW 분기 index. 분기 없으면 SW_BRANCH_NONE
    int* sw_span_idx_each_group;            // 그룹이 속한 구간 번호. 분기 없으면 SW_BRANCH_NONE
    int num_sw_span;                        // 분기가 걸린 구간의 개수
    int num_sw_branch_each_span[MAX_SW_SPAN]; // 구간별 분기 개수
    int restart_num;
    int* restart_iter;
    int* max_value;
    int* min_value;
    int** LLR_MATRIX;
    int* CSW_thr;
    int* iter_start;
    int* iter_end;
    int* sw_branch_idx;                     // row별 SW 분기 index
};
```

`ecc_data.h`는 `common.h`를 include하므로 `MAX_SW_SPAN`을 그대로 쓸 수 있다.
이 구조체는 포인터로만 전달되고 값 복사나 `sizeof`를 쓰는 곳이 없어 중간 삽입이 안전하다.

### 2.2 decoder.h 296-306행: 분기 상태와 문턱

수정 전:

```cpp
    int         flag_BF_on;     // 0 : 3bit precision mode, 1: 1bit precision mode
    int         flag_HD_1_4_Set;
    int         flag_HD_5_8_Set;
    int         syn_weight;     // partial syndrome
    int         psyn_weight;    // partial syndrome
    int         syn_th_BF;      //
    int         syn_th_BF0;   // S-4 Set
    int         syn_th_BF1;   // S-4 Set
    int       syn_th_5_8_Set_0;   // S-8 Set
    int       syn_th_5_8_Set_1;   // S-8 Set
```

수정 후:

```cpp
    int         flag_BF_on;     // 0 : 3bit precision mode, 1: 1bit precision mode
    int         syn_weight;     // partial syndrome
    int         psyn_weight;    // partial syndrome
    int         syn_th_BF0;     // BF 진입 문턱
    /* 구간별 SW 분기. span 0 = iteration 1~4, span 1 = iteration 5~8 [결정 대기 2] */
    int         cur_sw_branch_idx[MAX_SW_SPAN];
    int         num_sw_branch[MAX_SW_SPAN];
    int         syn_th_sw_branch[MAX_SW_SPAN][MAX_SW_BRANCH - 1];
```

`flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 `cur_sw_branch_idx[]`가 대신한다.
`syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_1`은 대입만 되고 읽히는 곳이 없으므로 지운다.

`[결정 대기 3]` `syn_th_BF1`의 값(`SW_TH_BF1_512B_TLC_OFF` = 130)을 iteration 1~4 구간의 분기 문턱으로 쓸지는 결정 3에 달려 있다.
코드 쪽 근거는 `decoder.h:302-303`의 `// S-4 Set` 주석이 `syn_th_BF0`과 `syn_th_BF1`을 한 묶음으로 짝짓는 것과 130이 BF 진입 문턱 680보다 작다는 것뿐이고, 배경 메모는 이 구간에 분기를 두지 않는다. 4.1에서는 이 값을 넣어 두었다.

### 2.3 decoder.h: 새 함수 선언

수정 전 (`Select_BF` 선언 부근):

```cpp
    void    Select_BF();
```

수정 후:

```cpp
    void    Select_BF();
    int     Select_SW_Branch(int span_idx, int weight);
```

### 2.4 decoder.cpp 606-616행: `Clear_Flag`

2.2에서 지우는 두 멤버에 대입하는 곳이다. 프레임마다 `decoder.cpp:1091`에서 메인 루프보다 먼저 불린다.

수정 전:

```cpp
void Decoder::Clear_Flag()
{
    real_mn = 0;
    flag_BF_on = FLAG_LOW;
    flag_dec_1iter = FLAG_LOW;
    flag_HD_1_4_Set = FLAG_LOW;
    flag_HD_5_8_Set = FLAG_LOW;
    state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
    cnt_hd_error_floor = 0;
}
```

수정 후:

```cpp
void Decoder::Clear_Flag()
{
    real_mn = 0;
    flag_BF_on = FLAG_LOW;
    flag_dec_1iter = FLAG_LOW;
    for (int i = 0; i < MAX_SW_SPAN; i++) {
        cur_sw_branch_idx[i] = 0;
    }
    iter_num = 0;
    state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
    cnt_hd_error_floor = 0;
}
```

- ㉮ `cur_sw_branch_idx[]`를 여기서 0으로 두므로 `Select_BF`(5장)가 들어가기 전 단계에서도 배열이 정의된 값을 갖는다. 5.1의 앞머리 초기화와 겹치지만 같은 값을 두 번 쓰는 것이라 무해하다
- ㉯ `iter_num`은 `Check_End_Iter`가 채우는 값인데 루프가 한 번도 돌지 않는 프레임에서는 앞 프레임 값이 남는다. 여기서 0으로 둔다

### 2.5 ecc_top.cpp 197-210행: 4인자 `Init_ECC_Top`

비AUTO 진입점(`main.cpp:105, 127`)이 부르는 오버로드다. `m_param_LLR`을 세우지 않은 채 208행에서 `Init_Dec`에 넘긴다.
`ECC_Top` 생성자(`ecc_top.cpp:6-34`)의 포인터 초기화 목록에도 이 멤버가 없다.

수정 전:

```cpp
void ECC_Top::Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec, int my_rank, int num_pro)
{
    m_ecc_info = info;
    m_param_dec = param_dec;
    m_my_rank = my_rank;
    m_num_process = num_pro;
```

수정 후:

```cpp
void ECC_Top::Init_ECC_Top(ECC_INFO* info, PARAM_DEC* param_dec, int my_rank, int num_pro)
{
    m_ecc_info = info;
    m_param_dec = param_dec;
    m_my_rank = my_rank;
    m_num_process = num_pro;
    m_param_LLR = NULL;
```

비AUTO 빌드에서 `m_param_LLR`이 NULL임이 보장되어야 4.1의 대조 검사가 이 포인터를 안전하게 건너뛸 수 있다.

---

<a id="ch3"></a>

## 3. 파일 읽기: local_opt.cpp

### 3.1 배열 할당 (74행)

수정 전:

```cpp
    LLR_info->num_set_each_group = new int[LLR_info->num_group];     LLR_info->type_each_group = new int[LLR_info->num_group];
```

수정 후:

```cpp
    LLR_info->num_set_each_group = new int[LLR_info->num_group];     LLR_info->type_each_group = new int[LLR_info->num_group];
    LLR_info->sw_branch_idx_each_group = new int[LLR_info->num_group];
    LLR_info->sw_span_idx_each_group = new int[LLR_info->num_group];
```

### 3.2 분기 index 줄 읽기 (81-84행)

수정 전:

```cpp
    for (i = 0; i < LLR_info->num_group; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->type_each_group[i] = c;
    }
```

수정 후:

```cpp
    for (i = 0; i < LLR_info->num_group; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->type_each_group[i] = c;
    }
    /* 그룹별 SW 분기 index. 분기가 없는 그룹은 SW_BRANCH_NONE */
    for (i = 0; i < LLR_info->num_group; i++) {
        fscanf(matrix_in, "%d", &c);
        LLR_info->sw_branch_idx_each_group[i] = c;
    }
    /* 구간 번호. 분기 index가 0으로 되돌아갈 때마다 다음 구간이다 [결정 대기 2]
       구간의 첫 그룹은 분기 0이어야 하고, 같은 구간 안에서 index는 작아지지 않는다 */
    LLR_info->num_sw_span = 0;
    {
        int prev_branch = SW_BRANCH_NONE;
        for (i = 0; i < LLR_info->num_group; i++) {
            int b = LLR_info->sw_branch_idx_each_group[i];
            if (b == SW_BRANCH_NONE) {
                LLR_info->sw_span_idx_each_group[i] = SW_BRANCH_NONE;
            }
            else {
                if (b < 0 || b >= MAX_SW_BRANCH) {
                    printf("[Error] SW branch index %d out of range @group%d\n", b, i);
                    err = TRUE;
                    b = 0;
                }
                if (b == 0 && prev_branch != 0) {
                    LLR_info->num_sw_span++;
                }
                else if (prev_branch == SW_BRANCH_NONE || b < prev_branch) {
                    printf("[Error] SW branch order @group%d: prev %d, cur %d\n", i, prev_branch, b);
                    err = TRUE;
                    if (LLR_info->num_sw_span == 0) LLR_info->num_sw_span = 1;
                }
                LLR_info->sw_span_idx_each_group[i] = LLR_info->num_sw_span - 1;
            }
            prev_branch = b;
        }
        if (LLR_info->num_sw_span > MAX_SW_SPAN) {
            printf("[Error] num_sw_span %d > MAX_SW_SPAN %d\n", LLR_info->num_sw_span, MAX_SW_SPAN);
            err = TRUE;
        }
    }
    /* 구간별 분기 개수. 분기 index는 0부터 빈틈없이 이어져야 한다 */
    if (!err) {
        int seen[MAX_SW_SPAN][MAX_SW_BRANCH];
        int s, b;
        for (s = 0; s < MAX_SW_SPAN; s++) {
            LLR_info->num_sw_branch_each_span[s] = 0;
            for (b = 0; b < MAX_SW_BRANCH; b++) seen[s][b] = 0;
        }
        for (i = 0; i < LLR_info->num_group; i++) {
            b = LLR_info->sw_branch_idx_each_group[i];
            s = LLR_info->sw_span_idx_each_group[i];
            if (b == SW_BRANCH_NONE) continue;
            seen[s][b] = 1;
            if (b + 1 > LLR_info->num_sw_branch_each_span[s]) LLR_info->num_sw_branch_each_span[s] = b + 1;
        }
        for (s = 0; s < LLR_info->num_sw_span; s++) {
            for (b = 0; b < LLR_info->num_sw_branch_each_span[s]; b++) {
                if (!seen[s][b]) {
                    printf("[Error] SW branch %d missing @span%d\n", b, s);
                    err = TRUE;
                }
            }
        }
    }
```

파서가 받아들이는 헤더의 규칙:

- ㉮ 구간의 첫 그룹은 분기 0이다. `1 0 -1 -1`처럼 분기 1 그룹이 앞에 오면 오류다
- ㉯ 같은 구간 안에서 분기 index는 작아지지 않는다. 같은 분기의 그룹이 잇달아 여러 개여도 된다 (그룹 0과 1이 둘 다 분기 0)
- ㉰ 분기 0이 다시 나오면 새 구간이다. 따라서 같은 구간의 분기 0 그룹은 잇달아 놓아야 한다. `0 1 0` 배치는 두 구간으로 센다
- ㉱ 구간은 `MAX_SW_SPAN`개까지, 분기 index는 `MAX_SW_BRANCH` 미만이며 0부터 빈틈없이 이어진다

`[결정 대기 2]` 이 계산은 구간 번호를 헤더의 등장 순서로 매긴다. 4.1과 5.1은 구간 0을 iteration 1~4, 구간 1을 iteration 5~8로 고정해 쓰므로, 분기가 iteration 5~8에만 있는 파일(배경 메모의 예시)에서는 그 구간이 구간 0이 되어 문턱이 어긋난다. 결정 2에 따라 구간을 iteration 범위로 정하는 형태로 바꾸며, 그 경우 계산 위치를 `iter_start`가 채워진 뒤(115행 뒤)로 옮기고 5.1의 상수 첨자 `[1]`도 범위로 찾게 바꾼다.

4장 ㉮ 형태로 변환한 `LLR_MATRIX_1.txt`(분기 줄 `0 0 1 0 1 1 -1 -1 -1 -1 -1 -1`)를 넣으면 이렇게 나온다.

| 그룹 | 분기 index | 구간 번호 |
|------|-----------|----------|
| 0, 1 | 0 | 0 |
| 2 | 1 | 0 |
| 3 | 0 | 1 |
| 4, 5 | 1 | 1 |
| 6~11 | -1 | -1 |

`num_sw_branch_each_span`은 `{2, 2, 0, 0}`이다.

`[결정 대기 4]` 분기 줄이 없는 파일을 이 파서에 넣으면 분기 줄이 restart 줄부터 읽혀 이후 헤더가 12토큰 밀린다. 3.4의 대조 오류와 6.2의 오류 (1)이 나오고 `MN_num`이 11로 줄어든 채 완주한다. 변환 절차와 변환된 파일의 위치는 결정 4에 따른다. 구 형태 파일도 같은 이유로 이 파서를 통과하지 못하므로 하위 호환은 없다.

### 3.3 row의 마지막 칸 (105행, 114행, 178행)

수정 전:

```cpp
    LLR_info->floor_flag = new int[LLR_info->num_row];
```

```cpp
        fscanf(matrix_in, "%d", &c); LLR_info->floor_flag[i] = c;
```

```cpp
            fprintf(fp_auto_result, "%2d ", LLR_info->floor_flag[i]);
```

수정 후:

```cpp
    LLR_info->sw_branch_idx = new int[LLR_info->num_row];
```

```cpp
        fscanf(matrix_in, "%d", &c); LLR_info->sw_branch_idx[i] = c;
```

```cpp
            fprintf(fp_auto_result, "%2d ", LLR_info->sw_branch_idx[i]);
```

### 3.4 헤더 검사 (115행 뒤에 추가)

수정 전: 없음

수정 후:

```cpp
    /* 헤더 값의 범위 */
    if (LLR_info->num_group <= 0 || LLR_info->num_row <= 0) {
        printf("[Error] num_group %d, num_row %d\n", LLR_info->num_group, LLR_info->num_row);
        err = TRUE;
    }
    for (i = 0; i < LLR_info->num_group; i++) {
        if (LLR_info->num_set_each_group[i] <= 0) {
            printf("[Error] num_set_each_group[%d] = %d\n", i, LLR_info->num_set_each_group[i]);
            err = TRUE;
        }
    }
    /* 헤더의 분기 index와 각 row의 분기 index가 어긋나면 오류 */
    {
        int row_base = 0;
        for (i = 0; i < LLR_info->num_group; i++) {
            for (int r = 0; r < LLR_info->num_set_each_group[i]; r++) {
                if (LLR_info->sw_branch_idx[row_base + r] != LLR_info->sw_branch_idx_each_group[i]) {
                    printf("[Error] SW branch mismatch @group%d row%d: header %d, row %d\n",
                        i, r, LLR_info->sw_branch_idx_each_group[i],
                        LLR_info->sw_branch_idx[row_base + r]);
                    err = TRUE;
                }
            }
            row_base += LLR_info->num_set_each_group[i];
        }
    }
    /* 같은 후보 집합 안에서 iteration 범위가 겹치면 오류.
       후보 집합은 같은 구간의 같은 분기 그룹과 분기 없는 그룹을 합친 것이다 */
    {
        int* g_start = new int[LLR_info->num_group];
        int* g_end = new int[LLR_info->num_group];
        int row_base = 0;
        for (i = 0; i < LLR_info->num_group; i++) {
            g_start[i] = LLR_info->iter_start[row_base];
            g_end[i] = LLR_info->iter_end[row_base + LLR_info->num_set_each_group[i] - 1];
            row_base += LLR_info->num_set_each_group[i];
        }
        for (i = 0; i < LLR_info->num_group; i++) {
            for (int j = i + 1; j < LLR_info->num_group; j++) {
                int bi = LLR_info->sw_branch_idx_each_group[i];
                int bj = LLR_info->sw_branch_idx_each_group[j];
                int same_set = (bi == SW_BRANCH_NONE) || (bj == SW_BRANCH_NONE) ||
                    ((LLR_info->sw_span_idx_each_group[i] == LLR_info->sw_span_idx_each_group[j]) && (bi == bj));
                if (same_set && (g_start[i] <= g_end[j]) && (g_start[j] <= g_end[i])) {
                    printf("[Error] iteration overlap @group%d(%d~%d), group%d(%d~%d)\n",
                        i, g_start[i], g_end[i], j, g_start[j], g_end[j]);
                    err = TRUE;
                }
            }
        }
        delete[] g_start;
        delete[] g_end;
    }
    if (err) {
        /* [결정 대기 6] 여기서 실행을 멈춘다. return err 사슬 또는 exit(1) */
    }
```

- ㉮ `err`(56행)는 140행에서 대입만 되고 읽는 곳이 없으며 이 함수는 void다. 검사가 실제로 실행을 멈추려면 결정 6의 수단이 있어야 한다. 그 수단이 없으면 검사는 출력만 남기고 복호가 이어진다
- ㉯ `printf`는 DAO가 읽는 어떤 파일에도 남지 않는다. DAO는 EXE의 stdout을 받지 않고 종료 코드만 본다(`DAO_Main.py:7937`의 `check=True`). 0이 아닌 종료 코드는 `CalledProcessError`로 올라와 DAO 전체를 끝내므로 결정 6의 수단은 종료 코드를 바꾸는 것이어야 한다
- ㉰ iteration 겹침 검사는 6.1의 전제("후보 집합 안에서 iteration 범위가 겹치지 않는다")를 파서가 지키게 한다. 이 검사는 `iter_start`, `iter_end`가 채워진 뒤에 와야 하므로 3.2 자리가 아니라 여기에 둔다
- ㉱ 변환한 `LLR_MATRIX_1.txt`는 모든 검사를 오탐 없이 통과한다 (row 마지막 칸이 그룹 안에서 균일하고 후보 집합 안 겹침이 없다)

### 3.5 최대 iteration 계산 (116-123행)과 HD 보정 (124-131행)

수정 전:

```cpp
    m_param_dec->MN_num = LLR_info->iter_end[LLR_info->num_row - 1];
    m_param_dec->MN = new int[m_param_dec->MN_num];
    for (i = 0; i < m_param_dec->MN_num; i++) {
        if (i == m_param_dec->MN_num - 1)
            m_param_dec->MN[i] = LLR_info->iter_end[LLR_info->num_row - 1];
        else
            m_param_dec->MN[i] = i;
    }
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_SSD == m_param_dec->init_n)) {
        for (i = 0; i < m_param_dec->MN_num; i++) {
            m_param_dec->MN[i] -= ITER_MAX_HBF;
        }
        if (m_param_dec->MN_num > 1) {
            m_param_dec->MN[0] = ITER_MAX_HBF;
        }
    }
```

수정 후:

```cpp
    int max_iter_end = 0;
    for (i = 0; i < LLR_info->num_row; i++) {
        if (LLR_info->iter_end[i] > max_iter_end) {
            max_iter_end = LLR_info->iter_end[i];
        }
    }
    if (max_iter_end <= 0) {
        printf("[Error] max iter_end %d\n", max_iter_end);
        err = TRUE;
    }
    m_param_dec->MN_num = max_iter_end;
    m_param_dec->MN = new int[m_param_dec->MN_num];
    for (i = 0; i < m_param_dec->MN_num; i++) {
        if (i == m_param_dec->MN_num - 1)
            m_param_dec->MN[i] = max_iter_end;
        else
            m_param_dec->MN[i] = i;
    }
    if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
        for (i = 0; i < m_param_dec->MN_num; i++) {
            m_param_dec->MN[i] -= ITER_MAX_HBF;
        }
        if (m_param_dec->MN_num > 1) {
            m_param_dec->MN[0] = ITER_MAX_HBF;
        }
    }
```

- ㉮ 분기가 있으면 마지막 row가 최대 iteration을 갖는다는 보장이 없으므로 전체 `iter_end`의 최댓값을 쓴다. 3.2를 넣고 이 수정을 함께 넣지 않으면 분기 줄이 없는 파일에서 `MN_num`이 -1이 되어 `new int[-1]`로 죽는다
- ㉯ HD 보정 블록(124-131행)은 살린다. 이 블록이 없으면 BF 미진입 프레임이 파일의 마지막 iteration을 4만큼 넘겨 돌아 6.2의 오류 (1)로 빠진다
- ㉰ **적용 전 확인 전제**: 저장소 사본의 124행 둘째 항은 `MODE_DEC_1_SSD`이고 이 이름은 어디에도 정의가 없다(정의된 이름은 `common.h:78`의 `MODE_DEC_1_5SD`). 외부 소스에서 이 줄을 확인하고 위와 같이 고친다. 1.5SD도 이 보정을 받아야 `Select_BF`의 +4와 합쳐 비AUTO와 같은 mn 5~124를 돈다. 받지 않으면 iteration 125~128을 돌며 매 iteration 오류를 찍고 row 0으로 복호한다

`ITER_MAX_HBF`가 4일 때(1.2장 적용 뒤) 변환한 `LLR_MATRIX_1.txt`로 계산한 결과:

| 항목 | 값 |
|------|-----|
| `MN_num` | 124 |
| `MN[]` | `[4, -3, -2, -1, 0, 1, ..., 118, 120]` |
| 루프 상한 `MN[MN_num-1]` | 120 |
| BF 진입 프레임의 mn | 1~120 |
| BF 미진입 프레임의 mn | 5~124 (`Select_BF`가 4를 더한다) |
| 실행 iteration | 두 프레임 종류 모두 120회 (`ITER_MAX_HBF`가 0일 때는 124회) |

`MN[]`의 중간 원소는 결과 파일의 iteration별 FER 열 문턱(`ecc_top.cpp:877-879`)과 머리글(`ecc_top.cpp:2052-2056`)에만 쓰인다. 음수 원소 때문에 열 1~4가 1.0으로 고정되고 머리글에 음수가 찍히지만, 이 파일(`Ref_C_result_*.txt`)은 DAO가 읽지 않고 지운다. DAO의 판정용 FER은 `fr[MN_num-1]`이라 `MN[]`과 무관하다. `avg_iteration`은 `iter_num -= ITER_MAX_HBF`(`decoder.cpp:1973-1979`)를 거치므로 절대 척도가 바뀌지만 같은 빌드에서 비교되므로 순위는 유지된다.

`[결정 대기 5]` DAO의 HBF 최적화 모드는 매트릭스 최대 iteration을 4 이하로 강제한다(`DAO_LLR_MATRIX.py:442-447`, `DAO_Config.py:372`). 그 파일에서는 보정으로 루프 상한이 0 이하가 되어 복호가 한 번도 일어나지 않는다. 보정에 하한을 둘지(`max_iter_end <= ITER_MAX_HBF`이면 보정 생략), `MN_num`까지 함께 줄이는 보정식으로 바꿀지는 결정 5에 따른다.

### 3.6 소멸자 (10-26행)

수정 전:

```cpp
    delete[] m_param_LLR.num_set_each_group;
    delete[] m_param_LLR.type_each_group;
```

수정 후:

```cpp
    delete[] m_param_LLR.num_set_each_group;
    delete[] m_param_LLR.type_each_group;
    delete[] m_param_LLR.sw_branch_idx_each_group;
    delete[] m_param_LLR.sw_span_idx_each_group;
    delete[] m_param_LLR.sw_branch_idx;
```

### 3.7 MPI 전파 (38-44행)

수정 전:

```cpp
#if defined(__RUN_MPI__)
    for (int i = 0; i < m_param_LLR.num_row; i++) {
        MPI_Barrier(MPI_COMM_WORLD);
        MPI_Bcast(&m_param_LLR.LLR_MATRIX[i][0], m_param_LLR.num_col, MPI_INT, 0, MPI_COMM_WORLD);
    }
    MPI_Bcast(&m_param_LLR.CSW_thr[0], m_param_LLR.num_row, MPI_INT, 0, MPI_COMM_WORLD);
#endif
```

수정 후: 그대로 둔다.

- ㉮ AUTO 빌드에서는 `__RUN_MPI__`가 정의되지 않는다. `mode.h:21-25`가 `__AUTO_LLR_OPT__`를 정의한 바로 다음 줄에서 `#if !defined(__AUTO_LLR_OPT__)`로 이 스위치를 감싸므로 위 블록은 컴파일되지 않는다
- ㉯ 각 rank가 파일을 따로 읽는다. `Run_Local_Opt`(27-35행)에 rank 조건이 없고 `fopen`(60행)이 rank와 무관하다. DAO의 병렬화는 Python 계층(mpi4py)에서 rank마다 단일 프로세스 EXE 하나를 부르는 방식이다
- ㉰ 따라서 새 배열을 뿌릴 필요가 없다

---

<a id="ch4"></a>

## 4. 문턱 설정: decoder.cpp `Init_Dec_Option`

### 4.1 459-493행

수정 전:

```cpp
    switch (m_ecc_info->matrix_sel) {
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: {
        syn_th_BF0 = SW_TH_BF0_512B_TLC_OFF;
        syn_th_BF1 = SW_TH_BF1_512B_TLC_OFF;
        break;
    }
    default: { syn_th_BF = SW_TH_BF_DEFAULT; break; }
    }
    /**************************************/
    // 5_8 Set mode 진입 판단 SW threshold
    switch (m_ecc_info->matrix_sel) {
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_512B_TLC_OFF; break; }
    default: { syn_th_5_8_Set_0 = SW_TH_5_8_SET0_DEFAULT; break; }
    }
    switch (m_ecc_info->matrix_sel) {
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_512B_TLC_OFF; break; }
    default: { syn_th_5_8_Set_1 = SW_TH_5_8_SET1_DEFAULT; break; }
    }
```

수정 후:

```cpp
    /* BF 진입 문턱 */
    switch (m_ecc_info->matrix_sel) {
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: { syn_th_BF0 = SW_TH_BF0_512B_TLC_OFF; break; }
    default: { syn_th_BF0 = SW_TH_BF_DEFAULT; break; }
    }
    /**************************************/
    /* 구간별 SW 분기 문턱.
       span 0 = iteration 1~4, span 1 = iteration 5~8 [결정 대기 2].
       배열에 넣는 값은 오름차순이어야 하고, 분기가 n개면 문턱은 n-1개다. */
    for (i = 0; i < MAX_SW_SPAN; i++) {
        num_sw_branch[i] = 1;
        for (int j = 0; j < MAX_SW_BRANCH - 1; j++) {
            syn_th_sw_branch[i][j] = 0;
        }
    }
    switch (m_ecc_info->matrix_sel) {
    case LAYOUT_PRIME_512B_TLC_VSS_OFF: {
        num_sw_branch[0] = 2;
        syn_th_sw_branch[0][0] = SW_TH_BF1_512B_TLC_OFF;    /* [결정 대기 3] */
        num_sw_branch[1] = 2;
        syn_th_sw_branch[1][0] = SW_TH_5_8_SET0_512B_TLC_OFF;
        break;
    }
    default: {
        num_sw_branch[0] = 1;
        num_sw_branch[1] = 2;
        syn_th_sw_branch[1][0] = SW_TH_5_8_SET0_DEFAULT;
        break;
    }
    }
    /* 파일의 구간별 분기 개수, 문턱의 개수와 순서를 대조한다 */
    if (m_param_LLR != NULL) {
        int mismatch = FALSE;
        for (i = 0; i < m_param_LLR->num_sw_span; i++) {
            if (m_param_LLR->num_sw_branch_each_span[i] != num_sw_branch[i]) {
                printf("[Error] SW branch count @span%d: file %d, code %d\n",
                    i, m_param_LLR->num_sw_branch_each_span[i], num_sw_branch[i]);
                mismatch = TRUE;
            }
            for (int j = 0; j < num_sw_branch[i] - 1; j++) {
                if (syn_th_sw_branch[i][j] <= 0 ||
                    (j > 0 && syn_th_sw_branch[i][j] <= syn_th_sw_branch[i][j - 1])) {
                    printf("[Error] SW threshold @span%d[%d] = %d is not positive ascending\n",
                        i, j, syn_th_sw_branch[i][j]);
                    mismatch = TRUE;
                }
            }
        }
        if (mismatch) {
            /* [결정 대기 6] 여기서 실행을 멈춘다 */
        }
    }
```

바뀐 점:

- ㉮ default 갈래는 `syn_th_BF0`을 `SW_TH_BF_DEFAULT`(630)로 채운다. 수정 전 default 갈래는 읽히지 않는 `syn_th_BF`에 넣고 `syn_th_BF0`은 채우지 않아, `LAYOUT_PRIME_512B_TLC_VSS_OFF`가 아닌 layout에서 BF 진입 판정이 미정의 값에 기댔다. 동작 변경이며 등급은 Review다. 전제 ㉰(값은 기존 상수에서)의 예외다
- ㉯ 대조 검사는 `Read_LLR_info_Auto`(`local_opt.cpp:46`)가 `Init_ECC_Top`(`ecc_top.cpp:229`)보다 먼저 불려 이 시점에 `m_param_LLR`이 채워져 있으므로 여기서 할 수 있다. 비AUTO 빌드는 2.5에 따라 이 포인터가 NULL이라 건너뛴다. 이 함수는 void이므로 멈추는 수단은 결정 6과 같이 정한다
- ㉰ 대조가 없으면 default 갈래(`num_sw_branch[0] = 1`)에 변환한 `LLR_MATRIX_1.txt`(구간 0에 분기 2개)를 넣었을 때 그룹 2가 어떤 프레임에서도 선택되지 않고 오류도 나지 않는다. DAO는 `matrix_sel`을 1로 고정해 넘기므로(`DAO_Config.py:170`) 이 갈래는 사람이 다른 `matrix_sel`을 손으로 넣을 때 도달한다

`[결정 대기 8]` 활성 상수는 `SW_TH_5_8_SET0_512B_TLC_OFF`(1100)가 `SW_TH_5_8_SET1_512B_TLC_OFF`(950)보다 크고 default도 960 > 950이다. `SET1` 계열은 그대로 `syn_th_sw_branch[1][1]`에 넣을 수 없다. 구간 0의 문턱 상수는 하나뿐이다. 분기를 셋 이상 두려면 문턱을 파일이나 실행 인자로 받는 것(상위 문서 7장 ㉯)이 전제 조건이다.

---

<a id="ch5"></a>

## 5. 분기 결정: decoder.cpp `Select_BF`

### 5.1 2082-2130행

수정 전:

```cpp
void Decoder::Select_BF()
{
#if defined (__AUTO_LLR_OPT__)
    flag_BF_on = FLAG_LOW;
#else
    if (MODE_DEC_HD == m_param_dec->init_n) {
        if ((MODE_BF_ON == m_param_dec->BF_mode) && (syn_weight < syn_th_BF0)) {
            flag_BF_on = FLAG_HIGH;
            flag_HD_1_4_Set = FLAG_HD_1_4_SET_TYPE_0;
            flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0;
#if defined(__CORNER_CHECKER__)
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0);
#endif
        }
        else {
            mn = mn + ITER_MAX_HBF;
            MN = MN + ITER_MAX_HBF;
            if (syn_weight < syn_th_5_8_Set_0) {
                flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0;
                ...
            }
            else{
                flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_1;
                ...
            }
        }
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        mn = mn + ITER_MAX_HBF;
        MN = MN + ITER_MAX_HBF;
        if (psyn_weight < syn_th_5_8_Set_0) {
            flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0;
            ...
        }
        else {
            flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_1;
            ...
        }
    }
#endif //__AUTO_LLR_OPT__
}
```

수정 후:

```cpp
//=================================================
// SW 문턱으로 그 구간의 분기 index를 고른다.
// 문턱은 오름차순이고, 어느 문턱에도 못 미치면 마지막 분기다.
//=================================================
int Decoder::Select_SW_Branch(int span_idx, int weight)
{
    for (int i = 0; i < num_sw_branch[span_idx] - 1; i++) {
        if (weight < syn_th_sw_branch[span_idx][i]) {
            return i;
        }
    }
    return num_sw_branch[span_idx] - 1;
}
//=================================================
// BF 진입 여부와 구간별 SW 분기 판단
//=================================================
void Decoder::Select_BF()
{
    for (int i = 0; i < MAX_SW_SPAN; i++) {
        cur_sw_branch_idx[i] = 0;
    }
    if (MODE_DEC_HD == m_param_dec->init_n) {
        if ((MODE_BF_ON == m_param_dec->BF_mode) && (syn_weight < syn_th_BF0)) {
            flag_BF_on = FLAG_HIGH;
            /* iteration 1~8을 모두 돈다. 두 구간의 분기를 각각 고른다 */
            cur_sw_branch_idx[0] = Select_SW_Branch(0, syn_weight);
            cur_sw_branch_idx[1] = Select_SW_Branch(1, syn_weight);
        }
        else {
            flag_BF_on = FLAG_LOW;
            mn = mn + ITER_MAX_HBF;
            MN = MN + ITER_MAX_HBF;
            /* ITER_MAX_HBF가 4이면 iteration 1~4를 건너뛰므로 span 0은 쓰이지 않는다 [결정 대기 2] */
            cur_sw_branch_idx[1] = Select_SW_Branch(1, syn_weight);
        }
#if defined(__CORNER_CHECKER__)
        if (cur_sw_branch_idx[1] < 3) {
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]);
        }
#endif
    }
    else if (MODE_DEC_1_5SD == m_param_dec->init_n) {
        flag_BF_on = FLAG_LOW;
        mn = mn + ITER_MAX_HBF;
        MN = MN + ITER_MAX_HBF;
        cur_sw_branch_idx[1] = Select_SW_Branch(1, psyn_weight);
#if defined(__CORNER_CHECKER__)
        if (cur_sw_branch_idx[1] < 3) {
            m_corner->Event_Flag(CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]);
        }
#endif
    }
    else {
        flag_BF_on = FLAG_LOW;      /* 2SD와 3SD. 분기는 0으로 고정된다 [결정 대기 7] */
    }
}
```

바뀐 점:

- ㉮ `__AUTO_LLR_OPT__` 갈래를 없앴다. 최적화 모드에서도 BF와 분기가 살아난다
- ㉯ BF에 진입할 때 iteration 1~4 구간의 분기를 문턱으로 고른다 `[결정 대기 3]`. 수정 전 코드는 `FLAG_HD_1_4_SET_TYPE_0`으로 고정했고 `TYPE_1`을 고르는 코드가 없었다. 변환한 `LLR_MATRIX_1.txt`는 이 구간에 분기 둘을 둔다. 동작이 갈리는 범위는 `matrix_sel` 1에서 syn_weight 130 이상 680 미만뿐이며 그때 iteration 1~4에 그룹 2가 쓰인다
- ㉰ span 1의 동작은 수정 전과 같다. BF 진입 조건(680)이 구간 1 문턱(1100)보다 작아 진입 프레임은 항상 분기 0이고, 미진입 프레임의 판정은 기존 `syn_weight < syn_th_5_8_Set_0`과 같은 결과다. 1.5SD도 `psyn_weight`로 같은 판정을 한다
- ㉱ Corner 이벤트는 수정 전과 같이 HD와 1.5SD 갈래 안에서만 찍는다. `IDX_FLAG_HD_5_8_SET_TYPE_0/1/2`가 [corner.h:79-81](../../../../0_LDPC_original/src/corner.h#L79-L81)에 이어진 세 값이고 그 다음이 `IDX_FLAG_HD_FLOOR_TYPE_0`이므로 index 3 이상은 찍지 않는다. `__CORNER_CHECKER__`는 `mode.h:75`에서 꺼져 있다
- ㉲ 2SD와 3SD는 `cur_sw_branch_idx[]`가 모두 0이라 분기 0 그룹만 후보가 된다. 수정 전 AUTO 갈래는 분기를 보지 않고 iteration 범위만으로 골라 뒤쪽 그룹(분기 1)을 잡았으므로 이 모드의 결과가 바뀐다. DAO가 `init_n` 2와 3을 쓰는 설정이 있으므로(`DAO_Config.py`) 적용 범위는 결정 7에 따른다
- ㉳ `common.h:717-725`의 `FLAG_HD_1_4_SET_TYPE_*`, `FLAG_HD_5_8_SET_TYPE_*` enum은 쓰는 곳이 없어지므로 지운다. 지우는 시점은 9장 2단계다

---

<a id="ch6"></a>

## 6. 그룹 선택: decoder.cpp `Get_Cur_LLR_Idx_FILE`

### 6.1 6973-7047행: 후보 그룹 찾기

수정 전:

```cpp
int Decoder::Get_Cur_LLR_Idx_FILE(int iter) {
	int table_row_idx = 0;
	int start_idx = 0;
	int end_idx = 0;
	int selected_group = -1;
	int i, g;
	int num_candidate;
	if (m_param_dec->init_n == MODE_DEC_HD && iter > 0) {
	    Adjust_HD_Floor_Type(Floor_Detect_CSW_TH1, Floor_Detect_CSW_TH2);
	}
#if defined (__AUTO_LLR_OPT__)
	for (g = m_param_LLR->num_group - 1; g >= 0; g--) {
	    start_idx = 0;
	    for (int gg = 0; gg < g; gg++) {
	        start_idx += m_param_LLR->num_set_each_group[gg];
	    }
	    end_idx = 0;
	    for (int gg = 0; gg <= g; gg++) {
	        end_idx += m_param_LLR->num_set_each_group[gg];
	    }
	    end_idx = end_idx - 1;
	    if ((iter >= m_param_LLR->iter_start[start_idx]) && (iter <= m_param_LLR->iter_end[end_idx])) {
	        selected_group = g;
	        break;
	    }
	}
#else
	if ((m_param_dec->init_n == MODE_DEC_HD) && (iter == 1)) {
	    if (FLAG_HD_1_4_SET_TYPE_0 == flag_HD_1_4_Set)
	        selected_group = 0;
	}
	else if ((m_param_dec->init_n == MODE_DEC_HD) && (iter >= 2) && (iter <= 4)) {
	    if (FLAG_HD_1_4_SET_TYPE_0 == flag_HD_1_4_Set)
	        selected_group = 1;
	}
	else if ((m_param_dec->init_n == MODE_DEC_HD) && (iter == 5)) {
	    if (FLAG_HD_5_8_SET_TYPE_0 == flag_HD_5_8_Set)
	        selected_group = 2;
	    else
	        selected_group = 4;
	}
	else if ((m_param_dec->init_n == MODE_DEC_HD) && (iter >= 6) && (iter <= 8)) {
	    if (FLAG_HD_5_8_SET_TYPE_0 == flag_HD_5_8_Set)
	        selected_group = 3;
	    else
	        selected_group = 5;
	}
	else {
	    for (g = m_param_LLR->num_group - 1; g >= 0; g--) {
	        ... (위와 같은 iteration 범위 탐색) ...
	    }
	}
	start_idx = 0;
	for (int gg = 0; gg < selected_group; gg++) {
	    start_idx += m_param_LLR->num_set_each_group[gg];
	}
	end_idx = 0;
	for (int gg = 0; gg <= selected_group; gg++) {
	    end_idx += m_param_LLR->num_set_each_group[gg];
	}
	end_idx = end_idx - 1;
#endif // __AUTO_LLR_OPT__
```

수정 후:

```cpp
int Decoder::Get_Cur_LLR_Idx_FILE(int iter) {
	int table_row_idx = -1;
	int start_idx = 0;
	int end_idx = 0;
	int selected_group = -1;
	int i, g;
	int num_candidate;
	if (m_param_dec->init_n == MODE_DEC_HD && iter > 0) {
	    Adjust_HD_Floor_Type(Floor_Detect_CSW_TH1, Floor_Detect_CSW_TH2);
	}
	for (g = m_param_LLR->num_group - 1; g >= 0; g--) {
	    int group_branch = m_param_LLR->sw_branch_idx_each_group[g];
	    /* 분기가 걸린 그룹은 이번 프레임이 그 분기를 탔을 때만 후보다 */
	    if (group_branch != SW_BRANCH_NONE) {
	        int span = m_param_LLR->sw_span_idx_each_group[g];
	        if (span < 0 || span >= MAX_SW_SPAN) {
	            continue;
	        }
	        if (group_branch != cur_sw_branch_idx[span]) {
	            continue;
	        }
	    }
	    start_idx = 0;
	    for (int gg = 0; gg < g; gg++) {
	        start_idx += m_param_LLR->num_set_each_group[gg];
	    }
	    end_idx = 0;
	    for (int gg = 0; gg <= g; gg++) {
	        end_idx += m_param_LLR->num_set_each_group[gg];
	    }
	    end_idx = end_idx - 1;
	    if ((iter >= m_param_LLR->iter_start[start_idx]) && (iter <= m_param_LLR->iter_end[end_idx])) {
	        selected_group = g;
	        break;
	    }
	}
```

바뀐 점:

- ㉮ `__AUTO_LLR_OPT__` 갈래를 없애고 한 갈래로 합쳤다. 하드코딩된 그룹 번호가 사라진다. 이 함수를 부르는 곳은 `decoder.cpp:1138` 하나뿐이고 그 줄이 AUTO 갈래 안이므로 지워지는 비AUTO 갈래는 어느 빌드에서도 실행되지 않던 코드다. `decoder.cpp:1137-1141`의 갈래는 그대로 둔다 (비AUTO는 항상 0을 돌려주는 `Get_VNU_Table_Idx`를 계속 쓴다) `[결정 대기 1]`
- ㉯ 분기가 맞지 않는 그룹은 후보에서 뺀다. 서로 다른 분기 사이에서는 훑는 순서가 결과를 정하지 않는다. 같은 후보 집합(현재 분기의 그룹과 분기 없는 그룹) 안에서 iteration 범위가 겹치면 여전히 뒤쪽 그룹이 이기므로 3.4의 겹침 검사가 이 전제를 지킨다. 분기 index가 `num_sw_branch[span]` 이상인 그룹은 위치와 무관하게 항상 건너뛰어진다
- ㉰ `table_row_idx` 초기값을 0에서 -1로 바꿨다. 아래 검사가 실제로 작동하게 된다
- ㉱ `span` 범위 방어는 3.2의 검사가 지켜지면 걸리지 않는다. 걸리면 그 그룹을 건너뛴다

변환한 `LLR_MATRIX_1.txt`로 확인한 결과:

| iter | 분기 | 고르는 그룹 | 근거 |
|------|------|------------|------|
| 3 | span0 = 0 | 1 | g5, g4, g3은 분기 1 또는 iteration 밖, g2는 분기 1이라 건너뜀, g1이 2~4 |
| 3 | span0 = 1 | 2 | g2가 분기 1이고 1~4를 덮음 |
| 6 | span1 = 0 | 3 | g5, g4는 분기 1이라 건너뜀, g3이 5~8 |
| 6 | span1 = 1 | 5 | g5가 분기 1이고 6~8을 덮음 |
| 20 | 없음 | 6 | 분기 없는 그룹이라 조건을 그냥 지남 |

### 6.2 7048-7073행: 오류 검사

수정 전:

```cpp
	if (selected_group == -1 || selected_group >= m_param_LLR->num_group) {
	    printf("[Error] @Cur_LLR_IDX (1): iter%d, state%d, CSW%d\n", iter, state_hd_error_floor_set, prev_CSW);
	}
	if (GROUP_TYPE_ITER == m_param_LLR->type_each_group[selected_group]) {
	    for (i = start_idx; i <= end_idx; i++) {
	        if ((iter >= m_param_LLR->iter_start[i]) && (iter <= m_param_LLR->iter_end[i])) {
	            table_row_idx = i;
	            break;
	        }
	    }
	}
	else if (GROUP_TYPE_CSW == m_param_LLR->type_each_group[selected_group]) {
	    table_row_idx = start_idx;
	    num_candidate = m_param_LLR->num_set_each_group[selected_group];
	    for (i = num_candidate - 1; i > 0; i--) {
	        if (prev_CSW <= m_param_LLR->CSW_thr[start_idx + i]) {
	            table_row_idx = start_idx + i;
	            break;
	        }
	    }
	}
	if (table_row_idx < 0 || table_row_idx >= m_param_LLR->num_row) {
	    printf("[Error] @Cur_LLR_IDX (2): iter%d, state%d, CSW%d, table_row%d\n", iter, state_hd_error_floor_set, prev_CSW, table_row_idx);
	}
	return table_row_idx;
}
```

수정 후:

```cpp
	if (selected_group == -1 || selected_group >= m_param_LLR->num_group) {
	    printf("[Error] @Cur_LLR_IDX (1): iter%d, branch%d/%d, state%d, CSW%d\n",
	        iter, cur_sw_branch_idx[0], cur_sw_branch_idx[1], state_hd_error_floor_set, prev_CSW);
	    return 0;
	}
	if (GROUP_TYPE_ITER == m_param_LLR->type_each_group[selected_group]) {
	    for (i = start_idx; i <= end_idx; i++) {
	        if ((iter >= m_param_LLR->iter_start[i]) && (iter <= m_param_LLR->iter_end[i])) {
	            table_row_idx = i;
	            break;
	        }
	    }
	}
	else if (GROUP_TYPE_CSW == m_param_LLR->type_each_group[selected_group]) {
	    table_row_idx = start_idx;
	    num_candidate = m_param_LLR->num_set_each_group[selected_group];
	    for (i = num_candidate - 1; i > 0; i--) {
	        if (prev_CSW <= m_param_LLR->CSW_thr[start_idx + i]) {
	            table_row_idx = start_idx + i;
	            break;
	        }
	    }
	}
	else {
	    printf("[Error] @Cur_LLR_IDX (3): unknown group type %d @group%d\n",
	        m_param_LLR->type_each_group[selected_group], selected_group);
	}
	if (table_row_idx < 0 || table_row_idx >= m_param_LLR->num_row) {
	    printf("[Error] @Cur_LLR_IDX (2): iter%d, state%d, CSW%d, table_row%d\n", iter, state_hd_error_floor_set, prev_CSW, table_row_idx);
	    return 0;
	}
	return table_row_idx;
}
```

바뀐 점:

- ㉮ `selected_group == -1`일 때 그대로 진행해 `type_each_group[-1]`을 읽던 것을 막는다
- ㉯ 그룹 타입이 둘 중 어느 것도 아니면 오류 (3)으로 잡는다. 이 오류는 `type_each_group`이 0도 1도 아닌 그룹이 후보로 뽑혔을 때만 나온다. 분기 줄이 없는 파일을 넣으면 파싱이 밀려 3.4의 대조 오류와 오류 (1)이 나오고, 이 오류는 나오지 않는다
- ㉰ 오류일 때 0을 돌려준다. 호출자(`decoder.cpp:1136-1142`)는 반환값을 검사하지 않으므로 출력만 남고 row 0으로 복호가 이어진다. 정상 프레임의 iteration 1 row도 0이라 값만으로는 구별되지 않는다. `num_row`가 1 이상이어야 row 0이 존재하며 그 검사는 3.4에 있다

---

<a id="ch7"></a>

## 7. 1bit precision 조건: `iter <= 4` 상수 되돌리기

`ITER_MAX_HBF`를 4로 되돌리면(1.2장) 아래 네 곳의 갈래가 필요 없어진다.

### 7.1 decoder.cpp 2373-2379행

수정 전:

```cpp
        if ((TRUE == flag_BF_on) &&
#ifdef __AUTO_LLR_OPT__
            (iter <= 4) &&
#else
            (iter <= ITER_MAX_HBF) &&
#endif
            (v_deg > DV_5)) { //Dv > 5 인 column은 1bit precision -> mag는 4로 고정
```

수정 후:

```cpp
        if ((TRUE == flag_BF_on) &&
            (iter <= ITER_MAX_HBF) &&
            (v_deg > DV_5)) { //Dv > 5 인 column은 1bit precision -> mag는 4로 고정
```

### 7.2 decoder.cpp 2796-2802행

수정 전:

```cpp
        if ((TRUE == flag_BF_on)
#ifdef __AUTO_LLR_OPT__
            && (iter <= 4)
#else
            && (iter <= ITER_MAX_HBF)
#endif
            && (v_deg > DV_5)) { //1bit mode
```

수정 후:

```cpp
        if ((TRUE == flag_BF_on)
            && (iter <= ITER_MAX_HBF)
            && (v_deg > DV_5)) { //1bit mode
```

### 7.3 decoder.cpp 4055-4059행과 4274-4278행

수정 전 (두 곳이 같다):

```cpp
#ifdef __AUTO_LLR_OPT__
            if ((TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)) { //1bit precision
#else
            if ((TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)) { //1bit precision
#endif
```

수정 후:

```cpp
            if ((TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)) { //1bit precision
```

### 7.4 BF 구간에서 파일 row가 쓰이는 범위

BF 진입 프레임의 iteration 1~4에서도 파일 row는 읽힌다. `channel_llr = ch1`(`decoder.cpp:4019`)은 1bit 갈래 밖에 있어 모든 column에 적용된다. 차수가 5를 넘는 column은 1bit 갈래(`decoder.cpp:4056-4079`)를 타서 `th1`, `th2`, `th3`를 쓰지 않고, 차수가 5 이하인 column은 4bit 갈래에서 `th1~th7`을 쓴다. 변환한 `LLR_MATRIX_1.txt`의 분기 구간 row 14개에서 차수 11 그룹의 `th1~th3` 42개 칸은 복호 결과에 영향이 없다.

---

<a id="ch8"></a>

## 8. 초기화 시점

`[결정 대기 1]` 8.1과 8.2는 `Is_Iter_Type_Edge_Clear`와 `Is_Iter_Type_Init`의 비AUTO 갈래를 지우는 장이다. 두 함수는 컴파일 스위치 없이 매 iteration 불리고, 비AUTO 빌드에서는 `m_param_LLR`이 세워지지 않으므로(2.5) 갈래를 지우면 `Is_Iter_Type_Edge_Clear`가 미초기화 포인터를 읽는다. 비AUTO 2SD와 3SD의 restart 지점 8개(`common.h:679-686`)와 TV Gen 빌드의 `matrix_sel` 가드도 함께 사라진다. 8.1의 수정 후 코드는 AUTO 갈래와 한 줄씩 같아 AUTO 빌드에는 기여가 없다. 결정 1의 권고는 이 두 장을 빼고 갈래를 유지하는 것이다.

### 8.1 decoder.cpp 6538-6598행: `Is_Iter_Type_Edge_Clear`

수정 전:

```cpp
int Decoder::Is_Iter_Type_Edge_Clear(int iter)
{
	int bClear = FALSE;
#if defined(__AUTO_LLR_OPT__)
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
		if (iter == 0 ||
			iter == 1 ||
			iter == ITER_MAX_HBF + 1) {
			bClear = TRUE;
		}
		else {
			for (int i = 0; i < m_param_LLR->restart_num; i++) {
				if (iter == m_param_LLR->restart_iter[i])
					bClear = TRUE;
			}
		}
	}
	else {
	    ... (iter == 0과 restart를 보는 갈래) ...
	}
#else
	... (matrix_sel별 하드코딩) ...
#endif
	return bClear;
}
```

수정 후 (결정 1이 "통일"일 때만): `#if defined(__AUTO_LLR_OPT__)` 갈래만 남긴다.

```cpp
int Decoder::Is_Iter_Type_Edge_Clear(int iter)
{
	int bClear = FALSE;
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
		if (iter == 0 ||
			iter == 1 ||
			iter == ITER_MAX_HBF + 1) {
			bClear = TRUE;
		}
		else {
			for (int i = 0; i < m_param_LLR->restart_num; i++) {
				if (iter == m_param_LLR->restart_iter[i])
					bClear = TRUE;
			}
		}
	}
	else {
		if (iter == 0) {
			bClear = TRUE;
		}
		else {
			for (int i = 0; i < m_param_LLR->restart_num; i++) {
				if (iter == m_param_LLR->restart_iter[i])
					bClear = TRUE;
			}
		}
	}
	return bClear;
}
```

`ITER_MAX_HBF`가 4이면 edge clear는 BF 진입 프레임에서 iteration 0, 1, 5 세 곳, 미진입 프레임에서 0, 5 두 곳에 일어난다. 이 조건은 `flag_BF_on`을 보지 않는다. 미진입 프레임은 mn 수열이 0, 5, 6, ...이라 1을 지나지 않는다.

파일의 `restart_iter`가 1 이상 4 이하이면 미진입 프레임만 그 restart를 놓친다. 변환한 `LLR_MATRIX_1.txt`는 `restart_num`이 0이고, 구 형태 파일은 `restart_iter` 2를 담고 있다. 파서에서 오류로 잡으면 실재하는 파일을 거부하므로 문서에 제약으로 적는다: restart 지점은 `ITER_MAX_HBF`보다 커야 한다.

### 8.2 decoder.cpp 6606-6676행: `Is_Iter_Type_Init` (`#if` 갈래 6609-6625)

수정 전:

```cpp
int Decoder::Is_Iter_Type_Init(int iter)
{
	int bInit = FALSE;
#if defined(__AUTO_LLR_OPT__)
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	    if (iter == 0) {
	        bInit = TRUE;
	    }
	}
	else {
	    if (iter == 0) {
	        bInit = TRUE;
	    }
	    else {
	        for (int i = 0; i < m_param_LLR->restart_num; i++) {
	            if (iter == m_param_LLR->restart_iter[i])
	                bInit = TRUE;
	        }
	    }
	}
#else
	... (matrix_sel별 하드코딩, 6627-6674) ...
#endif
	return bInit;
}
```

수정 후 (결정 1이 "통일"일 때만): `#if defined(__AUTO_LLR_OPT__)` 갈래만 남긴다. 조건은 그대로 둔다.

HD와 1.5SD에서 `iter == 0`만 보고 restart를 보지 않는 것은 의도다. 비AUTO 갈래도 두 모드에서 같은 조건이고, restart 시점의 레지스터 비우기는 `Clear_Edge_Restart`(`decoder.cpp:709-739`)가 따로 맡는다. `decoder.cpp:6604`의 주석 "HD는 Edge clear를 수행할때 초기화 과정이 필요없기에 mn==0에서만 초기화 작업 (Pre-update) 수행"이 이를 말한다.

### 8.3 decoder.cpp 1146-1156행: Preprocessing 시점

수정 전후 모두 그대로 둔다.

```cpp
#if defined (__RUN_PREPROCESSING__)
        if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
            if ((TRUE == flag_BF_on && mn == 1) ||
                (FALSE == flag_BF_on && mn == ITER_MAX_HBF + 1)) { //BF mode 진입하면 Iter 1전에 Preprocessing, 진입하지 않으면 Iter 5전
                Preprocessing();
```

`__RUN_PREPROCESSING__`은 `mode.h:63`에서 꺼져 있어 이 블록은 컴파일되지 않는다. 켜면 BF 진입 프레임은 mn 1에서, 미진입 프레임은 mn 5에서 한 번씩 돈다.

---

<a id="ch9"></a>

## 9. 적용 순서

지워지는 이름(`flag_HD_*_Set`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_*`, `floor_flag`)의 대체 코드가 2장, 3장, 4.1, 5장, 6장에 흩어져 있어 이 장들은 한 번에 넣어야 빌드된다. 나눠 넣으면 AUTO 빌드는 `local_opt.cpp` 3줄과 `decoder.cpp` 8줄에서, 비AUTO 빌드는 12줄이 더 깨진다.

- 1. **파일 준비** `[결정 대기 4]`. 세 벌이 필요하다.
     ㉮ 변환한 파일: 4장 ㉮ 형태로 분기 줄을 넣고 `type_each_group`을 1로 교정한 것.
     ㉯ 검증용 파일: ㉮와 같되 분기 줄을 모두 -1로 둔 것.
     ㉰ 옛 코드 비교용 파일: `type_each_group`만 1로 교정하고 분기 줄은 넣지 않은 것.
     `type_each_group` 교정이 필요한 이유는 6.1이 `table_row_idx` 초기값을 -1로 바꿔서, 0도 1도 아닌 type에서 옛 코드는 row 0을, 새 코드는 -1을 돌려주기 때문이다
- 2. **1.1, 2장, 3장, 4.1, 5장(enum 삭제 포함), 6장을 한 번에 넣는다.** 3.7은 수정이 없다. 1.2는 아직 넣지 않는다.
     검증: ㉯ 검증용 파일로 돌린 결과가 ㉰ 비교용 파일로 옛 코드를 돌린 결과와 같아야 한다. 분기 줄이 모두 -1이면 6.1의 분기 필터가 한 번도 걸리지 않아 두 루프의 순회가 같다. `ITER_MAX_HBF`는 아직 0이라 iteration 수열도 같다.
     3.4의 검사는 ㉮ 변환한 파일에서 오탐 없이 통과해야 한다
- 3. **㉮ 변환한 파일로 돌린다.** 분기가 실제로 갈리기 시작한다. 결과가 2단계와 달라야 정상이다.
     이 단계는 `ITER_MAX_HBF`가 0이라 BF 미진입 프레임도 iteration 1~4를 돌며 구간 0의 분기 0 row를 쓴다. 5.1의 "span 0은 쓰이지 않는다"는 4단계 이후에만 맞는다
- 4. **1.2, 7장, 8.3을 넣는다.** 8.1과 8.2는 결정 1에 따른다. BF가 살아나고 `local_opt.cpp:124-131`의 보정이 살아난다.
     기대 결과: 실행 iteration이 124회에서 120회로 줄고, BF 진입 프레임은 mn 1~120, 미진입 프레임은 mn 5~124를 돈다. 결과 파일의 iteration별 FER 열 1~4가 1.0으로 고정되고 머리글에 음수가 찍힌다(3.5장). `avg_iteration`의 절대 척도가 바뀐다. `decoder.cpp:2169`의 partial CRC 종료 제한이 mn 5에도 걸려 throughput 지표가 바뀐다
