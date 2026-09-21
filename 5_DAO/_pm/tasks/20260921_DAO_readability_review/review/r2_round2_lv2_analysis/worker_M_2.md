# Round 2 팀 M 워커 2: 타임아웃 워치독, 파일 종료 신호, 난수와 재현성

- 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
- 작성 시각: 2026-09-21 16:18:44
- 배정 관점: P2(타임아웃 워치독과 미적용 통신), P3(파일 종료 신호와 ack 경쟁), P16(난수와 재현성)

## 확인 범위

- [DAO_Main.py](5_DAO/SRC/DAO_Main.py) 전체(10,428줄)에서 MPI 호출 지점 전수 수집(`comm.*`, `MPI_Barrier`, `_safe_bcast`, `_safe_gather`, `_mpi_comm_with_timeout`) 후 해당 구간 정독
- 워치독 구현부 [DAO_Main.py:6685-6995](5_DAO/SRC/DAO_Main.py#L6685), 종료 플래그 구현부 [DAO_Main.py:1045-1246](5_DAO/SRC/DAO_Main.py#L1045), 테스트 루프 [DAO_Main.py:8937-9009](5_DAO/SRC/DAO_Main.py#L8937), 메인 최적화 루프 [DAO_Main.py:8003-8187](5_DAO/SRC/DAO_Main.py#L8003), GEN_SINGLE_ROW 루프 [DAO_Main.py:10027-10190](5_DAO/SRC/DAO_Main.py#L10027), 시드 설정 [DAO_Main.py:8746-8784](5_DAO/SRC/DAO_Main.py#L8746)
- [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py) 전체, [DAO_Config.py](5_DAO/SRC/DAO_Config.py)의 TIME_CONFIG, DEBUG_CONFIG, REFC_CONFIG, SPEED_TEST_REFC_CONFIG
- AST로 집단 통신이 rank 분기 안에 들어간 자리 전수 검사
- 로컬에서 mpi4py 4.1.1 기본 rc 값과 제공 스레드 수준, `random.getstate()` 직렬화 크기 실측

---

## 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|------|----------|------|
| M2-1 | CRITICAL | P2㉰ | 배리어 타임아웃 3600초가 단일 ECC 실행 허용치 36000초보다 짧아 정상 동작을 중단시킨다 | [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692), [DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840) | 한 rank의 ECC 1회가 1시간을 넘김 | 배리어 전용 타임아웃을 `SIM_MAX_TIME_OUT` 기준으로 재정의 |
| M2-2 | CRITICAL | P2㉯ | Test_Core_Speed의 `comm.allgather`가 워치독 없이 Run_ECC 바로 뒤에 놓여 hang 시 영구 정지 | [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049) | speed test ECC가 한 rank에서 멈춤 | `_mpi_comm_with_timeout`으로 감싼 `_safe_allgather` 추가 |
| M2-3 | HIGH | P2㉮㉠ | 모든 MPI 호출이 보조 스레드에서 실행되는데 제공 스레드 수준을 확인하지 않는다 | [DAO_Constants.py:3](5_DAO/SRC/DAO_Constants.py#L3), [DAO_Main.py:6931](5_DAO/SRC/DAO_Main.py#L6931) | MPI_THREAD_MULTIPLE 미만을 제공하는 빌드 | 시작 시 `MPI.Query_thread()` 확인 후 미달이면 중단 |
| M2-4 | HIGH | P3㉲㉳ | `_Report_Missing_Acks`가 동기화 배리어 앞에서 돌고 ack 파일을 지우지 않아 판정이 양방향으로 틀린다 | [DAO_Main.py:8989](5_DAO/SRC/DAO_Main.py#L8989), [DAO_Main.py:1211](5_DAO/SRC/DAO_Main.py#L1211) | 항상 | 배리어 뒤로 이동, `Initialize_Run_ECC_End_Flag`에서 ack 폴더 비우기 |
| M2-5 | HIGH | P3㉮㉱ | GEN_SINGLE_ROW가 dao_end_flag를 rank마다 직접 읽고 break한다 | [DAO_Main.py:10058](5_DAO/SRC/DAO_Main.py#L10058) | GEN_SINGLE_ROW 모드에서 사용자가 종료 플래그 기록 | root가 읽고 `_safe_bcast` (8071-8077과 같은 모양) |
| M2-6 | MEDIUM | P3㉯ | 플래그 파일 읽기가 FileNotFoundError만 잡아 PermissionError에서 한 rank만 abort 한다 | [DAO_Main.py:1091](5_DAO/SRC/DAO_Main.py#L1091), [DAO_Main.py:1105](5_DAO/SRC/DAO_Main.py#L1105) | Windows에서 편집기로 플래그 파일을 연 채 저장 | except 절을 `(OSError, ValueError)`로 확장 |
| M2-7 | MEDIUM | P3㉱ | GEN_SINGLE_ROW 루프가 in-loop 집계 없이 Check_Test_End를 불러 낡은 오류 수로 종료를 정한다 | [DAO_Main.py:10096-10102](5_DAO/SRC/DAO_Main.py#L10096) | GEN_SINGLE_ROW를 LOAD_UNCOR가 아닌 seed 모드로 실행 | 루프 안에 `Gather_Ref_C_Results(is_test_end=False)` 추가 |
| M2-8 | MEDIUM | P16㉮ | base_seed가 초 단위 시계라 같은 초에 띄운 세션들이 같은 난수열을 쓴다 | [DAO_Main.py:8750](5_DAO/SRC/DAO_Main.py#L8750) | 스크립트로 여러 세션 동시 기동 | 해상도와 엔트로피를 올리고 rank 오프셋을 해시로 |
| M2-9 | MEDIUM | P16 | speed test 고정 시드 `CORE_SPEED_TEST_SEED`가 ECC에 전달되지 않는다 | [DAO_Config.py:237](5_DAO/SRC/DAO_Config.py#L237), [DAO_Main.py:6471](5_DAO/SRC/DAO_Main.py#L6471) | ENABLE_CORE_SPEED_TEST=True | 시드 인자를 실제로 전달하거나 죽은 설정과 docstring 정리 |
| M2-10 | MEDIUM | P2㉢ | `MPI_Barrier`와 `Check_Barrier_Sync`는 통신 예외에서 상태 스냅샷을 남기지 않는다 | [DAO_Main.py:6690](5_DAO/SRC/DAO_Main.py#L6690), [DAO_Main.py:6713](5_DAO/SRC/DAO_Main.py#L6713) | 배리어에서 MPI 예외 발생 | 예외 처리를 `_mpi_comm_with_timeout` 안으로 모은다 |
| M2-11 | MEDIUM | P2㉰ | 타임아웃 설정값과 주석이 실제 동작과 어긋난다 | [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323) | 항상 | bcast용과 배리어용 두 설정으로 분리 |
| M2-12 | MEDIUM | P16㉱ | trial마다 base64 난수 상태 약 5 KB를 root 로그에 남기고, 그 상태로는 해당 trial이 재현되지 않는다 | [DAO_Main.py:2355-2359](5_DAO/SRC/DAO_Main.py#L2355) | 항상 | 기록을 debug 설정 아래로 내리고 별도 파일로 분리 |
| M2-13 | MEDIUM | P3 | 제외된 코어가 종료 플래그를 바쁜 대기로 폴링한다 | [DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968), [DAO_Main.py:7928](5_DAO/SRC/DAO_Main.py#L7928) | excluded_cores가 있거나 uncor 없는 채널 | 해당 rank는 while 루프를 건너뛰게 한다 |
| M2-14 | LOW | P16㉰ | `np.random.seed`가 아무도 쓰지 않는 상태를 심고, 복원 뒤 전 rank의 `random` 스트림이 같아진다 | [DAO_Main.py:8755](5_DAO/SRC/DAO_Main.py#L8755), [DAO_Main.py:8780](5_DAO/SRC/DAO_Main.py#L8780) | ENABLE_GET_RANDOM_STATE_FROM_CONFIG=True | 죽은 시드 제거, 재시도 지연은 별도 난수 스트림 |
| M2-15 | LOW | P3 | `Debug_Pause`의 배리어가 break 앞뒤로 갈려 되살리면 barrier count가 어긋난다 | [DAO_Main.py:1370-1386](5_DAO/SRC/DAO_Main.py#L1370) | `ENABLE_FILE_BREAKPOINT=True`로 되살릴 때 | root 판정 후 bcast, 배리어를 루프 앞 한 곳으로 |
| M2-16 | LOW | P2㉯ | 타임아웃 없는 allgather가 호출되지 않는 `MPI_Debug_Logging`에 남아 있다 | [DAO_Main.py:7011](5_DAO/SRC/DAO_Main.py#L7011) | 해당 함수를 되살릴 때 | 함수 삭제 |
| M2-17 | LOW | P3 | `_Write_Stop_Idx`가 쓴 값을 읽는 곳이 없다 | [DAO_Main.py:1136](5_DAO/SRC/DAO_Main.py#L1136), [DAO_Main.py:10060](5_DAO/SRC/DAO_Main.py#L10060) | GEN_SINGLE_ROW 재시작 | 읽어 이어붙이거나 파일과 함수를 함께 제거 |
| M2-18 | LOW | P2㉱ | MPI_Abort가 `comm.Abort` 전에 무거운 진단을 써서 통신 스레드와의 동시 진입 구간이 길어진다 | [DAO_Main.py:6839-6865](5_DAO/SRC/DAO_Main.py#L6839) | 타임아웃 abort | 스택 수집 깊이 제한 |

---

## M2-1 (CRITICAL, P2㉰) 배리어 타임아웃이 ECC 실행 허용치보다 짧다

### 근거

```python
# DAO_Main.py:6685-6695
def MPI_Barrier(self) -> None:
    self._mpi_comm_with_timeout(
        self.comm.Barrier,
        timeout_seconds=max(TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS, 3600),
        comm_name=f"MPI_Barrier[{self.barrier_count}]"
    )
    self.barrier_count += 1  # 성공 후에만 증가
```

한편 한 번의 ECC 실행에 허용된 시간은 이렇게 잡혀 있다.

```python
# DAO_Constants.py:144
SIM_MAX_TIME_OUT = 10 * 60 * 60
# DAO_Main.py:7939
subprocess.run(["cmd", "/c", ...], check=True, timeout=SIM_MAX_TIME_OUT)
```

코드 스스로 ECC 1회에 최대 36,000초를 허용해 놓고, 그 ECC가 끝나기를 기다리는 배리어에는 3,600초 상한을 걸었다.

### 이 두 값이 만나는 자리

[DAO_Main.py:8968-8991](5_DAO/SRC/DAO_Main.py#L8968)의 테스트 루프는 rank끼리 비동기다. 루프 안에는 집단 통신이 없고, 각 rank는 `8_End_flag/run_ecc_end_flag.txt`를 읽어 스스로 빠져나온다.

```python
# DAO_Main.py:8968-8991
while not self.is_test_end:
    self.Read_Run_ECC_End_Flag()
    if self.is_test_end:
        self._Write_Run_ECC_End_Ack()
        break
    ...
    self.Run_ECC(ch_idx=ch_idx)          # 최대 36,000초
    if not is_load_seed_mode:
        self.Gather_Ref_C_Results(..., is_test_end=False)   # root만 파일 읽기
    self.Check_Test_End(ch_idx=ch_idx)   # root만 플래그 기록

self._Write_Run_ECC_End_Ack()
self._Report_Missing_Acks()
self.Gather_Ref_C_Results(..., is_test_end=True)   # 이 안의 첫 줄이 MPI_Barrier
```

### 재현 조건

RUN_OPTIMIZATION 모드, rank 수 무관. worker W가 플래그를 "0"으로 읽고([DAO_Main.py:8970](5_DAO/SRC/DAO_Main.py#L8970)) 새 `Run_ECC`에 들어간 직후, root가 누적 오류 수를 채워 플래그를 "1"로 쓴다([DAO_Main.py:1068](5_DAO/SRC/DAO_Main.py#L1068)). W는 그 ECC가 끝나기 전에는 플래그를 다시 읽지 않는다. root는 먼저 루프를 나와 [DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840)의 `MPI_Barrier`에서 기다린다. W의 그 한 번의 ECC가 3,600초를 넘기면 root의 배리어가 타임아웃되어 `MPI_Abort`를 부르고([DAO_Main.py:6938](5_DAO/SRC/DAO_Main.py#L6938)) 작업 전체가 죽는다. 아무것도 고장나지 않았는데 죽는다.

메모리 재시도까지 겹치면 여유가 더 줄어든다. `Run_ECC`는 Errno 12에서 최대 10회, 회당 0에서 60초 사이를 쉰다([DAO_Main.py:7948](5_DAO/SRC/DAO_Main.py#L7948)). 실행 시간에 최대 600초가 더 붙는다.

### 처방

㉮ `TIME_CONFIG`에 배리어 전용 값을 새로 정의한다.

```python
# DAO_Config.py TIME_CONFIG
MPI_BARRIER_TIMEOUT_SECONDS = SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY + 600
```

㉯ [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692)의 `max(TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS, 3600)`을 `TIME_CONFIG.MPI_BARRIER_TIMEOUT_SECONDS`로 바꾼다. 코드에 박힌 3600은 지운다.

㉰ 더 좁히고 싶다면, 테스트 루프를 나온 뒤 `Gather_Ref_C_Results` 앞에 "모든 rank가 ECC를 끝냈다"를 알리는 배리어를 하나 넣고 그 배리어만 긴 상한을 쓴다. 그 뒤의 배리어와 bcast는 짧은 상한을 쓰면 되므로, 진짜 deadlock을 빨리 잡는 능력을 잃지 않는다.

---

## M2-2 (CRITICAL, P2㉯) Test_Core_Speed의 allgather에 워치독이 없다

### 근거

```python
# DAO_Main.py:9044-9050
start_time = time.time()
self.Run_ECC(ch_idx=0)
elapsed_time = time.time() - start_time

all_elapsed_times = self.comm.allgather(elapsed_time)
```

타임아웃을 거치지 않는 집단 통신은 세 곳이며, 각각의 노출도가 다르다.

| 위치 | 함수 | 앞선 동기화 | 판정 |
|------|------|------------|------|
| [DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861) `comm.Reduce` | Gather_Ref_C_Results | 바로 앞 [DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840) 배리어 | 위험 낮음 (아래 "문제 없던 항목" 참조) |
| [DAO_Main.py:7011](5_DAO/SRC/DAO_Main.py#L7011) `comm.allgather` | MPI_Debug_Logging | 호출되는 곳 없음 | 죽은 코드 (M2-16) |
| [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049) `comm.allgather` | Test_Core_Speed | 없음. 직전이 `Run_ECC` | **위험 높음** |

9049는 rank마다 실행 시간이 다른 것을 측정하려고 일부러 비동기 구간을 만든 직후의 첫 집단 통신이다. 워치독이 필요한 자리 중 가장 필요한 자리인데 유일하게 빠져 있다.

### 재현 조건

`SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST = True`(현재 기본값). 어떤 rank의 speed test용 ECC가 멈추거나 그 노드가 죽으면, 나머지 전 rank가 9049에서 무기한 대기한다. `MPI_Barrier`라면 3600초 뒤 타임아웃 메시지와 스택 덤프를 남기지만 여기서는 로그가 한 줄도 남지 않는다. `Periodic_Recheck` 경로([DAO_Main.py:9128](5_DAO/SRC/DAO_Main.py#L9128))도 같은 함수를 다시 부르므로 최적화 도중에도 같은 일이 생긴다.

### 처방

㉮ `_safe_bcast`, `_safe_gather`와 같은 모양으로 `_safe_allgather`를 [DAO_Main.py:6995](5_DAO/SRC/DAO_Main.py#L6995) 뒤에 추가한다.

```python
def _safe_allgather(self, data, comm_name: str = "allgather", timeout_seconds=None):
    try:
        return self._mpi_comm_with_timeout(
            self.comm.allgather, data,
            timeout_seconds=timeout_seconds, comm_name=comm_name)
    except Exception as e:
        self.Write_MPI_Error_Snapshot(e, comm_name)
        self.MPI_Abort(f"{comm_name} failed: {type(e).__name__}: {e}")
```

㉯ [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049)를 `self._safe_allgather(elapsed_time, "Allgather_core_speed", timeout_seconds=TIME_CONFIG.MPI_BARRIER_TIMEOUT_SECONDS)`로 바꾼다. 상한은 M2-1에서 새로 정의한 배리어 상한과 같은 값을 쓴다.

㉰ [DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861)의 `Reduce`도 같은 방식으로 감싸 두면 세 통로의 진단이 한 모양이 된다.

---

## M2-3 (HIGH, P2㉮㉠) 제공 스레드 수준을 확인하지 않는다

### 근거

```python
# DAO_Constants.py:3, 135-137
from mpi4py import MPI
...
comm = MPI.COMM_WORLD
```

`import mpi4py`와 `mpi4py.rc` 설정은 저장소 어디에도 없다(`grep -rn "mpi4py" 5_DAO/` 결과는 `DAO_Constants.py`와 `reference/` 사본 두 줄뿐). mpi4py 기본값은 `rc.threads=True`, `rc.thread_level='multiple'`이므로 `MPI_Init_thread`에 MULTIPLE을 **요청**한다. 요청과 제공은 다르다. 그리고 코드 어디에서도 `MPI.Query_thread()`를 읽지 않는다.

### 왜 문제인가

`_mpi_comm_with_timeout`은 MPI 호출을 전부 보조 스레드로 옮긴다.

```python
# DAO_Main.py:6921-6942
def comm_thread():
    try:
        result[0] = comm_func(*args, **kwargs)
    ...
thread = threading.Thread(target=comm_thread, daemon=True)
thread.start()

if not completed.wait(timeout=timeout_seconds):
    error_msg = f"{comm_name} timed out after {timeout_seconds} seconds. ..."
    self.MPI_Abort(error_msg)
```

㉮ 정상 경로에서는 본 스레드가 `completed.wait`로 막혀 있으므로 한 번에 한 스레드만 MPI 안에 있다. 이는 MPI_THREAD_SERIALIZED면 충분하다. 다만 `MPI_Init_thread`를 부른 스레드가 아닌 스레드에서 호출하므로 MPI_THREAD_FUNNELED로는 부족하다. FUNNELED만 제공하는 빌드에서는 DAO의 **모든** 집단 통신이 규격 밖 동작이 된다.

㉯ 타임아웃 경로에서는 조건이 더 세진다. `self.MPI_Abort(error_msg)`가 도는 동안 통신 스레드는 여전히 같은 communicator의 집단 통신 안에 살아 있다(daemon 스레드이며 취소하지 않는다). `MPI_Abort`는 로그 기록과 스택 덤프를 마친 뒤 [DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894)에서 `self.comm.Abort(error_code)`를 부른다. 이 순간 두 스레드가 동시에 MPI 안에 있으므로 MPI_THREAD_MULTIPLE이 필요하다.

### 확인한 것

이 환경(Windows, MS-MPI 10.1, mpi4py 4.1.1)에서 `MPI.Query_thread()`는 3(MPI_THREAD_MULTIPLE)을 돌려준다. 로컬은 만족한다. DAO를 실제로 돌리는 클러스터의 MPI 빌드는 이 저장소에서 확인할 수 없다.

### 처방

`LLR_OPT.Setup` 맨 앞([DAO_Main.py:8706](5_DAO/SRC/DAO_Main.py#L8706) 직전)에 한 줄짜리 점검을 넣는다.

```python
provided = MPI.Query_thread()
if provided < MPI.THREAD_MULTIPLE:
    self.MPI_Abort(
        f"MPI thread level too low: provided={provided}, required={MPI.THREAD_MULTIPLE}. "
        f"DAO runs every MPI call on a watchdog thread and calls Abort while a collective is in flight."
    )
```

`Setup`은 첫 `_safe_bcast`([DAO_Main.py:8708](5_DAO/SRC/DAO_Main.py#L8708))보다 앞서므로, 규격 미달 환경에서 원인을 알 수 없는 hang 대신 명시적인 메시지로 끝난다.

---

## M2-4 (HIGH, P3㉲㉳) ack 판정이 두 방향으로 틀린다

### 근거

```python
# DAO_Main.py:8987-8991
# while 루프 탈출 경로와 무관하게 모든 프로세스가 ack 작성
self._Write_Run_ECC_End_Ack()
self._Report_Missing_Acks()

self.Gather_Ref_C_Results(matrix=matrix, ch_idx=ch_idx, is_test_end=True)
```

`Gather_Ref_C_Results(is_test_end=True)`의 첫 줄이 `MPI_Barrier`다([DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840)). 즉 8989는 유일한 동기화 지점보다 **앞**이다.

### 거짓 양성: 정상 rank가 미응답으로 기록된다

root가 8988에서 자기 ack를 쓰고 바로 8989를 부른다. 이 시점에 worker들은 대부분 아직 각자의 `Run_ECC` 안이다(M2-1에서 본 그대로다). `_Report_Missing_Acks`는 그 순간의 디렉토리를 훑는다.

```python
# DAO_Main.py:1236-1244
expected_ranks = set(range(self.num_process)) - set(self.excluded_cores)
missing_ranks = sorted(expected_ranks - acked_ranks)

status_path = os.path.join(status_dir, "missing_acks.txt")
if missing_ranks:
    with open(status_path, "w") as f:
        f.write(f"Missing acks: {', '.join(f'rank {r}' for r in missing_ranks)}\n")
```

그래서 `missing_acks.txt`에는 멀쩡히 일하는 rank가 줄줄이 실린다. 이 파일은 배리어 뒤에 다시 계산되지 않으므로 바로잡히지 않는다.

### 거짓 음성: 한 번 ack한 rank는 영원히 ack한 것이 된다

```python
# DAO_Main.py:1200-1206
ack_dir = os.path.join(self.end_flag_dir, "run_ecc_ack")
os.makedirs(ack_dir, exist_ok=True)
ack_path = os.path.join(ack_dir, f"run_ecc_end_ack_rank{self.rank}.txt")
```

파일 이름은 rank마다 고정이며 매번 덮어쓴다. 그리고 이 디렉토리를 비우는 코드가 없다. `Initialize_Run_ECC_End_Flag`([DAO_Main.py:2165](5_DAO/SRC/DAO_Main.py#L2165))는 `run_ecc_end_flag.txt`만 건드리고, `Initialize_End_Flags`([DAO_Main.py:2172](5_DAO/SRC/DAO_Main.py#L2172))는 trial/dao 플래그만 건드리며, `Cleanup_Test_Environment`([DAO_Main.py:935](5_DAO/SRC/DAO_Main.py#L935))는 `local_session_dir` 아래만 훑는다. 따라서 채널 0에서 한 번 ack한 rank는 이후 어떤 채널, 어떤 trial에서 응답하지 않아도 계속 ack한 것으로 집계된다. 원래 잡으려던 "응답 없는 rank"를 세션 두 번째 테스트부터는 절대 잡지 못한다.

`elif os.path.exists(status_path): os.remove(status_path)`([DAO_Main.py:1245-1246](5_DAO/SRC/DAO_Main.py#L1245))가 있어, 두 번째 테스트부터는 파일이 지워진다. 결국 이 진단은 첫 채널에서는 거짓 양성을 내고, 그 뒤로는 무조건 "이상 없음"을 낸다.

### 재현 조건

rank 2개 이상, 어떤 설정이든. 첫 채널 테스트가 끝나면 `8_End_flag/run_ecc_ack_status/missing_acks.txt`에 정상 rank들이 실리고, 두 번째 채널 테스트가 끝나면 그 파일이 지워진다.

### 처방

㉮ `_Report_Missing_Acks` 호출을 배리어 뒤로 옮긴다. [DAO_Main.py:8989](5_DAO/SRC/DAO_Main.py#L8989)의 줄을 지우고 [DAO_Main.py:8991](5_DAO/SRC/DAO_Main.py#L8991)의 `Gather_Ref_C_Results` 다음 줄로 옮긴다. GEN_SINGLE_ROW의 [DAO_Main.py:10105](5_DAO/SRC/DAO_Main.py#L10105)도 같은 방식으로 [DAO_Main.py:10107](5_DAO/SRC/DAO_Main.py#L10107) 뒤로 옮긴다.

㉯ `Initialize_Run_ECC_End_Flag`([DAO_Main.py:2165-2170](5_DAO/SRC/DAO_Main.py#L2165))에 root의 ack 폴더 비우기를 추가한다. 이 함수는 `Set_Test_Environment`의 두 배리어 사이에서 불리므로([DAO_Main.py:8460](5_DAO/SRC/DAO_Main.py#L8460), [DAO_Main.py:8478](5_DAO/SRC/DAO_Main.py#L8478)) 추가 동기화가 필요 없다.

```python
def Initialize_Run_ECC_End_Flag(self):
    PATH_CONFIG.RUN_ECC_END_FLAG_FILE_PATH = os.path.join(self.end_flag_dir, RUN_ECC_END_FLAG_FILE_NAME)
    if self.is_root:
        self._Write_End_Flag(PATH_CONFIG.RUN_ECC_END_FLAG_FILE_PATH, False)
        shutil.rmtree(os.path.join(self.end_flag_dir, "run_ecc_ack"), ignore_errors=True)
```

㉰ 한 걸음 더 나아가려면 ack 파일 이름에 `current_LLR_matrix_idx`와 `ch_idx`를 넣어 어느 테스트의 응답인지 파일 이름만으로 알 수 있게 한다.

---

## M2-5 (HIGH, P3㉮㉱) GEN_SINGLE_ROW의 종료 플래그가 rank마다 따로 읽힌다

### 근거

메인 최적화 루프는 이 판정을 올바르게 다룬다.

```python
# DAO_Main.py:8071-8078
if self.is_root:
    is_dao_end = self.Read_DAO_End_Flag()
    trial_skip_count = self.Read_Trial_End_Flag()
else:
    is_dao_end = False
    trial_skip_count = 0
is_dao_end = self._safe_bcast(is_dao_end if self.is_root else None, "Bcast_dao_end_flag")
trial_skip_count = self._safe_bcast(trial_skip_count if self.is_root else None, "Bcast_trial_end_flag")
```

GEN_SINGLE_ROW 루프는 같은 판정을 rank마다 따로 한다.

```python
# DAO_Main.py:10054-10067
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

배리어가 읽기 **앞**에 있으므로 읽는 시점은 서로 가깝지만, 읽는 값이 같다는 보장은 없다. 사용자가 `dao_end_flag.txt`에 값을 쓰는 순간은 이 배리어와 아무 관계가 없다. `open(path, "w")`는 먼저 자르고 뒤에 쓰므로, 그 사이에 읽은 rank는 빈 문자열을 얻고 `_Read_End_Flag`는 `"" == "1"`이 거짓이라 False를 돌려준다([DAO_Main.py:1095](5_DAO/SRC/DAO_Main.py#L1095)).

### 어긋나면 벌어지는 일

True를 읽은 rank는 `_gen_single_row_stop_idx`를 세우고 다음 체크 지점에서 `break`하여 [DAO_Main.py:10190](5_DAO/SRC/DAO_Main.py#L10190)의 배리어로 내려간다. False를 읽은 rank는 계속 돌며 [DAO_Main.py:10075](5_DAO/SRC/DAO_Main.py#L10075)의 `_safe_bcast`와 [DAO_Main.py:10120](5_DAO/SRC/DAO_Main.py#L10120)의 배리어를 만난다. MPI 배리어에는 태그가 없어 서로 다른 지점의 배리어가 짝을 이루며 통과하고, rank별 `barrier_count`만 어긋난다. 그 상태로 다음 단계에 들어가면 `_safe_bcast`가 배리어와 짝지어져 1200초 타임아웃에 걸리거나, `Check_Barrier_Sync`([DAO_Main.py:2259](5_DAO/SRC/DAO_Main.py#L2259), [DAO_Main.py:2345](5_DAO/SRC/DAO_Main.py#L2345))가 barrier count 불일치로 `MPI_Abort` 한다. 어느 쪽이든 사용자가 "정상 종료"를 요청한 결과가 비정상 종료다.

`_Write_Stop_Idx`가 root 전용인 것([DAO_Main.py:1127-1128](5_DAO/SRC/DAO_Main.py#L1127))도 이 구조를 드러낸다. 판정은 전 rank가 하는데 기록은 root만 한다.

### 재현 조건

`DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.GEN_SINGLE_ROW`, `SINGLE_ROW_CONFIG.END_FLAG_CHECK_INTERVAL > 0`. 사용자가 `8_End_flag/dao_end_flag.txt`를 편집해 "1"을 저장하는 시점이 체크 지점과 겹치면 발생한다. 공유 파일 시스템에서 rank마다 캐시 갱신 시점이 다르면 겹치지 않아도 발생한다.

### 처방

[DAO_Main.py:10056-10067](5_DAO/SRC/DAO_Main.py#L10056)을 메인 루프와 같은 모양으로 다시 쓴다.

```python
if end_flag_interval > 0 and candidate_idx % end_flag_interval == 0:
    self.MPI_Barrier()
    if self.is_root:
        is_dao_end = self._gen_single_row_stop_idx is None and self.Read_DAO_End_Flag()
    else:
        is_dao_end = False
    is_dao_end = self._safe_bcast(is_dao_end if self.is_root else None, "Bcast_dao_end_flag_single_row")
    if is_dao_end:
        self._gen_single_row_stop_idx = candidate_idx + end_flag_interval
        self._Write_Stop_Idx(self._gen_single_row_stop_idx)
        self.Write_Log_Lines(...)
    if self._gen_single_row_stop_idx is not None and candidate_idx >= self._gen_single_row_stop_idx:
        self.Write_Log_Lines(...)
        break
```

`_gen_single_row_stop_idx`를 bcast된 `is_dao_end`로만 세우므로 전 rank가 같은 candidate에서 break 한다.

---

## M2-6 (MEDIUM, P3㉯) 플래그 파일 읽기의 예외 범위가 좁다

### 근거

```python
# DAO_Main.py:1091-1097
def _Read_End_Flag(self, file_path: str) -> bool:
    try:
        with open(file_path, "r") as f:
            return f.read().strip() == "1"
    except FileNotFoundError:
        return False
```

```python
# DAO_Main.py:1105-1115
def _Read_End_Flag_Count(self, file_path: str) -> int:
    try:
        with open(file_path, "r") as f:
            value = f.read().strip()
            if value.isdigit():
                return int(value)
            self.Write_Log_Lines(f"[WARN] _Read_End_Flag_Count: Invalid value '{value}' in {file_path}, using 0")
            return 0
    except (FileNotFoundError, ValueError):
        return 0
```

잡는 예외가 `FileNotFoundError`(와 `ValueError`)뿐이다.

### 재현 조건

㉮ Windows에서 사용자가 편집기로 `dao_end_flag.txt`를 열어 둔 채 저장하는 순간, 다른 프로세스의 `open(..., "r")`이 `PermissionError`를 던진다. 종료 플래그는 사람이 파일을 만들어 조작하는 통로이므로 이 상황이 정확히 정상 사용 경로다.

㉯ 네트워크 파일 시스템에서 `OSError(ESTALE)`나 `OSError(EIO)`가 나는 경우도 같다.

두 경우 모두 예외가 `Read_DAO_End_Flag` 밖으로 나가 `Run_Optimization`, `LLR_OPT.Main`을 지나 `Main()`의 최상위 except([DAO_Main.py:10407](5_DAO/SRC/DAO_Main.py#L10407))에 잡히고, 그 rank가 `MPI_Abort`로 작업 전체를 죽인다. 메인 루프에서는 root만 읽으므로 root만 이 위험을 지지만, [DAO_Main.py:8970](5_DAO/SRC/DAO_Main.py#L8970)과 [DAO_Main.py:10058](5_DAO/SRC/DAO_Main.py#L10058)은 전 rank가 읽는다.

### 확인한 것 (정상 동작)

잘린 값이나 빈 값 자체는 안전하다. `_Read_End_Flag`는 `"" == "1"`이 거짓이라 False를 주고, `_Read_End_Flag_Count`는 `"".isdigit()`이 거짓이라 경고를 남기고 0을 준다. 다만 그 "안전한" 결과가 M2-5에서 본 rank 사이 불일치의 재료가 된다.

### 처방

세 함수의 except 절을 넓힌다. `_Read_Stop_Idx`([DAO_Main.py:1136-1144](5_DAO/SRC/DAO_Main.py#L1136))도 같다.

```python
except (OSError, ValueError):
    return False       # _Read_End_Flag
```

읽기 실패를 "플래그 없음"으로 보는 것이 종료 신호의 안전한 쪽이다. 실패가 잦으면 눈에 띄도록 root에서 `Write_Log_Lines`로 한 줄 남긴다.

---

## M2-7 (MEDIUM, P3㉱) GEN_SINGLE_ROW가 낡은 오류 수로 종료를 정한다

### 근거

`Check_Test_End`의 종료 판정은 `self.total_num_errors[ch_idx]`를 본다.

```python
# DAO_Main.py:1066-1069
if self.is_root:
    if self.total_num_errors[ch_idx] >= self.max_error:
        self.Write_Run_ECC_End_Flag(True)
self.Read_Run_ECC_End_Flag()
```

이 값을 갱신하는 곳은 `Gather_Ref_C_Results`뿐이다([DAO_Main.py:1889](5_DAO/SRC/DAO_Main.py#L1889)). `Test_LLR`은 루프 안에서 갱신한 뒤 판정한다.

```python
# DAO_Main.py:8976-8980
self.Run_ECC(ch_idx=ch_idx)
if not is_load_seed_mode:
    self.Gather_Ref_C_Results(matrix=matrix, ch_idx=ch_idx, is_test_end=False)
self.Check_Test_End(ch_idx=ch_idx)
```

GEN_SINGLE_ROW 루프에는 그 갱신 호출이 없다.

```python
# DAO_Main.py:10096-10107
while not self.is_test_end:
    self.Read_Run_ECC_End_Flag()
    if self.is_test_end:
        self._Write_Run_ECC_End_Ack()
        break
    self.Run_ECC(ch_idx=ch_idx)
    self.Check_Test_End(ch_idx=ch_idx)      # total_num_errors 갱신 없이 판정

self._Write_Run_ECC_End_Ack()
self._Report_Missing_Acks()

self.Gather_Ref_C_Results(matrix=candidate_matrix, ch_idx=ch_idx, is_test_end=True)
```

### 재현 조건

GEN_SINGLE_ROW를 LOAD_UNCOR 모드가 아닌 seed 모드(`SeedMode.DEFAULT`)로 돌릴 때 드러난다. LOAD_UNCOR 모드에서는 `Check_Test_End`의 첫 분기가 걸려 루프가 1회로 끝나므로([DAO_Main.py:1057-1060](5_DAO/SRC/DAO_Main.py#L1057)) 증상이 없다. [DAO_Main.py:10082](5_DAO/SRC/DAO_Main.py#L10082)의 주석이 "LOAD_UNCOR 모드"를 전제하고 있으나 그 전제를 강제하는 검사는 없다.

DEFAULT 모드로 돌리면 ㉮ 첫 candidate의 첫 채널은 `total_num_errors`가 0이라 종료 조건을 만족하지 못해 루프가 계속 돌고 ㉯ 이전 채널의 최종 집계가 max_error 이상으로 남은 뒤부터는 매번 첫 판정에서 종료 플래그가 서서 각 candidate가 ECC를 1회만 돌고 끝난다. candidate마다 시행 횟수가 달라 FER 비교와 ranking([DAO_Main.py:10164](5_DAO/SRC/DAO_Main.py#L10164))이 서로 다른 표본 크기를 비교하게 된다.

### 처방

㉮ [DAO_Main.py:10101](5_DAO/SRC/DAO_Main.py#L10101)과 [DAO_Main.py:10102](5_DAO/SRC/DAO_Main.py#L10102) 사이에 `Test_LLR`과 같은 줄을 넣는다.

```python
self.Run_ECC(ch_idx=ch_idx)
if not self.is_load_seed_mode:
    self.Gather_Ref_C_Results(matrix=candidate_matrix, ch_idx=ch_idx, is_test_end=False)
self.Check_Test_End(ch_idx=ch_idx)
```

㉯ 더 나은 길은 이 루프를 `Test_LLR`과 합치는 것이다. GEN_SINGLE_ROW 루프는 `Test_LLR`의 채널 루프를 CSW 파싱 한 단계 때문에 통째로 복사한 형태다. `Test_LLR`에 채널별 후처리 콜백을 받는 인자를 하나 두면 두 벌의 종료 판정을 한 벌로 줄일 수 있다(가독성 팀 R의 중복 제거 목록과 겹친다).

---

## M2-8 (MEDIUM, P16㉮) base_seed가 초 단위 시계다

### 근거

```python
# DAO_Main.py:8746-8756
def Set_Python_Seed(self):
    if DEBUG_CONFIG.ENABLE_DEBUG_MODE:
        base_seed = 0
    else:
        base_seed = int(time.time()) if self.is_root else None
    self.base_seed = self._safe_bcast(base_seed if self.is_root else None, "Bcast_base_seed")
    local_init_seed = self.base_seed + self.rank * 10000

    random.seed(local_init_seed)
    np.random.seed(local_init_seed)
    self.Write_Log_Lines(f"[Base seed] {base_seed}")
```

### 시드 공간 분석

㉮ **한 세션 안에서는 겹치지 않는다.** 간격이 10000으로 고정이므로 rank 수가 아무리 커도 `b, b+10000, b+20000, ...`는 모두 다르다. 배정 질문 "rank 수가 커질 때 겹치는지"의 답은 "겹치지 않는다"이다.

㉯ **세션 사이에서 겹친다.** `int(time.time())`은 해상도가 1초다. 같은 초에 시작한 두 세션은 rank별 시드가 **완전히 같다**. 스크립트로 여러 DAO 세션을 한꺼번에 띄우면 실제로 일어난다. 매트릭스 생성은 root만 하므로([DAO_Main.py:1951](5_DAO/SRC/DAO_Main.py#L1951)의 `if self.is_root:`), 이는 두 세션이 똑같은 mutation 순서를 따라가며 똑같은 후보를 탐색한다는 뜻이다. 병렬 탐색의 이득이 사라진다.

㉰ 10000의 배수(약 2.78시간의 배수)만큼 떨어져 시작한 두 세션은 rank j와 rank j+k가 같은 시드를 쓴다. 오늘 worker가 `random`을 쓰는 곳은 재시도 지연뿐이라 영향이 작지만, 시드 공간 설계로는 취약하다.

㉱ 로그에 남는 것은 `base_seed`뿐이고 실제 사용된 `local_init_seed`는 남지 않는다. 재현하려면 `+ rank * 10000` 규칙을 소스에서 찾아야 한다.

### 처방

㉮ [DAO_Main.py:8750](5_DAO/SRC/DAO_Main.py#L8750)의 해상도와 엔트로피를 올린다.

```python
base_seed = (int(time.time() * 1000) ^ os.getpid()) & 0x7FFFFFFF if self.is_root else None
```

㉯ [DAO_Main.py:8752](5_DAO/SRC/DAO_Main.py#L8752)의 고정 간격을 해시로 바꾼다.

```python
local_init_seed = random.Random((self.base_seed, self.rank)).getrandbits(32)
```

㉰ [DAO_Main.py:8756](5_DAO/SRC/DAO_Main.py#L8756)에 실제 시드를 함께 남긴다. `self.Write_Log_Lines(f"[Base seed] {self.base_seed}, [rank {self.rank} seed] {local_init_seed}")`. 다만 `Write_Log_Lines`가 root 전용이므로 root의 시드만 남는다. 전 rank 시드가 필요하면 `_safe_gather`로 모아 root가 한 줄로 적는다.

---

## M2-9 (MEDIUM, P16) speed test 고정 시드가 ECC에 닿지 않는다

### 근거

```python
# DAO_Constants.py:146-147
# Core 속도 테스트용 고정 시드 (모든 프로세스가 동일한 시드로 테스트하여 속도 측정)
CORE_SPEED_TEST_SEED = 9999
```

```python
# DAO_Config.py:236-237  (class SPEED_TEST_REFC_CONFIG)
mode_seed = 0
mode_init_seed = CORE_SPEED_TEST_SEED
```

```python
# DAO_Main.py:9020-9024  (Test_Core_Speed docstring)
"""각 코어의 속도를 사전 측정하여 느린 코어를 식별한다.

모든 프로세스가 동일한 시드(CORE_SPEED_TEST_SEED)로 짧은 테스트를 실행하고,
소요 시간을 측정하여 평균 대비 CORE_SPEED_CUTOFF_RATIO배 이상 느린 코어를 제외한다.
```

그런데 인자 목록에 `mode_init_seed`가 없다.

```python
# DAO_Main.py:6469-6471
SPEED_TEST_REFC_CONFIG.max_num_test,            #10
SPEED_TEST_REFC_CONFIG.mode_seed,           #11
self.rank,          #12 (고정 시드)
```

`grep -rn "mode_init_seed" 5_DAO --include=*.py`의 결과는 `DAO_Config.py`의 정의 두 줄뿐이다. 읽는 곳이 없다. 그리고 #12 자리에는 rank마다 다른 `self.rank`가 들어가며 주석만 "(고정 시드)"라고 적혀 있다. 같은 자리가 일반 실행에서도 `self.rank`이고([DAO_Main.py:6421](5_DAO/SRC/DAO_Main.py#L6421), [DAO_Main.py:6444](5_DAO/SRC/DAO_Main.py#L6444)), 결과 파일 이름이 `process_idx`로 만들어지는 것([DAO_Main.py:1819](5_DAO/SRC/DAO_Main.py#L1819))을 보면 #12는 프로세스 인덱스에 가깝다.

### 결과

docstring이 약속한 "모든 프로세스가 동일한 시드로 짧은 테스트"를 보장하는 코드가 없다. 그래서 `excluded_cores` 판정의 기반이 흔들린다.

```python
# DAO_Main.py:9055-9060
for rank_idx, current_time in enumerate(all_elapsed_times):
    other_times = [t for i, t in enumerate(all_elapsed_times) if i != rank_idx]
    mean_time = sum(other_times) / len(other_times) if other_times else 0.0
    if mean_time > 0 and current_time > mean_time * SPEED_TEST_REFC_CONFIG.CORE_SPEED_CUTOFF_RATIO:
        excluded_cores.append(rank_idx)
```

Ref-C가 #12를 난수 시드로 쓴다면 rank마다 다른 프레임을 복호하므로 같은 작업량의 시간 비교가 아니다. Ref-C 소스는 이 저장소에 없어(`5_DAO/Input/Ref_C/*/SRC/`가 비어 있다) 어느 쪽인지는 확인할 수 없다. 확인할 수 있는 것은 "DAO가 시드를 보내지 않는다"는 사실이다.

여기에 `fn = 1, max_num_test = 1`([DAO_Config.py:229-230](5_DAO/SRC/DAO_Config.py#L229))이라 측정 구간 자체가 매우 짧다. 프로세스 기동과 파일 입출력의 잡음이 결과를 지배하기 쉽고, 한 번 제외된 코어는 `Periodic_Recheck`가 꺼져 있으면(`RECHECK_INTERVAL_STAGES = 0`, `RECHECK_INTERVAL_SECONDS = 0`이 기본값) 세션 내내 놀게 된다.

### 처방

㉮ Ref-C 인자 규격을 확인해 초기 시드 자리가 있다면 `SPEED_TEST_REFC_CONFIG.mode_init_seed`를 그 자리에 넣는다. 일반 실행 쪽 `REFC_CONFIG.mode_init_seed`도 같은 자리에 넣어 두 경로의 인자 구성을 같게 만든다.

㉯ 그럴 자리가 없다면 `CORE_SPEED_TEST_SEED`와 두 `mode_init_seed`를 지우고, [DAO_Main.py:9023](5_DAO/SRC/DAO_Main.py#L9023)의 docstring과 [DAO_Main.py:6471](5_DAO/SRC/DAO_Main.py#L6471), [DAO_Main.py:6494](5_DAO/SRC/DAO_Main.py#L6494)의 "(고정 시드)" 주석을 실제 동작으로 다시 쓴다(#12는 프로세스 인덱스라고 적는다).

㉰ 측정 잡음을 줄이려면 `SPEED_TEST_REFC_CONFIG.max_num_test`를 올려 측정 구간을 수 초 이상으로 만들고, 제외 판정에 평균 대신 중앙값을 쓴다.

---

## M2-10 (MEDIUM, P2㉢) 배리어 경로가 스냅샷을 남기지 않는다

### 근거

`_mpi_comm_with_timeout`은 스레드가 잡은 예외를 본 스레드에서 다시 던진다.

```python
# DAO_Main.py:6940-6944
# 예외 발생 시 재발생
if exception[0] is not None:
    raise exception[0]

return result[0]
```

호출자별로 처리가 셋으로 갈린다.

| 호출자 | 예외 처리 | 스냅샷 |
|--------|----------|--------|
| `_safe_bcast` [DAO_Main.py:6946](5_DAO/SRC/DAO_Main.py#L6946) | try/except | `Write_MPI_Error_Snapshot` 후 abort |
| `_safe_gather` [DAO_Main.py:6971](5_DAO/SRC/DAO_Main.py#L6971) | try/except | `Write_MPI_Error_Snapshot` 후 abort |
| `Bcast_Trial_LLR_Mode` [DAO_Main.py:818](5_DAO/SRC/DAO_Main.py#L818) | try/except | `Write_MPI_Error_Snapshot` 후 abort |
| `MPI_Barrier` [DAO_Main.py:6690](5_DAO/SRC/DAO_Main.py#L6690) | 없음 | 없음 |
| `Check_Barrier_Sync` [DAO_Main.py:6713](5_DAO/SRC/DAO_Main.py#L6713) | 없음 | 없음 |

`Write_MPI_Error_Snapshot`은 worker의 상태를 남기는 유일한 통로다.

```python
# DAO_Main.py:6752-6755
if not self.is_root:
    comm_keywords = ["bcast", "gather", "barrier", "comm"]
    if not any(kw in context.lower() for kw in comm_keywords):
        return
```

`"barrier"`가 키워드 목록에 들어 있다는 것은 배리어 실패에서도 스냅샷을 남기려는 의도였음을 보여준다. 그런데 `MPI_Barrier`가 이 함수를 부르지 않으므로 그 키워드는 쓰이지 않는다.

### 재현 조건

배리어에서 MPI 예외(통신 상대 소실, 버퍼 오류 등)가 나면 예외가 `Main()`의 최상위 except([DAO_Main.py:10407](5_DAO/SRC/DAO_Main.py#L10407))까지 올라가 `Log_Unhandled_Exception` 후 `MPI_Abort` 한다. root는 `MPI_Abort`가 `_collect_error_state_snapshot`을 부르므로 상태가 남지만, worker는 `error_snapshot_rank{N}.log`가 생기지 않는다. 배리어 불일치는 hang의 첫 징후이므로 진단이 가장 필요한 경로에서 진단이 빠진다. 타임아웃 경로도 스냅샷 없이 곧바로 `MPI_Abort`로 간다([DAO_Main.py:6938](5_DAO/SRC/DAO_Main.py#L6938)).

### 처방

`_mpi_comm_with_timeout` 안에서 한 번에 처리해 세 벌의 try/except를 한 벌로 줄인다.

```python
# DAO_Main.py:6935-6942 를 이렇게 다시 쓴다
if not completed.wait(timeout=timeout_seconds):
    error_msg = f"{comm_name} timed out after {timeout_seconds} seconds. ..."
    self.Write_MPI_Error_Snapshot(TimeoutError(error_msg), comm_name)
    self.MPI_Abort(error_msg)

if exception[0] is not None:
    self.Write_MPI_Error_Snapshot(exception[0], comm_name)
    self.MPI_Abort(f"{comm_name} failed: {type(exception[0]).__name__}: {exception[0]}")
```

그러면 `_safe_bcast`, `_safe_gather`, `Bcast_Trial_LLR_Mode`의 except 블록은 지울 수 있고, `MPI_Barrier`와 `Check_Barrier_Sync`도 같은 진단을 얻는다. `Write_MPI_Error_Snapshot`의 worker 필터가 `comm_name`을 보고 동작하므로 배리어 이름(`MPI_Barrier[...]`)도 `"barrier"` 키워드에 걸린다.

---

## M2-11 (MEDIUM, P2㉰) 타임아웃 설정과 주석이 실제와 어긋난다

### 근거

```python
# DAO_Config.py:318-323
class TIME_CONFIG:
    """시간 제한 관련 설정"""
    MAX_STAGE_TIMEOUT_SECONDS = 1 * 60 * 60    # Stage별 최대 실행 시간 (초 단위, 기본값: 1시간). 100시간 이상이면 제한 없음과 동일
    MAX_ECC_MEMORY_RETRY = 10             # ECC 실행 메모리 에러(Errno 12) 최대 재시도 횟수
    MAX_ECC_MEMORY_RETRY_DELAY = 60       # 메모리 에러 재시도 시 최대 대기 시간 (초, 0~이 값 사이 랜덤)
    MPI_COMM_TIMEOUT_SECONDS = 2*int(MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY)  # 메모리 재시도 최대 소요시간의 2배. 1시간 이상이면 타임아웃 없음과 동일
```

㉮ 값은 `2 * 10 * 60 = 1200`초다.

㉯ "1시간 이상이면 타임아웃 없음과 동일"이라는 주석에 해당하는 코드가 없다. 타임아웃을 끄는 분기는 어디에도 없다. 1200은 1시간보다 짧으므로 문장의 조건 자체도 현재 값에 해당하지 않는다.

㉰ 배리어는 `max(MPI_COMM_TIMEOUT_SECONDS, 3600)`이라 3600초 바닥이 깔려 있다([DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692)). 따라서 설정값 1200이 실제로 쓰이는 곳은 bcast와 gather뿐이다. 설정을 읽는 사람이 "MPI 통신 상한은 1200초"라고 이해하면 배리어의 3600초를 모른 채 넘어간다.

㉱ 근거로 든 "메모리 재시도 최대 소요시간"도 정확하지 않다. 대기는 `random.uniform(0, 60)`이므로([DAO_Main.py:7948](5_DAO/SRC/DAO_Main.py#L7948)) 최대가 600초이고 기댓값은 300초다. 그리고 이 대기는 ECC 실행 시간에 **더해지는** 값이지 통신 대기 시간의 전부가 아니다. M2-1에서 보았듯 통신 대기의 실제 상한은 ECC 실행 시간이 정한다.

### 처방

`TIME_CONFIG`를 두 상한이 각각 보이도록 다시 쓴다.

```python
class TIME_CONFIG:
    """시간 제한 관련 설정"""
    MAX_STAGE_TIMEOUT_SECONDS = 1 * 60 * 60   # Stage 하나의 최대 실행 시간
    MAX_ECC_MEMORY_RETRY = 10                 # ECC 실행 메모리 에러(Errno 12) 최대 재시도 횟수
    MAX_ECC_MEMORY_RETRY_DELAY = 60           # 재시도 사이 대기 상한 (0에서 이 값 사이 랜덤)

    # bcast, gather 상한: 모든 rank가 이미 같은 지점에 모인 뒤의 통신이므로 짧게 잡는다
    MPI_COMM_TIMEOUT_SECONDS = 1200

    # 배리어 상한: ECC 한 번이 끝나기를 기다리는 자리가 있으므로 ECC 상한을 기준으로 잡는다
    MPI_BARRIER_TIMEOUT_SECONDS = SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY + 600
```

`SIM_MAX_TIME_OUT`은 `DAO_Constants.py`에 있으므로 `DAO_Config.py`에서 import 한다(`DAO_Config.py`가 이미 `DAO_Constants`의 `CORE_SPEED_TEST_SEED`를 쓰고 있어 경로는 열려 있다).

---

## M2-12 (MEDIUM, P16㉱) 난수 상태 로깅의 비용과 쓸모

### 근거

```python
# DAO_Main.py:2355-2359
# Random state 로깅 (디버깅 재현용) - base64 인코딩으로 압축
rng_state = random.getstate()
state_bytes = pickle.dumps(rng_state)
state_b64 = base64.b64encode(state_bytes).decode("ascii")
self.Write_Log_Lines(f"[Random state (base64)]: {state_b64}")
```

### 실측

로컬에서 측정한 크기는 다음과 같다.

| 항목 | 크기 |
|------|------|
| `pickle.dumps(random.getstate())` | 3,763 바이트 |
| base64 인코딩 후 | 5,020 문자 |

주석은 "base64 인코딩으로 압축"이라고 적었지만 base64는 압축이 아니라 1.33배 팽창이다.

`Write_Log_Lines`는 root 전용이므로([DAO_Main.py:9942](5_DAO/SRC/DAO_Main.py#L9942)) root 로그가 trial마다 약 5 KB 커진다. trial 10,000회면 난수 상태만 약 50 MB다. 로그 회전은 줄 수로만 판단하므로([DAO_Main.py:9959](5_DAO/SRC/DAO_Main.py#L9959)의 `if self.log_line_count >= LOG_MAX_LINES`, `LOG_MAX_LINES = 10000`) 이 한 줄이 아무리 길어도 회전이 앞당겨지지 않는다. 한 로그 파일에 trial이 100회 들어간다면 그 파일의 절반가량이 난수 상태 문자열이다.

### 쓸모의 한계

복원은 `Run_Optimization` 맨 앞에서 한 번만 일어난다.

```python
# DAO_Main.py:8014
self.Restore_Random_State_If_Configured()
```

그래서 로그 중간 trial의 상태를 `RANDOM_STATE_TO_SET`에 붙여 넣어도 그 trial이 재현되지 않는다. 복원되는 것은 난수 스트림뿐이고, stage 인덱스, 모드 순서 위치(`current_gen_trial_LLR_mode_index`), 타겟 그룹 위치, `optimal_LLR_matrix`는 처음 상태로 돌아간다. `DEBUG_CONFIG`의 사용법 주석([DAO_Config.py:350](5_DAO/SRC/DAO_Config.py#L350))이 "로그 파일에서 [Random state (base64)]를 복사하여 아래에 설정"이라고만 적어 이 한계가 드러나지 않는다.

### 처방

㉮ `DEBUG_CONFIG`에 `ENABLE_RANDOM_STATE_LOGGING = False`를 추가하고 [DAO_Main.py:2355-2359](5_DAO/SRC/DAO_Main.py#L2355)를 그 아래로 옮긴다. 기본 실행에서 50 MB를 만들 이유가 없다.

㉯ 켜졌을 때는 본 로그 대신 `1_Log/random_states.txt`에 `trial idx, matrix idx, base64`를 한 줄씩 쌓고, 본 로그에는 "random state saved (trial N)"만 남긴다.

㉰ 사용법 주석을 다시 쓴다. 복원이 재현하는 것은 stage 1 trial 1부터의 난수 열이며, 특정 trial을 재현하려면 그 trial까지 같은 경로로 다시 진행해야 한다는 것을 적는다.

---

## M2-13 (MEDIUM, P3) 제외된 코어가 종료 플래그를 바쁜 대기로 폴링한다

### 근거

```python
# DAO_Main.py:7927-7934
# 코어 속도 테스트에서 제외된 코어는 skip
if self.is_current_core_excluded:
    return

# LOAD_UNCOR 모드에서 uncor가 없으면 skip
if self.is_load_uncor_seed_file_mode:
    if not self.has_uncor[ch_idx]:
        return
```

`Run_ECC`가 즉시 돌아오는 rank의 while 루프 한 바퀴는 다음이 전부다.

| 줄 | 하는 일 |
|----|--------|
| [DAO_Main.py:8970](5_DAO/SRC/DAO_Main.py#L8970) | `run_ecc_end_flag.txt` 열기 |
| [DAO_Main.py:8976](5_DAO/SRC/DAO_Main.py#L8976) | `Run_ECC` 즉시 반환 |
| [DAO_Main.py:8979](5_DAO/SRC/DAO_Main.py#L8979) | `Gather_Ref_C_Results(is_test_end=False)`가 non-root에서 즉시 반환([DAO_Main.py:1806](5_DAO/SRC/DAO_Main.py#L1806)) |
| [DAO_Main.py:8980](5_DAO/SRC/DAO_Main.py#L8980) | `Check_Test_End`가 같은 파일을 두 번 더 연다([DAO_Main.py:1062](5_DAO/SRC/DAO_Main.py#L1062), [DAO_Main.py:1069](5_DAO/SRC/DAO_Main.py#L1069)) |
| [DAO_Main.py:8985](5_DAO/SRC/DAO_Main.py#L8985) | `Print_Test_Result`가 non-root에서 즉시 반환 |

대기가 전혀 없다. 한 바퀴에 파일 열기 3회다.

### 재현 조건

`ENABLE_CORE_SPEED_TEST = True`(기본값)에서 제외 코어가 하나라도 생기면, 또는 LOAD_UNCOR 모드에서 어떤 rank에 배분된 uncor가 0이면 발생한다. root의 한 채널 테스트가 30분이면 그 rank는 30분 동안 CPU 하나를 다 쓰면서 공유 파일 시스템에 초당 수만 번의 open을 던진다. 이 부하는 다른 rank의 ECC 실행을 느리게 만들고, 그 결과가 다음 speed test에서 더 많은 코어를 제외시키는 쪽으로 돌아올 수 있다.

### 처방

이 루프 안에는 집단 통신이 없다(AST 전수 확인). 따라서 기여할 수 없는 rank는 루프를 건너뛰어도 동기화가 깨지지 않는다. [DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968) 앞에 조건을 세운다.

```python
can_run_ecc = not self.is_current_core_excluded
if self.is_load_uncor_seed_file_mode and not self.has_uncor[ch_idx]:
    can_run_ecc = False

while can_run_ecc and not self.is_test_end:
    ...
```

루프를 건너뛴 rank도 [DAO_Main.py:8988](5_DAO/SRC/DAO_Main.py#L8988)의 ack 작성과 [DAO_Main.py:8991](5_DAO/SRC/DAO_Main.py#L8991)의 `Gather_Ref_C_Results`(배리어 포함)에는 그대로 들어가므로 rank 사이 통신 횟수가 유지된다. GEN_SINGLE_ROW의 [DAO_Main.py:10096](5_DAO/SRC/DAO_Main.py#L10096) 루프도 같다.

---

## M2-14 (LOW, P16㉰) 복원 범위와 죽은 np.random 시드

### 근거

```python
# DAO_Main.py:8777-8781
state_bytes = base64.b64decode(DEBUG_CONFIG.RANDOM_STATE_TO_SET)
rng_state = pickle.loads(state_bytes)
random.setstate(rng_state)
```

`grep -n "np\.random" 5_DAO/SRC/*.py`의 결과는 [DAO_Main.py:8755](5_DAO/SRC/DAO_Main.py#L8755)의 `np.random.seed(local_init_seed)` 한 줄뿐이다. `np.random`에서 값을 뽑는 곳은 없다. 난수를 쓰는 곳은 모두 표준 `random`이다(`random.choice`, `random.randint`, `random.sample`, `random.uniform` 총 20여 곳).

㉮ 따라서 `random`만 복원해도 **오늘은 충분하다**. 배정 질문의 답은 "지금은 충분하다"이다. 다만 `np.random.seed`는 아무도 읽지 않는 상태를 심는 죽은 줄이고, 누군가 `np.random`으로 값을 뽑기 시작하면 복원이 조용히 반쪽이 된다. 매트릭스 생성 함수 여러 곳이 이미 numpy 배열을 다루므로([DAO_Main.py:747](5_DAO/SRC/DAO_Main.py#L747)의 `np.arange`, [DAO_Main.py:782](5_DAO/SRC/DAO_Main.py#L782)의 `np.array`) 손이 갈 만한 자리다.

㉯ `Restore_Random_State_If_Configured`는 `Run_Optimization` 맨 앞에서 **전 rank**가 부른다([DAO_Main.py:8014](5_DAO/SRC/DAO_Main.py#L8014)). 복원 값은 설정 파일의 상수 하나이므로 복원 뒤 모든 rank의 `random` 스트림이 같아진다. 오늘 worker가 `random`을 쓰는 곳은 메모리 재시도 지연뿐인데([DAO_Main.py:7948](5_DAO/SRC/DAO_Main.py#L7948)), 이 지연은 rank를 시간축에서 흩어 놓으려고 난수로 만든 값이다. 복원 뒤에는 전 rank가 같은 시각에 같은 길이로 쉬므로 메모리 압박이 다시 겹친다.

### 처방

㉮ [DAO_Main.py:8755](5_DAO/SRC/DAO_Main.py#L8755)의 `np.random.seed`를 지우거나, 남긴다면 복원 함수에 `np.random.set_state`를 짝으로 넣고 `Initialize_Trial`이 두 상태를 함께 남기게 한다.

㉯ 재시도 지연을 전용 난수 스트림에서 뽑아 복원의 영향을 받지 않게 한다. `__init__`에서 `self._retry_jitter = random.Random(self.rank)`를 만들고 [DAO_Main.py:7948](5_DAO/SRC/DAO_Main.py#L7948)을 `delay = self._retry_jitter.uniform(0, TIME_CONFIG.MAX_ECC_MEMORY_RETRY_DELAY)`로 바꾼다.

---

## M2-15 (LOW, P3) Debug_Pause의 배리어가 break 앞뒤로 갈린다

### 근거

```python
# DAO_Main.py:1370-1386
while True:
    if self.debug_is_init:
        if self.is_root:
            with open(debug_control_path, "w", encoding="utf-8") as f:
                f.write(f"{default_value}")
            ...
        self.debug_is_init = False
    else:
        with open(debug_control_path, "r", encoding="utf-8") as f:
            flag = f.read().strip()
        if flag != default_value:
            break
    time.sleep(sleep_interval)
    self.MPI_Barrier()
self.MPI_Barrier()
```

`break`가 루프 본문 끝의 `MPI_Barrier`([DAO_Main.py:1385](5_DAO/SRC/DAO_Main.py#L1385))보다 앞에 있고, 그 `break`는 rank마다 따로 읽은 `debug.txt` 값으로 결정된다. 먼저 break한 rank는 1385를 건너뛰고 1386에서 기다린다. MPI 배리어에는 태그가 없으므로 다른 지점의 배리어끼리 짝을 이뤄 통과하고, rank별 `barrier_count`만 어긋난다. 그 뒤 `Check_Barrier_Sync`([DAO_Main.py:2259](5_DAO/SRC/DAO_Main.py#L2259), [DAO_Main.py:2345](5_DAO/SRC/DAO_Main.py#L2345))가 불일치를 잡아 `MPI_Abort` 한다.

파일 읽기에 try/except가 없는 것도 같은 줄에 있다([DAO_Main.py:1380](5_DAO/SRC/DAO_Main.py#L1380)). 사용자가 `debug.txt`를 편집 중이면 PermissionError로 그 rank가 죽는다(M2-6과 같은 형태).

경로가 세션 밖에 있는 것도 이 함수뿐이다.

```python
# DAO_Main.py:1363
debug_control_path = os.path.join(self.work_space_dir, DEBUG_DIR_NAME, DEBUG_FILE_NAME)
```

`8_End_flag` 아래의 플래그는 모두 `session_dir` 밑이라 세션마다 분리되는데, 이 파일만 `work_space_dir` 밑이라 동시에 도는 두 세션이 같은 파일을 본다.

### 현재 상태

`Debug_Pause`는 호출되는 곳이 없고 `DEBUG_CONFIG.ENABLE_FILE_BREAKPOINT`도 False다. 지금 터지지는 않는다.

### 처방

되살릴 때는 ㉮ root만 읽고 `_safe_bcast`한 값으로 break를 결정하고 ㉯ 배리어를 루프 본문 맨 앞 한 곳으로 모아 break 여부와 무관하게 같은 횟수가 되게 하며 ㉰ 경로를 `self.end_flag_dir` 밑으로 옮긴다. 되살릴 계획이 없으면 함수와 `DEBUG_DIR_NAME`, `DEBUG_FILE_NAME`, `debug_is_init`, `debug_cnt`를 함께 지운다.

---

## M2-16 (LOW, P2㉯) 타임아웃 없는 allgather가 죽은 함수에 남아 있다

```python
# DAO_Main.py:7008-7011
if not DEBUG_CONFIG.ENABLE_MPI_DEBUG_LOGGING:
    return

counts: list[int] = self.comm.allgather(self.barrier_count)
```

`MPI_Debug_Logging`은 정의만 있고 호출되는 곳이 없다. 같은 일을 하는 코드가 `Check_Barrier_Sync` 안에 타임아웃을 붙여 들어 있다([DAO_Main.py:6732-6741](5_DAO/SRC/DAO_Main.py#L6732)). 되살리면 워치독 없는 집단 통신이 하나 더 생긴다.

처방: `MPI_Debug_Logging`을 지운다.

---

## M2-17 (LOW, P3) 중단 인덱스를 쓰기만 하고 읽지 않는다

`_Read_Stop_Idx`([DAO_Main.py:1136](5_DAO/SRC/DAO_Main.py#L1136))는 정의만 있고 호출되는 곳이 없다. `_Write_Stop_Idx`는 [DAO_Main.py:10060](5_DAO/SRC/DAO_Main.py#L10060)에서만 불린다. 그래서 GEN_SINGLE_ROW를 중단한 뒤 다시 띄워도 `gen_single_row_stop_idx.txt`를 읽지 않고 처음부터 시작한다. 파일이 남아 있어도 다음 세션 디렉토리가 다르므로 오염은 없다.

처방: 이어붙이기를 지원한다면 `Run_Single_Row_Generation` 시작부에서 root가 `_Read_Stop_Idx()`를 읽어 `_safe_bcast` 한다. 지원하지 않을 것이면 두 함수와 `GEN_SINGLE_ROW_STOP_IDX_FILE_NAME`([DAO_Constants.py:104](5_DAO/SRC/DAO_Constants.py#L104))을 함께 지운다.

---

## M2-18 (LOW, P2㉱) MPI_Abort가 comm.Abort 전에 무거운 진단을 쓴다

```python
# DAO_Main.py:6839-6865
stack_info = []
for frame_info in inspect.stack()[1:]:
    ...
    for key, value in frame_info.frame.f_locals.items():
        ...
        frame_locals[key] = _summarize_value(value)
```

타임아웃으로 abort할 때 전체 호출 스택의 지역 변수를 `_summarize_value`로 요약한다. 프레임에 `LLR_MATRIX`나 큰 리스트가 있으면 이 요약이 길어진다. 그동안 통신 스레드는 여전히 집단 통신 안에 있으므로(M2-3), 두 스레드가 MPI 안에 함께 있는 구간이 그만큼 길어진다. `comm.Abort`는 이 모든 작업이 끝난 [DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894)에서야 불린다.

타임아웃 rank와 그렇지 않은 rank의 종료 순서를 보면, 타임아웃 rank만 abort를 부르고 나머지는 자기 집단 통신 안에서 밖으로부터 끝난다. 따라서 진단 파일은 타임아웃 rank 것만 남고, 상대 rank가 어디에 있었는지는 기록되지 않는다.

처방: ㉮ 스택 수집 깊이를 제한한다(`inspect.stack()[1:6]`). ㉯ `_summarize_value` 호출 개수에 프레임당 상한을 둔다. ㉰ 배리어 타임아웃 메시지에 `barrier_count`가 이미 `comm_name`으로 들어가 있으므로, 남은 rank의 위치 추정을 돕도록 root가 마지막으로 통과한 배리어 번호를 함께 적는다.

---

## 확인했으나 문제 없던 항목

- `Set_Test_Environment`가 `run_ecc_end_flag.txt` 초기화를 두 배리어 사이에 넣어([DAO_Main.py:8460](5_DAO/SRC/DAO_Main.py#L8460), [DAO_Main.py:8468](5_DAO/SRC/DAO_Main.py#L8468), [DAO_Main.py:8478](5_DAO/SRC/DAO_Main.py#L8478)), 이전 채널의 "1"이 남아 worker가 먼저 읽는 경쟁을 막는다. 주석이 그 의도를 적고 있고 코드가 그대로 한다.
- `Initialize_End_Flags`는 세션 디렉토리 생성 배리어와 다음 배리어 사이에서 root만 쓴다([DAO_Main.py:6613-6619](5_DAO/SRC/DAO_Main.py#L6613)). 읽는 쪽이 쓰기 완료를 보장받는 지점이 실제로 사이에 있다.
- 종료 플래그 3종과 ack, 중단 인덱스는 모두 `session_dir/8_End_flag` 밑에 있고 `session_dir`에는 root가 만들어 bcast한 타임스탬프가 들어간다([DAO_Main.py:6584](5_DAO/SRC/DAO_Main.py#L6584), [DAO_Main.py:8708](5_DAO/SRC/DAO_Main.py#L8708)). 세션 사이 플래그 오염은 없다(`Debug_Pause`의 `debug.txt`만 예외이며 M2-15에 적었다).
- 숫자 카운트 파일의 비정상 내용 처리는 안전하다. 숫자가 아니면 경고를 남기고 0을 돌려주며([DAO_Main.py:1110-1113](5_DAO/SRC/DAO_Main.py#L1110)), 빈 문자열과 잘린 값도 `isdigit()` 실패로 0이 된다.
- trial_end_flag 카운트 감소는 root만 하고([DAO_Main.py:8083-8088](5_DAO/SRC/DAO_Main.py#L8083)) 감소 직후 trial 루프를 break 하므로 stage당 1회만 줄어든다. 감소한 값을 다시 bcast하지 않지만 다음 stage에서 root가 다시 읽고 bcast하므로 rank 사이 불일치가 생기지 않는다. 사용자가 감소와 겹치는 순간에 파일을 덮어쓰면 그 값이 날아가지만, 다음 stage에서 다시 읽으므로 한 stage만큼만 어긋난다.
- 메인 최적화 루프의 dao_end, trial_end, stage 시간 초과 판정은 모두 root가 읽고 `_safe_bcast`로 맞춘다([DAO_Main.py:8061-8078](5_DAO/SRC/DAO_Main.py#L8061), [DAO_Main.py:8178-8182](5_DAO/SRC/DAO_Main.py#L8178)). 주석이 그 이유("각 rank가 독립적으로 계산하면 desync 발생 가능")까지 적어 두었다.
- 집단 통신이 rank 분기 안으로 들어간 자리는 없다. `MPI_Barrier`, `_safe_bcast`, `_safe_gather`, `Check_Barrier_Sync`, `Bcast_Trial_LLR_Mode`, `comm.*` 호출을 AST로 훑어 rank 관련 조건문(`is_root`, `rank`, `is_current_core_excluded`, `excluded_cores`, `has_uncor`, `is_test_end`, `pool_has_uncor`) 안에 든 것을 전수 수집한 결과, 걸린 것은 `Gather_Ref_C_Results`의 `is_test_end` 인자 분기뿐이었다. 이 인자는 두 호출처에서 모든 rank가 같은 값을 준다([DAO_Main.py:8979](5_DAO/SRC/DAO_Main.py#L8979)는 False, [DAO_Main.py:8991](5_DAO/SRC/DAO_Main.py#L8991)은 True).
- `comm.Reduce`([DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861))는 바로 앞 배리어([DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840))로 동기화되어 있고, 버퍼 길이 `3 + matrix.max_iteration`의 matrix는 bcast된 것이라 rank 사이에서 같다. 그 사이의 `Read_Ref_C_Result`는 재시도 3회, 회당 100ms와 크기 확인 5회 20ms로 상한이 있다([DAO_Main.py:8207-8216](5_DAO/SRC/DAO_Main.py#L8207)). 워치독은 없지만 노출도가 M2-2와 다르다.
- `Bcast_Trial_LLR_Mode`([DAO_Main.py:818-844](5_DAO/SRC/DAO_Main.py#L818))는 예외를 잡아 스냅샷을 쓰고 abort 한다. `_safe_bcast`와 같은 처리다.
- `Print_Test_Result`([DAO_Main.py:7557](5_DAO/SRC/DAO_Main.py#L7557))는 root 전용이고 MPI 호출이 없어, while 루프 안에서 조건부로 불려도 rank 사이 통신 횟수를 바꾸지 않는다.
- `Ensure_Uncors_Loaded`([DAO_Main.py:7360-7378](5_DAO/SRC/DAO_Main.py#L7360))가 배리어를 포함한 `Load_Uncors_From_Pool`을 부르는 조건은 전 rank가 같은 값으로 갱신하는 `current_loaded_test_mode`([DAO_Main.py:7542](5_DAO/SRC/DAO_Main.py#L7542))와 `is_uncor_pool_ready`([DAO_Main.py:7486](5_DAO/SRC/DAO_Main.py#L7486))다.
- rank별 시드 `base_seed + rank * 10000`은 한 세션 안에서는 rank 수가 얼마든 겹치지 않는다. 간격이 10000 고정이므로 값이 충돌할 수 없다.
- 매트릭스 생성은 전부 root의 `if self.is_root:` 블록 안에서 일어난 뒤 bcast된다([DAO_Main.py:1951](5_DAO/SRC/DAO_Main.py#L1951), [DAO_Main.py:2015-2034](5_DAO/SRC/DAO_Main.py#L2015)). worker가 난수를 쓰는 곳은 `Run_ECC`의 메모리 재시도 지연 한 곳뿐이므로, worker의 난수 사용 때문에 rank 사이 매트릭스 값이 갈리는 일은 없다.
- `MPI_Abort`의 재진입 방지([DAO_Main.py:6807-6812](5_DAO/SRC/DAO_Main.py#L6807))와 `_append_lines_without_rotation`, `Make_Log_Backup`의 `_in_mpi_abort` 확인([DAO_Main.py:811](5_DAO/SRC/DAO_Main.py#L811), [DAO_Main.py:6643](5_DAO/SRC/DAO_Main.py#L6643))이 "abort 중 로그 실패가 다시 abort를 부르는" 재귀를 막는다.
