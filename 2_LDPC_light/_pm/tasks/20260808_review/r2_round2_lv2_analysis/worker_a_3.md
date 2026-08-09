# Worker A-3 — 관점 B 후반: magnitude 0 레벨 도입의 디코더 파급 + RESET 변화

작성: 2026-08-08 14:50:57

## 요약

균일 n-bit 모드는 `edge_mag = [top_level..1, 0]`으로 VNU 출력에 magnitude 0 레벨을 만든다.
이 변화가 만드는 파급을 정적 읽기와 실측으로 확인했다. 실측은 전부
`Input/H_matrix/example_18x147_z256.qc` (base 18x147, z=256, col degree {2:17, 3:1, 4:129}),
fixed_error 채널, max_iter 20으로 수행했다.

핵심 결과 세 가지.

- ㉮ **`channel_llr`가 `top_level`의 정수배면 FER이 1.0으로 붕괴한다** (HIGH). 4-bit에서
  ch=6은 FER 0.0, ch=7(=top_level)은 FER 1.0, ch=8은 0.219. run.py 검증은 이 값을 통과시킨다.
- ㉯ **`-0.0` 부호 소실은 실재하지만 현재 스케줄에서는 결과에 닿지 않는다** (MEDIUM, 잠복).
  전체 C2V의 최대 3.06%가 잘못된 부호를 받지만 그 전부가 magnitude 0이었다. 다만 이 면역은
  `_column_order`가 전 column을 매 iteration 갱신하는 데에 기댄 우연이며, 교체 지점을
  부분 갱신 스케줄로 바꾸자 magnitude가 0이 아닌 C2V 3,390건이 잘못된 부호를 받았다.
- ㉰ **min1 == 0 침묵 체크노드는 원본 HW에 대응이 없고 FER을 나쁘게 만든다** (MEDIUM).
  C++은 min1의 최소값(V_VERY_WEAK=0)을 EDGE_MAG_1=1로 되돌리므로 C2V magnitude가 0이 되는 일이
  없다. 0 레벨을 뺀 구성(edge_mag 최소 1)이 FER 0.1875 대 0.1211로 더 좋았다.

---

## 확인 항목별 판정

### ㉮ `-0.0` 부호 판정 (실측)

**numpy 동작 확인.**

| 식 | 결과 |
|----|------|
| `np.float32(-1.0) * np.float32(0.0)` | `-0.0` (signbit=True) |
| `(-0.0) < 0` | `False` |
| `np.signbit(-0.0)` | `True` |
| `np.roll([-0.0, 0.0, -1.0, 1.0], 1)`의 signbit | `[0 1 0 1]` (roll이 부호 비트를 그대로 옮긴다) |

따라서 `_vnu_quantize`가 `sgn=-1, mag=0`으로 만든 `-0.0`은 `np.roll`을 지나 그대로 도착하고,
`_process_column:295`의 `(vnu_out < 0)`에서 0(양)으로 기록된다.

**발생 빈도 실측** (균일 6-bit, ch=8, n_err=300, 16 frames, 20 iteration, 양자화 출력 17,979,136개).

| 항목 | 개수 | 비율 |
|------|------|------|
| `raw == 0` 원소 | 9,986 | 0.0555% |
| `mag == 0` 원소 | 9,986 | 0.0555% |
| `mag == 0` 이면서 `sgn == -1` (부호 소실) | 3,847 | 전체의 0.0214%, mag0의 38.5% |

`raw == 0` 개수와 `mag == 0` 개수가 정확히 같다. 균일 모드의 th가 `[top..1]` 정수이고 flip 도메인
값이 전부 정수이므로 `mag == 0`과 `raw == 0`이 동치이기 때문이다.

**CSW와 C2V sign 재구성으로의 전파 추적 (실측).** `edge_sgn`과 나란히 "기록된 sign이
`_vnu_quantize`가 계산한 sign과 다른 edge" 비트를 유지하고, `check_sum`과 나란히 CN별 XOR
누적(lost_parity)을 유지해서, C2V 재구성 시점마다 부호 오류 여부를 셌다
(16 frames, 20 iteration, C2V 재구성 45,301,760회).

| iteration | C2V 총수 | 부호 오류 | 부호 오류 이면서 mag != 0 |
|-----------|----------|-----------|--------------------------|
| 1 | 2,265,088 | 21 (0.001%) | 0 |
| 5 | 2,265,088 | 69,339 (3.061%) | 0 |
| 10 | 2,265,088 | 43,736 (1.931%) | 0 |
| 20 | 2,265,088 | 8,460 (0.373%) | 0 |

부호 오류는 최대 3.06%까지 올라가지만 **전부 magnitude 0인 C2V**였다. magnitude가 0이 아닌
C2V가 잘못된 부호를 받은 사례는 45M회 중 0건이다.

**본체와 `np.signbit` 수정본의 lockstep 비교 (실측).** 32 frames, n_err=350, 20 iteration
동안 매 iteration 내부 배열을 비교했다.

| iteration | min1 | min2 | min1_pos | check_sum | edge_sgn | err_bits |
|-----------|------|------|----------|-----------|----------|----------|
| 1 | 0 | 0 | 0 | 25 | 25 | 0 |
| 5 | 0 | 0 | 0 | 4,597 | 5,023 | 0 |
| 20 | 0 | 0 | 0 | 812 | 882 | 0 |

`check_sum`과 `edge_sgn`은 크게 갈라지지만 `min1`, `min2`, `min1_pos`, `err_bits`는 매 iteration
완전히 같다. FER도 n_err 300/350/400/450/500 (각 64 frames)에서 프레임별 성공 여부와 성공
iteration이 모두 일치했다.

**면역의 근거와 취약성.** `_cnu_update:179`가 `<=`를 쓰므로 min1 == 0인 상태는 "현재 min1_pos인
edge가 magnitude 0"인 경우뿐이다. `_column_order`가 매 iteration 전 column을 도는 한, edge e의
두 갱신 사이에 다른 모든 edge가 정확히 한 번씩 갱신된다. e가 아직 min1_pos라는 것은 e의 갱신
이후 어떤 edge도 magnitude 0을 내지 않았다는 뜻이므로 다른 edge의 부호 소실 비트가 전부 0이고,
CSW 패리티 오차가 상쇄된다. e가 아닌 edge는 `check_out = min1 = 0`을 읽으므로 부호가 무의미하다.

이 면역이 스케줄에 기댄 것임을 실측으로 확인했다. `_column_order`를 짝수 iteration에 짝수 column만
갱신하도록 바꾸자 (decoder.py 모듈 docstring 표가 "layered / informed dynamic scheduling"용
교체 지점으로 명시한 자리) 결과가 달라졌다.

| 변형 | C2V 총수 | 부호 오류 | 부호 오류 이면서 mag != 0 |
|------|----------|-----------|--------------------------|
| 본체 (`_column_order` 전 column) | 27,181,056 | 481,836 | 0 |
| `_column_order` 부분 갱신 | 20,422,656 | 504,924 | **3,390 (0.0166%)** |
| `_cnu_update` min1 비교 `<` | 27,181,056 | 479,022 | 0 |

**3-bit 파일 경로는 이 경로가 열리지 않는다.** `LLR_MATRIX_HD_1.txt` 로드 시 `edge_mag = [7,5,3,1]`
이라 `sgn * mag`가 `-0.0`을 만들 수 없다 (실측 확인).

**원본 HW 의미 (C++ 소스 확인).** C++은 도메인이 둘이다.

- ㉠ min1/min2는 압축된 V 도메인 `{V_VERY_STRONG=3, V_NORMAL_STRONG=2, V_NORMAL_WEAK=1,
  V_VERY_WEAK=0}`에 산다 (`common.h:338-341`). 즉 min1 == 0은 C++에서도 흔한 정상 상태다.
- ㉡ `C2V_Cal`이 이를 EDGE 도메인으로 되돌린다 (`decoder.cpp:2402-2405`).
  `V_VERY_WEAK`는 `EDGE_MAG_1 = 1`이 된다. 즉 **C2V magnitude는 절대 0이 되지 않는다**.
- ㉢ sign은 값과 별도로 `Check_SRAM_sgn`에 저장되고, 판정은
  `if (check_in >= 0) v2c_sgn = V_PLUS; else V_MINUS` (`decoder.cpp:2754-2755`)이다. 이 판정의
  입력값이 0이 되는 일이 없으므로 sign이 소실될 여지가 없다.
- ㉣ `VN_Cal_HD`의 `temp_m == 0` 분기(`decoder.cpp:4082-4099`)는 magnitude를 캐스케이드로
  정한 뒤 `if (VNU_in > 0) temp = temp_m; else temp = -temp_m;`로 **VNU_in의 부호를 실어 보낸다**.
  th가 양수면 magnitude는 `EDGE_MAG_1 = 1`이 되므로 부호가 반드시 살아남는다.

따라서 HW 의미로는 "가장 약한 메시지도 부호는 반드시 보존한다"가 맞다. Python이 두 도메인을
`edge_mag` 하나로 합친 결과, 균일 모드에서만 magnitude 0이 생기고 그때 부호가 사라진다.
`np.signbit(vnu_out)`이 HW에 충실한 읽기다.

**판정**: 부호 소실은 실재하고 빈도도 낮지 않다 (프레임당 약 240건). 현재 본체 조합에서는
결과에 닿지 않지만, 그 면역이 설계가 아이디어 교체를 권장하는 바로 그 함수(`_column_order`)에
기대고 있어 잠복 결함이다. `_vnu_quantize`가 계산한 부호를 `_process_column`이 버리는 구조
자체가 두 함수의 계약 불일치다.

### ㉯ mag 0의 min1/min2 점유 (실측)

`_cnu_update:179`가 `new_mag <= cur_min1`이므로 `new_mag == 0`은 항상 min1을 차지하고,
동시에 `:182`가 min2를 RESET으로 올린다. 그 CN은 min1_pos edge에만 RESET(6-bit면 31, 최대값)을
보내고 나머지 edge에는 전부 0을 보낸다.

**빈도 실측** (균일 6-bit, ch=8, n_err=350, 32 frames, CN lane 147,456개).

| iteration | min1==0 lane 비율 | zero edge 1개 받은 lane | zero edge 2개 이상 받은 lane |
|-----------|------------------|------------------------|----------------------------|
| 1 | 0.049% | 0.032% | 0.000% |
| 3 | 2.246% | 2.822% | 0.043% |
| 4 | 4.772% | 7.477% | 0.294% |
| 5 | 3.791% | 7.966% | 0.342% |
| 8 | 0.085% | 6.228% | 0.211% |
| 20 | (측정 구간 밖) | 5.922% | 0.187% |

수렴 구간(iteration 3~8)에서 CN의 6~8%가 magnitude 0 메시지를 받고, 그때마다 그 CN은
min1_pos 하나를 뺀 모든 edge에 0을 내보낸다.

**FER 영향 실측** (256 frames, max_iter 20, `edge_mag`만 다르고 로직은 동일).

| num_bits | ch | n_err | FER (0 레벨 있음) | FER (0 레벨 없음, 최소 1) |
|----------|----|-------|-------------------|--------------------------|
| 4 | 8 | 250 | 0.1719 | 0.1719 |
| 4 | 8 | 300 | 0.2148 | 0.2148 |
| 4 | 8 | 350 | 0.3398 | 0.3086 |
| 6 | 8 | 300 | 0.0000 | 0.0000 |
| 6 | 8 | 350 | **0.1875** | **0.1211** |
| 6 | 8 | 400 | 1.0000 | 1.0000 |

워터폴 구간에서 0 레벨이 FER을 상대 35% 악화시킨다 (48/256 대 31/256).

**판정**: 원본 HW 의미(C2V magnitude 하한 1)와 어긋나고, 측정 가능한 성능 손해가 있다.
"0 레벨을 둘 것인가"는 설계 선택이므로 Decision 등급 확인이 필요하다. 순수 min-sum 관점에서
magnitude 0은 정상 레벨이지만, 이 디코더는 min1 교체 시 min2를 RESET으로 올리는 HW 특성을
그대로 쓰고 있어서 두 규약이 섞이면 "한 edge만 최대 강도, 나머지 전부 침묵"이라는 극단적인 CN이
만들어진다.

### ㉰ `raw == 0`일 때 sign 규칙 (실측)

`_vnu_quantize:159-162`가 `raw == 0`이면 sign을 `vnu_in`에서 가져온다. 균일 모드에서 이 분기가
적용되는 원소 집합은 `mag == 0`이 되는 원소 집합과 정확히 같다 (실측: 둘 다 9,986개).
따라서 여기서 정한 부호는 `_process_column:295`가 전부 버린다. **이 분기는 균일 모드에서
실질적으로 무의미하다.**

`vnu_in == 0`인 경우도 확인했다. `np.where(vnu_in > 0, 1.0, -1.0)`은 `+0.0`과 `-0.0` 모두에 대해
`-1.0`을 준다. min1 == 0이 흔하므로(위 표에서 CN lane의 6~8%) `vnu_in == 0`은 예외가 아니라
일상적인 입력이다. C++도 같은 형태(`decoder.cpp:4098-4099`, else 가지가 음수)지만 C++의
VNU_in은 0이 될 수 없다.

3-bit 파일 경로에서는 `edge_mag[-1] = 1`이라 `raw == 0`일 때 magnitude 1이 나오고, `vnu_in`이
`±{1,3,5,7}`이라 부호가 그대로 살아남는다 (실측 확인).

**판정**: 로직 결함은 아니지만 `decoder.py:151`의 docstring이 약속한 동작("raw==0이면 sign은
VNU_in에서")이 균일 모드에서 지켜지지 않는다. ㉮를 고치면 이 분기도 의미를 되찾는다.

### ㉱ RESET = edge_mag[0] = top_level 변화

**전수 확인 (정적 읽기).** RESET을 쓰는 자리는 모두 `self._edge_mag[0]`에서 나온다.
남은 리터럴 7은 없다.

| 위치 | 용도 |
|------|------|
| `decoder.py:170` | `_cnu_update` 지역 상수 |
| `decoder.py:178` | remove old에서 min1_pos였던 edge의 min2 복귀값 |
| `decoder.py:182` | min1 교체 시 min2 |
| `decoder.py:208, 219, 220` | `_init_state` min1/min2 초기값 |
| `decoder.py:240, 249, 250` | `_run_iteration` restart 클리어값 |

**iteration 1의 sum_t 스케일 (계산).** Edge Clear 상태라 모든 C2V가 `±RESET`이므로
`sum_t = ch + Σ(±top_level)`이다. 채널 항과 메시지 한 개의 비율은 다음과 같다.

| 매트릭스 | dv | ch | RESET | ch / RESET |
|----------|----|----|-------|-----------|
| 균일 6-bit (config 기본) | 전 dv 공통 | 8 | 31 | 0.26 |
| 균일 4-bit | 전 dv 공통 | 8 | 7 | 1.14 |
| `LLR_MATRIX_HD_1.txt` | 4 | 10 | 7 | 1.43 |
| `LLR_MATRIX_HD_1.txt` | 3 | 13 | 7 | 1.86 |
| `LLR_MATRIX_HD_1.txt` | 2 | 28 | 7 | 4.00 |

균일 6-bit 기본값은 파일 매트릭스보다 채널 가중이 5배 이상 약하다. iteration 1에서 ch는
동점 깨기 역할만 한다.

**ch 스윕 실측** (균일 6-bit, top=31, n_err=350, 128 frames).

| ch | ch/RESET | FER |
|----|----------|-----|
| 2 | 0.06 | 1.0000 |
| 4 | 0.13 | 0.5547 |
| 8 (기본) | 0.26 | 0.1953 |
| 16 | 0.52 | 0.1016 |
| 24 | 0.77 | 0.0781 |
| 31 | 1.00 | **1.0000** |
| 48 | 1.55 | 0.6641 |

기본값 ch=8은 ch=24보다 FER이 2.5배 나쁘다. 그리고 ch=31에서 FER이 1.0으로 튄다.

**`ch == top_level` 붕괴 (실측, HIGH).** 인접 값과 비교하면 한 칸 차이로 갈린다.

| num_bits | top_level | ch | FER (0 레벨 있음) | FER (0 레벨 없음) |
|----------|-----------|----|-------------------|-------------------|
| 6 | 31 | 30 | 0.0938 | 0.0521 |
| 6 | 31 | **31** | **1.0000** | 0.3229 |
| 6 | 31 | 32 | 0.3229 | 0.3021 |
| 4 | 7 | 6 | 0.0000 | 0.0000 |
| 4 | 7 | **7** | **1.0000** | 0.2188 |
| 4 | 7 | 8 | 0.2188 | 0.2188 |
| 4 | 7 | **14** (2x) | **1.0000** | (미측정) |

원인은 iteration 1의 공명이다. 그때 모든 C2V가 `±top_level`이므로
`raw = sum_t - vnu_in = ch + Σ_{j != e}(±top_level)`이고, `ch = k * top_level`이면 이 값이 정확히
0이 되는 조합이 생긴다. 균일 모드에서 `raw == 0`은 곧 magnitude 0이고, 그 edge가 min1을 차지해
CN을 침묵시킨다. 0 레벨을 빼면 같은 ch에서 FER이 1.0에서 0.32(6-bit) 또는 0.22(4-bit)로
떨어지고, 인접 ch 값과 같아진다. 0 레벨이 공명을 재앙으로 증폭하는 증폭기다.

`run.py:197-198`은 `channel_llr >= 1`인 정수면 모두 통과시키므로
`{"num_bits": 6, "channel_llr": 31}` 설정이 경고 없이 끝까지 돌고 FER 1.0을 보고한다.

**"반전 가능 조건" 확인.** `_pm/TODO.md:19-21`에 있다. 원문은
"반전 가능 조건 `ch ≤ 7·dv` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)"이다. 균일 모드
기본값은 `8 ≤ 31·2 = 62`로 만족한다. 다만 규칙이 리터럴 7로 적혀 있어 균일 모드를 덮지 못하고,
위에서 찾은 `ch = k·top_level` 공명도 이 규칙으로는 걸러지지 않는다.

**RESET과 최대 실제값이 같은 것의 타당성.** C++도 같다. `RESET = V_VERY_STRONG = 3`은 V 도메인
최대값이고(`common.h:338`, `decoder.cpp:3523`), 대응하는 `EDGE_MAG_7 = 7`도 EDGE 도메인
최대값이다. 초기값과 실제값이 구분되지 않는 것은 원본 HW 특성 그대로이므로 새 문제가 아니다.

### ㉲ restart `th = -1` 관례와의 관계 (정적 읽기 + 실행 확인)

- ㉠ `make_internal_uniform_matrix:229`가 restart_iters로 `[]`를 넘긴다. 실행 확인 결과
  `restart_iters = set()`, `is_restart(1..3)`이 모두 False다. `_is_edge_clear_iter`는
  `iteration == 1`만 남는다.
- ㉡ `save()`/`load()` 왕복에서 restart 없음이 보존된다 (`save`가 개수 0을 쓰고 restart 줄을
  생략, `load`가 `num_restart > 0`일 때만 줄을 읽는다).
- ㉢ config로 균일 매트릭스에 restart를 넣는 경로는 없다. `_INTERNAL_QUANTIZE_KEYS`
  (`run.py:67`)는 `{num_bits, channel_llr, max_iter, mode}`뿐이다.
- ㉣ 생성 파일을 손으로 고쳐 restart를 넣으면 `_validate`가 막는다. 균일 매트릭스는 그룹이
  하나뿐이라 `llr_matrix.py:148-149`의 "restart 그룹 뒤에 그룹이 없음"에 걸린다.
- ㉤ `th = -1` 관례 자체는 두 경로에서 의미가 같다. `_vnu_quantize`에서 `mag_in >= -1`은 항상
  참이므로 `edge_mag[0]`(파일이면 7, 균일이면 top_level)이 나온다. 이는 llr_matrix.py 모듈
  docstring:25가 적은 "전 메시지 최대 레벨"과 일치한다.

**판정**: 기능 문제 없음. 문서 측면에서만, llr_matrix.py 모듈 docstring이 restart -1 관례를
두 공급 경로 공통 규약처럼 서술하는데 균일 경로는 이 관례를 쓸 수 없다.

### ㉳ `ch` 항의 정수 domain 확인 (실측 + 정적 읽기)

- ㉠ `col_dv_idx`가 균일 매트릭스에서 전 column을 0으로 매핑한다 (실측: `unique = [0]`,
  `num_dv = 1`, `th_len = 31`). `_process_column:271`의 `cur_ch[:, 0, None]`과 `:293`의
  `cur_th[:, 0, :]`가 전 column 공통 값을 소비한다. 동작에 문제 없다.
- ㉡ dv별 차등이 사라진 것은 구조적 제약이며 성능에 크게 작용한다. 같은 부호에서 dv별 ch를
  준 매트릭스와 공통 ch 매트릭스를 비교했다 (균일 6-bit th, n_err=350, 128 frames).

| ch 구성 | FER |
|---------|-----|
| dv2=24, dv3=12, dv4=8 | 1.0000 |
| dv2=16, dv3=10, dv4=8 | 1.0000 |
| dv2=8, dv3=8, dv4=8 (균일 모드가 만드는 구성) | 0.1953 |

  dv=2 column은 `Σ|C2V| >= ch`여야 반전되므로 ch를 올리면 고집스러워진다. 예시 부호는 dv=2
  column block이 17개(전체 147개 중)라 여기서 막히면 프레임 전체가 실패한다. DAO 파일
  매트릭스는 정확히 이 축을 쓴다 (`LLR_MATRIX_HD_1.txt`: dv11→ch1, dv4→ch10, dv3→ch13,
  dv2→ch28).
- ㉢ 경계 사례로, degree 0인 column block(전부 -1)이 있으면 `dv_from = 1` 때문에
  `col_dv_idx`가 에러를 낸다. 현 예시 부호에는 없다.

**판정**: 의도된 단순화가 맞지만 비정칙 부호 스크리닝에서는 실질적 제약이다. dv별 ch는
`ch ≤ top_level·dv` 규칙 자체가 dv별인 만큼 균일 모드가 그 규칙을 표현할 수 없다는 뜻이기도 하다.

### ㉴ 실제 디코딩 동작 확인

위 모든 실측이 `MinSumDecoder.decoder_main`을 직접 호출해 수행됐다. 저장소 추적 파일은
수정하거나 생성하지 않았다. 계측용 서브클래스와 스크립트는 scratchpad에만 두었다
(`probe_zero_level.py`, `probe2.py`, `probe3.py`, `probe4.py`, `probe5.py`, `probe6.py`,
`probe7.py`).

---

## 추가 발견 (범위 인접)

`LLRMatrix.load:170`이 파일명에 `uniform`이라는 낱말이 있으면 `edge_mag`를 th 개수만으로
`[th_len..0]`으로 정한다. 값이 실제 `[top..1]`인지 검사하지 않는다. 실측으로
`LLR_MATRIX_HD_1.txt`를 `LLR_MATRIX_HD_uniform_renamed.txt`로 복사해 로드하니
`edge_mag`가 `[7,5,3,1]`에서 `[3,2,1,0]`으로 조용히 바뀌었다. 레벨 값도 틀리고 없어야 할
0 레벨까지 생긴다.

---

## 발견 목록

| 심각도 | 문제 | 위치 | 근거 |
|--------|------|------|------|
| HIGH | `channel_llr`가 `top_level`의 정수배면 iteration 1에서 `raw = ch + Σ(±top_level) = 0` 공명이 생기고, 균일 모드는 그 raw를 magnitude 0으로 만들어 CN을 침묵시킨다. FER이 1.0으로 붕괴한다 | `llr_matrix.py:222-231` (`make_internal_uniform_matrix`가 `channel_llr`와 `top_level`의 관계를 제약하지 않음) + `run.py:197-198` (검증이 `>= 1`만 봄) | 실측: 4-bit ch=6 FER 0.0000, ch=7 FER 1.0000, ch=8 FER 0.2188, ch=14 FER 1.0000. 6-bit ch=30 FER 0.0938, ch=31 FER 1.0000, ch=32 FER 0.3229. 0 레벨을 빼면 ch=7이 0.2188, ch=31이 0.3229로 인접 값과 같아진다 (96~128 frames, n_err 300/350) |
| MEDIUM | magnitude 0인 메시지의 sign이 `-0.0` 때문에 항상 0(양)으로 기록된다. 현재 스케줄에서는 결과에 닿지 않지만, 교체 지점 `_column_order`를 부분 갱신 스케줄로 바꾸면 magnitude가 0이 아닌 C2V까지 잘못된 부호를 받는다 | `decoder.py:295` (`new_sgn = (vnu_out < 0)`), 발생원 `decoder.py:163` (`sgn * mag`) | 실측: `np.float32(-0.0) < 0`은 False, `np.signbit`은 True. 부호 소실 3,847건/17,979,136건 (mag0의 38.5%). 본체 스케줄에서 "부호 오류 이면서 mag != 0"은 45M회 중 0건, 부분 갱신 스케줄에서는 3,390건(0.0166%). C++은 `VN_Cal_HD`가 raw==0에서 VNU_in 부호를 실어 magnitude 1로 내보내고(`decoder.cpp:4082-4099`), `C2V_Cal`이 최소 magnitude를 `EDGE_MAG_1=1`로 되돌려(`decoder.cpp:2405`) 부호가 사라질 여지가 없다 |
| MEDIUM | magnitude 0이 항상 min1을 차지해(`<=`) 그 CN이 min1_pos 하나를 뺀 모든 edge에 0을 보낸다. 원본 HW에는 대응이 없고 FER이 나빠진다 | `decoder.py:179-184` (`new_mag <= cur_min1`, min2=RESET), `llr_matrix.py:49-51` (`uniform_edge_mag`가 0을 포함) | 실측: 수렴 구간에서 CN lane의 6~8%가 magnitude 0 edge를 받는다 (iteration 5에 7.97%). FER 비교 (256 frames, 6-bit ch=8 n_err=350): 0 레벨 있음 0.1875, 최소 레벨 1 0.1211. C++은 min1 최소값 `V_VERY_WEAK=0`(`common.h:341`)을 `EDGE_MAG_1=1`로 되돌린다(`decoder.cpp:2405`) |
| MEDIUM | `load()`가 파일명의 `uniform` 낱말만 보고 `edge_mag`를 th 개수에서 유도한다. 실제 th 값을 확인하지 않아 3-bit 파일에 그 낱말이 들어가면 레벨 구성이 조용히 바뀐다 | `llr_matrix.py:170, 202-203` | 실측: `LLR_MATRIX_HD_1.txt`를 `LLR_MATRIX_HD_uniform_renamed.txt`로 복사해 로드하니 `edge_mag`가 `[7,5,3,1]` → `[3,2,1,0]`으로 바뀌었다 |
| MEDIUM | 균일 모드가 dv별 ch를 표현하지 못한다. 이 축은 FER을 크게 좌우하며 `ch ≤ top_level·dv` 규칙 자체가 dv별이다 | `llr_matrix.py:226, 229` (`ch = [channel_llr] * ch_len`, dv 구간 `[1, dv_max]` 하나) | 실측: 같은 부호에서 dv2=24/dv3=12/dv4=8은 FER 1.0000, dv 공통 8은 0.1953 (128 frames, n_err=350). 파일 매트릭스는 이 축을 쓴다 (`LLR_MATRIX_HD_1.txt` dv11→1, dv4→10, dv3→13, dv2→28) |
| LOW | config 기본값 `num_bits=6, channel_llr=8`이 채널 가중을 파일 매트릭스보다 5배 이상 약하게 만들고, 측정상 최적에서 멀다 | `config.json:31-32` | 실측 ch 스윕 (6-bit, n_err=350, 128 frames): ch=8 FER 0.1953, ch=16 0.1016, ch=24 0.0781. ch/RESET이 0.26으로, `LLR_MATRIX_HD_1.txt`의 1.43~4.00과 크게 다르다 |
| LOW | `raw == 0`일 때 `vnu_in`에서 sign을 가져오는 분기가 균일 모드에서 무의미하다. docstring이 약속한 동작이 실현되지 않는다 | `decoder.py:159-162`, docstring `decoder.py:151` | 실측: `raw == 0` 개수와 `mag == 0` 개수가 9,986으로 정확히 같다. 그 부호는 `:295`에서 전부 버려진다. `vnu_in == 0`일 때 `sgn_zero`가 항상 -1이 되는 것도 확인 |
| LOW | `_pm/TODO.md`의 "반전 가능 조건 `ch ≤ 7·dv`"가 리터럴 7로 적혀 균일 모드를 덮지 못하고, `ch = k·top_level` 공명도 담지 못한다 | `_pm/TODO.md:19-21` | 균일 6-bit는 `8 ≤ 31·2`로 이 규칙을 만족하지만 ch=31에서 FER 1.0이 된다 |
| LOW | llr_matrix.py 모듈 docstring이 restart `-1` 관례를 두 공급 경로 공통 규약처럼 서술하지만 균일 경로는 restart를 가질 수 없다 | `llr_matrix.py:23-26`, `llr_matrix.py:229` | `make_internal_uniform_matrix`가 `[]`를 넘기고, config에 restart 키가 없으며(`run.py:67`), 손으로 넣으면 그룹이 하나라 `_validate`(`llr_matrix.py:148-149`)가 막는다 |

## 문제 없음으로 판정한 항목

- ㉮ RESET 전수 확인: `decoder.py`의 RESET 사용처 8곳이 모두 `self._edge_mag[0]`에서 나온다.
  남은 리터럴 없음
- ㉯ RESET이 실제 magnitude 최대값과 같아 초기값과 구분되지 않는 점: C++도 동일하다
  (`RESET = V_VERY_STRONG = 3`이 V 도메인 최대, 대응 `EDGE_MAG_7 = 7`이 EDGE 도메인 최대)
- ㉰ restart 규약: 두 경로에서 `th = -1`의 의미가 같고, 균일 매트릭스에 restart가 들어갈 경로가
  없다
- ㉱ `col_dv_idx`의 균일 매트릭스 매핑: 전 column이 dv_idx 0으로 매핑되어 `_process_column`이
  정상 소비한다
- ㉲ `np.roll`의 `-0.0` 취급: 부호 비트를 그대로 옮긴다 (roll이 부호를 잃는 문제는 없다)
