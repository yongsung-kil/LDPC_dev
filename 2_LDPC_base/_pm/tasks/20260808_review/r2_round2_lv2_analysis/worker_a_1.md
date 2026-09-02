# Round 2 · 팀 A 워커 1 — 관점 A (균일 양자화 수치 규약 + 저장/로드 왕복)

작성: 2026-08-08 14:25:12

대상: `LDPC_base/llr_matrix.py` 전체, `Input/LLR/*.txt` 3개, `LDPC_base/run.py`의 `setup()`과
생성 파일명 조립부.

실측 환경: Python 3.11.7 / numpy 1.26.4, `2_LDPC_light/`에서 실행. 모든 산출 파일은
scratchpad에만 기록했고 저장소 추적 파일은 수정하지 않았다.

---

## 확인 항목별 판정

### ㉮ 왕복 필드 대조 — 문제 없음 (실측)

합성 객체와 `save()` → `load()` 복원 객체를 12개 조합(mode HD/2SD/3SD × num_bits 2/3/4/6)에서
필드별로 비교했다. 비교 대상: `mode`, `ch_len`, `num_param`, `th_len`, `num_dv`, `max_iter`,
`edge_mag`, `dv_from`, `dv_to`, `row_values`, `row_ch`, `row_th`, `row_csw`, `row_iter`,
`max_value`, `min_value`, `group_rows`, `group_type`, `restart_iters`.

12개 조합 전부 `name`을 제외한 모든 필드가 완전 일치했다. `name`은 합성 시
`internal_uniform_{n}bit`, 로드 시 basename이라 다르며 이는 설계 의도다 (`summary()` 출력에만
쓰인다).

커밋된 파일 3개도 `load()` → `save()` → `load()` 왕복에서 `row_values` / `row_iter` /
`row_csw` / `restart_iters` / `edge_mag` / `max_value` / `min_value`가 모두 일치했다.

### ㉯ edge_mag 복원식 이원화 — 정상 경로에서 성립, 파일명 의존이 위험 지점

합성은 `uniform_edge_mag(top_level)`, 로드는 `uniform_edge_mag(num_param - MODE_CH_LEN[mode])`를
쓴다. `make_internal_uniform_matrix`가 `num_param = ch_len + top_level`
(`llr_matrix.py:227`)로 정의하므로 두 식은 항등이며, 실측에서 HD(ch 1) / 2SD(ch 2) /
3SD(ch 4) 전부 같은 값을 냈다.

| mode | num_bits | top_level | num_param | 합성 edge_mag | 로드 edge_mag |
|------|----------|-----------|-----------|---------------|---------------|
| HD | 6 | 31 | 32 | [31..0] | [31..0] |
| 2SD | 6 | 31 | 33 | [31..0] | [31..0] |
| 3SD | 6 | 31 | 35 | [31..0] | [31..0] |
| 2SD | 3 | 3 | 5 | [3,2,1,0] | [3,2,1,0] |
| 3SD | 3 | 3 | 7 | [3,2,1,0] | [3,2,1,0] |

성립 조건은 `mode`가 정확히 복원되는 것뿐인데, `mode`는 파일 본문이 아니라 파일명에서만 온다.
`run.py:209-211`의 생성 파일명이 `mode`를 포함하므로 정상 경로에서는 항상 성립한다.
파일명이 바뀌면 무너진다 (F-3 참조).

**2SD/3SD 균일 매트릭스 생성 경로는 열려 있다.** `run.py:201-204`가
`internal_quantize.mode`로 HD/2SD/3SD를 모두 받고, `setup()`이 그대로
`make_internal_uniform_matrix`에 넘긴다. 실측 결과 2SD/3SD 매트릭스는 정상적으로 합성되고
파일로 저장되며 `MinSumDecoder` 생성까지 성공한 뒤, 첫 복호에서
`NotImplementedError: 2SD 디코딩 산술 미구현`으로 멈춘다. 즉 실패는 나지만 **실패 시점이
늦고, 그 전에 추적 디렉토리에 파일이 하나 쓰인다** (F-5 참조).

합성값 자체도 2SD/3SD 의미와 어긋난다. `values = [channel_llr] * ch_len + th`
(`llr_matrix.py:226`)라 ch 칸 2개(2SD) 또는 4개(3SD)를 전부 같은 값으로 채운다. soft decision의
신뢰도 구분이 사라진 매트릭스다. 디코더가 막고 있어 지금은 무해하지만, 2SD/3SD 디코딩이
열리는 시점에 이 값이 그대로 쓰이면 조용히 틀린다.

### ㉰ 파일에 없는 정보 (edge_mag / mode / is_uniform) — 오탐과 누락 둘 다 실재 (실측)

`"uniform" in os.path.basename(path).lower()` (`llr_matrix.py:170`) 판정의 실측 결과.

| 파일명 | `mode` 판정 | `is_uniform` |
|--------|-------------|--------------|
| `LLR_MATRIX_HD_0.txt` | HD | False |
| `llr_matrix_hd_0.txt` | HD | False |
| `LLR_MATRIX_HD_UNIFORM_3bit.txt` | HD | True |
| `LLR_MATRIX_HD_nonuniform_tuned.txt` | HD | **True** (오탐) |
| `MY_LLR_MATRIX_2SD_backup_LLR_MATRIX_HD_0.txt` | **2SD** (첫 매칭) | False |

- **오탐**: `nonuniform`, `uniformity` 등 `uniform`을 부분문자열로 갖는 이름이 전부 True가 된다.
  실측으로 `Input/LLR/LLR_MATRIX_HD_1.txt`를 `LLR_MATRIX_HD_uniform_tuned_1.txt` 이름으로 두고
  로드하니 `edge_mag`가 `[7,5,3,1]`이 아니라 `[3,2,1,0]`이 되었다. 에러 없이 로드되고
  복호 결과만 달라진다.
- **누락**: 생성된 uniform 파일이 개명되어 `uniform`이 빠지면 `is_uniform=False`가 된다.
  num_bits ≥ 4면 `th_len != 3`이라 `NotImplementedError`로 걸린다(실측: 6-bit 개명 →
  `th 31개 — 파일 매트릭스는 3-bit(th 3개) 전용`). **num_bits=3만 `th_len == 3`이라 검사를
  통과해 `edge_mag`가 `[3,2,1,0]` 대신 `[7,5,3,1]`로 조용히 바뀐다** (실측 확인).
  `run.py:195-196`의 `_check_int(..., "num_bits", ..., 2)`가 하한 2만 보므로 num_bits=3은
  정상 설정값이다.
- **`re.IGNORECASE`**: 소문자 `llr_matrix_hd_uniform_3bit.txt`도 통과하고
  `m.group(1).upper()`가 `"hd"` → `"HD"`로 정규화하므로 동작은 정상이다 (실측: mode='HD',
  edge_mag=[3,2,1,0]). 기능적 문제는 없다.
- **`search` + basename**: 디렉토리 이름은 보지 않아(`uniform/LLR_MATRIX_HD_0.txt` →
  is_uniform=False) 그쪽 오탐은 없다. 대신 basename 안 어디서든 첫 매칭을 취하므로 백업
  접두어가 붙은 이름에서 엉뚱한 모드를 집는다 (위 표 마지막 줄).

### ㉱ restart 생략 대칭 — 문제 없음 (실측)

`save()`의 `if self.restart_iters:` (`llr_matrix.py:246`)와 `load()`의
`if num_restart > 0:` (`llr_matrix.py:185`)는 대칭이다.

- restart 없음: `Input/LLR/LLR_MATRIX_HD_1.txt` (num_restart=0) 왕복 후 `restart_iters` 양쪽
  모두 빈 set.
- restart 있음: `Input/LLR/LLR_MATRIX_HD_0.txt` (num_restart=1, restart_iter=2) 왕복 후
  `restart_iters == {2}` 유지, `_validate`의 restart 그룹 제약도 통과.

주의 하나: `restart_iters`가 `set`이라 원본 파일에 중복 iteration이 적혀 있으면 저장 시
개수가 줄어든다. 현재 파일에는 중복이 없어 실해는 없다.

### ㉲ floor_flag 고정 기입 — 손실 규모 0 (실측), 라이브 경로 없음

`save()`가 tail의 floor를 항상 `-1`로 쓴다 (`llr_matrix.py:255`). `__init__`은 rows 튜플의
5번째 원소를 아예 보관하지 않는다 (`llr_matrix.py:86-91`이 `r[0]`~`r[3]`만 쓴다).

- 커밋된 파일의 실제 floor 값 (실측): `LLR_MATRIX_HD_0.txt` = `[-1, -1, -1]`,
  `LLR_MATRIX_HD_1.txt` = `[-1, -1]`, `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` = `[-1]`.
  전부 -1이라 지금 손실되는 정보는 없다.
- 파일 → 객체 → 파일 왕복이 일어나는 코드 경로는 없다. `save()` 호출부는
  `run.py:302` 한 곳뿐이고 대상은 방금 합성한 객체다 (`grep -rn "\.save("` 결과
  `run.py:302`, `tools/H_mat_gen/gen_example_code.py:57`, `select_irregular.py:110` —
  뒤 둘은 `QCCode.save`).

### ㉳ int 캐스팅과 float32 정밀도 — 실측상 도달 불가한 한계

- `float32`가 정수를 정확히 담는 한계는 2^24다. `top_level = 2**(num_bits-1) - 1`이므로
  **num_bits ≤ 25까지 정확, num_bits = 26에서 깨진다** (실측: num_bits=25 → top_level
  16,777,215 정확 / num_bits=26 → top_level 33,554,431 이 float32에서 33,554,432).
- 그 지점에서 th 배열 내부 인접 정수도 뭉개진다 (실측: 원본
  `[16777220, 16777219, 16777218, 16777217, 16777216, 16777215]` → float32 후 `int()`
  `[16777220, 16777220, 16777218, 16777216, 16777216, 16777215]`, 중복 2건). th가 중복되면
  캐스케이드 레벨 두 개가 같은 경계를 갖게 된다.
- 다만 num_bits=26이면 `num_param`이 33,554,432이라 배열만 134MB, 파일은 수백 MB다.
  메모리·시간이 먼저 무너지므로 실무 도달 불가다. 실측 규모는 아래 ㉵ 표 참조.
- `int()` 절단 방향: 값이 정확한 정수면 방향 문제가 없다 (실측
  `int(np.float32(-1.0)) == -1`). 합성값과 파일값은 전부 정수이므로 절단 손실 없음.
- `max_value` / `min_value`는 int32 별도 경로라 무관하다.

### ㉴ max_value / min_value 합성값 — 소비처 없음, DAO 값과 도메인 다름

실측 대조:

| 파일 / 합성 | num_param | max_value | 실제 값 범위 |
|-------------|-----------|-----------|--------------|
| `LLR_MATRIX_HD_0.txt` | 4 | 전부 31 | ch 최대 28, th 최대 31, 전체 최소 -1 |
| `LLR_MATRIX_HD_1.txt` | 4 | 전부 31 | ch 최대 28, th 최대 31, 전체 최소 1 |
| `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` | 32 | 전부 31 | ch 8, th 최대 31 |
| 합성 num_bits=6, ch_llr=8 | 32 | 전부 31 | — |
| 합성 num_bits=3, ch_llr=40 | 4 | 전부 **40** | — |

- 한 값으로 전 칸을 채우는 **형태**는 DAO 파일과 같다 (DAO 파일도 4칸 전부 31).
- **값의 의미**가 다르다. DAO의 31은 5-bit 데이터패스 포화 한계이고(실제 값 최대 28보다 크다),
  합성값은 `max(top_level, channel_llr)`이라 실제 값의 최대치다. num_bits=3 / channel_llr=40이면
  40이 되는데 이는 어떤 데이터패스 폭도 아니다.
- **소비처 없음 (실측)**: `grep -rn "max_value\|min_value"` 결과 Python 쪽에서는
  `llr_matrix.py`의 저장(`:83-84`)과 기록(`:249-250`)뿐이고 디코더·시뮬 어디서도 읽지 않는다.
  C++ 쪽도 `local_opt.cpp:91-100` 읽기와 `:164-167` 로그 출력에만 등장하고 `decoder.cpp`에는
  없다. Python 동작에는 영향이 없다. 이 파일이 외부 DAO 최적화기로 넘어갈 때만 의미가 생긴다.

### ㉵ 파생값 정합과 경계 — 불변식 모순 없음, num_bits 상한이 없음

불변식은 서로 모순되지 않는다. `th` 개수 = top_level, `edge_mag` 길이 = top_level + 1,
`num_param = ch_len + top_level`, `__init__`의 `th_len = num_param - ch_len = top_level`이므로
`len(edge_mag) == th_len + 1` 검사(`llr_matrix.py:74`)를 항상 통과한다. 실측 12개 조합 전부 통과.

경계값 실측:

| num_bits | 결과 |
|----------|------|
| 0 | `TypeError: 'float' object cannot be interpreted as an integer` — `2**(0-1)-1 = -0.5`(float)가 `range()`에 들어간다 |
| 1 | `ValueError: num_param 1이 HD ch 1개 이하` (top_level=0, th 0개) |
| 2 | 정상. top_level=1, num_param=2, th=[1], edge_mag=[1,0] |
| 3 | 정상. top_level=3, num_param=4, th=[3,2,1], edge_mag=[3,2,1,0] |

`run.py:195-196`의 `_check_int`가 하한 2를 걸어 0과 1은 config 단계에서 막힌다. 직접 호출
경로에서는 위 에러가 난다 (num_bits=0의 메시지는 원인을 가리키지 않는다).

**상한은 없다.** 큰 num_bits 실측:

| num_bits | top_level | num_param | 파일 크기 | 합성 | 저장 | 로드 | 왕복 동일 |
|----------|-----------|-----------|-----------|------|------|------|-----------|
| 8 | 127 | 128 | 1,226 B | 0.00s | 0.00s | 0.01s | True |
| 12 | 2,047 | 2,048 | 23,523 B | 0.00s | 0.00s | 0.01s | True |
| 16 | 32,767 | 32,768 | 447,700 B | 0.00s | 0.01s | 0.02s | True |
| 20 | 524,287 | 524,288 | 8,277,557 B | 0.08s | 0.28s | 0.28s | True |

파일 자체는 20-bit까지 문제없이 왕복한다. 병목은 소비측이다. `decoder.py:156`의
`for k in range(len(edge_mag) - 2, -1, -1)`가 VNU 호출마다 `2^(num_bits-1)`번 도는
파이썬 루프라 복호 시간이 `2^num_bits`에 선형이다. 실측 (8 프레임 × 3 iteration,
example_18x147_z256):

| num_bits | edge_mag 길이 | 시간 |
|----------|---------------|------|
| 6 | 32 | 0.14 s |
| 8 | 128 | 0.43 s |
| 10 | 512 | 1.59 s |
| 12 | 2,048 | 6.30 s |

num_bits=16이면 같은 조건에서 약 100초, 실제 실험 규모(수천 프레임 × 30 iteration)에서는
사실상 멈춘 것과 구분되지 않는다. (캐스케이드 루프 자체는 관점 B 담당이므로 여기서는
num_bits 상한 부재라는 입력 검증 측면으로만 보고한다.)

### ㉶ dv 구간 — 문제 없음 (실측)

- `setup()`이 `dv_max=int(code.col_deg.max())` (`run.py:298`)로 넘기므로 run.py 경로에서
  dv_max가 실제 최대 column degree보다 작아지는 일은 없다.
- 실측 H-matrix `example_18x147_z256.qc`: col_deg 최소 2, 최대 4,
  히스토그램 `{2:17, 3:1, 4:129}`. `col_dv_idx()`가 전 column block에 0을 반환한다.
- `col_deg`에 0이 있으면 `[1, dv_max]`에 안 들어가 명시적 `ValueError`가 난다
  (실측: `dv=0 (col block 0)가 dv_from/dv_to [1]~[4] 어느 구간에도 없음`). 조용한 fallback
  없음.
- `make_internal_uniform_matrix`를 직접 호출하며 dv_max를 작게 주면 `col_dv_idx()`에서
  같은 형태의 명시적 에러가 난다 (실측: degree 9, dv_max 4).

### ㉷ save() 출력 형식 — 커밋 파일과 바이트 완전 동일 (실측)

`Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`를 파일명의 파라미터
(num_bits=6, channel_llr=8, max_iter=30)와 H-matrix에서 얻은 dv_max=4로 재생성한 결과
**바이트 완전 일치 (301 B == 301 B)**. 생성 로직과 커밋된 산출물이 어긋나지 않았다.

`"\n".join(lines).rstrip("\n") + "\n"` (`llr_matrix.py:259`)은 마지막 빈 원소를 걷어내고
개행 하나로 끝낸다. 빈 줄은 `load()`가 무시하고 DAO의 `fscanf("%d")`도 공백을 건너뛰므로
안전하다.

사람이 만든 파일과의 형식 차이 (실측, `LLR_MATRIX_HD_0.txt` 24줄 → 재저장 25줄):

- `save()`는 group_rows와 group_type 사이에 빈 줄을 넣는데 원본 파일은 붙여 쓴다. 값은 전부
  동일하고 파서가 빈 줄을 무시하므로 무해하다.
- 원본 row 줄 끝에 있는 후행 공백이 사라진다. 무해하다.
- **줄바꿈이 플랫폼 종속이다.** `open(path, "w")` 텍스트 모드 + `"\n"` 조합이라 Windows에서
  CRLF로 나간다 (실측: 커밋된 uniform 파일 CRLF 19개, 사람이 만든 `LLR_MATRIX_HD_1.txt`는
  LF 21개). `.gitattributes`가 없어 같은 파라미터를 리눅스에서 생성하면 다른 바이트로
  커밋된다.

---

## 발견 목록

| 심각도 | 문제 | 위치 | 근거 |
|--------|------|------|------|
| HIGH | 파일명에 `uniform`이 부분문자열로 들어간 사람 제작 3-bit 매트릭스가 균일 레벨로 오해석되어 조용히 다른 결과를 낸다. `nonuniform`도 `is_uniform=True`가 된다 | `llr_matrix.py:170` | 실측: `LLR_MATRIX_HD_1.txt` 내용을 `LLR_MATRIX_HD_uniform_tuned_1.txt` 이름으로 로드 → `edge_mag`가 `[7,5,3,1]` 대신 `[3,2,1,0]`. 에러 없음. `LLR_MATRIX_HD_nonuniform_tuned.txt` → `is_uniform=True` |
| HIGH | 생성된 **3-bit** uniform 파일이 개명되어 `uniform`이 빠지면 `th_len == 3` 검사를 통과해 `edge_mag`가 `[3,2,1,0]` → `[7,5,3,1]`로 조용히 바뀐다 (4-bit 이상은 `NotImplementedError`로 걸림) | `llr_matrix.py:170`, `llr_matrix.py:67-72` | 실측: `num_bits=3` 생성 파일을 `LLR_MATRIX_HD_9.txt`로 두고 로드 → 에러 없이 `edge_mag=[7,5,3,1]`. `run.py:195-196`이 num_bits 하한 2만 보므로 3은 정상 설정값 |
| MEDIUM | mode가 파일명에서만 오므로 다른 모드 이름으로 저장·개명하면 ch/th 경계가 조용히 밀린다. `_NAME_RE.search`가 basename 어디서든 첫 매칭을 취해 백업 접두어에도 걸린다 | `llr_matrix.py:46`, `llr_matrix.py:165-169` | 실측: HD `num_param=4` 매트릭스를 `LLR_MATRIX_2SD_uniform_*.txt`로 저장 → 로드 시 `row_ch=[8,3]`, `row_th=[2,1]`, `edge_mag=[2,1,0]` (th 첫 값 3이 채널 값으로 재분류). `MY_LLR_MATRIX_2SD_backup_LLR_MATRIX_HD_0.txt` → mode='2SD' |
| MEDIUM | `num_bits` 상한이 없어 큰 값에서 복호가 사실상 멈춘다 (`_vnu_quantize`의 파이썬 루프가 `2^(num_bits-1)`회) | `run.py:195-196` (검증), `decoder.py:156` (소비) | 실측 8프레임 3 iteration: num_bits 6→0.14s, 8→0.43s, 10→1.59s, 12→6.30s. 16이면 약 100s, 실험 규모(수천 프레임 × 30 iteration)에서 hang과 구분 불가 |
| MEDIUM | 생성 파일이 git 추적 디렉토리 `Input/LLR/`에 기본 기록된다. 파라미터 조합마다 파일이 쌓이고, 같은 이름의 사람 제작 파일이 있으면 매 실행마다 조용히 덮어쓴다 | `run.py:206`, `run.py:300-302` | `git ls-files`로 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`가 실제로 커밋되어 있음을 확인. `save()`는 존재 여부를 보지 않고 무조건 덮어쓴다 |
| LOW | `mode="2SD"/"3SD"` 균일 매트릭스는 ch 칸을 전부 같은 `channel_llr`로 채워 soft decision 구분이 없다. 파일 생성까지 성공한 뒤 첫 복호에서야 실패한다 | `llr_matrix.py:226`, `run.py:201-204`, `run.py:294-302` | 실측: 2SD `num_bits=4` → `row_ch=[8,8]`, 파일 저장·디코더 생성 성공, `decoder_main`에서 `NotImplementedError: 2SD 디코딩 산술 미구현`. 실패 전에 추적 디렉토리에 파일이 남는다 |
| LOW | `save()`가 floor_flag를 항상 `-1`로 쓰고 `__init__`은 floor를 보관조차 하지 않는다 | `llr_matrix.py:255`, `llr_matrix.py:86-91` | 실측: 커밋된 3개 파일의 floor는 전부 `-1`이라 현재 손실 0. 파일→객체→파일 경로도 없다 (`save()` 호출부는 `run.py:302`의 합성 객체 한 곳뿐). 잠재 손실만 |
| LOW | `max_value` 합성값 `[max(top_level, channel_llr)] * num_param`이 DAO의 데이터패스 포화 한계와 도메인이 다르고, 코드베이스 어디서도 소비되지 않는다 | `llr_matrix.py:230`, `llr_matrix.py:83-84`, `llr_matrix.py:249-250` | 실측: DAO 파일은 실제 최대(28)보다 큰 31(5-bit 한계)을 쓰는데 합성은 실제 값의 최대치. `num_bits=3, channel_llr=40` → `max_value=40` (어떤 데이터패스 폭도 아님). grep 결과 Python은 저장·기록만, C++도 `local_opt.cpp:91-100` 읽기와 `:164-167` 로그뿐 |
| LOW | `save()`의 줄바꿈이 플랫폼 종속이라 같은 파라미터가 OS마다 다른 바이트로 나간다 | `llr_matrix.py:258` | 실측: 커밋된 uniform 파일 CRLF 19개, 사람 제작 `LLR_MATRIX_HD_1.txt`는 LF 21개. 저장소에 `.gitattributes` 없음 |
| LOW | `num_bits=0`에서 `top_level`이 float `-0.5`가 되어 원인을 알 수 없는 `TypeError`로 죽는다 | `llr_matrix.py:222` | 실측: `TypeError: 'float' object cannot be interpreted as an integer` (`range()`에서 발생). `run.py`의 `_check_int` 하한 2가 config 경로는 막는다 |

---

## 문제 없다고 판정한 항목

- ㉮ 왕복 필드 대조: 12개 조합 × 19개 필드 전부 일치 (`name` 제외, 설계 의도).
- ㉯ edge_mag 이원 복원식: 정상 경로(파일명이 생성 규칙을 지킬 때)에서 항상 등가.
- ㉱ restart 생략 대칭: restart 있는 파일과 없는 파일 모두 왕복 보존.
- ㉳ float32 / `int()` 캐스팅: num_bits ≤ 25까지 정확, 26 이상은 메모리·시간이 먼저 무너져
  실무 도달 불가. 음수 절단 손실 없음.
- ㉵ 파생값 불변식: `len(edge_mag) == th_len + 1`이 정의상 항상 성립.
- ㉶ dv 구간: `[1, dv_max]`가 전 column을 덮고, 미매칭은 명시적 에러.
- ㉷ 커밋된 uniform 파일이 재생성 결과와 바이트 완전 동일 (301 B).
