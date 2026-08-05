# 2-4. stopping_criteria 판정 hoisting

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (2026-07-23 일괄 진행 지시) |
| 파일 | `1_LDPC_revised/decoder.cpp` (decoder.h 무변경) |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

VN_Cal 계열 5개 함수의 j-루프(z_sb 원소) 안에서, bTable 구간(shortening/puncturing이 아닌 일반 bit) 원소마다 다음 판정을 반복한다:

```cpp
if ((MODE_STOPPING_CRITERIA_ITER == m_param_dec->stopping_criteria) ||
    ((MODE_STOPPING_CRITERIA_CYCLE == m_param_dec->stopping_criteria) && (Force_stopping < POWER_STOPPING_DELAY)))
```

- `stopping_criteria`는 시뮬레이션 파라미터 — 프레임 내 불변
- `Force_stopping`은 clk/iteration 레벨에서만 갱신되는 멤버 (대입 지점 전수 확인: 초기화 1곳 + iteration 루프 내 증가 1곳) — **VN_Cal 함수 실행 중에는 불변**

즉 컬럼당 32회 × 129 컬럼 × iteration의 2중 비교 + 분기가 전부 같은 결과를 낸다.

## 무엇을 어떻게 바꿨나 — 함수별 두 가지 형태

### (a) 완전 hoist — `VN_Cal_HD()`, `VN_Cal_HD_HCU()`, `VN_Cal_CD()`

이 세 함수에서는 판정 결과가 곧바로 `channel_llr = ch1 or CH_LLR_MAX` 선택이므로 **값 자체를 사전 결정**:

```cpp
// 함수 서두 (Get_VNU_* 호출 뒤 — ch1 필요)
const int table_llr = (판정식) ? ch1 : CH_LLR_MAX;    /* FALSE = Power stopping algorithm (Part 2) */

// 루프 안: 기존 9줄 if-else → 
if (TRUE == bTable) {
    channel_llr = table_llr;
}
```

### (b) 바깥 판정만 hoist — `VN_Cal_SD()`, `VN_Cal_SD_HCU()`

SD 계열은 판정 통과 후 **per-element 로직**(`mag = abs(Soft_LLR_PRIME[bit_pos])`로 ch1/ch2 선택)이 있어 값 사전 결정이 불가능. 판정 bool만 hoist:

```cpp
// 함수 서두
const int b_use_table_llr = (판정식) ? TRUE : FALSE;

// 루프 안: 조건식만 교체, 내부 mag 로직은 그대로
if (TRUE == bTable) {
    if (TRUE == b_use_table_llr) {
        mag = abs(Soft_LLR_PRIME[bit_pos]);
        ...
```

## bit-exact 근거

- 판정식은 문자 그대로 동일, 평가 시점만 루프 밖으로 이동
- `Force_stopping` 대입 지점 전수 확인: 프레임 시작 초기화, iteration 루프 내 `Force_stopping++` — 모두 VN_Cal 호출 밖. VN_Cal과 그 피호출 함수(Get_VNU_*)는 이 멤버를 건드리지 않음
- SD 계열의 per-element mag 로직은 무변경

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `stopping_criteria`(또는 `POWER_STOPPING_DELAY` / "Power stopping algorithm" 주석)를 전역 검색 — VN 계산 함수의 element 루프 안 판정이 대상
2. 함수마다 확인: 판정 통과 후가 단순 대입(ch1/CH_LLR_MAX)이면 (a) 완전 hoist, per-element 값(soft LLR mag 등)에 의존하면 (b) bool만 hoist
3. 적용 전 확인: `Force_stopping`(또는 대응 카운터)의 모든 대입 지점이 VN 함수 실행 경로 밖인지 전수 확인 — 안이면 hoisting 불가
