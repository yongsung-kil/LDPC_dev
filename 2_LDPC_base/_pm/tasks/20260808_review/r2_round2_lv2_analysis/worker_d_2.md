# Round 2 / 팀 D 워커 2 — 관점 H 전반부 (문서와 코드의 사실 일치)

> 담당: `README.md`, `docs/plan.md`, `docs/차이.md`, `Ideas/vanilla/README.md`,
> `tools/H_mat_gen/README.md`, `LDPC_base/decoder.py` 모듈 docstring, `_pm/TODO.md`,
> `config.json`, `Ideas/vanilla/config.json`의 서술을 코드로 대조

## 검증에 쓴 실행 (전부 scratchpad 출력, 저장소 파일 무수정)

- ㉮ `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code <scratchpad>/out/test.qc`
  → `base 18x147, z=256, rate=0.8776, lifted 4-cycles: 0` 저장 성공
- ㉯ `load_config`에 shipped `config.json` + `use_input_llr_matrix=false` 투입
  → 생성 경로 `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt` (존재하지 않음)
- ㉰ 커밋된 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`를 입력 파일로 지정해 `setup` + `decoder_main`
  → `mode=HD (ch1+th31)`, `edge_mag len = 32`, 8프레임 전부 복호 성공
- ㉱ `QCCode.load('Input/H_matrix/example_18x147_z256.qc')`
  → `col_deg` 내림차순 True, `dv_max=4`
- ㉲ `load_config('Ideas/vanilla/config.json')` → H/LLR 모두 존재, out = `Ideas/vanilla/Sim_Output`

---

## 확인 항목별 근거

### ㉮ "3-bit 전용" 서술의 사실성 — **사실과 다름**

`decoder.py:144-163 _vnu_quantize`는 `self._edge_mag` 길이만큼 캐스케이드를 돈다
(`for k in range(len(edge_mag) - 2, -1, -1)`). 레벨 개수는 고정이 아니다.
`llr_matrix.py:49-51 uniform_edge_mag(top_level)`이 `[top_level..1, 0]`을 만들고,
`load()`는 파일명에 `uniform`이 있으면 `uniform_edge_mag(num_param - ch_len)`을 쓴다
(`llr_matrix.py:170, 202-203`). 실행 ㉰에서 32레벨(th 31개) 매트릭스로 복호가 성립했다.

th 3개 강제 에러는 `llr_matrix.py:67-71`의 **`edge_mag is None`일 때만** 발생한다.
그 조건은 파일명에 `uniform`이 없는 파일 로드 경로에 한정되고, uniform 파일 로드와
`make_internal_uniform_matrix` 합성은 그 분기에 들어가지 않는다.

→ `README.md:162`, `docs/차이.md:25`(#9)는 조건 없이 "고정/전용"이라 단정한다.
`decoder.py:150-151`은 반대로 "레벨 값과 개수는 llr_matrix.edge_mag가 결정한다"로
코드와 맞는다. 즉 문서 간 정면 충돌이다.

부수로 `docs/차이.md:34`(등가 #4 `EDGE 7`), `docs/차이.md:37`(등가 #7 `→7/5/3/1`)도
3-bit 수치를 못 박고 있는데, 실제 RESET은 `edge_mag[0]`(`decoder.py:208, 240`)이라
6-bit 균일 구성에서는 31이다.

### ㉯ 생성 파일 예시 삼자 관계 — **어긋남**

| 자리 | 값 |
|------|-----|
| `README.md:71` 예시 파일명 | `LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt` |
| `config.json:33` `internal_quantize.max_iter` | `120` |
| 저장소 커밋 파일 | `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` |

README 예시와 config.json은 일치하고, **커밋된 파일만 어긋난다**.
실행 ㉯로 확인한 결과, shipped config.json에서 플래그만 false로 바꾸면
`run.py:209-215`가 `..._iter120.txt` 이름을 만들고 `run.py:301-302`가
`Input/LLR/`에 새로 쓴다. `Input/LLR/`은 gitignore 대상이 아니라(루트 `.gitignore`
확인) **추적 폴더에 미추적 파일이 생기고**, 커밋된 `iter30` 파일은 저장소의 어떤
config도 참조하지 않는 사문화 데이터로 남는다.

### ㉰ 교체 지점 표 3곳 — **일치**

`README.md:117-125`와 `LDPC_base/decoder.py:47-55`의 표는 7행 전부 문자열까지 동일하다.
`Ideas/vanilla/README.md:24`는 자체 표 없이 "교체용 함수 목록과 C++ 대응은
`LDPC_base/decoder.py` 모듈 docstring의 표 참조"로 넘긴다 (`Ideas/registry.py:6`도 동일).
표에 적힌 6개 메서드가 모두 `decoder.py`에 존재하고 서술과 맞는다:
`_c2v_reconstruct`(:130), `_vnu_quantize`(:144), `_vn_decide`(:139), `_cnu_update`(:165),
`_column_order`(:126), `_is_edge_clear_iter`(:121), 그리고 `LLRMatrix.row_index`(`llr_matrix.py:284`).

다만 `README.md`에는 이 표가 `decoder.py` docstring의 사본이라는 표시가 없어
정본이 어디인지 README만 봐서는 알 수 없다 (vanilla README와 registry.py는 밝힘).

### ㉱ README JSON 스키마 vs run.py 키맵

| 섹션 | 코드 키맵 | README | 판정 |
|------|-----------|--------|------|
| 최상위 `_TOP_KEYS` | H_matrix, decoder, channels, run, output, seed, log | 7개 전부 | 일치 |
| `_DECODER_KEYS` | llr_matrix, type, use_input_llr_matrix, internal_quantize | 4개 전부 | 일치 |
| `_INTERNAL_QUANTIZE_KEYS` | num_bits, channel_llr, max_iter, mode | 4개 전부 | 일치 |
| `_RUN_KEYS` | max_frame_errors, max_frames, frames_per_batch, stop_below_fer, **print_progress** | print_progress 없음 | **누락** |
| `_OUTPUT_KEYS` | dir, csv_prefix, label | 예시엔 dir/csv_prefix, label은 :89에 설명 | 일치 |
| `_LOG_KEYS` | 7개 | 7개 전부 | 일치 |
| `_CHANNEL_KEYS` | type/points/label (+strong_error SER/SCR) | :76-77 동일 | 일치 |

문서에만 있고 코드에 없는 키: 없음.

`use_input_llr_matrix=false`일 때 `llr_matrix`가 "무시된다"는 서술은 **사실이 아니다**.
`run.py:206-208`이 `decoder_config["llr_matrix"]["dir"]`를 읽어 생성 파일의 저장
폴더를 정한다. 실행 ㉯에서 llr_matrix 키를 지우면 저장 위치가 config 파일 옆의
`Input/LLR`로 바뀌는 것을 확인했다. 즉 `file`만 무시되고 `dir`는 살아 있다.

### ㉲ README의 `Input/` 설명

- `Input/H_matrix/` (`README.md:14`): 실제 파일 헤더가 `147 18 / 4 31 / 256 / 빈 줄 / 행렬`로
  Ref-C 포맷과 일치(`pcm.py:60-79`). `col_deg` 내림차순도 실행 ㉱로 확인. **일치**
- `Input/LLR/` (`README.md:15`): 추적 파일이 3개인데 2개만 적혀 있다.
  `HD_0.txt`는 num_restart=1(restart iter 2), 마지막 iter_end=5 → "restart 포함 토이" 맞음.
  `HD_1.txt`는 restart 0개, 마지막 iter_end=20 → "restart 없는 20-iter 테스트용" 맞음.
  세 번째 `..._uniform_6bit_ch8_iter30.txt`가 **미기재**이고, 이 폴더가 생성 파일이
  쌓이는 자리라는 성격도 적혀 있지 않다.
- `README.md:10-19` 구성 표에 `llr_tables.py`(2_LDPC_light 루트, git 추적 중)가 없다.
  이 모듈은 어떤 코드도 import하지 않고(전수 grep 확인), docstring이 가리키는
  `2_LDPC_light/llr/*.txt` 폴더도 없다. `_pm/DONE.md:70`은 이 파일을 "삭제"했다고 기록한다.

### ㉳ `docs/plan.md` §3.1 구 모듈 표 — **어긋남, 단서가 부족**

머리 단서(`plan.md:4-6`)는 "§3.1 모듈 표 등 구조 서술은 개편 전 기준이며,
결정 이력(§1, §7)은 계속 유효"라고 적는다. 실제 어긋남 범위는 §3.1보다 넓다.

| plan.md 서술 | 현 상태 |
|---|---|
| §3.1 `config.py` | 없음 (JSON config로 대체) |
| §3.1 `mpi_runner.py` | 삭제 (TODO.md:25-26 재설계 대기) |
| §3.1 `llr_tables.py` | 파일은 남았으나 고아 모듈 |
| §3.1 나머지 6개 (pcm/encoder/channel/decoder/sim/run) | `LDPC_base/`로 이동 |
| §3.1 불릿 "아이디어별 코드는 `2_LDPC_light/ideas/` 하위" | 실제 `Ideas/` (대문자, registry 방식) |
| §3.1b `tools/peg.py`, `tools/lifting.py`, `tools/gen_example_code.py` | `tools/H_mat_gen/`로 이동 |
| §3.1b `examples/fer_curve.py` | 삭제 (폴더 없음) |
| §3.2 "`two_set`(flooding 등가)은 비교용으로 유지" | `two_set` 스케줄 없음 |
| §5 진행 순서 2 "예시 FER 테스트 (완료)" / 4 "mpi_runner + 슈퍼컴 반입" | 대상 파일 삭제됨 |

단서가 §3.1만 이름으로 지목하는데 §3.1b 표는 4행 전부 어긋났고, §3.2·§5도 어긋난다.

더 문제인 것은 단서가 **§7은 계속 유효하다고 못 박는데** §7 #4
"시뮬 파라미터 **max_iter = 120** (2026-07-30 사용자 지정)"이 현행 규약과 충돌한다는
점이다. 현재 max_iter는 LLR matrix가 결정하고(`decoder.py:116`, `llr_matrix.py:92`),
JSON에 `decoder.max_iter`를 쓰면 에러다(`run.py:178-181`). 기본 config가 쓰는
`HD_1.txt`의 max_iter는 20이다.

### ㉴ `tools/H_mat_gen/README.md`의 시제 — **미래형이 현 상태와 어긋남**

`README.md:15-17` ㉰: "`select_irregular.py`는 구 본체 API 기준 —
`_test/20260806_setup_구성_실험/LDPC_base` 개정본을 **본체로 반영할 때** 새 구조로
손봐야 실행된다". 본체 반영은 2e600ea/3f596ef로 이미 끝났고 그 `_test/` 경로는 없다.
같은 사실을 `select_irregular.py:14-16`은 "이 스크립트는 구 본체 API 기준이라
**현재 실행 불가**"로, `_pm/TODO.md:22-24`도 "현재 실행 불가"로 현재형으로 적는다.
README만 시제와 참조 경로가 뒤처졌다.

실행 명령은 **성립한다**: `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code [출력경로]`가
실제로 동작함을 실행 ㉮로 확인했다(상대 임포트 `from ...LDPC_base.pcm import QCCode`가
repo 루트 기준 패키지 실행에서 해석됨). ㉯의 "출력 기본 위치는 이 폴더의 `out/`"도
`gen_example_code.py`의 `default_out`(= `<H_mat_gen>/out/example_18x147_z256.qc`) 및
루트 `.gitignore`의 `out/`와 일치한다.

### ㉵ `Ideas/vanilla/README.md`의 실행 안내 경로 — **무효 경로**

`Ideas/vanilla/README.md:13`: "실험 루트(`_test/20260806_setup_구성_실험/`)에서:".
그 경로는 존재하지 않으며 `_test/`는 gitignore 대상이다. 현 실험 루트는 `2_LDPC_light/`다
(`README.md:23`, `run.py:9`).
`Ideas/vanilla/config.json`의 `_desc`는 "실험 루트"라고만 적어 경로를 박지 않았고,
상대경로 `../../Input/H_matrix`, `../../Input/LLR`, `output.dir: "Sim_Output"`는
실행 ㉲로 전부 유효함을 확인했다. 즉 config는 맞고 README 문장만 틀렸다.

### ㉶ `docs/차이.md` 머리말 — 경로는 맞음, 파생 시점 서술이 낡음

- "이 폴더의 `LDPC_base/decoder.py` `decoder_main()`" → 파일·함수 모두 존재. **일치**
- "본체 커밋 72b825a에서 파생하여 2026-08-06 개정" → 72b825a는 실재
  (`refactor(2_LDPC_light): 실행 흐름을 JSON 설정 기반 4단계 구조로 재편`).
  다만 그 뒤 2e600ea → d42ca8c → 01251f5 → e6282b1로 4회 더 갱신됐고 그 델타(균일
  n-bit 양자화)가 #9 등에 반영되지 않았다. 또 CLAUDE.md 문장 규칙 ㉮(과거 서술을
  코드·문서에 남기지 않음)와도 어긋난다.
- 줄번호 표본: 차이.md 자체는 C++ 함수명만 인용하고 줄번호는 없다. `decoder.py`가 든
  줄번호는 확인했다. `decoder.cpp:4044` = `VN_Cal_HD`의 `sum_t > 0` 판정부 **맞음**,
  `decoder.cpp:4112-4115` = 3-bit 캐스케이드 `th1→EDGE_MAG_7 … else EDGE_MAG_1` **맞음**.

### ㉷ README의 TODO 참조 — **일치**

- `README.md:106` "후순위 로그 7종은 미구현" ↔ `_pm/TODO.md:28-29`의 7개
  (bit_err_by_col, flip_count_per_iter, table_row_history, min_sum_stats,
  fail_frame_positions, fail_frame_seed, channel_stats). 개수·성격 모두 맞음
- `README.md:150` "2SD/3SD는 채널 출력까지만 준비 — 디코더가 HD 전용이라 현재 실행 불가"
  ↔ `_pm/TODO.md:16-18`, `decoder.py:371-374`의 명시적 `NotImplementedError`. 맞음

### 추가로 확인해 문제 없던 것

- `README.md:91-100` 실행 폴더 산출물 목록 7종이 `run.py:517-567`의 저장 파일과 전부 일치
- `README.md:103` "post_fec_ber는 로그와 무관하게 항상 FER CSV에 포함" ↔ `sim.py:84, 108-114` 일치
- `README.md:82-84` 설정 검증 서술(키맵 + 필수값 + 값 제약, `_` 시작 키 무시) ↔
  `run.py:83-107` 일치
- `README.md:144-148` 채널 3종 표 ↔ `channel.py` 대응 (팀 워커1 범위와 중복이라 표만 대조)

---

## 발견 목록

| # | 심각도 | 문제 | 위치 | 근거 |
|---|--------|------|------|------|
| D2-1 | HIGH | "VNU 출력 레벨 {7,5,3,1} 고정 — 3-bit 전용"은 사실이 아니다. 균일 n-bit 경로에서 레벨 수가 `edge_mag` 길이로 정해진다 | `README.md:162` | `decoder.py:144-163` 캐스케이드가 `len(edge_mag)` 기준. 실행 ㉰에서 32레벨 복호 성공. 같은 README의 `:66-71`이 n-bit를 설명해 자기모순 |
| D2-2 | HIGH | "**3-bit 전용** (EDGE {7,5,3,1} 고정, **th 3개 아니면 에러**)" — 그 에러는 uniform 표시가 없는 파일 로드에만 걸린다. 한정 조건이 빠져 있다 | `docs/차이.md:25` (#9) | `llr_matrix.py:67-71`은 `edge_mag is None`일 때만 raise. `load()`는 `:170,202`에서 uniform 파일에 edge_mag를 채우고, `make_internal_uniform_matrix`(`:229-231`)도 넘긴다 |
| D2-3 | HIGH | "`llr_matrix` 키는 있어도 무시된다 (플래그만 바꿔 토글 가능)" — `llr_matrix.dir`는 생성 파일의 저장 폴더로 실제 사용된다 | `README.md:70` | `run.py:206-208`. 실행 ㉯: dir 지정 시 그 폴더, 키 삭제 시 `<config dir>/Input/LLR`로 저장 경로가 바뀜. `run.py:17-19`와 `config.json:19-20`도 "무시"라 쓴 뒤 다음 줄에서 `llr_matrix.dir`를 지목해 자체 모순 |
| D2-4 | HIGH | "본체로 반영**할 때** 손봐야 한다"는 미래형이 이미 끝난 반영을 가리키고, 존재하지 않는 `_test/20260806_setup_구성_실험/` 경로를 참조한다 | `tools/H_mat_gen/README.md:15-17` | 반영 커밋 2e600ea·3f596ef. 같은 사실을 `select_irregular.py:14-16`과 `_pm/TODO.md:22-24`는 "현재 실행 불가"로 현재형 서술 |
| D2-5 | HIGH | 실행 안내가 존재하지 않는 `_test/20260806_setup_구성_실험/`를 실험 루트로 지목한다 (따라 하면 실행 불가) | `Ideas/vanilla/README.md:13` | 현 실험 루트는 `2_LDPC_light/` (`README.md:23`, `run.py:9`). config.json 상대경로는 실행 ㉲로 유효 확인 — README만 틀림 |
| D2-6 | MEDIUM | 커밋된 uniform 파일(`iter30`)이 README 예시(`iter120`)·`config.json:33`(120)과 어긋나, 플래그를 false로 바꾸면 추적 폴더에 미추적 `iter120` 파일이 새로 생기고 커밋 파일은 쓰이지 않는다 | `README.md:71`, `config.json:33`, `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` | 실행 ㉯. `run.py:209-215, 301-302`. `Input/LLR/`은 gitignore 비대상 |
| D2-7 | MEDIUM | `Input/LLR/` 설명이 커밋된 3개 중 2개만 담고, 생성 파일이 쌓이는 폴더라는 성격도 없다 | `README.md:15` | `git ls-files Input/`에 uniform 파일 포함. HD_0(restart 1개, iter_end 5)/HD_1(restart 0, iter_end 20) 서술 자체는 파일 내용과 일치 |
| D2-8 | MEDIUM | 구성 표에 `llr_tables.py`가 없다. 이 모듈은 어디서도 import되지 않고 docstring이 없는 폴더(`2_LDPC_light/llr/`)를 가리킨다 | `README.md:10-19`, `llr_tables.py:1` | 전수 grep에서 import 0건. `_pm/DONE.md:70`은 "llr_tables.py 삭제"로 기록했으나 파일은 추적 중 |
| D2-9 | MEDIUM | `run.print_progress`가 스키마 예시·설명 어디에도 없다 (코드 키맵과 run.py docstring에는 있음) | `README.md:50-51, 78-81` | `run.py:68-69 _RUN_KEYS`, `run.py:35`, `run.py:373` |
| D2-10 | MEDIUM | `use_input_llr_matrix=false`에서 생성 파일이 **어디에** 저장되는지 README가 말하지 않는다 (추적 폴더에 쓰이므로 알아야 할 정보) | `README.md:66-71` | `run.py:205-215`. `config.json:20`과 `run.py:18-19`에만 기재 |
| D2-11 | MEDIUM | plan.md 머리 단서가 "결정 이력 §7은 계속 유효"라고 못 박는데 §7 #4 `max_iter = 120`은 현행 규약(LLR matrix가 결정, JSON에 두면 에러)과 충돌한다 | `docs/plan.md:4-6, 129` | `run.py:178-181`, `decoder.py:116`, `llr_matrix.py:92`, `docs/차이.md:40`(#10). 기본 config의 HD_1.txt는 max_iter 20 |
| D2-12 | MEDIUM | 단서가 §3.1만 지목하는데 §3.1b 표 4행 전부, §3.2 `two_set`, §5 진행순서까지 어긋난다 | `docs/plan.md:4-6, 70-79, 84, 110-112` | `examples/`, `config.py`, `mpi_runner.py` 없음(확인). peg/lifting/gen_example_code는 `tools/H_mat_gen/`. `two_set` 미존재 |
| D2-13 | MEDIUM | 등가 항목 #4가 RESET을 "EDGE 7"로 못 박는다. 실제 RESET은 `edge_mag[0]`이라 6-bit 균일 구성에서 31 | `docs/차이.md:34` | `decoder.py:208, 240` `RESET = np.float32(self._edge_mag[0])` |
| D2-14 | MEDIUM | 등가 항목 #7이 양자화를 "→7, →5, →3, →1" 4레벨로 못 박는다. 실제는 임의 길이 캐스케이드 | `docs/차이.md:37` | `decoder.py:154-157` |
| D2-15 | MEDIUM | "내부 합성 — **파일 없이** 균일 n-bit 양자화로 디코딩할 때"가 현재 흐름(합성 → 파일 저장 → 파일 로드)과 반대다 | `LDPC_base/llr_matrix.py:5-7` | 같은 파일 `:212-213`이 "save()로 DAO 포맷 파일로 저장한 뒤 load()로 읽어"라 적고, `run.py:294-304`가 그대로 실행. 커밋 e6282b1의 변경 취지 |
| D2-16 | MEDIUM | th 배열 shape 주석이 `3`으로 고정돼 있다 (실제 마지막 축은 `th_len`, 6-bit 구성에서 31) | `LDPC_base/decoder.py:256` | `state.cur_th = self.llr_matrix.row_th[table_row_idx]  # (num_active_frames, num_dv, 3)`. `llr_matrix.py:89` `row_th`의 마지막 축은 `th_len` |
| D2-17 | LOW | "파일 로드 — DAO 산출물, 3-bit(th 3개, EDGE {7,5,3,1}) 구성"이 uniform 파일 로드 경로를 배제한다 | `LDPC_base/llr_matrix.py:4` | 같은 파일 `:160-164, 202-203`이 uniform 파일 로드를 명시 |
| D2-18 | LOW | README의 교체 지점 표에 정본 표시가 없어 `decoder.py` docstring 표와 이중 관리된다 (현재는 내용 일치) | `README.md:117-125` | `Ideas/vanilla/README.md:24`, `Ideas/registry.py:6`은 `decoder.py` docstring을 정본으로 지목 |
| D2-19 | LOW | "본체 커밋 72b825a에서 파생하여 2026-08-06 개정"이 이후 4개 커밋의 변경을 담지 못하고, 과거 서술을 문서에 남기지 않는다는 문장 규칙과도 어긋난다 | `docs/차이.md:4-5` | 72b825a 이후 2e600ea, d42ca8c, 01251f5, e6282b1. `CLAUDE.md` 문장 작성 규칙 ㉮ |

**집계**: 총 19건 — HIGH 5, MEDIUM 11, LOW 3.

**공통 뿌리 2개**
- ㉮ 균일 n-bit 양자화(01251f5, e6282b1) 도입 시 `decoder.py`/`llr_matrix.py` 본문 주석은
  일반화됐으나 `README.md`·`docs/차이.md`의 3-bit 서술이 그대로 남았다 (D2-1, D2-2, D2-13, D2-14, D2-16, D2-17)
- ㉯ 본체 반영(2e600ea, 3f596ef) 시 `tools/H_mat_gen/README.md`와 `Ideas/vanilla/README.md`의
  `_test/...` 경로·시제가 갱신되지 않았다 (D2-4, D2-5)
