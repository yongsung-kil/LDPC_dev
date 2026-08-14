# 검증팀 c 워커 1 — TD-1, TD-2 독립 재확인

> 작성: 2026-08-08 15:10:25
> 대상: Round 2 발견 TD-1(HIGH), TD-2(HIGH)
> 방식: 문서와 코드 직접 확인 + 시뮬레이터 실행 재현 + 반증 실험

---

## 1. 가설 H1 (TD-1) — 기본 config 실행이 FER 1.0

### 1.1 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E1-1 | 배포 기본 config가 `use_input_llr_matrix: true`이고 `decoder.llr_matrix.file = LLR_MATRIX_HD_1.txt`, 채널은 `fixed_error [200, 300]` | **확인됨** | 작업 트리 `config.json:25`(`"use_input_llr_matrix": true`), `:28`(`"file": "LLR_MATRIX_HD_1.txt"`), `:61-62`(`"type": "fixed_error"`, `"points": [200, 300]`). 커밋본은 `git show HEAD:2_LDPC_light/config.json`으로 확인 |
| E1-1b | 미커밋 수정이 판정에 영향을 주는가 | **영향 없음** | `git diff -- 2_LDPC_light/config.json` 결과가 `decoder._desc` 배열 첫 문자열을 두 줄로 나눈 1건뿐이다. `_desc`는 `run.py:83-85 _visible()`이 검사에서 제외하는 설명용 키다. 기능 키는 커밋본과 작업 트리가 동일하므로 "배포 기본"을 어느 쪽으로 읽어도 같은 실험이 된다 |
| E1-2 | `LLR_MATRIX_HD_1.txt`의 dv=2 구간 채널 LLR 값이 28이다 | **확인됨** | 파일 `Input/LLR/LLR_MATRIX_HD_1.txt:19`(row 1)과 `:21`(row 2)의 13번째 값이 `28`이다. 헤더 `:1` num_param=4, `:3` num_dv=4, `:5-6` dv_from=dv_to=[11,4,3,2]이므로 row를 (4,4)로 재구성하면 4번째 dv 구간(dv=2)의 첫 값(ch)이 13번째 자리다. `LLRMatrix.load()` 실호출 결과 `row_ch = [[1,10,13,28],[5,10,13,28]]` |
| E1-2b | `LLR_MATRIX_HD_0.txt`도 같은 위반이 있다 | **확인됨(단서 있음)** | `Input/LLR/LLR_MATRIX_HD_0.txt:20`(row 1)과 `:24`(row 3)의 13번째 값이 `28`이다. `row_ch = [[1,10,13,28],[-1,-1,-1,-1],[5,10,13,28]]`. 단서: HD_0은 iteration 2가 restart row(ch=-1, th=-1)라 그 한 iteration에서는 dv=2 비트도 반전된다. 나머지 iteration에서는 HD_1과 똑같이 고정된다 |
| E1-3 | `sum_t >= ch − dv·max(edge_mag)` 하한이 코드에서 성립한다 | **확인됨** | 아래 §1.2 재유도 참조. 계측 실행에서 dv=2 구간의 `min(sum_t) = 14.0`으로 하한과 정확히 일치했다 |
| E1-3b | Round 2 식의 `7`이 무엇인가 | **edge_mag 최댓값** | `7 = edge_mag[0] = max(edge_mag)`다. th 최댓값이 아니다(같은 파일의 th 최댓값은 31). 계측 실행에서 관측한 `max |C2V| = 7.0` |
| E1-3c | `2`가 dv인가 | **확인됨** | dv=2 구간의 column block은 실제 column degree가 2다(`col_deg` 히스토그램 `{2:17, 3:1, 4:129}`). `_process_column`의 edge 루프 횟수가 곧 column degree다 |
| E1-3d | 부호 판정이 `sum_t`로 비트 반전을 결정한다 | **확인됨** | `decoder.py:283` `flip = self._vn_decide(sum_t)`, `decoder.py:142` `return sum_t <= 0`, `decoder.py:284` `bit_err = state.read_bit[:, col, :] ^ flip` |
| E1-4 | 기본 config 그대로 실행하면 FER 1.0 | **확인됨** | 원본 파라미터 그대로 실행. `fixed_error point=200: FER=1.000e+00 [64/64]`, `point=300: FER=1.000e+00 [64/64]` (§3) |
| E1-4b | dv=2 비트 에러가 iteration 내내 불변 | **확인됨** | `log_iter_fixed_error_p200.csv`의 `bit_err_dv2_mean` 열이 iteration 1부터 20까지 전부 `22.672`다. p300은 전부 `34.016`. 같은 표에서 dv4는 187.656 → 0.875, dv3은 0.984 → 0.016으로 감소한다 |
| E1-4c | Round 2가 인용한 실측값 `34.500` | **미확인(값 불일치, 결론 영향 없음)** | Round 2 워커 1은 `worker_d_1.md:150-155`에서 8프레임 실행으로 34.500을 얻었다. 기본 config(64프레임, p300)로는 34.016이다. 프레임 표본이 달라 생긴 차이이며, "iteration 내내 불변"이라는 성질 자체는 양쪽 모두에서 성립한다 |
| E1-5 | 디코더 결함이 아니라 데이터와 부호의 정합 문제 | **확인됨** | 반증 실험 2건이 모두 디코더의 건전성을 지지한다(§1.3) |
| E1-6 | `_pm/TODO.md`가 이 데이터 문제를 미착수 항목으로 등록하고 있다 | **확인됨(줄 번호 정정)** | 작업 트리 `_pm/TODO.md:19-21`이다(Round 2 인용은 `:18-21`). 원문: `- [ ] LLR matrix 최적화 시 dv range 상한 고려 (사용자 지시 2026-08-07)` / `  - 반전 가능 조건 \`ch ≤ 7·dv\` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)를 최적화 탐색 범위에 반영` / `  - 현 토이 파일의 dv=2 ch=28 위반은 파라미터 수정 시점에 함께 처리 (벤더 참고값: dv=2 ch=10)`. 커밋본에서는 같은 내용이 `:16-18`에 있다(작업 트리가 앞에 3줄을 추가했다) |
| E1-6b | "기본 config가 그 파일을 가리킨다는 사실은 어디에도 기록돼 있지 않다" | **반박됨** | `_pm/done/20260806_review/r4_round2_lv1_fix_review/report.md:41`이 기록하고 있다. 원문: `스모크: \`python -m LDPC_base.run config.json\` 정상 (FER=1.0은 토이 LLR 파일의 dv=2 상한 위반 특성 — 파라미터는 사용자가 추후 수정, TODO "dv range 상한" 항목).` 이 파일은 `2_LDPC_light/` 안에 있고 `git ls-files`로 추적 중이다 |
| E1-6c | 현행 사용자 문서(README.md, docs/, config.json `_desc`)에는 경고가 없다 | **확인됨** | `README.md`, `docs/`, `config.json` 전수 grep 결과 "기본 config로 돌리면 FER 1.0" 취지의 서술 0건이다. `FER` 문자열은 스키마 설명과 출력 파일 이름 설명으로만 나온다. `Ideas/vanilla/Sim_Output/*/summary.txt`에 `FER=1.000e+00` 수치가 남아 있으나 이는 경고가 아니라 실행 산출물이다 |

### 1.2 하한식 독립 재유도 (E1-3)

Round 2의 식을 쓰지 않고 코드에서 다시 세웠다.

- ㉮ 채널 항: `decoder.py:271`이 `sum_t`를 `cur_ch[:, dv_idx]`로 초기화한다. 부호는 항상 +다(`decoder.py:269` 주석의 flip 도메인 규약).
- ㉯ 메시지 항: `decoder.py:275-281`이 그 column의 edge마다 `vnu_in`을 더한다. 더하는 횟수는 `code.col_edges[col]`의 길이, 곧 column degree다.
- ㉰ 메시지 크기의 상한: `_c2v_reconstruct`(`decoder.py:135-137`)가 돌려주는 값의 크기는 `min1` 또는 `min2`다. 두 배열의 초기값은 `RESET = edge_mag[0]`(`decoder.py:208, 219-220`)이고, 갱신값은 `_cnu_update`가 받는 `new_mag = np.abs(vnu_out)`(`decoder.py:296`)이다. `vnu_out`은 `_vnu_quantize`(`decoder.py:144-163`)의 산출물이라 크기가 `edge_mag`의 원소 중 하나다. 따라서 `|vnu_in| <= max(edge_mag)`가 모든 iteration에서 성립한다.
- ㉱ 결론: `sum_t >= ch − (column degree)·max(edge_mag)`.

파일 매트릭스는 `edge_mag`를 지정하지 않으므로 `llr_matrix.py:72`가 `[7, 5, 3, 1]`을 채운다. 곧 `max(edge_mag) = 7`이다.
dv=2 구간에 `ch = 28`, column degree = 2를 넣으면 `sum_t >= 28 − 14 = 14 > 0`이다.
`_vn_decide`는 `sum_t <= 0`일 때만 반전하므로 dv=2 column의 비트는 어떤 iteration에서도 반전되지 않는다.

계측 실행(`MinSumDecoder` 자식 클래스로 값만 기록, 저장소 코드 무수정)의 출력:

```
edge_mag        : [7.0, 5.0, 3.0, 1.0] -> max = 7.0
row_th max      : 31.0
관측 max |C2V|  : 7.0
    dv4: ch= 10.0  min(sum_t)=   -18.0  하한 ch-dv*max(edge_mag)= -18.0  누적 flip=56533
    dv3: ch= 13.0  min(sum_t)=    -8.0  하한 ch-dv*max(edge_mag)=  -8.0  누적 flip=477
    dv2: ch= 28.0  min(sum_t)=    14.0  하한 ch-dv*max(edge_mag)=  14.0  누적 flip=0
success: 0 / 16
```

세 dv 구간 모두 관측 최솟값이 하한과 정확히 일치했다. 하한은 느슨한 부등식이 아니라 실제로 도달하는 값이다.

Round 2의 대수 유도는 옳다. 다만 서술에서 `7`의 출처를 명확히 할 필요가 있다. `7`은 VNU 출력 레벨 집합의 최댓값(`edge_mag[0]`, RESET 값과 같다)이고, 임계값(th) 최댓값 31과는 무관하다.

비트 비율도 확인했다. dv=2 column block은 17개이므로 17 × 256 = 4352 bit, 전체 147 × 256 = 37632 bit의 11.565%다. Round 2의 "11.6%"와 일치한다.

한 가지 정밀화가 필요하다. FER 1.0은 항등식이 아니라 실측 결과다. dv=2 구간에 에러가 한 비트도 들어가지 않은 프레임은 성공할 수 있다. n_err=200에서 그 확률은 대략 `(1 − 0.11565)^200 ≈ 2e-11`이라 실행 규모에서는 관측되지 않는다. "FER 1.0으로 수렴한다"는 서술은 이 조건에서 정확하다.

### 1.3 원인 판정 반증 시도 (E1-5)

같은 디코더 코드를 그대로 두고 데이터만 바꾸는 두 실험을 했다.

- ㉮ **dv=2의 ch만 28에서 10으로 낮춘 매트릭스** (TODO가 적은 벤더 참고값). 나머지 15개 값과 헤더는 원본 그대로다.
  결과: p200 FER 5.156e-01(33/64 실패), p300 FER 9.062e-01(58/64 실패). `bit_err_dv2_mean`이 21.219 → 1.848로 감소한다.
- ㉯ **균일 6-bit(32레벨) 매트릭스**. `channel_llr=8`, `top_level=31`이라 하한이 `8 − 2·31 = −54`다.
  결과: p200과 p300 모두 FER 0.000e+00, 256/256 프레임 성공.

디코더 코드를 한 줄도 바꾸지 않고 데이터만 바꾸면 복호가 정상 동작한다. 따라서 원인은 디코더 알고리즘이 아니라 동봉 LLR 매트릭스와 이 H-matrix의 dv 구성이 맞지 않는 데 있다. Round 2의 원인 판정은 옳다.

### 1.4 H1 최종 판정: **부분 확인**

확인된 부분:
- ㉮ 기본 config가 `LLR_MATRIX_HD_1.txt`를 가리킨다는 사실(커밋본과 작업 트리 모두)
- ㉯ 그 파일의 dv=2 구간 ch가 28이고 반전 상한 `7·dv = 14`를 넘는다는 사실
- ㉰ 대수 하한식과 그 코드 근거(하한이 실측으로 정확히 도달)
- ㉱ 4352 bit(11.6%) 고정, 기본 실행 FER 1.0, dv=2 에러의 iteration 불변성
- ㉲ 디코더 결함이 아니라 데이터와 부호의 정합 문제라는 원인 판정
- ㉳ `_pm/TODO.md`에 미착수 항목으로 등록돼 있다는 사실

미달인 부분:
- ㉮ **"기록돼 있지 않다"는 부수 주장은 반박됐다.** `_pm/done/20260806_review/r4_round2_lv1_fix_review/report.md:41`이 기본 config 실행이 FER=1.0을 내는 사실과 그 원인을 이미 적고 있다. 다만 그 기록은 완료된 리뷰의 보고서 안에 있고, 실행자가 읽는 문서(README.md, docs/, config.json `_desc`)에는 없다. 발견을 살리려면 주장을 "실행자가 읽는 문서에 경고가 없다"로 좁혀야 한다.
- ㉯ 인용 수치 `bit_err_dv2_mean = 34.500`은 기본 config 실행값이 아니라 8프레임 실행값이다. 기본 config는 p200에서 22.672, p300에서 34.016이다.
- ㉰ `_pm/TODO.md` 줄 번호는 작업 트리 기준 `:19-21`이다(인용은 `:18-21`).

현상과 인과와 원인 판정이라는 발견의 본체는 전부 확인됐다. 심각도 HIGH 유지가 타당하다.

---

## 2. 가설 H2 (TD-2) — README의 "3-bit 전용" 서술

### 2.1 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E2-1 | `README.md:162`에 그 서술이 그 위치에 있다 | **확인됨** | 원문 그대로: `- VNU 출력 레벨 {7,5,3,1} 고정 — 3-bit 전용 (사용자 확정: LLR은 3-bit만 사용)` |
| E2-1b | 앞뒤 문맥에 서술 범위를 한정하는 문구가 있는가 | **없음** | 소속 절은 `README.md:160` `## 남은 근사/제한`이다. 같은 절의 나머지 항목(`:163-167`)은 2SD/3SD 미구현, 파이프라인 지연 미재현 등 시뮬레이터 전체의 제한을 열거한다. "파일 매트릭스 경로에서는"이나 "3-bit 모드에서는" 같은 한정어가 문장 안에도 절 머리에도 없다. false positive가 아니다 |
| E2-2 | `decoder.py:144-163`의 레벨 수가 `len(edge_mag)`로 결정된다 | **확인됨** | `decoder.py:155` `mag = np.full_like(mag_in, edge_mag[-1])`, `:156` `for k in range(len(edge_mag) - 2, -1, -1)`, `:157` `mag = np.where(mag_in >= th[:, k, None], edge_mag[k], mag)`. `edge_mag`는 `decoder.py:118`에서 `llr_matrix.edge_mag`를 그대로 받는다 |
| E2-2b | `decoder.py`에 `{7,5,3,1}` 하드코딩이 남아 있는가 | **없음(주석만)** | 전수 grep 결과 `decoder.py:150`의 docstring 한 곳뿐이고 로직에는 없다. 실제 하드코딩은 `llr_matrix.py:72` `edge_mag = [7, 5, 3, 1]`이며, 이는 `edge_mag`가 지정되지 않은 파일(사람이 만든 3-bit DAO 파일)에만 적용된다(`:67-72`). uniform 표시가 있는 파일과 내부 합성은 `llr_matrix.py:170, 202`와 `:225`가 `uniform_edge_mag(top_level)`로 임의 길이 레벨을 채운다 |
| E2-3 | 균일 6-bit(32레벨) 매트릭스로 복호가 성공한다 | **확인됨** | 두 경로 모두 실행했다. ㉮ 추적 파일 `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` 로드: p200과 p300 모두 **256/256 프레임 성공(FER 0.000e+00, BER 0.000e+00)**. ㉯ `use_input_llr_matrix: false`로 `make_internal_uniform_matrix` 생성 후 로드: 동일하게 256/256 성공. 생성 파일은 추적본과 바이트 완전 일치(301 byte). `edge_mag` 길이는 32(`[31, 30, ..., 1, 0]`) |
| E2-4 | 같은 README `:66-71`이 n-bit를 설명해 자기모순이다 | **확인됨** | `README.md:66-71` 원문: `false면 **균일 n-bit 양자화 매트릭스를 DAO 포맷 파일로 생성해 저장한 뒤 그 / 파일을 로드**해 디코딩한다 — \`internal_quantize\`의 num_bits(메시지 양자화 / bit 수, sign 포함), channel_llr(채널 LLR magnitude, 전 dv 공통), max_iter, / mode(기본 HD)로 파일을 만들며, llr_matrix 키는 있어도 무시된다 (플래그만 / 바꿔 토글 가능). 생성 파일명의 **uniform은 사람이 만든 파일이 아니라는 표시** / (예: LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt)`. 같은 문서가 `:70-71`에서 6-bit 예시 파일명을 들면서 `:162`에서는 3-bit 전용이라 못 박는다 |

### 2.2 보강 관찰

`README.md:162`의 서술이 참인 범위가 있다. 사람이 만든 DAO 3-bit 파일을 로드하는 경로에서는 `llr_matrix.py:67-72`가 th 3개가 아닌 구성을 거부하고 `edge_mag`를 `{7,5,3,1}`로 고정한다. 서술이 거짓이 되는 것은 그 범위를 벗어난 두 경로다.

- ㉮ 파일명에 `uniform`이 있는 파일 로드(`llr_matrix.py:170, 202`)
- ㉯ `use_input_llr_matrix: false`의 내부 합성(`llr_matrix.py:225`, `run.py:294-304`)

두 경로 모두 저장소에 실물이 있고(추적 파일 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`), 기본 config에 `internal_quantize` 블록이 준비돼 있으며, 실행하면 32레벨로 복호가 성공한다. 따라서 "고정", "전용"이라는 무조건 서술은 사실과 다르다.

같은 서술이 `docs/차이.md:25`(#9)에도 있다. 이 건은 Round 2가 TD-3으로 따로 분리했으므로 여기서는 위치만 적어 둔다.

### 2.3 H2 최종 판정: **확인됨**

세 조건이 모두 성립한다.
- ㉮ 문제의 서술이 지목된 위치에 있고 범위 한정 문구가 없다
- ㉯ 코드는 레벨 수를 `len(edge_mag)`로 결정하며 로직에 하드코딩이 없다
- ㉰ 32레벨 복호가 실제로 성공한다(256/256, 두 포인트 모두)
- ㉱ 같은 문서 `:66-71`과 정면으로 충돌한다

심각도 HIGH 유지가 타당하다. 문서 한 줄이 시뮬레이터의 실사용 가능 범위를 실제보다 좁게 알려 준다.

---

## 3. 실행 재현

### 3.1 사용한 명령

`2_LDPC_light/`에서 실행했다(`README.md:23-28`, `run.py:9`가 안내하는 실행 루트).

```
python -m LDPC_base.run <scratchpad>/config_default_full.json
python -m LDPC_base.run <scratchpad>/config_dv2ch10.json
python -m LDPC_base.run <scratchpad>/config_uniform6bit_file.json
python -m LDPC_base.run <scratchpad>/config_uniform6bit_gen.json
python -m LDPC_base.run <scratchpad>/config_hd0.json
```

`<scratchpad>` = `C:\Users\yongs\AppData\Local\Temp\claude\d--OneDrive-My-Projects-LDPC-dev\96aaaa04-61b8-4b90-ac92-52ca7348de60\scratchpad\wc1`

### 3.2 config 사본 내용 요약

기준 사본 `config_default_full.json`은 저장소 `config.json`과 **모든 실험 파라미터가 같다**. 값을 줄이지 않았다.

- `run`: `max_frame_errors=10`, `max_frames=256`, `frames_per_batch=64`, `stop_below_fer=null` (원본 그대로)
- `channels`: `fixed_error [200, 300]` (원본 그대로)
- `seed`: 0 (원본 그대로)
- `log`: 7개 항목 전부 true (원본 그대로)
- 바꾼 것은 경로뿐이다. `H_matrix.dir`와 `decoder.llr_matrix.dir`를 저장소 절대경로로, `output.dir`을 scratchpad로 돌렸다. 프레임 수와 iteration 수를 줄이지 않았으므로 FER 판정 왜곡 요인이 없다.

파생 사본은 기준 사본에서 한 항목씩만 바꿨다.

| 사본 | 바꾼 항목 |
|------|----------|
| `config_dv2ch10.json` | `llr_matrix`를 scratchpad의 `LLR_MATRIX_HD_1_dv2ch10.txt`로 (원본에서 13번째 값 28 → 10 한 자리만 수정) |
| `config_uniform6bit_file.json` | `llr_matrix.file`을 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`로 |
| `config_uniform6bit_gen.json` | `use_input_llr_matrix: false`, `internal_quantize.max_iter: 30`, `llr_matrix.dir`을 scratchpad로 (생성물이 저장소에 쌓이지 않게) |
| `config_hd0.json` | `llr_matrix.file`을 `LLR_MATRIX_HD_0.txt`로 |

### 3.3 관측 수치 원문

**기본 config (LLR_MATRIX_HD_1.txt)**

```
LLRMatrix LLR_MATRIX_HD_1.txt: mode=HD (ch1+th3), dv=[11, 4, 3, 2]~[11, 4, 3, 2], max_iter=20, groups: g1[1~1]x1, g2[2~20]x1
decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=20
== channel=fixed_error (fixed_error) ==
  frames=    64 errors=  64 FER=1.000e+00 BER=6.261e-04 avg_decode_success_iteration=0.00 (14.9 f/s)
  frames=    64 errors=  64 FER=1.000e+00 BER=1.041e-03 avg_decode_success_iteration=0.00 (14.8 f/s)
```

`log_iter_fixed_error_p200.csv` (iteration별, 발췌)

```
iter,active_frames,csw_mean,bit_err_mean,bit_err_dv11_mean,bit_err_dv4_mean,bit_err_dv3_mean,bit_err_dv2_mean
1,64,729.17,211.31,0.000,187.656,0.984,22.672
2,64,383.69,71.16,0.000,47.828,0.656,22.672
5,64,72.03,23.73,0.000,1.047,0.016,22.672
10,64,69.22,23.58,0.000,0.891,0.016,22.672
20,64,69.20,23.56,0.000,0.875,0.016,22.672
```

p300은 같은 열이 iteration 1부터 20까지 전부 `34.016`이다.

`log_fail_fixed_error_p200.csv` (실패 프레임 상세, 앞 5줄)

```
frame,final_err_bits,final_csw,err_dv11,err_dv4,err_dv3,err_dv2
0,25,82,0,0,0,25
1,24,85,0,0,0,24
2,34,95,0,3,0,31
3,15,48,0,0,0,15
4,30,88,0,2,0,28
```

잔여 에러가 거의 전부 dv=2 열에 몰려 있다.

**dv=2의 ch만 10으로 낮춘 매트릭스 (반증 실험 ㉮)**

```
param,fer,post_fec_ber,frames,errors,avg_decode_success_iteration,sec
200,5.156250e-01,2.823395e-05,64,33,5.677,3.0
300,9.062500e-01,1.100294e-04,64,58,12.333,4.2
```

iteration별 `bit_err_dv2_mean`: 21.219 → 15.188 → 7.234 → 3.375 → 1.746 → ... → 1.848 (감소)

**균일 6-bit 32레벨 (반증 실험 ㉯, 파일 로드와 내부 합성이 동일 결과)**

```
LLRMatrix LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt: mode=HD (ch1+th31), dv=[1]~[4], max_iter=30, groups: g1[1~30]x1
  frames=   256 errors=   0 FER=0.000e+00 BER=0.000e+00 avg_decode_success_iteration=5.10 (25.9 f/s)
  frames=   256 errors=   0 FER=0.000e+00 BER=0.000e+00 avg_decode_success_iteration=7.56 (17.6 f/s)
```

프레임 복호 성공률: p200 256/256 (100%), p300 256/256 (100%).

**LLR_MATRIX_HD_0.txt (참고)**

```
LLRMatrix LLR_MATRIX_HD_0.txt: mode=HD (ch1+th3), dv=..., max_iter=5, groups: g1[1~1]x1, g2[2~2]Rx1, g3[3~5]x1
  frames=    64 errors=  64 FER=1.000e+00 BER=1.521e-03 avg_decode_success_iteration=0.00 (57.5 f/s)
  frames=    64 errors=  64 FER=1.000e+00 BER=4.590e-03 avg_decode_success_iteration=0.00 (57.2 f/s)
```

```
iter,active_frames,csw_mean,bit_err_mean,bit_err_dv11_mean,bit_err_dv4_mean,bit_err_dv3_mean,bit_err_dv2_mean
1,64,729.17,211.31,0.000,187.656,0.984,22.672
2,64,2303.61,23423.22,0.000,20041.625,128.781,3252.812
3,64,1740.08,1268.92,0.000,1245.094,1.156,22.672
4,64,634.03,133.94,0.000,110.125,1.141,22.672
5,64,303.06,57.25,0.000,34.141,0.438,22.672
```

restart iteration 2에서만 dv=2 에러가 움직이고, iteration 3, 4, 5에서는 HD_1과 똑같은 22.672로 고정된다. HD_0도 같은 위반을 안고 있음이 실측으로 확인된다.

---

## 4. 저장소 오염 확인

```
$ git status --short
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

작업 시작 시점의 정상 상태 3줄과 동일하다. 추가 확인:

- `2_LDPC_light/Input/LLR/`: `LLR_MATRIX_HD_0.txt`, `LLR_MATRIX_HD_1.txt`, `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` 3개 그대로(생성물 없음)
- `2_LDPC_light/Sim_Output/`: 최신 폴더가 `260808_140006_fixed_error`(이 검증 시작 전 것). 새 폴더 없음
- `2_LDPC_light/Ideas/vanilla/Sim_Output/`: 최신이 `260808_132800_vanilla`. 새 폴더 없음

모든 config 사본, 생성 매트릭스, 실행 산출물은 scratchpad에만 있다.
