# 5-6. `xor_r25` double 왕복 제거 (정수 경로 분리)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** — 전수 검증으로 bit-exact 승격 |
| 파일 | `ldpc_revised/random.h`, `random.cpp`, `ecc_top.cpp` |
| bit-exact | **보장 (2^32 전 범위 전수 검증 통과)** |
| 위험도 | 낮음 (검증 완료 후) |

## 왜 해야 하나

`xor_r25()`는 32bit 정수 `w`를 만들고 `w / 4294967295.0`(double)로 반환한다. 그런데 주요 소비처 3곳(`rand_msg_xor25`, `rand_sel_ep`, `rand_int`)은 받자마자 `(unsigned int)(x * 4294967295)`로 **다시 정수로 되돌린다**. 난수 1개당 double 나눗셈+곱셈+변환 2회가 순수 낭비다 — 메시지 bit당 + 에러 위치당 호출되므로 프레임당 수만~수십만 회.

원래 우려: `w → w/M → ×M → trunc` 왕복에서 1 ulp 오차로 `w-1`이 나올 가능성 (그래서 Phase 5 분류였음).

## 왕복 항등 검증 — 통과 (이 항목을 bit-exact로 승격)

**전수 검증**: w = 0 ~ 2^32-1 전부에 대해 원본 표현식 그대로 왕복 비교 → **mismatch 0** (MSVC 2022 x64, /O2 /fp:precise — 프로젝트와 동일 계열 설정).

수학적 근거도 일치: M = 2^32-1 < 2^32이므로 `RN(RN(w/M)·M)`의 오차가 `½ulp(w)·(M/2^32)`로 **엄격히** ½ulp(w) 미만 → 반올림이 항상 정확히 w로 복귀. truncation 우려는 M이 2^32보다 작아서 생기는 마진 덕에 실현되지 않는다.

검증 프로그램 (대상 공간에서 재실행 권장):
```cpp
#include <cstdio>
int main() {
    unsigned long long bad = 0;
    for (unsigned long long i = 0; i <= 0xFFFFFFFFULL; ++i) {
        unsigned int w = (unsigned int)i;
        double tmp = w / (double)4294967295;              // 생성측 표현식
        unsigned int back = (unsigned int)(tmp * 4294967295); // 소비측 표현식
        if (back != w) ++bad;
    }
    printf("mismatches=%llu\n", bad);   // 기대값: 0
}
```

## 무엇을 어떻게 바꿨나

- `random.h/cpp`: 상태 갱신 + `w` 반환의 정수 경로 `unsigned int xor_r25_u32(unsigned int* a)` 신설. 기존 `xor_r25()`는 `xor_r25_u32(a) / (double)4294967295;` 한 줄로 축소 (동일 값, 시그니처 유지)
- 정수 소비처 3곳: `(unsigned int)(xor_r25(...) * 4294967295)` → `xor_r25_u32(...)` (`rand_msg_xor25` / `rand_sel_ep` XOR_25 분기 / `rand_int`)
- `ecc_top.cpp` 시드 전진 루프: `xor_r25(current_seed);` (반환 버림) → `xor_r25_u32(current_seed);` — 나눗셈 생략, 상태 갱신 동일
- **유지**: `Gaussian_xor25()`는 실수값을 실제로 사용 → `xor_r25()` 그대로 (값 동일). `ran2()`의 `* 4294967295`는 별개 RNG(초기 시드 생성 1회) — 범위 밖

## 검증

- grep: 정수 소비처의 `* 4294967295` 왕복 잔여 0건 (ran2 초기화 2건은 별개 RNG로 유지)
- 상태 갱신 코드(`t`/`w` 계산, memmove, `a[24]=w`)는 u32 경로로 이동만 — 시퀀스 불변

## 이식 앵커

1. 적용 전 대상 코드의 소비처를 전수 확인 — `xor_r25` 반환값을 **실수로 쓰는 곳**(Gaussian 등)은 그대로 두고, `* 4294967295` 왕복하는 곳만 u32로 교체
2. 대상 공간의 컴파일러/플래그가 다르면 위 검증 프로그램을 그쪽에서 1회 재실행 (x87 80bit 모드나 /fp:fast에서는 별도 확인 필요 — x64 SSE2 + /fp:precise면 동일 결과)
3. seed save/load 파일 포맷은 상태 배열 그대로라 무관 — 시퀀스 동일성은 동일 seed 실행 diff로 확인
