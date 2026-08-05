# LDPC C++ 스타일 가이드 (규칙 본문)

> 기준: **Google C++ Style Guide** 차용 + 프로젝트 특화.
> 각 규칙에 `[Google]`(구글과 동일) / `[특화]`(프로젝트 고유) / `[결정]`(확정 필요) 태그 표기.
> Good/Bad 예시는 실제 `LDPC_Original/` 코드에서 발췌.

---

## 1. 네이밍 (Naming)

### 1.1 상수 — `UPPER_SNAKE_CASE` `[특화]`

`#define` 매크로 상수와 `const`/`constexpr` 상수 모두 대문자 스네이크.

```cpp
#define MAX_DV_GLOBAL 17          // OK
constexpr int CRC_LEN = 80;       // OK
```

> 약어는 그대로 대문자 유지: `SEED_LEN`, `HCU_START`.

### 1.2 함수 — `PascalCase` (약어 대문자 보존) `[특화]`

```cpp
void C2V_Cal();          // OK — 약어 C2V 대문자 유지
double SNR_from_RBER();  // △ → SNR_From_RBER 로 통일 권장 (아래 참조)
void Get_Mag_2SD();      // OK
```

**규칙 세부**:
- 단어 경계는 PascalCase, **도메인 약어(SNR/LLR/C2V/V2C/HCU/CRC/TV/SD/HD/PCM)는 통째로 대문자**.
- 현재 혼재된 소문자 함수는 개명 대상 (§1.6, refactoring_checklist §3).

**Bad (현재 코드)**:
```cpp
double qfunc_inv(double p);   // snake_case + 소문자 → Qfunc_Inv 또는 Q_Func_Inv
double erf_m(double x);       // → Erf_M
void   shift_mem(int* arr);   // → Shift_Mem
unsigned char rand_int(void); // → Rand_Int
```

### 1.3 변수 — `snake_case` 또는 `camelCase` 중 택1 `[결정→권장 snake_case]`

현재 코드는 `r_offset`, `LLR_th`, `mux_index`, `col_P2`, `jj_temp` 등 **소문자 스네이크가 우세**.
→ **`snake_case` 로 통일** 권장 (도메인 약어는 대문자 토큰 허용: `LLR_th`, `col_P2`).

```cpp
int    mux_index = 0;    // OK
double llr_th   = 0.0;   // 이상적. 단 LLR_th 형태 관용 허용
```

### 1.4 멤버 변수 — `m_` 접두사 `[특화, 현행 유지]`

```cpp
PCM* m_PCM;   // OK — Decoder/Encoder 멤버는 m_ 접두사
```

> Google은 `member_` 접미 언더스코어지만, 이 프로젝트는 이미 `m_` 접두사가 자리잡음 → **현행 유지**.

### 1.5 타입/클래스 — `PascalCase` `[Google]`

```cpp
class Decoder { ... };    // OK
struct PARAM_DEC { ... }; // △ 구조체는 UPPER_SNAKE 관용 존재 → 유지(HW 대응)
```

### 1.6 약어(약자) 처리 규칙 `[특화]`

| 종류 | 규칙 | 예 |
|------|------|-----|
| 도메인 약어 | 통째로 대문자 유지 | `SNR`, `LLR`, `C2V`, `HCU`, `CRC`, `TV` |
| 일반 단어 | PascalCase(함수) / snake(변수) | `Offset`, `Index`, `Recovery` |

---

## 2. 포맷 (Formatting) — *대부분 clang-format 자동 적용 대상*

### 2.1 들여쓰기 — **스페이스 4칸, 탭 금지** `[결정→권장]`

> 현재 decoder.cpp·ecc_top.cpp·full_CRC.cpp는 **한 파일에서 탭과 스페이스를 혼용** 중 (최우선 정리 대상).
> Google 기본은 스페이스 2칸이나, 이 프로젝트는 4칸이 우세 → **4칸 스페이스로 통일**.

### 2.2 브레이스 — 함수는 next-line, 제어문은 attached `[특화 / K&R]`

**함수 정의**: 여는 브레이스를 **다음 줄**에 (현행 우세, "K&R" 요청 반영).
**제어문(if/for/while/switch)**: 여는 브레이스를 **같은 줄**에 (attached).

```cpp
// OK — 함수는 next-line
void Set_R_Offset(int init_n)
{
    if (MODE_DEC_2SD == init_n) {   // OK — 제어문은 attached
        r_offset = 0.35;
    }
    for (int i = 0; i < 5; i++) {   // OK — for도 attached
        temp_t *= t;
    }
}
```

**Bad (현재 코드 — for가 Allman)**:
```cpp
for (int i = 0; i < 5; i++)
{                                   // ✗ 제어문은 attached여야 함
    temp_t *= t;
}
```

> ⚠️ 이 항목은 Google과 다름(Google은 함수도 attached). [결정] 항목 — README 참조.

### 2.3 한 줄 if 금지 — 항상 braced 블록 `[특화]`

**Bad (현재 코드)**:
```cpp
if (Lq_ini_m >= LLR_th)  *sd = 1;              // ✗ 브레이스 없음
else                     *sd = 0;              // ✗
if (i < kb * zsb)  *(Codeword + i) = *(Msg+i); // ✗ 한 줄
if (a >= t2) { *sd = 1; *cc = 0; }             // ✗ 한 줄에 여러 문장
```

**Good**:
```cpp
if (Lq_ini_m >= LLR_th) {
    *sd = 1;
} else {
    *sd = 0;
}
```

### 2.4 포인터/참조 공백 — `int* p` (타입 쪽 부착) `[특화, 현행 우세]`

```cpp
int* arr;                 // OK
void Foo(int* sd);        // OK
int** P;                  // OK
```

**Bad**:
```cpp
int *arr;                 // ✗ 별표가 변수 쪽
int * arr;                // ✗ 양쪽 공백
new int* [z_sb];          // ✗ int* 와 [ 사이 공백 → new int*[z_sb]
```

> 주의: 다중 선언(`int* a, b;`)은 함정(b는 포인터 아님). **한 줄 한 선언** 권장 (§3.2).

### 2.5 return 문 — 괄호 없이 `[Google]`

```cpp
return u;          // OK
return q_fn;       // OK
return(q_fn);      // ✗ 괄호 제거
```

### 2.6 연산자/콤마 공백 `[Google]`

```cpp
a = 2 * r_offset / var;   // OK — 이항 연산자 양옆 공백
Foo(a, b, c);             // OK — 콤마 뒤 공백
```

---

## 3. 변수 선언·초기화

### 3.1 선언과 동시에 초기화 `[특화 / Core Guidelines ES.20]`

**Bad (현재 코드 — C 스타일 상단 일괄 선언)**:
```cpp
int i, j, r, c, tmp, flag, kb;   // ✗ 선언만
kb = NumColBlk - NumRowBlk;      //   나중에 초기화
double t, u;
t = sqrt(-2 * log(p));
```

**Good**:
```cpp
int kb = NumColBlk - NumRowBlk;
double t = sqrt(-2 * log(p));
```

### 3.2 한 줄에 한 변수 `[Google]`

```cpp
double r_offset  = 0.0;   // OK
double r_offset2 = 0.0;
// 다중 선언 금지: double r_offset, r_offset2, r_offset3;  ✗
```

### 3.3 루프 변수는 루프 스코프 안에서 선언 `[Google]`

```cpp
for (int i = 0; i < n; i++) { ... }   // OK
// int i; ... for (i = 0; ...)          ✗ (재사용 목적 아니면 금지)
```

---

## 4. 주석 (Comments)

### 4.1 언어 — **영어** `[특화]`

모든 주석은 영어로 작성. 기존 한글 주석은 번역 대상.

### 4.2 내용 — "무엇" 이 아니라 "왜" `[특화 / Google]`

코드가 이미 명확하면 주석을 **달지 않는다**.

**Bad**:
```cpp
// 생성자                          ✗ (자명함 + 한글)
Encoder::Encoder() { ... }

r_offset = 0.35;   // set r_offset to 0.35   ✗ (코드 반복)
```

**Good**:
```cpp
// 2SD mode biases the erasure region toward strong 1s (empirical, see ADR-xx).
r_offset = 0.35;
```

### 4.3 섹션 divider — 유지하되 영어로 `[특화]`

```cpp
//=============================================
// AWGN channel LLR quantization
//=============================================
```

> 현재 divider 안의 한글이 CP949 손상으로 `@@@` 깨짐 → 영어로 재작성 (refactoring §1).

---

## 5. 헤더 / include

### 5.1 include 파일명 대소문자 정확히 `[Google]`

```cpp
#include "encoder.h"    // OK — 실제 파일명과 일치
#include "Encoder.h"    // ✗ 실제 파일은 encoder.h (Windows에선 통과하나 부정확)
```

### 5.2 include 순서 `[Google]`

1. 대응 헤더 (`foo.cpp` → `foo.h`)  2. C 시스템  3. C++ 표준  4. 프로젝트 헤더.

---

## 6. 파일 인코딩 `[특화, 최우선]`

- **UTF-8 (BOM 권장, MSVC 안전)** 로 전 파일 통일.
- MSVC 컴파일 시 `/utf-8` 플래그 추가 권장.
- 현재 CP949 손상 파일(channel.cpp, ecc_top.cpp, TV_Enc.cpp)은 복구 후 UTF-8 저장.

---

## 부록 A. Google Style에서 **의도적으로 벗어난** 항목

| 항목 | Google | 이 프로젝트 | 이유 |
|------|--------|-------------|------|
| 함수 브레이스 | attached | **next-line** | 기존 코드 K&R 관용 |
| 들여쓰기 | 2 space | **4 space** | 기존 코드 우세 |
| 멤버 변수 | `member_` | **`m_member`** | 기존 `m_PCM` 관용 |
| 상수 | `kCamelCase` | **`UPPER_SNAKE`** | HW 상수 대응 + 사용자 지정 |
| 매크로 상수 | 지양 | **허용** | HW/모드 스위치 다수 |

## 부록 B. clang-format으로 자동화 가능한 규칙 vs 수작업 규칙

| 자동(clang-format) | 수작업(사람/AI + clang-tidy) |
|--------------------|------------------------------|
| 들여쓰기 탭→스페이스 | 네이밍 개명 |
| 브레이스 위치 | 주석 번역/삭제 |
| 포인터 공백 `int* p` | 선언-초기화 결합 |
| 한 줄 if → 블록 | 인코딩 복구 |
| return 괄호 제거 | include 대소문자 |
| 연산자 공백 | 도메인 약어 판단 |
