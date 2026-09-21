# Round 2 팀 M 워커 3 결과 (P5, P13, P14, P15)

- 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
- 작성: 2026-09-21
- 확인 범위:
  - [DAO_Main.py](5_DAO/SRC/DAO_Main.py) 10,428줄 중 다음 구간을 정독
    - 모듈 함수 `_summarize_ndarray`, `_summarize_value`, `_write_error_log` (1~205)
    - 로그 기록과 회전 `_append_lines_without_rotation`(787), `Make_Log_Backup`(6621), `Finalize_Log`(6660), `Write_Log_Separator`(9915), `Write_Log_Lines`(9927)
    - 종료 플래그 `_Write_End_Flag`(1071), `_Read_End_Flag`(1091), `Check_Test_End`(1045), `_Write_Run_ECC_End_Ack`(1198), `_Report_Missing_Acks`(1211)
    - 결과 집계 `Gather_Ref_C_Results`(1784), uncor 분배 `Distribute_Uncors_To_Local_Session`(1531)
    - MPI 계층 `MPI_Barrier`(6685), `Check_Barrier_Sync`(6700), `Write_MPI_Error_Snapshot`(6743), `MPI_Abort`(6800), `_mpi_comm_with_timeout`(6896), `_safe_bcast`(6946), `_safe_gather`(6971)
    - uncor 풀 `Ensure_Uncors_Loaded`(7347), `_Setup_Uncor_Pool_For_Channel`(7386), `Setup_Uncor_Pool`(7460), `Load_Uncors_From_Pool`(7505)
    - 외부 실행 `Run_ECC`(7913), `Read_FER_From_File`(7971), `Run_Optimization`(8003), `Set_Test_Environment`(8449), `Set_Max_Error`(8563), `Test_LLR`(8937)
    - 코어 속도 `Test_Core_Speed`(9020), `Periodic_Recheck`(9100), `_Recheck_Speed_Test`(9127), `_Redistribute_Uncor_Pool_Uniform`(9158)
    - 진입점 `LLR_OPT.Main`(10001), 모듈 `Main`(10401), `__main__`(10419)
  - [DAO_Config.py](5_DAO/SRC/DAO_Config.py) `DAO_CONFIG`(118), `SPEED_TEST_REFC_CONFIG`(218), `TIME_CONFIG`(318)
  - [DAO_Constants.py](5_DAO/SRC/DAO_Constants.py) 전체
  - [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py) `Save_Matrix`(549)
  - 보조 실측: 파이썬으로 예외 계층(`FileNotFoundError`가 `OSError` 하위인지)과 `capture_locals=True` traceback 크기를 직접 재 봄

## 확인에 쓴 설정 기준값

| 이름 | 값 | 출처 |
|------|-----|------|
| `TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS` | 1200초 (2 * 10 * 60) | [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323) |
| `MPI_Barrier` 실제 타임아웃 | 3600초 (`max(1200, 3600)`) | [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692) |
| `TIME_CONFIG.MAX_ECC_MEMORY_RETRY` | 10회 | [DAO_Config.py:321](5_DAO/SRC/DAO_Config.py#L321) |
| `TIME_CONFIG.MAX_ECC_MEMORY_RETRY_DELAY` | 60초 (0에서 60초 사이 균등난수) | [DAO_Config.py:322](5_DAO/SRC/DAO_Config.py#L322) |
| `SIM_MAX_TIME_OUT` | 36000초 (10시간) | [DAO_Constants.py:144](5_DAO/SRC/DAO_Constants.py#L144) |
| `SPEED_TEST_REFC_CONFIG.CORE_SPEED_CUTOFF_RATIO` | 2.0배 | [DAO_Config.py:225](5_DAO/SRC/DAO_Config.py#L225) |
| `SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_STAGES` / `RECHECK_INTERVAL_SECONDS` | 0 / 0 (기본 비활성) | [DAO_Config.py:226](5_DAO/SRC/DAO_Config.py#L226) |
| `LOG_MAX_LINES` | 10000줄 | [DAO_Constants.py:139](5_DAO/SRC/DAO_Constants.py#L139) |
| `DAO_CONFIG.MAX_RUN_ECC_ERRORS` | 9999 | [DAO_Config.py:123](5_DAO/SRC/DAO_Config.py#L123) |

---

## 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|------|----------|------|
| 1 | CRITICAL | P5 ㉮ | 집단 통신 타임아웃(배리어 3600초)이 `Run_ECC`가 허용하는 실행 시간(36000초)의 10분의 1이라, 한 채널 테스트가 한 시간을 넘으면 정상 동작 중에도 전체 작업이 죽는다 | [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692), [DAO_Main.py:1839](5_DAO/SRC/DAO_Main.py#L1839), [DAO_Main.py:7939](5_DAO/SRC/DAO_Main.py#L7939) | LOAD_UNCOR 계열 모드에서 Full 테스트 한 채널이 빠른 코어 기준 약 1시간을 넘고, 속도 제외 문턱(2.0배) 바로 아래인 느린 코어가 하나라도 있을 때 | `MPI_COMM_TIMEOUT_SECONDS`를 `SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY`로 다시 정의하고 `MPI_Barrier`의 3600초 하한을 없앤다 |
| 2 | HIGH | P14 ㉯ | `_write_error_log`가 `capture_locals=True`로 traceback을 만들면서 지역 변수 크기를 제한하지 않는다. 큰 파이썬 리스트를 쥔 프레임에서 예외가 나면 에러 로그가 수백 MB로 부푼다 | [DAO_Main.py:188](5_DAO/SRC/DAO_Main.py#L188) | uncor 원본 전체를 `all_lines`로 읽는 [DAO_Main.py:7410](5_DAO/SRC/DAO_Main.py#L7410), [DAO_Main.py:1555](5_DAO/SRC/DAO_Main.py#L1555) 안에서 예외 발생 | `capture_locals=False`로 바꾸고, 변수 요약은 이미 상한이 있는 `_collect_error_state_snapshot`에 맡긴다 |
| 3 | HIGH | P13 ㉰ | `_Redistribute_Uncor_Pool_Uniform`이 Partial 소스를 못 찾으면 모든 rank의 `has_uncor`가 False가 되고, `current_loaded_test_mode`는 PARTIAL로 표시되어 다음 테스트가 재로드 없이 빈 상태로 진행되며 `total_tests=0`으로 전체 중단 | [DAO_Main.py:9182](5_DAO/SRC/DAO_Main.py#L9182), [DAO_Main.py:7521](5_DAO/SRC/DAO_Main.py#L7521), [DAO_Main.py:1883](5_DAO/SRC/DAO_Main.py#L1883) | `ENABLE_TWO_STAGE_TEST=True`, 주기적 재점검 활성, `5_Uncors/tmp_partial_uncors/` 하위 디렉토리가 없는 상태에서 `excluded_cores` 변경 | `partial_src_dir`이 None이면 `initial_test_mode`를 FULL로 내리고 `current_loaded_test_mode = None`으로 두어 다음 `Ensure_Uncors_Loaded`가 반드시 재로드하게 한다 |
| 4 | MEDIUM | P5 ㉯㉰ | ECC 실패 원인이 로그에 남지 않는다. `subprocess.run`이 stdout과 stderr를 받지 않고, 재시도 로그는 root 전용 `Write_Log_Lines`라 워커 rank에서 사라진다 | [DAO_Main.py:7939](5_DAO/SRC/DAO_Main.py#L7939), [DAO_Main.py:7949](5_DAO/SRC/DAO_Main.py#L7949), [DAO_Main.py:9942](5_DAO/SRC/DAO_Main.py#L9942) | rank 0이 아닌 코어에서 ECC가 실패하거나 메모리 재시도에 들어갈 때 | `Run_ECC`에 `capture_output=True, text=True`를 주고, 실패와 재시도 메시지를 rank별 파일에 쓰는 `Write_Rank_Log_Lines`를 새로 만들어 쓴다 |
| 5 | MEDIUM | P5 ㉮㉴ | errno 12 재시도가 셸 기동 실패만 덮는다. `cmd`나 `bash`는 떴는데 ECC 실행 파일이 메모리 부족으로 죽으면 `CalledProcessError`가 되어 재시도 없이 즉시 중단 | [DAO_Main.py:7938](5_DAO/SRC/DAO_Main.py#L7938), [DAO_Main.py:7953](5_DAO/SRC/DAO_Main.py#L7953) | 노드 메모리가 모자란 상태에서 ECC 실행 파일 자체가 비정상 종료 코드로 끝날 때 (Windows와 Linux 모두) | `CalledProcessError`를 곧바로 중단으로 보내지 말고, 종료 코드와 stderr를 메모리 부족 신호와 대조해 같은 재시도 경로로 보낸다 |
| 6 | MEDIUM | P13 ㉮ | 코어 속도 측정이 `Run_ECC` 벽시계 시간을 재므로 errno 12 재시도 대기(최대 600초)가 측정값에 섞인다. 일시적 메모리 부족이 멀쩡한 코어를 영구 제외시킨다 | [DAO_Main.py:9044](5_DAO/SRC/DAO_Main.py#L9044), [DAO_Main.py:7950](5_DAO/SRC/DAO_Main.py#L7950) | 속도 테스트 중 한 rank가 메모리 부족으로 재시도에 들어가고, 재점검 주기가 기본값 0(비활성)이라 복구 기회가 없을 때 | `Run_ECC`가 재시도 대기 누적 시간을 인스턴스 변수에 쌓고, `Test_Core_Speed`가 `elapsed_time`에서 그만큼 뺀 값을 `allgather`에 넣는다 |
| 7 | MEDIUM | P13 ㉮ | 제외된 코어가 테스트 while 루프에서 대기 없이 회전한다. `Run_ECC`가 즉시 반환하고 루프 안에 sleep도 집단 통신도 없어 종료 플래그 파일을 초당 수만 번 연다 | [DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968), [DAO_Main.py:7927](5_DAO/SRC/DAO_Main.py#L7927), [DAO_Main.py:1091](5_DAO/SRC/DAO_Main.py#L1091) | `current_seed_mode`가 DEFAULT나 SAVE_UNCOR_SEED이고 제외 코어가 하나 이상일 때 | 제외 코어와 `has_uncor=False`인 코어는 루프 안에서 `time.sleep(1.0)`을 넣고, `_Read_End_Flag`의 `except FileNotFoundError`를 `except OSError`로 넓힌다 |
| 8 | MEDIUM | P14 ㉯ | 통신 감시 스레드 구조에서 메인 스레드가 `comm.Abort`를 부르는 동안 작업 스레드는 아직 MPI 호출 안에 있다. MPI가 MPI_THREAD_MULTIPLE로 초기화되지 않았으면 이 중단 자체가 매달릴 수 있다 | [DAO_Main.py:6932](5_DAO/SRC/DAO_Main.py#L6932), [DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894) | `_mpi_comm_with_timeout`이 타임아웃을 감지한 모든 경우 | 기동 시 `MPI.Query_thread()`를 확인해 로그로 알리고, 타임아웃 경로에서는 `comm.Abort` 대신 `os._exit(error_code)`로 프로세스를 끊는다 |
| 9 | MEDIUM | P14 ㉰ | `MPI_Abort`가 `NoReturn`으로 선언되었으나 재진입 분기에서 실제로 반환한다. 호출부가 그 뒤 코드를 이어 실행하면 미정의 이름이나 None을 쓴다 | [DAO_Main.py:6807](5_DAO/SRC/DAO_Main.py#L6807), [DAO_Main.py:7988](5_DAO/SRC/DAO_Main.py#L7988), [DAO_Main.py:6966](5_DAO/SRC/DAO_Main.py#L6966) | `comm.Abort`가 즉시 프로세스를 끊지 못하는 MPI 구현에서 `MPI_Abort` 재진입이 일어날 때 | `MPI_Abort` 본문 마지막을 `os._exit(error_code)`로 닫아 반환 자체를 없애고 재진입 분기의 `return`을 지운다 |
| 10 | MEDIUM | P14 ㉱ | 최상위 `Main`이 `Log_Unhandled_Exception`과 `MPI_Abort`로 같은 내용을 두 번 쌓는다. 두 번째 기록의 호출 스택은 예외 발생 지점이 아니라 처리부라서 쓸모가 없다 | [DAO_Main.py:10407](5_DAO/SRC/DAO_Main.py#L10407), [DAO_Main.py:6841](5_DAO/SRC/DAO_Main.py#L6841), [DAO_Main.py:676](5_DAO/SRC/DAO_Main.py#L676) | 처리되지 않은 예외가 `LLR_OPT.Main` 밖으로 나올 때마다 | `MPI_Abort`에 `capture_stack: bool = True` 인자를 두고 최상위 `Main`에서는 `capture_stack=False`로 부른다 |
| 11 | MEDIUM | P14 ㉳ | 매트릭스와 플래그 파일을 제자리에 직접 쓴다. 중단 시점이 쓰기 도중이면 잘린 최적 매트릭스 파일이나 빈 플래그 파일이 남는다 | [DAO_LLR_MATRIX.py:549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549), [DAO_Main.py:1071](5_DAO/SRC/DAO_Main.py#L1071) | 다른 rank의 `comm.Abort`가 root의 `Save_Matrix` 도중에 도달할 때 | `.tmp` 파일에 쓴 뒤 `os.replace`로 바꾸는 방식으로 고친다 |
| 12 | MEDIUM | P15 ㉰ | 백업 로그 이름이 (초 단위 생성 시각, 시작 idx, 종료 idx)만으로 정해져 같은 이름이 날 수 있다. POSIX는 이전 백업을 말없이 덮어쓰고 Windows는 `FileExistsError`로 전체 작업을 중단시킨다 | [DAO_Main.py:6638](5_DAO/SRC/DAO_Main.py#L6638), [DAO_Main.py:2182](5_DAO/SRC/DAO_Main.py#L2182) | 매트릭스 idx가 그대로인 채 1초 안에 회전이 두 번 일어날 때 (로그 폭주 구간) | 대상 경로가 이미 있으면 `_2`, `_3` 접미사로 빈 이름을 찾은 뒤 `os.rename` 대신 `os.replace`를 쓴다 |
| 13 | MEDIUM | P15 ㉯ | 중단 처리 중 로그 회전이 실패하면 `Make_Log_Backup`이 `Write_Log_Lines` 안쪽에서 `comm.Abort(1)`을 부른다. 그래서 `MPI_Abort`가 호출 스택 기록 구간에 도달하지 못하고 원인 진단이 사라진다 | [DAO_Main.py:6643](5_DAO/SRC/DAO_Main.py#L6643), [DAO_Main.py:6819](5_DAO/SRC/DAO_Main.py#L6819) | `log_line_count >= 10000`인 상태에서 `MPI_Abort`가 불리고 `os.rename`이 실패할 때 (로그 디렉토리 권한 문제, 디스크 가득 참) | `MPI_Abort`에서 상세 로그 기록을 `Write_Log_Lines` 호출보다 앞으로 옮기고, `_in_mpi_abort`가 True이면 회전 검사를 건너뛴다 |
| 14 | MEDIUM | P15 ㉱ | 비루트 rank의 경고가 전부 버려진다. `Write_Log_Lines`가 첫 줄에서 반환하므로 uncor 복사 실패, 파일 삭제 실패, ECC 메모리 재시도가 어디에도 남지 않는다 | [DAO_Main.py:9942](5_DAO/SRC/DAO_Main.py#L9942), [DAO_Main.py:959](5_DAO/SRC/DAO_Main.py#L959), [DAO_Main.py:1529](5_DAO/SRC/DAO_Main.py#L1529) | rank 0 외의 코어에서 비치명 오류가 날 때마다 | rank별 경고 파일에 기록하는 `Write_Rank_Warning`을 만들고 워커 경로의 호출을 그쪽으로 옮긴다 |
| 15 | MEDIUM | P5 ㉲ | ECC 실행 뒤 고정 `time.sleep(0.5)`가 결과 파일 가시성을 보장하지 못한다. 파일이 없으면 그 rank의 기여분이 0으로 조용히 빠지고 로그도 남지 않는다 | [DAO_Main.py:7942](5_DAO/SRC/DAO_Main.py#L7942), [DAO_Main.py:1852](5_DAO/SRC/DAO_Main.py#L1852) | 느린 저장소나 네트워크 공유에 `local_session_dir`이 있을 때 | 고정 대기를 결과 파일이 나타날 때까지 확인하는 대기로 바꾸고, 제외되지 않은 rank의 결과 파일이 없으면 경고를 남긴다 |
| 16 | MEDIUM | P5 ㉱ | `MAX_RUN_ECC_ERRORS`는 이름과 주석이 "RUN_ECC 오류 수"라고 말하지만 실제로는 FER 측정을 끝내는 누적 프레임 오류 목표값이다 | [DAO_Config.py:123](5_DAO/SRC/DAO_Config.py#L123), [DAO_Main.py:8566](5_DAO/SRC/DAO_Main.py#L8566), [DAO_Main.py:1067](5_DAO/SRC/DAO_Main.py#L1067) | 설정을 읽는 사람이 재시도 한도로 오해하고 값을 낮추면 FER 정밀도가 조용히 떨어진다 | 이름을 `TARGET_NUM_FRAME_ERRORS`로 바꾸고 주석을 "테스트를 끝낼 누적 프레임 오류 수"로 다시 쓴다 |
| 17 | MEDIUM | P14 ㉲, P13 | `comm.Reduce`와 두 곳의 `comm.allgather`가 타임아웃 감시를 거치지 않는다. 한 rank가 MPI 밖에서 죽으면 나머지는 영원히 매달린다 | [DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861), [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049), [DAO_Main.py:7011](5_DAO/SRC/DAO_Main.py#L7011) | 결과 집계 직전이나 코어 속도 측정 직후에 한 rank가 운영체제에 의해 강제 종료될 때 | 세 호출을 `self._mpi_comm_with_timeout`으로 감싼다 |
| 18 | LOW | P13 ㉯㉲ | `active_cores`가 빌 수 없다. root 보호 때문에 `if not active_cores` 세 곳은 도달하지 않고, 정작 위험한 "root 혼자 활성" 상태에는 경고가 없다 | [DAO_Main.py:9063](5_DAO/SRC/DAO_Main.py#L9063), [DAO_Main.py:647](5_DAO/SRC/DAO_Main.py#L647), [DAO_Main.py:1563](5_DAO/SRC/DAO_Main.py#L1563), [DAO_Main.py:7417](5_DAO/SRC/DAO_Main.py#L7417) | 두 코어 이상이 속도 문턱을 넘어 rank 0만 남는 경우 | bcast 직후 `len(self.active_cores) == 1`이면 경고를 남기고, 도달하지 않는 분기는 지운다 |
| 19 | LOW | P13 ㉮ | `Test_Core_Speed`가 `current_seed_mode`를 DEFAULT로 덮어쓰고 복원하지 않는다. 지금은 다음 `Test_LLR`이 다시 정하기 때문에만 안전하다 | [DAO_Main.py:9038](5_DAO/SRC/DAO_Main.py#L9038), [DAO_Main.py:8952](5_DAO/SRC/DAO_Main.py#L8952) | 주기적 재점검이 활성인 상태에서 trial 중간에 속도 테스트가 끼어들 때 | 시작에서 이전 값을 담고 끝에서 되돌린다 |
| 20 | LOW | P5 | `Run_ECC`에 죽은 코드가 둘 있다. `ecc_start`는 어디에도 쓰이지 않고, `except (..., FileNotFoundError)`의 `FileNotFoundError`는 `OSError` 하위라 위쪽 처리기에서 이미 걸린다 | [DAO_Main.py:7935](5_DAO/SRC/DAO_Main.py#L7935), [DAO_Main.py:7953](5_DAO/SRC/DAO_Main.py#L7953) | 항상 | `ecc_start` 줄을 지우고, 실행 파일 없음을 구분하려면 `except OSError` 안에서 `errno.ENOENT`를 먼저 분기한다 |
| 21 | LOW | P15 ㉮ | `log_line_count`가 전달된 리스트 원소 수만 센다. 줄바꿈을 품은 한 문자열이 파일에는 여러 줄로 들어가므로 실제 파일은 10000줄을 넘긴 뒤에 회전한다 | [DAO_Main.py:807](5_DAO/SRC/DAO_Main.py#L807), [DAO_Main.py:9925](5_DAO/SRC/DAO_Main.py#L9925) | `Write_Log_Separator`처럼 앞뒤에 빈 줄을 넣는 호출이 많을 때 | `sum(line.count("\n") + 1 for line in lines)`로 센다 |

---

## 발견 상세

### 1 (CRITICAL, P5 ㉮) 배리어 타임아웃 3600초가 ECC 허용 시간 36000초와 어긋난다

재시도 루프가 rank마다 쓰는 시간을 먼저 계산한다.

```python
# DAO_Main.py:7936-7955
for attempt in range(1, TIME_CONFIG.MAX_ECC_MEMORY_RETRY + 1):
    try:
        ... subprocess.run(..., check=True, timeout=SIM_MAX_TIME_OUT)
        time.sleep(0.5)
        return
    except OSError as error:
        if error.errno == 12:
            delay = random.uniform(0, TIME_CONFIG.MAX_ECC_MEMORY_RETRY_DELAY)
            ...
            time.sleep(delay)
```

메모리 부족은 프로세스 생성 단계에서 곧바로 실패하므로 한 번의 시도는 거의 즉시 끝나고 대기만 남는다. 10회에 최대 60초씩이므로 **대기 총합은 최대 600초, 평균 300초**다. 여기까지는 `MPI_COMM_TIMEOUT_SECONDS = 2 * (10 * 60) = 1200초`라는 산식([DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323))과 맞는다.

문제는 그 산식이 **ECC 실행 자체의 시간을 하나도 세지 않는다**는 점이다. 한 번의 `subprocess.run`은 `SIM_MAX_TIME_OUT = 36000초`까지 허용된다. 설계상 ECC 한 번이 10시간까지 돌 수 있다고 선언해 놓고, 그 결과를 모으는 배리어는 3600초만 기다린다.

`Test_LLR`의 while 루프 안에는 집단 통신이 하나도 없다([DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968)). rank들이 다시 만나는 첫 지점은 `Gather_Ref_C_Results(is_test_end=True)`의 배리어다.

```python
# DAO_Main.py:1838-1839
# === 테스트 종료: 각 rank가 자기 파일 읽고 MPI Reduce로 합산 ===
self.MPI_Barrier()
```

`MPI_Barrier`의 타임아웃은 `max(TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS, 3600)`이므로 3600초다([DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692)). 따라서 **가장 빠른 rank와 가장 느린 rank의 한 채널 소요 시간 차이가 3600초를 넘으면** 빠른 rank가 `MPI_Abort`를 부르고 작업 전체가 죽는다.

이 차이가 얼마나 벌어질 수 있는지는 코어 제외 문턱이 정한다. `CORE_SPEED_CUTOFF_RATIO = 2.0`이고 판정이 `current_time > mean_time * 2.0`이므로([DAO_Main.py:9058](5_DAO/SRC/DAO_Main.py#L9058)) **평균의 1.99배까지 느린 코어는 활성으로 남는다**. LOAD_UNCOR 계열 모드는 while 루프가 채널당 한 번만 돌기 때문에(`Check_Test_End`가 첫 호출에서 종료를 확정, [DAO_Main.py:1057](5_DAO/SRC/DAO_Main.py#L1057)) 한 채널의 소요 시간 차이가 곧 배리어 대기 시간이 된다. 빠른 코어가 한 채널에 1시간을 쓰면 1.99배 코어는 약 2시간을 쓰고 차이는 약 1시간이라 3600초 문턱에 걸린다.

재현 조건: `UNCOR_CONFIG.LOAD_UNCOR_MODE`가 `LOAD_SEED`, `ENABLE_CORE_SPEED_TEST=True`, 코어 속도 편차가 1.5배에서 2.0배 사이, Full 테스트 한 채널이 빠른 코어 기준 1시간 이상. 어느 rank가 먼저 배리어에 도착하든 결과는 같다.

처방:
- 1. [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323)의 `MPI_COMM_TIMEOUT_SECONDS`를 `SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY`로 다시 정의한다 (현재 값으로는 36600초). 주석도 "ECC 한 번의 최대 실행 시간에 메모리 재시도 대기를 더한 값"으로 고친다.
- 2. [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692)의 `max(TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS, 3600)`을 `TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS`로 바꾼다. 1에서 값을 올리면 하한은 필요 없다.
- 3. 느린 코어를 빨리 잘라내고 싶다면 `CORE_SPEED_CUTOFF_RATIO`를 1.3 근처로 낮추는 쪽으로 다루고, 타임아웃으로 처리하지 않는다.

### 2 (HIGH, P14 ㉯) `capture_locals=True` traceback에 크기 상한이 없다

```python
# DAO_Main.py:188-190
traceback_lines = "".join(
    traceback.TracebackException.from_exception(exc, capture_locals=True).format()
)
```

`capture_locals=True`는 traceback의 모든 프레임에 있는 모든 지역 변수에 `repr()`을 적용한다. numpy 배열은 numpy 자체 출력 상한 덕에 짧게 끝나지만 **파이썬 리스트는 잘리지 않는다**. 실측으로 확인했다.

```
원소 30만 개짜리 list 지역 변수 하나 -> traceback 문자열 2,289,482 바이트
```

DAO에는 파일 전체를 리스트로 쥐는 프레임이 여럿 있다.

```python
# DAO_Main.py:7409-7410 (_Setup_Uncor_Pool_For_Channel)
with src_path.open("r", encoding="utf-8") as f:
    all_lines = [line.rstrip("\n") for line in f if line.strip()]
```

```python
# DAO_Main.py:1554-1555 (Distribute_Uncors_To_Local_Session)
with src_path.open("r", encoding="utf-8") as f:
    all_lines = [line.rstrip("\n") for line in f if line.strip()]
```

uncor 원본이 수십만 줄이면 `error_logs_{rank}.txt` 한 번 기록에 수백 MB 문자열이 메모리에 만들어지고 그대로 파일에 쓰인다. 메모리 부족으로 죽은 상황에서 예외를 기록하려다 다시 메모리를 삼키는 모양이 된다.

대조적으로 같은 파일의 `_summarize_value`는 `MAX_COLLECTION_PREVIEW = 20`, `MAX_SUMMARY_DEPTH = 4`로 이미 상한을 걸어 두었다([DAO_Main.py:52](5_DAO/SRC/DAO_Main.py#L52)). 상한이 있는 경로와 없는 경로가 같은 로그 파일에 함께 쓰이고 있다.

처방: [DAO_Main.py:189](5_DAO/SRC/DAO_Main.py#L189)를 `capture_locals=False`로 바꾼다. 지역 변수는 이미 `state_text`(`_collect_error_state_snapshot`)가 상한을 지켜 가며 담고 있으므로 정보 손실이 없다.

### 3 (HIGH, P13 ㉰) 재분배가 Partial 소스를 못 찾으면 다음 테스트가 빈 uncor로 진행된다

```python
# DAO_Main.py:9166-9172
self.pool_has_uncor = {
    TestMode.PARTIAL: [False] * REFC_CONFIG.NUM_TARGET_CHANNELS,
    TestMode.FULL: [False] * REFC_CONFIG.NUM_TARGET_CHANNELS,
}
self.is_uncor_pool_ready = False
self.current_loaded_test_mode = None
```

```python
# DAO_Main.py:9192-9214
partial_src_dir = self._safe_bcast(...)
if partial_src_dir:
    ...
else:
    self.Write_Log_Lines("[Periodic_Recheck] tmp_partial_uncors 없음, Partial pool 스킵")

# 항상 Load 수행
initial_test_mode = TestMode.PARTIAL if UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST else TestMode.FULL
self.Load_Uncors_From_Pool(initial_test_mode)
```

`partial_src_dir`이 None이면 `pool_has_uncor[PARTIAL]`은 재설정된 그대로 전부 False다. 이어서 `Load_Uncors_From_Pool(TestMode.PARTIAL)`이 돌면 모든 채널에서 다음 분기를 타며 `has_uncor`가 모두 False가 된다.

```python
# DAO_Main.py:7521-7523
if not self.pool_has_uncor[test_mode][ch_idx]:
    self.has_uncor[ch_idx] = False
    continue
```

그리고 같은 함수 끝에서 `self.current_loaded_test_mode = test_mode`가 PARTIAL로 설정된다([DAO_Main.py:7542](5_DAO/SRC/DAO_Main.py#L7542)). 다음 trial의 `_Run_Test_Stage(TestMode.PARTIAL, ...)`는 `Ensure_Uncors_Loaded`에서 "이미 올바른 uncor가 로드되어 있음"으로 판단해 그대로 반환한다([DAO_Main.py:7368](5_DAO/SRC/DAO_Main.py#L7368)).

그 결과 모든 rank가 `Run_ECC`의 두 번째 조기 반환을 타고([DAO_Main.py:7932](5_DAO/SRC/DAO_Main.py#L7932)) 결과 파일을 하나도 만들지 않으며, 집계에서 다음 중단을 만난다.

```python
# DAO_Main.py:1883-1884
if total_tests == 0:
    self.MPI_Abort(f"Gather_Ref_C_Results: total_tests=0 for ch_idx={ch_idx}. All cores failed to produce results.")
```

재현 조건: `UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST=True`, `SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_STAGES > 0` 또는 `RECHECK_INTERVAL_SECONDS > 0`, 그리고 `5_Uncors/tmp_partial_uncors/` 아래에 디렉토리가 없는 시점(초기 Partial 풀 구성이 아직 끝나지 않았거나 이전 실행에서 세션 uncor 디렉토리를 정리한 경우)에 `excluded_cores`가 바뀜.

처방: [DAO_Main.py:9206](5_DAO/SRC/DAO_Main.py#L9206) 이후 구간을 다음처럼 고친다.
- 1. `else` 분기에서 `initial_test_mode`를 `TestMode.FULL`로 정한다.
- 2. `Load_Uncors_From_Pool` 호출 뒤 `self.current_loaded_test_mode = None`으로 두어 다음 `Ensure_Uncors_Loaded`가 반드시 다시 로드하게 한다. `Rebuild_Partial_Pool`이 이미 같은 방식을 쓴다([DAO_Main.py:9445](5_DAO/SRC/DAO_Main.py#L9445)).

### 4 (MEDIUM, P5 ㉯㉰) ECC 실패 원인이 로그 어디에도 남지 않는다

```python
# DAO_Main.py:7938-7941
subprocess.run(["cmd", "/c", os.path.basename(self.batch_path)], cwd=..., check=True, timeout=SIM_MAX_TIME_OUT)
```

`capture_output`이 없으므로 ECC가 무엇을 말하고 죽었는지는 mpirun 콘솔로만 흘러가고 세션 로그에는 남지 않는다. 같은 파일의 `Build_ECC`는 `capture_output=True`를 쓰고 실패 시 stdout과 stderr를 로그에 옮겨 적는다([DAO_Main.py:903](5_DAO/SRC/DAO_Main.py#L903)). 같은 저장소 안에서 처리 방식이 갈린다.

`check=True`로 잡힌 실패는 `MPI_Abort(f"ECC execution failed: {error}")`로 가는데, `CalledProcessError`의 문자열에는 명령줄과 반환 코드만 들어 있어 원인 판별이 되지 않는다.

메모리 재시도 로그도 사라진다.

```python
# DAO_Main.py:7949
self.Write_Log_Lines(f"[Run_ECC] 메모리 할당 실패 (시도 {attempt}/...), {delay:.1f}초 후 재시도...")
```

```python
# DAO_Main.py:9941-9943
if not self.is_root or self.log_file_path is None:
    return
```

rank 0이 아닌 코어에서는 이 줄이 통째로 버려진다. 발견 1의 배리어 타임아웃이 터졌을 때 운영자가 보는 것은 "MPI_Barrier[N] timed out"뿐이고 실제 원인(워커의 메모리 재시도)은 흔적이 없다.

처방:
- 1. [DAO_Main.py:7939](5_DAO/SRC/DAO_Main.py#L7939)와 [DAO_Main.py:7941](5_DAO/SRC/DAO_Main.py#L7941)에 `capture_output=True, text=True`를 더하고, `CalledProcessError` 처리에서 `error.stdout`과 `error.stderr`를 중단 메시지에 담는다.
- 2. rank별 진단 파일에 쓰는 `Write_Rank_Log_Lines(self, lines)`를 만든다. `_write_error_log`가 쓰는 `6_Error_Log/error_logs_{rank}.txt` 경로 규칙을 그대로 쓰면 된다. [DAO_Main.py:7949](5_DAO/SRC/DAO_Main.py#L7949)의 호출을 이쪽으로 바꾼다.

### 5 (MEDIUM, P5 ㉮㉴) 메모리 재시도가 셸 기동 실패만 덮는다

errno 12(`ENOMEM`)는 Windows와 Linux 모두에서 나올 수 있다. Linux에서는 `fork` 실패가 그대로 `OSError(errno=12)`가 되고, Windows에서는 `CreateProcess`가 `ERROR_NOT_ENOUGH_MEMORY`를 돌려줄 때 CPython이 errno 12로 대응시킨다. 그러므로 ㉴의 우려("두 운영체제가 같은 errno를 주는가")는 성립한다.

진짜 빈틈은 다른 데 있다. 실행 대상이 ECC 실행 파일이 아니라 **셸**이다.

```python
subprocess.run(["cmd", "/c", os.path.basename(self.batch_path)], ...)   # Windows
subprocess.run(["bash", os.path.basename(self.batch_path)], ...)        # Linux
```

`cmd`나 `bash`는 작으므로 거의 항상 뜬다. 정작 메모리를 크게 쓰는 ECC 실행 파일이 메모리 부족으로 죽으면 셸은 정상적으로 비정상 종료 코드를 돌려주고, 파이썬 쪽에서는 `OSError`가 아니라 `CalledProcessError`가 된다. 그러면 재시도 없이 다음 줄로 간다.

```python
# DAO_Main.py:7953-7954
except (subprocess.CalledProcessError, FileNotFoundError) as error:
    self.MPI_Abort(f"ECC execution failed: {error}")
```

즉 **`MAX_ECC_MEMORY_RETRY = 10`은 실제로 가장 잦은 메모리 부족 상황을 막아 주지 못한다**.

처방: 발견 4의 1번(stderr 수집)을 먼저 적용한 뒤, `CalledProcessError` 처리에서 종료 코드와 stderr를 메모리 부족 신호(Linux의 `Killed`나 `std::bad_alloc`, Windows의 `0xC0000017`)와 대조해 일치하면 errno 12와 같은 재시도 경로로 보낸다. 일치하지 않으면 지금처럼 즉시 중단한다.

### 6 (MEDIUM, P13 ㉮) 속도 측정값에 메모리 재시도 대기가 섞인다

```python
# DAO_Main.py:9043-9049
start_time = time.time()
self.Run_ECC(ch_idx=0)
elapsed_time = time.time() - start_time

all_elapsed_times = self.comm.allgather(elapsed_time)
```

`Run_ECC`가 errno 12 재시도에 들어가면 이 `elapsed_time`에 최대 600초의 `time.sleep(delay)`가 그대로 포함된다. 속도 테스트 자체는 `fn=1, max_num_test=1`로 짧게 설계되어 있으므로([DAO_Config.py:229](5_DAO/SRC/DAO_Config.py#L229)) 정상 측정값은 초 단위일 것이다. 여기에 수백 초가 얹히면 `current_time > mean_time * 2.0` 판정은 거의 확실히 참이 되어 그 코어는 제외된다.

제외가 고정되는 이유는 재점검이 기본으로 꺼져 있기 때문이다. `RECHECK_INTERVAL_STAGES = 0`, `RECHECK_INTERVAL_SECONDS = 0`이므로 `Periodic_Recheck`은 첫 줄에서 반환하고([DAO_Main.py:9107](5_DAO/SRC/DAO_Main.py#L9107)), trial 내부 주기 점검도 조건에서 걸러진다([DAO_Main.py:8126](5_DAO/SRC/DAO_Main.py#L8126)). **일시적 메모리 부족 한 번이 그 세션 내내 코어 하나를 놀린다**.

처방:
- 1. `Run_ECC`에 `self._last_run_ecc_retry_seconds`를 두고 재시도 대기 시간을 누적한다(함수 시작에서 0으로 초기화).
- 2. [DAO_Main.py:9046](5_DAO/SRC/DAO_Main.py#L9046)을 `elapsed_time = (time.time() - start_time) - self._last_run_ecc_retry_seconds`로 바꾼다.
- 3. 재시도가 있었던 rank는 그 사실을 `allgather` 값과 함께 보내 root 로그에 남긴다.

### 7 (MEDIUM, P13 ㉮) 제외된 코어가 대기 없이 종료 플래그 파일을 반복해서 연다

```python
# DAO_Main.py:8968-8985
while not self.is_test_end:
    self.Read_Run_ECC_End_Flag()
    if self.is_test_end:
        self._Write_Run_ECC_End_Ack()
        break
    loop_count += 1
    self.Set_Loop_Start_Time()
    self.Run_ECC(ch_idx=ch_idx)
    if not is_load_seed_mode:
        self.Gather_Ref_C_Results(matrix=matrix, ch_idx=ch_idx, is_test_end=False)
    self.Check_Test_End(ch_idx=ch_idx)
    if self.current_seed_mode in [SeedMode.DEFAULT, SeedMode.SAVE_UNCOR_SEED]:
        self.Print_Test_Result(...)
```

제외된 코어에서 이 루프의 본문은 사실상 비어 있다.

- `Run_ECC`는 첫 줄에서 반환한다([DAO_Main.py:7927](5_DAO/SRC/DAO_Main.py#L7927))
- `Gather_Ref_C_Results(is_test_end=False)`는 비루트에서 곧바로 반환한다([DAO_Main.py:1806](5_DAO/SRC/DAO_Main.py#L1806))
- `Print_Test_Result`도 비루트에서 곧바로 반환한다([DAO_Main.py:7557](5_DAO/SRC/DAO_Main.py#L7557))
- `Check_Test_End`는 비루트에서 `Read_Run_ECC_End_Flag` 한 번으로 끝난다([DAO_Main.py:1055](5_DAO/SRC/DAO_Main.py#L1055))

남는 것은 **반복당 종료 플래그 파일 열기 두 번**뿐이고 대기가 없다. root가 누적 오류 목표에 도달해 플래그를 쓸 때까지 이 회전이 계속된다. 제외 코어는 일을 시키지 않으려고 뺀 코어인데 실제로는 CPU 하나를 완전히 소모하며 공유 디렉토리의 같은 파일을 초당 수만 번 연다.

이 상황은 `current_seed_mode`가 DEFAULT나 SAVE_UNCOR_SEED일 때만 생긴다. LOAD 계열 모드에서는 `Check_Test_End`가 첫 호출에 종료를 확정해 루프가 한 번만 돈다.

곁들여, 이 파일 읽기의 예외 처리가 좁다.

```python
# DAO_Main.py:1091-1097
def _Read_End_Flag(self, file_path: str) -> bool:
    try:
        with open(file_path, "r") as f:
            return f.read().strip() == "1"
    except FileNotFoundError:
        return False
```

root는 같은 파일을 `open(file_path, "w")`로 덮어쓴다([DAO_Main.py:1076](5_DAO/SRC/DAO_Main.py#L1076)). 잘림 구간에 읽으면 빈 문자열이 되어 False가 되니 그 자체는 안전하다. 다만 바이러스 검사나 인덱서가 파일을 잠깐 잡으면 `PermissionError`가 나고, 이것은 `FileNotFoundError`가 아니므로 처리되지 않은 예외가 되어 전체 중단으로 이어진다. 회전 횟수가 많을수록 이 확률이 커진다.

처방:
- 1. [DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968) 루프 안, `Run_ECC` 호출 바로 뒤에 `if self.is_current_core_excluded or not self.has_uncor[ch_idx]: time.sleep(1.0)`을 넣는다.
- 2. [DAO_Main.py:1096](5_DAO/SRC/DAO_Main.py#L1096)의 `except FileNotFoundError`를 `except OSError`로 넓힌다.

### 8 (MEDIUM, P14 ㉯) 통신 감시 스레드가 살아 있는 동안 `comm.Abort`를 부른다

```python
# DAO_Main.py:6931-6941
thread = threading.Thread(target=comm_thread, daemon=True)
thread.start()

if not completed.wait(timeout=timeout_seconds):
    error_msg = f"{comm_name} timed out after {timeout_seconds} seconds. ..."
    self.MPI_Abort(error_msg)
```

타임아웃이 걸렸다는 것은 작업 스레드가 아직 `comm.Barrier`나 `comm.bcast` 안에 있다는 뜻이다. 그 상태에서 메인 스레드가 `MPI_Abort`를 거쳐 `self.comm.Abort(error_code)`를 부른다([DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894)). 두 스레드가 동시에 MPI를 호출하는 셈이라 MPI가 `MPI_THREAD_MULTIPLE`로 초기화되어 있어야 정의된 동작이 된다. 코드 어디에도 `MPI.Init_thread`나 `MPI.Query_thread` 확인이 없어서([DAO_Constants.py:135](5_DAO/SRC/DAO_Constants.py#L135)에서 `MPI.COMM_WORLD`만 잡는다) 실행 환경의 기본값에 전적으로 기댄다. 직렬화 수준으로 초기화된 구현에서는 감시 장치가 목적을 이루지 못하고 중단 호출 자체가 매달릴 수 있다.

더해서 `MPI_Abort`는 `comm.Abort` 전에 호출 스택 전체의 지역 변수를 요약한다([DAO_Main.py:6841](5_DAO/SRC/DAO_Main.py#L6841)). `_summarize_value`가 상한을 지키므로 폭주하지는 않지만, 프레임 수만큼 `linecache` 파일 읽기가 붙는 `inspect.stack()` 비용이 더해져 중단이 늦어진다. 그 사이 다른 rank는 같은 통신에서 계속 기다린다.

처방:
- 1. `Setup` 초반에 `MPI.Query_thread() == MPI.THREAD_MULTIPLE` 여부를 확인해 로그에 남긴다.
- 2. [DAO_Main.py:6939](5_DAO/SRC/DAO_Main.py#L6939)의 타임아웃 경로에서는 `MPI_Abort` 대신 진단 기록 후 `os._exit(error_code)`를 쓴다. 프로세스가 끊기면 다른 rank는 통신 오류로 정리되므로 스레드 안전성에 기대지 않는다.

### 9 (MEDIUM, P14 ㉰) `MPI_Abort` 뒤 코드가 이어질 수 있다

```python
# DAO_Main.py:6800, 6807-6811
def MPI_Abort(self, error_msg: str, error_code: int = 1) -> NoReturn:
    if self._in_mpi_abort:
        print(f"[Rank {self.rank}] MPI_Abort re-entered: {error_msg}", flush=True)
        self.comm.Abort(error_code)
        return  # comm.Abort() 이후 도달 불가이나 방어적 배치
```

반환 표기는 `NoReturn`인데 실제로 반환하는 경로가 있다. 호출부는 전부 반환하지 않는다는 전제로 쓰여 있어서, 이 경로가 실제로 반환하면 그 다음 줄이 성립하지 않는다. 대표 사례를 셋 든다.

```python
# DAO_Main.py:7985-7991 (Read_FER_From_File)
try:
    with open(result_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
except OSError as error:
    self.MPI_Abort(f"Failed to open {result_file}: {error}")

if not lines:            # lines가 정의되지 않음 -> UnboundLocalError
```

```python
# DAO_Main.py:1799-1808 (Gather_Ref_C_Results)
if matrix is None:
    self.MPI_Abort(error_msg)
...
max_iteration = matrix.max_iteration    # None.max_iteration -> AttributeError
```

```python
# DAO_Main.py:6959-6969 (_safe_bcast)
except Exception as e:
    ...
    self.MPI_Abort(error_msg)
# 함수가 암묵적으로 None을 반환 -> 호출부가 None을 데이터로 받는다
```

`_safe_bcast`의 경우가 특히 나쁘다. 중단이 실제로 끊기지 않으면 **모든 rank가 None을 정상 값처럼 받아 계속 진행**하므로, 프로세스가 죽는 대신 틀린 상태로 전진한다.

처방: [DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894) 다음 줄에 `os._exit(error_code)`를 넣고, [DAO_Main.py:6811](5_DAO/SRC/DAO_Main.py#L6811)의 `return`을 `os._exit(error_code)`로 바꾼다. 그러면 `NoReturn` 표기가 실제와 맞는다.

### 10 (MEDIUM, P14 ㉱) 최상위 처리부에서 같은 내용을 두 번 쌓고, 두 번째 스택은 쓸모가 없다

```python
# DAO_Main.py:10405-10415
    except Exception as exc:
        if LLR_opt is not None:
            try:
                LLR_opt.Log_Unhandled_Exception(exc)
            except Exception as log_error:
                ...
            LLR_opt.MPI_Abort(f"Unhandled exception: {type(exc).__name__}: {exc}")
```

`Log_Unhandled_Exception`은 `_collect_error_state_snapshot()`을 기본 인자(`include_stack=True`)로 부른다([DAO_Main.py:2555](5_DAO/SRC/DAO_Main.py#L2555)). 그 안의 `inspect.stack()`은 **현재 살아 있는 스택**, 곧 `Main` 처리부의 프레임만 훑는다([DAO_Main.py:676](5_DAO/SRC/DAO_Main.py#L676)). 예외가 실제로 난 프레임은 이미 풀렸고 `exc.__traceback__`에만 남아 있다. 그래서 이 절은 "Local Variables (Call Stack)"라는 제목 아래 `Main`의 지역 변수(`LLR_opt`, `exc`) 요약만 담는다.

이어서 `MPI_Abort`가 같은 파일에 두 번째 기록을 붙이는데([DAO_Main.py:6871](5_DAO/SRC/DAO_Main.py#L6871)), 이쪽의 `inspect.stack()` 역시 같은 처리부 프레임을 본다. 쓸 만한 정보는 `_write_error_log`가 만든 traceback 한 벌뿐인데 그 한 벌을 얻으려고 스택 요약을 두 번 돌린다.

처방: `MPI_Abort` 서명에 `capture_stack: bool = True`를 더하고 [DAO_Main.py:6841](5_DAO/SRC/DAO_Main.py#L6841)의 수집을 그 값으로 감싼다. [DAO_Main.py:10415](5_DAO/SRC/DAO_Main.py#L10415)의 호출을 `capture_stack=False`로 바꾸고, `Log_Unhandled_Exception`도 `self._collect_error_state_snapshot(include_stack=False)`로 부른다.

### 11 (MEDIUM, P14 ㉳) 중단 직전에 쓰던 파일이 잘린 채 남는다

```python
# DAO_LLR_MATRIX.py:549-559
def Save_Matrix(self, save_dir: str) -> None:
    lines = self.Build_LLR_Matrix_Output_Lines()
    save_path = os.path.join(save_dir, self.LLR_matrix_file_name)
    try:
        os.makedirs(save_dir, exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as file:
            for line in lines:
                file.write(f"{line}\n")
```

```python
# DAO_Main.py:1071-1079
def _Write_End_Flag(self, file_path: str, flag: bool = False):
    if not self.is_root:
        return
    try:
        with open(file_path, "w") as f:
            f.write("1" if flag else "0")
```

둘 다 대상 파일을 먼저 잘라 낸 뒤 내용을 채운다. 다른 rank의 `comm.Abort`는 이 프로세스를 신호로 끊으므로, 하필 그 사이에 걸리면 최적 매트릭스 파일이 절반만 남거나 플래그 파일이 빈 채로 남는다. 최적 매트릭스는 세션의 결과물이고 `4_Optimal/`에 누적되므로 복구 수단이 없다.

처방: 두 함수 모두 같은 디렉토리에 `{이름}.tmp`로 쓰고 `os.replace(tmp, dest)`로 바꾼다. `os.replace`는 같은 파일 시스템 안에서 원자적으로 동작한다. `Make_Log_Backup`의 `os.rename`도 같은 이유로 `os.replace`가 낫다(발견 12 참조).

### 12 (MEDIUM, P15 ㉰) 같은 이름의 백업 로그가 만들어질 수 있다

```python
# DAO_Main.py:2196-2199 (Get_Log_File_Name)
time_str = create_time.strftime("%Y.%m.%d__%H.%M.%S")
updated_suffix = "_updated" if has_update else ""
...
return f"{time_str}___LLR_MATRIX_from_{start_idx}_to_{end_idx}{updated_suffix}.txt"
```

```python
# DAO_Main.py:6636-6647 (Make_Log_Backup)
end_idx = self.current_LLR_matrix_idx
new_name = self.Get_Log_File_Name(self.log_create_time, self.log_start_matrix_idx, end_idx, has_update=self.log_has_update)
renamed_log_path = os.path.join(self.session_logs_dir, new_name)
try:
    os.rename(self.log_file_path, renamed_log_path)
```

이름을 이루는 것은 초 단위 생성 시각, 시작 매트릭스 idx, 종료 매트릭스 idx, update 여부 넷뿐이다. 회전 직후 `log_create_time`은 현재 시각으로 갱신되고 `log_start_matrix_idx`는 `current_LLR_matrix_idx`가 된다([DAO_Main.py:6650](5_DAO/SRC/DAO_Main.py#L6650)). 따라서 **매트릭스 idx가 그대로인 채 1초 안에 두 번 회전하면** 두 백업의 이름이 완전히 같아진다. 회전 문턱은 10000줄이므로 대량 로그를 쏟는 구간(모든 iteration의 FER 출력, CSW 로그 취합)에서 도달할 수 있다.

같은 이름일 때 결과는 운영체제마다 다르다.

- POSIX: `os.rename`이 기존 파일을 말없이 덮어쓴다. 먼저 회전된 10000줄이 사라지고 복구할 수 없다.
- Windows: `FileExistsError`(`OSError` 하위)가 나고 곧바로 `self.MPI_Abort(f"Make_Log_Backup: os.rename failed: {e}")`로 가서 전체 작업이 죽는다.

`Finalize_Log`도 같은 이름 규칙을 쓰므로([DAO_Main.py:6660](5_DAO/SRC/DAO_Main.py#L6660)) 마지막 회전 직후 1초 안에 실행이 끝나면 같은 충돌이 난다.

처방: `Make_Log_Backup`과 `Finalize_Log`에서 대상 경로가 이미 있으면 `_2`, `_3` 순으로 접미사를 붙여 빈 이름을 찾은 뒤 `os.replace`를 쓴다. 이름 결정을 `Get_Unique_Log_File_Path(base_name)` 한 함수로 모아 두 곳이 같은 규칙을 쓰게 한다.

### 13 (MEDIUM, P15 ㉯) 중단 처리 중 회전이 실패하면 진단이 통째로 사라진다

`_in_mpi_abort` 플래그가 막는 범위를 따라가면 다음 경로가 나온다.

- 1. 어떤 이유로 `MPI_Abort(msg)`가 불린다. `self._in_mpi_abort = True`가 세워진다([DAO_Main.py:6812](5_DAO/SRC/DAO_Main.py#L6812)).
- 2. 곧바로 `self.Write_Log_Lines(full_error_msg)`를 부른다([DAO_Main.py:6819](5_DAO/SRC/DAO_Main.py#L6819)).
- 3. `log_line_count`가 이미 10000 이상이면 `Write_Log_Lines` 끝에서 `Make_Log_Backup()`이 불린다([DAO_Main.py:9959](5_DAO/SRC/DAO_Main.py#L9959)).
- 4. 거기서 `os.rename`이 실패하면 `_in_mpi_abort`가 True이므로 `_write_error_log(self.rank, e)` 뒤 `self.comm.Abort(1)`이 즉시 실행된다([DAO_Main.py:6642](5_DAO/SRC/DAO_Main.py#L6642)).

이 경로에서 프로세스는 `MPI_Abort`의 상세 기록 구간([DAO_Main.py:6825](5_DAO/SRC/DAO_Main.py#L6825) 이후)에 **도달하지 못한다**. 남는 것은 rename 실패 자체의 traceback뿐이고, 애초에 중단을 부른 원인 메시지와 호출 스택은 기록되지 않는다. 로그 디렉토리가 가득 찼거나 권한이 바뀐 상황은 곧 무언가 잘못되어 중단이 불리는 상황이기도 해서, 하필 원인이 가장 궁금한 때에 진단이 빈다.

같은 경로에서 `log_line_count`는 회전 실패 시 0으로 되돌아가지 않는다([DAO_Main.py:6650](5_DAO/SRC/DAO_Main.py#L6650)이 rename 뒤에 있다). 그래서 이후 모든 로그 줄이 다시 rename을 시도한다.

처방:
- 1. `MPI_Abort`에서 상세 로그 기록 블록을 `Write_Log_Lines` 호출보다 **앞으로** 옮긴다. 파일 한 벌을 확보한 뒤에 세션 로그를 건드린다.
- 2. [DAO_Main.py:9959](5_DAO/SRC/DAO_Main.py#L9959)의 회전 검사에 `and not self._in_mpi_abort` 조건을 더한다. 중단 중에는 회전하지 않는다.

### 14 (MEDIUM, P15 ㉱) 워커 쪽 경고가 어디에도 남지 않는다

`Write_Log_Lines`는 첫 줄에서 비루트를 걸러 낸다([DAO_Main.py:9942](5_DAO/SRC/DAO_Main.py#L9942)). 그런데 워커 경로에서만 의미가 있는 경고가 이 함수로 나간다. 확인한 곳을 든다.

| 위치 | 버려지는 메시지 |
|------|----------------|
| [DAO_Main.py:959](5_DAO/SRC/DAO_Main.py#L959) | `Cleanup_Test_Environment`의 파일 삭제 실패 |
| [DAO_Main.py:1529](5_DAO/SRC/DAO_Main.py#L1529) | `Delete_Own_Uncors`의 uncor 삭제 실패 |
| [DAO_Main.py:7543](5_DAO/SRC/DAO_Main.py#L7543) | `Load_Uncors_From_Pool` 완료 알림 (rank마다 결과가 다른데 root 것만 남는다) |
| [DAO_Main.py:7949](5_DAO/SRC/DAO_Main.py#L7949) | `Run_ECC` 메모리 재시도 |
| [DAO_Main.py:9091](5_DAO/SRC/DAO_Main.py#L9091) | "현재 코어는 느려서 이후 테스트에서 제외됩니다" (정작 제외된 rank가 남길 수 없다) |

워커가 실제로 파일을 남기는 통로는 둘뿐이다. `_write_error_log`가 쓰는 `6_Error_Log/error_logs_{rank}.txt`(처리되지 않은 예외와 중단만)와 `Write_MPI_Error_Snapshot`이 쓰는 `error_snapshot_rank{N}.log`(통신 오류만, [DAO_Main.py:6752](5_DAO/SRC/DAO_Main.py#L6752)). 그래서 치명적이지 않은 워커 문제는 증거를 남기지 않고 지나간다.

처방: `Write_Rank_Warning(self, message: str)`을 만들어 `6_Error_Log/warnings_{rank}.txt`에 append한다. 위 표의 호출을 이쪽으로 옮기고, root는 기존대로 세션 로그에도 남긴다.

### 15 (MEDIUM, P5 ㉲) 고정 0.5초 대기가 결과 파일 가시성을 보장하지 못한다

```python
# DAO_Main.py:7942
time.sleep(0.5)
```

무엇을 기다리는지 주석이 없다. 문맥상 ECC가 쓴 결과 파일이 파일 시스템에 보이기를 기다리는 것으로 읽힌다. `subprocess.run`이 반환한 시점에 자식 프로세스는 이미 끝났고 운영체제 수준 쓰기는 완료되어 있으므로, 같은 노드의 로컬 저장소라면 이 대기는 필요 없다. 반대로 `local_session_dir`이 네트워크 공유 위에 있으면 0.5초로는 부족할 수 있고, 그때 `Gather_Ref_C_Results`는 아무 말 없이 그 rank를 0으로 처리한다.

```python
# DAO_Main.py:1848-1856
if not self.is_current_core_excluded:
    file_name = self.Get_Result_File_Name(process_idx=self.rank, ch_idx=ch_idx)
    file_path = os.path.join(self.local_session_dir, file_name)
    if os.path.exists(file_path):
        s_test, s_error, s_iter, s_err_per_iter = self.Read_Ref_C_Result(file_path)
        ...
```

분자와 분모가 같은 `sendbuf`에서 나오므로 FER 값 자체는 왜곡되지 않는다. 다만 **측정 프레임 수가 조용히 줄어든다**. 모든 rank가 실패해야만 `total_tests == 0` 중단에 걸리므로 일부만 빠진 경우는 눈치챌 방법이 없다. 또한 while 루프가 여러 번 도는 DEFAULT 모드에서는 반복마다 0.5초가 그대로 누적된다.

처방:
- 1. [DAO_Main.py:7942](5_DAO/SRC/DAO_Main.py#L7942)의 고정 대기를 없애고, 결과 파일 경로가 나타날 때까지 0.05초 간격으로 최대 5초 기다리는 `_Wait_For_Result_File(ch_idx)`로 바꾼다.
- 2. [DAO_Main.py:1852](5_DAO/SRC/DAO_Main.py#L1852)의 `if os.path.exists(...)`에 `else` 절을 붙여, 제외되지 않은 rank에 결과 파일이 없으면 발견 14의 rank별 경고로 남긴다.

### 16 (MEDIUM, P5 ㉱) `MAX_RUN_ECC_ERRORS`의 이름과 실제 쓰임이 다르다

```python
# DAO_Config.py:123
MAX_RUN_ECC_ERRORS: int = 9999               # RUN_ECC 오류 수
```

읽는 자리는 한 곳이다.

```python
# DAO_Main.py:8565-8566 (Set_Max_Error)
if self.is_root:
    self.max_error = DAO_CONFIG.MAX_RUN_ECC_ERRORS
```

그리고 `max_error`가 쓰이는 자리도 한 곳이다.

```python
# DAO_Main.py:1066-1068 (Check_Test_End)
if self.is_root:
    if self.total_num_errors[ch_idx] >= self.max_error:
        self.Write_Run_ECC_End_Flag(True)
```

`total_num_errors`는 ECC가 보고한 **복호 실패 프레임 수**를 모은 값이다([DAO_Main.py:1889](5_DAO/SRC/DAO_Main.py#L1889)). 즉 이 설정은 "ECC 실행이 몇 번 실패하면 포기할지"가 아니라 "FER 측정을 끝내기 위해 몇 개의 오류 프레임을 모을지"를 정하는 값이다. 이름과 주석이 반대로 읽히므로, 재시도 한도로 오해한 사람이 값을 10 같은 작은 수로 낮추면 모든 FER 측정이 오류 10개에서 멈추고 통계 정밀도가 두 자릿수만큼 떨어진다. 그런데도 프로세스는 정상적으로 끝난다.

처방: 이름을 `TARGET_NUM_FRAME_ERRORS`로 바꾸고 주석을 "한 채널 FER 측정을 끝낼 누적 프레임 오류 수"로 다시 쓴다. `Set_Max_Error`의 `self.max_error`도 `self.target_num_frame_errors`로 바꾸면 [DAO_Main.py:1067](5_DAO/SRC/DAO_Main.py#L1067)에서 뜻이 그대로 읽힌다.

### 17 (MEDIUM, P14 ㉲, P13) 타임아웃 감시를 거치지 않는 집단 통신이 셋 있다

```python
# DAO_Main.py:1861
self.comm.Reduce(sendbuf, recvbuf, op=MPI.SUM, root=0)
```

```python
# DAO_Main.py:9049
all_elapsed_times = self.comm.allgather(elapsed_time)
```

```python
# DAO_Main.py:7011
counts: list[int] = self.comm.allgather(self.barrier_count)
```

나머지 통신은 `_mpi_comm_with_timeout`을 지나므로 매달리면 중단으로 끝나지만, 이 셋은 무한정 기다린다. `comm.Abort`는 모든 rank를 함께 끊으므로 DAO 스스로 만든 중단에서는 문제가 드러나지 않는다. 드러나는 것은 **한 rank가 MPI 밖에서 사라질 때**다. 운영체제의 메모리 부족 강제 종료, 노드 장애, 사용자의 프로세스 종료 같은 경우 남은 rank는 이 세 지점에서 영구히 멈추고 진단도 남기지 않는다. 발견 5에서 본 대로 ECC 실행이 메모리 부족으로 죽는 상황은 강제 종료와 이웃해 있다.

처방: 세 호출을 감싼다. `Reduce`는 반환값 대신 출력 버퍼를 채우므로 다음처럼 쓰면 된다.

```
self._mpi_comm_with_timeout(self.comm.Reduce, sendbuf, recvbuf, op=MPI.SUM, root=0,
                            comm_name=f"Reduce_ECC_results[ch{ch_idx}]")
```

`allgather` 둘은 반환값을 그대로 받으면 된다. 타임아웃 값은 발견 1의 처방을 적용한 뒤의 `MPI_COMM_TIMEOUT_SECONDS`를 쓴다.

### 18 (LOW, P13 ㉯㉲) 활성 코어가 0이 되는 경로가 없고, root 혼자 남는 경우는 경고가 없다

```python
# DAO_Main.py:9062-9065
# Root(rank 0) 보호: root는 파일 I/O, 결과 집계, 매트릭스 생성 등 핵심 역할 담당
if 0 in excluded_cores:
    excluded_cores.remove(0)
```

root가 항상 복원되므로 `active_cores`는 최소한 `[0]`을 담는다([DAO_Main.py:647](5_DAO/SRC/DAO_Main.py#L647)). 따라서 다음 두 자리의 방어 분기는 도달하지 않는다.

- [DAO_Main.py:1563](5_DAO/SRC/DAO_Main.py#L1563) `Distribute_Uncors_To_Local_Session`
- [DAO_Main.py:7417](5_DAO/SRC/DAO_Main.py#L7417) `_Setup_Uncor_Pool_For_Channel`

정작 실무에서 위험한 상태는 활성 코어가 rank 0 하나만 남는 경우다. 이때 uncor 전량이 root 한 곳으로 몰리고 측정 시간이 프로세스 수만큼 늘어나 발견 1의 배리어 타임아웃과 곧바로 맞물린다. 그런데 이 상태에는 아무 경고가 없다.

또한 root 보호는 `is_current_core_excluded`에도 반영되므로 root가 진짜로 느려도 계속 ECC를 돌린다. root가 병목이 되는 상황 자체는 막지 못한다. 이것은 설계 선택으로 보이며 로그로 드러내 주는 것으로 충분하다.

처방: [DAO_Main.py:9088](5_DAO/SRC/DAO_Main.py#L9088) 뒤에 `if len(self.active_cores) <= 1:` 경고를 넣고, 위 두 자리의 도달하지 않는 분기는 지운다.

### 19 (LOW, P13 ㉮) 속도 테스트가 시드 모드를 바꾸고 되돌리지 않는다

```python
# DAO_Main.py:9037-9038
# Speed test용 seed mode 설정 (이후 Set_Seed_Mode에서 자동으로 재설정됨)
self.current_seed_mode = SeedMode.DEFAULT
```

주석이 말하는 자동 재설정은 `Test_LLR`이 첫 줄에서 `Set_Ref_C_Parameters`를 부르고 그 안에서 `Set_Seed_Mode`가 돌기 때문에 성립한다([DAO_Main.py:8952](5_DAO/SRC/DAO_Main.py#L8952), [DAO_Main.py:8608](5_DAO/SRC/DAO_Main.py#L8608)). 주기적 재점검이 trial 사이에서 실행되므로 지금 구조에서는 다음 테스트 전에 반드시 복구된다.

다만 `Test_Core_Speed`와 다음 `Test_LLR` 사이에 `_Redistribute_Uncor_Pool_Uniform`이 끼고, 그 안에서 `current_seed_mode`를 읽는 코드가 하나라도 생기면 즉시 틀린 값을 본다. 함수가 자기 부작용을 스스로 되돌리지 않는 것은 그 자체로 위험을 남긴다.

처방: [DAO_Main.py:9037](5_DAO/SRC/DAO_Main.py#L9037) 앞에 `previous_seed_mode = self.current_seed_mode`를 두고, [DAO_Main.py:9097](5_DAO/SRC/DAO_Main.py#L9097) 뒤에서 `self.current_seed_mode = previous_seed_mode`로 되돌린다. 주석은 "속도 측정 동안만 DEFAULT를 쓰고 끝에서 되돌린다"로 다시 쓴다.

### 20 (LOW, P5) `Run_ECC`의 죽은 코드 둘

```python
# DAO_Main.py:7935
ecc_start = time.time()
```

`ecc_start`는 함수 어디에서도 읽히지 않는다(`ecc_start_time`은 별개 인스턴스 변수로 `Set_Test_Environment`에서 설정된다, [DAO_Main.py:8474](5_DAO/SRC/DAO_Main.py#L8474)).

```python
# DAO_Main.py:7946-7954
except OSError as error:
    if error.errno == 12:
        ...
    else:
        self.MPI_Abort(f"ECC execution failed: {error}")
except (subprocess.CalledProcessError, FileNotFoundError) as error:
    self.MPI_Abort(f"ECC execution failed: {error}")
```

`FileNotFoundError`는 `OSError`의 하위 클래스라서(파이썬으로 확인) 위쪽 `except OSError`가 먼저 잡는다. `errno`가 2이므로 `else` 분기로 가 같은 메시지를 낸다. 결과가 같아 동작 문제는 없지만, 배치 파일이 없는 경우를 따로 다루려는 의도였다면 그 의도가 이뤄지지 않는다.

처방: `ecc_start` 줄을 지운다. 실행 파일 없음을 구분하고 싶으면 `except OSError` 블록 안에서 `errno.ENOENT`를 먼저 분기하고, 두 번째 except 절은 `except subprocess.CalledProcessError`만 남긴다.

### 21 (LOW, P15 ㉮) 줄 수 세기가 실제 파일 줄 수와 다르다

```python
# DAO_Main.py:803-807
with open(self.log_file_path, "a", encoding="utf-8") as log_file:
    for line in lines:
        log_file.write(f"{line}\n")
self.log_line_count += len(lines)
```

`len(lines)`는 전달된 리스트의 원소 수다. 그런데 한 원소가 줄바꿈을 품으면 파일에는 여러 줄이 들어간다.

```python
# DAO_Main.py:9925 (Write_Log_Separator)
self.Write_Log_Lines(f"\n{separator} [{log_msg} @ {self.Get_Timestamp()}] {separator}\n")
```

이 한 번의 호출은 파일에 세 줄(빈 줄, 구분선, 빈 줄)을 쓰지만 `log_line_count`는 1만 오른다. 구분선 호출이 많은 실행에서는 회전 시점이 뒤로 밀려 백업 파일이 `LOG_MAX_LINES`보다 꽤 커진다. 회전 자체는 정상 동작하므로 영향은 파일 크기에 그친다.

한편 `Write_Log_Lines` 재진입은 안전하다. `Make_Log_Backup`이 `log_line_count = 0`을 rename 성공 뒤이자 안내 메시지 기록 전에 실행하므로([DAO_Main.py:6650](5_DAO/SRC/DAO_Main.py#L6650)) 중첩 호출은 1회로 끝나고 반복 회전은 일어나지 않는다.

처방: [DAO_Main.py:807](5_DAO/SRC/DAO_Main.py#L807)을 `self.log_line_count += sum(line.count("\n") + 1 for line in lines)`로 바꾼다.

---

## 확인했으나 문제 없던 항목

- P5 ㉳ `Run_ECC`의 두 조기 반환(제외 코어, uncor 없음)은 집단 통신을 어긋나게 하지 않는다. `Test_LLR`의 while 루프([DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968)) 안에는 집단 통신이 하나도 없고, 루프 밖의 `Gather_Ref_C_Results`와 배리어는 모든 rank가 같은 횟수로 지난다.
- P5 ㉴ errno 12는 Linux의 `fork` 실패와 Windows의 `ERROR_NOT_ENOUGH_MEMORY` 대응 모두에서 나온다. errno 판정 자체는 두 운영체제에서 성립한다(실제 빈틈은 발견 5).
- P13 ㉮ 제외 판정 기준은 한 벌이다. `excluded_cores`(root 계산 뒤 bcast)와 `is_current_core_excluded`(`self.rank in self.excluded_cores`)가 [DAO_Main.py:9087](5_DAO/SRC/DAO_Main.py#L9087)에서 함께 정해지고, 결과 집계([DAO_Main.py:1818](5_DAO/SRC/DAO_Main.py#L1818), [DAO_Main.py:1848](5_DAO/SRC/DAO_Main.py#L1848)), uncor 분배([DAO_Main.py:1561](5_DAO/SRC/DAO_Main.py#L1561), [DAO_Main.py:7415](5_DAO/SRC/DAO_Main.py#L7415)), `Run_ECC` 건너뛰기([DAO_Main.py:7928](5_DAO/SRC/DAO_Main.py#L7928)), ack 집계([DAO_Main.py:1236](5_DAO/SRC/DAO_Main.py#L1236)), uncor 취합([DAO_Main.py:2123](5_DAO/SRC/DAO_Main.py#L2123))이 모두 같은 값을 본다.
- P13 ㉯ rank 0은 제외 목록에서 항상 복원되므로 root 전용 작업(생성, 판정, 저장, 로그)이 멈추는 경로는 없다([DAO_Main.py:9063](5_DAO/SRC/DAO_Main.py#L9063)).
- P13 ㉰ 제외 목록이 바뀌었을 때 `_Redistribute_Uncor_Pool_Uniform`이 `pool_has_uncor`(초기화 뒤 `_Setup_Uncor_Pool_For_Channel`이 bcast로 재설정)와 `has_uncor`(`Load_Uncors_From_Pool`이 전 채널을 다시 씀)를 함께 갱신한다. Partial 소스가 있을 때는 두 모드와 모든 채널을 덮는다(소스가 없을 때의 문제는 발견 3).
- P13 ㉱ `Reduce`의 분자와 분모가 같은 집합에서 나온다. 제외 코어는 `sendbuf`를 0으로 둔 채 참여하므로([DAO_Main.py:1846](5_DAO/SRC/DAO_Main.py#L1846)) `total_tests`와 `total_errors`가 동일한 활성 코어 집합의 합이다. 루프 중 경로(root 순차 읽기)도 같은 기준으로 제외 코어를 건너뛴다.
- P13 ㉳ `_last_speed_test_time`은 rank마다 다를 수 있으나 비교 판정은 root만 하고 `_safe_bcast`로 맞춘다([DAO_Main.py:8129](5_DAO/SRC/DAO_Main.py#L8129), [DAO_Main.py:10170](5_DAO/SRC/DAO_Main.py#L10170)). `Periodic_Recheck`은 전 rank가 같은 `stage_idx`와 같은 설정값으로 판단한다.
- P13 재점검이 `self.batch_path`를 속도 테스트용으로 덮어쓰지만, 다음 테스트가 `Set_Test_Environment`에서 `Make_Batch_File`로 다시 설정하므로 삭제된 배치 파일을 실행하는 경로는 없다([DAO_Main.py:8466](5_DAO/SRC/DAO_Main.py#L8466)).
- P14 ㉮ `except Exception` 20곳을 모두 확인했다. 대부분은 진단 기록 실패를 삼키고 본 흐름을 잇는 용도(`_write_error_log`, `Write_MPI_Error_Snapshot`, `_write_debug_snapshot`, `_summarize_value` 내부)라 삼킨 뒤 상태가 성립한다. 본 흐름을 삼키는 자리는 `Delete_Uncors`([DAO_Main.py:1511](5_DAO/SRC/DAO_Main.py#L1511))와 `Delete_Own_Uncors`([DAO_Main.py:1528](5_DAO/SRC/DAO_Main.py#L1528))의 파일 삭제 실패인데, 이어지는 `Load_Uncors_From_Pool`이 대상 파일을 다시 지우고 덮어쓰므로([DAO_Main.py:7530](5_DAO/SRC/DAO_Main.py#L7530)) 잔존 파일이 결과를 흔들지 않는다. 경고가 root에만 남는 문제는 발견 14에 담았다.
- P14 ㉲ 모듈 진입점에서 `Set_Configs_Manually`나 `Update_Configs`가 실패하면 모든 rank가 같은 설정 코드를 실행하므로 같은 예외를 만나 각자 `_write_error_log(rank, e)` 뒤 `comm.Abort(1)`을 부른다([DAO_Main.py:10419](5_DAO/SRC/DAO_Main.py#L10419)). rank별 파일 이름이 달라 기록이 서로 덮이지 않는다.
- P15 ㉮ `Write_Log_Lines` 에서 `Make_Log_Backup`을 거쳐 다시 `Write_Log_Lines`로 들어가는 재진입은 한 번으로 끝난다. `log_line_count = 0`이 중첩 호출보다 먼저 실행되므로 회전이 반복되지 않는다([DAO_Main.py:6650](5_DAO/SRC/DAO_Main.py#L6650)).
- 테스트 산출물 정리는 제외 코어에도 적용된다. `Cleanup_Test_Environment`는 모든 rank가 자기 `local_session_dir`에서 `result`로 시작하는 파일을 지우므로([DAO_Constants.py:129](5_DAO/SRC/DAO_Constants.py#L129), [DAO_Main.py:946](5_DAO/SRC/DAO_Main.py#L946)) 제외되었다가 복귀한 코어의 낡은 결과 파일이 집계에 섞이지 않는다.
