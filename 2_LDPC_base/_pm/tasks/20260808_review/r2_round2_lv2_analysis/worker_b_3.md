# Round 2 / 팀 B / 워커 3 — 의견1 이름 수정의 완결성 + 요약 출력의 사실 정확성

## 확인 범위

- 직접 읽은 파일: `LDPC_base/run.py`(전체), `LDPC_base/sim.py`(전체), `LDPC_base/decoder.py`(전체),
  `LDPC_base/llr_matrix.py`(전체), `LDPC_base/pcm.py`(summary + 모듈 docstring),
  `LDPC_base/channel.py`(docstring 발췌), `Ideas/registry.py`, `Ideas/vanilla/decoder.py`,
  `config.json`(미커밋 diff 포함), `_pm/done/20260808_의견1_반영/의견1.md`
- 조회: `git show d42ca8c`(의견1 반영 커밋 diff), `git log ea88882..HEAD`, `git diff -- config.json`
- Grep: 구 이름 전수(`decoder_cls`, `mx`, `verbose`, `rng`, `unknown`, `fail_rows`, `agg_`,
  `res`, `n_it`, `n_active`, `frozenset`, `dec`, `ch`, `cfg`, 단문자 대입), 중복이름 정규식
  `([a-z_]{3,})_\1`, 조사 어긋남(식별자+한글 조사 조합), `%` 마커, 이력 서술 후보 표현
- 실행은 하지 않음

---

## A. 의견1 항목별 대조표

`의견1.md` 전 항목(1~35행)을 추출해 대조했다. 근거는 현재 HEAD 기준 라인 번호.

| # | 지적 항목 (의견1.md 행) | 반영 | 근거 위치 | 잔존 사례 |
|---|---|---|---|---|
| 1 | `decoder_cls` → `decoder_class` (4행) | 완료 | `run.py:258` `_resolve_decoder_class()`, `run.py:305` `decoder_class = ...` | `decoder_cls` 전 파일 0건 |
| 2 | `mx` → `llr_matrix` (5행) | 완료 | `run.py:291,300,304,306`, `decoder.py:103~118`, `sim.py:41` | `\bmx\b` 0건 |
| 3 | summary: 코드정보/dec정보/읽은 config정보 출력 (6~7행) | 완료 | `run.py:310~330` `_experiment_summary_lines()`, 콘솔 `run.py:578~579`, 파일 `run.py:531` | 누락 항목은 C절 참조 |
| 4 | `verbose`는 뭐야 → `print_progress` (8행) | 완료 | `run.py:35,69,373,394,403`, `sim.py:12,17,95` | `\bverbose\b` 0건 |
| 5 | `used_labels` 분기 설명 (9~10행) | 완료 | `run.py:385~386` 주석("같은 type의 채널이 여러 개면 파일명이 겹쳐 덮어쓰므로 번호 접미사로 구분") | — |
| 6 | `points = []` 이름 부정확 (11행) | 완료 | 결과 리스트 지역변수를 `point_results`로 개명: `run.py:396,406,409`, `run.py:500,534`. JSON 키 `points`는 외부 계약이라 유지 | 아래 LOW-5(`param` 용어 드리프트) |
| 7 | `rng` → `random_generator` (12행) | 부분 | `run.py:353,398`, `sim.py:10,15,56`, `channel.py` 전역 | `tools/H_mat_gen/`은 `rng` 유지: `gen_example_code.py:28,33,43,44`, `lifting.py:10,24,42`, `peg.py:32,62`, `select_irregular.py:40,43` |
| 8 | `_make_channel_fn` 결과를 변수로 (13~14행) | 완료 | `run.py:399` `channel_fn = _make_channel_fn(...)` → `run.py:401~404`에서 인자로 전달 | — |
| 9 | `unknown` (15행) → `unknown_log_items` | 완료 | `sim.py:35~38`, `decoder.py:376~378`. `run.py:89`는 별개 문맥이라 `unknown_keys` | `llr_tables.py:64`의 `unknown key`는 에러 메시지 문자열(고아 모듈, 아래 LOW-6) |
| 10 | `fail_rows` (16행) → `fail_frame_details` | 완료 | `sim.py:51,75,94`, 소비측 `run.py:489,557` | `fail_rows` 0건 |
| 11 | `agg_active`의 `agg` (17행) → `total_*` | 완료 | `sim.py:47~50` `total_active_frames/total_csw/total_bit_err/total_bit_err_by_dv`, dict `sim.py:90~92` `iteration_totals` | `agg_` 0건 |
| 12 | `b` → `batch` (18~19행) | 완료 | `sim.py:55,56,79`, 채널 함수 시그니처 `run.py:353` `def channel_fn(batch, random_generator)` | — |
| 13 | `res` (20~21행) → `decode_result` | 완료 | `sim.py:56~78` | `\bres\b` 0건, `result*` 계열 오염 없음 |
| 14 | `n_it` (22행) → `num_iterations_run` | 완료 | `sim.py:64,65,67,69,71` | `\bn_it\b` 0건 |
| 15 | "과거에 어땠고 지금 어떻다" 금지 + 문장 규칙 3항 등록 (24~30행) | 부분 | 루트 `CLAUDE.md` "문장 작성 규칙" 절에 3항 등록됨 | 코드 주석 잔존 위반은 D절 |
| 16 | `frozenset` (32행) → `set` | 완료 | `decoder.py:60` `LOG_ITEMS = {...}`(set 리터럴), `decoder.py:67` `log: set`, `decoder.py:375`, `sim.py:34`, `run.py:376` | `frozenset` 0건 |
| 17 | `s = self._init_state(...)` (33행) → `state` | 완료 | `decoder.py:210,236,381` 및 `_run_iteration`/`_process_column`/`_record_iteration`/`_check_errors` 전 구간 | `\bs =` 0건 |
| 18 | `n_active` (34행) → `num_active_frames` | 완료 | `decoder.py:93,241~244,271,315`, `llr_matrix.py:291,295,298` 및 docstring 축 표기 | `\bn_active\b` 0건 |

**미완결 2건**: #7(tools/ 미적용), #15(코드 주석의 이력 서술 잔존).

### 이름 스윕이 닿지 않은 잔존 축약 (의견1 미열거, 완결성 관점)

| 위치 | 잔존 이름 | 내용 |
|---|---|---|
| `run.py:501~502` | `r` | `xs = [r["param"] for r in point_results]`, `fer = [r["fer"] if r["errors"] else 0.5 / r["frames"] ...]` — `res`→`decode_result`, `r = run_fer_point(...)`→`point_result` 개명이 이 comprehension에는 미적용 |
| `run.py:504` | `f` | `for x, f, point_result in zip(xs, fer, point_results)` — `f`가 FER 값 (다른 함수에서는 파일 핸들) |
| `run.py:425` | `f`, `t` | `_dv_labels`의 `zip(dv_from, dv_to)` 루프 변수 |
| `llr_matrix.py:175~189` | `i` | 파서 커서 (문맥상 허용 가능) |

---

## B. 기계 치환 후유증 점검

| 점검 | 결과 |
|---|---|
| ㉮ 조사 어긋남 | 없음. 식별자+조사 조합 14건 전수 확인(`llr_matrix는/가`, `max_iter를/는/와`, `points는/의`, `frames_per_batch가`, `frames로`) — 전부 정상 |
| ㉯ 이름 중복 | 없음. `([a-z_]{3,})_\1` 매치는 `_write_iter_log` / `_write_iter_hist_log` 뿐(정상 함수명). `llr_matrix_llr`, `total_total`, `state_state`, `batch_batch`, `result_result` 0건 |
| ㉰ 부분문자열 오염 | 없음. `res`→`decode_result` 치환이 `results`/`point_result(s)`를 건드리지 않았고, `b`→`batch`가 `frames_per_batch`만 정상 포함, `mx`→`llr_matrix`가 `matrix`를 오염시킨 흔적 없음. `LDPC_base` 내 `batch|state|decode_result|random_generator|llr_matrix|print_progress|num_active_frames` 포함 식별자 전수 열거 결과 12개 전부 정상 이름 |
| ㉱ 이름-의미 정합 | 아래 상세 |
| ㉲ 외부 계약(dict 키/CSV 헤더) 파손 | 없음. 아래 상세 |

### ㉱ 이름과 실제 의미

- `total_active_frames` (`sim.py:47`) — 스칼라 합이 아니라 **iteration별 배열**이며, 각 원소가 배치를 넘어 누적된 "그 iteration에 활성이던 프레임 수의 합"이다(`sim.py:65`). `total_`은 "배치 누적"을 뜻하고 축은 iteration이라는 사실이 이름만으로는 안 읽히지만, `sim.py:46` 주석("iteration별 합계 (배치를 넘어 누적 — 평균은 합/활성 프레임 수로 소비측 계산)")과 소비측 dict 키 `iteration_totals`(`sim.py:90`)가 축을 명시한다. 소비부 `run.py:432~454`의 계산(`sum[k] / active[k]`)과 의미가 일치 — **정합 확인**.
- `final_err_bits` (`decoder.py:337,364`) — "마지막 처리 iteration의 잔여 에러 bit"라는 뜻이 이름만으로 다 읽히지는 않으나, `decoder.py:229~230` 주석과 `decoder.py:364~365` docstring이 정확히 그 뜻을 적었다. 계산부(`decoder.py:310` `_record_iteration`이 매 iteration 활성 프레임 위치에 덮어쓰고, `_check_errors`의 배치 압축은 그 뒤에 일어남)를 읽어 확인 — 성공 프레임은 성공한 iteration의 값 0이 남고, 실패 프레임은 max_iter 시점 값이 남는다. **계산과 문서 일치**.
- `avg_decode_success_iteration` (`sim.py:85`) — 분모가 `max(1, frames - errors)` = 성공 프레임 수. **정합**.
- `num_iterations_run` (`sim.py:64`) — 조기 종료 시 max_iter보다 작을 수 있는 실제 수행 iteration 수. **정합**.

### ㉲ dict 키 · CSV 헤더 대조 (외부 계약)

| 생산 | 소비 | 일치 |
|---|---|---|
| `sim.py:82~88` `frames/errors/fer/post_fec_ber/avg_decode_success_iteration/sec/fps/iter_hist` | `run.py:502,540~545`, `sim.py:108~116` CSV 헤더 | ○ |
| `sim.py:90~92` `iteration_totals{active_frames, csw_sum, bit_err_sum, bit_err_by_dv_sum}` | `run.py:432~433,449,451,453` | ○ |
| `sim.py:94` `fail_frame_details` | `run.py:489,557` | ○ |
| `run.py:405` `point_result["param"]` | `sim.py:108` CSV 첫 열 `param`, `run.py:501` | ○ |
| `decoder.py:336~350` `success/decode_success_iteration/final_err_bits/log_active/log_csw_sum/log_err_sum/log_err_by_dv_sum/final_csw/final_err_by_dv` | `sim.py:58~78` | ○ (가드 조건도 생산·소비가 동일: `"csw" in log` 등) |

CSV 헤더 문자열(`param, fer, post_fec_ber, frames, errors, avg_decode_success_iteration, sec` /
`iter, active_frames, csw_mean, bit_err_mean, bit_err_dv*_mean` / `iter, success_at_iter,
fer_if_max_iter_k` / `frame, final_err_bits, final_csw, err_dv*`)은 모두 코드 내부에서만
생산·소비되며 파손 없음. JSON 설정 키(`use_input_llr_matrix`, `points`, `label`,
`print_progress` 등)도 `_TOP_KEYS`~`_CHANNEL_KEYS` 키맵과 `config.json`이 일치.

**결론: 기계 치환 후유증 없음.**

---

## C. 요약 출력 사실 정확성 대조표

`_experiment_summary_lines`(`run.py:310~330`)가 다시 읽는 값 전수 대조.

| 요약이 찍는 값 | 요약 쪽 소스 | 실제 사용처 | 일치 |
|---|---|---|---|
| `max_frame_errors` 기본 50 | `run.py:325` `.get(...,50)` | `run.py:369` `.get(...,50)` / 검증 `run.py:231` 기본 50 | ○ |
| `max_frames` 기본 20000 | `run.py:326` | `run.py:370` / 검증 `run.py:232` | ○ |
| `frames_per_batch` 기본 128 | `run.py:327` | `run.py:371` / 검증 `run.py:233` | ○ |
| `stop_below_fer` 기본 없음(None) | `run.py:328` | `run.py:372` | ○ |
| `seed` | `run.py:324` `config['seed']` | `run.py:374` | ○ (`load_config:221`이 config에 기본 0을 기록) |
| `decoder.type` | `run.py:321` | `run.py:305` `_resolve_decoder_class` | ○ |
| 실제 클래스명 | `run.py:322` `type(decoder).__module__/.__name__` | — | ○ (Ideas 있으면 `Ideas.vanilla.decoder.VanillaDecoder`, 없으면 `LDPC_base.decoder.MinSumDecoder`) |
| `max_iter` | `run.py:323` `decoder.max_iter` | `decoder.py:116` `self.max_iter = llr_matrix.max_iter` | ○ (llr_matrix.summary()의 max_iter와 **항상 동일** — 중복 표시) |
| `log` 켠 항목 | `run.py:316` `_LOG_KEYS` ∩ true | `run.py:376` `_LOG_TO_ITEM`(4개) + report 측 3개 | ○ |
| 채널 설명 | `run.py:313~315` `type` + `points` | `run.py:397` `channel_config["points"]` | 부분 (아래 ㉲) |
| 부호 정보 | `run.py:319` `code.summary()` | `pcm.py:105~111` | ○ (단, H-matrix 파일명 없음) |
| LLR matrix 정보 | `run.py:320` `decoder.llr_matrix.summary()` | `llr_matrix.py:309~317` | ○ (단, 전체 경로·생성 여부 없음) |

**기본값 리터럴 어긋남 0건 (HIGH 없음).** 다만 같은 기본값 리터럴이
`load_config`(검증) / `run_experiment`(사용) / `_experiment_summary_lines`(표시) 3곳에
독립적으로 복제되어 있어, 한쪽만 고치면 요약이 조용히 거짓을 찍게 된다 (LOW-1).

### ㉯ 균일 양자화 모드 판별 가능성 — 가능

`use_input_llr_matrix=false`로 돌리면 요약 2행이
`LLRMatrix LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt: mode=HD (ch1+th31), dv=[1]~[dv_max],
max_iter=120, groups: g1[1~120]x1` 형태가 되어, 파일명이 `mode`/`num_bits`/`channel_llr`/
`max_iter`를 전부 담는다(`run.py:209~211` 생성 파일명 규칙, `llr_matrix.py:206` `name=basename`).
**LLR matrix 공급 경로 자체(파일 로드 vs 생성 후 로드)는 요약에 없다** — `setup()`이
`run.py:303`에서 `generated LLR matrix: {path}`를 콘솔에만 출력하고 요약 줄에는 넣지 않는다.
파일명의 `uniform` 표시로 사실상 구분되고 `config.json` 원본이 실행 폴더에 복사되므로
치명적이지는 않다 (LOW-2).

### ㉰ summary() 반환 형태와 줄 구성 — 깨지지 않음

- `QCCode.summary()`는 `\n`이 2개 들어간 **3줄짜리 문자열 1개**(`pcm.py:108~111`)
- `LLRMatrix.summary()`는 **1줄 문자열**(`llr_matrix.py:315~317`)
- 콘솔: `run.py:578~579`가 리스트 원소를 그대로 `print` → 3줄이 3줄로 출력
- 파일: `run.py:566` `"\n".join(lines)` → 동일한 줄 구성

**콘솔 vs summary.txt**: summary.txt는 콘솔 출력의 상위집합이다.
`run.py:530`이 앞에 `run: {stamp}_{label}`, `code commit: {hash}`, 빈 줄을 덧붙이고,
`run.py:532` 이후 빈 줄 + 포인트별 결과 줄을 덧붙인다. 요약 블록 자체는 동일. **일치**.

### ㉱ `decoder.max_iter` vs `llr_matrix.max_iter` — 항상 같음

`decoder.py:116`에서 `self.max_iter = llr_matrix.max_iter`로 한 번만 대입되고 이후 갱신이
없다. 요약이 두 값을 각각 찍지만(`run.py:320`의 llr_matrix summary, `run.py:323`의
`decoder.max_iter`) 불일치가 발생할 경로가 없다. 중복 표시일 뿐 오류 아님 (LOW-3).

### ㉲ 채널 설명 줄 — points 정규화는 반영, 라벨은 미반영

- **points 스칼라→리스트 정규화: 반영됨.** `_check_channel`(`run.py:135~136`)이
  `channel_config["points"]`를 제자리에서 리스트로 덮어쓰고, `_experiment_summary_lines`는
  `load_config` 이후에만 호출되므로 정규화된 값을 읽는다.
- **라벨 접미사: 미반영.** `run.py:314`가 `channel_config['type']`만 쓰고 `label` 키도,
  `run_experiment`가 만드는 중복 회피 접미사(`run.py:388~393`의 `_2`, `_3`)도 반영하지 않는다.
  같은 type 채널이 2개면 요약의 채널 줄이 `rber[...], rber[...]`로 똑같이 찍히고,
  `label`을 지정한 경우 요약에는 label이 아예 안 나온다. 결과 줄(`run.py:539~545`)과
  CSV 파일명은 label 기준이라 summary.txt 안에서는 매핑이 가능하다 (LOW-4).

### ㉳ `_git_commit_hash()`와 dirty 상태 — MEDIUM 2건

`run.py:413~420`은 `git rev-parse --short HEAD`만 실행하고 working tree의 미커밋 변경을
표시하지 않는다. 현재 저장소는 `2_LDPC_light/config.json`이 미커밋 수정 상태이므로,
지금 실험을 돌리면 summary.txt에 `code commit: e6282b1`이 기록되지만 그 커밋을 체크아웃해도
같은 상태가 재현되지 않는다. config는 실행 폴더에 사본이 남아 복구 가능하지만,
`LDPC_base/*.py`가 미커밋 수정 상태라면 **재현성 기록이 조용히 거짓이 된다** (MEDIUM-1).

추가로 `except OSError`만 잡으므로 `subprocess.TimeoutExpired`(`SubprocessError` 계열,
`OSError` 아님)는 전파된다. 이 호출은 `run.py:530`으로 **CSV 저장 루프(`run.py:534~536`)보다
먼저** 실행되므로, 예외가 나면 시뮬레이션을 다 돌린 뒤 결과를 하나도 못 남기고 죽는다
(MEDIUM-2).

### ㉴ 요약 출력과 `run.print_progress`의 관계

요약은 `run.py:578~579`에서 **무조건** 출력된다. `print_progress`가 끄는 것은
`run.py:394~395`의 채널 헤더와 `sim.py:95~100`의 포인트별 진행 줄뿐이다.
`setup()`의 `generated LLR matrix:`(`run.py:303`), `report()`의 `saved:`/`run dir:`
(`run.py:537,564,567`)도 무조건 출력된다. 모듈 docstring `run.py:35`가 이 키를
"진행 상황 콘솔 출력 여부"로 한정해 적었으므로 **문서와 동작은 일관**. 다만 요약 줄에
`print_progress` 값 자체가 안 찍힌다 (LOW-2에 포함).

---

## D. 문장 규칙 자기 적용 (LOW 일괄)

`%` 마커 잔존: **0건**.
규칙 ㉯(부정 먼저 → 줄표 뒤 뒤집기) 위반: `run.py:180` 에러 메시지
`"decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(…)이 결정"` 1건.

규칙 ㉮(과거·현재 대비 서술 금지) 잔존 8건:

| 위치 | 표현 |
|---|---|
| `pcm.py:8` | "이 포맷만 지원 (2026-08-06 사용자 결정 — 구 포맷('#' 주석 + 'M_b N_b z' 헤더) 지원 제거)" |
| `pcm.py:15` | "(예시 부호도 재배열 완료, 2026-08-06 정정)" |
| `channel.py:16` | "난수는 original XOR25 대신 numpy Generator (plan.md 기존 결정과 동일)" |
| `channel.py:74` | "(구간 슬라이스로 나눠 쓰면 안 됨 — 리뷰 F1)" |
| `channel.py:98` | "2단계 추출 (사용자 확정 2026-08-07, 리뷰 F1 후속)" |
| `llr_matrix.py:15` | "(사용자 결정 2026-08-06)" |
| `llr_matrix.py:27` | "(사용자 확인 2026-08-06)" |
| `llr_matrix.py:29`, `llr_matrix.py:32~35` | "(사용자 결정 — 원본 C++의 조용한 col_idx=0 fallback은 재현하지 않음)", "(사용자 확정 2026-08-07). … C++(local_opt.cpp)에 검사가 없는 것은 검증을 생략한 것일 뿐이다" |

전부 "누가 언제 결정했다 / 예전엔 어땠다"라는 결정 이력이며, 규칙 ㉮에 따라
`_pm/DONE.md`와 git이 담당할 내용이다. 결정 **내용**만 남기고 날짜·주체·리뷰 태그를
지우면 된다.

---

## 발견 표

| 심각도 | 문제 | 위치 |
|---|---|---|
| MEDIUM-1 | `_git_commit_hash()`가 working tree dirty 여부를 기록하지 않아, 미커밋 코드 변경 상태로 돌린 실험의 `code commit:` 줄이 실제 코드와 다른 커밋을 가리킨다 (현 저장소가 dirty 상태) | `run.py:413~420` (사용처 `run.py:530`) |
| MEDIUM-2 | `_git_commit_hash()`가 `OSError`만 잡아 `subprocess.TimeoutExpired`가 전파되고, 이 호출이 CSV 저장보다 먼저라 예외 시 전 실험 결과가 유실된다 | `run.py:413~420`, `run.py:530` vs `534~536` |
| LOW-1 | run 기본값 리터럴(50 / 20000 / 128)이 검증·사용·표시 3곳에 복제되어 한쪽만 바뀌면 요약이 조용히 거짓을 찍는다 (현재는 3곳 모두 일치) | `run.py:231~233`, `369~371`, `325~327` |
| LOW-2 | 요약에 없는 항목: `print_progress`, `output.dir`/`label`/`csv_prefix`, H-matrix 파일명, LLR matrix 전체 경로와 "생성 후 로드"였다는 사실 | `run.py:310~330`, `pcm.py:108`, `run.py:303` |
| LOW-3 | `max_iter`가 요약 2·3행에 중복 표시 (두 값은 `decoder.py:116` 때문에 항상 동일) | `run.py:320,323` |
| LOW-4 | 채널 설명 줄이 `label`과 중복 회피 접미사를 반영하지 않아, 같은 type 채널 2개는 요약에서 구분되지 않는다 | `run.py:313~315` vs `run.py:387~393` |
| LOW-5 | JSON 키 `points` → 결과 dict 키·CSV 열 `param`으로 용어가 바뀐다 (요약도 `points`, CSV는 `param`) | `run.py:405`, `sim.py:108` |
| LOW-6 | 이름 스윕 미적용 잔존: `tools/H_mat_gen/*`의 `rng`, `run.py:501~504`의 `r`/`f`, `run.py:425`의 `f`/`t` | 표 참조 |
| LOW-7 | 모듈 docstring에 `run.max_frames`와 `output.csv_prefix` 설명 누락 (둘 다 유효 키이며 `max_frames`는 측정량을 좌우) | `run.py:31~35`, `41~43` vs `_RUN_KEYS run.py:68`, `_OUTPUT_KEYS run.py:70` |
| LOW-8 | 채널·포인트별 난수 파생 seed가 `int(1e6 * point)`라, RBER가 1e-6 미만이면 서로 다른 포인트가 같은 스트림을 공유한다 | `run.py:398` |
| LOW-9 | 문장 규칙 ㉮ 위반 8건, ㉯ 위반 1건 (D절) | D절 표 |
| LOW-10 | `llr_tables.py`(2_LDPC_light 루트)가 삭제된 `llr/*.txt` 프로파일을 읽는 고아 모듈로 남아 있다 (`LDPC_base` 어디에서도 import하지 않음) | `llr_tables.py:1~15` |

**HIGH·CRITICAL 없음.** 요약 출력이 실제와 다른 값을 찍는 사례는 발견되지 않았다.

---

## 상세

### MEDIUM-1 — dirty 상태 미표시

```python
def _git_commit_hash():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], ...).stdout.strip() or "(git 없음)"
    except OSError:
        return "(git 없음)"
```

`report()`가 이 값을 `code commit:`으로 summary.txt 첫머리에 적는다(`run.py:530`).
요약의 목적이 "이 결과를 다시 만들려면 무엇이 필요한가"인데, 미커밋 변경이 있으면
그 커밋만으로는 재현되지 않는다. 지금 이 저장소가 정확히 그 상태다
(`git status`: `M 2_LDPC_light/config.json`, `M 2_LDPC_light/_pm/TODO.md`).

수리 방향: `git status --porcelain`(또는 `git describe --dirty`)를 함께 조회해
dirty면 `e6282b1+dirty` 형태로 적는다.

### MEDIUM-2 — 결과 유실 경로

`report()`의 순서는 ㉮ 실행 폴더 생성 → ㉯ config 사본 복사 → ㉰ `lines` 조립
(여기서 `_git_commit_hash()` 호출) → ㉱ CSV 저장 루프 → ㉲ summary.txt 기록이다.
㉰에서 예외가 나면 몇 시간짜리 측정 결과가 통째로 사라진다. `_git_commit_hash()`가
`except OSError`만 잡으므로 `subprocess.TimeoutExpired`는 잡히지 않는다.
`except (OSError, subprocess.SubprocessError)`로 넓히면 해결된다.

### LOW-8 — 난수 스트림 충돌 조건

`np.random.default_rng([seed, channel_index, int(1e6 * point)])`에서 `int(1e6 * point)`가
0이 되는 구간(`point < 1e-6`)의 서로 다른 RBER 값들은 동일한 seed 벡터를 만든다.
검증은 `0 < p < 0.5`만 요구하므로(`run.py:140~144`) 설정상 가능하다. 실제로 그런
RBER를 측정하려면 프레임 수가 비현실적으로 커야 하므로 우선순위는 낮다.
