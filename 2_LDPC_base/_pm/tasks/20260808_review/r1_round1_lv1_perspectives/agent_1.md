# Round 1 관점 도출 (에이전트 1)

> 대상: `git diff ea88882..HEAD -- 2_LDPC_light/` + 미커밋 `2_LDPC_light/config.json`
> 목적: 어디를 봐야 하는지만 도출한다. 문제 판정은 Round 2 이후의 몫이다.
> 델타 5갈래: ㉮ 본체 반영·패키지화 ㉯ 가독성 리팩토링(단계별 함수 추출) ㉰ 의견1 반영(이름 명확화, 요약 출력)
> ㉱ 내부 균일 n-bit 양자화 모드 ㉲ 균일 매트릭스 파일 생성 후 로드 방식

---

## P1. 균일 양자화 매트릭스의 합성 → 저장 → 재로드 왕복 정합성

이번 델타의 심장부다. 합성 객체와 파일을 거쳐 복원된 객체가 같은 것인지가 전체 모드의 전제다.

**확인 항목**

- ㉮ `make_internal_uniform_matrix()`가 만든 객체와 `save()` 후 `load()`로 복원한 객체가 필드별로
  같은가 (`num_param`, `th_len`, `edge_mag`, `row_ch`, `row_th`, `dv_from/dv_to`, `max_iter`,
  `group_type`, `restart_iters`)
- ㉯ `edge_mag` 복원 경로: 합성 쪽은 `uniform_edge_mag(top_level)`, 로드 쪽은
  `uniform_edge_mag(num_param - MODE_CH_LEN[mode])`로 서로 다른 식을 쓴다. 두 식이 같은 값을 내는
  조건(`num_param = ch_len + top_level`)이 항상 성립하는지, HD 외 모드(`ch_len` 2, 4)에서도 성립하는지
- ㉰ `save()`가 기록하지 않는 정보가 복원에 필요한지: `edge_mag`, `mode`, `is_uniform`은 파일 본문에
  없고 파일명에서만 온다. 파일명 규약이 유일한 전달 통로인 설계의 취약점
- ㉱ `is_uniform` 판정이 `"uniform" in basename.lower()` 문자열 포함 검사다. 사람이 만든 3-bit 파일에
  uniform이 우연히 들어간 경우, 반대로 생성 파일이 이름 변경으로 표시를 잃은 경우의 결과
  (전자는 `th_len != 3` 검사를 우회하고, 후자는 `NotImplementedError`로 떨어진다)
- ㉲ `restart_iters`가 빈 `set`일 때 `save()`가 restart 줄을 생략하고 `load()`가 `num_restart > 0`에서만
  줄을 읽는 대칭 처리. `if self.restart_iters:`가 빈 집합에서 의도대로 동작하는지
- ㉳ `save()`의 tail 고정값: `floor_flag`를 원본 값 대신 항상 `-1`로 적는다. 로드한 파일을 다시
  저장하면 floor 값이 소실되는데, 왕복 저장이 일어날 수 있는 경로가 있는지
- ㉴ `save()`가 `int()` 캐스팅으로 값을 정수화한다. `row_values`가 `float32`라서 큰 정수에서 정밀도가
  깎이는 지점이 있는지 (`top_level`이 num_bits 커질 때 몇까지 안전한가)
- ㉵ `max_value` / `min_value`의 의미와 합성값 `[max(top_level, channel_llr)] * num_param`의 타당성.
  ch 열과 th 열이 서로 다른 도메인인데 한 값으로 채우는 것이 DAO 규칙에 맞는지, 그리고 이 두 필드를
  코드가 실제로 소비하는 곳이 있는지 (없다면 무의미한 값이 파일에 남는다)

**대상**: `LDPC_base/llr_matrix.py` (`uniform_edge_mag`, `__init__`, `load`, `save`,
`make_internal_uniform_matrix`), `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`

---

## P2. 균일 n-bit 양자화의 수치 의미

th를 정수 `[top_level..1]`로 두고 레벨을 `[top_level..0]`으로 둔 설계가 "균일 양자화"라는 이름값을
하는지 확인한다.

**확인 항목**

- ㉮ 캐스케이드 소비가 `|raw|`의 상한 클리핑과 같아지려면 `raw`가 정수여야 한다는 전제
  (docstring 주장). `sum_t`가 정수를 유지하는 경로 전부를 따라간다: ch(정수) + Σ vnu_in(레벨 정수),
  `np.roll` 후에도 값 보존, `float32` 누적에서 정수성이 깨지는 크기 한계 (`num_bits`가 커질 때)
- ㉯ 최소 레벨 0의 도입 효과. DAO 3-bit 파일은 최소 레벨이 1이라 magnitude 0인 메시지가 없지만,
  균일 모드는 0이 나온다. mag 0이 `min1`/`min2`에 들어가면 그 CN의 모든 C2V가 0이 되어 해당
  check node가 사실상 침묵한다. 이것이 의도된 동작인지, 원본 HW 의미와 어긋나는지
- ㉰ `raw == 0`일 때 sign을 `vnu_in`에서 가져오는 기존 규칙이 mag까지 0인 균일 모드에서 의미가 있는지
- ㉱ `RESET = edge_mag[0] = top_level`이 균일 모드의 min1/min2 초기값과 Edge Clear 값이 된다.
  3-bit의 `V_VERY_STRONG=7` 대응을 n-bit로 확장한 것이 타당한지, restart row의 `th=-1` 관례와
  균일 모드(restart 없음)의 관계
- ㉲ `channel_llr`이 전 dv 공통 단일 값이라는 제약. TODO에 등록된 반전 가능 조건 `ch <= 7·dv`의 n-bit
  일반화(`ch <= top_level·dv`)를 균일 모드가 만족하는지, `dv_min`이 작은 부호에서 채널값이 압도하지
  않는지 (예시 부호 dv=2, `channel_llr=8`, `top_level=31`)
- ㉳ 경계 파라미터: `num_bits=2`(top_level 1, th 1개, 레벨 {1,0}), `num_bits`가 큰 값(row 길이와 양자화
  루프 반복 수가 함께 커진다)에서의 동작과 비용

**대상**: `LDPC_base/llr_matrix.py:210-231`, `LDPC_base/decoder.py` (`_vnu_quantize`, `_cnu_update`,
`_init_state`의 RESET)

---

## P3. `_vnu_quantize` 캐스케이드 일반화의 정확성

th 3개 고정에서 th n개로 푼 변경이 3-bit 파일 경로의 기존 동작을 그대로 재현하는지 본다.

**확인 항목**

- ㉮ 역순 루프 `for k in range(len(edge_mag) - 2, -1, -1)`가 C++ elif 체인(위쪽 th의 참 조건 우선)과
  같은 결과를 내는지. th가 비단조일 때도 같은지 (`_validate`는 경고만 내고 통과시킨다)
- ㉯ `th[:, k, None]` 브로드캐스트가 `mag_in`의 shape `(num_active_frames, z)`와 맞는지, th 배열이
  `(num_active_frames, th_len)`로 들어오는 경로(`state.cur_th[:, dv_idx, :]`)의 축 정합
- ㉰ `edge_mag` 길이와 `th_len + 1`의 일치를 `__init__`이 강제하는데, 서브클래스가 `_vnu_quantize`만
  갈아끼울 때 이 불변식이 유지되는지
- ㉱ `_run_iteration`의 주석 `state.cur_th ... (num_active_frames, num_dv, 3)`에 3이 남아 있다.
  일반화 이후의 실제 shape와 주석의 일치
- ㉲ `mag`를 `np.full_like(mag_in, edge_mag[-1])`로 시작하는데 `mag_in`은 float32, `edge_mag`도 float32다.
  dtype 승격이나 정밀도 손실이 생기는 지점이 있는지

**대상**: `LDPC_base/decoder.py:144-163`, `LDPC_base/decoder.py:254-256`

---

## P4. `use_input_llr_matrix` 분기의 설정 처리와 파일 생성 부작용

config 검증 단계에서 파일 경로를 만들고 setup 단계에서 실제 파일을 쓰는 2단 구조를 확인한다.

**확인 항목**

- ㉮ `load_config`가 `decoder_config["generated_llr_matrix_path"]`를 주입한다. 이 키는
  `_DECODER_KEYS`에 없는데, config dict를 다시 검증하는 경로가 있는지 (`report`는 원본 파일을
  `shutil.copy`하므로 무관하지만, 재실행·재검증 흐름에서 걸릴 여지)
- ㉯ `use_input_llr_matrix=false`일 때 `llr_matrix` 키의 처리. `isinstance(..., dict)` 검사만 하고
  `dir` 이외의 키는 검증하지 않는다. 잘못된 형태(문자열, null)를 조용히 무시하는 범위
- ㉰ 생성 경로가 `llr_matrix.dir`을 재활용한다. 그 dir이 없으면 `Input/LLR`을 기본값으로 쓰는데,
  두 config(루트와 `Ideas/vanilla/`)에서 상대경로 기준(config 파일 위치)이 서로 다르게 풀리는지
- ㉱ 파일명이 `{mode}_{num_bits}bit_ch{channel_llr}_iter{max_iter}`만 담는다. `dv_max`는 H-matrix에서
  오는데 이름에 없다. 다른 H-matrix로 같은 파라미터를 돌리면 같은 이름으로 덮어써진다.
  setup이 매번 생성 후 로드하므로 stale 로드는 없지만, 파일명이 내용을 식별하지 못하는 점의 영향
- ㉲ 기존 파일 무경고 덮어쓰기. 사람이 만든 파일과 이름이 충돌할 수 있는지
- ㉳ `internal_quantize.mode`가 `2SD`/`3SD`도 통과하지만 디코딩은 HD 전용이라 `decoder_main`에서
  실패한다. setup 시점(파일까지 만든 뒤)에 실패하는 순서가 적절한지
- ㉴ `_check_int`의 하한값 선택 근거: `num_bits >= 2`, `channel_llr >= 1`, `max_iter >= 1`.
  `channel_llr = 0`(채널 무시)을 막을 이유가 있는지
- ㉵ `print(f"generated LLR matrix: ...")` 출력이 `run.print_progress`와 무관하게 항상 나오는 일관성

**대상**: `LDPC_base/run.py:157-255`(`load_config`), `LDPC_base/run.py:281-307`(`setup`),
`config.json`, `Ideas/vanilla/config.json`

---

## P5. 단계별 함수 추출 리팩토링의 동작 보존

`decoder_main`을 6개 단계로 쪼개면서 상태 전달과 호출 순서가 원래 흐름과 같은지 본다.

**확인 항목**

- ㉮ `_DecodeState`가 클래스 어노테이션만 갖고 실제 할당은 `_init_state`와 `_run_iteration`에서
  일어난다. 어노테이션 목록과 실제 할당 속성의 일대일 대응, 빠진 속성이 접근되는 시점
- ㉯ 호출 순서 의존: `_record_iteration`이 `_check_errors`보다 먼저 호출되어야
  `state.idx_active`가 압축 전 인덱스여야 한다는 전제가 성립한다. 이 순서 제약이 코드나 주석에
  드러나 있는지, 서브클래스가 순서를 바꿀 여지가 있는지
- ㉰ `_check_errors`의 배치 압축 대상 목록(`read_bit`, `syndrome`, `prev_csw`, `min1`, `min2`,
  `min1_pos`, `check_sum`, `edge_sgn`)에 누락이 없는지. `cur_ch`/`cur_th`는 매 iteration 재계산되므로
  제외되는데 그 전제가 항상 참인지 (`_run_iteration` 시작에서 항상 갱신되는가)
- ㉱ `state.num_active_frames`를 `_run_iteration` 진입에서 `read_bit.shape[0]`으로 다시 잡는다.
  압축 직후 iteration에서 shape 정합이 유지되는지
- ㉲ `final_err_bits` / `final_csw` / `final_err_by_dv`의 "마지막 처리 iteration 값" 의미가 압축
  이후에도 지켜지는지 (성공 프레임은 그 iteration의 0이 남고, 실패 프레임은 max_iter의 값이 남는가)
- ㉳ 교체 지점 함수의 시그니처가 state를 받지 않는 형태로 유지되어 아이디어 서브클래스가
  `LDPC_base`를 몰라도 재정의 가능한지. `_cnu_update`만 min1/min2 등 배열을 직접 받아 in-place로
  고치는 비대칭 구조인데, 그 이유와 재정의 난이도
- ㉴ `_build_result`가 만드는 키 집합과 `sim.py`가 읽는 키 집합의 일치
  (`success`, `decode_success_iteration`, `final_err_bits`, `log_active`, `log_csw_sum`,
  `log_err_sum`, `log_err_by_dv_sum`, `final_csw`, `final_err_by_dv`, `profile`)
- ㉵ `log` 항목별 조건 분기가 `_record_iteration`과 `_build_result`에서 짝을 이루는지
  (한쪽만 켜져 KeyError가 나는 조합이 있는지)

**대상**: `LDPC_base/decoder.py:63-100`(`_DecodeState`), `189-351`(단계 함수), `354-387`(`decoder_main`),
`LDPC_base/sim.py:54-94`

---

## P6. 패키지화 이후의 import 체인과 실행 위치 의존성

flat 파일에서 `LDPC_base/` + `Ideas/` + `tools/H_mat_gen/`으로 나뉜 뒤 실행 경로가 성립하는지 본다.

**확인 항목**

- ㉮ `python -m LDPC_base.run config.json`을 `2_LDPC_light/`에서 실행할 때 `Ideas` 패키지가
  `sys.path`에 잡히는 근거(cwd 삽입)와, 다른 위치에서 실행했을 때의 실패 양상
- ㉯ `_resolve_decoder_class`의 `ImportError` 처리 범위. `Ideas` 자체가 없을 때뿐 아니라
  `Ideas/vanilla/decoder.py` 내부 import 실패도 같은 `ImportError`로 잡혀 조용히
  `MinSumDecoder` fallback으로 빠질 수 있는지 (오진 위험)
- ㉰ `Ideas/vanilla/decoder.py`의 절대 import `from LDPC_base.decoder import MinSumDecoder`와
  registry 문자열 `"Ideas.vanilla.decoder:VanillaDecoder"`의 짝. registry 값 파싱(`split(":")`)이
  형식 오류를 어떻게 알리는지
- ㉱ `tools/H_mat_gen/gen_example_code.py`의 `from ...LDPC_base.pcm import QCCode`(3단계 상위)와
  README의 실행 예 `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code`. 저장소 루트에서
  숫자로 시작하는 패키지 이름이 `-m`으로 동작하는지 실제로 확인
- ㉲ `2_LDPC_light/__init__.py`와 `LDPC_base/__init__.py`의 역할 분담. `LDPC_base/__init__.py`가
  `channel`, `encoder`, `sim`을 즉시 import하는데 `run`은 빼놓았다. 순환 import 여부와 그 기준
- ㉳ `Ideas/__init__.py`와 `Ideas/vanilla/__init__.py`의 존재 여부와 내용 (vanilla의 `__init__.py`는
  구 `examples/__init__.py`에서 이름만 옮겨온 rename이다)
- ㉴ `run.py`가 함수 안에서 `import csv`, `import matplotlib`을 하는 지역 import 패턴의 일관성

**대상**: `LDPC_base/run.py:258-278`, `LDPC_base/__init__.py`, `__init__.py`, `Ideas/__init__.py`,
`Ideas/registry.py`, `Ideas/vanilla/decoder.py`, `tools/H_mat_gen/gen_example_code.py`,
`tools/H_mat_gen/select_irregular.py`

---

## P7. config 스키마 검증과 실제 소비의 일치

키맵이 늘어난 만큼 검증부와 소비부가 어긋날 여지가 커졌다.

**확인 항목**

- ㉮ 키맵 6종(`_TOP_KEYS`, `_DECODER_KEYS`, `_INTERNAL_QUANTIZE_KEYS`, `_RUN_KEYS`, `_OUTPUT_KEYS`,
  `_LOG_KEYS`, `_CHANNEL_KEYS`)이 실제 소비 코드가 읽는 키를 빠짐없이 덮는지. 반대로 검증만 되고
  아무도 안 읽는 키가 있는지 (`output.csv_prefix`, `run.print_progress`, `output.label`)
- ㉯ `_desc` 무시 규칙이 중첩 객체 전부에 적용되는지: 최상위, `decoder`, `decoder.llr_matrix`,
  `decoder.internal_quantize`, `run`, `log`, `output`, `channels[]`. `_path_pair` 안의
  `_check_keys(section, d, {"dir", "file"})`가 `_visible`을 거치는지
- ㉰ `_check_channel`이 `channel_config["points"]`를 스칼라에서 리스트로 in-place 정규화한다.
  원본 config dict 변형이 이후 소비(`_experiment_summary_lines`의 `channels_desc`, `report`의
  config 사본)에 미치는 영향
- ㉱ 난수 스트림 파생 `np.random.default_rng([seed, channel_index, int(1e6 * point)])`.
  rber 실수 포인트에서 `1e6` 스케일이 서로 다른 포인트를 같은 정수로 뭉갤 구간이 있는지,
  fixed_error 정수 포인트(200, 300)와 rber 포인트가 같은 정수로 충돌할 수 있는지
- ㉲ `run` 기본값이 `load_config`(검증)와 `run_experiment`/`_experiment_summary_lines`(소비) 세 곳에
  각각 리터럴로 흩어져 있다(50, 20000, 128). 값이 어긋날 여지
- ㉳ `_check_int`가 검증만 하고 정규화된 값을 config에 되쓰지 않는 점 (`seed`만 되쓴다)
- ㉴ `run.stop_below_fer`가 채널 안에서만 break를 걸고 다음 채널로 넘어가는 동작과 문서 서술의 일치
- ㉵ 루트 `config.json`과 `Ideas/vanilla/config.json`의 스키마 동기화. vanilla config에는
  `use_input_llr_matrix`와 `internal_quantize`가 없어 기본값 경로를 타는데, 두 파일이 같은 실험을
  가리키는지 (H_matrix, LLR, channels, seed가 같고 label만 다르다)

**대상**: `LDPC_base/run.py:64-255`, `LDPC_base/run.py:362-410`, `config.json`,
`Ideas/vanilla/config.json`

---

## P8. 요약 출력(의견1 반영)의 정확성과 재현성 가치

`_experiment_summary_lines`가 setup 직후 콘솔과 `summary.txt` 양쪽에 쓰인다.

**확인 항목**

- ㉮ 출력 4종(부호, LLR matrix, 디코더, config)이 의견1의 요구("코드정보, dec정보, 읽은 config정보")를
  덮는지, 빠진 정보(H-matrix 파일 경로, LLR matrix 파일 경로, 균일 모드 여부와 파라미터)가 있는지.
  균일 모드로 돌렸는지 여부가 summary만 보고 판별되는가
- ㉯ `LLRMatrix.summary()`의 그룹 표기(`g1[1~30]x1`)와 restart 표시(`R`) 규칙이 읽는 사람에게
  해석 가능한지. `R` 판정이 그룹 첫 iteration만 보는 방식의 한계
- ㉰ `QCCode.summary()`가 여러 줄을 반환하는데 리스트 원소 하나로 들어간다. `summary.txt`와 콘솔의
  줄 구성이 깨지지 않는지
- ㉱ `report`가 config 사본을 원본 파일 복사로 남기므로 정규화 결과(리스트화된 points, 절대경로,
  기본값 채움)는 사본에 없다. 재현성 목적에서 원본 사본과 정규화 결과 중 무엇이 맞는지
- ㉲ `_git_commit_hash()`가 dirty 상태를 표시하지 않는다. 미커밋 변경으로 돌린 실험의 재현성 서술
- ㉳ 콘솔 출력과 `summary.txt`가 실제로 같은 내용인지 (report는 앞에 run/commit 2줄을 덧붙인다)

**대상**: `LDPC_base/run.py:310-330`, `413-421`, `517-568`, `LDPC_base/pcm.py:105-111`,
`LDPC_base/llr_matrix.py:309-317`

---

## P9. 이름 명확화(의견1) 반영의 완결성

**확인 항목**

- ㉮ 의견1 지적 항목의 개별 반영 확인: `decoder_cls` → `decoder_class`, `mx` → `llr_matrix`,
  `verbose` → `print_progress`, `points` 설명 보강, `rng` → `random_generator`,
  `_make_channel_fn` 결과의 변수화, `unknown` → `unknown_log_items`, `fail_rows` →
  `fail_frame_details`, `agg_*` → `total_*`, `b` → `batch`, `res` → `decode_result`,
  `n_it` → `num_iterations_run`, `frozenset` → `set`, `s` → `state`, `n_active` →
  `num_active_frames`, `used_labels` 분기 주석
- ㉯ 남은 축약어가 프로젝트 규칙("수단이 아니라 목적이 이름")의 허용선 안인지 판단할 후보:
  `chan`(모듈 별칭), `cw`, `hd`/`sd`/`cc`, `e2`/`c1`/`c2`, `J`/`K`, `B`, `z`, `off`, `hit`, `m`,
  `dv`, `csw`, `th`, `ch`, `mag`, `sgn`, `raw`. 원본 C++ 용어 대응이라 유지하는 것과 그냥 짧은 것의 구분
- ㉰ 문장 작성 규칙 ㉮(과거가 어땠고 지금 어떻다는 서술 금지) 위반 잔존 검색. 후보 표현:
  "구 코드", "개편 전", "~에서 파생하여", "반영할 때", "이제", "더 이상", "기존에는"
- ㉱ 문장 작성 규칙 ㉯(부정 먼저 말하고 줄표 뒤에서 뒤집는 문형 금지) 위반 잔존 검색
- ㉲ 줄표(—)를 접속어나 나열 기호로 쓴 곳 (코드 주석과 docstring 포함). 검사 루틴 항목 1
- ㉳ `%` 마커 잔존 여부

**대상**: `LDPC_base/` 전체 docstring과 주석, `README.md`, `docs/plan.md`, `docs/차이.md`,
`Ideas/*/README.md`, `tools/H_mat_gen/README.md`

---

## P10. 문서와 코드의 사실 일치

**확인 항목**

- ㉮ `README.md` "JSON 설정 스키마" 예시가 `run.py` 키맵과 일치하는지. 예시에 없는 키
  (`run.print_progress`, `output.label`)의 문서화 여부
- ㉯ `README.md`가 드는 생성 파일 예시 `LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt`와 저장소에 실제로
  있는 `..._iter30.txt`, `config.json`의 `max_iter: 120`의 삼자 관계
- ㉰ `README.md` "남은 근사/제한"의 "VNU 출력 레벨 {7,5,3,1} 고정 (3-bit 전용)"이 균일 n-bit 모드
  도입 이후에도 사실인지. `docs/차이.md` #9 "3-bit 전용 (th 3개 아니면 에러)"도 같은 검토 대상
- ㉱ `README.md` "Input/LLR" 행 설명이 생성 파일(uniform)의 존재와 성격을 담는지
- ㉲ 교체 지점 표 3곳(`README.md`, `LDPC_base/decoder.py` docstring, `Ideas/vanilla/README.md`)의
  함수명과 C++ 대응이 서로 같고 실제 코드와 같은지
- ㉳ `docs/plan.md` 상단에 덧붙인 "2026-08-07 구조 개편" 블록이 문장 작성 규칙 ㉮와 충돌하는지,
  아니면 결정 이력 문서라 예외인지 (판단이 필요한 지점)
- ㉴ `tools/H_mat_gen/README.md` ㉰가 "본체로 반영할 때 손봐야 한다"는 미래형인데 반영은 이미 끝났다.
  `select_irregular.py` docstring("현재 실행 불가")과의 시제 불일치
- ㉵ `docs/차이.md`의 "본체 커밋 72b825a에서 파생하여 2026-08-06 개정" 서술과 현재 파일 경로
  (`LDPC_base/decoder.py`)의 정합
- ㉶ `README.md`의 `_pm/TODO.md` 참조("후순위 로그 7종은 미구현")가 TODO 실제 항목과 맞는지

**대상**: `README.md`, `docs/plan.md`, `docs/차이.md`, `tools/H_mat_gen/README.md`,
`Ideas/vanilla/README.md`, `LDPC_base/decoder.py` 모듈 docstring

---

## P11. 데이터 파일 무결성

**확인 항목**

- ㉮ `Input/H_matrix/example_18x147_z256.qc`: 헤더 `147 18` / `4 31` / `256`이 실제 행렬과 맞는지
  (`QCCode.load`의 J/K 검사 통과), README가 전제하는 column block DV 내림차순 배치가 실제로
  지켜지는지, shift 값이 `0 <= s < z` 범위인지
- ㉯ `Input/LLR/LLR_MATRIX_HD_0.txt`: 그룹 3개, restart 1개 구성이 `_validate`의 5개 제약
  (그룹 겹침 금지, 1..max_iter 커버리지, restart 그룹 단일 row·단일 iteration, restart 그룹이
  마지막이면 안 됨, ITER 다중 row 그룹 내부 연속)을 전부 통과하는지
- ㉰ `Input/LLR/LLR_MATRIX_HD_1.txt`: 그룹 2개, restart 0, max_iter 20 구성의 검증 통과와,
  `config.json`이 이 파일을 가리키는 것의 의도(README는 "restart 없는 20-iter 테스트용")
- ㉱ 두 파일의 `dv_from`/`dv_to`가 `[11, 4, 3, 2]`인데 예시 부호의 최대 column degree는 4다.
  dv 11 구간이 영영 매칭되지 않는 것이 의도인지, `col_dv_idx`가 부호의 모든 dv를 덮는지
- ㉲ 생성 파일 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`의 내용 검증: `num_param=32`,
  `num_dv=1`, `dv 1~4`, `group_type=0`, `num_restart=0`, `max_value` 32개 전부 31,
  row = ch 8 + th 31..1 + (csw −1, iter 1, iter 30, floor −1)
- ㉳ 생성 산출물을 git에 커밋하는 정책. `.gitignore`는 `Sim_Output/`만 무시하고 `Input/LLR/`은
  추적한다. 파라미터를 바꿔 실행할 때마다 새 파일이 추적 대상으로 쌓이는 구조의 관리 방침
- ㉴ 파일 인코딩과 줄바꿈(LF/CRLF). `save()`가 `"\n".join(...)`으로 쓰고 git이 CRLF 변환을 예고한다
  (미커밋 `config.json` diff의 warning). 왕복 로드에 영향이 있는지

**대상**: `Input/H_matrix/example_18x147_z256.qc`, `Input/LLR/*.txt`, `.gitignore`,
`LDPC_base/pcm.py:54-75`, `LDPC_base/llr_matrix.py:102-156`

---

## P12. 삭제된 구 코드의 기능 유실 점검

본체 반영 커밋이 구 flat 파일을 대량 삭제했다. 옮겨간 것과 사라진 것을 가른다.

**확인 항목**

- ㉮ 삭제 파일별 대체 경로 확인: `channel.py`/`decoder.py`/`encoder.py`/`run.py`/`sim.py`/`pcm.py`
  → `LDPC_base/` (이동), `tools/*.py` → `tools/H_mat_gen/` (이동)
- ㉯ 대체 없이 사라진 것: `mpi_runner.py`, `examples/fer_curve.py`, `examples/fer_curve.json`,
  `examples/fixed_error_sweep.py`, `examples/llr_tune.py`, `examples/irregular_17x144_z256.qc`,
  `llr/README.md`와 `llr/*.txt` 7종(ch/th 프리셋). TODO에 등록된 것(mpi_runner)과 미등록분의 구분
- ㉰ `llr/ch*_th*.txt` 프리셋이 담던 ch/th 조합 정보가 다른 곳에 남아 있는지, 균일 양자화 모드가
  그 역할을 대체하는지 (`llr_tune.py`의 탐색 기능이 사라진 자리를 무엇이 메우는지)
- ㉱ 구 `examples/fer_curve.json` 포맷으로 만들어 둔 사용자 설정이 새 스키마로 옮겨갈 안내가 있는지
- ㉲ `tools/H_mat_gen/select_irregular.py`가 신규 파일로 추가되면서 구 API 코드를 그대로 담았다
  (`MinSumDecoder(code, max_iter=...)`, `chan.bsc_llr`, `run_fer_point(target_errors=...)`).
  import만 고친 상태로 저장소에 두는 것과 TODO 등록 상태의 정합, 실행하면 어디서 실패하는지

**대상**: `git diff ea88882..HEAD --diff-filter=D -- 2_LDPC_light/`,
`tools/H_mat_gen/select_irregular.py`, `_pm/TODO.md`

---

## P13. 실제 실행 검증 (교차 검증)

정적 읽기로 못 잡는 것을 실행으로 가른다. Python은 로컬 실행이 허용된다.

**확인 항목**

- ㉮ 루트 `config.json`을 `use_input_llr_matrix: true`로 완주 실행. 출력 폴더 구성, `summary.txt`,
  FER CSV, 로그 CSV 3종, `fer_curves.png` 생성 확인
- ㉯ 같은 config를 `use_input_llr_matrix: false`로 바꿔 실행. 생성 파일이 나오고 로드되어 완주하는지,
  `max_iter=120`이 실제로 적용되는지, 소요 시간이 3-bit 대비 어느 정도인지
- ㉰ `Ideas/vanilla/config.json` 실행. 상대경로가 config 위치 기준으로 풀리는지, 결과가 아이디어 폴더
  아래 `Sim_Output/`에 쌓이는지, `decoder.type` 조회가 registry를 실제로 타는지
- ㉱ `save()` → `load()` 왕복 동일성을 파라미터 격자(`num_bits` 2/3/6/8, `mode` HD)로 확인
- ㉲ 균일 모드와 파일 모드의 FER이 같은 채널 포인트에서 물리적으로 납득 가능한 관계인지
  (균일 6-bit가 3-bit 튜닝 테이블보다 나쁘지 않은지, 극단값이 아닌지)
- ㉳ 오류 경로 확인: 존재하지 않는 H-matrix, 모드 불일치 채널(fixed_error + 2SD 파일명),
  `decoder.max_iter` 삽입, 알 수 없는 키, `decoder.type` 미등록 이름
- ㉴ `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code`를 저장소 루트에서 실행해
  README의 실행 예가 실제로 성립하는지
- ㉵ 실행 산출물이 `Sim_Output/`(git 무시) 밖으로 새지 않는지, `Input/LLR/`에 생성 파일이 추가되는
  부작용을 리뷰 후 되돌리는 절차

**대상**: `config.json`, `Ideas/vanilla/config.json`, `LDPC_base/run.py`, `LDPC_base/llr_matrix.py`

---

## 우선순위 제안

- 높음: P1, P2, P4, P5 (델타 로직의 핵심. 왕복 정합성과 상태 전달이 깨지면 결과 전체가 무의미)
- 중간: P3, P6, P7, P11, P13
- 낮음: P8, P9, P10, P12 (품질과 문서 정합. 순수 이동분은 가볍게)
