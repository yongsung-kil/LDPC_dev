# Round 3 검증팀 a / 워커 1 — A-1(공명), A-5(mag 0의 min1 점유), "0 레벨 제거" 처방

작성 2026-08-08 15:45:19. Round 2의 스크립트와 결론을 쓰지 않고 코드에서 직접 유도하고
직접 실행해 증거를 새로 확보했다.

---

## ㉮ 가설별 증거 확인 표

### H1 (A-1) — `channel_llr`가 `top_level`의 정수배일 때 공명

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|-----------|------|
| E1-1 `top_level` 정의와 `edge_mag`의 0 포함 | **확인됨** | `llr_matrix.py:222` `top_level = 2**(num_bits-1) - 1`<br>`llr_matrix.py:224` `th = list(range(top_level, 0, -1))`<br>`llr_matrix.py:225` + `49-51` `uniform_edge_mag`가 `range(top,-1,-1)` 반환 | num_bits 4 → top 7, edge_mag `[7,6,5,4,3,2,1,0]`<br>num_bits 6 → top 31, edge_mag `[31,...,1,0]` |
| E1-2 iteration 1에서 C2V가 전부 RESET = `edge_mag[0]` | **확인됨** | `decoder.py:208, 219-223` min1=min2=RESET, min1_pos=-1, check_sum=0, edge_sgn=0<br>`decoder.py:124` iteration 1은 edge clear<br>`decoder.py:174` edge clear면 remove old 생략<br>`decoder.py:135-137` min1_pos(-1) != edge → check_out = min1 = RESET, sign = syndrome | iteration 1의 첫 column 4개 edge 전부 \|C2V\| 고유값 `[7.0]` (ch 7, ch 14 양쪽) |
| E1-3 `raw = ch + Σ_{나머지 edge} vnu_in` | **확인됨** | `decoder.py:271` sum_t = cur_ch<br>`decoder.py:281` sum_t += vnu_in<br>`decoder.py:292` `vnu_out_raw = sum_t - vnu_in` | 아래 E1-4 열거로 대체 확인 |
| E1-4 raw = 0 조건의 독립 재유도 | **부분 반박됨** (아래 상세) | 위 경로에서 유도 | 열거 검증 15/15 조건식 일치 |
| E1-5 \|raw\| = 0 → 캐스케이드가 `edge_mag[-1]` = 0 | **확인됨** | `decoder.py:155` `mag = np.full_like(mag_in, edge_mag[-1])`<br>`decoder.py:156-157` 위 레벨부터 덮어씀, th 최솟값이 1이라 raw 0은 어느 조건도 못 만족 | uniform 4-bit에서 `_vnu_quantize` 출력이 raw −20..20 전 구간에서 `sign(raw)·min(\|raw\|,7)`과 일치, raw 0 → 0 |
| E1-6 독립 FER 재현 | **부분 확인됨** (ch=top만) | 아래 ㉯ 대조표 | 4-bit ch 7 → FER 1.0000, 6-bit ch 31 → 1.0000 |
| E1-7 경고 없이 완주 | **확인됨** | 경고 장치가 코드에 없음 | `python -W always -m LDPC_base.run` 종료 코드 0, stderr 0바이트, summary.txt에 `FER=1.000e+00 BER=5.914e-02`만 기록 |
| E1-8 파일 매트릭스 경로는 왜 무사한가 | **확인됨** | `llr_matrix.py:67-72` edge_mag 생략 시 3-bit 기본 `[7,5,3,1]`<br>`llr_matrix.py:170, 202-203` 파일명에 `uniform`이 있을 때만 `uniform_edge_mag` 사용 | `LLR_MATRIX_HD_1.txt`에서 \|VNU_out\| 고유값 `{1,3,5,7}`, 0 없음 |

#### E1-4 상세 — 대수 근거의 독립 재유도

iteration 1의 column 루프 초입에서 모든 C2V가 ±top이므로 (E1-2), degree dv인 column의
한 edge에 대해

```
raw = ch + Σ_{나머지 dv-1개 edge} (±top) = top·(k + Σ s_i),   ch = k·top, s_i ∈ {+1,-1}
```

Σ s_i는 dv−1개 항의 합이라 `[-(dv-1), dv-1]` 범위이며 dv−1과 같은 패리티만 취한다.
따라서 **raw = 0의 필요충분조건은 `|k| <= dv-1` 이면서 `k ≡ dv-1 (mod 2)`** 이다.
Round 2 요약은 이 패리티·범위 조건을 적지 않았고, 그 누락은 결론을 바꾼다.

- ㉮ 열거 검증 (top=7, dv ∈ {2,3,4}, k ∈ 0..4의 15조합): raw 가능값 집합의 0 포함 여부와
  위 조건식이 **15/15 일치**
- ㉯ 이 부호의 dv 분포는 dv 4가 129 블록, dv 2가 17 블록, dv 3이 1 블록이다
  (`example_18x147_z256.qc`). 따라서 k=1은 dv 4와 dv 2 양쪽에서 성립해 지배적이고,
  k=2는 dv 3(1블록)에서만, k=3은 dv 4에서 3개 edge가 전부 −1일 때만, k=4는 전혀
  성립하지 않는다
- ㉰ 계측이 이를 그대로 재현한다 (iteration 1의 dv별 raw==0 비율)

| ch (k) | dv 2 | dv 3 | dv 4 | 조건식 예측 |
|--------|------|------|------|------------|
| 7 (k=1) | 2.906% | 5.200% | 7.197% | dv 2 ○, dv 3 ✕, dv 4 ○ |
| 14 (k=2) | 0.000% | 1.526% | 0.000% | dv 2 ✕, dv 3 ○, dv 4 ✕ (**정확 일치**) |
| 21 (k=3) | 0.000% | 0.000% | 0.415% | dv 2 ✕, dv 3 ✕, dv 4 ○ (**정확 일치**) |

ch=7의 dv 3에서 5.200%가 나오는 것은 2차 오염이다. column 루프가 dv 내림차순으로 돌아
dv 4 column들이 먼저 magnitude 0을 CN에 심고, 그 뒤 dv 3 column이 읽는 C2V가 이미 ±top이
아니게 된다. iteration 1 내부에서 이미 오염이 번진다는 뜻이다.

- ㉱ **이후 iteration에서도 지속**: ch=7에서 raw==0 비율이 iteration 1의 6.922%에서
  iteration 30의 5.150%까지 유지되고, min1==0인 CN lane 비율은 88.934% → 80.082%로
  고착된다. 프레임당 잔여 에러 비트는 2726 → 2205로, 주입 에러 200보다 10배 이상
  증폭된 채 수렴한다

#### E1-4 판정 결과 — 실측이 대수와 정합하는가

정합하지 않는 부분이 있다. **k=1만 파국적 공명이고, k=2는 공명이 아니다.**

| 4-bit (top 7) ch | 5 | 6 | **7** | 8 | 9 | 10 | 13 | **14** | 15 | 20 | **21** | 22 | **28** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FER | 0 | 0 | **1.0000** | 0.0781 | 0.0781 | 0.2031 | 0.3594 | **0.7500** | 1.0000 | 1.0000 | **1.0000** | 1.0000 | **1.0000** |
| 프레임당 잔여 에러비트 | 0 | 0 | **2225.5** | 0.2 | 0.2 | 0.5 | 1.2 | **2.8** | 33.6 | 68.6 | **70.5** | 104.5 | **113.1** |

- ㉮ ch = top(k=1)은 좌우 이웃(ch 6은 FER 0, ch 8은 0.0781)과 완전히 단절된 고립
  스파이크이며, 잔여 에러비트가 2225.5로 세 자릿수 도약한다
- ㉯ ch = 2·top(k=2, ch 14)은 ch 13(0.3594)과 ch 15(1.0000) 사이의 단조 램프 위의 한 점이다.
  스파이크가 아니다
- ㉰ ch = 3·top(k=3, ch 21)의 잔여 에러비트 70.5는 이웃 ch 20(68.6), ch 22(104.5)와 같은
  급이다. 스파이크가 아니다
- ㉱ ch = 4·top(k=4, ch 28)은 조건식상 raw=0이 아예 불가능한데도 FER 1.0이다. 이쪽은
  공명이 아니라 채널항이 커서 VN이 거의 뒤집히지 않는 경직 구간이다
- ㉲ k=1 스파이크는 양자화 bit 수와 무관하게 **완전히 동일**하다. 3-bit ch 3, 4-bit ch 7,
  5-bit ch 15, 6-bit ch 31이 모두 FER 1.0000에 프레임당 잔여 에러비트 2225.5로 일치한다.
  수치 오차가 아니라 구조적 공명임을 뒷받침한다
- ㉳ ch = 1도 파국이다 (4-bit FER 1.0, 잔여 2190.9 / 3-bit FER 1.0, 잔여 2210.6).
  ch = k·top 형태가 아니므로 A-1의 서술 범위 밖이다. 작은 ch는 message magnitude의
  부호합으로 쉽게 상쇄되어 raw=0이 되는 별개 경로다

**H1 판정**: 공명 현상과 그 기전(raw 0 → magnitude 0 → CN 침묵 → FER 붕괴, 경고 없음)은
확인됨. 발동 조건의 서술 "top_level의 정수배"는 반박됨. 정확한 조건은
**`ch = k·top` 이면서 `|k| <= dv-1` 이고 `k ≡ dv-1 (mod 2)`인 dv가 존재할 것**이며,
이 부호에서 파국을 만드는 것은 `k = 1` 즉 `ch = top_level` 하나다.

### H2 (A-5) — magnitude 0이 min1을 점유해 CN이 침묵

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|-----------|------|
| E2-1 `<=` 비교로 mag 0이 항상 min1 점유 | **확인됨** | `decoder.py:179` `is_new_min1 = new_mag <= cur_min1` (cur_min1 >= 0이므로 new_mag 0은 항상 참) | 계측 전 iteration에서 "mag 0을 받은 CN lane 수"와 "min1==0인 CN lane 수"가 **완전히 동일**. 예외 0건 |
| E2-2 min1 교체 시 min2가 RESET으로 상승 | **확인됨** | `decoder.py:181-183` `min2 = where(is_new_min1, RESET, ...)`, `min1 = where(is_new_min1, new_mag, ...)`<br>`decoder.py:130-137` C2V = min1_pos면 min2, 아니면 min1 | min1=1, min2=3, min1_pos=5인 lane에 edge 9로 mag 0 투입 → min1=0, min2=7(RESET), min1_pos=9.<br>C2V: 다른 edge 3 → **0.0**, min1_pos edge 9 → **7.0** |
| E2-3 수렴 구간의 mag 0 비율 | **확인됨(수치는 다름)** | 위와 동일 | 아래 표 |
| E2-4 독립 FER 대조 | **확인됨(방향 일치)** | 아래 ㉰ | 아래 표 |

E2-2에서 드러난 것은 침묵 하나가 아니라 **2중 손상**이다. min1_pos 하나를 제외한 모든
edge가 magnitude 0을 받고, 정작 min1_pos edge는 min2 = RESET = top(최대 확신)을 받는다.
근거 없는 최강 메시지가 만들어진다.

**E2-3 계측 방법**: `MinSumDecoder`를 상속해 `_cnu_update` 진입 시 `new_mag == 0`인 lane을
CN 블록별로 OR 누적하고, `_run_iteration` 종료 시 `min1 == 0`인 원소 수를 세었다. 분모는
`B × M_b × z` 전체 CN lane 수다. 원본 코드는 수정하지 않았다.

| 조건 | iter1 | iter2 | iter3 | iter4 | iter5 | iter6 |
|------|-------|-------|-------|-------|-------|-------|
| 6-bit ch 8, point 300 | 0.031% | 0.327% | 1.935% | **4.579%** | 3.636% | 1.569% |
| 6-bit ch 8, point 200 | 0.036% | 0.219% | 0.541% | 0.339% | 0.028% | 0.000% |
| 4-bit ch 8, point 300 | 0.066% | 0.703% | 3.011% | **4.826%** | 3.217% | 1.305% |
| 6-bit ch 32, point 300 | 0.014% | 0.094% | 0.482% | **1.011%** | 0.840% | 0.350% |

Round 2의 "iter5에 7.97%"는 재현되지 않았다. 최댓값은 iteration 4의 4.6~4.8%다. 자릿수는
같으나 값과 위치가 다르다.

### H3 (처방: "0 레벨 제거 = edge_mag 최소 1")

| 증거 | 판정 | 근거 |
|------|------|------|
| E3-1 C++ 정합 주장 | **확인됨** | 아래 상세 |
| E3-2 처방의 실현 가능성 | **반박됨(그대로는 불가)** | 아래 상세 |
| E3-3 A-1·A-5 동시 해소 | **확인됨** | 아래 ㉰ |
| E3-4 부작용 스윕 | **확인됨(조건부)** | 아래 ㉰ |
| E3-5 적용 금지 | 준수 | 저장소 코드 무수정, 모두 서브클래스와 monkey-patch로 처리 |

#### E3-1 상세 — C++ 두 도메인 분리

| 항목 | 3-bit 기본 | `__4_BIT_LLR__` | 근거 |
|------|-----------|-----------------|------|
| V 도메인 (min1/min2 저장값) | `V_VERY_STRONG 3` ~ `V_VERY_WEAK 0` | `V_MAG7 7` ~ `V_MAG0 0` | `common.h:338-341`, `common.h:319-326` |
| EDGE 도메인 (C2V·VNU_out) | `EDGE_MAG_7 7`, `5`, `3`, `EDGE_MAG_1 1` | `EDGE_MAG_8 8` ~ `EDGE_MAG_1 1` | `common.h:343-346`, `common.h:328-335` |
| V → EDGE (C2V 출력) | 최하위 V값 → `EDGE_MAG_1 = 1` | 최하위 V값 → `EDGE_MAG_1 = 1` | `decoder.cpp:2402-2405`, `decoder.cpp:2393-2400` |
| EDGE → V (CN 입력) | `EDGE_MAG_1` 이하 → `V_VERY_WEAK 0` | `EDGE_MAG_2` 이하 → `V_MAG0 0` | `decoder.cpp:2766-2769`, `decoder.cpp:2757-2764` |
| RESET | `V_VERY_STRONG` | `V_MAG7` | `decoder.cpp:3521, 3523, 3531, 3533`, `decoder.cpp:934-951` |
| VNU_out 양자화 최하위 레벨 | `EDGE_MAG_1 = 1` | `EDGE_MAG_1 = 1` | `decoder.cpp:4096, 4115` / `decoder.cpp:4091, 4110` |

Round 2 주장이 맞다. min1/min2는 압축 V 도메인이라 0이 정상값이고, C2V 출력은 반드시
EDGE 도메인으로 되돌아가며 최솟값은 `EDGE_MAG_1 = 1`이다. `__4_BIT_LLR__` 분기도 동일하다.
C++에서 C2V magnitude 0은 존재하지 않는다.

Python이 두 도메인을 `edge_mag` 하나로 합쳤다는 서술도 코드상 정확하다.
`decoder.py:118`이 `edge_mag`를 양자화 출력 레벨로 쓰고, `decoder.py:170`과 `208`이 같은
배열의 [0]을 min 레지스터 RESET으로 쓰며, `decoder.py:183`이 양자화 결과를 그대로 min1에
저장한다. 파일 3-bit 경로에서는 V ↔ EDGE 대응이 순서동형(3↔7, 2↔5, 1↔3, 0↔1)이라 합쳐도
결과가 같다. 균일 경로에서만 `edge_mag[-1] = 0` 때문에 C++에 대응 상태가 없는 C2V 0이
생긴다.

#### E3-2 상세 — 처방의 실현 가능성

`uniform_edge_mag`를 그냥 `[top_level..1]`로 바꾸면 실행 즉시 막힌다.

```
ValueError: probe_top_to_1: edge_mag 길이 7 != th 개수 + 1 (8)      (llr_matrix.py:74-76)
```

`th = [top..1]`이라 `th_len = top_level`이고 `edge_mag` 길이는 `top_level + 1`이어야 하는데
`[top..1]`은 `top_level`개뿐이다. **처방은 그대로는 적용 불가다.**

두 대안을 실제로 만들어 정수 raw 전 범위에서 대조했다.

| 항목 | 안 ㉮ `edge_mag=[top..2,1,1]`, `th=[top..1]` | 안 ㉯ `th=[top..2]`, `edge_mag=[top..1]` |
|------|---------------------------------------------|------------------------------------------|
| `sign(raw)·max(min(\|raw\|,top),1)` 등가 | **일치** (top 7의 raw −20..20, top 31의 raw −200..200 전 구간) | **일치** (동일 범위) |
| `num_param` | 불변 (6-bit 32) | 1 감소 (6-bit 31) |
| 파일 내용 | 불변 | th 줄이 바뀜 |
| `save()` → `load()` 왕복 | 무손실 (`uniform_edge_mag` 재정의 전제) | 무손실 (`uniform_edge_mag(n) = [n+1..1]` 재정의 전제) |
| 커밋된 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` 호환 | **재생성 없이 그대로 고쳐짐**. \|out\|(raw 0,1,2,31,32) = 1,1,2,31,31 | **조용히 다른 부호가 됨**. \|out\| = 1,2,3,32,32 (magnitude가 top 31을 넘어 32가 나온다) |
| `max_value`/`min_value` | 길이·값 그대로 (`[max(top,ch)]*num_param`, `[0]*num_param`) | 길이가 1 줄지만 생성식이 `num_param` 기반이라 자동 추종 |
| DAO 정수 기록 규칙 (`llr_matrix.py:235`) | 준수 | 준수 |
| `run.py` 생성 파일명 규약 (`run.py:209-211`) | 불변 | 불변 (파일명은 같은데 내용이 달라진다) |
| `RESET = edge_mag[0]` | `top` 유지 | `top` 유지 |

안 ㉯의 마지막 항목이 결정적이다. `load()`가 `edge_mag`를 `num_param - ch_len`에서
재계산하므로(`llr_matrix.py:202`), 안 ㉯를 위해 `uniform_edge_mag(n) = [n+1..1]`로 바꾸면
기존 `num_param = 32` 파일이 `[32..1]`로 읽혀 `min(|raw|,31) + 1`이 된다. 선언한 6-bit
magnitude 범위(0..31)를 넘는 32가 메시지로 흐르고, 경고는 없다.

---

## ㉯ Round 2 수치와 독립 재현 수치의 대조표

독립 재현 조건은 아래 ㉲에 명시했다. Round 2 요약에는 point, frames, max_iter가 적혀
있지 않아 5가지 조합을 모두 돌려 역추적했다.

| 항목 | Round 2 | 독립 재현 | 판정 |
|------|---------|-----------|------|
| 4-bit ch 7 → FER | 1.0000 | **1.0000** (모든 조합: point 200/300 × max_iter 30/120 × 64/256 프레임) | 일치 |
| 4-bit ch 6 → FER | 0.0000 | **0.0000** (64프레임) / 0.0078 (256프레임, 2/256) | 64프레임 기준 일치 |
| 4-bit ch 8 → FER | 0.2188 (=14/64) | 0.0781 (point 200, 64f) / 0.1016 (point 200, 256f) / 0.1250 (point 300, 64f) / 0.1953 (point 300, 256f) | **재현 실패**. 어느 조합도 0.2188이 아님 |
| 4-bit ch 14 → FER | 1.0000 | 0.7500 (point 200, 64f) / 0.7539 (point 200, 256f) / **1.0000** (point 300) | point 300에서만 일치 |
| 6-bit ch 31 → FER | 1.0000 | **1.0000** (모든 조합) | 일치 |
| A-5 mag 0 CN lane 비율 (iter5) | 7.97% | 3.636% (6-bit ch 8, point 300). 최댓값은 iter4의 4.579% | 재현 실패, 자릿수만 일치 |
| A-5 FER 대조 (6-bit ch 8, 256f) | 0.1875 → 0.1211 | point 200/300에서는 양쪽 다 0.0000이라 대조 불가.<br>워터폴 구간에서 재현: point 350 **0.0898 → 0.0469**, 360 **0.3828 → 0.3086**, 370 **0.7266 → 0.5938**, 380 **0.9297 → 0.8828** | 절대값 불일치, **개선 방향과 크기(약 1.2~1.9배)는 일치** |

Round 2의 "6-bit ch 8, 256 frames, FER 0.1875"는 point 200과 300 어느 쪽에서도 나오지
않는다 (둘 다 FER 0). point를 올려 찾은 결과 350 부근이 0.0898, 400에서 1.0000으로,
워터폴이 매우 가파르다.

---

## ㉰ 처방 판정

### **처방 수정 필요 — 안 ㉮ 채택 권고**

원 처방("`uniform_edge_mag`가 최소 magnitude 1을 주도록")은 `llr_matrix.py:74-76`의 길이
제약에 걸려 그대로는 적용 불가다. 안 ㉮로 고쳐야 한다.

```
uniform_edge_mag(top_level) = [top_level, ..., 2, 1, 1]      # 길이 top_level + 1
th (make_internal_uniform_matrix)                              # [top_level..1] 그대로
```

#### 유효성 (E3-3)

| 조건 | FER 현행 | FER 안 ㉮ | FER 안 ㉯ | 잔여 에러비트 현행 → 안 ㉮ |
|------|---------|-----------|-----------|--------------------------|
| **4-bit ch 7 (공명)** | 1.0000 | **0.1016** | 0.1016 | 2201.4 → **0.2** |
| **6-bit ch 31 (공명)** | 1.0000 | **0.1016** | 0.1016 | 2201.4 → **0.2** |
| 6-bit ch 8, point 350 | 0.0898 | **0.0469** | 0.0469 | |
| 6-bit ch 8, point 360 | 0.3828 | **0.3086** | 0.3086 | |
| 6-bit ch 8, point 370 | 0.7266 | **0.5938** | 0.5938 | |
| 6-bit ch 8, point 380 | 0.9297 | **0.8828** | 0.8828 | |

A-1의 공명이 사라지고(FER 1.0 → 0.1016, 잔여 에러비트 2201 → 0.2), A-5의 FER 손해도
워터폴 구간에서 회복된다. 두 발견이 한 수정으로 동시에 해소된다. 안 ㉮와 안 ㉯는 모든
실측에서 FER이 동일하다 (양자화 함수가 등가이므로 예상대로다).

#### 부작용 (E3-4)

(a) 비공명 ch의 FER 변화 (point 200, 256프레임, max_iter 30)

| nb | ch | 현행 | 안 ㉮ | 비고 |
|----|----|------|-------|------|
| 4 | 5 | 0.0078 | 0.0078 | 동일 |
| 4 | 6 | 0.0078 | 0.0078 | 동일 |
| 4 | 8 | 0.1016 | 0.1016 | 동일 |
| 4 | 13 | 0.3398 | 0.3398 | 동일 |
| 4 | 14 | 0.7539 | 0.7539 | 동일 |
| 4 | 15 | 1.0000 | 1.0000 | 동일 |
| 4 | 28 | 1.0000 | 1.0000 | 잔여 113.2 → 113.2 |
| 6 | 8 | 0.0000 | 0.0000 | 동일 |
| 6 | 30 | 0.0078 | 0.0078 | 동일 |
| 6 | 32 | 0.1016 | 0.1016 | 동일 |
| 6 | 62 | 0.7539 | 0.7539 | 동일 |
| 4 | 13 (point 300) | 0.7266 | 0.7305 | 1프레임 차 (186/256 → 187/256) |
| 4 | **1** | 1.0000 | 1.0000 | 잔여 2204.6 → **4488.5** (악화) |
| 4 | **21** | 1.0000 | 1.0000 | 잔여 70.1 → **105.9** (악화) |

악화가 나타나는 두 지점(ch 1, ch 21)은 현행에서도 FER 1.0인 사용 불가 설정이며, 바뀌는
것은 잔여 에러비트뿐이다. 실사용 후보 구간에서는 개선 아니면 동일이다.

(b) `save()` → `load()` 왕복: `uniform_edge_mag`를 monkey-patch로 안 ㉮ 정의로 바꾼 상태에서
`make_internal_uniform_matrix` → `save` → `load`를 돌려, row 값 무손실과 `edge_mag` 보존
모두 True를 확인했다. `num_param`이 그대로라 파일 포맷과 `load()`의 재계산식이 자동으로
맞는다.

(c) 파일 로드 경로: `uniform_edge_mag` 호출 지점은 `llr_matrix.py:202`(파일명에 `uniform`이
있을 때만)과 `llr_matrix.py:225` 둘뿐이다 (저장소 전체 grep 확인). 3-bit DAO
`LLR_MATRIX_HD_1.txt`는 `edge_mag=None`으로 들어가 `llr_matrix.py:72`의 `[7,5,3,1]`을
쓰므로 영향이 없다. 실측 \|VNU_out\| 고유값 `{1,3,5,7}` 불변.

(d) `RESET = edge_mag[0]`: 현행, 안 ㉮, 안 ㉯ 모두 `top_level`(4-bit에서 7.0)로 동일하다.
`decoder.py:170, 208, 240`의 RESET 의미는 바뀌지 않는다.

(e) 커밋된 `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`: 안 ㉮에서는 파일을 그대로
두고도 새 규칙으로 읽혀 고쳐진다. 안 ㉯에서는 같은 파일이 `min(|raw|,31)+1`로 조용히
재해석되어 magnitude 32가 흐른다.

#### 안 ㉯를 채택하지 않는 이유

- ㉮ 기존 uniform 파일을 경고 없이 잘못 읽는다 (위 (e))
- ㉯ `num_param`이 32에서 31로 줄어 같은 파일명, 다른 내용이 공존한다
- ㉰ 등가성과 FER 개선은 안 ㉮와 완전히 같아, 얻는 것 없이 호환성만 잃는다

#### 남는 설계 질문 (사용자 결정 사안, Decision 등급)

안 ㉮는 `max(min(|raw|, top), 1)`이다. C++ 4-bit는 `V_MAG0..V_MAG7`(V 도메인 8단계)과
`EDGE_MAG_1..EDGE_MAG_8`(EDGE 도메인 8단계)을 쓰므로, C++ 구조를 그대로 옮기면
`edge_mag = [top+1, top, ..., 1]`(`th = [top..1]` 그대로, 길이 제약도 만족)이 되어
`min(|raw|, top) + 1`이 된다. 안 ㉮와 이 안은 magnitude가 1만큼 어긋난다. 어느 쪽을
"균일 n-bit 양자화"의 정의로 삼을지는 설계 선택이다. 이 워커는 처방의 기술적 타당성만
판정했고 코드는 고치지 않았다.

---

## ㉱ Round 2가 놓쳤거나 틀리게 적은 것

- ㉮ **A-1의 발동 조건에서 패리티·범위 조건 누락 (실질 오류)**. "`top_level`의 정수배"는
  틀렸다. 정확히는 `ch = k·top`이면서 `|k| <= dv-1`이고 `k ≡ dv-1 (mod 2)`인 dv가
  있어야 한다. 이 부호에서는 k=1만 파국을 만든다
- ㉯ **A-1 근거로 든 "4-bit ch=14(k=2)도 FER 1.0"이 오귀인**. ch 14의 FER 1.0은 point 300에서만
  나오고, 그때 ch 13은 0.625, ch 15는 1.0으로 단조 램프 위에 있다. iteration 1의 dv별
  raw==0 비율이 dv 2와 dv 4에서 정확히 0.000%인 것이 결정적이다. ch 14의 FER 악화는
  공명이 아니라 채널항 경직이다
- ㉰ **`uniform_edge_mag`를 `[top..1]`로 바꾸는 처방이 실행 즉시 ValueError로 막힌다는 점
  미기재**. 처방을 그대로 적으면 적용 단계에서 반드시 실패한다
- ㉱ **A-5의 손상이 "침묵" 하나가 아니라 2중이라는 점 미기재**. min1_pos edge는 min2 =
  RESET = top을 받아 근거 없는 최강 메시지가 만들어진다 (`decoder.py:181-183` + `135-137`)
- ㉲ **ch = 1 계열의 파국 미포착**. 4-bit ch 1, 3-bit ch 1도 FER 1.0에 잔여 에러비트
  2190~2211로 ch = top과 같은 급이다. `ch = k·top` 형태가 아니므로 A-1의 서술로는
  잡히지 않는다. 처방 적용 후에도 남고, 잔여 에러비트는 오히려 2204.6 → 4488.5로 악화한다
- ㉳ **실행 조건 미기재로 재현 불가**. point, frames, max_iter가 요약에 없어 5조합을
  역추적해야 했고, ch 8의 0.2188과 A-5의 7.97%는 끝내 재현되지 않았다
- ㉴ **k=1 공명이 num_bits와 무관하게 완전히 동일한 수치를 낸다는 강한 증거 미제시**.
  3-bit ch 3, 4-bit ch 7, 5-bit ch 15, 6-bit ch 31이 전부 FER 1.0000, 잔여 2225.5로 일치한다.
  구조적 공명임을 못박는 증거다

---

## ㉲ 실행 환경과 오염 확인

### 실행 조건 (전부 재현 가능)

- ㉮ Python 3.11.7, numpy 1.26.4, Windows 10
- ㉯ H-matrix: `2_LDPC_light/Input/H_matrix/example_18x147_z256.qc`
  (base 18×147, z=256, N=37632, K=33024, rate 0.8776, col degree {2:17, 3:1, 4:129})
- ㉰ 채널: `fixed_error` (HD), point는 프레임당 주입 에러 비트 수
- ㉱ seed: `config.seed = 0`. 난수 스트림은 `run.py:398`과 동일하게
  `np.random.default_rng([0, 0, int(1e6*point)])`로 만들고, 채널 함수도 `run.py:353-357`
  그대로 `generate_message` → `encode`(all-zero) → 채널 순서를 재현했다
- ㉲ 기본 스윕: `max_frames=256`, `frames_per_batch=64`, `max_frame_errors=10^9`(조기 종료
  없음), `max_iter=30`. 64프레임 대조표는 `max_frames=64`
- ㉳ 디코더: `LDPC_base.decoder.MinSumDecoder`. `run.py` 전 경로 실행에서는
  `Ideas.vanilla.decoder.VanillaDecoder`가 선택되며 재정의가 없어 동작이 같다
  (`Ideas/vanilla/decoder.py`). 두 경로의 4-bit ch 7 결과가 BER 5.914e-02로 동일함을 확인
- ㉴ 균일 매트릭스는 전부 `make_internal_uniform_matrix` → `save` → `load`의 실제 경로로
  만들었고, 생성 파일은 scratchpad `gen_llr/`에만 썼다
- ㉵ 처방 적용판은 저장소 코드를 고치지 않고 `LLRMatrix.edge_mag` 교체와
  `llr_matrix.uniform_edge_mag` monkey-patch로만 만들었다

### 산출물 위치 (전부 scratchpad)

`C:\Users\yongs\AppData\Local\Temp\claude\d--OneDrive-My-Projects-LDPC-dev\96aaaa04-61b8-4b90-ac92-52ca7348de60\scratchpad\`
아래 `harness.py`, `e_static.py`, `e_sweep.py`, `e_fine.py`, `e_instr.py`, `e_a5.py`,
`e_algebra.py`, `e_fix.py`, `cfg/config_ch7.json`, `cfg/config_ch8.json`, `gen_llr/`,
`Sim_Output/`, 로그 `fine.log`, `fix200.log`, `waterfall.log`, `run_ch7.out`, `run_ch7.err`.

### git status --short (작업 종료 시점)

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

사전 상태 3줄과 동일하다. 이 보고서는 이미 untracked인 `2_LDPC_light/_pm/tasks/` 안에
있으므로 줄이 늘지 않는다. **오염 없음.**
