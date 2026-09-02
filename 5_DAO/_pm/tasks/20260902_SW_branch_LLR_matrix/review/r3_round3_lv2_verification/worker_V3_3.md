# Round 3 검증: 팀 V3 워커 3 (발견 R2-6)

> 작성: 2026-09-03 01:37:26
> 대상: Round 2 발견 R2-6 (파일 변환 절차 부재, 두 파서의 형태 불일치)
> 규칙: 코드와 문서를 읽기만 했다. 수정한 파일은 없다.

---

## 0. 요약 판정

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| H6-A 현 파일을 3.2 파서에 넣으면 밀린다 | **확인됨** | 새 반복문이 12토큰을 앞당겨 먹어 row가 정확히 12토큰씩 밀리고, 파일 끝을 12토큰 넘어 읽는다 |
| H6-A 부속 주장 "12토큰씩 어긋난다" | **확인됨** | 손 실행으로 상수 12토큰 어긋남 확정 |
| H6-A 부속 주장 "오류 셋이 섞여 나온다" | **부분 확인** | 3.4 대조 오류 75건과 6.2 `[Error] (1)` 8건이 나온다. 6.2의 `(2)`와 `(3)`은 한 번도 걸리지 않는다 |
| code_diff 6.2 ㉯ "지금 형태의 파일을 넣으면 여기서 걸린다" | **반박됨** | type 20, 21 그룹은 밀림 때문에 후보에서 영구히 빠져 `(3)` 오류가 도달 불가 코드가 된다 |
| H6-B DAO 파서가 형태(2)의 새 줄을 `num_restart`로 읽는다 | **확인됨** | `DAO_LLR_MATRIX.py:485`가 `type_each_group` 다음 줄을 그대로 `num_restart`로 읽는다. 예외 없이 조용히 밀린 뒤 H4에서 엉뚱한 이유로 거부된다 |
| H6-C `Is_LLR_Valid` RW2가 형태(1)을 거부한다 | **확인됨** | `DAO_LLR_MATRIX.py:344-346`, 그룹 0 row 0의 `floor_flag` 0에서 거부 |
| P6 처방 "9장 2단계 앞에 변환 단계를 넣고 변환 파일을 함께 둔다" | **처방 수정 필요** | C++ 쪽 문제는 해결되지만 ㉮ 6.2 ㉯ 다시 쓰기 문구가 사실과 어긋나고 ㉯ DAO 쓰기 경로(`Build_LLR_Matrix_Output_Lines`)가 매 trial마다 변환 전 형태를 다시 만들어 낸다 |

심각도 재판정: **HIGH 유지**. 다만 근거의 무게중심이 옮겨진다. R2-6이 짚은 "6.2 ㉯가 깨끗한 거부가 아니다"보다 더 강한 사실이 나왔다. 6.2 ㉯가 말하는 거부는 **아예 일어나지 않으며**, 그 대신 `MN_num`이 124에서 11로 무너져 최대 iteration이 124에서 7로 줄어든 채 조용히 완주한다. 문서가 "여기서 걸린다"라고 안심시키는 지점이 실제로는 통과 지점이다.

---

## 1. H6-A: 현 파일을 3.2 파서에 넣으면 밀린다

### 1.1 ㉮ 입력 파일의 줄별 토큰 (증거: 확인됨)

[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)
전체는 105줄, 공백을 제외한 토큰 1584개다. 구분자는 탭이고 빈 줄과 탭만 있는 줄이 섞여 있다.

| 줄 | 내용 (요약) | 토큰 수 | 그 줄의 원래 뜻 |
|----|------------|--------|----------------|
| 1 | `4` | 1 | `num_para_each_set` |
| 2 | (빈 줄) | 0 | 구분 |
| 3 | `4` | 1 | `num_dv` |
| 4 | (빈 줄) | 0 | 구분 |
| 5 | `11 4 3 2` | 4 | `dv_from` |
| 6 | `11 4 3 2` | 4 | `dv_to` |
| 7 | (빈 줄) | 0 | 구분 |
| 8 | `12` | 1 | `num_group` |
| 9 | (빈 줄) | 0 | 구분 |
| 10 | `1 7 6 6 1 5 5 7 6 10 10 13` | 12 | `num_set_each_group` (합 77 = `num_row`) |
| 11 | `20 20 21 20 21 21 1 1 1 1 1 1` | 12 | `type_each_group` (`{x}{y}` 표기가 들어간 줄) |
| 12 | (빈 줄) | 0 | 구분 |
| 13 | `0` | 1 | `restart_num` |
| 14 | (빈 줄) | 0 | 구분 |
| 15 | `31 31 31 31` | 4 | `max_value` |
| 16 | `0 0 0 0` | 4 | `min_value` |
| 17 | (빈 줄) | 0 | 구분 |
| 18 | `21 0 0 0 16 11 5 4 11 8 4 2 19 18 14 13 -1 1 1 0` | 20 | row 0 (그룹 0). 앞 16칸 LLR, 다음 `CSW_thr`, `iter_start`, `iter_end`, `floor_flag` |
| 19 | (빈 줄) | 0 | 그룹 구분 |
| 20~26 | 각 20토큰 | 20 × 7 | rows 1~7 (그룹 1) |
| 27 | (탭만) | 0 | 그룹 구분 |
| 28~33 | 각 20토큰 | 20 × 6 | rows 8~13 (그룹 2) |
| 34 | (탭만) | 0 | 그룹 구분 |
| 35~40 | 각 20토큰 | 20 × 6 | rows 14~19 (그룹 3) |
| 41 | (탭만) | 0 | 그룹 구분 |
| 42 | 20토큰 | 20 | row 20 (그룹 4) |
| 43 | (탭만) | 0 | 그룹 구분 |
| 44~48 | 각 20토큰 | 20 × 5 | rows 21~25 (그룹 5) |
| 49 | (탭만) | 0 | 그룹 구분 |
| 50~54 | 각 20토큰 | 20 × 5 | rows 26~30 (그룹 6) |
| 55 | (탭만) | 0 | 그룹 구분 |
| 56~62 | 각 20토큰 | 20 × 7 | rows 31~37 (그룹 7) |
| 63 | (탭만) | 0 | 그룹 구분 |
| 64~69 | 각 20토큰 | 20 × 6 | rows 38~43 (그룹 8) |
| 70 | (탭만) | 0 | 그룹 구분 |
| 71~80 | 각 20토큰 | 20 × 10 | rows 44~53 (그룹 9) |
| 81 | (탭만) | 0 | 그룹 구분 |
| 82~91 | 각 20토큰 | 20 × 10 | rows 54~63 (그룹 10) |
| 92 | (탭만) | 0 | 그룹 구분 |
| 93~105 | 각 20토큰 | 20 × 13 | rows 64~76 (그룹 11). 마지막 토큰은 `-1` |

검산: 헤더 토큰 1 + 1 + 4 + 4 + 1 + 12 + 12 + 1 + 0 + 4 + 4 = 44. 1584 - 44 = 1540 = 77 × 20. row는 정확히 77개이고 각 20토큰이다.

`num_row`는 상위 문서 2장 표의 row 수 합과 같은 77이다.

### 1.2 ㉯ 3.1과 3.2 수정 후 파서의 `fscanf` 호출 순서 (증거: 확인됨)

수정 전 정본은 [local_opt.cpp:61-115](../../../../../../0_LDPC_original/src/local_opt.cpp#L61-L115)다.
[code_diff.md](../../code_diff.md) 3.1은 배열 두 개를 새로 잡고, 3.2는 `type_each_group` 반복문 **바로 뒤에**
`num_group`개를 읽는 반복문을 새로 넣는다.

수정 후 호출 순서 (각 항목이 몇 개를 읽는가):

| # | 호출 위치 | 읽는 개수 | 담는 곳 |
|---|----------|---------|---------|
| 1 | `local_opt.cpp:61` | 1 | `num_para_each_set` |
| 2 | `local_opt.cpp:62` | 1 | `num_dv` |
| 3 | `local_opt.cpp:65-68` | `num_dv` = 4 | `dv_from[]` |
| 4 | `local_opt.cpp:69-72` | `num_dv` = 4 | `dv_to[]` |
| 5 | `local_opt.cpp:73` | 1 | `num_group` |
| 6 | `local_opt.cpp:76-80` | `num_group` = 12 | `num_set_each_group[]`, `num_row` 누적 |
| 7 | `local_opt.cpp:81-84` | `num_group` = 12 | `type_each_group[]` |
| 8 | **3.2 신규 반복문** | `num_group` = 12 | `sw_branch_idx_each_group[]` |
| 9 | `local_opt.cpp:85` | 1 | `restart_num` |
| 10 | `local_opt.cpp:87-90` | `restart_num` | `restart_iter[]` |
| 11 | `local_opt.cpp:93-96` | `num_para_each_set` = 4 | `max_value[]` |
| 12 | `local_opt.cpp:97-100` | `num_para_each_set` = 4 | `min_value[]` |
| 13 | `local_opt.cpp:106-115` | row마다 `num_col`(16) + 4 = 20, 총 77회 | `LLR_MATRIX[i][]`, `CSW_thr[i]`, `iter_start[i]`, `iter_end[i]`, `sw_branch_idx[i]` |

8번이 새로 끼어들어 12토큰을 먹는다. 이 12토큰이 밀림의 전부다.

### 1.3 ㉰ 토큰 단위 손 실행 (증거: 확인됨)

토큰 번호는 파일 앞에서부터 1-based 일련번호다. 빈 줄과 탭은 `fscanf("%d")`가 건너뛴다.

| 호출 | 가져가는 토큰 번호 | 파일 위치 | 가져간 값 | 원래 그 토큰의 뜻 |
|------|------------------|----------|----------|-----------------|
| `num_para_each_set` | 1 | 18행이 아닌 1행 1칸 | 4 | 같음 |
| `num_dv` | 2 | 3행 1칸 | 4 | 같음 |
| `dv_from[0..3]` | 3~6 | 5행 | 11 4 3 2 | 같음 |
| `dv_to[0..3]` | 7~10 | 6행 | 11 4 3 2 | 같음 |
| `num_group` | 11 | 8행 | 12 | 같음 |
| `num_set_each_group[0..11]` | 12~23 | 10행 | 1 7 6 6 1 5 5 7 6 10 10 13 | 같음 |
| `type_each_group[0..11]` | 24~35 | 11행 | 20 20 21 20 21 21 1 1 1 1 1 1 | 같음 |
| **`sw_branch_idx_each_group[0..11]` (신규)** | **36~47** | **13행 1칸, 15행 1~4칸, 16행 1~4칸, 18행 1~3칸** | **0, 31, 31, 31, 31, 0, 0, 0, 0, 21, 0, 0** | **`restart_num`, `max_value[0..3]`, `min_value[0..3]`, row 0의 LLR 1~3칸** |
| `restart_num` | 48 | 18행 4칸 | 0 | row 0의 LLR 4번째 칸 |
| `restart_iter[]` | (없음) | | | `restart_num`이 0이라 한 개도 안 읽는다 |
| `max_value[0..3]` | 49~52 | 18행 5~8칸 | 16 11 5 4 | row 0의 LLR 5~8칸 |
| `min_value[0..3]` | 53~56 | 18행 9~12칸 | 11 8 4 2 | row 0의 LLR 9~12칸 |
| row 0 (20토큰) | 57~76 | 18행 13칸 ~ 20행 12칸 | LLR = 19 18 14 13 **-1 1 1 0** 15 0 0 0 14 14 9 5, CSW=27, `iter_start`=16, `iter_end`=11, `sw_branch_idx`=4 | 파일 row 0의 뒤 8칸과 파일 row 1의 앞 12칸 |
| row 1 (20토큰) | 77~96 | 20행 13칸 ~ 21행 12칸 | CSW=6, `iter_start`=10, `iter_end`=3, `sw_branch_idx`=2 | 파일 row 1 뒤 8칸 + row 2 앞 12칸 |
| ... | ... | ... | ... | ... |
| row 76 (20토큰) | 1577~1596 | 105행 13칸 ~ **파일 끝을 넘어감** | 앞 8토큰만 실제 값, 나머지 12개는 읽기 실패 | |

**첫 밀림 지점**: 토큰 36. 신규 반복문의 첫 `fscanf`가 13행의 `restart_num`(값 0)을 가져간 순간부터
이후 모든 필드가 밀린다. R2-6의 "분기 줄이 restart 줄부터 읽힌다"는 표현은 정확하다.

**밀림 이후 무엇이 무엇으로 읽히는가**:

| 필드 | 원래 값 | 밀린 뒤 실제로 담기는 값 |
|------|--------|----------------------|
| `sw_branch_idx_each_group[]` | (파일에 없음) | `[0, 31, 31, 31, 31, 0, 0, 0, 0, 21, 0, 0]` |
| `restart_num` | 0 | 0 (우연히 같다. 18행 4칸이 0이기 때문) |
| `max_value[]` | 31 31 31 31 | 16 11 5 4 |
| `min_value[]` | 0 0 0 0 | 11 8 4 2 |
| row i (i = 0..76) | 파일 row i 그대로 | 파일 row i의 13~20칸 + 파일 row (i+1)의 1~12칸 |

`restart_num`이 밀린 뒤에도 0이라 `restart_iter` 읽기가 0회로 유지되는 것이 우연이다.
이 우연 때문에 밀림 폭이 12토큰으로 고정된다. 만약 18행 4칸이 0이 아니었다면
밀림 폭이 더 커지고 `new int[restart_num]` 크기도 달라졌을 것이다.

### 1.4 3.2의 구간 계산이 만들어 내는 값 (증거: 확인됨)

밀린 `sw_branch_idx_each_group`을 [code_diff.md](../../code_diff.md) 3.2의 구간 계산 블록에 넣으면
(`b == 0 && prev_branch != 0`일 때 구간 증가):

| 그룹 | `type_each_group` | 밀린 분기 index | 계산된 구간 번호 |
|------|------------------|---------------|----------------|
| 0 | 20 | 0 | 0 |
| 1 | 20 | 31 | 0 |
| 2 | 21 | 31 | 0 |
| 3 | 20 | 31 | 0 |
| 4 | 21 | 31 | 0 |
| 5 | 21 | 0 | 1 |
| 6 | 1 | 0 | 1 |
| 7 | 1 | 0 | 1 |
| 8 | 1 | 0 | 1 |
| 9 | 1 | 21 | 1 |
| 10 | 1 | 0 | 2 |
| 11 | 1 | 0 | 2 |

`num_sw_span` = 3. `MAX_SW_SPAN`이 4이므로 `cur_sw_branch_idx[span]` 색인은 범위 안이다.
code_diff 3.2가 적어 둔 기대표(그룹 0, 1이 분기 0 구간 0, 그룹 2가 분기 1 구간 0, …)와는 전혀 다르다.
기대표는 변환된 파일(상위 4장 ㉮ 형태)을 넣었을 때의 값이다.

### 1.5 ㉱ 6.2가 정의한 오류 조건 중 실제로 걸리는 것 (증거: 확인됨 / 6.2 ㉯는 반박됨)

[code_diff.md](../../code_diff.md) 6.2 수정 후 코드가 정의하는 오류는 셋이다.

- ㉮ `[Error] @Cur_LLR_IDX (1)`: 조건 `selected_group == -1 || selected_group >= m_param_LLR->num_group`.
     출력 후 `return 0`
- ㉯ `[Error] @Cur_LLR_IDX (3)`: 조건 "그룹 타입이 `GROUP_TYPE_ITER`도 `GROUP_TYPE_CSW`도 아님".
     출력만 하고 반환하지 않는다. 6.2 바뀐 점 ㉯가 "지금 형태의 파일(`20`, `21`)을 넣으면
     여기서 걸린다"라고 적은 곳이 이것이다
- ㉰ `[Error] @Cur_LLR_IDX (2)`: 조건 `table_row_idx < 0 || table_row_idx >= m_param_LLR->num_row`.
     출력 후 `return 0`

여기에 3.4가 새로 넣는 헤더와 row 대조 오류 `[Error] SW branch mismatch`가 더해진다.

**손 실행 결과**:

㉠ **3.4 대조 검사**: 77개 row 중 **75개가 불일치**해 `printf` 75줄이 나온다.
   우연히 통과하는 것은 그룹 5의 row 2와 그룹 7의 row 4, 두 개뿐이다(둘 다 밀린 값이 0이고
   그 그룹의 밀린 헤더 값도 0인 경우). `err = TRUE`가 서는데 R2-8이 밝힌 대로 흐름을 바꾸지 못한다.

㉡ **6.1 그룹 선택**: 밀린 `iter_start`, `iter_end` 때문에 그룹 12개 중 10개의 iteration 구간이
   **비어 있다**(`iter_start > iter_end`). 남은 두 그룹만 후보가 된다.

| 그룹 | 밀린 `iter_start[start_idx]` | 밀린 `iter_end[end_idx]` | 구간 성립 여부 |
|------|---------------------------|------------------------|--------------|
| 0 | 16 | 11 | 비어 있음 |
| 1 | 10 | 5 | 비어 있음 |
| 2 | 29 | 8 | 비어 있음 |
| 3 | 8 | 5 | 비어 있음 |
| 4 | 31 | 10 | 비어 있음 |
| 5 | 15 | 11 | 비어 있음 |
| 6 | 7 | 9 | **7~9** |
| 7 | 7 | 7 | **7~7** |
| 8 | 8 | 7 | 비어 있음 |
| 9 | 8 | 7 | 비어 있음 |
| 10 | 8 | 7 | 비어 있음 |
| 11 | 8 | -1 | 비어 있음 |

㉢ **6.2 오류 판정** (`cur_sw_branch_idx[]`는 5.1이 모두 0으로 초기화하고 4.1이
   `num_sw_branch`를 1 또는 2로 두므로 `Select_SW_Branch`가 돌려주는 값은 0 또는 1뿐이다):

| iter | 고르는 그룹 | 그 그룹의 type | 결과 |
|------|-----------|--------------|------|
| 1 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 2 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 3 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 4 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 5 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 6 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 7 | 7 | 1 (`GROUP_TYPE_CSW`) | 오류 없음. `table_row_idx` = 31 이상 |
| 8 | 6 | 1 (`GROUP_TYPE_CSW`) | 오류 없음. `table_row_idx` = 26 이상 |
| 9 | 6 | 1 (`GROUP_TYPE_CSW`) | 오류 없음 |
| 10 | 없음 | | `[Error] (1)` 출력, `return 0` |
| 11 | 없음 | | `[Error] (1)` 출력, `return 0` |

**판정**:

- `[Error] (1)`은 실제로 걸린다. 프레임마다 iteration 1~6과 10, 11에서 8회 출력된다
- `[Error] (2)`는 **한 번도 걸리지 않는다**. `(1)`을 통과하는 iteration 7, 8, 9는 모두
  `GROUP_TYPE_CSW` 갈래로 들어가 `table_row_idx = start_idx`가 먼저 대입되고,
  `start_idx`는 항상 `0 <= start_idx < num_row`다
- `[Error] (3)`은 **한 번도 걸리지 않는다**. type이 20 또는 21인 그룹은 0~5인데,
  그 가운데 밀린 분기 index가 0인 그룹 0과 5는 iteration 구간이 비어 있어 조건문을 통과하지 못하고,
  나머지 그룹 1~4는 밀린 분기 index가 31이라 `cur_sw_branch_idx[0]`(0 또는 1)과 결코 같지 않아
  `continue`로 걸러진다. 이 두 겹의 이유로 6.2 ㉯가 잡겠다는 상황이 도달 불가 코드가 된다

**결론**: code_diff 6.2 바뀐 점 ㉯의 "지금 형태의 파일(`20`, `21`)을 넣으면 여기서 걸린다"는
**반박됨**이다. 실제로는 `(3)`이 아니라 `(1)`이 걸리고, 그것도 절반 남짓한 iteration에서만 걸린다.

Round 2의 "오류 셋이 섞여 나온다"는 **부분 확인**이다. 나오는 것은 두 종류(3.4의 mismatch 75건과
6.2의 `(1)` 8건)이고, 6.2가 정의한 셋 가운데 둘은 죽어 있다.

### 1.6 밀림이 `MN_num`에 미치는 영향 (추가 발견, 증거: 확인됨)

R2-6이 언급하지 않은 더 큰 결과가 있다.

밀린 `iter_end[]`의 최댓값은 **11**이고, 마지막 row의 `iter_end`는 **-1**이다.

- [code_diff.md](../../code_diff.md) 3.5를 함께 적용하면 `max_iter_end` = 11이므로 `MN_num` = 11이 된다.
  [local_opt.cpp:118-131](../../../../../../0_LDPC_original/src/local_opt.cpp#L118-L131)을 거치면
  `MN[]` = `[4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7]`이 되고
  [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp#L1118)의
  `MN = m_param_dec->MN[MN_num - 1]`이 **7**이 된다.
  정상 파싱이었다면 `MN_num` = 124, `MN[MN_num-1]` = 120이다.
  즉 최대 iteration이 120에서 7로 무너진 채 시뮬레이션이 완주하고, FER 결과 파일의 열 수도
  124에서 11로 바뀐다
- 3.5를 적용하지 않고 3.2만 적용하면 `local_opt.cpp:116`이 `MN_num = iter_end[num_row-1]` = **-1**을
  주고 바로 다음 줄 `new int[-1]`이 `std::bad_array_new_length`로 던진다.
  9장 2단계는 3장 전체를 한 번에 넣으므로 이 상태는 지나가지만, 3.2와 3.5의 순서가 바뀌면 즉사한다

이 사실은 처방 문구에도 영향을 준다. R2-6이 제안한 대체 문구 "변환 전 파일은 파싱이 밀린 채
오류 셋이 섞여 나온다"는 여전히 부정확하다. 오류가 나오기는 하지만 **멈추지 않고 완주하며
결과 파일의 열 수와 최대 iteration이 통째로 달라진다**는 것이 더 위험한 사실이다.

### 1.7 ㉲ "12토큰씩 어긋난다"의 계산 확인 (증거: 확인됨)

밀린 토큰 수를 세면 이렇다.

- 원래 `restart_num` 자리부터 row 시작까지 소비하는 토큰: 1 (`restart_num`) + 0 (`restart_iter`)
  + 4 (`max_value`) + 4 (`min_value`) = 9
- 수정 후 같은 구간에서 소비하는 토큰: 12 (신규 반복문) + 9 = 21
- 차이 = **12**

row 0은 파일 row 0의 13번째 토큰에서 시작하고, row i는 `57 + 20i`번 토큰에서 시작한다.
파일 row i는 `45 + 20i`번 토큰에서 시작하므로 차이는 모든 i에서 상수 12다.
누적되지 않는 고정 어긋남이다. R2-6의 "row가 12토큰씩 어긋난다"는 **정확하다**.

한 row가 20토큰이고 어긋남이 12이므로, 각 row는 파일 row i의 뒤 8칸(LLR 13~16칸,
`CSW_thr`, `iter_start`, `iter_end`, `floor_flag`)과 파일 row (i+1)의 앞 12칸을 이어 붙인 값이 된다.
LLR 값 자리에 `-1`(CSW), iteration 번호, 분기 index가 섞여 들어간다.

### 1.8 ㉳ 파일 끝을 넘어 읽는가, 반환값을 검사하는가 (증거: 확인됨)

- **파일 끝을 넘어 읽는다**. 필요한 row 토큰은 77 × 20 = 1540개인데 시작점이 12토큰 밀려 있어
  1540 - 12 = 1528개만 남는다. 마지막 **12번의 `fscanf` 호출이 실패**한다.
  실패한 `fscanf`는 `c`에 대입하지 않으므로 `c`는 마지막으로 성공한 값(파일 마지막 토큰 `-1`)을
  유지한다. 결과적으로 row 76의 LLR 9~16칸과 `CSW_thr`, `iter_start`, `iter_end`, `sw_branch_idx`가
  모두 `-1`로 채워진다
- **반환값 검사는 어디에도 없다**. [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp)의
  `fscanf` 호출 14곳(61, 62, 66, 70, 77, 82, 88, 94, 98, 108, 111, 112, 113, 114행)이 모두
  반환값을 버린다. 3.1과 3.2의 수정 후 코드도 같은 형태로 반환값을 버린다
- 부수 확인: `fopen`의 NULL 검사도 늦다. `matrix_in = fopen(...)`이 60행인데
  NULL 검사는 139행이라, 모든 `fscanf`를 마친 뒤에야 확인한다.
  이것은 이 작업이 만든 결함이 아니라 기존 상태이며 code_diff가 손대지 않는다

---

## 2. H6-B: DAO 파서가 형태(2)를 잘못 읽는다

### 2.0 형태 번호의 확정

상위 문서 [4장](../../20260902_SW_branch_LLR_matrix.md)은 표기 안을 ㉮㉯㉰으로 번호 매긴다
(㉮ 분기 전용 줄 추가, ㉯ 세 자리 표기, ㉰ row 마지막 칸만). R2-6이 쓴 "형태(1)", "형태(2)"는
이 번호가 아니라 Round 2 팀 P가 따로 쓴 번호다. Round 2 근거 문서
[worker_P_3.md](../r2_round2_lv2_analysis/worker_P_3.md)의 서술과 대조하면 이렇게 확정된다.

- **형태 (1)** = 지금 저장소에 있는 `LLR_MATRIX_1.txt` 그대로. `type_each_group`에 `{x}{y}`(20, 21)가
  들어가 있고 row 마지막 칸이 0, 1, -1이다
- **형태 (2)** = 상위 4장 ㉮로 변환한 파일. `type_each_group`은 원래 뜻(전부 1)으로 되돌리고
  그 아래에 `sw_branch_idx_each_group` 줄(`0 0 1 0 1 1 -1 -1 -1 -1 -1 -1`)을 새로 넣은 것

### 2.1 ㉮ DAO 파서의 줄 index 방식 (증거: 확인됨)

[DAO_LLR_MATRIX.py:459-492](../../../../../SRC/DAO_LLR_MATRIX.py#L459-L492)를 그대로 인용한다.

```python
with open(self.input_LLR_matrix_file_path, "r", encoding="utf-8") as f:
    # 빈 줄과 공백을 제거해야 헤더 오프셋 계산 오류 없앰
    lines = [line.strip() for line in f if line.strip()]
```

세 성질이 확정된다.

- ㉠ **빈 줄을 건너뛴다**. `if line.strip()`이 빈 줄과 탭만 있는 줄을 목록에서 지운다
- ㉡ **순차 소비다**. 고정 index가 아니라 `idx_line`을 하나씩 늘려 가며 읽는다
  (`477`행 `idx_line = 0`부터 `492`행까지 각 필드마다 `idx_line += 1`)
- ㉢ **한 필드가 한 줄이다**. 토큰 수를 세지 않고 그 줄 전체를 배열로 만든다.
  스칼라 필드는 `[0]`으로 첫 원소만 취한다 (`477`, `478`, `481`, `485`행)

문제의 줄은 `485`행이다.

```python
type_each_group = get_line(idx_line, "type_each_group"); idx_line += 1

num_restart = int(get_line(idx_line, "num_restart")[0]); idx_line += 1
```

`type_each_group` 바로 다음 줄을 아무 조건 없이 `num_restart`로 읽고 첫 원소만 취한다.
R2-6의 주장 그대로다.

### 2.2 ㉯ 형태(2)를 넣었을 때 어느 필드가 어느 값을 받는가 (증거: 확인됨)

형태 (2)의 비어 있지 않은 줄을 0-based로 번호 매기면 이렇게 된다.

| 파일의 비어 있지 않은 줄 | 그 줄의 진짜 뜻 | DAO가 담는 곳 | DAO가 담는 값 |
|------------------------|---------------|-------------|-------------|
| 0 `4` | `num_para_each_set` | `num_parameter_each_set` | 4 (맞음) |
| 1 `4` | `num_dv` | `num_dv` | 4 (맞음) |
| 2 `11 4 3 2` | `dv_from` | `dv_from` | 맞음 |
| 3 `11 4 3 2` | `dv_to` | `dv_to` | 맞음 |
| 4 `12` | `num_group` | `num_group` | 12 (맞음) |
| 5 `1 7 6 ...` | `num_row_each_group` | `num_row_each_group` | 맞음 |
| 6 `1 1 1 ...` | `type_each_group` | `type_each_group` | 맞음 |
| 7 `0 0 1 0 1 1 -1 ...` | **`sw_branch_idx_each_group` (신규)** | **`num_restart`** | **`[0]` = 0** |
| 8 `0` | `restart_num` | `max_value` | `[0]` (길이 1) |
| 9 `31 31 31 31` | `max_value` | `min_value` | `[31,31,31,31]` |
| 10 `0 0 0 0` | `min_value` | **matrix row 0** | 길이 4 |
| 11 ~ 87 | 파일 row 0 ~ row 76 | matrix row 1 ~ row 76 | 마지막 파일 row가 잘려 나감 |

파생 결과:

- `num_restart` = 0이므로 `486`행의 `if num_restart > 0` 갈래를 타지 않아 `restart_iter`는 빈 배열이 된다.
  H1 검사(`num_restart == len(restart_iter)`, `276`행)는 0 == 0으로 **우연히 통과한다**
- `total_rows` = 77이고 남은 줄이 정확히 77개(줄 10~86)라 `511`행의 `len(matrix_rows) != total_rows`
  검사도 **통과한다**. 예외가 나지 않는다
- matrix row 0은 `min_value` 줄 `0 0 0 0`이다. `524-528`행의 `row[:-4]` 슬라이싱이
  **빈 배열**을 `ch_th_values`로 만들고, `CSW = 0`, `iter_start = 0`, `iter_end = 0`, `floor_flag = 0`이 된다
- **파일의 마지막 row 한 개가 통째로 버려진다**

### 2.3 ㉰ 예외인가 조용히 틀린 값인가 (증거: 확인됨)

**읽기 단계는 예외 없이 조용히 틀린 값을 만든다.** `Read_Input_LLR_Matrix`는 끝까지 정상 반환한다.

거부는 나중에 `Is_LLR_Valid`에서 일어나고, **원인을 가리키지 않는 메시지**로 나온다.
검사 순서대로 짚으면([DAO_LLR_MATRIX.py:276-290](../../../../../SRC/DAO_LLR_MATRIX.py#L276-L290)):

| 규칙 | 조건 | 형태 (2)에서 |
|------|------|------------|
| H1 | `num_restart == len(restart_iter)` | 0 == 0 통과 |
| H2 | `num_group == len(num_row_each_group)` | 12 == 12 통과 |
| H3 | `num_group == len(type_each_group)` | 12 == 12 통과 |
| H4 | `len(max_value) == num_parameter_each_set` | **1 != 4 거부** |

메시지는 `"max_value length mismatch"`다. 진짜 원인(헤더에 줄이 하나 늘어난 것)을 전혀 가리키지 않는다.
`Validate_LLR_Matrix`([DAO_Main.py:9906-9910](../../../../../SRC/DAO_Main.py#L9906-L9910))가 이 메시지를
로그에 적고, 초기 매트릭스라면 [DAO_Main.py:2341-2343](../../../../../SRC/DAO_Main.py#L2341-L2343)의
`MPI_Abort("Initial LLR matrix validation failed.")`로 실행이 끝난다.

**판정: 확인됨.** R2-6의 "형태(2)는 DAO 파서가 새 줄을 `num_restart`로 읽는다"가 사실이며,
그 결과가 예외가 아니라 조용한 오독과 엉뚱한 메시지의 거부라는 점을 덧붙인다.

---

## 3. H6-C: `Is_LLR_Valid` RW2가 형태(1)을 거부한다

### 3.1 ㉮ 344-345행의 조건과 RW2의 정체 (증거: 확인됨)

[DAO_LLR_MATRIX.py:343-346](../../../../../SRC/DAO_LLR_MATRIX.py#L343-L346) 원문이다.

```python
                # Floor flag
                if row.floor_flag != -1:
                    output_msg = f"Group {g_idx} Row {r} invalid floor_flag {row.floor_flag}"
                    return False, output_msg
```

**RW2**는 이 코드에 붙은 이름이 아니라 문서 쪽 규칙 번호다.
[DAO_spec.md:94](../../../../../DAO_spec.md) 3.4절 "Row 검증" 표의 두 번째 줄이며
`RW`는 Row 검증 규칙(Row Rule)의 약자로 RW1부터 RW5까지 있다.

| 규칙 | 검증 내용 | 에러 메시지 |
|------|----------|------------|
| RW1 | `len(ch_th_values) == num_parameter_each_set * num_dv` | "Group {g} Row {r} length mismatch" |
| **RW2** | **`floor_flag == -1`** | **"Group {g} Row {r} invalid floor_flag"** |
| RW3 | CH 값들 >= 0 | "CH values must be positive" |
| RW4 | TH 값들 >= 0 | "TH values must be positive" |
| RW5 | TH 값들 내림차순 | "TH values must be non-increasing" |

같은 문서 [DAO_spec.md:51](../../../../../DAO_spec.md)의 `LLR_Row` 필드표는 `floor_flag`를
"플로어 플래그 (현재 항상 -1)"로 설명한다. 즉 RW2는 이 칸이 아직 뜻을 갖지 않은
예약 칸이라는 전제를 못으로 박아 둔 규칙이다. R2-6이 말한 "`floor_flag == -1`을 강제한다"가 맞다.

### 3.2 ㉯ 이 검사가 불리는 경로 (증거: 확인됨)

`Is_LLR_Valid`를 부르는 곳은 두 군데다 (`5_DAO/SRC` 전수 grep, `reference/`는 참조 전용 사본이라 제외).

| 호출 위치 | 시점 | 실패하면 |
|----------|------|---------|
| [DAO_Main.py:9906](../../../../../SRC/DAO_Main.py#L9906) `Validate_LLR_Matrix` | 현재 매트릭스를 검증할 때 | `is_current_LLR_valid = False`, 메시지를 로그에 적고 매트릭스를 `session_error_dir`에 저장 |
| [DAO_Main.py:10220](../../../../../SRC/DAO_Main.py#L10220) `Build_Single_Row_Matrix` | 단일 row 후보를 만든 뒤 | 로그를 적고 `return None` (후보 폐기) |

`Validate_LLR_Matrix`는 초기화 경로에서 불린다.
[DAO_Main.py:2337-2343](../../../../../SRC/DAO_Main.py#L2337-L2343)이 순서대로
`Update_Current_LLR` → `Print_LLR_Matrix` → `Save_LLR_Matrix` 둘 → `Validate_LLR_Matrix`를 부르고,
실패하면 `MPI_Abort("Initial LLR matrix validation failed.")`로 전체 실행을 멈춘다.

### 3.3 ㉰ 형태 (1)과 형태 (2)의 통과 여부 (증거: 확인됨)

| 형태 | `Read_Input_LLR_Matrix` | `Is_LLR_Valid`에서 처음 걸리는 규칙 | 메시지 |
|------|------------------------|--------------------------------|-------|
| 형태 (1) (현 파일 그대로) | 정상 통과. 헤더 11줄, row 77개를 모두 제자리에 읽는다 | **RW2** (`344-346`행) | `Group 0 Row 0 invalid floor_flag 0` |
| 형태 (2) (4장 ㉮ 변환) | 정상 통과하나 값이 한 줄씩 밀린다 | **H4** (`285-287`행) | `max_value length mismatch` |

형태 (1)의 손 실행:

- 헤더 검사 H1~H5 모두 통과. `num_restart` 0 == `len(restart_iter)` 0,
  `num_group` 12 == `len(num_row_each_group)` 12 == `len(type_each_group)` 12,
  `len(max_value)` 4 == 4, `len(min_value)` 4 == 4
- 그룹 0 (row 1개, `iter_start` 1, `iter_end` 1). `previous_group_end`가 `None`이라 G2를 건너뛴다
- restart 그룹 판정: `restart_iter`가 비어 있어 `restart_groups`도 비어 있고
  `is_group_restart`도 `False`. 따라서 `322`행의 `continue`를 타지 않고 row 검사로 들어간다
- RW1: `len(ch_th_values)` 16 == 4 × 4 통과
- **RW2: `floor_flag` = 0, `-1`이 아니므로 거부**

RW2를 가정으로 통과시켜도 그 다음에 **G2**([DAO_LLR_MATRIX.py:305-312](../../../../../SRC/DAO_LLR_MATRIX.py#L305-L312))가
막는다. 상위 문서 2장 표의 iteration 구간(그룹 1이 2~4, 그룹 2가 1~4)에서 그룹 2의 시작 1이
직전 그룹 끝 4 + 1 = 5와 다르므로 `Group 2 iter_start must be exactly one greater than
previous group's iter_end: 1 vs 4`로 거부한다. 그룹 4(5~5, 직전 끝 8)도 같은 이유로 걸린다.
분기 구조 자체가 G2와 양립하지 않는다.

### 3.4 ㉱ 현 파일과 구 형태 파일의 대조 (증거: 확인됨)

| 파일 | DAO 파서 | DAO `Is_LLR_Valid` | 수정 전 C++ 파서 | 3.2 적용 후 C++ 파서 |
|------|---------|-------------------|-----------------|-------------------|
| [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) (형태 1) | 통과 (제자리에 읽음) | **RW2 거부** (`Group 0 Row 0 invalid floor_flag 0`) | 통과하나 type 20, 21이 어느 갈래에도 안 걸려 조용히 첫 row 사용 | **12토큰 밀림** |
| 형태 (2) (아직 저장소에 없음) | **한 줄 밀림** | **H4 거부** (`max_value length mismatch`) | 해당 없음 | 정상 (설계 의도) |
| [LLR_MATRIX_0.txt](../../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt) (구 형태) | 통과 | **통과** | 통과 | **3토큰 밀림** |

구 형태 파일의 손 실행 근거:

- 구조: `num_para_each_set` 4, `num_dv` 4, `dv_from`/`dv_to` 각 4, `num_group` 3,
  `num_set_each_group` `1 1 1`, `type_each_group` `1 1 1`, `restart_num` 1, `restart_iter` `2`,
  `max_value` `31 31 31 31`, `min_value` `0 0 0 0`, row 3개. row 마지막 칸이 셋 다 `-1`이다
- DAO: H1~H5 통과. 그룹 0 (1~1) RW2 `-1` 통과. 그룹 1은 `iter_start` 2가 `restart_iter`에 있어
  restart 그룹으로 잡히고 R1(row 1개), R2(`iter_start == iter_end`)를 통과해 `continue`.
  그룹 2 (3~5) 통과. G2도 1 → 2 → 3으로 이어져 통과. **전체 통과**
- 3.2 적용 후 C++: `type_each_group`(3토큰) 뒤의 신규 반복문이 `num_group` = 3개를 읽어
  `restart_num`(1), `restart_iter[0]`(2), `max_value[0]`(31)을 가져간다.
  `sw_branch_idx_each_group` = `[1, 2, 31]`이 된다. Round 2 발견 R2-10이 예로 든 `1 2 31`이
  바로 이 값이며 **재현 확인됨**. 이후 `restart_num`이 31이 되어 `new int[31]`을 잡고
  31개 토큰을 `restart_iter`로 읽어 밀림이 훨씬 커진다

즉 **3.2 수정은 구 형태 파일까지 깨뜨린다**. 변환 단계는 새 파일만의 문제가 아니라
저장소에 이미 있는 두 개의 `LLR_MATRIX_0.txt` 모두에 걸리는 문제다.

---

## 4. P6: 처방 검증

처방 원문: "9장 2단계 앞에 파일 변환 단계를 넣고 변환된 파일을 함께 둔다.
6.2 ㉯를 '변환 전 파일은 파싱이 밀린 채 오류 셋이 섞여 나온다'로 다시 쓴다".

### 4.1 ㉮ 두 파서가 동시에 받을 수 있는 헤더 배치가 있는가 (핵심 질문)

두 파서의 요구를 나란히 적는다.

| 항목 | C++ 파서 (토큰 기반) | DAO 파서 (줄 index 기반) |
|------|---------------------|------------------------|
| 근거 | [local_opt.cpp:61-115](../../../../../../0_LDPC_original/src/local_opt.cpp#L61-L115) + code_diff 3.2 | [DAO_LLR_MATRIX.py:459-537](../../../../../SRC/DAO_LLR_MATRIX.py#L459-L537) |
| 줄바꿈 | 무시한다 (`fscanf("%d")`가 공백류를 모두 건너뜀) | 필드 경계다 (한 필드 = 한 줄) |
| 빈 줄 | 무시한다 | 미리 제거한다 (`461`행) |
| `type_each_group` 다음에 오는 것 | 신규 분기 토큰 `num_group`개 | `num_restart` 한 줄 |
| 한 줄의 토큰 수 | 상관없다 | `num_group`(H2, H3)과 `num_parameter_each_set`(H4, H5)에 맞아야 한다 |
| row 이후의 잉여 줄 | 읽지 않는다 (`num_row`개만 읽음) | 무시한다 (`510`행 슬라이싱이 `total_rows`개만 취함) |
| row 마지막 칸의 값 | 제약 없음 | **`-1`이어야 한다** (RW2, `344-346`행) |
| 그룹 iteration 구간 | 제약 없음 | **직전 그룹 끝 + 1이어야 한다** (G2, `305-312`행) |

배치 후보를 하나씩 검사한다.

- ㉠ **분기 줄을 `type_each_group` 바로 아래 새 줄로 (상위 4장 ㉮)**:
  C++ 통과, DAO는 그 줄을 `num_restart`로 읽어 밀린다(2.2절). **불가**
- ㉡ **`type_each_group` 줄 뒤에 이어 붙여 24토큰 한 줄로**:
  C++ 통과, DAO는 H3(`num_group != len(type_each_group)`, 12 != 24)에서 거부. **불가**
- ㉢ **`num_set_each_group` 줄에 이어 붙이기**: 같은 이유로 H2가 거부. **불가**
- ㉣ **모든 row 뒤에 마지막 줄로 두기**: C++은 row 반복문 뒤에 새 반복문을 두면 읽을 수 있고,
  DAO는 `510`행이 `parsed[idx_line : idx_line + total_rows]`로 잘라 쓰므로 그 뒤의 줄을
  **그냥 무시한다**. **읽기만 놓고 보면 성립한다**
- ㉤ **헤더에 분기 줄을 두지 않고 row 마지막 칸만 쓰기 (상위 4장 ㉰)**:
  파일의 줄 배치가 구 형태와 완전히 같아진다. C++은 row를 다 읽은 뒤 그룹 첫 row의
  마지막 칸으로 그룹 분기 index를 세우면 되고, DAO 파서는 손댈 필요가 없다.
  **읽기만 놓고 보면 성립한다**

**판정: 교집합은 비어 있지 않다.** 배치 ㉣과 ㉤ 두 개가 두 파서의 **읽기**를 동시에 만족한다.
따라서 R2-6의 "DAO 파서는 두 형태 모두 통과 못 한다"는 검증 축이 제시한 두 형태에 한해서만
참이고, 배치를 바꾸면 벗어날 수 있다.

다만 **읽기가 성립해도 검증과 쓰기가 남는다**.

| 배치 | DAO 읽기 | DAO 검증 (RW2, G2) | DAO 쓰기 | 사람이 읽기 |
|------|---------|-------------------|---------|-----------|
| ㉣ row 뒤 마지막 줄 | 무시하고 통과 | RW2는 row 마지막 칸이 `-1`이면 통과, 분기 index를 row에 안 적으면 통과. G2는 분기 그룹의 iteration 되돌아감을 거부 → **수정 필요** | `Build_LLR_Matrix_Output_Lines`가 그 줄을 만들지 않아 **저장할 때마다 사라진다** → 수정 필요 | 헤더와 분기 정보가 파일 양 끝으로 갈라져 나쁨 |
| ㉤ row 마지막 칸만 | 그대로 통과 | **RW2가 거부** (0, 1을 못 받음) → 수정 필요. G2도 수정 필요 | `193`행이 `row.floor_flag`를 그대로 출력하므로 **보존된다** | 헤더만 보고 구조를 못 읽음 (상위 4장 ㉰가 이미 지적) |

배치 ㉤이 DAO 쪽 변경량이 가장 작다. 파서와 쓰기 함수를 건드리지 않고 검증 규칙 둘(RW2, G2)만
고치면 된다. 배치 ㉣은 쓰기 함수까지 고쳐야 한다.

**"DAO를 전혀 고치지 않고 되는 배치"는 없다.** RW2와 G2가 분기 구조 자체를 거부하기 때문에,
분기 index를 파일 어디에 두든 DAO는 분기가 붙은 매트릭스를 유효하다고 판정하지 않는다.

### 4.2 ㉯ DAO 파서 수정이 이 작업 범위 안인가 밖인가 (증거: 확인됨)

**문서상 범위 밖이다.**

상위 문서 1장([20260902_SW_branch_LLR_matrix.md:9](../../20260902_SW_branch_LLR_matrix.md))이
명시한다.

> DAO 쪽 대응(매트릭스 모델, 유효성 규칙, GenLLRMode)은 이 문서에서 다루지 않는다.

**작업 관리상으로는 등재되어 있다.** [5_DAO/_pm/TODO.md](../../../../TODO.md)의
"SW 분기가 있는 LLR matrix 지원" 아래 마지막 항목이 `[ ] DAO 매트릭스 모델과 유효성 규칙 확장`이다.

**판정: 처방이 불완전하다.** 처방은 C++ 문서 안에서 닫히는 조치만 담고 있어서,
"변환된 파일을 두면 C++ 쪽이 돈다"는 참이지만 그 파일이 DAO를 거쳐 돌아오면
다시 변환 전 형태가 된다는 사실(4.3절)을 문서 어디에도 남기지 않는다.
범위 밖이라도 **의존 관계는 적어야 한다**. 최소한 상위 7장 ㉮(표기 선택)에
"이 선택이 DAO의 읽기, 검증, 쓰기 중 무엇을 함께 바꾸는가"를 배치별로 붙여야
선택의 비용이 보인다.

### 4.3 ㉰ DAO가 LLR matrix 파일을 새로 쓰는가 (증거: 확인됨, 처방을 무너뜨리는 사실)

**쓴다. 그것도 최적화 과정 내내 반복해서 쓴다.**

쓰기의 유일한 출구는 `LLR_MATRIX.Save_Matrix`
([DAO_LLR_MATRIX.py:549-559](../../../../../SRC/DAO_LLR_MATRIX.py#L549-L559))이고,
그 내용은 `Build_LLR_Matrix_Output_Lines`
([DAO_LLR_MATRIX.py:92-202](../../../../../SRC/DAO_LLR_MATRIX.py#L92-L202))가 만든다.

전수 grep 히트 (`5_DAO/SRC`, `5_DAO/Util`. `reference/`는 참조 전용 사본이라 제외):

| 파일:줄 | 함수 | 무엇을 저장하는가 |
|---------|------|-----------------|
| [DAO_LLR_MATRIX.py:555](../../../../../SRC/DAO_LLR_MATRIX.py#L555) | `Save_Matrix` | 실제 `open(..., "w")` 지점 |
| [DAO_Main.py:8279](../../../../../SRC/DAO_Main.py#L8279) | `Save_LLR_Matrix` | 공통 진입점 |
| [DAO_Main.py:2013](../../../../../SRC/DAO_Main.py#L2013) | | 현재 매트릭스를 trial 출력 폴더에 |
| [DAO_Main.py:2338](../../../../../SRC/DAO_Main.py#L2338) | 초기화 | 초기 매트릭스를 trial 출력 폴더에 |
| [DAO_Main.py:2340](../../../../../SRC/DAO_Main.py#L2340) | 초기화 | 초기 매트릭스를 각 프로세스의 local session 폴더에 |
| [DAO_Main.py:8461](../../../../../SRC/DAO_Main.py#L8461) | | 매트릭스를 local session 폴더에 |
| [DAO_Main.py:9137](../../../../../SRC/DAO_Main.py#L9137) | | |
| [DAO_Main.py:9584, 9587, 9624](../../../../../SRC/DAO_Main.py#L9584) | | optimal 매트릭스를 optimal 출력 폴더에 |
| [DAO_Main.py:9909](../../../../../SRC/DAO_Main.py#L9909) | `Validate_LLR_Matrix` | 검증 실패 매트릭스를 error 폴더에 |
| [DAO_Main.py:10265](../../../../../SRC/DAO_Main.py#L10265) | `Rank_And_Save_*` | Top-K 후보 저장 |

`Build_LLR_Matrix_Output_Lines`가 만드는 줄 목록은
[DAO_LLR_MATRIX.py:122-145](../../../../../SRC/DAO_LLR_MATRIX.py#L122-L145)에 그대로 있다.

```python
lines = [
    str(h.num_parameter_each_set), "",
    str(h.num_dv), "",
    "\t".join(map(str, h.dv_from)),
    "\t".join(map(str, h.dv_to)), "",
    format_with_diff(h.num_group, ...), "",
    format_array_with_diff(h.num_row_each_group, ...),
    format_array_with_diff(h.type_each_group, ...), "",
    str(h.num_restart), "",
]
if h.num_restart > 0:
    lines.append("\t".join(map(str, h.restart_iter)))
    lines.append("")
lines.append("\t".join(map(str, h.max_value)))
lines.append("\t".join(map(str, h.min_value)))
lines.append("")
```

`type_each_group` 다음에 바로 `num_restart`가 온다. **분기 줄을 만들 자리가 없다.**
`LLR_Header`에 그 필드가 아예 없기 때문이다([DAO_spec.md:29-39](../../../../../DAO_spec.md) 2.2절 필드표에도 없다).

row 출력은 [DAO_LLR_MATRIX.py:195-201](../../../../../SRC/DAO_LLR_MATRIX.py#L195-L201)이
`matrix_part`, `CSW`, `iter_start`, `iter_end`, `floor_flag` 순으로 적으므로
**row 마지막 칸은 값 그대로 보존된다**.

**판정: 처방 불완전 확정.** DAO는 매 trial, 매 optimal 갱신마다 LLR matrix 파일을 새로 쓰고,
그 형태에는 분기 줄이 없다. 따라서 "변환된 파일을 한 번 저장소에 두면 끝"이 아니라
**"DAO의 쓰기 경로도 함께 고쳐야 한다"**가 된다. 배치 ㉤(row 마지막 칸만)을 고르면
이 항목만은 자동으로 해결된다(`floor_flag`가 그대로 실려 나가므로).
배치 ㉮나 ㉣을 고르면 `LLR_Header`에 필드를 추가하고
`Build_LLR_Matrix_Output_Lines`를 함께 고쳐야 한다.

### 4.4 ㉱ 변환 파일을 저장소에 두는 것이 루트 규칙에 걸리는가 (증거: 확인됨)

루트 [CLAUDE.md](../../../../../../CLAUDE.md)의 "문장 작성 규칙" ㉲가 관계된다.

> **입력 파일의 성격을 서술하지 않는다**: 특정 H-matrix나 LLR 파일이 어디서 왔고
> 어떤 성격인지 문서, 주석, 로그, 커밋 메시지 어디에도 적지 않는다. 파일은 이름과
> 치수로만 가리키고, 평가 대상을 말할 때는 "평가 대상 파라미터"라고 쓴다

**파일을 두는 것 자체는 걸리지 않는다.** 규칙이 금지하는 것은 성격과 출처의 서술이지 배치가 아니다.
저장소는 이미 같은 성격의 파일을 추적하고 있다. `git ls-files` 결과 두 개가 추적 중이다.

```
5_DAO/Input/Ref_C/Prime_ECC_2.3/Initial_LLR_matrix/LLR_MATRIX_0.txt
5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt
```

`Prime_ECC_3.0/` 아래는 아직 커밋되지 않았을 뿐 `.gitignore` 대상이 아니다
(`git check-ignore` 종료 코드 1). 전례와 어긋나지 않는다.

**주의할 점은 변환 절차 문서 쪽이다.** 변환 단계를 서술할 때 다음을 지켜야 규칙 안에 머문다.

- ㉠ 파일을 이름과 치수(그룹 12개, row 77개, 열 20칸)로만 가리킨다
- ㉡ 어느 칸을 어떤 칸으로 옮긴다는 **구조 변환**만 적고, 값이 무엇을 뜻하는지나
  이 파라미터가 어디서 왔는지는 적지 않는다
- ㉢ 파일 이름 규칙이 `LLR_MATRIX_%d.txt`로 고정되어 있으므로
  ([local_opt.cpp:59](../../../../../../0_LDPC_original/src/local_opt.cpp#L59)의 `sprintf`),
  변환 전후 두 파일을 같은 폴더에 둘 수 없다.
  폴더를 나누거나 index를 달리해야 하며 이 점이 처방에 빠져 있다

추가로 걸리는 점 하나: **변환 파일을 두면 같은 파라미터가 저장소에 두 벌 존재하게 된다.**
루트 [CLAUDE.md](../../../../../../CLAUDE.md) 공통 규칙 ㉱가 HTML에 대해 "파일은 한 벌만 만든다"를 두었고,
㉲가 `3_LDPC_ideas`에 대해 "md가 정본이므로 html을 직접 고치지 않는다"를 두었다.
같은 취지를 적용하면 변환 파일은 **정본이 어느 쪽인지와 변환이 재현 가능한지**를 함께 정해야 한다.
처방이 "함께 둔다"까지만 말하고 정본과 재현 방법을 정하지 않은 것은 미비다.

### 4.5 처방 문구 자체에 대한 판정

처방 후반 "6.2 ㉯를 '변환 전 파일은 파싱이 밀린 채 오류 셋이 섞여 나온다'로 다시 쓴다"는
**그대로 쓰면 안 된다**. 1.5절에서 확인한 대로 6.2가 정의한 오류 셋 중 둘은 걸리지 않고,
더 중요한 사실(멈추지 않고 완주하며 최대 iteration이 무너진다)이 빠진다.

대안 문구를 제시한다.

> 이 검사는 그룹 타입이 `GROUP_TYPE_ITER`도 `GROUP_TYPE_CSW`도 아닐 때를 잡는다.
> 3.2가 분기 줄을 읽으므로 파일에는 분기 줄이 있어야 하고, 없는 파일을 넣으면
> 헤더가 12토큰 밀려 읽혀 이 검사가 아니라 `(1)` 검사에 걸리며 최대 iteration도 함께 무너진다.

---

## 5. 최종 판정과 처방 제안

### 5.1 발견 R2-6의 판정

**확인됨 (부분 정정 포함).** 심각도 **HIGH 유지**.

정확한 부분:
- 변환 절차와 변환된 파일이 문서와 저장소 어디에도 없다
- 현 파일을 3.2 파서에 넣으면 분기 줄이 restart 줄부터 읽혀 밀린다
- row가 **정확히 12토큰씩** 어긋난다
- DAO 파서가 형태(2)의 새 줄을 `num_restart`로 읽는다
- `Is_LLR_Valid` RW2가 `floor_flag == -1`을 강제해 형태(1)을 거부한다

정정이 필요한 부분:
- "6.2 ㉯가 깨끗한 거부가 아니다"보다 강하다. **거부가 아예 일어나지 않는다**.
  `(3)` 검사는 도달 불가 코드가 되고 `(2)`도 걸리지 않는다
- "오류 셋이 섞여 나온다"는 두 종류(3.4 mismatch 75건, 6.2 `(1)` 8건)다
- Round 2가 보지 못한 결과가 있다. **`MN_num`이 124에서 11로 무너져 최대 iteration이 120에서 7이 된다.**
  3.5를 적용하지 않으면 `new int[-1]`로 즉사한다
- Round 2가 보지 못한 범위가 있다. **3.2 수정은 구 형태 파일까지 깨뜨린다.**
  저장소에 추적 중인 두 개의 `LLR_MATRIX_0.txt`도 3토큰 밀림으로 읽힌다
- "DAO 파서는 두 형태 모두 통과 못 한다"는 그 두 형태에 한해 참이다.
  row 뒤 마지막 줄(㉣) 또는 row 마지막 칸만(㉤) 배치는 DAO 파서를 그대로 두고 통과한다

### 5.2 처방 판정: 처방 수정 필요

원 처방("9장 2단계 앞에 변환 단계를 넣고 변환된 파일을 함께 둔다. 6.2 ㉯를 다시 쓴다")에
아래를 더해야 성립한다.

- ㉮ **6.2 ㉯의 대체 문구를 4.5절 안으로 바꾼다.** Round 2가 제안한 문구는 여전히 부정확하다
- ㉯ **변환 절차에 구 형태 파일의 처리를 넣는다.** 3.2는 새 파일뿐 아니라
  `Prime_ECC_2.3`과 `2.4`의 `LLR_MATRIX_0.txt`도 3토큰 밀림으로 읽는다.
  구 형태 파일에 분기 줄(전부 `-1`)을 넣는 절차가 함께 있어야 한다
- ㉰ **변환 파일의 자리와 정본을 정한다.** 파일 이름이 `LLR_MATRIX_%d.txt`로 고정이라
  같은 폴더에 두 벌을 둘 수 없다. 폴더를 나눌지 index를 달리할지, 어느 쪽이 정본인지,
  변환이 재현 가능한지(스크립트인지 수작업인지)를 적는다
- ㉱ **표기 선택(상위 7장 ㉮)에 DAO 파급을 배치별로 붙인다.** 4.1절 표를 그대로 쓸 수 있다.
  배치 ㉤(row 마지막 칸만)은 DAO 파서와 쓰기 함수를 그대로 두고 검증 규칙 둘만 고치면 되고,
  상위 4장 ㉮(분기 전용 줄)는 DAO의 파서, 헤더 모델, 쓰기 함수, 검증 규칙을 모두 고쳐야 한다.
  이 비용 차이가 지금 문서에 보이지 않는다
- ㉲ **9장에 "DAO 쓰기 경로 대응"을 후속 항목으로 남긴다.** 범위 밖이라도 의존 관계는 적는다.
  변환된 파일을 두어도 DAO가 매 trial마다 `Save_Matrix`로 변환 전 형태를 다시 만들어 내므로
  (4.3절), 변환 단계만으로는 한 번의 수동 실행 이상을 지탱하지 못한다

### 5.3 추가로 기록할 사실

- `local_opt.cpp`의 `fscanf` 14곳이 모두 반환값을 버린다. 3.1과 3.2의 수정 후 코드도 같다.
  파일 끝을 넘어 12번 읽고도 아무 신호가 없다. 파서에 형태 검사를 넣으려면
  반환값 확인이 가장 값싼 방어다
- `fopen`의 NULL 검사가 [local_opt.cpp:139](../../../../../../0_LDPC_original/src/local_opt.cpp#L139)에 있어
  모든 `fscanf` 뒤다. 기존 상태이며 code_diff가 손대지 않는다
- 밀림 폭이 12로 고정된 것은 우연이다. 파일 18행 4칸의 값이 0이라 `restart_num`이 0으로
  유지됐기 때문이다. 다른 파일에서는 밀림 폭이 달라지고 `new int[restart_num]` 크기도 달라진다
