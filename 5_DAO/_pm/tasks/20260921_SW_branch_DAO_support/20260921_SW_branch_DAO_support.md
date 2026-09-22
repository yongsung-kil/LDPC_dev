# SW 분기 LLR matrix의 DAO 지원 (현재 수준)

> 작성: 2026-09-21 18:39:15
> 등급: Decision (매트릭스 모델과 유효성 규칙, 모드 허용 범위가 바뀐다). 6절의 결정을 받아 2026-09-21 20:38에 구현했다. 단일 프로세스 검사 30건 통과, MPI 실행 검증은 사용자 환경에서 한다.
> 관련: C++ 디코더 쪽은 [20260902_SW_branch_LLR_matrix](../20260902_SW_branch_LLR_matrix/20260902_SW_branch_LLR_matrix.md)가 담당한다. 이 문서는 DAO 쪽만 다룬다.

## 1. 목적

DAO(Decoder Auto Optimizer)가 SW(Syndrome Weight, 신드롬 무게) 분기가 들어간 LLR matrix 파일을 읽고, 분기 그룹을 묶음 단위로 변이하며, 허용되지 않은 모드가 들어오면 오류로 멈추게 한다. 분기 구조를 DAO가 만들거나 없애는 일은 하지 않는다.

## 2. 배경과 요구

사용자가 정한 현재 수준의 요구는 다음과 같다.

- ㉮ HBF(Hybrid Bit Flipping)는 지금 HD(Hard Decision) 복호의 iteration 1~4를 뜻한다 (뒤에 바뀔 수 있음)
- ㉯ DAO는 `Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`를 지금 형식 그대로 읽을 수 있어야 한다
- ㉰ SW 분기는 사용자가 입력 LLR matrix로 정한다. DAO는 분기를 만들거나 없애거나 옮기지 않는다
- ㉱ 타겟이 SW 분기 그룹이면 그 그룹에는 MUTATE_MATRIX와 MUTATE_CSW만 허용한다. 다른 모드가 들어오면 오류로 멈춘다 (모드 순서는 사용자가 맞춰 넣는다)
- ㉲ 분기마다 갱신 환경(입력 매트릭스와 uncor seed)은 사용자가 따로 모아 돌린다. 한 구간이 여러 분기로 갈라져 있으면 DAO는 마지막 분기만 갱신한다
- ㉳ 분기 표시가 같은 연속 그룹은 통째로 변이한다. `LLR_MATRIX_2.txt`는 `LLR_MATRIX_1.txt`보다 iteration 1~4의 분기 수가 2에서 1로 줄었지만 행 꼬리 칸은 -1이 아니라 0이다. 이것은 iteration 1(그룹 0)과 2~4(그룹 1)를 한 묶음으로 변이하라는 뜻이다. MUTATE_MATRIX는 묶음 안 각 그룹에서 설정된 요소 수만큼 변이하고 행마다 따로 정렬한다. MUTATE_CSW도 그룹마다 변이한 뒤 그룹 안에서 정렬한다

### 2.1 파일에서 읽히는 것

두 파일을 푼 결과다. "꼬리"는 각 행의 마지막 칸(지금 이름 `floor_flag`)이다.

| 파일 | 그룹 | 헤더 값 | 꼬리 | 행 수 | iteration | 뜻 |
|------|------|--------|------|-------|-----------|-----|
| 1 | 0, 1 | 20, 20 | 0, 0 | 1, 7 | 1~1, 2~4 | 구간 1~4의 분기 0 (두 그룹이 한 묶음) |
| 1 | 2 | 21 | 1 | 6 | 1~4 | 구간 1~4의 분기 1 |
| 1 | 3 | 20 | 0 | 6 | 5~8 | 구간 5~8의 분기 0 |
| 1 | 4, 5 | 21, 21 | 1, 1 | 1, 5 | 5~5, 6~8 | 구간 5~8의 분기 1 (두 그룹이 한 묶음) |
| 1 | 6~11 | 1 | -1 | | 9~124 | 분기 없음 |
| 2 | 0, 1 | 10, 10 | 0, 0 | 1, 7 | 1~1, 2~4 | 분기 1개짜리 묶음 (헤더 10 = 분기 수 1, index 0) |
| 2 | 2 | 20 | 0 | 6 | 5~8 | 구간 5~8의 분기 0 |
| 2 | 3, 4 | 21, 21 | 1, 1 | 1, 5 | 5~5, 6~8 | 구간 5~8의 분기 1 (한 묶음) |
| 2 | 5~10 | 1 | -1 | | 9~124 | 분기 없음 |

여기서 세 가지가 정해진다.

- ㉮ **묶음(bundle)** 은 한 구간 안에서 꼬리 값이 같은 그룹들이다. 꼬리가 -1이면 그룹 하나가 묶음 하나다. 파일 2의 그룹 0, 1처럼 헤더 10이 이어지는 것이 가장 단순한 묶음이다
- ㉯ **구간(span)** 은 꼬리 0으로 시작해 꼬리가 0으로 되돌아가거나 -1이 나오기 전까지의 그룹들이 덮는 iteration 범위다. 꼬리 0이 그대로 이어지는데 헤더 표시 값이 바뀌는 자리(파일 2의 그룹 1은 헤더 10, 그룹 2는 헤더 20)도 구간 경계다. 꼬리와 iteration만으로는 이 경계를 알 수 없어 헤더가 필요하다. 구간 안에서 꼬리가 1 늘면 iteration이 구간 시작으로 되돌아간다. 모든 분기는 구간의 시작과 끝을 똑같이 덮는다
- ㉰ **헤더 `type_each_group`** 은 10 미만(0, 1)이면 보통 그룹(꼬리 -1), 10 이상이면 `{분기 수}{분기 index}` 표시다. 10은 분기 1개짜리 묶음, 20과 21은 분기 2개. DAO는 읽은 그대로 보존해 다시 쓰고, 헤더와 꼬리를 양방향으로 대조하며, 표시 값이 바뀌는 자리를 구간 경계로 쓴다. 표기가 뒤에 바뀌면(옆 작업 4장 ㉮의 분기 전용 줄) 배치 계산의 `header_marker` 한 곳만 따라간다

### 2.2 지금 코드가 막히는 자리

- ㉮ [DAO_LLR_MATRIX.py:344](../../../SRC/DAO_LLR_MATRIX.py#L344) 부근 RW2: 꼬리가 -1이 아니면 무효. 파일 1, 2의 분기 그룹이 전부 걸린다
- ㉯ [DAO_LLR_MATRIX.py:302](../../../SRC/DAO_LLR_MATRIX.py#L302) 부근 G2: 그룹 iter_start가 앞 그룹 iter_end + 1이어야 함. 분기 1이 구간 시작으로 되돌아가는 자리(파일 1의 그룹 2, 4)에서 걸린다
- ㉰ [DAO_LLR_MATRIX.py](../../../SRC/DAO_LLR_MATRIX.py) `max_iteration = groups[-1][-1].iter_end`: 마지막 그룹이 분기이면 전체 최대가 아닐 수 있다
- ㉱ [DAO_Main.py](../../../SRC/DAO_Main.py) `Generate_Random_Mutation`과 `Mutate_CSW`: 타겟 그룹 하나만 변이한다. 묶음 개념이 없다
- ㉲ `Initialize_Stage`의 타겟 목록: 그룹 하나가 타겟 하나다. 묶음 안의 두 그룹이 따로 타겟이 된다
- ㉳ 구조 변경 모드(INSERT, DELETE, SPLIT, REORDER, ADJUST 등)는 이웃 그룹의 iteration을 빌리거나 재배치한다. 분기 그룹이 섞인 매트릭스에서 돌면 구간 정렬이 깨진다

## 3. 설계

### 3.1 데이터 모델 (`DAO_LLR_MATRIX.py`)

- ㉮ `LLR_Row.floor_flag`가 분기 index다 (이름은 그대로 두고 뜻을 필드 주석과 스펙에 적는다). 값은 -1(분기 없음) 또는 0 이상 `MAX_SW_BRANCH` 이하. 상수 `SW_BRANCH_NONE = -1`, `MAX_SW_BRANCH = 9`, 허용 모드 집합 `SW_BRANCH_ALLOWED_MODES`를 `DAO_Constants.py`에 둔다
- ㉯ 파일 형식은 바꾸지 않는다. 읽기와 쓰기 자리는 그대로다. 헤더 `type_each_group`은 읽은 값을 그대로 보존한다
- ㉰ 그룹 배치 정보를 그룹 목록에서 계산하는 메서드 `Build_SW_Branch_Layout()`을 둔다. 결과는 세 가지다
  - ㉠ `group_branch_idx[g]`: 그룹 g의 분기 index (첫 행의 꼬리)
  - ㉡ `bundle_of_group[g]`: 그룹 g와 같은 묶음인 그룹 index 목록 (자기 포함, 파일 순서)
  - ㉢ `span_of_group[g]`: 그룹 g가 속한 구간의 (시작 iteration, 끝 iteration, 분기 수). 분기 없는 그룹은 None
  - 읽기 직후와 쓰는 자리마다 다시 계산한다 (계산이 싸므로 낡은 값을 들고 있지 않는다). 헤더는 구간 경계 판정에만 쓴다
- ㉱ `max_iteration`은 모든 그룹의 iter_end 최대값으로 정한다

### 3.2 유효성 규칙 (`Is_LLR_Valid`)

기존 규칙은 그대로 두고 다음을 바꾸거나 더한다. 꼬리가 전부 -1인 옛 매트릭스에서는 모든 규칙이 지금과 같은 뜻으로 줄어든다.

| 규칙 | 내용 |
|------|------|
| RW2 (수정) | `floor_flag`는 -1 또는 0 이상 `MAX_SW_BRANCH` 이하 |
| G9 (신설) | 그룹 안 모든 행의 `floor_flag`가 같다 |
| G2 (수정) | 그룹 g와 바로 앞 그룹 p의 관계로 iter_start를 정한다. ㉠ g가 -1이면 iter_start는 (p가 구간 안이면 그 구간 끝, 아니면 p.iter_end) + 1. ㉡ g와 p의 index가 같고 헤더 분기 표시도 같으면 iter_start = p.iter_end + 1 (같은 묶음 이어짐). ㉢ g.index = p.index + 1이면 iter_start = 구간 시작 (다음 분기). 그 밖의 증가는 무효. ㉣ g가 0이고 (p가 0이 아니거나 헤더 분기 표시가 p와 다르면) 새 구간이며 iter_start는 (p가 구간 안이면 그 구간 끝, 아니면 p.iter_end) + 1 |
| G10 (신설) | 한 구간의 모든 분기는 구간 시작과 끝을 똑같이 덮는다 (각 분기의 첫 그룹 iter_start = 구간 시작, 마지막 그룹 iter_end = 구간 끝). 구간 끝은 분기 0이 덮는 끝이다 |
| H8 (신설) | `type_each_group[g]`가 10 미만이면 꼬리는 -1. 10 이상이면 일의 자리는 `group_branch_idx[g]`, 십의 자리는 그 구간의 분기 수와 같아야 한다 |
| R3, R4 (기존 수정분 유지) | restart 행의 길이와 CSW 검사 |

파일 1과 2는 이 규칙으로 모두 유효하다 (2.1의 표로 손으로 대조했다. 구현 뒤 실행으로 다시 확인한다).

### 3.3 타겟 단위와 모드 허용 (`DAO_Main.py`)

- ㉮ `Initialize_Stage`의 `target_group_indices`는 묶음 대표(묶음의 첫 그룹 index)만 담는다. `INITIAL_TARGET_GROUP_IDX`가 묶음 중간을 가리키면 그 묶음의 첫 그룹으로 당긴다. 로그에 묶음 구성을 함께 적는다
- ㉯ `Set_Gen_Trial_LLR_Mode`가 `current_target_group_idx`를 정한 뒤 `current_target_bundle`(그룹 index 목록)을 만들고 `Bcast_Trial_LLR_Mode`로 함께 뿌린다
- ㉰ 모드 허용 검사 (root에서 판정 뒤 `MPI_Abort`, 문구에 그룹과 모드 이름을 적는다)
  - ㉠ 타겟 그룹(묶음 포함)에 분기 그룹이 들어 있고 모드가 `SW_BRANCH_ALLOWED_MODES`(MUTATE_MATRIX, MUTATE_CSW) 밖이면 오류. GEN_INITIAL_GROUP은 분기 그룹이 있으면 언제나 오류. 판정은 `Check_SW_Branch_Mode_Allowed`가 하고 단일 프로세스로 검사할 수 있다. 타겟이 분기 구간 뒤의 보통 그룹뿐이면 다른 모드도 허용하되, `_Protected_Groups_Changed`가 타겟 앞 그룹의 변화를 잡아 그 trial을 버린다
  - ㉡ 타겟 묶음이 여러 분기로 갈라진 구간 안에 있는데 그 구간의 마지막 분기가 아니면 오류 ("DAO는 마지막 분기만 갱신")
- ㉱ `Generate_Random_Mutation`: 타겟 묶음의 그룹마다 따로 요소 풀을 만들고 `min(NUM_ELEMENTS_TO_MUTATE_CHTH, 풀 크기)`개를 뽑아 합친다. 행 정렬은 지금처럼 `Correct_LLR_Matrix`가 행마다 한다
- ㉲ `Mutate_CSW`: 타겟 묶음의 그룹마다 따로 `min(NUM_ELEMENTS_TO_MUTATE_CSW, 풀 크기)`개를 변이한다. 그룹 안 정렬과 중복 제거는 지금처럼 `Correct_LLR_Matrix`가 그룹마다 한다
- ㉳ `HBF_immutable_col_range`와 `IS_HBF_OPT` 경로는 건드리지 않는다. HBF가 iteration 1~4라는 뜻은 문서에만 적는다

### 3.4 문서

- ㉮ `DAO_spec.md` 2.3 필드 표(`floor_flag`의 뜻), 3장 규칙 표(RW2, G2 수정, G7, G9, G10, H6, H8, R3, R4 추가), 새 절 "3.7 SW 분기와 묶음"에 2.1의 용어와 표를 옮긴다
- ㉯ `README.md` 3장에 "SW 분기 매트릭스에서 허용되는 모드" 한 절을 더한다

## 4. 수정 대상 파일

| 파일 | 바뀌는 곳 |
|------|----------|
| `SRC/DAO_Constants.py` | `SW_BRANCH_NONE`, `MAX_SW_BRANCH`, `SW_BRANCH_ALLOWED_MODES` |
| `SRC/DAO_LLR_MATRIX.py` | `LLR_Row.floor_flag` 주석, 배치 속성, `Build_SW_Branch_Layout`, `Is_LLR_Valid`의 RW2, G2, G9, G10, H8, `max_iteration`, 읽기 직후 배치 계산 |
| `SRC/DAO_Main.py` | `Initialize_Stage` 타겟 목록, `Check_SW_Branch_Mode_Allowed`, `Set_Gen_Trial_LLR_Mode` 묶음과 허용 검사, `Bcast_Trial_LLR_Mode`, `_Get_Target_Bundle_Groups`, `Generate_Random_Mutation`, `Mutate_CSW`, `Print_Mode_Target_Info`, 단일 row 매트릭스의 꼬리 기본값 |
| `DAO_spec.md`, `README.md` | 3.4절 |

## 5. 안전성 체크리스트

- ㉮ 옛 형식(꼬리 전부 -1) 매트릭스 `Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt`를 읽어 유효하고, 다시 쓰면 같은 내용이 나온다 (회귀)
- ㉯ 파일 1, 2를 읽어 유효하고, 다시 쓰면 같은 내용이 나온다 (헤더 20, 21, 1과 꼬리 보존)
- ㉰ 묶음 계산: 파일 1은 {0,1}, {2}, {3}, {4,5}, 6~11 각각. 파일 2는 {0,1}, {2}, {3,4}, 5~10 각각
- ㉱ 구간 계산: 파일 1은 (1, 4, 2분기), (5, 8, 2분기). 파일 2는 (1, 4, 1분기)와 (5, 8, 2분기)
- ㉲ 틀린 파일 거부: 분기 index가 0에서 2로 건너뜀, 분기 1이 구간 끝을 덮지 않음, 한 그룹 안에서 꼬리가 다름, 헤더 20인데 꼬리 1, 새 구간이 앞 구간 끝 + 1에서 시작하지 않음, 구간이 분기 1로 시작
- ㉳ MUTATE_MATRIX가 묶음 {0,1}을 타겟으로 할 때 두 그룹 모두에 변이가 들어가고 다른 그룹은 그대로다. MUTATE_CSW도 같다
- ㉴ 파일 1에서 타겟이 그룹 3(구간 5~8의 분기 0)이면 마지막 분기가 아니므로 오류. 타겟이 묶음 {4,5}이면 허용
- ㉵ 파일 1에 REORDER_GROUP을 넣으면 오류 문구를 내고 멈춘다
- ㉶ 이 검사는 단일 프로세스 `python` 실행으로 한다 (`MPI_Abort`는 예외로 바꿔 잡는다). 실제 MPI 실행은 사용자 환경에서 한다. 결과: 30건 통과 (2026-09-21 20:38)

## 6. 결정 (2026-09-21)

사용자가 정한 것: 1은 ㉮, 2는 ㉮, 3은 ㉮, 4는 ㉯(이름 `floor_flag` 유지), 5는 ㉮. 구현하며 드러난 추가 사항: 구간 경계에 헤더의 분기 표시 변화가 필요하다 (2.1 ㉯). 이어서 2026-09-22에 헤더 규약을 엄격하게 확정했다: 1은 보통 그룹(꼬리 -1), 10은 분기 1개짜리 묶음(꼬리 0), 20과 21은 분기 2개. 이에 맞춰 `LLR_MATRIX_2.txt`의 그룹 0, 1 헤더를 1에서 10으로 바꿨다. 같은 날 결정 1을 좁혔다: 타겟 그룹에 분기 그룹이 들어 있을 때만 MUTATE 두 모드로 제한하고, 타겟이 분기 구간 뒤의 보통 그룹뿐이면 다른 모드도 허용한다 (GEN_INITIAL_GROUP은 언제나 금지). 대신 `_Protected_Groups_Changed`가 타겟 앞 그룹을 바꾼 trial을 버린다. 아래는 결정 당시의 선택지다.


- 1. 구조 변경 모드를 막는 범위. ㉮ 매트릭스에 분기 그룹이 하나라도 있으면 MUTATE 두 모드 외 전부 오류 (추천. 구조 변경 모드는 이웃 그룹의 iteration을 빌리거나 재배치해 구간 정렬을 깨뜨린다) ㉯ 타겟이 분기 그룹일 때만 오류 (요구 ㉱의 문자 그대로)
- 2. 헤더 `type_each_group` 검사. ㉮ 10 이상이면 꼬리와 대조하고 0, 1이면 검사하지 않음 (추천) ㉯ 검사하지 않고 그대로 통과
- 3. 타겟 단위. ㉮ 묶음 하나가 타겟 하나 (추천) ㉯ 그룹 단위를 유지하되 묶음의 첫 그룹만 후보
- 4. 이름. ㉮ `floor_flag`를 `sw_branch_idx`로 바꿈 (추천. 옆 작업의 C++ 이름과 맞고, 뜻이 그대로 읽힌다) ㉯ 이름은 두고 뜻만 문서화
- 5. 구현 세션. ㉮ 이 세션 (추천. 리뷰와 오류 수정 맥락을 갖고 있고, 옆 세션은 C++ 쪽과 파일 형식 결정을 맡는다) ㉯ 옆 세션
