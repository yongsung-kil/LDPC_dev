# Review Context (Round 1: 관점 도출)

## 리뷰 대상

DAO(Decoder Auto Optimizer, LLR matrix 자동 최적화기)의 파이썬 소스. 코드 변경분이 아니라 **코드 전체**가 대상이다.

| 우선순위 | 파일 | 줄 수 | 내용 |
|---------|------|------|------|
| 주 | `5_DAO/SRC/DAO_Main.py` | 10,428 | 최적화 엔진 `LLR_OPT` 클래스(메서드 약 200개), 모듈 함수 몇 개, 상태 dataclass 4개 |
| 주 | `5_DAO/SRC/DAO_LLR_MATRIX.py` | 645 | 데이터 모델 `LLR_MATRIX`, `LLR_Header`, `LLR_Row`, 파일 입출력, 유효성 검사 |
| 주 | `5_DAO/SRC/DAO_Config.py` | 457 | 설정 클래스 20여 개(클래스 속성), `Set_Configs_Manually`(argv로 설정 덮어쓰기), `PATH_CONFIG` |
| 주 | `5_DAO/SRC/DAO_Constants.py` | 196 | 열거형(GenLLRMode 등), 디렉토리와 파일 이름 상수, 모듈 레벨 MPI comm/rank |
| 부 | `5_DAO/Util/*.py`, `5_DAO/Util/fer_plot/fer_plot.py` | 1,278 | 보조 스크립트 8개 |

참조 문서: `5_DAO/README.md`(사용 설명서, 아키텍처 절 포함), `5_DAO/DAO_spec.md`(매트릭스 구조, 유효성 규칙 H1~C5, GenLLRMode 17개 스펙).
루트 `CLAUDE.md`와 `5_DAO/README.md` 상단 반입 내역도 먼저 읽는다.

## 리뷰 목적 (두 축)

- ㉮ **가독성**: 사람이 읽기 쉽게 만들려면 무엇을 어떻게 고쳐야 하는지. 구조(파일 분할, 클래스 분리), 이름, 흐름, 중복, 주석과 문서의 정합 등
- ㉯ **문제점**: 동작에 영향을 주는 결함이나 위험(버그, 엣지케이스, 동기화 오류, 자원 누수, 예외 처리 누락)이 있으면 어떻게 고쳐야 하는지

두 축 모두 관점을 도출한다. 이번 라운드는 "어디를 봐야 하는지"를 정하는 라운드이며 문제를 찾는 라운드가 아니다.

## 배경

- ㉮ `SRC/`는 반입 시점 원형(`5_DAO/reference/SRC/`)에 커밋 6e035e6 하나만 얹힌 상태다 (`Gather_And_Archive_Uncors`가 최적 매트릭스 대신 테스트한 매트릭스를 받도록 인자 추가). 다른 세션이 이 저장소에서 DAO를 수정하며 커밋하므로, 리뷰 중 파일이 바뀔 수 있다. 줄 번호는 항상 현재 파일 기준으로 다시 확인한다
- ㉯ 다른 세션에서 SW 분기 LLR matrix 지원 작업이 진행 중이다 (`5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/`).
  그 작업은 DAO 매트릭스 모델(`LLR_Header`, `LLR_Row`)과 유효성 규칙 확장을 예고한다.
  가독성 개선안은 그 확장을 쉽게 하는 방향이어야 한다
- ㉰ 이 환경에서 C++ 빌드는 하지 않는다. DAO는 외부 C++ ECC 실행 파일(Ref_C)을 subprocess로 돌려 FER를 읽는다

## 메인이 먼저 관찰한 구조 (관점 도출의 출발점, 결론 아님)

- ㉮ `DAO_Main.py`의 `LLR_OPT` 클래스 하나가 MPI 통신, 파일 입출력, 세션 디렉토리 관리, ECC 빌드와 실행, LLR 생성 모드 17개, 테스트, 최적 갱신, 로그, 속도 테스트, uncor 풀 관리, 단일 row 생성 모드를 모두 담는다
- ㉯ `from DAO_Config import *`, `from DAO_Constants import *`로 이름을 들여온다. `comm`, `rank`는 `DAO_Constants.py` 모듈 레벨에서 만들어져 전역으로 쓰인다
- ㉰ 메서드 이름이 `Gen_LLR_Insert_Random_Group`(대문자 시작 스네이크), `_safe_bcast`(소문자), `BACKUP_SRC`(전부 대문자)로 섞여 있다
- ㉱ 설정은 클래스 속성(`DAO_CONFIG.MAX_OPTIMIZATION_STAGE`)이고, `Set_Configs_Manually`가 argv의 SIM_IDX(10, 11, 12, 20, ...)로 여러 설정을 덮어쓴다. `Update_Configs`가 파생 설정을 다시 계산한다
- ㉲ 멀티라운드 모드(REORDER_GROUP, ADJUST_ITERATION, DELETE_ROW, INSERT_RESTART_GROUP)는 `MULTI_ROUND_MODES` 딕셔너리와 `getattr(self, name)`으로 상태와 갱신 함수를 찾는다
- ㉳ `Run_Optimization`의 trial 루프 안에서 root가 판단하고 `_safe_bcast`로 모든 rank에 동기화하는 패턴이 여러 번 반복된다
- ㉴ 종료 신호는 파일(`8_End_flag/*.txt`)로 주고받는다
- ㉵ 주석과 로그 문구는 한국어와 영어가 섞여 있고, 일부 docstring은 Args/Returns 형식이다

## 기술 맥락

- MPI(mpi4py): rank 0이 master(LLR 생성, 최적 판정), 나머지가 worker. 모든 rank가 ECC exe를 각자 실행해 FER를 측정하고 gather한다
- Two-stage 테스트: Partial(적은 uncor로 빠른 선별) 뒤 Full(정확 평가). uncor = uncorrectable frame(복호 실패 프레임)
- 용어: FER(Frame Error Rate), LLR(Log Likelihood Ratio), CSW(Column Selection Weight 문턱), DV(Degree Variable), HBF(Hybrid Bit Flipping), Ref_C(외부 C++ ECC 실행 파일)
- 프로젝트 문장 규칙(줄표와 가운뎃점 금지, 긍정문, 이름은 목적 우선)과 파일 참조 규칙(markdown link)은 루트 `CLAUDE.md`를 따른다
