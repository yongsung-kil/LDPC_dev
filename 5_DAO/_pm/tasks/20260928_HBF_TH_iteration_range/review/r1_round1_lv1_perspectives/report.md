## Round 1 결과: 관점 리스트업

> 작성: 2026-09-29 13:45:55
> 에이전트 3개(A 값의 흐름, B 실행 흐름과 설정 조합, C 요구와 근거와 문서와 검사)가 관점 38개(12, 14, 12)를 냈다. 겹치는 것을 합쳐 18개로 정리했다.

도출된 관점:

| # | 관점명 | 확인 항목 | 대상 파일/범위 | 출처 |
|---|--------|----------|--------------|------|
| P1 | HBF 구간 판단 기준과 경계값 | ㉮ `Is_Row_In_HBF_Iterations`가 끝 iteration만 보는데 HBF2보다 먼저 불리는 자리(보정, 변이, 다시 만들기)에 경계를 걸친 row가 들어오면 어떤 값이 되는지<br>㉯ `<=`와 `<`가 HBF1, HBF2, 디코더 조건에서 같은 쪽인지<br>㉰ `self.HBF_max_iteration`(저장 값)과 `HBF_OPT_CONFIG.HBF_MAX_ITERATION`(읽는 값)이 갈라질 수 있는지<br>㉱ init_n 2, 3에서 `is_HBF_OPT`를 내리는 두 자리가 같은 결론인지 | `DAO_LLR_MATRIX.py` 36~50, 98~106, `DAO_Main.py` 450~451 | A1, B1, C3 |
| P2 | HBF1, HBF2의 검사 순서와 적용 대상 | ㉮ restart row가 HBF1, HBF2를 모두 건너뛰는 것<br>㉯ HBF1이 비증가 검사(RW5) 뒤에 있어 어느 오류 문구가 먼저 나오는지<br>㉰ 한 그룹 안 row들의 iteration이 서로 다를 때의 판단 | `DAO_LLR_MATRIX.py` 452~533 | A2, C3 |
| P3 | 보정과 유효성 검사의 순서 | ㉮ trial 경로(보정 뒤 검사)와 초기 매트릭스 경로(보정 없이 검사)의 차이<br>㉯ 상수 0이 헤더 min_value보다 작을 때 보정과 검사의 결과<br>㉰ 상수 고정이 보정 로그에 남는지<br>㉱ 보정 실패(ValueError)와 검사 실패 trial의 처리 | `DAO_LLR_MATRIX.py` 731~835, `DAO_Main.py` 1964~2031, 2338~2363, 10067~10078 | A3, B6, C3, C4 |
| P4 | iteration이 정해지기 전의 row 생성 | `_generate_random_row`의 결과를 쓰는 모든 자리가 매트릭스에 넣은 뒤 `Correct_LLR_Matrix`를 거치는지, 거치지 않고 측정이나 저장으로 가는 경로 | `DAO_Main.py` 766~797, 2074, 2414, 2690, 3606~3677, 10363~10399 | A4, B6, C4 |
| P5 | 값 재사용과 조정 단계 | ㉮ REGEN_DV, REGEN_ROW의 재사용 모드가 HBF 구간 안과 밖의 row 사이에서 값을 옮길 때<br>㉯ MUTATE_MATRIX의 미세 조정과 거친 조정이 제외 column을 다시 넣거나 이전 타겟 그룹을 그대로 쓰는지 | `DAO_Main.py` 3755~3915, 3917~4191 | A5, A6, C5 |
| P6 | 변이 후보와 제외 column | ㉮ `HBF_immutable_col_range`가 dv_idx 0의 TH 칸과 정확히 같은지, CH는 변이하는지<br>㉯ 후보가 비었을 때의 흐름 | `DAO_Main.py` 7067~7131, `DAO_LLR_MATRIX.py` 710~715 | A6, B7, C1 |
| P7 | 그룹 구조를 바꾸는 모드와 HBF2 | ㉮ INSERT_RANDOM_GROUP, SPLIT_GROUP, GEN_INITIAL_GROUP이 만드는 iteration이 경계를 걸치는지, 뒤 그룹이 밀려 HBF 구간 밖으로 나갈 때<br>㉯ SPLIT_GROUP의 back 그룹 변이가 dv_idx 0 TH를 후보에서 빼지 않는 것<br>㉰ 버려지는 trial이 많을 때 연속 실패 종료(`seq_len * 2`)에 닿는지 | `DAO_Main.py` 2609~2760, 3351~3540, 3606~3677, 8177~8187, `DAO_Config.py` 134, 240~261 | A7, B7, C6 |
| P8 | row를 옮기는 모드의 값 이동 | INSERT_RANDOM_ROW, COPY_ROWS(외부 후보 포함), COPY_GROUP, SWAP_ROW가 HBF 구간 안과 밖 사이에서 값을 옮길 때 보정이 새 iteration 기준으로 고정하는지 | `DAO_Main.py` 2383~2450, 3679~3723, 4193~4375, 6353 | A8, B7 |
| P9 | 실행 모드별 HBF 경로 | ㉮ GEN_SINGLE_ROW가 iteration 1~50 row를 만들어 HBF2로 늘 버려지는지, `Validate_Config`가 막는지<br>㉯ TEST_FER, SAVE_UNCOR, REDECODE에서 매트릭스마다 HBF 판정과 타겟 목록이 다시 정해지는지 | `DAO_Main.py` 10138~10183, 10363~10400, 10020~10026 | A9, B9 |
| P10 | 모드 제한과 HBF 기본 시퀀스의 결합 | ㉮ 기본 HBF 시퀀스 `[40, 41, 10, 11, 60]`과 타겟 목록(T4), SW 분기 타겟의 조합<br>㉯ `Check_SW_Branch_Mode_Allowed`가 stage에서만 도는 것<br>㉰ `_Protected_Groups_Changed`의 보호 범위(목록 최솟값 앞)와 떨어진 목록, 보정보다 앞선 비교 | `DAO_Main.py` 2007~2031, 8329~8438, `DAO_Constants.py` 206~223 | A10, B5, C6 |
| P11 | 타겟 목록의 생성, 검사, 순환 | ㉮ 목록을 만드는 세 자리의 일관성과 "범위가 비면 마지막 그룹" 대체<br>㉯ `Setup` 순서에서 잘못 적은 목록이 검사 전에 쓰이는 자리<br>㉰ stage마다 고르는 순환과 별도 카운터 `current_target_idx`<br>㉱ 그룹 수 초과 시 마지막 그룹 대체, 구조 변경 모드가 목록을 갱신하는 경로 | `DAO_Main.py` 2276~2322, 2338~2363, 8310~8327, 8440~8474, 8857~8866, 9730~9738 | B2, B3, B4, C7 |
| P12 | seed 모드와 uncor 풀 | ㉮ 실행 모드와 uncor 로드 모드 조합이 풀과 맞는지<br>㉯ 최적화 중 LOAD_NONE의 중단, vector 경로의 길이 계산<br>㉰ 2단계 테스트 금지 검사가 여전히 유효한지 | `DAO_Main.py` 404~458, 7472~7501, 8648~8746, 9959~9974 | B8, C8 |
| P13 | 설정 출처와 MPI로 옮기는 값 | ㉮ `IS_HBF_OPT`가 정해지는 순서<br>㉯ `Bcast_Trial_LLR_Mode`의 칸 수와 순서<br>㉰ 타겟 목록을 root만 고치는 사이 worker가 읽는 자리<br>㉱ 복사와 방송 뒤 `is_HBF_OPT`, `HBF_immutable_col_range` 보존 | `DAO_Main.py` 404~491, 830~856, 9724~9754, `DAO_LLR_MATRIX.py` 355~385 | A11, B1, B10 |
| P14 | 디코더 소스와 DAO 규칙의 일치 | ㉮ `__AUTO_LLR_OPT__` 갈래의 `ITER_MAX_HBF`(0)와 상수 4<br>㉯ 같은 갈래에서 `flag_BF_on`이 참이 되는지<br>㉰ `v_deg > DV_5`가 dv_idx 0 하나에 대응하는지<br>㉱ 디코더의 iteration 눈금과 매트릭스 row의 iteration이 같은지<br>㉲ 문서의 "decoder.cpp:4058" 인용이 가리키는 갈래 | `0_LDPC_original/src/common.h` 403~407, `mode.h` 22, `decoder.cpp` 2084~2120, 4040~4080, 4268~4282, 6973~7000 | C2 |
| P15 | 사용자 요구 6가지와 구현의 대응 | 요구마다 코드 자리를 대응시켜 빠진 것, 특히 요구 3(경계가 4와 5 사이 하나만 검사됨)과 요구 4(앞부분과 뒷부분을 따로 최적화하는 설정이 실제로 만들어지는지) | context.md의 요구, 태스크 문서 3.1~3.3절, 6절 | B12, C1 |
| P16 | 없앤 것의 흔적과 쓰이지 않는 이름 | ㉮ max_iteration 상한 검사, `HBF_OPT_USING_UNCOR`, 묶음, 마지막 분기 규칙의 잔재<br>㉯ `HBF_max_iteration`, `GenLLRModeHBF`, `HBF_OPT_CONFIG.__init__`<br>㉰ docstring(`Gen_LLR_Mutate_Matrix`, `Generate_Random_Mutation`, `Mutate_CSW`)<br>㉱ `Check_SW_Branch_Mode_Allowed`를 부르는 자리의 인자 수 | `5_DAO/SRC`, 검사 스크립트, `_pm/TODO.md` | B11, C9, C10 |
| P17 | 문서와 코드의 일치 | ㉮ spec 3.6절 표와 ㉰(모든 자리가 이 함수를 쓴다)<br>㉯ spec 3.7절 ㉲(HBF 최적화 모드와 SW 분기의 결합은 다루지 않는다)와 실제 사용 방식<br>㉰ spec 3.7절 ㉰의 예와 표의 그룹 번호<br>㉱ spec 3.8절 T1~T4와 검사 함수<br>㉲ README의 HBF 서술 | `DAO_spec.md` 116~185, 250, 621, `README.md` 110~125, 847~853, 932~960 | A12, B13, C11 |
| P18 | 검사가 덮는 것과 덮지 못하는 것 | ㉮ 덮지 못하는 자리 목록<br>㉯ 검사가 전역 설정을 바꾼 뒤 되돌리는지<br>㉰ 태스크 문서 7절의 건수가 실제 실행과 같은지<br>㉱ 사용자가 MPI 실행에서 볼 로그 줄 | `_test/2026092*`, `check_sw_branch.py`, `check_dao_fixes.py` | A12, B14, C12 |

## 다음 단계 결정

→ Round 2 (lv1, 에이전트 5개)

사유: 변경은 SRC 네 파일 약 340줄이고 HBF 경로의 자리가 표 하나로 정리된다. 관점 사이의 의존이 작아 팀 리더의 교차 분석 없이 관점 묶음별로 나눠 읽는 편이 빠르다. 디코더 소스 대조(P14)는 읽을 양이 많아 요구 대응(P15)과 묶어 따로 둔다.

| 에이전트 | 맡은 관점 | 묶음 이름 |
|---------|----------|----------|
| 1 | P1, P2, P3, P4, P5, P6 | 값 규칙과 값 생성 |
| 2 | P7, P8, P9, P10 | 모드와 trial 흐름 |
| 3 | P11, P12, P13 | 타겟 목록, seed 모드, 설정과 MPI |
| 4 | P14, P15 | 디코더 근거와 요구 대응 |
| 5 | P16, P17, P18 | 흔적, 문서, 검사 |
