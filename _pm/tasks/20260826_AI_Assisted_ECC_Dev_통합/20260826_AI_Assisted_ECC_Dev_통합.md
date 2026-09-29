# 통합 저장소 AI_Assisted_ECC_Dev 구성

> 작성: 2026-08-26 23:04:16
> 상태: 설계 중 (사용자 결정 대기: [판정요청.md](%ED%8C%90%EC%A0%95%EC%9A%94%EC%B2%AD.md))
> 변경 등급: Decision (저장소 신설과 재배치)

---

## 목적

LDPC_dev와 LDPC_Paper_Analysis(원격 이름 ECC_papers) 두 저장소를 새 저장소
`AI_Assisted_ECC_Dev` 하나로 합쳐 AI-assisted LDPC code 개발 환경을 만든다.
이유는 세 가지다.

- ㉮ 저장소 둘을 따로 관리하는 부담
- ㉯ 두 저장소가 서로 연관됨 (논문 분석 → 아이디어 실험 → 본체 반영)
- ㉰ 결과를 한 사이트에서 열람

## 배경과 흐름

- ㉮ 개인 GitHub의 새 저장소는 **비공개**다 (https://github.com/yongsung-kil/AI_Assisted_ECC_Dev.git, 기본 브랜치 `main`, 비어 있음)
- ㉯ 모든 작업은 이 PC에서 하고, 사내에서 pull하여 supercom 환경에서 추가 실험이
  필요하면 진행한 뒤 회사 GitHub Enterprise에 올린다. 사이트는 그곳의 Pages로
  내고 Confluence가 iframe으로 미러링한다
- ㉰ 사내 사람들이 커밋 이력을 보므로, 검토를 거친 내용만 커밋한다. 과거 두 저장소의
  커밋 이력은 가져오지 않는다
- ㉱ 개인 저장소가 비공개라 사이트 확인은 로컬 서버로 한다. 사이트는 어느 호스트에
  올라가도 되도록 절대 주소를 쓰지 않는다

## 확정 사항

| 항목 | 결정 |
|------|------|
| 저장소 이름 | `AI_Assisted_ECC_Dev` (사용자 생성). 로컬 폴더 `D:\OneDrive\My_Projects\AI_Assisted_ECC_Dev\` |
| 제목 표기 | "AI-assisted" (예: AI-assisted LDPC code 개발 환경) |
| 시작 방식 | 새 폴더에 조립. 구 저장소 두 개의 뒤처리는 사용자가 직접 |
| 공간 폴더 | `1_ECC_papers`(논문 분석), `2_LDPC_revised`, `3_LDPC_base`, `4_LDPC_ideas`, `5_H_matrix_tool`, `6_DAO`. 기존 이름을 유지하고 번호만 1부터 다시 매김 |
| 로컬 전용(아카이브, git 무시) | `0_LDPC_original`, DAO 원형 스냅샷 `reference/`(작업본과 동일하므로 한 벌만 옮김), 임원 발표용 페이지와 그 설계 문서 |
| 1_LDPC_revised | 전부 포함. 다른 공간의 LDPC 최적화(C++)에 쓰기 위함 |
| 논문 데이터 | 전부 포함 (약 400MB: PDF 추출 텍스트, 카탈로그, 분석 md, papers.db, papers.json). PDF 원본은 git 미추적 유지 |
| 입력 파일 | H-matrix와 LLR 파일 전부 포함 |
| `_pm/` | 초기화. 각 프로젝트 TODO의 미완 항목만 문장을 새로 써서 옮기고, DONE과 done/, 완료된 tasks/는 구 저장소에만 |
| README | 루트 README는 새로 씀 |
| 사이트 루트 | 저장소 루트 (`.nojekyll`로 그대로 서비스). 사이트 구조 = 저장소 구조 |
| 페이지 | 메인 페이지 하나와 공간마다 페이지 하나. 메인이 공간 페이지를 참조. 임원 발표용 페이지는 구조만 참고하고 디자인은 새로 (기본 디자인 사용 가능) |
| 사이트 틀 | 사이드바형 (추후 수정 전제) |
| 문서와 html | md가 정본, html은 게시용. html마다 대응되는 md가 있고 md를 고치면 html에 반영. 아이디어용 자동 변환은 후속 |
| Base 페이지 | Reference-C 대비 설계 결정 관점으로 서술 |
| 원본 호칭 | Reference-C (Prime ECC 2.x). 불완전하다, 입력 파일 원본이 필요하다는 서술 금지 |
| 실험 환경 용어 | "local 환경"(이 PC, Python 스크리닝), "supercom 환경"(사내, Python+MPI와 C++ Reference-C, error floor 영역). 폴더는 나누지 않고 보고서 절로 구분 |
| supercom 결과 반입 | 미결정. 문서화만 하고 지금 다루지 않음 |
| 커밋 | 공간별 검토가 끝난 것부터 커밋을 쌓음. 첫 커밋은 뼈대 + 첫 공간 |

## 설계

설계안은 대화에서 절별로 제시했고, 판정요청의 답을 받은 뒤 이 폴더에
`설계.md`로 정리한다. 골자는 다음과 같다.

- ㉮ 저장소 구성: 루트에 CLAUDE.md(사내 독자 기준), CLAUDE.local.md(git 무시, 로컬 지시),
  README.md와 그 html, `_site/`(렌더러, 공간 목록, 흐름 그림), `_pm/`, `_archive/`(git 무시),
  공간 폴더 6개
- ㉯ 이름 치환: 번호 큰 것부터 내림차순 (5_DAO→6_DAO, 4_H_matrix_tool→5_H_matrix_tool,
  3_LDPC_ideas→4_LDPC_ideas, 2_LDPC_base→3_LDPC_base, 1_LDPC_revised→2_LDPC_revised,
  LDPC_dev→AI_Assisted_ECC_Dev, 저장소 이름으로 쓰인 ECC_papers와 LDPC_Paper_Analysis→1_ECC_papers).
  패치 파일과 구 `_pm/` 이력은 제외
- ㉰ 사이트: 렌더러가 site.json에 적힌 md만 html로 만들고, 모든 페이지에 같은 사이드바를
  넣고, 렌더 뒤 상대 링크와 금지 패턴을 검사. 탐색기는 raw 주소 대신 상대 경로로 분석 md를
  읽고, papers.json에 적용 상태 필드(applied, idea_dir, verdict)를 더해 아이디어 현황표와
  동기화
- ㉱ 문서 규칙: 금지 표현 목록(손상, 소실, 불완전, 빌드 불가, 입력 파일 출처, 개인 경로,
  개인 저장소 이름, AI 작업 환경 서술)으로 전수 검색 후 정비
- ㉲ 조립: manifest와 스크립트로 복사, 치환, 검증(렌더, 링크, 실행, fresh clone)
- ㉳ 커밋 순서: 뼈대 + 1_ECC_papers → 2_LDPC_revised → 3_LDPC_base → 4_LDPC_ideas →
  5_H_matrix_tool → 6_DAO → 탐색기 연동

## 수정 대상

- ㉮ 새 폴더 `D:\OneDrive\My_Projects\AI_Assisted_ECC_Dev\` 전체 (신규)
- ㉯ 구 저장소 LDPC_dev: 마감 커밋 여부는 판정요청 8번
- ㉰ Claude 메모리 폴더: 새 프로젝트 경로로 이전 (후속)

## 안전성 체크리스트

- [ ] 구 저장소 두 개는 조립 중 수정하지 않는다 (마감 커밋 제외)
- [ ] `_archive/`와 CLAUDE.local.md가 .gitignore에 들어간 뒤에 첫 커밋
- [ ] 커밋마다 금지 표현 검색 결과 0건 확인
- [ ] 렌더 후 링크 검사와 금지 패턴 검사 통과
- [ ] run.py 실행 검증 (base_run, 아이디어 001) 통과
- [ ] fresh clone에서 로컬 서버로 사이트 동작 확인

## 미결정 사항

- ㉮ 판정요청 9건: [판정요청.md](%ED%8C%90%EC%A0%95%EC%9A%94%EC%B2%AD.md)
- ㉯ supercom 환경 결과 반입 경로 (지금 다루지 않음)
- ㉰ 회사 GitHub Enterprise의 Pages 가능 여부 (사내 확인)
- ㉱ HTML 작성 가이드(html.md)의 게시 방법 절 갱신 시점 (사내 확인 뒤)
