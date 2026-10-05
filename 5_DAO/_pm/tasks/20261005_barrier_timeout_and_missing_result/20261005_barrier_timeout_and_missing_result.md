# 배리어 타임아웃이 도착하지 않은 rank를 적고, ECC를 돌린 rank의 result가 없으면 멈춤

> 작성: 2026-10-05
> 등급: Review (타임아웃 메시지와 진단 기록 추가, 집계 단계의 중단 조건 추가)
> 출처: 사용자 관측 2건 (2026-10-05)

이 문서에서 rank는 MPI 프로세스 번호(`Process_N` 폴더의 N)이고, 집단 통신은 배리어, bcast, gather처럼 모든 rank가 함께 불러야 끝나는 MPI 통신이다.

## 1. 목적

- ㉮ 집단 통신이 대기 상한에 닿아 끝날 때, 도착하지 않은 rank가 메시지에 적히게 한다
- ㉯ ECC를 돌린 rank가 쓸 수 있는 result 파일을 남기지 못하면 그 채널 테스트의 집계에서 멈추게 한다

## 2. 배경 (현상)

### 2.1 배리어 타임아웃

- ㉮ 타임아웃 문구는 `MPI_Barrier[N] timed out after 37800 seconds`뿐이고, 앞의 `[Rank X]`는 가장 먼저 배리어에 들어가 기다리던 rank다. 도착하지 않은 rank는 어디에도 적히지 않는다
- ㉯ `Write_Log_Lines`는 root에서만 쓴다. root가 아닌 rank가 먼저 대기 상한에 닿으면 그 rank가 전체를 종료시켜 메인 로그에는 타임아웃 줄이 남지 않는다. 남는 곳은 콘솔과 `6_Error_Log/error_logs_{rank}.txt`다
- ㉰ 미응답 rank를 적는 `_Report_Missing_Acks`는 테스트 종료 집계의 배리어를 지난 뒤에 불리므로, 그 배리어에서 타임아웃이 나면 실행되지 않는다
- ㉱ 재현 (rank 4개, rank 2가 오지 않음, 대기 상한 5초)

| 먼저 들어간 rank | 메인 로그 | `6_Error_Log` | rank 2 언급 |
|------------------|-----------|---------------|-------------|
| rank 0 | `[Rank 0] MPI_Abort: MPI_Barrier[1] timed out after 5 seconds.` | `error_logs_0.txt` | 없음 |
| rank 3 | 타임아웃 줄 없음 | `error_logs_3.txt` | 없음 |

### 2.2 result 파일이 없는 rank

- ㉮ 테스트 종료 집계(`Gather_Ref_C_Results`의 `is_test_end=True`)에서 각 rank는 자기 result 파일을 읽고, 파일이 없으면 테스트 0회와 실패 0회로 합산에 들어간다. 경고는 없다
- ㉯ 쓰다 만 파일은 `Read_Ref_C_Result`가 3번 다시 읽은 뒤 0건으로 돌려준다. 경고 문구는 root만 쓸 수 있어 다른 rank의 경고는 남지 않는다
- ㉰ 중단은 전체 합계가 0일 때뿐이다. 모은 테스트 수를 기대값과 견주는 곳은 없다
- ㉱ result가 없는 것이 정상인 rank: 속도 테스트로 제외된 코어, uncor를 불러오는 모드에서 배정받은 uncor가 없는 rank, 종료 플래그를 먼저 읽어 ECC를 돌리지 않은 rank
- ㉲ 재현 (rank 4개, rank당 1000회, rank 2만 실패 500회, 나머지는 10회)

| rank 2의 result | 집계 | FER | 경고 |
|-----------------|------|-----|------|
| 정상 | 530/4000 | 0.1325 | 없음 |
| 파일 없음 | 30/3000 | 0.0100 | 없음 |
| 쓰다 만 줄 | 30/3000 | 0.0100 | 없음 |

## 3. 설계

### 3.1 대기 기록과 타임아웃 메시지

- ㉮ `_mpi_comm_with_timeout`에서 `TIME_CONFIG.MPI_WAIT_RECORD_DELAY_SECONDS`(기본 60초) 넘게 기다린 rank는 `8_End_flag/mpi_wait/mpi_wait_rank{N}.txt`에 통신 이름과 기다리기 시작한 시각을 쓴다. 통신이 끝나면 그 파일을 지운다
- ㉯ 대기 상한에 닿은 rank는 모든 rank의 대기 기록을 읽어 메시지에 붙인다
  - ㉠ 기록의 통신 이름이 자기와 같으면 함께 기다리던 rank (`Ranks waiting in this call`)
  - ㉡ 기록의 통신 이름이 다르면 다른 통신에서 기다리는 rank (`rank K (waiting in X since T)`)
  - ㉢ 기록이 없으면 MPI 통신 밖에서 실행 중이거나 멈춘 rank (`rank K (no wait record)`)
- ㉰ `MPI_Barrier`는 통신 이름에 부른 함수 이름을 넣는다 (`MPI_Barrier[N] called from {함수}`). 배리어 번호 N은 모든 rank에서 같으므로 같은 배리어인지 이름으로 가릴 수 있다
- ㉱ 60초 안에 끝나는 통신은 파일을 쓰지 않는다. 오래 기다리는 통신 하나에 rank당 쓰기 1회와 지우기 1회가 든다
- ㉲ 대기 기록 파일의 쓰기와 지우기가 실패하면 `_write_error_log`에만 남기고 실행을 잇는다 (진단용 기록)
- ㉳ 메시지 예

```
[Rank 0] MPI_Abort: MPI_Barrier[12] called from Gather_Ref_C_Results timed out after 37800 seconds. This usually indicates a deadlock or network issue. Ranks not waiting in this call: rank 2 (no wait record). Ranks waiting in this call: 0, 1, 3.
```

### 3.2 result 파일 확인

- ㉮ `is_result_file_expected`는 이번 채널 테스트에서 ECC를 돌렸는지를 담는다. `Set_Test_Environment`가 False로 두고, `Run_ECC`가 ECC 실행을 마치면 True로 둔다
- ㉯ 테스트 종료 집계에서 각 rank는 자기 result 파일의 문제를 정한다. 파일이 없으면 `RESULT_FILE_MISSING`, 읽은 테스트 수가 0이면 `RESULT_FILE_UNREADABLE`, `is_result_file_expected`가 False이면 문제 없음이다
- ㉰ 문제를 gather로 root에 모으고, 하나라도 있으면 root가 `MPI_Abort`로 멈춘다. root가 멈추므로 메시지가 메인 로그에 남는다 (사용자 결정 2026-10-05: 경고만 남기기, trial 버리기, 멈추기 가운데 멈추기)
- ㉱ 메시지 예

```
[Rank 0] MPI_Abort: Gather_Ref_C_Results: ranks that ran ECC but left no usable result file for ch_idx=0. Missing file: rank 2. Unreadable or empty file: none. First one: {세션 폴더}/Process_2/result_4KB_S_1_H_1_CH_2_E100_init_n_4_seed_2.txt
```

- ㉲ 테스트 도중 root가 다른 rank의 result를 읽는 집계(`is_test_end=False`)는 그대로다. 그 시점에는 아직 첫 ECC를 끝내지 못한 rank가 있다

## 4. 수정 대상 파일

- `SRC/DAO_Main.py`: `MPI_Barrier`, `_mpi_comm_with_timeout`, 대기 기록 함수 5개(`_Get_MPI_Wait_Record_Path`, `_Write_MPI_Wait_Record`, `_Delete_MPI_Wait_Record`, `_Read_MPI_Wait_Record`, `_Describe_Ranks_Not_Waiting_In_Call`), `Set_Test_Environment`, `Run_ECC`, `Gather_Ref_C_Results`
- `SRC/DAO_Config.py`: `TIME_CONFIG.MPI_WAIT_RECORD_DELAY_SECONDS`
- `SRC/DAO_Constants.py`: `MPI_WAIT_RECORD_DIR_NAME`, `MPI_WAIT_RECORD_FILE_TEMPLATE`, `RESULT_FILE_MISSING`, `RESULT_FILE_UNREADABLE`
- `README.md`: TIME_CONFIG 두 곳, 부록 A의 에러 메시지 표와 「집단 통신 타임아웃 메시지 읽는 법」
- `DAO_spec.md`: 6.1절 공통 예외 케이스

## 5. 안전성 체크리스트

- ㉮ 집단 통신 대칭: 새 gather(`Gather_result_file_problems`)는 테스트 종료 집계에서 모든 rank가 한 번씩 부른다. 호출처 두 곳(`Test_LLR`, GEN_SINGLE_ROW 실행)이 모두 `Set_Test_Environment` 뒤에 `Run_ECC`와 집계를 부른다
- ㉯ 잘못된 중단 방지: ECC를 돌리지 않은 rank(제외된 코어, uncor 없는 rank, 종료 플래그를 먼저 읽은 rank)는 `is_result_file_expected`가 False라 대상에서 빠진다. `Set_Test_Environment`가 채널 테스트마다 False로 되돌린다
- ㉰ uncor를 받은 rank는 uncor가 1개 이상이다 (`Distribute_Uncors_To_Local_Session`과 `_Setup_Uncor_Pool_For_Channel`이 1개 이상 배정한 rank만 True로 둠). 그래서 ECC를 돌린 rank의 테스트 수는 1 이상이어야 한다
- ㉱ 정상 경로의 부담: 60초 안에 끝나는 통신에는 파일 입출력이 없다
- ㉲ 대기 기록은 세션 폴더(`8_End_flag`) 아래에 두므로 세션끼리 섞이지 않는다

## 6. 검증

- ㉮ 검사 위치: `_test/20261005_DAO_barrier_timeout_and_missing_result/` (rank 4개를 mpiexec으로 띄워 `LLR_OPT`의 메서드를 그대로 부름)
- ㉯ 새 검사 10건: 수정 전 소스에서 6건 실패(타임아웃 메시지 3건, 대기 기록 1건, result 없음과 읽기 실패 2건), 수정 뒤 10건 통과
- ㉰ `Set_Test_Environment`의 초기화 줄을 뺀 소스에서는 「앞 테스트에서 ECC를 돌리고 이번에는 돌리지 않은 rank」 검사가 실패함을 확인
- ㉱ 기존 5_DAO 검사 163건 통과

## 7. 미결정 사항과 남은 확인

- ㉮ 사용자 환경 MPI 실행 확인
  - ㉠ 정상 실행에서 `ranks that ran ECC but left no usable result file` 중단이 나오지 않는지
  - ㉡ 오래 기다리는 동안 `8_End_flag/mpi_wait/`에 기다리는 rank의 파일이 생기고, 통신이 끝나면 없어지는지
- ㉯ 지난 테스트의 result 파일이 지워지지 않고 남았을 때 다음 테스트의 집계에 섞이는 경우는 이 작업의 범위 밖이다 (`Cleanup_Test_Environment`의 삭제 실패는 root의 경고로만 남는다)
