# Round 3 / worker_b_1. F2 (HIGH) 검증: matrix 경로 dv=2 영구 미정정의 원인 판정

> 작성: 2026-08-06 23:34:12
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/decoder.py` `_decode_matrix()`
> 대조 원본: `0_LDPC_original/` (`decoder.cpp`, `common.h`, `mode.h`, `local_opt.cpp`, `build.bat`) 읽기 전용, 빌드 안 함
> 실증: 스크래치패드 사본에서 Python 실행 (프로젝트 파일 무수정, numpy 1.26.4)
> 참고 문서(독립 재확인 대상): `../r2_round2_lv1_analysis/agent_4.md` §H-1, `agent_1.md` §2

---

## 0. 결론 요약

| 질문 | 결론 |
|------|------|
| A | **구현 결함이 아니다.** 같은 테이블을 넣으면 C++ 원문도 dv=2를 동일하게 영구 미정정으로 만든다. 근거 ㉮~㉳ 전부 원문에서 확인됨 |
| B | **처방은 타당하다.** 경계는 `>`가 맞고 restart row(ch=-1)는 오탐하지 않는다. 다만 dv 구간이 넓은 파일에서 미탐이 나지 않도록 검사 기준을 column degree로 잡아야 한다 |
| C | **대체로 부합하나 네 곳이 과하거나 부족하다.** "전량", "C++도 동일할 산술"(무조건 서술), "구현 버그 아님"(조치 불요로 읽힘), "토이 매트릭스"(탐색 공간 문제 누락) |

**F2 재분류 제안: 토이 데이터 + 검출 장치 부재. 심각도 HIGH 유지.**
Round 2가 남긴 두 갈래 중 "도메인 불일치(구현 결함)" 갈래는 **반박됨**이다. 5-bit 채널값과 3-bit
edge 값이 같은 가산기에 섞이는 것은 원문 그대로의 설계이고, 벤더 자신의 3-bit 하드코딩 테이블은
그 상태에서 `ch <= 7*dv`를 전 degree에서 지킨다.

---

## 1. 확인한 빌드 전제

| 스위치 | 상태 | 근거 | 분류 |
|--------|------|------|------|
| `__4_BIT_LLR__` | 주석 처리 → 3-bit 분기 활성 | `mode.h:12` | 확인됨 |
| `__PROGRAM_MODE_REF_C__` | **주석 처리** | `mode.h:8` | 확인됨 |
| `__AUTO_LLR_OPT__` | `__PROGRAM_MODE_REF_C__` 정의 + 비Windows에서만 정의 | `mode.h:18-27` | 확인됨 |
| `flag_BF_on` | AUTO에서 `Select_BF()`가 무조건 `FLAG_LOW` | `decoder.cpp:2084-2085` | 확인됨 |
| `ITER_MAX_HBF` | AUTO에서 0 | `common.h:403-404` | 확인됨 |
| `__HD_FLOOR_SET__` | 주석 처리 | `mode.h:73` | 확인됨 |

**추가 지적 (리뷰 전제와 어긋남)**: 저장소의 `build.bat`은 MSVC `cl`을 쓰는 Windows 빌드다
(`build.bat:2`, `build.bat:5`). Windows에서는 `mode.h:18-19`가 `__WIN_OS__` 분기를 타므로
`__AUTO_LLR_OPT__`가 **정의되지 않는다**. 게다가 `mode.h:8`의 `__PROGRAM_MODE_REF_C__`도 주석
처리되어 있다. 즉 **저장소 현 상태의 `build.bat`으로는 리뷰가 기준으로 삼은 AUTO 프로파일이
만들어지지 않는다.** AUTO 프로파일은 ㉮ `mode.h:8` 주석 해제와 ㉯ 비Windows 컴파일러, 두 가지를
모두 갖춰야 성립한다. 이것이 F2의 판정을 바꾸지는 않으나, "C++도 동일하다"는 서술의 조건을
명시해야 하는 이유가 된다 (질문 C 참조).

참고로 비AUTO 경로의 임계값 테이블 `Get_VNU_Th_Adaptive`는 `int table_HD[...]`가 초기화자 없이
선언만 되어 있어(`decoder.cpp:7143-7145`) 값이 비어 있다. 채널값 테이블
`Get_VNU_Ch_LLR_Adaptive`의 `Ch_LLR_HD`는 값이 남아 있다(`decoder.cpp:6693`, `6777-6839`).

---

## 2. 질문 A: C++ 원문도 같은 테이블에서 dv=2가 영구 미정정인가

### ㉮ `sum_t = channel_llr`이고 `channel_llr = ch1`(테이블 값 그대로)인가 (**확인됨**)

- `decoder.cpp:3976` `int sum_t, temp, temp_nq;` (부호 있는 int)
- `decoder.cpp:4017-4020` `if (TRUE == bTable) { ... channel_llr = ch1; }`
- `decoder.cpp:4026` `sum_t = channel_llr;`
- ch1 역추적: `decoder.cpp:3986` `Get_VNU_LLR_SET_FILE(v_deg, col_idx, cur_set_idx, &ch1, ...)`
  → `decoder.cpp:7089` `*ch1 = m_param_LLR->LLR_MATRIX[table_row_idx][table_col_idx];`
  → `local_opt.cpp:108-109` `fscanf(matrix_in, "%d", &c); LLR_info->LLR_MATRIX[i][j] = c;`

**파일에서 읽은 정수가 `sum_t`의 초기값이 되기까지 스케일링, 시프트, 클리핑이 하나도 없다.**
`LLR_MATRIX`에 대한 쓰기는 `local_opt.cpp:109` 한 곳뿐이고 읽기는 `decoder.cpp:7089` 계열뿐이다
(grep 전수). 채널값이 테이블 값에서 바뀌는 경우는 다음 셋뿐이며 예시 부호에는 해당 사항이 없다.

- ㉠ 쇼트닝 구간: `channel_llr = CH_LLR_MAX`(= 31). 근거 `decoder.cpp:3995-3997`, `common.h:375`
- ㉡ 펑처링 구간: `channel_llr = CH_LLR_MIN`(= 0). 근거 `decoder.cpp:3999-4005`, `4013-4015`
- ㉢ Power stopping: `channel_llr = CH_LLR_MAX`. 근거 `decoder.cpp:4021-4024`. 이 경로는 ch를 오히려
  31로 **키우므로** dv=2 미반전을 완화하지 않는다

### ㉯ VN 누산 루프에서 5-bit ch와 3-bit edge가 같은 가산기에 섞이는가 (**확인됨**)

- `decoder.cpp:4039-4042`
  ```c
  for (ii = 0; ii < v_deg; ii++) {
      mux_idx = m_PCM->Mux_idx[ii][col_idx];
      sum_t = sum_t + VNU_in[mux_idx][j];
  }
  ```
- `VNU_in`의 값 도메인: `decoder.cpp:2402-2405`가 min 레지스터의 V 도메인 코드
  {`V_VERY_STRONG`=3, `V_NORMAL_STRONG`=2, `V_NORMAL_WEAK`=1, 그 외 0}을 EDGE 도메인
  {7, 5, 3, 1}로 사상하고, `decoder.cpp:2409`에서 부호를 붙여 `decoder.cpp:2410`
  `VNU_in[mux_index][j] = check_out;`으로 대입한다. 즉 `|VNU_in| <= EDGE_MAG_7 = 7`이 항상 성립한다
- 상수 정의: `common.h:338-346` (3-bit 분기), `common.h:375` `CH_LLR_MAX 31`

**따라서 "테이블에서 온 0~31 범위의 채널값"과 "최대 크기 7인 edge 값"이 같은 `int sum_t`에
누산되는 구조는 원문 그대로다.** 이것은 도메인 불일치 버그가 아니라 원 설계다 (dv가 낮을수록
채널값을 크게 주어 edge의 견인력을 상쇄시키는 것이 테이블 설계 의도로 보인다).

### ㉰ 3-bit 분기가 실제 활성 분기인가 (**확인됨**)

- `common.h:337-348`의 `#else` 블록(3-bit)이 활성. `mode.h:12`에서 `__4_BIT_LLR__` 주석 처리
- `flag_BF_on`이 AUTO에서 `FLAG_LOW`(`decoder.cpp:2084-2085`)이므로 `VN_Cal_HD`의 1-bit precision
  분기(`decoder.cpp:4056-4079`)는 진입하지 않고, 항상 4레벨 캐스케이드 분기
  (`decoder.cpp:4080-4120`, 3-bit는 `4112-4115`)를 탄다
- `C2V_Cal`의 1-bit precision 분기(`decoder.cpp:2373-2384`)도 같은 이유로 미진입

### ㉱ `sum_t`에 포화나 클리핑이 있는가, VN 판정문 원문 (**없음, 판정문 확인됨**)

- `decoder.cpp:3973-4129` 전체를 읽었다. `sum_t`는 `3993`(0 대입), `4026`(channel_llr 대입),
  `4041`(누산)에서만 쓰이고, 판정(`4044`)과 `temp` 계산(`4052`) 사이에 clamp나 saturate가 없다
- 판정: `decoder.cpp:4044-4045`
  ```c
  if (sum_t > 0)  cwc[bit_pos] = Variable_mem[bit_pos];
  else            cwc[bit_pos] = (Variable_mem[bit_pos] + 1) % 2;
  ```
  즉 **반전 조건은 `sum_t <= 0`**이다. Python `decoder.py:398` `flip = total <= 0`과 등호 위치까지 같다

### ㉲ C++에 `ch > EDGE_MAG_7 * dv`를 막는 검증이나 클리핑이 있는가 (**없음, 확인됨**)

LLR matrix 로더는 `LOCAL_OPT::Read_LLR_info_Auto`(`local_opt.cpp:52-132`) 하나뿐이다
(`Read_LLR_info` grep 전수, 다른 리더 없음. `input.cpp`는 H-matrix 전용).

- ㉠ 범위 검사 없음. `fscanf(matrix_in, "%d", &c); LLR_info->LLR_MATRIX[i][j] = c;`
  (`local_opt.cpp:107-110`)가 전부이고 상하한 비교가 없다
- ㉡ dv별 정합성 검사 없음. `dv_from`/`dv_to`는 `local_opt.cpp:65-72`에서 읽기만 한다
- ㉢ `max_value`/`min_value`는 `local_opt.cpp:91-100`에서 읽어 `local_opt.cpp:164-167`의
  `fprintf`로 **로그에 찍을 뿐** 클램프에 쓰이지 않는다 (grep 전수: `local_opt.cpp` 내부와
  소멸자, `ecc_data.h:191-192` 선언이 전부)
- ㉣ `floor_flag`도 `local_opt.cpp:114`에서 읽어 `local_opt.cpp:178`에서 찍기만 한다.
  `state_hd_error_floor_set`은 printf 인자(`decoder.cpp:7049`, `7070`)와 `__HD_FLOOR_SET__` 블록
  (`decoder.cpp:8100-8104`, 스위치 off)에만 쓰이고 `ch1`을 건드리지 않는다
- ㉤ 파일 열기 실패 검사조차 `fclose` **뒤**에 있다 (`local_opt.cpp:60` fopen → `132` fclose →
  `139` `if (NULL == matrix_in)`). 로더 전반이 무방비다

**즉 C++도 무방비다.** ch가 `EDGE_MAG_7 * dv`를 넘는 테이블을 넣으면 아무 경고 없이 받아들이고,
해당 degree의 column은 영구히 반전되지 않는다.

### ㉳ C++가 dv=2 column을 특별 취급하는가 (**하지 않는다, 확인됨**)

- `VN_Cal_HD`의 `v_deg`는 실제 column degree다: `decoder.cpp:5704`
  `VN_Cal_HD(m_PCM->ColW[jj], idx_offset, mn);`
- AUTO 경로의 dv 매핑은 구간 매칭뿐이다: `decoder.cpp:7078-7083`
  ```c
  for (i = 0; i < m_param_LLR->num_dv; i++)
      if ((dv >= m_param_LLR->dv_from[i]) && (dv <= m_param_LLR->dv_to[i])) {
          table_col_idx = i * m_param_LLR->num_para_each_set; break; }
  ```
  dv=2 전용 상수도, dv별 산술 분기도, col_idx fallback도 없다
- 유일한 특이점은 **미매칭 dv일 때 `table_col_idx`가 0으로 남아 첫 dv 그룹 값을 조용히 쓴다**는
  것이다 (`decoder.cpp:7075` 초기화). Python은 이 fallback을 재현하지 않고 에러를 낸다
  (`llr_matrix.py:144-147`, 사용자 결정). F2와는 별건이다
- 비AUTO 경로에는 `dv <= 2 → PRIME_LLR_TABLE_IDX_DV2`(`decoder.cpp:6943`, `7157`) 매핑이 있으나
  이는 하드코딩 테이블의 열 선택일 뿐 산술 분기가 아니다

### ㉴ (지시서에 없던 추가 근거) 벤더 자신의 3-bit 테이블은 이 부등식을 지킨다 (**확인됨**)

비AUTO 경로의 하드코딩 채널값 테이블 `Ch_LLR_HD`(`decoder.cpp:6693` 선언)의 3-bit 분기
(`decoder.cpp:6777-6839`)는 **63개 row 전부가 `{21, 14, 12, 10}`**이다 (전 row 기계 확인).

열 인덱스 사상은 `common.h:672-676`이다.

| 열 index | 상수 | 대상 dv | ch | `7 * dv` (가장 빡빡한 dv 기준) | 판정 |
|---|---|---|---|---|---|
| 0 | `PRIME_LLR_TABLE_IDX_MAXDV` / `_MIDDV` | dv >= 5 | 21 | 35 | ch <= 7dv |
| 1 | `PRIME_LLR_TABLE_IDX_DV4` | dv == 4 | 14 | 28 | ch <= 7dv |
| 2 | `PRIME_LLR_TABLE_IDX_DV3` | dv == 3 | 12 | 21 | ch <= 7dv |
| 3 | `PRIME_LLR_TABLE_IDX_DV2` | dv <= 2 | **10** | **14** | ch <= 7dv (여유 4) |

dv 매핑 근거는 `decoder.cpp:6939-6943`, 인덱스 상수는 `common.h:672-676`
(`PRIME_LLR_TABLE_IDX_DV2 = 3`).

**이것이 F2 판정의 결정적 근거다.** 벤더가 같은 산술 구조 위에서 실제로 쓰는 3-bit HD 채널값은
dv=2에 대해 10이며, 이는 상한 14보다 작다. 즉 `ch <= EDGE_MAG_7 * dv`는 원 설계가 지키는 암묵
불변식이고, 토이 파일의 `ch(dv=2) = 28`은 그 불변식을 깬 값이다.

### 질문 A 소결

**같은 테이블을 넣으면 C++ 원문도 동일하게 dv=2를 영구 미정정으로 만든다.** Python 쪽 산술은
원문 그대로이며 도메인 불일치는 존재하지 않는다. 다만 다음 두 가지가 남는다.

- ㉮ 두 파일의 `max_value`가 4개 파라미터 모두 31로 주어져 있고 dv별 구분이 없다 (`HD_0.txt:17`,
  `HD_1.txt:16`). 즉 DAO 최적화기가 dv=2에 대해서도 15~31을 탐색할 수 있는 설정이며, 이 구간은
  전부 영구 미정정이다. 토이 파일만의 문제라고 단정하기 어려운 부분이다
- ㉯ C++는 최적화 루프 안에서 FER이 나쁘면 그 후보를 버리므로 자체 교정되지만, 손으로 쓴 테이블이나
  단일 시뮬레이션에서는 원인 표시 없이 FER ≡ 1.0만 나온다. 검출 장치가 없다는 점은 C++과 Python이
  똑같다

---

## 3. 질문 B: 처방 `ch_table[dv] > edge_mag[0]*dv` 검사의 검증

### ㉮ restart row 오탐 여부 (**오탐하지 않음, 실측 확인**)

`LLR_MATRIX_HD_0.txt:22`의 restart row는 16개 값이 전부 -1이다. 어떤 dv에 대해서도
`-1 > 7*dv`가 거짓이므로 검사에 걸리지 않는다. 아래 §㉰ 표의 row 1 네 줄이 실측이다.
`LLR_MATRIX_HD_1.txt`에는 restart가 없다.

### ㉯ 검사 대상 row 범위와 경계 조건 (**전 row 검사가 안전, 경계는 `>`가 맞음, 실측 확인**)

- **row 범위**: restart row는 ch=-1이라 자동으로 통과하므로 굳이 제외할 필요가 없다. 일반 파일의
  restart row가 양수 ch를 가질 수도 있으므로 **전 row를 검사하는 편이 안전하다**
- **`>` 대 `>=`**: `ch == 7*dv`이면 `total`의 최솟값이 정확히 0이고, 반전 조건이 `total <= 0`
  (`decoder.py:398`)이므로 **반전이 가능하다**. 따라서 `>=`는 오탐이 된다. 실측으로 확정했다.

```
LLR_MATRIX_HD_1.txt, dv=2 column마다 1비트 에러를 심어 각각 디코딩 (17개 column 전수)
  ch(dv=2)=15  ( > 14) : 정정  0/17
  ch(dv=2)=14  (== 14) : 정정 13/17     <-- 반전이 실제로 일어난다
  ch(dv=2)=13  ( < 14) : 정정 13/17
```

`ch=14`에서 정정이 13/17에 그치는 것은 반전 자체는 일어나되 다른 column 판정이 함께 틀리는
별개 동역학 때문이다 (`ch=13`도 같은 4개 column에서 실패). 즉 이 검사는 **필요조건**이지
충분조건이 아니다 (§㉱ 참조).

### ㉰ 두 LLR 파일 전 row × 전 dv 판정표 (실측)

`edge_mag[0] = 7` (`decoder.py:68`).

**`Input/LLR/LLR_MATRIX_HD_0.txt`** (max_iter=5, restart={2})

| row | iter 구간 | restart | dv | ch | th | `7*dv` | `ch > 7dv` | `ch >= 7dv` | 판정 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1-1 | 아니오 | 11 | 1 | 28, 9, 5 | 77 | 거짓 | 거짓 | 반전 가능 |
| 0 | 1-1 | 아니오 | 4 | 10 | 10, 9, 4 | 28 | 거짓 | 거짓 | 반전 가능 |
| 0 | 1-1 | 아니오 | 3 | 13 | 31, 10, 7 | 21 | 거짓 | 거짓 | 반전 가능 |
| 0 | 1-1 | 아니오 | 2 | **28** | 12, 10, 8 | 14 | **참** | 참 | **영구 미반전** |
| 1 | 2-2 | 예 | 11 | -1 | -1, -1, -1 | 77 | 거짓 | 거짓 | 반전 가능 |
| 1 | 2-2 | 예 | 4 | -1 | -1, -1, -1 | 28 | 거짓 | 거짓 | 반전 가능 |
| 1 | 2-2 | 예 | 3 | -1 | -1, -1, -1 | 21 | 거짓 | 거짓 | 반전 가능 |
| 1 | 2-2 | 예 | 2 | -1 | -1, -1, -1 | 14 | 거짓 | 거짓 | 반전 가능 (오탐 없음) |
| 2 | 3-5 | 아니오 | 11 | 5 | 28, 9, 5 | 77 | 거짓 | 거짓 | 반전 가능 |
| 2 | 3-5 | 아니오 | 4 | 10 | 10, 9, 4 | 28 | 거짓 | 거짓 | 반전 가능 |
| 2 | 3-5 | 아니오 | 3 | 13 | 31, 10, 7 | 21 | 거짓 | 거짓 | 반전 가능 |
| 2 | 3-5 | 아니오 | 2 | **28** | 12, 10, 8 | 14 | **참** | 참 | **영구 미반전** |

**`Input/LLR/LLR_MATRIX_HD_1.txt`** (max_iter=20, restart 없음)

| row | iter 구간 | dv | ch | th | `7*dv` | `ch > 7dv` | 판정 |
|---|---|---|---|---|---|---|---|
| 0 | 1-1 | 11 | 1 | 28, 9, 5 | 77 | 거짓 | 반전 가능 |
| 0 | 1-1 | 4 | 10 | 10, 9, 4 | 28 | 거짓 | 반전 가능 |
| 0 | 1-1 | 3 | 13 | 31, 10, 7 | 21 | 거짓 | 반전 가능 |
| 0 | 1-1 | 2 | **28** | 12, 10, 8 | 14 | **참** | **영구 미반전** |
| 1 | 2-20 | 11 | 5 | 28, 9, 5 | 77 | 거짓 | 반전 가능 |
| 1 | 2-20 | 4 | 10 | 10, 9, 4 | 28 | 거짓 | 반전 가능 |
| 1 | 2-20 | 3 | 13 | 31, 10, 7 | 21 | 거짓 | 반전 가능 |
| 1 | 2-20 | 2 | **28** | 12, 10, 8 | 14 | **참** | **영구 미반전** |

두 파일 모두 `dv_from == dv_to`(11, 4, 3, 2)라 dv 구간이 단일 값이다.
예시 부호 `example_18x147_z256.qc`의 column degree 분포는 dv=2: 17블록(4352 bit, 11.56%),
dv=3: 1블록, dv=4: 129블록이다. **오탐 0건, 미탐 0건.**

### ㉱ 검사의 엄밀성 논증 (**필요조건으로서 옳고, degree만으로 세울 수 있는 가장 타이트한 부등식**)

**보조정리 1. `|C2V| <= 7`이 항상 성립한다.**
C2V의 크기는 `decoder.py:392` `mag = np.where(pos == e, min2, min1)`로 정해진다. `min1`/`min2`에
들어가는 값은 다음 셋뿐이다.

- ㉠ 초기값 `RESET = edge_mag[0] = 7` (`decoder.py:353`, `357-358`)
- ㉡ restart 클리어 값 `RESET` (`decoder.py:375-376`, `417`, `421`)
- ㉢ `mag_new = |v2c|`인데 `v2c`는 `_mx_vnu_quantize`의 출력 `sgn * self._edge_mag[lvl]`이고
  (`decoder.py:96`, `102`), `lvl`은 지시함수 3개의 합이라 항상 0~3이므로
  `mag_new ∈ {7, 5, 3, 1}` (`decoder.py:94-96`, `decoder.py:68`)

따라서 `|C2V| <= 7`. 실측으로도 `_mx_vnu_quantize`가 방출한 `|v2c|` 집합은 정확히 `{1, 3, 5, 7}`
이었다.

**보조정리 2. 하한 `-7*dv`는 실제로 도달된다.**
Edge clear iteration(iteration 1 또는 restart)에서는 `min1 = min2 = RESET = 7`, `pos = -1`이므로
모든 edge의 `|C2V| = 7`이고 부호는 `synd ^ 0 ^ 0 = synd`다 (`decoder.py:373-379`, `392-394`).
해당 column에 인접한 dv개 check가 모두 미충족이면 `Σ C2V = -7*dv`가 정확히 달성된다.
dv=2 column에 단일 비트 에러가 있으면 두 인접 check가 모두 미충족이므로 이 조건이 성립한다.

**정리.** `total = ch + Σ_{k=1..dv} C2V_k >= ch - 7*dv` (보조정리 1). 반전 조건은
`total <= 0`(`decoder.py:398`)이므로 반전이 한 번이라도 가능하려면 `ch - 7*dv <= 0`,
즉 **`ch <= 7*dv`가 필요하다.** 대우로 **`ch > 7*dv`이면 그 degree의 column은 수학적으로 반전이
불가능하다.** 보조정리 2에 의해 하한이 실제로 달성되므로 이 부등식은 degree 정보만으로 세울 수
있는 가장 타이트한 형태이고, 경계 `ch == 7*dv`에서는 `total == 0`이 되어 반전이 일어난다
(§㉯ 실측과 일치). **`>=`가 아니라 `>`가 맞다.**

`ch < 0`(restart row)이면 `ch - 7*dv < 0`이 자명하므로 검사에 걸리지 않는다.

**더 정확한 검사가 가능한가**: 불가능하다. 실제 `Σ C2V`의 도달 가능 최솟값은 min1/min2 동역학과
syndrome 상태에 의존하므로 닫힌 식으로 쓸 수 없다. 반대로 이 검사를 느슨하게 하면(`>=`) 오탐이
생긴다. 따라서 **"이 조건에 걸리면 확실히 죽는다"는 필요조건 검사가 정답이고, 걸리지 않는다고
정정이 보장되지는 않는다**는 점을 경고 문구에 넣어야 한다.

### ㉲ 처방 보강 제안 (Round 2 원문에 빠진 부분)

- ㉠ **dv 구간 처리**: Round 2 처방은 "`ch_table[dv] > edge_mag[0]*dv`인 dv 구간"이라고만 적어
  `dv_from != dv_to`인 파일에서 어느 dv를 쓸지 모호하다. 구간의 **최대** dv를 쓰면 미탐이 난다
  (예: dv_from=5, dv_to=11에 ch=50이면 dv=5 column은 `50 > 35`로 죽는데 dv=11 기준
  `50 <= 77`이라 통과). 가장 정확한 형태는 `decoder.py:67`에서 이미 계산하는 `self._col_dv`와
  `code.col_deg`를 짝지어 **column 단위로** 검사하는 것이다. 이러면 부호에 존재하지 않는 degree
  구간의 나쁜 값을 잘못 경고하는 일도 없다
- ㉡ **검사 위치**: `MinSumDecoder.__init__`의 `llr_matrix` 블록(`decoder.py:56-70`)에서
  `self._col_dv`와 `self._edge_mag`가 확정된 직후가 자연스럽다
- ㉢ **경고인가 차단인가**: 이 조건은 "정정 불가"를 확정하므로 차단(예외)이 정당하다. 다만
  DAO 최적화기가 후보 탐색 중 이 영역을 지나갈 수 있으므로, 최적화 루프에서 쓸 때는 예외보다
  경고 + FER 1.0 반환이 편할 수 있다. 기본은 경고로 두고 엄격 모드 플래그를 주는 편이 안전하다

---

## 4. 질문 C: `README.md:114-117` 서술 검증

**원문**

> `LLR_MATRIX_HD_1.txt`(restart 없는 20-iter 테스트용)로 수렴 확인. 잔여 floor는
> 전량 dv2 파리티 비트로 확인됨 — 이 토이 매트릭스의 dv2 ch=28이 dv2 최대 CN
> 견인력(2×7=14)보다 커서 파리티 비트가 read 값에 고정되는 구조 (C++도 동일할 산술,
> 매트릭스 값의 문제이지 구현 버그 아님)

### 부합하는 부분 (확인됨)

- ㉮ "dv2 ch=28", "2×7=14" 산술 정확 (§3 ㉰ 표)
- ㉯ "read 값에 고정" 정확. `flip`이 항상 거짓이므로 판정 bit는 `r_bit ^ 0 = r_bit`로 고정된다
  (`decoder.py:398-399`)
- ㉰ "dv2 파리티 비트" 정확. dv=2 column block은 130~146이고, 파리티 column은 마지막 M_b=18개
  (129~146)이므로 dv=2 column은 전부 파리티다 (column 129만 dv=3)
- ㉱ "매트릭스 값의 문제" 확인됨. 벤더 3-bit 테이블은 dv=2에 ch=10을 쓴다 (§2 ㉴)

### 과하거나 부족한 부분 (지적)

- ㉮ **"전량"은 과하다.** 실측하면 잔여 에러의 88.9~96.6%가 dv=2 column이고 나머지 3~5 bit는
  다른 degree의 column이다. dv=2에 고착된 에러가 인접 check의 syndrome을 영구히 오염시켜 이웃
  column 판정을 끌어내리는 2차 효과다. 정확한 서술은 "잔여 floor의 대부분이 dv2 파리티 비트이고,
  dv2 잔여 수는 주입된 dv2 에러 수와 정확히 일치하며 거기에 소수의 2차 오염이 얹힌다"이다

  ```
  300 에러 무작위, HD_1, 20 iteration (batch 8 중 4프레임)
    frame 0: 잔여  27 bit, dv2  24 (88.9%)   [주입된 dv2 에러 24]
    frame 1: 잔여  29 bit, dv2  28 (96.6%)   [주입된 dv2 에러 28]
    frame 2: 잔여  37 bit, dv2  34 (91.9%)   [주입된 dv2 에러 34]
    frame 3: 잔여  36 bit, dv2  32 (88.9%)   [주입된 dv2 에러 32]
  ```

- ㉯ **"C++도 동일할 산술"은 무조건 서술이라 부정확하다.** 동일해지는 조건은 "C++이 AUTO 빌드
  (`__AUTO_LLR_OPT__`, 파일 테이블 경로)로 **같은 테이블 파일**을 읽을 때"다. 저장소 현 상태의
  `build.bat`(MSVC/Windows)은 그 프로파일을 만들지 않고(§1), 그 비AUTO 경로가 쓰는 벤더 하드코딩
  테이블은 dv=2에 ch=10이라 반전이 가능하다 (`decoder.cpp:6777-6839`, `common.h:676`). 조건을
  명시하지 않으면 "C++ 원문도 이 부호에서 dv2를 못 고친다"로 오독될 수 있다

- ㉰ **"구현 버그 아님"은 맞지만 부족하다.** 이 표현은 "그러므로 조치 불요"로 읽힐 여지가 있는데,
  실제 상태는 다음과 같다.
  - ㉠ 저장소의 `config.json` 그대로 `run.py`를 돌리면 **FER이 정확히 1.0**이다. `fixed_error`
    points가 [200, 300]인데 (`config.json:20`), dv=2 영역이 전체의 11.56%라 200비트 에러에서
    dv=2를 하나도 안 맞을 확률이 2.1e-11이다. 실측 결과 batch 64에서 64/64 프레임 모두 dv=2 에러를
    포함했고 FER = 1.0000이었다
  - ㉡ 그 원인을 알려주는 장치가 Python에도 C++에도 없다 (§2 ㉲)

  즉 정확한 분류는 **"구현 결함은 아니지만 검출 장치 부재로 조용히 전멸하는 상태"**다. README는
  후자를 적지 않았다

- ㉱ **"토이 매트릭스"라는 한정이 낙관적이다.** 두 파일의 `max_value`가 파라미터 4개 모두 31이고
  dv별 구분이 없다 (`HD_0.txt:17`, `HD_1.txt:16`). 즉 DAO 최적화기의 탐색 공간 자체가 dv=2에
  대해 15~31이라는 영구 미정정 구간을 포함한다. 토이 파일 하나를 고치면 끝나는 문제가 아니라,
  실물 최적화에서도 재발할 수 있는 영역이라는 점을 함께 적는 편이 정확하다

---

## 5. 실증 기록

스크래치패드에 `LDPC_base/`와 `Input/`을 복사해 실행했다 (프로젝트 파일 무수정).
`LLR_MATRIX_HD_1.txt` 기준, batch 16, `MinSumDecoder(schedule="column_wise", llr_matrix=mx)`.

### 5-1. dv별 에러 위치에 따른 성공률 (agent_4 §H-1 재현)

```
                              HD_1 (20 iter)        HD_0 (5 iter, restart 2)
  1 err in dv=4 only          성공 16/16 (n_iter 1)  성공 16/16 (n_iter 1)
  1 err in dv=3 only          성공 16/16 (n_iter 1)  성공 16/16 (n_iter 1)
  1 err in dv=2 only          성공  0/16             성공  0/16
  5 err in dv=2 only          성공  0/16             성공  0/16
  30 err anywhere             성공  0/16             성공  0/16
  300 err anywhere            성공  0/16             성공  0/16
```

**agent_4 §H-1의 실측은 재현된다.** dv=2 에러 하나로 프레임이 죽는 것을 분리 실험으로도 확정했다.

```
  300 err, 전부 non-dv2 column : 성공 8/8  (n_iter 6~10)
  같은 패턴 + dv2 column에 1개 : 성공 0/8
```

### 5-2. `ch(dv=2)` 스윕 (경계 14 확인)

`mx.row_ch[:, 3, 0]`(dv=2 그룹)만 바꾸고 나머지는 원본 유지. dv=2 column에 1비트 에러.

```
  ch=28 ( >14)  성공  0/16
  ch=16 ( >14)  성공  0/16
  ch=15 ( >14)  성공  0/16
  ch=14 (==14)  성공 12/16    <-- 경계에서 반전 발생
  ch=13 ( <14)  성공 12/16
  ch=10 ( <14)  성공 16/16    <-- 벤더 하드코딩 테이블 값
  ch= 7 ( <14)  성공 16/16
  ch= 1 ( <14)  성공 16/16 (n_iter 2)
  ch= 0 ( <14)  성공 16/16 (n_iter 2~16, 수렴 지연)
```

300비트 무작위 에러에서도 같은 경계가 보인다 (ch=15, 14, 13은 0/16, ch=10에서 1/16 회복).
300비트에서는 dv=2 이외 요인이 지배하므로 ch를 낮추는 것만으로 FER이 회복되지는 않는다.

### 5-3. 현행 `config.json` 실측

```
  fixed_error n=200: dv2 에러 포함 프레임 64/64, 성공 0/64, FER = 1.0000
  fixed_error n=300: dv2 에러 포함 프레임 64/64, 성공 0/64, FER = 1.0000
  이론값 P(dv2 무에러 | n=200) = 2.11e-11,  P(... | n=300) = 9.72e-17
```

---

## 판정

### 질문 A

**구현 결함이 아니다. C++ 원문도 같은 테이블을 넣으면 dv=2를 동일하게 영구 미정정으로 만든다.**

- ㉮ `sum_t = channel_llr = ch1 = LLR_MATRIX[row][col]`이며 스케일링, 시프트, 클리핑이 없다
  (`decoder.cpp:4017-4026`, `7089`, `local_opt.cpp:109`)
- ㉯ `sum_t += VNU_in`(`decoder.cpp:4041`)이고 `|VNU_in| <= EDGE_MAG_7 = 7`
  (`decoder.cpp:2402-2410`, `common.h:343`). 5-bit 채널값과 3-bit edge가 같은 int 가산기에
  섞이는 것은 **원문 그대로의 설계**다. Round 2가 남긴 "도메인 불일치" 갈래는 **반박됨**
- ㉰ `sum_t`에 포화가 없고 판정은 `sum_t > 0` 유지 = `sum_t <= 0` 반전이다 (`decoder.cpp:4044-4045`)
- ㉱ 로더에 범위 검사도 클램프도 없고 `max_value`/`min_value`는 로그 전용이다
  (`local_opt.cpp:52-132`, `164-167`). **C++도 무방비**
- ㉲ dv=2 특별 취급 없음 (`decoder.cpp:7078-7083`, `5704`)
- ㉳ 결정적 근거: 벤더 자신의 3-bit HD 채널 테이블은 63 row 전부 `{21, 14, 12, 10}`이고
  dv=2 열의 값은 **10**으로 상한 14를 지킨다 (`decoder.cpp:6777-6839`, `common.h:672-676`).
  `ch <= EDGE_MAG_7 * dv`는 원 설계의 암묵 불변식이며 토이 파일이 그것을 깼다

### 질문 B

**처방은 타당하다. 다만 두 가지 보강이 필요하다.**

- ㉮ 경계는 **`>`가 맞다**. `ch == 7*dv`이면 edge clear iteration에서 `total == 0`이 도달 가능하고
  `flip = total <= 0`이므로 반전이 일어난다 (실측: ch=15는 0/17, ch=14는 13/17 정정).
  `>=`는 오탐이다
- ㉯ restart row(ch=-1)는 오탐하지 않으므로 **전 row를 검사해도 안전하다** (실측 표 §3 ㉰)
- ㉰ 검사 자체는 **필요조건**으로서 엄밀히 옳다 (§3 ㉱ 정리). 통과했다고 정정이 보장되지는 않으므로
  경고 문구에 그 한계를 적어야 한다
- ㉱ **보강 1**: `dv_from != dv_to`인 일반 파일에서 미탐이 나지 않도록, 구간 대표값이 아니라
  `decoder.py:67`의 `self._col_dv`와 `code.col_deg`를 짝지어 **column 단위로** 검사할 것
- ㉲ **보강 2**: 두 파일의 오탐 0건, 미탐 0건 (§3 ㉰)

### 질문 C

**대체로 부합하나 네 곳을 고쳐야 한다.**

- ㉮ "전량"은 과하다. 실측 88.9~96.6%이고 나머지는 dv2 고착 에러의 2차 오염이다
- ㉯ "C++도 동일할 산술"에 조건이 빠졌다. "AUTO 빌드로 **같은 테이블 파일**을 읽을 때"라야 한다.
  저장소 `build.bat`은 그 프로파일을 만들지 않으며, 비AUTO 경로의 벤더 테이블은 dv=2에 ch=10이라
  반전이 가능하다
- ㉰ "구현 버그 아님"은 맞지만 "그래서 조치 불요"로 읽힐 여지가 있다. 현행 `config.json` 그대로
  FER ≡ 1.0(실측 0/64)이고, 원인을 알리는 장치가 없다는 사실을 함께 적어야 한다
- ㉱ "토이 매트릭스"라는 한정이 낙관적이다. `max_value`가 dv 구분 없이 31이라 최적화 탐색 공간
  자체가 영구 미정정 구간을 포함한다

### F2 최종 재분류 제안

**분류: 토이 데이터 + 검출 장치 부재 (구현 결함 아님).**
**심각도: HIGH 유지.**

근거는 다음과 같다.

- ㉮ Python 산술이 C++ 원문과 일치하므로 "구현 결함"은 **반박됨**
- ㉯ 그러나 저장소에 들어 있는 설정 그대로 실행하면 FER이 항상 1.0이고(실측 0/64), 사용자에게
  전달되는 신호는 "FER 1.0"뿐이다. 조용한 전멸이며 심각도를 낮출 이유가 없다
- ㉰ 조치는 두 갈래로 나뉜다.
  - ㉠ **코드 조치 (Round 2 처방 채택, 보강 2건 반영)**: 생성자에서 column 단위로
    `ch > edge_mag[0] * col_deg[j]`를 검사해 경고 또는 차단
  - ㉡ **데이터 조치**: 토이 LLR 파일의 dv=2 ch를 상한 이하로 내린다. 벤더 3-bit 테이블의
    `{21, 14, 12, 10}`을 참고값으로 삼을 수 있다 (dv=2에 10). 이 값은 실증에서 dv=2 단일 에러를
    16/16 정정했다
- ㉱ 별도 후속: `mode.h:8`과 `build.bat`이 AUTO 프로파일을 만들지 못한다는 사실은 F2와는 별건이나,
  "원본 C++ 대응이 정확성의 기준"이라는 이 프로젝트의 전제에 직접 걸리므로 별도 항목으로
  기록해 둘 가치가 있다
