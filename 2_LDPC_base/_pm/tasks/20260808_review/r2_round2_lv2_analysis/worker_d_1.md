# worker_d_1 — 팀 D 워커 1, 관점 G (데이터 파일 무결성)

- 작성: 2026-08-08 14:27:22
- 검증 스크립트: `{scratchpad}/verify_data.py`, `{scratchpad}/verify_tracking.py` (저장소 밖)
- 대상 파일 3종 + H-matrix 1종, 전부 실제 파싱·실행으로 확인 (추측 없음)

---

## 확인 대상 실측 목록

| 파일 | 크기 | 인코딩 | 개행 | 구분자 | 끝 개행 | sha1(앞12) |
|------|------|--------|------|--------|---------|------------|
| `Input/LLR/LLR_MATRIX_HD_0.txt` | 254 B | ASCII, BOM 없음 | CRLF 23개 | 탭 | **없음** | af6493354598 |
| `Input/LLR/LLR_MATRIX_HD_1.txt` | 166 B | ASCII, BOM 없음 | **LF 21개** | 탭 | 있음 | 3a2330327455 |
| `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` | 301 B | ASCII, BOM 없음 | CRLF 19개 | 탭 | 있음 | 08894ddfb5fd |
| `Input/H_matrix/example_18x147_z256.qc` | 8252 B | ASCII, BOM 없음 | CRLF 22개 | 공백 | 있음 | — |

`2_LDPC_light/.gitignore`는 존재하지 않고, 저장소 루트 `.gitignore` 하나만 있다. `.gitattributes`는 저장소 전체에 없다.

---

## ㉮ LLR 파일 자기 정합 — `_validate`의 5개 제약

세 파일 모두 헤더를 직접 파싱해 대조했고, 이어서 `LLRMatrix.load()`를 실제로 호출해 예외·경고 없이 통과함을 확인했다.

### LLR_MATRIX_HD_0.txt

```
num_param=4  num_dv=4  ch_len=1(HD)  th_len=3
dv_from=[11,4,3,2]  dv_to=[11,4,3,2]
num_group=3  group_rows=[1,1,1]  group_type=[1,1,1]  (전부 CSW)
num_restart=1  restart_iters=[2]
max_value=[31,31,31,31]  min_value=[0,0,0,0]
row1 = 1 28 9 5 | 10 10 9 4 | 13 31 10 7 | 28 12 10 8 | csw=-1 iter=[1,1] floor=-1
row2 = -1 x16                                          | csw=-1 iter=[2,2] floor=-1
row3 = 5 28 9 5 | 10 10 9 4 | 13 31 10 7 | 28 12 10 8 | csw=-1 iter=[3,5] floor=-1
```

| 제약 | 결과 |
|------|------|
| 그룹 간 iteration 겹침 금지 | g1[1,1] g2[2,2] g3[3,5], 겹침 없음 |
| 1..max_iter 커버리지 | 빈틈 없음, max_iter=5 |
| restart 그룹은 단일 row/단일 iteration | restart 2 → g2, row 1개, iter [2,2], 만족 |
| restart 그룹이 마지막이면 안 됨 | g2는 3개 중 2번째, 만족 |
| ITER 다중 row 그룹 내부 연속성 | 해당 그룹 없음 (전 그룹 CSW, 각 1 row), 검사 대상 없음 |
| 헤더 개수 필드 = 배열 길이 | dv_from/dv_to 4, group_rows/type 3, restart 1, max/min_value 4 (= num_param), 전부 일치 |
| row 길이 = num_dv*num_param+4 = 20 | 3 row 전부 20 |
| group_rows 합 = row 수 | 3 = 3 |
| th 내림차순 (경고 조건) | (28,9,5) (10,9,4) (31,10,7) (12,10,8) 전부 내림차순, 경고 발생 없음 |

### LLR_MATRIX_HD_1.txt

```
num_param=4  num_dv=4  dv=[11,4,3,2]  num_group=2  group_rows=[1,1]  group_type=[1,1]
num_restart=0  max_value=[31]x4  min_value=[0]x4
row1 = (HD_0 row1과 동일 값) csw=-1 iter=[1,1] floor=-1
row2 = 5 28 9 5 | 10 10 9 4 | 13 31 10 7 | 28 12 10 8 | csw=-1 iter=[2,20] floor=-1
```

겹침 없음, 커버리지 1~20 빈틈 없음, restart 없음, row 길이 20, th 내림차순. 5개 제약 전부 통과.

### LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt

```
num_param=32  num_dv=1  dv_from=[1]  dv_to=[4]
num_group=1  group_rows=[1]  group_type=[0](ITER)  num_restart=0
max_value=[31]x32  min_value=[0]x32
row1 = ch=8, th=31,30,...,2,1 | csw=-1 iter=[1,30] floor=-1   (길이 1*32+4 = 36)
```

커버리지 1~30 빈틈 없음, restart 없음, th 내림차순. 통과.

**㉮ 결론: 문제 없음.** 다만 `max_value`/`min_value`의 길이(= `num_param`, C++ `local_opt.cpp:93-100`의 `num_para_each_set`와 일치)를 로더가 검사하지 않는다 (아래 F5).

---

## ㉯ H-matrix 정합

```
헤더 line0='147 18'  line1='4 31'  line2='256', 데이터 18줄
원소 수 2646 = 18x147                        OK
shift 값 범위 min=0 max=255 (0 <= s < z=256)  OK  (z 이상 0건, -1 미만 0건)
QCCode.load 통과 (J/K 검사 포함)
col degree hist {2:17, 3:1, 4:129}   실측 max=4 = 헤더 J=4  (정확히 일치)
row degree hist {30:5, 31:13}        실측 max=31 = 헤더 K=31 (정확히 일치)
N=37632, K=33024, rate=0.8776, E(base)=553
column block DV 내림차순 배치: 성립 (앞 129개 dv4 → 1개 dv3 → 뒤 17개 dv2)
degree 0인 column block: 없음
```

`README.md:14`의 "column block은 DV 내림차순 배치" 전제와 실제 배치가 일치한다.

**㉯ 결론: 문제 없음.**

---

## ㉰ LLR ↔ H-matrix 상호 정합

`col_dv_idx(code)` 실행 결과 (147개 column block 전부):

| LLR 파일 | dv 구간 | 매칭 column block 수 |
|----------|---------|---------------------|
| HD_0 / HD_1 | idx0 dv[11..11] | **0개 (죽은 구간)** |
| | idx1 dv[4..4] | 129개 |
| | idx2 dv[3..3] | 1개 |
| | idx3 dv[2..2] | 17개 |
| uniform | idx0 dv[1..4] | 147개 (전부) |

미매칭 dv는 0건이라 `llr_matrix.py:268-271`의 `ValueError` 경로는 발동하지 않는다. 즉 에러 없이 정상 동작하며, dv=11 구간만 영영 쓰이지 않는다.

**dv=11 미매칭이 의도인지의 근거**: 직전 리뷰에서 이미 판정이 끝난 사항이다. `_pm/done/20260806_review/r2_round2_lv1_analysis/agent_3.md:78`에 "dv=11 행은 실물 부호(dv 최대 11 이상)용 파라미터가 그대로 남아 있는 것이고, H-matrix 헤더 J와 LLR 테이블 dv 구간은 서로 다른 것을 뜻하므로 일치할 이유가 없다"로 기록돼 있고, `report.md:18`에도 "dv=11 그룹 미사용"이 관찰 항목으로 남아 있다. 실물 파일 반입은 `_pm/TODO.md`에 미착수 항목으로 등록돼 있다. **의도된 상태로 판정한다.**

**㉰ 결론: 코드 동작에 문제 없음.** 다만 `README.md:15`의 `Input/LLR/` 설명이 이 죽은 구간과 커밋된 uniform 파일을 언급하지 않는다 (아래 F6, 관점 H와 경계 항목).

---

## ㉱ 반전 가능 조건 위반 잔존 — **위반 그대로 남아 있음**

`_pm/TODO.md:18-20`의 "반전 가능 조건 `ch ≤ 7·dv`(3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)" 항목을 현 파일 실값으로 대조했다. uniform 파일은 n-bit 일반화 `top_level·dv`(top_level = th 개수 = 31)를 적용했다.

| 파일 | row | dv 구간 | ch | 상한 (top_level·dv_min) | 판정 |
|------|-----|---------|-----|------------------------|------|
| HD_0 | 1 | 11 | 1 | 77 | OK |
| HD_0 | 1 | 4 | 10 | 28 | OK |
| HD_0 | 1 | 3 | 13 | 21 | OK |
| HD_0 | 1 | **2** | **28** | **14** | **위반** |
| HD_0 | 2 | 전 구간 | -1 | — | restart row (-1은 설계 의도) |
| HD_0 | 3 | 11 / 4 / 3 | 5 / 10 / 13 | 77 / 28 / 21 | OK |
| HD_0 | 3 | **2** | **28** | **14** | **위반** |
| HD_1 | 1 | 11 / 4 / 3 | 1 / 10 / 13 | 77 / 28 / 21 | OK |
| HD_1 | 1 | **2** | **28** | **14** | **위반** |
| HD_1 | 2 | 11 / 4 / 3 | 5 / 10 / 13 | 77 / 28 / 21 | OK |
| HD_1 | 2 | **2** | **28** | **14** | **위반** |
| uniform | 1 | 1~4 (dv_min=1) | 8 | 31 | OK |

위반은 총 4개 row 인스턴스 (HD_0 row1·row3, HD_1 row1·row2).

### 결과에 실제로 미치는 영향 (코드 경로 + 실행 실측)

`decoder.py:266-279`에서 `sum_t = +ch + Σ vnu_in`이고, `decoder.py:142`의 판정이 `sum_t <= 0`이다. `vnu_in` magnitude는 `_vnu_quantize`가 `edge_mag`(파일 3-bit = {7,5,3,1})에서만 고르므로 `|vnu_in| <= 7`이다. dv=2 column은 edge가 2개뿐이라

```
sum_t >= 28 - 2*7 = 14 > 0   (모든 iteration, 모든 프레임)
```

즉 **dv=2 column의 비트는 어떤 iteration에서도 반전되지 않는다.** 17개 column block × z=256 = 4352 bit (전체 37632 bit의 11.6%)가 채널 값에 고정된다.

scratchpad에서 짧은 실행(`HD_1`, fixed_error 300, 8프레임, `bit_err_by_dv` 로그)으로 실측한 iteration별 dv 구간 에러:

```
iter  csw_mean  bit_err_mean  dv11    dv4      dv3     dv2
1     1197.25   487.50        0.000   450.375  2.625   34.500
5      388.25    80.38        0.000    44.500  1.375   34.500
10     174.25    43.12        0.000     8.375  0.250   34.500
20     167.38    41.88        0.000     7.250  0.125   34.500
```

`dv2` 열이 20 iteration 내내 **34.500으로 한 번도 변하지 않는다**. 최종 잔여 에러 41.88 중 34.5(82%)가 이 고정 비트다. FER은 1.0으로 수렴하며, 원인은 알고리즘이 아니라 데이터다.

**㉱ 결론: TODO에 등록된 위반이 현 파일에 그대로 남아 있고, 실행 결과를 실제로 왜곡한다.** TODO에 미착수 항목으로 등록돼 있으므로 신규 결함은 아니나, 이 파일로 vanilla reference 커브를 뽑으면 그 커브 자체가 무의미하다는 점을 리뷰 결론에 명시할 필요가 있다 (F1).

---

## ㉲ 균일 생성 파일 재생성 대조

파일명에서 `num_bits=6, channel_llr=8, max_iter=30`을 읽고, `dv_max`는 H-matrix 실측값 `col_deg.max()=4`를 넣어 `LLRMatrix.make_internal_uniform_matrix(num_bits=6, channel_llr=8, max_iter=30, dv_max=4, mode="HD")` → `save()`로 재생성한 뒤 대조했다.

```
바이트 동일: True   (원본 301 B / 재생성 301 B)
정규화 라인 동일: True
```

기대값 대조도 전부 일치한다.

| 항목 | 기대 | 실측 |
|------|------|------|
| num_param | 32 (= ch 1 + top_level 31) | 32 |
| num_dv | 1 | 1 |
| dv 구간 | 1~4 | dv_from=[1], dv_to=[4] |
| group_type | ITER(0), 그룹 1개 | `[0]`, group_rows `[1]` |
| num_restart | 0 | `restart_iters = []` |
| max_value | 전 원소 `max(31, 8) = 31` | 32개 전부 31 (고유값 {31}) |
| min_value | 전 원소 0 | 32개 전부 0 |
| row 구성 | ch 8 + th 31..1 + (csw −1, iter 1, iter 30, floor −1) | ch=8, th=[31,30,...,2,1], csw=-1, iter=[1,30], floor=-1 |
| edge_mag | [31..0], 길이 32 | [31,30,...,1,0], 길이 32 |

**㉲ 결론: 문제 없음 (바이트 단위 일치).**

---

## ㉳ 왕복(round-trip) 무결성 — `load()` → `save()`

| 파일 | 바이트 동일 | 정규화 라인 동일 | 재로드 후 의미 동일 |
|------|------------|-----------------|-------------------|
| HD_0 | 아니오 | **예** | **예** |
| HD_1 | 아니오 | **예** | **예** |
| uniform | **예** | 예 | 예 |

의미(`row_values`, `row_csw`, `row_iter`, `restart_iters`, `edge_mag`)는 세 파일 모두 완전히 보존된다. 바이트 차이는 전부 형식 층이다.

| 차이 | 발생 파일 | 원인 |
|------|-----------|------|
| 개행이 LF → CRLF로 바뀜 | HD_1 | `save()`가 텍스트 모드(`open(path,"w")`)로 쓰므로 플랫폼 기본 개행이 나온다 (Windows CRLF, Linux LF) |
| `group_rows`와 `group_type` 사이 빈 줄이 생김 | HD_0 | 원본은 두 줄이 붙어 있고 `save()`(`llr_matrix.py:242-243`)는 사이에 빈 줄을 넣는다. 로더가 빈 줄을 버려 무해 |
| row 끝 공백 1칸이 사라짐 | HD_0 (row1, row3) | 원본에 trailing space가 있다 |
| 파일 끝 개행이 추가됨 | HD_0 | 원본에 마지막 개행이 없다 |

### floor_flag 왕복 손실 (현 파일에는 영향 없음, 잠재)

`llr_matrix.py:255`가 tail의 4번째 값을 `-1`로 **고정 기입**하고, `__init__`은 `rows[i][4]`(floor)를 아예 저장하지 않는다. 현 3개 파일은 전부 floor_flag가 `-1`이라 관측되는 차이가 없다.

`HD_1`의 row tail을 `csw=7, floor=3`으로 바꾼 가상 파일로 실측했다.

```
row1 원본 tail=['7','1','1','3']   왕복 tail=['7','1','1','-1']   >>> 손실
row2 원본 tail=['7','2','20','3']  왕복 tail=['7','2','20','-1']  >>> 손실
```

csw는 보존되고 floor_flag만 소실된다. `floor_flag`는 C++에서도 `local_opt.cpp:114`(읽기)와 `:178`(로그 출력)에만 쓰이고 디코더 산술에는 등장하지 않으므로 디코딩 결과에는 영향이 없다. 다만 DAO 파일을 이 코드로 왕복시키면 DAO 최적화 로그가 참조하는 필드가 소실된다.

### 그 밖의 잠재 캐스팅

- `row_values`는 `float32`로 저장되고 `save()`는 `int()`로 되돌린다. float32가 정수를 정확히 담는 상한은 2^24 = 16777216이며 `2^25+1 = 33554433` → `33554432`로 왜곡된다. 현 파일 값은 전부 31 이하라 실제 위험은 없다.
- `restart_iters`가 `set`이라 파일에 중복 iteration이 있으면 왕복에서 개수가 줄고, 기입 순서는 `sorted()`로 바뀐다. 현 파일에는 해당 없음.

**㉳ 결론: 현 3개 파일은 왕복 무손실. floor_flag 고정 기입은 잠재 손실 (F3).**

---

## ㉴ 인코딩·개행

- 인코딩: 4개 파일 전부 순수 ASCII, BOM 없음. `load()`가 `encoding="utf-8"`로 열어도 문제 없다.
- 개행: **파일마다 다르다** (HD_0 CRLF, HD_1 LF, uniform CRLF, H-matrix CRLF). 로더가 `ln.strip()`으로 처리하므로 로드에는 영향이 없고, 세 파일 전부 실제로 로드에 성공했다.
- 구분자: LLR 3개 파일은 탭, H-matrix는 공백. 각 로더가 `split()`(공백류 전부)을 쓰므로 무관하다.
- 마지막 줄 개행: HD_0만 없다. 로더 무관.
- `save()`가 쓰는 형식: 탭 구분 + 플랫폼 기본 개행 + 마지막 개행 있음 + trailing space 없음. HD_1과는 개행만, HD_0과는 위 표의 4가지가 다르다.

### git CRLF 변환의 영향

`.gitattributes`가 없고 `core.autocrlf=true`다. git object store의 blob은 4개 파일 전부 **LF**로 정규화돼 있다 (HD_0 blob 231 B vs 워킹트리 254 B, uniform blob 282 B vs 301 B).

`git hash-object`를 설정별로 돌려 확인했다.

```
uniform 파일:  blob(HEAD)     = 234ffaf3...
               autocrlf=true  = 234ffaf3...   일치 (깨끗)
               autocrlf=input = 234ffaf3...   일치 (깨끗)
               autocrlf=false = deae4862...   불일치
HD_0 파일:     blob = aa7bd293..., true = aa7bd293..., false = 73305c1c...
```

즉 **`core.autocrlf=false`인 Windows 환경에서는** 체크아웃이 LF를 주고 `save()`가 CRLF를 쓰므로, 균일 매트릭스를 생성할 때마다 추적 파일이 수정 상태가 된다. 현재 이 저장소 설정(`true`)에서는 왕복 로드와 git 상태 모두 깨끗하다 (실제 재생성 결과 바이트 동일 확인).

**㉴ 결론: 로드에는 영향 없음. `.gitattributes` 부재로 인한 조건부 위험 (F4).**

---

## ㉵ 추적 정책

`git ls-files` 결과 `Input/` 아래 4개 파일이 **전부 추적 대상**이다 (H-matrix 1개 + LLR 3개). `git check-ignore -v` 실측:

```
2_LDPC_light/Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt   → 추적 대상 (무시 안 됨)
2_LDPC_light/Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt  → 추적 대상 (무시 안 됨)
2_LDPC_light/Sim_Output/x.csv                                      → IGNORED (.gitignore:45 Sim_Output/)
2_LDPC_light/_test/x                                               → IGNORED (.gitignore:24 _test/)
```

루트 `.gitignore`는 빌드 산출물, `_test/`, `Sim_Output/`, `result_*.txt`, `__pycache__/`, `0_LDPC_original/H_Matrix/`를 덮고 `Input/LLR/`의 생성물은 하나도 덮지 않는다. `2_LDPC_light/.gitignore`는 존재하지 않는다.

### 매 실행 생성 구조와의 충돌 2가지 (실측)

**(1) 커밋된 파일과 배포 config가 어긋난다.** `config.json:33`의 `internal_quantize.max_iter`는 **120**인데 커밋된 파일은 `iter30`이다. `load_config`를 실제로 태워 생성 경로를 뽑았다.

```
생성 파일명: LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt
생성 위치:   2_LDPC_light/Input/LLR/          (config의 llr_matrix.dir = "Input/LLR")
현재 폴더:   [HD_0.txt, HD_1.txt, uniform_6bit_ch8_iter30.txt]  — 같은 이름 없음
```

즉 배포된 config로 `use_input_llr_matrix: false`를 켜면 추적 폴더에 **새 untracked 파일**이 하나 생기고 `git status`가 더러워진다. 반대로 커밋된 `iter30` 파일은 어떤 배포 config도 만들어내지 않는 고아 산출물이다. 파라미터를 쓸어보는 실험을 하면 추적 폴더에 파일이 계속 쌓인다.

**(2) 파일명이 `dv_max`를 담지 않아 같은 이름에 다른 내용이 들어간다.** 파일명은 `num_bits`/`channel_llr`/`max_iter`만 담는데, `dv_to`는 H-matrix의 `col_deg.max()`에서 온다 (`run.py` setup). 실측:

```
dv_max=4  → dv_to=[4]   301 B
dv_max=6  → dv_to=[6]   301 B
dv_max=11 → dv_to=[11]  302 B
dv_max 4 vs 6 파일 동일? False   (차이: 4번째 유효 줄 '4' vs '6')
파일명은 셋 다 LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt로 동일
```

H-matrix를 바꾸면 같은 이름의 **추적 파일이 조용히 다른 내용으로 덮인다.**

**㉵ 결론: `Input/LLR/`이 "사람이 넣는 입력"과 "매 실행 생성되는 산출물"을 한 폴더에 섞어 두고, `.gitignore`가 후자를 전혀 덮지 않는다 (F2).**

---

## 발견 목록

| # | 심각도 | 문제 | 위치 | 근거 |
|---|--------|------|------|------|
| F1 | HIGH | 두 3-bit 파일의 dv=2 구간 `ch=28`이 반전 가능 상한 `7·dv=14`를 넘어, dv=2 column 4352 bit(전체의 11.6%)가 어떤 iteration에서도 반전되지 않는다. 이 파일로 뽑은 FER 커브는 알고리즘 비교의 기준선이 될 수 없다 | `Input/LLR/LLR_MATRIX_HD_0.txt` row1·row3의 13번째 값, `LLR_MATRIX_HD_1.txt` row1·row2의 13번째 값 / 판정식 `decoder.py:142`, 합산 `decoder.py:266-279` | 대수: `sum_t >= 28 − 2·7 = 14 > 0` 항상 성립. 실측: 20 iteration 내내 `bit_err_dv2_mean = 34.500` 불변, 최종 잔여 에러 41.88 중 34.5가 고정 비트. `_pm/TODO.md:18-20`에 미착수 항목으로 등록돼 있으므로 신규 결함은 아니며, **리뷰 결론에 "현 파일로 뽑은 커브는 무효"를 명시할 것을 제안** |
| F2 | MEDIUM | 추적 폴더 `Input/LLR/`에 매 실행 생성물이 쌓이고 `.gitignore`가 덮지 않는다. ㉮ 배포 config(`max_iter=120`)로 실행하면 커밋본(`iter30`)과 다른 새 untracked 파일이 생기고 커밋본은 고아가 된다. ㉯ 파일명에 `dv_max`가 없어 H-matrix를 바꾸면 같은 이름의 추적 파일이 다른 내용으로 덮인다 | `2_LDPC_light/config.json:33`(`max_iter: 120`), `LDPC_base/run.py` `load_config`의 `generated_name` 조립부와 `generated_dir` 기본값 `"Input/LLR"`, 저장소 루트 `.gitignore` (`Input/` 관련 항목 없음), `2_LDPC_light/.gitignore` 부재 | `git check-ignore -v`: iter30/iter120 둘 다 "추적 대상". `load_config` 실행 결과 생성 파일명 `LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt`. dv_max 4/6/11 재생성 결과 파일 내용이 서로 다름(4번째 유효 줄) |
| F3 | MEDIUM | `save()`가 row tail의 `floor_flag`를 원본 값과 무관하게 `-1`로 고정 기입하고, `__init__`은 floor 값을 저장조차 하지 않는다. DAO 파일을 이 코드로 왕복시키면 필드가 소실된다 | `LDPC_base/llr_matrix.py:254-255`(tail 조립), `:57`·`:86-91`(floor 미저장) | floor=3으로 바꾼 가상 파일 왕복 실측: `['7','1','1','3'] → ['7','1','1','-1']`. 현 3개 파일은 전부 -1이라 관측 영향 없음. C++에서도 `local_opt.cpp:114`(읽기)/`:178`(로그)에만 쓰여 디코딩 결과에는 무영향 |
| F4 | MEDIUM | `.gitattributes`가 없어 `Input/` 텍스트 파일의 개행이 git 설정에 좌우된다. `core.autocrlf=false`인 Windows에서는 `save()`(텍스트 모드, CRLF)가 LF 체크아웃본을 매 실행 수정 상태로 만든다 | 저장소 전체(`.gitattributes` 부재), `LDPC_base/llr_matrix.py:258`(`open(path,"w")`) | `git hash-object` 설정별 실측: uniform 파일이 `autocrlf=true/input`에서는 blob과 일치(`234ffaf3`), `false`에서는 불일치(`deae4862`). 현 저장소 설정(`true`)에서는 재생성 결과가 바이트 동일이라 깨끗함 |
| F5 | LOW | 로더가 `max_value`/`min_value` 줄의 길이를 검사하지 않는다. C++ 원문은 `num_para_each_set`개를 읽는데(`local_opt.cpp:93-100`), Python은 줄 전체를 그대로 받아 개수가 어긋난 파일을 통과시킨다 | `LDPC_base/llr_matrix.py:187-188`(길이 검사 없음), 대비 `:190-191`(dv_from/group_rows는 검사) | 현 3개 파일은 전부 길이 = num_param(4, 4, 32)으로 정상. 두 값 모두 런타임에 쓰이지 않아 실해는 없다 |
| F6 | LOW | `README.md:15`의 `Input/LLR/` 설명이 `HD_0.txt`, `HD_1.txt`만 열거하고, 커밋된 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`와 dv=11 구간이 죽은 파라미터라는 점을 담지 않는다 | `2_LDPC_light/README.md:15` | `ls Input/LLR/` 결과 파일 3개, README 설명은 2개. `col_dv_idx` 실측 dv=11 매칭 0개. 관점 H(worker 2)와 경계 항목이라 중복 보고 가능 |

### 문제 없음으로 판정한 범위

- ㉮ 세 LLR 파일의 `_validate` 5개 제약 + 헤더 개수 필드 + row 길이 + group_rows 합 + th 내림차순: 전부 통과, 경고 없음
- ㉯ H-matrix 헤더 `147 18` / `4 31` / `256`이 실제 행렬과 정확히 일치, shift 전부 `0 <= s < 256`, DV 내림차순 배치 성립
- ㉰ `col_dv_idx`가 147개 column block 전부를 매칭 (미매칭 0건). dv=11 미사용은 직전 리뷰에서 확정된 의도
- ㉲ uniform 파일이 `make_internal_uniform_matrix` 산출과 **바이트 단위 완전 일치**, 기대값 8항목 전부 일치
- ㉳ 현 3개 파일의 왕복 의미 보존 (재로드 후 `row_values`/`row_csw`/`row_iter`/`restart_iters`/`edge_mag` 전부 동일)
- ㉴ 인코딩 ASCII/BOM 없음, 개행 차이가 로드에 영향 없음 (CRLF·LF 파일 모두 로드 성공)
