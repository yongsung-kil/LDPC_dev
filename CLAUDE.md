# CLAUDE.md: AI 작업 진입점

> **모든 작업 시작 전 이 파일을 읽을 것.**
> 이 저장소는 다섯 갈래의 하위 프로젝트를 담는다. 각 프로젝트는 자기 `_pm/`과 `docs/`를 가지며, 루트는 공통 사항만 관리한다.

---

## 저장소 구성

| 경로 | 역할 | 작업 진입점 |
|------|------|------------|
| `0_LDPC_original/` | 외부 원본 C++ 소스(`src/`)와 공용 C++ 문서(`docs/`) (참조 전용, 일부 손상으로 빌드 불가) | `0_LDPC_original/CLAUDE.md` |
| `1_LDPC_revised/` | Project 1: 원본의 속도, 메모리 최적화 (수정 파일만 보관) | `1_LDPC_revised/_pm/TODO.md` |
| `2_LDPC_base/` | Project 2: 경량 Python 시뮬레이터 (src 정본과 기준 실험 workspace/) | `2_LDPC_base/_pm/TODO.md` |
| `3_LDPC_ideas/` | Project 3: 논문 아이디어의 접수(현황표)와 py 스크리닝 실험 | `3_LDPC_ideas/README.md` |
| `4_H_matrix_tool/` | Project 4: H-matrix 설계 툴 (PEG, lifting, 부호 선별) | `4_H_matrix_tool/_pm/TODO.md` |
| `5_DAO/` | Project 5: DAO(Decoder Auto Optimizer, LLR matrix 자동 최적화기) 발전 (원형 스냅샷은 `reference/`) | `5_DAO/_pm/TODO.md` |
| `_pm/` | 저장소 공통 작업 관리 | `_pm/TODO.md` |

---

## 프로젝트 간 흐름

- ㉮ `0_LDPC_original/`은 외부에서 가져온 원본이며 이 환경에서는 완성 대상이 아니다 (참조 전용)
- ㉯ `1_LDPC_revised/`에서 기능을 논의, 확정한 것만 외부 저장소로 반영한다 (단방향, 외부에서 이쪽으로 가져오지 않음)
- ㉰ `2_LDPC_base/`는 외부의 H-matrix와 파라미터를 넣어도 동작하는 것이 목표이며, 외부에서 pull하여 성능을 확인한다
- ㉱ `3_LDPC_ideas/`(Project 3)는 아이디어 현황표와 아이디어별 실험을 담당한다. py 실험은 `2_LDPC_base`의 src 정본을 import해 수행한다 (복사 금지)
- ㉲ `4_H_matrix_tool/`(Project 4)은 H-matrix 설계 도구를 담당한다. 디코딩과 FER 측정은 `2_LDPC_base`의 src 정본을 import해 수행하고(복사 금지), 결과는 Ref-C 포맷 파일로 공급한다
- ㉳ `5_DAO/`(Project 5)는 SSS 저장소에서 반입한 DAO를 발전시킨다. 반입 시점 원형은 `5_DAO/reference/`에 보존한다 (참조 전용, 수정 금지)

---

## 논문 아카이브 (형제 저장소)

- ㉮ 논문 분석 아카이브는 형제 폴더 `../LDPC_Paper_Analysis`에 있다 (별도 git 저장소, 원격 이름 ECC_papers)
- ㉯ 담긴 것: 논문 PDF와 추출 텍스트(`data/pdfs/`), 메타데이터 DB(`data/papers.db`), 선별 기준과 결과(`criteria/`), 논문 탐색기(`docs/papers.html`, 공개 주소 https://yongsung-kil.github.io/ECC_papers/)
- ㉰ 아이디어 적용 작업에서 근거 논문의 원문이 필요하면 이 아카이브에서 논문 ID로 찾아 읽는다
- ㉱ 적용 상태의 정본은 `3_LDPC_ideas/README.md`의 아이디어 현황표이며, 상태를 아카이브 탐색기에 반영하는 절차는 아카이브 쪽 `_pm/tasks/20260812_작업공간재구성/재구성계획.md`를 따른다

---

## 대화 시작 시

- ㉮ 루트 `_pm/TODO.md` 확인 ("새 작업 추가" 섹션에 새 항목이 있으면 작업 목록으로 이동 후 시작 여부 확인)
- ㉯ 특정 프로젝트 작업이면 해당 프로젝트의 `_pm/TODO.md`도 확인

---

## 공통 규칙

- ㉮ C++ 빌드와 실행은 이 환경에서 하지 않는다 (원본 소스 일부 손상, 검증은 외부에서 수행). Python(`2_LDPC_base/`)은 로컬 실행 가능
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
  수단이 아니라 목적이 이름이 된다. 사용자가 모를 수 있는 업계 용어와 축약어는 풀어 쓴다
- ㉱ **줄표와 가운뎃점 금지**: 줄표(em dash, U+2014)와 가운뎃점(middle dot, U+00B7)을
  문장에 쓰지 않는다. 접속은 접속사나 쉼표로, 부연은 괄호로, 나열은 쉼표로 쓴다
  (수식의 곱셈 기호 용법은 예외)

---

## 작업 전 추가 로드

| 작업 유형 | 추가로 읽을 것 |
|-----------|---------------|
| C++ 디코더 로직 (revised 포함) | `0_LDPC_original/CLAUDE.md` (상수, 스위치, 실수 포인트) + `0_LDPC_original/docs/architecture.md` |
| 1_LDPC_revised 속도 최적화 | `1_LDPC_revised/README.md` + `1_LDPC_revised/docs/speed_opt/checklist.md` |
| 2_LDPC_base | `2_LDPC_base/README.md` (확정 결정 기록 절 포함) |
| 논문 아이디어 추가 (3_LDPC_ideas) | `3_LDPC_ideas/새논문적용규칙.md` + `3_LDPC_ideas/README.md` |
| 논문 이식성 판정 | `0_LDPC_original/docs/paper_screening_profile.md` |
| H-matrix 설계 (4_H_matrix_tool) | `4_H_matrix_tool/README.md` |
| DAO (5_DAO) | `5_DAO/README.md` + `5_DAO/DAO_spec.md` |
| 새 디코딩 모드 추가 | `0_LDPC_original/docs/architecture.md` 전체 + `0_LDPC_original/docs/adr/` 전체 |
| 빌드, 인프라 | 이 파일만으로 충분 |

---

## 참조 문서

[루트 TODO](_pm/TODO.md) | [architecture.md](0_LDPC_original/docs/architecture.md) | [dependency_map](0_LDPC_original/docs/dependency_map.md) | [ADR](0_LDPC_original/docs/adr/README.md) | [guide/](0_LDPC_original/docs/guide/) | [0_LDPC_original/CLAUDE.md](0_LDPC_original/CLAUDE.md) | [3_LDPC_ideas/](3_LDPC_ideas/README.md)
