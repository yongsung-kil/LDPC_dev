# 2-1. shift_mem 순열 사전 계산

| 항목 | 내용 |
|------|------|
| 상태 | **검토 완료** (2026-07-23 사용자 승인) |
| 파일 | `1_LDPC_revised/decoder.h`, `1_LDPC_revised/decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

`C2V_Cal()`과 `V2C_Store()`는 edge 하나를 처리할 때마다 `shift_mem()`(common.cpp)을 호출해 barrel shift용 32-원소 순열 배열을 새로 계산한다. 그런데:

- shift 값 `s = PCM_b[row_idx][jj]`는 **H-matrix에서 오는 고정값** — 시뮬레이션 내내 불변
- 가능한 순열은 방향(dir 0/1) × shift(0~z_sb-1) = **총 64개뿐** (메모리 8KB)
- 호출 빈도: 컬럼당 최대 17 edge × 129 컬럼 × iteration 수십 회 × C2V/V2C 2회 → 프레임당 수만 회, 매번 32-루프 + 원소마다 dir/wrap 분기
- `shift_mem`은 다른 번역 단위(common.cpp)에 있어 `/GL` 없이는 인라인도 안 됨

즉, 64개짜리 고정 테이블을 프레임당 수만 번 다시 만들고 있던 것. Init에서 1회 만들어 두면 핫루프에서는 포인터 대입 1회로 끝난다.

## 무엇을 어떻게 바꿨나

| 위치 | 변경 전 | 변경 후 |
|------|---------|---------|
| `decoder.h` 멤버 | `int* z_mem_shift;` | `int** shift_tbl_C2V;` (dir=0), `int** shift_tbl_V2C;` (dir=1) |
| 생성자 | `z_mem_shift = NULL;` | 두 테이블 NULL 초기화 |
| `Alloc_Dec()` | `z_mem_shift = new int[z_sb];` | 두 테이블을 `[z_sb][z_sb]`로 할당하고 **기존 `shift_mem()`을 s=0~z_sb-1로 호출**해 1회 채움 |
| `Release_Dec()` | `delete[] z_mem_shift;` | 테이블 행별 해제 |
| `C2V_Cal()` | `shift_mem(z_mem_shift, m_PCM->z_sb, s, 0);` | `const int* z_mem_shift = shift_tbl_C2V[s];` |
| `V2C_Store()` | `shift_mem(z_mem_shift, m_PCM->z_sb, s, 1);` | `const int* z_mem_shift = shift_tbl_V2C[s];` |

핵심 트릭: 로컬 포인터 이름을 기존 멤버명(`z_mem_shift`)과 같게 해서 **루프 내부의 `z_mem_shift[j]` 사용부(C2V_Cal 2곳, V2C_Store 1곳)는 한 글자도 바꾸지 않음** — diff 최소화.

## bit-exact 근거

테이블을 채울 때 기존 `shift_mem()` 함수를 그대로 호출하므로, 핫루프가 읽는 순열 값은 기존 계산 결과와 정의상 동일하다. 연산 순서·결과 모두 불변.

## 주의사항

- **shift 값 범위 전제**: 테이블 조회 `shift_tbl_*[s]`는 `s`가 0 ~ z_sb-1 범위라는 전제. 기존 `shift_mem`은 s = z_sb가 들어와도 동작했지만(k = i로 wrap) 테이블은 out-of-bounds가 된다. → H-matrix 로드 시(input.cpp) shift 값 범위 검증 추가 권장 (TODO.md에 기록됨)
- `ecc_top.cpp`(C_net 초기화)와 `encoder.cpp`의 자체 `z_mem_shift`는 init 1회 경로 / 별도 멤버이므로 수정하지 않음

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `shift_mem(` 호출부를 전역 검색 (barrel shift 순열을 만드는 함수 — 이름이 다르면 "cyclic shift array" 계열 주석/로직으로 탐색)
2. **디코더 핫루프 안의 호출만 대상**: C2V 계산 함수(dir=0)와 V2C 저장 함수(dir=1)에서 edge 처리 시작부에 `s = PCM[row][col]`을 읽은 직후 호출되는 것
3. 초기화 1회 경로(C_net 구성, 인코더 등)의 호출은 대상 아님 — 그대로 둔다
4. 테이블은 [방향][z_sb][z_sb]로 디코더 버퍼 할당 시점에 만들고, **기존 shift_mem 함수를 그대로 호출해 채운다** (값 동일성 보장)
5. 적용 전 전제 확인: 그 버전에서도 shift 값 s가 0 ~ z_sb-1 범위인지 (H-matrix 로드 코드 확인)
