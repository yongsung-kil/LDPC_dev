# Worker A-2 — 관점 B: `_vnu_quantize` 캐스케이드 일반화의 정확성 + 정수성 전제

작업일: 2026-08-08 / 담당: 팀 A 워커 2
검증 환경: Python 3.11.7, numpy 1.26.4, `2_LDPC_light/`에서 실행
실측 스크립트 위치: scratchpad (`check_a2.py`, `check_a2b.py`, `check_a2c.py`, `check_a2d.py`, `check_a2e.py`) — 저장소 파일은 읽기만 함

---

## 핵심 질문 2개에 대한 답

**질문 1: th 3개 고정에서 th n개로 푼 `_vnu_quantize`가 3-bit 파일 경로의 기존 동작을 그대로 재현하는가**

재현한다. C++ 원본 `decoder.cpp:4112-4115`의 elif 체인과 `decoder.py:155-157`의 역순 루프가 수학적으로 등가이며, 실측으로도 불일치 0건이다 (아래 ㉮).

**질문 2: "flip 도메인 값이 전부 정수라 캐스케이드가 |값|의 상한 클리핑과 같아진다"는 전제가 float32 누적 경로 전체에서 성립하는가**

현재 코드 경로에서는 성립한다. 파일 로더가 정수만 파싱하고 (`llr_matrix.py:173`의 `int(v)`), `edge_mag`와 `RESET`이 전부 정수라 `sum_t`와 `vnu_out_raw`가 정수를 유지한다. 실제 디코딩 실행 중 `_vnu_quantize` 호출 11,060회(3-bit)와 4,424회(균일 6-bit) 전부에서 `raw == round(raw)`가 참이었고, float32 정수 정확 한계(2^24)까지 여유가 4자리수 이상이다. 다만 전제를 깨는 경로가 두 갈래 열려 있다 (아래 ㉲ / 발견 M-3).

---

## 확인 항목별 판정

### ㉮ 역순 루프 vs elif 체인 등가성 — 문제 없음 (실측)

C++ 원본 실체 (`0_LDPC_original/decoder.cpp:4112-4115`, `__4_BIT_LLR__` 미정의 빌드):

```c
if      (temp_m >= th1)      temp_m = EDGE_MAG_7;
else if (temp_m >= th2)      temp_m = EDGE_MAG_5;
else if (temp_m >= th3)      temp_m = EDGE_MAG_3;
else                         temp_m = EDGE_MAG_1;
```

`common.h:343-346`에서 `EDGE_MAG_7/5/3/1 = 7/5/3/1` 확인. Python의 `[7,5,3,1]` 기본값과 일치.

Python (`decoder.py:155-157`)은 `k = th_len-1 → 0` 역순으로 덮어쓰므로 **마지막에 적용되는 k=0(th1)이 최종 승자**가 되어 "위쪽 th 우선" elif 의미와 정확히 같다. `k`가 감소하며 덮어쓰는 구조라 th 단조성과 무관하게 등가다.

실측 결과:

| 대상 | 비교 건수 | 불일치 |
|------|----------|--------|
| `LLR_MATRIX_HD_0.txt` 전 row × 전 dv (th 조합 12개) × raw -64..64 | 1,548 | **0** |
| `LLR_MATRIX_HD_1.txt` 전 row × 전 dv (th 조합 8개) × raw -64..64 | 1,032 | **0** |
| 무작위 비단조 th (th_len=3, edge_mag [7,5,3,1]) | 51,000 | **0** |
| 무작위 비단조 th (th_len=1, edge_mag [1,0]) | 51,000 | **0** |
| 무작위 비단조 th (th_len=3, edge_mag [3,2,1,0]) | 51,000 | **0** |
| 무작위 비단조 th (th_len=7, edge_mag [7..0]) | 51,000 | **0** |

무작위 th는 `-2 ~ 34` 범위 정수를 순서 제약 없이 뽑아 비단조 조합을 포함시켰다.

실파일 비단조 row 존재 여부: `HD_0.txt`, `HD_1.txt`, `HD_uniform_6bit_ch8_iter30.txt` **모두 비단조 row 없음**. `HD_0.txt`의 restart row(전부 -1)는 th=[-1,-1,-1]로 등호가 성립해 경고 대상이 아니며, 캐스케이드는 `0 >= -1`이 참이라 전 메시지가 최대 레벨(7)이 된다 — `decoder.py:28-29` docstring이 주장하는 동작과 일치.

### ㉯ 인덱스 대응 / off-by-one — 문제 없음 (실측)

`len(edge_mag) == th_len + 1` 불변식(`llr_matrix.py:74-76`)이 있으므로 루프 범위 `k ∈ [0, len(edge_mag)-2] = [0, th_len-1]`이 th 인덱스 유효 범위와 정확히 일치한다. num_bits별 실측:

| num_bits | top_level | th_len | len(edge_mag) | k 범위 | th 유효범위 | 일치 | edge_mag[-1] |
|----------|-----------|--------|---------------|--------|-------------|------|--------------|
| 2 | 1 | 1 | 2 | [0..0] | [0..0] | 예 | 0.0 |
| 3 | 3 | 3 | 4 | [0..2] | [0..2] | 예 | 0.0 |
| 6 | 31 | 31 | 32 | [0..30] | [0..30] | 예 | 0.0 |
| 8 | 127 | 127 | 128 | [0..126] | [0..126] | 예 | 0.0 |
| 파일 3-bit | — | 3 | 4 | [0..2] | [0..2] | 예 | 1.0 |

`edge_mag[-1]`이 `np.full_like` 초기값이므로 "전부 아님" 가지에 정확히 대응한다.

### ㉰ shape / 브로드캐스트 축 정합 — 로직은 문제 없음, 주석 1건 불일치 (실측)

- `row_th.shape`: `HD_0` = (3, 4, 3), `uniform_6bit` = (1, 1, 31) — `(R, num_dv, th_len)` 확인
- `state.cur_th = row_th[table_row_idx]` → (num_active_frames, num_dv, th_len). 5프레임 균일 6-bit에서 (5, 1, 31) 실측
- `cur_th[:, dv_idx, :]` → (num_active_frames, th_len). `th[:, k, None]` → (num_active_frames, 1)이 `mag_in`의 (num_active_frames, z)에 정상 브로드캐스트
- 배치 압축 후에도 축이 맞는지: `_process_column`에 `cur_th.shape[0] == num_active_frames == read_bit.shape[0]`와 `cur_th.shape[2] == th_len` assert를 넣고 실제 디코딩 2회(3-bit 11,060 호출 / 균일 6-bit 4,424 호출) 실행 — **위반 0건**. `_run_iteration:241`이 매 iteration `num_active_frames`를 `read_bit.shape[0]`에서 다시 읽고, `row_index()`가 압축된 `prev_csw` 길이로 배열을 만들기 때문

**불일치 1건**: `decoder.py:256`의 주석 `# (num_active_frames, num_dv, 3)`. 실제는 `(num_active_frames, num_dv, th_len)`이고 균일 6-bit에서는 31이다. 일반화 후 남은 3 고정 표기 (발견 L-1).

### ㉱ dtype 승격 / 정밀도 — 문제 없음 (실측)

numpy 1.26.4 실측:

| 지점 | dtype |
|------|-------|
| `mag_in = np.abs(raw)` | float32 |
| `np.full_like(mag_in, edge_mag[-1])` | float32 |
| `np.where(mag_in >= th[:,k,None], edge_mag[k], mag)` (k=2,1,0 전부) | float32 |
| `sgn = np.where(raw > 0, np.float32(1.0), np.float32(-1.0))` | float32 |
| `sgn * mag` (반환값) | float32 |

`edge_mag[k]`는 `np.float32` 스칼라라 승격이 없다. 실제 디코딩 중 관측한 (raw, th, vnu_in) dtype 조합은 `('float32','float32','float32')` 하나, 출력은 `float32` 하나뿐이었다 (호출 15,484회 전수).

`th`의 출처도 float32다: `row_values = np.array([...], np.float32)` (`llr_matrix.py:86`) → `row_th`는 그 뷰. `make_internal_uniform_matrix`가 float64 배열을 넘겨도 `__init__`에서 float32로 캐스팅된다.

참고로 `edge_mag`를 float64로 강제해도 numpy 1.26의 스칼라 값 기반 캐스팅 때문에 결과는 float32를 유지했다. 다만 `self._edge_mag = np.asarray(llr_matrix.edge_mag, np.float32)` (`decoder.py:118`)가 dtype을 고정하므로 이 경로는 실현되지 않는다.

### ㉲ 정수성 전제 추적 — 현 경로에서 성립, 전제를 깨는 갈래 2개 존재

**정수성이 유지되는 근거 (경로 전수 추적)**

- ㉮ `state.cur_ch` ← `row_ch` ← `row_values`(float32) ← 파일 파싱 `int(v)` (`llr_matrix.py:173`). 파일에 소수가 있으면 `int()`가 예외를 내므로 **로더가 정수성을 구조적으로 강제**한다. `make_internal_uniform_matrix`의 `channel_llr`도 `run.py:197-198`의 `_check_int`로 정수 강제
- ㉯ `vnu_in` ← `np.roll(_c2v_reconstruct(...))`. `_c2v_reconstruct`는 `min1`/`min2`에서만 값을 꺼내고(`np.where`), `min1`/`min2`는 `new_mag = abs(sgn*mag)` (= `edge_mag` 원소) 또는 `RESET = edge_mag[0]`에서만 채워진다. `edge_mag`는 파일 기본 `[7,5,3,1]` 또는 `uniform_edge_mag(top)` = `[top..0]`으로 **전부 정수**
- ㉰ `np.roll`은 값을 재배치만 하므로 보존한다
- ㉱ 따라서 `sum_t = ch + Σ vnu_in`, `vnu_out_raw = sum_t - vnu_in` 모두 정수

**실측**: 실제 디코딩 실행 중 `_vnu_quantize`에 들어온 `raw`가 비정수인 호출 = **0건** (3-bit 11,060회, 균일 6-bit 4,424회). 관측 `max|raw|` = 35.0(3-bit), 101.0(균일 6-bit).

**float32 정수 정확 한계 (2^24 = 16,777,216) 대비 여유** — `dv_max = 17`, `ch = 8` 기준:

| num_bits | top_level | sum_t 최대 ≈ ch + dv·top | 정수 정확 |
|----------|-----------|--------------------------|-----------|
| 6 | 31 | 535 | 예 |
| 10 | 511 | 8,695 | 예 |
| 16 | 32,767 | 557,047 | 예 |
| 20 | 524,287 | 8,912,887 | 예 |
| **21** | 1,048,575 | **17,825,783** | **아니오 (2^24 초과)** |

num_bits 21 이상에서 정수성이 깨지지만, 그 전에 성능이 먼저 무너진다 (발견 M-1). 실용 구간에서는 문제 없음.

**"캐스케이드 == 상한 클리핑" 실측 검증** — 균일 매트릭스(th=[top..1], edge_mag=[top..0])에서 `_vnu_quantize` 출력과 `sign(raw)*min(|raw|, top)` 비교:

| num_bits | top | 정수 raw 전 범위 | 동일 |
|----------|-----|------------------|------|
| 2 | 1 | -8..8 | **예** |
| 3 | 3 | -14..14 | **예** |
| 4 | 7 | -26..26 | **예** |
| 6 | 31 | -98..98 | **예** |

64×256 무작위 정수 raw(-200..200)에서도 `np.array_equal` 참. `raw == 0`인 48건 포함.

**비정수 raw에서의 이탈** (num_bits=6, top=31):

| raw | 캐스케이드 | min(|raw|, top) | floor(|raw|) |
|-----|-----------|-----------------|--------------|
| 0.5 | 0.0 | 0.5 | 0.0 |
| 3.5 | 3.0 | 3.5 | 3.0 |
| 30.5 | 30.0 | 30.5 | 30.0 |
| 2.25 | 2.0 | 2.25 | 2.0 |

즉 비정수 입력에서 캐스케이드는 **클리핑이 아니라 "0 방향 내림(floor) 후 클리핑"**이 된다. `llr_matrix.py:218-219`의 주장은 정수 전제에 전적으로 의존하며, 정수성이 깨지면 주장 자체가 무효가 된다. 이 전제를 깨는 갈래는 발견 M-3 참조.

### ㉳ 불변식 유지 — 유지되나 결합 2건 (실측)

- `llr_matrix.py:74-76`이 `len(edge_mag) == th_len + 1`을 생성 시점에 강제. `LLRMatrix`를 만드는 모든 경로(`load`, `make_internal_uniform_matrix`, 직접 생성)가 이 검사를 통과해야 하므로 서브클래스가 `_vnu_quantize`만 재정의해도 불변식은 유지된다
- `Ideas/vanilla/decoder.py`는 아무것도 재정의하지 않는 빈 서브클래스 (`class VanillaDecoder(MinSumDecoder)`, 본문 docstring뿐). `Ideas/registry.py`에는 vanilla 1개만 등록
- **`self._edge_mag`는 `llr_matrix.edge_mag`와 같은 객체다** (실측: `dec._edge_mag is m.edge_mag` → `True`). `np.asarray`가 dtype이 이미 float32면 복사하지 않기 때문. `m.edge_mag[0] = 99`로 바꾸면 `dec._edge_mag[0]`도 99가 되고 `RESET`까지 함께 바뀐다 (발견 L-2)
- **`_vnu_quantize` 재정의는 `RESET` 전제와 암묵적으로 결합돼 있다**: `RESET = self._edge_mag[0]`이 `_cnu_update`(`decoder.py:170`), `_init_state`(`208`), `_run_iteration`(`240`) 세 곳에서 "가능한 최대 magnitude"로 쓰인다. `decoder.py:51`의 교체 지점 표는 `_vnu_quantize`가 "damping"을 커버한다고 적고 있는데, damping 결과가 `edge_mag[0]`을 넘거나 `edge_mag`에 없는 값이면 min1/min2 초기값 의미가 깨진다 (발견 M-3)

### ㉴ `_validate` th 내림차순 경고 — 실효성 낮음 (실측)

- 균일 매트릭스는 th=[top..1]이 항상 엄격 내림차순이라 **항상 통과**한다 (실측: 균일 6-bit 파일 로드 시 경고 0건)
- 실파일 `HD_0.txt`, `HD_1.txt`도 경고 0건 (비단조 row 없음)
- `warnings.warn`의 기본 필터는 (메시지, 카테고리, 모듈, 줄번호)가 같으면 한 번만 출력한다. 인위 비단조 매트릭스를 3회 생성해 실측 → **stderr 출력 1회**
- `2_LDPC_light/` 전체에 `warnings.simplefilter` / `filterwarnings` 설정이 없다 (grep 결과 `llr_matrix.py:39, 153` 두 줄이 전부). 경고는 stderr로만 나가고 `run.py`의 요약·진행 출력은 stdout이라, stdout만 파일로 리다이렉트하는 배치 실행에서는 경고가 유실된다
- `use_input_llr_matrix=false` 경로는 `make_internal_uniform_matrix`(검증 1회) → `save()` → `load()`(검증 2회)로 `_validate`가 두 번 돌지만, 균일 매트릭스는 경고 대상이 아니므로 실질 영향 없음
- 경고 내용이 `summary()`나 `summary.txt`에 남지 않아 사후 추적 경로가 없다 (발견 L-3)

### ㉵ 3 고정 잔재 전수 (코드 파일만) — 4곳

`2_LDPC_light/` 하위 `.py` 전수 grep 결과:

| 위치 | 내용 | 판정 |
|------|------|------|
| `LDPC_base/decoder.py:256` | 주석 `# (num_active_frames, num_dv, 3)` | **잘못됨** — 실제 `th_len` (발견 L-1) |
| `LDPC_base/decoder.py:150` | docstring "파일 3-bit {7,5,3,1}, 내부 균일 n-bit [최대..0]" | 정확 (설명용 예시) |
| `LDPC_base/llr_matrix.py:67-72` | `th_len != 3` → `NotImplementedError` | **의도 판정 필요** (발견 M-2) |
| `LDPC_base/llr_matrix.py:4` | 모듈 docstring "파일 로드 — DAO 산출물, 3-bit(th 3개, EDGE {7,5,3,1}) 구성" | **낡음** — `load()`가 uniform 파일도 읽는다 (발견 L-4) |
| `LDPC_base/llr_matrix.py:5-7` | 모듈 docstring "내부 합성 — **파일 없이** 균일 n-bit 양자화로 디코딩할 때" | **낡음** — 현 설계는 파일로 저장 후 로드 (발견 L-4) |
| `llr_tables.py` (2_LDPC_light 루트) | 3-bit 전용 프로파일 로더 (`_KEYS`에 `TH_HD:12`, `EDGE_MAG:4`, `reshape(4,3)`) | **죽은 모듈** — 어디서도 import 안 됨, 참조하는 `2_LDPC_light/llr/` 폴더도 없음 (발견 L-5) |

`llr_matrix.py:68-72`의 `th_len != 3` 판정 (발견 M-2로 상세):
파일 경로에 이 제약이 남는 것은 **부분적으로만 의도에 맞다**. `_NAME_RE`가 잡는 모드는 HD/2SD/3SD 3종이고 `is_uniform` 분기가 uniform 파일을 처리하므로, "사람이 만든 DAO 파일 = 항상 3-bit"라는 전제 위에서는 맞다. 그러나 C++ 원본은 `__4_BIT_LLR__` 빌드에서 th1~th7 + `EDGE_MAG_8..1` = `[8,7,6,5,4,3,2,1]`을 지원한다 (`decoder.cpp:4102-4110`, `common.h:328-335`). 실제 DAO 4-bit 매트릭스 파일(HD면 `num_param = 8`)은 지금 로드 자체가 막힌다. 실측: `th 7개 — 파일 매트릭스는 3-bit(th 3개) 전용` `NotImplementedError`.

---

## 발견 목록

| 심각도 | 문제 | 위치 (파일:라인) | 근거 |
|--------|------|------------------|------|
| MEDIUM | **`raw==0`의 부호 계산이 균일 n-bit 모드에서 통째로 버려진다.** `_vnu_quantize`가 `raw==0`일 때 `vnu_in`의 부호를 살려 `sgn`을 만들지만, 균일 모드는 `edge_mag[-1] == 0`이라 결과가 `±0.0`이 되고, `_process_column`의 `new_sgn = (vnu_out < 0)`가 `-0.0 < 0 == False`로 읽어 부호를 "+"로 기록한다. 이 부호는 `check_sum`과 `edge_sgn`에 들어가 CSW 값을 바꾼다 | `decoder.py:159-162` (부호 계산) ↔ `decoder.py:295` (부호 소실) | **실측**: 균일 6-bit 8프레임 실행에서 `raw==0` 4,074건 중 **1,624건이 `-0.0` 출력**. 본체와 `np.signbit` 판정판을 나란히 돌려 iteration별 상태 대조 → `edge_sgn` 차이 iter1 6건 → iter5 1,234건, `check_sum` 차이 iter5 1,134건, **`prev_csw`(CSW)는 iter2부터 8프레임 전부 다름**. 반면 `min1` 차이 0건, `err_bits` 차이 0건이고 최종 success/iteration은 동일 (32프레임 × 에러 250/300/350/400 4포인트 전부 동일). 즉 **현재는 복호 결과가 아니라 CSW 로그(`csw_per_iter` CSV, `fail_detail`의 `final_csw`)만 오염**된다. 균일 매트릭스에 CSW 타입 그룹을 쓰는 순간(현재 `make_internal_uniform_matrix`는 ITER 그룹만 만들지만 `LLRMatrix`는 CSW 그룹을 지원) row 선택이 갈려 복호 결과 자체가 바뀐다. 파일 3-bit 경로는 `edge_mag` 최소가 1이라 `-0.0`이 발생하지 않아 무관 (실측 동일) |
| MEDIUM | **`_vnu_quantize` 비용이 th 개수에 선형이라 num_bits 상향 시 실행이 사실상 멎는다.** 균일 모드에서 캐스케이드는 `sign(raw)*min(|raw|,top)` 한 줄과 수학적으로 동일한데, 루프는 `th_len`번 `np.where`를 돈다. `config.json`의 `num_bits`에 상한 검사가 없다 (`_check_int(..., 2)`는 하한만) | `decoder.py:156-157` (루프), `run.py:195-196` (상한 없음), `llr_matrix.py:224-225` (th_len = top_level) | **실측** (64×256 float32 배열 기준 1회 호출): th_len=3 → 0.09 ms, 31 → 0.50 ms, 127 → 2.00 ms, 511 → 8.00 ms, 2047 → 30.00 ms. 등가 클리핑 1줄은 0.02 ms (th_len=31 대비 **25배**, th_len=127 대비 **109배**). 등가성은 실측 확인 (`np.array_equal` 참, 64×256 raw -200..200). num_bits=12(th_len=2047)면 호출당 30 ms이고 `_vnu_quantize`는 (프레임배치 × column × edge × iteration)마다 호출되므로 8프레임 8 iteration 규모에서도 수 분대로 늘어난다. 파일 크기도 함께 폭증한다 (row당 값 개수 = 1 + top_level) |
| MEDIUM | **정수성 전제가 교체 지점 재정의로 조용히 깨진다.** `llr_matrix.py:218-219`가 "flip 도메인 값이 전부 정수라 캐스케이드가 상한 클리핑과 같아진다"고 선언하지만, 이 전제는 `_c2v_reconstruct`와 `_vnu_quantize`가 정수만 다룰 때만 성립한다. `decoder.py:49`의 교체 지점 표는 `_c2v_reconstruct`가 "min-sum 변형(offset/normalized/adjusted)"을 커버한다고 적고 있는데, offset(−β)이나 normalized(×α)는 정확히 이 전제를 깬다. 깨진 뒤에도 예외 없이 진행하며 클리핑이 아닌 **floor + 클리핑**이 된다. 같은 이유로 `_vnu_quantize`를 damping으로 재정의하면 `RESET = _edge_mag[0]`이 "가능한 최대 magnitude"라는 전제(`decoder.py:170, 208, 240` 세 곳)도 함께 깨진다 | `llr_matrix.py:218-219` (전제 선언), `decoder.py:49, 51` (교체 지점 표), `decoder.py:170/208/240` (RESET 전제) | **실측**: num_bits=6(top=31)에서 raw 3.5 → 3.0(클리핑이면 3.5), 2.25 → 2.0, 30.5 → 30.0, 0.5 → 0.0. 정수 raw 전 범위에서는 클리핑과 완전 일치. 현 코드 경로는 정수를 유지하며(파일 로더가 `int(v)`로 강제, 실행 중 비정수 raw 0건 / 15,484 호출) 전제가 성립한다 |
| MEDIUM | **DAO 4-bit LLR matrix 파일을 로드할 수 없고, 우회하면 조용히 틀린 레벨이 된다.** `th_len != 3`이면 `NotImplementedError`. C++ 원본은 `__4_BIT_LLR__` 빌드에서 th1~th7 + `EDGE_MAG_8..1`을 지원하므로 DAO 4-bit 산출물(HD면 `num_param=8`)은 정당한 입력이다. 유일한 우회는 파일명에 `uniform`을 넣는 것인데, 그러면 `edge_mag`가 `uniform_edge_mag(7) = [7,6,5,4,3,2,1,0]`으로 잡혀 **정답 `[8,7,6,5,4,3,2,1]`과 다른 값으로 조용히 복호**한다. `2_LDPC_light`의 목표가 "외부 H-matrix와 파라미터를 넣어도 동작"인 점과 충돌 | `llr_matrix.py:67-72` (거부), `llr_matrix.py:170, 202-203` (파일명 기반 uniform 판정) | **실측**: `num_param=8` HD 매트릭스 생성 시도 → `th 7개 — 파일 매트릭스는 3-bit(th 3개) 전용`. C++ 근거는 `decoder.cpp:4102-4110`과 `common.h:328-335` (직접 확인, 파일 손상 없음) |
| LOW | `cur_th` shape 주석에 일반화 전 상수 3이 남았다. 실제는 `th_len`이고 균일 6-bit에서 31이다 | `decoder.py:256` | **실측**: 균일 6-bit에서 `row_th[idx].shape == (5, 1, 31)` |
| LOW | `self._edge_mag`가 `llr_matrix.edge_mag`와 같은 배열 객체다 (`np.asarray`는 dtype이 일치하면 복사하지 않음). 한쪽을 바꾸면 다른 쪽과 `RESET`까지 함께 바뀐다 | `decoder.py:118` | **실측**: `dec._edge_mag is m.edge_mag` → `True`. `m.edge_mag[0] = 99` 후 `dec._edge_mag[0] == 99.0` |
| LOW | th 비단조 경고가 stderr로 한 번만 나가고 `summary()`/`summary.txt`에 남지 않아, stdout만 저장하는 배치 실행에서 유실된다. `2_LDPC_light/`에 `warnings` 필터 설정도 없다 | `llr_matrix.py:152-155`, `run.py` 전역 (필터 없음) | **실측**: 인위 비단조 매트릭스 3회 생성 → stderr 출력 1회. grep 결과 `simplefilter`/`filterwarnings` 사용처 0곳. 현 실파일 3개는 모두 비단조 없음이라 당장의 영향은 없음 |
| LOW | 모듈 docstring 2건이 현재 설계와 어긋난다. ㉮ `load()`가 uniform 파일도 읽는데 "파일 로드 — DAO 산출물, 3-bit 구성"으로만 적혀 있다 ㉯ "내부 합성 — **파일 없이** 균일 n-bit 양자화로 디코딩할 때"라고 적혀 있으나 현 설계는 `save()` 후 `load()`로 소비한다 (같은 파일 `make_internal_uniform_matrix` docstring 212-213줄이 정확한 설명) | `llr_matrix.py:4`, `llr_matrix.py:5-7` | 정적 읽기. `run.py:293-304` setup이 `save()` → `load()` 순서임을 확인 |
| LOW | `llr_tables.py`가 죽은 모듈이다. 어디서도 import되지 않고, docstring이 참조하는 `2_LDPC_light/llr/*.txt` 폴더도 없다. 내용은 3-bit 전용 고정(`TH_HD:12`, `EDGE_MAG:4`, `th.reshape(4,3)`)이라 일반화된 현 설계와 어긋나며, 새로 읽는 사람에게 잘못된 진입점이 된다 | `llr_tables.py:1-73` (특히 20, 27, 39) | **실측**: `grep -rn "llr_tables\|LLRProfile\|load_profile" --include=*.py .` → 정의부 4줄만, 사용처 0곳. `ls llr` → 폴더 없음 |

---

## 요약

캐스케이드 일반화 자체는 정확하다. 역순 루프가 C++ elif 체인과 등가임을 실파일 전 th 조합과 20만 건 이상의 무작위 비단조 th로 확인했고, 인덱스 대응·shape 정합·dtype 유지는 num_bits 2/3/6/8과 실제 디코딩 실행에서 위반 0건이었다. 정수성 전제도 현 코드 경로에서 구조적으로 보장된다 (파일 로더의 `int(v)` 강제 + `edge_mag` 정수 + `np.roll` 값 보존, float32 한계까지 4자리수 여유).

남은 위험은 **0 레벨 도입의 파급 2건**(zero-magnitude 메시지의 부호 소실 → CSW 로그 오염, th 개수에 선형인 비용 → num_bits 상향 시 실행 마비)과 **전제의 취약성 2건**(교체 지점 재정의가 정수성·RESET 전제를 조용히 깸, DAO 4-bit 파일 미지원)이다.
