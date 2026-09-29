# Review Context (HBF 관련 부분 라이트 리뷰)

> 작성: 2026-09-29 13:39:32
> 리뷰 종류: 라이트 리뷰 (Round 1 관점 도출, Round 2 분석에서 종료)
> 저장소 루트: `D:/OneDrive/My_Projects/LDPC_dev`. 아래 경로는 모두 저장소 루트 기준이다.

## 변경 목적

DAO(Decoder Auto Optimizer)의 HBF(Hybrid Bit Flipping) 최적화 모드(`DAO_CONFIG.IS_HBF_OPT`)를 iteration 5 이상의 그룹이 들어 있는 매트릭스에서도 돌 수 있게 고쳤다. HBF는 HD(Hard Decision) 복호의 iteration 1~4를 뜻한다.

- ㉮ dv_idx 0의 TH를 상수 0으로 고정하는 규칙을 HBF 구간(iteration 1 ~ `HBF_MAX_ITERATION`)의 row로 한정했다. 판단은 `LLR_MATRIX.Is_Row_In_HBF_Iterations` 한 곳이 맡는다
- ㉯ 매트릭스의 max_iteration이 4 이하여야 한다는 검사를 없애고, row가 HBF 구간의 경계(iteration 4와 5 사이)를 걸치는지 보는 검사(HBF2)를 넣었다
- ㉰ `Set_Seed_Mode`의 HBF 전용 갈래와 `HBF_OPT_CONFIG.HBF_OPT_USING_UNCOR`를 없애 HBF 최적화 모드도 보통 모드와 같은 규칙으로 seed 모드를 정한다
- ㉱ 타겟 그룹을 직접 고르는 `DAO_CONFIG.FIXED_TARGET_GROUP_IDX_LIST`를 넣었다 (HBF 최적화 모드에서 iteration 1~4의 그룹만 바꾸는 실행에 쓴다)
- ㉲ 타겟과 변이의 단위를 그룹 하나로 되돌리고, 여러 분기로 갈라진 구간에서 마지막 분기만 갱신하던 규칙을 없앴다

## 사용자가 확인한 요구

- 1. HBF 최적화 모드는 iteration 1~4에서만 dv_idx 0의 TH가 0이면 된다. iteration 5 이상은 TH가 0일 필요가 없다
- 2. row는 `ch(dv0) th(dv0) ch(dv1) th(dv1) ...` 순서이고 TH 0 대상은 첫 DV(dv_idx 0)다
- 3. 입력과 결과 모두 row가 iteration 경계를 걸치지 않는다. 구간은 1~4, 5~8, 9 이후이고 구간 안은 1, 2~3, 4처럼 나눌 수 있다
- 4. 앞부분(iteration 1~8)과 뒷부분(iteration 9 이후)은 따로 최적화한다
- 5. 타겟 목록에 넣는 값은 그룹 하나하나의 순서(index)다. SW(Syndrome Weight) 분기 그룹도 하나씩 다룬다
- 6. 지정한 그룹은 분기 index와 상관없이 바뀌어야 한다

## 리뷰 범위 (HBF 관련 부분)

- diff 명령: `git diff dff3dba..2e34036 -- 5_DAO/SRC 5_DAO/DAO_spec.md 5_DAO/README.md`
- 관련 plan(태스크 문서): `5_DAO/_pm/tasks/20260928_HBF_TH_iteration_range/20260928_HBF_TH_iteration_range.md`
- 커밋: 96727a2 (TH 고정 범위), 0f6022f (타겟 목록과 HBF2), b107504 (seed 모드), 64a07a9 (그룹 단위), 2e34036 (마지막 분기 규칙 제거)

HBF 최적화 모드가 지나는 코드 자리 (현재 소스 기준)

| 파일 | 자리 |
|------|------|
| `5_DAO/SRC/DAO_LLR_MATRIX.py` | `__init__`의 `is_HBF_OPT`와 `HBF_max_iteration`(36~50), `Is_Row_In_HBF_Iterations`(98), `Is_LLR_Valid`의 HBF2(491)와 HBF1(525), `Read_Input_LLR_Matrix`의 `HBF_immutable_col_range`(710), `Correct_LLR_Matrix`(753), `Correct_Ch_Th_In_Row`(789~831) |
| `5_DAO/SRC/DAO_Main.py` | `Update_RefC_Configs`의 `IS_HBF_OPT` 내리기(451), `Load_Initial_LLR_Matrix`(2605), `_generate_random_row`(767 부근), `Gen_LLR_Regen_DV`(4030), `Gen_LLR_Regen_Row`(4167), `_Load_External_Single_Row_Candidates`(4339), `Generate_Random_Mutation`(7104), `Get_Mode_Sequence_Str`(7196), `Run_Optimization`의 시퀀스 길이(8182), `Build_Target_Group_Indices`, `Check_Fixed_Target_Group_Idx_List`(8360), `Set_Gen_Trial_LLR_Mode`(8442), `Set_Seed_Mode`, `Validate_Config`(9808, 9971) |
| `5_DAO/SRC/DAO_Config.py` | `IS_HBF_OPT`(127), `Gen_LLR_Mode_HBF_SEQUENCE`(134), `FIXED_TARGET_GROUP_IDX_LIST`, `HBF_OPT_CONFIG`(368~375) |
| `5_DAO/SRC/DAO_Constants.py` | `GenLLRModeHBF`(43), `FIXED_TARGET_GROUP_ALLOWED_MODES`, `SW_BRANCH_ALLOWED_MODES` |
| `5_DAO/DAO_spec.md` | 3.6절(HBF 규칙), 3.7절(SW 분기), 3.8절(타겟 그룹 목록), 5.2절 특수 로직, 6.3절 |
| `5_DAO/README.md` | 타겟 그룹 설정, 3.4절, 4.1.1절 |

## 기술 맥락

- ㉮ DAO는 MPI로 도는 Python 프로그램이다. 이 환경에서는 MPI 실행을 하지 않는다. 검사는 `LLR_OPT.__new__`로 MPI 초기화를 건너뛴 단일 프로세스 실행으로 한다
- ㉯ C++ 빌드와 실행은 이 환경에서 하지 않는다. 디코더 근거는 소스를 읽어 확인한다. `0_LDPC_original/src/decoder.cpp` 4058행 부근: BF가 켜져 있고 `iter <= ITER_MAX_HBF`(4)이며 DV가 가장 높은 등급이면 1 bit 정밀도로 처리해 TH를 읽지 않는다
- ㉰ `5_DAO/reference/`는 반입 시점의 원형이다 (참조 전용, 수정 금지). 고치기 전 동작을 확인할 때 쓴다
- ㉱ `HBF_OPT_CONFIG.__init__`은 부르는 자리가 없다. `IS_HBF_OPT`는 설정 값과 `Update_RefC_Configs`의 내리기(`init_n != 1`이면 False)로만 정해진다
- ㉲ 입력 매트릭스 예: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`, `LLR_MATRIX_2.txt` (그룹 11~12개, max_iteration 124, iteration 1~8이 SW 분기 그룹)

## 있는 검사 (단일 프로세스)

| 검사 | 건수 |
|------|------|
| `_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py` | 11 |
| `_test/20260928_fixed_target_group_idx_list/test_fixed_target_group_idx_list.py` | 22 |
| `_test/20260928_hbf_seed_mode/test_hbf_seed_mode.py` | 3 |
| `_test/20260929_target_group_one_by_one/test_target_group_one_by_one.py` | 8 |
| `5_DAO/_pm/tasks/20260921_SW_branch_DAO_support/review/checks/check_sw_branch.py` | 41 |
| `5_DAO/_pm/tasks/20260921_SW_branch_DAO_support/review/checks/check_dao_fixes.py` | 20 |

## 에이전트 공통 규칙

- 1. 저장소의 파일을 고치지 않는다. 쓰는 파일은 지정받은 결과 파일 하나뿐이다. 확인용 실행은 `python -c`나 있는 검사 실행으로 하고, 임시 파일이 필요하면 OS 임시 폴더에 둔다
- 2. 루트 `CLAUDE.md`를 먼저 읽는다 (문장 작성 규칙 포함: 줄표와 가운뎃점을 쓰지 않는다, 나열은 ㉮㉯㉰, 입력 파일의 성격을 서술하지 않는다)
- 3. 코드를 직접 읽고 확인한 내용만 적는다. 위치는 `파일:줄번호`로 적고 markdown 링크를 쓴다
- 4. 사소한 스타일 지적은 하지 않는다 (로직과 동작에 영향 있는 것만)
- 5. 약어와 업계 용어는 처음 쓸 때 풀어 쓴다
- 6. C++ 빌드, MPI 실행, git commit, git push는 하지 않는다
