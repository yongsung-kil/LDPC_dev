# Round 2 결과: 분석 (lv1, 에이전트 4개)

> 기록: 2026-09-22 23:11:48
> 대상: 6e035e6..15ab8e3의 `5_DAO/SRC` 변경분. 에이전트 4개(Opus), 원본은 [agent_1.md](agent_1.md), [agent_2.md](agent_2.md), [agent_3.md](agent_3.md), [agent_4.md](agent_4.md)

발견: 원 33건 (CRITICAL 3, HIGH 3, MEDIUM 13, LOW 14). 같은 뿌리를 합치고 죽은 코드 건을 내려 **28건 (CRITICAL 2, HIGH 2, MEDIUM 10, LOW 14)**.

- 에이전트 4의 CRITICAL 2건과 HIGH 1건은 뿌리가 하나(타겟 목록에서 마지막이 아닌 분기를 빼지 않음)라 C1 한 건으로 합쳤다
- 에이전트 1의 MEDIUM 2번(`_create_reorder_test_matrix`의 restart 삽입)은 메인이 호출처를 확인한 결과 부르는 곳이 없는 죽은 코드라 LOW로 내리고 에이전트 2의 LOW 9번과 합쳤다
- 에이전트 1의 1번과 에이전트 2의 4번(restart 삽입), 에이전트 1의 3번과 에이전트 2의 5번(전면 재번호)은 같은 자리라 합쳤다

## CRITICAL 2건

| # | 문제 | 위치 | 재현 조건 | 처방 | 지적 |
|---|------|------|----------|------|------|
| C1 | `Initialize_Stage`가 타겟 목록을 묶음 대표로 접기만 하고 "마지막 분기가 아닌 묶음"을 빼지 않는데, `Check_SW_Branch_Mode_Allowed`는 그런 타겟을 만나면 `MPI_Abort`한다. 파일 1은 기본 `INITIAL_TARGET_GROUP_IDX`(1)로 목록이 [0, 2, 3, 4, 6, ...]이 되어 stage 1의 첫 타겟 g0(분기 0)에서 전체가 죽고, 파일 2는 한 바퀴 뒤 g2에서 죽는다. 어떤 시작 index로도 파일 1에서 설계 요구("마지막 분기만 갱신")를 만족시킬 수 없다 | [DAO_Main.py:2308](5_DAO/SRC/DAO_Main.py#L2308), [DAO_Main.py:8372](5_DAO/SRC/DAO_Main.py#L8372) | 분기 매트릭스를 초기 매트릭스로 쓰는 실행 전부 | `Initialize_Stage`의 묶음 접기에서 `span_of_group[head]`가 있고 `group_branch_idx[head] != span[2] - 1`이면 목록에 넣지 않고 로그에 적는다. 중단 검사는 안전망으로 남긴다. 파일 1 시작 1이면 목록이 [2, 4, 6, 7, 8, 9, 10, 11]이 된다 | 4 |
| C2 | SW 허용 검사가 stage 건너뛰기 판정보다 먼저 돈다. `Check_SW_Branch_Mode_Allowed`는 분기 매트릭스에서 GEN_INITIAL_GROUP을 무조건 거부하는데, 그 아래의 "GEN_INITIAL_GROUP은 stage 1에서만 동작하고 나머지는 skip" 처리에 닿기 전에 root가 `MPI_Abort`한다 | [DAO_Main.py:8452](5_DAO/SRC/DAO_Main.py#L8452), 건너뛰기 판정 [DAO_Main.py:8462](5_DAO/SRC/DAO_Main.py#L8462) | 분기 매트릭스 + 모드 시퀀스에 0(GEN_INITIAL_GROUP) 포함, stage 2 이상 | `is_skip_this_stage` 계산을 SW 검사 앞으로 옮기고 건너뛰는 stage에서는 SW 검사를 부르지 않는다 | 3 |

## HIGH 2건

| # | 문제 | 위치 | 재현 조건 | 처방 | 지적 |
|---|------|------|----------|------|------|
| H1 | COPY_GROUP이 후보 그룹의 `floor_flag`와 헤더 표시를 타겟에 그대로 복사한다. 후보가 헤더 10인 묶음이면 결과가 `Is_LLR_Valid`를 통과해, 사용자가 만들지 않은 SW 분기 구간이 보통 그룹 자리에 새로 생긴다 (실행 확인). "DAO는 분기를 만들지 않는다" 규칙 위반 | [DAO_Main.py:9043](5_DAO/SRC/DAO_Main.py#L9043), [DAO_Main.py:9052](5_DAO/SRC/DAO_Main.py#L9052) | 분기 매트릭스 + `INITIAL_TARGET_GROUP_IDX`를 구간 뒤로 둔 설정 + COPY_GROUP(31, 기본 시퀀스에 있음) | `Copy_Group`이 타겟 row의 `floor_flag`와 `type_each_group[target]`을 그대로 두고 `ch_th_values`와 `CSW`만 복사한다 (`Copy_Row`가 이미 그 방식). `Get_Copy_Group_Candidates`에서 분기 그룹을 후보에서 뺀다 | 2 |
| H2 | `Build_Single_Row_Matrix`가 새 row의 꼬리를 `groups[0][0].floor_flag`에서 가져오는데 헤더에는 1을 적는다. 분기 매트릭스에서는 꼬리 0에 헤더 1이라 H8에 걸려 GEN_SINGLE_ROW 후보가 전부 무효가 된다 | [DAO_Main.py:10356](5_DAO/SRC/DAO_Main.py#L10356) | `RUN_DAO_MODE = GEN_SINGLE_ROW` + 분기 매트릭스 | 새 1그룹 1row 매트릭스는 분기가 없으므로 `floor_flag = SW_BRANCH_NONE`으로 고정한다 | 2 |

## MEDIUM 10건

| # | 문제 | 위치 | 처방 | 지적 |
|---|------|------|------|------|
| M1 | `_Build_Inserted_Restart_Matrix`(INSERT_RESTART_GROUP)가 새 restart의 꼬리를 `groups[0]`에서 가져오고 헤더에 1을 적으며 모든 그룹의 iteration을 1부터 다시 매겨, 분기 매트릭스에서 언제나 무효 trial을 만든다 | [DAO_Main.py:5937](5_DAO/SRC/DAO_Main.py#L5937), [5949](5_DAO/SRC/DAO_Main.py#L5949), [5963](5_DAO/SRC/DAO_Main.py#L5963) | 꼬리를 `SW_BRANCH_NONE`으로, 재번호는 `min(target_group_indices)` 그룹부터만 | 1, 2 |
| M2 | iteration을 1부터 전면 재번호하는 네 자리(`_recalculate_group_iterations`, `Build_Adjusted_Iteration_Matrix`, `_Delete_Entire_Group`, restart 삽입)가 분기 구간을 펴 버린다. 보호 구간 안전망이 잡아 틀린 결과는 없지만, 기본 시퀀스의 모드 42, 62, 70(그룹 통째 삭제)이 닿는 stage는 trial마다 5회 재시도를 돌고 버려져 헛돈다 | [DAO_Main.py:3346](5_DAO/SRC/DAO_Main.py#L3346), [4752](5_DAO/SRC/DAO_Main.py#L4752), [5655](5_DAO/SRC/DAO_Main.py#L5655) | 재번호 시작점을 1이 아니라 `min(target_group_indices)` 그룹의 `iter_start`로 두고 그 앞 그룹은 건드리지 않는다. 그 전 단계로 `has_sw_branch`일 때 이 경로를 미리 걸러 헛도는 stage를 없앤다 | 1, 2 |
| M3 | `Build_SW_Branch_Layout`의 오류 반환을 `Is_LLR_Valid` 하나만 받는다. 배치가 깨진 매트릭스에서 `Check_SW_Branch_Mode_Allowed`가 반쪽 `span_of_group`으로 "마지막 분기만" 규칙을 조용히 건너뛴다 (실증) | [DAO_Main.py:2301](5_DAO/SRC/DAO_Main.py#L2301) 등 호출처 5곳 | `Initialize_Stage`, `Check_SW_Branch_Mode_Allowed`, `_Protected_Groups_Changed`는 오류면 `MPI_Abort`, `_Get_Target_Bundle_Groups`는 오류를 올려 trial을 버리게 한다 | 1 |
| M4 | `Gen_LLR_Gen_Initial_Group`도 꼬리를 `groups[0]`에서 가져오고 헤더에 1을 적으며, groups가 비었을 때 기본값이 0이다. 지금은 모드 제한이 막지만 조건이 바뀌면 바로 드러난다 | [DAO_Main.py:3666](5_DAO/SRC/DAO_Main.py#L3666) | `floor_flag = SW_BRANCH_NONE` 고정 | 2 |
| M5 | 묶음 변이로 mutation 개수가 묶음 그룹 수만큼 늘고, 그 개수가 `Generate_All_Fine_Tuning_Mutations`의 `itertools.product` 조합 수의 지수가 된다 (묶음 4그룹, 요소 2개, 범위 5면 조합 수가 수십만) | [DAO_Main.py:3887](5_DAO/SRC/DAO_Main.py#L3887) | 조합 수 상한을 두고 넘으면 무작위 표본, 리스트 대신 generator. `ENABLE_FINE_TUNING_AFTER_UPDATE`는 기본 False | 2 |
| M6 | 보호 구간 검사로 버려진 trial이 root의 `target_group_indices` 변경(INSERT 계열과 SPLIT이 반환 직전에 갈아 끼움)을 되돌리지 않고, 성공 시에만 도는 bcast를 타지 않아 root와 worker의 목록이 갈린다 | [DAO_Main.py:2011](5_DAO/SRC/DAO_Main.py#L2011) | 생성 함수를 부르기 전에 목록을 복사해 두고 `new_LLR_matrix`가 None이 되는 모든 갈래에서 되돌린다 | 3 |
| M7 | `Delete_Own_Uncors(is_redecoded_uncor=True)`가 벡터 적재 모드에서 다른 이름을 지워 아무 일도 하지 않는다. 0eebbb6의 재디코딩 uncor 누적 수정이 벡터 모드를 덮지 못한다 (다른 세션 수정과의 접점) | [DAO_Main.py:8604](5_DAO/SRC/DAO_Main.py#L8604), [2097](5_DAO/SRC/DAO_Main.py#L2097) | `Rebuild_Partial_Pool`과 같은 식으로 `is_uncor_type_seed`를 넘기되, 벡터 모드는 입력과 출력 파일 이름이 같아 삭제 대신 실행 전 줄 수를 기록해 뒤에서 잘라낸다 | 3 |
| M8 | uncor 파일 삭제가 `exists()`와 `unlink()` 사이의 경합으로 `FileNotFoundError`를 내면 곧바로 `MPI_Abort`로 전체가 죽는다 | [DAO_Main.py:1541](5_DAO/SRC/DAO_Main.py#L1541) | `FileNotFoundError`는 목적이 이루어진 것이므로 지나가고, 나머지 OSError는 짧게 재시도한 뒤 `MPI_Abort` | 3 |
| M9 | 검사 `check_sw_branch.py`의 모드 허용 검사가 `Initialize_Stage`가 실제로 만드는 목록 대신 손으로 고른 목록을 넘겨 C1을 잡지 못했다 | [checks/check_sw_branch.py](../checks/check_sw_branch.py) | 시작 index 0부터 그룹 수 - 1까지 실제 식으로 목록을 만들고 모든 타겟에 허용 검사를 돌려 하나도 막히지 않는지 보는 검사를 더한다 | 4 |
| M10 | `IS_HBF_OPT=True`와 분기 매트릭스를 함께 쓰면 반드시 `MPI_Abort`로 죽는다 (HBF 시퀀스의 INSERT 계열이 허용 검사에 걸리고, 매트릭스 전체가 한 구간이라 보통 그룹 타겟이 없다) | [DAO_Config.py:134](5_DAO/SRC/DAO_Config.py#L134), [DAO_Main.py:8359](5_DAO/SRC/DAO_Main.py#L8359) | `Validate_Config`에 "`IS_HBF_OPT`이 True인데 초기 매트릭스에 분기 그룹이 있으면 오류"를 더하고 spec 3.7 ㉲를 "함께 쓸 수 없고 시작 시점에 막는다"로 고친다 | 4 |

## LOW 14건

- L1 `Initialize_Stage`에서 그룹이 0개이면 `bundle_of_group[-1]`로 `IndexError` (1)
- L2 `type_each_group` 길이가 그룹 수와 다를 때 `[0] * n`으로 물러서면 헤더 기반 구간 가름이 사라진다. 오류로 돌려주는 편이 맞다 (1)
- L3 배치 계산기가 `max_iteration`을 다시 쓰는 부작용. rank 사이 값 차이로 번지는 경로는 없음 (1, 3)
- L4 restart 그룹을 만드는 두 자리가 헤더에 1과 0을 다르게 적는다. 입력 파일 관례는 1 (1)
- L5 죽은 코드 세 벌(`_create_reorder_test_matrix`, `_recalculate_iterations_for_reorder`, `Change_Max_Iteration`)이 지금 규약과 어긋난 값을 들고 남아 있다. 지운다 (1, 2)
- L6 `Mutate_CSW`의 마지막 범위 자르기가 이웃이 `MAX_CSW`나 `MIN_CSW`일 때 엄격 감소를 되돌린다. 자르지 말고 그 mutation을 버린다 (2)
- L7 `Correct_LLR_Matrix`의 배수 맞춤이 파이썬 반올림(절반은 짝수 쪽)을 탄다. 20은 16으로 간다. 규칙에는 맞음 (2)
- L8 배리어 타임아웃 37800초를 ECC를 끼지 않는 배리어에도 붙여 교착 감지가 늦다. `MPI_Barrier`에 인자를 두고 ECC를 사이에 둔 두 자리에만 긴 값을 넘긴다 (3, 4)
- L9 감시 thread가 MPI 스레드 지원 수준을 확인하지 않는다. 시작 시 `Query_thread()`를 읽어 로그에 남긴다 (3)
- L10 `Check_Barrier_Sync`의 두 통신만 `_safe_*` 경로를 벗어나 예외 스냅샷이 없다. 감시 자체는 되고 있어 Round 1 실마리 ㉱는 사실과 달랐다 (3)
- L11 타겟 목록을 짓는 식이 세 자리(`Initialize_Stage`, `Initialize_LLR_Matrix`, `Update_Optimal_LLR` 복원)에 흩어져 있고 묶음 접기는 한 곳뿐이다. 메서드 하나로 모은다 (4)
- L12 spec 3장 규칙표에 코드가 내는 오류 문구 네 개가 빠져 있다 (4)
- L13 spec 3.7 규칙 ㉯의 "타겟 그룹"이 목록 전체인지 현재 타겟인지 읽히지 않는다. 코드(목록 전체)가 맞으니 문구를 고친다 (4)
- L14 `check_dao_fixes.py`의 "H9 두 식 일치" 검사가 같은 식을 자기 자신과 견준다. `Init_Reorder_Group_Mode`를 실제로 불러 견준다 (4)

## 통과 항목

- ㉮ 배치 계산기의 다섯 갈래 전이에서 `expected_start`가 늘 정해짐 (퍼즈 2만 건 예외 0), `close_span`의 `nonlocal` 정합 (1)
- ㉯ 옛 형식 회귀: `Prime_ECC_2.3`과 `2.4`의 입력을 init_n 1, 2, 3으로 읽어 여섯 조합 모두 유효하고 왕복 일치. R3과 R4는 `_create_restart_group`의 출력과 일치 (1)
- ㉰ H6과 G7 전수 대조: 그룹이나 행 수를 바꾸는 열두 자리가 모두 헤더 세 배열을 함께 갱신 (2)
- ㉱ CSW 보정 순서와 `ValueError` 두 호출처, HBF 다섯 모드 처리와 dv 0 TH 범위 네 자리, `max_iteration` 두 정의 (2)
- ㉲ bcast 튜플 7개 송수신 순서, `Gen_Trial_LLR`의 집단 통신 횟수 rank 동일, ack 비우기가 배리어 사이, `_Report_Missing_Acks` 두 자리 순서 동일, `_Restore_State_After_Partial_Rebuild`의 bcast 횟수와 `prev_seed_mode`, GEN_SINGLE_ROW가 모든 rank에서 같은 후보에서 멈춤, `Update_Configs` 종속 (3)
- ㉳ 자명한 오류 수정 처방 여섯 건(설정 순서, ch_type 3 확장, 속도 테스트 시드, inf 치환, REORDER trial 식, C2 순서 교체) 모두 정확 (4)
- ㉴ 예시 파일 두 개의 헤더, 꼬리, 행 수, iteration, 묶음, 구간, max_iteration 124, 왕복 토큰이 설계 2.1 표와 spec 3.7 표에 한 칸도 어긋나지 않음. spec 규칙 아홉 개는 코드와 1대1 대응 (4)

## 종합 판정

**수정 필요.** CRITICAL 2건과 HIGH 2건은 모두 이번 SW 분기 지원 코드 안의 결함이고 고침이 작다.

- ㉮ C1은 정책의 빈틈이다. "마지막 분기만 갱신한다"를 중단이 아니라 타겟 목록에서 미리 빼는 것으로 구현해야 파일 1이 기본 설정으로 돈다
- ㉯ C2는 검사 순서다. 건너뛰기 판정 뒤로 옮기면 된다
- ㉰ H1, H2, M1, M4는 "새 row와 새 그룹의 꼬리는 분기 없음(-1)"이라는 한 규칙을 네 자리에 넣는 일이다
- ㉱ M2(전면 재번호)는 구조 변경 모드가 분기 구간 뒤에서도 헛돌지 않게 하려면 재번호 시작점을 타겟 앞으로 옮겨야 한다. 이것은 네 자리를 고치는 중간 규모 작업이다

라이트 리뷰이므로 Round 3(검증)은 하지 않았다. C1, C2, H1은 에이전트가 실행으로 재현했고, 나머지는 코드 읽기로 확정했다.
