# DONE: 완료 이력 (3_LDPC_ideas, 논문 아이디어 적용)

### 2026-11-06 대시보드 카드를 아이디어 한 줄, 결과 한 줄로 줄임
카드에 요약의 bullet 전부를 싣던 것을 두 항목의 첫 bullet 하나씩으로 줄이고, 7편 README 요약의 첫 bullet을 핵심 한 문장으로 다시 씀
- **배경**: 사용자 지시 (2026-11-06, "카드 글이 너무 많아. 핵심만 짧게"). 카드는 README 요약의 1단계 bullet 전부를 실어 카드 하나가 세로 700px를 넘었음
- **변경**:
  - render.py: 카드 본문을 `<dl class="gist">`의 아이디어 줄(논문 아이디어 첫 bullet)과 결과 줄(실험 결과 첫 bullet에서 `**판정: …**.` 머리를 뺀 나머지)로. 머리줄의 한 줄 사유(status-note)는 카드에서 뺌 (결과 줄이 대신함)
  - README 7편(001-007) 요약 절: 논문 아이디어 첫 bullet을 "논문이 바꾸자는 것 한 문장"으로, 실험 결과 첫 bullet을 "판정 뒤 핵심 한 문장(핵심 수치와 성립 조건, 약어 풀이)"으로 다시 씀. 배경 설명은 둘째 bullet으로 내리고 수치와 주장은 그대로 둠
  - 보고서작성규칙.md 16절 표(판정 점과 낱말, 아이디어 줄, 결과 줄)와 8절 판정 bullet 규칙, _template/README.md 요약 양식, README.md 동작 흐름 ㉯를 같은 규칙으로 갱신
- **파일**: 3_LDPC_ideas/render.py, 루트 index.html, 00{1-7}_*/README.md와 README.html, 보고서작성규칙.md와 html, _template/README.md, README.md와 README.html

### 2026-11-06 대시보드 틀을 조용하게 다듬기 (unslop 스킬 적용)
클로드 코드 스킬 unslop(heydamir/unslop, CC BY 4.0)의 진단대로 대시보드의 꾸밈을 걷어내고, 색은 실험 결과 수치(개선 빨강, 열화 파랑)와 판정 점에만 남김
- **배경**: 사용자 지시 (2026-11-06). 진단에서 판정 배지가 단색 채움 알약, 카드마다 5px 색 띠, 상단 링크 6개가 알약, 집계 상자와 번호가 굵기 600-700, 글자 크기 열 가지, 4px 눈금 밖 여백, 같은 줄 카드를 가장 긴 카드 높이로 늘려 생긴 빈 공간이 나옴. 이모지, 그라데이션, 느낌표는 없어 다듬기 모드로 진행
- **변경**:
  - render.py `DASH_STYLE`: 여백을 4px 눈금(4, 8, 12, 16, 20, 32)으로, 글자 크기를 28/17/16/15/14/13 여섯 단계로, 굵기는 500과 600만. 상단 링크를 글자 링크 줄로, 집계를 상자 없이 작은 라벨과 28px 모노스페이스 숫자로, 카드 띠와 호버 그림자를 없애고 호버는 바탕 한 단계(150ms, 완화 곡선 하나). 카드 격자 `align-items: start`로 카드가 자기 내용만큼만 길어짐. 포커스 링 추가
  - render.py `build_card`, `build_stats`: 판정 배지를 "판정 점"(8px 원, 유효 초록 `--ok`, 실패 파랑 `--worse`, 실험중 주황 `--warn`)과 글자로 바꾸고, 집계 라벨에도 같은 점을 붙여 카드와 집계가 같은 표시를 씀
  - 팔레트(`THEME_STYLE`), 시스템 글꼴, 카드 격자 배치, 카드 내용과 순서, 문서 페이지 스타일은 그대로
  - 전후 보존: `_test/20261106_unslop_dashboard/` (before/after의 index.html, render.py, 밝은/어두운 화면). 되돌리기는 `git revert` 또는 `git checkout fc1e202 -- 3_LDPC_ideas/render.py index.html`
- **파일**: 3_LDPC_ideas/render.py, 루트 index.html

### 2026-11-05 html을 md 옆으로 되돌리고 대시보드를 저장소 루트 index.html로 (GitHub Pages 소스는 루트)
md와 html의 자리를 하나로 유지하기 위해 docs/ 모음 구조를 접고, Pages 소스를 저장소 루트로 두는 전제로 html은 md 옆, 대시보드는 루트 index.html에 둠
- **배경**: 사용자 결정 (2026-11-05). docs/ 아래 모음 구조는 md와 html이 갈라져 관리 자리가 둘이 되고, 저장소 전체를 복사해 가므로 "docs 하나만 복사"의 이점이 쓰이지 않음. 다른 저장소의 Pages 소스를 루트 `/`로 두면 어느 폴더의 html이든 그대로 열림
- **변경**:
  - render.py: 산출 경로를 md 옆(`html_path_for`는 같은 이름 .html)으로, 대시보드를 `REPO_ROOT/index.html`로. 상대 링크 재계산과 링크 검사는 유지. 묵은 산출물 정리는 3_LDPC_ideas/ 안에서 표식(`<!-- render.py가 `)이 있는 html만 지움 (Sim_Output, __pycache__ 제외)
  - docs/ 폴더 삭제 (index.html, .nojekyll, 보고서 html 16편). 루트 `.nojekyll`은 유지
  - 루트 CLAUDE.md 저장소 구성 표의 docs/ 행을 index.html 행으로, README.md(머리말 링크, 동작 흐름 7단계, 폴더 규칙 ㉴), 새논문적용규칙.md 6절 ㉴, 보고서작성규칙.md 16절의 html 위치 설명 갱신
- **파일**: 3_LDPC_ideas/render.py, 루트 index.html, 3_LDPC_ideas/README.md와 README.html, 00{1-7}_*/README.html, 실험로그.html, 두 규칙 html, _pm/tasks/전력감축_논문정독/메모_*.html(5편), 루트 CLAUDE.md, 새논문적용규칙.md, 보고서작성규칙.md

### 2026-11-05 보고서 html을 저장소 루트 docs/ 아래로 모아 뽑기 (GitHub Pages 카드 404 수리)
render.py의 산출물을 전부 루트 docs/ 아래에 md와 같은 폴더 구조로 두어, docs/ 폴더 하나만 복사해도 대시보드와 카드 링크가 이어지게 함
- **배경**: 대시보드 docs/index.html을 다른 저장소의 GitHub Pages로 열면 카드가 404였음. 카드 링크가 `../3_LDPC_ideas/…/README.html`로 docs 바깥을 가리켰고, Pages 소스가 `/docs`이면 docs 바깥은 서빙되지 않음
- **변경**:
  - render.py: 산출 경로를 `docs/{md의 저장소 기준 경로}.html`로 통일(`html_path_for`). 본문의 상대 링크를 html 위치 기준으로 다시 계산(변환 대상 md는 그 html로, 그 밖의 파일은 저장소의 그 파일로). 대시보드 카드, 상단 링크, 메모 링크, "대시보드로" 링크 모두 docs/ 안에서 닫힘. docs/.nojekyll 생성, 이번에 만들지 않은 docs/ 안 html 정리, 저장소 밖 파일 인자 거부
  - md 옆의 html 16편 삭제(html은 docs/에 한 벌만)
  - 루트 CLAUDE.md docs/ 행, README.md(동작 흐름 7단계와 폴더 규칙 ㉴), 새논문적용규칙.md 6절 ㉴, 보고서작성규칙.md 16절의 html 위치 설명을 새 구조로
- **파일**: 3_LDPC_ideas/render.py, docs/ (index.html, .nojekyll, 3_LDPC_ideas/ 아래 html 16편), 루트 CLAUDE.md, 3_LDPC_ideas/README.md, 새논문적용규칙.md, 보고서작성규칙.md

### 2026-11-04 아이디어 보고서 양식 개편과 대시보드 생성
아이디어 README 7편을 새 양식(요약 다섯 항목, 개조식 bullet, 개선 빨강과 열화 파랑)으로 다시 쓰고, render.py가 README에서 카드형 대시보드 index.html을 만들게 함
- **배경**: 사용자 첨삭 (2026-11-04). 논문별 요약을 한눈에 보는 상위 페이지가 없었고, 요약 항목 이름이 의문문형이었으며, "그림자 측정" 같은 비유어와 긴 줄글이 읽기 어려웠음. 실험 결과를 요약만 읽고도 알 수 있어야 한다는 요구
- **변경**:
  - 보고서작성규칙.md: 요약 항목 이름 고정(논문 아이디어, 제안 이유, 성공시 효과, 개선 확인방법, 실험 결과), 절 이름 고정(평가 계획 등), 색 두 가지(`better` 빨강, `worse` 파랑), 출처 상세 형식, 비유어 치환표, 대시보드 카드 재료(16절)
  - 새논문적용규칙.md 6절을 새 항목 이름으로 갱신, `_template/README.md` 새 양식, 루트 CLAUDE.md 작업 전 로드 표에 보고서작성규칙.md 추가
  - README 7편(001-007) 전면 다시 쓰기: 요약에 실험 결과 추가, 본문 bullet 명사형, 1. 2. 3. 번호, 표 앞 h4와 조건/핵심 인용 블록, 결과 표와 지표별 해석에 색 표시, 비유어 제거(그림자 측정은 기록 전용 측정, 사망/붕괴는 전 프레임 실패, 견딤 한계는 복호 가능 상한, 사다리는 단계 비교 구성, 발화는 정지 조건 성립). 002는 첨삭 반영본(README_ver2)을 정본으로 합치고 ver2 파일 삭제
  - render.py: 대시보드 index.html 생성(카드: 번호, 상태 배지, 제목, 출처, 특징, 실험 결과, 상세 보고서와 논문 분석 메모 링크. 상단에 동작 흐름, 논문 분석 아카이브, 현황표, 실험 로그, 규칙 링크), :root css 변수와 어두운 모드, 제목 id(slugify_unicode), 링크로 참조된 md(_pm/tasks의 분석 메모)도 함께 변환, 변환 대상이 아닌 md 링크는 .md 유지, 렌더 뒤 상대 링크와 앵커 검사, 문서 페이지 상단에 대시보드 링크
  - README.md(현황표): 동작 흐름 절 신설(8단계 표), 디렉토리 칸을 README 링크로, 상태 낱말 통일(조건부 유효 / 실패), 대시보드 안내
  - 실험로그.md: 비유어와 판정 낱말 치환(그림자 측정, 붕괴, 사망, 건강, 급소, 수확, 흑자, 유의미/무의미), 수식 가운뎃점을 ×로
- **파일**: 3_LDPC_ideas/render.py, index.html, README.md, 보고서작성규칙.md, 새논문적용규칙.md, 실험로그.md, _template/README.md, 00{1-7}_*/README.md와 형제 html, _pm/tasks/전력감축_논문정독/메모_*.html(5편), 루트 CLAUDE.md
