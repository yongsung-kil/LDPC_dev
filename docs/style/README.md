# LDPC C++ 코딩 컨벤션 — 진입점

> **목적**: `LDPC_Original/` 하위 C++ 소스의 스타일을 하나로 통일하기 위한 규칙 모음.
> 리팩토링·신규 코드 작성 전 이 폴더를 읽고 시작합니다.

---

## 문서 구성

| 문서 | 내용 |
|------|------|
| [additional_conventions.md](additional_conventions.md) | ★ **기존 8개 룰이 다루지 않는 사각지대** — 결정 필요한 컨벤션 차원 + 놓치기 쉬운 위반 |
| [cpp_style_guide.md](cpp_style_guide.md) | 참조용 규칙 본문 — 기존 룰 + 사각지대를 합친 통합 스타일 가이드 |

> 지금 우선 보실 것은 **additional_conventions.md** 입니다.
> 기존 룰은 그대로 적용하시면 되고, 이 문서는 그 룰이 아직 안 정한 것들을 짚습니다.

---

## 이 프로젝트 스타일 한 줄 요약

> **Google C++ Style Guide를 기반**으로 하되, 함수 브레이스만 **K&R(next-line)** 를 유지하고,
> 식별자 약어(SNR, LLR, C2V 등)는 대문자로 보존한다.

---

## 참조 레퍼런스 (추천)

작업 시 아래 순서로 참고하시길 권장합니다.

| 우선 | 레퍼런스 | 용도 | 링크 |
|------|----------|------|------|
| ★★★ | **Google C++ Style Guide** | 프로젝트의 기준 베이스. 네이밍·포맷·헤더 규칙 | https://google.github.io/styleguide/cppguide.html |
| ★★★ | **clang-format** | 브레이스·들여쓰기·포인터 공백·한 줄 if 등 **기계적 규칙 자동 적용** | https://clang.llvm.org/docs/ClangFormat.html |
| ★★☆ | **clang-tidy** | 네이밍 검사·현대화(modernize)·버그 패턴 자동 검출 | https://clang.llvm.org/extra/clang-tidy/ |
| ★★☆ | **C++ Core Guidelines** (Stroustrup/Sutter) | "왜" 를 이해하는 상위 원칙. 초기화·RAII·포인터 안전성 | https://isocpp.github.io/CppCoreGuidelines/ |
| ★☆☆ | **LLVM Coding Standards** | Google과 다른 관점 참고용 (선언-초기화, 조기 return) | https://llvm.org/docs/CodingStandards.html |

### 핵심 권장: 손으로 다 고치지 말 것

브레이스 스타일, 들여쓰기(탭/스페이스), 포인터 공백(`int* p`), 한 줄 if 같은
**기계적(mechanical) 규칙은 `clang-format` 으로 자동 적용**하는 것이 정석입니다.
이 규칙들을 line-by-line 수작업하면 시간이 오래 걸리고 실수가 생깁니다.

- 기계적 규칙 → `.clang-format` 로 일괄 처리 ([proposed.clang-format](proposed.clang-format) 초안 참조)
- 의미적 규칙(네이밍, 주석 내용, 선언-초기화 결합, 인코딩) → 사람/AI 판단 필요

> ⚠️ **주의**: `LDPC_Original/`는 현재 빌드 불가 상태이고 일부 파일이 CP949 인코딩 손상(`@@@`)이 있습니다.
> clang-format 일괄 적용 **전에** 인코딩 정상화(UTF-8 통일)를 먼저 끝내야 합니다.
> (자세한 순서는 [refactoring_checklist.md](refactoring_checklist.md) §0 참조)

---

## 결정이 필요한 항목 (사용자 확인 대기)

아래는 규칙 확정 전 방향 결정이 필요합니다. 상세는 [refactoring_checklist.md](refactoring_checklist.md) 하단 참조.

1. **함수 브레이스**: next-line(현행 K&R) 유지 vs Google식 attached 통일 — *권장: 현행 유지*
2. **snake_case 자유함수**(`qfunc_inv`, `erf_m`, `xor_r25` 등): PascalCase로 개명 vs 유지 — *개명은 호출부 파급 있음*
3. **Yoda 조건**(`TRUE == x`): 유지 vs 일반 순서(`x == TRUE`)로 통일
4. **소스 인코딩**: UTF-8(권장) 확정 + MSVC `/utf-8` 플래그 적용 여부
