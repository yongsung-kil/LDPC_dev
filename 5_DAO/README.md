# 5_DAO: Decoder Auto Optimizer (Project 5)

DAO(Decoder Auto Optimizer, LLR matrix 자동 최적화기)를 발전시키는 프로젝트.
원형은 SSS 저장소의 `DAO/`이며 2026-08-14에 반입했다.

- ㉮ `reference/`는 반입 시점의 원형 스냅샷이다 (참조 전용, 수정 금지)
- ㉯ 개발은 이 폴더의 `SRC/`, `Util/`, `Input/` 사본에서 진행한다
- ㉰ 반입에서 제외한 것: `__pycache__/`, `Util/msmpisetup.exe`(MS-MPI 설치 파일, 7.5MB).
  MS-MPI는 Microsoft 공식 배포처에서 설치한다. 원형의 개발 로그 `_dev_log/`는
  `reference/`에만 보존한다
- ㉱ 작업 관리: `_pm/TODO.md`

아래는 원형의 사용 설명서다.

---

# DAO (Decoder Auto Optimizer) 사용 설명서

## 목차
1. [실행 방법 및 주요 파라미터](#1-실행-방법-및-주요-파라미터)
2. [아키텍처 및 핵심 클래스](#2-아키텍처-및-핵심-클래스)
3. [주요 기능별 가이드](#3-주요-기능별-가이드)
4. [설정 파일 상세 설명](#4-설정-파일-상세-설명)

---

## 1. 실행 방법 및 주요 파라미터

### 1.1 기본 실행

#### 의존성 설치
```batch
Util\install_requirements.bat
```
- numpy, mpi4py 설치

#### MPI 병렬 실행
```batch
3_run_DAO_mpi.bat
```
- 4개 MPI 프로세스로 병렬 실행
- 실행 인자는 bat 파일 내에서 직접 수정

**bat 파일 내용 예시:**
```batch
mpiexec -n 4 python SRC/DAO_Main.py ^
    --arg1 value1 ^
    --arg2 value2
```

### 1.2 주요 실행 모드

#### 1.2.1 일반 최적화 모드 (기본)
```python
# DAO_Config.py
DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.RUN_OPTIMIZATION
UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST = False
```
- 초기 매트릭스부터 시작하여 N개 스테이지 최적화 수행
- 각 스테이지마다 GenLLRMode 순환
- 명령행 인자로 SIM_IDX를 주면 `Set_Configs_Manually`의 프리셋이 적용된다 (예: `python DAO_Main.py 20`). 십의 자리는 디코더 모드(1 HD, 2 2SD, 3 3SD), 일의 자리는 실행 모드(0 최적화, 1 uncor 저장, 2 재디코딩)

#### 1.2.2 Two-Stage 테스트 모드 (Dynamic Partial)
```python
# DAO_Config.py
UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST = True
UNCOR_CONFIG.UNCOR_MATRIX_IDX = 202    # Full uncor 폴더 번호
```
- Input에는 Full uncor 한 벌만 둔다. Partial uncor는 초기 Full 테스트에서 실패한 uncor를 모아 세션 안에 자동으로 만든다
- 시도마다 Partial 테스트(빠른 스크리닝)로 먼저 거르고, 개선된 것만 Full 테스트(정확한 평가)로 확인한다
- 디렉토리 구조와 uncor 파일 준비 순서는 3.2절

#### 1.2.3 초기 매트릭스만 테스트
```python
# DAO_Config.py
DAO_CONFIG.RUN_DAO_MODE = RunDAOMode.TEST_FER
```
- 초기 매트릭스 로드 및 테스트만 수행
- FER 측정 후 종료
- `RunDAOMode.SAVE_UNCOR`는 같은 흐름에서 실패 uncor를 Input에 저장하고 종료한다 (부록 C)

#### 1.2.4 코어 속도 테스트 모드
```python
# DAO_Config.py
SPEED_TEST_REFC_CONFIG.ENABLE_CORE_SPEED_TEST = True
SPEED_TEST_REFC_CONFIG.CORE_SPEED_CUTOFF_RATIO = 2.0
```
- 최적화 시작 전 모든 코어의 속도를 사전 측정
- 평균 대비 `CORE_SPEED_CUTOFF_RATIO`배 이상 느린 코어 자동 제외
- 제외된 코어는 이후 모든 테스트에서 스킵

**동작 원리:**
1. 모든 프로세스가 동일 시드(`CORE_SPEED_TEST_SEED=9999`)로 짧은 테스트 실행
2. 각 코어별 소요 시간 수집
3. 각 코어마다 자신을 제외한 다른 코어들의 평균 계산
4. 평균 대비 2배 이상 느린 코어를 `excluded_cores` 리스트에 추가
5. 이후 모든 테스트에서 제외된 코어는 결과 수집 대상에서 자동 제외

### 1.3 주요 파라미터

#### 최적화 단계 제어
```python
# DAO_Config.py
class DAO_CONFIG:
    MAX_OPTIMIZATION_STAGE = 500         # 총 최적화 스테이지 수
    MAX_GEN_RETRY_PER_TRIAL = 5          # trial당 최대 재시도 횟수
    INITIAL_MATRIX_IDX = 999             # 초기 LLR 매트릭스 인덱스
```

#### 타겟 그룹 설정
```python
# DAO_Config.py
INITIAL_TARGET_GROUP_IDX = 1        # 이 인덱스부터 끝까지를 타겟 그룹으로 설정
FIXED_TARGET_GROUP_IDX_LIST = None  # 타겟 그룹을 직접 지정 (예: [0, 1]). None이면 INITIAL_TARGET_GROUP_IDX를 따름
```
- 예: `INITIAL_TARGET_GROUP_IDX = 1`이면 `[1, 2, 3, ..., 마지막 그룹]`
- 예: `INITIAL_TARGET_GROUP_IDX = 0`이면 `[0, 1, 2, ..., 마지막 그룹]`
- 예: `FIXED_TARGET_GROUP_IDX_LIST = [0, 1]`이면 그룹 0과 1만 변경 (이때 `INITIAL_TARGET_GROUP_IDX`는 쓰이지 않음)
- GenLLRMode 시퀀스 한 바퀴당 하나씩 순환
- **INSERT_RANDOM_GROUP 실행 시 자동 업데이트**
  - 삽입 위치 이후 인덱스 +1 보정
  - 새 그룹 인덱스 맨 뒤에 추가
- **`FIXED_TARGET_GROUP_IDX_LIST`와 함께 쓰는 모드**: 목록의 index가 그룹 번호에 묶여 있으므로 그룹 수, 순서, iteration 구간을 그대로 두는 모드만 쓴다
  - 허용: MUTATE_MATRIX(10), MUTATE_CSW(11), SWAP_ROW(21), COPY_ROWS(30), COPY_GROUP(31), INSERT_RANDOM_ROW(41), INSERT_MUTATED_ROW(43), REGEN_DV(50), REGEN_ROW(51)
  - 지금 쓰는 시퀀스에 다른 모드가 있으면 `Validate_Config`가 시작할 때 오류 문구를 내고 멈춘다
  - 목록에 SW 분기 그룹(헤더 10 이상)이 있으면 이 가운데 MUTATE_MATRIX(10)와 MUTATE_CSW(11)만 쓴다 (3.4절). 예: `LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`의 iteration 1~8 그룹을 바꾸려면 시퀀스에 MUTATE_MATRIX와 MUTATE_CSW만 남긴다

#### GenLLRMode 시퀀스
시퀀스는 모드를 이름으로 적는다. `DAO_Config.py`의 기본값에서 돌릴 모드만 남기고 순서를 정한다. 보통 모드의 기본값은 `GenLLRMode`의 모드 17개를 모두 적은 목록이고, HBF 최적화 모드의 기본값은 `GenLLRModeHBF`의 모드 11개에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 뺀 9개다.
```python
# DAO_Config.py
Gen_LLR_Mode_SEQUENCE = [            # 보통 모드: GenLLRMode의 이름
    GenLLRMode.MUTATE_MATRIX,
    GenLLRMode.MUTATE_CSW,
    GenLLRMode.COPY_ROWS,
]
Gen_LLR_Mode_HBF_SEQUENCE = [        # HBF 최적화 모드(IS_HBF_OPT): GenLLRModeHBF의 이름
    GenLLRModeHBF.MUTATE_MATRIX,
    GenLLRModeHBF.MUTATE_CSW,
]
```
- stage마다 목록의 다음 모드를 돌고, 끝까지 가면 처음으로 돌아간다
- GEN_INITIAL_GROUP은 stage 1에서만 돌므로 쓰려면 맨 앞에 둔다
- 로그는 모드를 값(숫자)으로 적는다 (예: `[current_gen_trial_LLR_mode]: MUTATE_CSW (11)  (2/3) [10, '11', 30]`)

#### 채널 설정
```python
# DAO_Config.py
REFC_CONFIG.NUM_TARGET_CHANNELS = 0  # ch_type에 따라 자동 설정
```

---

## 2. 아키텍처 및 핵심 클래스

### 2.1 전체 구조

```
-----------------------------------------------------------
DAO_Main.py

LLR_OPT (최적화 엔진)
  - MPI 통신 관리 (rank 0: master, 나머지: worker)
  - LLR 생성 (Gen_Trial_LLR)
  - 테스트 수행 (Test_LLR)
  - 최적 매트릭스 선정 (Update_Optimal_LLR)
-----------------------------------------------------------
                       ▼ 사용
-----------------------------------------------------------
DAO_LLR_MATRIX.py

LLR_MATRIX (데이터 구조)
  - groups: 그룹별 행 컨테이너
  - header: 메타데이터 (LLR_Header)
  - FERs: 테스트 결과
  - Deep_Copy: 매트릭스 복사
  - Read/Write: 파일 I/O
-----------------------------------------------------------
                       ▲ 참조
-----------------------------------------------------------
DAO_Config.py

- DAO_CONFIG: 최적화 설정
- REFC_CONFIG: ECC 실험 설정
- UNCOR_CONFIG: Uncor 관련 설정
- SPEED_TEST_REFC_CONFIG: 코어 속도 테스트 설정
- PRINT_LOG_CONFIG: 로그 출력 설정
- TIME_CONFIG: 시간 제한 설정
- DEBUG_CONFIG: 디버그 설정
- PATH_CONFIG: 입출력 경로
- GenLLRMode별 상세 설정
-----------------------------------------------------------
```

### 2.2 핵심 클래스 상세

#### 2.2.1 LLR_OPT ([DAO_Main.py:255](DAO/SRC/DAO_Main.py#L255))

**역할:** LLR 매트릭스 최적화를 수행하는 메인 엔진

**주요 속성:**
```python
class LLR_OPT:
    # 매트릭스
    initial_LLR_matrix: LLR_MATRIX          # 초기 매트릭스
    current_LLR_matrix: LLR_MATRIX          # 현재 작업 매트릭스
    optimal_LLR_matrix: LLR_MATRIX          # 최적 매트릭스

    # MPI 통신
    comm: MPI.Comm                          # MPI communicator
    rank: int                               # 프로세스 rank (0=master)
    num_process: int                        # 총 프로세스 수
    is_root: bool                           # rank 0 여부

    # 최적화 상태
    current_trial_idx: int                  # 현재 trial 번호
    current_gen_trial_LLR_mode: GenLLRMode  # 현재 GenLLRMode
    current_target_group_idx: int           # 현재 타겟 그룹 인덱스

    # Runtime 업데이트 (INSERT_RANDOM_GROUP에서 자동 갱신)
    target_group_indices: list[int]         # 동적 타겟 그룹 인덱스 리스트

    # 코어 속도 테스트 관련 (신규)
    excluded_cores: list[int]               # 테스트에서 제외할 느린 코어 rank 목록
    is_current_core_excluded: bool          # 현재 코어가 제외 대상인지 여부
```

**주요 메서드:**

| 메서드 | 설명 | 위치 |
|--------|------|------|
| `Run_Optimization` | 메인 최적화 루프 실행 | [DAO_Main.py](DAO/SRC/DAO_Main.py) |
| `Gen_Trial_LLR` | 새로운 trial LLR 생성 (GenLLRMode 실행) | [DAO_Main.py](DAO/SRC/DAO_Main.py) |
| `Test_LLR` | LLR 매트릭스 테스트 (FER 측정) | [DAO_Main.py](DAO/SRC/DAO_Main.py) |
| `Update_Optimal_LLR` | 최적 매트릭스 갱신 판단 | [DAO_Main.py](DAO/SRC/DAO_Main.py) |
| `Test_Core_Speed` | 코어 속도 사전 측정 및 느린 코어 제외 | [DAO_Main.py:5313](DAO/SRC/DAO_Main.py#L5313) |

**MPI 동기화 흐름:**
```python
# 각 rank가 독립 trial 수행
if self.is_root:
    new_LLR_matrix = self.Gen_Trial_LLR(...)  # rank 0만 생성

# 생성 성공 여부 동기화
self.generate_LLR_success = self.comm.bcast(
    self.generate_LLR_success if self.is_root else None
)

# 성공 시 매트릭스 전파
if self.generate_LLR_success:
    self.current_LLR_matrix = self.comm.bcast(
        self.current_LLR_matrix if self.is_root else None
    )
    # target_group_indices도 함께 동기화
    self.target_group_indices = self.comm.bcast(
        self.target_group_indices if self.is_root else None
    )
```

#### 2.2.2 LLR_MATRIX ([DAO_LLR_MATRIX.py:34](DAO/SRC/DAO_LLR_MATRIX.py#L34))

**역할:** LLR 매트릭스 데이터 구조 및 파일 I/O

**주요 속성:**
```python
class LLR_MATRIX:
    # 매트릭스 구조
    header: LLR_Header                  # 헤더 (DV, 그룹 정보)
    groups: list[list[LLR_Row]]         # 그룹별 행 컨테이너
    restart_groups: list[int]           # 재시작 그룹 1-based 인덱스

    # 테스트 결과 (Full)
    FERs: list[float]                   # Frame Error Rate
    raw_FERs: list[float]               # raw FER (uncor 적용 전)
    seed_FERs: list[float]              # seed FER
    effective_FERs: list[float]         # 유효 FER
    avg_iterations: list[float]         # 평균 iteration 수

    # 테스트 결과 (Partial - Two-stage 모드 전용)
    FERs_partial: list[float]
    raw_FERs_partial: list[float]
    seed_FERs_partial: list[float]
    effective_FERs_partial: list[float]

    # 메타 정보
    matrix_idx: int                     # 매트릭스 인덱스
    decoder_mode_str: str               # "HD", "2SD", "3SD"
    is_HBF_OPT: bool                    # HBF 최적화 여부
```

**LLR_Header 구조:**
```python
@dataclass
class LLR_Header:
    num_parameter_each_set: int         # DV당 파라미터 수
    num_dv: int                         # DV 개수
    dv_from: np.ndarray                 # DV 시작 인덱스
    dv_to: np.ndarray                   # DV 종료 인덱스
    num_group: int                      # 그룹 총 개수
    num_row_each_group: np.ndarray      # 그룹별 행 개수
    type_each_group: np.ndarray         # 그룹별 유형
    num_restart: int                    # 재시작 지점 수
    restart_iter: np.ndarray            # 재시작 iteration 배열
    max_value: np.ndarray               # 파라미터별 최대값
    min_value: np.ndarray               # 파라미터별 최소값
```

**LLR_Row 구조:**
```python
@dataclass
class LLR_Row:
    ch_th_values: np.ndarray            # DV별 CH/TH 값
    CSW: int                            # Column Selection Weight (0~1408)
    iter_start: int                     # 시작 iteration
    iter_end: int                       # 종료 iteration
    floor_flag: int                     # Floor 플래그
    is_group_restart: bool              # 재시작 그룹 여부
```

**주요 메서드:**

| 메서드 | 설명 | 위치 |
|--------|------|------|
| `Read_LLR_from_File` | 파일에서 LLR 매트릭스 로드 | [DAO_LLR_MATRIX.py](DAO/SRC/DAO_LLR_MATRIX.py) |
| `Write_To_File` | LLR 매트릭스를 파일로 저장 | [DAO_LLR_MATRIX.py](DAO/SRC/DAO_LLR_MATRIX.py) |
| `Deep_Copy` | 매트릭스 깊은 복사 (FER 선택적 복사) | [DAO_LLR_MATRIX.py:203](DAO/SRC/DAO_LLR_MATRIX.py#L203) |
| `Is_LLR_Valid` | 매트릭스 유효성 검증 | [DAO_LLR_MATRIX.py:242](DAO/SRC/DAO_LLR_MATRIX.py#L242) |

#### 2.2.3 DAO_Config 설정 클래스들 ([DAO_Config.py](DAO/SRC/DAO_Config.py))

**DAO_CONFIG:** 최적화 실행 설정
```python
class DAO_CONFIG:
    MAX_OPTIMIZATION_STAGE = 500        # 총 스테이지 수
    MAX_GEN_RETRY_PER_TRIAL = 5         # trial당 재시도 횟수
    INITIAL_TARGET_GROUP_IDX = 1        # 타겟 그룹 시작 인덱스
    Gen_LLR_Mode_SEQUENCE = [...]       # GenLLRMode 시퀀스
    RUN_DAO_MODE = RunDAOMode.RUN_OPTIMIZATION
```

**REFC_CONFIG:** ECC 실험 설정
```python
class REFC_CONFIG:
    ECC_VER = "3.0"                     # ECC 버전
    init_n = 1                          # 디코더 모드 (1=HD, 2=2SD, 3=3SD)
    fn = 3                              # 최소 Frame Error 수
    max_num_test = 1000                 # 최대 Frame 수
    MAX_DECODING_ITERATION = 1500       # 최대 디코딩 iteration
```

**UNCOR_CONFIG:** Uncor 관련 설정 (신규 분리)
```python
class UNCOR_CONFIG:
    ENABLE_TWO_STAGE_TEST = False
    UNCOR_MATRIX_IDX = -1
    ENABLE_LOAD_VECTOR = False
    IS_TLC = True
    LOAD_UNCOR_MODE = DAOLoadUncorMode.DEFAULT
```

**SPEED_TEST_REFC_CONFIG:** 코어 속도 테스트 설정 (신규)
```python
class SPEED_TEST_REFC_CONFIG(REFC_CONFIG):
    ENABLE_CORE_SPEED_TEST = True       # 코어 속도 테스트 활성화
    CORE_SPEED_CUTOFF_RATIO = 2.0       # 평균 대비 몇 배 느리면 제외할지
    fn = 50
    max_num_test = 50
    ch_type = 1
    RBERs = [0.1]
    mode_init_seed = CORE_SPEED_TEST_SEED  # 9999
```

**PRINT_LOG_CONFIG:** 로그 출력 설정 (신규)
```python
class PRINT_LOG_CONFIG:
    ENABLE_TEST_OPTIMAL_LLR_MATRIX_PRINT_CSW_LOG = True
    ENABLE_PRINT_ALL_ITER_FERs = True
```

**TIME_CONFIG:** 시간 제한 설정 (신규)
```python
class TIME_CONFIG:
    MAX_STAGE_TIME_SECONDS = 2 * 60 * 60       # Stage별 최대 실행 시간 (2시간)
    MPI_COMM_TIMEOUT_SECONDS = 1 * 60 * 60     # MPI 통신 타임아웃 (1시간)
```

**DEBUG_CONFIG:** 디버그 설정
```python
class DEBUG_CONFIG:
    ENABLE_DEBUG_MODE = False
    ENABLE_UPDATE_LOG = False
    ENABLE_SAVE_ALL_TRIAL_LLR_MATRIX = False
```

**각종 GenLLRMode Config:**
- `MUTATE_CONFIG`: MUTATE_MATRIX, MUTATE_CSW 설정
- `INSERT_RANDOM_GROUP_CONFIG`: INSERT_RANDOM_GROUP 설정
- `COPY_ROWS_CONFIG`: COPY_ROWS 설정
- 등등...

### 2.3 데이터 흐름

```
[초기화]
Load Initial Matrix → Test Core Speed → Test → Set as Optimal
         ▼
[최적화 루프: Stage 1 ~ N]
    ▼
Set_Gen_Trial_LLR_Mode (GenLLRMode 선택)
    ▼
Gen_Trial_LLR (새 매트릭스 생성)
    │
    ├─ MUTATE_MATRIX: 행렬 값 변이
    ├─ MUTATE_CSW: CSW 값 변이
    ├─ SWAP_ROW: 행 교환
    ├─ COPY_ROWS: 행 복사
    ├─ COPY_GROUP: 그룹 복사
    ├─ INSERT_RANDOM_GROUP: 그룹 삽입 ★
    ├─ INSERT_RANDOM_ROW: 행 삽입
    ├─ REGEN_DV: DV 재생성
    └─ REGEN_ROW: 행 재생성
    ▼
MPI Bcast (current_LLR_matrix 전파)
    ▼
Test_LLR (FER 측정)
    │
    ├─ Two-Stage=False: Full 테스트만
    └─ Two-Stage=True: Partial → Full (조건부)
    ▼
Update_Optimal_LLR (최적 여부 판단)
    │
    ├─ FER 개선 → Optimal 갱신
    └─ FER 나빠짐 → 유지
    ▼
[다음 Stage로]
```

**★ INSERT_RANDOM_GROUP 특별 동작:**
```
Gen_LLR_Insert_Random_Group 실행
    ▼
그룹 삽입 (target_group_idx + 1 위치)
    ▼
target_group_indices 자동 업데이트
    ├─ 삽입 위치 이후 인덱스 +1 보정
    └─ 새 그룹 인덱스 맨 뒤에 추가
    ▼
MPI Bcast로 모든 rank에 동기화
```

---

## 3. 주요 기능별 가이드

### 3.1 GenLLRMode 상세

#### 3.1.1 MUTATE_MATRIX (10)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 매트릭스의 CH/TH 값을 랜덤하게 변이
- 타겟 그룹의 특정 행들을 수정

**설정:**
```python
class MUTATE_CONFIG:
    NUM_ELEMENTS_TO_MUTATE_CHTH = 3     # 변이할 CH/TH 개수
    NUM_ELEMENTS_TO_MUTATE_CSW = 1      # 변이할 CSW 개수
    MUTATION_RANGE = 5                  # 변이 범위
    ENABLE_CSW_UPDATE_LIMIT = False     # CSW 업데이트 제한
    CSW_UPDATE_LIMIT_VALUE = 128        # CSW 최대값
```

**알고리즘:**
1. `current_target_group_idx`로 타겟 그룹 선택
2. 그룹 내 랜덤 행 선택
3. CH/TH 값에 랜덤 델타 적용
4. 유효성 검증 (min/max 범위 체크)
5. 반복 (MAX_GEN_RETRY_PER_TRIAL번)

#### 3.1.2 MUTATE_CSW (11)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- CSW (Column Selection Weight) 값 변경
- 디코더 성능에 직접 영향

**알고리즘:**
1. 타겟 그룹의 모든 행 순회
2. 각 행의 CSW에 ±1 적용
3. 범위 체크 (0 ~ MAX_CSW=1408)
4. 성능 측정 후 최적값 선택

#### 3.1.3 SWAP_ROW (21)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 같은 그룹 내 두 행의 위치 교환
- Iteration 순서 변경으로 성능 개선 시도

**알고리즘:**
1. 타겟 그룹에서 2개 행 선택
2. 위치 교환
3. iter_start/iter_end 재계산
4. 유효성 검증

#### 3.1.4 COPY_ROWS (30)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 다른 그룹의 우수한 행을 타겟 그룹으로 복사
- 성능 좋은 패턴 전파

**설정:**
```python
class COPY_ROWS_CONFIG:
    pass  # 기본 설정 사용
```

**알고리즘:**
1. 타겟 그룹 선택
2. 다른 모든 그룹에서 후보 행 수집
3. 타겟 그룹의 각 행에 대해:
   - 후보 행 하나씩 교체 시도
   - 최적 조합 찾기

#### 3.1.5 COPY_GROUP (31)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 타겟 그룹의 row를 다른 그룹(후보)의 row로 통째로 바꿈
- 후보에서 가져오는 것은 row의 값과 CSW
- 타겟 그룹의 iteration과 SW 분기 표시(row의 마지막 칸, 헤더의 분기 표시)는 그대로

**알고리즘:**
1. 타겟 그룹 선택
2. 소스 그룹 후보 수집 (타겟 제외)
3. 각 소스 그룹의 값과 CSW로 타겟 그룹의 row를 대체
4. 새 row에 타겟 그룹의 iteration과 SW 분기 표시를 적용
5. 최적 조합 선택

#### 3.1.6 INSERT_RANDOM_GROUP (40) ★
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- target_group_idx 바로 뒤에 새 그룹 삽입
- **target_group_indices 자동 업데이트**

**설정:**
```python
class INSERT_RANDOM_GROUP_CONFIG:
    INSERT_GROUP_NUM_ROWS = 3           # 삽입할 행 수
    INSERT_GROUP_NUM_ITERATION = 20     # 그룹 iteration 수
    ENABLE_INSERT_RESTART = True        # restart 그룹 함께 추가
```

**알고리즘:**
```python
# 1. 삽입 위치 결정
insert_position = target_group_idx + 1

# 2. 새 그룹 생성
new_group = [
    LLR_Row(
        ch_th_values=random_values,
        CSW=random_CSW,
        iter_start=calculated_start,
        iter_end=calculated_end
    )
    for _ in range(INSERT_GROUP_NUM_ROWS)
]

# 3. 삽입 (+ restart 그룹 옵션)
if ENABLE_INSERT_RESTART:
    groups_to_insert = [
        (restart_group, True),
        (new_group, False)
    ]
else:
    groups_to_insert = [(new_group, False)]

matrix.groups.insert(insert_position, groups_to_insert)

# 4. ★ target_group_indices 자동 업데이트
adjusted_indices = [
    idx + num_inserted if idx >= insert_position else idx
    for idx in self.target_group_indices
]
# 새 일반 그룹 인덱스 추가 (restart 그룹 제외)
for offset, (_, is_restart) in enumerate(groups_to_insert):
    if not is_restart:
        adjusted_indices.append(insert_position + offset)

self.target_group_indices = adjusted_indices

# 5. MPI Bcast로 동기화 (Gen_Trial_LLR에서 자동)
```

**예시:**
```
초기:
  groups: [G0, G1, G2, G3]
  target_group_indices: [1, 2, 3]
  target_group_idx: 2

삽입 후:
  groups: [G0, G1, G2, G_restart, G_new, G3]
                      ↑         ↑
                 position 3   position 4

  target_group_indices: [1, 2, 5, 4]
                               ↑  ↑
                              G3  G_new
                            (이동) (새로 추가)
```

#### 3.1.7 INSERT_RANDOM_ROW (41)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 타겟 그룹에 새 행 삽입
- 그룹 크기 증가

**설정:**
```python
class INSERT_RANDOM_ROW_CONFIG:
    pass  # 기본 설정 사용
```

#### 3.1.8 REGEN_DV (50)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 특정 DV의 모든 값 재생성
- 전역적 변화

**설정:**
```python
class REGEN_DV_CONFIG:
    ENABLE_FIX_IDX = False              # True일 때 고정 인덱스 사용
    FIXED_ROW_IDX: int | list[int] = -1  # -1: 전체 순회
    FIXED_DV_IDX: int | list[int] = -1   # -1: 전체 순회
```

**알고리즘:**
1. 타겟 그룹의 모든 행 수집
2. 각 DV별로:
   - 해당 DV의 CH/TH 값 재생성
   - 모든 행에 적용
3. 최적 DV 선택

#### 3.1.9 REGEN_ROW (51)
**위치:** [DAO_Main.py](DAO/SRC/DAO_Main.py)

**동작:**
- 타겟 그룹의 특정 행 완전 재생성
- 행 단위 리셋

**설정:**
```python
class REGEN_ROW_CONFIG:
    ENABLE_FIX_IDX = False              # True일 때 고정 인덱스 사용
    FIXED_ROW_IDX: int | list[int] = -1  # -1: 전체 순회
```

### 3.2 Two-Stage 테스트 시스템 (Dynamic Partial)

#### 3.2.1 개요
**목적:** 테스트 시간 절약
- Partial: 초기 매트릭스가 정정하지 못한 uncor만 모은 작은 묶음으로 빠르게 스크리닝
- Full: Input에 둔 uncor 전체로 정확하게 평가

Partial 묶음은 Input에 두지 않는다. 초기 Full 테스트에서 실패한 uncor를 모아 세션 안에 만들고, optimal이 갱신될 때마다 다시 만든다. 코드에서는 이 방식을 Dynamic Partial이라 부른다.

**동작 흐름:**
```
초기 매트릭스 Full 테스트 (실패 uncor 저장)
    ▼
실패 uncor를 모아 Partial 풀 생성
    ├─ 실패 uncor 0개 → 최적화 목표 달성으로 종료
    ▼
새 매트릭스 생성
    ▼
Partial Test (빠름)
    ├─ FER 개선 없음 → Full Test 생략
    └─ FER 개선 → Full Test 진행
         ▼
    Full Test (정확)
         ├─ FER 개선 → Optimal 갱신, Partial 풀 재구성
         └─ FER 개선 없음 → 유지
```

#### 3.2.2 설정
```python
# DAO_Config.py
UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST = True   # Dynamic Partial 켜기
UNCOR_CONFIG.UNCOR_MATRIX_IDX = 202         # Full uncor 폴더 번호 (-1이면 모드 폴더 바로 아래)
```
Partial 전용 설정은 없다. 위 두 값과 함께 uncor 파일 이름을 정하는 `REFC_CONFIG`의 `init_n`, `ch_type`, `matrix_sel`, 채널 값(`RBERs`, `num_fixed_errs`, `fixed_SCRs`, `fixed_SERs`)이 Input의 파일과 맞아야 한다. 하나라도 어긋나면 `Copy_Uncors`가 "Missing input uncor file"로 멈춘다.

함께 쓸 수 있는 조합은 `Validate_Config`가 시작할 때 검사한다.

| 설정 | Two-Stage 테스트 |
|------|------|
| `RUN_DAO_MODE`가 RUN_OPTIMIZATION | 사용 |
| `RUN_DAO_MODE`가 REDECODE 또는 GEN_SINGLE_ROW | 시작할 때 오류 |
| uncor 로드 모드가 LOAD_SEED | 사용 |
| uncor 로드 모드가 LOAD_NONE 또는 LOAD_VECTOR (`ENABLE_LOAD_VECTOR`) | 시작할 때 오류 |
| `IS_HBF_OPT` (HBF 최적화 모드) | 켜든 끄든 사용 |

#### 3.2.3 Uncor 디렉토리 구조
`Uncors/` 아래는 디코더 모드 폴더(`HD`, `2SD`, `3SD`)로 나뉘고, 그 아래에 LLR matrix 파일 이름과 같은 이름의 폴더를 둔다 (폴더 이름에 `.txt`까지 포함). Two-Stage 여부와 관계없이 구조는 같다. 아래는 2SD(init_n = 2), INITIAL_MATRIX_IDX = 200, UNCOR_MATRIX_IDX = 202 예시다.

```
Input/Ref_C/Prime_ECC_3.0/
├── EXE/
│   └── Prime_ECC_3.0.exe                    # Linux는 확장자 없이 Prime_ECC_3.0
├── H_Matrix/                                 # 폴더째 세션으로 복사
├── Initial_LLR_matrix/
│   └── 2SD/
│       └── LLR_MATRIX_200.txt                # 초기 매트릭스
└── Uncors/
    └── 2SD/
        ├── uncor_seed_..._init_n_2_0.txt     # UNCOR_MATRIX_IDX = -1 일 때 읽는 위치
        └── LLR_MATRIX_202.txt/               # UNCOR_MATRIX_IDX = 202 일 때 읽는 위치 (폴더)
            └── uncor_seed_..._init_n_2_0.txt # 채널마다 한 파일
```

uncor 파일 이름은 `Get_Uncor_File_Name`이 `ch_type`에 따라 만든다 (matrix_sel = 1, init_n = 2 예시). 끝의 `_0`은 프로세스 번호이며 Input에서 읽을 때는 항상 0이다. `ENABLE_LOAD_VECTOR`가 True면 `uncor_seed` 대신 `uncor_vector`, 확장자는 `.dat`이다.

| ch_type | 파일 이름 |
|---|---|
| 1 (RBER) | `uncor_seed_H_1_CH_1_E1.35e-02_init_n_2_0.txt` |
| 2 (고정 오류 수) | `uncor_seed_H_1_CH_2_E520_init_n_2_0.txt` |
| 3 (고정 오류 수, SCR, SER) | `uncor_seed_H_1_CH_3_E520_SC_0.94_SE_0.23_init_n_2_0.txt` |

**uncor 파일 준비 순서**
- ㉮ `RUN_DAO_MODE = RunDAOMode.SAVE_UNCOR`로 초기 매트릭스를 한 번 돌린다 (프리셋 SIM_IDX 11, 21, 31)
- ㉯ 결과는 `Uncors/{모드}/LLR_MATRIX_{INITIAL_MATRIX_IDX}.txt/Recoded_uncors_{YYYYMMDD_HHMMSS}/`에 저장된다 (부록 C)
- ㉰ 그 안의 uncor 파일을 `Uncors/{모드}/LLR_MATRIX_{UNCOR_MATRIX_IDX}.txt/` 바로 아래로 옮긴다. 읽기는 타임스탬프 폴더가 아니라 매트릭스 이름 폴더 바로 아래에서 한다

#### 3.2.4 Uncor 로드와 Partial 풀 생성 ([DAO_Main.py](DAO/SRC/DAO_Main.py))
- ㉮ `Setup_Uncor_Pool`: 최적화 모드에서는 `LOAD_UNCOR_MODE`가 자동으로 `LOAD_SEED`가 된다. root가 `Copy_Uncors`로 Input의 Full uncor를 세션 `5_Uncors/Copied_uncors/`로 복사하고, 각 코어의 `Uncor_Pool/`에 나눠 둔다
- ㉯ `Test_Initial_LLR`: Two-Stage가 켜져 있으면 초기 매트릭스를 Full uncor로 테스트하면서 실패한 uncor를 저장한다. 이 테스트와 Rebuild의 Full 테스트는 실행 전에 각 rank가 자기 redecode 파일을 지워 이번 실행분만 남긴다
- ㉰ `_Build_Initial_Partial_Pool`: 실패 uncor를 모아 `5_Uncors/tmp_partial_uncors/{매트릭스 파일 이름}/`에 두고 각 코어의 Partial 풀로 나눈다. 실패 uncor가 0개이면 종료 플래그를 세우고 최적화를 시작하지 않는다
- ㉱ `Rebuild_Partial_Pool`: 초기 테스트 뒤 optimal이 갱신될 때마다 그 매트릭스의 실패 uncor로 Partial 풀을 다시 만든다
- ㉲ `Ensure_Uncors_Loaded`: 시도마다 필요한 test_mode(PARTIAL 또는 FULL)의 uncor가 작업 폴더에 있는지 확인하고 풀에서 복사한다
#### 3.2.5 FER 저장 분리
**Partial과 Full 결과를 별도 필드에 저장:**
```python
# LLR_MATRIX
class LLR_MATRIX:
    # Full 테스트 결과
    FERs: list[float]
    raw_FERs: list[float]
    seed_FERs: list[float]
    effective_FERs: list[float]

    # Partial 테스트 결과 (덮어쓰기 방지)
    FERs_partial: list[float]
    raw_FERs_partial: list[float]
    seed_FERs_partial: list[float]
    effective_FERs_partial: list[float]
```

**업데이트 판단 로직:**
```python
# Partial 테스트 (현재 매트릭스)
Test_LLR(current_matrix, test_mode=TestMode.PARTIAL)
# → current_matrix.FERs_partial 저장

# Partial 결과 비교 (optimal의 Partial FER과 채널별 비교)
if not Is_List_A_Strictly_Better(current_matrix.FERs_partial, optimal_matrix.FERs_partial):
    # Partial에서 개선이 없음 → Full 테스트 생략
    return False

# Full 테스트 (현재 매트릭스)
Test_LLR(current_matrix, test_mode=TestMode.FULL)
# → current_matrix.FERs 저장

# Full 결과로 최종 판단
if Is_List_A_Strictly_Better(current_matrix.FERs, optimal_matrix.FERs):
    Update_Optimal_LLR()
    Rebuild_Partial_Pool()
    return True
```

`is_update_at_last_trial`이 켜져 있으면 비교 대상은 temp optimal이고, 모드의 마지막 trial은 Partial 결과와 관계없이 Full 테스트를 한다.

### 3.3 MPI 병렬 처리 구조

#### 3.3.1 Rank 역할 분담
```
------------------------------------------------
  Rank 0 (Master)
  - LLR 생성 (Gen_Trial_LLR)
  - 최적 매트릭스 결정 (Update_Optimal_LLR)
  - 로그 기록
  - 파일 저장 (optimal LLR)
------------------------------------------------
              │ bcast
              ▼
------------------------------------------------
  Rank 1, 2, 3, ... (Workers)
  - current_LLR_matrix 수신
  - target_group_indices 수신
  - 테스트 수행 (Test_LLR)
  - FER 측정
------------------------------------------------
              │ (독립 실행)
              ▼
          Barrier 동기화
```

#### 3.3.2 주요 동기화 포인트
```python
# 1. 매트릭스 생성 후
self.current_LLR_matrix = self.comm.bcast(
    self.current_LLR_matrix if self.is_root else None
)
self.target_group_indices = self.comm.bcast(
    self.target_group_indices if self.is_root else None
)

# 2. 테스트 전
self.comm.Barrier()  # 모든 rank 대기

# 3. 테스트 후
self.comm.Barrier()  # 결과 수집 전 동기화
```

#### 3.3.3 로컬 작업 디렉토리
**각 rank는 독립 작업 공간 사용:**
```
Output/{session}/
├── Process_0/              # Rank 0
│   ├── 1_Log/
│   │   └── Log.txt
│   ├── 2_Optimal_LLR_matrix/
│   ├── 3_Trial_LLR_matrix/
│   └── 5_Uncors/
├── Process_1/              # Rank 1
│   └── ...
├── Process_2/              # Rank 2
│   └── ...
└── Process_3/              # Rank 3
    └── ...
```

**Optimal LLR은 Rank 0만 저장:**
```python
if self.is_root and now_optimal_LLR_update:
    self.Save_LLR_Matrix(
        self.optimal_LLR_matrix,
        target_dir=self.optimal_output_dir
    )
```

---

### 3.4 SW 분기 매트릭스에서 허용되는 모드

헤더 `type_each_group`이 10 이상인 그룹은 SW(Syndrome Weight, 신드롬 무게) 분기 그룹이다. 10은 분기 1개(row 꼬리 0), 20과 21은 분기 2개(row 꼬리 0과 1)이고, 10 미만은 보통 그룹(row 꼬리 -1)이다. 타겟은 분기 그룹도 그룹 하나씩 고르고, 변이는 타겟 그룹 하나에만 들어간다. 자세한 규칙은 `DAO_spec.md` 3.7절에 있다.

- ㉮ 타겟 그룹(`INITIAL_TARGET_GROUP_IDX`부터 끝까지, 또는 `FIXED_TARGET_GROUP_IDX_LIST`로 지정한 그룹)에 분기 그룹이 들어 있으면 지금 쓰는 시퀀스(`Gen_LLR_Mode_SEQUENCE`, HBF 최적화 모드는 `Gen_LLR_Mode_HBF_SEQUENCE`)에 MUTATE_MATRIX(10)와 MUTATE_CSW(11)만 넣는다. 다른 모드가 있으면 `Validate_Config`가 시작할 때 오류 문구를 내고 멈춘다. 타겟을 분기 구간 뒤의 보통 그룹으로 두면 다른 모드도 쓸 수 있고(GEN_INITIAL_GROUP 제외), 그때 타겟 앞의 그룹을 바꾼 trial은 버려지고 로그에 `[SW branch]`로 남는다
- ㉯ 여러 분기로 갈라진 구간의 그룹은 분기 index와 상관없이 타겟이 된다. 어느 분기의 그룹을 바꿀지는 타겟 목록으로 정하고, 그 분기에 맞는 uncor seed는 사용자가 준비한다
- ㉰ `INITIAL_TARGET_GROUP_IDX`와 `FIXED_TARGET_GROUP_IDX_LIST`의 값은 그룹 하나하나의 index다 (매트릭스 파일에 적힌 그룹 순서를 0부터 센다). 분기 그룹도 그룹마다 따로 타겟이 된다
- ㉱ DAO는 분기를 만들거나 없애지 않는다. 헤더 `type_each_group`은 읽은 값을 그대로 보존한다

---

## 4. 설정 파일 상세 설명

### 4.1 DAO_Config.py 구조

#### 4.1.1 DAO_CONFIG (최적화 전역 설정)

```python
class DAO_CONFIG:
    # ========== 최적화 단계 설정 ==========
    MAX_OPTIMIZATION_STAGE: int = 500
    """총 최적화 스테이지 수
    - 각 스테이지마다 GenLLRMode 시퀀스 순환
    - 예: MAX_OPTIMIZATION_STAGE=500, 시퀀스 길이=9 → 55.5 사이클
    """

    MAX_GEN_RETRY_PER_TRIAL: int = 5
    """각 trial당 최대 재시도 횟수
    - LLR 생성 실패 시 재시도
    - MUTATE_MATRIX, INSERT_RANDOM_GROUP 등에서 사용
    """

    MAX_OPTIMIZATION_TRIALS: int = 30
    """각 모드별 기본 시도 횟수
    - 특정 모드에서는 모드에 따라 max trial 설정됨
    """

    # ========== 초기 매트릭스 설정 ==========
    INITIAL_MATRIX_IDX: int = 999
    """초기 LLR 매트릭스 인덱스
    - 파일명: LLR_MATRIX_{INITIAL_MATRIX_IDX}.txt
    - 위치: Input/Ref_C/{ECC_NAME}/Initial_LLR_matrix/{HD,2SD,3SD}/
    """

    # ========== 타겟 그룹 설정 ==========
    INITIAL_TARGET_GROUP_IDX: int = 1
    """타겟 그룹 시작 인덱스 (0-based)
    - 이 인덱스부터 마지막 그룹까지를 타겟 그룹으로 설정
    - 예: INITIAL_TARGET_GROUP_IDX=1 → [1, 2, 3, ..., 마지막]
    - 예: INITIAL_TARGET_GROUP_IDX=0 → [0, 1, 2, ..., 마지막]

    ★ INSERT_RANDOM_GROUP 실행 시 자동 업데이트됨
    - 삽입 위치 이후 인덱스 +1 보정
    - 새 그룹 인덱스 맨 뒤에 추가
    """

    FIXED_TARGET_GROUP_IDX_LIST: Optional[list] = None
    """직접 지정하는 타겟 그룹 목록 (0-based)
    - 예: [0, 1] → 그룹 0과 1만 변경, 적은 순서대로 순환
    - None → INITIAL_TARGET_GROUP_IDX부터 마지막 그룹까지
    - 값은 그룹 하나하나의 index (SW 분기 그룹도 그룹마다 따로 지정)
    - 함께 쓰는 모드: FIXED_TARGET_GROUP_ALLOWED_MODES
      (그룹 수, 순서, iteration 구간을 그대로 두는 모드)
    - 목록에 SW 분기 그룹이 있으면 MUTATE_MATRIX(10)와 MUTATE_CSW(11)만 사용
    - 값과 모드는 Validate_Config가 시작할 때 검사
    """

    # ========== GenLLRMode 시퀀스 ==========
    Gen_LLR_Mode_SEQUENCE: List[GenLLRMode] = [
        GenLLRMode.GEN_INITIAL_GROUP,     # 모든 그룹을 새 그룹 하나로 교체 (stage 1에서만 돎)
        GenLLRMode.MUTATE_MATRIX,         # CH, TH 값 변이
        GenLLRMode.MUTATE_CSW,            # CSW 값 변이
        GenLLRMode.SWAP_ROW,              # 그룹 안 두 row의 값 맞바꾸기
        GenLLRMode.REORDER_GROUP,         # 그룹 순서 재배열
        GenLLRMode.COPY_ROWS,             # 다른 row의 값 복사
        GenLLRMode.COPY_GROUP,            # 다른 그룹의 row 복사
        GenLLRMode.INSERT_RANDOM_GROUP,   # 난수 그룹 삽입
        GenLLRMode.INSERT_RANDOM_ROW,     # 난수 row 삽입
        GenLLRMode.INSERT_MUTATED_GROUP,  # 기존 그룹을 변이해 삽입
        GenLLRMode.INSERT_MUTATED_ROW,    # 기존 row를 변이해 삽입
        GenLLRMode.REGEN_DV,              # DV 하나의 값 재생성
        GenLLRMode.REGEN_ROW,             # row 하나의 값 재생성
        GenLLRMode.SPLIT_GROUP,           # 그룹의 iteration을 둘로 분할
        GenLLRMode.ADJUST_ITERATION,      # 그룹 사이 iteration 재분배
        GenLLRMode.DELETE_ROW,            # row 삭제
        GenLLRMode.INSERT_RESTART_GROUP,  # restart 그룹 삽입
    ]
    """최적화 모드 실행 순서 (쓸 수 있는 모드를 모두 적은 목록. 돌릴 모드만 남긴다)
    - Stage 1은 목록의 첫 모드, Stage 2는 둘째 모드, 끝까지 가면 처음으로 돌아감
    - 타겟에 SW 분기 그룹이 있으면 MUTATE_MATRIX와 MUTATE_CSW만 남김 (다른 모드가 있으면 시작할 때 오류)
    - 매트릭스에 SW 분기 그룹이 있으면 GEN_INITIAL_GROUP을 뺌 (시작할 때 오류)
    - FIXED_TARGET_GROUP_IDX_LIST와 함께 쓰면 FIXED_TARGET_GROUP_ALLOWED_MODES의 모드만 남김
    """

    # HBF 최적화 시퀀스 (별도)
    Gen_LLR_Mode_HBF_SEQUENCE: List[GenLLRModeHBF] = [
        GenLLRModeHBF.INSERT_RANDOM_ROW,
        GenLLRModeHBF.MUTATE_MATRIX,
        GenLLRModeHBF.MUTATE_CSW,
        GenLLRModeHBF.SPLIT_GROUP,
        GenLLRModeHBF.COPY_GROUP,
        GenLLRModeHBF.SWAP_ROW,
        GenLLRModeHBF.COPY_ROWS,
        GenLLRModeHBF.REGEN_DV,
        GenLLRModeHBF.REGEN_ROW,
    ]
    """HBF 최적화 모드(IS_HBF_OPT)의 시퀀스 (돌릴 모드만 남긴다)
    - GenLLRModeHBF의 모드 11개에서 GEN_INITIAL_GROUP과 INSERT_RANDOM_GROUP을 뺀 9개
    - GenLLRModeHBF에 없는 모드: REORDER_GROUP, INSERT_MUTATED_GROUP, INSERT_MUTATED_ROW,
      ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP
    - 위 Gen_LLR_Mode_SEQUENCE의 세 가지 제한이 똑같이 걸림
    - trial의 row는 iteration 구간 하나 안에 머물러야 함 (경계 기본값 4와 8). 걸치는 trial은 버려짐
    - 뺀 두 모드는 새 그룹을 만들며, 기본 설정값에서는 그 그룹이 경계를 걸쳐 trial이 버려짐.
      쓰려면 아래 조건을 맞추고 목록에 이름을 적음 (GEN_INITIAL_GROUP은 맨 앞에)
      - GEN_INITIAL_GROUP: GEN_INITIAL_GROUP_CONFIG.ITERATION(기본 20)이 4 이하일 때만 통과
      - INSERT_RANDOM_GROUP: 새 그룹과 뒤로 밀린 그룹이 경계를 걸치지 않을 때만 통과
        (INSERT_GROUP_NUM_ITERATION 기본 20은 iteration 1~8의 그룹 뒤에서 모두 버려짐)
    """

    # ========== 실행 모드 설정 ==========
    RUN_DAO_MODE: RunDAOMode = RunDAOMode.RUN_OPTIMIZATION
    """DAO 실행 모드
    - RUN_OPTIMIZATION: 정상 최적화
    - TEST_FER: 초기 매트릭스 FER 테스트 후 종료
    - SAVE_UNCOR: 초기 매트릭스로 uncor 저장 후 종료
    - REDECODE: uncor 로드 후 다시 저장하고 종료
    - GEN_SINGLE_ROW: 단일 row 후보 생성, 테스트, ranking
    """

    INITIAL_MATRIX_IDX_LIST: Optional[list] = None
    """복수 매트릭스 인덱스 (TEST_FER, SAVE_UNCOR, REDECODE 전용)
    - None이면 INITIAL_MATRIX_IDX 하나만 처리
    """

    # ========== 기타 설정 ==========
    IS_HBF_OPT: bool = False
    """HBF (Hybrid Bit Flipping) 최적화 모드
    - True: Gen_LLR_Mode_HBF_SEQUENCE 사용 (HD 복호, init_n 1에서만 켜짐)
    - False: Gen_LLR_Mode_SEQUENCE 사용
    - uncor 사용과 테스트 방식(seed 모드, Two-Stage 테스트)은 두 값에서 같음
    - True일 때 매트릭스가 지킬 것 (DAO_spec.md 3.6절, 입력과 trial 모두)
      - iteration 1~HBF_MAX_ITERATION(4)의 row는 dv_idx 0의 TH가 HBF_OPT_TH_CONSTANT_VAL(0)
      - row는 iteration 구간 하나 안에 머묾 (경계는 HBF_OPT_CONFIG.ITERATION_SPAN_ENDS,
        기본 4와 8이라 구간은 1~4, 5~8, 9 이후)
      - 입력 매트릭스가 어기면 시작할 때 "Initial LLR matrix validation failed."로 멈춤
    - RUN_DAO_MODE가 GEN_SINGLE_ROW이면 False로 둠 (후보 row가 iteration 1~CANDIDATE_ITERATION
      하나라 경계를 걸침. True이면 시작할 때 오류)
    """

    MAX_RUN_ECC_ERRORS: int = 5
    """RUN_ECC 오류 최대 허용 횟수"""
```

#### 4.1.2 REFC_CONFIG (ECC 실험 설정)

```python
class REFC_CONFIG:
    # ========== ECC 버전 ==========
    ECC_VER: str = "3.0"
    """ECC 코드 버전
    - 3.0: 3D NAND
    - 5G_LDPC_BG1: 5G LDPC Base Graph 1
    - 5G_LDPC_BG2: 5G LDPC Base Graph 2
    - 등등...
    """

    init_n: int = 1
    """디코더 모드
    - 1: HD (Hard Decision)
    - 2: 2SD (2-bit Soft Decision)
    - 3: 3SD (3-bit Soft Decision)
    """

    # ========== 테스트 종료 조건 ==========
    fn: int = 3
    """최소 Frame Error 수
    - FE 개수가 fn 이상이면 테스트 종료
    - FER = NUM_FE / NUM_FRAME
    """

    max_num_test: int = 1000
    """최대 Frame 수
    - Frame 개수가 max_num_test에 도달하면 테스트 종료
    - FE가 충분하지 않아도 종료
    """

    # ========== 채널 파라미터 ==========
    ch_type: int = 2
    """채널 타입
    - 1: RBER 모드
    - 2: Fixed Error 모드
    - 3: Strong Error 모드
    """

    RBERs: list[float] = [0.0135]
    """RBER 값 리스트 (ch_type=1일 때)"""

    num_fixed_errs: list[int] = [400]
    """Fixed Error 수 리스트 (ch_type=2일 때)"""

    # ========== 기타 설정 ==========
    NUM_TARGET_CHANNELS: int = 0
    """테스트할 채널 개수 (ch_type에 따라 자동 설정)"""

    MAX_DECODING_ITERATION: int = 1500
    """LDPC 디코더 최대 iteration 수"""
```

#### 4.1.3 UNCOR_CONFIG (Uncor 관련 설정)

```python
class UNCOR_CONFIG:
    # ========== Two-Stage 테스트 설정 ==========
    ENABLE_TWO_STAGE_TEST: bool = False
    """Two-Stage(Dynamic Partial) 테스트 활성화
    - False: Full 테스트만 수행
    - True: 초기 Full 테스트의 실패 uncor로 Partial 풀을 만들고, Partial에서 개선된 시도만 Full 테스트
    """

    # ========== Uncor 디렉토리 인덱스 ==========
    UNCOR_MATRIX_IDX: int = -1
    """Input uncor 폴더 번호 (Two-Stage 여부와 무관하게 Full uncor 위치)
    - -1: Uncors/{HD,2SD,3SD}/ 바로 아래
    - >=0: Uncors/{HD,2SD,3SD}/LLR_MATRIX_{idx}.txt/ 아래
    """

    # ========== Load Vector 설정 ==========
    ENABLE_LOAD_VECTOR: bool = False
    """seed(.txt) 대신 uncor vector(.dat)를 로드"""

    IS_TLC: bool = True
    """TLC 여부 (LEN_NO_PS 계산에 사용)"""

    LEN_NO_PS: int = 0
    """vector 한 개의 길이 (LOAD_VECTOR일 때 자동 계산)"""

    # ========== 종속성 있는 변수들 ==========
    NUM_LINES_PER_UNCOR: int = 1
    """Uncor 파일당 라인 수 (LOAD_VECTOR일 때 자동 계산)"""

    LOAD_UNCOR_MODE: DAOLoadUncorMode = DAOLoadUncorMode.DEFAULT
    """초기 uncor 로드 모드. Update_Exit_After_Run_Configs가 RUN_DAO_MODE에 따라 정한다
    - RUN_OPTIMIZATION: LOAD_SEED (ENABLE_LOAD_VECTOR가 True면 LOAD_VECTOR)
    - TEST_FER, SAVE_UNCOR: LOAD_NONE
    - REDECODE, GEN_SINGLE_ROW: LOAD_SEED
    """
```
#### 4.1.4 SPEED_TEST_REFC_CONFIG (코어 속도 테스트 설정) - 신규 클래스

```python
class SPEED_TEST_REFC_CONFIG(REFC_CONFIG):
    """Core 속도 측정용 RefC 설정

    REFC_CONFIG를 상속받아 기본값은 유지하되,
    speed test에 필요한 파라미터만 override한다.
    """
    ENABLE_CORE_SPEED_TEST: bool = True
    """코어 속도 테스트 활성화
    - True: Setup 완료 후 코어 속도 사전 측정
    - False: 속도 측정 스킵
    """

    CORE_SPEED_CUTOFF_RATIO: float = 2.0
    """평균 대비 몇 배 느리면 제외할지
    - 2.0: 평균의 2배 이상 느린 코어 제외
    - 각 코어마다 자신을 제외한 평균과 비교
    """

    fn: int = 50
    """속도 테스트용 Frame Error 수 (빠른 종료)"""

    max_num_test: int = 50
    """속도 테스트용 최대 Frame 수"""

    ch_type: int = 1
    """RBER 모드로 고정"""

    RBERs: list[float] = [0.1]
    """속도 테스트용 RBER 값"""

    num_fixed_errs: list[int] = [0]
    """Fixed Error는 사용 안 함"""

    mode_seed: int = 0
    """시드 모드"""

    mode_init_seed: int = CORE_SPEED_TEST_SEED
    """고정 시드 9999 사용 (모든 프로세스 동일 조건)"""
```

#### 4.1.5 PRINT_LOG_CONFIG (로그 출력 설정) - 신규 클래스

```python
class PRINT_LOG_CONFIG:
    """로그 출력 관련 설정"""

    ENABLE_TEST_OPTIMAL_LLR_MATRIX_PRINT_CSW_LOG: bool = True
    """최적 LLR 매트릭스 test 시 CSW 로그 출력 여부"""

    ENABLE_PRINT_ALL_ITER_FERs: bool = True
    """True 시 모든 iteration의 FER 출력"""
```

#### 4.1.6 TIME_CONFIG (시간 제한 설정) - 신규 클래스

```python
class TIME_CONFIG:
    """시간 제한 관련 설정"""

    MAX_STAGE_TIME_SECONDS: int = 2 * 60 * 60
    """Stage별 최대 실행 시간 (초 단위)
    - 기본값: 2시간
    - 100시간 이상이면 제한 없음과 동일
    """

    MPI_COMM_TIMEOUT_SECONDS: int = 1 * 60 * 60
    """MPI 통신 타임아웃 (초 단위)
    - 기본값: 1시간
    - 100시간 이상이면 타임아웃 없음과 동일
    """
```

#### 4.1.7 DEBUG_CONFIG (디버그 설정)

```python
class DEBUG_CONFIG:
    """디버그 모드 설정"""

    ENABLE_DEBUG_MODE: bool = False
    """디버그 모드 활성화 여부
    - True: 아래 모든 디버그 옵션 활성화
    - False: 프로덕션 모드
    """

    # ENABLE_DEBUG_MODE=True일 때
    if ENABLE_DEBUG_MODE:
        ENABLE_MPI_DEBUG_LOGGING = True
        ENABLE_FILE_BREAKPOINT = True
        ENABLE_UPDATE_LOG = True
        ENABLE_SAVE_ALL_TRIAL_LLR_MATRIX = True
    else:
        ENABLE_MPI_DEBUG_LOGGING = False
        ENABLE_FILE_BREAKPOINT = False
        ENABLE_UPDATE_LOG = False
        ENABLE_SAVE_ALL_TRIAL_LLR_MATRIX = False
```

#### 4.1.8 PATH_CONFIG (경로 설정)

```python
class PATH_CONFIG:
    # ========== 기본 디렉토리 ==========
    BASE_DIR_PATH: str = ""
    """프로젝트 루트 경로 (자동 설정)"""

    INPUT_DIR_PATH: str = ""
    """입력 파일 디렉토리
    - LLR 매트릭스: Input/Ref_C/{ECC_NAME}/Initial_LLR_matrix/{HD,2SD,3SD}/
    - Uncor: Input/Ref_C/{ECC_NAME}/Uncors/{HD,2SD,3SD}/
    """

    WORK_SPACE_DIR: str = ""
    """작업 공간 디렉토리
    - 임시 파일, uncor 복사본 등
    - Work_Space/{HD,2SD,3SD}/
    """

    # ========== 파일명 템플릿 ==========
    LLR_MATRIX_FILE_NAME_TEMPLATE: str = "LLR_MATRIX_{matrix_idx}.txt"
    """LLR 매트릭스 파일명 형식
    - 예: LLR_MATRIX_999.txt
    - {matrix_idx}가 실제 인덱스로 치환됨
    """

    LOCAL_SESSION_DIR_NAME_TEMPLATE: str = "Process_{process_idx}"
    """프로세스별 세션 디렉토리명 형식"""

    # ========== 동적 설정 (Update_Path_Configs에서 계산) ==========
    ECC_NAME: str = ""
    """ECC 이름 (ECC_NAME_TEMPLATE 기반 생성)
    - 예: Prime_ECC_3.0
    - Update_Path_Configs()에서 ECC_NAME_TEMPLATE.format(ecc_ver=REFC_CONFIG.ECC_VER)로 설정
    """

    ECC_DIR_NAME: str = ""
    """ECC 디렉토리명 (ECC_NAME과 동일)"""

    INPUT_ECC_DIR_PATH: str = ""
    """ECC 입력 디렉토리
    - 예: Input/Ref_C/Prime_ECC_3.0/
    """

    INPUT_UNCOR_DIR_PATH: str = ""
    """Uncor 입력 디렉토리
    - 예: Input/Ref_C/Prime_ECC_3.0/Uncors/
    """
```

#### 4.1.9 GenLLRMode별 상세 설정

##### MUTATE_CONFIG (MUTATE_MATRIX, MUTATE_CSW)
```python
class MUTATE_CONFIG:
    NUM_ELEMENTS_TO_MUTATE_CHTH: int = 3
    """MUTATE_MATRIX에서 변이할 CH/TH 개수"""

    NUM_ELEMENTS_TO_MUTATE_CSW: int = 1
    """MUTATE_CSW에서 변이할 CSW 개수"""

    MUTATION_RANGE: int = 5
    """변이 범위 (±MUTATION_RANGE)"""

    ENABLE_CSW_UPDATE_LIMIT: bool = False
    """CSW 업데이트 제한 활성화
    - True: CSW를 CSW_UPDATE_LIMIT_VALUE 이하로 제한
    - False: MAX_CSW(1408)까지 허용
    """

    CSW_UPDATE_LIMIT_VALUE: int = 128
    """CSW 최대값 (ENABLE_CSW_UPDATE_LIMIT=True 시)"""
```

##### INSERT_RANDOM_GROUP_CONFIG (INSERT_RANDOM_GROUP)
```python
class INSERT_RANDOM_GROUP_CONFIG:
    INSERT_GROUP_NUM_ROWS: int = 3
    """삽입할 그룹의 행 개수"""

    INSERT_GROUP_NUM_ITERATION: int = 20
    """삽입할 그룹의 iteration 수"""

    ENABLE_INSERT_RESTART: bool = True
    """Restart 그룹 함께 추가
    - True: restart 그룹 + 일반 그룹 (2개 삽입)
    - False: 일반 그룹만 (1개 삽입)
    - init_n=1(HD)일 때는 자동으로 False
    """
```

##### REGEN_DV_CONFIG (REGEN_DV)
```python
class REGEN_DV_CONFIG:
    """타겟 그룹의 특정 row, 특정 DV만 랜덤 재생성"""

    ENABLE_FIX_IDX: bool = False
    """True일 때 고정 인덱스 사용"""

    FIXED_ROW_IDX: int | list[int] = -1
    """-1: 전체 순회 | 정수: 단일 row 고정 | 리스트: 특정 rows만"""

    FIXED_DV_IDX: int | list[int] = -1
    """-1: 전체 순회 | 정수: 단일 dv 고정 | 리스트: 특정 dvs만"""
```

##### REGEN_ROW_CONFIG (REGEN_ROW)
```python
class REGEN_ROW_CONFIG:
    """타겟 그룹의 특정 row 전체를 랜덤 재생성"""

    ENABLE_FIX_IDX: bool = False
    """True일 때 고정 인덱스 사용"""

    FIXED_ROW_IDX: int | list[int] = -1
    """-1: 전체 순회 | 정수: 단일 row 고정 | 리스트: 특정 rows만"""
```

### 4.2 DAO_Constants.py 주요 상수

#### 4.2.1 RunDAOMode Enum
```python
class RunDAOMode(IntEnum):
    RUN_OPTIMIZATION = 0            # 정상 최적화 모드
    TEST_FER = 1                    # 초기 매트릭스 FER 테스트 후 종료
    SAVE_UNCOR = 2                  # 초기 매트릭스로 uncor 저장 후 종료
    REDECODE = 3                    # uncor 로드 후 다시 저장하고 종료
    GEN_SINGLE_ROW = 4              # 단일 row 후보 생성 + 테스트 + ranking
```

#### 4.2.2 DAOLoadUncorMode Enum (단순화)
```python
class DAOLoadUncorMode(IntEnum):
    DEFAULT = -1
    LOAD_NONE = 0           # Do not load uncor seed/vector
    LOAD_SEED = 1           # Load uncor seed (EXTEND 옵션 제거)
    LOAD_VECTOR = 2         # Load uncor vector (EXTEND 옵션 제거)
```

#### 4.2.3 주요 상수값
```python
MAX_CSW = 1408          # 최대 CSW 값 (1024 → 1408로 변경)
MIN_CSW = 8             # 최소 CSW 값
STEP_CSW = 8            # CSW 증감 단위

CORE_SPEED_TEST_SEED = 9999  # 코어 속도 테스트용 고정 시드 (신규)

# 경로 템플릿 (신규)
ECC_NAME_TEMPLATE = "Prime_ECC_{ecc_ver}"  # ECC 디렉토리명 템플릿
```

### 4.3 설정 예시

#### 4.3.1 빠른 스크리닝 설정
```python
# DAO_Config.py
class DAO_CONFIG:
    MAX_OPTIMIZATION_STAGE = 10         # 짧은 최적화
    MAX_GEN_RETRY_PER_TRIAL = 3         # 적은 재시도
    INITIAL_TARGET_GROUP_IDX = 1        # 단일 그룹만

    Gen_LLR_Mode_SEQUENCE = [
        GenLLRMode.MUTATE_MATRIX,
        GenLLRMode.MUTATE_CSW,
        GenLLRMode.COPY_ROWS,
    ]  # 핵심 모드만

class UNCOR_CONFIG:
    ENABLE_TWO_STAGE_TEST = True        # Two-Stage 활성화
    UNCOR_MATRIX_IDX = 102              # Full uncor 폴더 번호

class REFC_CONFIG:
    fn = 50                             # 낮은 FE 목표
    max_num_test = 100                  # 적은 프레임
```

#### 4.3.2 정밀 최적화 설정
```python
# DAO_Config.py
class DAO_CONFIG:
    MAX_OPTIMIZATION_STAGE = 1000       # 긴 최적화
    MAX_GEN_RETRY_PER_TRIAL = 10        # 많은 재시도
    INITIAL_TARGET_GROUP_IDX = 0        # 모든 그룹

    Gen_LLR_Mode_SEQUENCE = [
        GenLLRMode.MUTATE_MATRIX, GenLLRMode.MUTATE_CSW, GenLLRMode.SWAP_ROW,
        GenLLRMode.COPY_ROWS, GenLLRMode.COPY_GROUP,
        GenLLRMode.INSERT_RANDOM_GROUP, GenLLRMode.INSERT_RANDOM_ROW,
        GenLLRMode.REGEN_DV, GenLLRMode.REGEN_ROW,
    ]  # 값, row, 그룹을 바꾸는 모드를 차례로

class UNCOR_CONFIG:
    ENABLE_TWO_STAGE_TEST = False       # Full 테스트만
    UNCOR_MATRIX_IDX = 10

class REFC_CONFIG:
    fn = 200                            # 높은 FE 목표
    max_num_test = 5000                 # 많은 프레임
```

#### 4.3.3 디버그 설정
```python
# DAO_Config.py
class DAO_CONFIG:
    RUN_DAO_MODE = RunDAOMode.TEST_FER

class DEBUG_CONFIG:
    ENABLE_DEBUG_MODE = True            # 디버그 모드
    # 자동으로 모든 디버그 옵션 활성화

class REFC_CONFIG:
    fn = 10                             # 빠른 종료
    max_num_test = 100
```

---

## 부록

### A. 주요 에러 메시지 및 해결

| 에러 메시지 | 원인 | 해결 방법 |
|------------|------|----------|
| `There is no initial LLR matrix` | 초기 매트릭스 파일 없음 | `Input/Ref_C/{ECC_NAME}/Initial_LLR_matrix/{HD,2SD,3SD}/LLR_MATRIX_{idx}.txt` 확인 |
| `TARGET_GROUP_IDX must define at least one index` | 타겟 그룹 인덱스 비어있음 | [DAO_Config.py:35](DAO/SRC/DAO_Config.py#L35)에서 `INITIAL_TARGET_GROUP_IDX` 설정 |
| `Gen_LLR_Insert_Random_Group: Matrix must not be None` | 매트릭스 초기화 실패 | Run_Initial_Test 로그 확인 |
| `MPI_Abort` 호출 | 치명적 에러 발생 | 로그 파일의 에러 메시지 확인 |

### B. 로그 파일 위치

```
Output/{session}/Process_{rank}/
├── 1_Log/
│   └── Log.txt             # 전체 실행 로그
├── 2_Optimal_LLR_matrix/   # Optimal 매트릭스
│   └── LLR_MATRIX_{idx}.txt
├── 3_Trial_LLR_matrix/     # Trial 매트릭스 (옵션)
└── 5_Uncors/               # Uncor 파일
```

### C. Uncor를 Input에 저장하는 구조

**Update_Uncors_To_Input** ([DAO_Main.py](DAO/SRC/DAO_Main.py))

`RUN_DAO_MODE`가 SAVE_UNCOR 또는 REDECODE이면 테스트가 끝난 뒤 세션의 `5_Uncors/Redecoded_uncors/{매트릭스 파일 이름}/`에 모인 파일을 Input으로 복사한다. 기존 파일은 그대로 두고 실행마다 타임스탬프 폴더를 새로 만든다.

**저장 구조:**
```
Input/Ref_C/Prime_ECC_3.0/Uncors/2SD/LLR_MATRIX_200.txt/
├── uncor_log.txt                          # 저장 이력 (위치, Line 수, 시각)
├── Recoded_uncors_20260921_143025/        # 첫 번째 실행
│   ├── uncor_seed_..._init_n_2_0.txt
│   └── LLR_MATRIX_200.txt                 # 이 uncor를 만든 매트릭스
└── Recoded_uncors_20260921_150312/        # 두 번째 실행
    └── ...
```

**저장 로직:**
- ㉮ `Recoded_uncors_{YYYYMMDD_HHMMSS}/` 폴더를 만든다
- ㉯ `Redecoded_uncors/{매트릭스 파일 이름}/` 아래 파일을 그대로 복사한다 (`uncor_log.txt`는 제외)
- ㉰ `uncor_log.txt`에 저장 위치, Line 수, 시각을 덧붙인다
- ㉱ 최적화 입력으로 쓰려면 uncor 파일을 `LLR_MATRIX_{UNCOR_MATRIX_IDX}.txt/` 바로 아래로 옮긴다 (3.2.3절)
### D. 참고 파일

- [CLAUDE.md](CLAUDE.md): 프로젝트 개요 및 Claude Code 가이드
- [DAO_Constants.py](DAO/SRC/DAO_Constants.py): Enum 정의 (GenLLRMode, TestMode 등)
- [DAO_Config.py](DAO/SRC/DAO_Config.py): 모든 설정 클래스 정의
- [DAO_Main.py](DAO/SRC/DAO_Main.py): 메인 최적화 엔진
- [DAO_LLR_MATRIX.py](DAO/SRC/DAO_LLR_MATRIX.py): LLR 매트릭스 데이터 구조

---

**작성일:** 2026-02-06
**버전:** 2.1
**업데이트:** 최신 변경사항 반영
- 타겟 그룹 설정 변경 (INITIAL_TARGET_GROUP_IDX)
- 실행 모드 통합 (RunDAOMode Enum)
- UNCOR_CONFIG 클래스 신규 분리
- SPEED_TEST_REFC_CONFIG 신규 추가 (코어 속도 테스트)
- PRINT_LOG_CONFIG, TIME_CONFIG 신규 추가
- MAX_CSW 값 1408로 변경
- DAOLoadUncorMode 단순화
- 변수 이름 변경 (MAX_RUN_ECC_ERRORS, MAX_OPTIMIZATION_TRIALS 등)
- **ECC_NAME_TEMPLATE 템플릿화** (DAO_Constants.py)
- **경로 설정 개선** (PATH_CONFIG 동적 설정)
- **Uncor 저장 구조** (Recoded_uncors 타임스탬프 폴더)
