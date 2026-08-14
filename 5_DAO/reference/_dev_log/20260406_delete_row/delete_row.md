# DELETE_ROW 모드 — Row 삭제를 통한 LLR Matrix 구조 최적화

> 추가일: 2026-04-06 / 대상: DAO 사용자

## 배경 — 왜 필요했나

DAO의 LLR Matrix는 group 내에 여러 row를 가지며, 각 row는 채널별 threshold 값을 정의한다.
최적화 과정에서 row가 추가되는 모드(INSERT_RANDOM_ROW, APPEND_GROUP 등)는 있었지만,
**불필요한 row를 제거하여 구조를 단순화**하는 방법은 없었다.

실제 발생하는 문제:

- **과적합(Overfitting)**: row가 많을수록 매트릭스가 복잡해져, 특정 조건에 과적합될 수 있음
- **중복 row**: 최적화 과정에서 유사한 역할을 하는 row가 누적되어 실질적 개선 없이 테스트 비용만 증가
- **group 축소 불가**: row 추가는 가능하지만 group 내 row를 줄이거나 group 자체를 제거할 방법이 없었음

이 문제를 해결하기 위해 **Multi-round Greedy Deletion** 방식의 DELETE_ROW 모드를 도입했다.

---

## 변경 요약

| # | 항목 | 설명 |
|---|------|------|
| 1 | DeleteRowState 클래스 | Multi-round 상태를 하나의 클래스로 관리, MPI bcast 한 번으로 동기화 |
| 2 | Greedy Deletion 알고리즘 | 각 Round마다 모든 후보를 테스트 → best 확정 → 다음 Round 반복 |
| 3 | Case A/B 분기 처리 | row 단독 삭제 vs group 전체 삭제 + iteration 재분배 |
| 4 | Multi-round 프레임워크 통합 | REORDER_GROUP, INSERT_RESTART_GROUP과 동일한 패턴 적용 |

---

## 1. 핵심 알고리즘 — Multi-round Greedy Deletion

### 동작 흐름

```
[Init] optimal_LLR_matrix 기준 삭제 후보 리스트 생성
  ↓
[Round 0] 모든 후보를 하나씩 삭제 후 테스트 → FER 기준 best 선택
  ↓ (개선 있음)
[삭제 확정] best matrix를 새 baseline으로 설정 → 후보 리스트 재빌드
  ↓
[Round 1] 새 후보로 동일 과정 반복
  ↓ (개선 없음)
[종료] baseline을 final verification으로 반환
```

### 후보 선정 조건

- `target_group_indices` 범위 내의 모든 row (restart group 포함)
- 전체 matrix에 최소 1개 row는 남아야 함 → total_rows ≤ 1이면 스킵

### Trial 수 상한

- 삭제 가능 row 수 N일 때, 최악 N*(N+1)/2
- 예: N=10이면 최대 55 trials (Round 0: 10, Round 1: 9, ...)

---

## 2. 삭제 케이스 — Case A / Case B

row를 삭제할 때 group 내 row 수에 따라 처리 방식이 달라진다.

### Case A: group 내 row 2개 이상 → row만 제거

```
삭제 전: Group[g] = [row0, row1, row2]
삭제 후 (row1 삭제): Group[g] = [row0, row2]
```

- 첫 번째 row(index 0)를 삭제한 경우 → 새로운 첫 row의 CSW를 -1로 설정 (C1 규칙)
- `num_row_each_group[g]` 1 감소

### Case B: group 내 row 1개 → group 전체 삭제 + iteration 재분배

```
삭제 전: [G0(iter 1-5)] [G1(iter 6-8)] [G2(iter 9-15)]
G1 삭제: [G0(iter 1-7)] [G2(iter 8-15)]
         ↑ prev에 ceil(3/2)=2  ↑ next에 floor(3/2)=1
```

**재분배 규칙**:
- 삭제된 group의 iteration duration을 인접 non-restart group에 반씩 분배
- prev만 있으면 prev에 전부, next만 있으면 next에 전부
- 둘 다 없으면 iteration 소실 (나머지가 전부 restart group인 극단 케이스)
- 홀수면 prev에 ceiling, next에 floor

**추가 업데이트**:
- `header.num_group` 1 감소
- `type_each_group`, `num_row_each_group` 배열에서 해당 인덱스 제거
- `restart_groups` 인덱스 시프트 (삭제된 group 이후는 -1)
- `restart_iter` 재빌드
- `max_iteration` 재계산

---

## 3. 상태 관리 — DeleteRowState

MPI 환경에서 모든 rank가 동일한 상태를 유지해야 하므로, 관련 변수를 하나의 dataclass로 묶었다.

```python
@dataclass
class DeleteRowState:
    is_active: bool = False
    current_round: int = 0
    deletable_rows: list = field(default_factory=list)
    current_candidate_idx: int = 0
    round_best_candidate_idx: int = -1
    round_best_matrix: Optional[LLR_MATRIX] = None
    round_baseline_matrix: Optional[LLR_MATRIX] = None
    round_trial_count: int = 0
    total_expected_trials: int = 0
```

**생명주기**: Init에서 생성 → Stage 전체 유지 → Round에서 개선 없거나 삭제 가능 row 없으면 is_active=False

---

## 4. Multi-round 프레임워크 통합

DELETE_ROW는 기존 Multi-round 모드(REORDER_GROUP, INSERT_RESTART_GROUP)와 동일한 패턴으로 통합되어 있다.

### 등록 위치 ([DAO_Constants.py](DAO/SRC/DAO_Constants.py))

| 딕셔너리 | 키 | 값 |
|----------|-----|-----|
| `MULTI_ROUND_MODES` | `GenLLRMode.DELETE_ROW` | `'delete_row_state'` |
| `MULTI_ROUND_UPDATE_FUNC` | `GenLLRMode.DELETE_ROW` | `'Update_Delete_Row_Round_Result'` |
| `MULTI_ROUND_INIT_FUNC` | `GenLLRMode.DELETE_ROW` | `'Init_Delete_Row_Mode'` |

### 핵심 메서드 ([DAO_Main.py](DAO/SRC/DAO_Main.py))

| 메서드 | 역할 | 위치 |
|--------|------|------|
| `Init_Delete_Row_Mode()` | 모드 초기화, 후보 생성, 상한 설정 | [5347](DAO/SRC/DAO_Main.py#L5347) |
| `_Build_Delete_Row_Candidates()` | 삭제 가능 (g_idx, r_idx) 리스트 생성 | [5386](DAO/SRC/DAO_Main.py#L5386) |
| `Gen_LLR_Delete_Row()` | 메인 생성 함수 (while 기반, 재귀 없음) | [5406](DAO/SRC/DAO_Main.py#L5406) |
| `_Build_Deleted_Row_Matrix()` | row 삭제된 새 matrix 생성 (Case A/B) | [5476](DAO/SRC/DAO_Main.py#L5476) |
| `_Delete_Entire_Group()` | Case B: group 삭제 + iteration 재분배 | [5505](DAO/SRC/DAO_Main.py#L5505) |
| `Update_Delete_Row_Round_Result()` | Round 내 best 업데이트 | [5601](DAO/SRC/DAO_Main.py#L5601) |
| `_Finalize_Delete_Row_Round()` | Round 완료 처리 + 다음 Round 준비 | [5641](DAO/SRC/DAO_Main.py#L5641) |

---

## 5. 스펙 ([DAO_spec.md](DAO/DAO_spec.md) Section 5.16)

- **모드 코드**: `GenLLRMode.DELETE_ROW = 70`
- **업데이트 방식**: `is_update_at_last_trial = True` (Round 단위 업데이트)
- **Trial 수 상한**: N*(N+1)/2 (N = 삭제 가능 row 수)
- **종료 조건**: Round 완료 시 개선 없음 또는 삭제 가능 row 없음
