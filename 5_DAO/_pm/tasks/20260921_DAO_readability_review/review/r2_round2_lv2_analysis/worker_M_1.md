# worker_M_1: 팀 M (MPI 통신과 프로세스 수명) / 관점 P1 집단 통신의 rank 정합

- 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
- 작성: 2026-09-21
- 대상 파일: [DAO_Main.py](5_DAO/SRC/DAO_Main.py) (10,428줄), [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py), [DAO_Config.py](5_DAO/SRC/DAO_Config.py)

## 확인 범위

- ㉮ 집단 통신 호출 지점 전수: `MPI_Barrier` 32곳, `_safe_bcast` 44곳, `Bcast_Trial_LLR_Mode` 1곳,
  `comm.Reduce` 1곳, `comm.allgather` 3곳, `Check_Barrier_Sync` 2곳을 스크립트로 뽑아 각각의
  지배 조건(감싸고 있는 if, for, while)을 함께 확인했다
- ㉯ `if self.is_root:` 와 `if not self.is_root:` 블록 전수를 스크립트로 훑어 ㉠ 블록 안에서
  `return`, `break`, `continue` 로 빠지는 24곳 ㉡ 블록 안에 집단 통신이 들어 있는 곳을 조사했다
- ㉰ rank 0(root)과 rank 1(worker)의 통신 호출 순서를 따로 따라간 함수:
  `Main`, `Setup`, `Make_Dirs`, `Setup_Uncors`, `Setup_Uncor_Pool`, `Load_Uncors_From_Pool`,
  `Ensure_Uncors_Loaded`, `Test_Core_Speed`, `Run_Initial_Test`, `Test_Initial_LLR`,
  `_Build_Initial_Partial_Pool`, `Run_Optimization`, `Initialize_Stage`, `Initialize_Trial`,
  `Set_Gen_Trial_LLR_Mode`, `Gen_Trial_LLR`, `Test_Trial_LLR`, `Test_LLR`, `Set_Test_Environment`,
  `Gather_Ref_C_Results`, `Process_CSW_Logs`, `Update_Optimal_LLR`, `Rebuild_Partial_Pool`,
  `_Promote_Temp_Optimal_On_Stage_Exit`, `_Redistribute_Uncor_Pool_Uniform`, `Periodic_Recheck`,
  `Run_Single_Row_Generation`, `Debug_Pause`
- ㉱ 코드는 읽기만 했고 수정하지 않았다

## 발견 표

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|----------|------|
| 1 | CRITICAL | GEN_SINGLE_ROW 루프에서 각 rank가 DAO 종료 플래그 파일을 스스로 읽고 `break` 한다. rank마다 감지 시점이 한 주기 어긋나면 남은 rank의 bcast와 빠져나간 rank의 Barrier가 짝을 이루지 못한다 | [DAO_Main.py:10056-10067](5_DAO/SRC/DAO_Main.py#L10056) | `RUN_DAO_MODE=GEN_SINGLE_ROW`, 사용자가 `8_End_flag/` 에 DAO 종료 플래그를 쓰는 순간이 어느 rank의 파일 읽기와 겹칠 때 | root만 `Read_DAO_End_Flag()` 를 부르고 그 결과를 `_safe_bcast` 로 내린다. [DAO_Main.py:8071-8077](5_DAO/SRC/DAO_Main.py#L8071) 의 관용구를 그대로 옮긴다 |
| 2 | CRITICAL | Partial uncor 0개일 때의 "graceful stop" 이 실제로는 한 trial 더 진행한 뒤 `total_tests=0` MPI_Abort 로 끝난다 | [DAO_Main.py:9457-9477](5_DAO/SRC/DAO_Main.py#L9457), [DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884), [DAO_Main.py:8072-8077](5_DAO/SRC/DAO_Main.py#L8072) | `ENABLE_TWO_STAGE_TEST=True` 이고 Full uncor가 모두 복호 성공하여 Partial pool이 비는 경우 | `_Signal_Graceful_Stop_No_Partial` 이 rank 공용 플래그 `self.is_graceful_stop_requested` 를 세우고, `Run_Optimization` 의 trial 루프 머리와 `Test_Trial_LLR` 진입 직전에서 이 플래그를 보고 즉시 `break` 하도록 고친다 |
| 3 | CRITICAL | Barrier 타임아웃 상한(3600초)이 Ref_C 1회 실행 상한(36000초)과 메모리 재시도 대기(최대 600초)보다 짧다. 느린 코어 하나 때문에 정상 동작 중에 전체 job이 MPI_Abort 된다 | [DAO_Main.py:6690-6693](5_DAO/SRC/DAO_Main.py#L6690), [DAO_Constants.py:144](5_DAO/SRC/DAO_Constants.py#L144), [DAO_Config.py:320-323](5_DAO/SRC/DAO_Config.py#L320) | root가 종료 플래그를 쓴 뒤 느린 rank의 `Run_ECC` 한 번이 1시간을 넘길 때 (`Errno 12` 재시도가 겹치면 쉽게 도달) | `MPI_Barrier` 의 타임아웃 하한을 `SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY + 여유` 로 올리고, `TIME_CONFIG` 에 `MPI_TEST_BARRIER_TIMEOUT_SECONDS` 를 새로 두어 계산식을 한 곳에 모은다 |
| 4 | HIGH | `comm.Reduce` 와 `comm.allgather` 가 `_mpi_comm_with_timeout` 을 거치지 않는다. 이 자리에서 어긋나면 타임아웃도 진단 스냅샷도 없이 영원히 매달린다 | [DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861), [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049), [DAO_Main.py:7011](5_DAO/SRC/DAO_Main.py#L7011) | rank 하나가 `Run_ECC` 안에서 멈추거나 죽은 상태에서 나머지가 Reduce 또는 allgather에 도달할 때 | `_safe_reduce`, `_safe_allgather` 를 `_safe_bcast` 와 같은 모양으로 추가하고 세 곳을 모두 교체한다. Reduce는 버퍼 인자를 받으므로 `_mpi_comm_with_timeout(self.comm.Reduce, sendbuf, recvbuf, op=MPI.SUM, root=0, comm_name=...)` 형태로 감싼다 |
| 5 | MEDIUM | `_mpi_comm_with_timeout` 이 MPI 호출을 보조 스레드에서 실행하고, 타임아웃 시 주 스레드가 `comm.Abort` 를 부른다. MPI 스레드 지원 수준이 `MPI_THREAD_MULTIPLE` 이 아닌 빌드에서는 동작이 정의되지 않는다 | [DAO_Main.py:6896-6944](5_DAO/SRC/DAO_Main.py#L6896) | MPI 런타임이 `MPI_THREAD_MULTIPLE` 을 제공하지 않는 환경 | 모듈 진입부에서 `mpi4py.rc.thread_level = "multiple"` 을 명시하고, `MPI.Query_thread()` 결과가 `MPI.THREAD_MULTIPLE` 보다 낮으면 시작 시점에 경고를 남기고 타임아웃 감시를 끄도록 [DAO_Constants.py:135](5_DAO/SRC/DAO_Constants.py#L135) 부근에서 확인한다 |
| 6 | MEDIUM | `Update_Optimal_LLR` 이 root에서만 `target_group_indices` 를 고치고 bcast하지 않는다. 다음 `Gen_Trial_LLR` 의 bcast까지 root와 worker의 값이 다르다 | [DAO_Main.py:9574-9585](5_DAO/SRC/DAO_Main.py#L9574) | optimal 갱신으로 그룹 수가 줄어든 trial 직후 | `self.log_has_update = True` 앞뒤 어디든, root 블록을 빠져나온 뒤 `self.target_group_indices = self._safe_bcast(self.target_group_indices if self.is_root else None, "Bcast_target_group_indices_after_update")` 를 [DAO_Main.py:9600](5_DAO/SRC/DAO_Main.py#L9600) 다음 줄에 넣는다 |
| 7 | MEDIUM | `Check_Barrier_Sync` 가 Stage 시작과 Trial 시작 두 곳에만 있다. 두 지점 사이에는 채널당 6회 이상의 barrier가 있어, 그 사이에서 어긋나면 진단이 나오기 전에 통신이 먼저 멈춘다. 게다가 `Check_Barrier_Sync` 의 bcast 타임아웃은 1200초인데 `MPI_Barrier` 는 3600초라, 어긋났을 때 bcast 쪽이 먼저 터져 원인 지점이 가려진다 | [DAO_Main.py:6698-6741](5_DAO/SRC/DAO_Main.py#L6698), [DAO_Main.py:2258-2259](5_DAO/SRC/DAO_Main.py#L2258), [DAO_Main.py:2344-2345](5_DAO/SRC/DAO_Main.py#L2344) | rank 사이 barrier 수가 어긋나는 모든 경우 | `Test_LLR` 의 채널 루프 머리(현재 [DAO_Main.py:8963](5_DAO/SRC/DAO_Main.py#L8963) 의 `Set_Test_Environment` 직전)와 `Test_Trial_LLR` 의 Partial과 Full 사이에 `Check_Barrier_Sync` 를 추가하고, 이 함수의 bcast 타임아웃을 `MPI_Barrier` 와 같은 값으로 맞춘다 |
| 8 | LOW | `Debug_Pause` 의 `while True` 가 각 rank의 파일 읽기 결과로 `break` 되고, `break` 는 루프 끝의 `MPI_Barrier` 를 건너뛴다. rank마다 탈출 회차가 달라지면 barrier count가 영구히 갈린다 | [DAO_Main.py:1370-1386](5_DAO/SRC/DAO_Main.py#L1370) | `DEBUG_CONFIG.ENABLE_FILE_BREAKPOINT=True` 로 두고 이 함수를 쓰기 시작할 때 (현재 호출처 없음) | root만 파일을 읽고 `_safe_bcast` 로 탈출 여부를 내린 뒤 모든 rank가 같은 회차에 `break` 하도록 고친다 |
| 9 | LOW | `_Read_Stop_Idx` 와 `MPI_Debug_Logging` 은 정의만 있고 호출되지 않는다. 특히 `_Read_Stop_Idx` 는 발견 1의 올바른 해법(root가 쓴 stop idx를 worker가 읽는 방식)이 들어갈 자리를 비워 둔 흔적이다 | [DAO_Main.py:1136](5_DAO/SRC/DAO_Main.py#L1136), [DAO_Main.py:6997](5_DAO/SRC/DAO_Main.py#L6997) | 해당 없음 | 발견 1을 bcast 방식으로 고치면서 `_Read_Stop_Idx` 를 지우거나, 반대로 이 함수를 쓰는 방식으로 고친다. `MPI_Debug_Logging` 은 `Check_Barrier_Sync` 의 디버그 절과 기능이 겹치므로 지운다 |
| 10 | LOW | `MPI_Abort` 는 `NoReturn` 으로 선언되어 있으나 재진입 경로에서 `return` 한다. 호출부가 복귀를 가정하지 않고 작성되어 있어, 복귀가 일어나면 미정의 지역 변수를 읽는다 | [DAO_Main.py:6806-6811](5_DAO/SRC/DAO_Main.py#L6806), [DAO_Main.py:2006-2010](5_DAO/SRC/DAO_Main.py#L2006) | `comm.Abort` 가 즉시 프로세스를 끊지 못하는 런처 설정 | 재진입 경로도 `os._exit(error_code)` 로 확실히 끊거나, `Read_FER_From_File` 처럼 값을 돌려주는 함수는 `MPI_Abort` 뒤에 `raise SystemExit(...)` 를 명시한다 |

---

## 발견 1 (CRITICAL): GEN_SINGLE_ROW 종료 플래그를 rank마다 따로 읽는다

### 근거 코드

[DAO_Main.py:10053-10067](5_DAO/SRC/DAO_Main.py#L10053)

```python
for candidate_idx in range(num_candidates):
    end_flag_interval = SINGLE_ROW_CONFIG.END_FLAG_CHECK_INTERVAL
    if end_flag_interval > 0 and candidate_idx % end_flag_interval == 0:
        self.MPI_Barrier()
        if self._gen_single_row_stop_idx is None and self.Read_DAO_End_Flag():
            self._gen_single_row_stop_idx = candidate_idx + end_flag_interval
            self._Write_Stop_Idx(self._gen_single_row_stop_idx)
            ...
        if self._gen_single_row_stop_idx is not None and candidate_idx >= self._gen_single_row_stop_idx:
            ...
            break
```

`Read_DAO_End_Flag` 는 [DAO_Main.py:1123](5_DAO/SRC/DAO_Main.py#L1123) 의 `_Read_End_Flag` 를 그대로 부르는 파일 읽기이며 root 전용 가드가 없다. `_gen_single_row_stop_idx` 는 이 읽기 결과로 rank마다 따로 정해진다.

비교 대상: 같은 파일 읽기를 `Run_Optimization` 에서는 root만 하고 bcast로 내린다.
[DAO_Main.py:8071-8077](5_DAO/SRC/DAO_Main.py#L8071)

```python
if self.is_root:
    is_dao_end = self.Read_DAO_End_Flag()
    trial_skip_count = self.Read_Trial_End_Flag()
else:
    is_dao_end = False
    trial_skip_count = 0
is_dao_end = self._safe_bcast(is_dao_end if self.is_root else None, "Bcast_dao_end_flag")
```

### rank 0과 rank 1의 경로 대조

`END_FLAG_CHECK_INTERVAL = 10` (기본값, [DAO_Config.py:404](5_DAO/SRC/DAO_Config.py#L404)) 이고 사용자가 candidate 10번 검사 시점에 종료 플래그 파일을 쓰는 중이라고 하자.

| 시점 | rank 0 (root) | rank 1 (worker) |
|------|---------------|-----------------|
| candidate 10 | `MPI_Barrier` (count N) | `MPI_Barrier` (count N) |
| candidate 10, 플래그 읽기 | `"1"` 을 읽음, `stop_idx = 20` | 파일 속성 캐시 때문에 `"0"` 을 읽음, `stop_idx = None` |
| candidate 10, 탈출 판정 | `10 >= 20` 거짓, 계속 | `None` 이므로 계속 |
| candidate 11~19 | `Bcast_single_row_*` 9회 | `Bcast_single_row_*` 9회 |
| candidate 20 | `MPI_Barrier` (count M) | `MPI_Barrier` (count M) |
| candidate 20, 플래그 읽기 | `stop_idx` 이미 있음, 읽지 않음 | `"1"` 을 읽음, `stop_idx = 30` |
| candidate 20, 탈출 판정 | `20 >= 20` 참, **루프 탈출** | `20 >= 30` 거짓, **계속** |
| 이후 | `Rank_And_Save_Single_Row_Candidates` 후 `MPI_Barrier` ([DAO_Main.py:10190](5_DAO/SRC/DAO_Main.py#L10190)) | `Build_Single_Row_Matrix` 후 `_safe_bcast` ([DAO_Main.py:10075](5_DAO/SRC/DAO_Main.py#L10075)) |

root는 Barrier에, worker는 bcast에 들어가 서로 다른 집단 통신을 부른다. bcast의 root가 rank 0이므로 worker는 root가 보내 줄 데이터를 기다리고, root는 Barrier에서 worker를 기다린다.
bcast 타임아웃 1200초가 먼저 지나 `MPI_Abort` 가 나면서 job 전체가 끊어진다.

단 한 번의 읽기 경합이 아니라, 최초 감지 회차가 한 주기만 어긋나도 `stop_idx` 가 통째로 한 주기 차이 나면서 반드시 어긋난다는 점이 위험하다.

### 처방

`Run_Single_Row_Generation` 의 10056~10067 블록을 다음 순서로 다시 쓴다.

- ㉮ `self.MPI_Barrier()` 유지
- ㉯ `if self.is_root: is_dao_end = self.Read_DAO_End_Flag()` `else: is_dao_end = False`
- ㉰ `is_dao_end = self._safe_bcast(is_dao_end if self.is_root else None, "Bcast_dao_end_flag_single_row")`
- ㉱ `if self._gen_single_row_stop_idx is None and is_dao_end:` 안에서 `stop_idx` 를 정하고, `_Write_Stop_Idx` 는 root 전용이므로 그대로 둔다
- ㉲ 탈출 판정은 그대로 두되, 이제 모든 rank의 `stop_idx` 가 같은 값이 된다

---

## 발견 2 (CRITICAL): Partial 0개 graceful stop이 MPI_Abort로 끝난다

### 근거 코드

[DAO_Main.py:9457-9477](5_DAO/SRC/DAO_Main.py#L9457)

```python
def _Signal_Graceful_Stop_No_Partial(self):
    ...
    if self.is_root:
        self._Write_End_Flag(PATH_CONFIG.DAO_END_FLAG_FILE_PATH, True)
    self.MPI_Barrier()
```

이 함수는 DAO 종료 플래그 파일만 쓰고 돌아온다. 그런데 `Run_Optimization` 의 trial 루프는 이 플래그를 `Test_Trial_LLR()` 을 **끝낸 뒤에** 읽는다.

[DAO_Main.py:8044](5_DAO/SRC/DAO_Main.py#L8044) 가 `should_check_update = self.Test_Trial_LLR()` 이고, 플래그 읽기는 [DAO_Main.py:8072](5_DAO/SRC/DAO_Main.py#L8072) 이다.

그 사이 `Test_Trial_LLR` 은 Partial pool로 테스트를 돌린다.
[DAO_Main.py:9509](5_DAO/SRC/DAO_Main.py#L9509) 의 `_Run_Test_Stage(TestMode.PARTIAL, ...)` 가
[DAO_Main.py:7518-7522](5_DAO/SRC/DAO_Main.py#L7518) 에서 `pool_has_uncor[PARTIAL][ch] == False` 를 보고
모든 rank의 `has_uncor[ch]` 를 False로 만든다. 그러면 [DAO_Main.py:7932-7934](5_DAO/SRC/DAO_Main.py#L7932) 에서
`Run_ECC` 가 전 rank에서 즉시 반환하고, 결과 파일이 하나도 생기지 않는다.

마지막으로 [DAO_Main.py:1883-1884](5_DAO/SRC/DAO_Main.py#L1883) 가 모든 rank에서 걸린다.

```python
if total_tests == 0:
    self.MPI_Abort(f"Gather_Ref_C_Results: total_tests=0 for ch_idx={ch_idx}. All cores failed to produce results.")
```

### rank 0과 rank 1의 경로 대조

이 발견은 rank 사이 어긋남이 아니라 **모든 rank가 같은 방식으로 비정상 종료**하는 경우이다.
두 rank의 경로는 끝까지 동일하며, 마지막에 함께 `comm.Abort(1)` 을 부른다.
문제는 로그에 남는 메시지가 "All cores failed to produce results" 여서, 실제 원인("최적화 목표 달성")과
전혀 다른 진단을 남긴다는 점이다. 사용자는 코어 장애로 오해하게 된다.

호출 경로는 세 곳이다.

- ㉮ [DAO_Main.py:9251-9253](5_DAO/SRC/DAO_Main.py#L9251) `Test_Initial_LLR` 의 초기 Partial pool 구성 실패
- ㉯ [DAO_Main.py:9604-9607](5_DAO/SRC/DAO_Main.py#L9604) `Update_Optimal_LLR` 의 `Rebuild_Partial_Pool` 실패
- ㉰ [DAO_Main.py:9705-9708](5_DAO/SRC/DAO_Main.py#L9705) `_Promote_Temp_Optimal_On_Stage_Exit` 의 `Rebuild_Partial_Pool` 실패

세 곳 모두 플래그만 쓰고 그 자리에서 루프를 끊지 않는다.

### 처방

- ㉮ `LLR_OPT.__init__` 에 `self.is_graceful_stop_requested: bool = False` 를 추가한다
  (현재 필드 초기화는 [DAO_Main.py:511-543](5_DAO/SRC/DAO_Main.py#L511) 구역)
- ㉯ `_Signal_Graceful_Stop_No_Partial` 의 `MPI_Barrier` 앞에서 `self.is_graceful_stop_requested = True` 를 세운다.
  모든 rank가 이 함수를 같은 조건으로 부르므로 값이 자동으로 맞는다
- ㉰ `Run_Optimization` 의 trial 루프에서 `should_check_update = self.Test_Trial_LLR()` 바로 앞
  ([DAO_Main.py:8044](5_DAO/SRC/DAO_Main.py#L8044))에 `if self.is_graceful_stop_requested: break` 를 넣고,
  stage 루프 머리 ([DAO_Main.py:8019](5_DAO/SRC/DAO_Main.py#L8019) 의 `Periodic_Recheck(stage_idx)` 앞)에도 같은 검사를 넣는다
- ㉱ `Run_Initial_Test` 의 `Update_Optimal_LLR(is_initial=True)` 뒤에서도 이 플래그를 보고 바로 돌아오게 한다

`break` 는 모든 rank가 같은 플래그 값으로 동시에 수행하므로 집단 통신 정합이 깨지지 않는다.

---

## 발견 3 (CRITICAL): 타임아웃 예산이 Ref_C 실행 상한보다 짧다

### 근거 코드

[DAO_Main.py:6690-6693](5_DAO/SRC/DAO_Main.py#L6690)

```python
self._mpi_comm_with_timeout(
    self.comm.Barrier,
    timeout_seconds=max(TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS, 3600),
    comm_name=f"MPI_Barrier[{self.barrier_count}]"
)
```

[DAO_Config.py:321-323](5_DAO/SRC/DAO_Config.py#L321)

```python
MAX_ECC_MEMORY_RETRY = 10
MAX_ECC_MEMORY_RETRY_DELAY = 60
MPI_COMM_TIMEOUT_SECONDS = 2*int(MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY)
```

`MPI_COMM_TIMEOUT_SECONDS` 는 1200초이고, Barrier는 하한 3600초를 적용받는다.
반면 Ref_C 1회 실행 상한은 [DAO_Constants.py:144](5_DAO/SRC/DAO_Constants.py#L144) 의
`SIM_MAX_TIME_OUT = 10 * 60 * 60` 으로 36000초이며,
[DAO_Main.py:7936-7952](5_DAO/SRC/DAO_Main.py#L7936) 의 메모리 재시도가 최대 10회 반복되면
그 위에 최대 600초의 대기가 더 붙는다.

### rank 0과 rank 1의 경로 대조

| 시점 | rank 0 (root) | rank 1 (느린 worker) |
|------|---------------|---------------------|
| t0 | `Run_ECC` 종료, `Gather_Ref_C_Results(is_test_end=False)` 로 결과 집계 | `Run_ECC` 실행 중 |
| t0 | `Check_Test_End` 에서 `total_num_errors >= max_error` 판정, 종료 플래그 `"1"` 기록 | 계속 실행 중 |
| t0+ | while 루프 탈출, `_Write_Run_ECC_End_Ack`, `Gather_Ref_C_Results(is_test_end=True)` 진입 | 계속 실행 중 |
| t0+ | [DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840) `MPI_Barrier` 진입, 3600초 시계 시작 | 계속 실행 중 |
| t0+3600s | 타임아웃, `MPI_Abort("MPI_Barrier[N] timed out after 3600 seconds")` | `Run_ECC` 아직 정상 진행 중 |

`while` 루프 안에는 집단 통신이 없으므로(비root는 [DAO_Main.py:1806-1807](5_DAO/SRC/DAO_Main.py#L1806) 에서
즉시 반환한다) rank 사이 반복 횟수 차이 자체는 허용된다. 문제는 이 "허용된 차이"를 흡수해야 할
Barrier 타임아웃이 Ref_C 실행 상한보다 훨씬 짧다는 점이다. 느린 코어 하나 때문에 job 전체가 끊어지며,
로그에는 교착("deadlock or network issue")이라는 잘못된 진단이 남는다.

[DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323) 의 주석 "1시간 이상이면 타임아웃 없음과 동일" 도
코드와 맞지 않는다. Barrier만 3600초 하한을 받고 bcast와 gather는 설정값 1200초를 그대로 쓴다.

### 처방

- ㉮ `TIME_CONFIG` 에 계산식을 한 곳으로 모은다.
  `ECC_WORST_CASE_SECONDS = SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY`
- ㉯ `MPI_Barrier` 의 `timeout_seconds` 를 `max(TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS, TIME_CONFIG.ECC_WORST_CASE_SECONDS + 600)` 으로 바꾼다
- ㉰ 3600이라는 숫자를 코드에 직접 쓰지 않는다. 지금은 [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692) 한 곳에만 있으나 설정으로 옮긴다
- ㉱ `DAO_Config.py:323` 의 주석을 실제 동작에 맞게 다시 쓴다

---

## 발견 4 (HIGH): Reduce와 allgather가 타임아웃 감시를 거치지 않는다

### 근거 코드

[DAO_Main.py:1858-1861](5_DAO/SRC/DAO_Main.py#L1858)

```python
recvbuf = np.zeros(buf_size, dtype='f8') if self.is_root else None
self.comm.Reduce(sendbuf, recvbuf, op=MPI.SUM, root=0)
```

[DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049)

```python
all_elapsed_times = self.comm.allgather(elapsed_time)
```

[DAO_Main.py:7011](5_DAO/SRC/DAO_Main.py#L7011) 의 `MPI_Debug_Logging` 도 같은 형태이다 (현재 호출처 없음).

같은 파일의 `_safe_bcast` ([DAO_Main.py:6946](5_DAO/SRC/DAO_Main.py#L6946)) 와
`_safe_gather` ([DAO_Main.py:6971](5_DAO/SRC/DAO_Main.py#L6971)) 는 모두
`_mpi_comm_with_timeout` 과 `Write_MPI_Error_Snapshot` 을 거치는데, 위 세 곳만 맨 호출이다.

### rank 0과 rank 1의 경로 대조

`Test_Core_Speed` 의 allgather가 가장 위험하다. 이 함수의 목적 자체가 "코어마다 속도가 다름을 측정"하는
것이므로 rank 사이 도달 시각 차이가 크게 벌어지는 것이 정상이다.

| 시점 | rank 0 (root) | rank 1 (멈춘 worker) |
|------|---------------|---------------------|
| t0 | `Run_ECC(ch_idx=0)` 반환 | `Run_ECC` 안에서 Ref_C 프로세스가 응답 없음 |
| t0 | [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049) `comm.allgather` 진입 | 여전히 서브프로세스 대기 |
| 이후 | 타임아웃 없음. 무한 대기 | `SIM_MAX_TIME_OUT`(36000초)까지 대기 후 `MPI_Abort` |

Ref_C가 `subprocess.run(timeout=SIM_MAX_TIME_OUT)` 으로 감싸여 있어 결국 10시간 뒤에는 풀리지만,
그 10시간 동안 나머지 rank는 아무 진단도 남기지 못한 채 allgather 안에 있다.
Reduce 쪽은 바로 앞에 Barrier가 있어 정렬되어 있으므로 위험이 낮지만,
예외가 나도 `Write_MPI_Error_Snapshot` 이 호출되지 않아 진단 정보를 잃는다.

### 처방

`_safe_bcast` 바로 아래에 같은 모양으로 두 함수를 추가하고 호출부 세 곳을 바꾼다.

```python
def _safe_reduce(self, sendbuf, recvbuf, op, comm_name: str = "reduce", root: int = 0):
    try:
        return self._mpi_comm_with_timeout(
            self.comm.Reduce, sendbuf, recvbuf, op=op, root=root, comm_name=comm_name)
    except Exception as e:
        self.Write_MPI_Error_Snapshot(e, comm_name)
        self.MPI_Abort(f"{comm_name} failed: {type(e).__name__}: {e}")

def _safe_allgather(self, data, comm_name: str = "allgather"):
    try:
        return self._mpi_comm_with_timeout(self.comm.allgather, data, comm_name=comm_name)
    except Exception as e:
        self.Write_MPI_Error_Snapshot(e, comm_name)
        self.MPI_Abort(f"{comm_name} failed: {type(e).__name__}: {e}")
```

`Test_Core_Speed` 의 allgather는 Ref_C 실행 직후이므로 발견 3에서 정한
`ECC_WORST_CASE_SECONDS` 기반 타임아웃을 명시적으로 넘긴다.

---

## 발견 5 (MEDIUM): 보조 스레드에서 MPI를 부르고 주 스레드에서 Abort 한다

### 근거 코드

[DAO_Main.py:6919-6935](5_DAO/SRC/DAO_Main.py#L6919)

```python
def comm_thread():
    try:
        result[0] = comm_func(*args, **kwargs)
    except Exception as e:
        exception[0] = e
    finally:
        completed.set()

thread = threading.Thread(target=comm_thread, daemon=True)
thread.start()

if not completed.wait(timeout=timeout_seconds):
    error_msg = f"{comm_name} timed out after {timeout_seconds} seconds. ..."
    self.MPI_Abort(error_msg)
```

[DAO_Constants.py:135](5_DAO/SRC/DAO_Constants.py#L135) 에는 `comm = MPI.COMM_WORLD` 만 있고
`mpi4py.rc.thread_level` 설정이 없다.

### 문제

모든 집단 통신이 이 경로를 지나므로, MPI 런타임의 스레드 지원 수준이 `MPI_THREAD_MULTIPLE` 미만이면
평상시 통신 전부가 규격 밖 사용이 된다. 또 타임아웃이 났을 때 주 스레드가 `comm.Abort` 를 부르는 동안
보조 스레드는 여전히 MPI 안에 있다. `MPI_Abort` 는 그 전에 `inspect.stack()` 으로 전체 호출 스택과
지역 변수를 수집해 파일에 쓰므로([DAO_Main.py:6829-6861](5_DAO/SRC/DAO_Main.py#L6829)) 두 스레드가
MPI 라이브러리 안에 동시에 머무는 시간이 짧지 않다.

rank 0과 rank 1의 경로는 동일하므로 어긋남은 없고, 환경 의존 위험이다.

### 처방

- ㉮ `DAO_Constants.py` 의 `from mpi4py import MPI` 앞에 `import mpi4py; mpi4py.rc.thread_level = "multiple"` 를 넣는다
- ㉯ 모듈 레벨에서 `MPI_THREAD_LEVEL = MPI.Query_thread()` 를 기록하고,
  `LLR_OPT.Setup` 의 `Print_Initial_Setup` 에서 이 값을 로그에 남긴다
- ㉰ `_mpi_comm_with_timeout` 에서 `MPI_THREAD_LEVEL < MPI.THREAD_MULTIPLE` 이면
  스레드를 만들지 않고 `comm_func(*args, **kwargs)` 를 그대로 부른다 (타임아웃 감시 없이 동작)

---

## 발견 6 (MEDIUM): target_group_indices가 root에서만 바뀐다

### 근거 코드

[DAO_Main.py:9574-9585](5_DAO/SRC/DAO_Main.py#L9574) 는 root 전용 블록 안이다.

```python
num_groups = len(self.optimal_LLR_matrix.groups)
self.target_group_indices = [idx for idx in self.target_group_indices if idx < num_groups]
if not self.target_group_indices:
    self.target_group_indices = list(range(DAO_CONFIG.INITIAL_TARGET_GROUP_IDX,
                                           len(self.optimal_LLR_matrix.groups)))
```

이어지는 bcast 네 줄([DAO_Main.py:9597-9600](5_DAO/SRC/DAO_Main.py#L9597))에는
`update_mode`, `optimal_LLR_matrix`, `temp_optimal_LLR_matrix`, `is_previous_trial_updated` 만 들어 있고
`target_group_indices` 는 빠져 있다.

### rank 0과 rank 1의 경로 대조

DELETE_ROW 모드에서 optimal이 갱신되어 그룹 수가 5에서 4로 줄었다고 하자.

| 시점 | rank 0 (root) | rank 1 (worker) |
|------|---------------|-----------------|
| Update 직후 | `target_group_indices = [1, 2, 3]` | `target_group_indices = [1, 2, 3, 4]` |
| `Rebuild_Partial_Pool` | 이 값을 쓰지 않음 | 이 값을 쓰지 않음 |
| 다음 `Initialize_Trial` 후 `Gen_Trial_LLR` | root 값으로 bcast ([DAO_Main.py:2019](5_DAO/SRC/DAO_Main.py#L2019)) | 값이 root 값으로 맞춰짐 |
| 다음 `Initialize_Stage` | optimal 기준으로 다시 계산 | 같은 값으로 다시 계산 |

지금은 `Gen_Trial_LLR` 의 bcast와 `Initialize_Stage` 의 재계산이 뒤에서 값을 맞춰 주므로
집단 통신 정합이 깨지지는 않는다. 다만 이 두 곳 중 하나라도 조건 아래로 들어가면(예를 들어
`generate_LLR_success` 가 False인 trial이 이어지면 `target_group_indices` bcast는 건너뛴다)
값이 갈린 채로 `Init_Delete_Row_Mode` 같은 전 rank 공용 함수가 돌아
`max_modification_trial` 이 rank마다 달라질 수 있다. 그 경우
[DAO_Main.py:8024](5_DAO/SRC/DAO_Main.py#L8024) 의 trial 루프 길이가 어긋나 곧바로 교착이 된다.

### 처방

[DAO_Main.py:9600](5_DAO/SRC/DAO_Main.py#L9600) 다음 줄에 한 줄을 추가한다.

```python
self.target_group_indices = self._safe_bcast(
    self.target_group_indices if self.is_root else None, "Bcast_target_group_indices_after_update")
```

---

## 발견 7 (MEDIUM): Check_Barrier_Sync가 잡을 수 있는 범위가 좁다

### 근거 코드

[DAO_Main.py:6698-6741](5_DAO/SRC/DAO_Main.py#L6698) 의 `Check_Barrier_Sync` 는
`self.barrier_count` 를 bcast로 비교한다. 호출처는 두 곳뿐이다.

- [DAO_Main.py:2258-2259](5_DAO/SRC/DAO_Main.py#L2258) `Initialize_Stage` 시작
- [DAO_Main.py:2344-2345](5_DAO/SRC/DAO_Main.py#L2344) `Initialize_Trial` 시작

### 두 지점 사이의 barrier 수

Trial 하나에서 지나는 barrier를 세면 다음과 같다 (채널 수 `NUM_TARGET_CHANNELS` 를 `C` 라 한다).

- `Set_Test_Environment` 앞뒤 2회 × `C` ([DAO_Main.py:8460](5_DAO/SRC/DAO_Main.py#L8460), [DAO_Main.py:8478](5_DAO/SRC/DAO_Main.py#L8478))
- `Gather_Ref_C_Results(is_test_end=True)` 3회 × `C` ([DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840), [DAO_Main.py:1864](5_DAO/SRC/DAO_Main.py#L1864), [DAO_Main.py:1876](5_DAO/SRC/DAO_Main.py#L1876))
- `Process_CSW_Logs` 1회 × `C` ([DAO_Main.py:9018](5_DAO/SRC/DAO_Main.py#L9018))
- Two-stage 모드면 Partial과 Full 두 번이므로 위 합계가 두 배
- `Ensure_Uncors_Loaded` 가 전환을 수행하면 `Load_Uncors_From_Pool` 1회 ([DAO_Main.py:7541](5_DAO/SRC/DAO_Main.py#L7541))
- optimal 갱신이 있으면 `Rebuild_Partial_Pool` 안에서 `_Setup_Uncor_Pool_For_Channel` 1회 × `C` 와 마무리 1회

`C = 3`, Two-stage 모드면 trial 하나에 barrier가 36회를 넘는다.
이 구간 안에서 어긋나면 `Check_Barrier_Sync` 가 도는 다음 Trial 시작까지 가지 못하고
그 자리의 Barrier 또는 bcast에서 이미 멈춘다.

### 타임아웃 불일치

`Check_Barrier_Sync` 의 bcast는 `_mpi_comm_with_timeout` 의 기본값(1200초)을 쓰고
`MPI_Barrier` 는 3600초를 쓴다([DAO_Main.py:6713-6717](5_DAO/SRC/DAO_Main.py#L6713) 대 [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692)).
rank 0이 Barrier에, rank 1이 `Check_Barrier_Sync` 의 bcast에 들어가면 rank 1이 1200초 뒤 먼저 터진다.
그 로그에는 "Check_Barrier_Sync[...] timed out" 만 남고 barrier count 비교 결과는 남지 않아,
정작 이 함수가 만들려던 진단이 나오지 않는다.

### 처방

- ㉮ `Check_Barrier_Sync` 호출을 세 곳 더 넣는다.
  `Test_LLR` 의 채널 루프 머리([DAO_Main.py:8963](5_DAO/SRC/DAO_Main.py#L8963) 의 `Set_Test_Environment` 직전),
  `Test_Trial_LLR` 의 Partial과 Full 사이([DAO_Main.py:9534](5_DAO/SRC/DAO_Main.py#L9534) 직전),
  `Update_Optimal_LLR` 의 bcast 묶음 직전([DAO_Main.py:9597](5_DAO/SRC/DAO_Main.py#L9597))
- ㉯ `Check_Barrier_Sync` 의 bcast에 `timeout_seconds` 를 `MPI_Barrier` 와 같은 값으로 명시해 넘긴다
- ㉰ 태그에 `ch_idx` 와 `test_mode` 를 넣어 어느 채널의 어느 단계에서 갈렸는지 바로 보이게 한다

---

## 발견 8 (LOW): Debug_Pause의 탈출이 rank마다 다를 수 있다

[DAO_Main.py:1370-1386](5_DAO/SRC/DAO_Main.py#L1370)

```python
while True:
    if self.debug_is_init:
        ...
    else:
        with open(debug_control_path, "r", encoding="utf-8") as f:
            flag = f.read().strip()
        if flag != default_value:
            break
    time.sleep(sleep_interval)
    self.MPI_Barrier()
self.MPI_Barrier()
```

`break` 는 루프 끝의 `MPI_Barrier` 를 건너뛴다. 사용자가 파일 값을 바꾸는 순간이 rank마다 다른 회차에
걸리면 rank 사이 `barrier_count` 가 영구히 1 차이 난다. 이후 Barrier끼리는 계속 짝이 맞으므로
당장 멈추지는 않고, 다음 `Check_Barrier_Sync` 에서 `MPI_Abort` 로 끝난다.

이 함수는 현재 어디에서도 호출되지 않으므로 심각도는 낮다.
다시 쓸 때는 root만 파일을 읽고 `_safe_bcast` 로 탈출 여부를 내리도록 고친다.

---

## 발견 9 (LOW): 쓰이지 않는 함수 두 개

- [DAO_Main.py:1136](5_DAO/SRC/DAO_Main.py#L1136) `_Read_Stop_Idx` 는 정의만 있고 호출되지 않는다.
  `_Write_Stop_Idx` 는 [DAO_Main.py:10060](5_DAO/SRC/DAO_Main.py#L10060) 에서 root가 부르므로
  "root가 쓰고 worker가 읽는" 설계가 절반만 구현되어 있다. 발견 1의 어긋남이 여기서 비롯된다
- [DAO_Main.py:6997](5_DAO/SRC/DAO_Main.py#L6997) `MPI_Debug_Logging` 은 호출되지 않으며
  기능이 `Check_Barrier_Sync` 의 디버그 절([DAO_Main.py:6731-6741](5_DAO/SRC/DAO_Main.py#L6731))과 겹친다.
  감싸지 않은 `comm.allgather` 를 남겨 두는 위험만 있다

---

## 발견 10 (LOW): MPI_Abort의 NoReturn 가정

[DAO_Main.py:6806-6811](5_DAO/SRC/DAO_Main.py#L6806)

```python
if self._in_mpi_abort:
    print(f"[Rank {self.rank}] MPI_Abort re-entered: {error_msg}", flush=True)
    self.comm.Abort(error_code)
    return  # comm.Abort() 이후 도달 불가이나 방어적 배치
```

`MPI_Abort` 는 `-> NoReturn` 으로 선언되어 있고 호출부는 복귀를 가정하지 않는다.
예를 들어 [DAO_Main.py:2006-2010](5_DAO/SRC/DAO_Main.py#L2006) 의 `Read_FER_From_File` 은

```python
try:
    FER = float(parts[-1])
except (ValueError, IndexError) as error:
    self.MPI_Abort(f"Invalid FER in {result_file}: {error}")
return FER
```

로 되어 있어 복귀가 일어나면 `FER` 이 정의되지 않은 채 `return` 한다.
`comm.Abort` 가 즉시 프로세스를 끊지 못하는 런처 설정에서만 문제가 되므로 심각도는 낮다.
재진입 경로에서 `comm.Abort` 뒤에 `os._exit(error_code)` 를 두면 선언과 동작이 맞는다.

---

## 확인했으나 문제 없던 항목

- ㉮ root 전용 블록 약 95곳 가운데 집단 통신이 들어 있는 곳은 없다 (들여쓰기 기준 전수 검사)
- ㉯ root 전용 블록 안의 `MPI_Abort` (`Gen_Trial_LLR` [DAO_Main.py:1991](5_DAO/SRC/DAO_Main.py#L1991), `Set_Gen_Trial_LLR_Mode` 의 6곳, `Update_Optimal_LLR` [DAO_Main.py:9595](5_DAO/SRC/DAO_Main.py#L9595), `Init_Reorder_Group_Mode` [DAO_Main.py:4481](5_DAO/SRC/DAO_Main.py#L4481))는 모두 `comm.Abort` 로 job 전체를 끊으므로 뒤따르는 `Bcast_Trial_LLR_Mode` 나 `_safe_bcast` 짝이 깨져도 교착이 되지 않는다
- ㉰ `Init_Reorder_Group_Mode`, `Init_Adjust_Iteration_Mode`, `Init_Delete_Row_Mode`, `Init_Insert_Restart_Group_Mode` 는 전 rank가 부르지만 입력이 bcast된 `optimal_LLR_matrix` 와 `target_group_indices` 뿐이어서 판정이 갈리지 않는다
- ㉱ `MPI_Barrier` 32곳 가운데 조건 분기 안에 있는 것은 `Debug_Pause`(발견 8), `Run_Initial_Test`([DAO_Main.py:7802](5_DAO/SRC/DAO_Main.py#L7802), `current_seed_mode` 는 bcast 값), `Process_CSW_Logs`([DAO_Main.py:9012](5_DAO/SRC/DAO_Main.py#L9012), `enable_print_CSW_log` 는 [DAO_Main.py:8594](5_DAO/SRC/DAO_Main.py#L8594) 에서 bcast), `Run_Single_Row_Generation`(발견 1), `_Redistribute_Uncor_Pool_Uniform`(설정값 조건), `Setup_Uncor_Pool`(설정값 루프)이며, 발견 1과 8을 빼면 모두 전 rank 동일 값이다
- ㉲ `Test_LLR` 의 `while not self.is_test_end` 루프 안에는 집단 통신이 없다. `Gather_Ref_C_Results(is_test_end=False)` 는 [DAO_Main.py:1806-1807](5_DAO/SRC/DAO_Main.py#L1806) 에서 비root가 즉시 반환한다. 따라서 rank마다 반복 횟수가 달라도 정합은 깨지지 않는다 (다만 발견 3의 타임아웃 문제로 이어진다)
- ㉳ `Ensure_Uncors_Loaded` 의 스킵 조건 `self.current_loaded_test_mode == test_mode` 는 이 값을 고치는 세 곳([DAO_Main.py:7364](5_DAO/SRC/DAO_Main.py#L7364), [DAO_Main.py:7542](5_DAO/SRC/DAO_Main.py#L7542), [DAO_Main.py:9445](5_DAO/SRC/DAO_Main.py#L9445))과 [DAO_Main.py:9172](5_DAO/SRC/DAO_Main.py#L9172) 가 모두 전 rank 공통 경로에 있어 갈리지 않는다. 따라서 그 뒤의 `Load_Uncors_From_Pool` 의 Barrier도 전 rank가 함께 지난다
- ㉴ `Gather_Ref_C_Results` 의 두 제외 기준은 같은 bcast에서 나온다. root 경로의 `proc in self.excluded_cores` ([DAO_Main.py:1816](5_DAO/SRC/DAO_Main.py#L1816))와 각 rank의 `self.is_current_core_excluded` ([DAO_Main.py:1847](5_DAO/SRC/DAO_Main.py#L1847))는 [DAO_Main.py:9087-9088](5_DAO/SRC/DAO_Main.py#L9087) 에서 한 줄 차이로 함께 정해지므로 같은 집합을 가리킨다. `_Recheck_Speed_Test` 가 [DAO_Main.py:9136](5_DAO/SRC/DAO_Main.py#L9136) 에서 `is_current_core_excluded` 만 잠시 False로 두는 구간에도 두 값을 동시에 쓰는 코드가 없다
- ㉵ trial 루프의 `continue`([DAO_Main.py:8039](5_DAO/SRC/DAO_Main.py#L8039))와 `break`([DAO_Main.py:8149](5_DAO/SRC/DAO_Main.py#L8149), [DAO_Main.py:8157](5_DAO/SRC/DAO_Main.py#L8157))는 각각 `gen_success`, `is_forced_termination`, multi-round state에서 나오고 셋 다 bcast로 맞춰진 값이다. `continue` 는 그 뒤의 `_safe_bcast` 묶음을 통째로 건너뛰지만 전 rank가 함께 건너뛴다
- ㉶ `Is_Current_LLR_Valid`([DAO_Main.py:2474](5_DAO/SRC/DAO_Main.py#L2474))는 bcast된 `current_LLR_matrix` 만 본다. `LLR_MATRIX.Is_LLR_Valid`([DAO_LLR_MATRIX.py:266](5_DAO/SRC/DAO_LLR_MATRIX.py#L266))는 헤더와 그룹 값만 읽는 순수 함수여서 rank마다 판정이 갈리지 않는다. 실패 시 저장은 `Save_LLR_Matrix` 의 기본값 `save_root_only=True` 로 root 전용이다. 따라서 [DAO_Main.py:8030](5_DAO/SRC/DAO_Main.py#L8030) 의 재시도 루프 횟수가 rank마다 달라지지 않는다
- ㉷ `Test_LLR` 의 채널 조기 탈출([DAO_Main.py:9004-9008](5_DAO/SRC/DAO_Main.py#L9004))은 `_Is_Channel_Degraded` 가 비교하는 두 값이 모두 bcast에서 온 같은 실수이므로 전 rank가 같은 판정을 낸다. `matrix.FERs` 와 `FERs_partial` 은 [DAO_Main.py:1922-1932](5_DAO/SRC/DAO_Main.py#L1922) 에서 `Bcast_ECC_results` 결과로 전 rank가 함께 채운다. 비교 대상인 `temp_optimal_LLR_matrix` 도 [DAO_Main.py:9599](5_DAO/SRC/DAO_Main.py#L9599) 와 [DAO_Main.py:2261](5_DAO/SRC/DAO_Main.py#L2261) 에서 맞춰진다
- ㉸ `Test_Trial_LLR` 의 `should_proceed`(`Check_Partial_Improvement` [DAO_Main.py:1444](5_DAO/SRC/DAO_Main.py#L1444))도 같은 근거로 전 rank 동일하다. 이 값이 갈리면 Full 테스트 전체(채널당 barrier 6회)가 한쪽에서만 돌아 즉시 교착이 되므로 가장 위험한 자리인데, 현재 입력은 모두 bcast 값이다
- ㉹ `Make_Dirs`([DAO_Main.py:6597-6619](5_DAO/SRC/DAO_Main.py#L6597))의 root 전용 디렉토리 생성 뒤 Barrier는 전 rank가 무조건 지난다. `session_timestamp` 는 [DAO_Main.py:8708](5_DAO/SRC/DAO_Main.py#L8708) 에서 `Make_Dirs` 보다 먼저 bcast되므로 경로가 갈리지 않는다
- ㉺ `Setup_Uncor_Pool`, `_Setup_Uncor_Pool_For_Channel`, `Load_Uncors_From_Pool`, `Rebuild_Partial_Pool`, `_Build_Initial_Partial_Pool` 의 Barrier와 bcast는 root 전용 파일 작업과 전 rank 통신이 정확히 분리되어 있다. `src_path` 가 비root에서 None으로 넘어가도 root 블록에서만 쓰인다
- ㉻ `_Promote_Temp_Optimal_On_Stage_Exit`([DAO_Main.py:9610](5_DAO/SRC/DAO_Main.py#L9610))의 `promoted` 는 bcast 뒤에 분기하므로 `if promoted:` 안의 bcast 두 개와 `Rebuild_Partial_Pool` 을 전 rank가 함께 수행한다
