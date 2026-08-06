# Round 2 / agent_2 — [V2. C++ 대조 — 채널 3종] 분석

> 작성: 2026-08-06 23:05:24
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/channel.py` 전체 (129줄)
> 대조 원본: `0_LDPC_original/channel.cpp`, `ecc_top.cpp`, `random.cpp`, `common.h`
> 관점: Round 1 agent_1 "P2. C++ 대응 정확성 — 채널 3종" 12개 항목 + agent_2 "P3" ㉮~㉴
> 방법: 원문 행 대조 + 스크래치패드 수치 실증 (프로젝트 파일 무수정, Python 실행만 수행)

---

## 0. 결론 한 줄

**HIGH 1건, MEDIUM 2건, LOW 3건.** 산술식(qfunc_inv, dev_from_RBER, Set_R_Offset, Set_LLR_Th,
Get_Mag_2SD/3SD, HD 결정, e1/e2/c1/c2 산출, 슬라이스 배정)은 **전부 원문과 일치**한다.
다만 위치 추출기 `_rand_positions`가 원본 `rand_sel_ep`의 **순서 무작위성을 재현하지 못해**,
`strong_error` 채널이 뽑는 에러 위치가 특정 column block에 극단적으로 몰린다 (HIGH).

---

## 1. HIGH — `_rand_positions`의 argpartition이 순서 무작위성을 깨뜨림

**심각도: HIGH** (틀린 결과를 내지만 예외 없이 진행됨)

**위치**: `channel.py:71-73` ↔ `0_LDPC_original/random.cpp:343-369`

```python
# channel.py:71-73
def _rand_positions(rng, batch, N, k):
    """프레임별 무작위 k개 위치 (비복원) — rand_sel_ep 대응 (XOR25 → numpy)."""
    return np.argpartition(rng.random((batch, N)), k - 1, axis=1)[:, :k]
```

```cpp
// random.cpp:351-368  rand_sel_ep
for (i = 0; i < len_max; i++) { err_position[i] = temp_i; temp_i++; }
for (j = 0; j < n_err_len; j++) {
    tmp = (unsigned int)(xor_r25(memory_for_rng) * 4294967295);
    s = (tmp % (len_max - j)) + j;
    temp = err_position[j];
    err_position[j] = err_position[s];
    err_position[s] = temp;
}
```

원본은 **부분 Fisher–Yates 셔플**이다. 결과 `err_position[0..n_err_len-1]`은 집합도
균일하고 **그 안의 순서도 균일 무작위 순열**이다. 소비 측(`Make_Dec_Input_Fixed_4KB`,
`ecc_top.cpp:1707-1723`)이 이 배열을 `[0:e2)` / `[e2:e2+e1)` / `[e2+e1:e2+e1+c1)`으로
잘라 쓰므로, **순서 무작위성이 곧 strong/weak 배정의 무작위성**이다.

Python의 `argpartition`은 "k번째 순서통계량 기준 분할"만 보장한다. 앞쪽 k개의 **집합**은
균일하지만 **그 안의 배열 순서는 introselect 분할이 남긴 결정적 잔여 순서**이며, 원래 인덱스와
강하게 상관된다.

### 실증 (스크래치패드, 프로젝트 파일 무수정)

㉮ 뽑힌 집합 자체는 균일 (문제 없음) — N=37632를 8구간으로 나눈 히스토그램이 전 구간
   18,275,903 ~ 18,282,779 (기대 18,279,600) 로 평탄.

㉯ 그러나 `strong_error(E=300, SER=0.3, SCR=0.6)`가 실제로 주입하는 **에러 위치 300개**의
   column block(147개) 분포는 완전히 붕괴한다. 40회 × 32프레임 = 384,000 에러, 블록당 기대 2,612:

| | block 0 | block 1 | block 2~11 | ... | block 145 | block 146 |
|---|---|---|---|---|---|---|
| 실측 | 79,189 | 13,831 | 0~13 | | 34,251 | 63,221 |
| 기대 | 2,612 | 2,612 | 2,612 | | 2,612 | 2,612 |

   상위 2개 블록이 전체 에러의 **37.1%**를 차지하고, 중간 블록 다수는 **0회**다.

㉰ strong 에러(`pos[:, :e2]`)만 놓고 보면 카이제곱 = 3,547,197 (자유도 146).
   같은 자리를 `np.argsort`(= Fisher–Yates 등가)로 바꾸면 카이제곱 = 145.7로 정상화된다.

㉱ 대조군: `fixed_error(E=300)`은 뽑힌 k개 **전체**를 flip하므로 순서가 무의미하다.
   실측 블록별 카이제곱 = 140.7 (자유도 146) — **정상**. 즉 이 결함은 `strong_error` 전용이다.

### 영향

- `strong_error` 채널의 FER/BER 곡선은 C++과 비교 불가하다. 에러가 부호의 양 끝 블록
  (예시 부호는 DV 내림차순 배치이므로 마지막 블록군이 dv=2 패리티)에 쏠려, 실제보다
  훨씬 나쁘거나 좋은 FER이 나온다. 프레임 간 상관도 생긴다(같은 인덱스가 반복 선택되는 경향).
- `sd`(strong/weak 라벨)는 현재 디코더가 소비하지 않지만(`decoder.py:345`는 `hd`만 읽음),
  **`hd`의 에러 위치 자체가 편향**되므로 소비 여부와 무관하게 결과가 틀린다.
- `fixed_error`와 `rber`는 영향 없음.

### 수정 방향 (참고)

뽑은 k개를 한 번 더 섞으면 원본과 등가가 된다.
예: `p = np.argpartition(...)[:, :k]` 뒤에 `p = rng.permuted(p, axis=1)`.
(전체 `argsort`도 정확하지만 O(N log N)이라 비용이 크다.)

---

## 2. MEDIUM — SER/SCR 정의역 미검증으로 조용한 오동작

**심각도: MEDIUM** (엣지케이스, 예외 없이 잘못된 채널이 만들어짐)

**위치**: `channel.py:89-112`

`ser`, `scr`가 `[0, 1]` 밖이면 `e1`이나 `c1`이 음수가 되고, numpy의 음수 인덱스/역슬라이스가
**예외 없이** 잘못된 결과를 낸다. 실측 (E=300, N=37632):

| SER | SCR | flips | strong_err | weak_err | weak_cor | 판정 |
|---|---|---|---|---|---|---|
| 1.2 | 0.6 | 300 | 300 | 0 | 14,873 | 조용히 잘못됨 (e1 = -60인데 슬라이스가 빈 구간으로 접힘) |
| -0.2 | 0.6 | 300 | 300 | 0 | **60** | 조용히 잘못됨 (`pos[:, -60:15233]`이 음수 인덱스로 해석) |
| 0.3 | 1.05 | 300 | 90 | 210 | 34,198 | 조용히 잘못됨 (c1 < 0인데 k만 줄어듦) |
| 0.3 | -0.1 | — | — | — | — | `ValueError: kth(=41364) out of bounds (37632)` (우연히 걸림) |

원본 C++도 같은 입력에서 `for (n = e2; ...)`가 음수 인덱스를 읽어 UB가 되므로 "원문 일치"는
아니지만, 이 코드는 이미 다른 곳에서 "원본의 조용한 fallback을 재현하지 않는다"는 방침을
택했다(실험 README "채널 모델" 마지막 항목). `0 <= ser <= 1`, `0 <= scr <= 1` 검사를 두는 것이
그 방침과 일관된다.

---

## 3. MEDIUM — rber 정의역 미검증 (NaN 조용한 전파)

**심각도: MEDIUM**

**위치**: `channel.py:31`, `37-40`, `48-51`

| rber | `dev_from_rber` | 결과 | 비고 |
|---|---|---|---|
| 0.0 | `nan` (RuntimeWarning: divide by zero in log) | 전 비트 `hd=0` | 결과값은 우연히 타당하나 NaN이 조용히 흐른다 |
| 1.0 | 0.3403 | BER 0.0014 | 무의미한 값이 조용히 나온다 |
| 0.6 | 3.9531 | BER 0.3994 | 무의미 |

원본 `qfunc_inv`(`channel.cpp:110-136`)도 동일 산술이라 **C++ 대조로는 일치**하지만,
Python은 `RuntimeWarning`만 찍고 그대로 진행한다. `0 < rber < 0.5` 검사가 없으면
JSON 오타(예: `points: [0.8]`)가 시뮬레이션 끝까지 조용히 통과한다.

참고로 근사 정확도는 문제 없다. 실측 상대오차: p=0.01에서 1.5e-10, p=0.1에서 8.0e-7,
p=0.3에서 4.9e-5. 채널이 실제로 만드는 BER도 목표와 일치한다
(rber=0.01 → 실측 0.010023 / 48,168,960 bit, rber=0.008 → 0.008007).

---

## 4. LOW 3건

### L-1. `n_err` 입력 방어 (`channel.py:83`, `102`)

- `int(n_err)`는 실수를 0 방향 절단한다. `300.9` → `300` (조용히). C++은 int 파라미터라
  이런 입력 자체가 없다.
- `n_err > N`이면 numpy가 `ValueError: kth(=37636) out of bounds (37632)`를 던진다.
  동작은 안전하나 메시지가 어느 설정 항목 때문인지 지목하지 못한다.
- `n_err = 0`은 `argpartition(kth=-1)`이 유효 인덱스라 정상 동작한다 (실측: flip 0개).
  `E = N`도 정상 (실측: c2=0, c1=0, 전 비트 flip, strong_cor=0).

### L-2. README "검증 기록"의 RBER 수치 재현 불가

실험 README:84-85의 "RBER 0.01 → 측정 BER 0.0104"는 재현되지 않는다.
실측: 단일 프레임 0.00983~0.00996(seed 1/2/3), 64프레임 0.01008, 1,280프레임 0.010023.
채널은 정확히 0.01을 만들고 있으므로 **코드가 아니라 문서 수치가 부정확**하다.
(같은 문장의 strong_error 수치는 정확히 재현된다 — 아래 §5 참조.)

### L-3. `Set_Real_Err_Pos_4KB` 항등 가정의 유효 범위

`channel.py:15` docstring은 "vanilla 전제: 쇼트닝/펑처링 없음 → len_noPS = N,
Set_Real_Err_Pos는 항등"이라 선언한다. 원문(`ecc_top.cpp:2701-2720`)을 보면
첫 보정이 `if (tmp_pos >= bit_pos.info_punc_start1) tmp_pos += PUNCTURED_BIT_PRIME_INFO_4KB_SEPERATE;`
이고, 이 상수는 `common.h:710`에서 `50 * BITS_PER_BYTE` = **400 고정**이다
(`punctured_bit_info`에서 유도되지 않는다). 즉 항등이 되려면 `info_punc_start1 >= N`
(= 펑처링 구간이 아예 설정되지 않음)이어야 한다.
**현재 vanilla 실험에서는 문제 없고 docstring에도 선언되어 있으나**, 루트 `CLAUDE.md` ㉰의
목표("외부 H-matrix와 파라미터를 넣어도 동작")에 실물 파라미터를 반입할 때
이 함수는 항등이 아니게 되므로 반입 시 재구현이 필요하다. 방어 코드나 TODO 표시는 없다.

---

## 5. 문제 없음으로 확인한 항목 (원문 행 대조)

### 5-1. `qfunc_inv` — 계수 자리별 완전 일치, 분기 없음

| Python | C++ |
|---|---|
| `channel.py:26-28` `c` 6개 | `channel.cpp:122-126` `c[6]` — 6개 값 전부 자리까지 동일 |
| `channel.py:29-30` `d` 4개 | `channel.cpp:127-130` `d[4]` — 4개 값 전부 자리까지 동일 |
| `channel.py:31` `t = sqrt(-2*log(p))` | `channel.cpp:132` `t = sqrt(-2 * log(p))` |
| `channel.py:32-34` `-num/den`, 호너 전개 순서 | `channel.cpp:133-134` 동일 전개, 동일 부호 |

**분기 없음이 원문과 일치한다.** 원본 `channel.cpp:112-121`은 `a[6]`, `b[5]`(Acklam 중앙
구간 계수)를 선언만 하고 **본문에서 한 번도 참조하지 않는다**. 즉 원본도 정의역 분기 없이
꼬리 구간 근사식 하나만 쓴다. Python이 `a`/`b`를 아예 두지 않은 것은 정확한 재현이다.

### 5-2. `dev_from_rber` — rate 미반영이 원문과 일치

- `channel.py:39` `snr = qfunc_inv(p)**2 / 2.0` ↔ `channel.cpp:75` `u = pow(qfunc_inv(p), 2) / 2;`
- `channel.py:40` `sqrt(1/(2*snr))` ↔ `channel.cpp:86-87` `var = 1 / (2 * SNR); dev = sqrt(var);`
- **rate 곱셈은 원본에도 없다** (Eb/N0 환산 없이 Es/N0 = SNR 그대로). 부호율 미반영이 정확한 대조.
- 호출부 `ecc_top.cpp:490-491`도 `m_gaussian_dev = dev_from_RBER(RBER); m_gaussian_var = dev*dev;`로
  Python `channel.py:48-49` (`dev = dev_from_rber(rber); var = dev*dev`)와 동일.
- 자기정합성 확인: `1/dev = qinv(p)` → `Q(1/dev) = p`. 실측 BER이 목표 RBER과 일치(§3).

### 5-3. BPSK 매핑과 HD 결정 경계 — 부등호 방향 일치

- `channel.py:52` `hd = (cwr < 0).astype(np.uint8)`
- `ecc_top.cpp:1805-1806` `if (cwr[n] >= 0) HD_input[n] = 0; else HD_input[n] = 1;`

두 식은 경계값 0 포함하여 **완전히 동일**하다(`cwr==0` → 양쪽 다 HD 0; numpy에서 `-0.0 < 0`도
False이므로 `-0.0` → HD 0으로 C++ `-0.0 >= 0` == true와 일치). `channel.py:52`의 주석
"C++: cwr >= 0 → HD 0"은 정확한 서술이며, 구현이 그 대우를 쓴 것이다. **문제 없음.**

BPSK 방향(`channel.py:50` `bpsk = 1 - 2*cw`, 즉 0→+1)은 위 HD 규칙과 정합한다.
다만 원본의 `Make_Dec_Input_AWGN` **본체가 저장소에 존재하지 않는다** (`ecc_top.h:77`에 선언,
`ecc_top.cpp:844`에서 호출, 정의는 `0_LDPC_original/`과 `1_LDPC_revised/` 어디에도 없음 —
루트 `CLAUDE.md`가 말하는 "일부 손상"에 해당). 따라서 매핑 방향은 `Make_Dec_Input_AWGN_Quantize`의
HD 규칙에서 **역산으로만** 확인 가능하며, 그 역산 결과가 Python과 일치한다. 직접 행 대조는 불가.

### 5-4. `_R_OFFSET`과 `th = 2·r_offset/var`

| Python | C++ |
|---|---|
| `channel.py:21` `"2SD": (0.35,)` | `channel.cpp:16-18` `MODE_DEC_2SD` → `r_offset = 0.35` (2, 3은 0) |
| `channel.py:21` `"3SD": (0.15, 0.35, 0.55)` | `channel.cpp:19-23` `r_offset=0.15; r_offset2=0.35; r_offset3=0.55` |
| `channel.py:57` `th = [2.0*r/var for r in ...]` | `channel.cpp:35-37` `LLR_th = 2*r_offset/var` (2, 3 동일) |
| `channel.py:56` `m = abs(2.0*cwr/var)` | `ecc_top.cpp:1803-1804` `Lq_ini = (2.0*cwr[n])/var; Lq_ini_m = fabs(Lq_ini);` |

**원본은 LLR 크기(`Lq_ini_m`)와 비교하며, 수신값 자체와 비교하지 않는다.** Python도 동일하다
(양변에서 `2/var`가 약분되므로 결과적으로 `|y| >= r_offset`과 같지만, 식의 형태가 원문 그대로다).
`channel.py:21`의 주석 "Set_R_Offset (channel.cpp:11-29)"도 실제 행(11-29)과 정확히 일치.
`"HD": ()`는 `channel.cpp:13-15`의 전부 0 초기화(HD에서 미사용)와 정합.

`MODE_DEC_1_5SD`(`channel.cpp:24-28`, r_offset 0.15 / -0.15)는 Python에 없고, 지원하지 않는 모드는
`channel.py:46-47`에서 `ValueError`로 **명시적으로 막힌다** (조용한 통과 아님).

### 5-5. 2SD / 3SD region 판정 — 부등호와 sd/cc 배정 일대일 대응

**2SD**: `channel.py:59` `out["sd"] = (m >= th[0])` ↔ `channel.cpp:44-45`
`if (Lq_ini_m >= LLR_th) *sd = 1; else *sd = 0;` — 부등호(`>=`) 포함 동일.

**3SD**: `channel.cpp:52-55`는 4갈래 if-else 체인이고, `channel.py:62-67`은 3번의 마스크
대입이다. 겹쳐 쓰는 순서를 포함해 검증한 결과 **네 region이 일대일 대응**한다:

| 구간 | C++ (`channel.cpp:52-55`) | Python (`channel.py:62-66`) |
|---|---|---|
| `m >= LLR_th3` | `sd=1, cc=1` | `sd[m>=th2]=1` (포함) + `cc[m>=th3]=1` → (1,1) |
| `LLR_th2 <= m < LLR_th3` | `sd=1, cc=0` | `sd[m>=th2]=1`, cc 미대입 → (1,0) |
| `LLR_th <= m < LLR_th2` | `sd=0, cc=0` | 어느 마스크에도 안 걸림 → (0,0) |
| `m < LLR_th` | `sd=0, cc=1` | `cc[m<th1]=1` → (0,1) |

`th1/th2/th3` ↔ `LLR_th/LLR_th2/LLR_th3` 대응도 `_R_OFFSET["3SD"]`의 나열 순서(0.15, 0.35, 0.55)와
`Set_R_Offset`의 대입 순서가 같아 어긋나지 않는다. `cc[m>=th3]=1`(line 65)과 `cc[m<th1]=1`(line 66)이
같은 배열을 두 번 건드리지만 `th1 < th3`이므로 두 마스크가 겹치지 않는다(교집합 공집합).

수치 실증 (rber=0.01, 32프레임): very strong 0.8527 / normal strong 0.0828 / normal weak 0.0443 /
very weak 0.0201, 합 1.0000. 해석적 기대치(|1+N(0,dev)|의 구간 확률) 0.852604 / 0.082807 /
0.044277 / 0.020313과 일치. `channel.py:10-11` docstring의 region 서술도 정확하다.

### 5-6. fixed_error / strong_error 파라미터 산출 — round 규칙 포함 일치

**fixed_error** (`channel.py:76-86` ↔ `ecc_top.cpp:1854-1865`):

| | Python | C++ |
|---|---|---|
| e1 | `k = int(n_err)` | `e1 = num_fixed_err` |
| e2~e4, c2~c4 | 없음 (HD 전용) | `= 0` |
| c1 | 미사용 | `c1 = len_noPS - e1` (HD 분기에서 미사용) |
| 뽑는 길이 | `k = n_err` | `err_pos_len = e1` |

적용부 `ecc_top.cpp:1696-1705`(HD 분기)는 `[0, e1)`을 flip. Python `channel.py:85`는
뽑은 k개 전부를 flip. **일치.**

**strong_error** (`channel.py:103-106` ↔ `ecc_top.cpp:1867-1880`):

| | Python (`channel.py`) | C++ (`ecc_top.cpp`) |
|---|---|---|
| e2 | `:103` `int(np.floor(E*ser + 0.5))` | `:1868-1869` `temp_d = num_fixed_err * fixed_SER; e2 = (int)floor(temp_d + 0.5);` |
| e1 | `:104` `E - e2` | `:1870` `e1 = num_fixed_err - e2;` |
| c2 | `:105` `int(np.floor((N-E)*scr + 0.5))` | `:1873-1874` `temp_d = (len_noPS - e2 - e1) * fixed_SCR; c2 = (int)floor(temp_d + 0.5);` |
| c1 | `:106` `N - E - c2` | `:1875` `c1 = len_noPS - e2 - e1 - c2;` |
| 뽑는 길이 | `:109` `e2 + e1 + c1` | `:1878` `err_pos_len = e2 + e1 + c1;` |

round 규칙이 `floor(x + 0.5)`로 **동일**하다 (agent_2 ㉳). 음수 `x`에서도 양쪽 다 `floor`를 쓰므로
동일하게 동작한다(예: `x = -59.5` → 양쪽 다 -60). `c2`가 계산만 되고 쓰이지 않는 것도
원문과 같다 — C++은 `c2`를 `Make_Dec_Input_Fixed_4KB`에 넘기지만 2SD 분기(`:1707-1723`)에서
사용하지 않는다.

### 5-7. 위치 리스트 슬라이스 의미 — 소비 순서 일치

`ecc_top.cpp:1707-1723` (MODE_DEC_2SD 분기):

```cpp
/* flip */  start_pos = 0;  end_pos = start_pos + e2 + e1;
            for (n = 0; n < end_pos; n++) HD_input[m_err_position[n]] = (…+1)%2;
/* weak */  start_pos = e2; end_pos = start_pos + e1 + c1;
            for (n = start_pos; n < end_pos; n++) SD_input[m_err_position[n]] = 0;
```

`channel.py:111-112`:

```python
hd[row, pos[:, :e2 + e1]] ^= 1              # flip: [0 : e2+e1)
sd[row, pos[:, e2:e2 + e1 + c1]] = 0        # weak: [e2 : e2+e1+c1)
```

**구간 경계가 완전히 동일**하다. 결과 region 배정도 일치한다:
`[0,e2)` = strong 에러 / `[e2,e2+e1)` = weak 에러 / `[e2+e1,e2+e1+c1)` = weak 정정 /
나머지 `c2`개 = strong 정정 (미접촉, 초기값 유지). `channel.py:96-97` docstring 서술도 정확.

초기값도 일치: `ecc_top.cpp:1848-1853`이 `HD_input[n]=cw[n]; SD_input[n]=1; CC_input[n]=1;`로
두는 것과 `channel.py:107-108`의 `hd = cw.copy(); sd = np.ones(...)`가 같다. `CC_input`을
Python이 `None`으로 두는 것은 2SD 분기에서 CC를 전혀 건드리지 않고 디코더도 읽지 않으므로
현재 범위에서 무해하다(3SD 구현 시 재확인 필요).

**채널×모드 조합 제한이 오히려 원본의 잠재 결함을 피한다** (참고 정보):
C++에서 `MODE_CH_FIXED_ERROR` + `MODE_DEC_2SD` 조합이면 `err_pos_len = e1 = E`만 뽑아 놓고
weak 루프가 `[0, e1+c1) = [0, len_noPS)`까지 순회해 초기화되지 않은 `m_err_position` 뒷부분을
읽는다. Python은 `channel.py:78-79`, `98-99`에서 `fixed_error`는 HD 전용, `strong_error`는
2SD 전용으로 명시적으로 막는다 (`CHANNEL_MODES`, `channel.py:124-128`). 타당한 스코프 결정이다.

### 5-8. README 검증 수치 — strong_error 3개 값 정확히 재현

실험 README:84-85 "strong_error E=300/SER=0.3/SCR=0.6 → 에러 300 · strong 에러 90 ·
strong 정정 22399". 실측(N=37632):

```
E=300 SER=0.3 SCR=0.6: err=300, strong_err=90, weak_err=210, strong_cor=22399, weak_cor=14933
```

**정수 단위로 정확히 재현된다** (`e2=90`, `c2=22399`, `c1=14933`, 합 = 37632).
E=N 경계(`c1=0`, `c2=0`)도 예외 없이 동작한다(strong_cor=0, weak_cor=0 확인).
단, §1의 HIGH 결함은 이 **개수**가 아니라 **위치 분포**의 문제이므로 이 재현 결과와 양립한다.

### 5-9. 그 밖에 확인하여 문제 없는 것

- `channel.py:82`, `107`의 `np.asarray(cw, np.uint8).reshape(B, N).copy()`는 `cw`가 이미
  uint8일 때 `asarray`가 원본을 그대로 돌려주므로 `.copy()`가 필수인데, 두 곳 모두 있다.
  입력 `cw` 파괴 없음.
- all-zero codeword 하드코딩은 `channel.py`에 **없다**. 세 함수 모두 임의 codeword를 받아
  동작한다(genie 판정의 all-zero 전제는 `decoder.py` 쪽 문제로, 이 관점 밖).
- `channel.py:5`, `20`, `97`의 원본 함수명·행 번호 인용(`Make_Dec_Input_AWGN`,
  `Make_Dec_Input_Ref_C_Fixed_4KB`, `Make_Dec_Input_Fixed_4KB`, `channel.cpp:11-29`)은
  `Make_Dec_Input_AWGN`(본체 부재, 선언은 실존)을 제외하고 모두 실존·정확.
- `common.h:75-77`(`MODE_DEC_HD/2SD/3SD` = 1/2/3), `common.h:80-82`
  (`MODE_CH_RBER/FIXED_ERROR/STRONG_ERROR` = 1/2/3) 확인. Python의 채널 3종·모드 3종 이름 대응 정확.
- 스코프에서 뺀 원본 채널 모드는 `MODE_CH_ERASURE`(`ecc_top.cpp:1882-1895`)와
  `MODE_CH_3SD_FIXED`(`:1896-1918`) 2종이며, `channel.py` docstring 표(3-7행)에 3종만 적어
  제외 사실이 명시적으로 드러난다.

---

## 6. 심각도별 정리

| # | 심각도 | 요약 | 위치 |
|---|---|---|---|
| 1 | **HIGH** | `argpartition`이 뽑힌 k개의 순서 무작위성을 깨뜨려 `strong_error` 에러 위치가 특정 column block에 극단 편향 (상위 2블록 37.1%) | `channel.py:71-73` ↔ `random.cpp:343-369` |
| 2 | MEDIUM | `ser`/`scr` 범위 미검증 → 음수 인덱스/빈 슬라이스로 조용한 오동작 | `channel.py:89-112` |
| 3 | MEDIUM | `rber` 정의역 미검증 → NaN 및 무의미한 dev가 조용히 전파 | `channel.py:31`, `37-40` |
| 4 | LOW | `n_err` 실수 절단, `n_err > N` 에러 메시지가 설정 항목을 지목 못 함 | `channel.py:83`, `102` |
| 5 | LOW | README "RBER 0.01 → 측정 BER 0.0104" 재현 불가 (실측 0.0100) | 실험 README:84-85 |
| 6 | LOW | `Set_Real_Err_Pos_4KB` 항등 가정은 vanilla 한정 (상수 400 무조건 가산). 실물 반입 시 재구현 필요, 방어/TODO 없음 | `channel.py:15` ↔ `ecc_top.cpp:2707-2708`, `common.h:710` |

## 7. 검증 방법 기록

- 원문 대조: `channel.cpp` 전문(158행), `ecc_top.cpp` 470-509 / 826-865 / 1680-1930 / 2695-2735,
  `random.cpp` 330-370, `common.h` 상수 grep, `ecc_top.h` 선언부.
- 수치 실증(스크래치패드 4개 스크립트, 프로젝트 파일 무수정):
  `qfunc_inv` 정확도 대조(이분법 역Q함수 기준), 실측 BER(최대 48,168,960 bit),
  `argpartition` 순서 편향(구간 히스토그램 + column block별 카이제곱 + `argsort` 대조군),
  경계 입력 8종, 3SD region 비율 대 해석적 기대치.
