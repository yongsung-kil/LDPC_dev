# 논문 아이디어 적용

> 논문 아이디어를 `2_LDPC_base` 시뮬레이터에 하나씩 적용해 보고, 결과를 아이디어별
> 보고서와 현황표로 남기는 프로젝트. 한눈에 보는 화면은 [대시보드](../docs/index.html)
> (`python render.py`가 아이디어별 README에서 만든다).

---

## 동작 흐름

| 단계 | 하는 일 | 산출물 | 정본 문서 |
|------|---------|--------|----------|
| 1. 논문 선별 | 논문 분석 아카이브(형제 저장소 LDPC_Paper_Analysis)에서 이식 가능한 논문을 고름 | 후보 목록 (`_pm/TODO.md`) | 루트 CLAUDE.md의 논문 아카이브 절, `0_LDPC_original/docs/paper_screening_profile.md` |
| 2. 논문 분석 | 논문을 정독하고 현 디코더에 끼워 넣는 지점을 함수 단위로 적음 | 분석 메모 (`_pm/tasks/{작업}/메모_*.md`) | [새논문적용규칙.md](%EC%83%88%EB%85%BC%EB%AC%B8%EC%A0%81%EC%9A%A9%EA%B7%9C%EC%B9%99.md) 3절 (교체용 함수 표) |
| 3. 등록 | 아래 현황표에 번호와 상태를 올리고 `_template/`를 복사해 폴더를 만듦 | `{번호3자리}_{이름}/` | 새논문적용규칙.md 4절 1단계 |
| 4. 구현 | `2_LDPC_base/src`의 BaseDecoder를 상속해 논문이 바꾸는 함수만 재정의함 (복사 금지) | decoder.py, run.py, config.json | 새논문적용규칙.md 2절, 4절, 7절 |
| 5. py 스크리닝 | 기준선(base_run)과 같은 조건으로 on/off 비교하고 중간 지표를 모음 | `Sim_Output/` (git 무시) | 새논문적용규칙.md 5절 (평가 계획) |
| 6. 보고 | 아이디어 README에 요약, 평가 계획, 결과, 결론을 쓰고 실험로그에 환경과 인사이트를 남김 | README.md, [실험로그.md](%EC%8B%A4%ED%97%98%EB%A1%9C%EA%B7%B8.md) | 새논문적용규칙.md 6절, [보고서작성규칙.md](%EB%B3%B4%EA%B3%A0%EC%84%9C%EC%9E%91%EC%84%B1%EA%B7%9C%EC%B9%99.md) |
| 7. 판정 | 현황표 상태를 갱신하고 `python render.py`로 html과 대시보드를 다시 만듦 | README.html, 루트 docs/index.html | 이 문서의 현황표 |
| 8. 반영 | 유효 판정이 나고 사용자가 지시하면 C++(1_LDPC_revised)에 반영하고 ADR을 씀 | ADR | `0_LDPC_original/docs/adr/` |

- ㉮ 흐름은 1에서 8로 간다. 5에서 실패하면 7에서 실패로 기록하고 끝난다 (폐기 사유는
  README 후속 절)
- ㉯ 대시보드 카드 하나가 아이디어 하나다. 카드의 특징과 실험 결과는 README 요약 절의
  "논문 아이디어"와 "실험 결과" 항목에서 가져오고, 카드를 누르면 그 README로 간다

---

## 역할 경계

- ㉮ 이 폴더는 아이디어 현황표(모든 출처의 아이디어 접수와 상태 추적)와 아이디어별
  실험 폴더를 담는다
- ㉯ py 실험의 본체(src)는 `2_LDPC_base`에 정본 하나만 둔다. 아이디어
  폴더의 run.py가 상위로 올라가며 `2_LDPC_base/src`를 찾아 import하므로
  베이스 수리가 모든 아이디어 실험에 자동 전파된다 (복사 금지, 사본은 베이스
  수리에서 누락되어 비교를 오염시킨다)
- ㉰ 기준선(base_run)은 `2_LDPC_base/workspace/base_run/`다 (재정의 0개가 보증).
  스캔에 무클립 쌍을 포함하면 기준선을 같은 스캔 안에서 얻을 수도 있다
- ㉱ 실험 절차 정본은 [새논문적용규칙.md](%EC%83%88%EB%85%BC%EB%AC%B8%EC%A0%81%EC%9A%A9%EA%B7%9C%EC%B9%99.md),
  보고서 문장과 배치 정본은 [보고서작성규칙.md](%EB%B3%B4%EA%B3%A0%EC%84%9C%EC%9E%91%EC%84%B1%EA%B7%9C%EC%B9%99.md)

---

## 아이디어 현황표

출처 유형: 논문 / 특허 / 제안(사람) / 컨퍼런스 / 기타
상태: 대기 → 실험중 → 성공 / 조건부 유효 / 실패 / 폐기 → 반영됨
(README 머리줄의 판정 낱말과 같다. 실험중 항목은 괄호에 현재 판정을 적는다)

### 전체

| # | 제목 | 출처 | 상태 | 디렉토리 |
|---|------|------|------|---------|
| 1 | CNU min1/min2 이중 상한 클리핑 | 논문 ieee:9496601 (IEEE TCAD 2022) | 실험중 (조건부 유효: ch 대비 edge 상한 여유가 있을 때만 이득. 평가 대상 파라미터로 최종 판정) | [001_minsum_dual_clip/](001_minsum_dual_clip/README.md) |
| 2 | min1/min2 격차 기반 동적 정규화 + 이중 상한 | 논문 ieee:6865103 (IEEE 2014) | 실험중 (조건부 유효: 이득 조건은 001과 동일하고, 그 조건에서 클리핑과 결합 시 전 조합 최량. 격차 임계 T는 edge 레벨 간격으로 튜닝 필수. 평가 대상 파라미터로 최종 판정) | [002_minsum_dynamic_normalization/](002_minsum_dynamic_normalization/README.md) |
| 3 | ULPBF 1 pass (syndrome 갱신 생략, CRC 판정) | 논문 ieee:11449331 (NVMSA 2025) | 실험중 (조건부 유효: 에러 약 16bit 이하 전용 1단, dv별 혼합 문턱 필수, CRC 판정 비열화와 미검출 0 확인. C++ 반영 검토 대기) | [003_ulpbf_1pass/](003_ulpbf_1pass/README.md) |
| 4 | UP-GDBF 전역 탐색 BF (penalty 통합) | 논문 ieee:9902993 (IEEE OJCAS 2022) | 실패 (dv 혼합 H에서 전역 최대 비교가 비호환, 복호 가능 상한이 에러 40bit에 그침. dv 균일 부호 채택 시 재평가) | [004_upgdbf/](004_upgdbf/README.md) |
| 5 | ATBF 비트별 임계 적응과 휴면 | 논문 ieee:5671820 (PIMRC 2010) | 실험중 (조건부 유효: 휴면 절감 5-50%, ES 단축 44%. 전제는 1bit 창 8회 연장과 1bit 단가가 min-sum의 1/4 이하) | [005_atbf_quiescent/](005_atbf_quiescent/README.md) |
| 6 | BF 단계 적응 전환과 잔여 오류 기준 재튜닝 | 논문 ieee:8742682 (IEEE Comm. Letters 2019) | 실패 (적응 전환은 감지 신호 부재, ρ 재튜닝은 인과 경로 없음. 파생: 1bit 창 4에서 8로 고정 연장이 genie 상한 달성, 결정거리로 이관) | [006_bf_stage_switch/](006_bf_stage_switch/README.md) |
| 7 | 열 단위 조기 종료 CB-ET | 논문 ieee:6865738 (IEEE 2014) | 실패 (기존 PCRC 대비 순증 음수, -7.2%에서 -14.0%) | [007_cbet_column_stop/](007_cbet_column_stop/README.md) |

### 반영 완료

| # | 제목 | ADR | 디렉토리 |
|---|------|-----|-------------|
| | | | |

---

## 폴더 규칙

- ㉮ 아이디어마다 폴더 하나를 만들고 상세, 코드, 로그, 결과를 한곳에 둔다
  (폴더 양식은 `_template/`를 복사해 시작)
- ㉯ 실행은 아이디어 폴더에서 `python run.py` (형제 config.json 사용, 인자로
  다른 config 지정 가능). 어느 위치에서 실행해도 동작한다
- ㉰ 파라미터 스캔이 필요한 실험은 scan.py를 두고 config와 값 목록을 인자로
  받게 한다 (예: `001_minsum_dual_clip/scan.py`)
- ㉱ 실험이 끝나면 [실험로그.md](%EC%8B%A4%ED%97%98%EB%A1%9C%EA%B7%B8.md)에 환경(H-matrix, LLR set, edge 양자화,
  seed)과 인사이트를 기록한다
- ㉲ 결과는 각 폴더의 `Sim_Output/`에 실행별로 쌓인다 (git 무시). 입력은 공용
  `2_LDPC_base/Input/`을 쓴다 (config의 `../../2_LDPC_base/Input/...`)
- ㉳ 문서에는 날짜를 적지 않는다 (시점 기록은 git 이력과 `_pm/`이 담당하고,
  실험 시점 기록이 필요하면 [실험로그.md](%EC%8B%A4%ED%97%98%EB%A1%9C%EA%B7%B8.md)에 둔다)
- ㉴ 문서는 md가 정본이고, md를 고치면 `python render.py`로 형제 html과 대시보드
  루트 [docs/index.html](../docs/index.html)을 다시 만들어 함께 커밋한다 (html은 열람용. README 작성
  규칙은 [새논문적용규칙.md](%EC%83%88%EB%85%BC%EB%AC%B8%EC%A0%81%EC%9A%A9%EA%B7%9C%EC%B9%99.md) 6절과
  [보고서작성규칙.md](%EB%B3%B4%EA%B3%A0%EC%84%9C%EC%9E%91%EC%84%B1%EA%B7%9C%EC%B9%99.md)).
  render.py는 만든 html의 상대 링크가 가리키는 파일이 있는지 검사해 깨진 링크를 보고한다
