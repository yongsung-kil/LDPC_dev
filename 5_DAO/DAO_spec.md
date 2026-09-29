# DAO LLR Matrix & Optimization Mode Specification

## 1. 개요

DAO는 ECC 디코더의 LLR(Log Likelihood Ratio) 매트릭스를 최적화하는 엔진이다. 본 문서는 LLR 매트릭스의 구조와 유효성 규칙, 그리고 다양한 최적화 모드의 스펙을 정의한다.

### 1.1 문서 목적

- 새로운 GenLLRMode 추가 시 준수해야 할 규칙 명시
- LLR 매트릭스 유효성 검증 기준 문서화
- 예외 케이스 및 에러 처리 가이드라인 제공

---

## 2. LLR Matrix 구조

### 2.1 전체 구조도

```
LLR_MATRIX
├── header: LLR_Header
├── groups: list[list[LLR_Row]]   # 그룹 리스트, 각 그룹은 Row 리스트
├── restart_groups: list[int]     # Restart 그룹 인덱스 (1-based)
└── FERs, raw_FERs, ...           # 테스트 결과 필드
```

### 2.2 LLR_Header 필드

| 필드                    | 타입           | 설명                                |
|------------------------|----------------|-------------------------------------|
| `num_parameter_each_set` | int          | DV당 파라미터 수 (CH + TH 길이)      |
| `num_dv`                 | int          | DV(Degree Variable) 개수            |
| `dv_from`                | np.ndarray   | DV 시작 인덱스 배열                  |
| `dv_to`                  | np.ndarray   | DV 종료 인덱스 배열                  |
| `num_group`              | int          | 그룹 총 개수                         |
| `num_row_each_group`     | np.ndarray   | 그룹별 행 개수                       |
| `type_each_group`        | np.ndarray   | 그룹별 유형 식별자                   |
| `num_restart`            | int          | Restart 지점 수                     |
| `restart_iter`           | np.ndarray   | Restart iteration 번호 배열         |
| `max_value`              | np.ndarray   | 파라미터별 최대 허용값               |
| `min_value`              | np.ndarray   | 파라미터별 최소 허용값               |

### 2.3 LLR_Row 필드

| 필드              | 타입           | 설명                                |
|------------------|----------------|-------------------------------------|
| `ch_th_values`   | np.ndarray     | DV별 CH/TH 값 배열 (길이: num_dv * num_parameter_each_set) |
| `CSW`            | int            | CSW 값 (-1 또는 8~1408, 8의 배수)   |
| `iter_start`     | int            | 적용 시작 iteration                 |
| `iter_end`       | int            | 적용 종료 iteration                 |
| `floor_flag`     | int            | SW 분기 index. -1은 분기 없음, 0 이상은 구간 안의 분기 번호 (3.7절) |
| `is_group_restart` | bool         | Restart 그룹 여부                   |

---

## 3. LLR Matrix 유효성 규칙

유효성 검증은 `Is_LLR_Valid()` 메서드에서 수행된다.
([DAO_LLR_MATRIX.py:266-449](DAO/SRC/DAO_LLR_MATRIX.py#L266-L449))

### 3.1 Header 검증

| 규칙 | 검증 내용 | 에러 메시지 |
|------|----------|-------------|
| H1 | `num_restart == len(restart_iter)` | "num_restart mismatch" |
| H2 | `num_group == len(num_row_each_group)` | "num_group mismatch with num_row_each_group length" |
| H3 | `num_group == len(type_each_group)` | "num_group mismatch with type_each_group length" |
| H4 | `len(max_value) == num_parameter_each_set` | "max_value length mismatch" |
| H5 | `len(min_value) == num_parameter_each_set` | "min_value length mismatch" |
| H6 | `num_group == len(groups)` | "num_group mismatch with groups" |
| H8 | `type_each_group[g]`가 10 미만이면 row 꼬리 == -1. 10 이상이면 일의 자리 == 그룹의 분기 index, 십의 자리 == 그 구간의 분기 수 | "Group {idx} header type {t} is a plain group but rows carry SW branch index {c}", "Group {idx} header type {t} says branch {b} but rows carry {c}" |

### 3.2 그룹/행 구조 검증

| 규칙 | 검증 내용 | 에러 메시지 |
|------|----------|-------------|
| G1 | 그룹이 비어있지 않음 | "Group {idx} is empty" |
| G2 | 그룹의 iter_start가 SW 분기 배치 규칙(3.7절)에 맞음. 분기가 없으면 이전 그룹 iter_end + 1 | "Group {idx} iter_start must be {expected} (SW branch {b}), got {start}" |
| G3 | 그룹 내 모든 row의 iter_start 동일 | "Group {idx} iteration_start mismatch" |
| G4 | 그룹 내 모든 row의 iter_end 동일 | "Group {idx} iteration_end mismatch" |
| G5 | iter_end >= iter_start | "Group {idx} iteration_end < iteration_start" |
| G6 | 총 행 수 == sum(num_row_each_group) | "Total row count mismatch" |
| G7 | 그룹의 행 수 == `num_row_each_group[g]` | "Group {idx} row count mismatch" |
| G9 | 그룹 안 모든 row의 `floor_flag`가 같음 | "Group {idx} rows carry different SW branch index (floor_flag)" |
| G10 | 한 구간의 모든 분기가 구간 시작과 끝을 똑같이 덮음 (3.7절) | "SW branch {b} ends at iteration {e} but its span ends at {s}" |

### 3.3 Restart 그룹 규칙

| 규칙 | 검증 내용 | 에러 메시지 |
|------|----------|-------------|
| R1 | Restart 그룹은 정확히 1개의 row만 가짐 | "Restart Group {idx} must have exactly 1 row" |
| R2 | Restart 그룹의 iter_start == iter_end | "Restart Group {idx} row must have iter_start == iter_end" |
| R3 | Restart row 길이 == `num_parameter_each_set * num_dv` | "Restart Group {idx} row length mismatch" |
| R4 | Restart row CSW == -1 | "Restart Group {idx} row CSW must be -1" |

### 3.4 Row 검증

| 규칙 | 검증 내용 | 에러 메시지 |
|------|----------|-------------|
| RW1 | `len(ch_th_values) == num_parameter_each_set * num_dv` | "Group {g} Row {r} length mismatch" |
| RW2 | `floor_flag`가 -1 또는 0 이상 MAX_SW_BRANCH(9) 이하 | "Group {g} Row {r} invalid SW branch index (floor_flag)" |
| RW3 | CH 값들 >= 0 | "CH values must be positive" |
| RW4 | TH 값들 >= 0 | "TH values must be positive" |
| RW5 | TH 값들 내림차순 (non-increasing) | "TH values must be non-increasing" |

### 3.5 CSW 규칙

| 규칙 | 검증 내용 | 에러 메시지 |
|------|----------|-------------|
| C1 | 그룹 첫 번째 row의 CSW == -1 | "Group {idx} first CSW must be -1" |
| C2 | 그룹 내 CSW == -1인 row는 정확히 1개 | "Group {idx} must have exactly one CSW == -1" |
| C3 | CSW 범위: MIN_CSW(8) <= CSW <= MAX_CSW(1408) | "CSW out of range" |
| C4 | CSW는 STEP_CSW(8)의 배수 | "CSW must be a multiple of 8" |
| C5 | CSW 값들 내림차순 (row 1부터) | "CSW values must be non-increasing" |

### 3.6 HBF 모드 특수 규칙

| 규칙 | 조건 | 검증 내용 |
|------|------|----------|
| HBF1 | `is_HBF_OPT == True`이고 row의 `iter_end <= HBF_MAX_ITERATION` | dv_idx 0의 TH 값은 모두 상수(`HBF_OPT_TH_CONSTANT_VAL`) |
| HBF2 | `is_HBF_OPT == True` | row는 HBF 구간 안에서 끝나거나 HBF 구간 뒤에서 시작 (`iter_start <= HBF_MAX_ITERATION < iter_end`이면 오류) |

- ㉮ HBF 구간은 iteration 1부터 `HBF_MAX_ITERATION`(4)까지다. 이 구간에서 디코더는 가장 높은 DV를 1 bit 정밀도로 처리해 그 TH를 읽지 않는다
- ㉯ dv_idx 0은 row의 맨 앞 CH와 TH다. row는 `CH(dv 0) TH(dv 0) CH(dv 1) TH(dv 1) ...` 순서로 적는다
- ㉰ HBF 구간의 row인지는 `Is_Row_In_HBF_Iterations()`가 끝 iteration으로 판단하고(`iter_end <= HBF_MAX_ITERATION`), 유효성 검사, 보정, 변이, 난수 생성이 모두 이 함수를 쓴다
- ㉱ HBF 구간 뒤의 row는 dv_idx 0의 TH도 다른 DV와 같은 규칙(RW4, RW5)을 따른다. 매트릭스의 max_iteration은 `HBF_MAX_ITERATION`보다 클 수 있다
- ㉲ HBF 구간 안은 여러 그룹으로 나눌 수 있다 (예: iteration 1, 2~3, 4). HBF2는 입력 매트릭스와 trial 매트릭스에 똑같이 걸리므로, 경계를 걸치는 row를 만든 trial은 유효하지 않은 매트릭스로 버려진다

---

### 3.7 SW 분기

SW(Syndrome Weight, 신드롬 무게) 분기는 한 iteration 구간을 여러 분기로 갈라 디코더가 프레임마다 하나를 고르게 하는 구조다. DAO는 분기를 만들거나 없애거나 옮기지 않고, 사용자가 입력 매트릭스로 정한 분기를 그대로 보존한다. 타겟은 분기 그룹도 그룹 하나씩 고르고, 변이는 타겟 그룹 하나에만 들어간다.

**표기** (파일 형식은 바뀌지 않는다)

- ㉮ 각 row의 마지막 칸 `floor_flag`가 분기 index다. -1은 분기 없음, 0 이상은 그 구간 안의 분기 번호
- ㉯ 헤더 `type_each_group`은 두 가지 뜻을 갖는다. 10 미만(0, 1)은 보통 그룹이고 row 꼬리는 -1이어야 한다. 10 이상은 `{분기 수}{분기 index}` 표시다: 10은 분기 1개(꼬리 0), 20과 21은 분기 2개(꼬리 0과 1). DAO는 읽은 값을 그대로 보존해 다시 쓰고, 헤더와 꼬리를 양방향으로 대조하며(H8), 헤더 표시 값이 바뀌는 자리를 구간 경계로 쓴다

**용어**

- ㉮ **구간(span)**: index 0으로 시작해 index가 0으로 되돌아가거나 -1이 나오기 전까지의 그룹들이 덮는 iteration 범위. index 0이 그대로 이어지는데 헤더 표시 값이 바뀌는 자리도 구간 경계다 (예: 헤더 10인 그룹 뒤에 헤더 20인 그룹). 구간 안에서 index가 1 늘면 iteration은 구간 시작으로 되돌아간다. 모든 분기는 구간의 시작과 끝을 똑같이 덮는다(G10). 구간 끝은 분기 0이 덮는 끝이다. 같은 표시의 구간 두 개가 iteration이 이어진 채 붙어 있으면 한 구간으로 읽는다

`Build_SW_Branch_Layout()`이 groups만 보고 그룹별 분기 index와 구간을 계산한다. `Is_LLR_Valid()`가 이 계산으로 G2와 G10을 검사한다.

**예** (`Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`. 같은 폴더의 `LLR_MATRIX_2.txt`는 iteration 1~4가 헤더 10인 분기 1개짜리 구간이다)

| 그룹 | 헤더 | 꼬리 | iteration | 뜻 |
|------|------|------|-----------|-----|
| 0, 1 | 20, 20 | 0, 0 | 1~1, 2~4 | 구간 1~4의 분기 0 |
| 2 | 21 | 1 | 1~4 | 구간 1~4의 분기 1 |
| 3 | 20 | 0 | 5~8 | 구간 5~8의 분기 0 |
| 4, 5 | 21, 21 | 1, 1 | 5~5, 6~8 | 구간 5~8의 분기 1 |
| 6~11 | 1 | -1 | 9~124 | 분기 없음 |

**최적화 규칙**

- ㉮ 타겟 목록(`target_group_indices`)의 값은 그룹 하나하나의 index다. 분기 그룹도 그룹마다 따로 타겟이 된다 (3.8절). 예의 그룹 4와 5는 같은 분기지만 타겟 4는 그룹 4만, 타겟 5는 그룹 5만 바꾼다
- ㉯ 타겟 그룹에 분기 그룹이 들어 있으면 MUTATE_MATRIX와 MUTATE_CSW만 허용한다(`SW_BRANCH_ALLOWED_MODES`). 다른 모드가 시퀀스에 있으면 `Set_Gen_Trial_LLR_Mode`가 오류로 멈춘다. 구조 변경 모드는 이웃 그룹의 iteration을 빌리거나 재배치해 구간 정렬을 깨뜨리기 때문이다. 타겟을 분기 구간 뒤의 보통 그룹으로만 두면 다른 모드도 쓸 수 있다. 다만 GEN_INITIAL_GROUP은 모든 그룹을 바꾸므로 분기 그룹이 있으면 언제나 막는다. 허용된 모드가 타겟 앞의 그룹(분기 구간)을 조금이라도 바꾸면 `Gen_Trial_LLR`이 그 trial을 버리고 로그에 남긴다
- ㉰ 타겟이 여러 분기로 갈라진 구간 안에 있으면 마지막 분기만 갱신한다. 다른 분기가 타겟이면 오류로 멈춘다
- ㉱ MUTATE_MATRIX는 타겟 그룹에서 `NUM_ELEMENTS_TO_MUTATE_CHTH`개까지 변이하고, `Correct_LLR_Matrix`가 row마다 정렬한다. MUTATE_CSW는 타겟 그룹에서 `NUM_ELEMENTS_TO_MUTATE_CSW`개까지 변이하고 그룹 안에서 정렬한다
- ㉲ HBF(Hybrid Bit Flipping)는 지금 HD 복호의 iteration 1~4를 뜻한다. HBF 최적화 모드(`IS_HBF_OPT`)와 SW 분기의 결합은 다루지 않는다

---

### 3.8 타겟 그룹 목록

`Build_Target_Group_Indices()`가 설정과 매트릭스에서 타겟 목록(`target_group_indices`)을 만든다. 시작할 때 초기 매트릭스로 한 번, stage마다 optimal 매트릭스로 한 번 만든다. 목록의 값은 그룹 하나하나의 index이고, 매트릭스 파일에 적힌 그룹 순서를 0부터 센다.

| 설정 | 타겟 목록 |
|------|----------|
| `FIXED_TARGET_GROUP_IDX_LIST`가 None | `INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지 (그 범위가 비면 마지막 그룹 하나) |
| `FIXED_TARGET_GROUP_IDX_LIST`가 목록 (예: `[0, 1]`) | 목록에 적은 그룹만, 적은 순서대로 |

- ㉮ 타겟은 모드 시퀀스 한 바퀴마다 목록의 다음 그룹으로 넘어간다. HBF 최적화 모드도 같은 규칙을 따른다 (시퀀스만 `Gen_LLR_Mode_HBF_SEQUENCE`를 쓴다)
- ㉯ `FIXED_TARGET_GROUP_IDX_LIST`의 index는 매트릭스의 그룹 번호에 묶여 있다. 그래서 그룹 수, 순서, iteration 구간을 그대로 두는 모드(`FIXED_TARGET_GROUP_ALLOWED_MODES`)만 함께 쓴다: MUTATE_MATRIX, MUTATE_CSW, SWAP_ROW, COPY_ROWS, COPY_GROUP, INSERT_RANDOM_ROW, INSERT_MUTATED_ROW, REGEN_DV, REGEN_ROW
- ㉰ `Validate_Config`가 시작할 때 `Check_Fixed_Target_Group_Idx_List()`로 검사한다

| 규칙 | 검증 내용 |
|------|----------|
| T1 | `FIXED_TARGET_GROUP_IDX_LIST`는 비어 있지 않은 목록 |
| T2 | 목록의 값은 정수이고 0 이상 초기 매트릭스의 그룹 수 미만 |
| T3 | 목록에 같은 값이 한 번씩만 나옴 |
| T4 | 지금 쓰는 모드 시퀀스의 모드가 모두 `FIXED_TARGET_GROUP_ALLOWED_MODES` 안에 있음 |

---

## 4. Optimization Mode (GenLLRMode)

### 4.1 모드 분류표

```python
class GenLLRMode(IntEnum):
    GEN_INITIAL_GROUP = 0      # 초기 그룹 생성
    MUTATE_MATRIX = 10         # CH/TH 값 변이
    MUTATE_CSW = 11            # CSW 값 변이
    SWAP_ROW = 21              # 그룹 내 Row swap
    REORDER_GROUP = 22         # 그룹 순서 재배열
    COPY_ROWS = 30             # Row 복사
    COPY_GROUP = 31            # 그룹 복사
    INSERT_RANDOM_GROUP = 40   # 랜덤 그룹 삽입
    INSERT_RANDOM_ROW = 41     # 랜덤 Row 삽입
    INSERT_MUTATED_GROUP = 42  # 기존 그룹 복사+변이 후 삽입
    INSERT_MUTATED_ROW = 43    # 기존 Row 복사+변이 후 삽입
    REGEN_DV = 50              # DV 재생성
    REGEN_ROW = 51             # Row 재생성
    SPLIT_GROUP = 60           # Group 분할 + Mutation
    ADJUST_ITERATION = 62      # Iteration 조정
    DELETE_ROW = 70            # Row/Group 삭제
    INSERT_RESTART_GROUP = 80  # Restart 그룹 삽입
```

### 4.2 모드별 카테고리

| 카테고리 | 모드 | 설명 |
|---------|------|------|
| **구조 변경** | INSERT_RANDOM_GROUP, INSERT_RANDOM_ROW, INSERT_MUTATED_GROUP, INSERT_MUTATED_ROW, INSERT_RESTART_GROUP | 새로운 그룹/행 추가 |
| **구조 축소** | DELETE_ROW | 기존 행/그룹 삭제 |
| **값 변이** | MUTATE_MATRIX, MUTATE_CSW | 기존 값 랜덤 변경 |
| **재생성** | GEN_INITIAL_GROUP, REGEN_DV, REGEN_ROW | 완전히 새로운 값 생성 |
| **재배열** | SWAP_ROW, REORDER_GROUP, COPY_ROWS, COPY_GROUP | 기존 구조 재배치 |
| **Iteration** | SPLIT_GROUP, ADJUST_ITERATION | Iteration 범위 조정 |

---

## 5. 모드별 상세 스펙

### 5.1 GEN_INITIAL_GROUP (0)

**목적**: 모든 기존 그룹을 제거하고 새로운 초기 그룹 1개 생성

**입력 파라미터** (GEN_INITIAL_GROUP_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)
- `NUM_ROWS`: 새 그룹의 행 수
- `ITERATION`: 새 그룹의 iteration 수

**변경 사항**:
- `groups` → 새 그룹 1개로 교체
- `restart_groups` → 빈 리스트로 초기화
- `header.num_group` → 1
- `header.restart_iter` → 빈 배열
- `iter_start` = 1, `iter_end` = ITERATION

**필수 조건**:
- NUM_ROWS > 0
- ITERATION > 0

---

### 5.2 MUTATE_MATRIX (10)

**목적**: 타겟 그룹의 CH/TH 값을 랜덤하게 변이

**입력 파라미터** (MUTATE_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용). MUTATE_MATRIX/MUTATE_CSW 공유
- `NUM_ELEMENTS_TO_MUTATE_CHTH`: 변이할 최대 요소 수
- `MUTATION_RANGE`: 변이 범위

**변경 사항**:
- 선택된 row의 `ch_th_values` 일부 값 변경
- 변경 후 `Correct_LLR_Matrix()`로 정렬 및 범위 보정

**필수 조건**:
- 변이 후 CH/TH 값이 max_value/min_value 범위 내
- TH 값 내림차순 유지

**특수 로직**:
- 이전 trial 성공 시 Fine/Coarse Tuning 모드 진입
- HBF 모드: HBF 구간의 row는 dv_idx 0의 TH를 변이 후보에서 뺌 (3.6절)

---

### 5.3 MUTATE_CSW (11)

**목적**: 타겟 그룹의 CSW 값을 랜덤하게 변이

**입력 파라미터** (MUTATE_CONFIG):
- `MAX_TRIAL`: (MUTATE_MATRIX와 공유 — Section 5.2 참조)
- `MUTATION_RANGE`: 변이 범위 (STEP_CSW 단위)

**변경 사항**:
- 선택된 row(idx >= 1)의 CSW 값 변경
- row 0의 CSW는 항상 -1 유지

**필수 조건**:
- CSW는 8의 배수
- MIN_CSW(8) <= CSW <= MAX_CSW(1408)
- 내림차순 유지: prev_row.CSW >= curr.CSW >= next_row.CSW

---

### 5.4 SWAP_ROW (21)

**목적**: 같은 그룹 내 두 row의 ch_th_values만 교환

**동작**:
- CSW, iteration은 고정
- ch_th_values만 swap

**제외 조건**:
- Restart 그룹 제외
- 그룹 내 row가 2개 미만이면 제외

**Trial 수**: 각 그룹별 C(m, 2)의 합 (m = 그룹 내 row 수)

---

### 5.5 REORDER_GROUP (22)

**목적**: Greedy 방식으로 그룹 순서 재배열 최적화

**동작 방식**:
1. 각 position에서 모든 후보 그룹 테스트
2. 각 후보에 대해 restart O/X 2가지 케이스 테스트
3. 최적 후보 선택 후 다음 position으로

**상태 변수** (ReorderState):
- `is_active`: 모드 활성화 여부
- `current_position`: 현재 최적화 중인 위치
- `fixed_order`: 확정된 그룹 순서
- `remaining_pool`: 미배치 후보 그룹
- `best_matrix`: 현재 최적 매트릭스

**제외 조건**:
- Restart 그룹은 재배열 대상에서 제외

---

### 5.6 COPY_ROWS (30)

**목적**: 다른 그룹의 row를 타겟 그룹에 복사

**동작**:
- 선택된 row의 ch_th_values를 타겟 row에 복사
- CSW, iteration은 유지

**입력 파라미터** (COPY_ROWS_CONFIG):
- `ENABLE_EXTERNAL_SINGLE_ROW`: 외부 Single Row 후보 활용 여부 (기본: False)
- `EXTERNAL_SINGLE_ROW_DIRS`: GEN_SINGLE_ROW 결과 폴더명 리스트 (예: `["20260330_143025"]`)
- `MAX_EXTERNAL_CANDIDATES`: 외부 후보 로드 상한 (기본: 100)

**외부 후보 활용**:
- `ENABLE_EXTERNAL_SINGLE_ROW=True`이고 `EXTERNAL_SINGLE_ROW_DIRS`가 비어있지 않으면,
  `Input/Ref_C/{ECC_DIR}/Single_Row_LLR_Matrix/{MODE}/{YYYYMMDD_HHMMSS}/` 디렉토리들에서 외부 후보를 로드
- 각 디렉토리 내 모든 `LLR_MATRIX_*.txt` 파일을 순회하여 row 수집
- 외부 파일의 고정 header 필드(`num_parameter_each_set`, `num_dv`, `dv_from`, `dv_to`, `max_value`, `min_value`)가 현재 매트릭스와 일치해야 함
- 외부 파일 내 restart 그룹의 row는 후보에서 제외
- 내부 후보(기존 매트릭스의 row) + 외부 후보를 병합하여 trial 수행
- 외부 후보의 `orig_group=-1`로 출처 구분
- GEN_SINGLE_ROW 완료 시 workspace 결과가 자동으로 위 경로에 저장됨

---

### 5.7 COPY_GROUP (31)

**목적**: 기존 그룹을 복사하여 새 그룹 생성

**입력 파라미터** (COPY_GROUP_CONFIG):
- 복사 대상 그룹 선택 로직

---

### 5.8 INSERT_RANDOM_GROUP (40)

**목적**: 타겟 그룹 뒤에 랜덤 값으로 새 그룹 삽입

**입력 파라미터** (INSERT_RANDOM_GROUP_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)
- `INSERT_GROUP_NUM_ROWS`: 새 그룹의 행 수
- `INSERT_GROUP_NUM_ITERATION`: 새 그룹의 iteration 수
- `ENABLE_INSERT_RESTART`: Restart 그룹 추가 여부 (True 시 trials 절반 이후부터 restart 추가)

**변경 사항**:
- 새 그룹 삽입
- 삽입 위치 이후 모든 그룹의 iteration 증가
- header.restart_iter 업데이트
- target_group_indices 업데이트

**필수 조건**:
- CSW 후보 수 >= num_rows - 1 (첫 row는 CSW = -1)

---

### 5.9 INSERT_RANDOM_ROW (41)

**목적**: 타겟 그룹에 랜덤 row 삽입

**입력 파라미터** (INSERT_RANDOM_ROW_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)

**변경 사항**:
- 지정된 위치에 새 row 삽입
- header.num_row_each_group 업데이트

**필수 조건**:
- CSW 규칙 만족 (내림차순, 범위, 8의 배수)
- row_idx == 0 삽입 시 기존 첫 row의 CSW 재할당

---

### 5.10 INSERT_MUTATED_GROUP (42)

**목적**: 기존 그룹을 복사 후 mutation을 적용하여 타겟 그룹 뒤에 삽입

**입력 파라미터** (INSERT_MUTATED_GROUP_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)
- `INSERT_GROUP_NUM_ITERATION`: 새 그룹의 iteration 수 (기본값, 동적 조정됨)
- `ENABLE_INSERT_RESTART`: Restart 그룹 추가 여부 (True 시 trials 절반 이후부터 restart 추가)
- `NUM_ELEMENTS_TO_MUTATE_CHTH`: 변이할 CH/TH 요소 수
- `MUTATION_RANGE`: 변이 범위 (-MUTATION_RANGE ~ +MUTATION_RANGE)
- `ALLOW_ZERO_MUTATION`: mutation 개수 0 허용 여부

**변경 사항**:
- 기존 그룹 중 하나를 랜덤 선택하여 복사
- 복사된 그룹에 mutation 적용 후 삽입
- 삽입 위치 이후 모든 그룹의 iteration 증가
- header.restart_iter 업데이트
- target_group_indices 업데이트

**필수 조건**:
- Non-restart 그룹이 최소 1개 존재해야 함

**Iteration 동적 계산**:
- 잔여 공간 충분: `INSERT_GROUP_NUM_ITERATION` 설정대로 사용
- 잔여 공간 부족: 남은 만큼만 사용
- 꽉 차있음 (remaining <= 0): 십시일반 방식 적용
  - `INITIAL_TARGET_GROUP_IDX`부터 마지막 그룹까지에서 iteration 빌려오기
  - 각 donor 그룹에서 균등하게 빌려와 새 그룹에 할당
  - donor 그룹은 최소 1 iteration 유지

**특수 로직**:
- is_update_at_last_trial = True (temp_optimal → optimal on last trial)

---

### 5.11 INSERT_MUTATED_ROW (43)

**목적**: 기존 row를 복사 후 mutation을 적용하여 타겟 그룹에 삽입

**입력 파라미터** (INSERT_MUTATED_ROW_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)
- `NUM_ELEMENTS_TO_MUTATE_CHTH`: 변이할 CH/TH 요소 수
- `MUTATION_RANGE`: 변이 범위 (-MUTATION_RANGE ~ +MUTATION_RANGE)
- `ALLOW_ZERO_MUTATION`: mutation 개수 0 허용 여부

**변경 사항**:
- 타겟 그룹 내 row 중 하나를 랜덤 선택하여 복사
- 복사된 row에 mutation 적용 후 삽입
- header.num_row_each_group 업데이트

**필수 조건**:
- `optimal_LLR_matrix.max_iteration < MAX_DECODING_ITERATION` 일 때만 동작
- CSW 규칙 만족 (내림차순, 범위, 8의 배수)
- row_idx == 0 삽입 시 기존 첫 row의 CSW 재할당

**특수 로직**:
- is_update_at_last_trial = True (temp_optimal → optimal on last trial)

---

### 5.12 REGEN_DV (50)

**목적**: 타겟 그룹의 특정 DV의 CH/TH 전체를 랜덤 재생성

**입력 파라미터** (REGEN_DV_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)

**동작**:
- 순차적으로 row와 DV 선택
- 선택된 DV의 모든 값을 랜덤 생성

---

### 5.13 REGEN_ROW (51)

**목적**: 타겟 그룹의 특정 row 전체를 랜덤 재생성

**입력 파라미터** (REGEN_ROW_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)

**동작**:
- 순차적으로 row 선택
- 선택된 row의 모든 ch_th_values를 랜덤 생성

---

### 5.14 SPLIT_GROUP (60)

**목적**: 기존 그룹의 iteration을 분할하여 front/back 두 그룹을 생성하고, back 그룹에 mutation 적용

**입력 파라미터** (SPLIT_GROUP_CONFIG):
- `MAX_TRIAL`: 최대 trial 수 (-1: DAO_CONFIG.MAX_OPTIMIZATION_TRIALS 사용, >0: 해당 값 사용)
- SPLIT_RATIO: Front 그룹 iteration 비율 (0.0~1.0, 기본값 0.5)
- NUM_ELEMENTS_TO_MUTATE_CHTH: 변이할 CH/TH 요소 수 (기본값 3)
- MUTATION_RANGE: 변이 범위 (기본값 5)
- ALLOW_ZERO_MUTATION: mutation 0개 허용 여부 (기본값 True)

**동작 방식**:
1. 타겟 그룹의 iteration을 SPLIT_RATIO에 따라 front/back으로 분할
2. Front 그룹: 원본 rows 복사 (ch_th_values 동일)
3. Back 그룹: 원본 rows 복사 후 ch_th_values에 mutation 적용
4. 총 iteration 변화 없음

**제외 조건**:
- Restart 그룹 제외 (SKIP_RESTART_GROUP)
- Iteration 2 미만인 그룹 (분할 불가)

**업데이트 방식**: is_update_at_last_trial = True

---

### 5.15 ADJUST_ITERATION (62)

**목적**: Iteration 재분배 방식으로 그룹 최적화

**동작 방식**:
- 그룹간 iteration을 조정하여 최적 분배 탐색

**제외 조건**:
- Restart 그룹 제외

---

### 5.16 DELETE_ROW (70)

**목적**: 타겟 그룹의 row를 하나씩 삭제하여 최적 구조 탐색

**동작 방식** (Multi-round greedy deletion):
1. optimal_LLR_matrix 기준으로 삭제 가능한 (group_idx, row_idx) 후보 리스트 생성
2. 각 Round: 모든 후보를 하나씩 삭제 후 테스트 → FER 기준 best 선택
3. Round 완료 시: 개선 있으면 삭제 확정 후 다음 Round, 없으면 종료
4. 종료 시 baseline을 final verification으로 반환

**삭제 후보 조건**:
- target_group_indices 범위 내의 모든 row (restart group 포함)
- 전체 matrix에 최소 1개 row는 남아야 함

**삭제 케이스**:
- **Case A** (그룹 내 row 2개 이상): row만 제거, 첫 row 삭제 시 새 첫 row의 CSW를 -1로 설정 (C1 규칙)
- **Case B** (그룹 내 row 1개): group 전체 삭제, iteration 재분배

**상태 변수** (DeleteRowState):
- `is_active`: 모드 활성화 여부
- `current_round`: 현재 Round (0-based)
- `deletable_rows`: 현재 Round의 삭제 후보 [(group_idx, row_idx), ...]
- `current_candidate_idx`: deletable_rows 내 현재 테스트 중인 인덱스
- `round_best_candidate_idx`: 현재 Round에서 best 후보 인덱스 (-1: 개선 없음)
- `round_best_matrix`: 현재 Round의 best 매트릭스
- `round_baseline_matrix`: 현재 Round의 기준 매트릭스

**Trial 수**: N*(N+1)/2 (최악 상한, N = 삭제 가능 row 수)

**업데이트 방식**: is_update_at_last_trial = True

---

### 5.17 INSERT_RESTART_GROUP (80)

**목적**: Greedy 방식으로 유효한 위치에 restart group을 삽입하여 FER 개선 탐색

**동작 방식** (Multi-round greedy insertion):
1. optimal_LLR_matrix 기준으로 유효한 삽입 위치 리스트 생성
2. 각 Round: 모든 유효 위치에 restart group 삽입 후 테스트 → best 선택
3. Round 완료 시: 개선 있으면 삽입 확정 후 다음 Round, 없으면 종료
4. 종료 시 baseline을 final verification으로 반환

**삽입 위치 조건**:
- insert_pos ∈ [1, N-1] (맨 처음/끝 제외)
- groups[insert_pos - 1]이 restart → 제외 (연속 restart 방지)
- groups[insert_pos]이 restart → 제외 (연속 restart 방지)
- target_group_indices 범위 내만 허용

**삽입되는 Restart Group**:
- 1개 row, 1 iteration
- iter_start == iter_end
- 삽입 후 전체 iteration 재빌드 (G2 연속성 보장)
- header 업데이트: num_group, num_row_each_group, type_each_group, restart_iter, num_restart

**상태 변수** (InsertRestartGroupState):
- `is_active`: 모드 활성화 여부
- `current_round`: 현재 Round (0-based)
- `insertable_positions`: 유효 삽입 위치 리스트
- `current_candidate_idx`: 현재 테스트 중인 인덱스
- `round_best_candidate_idx`: 현재 Round에서 best 후보 인덱스 (-1: 개선 없음)
- `round_best_matrix`: 현재 Round의 best 매트릭스
- `round_baseline_matrix`: 현재 Round의 기준 매트릭스

**제외 조건**:
- 그룹 수 2개 미만이면 삽입 불가

**Trial 수**: N*(N+1)/2 (최악 상한, N = 유효 삽입 위치 수)

**업데이트 방식**: is_update_at_last_trial = True

---

## 6. 예외 케이스 및 에러 처리

### 6.1 공통 예외 케이스

| 상황 | 처리 방식 |
|------|----------|
| input_matrix가 None | `MPI_Abort()` 호출 |
| 그룹이 비어있음 | 해당 모드 실패 (None 반환) |
| CSW 후보 부족 | 해당 모드 실패 (None 반환) |
| 파라미터 범위 초과 | 자동 보정 (`Correct_LLR_Matrix`) |

### 6.2 모드별 실패 조건

| 모드 | 실패 조건 | 반환값 |
|------|----------|--------|
| INSERT_RANDOM_ROW | CSW 삽입 불가능한 위치 | None |
| INSERT_RANDOM_GROUP | CSW 후보 < num_rows - 1 | None |
| INSERT_MUTATED_GROUP | Non-restart 그룹 없음 / max_iteration >= MAX_DECODING_ITERATION | None / Skip |
| INSERT_MUTATED_ROW | CSW 삽입 불가능 / max_iteration >= MAX_DECODING_ITERATION | None / Skip |
| SWAP_ROW | 유효한 row pair 없음 | None |
| REORDER_GROUP | 재배열 대상 그룹 없음 | None |
| DELETE_ROW | 삭제 가능한 row 없음 / 전체 row 1개 이하 | Skip |
| INSERT_RESTART_GROUP | 유효한 삽입 위치 없음 / 그룹 수 2개 미만 | Skip |

### 6.3 자동 보정 (Correct_LLR_Matrix)

생성된 매트릭스는 `Correct_LLR_Matrix()`를 통해 자동 보정됨:

1. **범위 Truncation**: max_value/min_value 범위로 제한
2. **CH 정렬**: 내림차순 정렬 (truncation 후 수행)
3. **TH 정렬**: 내림차순 정렬 (HBF 모드: HBF 구간의 row는 dv_idx 0의 TH를 `HBF_OPT_TH_CONSTANT_VAL`로 고정, 3.6절)
4. **CSW 정렬**: 내림차순 정렬 (row 1부터)

**제외 조건**:
- **Restart row**: Ch/Th 정렬 및 Truncation 대상에서 제외
  - Restart row는 iteration이 1로 고정된 특수 row
  - 값 변이 대상이 아니므로 보정 불필요

---

## 7. 새 모드 추가 체크리스트

새로운 GenLLRMode를 추가할 때 확인해야 할 사항:

### 7.1 필수 구현

- [ ] `GenLLRMode` enum에 새 모드 추가
- [ ] `Gen_Trial_LLR()`에 분기 추가
- [ ] `Gen_LLR_{ModeName}()` 함수 구현
- [ ] 해당 모드용 CONFIG 클래스 정의 (필요시)
- [ ] CONFIG 클래스에 `MAX_TRIAL: int = -1` 필드 추가 (config 직접 사용 모드인 경우)
- [ ] `Set_Gen_Trial_LLR_Mode()`의 `MODE_MAX_TRIAL_MAP`에 새 모드 등록 (config 직접 사용 모드인 경우)

### 7.2 유효성 보장

- [ ] 생성된 매트릭스가 `Is_LLR_Valid()` 통과
- [ ] `Correct_LLR_Matrix()` 호출로 자동 보정
- [ ] Header 필드 일관성 유지

### 7.3 동기화

- [ ] MPI bcast를 통한 매트릭스 동기화
- [ ] 상태 변수 동기화 (해당시)

### 7.4 로깅

- [ ] 변경 사항 로그 출력
- [ ] 실패 시 에러 메시지 출력

---

## 8. 참조

- [DAO_LLR_MATRIX.py](DAO/SRC/DAO_LLR_MATRIX.py): LLR_MATRIX 클래스 정의
- [DAO_Constants.py](DAO/SRC/DAO_Constants.py): GenLLRMode 및 상수 정의
- [DAO_Main.py](DAO/SRC/DAO_Main.py): 최적화 로직 구현
- [DAO_Config.py](DAO/SRC/DAO_Config.py): 각 모드별 설정 클래스
