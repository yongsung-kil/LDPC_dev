# Round 2 / 팀 B / 워커 2 — config 스키마 검증부와 실제 소비부의 일치

작성: 2026-08-08 14:24:58

## 확인 범위

- 읽은 코드: `LDPC_base/run.py`(전체), `LDPC_base/sim.py`, `LDPC_base/channel.py`,
  `LDPC_base/encoder.py`, `LDPC_base/llr_matrix.py`, `LDPC_base/decoder.py`(`_vnu_quantize` 주변),
  `LDPC_base/pcm.py`(`summary`), `Ideas/registry.py`, `Ideas/vanilla/decoder.py`
- 읽은 설정과 문서: `config.json`, `Ideas/vanilla/config.json`, `README.md`(스키마 절)
- 전수 대조 방법: `grep -rn "config\[|config.get|_config\[|_config.get|.setdefault" --include=*.py`로
  설정 소비 지점을 모두 뽑아 키맵 상수와 1:1 대조
- 시뮬레이터 실행은 하지 않았다. 난수 스트림 파생과 배치 분할의 영향은 프로젝트 코드를
  건드리지 않는 별도 스크립트(scratchpad)로 numpy 동작만 확인했다
- `git diff -- 2_LDPC_light/config.json`으로 미커밋 1건 확인

## 키맵 대조표

키맵 상수는 `run.py:65~80`에 6개(+채널 3종)가 있다. 소비 위치는 전부 `run.py` 기준이며
다른 파일이면 파일명을 적었다.

### `_TOP_KEYS` (run.py:65)

| 키 | 검증 | 소비 위치 | 판정 |
|----|------|----------|------|
| H_matrix | `_path_pair` 174 (dir/file 필수, 경로 결합) | setup 286-289 | 소비됨 |
| decoder | 177-219 | setup 290-306 | 소비됨 |
| channels | 247-254 | run_experiment 378/383/397, report 523, 요약 313-315 | 소비됨 |
| run | 229-239 | run_experiment 368-373, 요약 317-328 | 소비됨 |
| output | 223-227 | report 521-533 | 소비됨 |
| seed | 221 (int, 0 이상) | run_experiment 374, 요약 324 | 소비됨 |
| log | 241-245 (전 키 bool) | run_experiment 376, report 436~561, 요약 316 | 소비됨 |

### `_DECODER_KEYS` (run.py:66)

| 키 | 검증 | 소비 위치 | 판정 |
|----|------|----------|------|
| use_input_llr_matrix | 183-186 (bool, 기본 true) | setup 290 | 소비됨 |
| llr_matrix | true 분기 188 `_path_pair` / false 분기는 검증 없음 | setup 291 (true), 207-208 `dir`만 (false) | 조건부 소비, 아래 F5·F7 |
| internal_quantize | false 분기 191-204만 | setup 293-299 | 조건부 소비, 아래 F6 |
| type | 216-219 (비어 있지 않은 str, 기본 "vanilla") | setup 305, 요약 321 | 소비됨 |
| (generated_llr_matrix_path) | 키맵 밖. 215에서 코드가 주입 | setup 300 | 내부 전용 (아래 C㉰) |

### `_INTERNAL_QUANTIZE_KEYS` (run.py:67)

| 키 | 검증 | 소비 위치 | 판정 |
|----|------|----------|------|
| num_bits | 195-196 (int ≥ 2, 상한 없음) | setup 295 → llr_matrix.py:222-227 | 소비됨, 아래 F3 |
| channel_llr | 197-198 (int ≥ 1, 상한 없음) | setup 296 → llr_matrix.py:226 | 소비됨 |
| max_iter | 199-200 (int ≥ 1, 상한 없음) | setup 297 → llr_matrix.py:228 | 소비됨, 아래 F3 |
| mode | 201-204 (HD/2SD/3SD, 기본 HD) | setup 299, 파일명 209 | 소비됨 |

### `_RUN_KEYS` (run.py:68-69)

| 키 | 검증 | 소비 위치 | 판정 |
|----|------|----------|------|
| max_frame_errors | 231 (int ≥ 1) | run_experiment 369, 요약 325 | 소비됨 |
| max_frames | 232 (int ≥ 1) | run_experiment 370, 요약 326 | 소비됨 |
| frames_per_batch | 233 (int ≥ 1) | run_experiment 371, 요약 327 | 소비됨, 아래 F1 |
| stop_below_fer | 234-239 (양수 또는 null) | run_experiment 372/407, 요약 328 | 소비됨 |
| print_progress | 키맵 통과만, 타입 검증 없음 | run_experiment 373/394 | 소비됨, 아래 F9 |

### `_OUTPUT_KEYS` (run.py:70)

| 키 | 검증 | 소비 위치 | 판정 |
|----|------|----------|------|
| dir | 225-227 (기본값 + 절대경로화) | report 525 | 소비됨 |
| csv_prefix | 키맵 통과만 | report 533 | 소비됨, 아래 F9 |
| label | 키맵 통과만 | report 523 (실행 폴더 이름) | 소비됨, 아래 F9 |

### `_LOG_KEYS` (run.py:71-72)

| 키 | 소비 위치 | 경유 |
|----|----------|------|
| csw_per_iter | `_LOG_TO_ITEM` 79 → sim.py:66-68, report 436/448/547 | 수집 + 출력 |
| bit_err_per_iter | `_LOG_TO_ITEM` → sim.py:69, report 438/450/547 | 수집 + 출력 |
| bit_err_by_dv | `_LOG_TO_ITEM` → sim.py:70-72, report 440/452/548 | 수집 + 출력 |
| fail_frame_detail | `_LOG_TO_ITEM` → sim.py:73-78, report 557 | 수집 + 출력 |
| iter_histogram | report 552, 464/475 | 출력만 (iter_hist는 항상 수집) |
| fer_vs_iter | report 552, 466/477 | 출력만 |
| fer_curve_png | report 561-564 | 출력만 |

`_LOG_TO_ITEM`의 값 4개는 `decoder.LOG_ITEMS`(sim.py에서 오타 검출용으로 재확인)와 정확히 일치한다.

### `_CHANNEL_KEYS` (run.py:73-77)

| 키 | 검증 | 소비 위치 | 판정 |
|----|------|----------|------|
| type | 127-132 (`chan.CHANNELS` 소속) | `_make_channel_fn` 347, `_check_channel_mode` 379, report 523, 요약 314 | 소비됨 |
| points | 133-148 (rber는 0<p<0.5, 그 외 0 이상 정수) | run_experiment 397, 요약 314 | 소비됨 |
| label | 키맵 통과만 | run_experiment 387 (CSV 파일명) | 소비됨, 아래 F9 |
| SER / SCR (strong_error 전용) | 149-154 (0~1) | `_make_channel_fn` 351 → channel.py:91 | 소비됨 |

### 반대 방향 (코드가 읽는데 키맵에 없는 키)

전수 grep 결과 키맵 밖에서 읽히는 설정 키는 `decoder.generated_llr_matrix_path` 하나뿐이며,
이것은 사용자 입력이 아니라 `load_config`가 215행에서 주입하는 내부 값이다. 사용자가 JSON에
직접 쓰면 `_check_keys`(182행)가 먼저 걸러낸다. **오타가 조용히 통과하는 사용자 키는 없다.**

### 두 config 파일 대조

| 항목 | `config.json` | `Ideas/vanilla/config.json` | 결과 |
|------|--------------|----------------------------|------|
| decoder.type | 없음 | "vanilla" | 둘 다 vanilla (216행 기본값) |
| decoder.use_input_llr_matrix | true (명시) | 없음 | 둘 다 true (183행 기본값) |
| decoder.internal_quantize | 있음 (num_bits 6, channel_llr 8, max_iter 120, mode HD) | 없음 | use_input_llr_matrix=true라 **양쪽 다 무시**. F6 |
| output.label | 없음 | "vanilla" | config.json은 첫 채널 type "fixed_error"가 폴더 이름 |
| run.print_progress | 없음 | 없음 | 둘 다 기본 true. 두 config 어디에도 없고 README에도 없다. F9 |
| 상대경로 기준 | `2_LDPC_light/` | `Ideas/vanilla/` | 각 config 파일 위치 기준으로 정상 해석 |

두 파일 모두 키맵 위반 키는 없다.

## 발견 표

| # | 심각도 | 문제 | 위치 |
|---|--------|------|------|
| F1 | MEDIUM | `frames_per_batch`를 바꾸면 프레임별 난수 실현값이 전부 달라진다. 문서 3곳의 "결과에 영향 없음" 서술과 어긋난다 | run.py:33/371, sim.py:55-56, encoder.py:13, config.json:44, README.md:79-80 |
| F2 | MEDIUM | `int(1e6 * point)` 절단 때문에 1e-6보다 가까운 rber 포인트 두 개가 같은 난수 스트림을 쓴다 | run.py:398 |
| F3 | MEDIUM | `internal_quantize.num_bits`와 `max_iter`에 상한이 없다. num_bits는 시간·메모리가 2^num_bits로 늘어 오타 한 글자로 프로세스가 멈춘다 | run.py:195-200, llr_matrix.py:222-227, decoder.py:156-157, sim.py:45-50 |
| F4 | MEDIUM | `setup()`이 git 추적 대상 폴더 `Input/LLR/`에 파일을 쓰고, 파일명이 `dv_max`를 담지 않아 H-matrix가 다르면 같은 이름에 다른 내용이 저장된다 | run.py:206-215, 300-303 |
| F5 | MEDIUM | "llr_matrix 키는 있어도 무시된다"고 세 곳에 적혀 있으나 코드는 `llr_matrix.dir`을 생성 파일 위치로 실제 사용한다 | run.py:17-18/207-208, config.json:19-20, README.md:69 |
| F6 | MEDIUM | `use_input_llr_matrix=true`일 때 `internal_quantize`는 키맵만 통과하고 값 검증을 전혀 받지 않는다. 잘못된 값이 있어도 토글하기 전에는 드러나지 않는다 | run.py:182, 190-204 |
| F7 | LOW | false 분기의 `decoder.llr_matrix` 객체에는 `_check_keys`가 적용되지 않아 `dir` 오타가 조용히 기본 경로로 떨어진다 | run.py:207-208 |
| F8 | LOW | run 기본값 3개(50/20000/128)가 검증·소비·요약 세 곳에 리터럴로 중복. 현재 값은 전부 일치하지만 다른 기본값은 setdefault 단일 출처라 비대칭 | run.py:231-233 / 369-371 / 325-327 |
| F9 | LOW | `print_progress`, `csv_prefix`, `output.label`, `channels[].label`은 타입 검증이 없다. 뒤 세 개는 폴더·파일 이름에 그대로 들어간다 | run.py:69-70, 373, 387, 523, 533 |
| F10 | LOW | 실험 요약에 strong_error의 SER/SCR, 중복 해소된 실제 라벨, H-matrix 파일명이 빠진다 | run.py:313-330, pcm.py:105-111 |
| F11 | LOW | `points`에 같은 값을 두 번 넣으면 같은 시드로 같은 실험을 두 번 돌리고 로그 CSV 파일명이 겹쳐 덮어쓴다 | run.py:397-398, 550/555/559 |
| F12 | LOW | `setup()`의 파일 생성 부작용이 채널 모드 호환 검사보다 먼저 일어난다. mode 불일치 config는 파일만 남기고 실패한다 | run.py:294-303 vs 378-379 |

문제 없음으로 확인한 항목: B(`_` 접두 무시 규칙), C㉮(points in-place 정규화), D(기본값 리터럴 값 일치),
E의 채널 간 충돌·음수 시드, F㉮(검증 순서), G(미커밋 diff). 근거는 아래 상세에 적었다.

## 항목별 상세

### A. 키맵 커버리지

㉮㉯㉱는 위 대조표에 정리했다. 결론만 적으면, 키맵 밖에서 읽히는 사용자 키는 없고,
두 config 파일 모두 키맵을 지킨다.

㉰ **죽은 설정**: 완전히 죽은 키는 없다. 다만 `decoder.internal_quantize`는
`use_input_llr_matrix=true`인 동안 **검증도 소비도 되지 않는다**(F6). 지금 `config.json`이
바로 그 상태다(25행 true, 30-35행 internal_quantize 존재). 사용자가 `num_bits`를 8로 고쳐도
아무 일이 없고, `"num_bits": "여섯"`처럼 타입이 틀려도 통과한다. `use_input_llr_matrix`를
false로 바꾸는 순간에야 에러가 난다. 반대로 `llr_matrix`는 false일 때도 `dir`이 살아 있어
"무시"가 아니다(F5).

수리 방향: 분기와 무관하게 `internal_quantize`가 있으면 항상 검증한다. 그러면 토글만으로
동작이 바뀌는 설계 의도(README ㉮의 "플래그만 바꿔 토글 가능")도 실제로 성립한다.

### B. `_desc` 무시 규칙

`_visible()`(83-85)은 `_check_keys()`(88-93)를 거쳐 적용되고, `_check_keys`는 최상위(168),
`decoder`(182), `decoder.internal_quantize`(194), `run`(230), `output`(224), `log`(242),
`channels[i]`(132), 그리고 `_path_pair` 안(116, 즉 `H_matrix`와 `decoder.llr_matrix`)에서
전부 호출된다. `log`의 bool 검사도 `_visible(log_config)`로 순회한다(243).

㉯ **경로 쌍 검증 헬퍼도 `_visible`을 거친다.** `_path_pair`는 `_check_keys(section, d, {"dir","file"})`를
쓰므로 `H_matrix` 안의 `_desc`가 허용된다. 실제 `config.json:5-8`이 `H_matrix._desc`를 쓰고 있고
정상 통과한다. **문제 없음.**

빠짐없이 적용되므로 `_desc`를 넣어 에러가 나는 섹션은 없다.

### C. in-place 정규화의 파급

㉮ **`points` 스칼라→리스트 정규화(136행)**: 정규화는 `load_config` 안에서 끝나고, 소비처
셋(`_experiment_summary_lines` 314, `run_experiment` 397, `report`)은 모두 그 뒤에 돌아가므로
전부 리스트를 본다. `report`가 저장하는 config 사본은 **변형된 dict가 아니라 원본 파일을
그대로 복사**하므로(527행 `shutil.copy(config_path, ...)`) 사본에는 사용자가 쓴 스칼라가
남는다. 라벨 생성(387)은 `points`를 쓰지 않는다. **파급 없음.**

㉯ **`seed`만 되쓰고 run의 `_check_int`는 되쓰지 않는 비대칭**: 실제 타입 오염은 없다.
`_check_int`(102-107)가 `isinstance(value, int)`를 요구해 문자열 `"50"`도 실수 `50.0`도
전부 에러로 막기 때문이다. 즉 검증을 통과한 값은 이미 int이고, 소비부가 `.get(기본값)`으로
다시 읽어도 같은 int가 나온다. 남는 것은 기본값 리터럴이 세 곳에 중복된다는 점뿐이다(F8).

㉰ **config를 고치는 곳 전수**: ㉠ `H_matrix` dict→문자열 경로(174) ㉡ `decoder` 생성(177)
㉢ `use_input_llr_matrix` 기본값 기입(183) ㉣ `llr_matrix` dict→문자열 경로(188, true 분기만)
㉤ `internal_quantize.mode` 기본값 기입(201) ㉥ `generated_llr_matrix_path` 주입(215)
㉦ `type` 기본값 기입(216) ㉧ `seed` 기입(221) ㉨ `output` 생성 + `dir` 기본값·절대경로화(223-227)
㉩ `run`/`log` 생성(229, 241) ㉪ `channels` dict→리스트(248-250) ㉫ `points` 리스트화(136).

전부 소비부보다 먼저 일어나고 사본 저장 경로를 타지 않아 실제 파급은 없다. 다만 ㉥ 때문에
`decoder` dict가 키맵에 없는 키를 갖게 되므로, 같은 dict를 `load_config`에 두 번 넣으면
`_check_keys`가 실패한다. 현재 `main()`은 한 번만 호출하므로 발현하지 않는다.
㉣ 때문에 `decoder.llr_matrix`의 타입이 분기에 따라 문자열이거나 dict인 점도 기록해 둔다.

### D. 기본값 리터럴 산재

세 곳을 전수 대조했다.

| 키 | load_config(검증) | run_experiment(소비) | `_experiment_summary_lines`(요약) | 일치 |
|----|------------------|---------------------|----------------------------------|------|
| max_frame_errors | 50 (231) | 50 (369) | 50 (325) | 일치 |
| max_frames | 20000 (232) | 20000 (370) | 20000 (326) | 일치 |
| frames_per_batch | 128 (233) | 128 (371) | 128 (327) | 일치 |
| stop_below_fer | None (234) | None (372) | None (328) | 일치 |
| print_progress | (검증 없음) | True (373) | (요약에 없음) | 요약 누락 |

**어긋난 값은 없다.** 참고로 `sim.run_fer_point`의 시그니처 기본값(sim.py:11-12)도
`50 / 20000 / 128`로 같다. 네 곳이 같은 숫자를 들고 있는 셈이다.

㉯ 다른 섹션은 산재하지 않는다. `decoder.type`("vanilla" 216), `use_input_llr_matrix`(true 183),
`internal_quantize.mode`("HD" 201), `output.dir`("Sim_Output" 225)는 `setdefault`로 config에
기입되어 소비부가 그 값을 그대로 읽는 단일 출처다. `output.csv_prefix`("fer" 533)와
`output.label`(523)은 소비부 한 곳에만 있다. **결국 리터럴이 흩어진 것은 run 섹션 3개뿐이며,
이것만 `setdefault` 방식으로 통일하면 종류가 하나로 정리된다.**

### E. 난수 스트림 파생

파생식은 `np.random.default_rng([seed, channel_index, int(1e6 * point)])` (run.py:398),
포인트 루프 안에서 포인트마다 새로 만든다.

㉮ 판정:

- **rber 포인트 뭉개짐 (F2, MEDIUM)**: `int()`는 버림이라 `1e6 * point`의 정수부가 같으면
  같은 스트림이 된다. 확인한 예로 `0.001`, `0.0010005`, `0.0010009`가 전부 `1000`이 된다.
  두 포인트가 완전히 같은 잡음 실현값을 쓰므로 서로 독립인 측정이 아니게 되고, FER 커브의
  두 점이 인위적으로 붙는다. 간격 1e-6 이상인 통상적 RBER 스윕에서는 발현하지 않지만,
  스윕을 촘촘하게 만들면 조용히 발현한다. 수리 방향은 포인트를 정수로 뭉개지 말고
  `repr(point)` 같은 문자열을 해시하거나 `float.hex()`를 쓰는 것이다.
- **fixed_error 정수 포인트와의 충돌**: `channel_index`가 `enumerate(config["channels"])`의
  인덱스(383행)이므로 서로 다른 채널 항목은 항상 다른 스트림을 받는다. 한 채널 항목 안의
  포인트는 전부 같은 type이라 rber와 fixed_error가 같은 스트림을 쓰는 일은 구조적으로 없다.
  **채널 간 충돌은 없다.**
  다만 한 rber 채널 안에서 `1e-7`, `5e-7`처럼 1e-6 미만 포인트는 전부 `0`이 되어 서로 충돌한다
  (F2와 같은 원인).
- **음수 포인트**: `np.random.default_rng([0, 0, -5])`는 `ValueError: expected non-negative integer`를
  낸다. 그러나 `_check_channel`(139-148)이 rber는 `0 < p`, 나머지는 `point >= 0`을 강제하므로
  음수는 config 경로로 도달할 수 없다. **발현 불가.**
- **같은 시드 재사용의 심각도**: 두 포인트가 같은 스트림을 쓰면 메시지 bit와 잡음이 완전히
  같아지므로, 두 포인트의 측정이 통계적으로 독립이 아니다. FER 자체는 각 포인트에서 여전히
  불편(unbiased) 추정이지만, 두 점의 차이를 비교하는 용도(커브의 기울기, 아이디어 on/off)에서는
  오차가 상쇄되어 실제보다 매끈해 보인다. 발현 조건이 좁아 MEDIUM으로 본다.

㉯ **배치 루프 안에서 rng는 재생성되지 않는다**(sim.py:54-79). 한 포인트의 모든 배치가 하나의
generator를 이어 쓰므로 배치 간 프레임은 독립이다. 여기까지는 정상이다.

**다만 배치 크기가 결과를 바꾼다 (F1, MEDIUM).** `channel_fn`(run.py:353-357)은 배치마다
㉠ `encoder.generate_message`가 `random_generator.integers(0, 2, size=(batch, K))`로 난수를 뽑고
㉡ 이어서 채널이 같은 generator로 잡음을 뽑는 순서로 동작한다. 즉 메시지 추출과 잡음 추출이
배치 단위로 번갈아 일어난다. 잡음만 뽑는다면 배치를 어떻게 쪼개도 스트림 소비가 같아 결과가
동일하지만, 사이에 메시지 추출이 끼면 배치 경계에 따라 소비량이 달라져 **모든 프레임의 잡음이
달라진다.**

프로젝트 코드를 건드리지 않고 numpy 동작만 재현해 확인한 결과다 (K=1000, N=2000, 128 프레임).

```
128 vs 64 identical: False       # 메시지 추출을 끼운 현재 구조
128 vs 32 identical: False
no-msg 128 vs 64 identical: True # 잡음만 뽑으면 배치 크기에 무관
```

문서 세 곳이 "결과에 영향 없음"이라고 단언한다 (run.py:32-33, config.json:44, README.md:79-80).
게다가 `encode()`(encoder.py:16-19)는 msg를 **무시하고 all-zero를 반환**하므로, 이 난수 소비는
결과에 기여하지 않으면서 스트림만 어긋나게 만든다.

실무 영향: `Ideas/vanilla/config.json`과 아이디어 config는 `frames_per_batch`가 서로 다를 수 있고
(속도 조절용으로 바꾸기 쉬운 값이다), 그러면 같은 seed인데도 다른 잡음으로 비교하게 된다.
지금 두 config의 `max_frames`가 256, `max_frame_errors`가 10으로 작아 실현값 차이가 FER 숫자에
크게 드러나므로, 아이디어 효과로 오인할 소지가 있다.

수리 방향 두 가지 중 하나: ㉮ `encode()`가 msg를 쓰지 않는 동안에는 `generate_message` 호출을
빼거나 별도 generator를 쓴다 (스트림이 잡음 전용이 되어 배치 크기 무관이 실제로 성립한다)
㉯ 문서에서 "결과에 영향 없음"을 "속도와 메모리만 조절하며, 실현값은 배치 크기에 따라 달라진다"로
바로잡는다. 실물 인코더가 들어오면 ㉮도 성립하지 않으므로, 배치 크기 무관을 유지하려면
프레임 단위로 스트림을 파생하는 구조가 필요하다.

### F. 검증 순서와 에러 메시지

㉮ **`decoder.max_iter` 금지 검사(178-181)가 `_check_keys("decoder", ...)`(182)보다 먼저다.**
따라서 사용자는 "허용 키 목록" 같은 일반 메시지가 아니라
`decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(또는 internal_quantize.max_iter)이 결정`
이라는 이유 있는 메시지를 본다. README ㉮의 서술과도 맞는다. **문제 없음.**

㉯ **하한 근거와 상한 부재**:

- `num_bits >= 2`: 타당하다. 1이면 `top_level = 0`, `th = []`이 되어 `LLRMatrix.__init__`의
  `th_len <= 0` 에러(llr_matrix.py:65-66)로 떨어지는데, 그 메시지는 원인을 알기 어렵다.
  하한 2가 그 상황을 앞에서 막는다.
- `channel_llr >= 1`: 0을 막을 기술적 이유는 확인되지 않았다. 0이면 채널 기여가 없는
  syndrome 전용 디코딩이 되는데, 이는 llr_matrix.py 모듈 docstring(24-26)이 restart row의
  `ch=-1`을 설명하며 의미 있는 동작으로 기술한 것과 같은 계열이다. 지금 하한 1은 그 실험을
  막는다. 설계 의도라면 그대로 두되 이유를 적어 두는 편이 좋다 (LOW).
- **상한 부재 (F3, MEDIUM)**: `num_bits`는 상한이 없는데 비용이 지수로 늘어난다.
  `top_level = 2**(num_bits-1) - 1`이고(llr_matrix.py:222) `th = list(range(top_level, 0, -1))`(224)이
  그 길이만큼 파이썬 리스트를 만든다. 소비부인 `_vnu_quantize`(decoder.py:156-157)도
  `for k in range(len(edge_mag)-2, -1, -1)` 파이썬 루프로 임계값 수만큼 `np.where`를 돈다.
  정리하면 매 iteration, 매 column block마다 2^(num_bits-1)-1 회의 배열 연산이다.
  `num_bits: 6`이면 31회지만 `num_bits: 16`이면 32767회, `num_bits: 64`(레벨 수와 bit 수를
  혼동하기 쉬운 값이다)면 리스트 생성 단계에서 메모리가 터진다. 검증이 하한만 두고 상한을
  비워 둔 탓에, 오타 하나가 곧바로 프로세스 정지로 이어진다. `num_bits <= 12` 정도의 상한과
  이유를 붙이는 것을 제안한다.
  `internal_quantize.max_iter`도 같다. sim.py:45-50이 `np.zeros(max_iter+1)`,
  `np.zeros((max_iter, num_dv))`를 잡으므로 큰 값이면 메모리로 직행한다.
  파일 로드 경로는 파일의 `iter_end`가 max_iter를 정해 실질 상한이 있지만, internal_quantize는
  사용자 숫자가 그대로 들어간다.
- 참고로 `channel_llr` 상한도 없어 `num_bits`가 정하는 최대 레벨보다 큰 채널 LLR을 넣을 수
  있다. 그것이 의도인지(HW에서는 채널 LLR이 메시지 범위를 넘어설 수 있다) 실수인지는
  균일 양자화 수치 규약을 맡은 팀 A의 판정 영역이라 여기서는 검증 부재 사실만 남긴다.

㉰ **`stop_below_fer`의 break 범위**: 407-408행의 `break`는 포인트 루프만 빠져나오고 바깥
채널 루프는 계속 돈다. 즉 "해당 채널의 남은 포인트만" 중단한다. 서술 셋을 대조하면
run.py:34 "남은 포인트 측정 중단", config.json:45 "남은 포인트 중단", README.md:81
"남은 포인트 측정 중단"으로 모두 "어느 범위의 남은 포인트인지"를 적지 않았다. 채널이 여러 개일
때 실행 전체가 멈춘다고 읽을 수 있다. 동작 자체는 합리적이므로 서술에 "해당 채널의"를
넣어 맞추면 된다 (LOW, 문서 정합).

또한 `break` 이후에도 `results.append((label, point_results))`(409)가 실행되어 그때까지의
포인트는 정상 저장된다. 반면 실험 요약(313-315)은 `channel_config['points']` 전체를 그대로
찍으므로, 중단이 일어나면 요약이 광고한 포인트와 CSV에 실제 있는 포인트가 달라진다.
summary.txt만 보는 사람이 오해할 수 있다 (LOW, F10과 함께 묶임).

### G. 미커밋 config.json 변경

```
-      "use_input_llr_matrix: true면 llr_matrix 파일 사용 (모드는 파일명 HD/2SD/3SD로 판별,",
+      "use_input_llr_matrix:",
+      "true면 llr_matrix 파일 사용 (모드는 파일명 HD/2SD/3SD로 판별,",
```

- **동작 영향 없음**: `decoder._desc`는 `_visible()`이 걸러내는 설명용 키이고, 배열 원소가
  하나 늘어난 것뿐이다.
- **코드 동작과의 일치**: "true면 llr_matrix 파일 사용", "모드는 파일명 HD/2SD/3SD로 판별",
  "max_iter는 파일의 마지막 iter_end가 결정, JSON에 두면 에러" 세 서술은 각각
  llr_matrix.py:165-169, llr_matrix.py:92, run.py:178-181과 맞는다.
- **서술 관례**: 키 이름만 있는 줄 뒤에 들여쓴 설명 줄이 이어지는 형태는 같은 `_desc`
  안의 `internal_quantize:` 항목(22-23행)과 같은 관례라 섹션 안에서 일관된다.
  `run`/`log`/`output`의 `_desc`가 "키: 설명" 한 줄 형식인 것과는 다르지만, decoder 항목은
  설명이 길어 두 형식이 공존할 이유가 있다.
- **판정: 문제 없음.** 다만 같은 `_desc` 블록의 19행 "llr_matrix 키는 무시"는 F5의 대상이므로,
  이 파일을 손대는 김에 함께 고치는 것이 좋다.

### 부수 기록 (참고)

- `2_LDPC_light/llr_tables.py`는 docstring이 `2_LDPC_light/llr/*.txt`를 전제하는데 그 폴더가
  없고, 어느 모듈도 이 파일을 import하지 않는다. config 스키마와는 무관하지만 남은 파일로
  보인다. 패키지 경계를 맡은 팀 C의 판정 영역이라 사실만 적어 둔다.
