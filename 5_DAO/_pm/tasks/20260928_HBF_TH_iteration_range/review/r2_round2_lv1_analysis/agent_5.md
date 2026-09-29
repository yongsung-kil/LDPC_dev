# Round 2 에이전트 5: 흔적, 문서, 검사 (P16, P17, P18)

> 작성: 2026-09-29
> 기준 커밋 2e34036. 줄 번호는 모두 2e34036 기준이다. 소스 읽기, 흔적 찾기, 검사 실행은 작업 폴더의 `5_DAO/SRC`, `DAO_spec.md`, `README.md`가 2e34036과 같던 때에 했다 (2026-09-29 13:56:38에 `git diff --stat 2e34036`이 비어 있음을 확인, `DAO_Main.py`는 `git show 2e34036:`과 한 줄도 다르지 않음을 확인)
> 읽은 범위: `git diff dff3dba..2e34036 -- 5_DAO/SRC 5_DAO/DAO_spec.md 5_DAO/README.md` 전체, 현재 `5_DAO/SRC` 네 파일의 HBF(Hybrid Bit Flipping, HD 복호의 iteration 1~4) 관련 자리, `DAO_spec.md` 3.6~3.8절과 5.2, 6.3절, `README.md` 타겟 그룹 설정, 3.4절, 4.1.1절, 검사 6종의 소스.
> 확인 방법: Grep으로 흔적을 찾고, 검사 6종을 실행하고, `LLR_OPT.__new__`로 만든 단일 프로세스 객체로 `Check_Fixed_Target_Group_Idx_List`와 `Set_Gen_Trial_LLR_Mode`를 stage마다 불러 보았다 (임시 스크립트는 세션 scratchpad에 두었다).

## 발견 표

| # | 심각도 | 관점 | 문제 | 위치 | 이번 변경이 만든 것인가 | 확인 방법 |
|---|--------|------|------|------|------------------------|----------|
| 1 | HIGH | P17, P18 | 타겟 목록에 SW(Syndrome Weight) 분기 그룹이 있으면 실제로 도는 모드는 10, 11뿐인데, 시작 검사(T4)와 그 오류 문구, README, spec은 9개 모드를 "함께 쓸 수 있다"고 안내한다. 안내대로 41 등을 넣으면 시작 검사를 통과한 뒤 그 모드의 stage가 올 때 멈춘다 | [DAO_Main.py:8360-8374](../../../../../SRC/DAO_Main.py#L8360), [DAO_Main.py:8476-8480](../../../../../SRC/DAO_Main.py#L8476), [README.md:123-125](../../../../../README.md#L123), [DAO_spec.md:176](../../../../../DAO_spec.md#L176) | 예 (새 설정, 새 검사, 새 안내). stage마다 멈추는 검사 자체는 2026-09-21부터 | 단일 프로세스 재현 (아래 상세) |
| 2 | MEDIUM | P17 | spec 3.7절 ㉲ "HBF 최적화 모드와 SW 분기의 결합은 다루지 않는다"가 실제 사용과 코드에 어긋난다. README 3.4절 ㉮와 spec 3.7절 ㉯는 제한 대상 시퀀스를 `Gen_LLR_Mode_SEQUENCE`로만 적어 HBF 최적화 모드의 `Gen_LLR_Mode_HBF_SEQUENCE`에도 걸린다는 것이 빠졌고, "멈춘다"가 시작이 아니라 그 모드의 stage 시작이라는 점도 빠졌다 | [DAO_spec.md:159](../../../../../DAO_spec.md#L159), [DAO_spec.md:162](../../../../../DAO_spec.md#L162), [README.md:851](../../../../../README.md#L851) | ㉲ 문장은 예전부터 있었고 이번 변경의 목적(분기 매트릭스를 HBF 최적화 모드로 돌림) 때문에 틀린 문장이 됨. README ㉮는 이번 diff에서 고쳐 쓴 문장 | 코드 대조, 단일 프로세스 재현 |
| 3 | MEDIUM | P17 | HBF 최적화 모드를 쓰는 사람이 알아야 할 안내가 README에 없다: init_n 1에서만 켜짐, iteration 1~4 row의 dv_idx 0 TH가 0이어야 시작됨, row가 iteration 4와 5 사이를 걸치면 안 됨, 기본 HBF 시퀀스 `[40, 41, 10, 11, 60]`은 타겟 목록이나 분기 타겟과 함께 쓰면 시작 또는 stage 1에서 멈춤. `DAO_Config.py` 134행 주석은 쓰이지 않는 `GenLLRModeHBF`를 가리킨다 | [README.md:932-956](../../../../../README.md#L932), [DAO_Config.py:134](../../../../../SRC/DAO_Config.py#L134) | 일부 (앞의 둘은 예전부터 빠짐, 뒤의 둘은 이번 변경으로 생긴 제약) | 문서와 코드 대조, 재현 |
| 4 | LOW | P17 | spec 3.6절 ㉰ "유효성 검사, 보정, 변이, 난수 생성이 모두 이 함수를 쓴다"가 넓게 적혀 있다. `_generate_random_row`, `_generate_mutation_for_group`(SPLIT_GROUP, INSERT_MUTATED_GROUP), `_generate_mutation_for_row`(INSERT_MUTATED_ROW)는 이 함수를 쓰지 않고 뒤이은 `Correct_LLR_Matrix`에 기댄다 | [DAO_spec.md:125](../../../../../DAO_spec.md#L125), [DAO_Main.py:795](../../../../../SRC/DAO_Main.py#L795), [DAO_Main.py:3517-3520](../../../../../SRC/DAO_Main.py#L3517), [DAO_Main.py:3568](../../../../../SRC/DAO_Main.py#L3568) | 예 (이번 diff가 쓴 문장) | Grep, 코드 읽기 |
| 5 | LOW | P16 | 쓰이지 않는 이름 세 개: `LLR_MATRIX.HBF_max_iteration`(저장만 하고 읽는 곳 없음), `GenLLRModeHBF`(정의만 있음), `HBF_OPT_CONFIG.__init__`(부르는 곳 없음) | [DAO_LLR_MATRIX.py:42](../../../../../SRC/DAO_LLR_MATRIX.py#L42), [DAO_Constants.py:43](../../../../../SRC/DAO_Constants.py#L43), [DAO_Config.py:369](../../../../../SRC/DAO_Config.py#L369) | 아니오 (`reference/`에도 같은 줄) | Grep |
| 6 | LOW | P16 | 지금 동작과 다른 docstring과 주석: `Gen_LLR_Mutate_Matrix`("HD_HBF mode라면 전 영역", "마지막 그룹"), `Gen_LLR_Mutate_CSW`("마지막 그룹"), `Generate_Random_Mutation`과 `Mutate_CSW`("Gen_LLR_Mode_SEQUENCE 한 바퀴당", HBF 제외 규칙 빠짐), `Set_Gen_Trial_LLR_Mode`의 오류 문구와 주석 | [DAO_Main.py:3726-3728](../../../../../SRC/DAO_Main.py#L3726), [DAO_Main.py:3756-3760](../../../../../SRC/DAO_Main.py#L3756), [DAO_Main.py:7079-7080](../../../../../SRC/DAO_Main.py#L7079), [DAO_Main.py:7138](../../../../../SRC/DAO_Main.py#L7138), [DAO_Main.py:8448](../../../../../SRC/DAO_Main.py#L8448), [DAO_Main.py:8458](../../../../../SRC/DAO_Main.py#L8458) | 아니오 (`reference/`에도 같은 문장) | 코드 읽기 |
| 7 | LOW | P18 | 태스크 문서 7절의 `test_fixed_target_group_idx_list.py` 내역 "20건 (타겟 목록 만들기 7, stage마다 고르는 타겟 3, 설정 검사 10)"이 지금 파일(7, 5, 10, 합계 22)과 다르다 | [20260928_HBF_TH_iteration_range.md:127](../../20260928_HBF_TH_iteration_range.md#L127) | 예 | 검사 실행, 파일의 구역 주석 |
| 8 | LOW | P18 | `test_hbf_th_iteration_range.py`가 바꾼 전역 설정(`DAO_CONFIG.IS_HBF_OPT`, `HBF_OPT_CONFIG` 두 값, `MUTATE_CONFIG`, `REGEN_ROW_CONFIG`, `REGEN_DV_CONFIG`)을 되돌리지 않는다. 지금은 파일마다 따로 실행하고, 네 파일을 한 프로세스에서 두 순서로 돌려도 44건 통과라 결과에 영향은 없다 | [test_hbf_th_iteration_range.py:68-80](../../../../../../_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py#L68) | 예 | 순서 바꿔 실행 |

심각도별: HIGH 1, MEDIUM 2, LOW 5 (합계 8)

## 발견 상세

### 1. 타겟 목록의 허용 모드 안내가 분기 제한을 빼먹어 실행 중간에 멈춤 (HIGH)

근거
- ㉮ `Check_Fixed_Target_Group_Idx_List`(T4)는 시퀀스를 `FIXED_TARGET_GROUP_ALLOWED_MODES`(9개)와만 대조한다 ([DAO_Main.py:8360-8374](../../../../../SRC/DAO_Main.py#L8360)). 오류 문구도 "Allowed modes: MUTATE_MATRIX (10), ..., REGEN_ROW (51)."로 9개를 알린다
- ㉯ 분기 그룹이 타겟 목록에 있으면 `Check_SW_Branch_Mode_Allowed`가 10, 11만 허용한다. 이 검사는 시작 때가 아니라 `Set_Gen_Trial_LLR_Mode`에서 stage마다 그 stage의 모드 하나만 본다 ([DAO_Main.py:8476-8480](../../../../../SRC/DAO_Main.py#L8476))
- ㉰ 사용자의 실제 용도(HBF 구간 iteration 1~4의 그룹만 바꿈)에서 입력 매트릭스의 iteration 1~4 그룹은 모두 분기 그룹이다. `LLR_MATRIX_1.txt`는 그룹 0, 1(헤더 20), 2(헤더 21), `LLR_MATRIX_2.txt`는 그룹 0, 1(헤더 10). 두 파일 모두 `is_HBF_OPT=True`로 읽으면 유효하다 (직접 확인)
- ㉱ 재현: `LLR_MATRIX_2.txt`, `IS_HBF_OPT=True`, `FIXED_TARGET_GROUP_IDX_LIST=[0, 1]`, `Gen_LLR_Mode_HBF_SEQUENCE=[10, 11, 41]`
  - `Check_Fixed_Target_Group_Idx_List` 결과: `[]` (시작 검사 통과)
  - stage 1 모드 10, stage 2 모드 11은 진행
  - stage 3에서 멈춤: `Set_Gen_Trial_LLR_Mode: target groups [0, 1] are SW branch groups, so mode INSERT_RANDOM_ROW (41) is not allowed. Allowed modes there: MUTATE_MATRIX, MUTATE_CSW. Point the targets (INITIAL_TARGET_GROUP_IDX or FIXED_TARGET_GROUP_IDX_LIST) at the plain groups after the branch groups to use other modes`
- ㉲ stage 1, 2는 각각 `MAX_OPTIMIZATION_TRIALS`(기본 9999)까지 도므로, 멈추기 전에 긴 시간이 지나간다. 저장된 optimal 매트릭스는 남지만 실행은 끊긴다. 오류 문구는 분명하므로 CRITICAL이 아닌 HIGH로 두었다 (사용자가 안내대로 설정해 실행이 중간에 멈춤)

고칠 방향
- 코드: `Validate_Config`에서 지금 쓰는 시퀀스의 모드마다 `Check_SW_Branch_Mode_Allowed(self.initial_LLR_matrix, mode, Build_Target_Group_Indices(self.initial_LLR_matrix))`를 불러 오류를 모은다. 그러면 `INITIAL_TARGET_GROUP_IDX`로 분기 그룹을 타겟에 넣은 경우(예전부터 있던 stage 중 멈춤)도 시작에서 잡힌다
- 문서: README 124행 아래와 spec 3.8절 ㉯ 끝에 한 문장을 넣는다: "목록에 SW 분기 그룹이 있으면 이 가운데 MUTATE_MATRIX(10)와 MUTATE_CSW(11)만 쓴다 (3.7절 ㉯). 예: `LLR_MATRIX_1.txt`와 `LLR_MATRIX_2.txt`의 iteration 1~4 그룹을 바꾸려면 `Gen_LLR_Mode_HBF_SEQUENCE = [10, 11]`"

### 2. spec 3.7절 ㉲와 SW 분기 제한의 대상 시퀀스 (MEDIUM)

근거
- ㉮ [DAO_spec.md:162](../../../../../DAO_spec.md#L162)는 HBF 최적화 모드와 SW 분기의 결합을 다루지 않는다고 적었다. 코드는 결합을 다룬다: `Set_Gen_Trial_LLR_Mode`는 HBF 최적화 모드에서 `Gen_LLR_Mode_HBF_SEQUENCE`를 고른 뒤 같은 `Check_SW_Branch_Mode_Allowed`를 부른다 ([DAO_Main.py:8442-8480](../../../../../SRC/DAO_Main.py#L8442)). 분기 그룹이 HBF 구간 안에 있어도 HBF1, HBF2가 row마다 걸리고, 두 입력 파일이 유효하다
- ㉯ [README.md:851](../../../../../README.md#L851)과 [DAO_spec.md:159](../../../../../DAO_spec.md#L159)는 "`Gen_LLR_Mode_SEQUENCE`에 10과 11만 넣는다", "다른 모드가 시퀀스에 있으면 ... 멈춘다"라고 적었다. HBF 최적화 모드의 시퀀스 이름이 빠졌고, 멈추는 때는 그 모드의 stage가 시작될 때다
- ㉰ 재현: `LLR_MATRIX_2.txt`, `IS_HBF_OPT=True`, 기본값(`INITIAL_TARGET_GROUP_IDX=1`, `FIXED_TARGET_GROUP_IDX_LIST=None`, `Gen_LLR_Mode_HBF_SEQUENCE=[40, 41, 10, 11, 60]`)이면 stage 1에서 `target groups [1, 2, 3, 4] are SW branch groups, so mode INSERT_RANDOM_GROUP (40) is not allowed.`로 멈춘다

고칠 방향 (바꿀 문장)
- spec 3.7절 ㉲: "HBF(Hybrid Bit Flipping)는 지금 HD 복호의 iteration 1~4를 뜻한다. HBF 최적화 모드(`IS_HBF_OPT`)도 분기 매트릭스에 이 절의 규칙을 그대로 쓴다. 분기 그룹이 HBF 구간 안에 있으면 3.6절의 HBF1이 그 row에도 걸리고, 타겟에 분기 그룹이 있으면 `Gen_LLR_Mode_HBF_SEQUENCE`에도 MUTATE_MATRIX와 MUTATE_CSW만 넣는다"
- spec 3.7절 ㉯와 README 3.4절 ㉮: "`Gen_LLR_Mode_SEQUENCE`(HBF 최적화 모드는 `Gen_LLR_Mode_HBF_SEQUENCE`)에 MUTATE_MATRIX(10)와 MUTATE_CSW(11)만 넣는다. 다른 모드가 있으면 그 모드의 stage가 시작될 때 `Set_Gen_Trial_LLR_Mode`가 오류 문구를 내고 멈춘다"

### 3. README의 HBF 최적화 모드 안내 누락 (MEDIUM)

근거
- ㉮ [README.md:952-956](../../../../../README.md#L952)의 `IS_HBF_OPT` 설명은 "True: HBF 전용 GenLLRMode 시퀀스 사용"뿐이다. 코드에서 확인한 사용 조건
  - ㉠ init_n이 1이 아니면 `Update_RefC_Configs`가 False로 내린다 ([DAO_Main.py:450-451](../../../../../SRC/DAO_Main.py#L450))
  - ㉡ iteration 1~4 row의 dv_idx 0 TH가 0이 아니면 초기 매트릭스 검증에서 `Initial LLR matrix validation failed.`로 멈춘다 ([DAO_LLR_MATRIX.py:525-533](../../../../../SRC/DAO_LLR_MATRIX.py#L525), [DAO_Main.py:2361-2363](../../../../../SRC/DAO_Main.py#L2361))
  - ㉢ row가 iteration 4와 5 사이를 걸치면 입력은 시작에서 멈추고 trial은 버려진다 ([DAO_LLR_MATRIX.py:491-497](../../../../../SRC/DAO_LLR_MATRIX.py#L491))
  - ㉣ `ENABLE_TWO_STAGE_TEST`와 함께 쓸 수 없다 ([DAO_Main.py:9971-9974](../../../../../SRC/DAO_Main.py#L9971))
- ㉯ [README.md:933-934](../../../../../README.md#L933)와 [DAO_Config.py:134](../../../../../SRC/DAO_Config.py#L134)는 기본 시퀀스 `[40, 41, 10, 11, 60]`만 적는다. 이 값은 `FIXED_TARGET_GROUP_IDX_LIST`와 쓰면 시작 검사(T4)에서, 분기 그룹을 타겟으로 두면 stage 1에서 멈춘다 (발견 2 재현). 134행 주석의 "GenLLRModeHBF 순서"는 정의만 있고 쓰이지 않는 enum을 가리킨다

고칠 방향
- README 4.1.1절 `IS_HBF_OPT` docstring을 다음 줄들로 바꾼다: "True: `Gen_LLR_Mode_HBF_SEQUENCE`를 쓴다 (init_n 1에서만 켜진다)", "iteration 1~`HBF_MAX_ITERATION`(4)의 row는 dv_idx 0의 TH가 `HBF_OPT_TH_CONSTANT_VAL`(0)이어야 하고 DAO가 이 값을 바꾸지 않는다", "row는 iteration 4와 5 사이를 걸치지 않는다 (DAO_spec.md 3.6절)", "`ENABLE_TWO_STAGE_TEST`와 함께 쓰지 않는다"
- README 933행 아래와 `DAO_Config.py` 134행 주석: "HBF 최적화 모드의 시퀀스. `FIXED_TARGET_GROUP_IDX_LIST`와 함께 쓰거나 타겟에 SW 분기 그룹이 있으면 `[10, 11]`을 쓴다"

### 4. spec 3.6절 ㉰의 범위 (LOW)

근거: `Is_Row_In_HBF_Iterations`를 부르는 자리는 `Is_LLR_Valid`의 HBF1([DAO_LLR_MATRIX.py:526](../../../../../SRC/DAO_LLR_MATRIX.py#L526)), `Correct_LLR_Matrix`([DAO_LLR_MATRIX.py:753](../../../../../SRC/DAO_LLR_MATRIX.py#L753)), `Gen_LLR_Regen_DV`([DAO_Main.py:4030](../../../../../SRC/DAO_Main.py#L4030)), `Gen_LLR_Regen_Row`([DAO_Main.py:4167](../../../../../SRC/DAO_Main.py#L4167)), `Generate_Random_Mutation`([DAO_Main.py:7105](../../../../../SRC/DAO_Main.py#L7105)) 다섯 곳이다. HBF2는 조건을 직접 적는다(맞는 설계). `_generate_random_row`(설계대로 난수), `_generate_mutation_for_group`(SPLIT_GROUP 3436행, INSERT_MUTATED_GROUP 3052행), `_generate_mutation_for_row`(INSERT_MUTATED_ROW 3209행)는 dv_idx 0 TH도 후보에 넣고, `Gen_Trial_LLR`의 `Correct_LLR_Matrix`([DAO_Main.py:2022](../../../../../SRC/DAO_Main.py#L2022))가 0으로 덮는다. 결과 값은 맞고, 그 칸에 쓴 변이만 헛돈다.

고칠 방향 (바꿀 문장): "㉰ HBF 구간의 row인지는 `Is_Row_In_HBF_Iterations()`가 끝 iteration으로 판단한다(`iter_end <= HBF_MAX_ITERATION`). HBF1 검사, 보정, MUTATE_MATRIX의 후보 선택, REGEN_DV와 REGEN_ROW가 이 함수를 쓴다. 다른 모드가 만든 row는 `Correct_LLR_Matrix()`가 이 함수로 dv_idx 0의 TH를 고정한다"

### 5. 쓰이지 않는 이름 (LOW)

Grep으로 찾은 줄 (`5_DAO/SRC`)
- `DAO_LLR_MATRIX.py:42:            self.HBF_max_iteration = HBF_OPT_CONFIG.HBF_MAX_ITERATION` (46, 50행은 None). 읽는 곳 없음. HBF1, HBF2, `Is_Row_In_HBF_Iterations`는 모두 `HBF_OPT_CONFIG.HBF_MAX_ITERATION`을 직접 읽는다. 이 저장 값을 누가 나중에 읽기 시작하면 두 값이 갈라질 수 있다
- `DAO_Constants.py:43:class GenLLRModeHBF(IntEnum):` 쓰는 곳은 `DAO_Config.py:134`의 주석뿐
- `DAO_Config.py:369:    def __init__(self):` `HBF_OPT_CONFIG()`를 부르는 곳 없음

고칠 방향: 세 이름을 지우고 134행 주석을 발견 3대로 고친다. 예전부터 있던 것이라 이번 리뷰의 수정 범위에 넣을지는 선택이다.

### 6. 지금 동작과 다른 docstring과 주석 (LOW)

- `Gen_LLR_Mutate_Matrix` [DAO_Main.py:3758-3760](../../../../../SRC/DAO_Main.py#L3758): "HD_HBF mode라면 전 영역에 걸쳐 수정하며, 그밖이라면 마지막 그룹의 Ch, Th를 변화시킨다. 지정된 매트릭스의 마지막 그룹을 수정" → "타겟 그룹 하나의 CH와 TH를 변이한다. HBF 최적화 모드에서는 HBF 구간 row의 dv_idx 0 TH를 후보에서 뺀다"
- `Gen_LLR_Mutate_CSW` [DAO_Main.py:3726-3728](../../../../../SRC/DAO_Main.py#L3726): "마지막 그룹의 CSW" → "타겟 그룹의 CSW"
- `Generate_Random_Mutation` [DAO_Main.py:7079-7080](../../../../../SRC/DAO_Main.py#L7079)과 `Mutate_CSW` [DAO_Main.py:7138](../../../../../SRC/DAO_Main.py#L7138): "Gen_LLR_Mode_SEQUENCE 한 바퀴당" → "지금 쓰는 모드 시퀀스 한 바퀴당", 그리고 `Generate_Random_Mutation`에 HBF 제외 규칙 한 줄
- `Set_Gen_Trial_LLR_Mode` [DAO_Main.py:8448](../../../../../SRC/DAO_Main.py#L8448): HBF 최적화 모드에서 빈 시퀀스여도 "Gen_LLR_Mode_SEQUENCE must define at least one mode."라고 알린다

없앤 것의 흔적: `HBF_OPT_USING_UNCOR`, `bundle_of_group`, `current_target_bundle`, `_Get_Target_Bundle_Groups`, "only the last", 매트릭스 max_iteration 상한 문구("greater than HBF_MAX_ITERATION")는 `5_DAO/SRC`, `DAO_spec.md`, `README.md`, 검사 6종에 남아 있지 않다. `_pm` 쪽에 남은 줄은 이력 기록이다 (`_pm/TODO.md` 17, 19, 57, 60, 65, 66행, `20260921_SW_branch_DAO_support.md`는 6행 머리말에서 코드에 없는 설계라고 밝힘). `Check_SW_Branch_Mode_Allowed`를 부르는 자리는 [DAO_Main.py:8478](../../../../../SRC/DAO_Main.py#L8478), `check_sw_branch.py` 131~138행, `test_target_group_one_by_one.py` 92, 100행으로, 모두 인자 세 개(매트릭스, 모드, 타겟 목록)로 새 시그니처와 맞다.

### 7. 태스크 문서 7절의 건수 내역 (LOW)

`test_fixed_target_group_idx_list.py`의 구역 주석 기준 실제 내역은 타겟 목록 만들기 7건(111~139행), stage마다 고르는 타겟 5건(141~175행), 설정 검사 10건(176행~)이다. 7절 첫 문장을 "22건 (타겟 목록 만들기 7, stage마다 고르는 타겟 5, 설정 검사 10)"으로 다시 쓴다.

### 8. 검사가 전역 설정을 되돌리지 않음 (LOW)

`test_hbf_th_iteration_range.py`는 `setUpClass`에서 `DAO_CONFIG.IS_HBF_OPT`, `HBF_OPT_CONFIG.HBF_MAX_ITERATION`, `HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL`을, 각 검사에서 `MUTATE_CONFIG`(129~130행), `REGEN_ROW_CONFIG`(147행), `REGEN_DV_CONFIG`(159~161행)를 바꾸고 되돌리지 않는다. 나머지 세 unittest 파일은 `setUp`/`tearDown`에서 되돌린다. `check_sw_branch.py`와 `check_dao_fixes.py`는 위에서 아래로 한 번 도는 스크립트라 되돌리지 않아도 순서가 고정이다. 영향 확인은 아래 표.

## 검사 실행 결과

| 검사 | 건수 | 결과 |
|------|------|------|
| `_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py` | 11 | 통과 (종료 코드 0) |
| `_test/20260928_fixed_target_group_idx_list/test_fixed_target_group_idx_list.py` | 22 | 통과 |
| `_test/20260928_hbf_seed_mode/test_hbf_seed_mode.py` | 3 | 통과 |
| `_test/20260929_target_group_one_by_one/test_target_group_one_by_one.py` | 8 | 통과 |
| `check_sw_branch.py` | 41 | PASS 41, FAIL 0 |
| `check_dao_fixes.py` | 20 | PASS 20, FAIL 0 |
| unittest 네 파일, 파일 안 순서를 거꾸로 1회와 무작위 3회 | 11, 22, 3, 8 | 모두 통과 |
| unittest 네 파일을 한 프로세스에서 (정순, 역순, th와 one_by_one, th와 seed) | 44, 44, 19, 14 | 모두 통과 |

실행 시각: 2026-09-29 13:50 부근 (13:56:38 확인 때까지 작업 폴더의 SRC가 2e34036과 같았으므로 2e34036 기준 결과다). context.md의 건수 표와 모두 같다. 실행 뒤 `git status`에 `5_DAO/SRC`와 `checks/mat` 변경 없음.

## 검사가 덮지 못하는 자리

- ㉮ `Gen_Trial_LLR` 전체 흐름(모드 실행, `Correct_LLR_Matrix`, `Validate_LLR_Matrix`)을 HBF 최적화 모드로 도는 검사가 없다. INSERT_RANDOM_GROUP, SPLIT_GROUP, INSERT_RANDOM_ROW가 경계를 걸치는 row를 만들어 HBF2로 버려지는 경로와, 버려지는 trial이 이어질 때의 연속 실패 종료([DAO_Main.py:8182](../../../../../SRC/DAO_Main.py#L8182))는 덮이지 않는다
- ㉯ `Validate_Config` 자체는 불리지 않는다 (검사는 `Check_Fixed_Target_Group_Idx_List`만 직접 부른다). `Setup`의 순서(`Initialize_LLR_Matrix` 다음 `Validate_Config`)도 덮이지 않는다
- ㉰ 타겟 목록과 분기 제한의 결합: 시작 검사 통과 뒤 stage 중간에 멈추는 경우(발견 1)를 보는 검사가 없다
- ㉱ 실제 입력 `LLR_MATRIX_1.txt`, `LLR_MATRIX_2.txt`를 `is_HBF_OPT=True`로 `Is_LLR_Valid`에 넣는 검사가 없다 (`test_fixed_target_group_idx_list.py`는 읽기만, `check_sw_branch.py`는 `IS_HBF_OPT=False`). 이번에 직접 돌려 두 파일 모두 `(True, '')`, max_iteration 124를 확인했다
- ㉲ `Initialize_Stage`의 타겟 목록 다시 만들기와 로그, `Update_Optimal_LLR`의 빈 목록 복원([DAO_Main.py:9738](../../../../../SRC/DAO_Main.py#L9738))
- ㉳ `Bcast_Trial_LLR_Mode`의 튜플 칸 수(묶음 칸 삭제)와 worker 쪽 풀기 (MPI 필요)
- ㉴ `Update_RefC_Configs`의 `IS_HBF_OPT` 내리기와 `HBF_OPT_CONFIG`
- ㉵ REGEN_DV, REGEN_ROW의 재사용 모드(검사는 `is_gen_row_reuse_mode=False`), COPY_ROWS, COPY_GROUP, SWAP_ROW, INSERT_MUTATED_ROW가 HBF 구간 안과 밖 사이로 값을 옮기는 경로
- ㉶ `_generate_random_row`의 결과가 `Correct_LLR_Matrix`를 거쳐 고정되는지 (GEN_SINGLE_ROW 10372행, INSERT_RANDOM_ROW 2414행, INSERT_RANDOM_GROUP 2690행)
- ㉷ TEST_FER, SAVE_UNCOR, REDECODE, GEN_SINGLE_ROW를 HBF 최적화 모드로 돌 때의 매트릭스별 흐름
- ㉸ C++ 디코더(`decoder.cpp`)와 DAO 규칙의 일치 (빌드 불가, 에이전트 4 담당)

## 사용자가 MPI 실행에서 볼 로그 줄

설정 출력 (`Print_Configs`, [DAO_Main.py:7282-7290](../../../../../SRC/DAO_Main.py#L7282), 값은 예)
```
- IS_HBF_OPT: True
- Gen_LLR_Mode_HBF_SEQUENCE: [10, 11]
- FIXED_TARGET_GROUP_IDX_LIST: [0, 1]
- HBF_MAX_ITERATION: 4
- HBF_OPT_TH_CONSTANT_VAL: 0
```

초기 매트릭스 검증 ([DAO_Main.py:2603](../../../../../SRC/DAO_Main.py#L2603), [DAO_Main.py:10077](../../../../../SRC/DAO_Main.py#L10077), [DAO_Main.py:2363](../../../../../SRC/DAO_Main.py#L2363)). 통과하면 오류 줄이 없고, 실패하면 아래 가운데 하나 다음에 멈춘다
```
[Load initial matrix from] {input_path}
In HD_HBF_OPT mode, Group {g_idx} Row {r} DV {dv_idx} invalid TH values: expected all {HBF_OPT_TH_CONSTANT_VAL} for iteration {iter_start}~{iter_end} (HBF iterations are 1~{HBF_MAX_ITERATION}), got {th_part}
In HD_HBF_OPT mode, Group {g_idx} Row {r} iteration {iter_start}~{iter_end} crosses the HBF boundary: a row must end within iteration 1~{HBF_MAX_ITERATION} or start after it
Initial LLR matrix validation failed.
```

설정 검사 ([DAO_Main.py:10040-10044](../../../../../SRC/DAO_Main.py#L10040))
```
[Config validation] No error.
```
실패하면 `[Validate_Config] Invalid configuration detected:` 뒤에 `- {오류 문구}` 줄들. 타겟 목록 쪽 문구는 [DAO_Main.py:8340-8374](../../../../../SRC/DAO_Main.py#L8340)의 여섯 가지(`must be a list of group indices`, `must not be empty`, `must contain integers only`, `out of range`, `more than once`, `... cannot run with FIXED_TARGET_GROUP_IDX_LIST. Allowed modes: ...`)

stage 시작 ([DAO_Main.py:2297](../../../../../SRC/DAO_Main.py#L2297), [DAO_Main.py:7228-7229](../../../../../SRC/DAO_Main.py#L7228)). 요구 6(지정한 그룹이 분기 index와 상관없이 바뀜)은 둘째, 셋째 줄의 따옴표 친 값이 목록을 차례로 도는지로 본다
```
	- Updated target_group_indices: [0, 1] (from optimal_LLR_matrix and FIXED_TARGET_GROUP_IDX_LIST)
[current_gen_trial_LLR_mode]: MUTATE_MATRIX (10)  (1/2) ['10', 11]
[target_group_indices]: 0  ['0', 1]
```

seed 모드 ([DAO_Main.py:8702](../../../../../SRC/DAO_Main.py#L8702)). 최적화 실행에서 `LOAD_UNCOR_MODE`가 LOAD_SEED면 `LOAD_UNCOR_SEED`, LOAD_VECTOR면 `LOAD_UNCOR_VECTOR`
```
[current_seed_mode]: LOAD_UNCOR_SEED
```

trial 중 ([DAO_Main.py:2011](../../../../../SRC/DAO_Main.py#L2011), [DAO_Main.py:2024](../../../../../SRC/DAO_Main.py#L2024), [DAO_Main.py:2516](../../../../../SRC/DAO_Main.py#L2516))
```
[SW branch] {mode_name} changed groups before the target: {protected_change}. Trial discarded
[Corrected LLR Matrix]
[Gen_Trial_LLR failed] Matrix idx: {idx} — 검증 실패 (상세는 위 로그 참조)
```

멈춤 (발견 1, 2의 경우, [DAO_Main.py:8480](../../../../../SRC/DAO_Main.py#L8480))
```
Set_Gen_Trial_LLR_Mode: target groups [0, 1] are SW branch groups, so mode INSERT_RANDOM_ROW (41) is not allowed. Allowed modes there: MUTATE_MATRIX, MUTATE_CSW. Point the targets (INITIAL_TARGET_GROUP_IDX or FIXED_TARGET_GROUP_IDX_LIST) at the plain groups after the branch groups to use other modes
```

## 통과 관점

- P16 없앤 것의 흔적: SRC, spec, README, 검사 6종에 남은 흔적 없음. `Check_SW_Branch_Mode_Allowed`의 모든 부르는 자리가 인자 세 개로 맞음
- P17 spec 3.6절 HBF1, HBF2 표: 조건과 부등호가 [DAO_LLR_MATRIX.py:492](../../../../../SRC/DAO_LLR_MATRIX.py#L492), [DAO_LLR_MATRIX.py:106](../../../../../SRC/DAO_LLR_MATRIX.py#L106)과 같음. ㉱(max_iteration 상한 없음)는 코드에서 상한 검사가 빠진 것과 맞음
- P17 spec 3.7절 ㉰의 예 `[3]`, `[4, 5]`: 같은 절 예 표(`LLR_MATRIX_1.txt`)와 직접 읽은 배치(그룹 3 헤더 20 분기 0 iteration 5~8, 그룹 4, 5 헤더 21 분기 1 iteration 5~5, 6~8)가 같음
- P17 spec 3.8절 T1~T4: `Check_Fixed_Target_Group_Idx_List`의 검사와 하나씩 대응 (T1 목록 꼴과 빈 목록, T2 정수와 범위, T3 중복, T4 시퀀스). 정수가 아닌 값이 있으면 T2 뒤를 건너뛰고 바로 돌려주는 것은 문서와 어긋나지 않음
- P17 spec 5.2절 특수 로직과 6.3절 3번: `Generate_Random_Mutation`, `Correct_Ch_Th_In_Row`와 같음
