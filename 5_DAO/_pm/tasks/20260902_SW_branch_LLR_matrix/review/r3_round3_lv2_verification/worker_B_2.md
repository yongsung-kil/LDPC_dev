# Round 3 팀 B(재탐색) 워커 2 결과

작성: 2026-09-03 01:43:54

배정 영역: ㉯ `MN[n]` 소비처 전수와 음수 값 동작, ㉲ BF 진입 프레임의 iteration 121~124 미도달 비대칭.

리뷰 대상: [20260902_SW_branch_LLR_matrix.md](../../20260902_SW_branch_LLR_matrix.md), [code_diff.md](../../code_diff.md).
"수정 후 코드"는 code_diff의 수정 후 블록을 그대로 적용한 상태를 뜻한다.

---

## 0. 사전 지식 정정

과제문에 적힌 "`MN`은 `Decoder`에서 포인터로 들려 다닌다"는 코드와 다르다.

- ㉮ [decoder.h:328](../../../../../../0_LDPC_original/src/decoder.h)의 `int MN;`은 스칼라다.
  [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)에서
  `MN = m_param_dec->MN[m_param_dec->MN_num - 1]`로 값을 받고,
  [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp)의
  `for (mn = 0; mn < MN + 1; mn++)`에서 루프 상한으로 쓰인다
- ㉯ 따라서 [decoder.cpp:2098](../../../../../../0_LDPC_original/src/decoder.cpp), 2115의
  `MN = MN + ITER_MAX_HBF`는 포인터 이동이 아니라 루프 상한 연장이다
- ㉰ `int*`인 것은 [ecc_data.h:130](../../../../../../0_LDPC_original/src/ecc_data.h)의
  `m_param_dec->MN` 하나뿐이다

이 구분이 결론을 뒤집는다. 상한 연장이므로 BF 미진입 프레임은 iteration 개수를 잃지 않고,
대신 BF 진입 프레임이 4개를 잃는다. 포인터 이동이라고 읽으면 반대 결론이 나온다.

---

## 1. 영역 ㉯: `MN` 전수 grep과 분류

검색어 `\bMN\b`, `MN_num|MN_max`를 [0_LDPC_original/src](../../../../../../0_LDPC_original/src)
전체에 걸었다. 분류는 ㉠ 배열 원소 읽기, ㉡ 스칼라 루프 상한 조작, ㉢ 크기 계산, ㉣ 할당과 해제다.

### 1.1 `m_param_dec->MN` (int*, [ecc_data.h:130](../../../../../../0_LDPC_original/src/ecc_data.h))

| 파일:줄 | 표현 | 분류 |
|---------|------|------|
| local_opt.cpp:117 | `MN = new int[MN_num]` | ㉣ 할당 |
| local_opt.cpp:119-122 | `MN[i] = i` 또는 `MN[i] = iter_end[num_row-1]` | ㉠ 채우기 |
| local_opt.cpp:125-127 | `MN[i] -= ITER_MAX_HBF` (전 원소) | ㉠ 중간 원소 갱신 |
| local_opt.cpp:128-130 | `MN[0] = ITER_MAX_HBF` | ㉠ 첫 원소 갱신 |
| decoder.cpp:564 | `MN_max = MN[MN_num-1] + ITER_MAX_HBF` | ㉢ 크기 계산 |
| decoder.cpp:587 | `printf("* Max iter : %d", MN[MN_num-1])` | ㉠ 마지막 원소 표시 |
| decoder.cpp:1118 | `MN = MN[MN_num-1]` (스칼라로 복사) | ㉠ 마지막 원소 |
| decoder.cpp:7583, 7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018 | `MN_size = MN[MN_num-1] + ITER_MAX_HBF + 1` | ㉢ 크기 계산 (18곳) |
| ecc_top.cpp:878 | `if (o_iter_num > m_param_dec->MN[n])` | **㉠ 중간 원소 읽기** |
| ecc_top.cpp:2022 | `tmp = MN[n]` (stdout 머리글) | **㉠ 중간 원소 읽기** |
| ecc_top.cpp:2054 | `tmp = MN[n]` (Ref_C_result 머리글) | **㉠ 중간 원소 읽기** |
| ecc_top.cpp:2738, 2741, 2757, 2760, 2774, 2790, 2815, 2819 | `MN[MN_num-1] + 2`, `* 4`, `+ 1` | ㉢ 크기 계산 |
| corner.cpp:103 | `m_dec_i[IDX_DEC_I_MAX_ITR] = MN[MN_num-1]` | ㉠ 마지막 원소 |
| main.cpp:317 | `fprintf(fp, "%d ", g_param_dec.MN[n])` | **㉠ 중간 원소 읽기** (AUTO 전용, main.cpp:313-320) |
| main.cpp:108, 129 | `delete[] g_param_dec.MN` | ㉣ 해제 |
| main.cpp:711-879 | 비AUTO 경로의 `MN_num`, `MN[i]` 하드코딩 대입 | ㉣ 할당과 채우기 |

중간 원소 `MN[n]`(0 < n < MN_num-1)을 읽는 곳은 **ecc_top.cpp:878, ecc_top.cpp:2022,
ecc_top.cpp:2054, main.cpp:317 네 곳뿐**이다.

### 1.2 `Decoder::MN` (int, [decoder.h:328](../../../../../../0_LDPC_original/src/decoder.h))

| 파일:줄 | 표현 | 분류 |
|---------|------|------|
| decoder.cpp:1118 | 대입 | ㉡ |
| decoder.cpp:1120 | 루프 상한 | ㉡ |
| decoder.cpp:2098, 2115 | `MN = MN + ITER_MAX_HBF` | ㉡ 상한 연장 |
| decoder.cpp:4960, 5076, 5104, 5204, 5272 | `mn = MN` (강제 종료) | ㉡ |
| decoder.cpp:4996-5069 (2SD), 5124-5265 (3SD) | `if (MN < RSP1_*)`, `MN_old = MN`, `MN = RSP1_*` | ㉡ restart 상한 갱신 |
| decoder.cpp:5350 | `if (mn == MN)` (uncor 판정) | ㉡ |
| ecc_top.cpp:2738, 2757, 2774, 2790, 2815 | 지역 변수 `int MN` (이름만 같음) | ㉢ |
| main.cpp:788-879 | 지역 변수 `int MN` (이름만 같음) | ㉣ |

이 갈래에는 배열 원소 읽기가 없다.

### 1.3 손계산: `ITER_MAX_HBF` 4, 파일 최대 iteration 124

[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)의
마지막 row(105행)는 `iter_start 105, iter_end 124`이고 전체 row의 `iter_end` 최댓값도 124다.
code_diff 3.5의 수정 후 코드로도 수정 전 코드로도 `MN_num = 124`가 나온다.

[local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp)을 그대로 실행하면

- ㉮ 116-123행: `MN_num = 124`, `MN[i] = i` (i = 0..122), `MN[123] = 124`
- ㉯ 124-127행 (`init_n == MODE_DEC_HD`이므로 참): 전 원소에서 4를 뺀다.
  `MN[i] = i - 4` (i = 0..122), `MN[123] = 120`
- ㉰ 128-130행 (`MN_num > 1`이므로 참): `MN[0] = 4`

최종 배열:

| index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | ... | 122 | 123 |
|-------|---|---|---|---|---|---|---|---|---|---|-----|-----|-----|
| 값 | 4 | -3 | -2 | -1 | 0 | 1 | 2 | 3 | 4 | 5 | ... | 118 | 120 |

- ㉮ 음수 원소는 index 1, 2, 3 (값 -3, -2, -1)
- ㉯ index 4의 값은 0
- ㉰ index 0과 index 8이 둘 다 4로 중복이다
- ㉱ 마지막 원소는 120이며 이것이 [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)의 루프 상한이 된다

현재 상태(`ITER_MAX_HBF` 0)에서는 124-130행이 전부 무효라 `MN = [0, 1, ..., 122, 124]`다.

### 1.4 소비처별 동작

**ecc_top.cpp:877-881 (FER 집계)**

```
for (int n = 0; n < m_param_dec->MN_num - 1; n++) {
    if (o_iter_num > m_param_dec->MN[n]) {
        fr_4KB[n]++;
    }
}
```

`o_iter_num`은 [decoder.cpp:5344, 5355](../../../../../../0_LDPC_original/src/decoder.cpp)에서
`mn`으로 대입되고, `Check_End_Iter`는 [decoder.cpp:1947-1951](../../../../../../0_LDPC_original/src/decoder.cpp)에
따라 `mn > 0`에서만 불린다. HD에서 [decoder.cpp:1976](../../../../../../0_LDPC_original/src/decoder.cpp)의
`iter_num -= ITER_MAX_HBF`까지 거치면 값의 범위는 1 이상 120 이하다. 따라서

- ㉮ n = 1, 2, 3 (문턱 -3, -2, -1): 조건이 항상 참 → FER 열 1.0 고정
- ㉯ n = 4 (문턱 0): 조건이 항상 참 → FER 열 1.0 고정
- ㉰ n = 0 (문턱 4): iteration 4 시점 FER
- ㉱ n = 5 이상: iteration `n - 4` 시점 FER (열 번호와 iteration이 4만큼 어긋난다)
- ㉲ n = 8의 문턱도 4라서 열 0과 열 8의 값이 같다

배열 index는 `n`이므로 음수 index 접근은 없다. `fr_4KB`는
[ecc_top.cpp:638-640](../../../../../../0_LDPC_original/src/ecc_top.cpp)에서 `new int[MN_num]`으로 잡히고
0으로 초기화된다.

**ecc_top.cpp:2020-2024와 2052-2056 (머리글)**

`FER (4 -3 -2 -1 0 1 2 3 4 5 ... 118 120)` 형태로 음수와 중복이 그대로 찍힌다.
2020-2024는 stdout(`Print_Result_Part1`), 2052-2056은 `Ref_C_result_{seed}.txt`(`Print_Result_Part1_Auto`)다.
열 개수는 `MN_num` = 124로 바뀌지 않는다.

**main.cpp:313-320**

`__AUTO_LLR_OPT__` 갈래에서 `* iteration number : 4 -3 -2 -1 0 1 ...`이 설정 요약 파일에 찍힌다.
표시만 한다.

**decoder.cpp:564 (`MN_max`)**

`MN_max = 120 + 4 = 124`. 현재 상태의 `124 + 0 = 124`와 같다.
`crc_dec_LFSR_iter`는 `MN_max * CRC_LEN` = 9920칸이고,
[decoder.cpp:5315](../../../../../../0_LDPC_original/src/decoder.cpp)의 색인 `real_mn - 1`은
`real_mn`이 [decoder.cpp:1966](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `mn == 0` 본문 끝에
먼저 1이 되므로 최소 0, 최대 119다. 범위 밖 접근 없음.

**decoder.cpp:7583 외 17곳 (`MN_size`)**

`120 + 4 + 1 = 125`. 현재 상태의 `124 + 0 + 1 = 125`와 같다.
로그 배열 폭이 유지되므로 `mn` 최대 124를 담을 수 있다.

**ecc_top.cpp:2738, 2757, 2774, 2790, 2815, 2819 (로그와 histogram 크기)**

여기는 `ITER_MAX_HBF`를 더하지 않는다. `MN[MN_num-1] + 2` = 122 (현재 126),
`size_histogram = MN[MN_num-1] * 4` = 480 (현재 496)이다.
`__PRINT_LOG_DATA__`가 [mode.h:31](../../../../../../0_LDPC_original/src/mode.h)에서 주석이라
지금 빌드에서는 컴파일되지 않는다. 켜면 아래 두 가지가 생긴다.

- ㉮ `Update_Log_Data`([ecc_top.cpp:2790-2801](../../../../../../0_LDPC_original/src/ecc_top.cpp))가
  i를 0..120까지만 돌아 mn 121~124 기록이 사라진다 (읽는 쪽 배열은 125칸이라 범위 밖 접근은 없다)
- ㉯ `Update_Log_Iter_Histogram`([ecc_top.cpp:2805-2810](../../../../../../0_LDPC_original/src/ecc_top.cpp))의
  `idx = (iter - 1) * 4 + pcrc`에서 `iter`가 `o_iter_num`이다.
  `matrix_sel`이 `LAYOUT_PRIME_512B_TLC_VSS_OFF`(common.h:193, 값 1)가 아니면
  [decoder.cpp:1973-1978](../../../../../../0_LDPC_original/src/decoder.cpp)의 `iter_num -= ITER_MAX_HBF`가
  걸리지 않아 `o_iter_num` 최대가 124가 되고 `idx`가 492까지 올라가 480칸 배열 밖을 쓴다

**corner.cpp:103**

`IDX_DEC_I_MAX_ITR`에 120이 들어간다. `__CORNER_CHECKER__`가
[mode.h:75](../../../../../../0_LDPC_original/src/mode.h)에서 주석이라 지금 빌드 밖이다.

**decoder.cpp:1919 (`m_log_CSW_auto[mn]`)**

배열 크기는 [decoder.cpp:7774](../../../../../../0_LDPC_original/src/decoder.cpp)의 `MN_size` = 125로
현재와 같다. 다만 BF 진입 프레임은 121~124칸이, 미진입 프레임은 1~4칸이
[decoder.cpp:7742](../../../../../../0_LDPC_original/src/decoder.cpp)의 초기값 -1로 남는다.
지금은 모든 프레임이 0~124를 채운다.

### 1.5 `MN[]` 값이 배열 index로 쓰이는 곳

없다. 값에서 index를 만드는 유일한 곳은 위의 histogram(`o_iter_num` 기반)이며,
그것도 `MN[]` 값을 직접 쓰지 않는다. **음수 index 접근은 발생하지 않는다.**

### 1.6 DAO Python 쪽 파싱

- ㉮ DAO가 읽는 파일은 [DAO_Main.py:1604-1628](../../../../../SRC/DAO_Main.py)의
  `result_4KB_S_..._seed_{n}.txt`이고, C++ 쪽에서는
  [ecc_top.cpp:2163](../../../../../../0_LDPC_original/src/ecc_top.cpp)의
  `m_param_ref_c->str_result_name_4KB`다. 이 파일에는 데이터 줄만 들어가고
  `MN[]` 머리글은 들어가지 않는다 (머리글은 stdout과 `Ref_C_result_{seed}.txt` 전용)
- ㉯ [DAO_Main.py:8187-8261](../../../../../SRC/DAO_Main.py)의 `Read_Ref_C_Result`는
  줄을 공백으로 쪼개 `parts[base_offset:]`을 숫자로 읽고 `parts[result_offset:-3]`을 FER 배열로 쓴다.
  열 개수가 `MN_num` = 124로 그대로이므로 파싱은 깨지지 않는다
- ㉰ [DAO_Main.py:1809-1836](../../../../../SRC/DAO_Main.py)이 `matrix.max_iteration`(=124)과
  배열 길이를 대조하는데 길이가 같으므로 잘림도 없다
- ㉱ 다만 배열의 뜻이 달라진다. `total_FER_per_iters[i]`가 더 이상 "iteration i+1의 FER"이 아니라
  "문턱 `MN[i]`의 FER"이 되고, index 1~4는 1.0 고정, index 0과 8은 중복이다.
  이 배열은 [DAO_Main.py:1891-1892](../../../../../SRC/DAO_Main.py)에 저장되어
  [DAO_Main.py:7594-7598](../../../../../SRC/DAO_Main.py)의 로그 문자열에만 쓰인다.
  최적화 판단은 `FERs`(마지막 열)와 `avg_iterations`를 쓰므로 판단 자체는 어긋나지 않는다

---

## 2. 영역 ㉲: BF 진입 여부에 따른 iteration 수열 비대칭

### 2.1 메인 루프 손실행

관련 줄: [decoder.cpp:1118-1120](../../../../../../0_LDPC_original/src/decoder.cpp),
[1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp),
[1947-1970](../../../../../../0_LDPC_original/src/decoder.cpp),
code_diff 5.1의 수정 후 `Select_BF`.

루프 진입 시 `MN = m_param_dec->MN[123] = 120`이다. `Select_BF`는 `mn == 0` 본문 끝에서 불린다.

**BF 진입 프레임** (`syn_weight < syn_th_BF0`)

- ㉮ `mn`과 `MN`을 건드리지 않는다
- ㉯ `mn` 수열: 0, 1, 2, ..., 120
- ㉰ `Get_Cur_LLR_Idx_FILE(mn)`은 `mn > 0`에서만 불리므로 iteration 1..120
- ㉱ 루프 본문 실행 횟수 121회, 실제 복호 iteration 120회 (그중 1~4는 1bit precision)
- ㉲ 최대 도달 iteration **120**

**BF 미진입 프레임**

- ㉮ `mn = 0 + 4 = 4`, `MN = 120 + 4 = 124`
- ㉯ 루프 증가로 `mn` 수열: 0, 5, 6, ..., 124
- ㉰ iteration 5..124
- ㉱ 루프 본문 실행 횟수 121회, 실제 복호 iteration 120회 (전부 3bit precision)
- ㉲ 최대 도달 iteration **124**

두 경우 모두 복호 iteration 수는 120으로 같다. 그러나 현재 코드(`ITER_MAX_HBF` 0)는
`MN = MN[123] = 124`이고 `Select_BF`가 아무것도 밀지 않아 모든 프레임이 iteration 1..124,
즉 **124회**를 돈다. 수정 후에는 모든 프레임이 **120회**로 줄어든다.

`Check_End_Iter`의 uncor 판정은 [decoder.cpp:5350](../../../../../../0_LDPC_original/src/decoder.cpp)의
`if (mn == MN)`이므로 BF 진입은 mn 120에서, 미진입은 mn 124에서 uncor가 확정된다.

### 2.2 파일 그룹 11의 실체

[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)에서

- ㉮ 10행 `num_set_each_group` 마지막 값 13, 11행 `type_each_group` 마지막 값 `1`
- ㉯ 93행부터 105행까지 13개 row가 그룹 11이고, **13개 row 모두 `iter_start 105, iter_end 124`**로 같다
- ㉰ CSW 칸은 -1, 1056, 768, 728, 584, 480, 424, 168, 64, 40, 32, 24, 16으로 내림차순이다
- ㉱ 값 `1`은 [common.h:757](../../../../../../0_LDPC_original/src/common.h)의 `GROUP_TYPE_CSW`다.
  상위 문서 4장 ㉮의 예시 표기(113행)에서도 `type_each_group`은 전 그룹 `1`이다

따라서 그룹 11 안의 row 선택은 iteration이 아니라 `prev_CSW`로 이루어진다
([decoder.cpp:7056-7065](../../../../../../0_LDPC_original/src/decoder.cpp), code_diff 6.2의 `GROUP_TYPE_CSW` 갈래).

### 2.3 "121~124 미도달"이 row 미사용을 뜻하는가

**뜻하지 않는다.** 그룹 11의 13개 row는 iteration 105~124 전 구간에서 CSW 문턱으로만 갈리므로,
iteration 105~120만 도는 BF 진입 프레임도 13개 row를 모두 고를 수 있다.
iteration을 조건으로 삼는 row가 그룹 11에 없기 때문에 특정 row가 미진입 프레임 전용이 되는 일은 없다.

같은 검사를 그룹 선택 단계에도 적용하면 결과가 다르다.
code_diff 6.1의 그룹 선택은 `iter_start[start_idx] <= iter <= iter_end[end_idx]`와 분기 일치를 함께 본다.
문턱은 [common.h:236-244](../../../../../../0_LDPC_original/src/common.h)에서
`SW_TH_BF0_512B_TLC_OFF` 680, `SW_TH_BF1_512B_TLC_OFF` 130,
`SW_TH_5_8_SET0_512B_TLC_OFF` 1100이고, code_diff 4.1이 이 값을
`syn_th_BF0`, `syn_th_sw_branch[0][0]`, `syn_th_sw_branch[1][0]`에 넣는다.

- ㉮ BF 진입 조건은 `syn_weight < 680`이다. 그러면 `Select_SW_Branch(1, syn_weight)`는
  `syn_weight < 1100`이므로 항상 0을 돌려준다.
  즉 **그룹 4와 5(구간 1의 분기 1)는 BF 진입 프레임이 절대 고르지 않는다**
- ㉯ 반대로 그룹 0, 1, 2(구간 0)는 iteration 1~4를 덮으므로 **BF 미진입 프레임이 절대 고르지 않는다**
- ㉰ 그룹 3(구간 1의 분기 0)만 두 종류 프레임이 함께 쓴다
- ㉱ 이 갈림은 원본 비AUTO 코드와 같은 결과다. 기존 코드도 BF 진입 시
  `flag_HD_5_8_Set = FLAG_HD_5_8_SET_TYPE_0`으로 못박았다
  ([decoder.cpp:2091](../../../../../../0_LDPC_original/src/decoder.cpp))

### 2.4 DAO 최적화 관점

- ㉮ 매트릭스가 선언한 최대 iteration은 124인데 수정 후 어떤 프레임도 124회를 돌지 않는다.
  DAO는 [DAO_LLR_MATRIX.py:441](../../../../../SRC/DAO_LLR_MATRIX.py)에서
  `max_iteration = groups[-1][-1].iter_end` = 124로 잡고
  [DAO_Main.py:1809-1813](../../../../../SRC/DAO_Main.py)에서 그 값으로 배열을 만든다.
  DAO가 `Change_Max_Iteration(N)`으로 예산을 N으로 늘려도 실제 복호 iteration은 N-4가 된다
- ㉯ `avg_iteration`은 [DAO_Main.py:1886, 1935-1937](../../../../../SRC/DAO_Main.py)에서
  결과 파일의 `Avg Iter` 칸을 그대로 읽는다. C++ 쪽 값은
  [ecc_top.cpp:887-900](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `iter_sum / rn`이고,
  `o_iter_num`은 미진입 프레임에서 4가 빠진 값이다
  ([decoder.cpp:1973-1978](../../../../../../0_LDPC_original/src/decoder.cpp),
  `matrix_sel`은 [DAO_Config.py:170](../../../../../SRC/DAO_Config.py)에서 1이므로 조건 성립).
  같은 실행 안에서는 두 프레임 종류가 같은 척도(1~120)로 합쳐지지만,
  현재 코드(1~124)로 얻은 과거 결과와는 비교할 수 없다.
  `avg_iterations`는 [DAO_Config.py:136](../../../../../SRC/DAO_Config.py)의
  `ENABLE_AVG_ITER_UPDATE`에서 tie-breaker로 쓰인다
- ㉰ iteration별 FER 배열은 열 뜻이 4만큼 밀리지만
  [DAO_Main.py:7594-7598](../../../../../SRC/DAO_Main.py)의 로그 출력에만 쓰이므로 판단은 어긋나지 않는다
- ㉱ 그룹 4, 5가 BF 진입 프레임에게 죽는 것은 SW 문턱 배치의 결과이지 코드 결함이 아니다.
  다만 DAO가 그 그룹의 파라미터를 움직여도 `syn_weight >= 1100`인 프레임에만 반영된다

### 2.5 문서 서술 여부

두 문서 어디에도 이 비대칭이 없다.

- ㉮ 상위 문서 2장 62행은 "최대 iteration은 124다"라고 적는다. 수정 후 BF 진입 프레임은 120까지만 돈다
- ㉯ 상위 문서 5.5장 표 262행은 `local_opt.cpp:126-130`을 "딸려 오는 곳"으로만 적고
  `MN[]`이 어떤 값이 되는지 적지 않는다
- ㉰ code_diff 3.5장은 제목부터 `(116-123행)`이라 124-131행의 보정 블록을 다루지 않는다.
  1.2장의 `ITER_MAX_HBF` 4가 이 블록을 처음으로 살리는데, 그 결과가 문서 어디에도 없다
- ㉱ code_diff 8.1장 950-951행은 edge clear 지점이 1과 5로 갈린다고만 적고
  iteration 수열의 끝이 갈리는 것은 적지 않는다

---

## 3. 발견 목록

### B2-1 (HIGH) 수정 후 모든 프레임의 복호 iteration이 124에서 120으로 줄어든다

- 가설: `ITER_MAX_HBF`를 4로 바꾸면 `local_opt.cpp:126`이 `MN[123]`을 124에서 120으로 낮추고,
  이것이 `decoder.cpp:1118`의 루프 상한이 되어 BF 진입 프레임은 iteration 120에서,
  미진입 프레임은 `Select_BF`의 상한 연장으로 124에서 끝난다. 두 경우 모두 실제 복호 iteration은 120회다
- 근거 (확인됨): [local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp),
  [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp),
  [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp),
  [decoder.cpp:2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp),
  code_diff 5.1 수정 후 블록,
  [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 105행
- 영향: FER과 avg_iteration이 모두 달라진다. DAO의 매트릭스 모델은 124 iteration을 전제한다
- 처방: 문서에 이 결과를 명시하고 의도인지 사용자 결정을 받는다.
  의도가 아니라면 `MN[]` 보정식이나 `Select_BF`의 상한 연장 중 하나를 고쳐야 한다 (**동작 변경 요구**)

### B2-2 (HIGH) 최대 iteration이 4 이하인 매트릭스에서 복호가 한 번도 일어나지 않는다

- 가설: `MN_num <= ITER_MAX_HBF`이면 `MN[MN_num-1] = max_iter - 4 <= 0`이 되어
  `for (mn = 0; mn < MN + 1; mn++)`가 `mn == 0` 한 번만 돌고 끝난다.
  `mn == 0`에서는 `Get_Cur_LLR_Idx_FILE`도 `Check_End_Iter`도 불리지 않으므로
  모든 프레임이 uncor가 되고 FER이 1.0으로 고정된다
- 손계산 (최대 iteration 4): `MN = [0,1,2,4]` → 4씩 빼면 `[-4,-3,-2,0]` → `MN[0] = 4`로 `[4,-3,-2,0]`.
  `decoder.cpp:1118`에서 상한 0. BF 진입이면 `mn < 1`, 미진입이면 `mn`이 4로 밀리고 상한도 4가 되어 `mn < 5`인데
  증가 후 5라 즉시 종료. 어느 쪽도 iteration을 돌지 않는다
- 근거 (확인됨): [local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp),
  [decoder.cpp:1118-1120](../../../../../../0_LDPC_original/src/decoder.cpp),
  [decoder.cpp:1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp),
  [decoder.cpp:1947-1951](../../../../../../0_LDPC_original/src/decoder.cpp)
- 실제 도달 경로: DAO의 HBF 최적화 모드가 매트릭스 최대 iteration을 4 이하로 강제한다.
  [DAO_LLR_MATRIX.py:442-447](../../../../../SRC/DAO_LLR_MATRIX.py)이
  `max_iteration > HBF_OPT_CONFIG.HBF_MAX_ITERATION`(=4, [DAO_Config.py:372](../../../../../SRC/DAO_Config.py))이면
  오류를 낸다. 이 모드는 `init_n == 1`에서만 켤 수 있고
  ([DAO_Config.py:127](../../../../../SRC/DAO_Config.py), [DAO_Main.py:439-440](../../../../../SRC/DAO_Main.py))
  기본값은 False라 사용자가 켤 때만 발생한다
- 추가로, `iter_num`은 [decoder.cpp:606-616](../../../../../../0_LDPC_original/src/decoder.cpp)의
  `Clear_Flag`에서 초기화되지 않는다. iteration을 한 번도 돌지 않으면 앞 프레임 값이 남고
  `decoder.cpp:1976`의 `-= 4`가 프레임마다 누적되어 음수로 내려간다
- 처방: `MN[]` 보정에서 최소값 하한을 두거나(예: `max_iter <= ITER_MAX_HBF`이면 보정 생략),
  파서가 `max_iter > ITER_MAX_HBF`를 검사해 멈춘다 (**동작 변경 요구**)

### B2-3 (MEDIUM) 1.5SD 모드에서 존재하지 않는 iteration 125~128을 돈다

- 가설: `local_opt.cpp:124`의 보정 조건은 `MODE_DEC_HD`와 `MODE_DEC_1_SSD`만 본다.
  `MODE_DEC_1_5SD`(=4, [common.h:78](../../../../../../0_LDPC_original/src/common.h))는 `MN[]` 보정을 받지 못해
  `MN[MN_num-1] = 124`가 그대로 남는다. 그런데 code_diff 5.1의 수정 후 `Select_BF`는
  1.5SD에서 `mn += 4`, `MN += 4`를 수행하므로 상한이 128이 되어 iteration 125~128을 돈다.
  파일의 최대 `iter_end`는 124라 `Get_Cur_LLR_Idx_FILE`이 `selected_group = -1`을 남기고,
  code_diff 6.2의 수정 후 코드가 프레임마다 오류 4줄을 찍고 row 0의 파라미터로 4 iteration을 돈다
- 근거 (확인됨): [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp),
  [decoder.cpp:1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp),
  code_diff 5.1과 6.2 수정 후 블록,
  [decoder.cpp:1973-1978](../../../../../../0_LDPC_original/src/decoder.cpp)(1.5SD도 `iter_num -= 4` 대상)
- 현재 상태에서는 `ITER_MAX_HBF`가 0이라 발생하지 않는 새 결함이다
- DAO는 `init_n`을 1, 2, 3만 쓰므로([DAO_Config.py:36-111](../../../../../SRC/DAO_Config.py))
  지금 운용에서는 도달하지 않지만, code_diff 5.1이 1.5SD 갈래를 명시적으로 유지하므로 계획 안의 결함이다
- 처방: `local_opt.cpp:124`의 둘째 항을 `MODE_DEC_1_5SD`로 고친다 (**식별자 변경, 동작 변경 요구**).
  단 그러면 1.5SD도 B2-1의 iteration 120 축소를 함께 받는다

### B2-4 (MEDIUM) 결과 파일 FER 열의 문턱이 음수, 중복, 축퇴가 된다

- 가설: `MN = [4, -3, -2, -1, 0, 1, ..., 118, 120]`이므로 `ecc_top.cpp:878`의 비교에서
  열 1~4가 항상 참이 되어 FER 1.0으로 고정되고, 열 0과 열 8의 문턱이 4로 겹치며,
  열 n(n >= 5)의 뜻이 iteration `n - 4`로 밀린다
- 근거 (확인됨): [ecc_top.cpp:877-881](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [ecc_top.cpp:2020-2024](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [main.cpp:313-320](../../../../../../0_LDPC_original/src/main.cpp)
- DAO 파싱은 깨지지 않는다 (반박됨): 열 개수가 124로 그대로이고,
  머리글은 DAO가 읽지 않는 `Ref_C_result_{seed}.txt`와 stdout에만 간다.
  DAO가 읽는 `result_4KB_*.txt`([ecc_top.cpp:2163](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [DAO_Main.py:1604-1628](../../../../../SRC/DAO_Main.py))에는 데이터 줄만 들어간다.
  파서 [DAO_Main.py:8187-8261](../../../../../SRC/DAO_Main.py)는 통과한다
- 처방: 보정식을 음수가 나오지 않게 고치거나, 문서에 열 배치를 적는다 (**보정식 변경이면 동작 변경 요구**)

### B2-5 (MEDIUM) code_diff 3.5가 `local_opt.cpp:124-131`을 다루지 않아 `MN[]`의 최종 모습이 문서에 없다

- 근거 (확인됨): code_diff 3.5장 제목 `(116-123행)`,
  상위 문서 5.5장 표 262행이 `local_opt.cpp:126-130`을 언급만 하고 결과를 적지 않음
- 이 보정 블록은 `ITER_MAX_HBF`가 0인 지금은 전부 무효라 눈에 띄지 않지만, 1.2장이 4로 바꾸는 순간 살아난다
- 처방: 3.5장에 124-131행을 살린다고 적고 그때의 `MN[]` 값을 표로 싣는다 (문서 보강)

### B2-6 (MEDIUM) BF 진입 프레임과 미진입 프레임의 iteration 수열 비대칭이 문서에 없다

- 근거 (확인됨): 상위 문서 2장 62행, 5.5장 표 255-256행, code_diff 8.1장 950-951행 어디에도
  "BF 진입 프레임은 iteration 120에서 끝난다"는 서술이 없다
- 처방: 상위 문서 5.5장에 두 프레임 종류의 `mn` 수열과 최대 도달 iteration을 표로 적는다 (문서 보강)

### B2-7 (LOW) `__PRINT_LOG_DATA__`를 켜면 histogram 배열 밖을 쓴다

- 가설: `size_histogram = MN[MN_num-1] * 4` = 480인데
  `matrix_sel != LAYOUT_PRIME_512B_TLC_VSS_OFF`이면 `o_iter_num` 최대가 124라
  `idx = (124-1)*4 + 3 = 495`가 되어 배열 밖을 쓴다
- 근거 (확인됨): [ecc_top.cpp:2819](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [ecc_top.cpp:2805-2810](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [ecc_top.cpp:953-959](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [decoder.cpp:1973-1978](../../../../../../0_LDPC_original/src/decoder.cpp)
- 지금 빌드 밖이다: `__PRINT_LOG_DATA__`가 [mode.h:31](../../../../../../0_LDPC_original/src/mode.h)에서 주석
- 같은 블록의 `MN[MN_num-1] + 2` 계열(2738, 2757, 2774, 2790, 2815)은 `ITER_MAX_HBF`를 더하지 않아
  로그 커버리지가 126칸에서 122칸으로 줄어든다 (범위 밖 접근은 아니다)
- 처방: 이 다섯 곳도 `+ ITER_MAX_HBF`를 붙여 `decoder.cpp:7583` 계열과 맞춘다 (코드 추가)

### B2-8 (LOW) CSW 로그에 프레임 종류별 구멍이 생긴다

- 근거 (확인됨): [decoder.cpp:1919](../../../../../../0_LDPC_original/src/decoder.cpp),
  [decoder.cpp:7774](../../../../../../0_LDPC_original/src/decoder.cpp),
  [decoder.cpp:7742](../../../../../../0_LDPC_original/src/decoder.cpp)
- 배열 폭은 125로 그대로지만 BF 진입 프레임은 121~124칸이, 미진입 프레임은 1~4칸이 -1로 남는다.
  지금은 모든 프레임이 0~124를 채운다
- DAO는 이 파일을 [DAO_Main.py:1737-1749](../../../../../SRC/DAO_Main.py)에서 병합만 하고 수치 판단에 쓰지 않는다
- 처방: 문서에 구멍이 생기는 것을 적는다 (문서 보강)

### B2-9 (LOW) code_diff 4.1의 "문턱 오름차순" 서술과 상수가 어긋난다

- code_diff 4.1 473-474행은 `SW_TH_5_8_SET1_*`을 분기가 셋 이상일 때 `syn_th_sw_branch[1][1]`에 넣는다고 적고,
  447-449행은 "문턱은 오름차순"이라고 적는다
- 실제 상수는 [common.h:244](../../../../../../0_LDPC_original/src/common.h) `SW_TH_5_8_SET0_512B_TLC_OFF` 1100,
  [common.h:251](../../../../../../0_LDPC_original/src/common.h) `SW_TH_5_8_SET1_512B_TLC_OFF` 950으로 내림차순이다
- code_diff 5.1의 `Select_SW_Branch`(542-547행)는 오름차순을 전제하므로 그대로 넣으면 분기 2가 영영 선택되지 않는다
- 처방: 상위 문서 7장 ㉯(문턱을 파일이나 실행 인자로 받을지)에 이 상수 순서 문제를 근거로 붙인다 (문서 보강)

### B2-10 (LOW, 정정) 과제문의 "`MN`은 포인터" 전제가 코드와 다르다

- `Decoder::MN`은 [decoder.h:328](../../../../../../0_LDPC_original/src/decoder.h)의 `int`이며 루프 상한이다.
  `MN = MN + ITER_MAX_HBF`는 상한 연장이다
- 이 구분이 B2-1의 결론을 결정한다. 상한 연장이므로 잃는 쪽은 BF 진입 프레임이다

### B2-11 (참고, 기존 손상) `MODE_DEC_1_SSD`가 정의되어 있지 않다

- [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp)의 `MODE_DEC_1_SSD`는
  저장소 전체 grep에서 이 한 곳뿐이고 [common.h:75-78](../../../../../../0_LDPC_original/src/common.h)에 정의가 없다
- `Local_Opt.h`에 컴파일 가드가 없으므로 저장소의 현재 상태로는 `local_opt.cpp`가 컴파일되지 않는다
- 이 줄이 `MN[]` 보정 블록의 진입 조건이므로, 영역 ㉯의 모든 결론은 이 조건이 `MODE_DEC_HD`에서 참이라는 전제 위에 있다

---

## 4. 확인한 범위

읽은 소스: [local_opt.cpp:1-190](../../../../../../0_LDPC_original/src/local_opt.cpp),
[Local_Opt.h 전체](../../../../../../0_LDPC_original/src/Local_Opt.h),
[decoder.cpp:550-604, 603-632, 1100-1210, 1900-2078, 2060-2139, 5295-5362](../../../../../../0_LDPC_original/src/decoder.cpp),
[decoder.h:285-344, 429-437](../../../../../../0_LDPC_original/src/decoder.h),
[ecc_top.cpp:860-909, 2000-2289, 2730-2840](../../../../../../0_LDPC_original/src/ecc_top.cpp),
[main.cpp:295-329](../../../../../../0_LDPC_original/src/main.cpp),
[mode.h 전체](../../../../../../0_LDPC_original/src/mode.h),
[common.h:75-78, 86-87, 193-251, 756-757](../../../../../../0_LDPC_original/src/common.h),
[ecc_data.h:129-130](../../../../../../0_LDPC_original/src/ecc_data.h).

읽은 입력: [LLR_MATRIX_1.txt 전체](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) (106줄).

읽은 DAO: [DAO_Main.py:425-449, 1604-1628, 1780-1899, 7585-7609, 8187-8273](../../../../../SRC/DAO_Main.py),
[DAO_LLR_MATRIX.py:300-544](../../../../../SRC/DAO_LLR_MATRIX.py),
[DAO_Config.py:120-200, 355-432](../../../../../SRC/DAO_Config.py),
[DAO_Constants.py:123-135](../../../../../SRC/DAO_Constants.py).

전수 grep: `\bMN\b`, `MN_num|MN_max`, `iter_num|real_mn`, `MODE_DEC_1_SSD`,
`BF_mode|MODE_BF_ON|MODE_BF_OFF`, `Update_Log_Iter_Histogram|Padding_Zero_Log|Update_Log_Data`,
`m_log_CSW_auto`, `str_result_name_4KB`, `IS_HBF_OPT|is_HBF_OPT`, `total_FER_per_iters`.
