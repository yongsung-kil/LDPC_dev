# Round 2 [R: 가독성] 워커 1 (구조): R1, R2, R7, R8

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 작업 시점 파일: [DAO_Main.py](5_DAO/SRC/DAO_Main.py) 10,428줄, [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py) 645줄,
> [DAO_Config.py](5_DAO/SRC/DAO_Config.py) 457줄, [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py) 196줄
> 줄 번호는 모두 이 커밋 기준으로 다시 확인했다.

## 0. 이 문서를 읽는 법

- ㉮ 배정 관점 네 개를 2장(R1), 3장(R2), 4장(R7), 5장(R8)으로 나누어 담았다
- ㉯ 처방에는 **우선순위**(상, 중, 하), **위험**(동작 변경 여부와 옆 세션 SW 분기 작업과의 충돌), **구체 처방**(무엇을 어디로, 어떤 이름으로)을 붙였다
- ㉰ 처방 사이의 적용 순서 의존은 6장에 모아 두었다
- ㉱ 필수 산출물 ㉮(메서드 212개 전수 분류표)는 문서 끝 [부록 A](#부록-a-llr_opt-메서드-212개-전수-분류표)에 있다
- ㉲ 이 문서에서 **메서드 묶음 클래스**는 자기 인스턴스를 만들지 않고 메서드만 담아 다른 클래스가 상속으로 합쳐 쓰는 클래스를 뜻한다 (파이썬에서 mixin이라 부르는 것). `self`가 그대로 유지되므로 메서드를 옮겨도 동작이 바뀌지 않는다

### 조사 방법

`DAO_Main.py`를 파이썬 `ast` 모듈로 파싱해 메서드 226개(클래스 밖 모듈 함수 10개와 상태 dataclass 4개 포함, `LLR_OPT` 메서드 212개)의 줄 범위, 각 메서드가 읽고 쓰는 `self` 속성, 메서드 사이 호출 관계를 전수로 뽑았다. 그 위에서 책임군을 손으로 배정하고, 군별 속성 집합과 군 사이 공유 속성 수를 기계로 셌다. 문자열 디스패치(`getattr`)로 이어지는 호출은 기계가 못 잡으므로 해당 지점을 따로 정독해 보충했다.

---

## 1. 결론 요약

| 관점 | 결론 | 가장 급한 처방 |
|------|------|--------------|
| R1 | `LLR_OPT` 212개 메서드는 16개 책임군으로 깔끔하게 갈린다. 군 사이 공유 속성이 적은 순서가 곧 분할 순서다. 파일을 나누면 `DAO_Main.py`는 10,428줄에서 약 2,200줄로 줄어든다 | [R1-1](#처방-r1-1-공유-속성이-적은-군부터-메서드-묶음-클래스로-떼어낸다) 인프라 5개 군(로그, 종료 플래그, CSW 로그, MPI, 세션 경로) 먼저 분리 |
| R2 | 모드 하나를 더할 때 손대는 자리는 **15곳**이다. `DAO_spec.md` 7.1 체크리스트는 그중 **6곳**만 적는다. 나머지 9곳은 빠뜨려도 실행 전까지 드러나지 않는다 | [R2-1](#처방-r2-1-모드-정보를-표-하나로-모은다) 모드 정보를 `GEN_LLR_MODE_SPECS` 표 하나로 모은다 |
| R7 | 의존 방향에 순환은 없다. 다만 상수 모듈을 import하는 것만으로 MPI가 초기화되고, 별표 import 두 줄로 이름 102개가 들어오며, 데이터 모델이 설정 클래스 3개를 직접 읽는다 | [R7-1](#처방-r7-1-mpi-초기화를-상수-모듈에서-꺼낸다) MPI 초기화를 `DAO_Constants.py`에서 꺼낸다 |
| R8 | `LLR_Row`에 칸을 하나 더하면 **10종 29곳**, `LLR_Header`에 그룹당 값 배열을 하나 더하면 **10종 22곳**을 고쳐야 한다. 옆 세션 SW 분기 작업이 바로 이것이고, 현재 유효성 규칙 한 줄이 그 작업과 정면으로 부딪친다 | [R8-1](#처방-r8-1-row-꼬리-칸을-이름으로-읽는다) ~ [R8-4](#처방-r8-4-row-필드-규칙을-이름-붙인-함수로-뽑는다) 를 SW 분기 DAO 작업 **전에** 적용 |

문제 없음으로 판정한 것: 메서드 이름 212개는 모두 서로 다르다 (메서드 묶음 클래스로 나눠도 이름 충돌이 없다). 모듈 사이 import에 순환이 없다.

---

## 2. R1: `LLR_OPT` 책임 경계와 파일 분할 축

### 2.1 책임군 16개

필수 산출물 ㉯다.

212개 메서드를 16개 책임군으로 갈랐다. 메서드별 배정은 [부록 A](#부록-a-llr_opt-메서드-212개-전수-분류표)에 있다.

"공유 속성"은 그 군이 읽거나 쓰는 `self` 속성 가운데 다른 군도 쓰는 것의 개수다. `__init__`, `_init_per_matrix_state`, `_Reset_For_Next_Matrix`, `_collect_error_state_snapshot`은 속성을 전부 건드리므로 이 셈에서 뺐다 (생성자가 모든 속성을 만드는 것은 당연하고, 분할 난이도와 무관하다).

| 책임군 | 메서드 | 줄수 | 전용 속성 | 공유 속성 | 이 군이 부르는 다른 군 (인프라 제외) |
|--------|--------|------|----------|----------|--------------------------------|
| CSW 로그 (CSWLOG) | 3 | 114 | 0 | 6 | 없음 |
| 멀티라운드 상태기계 (MULTIROUND) | 25 | 1,826 | 4 | 7 | 갱신 판정, LLR 생성, 보고 출력 |
| 종료 플래그 파일 (FLAG) | 15 | 152 | 0 | 8 | 없음 |
| 수명주기와 설정 검증 (LIFECYCLE) | 14 | 552 | 2 | 9 | 최적화 루프, 단일 row, 속도 테스트, uncor 풀 |
| 로그 기록 (LOG) | 12 | 354 | 8 | 9 | 없음 |
| 코어 속도 테스트 (SPEED) | 3 | 135 | 1 | 9 | 갱신 판정, Ref-C 실행, uncor 풀 |
| LLR 생성 모드 (GEN) | 35 | 2,394 | 13 | 10 | 수명주기 (1곳) |
| 단일 row 생성 모드 (SINGLEROW) | 5 | 339 | 1 | 11 | 8개 군 |
| 세션 경로와 정리 (PATH) | 13 | 283 | 2 | 12 | Ref-C 실행, 종료 플래그, LLR 생성, 보고 출력 |
| MPI 통신 (MPI) | 9 | 354 | 1 | 13 | 없음 |
| uncor 풀 (UNCOR) | 18 | 841 | 3 | 14 | 갱신 판정, 종료 플래그, 최적화 루프, 보고 출력 |
| Ref-C 실행 (ECC) | 14 | 461 | 6 | 14 | 갱신 판정, 종료 플래그, 결과 집계, uncor 풀 |
| 갱신 판정 (DECIDE) | 15 | 376 | 0 | 17 | uncor 풀 |
| Ref-C 결과 집계 (RESULT) | 6 | 324 | 4 | 17 | 갱신 판정, Ref-C 실행 |
| 보고 출력 (PRINT) | 14 | 405 | 0 | 26 | Ref-C 실행 |
| 최적화 루프 (LOOP) | 11 | 784 | 1 | 30 | 11개 군 전부 |

군별 공유 속성 전체 목록:

| 책임군 | 전용 속성 | 공유 속성 |
|--------|----------|----------|
| CSWLOG | (없음) | `current_test_mode`, `enable_print_CSW_log`, `excluded_cores`, `is_root`, `num_process`, `optimal_output_dir` |
| MULTIROUND | `reorder_state`, `adjust_iter_state`, `delete_row_state`, `insert_restart_group_state` | `current_LLR_matrix_idx`, `current_target_idx`, `current_trial_idx`, `max_modification_trial`, `optimal_LLR_matrix`, `target_group_indices`, `temp_optimal_LLR_matrix` |
| FLAG | (없음) | `excluded_cores`, `is_current_core_excluded`, `is_root`, `is_test_end`, `max_error`, `num_process`, `rank`, `total_num_errors` |
| LIFECYCLE | `_current_initial_matrix_idx`, `base_seed` | `CSW_update_limit_value`, `current_seed_mode`, `excluded_cores`, `initial_LLR_matrix`, `is_root`, `now_enable_CSW_update_limit`, `num_process`, `rank`, `target_group_indices` |
| LOG | `debug_cnt`, `debug_is_init`, `log_create_time`, `log_file_path`, `log_line_count`, `log_start_matrix_idx`, `start_time_str`, `update_log_file_path` | `comm`, `current_LLR_matrix_idx`, `is_root`, `log_has_update`, `num_process`, `rank`, `session_dir`, `session_timestamp`, `simulation_start` |
| SPEED | `core_elapsed_times` | `_last_speed_test_time`, `comm`, `current_LLR_matrix`, `current_seed_mode`, `excluded_cores`, `is_current_core_excluded`, `is_root`, `local_session_dir`, `rank` |
| GEN | `_external_row_cache`, `gen_DV_idx`, `gen_row_idx`, `insert_group_add_restart`, `is_gen_row_reuse_mode`, `is_mutate_matrix_tuning_phase`, `is_replace_DV_in_Ch_Th_reuse_mode`, `max_possible_tuning_mutation_count`, `prev_generated_mutation`, `previous_dv_segment`, `previous_gen_row`, `tuning_mutation_count`, `tuning_mutations` | `CSW_update_limit_value`, `copy_group_candidates`, `copy_row_candidates`, `current_target_group_idx`, `current_trial_idx`, `initial_LLR_matrix`, `is_previous_trial_updated`, `max_modification_trial`, `now_enable_CSW_update_limit`, `target_group_indices` |
| SINGLEROW | `_gen_single_row_stop_idx` | `_last_saved_local_matrix_idx`, `_last_speed_test_time`, `current_test_mode`, `enable_print_CSW_log`, `excluded_cores`, `initial_LLR_matrix`, `is_root`, `is_test_end`, `local_session_dir`, `num_process`, `session_dir` |
| PATH | `input_args`, `src_backup_dir` | `_last_saved_local_matrix_idx`, `end_flag_dir`, `is_root`, `local_session_dir`, `optimal_output_dir`, `rank`, `session_dir`, `session_error_dir`, `session_timestamp`, `session_uncor_dir`, `single_row_candidates_dir`, `trial_output_dir` |
| MPI | `barrier_count` | `comm`, `current_gen_trial_LLR_mode`, `current_gen_trial_LLR_mode_index`, `current_gen_trial_LLR_mode_name`, `current_target_group_idx`, `current_target_group_list_index`, `is_root`, `max_modification_trial`, `num_process`, `optimal_LLR_matrix`, `rank`, `session_dir`, `session_error_dir` |
| UNCOR | `current_loaded_test_mode`, `is_uncor_pool_ready`, `pool_has_uncor` | `current_LLR_matrix`, `current_seed_mode`, `current_test_mode`, `excluded_cores`, `has_uncor`, `is_current_core_excluded`, `is_root`, `local_session_dir`, `num_process`, `optimal_LLR_matrix`, `rank`, `session_dir`, `total_num_partial_uncors`, `total_num_uncors` |
| ECC | `batch_path`, `ecc_start_time`, `ecc_end_time`, `ecc_elapsed_time`, `loop_start_time`, `loop_end_time_stamp` | `_last_saved_local_matrix_idx`, `current_gen_trial_LLR_mode`, `current_seed_mode`, `enable_print_CSW_log`, `has_uncor`, `is_current_core_excluded`, `is_root`, `is_test_end`, `local_session_dir`, `loop_elapsed_time`, `loop_end_time`, `max_error`, `rank`, `total_elapsed_time` |
| DECIDE | (없음) | `current_LLR_matrix`, `current_LLR_matrix_idx`, `current_gen_trial_LLR_mode`, `current_trial_idx`, `generate_LLR_success`, `is_current_LLR_valid`, `is_previous_trial_updated`, `is_root`, `is_update_at_last_trial`, `log_has_update`, `max_modification_trial`, `optimal_LLR_matrix`, `optimal_output_dir`, `previous_optimal_LLR_matrix`, `target_group_indices`, `temp_optimal_LLR_matrix`, `update_mode` |
| RESULT | `total_num_tests`, `total_num_iterations`, `total_raw_FERs`, `total_seed_FERs` | 나머지 17개 (FER 누적 배열 전부와 `current_test_mode`, `excluded_cores` 등) |
| PRINT | (없음) | 26개 (쓰기는 하나도 없고 전부 읽기) |
| LOOP | `is_current_stage_enable_max_stage_time_limit` | 30개 |

### 2.2 읽어낸 것

- ㉮ **`PRINT` 군은 속성을 하나도 쓰지 않는다.** 메서드 14개, 405줄이 오직 읽기만 한다. 즉 지금도 사실상 "상태를 보고 문자열을 만드는" 순수 계층이다. 분할해도 상태가 갈라질 일이 없다
- ㉯ **`MULTIROUND` 군은 1,826줄인데 공유 속성이 7개뿐이고 전용 상태 4개(`reorder_state` 등)를 독점한다.** 덩치 대비 결합도가 가장 낮다. 바깥에서 이 군으로 들어오는 입구는 `Gen_Trial_LLR`이 부르는 `Gen_LLR_*` 4개와, `MULTI_ROUND_INIT_FUNC`/`MULTI_ROUND_UPDATE_FUNC` 문자열로 불리는 `Init_*` 4개, `Update_*` 3개뿐이다
- ㉰ **`GEN` 군은 2,394줄로 가장 크지만 전용 속성 13개를 가지고 공유는 10개다.** 이 13개 가운데 `gen_DV_idx`, `gen_row_idx`, `tuning_mutations`, `prev_generated_mutation`, `previous_gen_row`, `previous_dv_segment`, `is_mutate_matrix_tuning_phase`, `max_possible_tuning_mutation_count`, `tuning_mutation_count`는 `__init__`에 선언되지 않고 생성 메서드 안에서 처음 생긴다 (R5와 겹치는 지점이니 워커 2와 대조 필요)
- ㉱ **`LOOP` 군(11개 메서드, 784줄)이 공유 속성 30개를 쥔 중심이다.** 이 군은 나머지 11개 군 전부를 부른다. 분할 뒤에도 `DAO_Main.py`에 남아야 하는 몸통이다
- ㉲ **위로 거슬러 부르는 자리는 두 곳뿐이다.** `Rebuild_Partial_Pool`(UNCOR, [DAO_Main.py:9350](5_DAO/SRC/DAO_Main.py#L9350))이 `Test_LLR`(LOOP)을 부르고, `Mutate_Matrix_Setup`(GEN, [DAO_Main.py:7097](5_DAO/SRC/DAO_Main.py#L7097))이 `Set_CSW_Update_Limit`(LIFECYCLE)을 부른다. 메서드 묶음 클래스로 나누면 둘 다 문제가 되지 않지만, 나중에 진짜 협력 객체로 뽑을 때는 이 두 자리가 순환 의존이 된다
- ㉳ **`DAO_LLR_MATRIX`와의 경계**: 매트릭스 객체를 만드는 자리는 [DAO_Main.py:2581](5_DAO/SRC/DAO_Main.py#L2581)과 [DAO_Main.py:4312](5_DAO/SRC/DAO_Main.py#L4312) 두 곳뿐이다. 반면 매트릭스의 `header`와 `groups`를 직접 뜯어고치는 자리는 `GEN`과 `MULTIROUND` 두 군에 몰려 있다. 즉 데이터 모델의 불변 규칙이 `DAO_LLR_MATRIX.py`가 아니라 생성 모드 쪽 60개 메서드에 흩어져 있다 (5장 R8이 이 얘기다)

### 처방 R1-1: 공유 속성이 적은 군부터 메서드 묶음 클래스로 떼어낸다

**우선순위: 상**

**구체 처방.** `LLR_OPT`를 메서드 묶음 클래스 여러 개의 상속으로 조립한다. 메서드 본문은 한 글자도 바꾸지 않고 파일만 옮긴다.

```python
# DAO_Main.py
class LLR_OPT(
        Single_Round_Mode_Generation,
        Multi_Round_Mode_Generation,
        Uncor_Pool,
        Ref_C_Execution,
        Ref_C_Result_Reading,
        Result_Report,
        Session_Directories,
        CSW_Log_Files,
        End_Flag_Files,
        MPI_Communication,
        Log_Writing,
        Single_Row_Generation,
        ):
```

떼어내는 순서와 이름은 아래와 같다. 순서 기준은 ㉠ 공유 속성 수가 적을 것 ㉡ 다른 군을 부르지 않을 것 ㉢ 옆 세션 SW 분기 작업과 겹치지 않을 것이다.

| 순서 | 책임군 | 새 파일 | 클래스 이름 | 옮기는 줄수 | 옆 세션 충돌 |
|------|--------|---------|------------|-----------|------------|
| 1 | LOG | `DAO_Log_Writing.py` | `Log_Writing` | 354 | 없음 |
| 2 | FLAG | `DAO_End_Flag_Files.py` | `End_Flag_Files` | 152 | 없음 |
| 3 | CSWLOG | `DAO_CSW_Log_Files.py` | `CSW_Log_Files` | 114 | 없음 |
| 4 | MPI | `DAO_MPI_Communication.py` | `MPI_Communication` | 354 | 없음 |
| 5 | PATH | `DAO_Session_Directories.py` | `Session_Directories` | 283 | 없음 |
| 6 | ECC + SPEED | `DAO_Ref_C_Execution.py` | `Ref_C_Execution` | 596 | 없음 |
| 7 | RESULT | `DAO_Ref_C_Result_Reading.py` | `Ref_C_Result_Reading` | 324 | 없음 |
| 8 | UNCOR | `DAO_Uncor_Pool.py` | `Uncor_Pool` | 841 | 없음 |
| 9 | PRINT | `DAO_Result_Report.py` | `Result_Report` | 405 | 낮음 (모드별 config 분기 하나) |
| 10 | SINGLEROW | `DAO_Single_Row_Generation.py` | `Single_Row_Generation` | 339 | 낮음 |
| 11 | MULTIROUND | `DAO_Gen_Multi_Round_Modes.py` | `Multi_Round_Mode_Generation` | 1,826 | **높음** |
| 12 | GEN | `DAO_Gen_Single_Round_Modes.py` | `Single_Round_Mode_Generation` | 2,394 | **높음** |

1번부터 10번까지가 3,762줄이고, 11번과 12번이 4,220줄이다. 둘 다 끝나면 `DAO_Main.py`에는 모듈 함수와 상태 dataclass 4개(1~480줄), 최적화 루프(LOOP) 784줄, 갱신 판정(DECIDE) 376줄, 수명주기(LIFECYCLE) 552줄만 남아 약 2,200줄이 된다.

**위험.**

- ㉮ 동작 변경: 없다. 메서드 이름 212개가 서로 겹치지 않는 것을 확인했으므로 상속 순서가 결과에 영향을 주지 않는다. `self`가 그대로이므로 속성 접근도 동일하다
- ㉯ 옆 세션 충돌: 1번부터 10번까지는 SW 분기 작업이 건드리지 않는 영역이라 안전하다. **11번과 12번은 SW 분기 DAO 작업이 끝난 뒤에 한다.** SW 분기는 매트릭스 생성 본문(그룹을 넣고 빼는 자리)을 고치므로, 그 파일을 동시에 옮기면 diff가 통째로 어긋난다
- ㉰ 잔여 위험: `Debug_Pause`([DAO_Main.py:1346](5_DAO/SRC/DAO_Main.py#L1346))가 `inspect`로 호출 스택을 읽고, `Write_MPI_Error_Snapshot`([DAO_Main.py:6743](5_DAO/SRC/DAO_Main.py#L6743))이 `traceback` 문자열에서 `"bcast"`, `"gather"`, `"barrier"`, `"comm"` 낱말을 찾는다. 파일이 갈라져도 함수 이름은 그대로이므로 동작은 같지만, 옮긴 뒤 한 번 실행해 로그를 눈으로 확인하는 편이 좋다

### 처방 R1-2: 전용 상태를 가진 두 군은 두 번째 단계에서 협력 객체로 뽑는다

**우선순위: 중** (R1-1이 끝난 뒤)

**구체 처방.** `MULTIROUND`와 `GEN`은 전용 속성이 각각 4개와 13개로, 메서드 묶음 클래스를 넘어 진짜 객체로 뽑을 값이 있다.

- ㉮ `MULTIROUND`: 상태 dataclass 4개(`ReorderState`, `AdjustIterState`, `DeleteRowState`, `InsertRestartGroupState`)가 이미 상태를 한 덩어리로 묶고 있다. 각 상태 클래스가 자기 `Init`, `Update_Round_Result`, `Finalize_Round`, `Build_Matrix` 메서드를 갖게 하면 [3장 R2](#3-r2-생성-모드-정보의-분산과-문자열-디스패치)의 문자열 디스패치 3개(`MULTI_ROUND_MODES`, `MULTI_ROUND_INIT_FUNC`, `MULTI_ROUND_UPDATE_FUNC`)가 통째로 사라진다
- ㉯ `DeleteRowState`([DAO_Main.py:327](5_DAO/SRC/DAO_Main.py#L327))와 `InsertRestartGroupState`([DAO_Main.py:381](5_DAO/SRC/DAO_Main.py#L381))는 필드 9개 가운데 8개가 완전히 같고, 후보 목록 필드 이름만 `deletable_rows`와 `insertable_positions`로 다르다. 공통 기반 `Round_Based_Mode_State`(필드: `is_active`, `current_round`, `candidates`, `current_candidate_idx`, `round_best_candidate_idx`, `round_best_matrix`, `round_baseline_matrix`, `round_trial_count`, `total_expected_trials`)를 만들고 둘을 상속으로 잇는다
- ㉰ `GEN`: 전용 속성 13개 가운데 9개가 `__init__` 밖에서 처음 생긴다. 이것들을 `Mutation_Progress_State` dataclass 하나로 묶어 `self.mutation_progress`에 담는다

**위험.** 동작 변경 가능. 상태를 객체로 옮기면 MPI bcast 대상도 바뀐다(`Gen_Trial_LLR` [DAO_Main.py:2022-2026](5_DAO/SRC/DAO_Main.py#L2022), `Run_Optimization` [DAO_Main.py:8047-8056](5_DAO/SRC/DAO_Main.py#L8047)). 상태 dataclass에 메서드를 달면 pickle 직렬화 대상이 넓어지므로 bcast 전후 값을 로그로 대조해야 한다. 옆 세션 작업과 겹칠 소지가 크므로 SW 분기 작업 완료 후에 한다.

---

## 3. R2: 생성 모드 정보의 분산과 문자열 디스패치

### 3.1 모드 하나를 추가할 때 손대는 자리

필수 산출물 ㉱이다.

| # | 손대는 자리 | 위치 | spec 7.1에 있는가 |
|---|-----------|------|-----------------|
| 1 | `GenLLRMode` 열거형에 값 추가 | [DAO_Constants.py:24-41](5_DAO/SRC/DAO_Constants.py#L24) | O |
| 2 | `Gen_Trial_LLR`의 `if/elif` 사슬에 갈래 추가 (18갈래) | [DAO_Main.py:1956-1992](5_DAO/SRC/DAO_Main.py#L1956) | O |
| 3 | `Gen_LLR_{모드이름}` 메서드 구현 | 모드별 | O |
| 4 | 모드용 CONFIG 클래스 정의 | [DAO_Config.py:239-405](5_DAO/SRC/DAO_Config.py#L239) | O |
| 5 | CONFIG 클래스에 `MAX_TRIAL` 필드 추가 | 같은 곳 | O |
| 6 | `Set_Gen_Trial_LLR_Mode`의 `MODE_MAX_TRIAL_MAP`에 등록 | [DAO_Main.py:8429-8440](5_DAO/SRC/DAO_Main.py#L8429) | O |
| 7 | `Set_Gen_Trial_LLR_Mode`의 모드 전용 trial 수 계산 갈래 (7갈래) | [DAO_Main.py:8333-8428](5_DAO/SRC/DAO_Main.py#L8333) | X |
| 8 | `Set_Update_Flags`의 모드 목록 (11개) | [DAO_Main.py:8626-8639](5_DAO/SRC/DAO_Main.py#L8626) | X |
| 9 | `Print_Test_Summary`의 같은 뜻 목록 (10개) | [DAO_Main.py:7632-7643](5_DAO/SRC/DAO_Main.py#L7632) | X |
| 10 | `Print_Stage_Info`의 모드별 CONFIG 출력 사슬 (12갈래) | [DAO_Main.py:7236-7259](5_DAO/SRC/DAO_Main.py#L7236) | X |
| 11 | `SKIP_RESTART_GROUP` 목록 (12개) | [DAO_Constants.py:151-164](5_DAO/SRC/DAO_Constants.py#L151) | X |
| 12 | `MULTI_ROUND_MODES` 딕셔너리 (상태 속성 이름) | [DAO_Constants.py:169-174](5_DAO/SRC/DAO_Constants.py#L169) | 부분 ("상태 변수 동기화 (해당시)") |
| 13 | `MULTI_ROUND_FULL_ONLY_MODES` 집합 | [DAO_Constants.py:179-182](5_DAO/SRC/DAO_Constants.py#L179) | X |
| 14 | `MULTI_ROUND_UPDATE_FUNC` 딕셔너리 (메서드 이름 문자열) | [DAO_Constants.py:185-189](5_DAO/SRC/DAO_Constants.py#L185) | X |
| 15 | `MULTI_ROUND_INIT_FUNC` 딕셔너리 (메서드 이름 문자열) | [DAO_Constants.py:192-196](5_DAO/SRC/DAO_Constants.py#L192) | X |
| (참고) | `Gen_LLR_Mode_SEQUENCE` 기본값에 넣을지 판단 | [DAO_Config.py:133](5_DAO/SRC/DAO_Config.py#L133) | X |
| (참고) | `GenLLRModeHBF` 열거형 (현재 코드에서 읽는 자리 없음) | [DAO_Constants.py:43-51](5_DAO/SRC/DAO_Constants.py#L43) | X |
| (참고) | `CONFIGS` 목록에 CONFIG 클래스 등록 (로그 출력용) | [DAO_Config.py:406-425](5_DAO/SRC/DAO_Config.py#L406) | X |
| (참고) | `Validate_Config`에 설정 검증 블록 | [DAO_Main.py:9647-9900](5_DAO/SRC/DAO_Main.py#L9647) | X |
| (참고) | `DAO_spec.md` 5장 모드별 상세 스펙 절 | [DAO_spec.md](5_DAO/DAO_spec.md) 5장 | X |

**spec 7장 체크리스트 대조 결과: 필수 15곳 가운데 6곳만 적혀 있다.** 빠진 9곳 가운데 7번부터 11번까지 5곳은 잊어도 예외가 나지 않고 조용히 잘못 동작한다.

- ㉮ 8번을 잊으면 `is_update_at_last_trial`이 `False`가 되어 여러 trial 중 가장 좋은 것을 고르는 대신 매 trial마다 optimal과 직접 비교한다
- ㉯ 11번을 잊으면 restart 그룹을 타겟으로 잡는 stage가 그대로 돌아 시간만 쓴다
- ㉰ 10번을 잊으면 로그에 그 모드의 설정이 찍히지 않아 나중에 로그만으로 재현할 수 없다

### 3.2 모드별 등록 현황 교차표

O는 등록됨, X는 없음이다. 14, 15번 열은 멀티라운드 모드에만 해당한다.

| 모드 (값) | 2 생성분기 | 3 구현 | 4 CONFIG | 6 MAX_TRIAL맵 | 7 전용trial계산 | 8 UpdateFlags | 9 TestSummary | 10 StageInfo | 11 SKIP_RESTART | 12 MULTI_ROUND | 13 FULL_ONLY | 14 UPDATE_FUNC | 15 INIT_FUNC | 기본 SEQUENCE |
|-----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GEN_INITIAL_GROUP (0) | O | O | O | O | O | O | O | O | O | X | X | X | X | X |
| MUTATE_MATRIX (10) | O | O | O(MUTATE_CONFIG) | O | X | X | X | O | O | X | X | X | X | O |
| MUTATE_CSW (11) | O | O | O(MUTATE_CONFIG) | O | X | X | X | O | O | X | X | X | X | O |
| SWAP_ROW (21) | O | O | **X** | X | O | X | X | **X** | O | X | X | X | X | O |
| REORDER_GROUP (22) | O | O | **X** | X | O | O | O | **X** | X | O | O | O | O | X |
| COPY_ROWS (30) | O | O | O | X | O | X | X | O | O | X | X | X | X | O |
| COPY_GROUP (31) | O | O | O | X | O | O | O | O | O | X | X | X | X | O |
| INSERT_RANDOM_GROUP (40) | O | O | O | O | X | O | O | O | X | X | X | X | X | O |
| INSERT_RANDOM_ROW (41) | O | O | O | O | X | O | O | O | O | X | X | X | X | O |
| INSERT_MUTATED_GROUP (42) | O | O | O | O | X | O | O | O | X | X | X | X | X | O |
| INSERT_MUTATED_ROW (43) | O | O | O | O | X | O | O | O | O | X | X | X | X | O |
| REGEN_DV (50) | O | O | O | O | X | X | X | O | O | X | X | X | X | O |
| REGEN_ROW (51) | O | O | O | O | X | X | X | O | O | X | X | X | X | O |
| SPLIT_GROUP (60) | O | O | O | O | X | O | O | O | O | X | X | X | X | X |
| ADJUST_ITERATION (62) | O | O | O | X | O | O | O | **X** | O | O | O | **X** | O | X |
| DELETE_ROW (70) | O | O | **X** | X | O | O | O | **X** | X | O | X | O | O | O |
| INSERT_RESTART_GROUP (80) | O | O | **X** | X | **X** | O | **X** | **X** | X | O | X | O | O | X |

표에서 바로 드러나는 어긋남 (동작 판정은 L팀 몫이고, 여기서는 "표 하나였다면 눈에 보였을 것"이라는 근거로 적는다):

- ㉮ **8번 `Set_Update_Flags` 목록에는 `INSERT_RESTART_GROUP`이 있는데 9번 `Print_Test_Summary` 목록에는 없다.** 두 목록은 나머지 10개가 똑같다. 로그의 `[Test Summary]`가 `INSERT_RESTART_GROUP` stage에서 temp_optimal을 표시하지 않는다
- ㉯ **`INSERT_RESTART_GROUP`은 7번 전용 trial 계산 갈래에도, 6번 `MODE_MAX_TRIAL_MAP`에도 없다.** [DAO_Main.py:8441-8446](5_DAO/SRC/DAO_Main.py#L8441)의 `else`로 떨어져 `max_modification_trial = DAO_CONFIG.MAX_OPTIMIZATION_TRIALS`(9999)가 되고, 그 뒤 `Initialize_Stage`가 부르는 `Init_Insert_Restart_Group_Mode`가 덮어쓴다. `DELETE_ROW`는 같은 상황에 [DAO_Main.py:8423-8427](5_DAO/SRC/DAO_Main.py#L8423)에 "여기서는 임시값, Init에서 덮어씀"이라는 갈래를 명시해 두었다. 같은 일을 두 모드가 서로 다르게 쓴다
- ㉰ **10번 `Print_Stage_Info`에 `SWAP_ROW`, `REORDER_GROUP`, `ADJUST_ITERATION`, `DELETE_ROW`, `INSERT_RESTART_GROUP` 다섯 모드가 없다.** 앞의 셋은 CONFIG 클래스가 아예 없어서이고, `ADJUST_ITERATION`은 `ADJUST_ITERATION_CONFIG`가 있는데도 빠졌다
- ㉱ **`ADJUST_ITERATION_CONFIG`는 `CONFIGS` 목록([DAO_Config.py:406-425](5_DAO/SRC/DAO_Config.py#L406))에도 없다.** `SPEED_TEST_REFC_CONFIG`, `PATH_CONFIG`도 없다. 이 셋은 세션 시작 로그에 찍히지 않는다

### 3.3 문자열 디스패치가 읽는 사람에게 주는 비용

`getattr(self, ...)`와 `setattr(self, ...)`로 상태와 메서드를 찾는 자리는 8곳이다.

| 위치 | 무엇을 문자열로 찾는가 | 이름의 출처 |
|------|---------------------|-----------|
| [DAO_Main.py:2024](5_DAO/SRC/DAO_Main.py#L2024), [2026](5_DAO/SRC/DAO_Main.py#L2026) | 상태 속성 (`reorder_state` 등) | `MULTI_ROUND_MODES` |
| [DAO_Main.py:2301](5_DAO/SRC/DAO_Main.py#L2301) | 초기화 메서드 (`Init_Reorder_Group_Mode` 등) | `MULTI_ROUND_INIT_FUNC` |
| [DAO_Main.py:8052](5_DAO/SRC/DAO_Main.py#L8052) | 라운드 결과 갱신 메서드 | `MULTI_ROUND_UPDATE_FUNC` |
| [DAO_Main.py:8054](5_DAO/SRC/DAO_Main.py#L8054), [8056](5_DAO/SRC/DAO_Main.py#L8056) | 상태 속성 | `MULTI_ROUND_MODES` |
| [DAO_Main.py:8108](5_DAO/SRC/DAO_Main.py#L8108) | 상태 속성 | `MULTI_ROUND_MODES` |
| [DAO_Main.py:8154](5_DAO/SRC/DAO_Main.py#L8154) | 상태 속성 | `MULTI_ROUND_MODES` |
| [DAO_Main.py:9500](5_DAO/SRC/DAO_Main.py#L9500) | 상태 속성 | `MULTI_ROUND_MODES` |

비용을 구체적으로 적으면 이렇다.

- ㉮ `Init_Reorder_Group_Mode`, `Init_Adjust_Iteration_Mode`, `Init_Delete_Row_Mode`, `Init_Insert_Restart_Group_Mode` 네 메서드는 코드 안에서 호출되는 자리가 한 곳도 없다. 편집기의 "사용처 찾기"가 0건을 돌려주므로, 읽는 사람은 이 메서드들이 죽은 코드라고 오해하거나 `DAO_Constants.py`의 문자열까지 뒤져야 한다. `Update_Reorder_Round_Result` 등 세 메서드도 같다
- ㉯ 상태 속성 이름을 잘못 적으면 `getattr`이 `AttributeError`를 던지는데, 그 모드가 실제로 도는 stage에 이르러서야 터진다. `Gen_LLR_Mode_SEQUENCE` 한 바퀴가 12 stage이므로 오류가 늦게 드러난다
- ㉰ 같은 4줄짜리 관용구(`state_attr = MULTI_ROUND_MODES[...]`, `state = getattr(...)`, bcast, `setattr(...)`)가 `Gen_Trial_LLR`과 `Run_Optimization`에서 4번, `Test_Trial_LLR`에서 1번, 모두 5번 되풀이된다

### 처방 R2-1: 모드 정보를 표 하나로 모은다

**우선순위: 상**

**구체 처방.** `DAO_Constants.py`에 모드 사양 dataclass와 표를 만든다.

```python
@dataclass(frozen=True)
class Gen_LLR_Mode_Spec:
    generator_method_name: str          # Gen_Trial_LLR이 부를 메서드 이름
    config_class_name: Optional[str]    # Print_Stage_Info가 출력할 설정 클래스
    uses_config_max_trial: bool         # MODE_MAX_TRIAL_MAP을 쓰는 모드인가
    updates_optimal_at_last_trial: bool # Set_Update_Flags, Print_Test_Summary 공용
    skips_restart_target_group: bool    # SKIP_RESTART_GROUP 공용
    multi_round_state_attr: Optional[str]
    multi_round_init_method: Optional[str]
    multi_round_update_method: Optional[str]
    runs_full_test_only: bool

GEN_LLR_MODE_SPECS: dict[GenLLRMode, Gen_LLR_Mode_Spec] = { ... }
```

이 표 하나가 지금의 딕셔너리 4개(`MULTI_ROUND_MODES`, `MULTI_ROUND_FULL_ONLY_MODES`, `MULTI_ROUND_UPDATE_FUNC`, `MULTI_ROUND_INIT_FUNC`), 목록 2개(`SKIP_RESTART_GROUP`, `MODE_MAX_TRIAL_MAP`), 그리고 `Set_Update_Flags`와 `Print_Test_Summary`가 각자 적어 둔 목록 2개를 대신한다. 새 모드를 더할 때 손대는 자리가 15곳에서 **5곳**(열거형, 이 표의 한 행, `Gen_LLR_*` 구현, CONFIG 클래스, 기본 SEQUENCE)으로 준다.

같이 고칠 것:

- ㉮ `Set_Update_Flags`([DAO_Main.py:8626-8639](5_DAO/SRC/DAO_Main.py#L8626))와 `Print_Test_Summary`([DAO_Main.py:7632-7643](5_DAO/SRC/DAO_Main.py#L7632))가 각자 쓰던 목록을 `GEN_LLR_MODE_SPECS[mode].updates_optimal_at_last_trial` 한 줄로 바꾼다
- ㉯ `Print_Stage_Info`([DAO_Main.py:7236-7259](5_DAO/SRC/DAO_Main.py#L7236))의 12갈래 사슬을 `config_class_name`을 읽어 `Print_Config`를 한 번 부르는 3줄로 바꾼다
- ㉰ `DAO_spec.md` 7.1 체크리스트를 이 5곳으로 다시 쓴다

**위험.** 동작 변경 가능. 두 목록(8번과 9번)이 `INSERT_RESTART_GROUP`에서 어긋나 있으므로, 표로 합치면 그 모드의 `Print_Test_Summary` 출력이 바뀐다. **표를 만들기 전에 L팀이 "어느 쪽이 맞는가"를 판정해야 한다.** 옆 세션 SW 분기 작업과는 겹치지 않는다 (모드 등록 표는 매트릭스 생성 본문을 건드리지 않는다).

### 처방 R2-2: 문자열 대신 함수 객체로 디스패치한다

**우선순위: 중** (R2-1 뒤)

**구체 처방.** `DAO_Main.py`의 `LLR_OPT` 클래스 본문이 끝난 자리(현재 [DAO_Main.py:10399](5_DAO/SRC/DAO_Main.py#L10399) 뒤)에 메서드 연결 표를 둔다.

```python
GEN_LLR_MODE_GENERATORS: dict[GenLLRMode, Callable] = {
    GenLLRMode.INSERT_RANDOM_ROW: LLR_OPT.Gen_LLR_Insert_Random_Row,
    ...
}
MULTI_ROUND_MODE_INITIALIZERS: dict[GenLLRMode, Callable] = {
    GenLLRMode.REORDER_GROUP: LLR_OPT.Init_Reorder_Group_Mode,
    ...
}
```

`Gen_Trial_LLR`의 18갈래 `elif`([DAO_Main.py:1956-1992](5_DAO/SRC/DAO_Main.py#L1956), 37줄)가 아래 3줄이 된다.

```python
generator = GEN_LLR_MODE_GENERATORS.get(self.current_gen_trial_LLR_mode)
if generator is None:
    self.MPI_Abort(f"Gen_Trial_LLR: Unhandled GenLLRMode={self.current_gen_trial_LLR_mode}")
new_LLR_matrix = generator(self, input_matrix=input_LLR_matrix)
```

이렇게 하면 편집기의 정의 이동과 사용처 찾기가 통하고, 이름을 잘못 적으면 import 시점에 `AttributeError`로 바로 드러난다. 상태 속성 쪽 `getattr`/`setattr` 5곳은 R1-2(상태 객체가 자기 갱신 메서드를 갖는 구조)로 없앤다.

**위험.** 동작 변경 없음. 다만 클래스 본문 밖에서 표를 만들어야 하므로 표의 위치가 파일 맨 끝이 된다. R1-1로 파일이 갈라진 뒤라면 `DAO_Main.py` 끝에 두면 된다 (생성 메서드가 다른 파일에 있어도 `LLR_OPT`를 통해 접근되므로 순환 import가 생기지 않는다). 옆 세션 충돌 낮음.

### 처방 R2-3: 모드 시퀀스를 열거형 목록으로 선언한다

**우선순위: 중**

**구체 처방.** [DAO_Config.py:133-134](5_DAO/SRC/DAO_Config.py#L133)의

```python
Gen_LLR_Mode_SEQUENCE = [10, 11, 21, 30, 31, 40, 41, 42, 43, 50, 51, 70]
Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]
```

를 `list[GenLLRMode]`로 바꿔 `[GenLLRMode.MUTATE_MATRIX, GenLLRMode.MUTATE_CSW, ...]`로 적는다. `Set_Configs_Manually`의 세 자리([DAO_Config.py:35](5_DAO/SRC/DAO_Config.py#L35), [61](5_DAO/SRC/DAO_Config.py#L61), [93](5_DAO/SRC/DAO_Config.py#L93))도 같이 바꾼다.

**위험.** 동작 변경 있음. `Gen_LLR_Mode_HBF_SEQUENCE`의 값 `[7, 8, 1, 2, 12]`는 `GenLLRMode`에 없는 값이라(유효값은 0, 10, 11, 21, 22, 30, 31, 40, 41, 42, 43, 50, 51, 60, 62, 70, 80) 열거형으로 바꾸는 순간 import가 실패한다. **L팀이 올바른 값을 판정한 뒤에 적용한다.** 뒤집어 말하면, 지금은 이 값이 틀렸다는 사실이 `Set_Gen_Trial_LLR_Mode`의 `GenLLRMode(selected_mode).name`([DAO_Main.py:8307](5_DAO/SRC/DAO_Main.py#L8307))에 이를 때까지 드러나지 않는다. 열거형 선언이 이 문제를 import 시점으로 끌어올린다.

---

## 4. R7: 전역 이름 반입과 모듈 의존 방향

### 4.1 의존 방향 그래프

```
                     mpi4py.MPI
                         |
                         v
   DAO_Constants.py  (comm, rank, num_process 를 모듈 본문에서 생성: 135-137줄)
        |         \
        |          \  from DAO_Constants import *
        v           v
   DAO_Config.py  ------------------------.
        |    \                             |
        |     \ from DAO_Config import *   | from DAO_Constants import *
        v      v                           v
   DAO_LLR_MATRIX.py  <------------- (설정 3종을 직접 읽음)
        |
        | from DAO_LLR_MATRIX import LLR_MATRIX, LLR_Row
        v
   DAO_Main.py  (+ from DAO_Config import *, from DAO_Constants import *)
```

- ㉮ **순환은 없다.** 네 모듈이 한 줄로 이어진다
- ㉯ **별표 import 두 줄로 들어오는 이름은 102개다.** `DAO_Config` 최상위 공개 이름 29개, `DAO_Constants` 73개다. 이 가운데 `DAO_Constants`의 73개는 `DAO_Config`를 거쳐 한 번, `DAO_Main.py:10`에서 직접 한 번, 모두 두 경로로 들어온다. `__all__`은 네 파일 어디에도 없다
- ㉰ **`os`와 `sys`가 별표 import로 다시 들어온다.** `DAO_Main.py:1`이 `import os, ... sys, ...`로 가져온 뒤, `DAO_Main.py:9`의 `from DAO_Config import *`가 `DAO_Config.py:2`의 `os`, `sys`를 다시 덮고, `DAO_Main.py:10`의 `from DAO_Constants import *`가 `DAO_Constants.py:1`의 `os`를 또 덮는다. 같은 모듈 객체라 동작은 같지만, 읽는 사람이 `MAX_CSW`, `SEPARATOR_TYPE1`, `comm`, `SKIP_RESTART_GROUP` 같은 이름의 출처를 코드만 보고 알 수 없다
- ㉱ **`DAO_Constants.py:135-137`이 모듈 본문에서 MPI를 초기화한다.** `import DAO_Constants` 한 줄로 `MPI.COMM_WORLD`가 잡힌다. 이름이 "상수 모듈"이라 이런 일이 벌어진다는 것이 드러나지 않는다. `Util/`의 보조 스크립트 8개가 `SRC/`의 상수를 재사용하지 않고 문자열을 다시 적는 이유도 여기에 있을 수 있다 (실제로 `Util/*.py`는 `DAO_` 모듈을 하나도 import하지 않는다)
- ㉲ **데이터 모델이 설정에 매여 있다.** `DAO_LLR_MATRIX.py`가 `REFC_CONFIG`를 24곳, `HBF_OPT_CONFIG`를 5곳, `PATH_CONFIG`를 3곳에서 직접 읽는다. 반면 `LLR_MATRIX`를 만드는 자리는 [DAO_Main.py:2581](5_DAO/SRC/DAO_Main.py#L2581)과 [DAO_Main.py:4312](5_DAO/SRC/DAO_Main.py#L4312) 두 곳뿐이다
- ㉳ **전역 `rank`가 지역 변수에 가려지는 자리가 2곳 있다.** `Rank_And_Save_Single_Row_Candidates`의 `for rank, c in enumerate(top_fer, 1)`([DAO_Main.py:10306](5_DAO/SRC/DAO_Main.py#L10306))와 `for rank, c in enumerate(top_csw, 1)`([DAO_Main.py:10333](5_DAO/SRC/DAO_Main.py#L10333))다. 여기서 `rank`는 MPI 프로세스 번호가 아니라 순위(1부터 K까지)다. 이 함수 안에서 나중에 누군가 MPI rank를 읽으면 조용히 순위 값을 받는다
- ㉴ **MPI 접근 경로가 두 갈래다.** 클래스 안에서는 `self.comm`, `self.rank`([DAO_Main.py:505-508](5_DAO/SRC/DAO_Main.py#L505)에서 전역을 복사)를 쓰고, 모듈 진입점([DAO_Main.py:10413-10418](5_DAO/SRC/DAO_Main.py#L10413), [10426-10427](5_DAO/SRC/DAO_Main.py#L10426))은 전역 `rank`, `comm`을 직접 쓴다

### 처방 R7-1: MPI 초기화를 상수 모듈에서 꺼낸다

**우선순위: 상**

**구체 처방.** [DAO_Constants.py:135-137](5_DAO/SRC/DAO_Constants.py#L135)의 세 줄과 `from mpi4py import MPI`([DAO_Constants.py:3](5_DAO/SRC/DAO_Constants.py#L3))를 처방 R1-1의 4번에서 만든 `DAO_MPI_Communication.py`로 옮긴다. 그 파일에 다음을 둔다.

```python
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
num_process = comm.Get_size()
```

`DAO_Main.py`는 `from DAO_MPI_Communication import MPI_Communication, comm, rank, num_process`로 명시해 가져온다. 이렇게 하면 파일 이름만 보고 "이걸 import하면 MPI가 뜬다"를 알 수 있고, `DAO_Constants.py`는 mpi4py 없이도 import되는 순수 상수 모듈이 되어 `Util/` 스크립트가 경로 상수와 파일 이름 규칙을 재사용할 수 있게 된다.

**위험.** 동작 변경 없음 (초기화 시점은 여전히 import 시점이다). 고칠 자리는 `DAO_Constants.py` 4줄과 `DAO_Main.py` import 줄, 그리고 전역 `rank`/`comm`을 쓰는 모듈 진입점 6줄뿐이다. 옆 세션 충돌 없음.

### 처방 R7-2: 별표 import를 명시 import로 바꾼다

**우선순위: 중**

**구체 처방.** 두 단계로 나눈다.

- 1. `DAO_Constants.py`와 `DAO_Config.py` 각각에 `__all__`을 선언해 반입 이름을 실제로 쓰이는 것만으로 좁힌다. 특히 `os`, `sys`, `Enum`, `IntEnum`, `MPI`, `Optional`, `annotations`가 별표로 새 나가지 않게 한다
- 2. `DAO_Main.py:9-10`과 `DAO_LLR_MATRIX.py:6-7`의 별표 import를 명시 목록으로 바꾼다

**위험.** 동작 변경 없음 (같은 이름을 같은 값으로 가져오므로). 다만 2단계는 이름 수가 많아 한 번에 하면 diff가 커진다. R1-1 파일 분할이 끝난 뒤, 파일별로 필요한 이름만 적으면 자연스럽게 정리된다. 옆 세션 충돌 낮음.

### 처방 R7-3: 순위 루프 변수 이름을 바꾼다

**우선순위: 중**

**구체 처방.** [DAO_Main.py:10306](5_DAO/SRC/DAO_Main.py#L10306)과 [DAO_Main.py:10333](5_DAO/SRC/DAO_Main.py#L10333)의 루프 변수 `rank`를 `ranking_position`으로 바꾸고, 같은 줄의 출력 문구 `f"[Rank {rank}]"`를 `f"[Rank {ranking_position}]"`로 맞춘다.

**위험.** 동작 변경 없음 (출력 문자열 동일). 옆 세션 충돌 없음.

### 처방 R7-4: 데이터 모델이 설정을 인자로 받게 한다

**우선순위: 중** (SW 분기 DAO 작업과 함께 하면 이득이 크다)

**구체 처방.** `LLR_MATRIX.__init__`([DAO_LLR_MATRIX.py:35](5_DAO/SRC/DAO_LLR_MATRIX.py#L35))이 채널 수와 HBF 설정, 입력 경로를 인자로 받게 한다.

```python
def __init__(self, init_n, matrix_idx, is_HBF_OPT, num_target_channels,
             hbf_max_iteration=None, hbf_th_constant_value=None,
             file_name_template=None, input_dir=None):
```

호출 지점은 두 곳뿐이므로([DAO_Main.py:2581](5_DAO/SRC/DAO_Main.py#L2581), [DAO_Main.py:4312](5_DAO/SRC/DAO_Main.py#L4312)) 옮기는 값이 명시적으로 드러난다. 이렇게 하면 `DAO_LLR_MATRIX.py`가 `DAO_Config`를 import하지 않아도 되어 데이터 모델을 단위 시험에 그대로 태울 수 있다.

**위험.** 동작 변경 없음. 다만 `Is_LLR_Valid`의 HBF 규칙([DAO_LLR_MATRIX.py:377](5_DAO/SRC/DAO_LLR_MATRIX.py#L377), [443](5_DAO/SRC/DAO_LLR_MATRIX.py#L443))도 인스턴스 속성을 읽도록 바꿔야 한다. **옆 세션 충돌 높음**: SW 분기 작업이 유효성 규칙을 고치는 중이므로, 그쪽이 끝난 뒤에 한다.

---

## 5. R8: 매트릭스 데이터 모델의 확장 용이성

이 관점은 옆 세션의 SW 분기 작업이 바로 지금 하려는 일이다. 그 작업의 계획 문서([20260902_SW_branch_LLR_matrix.md](5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/20260902_SW_branch_LLR_matrix.md) 4장)에 따르면 매트릭스에 들어갈 변화는 두 가지다.

- ㉮ 헤더에 그룹당 값 배열 `sw_branch_idx_each_group`이 하나 늘어난다 (분기 없음은 -1)
- ㉯ row의 마지막 칸 `floor_flag`가 분기 index를 담는 `sw_branch_idx`로 뜻과 이름이 바뀐다

그래서 아래 전수 목록은 "임의의 필드 하나"가 아니라 이 두 변화를 기준으로 셌다.

### 5.1 `LLR_Row`에 칸을 하나 더할 때 손대는 자리

필수 산출물 ㉲의 앞쪽이다.

| # | 자리 | 위치 | 고칠 줄 수 |
|---|------|------|----------|
| 1 | dataclass 정의 | [DAO_LLR_MATRIX.py:23-31](5_DAO/SRC/DAO_LLR_MATRIX.py#L23) | 1 |
| 2 | 파일 파서의 꼬리 칸 음수 인덱스 5줄 (`row[:-4]`, `row[-4]`, `row[-3]`, `row[-2]`, `row[-1]`) | [DAO_LLR_MATRIX.py:524-528](5_DAO/SRC/DAO_LLR_MATRIX.py#L524) | 5 (전부) |
| 3 | 파서의 `LLR_Row(...)` 위치 인자 생성 | [DAO_LLR_MATRIX.py:535](5_DAO/SRC/DAO_LLR_MATRIX.py#L535) | 1 |
| 4 | 출력 줄 조립의 3갈래 (`compare_with` 없음, 있고 `opt_row` 없음, 둘 다 있음) | [DAO_LLR_MATRIX.py:176-193](5_DAO/SRC/DAO_LLR_MATRIX.py#L176) | 3 |
| 5 | 출력 줄 문자열 결합 | [DAO_LLR_MATRIX.py:195-201](5_DAO/SRC/DAO_LLR_MATRIX.py#L195) | 1 |
| 6 | 유효성 규칙 | [DAO_LLR_MATRIX.py:344-346](5_DAO/SRC/DAO_LLR_MATRIX.py#L344) (`floor_flag != -1`) | 1 |
| 7 | 자동 보정 | [DAO_LLR_MATRIX.py:561-601](5_DAO/SRC/DAO_LLR_MATRIX.py#L561) (새 칸이 정렬 대상이면) | 0~1 |
| 8 | 로그 요약 도우미의 row 필드 나열 | [DAO_Main.py:111-118](5_DAO/SRC/DAO_Main.py#L111) | 1 |
| 9 | `LLR_Row(...)` 생성 13곳 | [DAO_Main.py:2446](5_DAO/SRC/DAO_Main.py#L2446), [2636](5_DAO/SRC/DAO_Main.py#L2636), [2670](5_DAO/SRC/DAO_Main.py#L2670), [2990](5_DAO/SRC/DAO_Main.py#L2990), [3017](5_DAO/SRC/DAO_Main.py#L3017), [3252](5_DAO/SRC/DAO_Main.py#L3252), [3391](5_DAO/SRC/DAO_Main.py#L3391), [3403](5_DAO/SRC/DAO_Main.py#L3403), [3628](5_DAO/SRC/DAO_Main.py#L3628), [5746](5_DAO/SRC/DAO_Main.py#L5746), [8907](5_DAO/SRC/DAO_Main.py#L8907), [10205](5_DAO/SRC/DAO_Main.py#L10205), [DAO_LLR_MATRIX.py:535](5_DAO/SRC/DAO_LLR_MATRIX.py#L535) | 13 |
| 10 | copy 후보 dict 3종과 그 소비 2곳 | [DAO_Main.py:4339-4343](5_DAO/SRC/DAO_Main.py#L4339), [4383-4387](5_DAO/SRC/DAO_Main.py#L4383), [4428-4434](5_DAO/SRC/DAO_Main.py#L4428), [8850](5_DAO/SRC/DAO_Main.py#L8850), [8907-8914](5_DAO/SRC/DAO_Main.py#L8907) | 5 |
| (문서) | `DAO_spec.md` 2.3 표, `README.md` 매트릭스 절 | | 2 |

**합계: 10종 29곳** (문서 2곳 제외).

특히 위험한 세 가지:

- ㉮ **2번의 음수 인덱스.** 칸이 하나 늘면 `row[:-4]`가 `row[:-5]`로, `row[-4]`가 `row[-5]`로, 다섯 줄이 모두 한 칸씩 밀린다. 하나라도 빠뜨리면 `ch_th_values`에 CSW 값이 섞여 들어가고, 그 뒤 `Is_LLR_Valid`의 길이 검사([DAO_LLR_MATRIX.py:335-338](5_DAO/SRC/DAO_LLR_MATRIX.py#L335))에 걸려 "Row length mismatch"만 뜬다. 원인이 파서라는 단서가 없다
- ㉯ **6번의 `floor_flag != -1` 규칙이 SW 분기와 정면으로 부딪친다.** 지금 규칙은 row의 마지막 칸이 -1이 아니면 무조건 무효로 친다. 마지막 칸이 분기 index(0, 1, 2 ...)가 되면 **분기가 붙은 매트릭스는 전부 무효 판정된다.** 이 한 줄을 고치지 않으면 SW 분기 매트릭스는 `Load_Initial_LLR_Matrix` 단계에서 멈춘다
- ㉰ **9번의 13곳 가운데 10곳이 `floor_flag` 값을 이웃 그룹에서 베껴 온다.** [DAO_Main.py:2397](5_DAO/SRC/DAO_Main.py#L2397), [2621](5_DAO/SRC/DAO_Main.py#L2621), [2829](5_DAO/SRC/DAO_Main.py#L2829), [3257](5_DAO/SRC/DAO_Main.py#L3257), [3387](5_DAO/SRC/DAO_Main.py#L3387), [3618](5_DAO/SRC/DAO_Main.py#L3618), [4931](5_DAO/SRC/DAO_Main.py#L4931), [4960](5_DAO/SRC/DAO_Main.py#L4960), [5889](5_DAO/SRC/DAO_Main.py#L5889), [6261](5_DAO/SRC/DAO_Main.py#L6261), [10203](5_DAO/SRC/DAO_Main.py#L10203)이 그렇다. 지금은 모든 값이 -1이라 베껴도 맞지만, 이 칸이 분기 index가 되면 **다른 분기에 속한 그룹의 분기 번호를 그대로 베껴 넣는다.** 유효성 검사가 분기 규칙을 모르면 조용히 잘못된 매트릭스가 만들어진다
- ㉱ [DAO_Main.py:3618](5_DAO/SRC/DAO_Main.py#L3618)과 [DAO_Main.py:10203](5_DAO/SRC/DAO_Main.py#L10203)은 베낄 원본이 없을 때 `else 0`으로 떨어진다. 0은 지금 유효성 규칙(-1이어야 함)을 통과하지 못한다. `-1`이라는 값이 이름 없는 숫자로 세 파일에 흩어져 있어 이런 어긋남이 눈에 띄지 않는다

### 5.2 `LLR_Header`에 그룹당 값 배열을 하나 더할 때 손대는 자리

필수 산출물 ㉲의 뒤쪽이다.

| # | 자리 | 위치 | 고칠 줄 수 |
|---|------|------|----------|
| 1 | dataclass 정의 | [DAO_LLR_MATRIX.py:9-21](5_DAO/SRC/DAO_LLR_MATRIX.py#L9) | 1 |
| 2 | 파서의 줄 순서 (`idx_line` 순차 증가) | [DAO_LLR_MATRIX.py:476-492](5_DAO/SRC/DAO_LLR_MATRIX.py#L476) | 1 |
| 3 | 파서의 `LLR_Header(...)` 위치 인자 11개 | [DAO_LLR_MATRIX.py:494-506](5_DAO/SRC/DAO_LLR_MATRIX.py#L494) | 1 |
| 4 | 출력 헤더 줄 목록 | [DAO_LLR_MATRIX.py:122-146](5_DAO/SRC/DAO_LLR_MATRIX.py#L122) | 1 |
| 5 | 유효성 길이 검사 (`num_group != len(...)` 형태) | [DAO_LLR_MATRIX.py:271-284](5_DAO/SRC/DAO_LLR_MATRIX.py#L271) | 1 |
| 6 | 외부 매트릭스 헤더 호환성 검사 | [DAO_Main.py:4261-4276](5_DAO/SRC/DAO_Main.py#L4261) | 1 |
| 7 | 로그 요약 도우미의 헤더 필드 나열 11개 | [DAO_Main.py:93-105](5_DAO/SRC/DAO_Main.py#L93) | 1 |
| 8 | 그룹을 넣고 빼는 8곳에서 배열 갱신 | [DAO_Main.py:2711-2713](5_DAO/SRC/DAO_Main.py#L2711), [3069-3071](5_DAO/SRC/DAO_Main.py#L3069), [3433-3438](5_DAO/SRC/DAO_Main.py#L3433), [3575-3577](5_DAO/SRC/DAO_Main.py#L3575), [5108-5132](5_DAO/SRC/DAO_Main.py#L5108), [5618-5620](5_DAO/SRC/DAO_Main.py#L5618), [5912-5914](5_DAO/SRC/DAO_Main.py#L5912), [6323-6325](5_DAO/SRC/DAO_Main.py#L6323) | 8 |
| 9 | 그룹당 행 수만 고치는 3곳 (배열 길이는 그대로) | [DAO_Main.py:2471](5_DAO/SRC/DAO_Main.py#L2471), [3277](5_DAO/SRC/DAO_Main.py#L3277), [8921](5_DAO/SRC/DAO_Main.py#L8921) | 0 |
| 10 | 그룹 하나로 갈아엎는 도우미 | [DAO_Main.py:3570-3580](5_DAO/SRC/DAO_Main.py#L3570) | 1 |
| (문서) | `DAO_spec.md` 2.2 표, `README.md` | | 2 |

**합계: 10종 22곳** (문서 2곳 제외).

8번이 핵심이다. 그룹을 넣거나 빼는 8곳이 각자 `num_group`, `num_row_each_group`, `type_each_group`, `restart_iter`, `num_restart`를 손으로 맞춘다. 여덟 자리가 쓰는 방식이 서로 다르다.

| 자리 | 하는 일 | 배열 갱신 방식 |
|------|--------|--------------|
| [2711-2721](5_DAO/SRC/DAO_Main.py#L2711) INSERT_RANDOM_GROUP | 그룹 삽입 | `np.insert`, restart는 `np.append` 후 `np.sort` |
| [3069-3078](5_DAO/SRC/DAO_Main.py#L3069) INSERT_MUTATED_GROUP | 그룹 삽입 | 위와 같은 코드 (사실상 복제) |
| [3433-3439](5_DAO/SRC/DAO_Main.py#L3433) SPLIT_GROUP | 그룹 삽입 | `np.insert`, type은 원본 type 복사 |
| [3575-3579](5_DAO/SRC/DAO_Main.py#L3575) `_Replace_With_Single_Group` | 전체 교체 | `np.array([...])`로 새로 만듦, restart 비움 |
| [5108-5132](5_DAO/SRC/DAO_Main.py#L5108) REORDER_GROUP | 순서 재배열 | 목록 재조립 후 `np.array` |
| [5618-5620](5_DAO/SRC/DAO_Main.py#L5618) DELETE_ROW의 그룹 삭제 | 그룹 삭제 | `num_row_each_group`은 재계산, `type_each_group`은 `np.delete` |
| [5912-5914](5_DAO/SRC/DAO_Main.py#L5912) INSERT_RESTART_GROUP | 그룹 삽입 | `num_row_each_group`은 재계산, `type_each_group`은 `np.insert` |
| [6323-6325](5_DAO/SRC/DAO_Main.py#L6323) reorder 시험 매트릭스 | 전체 재구성 | 둘 다 재계산 |

같은 일(그룹 하나 삽입)을 네 자리가 세 가지 방식으로 한다. 배열이 하나 늘면 여덟 자리 모두에 한 줄씩 더해야 하고, 한 곳이라도 빠지면 그 배열만 길이가 어긋난다. 5번의 유효성 검사가 길이를 보긴 하지만, 그건 매트릭스가 다 만들어진 뒤다.

### 처방 R8-1: row 꼬리 칸을 이름으로 읽는다

**우선순위: 상** (SW 분기 DAO 작업 **전에**)

**구체 처방.** [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py) 상단에 꼬리 칸 이름 목록을 두고 파서가 그것으로 자르게 한다.

```python
ROW_TAIL_FIELD_NAMES = ("CSW", "iter_start", "iter_end", "floor_flag")

# Read_Input_LLR_Matrix 안에서
num_tail = len(ROW_TAIL_FIELD_NAMES)
ch_th_values = row[:-num_tail]
tail = dict(zip(ROW_TAIL_FIELD_NAMES, (int(v) for v in row[-num_tail:])))
```

`Build_LLR_Matrix_Output_Lines`의 출력 쪽도 같은 목록을 돌게 한다. 그러면 칸을 더할 때 목록에 이름 하나를 더하는 것으로 읽기와 쓰기가 동시에 맞는다.

**위험.** 동작 변경 없음 (같은 값을 같은 순서로 읽는다). 옆 세션 충돌 낮음이되 **먼저 하는 편이 낫다.** 이 처방이 먼저 들어가면 SW 분기 쪽은 `ROW_TAIL_FIELD_NAMES`에 `"sw_branch_idx"`를 더하고 `floor_flag`를 빼는 것으로 파서와 출력이 한꺼번에 맞는다.

### 처방 R8-2: 출력 줄의 차이 표시를 도우미 하나로 묶는다

**우선순위: 상** (SW 분기 DAO 작업 **전에**)

**구체 처방.** [DAO_LLR_MATRIX.py:176-193](5_DAO/SRC/DAO_LLR_MATRIX.py#L176)의 3갈래 18줄을 도우미 하나로 바꾼다.

```python
def _format_row_field(value, opt_value, has_compare_target, width=4):
    """optimal 매트릭스와 다른 값에 * 를 붙여 고정 너비로 찍는다."""
    text = f"{value:{width}d}" if width else f"{value}"
    if has_compare_target and (opt_value is None or value != opt_value):
        return text + "*"
    return text
```

호출부는 `ROW_TAIL_FIELD_NAMES`를 돌며 이 도우미를 부른다. 필드가 늘어도 호출부가 늘지 않는다.

**위험.** 동작 변경 없음 (세 갈래의 현재 결과가 이 한 식과 같다는 것을 확인했다: `compare_with`가 있고 `opt_row`가 없으면 항상 `*`, 있으면 값이 다를 때만 `*`, `compare_with`가 없으면 `*` 없음). 출력 파일이 바뀌지 않는지 기존 매트릭스 하나로 대조 시험을 한 번 돌린다. 옆 세션 충돌 낮음.

### 처방 R8-3: 그룹 구조 변경을 헤더 도우미 세 개로 모은다

**우선순위: 상** (SW 분기 DAO 작업 **전에**)

**구체 처방.** [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py)에 `LLR_MATRIX`의 메서드로 다음 셋을 만든다.

- 1. `Insert_Group_Into_Header(self, position, num_rows, group_type, restart_iteration=None)`: `num_group` 증가, `num_row_each_group`과 `type_each_group`에 `np.insert`, restart면 `restart_iter`와 `num_restart` 갱신. 현재 [2711-2721](5_DAO/SRC/DAO_Main.py#L2711), [3069-3078](5_DAO/SRC/DAO_Main.py#L3069), [3433-3439](5_DAO/SRC/DAO_Main.py#L3433), [5912-5914](5_DAO/SRC/DAO_Main.py#L5912)가 이것이다
- 2. `Delete_Group_From_Header(self, position)`: 현재 [5618-5620](5_DAO/SRC/DAO_Main.py#L5618)이 이것이다
- 3. `Rebuild_Header_Group_Arrays(self, group_types=None)`: `self.groups`를 진실로 보고 그룹당 배열을 다시 만든다. 현재 [3575-3579](5_DAO/SRC/DAO_Main.py#L3575), [5108-5132](5_DAO/SRC/DAO_Main.py#L5108), [6323-6325](5_DAO/SRC/DAO_Main.py#L6323)가 이것이다

여덟 자리를 이 셋의 호출로 바꾸면, 그룹당 배열이 하나 늘 때 고칠 자리가 여덟 곳에서 **세 곳**으로 준다.

**위험.** 동작 변경 가능. 여덟 자리가 `type_each_group`에 넣는 값이 서로 다르다 (2713과 3071은 상수 1, 3438은 원본 그룹의 type 복사, 5113-5132는 목록 재조립, 6324는 별도 계산한 `new_types`). **옮기기 전에 여덟 자리의 현재 값 계산을 표로 대조해야 한다.** 옆 세션 충돌은 높지만, 이 처방이 먼저 들어가면 SW 분기 쪽이 여덟 자리 대신 세 자리만 고치면 되므로 **순서를 먼저로 잡는 것이 전체 비용을 줄인다.** 옆 세션과 순서를 협의해야 하는 항목이다.

### 처방 R8-4: row 필드 규칙을 이름 붙인 함수로 뽑는다

**우선순위: 상** (SW 분기 DAO 작업 **전에**)

**구체 처방.** [DAO_LLR_MATRIX.py:344-346](5_DAO/SRC/DAO_LLR_MATRIX.py#L344)의

```python
if row.floor_flag != -1:
    output_msg = f"Group {g_idx} Row {r} invalid floor_flag {row.floor_flag}"
    return False, output_msg
```

를 `_Check_Row_Tail_Fields(self, row, group_idx, row_idx) -> Optional[str]`로 뽑고, 상수 `FLOOR_FLAG_UNUSED = -1`에 이름을 붙인다. 아울러 `floor_flag` 값을 이웃에서 베끼는 11곳([5.1절 ㉰](#51-llr_row에-칸을-하나-더할-때-손대는-자리)) 대신 `LLR_Row`의 기본값(`floor_flag: int = FLOOR_FLAG_UNUSED`)을 쓰게 한다.

**위험.** 동작 변경 없음. **이 처방이 SW 분기 작업의 진입점이 된다.** 규칙이 이름 붙은 한 함수에 모여 있으면 SW 분기는 그 함수 안에서 "마지막 칸은 그 그룹의 `sw_branch_idx_each_group` 값과 같아야 한다"로 다시 쓰면 된다. 지금처럼 규칙이 유효성 함수 한가운데 박혀 있으면 그 함수 전체(184줄)를 읽어야 한다.

### 처방 R8-5: 로그 요약 도우미가 필드를 자동으로 돌게 한다

**우선순위: 중**

**구체 처방.** [DAO_Main.py:93-118](5_DAO/SRC/DAO_Main.py#L93)의 `header_summary`(11필드 손으로 나열)와 `row_summary`(6필드 손으로 나열)를 `dataclasses.fields()`로 도는 코드로 바꾼다. `from dataclasses import is_dataclass, fields, dataclass`는 이미 [DAO_Main.py:6](5_DAO/SRC/DAO_Main.py#L6)에 있다.

```python
header_summary = {
    f.name: _summarize_value(getattr(header, f.name), depth + 1)
    for f in fields(header)
}
```

**위험.** 동작 변경 있음(출력 형식만). 지금은 `num_parameter_each_set` 같은 int를 요약 없이 그대로 찍고 배열만 `_summarize_value`를 거치는데, 자동화하면 int도 `_summarize_value`를 거친다. `_summarize_value`는 int를 그대로 돌려주므로([DAO_Main.py:68](5_DAO/SRC/DAO_Main.py#L68)) 결과는 같다. 필드 순서는 dataclass 선언 순서로 나온다. 옆 세션 충돌 없음.

### 처방 R8-6: copy 후보를 dict 대신 dataclass로 담는다

**우선순위: 중**

**구체 처방.** `Get_Copy_Row_Candidates`([DAO_Main.py:4383-4387](5_DAO/SRC/DAO_Main.py#L4383)), `_Load_External_Single_Row_Candidates`([DAO_Main.py:4339-4343](5_DAO/SRC/DAO_Main.py#L4339)), `Get_Copy_Group_Candidates`([DAO_Main.py:4428-4434](5_DAO/SRC/DAO_Main.py#L4428))가 각자 만드는 dict를 dataclass 둘로 바꾼다.

```python
@dataclass
class Row_Copy_Candidate:
    ch_th_values: np.ndarray
    source_group_idx: int      # -1 이면 외부 파일에서 온 후보
    source_row_idx: int

@dataclass
class Group_Copy_Candidate:
    rows: list[LLR_Row]
    source_group_idx: int
    group_type: int
```

소비하는 쪽은 `Copy_Row`([DAO_Main.py:8845-8862](5_DAO/SRC/DAO_Main.py#L8845))와 `Copy_Group`([DAO_Main.py:8900-8923](5_DAO/SRC/DAO_Main.py#L8900))이다. `Group_Copy_Candidate.rows`를 dict 목록 대신 `LLR_Row` 목록으로 담으면, row에 칸이 늘어도 `Copy_Group`이 고칠 것이 없어진다.

**위험.** 동작 변경 가능. 후보 목록은 MPI bcast로 전파된다(`Gen_Trial_LLR` [DAO_Main.py:2030](5_DAO/SRC/DAO_Main.py#L2030), [2034](5_DAO/SRC/DAO_Main.py#L2034)). dict에서 dataclass로 바뀌면 pickle 대상이 바뀌므로 bcast 전후 값을 한 번 대조해야 한다. 옆 세션 충돌 중간.

---

## 6. 처방 적용 순서

화살표는 "앞의 것이 먼저"를 뜻한다.

### 6.1 다른 팀, 다른 세션의 판정을 기다려야 하는 것

- 1. **L팀 판정 -> R2-1**: `Set_Update_Flags`(11개)와 `Print_Test_Summary`(10개) 목록 가운데 `INSERT_RESTART_GROUP`이 어느 쪽에 있어야 맞는지 정해야 표로 합칠 수 있다
- 2. **L팀 판정 -> R2-3**: `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`의 올바른 값을 정해야 열거형 목록으로 선언할 수 있다
- 3. **R8-1, R8-2, R8-3, R8-4 -> 옆 세션 SW 분기 DAO 작업**: 이 넷이 먼저 들어가면 SW 분기 쪽이 고칠 자리가 29곳에서 약 10곳으로, 22곳에서 약 12곳으로 준다. 특히 R8-3은 옆 세션과 순서를 협의해야 하는 항목이다
- 4. **옆 세션 SW 분기 DAO 작업 -> R1-1의 11번(MULTIROUND), 12번(GEN), R7-4**: 이 셋은 SW 분기가 고치는 파일과 정면으로 겹친다

### 6.2 이 팀 안의 순서

```
R7-3 (순위 루프 변수 이름)          독립, 언제든
R8-5 (로그 요약 자동화)             독립, 언제든

R1-1 1~5번 (LOG, FLAG, CSWLOG, MPI, PATH 분리)
   └-> R7-1 (MPI 초기화를 DAO_MPI_Communication.py로)
          └-> R7-2 (별표 import 정리)

R1-1 6~10번 (ECC+SPEED, RESULT, UNCOR, PRINT, SINGLEROW 분리)

R8-1 (row 꼬리 이름) ┐
R8-2 (차이 표시 도우미) ┤-> 옆 세션 SW 분기 DAO 작업
R8-3 (헤더 도우미 3개) ┤       └-> R1-1 11~12번 -> R1-2 (상태 객체화)
R8-4 (row 규칙 함수)   ┘       └-> R7-4 (데이터 모델 설정 분리)

L팀 판정 -> R2-1 (모드 사양 표) -> R2-2 (함수 객체 디스패치)
L팀 판정 -> R2-3 (모드 시퀀스 열거형)
R8-6 (copy 후보 dataclass)  R1-1 12번 뒤가 편하다 (같은 파일을 만진다)
```

### 6.3 우선순위 묶음

| 우선순위 | 처방 | 근거 |
|---------|------|------|
| 상 | R8-1, R8-2, R8-3, R8-4 | 옆 세션이 지금 하려는 일의 비용을 직접 줄인다. 늦으면 이득이 사라진다 |
| 상 | R1-1 1~10번 | 3,762줄을 옮겨 `DAO_Main.py`를 6,600줄대로 줄인다. 충돌 위험이 없다 |
| 상 | R2-1, R7-1 | 새 모드 추가 비용을 15곳에서 5곳으로, MPI 초기화를 드러나게 한다 |
| 중 | R1-1 11~12번, R2-2, R2-3, R7-2, R7-3, R7-4, R8-5, R8-6 | 선행 조건이 있거나 효과가 위의 것보다 작다 |
| 중 | R1-2 | 가장 큰 구조 변경이고 동작 변경 위험이 있다. 나머지가 끝난 뒤에 한다 |

---

## 부록 A: `LLR_OPT` 메서드 212개 전수 분류표

필수 산출물 ㉮다. 책임군 순서는 [2.1절](#21-책임군-16개)의 중요도를 따르고, 군 안에서는 줄 번호 순이다.

"주로 읽고 쓰는 `self` 속성" 열은 쓰기를 `=` 표시로 먼저 적고 읽기를 뒤에 적었다. 모든 메서드가 쓰는 `is_root`, `rank`, `comm`, `num_process`는 표에서 뺐다. 속성이 많으면 쓰기 6개와 읽기 7개까지만 적고 "외"로 줄였다.

| 메서드 | 줄 | 줄수 | 책임군 | 주로 읽고 쓰는 `self` 속성 (`=` 표시는 쓰기) |
|--------|-----|------|--------|----------------------------------------|
| `Gen_Trial_LLR` | 1950-2034 | 85 | 최적화 루프 | `copy_group_candidates=`, `copy_row_candidates=`, `current_LLR_matrix=`, `generate_LLR_success=`, `target_group_indices=`, `current_LLR_matrix_idx`, `current_gen_trial_LLR_mode`, `current_trial_idx`, `optimal_LLR_matrix`, `trial_output_dir` |
| `Initialize_Stage` | 2247-2310 | 64 | 최적화 루프 | `current_stage_idx=`, `current_target_idx=`, `is_current_stage_enable_max_stage_time_limit=`, `target_group_indices=`, `temp_optimal_LLR_matrix=`, `current_gen_trial_LLR_mode`, `optimal_LLR_matrix` |
| `Initialize_LLR_Matrix` | 2312-2341 | 30 | 최적화 루프 | `initial_LLR_matrix=`, `target_group_indices=`, `current_LLR_matrix`, `is_current_LLR_valid`, `local_session_dir`, `trial_output_dir` |
| `Initialize_Trial` | 2343-2359 | 17 | 최적화 루프 | `current_LLR_matrix_idx=`, `current_trial_idx=`, `current_stage_idx`, `max_modification_trial` |
| `Run_Initial_Test` | 7771-7815 | 45 | 최적화 루프 | `total_num_uncors=`, `current_LLR_matrix`, `current_seed_mode`, `current_test_mode`, `initial_LLR_matrix` |
| `Run_Optimization` | 8003-8187 | 185 | 최적화 루프 | `current_test_mode=`, `is_previous_trial_updated=`, `log_has_update=`, `update_mode=`, `_last_speed_test_time`, `current_LLR_matrix`, `current_gen_trial_LLR_mode`, `current_gen_trial_LLR_mode_name`, `is_current_stage_enable_max_stage_time_limit`, `max_modification_trial` |
| `Set_Gen_Trial_LLR_Mode` | 8293-8447 | 155 | 최적화 루프 | `current_gen_trial_LLR_mode=`, `current_gen_trial_LLR_mode_index=`, `current_gen_trial_LLR_mode_name=`, `current_target_group_idx=`, `current_target_group_list_index=`, `max_modification_trial=`, `current_stage_idx`, `optimal_LLR_matrix`, `target_group_indices` |
| `Test_LLR` | 8937-9009 | 73 | 최적화 루프 | `current_seed_mode`, `current_test_mode`, `is_test_end` |
| `_Run_Test_Stage` | 9217-9221 | 5 | 최적화 루프 | `current_test_mode=` |
| `Test_Initial_LLR` | 9223-9283 | 61 | 최적화 루프 | `current_seed_mode=`, `current_test_mode=`, `current_LLR_matrix`, `total_num_partial_uncors` |
| `Test_Trial_LLR` | 9479-9542 | 64 | 최적화 루프 | `current_LLR_matrix`, `current_gen_trial_LLR_mode` |
| `_get_new_CSW` | 732-752 | 21 | LLR 생성 모드 | (없음) |
| `_generate_random_row` | 754-785 | 32 | LLR 생성 모드 | (없음) |
| `Generate_Initial_Random_Row` | 2036-2053 | 18 | LLR 생성 모드 | `initial_LLR_matrix` |
| `Insert_Random_Row` | 2361-2472 | 112 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Insert_Random_Group` | 2585-2790 | 206 | LLR 생성 모드 | `insert_group_add_restart=`, `target_group_indices=`, `current_target_group_idx`, `current_trial_idx`, `max_modification_trial` |
| `Gen_LLR_Insert_Mutated_Group` | 2792-3134 | 343 | LLR 생성 모드 | `insert_group_add_restart=`, `target_group_indices=`, `current_target_group_idx`, `current_trial_idx`, `max_modification_trial` |
| `Gen_LLR_Insert_Mutated_Row` | 3136-3286 | 151 | LLR 생성 모드 | `current_target_group_idx`, `current_trial_idx` |
| `_recalculate_group_iterations` | 3288-3325 | 38 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Split_Group` | 3327-3470 | 144 | LLR 생성 모드 | `target_group_indices=`, `current_target_group_idx` |
| `_generate_mutation_for_group` | 3472-3521 | 50 | LLR 생성 모드 | (없음) |
| `_generate_mutation_for_row` | 3523-3568 | 46 | LLR 생성 모드 | (없음) |
| `_Replace_With_Single_Group` | 3570-3580 | 11 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Gen_Initial_Group` | 3582-3653 | 72 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Insert_Random_Row` | 3655-3699 | 45 | LLR 생성 모드 | `current_target_group_idx`, `current_trial_idx` |
| `Gen_LLR_Mutate_CSW` | 3701-3729 | 29 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Mutate_Matrix` | 3731-3800 | 70 | LLR 생성 모드 | `is_mutate_matrix_tuning_phase=`, `max_possible_tuning_mutation_count=`, `prev_generated_mutation=`, `tuning_mutation_count=`, `tuning_mutations=`, `current_trial_idx`, `is_previous_trial_updated` |
| `Generate_All_Fine_Tuning_Mutations` | 3802-3847 | 46 | LLR 생성 모드 | (없음) |
| `Generate_All_Coarse_Tuning_Mutations` | 3849-3891 | 43 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Regen_DV` | 3893-4041 | 149 | LLR 생성 모드 | `gen_DV_idx=`, `is_replace_DV_in_Ch_Th_reuse_mode=`, `previous_dv_segment=`, `current_target_group_idx`, `current_trial_idx`, `is_previous_trial_updated` |
| `Gen_LLR_Regen_Row` | 4043-4167 | 125 | LLR 생성 모드 | `gen_row_idx=`, `is_gen_row_reuse_mode=`, `previous_gen_row=`, `current_target_group_idx`, `current_trial_idx`, `is_previous_trial_updated` |
| `Gen_LLR_Copy_Rows` | 4169-4204 | 36 | LLR 생성 모드 | `copy_row_candidates=`, `current_target_group_idx`, `current_trial_idx` |
| `Gen_LLR_Copy_Group` | 4206-4234 | 29 | LLR 생성 모드 | `copy_group_candidates=`, `current_trial_idx` |
| `Get_Mutate_Matrix_Skip_Row_Idx` | 4236-4244 | 9 | LLR 생성 모드 | `CSW_update_limit_value` |
| `_List_LLR_Matrix_Files` | 4247-4259 | 13 | LLR 생성 모드 | (없음) |
| `_Check_Header_Compatibility` | 4261-4276 | 16 | LLR 생성 모드 | (없음) |
| `_Load_External_Single_Row_Candidates` | 4278-4366 | 89 | LLR 생성 모드 | `_external_row_cache=` |
| `Get_Copy_Row_Candidates` | 4368-4403 | 36 | LLR 생성 모드 | (없음) |
| `Get_Copy_Group_Candidates` | 4405-4444 | 40 | LLR 생성 모드 | `current_target_group_idx` |
| `_create_restart_group` | 5728-5754 | 27 | LLR 생성 모드 | (없음) |
| `Gen_LLR_Swap_Row` | 6329-6405 | 77 | LLR 생성 모드 | `current_target_group_idx`, `current_trial_idx` |
| `Generate_Random_Mutation` | 7021-7095 | 75 | LLR 생성 모드 | `current_target_group_idx`, `now_enable_CSW_update_limit` |
| `Mutate_Matrix_Setup` | 7097-7098 | 2 | LLR 생성 모드 | (없음) |
| `Mutate_CSW` | 7100-7180 | 81 | LLR 생성 모드 | `current_target_group_idx` |
| `Copy_Row` | 8812-8863 | 52 | LLR 생성 모드 | `copy_row_candidates`, `current_target_group_idx` |
| `Copy_Group` | 8865-8925 | 61 | LLR 생성 모드 | `copy_group_candidates`, `current_target_group_idx` |
| `Init_Reorder_Group_Mode` | 4446-4523 | 78 | 멀티라운드 상태기계 | `current_target_idx`, `optimal_LLR_matrix`, `reorder_state`, `target_group_indices` |
| `Init_Adjust_Iteration_Mode` | 4525-4602 | 78 | 멀티라운드 상태기계 | `adjust_iter_state`, `optimal_LLR_matrix`, `target_group_indices` |
| `Build_Adjusted_Iteration_Matrix` | 4604-4735 | 132 | 멀티라운드 상태기계 | `target_group_indices` |
| `Update_Reorder_Round_Result` | 4737-4798 | 62 | 멀티라운드 상태기계 | `reorder_state` |
| `Finalize_Reorder_Round` | 4800-4847 | 48 | 멀티라운드 상태기계 | `reorder_state` |
| `Build_Reordered_Matrix` | 4849-5159 | 311 | 멀티라운드 상태기계 | `current_LLR_matrix_idx`, `optimal_LLR_matrix`, `reorder_state`, `target_group_indices` |
| `Gen_LLR_Reorder_Group` | 5161-5298 | 138 | 멀티라운드 상태기계 | `current_trial_idx`, `reorder_state` |
| `Gen_LLR_Adjust_Iteration` | 5300-5389 | 90 | 멀티라운드 상태기계 | `adjust_iter_state`, `temp_optimal_LLR_matrix` |
| `Init_Delete_Row_Mode` | 5393-5430 | 38 | 멀티라운드 상태기계 | `delete_row_state=`, `max_modification_trial=`, `optimal_LLR_matrix` |
| `_Build_Delete_Row_Candidates` | 5432-5450 | 19 | 멀티라운드 상태기계 | `target_group_indices` |
| `Gen_LLR_Delete_Row` | 5452-5520 | 69 | 멀티라운드 상태기계 | `delete_row_state` |
| `_Build_Deleted_Row_Matrix` | 5522-5549 | 28 | 멀티라운드 상태기계 | (없음) |
| `_Delete_Entire_Group` | 5551-5645 | 95 | 멀티라운드 상태기계 | (없음) |
| `Update_Delete_Row_Round_Result` | 5647-5685 | 39 | 멀티라운드 상태기계 | `delete_row_state` |
| `_Finalize_Delete_Row_Round` | 5687-5726 | 40 | 멀티라운드 상태기계 | `delete_row_state` |
| `Init_Insert_Restart_Group_Mode` | 5758-5784 | 27 | 멀티라운드 상태기계 | `insert_restart_group_state=`, `max_modification_trial=`, `optimal_LLR_matrix` |
| `_Build_Insert_Restart_Candidates` | 5786-5815 | 30 | 멀티라운드 상태기계 | `target_group_indices` |
| `Gen_LLR_Insert_Restart_Group` | 5817-5868 | 52 | 멀티라운드 상태기계 | `insert_restart_group_state` |
| `_Build_Inserted_Restart_Matrix` | 5870-5939 | 70 | 멀티라운드 상태기계 | (없음) |
| `Update_Insert_Restart_Group_Round_Result` | 5941-5976 | 36 | 멀티라운드 상태기계 | `insert_restart_group_state` |
| `_Finalize_Insert_Restart_Group_Round` | 5978-6016 | 39 | 멀티라운드 상태기계 | `insert_restart_group_state` |
| `_is_reorder_candidate_better` | 6018-6086 | 69 | 멀티라운드 상태기계 | (없음) |
| `_is_reorder_candidate_equal` | 6088-6116 | 29 | 멀티라운드 상태기계 | (없음) |
| `_recalculate_iterations_for_reorder` | 6118-6193 | 76 | 멀티라운드 상태기계 | (없음) |
| `_create_reorder_test_matrix` | 6195-6327 | 133 | 멀티라운드 상태기계 | (없음) |
| `_Get_Compare_Target` | 1146-1155 | 10 | 갱신 판정 | `is_update_at_last_trial`, `optimal_LLR_matrix`, `temp_optimal_LLR_matrix` |
| `Determine_Update_Decision` | 1398-1442 | 45 | 갱신 판정 | `current_LLR_matrix`, `current_gen_trial_LLR_mode`, `current_trial_idx`, `is_update_at_last_trial`, `max_modification_trial`, `optimal_LLR_matrix`, `temp_optimal_LLR_matrix` |
| `Check_Partial_Improvement` | 1444-1488 | 45 | 갱신 판정 | `current_LLR_matrix`, `current_trial_idx`, `is_update_at_last_trial`, `max_modification_trial`, `optimal_LLR_matrix`, `temp_optimal_LLR_matrix` |
| `Is_Current_LLR_Valid` | 2474-2497 | 24 | 갱신 판정 | `is_current_LLR_valid=`, `current_LLR_matrix_idx`, `generate_LLR_success` |
| `Is_List_A_Strictly_Better` | 2499-2513 | 15 | 갱신 판정 | (없음) |
| `Is_Matrix_Better` | 2515-2545 | 31 | 갱신 판정 | (없음) |
| `Save_LLR_Matrix` | 8277-8283 | 7 | 갱신 판정 | (없음) |
| `Set_Update_Flags` | 8614-8643 | 30 | 갱신 판정 | `is_update_at_last_trial=`, `current_gen_trial_LLR_mode` |
| `Set_Optimal_Matrix` | 8645-8657 | 13 | 갱신 판정 | (없음) |
| `Set_Previous_Optimal_Matrix` | 8659-8683 | 25 | 갱신 판정 | `previous_optimal_LLR_matrix=`, `optimal_LLR_matrix`, `temp_optimal_LLR_matrix`, `update_mode` |
| `Set_Current_Optimal_Matrix` | 8685-8703 | 19 | 갱신 판정 | `optimal_LLR_matrix=`, `temp_optimal_LLR_matrix=`, `current_LLR_matrix`, `update_mode` |
| `Update_Current_LLR` | 9544-9546 | 3 | 갱신 판정 | `current_LLR_matrix=`, `current_LLR_matrix_idx=` |
| `Update_Optimal_LLR` | 9548-9608 | 61 | 갱신 판정 | `is_previous_trial_updated=`, `log_has_update=`, `optimal_LLR_matrix=`, `target_group_indices=`, `temp_optimal_LLR_matrix=`, `update_mode=`, `optimal_output_dir` |
| `_Promote_Temp_Optimal_On_Stage_Exit` | 9610-9645 | 36 | 갱신 판정 | `log_has_update=`, `optimal_LLR_matrix=`, `previous_optimal_LLR_matrix=`, `temp_optimal_LLR_matrix=`, `update_mode=`, `is_update_at_last_trial`, `optimal_output_dir` |
| `Validate_LLR_Matrix` | 9902-9913 | 12 | 갱신 판정 | `is_current_LLR_valid=`, `current_LLR_matrix`, `session_error_dir` |
| `Count_Gathered_Uncors` | 1022-1043 | 22 | uncor 풀 | (없음) |
| `Copy_Uncors` | 1248-1305 | 58 | uncor 풀 | `session_uncor_dir`, `total_num_uncors` |
| `Delete_Uncors` | 1490-1513 | 24 | uncor 풀 | (없음) |
| `Delete_Own_Uncors` | 1515-1529 | 15 | uncor 풀 | `is_current_core_excluded`, `local_session_dir` |
| `Distribute_Uncors_To_Local_Session` | 1531-1590 | 60 | uncor 풀 | `excluded_cores`, `has_uncor` |
| `Gather_And_Archive_Uncors` | 2089-2152 | 64 | uncor 풀 | `excluded_cores`, `session_uncor_dir`, `total_num_uncors` |
| `Process_Uncors` | 7313-7345 | 33 | uncor 풀 | `total_num_uncors=` |
| `Ensure_Uncors_Loaded` | 7347-7384 | 38 | uncor 풀 | `current_loaded_test_mode=`, `is_uncor_pool_ready` |
| `_Setup_Uncor_Pool_For_Channel` | 7386-7458 | 73 | uncor 풀 | `excluded_cores`, `pool_has_uncor` |
| `Setup_Uncor_Pool` | 7460-7489 | 30 | uncor 풀 | `is_uncor_pool_ready=`, `total_num_uncors=` |
| `_Get_Tmp_Partial_Uncor_Dir` | 7491-7503 | 13 | uncor 풀 | `session_uncor_dir` |
| `Load_Uncors_From_Pool` | 7505-7543 | 39 | uncor 풀 | `current_loaded_test_mode=`, `has_uncor`, `is_current_core_excluded`, `local_session_dir`, `pool_has_uncor` |
| `Update_Uncors_To_Input` | 7817-7911 | 95 | uncor 풀 | `optimal_LLR_matrix`, `session_dir` |
| `Setup_Uncors` | 8716-8744 | 29 | uncor 풀 | `is_uncor_pool_ready`, `total_num_uncors` |
| `_Redistribute_Uncor_Pool_Uniform` | 9158-9214 | 57 | uncor 풀 | `current_loaded_test_mode=`, `is_uncor_pool_ready=`, `pool_has_uncor=`, `session_uncor_dir` |
| `_Build_Initial_Partial_Pool` | 9285-9348 | 64 | uncor 풀 | `total_num_uncors=`, `current_LLR_matrix`, `total_num_partial_uncors` |
| `Rebuild_Partial_Pool` | 9350-9455 | 106 | uncor 풀 | `current_loaded_test_mode=`, `current_seed_mode=`, `current_test_mode=`, `optimal_LLR_matrix=`, `total_num_uncors=`, `total_num_partial_uncors` |
| `_Signal_Graceful_Stop_No_Partial` | 9457-9477 | 21 | uncor 풀 | (없음) |
| `_Is_Channel_Degraded` | 1157-1178 | 22 | Ref-C 결과 집계 | `current_test_mode` |
| `_Fill_Untested_Channels` | 1180-1196 | 17 | Ref-C 결과 집계 | `current_test_mode` |
| `Gather_Ref_C_Results` | 1784-1937 | 154 | Ref-C 결과 집계 | `current_test_mode`, `excluded_cores`, `is_current_core_excluded`, `local_session_dir`, `total_FER_per_iters`, `total_num_error_per_iters`, `total_num_errors` 외 |
| `Reset_Optimal_Results` | 7957-7969 | 13 | Ref-C 결과 집계 | `current_seed_mode`, `optimal_LLR_matrix` |
| `Read_FER_From_File` | 7971-8001 | 31 | Ref-C 결과 집계 | (없음) |
| `Read_Ref_C_Result` | 8189-8275 | 87 | Ref-C 결과 집계 | (없음) |
| `Build_ECC` | 846-933 | 88 | Ref-C 실행 | (없음) |
| `Get_Ref_C_Args` | 6407-6454 | 48 | Ref-C 실행 | `current_seed_mode`, `enable_print_CSW_log` |
| `Get_Ref_C_Args_For_Speed_Test` | 6456-6504 | 49 | Ref-C 실행 | (없음) |
| `Make_Batch_File_For_Speed_Test` | 6506-6536 | 31 | Ref-C 실행 | `batch_path=`, `local_session_dir` |
| `Make_Batch_File` | 6538-6571 | 34 | Ref-C 실행 | `batch_path=`, `local_session_dir` |
| `Run_ECC` | 7913-7955 | 43 | Ref-C 실행 | `batch_path`, `has_uncor`, `is_current_core_excluded` |
| `Set_Test_Environment` | 8449-8478 | 30 | Ref-C 실행 | `_last_saved_local_matrix_idx=`, `ecc_start_time=`, `is_test_end=`, `current_seed_mode`, `local_session_dir` |
| `Finalize_ECC_Time` | 8480-8489 | 10 | Ref-C 실행 | `ecc_elapsed_time=`, `ecc_end_time=`, `ecc_start_time` |
| `Set_Seed_Mode` | 8491-8551 | 61 | Ref-C 실행 | `current_seed_mode=`, `current_gen_trial_LLR_mode` |
| `Set_Max_Error` | 8553-8576 | 24 | Ref-C 실행 | `max_error=`, `current_seed_mode` |
| `Set_Enable_Print_CSW_LOG` | 8578-8594 | 17 | Ref-C 실행 | `enable_print_CSW_log=` |
| `Set_Ref_C_Parameters` | 8596-8612 | 17 | Ref-C 실행 | (없음) |
| `Set_Loop_Start_Time` | 8927-8929 | 3 | Ref-C 실행 | `loop_start_time=` |
| `Calc_Loop_Elapsed_Time` | 8930-8935 | 6 | Ref-C 실행 | `loop_elapsed_time=`, `loop_end_time=`, `loop_end_time_stamp=`, `total_elapsed_time=`, `ecc_start_time`, `loop_start_time` |
| `Bcast_Trial_LLR_Mode` | 818-844 | 27 | MPI 통신 | `current_gen_trial_LLR_mode=`, `current_gen_trial_LLR_mode_index=`, `current_gen_trial_LLR_mode_name=`, `current_target_group_idx=`, `current_target_group_list_index=`, `max_modification_trial=` |
| `MPI_Barrier` | 6685-6695 | 11 | MPI 통신 | `barrier_count=` |
| `Check_Barrier_Sync` | 6698-6741 | 44 | MPI 통신 | `barrier_count` |
| `Write_MPI_Error_Snapshot` | 6743-6798 | 56 | MPI 통신 | `optimal_LLR_matrix`, `session_error_dir` |
| `MPI_Abort` | 6800-6894 | 95 | MPI 통신 | `_in_mpi_abort=`, `session_dir` |
| `_mpi_comm_with_timeout` | 6896-6944 | 49 | MPI 통신 | (없음) |
| `_safe_bcast` | 6946-6969 | 24 | MPI 통신 | (없음) |
| `_safe_gather` | 6971-6995 | 25 | MPI 통신 | (없음) |
| `MPI_Debug_Logging` | 6997-7019 | 23 | MPI 통신 | `barrier_count` |
| `_collect_error_state_snapshot` | 651-700 | 50 | 로그 기록 | `__dict__` |
| `_write_debug_snapshot` | 702-730 | 29 | 로그 기록 | `session_debug_snapshot_dir` |
| `_append_lines_without_rotation` | 787-816 | 30 | 로그 기록 | `log_line_count=`, `_in_mpi_abort`, `log_file_path` |
| `Debug_Pause` | 1346-1396 | 51 | 로그 기록 | `debug_cnt=`, `debug_is_init=`, `work_space_dir` |
| `Get_Timestamp` | 1939-1948 | 10 | 로그 기록 | (없음) |
| `Get_Log_File_Name` | 2181-2198 | 18 | 로그 기록 | (없음) |
| `Initialize_Log` | 2200-2245 | 46 | 로그 기록 | `log_create_time=`, `log_file_path=`, `log_has_update=`, `log_line_count=`, `log_start_matrix_idx=`, `start_time_str=`, `session_logs_dir`, `session_timestamp`, `simulation_start` 외 |
| `Log_Unhandled_Exception` | 2547-2559 | 13 | 로그 기록 | `session_dir` |
| `Make_Log_Backup` | 6621-6657 | 37 | 로그 기록 | `log_create_time=`, `log_file_path=`, `log_has_update=`, `log_line_count=`, `log_start_matrix_idx=`, `_in_mpi_abort`, `current_LLR_matrix_idx`, `session_logs_dir` |
| `Finalize_Log` | 6659-6683 | 25 | 로그 기록 | `log_file_path=`, `current_LLR_matrix_idx`, `log_create_time`, `log_has_update`, `log_start_matrix_idx`, `session_logs_dir` |
| `Write_Log_Separator` | 9915-9925 | 11 | 로그 기록 | (없음) |
| `Write_Log_Lines` | 9927-9960 | 34 | 로그 기록 | `log_file_path`, `log_line_count`, `update_log_file_path` |
| `Get_Channel_Param_String` | 1630-1660 | 31 | 보고 출력 | (없음) |
| `Get_Test_Mode_String` | 1662-1673 | 12 | 보고 출력 | `current_test_mode` |
| `Get_Decoder_Mode_Str` | 2055-2070 | 16 | 보고 출력 | (없음) |
| `Get_Mode_Sequence_Str` | 7182-7192 | 11 | 보고 출력 | `current_gen_trial_LLR_mode_index` |
| `Get_Target_Group_Indices_Str` | 7194-7203 | 10 | 보고 출력 | `current_target_group_list_index`, `target_group_indices` |
| `Print_Initial_Setup` | 7205-7209 | 5 | 보고 출력 | (없음) |
| `Print_Mode_Target_Info` | 7211-7218 | 8 | 보고 출력 | `current_gen_trial_LLR_mode`, `current_gen_trial_LLR_mode_name`, `current_target_group_idx`, `is_update_at_last_trial` |
| `Print_Stage_Info` | 7220-7259 | 40 | 보고 출력 | `current_gen_trial_LLR_mode`, `current_gen_trial_LLR_mode_name`, `current_stage_idx` |
| `Print_Config` | 7261-7268 | 8 | 보고 출력 | (없음) |
| `Print_Configs` | 7270-7278 | 9 | 보고 출력 | (없음) |
| `Print_Final_Optimal_LLR_Results` | 7280-7282 | 3 | 보고 출력 | `optimal_LLR_matrix` |
| `Print_LLR_Matrix` | 7284-7311 | 28 | 보고 출력 | `optimal_LLR_matrix` |
| `Print_Test_Result` | 7545-7615 | 71 | 보고 출력 | `current_test_mode`, `loop_elapsed_time`, `loop_end_time`, `total_FER_per_iters`, `total_elapsed_time`, `total_num_error_per_iters`, `total_num_raw_errors` 외 |
| `Print_Test_Summary` | 7617-7769 | 153 | 보고 출력 | `current_LLR_matrix`, `current_gen_trial_LLR_mode`, `initial_LLR_matrix`, `optimal_LLR_matrix`, `previous_optimal_LLR_matrix`, `temp_optimal_LLR_matrix`, `update_mode` |
| `Cleanup_Test_Environment` | 935-964 | 30 | 세션 경로와 정리 | `local_session_dir` |
| `_Cleanup_LLR_Matrix_Files` | 966-975 | 10 | 세션 경로와 정리 | `_last_saved_local_matrix_idx=`, `local_session_dir` |
| `Cleanup_Session` | 977-1020 | 44 | 세션 경로와 정리 | `session_dir` |
| `Copy_ECC_EXE` | 1307-1332 | 26 | 세션 경로와 정리 | `local_session_dir` |
| `Copy_H_Matrix` | 1334-1344 | 11 | 세션 경로와 정리 | `local_session_dir` |
| `Get_CSW_Log_File_Name` | 1592-1602 | 11 | 세션 경로와 정리 | (없음) |
| `Get_Result_File_Name` | 1604-1628 | 25 | 세션 경로와 정리 | (없음) |
| `Get_Uncor_File_Name` | 2072-2087 | 16 | 세션 경로와 정리 | (없음) |
| `Get_Local_Session_Dir` | 2154-2163 | 10 | 세션 경로와 정리 | `session_dir` |
| `Make_Dirs` | 6573-6619 | 47 | 세션 경로와 정리 | `end_flag_dir=`, `local_session_dir=`, `optimal_output_dir=`, `session_debug_snapshot_dir=`, `session_dir=`, `session_error_dir=`, `input_args`, `session_timestamp` 외 |
| `Set_Work_Space` | 8786-8793 | 8 | 세션 경로와 정리 | (없음) |
| `BACKUP_SRC` | 8795-8810 | 16 | 세션 경로와 정리 | `src_backup_dir` |
| `_Export_Workspace_To_Input` | 10371-10399 | 29 | 세션 경로와 정리 | `single_row_candidates_dir` |
| `Check_Test_End` | 1045-1069 | 25 | 종료 플래그 파일 | `is_test_end=`, `max_error`, `total_num_errors` |
| `_Write_End_Flag` | 1071-1079 | 9 | 종료 플래그 파일 | (없음) |
| `_Write_End_Flag_Count` | 1081-1089 | 9 | 종료 플래그 파일 | (없음) |
| `_Read_End_Flag` | 1091-1097 | 7 | 종료 플래그 파일 | (없음) |
| `Write_Run_ECC_End_Flag` | 1099-1100 | 2 | 종료 플래그 파일 | (없음) |
| `Read_Run_ECC_End_Flag` | 1102-1103 | 2 | 종료 플래그 파일 | `is_test_end=` |
| `_Read_End_Flag_Count` | 1105-1115 | 11 | 종료 플래그 파일 | (없음) |
| `Read_Trial_End_Flag` | 1117-1119 | 3 | 종료 플래그 파일 | (없음) |
| `Read_DAO_End_Flag` | 1121-1123 | 3 | 종료 플래그 파일 | (없음) |
| `_Write_Stop_Idx` | 1125-1134 | 10 | 종료 플래그 파일 | `end_flag_dir` |
| `_Read_Stop_Idx` | 1136-1144 | 9 | 종료 플래그 파일 | `end_flag_dir` |
| `_Write_Run_ECC_End_Ack` | 1198-1209 | 12 | 종료 플래그 파일 | `end_flag_dir`, `is_current_core_excluded` |
| `_Report_Missing_Acks` | 1211-1246 | 36 | 종료 플래그 파일 | `end_flag_dir`, `excluded_cores` |
| `Initialize_Run_ECC_End_Flag` | 2165-2170 | 6 | 종료 플래그 파일 | `end_flag_dir` |
| `Initialize_End_Flags` | 2172-2179 | 8 | 종료 플래그 파일 | `end_flag_dir` |
| `Gather_CSW_Logs` | 1675-1762 | 88 | CSW 로그 | `current_test_mode`, `excluded_cores`, `optimal_output_dir` |
| `Delete_CSW_Logs` | 1764-1781 | 18 | CSW 로그 | `excluded_cores` |
| `Process_CSW_Logs` | 9011-9018 | 8 | CSW 로그 | `enable_print_CSW_log` |
| `Test_Core_Speed` | 9020-9098 | 79 | 코어 속도 테스트 | `_last_speed_test_time=`, `core_elapsed_times=`, `current_seed_mode=`, `excluded_cores=`, `is_current_core_excluded=`, `current_LLR_matrix` |
| `Periodic_Recheck` | 9100-9125 | 26 | 코어 속도 테스트 | (없음) |
| `_Recheck_Speed_Test` | 9127-9156 | 30 | 코어 속도 테스트 | `is_current_core_excluded=`, `current_LLR_matrix`, `excluded_cores`, `local_session_dir` |
| `Run_Single_Row_Generation` | 10027-10190 | 164 | 단일 row 생성 모드 | `_gen_single_row_stop_idx=`, `_last_saved_local_matrix_idx=`, `current_test_mode=`, `enable_print_CSW_log=`, `single_row_candidates_dir=`, `_last_speed_test_time`, `is_test_end`, `local_session_dir`, `session_dir` |
| `Build_Single_Row_Matrix` | 10192-10229 | 38 | 단일 row 생성 모드 | `initial_LLR_matrix` |
| `Parse_CSW_Min_Values` | 10231-10254 | 24 | 단일 row 생성 모드 | `excluded_cores` |
| `_Save_Top_K_Matrices` | 10256-10269 | 14 | 단일 row 생성 모드 | (없음) |
| `Rank_And_Save_Single_Row_Candidates` | 10271-10369 | 99 | 단일 row 생성 모드 | `single_row_candidates_dir` |
| `__init__` | 482-570 | 89 | 수명주기와 설정 검증 | `_current_initial_matrix_idx=`, `_in_mpi_abort=`, `_last_speed_test_time=`, `adjust_iter_state=`, `barrier_count=`, `base_seed=` 외 |
| `_init_per_matrix_state` | 572-625 | 54 | 수명주기와 설정 검증 | `_external_row_cache=`, `_last_saved_local_matrix_idx=`, `copy_group_candidates=`, `copy_row_candidates=`, `current_LLR_matrix=`, `current_gen_trial_LLR_mode=` 외 |
| `is_load_seed_mode` | 630-636 | 7 | 수명주기와 설정 검증 | `current_seed_mode` |
| `is_load_uncor_seed_file_mode` | 639-644 | 6 | 수명주기와 설정 검증 | `current_seed_mode` |
| `active_cores` | 647-649 | 3 | 수명주기와 설정 검증 | `excluded_cores` |
| `Load_Initial_LLR_Matrix` | 2561-2583 | 23 | 수명주기와 설정 검증 | `initial_LLR_matrix=`, `_current_initial_matrix_idx` |
| `Set_CSW_Update_Limit` | 8285-8291 | 7 | 수명주기와 설정 검증 | `CSW_update_limit_value=`, `now_enable_CSW_update_limit=` |
| `Setup` | 8705-8714 | 10 | 수명주기와 설정 검증 | `_current_initial_matrix_idx=`, `session_timestamp=`, `simulation_start=` |
| `Set_Python_Seed` | 8746-8756 | 11 | 수명주기와 설정 검증 | `base_seed=` |
| `Restore_Random_State_If_Configured` | 8758-8784 | 27 | 수명주기와 설정 검증 | (없음) |
| `Validate_Config` | 9647-9900 | 254 | 수명주기와 설정 검증 | `initial_LLR_matrix`, `target_group_indices` |
| `_Reset_For_Next_Matrix` | 9963-9971 | 9 | 수명주기와 설정 검증 | (없음) |
| `_Run_Exit_After_Multi_Matrix` | 9973-9999 | 27 | 수명주기와 설정 검증 | `_current_initial_matrix_idx=` |
| `Main` | 10001-10025 | 25 | 수명주기와 설정 검증 | (없음) |
