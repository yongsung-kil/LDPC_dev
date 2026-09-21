# Worker T-2: Two-stage와 승격 (P6, P7, P8)

> 시작 시점 커밋: 6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정
> 기록: 2026-09-21 15:15:17

대상 파일: [DAO_Main.py](5_DAO/SRC/DAO_Main.py) (10,428줄), [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py), [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py)

## 발견 요약

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|----------|------|
| T2-1 | CRITICAL | Partial uncor가 0개가 되어 정상 종료를 시그널한 뒤에도 trial이 한 번 더 돌아 빈 Partial pool로 테스트하고 `Gather_Ref_C_Results`가 `total_tests=0`으로 `MPI_Abort` 한다 | [DAO_Main.py:9457](5_DAO/SRC/DAO_Main.py#L9457), [DAO_Main.py:8070](5_DAO/SRC/DAO_Main.py#L8070), [DAO_Main.py:10017](5_DAO/SRC/DAO_Main.py#L10017) | `ENABLE_TWO_STAGE_TEST=True`이고 어떤 매트릭스가 Full uncor를 전부 복호했을 때 | trial 루프 시작 지점과 `Run_Initial_Test`와 `Run_Optimization` 사이에서 DAO 종료 플래그를 읽어 곧바로 빠져나간다 |
| T2-2 | HIGH | `Rebuild_Partial_Pool`이 Partial 0개로 조기 반환할 때 Step 7(상태 복원)을 건너뛰어 `current_seed_mode`가 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로 고착하고 `current_test_mode`, `current_loaded_test_mode`, `optimal.FERs_partial`도 복원되지 않는다 | [DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426), [DAO_Main.py:9443](5_DAO/SRC/DAO_Main.py#L9443), [DAO_Main.py:8504](5_DAO/SRC/DAO_Main.py#L8504) | 위와 같은 조건 | 상태 복원을 try와 finally로 감싸고, 복원값은 고정 상수 대신 진입 시점 값을 저장해 되돌린다 |
| T2-3 | MEDIUM | 초기 테스트 직후 `Update_Optimal_LLR(is_initial=True)`가 `Rebuild_Partial_Pool`을 불러 같은 매트릭스로 Full 테스트를 한 번 더 수행한다 | [DAO_Main.py:9603](5_DAO/SRC/DAO_Main.py#L9603), [DAO_Main.py:9266](5_DAO/SRC/DAO_Main.py#L9266) | `ENABLE_TWO_STAGE_TEST=True`로 최적화를 시작할 때마다 | Rebuild 조건에 `and not is_initial`을 넣는다 |
| T2-4 | MEDIUM | Partial에서 걸러진 trial도 멀티라운드 round result 갱신 함수에 넘어가, 측정되지 않은 FER 1.0과 avg_iter -1.0이 baseline과 비교된다 | [DAO_Main.py:8047](5_DAO/SRC/DAO_Main.py#L8047), [DAO_Main.py:5670](5_DAO/SRC/DAO_Main.py#L5670) | `ENABLE_TWO_STAGE_TEST=True`, DELETE_ROW 또는 INSERT_RESTART_GROUP stage에서 Partial 개선이 없는 trial | round result 갱신을 `should_check_update`로 가드한다 |
| T2-5 | MEDIUM | DELETE_ROW와 INSERT_RESTART_GROUP의 `max_modification_trial`이 final verification trial 한 칸을 포함하지 않아, 모든 라운드가 개선되면 최종 검증이 실행되지 않는다 | [DAO_Main.py:5415](5_DAO/SRC/DAO_Main.py#L5415), [DAO_Main.py:5772](5_DAO/SRC/DAO_Main.py#L5772) | 삭제 후보 N개가 모두 라운드마다 개선을 내는 경우 | `max_trials = N * (N + 1) // 2 + 1` |
| T2-6 | MEDIUM | `Rebuild_Partial_Pool`이 `total_num_uncors`를 Partial 수로 덮어쓰고 Full 수를 복원하지 않는다 | [DAO_Main.py:9410](5_DAO/SRC/DAO_Main.py#L9410), [DAO_Main.py:2144](5_DAO/SRC/DAO_Main.py#L2144) | Two-stage 모드에서 optimal이 갱신될 때마다 | 진입 시점 값을 저장했다가 Step 7에서 되돌리거나, `Gather_And_Archive_Uncors`가 개수를 반환값으로만 넘기게 한다 |
| T2-7 | MEDIUM | 강제 종료 시 Full 강제 수행 경로가 `_Run_Test_Stage`를 쓰지 않고 준비 단계를 손으로 복제한다 | [DAO_Main.py:8098](5_DAO/SRC/DAO_Main.py#L8098), [DAO_Main.py:9217](5_DAO/SRC/DAO_Main.py#L9217) | 시간 제한, DAO 종료 플래그, trial 종료 플래그 가운데 하나가 Partial 스킵 trial에서 걸릴 때 | `self._Run_Test_Stage(TestMode.FULL, self.current_LLR_matrix, enable_early_channel_exit=True)` 한 줄로 교체한다 |
| T2-8 | LOW | `Print_Test_Summary`의 모드 목록에 INSERT_RESTART_GROUP이 빠져 `Set_Update_Flags` 목록과 어긋나고, 그 stage에서 Temp Opt 줄이 출력되지 않는다 | [DAO_Main.py:7632](5_DAO/SRC/DAO_Main.py#L7632), [DAO_Main.py:8625](5_DAO/SRC/DAO_Main.py#L8625) | INSERT_RESTART_GROUP stage의 모든 trial | 목록을 `DAO_Constants.py`의 `UPDATE_AT_LAST_TRIAL_MODES` 상수로 올리고 두 곳이 그것을 참조한다 |
| T2-9 | LOW | `_Promote_Temp_Optimal_On_Stage_Exit`가 `update_mode`를 root에만 설정하고, `Update_Optimal_LLR`이 수행하는 `target_group_indices` 정리를 하지 않는다 | [DAO_Main.py:9610](5_DAO/SRC/DAO_Main.py#L9610), [DAO_Main.py:9570](5_DAO/SRC/DAO_Main.py#L9570) | 안전망 승격이 일어나는 stage | 승격 후 뒷처리를 공용 함수로 뽑아 양쪽에서 부른다 |
| T2-10 | LOW | 사용자가 DAO 종료 플래그를 세워 멈출 때도 `Rebuild_Partial_Pool`이 Full 테스트를 한 번 더 수행한다 | [DAO_Main.py:9606](5_DAO/SRC/DAO_Main.py#L9606), [DAO_Main.py:9643](5_DAO/SRC/DAO_Main.py#L9643) | 강제 종료 trial에서 optimal이 갱신될 때 | 강제 종료가 확정된 경우 Rebuild를 건너뛴다 (Partial pool은 다음 실행이 다시 만든다) |

## 발견 상세

### T2-1 (CRITICAL) Partial uncor 0개 정상 종료가 MPI_Abort로 끝난다

**현상**

`_Signal_Graceful_Stop_No_Partial` ([DAO_Main.py:9457](5_DAO/SRC/DAO_Main.py#L9457))은 DAO 종료 플래그 파일을 쓰는 것으로 정상 종료를 알린다. 그런데 이 플래그를 읽는 자리가 늦다.

- ㉮ `Main` ([DAO_Main.py:10001](5_DAO/SRC/DAO_Main.py#L10001))은 `Run_Initial_Test()` 다음에 곧바로 `Run_Optimization()`을 부르며 그 사이에서 플래그를 읽지 않는다
- ㉯ `Run_Optimization`의 trial 루프는 `Test_Trial_LLR()`을 마친 뒤 ([DAO_Main.py:8044](5_DAO/SRC/DAO_Main.py#L8044)) 에야 플래그를 읽는다 ([DAO_Main.py:8070](5_DAO/SRC/DAO_Main.py#L8070))

그래서 "Partial pool이 비었다"는 결론이 난 뒤에도 최소 한 번의 Partial 테스트가 더 실행된다.

**터지는 지점**

- 1. `_Setup_Uncor_Pool_For_Channel`이 빈 소스로 불려 `pool_has_uncor[PARTIAL]`이 전 rank, 전 채널에서 False가 된다 ([DAO_Main.py:7458](5_DAO/SRC/DAO_Main.py#L7458))
- 2. 다음 trial의 `_Run_Test_Stage(TestMode.PARTIAL, ...)`가 `Load_Uncors_From_Pool(PARTIAL)`을 부르고 모든 rank의 `has_uncor[ch]`가 False가 된다 ([DAO_Main.py:7521](5_DAO/SRC/DAO_Main.py#L7521))
- 3. `Run_ECC`가 `is_load_uncor_seed_file_mode`와 `has_uncor[ch]=False`로 즉시 반환해 결과 파일을 만들지 않는다 ([DAO_Main.py:7932](5_DAO/SRC/DAO_Main.py#L7932))
- 4. 직전 `Cleanup_Test_Environment`가 result로 시작하는 파일을 이미 지웠으므로 ([DAO_Main.py:952](5_DAO/SRC/DAO_Main.py#L952), `HEADER_TO_REMOVE`는 [DAO_Constants.py:129](5_DAO/SRC/DAO_Constants.py#L129)) 읽을 파일이 남지 않는다
- 5. `Gather_Ref_C_Results(is_test_end=True)`의 Reduce 결과가 0이 되어 `total_tests == 0` 분기에서 `MPI_Abort` 한다 ([DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884))

**재현 조건**

`UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST=True`, `RUN_DAO_MODE=RUN_OPTIMIZATION`. 초기 매트릭스가 Full uncor를 전부 복호하면 `_Build_Initial_Partial_Pool`이 False를 돌려주고 ([DAO_Main.py:9341](5_DAO/SRC/DAO_Main.py#L9341)), 최적화 도중 갱신된 optimal이 전부 복호하면 `Rebuild_Partial_Pool`이 False를 돌려준다 ([DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426)). 두 경우 모두 같은 자리에서 끝난다.

**처방**

- ㉮ `LLR_OPT`에 `self.is_graceful_stop: bool = False`를 두고 `_Signal_Graceful_Stop_No_Partial`이 플래그 파일 기록과 함께 이 값을 True로 세운다 (모든 rank가 이 함수를 부르므로 값이 자동으로 일치한다)
- ㉯ `Run_Optimization`의 trial 루프에서 `self.Initialize_Trial(trial_idx)` 바로 다음에 `if self.is_graceful_stop: break`를 넣는다 ([DAO_Main.py:8026](5_DAO/SRC/DAO_Main.py#L8026) 부근)
- ㉰ stage 루프 시작부 `self.Periodic_Recheck(stage_idx)` 앞에도 같은 검사를 넣어 stage가 새로 열리지 않게 한다 ([DAO_Main.py:8019](5_DAO/SRC/DAO_Main.py#L8019))
- ㉱ `Main`에서 `self.Run_Initial_Test()` 다음에 `if not self.is_graceful_stop: self.Run_Optimization()`으로 감싼다 ([DAO_Main.py:10017](5_DAO/SRC/DAO_Main.py#L10017))

### T2-2 (HIGH) Rebuild_Partial_Pool 조기 반환이 seed mode와 test mode를 고착시킨다

`Rebuild_Partial_Pool`은 Step 1에서 `current_seed_mode`를 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로, Step 2에서 `current_test_mode`를 FULL로 바꾼 뒤 Step 7에서 되돌린다 ([DAO_Main.py:9443](5_DAO/SRC/DAO_Main.py#L9443)). 그런데 Partial 수가 0이면 Step 6과 Step 7에 닿기 전에 `return False` 한다 ([DAO_Main.py:9426](5_DAO/SRC/DAO_Main.py#L9426)).

남는 결과는 다음과 같다.

- ㉮ `current_seed_mode`가 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로 남는다. `Set_Seed_Mode`는 이 값을 만나면 분기 전체를 건너뛰고 그대로 보존하므로 ([DAO_Main.py:8504](5_DAO/SRC/DAO_Main.py#L8504)) 이후 모든 테스트가 fail seed 저장 모드로 돈다
- ㉯ `current_test_mode`가 FULL로 남아 호출 직전의 stage 값을 잃는다
- ㉰ `current_loaded_test_mode`가 초기화되지 않아 다음 `Ensure_Uncors_Loaded`가 재로드를 건너뛸 수 있다
- ㉱ Step 6이 건너뛰어져 `optimal_LLR_matrix.FERs_partial`이 1.0으로 맞춰지지 않는다. Dynamic Partial은 "optimal의 partial FER은 1.0"을 전제로 `Check_Partial_Improvement`가 비교하므로 ([DAO_Main.py:1468](5_DAO/SRC/DAO_Main.py#L1468)), 이 값이 1.0 미만으로 남으면 이후 Partial 판정 기준이 어긋난다

복원값을 `SeedMode.LOAD_UNCOR_SEED`로 고정한 점도 `UNCOR_CONFIG.LOAD_UNCOR_MODE=LOAD_VECTOR` 설정에서는 틀린 값이다. 다음 `Test_LLR`이 `Set_Seed_Mode`를 불러 `LOAD_UNCOR_VECTOR`로 고쳐 주므로 지금은 드러나지 않지만, 복원 책임이 두 곳으로 갈라져 있다.

**처방**

`Rebuild_Partial_Pool` 본문을 아래 구조로 다시 쓴다.

- 1. 함수 시작에서 `prev_seed_mode = self.current_seed_mode`, `prev_test_mode = self.current_test_mode`를 저장한다
- 2. Step 1부터 Step 6까지를 try 블록에 넣는다
- 3. finally 블록에서 `current_test_mode = prev_test_mode`, `current_loaded_test_mode = None`, `current_seed_mode = prev_seed_mode`를 되돌리고 root 기준 값을 bcast 한다
- 4. Partial 수가 0일 때도 `optimal_LLR_matrix.FERs_partial`을 1.0으로 맞추도록 Step 6을 조기 반환 앞으로 옮긴다

### T2-3 (MEDIUM) 초기 테스트가 두 번 돈다

`Test_Initial_LLR`은 Full 테스트를 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로 수행하고 `_Build_Initial_Partial_Pool`로 Partial pool을 만든다 ([DAO_Main.py:9247](5_DAO/SRC/DAO_Main.py#L9247) 이후). 그 직후 `Run_Initial_Test`가 `Update_Optimal_LLR(is_initial=True)`를 부르고 ([DAO_Main.py:7800](5_DAO/SRC/DAO_Main.py#L7800)), `Determine_Update_Decision`은 `is_initial=True`에서 항상 `OPTIMAL_MATRIX_FROM_CURRENT`를 돌려준다 ([DAO_Main.py:1399](5_DAO/SRC/DAO_Main.py#L1399)). 그 결과 `Update_Optimal_LLR` 끝의 Rebuild 조건이 성립해 ([DAO_Main.py:9603](5_DAO/SRC/DAO_Main.py#L9603)) 방금 테스트한 것과 같은 매트릭스로 Full 테스트가 한 번 더 실행된다.

Full 테스트는 uncor 전체를 다시 돌리므로 시작 비용이 두 배가 된다. 같은 seed 집합을 쓰므로 결과 값 자체는 달라지지 않는다.

**처방**

[DAO_Main.py:9603](5_DAO/SRC/DAO_Main.py#L9603)의 조건을 `if (UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST and not is_initial and self.update_mode in (...))`로 고친다. 초기 pool은 `_Build_Initial_Partial_Pool`이 이미 만들어 두었다.

### T2-4 (MEDIUM) Partial에서 걸러진 trial이 round result 비교에 들어간다

`Run_Optimization`은 `Test_Trial_LLR()`의 반환값과 무관하게 멀티라운드 갱신 함수를 부른다 ([DAO_Main.py:8047](5_DAO/SRC/DAO_Main.py#L8047)).

```python
should_check_update = self.Test_Trial_LLR()
if self.current_gen_trial_LLR_mode in MULTI_ROUND_MODES:
    ...
    getattr(self, update_func_name)(self.current_LLR_matrix)
```

Partial에서 개선이 없어 Full을 건너뛰면 `current_LLR_matrix.FERs`는 `Gen_Trial_LLR`의 `Deep_Copy(copy_raw_FER=False, copy_seed_FER=False)`가 넣은 1.0 그대로이고 ([DAO_LLR_MATRIX.py:246](5_DAO/SRC/DAO_LLR_MATRIX.py#L246)), `avg_iterations`는 -1.0이다. `Update_Delete_Row_Round_Result`는 이 값을 그대로 로그에 찍고 baseline과 비교한다 ([DAO_Main.py:5660](5_DAO/SRC/DAO_Main.py#L5660)).

- ㉮ 로그에 `FER=1.000000e+00, avg_iter=-1.00`이 실제 측정값처럼 남는다
- ㉯ baseline의 FER이 전 채널 1.0인 상태라면 `Is_Matrix_Better`가 `ENABLE_AVG_ITER_UPDATE` 타이브레이크로 들어가 avg_iter -1.0을 개선으로 읽는다 ([DAO_Main.py:2542](5_DAO/SRC/DAO_Main.py#L2542)). 이때 테스트되지 않은 매트릭스가 round best가 된다

**처방**

- ㉮ [DAO_Main.py:8051](5_DAO/SRC/DAO_Main.py#L8051)의 조건을 `if should_check_update and update_func_name and self.is_root and self.current_LLR_matrix is not None:`으로 고친다. state 동기화 bcast는 지금처럼 조건 밖에 둔다
- ㉯ `Is_Matrix_Better`의 avg_iter 타이브레이크 앞에서 두 매트릭스 가운데 하나라도 `avg_iterations`에 음수가 있으면 False를 돌려주도록 한다 ([DAO_Main.py:2542](5_DAO/SRC/DAO_Main.py#L2542))

### T2-5 (MEDIUM) 멀티라운드 상한이 final verification trial을 포함하지 않는다

`Init_Delete_Row_Mode`는 후보 N개로 `max_trials = N * (N + 1) // 2`를 잡는다 ([DAO_Main.py:5415](5_DAO/SRC/DAO_Main.py#L5415)). 라운드 k의 후보 수가 N-k로 줄고 모든 라운드가 개선을 내면 후보 테스트에만 정확히 N(N+1)/2 trial이 쓰인다. `Gen_LLR_Delete_Row`의 final verification은 `current_candidate_idx`가 후보 수에 도달한 다음 호출에서 baseline을 돌려주므로 ([DAO_Main.py:5471](5_DAO/SRC/DAO_Main.py#L5471)) trial 번호 N(N+1)/2 + 1이 필요하다. trial 루프가 `range(1, max_modification_trial + 1)`이라 ([DAO_Main.py:8024](5_DAO/SRC/DAO_Main.py#L8024)) 그 trial이 실행되지 않는다.

이때 stage는 `_Promote_Temp_Optimal_On_Stage_Exit` 안전망으로만 마감된다 ([DAO_Main.py:8160](5_DAO/SRC/DAO_Main.py#L8160)). 안전망은 temp_optimal이 optimal보다 나을 때만 승격하므로 틀린 매트릭스가 남지는 않지만, 설계가 의도한 최종 검증 측정은 사라진다. `Init_Insert_Restart_Group_Mode`도 같은 식이다 ([DAO_Main.py:5772](5_DAO/SRC/DAO_Main.py#L5772)).

**처방**

두 곳의 `max_trials`를 `N * (N + 1) // 2 + 1`로 고친다. `DeleteRowState.total_expected_trials`와 `InsertRestartGroupState.total_expected_trials`도 같은 값을 받게 한다.

### T2-6 (MEDIUM) total_num_uncors가 Partial 수로 덮인 뒤 돌아오지 않는다

`Gather_And_Archive_Uncors`는 병합 결과를 세어 `self.total_num_uncors[ch_idx]`에 넣는다 ([DAO_Main.py:2144](5_DAO/SRC/DAO_Main.py#L2144)). `Rebuild_Partial_Pool`이 이 함수를 redecoded uncor에 대해 부르므로 ([DAO_Main.py:9385](5_DAO/SRC/DAO_Main.py#L9385)) Full 개수가 Partial 개수로 덮인다. 뒤이어 bcast 한 값을 `total_num_partial_uncors`에 복사할 뿐 ([DAO_Main.py:9410](5_DAO/SRC/DAO_Main.py#L9410)) Full 값을 되살리지 않는다.

Full 값이 다시 채워지는 자리는 `Copy_Uncors`뿐이고 ([DAO_Main.py:1303](5_DAO/SRC/DAO_Main.py#L1303)), 그것은 `Setup_Uncor_Pool`에서만 불린다 ([DAO_Main.py:7478](5_DAO/SRC/DAO_Main.py#L7478)). 최적화 도중에는 `Periodic_Recheck`가 `excluded_cores` 변경을 감지했을 때만 거기에 닿는다.

지금 `total_num_uncors`를 읽는 자리는 `Setup_Uncors`의 시작 검증 ([DAO_Main.py:8740](5_DAO/SRC/DAO_Main.py#L8740))과 로그 문자열뿐이라 동작에 직접 영향은 없다. 이름이 뜻하는 값과 실제 값이 어긋난 채로 오래 유지되는 상태 변수이므로 정리한다.

**처방**

`Gather_And_Archive_Uncors`가 개수를 반환값에 담아 넘기고 호출자가 목적에 맞는 변수에 넣게 한다. 당장은 `Rebuild_Partial_Pool`과 `_Build_Initial_Partial_Pool`에서 진입 전 `total_num_uncors`를 저장했다가 Partial 수를 `total_num_partial_uncors`에 옮긴 뒤 되돌린다.

### T2-7 (MEDIUM) 강제 종료 Full 수행 경로가 준비 단계를 복제한다

`_Run_Test_Stage`는 "test mode 설정, uncor 로드, Test_LLR"의 세 단계를 묶는다 ([DAO_Main.py:9217](5_DAO/SRC/DAO_Main.py#L9217)). 강제 종료 경로는 같은 세 줄을 직접 쓴다 ([DAO_Main.py:8098](5_DAO/SRC/DAO_Main.py#L8098)).

```python
self.current_test_mode = TestMode.FULL
self.Ensure_Uncors_Loaded(TestMode.FULL)
self.Test_LLR(self.current_LLR_matrix)
```

현재 이 세 줄은 `_Run_Test_Stage`와 정확히 같아 빠뜨린 준비 단계가 없다. 다만 `enable_early_channel_exit`를 넘기지 않아 다른 trial과 측정 조건이 다르고 (전 채널을 끝까지 재므로 결과 자체는 더 정확하다), 앞으로 `_Run_Test_Stage`에 단계가 늘면 이 경로만 빠진다.

**처방**

세 줄을 `self._Run_Test_Stage(TestMode.FULL, self.current_LLR_matrix, enable_early_channel_exit=True)` 한 줄로 바꾼다.

### T2-8 (LOW) 모드 목록이 두 곳에 따로 적혀 어긋난다

`Set_Update_Flags`가 `is_update_at_last_trial=True`로 잡는 모드 목록 ([DAO_Main.py:8625](5_DAO/SRC/DAO_Main.py#L8625))에는 `INSERT_RESTART_GROUP`이 들어 있고, `Print_Test_Summary`의 같은 목적 목록 ([DAO_Main.py:7632](5_DAO/SRC/DAO_Main.py#L7632))에는 빠져 있다. INSERT_RESTART_GROUP stage에서는 temp_optimal이 실제로 쓰이는데 요약에 Temp Opt 줄이 나오지 않아 승격 흐름을 로그로 추적할 수 없다.

**처방**

`DAO_Constants.py`에 `UPDATE_AT_LAST_TRIAL_MODES: set[int]`를 정의하고 두 함수가 그것을 참조한다. `MULTI_ROUND_MODES`와 `MULTI_ROUND_FULL_ONLY_MODES`가 이미 같은 파일에 있으므로 자리도 맞는다.

### T2-9 (LOW) 안전망 승격이 Update_Optimal_LLR과 부수 상태를 다르게 남긴다

`_Promote_Temp_Optimal_On_Stage_Exit` ([DAO_Main.py:9610](5_DAO/SRC/DAO_Main.py#L9610))는 승격 자체는 bcast로 맞추지만 다음 두 가지를 `Update_Optimal_LLR`과 다르게 처리한다.

- ㉮ `self.update_mode`와 `self.log_has_update`를 root에서만 세운다. `update_mode`는 다음 trial의 `Update_Optimal_LLR` 첫 줄이 전 rank에서 None으로 되돌리고 `log_has_update`는 호출 직후 bcast 되므로 ([DAO_Main.py:8163](5_DAO/SRC/DAO_Main.py#L8163)) 지금은 드러나지 않는다
- ㉯ `Update_Optimal_LLR`이 하는 `target_group_indices` 정리 ([DAO_Main.py:9570](5_DAO/SRC/DAO_Main.py#L9570))를 하지 않는다. 승격된 temp_optimal의 그룹 수가 더 적으면 범위를 벗어난 인덱스가 남는다. 다음 `Initialize_Stage`가 `optimal_LLR_matrix` 기준으로 다시 만들기 때문에 ([DAO_Main.py:2266](5_DAO/SRC/DAO_Main.py#L2266)) 지금은 드러나지 않는다

승격 경로가 둘인 채로 부수 상태 처리가 갈라져 있는 점이 문제다.

**처방**

`optimal_LLR_matrix` 교체 후의 공통 뒷처리(그룹 인덱스 정리, 저장, 로그 플래그, bcast)를 `_Apply_Optimal_Update(new_optimal, update_mode)` 한 함수로 뽑고 `Update_Optimal_LLR`과 `_Promote_Temp_Optimal_On_Stage_Exit`가 모두 그것을 부른다.

### T2-10 (LOW) 종료 요청 뒤에도 Full 테스트를 한 번 더 한다

사용자가 DAO 종료 플래그를 세우면 그 trial은 `is_forced_last_trial=True`로 `Update_Optimal_LLR`에 들어간다 ([DAO_Main.py:8113](5_DAO/SRC/DAO_Main.py#L8113)). 여기서 optimal이 갱신되면 `Rebuild_Partial_Pool`이 Full uncor 전체로 테스트를 한 번 더 돌린다 ([DAO_Main.py:9606](5_DAO/SRC/DAO_Main.py#L9606)). 이어서 `_Promote_Temp_Optimal_On_Stage_Exit`가 승격하면 또 한 번 돈다 ([DAO_Main.py:9643](5_DAO/SRC/DAO_Main.py#L9643)). 종료 요청에서 실제 종료까지 Full 테스트 한두 번의 시간이 더 걸린다.

**처방**

`Update_Optimal_LLR`에 `is_forced_last_trial`이 참이면 Rebuild를 건너뛰는 조건을 넣는다. Partial pool은 최적화를 이어갈 때만 필요하고 다음 실행이 `Test_Initial_LLR`에서 다시 만든다.

## 확인했으나 문제 없던 범위

- ㉮ **비교 대상의 일관성 (P6-㉯, P6-㉰)**: `_Get_Compare_Target` ([DAO_Main.py:1146](5_DAO/SRC/DAO_Main.py#L1146)), `Check_Partial_Improvement` ([DAO_Main.py:1444](5_DAO/SRC/DAO_Main.py#L1444)), `Determine_Update_Decision`의 중간 trial 분기 ([DAO_Main.py:1406](5_DAO/SRC/DAO_Main.py#L1406))가 모두 "`is_update_at_last_trial`이 참이고 temp_optimal이 있으면 temp_optimal, 아니면 optimal"이라는 같은 규칙을 쓴다.
- ㉯ **초기값 1.0이 비교 기준이 되는 경우 (P6-㉯)**: Dynamic Partial에서는 Partial pool이 optimal이 실패한 프레임 집합이므로 optimal의 partial FER이 1.0인 것이 정의상 맞다. `Test_Initial_LLR` Step 3 ([DAO_Main.py:9270](5_DAO/SRC/DAO_Main.py#L9270))과 `Rebuild_Partial_Pool` Step 6 ([DAO_Main.py:9435](5_DAO/SRC/DAO_Main.py#L9435))이 이 값을 명시로 1.0으로 맞추고, temp_optimal은 `copy_partial_FER=True`로 실측값을 넘겨받으므로 ([DAO_Main.py:8700](5_DAO/SRC/DAO_Main.py#L8700)) 초기값과 실측값이 섞이지 않는다. T2-2의 조기 반환 경로만 예외다.
- ㉰ **update_mode가 None인 채 Set_Optimal_Matrix에 닿는 경로 (P7-㉮)**: `Determine_Update_Decision`은 True를 돌려주는 모든 return에서 UpdateMode 값을 함께 준다. `Set_Optimal_Matrix`는 `now_optimal_LLR_update`가 참일 때만 불린다.
- ㉱ **생성 실패 직후 강제 종료에서의 비교 (P7-㉮)**: `Run_Optimization`은 `gen_success`가 거짓이면 continue로 trial을 건너뛰므로 ([DAO_Main.py:8038](5_DAO/SRC/DAO_Main.py#L8038)) 테스트되지 않은 `current_LLR_matrix`가 `Update_Optimal_LLR`에 들어가지 않는다. 이 경우는 `_Promote_Temp_Optimal_On_Stage_Exit`가 맡고, 그 함수는 current를 참조하지 않는다.
- ㉲ **안전망의 이중 승격 (P7-㉱, P7-㉳)**: `Is_Matrix_Better`는 FER의 Pareto 지배와 FER 동률 시 avg_iter 타이브레이크로 이루어져 추이적이다. 마지막 trial의 `Determine_Update_Decision`이 `best_candidate`를 optimal과 비교해 갱신하거나 갱신하지 않은 어느 쪽이든, 그 뒤 `Is_Matrix_Better(temp_optimal, optimal)`은 거짓이 된다. 같은 stage에서 두 번 승격되지 않는다.
- ㉳ **Initialize_Stage와 안전망의 순서 (P7-㉲)**: `_Promote_Temp_Optimal_On_Stage_Exit`는 trial 루프 종료 직후 ([DAO_Main.py:8160](5_DAO/SRC/DAO_Main.py#L8160)), `temp_optimal_LLR_matrix = None`은 다음 stage의 `Initialize_Stage` 앞부분 ([DAO_Main.py:2261](5_DAO/SRC/DAO_Main.py#L2261))이므로 안전망이 항상 먼저 돈다.
- ㉴ **REORDER_GROUP 전용 분기 (P7-㉵)**: `Determine_Update_Decision`이 REORDER_GROUP의 첫 trial에서 temp_optimal을 무조건 current로 세우지만 ([DAO_Main.py:1412](5_DAO/SRC/DAO_Main.py#L1412)), 마지막 trial에서 `best_candidate`를 optimal과 다시 비교하므로 나쁜 매트릭스가 optimal로 남지 않는다. 안전망도 같은 비교를 한다.
- ㉵ **Set_Previous_Optimal_Matrix와 Set_Current_Optimal_Matrix (P7-㉶)**: UpdateMode 세 값을 모두 다루고 그 밖의 값은 `MPI_Abort`로 막는다 ([DAO_Main.py:8659](5_DAO/SRC/DAO_Main.py#L8659), [DAO_Main.py:8685](5_DAO/SRC/DAO_Main.py#L8685)). 둘 다 root 안에서만 불리고 결과는 `Update_Optimal_LLR`이 bcast 한다. `previous_optimal_LLR_matrix`는 root 전용 로그에서만 읽으므로 bcast 하지 않아도 어긋나지 않는다.
- ㉶ **rank 사이 분기 일치 (P6 전반)**: `Test_Trial_LLR`의 분기 입력인 `current_gen_trial_LLR_mode`, 멀티라운드 `state.is_active`, `max_modification_trial`, `current_trial_idx`, 매트릭스의 FER 값이 모두 bcast 된 값이다. `Gather_Ref_C_Results`는 종료 집계를 Reduce 후 bcast 하므로 ([DAO_Main.py:1877](5_DAO/SRC/DAO_Main.py#L1877)) 전 rank의 FER이 같다. rank마다 Partial 스킵 여부가 갈리는 경로는 없다.
- ㉷ **Partial 스킵 시 current_test_mode (P6-㉲)**: `MULTI_ROUND_FULL_ONLY_MODES` 또는 `is_multi_round_final`로 Partial을 건너뛰면 곧바로 `_Run_Test_Stage(TestMode.FULL, ...)`가 `current_test_mode`를 FULL로 바꾼다 ([DAO_Main.py:9534](5_DAO/SRC/DAO_Main.py#L9534)).
- ㉸ **Rebuild_Partial_Pool의 재진입 (P8-㉯)**: 안에서 부르는 `Test_LLR`은 `Update_Optimal_LLR`을 부르지 않는다. `Update_Optimal_LLR` 호출 자리는 `Run_Initial_Test`와 `Run_Optimization` 두 곳뿐이다.
- ㉹ **_Signal_Graceful_Stop_No_Partial의 rank 일치 (P8-㉰)**: 판정에 쓰는 `total_partial`과 `total_partial_count`가 bcast 된 값이고, 함수 자체도 전 rank가 부르며 플래그 파일 기록만 root로 제한한다. 끝에 `MPI_Barrier`가 있어 집단 통신 횟수도 맞는다.
- ㉺ **Partial pool 재구성 뒤의 기준 불일치 (P6-㉵)**: temp_optimal만 갱신되는 중간 trial에서는 Rebuild가 실행되지 않고 ([DAO_Main.py:9603](5_DAO/SRC/DAO_Main.py#L9603)의 조건이 `TEMP_OPTIMAL_MATRIX_FROM_CURRENT`를 뺀다), optimal 갱신으로 Rebuild가 돈 뒤에는 stage가 끝나거나 다음 `Initialize_Stage`가 temp_optimal을 비운다. 서로 다른 uncor 집합에서 잰 두 Partial FER을 비교하는 자리는 찾지 못했다.
- ㉻ **current_test_mode와 current_loaded_test_mode의 어긋남 (P6-㉴)**: `_Redistribute_Uncor_Pool_Uniform`이 `current_loaded_test_mode`만 PARTIAL로 갱신하고 `current_test_mode`는 건드리지 않아 ([DAO_Main.py:9172](5_DAO/SRC/DAO_Main.py#L9172), [DAO_Main.py:9212](5_DAO/SRC/DAO_Main.py#L9212)) 둘이 잠시 어긋난다. 그 사이에 도는 `Initialize_Stage`, `Initialize_Trial`, `Gen_Trial_LLR`이 `current_test_mode`를 읽지 않고, 다음 `_Run_Test_Stage`가 두 값을 함께 맞추므로 지금은 동작에 영향이 없다.
