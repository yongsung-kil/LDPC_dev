# 기존 룰 밖의 컨벤션 사각지대 (Blind Spots)

---

## A. 정책이 비어 있는 차원 — **결정이 필요한 것들**

우선순위 순. 위쪽일수록 다른 작업의 선행조건입니다.

| # | 사각지대 | 현행 상태(근거) | 권장 | 우선 |
|---|----------|----------------|------|------|
| A1 | **파일 인코딩** | channel/ecc_top/TV_Enc 한글 주석이 `@@@`로 깨짐(CP949 손상), encoder는 정상 UTF-8 → **파일마다 인코딩 다름** | UTF-8(BOM) 통일 + MSVC `/utf-8` | 🔴 최우선 |
| A2 | **탭 vs 스페이스** | decoder·ecc_top·TV_Dec는 **한 파일 안에서 탭+스페이스 혼용**, channel·full_CRC는 탭, 나머지는 4-스페이스 | 4-스페이스 통일 | 🔴 |
| A3 | **변수 네이밍 케이스** | 룰은 상수·함수만 규정. 로컬/멤버 변수 케이스는 미정 (`r_offset`, `mux_index`, `col_P2`, `jj_temp` 혼재) | snake_case + 도메인 약어 대문자 토큰 허용 | 🔶 |
| A4 | **한 줄 한 선언** | `int i, j, r, c, tmp, flag, kb;` (encoder), `double t, u;` (channel) 다수 | 1줄 1선언 (init-결합 룰과 시너지) | 🔶 |
| A5 | **줄 길이 제한** | 규정 없음. 일부 인자 나열 줄이 매우 김 | column limit 100 또는 120 확정 | 🔶 |
| A6 | **`NULL` vs `nullptr`** | encoder 등 `= NULL` 사용 (C++11 미반영) | `nullptr` | 🔶 |
| A7 | **`TRUE/FALSE` 매크로 vs `true/false`** | `TRUE == shuffled_dual_diag` 등 매크로 bool 사용 | 유지할지 결정 (HW 코드 대응이면 유지) | 🟢 |
| A8 | **매크로 상수 vs `constexpr`** | 상수 대부분 `#define`. UPPER_SNAKE만 정하고 형태는 미정 | 신규는 `constexpr`, HW 스위치는 `#define` | 🟢 |
| A9 | **인덱싱 표기** `*(arr+i)` vs `arr[i]` | encoder에 `*(Codeword+i)`, `*(*(P+r)+c)` 다수 (CLAUDE.md도 혼용 지적) | `arr[i]` 통일 | 🟢 |
| A10 | **전역 변수 정책** | channel.cpp의 `r_offset`, `LLR_th` 등 **파일 전역 변수** 노출 | namespace/static 캡슐화 or 유지 결정 | 🟢 |
| A11 | 포인터 공백 룰 int* a 로 수정 | | |
---

## C. 8개 룰 범위 밖이지만 리팩토링 시 같이 볼 값어치 있는 것

품질 이슈라 "컨벤션"보다 넓지만, 어차피 파일을 건드리는 김에 후보로만 적습니다. (즉시 결정 불필요)

| 항목 | 현상 | 비고 |
|------|------|------|
| include 가드 | `#pragma once` vs 매크로 가드 일관성 미확인 | 헤더 17개 확인 필요 |
| const 정확성 | 입력 포인터 인자에 `const` 거의 없음 | 안전성 |
| C 캐스트 vs `static_cast` | 미확인, 대형 파일에 존재 가능 | clang-tidy로 스캔 |
| new/delete 수동 관리 | `Alloc_`/`Release_` 쌍 (RAII 아님) | **범위 큼, 지금은 손대지 말 것** |
| 매직 넘버 | 리터럴 상수 산재 | 상수화는 별도 판단 |

---

## D. 적용 순서 권장 (사각지대 반영)

1. **A1 인코딩 복구** (UTF-8) — 이거 먼저 안 하면 주석 작업/자동 포맷이 깨짐
2. **A2 탭→스페이스** + 기계적 룰(브레이스·포인터·한 줄 if·return 괄호)은 **clang-format 일괄** → 손으로 안 함
3. 의미적 룰(주석 번역/삭제, A3·A4 네이밍·선언)은 파일 단위 수작업
