# Round 3 검증: 팀 V3 워커 2 (R2-5 처방, R2-8 전체)

작성: 2026-09-03 01:36:39

담당: 발견 R2-5의 처방 네 갈래 부작용 검증, 발견 R2-8의 사실과 처방 검증.
R2-5의 사실 축은 워커 1 담당이므로 여기서는 처방 판정에 필요한 만큼만 사실을 다시 확인했다.

용어: LLR(Log Likelihood Ratio, 로그 우도비), FER(Frame Error Rate, 프레임 오류율),
BF(Bit Flipping, 비트 뒤집기), SW(Syndrome Weight, 신드롬 무게),
CSW(Check Sum Weight), DAO(Decoder Auto Optimizer),
MPI(Message Passing Interface, 프로세스 간 메시지 전달 규격),
HD(Hard Decision, 경판정), UB(Undefined Behavior, 정의되지 않은 동작).

---

## 1. 판정 요약

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| P5-㉮ 보정식을 음수가 안 나오게 고친다 | **처방 수정 필요** | 음수를 없애는 식은 셋 다 성립하나, 어느 것도 BF 진입 프레임의 row 121~124 미도달을 고치지 못한다. 후보 중 "마지막 원소만 보정"은 뒤쪽 열 세 개가 0.0으로 죽는 새 부작용을 만든다 |
| P5-㉯ AUTO에서도 검사점 5개 | **처방 수정 필요 (조건부)** | DAO 파싱은 열 수 변경을 견딘다 (열 수를 파일에서 추론). 다만 검사점 5개를 비AUTO처럼 상수 배열로 채우면 `MN[MN_num-1]`이 상수 120이 되어 파일 기반 iteration 예산이 무너진다. 마지막 원소를 파일 값으로 유지하는 형태로만 성립 |
| P5-㉰ 문서에만 열 배치를 적는다 | **부분 유효** | DAO는 iteration별 FER 열을 읽지만 최적화 판정에는 쓰지 않고 로그 한 줄에만 쓴다. 따라서 열 배치는 문서로 닫힌다. 그러나 row 121~124 미도달은 문서로 닫히지 않는다 |
| P5-㉱ mn 0 종료 경로에서 보정 건너뛰기 | **처방 불필요 (대상 반박됨)** | HD와 1.5SD에서 mn 0 종료 경로가 존재하지 않는다. `Check_End_Iter`는 mn 0에서 호출되지 않고 `Jump_Iter`는 HD, 1.5SD에서 항상 FALSE를 돌려준다 |
| H8 검사 실패가 어디에도 닿지 않는다 | **확인됨** | `err` 읽는 곳 없음, 함수 void, DAO는 stdout을 받지 않음, `main`은 return 0 고정, 저장소 전체에 `exit`/`abort`/`assert` 없음 |
| P8 프로세스를 멈추거나 종료 코드를 바꾼다 | **처방 유효 (경로 확정 필요)** | Linux 배치가 `set -euo pipefail`이라 EXE의 0 아닌 종료가 `CalledProcessError`로 올라오고 [DAO_Main.py:7951-7952](../../../../../SRC/DAO_Main.py)가 `MPI_Abort`로 DAO 전체를 죽인다. MPI 경로 걱정은 실체가 없다 (AUTO 빌드에서 `__RUN_MPI__`가 정의되지 않는다) |

Round 2 대비 정정 두 건:

- ㉮ **R2-5의 "열 1~3이 1.0 고정"은 한 열 모자란다.** 열 4도 1.0이다 (아래 2.1 ㉰)
- ㉯ **R2-8과 context가 DAO의 결과 파일 파서로 지목한 `Read_FER_From_File`([DAO_Main.py:7969-7999](../../../../../SRC/DAO_Main.py))은 호출자가 없는 죽은 코드다.** 실제 파서는 `Read_Ref_C_Result`([DAO_Main.py:8187-8273](../../../../../SRC/DAO_Main.py))이다 (아래 2.4)

---

## 2. 임무 1: R2-5 처방 검증

### 2.1 검증에 쓴 사실 기반

처방 판정에 필요한 만큼만 다시 확인했다.

**㉮ 보정 블록의 현재 식** ([local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp)):

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

**확인됨.** 조건의 둘째 항 `MODE_DEC_1_SSD`는 저장소 전체에서 이 줄에만 있고 정의가 없다
([common.h:75-78](../../../../../../0_LDPC_original/src/common.h)에는 `MODE_DEC_HD` 1, `MODE_DEC_2SD` 2,
`MODE_DEC_3SD` 3, `MODE_DEC_1_5SD` 4만 있다). R2-15의 사실 주장과 일치한다.
DAO는 `init_n` 1(HD)을 쓰므로([DAO_Config.py:171](../../../../../SRC/DAO_Config.py)) 첫째 항만으로 블록이 동작한다.

**㉯ 이 블록이 하는 일 두 가지 (분리)**:

- ㉠ **검사점 배열 보정**: `MN[0]`부터 `MN[MN_num-2]`까지는 결과 파일의 iteration별 FER 열의 문턱이다.
  소비처는 [ecc_top.cpp:877-879](../../../../../../0_LDPC_original/src/ecc_top.cpp)
  (`if (o_iter_num > m_param_dec->MN[n]) fr_4KB[n]++;`)와 머리글 출력 두 곳
  ([ecc_top.cpp:2054](../../../../../../0_LDPC_original/src/ecc_top.cpp),
  [main.cpp:317](../../../../../../0_LDPC_original/src/main.cpp))
- ㉡ **iteration 상한 축소**: `MN[MN_num-1]`은 메인 루프의 상한이다.
  [decoder.cpp:1118-1120](../../../../../../0_LDPC_original/src/decoder.cpp)
  (`MN = m_param_dec->MN[m_param_dec->MN_num - 1];` 뒤 `for (mn = 0; mn < MN + 1; mn++)`).
  이 값이 124에서 120으로 줄어야 BF 미진입 프레임이 `Select_BF`에서 `MN += ITER_MAX_HBF`를 받고도
  파일이 덮는 iteration 124를 넘지 않는다

두 일은 같은 반복문 안에 섞여 있으나 소비처가 완전히 다르다. 이것이 처방 설계의 출발점이다.

**㉰ 값 손계산과 열 판정**: [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)의
마지막 row(105행)가 `iter_end` 124이므로 `MN_num` = 124.
보정 전 `MN` = [0, 1, 2, ..., 122, 124], 보정 후 `MN` = [4, -3, -2, -1, 0, 1, ..., 118, 120]. **확인됨.**

열 판정에서 R2-5를 한 칸 정정한다. HD에서 정규화된 `o_iter_num`은 항상 1 이상이다.
BF 진입 프레임은 `Check_End_Iter`가 mn 1부터만 불리므로 `iter_num >= 1`,
BF 미진입 프레임은 mn 5부터 시작하므로 `iter_num >= 5`이고 보정 뒤 1 이상이다.
따라서 `o_iter_num > MN[n]` 비교에서

- 열 0: `MN[0]` 4 → 뜻이 있다 (정규화 iteration 4 초과 프레임 비율)
- 열 1, 2, 3: `MN` -3, -2, -1 → 항상 참 → 1.0 고정
- **열 4: `MN[4]` 0 → `iter_num >= 1`이므로 이것도 항상 참 → 1.0 고정**
- 열 5 이후: `MN[n]` = n - 4 → 뜻이 있다

즉 1.0 고정 열은 **네 개(1~4)**다. context의 "열 4는 `MN[4] = 0`"이라는 단서는
0을 경계로 본 것인데, `iter_num`이 0이 되는 경로가 없으므로 열 4도 포화된다 (근거는 2.5의 P5-㉱).

**㉱ BF 진입 프레임의 row 121~124 미도달**: `MN` = 120이므로 BF 진입 프레임은 mn 1~120만 돈다.
BF 미진입 프레임은 [decoder.cpp(수정 후 5.1)](../../code_diff.md#ch5)에서 `mn += 4`, `MN += 4`를 받아
mn 5~124를 돈다. 파일 그룹 11이 iteration 105~124를 덮으므로 121~124 row는 미진입 프레임만 쓴다. **확인됨.**

### 2.2 처방 가설 P5-㉮: 보정식을 음수가 나오지 않게 고친다

가설: 124-131의 보정식을 음수가 나오지 않는 식으로 바꾸면 결과 파일 열이 정상으로 돌아오고 새 문제가 생기지 않는다.

#### 후보 세 개와 각각의 소비처 영향

**후보 ㉠: 마지막 원소만 보정한다.**

```cpp
    if (MODE_DEC_HD == m_param_dec->init_n) {
        m_param_dec->MN[m_param_dec->MN_num - 1] -= ITER_MAX_HBF;
    }
```

- 결과 `MN` = [0, 1, 2, ..., 122, 120]
- 상한 축소 유지: **유지한다** (120)
- 열: 음수 사라짐. 열 0은 `MN[0]` 0이라 1.0 고정 (보정 전 AUTO와 같은 상태이므로 새 문제 아님)
- **새 부작용**: 배열이 단조가 아니다. 정규화 `iter_num`의 최댓값이 120이므로
  `MN[n]`이 120 이상인 열 120, 121, 122가 항상 0.0이 된다.
  즉 앞쪽 포화 열 넷이 뒤쪽 죽은 열 셋으로 바뀐다. 사람이 읽는 지표로는 개선이지만 새 왜곡이 남는다

**후보 ㉡: 검사점 개수까지 함께 줄인다.**

```cpp
    int mn_top = max_iter_end;
    if (MODE_DEC_HD == m_param_dec->init_n) {
        mn_top -= ITER_MAX_HBF;
    }
    m_param_dec->MN_num = mn_top;
    m_param_dec->MN = new int[m_param_dec->MN_num];
    for (i = 0; i < m_param_dec->MN_num; i++) {
        m_param_dec->MN[i] = (i == m_param_dec->MN_num - 1) ? mn_top : i;
    }
```

- 결과 `MN_num` = 120, `MN` = [0, 1, ..., 118, 120]
- 상한 축소 유지: **유지한다** (120)
- 열: 음수 없음, 단조, 죽은 열 없음. 열 0만 1.0 (보정 전과 동일)
- 부작용: 결과 파일 열 수가 124에서 120으로 준다. DAO 파싱은 견딘다 (2.4 참조)
- **세 후보 중 가장 깨끗하다**

**후보 ㉢: 음수를 0으로 clamp한다.**

```cpp
        for (i = 0; i < m_param_dec->MN_num; i++) {
            m_param_dec->MN[i] -= ITER_MAX_HBF;
            if (m_param_dec->MN[i] < 0) m_param_dec->MN[i] = 0;
        }
```

- 결과 `MN` = [4, 0, 0, 0, 0, 1, ..., 118, 120]
- 상한 축소 유지: **유지한다** (120)
- 열: 머리글의 음수는 사라지지만 열 1~4는 여전히 1.0 고정이다. **실체 문제를 고치지 못한다.**
  검사점이 중복되어 머리글에 `4 0 0 0 0 1 2 ...`가 찍힌다. 권하지 않는다

#### 후보 공통 판정

**㉰ iteration 상한 축소 유지 여부**: 세 후보 모두 `MN[MN_num-1]`을 120으로 유지한다. **확인됨.**

유지하지 않으면 무슨 일이 생기는지도 확인했다. `MN`이 124로 남으면 BF 미진입 프레임은
`Select_BF`에서 `MN += 4`를 받아 128까지 돌고, `Get_Cur_LLR_Idx_FILE(125..128)`은
[decoder.cpp:6985-6999](../../../../../../0_LDPC_original/src/decoder.cpp)의 그룹 탐색에서
어느 그룹의 `iter_start ~ iter_end`에도 들지 못해 `selected_group`이 -1로 남는다.
그 다음 줄 [decoder.cpp:7048-7051](../../../../../../0_LDPC_original/src/decoder.cpp)은

```cpp
	if (selected_group == -1 || selected_group >= m_param_LLR->num_group) {
	    printf("[Error] @Cur_LLR_IDX (1): iter%d, state%d, CSW%d\n", iter, state_hd_error_floor_set, prev_CSW);
	}
	if (GROUP_TYPE_ITER == m_param_LLR->type_each_group[selected_group]) {
```

으로, printf만 하고 그대로 진행해 `type_each_group[-1]`을 읽는다. 배열 범위 밖 읽기(UB)다.
Round 2의 "오류 경로로 빠진다"는 판정은 **확인됨**이며, 실제로는 printf보다 무겁다.
code_diff 6.2가 이 자리에 `return 0`을 넣으므로([code_diff.md 6.2](../../code_diff.md#ch6))
수정 후에는 UB 대신 매 iteration 매 프레임 printf 폭주와 row 0 오선택이 된다. 어느 쪽이든 상한 축소는 필수다.

**㉱ row 121~124 미도달 수리 여부**: **세 후보 모두 고치지 못한다.**

이 결함은 검사점 배열과 무관하고, "BF 미진입 프레임만 `MN`에 +4를 받는다"는 구조에서 나온다.
`MN` 하나를 두 종류 프레임이 공유하는 한, 상한을 120으로 두면 BF 진입 프레임이 121~124를 못 보고,
124로 두면 미진입 프레임이 125~128로 넘쳐 파일 범위를 벗어난다.
고치려면 `Select_BF`의 미진입 갈래에서 `MN += ITER_MAX_HBF`를 빼고 상한 축소도 없애야 하는데
(그러면 BF 진입 프레임 124 mini iteration, 미진입 120 mini iteration으로 예산이 어긋난다),
이는 디코더가 소비하는 iteration 수를 바꾸는 Decision 등급 변경이다.
**처방 문서에 "이 갈래는 열 배치만 고치고 row 121~124 미도달은 별건"이라고 명시해야 한다.**

**㉲ `MN[]` 소비처 전수 grep**

패턴 `MN\[|MN_num|MN_size`로 [0_LDPC_original/src](../../../../../../0_LDPC_original/src) 전체를 훑었다.

| 파일 | 히트 줄 수 | 첨자 읽기 형태 | 중간 원소 `MN[n]` 읽기 |
|------|-----------|---------------|----------------------|
| [corner.cpp](../../../../../../0_LDPC_original/src/corner.cpp) | 1 (103) | `MN[MN_num-1]`만 | 없음 |
| [ecc_data.h](../../../../../../0_LDPC_original/src/ecc_data.h) | 1 (129) | 선언 `int MN_num;`, 130행 `int* MN;` | 없음 |
| [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) | 41 | `MN[MN_num-1]` 21곳 (564, 587, 1118, 7583, 7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931, 7941, 7950, 7959, 7971, 7983, 7996, 8009, 8018), 나머지는 `MN_size` 루프 | 없음 |
| [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) | 25 | `MN[MN_num-1]` 8곳 (2738, 2741, 2757, 2760, 2774, 2790, 2815, 2819), `MN_num` 루프 다수 | **878, 2022, 2054** |
| [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) | 8 (116-129) | 쓰는 곳 | 쓰는 곳 |
| [main.cpp](../../../../../../0_LDPC_original/src/main.cpp) | 25 | 비AUTO와 TV Gen에서 쓰는 곳 (710-778, 879) | **317** (출력) |

**중간 원소를 읽는 소비처는 네 곳뿐이다.** 값이 `[4, -3, -2, -1, 0, ...]`일 때 각각의 동작:

- ㉠ [ecc_top.cpp:877-879](../../../../../../0_LDPC_original/src/ecc_top.cpp)
  `if (o_iter_num > m_param_dec->MN[n]) fr_4KB[n]++;`
  → 열 1~4가 1.0으로 포화. **실체 있는 오동작.** 이 값이 결과 파일의 FER 열이 되어 DAO로 간다
- ㉡ [ecc_top.cpp:2020-2025](../../../../../../0_LDPC_original/src/ecc_top.cpp) `Print_Result_Part1`
  → `printf`이므로 stdout으로만 나간다. AUTO 빌드에서는 이 함수가 불리지 않는다
  ([ecc_top.cpp:652-661](../../../../../../0_LDPC_original/src/ecc_top.cpp)에서 AUTO는 `Print_Result_Part1_Auto`를 부른다)
- ㉢ [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp) `Print_Result_Part1_Auto`
  → `Ref_C_result_%d.txt`에 `FER (4 -3 -2 -1 0 1 ...)` 머리글을 쓴다.
  DAO는 이 파일을 읽지 않고 지운다 ([DAO_Constants.py:129](../../../../../SRC/DAO_Constants.py)의
  `HEADER_TO_REMOVE = ["result", "log_CSW", "Ref_C_result"]`,
  [DAO_Main.py:946-957](../../../../../SRC/DAO_Main.py)에서 삭제).
  **사람이 읽는 로그만의 문제.**
- ㉣ [main.cpp:314-319](../../../../../../0_LDPC_original/src/main.cpp)
  → 같은 `Ref_C_result_%d.txt`에 `* iteration number : 4 -3 -2 -1 0 ...`를 쓴다. 같은 판정

**판정: 처방 수정 필요.** 후보 ㉡을 권하고, 후보 ㉠은 뒤쪽 죽은 열이라는 새 부작용을,
후보 ㉢은 실체를 못 고침을 문서에 적어야 한다. 어느 후보도 row 121~124 미도달을 고치지 못한다는 점을 함께 적는다.

### 2.3 처방 가설 P5-㉯: AUTO에서도 검사점 5개로 바꾼다

**㉮ 비AUTO 빌드의 `MN[]`과 `MN_num`** ([main.cpp:704-781](../../../../../../0_LDPC_original/src/main.cpp), `Set_Ref_C_Iteration`):

함수 전체가 `#ifndef __AUTO_LLR_OPT__` (706행)과 `#endif` (780행)로 감싸여 있다. **확인됨.**
HD에 `MODE_ITER_DEFAULT`일 때:

```cpp
            g_param_dec.MN_num = ITER_MAX_REF_C_HD_NUM;   // 5
            g_param_dec.MN = new int[g_param_dec.MN_num];
            g_param_dec.MN[0] = ITER_MAX_HBF;             // 4
            g_param_dec.MN[1] = ITER_MAX_HD_1_PRIME;      // 8
            g_param_dec.MN[2] = ITER_MAX_HD_2_PRIME;      // 50 (__4_BIT_LLR__) 또는 64
            g_param_dec.MN[3] = ITER_MAX_HD_3_PRIME;      // 100
            g_param_dec.MN[4] = ITER_MAX_HD_PRIME;        // 120
```

상수는 [common.h:398-401, 411-414, 445-448](../../../../../../0_LDPC_original/src/common.h).
`__4_BIT_LLR__`은 [mode.h:12](../../../../../../0_LDPC_original/src/mode.h)에서 주석이므로
저장소 기준 `MN[2]` = 64다. 호출은 [main.cpp:245](../../../../../../0_LDPC_original/src/main.cpp)(Ref-C)와
[main.cpp:579](../../../../../../0_LDPC_original/src/main.cpp)(TV Gen).

여기서 `MN[0]` = `ITER_MAX_HBF` = 4는 보정 잔재가 아니라 **정규화된 iteration 척도의 첫 검사점**이다.
비AUTO에서도 `iter_num -= ITER_MAX_HBF` 정규화가 걸리므로 4, 8, 64, 100, 120은 모두 1~120 척도 위의 값이다.
이 점이 AUTO 보정 블록이 `MN[0] = ITER_MAX_HBF`를 두는 이유를 설명한다.
다만 AUTO는 중간 원소를 절대 iteration 번호가 아니라 `i - 4`로 밀어 버려 척도가 어긋났다.

**㉯ 열 수를 정하는 것**: 머리글은 [ecc_top.cpp:2020](../../../../../../0_LDPC_original/src/ecc_top.cpp)과
[2052](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `for (int n = 0; n < m_param_dec->MN_num; n++)`,
값은 [2123](../../../../../../0_LDPC_original/src/ecc_top.cpp),
[2203](../../../../../../0_LDPC_original/src/ecc_top.cpp),
[2274](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 같은 형태 루프다.
따라서 열 수는 정확히 `MN_num`이고, 124에서 5로 바뀐다. **확인됨.**

**㉰ (핵심) DAO 파싱이 열 수 변경을 견디는가**

먼저 파서 지목을 바로잡는다. context와 R2-8이 든 [DAO_Main.py:7969-7999](../../../../../SRC/DAO_Main.py)
`Read_FER_From_File`은 **호출자가 없다**. `Read_FER_From_File`로 전수 grep한 결과
[5_DAO/SRC/DAO_Main.py:7969](../../../../../SRC/DAO_Main.py)(정의)와
`5_DAO/reference/SRC/DAO_Main.py:7969`(반입 원형의 같은 정의) 둘뿐이다. **죽은 코드다.**
(설령 불렸어도 `parts[-1]`은 실행 시간 문자열 `0hour(s)_0minute(s)_5sec(s)`라 `float()`에서 예외가 난다.)

실제 파서는 [DAO_Main.py:8187-8273](../../../../../SRC/DAO_Main.py) `Read_Ref_C_Result`이고,
호출은 [DAO_Main.py:1824](../../../../../SRC/DAO_Main.py), [1851](../../../../../SRC/DAO_Main.py) 두 곳이다.
읽는 파일은 [DAO_Main.py:1604-1628](../../../../../SRC/DAO_Main.py) `Get_Result_File_Name`이 만드는
`result_4KB_S_...` 이름이며, 이는 C++ 쪽 `str_result_name_4KB`
([main.cpp:698](../../../../../../0_LDPC_original/src/main.cpp))다.
이 파일에 쓰는 곳은 [ecc_top.cpp:2090](../../../../../../0_LDPC_original/src/ecc_top.cpp),
[2163](../../../../../../0_LDPC_original/src/ecc_top.cpp),
[2238](../../../../../../0_LDPC_original/src/ecc_top.cpp)뿐이고 머리글은 들어가지 않는다.
비Windows AUTO 빌드에서 실제로 도는 것은
[ecc_top.cpp:684](../../../../../../0_LDPC_original/src/ecc_top.cpp)의
`Print_Result_Part2_Memory_Opt(TRUE, ...)` 하나다
(680-683행의 `Print_Result_Part2_Memory_Opt(FALSE, ...)`와 946행의 `..._Auto`는 `__WIN_OS__` 안에 있다).

파싱 코드 원문:

```python
        if REFC_CONFIG.ch_type in (1, 2):
            base_offset = 1
        elif REFC_CONFIG.ch_type == 3:
            base_offset = 3
...
                for line in lines:
                    parts = line.split()
                    result_offset = base_offset
                    if len(parts) <= base_offset:
                        continue

                    try:
                        num_test = int(parts[result_offset]); result_offset += 1
                        num_error = int(parts[result_offset]); result_offset += 1
                        avg_iteration = float(parts[result_offset]); result_offset += 1
                    except (ValueError, IndexError):
                        raise ValueError(f"Incomplete line in {file_path}: {line[:50]}...")

                    num_iteration = avg_iteration * num_test

                    # parts 슬라이싱 검증: result_offset:-3 범위가 유효한지 확인
                    if len(parts) < result_offset + 3:
                        continue  # 파일 형식 오류, 이 라인 스킵

                    arr = np.array(parts[result_offset:-3], dtype='f8')
                    if len(arr) == 0:
                        continue  # 빈 배열이면 스킵
```

한 줄의 토큰 배치는 (RBER 채널 기준) `[RBER, rn, fr, avg_iter, FER×MN_num, avg_clk, avg_clk_throughput, 실행시간]`이다.
실행시간은 [common.cpp:83-99](../../../../../../0_LDPC_original/src/common.cpp) `Print_Excuting_Time`이
`%dhour(s)_%dminute(s)_%dsec(s)`로 한 토큰을 붙인다.
따라서 `parts[4:-3]`은 정확히 FER 열 전부다. **열 수를 코드가 고정하지 않고 파일에서 추론한다.**

열 수가 124에서 5로 바뀌면:

- ㉠ `len(parts)` = 12, `result_offset` = 4, `len(parts) < 7` 검사 통과, `arr` 길이 5. **예외 없음**
- ㉡ [DAO_Main.py:1831-1836](../../../../../SRC/DAO_Main.py)에서 `len(sum_error_per_iter) != max_iteration`
  (`max_iteration`은 [DAO_LLR_MATRIX.py:441](../../../../../SRC/DAO_LLR_MATRIX.py) `groups[-1][-1].iter_end` = 124)
  이므로 `min_len` = 5로 잘라 앞 다섯 칸에만 더한다. **예외 없음, 배열 길이 불일치는 이미 방어되어 있다**
- ㉢ 다만 배열 위치 n이 "iteration n"이 아니라 "검사점 [4, 8, 64, 100, 120]"이 되어 **로그 표시가 잘못된 뜻을 갖는다**
  ([DAO_Main.py:7594-7598](../../../../../SRC/DAO_Main.py)의 `Errors per it.` / `FER per it.` 줄,
  [DAO_Config.py:316](../../../../../SRC/DAO_Config.py) `ENABLE_PRINT_ALL_ITER_FERs = True`가 기본값)
- ㉣ 최적화 판정에 쓰이는 값은 `num_error`(`parts[2]`)와 `avg_iteration`(`parts[3]`)이며 열 수와 무관하다

**결론: 파싱은 깨지지 않는다. 잘못된 값이 최적화에 들어가지도 않는다. 로그 표시만 어긋난다.** **확인됨.**

**㉱ 검사점 축소가 메인 루프 상한에 영향을 주는가**

**준다.** [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)이
`MN = m_param_dec->MN[m_param_dec->MN_num - 1];`이므로 상한은 배열의 **마지막 원소**다.
검사점을 5개로 줄이면서 비AUTO처럼 상수 배열([main.cpp:719-723](../../../../../../0_LDPC_original/src/main.cpp))을
그대로 가져오면 `MN[4]` = `ITER_MAX_HD_PRIME` = 120으로 못박히고,
파일의 `iter_end`가 124든 200이든 무시된다.
**AUTO의 파일 기반 iteration 예산 설계가 무너진다.**
같은 이유로 [corner.cpp:103](../../../../../../0_LDPC_original/src/corner.cpp),
[decoder.cpp:564](../../../../../../0_LDPC_original/src/decoder.cpp)(CRC LFSR 버퍼 크기),
[decoder.cpp:7583 외 20곳](../../../../../../0_LDPC_original/src/decoder.cpp)(`MN_size` 로그 버퍼),
[ecc_top.cpp:2738-2819](../../../../../../0_LDPC_original/src/ecc_top.cpp)(histogram 크기)가
모두 파일과 무관한 크기로 잡힌다.

**판정: 처방 수정 필요.** "검사점 5개"는 **마지막 원소를 파일의 `max_iter_end - ITER_MAX_HBF`로 유지하고
앞의 네 개만 검사점으로 쓰는 형태**로만 성립한다. 그 형태는 사실상 P5-㉮ 후보 ㉡의 열 수를 더 줄인 변종이며,
DAO 로그의 `FER per it.` 줄이 iteration이 아니라 검사점을 가리키게 되므로 로그 문구도 함께 손봐야 한다.

### 2.4 처방 가설 P5-㉰: 배열을 그대로 두고 열 배치를 문서에 적는다

**㉮ 문서 보강만으로 남는 실체 문제**

- ㉠ 결과 파일의 FER 열 1~4가 1.0으로 포화 → DAO의 `total_FER_per_iters`에 그대로 들어간다
- ㉡ `Ref_C_result_*.txt` 머리글의 음수 → DAO가 지우는 파일이므로 사람이 읽는 지표만의 문제
- ㉢ BF 진입 프레임의 row 121~124 미도달 → **문서로 닫히지 않는 디코딩 동작 비대칭**

**㉯ DAO가 그 열을 읽어 최적화 판정에 쓰는가**

읽기는 읽는다. 쓰지는 않는다. 전수 확인:

- `total_num_error_per_iters` 히트 3곳: [DAO_Main.py:592](../../../../../SRC/DAO_Main.py)(선언),
  [1891](../../../../../SRC/DAO_Main.py)(대입), [7595](../../../../../SRC/DAO_Main.py)(로그 문자열)
- `total_FER_per_iters` 히트 3곳: [593](../../../../../SRC/DAO_Main.py)(선언),
  [1892](../../../../../SRC/DAO_Main.py)(대입), [7596](../../../../../SRC/DAO_Main.py)(로그 문자열)

최적화 판정에 쓰이는 값은 다음 둘이다.

- ㉠ `FERs[ch_idx]` = `total_errors / total_tests` ([DAO_Main.py:1885](../../../../../SRC/DAO_Main.py)).
  `total_errors`는 `parts[2]`, 곧 C++의 `fr[MN_num-1]`이고 이는
  [ecc_top.cpp:874-876](../../../../../../0_LDPC_original/src/ecc_top.cpp)에서 `o_CRC_flag`로만 세므로
  `MN[]` 보정과 무관하다
- ㉡ `avg_iterations[ch_idx]` ([DAO_Main.py:1886, 1935-1937](../../../../../SRC/DAO_Main.py)).
  비교에 쓰이는 곳은 [DAO_Main.py:2541-2544](../../../../../SRC/DAO_Main.py)
  (`ENABLE_AVG_ITER_UPDATE`, [DAO_Config.py:136](../../../../../SRC/DAO_Config.py) 기본 False)와
  [DAO_Main.py:6076-6085](../../../../../SRC/DAO_Main.py)(REORDER_GROUP 모드, 무조건).
  `iter_num -= ITER_MAX_HBF`는 이 값의 절대 척도를 바꾸지만 비교되는 두 matrix가 같은 빌드에서 측정되므로
  **순위를 계통적으로 뒤집지는 않는다.** 로그에 찍히는 절대값의 뜻만 바뀐다

**판정: 부분 유효.** 열 배치는 문서로 닫힌다 (DAO 판정에 들어가지 않으므로).
그러나 ㉢ row 121~124 미도달은 문서로 닫히지 않으므로 이 갈래를 고를 경우
"㉢은 별도 항목으로 남긴다"를 반드시 함께 적어야 한다.
또한 문서에 적을 열 배치는 "열 1~3"이 아니라 **"열 1~4"**여야 한다 (2.1 ㉰).

### 2.5 처방 가설 P5-㉱: mn 0 종료 경로에서 보정을 건너뛴다

**㉮ 1973-1979의 조건문 원문** ([decoder.cpp:1972-1979](../../../../../../0_LDPC_original/src/decoder.cpp)):

```cpp
    /* Output */
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel) {
        if ((MODE_DEC_HD == m_param_dec->init_n || MODE_DEC_1_5SD == m_param_dec->init_n)) {
            if (FLAG_LOW == flag_BF_on) {
                iter_num -= ITER_MAX_HBF;
            }
        }
    }
```

**조건을 덧붙일 필요가 없다. 대상 상황이 도달 불가능하기 때문이다.**

mn 0에서 프레임이 끝나려면 메인 루프가 mn 0에서 `break`해야 한다. 루프 안의 종료 지점은 둘뿐이다.

- ㉠ [decoder.cpp:1947-1959](../../../../../../0_LDPC_original/src/decoder.cpp):
  `if (mn == 0) { CRC_flag = FLAG_HIGH; } else { if (TRUE == Check_End_Iter(&mn)) break; }`
  → **mn 0에서는 `Check_End_Iter`를 아예 부르지 않는다.** 종료 불가
- ㉡ [decoder.cpp:1960-1965](../../../../../../0_LDPC_original/src/decoder.cpp):
  `if (MODE_POWER_STOPPING_ON == m_param_dec->power_index) { if (TRUE == Jump_Iter(&mn)) break; }`
  → `Jump_Iter`([decoder.cpp:4954-5299](../../../../../../0_LDPC_original/src/decoder.cpp))가 TRUE를 돌려주는 길은
  `flag_dec_1iter == FLAG_HIGH`(4958-4971)이거나 2SD, 3SD 갈래의 최종 점프 지점(5075-5079, 5102-5108, 5202-5208, 5270-5276)뿐이다.
  `flag_dec_1iter`는 `Clear_Flag`([decoder.cpp:610](../../../../../../0_LDPC_original/src/decoder.cpp))에서 LOW로 초기화되고
  2SD, 3SD 갈래에서만 HIGH가 된다. **HD 갈래(4973-4983)와 1.5SD 갈래(5280-5290)는 `Set_CSW`만 하고
  함수 끝 [decoder.cpp:5298](../../../../../../0_LDPC_original/src/decoder.cpp) `return FALSE`로 빠진다.**
  1973-1979의 보정은 HD와 1.5SD에만 걸리므로 이 경로로도 mn 0 종료는 없다

따라서 HD, 1.5SD 프레임의 `iter_num`은 항상 `Check_End_Iter`
([decoder.cpp:5344](../../../../../../0_LDPC_original/src/decoder.cpp) 또는
[5355](../../../../../../0_LDPC_original/src/decoder.cpp))에서 mn 1 이상으로 대입된다.
BF 미진입 프레임은 mn 5부터 시작하므로 `iter_num >= 5`이고 보정 뒤 1 이상이다.
**`iter_num`이 음수가 되는 경로는 없다. R2-5의 이 항목(도달 가능성 미확정으로 적힌 부분)은 반박됨.**

**㉯ 보정을 건너뛰면 통계의 뜻이 프레임마다 갈리는가**

건너뛰면 갈린다. 현 보정은 BF 진입 프레임(mn 1~120)과 미진입 프레임(mn 5~124)의 `iter_num`을
같은 1~120 척도로 맞추는 정규화다. 두 종류 모두 실제로 120 mini iteration을 돈다
(진입: 1~120, 미진입: 5~124). 보정을 조건부로 건너뛰면 한쪽만 5~124 척도가 되어
`avg_iteration`과 iteration별 FER 열이 서로 다른 자를 쓰게 된다.
따라서 **보정 자체는 유지가 옳다.**

**판정: 처방 불필요 (대상 반박됨).** 상위 문서에는 "mn 0 종료 경로는 HD, 1.5SD에서 존재하지 않으므로
1973-1979에 조건을 덧붙이지 않는다"라고 적는 편이 낫다.

### 2.6 R2-5 심각도 재판정 제안

Round 2는 HIGH로 두었다. 근거를 나눠 보면 성격이 다르다.

- ㉮ 열 1~4 포화와 머리글 음수: DAO 최적화 판정에 들어가지 않고 로그 표시만 어긋난다 → **LOW~MEDIUM**
- ㉯ `iter_num` 척도 변경: 비교가 같은 빌드 안에서 이루어지므로 순위를 뒤집지 않는다 → **LOW**
- ㉰ `iter_num` 음수: **도달 불가, 반박됨** → 항목 삭제
- ㉱ BF 진입 프레임의 row 121~124 미도달: 디코딩이 파일의 마지막 20 row 중 4개를
  프레임 종류에 따라 쓰거나 안 쓴다. DAO가 최적화하는 대상(LLR row)의 일부가
  절반의 프레임에만 적용된다 → **HIGH 유지 가치가 여기에 있다**

**제안: R2-5를 두 건으로 쪼갠다.** 열 배치와 척도(MEDIUM, 처방 P5-㉮ 후보 ㉡ 또는 P5-㉰)와
row 121~124 비대칭(HIGH, 처방은 Decision 등급이라 사용자 결정 필요)이다.
현재 처방 세 갈래가 뒤엣것을 고치지 못하는데 한 발견 안에 묶여 있어
"처방을 적용하면 닫힌다"는 오해를 부른다.

---

## 3. 임무 2: R2-8 전체 검증

### 3.1 사실 가설 H8: 검사 실패가 어디에도 닿지 않는다

**㉮ `err`의 모든 참조** (`\berr\b`로 [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) 전수):

| 줄 | 형태 | 분류 |
|----|------|------|
| 56 | `int err = FALSE;` | 선언과 초기화 |
| 140 | `err = TRUE;` | 대입 |

**히트 두 개가 전부다. 읽는 곳은 없다.** **확인됨.**

`Read_LLR_info_Auto`의 반환 타입은 `void`다
([local_opt.cpp:52](../../../../../../0_LDPC_original/src/local_opt.cpp) 정의,
[Local_Opt.h:23](../../../../../../0_LDPC_original/src/Local_Opt.h) 선언
`void Read_LLR_info_Auto(PARAM_LLR* LLR_info, PARAM_OPT* OPT_info);`). **확인됨.**

덧붙여 140행의 `err = TRUE`는 `if (NULL == matrix_in)` 안에 있는데,
이 검사는 [local_opt.cpp:60](../../../../../../0_LDPC_original/src/local_opt.cpp)의 `fopen` 직후가 아니라
**132행 `fclose(matrix_in);` 뒤인 139행**에 있다.
파일이 열리지 않았다면 61행의 첫 `fscanf(matrix_in, ...)`에서 이미 널 포인터 역참조로 죽는다.
곧 이 검사 자체가 이미 도달 불가에 가깝다. R2-8이 든 "무효"의 배경으로 함께 적을 값이 있다.

**㉯ code_diff 3.4가 추가하는 검사 코드** ([code_diff.md 3.4](../../code_diff.md#ch3)):

```cpp
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
```

code_diff.md 전체에서 `err`는 이 309행 한 곳뿐이다 (`err\b` 전수 grep).
**수정 후 코드에도 `err`를 읽는 곳이 추가되지 않는다.** 함수는 여전히 void다. **확인됨.**

**㉰ DAO의 subprocess 호출 인자** ([DAO_Main.py:7933-7953](../../../../../SRC/DAO_Main.py)):

```python
        ecc_start = time.time()
        for attempt in range(1, TIME_CONFIG.MAX_ECC_MEMORY_RETRY + 1):
            try:
                if os.name == "nt":  # Windows
                    subprocess.run(["cmd", "/c", os.path.basename(self.batch_path)], cwd=os.path.dirname(self.batch_path), check=True, timeout=SIM_MAX_TIME_OUT)
                else:  # Linux or macOS
                    subprocess.run(["bash", os.path.basename(self.batch_path)], cwd=os.path.dirname(self.batch_path), check=True, timeout=SIM_MAX_TIME_OUT)
                time.sleep(0.5)
                return
            except subprocess.TimeoutExpired:
                self.MPI_Abort(f"[Run_ECC] ECC timeout ({SIM_MAX_TIME_OUT}s) - rank {self.rank}, batch: {self.batch_path}")
            except OSError as error:
                if error.errno == 12:  # Cannot allocate memory
                    delay = random.uniform(0, TIME_CONFIG.MAX_ECC_MEMORY_RETRY_DELAY)
                    self.Write_Log_Lines(f"[Run_ECC] 메모리 할당 실패 (시도 {attempt}/{TIME_CONFIG.MAX_ECC_MEMORY_RETRY}), {delay:.1f}초 후 재시도...")
                    time.sleep(delay)
                else:
                    self.MPI_Abort(f"ECC execution failed: {error}")
            except (subprocess.CalledProcessError, FileNotFoundError) as error:
                self.MPI_Abort(f"ECC execution failed: {error}")
```

인자 유무: `check=True` **있음**, `timeout` **있음**, `stdout` **없음**, `stderr` **없음**, `capture_output` **없음**.
따라서 자식 프로세스는 부모의 표준 출력을 그대로 물려받고 DAO는 그 내용을 프로그램적으로 볼 수 없다. **확인됨.**

DAO가 EXE를 실행하는 다른 지점 전수 (`subprocess\.|os\.system|Popen`으로
[5_DAO/SRC](../../../../../SRC) 전수 grep):

| 줄 | 대상 | 인자 |
|----|------|------|
| [898-905](../../../../../SRC/DAO_Main.py) | `["make"]` (빌드) | `check=True`, `capture_output=True`, `text=True` |
| [7937](../../../../../SRC/DAO_Main.py) | `["cmd", "/c", batch]` | `check=True`, `timeout` |
| [7939](../../../../../SRC/DAO_Main.py) | `["bash", batch]` | `check=True`, `timeout` |

`os.system`과 `Popen` 히트는 없다. **EXE 실행 지점은 7937, 7939 둘뿐이다.** **확인됨.**
(빌드만 출력을 받는데, 이것이 "받을 수 있는데 안 받는다"의 증거다.)

**㉱ `main`의 반환** ([main.cpp:47-70](../../../../../../0_LDPC_original/src/main.cpp)):

```cpp
int main(int argc, char* argv[]) {
    int err = FALSE;
...
    if (1 == argc) { Usage(); }
    else {
        err = Setup(argc, argv);
        if (FALSE == err) {
            Run_Simulation();
        }
    }
...
    return 0;
}
```

`return`/`exit` 전수: `return\s+[0-9]|return\s+err|exit\s*\(`로
[main.cpp](../../../../../../0_LDPC_original/src/main.cpp)를 훑으면
69행 `return 0`이 `main` 안의 유일한 반환이다. 나머지 `return err`(82, 151, 161, 171, 178, 327, 507, 527, 580)는
모두 `Setup*` 계열 함수의 반환이며 `main`은 그 값을 `err`에 담고도 버린다.
**`Setup`이 오류를 돌려줘도 종료 코드는 0이다.** **확인됨.**

더 넓게 `\bexit\s*\(|\babort\s*\(|EXIT_FAILURE|assert\s*\(`로
[0_LDPC_original/src](../../../../../../0_LDPC_original/src) 전체를 훑으면 **히트 0건**이다.
곧 이 프로그램은 어떤 오류에서도 0이 아닌 종료 코드를 내지 않는다. **확인됨.**

**㉲ printf 출력이 어디로 가는가**

- ㉠ 배치 스크립트에 리다이렉션이 없다
  ([DAO_Main.py:6557-6567](../../../../../SRC/DAO_Main.py)):
  Windows는 `@echo off` + `cd /d "%~dp0"` + `"EXE" 인자들`,
  Linux는 `#!/usr/bin/env bash` + `set -euo pipefail` + `cd "$(dirname "$0")"` + `./EXE 인자들`
- ㉡ `subprocess.run`이 `stdout`을 지정하지 않으므로 자식이 DAO 프로세스의 표준 출력을 상속한다
- ㉢ C++이 파일에 쓰는 로그는 `Ref_C_result_%d.txt`
  ([local_opt.cpp:133-183](../../../../../../0_LDPC_original/src/local_opt.cpp),
  [main.cpp:264-326](../../../../../../0_LDPC_original/src/main.cpp),
  [ecc_top.cpp:2035-2060](../../../../../../0_LDPC_original/src/ecc_top.cpp))인데,
  DAO는 이 이름을 [DAO_Constants.py:129](../../../../../SRC/DAO_Constants.py) `HEADER_TO_REMOVE`에 넣어
  [DAO_Main.py:946-957](../../../../../SRC/DAO_Main.py)에서 **삭제만 한다. 읽는 코드는 없다**
  (`Ref_C_result` 전수 grep 히트 1건, 그 상수 정의뿐)

**판정: H8 확인됨.** 3.4의 `err = TRUE`는 흐름을 바꾸지 않고, printf는 DAO가 읽을 수 없는 곳으로 나가며,
종료 코드로도 알 수 없다. **어긋난 파일로 DAO 최적화가 그대로 진행된다는 R2-8의 결론은 그대로 성립한다.**
단, "로그 파일에도 남지 않는다"는 표현은 "DAO가 읽는 어떤 파일에도 남지 않는다"로 고쳐 적는 편이 정확하다.
(작업 스케줄러가 표준 출력을 잡아 두는 환경이라면 사람이 사후에 볼 수는 있다.)

### 3.2 처방 가설 P8: 프로세스를 멈추거나 종료 코드를 바꾸고 DAO가 읽게 한다

**㉮ 0이 아닌 종료 코드가 `check=True`에서 어떻게 보이는가**

- ㉠ Linux 배치는 `set -euo pipefail`
  ([DAO_Main.py:6565](../../../../../SRC/DAO_Main.py))이므로 마지막 명령인 EXE가 0이 아닌 코드로 끝나면
  스크립트가 그 코드로 즉시 끝난다. Windows 배치는 마지막 명령의 코드가 `cmd /c`의 코드가 된다.
  어느 쪽이든 `subprocess.run(..., check=True)`가 `subprocess.CalledProcessError`를 던진다
- ㉡ 그 예외를 잡는 곳: [DAO_Main.py:7951-7952](../../../../../SRC/DAO_Main.py)
  `except (subprocess.CalledProcessError, FileNotFoundError) as error: self.MPI_Abort(...)`.
  **잡힌다.**
- ㉢ `MPI_Abort`([DAO_Main.py:6802-6860 부근](../../../../../SRC/DAO_Main.py))는 로그를 남긴 뒤
  `self.comm.Abort(error_code)`로 **DAO의 모든 rank를 죽인다**
- ㉣ 바람직한가: **조건부로 바람직하다.** 3.4 검사는 입력 파일의 형식 어긋남이고,
  DAO의 모든 rank가 같은 형식의 파일을 쓰므로 한 rank에서 걸리면 나머지도 걸린다.
  조용히 잘못된 최적화를 이어 가는 것보다 낫다.
  **다만 위험이 하나 있다.** DAO는 최적화 도중 trial LLR matrix를 계속 새로 만들어 쓰므로,
  검사가 생성 결과에도 걸리는 종류라면 한 번의 trial 실패가 전체 세션을 죽인다.
  3.4 검사는 "헤더의 그룹별 분기 index와 그 그룹에 속한 row들의 분기 index가 같은가"이고
  이는 파일을 쓰는 쪽(DAO)이 지키기 쉬운 불변식이므로 실용상 위험은 낮다.
  그래도 **상위 문서에 "생성 실패는 trial 폐기, 형식 오류는 중단"의 구분을 적어 두는 편이 안전하다**

**㉯ MPI 경로: AUTO 빌드에서 컴파일되는가**

[mode.h:18-27](../../../../../../0_LDPC_original/src/mode.h) 원문:

```cpp
#if (defined(_WIN64) || defined(_WIN32))
#define __WIN_OS__                  // Windows
#else
#ifdef __PROGRAM_MODE_REF_C__
#define __AUTO_LLR_OPT__
#if !defined(__AUTO_LLR_OPT__)       // LLR matrix loading
#define __RUN_MPI__                 // Supercon
#endif
#endif // __PROGRAM_MODE_REF_C__
#endif
```

`__AUTO_LLR_OPT__`를 정의한 **바로 다음 줄에서** `#if !defined(__AUTO_LLR_OPT__)`를 검사하므로
이 조건은 항상 거짓이다. [mode.h:10](../../../../../../0_LDPC_original/src/mode.h)의
`//#define __RUN_MPI__`도 주석이다.
**AUTO 빌드에서 `__RUN_MPI__`는 정의되지 않는다. 두 스위치는 배타적이다.** **확인됨.**

따라서 다음이 모두 컴파일되지 않는다.

- ㉠ [local_opt.cpp:38-44](../../../../../../0_LDPC_original/src/local_opt.cpp)의 `MPI_Barrier`, `MPI_Bcast` 블록
- ㉡ [main.cpp:49-53, 66-68](../../../../../../0_LDPC_original/src/main.cpp)의 `MPI_Init`, `MPI_Finalize`
- ㉢ [ecc_top.cpp:646-651, 672-678, 935-941](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `Gather_Result_MPI` 경로
- ㉣ [mpi.cpp](../../../../../../0_LDPC_original/src/mpi.cpp) 전체(파일 자체는 컴파일되나 호출이 없다)

또한 DAO 쪽 MPI는 **Python 계층(mpi4py)의 것**이다
([5_DAO/3_run_DAO_mpi.bat:3](../../../../../3_run_DAO_mpi.bat) `mpiexec -n 4 python SRC/DAO_Main.py 1 2 3 4`,
[DAO_Constants.py:135](../../../../../SRC/DAO_Constants.py) `comm = MPI.COMM_WORLD`).
각 Python rank가 자기 배치 파일로 **단일 프로세스 EXE 하나**를 부르며 `mpiexec`로 감싸지 않는다
([DAO_Main.py:6551-6555](../../../../../SRC/DAO_Main.py)).

**결론: "한 rank의 종료가 어떻게 전파되는가"라는 걱정은 C++ 쪽에 실체가 없다.**
전파는 Python 쪽에서 일어나며, 위 ㉮ ㉢대로 `comm.Abort`가 전체를 끝낸다. **확인됨.**
code_diff 3.7이 손대는 MPI 전파 블록도 AUTO 빌드에서는 컴파일되지 않으므로
"어느 쪽인지 확인한 뒤 맞춘다"는 code_diff의 유보는 **AUTO 빌드 한정으로는 답이 이미 나와 있다**
(비AUTO 비Windows 빌드는 현재 `mode.h`로는 만들 수 없다).

**㉰ 정상 파일에서 오탐으로 멈추는가**

3.4 검사가 참이 되는 조건은 "그룹 i에 속한 어떤 row의 `sw_branch_idx`가
헤더의 `sw_branch_idx_each_group[i]`와 다르다"이다.

[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)를
[code_diff.md 3.2, 3.3](../../code_diff.md#ch3)의 파서로 손 실행했다.
`num_group` 12, `num_set_each_group` = `1 7 6 6 1 5 5 7 6 10 10 13` (합 77 = 실제 데이터 row 수).
각 row의 마지막 칸(3.3에서 `sw_branch_idx`로 개명)을 그룹별로 모으면

| 그룹 | row 줄 | row의 마지막 칸 | 그룹 안에서 균일한가 |
|------|--------|----------------|--------------------|
| 0 | 18 | 0 | 예 |
| 1 | 20~26 | 0 (7개 모두) | 예 |
| 2 | 28~33 | 1 (6개 모두) | 예 |
| 3 | 35~40 | 0 (6개 모두) | 예 |
| 4 | 42 | 1 | 예 |
| 5 | 44~48 | 1 (5개 모두) | 예 |
| 6~11 | 50~105 | -1 (전부) | 예 |

**모든 그룹에서 row의 값이 균일하다.** 헤더 줄을 `0 0 1 0 1 1 -1 -1 -1 -1 -1 -1`로 쓰면
검사는 통과하고 오탐이 없다. **확인됨.**

다만 **전제가 하나 있다.** 3.2가 읽는 `sw_branch_idx_each_group` 줄은 지금 파일에 없다.
현재 파일에서 `type_each_group` 자리로 읽히는 11행은 `20 20 21 20 21 21 1 1 1 1 1 1`이며
(앞 여섯 개가 `2X` 꼴로 X가 분기 index와 일치한다),
`num_group` 줄 다음에 오는 줄이 하나 모자란다.
곧 **변환되지 않은 현 파일을 3.2 파서에 넣으면 이후 토큰이 통째로 밀려 3.4가 반드시 걸린다** (R2-6의 사실).
P8을 적용하면 그 상태에서 DAO 세션 전체가 즉시 죽는다.
이것은 오탐이 아니라 정탐이지만, **P8과 R2-6(파일 변환 절차 부재)이 겹치면 첫 실행이 바로 중단된다**는 점을
9장 적용 순서에 적어야 한다. 변환 단계를 P8보다 앞에 두면 해결된다.

**㉱ 대안 처방과 부작용**

| 대안 | 방법 | 부작용 |
|------|------|--------|
| ㉠ `exit(1)` 또는 `main`이 err 반환 | `main`의 `return 0`을 `return err`로 바꾸고 `Read_LLR_info_Auto`가 err를 상위로 올린다 | 반환 타입 변경이 필요하다 (`void` → `int`). `Run_Local_Opt`, `Run_Simulation_Local_Opt`, `Run_Simulation`까지 사슬을 고쳐야 한다. 대신 `exit(1)`을 쓰면 사슬을 안 건드리지만 저장소에 `exit` 용례가 하나도 없어 관례를 깬다. DAO 쪽은 이미 `CalledProcessError`를 잡으므로 추가 수정이 없다. **가장 적은 수정으로 닫힌다** |
| ㉡ DAO가 stdout을 받는다 | [DAO_Main.py:7937, 7939](../../../../../SRC/DAO_Main.py)에 `capture_output=True, text=True`를 넣고 반환 문자열에서 `[Error]`를 찾는다 | 시뮬레이션이 오래 돌면 stdout이 파이프 버퍼를 채워 **자식이 블록되어 교착에 빠질 수 있다** (`subprocess.run`은 통신을 끝까지 하므로 실제로는 메모리에 다 쌓인다. 장시간 실행에서 메모리가 커진다). 또 문자열 매칭은 메시지 문구에 결합되어 깨지기 쉽다. **권하지 않는다** |
| ㉢ C++이 결과 파일에 오류 표시를 남긴다 | `str_result_name_4KB`에 오류 줄을 쓴다 | DAO의 `Read_Ref_C_Result`가 모든 줄을 돌며 `int(parts[1])`을 시도하므로 오류 줄이 `ValueError`를 일으켜 [DAO_Main.py:8263-8270](../../../../../SRC/DAO_Main.py)에서 **3회 재시도 후 결과를 통째로 무시하고 `0, 0, 0, None`을 돌려준다**. 그러면 [DAO_Main.py:1883-1884](../../../../../SRC/DAO_Main.py)의 `total_tests == 0` 검사가 `MPI_Abort`를 부른다. 곧 결과적으로는 멈추지만 원인이 "파싱 실패"로 가려진다. **진단이 나빠진다** |
| ㉣ 결과 파일을 아예 쓰지 않는다 | 검사 실패 시 시뮬레이션을 건너뛰고 결과 파일을 만들지 않는다 | [DAO_Main.py:1823, 1850](../../../../../SRC/DAO_Main.py)이 `os.path.exists`로 건너뛰므로 그 rank의 기여가 0이 되고, 모든 rank가 실패하면 `total_tests == 0`으로 `MPI_Abort`. ㉢과 같은 진단 문제 |

**판정: 처방 유효, 갈래는 ㉠을 권한다.** 근거는 ㉮ ㉡에서 DAO가 이미 `CalledProcessError`를 잡아
명확한 메시지(`ECC execution failed: Command ... returned non-zero exit status 1`)를 로그에 남기기 때문이다.
`exit(1)` 대신 반환 사슬을 고치는 쪽이 저장소 관례에 맞으나 수정 범위가 넓으므로,
**상위 문서에 두 갈래를 나란히 적고 사용자 결정을 받는 편이 낫다** (`main`의 반환은 지금 어느 오류도 전달하지 않으므로,
고치면 3.4 말고 [main.cpp:139-178](../../../../../../0_LDPC_original/src/main.cpp)의 기존 `Print_Input_Err_Code` 경로도
함께 살아난다. 이는 이 작업의 범위를 넘는 개선이라 Decision 등급이다).

### 3.3 R2-8 심각도

Round 2의 HIGH를 유지한다. 근거가 모두 코드에서 확인되었고 반례가 없다.
처방을 적용하지 않으면 3.4를 넣는 의미가 사라진다 (검사가 아무것도 막지 못한다).

---

## 4. 증거 분류 표

| # | 증거 | 판정 | 근거 |
|---|------|------|------|
| 1 | 보정 블록이 `MN[]` 보정과 상한 축소 두 일을 겹쳐 한다 | 확인됨 | [local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp), 소비처 [ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp)와 [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp) |
| 2 | `MODE_DEC_1_SSD`가 저장소에 정의 없음 | 확인됨 | [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp) 단독 히트, [common.h:75-78](../../../../../../0_LDPC_original/src/common.h) |
| 3 | 1.0 고정 열은 1~3이 아니라 1~4다 | 반박됨 (R2-5 정정) | `MN[4]` = 0이고 `iter_num >= 1`이므로 `o_iter_num > 0`이 항상 참. [ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp), [decoder.cpp:1947, 5344](../../../../../../0_LDPC_original/src/decoder.cpp) |
| 4 | 상한을 축소하지 않으면 `type_each_group[-1]` 범위 밖 읽기 | 확인됨 (Round 2보다 강함) | [decoder.cpp:7048-7051](../../../../../../0_LDPC_original/src/decoder.cpp) |
| 5 | `MN[n]` 중간 원소 읽기는 네 곳뿐 | 확인됨 | [ecc_top.cpp:878, 2022, 2054](../../../../../../0_LDPC_original/src/ecc_top.cpp), [main.cpp:317](../../../../../../0_LDPC_original/src/main.cpp) |
| 6 | `Set_Ref_C_Iteration`은 비AUTO 전용, HD 5개 검사점 | 확인됨 | [main.cpp:704-781](../../../../../../0_LDPC_original/src/main.cpp) |
| 7 | 결과 파일 열 수는 `MN_num` | 확인됨 | [ecc_top.cpp:2020, 2052, 2123, 2203, 2274](../../../../../../0_LDPC_original/src/ecc_top.cpp) |
| 8 | DAO 결과 파서는 `Read_Ref_C_Result`이며 `Read_FER_From_File`은 죽은 코드 | 확인됨 (R2-8 인용 정정) | [DAO_Main.py:8187-8273](../../../../../SRC/DAO_Main.py) 호출 [1824, 1851](../../../../../SRC/DAO_Main.py); `Read_FER_From_File` 전수 grep 히트 = 정의뿐 |
| 9 | DAO 파싱은 열 수 변경을 견딘다 | 확인됨 | `parts[result_offset:-3]` ([DAO_Main.py:8244](../../../../../SRC/DAO_Main.py)), 길이 방어 [8241](../../../../../SRC/DAO_Main.py), [1831-1836](../../../../../SRC/DAO_Main.py) |
| 10 | iteration별 FER 열은 로그에만 쓰인다 | 확인됨 | `total_num_error_per_iters`/`total_FER_per_iters` 히트 6개 중 소비는 [7595-7596](../../../../../SRC/DAO_Main.py)뿐 |
| 11 | `MN[MN_num-1]`이 메인 루프 상한이라 검사점 축소가 예산을 건드린다 | 확인됨 | [decoder.cpp:1118-1120](../../../../../../0_LDPC_original/src/decoder.cpp), [local_opt.cpp:126](../../../../../../0_LDPC_original/src/local_opt.cpp) |
| 12 | HD, 1.5SD에서 mn 0 종료 경로가 없다 | 확인됨 (R2-5 항목 반박) | [decoder.cpp:1947-1959](../../../../../../0_LDPC_original/src/decoder.cpp), [4954-4983](../../../../../../0_LDPC_original/src/decoder.cpp), [5280-5298](../../../../../../0_LDPC_original/src/decoder.cpp) |
| 13 | `err` 참조는 선언과 대입 둘뿐, 함수는 void | 확인됨 | [local_opt.cpp:56, 140](../../../../../../0_LDPC_original/src/local_opt.cpp), [Local_Opt.h:23](../../../../../../0_LDPC_original/src/Local_Opt.h) |
| 14 | code_diff가 `err`를 읽는 코드를 추가하지 않는다 | 확인됨 | [code_diff.md:309](../../code_diff.md) 단독 히트 |
| 15 | DAO subprocess에 `stdout`, `stderr`, `capture_output` 없음 | 확인됨 | [DAO_Main.py:7937, 7939](../../../../../SRC/DAO_Main.py) |
| 16 | EXE 실행 지점은 두 곳뿐 | 확인됨 | `subprocess\.|os\.system|Popen` 전수, 히트 [898, 7937, 7939](../../../../../SRC/DAO_Main.py) |
| 17 | `main`은 return 0 고정, 저장소 전체에 exit/abort/assert 없음 | 확인됨 | [main.cpp:69](../../../../../../0_LDPC_original/src/main.cpp), `\bexit\s*\(|\babort\s*\(|EXIT_FAILURE|assert\s*\(` 전수 히트 0 |
| 18 | printf는 DAO가 읽는 어떤 파일에도 남지 않는다 | 확인됨 | 배치에 리다이렉션 없음 [DAO_Main.py:6557-6567](../../../../../SRC/DAO_Main.py), `Ref_C_result`는 삭제 대상 [DAO_Constants.py:129](../../../../../SRC/DAO_Constants.py) |
| 19 | 0 아닌 종료 코드는 `MPI_Abort`로 DAO 전체를 끝낸다 | 확인됨 | `set -euo pipefail` [DAO_Main.py:6565](../../../../../SRC/DAO_Main.py), 예외 처리 [7951-7952](../../../../../SRC/DAO_Main.py), `comm.Abort` [6812](../../../../../SRC/DAO_Main.py) |
| 20 | AUTO 빌드에서 `__RUN_MPI__`가 정의되지 않는다 | 확인됨 | [mode.h:18-27](../../../../../../0_LDPC_original/src/mode.h)의 `#if !defined(__AUTO_LLR_OPT__)`가 항상 거짓 |
| 21 | 3.4 검사가 변환된 정상 파일에서 오탐을 내지 않는다 | 확인됨 | [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 그룹별 마지막 칸 균일 (18, 20-26, 28-33, 35-40, 42, 44-48, 50-105행) |
| 22 | 140행 `if (NULL == matrix_in)`는 `fclose` 뒤에 있어 이미 도달 불가에 가깝다 | 확인됨 (보강) | [local_opt.cpp:60-61, 132, 139-142](../../../../../../0_LDPC_original/src/local_opt.cpp) |

---

## 5. 상위 문서에 반영을 권하는 것

- ㉮ R2-5를 **열 배치, 척도(MEDIUM)** 와 **row 121~124 비대칭(HIGH, Decision)** 두 건으로 쪼갠다.
  현재 처방 세 갈래는 앞엣것만 닫는다
- ㉯ 열 표기를 "열 1~3"에서 **"열 1~4"**로 고친다
- ㉰ R2-5의 "mn 0 종료 프레임 `iter_num` -4" 항목을 삭제한다 (도달 불가)
- ㉱ P5-㉮를 고를 경우 후보 ㉡(`MN_num`까지 줄이기)을 기본으로 적고,
  후보 ㉠(마지막 원소만)의 뒤쪽 죽은 열 셋을 부작용으로 적는다
- ㉲ P5-㉯를 고를 경우 "마지막 원소는 파일 값을 유지한다"를 반드시 함께 적는다.
  비AUTO 상수 배열을 그대로 가져오면 파일 기반 iteration 예산이 무너진다
- ㉳ R2-8의 "DAO는 결과 파일의 마지막 줄 마지막 토큰을 읽는다"는 서술을 지운다.
  실제 파서는 [DAO_Main.py:8187-8273](../../../../../SRC/DAO_Main.py)이고
  `Read_FER_From_File`은 호출자가 없다
- ㉴ P8 처방에 "AUTO 빌드에서 `__RUN_MPI__`는 정의되지 않으므로 C++ 쪽 MPI 전파 걱정은 없다"를 적는다.
  code_diff 3.7의 유보("어느 쪽인지 확인한 뒤 맞춘다")도 이 결론으로 닫힌다
- ㉵ 9장 적용 순서에서 **파일 변환 단계를 P8(중단 처방)보다 앞**에 둔다.
  변환 전 파일은 3.4를 반드시 걸리게 하므로 순서가 뒤바뀌면 첫 실행이 즉시 중단된다
