# Review Context (Round 2: 분석, lv2 4팀)

> 작성: 2026-09-21 15:02:00

## 리뷰 목적

DAO(Decoder Auto Optimizer, LLR matrix 자동 최적화기)의 파이썬 소스를 두 축으로 분석한다. 코드 변경분이 아니라 **코드 전체**가 대상이다.

- ㉮ **가독성**: 사람이 읽기 쉽게 만들려면 무엇을 어떻게 고쳐야 하는지. 결과물은 "개선 처방"이다 (무엇을, 어떤 순서로, 어떤 위험을 안고 고치는지)
- ㉯ **문제점**: 동작에 영향을 주는 결함이나 위험. 결과물은 "발견 + 심각도 + 수정 처방"이다

사용자가 원하는 것은 "어떻게 수정하면 되는지"이므로, 모든 발견과 개선안에 **처방(수정 방안)**을 붙인다. 처방은 구체적으로(어느 함수를 어디로, 어떤 이름으로, 어떤 순서로) 쓴다.

## 리뷰 대상

| 우선순위 | 파일 | 줄 수 | 내용 |
|---------|------|------|------|
| 주 | `5_DAO/SRC/DAO_Main.py` | 10,428 | 최적화 엔진 `LLR_OPT` 클래스(메서드 약 200개), 모듈 함수, 상태 dataclass 4개 |
| 주 | `5_DAO/SRC/DAO_LLR_MATRIX.py` | 645 | 데이터 모델 `LLR_MATRIX`, `LLR_Header`, `LLR_Row`, 파일 입출력, 유효성 검사 |
| 주 | `5_DAO/SRC/DAO_Config.py` | 457 | 설정 클래스 20여 개, `Set_Configs_Manually`(argv), `PATH_CONFIG` |
| 주 | `5_DAO/SRC/DAO_Constants.py` | 196 | 열거형, 디렉토리와 파일 이름 상수, 모듈 레벨 MPI comm/rank, `MULTI_ROUND_*` 표 |
| 부 | `5_DAO/Util/*.py`, `5_DAO/Util/fer_plot/fer_plot.py` | 1,278 | 보조 스크립트 8개 |

참조 문서: `5_DAO/README.md`(사용 설명서), `5_DAO/DAO_spec.md`(매트릭스 구조, 유효성 규칙 H1~HBF2, GenLLRMode 17개 스펙, 7장 새 모드 추가 체크리스트).

**줄 번호 주의**: Round 1 문서의 줄 번호는 일부가 커밋 6e035e6 이전 파일(10,424줄) 기준이라 2089줄 이후는 최대 4줄 어긋날 수 있다. 함수 이름으로 다시 찾아 현재 파일 기준 줄 번호를 적는다. 다른 세션이 DAO를 수정하며 커밋하므로 리뷰 도중 파일이 또 바뀔 수 있다. `git log --oneline -3 -- 5_DAO/SRC`로 시작 시점 커밋을 워커 문서 머리에 적는다.

## 배정된 관점

Round 1 통합 관점 30개의 정의와 확인 항목은 [r1 report.md](../r1_round1_lv1_perspectives/report.md)에 있고, 상세 확인 항목은 [agent_A.md](../r1_round1_lv1_perspectives/agent_A.md), [agent_B.md](../r1_round1_lv1_perspectives/agent_B.md), [agent_C.md](../r1_round1_lv1_perspectives/agent_C.md)의 해당 행(출처 열)에 있다. 팀 리더는 자기 팀 관점의 상세 행을 읽고 워커에 나눈다.

| 팀 | 이름 | 배정 관점 | 핵심 질문 |
|----|------|----------|----------|
| R | 가독성 | R1~R11 | `LLR_OPT` 10,000줄을 사람이 읽을 수 있는 구조로 바꾸려면 무엇을 어떤 순서로 고쳐야 하는가. 옆 세션의 SW 분기 확장(매트릭스 모델 필드 추가)을 쉽게 하는 방향인가 |
| M | MPI 통신과 프로세스 수명 | P1, P2, P3, P5, P13, P14, P15, P16 | rank 사이 집단 통신이 어긋나 hang이 나거나, 종료와 예외 경로에서 프로세스가 매달리거나 진단 정보를 잃는 자리가 있는가 |
| L | 매트릭스 모델, 생성 모드, 설정 | P10, P11, P12, P17, P18 | 유효성 규칙과 spec이 어긋나거나, 구조 변경 모드 뒤 헤더와 인덱스가 깨지거나, 설정 조합이 검증을 통과한 뒤 실행 중 터지는 자리가 있는가 |
| T | 테스트 파이프라인과 결과 집계 | P4, P6, P7, P8, P9, P19 | FER 측정 결과가 잘못 집계되거나, Two-stage와 temp_optimal 승격이 틀린 매트릭스를 최적으로 남기거나, uncor 파일 처리가 어긋나는 자리가 있는가 |

Round 1의 "실마리" 절(r1 report.md 끝)은 검증 전 관찰이다. 관련 팀이 확인하되, 실마리에 없는 것을 더 넓게 찾는다.

| 실마리 | 담당 팀 |
|--------|--------|
| ㉮ README 이름과 링크 | R |
| ㉯ HBF 시퀀스 값, `GenLLRModeHBF` 미사용 | L |
| ㉰ CSW 같은 값 금지 대 spec C5 | L |
| ㉱ Reduce/allgather 타임아웃 미적용 | M |
| ㉲ 타임아웃 값 1200초 대 3600초 | M |
| ㉳ `TEST_MODE_DIR_NAME` FULL 누락 | T |
| ㉴ `Copy_Uncors` `test_mode` 미사용 | T |
| ㉵ `current_target_idx` 생성 순서 | L (R5와 겹치면 R도) |
| ㉶ `Set_CSW_Update_Limit` 미호출, `CSW_UPDATE_LIMIT_VALUE` 미정의 | L |
| ㉷ `CONFIGS` 누락, `HBF_OPT_CONFIG` 부수효과 | L (R4와 겹치면 R도) |
| ㉸ `ReorderState` docstring 필드 불일치 | R |
| ㉹ docstring과 실제 동작 불일치 | R |
| ㉺ 줄표, 이모지, U+FFFD | R |
| ㉻ Util 하드코딩 | R(사용법), T(위험) |

## 기술 맥락

- MPI(mpi4py): rank 0이 root(LLR 생성, 최적 판정), 나머지가 worker. 모든 rank가 외부 C++ ECC 실행 파일(Ref_C)을 각자 subprocess로 돌려 FER를 측정하고 `_safe_gather`/`Reduce`로 모은다. `comm`, `rank`, `num_process`는 `DAO_Constants.py` 모듈 레벨 전역이다
- root 판단 뒤 `_safe_bcast`로 모든 rank에 값을 맞추는 관용구가 여러 곳에 반복된다. 집단 통신(bcast, gather, barrier)은 모든 rank가 같은 횟수로 불러야 하며, 한 rank만 다른 경로로 빠지면 hang이 난다
- `_mpi_comm_with_timeout`은 스레드로 통신을 감싸 타임아웃을 잰다
- Two-stage 테스트: Partial(적은 uncor로 빠른 선별) 뒤 Full(정확 평가). uncor는 uncorrectable frame(복호 실패 프레임)이며 파일로 세션 디렉토리에 복사, 분배, 병합된다
- 멀티라운드 모드 4개(REORDER_GROUP, ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP)는 dataclass 상태(`ReorderState` 등)를 `MULTI_ROUND_MODES` 표로 찾아 root가 갱신하고 bcast한다
- 종료 신호는 파일(`8_End_flag/*.txt`)로 주고받는다. 사용자가 파일을 만들면 root가 읽고 bcast한다
- 용어: FER(Frame Error Rate), LLR(Log Likelihood Ratio), CSW(Column Selection Weight 문턱), DV(Degree Variable), HBF(Hybrid Bit Flipping), Ref_C(외부 C++ ECC 실행 파일)
- 이 환경에서 C++ 빌드와 MPI 실행은 하지 않는다. 코드를 읽어 판단한다. Python 3.11, numpy, mpi4py는 설치되어 있어 문법 검사나 작은 단위 실행(`python -c`, `py_compile`)은 가능하다
- 프로젝트 문장 규칙(줄표와 가운뎃점 금지, 긍정문, 이름은 목적 우선, 수리는 다시 쓰기)과 파일 참조 규칙(markdown link)은 루트 `CLAUDE.md`를 따른다. 워커와 리더의 문서도 이 규칙을 지킨다

## 심각도 기준

| 심각도 | 정의 |
|--------|------|
| CRITICAL | 프로세스 중단이나 hang, 또는 데이터 비가역 손상 |
| HIGH | 틀린 결과를 내지만 프로세스는 계속됨 |
| MEDIUM | 엣지케이스 위험, 누락 커버리지 |
| LOW | 개선 제안 |

가독성 팀(R)의 개선안은 심각도 대신 **우선순위(상/중/하)**와 **위험(동작 변경 여부, 옆 세션 작업과의 충돌 가능성)**을 붙인다.
