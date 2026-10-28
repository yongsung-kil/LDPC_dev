# RowStack: uncor 하나씩 row를 쌓아 고치는 LLR matrix 탐색기

기존 LLR matrix로 고쳐지지 않는 uncor(디코더가 최대 iteration 안에 고치지 못한 프레임)를 모은 뒤, uncor 하나마다
그룹 1개짜리 작은 LLR matrix를 row 하나씩 쌓아 가며 그 uncor를 고치는 매트릭스를 찾는다. 모든 rank(MPI 프로세스)가
같은 uncor 하나를 놓고 서로 다른 후보 row를 시험하고, root(rank 0)가 결과를 모아 부모보다 BER(iteration 중 최소 잔여
에러 bit 수)이 실제로 줄어든 변형만 남긴다. 한 번에 상위 t개의 매트릭스 후보를 함께 키우고, row가 늘수록 복호 iteration
예산을 늘린다. 새 uncor는 먼저 이미 찾은 매트릭스들로 복호해 보고, 모두 실패할 때만 새로 찾는다. 디코더는
`2_LDPC_base/src`의 Python 디코더다 (상대 비교 전용이라 Ref-C와 bit 단위로 같지 않다).

설계와 결정 기록: `../_pm/tasks/20261021_uncor별_row누적_탐색/` (1판 설계, 판정요청, 구현 계획, 탐색 규칙 2판)

## 실행

```bat
run_RowStack_mpi.bat                      :: mpiexec -n 4 python RowStack_Main.py
mpiexec -n 8 python RowStack_Main.py      :: rank 수를 바꿀 때
python RowStack_Main.py                   :: 단일 프로세스 (mpi4py가 rank 1개로 돈다)
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
| `COLLECT_MAX_FRAMES` | 1000000 | 모으기에서 돌릴 프레임 상한 (rank 전체 합) |
| `COLLECT_FRAMES_PER_BATCH` | 64 | 모으기 배치 크기 |
| `UNCOR_SEED_DIR` | None | 지난 실행의 `collected_uncors/` 폴더를 주면 모으기를 건너뛴다 (채널 설정이 다르면 멈춤) |
| `MAX_ROWS` | 6 | row 수 상한 (stage 수 상한) |
| `NUM_MATRICES_TO_KEEP` | 3 | t. round마다 들고 가는 매트릭스 후보 수 (gen과 mut 공통) |
| `CANDIDATES_PER_RANK_PER_BLOCK` | 20 | n. gen 블록에서 rank마다 만드는 후보 row 수 |
| `MAX_GEN_BLOCKS_PER_ROW` | 3 | k_gen. 개선이 없을 때 gen 블록을 다시 도는 상한 (매트릭스 후보마다 최소 n, 최대 k_gen × n회) |
| `MUTANTS_PER_RANK_PER_BLOCK` | 10 | m. mut 블록에서 rank마다 만드는 변이 수 (0이면 변이 없음) |
| `MAX_MUT_BLOCKS_PER_ROW` | 2 | k_mut. 개선이 없을 때 mut 블록을 다시 도는 상한 |
| `MUTATION_NUM_ELEMENTS`, `MUTATION_RANGE` | 3, 5 | 변이에서 바꾸는 CH/TH 자리 수(매트릭스 전체에서 고름)와 폭 |
| `INIT_DECODING_ITERATION` | 30 | 첫 row의 복호 iteration 수 |
| `STEP_ITERATION_PER_ROW` | 5 | row가 하나 붙을 때마다 더하는 iteration 수 |
| `MAX_DECODING_ITERATION` | 50 | 복호 iteration 상한 (HW 제약) |
| `CSW_MARGIN_ABOVE_MIN` | 32 | 새 row 문턱을 부모 궤적의 최소 CSW보다 얼마나 위에 두는지 (CSW 단위) |
| `MAX_MATRIX_ATTEMPTS_PER_UNCOR` | 1 | 큰 반복 (후보가 모두 끝나면 빈 매트릭스부터 다시 시작하는 횟수) |
| `TRY_FOUND_MATRICES_FIRST` | True | 새 uncor를 먼저 찾은 매트릭스들로 복호해 보는지 |
| `RANDOM_SEED` | 0 | 후보 생성 난수의 뿌리 (같은 설정과 값이면 결과가 같다) |
| `SAVE_TESTED_MATRICES` | True | 시험한 후보 매트릭스를 `tested_matrices/rank_N/`에 DAO 형식 파일로 남긴다 (후보 수만큼 파일이 생기므로 많으면 끈다) |
| `OUTPUT_ROOT` | 5_DAO/Output_RowStack | 세션 폴더가 생기는 곳 |

## 동작 규칙 (탐색 규칙 2판)

- ㉮ **round**: stage마다 gen round(row 추가)와 mut round(변이)가 차례로 온다. 들고 가는 매트릭스 후보는 처음에 빈 매트릭스
  하나이고, 빈 매트릭스의 성능은 받은 프레임 자체(에러 bit 수, 초기 CSW)다
- ㉯ **블록과 반복**: 후보 하나에 대해 rank마다 후보 row n개(gen) 또는 변이 m개(mut)를 시험하는 것이 블록 하나다. 블록이 끝나면
  root가 rank마다 보낸 "개선된 변형"(부모보다 BER이 실제로 작아진 것. 같으면 개선이 아님)을 모은다. 하나도 없으면 같은 블록을
  다시 돌고, 상한(k_gen, k_mut)까지 없으면 그 후보의 이번 round는 끝이다. 복호 성공이 나와도 블록은 n개를 다 돈다
- ㉰ **선별**: gen round가 끝나면 모든 후보의 개선된 변형을 한데 모아 순위 상위 t개를 고른다 (어느 부모에서 왔는지는 상관없다).
  순위는 복호 성공이 먼저(성공끼리는 고친 iteration이 빠른 쪽), 실패끼리는 최소 잔여 에러 bit 수, 같으면 그때 CSW, 같으면 그
  iteration이 빠른 쪽이다. 개선된 변형이 하나도 없으면 이 시도는 `no improving candidate`로 끝난다
- ㉱ **변이**: 살아남은 후보마다 매트릭스 전체의 CH, TH에서 자리를 골라 변이한 뒤, 개선된 변형 가운데 최고 1개로 바꾼다.
  개선이 없으면 변이 전 상태 그대로 다음 stage로 간다. CSW 문턱과 iteration은 그대로다
- ㉲ **성공**: mut round 뒤 살아남은 후보에 복호 성공이 있으면 고친 iteration이 가장 빠른 것을 저장하고 이 uncor를 끝낸다
- ㉳ **iteration 예산**: row가 r개인 매트릭스는 `min(MAX_DECODING_ITERATION, INIT_DECODING_ITERATION + (r - 1) × STEP_ITERATION_PER_ROW)`
  iteration으로 복호한다
- ㉴ **새 row의 문턱**: 첫 row는 -1 (CSW가 어느 문턱에도 들지 않을 때 쓰는 row). 그 뒤 row의 문턱은 부모 궤적의 최소 CSW에
  `CSW_MARGIN_ABOVE_MIN`을 더해 8의 배수로 올린 값이고, 앞 row 문턱보다 8 이상 작게(크면 내림), 초기 CSW보다 작게 둔다.
  새 row는 궤적에서 CSW가 처음 문턱 이하가 되는 iteration의 다음부터 이어받으며 그 iteration이 새 예산 안이어야 한다.
  그런 문턱이 없는 후보는 row를 더 붙일 수 없어 끝난다 (`no reachable CSW threshold`)
- ㉵ **찾은 매트릭스 먼저 시험**: 고친 uncor 수가 많은 매트릭스부터 rank마다 나눠 시험하고, 여럿이 고치면 고친 수가 많은 쪽에
  적는다. 실패한 uncor의 매트릭스는 목록에 넣지 않는다
- ㉶ rank 사이 동점은 rank 번호, 그 다음 후보 번호가 작은 쪽이 앞선다. 단일 프로세스로 돌리면 블록마다 n개(또는 m개)만 시험한다

## 출력 폴더

```
Output_RowStack/{YYYYMMDD_HHMMSS}/
├── result.txt                   # root의 중요 결과만: 설정 머리글, uncor 모은 수, uncor마다 한 줄(SUCCESS, REUSED, FAIL), 마지막 집계
├── log.txt                      # root의 상세 로그: 머리글, uncor마다 구분선, 블록마다 한 줄, round마다 살아남은 후보 목록, 결과 줄
├── rank_logs/rank_{N}.txt       # rank마다 블록 머리줄(부모 성능 포함), 후보 하나하나의 결과, 블록의 전체 결과
├── tested_matrices/rank_{N}/LLR_MATRIX_{모드}_seed{seed}_attempt{a}_stage{s}_c{후보}_b{블록}_{gen|mut}{번호}.txt   # 그 후보로 시험한 매트릭스 (SAVE_TESTED_MATRICES)
├── config_used.py               # 실행에 쓴 RowStack_Config.py 사본
├── collected_uncors/            # uncor_seeds.txt (한 줄에 seed 하나), info.json (채널 설정, 모은 수, 돌린 프레임 수), 기존 매트릭스 사본
├── history.csv                  # 블록마다 한 줄: seed, attempt, stage, kind(gen/mut/pool), candidate(후보 번호), block(반복 번호),
│                                #   threshold, takeover_iteration, iterations(예산), parent_min_err, num_improved(개선된 변형 수),
│                                #   best_rank, best_index(최고를 낸 rank와 후보 번호), min_err, min_err_iteration, csw_at_min_err,
│                                #   decoding(success/fail), corrected_iteration, elapsed_sec, note
├── per_uncor/seed_{seed}/LLR_MATRIX_{모드}_uncor_{seed}.txt   # 성공이면 고치는 매트릭스, 실패면 마지막 round에서 순위가 가장 앞선 것
├── summary.csv                  # seed, result(success/reused/fail), num_rows, final_min_err, matrix_file, elapsed_sec, fail_reason
└── found_matrices.csv           # matrix_file, origin_seed, num_fixed, fixed_seeds
```

어느 rank에서든 예외가 나면 traceback을 찍고 `MPI_Abort`로 모든 rank를 멈춘다 (한 rank만 죽어 나머지가 기다리는 일을 막는다).

seed는 `numpy.random.default_rng(seed)`로 프레임을 다시 만드는 정수다. 같은 seed와 같은 채널 설정이면 같은 프레임이다.

## 코드 구성

| 파일 | 책임 |
|------|------|
| `RowStack_Config.py` | 경로 상수, `RowStackConfig`(iteration 예산 계산 포함), `CONFIG` |
| `RowStack_Matrix.py` | 템플릿, `StackedRow`, 값 규칙, 난수 row, 매트릭스 전체 변이, 2_LDPC_base `LLRMatrix` 변환과 DAO 형식 저장, CSW 문턱 규칙 |
| `RowStack_Evaluate.py` | 후보 평가 결과 `CandidateResult`, 순위 키, 개선 판정, `UncorDecoder` (디코더 호출 한 곳, 빈 매트릭스 성능) |
| `RowStack_Parallel.py` | `SerialParallel`, `MpiParallel`, round robin 나누기 |
| `RowStack_Uncor.py` | uncor seed 파일과 info.json, 설정 대조, 실패 seed 추리기 |
| `RowStack_Report.py` | history, summary, found_matrices csv, 설정 머리글, 로그 |
| `RowStack_Main.py` | MPI 흐름 (`run`, `RowStackSession`의 블록과 round, `collect_uncors`) |

## 검사

저장소 루트에서 `python -m pytest 5_DAO/_test/20261021_RowStack -q` (단일 프로세스, 가짜 평가기 포함)과
`python -m pytest 2_LDPC_base/_test/20261021_seed_channel -q` (seed 채널과 복호 함수). mpiexec 확인은
`mpiexec -n 2 python 5_DAO/_test/20261021_RowStack/smoke_run.py`.
