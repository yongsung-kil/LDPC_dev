# TODO: 저장소 공통 작업

> Claude 마지막 확인: 2026-09-30 05:05:26

> 이 파일은 저장소 공통 작업만 관리한다.
> 프로젝트별 작업은 각 프로젝트의 `_pm/TODO.md`를 볼 것.

---

## 작업 목록

- [ ] Claude 플러그인 AI_Assisted_Dev 제작 (LDPC_dev 형제 폴더에 새 저장소, 통합 저장소 작업과 병행)
  - 상세: `_pm/tasks/20260929_AI_Assisted_Dev_플러그인/`
  - [x] 초안(make_plugin.md) 조사와 판정요청 7건 답 (2026-09-29)
  - [x] 설계 문서 검토 (2026-09-30, 위키 tech 갈래와 안정성 검사와 소개 페이지 추가)
  - [x] 실행 계획 검토 (2026-09-30, 마커 1건 반영)
  - [x] 1단계 마감 판정요청 6건 답 (2026-09-30, 전부 권고대로. 이후 결정은 8단계 뒤 한 번에)
  - [x] 저장소 뼈대와 pm, doc-check 스킬 (2026-09-30, 형제 폴더 AI_Assisted_Dev에 커밋 11개. 세션 시작 자동 실행과 두 스킬을 시험장 실제 실행으로 확인)
  - [x] onboard, explore, wiki 스킬 (프로젝트 프로파일) (2026-09-30, 시험장 onboard 실제 실행 진행 중)
  - [x] dashboard (자료 양식과 스크립트, html_guide.md, 자기 적용 확인) (2026-09-30)
  - [x] idea-apply, speed-opt, robustness-check(안정성 검사), param-opt 스킬 (2026-09-30)
  - [x] paper-search, paper-screen, paper-analyze 스킬 (2026-09-30, arXiv API와 내보내기 CSV 두 통로)
  - [x] plan, review, debug, test-design 스킬 이관 (2026-09-30)
  - [x] evals 13건과 배포 준비 (marketplace.json, 설치 안내) (2026-09-30)
  - [x] 소개 페이지 docs/intro.html (2026-09-30)
  - [x] 라이트 리뷰(2단계부터 8단계, Important 7건 반영), 시험장 onboard와 dashboard 실행 확인, 판 0.1.0 태그 (2026-09-30)
  - [x] 시험장 wiki 실행 결과 확인 (2026-09-30. 첫 실행은 비대화 실행의 배경 작업 상한 600초에 끊겨 `_inbox/` 초안 75편에서 5단계부터 이어서 실행. 결과 decisions 25편, trials 7편, assets 22편, tech 21편, 문서 검사 0건, 개인 경로 0건. wiki 스킬에 이어서 하기 규칙을 넣어 플러그인 저장소에 커밋 766f2f4)
  - [x] 대시보드 화면 개편 (2026-09-30. 사용자 지시: 사이드바를 온보딩, 작업 관리, 논문, 아이디어 적용, 최적화, 위키 묶음으로, 단계별 글자 크기와 접기, 첫 화면은 계획과 진행 중과 완료 보드, 변경 이력 페이지, 소개 페이지도 같은 틀. 라이트 리뷰 3건 반영, 테스트 101건 통과, 플러그인 저장소 커밋)
  - [x] 예시 저장소 분리 (2026-09-30. 시험장 사본을 형제 폴더 ldpc_py로 옮기고 GitHub 비공개 저장소 yongsung-kil/ldpc_py에 올림. 플러그인 소개 페이지의 바깥 링크 제거, 회사망 표현 교체)
  - [x] 예시 저장소 채우기와 대시보드 개편 2차 (2026-09-30. 묶음을 온보딩, 작업 관리, 외부 기술문서, 아이디어 적용, 최적화, 내부 기술문서로. 논문 탐색기 페이지(검색 도구, 색 갈래), 온보딩 사용법 문서, 최적화 도구 제작 안내, 제목 색. ldpc_py에 아카이브 6,053편과 분석 md 반입, 최적화 뼈대. 플러그인 커밋 f689c7e부터 5c37b5d)
  - [ ] 대시보드 개편 3차 답 대기 (제목 색 방식, "아이디어 적용" 대신 쓸 말, 사이드바 순서)
  - [ ] 판정요청 3건 답 대기 (`판정요청_플러그인마감_260930.md`)
- [ ] 통합 저장소 AI_Assisted_ECC_Dev 구성 (LDPC_dev + LDPC_Paper_Analysis를 새 저장소 하나로)
  - 상세: `_pm/tasks/20260826_AI_Assisted_ECC_Dev_통합/`
  - [x] 요구 파악과 확정 사항 정리 (2026-08-26)
  - [ ] 사용자 결정 9건 (`판정요청.md`)
  - [ ] 설계 문서 작성과 검토
  - [ ] 실행 계획 작성 → 조립 → 공간별 검토와 커밋
- [ ] 001 이중 상한 클리핑의 적용 판정 (3_LDPC_ideas 001, 평가 대상 파라미터 기준)
  - 상세: `_pm/tasks/20260907_review_001_th_clipping/` (분석메모.md가 정본, 리뷰 기록 포함)
  - [x] th의 클리핑 역할 분석과 라이트 리뷰 (2026-09-07, 발견 32건 반영)
  - [ ] 001 문서 어긋남 4건 수리 (README 반전 조건 식, 결과표 열 이름, config_target 채널 슬롯, 실험로그 동점)
  - [ ] 판정 절차 C10 ㉮~㉲ 실행 여부 결정
- [ ] 0_LDPC_original 디코딩 알고리즘 요약 문서 정비
  - 기존 상세 분석 문서(세부 기능까지 기술)는 과하다는 판단으로 구 저장소 아카이브에 남김
  - `0_LDPC_original/docs/guide/algorithms.md`가 요약 역할을 하는지 점검하고, 부족하면 기능 수준의 간단한 설명 1편으로 보강
## 새 작업 추가

(비어 있음)

---

## 프로젝트별 TODO

| 프로젝트 | TODO 위치 |
|----------|-----------|
| 1_LDPC_revised (Project 1) | `1_LDPC_revised/_pm/TODO.md` |
| 2_LDPC_base (Project 2) | `2_LDPC_base/_pm/TODO.md` |
| 3_LDPC_ideas (Project 3) | `3_LDPC_ideas/_pm/TODO.md` |
| 4_H_matrix_tool (Project 4) | `4_H_matrix_tool/_pm/TODO.md` |
| 5_DAO (Project 5) | `5_DAO/_pm/TODO.md` |
