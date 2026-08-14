# Two-Stage Test 모드 — Partial → Full 2단계 테스트를 통한 최적화 속도 향상

> 추가일: 2026-04-06 / 대상: DAO 사용자

## 배경 — 왜 필요했나

DAO의 최적화 루프에서 가장 시간이 많이 소요되는 단계는 **LLR Matrix 테스트(FER 측정)**이다.
매 trial마다 전체 uncor pool을 디코딩하여 FER을 계산하는데, uncor 수가 수천~수만 개에 달하면 한 trial의 테스트 시간이 상당하다.

실제 발생하는 문제:

- **대부분의 trial은 개선이 아님**: 변이 생성(Mutation)으로 만든 matrix 후보 중 실제로 FER이 개선되는 경우는 소수. 나머지 대다수 trial에서 Full 테스트를 수행하는 것은 낭비
- **uncor 수 증가 시 비례 증가**: uncor pool이 클수록 trial당 테스트 시간이 선형 증가하여 전체 최적화 시간이 급격히 늘어남
- **필터링 수단 부재**: 개선 가능성이 낮은 후보를 빠르게 걸러낼 방법이 없었음

이 문제를 해결하기 위해 **Partial → Full 2단계 테스트** 방식을 도입했다.

---

## 변경 요약

| # | 항목 | 설명 |
|---|------|------|
| 1 | TestMode enum | PARTIAL(1) / FULL(2) 모드 정의 |
| 2 | Dynamic Partial Pool | Full uncor 중 fail한 것만 추출하여 Partial pool 동적 생성 |
| 3 | 2단계 필터링 | Partial에서 개선된 경우만 Full 테스트 진행 → 비개선 trial 시간 절감 |
| 4 | Partial Pool 재구성 | optimal 갱신 시 Full 재디코딩 → 새 fail uncor로 Partial pool 갱신 |
| 5 | Graceful Stop | Partial=0(전부 성공) → 최적화 목표 달성으로 자동 종료 |

---

## 1. 핵심 개념 — Partial vs Full

```
Full uncor pool: [1000개 uncor seed]
         ↓ optimal matrix로 디코딩
         ↓ fail한 것만 추출
Partial pool:    [150개 fail uncor] ← 이 matrix로 아직 못 푸는 것들
```

- **Full 테스트**: 전체 uncor pool로 FER 측정. 정확하지만 느림
- **Partial 테스트**: fail uncor만으로 FER 측정. 빠르고 개선 탐지에 민감

Partial pool은 정의상 현재 optimal matrix에서 모두 실패하는 codeword이므로 **Partial FER = 1.0**이 baseline이다.
새 matrix 후보가 이 중 일부라도 성공하면 Partial FER < 1.0 → **개선 신호**.

---

## 2. 전체 흐름

### 2.1 초기화 (`Test_Initial_LLR`)

```
[Step 1] Full 테스트 (SAVE 모드) → fail uncor seed 저장
[Step 2] Gather fail uncors → Partial pool 동적 구성
[Step 3] Partial FER = 1.0 설정 (정의상 모두 fail)
[Step 4] Seed mode 복원
```

- SAVE 모드(`LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`)로 Full 테스트하면 디코딩 실패한 codeword가 redecoded uncor로 저장됨
- 이를 Gather하여 `tmp_partial_uncors/`에 보관하고 Partial pool로 분배

### 2.2 Trial 테스트 (`Test_Trial_LLR`)

```
[1단계: Partial] trial matrix로 Partial pool 디코딩
       ↓
  개선됨? ──Yes──→ [2단계: Full] Full pool 디코딩 → Update 판단
       │
       No → Full 스킵 (시간 절감!)
```

- **Partial 개선 판단** (`Check_Partial_Improvement`):
  - `is_update_at_last_trial=True` 모드: temp_optimal과 비교, 마지막 trial은 무조건 Full 진행
  - `is_update_at_last_trial=False` 모드: optimal의 Partial FER과 비교
  - "strictly better" 조건: 모든 채널 A[i] ≤ B[i] 이고 하나 이상 A[i] < B[i]

### 2.3 Optimal 갱신 후 Partial Pool 재구성 (`Rebuild_Partial_Pool`)

optimal matrix가 갱신되면 Partial pool도 재구성해야 한다 (새 optimal로는 기존 fail uncor 중 일부가 성공할 수 있으므로).

```
[Step 1] Seed mode → SAVE 모드
[Step 2] Full uncor 로드
[Step 3] 새 optimal로 Test_LLR (fail codeword 저장)
[Step 4] Gather fail → tmp_partial_uncors 갱신 + Partial pool 재분배
[Step 5] Partial 수 확인 (0이면 graceful stop)
[Step 6] Partial FER = 1.0 재설정
[Step 7] 상태 복원
```

### 2.4 Graceful Stop

모든 Full uncor이 디코딩에 성공하면 Partial = 0 → **최적화 목표 달성**. DAO end flag를 기록하여 optimization loop에서 자연 종료.

---

## 3. 설정

### UNCOR_CONFIG ([DAO_Config.py](DAO/SRC/DAO_Config.py))

```python
ENABLE_TWO_STAGE_TEST: bool = False  # True: 2단계 모드 활성화
UNCOR_MATRIX_IDX: int = -1           # Full uncor 경로 (Two-stage=True일 때 루트 경로)
```

### 비호환 모드 ([DAO_Main.py:9701-9737](DAO/SRC/DAO_Main.py#L9701-L9737))

| 조합 | 이유 |
|------|------|
| REDECODE 모드 | uncor 재디코딩 전용이라 Partial 개념 불필요 |
| GEN_SINGLE_ROW 모드 | 단일 row 생성 전용, 별도 테스트 체계 사용 |
| LOAD_UNCOR_MODE=LOAD_NONE | uncor 없이는 Partial 구성 불가 |
| LOAD_UNCOR_MODE=LOAD_VECTOR | 현재 미지원 (seed 기반만 지원) |
| IS_HBF_OPT=True | HBF 최적화와 비호환 |

### Multi-round 모드 예외 ([DAO_Main.py:9414-9416](DAO/SRC/DAO_Main.py#L9414-L9416))

DELETE_ROW, REORDER_GROUP, INSERT_RESTART_GROUP 등 Multi-round 모드에서는 **항상 Full 테스트만 수행**.
이유: final verification trial에서 Partial 실패 시 temp_optimal → optimal 전환이 누락될 수 있음.

---

## 4. 디렉토리 구조

```
{session}/
├── HD/                          # Full uncor pool (루트)
│   ├── uncor_seed_ch0.txt
│   └── uncor_seed_ch1.txt
├── tmp_partial_uncors/          # Partial pool 소스 (Rebuild 시 갱신)
│   └── {timestamp}/
│       ├── uncor_seed_ch0.txt
│       └── uncor_seed_ch1.txt
└── Local_Session_{rank}/
    ├── uncor_seed_ch0.txt       # Full 분배분
    └── Partial/
        └── uncor_seed_ch0.txt   # Partial 분배분
```

- Full 결과는 루트, Partial 결과는 `Partial/` 서브디렉토리
- `tmp_partial_uncors/`는 Periodic Recheck 재분배 시에도 소스로 활용

---

## 5. 핵심 메서드 맵

| 메서드 | 역할 | 위치 |
|--------|------|------|
| `Test_Initial_LLR()` | 초기 Full 테스트 + Partial pool 구성 | [9146](DAO/SRC/DAO_Main.py#L9146) |
| `_Build_Initial_Partial_Pool()` | fail uncor Gather → Partial pool 생성 | [9208](DAO/SRC/DAO_Main.py#L9208) |
| `Test_Trial_LLR()` | 2단계 필터링 (Partial → Full) | [9400](DAO/SRC/DAO_Main.py#L9400) |
| `Check_Partial_Improvement()` | Partial FER 개선 판단 | [1421](DAO/SRC/DAO_Main.py#L1421) |
| `Rebuild_Partial_Pool()` | optimal 갱신 후 Partial pool 동적 재구성 | [9272](DAO/SRC/DAO_Main.py#L9272) |
| `_Signal_Graceful_Stop_No_Partial()` | Partial=0 → graceful stop | [9378](DAO/SRC/DAO_Main.py#L9378) |
| `_Run_Test_Stage()` | test mode 설정 → uncor 로드 → Test_LLR 일괄 수행 | [9140](DAO/SRC/DAO_Main.py#L9140) |

---

## 6. 상수 및 Enum ([DAO_Constants.py](DAO/SRC/DAO_Constants.py))

```python
class TestMode(IntEnum):
    PARTIAL = 1  # Partial 테스트 (빠른 스크리닝)
    FULL = 2     # Full 테스트 (정확한 평가)

TEST_MODE_DIR_NAME = {
    TestMode.PARTIAL: "Partial",  # Partial은 서브디렉토리 사용
}

TMP_PARTIAL_UNCORS_DIR_NAME = "tmp_partial_uncors"
```
