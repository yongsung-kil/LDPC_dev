# DONE — 완료 이력 (저장소 공통)

### 2026-08-14 — Project 4 (4_H_matrix_tool), Project 5 (5_DAO) 신설
H-matrix 설계 툴을 독립 프로젝트로 승격하고, SSS의 DAO를 반입
- **배경**: H-matrix 설계 도구와 DAO를 각각 독립 프로젝트로 발전시키기로 함 (사용자 결정 2026-08-14)
- **변경**: 2_LDPC_base/tools/H_mat_gen/의 4개 모듈을 4_H_matrix_tool/src/로 이동 (import는 2_LDPC_base/src 상위 탐색 부트스트랩으로 전환, 생성 결과가 기존 정본과 동일함을 확인). SSS 저장소의 DAO를 5_DAO/로 반입 (원형 스냅샷은 reference/에 보존, __pycache__와 msmpisetup.exe 제외). select_irregular 손질 TODO를 4번으로 이전
- **파일**: 4_H_matrix_tool/, 5_DAO/, 2_LDPC_base/ (README.md, __init__.py, _pm/TODO.md, tools/ 삭제), CLAUDE.md, .gitignore, _pm/TODO.md

### 2026-08-10 — 현행 문서에서 구 저장소(LDPC_2) 참조 제거
현행 문서가 구 저장소를 가리키지 않도록 관련 서술 삭제 (구 저장소 폴더 자체는 보존)
- **배경**: 현 저장소가 구 저장소의 상위 버전이라 문서가 독자를 구 저장소로 보낼 이유가 없음 (사용자 결정 2026-08-10). 이력 기록(_pm/done/, DONE.md, 리뷰 아카이브)의 언급은 이력이므로 보존
- **변경**: 루트 CLAUDE.md 히스토리 절 삭제, 0_LDPC_original/CLAUDE.md의 아카이브 링크 2곳 제거, paper_screening_profile.md의 코드 정체 서술을 현행 경로(0_LDPC_original/src/)로 갱신
- **파일**: CLAUDE.md, 0_LDPC_original/CLAUDE.md, 0_LDPC_original/docs/paper_screening_profile.md

### 2026-08-10 — 루트 docs/를 0_LDPC_original/ 하위로 이동, C++ 소스를 src/로 정리
루트 docs가 전부 원본 C++ 문서라 원본 폴더 아래로 통합
- **배경**: 루트 docs/의 문서(architecture, dependency_map, ADR, guide, style, paper_screening_profile)가 모두 원본 C++ 코드베이스를 다루는 내용이라 루트에 둘 이유가 없었음 (사용자 결정 2026-08-10)
- **변경**: 0_LDPC_original/src/ 신설 후 C++ 소스와 build.bat 이동, 루트 docs/ 전체를 0_LDPC_original/docs/로 이동. 문서 안의 소스 경로에 src/ 삽입, 구 저장소(LDPC_2) 시절 낡은 참조(DAO 언급, 아카이브로 넘어간 문서 링크)를 아카이브 경로로 수리
- **파일**: 0_LDPC_original/ (src/, docs/, CLAUDE.md), CLAUDE.md, _pm/TODO.md, .gitignore, 2_LDPC_light/docs/차이.md

### 2026-08-10 — 루트 ideas/ 폐지, Project 3 폴더 신설 (3_LDPC_ideas/)
아이디어 대장과 폴더 양식을 3_LDPC_ideas/로 이관하고 루트 ideas/를 삭제
- **배경**: 루트 ideas/의 역할(아이디어별 코드, 로그, 결과 관리)이 2_LDPC_light/Ideas/ registry 방식과 겹쳤고, Project 3에 흡수될 예정이었음 (사용자 결정 2026-08-10)
- **변경**: 3_LDPC_ideas/ 신설 (아이디어 대장 README, _template/, _pm/TODO.md). 본격 착수는 2_LDPC_light가 외부 H-matrix와 파라미터로 동작 확인된 뒤. 루트 ideas/ 삭제, CLAUDE.md 구성 표와 프로젝트 간 흐름 갱신
- **파일**: 3_LDPC_ideas/, CLAUDE.md, _pm/TODO.md

### 2026-08-05 — 프로젝트 재구성 (LDPC_2 → LDPC_dev)
구 LDPC_2 저장소에서 필요한 내용만 옮겨 새 저장소로 재구성
- **배경**: 성격이 다른 세 갈래(원본 참조, 속도 최적화, 경량 시뮬레이터)가 한 폴더에 섞여 있었고, 구 `_pm/` 이력과 상세 분석 문서가 과하게 누적됨
- **변경**: 형제 폴더 `LDPC_dev/` 신설, 새 git 저장소로 시작. 프로젝트별 `_pm/`과 `docs/` 분리 (1_LDPC_revised, 2_LDPC_light). 구 LDPC_2는 아카이브로 보존
- **파일**: 상세 기록 `_pm/done/20260805_프로젝트재구성/`
