# RowStack: uncor 하나씩 row를 쌓아 고치는 LLR matrix 탐색기

기존 LLR matrix로 고쳐지지 않는 uncor(디코더가 최대 iteration 안에 고치지 못한 프레임)를 모은 뒤, uncor 하나마다
그룹 1개, iteration 1-50짜리 작은 LLR matrix를 row 하나씩 쌓아 가며 그 uncor를 고치는 매트릭스를 찾는다.
모든 rank(MPI 프로세스)가 같은 uncor 하나를 놓고 서로 다른 후보 row를 시험하고, root(rank 0)가 iteration 중
잔여 에러 bit 수가 가장 작았던 후보를 골라 고정한다. 새 uncor는 먼저 이미 찾은 매트릭스들로 복호해 보고,
모두 실패할 때만 새로 찾는다. 디코더는 `2_LDPC_base/src`의 Python 디코더다 (상대 비교 전용이라 Ref-C와
bit 단위로 같지 않다).

설계와 결정 기록: `../_pm/tasks/20261021_uncor별_row누적_탐색/` (설계 문서, 판정요청, 구현 계획)

## 실행

```bat
run_RowStack_mpi.bat                      :: mpiexec -n 4 python RowStack_Main.py
mpiexec -n 8 python RowStack_Main.py      :: rank 수를 바꿀 때
```

설정은 `RowStack_Config.py` 끝의 `CONFIG = RowStackConfig()` 자리에서 값을 넣는다 (예:
`CONFIG = RowStackConfig(INITIAL_LLR_MATRIX_FILE="LLR_MATRIX_HD_matrix_sel_1.txt", CHANNEL_POINT=390)`).
입력 파일은 `2_LDPC_base/Input/H_matrix/`와 `2_LDPC_base/Input/LLR/`에서 이름으로 찾고, LLR 파일 이름의
HD/2SD/3SD가 복호 모드다. 의존 패키지는 numpy, mpi4py (MS-MPI).

## 설정값

| 이름 | 기본값 | 뜻 |
|------|--------|-----|
| `H_MATRIX_FILE` | example_18x147_z256.qc | H-matrix 파일 이름 |
| `INITIAL_LLR_MATRIX_FILE` | LLR_MATRIX_HD_1.txt | uncor를 모을 때 쓰는 기존 매트릭스 (DAO 형식) |
| `CHANNEL_TYPE`, `CHANNEL_POINT` | fixed_error, 400 | 채널 종류와 값 (fixed_error와 strong_error는 프레임당 에러 bit 수, rber는 RBER) |
| `STRONG_SCR`, `STRONG_SER` | 0.94, 0.23 | strong_error일 때만 |
| `NUM_UNCORS_TO_COLLECT` | 100 | 모을 uncor 수 K |
| `COLLECT_MAX_FRAMES` | 1,000,000 | 모으기에서 돌릴 프레임 상한 (rank 전체 합) |
| `COLLECT_FRAMES_PER_BATCH` | 64 | 모으기 배치 크기 |
| `UNCOR_SEED_DIR` | None | 지난 실행의 `collected_uncors/` 폴더를 주면 모으기를 건너뛴다 (채널 설정이 다르면 멈춤) |
| `MAX_ITERATION_OF_STACKED_GROUP` | 50 | 쌓는 그룹의 iteration 수 |
| `CANDIDATES_PER_RANK_PER_STAGE` | 20 | n, 작은 반복 (stage마다 rank당 후보 수) |
| `MAX_ROWS` | 6 | stage 수 상한 (row 수 상한) |
| `MUTANTS_PER_RANK_PER_FIXED_ROW` | 10 | row를 고정한 직후 rank마다 시험하는 변이 후보 수 (0이면 변이 없음) |
| `MUTATION_NUM_ELEMENTS`, `MUTATION_RANGE` | 3, 5 | 변이에서 바꾸는 CH/TH 원소 수와 폭 |
| `MAX_MATRIX_ATTEMPTS_PER_UNCOR` | 1 | 큰 반복 (row 상한까지 실패하면 row 1부터 새 난수로 다시 시작하는 횟수) |
| `TRY_FOUND_MATRICES_FIRST` | True | 새 uncor를 먼저 찾은 매트릭스들로 복호해 보는지 |
| `RANDOM_SEED` | 0 | 후보 생성 난수의 뿌리 (같은 설정과 값이면 결과가 같다) |
| `SAVE_TESTED_MATRICES` | True | 시험한 후보 매트릭스를 `tested_matrices/rank_N/`에 DAO 형식 파일로 남긴다 (후보 수만큼 파일이 생기므로 많으면 끈다) |
| `OUTPUT_ROOT` | 5_DAO/Output_RowStack | 세션 폴더가 생기는 곳 |

## 동작 규칙

- ㉮ row 1의 CSW 문턱은 -1이다 (CSW가 어느 문턱에도 들지 않을 때 쓰는 row). row k(k ≥ 2)의 문턱은 고정된 row들이
  최소 잔여 에러에 닿은 iteration의 CSW를 8의 배수로 올린 값이고, 앞 row의 문턱보다 8 이상 작으며, 초기 CSW와
  그 앞 iteration들의 CSW가 모두 그 값보다 커야 한다 (그래야 새 row가 정확히 그 다음 iteration부터 이어받는다).
  그 값을 쓸 수 없으면 조건을 만족하는 iteration 가운데 잔여 에러가 가장 작은 것의 CSW를 쓰고, 그마저 없으면
  그 uncor는 `no reachable CSW threshold`로 실패 처리한다
- ㉯ 새 row를 붙인 최고 후보가 고정된 row들만으로 복호한 결과보다 나쁘면 그 row를 고정하지 않고
  `no improving candidate`로 실패 처리한다 (고정된 row들만의 매트릭스가 더 낫기 때문)
- ㉰ 후보 순위: 성공이 먼저(성공 iteration이 빠른 쪽), 실패끼리는 최소 잔여 에러 bit 수, 같으면 그때 CSW, 같으면
  그 iteration이 빠른 쪽. rank 사이 동점은 rank 번호가 작은 쪽
- ㉱ row를 고정한 직후 변이 블록을 한 번 돈다. rank마다 변이 후보 m개를 시험하고 root가 최고를 골라 지금 row보다
  좋을 때만 교체한다
- ㉲ 어느 시험에서든 uncor가 고쳐지면 그 자리에서 성공으로 끝낸다. row 상한까지 성공이 없으면 큰 반복 횟수만큼
  row 1부터 다시 시작하고, 다 쓰면 실패로 적는다
- ㉳ 찾은 매트릭스 먼저 시험: 고친 uncor 수가 많은 매트릭스부터 rank마다 나눠 시험하고, 여럿이 고치면 고친 수가
  많은 쪽에 적는다. 실패한 uncor의 매트릭스는 목록에 넣지 않는다

## 출력 폴더

```
Output_RowStack/{YYYYMMDD_HHMMSS}/
├── result.txt                   # root의 중요 결과만: 설정 머리글, uncor 모은 수, uncor마다 한 줄(SUCCESS, REUSED, FAIL), 마지막 집계
├── log.txt                      # root의 상세 로그: 머리글, uncor마다 구분선과 stage별 최고 후보, 결과 줄
├── rank_logs/rank_{N}.txt       # rank마다 자기 후보 하나하나의 결과 (min_err, iteration, CSW, 성공 여부, 시간, 매트릭스 파일 이름)
├── tested_matrices/rank_{N}/LLR_MATRIX_{모드}_seed{seed}_attempt{a}_stage{s}_{gen|mut}{번호}.txt   # 그 후보로 시험한 매트릭스 (SAVE_TESTED_MATRICES)
├── config_used.py               # 실행에 쓴 RowStack_Config.py 사본
├── collected_uncors/            # uncor_seeds.txt (한 줄에 seed 하나), info.json (채널 설정, 모은 수, 돌린 프레임 수), 기존 매트릭스 사본
├── history.csv                  # seed, attempt, stage, kind(gen/mut/pool), threshold, source_iteration, takeover_iteration, best_rank,
│                                #   min_err, min_err_iteration, csw_at_min_err, corrected(uncor가 고쳐졌는지), corrected_iteration, replaced, elapsed_sec, note
├── per_uncor/seed_{seed}/LLR_MATRIX_{모드}_uncor_{seed}.txt   # 성공이면 고치는 매트릭스, 실패면 마지막 stage의 매트릭스
├── summary.csv                  # seed, result(success/reused/fail), num_rows, final_min_err, matrix_file, elapsed_sec, fail_reason
└── found_matrices.csv           # matrix_file, origin_seed, num_fixed, fixed_seeds
```

어느 rank에서든 예외가 나면 traceback을 찍고 `MPI_Abort`로 모든 rank를 멈춘다 (한 rank만 죽어 나머지가 기다리는 일을 막는다).

seed는 `numpy.random.default_rng(seed)`로 프레임을 다시 만드는 정수다. 같은 seed와 같은 채널 설정이면 같은 프레임이다.

## 코드 구성

| 파일 | 책임 |
|------|------|
| `RowStack_Config.py` | 경로 상수, `RowStackConfig`, `CONFIG` |
| `RowStack_Matrix.py` | 템플릿, `StackedRow`, 값 규칙, 난수 row와 변이, 2_LDPC_base `LLRMatrix` 변환과 DAO 형식 저장, CSW 문턱 규칙 |
| `RowStack_Evaluate.py` | 후보 평가 결과 `CandidateResult`, 순위 키, `UncorDecoder` (디코더 호출 한 곳) |
| `RowStack_Parallel.py` | `SerialParallel`, `MpiParallel`, round robin 나누기 |
| `RowStack_Uncor.py` | uncor seed 파일과 info.json, 설정 대조, 실패 seed 추리기 |
| `RowStack_Report.py` | history, summary, found_matrices csv와 root 로그 |
| `RowStack_Main.py` | MPI 흐름 (`run`, `RowStackSession`, `collect_uncors`) |

## 검사

저장소 루트에서 `python -m pytest 5_DAO/_test/20261021_RowStack -q` (단일 프로세스, 가짜 평가기 포함)과
`python -m pytest 2_LDPC_base/_test/20261021_seed_channel -q` (seed 채널과 복호 함수). mpiexec 확인은
`mpiexec -n 2 python 5_DAO/_test/20261021_RowStack/smoke_run.py`.
