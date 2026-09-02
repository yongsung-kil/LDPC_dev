# 팀 V3 워커 1: 발견 R2-5 사실 축 검증

작성: 2026-09-03 01:35:43

검증 대상: Round 2 발견 R2-5 (`ITER_MAX_HBF` 4에서 `MN[]` 보정이 만드는 결과 파일 왜곡, 실행 iteration 수 변화, `iter_num` 보정 부활)

방법: 코드 직접 읽기, grep 전수 확인, 파일 토큰 세기, 손 실행. 문서와 코드는 수정하지 않았다.

---

## 0. 전제 확인 (모든 가설의 공통 바탕)

| # | 전제 | 판정 | 근거 |
|---|------|------|------|
| 0-1 | DAO가 쓰는 빌드는 `__AUTO_LLR_OPT__`가 정의되고 `__RUN_MPI__`는 정의되지 않는다 | 확인됨 | [mode.h:18-27](../../../../../../0_LDPC_original/src/mode.h#L18-L27). `__PROGRAM_MODE_REF_C__`를 켜고 비Windows로 빌드하면 21-22행이 `__AUTO_LLR_OPT__`를 정의한다. `__RUN_MPI__`는 23-25행의 `#if !defined(__AUTO_LLR_OPT__)` 안에만 있어, 바로 위에서 정의된 매크로 때문에 절대 정의되지 않는다 |
| 0-2 | DAO 설정은 `matrix_sel` 1, `init_n` 1 | 확인됨 | [DAO_Config.py:170-171](../../../../../SRC/DAO_Config.py#L170-L171). `LAYOUT_PRIME_512B_TLC_VSS_OFF`가 1 ([common.h:193](../../../../../../0_LDPC_original/src/common.h#L193)), `MODE_DEC_HD`가 1 ([common.h:75](../../../../../../0_LDPC_original/src/common.h#L75)) |
| 0-3 | `__4_BIT_LLR__`, `__RUN_PREPROCESSING__`, `__CORNER_CHECKER__`, `__RUN_PARITY_SKIP__`은 꺼져 있다 | 확인됨 | [mode.h:12, 63, 75, 79](../../../../../../0_LDPC_original/src/mode.h#L12) 모두 주석 |
| 0-4 | code_diff 1.2가 `ITER_MAX_HBF`를 4로 통일한다 | 확인됨 | [code_diff.md 1.2](../../code_diff.md#L58-L77). 수정 전은 [common.h:403-407](../../../../../../0_LDPC_original/src/common.h#L403-L407)의 AUTO 0, 비AUTO 4 |
| 0-5 | code_diff 5.1의 `Select_BF`는 AUTO 갈래를 없애 미진입 프레임에서 `mn += ITER_MAX_HBF`, `MN += ITER_MAX_HBF`를 실행한다 | 확인됨 | [code_diff.md 5.1 수정 후 564-570행](../../code_diff.md#L564-L570). 수정 전 [decoder.cpp:2084-2085](../../../../../../0_LDPC_original/src/decoder.cpp#L2084-L2085)는 AUTO에서 `flag_BF_on = FLAG_LOW`만 하고 mn을 밀지 않는다 |
| 0-6 | `mn`과 `MN`은 `Decoder`의 멤버라 `Select_BF`의 대입이 메인 루프 조건에 반영된다 | 확인됨 | [decoder.h:327-328](../../../../../../0_LDPC_original/src/decoder.h#L327-L328) `int mn; int MN;` |

---

## 1. 가설 H5-A: `MN[]` 배열 값

> `ITER_MAX_HBF`가 4일 때 `local_opt.cpp` 116-131행을 손으로 실행하면 `MN[]`이 `[4, -3, -2, -1, 0, 1, ..., 118, 120]`이 되고 `MN_num`은 125다.

**판정: 부분 확인 (값은 확인됨, `MN_num`은 반박됨)**

배열 내용은 Round 2 주장 그대로다. `MN_num`은 125가 아니라 **124**다. 이 가설 문장의 "125"는 이번 검증 지시문에서 처음 나온 수이며, Round 2 report 본문은 수를 적지 않았다.

### ㉮ 116-123행이 `MN[]`을 채우는 값과 `MN_num`의 출처

| 항목 | 값 | 판정 | 근거 |
|------|-----|------|------|
| `MN_num`의 출처 | 파일의 **마지막 row의 `iter_end`** (iteration 번호). `num_row`가 아니다 | 확인됨 | [local_opt.cpp:116](../../../../../../0_LDPC_original/src/local_opt.cpp#L116) `m_param_dec->MN_num = LLR_info->iter_end[LLR_info->num_row - 1];` |
| 채우는 규칙 | `i == MN_num-1`이면 `iter_end[num_row-1]`, 아니면 `i` | 확인됨 | [local_opt.cpp:118-123](../../../../../../0_LDPC_original/src/local_opt.cpp#L118-L123) |
| 결과 | `[0, 1, 2, ..., MN_num-2, MN_num]`. 값 `MN_num-1`은 어느 칸에도 들어가지 않는다 | 확인됨 | 같은 곳 |

`num_row`(77)와 `MN_num`(124)이 다르다는 점이 뒤 가설들에서 중요하다. 결과 파일의 FER 열 수는 파일의 row 수가 아니라 iteration 상한을 따른다.

### ㉯ 124-131행의 조건과 보정식

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| 조건 | `(MODE_DEC_HD == init_n) || (MODE_DEC_1_SSD == init_n)` | 확인됨 | [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp#L124) |
| 보정 1 | **전 원소**에 `-= ITER_MAX_HBF` | 확인됨 | [local_opt.cpp:125-127](../../../../../../0_LDPC_original/src/local_opt.cpp#L125-L127) |
| 보정 2 | `MN_num > 1`이면 `MN[0] = ITER_MAX_HBF` (0번 칸만 되돌리는 것이 아니라 **`ITER_MAX_HBF` 값 자체**를 넣는다) | 확인됨 | [local_opt.cpp:128-130](../../../../../../0_LDPC_original/src/local_opt.cpp#L128-L130) |
| `MODE_DEC_1_SSD` | 저장소 전체에서 이 줄 한 곳뿐이고 정의가 없다 (grep 히트: `local_opt.cpp:124` 하나) | 확인됨 | 저장소 전체 grep 결과 소스 히트는 이 한 줄뿐이고 나머지는 리뷰 문서 |
| AUTO 가드 | `local_opt.cpp`에 파일 단위 `#if defined(__AUTO_LLR_OPT__)` 가드가 없다 | 확인됨 | [local_opt.cpp:1-9](../../../../../../0_LDPC_original/src/local_opt.cpp#L1-L9) |

보정 2가 "0번 칸을 원래 값으로 되돌린다"는 뜻이라면 `MN[0]`은 0이어야 한다. 실제로는 `ITER_MAX_HBF`를 넣으므로 4가 된다. `ITER_MAX_HBF`가 0인 지금은 두 해석의 결과가 우연히 같아서 차이가 드러나지 않는다.

### ㉰ code_diff 3.5가 이 블록을 다루는 방식

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| 3.5의 수정 전 인용 범위 | 116-123행만 인용한다 (124-131행은 인용에 없다) | 확인됨 | [code_diff.md 3.5 수정 전 321-330행](../../code_diff.md#L321-L330) |
| 3.5의 수정 후 코드 | 116-123행 자리를 `max_iter_end` 계산으로 바꾼다. 124-131행에 해당하는 코드는 없다 | 확인됨 | [code_diff.md 3.5 수정 후 334-349행](../../code_diff.md#L334-L349) |
| 3.5가 `MN_num`을 바꾸는가 | 마지막 row의 `iter_end` 대신 전체 최댓값을 쓴다. 이 파일에서는 둘 다 124라 값이 같다 | 확인됨 | [code_diff.md 3.5](../../code_diff.md#L335-L341)와 아래 ㉲의 파일 확인 |

즉 3.5 적용 뒤에도 124-131행 블록의 거취는 문서가 말하지 않는다. 살리면 아래 표대로 음수가 생기고, 지우면 R2-15가 지적한 별개의 문제(미진입 프레임이 mn 128까지 돎)가 생긴다. 이 검증은 **블록을 살린 경우**를 다룬다.

### ㉱ 손 실행 표

입력: `num_row` 77, `iter_end[76]` 124, `init_n` 1 (`MODE_DEC_HD`), `MN_num > 1`.

| 단계 | 줄 | 하는 일 | 중간값 |
|------|-----|--------|--------|
| 1 | 116 | `MN_num = iter_end[76]` | `MN_num = 124` |
| 2 | 117 | `MN = new int[124]` | 칸 0~123 |
| 3 | 118-123 | `i==123`이면 124, 아니면 `i` | `[0, 1, 2, ..., 122, 124]` |
| 4 | 124 | 조건 판정 (`init_n`이 `MODE_DEC_HD`) | 참, 블록 진입 |
| 5 | 125-127 | 전 원소 `-= 4` | `[-4, -3, -2, -1, 0, ..., 118, 120]` |
| 6 | 128-130 | `MN[0] = 4` | `[4, -3, -2, -1, 0, ..., 118, 120]` |

칸별 대조:

| 칸 index | 원본 (`ITER_MAX_HBF` 0) | 수정 후 (`ITER_MAX_HBF` 4) |
|---------|------------------------|---------------------------|
| 0 | 0 | **4** |
| 1 | 1 | **-3** |
| 2 | 2 | **-2** |
| 3 | 3 | **-1** |
| 4 | 4 | **0** |
| 5 | 5 | 1 |
| ... | ... | ... |
| 122 | 122 | 118 |
| 123 (마지막) | 124 | **120** |

원본에서도 5-6단계는 실행되지만 `ITER_MAX_HBF`가 0이라 값이 바뀌지 않는다 (`MN[0] = 0`은 이미 0).

**판정: 확인됨.** Round 2가 적은 `[4, -3, -2, -1, 0, ..., 118, 120]`이 그대로 나온다.

### ㉲ 파일의 실제 row 수와 마지막 iteration 번호

| 항목 | 값 | 판정 | 근거 |
|------|-----|------|------|
| 20칸 이상인 데이터 row 수 | 77 | 확인됨 | [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 18-105행을 세었다. 헤더의 `num_set_each_group` 합(1+7+6+6+1+5+5+7+6+10+10+13)도 77 |
| 전체 정수 토큰 수 | 1584 (헤더 44 + row 77×20 = 1540) | 확인됨 | 같은 파일. 현행 파서 기준으로 남는 토큰도 모자라는 토큰도 없다 |
| `iter_end` 값 분포 | 1(1개), 4(13), 5(1), 8(11), 24(5), 44(7), 64(6), 84(10), 104(10), 124(13) | 확인됨 | 같은 파일 19번째 칸 |
| 마지막 row의 `iter_end` | 124 | 확인됨 | 105행 |
| 전체 최댓값 | 124 | 확인됨 | 위 분포 |
| **`MN_num`** | **124** | 확인됨 | 116행 식(마지막 row)과 code_diff 3.5 식(전체 최댓값)이 같은 값을 준다 |
| **`MN[MN_num-1]` = `MN[123]`** | 원본 124, 수정 후 **120** | 확인됨 | ㉱ 표 |

**반박: `MN_num`은 125가 아니라 124다.** 이 수가 뒤 가설의 열 개수와 loop 상한을 정하므로 문서에 옮겨 적을 때 주의가 필요하다.

**주의 (H5-A의 전제 조건):** 위 손 실행은 **3.2 파서가 요구하는 분기 줄이 들어간 변환된 파일**을 전제한다. 현재 파일을 3.2 수정 후 파서에 그대로 넣으면 헤더가 12토큰 더 소비되어 row 읽기가 12토큰 밀리고, 마지막 12토큰이 모자라 `fscanf`가 실패해 `iter_end[76]`이 확정되지 않는다 (헤더 44+12=56, 남는 row 토큰 1528 < 필요한 1540). 이는 R2-6의 영역이며 H5-A는 변환 완료를 전제로 성립한다.

---

## 2. 가설 H5-B: 결과 파일 FER 열과 머리글

> `MN[]`에 음수와 0이 들어가면 FER 집계에서 특정 열이 모든 프레임을 세고, 머리글에 음수가 찍힌다.

**판정: 부분 확인 (머리글은 확인됨, 1.0 고정 열의 개수는 반박됨)**

### ㉮ 877-879행의 비교식

```cpp
for (int n = 0; n < m_param_dec->MN_num - 1; n++) {
    if (o_iter_num > m_param_dec->MN[n]) {
        fr_4KB[n]++;
    }
}
```

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| 비교 연산자 | **엄격한 `>`** (`>=`가 아니다) | 확인됨 | [ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp#L878) |
| 좌변 | `o_iter_num` (디코더가 돌려준 iteration 수) | 확인됨 | 같은 줄. 값은 [decoder.cpp:1998](../../../../../../0_LDPC_original/src/decoder.cpp#L1998) `*o_iter_num = iter_num;` |
| loop 범위 | `n = 0 .. MN_num-2` (마지막 칸 123은 제외) | 확인됨 | [ecc_top.cpp:877](../../../../../../0_LDPC_original/src/ecc_top.cpp#L877) |
| 마지막 칸 | CRC 실패 프레임만 센다 | 확인됨 | [ecc_top.cpp:874-876](../../../../../../0_LDPC_original/src/ecc_top.cpp#L874-L876) `if (FLAG_HIGH == o_CRC_flag) fr_4KB[MN_num - 1]++;` |

### ㉯ `o_iter_num`이 0 또는 음수가 될 수 있는가

| 경로 | 결과 | 판정 | 근거 |
|------|------|------|------|
| `iter_num` 대입처 전수 | `decoder.cpp` 4965, 5077, 5105, 5205, 5273 (모두 `Jump_Iter` 안), 5344, 5355 (`Check_End_Iter` 안) | 확인됨 | grep `iter_num =` 전수 |
| `Jump_Iter`의 대입 | 4965는 `flag_dec_1iter == FLAG_HIGH`일 때만, 5077 이후는 모두 `#ifdef __4_BIT_LLR__` 안 | 확인됨 | [decoder.cpp:4958-4971](../../../../../../0_LDPC_original/src/decoder.cpp#L4958-L4971), [4993](../../../../../../0_LDPC_original/src/decoder.cpp#L4993), [5277](../../../../../../0_LDPC_original/src/decoder.cpp#L5277) |
| `flag_dec_1iter` | 프레임 시작에 `FLAG_LOW`, HIGH로 바꾸는 곳은 모두 `__4_BIT_LLR__` 안 | 확인됨 | [decoder.cpp:610](../../../../../../0_LDPC_original/src/decoder.cpp#L610), 5000/5010/... 전부 4비트 갈래 |
| `Check_End_Iter`의 대입 | `iter_num = mn` (성공 5344, `mn == MN` 실패 5355) | 확인됨 | [decoder.cpp:5344, 5355](../../../../../../0_LDPC_original/src/decoder.cpp#L5342-L5359) |
| `Check_End_Iter` 호출 최소 `mn` | BF 진입 프레임 1, 미진입 프레임 5 (mn 0에서는 불리지 않는다, H5-D 참조) | 확인됨 | [decoder.cpp:1947-1951](../../../../../../0_LDPC_original/src/decoder.cpp#L1947-L1951) |
| 1973-1979 보정 후 최솟값 | 미진입 5 - 4 = **1**, 진입은 보정 없음 **1** | 확인됨 | [decoder.cpp:1973-1979](../../../../../../0_LDPC_original/src/decoder.cpp#L1973-L1979) |

**`o_iter_num >= 1`이 항상 성립한다. 0도 음수도 되지 않는다.** (`__4_BIT_LLR__`이 꺼진 저장소 mode.h 기준)

### ㉰ 1.0 고정이 되는 열의 개수

`o_iter_num >= 1`과 엄격한 `>`를 대입한다.

| 열 index n | `MN[n]` | 조건 `o_iter_num > MN[n]` | 결과 |
|-----------|---------|--------------------------|------|
| 0 | 4 | `iter_num > 4` | 프레임에 따라 다름. 1.0 고정 아님 |
| 1 | -3 | 항상 참 | **1.0 고정** |
| 2 | -2 | 항상 참 | **1.0 고정** |
| 3 | -1 | 항상 참 | **1.0 고정** |
| 4 | **0** | `iter_num > 0`, `iter_num >= 1`이므로 **항상 참** | **1.0 고정** |
| 5 | 1 | `iter_num > 1` | 프레임에 따라 다름 |

**반박: 1.0 고정 열은 셋이 아니라 넷이다 (index 1, 2, 3, 4).** Round 2가 index 4를 뺀 것은 `MN[4] = 0`에서 `iter_num > 0`이 성립하지 않는 프레임(즉 `iter_num == 0`)이 있을 수 있다고 본 것으로 보이나, ㉯에서 그런 프레임이 없음이 확정된다. `MN[4] = 0` 열도 1.0 고정이다.

참고로 **원본(`ITER_MAX_HBF` 0)에서도 열 0은 이미 1.0 고정이다** (`MN[0] = 0`, `iter_num > 0` 항상 참). 그러므로 이 변경의 실제 효과는 "0개에서 3개"가 아니라 **"1개에서 4개"**이며, 동시에 열 0의 뜻이 "iteration 0을 넘긴 비율(항상 1.0)"에서 "iteration 4를 넘긴 비율"로 바뀐다. 열 배치도 단조성을 잃는다 (머리글이 4, -3, -2, -1, 0, 1, ... 순).

### ㉱ 2052-2056행이 머리글에 `MN[n]`을 그대로 찍는가

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| AUTO 머리글 | `for (n=0; n<MN_num; n++) { tmp = MN[n]; fprintf(fp, "%d", tmp); }` 로 가공 없이 그대로 | 확인됨 | [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp#L2052-L2056) |
| 비AUTO 머리글 | 같은 형태 | 확인됨 | [ecc_top.cpp:2020-2024](../../../../../../0_LDPC_original/src/ecc_top.cpp#L2020-L2024) |
| 찍히는 문자열 | `FER (4 -3 -2 -1 0 1 2 ... 118 120)` | 확인됨 | ㉱ 손 실행 표 대입 |

### ㉲ 이 출력 경로의 컴파일 스위치와 대상 파일 (중요한 정정)

| 함수 | 대상 파일 | 컴파일 조건 | 호출 지점 | 판정 |
|------|----------|------------|----------|------|
| `Print_Result_Part1_Auto` (머리글) | **`Ref_C_result_<seed>.txt`** | `#if !defined(__RUN_MPI__)` 안의 `#ifdef __AUTO_LLR_OPT__` | [ecc_top.cpp:651-653](../../../../../../0_LDPC_original/src/ecc_top.cpp#L646-L662) | 확인됨. AUTO 빌드에서 컴파일되고 실행된다 |
| `Print_Result_Part2_Memory_Opt(TRUE, ...)` (데이터 줄) | **`str_result_name_4KB`** = `result_4KB_S_<scenario>_...txt` | 같은 조건 | [ecc_top.cpp:680-684](../../../../../../0_LDPC_original/src/ecc_top.cpp#L679-L688), 파일명 [main.cpp:698](../../../../../../0_LDPC_original/src/main.cpp#L698) | 확인됨 |
| `Print_Result_Part2_Memory_Opt_Auto` (주기 출력) | `Ref_C_result_<seed>.txt` | `__WIN_OS__` 안 | [ecc_top.cpp:944-947](../../../../../../0_LDPC_original/src/ecc_top.cpp#L943-L951) | 확인됨. Linux 빌드에서는 컴파일되지 않는다 |

**정정할 점: 음수 머리글은 DAO가 파싱하는 파일에 들어가지 않는다.** 머리글은 `Ref_C_result_<seed>.txt`로 가고, DAO가 읽는 것은 `result_4KB_S_...txt`이며 AUTO 빌드에서 이 파일에는 머리글을 쓰는 코드가 컴파일되지 않는다 (`Print_Result_Part1`은 `#else` 갈래라 AUTO에서 빠진다). 따라서 음수 머리글은 **사람이 읽는 로그의 가독성 문제**이지 DAO 파싱을 깨는 문제가 아니다. 이 구분이 R2-5의 심각도 판단을 바꾼다 (7절 참조).

**H5-B 종합 판정: 부분 확인.** 머리글 음수는 확인됨, 1.0 고정 열 개수는 반박됨(셋이 아니라 넷), 영향 범위는 축소됨(DAO 파싱 파일이 아니라 사람이 읽는 로그).

---

## 3. 가설 H5-C: 실행 iteration 수와 iteration 121~124 미도달

> BF 진입 프레임은 mn 1~120, 미진입 프레임은 mn 5~124를 돌아 둘 다 120회이고, 진입 프레임은 파일의 121~124 row를 쓰지 않는다.

**판정: 확인됨 (단 "row"라는 표현은 부정확, 아래 ㉱)**

### ㉮ 메인 루프의 상한

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| 상한 대입 | `MN = m_param_dec->MN[m_param_dec->MN_num - 1];` = `MN[123]` | 확인됨 | [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp#L1117-L1118) |
| 루프 | `for (mn = 0; mn < MN + 1; mn++)` | 확인됨 | [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp#L1120) |
| 수정 후 `MN` 초기값 | 120 (H5-A ㉲) | 확인됨 | |
| 원본 `MN` 초기값 | 124 | 확인됨 | |

### ㉯ `Select_BF`가 미진입 프레임에서 더하는 값

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| 수정 전 AUTO | `flag_BF_on = FLAG_LOW`만. mn과 MN을 건드리지 않는다 | 확인됨 | [decoder.cpp:2084-2085](../../../../../../0_LDPC_original/src/decoder.cpp#L2084-L2086) |
| 수정 전 비AUTO | `mn = mn + ITER_MAX_HBF; MN = MN + ITER_MAX_HBF;` | 확인됨 | [decoder.cpp:2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp#L2096-L2098) |
| 수정 후 (5.1) | 갈래 없이 미진입 프레임에서 `mn += ITER_MAX_HBF; MN += ITER_MAX_HBF;` | 확인됨 | [code_diff.md 5.1 566-567행](../../code_diff.md#L564-L570) |
| 호출 지점 | mn 0 루프 본문 끝 | 확인됨 | [decoder.cpp:1967-1970](../../../../../../0_LDPC_original/src/decoder.cpp#L1967-L1970) |

### ㉰ 두 프레임의 mn 수열

| 프레임 | mn 수열 | 복호 iteration 수 (mn 0 제외) | 근거 |
|--------|---------|------------------------------|------|
| BF 진입 (`flag_BF_on` HIGH) | 0, 1, 2, ..., 120 | **120** | `MN`이 120으로 유지되고 루프 조건이 `mn < 121` |
| BF 미진입 (`flag_BF_on` LOW) | 0, 5, 6, ..., 124 | **120** | mn 0 본문 끝에서 mn이 4가 되고 `mn++`로 5, `MN`은 124가 되어 루프 조건이 `mn < 125` |
| (참고) 현행 AUTO | 0, 1, 2, ..., 124 | 124 | `Select_BF`가 mn을 밀지 않고 `MN`이 124 |

**확인됨.** 실행 iteration이 124회에서 120회로 준다. 두 갈래가 120회로 같다는 것도 확인됨.

### ㉱ 진입 프레임이 닿지 못하는 것의 실체

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| 마지막 그룹(그룹 11)이 덮는 iteration 범위 | `iter_start` 105, `iter_end` 124 | 확인됨 | [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 93-105행, 13개 row가 모두 105/124 |
| 그룹 11의 row 선택 방식 | `type_each_group[11]` = 1 = `GROUP_TYPE_CSW`. row는 iteration이 아니라 `prev_CSW`로 고른다 | 확인됨 | 파일 11행의 12번째 값이 1, [decoder.cpp:7059-7067](../../../../../../0_LDPC_original/src/decoder.cpp#L7059-L7067) |
| 모든 그룹의 `iter_start` 최댓값 | 105 (≤ 120) | 확인됨 | 파일의 18번째 칸 전수 (1, 2, 1, 5, 5, 6, 9, 25, 45, 65, 85, 105) |
| 진입 프레임이 못 쓰는 것 | **iteration 번호 121, 122, 123, 124 네 개** | 확인됨 | ㉰의 mn 수열 |
| 진입 프레임이 못 쓰는 **row** | **없음** | 반박됨 | 파일은 row가 77개뿐이고 iteration으로 index되지 않는다. 그룹 11은 CSW로 row를 고르므로 105~120 구간에서 13개 row 모두 선택 가능하다 |

**반박: "파일의 121~124 row"는 실체가 없다.** 파일에는 77개 row가 있고 iteration 번호로 row를 세지 않는다. 실제로 생기는 것은 ㉠ 진입 프레임이 그룹 11의 마지막 20 iteration 중 16회만 돈다는 비대칭과, ㉡ 진입 프레임과 미진입 프레임이 같은 120회를 돌되 진입 프레임은 그 중 4회를 1bit precision에 쓴다는 차이다. 어느 LLR row도 도달 불가가 되지 않는다.

**H5-C 종합 판정: 확인됨** (iteration 수 124→120, 두 갈래 모두 120회). 다만 "121~124 row 미도달"이라는 표현은 **반박됨**이므로 문서에 옮길 때 "iteration 번호 121~124"로 고쳐야 한다.

---

## 4. 가설 H5-D: mn 0 종료와 `iter_num` -4 (이번 검증의 핵심)

> `Check_End_Iter`가 mn 0에서 복호 성공을 돌려주면 `iter_num`이 0이 되고 1973-1979의 보정이 4를 빼서 -4가 된다.

**판정: 반박됨. mn 0 종료는 코드상 불가능한 경로다.**

### ㉮ mn 0 루프의 흐름

메인 루프 본문 끝부분([decoder.cpp:1946-1971](../../../../../../0_LDPC_original/src/decoder.cpp#L1946-L1971))을 그대로 옮기면 이렇다.

```cpp
/* Check CRC done */
if (mn == 0) {
    CRC_flag = FLAG_HIGH; // 0번째 crc 체크는 무조건 실패하도록 setting
}
else {
    if (TRUE == Check_End_Iter(&mn)) { ... break; }
}
/* Power stopping algorithm (Part 3) */
if (MODE_POWER_STOPPING_ON == m_param_dec->power_index) {
    if (TRUE == Jump_Iter(&mn)) { break; }
}
real_mn++;
/* HBF algorithm (Part 1) */
if (mn == 0) { Select_BF(); }
```

| 항목 | 내용 | 판정 | 근거 |
|------|------|------|------|
| mn 0에서 `Check_End_Iter` 호출 여부 | **불리지 않는다.** 1947-1949가 mn 0을 가로채 `CRC_flag = FLAG_HIGH`만 세운다 | 확인됨 | [decoder.cpp:1947-1949](../../../../../../0_LDPC_original/src/decoder.cpp#L1947-L1949). 주석도 "0번째 crc 체크는 무조건 실패하도록 setting" |
| 메인 mn 루프의 `break` 전수 | 1957(`Check_End_Iter`)과 1963(`Jump_Iter`) 둘뿐 | 확인됨 | 1120-1971 구간에서 들여쓰기 12칸 이하의 `break;`를 전수 검색한 결과 1805행 하나가 나왔고, 그것은 안쪽 clk 루프의 종료다 ([decoder.cpp:1803-1807](../../../../../../0_LDPC_original/src/decoder.cpp#L1803-L1807)) |
| mn 0에서 `Jump_Iter`가 TRUE를 돌려줄 수 있는가 | **없다.** 첫 관문 `flag_dec_1iter == FLAG_HIGH`는 프레임 시작에 LOW이고 HIGH로 바뀌는 곳이 모두 `__4_BIT_LLR__` 안이다. HD 갈래(4973-4983)는 `jump_flag`와 CSW만 건드리고 `mn`도 `iter_num`도 바꾸지 않은 채 5298행에서 FALSE를 돌려준다 | 확인됨 | [decoder.cpp:4954-4983](../../../../../../0_LDPC_original/src/decoder.cpp#L4954-L4983), [5297-5298](../../../../../../0_LDPC_original/src/decoder.cpp#L5297-L5298), [mode.h:12](../../../../../../0_LDPC_original/src/mode.h#L12) |

### ㉯ `real_mn`과 5315행 색인

| 항목 | 값 | 판정 | 근거 |
|------|-----|------|------|
| 초기값 | `real_mn = 0` (프레임마다 `Clear_Flag`에서) | 확인됨 | [decoder.cpp:608](../../../../../../0_LDPC_original/src/decoder.cpp#L608), 호출 [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp#L1091) |
| 증가 지점 | 1966행, `Check_End_Iter` **뒤**, `Select_BF` **앞** | 확인됨 | [decoder.cpp:1966](../../../../../../0_LDPC_original/src/decoder.cpp#L1966) |
| mn 0 본문이 끝났을 때 | `real_mn = 1` | 확인됨 | mn 0에서는 `Check_End_Iter`를 건너뛰고 1966행만 실행 |
| 첫 `Check_End_Iter` 호출 시 `real_mn` | 1 (진입 프레임 mn 1, 미진입 프레임 mn 5, 둘 다 real_mn 1) | 확인됨 | 위 흐름 |
| 5315행 색인 `CRC_LEN * (real_mn - 1)` | 최소 0. **음수가 되지 않는다** | 확인됨 | [decoder.cpp:5315](../../../../../../0_LDPC_original/src/decoder.cpp#L5315) |
| 버퍼 크기 | `MN_max * CRC_LEN`, `MN_max = MN[MN_num-1] + ITER_MAX_HBF` = 120 + 4 = 124 | 확인됨 | [decoder.cpp:564-565](../../../../../../0_LDPC_original/src/decoder.cpp#L564-L565). `Read_LLR_info_Auto`가 `Init_ECC_Top`보다 먼저 돌아 보정된 `MN[]`을 쓴다 ([local_opt.cpp:34, 46](../../../../../../0_LDPC_original/src/local_opt.cpp#L34-L46)) |
| `real_mn` 최댓값 | 120 (두 갈래 모두 본문 실행 121회, 마지막 `Check_End_Iter` 시점의 값은 120) | 확인됨 | ㉰의 mn 수열 |
| 색인 상한 | `80*(120-1)+79 = 9599 < 124*80 = 9920` | 확인됨 | 넘치지 않는다 |

`real_mn`은 "실제로 돈 본문 수"라 미진입 프레임에서도 1부터 센다. `mn`이 5로 뛰어도 `real_mn`은 뛰지 않으므로 5315행의 색인은 안전하다.

### ㉰ 5344행과 5355행이 `iter_num`에 넣는 값

| 줄 | 대입 | 조건 | 판정 |
|----|------|------|------|
| 5344 | `iter_num = mn` | 복호 성공(`FLAG_LOW == failure_flag`) | 확인됨 |
| 5355 | `iter_num = mn` (직전 5350-5354에서 `mn == MN`이고 `flag_dec_1iter`가 HIGH면 `mn = MN_old`) | 상한 도달 실패 | 확인됨 |

두 대입 모두 그 시점의 `mn`이고, `Check_End_Iter`는 `mn >= 1`에서만 불리므로 `iter_num >= 1`이다. 미진입 프레임은 `mn >= 5`이므로 `iter_num >= 5`다.
`MN_old`는 `__4_BIT_LLR__` 안에서만 대입되므로 이 빌드에서는 5353행이 실행되지 않는다.

### ㉱ 1973-1979행 보정의 조건

```cpp
if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
    if ((MODE_DEC_HD == m_param_dec->init_n || MODE_DEC_1_5SD == m_param_dec->init_n)) {
        if (FLAG_LOW == flag_BF_on) {
            iter_num -= ITER_MAX_HBF;
        }
    }
}
```

| 조건 | 내용 | DAO 설정에서 | 판정 |
|------|------|-------------|------|
| `matrix_sel` | `LAYOUT_PRIME_512B_TLC_VSS_OFF`(1)일 때만 | `matrix_sel = 1`이라 **성립** | 확인됨 ([DAO_Config.py:170](../../../../../SRC/DAO_Config.py#L170)) |
| `init_n` | HD(1) 또는 1.5SD(4) | `init_n = 1`이라 **성립** | 확인됨 ([DAO_Config.py:171](../../../../../SRC/DAO_Config.py#L171)) |
| `flag_BF_on` | **LOW일 때만 뺀다** (BF 진입 프레임은 빼지 않는다) | 프레임마다 다름 | 확인됨 ([decoder.cpp:1975](../../../../../../0_LDPC_original/src/decoder.cpp#L1975)) |

즉 보정은 미진입 프레임에만 걸리고, 그 프레임의 `iter_num`은 최소 5이므로 결과는 최소 1이다.

### ㉲ 결론

| 값 | 도달 가능성 | 근거 |
|----|------------|------|
| `iter_num == 0` | **불가능** | mn 0에서 `Check_End_Iter`가 불리지 않고([decoder.cpp:1947-1949](../../../../../../0_LDPC_original/src/decoder.cpp#L1947-L1949)), `Jump_Iter`는 이 빌드에서 TRUE를 돌려줄 수 없으며([decoder.cpp:4958](../../../../../../0_LDPC_original/src/decoder.cpp#L4958), `__4_BIT_LLR__` off), 메인 루프에 다른 탈출구가 없다(전수 확인) |
| `iter_num == -4` | **불가능** | 위와 같음 |
| 미진입 프레임의 `iter_num` 최솟값 | 5 - 4 = **1** | ㉰, ㉱ |
| 진입 프레임의 `iter_num` 최솟값 | **1** (보정 없음) | ㉱ |

**반박됨.** R2-5의 "mn 0에서 끝나는 프레임은 `iter_num`이 -4가 된다(도달 가능성 미확정)"는 코드 근거로 배제된다. Round 2 처방 가운데 "mn 0 종료 경로에서 보정을 건너뛴다"는 **필요 없는 처방**이며, 넣으면 존재하지 않는 경우를 위한 죽은 조건이 하나 늘어난다.

확정을 막는 요소는 없다. 다만 이 결론은 저장소의 `mode.h` 기준이며, 외부 빌드가 `__4_BIT_LLR__`을 켜면 `Jump_Iter`의 2SD/3SD 갈래가 살아난다. 그 갈래들도 `MODE_DEC_2SD`/`MODE_DEC_3SD` 전용이라 HD 경로에는 닿지 않고, 그 안의 첫 조건도 `mn > 0`이다([decoder.cpp:4994](../../../../../../0_LDPC_original/src/decoder.cpp#L4994)). 따라서 HD에 대한 결론은 그 경우에도 유지된다.

---

## 5. 가설 H5-E: DAO가 읽는 값

**판정: 확인됨 (다만 읽는 위치는 지시문의 7969-7999가 아니라 8187-8273)**

### ㉮ 결과 파일 파싱 코드

지시문이 가리킨 [DAO_Main.py:7969-7999](../../../../../SRC/DAO_Main.py#L7969-L7999)의 `Read_FER_From_File`은 **호출처가 없다** (grep 전수: 정의 한 곳뿐). 실제로 쓰이는 파서는 `Read_Ref_C_Result`다.

```python
if REFC_CONFIG.ch_type in (1, 2):
    base_offset = 1
elif REFC_CONFIG.ch_type == 3:
    base_offset = 3
...
    result_offset = base_offset
    num_test = int(parts[result_offset]); result_offset += 1
    num_error = int(parts[result_offset]); result_offset += 1
    avg_iteration = float(parts[result_offset]); result_offset += 1
    num_iteration = avg_iteration * num_test
    ...
    arr = np.array(parts[result_offset:-3], dtype='f8')
    num_error_per_iteration = np.round(arr * num_test).astype('f8')
```

([DAO_Main.py:8198-8248](../../../../../SRC/DAO_Main.py#L8198-L8248), 호출 [1824](../../../../../SRC/DAO_Main.py#L1824)와 [1851](../../../../../SRC/DAO_Main.py#L1851))

읽는 파일은 [DAO_Main.py:1604-1628](../../../../../SRC/DAO_Main.py#L1604-L1628)의 `result_4KB_S_{mode_scenario}_H_{matrix_sel}_CH_{ch_type}_E..._init_n_{init_n}_seed_{proc}.txt`이며, C++의 `str_result_name_4KB`([main.cpp:698](../../../../../../0_LDPC_original/src/main.cpp#L698) `result_4KB_S_%d_%s.txt`)와 일치한다. 확인됨.

### ㉯ 읽은 값이 우열 판정에 쓰이는 경로

| 값 | 파싱 위치 | 소비처 | 판정 |
|----|----------|--------|------|
| `num_test` | `parts[base_offset]` | `total_tests` → FER 분모 ([DAO_Main.py:1885](../../../../../SRC/DAO_Main.py#L1885)) | 확인됨 |
| `num_error` | `parts[base_offset+1]` | `total_errors` → `FER_value = total_errors / total_tests` → `matrix.FERs[ch_idx]` ([1885, 1918-1932](../../../../../SRC/DAO_Main.py#L1885-L1932)) | 확인됨 |
| `avg_iteration` | `parts[base_offset+2]` | `num_iteration = avg_iteration * num_test` → 합산 → `avg_iteration = total_iterations / total_tests` → `matrix.avg_iterations[ch_idx]` ([1886, 1934-1937](../../../../../SRC/DAO_Main.py#L1886-L1937)) | 확인됨 |
| FER 배열 | `parts[base_offset+3:-3]` | `total_num_error_per_iters`, `total_FER_per_iters`. **소비처는 로그 출력뿐** ([7595-7596](../../../../../SRC/DAO_Main.py#L7595-L7596)). 우열 판정에 쓰이지 않는다 (grep 전수) | 확인됨 |

우열 판정:

- ㉠ 1순위는 항상 FER이다 ([DAO_Main.py:2537](../../../../../SRC/DAO_Main.py#L2536-L2538), [6066-6073](../../../../../SRC/DAO_Main.py#L6065-L6074))
- ㉡ `avg_iterations`는 FER 동점일 때만 쓰인다. 일반 갱신 판정에서는 `DAO_CONFIG.ENABLE_AVG_ITER_UPDATE`가 **기본 False**라 쓰이지 않는다 ([DAO_Config.py:136](../../../../../SRC/DAO_Config.py#L136), [DAO_Main.py:2541-2544](../../../../../SRC/DAO_Main.py#L2540-L2544))
- ㉢ REORDER_GROUP 모드의 후보 비교에서는 설정과 무관하게 FER 동점 시 `avg_iterations`가 **큰 쪽**을 고른다 ([DAO_Main.py:6076-6085](../../../../../SRC/DAO_Main.py#L6076-L6085)). 동점 판정에도 쓰인다 ([6113-6116](../../../../../SRC/DAO_Main.py#L6113-L6116))

### ㉰ `avg_iteration`을 만드는 C++ 쪽 코드와의 대응

| 단계 | 코드 | 판정 |
|------|------|------|
| 프레임별 값 | `iter_effective = (double)o_iter_num;` 이후 복호 성공이고 HD이며 partial CRC면 0.75/0.5/0.25를 뺀다 | 확인됨 ([ecc_top.cpp:887-898](../../../../../../0_LDPC_original/src/ecc_top.cpp#L887-L898)) |
| 합 | `iter_sum += iter_effective;` | 확인됨 ([ecc_top.cpp:900](../../../../../../0_LDPC_original/src/ecc_top.cpp#L900)) |
| 출력 | `avg_iter = iter_sum / rn;` 를 `rn`, `fr[MN_num-1]` 다음 세 번째 칸에 찍는다 | 확인됨 ([ecc_top.cpp:2152, 2200-2202](../../../../../../0_LDPC_original/src/ecc_top.cpp#L2200-L2202)) |
| DAO 열 대응 | `parts[base_offset+2]`가 바로 이 칸이다 (선행 칸은 채널 필드 1개 또는 3개, `rn`, `fr[MN_num-1]`) | 확인됨. C++의 채널 필드 수와 DAO의 `base_offset` 규칙이 일치한다 ([ecc_top.cpp:2174-2199](../../../../../../0_LDPC_original/src/ecc_top.cpp#L2174-L2199) 대 [DAO_Main.py:8198-8203](../../../../../SRC/DAO_Main.py#L8198-L8203)) |
| 후행 3칸 | `avg_clk`, `avg_clk_throughput`, `Print_Excuting_Time`의 `%dhour(s)_%dminute(s)_%dsec(s)` | 확인됨. DAO의 `parts[result_offset:-3]`과 정확히 맞는다 ([ecc_top.cpp:2209-2213](../../../../../../0_LDPC_original/src/ecc_top.cpp#L2209-L2213), [common.cpp:93-95](../../../../../../0_LDPC_original/src/common.cpp#L93-L95)) |

**`iter_num -= ITER_MAX_HBF`가 살아나면 `avg_iteration`이 바뀐다는 주장은 확인됨.** 변화량은 정확히 `4 × (BF 미진입 프레임 비율)`이다 (partial CRC 보정은 그대로).

### ㉱ FER 열의 DAO 노출

| 항목 | 내용 | 판정 |
|------|------|------|
| DAO가 FER 배열을 읽는가 | 읽는다 (`arr`) | 확인됨 |
| 배열 길이 기대값 | `matrix.max_iteration = groups[-1][-1].iter_end` = 124 = `MN_num` | 확인됨 ([DAO_LLR_MATRIX.py:441](../../../../../SRC/DAO_LLR_MATRIX.py#L441), [DAO_Main.py:1809-1813](../../../../../SRC/DAO_Main.py#L1809-L1813)) |
| 길이가 바뀌는가 | **바뀌지 않는다.** `MN_num`은 124로 그대로이고 값만 바뀐다 | 확인됨 |
| 1.0 고정 열의 노출 | `total_FER_per_iters`에 1.0이 넉 칸 들어가고 로그에만 찍힌다. 판정에는 쓰이지 않는다 | 확인됨 |
| 판정용 FER의 오염 여부 | **없다.** `matrix.FERs`는 `parts[base_offset+1]` = `fr[MN_num-1]`에서 오고, 이 칸은 877-879행의 `MN[]` 비교 loop 밖에서 CRC 실패만 센다 | 확인됨 ([ecc_top.cpp:874-877](../../../../../../0_LDPC_original/src/ecc_top.cpp#L874-L877)) |

---

## 6. 종합 판정

| 가설 | 판정 | 요지 |
|------|------|------|
| H5-A `MN[]` 값 | **부분 확인** | 배열 `[4, -3, -2, -1, 0, ..., 118, 120]`은 확인됨. `MN_num`은 125가 아니라 **124** (반박). 손 실행은 변환된 파일을 전제로 한다 |
| H5-B FER 열과 머리글 | **부분 확인** | 머리글 음수 확인됨. 1.0 고정 열은 셋이 아니라 **넷**(index 1~4, `MN[4] = 0` 포함). 원본에서도 이미 한 칸(index 0)이 1.0이므로 실제 변화는 1개→4개. 음수 머리글은 **DAO가 읽지 않는 파일**(`Ref_C_result_*.txt`)에만 들어간다 |
| H5-C iteration 수 | **확인됨** | 124회→120회, 두 갈래 모두 120회. 다만 "121~124 **row** 미도달"은 **반박** (파일 row는 77개이고 iteration으로 색인되지 않는다). 실체는 iteration 번호 4개 미사용이며 도달 불가가 되는 row는 없다 |
| H5-D mn 0 종료와 -4 | **반박됨** | `Check_End_Iter`는 mn 0에서 불리지 않고([decoder.cpp:1947-1949](../../../../../../0_LDPC_original/src/decoder.cpp#L1947-L1949)) `Jump_Iter`는 이 빌드에서 TRUE를 못 돌려주며 다른 탈출구가 없다. `iter_num >= 1`이 항상 성립. `real_mn`도 항상 1 이상이라 5315행 색인도 안전 |
| H5-E DAO가 읽는 값 | **확인됨** | `avg_iteration`이 `iter_num` 보정에 그대로 흔들린다. FER 판정값은 흔들리지 않는다. 실제 파서는 `Read_Ref_C_Result`(8187-8273)이고 `Read_FER_From_File`(7969-7999)은 호출처가 없다 |

---

## 7. 심각도 재판정 제안

**R2-5를 HIGH에서 MEDIUM으로 내릴 것을 제안한다.** 근거는 다음 셋이다.

- ㉮ DAO의 갱신 판정을 직접 깨는 요소가 없다. 판정 1순위인 FER은 `fr[MN_num-1]`(CRC 실패 수)에서 오고 `MN[]` 값과 무관하다. FER 배열의 1.0 고정 열은 로그 출력에만 쓰인다
- ㉯ 음수 머리글은 사람이 읽는 `Ref_C_result_*.txt`에만 들어가고, DAO가 파싱하는 `result_4KB_S_*.txt`에는 AUTO 빌드에서 머리글을 쓰는 코드가 컴파일되지 않는다
- ㉰ 가장 위험해 보이던 항목(`iter_num` -4)이 도달 불가로 확정됐다

다만 아래는 남는다.

- ㉠ `avg_iteration`의 척도가 바뀐다. `ENABLE_AVG_ITER_UPDATE`가 켜지거나 REORDER_GROUP 모드를 쓰면 FER 동점 시 판정에 들어가며, **이전 실행의 결과와 이후 실행의 결과를 같은 자로 비교할 수 없게 된다**. 특히 REORDER_GROUP은 큰 `avg_iteration`을 좋다고 보므로([DAO_Main.py:6082](../../../../../SRC/DAO_Main.py#L6076-L6085)), 미진입 프레임 비율이 높은 파라미터가 4만큼 손해를 본다
- ㉡ 실행 iteration이 124회에서 120회로 줄어 성능 자체가 달라진다. 이는 결과 파일 형식 문제가 아니라 **동작 변경**이며 R2-5보다 넓은 문제다
- ㉢ FER 열의 뜻이 열 0에서 뒤집힌다 (iteration 0 기준에서 iteration 4 기준으로). 머리글이 단조 증가를 잃어 사람이 열을 잘못 읽기 쉽다

---

## 8. 처방 검토

Round 2 처방: "㉮ 보정식을 음수가 안 나오게 고치거나 ㉯ AUTO에서도 검사점 5개로 바꾸거나 ㉰ 배열을 두고 열 배치를 문서에 적는다. mn 0 종료 경로에서 보정을 건너뛴다"

| 갈래 | 판정 | 근거 |
|------|------|------|
| ㉮ 보정식을 고친다 | **처방 수정 필요** | 음수를 없애는 가장 단순한 식은 124-131행의 두 보정 중 **125-127행(전 원소 빼기)만 지우고 `MN[0] = ITER_MAX_HBF`만 남기는 것**이다. 그러면 `MN = [4, 1, 2, ..., 122, 124]`가 되어 음수와 중복 0이 사라지고 `MN[MN_num-1]`이 124로 남는다. 그런데 그 값이 그대로 메인 루프 상한이 되므로([decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp#L1118)) 미진입 프레임이 mn 128까지 돌아 R2-15가 지적한 문제로 되돌아간다. 음수 제거와 상한 유지를 함께 이루려면 `MN[MN_num-1]`만 `iter_end - ITER_MAX_HBF`로 낮추고 나머지 칸은 그대로 두는 식이 필요하며, 이는 문서에 명시적으로 적어야 한다. DAO 파싱은 열 수(124)가 유지되므로 이 갈래에서 깨지지 않는다 |
| ㉯ 검사점 5개로 바꾼다 | **처방 반대** | 열 수가 124에서 5로 바뀌면 DAO의 `arr` 길이가 `matrix.max_iteration`(124)과 어긋난다. [DAO_Main.py:1832-1833](../../../../../SRC/DAO_Main.py#L1832-L1833)이 길이 불일치를 잘라 넘기긴 하나, `parts[result_offset:-3]` 슬라이스 자체는 성립하므로 조용히 잘린 데이터가 로그에 남는다. 판정값은 안 깨지지만 이득이 없고 로그가 왜곡되므로 권하지 않는다 |
| ㉰ 열 배치를 문서에 적는다 | **처방 유효** | 열 0의 뜻이 "iteration 4 초과 비율"로 바뀌고 열 1~4가 항상 1.0이라는 사실을 적으면 로그를 읽는 사람이 헤매지 않는다. 코드 위험은 없다. 다만 "열 셋"이 아니라 **"열 넷"**으로 적어야 한다 |
| "mn 0 종료 경로에서 보정을 건너뛴다" | **처방 반대** | 4절에서 mn 0 종료가 불가능함이 확정됐다. 이 조건을 넣으면 절대 참이 되지 않는 분기가 하나 늘어난다 |
| 추가 제안 | | R2-5의 실질 위험은 `avg_iteration` 척도 변경이다. 처방에 **"`ITER_MAX_HBF` 4 적용 전후의 `avg_iteration`은 서로 비교할 수 없다. 적용 시점에 기준 실험을 다시 잡는다"**를 넣는 것이 열 배치 문서화보다 우선이다 |

---

## 9. 미확인으로 남은 것과 인접 발견

- ㉮ H5-A의 손 실행은 **3.2 파서용으로 변환된 파일**을 전제한다. 변환 절차와 변환된 파일이 없다는 것이 R2-6이며, 변환 전 파일로는 `iter_end[76]`이 확정되지 않아 `MN_num` 자체가 미정이 된다. 두 발견은 묶여 있다
- ㉯ [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp#L124)의 `MODE_DEC_1_SSD`는 저장소에 정의가 없어(grep 전수, 소스 히트 한 곳) 이 저장소의 소스 그대로는 컴파일되지 않는다. 외부 소스의 이 줄이 무엇인지는 이 환경에서 확정할 수 없다. R2-15의 제안대로 `MODE_DEC_1_5SD`로 고치면 1.5SD도 보정을 받게 되는데, 지금 상태(1.5SD가 조건 밖)에서는 1.5SD 프레임이 `MN` 124에 `Select_BF`의 +4로 mn 128까지 돌아 `Get_Cur_LLR_Idx_FILE`에서 `selected_group`이 -1로 남고, [decoder.cpp:7051](../../../../../../0_LDPC_original/src/decoder.cpp#L7048-L7051)이 `type_each_group[-1]`을 읽는 범위 밖 접근이 된다. DAO는 `init_n` 1이라 이 경로를 타지 않지만, R2-15 처방의 근거로 쓸 수 있다
- ㉰ 현재 파일의 `type_each_group` 값 `20 20 21 20 21 21 1 1 1 1 1 1`에서 앞 여섯은 `GROUP_TYPE_ITER`(0)도 `GROUP_TYPE_CSW`(1)도 아니다. 현행 파서와 현행 `Get_Cur_LLR_Idx_FILE`([decoder.cpp:7051-7068](../../../../../../0_LDPC_original/src/decoder.cpp#L7051-L7068))로는 그룹 0~5가 선택될 때 `table_row_idx`가 초기값 0으로 남는다. Round 2가 R2-4에서 적은 "현 파일 결과는 항상 첫 row"와 일치한다. 이 항목은 R2-3, R2-6의 영역이라 판정하지 않고 관찰만 적는다
