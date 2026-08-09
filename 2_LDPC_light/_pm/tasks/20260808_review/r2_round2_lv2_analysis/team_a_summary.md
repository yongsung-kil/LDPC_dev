# Round 2 · 팀 A (uniform_numeric) 종합

작성: 2026-08-08 14:55:28
담당 관점: A (균일 양자화 수치 규약 + 저장/로드 왕복), B (캐스케이드 일반화 + 0 레벨 도입 파급)
워커 3개, 총 발견 28건. 중복 병합 후 고유 발견 19건.

---

## 1. 워커별 결과 요약

| 워커 | 범위 | 발견 | 심각도 분포 | 한 줄 결론 |
|------|------|------|------------|-----------|
| worker_a_1 | 합성 → save → load 왕복, 파일명 규약, int/float32, max/min_value, 경계 파라미터 | 10건 | HIGH 2, MEDIUM 3, LOW 5 | 왕복 자체는 12개 조합 × 19개 필드 전부 일치. 위험은 전부 파일명이 의미를 결정하는 구조에서 나온다 |
| worker_a_2 | `_vnu_quantize` 캐스케이드 일반화 정확성, 정수성 전제, dtype·shape·인덱스 | 9건 | MEDIUM 4, LOW 5 | 캐스케이드 일반화는 C++ elif 체인과 등가(불일치 0건 / 20만 건 이상 대조). 정수성 전제도 현 경로에서 구조적으로 성립 |
| worker_a_3 | magnitude 0 레벨 도입 파급, RESET 변화, min1/min2 점유, `-0.0` 부호 | 9건 | HIGH 1, MEDIUM 4, LOW 4 | 0 레벨이 실제 FER을 악화시키고, 특정 `channel_llr` 값에서 FER 1.0으로 붕괴시킨다 |

### 정상으로 확인된 것 (교차 확인 포함)

- ㉮ **왕복 무손실**: 합성 객체와 `save()` → `load()` 복원 객체가 mode HD/2SD/3SD × num_bits 2/3/4/6의 12개 조합에서 `name`을 뺀 19개 필드 전부 일치 (worker_a_1 ㉮).
- ㉯ **커밋 산출물 정합**: `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`가 `make_internal_uniform_matrix(6, 8, 30, 4)` 재생성 결과와 바이트 완전 동일 (301 B).
- ㉰ **캐스케이드 등가성**: 역순 루프가 C++ `decoder.cpp:4112-4115`의 elif 체인과 같은 결과를 낸다. 실파일 전 th 조합 2,580건과 무작위 비단조 th 20만 4천 건에서 불일치 0건.
- ㉱ **정수성 전제 성립**: 파일 로더의 `int(v)` 강제와 `edge_mag` 정수성이 `sum_t` 정수성을 구조적으로 보장한다. 실행 중 비정수 raw는 15,484회 호출에서 0건. float32 한계(2^24)까지 num_bits 20까지 여유.
- ㉲ **restart 대칭, floor_flag 실손실 0, dv 구간 커버리지, `np.roll` 부호 보존, RESET 사용처 8곳 전수**가 모두 정상.

---

## 2. 팀 내 교차 분석

### 2.1 근본 원인 3갈래로 수렴

워커 3개가 서로 다른 각도에서 찾은 발견들이 근본 원인 세 개로 모인다.

- **R1. `edge_mag`에 magnitude 0 레벨을 넣은 설계 선택** (worker_a_2 ㉲ + worker_a_3 ㉮㉯㉱)
  - ㉠ `channel_llr = k · top_level`이면 iteration 1에서 `raw = ch + Σ(±top_level) = 0` 공명이 생기고, 균일 모드는 그 raw를 magnitude 0으로 만들어 CN을 침묵시켜 FER이 1.0으로 붕괴한다 (worker_a_3 실측: 4-bit ch=7 → 1.0000, ch=6 → 0.0000, ch=8 → 0.2188).
  - ㉡ magnitude 0이 `<=` 비교로 항상 min1을 차지해 그 CN이 min1_pos 하나를 뺀 모든 edge에 0을 보낸다. 수렴 구간에서 CN lane의 6~8%가 이 상태다. FER 상대 35% 악화 (0.1875 대 0.1211).
  - ㉢ `sgn * 0`이 `-0.0`이 되고 `new_sgn = (vnu_out < 0)`가 이를 양수로 읽어 부호가 사라진다.
  - **결정적 증거**: worker_a_3이 `edge_mag` 최소를 1로 바꿔 재측정하니 ㉠의 FER 1.0이 인접 ch 값과 같은 0.32로 떨어지고, ㉡의 FER 악화가 사라졌다. 세 증상의 공통 원인이 0 레벨임이 실측으로 분리된다.
  - **C++ 대조**: 원본은 도메인이 둘이다. min1/min2는 압축 V 도메인(`V_VERY_WEAK=0`이 정상 상태), C2V 출력은 `C2V_Cal`이 `EDGE_MAG_1=1`로 되돌린다 (`decoder.cpp:2405`, `common.h:338-341`). 즉 C2V magnitude는 절대 0이 되지 않는다. Python이 두 도메인을 `edge_mag` 하나로 합치면서 균일 모드에만 0 레벨이 생겼다.

- **R2. 레벨 구성과 모드를 파일 내용이 아니라 파일명으로 결정하는 구조** (worker_a_1 ㉰㉯ + worker_a_2 ㉵ + worker_a_3 추가발견)
  - ㉠ `"uniform" in basename.lower()` 부분문자열 검사라 `nonuniform`, `uniformity`도 True가 된다.
  - ㉡ 반대 방향으로, 생성된 **3-bit** uniform 파일이 개명되면 `th_len == 3` 검사를 통과해 `edge_mag`가 `[3,2,1,0]`에서 `[7,5,3,1]`로 조용히 바뀐다 (4-bit 이상은 `NotImplementedError`로 걸린다).
  - ㉢ mode도 파일명에서만 오므로 다른 모드 이름이면 ch/th 경계가 밀린다.
  - ㉣ 정당한 DAO 4-bit 파일(C++ `__4_BIT_LLR__` 빌드가 지원, `decoder.cpp:4102-4110`)은 로드가 막히고, 파일명에 `uniform`을 넣는 유일한 우회는 `[7..0]`을 만들어 정답 `[8..1]`과 다른 값으로 조용히 복호한다.
  - **워커 2개가 독립적으로 같은 실측을 재현**했다 (worker_a_1과 worker_a_3이 각각 `LLR_MATRIX_HD_1.txt`를 uniform 이름으로 복사해 로드 → `[7,5,3,1]`이 `[3,2,1,0]`으로 바뀜을 확인).

- **R3. `num_bits` 상한 부재 + 캐스케이드 비용이 th 개수에 선형** (worker_a_1 ㉵ + worker_a_2 발견 M-2)
  - 두 워커의 실측이 서로 다른 축에서 일치한다. worker_a_1은 종단(8프레임 3 iteration: 6bit 0.14s, 12bit 6.30s), worker_a_2는 호출당(64×256 배열: th_len 3 → 0.09ms, 2047 → 30ms). 둘 다 `2^(num_bits-1)`에 선형.
  - **worker_a_2가 해법을 실측으로 제시**했다. 균일 매트릭스에서 캐스케이드는 `sign(raw) * min(|raw|, top_level)`과 정수 raw 전 범위에서 완전히 동일하고(`np.array_equal` 참), 이 한 줄은 th_len=31 대비 25배, 127 대비 109배 빠르다. 즉 균일 경로는 O(1)로 대체 가능하다.

### 2.2 워커 간 모순과 조정

- **`-0.0` 부호 소실의 영향 범위**: worker_a_2는 "CSW 로그가 이미 오염됨"(`prev_csw`가 iter2부터 전 프레임 다름), worker_a_3은 "결과에 닿지 않음"(min1·err_bits·success 전부 동일)이라고 적었다. **모순이 아니다.** `check_sum`과 `edge_sgn`이 갈라지면 `prev_csw`가 갈라지지만, 균일 매트릭스는 ITER 타입 그룹만 만들어 `prev_csw`가 row 선택에 쓰이지 않는다 (`llr_matrix.py:292`). 두 결과를 합치면 **활성화 경로 3개**로 정리된다.
  - 1. 이미 발생 중: `csw` 로그와 `fail_detail`의 `final_csw`가 균일 모드에서 틀린 값을 낸다 (worker_a_2 실측).
  - 2. 잠복: 균일 매트릭스에 CSW 타입 그룹을 쓰면 row 선택이 갈려 복호 결과가 바뀐다 (`LLRMatrix`는 CSW 그룹을 지원하지만 `make_internal_uniform_matrix`는 만들지 않는다).
  - 3. 잠복: `_column_order`를 부분 갱신 스케줄로 재정의하면 magnitude 0이 아닌 C2V까지 잘못된 부호를 받는다 (worker_a_3 실측: 3,390건). 이 함수는 모듈 docstring 표가 "layered / informed dynamic scheduling"용 교체 지점으로 명시한 자리다.
  - **조정 결과**: 심각도 MEDIUM 유지, 단 1번 경로는 이미 실사용 출력이 틀린 상태이므로 Round 3에서 HIGH 승격 후보로 다룬다.

- **`uniform` 파일명 오탐의 심각도**: worker_a_1은 HIGH, worker_a_3은 MEDIUM으로 매겼다. **코드 근거 우선으로 HIGH로 조정**한다. 심각도 정의가 "틀린 결과를 내지만 진행됨"인데, 두 방향 모두 예외 없이 다른 `edge_mag`로 끝까지 복호하고 FER을 보고한다. worker_a_1이 추가로 찾은 num_bits=3 역방향 사례는 `run.py`가 허용하는 정상 설정값에서 발생하므로 사용자 실수만의 문제가 아니다.

- **`ch = k · top_level` 공명과 정수성 전제의 관계**: worker_a_2가 확인한 "캐스케이드 = 상한 클리핑 등가"는 worker_a_3의 공명 발견과 모순되지 않고 오히려 이를 설명한다. 상한 클리핑이므로 `|raw| = 0`은 그대로 0이 되고, 하한이 없어 0 레벨로 떨어진다. 3-bit 파일 경로는 `edge_mag[-1] = 1`이라 같은 공명이 일어나도 magnitude 1이 남는다.

### 2.3 검증 방법이 불충분한 발견 1건 (Round 3 재확인 필요)

worker_a_3의 "균일 모드가 dv별 ch를 표현하지 못한다" (MEDIUM)는 실측 수치는 정확하지만 **인과 해석에 방법론 결함**이 있다. worker_a_3은 `dv2=24 / dv3=12 / dv4=8` 매트릭스가 FER 1.0000이고 공통 `ch=8`이 0.1953이라는 관측에서 "ch를 올리면 dv=2 column이 고집스러워진다"고 결론지었는데, 이는 DAO 파일이 dv2에 가장 높은 ch(28)를 주는 설계 의도와 정반대다. 원인은 스케일 불일치로 보인다. `LLR_MATRIX_HD_1.txt`는 top_level 7에 dv2 ch=28이라 비율이 4.0인데, 실험은 top_level 31에 ch=24를 써서 비율 0.77이다. DAO 비율을 맞추려면 dv2 ch가 약 124여야 한다. **"dv별 ch 차등이 균일 모드에 없다"는 사실 자체는 참이고 구조적 제약도 맞지만, 그것이 FER에 미치는 방향과 크기는 이 실험으로 판정되지 않는다.**

---

## 3. 통합 발견 목록

| # | 심각도 | 문제 | 위치 (파일:라인) | 근거 | 출처 |
|---|--------|------|------------------|------|------|
| A-1 | HIGH | `channel_llr`가 `top_level`의 정수배면 iteration 1에서 `raw = ch + Σ(±top_level) = 0` 공명이 생기고, 0 레벨이 이를 magnitude 0으로 만들어 CN을 침묵시킨다. FER이 1.0으로 붕괴하고 경고 없이 완주한다 | `llr_matrix.py:222-231`, `run.py:197-198` | 실측 4-bit: ch=6 → 0.0000, **ch=7 → 1.0000**, ch=8 → 0.2188, ch=14 → 1.0000. 6-bit: ch=30 → 0.0938, **ch=31 → 1.0000**, ch=32 → 0.3229. 0 레벨 제거 시 ch=7이 0.2188, ch=31이 0.3229로 인접 값과 같아짐 | w3 |
| A-2 | HIGH | 파일명에 `uniform`이 부분문자열로 든 사람 제작 3-bit 매트릭스가 균일 레벨로 오해석되어 조용히 다른 결과를 낸다 (`nonuniform`도 True) | `llr_matrix.py:170` | 실측(워커 2개 독립 재현): `LLR_MATRIX_HD_1.txt` 내용을 uniform 이름으로 로드 → `edge_mag`가 `[7,5,3,1]` 대신 `[3,2,1,0]`. 에러 없음 | w1, w3 |
| A-3 | HIGH | 생성된 **3-bit** uniform 파일이 개명되면 `th_len == 3` 검사를 통과해 `edge_mag`가 `[3,2,1,0]` → `[7,5,3,1]`로 조용히 바뀐다 (4-bit 이상만 `NotImplementedError`) | `llr_matrix.py:170`, `llr_matrix.py:67-72` | 실측: num_bits=3 생성 파일을 `LLR_MATRIX_HD_9.txt`로 로드 → 에러 없이 `edge_mag=[7,5,3,1]`. `run.py:195-196`이 하한 2만 보므로 num_bits=3은 정상 설정값 | w1 |
| A-4 | MEDIUM (HIGH 승격 후보) | magnitude 0 메시지의 sign이 `-0.0` 때문에 항상 양으로 기록된다. `csw` 로그와 `final_csw`가 **이미 틀린 값**이고, CSW 타입 그룹 또는 `_column_order` 재정의 시 복호 결과까지 바뀐다 | `decoder.py:295` (소실), `decoder.py:163` (발생원), `decoder.py:159-162` (버려지는 계산) | 실측: 부호 소실 3,847건 / 17,979,136건(mag0의 38.5%). `np.signbit` 판정판 대조 시 `prev_csw`가 iter2부터 전 프레임 상이, `check_sum` 차이 iter5에 1,134건. 본체 스케줄에서 "부호 오류 이면서 mag != 0"은 45M회 중 0건이나, 부분 갱신 스케줄에서 3,390건. C++은 `C2V_Cal`이 최소 magnitude를 `EDGE_MAG_1=1`로 되돌려(`decoder.cpp:2405`) 부호 소실 여지가 없다 | w2, w3 |
| A-5 | MEDIUM | magnitude 0이 `<=` 비교로 항상 min1을 차지해 그 CN이 min1_pos 하나를 뺀 모든 edge에 0을 보낸다. 원본 HW에 대응이 없고 FER이 나빠진다 | `decoder.py:179-184`, `llr_matrix.py:49-51` | 실측: 수렴 구간 CN lane의 6~8%가 magnitude 0 edge 수신(iter5에 7.97%). FER 비교(256 frames, 6-bit ch=8 n_err=350): 0 레벨 있음 0.1875, 최소 1 0.1211. C++은 min1의 `V_VERY_WEAK=0`을 `EDGE_MAG_1=1`로 되돌린다 | w3 |
| A-6 | MEDIUM | `num_bits` 상한이 없고 `_vnu_quantize` 비용이 th 개수에 선형이라 큰 값에서 복호가 사실상 멎는다. 균일 경로는 `sign(raw)·min(|raw|, top)` 한 줄로 O(1) 대체가 가능하다 | `run.py:195-196` (검증), `decoder.py:156-157` (소비) | 실측 종단(8프레임 3 iter): 6bit 0.14s, 8bit 0.43s, 10bit 1.59s, 12bit 6.30s. 실측 호출당(64×256): th_len 3 → 0.09ms, 31 → 0.50ms, 127 → 2.00ms, 2047 → 30ms. 등가 1줄은 0.02ms(25~109배). 등가성 `np.array_equal` 참 | w1, w2 |
| A-7 | MEDIUM | mode도 파일명에서만 오므로 다른 모드 이름으로 저장·개명하면 ch/th 경계가 조용히 밀린다. `_NAME_RE.search`가 basename 어디서든 첫 매칭을 취해 백업 접두어에도 걸린다 | `llr_matrix.py:46`, `llr_matrix.py:165-169` | 실측: HD `num_param=4` 매트릭스를 2SD 이름으로 저장 → `row_ch=[8,3]`, `row_th=[2,1]` (th 첫 값이 채널 값으로 재분류). `MY_LLR_MATRIX_2SD_backup_LLR_MATRIX_HD_0.txt` → mode='2SD' | w1 |
| A-8 | MEDIUM | 정당한 DAO 4-bit LLR matrix 파일을 로드할 수 없고, 우회하면 조용히 틀린 레벨이 된다. `2_LDPC_light`의 "외부 파라미터로 동작" 목표와 충돌한다 | `llr_matrix.py:67-72`, `llr_matrix.py:170, 202-203` | 실측: `num_param=8` HD → `th 7개 — 파일 매트릭스는 3-bit(th 3개) 전용`. 파일명 우회 시 `[7..0]`이 되어 정답 `[8,7,6,5,4,3,2,1]`과 다름. C++ 근거 `decoder.cpp:4102-4110`, `common.h:328-335` | w2 |
| A-9 | MEDIUM | 정수성 전제가 교체 지점 재정의로 조용히 깨진다. `_c2v_reconstruct`를 offset/normalized min-sum으로 바꾸면 캐스케이드가 클리핑이 아니라 floor + 클리핑이 되고, `_vnu_quantize`를 damping으로 바꾸면 `RESET = edge_mag[0]`의 "가능한 최대 magnitude" 전제도 함께 깨진다 | `llr_matrix.py:218-219` (전제 선언), `decoder.py:49, 51` (교체 지점 표), `decoder.py:170/208/240` (RESET 전제) | 실측(num_bits=6, top=31): raw 3.5 → 3.0(클리핑이면 3.5), 2.25 → 2.0, 0.5 → 0.0. 현 경로는 정수 유지(비정수 raw 0건 / 15,484 호출) | w2 |
| A-10 | MEDIUM | 생성 파일이 git 추적 디렉토리 `Input/LLR/`에 기본 기록된다. 파라미터 조합마다 파일이 쌓이고 같은 이름의 사람 제작 파일을 매 실행마다 조용히 덮어쓴다 | `run.py:206`, `run.py:300-302` | `git ls-files`로 uniform 파일이 커밋되어 있음을 확인. `save()`는 존재 여부를 보지 않는다 | w1 |
| A-11 | MEDIUM (해석 재확인 필요) | 균일 모드가 dv별 ch를 표현하지 못한다. 이 축은 DAO 파일이 실제로 쓰는 축이다 | `llr_matrix.py:226, 229` | 실측: dv2=24/dv3=12/dv4=8 → FER 1.0000, dv 공통 8 → 0.1953. **단 실험의 ch/top 비율(0.77)이 DAO 파일 비율(4.0)과 어긋나 인과 해석이 성립하지 않는다** (2.3절 참조). 구조적 제약이라는 사실만 확정 | w3 |
| A-12 | LOW | `mode="2SD"/"3SD"` 균일 매트릭스는 ch 칸을 전부 같은 값으로 채워 soft decision 구분이 없다. 파일 생성까지 성공한 뒤 첫 복호에서야 실패한다 | `llr_matrix.py:226`, `run.py:201-204`, `run.py:294-302` | 실측: 2SD num_bits=4 → `row_ch=[8,8]`, 파일 저장·디코더 생성 성공 후 `NotImplementedError`. 실패 전에 추적 디렉토리에 파일이 남는다 | w1 |
| A-13 | LOW | config 기본값 `num_bits=6, channel_llr=8`이 채널 가중을 파일 매트릭스보다 5배 이상 약하게 만들고 측정상 최적에서 멀다 | `config.json:31-32` | 실측 ch 스윕(6-bit, n_err=350, 128 frames): ch=8 → 0.1953, ch=16 → 0.1016, ch=24 → 0.0781 | w3 |
| A-14 | LOW | `raw == 0`일 때 `vnu_in`에서 sign을 가져오는 분기가 균일 모드에서 무의미하다 (docstring이 약속한 동작이 실현되지 않는다) | `decoder.py:159-162`, docstring `decoder.py:151` | 실측: `raw == 0` 개수와 `mag == 0` 개수가 9,986으로 정확히 같고, 그 부호는 `:295`에서 전부 버려진다. A-4를 고치면 이 분기도 의미를 되찾는다 | w2, w3 |
| A-15 | LOW | `cur_th` shape 주석에 일반화 전 상수 3이 남았다 | `decoder.py:256` | 실측: 균일 6-bit에서 `(5, 1, 31)` | w1, w2 |
| A-16 | LOW | `self._edge_mag`가 `llr_matrix.edge_mag`와 같은 배열 객체다. 한쪽을 바꾸면 `RESET`까지 함께 바뀐다 | `decoder.py:118` | 실측: `dec._edge_mag is m.edge_mag` → True. `m.edge_mag[0] = 99` 후 `dec._edge_mag[0] == 99.0` | w2 |
| A-17 | LOW | th 비단조 경고가 stderr로 한 번만 나가고 `summary()`나 `summary.txt`에 남지 않아 배치 실행에서 유실된다 | `llr_matrix.py:152-155` | 실측: 인위 비단조 매트릭스 3회 생성 → stderr 1회. `2_LDPC_light/`에 `warnings` 필터 설정 0곳 | w2 |
| A-18 | LOW | `save()`가 floor_flag를 항상 `-1`로 쓰고 `__init__`이 floor를 보관조차 하지 않는다 | `llr_matrix.py:255`, `llr_matrix.py:86-91` | 실측: 커밋 파일 3개의 floor가 전부 `-1`이라 현재 손실 0. 파일→객체→파일 경로도 없다 (`save()` 호출부는 `run.py:302` 한 곳) | w1 |
| A-19 | LOW | `max_value` 합성값이 DAO의 데이터패스 포화 한계와 도메인이 다르고, 코드베이스 어디서도 소비되지 않는다 | `llr_matrix.py:230, 83-84, 249-250` | 실측: DAO는 실제 최대(28)보다 큰 31(5-bit 한계), 합성은 실제 값의 최대치. `num_bits=3, channel_llr=40` → `max_value=40`. grep 결과 Python은 저장·기록만, C++도 `local_opt.cpp:91-100` 읽기와 `:164-167` 로그뿐 | w1 |

### 부수 발견 (다른 팀 범위와 겹침, 참고용)

| 심각도 | 문제 | 위치 | 인계 대상 |
|--------|------|------|-----------|
| LOW | `save()`의 줄바꿈이 플랫폼 종속이라 같은 파라미터가 OS마다 다른 바이트로 나간다 (`.gitattributes` 없음) | `llr_matrix.py:258` | 팀 D (관점 G 데이터 무결성) |
| LOW | `llr_tables.py`가 죽은 모듈이다 (import 0곳, 참조하는 `llr/` 폴더도 없음, 내용은 3-bit 고정) | `llr_tables.py:1-73` | 팀 C (관점 E 패키지 경계) |
| LOW | 모듈 docstring 2건이 현 설계와 어긋난다 (`load()`가 uniform도 읽는 점, "파일 없이" 합성한다는 서술) | `llr_matrix.py:4, 5-7, 23-26` | 팀 D (관점 H 문서-코드 일치) |
| LOW | `_pm/TODO.md`의 "반전 가능 조건 `ch ≤ 7·dv`"가 리터럴 7로 적혀 균일 모드를 덮지 못하고 `ch = k·top_level` 공명도 담지 못한다 | `_pm/TODO.md:19-21` | 팀 D |
| LOW | `num_bits=0`에서 `top_level`이 float `-0.5`가 되어 원인을 알 수 없는 `TypeError`로 죽는다 (config 경로는 `_check_int` 하한 2가 막는다) | `llr_matrix.py:222` | 팀 B (관점 C config 검증) |

---

## 4. 미커버 영역

팀 A 범위 안에서 이번 라운드가 닿지 못한 곳이다.

- ㉮ **A-11의 인과 재확인**: dv별 ch 차등이 균일 모드 FER에 미치는 방향과 크기. DAO 파일과 같은 ch/top_level 비율(dv2 약 4.0, dv4 약 1.4)로 다시 스윕해야 판정된다.
- ㉯ **0 레벨 유지 여부의 설계 판단**: A-1과 A-5의 수리 방향이 "0 레벨 제거"인지 "min1 하한 도입"인지 "`channel_llr` 제약 추가"인지가 갈린다. 이는 Decision 등급이라 사용자 확인이 필요하고, Round 2가 판정할 사안이 아니다.
- ㉰ **A-4 수리의 등가성 검증**: `new_sgn = np.signbit(vnu_out)`로 바꿨을 때 3-bit 파일 경로의 기존 동작이 완전히 보존되는지. 워커 2, 3이 균일 모드에서만 대조했고 3-bit 경로는 `-0.0`이 발생하지 않는다는 점만 확인했다.
- ㉱ **`needs_csw`가 False인 균일 모드에서 `prev_csw`를 매 iteration 계산하는 비용** (Round 1 agent_2 P13 ㉱). 성능 축이라 팀 C의 실행 검증과 함께 봐야 한다.
- ㉲ **아이디어 서브클래스가 `LLRMatrix`를 상속해 restart가 있는 균일 매트릭스를 만들 때의 동작**. 현재는 config 경로가 없어 실현 불가라고만 확인했다.
- ㉳ **min1 교체 시 min2를 RESET으로 올리는 HW 특성과 0 레벨의 조합**이 min-sum 이론상 타당한지. worker_a_3이 "한 edge만 최대 강도, 나머지 전부 침묵"이라는 극단적 CN이 만들어진다고 지적했으나, 이것이 알고리즘 결함인지 HW 근사의 알려진 대가인지는 판정하지 못했다.
- ㉴ **2SD/3SD 균일 매트릭스의 ch 의미** (A-12). 2SD/3SD 디코딩 산술이 구현되는 시점에 조용히 틀릴 값이라 그때 재검토가 필요하다.
