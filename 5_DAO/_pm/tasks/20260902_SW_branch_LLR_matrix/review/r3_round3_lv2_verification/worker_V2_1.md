# Round 3 검증: 팀 V2 워커 1 (R2-3, R2-10)

작성: 2026-09-03 01:40:34

검증 대상은 코드 수정 계획 문서다. C++ 소스는 수정되지 않았고 빌드도 하지 않았다.
아래 손 실행은 [code_diff.md](../../code_diff.md)의 수정 후 코드를 종이 위에서 실행한 결과다.

참조 파일:
[local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp),
[decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp),
[decoder.h](../../../../../../0_LDPC_original/src/decoder.h),
[common.h](../../../../../../0_LDPC_original/src/common.h),
[mode.h](../../../../../../0_LDPC_original/src/mode.h),
[ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp),
[main.cpp](../../../../../../0_LDPC_original/src/main.cpp),
[msg1.md](../../../../../../msg1.md),
[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt),
[LLR_MATRIX_0.txt](../../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt)

---

## ㉮ 가설별 판정 요약

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| A (R2-3 사실): 구간 번호의 뜻이 파서와 디코더에서 다르다 | **확인됨** | 배경 메모 예시 헤더 `-1 0 1 2 -1`을 [code_diff 3.2](../../code_diff.md#ch3) 파서에 넣으면 iteration 5~8 구간이 span 0이 되고, [decoder.h 수정 후 165행 주석](../../code_diff.md#ch2)과 [code_diff 4.1](../../code_diff.md#ch4)이 span 0을 iteration 1~4로 못박아 문턱 130을 쓴다. 손 실행 2 참조 |
| A 부속 주장 ㉠: BF 진입 프레임이 5~8 분기를 문턱 130으로 고른다 | **확인됨** | `syn_th_sw_branch[0][0] = SW_TH_BF1_512B_TLC_OFF = 130` ([common.h:237](../../../../../../0_LDPC_original/src/common.h)) |
| A 부속 주장 ㉡: BF 미진입 프레임은 `cur_sw_branch_idx[0]`이 0에 고정된다 | **확인됨** | [code_diff 5.1](../../code_diff.md#ch5) 수정 후 `Select_BF`의 `else` 갈래가 `cur_sw_branch_idx[1]`만 채운다. 앞머리 초기화로 `[0]`은 0 |
| A 부속 주장 ㉢: 분기 2가 어떤 프레임에서도 선택되지 않는다 | **확인됨** | `num_sw_branch[0] = 2`이므로 `Select_SW_Branch(0, w)`의 반환값은 0 또는 1뿐이다. 손 실행 2 ㉯ 참조 |
| A 부속 주장 ㉣: 오류 출력이 없다 | **확인됨** | iteration 5~8에서 그룹 1 또는 2가 늘 뽑혀 `selected_group != -1`이다. `[Error] @Cur_LLR_IDX (1)`은 나오지 않는다 |
| A 부속 주장 ㉤: 현 파일에서는 우연히 맞는다 | **확인됨** | 손 실행 1에서 span 0이 iteration 1~4, span 1이 5~8과 일치한다 |
| A-처방1 (구간별 `iter_start` 기록 후 범위로 문턱 선택) | **부분 확인 (처방 수정 필요)** | 손 실행 5에서 메모 예시와 현 파일 양쪽의 구간 대응이 바로잡힌다. 다만 ㉠ 파서 안 계산 위치가 틀리고 ㉡ 분기 3개는 여전히 못 고르며 ㉢ 비AUTO 빌드에서 미초기화 포인터를 역참조한다 |
| A-처방2 (구간 0의 시작이 1이 아니면 오류) | **반박됨 (처방 반대)** | 배경 메모가 유효하다고 제시한 형태([msg1.md:29-34](../../../../../../msg1.md))를 거부한다. 손 실행 5 참조 |
| B (R2-10 사실): 첫 분기 그룹 index가 0이 아니면 span이 -1 | **확인됨** | 구 파일을 토큰 순서로 손 실행하면 분기 줄이 `1 2 31`로 읽히고 세 그룹 모두 span이 -1이다. 손 실행 3 참조 |
| B 부속 주장: 6.1이 `cur_sw_branch_idx[-1]`을 읽는다 | **확인됨** | [code_diff 6.1](../../code_diff.md#ch6) 수정 후 루프에 `span` 범위 검사가 없다 |
| B-처방 (검사 셋 3개와 6.1 방어) | **부분 확인 (처방 수정 필요)** | 메모 예시 헤더는 검사 셋을 오류 없이 통과한다. 다만 ㉠ 오류가 흐름을 멈추지 않고 ㉡ 방어에 걸렸을 때의 동작이 정해져 있지 않으며 ㉢ 배치 뒤집기(손 실행 4)를 잡지 못한다 |

심각도 재판정: R2-3은 HIGH 유지가 타당하다. 오류 출력 없이 잘못된 LLR 파라미터가 쓰이고, 최적화기가 그 결과를 정답으로 받아들이기 때문이다. R2-10은 MEDIUM에서 **HIGH로 올릴 근거**가 있다. 손 실행 4에서 같은 구간의 분기 순서를 바꾸기만 해도 span이 -1이 되어 배열 밖 접근이 일어나므로, 발동 조건이 구 파일이라는 특수 사례에 한정되지 않는다.

---

## ㉯ 손 실행

파서 3.2의 구간 번호 계산 규칙 (수정 후 코드 그대로):

```
num_sw_span = 0; prev_branch = SW_BRANCH_NONE(-1);
for i in 0 .. num_group-1:
    b = sw_branch_idx_each_group[i]
    if b == -1: span[i] = -1
    else:
        if (b == 0 && prev_branch != 0): num_sw_span++
        span[i] = num_sw_span - 1
    prev_branch = b
```

### 손 실행 1: 현 파일의 변환 후 헤더

입력은 상위 문서 4장 ㉮가 제안하는 분기 줄 `0 0 1 0 1 1 -1 -1 -1 -1 -1 -1` (그룹 12개)이다.

| 그룹 i | b | prev_branch (그 시점) | 증가 조건 성립 | num_sw_span (갱신 후) | sw_span_idx_each_group[i] |
|--------|---|----------------------|---------------|----------------------|--------------------------|
| 0 | 0 | -1 | 예 | 1 | 0 |
| 1 | 0 | 0 | 아니오 | 1 | 0 |
| 2 | 1 | 0 | 아니오 | 1 | 0 |
| 3 | 0 | 1 | 예 | 2 | 1 |
| 4 | 1 | 0 | 아니오 | 2 | 1 |
| 5 | 1 | 1 | 아니오 | 2 | 1 |
| 6 | -1 | 1 | 해당 없음 | 2 | -1 |
| 7 | -1 | -1 | 해당 없음 | 2 | -1 |
| 8 | -1 | -1 | 해당 없음 | 2 | -1 |
| 9 | -1 | -1 | 해당 없음 | 2 | -1 |
| 10 | -1 | -1 | 해당 없음 | 2 | -1 |
| 11 | -1 | -1 | 해당 없음 | 2 | -1 |

판정: [code_diff 3.2](../../code_diff.md#ch3)에 실린 결과 표(그룹 0과 1은 구간 0, 그룹 2는 구간 0, 그룹 3은 구간 1, 그룹 4와 5는 구간 1, 그룹 6부터 11은 -1)와 **일치한다**. `num_sw_span = 2`이다.

파일의 그룹별 iteration 범위를 [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) row에서 직접 읽으면 span 0은 iteration 1~4(그룹 0은 1~1, 그룹 1은 2~4, 그룹 2는 1~4), span 1은 iteration 5~8(그룹 3은 5~8, 그룹 4는 5~5, 그룹 5는 6~8)이다. [decoder.h 수정 후 주석](../../code_diff.md#ch2)의 "span 0 = iteration 1~4, span 1 = iteration 5~8"과 우연히 맞는다.

### 손 실행 2: 배경 메모 예시 헤더

[msg1.md:29-34](../../../../../../msg1.md)의 `iter start/iter end/flag` 표(`1/4/-1`, `5/8/0`, `5/8/1`, `5/8/2`)를 4장 ㉮ 표기로 옮긴 그룹 배치는 다음과 같다.

| 그룹 | iteration | 분기 index | 비고 |
|------|-----------|-----------|------|
| 0 | 1~4 | -1 | 분기 없음 |
| 1 | 5~8 | 0 | |
| 2 | 5~8 | 1 | |
| 3 | 5~8 | 2 | |
| 4 | 9 이후 | -1 | 분기 없음 |

분기 줄은 `-1 0 1 2 -1`이다. 파서 3.2 손 실행:

| 그룹 i | b | prev_branch (그 시점) | 증가 조건 성립 | num_sw_span (갱신 후) | sw_span_idx_each_group[i] |
|--------|---|----------------------|---------------|----------------------|--------------------------|
| 0 | -1 | -1 | 해당 없음 | 0 | -1 |
| 1 | 0 | -1 | 예 | 1 | 0 |
| 2 | 1 | 0 | 아니오 | 1 | 0 |
| 3 | 2 | 1 | 아니오 | 1 | 0 |
| 4 | -1 | 2 | 해당 없음 | 1 | -1 |

**iteration 5~8 구간이 span 0이 된다.** `num_sw_span = 1`이다.

#### ㉮ 4.1이 채우는 실제 값

[mode.h:11](../../../../../../0_LDPC_original/src/mode.h)의 `__12META__`가 주석 처리되어 있으므로 [common.h:228-252](../../../../../../0_LDPC_original/src/common.h)의 `#else` 갈래가 쓰인다. `LAYOUT_PRIME_512B_TLC_VSS_OFF`는 [common.h:193](../../../../../../0_LDPC_original/src/common.h)에서 1이다.

| 변수 | 값 | 출처 |
|------|-----|------|
| `syn_th_BF0` | 680 | `SW_TH_BF0_512B_TLC_OFF` (common.h:236) |
| `num_sw_branch[0]` | 2 | code_diff 4.1 |
| `syn_th_sw_branch[0][0]` | 130 | `SW_TH_BF1_512B_TLC_OFF` (common.h:237) |
| `num_sw_branch[1]` | 2 | code_diff 4.1 |
| `syn_th_sw_branch[1][0]` | 1100 | `SW_TH_5_8_SET0_512B_TLC_OFF` (common.h:244) |
| `num_sw_branch[2]`, `num_sw_branch[3]` | 1 | 4.1 앞머리 초기화 반복문 |
| `syn_th_sw_branch[2][*]`, `[3][*]` | 0 | 같은 반복문 |

참고로 `default` 갈래는 `num_sw_branch[0] = 1`, `num_sw_branch[1] = 2`, `syn_th_sw_branch[1][0] = SW_TH_5_8_SET0_DEFAULT = 960`(common.h:240)이다. `SW_TH_5_8_SET1_512B_TLC_OFF`는 950(common.h:251), `SW_TH_5_8_SET1_DEFAULT`는 950(common.h:247)이며 4.1은 이 둘을 어디에도 넣지 않는다.

#### ㉯ 5.1 `Select_BF` 손 실행

전제: `MODE_DEC_HD == init_n`, `BF_mode == MODE_BF_ON`([main.cpp:232](../../../../../../0_LDPC_original/src/main.cpp)), BF 진입 조건은 `syn_weight < syn_th_BF0(680)`.
`Select_SW_Branch(span, w)`는 `w < syn_th_sw_branch[span][0]`이면 0, 아니면 `num_sw_branch[span] - 1`을 돌려준다.

| syn_weight | BF 진입 | flag_BF_on | cur_sw_branch_idx[0] | cur_sw_branch_idx[1] | mn, MN 이동 |
|-----------|--------|-----------|---------------------|---------------------|-----------|
| 100 | 예 (100 < 680) | FLAG_HIGH | 0 (100 < 130) | 0 (100 < 1100) | 없음 |
| 200 | 예 (200 < 680) | FLAG_HIGH | **1** (200 >= 130) | 0 (200 < 1100) | 없음 |
| 700 | 아니오 | FLAG_LOW | **0 (고정)** | 0 (700 < 1100) | +4 |
| 1000 | 아니오 | FLAG_LOW | **0 (고정)** | 0 (1000 < 1100) | +4 |
| 1200 | 아니오 | FLAG_LOW | **0 (고정)** | 1 (1200 >= 1100) | +4 |

#### ㉰ 6.1 그룹 선택 손 실행

메모 예시에서 분기가 걸린 그룹 1, 2, 3은 모두 span 0이므로 6.1이 비교하는 값은 `cur_sw_branch_idx[0]`이다. 루프는 그룹 4에서 0으로 내려간다.

| syn_weight | cur[0] | iteration 5 | iteration 6 | iteration 8 | 뽑힌 분기 | 메모 기준 옳은 분기 |
|-----------|--------|------------|------------|------------|----------|------------------|
| 100 | 0 | 그룹 1 | 그룹 1 | 그룹 1 | 0 | 0 (BF 구간) |
| 200 | 1 | 그룹 2 | 그룹 2 | 그룹 2 | 1 | **0** (SW 200 < 680이므로 BF, 5~8은 분기 0) |
| 700 | 0 | 그룹 1 | 그룹 1 | 그룹 1 | 0 | 0 (680 <= SW < 1100) |
| 1000 | 0 | 그룹 1 | 그룹 1 | 그룹 1 | 0 | 0 |
| 1200 | 0 | 그룹 1 | 그룹 1 | 그룹 1 | **0** | **1 또는 2** (SW >= 1100) |

분기 2 그룹(그룹 3)이 뽑히는 syn_weight 범위는 **존재하지 않는다**. `cur_sw_branch_idx[0]`의 치역이 `{0, 1}`이기 때문이다.
분기 1 그룹(그룹 2)이 뽑히는 범위는 `130 <= syn_weight < 680`이며, 이는 메모 기준으로 분기 0이어야 하는 구간이다.

#### ㉱ 오류 출력 여부

iteration 1~4는 그룹 0(분기 -1)이, 5~8은 그룹 1 또는 2가, 9 이후는 그룹 4가 늘 뽑히므로 `selected_group`은 어느 iteration에서도 -1이 아니다. [code_diff 6.2](../../code_diff.md#ch6)의 `[Error] @Cur_LLR_IDX (1)`은 **나오지 않는다**. 잘못된 분기가 조용히 쓰인다.

### 손 실행 3: 구 파일 헤더

[LLR_MATRIX_0.txt](../../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt)를 `fscanf("%d")` 토큰 순서로 소비한다. 파서는 [local_opt.cpp:61-115](../../../../../../0_LDPC_original/src/local_opt.cpp)에 3.2의 추가 반복문(그룹 수만큼 토큰 소비)을 84행 뒤에 끼운 상태다.

| 토큰 순번 | 값 | 파일 위치 | 담기는 곳 |
|----------|-----|----------|----------|
| 1 | 4 | 1행 | `num_para_each_set` |
| 2 | 4 | 3행 | `num_dv` (`num_col = 16`) |
| 3~6 | 11 4 3 2 | 5행 | `dv_from[0..3]` |
| 7~10 | 11 4 3 2 | 6행 | `dv_to[0..3]` |
| 11 | 3 | 8행 | `num_group` |
| 12~14 | 1 1 1 | 10행 | `num_set_each_group[0..2]` (`num_row = 3`) |
| 15~17 | 1 1 1 | 11행 | `type_each_group[0..2]` |
| **18** | **1** | **13행 (원래 `restart_num`)** | **`sw_branch_idx_each_group[0]`** |
| **19** | **2** | **15행 (원래 `restart_iter[0]`)** | **`sw_branch_idx_each_group[1]`** |
| **20** | **31** | **17행 첫 칸 (원래 `max_value[0]`)** | **`sw_branch_idx_each_group[2]`** |
| 21 | 31 | 17행 둘째 칸 | `restart_num` (31이 된다) |
| 22 이후 | 31 31 0 0 0 0 그리고 row 토큰들 | 17행 이후 | `restart_iter[0..30]`으로 31개 소비 |

분기 줄이 `1 2 31`로 읽히는 것이 **확인된다**. 이후 토큰 배치는 전부 밀려 나머지 필드도 무의미한 값이 된다.

span 계산:

| 그룹 i | b | prev_branch | b == 0 && prev != 0 | num_sw_span | span[i] |
|--------|---|-------------|--------------------|-------------|---------|
| 0 | 1 | -1 | 아니오 | 0 | **-1** (`0 - 1`) |
| 1 | 2 | 1 | 아니오 | 0 | **-1** |
| 2 | 31 | 2 | 아니오 | 0 | **-1** |

6.1이 읽는 첨자 값: 세 그룹 모두 `group_branch != SW_BRANCH_NONE`이므로 `span = -1`을 얻고 `cur_sw_branch_idx[-1]`을 읽는다. [code_diff 6.1](../../code_diff.md#ch6) 수정 후 루프에는 `span`을 첨자로 쓰기 전 검사가 없다(수정 후 코드 `int span = m_param_LLR->sw_span_idx_each_group[g];` 바로 다음 줄이 `if (group_branch != cur_sw_branch_idx[span])`이다). 배열 밖 읽기가 **확인된다**.

실제 메모리 배치에서는 [code_diff 2.2](../../code_diff.md#ch2)의 수정 후 `decoder.h`에서 `cur_sw_branch_idx[]` 바로 앞이 `syn_th_BF0`이므로 `cur_sw_branch_idx[-1]`은 680을 읽을 공산이 크다. 그러면 세 그룹이 모두 걸러지고 `selected_group = -1`이 되어 오류 출력과 `return 0`으로 빠진다. 표준상 정의되지 않은 동작이라는 사실은 그대로다.

### 손 실행 4: 배치 뒤집기

같은 구간의 분기 1 그룹을 분기 0 그룹보다 앞에 둔 헤더 `1 0 -1 -1`을 넣는다.

| 그룹 i | b | prev_branch | b == 0 && prev != 0 | num_sw_span | span[i] |
|--------|---|-------------|--------------------|-------------|---------|
| 0 | 1 | -1 | 아니오 | 0 | **-1** |
| 1 | 0 | 1 | 예 | 1 | 0 |
| 2 | -1 | 0 | 해당 없음 | 1 | -1 |
| 3 | -1 | -1 | 해당 없음 | 1 | -1 |

판정: 구간은 **1개로 세어진다**. 그러나 같은 구간에 속해야 할 그룹 0이 span -1을 받아 구 파일과 똑같은 배열 밖 접근을 일으킨다. 구간 번호 계산이 **분기 index의 등장 순서에 의존한다**는 것이 확인된다. 즉 R2-10의 발동 조건은 구 파일이라는 특수 사례가 아니라, 같은 구간 안에서 분기 0 그룹을 맨 앞에 두지 않은 모든 파일이다.

### 손 실행 5: 두 처방 갈래 재실행

#### 처방1 (파서가 구간별 `iter_start`를 기록하고 `Select_BF`가 범위로 문턱 배열을 고른다)

먼저 처방이 성립하는지 두 가지를 코드로 확인했다.

- ㉮ **구간별 `iter_start`를 얻는 방법과 계산 위치**: 구간의 `iter_start`는 그 구간에 속한 첫 그룹의 첫 row가 갖는 `iter_start` 값이다. 그 row 번호는 `num_set_each_group[]`의 앞쪽 합이다. 그런데 [code_diff 3.2](../../code_diff.md#ch3)가 span을 계산하는 자리는 [local_opt.cpp:84](../../../../../../0_LDPC_original/src/local_opt.cpp) 바로 뒤이고, `iter_start` 배열은 [local_opt.cpp:103](../../../../../../0_LDPC_original/src/local_opt.cpp)에서 할당되어 [local_opt.cpp:112](../../../../../../0_LDPC_original/src/local_opt.cpp)에서 채워진다. **그 자리에서는 `iter_start`를 읽을 수 없다.** 구간별 `iter_start` 계산은 row 읽기 반복문이 끝난 [local_opt.cpp:115](../../../../../../0_LDPC_original/src/local_opt.cpp) 뒤로 옮겨야 한다 (3.4의 대조 검사와 같은 자리)
- ㉯ **`Select_BF` 호출 시점에 `m_param_LLR`이 세워져 있는지**: AUTO 빌드에서는 세워져 있다. [local_opt.cpp:34](../../../../../../0_LDPC_original/src/local_opt.cpp)의 `Read_LLR_info_Auto`가 먼저 돌고, [local_opt.cpp:46](../../../../../../0_LDPC_original/src/local_opt.cpp)이 5인자 `Init_ECC_Top`([ecc_top.cpp:216-230](../../../../../../0_LDPC_original/src/ecc_top.cpp))을 불러 [ecc_top.cpp:228](../../../../../../0_LDPC_original/src/ecc_top.cpp)이 `Init_Dec`을 부르고, [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp)이 `m_param_LLR`을 대입한다. `Select_BF`는 복호 루프 안 [decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp)에서 불리므로 훨씬 뒤다. 다만 **비AUTO 빌드에서는 세워지지 않는다**. 4인자 `Init_ECC_Top`([ecc_top.cpp:197-210](../../../../../../0_LDPC_original/src/ecc_top.cpp))은 `m_param_LLR`을 대입하지 않은 채 [ecc_top.cpp:208](../../../../../../0_LDPC_original/src/ecc_top.cpp)에서 그대로 넘기고, `ECC_Top` 생성자([ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp))도 이 멤버를 초기화하지 않는다 (`m_param_LLR` 대입은 [ecc_top.cpp:222](../../../../../../0_LDPC_original/src/ecc_top.cpp) 한 곳뿐)

처방1을 적용한 문턱 선택 규칙을 다음처럼 놓는다. 슬롯 0은 iteration 1~4용 문턱 집합(분기 2개, 문턱 130), 슬롯 1은 iteration 5~8용 문턱 집합(분기 2개, 문턱 1100)이며, `Select_BF`는 각 구간의 `iter_start`가 어느 슬롯의 범위에 드는지로 슬롯을 고른다.

메모 예시 재실행 (구간은 하나, `iter_start = 5` 이므로 슬롯 1, 문턱 1100):

| syn_weight | BF 진입 | 고른 슬롯 | cur_sw_branch_idx[span 0] | 뽑히는 그룹 | 메모 기준 옳은 분기 | 판정 |
|-----------|--------|----------|--------------------------|------------|------------------|------|
| 100 | 예 | 1 | 0 | 그룹 1 (분기 0) | 0 | 맞음 |
| 200 | 예 | 1 | 0 | 그룹 1 (분기 0) | 0 | 맞음 (처방 전에는 분기 1을 골랐다) |
| 700 | 아니오 | 1 | 0 | 그룹 1 (분기 0) | 0 | 맞음 |
| 1000 | 아니오 | 1 | 0 | 그룹 1 (분기 0) | 0 | 맞음 |
| 1200 | 아니오 | 1 | 1 | 그룹 2 (분기 1) | 1 또는 2 | 분기 2개 한도 안에서 맞음 |

분기 2 그룹(그룹 3)은 **여전히 뽑히지 않는다**. `num_sw_branch[슬롯 1] = 2`가 4.1에 상수로 박혀 있어 `Select_SW_Branch`가 2를 돌려줄 수 없기 때문이다. 이것은 R2-9가 지적한 별개의 결함이며, 처방1만으로는 남는다.

현 파일 재실행 (구간 2개, 구간 0의 `iter_start = 1` 이므로 슬롯 0, 구간 1의 `iter_start = 5` 이므로 슬롯 1):

| iteration | cur[구간 0] | cur[구간 1] | 뽑히는 그룹 | 처방 전과 같은가 |
|-----------|------------|------------|------------|----------------|
| 3 | 0 | 해당 없음 | 1 | 같음 |
| 3 | 1 | 해당 없음 | 2 | 같음 |
| 6 | 해당 없음 | 0 | 3 | 같음 |
| 6 | 해당 없음 | 1 | 5 | 같음 |
| 20 | 해당 없음 | 해당 없음 | 6 | 같음 |

현 파일에서는 구간과 슬롯의 대응이 처방 전과 같으므로 결과가 바뀌지 않는다. 처방1은 현 파일에 무해하고 메모 예시의 구간 대응을 바로잡는다.

추가로 처방1은 BF 미진입 프레임에서 "건너뛰는 구간"을 정하는 규칙도 함께 고쳐야 한다. 5.1 수정 후 코드는 `else` 갈래에서 `cur_sw_branch_idx[1]`만 채우는데, 이때 1은 구간 번호가 아니라 "iteration 5~8"을 뜻하는 상수다. 처방1을 넣으면 이 자리도 "iteration 범위가 `ITER_MAX_HBF` 이하인 구간은 건너뛴다"로 다시 써야 한다.

#### 처방2 (구간 0의 시작이 1이 아니면 오류)

메모 예시에서 구간 0은 iteration 5~8이므로 시작이 5다. 처방2를 적용하면 **거부된다**.

이것이 부작용인지 판정하기 위해 [msg1.md](../../../../../../msg1.md) 원문을 확인했다. msg1.md:29-34는 "위 520b tlc off의 경우"라며 `iter start/iter end/flag`를 `1/4/-1`, `5/8/0`, `5/8/1`, `5/8/2`로 적는다. msg1.md:21-22는 "bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리하는거야", "추가로 bf 구간은 늘어나지않아. 딱 1~4야"라고 못박는다. 즉 **iteration 1~4에 분기를 두지 않는 것이 사용자가 유효하다고 제시한 형태**이며, 처방2는 그 형태를 거부한다. 부작용이 아니라 정면 충돌이다.

#### 처방B의 검사 셋을 메모 예시에 적용

메모 예시 헤더 `-1 0 1 2 -1`에 세 검사와 6.1 방어를 적용한다.

| 검사 | 메모 예시 결과 | 판정 |
|------|--------------|------|
| ㉠ 첫 분기 그룹 index가 0이 아니면 오류 | 첫 분기 그룹은 그룹 1이고 index가 0 | 통과 |
| ㉡ 같은 구간 안 index 역행 오류 | 구간 0의 index는 0, 1, 2로 오름차순 | 통과 |
| ㉢ `num_sw_span > MAX_SW_SPAN` 오류 | `num_sw_span = 1`, `MAX_SW_SPAN = 4` | 통과 |
| 6.1 방어 `span < 0 \|\| span >= MAX_SW_SPAN` | 그룹 1, 2, 3의 span이 모두 0 | 통과 |

메모 예시는 검사 셋을 **오류 없이 통과한다**. 처방B는 R2-3의 유효 형태를 막지 않는다.

---

## ㉰ 증거 목록

| # | 증거 | 분류 | 코드 근거 |
|---|------|------|----------|
| 1 | `__12META__`가 정의되지 않아 common.h의 `#else` 문턱 갈래가 쓰인다 | 확인됨 | [mode.h:11](../../../../../../0_LDPC_original/src/mode.h) (주석 처리), [common.h:200](../../../../../../0_LDPC_original/src/common.h), [common.h:228](../../../../../../0_LDPC_original/src/common.h). 전수 grep 히트: common.h:200, corner.cpp:84, main.cpp:932, 933, 935, 976, 977, 979, mode.h:11 |
| 2 | `SW_TH_BF_DEFAULT` 630 | 확인됨 | [common.h:231](../../../../../../0_LDPC_original/src/common.h) |
| 3 | `SW_TH_BF0_512B_TLC_OFF` 680 | 확인됨 | [common.h:236](../../../../../../0_LDPC_original/src/common.h) |
| 4 | `SW_TH_BF1_512B_TLC_OFF` 130 | 확인됨 | [common.h:237](../../../../../../0_LDPC_original/src/common.h) |
| 5 | `SW_TH_5_8_SET0_DEFAULT` 960, `SW_TH_5_8_SET0_512B_TLC_OFF` 1100 | 확인됨 | [common.h:240](../../../../../../0_LDPC_original/src/common.h), [common.h:244](../../../../../../0_LDPC_original/src/common.h) |
| 6 | `SW_TH_5_8_SET1_DEFAULT` 950, `SW_TH_5_8_SET1_512B_TLC_OFF` 950 | 확인됨 | [common.h:247](../../../../../../0_LDPC_original/src/common.h), [common.h:251](../../../../../../0_LDPC_original/src/common.h) |
| 7 | `LAYOUT_PRIME_512B_TLC_VSS_OFF` 1이고 나머지 레이아웃 상수는 주석 처리 | 확인됨 | [common.h:193-198](../../../../../../0_LDPC_original/src/common.h) |
| 8 | `matrix_sel`은 실행 인자 `argv[1]`에서 온다. AUTO 빌드에서 `argc > 19`이면 임의 값이 통과해 4.1의 `default` 갈래에 닿는다 | 확인됨 | [main.cpp:139](../../../../../../0_LDPC_original/src/main.cpp), [main.cpp:141-143](../../../../../../0_LDPC_original/src/main.cpp). 전수 grep 히트(대입): main.cpp:139, 499. TV Gen 경로는 main.cpp:499-503에서 `LAYOUT_PRIME_512B_TLC_VSS_OFF <= matrix_sel`만 본다 |
| 9 | `BF_mode`는 Ref-C 경로에서 `MODE_BF_ON` 고정 | 확인됨 | [main.cpp:232](../../../../../../0_LDPC_original/src/main.cpp), TV Gen은 [main.cpp:538](../../../../../../0_LDPC_original/src/main.cpp). `MODE_BF_ON` 1 (common.h:87) |
| 10 | `MAX_SW_SPAN` 4, `MAX_SW_BRANCH` 9는 code_diff 1.1의 제안값이고 소스에 아직 없다 | 확인됨 | [code_diff 1.1](../../code_diff.md#ch1). 전수 grep(`MAX_SW_SPAN`, `MAX_SW_BRANCH`, `SW_BRANCH_NONE`, `sw_branch_idx`, `sw_span_idx`, `num_sw_span`, `num_sw_branch`, `syn_th_sw_branch`) 결과 `0_LDPC_original/src` 전체에서 히트 0건 |
| 11 | `syn_th_BF1`은 선언과 대입 두 곳뿐이고 읽는 곳이 없다 | 확인됨 | 전수 grep 히트: [decoder.h:303](../../../../../../0_LDPC_original/src/decoder.h) (선언), [decoder.cpp:468](../../../../../../0_LDPC_original/src/decoder.cpp) (대입). `syn_th_BF0`는 decoder.h:302, decoder.cpp:467, decoder.cpp:2088(읽기) |
| 12 | 6.1 수정 후 루프에 `span` 범위 검사가 없다 | 확인됨 | [code_diff 6.1](../../code_diff.md#ch6) 수정 후 코드에서 `int span = ...sw_span_idx_each_group[g];` 다음 줄이 곧바로 `cur_sw_branch_idx[span]` 첨자다 |
| 13 | 3.2가 span을 계산하는 자리에서는 `iter_start`를 읽을 수 없다 | 확인됨 | 헤더 반복문 [local_opt.cpp:81-84](../../../../../../0_LDPC_original/src/local_opt.cpp), `iter_start` 할당 [local_opt.cpp:103](../../../../../../0_LDPC_original/src/local_opt.cpp), 채우기 [local_opt.cpp:112](../../../../../../0_LDPC_original/src/local_opt.cpp) |
| 14 | AUTO 빌드에서 `Select_BF`가 `m_param_LLR`을 참조할 수 있다 | 확인됨 | [local_opt.cpp:34](../../../../../../0_LDPC_original/src/local_opt.cpp) → [local_opt.cpp:46](../../../../../../0_LDPC_original/src/local_opt.cpp) → [ecc_top.cpp:222, 228](../../../../../../0_LDPC_original/src/ecc_top.cpp) → [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp), 호출은 [decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp) |
| 15 | 비AUTO 빌드에서 `m_param_LLR`은 미초기화다 | 확인됨 | 전수 grep 히트: [ecc_top.h:94](../../../../../../0_LDPC_original/src/ecc_top.h) (선언), [ecc_top.cpp:222](../../../../../../0_LDPC_original/src/ecc_top.cpp) (유일한 대입), [ecc_top.cpp:208, 228](../../../../../../0_LDPC_original/src/ecc_top.cpp) (전달). 생성자 [ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp)에 이 멤버가 없다 |
| 16 | `err = TRUE`는 흐름을 바꾸지 않는다 (3.4와 처방B의 오류가 비치명적) | 확인됨 | `int err = FALSE;` [local_opt.cpp:56](../../../../../../0_LDPC_original/src/local_opt.cpp), 유일한 대입 [local_opt.cpp:140](../../../../../../0_LDPC_original/src/local_opt.cpp), 함수는 `void` [local_opt.cpp:52](../../../../../../0_LDPC_original/src/local_opt.cpp) |
| 17 | 구 파일의 분기 줄이 `1 2 31`로 읽힌다 | 확인됨 | 손 실행 3의 토큰 표. 파일은 [LLR_MATRIX_0.txt](../../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt) 1~24행, 파서는 [local_opt.cpp:61-115](../../../../../../0_LDPC_original/src/local_opt.cpp) |
| 18 | 현 파일의 그룹별 iteration 범위와 분기 index | 확인됨 | [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 10행(`num_set_each_group`), 18~105행(row의 `iter_start`, `iter_end`, 마지막 칸) |
| 19 | 수정 전 `Select_BF`의 AUTO 갈래가 `flag_BF_on = FLAG_LOW` 한 줄이다 | 확인됨 | [decoder.cpp:2084-2085](../../../../../../0_LDPC_original/src/decoder.cpp) |
| 20 | 수정 전 코드에 `FLAG_HD_1_4_SET_TYPE_1`을 대입하는 곳이 없다 | 확인됨 | 전수 grep 히트: `flag_HD_1_4_Set` 대입은 decoder.cpp:612(`FLAG_LOW`), decoder.cpp:2090(`TYPE_0`), 읽기는 decoder.cpp:7002, 7006. enum은 [common.h:717-720](../../../../../../0_LDPC_original/src/common.h) |

미확인 항목: 없음. 위 20건은 모두 코드에서 직접 확인했다.

---

## ㉱ 처방 평가

### R2-3 처방 갈래 ㉮ (구간별 `iter_start` 기록): **처방 수정 필요**

핵심 방향은 옳다. 구간 번호를 등장 순서가 아니라 iteration 범위에 묶으면 손 실행 5에서 보듯 메모 예시가 바로잡히고 현 파일은 그대로다. 다만 세 곳을 고쳐야 성립한다.

- ㉠ **계산 위치**: 구간별 `iter_start`는 [local_opt.cpp:115](../../../../../../0_LDPC_original/src/local_opt.cpp) 뒤(row 읽기가 끝난 자리)에서 구한다. 3.2가 span을 계산하는 84행 뒤에서는 `iter_start` 배열이 아직 없다. 구간의 `iter_start`는 그 구간 첫 그룹의 첫 row 값으로 정하고, 같은 구간의 다른 분기 그룹들이 같은 값을 갖는지 대조 검사를 함께 둔다 (상위 문서 4장 읽는 규칙 ㉱ "구간의 시작과 끝만 모든 분기가 맞춘다"를 검사로 옮기는 것이다)
- ㉡ **BF 미진입 시 건너뛰는 구간**: 5.1의 `else` 갈래에 박힌 `cur_sw_branch_idx[1]`의 1은 구간 번호가 아니라 iteration 5~8을 뜻하는 상수다. "iteration 범위가 `ITER_MAX_HBF` 이하인 구간은 건너뛴다"로 다시 쓴다
- ㉢ **비AUTO 빌드**: 처방을 넣으면 `Select_BF`가 `m_param_LLR`을 역참조하게 되어, 미초기화 포인터를 매 프레임 읽는다(증거 15). R2-1의 처방(갈래 유지 또는 널 초기화와 널 검사)이 먼저 확정되어야 한다. 이 의존을 상위 문서 9장 적용 순서에 적는다

또한 이 처방만으로는 분기 3개 이상을 고를 수 없다. `num_sw_branch[]`가 4.1에 상수로 박혀 있기 때문이며, R2-9의 처방(파일에서 분기 수를 세어 대조하거나 채우기)이 함께 들어가야 메모 예시가 온전히 동작한다.

### R2-3 처방 갈래 ㉯ (구간 0의 시작이 1이 아니면 오류): **처방 반대**

배경 메모가 유효하다고 제시한 형태를 거부한다(손 실행 5). 적용하면 사용자가 쓰려는 파일이 통과하지 못한다. 이 갈래는 상위 문서에서 빼는 것이 옳다.

### R2-10 처방 (검사 셋 3개와 6.1 방어): **처방 수정 필요**

메모 예시를 막지 않는다는 점은 확인됐다(손 실행 5). 세 가지를 보태야 한다.

- ㉠ **손 실행 4를 못 잡는다**: 헤더 `1 0 -1 -1`은 첫 분기 그룹의 index가 1이므로 검사 ㉠에 걸린다. 그러나 `0 1 -1 1 0` 같이 첫 분기 그룹이 0이면서 뒤에서 순서가 뒤집힌 배치는 세 검사를 모두 통과하면서 span이 잘못 붙는다. 검사를 "분기 index가 0인 그룹으로 시작하지 않는 구간이 있으면 오류"로 일반화하거나, 구간 번호 계산 자체를 iteration 범위 기준으로 바꾸는 편(R2-3 처방 ㉮)이 근본적이다
- ㉡ **오류가 멈추지 않는다**: `err = TRUE`는 흐름을 바꾸지 않는다(증거 16). 검사에 걸린 파일도 그대로 복호에 들어간다. R2-8의 처방(프로세스 중단 또는 종료 코드)과 묶어야 검사가 값을 한다
- ㉢ **6.1 방어의 동작이 미정**: `span < 0 || span >= MAX_SW_SPAN`일 때 무엇을 할지 code_diff에 없다. 그 그룹을 후보에서 빼면(`continue`) 구 파일에서는 모든 그룹이 빠져 `selected_group = -1`이 되고 [code_diff 6.2](../../code_diff.md#ch6)의 오류 출력과 `return 0`으로 이어진다. 이 동작을 code_diff에 명시한다

---

## ㉲ 검증 중 새로 드러난 사실

- ㉮ **`SW_TH_5_8_SET1_*`이 `SW_TH_5_8_SET0_*`보다 작다.** 현재 활성인 `__12META__` 미정의 갈래에서 `SW_TH_5_8_SET0_512B_TLC_OFF`는 1100, `SW_TH_5_8_SET1_512B_TLC_OFF`는 950이고, DEFAULT도 960과 950으로 뒤집혀 있다([common.h:240-251](../../../../../../0_LDPC_original/src/common.h)). [code_diff 4.1](../../code_diff.md#ch4)은 "문턱은 오름차순"을 전제하는데, 이 상수들로는 분기 3개짜리 오름차순 문턱 배열을 만들 수 없다. `syn_th_sw_branch[1] = {1100, 950}`으로 넣으면 `Select_SW_Branch`가 1을 절대 돌려주지 않아 분기 1 그룹이 영영 미선택이 된다. `__12META__` 정의 갈래는 950과 1270으로 오름차순이다([common.h:211-226](../../../../../../0_LDPC_original/src/common.h)). 배경 메모가 요구하는 분기 3개를 지원하려면 상위 문서 7장 ㉯(문턱을 파일이나 실행 인자로 받기)가 선택 사항이 아니라 전제 조건이 된다
- ㉯ **파서의 구간 번호 규칙이 표현할 수 없는 배치가 있다.** `b == 0 && prev_branch != 0`을 새 구간의 신호로 삼으므로, 한 구간 안에서 분기 0 그룹이 분기 1 그룹 뒤에 다시 나오는 배치(예: `0 1 0`)는 두 구간으로 세어진다. 상위 문서 4장 읽는 규칙 ㉮(같은 `{x}{y}`가 연속하면 이어붙는다)는 분기 0 그룹이 연속할 때만 성립하며, 이 제약이 문서에 적혀 있지 않다
- ㉰ **처방1이 R2-1과 결합 의존을 만든다.** 지금의 [code_diff 5.1](../../code_diff.md#ch5) 수정 후 `Select_BF`는 `m_param_LLR`을 건드리지 않아 비AUTO 빌드에서도 안전하다. 처방1을 넣으면 `Select_BF`가 `m_param_LLR`을 읽게 되어, 비AUTO 빌드의 미초기화 포인터 문제(R2-1)가 `Is_Iter_Type_*` 두 함수를 넘어 `Select_BF`까지 번진다. 두 처방의 적용 순서를 상위 문서 9장에 못박아야 한다
- ㉱ **`cur_sw_branch_idx[-1]`이 읽는 값이 `syn_th_BF0`일 공산이 크다.** [code_diff 2.2](../../code_diff.md#ch2) 수정 후 `decoder.h`에서 `cur_sw_branch_idx[]` 바로 앞 멤버가 `syn_th_BF0`(680)이다. 그러면 분기 비교가 모두 실패해 `selected_group = -1`로 빠지므로, 겉으로는 오류 메시지가 나오는 것처럼 보인다. 배열 밖 읽기가 표준상 정의되지 않은 동작이라는 사실과, 멤버 배치를 바꾸면 증상이 달라진다는 사실을 함께 적어야 한다
- ㉲ **BF 진입 프레임의 iteration 1~4 분기와 배경 메모가 충돌한다.** [msg1.md:21-22](../../../../../../msg1.md)는 BF에서 LLR matrix 문턱을 받지 않고 -1로 처리한다고 못박는데, [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)는 iteration 1~4에 분기 두 개를 두고 있다(그룹 0, 1이 분기 0이고 그룹 2가 분기 1). R2-7이 이미 지적한 사안이며, 이번 손 실행에서 문턱 130이 실제로 span 0에 들어가 분기를 가르는 것을 확인했으므로 결정 없이 진행하면 두 형태 중 하나는 반드시 틀린다
