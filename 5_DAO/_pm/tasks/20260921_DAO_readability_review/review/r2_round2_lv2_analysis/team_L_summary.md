# Round 2 팀 L 요약: 매트릭스 모델, 생성 모드, 설정

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 배정 관점: P10, P11, P12, P17, P18 / 배정 실마리: ㉯ ㉰ ㉵ ㉶ ㉷
> 워커 문서: [worker_L_1.md](worker_L_1.md) (유효성과 보정), [worker_L_2.md](worker_L_2.md) (구조 변경 모드와 인덱스), [worker_L_3.md](worker_L_3.md) (설정과 단일 row 경로)

핵심 질문의 답은 셋 다 "있다"이다. 유효성 규칙은 spec보다 느슨한 구멍이 다섯 개 있고, 구조 변경 모드 가운데 두 개가 헤더를 갱신하지 않으며, 설정 프리셋 세 개와 HBF 최적화 전체가 검증을 통과한 뒤 실행 첫 단계에서 죽는다.

---

## ㉮ 워커 결과 요약

발견 49건이다. 심각도별로 CRITICAL 4건, HIGH 13건, MEDIUM 19건, LOW 13건이다.

### CRITICAL (프로세스 중단이나 hang)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| 1 | CRITICAL | `Gen_LLR_Mode_HBF_SEQUENCE = [7, 8, 1, 2, 12]`의 다섯 값이 모두 `GenLLRMode`에 없다. HBF 최적화를 켜면 root가 stage 1의 `GenLLRMode(selected_mode).name`에서 `ValueError`를 내고 예외가 `Main`까지 올라가 `MPI_Abort`로 전체가 죽는다. 뜻을 담은 `GenLLRModeHBF` 열거형은 정의만 되고 읽는 자리가 없다 | [DAO_Config.py:134](5_DAO/SRC/DAO_Config.py#L134), 터지는 자리 [DAO_Main.py:8309](5_DAO/SRC/DAO_Main.py#L8309), 미사용 열거형 [DAO_Constants.py:43](5_DAO/SRC/DAO_Constants.py#L43) | `IS_HBF_OPT = True`, `init_n = 1`, `RUN_DAO_MODE = RUN_OPTIMIZATION` | [DAO_Config.py:134](5_DAO/SRC/DAO_Config.py#L134)를 `GenLLRModeHBF` 멤버로 다시 쓴다(`[40, 41, 10, 11, 60]` 꼴). 그리고 `Validate_Config`에 두 시퀀스의 원소가 `{m.value for m in GenLLRMode}`에 있는지 보는 검사를 더한다 | W3 (L3-2) |
| 2 | CRITICAL | `Initialize_Stage`가 `Set_Gen_Trial_LLR_Mode`를 [2263](5_DAO/SRC/DAO_Main.py#L2263)에서 먼저 부르고 `target_group_indices`를 [2265~2274](5_DAO/SRC/DAO_Main.py#L2265)에서 나중에 다시 만든다. 빈 목록 검사는 앞쪽에만 있어서, 목록이 비면 [2280](5_DAO/SRC/DAO_Main.py#L2280)의 `% len(...)`이 `ZeroDivisionError`를, [2296](5_DAO/SRC/DAO_Main.py#L2296)의 첨자가 `IndexError`를 낸다 | [DAO_Main.py:2263~2296](5_DAO/SRC/DAO_Main.py#L2263) | optimal 매트릭스의 그룹 수가 `INITIAL_TARGET_GROUP_IDX`(기본 1) 이하로 줄어드는 순간. GEN_INITIAL_GROUP이 stage 1에서 채택되어 1그룹이 되거나, DELETE_ROW가 `_Delete_Entire_Group`으로 그룹을 지워 1그룹이 되는 경우 | [2263](5_DAO/SRC/DAO_Main.py#L2263)의 `Set_Gen_Trial_LLR_Mode()` 호출을 [2274](5_DAO/SRC/DAO_Main.py#L2274) 다음으로 옮긴다. 옮기면 발견 6, 7, 12도 함께 낫는다. 목록 재설정 블록 끝에 빈 목록 방어(`if not new_target_indices: new_target_indices = [len(base_matrix.groups) - 1]`)를 둔다 | W2 (L2-1) |
| 3 | CRITICAL | GEN_SINGLE_ROW의 종료 플래그를 모든 rank가 각자 `Read_DAO_End_Flag()`로 읽는다. 본 루프는 root만 읽고 `_safe_bcast`로 전파한다. 배리어는 읽기 직전 한 번뿐이라 배리어 통과와 각 rank의 `open()` 사이에 사용자가 플래그 파일을 만들면 rank마다 판정이 갈리고 집단 통신 횟수가 어긋난다 | [DAO_Main.py:10055~10068](5_DAO/SRC/DAO_Main.py#L10055) | `RUN_DAO_MODE = GEN_SINGLE_ROW`로 여러 rank 실행 중 종료 플래그 파일 생성 | 10055~10068을 본 루프 관용구([DAO_Main.py:8071~8077](5_DAO/SRC/DAO_Main.py#L8071))로 다시 쓴다. root만 읽고 `_safe_bcast`로 전파한다 | W3 (L3-5) |
| 4 | CRITICAL | 2SD 빠른 설정 프리셋 3개(SIM_IDX 20, 21, 22)가 시작 직후 `MPI_Abort`로 죽는다. `ch_type = 3`인데 `num_fixed_errs`는 채널 2개분, `fixed_SCRs`와 `fixed_SERs`는 1개분이라 길이 검사에 걸린다. `Update_RefC_Configs`의 ch_type 3 분기가 이 두 배열을 채널 수만큼 다시 채우지 않는다 | [DAO_Config.py:65](5_DAO/SRC/DAO_Config.py#L65), [77](5_DAO/SRC/DAO_Config.py#L77), [86](5_DAO/SRC/DAO_Config.py#L86), 검사 [DAO_Main.py:9893](5_DAO/SRC/DAO_Main.py#L9893), 누락 [DAO_Main.py:433](5_DAO/SRC/DAO_Main.py#L433) | `python DAO_Main.py 20` (21, 22도 같음) | [DAO_Main.py:433](5_DAO/SRC/DAO_Main.py#L433)의 ch_type 3 분기에서 `fixed_SCRs`와 `fixed_SERs`를 `NUM_TARGET_CHANNELS` 길이로 맞춘다. 프리셋 쪽에서 길이를 맞추는 방법도 있으나, 세 분기가 같은 규칙을 쓰도록 `Update_RefC_Configs`에서 고치는 편이 재발을 막는다 | W3 (L3-1) |

### HIGH (틀린 결과를 내지만 프로세스는 계속됨)

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 | 지적 워커 |
|---|--------|------|------|----------|------|----------|
| 5 | HIGH | `Correct_LLR_Matrix`가 `Is_LLR_Valid` 통과를 보장하지 않는다. CSW 범위(C3), 8배수(C4), 같은 값 중복(C5)을 보정 대상에서 빼고 있어 spec 7.2의 "생성된 매트릭스가 `Is_LLR_Valid()` 통과"와 6.3의 자동 보정 약속이 깨진다 | [DAO_LLR_MATRIX.py:561](5_DAO/SRC/DAO_LLR_MATRIX.py#L561) | 실측: 그룹 CSW를 `[-1, 5000, 3]`으로 두고 `Correct_LLR_Matrix()`를 부르면 값이 그대로 남고 검증이 "CSW 5000 out of range"로 실패한다. `[-1, 400, 400, 200]`도 보정 뒤 "must be decreasing"으로 실패한다 | [DAO_LLR_MATRIX.py:585~599](5_DAO/SRC/DAO_LLR_MATRIX.py#L585)의 CSW 정렬 블록을 보정 블록으로 넓힌다. 순서는 ㉮ `MIN_CSW`~`MAX_CSW` 클램프, ㉯ `STEP_CSW` 배수 반올림, ㉰ 내림차순 정렬, ㉱ 앞 값과 같아진 항목을 `STEP_CSW`만큼 내리기다 | W1 (발견 2) |
| 6 | HIGH | restart 그룹의 row가 RW1~RW5, C1~C5, G3~G5를 전부 건너뛴다. 길이가 틀린 restart row도 유효로 판정된다 | `continue` 위치 [DAO_LLR_MATRIX.py:333](5_DAO/SRC/DAO_LLR_MATRIX.py#L333) | 실측: restart row의 `ch_th_values`를 길이 4(정상 16)로, `floor_flag`를 77로 바꿔도 `Is_LLR_Valid`가 `(True, "")`를 돌려준다. 저장하면 짧은 줄이 쓰이고 재읽기와 외부 디코더가 서로 다르게 해석한다 | [DAO_LLR_MATRIX.py:322~333](5_DAO/SRC/DAO_LLR_MATRIX.py#L322)의 restart 분기에서 `continue` 앞에 restart 전용 검사를 넣는다: `len(row.ch_th_values)`가 정상 길이와 같고 `floor_flag == -1`, `CSW == -1`인지 본다. spec 3.3에 R3, R4, R5로 적는다 | W1 (발견 3) |
| 7 | HIGH | restart 그룹 판정이 두 갈래(`restart_groups` 1 기준 목록, `is_group_restart` 플래그)라 어긋날 수 있고, 어긋나면 `Correct_LLR_Matrix`가 restart row를 조용히 망가뜨린다. 검증은 두 갈래의 OR을 보고 보정은 플래그만 본다 | 검증 [DAO_LLR_MATRIX.py:318~320](5_DAO/SRC/DAO_LLR_MATRIX.py#L318), 보정 [DAO_LLR_MATRIX.py:580](5_DAO/SRC/DAO_LLR_MATRIX.py#L580) | 실측: `restart_groups`에는 남기고 `is_group_restart`만 False로 두면 검증은 통과하고 보정은 `-1` 16개를 `min_value`인 `0` 16개로 깎는다. restart 표식이 사라진 매트릭스가 최적으로 남는다 | 발견 17의 처방(`_Rebuild_Restart_Header_From_Groups` 한 메서드로 통일)을 먼저 넣고, 회귀 방지로 `Is_LLR_Valid`에 "목록과 플래그가 같은 그룹 집합을 가리킨다"(G8)를 더한다 | W1 (발견 4) |
| 8 | HIGH | HBF 모드 보정이 dv_idx 0뿐 아니라 **모든 DV**의 TH를 0으로 지운다. 규칙 HBF1, 생성, 변이는 모두 dv_idx 0만 고정하므로 HBF 모드에서 DV 1 이상의 TH 탐색이 매 trial 무효가 된다. `HBF_OPT_TH_CONSTANT_VAL`을 0 이외로 두면 생성이 영구히 실패한다 | [DAO_LLR_MATRIX.py:641~642](5_DAO/SRC/DAO_LLR_MATRIX.py#L641) | 실측: `is_HBF_OPT=True`로 보정하면 `[1,28,9,5, 10,10,9,4, ...]`가 `[28,1,0,0, 10,10,0,0, ...]`가 되어 DV 4개 전부의 TH가 0이 된다 | 641~642의 덮어쓰기를 `HBF_immutable_col_range`가 가리키는 dv_idx 0 구간으로 한정하고, 상수값을 `HBF_OPT_TH_CONSTANT_VAL`에서 읽는다. 발견 1과 한 묶음으로 고친다(아래 교차 분석 ㉲) | W1 (발견 5) |
| 9 | HIGH | 헤더의 `num_group`과 그룹별 `num_row_each_group`을 실제 `groups`와 대조하지 않아 헤더와 본문이 어긋난 파일이 유효로 판정된다 | [DAO_LLR_MATRIX.py:279](5_DAO/SRC/DAO_LLR_MATRIX.py#L279), [431](5_DAO/SRC/DAO_LLR_MATRIX.py#L431) | 실측 ㉮ 실제 그룹 크기가 `[2, 1]`인데 헤더가 `[1, 2]`면 합이 같아 통과한다 ㉯ `num_group`을 99로 두고 배열을 99칸으로 채우면 실제 그룹이 3개여도 통과한다 | [279](5_DAO/SRC/DAO_LLR_MATRIX.py#L279)의 H2 뒤에 `num_group == len(self.groups)`(H6)를, 그룹 루프 안에 `len(groups[g]) == num_row_each_group[g]`(G7)를 넣는다. 발견 18(H7)도 같이 넣는다 | W1 (발견 6) |
| 10 | HIGH | `Set_Gen_Trial_LLR_Mode`가 낡은 `target_group_indices`로 타겟 그룹과 `max_modification_trial`을 정한다. 발견 2와 같은 순서 문제다 | 호출 [DAO_Main.py:2263](5_DAO/SRC/DAO_Main.py#L2263), 쓰는 쪽 [8316~8327](5_DAO/SRC/DAO_Main.py#L8316), [8404~8422](5_DAO/SRC/DAO_Main.py#L8404) | 직전 stage에서 그룹 수가 달라진 모든 경우. 8322가 실제 그룹 수를 넘는 인덱스를 집으면 8325~8327이 "마지막 그룹"으로 낮추므로 여러 stage 동안 타겟이 마지막 그룹에 붙어 있게 된다 | 발견 2의 처방(호출 순서 교체)으로 함께 낫는다 | W2 (L2-2) |
| 11 | HIGH | INSERT_RANDOM_GROUP, INSERT_MUTATED_GROUP, SPLIT_GROUP이 `self.target_group_indices`를 trial마다 누적해서 바꾼다. 매트릭스는 trial마다 optimal에서 새로 복사되는데 목록은 되돌아가지 않는다 | [2770~2785](5_DAO/SRC/DAO_Main.py#L2770), [3120~3131](5_DAO/SRC/DAO_Main.py#L3120), [3454~3460](5_DAO/SRC/DAO_Main.py#L3454) | 그룹 4개, `INITIAL_TARGET_GROUP_IDX=1`이면 목록은 `[1,2,3]`. SPLIT_GROUP stage에서 타겟이 g1이면 trial 5 뒤 목록이 `[1,7,8,6,5,4,3,2]`가 된다(모의 실행) | 세 자리의 목록 보정을 지우고, trial마다 바뀌는 목록은 `Gen_Trial_LLR`이 만드는 후보 매트릭스에만 실어 보낸다. 영구 상태는 `Initialize_Stage`의 stage 단위 재생성 한 곳에서만 만든다 | W2 (L2-3) |
| 12 | HIGH | ADJUST_ITERATION의 `Build_Adjusted_Iteration_Matrix`가 iteration을 재배치하면서 `header.restart_iter`를 갱신하지 않는다. 저장 파일의 restart 줄이 실제 위치와 어긋난다 | [DAO_Main.py:4604](5_DAO/SRC/DAO_Main.py#L4604), 재계산 루프 [4701~4727](5_DAO/SRC/DAO_Main.py#L4701) | restart 그룹이 하나 이상 있는 매트릭스로 ADJUST_ITERATION stage를 돌리면 항상. 함수 자신의 docstring 예시(4631~4636)가 이 경우를 보여 준다 | 4727 뒤에 발견 17의 `_Rebuild_Restart_Header_From_Groups(matrix)`를 부른다. 검증 쪽은 발견 18(H7)이 잡아 준다 | W2 (L2-4) |
| 13 | HIGH | REORDER_GROUP의 `max_modification_trial`이 필요한 trial 수보다 정확히 1 작다. 마지막 Round의 `Finalize_Reorder_Round`와 Final Verification이 실행되지 않는다 | [Set_Gen_Trial_LLR_Mode:8409~8412](5_DAO/SRC/DAO_Main.py#L8409) 대 [Init_Reorder_Group_Mode:4503~4509](5_DAO/SRC/DAO_Main.py#L4503) | REORDER_GROUP stage를 돌리면 항상 | 8409~8412를 4503~4509와 같은 식(`1 + trials_per_round + 1`, SD는 `1 + trials_per_round * 2 + 1`)으로 맞춘다. 두 자리가 같은 값을 따로 계산하므로 `Init_Reorder_Group_Mode`가 정한 값을 `Set_Gen_Trial_LLR_Mode`가 읽게 한 곳으로 모으는 편이 낫다 | W2 (L2-5) |
| 14 | HIGH | REORDER_GROUP의 iteration 등분이 restart 그룹까지 센 개수로 나눠 총 iteration이 줄어든다 | [Build_Reordered_Matrix:4918](5_DAO/SRC/DAO_Main.py#L4918), [5015](5_DAO/SRC/DAO_Main.py#L5015) | target 범위 안에 restart 그룹이 있는 매트릭스로 REORDER_GROUP 수행. `target_group_indices=[1,2,3]`이고 g2가 restart면 donor는 두 개인데 등분은 3으로 나눠 target 영역 iteration이 원래의 약 2/3로 줄어든다 | [4918](5_DAO/SRC/DAO_Main.py#L4918)의 `num_original_target_groups`를 `len(base_donor_pool)`로 바꾸고, [5015](5_DAO/SRC/DAO_Main.py#L5015)의 나머지(`total_iterations % 개수`)를 마지막 그룹에 얹어 총량을 보존한다 | W2 (L2-6) |
| 15 | HIGH | `Update_Configs`가 `Update_RefC_Configs`를 먼저, `Update_Exit_After_Run_Configs`를 나중에 부르는데 앞쪽이 뒤쪽이 정하는 `UNCOR_CONFIG.LOAD_UNCOR_MODE`를 읽는다. `ENABLE_LOAD_VECTOR=True`여도 `LEN_NO_PS`가 0, `NUM_LINES_PER_UNCOR`가 1로 남아 uncor 벡터 한 줄을 uncor 한 개로 세고 쪼갠다 | [DAO_Main.py:475~479](5_DAO/SRC/DAO_Main.py#L475), 읽는 자리 [442~447](5_DAO/SRC/DAO_Main.py#L442), 쓰는 자리 [414](5_DAO/SRC/DAO_Main.py#L414) | `ENABLE_LOAD_VECTOR = True`로 실행 | [DAO_Main.py:475~479](5_DAO/SRC/DAO_Main.py#L475)에서 `Update_Exit_After_Run_Configs`를 `Update_RefC_Configs`보다 앞으로 옮긴다 | W3 (L3-3) |
| 16 | HIGH | 코어 속도 테스트가 rank마다 다른 초기 시드로 돈다. 설명과 `SPEED_TEST_REFC_CONFIG.mode_init_seed`는 모든 프로세스가 같은 시드를 쓴다고 하는데, 인자 12번 자리에 `self.rank`가 들어가고 `mode_init_seed`를 읽는 자리가 없다. 서로 다른 프레임을 복호한 시간을 비교하므로 정상 코어가 느린 코어로 제외될 수 있다 | 설명 [DAO_Main.py:9022](5_DAO/SRC/DAO_Main.py#L9022), 인자 [6471](5_DAO/SRC/DAO_Main.py#L6471)과 [6494](5_DAO/SRC/DAO_Main.py#L6494), 설정 [DAO_Config.py:237](5_DAO/SRC/DAO_Config.py#L237) | 코어 속도 테스트를 켜고 실행 | [6471](5_DAO/SRC/DAO_Main.py#L6471)과 [6494](5_DAO/SRC/DAO_Main.py#L6494)의 `self.rank`를 `SPEED_TEST_REFC_CONFIG.mode_init_seed`로 바꾼다 | W3 (L3-4) |
| 17 | HIGH | GEN_SINGLE_ROW의 `candidates` 리스트가 `LLR_MATRIX` 객체 전체를 담은 채 끝없이 자란다(기본 `NUM_GEN_TRIALS` 1,000,000). `RANKING_UPDATE_INTERVAL`(기본 100)마다 전체 목록을 채널 수 곱하기 (1 + CSW 문턱 수)번 다시 정렬한다. root가 메모리 고갈로 죽으면 `MPI_Abort` 없이 통신이 멎어 전체가 매달린다 | [DAO_Main.py:10044](5_DAO/SRC/DAO_Main.py#L10044), [10139](5_DAO/SRC/DAO_Main.py#L10139), [10160~10164](5_DAO/SRC/DAO_Main.py#L10160) | `RUN_DAO_MODE = GEN_SINGLE_ROW`로 수만 trial 이상 실행 | 순위 갱신 뒤 `candidates`를 상위 `TOP_K`만 남기고 자른다. 후보 객체 대신 (FER, CSW, 행 값) 요약만 보관하고 저장 시점에만 매트릭스를 다시 만드는 방식이 더 낫다 | W3 (L3-6) |

### MEDIUM 19건과 LOW 13건

지면을 아끼기 위해 목록만 적는다. 각 항목의 재현 조건과 처방은 워커 문서의 발견 표에 있다.

- ㉮ MEDIUM (W1, [worker_L_1.md](worker_L_1.md) 2절): 발견 1(C5 문구와 `Mutate_CSW` 7167, 7173이 같은 값을 만듦), 7(`restart_iter` 값 정합성 미검사), 8(`max_iteration`이 검증 부수효과로만 생김), 9(`Gen_Trial_LLR`이 `ValueError`만 포착), 10(`Correct_Ch_Th_In_Row` 클램프의 길이 전제, 길이 1이면 조용히 전체 클램프), 11(입력 `Prime_ECC_3.0`이 RW2와 G2 위반, **Decision 등급**)
- ㉯ MEDIUM (W2, [worker_L_2.md](worker_L_2.md) 3절): L2-7(INSERT 계열이 `MAX_DECODING_ITERATION` 상한 미확인), L2-8(DELETE_ROW 다음 Round 후보를 옛 목록으로 생성), L2-9(ADJUST_ITERATION trial 수와 실제 target 개수가 다른 목록에서 계산), L2-10(`Initialize_Stage`의 restart 건너뛰기 루프가 실제 타겟 선택에 영향 없음)
- ㉰ MEDIUM (W3, [worker_L_3.md](worker_L_3.md) 4절): L3-7(`CSW_UPDATE_LIMIT_VALUE` 조건부 정의), L3-8(`CONFIGS` 3개 누락, 로그 기록에만 영향), L3-9(`INITIAL_MATRIX_IDX_LIST` 검사가 GEN_SINGLE_ROW를 통과시킴), L3-10(`INITIAL_TARGET_GROUP_IDX` 음수 통과), L3-11(stage 시간 제한 판정이 두 곳에서 10시간과 100시간으로 갈림), L3-12(`SINGLE_ROW_CONFIG` 4개 필드 미검증), L3-13(`Gen_LLR_Mode_SEQUENCE` 값 미검증), L3-14(`init_n`이 1, 2, 3이 아니면 진단 로그 없이 `comm.Abort`), L3-15(GEN_SINGLE_ROW와 HBF 병행을 막지 않음)
- ㉱ LOW: W1 발견 12(도달 불가 코드 다섯 자리), 13(`Deep_Copy`가 `input_LLR_matrix_file_path`를 원본 그대로 둠) / W2 L2-11(죽은 코드 3함수, 되살리면 optimal 오염), L2-12(`total_num_iterations` 타입 표기), L2-13(`num_row_each_group` dtype 미지정 3곳), L2-14(`Optional` 선언 뒤 None 확인 없는 8자리), L2-15(spec 5.11이 코드에 없는 제약을 적음) / W3 L3-16~L3-21(`_Read_Stop_Idx` 미사용, `Build_Single_Row_Matrix`의 `floor_flag` 기본값 0, 로그 문구, 미사용 설정 필드, 상속 고리를 끊는 대입, `TEST_MODE_DIR_NAME` 죽은 상수)

---

## ㉯ 팀 내 교차 분석

### 워커 결과가 서로를 보강한 자리

- ㉮ **발견 12와 발견 18의 짝**: W2가 "ADJUST_ITERATION이 `restart_iter`를 갱신하지 않는다"를 찾았고 W1이 "검증이 `restart_iter` 값을 보지 않는다"를 찾았다. 결함을 만드는 쪽과 잡지 못하는 쪽이 정확히 맞물린다. 합치면 "restart 그룹이 있는 매트릭스로 ADJUST_ITERATION stage를 돌리면 저장 파일이 조용히 깨지고 재읽기에서 restart 그룹이 다른 자리로 옮겨간다"가 된다. 둘 다 확정한다.
- ㉯ **발견 7과 W2 1-1절 ㉮의 짝**: W1은 `restart_groups` 목록과 `is_group_restart` 플래그가 어긋날 수 있다는 것을 실측으로 보였고, W2는 `restart_iter` 재빌드가 "플래그에서 만든다"(3320~3325, 5140~5150)와 "목록에서 만든다"(5635~5639, 5928~5933) 두 갈래로 갈려 있음을 코드에서 보였다. 같은 뿌리의 두 증상이다. 처방은 W2 쪽(`_Rebuild_Restart_Header_From_Groups` 한 메서드로 모으기)이 더 근본적이므로 그것을 먼저 넣고, W1의 G8 검사는 회귀 방지로 함께 넣는다.
- ㉰ **발견 9와 W2 1절 표의 짝**: W1이 제안한 H6(`num_group == len(groups)`)과 G7(그룹별 행 수)만으로는 W2가 찾은 `_create_reorder_test_matrix`의 `num_restart`, `restart_iter` 미갱신을 잡지 못한다. W1의 H7(restart 정합)까지 함께 넣어야 세 필드가 모두 덮인다.

### 처방이 서로 부딪히는 자리 (수리 순서 제약)

- ㉱ **발견 8(`max_iteration` 부수효과)의 처방 순서**: W1은 "`__init__`에 `max_iteration` 초기화를 넣어라"를 처방했다. 그런데 W2가 1-1절 ㉯에서 "REORDER와 ADJUST 두 모드는 `max_iteration`을 대입하지 않고 `Is_LLR_Valid`의 부수 대입에 기대고 있다"를 찾았다. 그러므로 부수 대입을 걷어내는 순서가 중요하다. ㉠ 먼저 `Build_Reordered_Matrix`(5157 뒤)와 `Build_Adjusted_Iteration_Matrix`(4727 뒤)에 명시 대입을 넣고 ㉡ 그 다음에 `__init__` 초기화를 넣는다. 순서를 뒤집으면 두 모드가 낡은 `max_iteration`으로 돈다.
- ㉲ **발견 1과 발견 8의 묶음**: 지금 HBF 최적화는 발견 1 때문에 stage 1에 닿지 못한다. 그래서 발견 8(HBF 보정이 모든 DV의 TH를 0으로 지움)이 지금까지 드러나지 않았다. 발견 1만 고치면 발견 8이 곧바로 살아나 HBF 탐색이 매 trial 무효가 된다. 두 건을 한 묶음으로 고친다.

### 반박되거나 심각도가 바뀐 것

Round 1의 실마리 가운데 네 건이 확인 결과 사실과 달랐다. 워커끼리 같은 자리를 다르게 판단한 경우는 없었다.

- ㉳ 실마리 ㉶ "`Set_CSW_Update_Limit` 미호출": **반박된다.** W3이 [DAO_Main.py:3785](5_DAO/SRC/DAO_Main.py#L3785) → [7098](5_DAO/SRC/DAO_Main.py#L7098) → [8285](5_DAO/SRC/DAO_Main.py#L8285) 호출 사슬을 확인했다. 실제 위험은 `CSW_UPDATE_LIMIT_VALUE`의 조건부 정의(L3-7, MEDIUM)로 좁혀진다.
- ㉴ 실마리 ㉳ "`TEST_MODE_DIR_NAME` FULL 누락으로 KeyError": **반박된다.** 이 상수를 읽는 자리가 없어 죽은 상수다(L3-21). 최종 판단은 팀 T에 맡긴다.
- ㉵ 실마리 ㉵ "`current_target_idx` 생성 순서로 `AttributeError`": **반박된다.** `Init_Reorder_Group_Mode`는 `Initialize_Stage` 2299~2301 한 곳에서만 불리고 속성 생성(2277~2280)보다 뒤다. 다만 W2가 그 자리에서 더 큰 문제를 찾았다. `current_target_idx`와 restart 건너뛰기 루프가 실제 타겟 선택에 아무 영향을 주지 않는다는 것이다(L2-10). 실제 타겟은 `Set_Gen_Trial_LLR_Mode` 8322~8323의 `current_target_group_idx`이고, 실제 건너뛰기는 8337~8343이 stage를 통째로 비우는 방식으로 따로 한다.
- ㉶ 실마리 ㉷ "`HBF_OPT_CONFIG.__init__` 부수효과": **범위가 좁혀진다.** W3이 전 소스를 grep해 `HBF_OPT_CONFIG()` 호출이 없음을 확인했다. `__init__`이 아예 돌지 않으므로 부수효과는 일어나지 않고, `IS_HBF_OPT`는 [DAO_Config.py:127](5_DAO/SRC/DAO_Config.py#L127)의 기본값과 `Update_RefC_Configs`의 하향 조정으로만 정해진다. 같은 실마리의 `CONFIGS` 누락은 확인되었으나 소비처가 로그 출력 하나뿐이라 MEDIUM으로 내린다.
- ㉷ 실마리 ㉰ "CSW 같은 값 금지 대 spec C5": **코드 쪽이 정본이다.** 삽입 경로([DAO_Main.py:2409~2440](5_DAO/SRC/DAO_Main.py#L2409))가 `next + STEP` ~ `prev - STEP`으로 엄격 감소를 강제하고, 같은 CSW는 뒤 row를 고를 수 없게 만들어 죽은 행이 된다. 고칠 자리는 spec 3.5 문구와 `Mutate_CSW`의 [7167](5_DAO/SRC/DAO_Main.py#L7167), [7173](5_DAO/SRC/DAO_Main.py#L7173) 두 줄이다(발견 표의 MEDIUM 1번).

### 팀 리더가 직접 재확인한 것

- ㉸ 발견 1: `GenLLRMode`에 7, 8, 1, 2, 12가 없고 `GenLLRModeHBF`가 의도했던 열거형(값 40, 41, 10, 11, 60, 0, 31, 21)임을 [DAO_Constants.py:24~51](5_DAO/SRC/DAO_Constants.py#L24)에서 확인했다.
- ㉹ 발견 2, 10, L2-10: `Initialize_Stage` [2263](5_DAO/SRC/DAO_Main.py#L2263)의 `Set_Gen_Trial_LLR_Mode()` 호출이 [2265~2274](5_DAO/SRC/DAO_Main.py#L2265)의 목록 재설정보다 앞이고, [2280](5_DAO/SRC/DAO_Main.py#L2280)이 `% len(self.target_group_indices)`임을 확인했다.

---

## ㉰ 미커버 영역

팀 L의 배정 관점 안에서 손이 닿지 않은 자리다. 다음 리뷰에서 다룬다.

- ㉮ 값만 바꾸고 헤더를 건드리지 않는 모드(`Gen_LLR_Mutate_Matrix`, `Gen_LLR_Regen_DV`, `Gen_LLR_Regen_Row`, `Gen_LLR_Swap_Row`, `Copy_Rows`)가 값 범위 규칙(C3, C4, RW3, RW4)을 지키는지. W1은 `Mutate_CSW` 한 곳만 확인했고 거기서 C5 위반을 찾았으므로 나머지도 볼 값이 있다
- ㉯ `_Load_External_Single_Row_Candidates`가 읽는 외부 후보 파일의 형식 검증과 실패 처리
- ㉰ `Get_Ref_C_Args`와 `Get_Ref_C_Args_For_Speed_Test`의 ECC_VER 두 분기, 모두 네 자리가 서로 같은 인자 순서를 쓰는지 전수 대조. W3은 L3-4에서 시드 한 자리만 짚었다
- ㉱ 멀티라운드 상태 dataclass(`ReorderState` 등)가 rank 사이에 bcast되는 정합. 팀 M 영역과 겹쳐 확인하지 않았다
- ㉲ spec 5절의 모드별 "변경 사항" 목록 전체와 코드의 대조. W2가 1절 표로 헤더 필드만 부분 대조했다

---

## ㉱ 매트릭스 모델에 필드를 하나 더할 때 손대야 하는 자리

SW 분기 필드를 `LLR_Header`나 `LLR_Row`에 넣을 다른 세션을 위한 통합 목록이다. 줄 번호는 커밋 `6e035e6` 기준이다. 세부 항목은 [worker_L_1.md](worker_L_1.md) 4절(`DAO_LLR_MATRIX.py` 안쪽)과 [worker_L_2.md](worker_L_2.md) 4절(`DAO_Main.py` 생성 모드 쪽)에 있다.

### 1. 먼저 고쳐 두면 손댈 자리가 줄어드는 것 (순서대로)

- 1. 죽은 코드 세 함수를 지운다: `_create_reorder_test_matrix`([6195](5_DAO/SRC/DAO_Main.py#L6195)), `_recalculate_iterations_for_reorder`([6118](5_DAO/SRC/DAO_Main.py#L6118)), `_is_reorder_candidate_better`([6018](5_DAO/SRC/DAO_Main.py#L6018)). 동작 변경이 없고 고칠 자리가 한 벌 줄어든다
- 2. 행 끝 열 개수 `4`를 상수로 뽑는다. 지금은 읽기([DAO_LLR_MATRIX.py:524~528](5_DAO/SRC/DAO_LLR_MATRIX.py#L524))와 쓰기([195~201](5_DAO/SRC/DAO_LLR_MATRIX.py#L195))가 서로를 모르는 채 숫자로만 맞춰져 있다. **이 파일에서 가장 깨지기 쉬운 자리다**
- 3. `LLR_Header(...)`([494~506](5_DAO/SRC/DAO_LLR_MATRIX.py#L494), 위치 인자 11개)와 `LLR_Row(...)`([535](5_DAO/SRC/DAO_LLR_MATRIX.py#L535), 위치 인자 6개)의 생성자 호출을 키워드 인자로 바꾼다. 필드를 중간에 끼워도 값이 밀리지 않는다
- 4. restart 헤더 재빌드를 `_Rebuild_Restart_Header_From_Groups(matrix)` 한 메서드로 뽑고 다섯 곳이 그것을 부르게 한다(발견 7, 12가 함께 낫는다)
- 5. 그룹 삽입과 삭제 뒤의 헤더 재계산도 `_Rebuild_Group_Header_From_Groups(matrix)` 하나로 모은다. `num_group`, `num_row_each_group`, `max_iteration`은 `matrix.groups`만 보면 다시 만들 수 있다

### 2. `LLR_Row`에 필드를 더할 때

| 갈래 | 자리 | 수 |
|------|------|-----|
| 모델과 파일 입출력 | dataclass 정의 [23~32](5_DAO/SRC/DAO_LLR_MATRIX.py#L23), 파일 읽기의 열 분해와 생성자 [520~537](5_DAO/SRC/DAO_LLR_MATRIX.py#L520), 파일 쓰기의 세 갈래 [176~201](5_DAO/SRC/DAO_LLR_MATRIX.py#L176) | 3 |
| 유효성 검사 | 행 루프 [335~382](5_DAO/SRC/DAO_LLR_MATRIX.py#L335), restart 행 분기 [322~333](5_DAO/SRC/DAO_LLR_MATRIX.py#L322), CSW 블록 [384~419](5_DAO/SRC/DAO_LLR_MATRIX.py#L384), iteration 블록 [421~429](5_DAO/SRC/DAO_LLR_MATRIX.py#L421) | 4 |
| 자동 보정 | 행 재배치와 정렬 키 [586~599](5_DAO/SRC/DAO_LLR_MATRIX.py#L586), 보정 제외 조건 [580](5_DAO/SRC/DAO_LLR_MATRIX.py#L580), 값 클램프 [603~645](5_DAO/SRC/DAO_LLR_MATRIX.py#L603) | 3 |
| `LLR_Row` 생성자 호출 | `DAO_Main.py` 2446, 2636, 2670, 2990, 3017, 3252, 3391, 3403, 3628, 5746, 8907, 10205 | 12 |
| 행 값을 dict로 담았다 되살리는 경로 | `Get_Copy_Row_Candidates`([4383~4387](5_DAO/SRC/DAO_Main.py#L4383)), `Get_Copy_Group_Candidates`([4429~4435](5_DAO/SRC/DAO_Main.py#L4429)), `Copy_Group` 되살리기([8905~8913](5_DAO/SRC/DAO_Main.py#L8905)), `_Load_External_Single_Row_Candidates`([4278~4366](5_DAO/SRC/DAO_Main.py#L4278)), 값 변이 두 함수([3472](5_DAO/SRC/DAO_Main.py#L3472), [3523](5_DAO/SRC/DAO_Main.py#L3523)) | 6 |
| 진단과 문서 | `_summarize_value`([DAO_Main.py:91~105](5_DAO/SRC/DAO_Main.py#L91)), `DAO_spec.md` 2.3 필드 표와 3장 규칙 표와 7장 체크리스트 | 2 |

`Build_Reordered_Matrix`, `Build_Adjusted_Iteration_Matrix`, `_Build_Deleted_Row_Matrix`, `_Build_Inserted_Restart_Matrix`는 기존 행 객체를 옮기거나 `Deep_Copy`(`copy.deepcopy`)에 기대므로 새 필드가 저절로 따라간다.

### 3. `LLR_Header`에 필드를 더할 때

| 갈래 | 자리 | 수 |
|------|------|-----|
| 모델과 파일 입출력 | dataclass 정의 [9~21](5_DAO/SRC/DAO_LLR_MATRIX.py#L9), 읽기 줄 순서 [476~492](5_DAO/SRC/DAO_LLR_MATRIX.py#L476), 헤더 생성자 [494~506](5_DAO/SRC/DAO_LLR_MATRIX.py#L494), 쓰기 줄 순서 [122~145](5_DAO/SRC/DAO_LLR_MATRIX.py#L122), 파생 속성 [539~547](5_DAO/SRC/DAO_LLR_MATRIX.py#L539) | 5 |
| 유효성 검사 | 헤더 블록 [275~291](5_DAO/SRC/DAO_LLR_MATRIX.py#L275) | 1 |
| 헤더를 다시 쓰는 생성 모드 | `DAO_Main.py` 2471, 2695~2738, 3056~3094, 3277, 3316~3325, 3430~3452, 3572~3580, 5106~5157, 4701~4727, 5542, 5616~5643, 5910~5937, 8918~8919 | 13 |
| 헤더를 읽기만 하는 자리 | `_Check_Header_Compatibility`([4261~4277](5_DAO/SRC/DAO_Main.py#L4261)), `_summarize_value`([91~105](5_DAO/SRC/DAO_Main.py#L91)), COPY_ROWS trial 수 계산([8361](5_DAO/SRC/DAO_Main.py#L8361)), 행 길이 계산 `num_parameter_each_set * num_dv` 다섯 자리(2623, 2856, 4292, 5888, 6267) | 4 |
| 문서 | `DAO_spec.md` 2.2 필드 표, 3장 H 규칙 표, 5장 모드별 "변경 사항" 목록 | 1 |

### 4. `LLR_MATRIX` 인스턴스 속성을 더할 때

- ㉮ 생성자 초기화 [36~84](5_DAO/SRC/DAO_LLR_MATRIX.py#L36). **빠뜨리면 `max_iteration`처럼 속성이 아예 없는 상태가 생긴다**(발견 8과 같은 사고)
- ㉯ 읽기에서 채우기 [539~547](5_DAO/SRC/DAO_LLR_MATRIX.py#L539)
- ㉰ 복사 정책 `Deep_Copy` [234~261](5_DAO/SRC/DAO_LLR_MATRIX.py#L234). `copy.deepcopy`가 자동으로 복사하므로 **따라가면 안 되는 값일 때만** 초기화를 넣는다. 조용히 따라가는 것이 기본 동작이라는 점이 함정이다
- ㉱ 파일 이름에 들어가면 `Get_LLR_Matrix_File_Name` [263](5_DAO/SRC/DAO_LLR_MATRIX.py#L263)과 `Save_Matrix` [549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549)

### 5. 설정 항목이 함께 늘어날 때

[worker_L_3.md](worker_L_3.md) 5절에 15개 자리가 있다. 요점은 ㉮ `CONFIGS`([DAO_Config.py:406](5_DAO/SRC/DAO_Config.py#L406))에 더하기, ㉯ 클래스 본문에서 다른 설정을 읽어 값을 계산하지 않고 `Update_*` 함수에서 채우기, ㉰ 조건부 정의(`if 플래그: 필드 = 값`)를 쓰지 않기, ㉱ `MAX_TRIAL` 필드는 `Validate_Config` 목록과 `MODE_MAX_TRIAL_MAP` 양쪽에 넣기다.
