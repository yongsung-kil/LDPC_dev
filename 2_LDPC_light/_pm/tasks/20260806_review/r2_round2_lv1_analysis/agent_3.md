# Round 2 / agent_3 — [V3. LLR_MATRIX 파서와 row 선택] 검토 결과

> 작성: 2026-08-06 23:05:33
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/llr_matrix.py` 전체,
> `LDPC_base/decoder.py:368-382` 호출부, `Input/LLR/LLR_MATRIX_HD_{0,1}.txt`,
> `Input/H_matrix/example_18x147_z256.qc`, `LDPC_base/pcm.py`
> 원문 대조: `0_LDPC_original/local_opt.cpp`, `decoder.cpp`, `common.h`, `mode.h`
> 커버 관점: agent_1 P3(13항목) + P6, agent_2 P5(㉮~㉴) + P6(㉮~㉳) + P12(㉮~㉴)

---

## 0. 결론

**CRITICAL 0건, HIGH 0건, MEDIUM 4건, LOW 6건.**

포맷 정본이 저장소에 없다는 Round 1의 전제는 **틀렸다**. 포맷을 읽는 C++ 로더가
`0_LDPC_original/local_opt.cpp:52-184` `LOCAL_OPT::Read_LLR_info_Auto()`에 그대로 있다.
이 함수와 대조한 결과 **파싱 필드 순서, 값 배치(dv-major), row 선택 산술은 전부 원문과 일치**한다.
남은 지적은 전부 "합법 입력을 거부한다" 또는 "에러 메시지 품질" 쪽이며,
**조용히 다른 FER을 내는 경로는 발견하지 못했다.**

---

## 1. 원문 대조로 확인된 항목 (문제 없음)

포맷 정본을 찾았으므로 추측이 아닌 원문 대조로 판정했다.

| 확인 항목 | Python | C++ 원문 | 판정 |
|---|---|---|---|
| 헤더 필드 순서 | `llr_matrix.py:109-121` | `local_opt.cpp:61-100` (`num_para_each_set` → `num_dv` → `dv_from[]` → `dv_to[]` → `num_group` → `num_set_each_group[]` → `type_each_group[]` → `restart_num` → `restart_iter[]` → `max_value[]` → `min_value[]`) | 일치 |
| row 꼬리 4필드 순서 (CSW, iter_start, iter_end, floor) | `llr_matrix.py:133` | `local_opt.cpp:111-114` | 일치 |
| `num_restart = 0`이면 restart 줄 생략 | `llr_matrix.py:117-119` | `local_opt.cpp:86-90` — `restart_num`이 0이면 루프가 토큰을 하나도 소비하지 않음 | 일치 (HD_1.txt가 이 형태) |
| **row 값 배치 = dv-major, dv 블록 안은 (ch, th1, th2, th3)** | `llr_matrix.py:58-60` `reshape(R, num_dv, num_param)` | `decoder.cpp:7080` `table_col_idx = i * num_para_each_set` → `:7089` `ch1=[col]`, `:7093-7095` `th1=[col+1] th2=[col+2] th3=[col+3]` | **일치. param-major 아님이 원문으로 확정됨** |
| ch 개수 = 2^(init_n-1) (HD 1 / 2SD 2 / 3SD 4) | `llr_matrix.py:31`, `43-45` | `decoder.cpp:7088-7132` (HD ch 1개, 2SD 2개, 3SD 4개, 그 뒤가 th) | 일치 |
| `max_iter = row_iter[-1, 1]` | `llr_matrix.py:63` | `local_opt.cpp:116` `m_param_dec->MN_num = LLR_info->iter_end[LLR_info->num_row - 1];` | **일치 (동일 식)** |
| 실행 iteration 범위 1..max_iter | `decoder.py:368` `range(1, max_iter+1)` | `decoder.cpp:1118` `MN = MN[MN_num-1]` → `:1120` `for (mn=0; mn<MN+1; mn++)`, `:1136-1145` mn=0은 테이블 미조회. `ITER_MAX_HBF = 0` (`common.h:404`, `__AUTO_LLR_OPT__` 정의됨 `mode.h:22`) | 일치 |
| dv 구간 매칭 = 첫 매칭 채택 | `llr_matrix.py:143-148` `hit[0]` | `decoder.cpp:7078-7083` 첫 매칭에서 `break` | 일치 |
| ITER 타입 row 선택 = 그룹 내 첫 매칭 | `llr_matrix.py:169-171` | `decoder.cpp:7052-7057` 첫 매칭 `break` | 일치 (순회 방향 동일) |
| **CSW 타입 row 선택** | `llr_matrix.py:174-177` (a+1..b-1 상향, 마지막 매칭 유지, fallback a) | `decoder.cpp:7060-7067` (`table_row_idx = start_idx` → `i = num_candidate-1`부터 하향, 첫 매칭 `break`) | **일치.** 양쪽 모두 "조건 만족하는 최대 인덱스, 없으면 그룹 첫 row". 비교 연산자도 `<=`로 동일 (`:7063` vs `:176`) |
| CSW 그룹 row 1개일 때 | `llr_matrix.py:168` `b - a == 1` 단축 → ITER 분기 | `decoder.cpp:7060-7062` `table_row_idx = start_idx` 후 `for (i=0; i>0; ...)`가 실행되지 않음 → `start_idx` | 일치 |
| `prev_csw` 초기값 = `|synd|` | `decoder.py:355` | `decoder.cpp:2993-3008` (iter 0 종료 시 `Syndrome[j] = Check_REG[j][IDX_CHECK_SUM]` 후 check_sum reg를 0으로 reset) → 같은 함수 뒤쪽 `:3462-3465` `Compute_CSW()`가 `Σ (check_sum + Syndrome) % 2 = Σ Syndrome`. 즉 iteration 1 진입 시 `prev_CSW = |synd|` | 일치 |
| CSW 갱신 시점 = column 루프 종료 후 | `decoder.py:427` | `decoder.cpp:3462-3465` (`jj == N_b-1 && ii == ColW[jj]-1`) → `Set_CSW` (`:6680-6683`) | 일치 |
| row 선택이 **직전** iteration CSW를 씀 | `decoder.py:380` | `decoder.cpp:1138` `Get_Cur_LLR_Idx_FILE(mn)`이 iteration 진입 시점(`:1133` Edge clear 직후) 호출 → 직전 iteration 종료 시 갱신된 `prev_CSW` 사용 | 일치 |
| `Compute_CSW` 정의 | `decoder.py:427` `(csum ^ synd).sum()` | `decoder.cpp:7293-7304`. `Compute_CSW_Auto`(`:7340-7351`)도 **본문이 완전히 동일**하며 `:1919` 로깅에만 쓰임 | 일치 (두 함수 어느 쪽이든 같음) |
| `is_restart` 소비 = edge clear 조건 | `decoder.py:373` `it == 1 or is_restart(it)` | `decoder.cpp:6538-6553` `Is_Iter_Type_Edge_Clear` (AUTO+HD): `iter==0 \|\| iter==1 \|\| iter==ITER_MAX_HBF+1(=1) \|\| iter ∈ restart_iter[]` | 일치 |
| restart 시 syndrome 유지 | `decoder.py:374-379` (synd 미클리어) | `decoder.cpp:709-724` `Clear_Edge_Restart` HD 분기에 `Clear_Syndrome()` 없음 (`:717` 주석 "HD는 Syndrome을 계속 들고감") | 일치 |
| Syndrome이 iteration 0에서만 갱신됨 | `decoder.py:354` 1회 계산 후 고정 | `decoder.cpp:2993` `Is_Iter_Type_Init(iter)` → `:6606-6614` AUTO+HD는 `iter==0`만 TRUE | 일치 |
| `GROUP_TYPE_ITER=0 / GROUP_TYPE_CSW=1` 및 인용 행번호 | `llr_matrix.py:32` 주석 `common.h:756-757` | `common.h:756-757` 실제로 그 행 | 일치 (행번호까지 정확) |
| **`max_value` / `min_value` / `floor_flag`를 안 쓰는 것** | `llr_matrix.py:54-55`, `133`(floor는 저장도 안 함) | 저장소 전체 grep 결과 이 세 필드는 `local_opt.cpp`의 **읽기(93-114)와 로그 출력(164-178)에만** 등장. `decoder.cpp`에는 한 번도 나오지 않음 (`Clear_REG_min_value`는 별개 심볼) | **일치. 원본도 산술에 쓰지 않으므로 무시가 맞다** |
| restart row의 `-1`을 그대로 산술에 넣는 것 | `llr_matrix.py:17-20` docstring, `decoder.py:388`, `94-96` | `decoder.cpp:7089-7095`가 배열 값을 클리핑 없이 그대로 반환 | 일치 |
| `row_csw = -1`(HD 파일)의 의미 | `llr_matrix.py:61` 그대로 보관 | ITER 타입 그룹에서는 조회되지 않음. CSW 그룹에 있어도 `prev_CSW <= -1`이 거짓이 되어 fallback (C++ `:7063`과 동일 동작) | 일치 |
| `is_restart`의 int/numpy 정수 멤버십 | `llr_matrix.py:53` `set(int(i) ...)`, `:152` | 호출부 `decoder.py:373`의 `it`은 `range()` 산출 Python int | 문제 없음 |
| 탭 / CRLF / 후행 공백 / 마지막 줄 개행 없음 | `llr_matrix.py:105-106` `ln.strip()` + `ln.split()` | — | 문제 없음 (실제 파일이 탭 구분이며 정상 로드됨) |
| `_group_of_iter` 첫 매칭 vs C++ 역방향 | `llr_matrix.py:154-158` | `decoder.cpp:6985-6999` `g = num_group-1`부터 하향, 첫 매칭 break | **현행 `_validate` 하에서는 등가.** 단 아래 M2 참조 |

### 1-1. CSW 경로 실측 검증

배포된 LLR 파일 2개는 모두 `needs_csw == False`(CSW 그룹 row가 1개)라 이 경로가 한 번도
실행되지 않는다(agent_2 P6㉳ 지적대로). 그래서 CSW 그룹 3 row짜리 합성 파일을 스크래치패드에
만들어 `row_index()`와 `decoder.cpp:7060-7067` 직역 함수를 비교했다.
임계값을 **비단조**(row1=100, row2=50, row3=200)로 두고 `csw ∈ {0,49,50,51,99,100,101,150,199,200,201,10^6}`
전부에 대해 **결과가 완전히 일치**했다(양쪽 모두 `[3,3,3,3,3,3,3,3,3,3,1,1]`).
즉 순회 방향이 반대여도(하향 break 대 상향 마지막 유지) 답은 같고, fallback도 그룹 첫 row로 동일하다.

### 1-2. 입력 데이터 무결성 (실측)

`example_18x147_z256.qc`를 `QCCode.load`로 읽어 확인했다.

- N_b=147, M_b=18, z=256, E=553
- column degree 히스토그램 `{2:17, 3:1, 4:129}`, row degree `{30:5, 31:13}`
- column DV 내림차순 성립 (`np.all(np.diff(col_deg) <= 0)` True)
- 헤더 `147 18` / `4 31` / `256` — J=4, K=31이 **실측 최대 degree와 정확히 일치**
- `col_dv_idx(code)` 결과: dv=4 → 구간 idx 1(129개), dv=3 → idx 2(1개), dv=2 → idx 3(17개).
  **예외 없이 전부 매칭된다.** dv 구간 `[11,4,3,2]`의 idx 0(dv=11)만 미사용
- LLR 파일의 th 4조 `(28,9,5) (10,9,4) (31,10,7) (12,10,8)` 모두 내림차순이고 `max_value=31` 이내

즉 agent_1 P6과 agent_2 P12㉮㉯㉰㉳의 "헤더 J=4인데 dv 구간에 11이 있다"는 우려는 **오류가 아니다**.
dv=11 행은 실물 부호(dv 최대 11 이상)용 파라미터가 그대로 남아 있는 것이고,
H-matrix 헤더 J와 LLR 테이블 dv 구간은 서로 다른 것을 뜻하므로 일치할 이유가 없다.

---

## 2. 지적 사항

### M1 (MEDIUM) — 줄 기반 파싱이 원 포맷(공백 구분 토큰 스트림)보다 좁다

`llr_matrix.py:105-121`

```python
lines  = [ln.strip() for ln in f if ln.strip()]
parsed = [np.array([int(v) for v in ln.split()], np.int64) for ln in lines]
num_param = int(parsed[i][0]); i += 1     # 줄 하나 = 필드 하나, 첫 토큰만 사용
```

원 포맷은 줄 구조가 없다. `local_opt.cpp:61-115`는 전부 `fscanf(matrix_in, "%d", &c)`로
읽으므로 **개행 위치가 어디든 동일하게 파싱된다**. 반면 이 파서는 "필드 하나 = 줄 하나"를
강제하고, 스칼라 필드는 그 줄의 첫 토큰만 취하고 나머지를 버린다.

스크래치패드 실측:

- ㉮ 헤더를 다르게 줄바꿈한 파일(`4 4` 한 줄, `dv_from dv_to` 한 줄 등, C++이 정상 읽는 스트림)
  → `IndexError: list index out of range` (원인을 지목하지 않는 맨 예외)
- ㉯ `num_restart = 2`이고 restart iteration이 한 줄에 하나씩(`2\n2\n4\n`)인 파일
  → `row 길이 4 != 4*4+4`. 배포 파일 2개는 `restart_num`이 0과 1뿐이라 **다중 restart 줄 배치는 미검증 구간**이다

다행히 row 길이 검사(`llr_matrix.py:131`)가 줄 밀림을 대부분 잡아내므로 **조용한 오파싱은
재현하지 못했다**. 즉 실패는 시끄럽게 난다. 그래도 루트 `CLAUDE.md` ㉰의 "외부 파라미터를
넣어도 동작"이라는 목표에서는 제약이다. 최소한 ㉮ 파싱을 토큰 스트림으로 바꾸거나
(`f.read().split()` 후 순차 소비), ㉯ docstring에 "필드마다 줄바꿈된 파일만 지원"을 명시할 것.

### M2 (MEDIUM) — `_validate`의 제약 4종이 C++에 근거가 없고, 합법 파일을 거부한다

`llr_matrix.py:73-94`. 각 제약을 원문과 대조하고 실제 파일로 확인했다.

| 제약 | Python | C++ 근거 | 실측 |
|---|---|---|---|
| 그룹 구간이 직전 그룹 `iter_end+1`에서 시작 (겹침, 빈틈 금지) | `:83-84` | **없음.** `decoder.cpp:6985-6998`은 `g = num_group-1`부터 내려오며 첫 매칭에서 break — 겹침을 허용하고 **높은 인덱스 그룹이 이긴다**. 겹침을 전제로 한 설계다 | 겹치는 파일 → `ValueError: 그룹 2 iter_start 5 != 이전 iter_end+1` |
| 첫 그룹이 iteration 1에서 시작 | `:80`, `:83` (`prev_end = 0`) | **없음.** C++은 mn=0에서 테이블을 조회하지 않을 뿐(`decoder.cpp:1143-1145`), `iter_start=0`인 파일도 문제없이 돈다 | `iter_start=0` 파일 → `ValueError: 그룹 1 iter_start 0 != 이전 iter_end+1` |
| restart iteration의 그룹은 단일 row, 단일 iteration | `:91-92` | **없음.** `decoder.cpp:6549-6552`, `:6620-6623`은 `iter == restart_iter[i]`만 본다. 다중 iteration 그룹 안의 restart도 정상 동작한다 | 그룹2가 `[2,20]`이고 restart=5인 파일 → `ValueError: restart iter 5 그룹이 단일 iteration/row가 아님` |
| restart 그룹이 마지막이면 안 됨 | `:93-94` | **없음.** restart가 마지막 iteration이어도 C++은 edge clear 후 그 iteration을 수행하고 끝난다 | restart=2이고 max_iter=2인 파일 → `ValueError: restart 그룹 뒤에 그룹이 없음` |

네 제약 모두 **배포된 예시 파일 2개의 모양에 맞춘 자체 가정**이고, DAO가 정당하게 낼 수 있는
구성을 막는다. 특히 첫 번째(겹침 금지)는 C++이 역방향 순회를 쓰는 이유 자체를 부정하는 제약이다.

동시에 이 제약이 **`_group_of_iter`의 정방향 순회(`llr_matrix.py:155`)를 안전하게 만드는
유일한 근거**라는 점이 중요하다. 제약을 완화하려면 순회 방향을 C++과 같은 역방향
(`reversed(list(enumerate(self.group_slices)))`)으로 바꿔야 하며, 그러지 않으면 겹침 파일에서
**조용히 다른 row를 골라 FER만 달라진다**. 지금 고칠 필요는 없으나, 제약과 순회 방향이 한 쌍이라는
사실을 `_validate` 주석에 남길 것 (지금은 어디에도 적혀 있지 않다).

전부 시끄러운 실패이므로 MEDIUM. 다만 ㉮ 각 제약이 자체 가정임을 docstring에 명시하고,
㉯ 최소한 "restart 그룹 마지막 금지"와 "iteration 1 시작 강제"는 근거가 없으므로 제거를 권고한다.

### M3 (MEDIUM) — 파일명 모드 판별이 실제 DAO 산출 파일명과 맞지 않는다

`llr_matrix.py:34`, `:99-102`

```python
_NAME_RE = re.compile(r"LLR_MATRIX_(HD|2SD|3SD)_", re.IGNORECASE)
```

원본이 여는 파일명은 `local_opt.cpp:59` `sprintf(filename, "LLR_MATRIX_%d.txt", OPT_info->matrix_idx);`
즉 **`LLR_MATRIX_0.txt` 형태이고 모드 표기가 없다**. 원본은 모드를 파일이 아니라
`m_param_dec->init_n`에서 가져온다(`decoder.cpp:7088`, `:7103`, `:7118`).

따라서 외부(DAO)에서 받은 파일을 그대로 넣으면 로드 자체가 실패한다.
실측: `LLR_MATRIX_0.txt` → `ValueError: 파일명에서 모드 판별 불가`.

파일명 규약 자체는 2026-08-06 사용자 결정이므로 설계 위반은 아니다. 다만 루트 `CLAUDE.md` ㉰의
"외부 H-matrix와 파라미터를 넣어도 동작"이라는 목표와 부딪히므로, ㉮ 설정(JSON)에서 모드를
명시할 수 있는 우회로를 두거나 ㉯ 반입 시 파일명을 바꿔야 한다는 절차를 실험 README에 적어둘 것.

### M4 (MEDIUM) — CSW row 선택 경로가 배포 데이터로 실행되지 않는다 (본 리뷰에서 별도 검증 완료)

`Input/LLR/LLR_MATRIX_HD_{0,1}.txt` 둘 다 CSW 그룹의 row가 1개라 `needs_csw == False`.
따라서 `llr_matrix.py:173-177`은 현재 설정으로는 한 줄도 실행되지 않는다.

본 리뷰에서 §1-1처럼 합성 파일로 C++ 직역과 대조해 등가임을 확인했으므로 **정확성 문제는 없다**.
다만 본체 반영 시 회귀 테스트가 없으면 이후 수정에서 조용히 깨질 수 있는 구간이다.
CSW 다중 row 파일 1개를 `Input/LLR/`에 테스트용으로 추가하거나, `_test/` 아래 단위 테스트로
남길 것을 권고한다.

### L1 (LOW) — `max_value` / `min_value`의 길이를 검증하지 않는다

`llr_matrix.py:120-121`은 줄 하나를 통째로 받고 길이를 확인하지 않는다.
C++ `local_opt.cpp:93-99`는 정확히 `num_para_each_set`개씩 읽는다.
실측: `max_value`가 2개, `min_value`가 7개인 파일이 **경고 없이 로드된다**.
값 자체는 쓰이지 않으므로 결과에 영향은 없지만, 줄 밀림을 조기에 잡을 검사 하나가 비어 있다.
`if len(max_value) != num_param or len(min_value) != num_param:` 추가를 권고한다.

### L2 (LOW) — 파싱 실패 시 원인을 지목하지 않는 맨 예외가 나온다

`llr_matrix.py:106`, `:109-121`. 실측:

- 잘린 헤더 → `IndexError: list index out of range` (파일명도 필드명도 없음)
- 비정수 토큰(`31.0`) → `ValueError: invalid literal for int() with base 10: '31.0'` (어느 줄인지 없음)
- UTF-8 BOM 파일 → `ValueError: invalid literal for int() with base 10: '﻿4'`

`col_dv_idx`(`:145-147`)나 row 길이 검사(`:132`)는 메시지가 좋은데 헤더 파싱만 무방비다.
㉮ 파일 열 때 `encoding="utf-8-sig"`로 바꾸면 BOM 문제는 사라지고(일반 UTF-8도 그대로 읽힘),
㉯ 헤더 파싱을 `try/except`로 감싸 파일명과 진행 위치를 붙일 것.

### L3 (LOW) — `needs_csw` 프로퍼티가 어디서도 호출되지 않는다

`llr_matrix.py:179-183`. 실험 폴더 전체 grep 결과 호출처 0건.
`summary()`에 CSW 사용 여부를 표시하는 데 쓰거나 제거할 것.

### L4 (LOW) — `_validate`의 총 row 수 검사가 죽은 검사다

`llr_matrix.py:78-79` `if self.group_slices[-1][1] != len(self.row_csw)`.
`load()`가 `total_rows = sum(group_rows)`만큼만 row를 담아 넘기므로(`:125-128`)
이 조건은 `load` 경로에서 항상 거짓이다. 생성자를 직접 호출하는 경로에서만 의미가 있다.

### L5 (LOW) — C++의 조용한 fallback을 에러로 바꾼 지점이 docstring에 일부만 적혀 있다

원본이 조용히 넘어가는 곳은 세 군데인데, docstring(`llr_matrix.py:23-24`)은 dv 미매칭 하나만 언급한다.

| 지점 | C++ 동작 | Python 동작 | docstring |
|---|---|---|---|
| dv 미매칭 | `decoder.cpp:7075` `table_col_idx = 0` 초기값 유지 → **dv 구간 0번 값 사용** | `llr_matrix.py:145` ValueError | 명시됨 |
| ITER 그룹 안에 `it`을 덮는 row 없음 | `decoder.cpp:6974` `table_row_idx = 0` 초기값 유지 → **테이블 전체의 0번 row 사용** (그룹 첫 row가 아님) | `llr_matrix.py:172` ValueError | 미기재 |
| 어느 그룹도 `it`을 덮지 않음 | `decoder.cpp:7048-7049` printf만 하고 `selected_group = -1`로 진행 → `type_each_group[-1]` 범위 밖 접근 | `llr_matrix.py:158` ValueError | 미기재 |

Python 쪽이 모두 더 안전하다. 정책은 일관되므로 docstring에 나머지 두 개를 추가만 하면 된다.

### L6 (LOW) — CSW 선택 주석이 코드 순회 방향과 반대로 읽힌다

`llr_matrix.py:16`, `:173` "아래에서부터 처음으로 csw <= 임계값인 row".
이 표현은 C++(`decoder.cpp:7062` 하향 순회 후 첫 매칭에서 break)을 정확히 서술한 것이고
결과도 같지만, 바로 아래 코드(`:175` `for r in range(a + 1, b)`)는 **위로 올라가며 마지막 매칭을
남기는** 방식이라 처음 읽는 사람이 불일치로 오독한다.
"조건을 만족하는 가장 큰 row 인덱스 (C++ `Get_Cur_LLR_Idx_FILE`의 하향 순회와 등가)"처럼
결과 기준으로 적을 것.

---

## 3. 확인했으나 문제 없던 항목 (재확인 불필요)

- 헤더 개수 필드 검증 범위: `num_dv` 대 `len(dv_from)`(`:123`), `num_group` 대 `len(group_rows)`(`:123`),
  `len(dv_to)`(`:74`), `len(group_type)`(`:76`), row 길이(`:131`), row 개수(`:128`) — `max_value`/`min_value`(L1) 외에는 모두 검사됨
- `row_values` float32 변환: 값 범위가 -1~31이라 float32에서 정확히 표현됨. 비교 연산(`decoder.py:94-96`)에 오차 없음
- 배치 압축과 row 선택의 상호작용: `decoder.py:439`가 `prev_csw`를 `keep`으로 함께 줄이고,
  `row_index`는 프레임별 독립 계산이므로 배치 크기가 결과에 영향을 주지 않음
- `ch_cur = row_ch[row_idx, :, 0]`, `th_cur = row_th[row_idx]`의 축 정렬 — dv-major 배치와 일치
- `os.path.basename` + `re.IGNORECASE` — Windows 경로 구분자 양쪽(`/`, `\`) 모두 처리됨
- `mode.h` 스위치 전제: `__AUTO_LLR_OPT__` 정의(`:22`), `__4_BIT_LLR__` 주석 처리(`:12`),
  `__LLR_TWO_DV3__` 주석 처리(`:9`, 이게 켜져 있으면 `decoder.cpp:7084-7087`에서 dv=3 col<88이
  한 칸 앞 dv 구간을 쓰므로 Python과 갈렸을 것), `__HD_FLOOR_SET__` 주석 처리(`:73`,
  따라서 `decoder.cpp:6980-6983`의 `Adjust_HD_Floor_Type`은 `:8109-8113`에서 상태를 0으로
  두는 no-op이고 AUTO 경로의 그룹 선택에 관여하지 않음) — **네 전제 모두 성립**

---

## 4. 후속 권고 (우선순위 순)

1. `_validate`의 네 제약이 C++ 근거 없는 자체 가정임을 주석/docstring에 명시하고,
   "restart 그룹 마지막 금지"와 "iteration 1 시작 강제"는 제거 (M2)
2. `_group_of_iter`의 정방향 순회가 겹침 금지 제약에 의존한다는 사실을 주석에 남길 것 (M2)
3. 헤더 파싱을 토큰 스트림 방식으로 바꾸거나 줄 구조 전제를 docstring에 명시 (M1)
4. CSW 다중 row 테스트 입력을 회귀용으로 확보 (M4)
5. `encoding="utf-8-sig"`, `max_value`/`min_value` 길이 검사, 헤더 파싱 예외 감싸기 (L1, L2)
6. docstring 보완 3건 (L5, L6, M3의 파일명 규약 안내)
