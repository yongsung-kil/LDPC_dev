# DONE — 완료 이력 (저장소 공통)

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
