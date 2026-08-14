# Round 3 / worker B-3 — F11 검증 (`_validate` 제약 4종)

> 작성: 2026-08-06 23:38:24
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/llr_matrix.py:73-94` `_validate()`
> 원문 대조: `0_LDPC_original/local_opt.cpp`, `decoder.cpp`, `common.h`, `mode.h`
> 실증: 스크래치패드 `exp/exp_a.py`, `exp_b.py`, `exp_c.py` (프로젝트 파일 무수정, 사본 + `_validate` 무력화)

---

## 0. 요약

Round 2(agent_3 M2)의 사실 진술은 **네 항목 모두 확인됨**이다. C++에는 대응 검증이 하나도 없다.
그러나 처방("restart 마지막 금지와 iter1 시작 강제는 제거")은 **두 항목 모두 수정이 필요하다**.

- ㉮ "iter1 시작 강제"를 **그냥 제거하면 퇴보다**. C++도 iteration 1이 어느 그룹에도 안 덮이면
  `selected_group = -1`로 배열 범위 밖을 읽는다 (`decoder.cpp:7048-7051`). 즉 커버리지는 C++에서도
  요구 사항이며, 제거하면 로드 시 에러가 런타임 중간 `ValueError`로 늦춰질 뿐이다 (실측 [B-2], [C-2]).
  틀린 것은 커버리지 요구가 아니라 **`s == 1` 이라는 형태**다 (C++이 받는 `iter_start = 0` 파일을 거부).
- ㉯ "restart 마지막 금지"는 **C++ 근거도 없고 디코딩도 정상 완주하며 성공 판정까지 낸다** (실측 [D]:
  restart가 마지막 iteration일 때 512프레임 중 445프레임이 **그 restart iteration에서 성공**).
  다만 restart iteration은 잔여 에러를 크게 늘리는 교란 단계이므로 마지막에 두면 손해다
  (실측 [1] 대 [2]). 하드 에러가 아니라 **경고로 완화**가 맞다.
- ㉰ "겹침 금지"는 Round 2 주장대로 `_group_of_iter` 정방향 순회의 **유일한 안전 근거임이 실증됨**
  (실측 [C-1]: 겹침 파일에서 정방향과 C++ 역방향이 iteration 3, 4, 5에서 서로 다른 그룹을 고른다).
- ㉱ "restart 단일화"는 C++ 근거가 전무하고 완화해도 아무 영향이 없다 (실측 [C-3]).

---

## 1. 확인할 근거 ㉮ — C++에 대응 검증이 있는가

### 1-1. LLR matrix 로더 전수 확인

`local_opt.cpp:52-184` `LOCAL_OPT::Read_LLR_info_Auto()`가 이 포맷의 유일한 리더다.
전 함수를 읽었으며 **검증문(`if` + 에러 처리)이 단 하나도 없다**. `fopen` 실패조차
`:60`에서 반환값을 확인하지 않고 바로 `fscanf`하며, NULL 검사는 로그 출력 시점인
`:139-142`에서 사후에 한 번 나온다 (그때는 이미 역참조된 뒤다).

**확인됨**: 그룹 연속성, iteration 1 시작, restart 단일, restart 마지막 중 어느 것도
로더에서 검사되지 않는다.

### 1-2. 소비처 전수 확인

`iter_start` / `iter_end` / `restart_iter` / `restart_num` / `num_group` /
`type_each_group` / `num_set_each_group`를 저장소 전체에서 grep한 결과, 소비처는 네 곳뿐이다.

| 소비처 | 파일:라인 | 무엇을 보는가 |
|---|---|---|
| 그룹, row 선택 | `decoder.cpp:6973-7073` `Get_Cur_LLR_Idx_FILE` | `num_group`, `num_set_each_group`, `iter_start`, `iter_end`, `type_each_group`, `CSW_thr` |
| Edge clear 판정 | `decoder.cpp:6538-6553` `Is_Iter_Type_Edge_Clear` | `restart_num`, `restart_iter[]` 뿐 |
| Init 판정 (SD 전용) | `decoder.cpp:6606-6625` `Is_Iter_Type_Init` | `restart_num`, `restart_iter[]` 뿐. **HD/AUTO는 `iter == 0`만 TRUE** (`:6610-6614`) |
| max_iteration 산출 | `local_opt.cpp:116` | `iter_end[num_row - 1]` 하나만 |

나머지 파일(`input.cpp`, `ecc_top.cpp`, `main.cpp`, `ecc_data.h`)에는 선언(`ecc_data.h:185-196`)과
포인터 전달(`ecc_top.cpp:216-229`)만 있고 값 검사가 없다.

**확인됨**: `input.cpp`은 H-matrix 로더(`ecc_top.cpp:251` `Load_PCM`이 여는 파일)만 다루며
LLR matrix와 무관하다. `Get_VNU_LLR_SET_FILE`(`decoder.cpp:7074-7133`)도 dv 구간 매칭
(`:7078-7083`)과 배열 읽기만 하고 iteration 구조를 보지 않는다.

### 1-3. 검사 없이 어떻게 동작하는가 (fallback)

| 상황 | C++ 동작 | 파일:라인 |
|---|---|---|
| 그룹 겹침 | **정상 설계**. 역방향 순회라 **높은 인덱스 그룹이 이긴다** | `decoder.cpp:6985-6999` |
| 어느 그룹도 iteration을 안 덮음 (빈틈, iteration 1 미커버) | `printf("[Error] @Cur_LLR_IDX (1)...")` 후 **`selected_group = -1`로 진행** → `type_each_group[-1]` 배열 범위 밖 읽기 (미정의 동작). AUTO 경로에서는 `start_idx` / `end_idx`가 루프 마지막 회차(g=0)의 값으로 남아 있어 사실상 그룹 0으로 흐른다 | `decoder.cpp:7048-7051`, `:6984-6999` |
| ITER 그룹 안에 iteration을 덮는 row 없음 | `table_row_idx`가 초기값 0 유지 → **테이블 전체의 0번 row** (그룹 첫 row가 아님) | `decoder.cpp:6974`, `:7051-7057` |
| CSW 그룹에서 어느 임계값도 만족 안 됨 | `table_row_idx = start_idx` (그룹 첫 row) | `decoder.cpp:7060` |
| 최종 `table_row_idx`가 범위 밖 | `printf("[Error] ... (2)")`만 하고 **그대로 반환** | `decoder.cpp:7069-7072` |

**핵심**: C++의 "빈틈" 처리는 관용이 아니라 **미정의 동작**이다. 즉 커버리지는 C++에서도
사실상 요구 사항이고, 다만 그 위반을 안전하게 잡지 못할 뿐이다.

---

## 2. 확인할 근거 ㉯ — C++의 iteration→row 선택 알고리즘 원문과 Python 대조

### 2-1. 원문 (`decoder.cpp:6984-6999`, AUTO 빌드 경로. `mode.h:20-26`에서 `__AUTO_LLR_OPT__` 정의)

```cpp
#if defined (__AUTO_LLR_OPT__)
	for (g = m_param_LLR->num_group - 1; g >= 0; g--) {   // 역방향
	    start_idx = 0;
	    for (int gg = 0; gg < g; gg++)  start_idx += m_param_LLR->num_set_each_group[gg];
	    end_idx = 0;
	    for (int gg = 0; gg <= g; gg++) end_idx += m_param_LLR->num_set_each_group[gg];
	    end_idx = end_idx - 1;
	    if ((iter >= m_param_LLR->iter_start[start_idx]) && (iter <= m_param_LLR->iter_end[end_idx])) {
	        selected_group = g;
	        break;                                        // 첫 매칭에서 종료
	    }
	}
#endif
```

이어서 row 선택 (`decoder.cpp:7051-7068`):

```cpp
	if (GROUP_TYPE_ITER == m_param_LLR->type_each_group[selected_group]) {
	    for (i = start_idx; i <= end_idx; i++) {          // 그룹 내 오름차순, 첫 매칭
	        if ((iter >= m_param_LLR->iter_start[i]) && (iter <= m_param_LLR->iter_end[i])) {
	            table_row_idx = i;  break;
	        }
	    }
	}
	else if (GROUP_TYPE_CSW == m_param_LLR->type_each_group[selected_group]) {
	    table_row_idx = start_idx;                        // fallback = 그룹 첫 row
	    num_candidate = m_param_LLR->num_set_each_group[selected_group];
	    for (i = num_candidate - 1; i > 0; i--) {         // 그룹 내 내림차순, 첫 매칭
	        if (prev_CSW <= m_param_LLR->CSW_thr[start_idx + i]) {
	            table_row_idx = start_idx + i;  break;
	        }
	    }
	}
```

`GROUP_TYPE_ITER = 0`, `GROUP_TYPE_CSW = 1` (`common.h:756-757`).

### 2-2. Python 대조

| 단계 | C++ | Python | 판정 |
|---|---|---|---|
| **그룹 순회 방향** | **역방향** `g = num_group-1 → 0`, 첫 매칭 (`decoder.cpp:6985-6998`) | **정방향** `for g, (a, b) in enumerate(...)`, 첫 매칭 (`llr_matrix.py:155-157`) | **반대 방향.** 겹침이 없으면 등가, 겹침이 있으면 갈림 (§6-1 실측) |
| 그룹 매칭 조건 | `iter >= iter_start[start_idx] && iter <= iter_end[end_idx]` (그룹 첫 row의 start, 마지막 row의 end) | `row_iter[a,0] <= it <= row_iter[b-1,1]` (`llr_matrix.py:156`) | 일치 |
| 매칭 실패 | `selected_group = -1` 유지 → printf 후 **OOB 읽기** (`:7048-7051`) | `ValueError` (`llr_matrix.py:158`) | Python이 더 안전, 정책 차이 |
| ITER 타입 row | 그룹 내 오름차순 첫 매칭 (`:7052-7057`) | 오름차순 첫 매칭 (`llr_matrix.py:169-171`) | 일치 |
| ITER 타입 매칭 실패 | `table_row_idx = 0` 초기값 → **테이블 0번 row** (`:6974`) | `ValueError` (`llr_matrix.py:172`) | Python이 더 안전, 정책 차이 |
| CSW 타입 row | 내림차순 첫 매칭 = 조건 만족 최대 인덱스, 없으면 `start_idx` (`:7060-7067`) | 오름차순 마지막 덮어쓰기 = 같은 답, 없으면 `a` (`llr_matrix.py:174-177`) | **결과 일치** (agent_3 §1-1 합성 파일 검증, agent_1 `:344`도 동일 결론) |
| row 1개 그룹 | `for (i=0; i>0; ...)` 미실행 → `start_idx` (`:7062`) | `b - a == 1` 단락 → ITER 분기 (`llr_matrix.py:168`) | 일치 |

**확인됨**: 산술은 일치하고, 갈리는 지점은 **그룹 순회 방향 하나뿐**이다.

---

## 3. 확인할 근거 ㉰ — restart 처리 원문

### 3-1. `Clear_Edge_Restart` (`decoder.cpp:709-739`)

HD 분기 (`:711-724`):

```cpp
	if ((MODE_DEC_HD == m_param_dec->init_n) || (MODE_DEC_1_5SD == m_param_dec->init_n)) {
	    if (TRUE == Is_Iter_Type_Edge_Clear(mn)) {
	        Clear_REG_min_pos();  Clear_REG_min_value(TRUE, TRUE);
	        Clear_CN_REG(IDX_CHECK_SUM);  Clear_Edge_SRAM_Sgn();
	        // Clear_Syndrome 없음, HD는 Syndrome을 계속 들고감  ← :717 원 주석
	        Clear_PMU();  Clear_Sum_t_OLD();
	    }
	}
```

`Is_Iter_Type_Edge_Clear` (AUTO + HD, `decoder.cpp:6541-6553`):
`iter == 0 || iter == 1 || iter == ITER_MAX_HBF + 1 || iter ∈ restart_iter[]`.
`ITER_MAX_HBF = 0` (`common.h:403-404`, AUTO 빌드) 이므로 실질 조건은 `iter ∈ {0, 1} ∪ restart_iter`.
Python `decoder.py:373` `edge_clear = it == 1 or mx.is_restart(it)`와 일치.

`Is_Iter_Type_Init`은 AUTO + HD에서 `iter == 0`만 TRUE (`decoder.cpp:6610-6614`).
즉 **restart iteration에서 syndrome은 재계산되지 않고 유지된다**. Python `decoder.py:354`가
syndrome을 1회만 계산하고 `:374-379`가 `synd`를 클리어하지 않는 것과 일치.

### 3-2. restart iteration이 마지막이어도 되는가 (C++ 흐름)

메인 루프 (`decoder.cpp:1117-1971`):

```cpp
	MN = m_param_dec->MN[m_param_dec->MN_num - 1];      // :1118
	for (mn = 0; mn < MN + 1; mn++) {                   // :1120
	    Clear_Iter_Start();                             // :1131
	    Clear_Edge_Restart();                           // :1133  ← iteration 진입 시점
	    Clk_Init();                                     // :1135
	    if (mn > 0) cur_set_idx = Get_Cur_LLR_Idx_FILE(mn);   // :1136-1138
	    else        cur_set_idx = 0;                    // :1143-1144
	    ... (column 전 구간 업데이트) ...
	    if (mn == 0) CRC_flag = FLAG_HIGH;              // :1947-1949
	    else if (TRUE == Check_End_Iter(&mn)) break;    // :1951-1958
	}
```

`Check_End_Iter` (`decoder.cpp:5303-5362`)는 `failure_flag == FLAG_LOW`면 `CRC_flag = FLAG_LOW`로
**성공 반환**(`:5342-5347`)하고, 실패이면서 `mn == MN`이면 `CRC_flag = FLAG_HIGH`로 종료한다(`:5350-5359`).

즉 **마지막 iteration `mn == MN`도 다른 iteration과 완전히 동일한 순서로 처리된다**:
edge clear → 전 column 업데이트 → CRC 판정. restart가 `MN`이어도 그 iteration은
정상 수행되고 성공 판정을 낼 수 있다. **확인됨.**

`MN` 산출 (`local_opt.cpp:116-131`):
`MN_num = iter_end[num_row-1]`, `MN[MN_num-1] = iter_end[num_row-1]`, HD는 전 원소에서
`ITER_MAX_HBF`(=0)를 빼므로 무변화 → **`MN = 마지막 row의 iter_end = max_iter`**.
루프는 `mn = 0 .. max_iter`, 테이블 조회는 `mn = 1 .. max_iter`.
Python `decoder.py:368` `range(1, self.max_iter + 1)` + `llr_matrix.py:63` `max_iter = row_iter[-1,1]`와 **정확히 대응**.

---

## 4. 질문 A — "restart 마지막 금지" 제거가 안전한가

### 4-1. 실측 [A] — restart를 마지막 그룹에 둔 인공 파일

`exp_a.py` [A-1] ~ [A-4]. 배포 `LLR_MATRIX_HD_0.txt`의 row 값을 그대로 쓰고 그룹 배치만 바꾼 파일.

- **strict 로드**: `ValueError: restart 그룹 뒤에 그룹이 없음` — **거부됨** (`llr_matrix.py:93-94`)
- **`_validate` 무력화 후**: 로드 성공, 디코딩 **정상 완주**, 예외 없음.
  FER은 restart 없는 대조군 [A-3], restart 뒤 그룹이 있는 [A-4]와 소수점 이하까지 동일
  (n_err 5/10/20/40 → FER 0.4297 / 0.6992 / 0.9375 / 0.9883)

### 4-2. 실측 [D] — restart iteration이 스스로 성공 판정을 내는가 (결정적)

`exp_c.py`. iteration 1을 무력화(`ch = 31`, `th` 전부 31 → flip 거의 불가)하고
iteration 2를 restart이자 마지막으로 둔 파일 대 iteration 1만 있는 대조군.

| n_err | [D] g1[1~1] 무력 + g2[2~2]R(마지막) | [D-대조] g1[1~1] 무력만 |
|---|---|---|
| 1 | **445 / 512 성공, 전부 iteration 2(restart)에서** | 0 / 512 |
| 2 | **359 / 512, 전부 iteration 2** | 0 / 512 |
| 3 | **271 / 512, 전부 iteration 2** | 0 / 512 |
| 5 | **132 / 512, 전부 iteration 2** | 0 / 512 |
| 10 | **4 / 512, 전부 iteration 2** | 0 / 512 |

**반대 논점(`llr_matrix.py:17-21` docstring, `decoder.py:333-334` 주석의 "ch=-1로 채널 무시 +
th=-1로 전 메시지 최대 레벨 → 순수 syndrome bit-flip")은 반박됨.** 순수 syndrome bit-flip
iteration은 그 자체로 **유효한 정정과 성공 판정을 낸다**. "그래서 뒤에 그룹이 필요하다"는
설계 의도는 코드, 주석, 문서 어디에서도 발견되지 않았다 (`llr_matrix.py` 전체와
`decoder.py:319-338` docstring 확인, 저장소 md grep 결과 해당 근거 없음).

### 4-3. 다만 restart를 마지막에 두면 손해다 (실측 [1] 대 [2])

`exp_b.py`. 그룹 배치만 다르고 나머지 동일. `collect_profile`로 iteration별 평균 잔여 에러비트 측정.

| 파일 | n_err=20 성공 iteration 분포 | FER | iteration별 (활성, 평균 잔여 에러비트) |
|---|---|---|---|
| [1] g1[1~1], g2[2~2]**R**, max_iter=2 | {1: 36} | 0.9297 | (512, 2.4) → (476, **1635.2**) |
| [2] g1[1~1], g2[2~2] 일반 row | {1: 36, 2: 2} | 0.9258 | (512, 2.4) → (476, 2.5) |
| [3] 배포 HD_0 (restart=2, 뒤에 g3[3~5]) | {1: 36, 5: 1} | 0.9277 | (512, 2.4) → (476, **1635.2**) → (476, 650.1) → (476, 7.4) → (476, 2.5) |

restart iteration은 잔여 에러를 2.4 → 1635.2로 크게 늘리는 **교란 단계**이고, [3]처럼
뒤 그룹이 있어야 650.1 → 7.4 → 2.5로 회수된다. 마지막에 두면 그 회수 기회가 없어 손해다.
단 [4] 대 [5](g3[8~8]이 restart냐 일반이냐)에서는 FER 차이가 없었다 (양쪽 0.9258).

**주의**: 이 FER 수치는 F2가 지적한 대로 matrix 경로 자체가 현행 토이 데이터에서
포화되어 있으므로(n_err 50 이상 FER≡1.0) 절대값을 신뢰하면 안 된다. 여기서 쓰는 것은
㉮ 예외 없이 완주하는가, ㉯ restart iteration이 성공 판정을 내는가, ㉰ 잔여 에러 추이의
방향뿐이며, 이 셋은 데이터 품질과 무관하게 성립한다.

### 4-4. 질문 A 결론

**제거 자체는 안전하다** (C++ 근거 없음 확인됨, 완주 확인됨, 성공 판정 확인됨).
그러나 **품질 신호를 잃는다**. 하드 에러(`raise`)를 **경고**로 낮추는 것이 맞다.

---

## 5. 질문 B — "iter1 시작 강제" 제거가 안전한가

### 5-1. C++의 iteration 계수 (확인됨)

- 루프는 `mn = 0 .. MN` (`decoder.cpp:1120`), `MN = max_iter` (§3-2)
- `mn == 0`은 테이블 미조회 (`decoder.cpp:1143-1144` `cur_set_idx = 0`), CRC도 무조건 실패 처리
  (`decoder.cpp:1947-1949`)
- 테이블 조회는 `mn = 1 .. max_iter` (`decoder.cpp:1136-1138`)
- iteration 0은 별도의 Pre-update 단계로 취급된다 (`Is_Iter_Type_Init`이 HD/AUTO에서
  `iter == 0`만 TRUE — `decoder.cpp:6610-6614`)

**따라서 C++도 1-base로 테이블을 조회하며, Python `decoder.py:368` `range(1, max_iter+1)`과 일치한다.**
"iteration 1 커버리지"는 파일 포맷 제약이 아니라 **디코더 루프와의 계약**이라는 가설은 **확인됨**.

### 5-2. 그러나 커버리지는 C++에서도 요구 사항이다 (가설의 후반부는 반박됨)

C++에서 iteration 1을 덮는 그룹이 없으면 `selected_group = -1`이 되고,
`decoder.cpp:7048-7050`이 `[Error]`를 출력한 뒤 `:7051`에서 `type_each_group[-1]`을 읽는다.
**배열 범위 밖 접근이며 미정의 동작이다.** 즉 C++이 "iteration 1부터 시작하지 않는 파일"을
정상 입력으로 받아들이는 것이 아니라, 위반을 안전하게 잡지 못할 뿐이다.

### 5-3. 실측 [B]

| 케이스 | strict | `_validate` 무력화 후 |
|---|---|---|
| [B-1] 첫 그룹 `iter_start = 0` (g1[0~1], g2[2~5]) | `ValueError: 그룹 1 iter_start 0 != 이전 iter_end+1` — **거부** | 로드 성공, 디코딩 정상 (n_err=20 FER 0.9375, 기준선과 동일). **C++에서도 정상**(iteration 0은 미조회) → **거짓 거부** |
| [B-2] 첫 그룹 `iter_start = 3` (g1[3~4], g2[5~8]) | `ValueError: 그룹 1 iter_start 3 != 이전 iter_end+1` — 거부 | 로드는 성공하지만 **디코딩 중 `ValueError: iteration 1을 덮는 그룹 없음 (max_iter=8)`** |

[B-2]가 결정적이다. 제거하면 **로드 시점의 명확한 에러가 첫 배치 디코딩 도중의
`ValueError`로 늦춰진다**. 배치 루프(`sim.py:17-22`)가 이미 프레임을 돌린 뒤 터지므로
진단은 나빠지고 안전성은 그대로다.

### 5-4. 질문 B 결론

**"iter1 시작 강제"를 그냥 제거하는 것은 반대한다 (퇴보).**
틀린 것은 커버리지 요구가 아니라 `s == prev_end + 1`이라는 **표현 형태**다.
이 형태는 ㉮ `iter_start = 0`인 C++ 합법 파일을 거부하고([B-1] 확인),
㉯ 겹침, 빈틈, iteration 1 커버리지 세 가지를 한 조건에 뭉쳐 에러 메시지가 원인을 지목하지 못한다.
**"1..max_iter 전 구간 커버리지" 검사로 교체**해야 한다 (§7 대체 검사식).

---

## 6. 질문 C — 그룹 연속성과 restart 단일화의 처분

### 6-1. "겹침 금지"가 정방향 순회의 안전 근거인가 — **확인됨**

`exp_a.py` [C-1]. g1 = [1,5], g2 = [3,8]로 겹치게 만든 파일에서
Python 정방향(`llr_matrix.py:155-157`)과 C++ 역방향 직역(`decoder.cpp:6985-6998`)을 비교.

| iteration | Python 정방향 | C++ 역방향 | |
|---|---|---|---|
| 1, 2 | 0 | 0 | 일치 |
| **3, 4, 5** | **0** | **1** | **불일치** |
| 6, 7, 8 | 1 | 1 | 일치 |

**겹치는 구간 전체에서 서로 다른 그룹을 고른다.** 그룹이 다르면 row가 다르고,
row가 다르면 ch / th가 달라 **조용히 다른 FER**이 나온다 (예외 없음).
Round 2 주장은 **확인됨**이며, 겹침 허용은 반드시 `_group_of_iter` 역방향 전환과 한 쌍이어야 한다.

### 6-2. "빈틈 금지"는 별개 사안이다 — 연속성을 겹침 금지만으로 완화할 수 없다

`exp_a.py` [C-2]. g1 = [1,3], g2 = [6,8] (겹침 없음, 빈틈 있음).
`_validate` 무력화 시 로드는 통과하고 **디코딩 도중 `ValueError: iteration 4을 덮는 그룹 없음`**.
C++에서는 §5-2와 같은 OOB 경로다.

즉 연속성 검사가 막고 있던 세 가지는 서로 독립이다.

- ㉮ **겹침**: 순회 방향과 짝. 역방향으로 바꾸면 허용 가능
- ㉯ **빈틈**: 순회 방향과 무관. C++에서 미정의 동작이므로 **반드시 막아야 한다**
- ㉰ **iteration 1 미커버**: 빈틈의 특수 경우. 역시 막아야 한다

㉯와 ㉰는 하나의 커버리지 검사로 합칠 수 있고, 그러면 `iter_start = 0`도 자연히 허용된다.

### 6-3. restart 단일화의 C++ 근거 — **없음 (확인됨)**

`restart_iter[]`를 읽는 세 지점(`decoder.cpp:6549-6552`, `:6560-6563`, `:6620-6623`)은
모두 `iter == restart_iter[i]` 스칼라 비교만 한다. 그룹 구조, row 수, 그룹의 iteration 폭을
보는 코드는 없다. `Get_Cur_LLR_Idx_FILE`은 restart를 아예 참조하지 않는다
(`decoder.cpp:6973-7073` 전문에 `restart` 문자열 없음).

`exp_a.py` [C-3] 실측: g2 = [2,20]에 restart = 5인 파일 →
strict는 `ValueError: restart iter 5 그룹이 단일 iteration/row가 아님`으로 **거부**,
무력화 후에는 로드와 디코딩 모두 정상 (n_err=20 FER 0.9375, 기준선 동일).

배포 파일 `LLR_MATRIX_HD_0.txt`가 restart 그룹을 단일 row 단일 iteration으로 둔 것은
**그 파일의 모양일 뿐 포맷 규칙이 아니다**.

---

## 7. 대체 검사식 (질문 D의 근거)

`_validate`(`llr_matrix.py:73-94`)의 연속성 루프 `:80-87`과 restart 루프 `:88-94`를 다음으로 교체한다.

```python
    def _validate(self):
        # ... (74-79행 길이 검사는 그대로) ...
        for g, (a, b) in enumerate(self.group_slices):
            s, e = int(self.row_iter[a, 0]), int(self.row_iter[b - 1, 1])
            if e < s:
                raise ValueError(f"{self.name}: 그룹 {g + 1} iter_end {e} < iter_start {s}")

        # 커버리지: 디코더 루프가 도는 1..max_iter를 그룹이 빠짐없이 덮어야 한다.
        #   근거 = decoder.py:368 range(1, max_iter+1)  ↔  decoder.cpp:1120 for(mn=0; mn<MN+1; mn++)
        #          + decoder.cpp:1136-1138 (mn>0에서만 테이블 조회)
        #   C++은 미커버 iteration에서 selected_group=-1로 배열 범위 밖을 읽는다
        #   (decoder.cpp:7048-7051) — 조용한 오동작이므로 로드 시점에 막는다.
        #   iter_start=0으로 시작하는 파일은 C++이 정상 처리하므로 허용한다 (iteration 0은 미조회).
        covered = np.zeros(self.max_iter + 2, bool)
        for a, b in self.group_slices:
            s = max(1, int(self.row_iter[a, 0]))
            e = min(self.max_iter, int(self.row_iter[b - 1, 1]))
            if e >= s:
                covered[s:e + 1] = True
        gap = np.flatnonzero(~covered[1:self.max_iter + 1]) + 1
        if len(gap):
            raise ValueError(
                f"{self.name}: iteration {gap.tolist()}을 덮는 그룹이 없음 "
                f"(max_iter={self.max_iter} = 마지막 row의 iter_end)")

        # 겹침 금지: _group_of_iter(llr_matrix.py:154-158)가 정방향 첫 매칭인데
        #   C++ Get_Cur_LLR_Idx_FILE(decoder.cpp:6985-6998)은 역방향 첫 매칭이라
        #   겹침 파일에서 서로 다른 그룹을 고른다(실측: g1=[1,5], g2=[3,8]에서 iter 3~5 불일치).
        #   이 검사와 순회 방향은 한 쌍이다 — 겹침을 허용하려면 반드시
        #   _group_of_iter를 reversed(...)로 함께 바꿔야 한다.
        prev_end = None
        for g, (a, b) in enumerate(self.group_slices):
            s, e = int(self.row_iter[a, 0]), int(self.row_iter[b - 1, 1])
            if prev_end is not None and s <= prev_end:
                raise ValueError(
                    f"{self.name}: 그룹 {g + 1} iter_start {s}가 이전 그룹 iter_end {prev_end} "
                    f"이하 — 그룹 구간이 겹친다")
            prev_end = e
```

restart 관련 두 검사는 다음으로 대체한다 (`raise` 제거, 경고만).

```python
        # restart는 CN 상태를 지우고 순수 syndrome bit-flip을 1회 수행하는 교란 단계라
        # 뒤에 회복할 iteration이 있는 것이 통상적인 구성이다. C++에는 이 제약이 없고
        # (decoder.cpp:6549-6552는 iter == restart_iter[i]만 본다) 마지막이어도 정상
        # 성공 판정이 나오므로(decoder.cpp:1120,1133,1951,5350) 거부하지 않고 알린다.
        for it in sorted(self.restart_iters):
            if it < 1 or it > self.max_iter:
                warnings.warn(f"{self.name}: restart iter {it}가 1~{self.max_iter} 밖 — 무시된다")
            elif it == self.max_iter:
                warnings.warn(
                    f"{self.name}: restart iter {it}가 마지막 iteration — "
                    f"교란 뒤 회복할 iteration이 없다")
```

`_group_of_iter`(`:154-158`)에는 다음 주석을 단다.

```python
        # 정방향 첫 매칭. C++(decoder.cpp:6985-6998)은 역방향 첫 매칭이며,
        # 두 방향은 _validate의 겹침 금지 검사 아래에서만 등가다.
```

**대안**: 겹침을 허용하고 싶다면 `_group_of_iter`를
`for g, (a, b) in reversed(list(enumerate(self.group_slices)))`로 바꾸고 겹침 검사를 지운다.
이때 커버리지 검사는 그대로 유지해야 한다. 다만 배포 파일 2개와 C++ 예시 어디에도
겹치는 구성이 없으므로 지금은 겹침 금지 + 주석이 비용 대비 낫다.

---

## 판정

### 질문 A — restart 마지막 금지 제거가 안전한가

**안전하다 (제거 가능). 다만 경고로 남기는 편이 낫다.**

- C++ 근거 없음: **확인됨** (`local_opt.cpp:52-184` 검증문 0건, `decoder.cpp:6549-6552`,
  `:6560-6563`, `:6620-6623`은 `iter == restart_iter[i]`만 비교)
- 마지막 iteration도 동일 흐름으로 처리되어 성공 판정을 낸다: **확인됨**
  (`decoder.cpp:1120` 루프 상한 `MN+1`, `:1133` 진입 시 edge clear, `:1951` `Check_End_Iter`,
  `:5342-5347` 성공 반환, `:5350-5359` `mn == MN` 종료)
- Python도 예외 없이 완주: **확인됨** (실측 [A-2])
- restart iteration 자체가 성공 판정을 낸다: **확인됨** (실측 [D]: 512프레임 중 최대 445프레임이
  restart iteration에서 성공, 대조군은 0)
- "ch=-1, th=-1이라 유효 판정이 안 나온다"는 반대 논점: **반박됨** (동 실측)
- 다만 restart는 잔여 에러를 2.4 → 1635.2로 늘리는 교란 단계라 마지막에 두면 회수 기회가 없다:
  **확인됨** (실측 [1] 대 [2] 대 [3])

### 질문 B — iter1 시작 강제 제거가 안전한가

**그냥 제거하는 것은 반대한다. 커버리지 검사로 교체해야 한다.**

- C++도 1-base로 테이블을 조회하고 iteration 0은 미조회: **확인됨**
  (`decoder.cpp:1120`, `:1136-1138`, `:1143-1144`, `local_opt.cpp:116-131`, `common.h:404`)
- "iteration 1 시작은 파일 포맷 제약이 아니라 디코더 루프와의 계약"이라는 가설의 전반부: **확인됨**
- 가설의 후반부("따라서 없애도 된다"): **반박됨**. C++도 미커버 iteration에서
  `selected_group = -1`로 `type_each_group[-1]`을 읽는다 (`decoder.cpp:7048-7051`, 미정의 동작).
  Python에서 제거하면 로드 시 명확한 에러가 **첫 배치 디코딩 도중 `ValueError`로 늦춰질 뿐**:
  **확인됨** (실측 [B-2])
- 진짜 결함은 `s == 1` 형태가 `iter_start = 0`인 C++ 합법 파일을 거부하는 것: **확인됨** (실측 [B-1])

### 질문 C — 그룹 연속성과 restart 단일화의 처분

- **겹침 금지가 정방향 순회의 안전 근거**: **확인됨**. 겹침 파일에서 정방향과 역방향이
  iteration 3, 4, 5에 대해 서로 다른 그룹을 고른다 (실측 [C-1]). 조용히 다른 FER이 나온다
- **빈틈 금지는 별개 사안**: **확인됨**. 겹침 금지만으로는 완화할 수 없다.
  빈틈은 C++에서 미정의 동작이므로 커버리지 검사로 **반드시 막아야 한다** (실측 [C-2])
- **restart 단일화의 C++ 근거**: **없음 (확인됨)**. 완화해도 로드와 디코딩 모두 정상 (실측 [C-3])

### 질문 D — 최종 처방

| # | 제약 | 현행 (`llr_matrix.py`) | C++ 근거 | 처분 | 대체 검사식 |
|---|---|---|---|---|---|
| ㉮ | 그룹 겹침 금지 | `:83-84` (연속성에 포함) | 없음 (C++은 역방향 순회로 **겹침을 전제**, `decoder.cpp:6985-6998`) | **유지** (분리해서 명시) | `s <= prev_end`면 raise + "`_group_of_iter` 정방향 순회와 한 쌍" 주석 (§7). 겹침을 허용하려면 `_group_of_iter`(`:154-158`)를 `reversed(...)`로 함께 전환 |
| ㉯ | 빈틈 금지 + iteration 1 시작 강제 | `:80`, `:83-84` (`prev_end = 0`) | 형태(`s == prev_end+1`)는 근거 없음. **커버리지 요구 자체는 C++에도 있다** (`decoder.cpp:7048-7051` 미정의 동작) | **완화** (제거 아님) | `1..max_iter` 전 구간 커버리지 검사로 교체 (§7). `iter_start = 0` 허용, 미커버 iteration 번호를 메시지에 나열 |
| ㉰ | restart 그룹 단일 row / 단일 iteration | `:91-92` | **없음** (`decoder.cpp:6549-6552`는 `iter == restart_iter[i]`만) | **제거** | 없음. 대신 `restart_iters`가 `1..max_iter` 밖이면 경고 |
| ㉱ | restart 그룹 마지막 금지 | `:93-94` | **없음** (마지막이어도 `decoder.cpp:1120`, `:1133`, `:1951`, `:5350`으로 정상 판정) | **완화** (에러 → 경고) | `it == self.max_iter`면 `warnings.warn` (§7) |

**Round 2 처방의 판정: 수정 필요.**

- "restart 마지막 금지 제거" → **부분 유효**. 하드 에러 해제는 옳으나 완전 삭제보다 경고 전환이 낫다
  (교란 뒤 회복 iteration이 없다는 품질 신호를 잃지 않기 위함)
- "iter1 시작 강제 제거" → **반대**. 그냥 제거하면 로드 시 에러가 런타임 중간 에러로 밀리는 퇴보다.
  **커버리지 검사로 교체**가 맞다
- "제약과 순회의 한 쌍 관계를 주석으로" → **유효**. 실측으로 뒷받침됨 (실측 [C-1])
- Round 2가 다루지 않은 항목: **restart 단일화 제약(㉰)은 근거가 전무하므로 제거**해야 하며,
  **빈틈 금지(㉯)는 반대로 유지 강화**해야 한다

### 변경 등급

**Review**. 로직 변경이지만 배포 파일 2개(`LLR_MATRIX_HD_0.txt`, `HD_1.txt`)는 새 검사식을
그대로 통과하므로 현행 동작은 유지된다 (양쪽 모두 그룹이 iteration 1부터 겹침, 빈틈 없이 연속,
restart는 마지막이 아님). 다만 `_group_of_iter`를 역방향으로 바꾸는 대안을 택할 경우에는
FER에 영향을 줄 수 있으므로 **Decision**이다.

### 후속 확인 필요 (이번 검증 범위 밖)

- DAO(외부 최적화기)가 `iter_start = 0`, 겹치는 그룹, 다중 iteration 그룹 안의 restart,
  restart 마지막 중 어느 구성을 실제로 산출하는지 — 이 저장소에는 DAO 산출 규칙 문서가 없어
  확인 불가. 이것이 확인되면 ㉮의 "겹침 금지 유지 대 역방향 전환" 선택이 확정된다
- 여기서 쓴 FER 수치는 F2가 지적한 matrix 경로 포화 상태에서 측정한 것이라
  절대값 비교에 쓰면 안 된다 (본문 §4-3 주의 참조)
