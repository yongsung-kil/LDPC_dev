# CLAUDE.md — AI 작업 진입점

> **모든 작업 시작 전 이 파일을 읽을 것.**
> 이 저장소는 세 갈래의 하위 프로젝트를 담는다. 각 프로젝트는 자기 `_pm/`과 `docs/`를 가지며, 루트는 공통 사항만 관리한다.

---

## 저장소 구성

| 경로 | 역할 | 작업 진입점 |
|------|------|------------|
| `LDPC_Original/` | 외부 원본 C++ 소스 (참조 전용, 일부 손상으로 빌드 불가) | `LDPC_Original/CLAUDE.md` |
| `ldpc_revised/` | Project 1: 원본의 속도, 메모리 최적화 (수정 파일만 보관) | `ldpc_revised/_pm/TODO.md` |
| `ldpc_light/` | Project 2: 논문 아이디어 스크리닝용 경량 Python 시뮬레이터 | `ldpc_light/_pm/TODO.md` |
| `docs/` | 공용 문서 (architecture, ADR, guide, style) | `docs/architecture.md` |
| `ideas/` | 아이디어 저장소 (추후 Project 3, 논문 적용의 씨앗) | `ideas/README.md` |
| `_pm/` | 저장소 공통 작업 관리 | `_pm/TODO.md` |

---

## 프로젝트 간 흐름

- ㉮ `LDPC_Original/`은 외부에서 가져온 원본이며 이 환경에서는 완성 대상이 아니다 (참조 전용)
- ㉯ `ldpc_revised/`에서 기능을 논의, 확정한 것만 외부 저장소로 반영한다 (단방향, 외부에서 이쪽으로 가져오지 않음)
- ㉰ `ldpc_light/`는 외부의 H-matrix와 파라미터를 넣어도 동작하는 것이 목표이며, 외부에서 pull하여 성능을 확인한다
- ㉱ 추후 Project 3에서 `ldpc_light`를 받아 논문 아이디어를 적용한다 (ldpc_light가 외부 파라미터로 동작하는 시점에 폴더 신설)

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

- ㉮ C++ 빌드와 실행은 이 환경에서 하지 않는다 (원본 소스 일부 손상, 검증은 외부에서 수행). Python(`ldpc_light/`)은 로컬 실행 가능
- ㉯ 변경 금지 대상: TV 출력 hex 포맷, HCU 버퍼 레이아웃, Partial CRC 다항식, H-matrix 파일 포맷 (상세: `LDPC_Original/CLAUDE.md`)
- ㉰ 변경 등급을 지킨다 (아래 표)

| 등급 | 대상 | 처리 |
|------|------|------|
| Safe | 로그, 포맷, 주석 | 자동 진행 |
| Review | 로직 변경, 동작 유지 의도 | 브리핑 후 진행 |
| Decision | 설계 변경, 영향 범위 큼 | **작업 멈추고 사용자 확인** |

---

## 작업 전 추가 로드

| 작업 유형 | 추가로 읽을 것 |
|-----------|---------------|
| C++ 디코더 로직 (revised 포함) | `LDPC_Original/CLAUDE.md` (상수, 스위치, 실수 포인트) + `docs/architecture.md` |
| ldpc_revised 속도 최적화 | `ldpc_revised/README.md` + `ldpc_revised/docs/speed_opt/checklist.md` |
| ldpc_light | `ldpc_light/README.md` + `ldpc_light/docs/plan.md` |
| 논문 이식성 판정 | `docs/paper_screening_profile.md` |
| 새 디코딩 모드 추가 | `docs/architecture.md` 전체 + `docs/adr/` 전체 |
| 빌드, 인프라 | 이 파일만으로 충분 |

---

## 참조 문서

[루트 TODO](_pm/TODO.md) | [architecture.md](docs/architecture.md) | [dependency_map](docs/dependency_map.md) | [ADR](docs/adr/README.md) | [guide/](docs/guide/) | [LDPC_Original/CLAUDE.md](LDPC_Original/CLAUDE.md) | [ideas/](ideas/README.md)
