# Round 2 / agent_6 — V6. 본체 반영 파손 범위, 스코프, 문서 일치

> 작성: 2026-08-06
> 대상: 개정본 `2_LDPC_light/_test/20260806_setup_구성_실험/` 전체, 본체 `2_LDPC_light/` 전체,
> 원본 `0_LDPC_original/` (행 번호 인용 확인)
> 관점 출처: Round 1 agent_1 P7, P8, P11 / agent_2 P9, P10, P13
> 방법: 본체 전수 grep + 개정본 실제 실행(Python 로컬 실행 허용) + 원본 C++ 행 번호 대조

**심각도 표기 규칙**: 본체 반영 파손은 "반영 시점에 터진다"는 조건부이므로 심각도 뒤에 조건을 적었다.
현재 상태(개정본이 `_test/` 안에 격리)에서는 아무것도 깨지지 않는다.

---

## 0. 요약

발견 20건. CRITICAL 0, HIGH 4, MEDIUM 9, LOW 7.

- ㉮ 본체 반영 시 파손: `examples/` 4개 스크립트 전부, `examples/*.qc` 2개, `mpi_runner.py`가 깨진다.
  깨지는 방식은 대부분 즉시 예외(ImportError, TypeError, ValueError)라서 **조용한 오동작은 없다**.
- ㉯ 다만 `examples/fer_curve.json`의 `target_errors`/`stop_below` 2개 키는 개정본에서 **무시된다**
  (조용한 기본값 대체). 이것만 예외적으로 조용하다.
- ㉰ `irregular_17x144_z256.qc`는 로드도 재생성도 불가해지는 유일한 **자산 소실** 지점이다.
- ㉱ 코드 주석의 C++ 행 번호 인용은 확인한 4건 전부 정확했다 (아래 §4-0).
- ㉲ 본체 `_pm/TODO.md`에 반영 절차가 작업으로 등록되어 있지 않다.

---

## 1. 본체 반영 시 파손 범위 (전수)

grep으로 확인한 구 인터페이스 의존처는 아래가 전부다.
확인 명령: `grep -rn "bsc_llr|awgn_llr|fixed_error_llr|awgn_rber"`, `grep -rn "code_file|target_errors|stop_below|max_iter"`,
`.qc` 헤더 실측, 개정본 `pcm.QCCode.load()` 실행 대조.

### V6-1 [HIGH — 반영 시점에 터짐] `examples/fer_curve.json` + `fer_curve.py` 전면 파손

`2_LDPC_light/examples/fer_curve.json` 의 5개 키가 전부 개정본 스키마와 어긋난다.

| json 위치 | 현재 값 | 개정본에서의 결과 |
|---|---|---|
| `examples/fer_curve.json:2` | `"code_file"` | `LDPC_base/run.py:46` `config["H_matrix"]`에서 **KeyError: 'H_matrix'** (안내 메시지 없는 원시 예외) |
| `examples/fer_curve.json:4` | `"max_iter": 120` | `LDPC_base/run.py:48-50` **ValueError** |
| `examples/fer_curve.json:7` | `"target_errors": 40` | `LDPC_base/run.py:110`이 `max_frame_errors`만 읽으므로 **조용히 무시**, 기본값 50 사용 |
| `examples/fer_curve.json:10` | `"stop_below": 5e-4` | `LDPC_base/run.py:113`이 `stop_below_fer`만 읽으므로 **조용히 무시** |
| `examples/fer_curve.json:12-24` | `"channels": [ {bsc}, {awgn} ]` | `LDPC_base/run.py:57` `config["channel"]`에서 **KeyError: 'channel'**. 채널 이름 `bsc`/`awgn`도 개정본 `CHANNELS` = {rber, fixed_error, strong_error}에 없음 |

`examples/fer_curve.py`는 그 위에서 다시 깨진다.

- ㉮ `examples/fer_curve.py:67` `runner.load_config(CONFIG_FILE)` 에서 위 KeyError로 즉사
- ㉯ 설정을 고쳐도 `examples/fer_curve.py:73` `results["bsc"], results["awgn"]` 가 KeyError.
  개정본 `run_experiment`(`LDPC_base/run.py:131`)는 `{ch_type: points}` **단일 항목**만 반환한다
- ㉰ `examples/fer_curve.py:23-63` `plot()`이 bsc/awgn 2채널 병렬 서브플롯으로 하드코딩되어 있어
  단일 채널 반환 구조와 형태가 맞지 않는다

**조치 필요**: json은 전면 재작성, `fer_curve.py`는 plot 함수 시그니처까지 재설계.

### V6-2 [HIGH — 반영 시점에 터짐] 채널 함수 3종 삭제로 `examples/` 스크립트 3개 ImportError

개정본 `LDPC_base/channel.py`에는 `bsc_llr` / `awgn_llr` / `fixed_error_llr` / `awgn_rber`가 전부 없다
(신규 3종 `rber_channel` / `fixed_error_channel` / `strong_error_channel`로 교체, 출력도 배열이 아니라 dict).

| 파일:라인 | 구문 | 결과 |
|---|---|---|
| `examples/fixed_error_sweep.py:15` | `from ..channel import fixed_error_llr` | **ImportError** (모듈 임포트 시점) |
| `examples/llr_tune.py:18` | `from ..channel import fixed_error_llr` | **ImportError** |
| `examples/select_irregular.py:38` | `chan.bsc_llr(...)` | **AttributeError** (`main()` 실행 중) |
| `mpi_runner.py:51` | `chan.bsc_llr(...)` | **AttributeError** |
| `mpi_runner.py:53` | `chan.awgn_llr(...)` | **AttributeError** |
| `llr/README.md:27` | `fixed_error_llr(code, n_err, B, rng, mag=mag)` 사용 예시 | 문서 예시가 죽음 |

`awgn_rber`는 본체 안에 호출처가 없다(정의만 존재). 삭제해도 무해.

### V6-3 [HIGH — 반영 시점에 터짐] `run_fer_point` 인자명 변경으로 호출부 4곳 TypeError

`sim.run_fer_point`의 인자가 `target_errors` → `max_frame_errors`로 바뀌었다
(`2_LDPC_light/sim.py:8` vs `LDPC_base/sim.py:8`). 키워드 인자로 호출하는 곳이 전부 깨진다.

- ㉮ `examples/fixed_error_sweep.py:40` `target_errors=TARGET_ERRORS`
- ㉯ `examples/llr_tune.py:40` `target_errors=TARGET_ERRORS`
- ㉰ `examples/select_irregular.py:39` `target_errors=target_errors`
- ㉱ `mpi_runner.py:56` `target_errors=10 ** 9`

전부 `TypeError: run_fer_point() got an unexpected keyword argument 'target_errors'`.
`sim.py`의 반환 dict 키(`frames`/`errors`/`fer`/`avg_iter_ok`/`sec`/`fps`)와 `save_csv` 시그니처는
동일하므로 그쪽 소비처는 무사하다.

### V6-4 [HIGH — 반영 시점에 터짐] 구 H-matrix 포맷 지원 제거로 `examples/*.qc` 2개 로드 불가, 1개는 자산 소실

본체 `examples/`의 `.qc` 2개는 모두 **구 포맷**이다 (첫 줄 `# QC-LDPC base matrix (-1 = zero block)`,
둘째 줄 `18 147 256` = `M_b N_b z` 정수 3개). 개정본 `LDPC_base/pcm.py:59-62`는 첫 줄 정수 2개만 받는다.
실제로 실행해 확인한 결과:

```
examples/example_18x147_z256.qc     -> ValueError : ... Ref-C 헤더가 아님 (첫 줄 '# QC-LDPC base matrix ...')
examples/irregular_17x144_z256.qc   -> ValueError : ... Ref-C 헤더가 아님 (첫 줄 '# QC-LDPC base matrix ...')
```

예외는 명시적이고 메시지도 원인을 지목한다 (조용한 오동작 아님). 그러나 재생성 경로가 갈린다.

- ㉮ `example_18x147_z256.qc`는 `tools/gen_example_code.py`로 재생성 가능하다.
  `pcm.save()`(본체 `pcm.py:46-51`)가 이미 Ref-C 포맷을 쓰므로 도구 자체는 무사하다
  (`tools/gen_example_code.py`, `tools/peg.py`, `tools/lifting.py`는 `..pcm`만 의존, 파손 없음)
- ㉯ **`irregular_17x144_z256.qc`는 재생성 불가**하다. 유일한 생성처가 `examples/select_irregular.py:106`
  `win_code.save(WINNER_FILE)`인데 그 스크립트가 V6-2/V6-3으로 깨져 있다.
  게다가 이 파일은 `examples/fixed_error_sweep.py:26`과 `examples/llr_tune.py:31`의 **기본 부호**다.
  → 이 3개 파일(스크립트 2개 + 부호 1개)이 서로를 잡고 함께 죽는 유일한 자산 소실 지점이다.

**조치 필요**: 반영 전에 두 `.qc`를 Ref-C 포맷으로 1회 변환해 두거나, `select_irregular.py`를 먼저 고칠 것.

### V6-5 [MEDIUM — 반영 시점에 터짐] 실험 README가 "제거 후보"로 선언한 `llr_tables.py`는 지금 상태로 제거 불가

실험 README `README.md:31-32`는 "`LDPC_base/llr_tables.py`(구 프로파일 로더)와 decoder의 `llr_profile`
모드는 코드만 남아 있고 데이터 파일이 없어 사실상 미사용 — 본체 반영 시 제거 후보"라고 적었다.
그러나 개정본 코드가 아직 의존한다.

- ㉮ `LDPC_base/decoder.py:50` `from .llr_tables import dv_group`
- ㉯ `LDPC_base/decoder.py:48-55` `llr_profile` 분기 (`self._col_th`, `self._col_bf`, `self._edge_mag`, `self.beta`)
- ㉰ `LDPC_base/decoder.py:72-88` `_vnu_quantize()` 전체
- ㉱ `LDPC_base/decoder.py:233` `RESET = self._edge_mag[0] if self.profile is not None else self.msg_clip`
- ㉲ `LDPC_base/decoder.py:275-276` `_decode_column_wise`의 프로파일 분기
- ㉳ `LDPC_base/decoder.py:178` `decode_batch` two_set 경로의 프로파일 분기

즉 `llr_tables.py`를 지우려면 위 6곳과 `MinSumDecoder.__init__`의 `llr_profile` 인자를 함께 걷어내야 한다.
딸려 나가는 본체 자산은 `llr/` 폴더 8개 `.txt` + `llr/README.md`, 그리고 `examples/llr_tune.py`다.
`LDPC_base/llr_tables.py`와 본체 `llr_tables.py`의 차이는 docstring 한 줄뿐이다(4행 "스텁" 표현 변경).

**판단 필요 사항(Decision 등급)**: `llr_profile` 모드를 유지할지 폐기할지가 결정되지 않은 채
"제거 후보"라는 문구만 문서에 남아 있다.

### V6-6 [MEDIUM] 본체 `_pm/TODO.md`에 반영 절차가 작업으로 등록되어 있지 않다

`2_LDPC_light/_pm/TODO.md:12-13`에 있는 항목은 "개정본 코드 딥 리뷰" 하나뿐이다.
리뷰 통과 후 실제로 해야 할 아래 작업이 어디에도 등록되어 있지 않다.

- ㉮ `LDPC_base/*.py` → 본체로 이동 (파일 8개)
- ㉯ `examples/` 4개 스크립트 + `fer_curve.json` 갱신 또는 폐기 결정
- ㉰ `examples/*.qc` 2개 Ref-C 변환 (V6-4)
- ㉱ `mpi_runner.py` 갱신 (V6-2, V6-3)
- ㉲ `llr_tables.py` + `llr/` 처분 결정 (V6-5)
- ㉳ `README.md`, `docs/plan.md` 갱신 (§4)
- ㉴ `Input/` 배치(H_matrix, LLR 분리)를 본체에서 어떻게 둘지 결정

루트 `_pm/TODO.md`에도 없다. `2_LDPC_light/_pm/tasks/`에는 `_template/`이 없다
(루트 `_pm/tasks/_template/README.md`는 존재).

### V6-7 [LOW — 이력 보존 위험] 개정본이 git 추적 대상이 아니다

`git check-ignore -v` 결과 `.gitignore:24: _test/` 로 개정본 전체가 무시된다.
실험 README `README.md:132`가 이 사실을 적어 두긴 했으나, 반영 전까지 개정본의 유일한 사본이
OneDrive 동기화본뿐이고 개발 이력(중간 버전, 되돌리기 지점)이 남지 않는다.
리뷰 문서(`_pm/tasks/20260806_review/`)는 추적 대상이므로 그쪽은 무사하다.

---

## 2. 스코프 완성도 (본체의 새 원본이 될 자격)

### V6-8 [MEDIUM] `llr_matrix` 모드에서 `alpha`/`beta`/`msg_clip`/`quantize`가 무경고로 무시되고, 논문 아이디어 훅이 주 경로에 없다

`_decode_matrix()`(`LDPC_base/decoder.py:319-446`)는 `cn_mag_fn()`을 한 번도 호출하지 않는다
(`decoder.py:392`가 `mag`를 그대로 쓴다). `msg_clip`, `quantize`도 이 경로에서 쓰이지 않고,
`beta`는 `decoder.py:69`에서 조용히 0으로 덮인다.

실제로 확인했다. `decoder`에 `"alpha": 0.75, "msg_clip": 3.0, "quantize": false`를 넣고 실행하면
경고 하나 없이 정상 종료한다 (값은 전부 무효).

두 가지가 문제다.

- ㉮ 사용자가 튜닝 파라미터를 넣어도 아무 일이 일어나지 않고 알 방법이 없다
- ㉯ **`cn_mag_fn`은 이 프로젝트의 존재 이유인 "논문 아이디어 훅"**(`decoder.py:104-108`,
  모듈 docstring 15행)인데, 세 경로 중 주 경로인 matrix 경로에만 없다.
  나머지 두 경로(`decoder.py:163`, `decoder.py:262`)에는 있다.
  논문 아이디어를 syndrome-aided 경로에 붙이려면 훅을 새로 뚫어야 한다

### V6-9 [MEDIUM] `max_iter` 금지 검사가 `llr_matrix` 없는 설정에도 걸려, plan.md의 `max_iter=120`을 설정할 방법이 사라진다

`LDPC_base/run.py:48-50`의 검사는 `llr_matrix` 유무와 무관하게 무조건이다.
`llr_matrix` 없는 설정에 `"max_iter": 120`을 넣고 실행해 확인했다.

```
ValueError: decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일의 마지막 iter_end가 결정
```

결과적으로 `llr_matrix`를 쓰지 않는 실험(legacy two_set / column_wise / llr_profile 경로)은
`MinSumDecoder`의 기본값 `max_iter=20`에 고정되고, JSON으로 바꿀 수 없다.
`docs/plan.md:126` §7 #4가 "**max_iter = 120** (2026-07-30 사용자 지정)"이므로 정면 충돌한다.
실험 README `README.md:63-64`의 문구("`decoder.llr_matrix`: DAO LLR_MATRIX 파일. max_iter는 이 파일의
마지막 iter_end가 결정 — JSON에 max_iter를 쓰면 에러")도 이 금지가 `llr_matrix` 항목에 딸린 것처럼
읽히므로 실제 동작과 어긋난다.

같은 이유로 `LDPC_base/run.py:80` `dec_cfg.setdefault("schedule", "column_wise")`는 `llr_matrix` 분기
**안에만** 있어서, `llr_matrix` 없는 설정의 기본 스케줄은 여전히 `two_set`이다. 문서에 없는 규칙이다.

### V6-10 [MEDIUM] `encoder.encode()` 스텁 교체만으로 끝난다는 서술이 틀렸다 (genie 판정이 all-zero 하드코딩)

`LDPC_base/encoder.py:5-6` docstring: "실물 인코더가 필요해지면 이 함수 내용만 채우면 되고,
channel.py는 이미 cw를 그대로 받아 처리하므로 **다른 곳은 손댈 필요가 없다**".
본체 `README.md:12`, `docs/plan.md:60` §3.1도 같은 취지다.

채널은 맞다 (`LDPC_base/channel.py:82`, `:107`이 `cw`를 받아 그 위에 flip). 그러나 **디코더가 아니다**.
세 경로 전부 정답이 all-zero라는 전제를 코드에 박아 두었다.

- ㉮ `LDPC_base/decoder.py:170` two_set: `frame_err |= (total < 0).any(...)` (total<0 = 비트 에러 = 정답 0 전제)
- ㉯ `LDPC_base/decoder.py:268` column_wise: 동일
- ㉰ `LDPC_base/decoder.py:399` matrix: `bit_err = r_bit[:, j, :] ^ flip` 를 그대로 에러로 센다.
  일반 codeword라면 `r_bit ^ flip ^ cw[:, j, :]`여야 한다

게다가 `decode_batch()`는 `cw`를 받을 인자가 없고, 채널 출력 dict(`{"mode","hd","sd","cc"}`,
`LDPC_base/channel.py:113`)에도 `cw`가 들어 있지 않다. 즉 인코더 반입 시
㉮ `decode_batch` 시그니처, ㉯ 채널 출력 dict 계약, ㉰ 세 경로의 genie 판정을 모두 고쳐야 한다.
"encode()만 교체" 서술은 정정이 필요하다.

### V6-11 [LOW] 미구현 항목의 차단 상태 (대체로 양호)

명시적으로 막히는지 코드로 확인했다.

| 미구현 항목 | 차단 지점 | 판정 |
|---|---|---|
| llr_matrix 2SD/3SD 디코딩 | `LDPC_base/decoder.py:62-64` NotImplementedError | 막힘 |
| 4-bit 빌드 (th 7개) | `LDPC_base/decoder.py:65-66` `th_len != 3` NotImplementedError | 막힘 |
| 채널 대 모드 불일치 | `LDPC_base/run.py:90-93` ValueError | 막힘 (실행 확인) |
| 채널별 미지원 모드 | `channel.py:47`, `:79`, `:98-99` ValueError | 막힘 |
| llr_matrix + two_set 조합 | `LDPC_base/decoder.py:60-61` NotImplementedError | 막힘 |
| BF(1-bit precision) 구간 | 차단 장치 **없음** | LLR_MATRIX 포맷에 BF 필드가 없어 요청 경로 자체가 없다. 실질 무해 |
| 파이프라인 store 지연 | 차단 장치 **없음** | 문서에만 기록. 조용히 통과 (구조상 차단 불가) |
| alpha/msg_clip/quantize | 차단 장치 **없음** | V6-8. 조용히 통과 |

`run.py:90-93` 차단은 실제로 실행해 확인했다.

```
ValueError: channel strong_error은 ('2SD',) 전용 — 현재 디코딩 모드 HD (LLR matrix 파일명 확인)
```

### V6-12 [LOW-MEDIUM] `config.json`이 현재 실행 불가능한 채널 구성을 동봉하고 있다

`config.json:22-27`의 `strong_error` 블록은 지금 어떤 방법으로도 실행할 수 없다.

- ㉮ `strong_error`는 2SD 전용 (`channel.py:98-99`, `CHANNEL_MODES`)
- ㉯ 모드는 LLR matrix 파일명에서만 온다 (`run.py:89`)
- ㉰ `Input/LLR/`에 2SD 파일이 없다 (HD_0, HD_1 두 개뿐)
- ㉱ 2SD 파일을 만들어 넣어도 `decoder.py:62-64`에서 막힌다

`rber` 채널의 2SD/3SD 모드도 같은 이유로 도달 불가다.
실험 README `README.md:78`의 채널 표는 rber의 지원 모드를 "HD, 2SD, 3SD"로, strong_error를 "2SD"로
적어 두었다. 바로 아래 82행 "채널이 지원하지 않는 디코딩 모드와 조합하면 명시적 에러"와
93행 "현재 HD만 구현"이 있어 완전한 오독은 막지만, **표만 보면 실행 가능한 조합으로 읽힌다**.
표 자체에 "현재 미실행" 표시가 필요하다.

### V6-13 [MEDIUM] 개정본 파이프라인이 아직 한 번도 비퇴화 FER를 산출한 적이 없다

`Sim_Output/`에 남은 4개 CSV가 전부 `fer=1.000000e+00`, `avg_iter_ok=0.000`이다
(`fer_rber.csv`, `fer_fixed_error.csv`, `fer_bsc.csv`, `fer_llr_bsc.csv`).
직접 재현해도 같다.

- ㉮ `config.json`의 fixed_error 200/300 포인트: FER 1.0
- ㉯ 에러 30비트로 낮춰도 matrix 경로는 63/64 실패 (FER 0.984)
- ㉰ 같은 30비트를 `llr_matrix` 없이 legacy two_set으로 돌리면 **0/16 실패 (FER 0)**

즉 개정본의 주 경로(matrix)는 이 토이 입력에서 정상 동작하는 구간을 한 번도 보여주지 못했다.
실험 README `README.md:114-117`이 그 원인을 "토이 매트릭스의 dv2 ch=28 문제, 구현 버그 아님"으로
설명하고는 있으나, **본체의 새 원본으로 반영하기 전 정상 수렴하는 입력으로 1회 검증**하지 않으면
반영 후에도 회귀를 감지할 기준선이 없다.

---

## 3. 문서와 코드의 사실 일치

### V6-0 [문제 없음] 코드 주석의 C++ 행 번호 인용은 확인한 4건 전부 정확

`0_LDPC_original/`에서 직접 대조했다.

| 인용 위치 | 인용 내용 | 실제 | 판정 |
|---|---|---|---|
| `LDPC_base/channel.py:20` | `Set_R_Offset (channel.cpp:11-29)` | `channel.cpp:11` 함수 시작, `:29` 닫는 괄호. 값 2SD 0.35, 3SD 0.15/0.35/0.55 일치 | 정확 |
| `LDPC_base/llr_matrix.py:32` | `common.h:756-757` GROUP_TYPE_ITER/CSW | `common.h:756 #define GROUP_TYPE_ITER 0`, `:757 #define GROUP_TYPE_CSW 1` | 정확 |
| `LDPC_base/decoder.py:221-222` | `decoder.cpp:3476-3526` remove-old + update 앞부분 | `:3476 CNU_Remove_Old_Sgn`, `:3514 CNU_Update_New_Mag`, `:3518-3526`이 min1←min2 / min2=V_VERY_STRONG 부분 | 정확 |
| `LDPC_base/decoder.py:29` | `decoder.cpp:4080-4120` VNU 출력 양자화 | `:3973 VN_Cal_HD` 안, `:4080-4120`이 정확히 `temp_m >= th1/th2/th3 → EDGE_MAG_7/5/3/1` 구간 | 정확 |

부수적으로 `차이.md:18` §1 #2의 근거도 원문에서 확인했다.
`common.h:403-407`이 `#ifdef __AUTO_LLR_OPT__ → ITER_MAX_HBF 0`, `mode.h:22`가 `__AUTO_LLR_OPT__` 활성,
`decoder.cpp:2084-2085`가 AUTO 빌드에서 `flag_BF_on = FLAG_LOW` 무조건 대입. 서술 정확하다.

`channel.py` docstring이 인용한 C++ 심볼도 전부 실존한다
(`Make_Dec_Input_Ref_C_Fixed_4KB`, `Make_Dec_Input_Fixed_4KB`, `Make_Dec_Input_AWGN`,
`Make_Dec_Input_AWGN_Quantize`, `Get_Mag_2SD`, `Get_Mag_3SD`, `dev_from_RBER`, `qfunc_inv`,
`rand_sel_ep`, `Set_Real_Err_Pos_4KB`, `MODE_CH_RBER/FIXED_ERROR/STRONG_ERROR`, `V_VERY_STRONG`).

### V6-14 [LOW] `llr_matrix.py` docstring이 저장소에 없는 파일을 포맷 근거로 인용

`LDPC_base/llr_matrix.py:3` "파일 포맷 (DAO_LLR_MATRIX.py Read_Input_LLR_Matrix와 동일, 빈 줄 무시)".
저장소 전체 grep 결과 `DAO_LLR_MATRIX.py`도 `Read_Input_LLR_Matrix`도 존재하지 않는다
(리뷰 문서에서의 언급을 제외하면 이 docstring이 유일한 출현).
포맷 해석이 맞는지 이 저장소 안에서 검증할 수단이 없다는 사실을 docstring에 명시해야 한다.

### V6-15 [MEDIUM] 본체 `README.md`가 반영 후 사실과 어긋나는 곳 9개

| 위치 | 현재 서술 | 개정본 반영 후 |
|---|---|---|
| `README.md:11` | pcm.py "자체 텍스트 포맷 입출력" | Ref-C 포맷 전용 (구 포맷 지원 제거). 현재도 이미 낡음 |
| `README.md:13` | channel.py "BSC(hard) / AWGN(soft, 균일 양자화)" | rber / fixed_error / strong_error 3종, 출력이 dict |
| `README.md:14` | decoder.py "CN 상태 old/new 2세트" | 주 경로는 단일 CN 상태 syndrome-aided flip 도메인 |
| `README.md:15` | sim.py "target_errors까지 배치 반복" | `max_frame_errors` |
| `README.md:16` | run.py "**채널 1개/여러 개**, 포인트 1개/여러 개 모두 설정만으로 처리" | **거짓이 된다**. 개정본은 `channel.use` 단수 선택이라 한 번에 채널 1개만 처리 (`LDPC_base/run.py:116, :131`) |
| `README.md:21-22` | examples/fer_curve.py, fer_curve.json 항목 | V6-1로 파손 |
| `README.md:27-34` | 빠른 실행 3개 명령 전부 | 2번 명령(`examples.fer_curve`)과 3번 명령(`run 2_LDPC_light/examples/fer_curve.json`)이 파손 |
| `README.md:39` | 알려진 갭 "LLR 도메인: signed 등가 구현 (원본은 magnitude+HD flip 도메인)" | matrix 경로가 flip 도메인이므로 갭이 해소됨. 남겨 두면 오독 |
| `README.md:42` | 알려진 갭 "`Get_VNU_Table_Idx` 대응 iteration별 테이블 세트 전환 없음" | `llr_matrix.py`가 정확히 그 전환을 구현하므로 갭이 해소됨 |

`llr_matrix.py`는 구성표에 아예 없다 (신규 모듈 누락).
`README.md:17` mpi_runner "아직 JSON 설정과 통일하지 않음"은 여전히 사실이나, 반영 후에는
"통일 안 됨"이 아니라 "동작 불가"로 격상된다.

### V6-16 [MEDIUM] 본체 `docs/plan.md`가 반영 후 사실과 어긋나는 곳 6개

| 위치 | 현재 서술 | 실제 |
|---|---|---|
| `docs/plan.md:50` §3.1 | 모듈표 첫 행 `config.py` | **본체에도 개정본에도 없는 파일**. 파라미터는 JSON으로 옮겨졌다 (현재도 이미 틀림) |
| `docs/plan.md:44-58` §3.1 | 모듈표에 `llr_matrix.py` 행 없음 | 신규 핵심 모듈 누락 |
| `docs/plan.md:51` | pcm.py "H-matrix 파일 로드 (기존 포맷 그대로 파싱)" | Ref-C 전용 |
| `docs/plan.md:53` | llr_tables.py "2-9 포맷 LLR 테이블 파일 로드" | DAO LLR_MATRIX 포맷으로 사실상 대체 (§1 #5 line 19도 동일 문제) |
| `docs/plan.md:82` §3.2 | "py 뼈대는 수학적으로 등가인 signed 표현으로 구현 (실물 C++ 정합이 필요해지면 flip 도메인 모드 추가)" | flip 도메인 모드가 이미 추가됨 |
| `docs/plan.md:126` §7 #4 | "**max_iter = 120** (2026-07-30 사용자 지정)" | V6-9 참조. matrix 모드는 파일이 결정, 비 matrix 모드는 JSON 설정 불가 |

### V6-17 [MEDIUM] `docs/plan.md` §7 #6의 사용자 결정이 뒤집혔는데 기록이 없다

`docs/plan.md:128` §7 #6은 2026-08-05 사용자 지시로 다음을 확정했다.

> "sweep"이라는 이름/개념 대신 config의 **`channels` 리스트**(채널별 `points` 리스트)로
> 단일·다중 채널·포인트를 동일하게 처리한다

개정본은 이를 `channel.use` **단수 선택**으로 바꿨다 (`LDPC_base/run.py:57-64`, `:116-131`).
설계 결정을 되돌린 변경이므로 루트 `CLAUDE.md` 변경 등급표의 **Decision 등급**에 해당하는데,
근거가 실험 README의 스키마 설명(`README.md:65` "세 종류를 모두 구성해 두고 `use`로 실행할 채널 선택")
한 줄뿐이고 plan.md §7이나 `_pm/DONE.md`에는 반영되지 않았다.
`_pm/DONE.md:9` 2026-08-05 항목이 여전히 "`config["channels"]` 리스트로 채널 1개/여러 개를 동일 경로로 처리"를
완료 사실로 기록하고 있어 서로 모순된다.

### V6-18 [LOW-MEDIUM] 개정본 `decoder.py` 모듈 docstring이 주 경로를 전혀 반영하지 못한다

`LDPC_base/decoder.py:1-16`은 개정 전 그대로다. 세 지점이 틀렸다.

- ㉮ `decoder.py:8` "LLR 도메인: 수학적 등가인 signed 표현 (원본 C++는 flip/magnitude 도메인)".
  주 경로 `_decode_matrix`는 flip/magnitude 도메인이다 (`decoder.py:319-338` 자체 docstring이 그렇게 적었다).
  같은 파일 안에서 모듈 docstring과 함수 docstring이 상반된다
- ㉯ `decoder.py:4-6` "CN 상태 old/new 2세트"만 서술. `_decode_column_wise`와 `_decode_matrix`는
  단일 CN 상태 즉시 갱신 구조다
- ㉰ `decoder.py:9-10` "성공 판정: genie — **매 iteration** hard decision을 정답(all-zero)과 bitwise 비교".
  실제 구현은 iteration 경계 스냅샷이 아니라 **column 루프 도중** `frame_err |=`로 누적한다
  (`decoder.py:170`, `:268`, `:399-400`). 판정 시점이 column 순서에 의존한다

`llr_matrix`와 `_decode_matrix`에 대한 언급이 모듈 docstring에 한 줄도 없다.

### V6-19 [LOW] 실험 README "검증 기록"의 수치 3개 중 2개가 재현되지 않고, 재현 조건이 기록되어 있지 않다

직접 실행해 대조했다.

| README 위치 | 서술 | 재현 결과 | 판정 |
|---|---|---|---|
| `README.md:85` | "strong 에러 90 · strong 정정 22399" | e2 = round(300×0.3) = 90, c2 = round((37632−300)×0.6) = round(22399.2) = **22399**. 정확히 일치 | 정확 |
| `README.md:84` | "RBER 0.01 → 측정 BER **0.0104**" | 256프레임(9.6M bit) 측정값 **0.010003**. 이론값도 0.0100. `0.0104`는 B=8, seed=1 같은 극소 표본에서만 나온다(0.01035) | **재현 불가**. 표본 크기와 시드 미기재. 4% 계통 편차처럼 읽힌다 |
| `README.md:112` | "fixed-error 30비트 → 잔여 **4.4**" | seed `[20260806, 30]`, B=64에서 iteration 1 잔여 = **3.98** (HD_0, HD_1 동일) | **재현 불가**. 시드/배치/파일 미기재 |

세 번째 수치를 뽑는 경로 자체가 현재 폴더에 없다. `collect_profile`은 `LDPC_base/decoder.py:110`의
인자로만 존재하고 `sim.py:19`가 `dec.decode_batch(...)`를 인자 없이 호출하므로
**실행 경로에서 도달 불가**다. 즉 검증 기록을 만든 임시 스크립트가 폴더에 남아 있지 않아
기록을 재확인할 방법이 없다.

### V6-20 [LOW] 실험 README의 사실 서술 3건

- ㉮ `README.md:26` "column block은 **DV 내림차순 배치** (예시 부호 재배열 완료)".
  `Input/H_matrix/example_18x147_z256.qc`의 행렬 내용은 본체 `examples/example_18x147_z256.qc`와
  **완전히 동일**하다 (원소 단위 비교 확인). 헤더 포맷만 바뀌었고 **재배열은 일어나지 않았다**.
  원래부터 DV 내림차순(4×129 → 3×1 → 2×17)이었다. "재배열 완료"는 하지 않은 작업을 했다고 적은 것이다
- ㉯ `README.md:119-125` "남은 근사/제한" 4항목이 같은 폴더 `차이.md:13-25` §1의 9항목의 부분집합이다.
  README에만 있는 항목은 없고, README에 빠진 것은 error floor 감지 상태머신(#3), power stopping(#5),
  1.5SD(#1), dv 미매칭 처리 차이(#8)다. README만 읽으면 제한 범위를 과소평가한다
- ㉰ `README.md:27` "구 프로파일(ch*.txt 류)은 삭제"는 `Input/` 기준으로만 참이다.
  로더 `LDPC_base/llr_tables.py`는 복사되어 남아 있고 `decoder.py:50`이 임포트한다 (V6-5)

### V6-21 [LOW] `Sim_Output/`에 현행 채널 이름 체계와 맞지 않는 구 결과가 섞여 있다

`Sim_Output/`의 6개 파일 중 4개가 정리 대상이다.

- ㉮ `fer_bsc.csv` (param 0.02), `fer_llr_bsc.csv` (param 0.005, 0.002).
  `bsc` / `llr_bsc`는 개정본 `CHANNELS` = {rber, fixed_error, strong_error}에 없는 이름이다.
  개정 전 코드가 만든 산출물이 개정본 산출물과 같은 폴더에 섞여 있다
- ㉯ `_tmp_rber.json`, `_tmp_strong.json`은 임시 **설정** 파일인데 **출력** 폴더에 들어 있다

실험 README `README.md:133-134`가 "이 폴더는 그대로 실험 기록으로 남긴다 (삭제하지 않음)"이므로,
정리하지 않으면 나중에 이 CSV들이 개정본의 검증 결과로 오독될 수 있다.

### V6-22 [LOW] 본체 `llr/README.md`의 파일 목록이 실제 파일과 다르다 (기존 문제)

`llr/README.md:15-21` 표가 나열한 `chA_thmid.txt`, `chB_thmid.txt`, `chA_thlow.txt`, `chA_thhigh.txt`는
**존재하지 않는다**. 실제 파일은 `ch5577_th842.txt`, `ch6666_th842.txt`, `ch66810_th842.txt`,
`ch6688_th1052.txt`, `ch6688_th842.txt`, `ch6688_th952.txt`, `ch6688_thdv.txt`, `_hw_orig_ch.txt`다.
`llr/README.md:26` 사용 예시도 `chA_thmid.txt`를 가리킨다.
개정본 반영과 무관한 기존 문제이나, `llr/` 처분(V6-5) 결정 시 함께 정리할 것.

### V6-23 [LOW] 리뷰 기록 위치가 두 곳으로 갈렸다

`2_LDPC_light/_pm/TODO.md:29`는 "리뷰 기록: `docs/review/`"를 가리키는데,
이번 리뷰는 `_pm/tasks/20260806_review/`에 쌓이고 있다. 두 폴더는 하위 폴더 이름과 파일 이름이 같지만
내용은 다르다 (`docs/review/`는 2026-07-30 plan.md 리뷰, `_pm/tasks/`는 2026-08-06 개정본 코드 리뷰).
파일 이름이 같아 혼동 여지가 있으므로 TODO의 참조 항목에 두 곳을 구분해 적을 것.

---

## 4. 확인했으나 문제가 아닌 것

- ㉮ **C++ 행 번호 인용 4건 전부 정확** (§3 V6-0). 인용한 C++ 심볼 12개도 전부 실존
- ㉯ **파손이 조용하지 않다**: 구 인터페이스 의존처는 `fer_curve.json`의 `target_errors`/`stop_below`
  2개 키를 제외하면 전부 즉시 예외로 터진다. `pcm.load`의 구 포맷 거부 메시지도 원인을 지목한다
  (`LDPC_base/pcm.py:61-62`)
- ㉰ `tools/` 3개 파일(`peg.py`, `lifting.py`, `gen_example_code.py`)은 `..pcm`만 의존하고
  `pcm.save()`가 이미 Ref-C 포맷이므로 반영 후에도 그대로 동작한다
- ㉱ `sim.py`의 반환 dict 키와 `save_csv` 시그니처가 유지되어 결과 소비 측은 파손되지 않는다
- ㉲ 디코더 반환 dict 계약(`success` / `n_iter` / `profile`)이 개정 전후 동일하다
- ㉳ `__init__.py`는 개정본과 본체가 완전히 동일하다 (임포트하는 4개 모듈이 전부 남아 있어 파손 없음)
- ㉴ `encoder.py`는 함수 시그니처와 동작이 동일하다 (docstring 표현만 "스텁" → "임시 함수")
- ㉵ 개정본은 `_test/` 아래에 있고 `README.md`가 존재하므로, 글로벌 규칙의 테스트 폴더 요건
  (디렉토리 명명, README 작성, 기존 데이터 미수정)은 충족한다.
  실제로 본체 파일은 하나도 수정되지 않았음을 git status(clean)로 확인했다

---

## 5. 반영 전 처리 순서 제안 (참고)

파손 의존 관계상 아래 순서를 지키지 않으면 자산이 소실된다.

- 1. `examples/*.qc` 2개를 Ref-C 포맷으로 변환 (V6-4 ㉯. 이걸 먼저 하지 않으면
  `irregular_17x144_z256.qc`가 복구 불가)
- 2. `llr_profile` 모드 존치 여부 결정 (V6-5. Decision 등급)
- 3. `channels` 리스트 → `channel.use` 단수 전환을 plan.md §7 #6과 DONE.md에 기록 (V6-17. Decision 등급)
- 4. `max_iter` 금지 범위 확정 (V6-9)
- 5. 코드 이동 후 `examples/` 4개 + `mpi_runner.py` 갱신 또는 폐기
- 6. `README.md` 9곳, `docs/plan.md` 6곳 갱신 (V6-15, V6-16)
- 7. `Sim_Output/` 구 산출물 정리 (V6-21)
