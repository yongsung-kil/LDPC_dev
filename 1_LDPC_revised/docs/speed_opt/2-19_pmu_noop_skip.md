# 2-19. `VNU_out3_temp` 복사 + no-op PMU 경로 스킵

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/decoder.cpp` |
| bit-exact | 현 파라미터(z_sb=32 < PMU_UNIT_SIZE=128)에서 보장. 파라미터 변경 시에도 기존 경로 그대로 실행됨 |
| 위험도 | 중간 (HW 타이밍 시뮬 경로 인접) |

## 왜 해야 하나

`V2C_Store(jj, skip)` / `V2C_Store_HCU()` wrapper는 **컬럼마다** VNU_out3 전체(J×z_sb=544 int)를 `VNU_out3_temp`로 복사한 뒤 `PMU_Write(_HCU)`를 호출한다. 그런데:

- `factor = z_sb / PMU_UNIT_SIZE = 32 / 128 = 0`
- `PMU_Write` 내부의 fragment 루프(`for (fragment = 0; fragment < factor; ...)`)가 **0회 실행** — 본체 확인 결과 fragment 루프 밖에는 상태 변경이 없음 (mux 조회뿐)
- `VNU_out3_temp`의 유일한 소비처가 PMU_Write(_HCU)의 fragment 루프 내부

즉 컬럼당 544 int 복사 + 함수 호출이 완전한 no-op였다.

## 무엇을 어떻게 바꿨나

두 wrapper에서 복사+호출을 런타임 조건으로 감싼다:

```cpp
if (m_PCM->z_sb >= PMU_UNIT_SIZE) {    // factor >= 1인 구성에서만 의미 있음
    for (ii...) memcpy(VNU_out3_temp[ii], VNU_out3[ii], z_sb*sizeof(int));   // (겸사겸사 memcpy화)
    if (FALSE == skip) PMU_Write(...);
}
```

- 현 구성(z_sb=32): 복사·호출 스킵 — 결과/overall_clk 영향 없음 (Clk_Manager FIFO도 factor 비례라 0회)
- z_sb ≥ 128인 미래 구성: 기존과 동일하게 실행 (복사만 memcpy로 빨라짐)

## no-op 확인 (2026-07-23 재검증)

"타이밍 시뮬 경로라 위험"이라는 지적에 따라 스킵 대상의 부작용을 다시 전수 확인했다:

- `PMU_Write()` 본체 구조가 `for (ii < ColW[jj]) { mux_idx = Mux_idx[ii][jj]; for (fragment < factor) { ... } }`
  — **상태를 바꾸는 코드는 전부 안쪽 fragment 루프 안**에 있다 (`PMU_SRAM[...]` 쓰기, `MAIN_SRAM_write_rq[n] = TRUE` 포함).
  바깥 ii 루프는 `mux_idx` 조회뿐이므로 factor=0에서 완전한 no-op
- `VNU_out3_temp`의 읽기 지점은 `PMU_Write` / `PMU_Write_HCU`의 fragment 루프 내부 **2곳뿐** (TV 출력 경로에도 없음)
- 스킵으로 `MAIN_SRAM_write_rq`가 갱신되지 않는 것도 무해 — 이를 읽는 `Clk_Manager()`의 루프 상한이
  `factor × MAX_DV_GLOBAL_HALF = 0`이라 한 번도 돌지 않는다. 즉 `cnt_idle_cycle`이 2가 될 수 없어
  **idle cycle 삽입이 구조적으로 불가능** → `overall_clk` 불변

## 이식 앵커

1. PMU/압축 유닛 크기 상수와 z_sb의 비율(factor)을 확인 — **그 버전에서 factor ≥ 1이면 스킵 조건이 발동하지 않으므로 안전하지만, PMU_Write 본체에 fragment 루프 밖 부작용(통계/clk 카운트)이 있는지 반드시 확인** 후 적용
2. VNU_out3_temp의 소비처가 PMU 경로뿐인지 전수 확인
