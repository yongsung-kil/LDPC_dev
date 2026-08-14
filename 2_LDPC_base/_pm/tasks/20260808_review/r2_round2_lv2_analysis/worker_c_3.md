# Round 2 / 팀 C (refactor_exec) / 워커 3 — 동적 실행 검증

작성: 2026-08-08 14:31:32 | 대상 커밋: e6282b1 (+ 미커밋 `2_LDPC_light/config.json`)

## 실행 환경

- Python 3.11.7 (Windows, MSC v.1937 64bit), numpy 1.26.4, matplotlib 3.10.7
- cwd: `D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_light`
- 콘솔 기본 인코딩: `sys.stdout.encoding == sys.stderr.encoding == cp949`
- 모든 config 사본과 산출물은 scratchpad에 둠
  (`C:\Users\yongs\AppData\Local\Temp\claude\d--OneDrive-My-Projects-LDPC-dev\96aaaa04-61b8-4b90-ac92-52ca7348de60\scratchpad\wc3`)
- 저장소 파일은 읽기만 했다. H-matrix와 LLR matrix 입력은 저장소 절대경로로 참조하고,
  `output.dir`과 생성 LLR 경로는 scratchpad로 돌렸다

실행 전 `git status --short`:

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

---

## ① 파일 경로 config 실행 완주 — 통과

명령: `python -m LDPC_base.run <scratchpad>/cfg1_file.json`
(루트 `config.json` 사본, `use_input_llr_matrix: true`, `LLR_MATRIX_HD_1.txt`)

```
LLRMatrix LLR_MATRIX_HD_1.txt: mode=HD (ch1+th3), dv=[11, 4, 3, 2]~[11, 4, 3, 2], max_iter=20, groups: g1[1~1]x1, g2[2~20]x1
decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=20
  frames=    64 errors=  64 FER=1.000e+00 BER=6.261e-04 avg_decode_success_iteration=0.00 (13.5 f/s)
  frames=    64 errors=  64 FER=1.000e+00 BER=1.041e-03 avg_decode_success_iteration=0.00 (13.9 f/s)
run dir: ...\scratchpad\wc3\Sim_Output\260808_142110_fixed_error
```

전체 10.5초에 완주했고 산출물 구성이 모두 생겼다.

- ㉮ `config.json` (사본), `summary.txt`, `fer_fixed_error.csv`, `fer_curves.png`
- ㉯ `log_iter_fixed_error_p200.csv`, `..._p300.csv`
- ㉰ `log_iter_hist_fixed_error_p200.csv`, `..._p300.csv`
- ㉱ `log_fail_fixed_error_p200.csv`, `..._p300.csv`

`summary.txt`에 실행 폴더 이름, `code commit: e6282b1`, 부호 정보, LLR matrix 요약,
디코더 클래스, config 요약, 포인트별 결과가 모두 들어 있었다. FER 커브 PNG는 48,930 바이트로
정상 생성됐다.

참고 사항 하나: `run.max_frames`가 256인데 두 포인트 모두 64 프레임에서 멈췄다.
첫 배치(64 프레임)에서 `max_frame_errors=10`을 넘겼기 때문이며, 배치 단위 종료 판정이라
의도한 동작으로 보인다.

---

## ② 균일 양자화 경로 실행 완주 — 통과

명령: `python -m LDPC_base.run <scratchpad>/cfg2_uniform.json`
(`use_input_llr_matrix: false`, `internal_quantize: {num_bits:6, channel_llr:8, max_iter:30, mode:"HD"}`,
`llr_matrix.dir: "gen"`)

```
generated LLR matrix: ...\scratchpad\wc3\gen\LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt
LLRMatrix LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt: mode=HD (ch1+th31), dv=[1]~[4], max_iter=30, groups: g1[1~30]x1
decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=30
  frames=   128 errors=   0 FER=0.000e+00 BER=0.000e+00 avg_decode_success_iteration=7.47 (17.1 f/s)
  frames=    64 errors=  64 FER=1.000e+00 BER=4.943e-02 ...
```

`internal_quantize` 세 값이 실제로 적용된 증거:

- ㉮ `num_bits: 6` → 요약의 `ch1+th31` (`2^(6-1)-1 = 31`개 임계값)과 파일명 `_6bit`
- ㉯ `channel_llr: 8` → 생성 파일 row 첫 값이 `8`, 이어서 th가 `31 30 ... 1`
- ㉰ `max_iter: 30` → 요약의 `max_iter=30`, `groups: g1[1~30]x1`, 파일명 `_iter30`
- ㉱ `mode: "HD"` → 파일명 `LLR_MATRIX_HD_uniform_...`, 요약의 `mode=HD`
- ㉲ `dv=[1]~[4]`는 H-matrix의 최대 column degree 4(`col degree hist: {2:17, 3:1, 4:129}`)에서 온 값

생성 파일은 지정한 `llr_matrix.dir`(scratchpad의 `gen/`)에 떨어졌고, 같은 객체의 `llr_matrix.file`
값(`unused.txt`)은 무시됐다. 문서 설명과 일치한다.

---

## ③ round-trip FER 동일성 — 통과 (완전 동일)

②가 생성한 파일을 `use_input_llr_matrix: true`의 입력으로 재지정하고, 같은 seed(0),
같은 `run` 값(max_frame_errors 10, max_frames 128, frames_per_batch 64),
같은 채널 포인트(fixed_error `[300, 1200, 1800, 2400]`)로 재실행했다.

| point | FER (②생성경로) | FER (③파일경로) | BER (②) | BER (③) | avg_iter (②) | avg_iter (③) |
|-------|------------------|------------------|---------|---------|---------------|---------------|
| 300   | 0.000000e+00 | 0.000000e+00 | 0.000000e+00 | 0.000000e+00 | 7.469 | 7.469 |
| 1200  | 1.000000e+00 | 1.000000e+00 | 4.943017e-02 | 4.943017e-02 | 0.000 | 0.000 |
| 1800  | 1.000000e+00 | 1.000000e+00 | 6.706975e-02 | 6.706975e-02 | 0.000 | 0.000 |
| 2400  | 1.000000e+00 | 1.000000e+00 | 8.325984e-02 | 8.325984e-02 | 0.000 | 0.000 |

로그 CSV 12개(`log_iter_*` 4개, `log_iter_hist_*` 4개, `log_fail_*` 4개)를 `diff`로 대조한 결과
전부 `SAME`이었다. `fer_curves.png`도 md5가 같았다(`5194674ef0616d9913cf090b83a4b627`).
FER CSV는 벽시계 시간을 담는 `sec` 열만 달랐고 나머지 6개 열은 완전히 같았다.

**결론: save/load 왕복은 디코딩 결과에 대해 무손실이다.**

---

## ④ `Ideas/vanilla/config.json` 실행 — 통과

registry 경유 확인 (실행하지 않고 함수를 직접 호출, 저장소 무변경):

```
cwd = D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_light
decoder.type -> vanilla
resolved class -> Ideas.vanilla.decoder.VanillaDecoder | MRO: ['VanillaDecoder', 'MinSumDecoder', 'object']
```

실제 실행(입력은 저장소 절대경로, 출력은 scratchpad로 돌린 사본)에서도 summary가 클래스를 찍는다.

```
decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=20
run dir: ...\scratchpad\wc3\Sim_Output_vanilla\260808_142517_vanilla
```

상대경로 해석 기준 실측: **cwd가 아니라 config 파일 위치 기준**이다. cwd를 저장소 루트
(`D:\OneDrive\My_Projects\LDPC_dev`)로 바꾸고 같은 config를 절대경로로 로드해도 결과가 동일했다.

| 항목 | cwd = 2_LDPC_light | cwd = LDPC_dev |
|------|--------------------|----------------|
| H_matrix | `...\Ideas\vanilla\../../Input/H_matrix\example_18x147_z256.qc` (존재) | 동일 |
| llr_matrix | `...\Ideas\vanilla\../../Input/LLR\LLR_MATRIX_HD_1.txt` (존재) | 동일 |
| output.dir | `...\Ideas\vanilla\Sim_Output` | 동일 |

cwd가 영향을 주는 곳은 `Ideas` 패키지 import 하나뿐이다(`python -m` 이 cwd를 `sys.path[0]`에 넣기
때문). `Ideas`가 없는 환경을 흉내내(`sys.modules['Ideas.registry'] = None`) 확인한 fallback 동작도
문서대로였다.

- ㉮ `_resolve_decoder_class('vanilla')` → `LDPC_base.decoder.MinSumDecoder`
- ㉯ `_resolve_decoder_class('foo')` → `ValueError: decoder.type='foo' ... Ideas 패키지를 찾을 수 없음 (2_LDPC_light/에서 실행했는지 확인)`

참고로 커밋된 `Ideas/vanilla/config.json`을 그대로 실행하면 `output.dir`이
`Ideas/vanilla/Sim_Output`으로 잡히는데, 이 경로는 `.gitignore`의 `Sim_Output/`에 걸려서
저장소를 더럽히지 않는다.

---

## ⑤ 커밋된 uniform 파일 재생성 대조 — 바이트 단위 동일

파라미터는 파일명과 내용에서 역산했다: `num_bits=6`(row의 th가 31개, 헤더 num_param=32),
`channel_llr=8`(row 첫 값), `max_iter=30`(row의 iter_end), `dv_max=4`
(`Input/H_matrix/example_18x147_z256.qc`의 col degree hist `{2:17, 3:1, 4:129}`의 최대값).

`LLRMatrix.make_internal_uniform_matrix(num_bits=6, channel_llr=8, max_iter=30, dv_max=4, mode="HD")`
+ `save()`로 scratchpad에 재생성한 뒤 대조했다.

```
$ diff <생성본> 2_LDPC_light/Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt
IDENTICAL(text)
$ md5sum ...
6267445ef48f518f8f9c2e9ffdb7a586  <생성본>
6267445ef48f518f8f9c2e9ffdb7a586  Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt
```

**차이 없음(md5 일치).** 줄바꿈까지 같았다(둘 다 CRLF). 커밋된 파일은 현재 코드의 산출물과
정확히 같다.

추가로 DAO 원본 파일의 왕복도 확인했다.

| 파일 | load→save→load 객체 비교 | 텍스트 동일 |
|------|--------------------------|-------------|
| `LLR_MATRIX_HD_0.txt` (그룹 3개, restart 있음) | 동일 | 아니오 (원본의 행 끝 공백과 마지막 줄바꿈 없음 차이뿐, 의미 동일) |
| `LLR_MATRIX_HD_1.txt` | 동일 | 예 |

---

## ⑥ 오류 경로 메시지 적절성

네 경우 모두 원인을 정확히 짚는 메시지를 낸다. 다만 전달 형태는 전부 스택트레이스이고,
메시지의 줄표(`—`)가 기본 콘솔에서 깨진다(아래 발견 5).

### (ㄱ) `decoder.type`에 미등록 이름 (`"vanila"`)

```
File "...\LDPC_base\run.py", line 274, in _resolve_decoder_class
ValueError: decoder.type='vanila' — Ideas/registry.py 미등록 (등록된 이름: ['vanilla'])
```
등록된 이름 목록까지 보여줘서 오타를 바로 찾을 수 있다. 적절.

### (ㄴ) `decoder.max_iter` 키 삽입 (금지 키)

```
File "...\LDPC_base\run.py", line 179, in load_config
ValueError: decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(또는 internal_quantize.max_iter)이 결정
```
어디서 값이 오는지까지 알려준다. 적절.

### (ㄷ) 존재하지 않는 H-matrix 경로

```
File "...\LDPC_base\run.py", line 288, in setup
FileNotFoundError: D:/.../Input/H_matrix\no_such_matrix.qc 없음 — H-matrix를 먼저 준비할 것
```
해석된 절대경로를 그대로 보여준다. 적절.

### (ㄹ) 알 수 없는 최상위 키 오타 (`"chanels"`)

```
File "...\LDPC_base\run.py", line 91, in _check_keys
ValueError: config [최상위]에 알 수 없는 키 ['chanels'] — 허용 키: ['H_matrix', 'channels', 'decoder', 'log', 'output', 'run', 'seed']
```
허용 키 목록을 보여준다. 적절.

### 추가로 확인한 오류 경로

| 경우 | 결과 | 판정 |
|------|------|------|
| LLR matrix 파일 없음 | `FileNotFoundError: [Errno 2] No such file or directory: 'D:/.../Input/LLR\\LLR_MATRIX_HD_9.txt'` (llr_matrix.py:171 `open()` 원문) | 원인은 알 수 있으나 H-matrix 쪽 안내문과 비대칭 (발견 4) |
| LLR matrix 파일명이 규칙 위반 | `ValueError: ...example_18x147_z256.qc: 파일명에서 모드 판별 불가 — LLR_MATRIX_{HD\|2SD\|3SD}_*.txt 형식이어야 함` | 적절 |
| `internal_quantize.mode: "2SD"` + rber 채널 | `NotImplementedError: 2SD 디코딩 산술 미구현 — 현재 HD만 디코딩 가능 (...)` | 메시지는 적절하나 이미 파일을 쓴 뒤 실패 (발견 6) |
| `decoder.llr_matrix`에 오타 키 (`"flie"`) + `use_input_llr_matrix: false` | 조용히 통과하고 완주 | **발견 2** |
| 같은 오타 + `use_input_llr_matrix: true` | `ValueError: config [decoder.llr_matrix]에 알 수 없는 키 ['flie'] — 허용 키: ['dir', 'file']` | 적절 |
| `internal_quantize.num_bits: 2` (최소값) | 정상 완주 (`ch1+th1`), FER 1.0 | 문제 없음 |

---

## 성능 실측

### 실측 1: 종단 실행 (같은 조건 고정)

전 프레임이 실패하는 포인트(fixed_error 2400)를 골라 **프레임 수 x iteration 수를 고정**했다.
64 프레임 1배치, 로그 전부 끔, seed 0, 같은 H-matrix.

| 경로 | th 개수 | max_iter | 실행 시간 | 프레임x iteration 당 | 배수 |
|------|---------|----------|-----------|----------------------|------|
| uniform 3-bit | 3 | 30 | 6.9 s | 3.59 ms | 1.00x (기준) |
| uniform 6-bit | 31 | 30 | 13.6 s | 7.08 ms | 1.97x |
| uniform 8-bit | 127 | 30 | 39.4 s | 20.52 ms | 5.72x |
| DAO 파일 3-bit (`LLR_MATRIX_HD_1.txt`) | 3 | 20 | 4.8 s | 3.75 ms | 1.05x |

`num_bits` 6 대비 8은 **2.90배**다. 파일 경로 3-bit와 uniform 3-bit는 프레임x iteration 당 비용이
사실상 같아서(3.75 ms 대 3.59 ms), 파일이냐 생성이냐가 아니라 **th 개수만이 비용을 가른다**.

### 실측 2: `_vnu_quantize` 단독 (배열 (64, 256) float32, 200회 평균)

| 구성 | th 개수 | 1회 시간 | 배수 |
|------|---------|----------|------|
| DAO 파일 3-bit `{7,5,3,1}` | 3 | 92.9 us | 1.00x |
| uniform 3-bit | 3 | 93.3 us | 1.00x |
| uniform 6-bit | 31 | 491.6 us | 5.27x |
| uniform 8-bit | 127 | 1871.9 us | 20.1x |
| uniform 10-bit | 511 | 7.08 ms | 76x |
| uniform 12-bit | 2047 | 28.35 ms | 305x |

이 부호는 base edge가 553개라 iteration 당 `_vnu_quantize` 호출이 553회, 30 iteration 배치면
16,590회다. 전체 실행 시간 대비 이 함수의 몫을 추산하면 다음과 같다.

- ㉮ 3-bit: 16,590 x 93 us = 1.55 s / 6.9 s = 약 22%
- ㉯ 6-bit: 16,590 x 492 us = 8.16 s / 13.6 s = 약 60%
- ㉰ 8-bit: 16,590 x 1872 us = 31.1 s / 39.4 s = 약 79%

`num_bits`를 키우면 이 함수가 곧 실행 시간 전체가 된다. 10-bit면 64프레임 1배치가 약 2분,
12-bit면 약 8분으로 추산된다(호출 시간 x 16,590).

---

## 발견 목록

### 1. [MEDIUM] `use_input_llr_matrix: false`가 기본값으로 추적 디렉터리에 파일을 쓴다

- 위치: `2_LDPC_light/LDPC_base/run.py:206-215`, `2_LDPC_light/LDPC_base/run.py:300-303`
- 근거: `generated_dir` 기본값이 `"Input/LLR"`이고 config 위치 기준으로 해석되므로,
  루트 `config.json`으로 실행하면 `2_LDPC_light/Input/LLR/`에 생성된다.
  이 경로는 무시 대상이 아니다.
  ```
  $ git check-ignore -v 2_LDPC_light/Sim_Output/x.txt 2_LDPC_light/Input/LLR/foo.txt
  .gitignore:45:Sim_Output/   2_LDPC_light/Sim_Output/x.txt
  ```
  (`Input/LLR/foo.txt`는 출력에 없다 = 무시되지 않는다)
- 영향: `(num_bits, channel_llr, max_iter, mode)` 조합마다 새 파일이 생겨 `git status`가
  매번 더러워진다. 실제로 `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`가 그렇게 생긴
  산출물이며 커밋까지 됐다(⑤에서 재생성본과 md5 일치 확인).
- 덧붙여 `save()`가 텍스트 모드로 쓰기 때문에 줄바꿈이 플랫폼을 탄다. 커밋된 파일은 CRLF이고
  저장소에 `.gitattributes`가 없어서, Linux에서 같은 파라미터로 재생성하면 LF가 나와
  추적 파일이 수정된 것으로 보인다.
- 제안: 생성 파일 기본 위치를 `Sim_Output/` 아래나 별도의 무시 대상 폴더로 두거나,
  `Input/LLR/*uniform*`을 `.gitignore`에 넣는다.

### 2. [MEDIUM] `use_input_llr_matrix: false`일 때 `decoder.llr_matrix`의 오타 키가 무검사 통과

- 위치: `2_LDPC_light/LDPC_base/run.py:187-208`
- 근거: `_path_pair()`(그 안에서 `_check_keys(section, d, {"dir", "file"})`)는 true 분기에서만
  호출된다. false 분기는 `decoder_config.get("llr_matrix")`를 dict로 확인하고 `.get("dir")`만 꺼낸다.
  ```
  # use_input_llr_matrix=false, decoder.llr_matrix = {"dir": "gen", "flie": "x.txt"}
  통과함. decoder.llr_matrix = {'dir': 'gen', 'flie': 'x.txt'}
  생성 경로 = ...\scratchpad\wc3\gen\LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt
  # 같은 오타 + use_input_llr_matrix=true
  ValueError: config [decoder.llr_matrix]에 알 수 없는 키 ['flie'] — 허용 키: ['dir', 'file']
  ```
- 영향: 같은 오타가 토글 값에 따라 잡히기도 하고 안 잡히기도 한다. `dir`을 `dri`로 잘못 쓰면
  경고 없이 기본값 `Input/LLR`로 떨어져 발견 1의 오염이 조용히 일어난다.
- 제안: false 분기에서도 `_check_keys("decoder.llr_matrix", ..., {"dir", "file"})`를 부른다.

### 3. [MEDIUM] `LLRMatrix.save()`가 floor flag를 항상 -1로 덮어쓴다

- 위치: `2_LDPC_light/LDPC_base/llr_matrix.py:254-256` (저장), `llr_matrix.py:86-92` (`__init__`)
- 근거: `__init__`이 row 튜플의 다섯째 값(floor)을 어디에도 보관하지 않고, `save()`의 꼬리가
  `[csw, iter_start, iter_end, -1]`로 상수 `-1`을 쓴다. floor를 1로 바꾼 파일로 왕복시킨 실측:
  ```
  원본   row 꼬리 4개: ['-1', '1', '1', '1']    ['-1', '2', '20', '1']
  재저장 row 꼬리 4개: ['-1', '1', '1', '-1']   ['-1', '2', '20', '-1']
  ```
- 영향: 현재 저장소의 DAO 파일 3개는 모두 floor가 -1이고 디코더가 이 값을 쓰지 않아서
  지금은 드러나지 않는다. 다만 외부에서 floor를 쓰는 파일을 받아 `save()`를 거치면
  파일 포맷 호환 요구(DAO 포맷 무변경)를 조용히 깬다.
- 제안: floor를 `__init__`에서 보관하고 `save()`가 그대로 되쓴다.

### 4. [LOW] LLR matrix 파일 부재 메시지가 H-matrix 쪽과 비대칭

- 위치: `2_LDPC_light/LDPC_base/run.py:287-288` (H-matrix 안내문) 대 `llr_matrix.py:171` (`open()` 원문)
- 근거:
  ```
  FileNotFoundError: D:/.../Input/H_matrix\no_such_matrix.qc 없음 — H-matrix를 먼저 준비할 것
  FileNotFoundError: [Errno 2] No such file or directory: 'D:/.../Input/LLR\\LLR_MATRIX_HD_9.txt'
  ```
- 영향: 원인은 알 수 있으나 안내가 없다. 같은 종류의 실수인데 안내 수준이 다르다.

### 5. [LOW] 오류 메시지의 줄표(`—`)가 기본 Windows 콘솔에서 `\u2014`로 깨진다

- 위치: `2_LDPC_light/LDPC_base/run.py`(40곳), `llr_matrix.py`(13곳), `decoder.py`(25곳)의 메시지 문자열
- 근거: 이 환경의 stderr 인코딩은 cp949이며, cp949에 없는 `—`는 traceback 출력의
  `backslashreplace` 처리로 이스케이프된다.
  ```
  ValueError: config [최상위]에 알 수 없는 키 ['chanels'] \u2014 허용 키: [...]
  ```
  `PYTHONIOENCODING=utf-8`을 주면 정상 출력된다.
- 영향: 한글은 cp949로 잘 나오는데 구분자만 깨져서 읽기가 나빠진다. 프로젝트 문장 규칙이
  줄표를 접속어나 나열 기호로 쓰지 말라고 정한 것과도 어긋난다(코드 주석과 문서 공통 규칙).
- 제안: 메시지의 `—`를 콜론이나 괄호로 바꾼다.

### 6. [LOW] 균일 매트릭스 파일을 쓴 뒤에야 HD 전용 검사에 걸린다

- 위치: `2_LDPC_light/LDPC_base/run.py:293-303`(생성과 저장) 대 `LDPC_base/decoder.py:372`(모드 검사)
- 근거: `internal_quantize.mode: "2SD"` + rber 채널로 실행하면 파일이 먼저 저장되고
  요약까지 출력한 뒤 첫 배치에서 실패한다.
  ```
  generated LLR matrix: ...\gen\LLR_MATRIX_2SD_uniform_6bit_ch8_iter30.txt
  ...
  == channel=rber (rber) ==
  NotImplementedError: 2SD 디코딩 산술 미구현 — 현재 HD만 디코딩 가능 (...)
  ```
- 영향: 쓸 수 없는 파일이 남는다. 기본 생성 위치가 `Input/LLR`이므로(발견 1) 저장소에
  고아 파일이 쌓인다. 채널 모드 호환은 `run_experiment` 진입 때 전 채널을 미리 검사하는데
  (`run.py:378-379`), 디코딩 산술 지원 여부는 그 사전 검사에 없다.
- 제안: `setup()`에서 디코더 구성 직후에 모드 지원 여부를 확인하거나, 사전 검사에 추가한다.

### 7. [LOW] `internal_quantize.num_bits`에 상한이 없어 실질적 정지 상태를 만들 수 있다

- 위치: `2_LDPC_light/LDPC_base/run.py:195-197` (`_check_int(..., "num_bits", ..., 2)`),
  `2_LDPC_light/LDPC_base/decoder.py:156-157` (`for k in range(len(edge_mag) - 2, -1, -1)`)
- 근거: th 개수가 `2^(num_bits-1)-1`로 늘고 `_vnu_quantize`의 파이썬 루프가 그만큼 돈다.
  단독 측정으로 10-bit는 7.08 ms/호출, 12-bit는 28.35 ms/호출이며, 이 부호에서 64프레임
  30 iteration 배치는 호출이 16,590회라 각각 약 118초와 약 470초로 추산된다.
  16-bit면 th가 32,767개라 배치 하나가 시간 단위로 늘어난다.
- 영향: 진행 표시가 배치 끝에서만 나오므로 사용자에게는 멈춘 것처럼 보인다.
- 제안: `num_bits` 상한을 두거나(예: 8), th 비교를 `np.searchsorted`로 바꿔 루프를 없앤다.

### 통과 확인 (문제 없음)

- ㉮ 파일 경로와 균일 양자화 경로 모두 완주하며 산출물 구성이 완전하다 (①, ②)
- ㉯ 생성 후 저장, 재로드 왕복이 FER, BER, 수렴 iteration, 로그 CSV 12개, PNG까지 완전히 같다 (③)
- ㉰ registry 경유가 실제로 타며 상대경로는 config 파일 위치 기준으로 일관되게 해석된다 (④)
- ㉱ 커밋된 uniform 파일이 현재 코드 산출물과 바이트 단위로 같다 (⑤)
- ㉲ 오류 네 갈래 모두 원인을 짚는 메시지를 낸다 (⑥)
- ㉳ `num_bits` 최소값 2도 정상 동작한다 (`ch1+th1`)

---

## git status 최종 확인

```
$ git status --short
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

실행 전과 동일하다. `?? _pm/tasks/`는 이번 리뷰의 다른 워커 보고서들이다.

`2_LDPC_light/Input/LLR/`는 파일 3개 그대로이고 갱신 시각도 그대로였다
(`LLR_MATRIX_HD_0.txt` 8/6 18:30, `LLR_MATRIX_HD_1.txt` 8/6 22:11,
`LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` 8/8 13:59 = 이번 실행 시작 14:21보다 앞).
저장소의 `Sim_Output/`과 `Ideas/vanilla/Sim_Output/`도 최신 폴더가 각각 14:00과 13:28로
이번 실행 이전 것이다. **저장소 오염 없음.**
