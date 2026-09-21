# 팀 M 요약: MPI 통신과 프로세스 수명 (관점 P1, P2, P3, P5, P13, P14, P15, P16)

- 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
- 기록: 2026-09-21
- 워커 문서: [worker_M_1.md](worker_M_1.md) (P1 집단 통신의 rank 정합), [worker_M_2.md](worker_M_2.md) (P2 타임아웃, P3 종료 신호, P16 난수), [worker_M_3.md](worker_M_3.md) (P5 실행 실패, P13 제외 코어, P14 예외 경로, P15 로그)

핵심 질문에 대한 답: 어긋난 자리가 있다. hang이나 전체 중단으로 이어지는 자리 5건, 틀린 결과를 내는 자리 2건을 찾았다.
가장 무거운 것은 집단 통신 타임아웃 예산(3600초)이 Ref_C 1회 실행 허용 시간(36000초)보다 짧아 정상 동작이 중단되는 것이며, 세 워커가 독립으로 같은 결론에 닿았다.

---

## ㉮ 워커 결과 요약

워커 발견 49건을 중복 제거해 39건으로 정리했다. 심각도는 리더가 교차 분석 결과로 조정했고, 조정한 것은 ㉯ 절에 사유를 적었다.

- CRITICAL 5건, HIGH 2건, MEDIUM 24건, LOW 8건
- 워커별 원 건수: 워커 1이 10건, 워커 2가 18건, 워커 3이 21건

### CRITICAL (프로세스 중단이나 hang)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| M-01 | CRITICAL | 배리어 타임아웃 하한 3600초가 Ref_C 1회 실행 허용 시간 36000초보다 짧다. `Test_LLR`의 while 루프 안에는 집단 통신이 없어 rank들이 다시 만나는 첫 지점이 `Gather_Ref_C_Results`의 배리어인데, 느린 코어 하나의 `Run_ECC`가 1시간을 넘기면 먼저 도착한 rank가 정상 동작 중에 job 전체를 중단시킨다. 코어 제외 문턱이 평균의 2.0배라 1.99배까지 느린 코어가 활성으로 남는다 | [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692), [DAO_Main.py:1839](5_DAO/SRC/DAO_Main.py#L1839), [DAO_Main.py:7939](5_DAO/SRC/DAO_Main.py#L7939), [DAO_Constants.py:144](5_DAO/SRC/DAO_Constants.py#L144) | Full 테스트 한 채널이 빠른 코어 기준 1시간을 넘고 rank 사이 도달 시각 차이가 3600초를 넘을 때. errno 12 재시도(최대 600초)가 겹치면 문턱이 더 낮아진다 | `TIME_CONFIG`에 `MPI_TEST_BARRIER_TIMEOUT_SECONDS = SIM_MAX_TIME_OUT + MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY + 여유`를 새로 두고 [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692)의 `max(MPI_COMM_TIMEOUT_SECONDS, 3600)`을 이 값으로 바꾼다. 계산식을 설정 한 곳에 모은다 | 1, 2, 3 |
| M-02 | CRITICAL | GEN_SINGLE_ROW 루프에서 각 rank가 DAO 종료 플래그 파일을 스스로 읽고 `_gen_single_row_stop_idx`를 정한 뒤 `break` 한다. 감지 회차가 한 주기 어긋나면 stop idx가 통째로 한 주기 차이 나서, 빠져나간 rank는 Barrier에 들어가고 남은 rank는 bcast에 들어간다. 같은 판정을 `Run_Optimization`은 root가 읽고 bcast하는 관용구로 처리한다 | [DAO_Main.py:10056-10067](5_DAO/SRC/DAO_Main.py#L10056), [DAO_Main.py:10075](5_DAO/SRC/DAO_Main.py#L10075), [DAO_Main.py:10190](5_DAO/SRC/DAO_Main.py#L10190) | `RUN_DAO_MODE=GEN_SINGLE_ROW`에서 사용자가 종료 플래그 파일을 쓰는 순간이 어느 rank의 검사 주기와 겹칠 때 | root만 `Read_DAO_End_Flag()`를 부르고 결과를 `_safe_bcast`로 내린다. [DAO_Main.py:8071-8077](5_DAO/SRC/DAO_Main.py#L8071)의 관용구를 그대로 옮긴다 | 1, 2 |
| M-03 | CRITICAL | Partial uncor가 0개일 때의 정상 종료 경로가 실제로는 전체 중단으로 끝난다. `_Signal_Graceful_Stop_No_Partial`은 플래그 파일만 쓰고 돌아오는데 trial 루프는 그 플래그를 `Test_Trial_LLR()` 뒤에서 읽으므로, 그 사이 빈 Partial pool로 테스트가 한 번 더 돌아 `total_tests=0` 중단에 걸린다. 진단 문구는 "All cores failed to produce results"가 되어 원인과 맞지 않는다 | [DAO_Main.py:9457-9477](5_DAO/SRC/DAO_Main.py#L9457), [DAO_Main.py:8072-8077](5_DAO/SRC/DAO_Main.py#L8072), [DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884) | `ENABLE_TWO_STAGE_TEST=True`이고 Full uncor가 모두 복호에 성공해 Partial pool이 비는 경우. 호출 경로 3곳이 모두 같다 | `_Signal_Graceful_Stop_No_Partial`이 rank 공용 플래그 `self.is_graceful_stop_requested`를 세우게 하고, `Run_Optimization`의 trial 루프 머리와 `Test_Trial_LLR` 진입 직전에서 이 플래그를 보고 즉시 `break` 한다. 함께 [DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884)의 중단 메시지에 "Partial pool 고갈"과 "코어 실패"를 구분해 적는다 | 1 |
| M-04 | CRITICAL | `Test_Core_Speed`의 `comm.allgather`가 타임아웃 감시를 거치지 않는다. 바로 앞이 `Run_ECC`라 rank 사이 도달 시각 편차가 가장 큰 자리인데, 한 rank가 멈추면 전 rank가 로그 한 줄 없이 영구 대기한다. `Periodic_Recheck`도 같은 함수를 다시 부른다 | [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049) | `ENABLE_CORE_SPEED_TEST=True`에서 속도 측정용 ECC가 한 rank에서 멈추거나 그 rank가 MPI 밖에서 죽을 때 | `_safe_bcast`와 같은 모양의 `_safe_allgather`를 추가하고 이 자리를 교체한다. 타임아웃 값은 M-01의 배리어 전용 값을 쓴다 | 1, 2, 3 |
| M-05 | CRITICAL | `_Redistribute_Uncor_Pool_Uniform`이 Partial 소스 디렉토리를 찾지 못하면 `pool_has_uncor[PARTIAL]`이 전 rank에서 False로 남는데, `Load_Uncors_From_Pool`은 `current_loaded_test_mode`를 PARTIAL로 세워 버려서 다음 `Ensure_Uncors_Loaded`가 재로드를 건너뛴다. 모든 rank가 `Run_ECC`를 건너뛰고 `total_tests=0` 중단으로 끝난다 | [DAO_Main.py:9182](5_DAO/SRC/DAO_Main.py#L9182), [DAO_Main.py:7521](5_DAO/SRC/DAO_Main.py#L7521), [DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884) | 주기적 재점검으로 제외 목록이 바뀐 뒤 `tmp_partial_uncors` 하위 디렉토리가 없는 상태 | `Load_Uncors_From_Pool`이 실제로 적재한 파일이 0개면 `current_loaded_test_mode`를 세우지 않고 호출자에게 실패를 돌려준다. `_Redistribute_Uncor_Pool_Uniform`은 소스 부재를 발견하면 즉시 진단을 남기고 중단한다 | 3 |

### HIGH (틀린 결과)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| M-06 | HIGH | `Run_ECC` 종료 확인 응답(ack) 판정이 두 방향으로 틀린다. `_Report_Missing_Acks`가 유일한 동기화 배리어보다 앞에서 돌아 아직 ECC 중인 정상 rank를 미응답으로 적고(거짓 양성), `run_ecc_ack/`를 비우는 코드가 없어 한 번 ack한 rank는 이후 어느 채널, 어느 trial에서도 응답한 것으로 집계된다(거짓 음성). 결과적으로 첫 채널 뒤로는 무조건 "이상 없음"이 된다 | [DAO_Main.py:8989](5_DAO/SRC/DAO_Main.py#L8989), [DAO_Main.py:1211](5_DAO/SRC/DAO_Main.py#L1211) | 항상 | `_Report_Missing_Acks` 호출을 동기화 배리어 뒤로 옮기고, `Initialize_Run_ECC_End_Flag`에서 `run_ecc_ack/` 폴더를 비운다 | 2 |
| M-07 | HIGH | `_write_error_log`가 `capture_locals=True`로 traceback을 만들면서 지역 변수 크기를 제한하지 않는다. 같은 파일의 `_summarize_value`는 상한을 지키고 있어 상한 있는 경로와 없는 경로가 한 로그에 섞인다. uncor 원본 전체를 리스트로 쥔 프레임이 둘 있어 수백 MB 로그가 나올 수 있다(원소 30만 개 리스트 하나가 2.3 MB 문자열) | [DAO_Main.py:188](5_DAO/SRC/DAO_Main.py#L188), [DAO_Main.py:7410](5_DAO/SRC/DAO_Main.py#L7410), [DAO_Main.py:1555](5_DAO/SRC/DAO_Main.py#L1555) | uncor 적재나 분배 구간에서 예외가 날 때 | `_write_error_log`가 `_summarize_value`와 같은 상한을 쓰도록 프레임별 지역 변수 요약을 거쳐 기록한다 | 3 |

### MEDIUM (엣지케이스 위험, 누락 커버리지)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| M-08 | MEDIUM | DAO는 모든 MPI 호출을 보조 스레드에서 돌리는데 `mpi4py.rc` 설정도 `MPI.Query_thread()` 확인도 없다. 타임아웃 경로에서는 주 스레드가 `comm.Abort`를 부르는 동안 통신 스레드가 같은 communicator 안에 살아 있어 두 스레드가 동시에 MPI에 들어간다 | [DAO_Constants.py:135](5_DAO/SRC/DAO_Constants.py#L135), [DAO_Main.py:6896-6944](5_DAO/SRC/DAO_Main.py#L6896) | MPI_THREAD_MULTIPLE 미만을 제공하는 빌드에서 실행할 때 | `DAO_Constants.py`의 `import MPI` 앞에 `mpi4py.rc.thread_level = "multiple"`을 두고, `Setup` 초입에서 `MPI.Query_thread()`가 `MPI.THREAD_MULTIPLE` 미만이면 경고를 남기고 타임아웃 감시를 끈다 | 1, 2, 3 |
| M-09 | MEDIUM | `Update_Optimal_LLR`이 root에서만 `target_group_indices`를 고치고 bcast 묶음에서 빠뜨린다. 다음 `Gen_Trial_LLR`의 bcast까지 root와 worker의 값이 다르다 | [DAO_Main.py:9574-9585](5_DAO/SRC/DAO_Main.py#L9574) | optimal 갱신으로 그룹 수가 줄어든 trial 직후 | root 블록을 빠져나온 뒤 [DAO_Main.py:9600](5_DAO/SRC/DAO_Main.py#L9600) 다음 줄에 `self.target_group_indices = self._safe_bcast(self.target_group_indices if self.is_root else None, "Bcast_target_group_indices_after_update")`를 넣는다 | 1 |
| M-10 | MEDIUM | `Check_Barrier_Sync`가 Stage 시작과 Trial 시작 두 곳에만 있어 채널당 6회 이상의 배리어 구간을 덮지 못한다. 게다가 이 함수의 bcast 타임아웃은 1200초이고 `MPI_Barrier`는 3600초라, 어긋났을 때 bcast 쪽이 먼저 터져 원인 지점이 가려진다 | [DAO_Main.py:6698-6741](5_DAO/SRC/DAO_Main.py#L6698), [DAO_Main.py:2258-2259](5_DAO/SRC/DAO_Main.py#L2258), [DAO_Main.py:2344-2345](5_DAO/SRC/DAO_Main.py#L2344) | rank 사이 배리어 수가 어긋나는 모든 경우 | `Test_LLR`의 채널 루프 머리와 `Test_Trial_LLR`의 Partial과 Full 사이에 `Check_Barrier_Sync`를 추가하고, 이 함수의 bcast 타임아웃을 `MPI_Barrier`와 같은 값으로 맞춘다 | 1 |
| M-11 | MEDIUM | `comm.Reduce`가 타임아웃 감시를 거치지 않는다. 바로 앞 배리어가 rank를 맞춰 주므로 위험은 낮으나, 배리어와 Reduce 사이에서 한 rank가 죽으면 진단 없이 매달린다 | [DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861) | 배리어 통과 뒤 결과 파일 읽기 구간에서 한 rank가 죽을 때 | `_safe_reduce`를 추가해 `_mpi_comm_with_timeout(self.comm.Reduce, sendbuf, recvbuf, op=MPI.SUM, root=0, comm_name=...)` 형태로 감싼다 | 1, 3 |
| M-12 | MEDIUM | 플래그 파일 읽기가 `FileNotFoundError`만 잡아 Windows `PermissionError`에서 한 rank가 작업 전체를 중단시킨다 | [DAO_Main.py:1091](5_DAO/SRC/DAO_Main.py#L1091), [DAO_Main.py:1105](5_DAO/SRC/DAO_Main.py#L1105) | 사용자가 편집기로 플래그 파일을 연 채 저장할 때 | `except` 절을 `(OSError, ValueError)`로 넓히고 읽기 실패를 "플래그 없음"으로 다룬다 | 2 |
| M-13 | MEDIUM | GEN_SINGLE_ROW 루프가 루프 안 결과 집계 없이 `Check_Test_End`를 불러 이전 candidate의 낡은 오류 수로 종료를 정한다. LOAD_UNCOR가 아닌 모드에서 candidate마다 시행 횟수가 달라진다 | [DAO_Main.py:10096-10102](5_DAO/SRC/DAO_Main.py#L10096) | `RUN_DAO_MODE=GEN_SINGLE_ROW`를 LOAD_UNCOR가 아닌 seed 모드로 실행할 때 | 루프 안에 `Gather_Ref_C_Results(is_test_end=False)`를 넣어 `Test_LLR`과 같은 순서로 맞춘다 | 2 |
| M-14 | MEDIUM | `base_seed = int(time.time())`이라 같은 초에 띄운 두 세션은 rank별 시드가 완전히 같아 동일한 mutation 순서를 탐색한다 | [DAO_Main.py:8750](5_DAO/SRC/DAO_Main.py#L8750) | 스크립트로 여러 세션을 동시에 기동할 때 | 시계 해상도와 엔트로피를 올리고(`time.time_ns()`와 프로세스 식별자 조합) rank 오프셋을 해시로 만든다 | 2 |
| M-15 | MEDIUM | 속도 측정용 고정 시드 `CORE_SPEED_TEST_SEED`가 `mode_init_seed`에만 들어 있고 어느 인자 목록에도 없다. docstring이 약속한 "모든 프로세스 동일 시드"를 보장하는 코드가 없어 `excluded_cores` 판정 기반이 흔들린다. `fn=1, max_num_test=1`이라 측정 구간도 매우 짧다 | [DAO_Config.py:237](5_DAO/SRC/DAO_Config.py#L237), [DAO_Main.py:6471](5_DAO/SRC/DAO_Main.py#L6471) | `ENABLE_CORE_SPEED_TEST=True` | 시드를 배치 파일 인자로 실제 전달하거나, 쓰지 않는 설정과 docstring을 함께 정리한다. 측정 구간을 늘려 편차를 줄인다 | 2 |
| M-16 | MEDIUM | `MPI_Barrier`와 `Check_Barrier_Sync`만 통신 예외를 잡지 않아 hang 진단이 가장 필요한 경로에서 worker의 상태 스냅샷을 잃는다 | [DAO_Main.py:6690](5_DAO/SRC/DAO_Main.py#L6690), [DAO_Main.py:6713](5_DAO/SRC/DAO_Main.py#L6713) | 배리어에서 MPI 예외가 날 때 | 예외 처리와 `Write_MPI_Error_Snapshot` 호출을 `_mpi_comm_with_timeout` 안으로 모아 모든 통신이 같은 진단을 남기게 한다 | 2 |
| M-17 | MEDIUM | `MPI_COMM_TIMEOUT_SECONDS = 2 * MAX_ECC_MEMORY_RETRY * MAX_ECC_MEMORY_RETRY_DELAY = 1200`인데 주석은 "1시간 이상이면 타임아웃 없음과 동일"이라 적혀 있다. 그런 분기는 없고 배리어만 별도로 3600초 바닥을 깔아 두 한도가 설정 한 곳에서 읽히지 않는다. 산식은 재시도 대기 시간만 세고 ECC 실행 시간은 전혀 세지 않는다 | [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323) | 항상 | M-01의 처방과 묶어 bcast용과 배리어용 두 설정으로 나누고, 각 설정의 산식과 주석을 실제 동작에 맞춰 다시 쓴다 | 1, 2, 3 |
| M-18 | MEDIUM | trial마다 base64 난수 상태 약 5 KB를 root 로그에 남긴다(trial 10,000회면 약 50 MB). 로그 회전은 줄 수로만 판단해 앞당겨지지 않는다. 복원은 `Run_Optimization` 맨 앞 1회뿐이라 중간 trial 상태를 붙여 넣어도 그 trial은 재현되지 않는다 | [DAO_Main.py:2355-2359](5_DAO/SRC/DAO_Main.py#L2355) | 항상 | 난수 상태 기록을 디버그 설정 아래로 내리고 별도 파일에 남긴다. 복원 지점을 trial 단위로 넓히거나 docstring에서 세션 단위 재현임을 분명히 한다 | 2 |
| M-19 | MEDIUM | 제외된 코어와 uncor 없는 rank가 `Run_ECC` 즉시 반환 뒤 테스트 while 루프를 대기 없이 회전하며 공유 종료 플래그 파일을 한 바퀴에 3회씩 연다 | [DAO_Main.py:8968](5_DAO/SRC/DAO_Main.py#L8968), [DAO_Main.py:7927-7934](5_DAO/SRC/DAO_Main.py#L7927) | `excluded_cores`가 있거나 uncor 없는 채널을 도는 동안 | 루프 안에 집단 통신이 없으므로 해당 rank는 while 루프를 건너뛰고 종료 플래그를 긴 주기로만 확인하게 한다 | 2, 3 |
| M-20 | MEDIUM | ECC 실패 원인이 어디에도 남지 않는다. `subprocess.run`이 stdout과 stderr를 받지 않고, 재시도 로그는 root 전용 `Write_Log_Lines`라 워커 rank에서 사라진다 | [DAO_Main.py:7939](5_DAO/SRC/DAO_Main.py#L7939), [DAO_Main.py:7949](5_DAO/SRC/DAO_Main.py#L7949), [DAO_Main.py:9942](5_DAO/SRC/DAO_Main.py#L9942) | rank 0이 아닌 코어에서 ECC가 실패할 때 | `capture_output=True`로 받아 실패 시 `error_logs_{rank}.txt`에 남긴다. 워커 경고를 rank별 파일로 흘리는 경로를 만든다 | 3 |
| M-21 | MEDIUM | errno 12 재시도가 셸(`cmd`, `bash`) 기동 실패만 덮는다. 셸은 떴는데 ECC 실행 파일이 메모리 부족으로 죽으면 `CalledProcessError`가 되어 재시도 없이 즉시 중단된다 | [DAO_Main.py:7938](5_DAO/SRC/DAO_Main.py#L7938), [DAO_Main.py:7953](5_DAO/SRC/DAO_Main.py#L7953) | 노드 메모리가 모자란 상태에서 ECC 실행 파일 자체가 죽을 때 | `CalledProcessError`의 반환 코드와 stderr를 보고 메모리 부족을 판별해 같은 재시도 경로에 태운다 | 3 |
| M-22 | MEDIUM | 코어 속도 측정이 `Run_ECC`의 벽시계 시간을 재므로 errno 12 재시도 대기(최대 600초)가 측정값에 섞인다. 일시적 메모리 부족이 멀쩡한 코어를 영구 제외시킨다(재점검 기본값이 0이라 복구 기회가 없다) | [DAO_Main.py:9044](5_DAO/SRC/DAO_Main.py#L9044), [DAO_Main.py:7950](5_DAO/SRC/DAO_Main.py#L7950) | 속도 테스트 중 한 rank가 메모리 부족으로 재시도할 때 | `Run_ECC`가 재시도 대기 시간을 따로 돌려주게 하고 측정값에서 뺀다. 속도 테스트에서는 재시도 횟수를 0으로 두고 실패를 측정 실패로 다룬다 | 3 |
| M-23 | MEDIUM | `MPI_Abort`가 `NoReturn`으로 선언되었으나 재진입 분기에서 실제로 반환한다. 호출부가 그 뒤 코드를 이어 실행하면 미정의 이름이나 None을 쓴다 | [DAO_Main.py:6807-6811](5_DAO/SRC/DAO_Main.py#L6807), [DAO_Main.py:7988](5_DAO/SRC/DAO_Main.py#L7988), [DAO_Main.py:6966](5_DAO/SRC/DAO_Main.py#L6966) | `comm.Abort`가 즉시 프로세스를 끊지 못하는 런처 설정 | 재진입 경로도 `os._exit(error_code)`로 확실히 끊는다. 값을 돌려주는 함수는 `MPI_Abort` 뒤에 `raise SystemExit(...)`를 명시한다 | 1, 3 |
| M-24 | MEDIUM | 최상위 `Main`이 `Log_Unhandled_Exception`과 `MPI_Abort`로 같은 내용을 두 번 쌓는다. 두 번째 기록의 호출 스택은 예외 발생 지점이 아니라 처리부라서 쓸모가 없다 | [DAO_Main.py:10407](5_DAO/SRC/DAO_Main.py#L10407), [DAO_Main.py:6841](5_DAO/SRC/DAO_Main.py#L6841) | 처리되지 않은 예외가 최상위까지 올라올 때 | `Main`의 처리부는 `Log_Unhandled_Exception`만 부르고, `MPI_Abort`에는 스택 재수집을 건너뛰는 인자를 준다 | 3 |
| M-25 | MEDIUM | 매트릭스와 플래그 파일을 제자리에 직접 쓴다. 중단 시점이 쓰기 도중이면 잘린 최적 매트릭스 파일이나 빈 플래그 파일이 남는다 | [DAO_LLR_MATRIX.py:549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549), [DAO_Main.py:1071](5_DAO/SRC/DAO_Main.py#L1071) | 다른 rank의 `comm.Abort`가 root의 매트릭스 저장 도중에 도달할 때 | `.tmp`로 쓰고 `os.replace`로 바꾸는 방식으로 고친다 | 3 |
| M-26 | MEDIUM | 백업 로그 이름이 (초 단위 생성 시각, 시작 idx, 종료 idx)만으로 정해져 같은 이름이 날 수 있다. POSIX는 이전 백업을 말없이 덮어쓰고 Windows는 `FileExistsError`로 전체 작업을 중단시킨다 | [DAO_Main.py:6638](5_DAO/SRC/DAO_Main.py#L6638), [DAO_Main.py:2182](5_DAO/SRC/DAO_Main.py#L2182) | 매트릭스 idx가 그대로인 채 1초 안에 두 번 회전할 때 | 이름에 일련번호를 더하고, 이미 있으면 번호를 올려 가며 빈 이름을 찾는다 | 3 |
| M-27 | MEDIUM | 중단 처리 중 로그 회전이 실패하면 `Make_Log_Backup`이 `Write_Log_Lines` 안쪽에서 `comm.Abort(1)`을 부른다. 그래서 `MPI_Abort`가 호출 스택 기록 구간에 도달하지 못하고 원인 진단이 사라진다 | [DAO_Main.py:6643](5_DAO/SRC/DAO_Main.py#L6643), [DAO_Main.py:6819](5_DAO/SRC/DAO_Main.py#L6819) | 로그 줄 수가 임계를 넘은 상태에서 중단이 일어나고 rename이 실패할 때 | `_in_mpi_abort`가 참이면 회전을 건너뛰고 그대로 이어 쓴다. 회전 실패는 경고로 남기고 중단시키지 않는다 | 3 |
| M-28 | MEDIUM | 비루트 rank의 경고가 전부 버려진다. `Write_Log_Lines`가 첫 줄에서 반환하므로 uncor 복사 실패, 파일 삭제 실패, ECC 메모리 재시도가 어디에도 남지 않는다 | [DAO_Main.py:9942](5_DAO/SRC/DAO_Main.py#L9942), [DAO_Main.py:959](5_DAO/SRC/DAO_Main.py#L959), [DAO_Main.py:1529](5_DAO/SRC/DAO_Main.py#L1529) | rank 0 외의 코어에서 경고가 날 때 | 비루트 rank의 경고를 `error_logs_{rank}.txt`로 보내는 `Write_Rank_Log_Lines`를 두고 경고 호출부를 이 경로로 바꾼다 | 3 |
| M-29 | MEDIUM | ECC 실행 뒤 고정 `time.sleep(0.5)`가 결과 파일 가시성을 보장하지 못한다. 파일이 없으면 그 rank의 기여분이 0으로 조용히 빠지고 로그도 남지 않는다 | [DAO_Main.py:7942](5_DAO/SRC/DAO_Main.py#L7942), [DAO_Main.py:1852](5_DAO/SRC/DAO_Main.py#L1852) | 느린 저장소나 네트워크 공유에 `local_session_dir`이 있을 때 | 고정 대기를 파일 존재 확인 재시도(짧은 간격, 상한 있음)로 바꾸고, 상한을 넘기면 경고를 남긴다 | 3 |
| M-30 | MEDIUM | `MAX_RUN_ECC_ERRORS`는 이름과 주석이 "RUN_ECC 오류 수"라고 말하지만 실제로는 FER 측정을 끝내는 누적 프레임 오류 목표값이다 | [DAO_Config.py:123](5_DAO/SRC/DAO_Config.py#L123), [DAO_Main.py:8566](5_DAO/SRC/DAO_Main.py#L8566), [DAO_Main.py:1067](5_DAO/SRC/DAO_Main.py#L1067) | 설정을 읽는 사람이 재시도 한도로 오해할 때 | 이름을 `TARGET_FRAME_ERROR_COUNT`처럼 목적을 가리키는 것으로 바꾸고 주석을 다시 쓴다 | 3 |
| M-31 | MEDIUM | `MPI_Abort`가 `comm.Abort` 전에 `inspect.stack()`으로 전 프레임의 지역 변수를 요약해 통신 스레드와의 동시 진입 구간이 길어지고 다른 rank의 대기가 늘어난다 | [DAO_Main.py:6839-6865](5_DAO/SRC/DAO_Main.py#L6839) | 타임아웃으로 중단할 때 | 스택 수집 깊이에 상한을 두고, 요약 도중 예외가 나면 그 프레임을 건너뛰고 이어간다 | 2 |

### LOW (개선 제안)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| M-32 | LOW | `Debug_Pause`의 `while True`가 각 rank의 파일 읽기 결과로 `break` 되고, `break`는 루프 끝의 `MPI_Barrier`를 건너뛴다 | [DAO_Main.py:1370-1386](5_DAO/SRC/DAO_Main.py#L1370) | `DEBUG_CONFIG.ENABLE_FILE_BREAKPOINT=True`로 이 함수를 되살릴 때 (현재 호출처 없음) | root만 파일을 읽고 `_safe_bcast`로 탈출 여부를 내린다. 배리어를 루프 앞 한 곳으로 모은다 | 1, 2 |
| M-33 | LOW | 죽은 코드 세 가지: `_Read_Stop_Idx`와 `MPI_Debug_Logging`은 호출처가 없고, `_Write_Stop_Idx`가 쓴 값을 읽는 곳이 없다. `_Read_Stop_Idx`는 M-02의 올바른 해법이 들어갈 자리를 비워 둔 흔적이다 | [DAO_Main.py:1136](5_DAO/SRC/DAO_Main.py#L1136), [DAO_Main.py:6997](5_DAO/SRC/DAO_Main.py#L6997), [DAO_Main.py:10060](5_DAO/SRC/DAO_Main.py#L10060) | 해당 없음 | M-02를 bcast 방식으로 고치면서 stop idx 파일과 두 함수의 존치를 함께 결정한다. `MPI_Debug_Logging`은 `Check_Barrier_Sync`와 기능이 겹치므로 지운다 | 1, 2 |
| M-34 | LOW | `np.random.seed`가 아무도 쓰지 않는 상태를 심고, 난수 상태 복원 뒤 전 rank의 `random` 스트림이 같아져 재시도 지연 지터가 무력화된다 | [DAO_Main.py:8755](5_DAO/SRC/DAO_Main.py#L8755), [DAO_Main.py:8780](5_DAO/SRC/DAO_Main.py#L8780) | `ENABLE_GET_RANDOM_STATE_FROM_CONFIG=True` | 쓰지 않는 numpy 시드 줄을 지운다. 재시도 지연은 rank 고유 시드를 쓰는 별도 난수 스트림에서 뽑는다 | 2 |
| M-35 | LOW | `active_cores`가 빌 수 없다. root 보호 때문에 `if not active_cores` 세 곳은 도달하지 않고, 정작 위험한 "root 혼자 활성" 상태에는 경고가 없다 | [DAO_Main.py:9063](5_DAO/SRC/DAO_Main.py#L9063), [DAO_Main.py:647](5_DAO/SRC/DAO_Main.py#L647), [DAO_Main.py:1563](5_DAO/SRC/DAO_Main.py#L1563) | 코어 대부분이 제외될 때 | 도달하지 않는 분기를 지우고, 활성 코어가 1개로 줄면 경고를 남긴다 | 3 |
| M-36 | LOW | `Test_Core_Speed`가 `current_seed_mode`를 DEFAULT로 덮어쓰고 복원하지 않는다. 지금은 다음 `Test_LLR`이 다시 정하기 때문에만 안전하다 | [DAO_Main.py:9038](5_DAO/SRC/DAO_Main.py#L9038), [DAO_Main.py:8952](5_DAO/SRC/DAO_Main.py#L8952) | 주기적 재점검이 활성인 상태에서 trial 중간에 속도 테스트가 끼어들 때 | 시작에서 값을 저장하고 끝에서 되돌린다 | 3 |
| M-37 | LOW | `Run_ECC`에 죽은 코드가 둘 있다. `ecc_start`는 쓰이지 않고, `except (..., FileNotFoundError)`의 `FileNotFoundError`는 `OSError` 하위라 위쪽 처리기에서 이미 걸린다 | [DAO_Main.py:7935](5_DAO/SRC/DAO_Main.py#L7935), [DAO_Main.py:7953](5_DAO/SRC/DAO_Main.py#L7953) | 항상 | `ecc_start` 줄을 지우고, 실행 파일 없음을 구분하려면 errno로 판별한다 | 3 |
| M-38 | LOW | `log_line_count`가 전달된 리스트 원소 수만 센다. 줄바꿈을 품은 한 문자열이 파일에는 여러 줄로 들어가므로 실제 파일은 임계를 넘긴 뒤에 회전한다 | [DAO_Main.py:807](5_DAO/SRC/DAO_Main.py#L807), [DAO_Main.py:9925](5_DAO/SRC/DAO_Main.py#L9925) | 앞뒤에 빈 줄을 넣는 호출이 많을 때 | 원소마다 줄바꿈 수에 1을 더해 실제 줄 수를 센다 | 3 |
| M-39 | LOW | 스테이지 시간 제한을 켜는 문턱이 두 자리에서 다르다. `__init__`은 `< SIM_MAX_TIME_OUT`(36000초), `Initialize_Stage`는 `< 100*60*60`(360000초)을 쓴다. 설정 주석은 100시간을 말한다. 10시간에서 100시간 사이 값을 주면 초기값은 제한 꺼짐, 스테이지 시작 뒤에는 제한 켜짐으로 뒤집힌다 | [DAO_Main.py:523](5_DAO/SRC/DAO_Main.py#L523), [DAO_Main.py:2307](5_DAO/SRC/DAO_Main.py#L2307), [DAO_Config.py:320](5_DAO/SRC/DAO_Config.py#L320) | `MAX_STAGE_TIMEOUT_SECONDS`를 10시간에서 100시간 사이로 둘 때 | 두 자리가 같은 상수(`NO_STAGE_TIME_LIMIT_SECONDS`)를 읽게 하고 `TIME_CONFIG`에 정의한다 | 리더 |

---

## ㉯ 팀 내 교차 분석

### 세 워커가 독립으로 같은 결론에 닿은 것 (확정)

- ㉮ **M-01 타임아웃 예산 부족**: 워커 1은 P1의 배리어 짝 맞춤에서, 워커 2는 P2의 타임아웃 값 검토에서, 워커 3은 P5의 재시도 시간 계산에서 각각 출발해 같은 자리에 닿았다. 리더가 [DAO_Main.py:6692](5_DAO/SRC/DAO_Main.py#L6692), [DAO_Config.py:323](5_DAO/SRC/DAO_Config.py#L323), [DAO_Constants.py:144](5_DAO/SRC/DAO_Constants.py#L144)를 직접 확인해 값(3600초 대 36000초)을 검증했다. Round 1 실마리 ㉲(1200초 대 3600초)는 사실이며, 두 값 모두 ECC 실행 상한보다 훨씬 작다는 점이 실마리보다 무겁다
- ㉯ **root 전용 블록 안에 집단 통신이 없음**: 워커 1이 `if self.is_root:` 블록 약 95곳을 전수 스캔하고, 워커 2가 AST 전수 검사로 같은 결론을 냈다. Round 1 관점 P1의 확인 항목 가운데 "root 전용 블록 안의 통신"은 근거가 없다
- ㉰ **`Test_LLR` while 루프 안에 집단 통신이 없음**: 세 워커가 같은 사실을 확인했다. 그래서 반복 횟수가 rank마다 달라도 짝은 깨지지 않으며, 그 차이를 흡수해야 할 것이 M-01의 배리어 타임아웃이다. 워커 2와 3은 같은 사실에서 M-19(바쁜 대기)를 따로 지적했다

### 이견이 있어 리더가 조정한 것

| 항목 | 워커 판단 | 리더 판정과 사유 |
|------|----------|-----------------|
| 타임아웃 없는 집단 통신 3곳 | 워커 1은 세 자리를 묶어 HIGH, 워커 2는 [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049)만 CRITICAL이고 나머지는 낮음, 워커 3은 세 자리를 묶어 MEDIUM | **자리별로 나눈다**. 리더가 코드를 확인한 결과 [DAO_Main.py:1840](5_DAO/SRC/DAO_Main.py#L1840)에 배리어가 있어 [DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861)의 Reduce는 이미 맞춰진 rank끼리 만난다(M-11 MEDIUM). [DAO_Main.py:7011](5_DAO/SRC/DAO_Main.py#L7011)은 `MPI_Debug_Logging` 안이고 grep으로 호출처가 없음을 확인했다(M-33 LOW). [DAO_Main.py:9049](5_DAO/SRC/DAO_Main.py#L9049)는 `Run_ECC` 직후이고 앞에 배리어가 없어 rank 편차가 가장 크므로 워커 2의 CRITICAL을 채택한다(M-04) |
| GEN_SINGLE_ROW 종료 플래그 | 워커 1은 CRITICAL, 워커 2는 HIGH | **CRITICAL**. 결과가 hang이므로 심각도 기준의 CRITICAL 정의에 든다. 다만 워커 1이 "반드시 갈린다"고 쓴 것은 과하다. 갈리려면 파일 쓰기와 읽기가 겹쳐야 하므로 재현 조건을 경쟁 조건으로 적었다 |
| MPI 스레드 지원 수준 | 워커 1과 3은 MEDIUM, 워커 2는 HIGH | **MEDIUM**. 워커 2가 로컬 환경(MS MPI 10.1, mpi4py 4.1.1)에서 `Query_thread()`가 MULTIPLE을 돌려주는 것을 실측했다. 실행 클러스터는 이 환경에서 확인할 수 없으므로 위험은 남지만 즉시 결함은 아니다. 워커 2의 처방(시작 시 점검 한 줄)은 그대로 채택한다 |
| `MPI_Abort`의 `NoReturn` 불일치 | 워커 1은 LOW, 워커 3은 MEDIUM | **MEDIUM**. 워커 3이 복귀가 일어났을 때 실제로 깨지는 호출부 두 곳([DAO_Main.py:7988](5_DAO/SRC/DAO_Main.py#L7988), [DAO_Main.py:6966](5_DAO/SRC/DAO_Main.py#L6966))을 짚었다. 근거가 더 구체적인 쪽을 따른다 |
| `_Redistribute_Uncor_Pool_Uniform` 소스 부재 | 워커 3은 HIGH | **CRITICAL**. 종착지가 `total_tests=0`의 `MPI_Abort`(전체 중단)이므로 심각도 기준상 CRITICAL이다. 재현 조건이 엣지케이스라는 점은 표에 적었다 |

### 한 워커의 발견이 다른 워커에게 반박되지 않고 보강된 것

- ㉮ **M-03과 M-05는 서로 다른 경로가 같은 종착지로 간다**: 워커 1은 Partial pool 고갈에서, 워커 3은 재분배 실패에서 출발했는데 둘 다 [DAO_Main.py:1884](5_DAO/SRC/DAO_Main.py#L1884)의 `total_tests=0` 중단으로 끝난다. 반박이 아니라 같은 중단 지점을 두 방향에서 짚은 것이다. 처방은 다르므로 둘 다 남기고, 그 중단 메시지가 원인을 구분하지 못한다는 공통 문제를 M-03 처방에 덧붙였다
- ㉯ **워커 2의 M-06(ack 판정)은 워커 1의 P3 경로 추적과 어긋나지 않는다**: 워커 1은 통신 짝만 보았고 ack는 통신이 아니라 파일이라 짝에 영향이 없다. 두 관찰이 같은 자리를 다르게 판단한 것이 아니다

### 워커가 확인해 기각한 Round 1 관점

- ㉮ `Gather_Ref_C_Results`의 제외 기준 두 가지(root의 `excluded_cores` 목록과 각 rank의 `is_current_core_excluded`)가 다르다는 Round 1 관찰은 **사실이 아니다**. 워커 1과 워커 3이 각각 [DAO_Main.py:9087-9088](5_DAO/SRC/DAO_Main.py#L9087)에서 두 값이 한 줄 차이로 함께 정해지는 것을 확인했다
- ㉯ `Is_Current_LLR_Valid`가 rank마다 갈릴 수 있다는 관찰도 **사실이 아니다**. bcast된 같은 매트릭스만 보는 순수 함수다
- ㉰ 종료 플래그와 ack, 중단 인덱스 파일은 모두 세션 디렉토리 아래라 세션 사이 오염이 없다(`Debug_Pause`의 `debug.txt`만 예외이며 호출처가 없다). `Set_Test_Environment`와 `Initialize_End_Flags`의 플래그 초기화는 배리어 사이에 제대로 놓여 있다
- ㉱ 숫자 카운트 파일의 비정상 내용과 잘린 읽기는 0으로 안전하게 처리되고, trial 종료 카운트 감소는 stage당 1회라 재진입 문제가 없다
- ㉲ rank별 시드는 한 세션 안에서 rank 수가 얼마든 겹치지 않는다(간격 10000 고정). 매트릭스 생성은 전부 root 블록 안이고 bcast되므로 worker의 난수 사용으로 rank 사이 매트릭스가 갈리지 않는다. `np.random`은 시드만 심고 값을 뽑는 곳이 없어 `random`만 복원해도 현재 코드에서는 충분하다
- ㉳ `except Exception` 약 20곳을 워커 3이 전수 확인했고, 삼킨 뒤 상태가 깨지는 곳은 없었다. 로그 회전 재진입은 1회로 끝난다

### Round 1 실마리 판정

| 실마리 | 판정 | 대응 발견 |
|--------|------|----------|
| ㉱ Reduce와 allgather 타임아웃 미적용 | 사실. 세 자리 모두 확인했고 위험도는 자리마다 다르다 | M-04 (CRITICAL), M-11 (MEDIUM), M-33 (LOW) |
| ㉲ 타임아웃 값 1200초 대 3600초 | 사실이며 실마리보다 무겁다. 두 값 모두 `SIM_MAX_TIME_OUT` 36000초보다 훨씬 작다 | M-01 (CRITICAL), M-17 (MEDIUM) |

---

## ㉰ 미커버 영역

- ㉮ **실행 환경의 MPI 스레드 지원 수준**: 이 환경에서는 로컬 설치본만 확인할 수 있었다. 실제 실행 클러스터의 MPI 빌드가 `MPI_THREAD_MULTIPLE`을 제공하는지는 외부에서 확인해야 한다 (M-08)
- ㉯ **`Rebuild_Partial_Pool`의 상태 복원 자체**: 워커 1은 이 함수의 통신 짝만 확인했다. 상태 복원과 재진입은 관점 P8이라 팀 T 담당이다
- ㉰ **GEN_SINGLE_ROW의 Top-K 저장과 결과 집계 정확성**: M-13(루프 안 결과 집계 누락)은 관점 P18(팀 L)과 P4(팀 T)에 걸친다. 팀 M은 통신과 종료 신호 쪽만 보았으므로 두 팀이 결과 정확성 쪽을 이어서 보면 좋다
- ㉱ **매트릭스 파일 제자리 쓰기(M-25)**: uncor와 매트릭스 파일 입출력 전반은 관점 P9(팀 T)와 겹친다. 팀 M은 중단 시점의 잘린 파일만 짚었다
- ㉲ **이름과 실제 의미 불일치(M-30)**: `MAX_RUN_ECC_ERRORS` 건은 가독성 관점 R3(이름 규약)과 겹치므로 팀 R의 이름 정리 처방과 묶어 다루는 편이 낫다
- ㉳ **실행 검증**: 이 환경에서는 MPI 실행을 하지 않으므로 모든 발견은 코드 정독 결과다. M-01, M-04, M-05는 실제 hang이나 중단을 재현해 확인하는 것이 바람직하다
