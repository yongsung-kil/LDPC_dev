# CLAUDE.md: AI 작업 진입점

> **모든 작업 시작 전 이 파일을 읽을 것.**
> 이 저장소는 세 갈래의 하위 프로젝트를 담는다. 각 프로젝트는 자기 `_pm/`과 `docs/`를 가지며, 루트는 공통 사항만 관리한다.

---

## 저장소 구성

| 경로 | 역할 | 작업 진입점 |
|------|------|------------|
| `0_LDPC_original/` | 외부 원본 C++ 소스 (참조 전용, 일부 손상으로 빌드 불가) | `0_LDPC_original/CLAUDE.md` |
| `1_LDPC_revised/` | Project 1: 원본의 속도, 메모리 최적화 (수정 파일만 보관) | `1_LDPC_revised/_pm/TODO.md` |
| `2_LDPC_light/` | Project 2: 논문 아이디어 스크리닝용 경량 Python 시뮬레이터 | `2_LDPC_light/_pm/TODO.md` |
| `docs/` | 공용 문서 (architecture, ADR, guide, style) | `docs/architecture.md` |
| `ideas/` | 아이디어 저장소 (추후 Project 3, 논문 적용의 씨앗) | `ideas/README.md` |
| `_pm/` | 저장소 공통 작업 관리 | `_pm/TODO.md` |

---

## 프로젝트 간 흐름

- ㉮ `0_LDPC_original/`은 외부에서 가져온 원본이며 이 환경에서는 완성 대상이 아니다 (참조 전용)
- ㉯ `1_LDPC_revised/`에서 기능을 논의, 확정한 것만 외부 저장소로 반영한다 (단방향, 외부에서 이쪽으로 가져오지 않음)
- ㉰ `2_LDPC_light/`는 외부의 H-matrix와 파라미터를 넣어도 동작하는 것이 목표이며, 외부에서 pull하여 성능을 확인한다
- ㉱ 추후 Project 3에서 `2_LDPC_light`를 받아 논문 아이디어를 적용한다 (2_LDPC_light가 외부 파라미터로 동작하는 시점에 폴더 신설)

---

## 히스토리

- ㉮ 이 저장소는 2026-08-05에 구 `LDPC_2` 저장소에서 필요한 내용만 옮겨 새로 구성했다
- ㉯ 구 저장소는 아카이브로 보존한다 (`../LDPC_2/`, github.com/yongsung-kil/LDPC_2). 상세 분석 문서와 구 `_pm/` 이력은 그쪽에 있다
- ㉰ 재구성 기록: `_pm/done/20260805_프로젝트재구성/`

---

## 대화 시작 시

- ㉮ 루트 `_pm/TODO.md` 확인 ("새 작업 추가" 섹션에 새 항목이 있으면 작업 목록으로 이동 후 시작 여부 확인)
- ㉯ 특정 프로젝트 작업이면 해당 프로젝트의 `_pm/TODO.md`도 확인

---

## 공통 규칙

- ㉮ C++ 빌드와 실행은 이 환경에서 하지 않는다 (원본 소스 일부 손상, 검증은 외부에서 수행). Python(`2_LDPC_light/`)은 로컬 실행 가능
- ㉯ 변경 금지 대상: TV 출력 hex 포맷, HCU 버퍼 레이아웃, Partial CRC 다항식, H-matrix 파일 포맷 (상세: `0_LDPC_original/CLAUDE.md`)
- ㉰ 변경 등급을 지킨다 (아래 표)

| 등급 | 대상 | 처리 |
|------|------|------|
| Safe | 로그, 포맷, 주석 | 자동 진행 |
| Review | 로직 변경, 동작 유지 의도 | 브리핑 후 진행 |
| Decision | 설계 변경, 영향 범위 큼 | **작업 멈추고 사용자 확인** |

---

## 문장 작성 규칙 (코드 주석과 문서 공통)

- ㉮ **수리는 덧대기가 아니라 다시 쓰기**: 리뷰 반영이나 수정 시 기존 문장 뒤에 단서나
  괄호를 덧붙이지 않는다. 그 문장을 처음부터 그렇게 설계됐던 것처럼 다시 쓴다.
  과거가 어땠고 지금 어떻다는 서술을 코드와 문서에 남기지 않는다 (변경 이력은
  `_pm/DONE.md`와 git이 담당)
- ㉯ **규칙은 긍정문**: 하는 일을 바로 말한다. "~하지 않는다"로 시작해 뒤에서
  "실제로는 …한다"로 뒤집는 문형을 쓰지 않는다
- ㉰ **이름과 용어는 명확성 우선**: 함수명과 변수명은 길어져도 뜻이 그대로 읽혀야 하고,
  수단이 아니라 목적이 이름이 된다. 사용자가 모를 수 있는 업계 용어·축약어는 풀어 쓴다
- ㉱ **줄표 금지**: 줄표(em dash, U+2014)를 쓰지 않는다. 접속은 접속사나 쉼표로,
  부연은 괄호로 쓴다

---

## 작업 전 추가 로드

| 작업 유형 | 추가로 읽을 것 |
|-----------|---------------|
| C++ 디코더 로직 (revised 포함) | `0_LDPC_original/CLAUDE.md` (상수, 스위치, 실수 포인트) + `docs/architecture.md` |
| 1_LDPC_revised 속도 최적화 | `1_LDPC_revised/README.md` + `1_LDPC_revised/docs/speed_opt/checklist.md` |
| 2_LDPC_light | `2_LDPC_light/README.md` + `2_LDPC_light/docs/plan.md` |
| 논문 이식성 판정 | `docs/paper_screening_profile.md` |
| 새 디코딩 모드 추가 | `docs/architecture.md` 전체 + `docs/adr/` 전체 |
| 빌드, 인프라 | 이 파일만으로 충분 |

---

## 참조 문서

[루트 TODO](_pm/TODO.md) | [architecture.md](docs/architecture.md) | [dependency_map](docs/dependency_map.md) | [ADR](docs/adr/README.md) | [guide/](docs/guide/) | [0_LDPC_original/CLAUDE.md](0_LDPC_original/CLAUDE.md) | [ideas/](ideas/README.md)
