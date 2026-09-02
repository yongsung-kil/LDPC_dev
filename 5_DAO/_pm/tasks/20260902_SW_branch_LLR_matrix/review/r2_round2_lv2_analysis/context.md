# Review Context (Round 2: 분석, lv2)

## 변경 목적

LLR matrix 파일이 iteration 구간 안에서 Syndrome Weight(SW, 신드롬 무게)에 따라 여러 분기를 갖는 형태로 바뀌었다. `0_LDPC_original` C++ 디코더가 이 형태를 읽고 복호에 반영하도록 고칠 곳을 두 문서로 정리했다. 사용자는 이 문서를 보고 외부 환경에서 직접 코드를 고친다. 이 저장소에서는 C++ 빌드를 하지 않는다.

배경: DAO(Decoder Auto Optimizer)를 error floor 대응이 아니라 throughput 최적화(HD decoding iteration 1~4 안에 복호가 끝나는 비율 높이기)에 쓰려는 방향. 근거 메모는 저장소 루트 `msg1.md`.

## 변경 범위

리뷰 대상은 코드가 아니라 "코드 수정 계획" 문서 두 개다. 실제 C++ 소스는 아직 수정되지 않았다.

- `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/20260902_SW_branch_LLR_matrix.md` (이하 "상위 문서". 새 파일 형태 해석, 무엇을 왜 고치는지, `__AUTO_LLR_OPT__` 86곳 분류, 미결정 사항)
- `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/code_diff.md` (9장에 걸친 수정 전후 코드. 장 앵커는 `#ch3` 형태)

문서가 가리키는 실제 소스: `0_LDPC_original/src/` (decoder.cpp 8115행, local_opt.cpp 184행, common.h, decoder.h, ecc_data.h, corner.h, corner.cpp, ecc_top.cpp, ecc_top.h, main.cpp, mode.h, mpi.h, mpi.cpp, TV_Dec_Inter.cpp)

새 형태의 입력 파일 예시: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`
구 형태의 입력 파일 예시: `5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt`

Round 1 관점 전체와 팀 배정: `../r1_round1_lv1_perspectives/report.md`

## 문서 작성자가 내린 핵심 판단 (리뷰 대상)

- ㉮ 새 표기 `{x}{y}`가 들어간 헤더 줄은 `PARAM_LLR::type_each_group` 자리이며 기존 값(`GROUP_TYPE_ITER`=0, `GROUP_TYPE_CSW`=1)과 충돌한다. `20`, `21`을 넣으면 `decoder.cpp:7051-7068`의 두 갈래 어디에도 안 걸려 `table_row_idx`가 0으로 남아 항상 첫 row를 쓴다
- ㉯ 분기 정보를 별도 줄(`sw_branch_idx_each_group`)로 빼는 안을 추천
- ㉰ code_diff.md의 수정 후 코드는 세 전제 위에서 작성: 별도 줄 추가, 분기 없음은 -1, SW 문턱은 배열화하되 값은 기존 상수에서 가져오기
- ㉱ 구간(span) 개념 도입: `sw_span_idx_each_group`을 파서가 계산(분기 index가 0으로 되돌아갈 때 다음 구간), `Decoder::cur_sw_branch_idx[MAX_SW_SPAN]`이 기존 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 대신
- ㉲ `ITER_MAX_HBF`를 AUTO 빌드에서도 4로 통일해 BF(Bit Flipping) 모드를 AUTO 경로에서 살린다

## 배정된 관점

각 팀은 아래 표에서 자기 팀 행만 맡는다. 관점 번호와 확인 항목의 원문은 `../r1_round1_lv1_perspectives/report.md`의 표를 본다.

| 팀 | 팀명 | 배정 관점 | 핵심 질문 |
|----|------|----------|----------|
| P | 파일 형식과 파서 | 1 파일 해석 정합, 3 구간 번호 계산의 반례, 10 파서 견고성과 구 포맷 호환, 11 MPI rank별 파일 읽기 구조, 16 DAO 쪽 도구 영향 | 새 파일을 문서대로 읽으면 헤더와 row가 의도한 구조로 들어오는가. 파서의 오류 처리와 구 파일, MPI, DAO 도구까지 파급이 닫혀 있는가 |
| D | 디코더 분기 로직 | 4 그룹 선택의 순서 독립성, 5 `Select_BF`와 문턱 배열, 9 제거되거나 개명되는 멤버의 참조 전수와 새 배열 초기화, 13 프레임 상태 초기화와 restart, edge clear 상호작용 | 프레임 시작에서 정한 분기가 매 iteration의 row 선택까지 순서에 좌우되지 않고 일관되게 흐르는가. 지우는 멤버와 새 배열의 초기화가 빠짐없는가 |
| I | iteration 번호 체계와 빌드 갈래 | 2 배경 메모와 설계 방향 정합, 6 `ITER_MAX_HBF` 딸린 곳 전수, 7 MN 배열과 iteration 번호 체계, 8 비AUTO 빌드 안전성과 컴파일 스위치 조합, 12 `__AUTO_LLR_OPT__` 분류 재검토 | `ITER_MAX_HBF`를 4로 되돌리고 AUTO 갈래를 한 갈래로 합칠 때 배경 메모의 설계 의도와 맞는가, 딸린 곳과 비AUTO 빌드가 빠짐없이 다루어졌는가 |
| C | 문서 정합과 규칙 | 14 두 문서 상호 정합과 소스 인용 정확성, 15 적용 순서(9장)의 단계별 성립, 17 문서 작성 규칙과 변경 등급 | 두 문서가 같은 결정을 말하는가, 인용이 소스와 맞는가, 적용 순서가 단계별로 성립하는가, 작성 규칙과 변경 등급을 지켰는가 |

## 기술 맥락

- C++ LDPC 디코더. `__AUTO_LLR_OPT__` 전처리기 스위치가 켜지면 LLR 파라미터를 파일(`LOCAL_OPT::Read_LLR_info_Auto`, `local_opt.cpp:52-132`)에서 읽어 `Decoder::Get_Cur_LLR_Idx_FILE(iter)`(`decoder.cpp:6973-7073`)로 매 iteration의 row를 고른다. 호출은 `decoder.cpp:1136-1142`(`mn > 0`일 때)
- BF(Bit Flipping) 모드: HD(Hard Decision) 복호 초기 iteration 1~4에서 1bit precision으로 도는 모드. `Select_BF`(`decoder.cpp:2082-2130`, 호출 `1966-1970`, `mn == 0` 루프 끝)가 SW 문턱으로 진입을 정한다. 미진입이면 `mn`과 `MN`에 `ITER_MAX_HBF`를 더해 iteration 5부터 돈다
- `ITER_MAX_HBF`(`common.h:403-407`): BF 모드의 최대 iteration 수. 현재 `__AUTO_LLR_OPT__`에서 0, 아니면 4
- SW 문턱 상수는 `common.h:200-252`. `__12META__` 갈래(200-227)와 그렇지 않은 갈래(230-251)가 있고, 후자에만 `SW_TH_BF0_512B_TLC_OFF`(680), `SW_TH_BF1_512B_TLC_OFF`(130), `SW_TH_5_8_SET0_512B_TLC_OFF`(1100), `SW_TH_5_8_SET1_512B_TLC_OFF`(950), `SW_TH_BF_DEFAULT`(630), `SW_TH_5_8_SET0_DEFAULT`(960), `SW_TH_5_8_SET1_DEFAULT`(950)가 있다
- `GROUP_TYPE_ITER`=0, `GROUP_TYPE_CSW`=1은 `common.h:756-757`. `FLAG_HD_1_4_SET_TYPE_*`, `FLAG_HD_5_8_SET_TYPE_*` enum은 `common.h:717-725`
- 파서는 `fscanf("%d")` 토큰 기반이라 빈 줄과 탭을 무시한다. DAO의 Python 파서(`5_DAO/SRC/DAO_LLR_MATRIX.py:476-537`)는 줄 index 기반이다
- `msg1.md`(루트)의 배경 서술: "BF decoding (0<=SW<SW_TH_BF), normal decoding0/1/2 ... 구간 개수는 바뀔 수 있어", "bf를 타면 iteration 0,1,2,3,4,5,6,7.. 안 타면 0,5,6,7..", "bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리하는거야", "bf 구간은 늘어나지않아. 딱 1~4야", "dao는 bf가 없다고 가정하고 normal decoding이 0,1,2,3,4..", 예시 iter start/end/flag = 1/4/-1, 5/8/0, 5/8/1, 5/8/2, "분기가 없으면 -1 분기가 2개 이상이면 각각 idx가 0.1.2.."
- 변경 금지 대상: TV 출력 hex 포맷, HCU 버퍼 레이아웃, Partial CRC 다항식, H-matrix 파일 포맷 (상세: `0_LDPC_original/CLAUDE.md`)
- 프로젝트 문장 규칙과 파일 참조 규칙은 루트 `CLAUDE.md`를 따른다. 특히 줄표(U+2014)와 가운뎃점(U+00B7) 금지, 나열은 ㉮㉯㉰, 입력 파일의 성격(출처) 서술 금지

## 보고 규칙 (모든 팀 공통)

- 문서를 수정하지 않는다. 발견만 기록한다
- 발견마다 심각도(CRITICAL, HIGH, MEDIUM, LOW)를 붙이고 근거를 `파일:줄`로 적는다. 문서 안의 위치는 `code_diff.md 6.1` 또는 `상위 문서 5.4-2`처럼 장 번호로 적는다
- 심각도 기준: CRITICAL은 프로세스 중단이나 hang, 데이터 비가역 손상. HIGH는 틀린 결과를 내지만 프로세스는 계속됨. MEDIUM은 엣지케이스 위험이나 누락 커버리지. LOW는 개선 제안
- 문서에 대한 리뷰이므로 "수정 후 코드를 그대로 적용하면 생기는 결함"과 "문서 서술 자체의 오류(인용 불일치, 상충, 누락)"를 구분해 적는다
- 발견에 처방(어떻게 고쳐야 하는지)을 붙일 때는 처방이 코드 삭제나 동작 변경을 요구하는지 표시한다
- 작성자가 요청한 7건(관점 1, 3, 4, 5, 6, 11, 12)은 "문제 없음"이라도 판정과 확인 범위를 반드시 적는다
