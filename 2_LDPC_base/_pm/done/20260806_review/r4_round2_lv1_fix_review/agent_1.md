# 수정 후 라이트 재리뷰 — agent_1 [수정 정확성·회귀]

> 작성: 2026-08-07
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/` (LDPC_base 6개 파일 + config.json)
> 정답 기준: `_pm/tasks/20260807_리뷰후속수정/20260807_리뷰후속수정.md` §1~§4
> 대조 원본: `0_LDPC_original/decoder.cpp`, `ecc_top.cpp`, `random.cpp` (읽기 전용)

---

## 0. 결론

**수정의 핵심 3건은 정확하다.** strong_error 2단계 추출은 원본 C++와 결합분포까지 정확히 같고
(카이제곱 실측으로 확인), `_mx_vnu_quantize` 캐스케이드는 C++ 원문과 1080케이스 전수 일치이며,
llr_profile 제거에 잔여 참조가 없다. 회귀도 없다 (fixed_error와 rber의 난수 소비가 수정 전과 동일).

다만 **명세 §4가 요구한 "겹침 거부 + 커버리지 검사"가 그룹 경계 수준에서만 구현되어**
그룹 내부 row 구간의 빈틈과 겹침을 잡지 못하고, **설정 검증에서 `seed: null`이 새어 나가**
시뮬레이션 도중 불친절한 TypeError로 죽는다.

발견: **MEDIUM 3건, LOW 6건** (CRITICAL 0, HIGH 0)

---

## 1. 확인 결과 요약 (요청 항목별)

| 요청 항목 | 판정 |
|-----------|------|
| 1. 명세와 구현 일치 | 코드는 §1~§5 전부 반영. 문서 반영만 미완 (LOW-5) |
| 2. strong_error 2단계 추출 논리와 경계 | **정확** (§2 상세). 경계 10종 전부 정상 |
| 3. `_mx_vnu_quantize` C++ 등가성, dtype, raw==0 sign | **정확** (§3 상세). float32 유지, 1080케이스 전수 일치 |
| 4. `_validate` 커버리지/겹침 논리 | 그룹 경계만 검사 (MEDIUM-1, MEDIUM-2) |
| 5. run.py 검증 항목 | bool 누수 없음, 정규화·라벨·"_" 키 처리 정상. seed null 누수 (MEDIUM-3) |
| 6. 회귀 (fixed_error·rber 난수 소비, decode 3경로) | **회귀 없음** (§4 상세) |

---

## 2. strong_error 2단계 추출 검증 (문제 없음)

### 2-1. 원본 C++ 구조 재확인

`ecc_top.cpp:1867-1880` (파라미터 산출) + `ecc_top.cpp:1707-1723` (2SD 소비) + `random.cpp:343-369`
(`rand_sel_ep` = 부분 Fisher-Yates):

- ㉮ `err_position[0 .. E+c1)`은 크기 `E+c1`의 **균일 순서 표본**이다
- ㉯ flip 구간 `[0, e2+e1)` = 에러 집합 E개
- ㉰ weak 구간 `[e2, e2+e1+c1)` = weak 에러 `e1`개 + weak 정정 `c1`개

따라서 원본의 결합분포는 다음과 같다.

- 1. 에러 집합 = `[N]`에서 균일한 크기 E 부분집합
- 2. 에러 집합이 주어졌을 때 strong 에러 = 그 안의 균일한 크기 `e2` 부분집합
- 3. 에러 집합이 주어졌을 때 weak 정정 = **여집합** 안의 균일한 크기 `c1` 부분집합
- 4. 위 2와 3은 에러 집합 조건부로 서로 독립

### 2-2. Python 구현이 이 결합분포를 실제로 주는가

`channel.py:119-132`의 세 단계를 각각 확인했다.

- ㉮ `err_pos = argpartition(r, E-1)[:, :E]` — `r`이 iid 균일이므로 "가장 작은 E개"의 **집합**은
  균일한 크기 E 부분집합이다 (순서는 비균일하나 이후 집합으로만 쓰임). 원본 1과 일치
- ㉯ `shuffled = rng.permuted(err_pos, axis=1)` 후 `[:, e2:]`를 weak로 — `permuted`는 `err_pos`와
  독립인 새 난수를 쓰고 `out=None`이면 입력을 **제자리 변경하지 않으므로**, 뒤(line 130)에서
  `err_pos`를 다시 쓰는 것이 안전하다. 원본 2와 4에 일치
- ㉰ `r2 = r.copy(); r2[row, err_pos] = 2.0` 후 `argpartition(r2, c1-1)[:, :c1]` — 이것은 `r` 순위로
  `E+1 .. E+c1`번째 위치들이다. `r`이 iid 연속이므로 순위 순열은 균일하고, **"앞 E개가 집합 S"라는
  조건에서 나머지 N−E개의 순위 순열은 S 여집합의 균일 순열**이다. 따라서 다음 `c1`개는 여집합
  안의 균일 부분집합이 된다. `r`이 에러 집합 선택에 이미 쓰였다는 점이 편향을 만들지 않는다.
  원본 3과 일치. `r ∈ [0,1)`이라 2.0으로 미는 것은 항상 유효하다

**실측 검증** (N=6, E=3, e2=2, c1=2, 40만 프레임): 가능한 (에러집합, strong집합, weak정정집합) 조합
180가지가 모두 나타났고 카이제곱 = 160.1 (자유도 179)로 **완전 균일**. 즉 결합분포까지 일치한다.

**블록 편향 실측** (F1 원 증상, 실물 크기 N=37632, N_b=147, E=300/SER=0.3/SCR=0.6, 200프레임):

| 집합 | 카이제곱 (자유도 146) | 상위 2블록 비율 (균일 = 0.0136) |
|------|----------------------|--------------------------------|
| 에러 위치 | 121.2 | 0.0150 |
| strong 에러 | 157.4 | 0.0172 |
| weak 에러 | 122.5 | 0.0153 |
| weak 정정 | 92.1 | 0.0138 |
| strong 정정 | 63.0 | 0.0137 |

F1이 보고한 "상위 2블록 37.1%" 편향은 완전히 사라졌다.

### 2-3. 경계 인덱싱 안전성 (전부 정상)

`E=0`, `E=N`, `E=N−1`, `E=1`, `e2=0`, `e2=E`, `c1=0`, `c1=N`, `SCR=0`, `SCR=1`의 10조합을 실행해
에러 수·strong 에러 수·strong 정정 수가 모두 기대값과 정수 단위로 일치함을 확인했다.

- `E=0`: `argpartition(r, max(-1,0)=0)[:, :0]`이 (B,0)이 되고, `hd[row, 빈배열] ^= 1`과
  `r2[row, 빈배열] = 2.0`이 브로드캐스팅으로 무연산 처리된다
- `c1=0`, `E>0` 분기 모두 `if`로 보호됨
- `c1 = N` (E=0, SCR=0)에서 `argpartition(r2, N-1)`이 유효 범위 상한

`e2`, `c2`의 round 규칙도 C++ `(int)floor(x + 0.5)`와 동일하고, README:93-94의 검증 수치
(E=300 → strong 에러 90, strong 정정 22399)를 재현한다.

---

## 3. `_mx_vnu_quantize` 캐스케이드 검증 (문제 없음)

`decoder.py:63-78` ↔ `decoder.cpp:4080-4119` (`__4_BIT_LLR__` 미정의 = 3-bit 빌드, BF off 분기)

- ㉮ **캐스케이드 등가**: C++는 `temp_m == 0` 분기(4093-4096)와 `!= 0` 분기(4112-4115) 양쪽에서
  같은 4단 캐스케이드를 쓴다. Python의 중첩 `np.where` 3단이 `em = [7,5,3,1]`로 이를 그대로 재현.
  raw −12~+12, c2v {−7,−1,0,1,7}, th 8세트(내림차순·전부동일·전부 −1·비단조·0 포함)의
  **1080 케이스 전수 대조에서 불일치 0건**
- ㉯ **비단조 th에서도 C++와 일치**: 구 지시함수 합 방식은 th=(5,10,3), m=7에서 C++와 갈렸으나
  (r2 agent_1 MEDIUM-1 반례), 캐스케이드는 이 케이스를 포함해 전부 일치
- ㉰ **dtype float32 유지 확인**: `m`(float32) ↔ `th[:, k, None]`(row_th가 float32),
  `em[k]`(np.float32 스칼라), `sgn`(np.float32 스칼라 2개)로 결과가 float32.
  실측 `o.dtype == float32`, 값 집합 `{±1, ±3, ±5, ±7}`
- ㉱ **raw == 0 sign 처리 유지**: C++ `if (VNU_in > 0) temp = temp_m; else temp = -temp_m;`(4098-4099)
  ↔ Python `sgn_z = np.where(c2v > 0, 1.0, -1.0)`. `c2v == 0`이 −1로 가는 것까지 동일
- ㉲ **restart row(-1) 동작 유지**: th=(−1,−1,−1)이면 `m >= -1`이 항상 참이라 전 메시지가 최대
  레벨 7이 된다. 모듈 docstring이 서술한 "순수 syndrome bit-flip iteration"과 일치

기존 두 LLR 파일은 네 dv 구간 모두 내림차순이므로 **이번 교체로 현재 결과가 달라지지 않는다**
(구 지시함수 합과 캐스케이드가 내림차순 입력에서 동일). 회귀 없음.

---

## 4. 회귀 검증 (문제 없음)

- ㉮ **fixed_error 난수 소비 불변**: `_rand_positions`는 docstring만 바뀌었고 본문은 그대로다.
  같은 시드에서 `fixed_error_channel` 호출 후의 rng 상태가 `rng.random((B, N))` 1회 소비 후 상태와
  **비트 단위로 같음**을 실측 확인 (r3 team_a의 재현성 유지 결론 충족)
- ㉯ **rber 난수 소비 불변**: `rng.normal(0, dev, size=cw.shape)` 1회 소비 후 상태와 일치 확인
- ㉰ **decode 3경로 동작**: `two_set`, `column_wise`, `_decode_matrix`(HD_0 restart 포함 / HD_1)
  4조합을 채널 dict 입력과 legacy signed 배열 입력 양쪽으로 실행. 전부 정상 동작하고
  `collect_profile=True`도 유효
- ㉱ **제거 심볼 잔여 참조 0건**: `llr_tables`, `llr_profile`, `_vnu_quantize`, `channel.use`를
  `.py`/`.json`/`.md` 전체에서 검색한 결과 코드 참조 없음 (README의 "제거했다" 서술만 남음).
  `__init__.py`도 정합
- ㉲ **F14 주석 3곳 확인**: `decoder.py:145-148`(two_set 동점 유지),
  `decoder.py:244`(column_wise 동점 유지), `decoder.py:372`(matrix 동점 반전, 변경 금지).
  모듈 docstring:12에도 요약 기재. 명세 §5 충족

---

## 5. 지적 사항

### MEDIUM-1. 커버리지 검사가 그룹 경계만 보고 그룹 내부 row 빈틈을 놓친다

- 위치: `llr_matrix.py:90-101`
- 현상: 검사가 그룹의 `row_iter[a, 0] ~ row_iter[b-1, 1]`만 본다. ITER 타입 다중 row 그룹의
  row가 `[4,4]`와 `[6,6]`이면 그룹 구간은 `[4,6]`으로 잡혀 **로드 시 통과**한다.
- 실측: 그룹 구성 `[[1,3]], [[4,4],[6,6]]`이 검증을 통과하고 `max_iter=6`으로 로드된다.
  이후 `row_index(5, ...)`가 `ValueError: 그룹 2 내 iteration 5 row 없음`을 던진다.
  즉 **파일 로드가 아니라 시뮬레이션 첫 배치 도중에** 죽는다.
- 명세 대비: §4 "그룹 간 겹침 없이 1..max_iter 전 구간이 덮이는지 검사"의 목적은 fail-fast인데,
  그룹 타입 0(ITER)은 정의상 iteration 서브구간을 row로 쪼개는 구조(`row_index`의 ITER 분기)라서
  **정확히 이 경우가 검사에서 빠져 있다**. 현 토이 파일 2개는 전부 CSW 타입 단일 row라
  이 구멍을 실행으로 밟지 않는다 (자동 검증 44건이 못 덮은 영역).
- 수리 방향: 그룹 단위가 아니라 **row 단위로 `covered_end`를 진행**시키면 두 문제(MEDIUM-1, 2)가
  같이 해소된다. 단, CSW 타입 그룹은 모든 row가 같은 iteration 구간을 공유하므로 그룹 타입별
  분기가 필요하다 (CSW 그룹은 그룹 구간 1개로, ITER 그룹은 row별로).

### MEDIUM-2. 겹침 금지도 그룹 경계 수준이라 그룹 내부 row 겹침을 통과시킨다

- 위치: `llr_matrix.py:95-97`
- 실측: 그룹 구성 `[[1,3]], [[4,6],[5,8]]`이 검증을 통과한다. 이후 `row_index`가 정방향 첫 매칭
  규칙으로 iteration 5, 6에 대해 조용히 `[4,6]` row를 고른다.
- 명세 대비: §4 "겹침은 거부(오류). 겹치는 파일은 오류가 있는 파일이다"라는 사용자 확정 원칙이
  그룹 사이에만 적용되고 그룹 안에는 적용되지 않는다. `llr_matrix.py:86-89` 주석이
  "겹침 금지는 `_group_of_iter()` 정방향 첫 매칭의 전제"라고 밝혔는데, `row_index`의 ITER 분기
  (`llr_matrix.py:189-192`)도 같은 정방향 첫 매칭이므로 **같은 전제가 필요한데 검사가 없다**.
- 수리 방향: MEDIUM-1과 동일 (row 단위 순회).

### MEDIUM-3. `seed: null`이 검사를 통과해 시뮬레이션 도중 불친절한 TypeError로 죽는다

- 위치: `run.py:96-97`(채널 seed), `run.py:150-151`(run seed), 소비처 `run.py:212, 218, 230`
- 현상: 두 검사 모두 `is not None`일 때만 `_check_int`를 부르므로 `null`이 통과한다. 이후
  `run_cfg.get("seed", 12345)`와 `ch.get("seed", default_seed)`는 **키가 있고 값이 None이면
  기본값이 아니라 None을 돌려주므로**, `np.random.default_rng([None, int(1e6*p)])`에서
  `TypeError: object of type 'NoneType' has no len()`가 난다.
- 실측: `{"run": {"seed": null}}`과 `{"channels": [{"seed": null, ...}]}` 양쪽 모두 `load_config` 통과,
  `default_rng([None, 200000000])` 호출에서 위 TypeError 확인.
- 파급: H-matrix 로드와 LLR matrix 요약 출력이 끝난 **뒤에** 죽으므로 로그만 보면 원인이
  설정값이라는 것이 드러나지 않는다. 명세 §2 ㉯ "미정의/null이면 에러"의 fail-fast 원칙 위반이고,
  이 수정의 주제(F3 + F19 config checker) 한복판에 남은 구멍이라 지적한다.
- 수리 방향: `_require`로 승격하거나, null을 기본값으로 접는다
  (`v = ch.get("seed"); seed = default_seed if v is None else v`). 어느 쪽이든 명세 §2와 정합한 선택을
  문서에 남길 것.

### LOW-1. null과 비-dict 섹션에서 원시 예외가 그대로 노출된다

- `run.py:138-139` — `"output": {"dir": null}`이면 `setdefault`가 값을 바꾸지 않아
  `resolve(None)`에서 `TypeError: expected str, bytes or os.PathLike object, not NoneType` (실측).
- `run.py:133` — `"decoder": "x"`처럼 dict가 아니면 `AttributeError: 'str' object has no attribute 'get'`
  (실측). `decoder`는 키맵 대상이 아니라는 설계 결정(`run.py:41` 주석) 때문에 타입 검사도 없다.
- 나머지 섹션(최상위, run, channels, output)의 오류 메시지는 전부 명확하고 섹션·키·허용값을
  포함한다. 이 두 건만 원시 예외다.

### LOW-2. label 중복 접미가 사용자가 명시한 label을 조용히 밀어낼 수 있다

- 위치: `run.py:219-225`
- 실측: `channels`의 label이 `["A", "A", "A_2"]`이면 확정 라벨이 `A`, `A_2`, `A_2_2`가 된다.
  즉 **사용자가 명시한 `A_2` 채널의 결과가 `fer_A_2_2.csv`로 가고, `fer_A_2.csv`에는 두 번째
  `A` 채널이 들어간다**. CSV 덮어쓰기(원 결함)는 확실히 막았으나 이름 오귀속이 생긴다.
- `verbose=True`이면 `== channel=... (A_2_2) ==` 출력으로 드러나지만 `verbose=False`면 흔적이 없다.
- 수리 방향: 라벨을 바꿀 때 경고를 출력하거나, 사용자가 명시한 label의 중복은 에러로 거부.
- 같은 자리에 label 문자열 검사가 없어 `"label": "../evil"`도 통과한다 (실측). CSV 경로를
  `os.path.join(out_dir, f"..._{label}.csv")`로 만들므로 상위 폴더 쓰기가 된다.

### LOW-3. fixed_error에만 에러 비트 수 상한 가드가 없다

- 위치: `channel.py:78-88` (가드 없음) ↔ `channel.py:111-112` (strong_error는 `0 <= E <= N` 검사)
- 실측: `points: [999999]`가 설정 검증을 통과하고, 실행 시
  `ValueError: kth(=999998) out of bounds (37632)`라는 numpy 내부 메시지로 죽는다.
- `load_config` 시점에는 `code.N`을 모르지만 `_make_channel_fn`(`run.py:182`)은 `code`를 받으므로
  거기서 막을 수 있다. 두 채널의 오류 품질이 비대칭이라 지적한다.

### LOW-4. `stop_below_fer`에 상한이 없어 1 초과 값이 조용히 "첫 포인트만 측정"이 된다

- 위치: `run.py:146-149`
- 실측: `stop_below_fer: 1.5`가 통과한다. FER은 항상 1 이하이므로 첫 포인트 측정 후 무조건
  `break`가 되어, 나머지 포인트가 조용히 빠진다.
- 명세 §2 ㉰이 이 키의 허용값을 정의하지 않았으므로 "미정의 항목"이지만, 값 제약 도입의 취지
  (조용한 오동작 제거)에 비추어 `0 < v <= 1` 권고.

### LOW-5. 명세 §7이 요구한 문서 반영이 아직 미완이다

- ㉮ `docs/plan.md` §7 #6 — 채널 리스트 복원 이력이 없다. 다만 plan.md:128의 원 문장이 이미
  `channels` 리스트 구조를 서술하고 있어 **내용상 모순은 없다** (구 `channel.use`가 plan.md에
  기록된 적이 없어 되돌릴 것이 없는 상태). 명세가 요구한 "이력 기록"만 빠짐
- ㉯ `_pm/DONE.md` — 2026-08-07 항목 없음 (TODO의 해당 작업도 아직 열려 있어 시점상 자연스러움)
- ㉰ 명세 §5가 요구한 "경로 간 FER 상대 약 7% 계통 오차" 수치가 어디에도 없다.
  `decoder.py:148` 주석은 "계통 오차"라고만 적고 수치를 생략했고 README에도 없다
- ㉱ `llr/_hw_orig_ch.txt` 값 이관이 부분적이다. 후속수정 문서에 옮겨진 것은 `CH_HD 21/14/12/10`과
  `EDGE_MAG 7/5/3/1`뿐이고, 같은 파일의 `TH_HD 24 14 6`(추정값이라는 단서 포함), `BETA 0`,
  `BF_ITERS 0`, "dv2 ch=21 > 최대 외부정보 14라서 예시 부호에서 FER~1" 경고 주석은 옮겨지지 않았다.
  원본 파일이 본체 `2_LDPC_light/llr/`에 그대로 있으므로 **소실은 아니다**. 다만 실험 README:32-33이
  "보존"이라고 단정하므로 본체 반영 때 아카이빙 전에 나머지도 옮길 것

### LOW-6. LLR matrix 헤더가 그룹 0개 또는 row 0개면 원시 IndexError

- 위치: `llr_matrix.py:69`(`self.row_iter[-1, 1]`), `llr_matrix.py:84`(`self.group_slices[-1][1]`)
- `num_group = 0`이거나 총 row가 0이면 검사 메시지 없이 IndexError. 실제 DAO 산출에서는
  생기기 어려운 케이스라 우선순위 낮음.

---

## 6. 문제 없음으로 확인한 범위

- ㉮ **키맵**: 최상위, `run`, `output`, `channels[i]` 4개 섹션에서 미지 키가 섹션명·키·허용 목록과
  함께 거부됨 (실측 4건). `decoder`는 설계상 제외이고 `setup`이 `_` 키를 걸러
  `MinSumDecoder(**kwargs)` TypeError로 넘긴다 (`run.py:171`)
- ㉯ **`_` 키 무시**: 최상위 `_desc`, `run._desc`, `output._desc`, `channels[i]._desc`, `decoder._note`가
  모두 통과하고 소비처에도 새지 않음 (실측). `_visible`이 적용되지 않는 `decoder`도
  `setup`의 컴프리헨션 필터로 덮인다
- ㉰ **필수값**: `H_matrix`, `channels`, `channels[i].type`, `channels[i].points`, strong_error의
  `SER`/`SCR` 부재와 null이 전부 명확한 메시지로 거부됨 (실측 8건)
- ㉱ **bool 누수 없음**: `_check_int`, `stop_below_fer`, `SER`/`SCR`, rber points, 정수 points의
  5개 검사 전부 `isinstance(v, bool)` 선차단. `batch: true`가 "정수여야 함"으로 거부됨 (실측)
- ㉲ **값 제약**: `batch=0`, `batch=1.0`, `batch=null`, `max_frames="100"`, `seed=-1`,
  `stop_below_fer=0`, rber `p=0.6`, fixed `p=-1`, fixed `p=200.5`, `SER=1.5`, `type="fixed"`,
  `decoder.max_iter` 전부 거부 (실측 12건)
- ㉳ **channels 정규화**: 단일 dict → 리스트 1개, 스칼라 points → 리스트 1개 모두 정상 (실측).
  빈 리스트와 문자열은 거부
- ㉴ **seed fallback**: 키가 없을 때 `ch.seed → run.seed → 12345` 순서 유지 확인 (null만 MEDIUM-3)
- ㉵ **sim.py 진입부 가드**: `numbers.Integral` 기반이라 numpy 정수도 통과하고 bool은 차단.
  `batch=0` 무한 대기 시나리오가 막힘
- ㉶ **`_validate` 그룹 경계 케이스 18종 실측**: 정상 연속, 그룹 간 겹침 거부, 그룹 간 빈틈 거부,
  단일 그룹, iteration 1 미시작 거부, `iter_start=0` 허용, 그룹 역순 거부, 그룹 내 역순 거부,
  restart 정상/마지막/다중row/다중iteration/범위밖 거부, 비단조 th 경고, 전부 −1 th 무경고.
  **그룹 경계 수준에서는 판정과 메시지가 모두 명세와 맞다** (그룹 내부만 MEDIUM-1, 2)
- ㉷ **비단조 th 경고**: `UserWarning`으로 정상 발생하고, cp949 콘솔에서도
  `backslashreplace` 덕분에 죽지 않음 (실측)
- ㉸ **`iter_start=0` 허용**: `max(s, 1)` 처리로 0-base 시작 파일을 통과시킨다. 디코더 루프가
  `range(1, max_iter+1)`이라 정합

---

## 7. 검증에 쓴 스크래치패드 스크립트

`C:\Users\yongs\AppData\Local\Temp\claude\...\scratchpad\` 에 t1~t10.py로 보관.
`t1`(결합분포 카이제곱), `t2`(경계 10종), `t3`(블록 균일성), `t4`(C++ 전수 대조),
`t5`(`_validate` 18종), `t7`(config 40종), `t8`(seed null·난수 소비 회귀), `t9`(decode 3경로).

> 정리 메모: 다중 채널 스모크 시험으로 만든 `_test/20260806_setup_구성_실험/Sim_Output_test/`가
> 빈 폴더로 남아 있다 (OneDrive 잠금으로 rmdir 실패). 내용물은 삭제했으니 폴더만 지우면 된다.
