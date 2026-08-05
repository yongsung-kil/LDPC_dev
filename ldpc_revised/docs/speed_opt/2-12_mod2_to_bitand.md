# 2-12. `% 2` → `& 1` / `^ 1` 치환 (핫패스)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.cpp` |
| bit-exact | 보장 (동치 규칙 아래 명시) |
| 위험도 | 낮음 |

## 왜 해야 하나

signed int의 `% 2`는 MSVC에서 음수 부호 보정 시퀀스(cdq/sub/and)를 생성한다. 피연산자가 0/1임이 보장되는 패리티 연산에는 순수 낭비 — 특히 element당 실행되는 sgn/checksum 갱신.

## 동치 규칙 (적용 근거)

- `x % 2 == 0` ⟺ `(x & 1) == 0`, `x % 2 != 0` ⟺ `(x & 1) != 0` — **모든 int에서 성립** (음수 포함: x%2 ∈ {-1,0,1})
- `x % 2` (값 사용) → `x & 1` — **x ≥ 0일 때만** 동치. 치환 지점 전부 0/1 합(비음수)임을 확인함
- `(v + 1) % 2` → `v ^ 1` — v ∈ {0,1}일 때 동치
- `v % 2 == 1` → `v != 0` — v ∈ {0,1}일 때 동치

## 치환 지점 (Ref-C 핫패스만)

| 위치 | 기존 → 변경 |
|------|-------------|
| `C2V_Cal()` new_sgn 계산 (element당) | `(synd+check_sum+eff) % 2` → `& 1` |
| `C2V_Cal()` 부호 적용 (element당) | `new_sgn % 2 == 1` → `new_sgn != 0` |
| `V2C_Store()` checksum old sgn 제거 (element당) | `% 2` → `& 1` |
| `CNU_Update_New_Sgn()` (element당) | `*check_sum = (...) % 2` → `& 1` |
| VN_Cal 계열 5곳 cwc 판정 | `(Variable_mem+1) % 2` → `Variable_mem ^ 1` |
| 출력 반전 2곳 | `(cwc[n]+1) % 2` → `cwc[n] ^ 1` |
| partial CRC checksum (컬럼당×80) | `(TP1+TP2+TP3+TP4) % 2` → `& 1` |
| 메인 루프 synd_val 검사 7곳 | `% 2 == 0` → `(& 1) == 0` |
| `Compute_SW/PSW` synd_val 2곳 | `% 2 != 0` → `(& 1) != 0` |
| `Compute_*` check_sum_prime 2곳 | `% 2` → `& 1` |
| `Make_LLR()` inv_hd 2곳 / CD 1곳 | `^ 1` / `& 1` |
| 출력 검사 1곳 | `(Variable_mem+1)%2==1` → `0 == Variable_mem` |

## 건드리지 않은 곳 (의도적)

- TV 가드 내부의 `% 2` (tv_vtc_inp 부호, HCU 매핑 `iter % 2`) — Ref-C 무관
- `current_G_idx = (G_idx + iter) % 2` — 함수 호출당 1회, 이득 없음
- `PMU_SRAM` 비트 분해 `% 2` — HW 타이밍 경로 (2-19에서 factor=0 시 스킵됨)
- 로그 함수(`Update_Log_Data`) 내부 — 로그 빌드 전용
- 인코더/ecc_top의 `% 2`는 별도 항목(3-5, 3-8~3-10)

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `% 2` 전역 검색 후 **핫패스(element/bit 단위 루프)만 선별**
2. 값 사용형(`x % 2`)은 x의 비음수 보장을 먼저 확인, 비교형(`== 0`/`!= 0`)은 무조건 안전
3. `% z_sb` 같은 다른 modulo와 혼동 금지 (한 줄에 둘 다 있는 경우 있음 — Syndrome punct recovery 라인은 이 이유로 제외했음)
