# Round 2 팀 L 워커 1: 유효성 규칙과 자동 보정 (관점 P10, 실마리 ㉰)

- 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
- 작성: 2026-09-21
- 확인 범위
  - ㉮ [DAO_LLR_MATRIX.py](5_DAO/SRC/DAO_LLR_MATRIX.py) 645줄 전체
  - ㉯ [DAO_spec.md](5_DAO/DAO_spec.md) 3장(유효성 규칙)과 6.3절(자동 보정), 7.2절(유효성 보장)
  - ㉰ [DAO_Main.py](5_DAO/SRC/DAO_Main.py)의 보정과 검증 호출부: `Gen_Trial_LLR` 1950~2032, `Is_Current_LLR_Valid` 2474~2497, `Validate_LLR_Matrix` 9902~9915, `Build_Single_Row_Matrix` 10192~10230, `Mutate_CSW` 7100~7180, `Correct_Ch_Th_In_Row` 호출부 783, restart 그룹 유지 코드 2697~2738, 3059~3094, 3320~3325, 3442~3452, 5622~5640, 5918~5934, 6230~6320
  - ㉱ 실제 입력 파일 3개를 읽고 다시 써서 대조 (읽기 전용, 출력은 스크래치 디렉토리)
- 실행 검증: Python 3.11 단일 프로세스로 `DAO_LLR_MATRIX` 를 직접 import 해 실측했다. 실측 결과에는 "실측" 이라고 표시했다.

---

## 1절. spec 3장 대 `Is_LLR_Valid` 대조표

검증 본체는 [Is_LLR_Valid](5_DAO/SRC/DAO_LLR_MATRIX.py#L266) 266~449줄이다.

### 1.1 spec에 있는 규칙

| 규칙 | spec 내용 | 코드 구현 위치 | 일치 | 비고 |
|------|----------|---------------|------|------|
| H1 | `num_restart == len(restart_iter)` | [276~278](5_DAO/SRC/DAO_LLR_MATRIX.py#L276) | 일치 | |
| H2 | `num_group == len(num_row_each_group)` | [279~281](5_DAO/SRC/DAO_LLR_MATRIX.py#L279) | 일치 | `len(self.groups)` 와는 대조하지 않는다 (발견 6) |
| H3 | `num_group == len(type_each_group)` | [282~284](5_DAO/SRC/DAO_LLR_MATRIX.py#L282) | 일치 | |
| H4 | `len(max_value) == num_parameter_each_set` | [285~287](5_DAO/SRC/DAO_LLR_MATRIX.py#L285) | 일치 | 보정은 이 검사보다 먼저 돈다 (발견 12) |
| H5 | `len(min_value) == num_parameter_each_set` | [288~290](5_DAO/SRC/DAO_LLR_MATRIX.py#L288) | 일치 | |
| G1 | 그룹이 비어있지 않음 | [300~302](5_DAO/SRC/DAO_LLR_MATRIX.py#L300) | 일치 | |
| G2 | `iter_start == 이전 그룹 iter_end + 1` | [305~312](5_DAO/SRC/DAO_LLR_MATRIX.py#L305) | 일치 | restart 그룹의 `continue` 보다 앞에서 `previous_group_end` 를 갱신하므로 restart 를 낀 배치에서도 성립 (실측) |
| G3 | 그룹 내 모든 row 의 `iter_start` 동일 | [421~423](5_DAO/SRC/DAO_LLR_MATRIX.py#L421) | 느슨 | restart 그룹은 `continue` 로 건너뛴다 |
| G4 | 그룹 내 모든 row 의 `iter_end` 동일 | [424~426](5_DAO/SRC/DAO_LLR_MATRIX.py#L424) | 느슨 | 위와 같음 |
| G5 | `iter_end >= iter_start` | [427~429](5_DAO/SRC/DAO_LLR_MATRIX.py#L427) | 느슨 | 위와 같음. restart 는 R2 가 같은 값을 요구하므로 실질 손실은 없다 |
| G6 | 총 행 수 == `sum(num_row_each_group)` | [431~434](5_DAO/SRC/DAO_LLR_MATRIX.py#L431) | 일치 | 합만 보고 그룹별 배분은 보지 않는다 (발견 6) |
| R1 | restart 그룹은 row 1개 | [322~325](5_DAO/SRC/DAO_LLR_MATRIX.py#L322) | 일치 | |
| R2 | restart 그룹의 `iter_start == iter_end` | [327~332](5_DAO/SRC/DAO_LLR_MATRIX.py#L327) | 일치 | |
| RW1 | `len(ch_th_values) == num_parameter_each_set * num_dv` | [339~341](5_DAO/SRC/DAO_LLR_MATRIX.py#L339) | 느슨 | restart 그룹은 건너뛴다 (발견 3) |
| RW2 | `floor_flag == -1` | [344~346](5_DAO/SRC/DAO_LLR_MATRIX.py#L344) | 느슨 | restart 그룹은 건너뛴다. 새 입력 파일은 이 규칙을 위반한다 (발견 13) |
| RW3 | CH 값 >= 0 | [361~363](5_DAO/SRC/DAO_LLR_MATRIX.py#L361) | 느슨 | restart 그룹은 건너뛴다 |
| RW4 | TH 값 >= 0 | [365~367](5_DAO/SRC/DAO_LLR_MATRIX.py#L365) | 느슨 | restart 그룹은 건너뛴다 |
| RW5 | TH 값 내림차순 | [370~372](5_DAO/SRC/DAO_LLR_MATRIX.py#L370) | 일치 | `_is_non_increasing` 은 같은 값을 허용한다 (spec 과 같음) |
| C1 | 그룹 첫 row 의 `CSW == -1` | [386~388](5_DAO/SRC/DAO_LLR_MATRIX.py#L386) | 느슨 | restart 그룹은 건너뛴다 |
| C2 | 그룹 내 `CSW == -1` 인 row 가 정확히 1개 | [389~392](5_DAO/SRC/DAO_LLR_MATRIX.py#L389) | 느슨 | restart 그룹은 건너뛴다 |
| C3 | `MIN_CSW(8) <= CSW <= MAX_CSW(1408)` | [399~403](5_DAO/SRC/DAO_LLR_MATRIX.py#L399) | 일치 | 보정 대상이 아니다 (발견 2) |
| C4 | `CSW % STEP_CSW(8) == 0` | [406~410](5_DAO/SRC/DAO_LLR_MATRIX.py#L406) | 일치 | 보정 대상이 아니다 (발견 2) |
| C5 | CSW 내림차순 (non-increasing) | [413~417](5_DAO/SRC/DAO_LLR_MATRIX.py#L413) | **코드가 더 엄격** | 코드는 `prev_CSW <= current_CSW` 를 실패로 보아 같은 값을 금지한다 (발견 1) |
| HBF1 | `is_HBF_OPT` 일 때 dv_idx 0 의 TH 는 모두 `HBF_OPT_TH_CONSTANT_VAL` | [375~382](5_DAO/SRC/DAO_LLR_MATRIX.py#L375) | 일치 | 보정은 이보다 넓게 동작한다 (발견 5) |
| HBF2 | `max_iteration <= HBF_MAX_ITERATION` | [442~447](5_DAO/SRC/DAO_LLR_MATRIX.py#L442) | 일치 | 이 직전 441줄에서 `self.max_iteration` 을 대입한다 (발견 8) |

### 1.2 spec에는 없고 코드에만 있는 검사

| 코드 위치 | 검사 내용 | 판정 |
|-----------|----------|------|
| [354~356](5_DAO/SRC/DAO_LLR_MATRIX.py#L354) | DV 세그먼트 길이 == `num_parameter_each_set` | 도달 불가. RW1 을 통과하면 슬라이스 길이는 항상 같다 |
| [437~439](5_DAO/SRC/DAO_LLR_MATRIX.py#L437) | groups 가 비었거나 마지막 그룹이 빈 경우 | spec 3.2 에 G7 로 적어 두는 것이 좋다 |
| [441](5_DAO/SRC/DAO_LLR_MATRIX.py#L441) | `self.max_iteration` 대입 | 검사가 아니라 상태 변경이다 (발견 8) |

### 1.3 spec에도 코드에도 없어 빠진 검사

| 제안 규칙 | 내용 | 근거 |
|-----------|------|------|
| H6 | `num_group == len(self.groups)` | 발견 6 |
| H7 | `restart_iter` 와 실제 restart 그룹의 `iter_start` 집합이 같고 `num_restart` 가 그 개수와 같음 | 발견 7 |
| G7 | `len(groups[g]) == num_row_each_group[g]` (그룹별 배분) | 발견 6 |
| G8 | `restart_groups` 목록과 `is_group_restart` 플래그가 같은 그룹 집합을 가리킴 | 발견 4 |
| R3, R4, R5 | restart row 의 길이, `floor_flag == -1`, `CSW == -1` | 발견 3 |

---

## 2절. 발견

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|----------|------|
| 1 | MEDIUM | C5 를 코드는 엄격 감소로, spec 은 같은 값 허용으로 적는다. `Mutate_CSW` 는 같은 값을 만들어 스스로 검증을 깬다 | [DAO_LLR_MATRIX.py:413](5_DAO/SRC/DAO_LLR_MATRIX.py#L413), [DAO_Main.py:7167](5_DAO/SRC/DAO_Main.py#L7167), [DAO_Main.py:7173](5_DAO/SRC/DAO_Main.py#L7173) | MUTATE_CSW 모드, 대상 그룹에 row 3개 이상, 선택된 row 의 새 CSW 가 앞 row 의 CSW 를 넘어서는 경우. 7167 이 `(prev_row.CSW // STEP_CSW) * STEP_CSW` 로 되돌리는데 앞 값이 이미 8의 배수라 결과가 앞 값과 같아진다 | **코드(엄격 감소)를 정본으로 삼는다.** 7167 을 `prev_row.CSW - STEP_CSW`, 7173 을 `next_row.CSW + STEP_CSW` 로 바꾸고, 그 값이 `MIN_CSW`~`MAX_CSW` 를 벗어나면 그 row 의 변이를 건너뛴다. `DAO_spec.md` 3.5 C5 의 "내림차순 (non-increasing)" 을 "엄격 내림차순 (같은 값 금지, row 1부터)" 로, 에러 메시지 열을 "CSW values must be decreasing" 으로 고친다 |
| 2 | HIGH | `Correct_LLR_Matrix` 가 `Is_LLR_Valid` 통과를 보장하지 않는다. spec 7.2 의 "생성된 매트릭스가 `Is_LLR_Valid()` 통과" 와 6.3 의 자동 보정 약속이 깨진다 | [DAO_LLR_MATRIX.py:561](5_DAO/SRC/DAO_LLR_MATRIX.py#L561) | 실측: 그룹 CSW 를 `[-1, 5000, 3]` 로 두고 `Correct_LLR_Matrix()` 호출 → 값이 그대로 남고 검증이 "CSW 5000 out of range" 로 실패. `[-1, 400, 400, 200]` 도 보정 뒤 "must be decreasing" 으로 실패 | 585~599 줄의 CSW 정렬 블록을 보정 블록으로 넓힌다. 순서는 ㉮ `MIN_CSW`~`MAX_CSW` 로 클램프, ㉯ `STEP_CSW` 배수로 반올림, ㉰ 내림차순 정렬, ㉱ 앞 값과 같아진 항목을 `STEP_CSW` 씩 내려 중복을 없애고 `MIN_CSW` 아래로 내려가면 그 row 를 만든 모드를 실패로 되돌린다. 보정 내역은 기존 `correct_msg` 에 같은 형식으로 덧붙인다 |
| 3 | HIGH | restart 그룹의 row 가 RW1~RW5, C1~C5, G3~G5 를 전부 건너뛴다. 길이가 틀린 restart row 도 유효로 판정된다 | [DAO_LLR_MATRIX.py:333](5_DAO/SRC/DAO_LLR_MATRIX.py#L333) 의 `continue` | 실측: restart row 의 `ch_th_values` 를 길이 4(정상 16)로, `floor_flag` 를 77 로 바꾸어도 `Is_LLR_Valid` 가 `(True, "")` 를 돌려준다. 그 매트릭스를 저장하면 [Build_LLR_Matrix_Output_Lines](5_DAO/SRC/DAO_LLR_MATRIX.py#L92) 가 짧은 줄을 쓰고, 그 파일은 `Read_Input_LLR_Matrix` 와 외부 디코더가 서로 다르게 해석한다 | 322~333 의 restart 분기에서 `continue` 앞에 restart 전용 검사를 넣는다: `len(row.ch_th_values) == h.num_parameter_each_set * h.num_dv`, `row.floor_flag == -1`, `row.CSW == -1`, `np.all(row.ch_th_values == -1)`. spec 3.3 에 R3, R4, R5 로 추가한다 |
| 4 | HIGH | restart 그룹 판정이 두 갈래라 어긋날 수 있고, 어긋나면 `Correct_LLR_Matrix` 가 restart row 를 조용히 망가뜨린다 | 검증은 목록과 플래그의 OR: [DAO_LLR_MATRIX.py:318~320](5_DAO/SRC/DAO_LLR_MATRIX.py#L318). 보정은 플래그만: [DAO_LLR_MATRIX.py:580](5_DAO/SRC/DAO_LLR_MATRIX.py#L580) | 실측: `restart_groups` 에는 남기고 `is_group_restart` 만 False 로 두면 ㉮ 검증은 목록을 보고 restart 로 판정해 통과하고 ㉯ 보정은 플래그를 보고 일반 row 로 다뤄 `-1` 16개를 `min_value` 인 `0` 16개로 깎는다. ㉰ 그 뒤 검증은 또 통과한다. restart 표식이 사라진 매트릭스가 유효한 최적해로 남는다. 어긋남을 만드는 코드로는 [_create_reorder_test_matrix](5_DAO/SRC/DAO_Main.py#L6195)(재배열 영역 안의 기존 restart 그룹을 `restart_groups` 에 다시 넣지 않는다. 현재는 호출처가 없는 죽은 코드)가 있고, 새 모드를 붙일 때 같은 실수가 나기 쉽다 | 판정 창구를 하나로 만든다. ㉮ `is_group_restart` 를 유일한 정본으로 선언하고 ㉯ `LLR_MATRIX` 에 `Rebuild_Restart_Groups(self)` 를 추가해 플래그에서 `restart_groups` 와 `header.restart_iter`, `header.num_restart` 를 한 번에 다시 만든다 ㉰ 구조를 바꾸는 모드는 인덱스를 손으로 옮기는 대신 이 함수를 부른다 ㉱ `Is_LLR_Valid` 에 G8 로 "`restart_groups` == 플래그가 True 인 그룹의 1-based 목록" 을 넣는다 ㉲ 318~320 의 OR 을 플래그 단독 판정으로 바꾼다 |
| 5 | HIGH | HBF 모드 보정이 dv_idx 0 뿐 아니라 **모든 DV** 의 TH 를 0 으로 지우고, 상수를 0 이외로 두면 생성이 영구히 실패한다 | [DAO_LLR_MATRIX.py:641~642](5_DAO/SRC/DAO_LLR_MATRIX.py#L641) | 실측: `is_HBF_OPT=True` 로 보정하면 `[1,28,9,5, 10,10,9,4, ...]` 가 `[28,1,0,0, 10,10,0,0, ...]` 가 되어 DV 4개 전부의 TH 가 0 이 된다. 규칙 HBF1([375](5_DAO/SRC/DAO_LLR_MATRIX.py#L375)), 생성([DAO_Main.py:4005](5_DAO/SRC/DAO_Main.py#L4005), [DAO_Main.py:4143](5_DAO/SRC/DAO_Main.py#L4143)), 변이([DAO_Main.py:7066](5_DAO/SRC/DAO_Main.py#L7066))는 모두 dv_idx 0 만 고정한다. 그래서 HBF 모드에서 DV 1 이상의 TH 탐색이 매 trial 무효가 된다. 또 `HBF_OPT_TH_CONSTANT_VAL` 을 3 으로 바꾸면 보정 직후 검증이 "expected all 3, got [0, 0]" 로 항상 실패한다(실측) | **Decision 등급.** 의도가 "maxDv 만 고정" 이면 641~644 를 `if self.is_HBF_OPT and dv_idx == 0: segment[self.ch_length:] = HBF_OPT_CONFIG.HBF_OPT_TH_CONSTANT_VAL` 과 그 외에는 내림차순 정렬로 고친다. 의도가 "HBF 는 TH 전부 0" 이면 반대로 HBF1, 4005, 4143, 7066 을 전체 DV 로 넓히고 spec 3.6 을 고친다. 어느 쪽이든 상수는 `HBF_OPT_TH_CONSTANT_VAL` 하나만 쓰고 리터럴 `0` 을 없앤다 |
| 6 | HIGH | 헤더의 그룹 개수와 그룹별 행 수가 실제 `groups` 와 달라도 통과한다 | [DAO_LLR_MATRIX.py:279](5_DAO/SRC/DAO_LLR_MATRIX.py#L279), [DAO_LLR_MATRIX.py:431](5_DAO/SRC/DAO_LLR_MATRIX.py#L431) | 실측 ㉮ 실제 그룹 크기가 `[2, 1]` 인데 헤더가 `[1, 2]` 면 합이 같아 통과한다 ㉯ `num_group` 을 99 로 두고 `num_row_each_group`, `type_each_group` 을 99칸으로 채우면 실제 그룹이 3개여도 통과한다. 둘 다 저장 파일의 헤더와 본문이 어긋나서 재읽기와 외부 디코더가 다른 그룹 경계를 본다 | 279 의 H2 뒤에 `if h.num_group != len(self.groups): return False` 를 넣고, 294 의 그룹 루프 안 G1 검사 다음에 `if len(group) != int(h.num_row_each_group[g_idx]): return False` 를 넣는다. spec 3.1 에 H6, 3.2 에 G7 로 적는다 |
| 7 | MEDIUM | `header.restart_iter` 가 실제 restart 그룹의 iteration 과 달라도 통과한다 | [DAO_LLR_MATRIX.py:276](5_DAO/SRC/DAO_LLR_MATRIX.py#L276) 가 길이만 본다 | 실측: `restart_iter` 를 `[999]` 로 바꿔도 통과. 읽기는 `iter_start in restart_iter` 로 restart 를 판정하므로([DAO_LLR_MATRIX.py:530](5_DAO/SRC/DAO_LLR_MATRIX.py#L530)) 저장했다가 다시 읽으면 restart 그룹이 사라지거나 엉뚱한 그룹이 restart 로 표시된다. 갱신을 빠뜨리는 코드로 [_recalculate_group_iterations](5_DAO/SRC/DAO_Main.py#L3320) 가 `restart_iter` 만 다시 만들고 `num_restart` 는 손대지 않는다 | 발견 4 의 `Rebuild_Restart_Groups` 로 한 군데에서 만들게 하고, `Is_LLR_Valid` 에 H7 을 추가한다. `_recalculate_group_iterations` 의 3320~3325 도 그 함수 호출로 바꾼다 |
| 8 | MEDIUM | `max_iteration` 이 `__init__` 에 없고 검증의 부수효과로만 생긴다 | 대입은 [DAO_LLR_MATRIX.py:441](5_DAO/SRC/DAO_LLR_MATRIX.py#L441), 읽기는 [DAO_Main.py:1809](5_DAO/SRC/DAO_Main.py#L1809), [DAO_Main.py:1842](5_DAO/SRC/DAO_Main.py#L1842), [DAO_Main.py:2862](5_DAO/SRC/DAO_Main.py#L2862) | 실측: 생성 직후와 `Deep_Copy` 직후 모두 `hasattr(matrix, "max_iteration")` 이 False 다. 대입은 성공 경로 끝에서만 일어나므로 검증이 중간에 실패하면 이전 값이 남는다. 지금은 `Setup` → `Initialize_LLR_Matrix` → `Validate_LLR_Matrix` 순서라 사고가 나지 않지만, 검증을 부르지 않는 경로를 새로 만들면 `Gather_Ref_C_Results` 가 root 에서 AttributeError 로 죽는다. `self.initial_LLR_matrix` 는 끝까지 이 속성을 갖지 않는다 (`Update_Current_LLR` 이 `Deep_Copy` 로 사본을 만들고 검증은 사본에만 걸리기 때문) | ㉮ `__init__` 에 `self.max_iteration: int = 0` 을 넣는다 ㉯ `Read_Input_LLR_Matrix` 끝(540줄 뒤)에서 `self.max_iteration = self.groups[-1][-1].iter_end` 로 채운다 ㉰ 441 의 대입을 없애고 `last_iteration = self.groups[-1][-1].iter_end` 를 지역 변수로 읽어 HBF2 만 검사하게 바꾼다 (검사 함수가 상태를 바꾸지 않게 한다) ㉱ 구조를 바꾸는 모드가 이미 `max_iteration` 을 직접 갱신하고 있으므로 동작은 그대로 유지된다 |
| 9 | MEDIUM | `Gen_Trial_LLR` 이 `Correct_LLR_Matrix` 의 `ValueError` 만 잡고 생성 함수의 예외는 그대로 흘린다 | [DAO_Main.py:2000~2008](5_DAO/SRC/DAO_Main.py#L2000), 생성 분기는 [DAO_Main.py:1956~1991](5_DAO/SRC/DAO_Main.py#L1956) | `Gen_LLR_*` 안에서 IndexError 나 numpy TypeError 가 나면 root 만 `if self.is_root:` 블록을 빠져나가고 worker 는 2017 의 `_safe_bcast` 에서 기다린다. 다만 모듈 말미 `Main()` 의 `except Exception` 이 `MPI_Abort` 를 통해 `comm.Abort` 를 부르므로 hang 대신 세션 전체가 중단된다. 즉 "한 trial 실패" 로 끝났어야 할 일이 "세션 중단" 이 된다 | 1956~2008 을 하나의 `try` 로 묶고 `except Exception as e:` 로 받아 `self.generate_LLR_success = False` 로 만든 뒤 `traceback.format_exc()` 를 로그에 남긴다. `MPI_Abort` 로 끝내야 할 예외(설정 오류)는 지금처럼 생성 함수 안에서 `self.MPI_Abort` 를 직접 부르므로 이 변경에 영향받지 않는다 |
| 10 | MEDIUM | `Correct_Ch_Th_In_Row` 의 클램프가 세그먼트 길이와 `max_value` 길이가 같다고 전제한다 | [DAO_LLR_MATRIX.py:626~627](5_DAO/SRC/DAO_LLR_MATRIX.py#L626) | 실측 ㉮ `max_value` 길이가 1 이면 numpy 브로드캐스트로 **조용히** 모든 파라미터를 같은 경계로 깎는다 (`[1,28,9,5,...]` → `[2,1,2,2,...]`) ㉯ 길이가 3 처럼 안 맞으면 `ValueError: operands could not be broadcast together` 가 나서 `Gen_Trial_LLR` 이 trial 실패로 처리한다. 앞의 조용한 경우가 위험하다. H4, H5 는 보정보다 나중에 돈다 | 614 의 길이 검사 옆에 `if len(self.header.max_value) != expected_param or len(self.header.min_value) != expected_param: raise ValueError(...)` 를 넣는다 (`expected_param = self.header.num_parameter_each_set`) |
| 11 | MEDIUM | 입력 디렉토리 `Prime_ECC_3.0` 의 매트릭스가 RW2 를 위반한다 | [DAO_LLR_MATRIX.py:344](5_DAO/SRC/DAO_LLR_MATRIX.py#L344) | 실측: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt` 를 `init_n=3` 으로 읽고 검증하면 "Group 0 Row 0 invalid floor_flag 0" 으로 실패한다. 이 파일은 `floor_flag` 에 0 과 1 을 쓰고 `type_each_group` 에 20, 21 을 쓰며 `num_restart=0` 인데 일부 그룹이 `iter_start` 를 1 로 되돌린다(G2 도 위반). 이 디렉토리는 아직 git 에 들어가지 않은 새 입력이다 | **Decision 등급.** SW 분기 필드를 넣는 세션과 규격을 맞춰야 한다. RW2 를 "`floor_flag` 가 허용 집합에 속함" 으로 넓히고, `floor_flag` 가 갈래를 가르는 값이면 G2 의 iteration 연속성도 갈래별로 따로 보도록 바꾼다. 결정 전에는 이 입력을 쓰지 않는다 |
| 12 | LOW | 도달하지 않거나 쓰이지 않는 코드 | [DAO_LLR_MATRIX.py:274](5_DAO/SRC/DAO_LLR_MATRIX.py#L274), [DAO_LLR_MATRIX.py:354](5_DAO/SRC/DAO_LLR_MATRIX.py#L354), [DAO_LLR_MATRIX.py:207](5_DAO/SRC/DAO_LLR_MATRIX.py#L207), [DAO_LLR_MATRIX.py:40](5_DAO/SRC/DAO_LLR_MATRIX.py#L40), [DAO_LLR_MATRIX.py:42](5_DAO/SRC/DAO_LLR_MATRIX.py#L42) | ㉮ 274 의 `output_msg = "[Validate error!] "` 는 모든 분기가 덮어써서 로그에 나타나지 않는다 ㉯ 354~356 의 DV 세그먼트 길이 검사는 RW1 통과 뒤 항상 참이다 ㉰ `Change_Max_Iteration` 은 저장소 전체에서 호출처가 없다 (`5_DAO/SRC`, `5_DAO/Util` 전수 grep) ㉱ `decoder_mode_str`, `HBF_max_iteration` 도 모듈 밖에서 읽히지 않는다 | ㉮ 274 를 지우고 각 메시지에 `"[Validate error!] "` 접두사를 붙이거나, 반환 직전에 한 번 붙인다 ㉯ 354~356 을 지운다 ㉰ `Change_Max_Iteration` 은 쓰지 않으면 지우고, `ADJUST_ITERATION` 모드가 직접 `iter_end` 를 만지는 대신 이 함수를 쓰게 할지 결정한다 ㉱ `decoder_mode_str` 과 `HBF_max_iteration` 은 남길 이유를 확인하고 없으면 지운다 |
| 13 | LOW | `Deep_Copy` 가 `input_LLR_matrix_file_path` 를 원본 값 그대로 둔다 | [DAO_LLR_MATRIX.py:238](5_DAO/SRC/DAO_LLR_MATRIX.py#L238) | 사본의 `LLR_matrix_file_name` 은 새 인덱스로 갱신되지만 `input_LLR_matrix_file_path` 는 원본 파일을 계속 가리킨다. 지금은 이 값을 읽는 곳이 없어 사고는 없지만 진단 로그를 붙이면 바로 오해를 만든다 | 238 다음 줄에 `new_matrix.input_LLR_matrix_file_path = ""` 를 넣거나, 이 속성을 지역 변수로 바꾸고 인스턴스에 남기지 않는다 |

### 2.1 배정 항목별 판정 요약

- ㉯ 실마리 ㉰ (C5 같은 값): **코드가 맞고 spec 문구가 틀렸다.** 같은 CSW 는 뒤 row 를 고를 수 없게 만들어 죽은 행이 되고, 삽입 경로([DAO_Main.py:2409~2440](5_DAO/SRC/DAO_Main.py#L2409))도 `next + STEP` ~ `prev - STEP` 으로 엄격 감소를 강제한다. 어긋난 곳은 spec 3.5 문구와 `Mutate_CSW` 의 7167, 7173 두 줄이다 (발견 1).
- ㉰ restart 판정 두 갈래: 어긋날 수 있고, 어긋나면 보정이 restart row 를 지운다 (발견 4). `continue` 가 RW1~RW5 와 C1~C5 를 무효화하는 것은 restart row 의 값이 모두 `-1` 이라 RW3, RW4 를 통과할 수 없기 때문이라 **설계 의도가 맞다**. 다만 지금은 "검사를 안 한다" 로만 되어 있어 restart row 전용 검사가 필요하다 (발견 3).
- ㉱ G2 와 `previous_group_end`: 갱신(314~315)이 restart 그룹의 `continue`(333)보다 **앞**이므로 restart 를 낀 배치에서도 연속성이 성립한다. 실측으로 확인했다 (restart 다음 그룹의 `iter_start` 를 4 로 틀면 "4 vs 2" 로 잡힌다). **문제 없음.**
- ㉲ `max_iteration` 부수효과: 발견 8. 지금 살아 있는 경로에서는 사고가 없지만 `__init__` 초기화가 없어 새 경로를 만들면 바로 AttributeError 가 된다.
- ㉳ `ch_length`, `th_length`: `__init__` 마지막 줄([DAO_LLR_MATRIX.py:84](5_DAO/SRC/DAO_LLR_MATRIX.py#L84))이 `Read_Input_LLR_Matrix` 를 반드시 부르므로 모든 인스턴스가 이 속성을 갖는다. `Deep_Copy` 는 `copy.deepcopy` 라 함께 복사된다. 파일 없이 매트릭스를 만드는 길 자체가 없다. **문제 없음** (다만 "생성자가 파일 입출력을 한다" 는 구조는 팀 R 의 가독성 처방과 맞물린다).
- ㉴ 보정 결과가 검증을 통과하는가: 통과를 보장하지 않는다 (발견 2). 세부 확인은 아래와 같다.
  - CSW 정렬은 `LLR_Row` 객체 단위로 재배치하므로([DAO_LLR_MATRIX.py:597~599](5_DAO/SRC/DAO_LLR_MATRIX.py#L597)) `ch_th_values` 와 CSW 의 짝은 **섞이지 않는다**. 문제 없음.
  - 같은 CSW 가 남으면 발견 1 의 엄격 조건에 걸린다. 실측으로 확인했다.
  - 범위를 벗어난 restart row 는 보정에서도 검증에서도 잡히지 않는다 (발견 3).
  - 보정은 `header.num_row_each_group`, `type_each_group`, `iter_start`, `iter_end` 를 건드리지 않으므로 이들과 어긋나게 만들지 않는다. 문제 없음.
- ㉵ `Correct_Ch_Th_In_Row` 클램핑 전제: 발견 10.
- ㉶ 왕복 일치: 3절에 결과를 적었다. 값은 보존되고 바이트는 다르다.
- ㉷ `Deep_Copy` 필드 대조: 3절. 누락 필드는 없다.
- ㉸ 생성 경로 예외 누출: 발견 9.

---

## 3절. `Deep_Copy` 필드 대조와 읽기 쓰기 왕복

### 3.1 `Deep_Copy` 필드 대조표

`Deep_Copy` 는 [DAO_LLR_MATRIX.py:234](5_DAO/SRC/DAO_LLR_MATRIX.py#L234) 에서 `copy.deepcopy(self)` 로 시작하므로 **인스턴스 속성 전부가 복사된다.** 실측으로 원본과 사본의 `__dict__` 키 집합이 같음을 확인했다 (양쪽 차집합 모두 공집합). 아래는 실제 인스턴스가 갖는 26개 속성과 그 처리다.

| 속성 | 만들어지는 곳 | `Deep_Copy` 처리 | 비고 |
|------|--------------|------------------|------|
| `init_n` | `__init__` [37](5_DAO/SRC/DAO_LLR_MATRIX.py#L37) | 복사 | |
| `is_HBF_OPT` | `__init__` [38~49](5_DAO/SRC/DAO_LLR_MATRIX.py#L38) | 복사 | |
| `decoder_mode_str` | `__init__` [40,44,48](5_DAO/SRC/DAO_LLR_MATRIX.py#L40) | 복사 | 모듈 밖에서 읽히지 않음 (발견 12) |
| `HBF_max_iteration` | `__init__` [42,46,50](5_DAO/SRC/DAO_LLR_MATRIX.py#L42) | 복사 | 모듈 밖에서 읽히지 않음 (발견 12) |
| `matrix_idx` | `__init__` [54](5_DAO/SRC/DAO_LLR_MATRIX.py#L54) | **재설정** [237](5_DAO/SRC/DAO_LLR_MATRIX.py#L237) | 인자가 None 이면 유지 |
| `groups` | `__init__` [56](5_DAO/SRC/DAO_LLR_MATRIX.py#L56), `Read_Input_LLR_Matrix` [537](5_DAO/SRC/DAO_LLR_MATRIX.py#L537) | 복사 | |
| `restart_groups` | `__init__` [57](5_DAO/SRC/DAO_LLR_MATRIX.py#L57), `Read_Input_LLR_Matrix` [532](5_DAO/SRC/DAO_LLR_MATRIX.py#L532) | 복사 | |
| `FERs` | `__init__` [66](5_DAO/SRC/DAO_LLR_MATRIX.py#L66) | 조건부 초기화 [245~246](5_DAO/SRC/DAO_LLR_MATRIX.py#L245) | |
| `raw_FERs` | `__init__` [67](5_DAO/SRC/DAO_LLR_MATRIX.py#L67) | `copy_raw_FER` | |
| `seed_FERs` | `__init__` [68](5_DAO/SRC/DAO_LLR_MATRIX.py#L68) | `copy_seed_FER` | |
| `FERs_partial` | `__init__` [71](5_DAO/SRC/DAO_LLR_MATRIX.py#L71) | `copy_partial_FER` | |
| `raw_FERs_partial` | `__init__` [72](5_DAO/SRC/DAO_LLR_MATRIX.py#L72) | `copy_partial_FER` | |
| `seed_FERs_partial` | `__init__` [73](5_DAO/SRC/DAO_LLR_MATRIX.py#L73) | `copy_partial_FER` | |
| `avg_iterations` | `__init__` [76](5_DAO/SRC/DAO_LLR_MATRIX.py#L76) | 조건부 초기화 | |
| `avg_iterations_partial` | `__init__` [77](5_DAO/SRC/DAO_LLR_MATRIX.py#L77) | `copy_partial_FER` | |
| `num_errors` | `__init__` [80](5_DAO/SRC/DAO_LLR_MATRIX.py#L80) | 조건부 초기화 | |
| `num_tests` | `__init__` [81](5_DAO/SRC/DAO_LLR_MATRIX.py#L81) | 조건부 초기화 | |
| `num_errors_partial` | `__init__` [82](5_DAO/SRC/DAO_LLR_MATRIX.py#L82) | `copy_partial_FER` | |
| `num_tests_partial` | `__init__` [83](5_DAO/SRC/DAO_LLR_MATRIX.py#L83) | `copy_partial_FER` | |
| `LLR_matrix_file_name` | `Read_Input_LLR_Matrix` [452](5_DAO/SRC/DAO_LLR_MATRIX.py#L452) | **재생성** [238](5_DAO/SRC/DAO_LLR_MATRIX.py#L238) | |
| `input_LLR_matrix_file_path` | `Read_Input_LLR_Matrix` [455](5_DAO/SRC/DAO_LLR_MATRIX.py#L455) | 복사 (갱신 없음) | 발견 13 |
| `header` | `Read_Input_LLR_Matrix` [494](5_DAO/SRC/DAO_LLR_MATRIX.py#L494) | 복사 | |
| `ch_length` | `Read_Input_LLR_Matrix` [539](5_DAO/SRC/DAO_LLR_MATRIX.py#L539) | 복사 | |
| `th_length` | `Read_Input_LLR_Matrix` [540](5_DAO/SRC/DAO_LLR_MATRIX.py#L540) | 복사 | |
| `HBF_immutable_col_range` | `Read_Input_LLR_Matrix` [544,547](5_DAO/SRC/DAO_LLR_MATRIX.py#L544) | 복사 | [DAO_Main.py:7066](5_DAO/SRC/DAO_Main.py#L7066) 에서 읽는다 |
| `max_iteration` | `Is_LLR_Valid` [441](5_DAO/SRC/DAO_LLR_MATRIX.py#L441), `Change_Max_Iteration` [216](5_DAO/SRC/DAO_LLR_MATRIX.py#L216), `DAO_Main` 의 여러 모드 | 복사 (값 재계산 없음) | 발견 8. 검증 전에는 속성 자체가 없다 |

누락 필드는 없다. 다만 `Deep_Copy` 가 `copy.deepcopy` 에 기대므로 **필드를 새로 넣어도 아무 경고 없이 따라온다.** SW 분기 필드가 "복사본에서는 초기화되어야 하는 값" 이면 240~259 의 초기화 블록에 직접 넣어야 하고, 넣지 않으면 조용히 값이 따라간다. 4절에 이 자리를 적었다.

### 3.2 읽기 쓰기 왕복 일치

실제 파일 3개를 `Read_Input_LLR_Matrix` 로 읽고 `Save_Matrix`(내부적으로 `Build_LLR_Matrix_Output_Lines`)로 다시 써서 대조했다. 출력은 스크래치 디렉토리 `C:/Users/yongs/AppData/Local/Temp/claude/dao_r2_L1/` 에 두었고 저장소에는 파일을 만들지 않았다.

| 입력 | 바이트 일치 | 공백을 무시한 토큰열 일치 | 검증 결과 |
|------|------------|--------------------------|----------|
| `Input/Ref_C/Prime_ECC_2.3/Initial_LLR_matrix/LLR_MATRIX_0.txt` (init_n 2) | 아니오 | **예** (14줄) | 유효, `max_iteration` 5 |
| `Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt` (init_n 2) | 아니오 | **예** (14줄) | 유효, `max_iteration` 5 |
| `Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt` (init_n 3) | 아니오 | **예** (87줄) | 무효, "Group 0 Row 0 invalid floor_flag 0" (발견 11) |

- ㉮ 줄 순서, 줄 개수, 필드 수, 숫자 표기(전부 정수), 구분자(탭)는 모두 같다. 읽기가 `line.strip()` 으로 빈 줄과 탭만 있는 줄을 걸러내고([DAO_LLR_MATRIX.py:461](5_DAO/SRC/DAO_LLR_MATRIX.py#L461)) 쓰기가 그룹 사이에 빈 줄을 넣으므로 구획도 보존된다.
- ㉯ 바이트가 다른 이유는 세 가지다. ㉠ 쓰기가 `f"{int(value):2d}"`, `f"{row.CSW:4d}"` 로 폭을 맞춰 한 자리 수 앞에 공백을 붙인다([DAO_LLR_MATRIX.py:171](5_DAO/SRC/DAO_LLR_MATRIX.py#L171), [190](5_DAO/SRC/DAO_LLR_MATRIX.py#L190)) ㉡ 원본의 일부 줄 끝에 있던 공백이 사라진다 ㉢ 원본에는 없는 마지막 줄 개행이 붙는다.
- ㉰ CSW 가 1000 이상이면 `:4d` 폭을 넘어 자리 맞춤이 무너지지만 탭 구분이라 파싱에는 영향이 없다 (`MAX_CSW` 가 1408 이므로 실제로 일어난다).
- ㉱ 따라서 왕복은 **값을 보존한다.** 바이트 동일성이 필요하면 별도 처방이 필요하지만, 외부 디코더가 공백 구분으로 읽는 한 현재 상태로 문제 없다.

---

## 4절. 매트릭스 모델에 필드를 하나 더할 때 `DAO_LLR_MATRIX.py` 에서 손대야 하는 자리

SW 분기 필드를 넣을 다른 세션이 쓸 목록이다. 줄 번호는 커밋 `6e035e6` 기준이다.

### 4.1 `LLR_Row` 에 새 열을 더할 때 (파일의 행 끝에 열이 하나 늘어나는 경우)

| 순서 | 자리 | 함수, 줄 | 해야 할 일 |
|------|------|---------|-----------|
| 1 | dataclass 정의 | `LLR_Row` [23~32](5_DAO/SRC/DAO_LLR_MATRIX.py#L23) | 필드 추가. `is_group_restart` 뒤에 넣으면 기본값이 필요하고, 앞에 넣으면 `LLR_Row(...)` 를 위치 인자로 부르는 곳이 전부 어긋난다. `DAO_Main` 은 대부분 키워드 인자를 쓰지만 [DAO_LLR_MATRIX.py:535](5_DAO/SRC/DAO_LLR_MATRIX.py#L535) 의 읽기 경로는 위치 인자다 |
| 2 | 파일 읽기의 열 분해 | `Read_Input_LLR_Matrix` [524~528](5_DAO/SRC/DAO_LLR_MATRIX.py#L524) | `matrix = row[:-4]` 의 `4` 와 `row[-4]`~`row[-1]` 인덱스를 전부 옮긴다. **이 파일에서 가장 깨지기 쉬운 자리다.** 상수 `NUM_TRAILING_FIELDS` 를 만들어 쓰기와 공유하기를 권한다 |
| 3 | 새 행 객체 생성 | `Read_Input_LLR_Matrix` [534~536](5_DAO/SRC/DAO_LLR_MATRIX.py#L534) | 위치 인자 목록에 새 값을 끼운다 |
| 4 | 파일 쓰기의 열 구성 | `Build_LLR_Matrix_Output_Lines` [176~201](5_DAO/SRC/DAO_LLR_MATRIX.py#L176) | 세 갈래(`compare_with` 없음, 있고 `opt_row` 없음, 둘 다 있음) 모두에 새 필드의 문자열을 만들고 195~201 의 f-string 에 끼운다. 세 갈래 중 하나만 고치면 diff 출력에서만 열이 빠진다 |
| 5 | 행 단위 검증 | `Is_LLR_Valid` 의 row 루프 [335~382](5_DAO/SRC/DAO_LLR_MATRIX.py#L335) | 새 필드의 규칙을 추가하고 `DAO_spec.md` 3.4 에 RW 번호를 붙인다 |
| 6 | restart 행 분기 | `Is_LLR_Valid` [322~333](5_DAO/SRC/DAO_LLR_MATRIX.py#L322) | restart 행에서 새 필드가 어떤 값이어야 하는지 정한다. 지금은 `continue` 로 전부 건너뛴다 (발견 3) |
| 7 | CSW 블록 | `Is_LLR_Valid` [384~419](5_DAO/SRC/DAO_LLR_MATRIX.py#L384) | 새 필드가 그룹 안 행 순서에 관여하면 여기 규칙을 더한다 |
| 8 | iteration 블록 | `Is_LLR_Valid` [421~429](5_DAO/SRC/DAO_LLR_MATRIX.py#L421) | 새 필드가 그룹 안에서 모두 같아야 하면 `starts`, `ends` 와 같은 형태로 검사를 더한다 |
| 9 | 자동 보정의 행 재배치 | `Correct_LLR_Matrix` [586~599](5_DAO/SRC/DAO_LLR_MATRIX.py#L586) | 행을 통째로 재배치하므로 새 필드는 자동으로 따라간다. 새 필드가 정렬 키에 끼면 598 의 `sort(key=...)` 를 고친다 |
| 10 | 자동 보정의 행 제외 | `Correct_LLR_Matrix` [580](5_DAO/SRC/DAO_LLR_MATRIX.py#L580) | 새 필드가 "보정 제외" 를 나타내면 이 조건에 더한다 |

### 4.2 `LLR_Header` 에 새 줄을 더할 때

| 순서 | 자리 | 함수, 줄 | 해야 할 일 |
|------|------|---------|-----------|
| 1 | dataclass 정의 | `LLR_Header` [9~21](5_DAO/SRC/DAO_LLR_MATRIX.py#L9) | 필드 추가. 아래 3번이 위치 인자 호출이라 순서가 곧 파일의 줄 순서가 되게 두는 편이 읽기 쉽다 |
| 2 | 파일 읽기의 줄 순서 | `Read_Input_LLR_Matrix` [476~492](5_DAO/SRC/DAO_LLR_MATRIX.py#L476) | `idx_line` 을 하나 더 소비한다. `restart_iter` 처럼 조건부로 있는 줄이면 [486~489](5_DAO/SRC/DAO_LLR_MATRIX.py#L486) 를 본떠 분기한다 |
| 3 | 헤더 객체 생성 | `Read_Input_LLR_Matrix` [494~506](5_DAO/SRC/DAO_LLR_MATRIX.py#L494) | 위치 인자 11개 목록에 끼운다 |
| 4 | 파일 쓰기의 줄 순서 | `Build_LLR_Matrix_Output_Lines` [122~145](5_DAO/SRC/DAO_LLR_MATRIX.py#L122) | 읽기와 **같은 순서, 같은 빈 줄 배치**로 넣는다. 조건부 줄이면 [139~141](5_DAO/SRC/DAO_LLR_MATRIX.py#L139) 을 본뜬다. 값이 배열이면 `format_array_with_diff`, 스칼라면 `format_with_diff` 를 쓴다 (`compare_with` 의 diff 표시를 받으려면 필수) |
| 5 | 헤더 검증 | `Is_LLR_Valid` [276~290](5_DAO/SRC/DAO_LLR_MATRIX.py#L276) | 길이와 일관성 규칙을 더하고 `DAO_spec.md` 3.1 에 H 번호를 붙인다 |
| 6 | 파생 속성 | `Read_Input_LLR_Matrix` [539~547](5_DAO/SRC/DAO_LLR_MATRIX.py#L539) | 새 헤더 값에서 `ch_length` 처럼 파생되는 값이 있으면 여기서 만든다 |
| 7 | 값 범위 보정 | `Correct_Ch_Th_In_Row` [614~627](5_DAO/SRC/DAO_LLR_MATRIX.py#L614) | 새 필드가 `max_value`, `min_value` 처럼 파라미터별 경계면 클램프에 더하고, 길이 검사도 같이 더한다 (발견 10) |

### 4.3 `LLR_MATRIX` 인스턴스 속성을 더할 때

| 순서 | 자리 | 함수, 줄 | 해야 할 일 |
|------|------|---------|-----------|
| 1 | 생성자 초기화 | `__init__` [36~84](5_DAO/SRC/DAO_LLR_MATRIX.py#L36) | `init_n` 별로 갈리면 39~52 의 분기에, 공통이면 54~83 에 둔다. **초기화를 빠뜨리면 `max_iteration` 처럼 속성이 아예 없는 상태가 생긴다** (발견 8) |
| 2 | 읽기에서 채우기 | `Read_Input_LLR_Matrix` [539~547](5_DAO/SRC/DAO_LLR_MATRIX.py#L539) | 파일에서 파생되는 값이면 여기 |
| 3 | 복사 정책 | `Deep_Copy` [234~261](5_DAO/SRC/DAO_LLR_MATRIX.py#L234) | `copy.deepcopy` 가 자동으로 복사하므로 **따라가면 안 되는 값일 때만** 240~259 에 초기화를 넣는다. 파일 이름처럼 인덱스를 따라가는 값이면 238 옆에 재생성을 넣는다 |
| 4 | 파일 이름 | `Get_LLR_Matrix_File_Name` [263](5_DAO/SRC/DAO_LLR_MATRIX.py#L263), `Save_Matrix` [549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549) | 새 속성이 저장 경로나 이름에 들어가면 |

### 4.4 이 파일 밖에서 함께 손대야 하는 자리

| 자리 | 위치 | 이유 |
|------|------|------|
| 로그 요약기 | [DAO_Main.py:87~143](5_DAO/SRC/DAO_Main.py#L87) | `_summarize_value` 가 헤더 필드와 행 필드를 이름으로 하나씩 적는다. 새 필드를 넣지 않으면 디버그 로그에서만 조용히 빠진다 |
| 규격 문서 | [DAO_spec.md](5_DAO/DAO_spec.md) 2.2, 2.3, 3장 | 필드표와 유효성 규칙 |
| 새 모드 체크리스트 | [DAO_spec.md](5_DAO/DAO_spec.md) 7장 | 새 필드를 만드는 모드가 지켜야 할 항목 |

### 4.5 필드 추가 전에 먼저 정리하기를 권하는 것

- ㉮ 행 끝 열 개수 `4` 를 상수로 뽑아 읽기(524~528)와 쓰기(195~201)가 같은 값을 보게 한다. 지금은 두 곳이 서로를 모르는 채 숫자로만 맞춰져 있다.
- ㉯ 헤더와 행의 생성자 호출을 위치 인자에서 키워드 인자로 바꾼다 (494~506, 534~536). 필드를 끼워 넣을 때 순서가 어긋나도 즉시 드러난다.
- ㉰ 발견 6 의 H6, G7 을 먼저 넣는다. 새 필드가 그룹 구조를 건드리면 그 오류를 잡아 줄 검사가 현재는 없다.

---

## 5절. 실행 검증에 쓴 스크립트

읽기 전용으로 돌렸고 저장소에 파일을 만들지 않았다. 스크립트와 출력은 `C:/Users/yongs/AppData/Local/Temp/claude/dao_r2_L1/` 에 있다 (`roundtrip.py`, `rules.py`, `gaps.py`, `hbf.py`).
