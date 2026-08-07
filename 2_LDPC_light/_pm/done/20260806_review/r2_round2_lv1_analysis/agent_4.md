# Round 2 / agent_4 — V4. 디코더 자체 정확성 (3경로 일관성, 배치 압축, 뷰/사본, dtype)

> 작성: 2026-08-06 23:15:35
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/` 의 `decoder.py`, `pcm.py`, `sim.py`, `llr_matrix.py`
> 관점: Round 1 agent_1 P5/P9/P10 + agent_2 P7/P11/P15
> 범위 제한: C++ 원문 대조는 하지 않았다 (다른 에이전트 소관). Python 코드 자체의 정확성만 판정한다.
> 검증 수단: 코드 정독 + 스크래치패드 실증 (numpy 시맨틱 스니펫, 스칼라 레퍼런스 대조, 배치 압축 불변성 시험)

---

## 0. 결론 요약

| 심각도 | 건수 | 항목 |
|--------|------|------|
| CRITICAL | 0 | 없음 |
| HIGH | 1 | H-1. matrix 경로에서 dv=2 column block 이 구조적으로 절대 반전되지 않음 (현재 `config.json` 실험 FER ≡ 1) |
| MEDIUM | 4 | M-1. `cn_mag_fn` 훅이 matrix 경로에서 미호출<br>M-2. `alpha`/`msg_clip`/`quantize` 가 matrix 모드에서 무경고 무시<br>M-3. genie 동점(`total == 0`) 규칙이 경로별로 다르고 signed 경로는 항상 낙관 방향<br>M-4. `assert` 3곳이 `python -O` 에서 사라져 shape 불일치 입력이 조용히 성공 판정 |
| LOW | 4 | L-1. `sim.py` `max_frames=0` ZeroDivisionError, `max_iter<=0` 무경고 전 프레임 실패<br>L-2. two_set 의 deg-1 row 방어값이 profile 모드에서 column_wise 와 도메인 불일치<br>L-3. `broadcast_to(...).astype(...).copy()` 의 중복 사본<br>L-4. 성능: 실물 규모 max_iter=120 에서 약 2.7 frame/s |

**리뷰 의뢰서가 지목한 핵심 확인 대상은 전부 "문제 없음"으로 판정했다.** 배치 압축 배열 목록의 완전성(3경로 전수), `fill()` 의 뷰/사본 안전성, `np.where` 재대입 순서 의존성, `csum` 이중 XOR 순서, CSW 모드에서의 배치 압축 결과 불변, dtype 전반이 모두 실증으로 통과했다 (§2). 위 지적 5건은 그와 별개로 발견된 항목이다.

---

## 1. 발견 사항

### H-1 (HIGH). matrix 경로에서 dv=2 column block 이 구조적으로 절대 반전되지 않는다

**위치**: `decoder.py:68`, `decoder.py:353`, `decoder.py:388`, `decoder.py:398`

**산술 근거**

`_decode_matrix` 의 flip 도메인에서 한 column block 의 판정식은 다음과 같다.

- ㉮ `decoder.py:388` — `total` 초기값은 테이블 채널값 `ch_cur[dvmap[j]]` 하나뿐이다 (항상 양수 방향)
- ㉯ `decoder.py:392` — 더해지는 C2V 는 `min1`/`min2` 에서 오는데, 이 둘은 `RESET = self._edge_mag[0] = 7` 로 초기화되고 이후에도 `_mx_vnu_quantize` 가 내놓는 `{7,5,3,1}` 값만 들어간다. 즉 `|c2v| <= 7` 이 항상 성립한다
- ㉰ `decoder.py:398` — `flip = total <= 0`

따라서 degree `dv` 인 column 이 한 번이라도 반전될 수 있으려면 `ch_table[dv] <= 7 * dv` 여야 한다. `self._edge_mag` 는 `decoder.py:68` 에서 `[7, 5, 3, 1]` 로 하드코딩되어 있으므로 이 상한은 입력 파일과 무관하게 고정이다.

**입력 데이터 실측** (스크래치패드 `t_edge.py`)

```
LLR_MATRIX_HD_0.txt / HD_1.txt 공통
  dv=11: ch= 1.0   7*dv= 77   ok
  dv=4 : ch=10.0   7*dv= 28   ok
  dv=3 : ch=13.0   7*dv= 21   ok
  dv=2 : ch=28.0   7*dv= 14   FLIP 불가 (total 이 항상 >= 14 > 0)
```

restart row (HD_0 의 iteration 2, `ch=-1`) 만 예외이고, `config.json` 이 지정한 `LLR_MATRIX_HD_1.txt` 에는 restart 가 아예 없다 (`restart set()`).

**실측 결과**

예시 부호 `example_18x147_z256.qc` 의 column degree 분포는 `{2:17, 3:1, 4:129}` 이다. dv=2 column block 17개 = 4352 bit = 전체 codeword 의 11.6% 다.

```
(batch 16, HD_1, max_iter=20)
  에러 1개를 dv=4 column 에만 심음 : 성공 16/16
  에러 1개를 dv=2 column 에만 심음 : 성공  0/16
  에러 1개를 전체에 무작위로 심음  : 성공 10/16
  에러 20개를 전체에 무작위       : 성공  1/16
```

전체 무작위 300 bit 에러(현재 `config.json` 의 `fixed_error` 포인트)에서는 배치 전원 실패한다. 즉 **현재 저장소에 들어 있는 설정 그대로 `run.py` 를 돌리면 FER 이 항상 1.0 이며, 어떤 파라미터를 바꿔도 dv=2 에 에러가 하나라도 들어간 프레임은 영구히 실패한다.** 반면 같은 입력을 two_set/column_wise 경로에 넣으면 정상 수렴한다 (n_iter 8~17).

**판정과 후속**

원인 후보는 두 갈래이며 코드만으로는 가릴 수 없다.

- ㉮ 도메인 불일치: `_edge_mag` 가 3-bit VNU 출력 도메인 `{7,5,3,1}` 인데 테이블의 `ch`/`th` 는 5-bit 도메인(파일 헤더 `max_value 31`)이다. C++ 에서 두 값이 같은 가산 도메인에 놓이는지 확인이 필요하다
- ㉯ 입력 데이터 문제: LLR matrix 2개가 자작 토이 값이라 dv=2 의 `ch` 만 비현실적으로 큰 것일 수 있다

어느 쪽이든 **Python 쪽에서 이 조건을 검출하는 장치가 전혀 없다는 것이 문제다.** `ch_table[dv] > edge_mag[0] * dv` 인 dv 구간이 있으면 그 degree 의 column 은 영원히 정정 불가이므로, `MinSumDecoder.__init__`(`decoder.py:56-70`)에서 `self._col_dv` 를 만들 때 함께 검사해 경고하거나 막을 수 있다. 근본 원인 판정(㉮ 대 ㉯)은 P1 담당 에이전트의 C++ 대조 결과에 넘긴다.

---

### M-1 (MEDIUM). `cn_mag_fn` 훅이 matrix 경로에서 호출되지 않는다

**위치**: `decoder.py:105-108` (정의), `decoder.py:163`, `decoder.py:262` (호출), `decoder.py:392` (미호출)

모듈 docstring `decoder.py:15` 는 `cn_mag_fn` 을 "논문 아이디어 훅(C2V magnitude 변형)"으로 선언한다. two_set 과 column_wise 는 C2V magnitude 를 만들 때 이 함수를 통과시키지만 `_decode_matrix:392` 는 `mag` 를 그대로 쓴다.

실증 (`t_opt.py`): `cn_mag_fn` 을 "항상 0 반환"으로 오버라이드한 서브클래스를 만들어 같은 입력을 넣으면,

```
matrix 경로            : cn_mag_fn 호출 0회,  n_iter 변화 없음
column_wise(non-matrix): cn_mag_fn 호출 2212회
```

matrix 경로가 원본 C++ 대응 정본이고 앞으로 논문 아이디어를 이식할 주 경로인데, 그 경로에서만 훅이 죽어 있다. 서브클래스가 훅을 갈아끼워도 **예외도 경고도 없이 무시**되므로 "아이디어를 적용했는데 FER 이 안 변한다"는 형태로만 드러난다. matrix 모드는 `beta=0` 이라 기본 구현은 항등이므로 현재 결과는 틀리지 않지만, 훅의 존재 이유가 사라진 상태다.

---

### M-2 (MEDIUM). `alpha`/`msg_clip`/`quantize` 가 matrix 모드에서 무경고로 무시된다

**위치**: `decoder.py:43-47`, `decoder.py:56-70`

생성자는 `llr_profile` 과 `llr_matrix` 동시 지정만 `ValueError` 로 막고(`decoder.py:58-59`), `beta` 는 0 으로 덮어쓴다(`decoder.py:69`). 그러나 `alpha`, `msg_clip`, `quantize` 는 그대로 저장되고 `_decode_matrix` 에서 한 번도 읽히지 않는다.

실증 (`t_opt.py`): `alpha=0.5, msg_clip=3.0, quantize=False` 를 지정해도 기본 디코더와 `n_iter` 가 완전히 동일하다.

`run.py:82` 가 JSON 의 `decoder` 하위 키를 `MinSumDecoder(**dec_cfg)` 로 그대로 넘기므로, 사용자가 `config.json` 에 `"alpha": 0.75` 를 써도 아무 반응 없이 무시된다. `max_iter` 는 `run.py:48-50` 에서 명시적으로 막는데 같은 성격의 다른 키는 통과하는 비대칭이다.

---

### M-3 (MEDIUM). genie 동점 규칙이 경로별로 다르고, signed 경로는 all-zero 전제에서 항상 낙관 방향이다

**위치**: `decoder.py:170` (two_set), `decoder.py:268` (column_wise), `decoder.py:398` (matrix)

- two_set 과 column_wise: `frame_err |= (total < 0).any(axis=-1)` — 엄격 부등호. `total == 0` 은 "비트 0" 으로 판정된다
- matrix: `flip = total <= 0` — 동점 반전

all-zero codeword 만 송신하므로 signed 두 경로에서는 **동점이 언제나 정답 쪽으로 떨어진다**. 실제 디코더라면 동점은 임의 결정(기대값으로 절반이 오류)인데, 여기서는 100% 정답으로 집계된다.

동점 발생 빈도 실측 (`t_tie.py`, 예시 부호, 300 bit 에러, batch 16, `quantize=True`, `beta=1.0`)

```
two_set     : total == 0 이 전체 판정의 0.1856% (total < 0 은 1.2404%)
column_wise : total == 0 이 전체 판정의 0.0941% (total < 0 은 0.5448%)
```

`quantize=True` 로 LLR 이 정수격자에 놓이므로 동점이 드물지 않다 (프레임당 약 70 bit).

영향 측정 (`t_tie2.py`, 판정을 `<` 에서 `<=` 로 바꿔 비교)

```
nerr=200 column_wise: n_iter <  = [6 6 6 7 6 6 6 6 ...]
                      n_iter <= = [6 6 7 8 6 6 7 6 ...]   (프레임 다수가 +1~2)
nerr=400 column_wise: 성공 프레임 수는 동일, n_iter 만 이동
```

측정 표본에서 FER 자체는 바뀌지 않았고 `avg_iter_ok` 만 낙관 쪽으로 치우친다. 다만 세 경로를 나란히 비교할 때 matrix 경로는 동점을 오류로 세고 signed 경로는 정답으로 세므로, 경로 간 `n_iter`/FER 비교에 계통 오차가 들어간다. 도메인이 다르니 규칙이 달라도 된다는 판단이라면 그 근거를 코드 주석이나 문서에 남길 대상이다.

---

### M-4 (MEDIUM). `assert` 3곳이 `python -O` 에서 사라져 shape 불일치 입력이 조용히 성공 판정된다

**위치**: `decoder.py:129`, `decoder.py:230`, `decoder.py:349`

세 경로 모두 `assert N_b == code.N_b and z == code.z` 하나로 입력 shape 를 지킨다.

실증 (`t_opt.py` 를 `python -O` 로 실행): 부호보다 column block 이 3개 많은 입력을 만들고 **초과분 column 을 전부 에러 비트로 채웠는데도** 결과는 다음과 같다.

```
N_b 초과 입력: success=[True True]  n_iter=[1 1]
```

column 루프가 `range(code.N_b)` 라 초과분을 읽지 않고, genie 도 그 범위만 검사하므로 오류가 통째로 사라진다. 예외도 나지 않는다. 프레임 수가 긴 배치 실험에서 조용히 잘못된 FER 을 내는 형태다. `assert` 대신 `raise ValueError` 로 바꾸면 해소된다.

---

### L-1 (LOW). `sim.py` 와 `max_iter` 경계

- ㉮ `sim.py:24` — `fer = errors / frames`. `max_frames=0` 이면 while 루프가 한 번도 돌지 않아 `frames=0` 이 되고 `ZeroDivisionError` 가 난다 (실측 확인)
- ㉯ `decoder.py:146`, `decoder.py:247`, `decoder.py:368` — `max_iter <= 0` 이면 루프가 실행되지 않고 `success` 전부 False, `n_iter` 전부 0 으로 정상 반환된다. "전 프레임 실패" 와 구분되지 않는다 (실측 확인)
- ㉰ `sim.py:27` — 전 프레임 실패 시 `avg_iter_ok = 0 / max(1, 0) = 0.0`. "데이터 없음" 이 0.00 으로 출력된다

`b = min(batch, max_frames - frames)` (`sim.py:18`) 와 `avg_iter_ok = iter_sum / max(1, frames - errors)` (`sim.py:27`) 자체는 정확하다. 실패 프레임 `n_iter=0` 규약과 맞물려 `iter_sum` 이 성공 프레임 합과 정확히 일치하고, 분모 `frames - errors` 가 성공 프레임 수와 일치한다 (`t_edge.py` 로 확인: `max_frames=100, batch=64` → `frames=100`, `avg_iter_ok=3.0`).

`max_frame_errors` 종료 조건은 배치 경계에서만 검사하므로 목표 에러 수를 초과 달성한 채 끝난다. 이는 오히려 고전적인 역이항 편향을 줄이는 방향이라 문제로 보지 않는다. 다만 현재 `config.json` 의 `max_frames=256`, `max_frame_errors=10` 조합은 최대 4배치라 통계량이 매우 얇다 (별도 관점 소관).

---

### L-2 (LOW). two_set 의 deg-1 row 방어값이 profile 모드에서 column_wise 와 도메인이 어긋난다

**위치**: `decoder.py:206-207` 대 `decoder.py:233`

- two_set: `old_min1 = np.minimum(new_min1[keep], self.msg_clip)` — 상한이 항상 `msg_clip` (기본 31.0)
- column_wise: `RESET = self._edge_mag[0] if self.profile is not None else self.msg_clip` — profile 모드에서는 7

같은 `llr_profile` 을 쓰면서 스케줄만 바꾸면 min2 미설정 row 의 magnitude 가 31 대 7 로 갈린다. `_INF` 가 `cn_mag_fn` 에 도달하지는 않으므로(항상 `msg_clip` 으로 먼저 잘림) 오버플로 위험은 없다. 예시 부호의 row degree 는 `{30:5, 31:13}` 이라 deg-1 row 가 없어 현재 영향은 0이다. `llr_profile` 경로가 제거 후보로 선언된 상태이므로 제거되면 함께 사라진다.

---

### L-3 (LOW). `broadcast_to(...).astype(...).copy()` 의 중복 사본

**위치**: `decoder.py:387-388`

`astype` 은 기본이 `copy=True` 라 이미 쓰기 가능한 새 배열을 만든다. 뒤의 `.copy()` 는 column 마다 (Ba, z) 배열을 한 번 더 복사한다. 프로파일에서 `ndarray.copy` 2940회(= 147 column x 20 iteration)로 잡히며 비중은 작다 (0.027s / 3.9s).

---

### L-4 (LOW, 참고). 성능: 실물 규모 병목

실측 (`t_edge.py`, `cProfile`, batch=64, N_b=147, z=256, E=553, max_iter=20, matrix 경로)

```
tottime  ncalls  대상
 2.155        1  _decode_matrix 본체 (파이썬 루프 왕복 자체)
 1.039    11060  _mx_vnu_quantize          (= 553 edge x 20 iteration)
 0.253    36141  ndarray.astype
 0.246    22673  np.roll                   (= edge 당 2회 + syndrome 553회)
 총 cumtime 3.906s
```

- ㉮ 처리량은 batch 64 / max_iter 20 기준 약 16.4 frame/s 다. 문서상 실물 `max_iter=120` 이면 약 2.7 frame/s 이고, FER 1e-3 지점에서 프레임 에러 50건을 모으려면 약 5시간이 든다
- ㉯ 최대 비중은 numpy 호출 자체가 아니라 **Python 인터프리터 왕복**이다 (column 147 x edge 평균 3.8 x 2 pass x iteration). edge 루프를 row 단위 배치 연산으로 묶는 것이 유일한 큰 개선 축이다
- ㉰ `_mx_vnu_quantize` 가 단일 함수로는 최대(30%)이며, 안에서 `np.abs` 1회, 비교 3회, `astype(int8)` 1회, fancy index 1회, `np.where` 2회, `zero.any()` 전수 스캔 1회를 돈다. `zero.any()` 는 `raw == 0` 배열을 이미 만든 뒤의 가드라 절약 효과가 작다
- ㉱ 메모리는 `esgn` (B, E, z) uint8 이 batch 64 / E 553 / z 256 에서 약 9 MB 로 부담이 아니다

배치 압축은 잘 작동한다. dv=4 에만 에러를 심어 iteration 1 에 전원 수렴하는 경우 0.1s 로 끝나고, 전원 실패면 1.6s 로 full cost 를 낸다.

---

## 2. "문제 없음" 으로 확인한 범위 (의뢰서 핵심 확인 대상)

### 2-1. 배치 압축 시 줄이는 상태 배열 목록의 완전성 — 3경로 전수 문제 없음

경로별로 iteration 을 넘어 살아남는 상태를 전수 대조했다.

| 경로 | iteration 간 유지 상태 | 압축 코드 | 판정 |
|------|----------------------|-----------|------|
| two_set (`decode_batch`) | `ch`, `old_min1`, `old_min2`, `old_pos`, `old_sgnp`, `old_esgn`, `idx_active` | `decoder.py:204-210` | 전부 포함, 누락 없음 |
| `_decode_column_wise` | `ch`, `min1`, `min2`, `pos`, `csum`, `esgn`, `idx_active` | `decoder.py:309-312` | 전부 포함, 누락 없음 |
| `_decode_matrix` | `r_bit`, `synd`, `prev_csw`, `min1`, `min2`, `pos`, `csum`, `esgn`, `idx_active` | `decoder.py:438-441` | 전부 포함, 누락 없음 |

`success`/`n_iter` 는 원본 인덱스 기준이고 `idx_active[ok]` 로만 접근하므로 압축 대상이 아니다. two_set 의 `new_*` 5종은 iteration 시작마다 `Ba = ch.shape[0]` 로 새로 할당되므로 압축 대상이 아니다 (`decoder.py:147-152`).

**실증 (배치 대 단일 프레임 대조)**: 같은 입력을 (ㄱ) 배치로 한 번에, (ㄴ) 프레임마다 B=1 로 따로 디코딩해 `success`/`n_iter` 를 비교했다. 상태 배열이 하나라도 누락되면 압축이 일어나는 순간 프레임이 어긋나므로 즉시 드러난다.

```
프레임별 에러 수를 [5, 20, 60, 120, 200, 300, 500, 900] 로 달리해
iteration 마다 일부만 빠지도록(부분 압축이 실제로 일어나도록) 구성

matrix HD_0    batch n_iter=[1 0 0 0 0 0 0 0]  single 동일   MATCH
matrix HD_1    batch n_iter=[1 0 0 0 0 0 0 0]  single 동일   MATCH
two_set        batch n_iter=[2 3 4 7 10 15 0 0] single 동일  MATCH
column_wise    batch n_iter=[2 2 3 5 6 8 0 0]  single 동일   MATCH
```

### 2-2. `min1.fill(RESET)` 등 in-place 연산의 뷰/사본 안전성 — 문제 없음

**위치**: `decoder.py:374-379`

`min1`, `min2`, `pos`, `csum`, `esgn` 는 직전 iteration 끝(`decoder.py:440-441`)에서 `min1[keep]` 형태의 **불리언 인덱싱**으로 만들어진다. numpy 의 advanced indexing 은 `keep` 이 전부 True 여도 항상 새 배열을 만든다.

```
a = np.arange(12.).reshape(3,4); keep = np.array([True,True,True])
b = a[keep]
b.base is a          -> False
np.may_share_memory(a, b) -> False
b.fill(9); a[0,0]    -> 0.0  (원본 불변)
```

첫 iteration 에서는 `it > 1` 조건이 막아 `fill` 자체가 실행되지 않는다. 또한 이 배열들의 유일한 참조자가 함수 지역 변수이므로 외부 공유 위험도 없다. `restart` 처리는 안전하다.

### 2-3. `m1, m2, p = min1[:, i, :], ...` 뷰 + `np.where` 재대입 — 문제 없음

**위치**: `decoder.py:285-298` (column_wise), `decoder.py:412-425` (matrix), `decoder.py:188-192` (two_set)

- ㉮ `m1/m2/p` 는 기본 슬라이싱이라 뷰다. 그러나 `remove old` 분기에서 `m1 = np.where(...)` 가 실행되면 그 시점에 새 배열로 재바인딩되어 뷰 성질이 끊긴다
- ㉯ `edge clear` 분기(뷰가 그대로 남는 경로)에서도 `np.where` 가 RHS 를 먼저 완전히 평가한 뒤 슬라이스에 대입하므로 aliasing 이 생기지 않는다. 대입 순서(`min2` → `min1` → `pos`)도 각 RHS 가 아직 갱신되지 않은 값만 읽도록 배치되어 있다
- ㉰ 의뢰서가 우려한 "같은 column 에 같은 row 가 두 번" 은 base matrix 표현상 불가능하다. edge 는 `base` 의 nonzero 원소에서 만들어지므로 `(i, j)` 쌍이 유일하고, 따라서 한 column 안의 edge 들은 서로 다른 row 를 가진다. 예시 부호 147개 column block 전수 확인 결과 중복 0건

### 2-4. `csum` 이중 XOR 순서 의존성 — 문제 없음

**위치**: `decoder.py:287` (remove 의 `csum ^= esgn[e]`) 와 `decoder.py:297` (insert 의 `csum ^= sgn_new`), matrix 는 `decoder.py:414`, `decoder.py:424`

XOR 은 교환법칙이 성립하고, 두 XOR 사이에서 `csum[:, i, :]` 를 읽는 코드가 없다. 같은 column 안의 다른 edge 는 §2-3 ㉰ 에 의해 항상 다른 row 를 건드리므로 간섭하지 않는다. 같은 iteration 의 뒤쪽 column 이 이 row 를 읽을 때는 두 XOR 이 모두 반영된 값을 보며, 이는 column-wise 스케줄의 의도다.

### 2-5. 독립 스칼라 레퍼런스와의 전면 대조 — 3경로 전부 일치

§2-2 ~ §2-4 를 종합 검증하기 위해, numpy 를 전혀 쓰지 않는 **순수 파이썬 스칼라 구현**을 세 경로 각각에 대해 따로 작성해 대조했다. 스칼라판은 프레임/lane 을 명시적으로 루프하고 상태를 중첩 리스트로 들고 있어 뷰, 브로드캐스트, 순서 의존성이 원리적으로 개입할 수 없다. shift 도 `np.roll` 대신 `(k ± s) % z` 인덱스 산술로 독립 구현했다.

```
toy 부호 (M_b=4, N_b=8, z=4, col_deg [3,3,3,3,3,2,2,2], E=21)

matrix 경로      : 30 trial x 6 frame,  불일치 0건 (성공 81/180 으로 성공과 실패가 섞임)
two_set 경로     : 25 trial x 6 frame,  불일치 0건
column_wise 경로 : 25 trial x 6 frame,  불일치 0건 (두 경로 합산 성공 256)
```

성공과 실패가 섞인 배치라 iteration 마다 부분 압축이 실제로 일어나는 조건이다. 이 대조가 통과했다는 것은 min1/min2/pos 갱신 규칙, remove/insert XOR 순서, `np.roll` 방향(VN 정렬 ↔ CN 정렬), `prev_csw` 프레임별 처리, 배치 압축이 전부 스칼라 정의와 동일함을 뜻한다.

### 2-6. CSW 모드에서 프레임별 row 선택 x 배치 압축 — 문제 없음

Round 1 agent_2 P6 ㉳ 가 지적한 대로, 예시 LLR matrix 2개는 CSW 그룹의 row 가 1개씩이라 이 경로가 한 번도 실행되지 않는다. 그래서 **CSW 다중 row 그룹을 직접 만들어** 시험했다 (임계 20/10/4 의 3-row CSW 그룹).

```
row_index 동작 확인: csw= 0->row3,  4->row3,  5->row2, 10->row2,
                     11->row1, 20->row1, 50->row1(그룹 첫 row fallback)

40 trial x 8 frame, 배치 대 단일 프레임 대조: 불일치 0건
같은 iteration 에서 프레임마다 서로 다른 row 가 선택된 사례 16종 관측
  예: (it=2, rows {1,2,3}), (it=3, rows {1,2}), (it=4, rows {1,2}) 등
```

`prev_csw` 가 프레임별 상태(`csum ^ synd`)에서만 나오고 배치 내 다른 프레임에 의존하지 않으므로, 프레임을 제거해도 남은 프레임의 row 선택이 변하지 않는다. `row_index` 반환 크기도 `Ba = len(csw)` 로 압축된 `prev_csw` 길이를 그대로 따라가며(`llr_matrix.py:167`, `llr_matrix.py:174`), `ch_cur (Ba, num_dv)` 와 `th_cur (Ba, num_dv, 3)` 이 매 iteration 재계산되므로 크기 어긋남이 없다 (`decoder.py:380-382`).

**"배치 압축 = 결과 불변" 주장은 3경로 모두에서 성립한다.** 유일한 배치 전역 연산은 `_vnu_quantize`/`_mx_vnu_quantize` 의 `if zero.any():` 가드(`decoder.py:85`, `decoder.py:99`)인데, 이는 조건이 거짓일 때 뒤따르는 `np.where` 가 어차피 항등이므로 결과를 바꾸지 않는 순수 최적화다.

### 2-7. dtype 안정성 — 문제 없음

스크래치패드 실측 (numpy 1.26.4, Python 3.11, Windows/AMD64, `np.int_` 는 int32)

| 확인 항목 | 위치 | 결과 |
|-----------|------|------|
| `uint8 ^= bool` in-place | `decoder.py:186` | 결과 dtype uint8, 정상 동작 |
| `uint8 ^ bool` (genie) | `decoder.py:399` | uint8, 값 0/1 정상 |
| `np.where(bool, int64스칼라, int32배열)` → int32 슬라이스 대입 | `decoder.py:192`, `decoder.py:296`, `decoder.py:423` | 결과 int32, 값 손실 없음 (edge index 는 항상 E 미만) |
| `lvl` 인덱스 범위 | `decoder.py:81`, `decoder.py:94-95` | 각 비교가 0/1 을 더하므로 **th 값과 무관하게 항상 0~3**. `th=(-1,-1,-1)` 이면 lvl=0(최대 레벨), th 가 오름차순으로 뒤집혀도 0~3 유지. `_edge_mag` 길이 4 를 벗어날 수 없음 |
| `-0.0` 처리 | `decoder.py:83-87`, `decoder.py:97-101` | `np.rint(-0.4)` 는 `-0.0` 을 낸다. `raw == 0` 이 `-0.0` 도 True 로 잡아 sign 을 `c2v` 에서 가져오므로 `+0.0` 과 동일 취급. `(v2c < 0)` 도 `-0.0` 에 False 를 주고 `np.abs` 가 `0.0` 을 주어 부호/크기 모두 일관 |
| uint8 합산 오버플로 | `decoder.py:427` | `(csum ^ synd).sum()` 이 uint32 로 승격(최대 4.29e9). 실물 최대값 `M_b*z` 는 예시에서 4608, 실물 규모에서도 수만 수준이라 여유 충분. 이후 `.astype(np.int64)` |
| `err_bits` 누적 | `decoder.py:172`, `decoder.py:402` | int64 배열에 int32/uint32 를 in-place 가산. 안전 캐스팅 |
| float32/float64 혼용 | `channel.py` 대 `decoder.py` | 현재 `channel.py` 는 배열이 아니라 dict 를 반환하고 `hd`/`sd` 가 uint8 이라 **float64 가 디코더로 새어들어가는 경로가 없다**. legacy 어댑터(`decoder.py:124`)도 float32 리터럴을 쓰고, `ch = ch_llr.astype(np.float32, copy=True)` 로 한 번 더 고정 |
| `_INF` 오버플로 | `decoder.py:19`, `decoder.py:108` | `_INF` 는 `new_min2` 초기값으로만 쓰이고, `cn_mag_fn` 에 넘어가는 것은 항상 `np.minimum(new_min*[keep], msg_clip)` 을 거친 `old_*` 다. `alpha` 를 곱해도 inf 가 될 수 없음 |
| 입력 배열 훼손 | `decoder.py:133`, `decoder.py:345` | two_set/column_wise 는 `astype(copy=True)`, matrix 는 `np.asarray` 후 읽기만 하고 in-place 쓰기가 없다. 호출자 배열이 변형되지 않음 |
| `pcm.syndrome` dtype | `pcm.py:81` | `dtype=bits.dtype` 이라 bool 입력이면 bool syndrome 이 되지만, `decoder.py:345` 가 `np.asarray(..., np.uint8)` 로 강제하므로 실제 경로에서는 항상 uint8. `roll(-s)` 방향도 디코더의 `roll(+s)` 와 정합 (§2-5 스칼라 대조로 검증) |

### 2-8. `sim.py` 집계 규약 — 문제 없음 (L-1 의 경계 사례 제외)

- ㉮ `n_iter=0`(실패) 규약과 `avg_iter_ok = iter_sum / max(1, frames - errors)` 는 정합한다. 실패 프레임이 `iter_sum` 에 0 을 기여하므로 분자는 성공 프레임 iteration 합과 정확히 같고, 분모 `frames - errors` 는 성공 프레임 수와 정확히 같다
- ㉯ `b = min(batch, max_frames - frames)` 는 while 조건 `frames < max_frames` 덕에 항상 1 이상이며, 최종 `frames` 가 `max_frames` 를 넘지 않는다 (`max_frames=100, batch=64` → `frames=100` 실측)
- ㉰ 배치 압축은 `decode_batch` 내부에서만 일어나고 반환 배열은 항상 원래 배치 크기 B 이므로, `sim.py` 의 `frames += b` 와 어긋나지 않는다

---

## 3. Round 3 로 넘기는 것

- ㉮ H-1 의 근본 원인 판정(도메인 불일치인가 토이 데이터인가)은 C++ 대조가 필요하다. `_edge_mag = [7,5,3,1]` 하드코딩(`decoder.py:68`)과 파일 헤더 `max_value 31` 의 도메인 관계, 그리고 C++ 이 dv=2 column 을 특별 취급하는지가 확인 대상이다
- ㉯ M-3 의 동점 규칙 차이가 의도인지(도메인이 다르니 달라도 된다) 아니면 signed 두 경로도 `<=` 로 맞춰야 하는지는 설계 결정이다
- ㉰ M-1 은 "세 경로를 계속 유지할지" (Round 1 agent_2 P10 ㉲) 와 묶어서 판단할 사항이다. 경로를 하나로 정리하면 자연히 해소된다
