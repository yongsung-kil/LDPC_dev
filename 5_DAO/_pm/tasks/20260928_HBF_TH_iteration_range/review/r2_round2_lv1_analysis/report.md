## Round 2 결과: 분석

> 작성: 2026-09-29 13:58:32
> 기준 커밋 2e34036. 에이전트 5개(lv1)의 발견 29건을 같은 문제끼리 합쳐 21건으로 정리했다.
> 리뷰 도중 다른 세션이 `5_DAO/SRC`를 고치기 시작해, 에이전트 2, 4, 5는 기준 커밋에서 꺼낸 복사본으로 다시 확인했다. 에이전트 1, 3은 작업 폴더가 기준 커밋과 같던 때(13:56:38 이전)에 끝났다.
> 메인이 F1~F5를 기준 커밋의 복사본으로 다시 재현했다 (아래 "메인 재현" 절).

발견: 21건 (CRITICAL 0, HIGH 3, MEDIUM 3, LOW 15)

| # | 심각도 | 문제 | 위치 (2e34036 기준) | 이번 변경이 만든 것인가 | 지적 에이전트 |
|---|--------|------|------|------|------|
| F1 | HIGH | 타겟에 SW(Syndrome Weight) 분기 그룹이 있으면 도는 모드는 MUTATE_MATRIX(10)와 MUTATE_CSW(11)뿐인데, 시작 검사(T4)와 그 오류 문구, README, spec은 9개 모드를 함께 쓸 수 있다고 안내한다. 안내대로 다른 모드를 넣으면 시작 검사를 통과하고 그 모드 차례의 stage에서 `MPI_Abort`로 멈춘다 | [DAO_Main.py:8360](../../../../../SRC/DAO_Main.py#L8360), [DAO_Main.py:8478](../../../../../SRC/DAO_Main.py#L8478), [README.md:123](../../../../../README.md#L123), [DAO_spec.md:176](../../../../../DAO_spec.md#L176) | 예 (새 설정과 새 검사와 새 안내). 모드 제한을 stage에서만 보는 것은 2026-09-21부터 | 2, 3, 4, 5 |
| F2 | HIGH | 검사되는 경계는 iteration 4와 5 사이 하나뿐이다. SW 분기가 없는 매트릭스에서 HBF(Hybrid Bit Flipping) 기본 시퀀스의 INSERT_RANDOM_GROUP이 iteration 5~24 그룹을 붙이고 그 trial이 유효로 통과한다. 8과 9 사이를 걸치는 입력 row(5~10)도 통과한다 (사용자 요구 3과 어긋남) | [DAO_LLR_MATRIX.py:492](../../../../../SRC/DAO_LLR_MATRIX.py#L492), [DAO_Main.py:2685](../../../../../SRC/DAO_Main.py#L2685), [DAO_Config.py:258](../../../../../SRC/DAO_Config.py#L258) | 예 (매트릭스 max_iteration 상한 검사를 없애며 열림) | 2, 4 |
| F3 | HIGH | COPY_GROUP이 후보 그룹의 분기 index(`floor_flag`)와 헤더 표시(`type_each_group`)를 타겟 그룹에 복사한다. 분기 구간 뒤의 보통 그룹이 타겟이면 새 분기 구간이 생기고 유효로 통과한다. 갱신되면 그 그룹이 타겟인 다음 stage에서 10, 11 밖의 모드가 멈춘다 | [DAO_Main.py:9062](../../../../../SRC/DAO_Main.py#L9062), [DAO_Main.py:9071](../../../../../SRC/DAO_Main.py#L9071) | 아니오 (예전부터). 이번 변경이 COPY_GROUP을 그룹 구조를 그대로 두는 모드로 허용 목록에 넣음 | 2 |
| F4 | MEDIUM | row가 하나뿐인 그룹이 타겟이면 MUTATE_CSW가 바뀌지 않은 매트릭스를 성공으로 돌려주고, 그 stage의 trial이 모두 같은 매트릭스를 측정한다 | [DAO_Main.py:7146](../../../../../SRC/DAO_Main.py#L7146), [DAO_Main.py:3743](../../../../../SRC/DAO_Main.py#L3743) | 아니오 (예전부터). 그룹 단위 타겟(64a07a9)으로 row 하나짜리 그룹이 타겟이 되면서 드러남 | 2, 4 |
| F5 | MEDIUM | GEN_SINGLE_ROW와 `IS_HBF_OPT = True`를 함께 쓰면 후보 row(iteration 1~50)가 모두 HBF2로 버려진다. `Validate_Config`가 이 조합을 막지 않는다 | [DAO_Main.py:10363](../../../../../SRC/DAO_Main.py#L10363), [DAO_Main.py:9977](../../../../../SRC/DAO_Main.py#L9977) | 아니오 (예전에는 max_iteration 상한으로 같은 결과) | 2 |
| F6 | MEDIUM | 문서가 HBF 최적화 모드의 사용 조건을 알리지 않는다. ㉮ spec 3.7절 ㉲ "HBF 최적화 모드와 SW 분기의 결합은 다루지 않는다"가 실제 사용과 어긋남 ㉯ spec 3.7절 ㉯와 README 3.4절 ㉮가 제한 대상 시퀀스를 `Gen_LLR_Mode_SEQUENCE`로만 적고 멈추는 때(그 모드의 stage 시작)를 적지 않음 ㉰ README 4.1.1절의 `IS_HBF_OPT` 설명에 HBF1, HBF2, init_n 조건, 기본 HBF 시퀀스의 제약이 없음 ㉱ `DAO_Config.py` 134행 주석이 쓰이지 않는 `GenLLRModeHBF`를 가리킴 | [DAO_spec.md:159](../../../../../DAO_spec.md#L159), [DAO_spec.md:162](../../../../../DAO_spec.md#L162), [README.md:851](../../../../../README.md#L851), [README.md:932](../../../../../README.md#L932), [DAO_Config.py:134](../../../../../SRC/DAO_Config.py#L134) | 일부 | 5 |
| F7 | LOW | 문서와 docstring이 "HBF 구간에서 디코더는 dv_idx 0의 TH를 읽지 않는다"고 적고 `decoder.cpp:4058`을 든다. 4058행은 `__AUTO_LLR_OPT__`가 꺼진 갈래다. 켜진 갈래에서는 `flag_BF_on`이 늘 LOW라 TH를 읽고, TH가 모두 0이면 1 bit 정밀도와 같은 출력이 나온다. 규칙의 결론은 같고 설명이 어긋난다 (사용자 확인 필요) | [DAO_spec.md:123](../../../../../DAO_spec.md#L123), [DAO_LLR_MATRIX.py:101](../../../../../SRC/DAO_LLR_MATRIX.py#L101) | 예 | 4 |
| F8 | LOW | 디코더의 1 bit 조건은 열 차수 6 이상(`v_deg > DV_5`)이고 DAO의 고정 대상은 헤더 첫 DV 칸이다. 둘이 같으려면 열 차수 6 이상이 헤더 첫 칸의 범위에만 있어야 한다 (사용자 확인 필요) | [DAO_LLR_MATRIX.py:710](../../../../../SRC/DAO_LLR_MATRIX.py#L710) | 아니오 | 4 |
| F9 | LOW | 새 row를 만드는 모드의 로그가 보정 전 값을 찍어 HBF 구간 row의 dv_idx 0 TH가 난수로 보인다. 보정이 0으로 바꾼 것은 보정 로그에 남지 않는다 | [DAO_Main.py:795](../../../../../SRC/DAO_Main.py#L795), [DAO_LLR_MATRIX.py:829](../../../../../SRC/DAO_LLR_MATRIX.py#L829) | 로그 어긋남은 예 | 1 |
| F10 | LOW | REGEN_DV의 재사용 모드가 HBF 구간 row의 dv_idx 0 조각(TH 0 0 0)을 다른 DV로 옮긴다 | [DAO_Main.py:3986](../../../../../SRC/DAO_Main.py#L3986) | 아니오 | 1 |
| F11 | LOW | 규칙 두 개를 함께 어긴 row의 오류 문구가 원인과 다르다 (비증가 문구가 HBF1보다 먼저, 거꾸로 된 iteration에 HBF1 문구) | [DAO_LLR_MATRIX.py:521](../../../../../SRC/DAO_LLR_MATRIX.py#L521), [DAO_LLR_MATRIX.py:578](../../../../../SRC/DAO_LLR_MATRIX.py#L578) | 일부 | 1 |
| F12 | LOW | 쓰이지 않는 이름: `LLR_MATRIX.HBF_max_iteration`, `GenLLRModeHBF`, `HBF_OPT_CONFIG.__init__` | [DAO_LLR_MATRIX.py:42](../../../../../SRC/DAO_LLR_MATRIX.py#L42), [DAO_Constants.py:43](../../../../../SRC/DAO_Constants.py#L43), [DAO_Config.py:369](../../../../../SRC/DAO_Config.py#L369) | 아니오 | 1, 5 |
| F13 | LOW | 지금 동작과 다른 docstring과 문구: `Gen_LLR_Mutate_Matrix`, `Gen_LLR_Mutate_CSW`, `Generate_Random_Mutation`, `Mutate_CSW`, `Set_Gen_Trial_LLR_Mode`의 빈 시퀀스 문구 | [DAO_Main.py:3726](../../../../../SRC/DAO_Main.py#L3726), [DAO_Main.py:3756](../../../../../SRC/DAO_Main.py#L3756), [DAO_Main.py:7079](../../../../../SRC/DAO_Main.py#L7079), [DAO_Main.py:8448](../../../../../SRC/DAO_Main.py#L8448) | 아니오 | 5 |
| F14 | LOW | HBF 최적화 모드에서 모든 trial이 버려지는 stage가 있다 (GEN_INITIAL_GROUP의 iteration 1~20, 끝 iteration이 4보다 작은 그룹 뒤의 INSERT_RANDOM_GROUP). 버릴 때마다 오류 매트릭스 파일을 쓴다 | [DAO_Main.py:3639](../../../../../SRC/DAO_Main.py#L3639), [DAO_Main.py:10078](../../../../../SRC/DAO_Main.py#L10078) | 아니오 (버려지는 경우는 줄었음) | 2 |
| F15 | LOW | `_generate_mutation_for_group`(SPLIT_GROUP, INSERT_MUTATED_GROUP)과 `_generate_mutation_for_row`(INSERT_MUTATED_ROW)가 HBF 구간 row의 dv_idx 0 TH도 후보로 고른다. 보정이 0으로 되돌려 그 변이는 사라진다 | [DAO_Main.py:3517](../../../../../SRC/DAO_Main.py#L3517), [DAO_Main.py:3568](../../../../../SRC/DAO_Main.py#L3568) | 아니오 | 2, 5 |
| F16 | LOW | INSERT_RANDOM_GROUP과 SPLIT_GROUP이 유효성 검사 전에 root의 `target_group_indices`를 고쳐, 버려진 trial의 고침이 그 stage 동안 root에 남는다 | [DAO_Main.py:2809](../../../../../SRC/DAO_Main.py#L2809), [DAO_Main.py:3484](../../../../../SRC/DAO_Main.py#L3484) | 아니오 | 2 |
| F17 | LOW | stage 로그의 "Current target index" 줄이 실제 타겟과 다른 그룹을 적는다 (별도 카운터). 실제 타겟은 `[target_group_indices]` 줄이 적는다 | [DAO_Main.py:2302](../../../../../SRC/DAO_Main.py#L2302), [DAO_Main.py:2322](../../../../../SRC/DAO_Main.py#L2322) | 아니오 | 3 |
| F18 | LOW | `REGEN_DV_CONFIG.ENABLE_FIX_IDX`나 `REGEN_ROW_CONFIG.ENABLE_FIX_IDX`가 켜져 있으면 목록을 준 실행에서도 쓰이지 않는 `INITIAL_TARGET_GROUP_IDX`의 범위를 검사한다 | [DAO_Main.py:9861](../../../../../SRC/DAO_Main.py#L9861), [DAO_Main.py:9916](../../../../../SRC/DAO_Main.py#L9916) | 아니오 | 3 |
| F19 | LOW | spec 3.6절 ㉰ "유효성 검사, 보정, 변이, 난수 생성이 모두 이 함수를 쓴다"가 넓게 적혀 있다. 이 함수를 쓰는 자리는 다섯 곳이고 나머지는 뒤이은 보정에 기댄다 | [DAO_spec.md:125](../../../../../DAO_spec.md#L125) | 예 | 5 |
| F20 | LOW | 태스크 문서 7절의 검사 건수 내역(20건)이 실제(22건: 7, 5, 10)와 다르다 | [태스크 문서](../../20260928_HBF_TH_iteration_range.md) | 예 | 5 |
| F21 | LOW | `test_hbf_th_iteration_range.py`가 바꾼 전역 설정을 되돌리지 않는다 (네 파일을 한 프로세스에서 두 순서로 돌려도 44건 통과라 지금은 영향 없음) | `_test/20260928_hbf_th_iteration_range/test_hbf_th_iteration_range.py` 68~80 | 예 | 5 |

참고 (발견이 아님): 목록을 주지 않은 실행의 타겟 목록은 SW 분기 매트릭스에서만 dff3dba와 다르다. 예전에는 같은 분기의 연속 그룹을 첫 그룹 하나로 줄였고 지금은 그룹 하나하나가 타겟이다 (의도한 변경, 에이전트 3).

### 심각도를 정한 까닭

- ㉮ F1은 에이전트 셋이 MEDIUM, 하나가 HIGH로 매겼다. 멈춤은 의도한 보호 동작이고 문구가 분명하며 그때까지의 optimal 매트릭스는 남는다. 그러나 문서가 쓸 수 있다고 안내한 설정에서, 앞 stage들이 다 돈 뒤에 실행이 끊기므로 HIGH로 둔다
- ㉯ F2는 SW 분기가 없는 매트릭스에서만 조용히 일어난다. iteration 1~8이 분기 그룹인 매트릭스는 모드 제한 때문에 40번 모드가 돌지 못한다 (F1의 멈춤으로 드러난다). 결과가 요구 3과 어긋난 채 남으므로 HIGH로 둔다
- ㉰ F3은 에이전트가 MEDIUM으로 매겼다. DAO가 분기를 만들지 않는다는 규칙(spec 3.7절)이 깨진 매트릭스가 optimal로 남을 수 있고, 뒷부분을 따로 최적화하는 실행(기본 시퀀스에 31번 모드 포함)에서 닿으므로 HIGH로 올린다

### 메인 재현 (기준 커밋 2e34036의 복사본, 단일 프로세스)

| 발견 | 입력과 설정 | 결과 |
|------|------|------|
| F1 | `LLR_MATRIX_2.txt`, 목록 `[0, 1]`, HBF 시퀀스 `[10, 11, 41]` | 시작 검사 오류 없음. stage 1(모드 10, 그룹 0), stage 2(모드 11, 그룹 0) 진행. stage 3에서 "target groups [0, 1] are SW branch groups, so mode INSERT_RANDOM_ROW (41) is not allowed"로 중단 |
| F2 | 분기 없는 2그룹 매트릭스(iteration 1~1, 2~4), 타겟 그룹 1, INSERT_RANDOM_GROUP | 결과 (1~1), (2~4), (5~24), 유효, max_iteration 24 |
| F2 | 분기 없는 3그룹 매트릭스(1~1, 2~4, 5~10) | 유효 |
| F3 | `LLR_MATRIX_2.txt`, 타겟 그룹 5, COPY_GROUP의 후보 그룹 0 | 그룹 5의 헤더 1에서 10으로, 꼬리 -1에서 0으로 바뀜. iteration 9~24 유지. 유효, `span_of_group[5] = (9, 24, 1)`. 이어서 타겟 `[5]`에 모드 30을 검사하면 "target groups [5] are SW branch groups"로 막힘 |
| F4 | `LLR_MATRIX_2.txt`, 타겟 그룹 0(row 1개), `Gen_LLR_Mutate_CSW` | 매트릭스를 돌려줌(None 아님), 값과 CSW 모두 그대로, 로그 "No mutations were applied." |
| F5 | `LLR_MATRIX_2.txt`, `Build_Single_Row_Matrix(0)` | None. "Group 0 Row 0 iteration 1~50 crosses the HBF boundary" |

### 통과 관점

- P1 HBF 구간 판단 기준과 경계값: 문제 미발견 (F12 제외). HBF1, HBF2, 디코더 조건이 모두 iteration 4를 HBF 구간에 넣는다. 경계를 걸친 row는 보정이 값을 그대로 두고 이어지는 유효성 검사가 거부한다. init_n 2, 3에서 HBF를 끄는 두 자리가 같은 결론을 낸다
- P2 HBF1, HBF2의 검사 순서와 적용 대상: 문제 미발견 (F11 제외). restart row는 iteration이 한 칸이라 경계를 걸칠 수 없다
- P3 보정과 유효성 검사의 순서: 문제 미발견 (F9 제외). 초기 매트릭스는 보정 없이 검사해 입력의 규칙 위반이 오류로 드러난다. 헤더 TH 최소값이 0보다 커도 보정과 검사가 부딪히지 않는다
- P4 iteration이 정해지기 전의 row 생성: 문제 미발견. `_generate_random_row`를 쓰는 네 자리가 모두 측정과 저장 전에 보정을 거친다
- P5 값 재사용과 조정 단계: 문제 미발견 (F10 제외). 재사용은 같은 stage, 같은 타겟 그룹 안에서만 일어나 HBF 구간 안과 밖 사이로 값이 옮겨지지 않는다
- P6 변이 후보와 제외 column: 문제 미발견. 제외 범위는 dv_idx 0의 TH 칸(column 1~3)과 같고 CH(column 0)는 후보에 남는다
- P8 row를 옮기는 모드의 값: 문제 미발견. 보정이 row의 새 iteration으로 판단하므로 옮기는 방향과 상관없이 값 규칙이 맞다 (분기 표시 복사는 F3)
- P9 TEST_FER, SAVE_UNCOR, REDECODE: 문제 미발견. 매트릭스마다 HBF 판정과 타겟 목록이 다시 정해진다
- P10 모드 17개: 허용 아홉 모드는 모두 그룹 수, 순서, iteration을 바꾸지 않고 타겟 그룹 하나만 쓴다 (COPY_GROUP의 분기 표시 복사는 F3). 막은 여덟 모드는 모두 그 가운데 하나 이상을 바꾼다
- P11 타겟 목록: 문제 미발견 (F1, F17, F18 제외). 목록을 만드는 세 자리가 같은 함수로 같은 목록을 낸다. 잘못 적은 목록은 걸러진 뒤 바로 다음 `Validate_Config`에서 멈춘다
- P12 seed 모드와 uncor 풀: 문제 미발견. 실행 모드마다 풀과 seed 모드가 같은 `LOAD_UNCOR_MODE`에서 정해진다. 최적화 실행에서 LOAD_NONE으로 중단되는 갈래는 설정으로 닿지 않는다
- P13 설정 출처와 MPI: 문제 미발견. `Bcast_Trial_LLR_Mode`의 보내는 쪽과 받는 쪽이 6칸, 같은 순서다. 모든 rank가 부르는 함수에서 root만 아는 값을 새로 읽는 자리가 없다. 복사와 pickle 뒤 속성이 보존된다
- P14 iteration 눈금: 문제 미발견. 디코더의 반복 번호와 매트릭스 row의 iteration이 같은 눈금이다 (F7, F8은 사용자 확인 필요)
- P15 요구 1, 2, 5, 6: 코드 자리와 검사가 모두 있다 (요구 3은 F2, 요구 4는 F1)
- P16 없앤 것의 흔적: SRC, spec, README, 검사 6종에 남은 흔적 없음. `Check_SW_Branch_Mode_Allowed`를 부르는 자리가 모두 인자 세 개다
- P17 spec 3.6절 표, 3.7절 ㉰의 예, 3.8절 T1~T4, 5.2절, 6.3절: 코드와 같다
- P18 검사 6종: 11, 22, 3, 8, 41, 20건 모두 통과

### 리뷰 뒤에 바뀌는 자리

다른 세션(ldpc-dev-94)이 사용자 지시로 HBF 구간 row의 dv_idx 0 TH를 변이와 난수 생성에서 빼는 수정을 하고 있다 (`IS_HBF_OPT`가 꺼져 있어도 적용, `HBF_immutable_col_range` 제거, `_generate_mutation_for_group`과 `_generate_random_row`의 인자 추가). F9, F12의 일부, F15가 이 수정과 겹친다. 이 보고서의 줄 번호는 그 수정 전인 2e34036 기준이다.

## 다음 단계 결정

→ 라이트 전환 종료 (트리거가 라이트 리뷰)

사유: 트리거가 라이트 리뷰라 Round 2에서 끝낸다. HIGH 3건은 메인이 기준 커밋에서 재현해 사실 여부를 확인했다. 처방의 검증(Round 3)은 하지 않았다.

### 종합 판정

수정 필요.

- ㉮ 이번 변경의 핵심(HBF 구간 row로 한정한 TH 0 규칙, 4와 5 사이 경계 검사, seed 모드, 그룹 단위 타겟)은 값과 흐름 모두 요구대로 동작한다. 값을 틀리게 만드는 결함은 찾지 못했다
- ㉯ 고칠 것은 설정과 모드의 결합 쪽에 모여 있다. F1(시작 검사에 분기 모드 제한 넣기)과 F3(COPY_GROUP이 타겟의 분기 표시를 지키게 하기)은 처방이 분명하다. F4, F5, F6도 작은 수정이다
- ㉰ F2는 사용자 결정이 필요하다: iteration 8과 9 사이 경계도 DAO가 검사할지, HBF 기본 시퀀스에서 그룹을 늘리는 모드(40, 60)를 어떻게 할지
- ㉱ F7, F8은 실행 파일의 디코더 갈래와 부호의 열 차수를 사용자가 확인해야 닫힌다. 규칙의 결론은 어느 쪽이든 같다
