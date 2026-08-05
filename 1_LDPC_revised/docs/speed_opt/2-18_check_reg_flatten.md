# 2-18. `Check_REG` 평탄화 (int[M][2] → int[M])

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/decoder.h`, `decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 중간 (TV 시그니처 접점 — 뷰 어댑터로 해소) |

## 왜 해야 하나

`Check_REG`는 M(4128)개의 `int[2]`를 **개별 heap 할당**한 이중 포인터였다. 실사용 슬롯은 `IDX_CHECK_SUM` 하나뿐 (`IDX_WEAK_NUM` 사용처 0건 — grep 전수 확인). C2V_Cal/V2C_Store의 element 루프에서 매 원소 2단 역참조 + 산재된 8-byte 힙 블록 접근(캐시 미스 후보)이 발생했다.

## 무엇을 어떻게 바꿨나

- `int** Check_REG` → `int* Check_REG` (연속 int[M]) — 접근 `Check_REG[x][IDX_CHECK_SUM]` → `Check_REG[x]` (Ref-C 9곳 + 로그 1곳 + TV 디버그 1곳)
- `Clear_CN_REG(type)`: memset으로 치환 (type 인자는 호환성 유지 — checksum 슬롯만 존재)
- **TV 시그니처 보존**: `Print_TV_check_sum(int**, ...)`은 변경 금지 대상 → `__ECC_TV__` 가드 안에 `m_Check_REG_view`([M][2])와 `Get_Check_REG_View()`(호출 시 checksum 값을 뷰에 복사 후 반환)를 추가하고, TV 호출 5곳의 인자를 뷰로 교체. TV hex 출력 값은 동일

## 검증

- grep `Check_REG[...][...]` 2D 인덱싱 잔여 → 주석 1줄뿐
- IDX_WEAK_NUM 사용처 0건 재확인

## 이식 앵커

1. `Check_REG` 할당부와 `IDX_WEAK_NUM` 사용처를 먼저 전수 확인 — **두 번째 슬롯을 실제로 쓰는 버전이면 이 항목 적용 금지**
2. TV Print 함수 시그니처는 절대 변경하지 말고 뷰 어댑터 방식 사용
