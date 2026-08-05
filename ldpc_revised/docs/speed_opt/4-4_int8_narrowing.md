# 4-4. 0/1 값 배열의 int → int8_t 축소

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.h`, `decoder.cpp` |
| bit-exact | 보장 (저장 값 전부 0/1 — 읽기 시 int 승격으로 산술 동일) |
| 위험도 | 중간 (값 범위 전제 + int* 인터페이스 경계 처리) |

## 왜 해야 하나

0/1만 담는 배열이 int(4B)로 되어 있어 캐시 밀도가 1/4이다. int8_t로 줄이면 같은 캐시 라인에 4배의 원소가 들어간다. C++ 정수 승격 규칙상 int8_t는 산술식에서 int로 승격되므로, **저장 값이 [-128,127] 안이면 연산 결과는 완전 동일** — 여기서는 전부 0/1이라 여유가 크다.

## 적용 대상 (값 범위 전수 확인 완료)

| 배열 | 크기 | 값 | 효과 |
|------|------|-----|------|
| `Check_SRAM_sgn` [M][K] | 4128×26×4B ≈ 429KB → **107KB** | 0 / v2c_sgn(V_PLUS=0/V_MINUS=1) | 최대 — C2V 읽기·V2C 쓰기 모두 element당 |
| `Variable_mem` [N] | 16.5KB → 4KB | 0/1 (HD 초기화·genie 복사·PR 결정) | VN_Cal element당 읽기 |
| `cwc` [N] | 16.5KB → 4KB | 0/1 (Variable_mem 파생) | VN_Cal 쓰기·수렴 검사 읽기 |

**제외 대상과 이유**:
- `Syndrome` — 4-3에서 `CN_STATE` struct 필드가 됨. 필드 하나만 int8_t로 줄여도 정렬 패딩 때문에 struct 크기가 20B 그대로 → 이득 0
- `prev_cwc` — 할당/해제만 있고 사용처 0건 (사장 멤버). 굳이 건드리지 않음
- `pre_exist_sgn_reg` 계열 — J×z_sb 소형 배열이라 캐시 상주. 이득 미미하여 제외

## 무엇을 어떻게 바꿨나

- `decoder.h`: `#include <stdint.h>` 추가, 3개 멤버 `int8_t`화
- 할당: `new int8_t[...]`, memset 길이 `K * sizeof(int8_t)` (2곳)
- 대입 지점: 리터럴 0/1은 그대로(상수 변환은 경고 없음). **int 표현식 대입만 명시 캐스트** — `(int8_t)v2c_sgn` 1곳, `(int8_t)m_genie_inv_cw[..]` 3곳, `(int8_t)(Variable_mem[..] ^ 1)` 5곳 (승격된 int 식의 재축소, C4244 방지)
- 읽기 지점은 무변경 — int 승격이 자동 처리 (`* (-2) + 1`, `synd_val +=`, 비교 등)

## int* 인터페이스 경계 (시그니처 변경 금지 → 뷰 어댑터)

| 경계 | 처리 |
|------|------|
| `CRC_decoder(cwc, ...)` 2곳 (Check_End_Iter, full CRC 모드) | `Get_Cwc_View()` — **TV 가드 밖 경로라 뷰를 무조건 보유**. 복사 O(N)은 iteration당 1회뿐 |
| `Print_TV_cwc(cwc, ...)` | `Get_Cwc_View()` (호출부는 `__ECC_TV__` 안) |
| `Print_TV_llr_out(.., Variable_mem, ..)` 2곳 | `Get_Variable_Mem_View()` (`__ECC_TV__` 전용 멤버/함수) |
| `Print_TV_str_err_cnt_BLK(Variable_mem, cwc, ..)` | 두 뷰 모두 사용 |
| partial CRC (`partial_crc_HW_T4`) | 수정 불필요 — `dec_d`(int) 중간 버퍼에 원소별 복사로 이미 절연됨 |

## 검증

- 쓰기 지점 전수 grep: 리터럴/캐스트/동일 타입 대입만 존재 (`Variable_mem[..]=`, `cwc[..]=`, `Check_SRAM_sgn[..][..]=`)
- 포인터 전달 grep (`배열명 [,)]`, `&배열명`, `배열명 +`): 잔여 0건 (주석 1건 제외)
- `Init_Buf(int*)` 사용처: 3개 배열에 대해 0건 (오버로드 혼용 없음)
- 중괄호/전처리기 균형: 수정 전후 동일

## 이식 앵커

1. 적용 전 **대상 배열의 모든 대입 지점을 grep으로 전수 확인** — 0/1 외의 값(예: 다른 버전에서 -1 sentinel)이 하나라도 있으면 그 배열은 제외
2. 대상 배열이 `int*` 파라미터 함수(CRC/TV/로그)로 넘어가는 곳을 먼저 찾을 것 — HW 생성 함수·TV Print 시그니처는 변경 금지, 뷰 어댑터로 우회. **가드 밖 경로(full CRC 등)의 뷰는 가드 없이 보유**
3. `memset`/`memcpy`의 `sizeof(int)`를 반드시 함께 수정 (놓치면 인접 heap 침범)
4. `Init_Buf` 같은 int* 전용 유틸에 넘기는 곳이 있으면 해당 배열 제외 또는 유틸 오버로드 추가
5. 회귀 검증(동일 seed FER/iter/uncor diff) 필수 — 이 항목은 값 범위 **전제**가 깨지면 조용히 오동작
