# 4-3. CN 상태 struct 묶음 (5개 배열 → `CN_STATE[M]`)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/decoder.h`, `decoder.cpp` |
| bit-exact | 보장 (저장 위치만 이동, 값·연산 순서 불변) |
| 위험도 | 중간 (수정 지점 ~65곳 — 누락 시 컴파일 에러로 드러남) |

## 왜 해야 하나

C2V_Cal / V2C_Store의 element 루프는 **같은 CN 인덱스**로 5개 배열을 함께 접근한다:
`REG_min1_pos` / `REG_min1_value` / `REG_min2_value` / `Check_REG` / `Syndrome` (각 int[M], 별도 heap 할당).

원소 1개 처리마다 서로 다른 5개 배열 → 서로 다른 5개 캐시 라인을 터치한다. 배열들이 각각 16.5KB(M=4128×4B)라 L1에서 set 충돌 후보이기도 하다. 한 CN의 5개 상태를 20-byte struct 하나로 묶으면 원소당 접근이 캐시 라인 1개로 줄고, 주소 계산도 base 포인터 1개로 단순해진다.

**효과의 정직한 범위**: row block 전체(32 CN)를 순회할 때의 총 바이트 트래픽은 동일하다(5×128B = 1×640B). 이득은 (1) 원소당 활성 캐시 라인 수 감소, (2) 5개 스트림 → 1개 스트림으로 프리페치/TLB 부담 감소, (3) 배열 간 set 충돌 제거에서 온다. 효과 중간 등급인 이유 — 적용 후 프로파일 확인 권장.

## 무엇을 어떻게 바꿨나

- `decoder.h`: class 위에 `struct CN_STATE { min1_pos; min1_value; min2_value; check_sum; syndrome; }` 선언 (모두 int). 멤버 5개 제거 → `CN_STATE* m_CN;` 하나로 교체. **20byte로 두고 의도적으로 패딩하지 않음** — 순회 시 전 바이트를 읽으므로 밀도가 정렬보다 우선
- 할당/해제/NULL 초기화: `m_CN = new CN_STATE[M]` 1회 (기존 5회 할당 제거)
- **핫패스**: C2V_Cal j-루프에서 `const CN_STATE* cn = &m_CN[row_idx_r];` (읽기 전용), V2C_Store j-루프에서 `CN_STATE* cn = &m_CN[bit_pos];` — 이후 필드 접근은 `cn->syndrome` 등
- Clear 계열: `Clear_CN_REG`/`Clear_Syndrome`은 memset → 필드 단위 루프 (struct 통합으로 필드가 흩어져 memset 불가 — 2-15와의 절충, iteration당 O(M)이라 핫패스 아님). `Clear_REG_min_pos`/`Clear_REG_min_value`는 인덱스만 치환
- Update Syndrome 블록(`m_CN[j].syndrome = m_CN[j].check_sum; ... m_CN[j].check_sum = 0;`), puncturing recovery의 syndrome 읽기/갱신, Compute_CSW/SW/PSW/Min1·2_Sum, 로그 함수들 — 전부 필드 접근으로 치환
- **TV 시그니처 보존**: `Print_TV_syndrome(int*)` / `Print_TV_min_pos(int*, ...)` / `Print_TV_check_sum(int**, int*, ...)`은 변경 금지 → `__ECC_TV__` 가드 안에 `m_Syndrome_view` / `m_min1_pos_view`(각 int[M])와 `Get_Syndrome_View()` / `Get_Min1_Pos_View()`를 추가 (2-18의 `Get_Check_REG_View()`와 동일 패턴). TV hex 출력 값은 동일

## 함께 수정한 잠재 회귀 (2-18 유래)

`Print_TV_Cycle_Based()`는 가드 없이 항상 컴파일되는데, 2-18부터 본문이 `__ECC_TV__` 전용인 `Get_Check_REG_View()`를 호출하고 있었다 → **`__ECC_TV__` 미정의 빌드는 컴파일 실패** (2-18 적용 시점의 회귀). 호출부 3곳이 전부 `__ECC_TV__` 가드 안임을 확인하고 **함수 본문 전체를 `#if defined(__ECC_TV__)`로 감쌈** — 비TV 빌드에서는 호출이 없으므로 빈 함수로 bit-exact.

## 검증

- grep: `REG_min1_pos|REG_min1_value|REG_min2_value|Check_REG[|Syndrome[` 코드 잔여 0건 (주석/문서만 잔존)
- `m_CN[`/`cn->` 접근 58곳 == 기존 5개 배열 접근처 전수 치환 (지역변수 `cn` 이름 충돌 0건)
- 전처리기 가드 균형: comment-strip 후 depth 0 확인. 중괄호 균형: 수정 전후 동일 (기존 diff=1은 `#if/#else` 분기 탓, 원본 0_LDPC_original/도 동일 양상)
- `Syndrome_intermediate`(_internal)는 TV 검증용 별도 배열이라 통합하지 않고 유지

## 이식 앵커

1. 대상 5개 배열의 **사용처를 먼저 전수 grep** (`REG_min1_pos|REG_min1_value|REG_min2_value|Check_REG|Syndrome`) — 버전에 따라 로그/코너체커 쪽 사용처 수가 다를 수 있음. 컴파일 에러가 누락 검출기 역할을 하므로, 멤버 제거 → 에러 나는 곳 전부 치환 순서로 진행하면 안전
2. TV Print 함수 시그니처는 절대 변경하지 말고 뷰 어댑터(`Get_*_View()`) 방식 사용
3. `Print_TV_Cycle_Based` 같은 **가드 밖 함수가 TV 전용 심볼을 참조하는지** 확인 — 참조하면 본문을 `__ECC_TV__`로 가드 (호출부가 모두 가드 안인지 먼저 확인)
4. struct 필드 순서는 임의(접근 빈도 균등) — 단 `Check_REG` 2슬롯([M][2])을 실사용하는 버전이면 2-18 앵커부터 재확인
