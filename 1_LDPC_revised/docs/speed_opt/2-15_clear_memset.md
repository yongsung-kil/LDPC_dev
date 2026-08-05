# 2-15. Clear 계열 함수 memset화

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/decoder.cpp` |
| bit-exact | 보장 (0 채우기) |
| 위험도 | 낮음 |

## 왜 해야 하나

restart/init iteration마다 실행되는 클리어 함수들이 이중 루프 원소별 `= 0` 대입으로 M×K(4128×수십) 등 큰 배열을 지운다. int의 0 채우기는 memset과 완전 동일.

## 무엇을 어떻게 바꿨나

| 함수 | 변경 |
|------|------|
| `Clear_Edge_SRAM()` / `Clear_Edge_SRAM_Sgn()` (동일 본체 2곳) | M행 × K열 이중 루프 → 행별 `memset(Check_SRAM_sgn[i], 0, K*sizeof(int))` |
| `Clear_Syndrome()` | 원소별 루프 → `memset(Syndrome, ...)` + `memset(Syndrome_intermediate, ...)` (연속 1D 배열) |
| `Clear_Delay_REG()` | J×z_sb 이중 루프(배열 7개) → 행별 memset (TV 전용 2개는 기존 `__ECC_TV__` 가드 유지) |

## 제외 (의도적)

- `Clear_CN_REG(type)`: `Check_REG[i][type] = 0` — 행마다 특정 슬롯 하나만 지우는 구조라 현 레이아웃에서 memset 불가 (2-18 평탄화와 함께 다룰 사안)
- `Clear_REG_min_pos()`: 값이 `Get_Default_Min_Pos(i)` — 0이 아니라 memset 불가
- lfsr 4종 클리어: 80원소 소형 — 이득 미미하여 유지
- `Clear_TV_buffer()`: TV 전용 (Ref-C 컴파일 아웃)

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. Clear_* 함수들에서 **0을 채우는** 이중/단일 루프만 대상 (0이 아닌 값 채우기는 memset 불가)
2. int 배열의 0 채우기는 memset과 비트 동일 — float/포인터 배열이면 불가
