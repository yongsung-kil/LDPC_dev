# Round 3 / worker A-1 — F1 (channel.py argpartition 순서 편향) 증거 검증

> 작성: 2026-08-06 23:34:29
> 담당: F1 (HIGH) 의 증거 독립 재확인
> 방법: `0_LDPC_original` 원문 직접 열람 + 스크래치패드 자체 스크립트 5개 (agent_2 스크립트 미사용, 전부 새로 작성)
> 실행 환경: Python 3.11.7, **numpy 1.26.4** (Windows, MSC v.1937 64bit)
> 프로젝트 파일 무수정 (읽기와 in-memory 몽키패치만 사용), C++ 빌드 없음

---

## 0. 결론 한 줄

**F1 발견 자체는 확인됨(CONFIRMED). 심각도 HIGH는 과대이며 실효는 "현행 실행 경로에서 도달 불가한 잠재 결함"이다.**
**F1 처방(`rng.permuted`)은 편향 제거에는 유효하나, rng 스트림을 소비하여 `fixed_error`의 비트 단위 재현성을 깨뜨린다.**
**`np.argsort` 전면 교체가 `fixed_error`에 대해 비트 단위로 완전 무해함을 실측 증명했다 (permuted는 아님).**

---

## 1. 증거별 판정표

| ID | 항목 | 판정 | 근거 |
|----|------|------|------|
| E1-㉮ | 초기화 루프가 identity | **확인됨** | `random.cpp:350-354` `temp_i=0; for(i=0;i<len_max;i++){err_position[i]=temp_i; temp_i++;}` |
| E1-㉯ | 부분 Fisher-Yates 셔플 | **확인됨** | `random.cpp:356-368` `for(j=0;j<n_err_len;j++){ ... s=(tmp%(len_max-j))+j; swap(ep[j],ep[s]); }` |
| E1-행번호 | Round 2 인용 "343-369" | **확인됨** | 함수 시그니처 `random.cpp:343`, 닫는 중괄호 `random.cpp:369`. 본문 350-368. 인용 정확 |
| E1-㉰ | 앞 k개의 **순서까지** 균일 무작위 순열 | **확인됨** | 원문 알고리즘을 Python으로 그대로 옮겨 실측. n=6,k=3, 60만 시행 → 순서있는 3-순열 120종 전수 출현, 카이제곱 114.1 (자유도 119, 임계 144.4). 위치별 값 히스토그램도 균일 |
| E1-㉰-보조 | 모듈로 편향 크기 | **무시 가능** | `tmp % (len_max-j)`, len_max=37632에서 q=floor(2^32/37632)=114,130. 최대 상대 과대표현 = 1/q = **8.76e-06** |
| E1-㉱ | 소비 측이 구간별로 잘라 쓰는가 | **확인됨** | `ecc_top.cpp:1707-1723` (Round 2 인용 정확). 2SD 분기: flip `[0, e2+e1)` (`:1709-1716`), weak `[e2, e2+e1+c1)` (`:1718-1722`) |
| E1-㉱-보조 | 함수 실체와 행 번호 | **확인됨** | `Make_Dec_Input_Ref_C_Fixed_4KB` = `ecc_top.cpp:1828-1920` (strong_error 분기 `:1867-1881`, `rand_sel_ep` 호출 `:1879`). `Make_Dec_Input_Fixed_4KB` = `ecc_top.cpp:1687-1790` (HD 분기 `:1696-1705`) |
| E2-㉮ | 뽑힌 k개 **집합**은 균일 | **확인됨** | 8구간 히스토그램 2,436,259 ~ 2,438,139 (기대 2,437,280). 147 블록 카이제곱 = **85.5** (자유도 146) |
| E2-㉯ | 배열 내 **위치별** 분포는 비균일 | **확인됨** | `pos[:, 0]` 블록 카이제곱 = 932.1 (argsort 138.1). `pos[:, j]`의 min이 항상 정확히 j (introselect의 결정적 잔여 순서 지문) |
| E2-㉰ | `pos[:, :90]` 블록 카이제곱 자릿수 | **확인됨 (자릿수)** | 실측 **2,439,055** (자유도 146). Round 2 보고 3,547,197. **10^6 자릿수 일치**, 정확값은 시드 의존 (내 3개 시드에서 2.27M~2.48M) |
| E2-㉰ | "상위 2블록 37.1%" | **확인됨** | flip 300개 기준 실측 **36.7%** (블록 0 = 78,519 / 블록 146 = 62,239 / 총 384,000). Round 2 보고값 79,189 / 63,221과 1% 이내 |
| E2-㉰ | "중간 블록 다수는 0회" | **확인됨** | 블록 2~11 실측 [2, 2, 6, 11, 2, 9, 7, 11, 7, 8]. Round 2 보고 "0~13"과 일치. 147블록 중 50개가 100회 미만 |
| E2-㉱ | 대조군 argsort / permuted 정상화 | **확인됨** | strong 카이제곱: argpartition 중앙값 1,216,655 / argsort 151.1 / permuted 150.9 (10시드, 자유도 146) |
| E2-㉲ | 실제 flip 300개 위치도 편향 | **확인됨** | flip 블록 카이제곱 = 4,252,837. 블록 0 또는 146에 떨어지는 비율 **0.3184** (균일 기대 0.0136, **23배**) |
| E2-보조 | 프레임 간 상관 | **확인됨** | 두 프레임의 strong 집합(90개) 평균 교집합 = **10.44** (균일 기대 0.215, **48배**). argsort 0.226 / permuted 0.295 |
| E3-㉮ | `permuted(x, axis=1)` = 행별 독립 셔플 | **확인됨** | 동일 행 4개 입력에 permuted → 4행 전부 다른 순열. `permutation(x,axis=1)`과 `shuffle(y,axis=1)`은 4행 전부 **동일** 순열. 20만 행 실측: permuted의 "row0과 같은 행" 비율 5e-06 (독립 기대 2.76e-07, 동일순열 기대 1.0), permutation은 1.000000 |
| E3-㉯ | permuted 후 카이제곱 정상 범위 | **확인됨** | strong 카이제곱 10시드 min 125.8 / 중앙값 150.9 / max 164.8. 전부 임계 176.0 미만 |
| E3-㉰ | permuted ≟ argsort (통계적 구분 불가) | **확인됨** | 2×147 동질성 카이제곱 = **143.9** (자유도 146, 임계 176.0) → 구분 불가. 각자 균일성 카이제곱 148.1 / 147.1 |
| E3-㉱ | 비용 (N=37632, B=128) | **확인됨** | k=15233: argpartition 63.8ms / +permuted 94.1ms (1.48배) / argsort 288.3ms (4.52배). k=300: 53.4 / 55.0 (1.03배) / 288.0ms (5.39배) |
| E4-㉮ | permuted가 rng 상태를 소비 | **확인됨** | 동일 시드 두 rng, 한쪽만 permuted 호출 → 이후 `random(5)`가 완전히 다름. 크기 (1,2)의 최소 배열에서도 상태 변화 |
| E4-㉯ | fixed_error 첫 배치 flip 집합 동일 | **확인됨** | seed 999, B=8: 배치 0의 8프레임 전부 flip 집합 완전 일치 (교집합 300/300) |
| E4-㉯ | 두 번째 이후 배치는 달라짐 | **확인됨** | 배치 1, 2는 frame0 교집합 **1/300**. seed 31337 5배치 연속 실행에서 배치 0만 일치, 1~4 전부 불일치 |
| E4-㉯ | "fixed_error 결과 불변" 주장 | **부분 반박됨** | 통계 단위로는 참, **비트 단위 재현성은 첫 배치 이후 전부 깨진다**. 5배치 후 rng tail: 현행 [0.00994688, …] vs permuted [0.00761032, …] |
| E4-㉰ | rber는 `_rand_positions` 미호출 | **확인됨** | `channel.py`에서 `_rand_positions(` 호출은 `:83`(fixed_error)과 `:109`(strong_error) 두 곳뿐. `rber_channel` 소스에 미등장 |
| E4-㉲ | 통계 결과 불변 | **확인됨** | fixed_error 블록 카이제곱 5시드: argpartition [129.5, 140.5, 128.2, 173.5, 149.9] vs permuted [150.7, 142.9, 146.6, 136.3, 156.2] (동일 분포) |
| E4-추가 | **argsort는 fixed_error에 비트 단위로 무해** | **신규 확인** | seed 31337 5배치 연속: argsort 결과 hd가 5배치 **전부** 현행과 완전 일치, rng tail도 완전 일치. permuted는 배치 0만 일치 |
| E5 | strong_error가 run.py 경유 도달 불가 | **확인됨** | 3개 설정 실행 실측. `run.py:89` `mode = dec.matrix.mode if dec.matrix is not None else "HD"` + `decoder.py:62-64` (2SD/3SD 차단) → mode는 항상 "HD" → `run.py:90-93`이 `CHANNEL_MODES["strong_error"]=("2SD",)`와 불일치로 ValueError |
| E5 | fixed_error 경로 영향 없음 (agent_2 ㉱) | **확인됨** | 카이제곱 140.5 등 (Round 2 보고 140.7과 사실상 동일). argpartition과 argsort의 카이제곱이 **자릿수까지 완전 동일** (집합이 같으므로) |

---

## 2. E1 — 원본 `rand_sel_ep` 직접 확인

### 2-1. 원문 (직접 열람, 행 번호 실측)

`0_LDPC_original/random.cpp` 343~369행 (시그니처 343, 닫는 중괄호 369). Round 2 인용 "343-369"는 정확하다.

```cpp
// random.cpp:343
void rand_sel_ep(int* err_position, int len_max, int n_err_len, int type)
{
    ...
    temp_i = 0;                                        // :350
    for (i = 0; i < len_max; i++) {                    // :351   ← ㉮ identity 초기화
        err_position[i] = temp_i;
        temp_i++;
    }

    for (j = 0; j < n_err_len; j++) {                  // :356   ← ㉯ 부분 Fisher-Yates
        if (MODE_RANDOM_TYPE_SRAND == type) {
            tmp = (unsigned int)(rand() * rand());
        }
        else if (MODE_RANDOM_TYPE_XOR_25 == type) {
            tmp = (unsigned int)(xor_r25(memory_for_rng) * 4294967295);   // :361
        }
        s = (tmp % (len_max - j)) + j;                 // :363   ← j..len_max-1 에서 뽑음
        temp = err_position[j];                        // :365
        err_position[j] = err_position[s];             // :366
        err_position[s] = temp;                        // :367
    }
}
```

㉮ 확인됨, ㉯ 확인됨. `s`가 `[j, len_max-1]` 범위이고 `err_position[j]`와 swap하는 전형적인 Durstenfeld 전방 변형이다.

### 2-2. ㉰ 순서까지 균일한가 (독립 실증)

수학적으로는 앞 k개가 균일 무작위 k-순열이 되는 표준 알고리즘이다. 원문을 그대로 Python으로 옮겨 실측했다.

```python
def rand_sel_ep(len_max, n_err_len, rnd):
    ep = list(range(len_max))                    # random.cpp:351-354
    for j in range(n_err_len):                   # :356
        s = (rnd() % (len_max - j)) + j          # :363
        ep[j], ep[s] = ep[s], ep[j]              # :365-367
    return ep[:n_err_len]
```

```
n=6 k=3, 60만 시행:
  distinct ordered tuples seen = 120 / 120
  expected count per tuple = 5000.0, observed min=4865 max=5187
  chi2 = 114.1, df = 119 (critical p=0.05 ~ 144.4)
  per-position value histogram (expect ~33333 each):
    pos 0: [33479, 33561, 33276, 33280, 33130, 33274]
    pos 1: [33081, 33613, 33325, 33238, 33510, 33233]
    pos 2: [33219, 33207, 33191, 33586, 33388, 33409]
```

**순서있는 k-튜플 전수가 균일하게 나온다.** ㉰ 확인됨.

모듈로 편향은 실효 없다. len_max=37632에서 `2^32 = 114130 × 37632 + 27136`이므로, 27,136개 값이 114,131회, 나머지가 114,130회를 받는다. 최대 상대 과대표현 = 1/114,130 = **8.76e-06**. 무시 가능하다.

### 2-3. ㉱ 소비 측의 구간 슬라이스 (실제 행 번호)

`Make_Dec_Input_Ref_C_Fixed_4KB` = `ecc_top.cpp:1828-1920`. strong_error 분기는 `:1867-1881`이며 `:1879`에서 `rand_sel_ep`를 호출한다.
슬라이스를 실제로 쓰는 곳은 `Make_Dec_Input_Fixed_4KB` = `ecc_top.cpp:1687-1790`이다.

```cpp
// ecc_top.cpp:1707-1723  (MODE_DEC_2SD 분기)
else if (MODE_DEC_2SD == m_param_dec->init_n) {
    /* flip */
    start_pos = 0;                                     // :1709
    end_pos = start_pos + e2 + e1;                     // :1710
    for (int n = 0; n < end_pos; n++) {                // :1711
        HD_input[m_err_position[n]] = (HD_input[m_err_position[n]] + 1) % 2;
        ...
    }
    /* weak */
    start_pos = e2;                                    // :1718
    end_pos = start_pos + e1 + c1;                     // :1719
    for (int n = start_pos; n < end_pos; n++) {        // :1720
        SD_input[m_err_position[n]] = 0;               // :1721
    }
}
```

Round 2 인용 "1707-1723"은 **정확하다**. 구간 경계 `[0, e2+e1)`과 `[e2, e2+e1+c1)`도 `channel.py:111-112`와 정확히 대응한다.
HD 분기는 `:1696-1705`로 `[0, e1)`만 flip하며, weak 슬라이스를 쓰지 않는다 (그래서 `fixed_error`에는 순서가 무의미하다).

즉 **순서 무작위성이 곧 strong/weak 배정의 무작위성**이라는 Round 2의 서술은 원문 대조로 확인된다.

---

## 3. E2 — argpartition 편향 독립 재현

### 3-1. 파라미터 (요구된 실제 값 사용)

```
N_b=147, z=256 → N=37632
E=300, SER=0.3, SCR=0.6
  e2 = floor(300*0.3+0.5)      = 90
  e1 = 300 - 90                = 210
  c2 = floor(37332*0.6+0.5)    = 22399
  c1 = 37632 - 300 - 22399     = 14933
  k  = e2+e1+c1                = 15233
규모: B=32 프레임 × 40회 = flip 384,000개 / strong 115,200개 (Round 2와 동일 규모)
```

### 3-2. 핵심 코드

```python
def pick_argpartition(rng, b, n, k):
    return np.argpartition(rng.random((b, n)), k - 1, axis=1)[:, :k]

def pick_argsort(rng, b, n, k):
    return np.argsort(rng.random((b, n)), axis=1)[:, :k]

def pick_permuted(rng, b, n, k):
    p = np.argpartition(rng.random((b, n)), k - 1, axis=1)[:, :k]
    return rng.permuted(p, axis=1)

strong_blk += np.bincount(pos[:, :e2].ravel() // Z, minlength=N_B)   # 블록 = 인덱스 // 256
```

### 3-3. 실측 출력 (seed 20260806)

```
=== argpartition (현행 channel.py:71-73) ===
  집합(k개) 8구간 히스토그램: [2438139, 2436985, 2436690, 2437122, 2436259, 2437408, 2437949, 2437688]  (기대 2437280)
  집합 블록(147) 카이제곱 = 85.5
  strong 에러 pos[:, :90]: total=115,200 기대/블록=783.7 카이제곱=2,439,054.9
     상위3 블록 [146, 0, 145] 값 [34621, 27412, 4395], 상위2블록 점유율 53.8%
  flip 전체 pos[:, :300]: total=384,000 기대/블록=2,612.2 카이제곱=4,252,836.9
     상위3 블록 [0, 146, 145] 값 [78519, 62239, 33642], 상위2블록 점유율 36.7%
  pos[:, 0]: 카이제곱=932.1

=== argsort (대조군) ===
  집합 8구간 히스토그램: (argpartition과 완전히 동일)
  strong 카이제곱=157.5 / flip 카이제곱=162.9 / pos[:,0] 카이제곱=138.1

=== argpartition + rng.permuted (처방) ===
  strong 카이제곱=186.3 / flip 카이제곱=128.7 / pos[:,0] 카이제곱=165.0
```

### 3-4. 분포 형태 (147 블록 전수, flip 300개)

```
blk   0- 20: [78519, 13605, 2, 2, 6, 11, 2, 9, 7, 11, 7, 8, 13, 13, 15, 13, 12, 13, 19, 11, 20]
blk  21- 41: [11, 27, 18, 19, 13, 21, 18, 22, 21, 26, 26, 44, 24, 38, 39, 32, 23, 44, 47, 33, 43]
blk  42- 62: [48, 43, 41, 47, 48, 54, 73, 84, 85, 96, 138, 108, 146, 156, 284, 532, 861, 1865, 2738, 2945, 2833]
blk  63- 83: [3039, 3173, 3154, 2831, 3057, 2929, 3190, 3426, 3079, 2662, 2819, 2535, 2511, 2386, 2258, 1961, 2109, 2242, 2093, 1943, 1913]
...
blk 126-146: [816, 1035, 913, 714, 795, 727, 819, 891, 983, 922, 990, 1049, 1234, 1720, 2292, 3282, 5308, 9403, 16921, 33642, 62239]

flip min = 2 (블록 2), max = 78,519 (블록 0). 100회 미만 블록 50개, 1000회 미만 70개.
블록 0 또는 146에 떨어지는 비율 = 0.3184 (균일 기대 0.0136)
```

이 형태는 **Round 2 보고와 사실상 동일하다** (블록 0 79,189 → 78,519, 블록 146 63,221 → 62,239, 블록 145 34,251 → 33,642, 블록 2~11 "0~13" → 2~11). 시드가 달라도 형태가 재현되는 결정적 편향이다.

### 3-5. 다중 시드 안정성 (10시드, 자유도 146, 임계값 176.0)

```
argpartition  strong chi2: min=1,098,614 med=1,216,655 max=1,277,530
              flip   chi2: min=1,974,467 med=2,161,321 max=2,238,059
argsort       strong chi2: min=133.1 med=151.1 max=168.2
              flip   chi2: min=111.6 med=139.2 max=153.1
permuted      strong chi2: min=125.8 med=150.9 max=164.8
              flip   chi2: min=129.0 med=155.0 max=175.2
```

(3-3의 40회 실행과 이 표의 20회 실행은 표본 수가 2배 다르므로 카이제곱 절대값이 다르다. 방법 간 비교만 유효하다.)

**참고**: 3-3에서 permuted의 strong 카이제곱 186.3이 임계 176을 넘었으나, 10시드 반복에서 max 164.8로 정상 범위임이 확인되었다. 단일 시드의 우연이다.

### 3-6. 프레임 간 상관 (Round 2 §영향의 부수 주장 검증)

```
두 프레임의 strong 집합(90개) 교집합, 균일 기대 = 90*90/37632 = 0.215
  argpartition  mean overlap = 10.437  max = 34    ← 48배
  argsort       mean overlap =  0.226  max = 3
  permuted      mean overlap =  0.295  max = 3

fixed_error flip 집합(300개) 교집합, 균일 기대 = 2.392
  argpartition / argsort / permuted 전부 mean = 2.305, max = 7  ← 완전 동일
```

**numpy 버전 의존성 주의**: 이 결과는 numpy 1.26.4의 introselect 구현 기준이다. 편향의 방향과 크기는 구현 세부에 의존할 수 있으나, "argpartition은 앞쪽 k개의 순서를 보장하지 않는다"는 것은 API 계약상의 사실이므로 버전과 무관하게 결함이다.

---

## 4. E3 — 처방 `rng.permuted(p, axis=1)` 의 유효성

### 4-1. ㉮ 의미론 실측

```
input rows (all identical 0..5), 4행:
  permuted(x, axis=1)          permutation(x, axis=1) / shuffle(y, axis=1)
  [[3 2 5 4 0 1]               [[3 2 5 4 0 1]
   [4 5 1 2 0 3]                [3 2 5 4 0 1]
   [3 2 0 5 4 1]                [3 2 5 4 0 1]
   [5 4 2 1 3 0]]               [3 2 5 4 0 1]]

20만 행 정량 확인 (n=10):
  permuted:    row0과 같은 행 비율 = 0.000005   (독립 기대 1/10! = 2.756e-07)
  permutation: row0과 같은 행 비율 = 1.000000   (모든 행에 동일 순열)
  permuted col0 값 히스토그램: [20087, 19963, 20032, 19943, 20041, 20041, 20021, 20099, 19759, 20014]
```

**`permuted`만 행별 독립 셔플이다.** `permutation`과 `shuffle`은 axis=1에서 모든 행에 같은 순열을 적용하므로 이 용도에 **쓰면 안 된다**. 처방이 `permuted`를 지목한 것은 정확하다.

### 4-2. ㉰ argsort와 통계적 구분 불가

```
argsort total=576,000  permuted total=576,000  (B=64 × 100회)
2x147 동질성 카이제곱 = 143.9  (자유도 146, 임계 p=0.05 ~ 176.0)  → 구분 불가
argsort 자체 균일성 카이제곱  = 148.1
permuted 자체 균일성 카이제곱 = 147.1
pos[:,0] 블록 카이제곱: argsort 139.3 / permuted 128.7
```

### 4-3. ㉱ 비용 (N=37632, B=128, 7회 반복 중앙값)

| 방식 | k=15233 (strong_error) | k=300 (fixed_error) |
|------|------------------------|---------------------|
| argpartition (현행) | 63.75 ms | 53.44 ms |
| argpartition + permuted | 94.09 ms (1.48배) | 54.96 ms (1.03배) |
| argsort | 288.30 ms (4.52배) | 287.95 ms (5.39배) |

permuted 비용은 k에 비례한다. `fixed_error`의 k=300에서는 사실상 무료(3%)이고, `strong_error`의 k=15233에서만 48% 증가한다.

---

## 5. E4 — 처방의 부작용 (rng 상태 소비)

### 5-1. ㉮ permuted는 rng 상태를 소비한다

```python
r1 = np.random.default_rng(42); r2 = np.random.default_rng(42)
_ = r2.permuted(np.arange(20).reshape(2, 10), axis=1)
```
```
  no-permuted    next random(5): [0.773956, 0.438878, 0.858598, 0.697368, 0.094177]
  after-permuted next random(5): [0.822762, 0.443414, 0.227239, 0.554585, 0.063817]
  shape (1,2) / (2,10) / (128,15233) 전부 bit_generator state 변화 확인
```

**확인됨.** 최소 크기 배열에서도 소비한다.

### 5-2. ㉯ fixed_error 결과 변화 (seed 999, B=8, E=300)

```
batch 0: flip SET identical across all 8 frames? True    (frame0 교집합 300/300)
batch 1: flip SET identical across all 8 frames? False   (frame0 교집합   1/300)
batch 2: flip SET identical across all 8 frames? False   (frame0 교집합   1/300)
```

seed 31337, 5배치 연속 실행 (프로젝트 `chan.fixed_error_channel` 실제 호출, in-memory 몽키패치):

```
  batch : argsort==current ?   permuted==current ?
    0   :  True                 True
    1   :  True                 False
    2   :  True                 False
    3   :  True                 False
    4   :  True                 False
  5배치 후 rng tail:
    current : [0.00994688, 0.25072195, 0.46719244]
    argsort : [0.00994688, 0.25072195, 0.46719244]   ← 완전 일치
    permuted: [0.00761032, 0.35100843, 0.97896458]   ← 스트림 분기
```

**"fixed_error 결과 불변" 가설은 배치 단위/통계 단위로만 참이다.** 첫 호출의 집합은 동일하나, permuted가 rng를 소비하는 순간 이후 모든 배치가 갈라진다. 비트 단위 재현성(같은 시드 → 같은 CSV)은 깨진다.

### 5-3. ㉰ rber 무영향

`channel.py` 전체에서 `_rand_positions(` 호출은 두 곳뿐이다.

```
def _rand_positions(rng, batch, N, k):            # 정의 :71
pos = _rand_positions(rng, B, N, int(n_err))      # :83   fixed_error
pos = _rand_positions(rng, B, N, e2 + e1 + c1)    # :109  strong_error
```

`rber_channel` (`channel.py:43-68`)은 `rng.normal`만 쓴다. 또한 `run.py:122-126`이 포인트마다 새 rng를 만들고 채널은 `channel.use` 하나만 실행되므로, 채널 간 rng 공유도 없다. **무영향 확인됨.**

### 5-4. ㉲ 통계 결과 불변 (fixed_error 블록 카이제곱, 5시드)

```
argpartition  chi2: [129.5, 140.5, 128.2, 173.5, 149.9]   (자유도 146, 임계 176.0)
argsort       chi2: [129.5, 140.5, 128.2, 173.5, 149.9]   ← argpartition과 자릿수까지 완전 동일
permuted      chi2: [150.7, 142.9, 146.6, 136.3, 156.2]   ← 다른 표본, 같은 분포
```

argpartition과 argsort의 카이제곱이 **완전히 같은 값**인 것이 결정적이다. 두 방식이 뽑는 **집합이 동일**하고 `fixed_error`가 집합 전체를 flip하므로 결과가 비트 단위로 같다. 실제로 `strong_error` 파라미터에서 확인하면:

```
k-set identical: True      array order identical: False
flip subset [0:300] identical as a set: False
```

**집합은 같고 순서만 다르다.** 이것이 `fixed_error` 무해성과 `strong_error` 결함의 동시 근거다.

### 5-5. ㉱ 대안 처방 3종 비교 (실측 근거)

| | (a) `_rand_positions` 내부 permuted | (b) `strong_error_channel`에서만 permuted | (c) argsort 전면 교체 |
|---|---|---|---|
| strong_error 편향 제거 | 예 (카이제곱 150.9) | 예 (동일) | 예 (카이제곱 151.1) |
| fixed_error 비트 재현성 | **깨짐** (배치 1부터 불일치, rng tail 분기) | 유지 (호출 자체가 없음) | **완전 유지** (5배치 hd와 rng tail 전부 일치) |
| rber 영향 | 없음 | 없음 | 없음 |
| 비용 (B=128, k=15233) | 94.1 ms (+48%) | 94.1 ms (+48%) | 288.3 ms (+352%) |
| 비용 (B=128, k=300) | 55.0 ms (+3%) | 53.4 ms (변화 없음) | 288.0 ms (+439%) |
| 구현 위치 | 1곳 (`channel.py:73`) | 1곳 (`channel.py:109` 뒤) | 1곳 (`channel.py:73`) |
| 의미론적 정합 | 두 채널 모두 원본 등가 | 두 채널 모두 원본 등가 (fixed_error는 순서 무관) | 두 채널 모두 원본 등가 |

**권고**: 재현성 보존이 우선이면 (c) argsort 전면 교체 또는 (b) strong_error 한정 permuted다. 성능과 재현성을 둘 다 잡으려면 (b)가 최선이며, (a)는 얻는 것 없이 `fixed_error`의 기존 CSV 재현성만 잃는다. (b)는 현재 `strong_error`가 실행되지 않으므로 실질 비용이 0이다.

---

## 6. E5 — F1의 실효 심각도 교차 확인

### 6-1. 도달 불가 경로 추적 (코드 + 실행 실측)

```
run.py:89    mode = dec.matrix.mode if dec.matrix is not None else "HD"
             ├─ llr_matrix 미지정 → dec.matrix is None → mode = "HD"
             └─ llr_matrix 지정   → decoder.py:62-64 가 mode != "HD" 를 NotImplementedError 로 차단
                                    → 통과한 dec.matrix.mode 는 항상 "HD"
run.py:90-93 if mode not in chan.CHANNEL_MODES[ch_type]: raise ValueError
channel.py:127  CHANNEL_MODES["strong_error"] = ("2SD",)
             → "HD" not in ("2SD",) → 항상 ValueError
channel.py:98-99 strong_error_channel 자체도 mode != "2SD" 를 ValueError 로 재차 차단
```

실행 실측 3케이스 (스크래치패드에서 `LDPC_base.run.main()` 직접 호출, 출력은 스크래치패드로):

```
case cfg_hd.json    (llr_matrix = LLR_MATRIX_HD_1.txt)
  -> ValueError: channel strong_error은 ('2SD',) 전용 — 현재 디코딩 모드 HD (LLR matrix 파일명 확인)
case cfg_nomx.json  (llr_matrix 없음)
  -> ValueError: channel strong_error은 ('2SD',) 전용 — 현재 디코딩 모드 HD (LLR matrix 파일명 확인)
case cfg_2sd_name.json (2SD 이름 파일)
  -> FileNotFoundError  (Input/LLR/ 에는 LLR_MATRIX_HD_0.txt, LLR_MATRIX_HD_1.txt 2개뿐)
```

HD 파일을 `LLR_MATRIX_2SD_9.txt`로 복사해 억지로 2SD 모드를 만들어도 차단된다.

```
loaded matrix mode = 2SD  ch_len = 2  th_len = 2
-> NotImplementedError: llr_matrix 2SD/3SD는 채널 region 매핑 미구현 — 현재 HD만 지원   (decoder.py:62-64)
```

**agent_5 M-3의 "어떤 설정으로도 실행 불가" 주장은 확인됨.** 차단은 이중(디코더 생성자 + run.py 모드 검사)이고, 나아가 `strong_error_channel` 자신도 세 번째 방어선을 갖는다.

### 6-2. fixed_error 경로 영향 (agent_2 ㉱ 독립 재현)

`fixed_error`는 뽑은 k개를 전부 flip하므로 순서를 소비하지 않는다. 5-4에서 argpartition과 argsort의 카이제곱이 **자릿수까지 동일**하고 (129.5 / 140.5 / 128.2 / 173.5 / 149.9), 5-2에서 hd 배열이 5배치 전부 비트 단위로 동일함을 확인했다. Round 2가 보고한 140.7은 이 범위 안이다. **영향 없음 확인됨.**

### 6-3. 판정에 필요한 사실 정리

- ㉮ F1이 실제로 잘못된 결과를 내는 경로는 `strong_error` 하나뿐이며, 그 채널은 현행 코드에서 세 겹으로 차단되어 실행되지 않는다
- ㉯ `fixed_error`와 `rber`는 비트 단위로 무해하다 (추정이 아니라 실측)
- ㉰ 그러나 결함은 `_rand_positions` (`channel.py:71-73`)라는 **공용 헬퍼**에 있고, 그 docstring이 "rand_sel_ep 대응"이라고 선언한다. 이 선언이 거짓이므로, 향후 2SD 지원이 열리는 순간 조용히 발현한다
- ㉱ `strong_error` 실행을 막는 것은 `decoder.py:62-64`의 "2SD/3SD 채널 region 매핑 미구현"이다. 이는 명시적 TODO 성격의 차단이므로 해제될 예정의 코드다. 즉 "영구적 도달 불가"가 아니라 **"다음 기능 추가 시 발현하는 시한 결함"** 이다
- ㉲ 결함의 크기는 잠재적으로 크다 (에러의 31.8%가 147개 중 2개 블록에 집중, 프레임 간 상관 48배). 발현하면 FER 곡선이 무의미해지고, 그것이 편향 때문이라는 것을 알아채기 어렵다 (예외 없이 그럴듯한 숫자가 나온다)

---

## 7. 최종 판정

### 7-1. "F1 발견 자체"에 대한 판정

**CONFIRMED (발견 유효). 단 심각도는 HIGH → MEDIUM 하향 권고.**

근거:
- ㉮ 기술적 사실 관계는 전부 독립 재확인되었다. 원본은 부분 Fisher-Yates로 **순서까지 균일**하고 (E1-㉰ 실측 카이제곱 114.1/자유도 119), Python `argpartition`은 순서를 보장하지 않으며 (E2-㉯), 소비 측이 순서를 구간으로 잘라 쓴다 (E1-㉱, `ecc_top.cpp:1707-1723`). 세 고리 전부 확인됨
- ㉯ 편향의 크기도 재현되었다. Round 2가 보고한 "상위 2블록 37.1%"는 실측 36.7%, 블록별 개수는 1% 이내로 일치한다. 카이제곱 3,547,197은 실측 2,439,055로 절대값이 다르나 **10^6 자릿수는 일치**하며, 시드 간 변동(2.27M~2.48M)을 감안하면 결론에 영향이 없다. Round 2의 인용 행 번호(`random.cpp:343-369`, `ecc_top.cpp:1707-1723`)도 전부 정확하다
- ㉰ 하향 근거: 이 결함이 잘못된 결과를 내는 유일한 경로(`strong_error`)가 현재 **세 겹으로 차단되어 실행 불가**하다 (E5 실측). Round 2 심각도 기준의 HIGH는 "틀린 결과를 내지만 예외 없이 진행됨"인데, 현행 코드에서는 예외로 막히므로 이 정의에 해당하지 않는다. "향후 2SD 지원 시 조용히 발현할 결함"에 해당하는 MEDIUM이 정확하다
- ㉱ 다만 하향은 "고치지 않아도 된다"는 뜻이 아니다. `_rand_positions`의 docstring이 "rand_sel_ep 대응"이라 선언한 것이 사실이 아니므로, 코드를 고치든 docstring에 한계를 명시하든 둘 중 하나는 필요하다

### 7-2. "F1 처방(`rng.permuted`)"에 대한 판정

**정확성은 유효, 처방 위치는 재고 필요.**

근거:
- ㉮ `rng.permuted(p, axis=1)`가 행별 독립 셔플이라는 전제는 확인됨 (E3-㉮). `permutation`/`shuffle`은 모든 행에 같은 순열을 적용하므로 오답이며, 처방이 `permuted`를 정확히 지목한 것은 옳다
- ㉯ 편향 제거 효과도 확인됨. 카이제곱 2,439,055 → 150.9 (자유도 146), argsort와 통계적으로 구분 불가 (2×147 동질성 카이제곱 143.9)
- ㉰ "전체 argsort도 정확하나 비용 큼"도 확인됨 (288.3 ms vs 94.1 ms, 4.5배 대 1.5배)
- ㉱ **그러나 처방이 놓친 것**: `permuted`는 rng 상태를 소비한다 (E4-㉮ 실측). `_rand_positions` 내부에 넣으면 `fixed_error`의 **두 번째 배치부터 결과가 달라진다** (E4-㉯: 배치 1의 frame0 교집합 1/300, rng tail 분기). Round 2 §1은 "`fixed_error`와 `rber`는 영향 없음"이라 단정했으나, 이는 **결함의 영향**에 대해서만 참이고 **처방의 영향**에 대해서는 거짓이다. 이미 저장된 `Sim_Output/fer_fixed_error.csv` 같은 결과의 재현이 불가능해진다
- ㉲ **더 나은 대안이 존재한다**: `np.argsort` 전면 교체는 `fixed_error`에 대해 **비트 단위로 완전 무해**하다 (E4-추가: 5배치 hd 전부 일치, rng tail까지 일치). argpartition과 argsort가 같은 집합을 뽑고 `fixed_error`는 집합 전체를 쓰므로 수학적으로 보장되며 실측으로도 확인했다. 비용이 4.5배이나, `strong_error`가 실행되지 않는 현재 상황에서 실제 비용은 `fixed_error`의 k=300 경로뿐이다 (53 ms → 288 ms)
- ㉳ **최소 부작용 처방**: `strong_error_channel` 안에서만 (`channel.py:109` 직후) permuted를 적용하면 편향은 제거하면서 `fixed_error`/`rber`의 rng 스트림은 손대지 않는다. 실질 비용 0, 재현성 손실 0이다

**권고 우선순위**: ㉮ `strong_error_channel` 한정 permuted (부작용 0), ㉯ argsort 전면 교체 (비트 재현성 유지, 비용 증가), ㉰ `_rand_positions` 내부 permuted (Round 2 원 처방, `fixed_error` 재현성 상실).
어느 경우든 `_rand_positions` docstring의 "rand_sel_ep 대응" 문구와 순서 보장 여부를 함께 명시해야 한다.

---

## 8. 검증 방법 기록

원문 직접 열람:
- `0_LDPC_original/random.cpp` 320-390 (`rand_sel_ep` 전문)
- `0_LDPC_original/ecc_top.cpp` 1680-1800 (`Make_Dec_Input_Fixed_4KB` 전문), 1812-1940 (`Make_Dec_Input_Ref_C_Fixed_4KB`), 2695-2740 (`Set_Real_Err_Pos_4KB`)
- `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/` 의 `channel.py` 전문, `run.py` 전문, `decoder.py` 1-110, `llr_matrix.py` 전문
- grep: `rand_sel_ep`, `m_err_position`, `strong_error|CHANNELS\[|CHANNEL_MODES|_rand_positions`

스크래치패드 자체 스크립트 6개 (전부 새로 작성, agent_2 스크립트 미참조, 프로젝트 파일 무수정):
- `e2_bias.py`: 3방식 집합, 순서, 블록 카이제곱 비교
- `e2b_shape.py`: 147블록 전수 분포, `pos[:, j]` 구조
- `e2c_extra.py`: 모듈로 편향 정량, 프레임 간 교집합
- `e3_permuted.py`: permuted, permutation, shuffle 의미론과 10시드 카이제곱, 2×147 동질성, 타이밍
- `e4_rngstate.py`: rng 상태 소비, `chan.fixed_error_channel` 실호출 배치 비교, rber 독립성
- `e4e_argsort_dropin.py`: argsort 비트 단위 드롭인 검증
- `e1_e5b.py`: `rand_sel_ep` 원문 전사 후 순서 균일성 검정, 2SD 강제 파일 차단 확인
- `e5_reach.py`: `LDPC_base.run.main()` 3케이스 실행 (출력 디렉터리는 스크래치패드)

프로젝트 파일 수정 0건, C++ 빌드 0건.
