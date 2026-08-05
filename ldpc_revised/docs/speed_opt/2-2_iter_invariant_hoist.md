# 2-2. iteration 판정의 element 루프 탈출 (loop-invariant hoisting)

| 항목 | 내용 |
|------|------|
| 상태 | **검토 완료** (2026-07-23 사용자 승인) |
| 파일 | `ldpc_revised/decoder.cpp` (decoder.h 무변경) |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

`C2V_Cal()`과 `V2C_Store()`의 z_sb(32) 원소 루프 안에서 매 원소마다 다음이 실행된다:

- `C2V_Cal_New_Sgn(iter, synd, check_sum, edge_sgn, jj)` — 내부에서 `init_n` 모드 비교 체인 + `Is_Iter_Type_Edge_Clear(iter)` 호출
- `CNU_Remove_Old_Sgn(iter, pre_v2c_sgn, &check_sum, jj)` — 동일 구조
- `Is_Iter_Type_Init(iter)` — edge SRAM 쓰기 분기

`Is_Iter_Type_Edge_Clear/Init`는 내부에서 matrix_sel 비교 + iter 상수 비교 체인(`__AUTO_LLR_OPT__` 빌드에서는 restart_iter 배열 순회까지)을 수행한다. 그런데 이 판정들의 입력(`iter`, `jj`, `init_n`, `flag_BF_on`)은 **j-루프 32회 동안 완전 불변**이다. 두 함수의 실질 효과도 "old sign을 0으로 취급할지"라는 **bool 하나**로 요약된다. 즉 원소마다 함수 호출 2회 + 분기 체인을 반복할 이유가 없다.

실행 빈도: 원소 레벨이므로 컬럼당 17 edge × 32 원소 × 129 컬럼 × iteration — 프레임당 수십만 회.

## 무엇을 어떻게 바꿨나 — "프로브 호출" 방식

**원본 판정 함수 두 개는 한 줄도 수정하지 않았다.** 대신 루프 밖에서 각 함수를 **중립 입력으로 1회 호출**해 불변 판정값을 추출한다:

### C2V_Cal()

```cpp
// 루프 진입 전 (1회)
const int b_c2v_keep_old_sgn = C2V_Cal_New_Sgn(iter, 0, 0, 1, jj);
```

`C2V_Cal_New_Sgn`은 마지막에 `t = (synd + check_sum + edge_sgn_eff) % 2`를 반환하므로, `synd=0, check_sum=0, edge_sgn=1`을 넣으면 반환값은 **old sgn이 유지되면 1, clear되면 0** — 즉 판정 bool 그 자체다.

```cpp
// 루프 안: 기존
new_sgn = C2V_Cal_New_Sgn(iter, synd, check_sum, edge_sgn, jj);
// 루프 안: 변경
new_sgn = (synd + check_sum + ((TRUE == b_c2v_keep_old_sgn) ? edge_sgn : 0)) % 2;
```

### V2C_Store()

```cpp
// 루프 진입 전 (1회)
int b_v2c_keep_old_sgn = 0;
CNU_Remove_Old_Sgn(iter, 1, &b_v2c_keep_old_sgn, jj);   // (0 + pre_v2c_sgn_eff) % 2 → 유지=1 / clear=0
const int b_iter_init = Is_Iter_Type_Init(iter);
```

```cpp
// 루프 안: 기존
CNU_Remove_Old_Sgn(iter, pre_v2c_sgn, &check_sum, jj);
// 루프 안: 변경
check_sum = (check_sum + ((TRUE == b_v2c_keep_old_sgn) ? pre_v2c_sgn : 0)) % 2;

// 루프 안: 기존
if (TRUE == store_edge_SRAM) { if (TRUE == Is_Iter_Type_Init(iter)) { ... } }
// 루프 안: 변경
if (TRUE == store_edge_SRAM) { if (TRUE == b_iter_init) { ... } }
```

## bit-exact 근거

1. 두 판정 함수의 "old sgn을 0으로 만들지" 결정은 `(iter, col_idx, init_n, flag_BF_on)`만의 함수 — 루프 내 어떤 값에도 의존하지 않음 (본체 전수 확인)
2. 프로브 결과가 정확히 그 결정과 일치: `C2V_Cal_New_Sgn(iter,0,0,1,jj) = (0+0+eff(1))%2 = 유지 여부`. CNU도 동일
3. 원소별 최종 산술식 `(synd + check_sum + eff) % 2` / `(check_sum + eff) % 2`는 원본 함수 마지막 줄과 동일 (`% 2`는 2-12에서 별도 처리 예정이라 유지)
4. `edge_sgn` 변수 자체는 건드리지 않음 — 원본도 함수에 **값 전달**이라 호출 후 `pre_exist_sgn_reg[...] = edge_sgn` 저장은 SRAM에서 읽은 원래 값이었고, 변경 후에도 동일

## 건드리지 않은 곳

- `__ECC_TV__` 가드 안의 `Is_Iter_Type_Init` 호출 2곳 (TV 전용 — Ref-C에서 컴파일 아웃)
- j-루프 종료 후의 Syndrome 복사 판정 (edge당 1회라 유지)
- 컬럼 단위 wrapper의 `Is_Iter_Type_Init(mn)` 검사 (컬럼당 1회라 유지)
- 원본 `C2V_Cal_New_Sgn()` / `CNU_Remove_Old_Sgn()` 본체 (주석 포함 그대로 — 이제 프로브로만 호출됨)

## 부작용 없음 확인 (2026-07-23 재검증)

프로브 방식은 함수를 **원래보다 1회 더 호출**하므로, 그 함수에 부작용이 있으면 중간 상태가 달라진다.
본체를 다시 전수 확인한 결과 **모두 순수 함수**임을 확인했다:

- `C2V_Cal_New_Sgn()` — 지역변수 `t`와 **값 전달된** `edge_sgn`만 수정 후 반환. 멤버 쓰기 0건
- `CNU_Remove_Old_Sgn()` — out 파라미터 `*check_sum`과 값 전달 `pre_v2c_sgn`만 수정. 멤버 쓰기 0건
- `Is_Iter_Type_Edge_Clear()` / `Is_Iter_Type_Init()` — 지역 `bClear`/`bInit` 반환만. 멤버 쓰기 0건
- 분기 안의 `Intentional_Blank()` — 본체가 `;` 뿐인 빈 함수 (`common.cpp`)

따라서 프로브 호출을 추가해도 카운터·로그·타이밍 등 어떤 중간 상태도 변하지 않는다.

## 주의사항

- **프로브 패턴의 전제**: 두 판정 함수의 clear 결정이 per-element 입력(synd/check_sum/edge_sgn)에 의존하지 않는다는 것. 나중에 누군가 함수 내부에 per-element 의존 로직을 추가하면 프로브가 깨진다 → 함수 주석 또는 코드 리뷰에서 인지 필요 (TODO.md에 기록)
- `__RUN_PREPROCESSING__` 빌드에서도 판정 입력이 (iter, col_idx, flag_BF_on)뿐이라 동일하게 성립 (현재 mode.h에서 미정의)

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. element 루프(z_sb 원소) **안에서** 호출되는 판정 함수를 검색: `C2V_Cal_New_Sgn`, `CNU_Remove_Old_Sgn`, `Is_Iter_Type_Init` (이름이 다르면 "Restart iteration에서 old_sgn을 읽지 않음" 계열 주석으로 탐색)
2. **적용 전 필수 확인**: 그 버전에서도 clear 판정이 per-element 입력(synd/check_sum/sgn 값)에 의존하지 않고 (iter, col, mode)만의 함수인지 본체를 읽어 확인 — 아니면 이 항목을 적용하지 말 것
3. 프로브 입력 구성: 함수의 마지막 산술식이 `(a + b + sgn_eff) % 2` 형태인지 확인 후, sgn 자리에 1·나머지에 0을 넣으면 반환값 = "old sgn 유지 여부" bool
4. 루프 밖 판정 캐시 후, 루프 안은 원본 함수의 마지막 산술식을 그대로 인라인 (`% 2` 등 연산 형태 변경 금지 — 그건 별도 항목)
