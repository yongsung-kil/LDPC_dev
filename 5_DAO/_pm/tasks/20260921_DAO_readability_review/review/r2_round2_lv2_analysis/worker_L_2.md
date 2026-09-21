# Round 2 팀 L 워커 2: 구조 변경 모드와 인덱스 정합(P11), 타입 표기와 실제 값(P17), 실마리 ㉵

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> (`git log --oneline -1 -- 5_DAO/SRC` 결과)
> 줄 번호는 모두 이 커밋의 현재 파일 기준으로 다시 확인했다.

## 확인 범위

- `5_DAO/SRC/DAO_Main.py`: 그룹과 행을 넣고 빼고 나누고 재배열하는 생성 모드 13개 함수 전체 정독,
  `Initialize_Stage`, `Initialize_LLR_Matrix`, `Set_Gen_Trial_LLR_Mode`, `Update_Optimal_LLR`,
  `Gen_Trial_LLR`, `Run_Optimization` 트라이얼 루프, 멀티라운드 상태 초기화 함수 4개
- `5_DAO/SRC/DAO_LLR_MATRIX.py` 전체 (645줄)
- `5_DAO/SRC/DAO_Constants.py` 전체, `5_DAO/DAO_spec.md` 2절과 5절
- `target_group_indices`, `current_target_idx`, `current_target_group_idx`,
  `current_target_group_list_index`, `max_modification_trial`, `max_iteration`,
  `restart_groups`, `restart_iter`의 모든 등장 위치를 grep으로 뽑아 생성과 읽기 순서를 정리

---

## 1절. 모드별 헤더 필드 갱신 대조표

표기: `○` 갱신함, `–` 그 모드가 값을 바꾸지 않아 갱신이 필요 없음, `✗` 값이 바뀌는데 갱신하지 않음(결함), `n/a` 해당 없음.

| 모드 함수 | num_group | num_row_each_group | type_each_group | num_restart | restart_groups | restart_iter | target_group_indices | 비고 |
|---|---|---|---|---|---|---|---|---|
| [Gen_LLR_Insert_Random_Group](5_DAO/SRC/DAO_Main.py#L2585) | ○ 2711 | ○ 2712 | ○ 2713 (항상 1) | ○ 2721 | ○ 2725-2738 | ○ 2698-2700, 2718-2720 | ○ 2770-2785 | `max_iteration` 상한 확인 없음 (발견 L2-7). target 갱신이 trial마다 쌓임 (L2-3) |
| [Gen_LLR_Insert_Mutated_Group](5_DAO/SRC/DAO_Main.py#L2792) | ○ 3069 | ○ 3070 | ○ 3071 (항상 1) | ○ 3078 | ○ 3082-3094 | ○ 3059-3061, 3075-3077 | ○ 3120-3131 | 십시일반 경로에서 [_recalculate_group_iterations](5_DAO/SRC/DAO_Main.py#L3288)가 restart_iter를 다시 만든다. target 갱신이 trial마다 쌓임 (L2-3) |
| [Insert_Random_Row](5_DAO/SRC/DAO_Main.py#L2361) (INSERT_RANDOM_ROW 본체) | – | ○ 2471 | – | – | – | – | – | 행만 늘어나므로 그룹 단위 필드는 불변 |
| [Gen_LLR_Insert_Mutated_Row](5_DAO/SRC/DAO_Main.py#L3136) | – | ○ 3277 | – | – | – | – | – | 같음 |
| [Gen_LLR_Split_Group](5_DAO/SRC/DAO_Main.py#L3327) | ○ 3433 | ○ 3434 | ○ 3437-3440 (원본 type 승계) | – | ○ 3443-3449 | – | ○ 3454-3460 | 총 iteration 불변이라 restart_iter 값도 불변. target 갱신이 trial마다 쌓임 (L2-3) |
| [_Replace_With_Single_Group](5_DAO/SRC/DAO_Main.py#L3570) (GEN_INITIAL_GROUP, GEN_SINGLE_ROW) | ○ 3575 | ○ 3576 | ○ 3577 | ○ 3579 | ○ 3573 | ○ 3578 | ✗ 없음 | 그룹이 1개로 줄어드는데 `target_group_indices`를 건드리지 않아 다음 stage가 멈춘다 (L2-1) |
| [Copy_Group](5_DAO/SRC/DAO_Main.py#L8865) (COPY_GROUP 본체) | – | ○ 8918 | ○ 8919 | – | – | – | – | 타겟 그룹의 iteration을 유지하므로 iteration 계열 불변 |
| [Build_Reordered_Matrix](5_DAO/SRC/DAO_Main.py#L4849) (REORDER_GROUP) | ○ 5108 | ○ 5109 | ○ 5113-5132 | ○ 5146, 5149 | ○ 5154-5157 | ○ 5147, 5150 | – | `max_iteration`은 갱신하지 않고 `Is_LLR_Valid`가 다시 계산한다. iter_per_group 계산이 총 iteration을 줄인다 (L2-6) |
| [Build_Adjusted_Iteration_Matrix](5_DAO/SRC/DAO_Main.py#L4604) (ADJUST_ITERATION) | – | – | – | – | – | **✗** | – | restart 그룹의 iter_start가 옮겨가는데 restart_iter를 그대로 둔다 (L2-4) |
| [_Build_Deleted_Row_Matrix](5_DAO/SRC/DAO_Main.py#L5522) Case A (행만 삭제) | – | ○ 5542 | – | – | – | – | – | 그룹 구조 불변 |
| [_Delete_Entire_Group](5_DAO/SRC/DAO_Main.py#L5551) (DELETE_ROW Case B) | ○ 5618 | ○ 5619 | ○ 5620 | ○ 5640 | ○ 5623-5632 | ○ 5635-5639 | ✗ 없음 | 그룹 인덱스가 당겨지는데 다음 Round 후보를 옛 `target_group_indices`로 만든다 (L2-8). 5619가 dtype 미지정 (L2-13) |
| [_Build_Inserted_Restart_Matrix](5_DAO/SRC/DAO_Main.py#L5870) (INSERT_RESTART_GROUP) | ○ 5912 | ○ 5913 | ○ 5914 (항상 1) | ○ 5934 | ○ 5919-5925 | ○ 5928-5933 | ✗ 없음 | 삽입마다 총 iteration이 1 늘어나는데 상한 확인 없음 (L2-7). 5913이 dtype 미지정 (L2-13) |
| [_create_reorder_test_matrix](5_DAO/SRC/DAO_Main.py#L6195) | ○ 6325 | ○ 6323 | ○ 6324 (restart는 0) | ✗ | ○ 6320 | ✗ | – | 호출자가 없는 죽은 코드. 되살리면 base_matrix를 오염시킨다 (L2-11) |

### 1-1. 표에서 읽히는 규칙성

- ㉮ 그룹을 넣거나 빼는 모드는 헤더 6개 필드와 `restart_groups`를 손으로 각각 맞춘다. 같은 일을 하는
  코드 덩어리가 6벌 있고 (2711-2738, 3069-3094, 3433-3449, 5108-5157, 5618-5640, 5912-5934)
  그중 한 벌이라도 빠뜨리면 검증이 잡아내지 못한다. `restart_iter` 재빌드만 놓고 보아도
  "그룹의 `is_group_restart` 플래그에서 만든다"(3320-3325, 5140-5150)와
  "`restart_groups` 1 기준 목록에서 만든다"(5635-5639, 5928-5933) 두 갈래가 섞여 있다.
- ㉯ `max_iteration`은 여섯 모드가 각자 마지막에 다시 대입하고 (2741, 3097, 3452, 5643, 5937),
  REORDER와 ADJUST는 대입하지 않은 채 [Is_LLR_Valid](5_DAO/SRC/DAO_LLR_MATRIX.py#L441)의
  부수 대입에 기대고 있다. 필드 하나를 더할 때 이 두 갈래를 모두 찾아야 한다.
- ㉰ `type_each_group`에 넣는 restart 그룹의 값이 `1`(2713, 3071, 5115-5117, 5915)과
  `0`(6274, 죽은 코드) 두 가지로 갈린다.

---

## 2절. 타겟 그룹 인덱스 상태의 생성과 읽기 순서

### 2-1. 상태 네 개의 정체

| 속성 | 만들어지는 곳 | 뜻 | 읽는 곳 |
|---|---|---|---|
| `target_group_indices` | [Initialize_LLR_Matrix:2328](5_DAO/SRC/DAO_Main.py#L2328) 최초 생성, [Initialize_Stage:2265-2274](5_DAO/SRC/DAO_Main.py#L2265) stage마다 재설정, 생성 모드 3개가 trial마다 변경(2785, 3131, 3460), [Update_Optimal_LLR:9573-9583](5_DAO/SRC/DAO_Main.py#L9573) 채택 시 정리 | 최적화 대상 그룹의 0 기준 인덱스 목록 | Set_Gen_Trial_LLR_Mode(8316), Init_* 4개(4468, 4564, 5443, 5801), Build_Reordered_Matrix(4898, 4918), Build_Adjusted_Iteration_Matrix(4662), Get_Target_Group_Indices_Str(7198) |
| `current_target_idx` | [Initialize_Stage:2277-2294](5_DAO/SRC/DAO_Main.py#L2277)에서 `hasattr`로 만들고 stage마다 +1 | 아무 곳에서도 타겟 결정에 쓰이지 않는다 | [Init_Reorder_Group_Mode:4516](5_DAO/SRC/DAO_Main.py#L4516)의 로그 한 줄뿐 |
| `current_target_group_list_index` | `__init__`(607)에서 -1, [Set_Gen_Trial_LLR_Mode:8321](5_DAO/SRC/DAO_Main.py#L8321)에서 `sequence_cycle_count % len(target_group_list)` | `target_group_indices` 안의 위치 | Get_Target_Group_Indices_Str(7196), Bcast_Trial_LLR_Mode(828, 839) |
| `current_target_group_idx` | `__init__`(606)에서 -1, [Set_Gen_Trial_LLR_Mode:8322](5_DAO/SRC/DAO_Main.py#L8322), 그룹 수 초과 시 8325-8327에서 마지막 그룹으로 낮춤 | 실제 타겟 그룹의 0 기준 인덱스 | 생성 모드 12곳 (2604, 2812, 3153, 3345, 3669, 3912, 4062, 4196, 4412, 6343, 7037, 7107, 8822, 8878) |

### 2-2. 한 stage가 시작될 때의 실제 실행 순서

`Initialize_Stage(stage_idx)`가 하는 일을 줄 순서대로 적으면 이렇다.

- 1. 2249-2250: barrier와 동기 확인
- 2. 2251-2252: `current_stage_idx` 갱신, `temp_optimal_LLR_matrix = None`
- 3. **2262: `Set_Gen_Trial_LLR_Mode()`** 호출. 이 안에서 `target_group_indices`(**이전 stage에서 남은 값**)로
  `current_target_group_list_index`와 `current_target_group_idx`, `max_modification_trial`을 정하고 bcast한다
- 4. 2265-2274: `optimal_LLR_matrix` 기준으로 `target_group_indices`를 **다시 만든다**
- 5. 2276-2294: `current_target_idx`를 +1 하고 restart 그룹이면 건너뛴다
- 6. 2296: `self.target_group_indices[self.current_target_idx]`를 로그에 찍는다
- 7. 2299-2301: `MULTI_ROUND_INIT_FUNC`로 `Init_Reorder_Group_Mode` 등을 부른다. 이들은 **4번에서 새로
  만든 목록**을 쓴다
- 8. 2304-2308: stage 시간 제한 설정, 2310-2311: `Set_Update_Flags`, `Print_Stage_Info`

여기서 3번과 4번의 순서가 어긋나 있다. 3번이 쓰는 목록과 7번이 쓰는 목록이 서로 다르다.

### 2-3. 실마리 ㉵ (`current_target_idx` 생성 순서) 판정: AttributeError는 나지 않는다

`Init_Reorder_Group_Mode`를 부르는 곳은 `Initialize_Stage` 2299-2301 한 곳뿐이고
(`MULTI_ROUND_INIT_FUNC` 표를 거친 `getattr` 호출이라 grep으로는 이름이 직접 보이지 않는다),
그 호출은 `current_target_idx`를 만드는 2277-2280보다 **뒤**에 있다. 다른 진입 경로가 없으므로
[DAO_Main.py:4516](5_DAO/SRC/DAO_Main.py#L4516)에서 `AttributeError`가 나는 경로는 없다.

대신 같은 자리에 다른 문제가 있다. `Init_Reorder_Group_Mode`의 docstring 4464줄이
"REORDER_GROUP은 모든 target group을 재배열하므로 current_target_idx와 무관"이라고 적어 놓고
로그 4516줄은 그 값을 "Current target index"라는 이름으로 찍는다. 읽는 사람은 이 값이 재배열
시작 위치라고 오해한다. 더 넓게 보면 `current_target_idx`는 로그 한 줄 말고는 쓰이는 곳이 없다
(발견 L2-10).

---

## 3절. 발견

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|---|---|---|---|---|
| L2-1 | CRITICAL | `target_group_indices`가 빈 목록이 되면 최적화가 멈춘다. 빈 목록 검사는 [Set_Gen_Trial_LLR_Mode:8318-8320](5_DAO/SRC/DAO_Main.py#L8318)에만 있는데 이 함수는 목록을 다시 만들기 **전**에 돈다 | [DAO_Main.py:2280](5_DAO/SRC/DAO_Main.py#L2280) (`% len(...)`), [DAO_Main.py:2296](5_DAO/SRC/DAO_Main.py#L2296) (`[...]` 첨자) | optimal 매트릭스의 그룹 수가 `INITIAL_TARGET_GROUP_IDX`(기본값 1) 이하로 줄어드는 순간. GEN_INITIAL_GROUP이 stage 1에서 채택되어 [_Replace_With_Single_Group](5_DAO/SRC/DAO_Main.py#L3570)으로 1그룹이 되거나, DELETE_ROW가 [_Delete_Entire_Group](5_DAO/SRC/DAO_Main.py#L5551)로 그룹을 지워 1그룹이 되는 경우. 두 갈래로 갈린다. ㉮ 직전 trial에서 optimal이 갱신되었으면 9575-9583이 목록을 비우고 복원도 빈 목록이라 다음 stage의 8319에서 `MPI_Abort`로 멈춘다 (메시지가 원인을 가리키지 않는다). ㉯ 갱신이 없어 낡은 목록이 남아 있으면 8319를 통과한 뒤 2280에서 모든 rank가 `ZeroDivisionError`로 죽는다 | ㉮ 2265-2274 블록을 2262(`Set_Gen_Trial_LLR_Mode()` 호출) **앞**으로 옮긴다. ㉯ 옮긴 블록 끝에 빈 목록 보정을 넣는다: `if not self.target_group_indices: self.target_group_indices = [len(base_matrix.groups) - 1]` 와 같이 최소 한 개를 담아 놓고 그 사실을 로그로 남긴다. ㉰ [_Replace_With_Single_Group](5_DAO/SRC/DAO_Main.py#L3570)이 그룹 수를 줄이므로 이 함수 안에서도 `self.target_group_indices`를 새 그룹 수에 맞춰 다시 만든다 |
| L2-2 | HIGH | `Set_Gen_Trial_LLR_Mode`가 낡은 `target_group_indices`로 타겟 그룹과 trial 수를 정한다 | [DAO_Main.py:2262](5_DAO/SRC/DAO_Main.py#L2262) 호출과 [DAO_Main.py:2265-2274](5_DAO/SRC/DAO_Main.py#L2265) 재설정의 순서, 쓰는 쪽은 [8316-8327](5_DAO/SRC/DAO_Main.py#L8316), [8404-8412](5_DAO/SRC/DAO_Main.py#L8404), [8414-8422](5_DAO/SRC/DAO_Main.py#L8414) | 직전 stage가 INSERT_RANDOM_GROUP, INSERT_MUTATED_GROUP, SPLIT_GROUP 가운데 하나였고 (L2-3으로 목록이 부풀어 있음), 또는 직전 stage에서 그룹 수가 달라진 모든 경우. 8322가 실제 그룹 수를 넘는 인덱스를 집으면 8325-8327이 "마지막 그룹"으로 낮추므로, 여러 stage 동안 타겟이 마지막 그룹에 고정되고 앞쪽 그룹은 최적화 대상에서 빠진다 | 2265-2274 블록을 2262 앞으로 옮긴다 (L2-1과 같은 처방). 옮긴 뒤 8325-8327의 낮춤 코드는 남겨 두되 로그를 `WARNING`에서 `MPI_Abort`로 올려 다시 어긋나면 바로 드러나게 한다 |
| L2-3 | HIGH | 구조 변경 모드 3개가 `self.target_group_indices`를 trial마다 누적해서 바꾼다. 매트릭스는 trial마다 optimal에서 새로 복사되는데 (`Gen_Trial_LLR` [1953](5_DAO/SRC/DAO_Main.py#L1953)) 목록은 되돌아가지 않는다 | [Gen_LLR_Insert_Random_Group:2770-2785](5_DAO/SRC/DAO_Main.py#L2770), [Gen_LLR_Insert_Mutated_Group:3120-3131](5_DAO/SRC/DAO_Main.py#L3120), [Gen_LLR_Split_Group:3454-3460](5_DAO/SRC/DAO_Main.py#L3454), 전파는 [2019](5_DAO/SRC/DAO_Main.py#L2019) | 그룹 4개(0~3), `INITIAL_TARGET_GROUP_IDX=1`이라 목록은 `[1,2,3]`. SPLIT_GROUP stage에서 타겟이 g1이면 `insert_position=2`로 고정이다. trial 1: `[1,3,4,2]`, trial 2: `[1,4,5,3,2]`, trial 5: `[1,7,8,6,5,4,3,2]`. 매트릭스는 언제나 5그룹인데 목록은 인덱스 8까지 자란다 (직접 모의 실행으로 확인). MAX_TRIAL이 수십이면 목록 길이가 수십이 된다 | 세 함수의 갱신 코드를 통째로 들어내고, 갱신을 [Update_Optimal_LLR](5_DAO/SRC/DAO_Main.py#L9548)의 채택 경로 한 곳으로 모은다. 9573-9583이 이미 "그룹 수를 넘는 인덱스 제거"를 하고 있으므로 그 자리에서 `list(range(INITIAL_TARGET_GROUP_IDX, len(self.optimal_LLR_matrix.groups)))`로 통째로 다시 만들면 된다. 그러면 2019의 `Bcast_target_group_indices`도 필요가 없어진다 |
| L2-4 | HIGH | ADJUST_ITERATION이 iteration을 재배치하면서 `header.restart_iter`를 그대로 둔다. 저장되는 LLR matrix 파일의 restart 줄이 실제 restart 그룹 위치와 어긋난다 | [Build_Adjusted_Iteration_Matrix](5_DAO/SRC/DAO_Main.py#L4604), 재계산 루프 [4701-4727](5_DAO/SRC/DAO_Main.py#L4701). 이 함수는 `header`를 한 번도 건드리지 않는다 | restart 그룹이 하나 이상 있는 매트릭스로 ADJUST_ITERATION stage를 돌리면 항상. 함수 자신의 docstring 예시(4631-4636)가 restart 그룹 g2가 `[201-201]`에서 `[211-211]`로 옮겨가는 경우를 적어 놓았는데, `restart_iter`는 201로 남는다. [Is_LLR_Valid](5_DAO/SRC/DAO_LLR_MATRIX.py#L266)는 `num_restart == len(restart_iter)`(H1)만 보고 값이 맞는지는 보지 않으므로 검증을 통과한다 | 4727 루프 바로 뒤에 restart_iter 재빌드를 넣는다. [_recalculate_group_iterations:3320-3325](5_DAO/SRC/DAO_Main.py#L3320)의 6줄과 같은 내용이므로, 그 부분을 `_Rebuild_Restart_Header_From_Groups(matrix)` 같은 이름의 메서드로 뽑아 `Build_Adjusted_Iteration_Matrix`, `_recalculate_group_iterations`, `_Delete_Entire_Group`, `_Build_Inserted_Restart_Matrix`, `Build_Reordered_Matrix`가 모두 그것을 부르게 하면 1절 ㉮에서 적은 두 갈래도 한 갈래가 된다. 덧붙여 `Is_LLR_Valid`에 "restart 그룹의 iter_start 모음 == restart_iter" 규칙을 추가해 같은 실수를 검증이 잡게 한다 |
| L2-5 | HIGH | REORDER_GROUP의 `max_modification_trial`이 필요한 trial 수보다 정확히 1 작다. 마지막 Round의 `Finalize_Reorder_Round`와 Final Verification이 실행되지 않는다 | [Set_Gen_Trial_LLR_Mode:8409-8412](5_DAO/SRC/DAO_Main.py#L8409)는 `trials_per_round + 1`(HD) / `trials_per_round * 2 + 1`(SD), [Init_Reorder_Group_Mode:4503-4509](5_DAO/SRC/DAO_Main.py#L4503)는 `1 + trials_per_round + 1` / `1 + trials_per_round * 2 + 1` | REORDER_GROUP stage를 돌리면 항상. donor가 n개일 때 trial 1은 초기 테스트([5188-5202](5_DAO/SRC/DAO_Main.py#L5188)), trial 2부터 n(n+1)/2개가 Round 테스트, 그 다음 trial이 Final Verification인데 루프([8024](5_DAO/SRC/DAO_Main.py#L8024))가 n(n+1)/2+1에서 끝난다. `Finalize_Reorder_Round`는 다음 trial 진입 때 불리므로 마지막 Round의 best가 `fixed_order`에 들어가지 않고, `reorder_state.is_active`도 True로 남는다. n=3이면 7회 도는데 8회가 필요하다 (직접 계산으로 확인) | `Init_Reorder_Group_Mode` 끝(4509 다음)에 `self.max_modification_trial = total_trials`를 넣어 [Init_Delete_Row_Mode:5427](5_DAO/SRC/DAO_Main.py#L5427), [Init_Insert_Restart_Group_Mode:5781](5_DAO/SRC/DAO_Main.py#L5781)과 같은 방식으로 맞춘다. 그러면 8404-8412의 REORDER 분기는 지워도 되고 (`self.max_modification_trial = 1` 임시값 + 주석으로 DELETE_ROW와 같게), 계산식이 한 곳에만 남는다. 같은 이유로 8414-8422의 ADJUST_ITERATION 분기도 L2-9와 함께 옮긴다 |
| L2-6 | HIGH | REORDER_GROUP의 iteration 등분이 restart 그룹까지 센 개수로 나눠 총 iteration이 줄어든다 | [Build_Reordered_Matrix](5_DAO/SRC/DAO_Main.py#L4849), `num_original_target_groups = len(self.target_group_indices)` [4918](5_DAO/SRC/DAO_Main.py#L4918), `iter_per_group = total_iterations // num_original_target_groups` [5015](5_DAO/SRC/DAO_Main.py#L5015) | target 범위 안에 restart 그룹이 있는 매트릭스로 REORDER_GROUP 수행. `target_group_indices=[1,2,3]`이고 g2가 restart면 `base_donor_pool`은 g1과 g3 두 개인데 등분은 3으로 나눈다. 결과 매트릭스의 target 영역 iteration이 원래의 약 2/3로 줄고, 남은 1/3은 사라진다. restart가 없더라도 `total_iterations`가 그룹 수로 나누어떨어지지 않으면 나머지가 버려진다 | ㉮ 4918의 `num_original_target_groups`를 `len(self.reorder_state.base_donor_pool)`(실제로 배치될 non-restart 그룹 수)로 바꾼다. ㉯ 5083-5104의 Final Verification 루프 마지막 그룹의 `group_end`를 `target_iter_end`로 맞춰 나머지 iteration을 마지막 그룹이 흡수하게 한다. ㉰ Position 테스트(5022-5070)도 같은 기준으로 계산해 후보끼리 공정하게 비교되게 한다 |
| L2-7 | MEDIUM | INSERT_RANDOM_GROUP과 INSERT_RESTART_GROUP이 `REFC_CONFIG.MAX_DECODING_ITERATION` 상한을 확인하지 않는다 | [Gen_LLR_Insert_Random_Group:2695-2741](5_DAO/SRC/DAO_Main.py#L2695), [_Build_Inserted_Restart_Matrix:5899-5937](5_DAO/SRC/DAO_Main.py#L5899). 비교 대상은 상한을 지키는 [Gen_LLR_Insert_Mutated_Group:2858-2884](5_DAO/SRC/DAO_Main.py#L2858) | optimal의 `max_iteration`이 `MAX_DECODING_ITERATION`에 가까울 때 INSERT_RANDOM_GROUP stage를 돌리면 매 trial `INSERT_GROUP_NUM_ITERATION`(+restart 1)만큼 넘어간다. INSERT_RESTART_GROUP은 Round마다 1씩 넘어간다. [Is_LLR_Valid](5_DAO/SRC/DAO_LLR_MATRIX.py#L266)는 HBF 모드 규칙(HBF2)만 보고 일반 모드의 상한은 보지 않아 통과한다. 디코더가 실제로 돌지 않는 뒤쪽 그룹이 매트릭스에 남고, 그 상태로 optimal에 저장된다 | ㉮ [Is_LLR_Valid](5_DAO/SRC/DAO_LLR_MATRIX.py#L441) `max_iteration` 대입 바로 뒤에 `max_iteration <= REFC_CONFIG.MAX_DECODING_ITERATION` 규칙을 추가해 생성 단계에서 걸러지게 한다 (규칙 표에 H6으로 기재). ㉯ `Gen_LLR_Insert_Random_Group`에도 2858-2884와 같은 잔여 iteration 계산을 넣어 애초에 넘지 않는 크기로 만든다 |
| L2-8 | MEDIUM | DELETE_ROW의 다음 Round 후보를 그룹 삭제 뒤에도 옛 `target_group_indices`로 만든다 | [_Build_Delete_Row_Candidates:5432-5450](5_DAO/SRC/DAO_Main.py#L5432), 부르는 곳 [_Finalize_Delete_Row_Round:5711](5_DAO/SRC/DAO_Main.py#L5711) | Case B(그룹 전체 삭제, [_Delete_Entire_Group](5_DAO/SRC/DAO_Main.py#L5551))가 한 번이라도 확정되면 그 뒤 그룹의 인덱스가 1씩 당겨진다. `target_group_indices`는 그대로라 5442의 경계 검사가 마지막 값을 버리고, 결과적으로 마지막 그룹이 다음 Round부터 삭제 후보에서 빠진다. 그룹을 k번 지우면 뒤에서 k개가 빠진다 | `_Build_Delete_Row_Candidates`가 `self.target_group_indices` 대신 `range(DAO_CONFIG.INITIAL_TARGET_GROUP_IDX, len(matrix.groups))`를 돌게 바꾼다. 인자로 받은 `matrix`가 이미 현재 baseline이므로 그룹 수가 항상 맞는다. 같은 이유로 [_Build_Insert_Restart_Candidates:5799-5803](5_DAO/SRC/DAO_Main.py#L5799)도 같이 바꾼다 |
| L2-9 | MEDIUM | ADJUST_ITERATION의 trial 수와 실제 target 개수가 서로 다른 목록에서 계산된다 | [Set_Gen_Trial_LLR_Mode:8414-8422](5_DAO/SRC/DAO_Main.py#L8414)는 낡은 목록으로, [Init_Adjust_Iteration_Mode:4562-4588](5_DAO/SRC/DAO_Main.py#L4562)은 새 목록으로 센다 | 직전 stage가 그룹 수를 바꾼 뒤 ADJUST_ITERATION stage 진입. `max_modification_trial`이 더 작으면 뒤쪽 target이 아예 테스트되지 않고, 더 크면 남는 trial마다 [Gen_LLR_Adjust_Iteration:5336-5351](5_DAO/SRC/DAO_Main.py#L5336)이 None을 돌려주어 헛돈다 | `Init_Adjust_Iteration_Mode` 끝(4589 근처)에 `self.max_modification_trial = num_target_groups`를 넣고 8414-8422를 DELETE_ROW와 같은 임시값 분기로 줄인다 (L2-5와 같은 정리) |
| L2-10 | MEDIUM | `Initialize_Stage`의 restart 그룹 건너뛰기 루프가 실제 타겟 선택에 아무 영향을 주지 않는다 | 루프는 [2282-2294](5_DAO/SRC/DAO_Main.py#L2282)인데 생성 모드가 읽는 값은 [8322](5_DAO/SRC/DAO_Main.py#L8322)의 `current_target_group_idx`다. 실제 건너뛰기는 [8337-8343](5_DAO/SRC/DAO_Main.py#L8337)이 `max_modification_trial = 0`으로 stage 전체를 비우는 방식으로 따로 한다 | 항상. "모든 그룹이 restart인 경우"를 확인하면 `max_skip = len(target_group_indices)`만큼 돌고 (2285) 출발 자리로 정확히 되돌아와 restart 그룹을 가리킨 채 빠져나온다. 무한 루프는 없고 잘못된 인덱스도 남지 않지만, "Skipping restart group" 로그가 목록 길이만큼 찍혀 실제로 건너뛴 것처럼 보인다. 그 stage는 8337-8343이 비우므로 결과는 맞는다 | 2276-2296의 `current_target_idx` 계산과 건너뛰기 루프를 통째로 지우고, 타겟 커서를 `current_target_group_list_index` 하나로 통일한다. [Init_Reorder_Group_Mode:4516](5_DAO/SRC/DAO_Main.py#L4516)의 로그 줄은 `base_donor_pool`만 찍게 고치고 4456, 4464의 설명도 다시 쓴다 |
| L2-11 | LOW | `_create_reorder_test_matrix`와 그 짝인 `_recalculate_iterations_for_reorder`, `_is_reorder_candidate_better`가 호출자 없는 코드인데, 되살리면 optimal 매트릭스를 망가뜨린다 | [_create_reorder_test_matrix:6195](5_DAO/SRC/DAO_Main.py#L6195), [_recalculate_iterations_for_reorder:6118](5_DAO/SRC/DAO_Main.py#L6118), [_is_reorder_candidate_better:6018](5_DAO/SRC/DAO_Main.py#L6018) | grep으로 확인한 결과 세 함수 모두 외부 호출자가 없다. 6244-6288이 `base_matrix.groups[i]`를 복사 없이 그대로 담고 6308이 그 행들의 iteration을 덮어쓰므로, `base_matrix`(호출 시 optimal)가 같이 바뀐다. 또 `num_restart`, `restart_iter`, `max_iteration`을 갱신하지 않고 restart 그룹 type을 0으로 넣어(6274) `Build_Reordered_Matrix`(1)와 어긋난다 | 세 함수를 지운다. REORDER_GROUP의 현역 구현은 [Build_Reordered_Matrix:4849](5_DAO/SRC/DAO_Main.py#L4849)뿐이다 |
| L2-12 | LOW | `total_num_iterations` 선언은 `list[int]`인데 들어가는 값은 float이다 | 선언 [DAO_Main.py:590](5_DAO/SRC/DAO_Main.py#L590), 대입 [DAO_Main.py:1890](5_DAO/SRC/DAO_Main.py#L1890) (`total_iterations = float(recvbuf[2])` [1888](5_DAO/SRC/DAO_Main.py#L1888)) | 언제나. 다만 이 필드를 읽는 곳이 한 군데도 없어 (grep으로 확인: 590과 1890뿐) 동작과 출력에 영향이 없다 | 선언을 `list[float]`로 고치거나 필드를 지운다. 파일에 쓰이는 평균 반복 횟수는 `matrix.avg_iterations`([1960-1962](5_DAO/SRC/DAO_Main.py#L1960))가 따로 들고 있다 |
| L2-13 | LOW | `num_row_each_group`을 만들 때 세 곳이 dtype을 지정하지 않아 플랫폼 기본 정수형이 된다 | [_Delete_Entire_Group:5619](5_DAO/SRC/DAO_Main.py#L5619), [_Build_Inserted_Restart_Matrix:5913](5_DAO/SRC/DAO_Main.py#L5913), [_create_reorder_test_matrix:6323](5_DAO/SRC/DAO_Main.py#L6323). 다른 경로(3576, 5109, `np.insert` 계열)는 int32 | DELETE_ROW로 그룹을 지우거나 INSERT_RESTART_GROUP으로 그룹을 넣은 뒤. 파일 출력은 [Build_LLR_Matrix_Output_Lines:108-119](5_DAO/SRC/DAO_LLR_MATRIX.py#L108)가 `str()`을 거치므로 표기는 같고 동작 차이는 없다 | 세 곳에 `dtype=np.int32`를 붙여 매트릭스 안의 정수형을 한 가지로 맞춘다 |
| L2-14 | LOW | `Optional[LLR_MATRIX]`로 선언한 `optimal_LLR_matrix`를 None 확인 없이 쓰는 자리가 여덟 곳 있다 | [8353](5_DAO/SRC/DAO_Main.py#L8353), [8361](5_DAO/SRC/DAO_Main.py#L8361), [8377](5_DAO/SRC/DAO_Main.py#L8377), [8390-8391](5_DAO/SRC/DAO_Main.py#L8390), [8404](5_DAO/SRC/DAO_Main.py#L8404), [8419](5_DAO/SRC/DAO_Main.py#L8419), [Init_Reorder_Group_Mode:4448](5_DAO/SRC/DAO_Main.py#L4448), [Init_Delete_Row_Mode:5399](5_DAO/SRC/DAO_Main.py#L5399), [Init_Insert_Restart_Group_Mode:5763](5_DAO/SRC/DAO_Main.py#L5763) | 현재 호출 순서에서는 [Update_Optimal_LLR(is_initial=True):7800](5_DAO/SRC/DAO_Main.py#L7800)이 `Determine_Update_Decision`의 [1399-1400](5_DAO/SRC/DAO_Main.py#L1399)을 거쳐 무조건 optimal을 채우므로 닿지 않는다. 같은 파일 8325가 `if self.optimal_LLR_matrix`로 확인하는 것과 대비된다 | 확인을 넣기보다 선언을 정리하는 쪽이 낫다. `Run_Optimization` 진입 시점에 optimal이 채워져 있음이 불변 조건이므로, [Run_Optimization:8014-8016](5_DAO/SRC/DAO_Main.py#L8014)의 stage 루프 앞에 `if self.optimal_LLR_matrix is None: self.MPI_Abort(...)` 한 줄을 두고 이후 코드는 확인 없이 쓴다. 그러면 8325의 `if` 도 지울 수 있다 |
| L2-15 | LOW | spec 5.11이 INSERT_MUTATED_ROW의 필수 조건으로 `optimal_LLR_matrix.max_iteration < MAX_DECODING_ITERATION`을 적었는데 코드에는 그 확인이 없다 | [DAO_spec.md 5.11](5_DAO/DAO_spec.md), 6.2 실패 조건 표. 코드 쪽은 [DAO_Main.py:8347-8348](5_DAO/SRC/DAO_Main.py#L8347)의 주석이 "row만 추가하므로 iteration을 증가시키지 않는다"고 적고 있다 | 문서를 읽고 코드를 고치려는 사람이 없는 제약을 되살리게 된다. 실제로 INSERT_MUTATED_ROW는 iteration을 바꾸지 않으므로 제약이 필요 없다 | spec 5.11의 필수 조건 첫 줄과 6.2 표의 INSERT_MUTATED_ROW 행에서 max_iteration 조건을 지운다. INSERT_MUTATED_GROUP 행은 코드와 맞으므로 그대로 둔다 |

### 3-1. 문제 없음으로 확인한 항목

- ㉮ **`restart_groups`(1 기준)와 `groups`(0 기준)의 인덱스 보정 산술**: 그룹을 넣고 빼는 다섯 모드의
  보정식을 모두 확인했다. 삽입 쪽은 `restart_idx - 1 >= insert_position`일 때만 더하고
  (2726-2730, 3083-3087, 3444-3448, 5919-5925), 삭제 쪽은 `rg_0based > del_g_idx`일 때만 뺀다
  (5623-5632). 새로 넣은 restart 그룹의 1 기준 번호도 `insert_position + offset + 1`로 맞다
  (2734-2738, 3090-3094, 5925). 재배열은 완성된 그룹 목록에서 다시 만든다 (5154-5157).
  삽입 위치 **이후**만 보정하는 규칙이 다섯 곳 모두에서 지켜진다.
- ㉯ **`_Delete_Entire_Group`의 duration 배열 첨자**: `durations`를 삭제 대상을 건너뛰며 쌓고
  (5592-5601) `pop` 뒤에 같은 첨자로 다시 읽는다 (5604-5612). 삭제 후 위치와 첨자가 일치한다.
- ㉰ **그룹 간 iteration 연속성(spec G2)**: 모든 구조 변경 경로가 `current_iter = iter_end + 1`
  방식으로 다시 깔거나(3300-3312, 5604-5612, 5900-5909, 5083-5104) 삽입량만큼 뒤쪽을 통째로
  밀어(2703-2708, 3063-3068) 연속성을 지킨다. G2를 깨는 경로는 찾지 못했다.
- ㉱ **실마리 ㉵ (`current_target_idx` 생성 순서)**: 위 2-3절대로 `AttributeError` 경로는 없다.
- ㉲ **numpy 정수가 파일 출력 표기를 바꾸는 경우**: `Build_LLR_Matrix_Output_Lines`가
  `str()`([122-145](5_DAO/SRC/DAO_LLR_MATRIX.py#L122))와 `int(value):2d`, `CSW:4d`
  ([161-193](5_DAO/SRC/DAO_LLR_MATRIX.py#L161))로 찍으므로 int32와 파이썬 int의 표기가 같다.
  CSW는 [_get_new_CSW](5_DAO/SRC/DAO_Main.py#L732)가 `int()`로 돌려주고 ch/th는
  [_generate_random_row](5_DAO/SRC/DAO_Main.py#L754)가 int32 배열로 만든다. 실수가 섞여
  표기가 달라지는 자리는 찾지 못했다 (L2-12는 파일에 쓰이지 않는 필드다).

---

## 4절. `LLR_Header`나 `LLR_Row`에 필드를 하나 더할 때 손대야 하는 자리 전체 목록

옆 세션의 SW 분기 필드 추가를 위한 체크리스트다. 위에서 아래로 훑으면 빠지는 자리가 없다.

### 4-1. `LLR_Row`에 필드를 더할 때

**㉮ 모델과 파일 입출력 (`DAO_LLR_MATRIX.py`)**

| 자리 | 위치 | 할 일 |
|---|---|---|
| dataclass 정의 | [DAO_LLR_MATRIX.py:23-32](5_DAO/SRC/DAO_LLR_MATRIX.py#L23) | 필드 추가. 기본값을 주면 아래 생성자 호출 12곳을 한꺼번에 고치지 않아도 컴파일은 되지만, 값을 제대로 채우려면 12곳을 모두 봐야 한다 |
| 파일 읽기 | [Read_Input_LLR_Matrix:520-537](5_DAO/SRC/DAO_LLR_MATRIX.py#L520) | `row[:-4]`, `row[-4]`~`row[-1]` 슬라이스 위치가 고정 오프셋이므로 열이 늘면 여기를 먼저 고친다. `LLR_Row(...)` 호출은 [535](5_DAO/SRC/DAO_LLR_MATRIX.py#L535)의 위치 인자 6개 |
| 파일 쓰기 | [Build_LLR_Matrix_Output_Lines:147-204](5_DAO/SRC/DAO_LLR_MATRIX.py#L147) | 행 루프의 `line` 조립(195-201)과 optimal 대비 `*` 표시 로직(178-193) 양쪽에 새 열을 넣는다 |
| 유효성 검사 | [Is_LLR_Valid:294-430](5_DAO/SRC/DAO_LLR_MATRIX.py#L294) | 행 단위 규칙(G4 floor_flag, C1~C4 CSW, R1~R2 restart)이 모이는 자리. 새 필드 규칙을 여기에 넣고 `DAO_spec.md` 3절 표에도 같은 번호로 적는다 |
| 자동 보정 | [Correct_LLR_Matrix:561-601](5_DAO/SRC/DAO_LLR_MATRIX.py#L561), [Correct_Ch_Th_In_Row:603-645](5_DAO/SRC/DAO_LLR_MATRIX.py#L603) | 새 필드가 범위나 정렬 규칙을 가지면 보정 대상에 넣는다. 575-582가 restart 행을 건너뛰는 규칙에 주의 |

**㉯ `LLR_Row` 생성자 호출 12곳 (`DAO_Main.py`)**

| 함수 | 줄 | 어떤 행인지 |
|---|---|---|
| [Insert_Random_Row](5_DAO/SRC/DAO_Main.py#L2361) | 2446 | INSERT_RANDOM_ROW가 넣는 랜덤 행 |
| [Gen_LLR_Insert_Random_Group](5_DAO/SRC/DAO_Main.py#L2585) | 2636 | 함께 넣는 restart 행 |
| 같은 함수 | 2670 | 새 그룹의 랜덤 행 |
| [Gen_LLR_Insert_Mutated_Group](5_DAO/SRC/DAO_Main.py#L2792) | 2990 | 함께 넣는 restart 행 |
| 같은 함수 | 3017 | 소스 그룹을 복사한 행 (`source_row`에서 옮겨야 할 필드가 있는지 확인) |
| [Gen_LLR_Insert_Mutated_Row](5_DAO/SRC/DAO_Main.py#L3136) | 3252 | 소스 행을 복사한 행 |
| [Gen_LLR_Split_Group](5_DAO/SRC/DAO_Main.py#L3327) | 3391 | front 그룹 행 (원본에서 승계) |
| 같은 함수 | 3403 | back 그룹 행 (원본에서 승계) |
| [Gen_LLR_Gen_Initial_Group](5_DAO/SRC/DAO_Main.py#L3582) | 3628 | 초기 그룹의 랜덤 행 |
| [_create_restart_group](5_DAO/SRC/DAO_Main.py#L5728) | 5746 | REORDER와 INSERT_RESTART_GROUP이 공용으로 쓰는 restart 행 |
| [Copy_Group](5_DAO/SRC/DAO_Main.py#L8865) | 8907 | 후보 그룹 dict에서 되살리는 행 |
| [Build_Single_Row_Matrix](5_DAO/SRC/DAO_Main.py#L10192) | 10205 | GEN_SINGLE_ROW 모드의 단일 행 |

**㉰ 행 값을 dict로 담았다가 되살리는 경로 (여기를 빠뜨리면 복사 계열 모드에서만 값이 사라진다)**

| 자리 | 위치 | 할 일 |
|---|---|---|
| COPY_ROWS 후보 수집 | [Get_Copy_Row_Candidates:4368-4403](5_DAO/SRC/DAO_Main.py#L4368) | 4383-4387의 dict 키에 새 필드 추가 |
| COPY_GROUP 후보 수집 | [Get_Copy_Group_Candidates:4405-4443](5_DAO/SRC/DAO_Main.py#L4405) | 4429-4435의 dict 키에 새 필드 추가 |
| COPY_GROUP 되살리기 | [Copy_Group:8905-8913](5_DAO/SRC/DAO_Main.py#L8905) | 위 dict에서 새 필드를 읽어 `LLR_Row`에 넣는다 |
| 외부 후보 읽기 | [_Load_External_Single_Row_Candidates:4278-4366](5_DAO/SRC/DAO_Main.py#L4278) | 외부 파일에서 만든 후보 dict의 키를 맞춘다 |
| 값 변이 | [_generate_mutation_for_group:3472](5_DAO/SRC/DAO_Main.py#L3472), [_generate_mutation_for_row:3523](5_DAO/SRC/DAO_Main.py#L3523) | 새 필드가 변이 대상이면 두 함수에 넣는다 (지금은 `ch_th_values`만 본다) |

**㉱ 손댈 필요가 없는 자리**: `Build_Reordered_Matrix`, `Build_Adjusted_Iteration_Matrix`,
`_Build_Deleted_Row_Matrix`, `_Build_Inserted_Restart_Matrix`는 기존 `LLR_Row` 객체를 그대로
옮기거나 `Deep_Copy`([DAO_LLR_MATRIX.py:220](5_DAO/SRC/DAO_LLR_MATRIX.py#L220), `copy.deepcopy`)에
기대므로 새 필드가 저절로 따라간다.

### 4-2. `LLR_Header`에 필드를 더할 때

**㉮ 모델과 파일 입출력 (`DAO_LLR_MATRIX.py`)**

| 자리 | 위치 | 할 일 |
|---|---|---|
| dataclass 정의 | [DAO_LLR_MATRIX.py:9-21](5_DAO/SRC/DAO_LLR_MATRIX.py#L9) | 필드 추가 |
| 헤더 생성 | [Read_Input_LLR_Matrix:494-506](5_DAO/SRC/DAO_LLR_MATRIX.py#L494) | `LLR_Header(...)`를 **위치 인자 11개**로 부르고 있다. 중간에 필드를 끼우면 값이 통째로 밀린다. 이 기회에 키워드 인자로 바꾸는 편이 안전하다 |
| 파일 읽기 순서 | [Read_Input_LLR_Matrix:476-492](5_DAO/SRC/DAO_LLR_MATRIX.py#L476) | `idx_line`을 한 줄씩 밀며 읽는다. 새 줄을 넣는 위치를 정하고 `num_restart > 0`일 때만 한 줄 더 읽는 486-489의 조건부 구조를 따른다 |
| 파일 쓰기 순서 | [Build_LLR_Matrix_Output_Lines:122-145](5_DAO/SRC/DAO_LLR_MATRIX.py#L122) | 읽기와 같은 순서로 넣는다. optimal 대비 `*` 표시가 필요하면 102-119의 `format_with_diff` / `format_array_with_diff`를 쓴다 |
| 유효성 검사 | [Is_LLR_Valid:275-291](5_DAO/SRC/DAO_LLR_MATRIX.py#L275) | H1~H5가 모인 자리. 그룹 수에 비례하는 배열이면 `num_group == len(새 필드)` 규칙을 추가하고 `DAO_spec.md` 3절 표에 H6으로 적는다 |

**㉯ 헤더를 다시 쓰는 생성 모드 (그룹 수에 비례하는 배열 필드라면 전부 손대야 한다)**

| 함수 | 줄 | 지금 무엇을 고치고 있는지 |
|---|---|---|
| [Insert_Random_Row](5_DAO/SRC/DAO_Main.py#L2361) | 2471 | `num_row_each_group[g] += 1` |
| [Gen_LLR_Insert_Random_Group](5_DAO/SRC/DAO_Main.py#L2585) | 2695-2738 | restart_iter 밀기, num_group, num_row_each_group, type_each_group, num_restart, restart_groups |
| [Gen_LLR_Insert_Mutated_Group](5_DAO/SRC/DAO_Main.py#L2792) | 3056-3094 | 위와 같은 여섯 가지 |
| [Gen_LLR_Insert_Mutated_Row](5_DAO/SRC/DAO_Main.py#L3136) | 3277 | `num_row_each_group[g] += 1` |
| [_recalculate_group_iterations](5_DAO/SRC/DAO_Main.py#L3288) | 3316-3325 | max_iteration, restart_iter |
| [Gen_LLR_Split_Group](5_DAO/SRC/DAO_Main.py#L3327) | 3430-3452 | num_group, num_row_each_group, type_each_group, restart_groups, max_iteration |
| [_Replace_With_Single_Group](5_DAO/SRC/DAO_Main.py#L3570) | 3572-3580 | 헤더 전체를 1그룹 상태로 다시 씀 (새 필드도 여기서 초기화해야 한다) |
| [Build_Reordered_Matrix](5_DAO/SRC/DAO_Main.py#L4849) | 5106-5157 | num_group, num_row_each_group, type_each_group, num_restart, restart_iter, restart_groups |
| [Build_Adjusted_Iteration_Matrix](5_DAO/SRC/DAO_Main.py#L4604) | 4701-4727 | 지금은 헤더를 건드리지 않는다 (L2-4 수리 대상) |
| [_Build_Deleted_Row_Matrix](5_DAO/SRC/DAO_Main.py#L5522) | 5542 | `num_row_each_group[g] -= 1` |
| [_Delete_Entire_Group](5_DAO/SRC/DAO_Main.py#L5551) | 5616-5643 | 위 여섯 가지 + max_iteration |
| [_Build_Inserted_Restart_Matrix](5_DAO/SRC/DAO_Main.py#L5870) | 5910-5937 | 위 여섯 가지 + max_iteration |
| [Copy_Group](5_DAO/SRC/DAO_Main.py#L8865) | 8918-8919 | `num_row_each_group[g]`, `type_each_group[g]` |
| [_create_reorder_test_matrix](5_DAO/SRC/DAO_Main.py#L6195) | 6323-6325 | 죽은 코드. L2-11대로 지우면 이 줄은 볼 필요가 없다 |

**㉰ 헤더를 읽기만 하는 자리 (새 필드가 비교나 출력 대상이면 같이 본다)**

| 자리 | 위치 | 할 일 |
|---|---|---|
| 외부 매트릭스 호환 검사 | [_Check_Header_Compatibility:4261-4277](5_DAO/SRC/DAO_Main.py#L4261) | 외부에서 읽은 매트릭스와 현재 매트릭스가 같아야 하는 고정 필드 목록. 새 필드가 고정 필드면 여기에 넣는다 |
| 디버그 요약 | [_summarize_value:91-105](5_DAO/SRC/DAO_Main.py#L91) | 오류 스냅샷에 찍히는 헤더 dict |
| COPY_ROWS trial 수 계산 | [Set_Gen_Trial_LLR_Mode:8361](5_DAO/SRC/DAO_Main.py#L8361) | `num_row_each_group` 합에서 `num_restart`를 빼 후보 행 수를 센다 |
| 행 길이 계산 | [2623](5_DAO/SRC/DAO_Main.py#L2623), [2856](5_DAO/SRC/DAO_Main.py#L2856), [4292](5_DAO/SRC/DAO_Main.py#L4292), [5888](5_DAO/SRC/DAO_Main.py#L5888), [6267](5_DAO/SRC/DAO_Main.py#L6267)의 `num_parameter_each_set * num_dv` | 행 길이에 영향을 주는 필드면 이 식을 쓰는 모든 자리를 확인한다 |

**㉱ 문서**: 새 필드는 [DAO_spec.md 2.2 LLR_Header 필드 표](5_DAO/DAO_spec.md)와
2.3 LLR_Row 필드 표, 3절 유효성 규칙 표, 그리고 그 필드를 바꾸는 모드의 5절 "변경 사항" 목록에
같이 적는다. 5절 각 모드의 "변경 사항"이 헤더 갱신 체크리스트 노릇을 하므로, 1절 표에서 `○`인 칸은
전부 5절에 한 줄씩 있어야 한다.

### 4-3. 필드를 더하기 전에 먼저 고치기를 권하는 것

옆 세션이 필드를 더하면 위 표의 "여섯 벌 중복" 자리를 여섯 번 똑같이 고쳐야 한다. 순서를 이렇게
잡으면 고칠 자리가 줄어든다.

- 1. L2-11대로 죽은 코드 세 함수를 지운다 (동작 변경 없음, 고칠 자리 1벌 감소)
- 2. L2-4의 처방대로 restart 헤더 재빌드를 `_Rebuild_Restart_Header_From_Groups(matrix)` 한 메서드로
  뽑고 다섯 곳이 그것을 부르게 한다 (L2-4 결함도 같이 낫는다)
- 3. 그룹 삽입과 삭제 뒤의 헤더 재계산도 같은 방식으로 `_Rebuild_Group_Header_From_Groups(matrix)`
  하나로 모은다 (`num_group`, `num_row_each_group`, `max_iteration`은 `matrix.groups`만 보면
  전부 다시 만들 수 있다. `type_each_group`은 그룹별 값이라 모드가 따로 넘겨야 한다)
- 4. 그 다음에 새 필드를 더하면 ㉯ 표의 열네 줄이 두세 줄로 줄어든다
