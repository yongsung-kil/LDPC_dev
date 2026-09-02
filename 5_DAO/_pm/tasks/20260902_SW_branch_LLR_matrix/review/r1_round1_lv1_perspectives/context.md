# Review Context (Round 1: 관점 도출)

## 리뷰 대상

두 문서 (코드가 아니라 "코드 수정 계획" 문서다. 실제 C++ 소스는 아직 수정되지 않았다):

- `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/20260902_SW_branch_LLR_matrix.md` (무엇을 왜 고치는지, `__AUTO_LLR_OPT__` 86곳 분류, 미결정 사항)
- `5_DAO/_pm/tasks/20260902_SW_branch_LLR_matrix/code_diff.md` (9장에 걸친 수정 전후 코드)

문서가 가리키는 실제 소스: `0_LDPC_original/src/` (decoder.cpp 8115행, local_opt.cpp, common.h, decoder.h, ecc_data.h, corner.h, ecc_top.cpp, main.cpp)

새 형태의 입력 파일 예시: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`

## 변경 목적

LLR matrix 파일이 iteration 구간 안에서 Syndrome Weight(SW, 신드롬 무게)에 따라 여러 분기를 갖는 형태로 바뀌었다.
`0_LDPC_original` C++ 디코더가 이 형태를 읽고 복호에 반영하도록 고칠 곳을 문서로 정리했다.
사용자는 이 문서를 보고 외부 환경에서 직접 코드를 고친다. 이 저장소에서는 C++ 빌드를 하지 않는다.

배경: DAO(Decoder Auto Optimizer)를 error floor 대응이 아니라 throughput 최적화(HD decoding iteration 1~4 안에 복호가 끝나는 비율 높이기)에 쓰려는 방향. 근거 메모는 저장소 루트 `msg1.md`.

## 문서 작성자가 내린 핵심 판단 (리뷰 요청 사항)

- ㉮ 새 표기 `{x}{y}`가 들어간 헤더 줄은 빈 칸이 아니라 `PARAM_LLR::type_each_group`이며, 기존 값(`GROUP_TYPE_ITER`=0, `GROUP_TYPE_CSW`=1)과 충돌한다. `20`, `21`을 넣으면 `decoder.cpp:7051-7068`의 두 갈래 어디에도 안 걸려 `table_row_idx`가 0으로 남아 항상 첫 row를 쓴다
- ㉯ 분기 정보를 별도 줄(`sw_branch_idx_each_group`)로 빼는 안을 추천
- ㉰ code_diff.md의 수정 후 코드는 세 전제 위에서 작성: 별도 줄 추가, 분기 없음은 -1, SW 문턱은 배열화하되 값은 기존 상수에서 가져오기
- ㉱ 구간(span) 개념 도입: `sw_span_idx_each_group`을 파서가 계산(분기 index가 0으로 되돌아갈 때 다음 구간), `Decoder::cur_sw_branch_idx[MAX_SW_SPAN]`이 기존 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`을 대신

## 작성자가 특히 확인을 요청한 곳

- 1. 파일 해석이 맞는지 (`LLR_MATRIX_1.txt`와 상위 문서 2장 표 대조)
- 2. code_diff.md 6장의 그룹 선택 로직: 뒤에서 앞으로 훑는 루프에 분기 필터를 넣었는데, 분기 개수나 구간 배치가 달라져도 결과가 순서에 좌우되지 않는지
- 3. code_diff.md 3.2장의 구간 번호 계산: `prev_branch != 0` 조건으로 같은 분기 안의 그룹 쪼개짐과 새 구간 시작을 구분하는데 반례가 있는지
- 4. code_diff.md 5장의 `Select_BF`: BF 진입 시 iteration 1~4 구간 분기를 `syn_weight`로 고르게 했는데, 기존 코드는 `FLAG_HD_1_4_SET_TYPE_0`으로 못박혀 있었다. 타당한지
- 5. `ITER_MAX_HBF`를 4로 통일할 때 딸려오는 12곳(상위 문서 5.5장 표)에 빠진 곳이 있는지
- 6. `__AUTO_LLR_OPT__` 86곳 분류에서 "손대지 않아도 되는 곳"으로 넘긴 것 중 실제로는 고쳐야 하는 것이 있는지
- 7. (작성자가 확인 못 함) `local_opt.cpp:38-44`가 MPI로 `LLR_MATRIX`와 `CSW_thr`만 뿌리고 나머지 헤더는 각 rank가 자기가 읽은 값을 쓴다. 각 rank가 파일을 따로 읽는 구조인지

## 기술 맥락

- C++ LDPC 디코더. `__AUTO_LLR_OPT__` 전처리기 스위치가 켜지면 LLR 파라미터를 파일(`LOCAL_OPT::Read_LLR_info_Auto`)에서 읽어 `Decoder::Get_Cur_LLR_Idx_FILE`로 매 iteration의 row를 고른다
- BF(Bit Flipping) 모드: HD(Hard Decision) 복호 초기 iteration 1~4에서 1bit precision으로 도는 모드. `Select_BF`가 SW 문턱으로 진입을 정한다
- `ITER_MAX_HBF`: BF 모드의 최대 iteration 수. 현재 `__AUTO_LLR_OPT__`에서 0, 아니면 4
- 변경 금지 대상: TV 출력 hex 포맷, HCU 버퍼 레이아웃, Partial CRC 다항식, H-matrix 파일 포맷 (상세: `0_LDPC_original/CLAUDE.md`)
- 프로젝트 문장 규칙과 파일 참조 규칙은 루트 `CLAUDE.md`를 따른다
