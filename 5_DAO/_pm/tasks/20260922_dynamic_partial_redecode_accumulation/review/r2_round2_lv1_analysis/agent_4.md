# Round 2 분석: 에이전트 4 (관점 14, 15, 16)

> 작성: 2026-09-22 10:23:00
> 담당 관점: 14 실행 모드별 회귀, 15 시그니처 호환과 문서 정합, 16 대안 접근과 두 수정의 독립성
> 대상: `5_DAO/SRC/DAO_Main.py` diff 3곳, 태스크 문서, `5_DAO/README.md` 3.2절, `0_LDPC_original/src/random.cpp`, `ecc_top.cpp`

## 1. 확인 범위

- ㉮ `git diff HEAD -- 5_DAO/SRC/DAO_Main.py`의 3곳(Delete_Own_Uncors 1530행, Set_Test_Environment 8548~8552행, Update_Optimal_LLR 9688~9692행)을 읽고, 각 실행 모드에서 seed 모드가 어떻게 정해지는지 Set_Seed_Mode(8572행), Update_Exit_After_Run_Configs(404행), Validate_Config(9884~9915행), Update_Configs(486행)로 추적했다
- ㉯ Delete_Own_Uncors 호출처를 `5_DAO/` 전체에서 검색했고, `reference/SRC/DAO_Main.py`는 git status에서 수정 흔적이 없음을 확인했다
- ㉰ Ref-C의 Print_Seed(random.cpp 207~216행)와 mode 12의 파일 이름 생성(ecc_top.cpp 560~572행), 기록 시점(928~932행), 적재(2563~2565행)를 읽었다
- ㉱ 코드 실행이나 C++ 빌드는 하지 않았다

## 2. 관점별 확인 결과

### 관점 14. 실행 모드별 회귀

| 항목 | 결과 | 근거 |
|---|---|---|
| RUN_OPTIMIZATION, Two-Stage 꺼짐 | 무영향 | Set_Seed_Mode는 DEFAULT, LOAD_UNCOR_SEED, LOAD_UNCOR_VECTOR만 낸다(8595~8626행). LOAD_UNCOR_SEED_SAVE_UNCOR_SEED는 Test_Initial_LLR의 Two-Stage 분기(9331행), Rebuild_Partial_Pool(9450행), REDECODE 분기(8600행) 세 곳만 만든다. Update_Optimal_LLR의 조건은 ENABLE_TWO_STAGE_TEST를 먼저 보므로(9689행) `not is_initial`은 평가되지 않는다 |
| HBF(IS_HBF_OPT) | 무영향 | Set_Seed_Mode의 HBF 분기(8588~8592행)는 LOAD_UNCOR_SEED 또는 DEFAULT만 낸다. REDECODE 분기는 HBF 분기의 else 아래(8593행 이후)라 HBF와 REDECODE를 함께 켜도 mode 12가 나오지 않는다. Two-Stage와 HBF의 동시 사용은 Validate_Config가 막는다(9903~9906행) |
| RunDAOMode.SAVE_UNCOR | 무영향 | Update_Exit_After_Run_Configs가 LOAD_NONE으로 강제(409~410행), Set_Seed_Mode가 SAVE_UNCOR_SEED를 낸다(8597~8598행). Set_Test_Environment의 기존 if 분기(8548~8549행)만 타고, 호출 `Delete_Own_Uncors(ch_idx=ch_idx)`는 새 인자의 기본값 False로 이전과 같은 working copy 이름을 지운다(2090행 `redecode_header = ""`). Test_LLR 채널 루프 끝의 Gather(9080~9083행)는 is_redecoded_uncor=False로 변함없다 |
| RunDAOMode.TEST_FER | 무영향 | DEFAULT(8595~8596행). Set_Test_Environment의 어느 분기도 타지 않는다 |
| RunDAOMode.GEN_SINGLE_ROW | 무영향 | Update_Exit_After_Run_Configs가 LOAD_SEED(411~412행), Run_Single_Row_Generation은 Set_Ref_C_Parameters(is_test_initial=False)를 부르고(10186행) current_gen_trial_LLR_mode가 None이라 "other mode" 분기에서 LOAD_UNCOR_SEED가 된다(8621~8623행). Set_Test_Environment(10195행)는 어느 삭제 분기도 타지 않는다. Two-Stage와의 동시 사용은 Validate_Config가 막는다(9915~9919행) |
| Two-Stage와 multi-matrix 조합 | 도달 불가 | REDECODE는 Validate_Config 9884~9889행이 명시적으로 막고, TEST_FER와 SAVE_UNCOR는 LOAD_NONE 강제 뒤 Validate_Config 9892~9896행에서 막힌다. Update_Configs(486행)가 Update_Exit_After_Run_Configs를 먼저 부르고 Validate_Config는 Setup(8794행)에서 부르므로 순서가 맞다. 따라서 `not is_initial`은 RUN_OPTIMIZATION의 Two-Stage 경로에서만 뜻을 가진다 |
| Set_Seed_Mode의 "mode 12 보존" 규칙 | 예상 밖 시점 없음 | Two-Stage에서는 Test_Initial_LLR Step 4(9358~9363행)와 _Restore_State_After_Partial_Rebuild(9536~9541행)가 LOAD_UNCOR_SEED로 되돌린 뒤 trial 테스트에 들어가므로 trial 중에는 새 elif가 타지 않는다. REDECODE에서는 초기 테스트부터 끝까지 mode 12가 유지되는데 그것이 의도한 동작이다 |
| REDECODE 단일 매트릭스 | 결과 같음 | 새 세션의 local_session_dir에 redecode 파일이 없으므로 삭제는 무동작(`target_path.exists()` False)이고 Ref-C 출력과 Gather 결과가 이전과 같다 |
| REDECODE multi-matrix (INITIAL_MATRIX_IDX_LIST) | 결과가 달라짐, 개선 | 아래 발견 1 참조 |

REDECODE multi-matrix의 흐름을 코드로 따라간 결과는 다음과 같다.

- ㉮ _Run_Exit_After_Multi_Matrix(10068행)는 같은 세션에서 매트릭스마다 Run_Initial_Test를 반복한다. _Reset_For_Next_Matrix(10058행)와 _init_per_matrix_state(584행)는 메모리 상태만 초기화하고 local_session_dir의 파일은 건드리지 않는다. current_seed_mode는 _init_per_matrix_state 밖(573행)에 있어 첫 매트릭스의 mode 12가 그대로 남고, Set_Seed_Mode의 보존 규칙(8586~8587행)으로 두 번째 매트릭스도 mode 12다
- ㉯ 수정 전에는 두 번째 매트릭스의 Ref-C가 첫 매트릭스의 실패 seed가 든 `redecode_uncor_seed_..._{rank}.txt`에 이어쓰기하고(random.cpp 209행 `"a"`), Cleanup_Test_Environment의 규칙(EXTENSIONS_TO_REMOVE, HEADER_TO_REMOVE, DAO_Constants.py 128~129행)에도 "redecode_"가 없어 파일이 남는다. Gather_And_Archive_Uncors(2129~2131행)는 dest만 새로 만들고 src는 있는 그대로 읽으므로 `Redecoded_uncors/{두 번째 매트릭스}/`에 첫 매트릭스 실패분이 섞이고, Update_Uncors_To_Input(7855행)이 그 섞인 파일을 Input에 저장했다
- ㉰ 수정 후에는 두 번째 매트릭스의 Set_Test_Environment가 자기 redecode 파일을 먼저 지우므로 Input에는 그 매트릭스가 정정하지 못한 uncor만 저장된다. REDECODE의 목적("uncor 로드 후 다시 저장")에 맞는 결과이며 회귀가 아니라 개선이다. 다만 태스크 문서 5장 ㉱의 "결과는 같다"는 단일 매트릭스(또는 목록의 첫 매트릭스)에만 맞는 서술이다

### 관점 15. 시그니처 호환과 문서 정합

| 항목 | 결과 | 근거 |
|---|---|---|
| Delete_Own_Uncors 호출처 전수 | 2곳뿐 | `5_DAO/` 전체 grep 결과 SRC/DAO_Main.py 8549행(기존, 키워드 호출), 8552행(신규, 키워드 호출). 위치 인자에 의존하는 호출이 없고 새 인자는 마지막에 기본값 False로 붙어 기존 호출의 동작이 같다 |
| reference/SRC 미수정 | 확인 | `git diff HEAD --stat -- 5_DAO/`에 SRC/DAO_Main.py와 _pm/TODO.md만 있다. reference/SRC/DAO_Main.py 1515행의 Delete_Own_Uncors는 원형 시그니처 그대로다 |
| 새 docstring(1531~1536행) | 규칙 적합 | 긍정문이고 줄표와 가운뎃점이 없으며 과거 동작과 견주는 표현이 없다. 두 모드와 각각 지우는 파일을 한 문장으로 나열해 뜻이 분명하다 |
| Set_Test_Environment 주석(8551행) | 규칙 적합 | "Ref-C는 실패 seed를 redecode 파일에 이어쓰기로 붙이므로, 이번 실행분만 남도록 이전 파일을 먼저 지운다". 현재 동작의 이유를 말하는 긍정문이다. "이전 파일"은 직전 실행이 남긴 파일을 가리키는 것이지 과거 코드 서술이 아니다 |
| Update_Optimal_LLR 주석(9685~9686행) | 규칙 적합 | "초기 매트릭스의 Partial 풀은 Test_Initial_LLR이 이미 만들었으므로 is_initial이면 건너뛴다". 긍정문, 기호 없음 |
| Set_Test_Environment docstring(8530행) | 적합 | "현재 시드 모드에 맞춰 사전 정리를 수행한다"는 두 모드를 모두 포괄한다 |
| README 3.2.1 흐름도 | 정합 | "초기 매트릭스 Full 테스트(실패 uncor 저장) → 실패 uncor를 모아 Partial 풀 생성 → ... Full Test 개선 → Optimal 갱신, Partial 풀 재구성"은 수정 후 흐름(초기는 한 번만 만들고 이후 갱신마다 재구성)과 같다 |
| README 3.2.4 ㉱ | 정합 | "optimal이 갱신되면 그 매트릭스의 실패 uncor로 Partial 풀을 다시 만든다". 초기 경로는 ㉯㉰가 따로 서술하므로 초기 update에서도 Rebuild가 돈다고 읽힐 여지가 없다 |
| README 3.2.5 코드 블록 | 정합 | trial 경로의 판단 순서를 보이는 의사 코드이며 초기 경로를 다루지 않는다. Rebuild_Partial_Pool이 실제로는 Update_Optimal_LLR 안에서 불린다는 점은 이전부터 같은 단순화다 |
| 태스크 문서 3장 제목 "수정 2건" 대 표 3행 | 불일치 | 아래 발견 2 참조 |
| 7장 검증 로그 문자열 | 일치 | "[Initial Partial] Dynamic partial pool created: {N} fail uncors"(9425~9427행), "[Rebuild_Partial_Pool] Partial pool reconstructed: {M} fail uncors"(9509~9511행). 문서의 "..." 생략 표기와 앞뒤가 같다 |
| Count_Gathered_Uncors 단위 | 일치 | 공백 아닌 줄 수를 NUM_LINES_PER_UNCOR로 나눈다(1049~1058행). seed 모드의 NUM_LINES_PER_UNCOR는 기본값 1(DAO_Config.py 214행)이고 Update_RefC_Configs는 LOAD_VECTOR일 때만 바꾸는데(455~458행) Two-Stage는 LOAD_VECTOR를 막는다(9897~9901행). Ref-C는 mode 12에서 CRC 실패(FLAG_HIGH == o_CRC_flag)마다 Print_Seed로 한 줄을 쓴다(ecc_top.cpp 928~932행, random.cpp 210~214행). 따라서 N은 실패 seed 수와 같다 |
| N과 비교할 "초기 Full 실패 수" | 출처 보완 권장 | 아래 발견 3 참조 |

### 관점 16. 대안 접근과 두 수정의 독립성

| 대안 | 판정 | 근거 |
|---|---|---|
| Ref-C Print_Seed를 `"w"`로 | 채택 불가 | Print_Seed는 호출마다 fopen과 fclose를 한다(random.cpp 209행, 215행). `"w"`로 바꾸면 실패마다 파일이 비워져 마지막 seed 한 줄만 남는다. 같은 함수를 SAVE_UNCOR_SEED, SAVE_COR_SEED, SAVE_CORNER_SEED, SAVE_ALL_SEED(ecc_top.cpp 909~926행)가 공유하므로 모든 저장 모드가 깨진다. 한 번만 열도록 구조를 바꿔야 하는 C++ 수정이고 이 환경에서 검증할 수 없다 |
| HEADER_TO_REMOVE에 "redecode_" 추가 | 채택 불가 | Cleanup_Test_Environment는 Test_LLR의 마지막 줄(9092행)에서 불리고, redecode 파일을 읽는 Gather는 Test_LLR이 돌아온 뒤에 불린다(_Build_Initial_Partial_Pool 9380행, Rebuild_Partial_Pool 9467행, Run_Initial_Test의 Process_Uncors 7846행). Gather보다 먼저 지워져 Partial 풀이 항상 비게 된다 |
| Gather 직후 root가 전 rank 파일 삭제(Delete_Uncors 계열) | 동작하나 열세 | Delete_Uncors(1505행)는 root만 전 rank 폴더를 돌며 지우는 구조라 is_redecoded_uncor 인자를 더해야 한다. README 3.3.3의 "각 rank는 독립 작업 공간 사용"과 어긋나며, Gather에 이르기 전에 실행이 끊기면(MPI_Abort, 타임아웃) 다음 세션 재개 시가 아니라 같은 세션의 다음 실행에서 옛 파일이 남는다. 실행 전 자기 파일 삭제는 직전 실행이 어떻게 끝났든 이번 실행분만 남긴다 |
| Determine_Update_Decision 수정 | 열세 | is_initial에서 (True, OPTIMAL_MATRIX_FROM_CURRENT)를 돌려야 Set_Optimal_Matrix, target_group_indices 정리, Save_LLR_Matrix, "[Update optimal LLR matrix!]" 로그(9657~9677행)가 돈다. Rebuild만 빼려고 다른 UpdateMode를 만들면 9670~9677행의 분기와 Set_Current_Optimal_Matrix까지 손대야 한다. `not is_initial` 한 조건이 최소 변경이다 |

두 수정의 독립성은 다음과 같다.

- ㉮ 삭제(수정 1과 2)만 있고 `not is_initial`이 없으면: 초기 Full 테스트가 같은 매트릭스로 한 번 더 돌지만, 두 번째 실행 전에 파일이 지워지므로 Partial 수는 초기 실패 수와 같다. 아카이브도 같은 `Redecoded_uncors/{초기 매트릭스}/`에 덮어쓴다(2129~2131행 dest unlink). 남는 것은 Full 테스트 한 번의 시간 낭비다
- ㉯ `not is_initial`(수정 3)만 있고 삭제가 없으면: 새 세션이라 초기 Partial 수는 맞지만, 첫 Rebuild부터 초기 실패 seed 위에 이어쓰기되어 다시 누적된다. REDECODE multi-matrix의 섞임도 그대로 남는다
- ㉰ 따라서 누적을 끊는 것은 삭제이고, 조건은 중복 Full 테스트를 없애는 것이다. 둘 다 필요하다

## 3. 발견 목록

### 발견 1. [LOW] 태스크 문서 5장 ㉱ "결과는 같다"의 범위가 단일 매트릭스에 한정된다

- 위치: `20260922_dynamic_partial_redecode_accumulation.md` 39행
- 내용: REDECODE에서 INITIAL_MATRIX_IDX_LIST로 여러 매트릭스를 돌리면 두 번째 매트릭스부터 Input에 저장되는 uncor 내용이 달라진다. 수정 전에는 앞 매트릭스의 실패 seed가 섞였고, 수정 후에는 그 매트릭스의 실패분만 남는다(근거는 2장 관점 14의 흐름 ㉮~㉰). 이 변화는 REDECODE의 목적에 맞는 개선이지만 문서는 "결과는 같다"고만 적는다
- 처방: ㉱를 "RunDAOMode.REDECODE는 실행 전 삭제만 추가된다. 단일 매트릭스는 결과가 같고, INITIAL_MATRIX_IDX_LIST로 여러 매트릭스를 돌릴 때는 두 번째 매트릭스부터 앞 매트릭스의 실패 seed가 섞이지 않아 각 매트릭스가 정정하지 못한 uncor만 Input에 저장된다"로 다시 쓴다

### 발견 2. [LOW] 태스크 문서의 "수정 2건"과 표의 3행이 맞지 않는다

- 위치: 같은 문서 4행("로직 수정 2건"), 20행("## 3. 설계 (수정 2건)"), `5_DAO/_pm/TODO.md`의 진행 메모("수정 2건 적용")
- 내용: 표에는 Delete_Own_Uncors 인자 추가, Set_Test_Environment 삭제, Update_Optimal_LLR 조건의 3행이 있다. 1행은 2행을 위한 시그니처 확장이므로 뜻은 "삭제"와 "조건" 2건이 맞지만, 숫자만 보면 어긋난다
- 처방: 제목을 "설계 (수정 2건, 코드 변경 3곳)"으로 쓰거나, 표의 1행을 2행 안에 합쳐 "Delete_Own_Uncors에 is_redecoded_uncor 인자를 더하고 Set_Test_Environment에서 ... 지움"으로 2행으로 맞춘다

### 발견 3. [LOW] 7장 검증에서 N과 비교할 "초기 Full 실패 수"의 출처와 합산 단위를 적지 않았다

- 위치: 같은 문서 49행
- 내용: N(`[Initial Partial] Dynamic partial pool created: N fail uncors`)은 모든 채널의 합이다(9414~9419행 `sum(self.total_num_partial_uncors)`). 비교 대상인 초기 Full 실패 수는 채널마다 Print_Test_Result가 남기는 "(seed_errors/tests): X/Y"(7616~7621행)의 X이므로, 채널이 둘 이상이면 X를 채널별로 더해야 N과 같다. 제외 코어와 배분 0개 코어는 Gather_And_Archive_Uncors(2141~2148행)와 Run_ECC(7966~7972행)가 같은 기준으로 건너뛰므로 두 수의 정의는 같다
- 처방: "N이 초기 Full 테스트의 채널별 '(seed_errors/tests): X/Y'의 X를 모두 더한 값과 같고"로 다시 쓴다. M도 같은 방식으로 그 회차 Full 테스트의 X 합과 비교한다

## 4. 요약

담당 관점 14~16에서 코드 결함은 없다. 다섯 실행 모드와 HBF에서 새 elif와 `not is_initial`은 도달하지 않거나 기존 분기와 같은 파일을 지운다. 문서 정합 3건(LOW)만 남으며, 모두 태스크 문서의 서술 범위와 검증 절차의 정확도를 높이는 처방이다. 대안 넷은 채택한 방식보다 열세이거나 동작하지 않음을 코드 순서로 확인했다.
