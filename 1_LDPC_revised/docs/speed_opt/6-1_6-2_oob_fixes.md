# 6-1 / 6-2. 잠재 버그 수정 — heap 범위 밖 접근 2건

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (사용자 승인 후 진행) |
| 파일 | `1_LDPC_revised/decoder.cpp` (`PMU_Read` / `PMU_Read_HCU` / `DU_Manager`) |
| 분류 | 성능 아님 — UB(범위 밖 접근) 제거. 단 6-1은 clk당 낭비 루프 제거 부수 효과 있음 |
| 결과 영향 | **golden과 달라질 수 있음** (아래 "영향 범위 정밀 분석" 참조). 달라진다면 기존 코드가 쓰레기값을 읽고 있었다는 뜻이므로 **새 값이 올바른 값** |
| 적용 시점 | **다른 모든 항목을 끝내고 맨 마지막에.** 1단계(순수 최적화)와 커밋을 반드시 분리 — 섞으면 불일치 원인 분리가 불가능 |

## ⚠ 영향 범위 정밀 분석 (2026-07-23 코드 추적 결과)

"최종 FER가 같아도 중간값이 다르면 안 된다"는 요구에 따라 타이밍·중간 상태 경로를 전수 추적한 결과다.
**결론: 타이밍(`overall_clk`)에는 영향이 없고, 결과가 달라질 수 있는 경로는 6-2에 딱 한 곳 있다.**

### 6-1은 타이밍에 영향을 줄 수 없다 (구조적으로)

`MAIN_SRAM_read_rq`를 읽는 곳은 `Clk_Manager()`와 `Clk_Delay_REG()` 두 곳뿐인데, **둘 다 루프 상한이
`factor × MAX_DV_GLOBAL_HALF = 0`이라 한 번도 돌지 않는다.** 따라서:

- `Clk_Manager`의 `insert_idle`이 TRUE가 될 수 없음 → `cnt_idle_cycle`이 2가 될 수 없음
  (`cnt_idle_cycle = 2`를 만드는 곳은 `Clk_Manager` **한 곳뿐**임을 grep으로 확인)
- → idle cycle이 삽입되지 않음 → **`overall_clk` 불변**
- → `col_M1`이 `CYCLE_IDLE`이 되는 경로도 발동하지 않음

**그럼 6-1의 진짜 위험은 무엇이었나 — heap 손상이다.** 기존 코드는 `MAIN_SRAM_read_rq[n] = TRUE`를
**길이 0 배열에 최대 20개(n ≤ 19)** 썼다. 할당 순서가

```
FIFO_level[0] → MAIN_SRAM_read_rq[0] → MAIN_SRAM_read_rq2[0] → MAIN_SRAM_write_rq[0] → Soft_LLR[N] → ...
```

이므로, 80바이트를 넘겨 쓰면 **뒤따르는 할당(실사용 배열 `Soft_LLR` 포함)의 heap 블록을 침범**할 수 있다.
즉 golden(원본 바이너리)이 오염된 값으로 돌고 있었을 가능성이 있고, 이 경우 수정본과 결과가 달라진다.

### 6-2에서 결과가 달라질 수 있는 유일한 지점

`DU_flag_*` 사용처를 전수 확인한 결과 대부분은 안전하다:

| 사용처 | 판정 |
|--------|------|
| `DU_flag_Z` | `Clk_Valid_Col(PHASE_Z)` 안에서만 사용 → col 범위 밖이면 아무 동작 없음. **안전** |
| `DU_flag_P2` | `Clk_Valid_Col(PHASE_P2)` 안 → **안전** |
| `DU_flag_M1` (`Clk_Set_Col`) | `col_M1 == CYCLE_END`가 **앞 분기에서 먼저** 걸러진 뒤에만 사용. `col_M1`은 0에서 시작해 음수가 되지 않음(CYCLE_IDLE 경로는 위 이유로 미발동). **안전** |
| `col = N_b-1`인 모든 경우 | 기존에도 맨 뒤 범위 검사에서 FALSE로 확정됐음 → **결과 동일**, OOB 읽기만 제거됨 |
| **`DU_flag_P4`** | **⚠ 위험 — 아래** |

`decoder.cpp`의 P4 처리 블록:

```cpp
if (Clk_Valid_Col(PHASE_P2) || Clk_Valid_Col(PHASE_P4) || (CYCLE_END == col_P2)) {   // OR 조건
    if ((col_P4 != CYCLE_IDLE) && (col_P4 != CYCLE_BEFORE_START)) {   // ← CYCLE_END(-2)는 안 걸러짐!
        ...
        if (TRUE == DU_flag_P4) {
            V2C_Store(prev_variable_node2, FALSE);
            V2C_Store(prev_variable_node2 + 1, FALSE);   // ← 컬럼을 2개 처리
        }
```

`col_P4 == CYCLE_END(-2)`인 clk에 이 블록이 실행되는데, 그때 `DU_flag_P4`는:

- **기존**: `ColW[-2]`, `ColW[-1]`(= heap 블록 헤더 영역) 쓰레기값으로 판정 → 값이 우연히 `DV_2 ~ DV_5`
  범위에 들어가면 **TRUE → 컬럼 2개 저장**(디코더 상태가 실제로 달라짐)
- **수정 후**: `col_P4 >= 0` 검사에 걸려 **결정적으로 FALSE → 컬럼 1개**

실무적으로 heap 헤더는 보통 큰 값이라 FALSE가 나올 가능성이 높지만 **보장은 없다**. 6-1/6-2 적용 후
결과가 달라졌다면 최우선 확인 대상이 이 지점이다.

## 검증 순서 (권장)

1. **6-1/6-2를 뺀 상태**(이 저장소 기준 `96509fe`)로 golden diff → **FER·iter·uncor·overall_clk·TV hex가 완전 일치해야 함.** 불일치 = 최적화 항목의 적용 실수
2. 그다음 6-1/6-2를 얹어 재비교 → 차이가 나면 기존 UB가 실제로 결과에 영향을 주고 있었던 것 (새 값이 정답)
3. 차이가 났다면 **6-1만 / 6-2만** 각각 얹어 원인 분리. 6-2 쪽이면 위 `DU_flag_P4` 경로를 확인

## 6-1. `PMU_Read()` / `PMU_Read_HCU()` 범위 밖 읽기·쓰기

**버그**: 할당은 factor(= z_sb / PMU_UNIT_SIZE = 32/128 = **0**)를 반영해
`PMU_SRAM[i] = new int[factor × … × PMU_UNIT_WIDTH]` → **길이 0**, `MAIN_SRAM_read_rq = new int[factor × …]` → **길이 0**.
그런데 읽기 함수들은 factor 대신 **하드코딩 2**(z_sb=256 시절의 fragment 수)를 사용:

- `PMU_Read`: `sram_inst_num = 2 * MAX_DV_GLOBAL_HALF` → 매 clk 최대 offset 159까지 `PMU_SRAM` **OOB 읽기** + `MAIN_SRAM_read_rq[n]` (n ≤ 19) **OOB 쓰기** (heap 오염 가능)
- `PMU_Read_HCU`: `sram_inst_num = 2 * MAX_DV_GLOBAL` (34) 등 동일 패턴 — 체크리스트에는 PMU_Read만 있었으나 적용 중 동일 버그 발견하여 함께 수정

호출 위치는 메인 clk 루프(col_Z 스테이지) — **매 clk 발생**하던 UB.

**수정**: 두 함수에 `int factor = m_PCM->z_sb / PMU_UNIT_SIZE;`를 선언하고 하드코딩 2를 factor로 교체 (할당식과 동일 구조). 현 파라미터에서 factor=0 → 루프 0회로 자연 해소 + clk당 낭비 루프 제거. factor=2인 구성(z_sb=256)에서는 기존과 완전 동일 동작.

**주의(이식)**: 내부의 `mux_idx = n / 2; fragment = n % 2;` 분해는 여전히 fragment 수 2를 가정 — factor=1인 구성(z_sb=128)을 실제로 쓸 경우 별도 재검토 필요 (현재/기존 구성 모두 해당 없음).

## 6-2. `DU_Manager()` 범위 밖 읽기

**버그**: 6개 블록(col_M1/Z/P1/P2/P3/P4 각각)이 모두
```cpp
if ((ColW[col] ...) && (ColW[col + 1] ...) && (col + 1 < N_b))
```
형태 — `&&`는 좌→우 평가이므로 **범위 검사가 맨 뒤에 있어 보호가 안 됨**:
- col이 파이프라인 sentinel(`CYCLE_BEFORE_START = -3`, `CYCLE_IDLE = -1`)일 때 `ColW[-3]` 등 **음수 인덱스 읽기**
- col = N_b-1일 때 `ColW[N_b]` 읽기 (범위 검사 도달 전)

**수정**: 범위 검사를 맨 앞으로 이동 —
```cpp
if ((col >= 0) && (col + 1 < N_b) && (ColW[col] ...) && (ColW[col + 1] ...))
```
- col = N_b-1: 기존에도 최종 FALSE(마지막 검사에서) → 결과 동일, OOB만 제거
- col < 0: 기존엔 garbage 비교라 **비결정** (우연히 TRUE 가능) → 이제 결정적으로 FALSE (명백한 의도)
- 함수 하단의 대안 구현 세트는 블록 주석 안(비활성)이라 미수정

## 검증

- grep: 활성 코드에서 "범위 검사가 뒤에 오는" 패턴 잔여 0건 (잔여 6건은 전부 블록 주석 안)
- factor 미반영 `2 *` 패턴: PMU_Read/PMU_Read_HCU에서 제거 확인. `n / 2`·`n % 2` 분해는 의도적 유지 (위 주의 참조)
- 중괄호/전처리기 균형: 수정 전후 동일

## 이식 앵커

1. 6-1: 대상 코드의 `PMU_SRAM`/`MAIN_SRAM_read_rq` **할당 길이 식**을 먼저 확인하고, 읽기 함수의 루프 상한이 같은 식(factor 포함)인지 대조 — 다르면 그 차이가 버그
2. 6-1: PMU_Write / PMU_Write_HCU는 fragment 루프가 factor 기반이라 factor=0에서 이미 no-op (2-19 참조) — 수정 불필요, 단 대상 버전에서 재확인
3. 6-2: `DU_Manager`류 함수가 여러 벌(주석 포함) 있을 수 있음 — **활성 코드만** 수정하고 sentinel 값(CYCLE_*)의 실제 정의를 확인할 것
4. 적용 후 동일 seed에서 FER/iter/uncor은 동일해야 하고, overall_clk이 달라졌다면 기존 값이 garbage 의존이었다는 뜻 — 새 값을 기준으로 삼을 것
