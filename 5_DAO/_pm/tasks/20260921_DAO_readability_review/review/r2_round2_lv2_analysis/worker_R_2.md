# Round 2 / 팀 R(가독성) / 워커 2: 이름, 설정, 상태, 함수

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> (`git log --oneline -1 -- 5_DAO/SRC` 결과)
> 기록: 2026-09-21 15:12:07
> 배정 관점: R3(이름 규약과 같은 뜻의 다른 이름), R4(설정 계층과 확정 시점), R5(인스턴스 상태의 생성 위치), R6(함수 길이, 중첩 깊이, 반복 관용구)

## 확인 범위

- ㉮ 기계 집계: `DAO_Main.py` 전체(10,428줄)에서 def 경계 234개와 길이, `self.X = ` 최초 대입 지점 전수, 들여쓰기 최대 깊이, `_safe_bcast` 호출 46곳, 이름 규약 갈래별 개수
- ㉯ 정독: `__init__`과 `_init_per_matrix_state`와 프로퍼티(L481-660), 상태 dataclass 4개(L207-402), `Update_*_Configs`(L403-480), `Initialize_Stage`(L2247-2311), 긴 함수 8개, 멀티라운드 4모드 구획(L4446-6017), `Print_Test_Summary`(L7617-7770), `Print_Config`와 `Print_Configs`(L7261-7279), `Set_Gen_Trial_LLR_Mode`(L8293-8448), `Set_CSW_Update_Limit`과 호출 경로, `Setup`과 `Main`(L8705-8715, L10001-10025), `Validate_Config`(L9647-9901)
- ㉰ 전체 정독: [DAO_Config.py](5_DAO/SRC/DAO_Config.py) 457줄, [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py)의 `MULTI_ROUND_*` 표와 `SKIP_RESTART_GROUP`, [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py)의 `__init__`과 `Deep_Copy`

---

## R3. 이름 규약과 같은 뜻의 다른 이름

### R3-1. 대소문자 규약 실태 (전수 집계)

| 갈래 | `DAO_Main.py` 개수 | 보기 | 판정 |
|------|------|------|------|
| 첫 글자 대문자 스네이크 | 161 | `Gen_LLR_Insert_Random_Group`, `Test_Trial_LLR` | 이 저장소의 사실상 정본 |
| 밑줄 + 첫 글자 대문자 | 35 | `_Finalize_Delete_Row_Round`, `_Build_Delete_Row_Candidates` | 정본에 `_` 접두사를 붙인 형태 |
| 밑줄 + 소문자 | 22 | `_safe_bcast`, `_init_per_matrix_state`, `_summarize_value` | 다른 규약 |
| 소문자 | 5 | `is_load_seed_mode`, `active_cores`(프로퍼티), `fmt_result`(중첩 함수) | 프로퍼티와 중첩 함수는 이 규약이 자연스럽다 |
| 전부 대문자 | 1 | [BACKUP_SRC](5_DAO/SRC/DAO_Main.py#L8795) | 메서드인데 상수처럼 보인다 |

`_` 접두사가 실제로 비공개를 뜻하는지 확인한 결과, 같은 역할을 하는 형제 함수 사이에서도 규약이 갈린다.

- ㉠ [Finalize_Reorder_Round](5_DAO/SRC/DAO_Main.py#L4800)(접두사 없음)와 [_Finalize_Delete_Row_Round](5_DAO/SRC/DAO_Main.py#L5687), [_Finalize_Insert_Restart_Group_Round](5_DAO/SRC/DAO_Main.py#L5978)(접두사 있음)는 호출 방식이 같은데(각 모드의 `Gen_LLR_*` 안에서만 호출) 이름 규약만 다르다
- ㉡ `Update_Reorder_Round_Result`, `Update_Delete_Row_Round_Result`, `Update_Insert_Restart_Group_Round_Result` 셋은 `MULTI_ROUND_UPDATE_FUNC` 표에서 문자열로 찾아 부르므로 모두 공개여야 하고, 실제로 셋 다 접두사가 없다. 이 셋만 규약이 일관된다

**처방 (우선순위 하, 위험 없음, 손대는 자리 3곳)**: `Finalize_Reorder_Round`에 `_` 접두사를 붙여 `_Finalize_Reorder_Round`로 맞춘다. 정의 1곳, 호출 1곳([L5229](5_DAO/SRC/DAO_Main.py#L5229)), 오류 문구 1곳이다.

**처방 (우선순위 중, 위험 없음, 손대는 자리 2곳)**: [BACKUP_SRC](5_DAO/SRC/DAO_Main.py#L8795)를 `Backup_Src_Files`로 바꾼다. 정의 1곳과 호출 1곳([L8789](5_DAO/SRC/DAO_Main.py#L8789))뿐이다. README와 DAO_spec에는 나오지 않는다.

**처방 (우선순위 하, 위험 없음)**: `_safe_bcast`, `_safe_gather`, `_mpi_comm_with_timeout`처럼 MPI 계층의 소문자 이름 22개는 "이 계층은 저수준 도우미"라는 뜻을 이미 담고 있다. 규약을 하나로 통일하기보다, 모듈 머리말이나 클래스 머리 주석에 "소문자 밑줄 이름은 MPI와 문자열 요약 저수준 도우미"라고 한 줄로 밝히는 쪽이 비용 대비 효과가 크다.

### R3-2. 같은 뜻의 다른 이름: target 인덱스 5종 (필수 산출물 ㉮)

| 현재 이름 | 그 이름이 가리키는 뜻 (코드 확인) | 값이 정해지는 자리 | 제안 이름 | 손대는 자리 |
|-----------|--------------------------------|------------------|-----------|-----------|
| `target_group_indices` | 최적화 대상 그룹 번호의 목록 (매트릭스 안의 실제 그룹 번호들) | [Initialize_Stage:L2273](5_DAO/SRC/DAO_Main.py#L2273), 그룹 구조 변경 모드 7곳 | `target_group_numbers` | SRC 65, README와 spec 17 |
| `current_target_group_idx` | 이번 stage가 손볼 그룹의 **매트릭스 안 번호** | [Set_Gen_Trial_LLR_Mode:L8322](5_DAO/SRC/DAO_Main.py#L8322) | `current_target_group_number` | SRC 36, 문서 2 |
| `current_target_group_list_index` | 위 번호를 고를 때 쓴 **목록 안 위치**. `Gen_LLR_Mode_SEQUENCE` 한 바퀴마다 1 증가 | [Set_Gen_Trial_LLR_Mode:L8321](5_DAO/SRC/DAO_Main.py#L8321) | `target_position_by_mode_cycle` | SRC 6 |
| `current_target_idx` | 또 다른 **목록 안 위치**. stage마다 1 증가하고 restart 그룹이면 건너뛴다 | [Initialize_Stage:L2278-2291](5_DAO/SRC/DAO_Main.py#L2278) | `target_position_by_stage` | SRC 19 |
| `AdjustIterState.current_target_idx` | `adjust_iter_state.target_groups` 안의 위치 (위 둘과 무관한 제3의 목록) | [Init_Adjust_Iteration_Mode](5_DAO/SRC/DAO_Main.py#L4525) | `position_in_adjust_target_groups` | SRC 8 |

확인된 사실 하나를 덧붙인다. `current_target_idx`는 `Initialize_Stage` 안에서 계산되고 로그로 출력된 뒤, **바깥에서 읽는 자리가 [Init_Reorder_Group_Mode:L4516](5_DAO/SRC/DAO_Main.py#L4516)의 로그 문자열 한 곳뿐**이다. 실제로 손볼 그룹을 정하는 값은 `current_target_group_idx`이며 그 값은 `current_target_group_list_index`(회전 주기가 다른 별개 변수)로 뽑는다. 즉 같은 목록 위에서 회전 규칙이 다른 두 포인터가 동시에 돌고 있고, 그중 하나는 로그만 만든다.

- **처방 갈래 1 (우선순위 상, 위험 없음, 손대는 자리 19곳)**: `current_target_idx`를 `stage_target_rotation_for_log`로 바꾸고, `Initialize_Stage`의 계산 블록 위에 "이 값은 stage 진행 상황을 사람이 읽기 위한 표시이며 실제 타겟 선택은 `Set_Gen_Trial_LLR_Mode`가 한다"를 적는다. 동작은 그대로다
- **처방 갈래 2 (우선순위 중, 위험 있음, Decision 등급)**: 두 회전을 하나로 합쳐 `Initialize_Stage`가 정한 위치를 `Set_Gen_Trial_LLR_Mode`가 그대로 쓰게 만든다. restart 그룹 건너뛰기가 실제 타겟 선택에도 적용되므로 stage별 타겟 순서가 바뀐다. 동작 변경이므로 사용자 확인이 필요하다

### R3-3. 같은 뜻의 다른 이름: FER 계열 (필수 산출물 ㉮)

FER 이름은 **소유 계층**으로 갈린다. 표로 정리하면 혼동이 줄어든다.

| 층 | 이름 | 뜻 | 상태 |
|----|------|-----|------|
| 매트릭스(`LLR_MATRIX`) | `FERs` | 비교에 쓰는 Full FER (load_seed 모드면 seed, 아니면 raw) | 사용 중 |
| 매트릭스 | `raw_FERs`, `seed_FERs` | 측정 경로별 Full FER | 사용 중 |
| 매트릭스 | `FERs_partial`, `raw_FERs_partial`, `seed_FERs_partial` | 위 셋의 Partial 판 | 사용 중 |
| 매트릭스 | `avg_iterations`, `avg_iterations_partial` | 동점 시 가르는 평균 반복 횟수 | 사용 중 |
| 매트릭스 | `num_errors`, `num_tests`, `*_partial` | 요약 출력용 개수 | 사용 중 |
| 엔진(`LLR_OPT`) | `total_num_tests`, `total_num_errors`, `total_num_error_per_iters`, `total_FER_per_iters` | 이번 채널 테스트에서 모든 rank를 합산한 개수 | 사용 중 |
| 엔진 | `total_num_raw_tests`, `total_num_raw_errors`, `total_num_seed_tests`, `total_num_seed_errors` | 경로별 합산 개수, `Print_Test_Result`가 읽음 | 사용 중 |
| 엔진 | `total_raw_FERs`, `total_seed_FERs` | 합산 개수로 계산한 FER 값 | **쓰기만 하고 읽는 자리 없음** |
| 엔진 | `total_num_iterations` | 합산 반복 횟수 | **쓰기만 하고 읽는 자리 없음** |

- ㉠ `total_` 접두사가 두 가지 뜻으로 쓰인다. `total_num_tests`는 합계(개수)지만 `total_raw_FERs`는 합계가 아니라 그 합계로 계산한 비율이다. 이름만 보고 더할 수 있는 값이라고 오해할 수 있다
- ㉡ `total_raw_FERs`([L598](5_DAO/SRC/DAO_Main.py#L598) 생성, [L1912](5_DAO/SRC/DAO_Main.py#L1912) 대입), `total_seed_FERs`([L599](5_DAO/SRC/DAO_Main.py#L599), [L1900](5_DAO/SRC/DAO_Main.py#L1900)), `total_num_iterations`([L590](5_DAO/SRC/DAO_Main.py#L590), [L1890](5_DAO/SRC/DAO_Main.py#L1890))는 대입만 있고 읽는 자리가 없다

**처방 (우선순위 중, 위험 없음, 손대는 자리 6곳)**: `total_raw_FERs`, `total_seed_FERs`, `total_num_iterations` 세 속성을 지운다. 세 속성 모두 생성 1곳과 대입 1곳뿐이라 grep 6회로 끝난다. 지우기가 망설여지면 이름을 `measured_raw_FER_of_last_channel_test`처럼 바꿔 "합계가 아니라 마지막 채널 테스트의 측정값"임을 드러낸다.

### R3-4. 수단이 아니라 목적이 이름이 되었는지

| 현재 이름 | 실제로 하는 일 | 판정 | 제안 이름 | 손대는 자리 |
|-----------|---------------|------|-----------|-----------|
| [Set_Gen_Trial_LLR_Mode](5_DAO/SRC/DAO_Main.py#L8293) (156줄) | 모드 선택 + 타겟 그룹 번호 결정 + stage 건너뛰기 판정 + 모드별 최대 trial 수 계산 + bcast | 이름이 첫 번째 일만 말한다 | `Prepare_Stage_Plan` (아래 R6-3에서 쪼갠 뒤) | SRC 7, 문서 2 |
| [Mutate_Matrix_Setup](5_DAO/SRC/DAO_Main.py#L7097) | 본문 한 줄로 `Set_CSW_Update_Limit()`만 부른다 | 수단도 목적도 말하지 않는 빈 껍데기 | 없앤다 (호출자가 `Set_CSW_Update_Limit`을 직접 부른다) | SRC 2 |
| [Set_CSW_Update_Limit](5_DAO/SRC/DAO_Main.py#L8285) | `ENABLE_CSW_UPDATE_LIMIT` 값에 따라 `now_enable_CSW_update_limit`와 `CSW_update_limit_value` 두 속성을 세운다 | 뜻은 맞으나 호출이 한 겹 감싸여 있어 찾기 어렵다 | 이름 유지, 호출을 직접 연결 | SRC 2 |
| [Is_Current_LLR_Valid](5_DAO/SRC/DAO_Main.py#L2474) | 검사만 하지 않고 `Validate_LLR_Matrix()`를 불러 상태를 바꾸고 실패 로그까지 남긴다 | `Is_`는 부작용 없는 질의를 연상시킨다 | `Check_And_Log_Current_LLR_Validity` | SRC 2 |
| [Update_Configs](5_DAO/SRC/DAO_Main.py#L475) | 설정에서 파생되는 값을 다시 계산한다 | `Update_Optimal_LLR`(상태 저장)과 접두사가 같아 뜻이 갈린다 | `Recalculate_Derived_Configs` | SRC 2, 문서 11 |
| [Print_Configs](5_DAO/SRC/DAO_Main.py#L7270) | `Print_Config`을 목록에 대해 반복하는 것과 본문이 똑같다 | 두 이름이 한 글자 차이라 호출자가 어느 쪽인지 눈으로 구분하기 어렵다 | `Print_Config_Group` | SRC 2 |
| `십시일반` (주석 용어, [L2865](5_DAO/SRC/DAO_Main.py#L2865) 등 5곳) | donor 그룹들에서 iteration을 조금씩 걷어 새 그룹에 준다 | 코드 주석의 비유 표현이라 처음 읽는 사람이 무엇을 하는지 모른다 | 주석을 "donor 그룹에서 iteration 나눠 걷기"로 바꾼다 | 주석 5곳 |

**처방 (우선순위 상, 위험 없음, 손대는 자리 2곳)**: `Mutate_Matrix_Setup`을 없애고 [Gen_LLR_Mutate_Matrix:L3785](5_DAO/SRC/DAO_Main.py#L3785)가 `self.Set_CSW_Update_Limit()`을 직접 부르게 한다. Round 1 실마리 ㉶은 "`Set_CSW_Update_Limit`을 부르는 자리가 보이지 않는다"였는데, 실제로는 이 한 줄짜리 껍데기를 거쳐 [L7098](5_DAO/SRC/DAO_Main.py#L7098)에서 불린다. 껍데기가 grep 한 번에 안 잡히는 원인이므로, 없애면 실마리 자체가 사라진다.

---

## R4. 설정 계층과 설정 값이 확정되는 시점

### R4-1. 설정 값이 지나는 네 단계

```
㉮ import 시점        DAO_Config.py 클래스 본문 (조건문 포함)
㉯ argv 반영          Set_Configs_Manually()   (SIM_IDX 아홉 갈래)
㉰ 파생 재계산        Update_Configs()  =  Update_RefC_Configs
                                        → Update_Insert_Group_Configs
                                        → Update_Path_Configs
                                        → Update_Exit_After_Run_Configs
㉱ 실행 중 변경       없음 (LLR_OPT는 설정 클래스를 읽기만 한다)
```

㉮, ㉯, ㉰은 [DAO_Main.py:10420-10427](5_DAO/SRC/DAO_Main.py#L10420)의 `__main__` 블록에서 이 순서로 정확히 한 번씩 돈다.

### R4-2. 설정 값의 정본 위치 표 (필수 산출물 ㉰)

"정본 위치"는 그 값의 최종 결정권을 가진 자리다. 읽는 사람이 값을 바꾸려면 그 자리를 고쳐야 한다.

| 설정 | 기본값 자리 | 덮어쓰는 자리 | 최종 확정 시점 | 읽는 사람이 헷갈리는 점 |
|------|-----------|-------------|--------------|----------------------|
| `DAO_CONFIG.INITIAL_MATRIX_IDX` | [DAO_Config.py:121](5_DAO/SRC/DAO_Config.py#L121) | `Set_Configs_Manually` 아홉 갈래 전부 | ㉯ | argv 없이 실행하면 999가 그대로 쓰인다 |
| `DAO_CONFIG.Gen_LLR_Mode_SEQUENCE` | [DAO_Config.py:133](5_DAO/SRC/DAO_Config.py#L133) | `Set_Configs_Manually`의 10, 20, 30만 | ㉯ | 11, 12, 21, 22, 31, 32 갈래는 기본값 12개 모드를 그대로 쓴다 |
| `DAO_CONFIG.IS_HBF_OPT` | [DAO_Config.py:127](5_DAO/SRC/DAO_Config.py#L127) `False` | [HBF_OPT_CONFIG.__init__:369](5_DAO/SRC/DAO_Config.py#L369)이 True로, [Update_RefC_Configs:440](5_DAO/SRC/DAO_Main.py#L440)이 False로 | ㉰ | **아래 R4-3 참고. 실제로는 항상 False다** |
| `REFC_CONFIG.NUM_TARGET_CHANNELS` | [DAO_Config.py:191](5_DAO/SRC/DAO_Config.py#L191) `0` | [Update_RefC_Configs:420-434](5_DAO/SRC/DAO_Main.py#L420) | ㉰ | 기본값 0은 절대 쓰이지 않는 자리 표시용이다 |
| `REFC_CONFIG.RBERs` / `num_fixed_errs` / `fixed_SCRs` / `fixed_SERs` / `fixed_erasure_ratios` | [DAO_Config.py:173-177](5_DAO/SRC/DAO_Config.py#L173) | `Set_Configs_Manually`가 값을, `Update_RefC_Configs`가 `ch_type`에 따라 쓰지 않는 쪽을 0으로 다시 채운다 | ㉰ | `ch_type`이 어떤 배열을 살리고 어떤 배열을 0으로 덮는지가 `Update_RefC_Configs` 안에만 있다 |
| `UNCOR_CONFIG.LOAD_UNCOR_MODE` | [DAO_Config.py:215](5_DAO/SRC/DAO_Config.py#L215) `DEFAULT` | [Update_Exit_After_Run_Configs:405-416](5_DAO/SRC/DAO_Main.py#L405) | ㉰ (마지막 단계) | **아래 R4-4 참고. 같은 `Update_Configs` 안에서 이 값을 먼저 읽는 자리가 있다** |
| `UNCOR_CONFIG.NUM_LINES_PER_UNCOR`, `LEN_NO_PS` | [DAO_Config.py:211,214](5_DAO/SRC/DAO_Config.py#L211) | [Update_RefC_Configs:442-447](5_DAO/SRC/DAO_Main.py#L442) | ㉰ | 조건이 `LOAD_UNCOR_MODE == LOAD_VECTOR`인데 그 값이 아직 안 정해진 시점에 검사한다 |
| `MUTATE_CONFIG.CSW_UPDATE_LIMIT_VALUE` | [DAO_Config.py:251-252](5_DAO/SRC/DAO_Config.py#L251) | 없음 | ㉮ | `ENABLE_CSW_UPDATE_LIMIT`이 False면 **속성 자체가 만들어지지 않는다** |
| `DEBUG_CONFIG`의 7개 토글 | [DAO_Config.py:329-345](5_DAO/SRC/DAO_Config.py#L329) if/else 두 벌 | 없음 | ㉮ | 같은 이름이 두 벌 적혀 있어 어느 쪽이 현재 값인지 `ENABLE_DEBUG_MODE`를 거슬러 읽어야 안다 |
| `DEBUG_CONFIG.RANDOM_STATE_TO_SET` | [DAO_Config.py:349-354](5_DAO/SRC/DAO_Config.py#L349) if/else | 없음 | ㉮ | 같음 |
| `INSERT_RANDOM_GROUP_CONFIG.ENABLE_INSERT_RESTART`, `INSERT_MUTATED_GROUP_CONFIG.ENABLE_INSERT_RESTART` | [DAO_Config.py:258-261, 271-274](5_DAO/SRC/DAO_Config.py#L258) 클래스 본문의 `if REFC_CONFIG.init_n == 1` | [Update_Insert_Group_Configs:469-473](5_DAO/SRC/DAO_Main.py#L469) | ㉰ | 클래스 본문의 조건문은 import 시점 `init_n` 기본값(1)으로 돌고, 나중에 통째로 덮인다. **두 자리 중 정본은 `Update_Insert_Group_Configs` 한 곳뿐인데 클래스 본문이 같은 규칙을 한 번 더 적고 있다** |
| `SPEED_TEST_REFC_CONFIG.str_matrix_name` | 상속 | [Update_RefC_Configs:448](5_DAO/SRC/DAO_Main.py#L448)이 손으로 한 필드만 복사 | ㉰ | 아래 R4-5 참고 |
| `PATH_CONFIG`의 13개 경로 | [DAO_Config.py:442-457](5_DAO/SRC/DAO_Config.py#L442) 빈 문자열 | [Update_Path_Configs:450-467](5_DAO/SRC/DAO_Main.py#L450) | ㉰ | 빈 문자열 기본값은 자리 표시용이며 실제 경로는 전부 ㉰에서 정해진다 |
| `TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS` | [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323) 다른 두 상수의 곱 | 없음 | ㉮ | 식이 값 자리에 있어 실제 숫자(1200)를 계산해 봐야 안다 |

**처방 (우선순위 중, 위험 없음, 손대는 자리 4곳)**: 클래스 본문 안 조건 분기 네 자리(`INSERT_RANDOM_GROUP_CONFIG`, `INSERT_MUTATED_GROUP_CONFIG`, `MUTATE_CONFIG.CSW_UPDATE_LIMIT_VALUE`, `DEBUG_CONFIG`)를 값 하나로 펴고, 파생 규칙은 `Update_*_Configs`에만 둔다. 구체적으로는 ㉠ 두 `ENABLE_INSERT_RESTART`를 `ENABLE_INSERT_RESTART: bool = False` 한 줄로 바꾸고 계산은 `Update_Insert_Group_Configs`에 맡긴다 ㉡ `CSW_UPDATE_LIMIT_VALUE = 128`을 조건 밖으로 꺼내 항상 정의되게 한다 ㉢ `DEBUG_CONFIG`는 토글 7개를 한 벌만 적고, `ENABLE_DEBUG_MODE`가 참일 때 값을 바꾸는 `Update_Debug_Configs()`를 만들어 `Update_Configs`에 넣는다.

**처방 (우선순위 중, 위험 없음, 손대는 자리 1곳)**: `TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS`의 주석 "1시간 이상이면 타임아웃 없음과 동일"은 실제 값(1200초)과 다른 이야기를 한다. 값 옆에 `# = 1200초` 를 적는다. (값 자체의 적정성은 팀 M의 실마리 ㉲ 소관이다.)

### R4-3. `HBF_OPT_CONFIG.__init__`의 부수효과가 절대 실행되지 않는다 (실마리 ㉷ 확인 결과)

[HBF_OPT_CONFIG](5_DAO/SRC/DAO_Config.py#L366)는 `__init__`에서 `DAO_CONFIG.IS_HBF_OPT`를 바꾼다. 그런데 이 클래스를 인스턴스로 만드는 자리가 저장소 전체에 없다. 확인한 `HBF_OPT_CONFIG` 사용처 8곳은 전부 클래스 속성 직접 접근(`HBF_OPT_CONFIG.HBF_MAX_ITERATION` 등)이다. `CONFIGS` 목록([DAO_Config.py:415](5_DAO/SRC/DAO_Config.py#L415))에도 클래스 자체로 들어가 있어 인스턴스가 만들어지지 않는다.

`IS_HBF_OPT`를 True로 만드는 자리는 이 `__init__` 한 곳뿐이므로, **현재 코드에서 `DAO_CONFIG.IS_HBF_OPT`는 항상 False**다. 그 결과 `Gen_LLR_Mode_HBF_SEQUENCE`(실마리 ㉯)와 `HBF_immutable_col_range` 분기([L7066](5_DAO/SRC/DAO_Main.py#L7066)), HBF 모드 시드 분기([L8507](5_DAO/SRC/DAO_Main.py#L8507))도 실행되지 않는다.

- **처방 (우선순위 상, 위험 있음, 동작 변경, 손대는 자리 3곳)**: 생성자 부수효과를 없애고 `Update_RefC_Configs` 안에 `DAO_CONFIG.IS_HBF_OPT = (REFC_CONFIG.init_n == 1)` 한 줄로 옮긴다. 이렇게 하면 init_n=1일 때 HBF 경로가 **처음으로 켜진다**. 의도된 동작인지 사용자 확인이 필요하다(Decision 등급). 켜는 것이 의도가 아니라면 `IS_HBF_OPT`와 관련 분기를 통째로 걷어내는 쪽이 읽기 쉬워진다
- 옆 세션 충돌: `DAO_LLR_MATRIX.py`의 `is_HBF_OPT` 검사([DAO_LLR_MATRIX.py:377](5_DAO/SRC/DAO_LLR_MATRIX.py#L377), [443](5_DAO/SRC/DAO_LLR_MATRIX.py#L443))가 살아나므로, 유효성 규칙을 넓히고 있는 SW 분기 작업과 같은 파일을 건드린다. **SW 분기 작업이 끝난 뒤에 손대는 것을 권한다**
- 팀 L에 넘길 것: 이 항목은 실마리 ㉷와 ㉯의 뿌리다. 결함 여부 판정은 팀 L(P12)이 맡는 것이 맞다

### R4-4. `Update_Configs` 안의 순서 때문에 LOAD_VECTOR 파생값이 계산되지 않는다

[Update_Configs](5_DAO/SRC/DAO_Main.py#L475)는 `Update_RefC_Configs` → `Update_Insert_Group_Configs` → `Update_Path_Configs` → `Update_Exit_After_Run_Configs` 순서로 돈다. 그런데

- ㉠ `UNCOR_CONFIG.LOAD_UNCOR_MODE`를 **정하는** 자리는 마지막 `Update_Exit_After_Run_Configs`([L405-416](5_DAO/SRC/DAO_Main.py#L405))다
- ㉡ 그 값을 **읽는** 자리는 첫 번째 `Update_RefC_Configs`([L442](5_DAO/SRC/DAO_Main.py#L442))의 `if UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_VECTOR:` 다
- ㉢ `Update_Configs`는 `__main__`에서 한 번만 불린다([DAO_Main.py:10427](5_DAO/SRC/DAO_Main.py#L10427) 확인. 저장소 전체에서 정의 1곳과 호출 1곳뿐이다)

따라서 `UNCOR_CONFIG.ENABLE_LOAD_VECTOR = True`로 두어도 ㉡의 조건은 기본값 `DEFAULT`와 비교되어 거짓이 되고, `LEN_NO_PS`는 0, `NUM_LINES_PER_UNCOR`는 1로 남는다. 이 두 값은 uncor 파일을 몇 줄씩 끊어 나눌지 계산하는 데 쓰이므로([L1042](5_DAO/SRC/DAO_Main.py#L1042), [L1567-1580](5_DAO/SRC/DAO_Main.py#L1567), [L7420](5_DAO/SRC/DAO_Main.py#L7420)) LOAD_VECTOR 경로가 어긋난다.

- **처방 (우선순위 상, 위험 있음, 동작 변경, 손대는 자리 1곳)**: `Update_Configs`의 호출 순서를 `Update_Exit_After_Run_Configs` → `Update_RefC_Configs` → `Update_Insert_Group_Configs` → `Update_Path_Configs`로 바꾼다. `Update_Exit_After_Run_Configs`는 `DAO_CONFIG.RUN_DAO_MODE`와 `UNCOR_CONFIG.ENABLE_LOAD_VECTOR`만 읽으므로 앞으로 옮겨도 입력이 부족해지지 않는다
- **함께 할 처방 (우선순위 중, 위험 없음)**: 각 `Update_*_Configs` 함수 docstring 첫 줄에 "읽는 설정"과 "쓰는 설정"을 적는다. 이 순서 문제가 눈에 보이게 된다
- 팀 L에 넘길 것: 동작 결함이므로 P12 관점에서 심각도를 매겨야 한다

### R4-5. `SPEED_TEST_REFC_CONFIG` 상속은 읽는 사람이 두 클래스를 대조해야 한다

[SPEED_TEST_REFC_CONFIG(REFC_CONFIG)](5_DAO/SRC/DAO_Config.py#L218)는 필드를 세 갈래로 다룬다.

| 갈래 | 필드 | 뜻 |
|------|------|-----|
| 자기가 다시 정한 것 (9개) | `fn`, `max_num_test`, `ch_type`, `RBERs`, `num_fixed_errs`, `fixed_SCRs`, `fixed_SERs`, `mode_seed`, `mode_init_seed` | 속도 측정용 값 |
| 손으로 복사하는 것 (1개) | `str_matrix_name` | [Update_RefC_Configs:448](5_DAO/SRC/DAO_Main.py#L448)에서 대입 |
| 조용히 물려받는 것 (12개) | `ECC_VER`, `matrix_sel`, `init_n`, `fixed_erasure_ratios`, `mode_all_one_cw`, `CRC_Option_F_P`, `mode_iter`, `mode_scenario`, `LLR_matrix_idx`, `CRC_skip_mode`, `HighDV_skip_mode`, `NUM_TARGET_CHANNELS`, `MAX_DECODING_ITERATION` | 부모가 ㉯, ㉰에서 바뀌면 같이 바뀐다 |

한 필드가 어느 갈래인지 알려면 두 클래스 본문을 나란히 놓고 대조해야 한다. `str_matrix_name` 한 줄만 손으로 복사하는 것이 그 증거다.

- **처방 (우선순위 중, 위험 없음, 손대는 자리 1곳 + 34곳 재확인)**: 상속을 끊고 독립 클래스로 만든 뒤, 부모를 따라가야 하는 12개는 `Update_Speed_Test_Configs()`에서 한 줄씩 대입한다. `SPEED_TEST_REFC_CONFIG` 참조는 `DAO_Main.py`에 34곳 있지만 전부 읽기이므로 이름은 그대로 두면 되고, 새 `Update_` 함수 하나를 `Update_Configs`에 추가하면 된다
- 낮은 비용 대안 (우선순위 하): 상속은 그대로 두고 클래스 docstring에 위 세 갈래 표를 적는다

### R4-6. `CONFIGS` 목록 누락 (실마리 ㉷ 확인 결과)

`DAO_Config.py`의 설정 클래스는 22개인데 [CONFIGS](5_DAO/SRC/DAO_Config.py#L406)에는 19개만 들어 있다. 빠진 것은 `SPEED_TEST_REFC_CONFIG`, `ADJUST_ITERATION_CONFIG`, `PATH_CONFIG` 셋이다. `CONFIGS`는 [Print_Configs(CONFIGS)](5_DAO/SRC/DAO_Main.py#L7208) 한 곳에서만 쓰이므로, 결과는 **세션 로그에 속도 테스트 설정, iteration 전달 비율, 경로가 기록되지 않는 것**이다. 실행 결과를 나중에 재현하거나 확인할 때 이 세 가지를 로그에서 찾을 수 없다.

주의할 점이 하나 있다. `Print_Config`은 `vars(config_class)`를 쓰므로 상속받은 필드는 찍지 않는다. `SPEED_TEST_REFC_CONFIG`를 목록에 넣어도 위 R4-5의 "조용히 물려받는 12개"는 여전히 로그에 남지 않는다.

- **처방 (우선순위 중, 위험 없음, 손대는 자리 1곳)**: `CONFIGS`에 세 클래스를 추가한다
- **함께 할 처방 (우선순위 중, 위험 없음, 손대는 자리 1곳)**: `Print_Config`이 `vars(cls)` 대신 MRO를 거슬러 모으도록 바꾸거나, R4-5의 상속 끊기를 먼저 한다

---

## R5. 인스턴스 상태의 생성 위치

`LLR_OPT`가 가진 `self` 속성은 113개이고, 그중 92개는 [__init__:L482-570](5_DAO/SRC/DAO_Main.py#L482) 또는 [_init_per_matrix_state:L572-628](5_DAO/SRC/DAO_Main.py#L572)에서 만들어진다. 나머지 21개는 아래와 같이 다른 메서드에서 처음 생긴다.

### R5-1. `__init__` 밖에서 생기는 속성 전수 (필수 산출물 ㉯)

| 속성 | 만들어지는 자리 | 읽는 자리 | 순서 위험 |
|------|---------------|----------|----------|
| `current_target_idx` | [Initialize_Stage:L2278, 2280, 2291](5_DAO/SRC/DAO_Main.py#L2278) (`hasattr` 검사) | 같은 함수 L2277, 2287, 2296 / [Init_Reorder_Group_Mode:L4516](5_DAO/SRC/DAO_Main.py#L4516) 로그 | **없음.** `Init_Reorder_Group_Mode`는 같은 함수 L2299-2302의 `getattr` 디스패치로만 불리고, 그 자리는 L2278보다 뒤다 (실마리 ㉵ 해소) |
| `now_enable_CSW_update_limit` | [Set_CSW_Update_Limit:L8287, 8290](5_DAO/SRC/DAO_Main.py#L8287) | [Generate_Random_Mutation:L7053](5_DAO/SRC/DAO_Main.py#L7053) | **없음.** [Gen_LLR_Mutate_Matrix:L3785](5_DAO/SRC/DAO_Main.py#L3785)가 `Mutate_Matrix_Setup()`(= `Set_CSW_Update_Limit`)을 부른 바로 다음 줄에서 `Generate_Random_Mutation`을 부른다 (실마리 ㉶ 해소) |
| `CSW_update_limit_value` | [Set_CSW_Update_Limit:L8288, 8291](5_DAO/SRC/DAO_Main.py#L8288) | [Get_Mutate_Matrix_Skip_Row_Idx:L4242](5_DAO/SRC/DAO_Main.py#L4242) | **없음.** 위와 같은 경로이고, 게다가 `now_enable_CSW_update_limit`이 참일 때만 불린다 |
| `src_backup_dir` | [Make_Dirs:L6593](5_DAO/SRC/DAO_Main.py#L6593) | 같은 함수 L6605, [BACKUP_SRC:L8806, 8809](5_DAO/SRC/DAO_Main.py#L8806) | **없음.** [Set_Work_Space:L8787-8789](5_DAO/SRC/DAO_Main.py#L8787)가 `Make_Dirs` 다음에 `BACKUP_SRC`를 부른다 |
| `is_current_LLR_valid` | [Is_Current_LLR_Valid:L2488](5_DAO/SRC/DAO_Main.py#L2488), [Validate_LLR_Matrix:L9907, 9911](5_DAO/SRC/DAO_Main.py#L9907) | [Initialize_LLR_Matrix:L2340](5_DAO/SRC/DAO_Main.py#L2340), `Is_Current_LLR_Valid:L2490` | **없음.** 두 읽기 모두 바로 앞줄에서 `Validate_LLR_Matrix()`를 부른다 |
| `loop_start_time` | [Set_Loop_Start_Time:L8929](5_DAO/SRC/DAO_Main.py#L8929) (root만) | [Calc_Loop_Elapsed_Time:L8932](5_DAO/SRC/DAO_Main.py#L8932) | **있음 (낮음).** 아래 R5-2 |
| `loop_elapsed_time`, `total_elapsed_time`, `loop_end_time` | [Calc_Loop_Elapsed_Time:L8932-8934](5_DAO/SRC/DAO_Main.py#L8932) | [Print_Test_Result:L7601, 7607, 7612](5_DAO/SRC/DAO_Main.py#L7601) | **있음 (낮음).** 같은 함수 L7560이 `Calc_Loop_Elapsed_Time()`을 먼저 부르지만 그 안이 `loop_start_time`에 기댄다 |
| `loop_end_time_stamp` | [Calc_Loop_Elapsed_Time:L8935](5_DAO/SRC/DAO_Main.py#L8935) | **없음 (죽은 속성)** | 해당 없음 |
| `start_time_str` | [Initialize_Log:L2241](5_DAO/SRC/DAO_Main.py#L2241) (root만) | **없음 (죽은 속성)** | 해당 없음 |
| `gen_DV_idx`, `previous_dv_segment` | [Gen_LLR_Regen_DV:L3959-3976, L4017](5_DAO/SRC/DAO_Main.py#L3959) | 같은 함수 L3963-3983, L3998 | **없음.** `current_trial_idx == 1` 가지에서 먼저 만들어진다 |
| `gen_row_idx`, `previous_gen_row` | [Gen_LLR_Regen_Row:L4097-4114, L4156](5_DAO/SRC/DAO_Main.py#L4097) | 같은 함수 L4101-4131 | **없음.** 위와 같은 구조 |
| `is_mutate_matrix_tuning_phase`, `tuning_mutation_count` | [Gen_LLR_Mutate_Matrix:L3753-3778](5_DAO/SRC/DAO_Main.py#L3753) | 같은 함수 L3756, 3780-3783 | **없음.** `current_trial_idx == 1` 가지에서 먼저 만들어진다 |
| `tuning_mutations`, `max_possible_tuning_mutation_count` | [Gen_LLR_Mutate_Matrix:L3771-3774](5_DAO/SRC/DAO_Main.py#L3771) | 같은 함수 L3759, 3775, 3782-3783 | **없음.** `is_mutate_matrix_tuning_phase`가 참으로 바뀌는 같은 블록에서 만들어진다 |
| `prev_generated_mutation` | [Gen_LLR_Mutate_Matrix:L3788](5_DAO/SRC/DAO_Main.py#L3788) (`current_mutation`이 비지 않을 때만) | 같은 함수 L3771, 3773 | **있음 (낮음).** 아래 R5-3 |
| `_gen_single_row_stop_idx` | [Run_Single_Row_Generation:L10050, 10059](5_DAO/SRC/DAO_Main.py#L10050) | 같은 함수 L10058-10064 | **없음.** 같은 함수 안에서 만들고 읽는다 |

정리하면 **순서가 실제로 깨질 수 있는 자리는 3개**이고(`loop_*` 묶음 하나, `prev_generated_mutation` 하나), Round 1 실마리 ㉵과 ㉶는 확인 결과 순서 위험이 아니다. 다만 둘 다 "속성이 어디서 생기는지 찾기 어렵다"는 원래 문제는 그대로다.

### R5-2. `loop_start_time` 순서 위험 (우선순위 중)

[Test_LLR:L8961-8992](5_DAO/SRC/DAO_Main.py#L8961)의 채널 루프는 이렇게 돈다.

```
Set_Test_Environment()        # is_test_end = False (L8473)
while not self.is_test_end:
    Read_Run_ECC_End_Flag()   # 파일을 읽어 is_test_end를 다시 정한다 (L1103)
    if self.is_test_end: break   # <-- Set_Loop_Start_Time 전에 빠져나간다
    Set_Loop_Start_Time()     # 여기서 loop_start_time이 처음 생긴다
    ...
Print_Test_Result(..., is_test_end=True)   # L8992, 무조건 실행
  └ Calc_Loop_Elapsed_Time()  # L7560 → self.loop_start_time 읽기
```

`Initialize_Run_ECC_End_Flag()`와 `MPI_Barrier()`가 앞에 있어 플래그 파일은 보통 "0"이므로 while 본문이 최소 한 번은 돈다. 그러나 플래그 파일 쓰기가 실패했거나 외부에서 "1"이 남은 상황에서는 첫 읽기에서 바로 break 하고, root가 `Print_Test_Result` 안에서 `AttributeError: loop_start_time`으로 죽는다.

같은 함수가 이 불안을 스스로 드러낸다. [L7601](5_DAO/SRC/DAO_Main.py#L7601)은 `if self.loop_elapsed_time is not None:`으로, [L7607](5_DAO/SRC/DAO_Main.py#L7607)은 `if hasattr(self, 'total_elapsed_time'):`으로 같은 성격의 속성을 서로 다른 방식으로 방어한다. 게다가 `loop_elapsed_time`은 None이 되는 경로가 없으므로 앞쪽 검사는 아무것도 막지 못한다.

- **처방 (우선순위 중, 위험 없음, 손대는 자리 5곳)**: `loop_start_time`, `loop_elapsed_time`, `total_elapsed_time`, `loop_end_time`을 `__init__`에 `0.0`과 `None`으로 선언하고, `Print_Test_Result`의 두 방어 검사를 지운다. 죽은 `loop_end_time_stamp`는 함께 지운다

### R5-3. `prev_generated_mutation` 순서 위험 (우선순위 하)

[Gen_LLR_Mutate_Matrix:L3788](5_DAO/SRC/DAO_Main.py#L3788)은 `if current_mutation:` 안에서만 `prev_generated_mutation`을 만든다. `Generate_Random_Mutation`은 `MUTATION_RANGE == 0`이거나 후보 원소가 없으면 빈 목록을 돌려주므로([L7075-7083](5_DAO/SRC/DAO_Main.py#L7075)) 속성이 만들어지지 않을 수 있다. 그 다음 trial에서 `is_previous_trial_updated`가 참이면 [L3771](5_DAO/SRC/DAO_Main.py#L3771)이 없는 속성을 읽는다. 변이가 비었으면 매트릭스가 그대로라 갱신 판정이 참이 되기는 어려우므로 실제 발생 가능성은 낮다.

- **처방 (우선순위 하, 위험 없음, 손대는 자리 1곳)**: `_init_per_matrix_state`에 `self.prev_generated_mutation: list = []`를 추가한다

### R5-4. 죽은 속성 5개 (우선순위 중)

읽는 자리가 한 곳도 없는 속성이다. 사람이 코드를 읽을 때 "이 값이 어디에 쓰이나" 하고 따라가다 헛걸음하게 만든다.

| 속성 | 생성 | 대입 |
|------|------|------|
| `total_raw_FERs` | [L598](5_DAO/SRC/DAO_Main.py#L598) | [L1912](5_DAO/SRC/DAO_Main.py#L1912) |
| `total_seed_FERs` | [L599](5_DAO/SRC/DAO_Main.py#L599) | [L1900](5_DAO/SRC/DAO_Main.py#L1900) |
| `total_num_iterations` | [L590](5_DAO/SRC/DAO_Main.py#L590) | [L1890](5_DAO/SRC/DAO_Main.py#L1890) |
| `loop_end_time_stamp` | 없음 | [L8935](5_DAO/SRC/DAO_Main.py#L8935) |
| `start_time_str` | 없음 | [L2241](5_DAO/SRC/DAO_Main.py#L2241) |

- **처방 (우선순위 중, 위험 없음, 손대는 자리 8곳)**: 다섯 속성을 지운다. 지우면 `Gather_Ref_C_Results`의 `is_load_seed_mode` 분기가 4줄 짧아지고, `Calc_Loop_Elapsed_Time`과 `Initialize_Log`도 짧아진다

### R5-5. 속성이 생기는 층을 문서로 못 박기 (우선순위 상)

현재 초기화는 네 층으로 나뉘는데(`__init__`, `_init_per_matrix_state`, `Initialize_Stage`, `Initialize_Trial`), 어떤 속성이 어느 층에 속하는지는 `_init_per_matrix_state`의 docstring 두 줄이 전부다.

- **처방 (우선순위 상, 위험 없음, 손대는 자리 1곳)**: `LLR_OPT` 클래스 docstring(현재 없음)을 만들어 아래 네 줄짜리 수명 표를 적는다. 옆 세션이 매트릭스 모델에 필드를 더할 때도 "이 값은 어느 층에서 리셋되어야 하나"를 바로 판단할 수 있다

| 수명 | 층 | 대표 속성 |
|------|----|----------|
| 세션 전체 | `__init__` | `session_dir`, `excluded_cores`, `pool_has_uncor`, `base_seed`, 로그 경로 |
| 매트릭스 1개 | `_init_per_matrix_state` | `initial/current/optimal/temp_optimal_LLR_matrix`, `total_num_*`, `current_test_mode` |
| stage 1개 | `Initialize_Stage` | `current_stage_idx`, `temp_optimal_LLR_matrix`, `current_target_idx`, 모드별 state |
| trial 1개 | `Initialize_Trial` | `current_trial_idx`, `current_LLR_matrix_idx` |

---

## R6. 함수 길이, 중첩 깊이, 반복 관용구

### R6-1. 300줄 넘는 함수 (2개)와 그 아래 긴 함수 (필수 산출물 ㉱)

현재 파일 기준으로 300줄을 넘는 함수는 둘뿐이다. 함께 다룰 만한 120줄 이상 함수를 아래에 이어 적는다.

| 함수 | 줄 수 | 최대 중첩 | 내부 구획 (주석 띠 기준) | 쪼갤 경계와 새 함수 이름 |
|------|------|----------|------------------------|----------------------|
| [Gen_LLR_Insert_Mutated_Group:L2792](5_DAO/SRC/DAO_Main.py#L2792) | 344 | 4단 | 번호 주석 10개 (1 삽입 위치, 2 소스 그룹 선택, 3 그룹 생성, 3-1 iteration 동적 계산, 3-2 donor 조정, 3-3 restart 추가, 4 복사, 5 mutation, 6 뒷 그룹 재계산, 7 삽입과 header, 8 restart_groups 보정, 9 max_iteration, 10 target_group_indices) | ㉠ 3-1 전체(L2858-2968, 111줄)를 `Borrow_Iterations_From_Donor_Groups(matrix, requested_iteration) -> tuple[int, list[tuple[int,int]]]`로 뽑는다. 이 덩어리는 새 그룹을 전혀 모르고 iteration 숫자만 다룬다 ㉡ 7 + 8 + 9(L3063-3098)를 `Insert_Group_And_Fix_Header(matrix, insert_pos, new_groups)`로 뽑는다 ㉢ 10(L3120-3135)을 `Shift_Target_Group_Numbers_After_Insert(insert_pos, num_inserted)`로 뽑는다. **㉡과 ㉢은 [Gen_LLR_Insert_Random_Group](5_DAO/SRC/DAO_Main.py#L2585)의 4, 5, 6, 7번 구획과 같은 일을 하므로 두 함수가 함께 쓴다** |
| [Build_Reordered_Matrix:L4849](5_DAO/SRC/DAO_Main.py#L4849) | 312 | 7단 | `========== N. ==========` 띠 3개 (1 그룹 재배열, 1-1 restart 생성과 삽입, 2 iteration 재계산, 3 header 갱신) + iteration 재계산 안이 다시 "Position별 테스트"(L5012-5070)와 "Final verification"(L5072-5106) 두 갈래 | ㉠ 1과 1-1(L4892-4972)을 `Arrange_Groups_For_Reorder(group_order, is_position_test, candidate_restart_flag) -> tuple[list, int]`로 뽑는다 ㉡ 2의 두 갈래를 각각 `Assign_Iterations_For_Position_Test(...)`와 `Assign_Iterations_For_Final_Verification(...)`으로 나눈다. 지금은 한 `if/else` 안에 60줄씩 들어 있어 7단 중첩의 원인이다 ㉢ 3(L5107-5160)을 `Rebuild_Header_After_Reorder(matrix, new_groups)`로 뽑는다 |
| [Validate_Config:L9647](5_DAO/SRC/DAO_Main.py#L9647) | 255 | 7단 | 검증 묶음 6개 (기본값, REGEN_DV, REGEN_ROW, REDECODE 대 Two-Stage, GEN_SINGLE_ROW, 모드별 MAX_TRIAL) | `errors: list[str]`를 받아 채우는 검사 함수 6개로 나눈다: `_Validate_Refc_Basics`, `_Validate_Regen_Fixed_Index(config, config_name, errors)`(아래 R6-4에서 DV와 ROW 공용), `_Validate_Run_Mode_Combinations`, `_Validate_Max_Trials`. 본문은 여섯 줄이 된다 |
| [Gen_LLR_Insert_Random_Group:L2585](5_DAO/SRC/DAO_Main.py#L2585) | 207 | 4단 | 번호 주석 7개 | 위 `Gen_LLR_Insert_Mutated_Group`의 ㉡, ㉢ 처방과 같은 함수를 쓴다 |
| [Run_Optimization:L8003](5_DAO/SRC/DAO_Main.py#L8003) | 186 | 7단 | 관심사 8개 (stage 루프, trial 루프, 생성 재시도, 멀티라운드 후처리, 시간 제한, 종료 플래그, 주기 속도 테스트, 연속 실패 판정) | ㉠ L8058-8088(시간 제한 + 종료 플래그 + 플래그 카운트 감소)을 `Decide_Forced_Termination(stage_start_time) -> tuple[bool, bool, bool, float]`로 뽑는다 ㉡ L8124-8145(주기 속도 테스트)를 `Run_Periodic_Speed_Test_If_Due(is_forced_termination)`로 뽑는다 ㉢ L8046-8056(멀티라운드 결과 수집과 동기화)을 `Collect_And_Sync_Multi_Round_State()`로 뽑는다. 세 덩어리를 빼면 본문이 90줄 아래로 내려가고 중첩도 5단이 된다 |
| [Set_Gen_Trial_LLR_Mode:L8293](5_DAO/SRC/DAO_Main.py#L8293) | 156 | 5단 | 관심사 4개 | ㉠ L8294-8327(모드 고르기 + 타겟 그룹 번호 정하기)을 `Select_Stage_Mode_And_Target()`으로 ㉡ L8329-8345(stage 건너뛰기 판정)를 `Should_Skip_This_Stage(selected_mode) -> bool`로 ㉢ L8346-8440(모드별 최대 trial 계산, elif 사슬 13갈래)을 `Calculate_Max_Modification_Trial(selected_mode) -> int`로 뽑는다. ㉢은 R2(모드 정보 분산) 관점과 맞닿으므로 그 워커의 결론과 맞춰야 한다 |
| [Print_Test_Summary:L7617](5_DAO/SRC/DAO_Main.py#L7617) | 154 | **10단 (파일 최대)** | 관심사 3개 (파일명 블록, Partial/Full 모드 루프, 채널별 5행 출력) | 아래 R6-2에서 따로 다룬다 |
| [Gather_Ref_C_Results:L1784](5_DAO/SRC/DAO_Main.py#L1784) | 155 | 4단 | 구획 3개 (루프 중 root 읽기, 테스트 종료 시 Reduce 합산, Array 변환과 저장) | ㉠ L1805-1838을 `_Read_Results_On_Root_During_Loop(ch_idx)`로 ㉡ L1839-1878을 `_Reduce_Results_At_Test_End(ch_idx)`로 ㉢ L1893-1938(partial/full 분기 저장)을 `_Store_Channel_Result(matrix, ch_idx, FER_value, avg_iteration, total_errors, total_tests)`로 뽑는다 |
| [Run_Single_Row_Generation:L10027](5_DAO/SRC/DAO_Main.py#L10027) | 165 | 5단 | 번호 주석 9개 | 번호 3~7(L10070-10165)이 후보 하나를 처리하는 한 덩어리이므로 `_Evaluate_One_Single_Row_Candidate(candidate_idx) -> Optional[dict]`로 뽑는다. 본문은 루프 골격만 남는다 |

### R6-2. `Print_Test_Summary`의 10단 중첩과 40줄 쌍둥이 블록 (우선순위 상)

[L7700-7741](5_DAO/SRC/DAO_Main.py#L7700)에서 지역 변수 20개를 `if is_partial:` 갈래와 `else:` 갈래에 각각 한 번씩, 합쳐 40줄로 대입한다. 두 갈래의 차이는 필드 이름에 `_partial`이 붙느냐뿐이다. 이 블록이 채널 루프와 모드 루프 안에 있어 파일 최대 중첩 10단이 나온다.

- **처방 (우선순위 상, 위험 있음, 손대는 자리 DAO_LLR_MATRIX 1곳 + DAO_Main 3곳)**: `LLR_MATRIX`에 측정 결과 한 벌을 돌려주는 접근자를 만든다

```
# DAO_LLR_MATRIX.py
@dataclass
class ChannelResult:
    FER: float
    avg_iteration: float
    num_errors: int
    num_tests: int

def Get_Channel_Result(self, ch_idx: int, is_partial: bool) -> ChannelResult:
    ...
```

  그러면 `Print_Test_Summary`의 40줄이 `init = matrix.Get_Channel_Result(ch_idx, is_partial)` 네 줄로 줄고, [Print_Test_Result:L7587-7593](5_DAO/SRC/DAO_Main.py#L7587)과 [Gather_Ref_C_Results:L1893-1938](5_DAO/SRC/DAO_Main.py#L1893)의 같은 분기도 같은 접근자를 쓴다. `_partial` 붙은 필드 접근이 현재 52곳인데 그중 30곳 남짓이 사라진다
- 옆 세션 충돌: **`DAO_LLR_MATRIX.py`를 건드리므로 SW 분기 확장 작업(매트릭스 모델에 분기 필드 추가)과 같은 파일이다.** 다만 손대는 곳이 FER 계열 필드 접근자이고 `LLR_Header`/`LLR_Row`가 아니므로 충돌 범위는 작다. 그래도 옆 세션이 먼저 커밋한 뒤 착수하는 것을 권한다

### R6-3. 반복 관용구 (필수 산출물 ㉲)

| 관용구 | 반복 횟수 | 나타나는 자리 | 묶어낼 함수 이름과 시그니처 |
|--------|---------|-------------|--------------------------|
| root가 정하고 `_safe_bcast`로 모든 rank에 맞추기 (`X = self._safe_bcast(X if self.is_root else None, "tag")`) | **43** (`_safe_bcast` 호출 46곳 중 43곳이 이 모양, `Run_Optimization` 한 함수 안에만 7곳) | [Run_Optimization:L8055, 8068, 8077, 8078, 8133, 8163, 8182](5_DAO/SRC/DAO_Main.py#L8055), `Gen_Trial_LLR` 6곳, `Rebuild_Partial_Pool` 5곳, `Update_Optimal_LLR` 4곳 등 | `def Decide_On_Root(self, decide: Callable[[], Any], tag: str, default: Any = None) -> Any:` 로 묶는다. 호출 쪽은 `is_time_exceeded = self.Decide_On_Root(lambda: ..., "Bcast_is_time_exceeded", default=False)` 한 줄이 된다. **주의**: root 전용 블록이 로그를 쓰거나 파일을 만드는 경우(`Read_Trial_End_Flag` 뒤의 카운트 감소 등)는 부작용이 람다 안으로 들어가므로 그대로 두고, 값 계산만 하는 자리부터 바꾼다 |
| root 전용 판정 앞뒤의 `if self.is_root: ... else: ...`로 기본값 채우기 | 위 43곳 가운데 14곳 | `Run_Optimization` L8061-8067, L8071-8076, L8129-8132 등 | 위 `Decide_On_Root`의 `default` 인자가 이 `else` 블록을 대신한다 |
| 멀티라운드 round 결과 갱신과 마무리 | **2벌이 87% 동일** (81줄 대 77줄에서 다른 줄 22줄, 그중 실질 차이는 후보 설명 문자열 4줄) | [Update_Delete_Row_Round_Result:L5647](5_DAO/SRC/DAO_Main.py#L5647) + [_Finalize_Delete_Row_Round:L5687](5_DAO/SRC/DAO_Main.py#L5687) 대 [Update_Insert_Restart_Group_Round_Result:L5941](5_DAO/SRC/DAO_Main.py#L5941) + [_Finalize_Insert_Restart_Group_Round:L5978](5_DAO/SRC/DAO_Main.py#L5978) | `def Update_Greedy_Round_Result(self, state, tested_matrix, describe_candidate: Callable[[Any], str]) -> None:` 와 `def Finalize_Greedy_Round(self, state, mode_name: str, rebuild_candidates: Callable[[LLR_MATRIX], list], candidate_word: str) -> None:` 두 개로 묶는다 |
| 멀티라운드 상태 dataclass | **2벌이 필드 구성 동일** | [DeleteRowState:L327](5_DAO/SRC/DAO_Main.py#L327)와 [InsertRestartGroupState:L381](5_DAO/SRC/DAO_Main.py#L381). 9개 필드 중 8개가 이름까지 같고, 다른 하나가 `deletable_rows` 대 `insertable_positions` | `@dataclass class GreedyRoundState:` 하나로 합치고 후보 목록 필드를 `candidates: list`로 통일한다. 두 모드는 `delete_row_state`, `insert_restart_group_state` 속성 이름으로만 구분된다 |
| `Validate_Config`의 REGEN 고정 인덱스 검사 | **2벌** (각 40줄 안팎, `REGEN_DV_CONFIG`/`REGEN_ROW_CONFIG`와 오류 문구의 접두사만 다름) | [L9690-9745](5_DAO/SRC/DAO_Main.py#L9690)와 [L9747-9787](5_DAO/SRC/DAO_Main.py#L9747) | `def _Validate_Regen_Fixed_Index(self, config, config_name: str, check_dv: bool, errors: list[str]) -> None:` 하나로 묶는다. `check_dv=True`일 때만 `FIXED_DV_IDX` 검사를 더한다 |
| 채널 수만큼 도는 FER 로그 출력 | **27** (`for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS)`), 그중 "`ch{ch_idx}({ch_param}) FER: ..., Avg_iter: ...`" 한 줄 짜리가 5곳 | [L4834](5_DAO/SRC/DAO_Main.py#L4834), [L5704](5_DAO/SRC/DAO_Main.py#L5704), [L5994](5_DAO/SRC/DAO_Main.py#L5994), [L9516](5_DAO/SRC/DAO_Main.py#L9516), [L9539](5_DAO/SRC/DAO_Main.py#L9539) | `def Write_Channel_FER_Lines(self, matrix: LLR_MATRIX, prefix: str, is_partial: bool = False) -> None:` 로 묶는다. R6-2의 `Get_Channel_Result`와 짝을 이룬다 |
| `Deep_Copy`에 인자를 손으로 적기 | 호출 **33곳 전부**가 인자를 적는다. 조합은 세 가지뿐이다: 세 인자 모두 True 10곳, raw와 seed만 True 9곳, raw와 seed를 False로 적기 14곳 | 세 인자 True는 [L8670, 8673, 8675, 8679, 8681, 8697, 8699, 8701](5_DAO/SRC/DAO_Main.py#L8670)과 [L9624, 9626](5_DAO/SRC/DAO_Main.py#L9624) | 조합이 셋뿐이므로 이름 붙은 갈래로 만든다. `def Copy_With_All_Results(self, matrix_idx=None)`, `def Copy_With_Full_Results_Only(self, matrix_idx=None)`, `def Copy_Structure_Only(self, matrix_idx=None)` 세 메서드를 `LLR_MATRIX`에 두고 `Deep_Copy`는 그 셋이 쓰는 내부 함수로 남긴다. 호출 쪽 33곳이 인자 없는 한 줄이 된다 |
| `Print_Config`과 `Print_Configs` | **2벌이 본문 동일** | [L7261-7268](5_DAO/SRC/DAO_Main.py#L7261)과 [L7270-7278](5_DAO/SRC/DAO_Main.py#L7270) | `Print_Configs`를 `for cls in config_classes: self.Print_Config(cls)` 두 줄로 줄인다 |
| [Print_Stage_Info](5_DAO/SRC/DAO_Main.py#L7220)의 모드별 `elif` 사슬 | 13갈래가 모두 `self.Print_Config(XXX_CONFIG)` 한 줄 | [L7236-7259](5_DAO/SRC/DAO_Main.py#L7236) | `MODE_CONFIG_CLASS: dict[int, type]` 표를 `DAO_Constants.py`에 두고 `cls = MODE_CONFIG_CLASS.get(mode)` 한 줄로 바꾼다. `MULTI_ROUND_INIT_FUNC`와 같은 방식이다 |

**Deep_Copy 주의**: 호출 33곳이 모두 인자를 손으로 적고 있으므로 기본값을 뒤집는 것만으로는 아무것도 줄지 않는다. 특히 `copy_partial_FER`를 적지 않은 9곳은 "Partial 결과를 버린다"를 생략으로 표현한 것이라서, 기본값을 True로 바꾸면 이 9곳의 동작이 조용히 뒤집힌다. 그래서 기본값 뒤집기 대신 위 표의 이름 붙은 세 갈래 메서드를 권한다. 우선순위 중, 위험 있음(잘못 고치면 동작 변경), 옆 세션 충돌 가능(`DAO_LLR_MATRIX.py`).

### R6-4. 중첩 깊이 상위 (우선순위 중)

| 함수 | 최대 중첩 | 가장 깊은 자리 | 펴는 방법 |
|------|----------|--------------|----------|
| [Print_Test_Summary](5_DAO/SRC/DAO_Main.py#L7617) | 10단 | [L7652](5_DAO/SRC/DAO_Main.py#L7652) | R6-2의 접근자 도입으로 2단이 줄고, 모드 루프 본문을 `_Print_One_Mode_Summary(mode_name, is_partial, ...)`로 빼면 3단이 더 준다 |
| [Update_Optimal_LLR](5_DAO/SRC/DAO_Main.py#L9548) | 8단 | [L9605](5_DAO/SRC/DAO_Main.py#L9605) | 판정 부분과 bcast 부분을 나눈다. bcast 4줄은 R6-3의 `Decide_On_Root`로 대체된다 |
| [_Setup_Uncor_Pool_For_Channel](5_DAO/SRC/DAO_Main.py#L7386) | 8단 | [L7445](5_DAO/SRC/DAO_Main.py#L7445) | root 전용 블록 전체를 `_Split_Uncor_File_Into_Pool(...)`로 빼면 `if self.is_root:` 한 겹이 사라진다 |
| [Build_Reordered_Matrix](5_DAO/SRC/DAO_Main.py#L4849) | 7단 | [L4963](5_DAO/SRC/DAO_Main.py#L4963) | R6-1의 ㉠, ㉡ 처방 |
| [Validate_Config](5_DAO/SRC/DAO_Main.py#L9647) | 7단 | [L9729](5_DAO/SRC/DAO_Main.py#L9729) | R6-3의 `_Validate_Regen_Fixed_Index` 묶기 + `initial_LLR_matrix is None`을 조기 반환으로 바꾸기 |
| [Run_Optimization](5_DAO/SRC/DAO_Main.py#L8003) | 7단 | [L8064](5_DAO/SRC/DAO_Main.py#L8064) | R6-1의 ㉠, ㉡, ㉢ 처방 |
| [Gather_CSW_Logs](5_DAO/SRC/DAO_Main.py#L1675) | 7단 | [L1760](5_DAO/SRC/DAO_Main.py#L1760) | 파일 순회 본문을 `_Merge_One_CSW_File(...)`로 뺀다 |

---

## 우선순위 요약

| 순위 | 항목 | 우선순위 | 위험 | 옆 세션 충돌 | 손대는 자리 |
|------|------|---------|------|-------------|-----------|
| 1 | R4-4 `Update_Configs` 호출 순서를 고쳐 LOAD_VECTOR 파생값이 계산되게 한다 | 상 | 동작 변경 | 없음 | 1곳 |
| 2 | R4-3 `HBF_OPT_CONFIG` 생성자 부수효과를 `Update_RefC_Configs`로 옮긴다 | 상 | 동작 변경 (Decision) | **있음** (`DAO_LLR_MATRIX.py` 검증 경로가 살아난다) | 3곳 |
| 3 | R6-2 `LLR_MATRIX.Get_Channel_Result` 접근자로 Partial/Full 쌍둥이 블록을 없앤다 | 상 | 없음 | **있음** (`DAO_LLR_MATRIX.py`) | 4곳 |
| 4 | R6-1 `Gen_LLR_Insert_Mutated_Group`(344줄)과 `Build_Reordered_Matrix`(312줄)를 구획대로 쪼갠다 | 상 | 없음 | 없음 | 2함수 + 새 함수 6개 |
| 5 | R3-2 `current_target_idx`를 로그 전용임이 드러나는 이름으로 바꾼다 | 상 | 없음 | 없음 | 19곳 |
| 6 | R5-5 `LLR_OPT` 클래스 docstring에 속성 수명 4층 표를 적는다 | 상 | 없음 | 없음 | 1곳 |
| 7 | R3-4 `Mutate_Matrix_Setup` 껍데기를 없앤다 | 상 | 없음 | 없음 | 2곳 |
| 8 | R6-3 멀티라운드 greedy 두 벌을 `GreedyRoundState` + 공용 함수 2개로 합친다 | 중 | 없음 | 없음 | 4함수 + dataclass 2개 |
| 9 | R6-3 `Decide_On_Root` 도우미로 root 판정 후 bcast 관용구 43곳을 줄인다 | 중 | 없음 (부작용 있는 자리는 제외) | 없음 | 43곳 중 30곳 남짓 |
| 10 | R5-2, R5-4 `loop_*` 4개를 `__init__`에 선언하고 죽은 속성 5개를 지운다 | 중 | 없음 | 없음 | 13곳 |
| 11 | R4-2 클래스 본문 조건 분기 4자리를 `Update_*_Configs`로 옮긴다 | 중 | 없음 | 없음 | 4곳 |
| 12 | R4-6 `CONFIGS`에 빠진 3클래스를 넣는다 | 중 | 없음 | 없음 | 1곳 |
| 13 | R4-5 `SPEED_TEST_REFC_CONFIG` 상속을 끊는다 | 중 | 없음 | 없음 | 1곳 + 34곳 확인 |
| 14 | R6-3 `Deep_Copy`를 이름 붙은 세 갈래 메서드로 감싼다 | 중 | 잘못 고치면 동작 변경 | **있음** (`DAO_LLR_MATRIX.py`) | 33곳 |
| 15 | R6-1 `Validate_Config`을 검사 함수 4개로 나눈다 | 중 | 없음 | 없음 | 1함수 |
| 16 | R3-1 `BACKUP_SRC` 이름을 규약에 맞춘다 | 중 | 없음 | 없음 | 2곳 |
| 17 | R3-3 `total_raw_FERs`, `total_seed_FERs`, `total_num_iterations`를 지운다 | 중 | 없음 | 없음 | 6곳 |
| 18 | R6-3 `Print_Configs` 본문을 `Print_Config` 반복으로 줄인다 | 하 | 없음 | 없음 | 1곳 |
| 19 | R5-3 `prev_generated_mutation`을 `_init_per_matrix_state`에 선언한다 | 하 | 없음 | 없음 | 1곳 |
| 20 | R3-1 `Finalize_Reorder_Round`에 `_` 접두사를 붙인다 | 하 | 없음 | 없음 | 3곳 |

## 다른 팀에 넘길 것

- ㉮ 팀 L(P12 설정 검증): R4-3(`IS_HBF_OPT`가 항상 False라 HBF 경로 전체가 죽어 있다)과 R4-4(`Update_Configs` 순서 때문에 `NUM_LINES_PER_UNCOR`가 1로 남는다)는 가독성이 아니라 동작 결함이다. 심각도 판정이 필요하다
- ㉯ 팀 R 워커 1(R2 모드 정보 분산): R6-1의 `Set_Gen_Trial_LLR_Mode` 쪼개기 가운데 `Calculate_Max_Modification_Trial`(13갈래 elif)과 R6-3의 `MODE_CONFIG_CLASS` 표는 모드 추가 비용 문제와 같은 뿌리다. 처방을 맞춰야 한다
- ㉰ 팀 R 워커 3(R9 주석과 로그): R3-4의 "십시일반" 용어, R5-2의 무의미한 `is not None` 검사는 주석과 방어 코드 관점과 겹친다
