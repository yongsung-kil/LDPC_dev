# 2-3. 1bit-precision 판정 hoisting

| 항목 | 내용 |
|------|------|
| 상태 | **검토 완료** (2026-07-23 사용자 승인) |
| 파일 | `1_LDPC_revised/decoder.cpp` (decoder.h 무변경) |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

BF(Bit-Flipping) 초기 iteration에서 degree가 큰 컬럼(dv > 5)은 1bit precision으로 동작한다. 이 판정이 4개 함수의 **element 루프 안**에서 원소마다 반복된다:

```cpp
if ((TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)) { ... }
```

세 항(`flag_BF_on`, `iter`, `v_deg`) 모두 **함수 호출 동안 완전 불변** — `flag_BF_on`은 멤버 상태, `iter`와 `v_deg`는 함수 인자/컬럼 고정값이다. 실행 빈도는 원소 레벨(C2V/V2C는 z_sb=32회, VN은 z_sb × v_deg회 = 컬럼당 최대 544회) × 129 컬럼 × iteration. 게다가 HD 초기 몇 iteration 외에는 절대 참이 되지 않는 조건을 매번 3항 평가한다.

## 무엇을 어떻게 바꿨나

4개 함수 각각의 서두(원소 루프 진입 전)에서 1회만 평가:

```cpp
// j-루프 불변: 1bit precision 모드 판정
#ifdef __AUTO_LLR_OPT__
const int b_1bit_precision = ((TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)) ? TRUE : FALSE;
#else
const int b_1bit_precision = ((TRUE == flag_BF_on) && (iter <= ITER_MAX_HBF) && (v_deg > DV_5)) ? TRUE : FALSE;
#endif
```

루프 안은 3항 조건 대신 캐시된 값만 검사:

| 함수 | 위치 | 변경 후 |
|------|------|---------|
| `C2V_Cal()` | mag 계산 분기 | `if (TRUE == b_1bit_precision) { //Dv > 5 인 column은 1bit precision ...` |
| `V2C_Store()` | MIN REG 갱신 분기 | `if (TRUE == b_1bit_precision) { //1bit mode` |
| `VN_Cal_HD()` | 출력 양자화 분기 (ii 루프 내) | `if (TRUE == b_1bit_precision) { //1bit precision` |
| `VN_Cal_HD_HCU()` | 출력 양자화 분기 (ii 루프 내) | 〃 |

`__AUTO_LLR_OPT__` 빌드의 조건 차이(`iter <= 4` vs `iter <= ITER_MAX_HBF`)는 정의부의 `#ifdef`로 그대로 보존 — 루프 안에 있던 `#ifdef` 분기 4벌이 정의부 4벌로 이동했을 뿐이다.

## bit-exact 근거

- 조건식 자체는 문자 그대로 동일하고 평가 시점만 루프 밖으로 이동
- 세 피연산자가 함수 실행 중 변경되는 지점 없음: `flag_BF_on`은 iteration 루프 레벨에서만 갱신되는 멤버, `iter`/`v_deg`는 값 전달 인자
- `VN_Cal_CD/SD/SD_HCU`에는 이 판정이 원래 없음 (1bit는 HD 계열 전용) — 건드리지 않음

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `DV_5`(또는 "1bit precision" / "1bit mode" 주석)를 전역 검색 — element 루프 안에서 `flag_BF_on && iter 상한 && v_deg > DV_5` 3항 조건이 나오는 곳이 대상
2. 대상은 디코더 핫루프 4곳: C2V mag 계산, V2C의 MIN REG 갱신, HD 계열 VN 출력 양자화 (HCU 변형 포함)
3. `DU_Manager` 등 clk 레벨 함수의 `ColW[..] <= DV_5` 비교는 **다른 용도** — 대상 아님
4. 적용 전 확인: 그 버전에서 `flag_BF_on`이 element 루프 안에서 변경되지 않는지 (컬럼/원소 처리 중 BF 모드 전환이 없는지)
