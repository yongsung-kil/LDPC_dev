# worker_c_1 — 독립 전수 수색 (개정본 반영 시 본체 잔여 파일 파손 조사)

작성: 2026-08-06 23:32:21
담당: team_c 워커 1
방법: 본체(`2_LDPC_light/`)와 개정본(`_test/20260806_setup_구성_실험/LDPC_base/`)을 파일 단위로 직접 대조한 뒤,
저장소 전체(모든 확장자)를 grep. 추가로 스크래치패드에 **합성 트리**(본체 복사 → 개정본 `.py` 9개로 덮어쓰기)를
만들어 임포트/실행으로 실증했다. 프로젝트 파일은 읽기만 했다.

- 합성 트리 경로: `C:\Users\yongs\AppData\Local\Temp\claude\d--OneDrive-My-Projects-LDPC-dev\16fcbdf4-af26-4590-914b-4ced68125c6f\scratchpad\work\ldpclight\`
- 변경 전 비교용 트리: 같은 위치의 `ldpcbefore\`
- 덮어써지는 파일 9개: `__init__.py`, `pcm.py`, `encoder.py`, `channel.py`, `decoder.py`, `sim.py`, `run.py`, `llr_tables.py`, (신규) `llr_matrix.py`

> 편향 방지를 위해 `r2_round2_lv1_analysis/`, `docs/review/`는 읽지 않았다. 다만 6번 항목의 첫 grep에서
> `agent_6.md`의 몇 줄이 결과에 섞여 출력되었다. 이후 모든 grep에서 해당 폴더를 제외했고, 아래 결론은
> 전부 스스로 재현한 실행 결과와 파일:라인 근거만으로 세웠다.

---

## 1. 인터페이스 변화 대조표

표기: **본체** = `2_LDPC_light/<파일>`, **개정본** = `_test/20260806_setup_구성_실험/LDPC_base/<파일>`

### 1-1. 설정 JSON 키 (`run.py`)

| 항목 | 본체 | 개정본 | 근거 |
|------|------|--------|------|
| H-matrix 경로 키 | `code_file` | `H_matrix` | 본체 `run.py:40`, 개정본 `run.py:46` |
| 채널 구성 | `channels` (리스트, 각 원소에 `type`/`points`/`seed`) | `channel` (객체) + `channel.use`로 1개 선택 | 본체 `run.py:47`, 개정본 `run.py:57-64` |
| 채널 이름 | `"bsc"`, `"awgn"` | `"rber"`, `"fixed_error"`, `"strong_error"` | 본체 `run.py:26-29`, 개정본 `channel.py:117-121` |
| 종료 조건 키 | `run.target_errors` | `run.max_frame_errors` | 본체 `run.py:83`, 개정본 `run.py:110` |
| 조기 중단 키 | `run.stop_below` | `run.stop_below_fer` | 본체 `run.py:86`, 개정본 `run.py:113` |
| `decoder.max_iter` | 허용 (그대로 `MinSumDecoder`에 전달) | **금지** — 있으면 `ValueError` | 본체 `run.py:64`, 개정본 `run.py:48-50` |
| `decoder.llr_matrix` | 없음 | 신설 (DAO LLR_MATRIX 파일 경로) | 개정본 `run.py:51-52`, `run.py:76-81` |
| `channel.strong_error.SCR`/`SER` | 없음 | 신설 (필수) | 개정본 `run.py:95-96` |
| `output.dir` 기본값 | config 파일이 있는 폴더 | `<config 폴더>/Sim_Output` | 본체 `run.py:43`, 개정본 `run.py:54` |
| 알 수 없는 `run.*` 키 | 검증 없음 (`.get()`) | **검증 없음 (동일)** — 구 키는 조용히 무시 | 본체 `run.py:82-88`, 개정본 `run.py:109-114` |

### 1-2. `channel.py` 공개 함수

| 본체 (파일:라인) | 개정본 | 상태 |
|------------------|--------|------|
| `bsc_llr(code, cw, rber, rng, mag=8.0)` `channel.py:14` | — | **삭제** |
| `fixed_error_llr(code, n_err, batch, rng, mag=8.0)` `channel.py:27` | — | **삭제** |
| `awgn_llr(code, cw, ebn0_db, rng, step, ch_clip, quantize)` `channel.py:42` | — | **삭제** |
| `awgn_rber(ebn0_db, rate)` `channel.py:56` | — | **삭제** |
| — | `rber_channel(code, cw, rber, rng, mode="HD")` `channel.py:43` | 신설 |
| — | `fixed_error_channel(code, cw, n_err, rng, mode="HD")` `channel.py:76` | 신설 |
| — | `strong_error_channel(code, cw, n_err, rng, scr, ser, mode="2SD")` `channel.py:89` | 신설 |
| — | `qfunc_inv`, `dev_from_rber`, `CHANNELS`, `CHANNEL_MODES` `channel.py:24,37,117,124` | 신설 |

**반환값 형태 변화**: 본체 4함수는 모두 `(B, N_b, z) float32 signed LLR 배열`을 반환한다
(`channel.py:24,39,53`). 개정본 3함수는 모두 `dict {"mode","hd","sd","cc"}`를 반환한다
(`channel.py:53,86,113-114`). 실증:

```
$ python -c "from ldpclight import channel as chan; print([a for a in dir(chan) if not a.startswith('_')])"
['CHANNELS', 'CHANNEL_MODES', 'dev_from_rber', 'fixed_error_channel', 'np', 'qfunc_inv', 'rber_channel', 'strong_error_channel']
has bsc_llr: False | has awgn_llr: False | has fixed_error_llr: False | has awgn_rber: False
```

> 완충 장치: 개정본 `decoder.py:120-124`가 `decode_batch`에 dict가 들어오면 HD에 한해 `±8.0` signed 배열로
> 변환한다. 즉 **디코더 쪽은 dict를 받아준다.** 그러나 삭제된 4개 함수 이름 자체는 어디에도 복원되지 않는다.

### 1-3. `sim.py`

| 항목 | 본체 | 개정본 |
|------|------|--------|
| `run_fer_point` 인자 | `(code, channel_fn, dec, rng, target_errors=50, max_frames=20000, batch=128, verbose=False)` `sim.py:7-8` | `(..., max_frame_errors=50, ...)` `sim.py:7-8` |
| `run_fer_point` 반환 키 | `frames, errors, fer, avg_iter_ok, sec, fps` `sim.py:25-29` | **동일** `sim.py:25-29` |
| `save_csv(results, path, param_name="param")` | `sim.py:36` | **동일** `sim.py:36` (본문 바이트 동일) |

실증:
```
run_fer_point (code, channel_fn, dec, rng, max_frame_errors=50, max_frames=20000, batch=128, verbose=False)
save_csv      (results, path, param_name='param')
```
`sim.py`의 두 함수 외 차이는 없다 (docstring 2줄만 다름).

### 1-4. `pcm.py` `.qc` 포맷

| 항목 | 본체 | 개정본 |
|------|------|--------|
| `QCCode.load` | Ref-C(헤더 정수 2개) **+ 구 포맷(정수 3개) 자동 감지**, `#` 주석 제거 | **Ref-C 전용**, `#` 주석 제거 안 함 |
| 근거 | `pcm.py:53-79` (특히 `:57` 주석 제거, `:65` 구 포맷 분기) | `pcm.py:54-75` (특히 `:57-58` 주석 미제거, `:60-62` `ValueError`) |
| `QCCode.save` | Ref-C 포맷 | **동일** (`pcm.py:45-52` ↔ `pcm.py:46-52`, 바이트 동일) |
| 그 외 (`__init__`, `syndrome`, `count_cycles4`, `summary`) | — | **동일** |
| 추가 전제 (docstring만, 코드 미강제) | 없음 | "column block은 DV 내림차순 배치를 전제" `pcm.py:15` |

**본체 `examples/*.qc` 2개의 실제 헤더 (직접 확인)**

```
examples/example_18x147_z256.qc   1행: "# QC-LDPC base matrix (-1 = zero block)"   2행: "18 147 256"   → 구 포맷
examples/irregular_17x144_z256.qc 1행: "# QC-LDPC base matrix (-1 = zero block)"   2행: "17 144 256"   → 구 포맷
```

개정본 `Input/H_matrix/example_18x147_z256.qc`는 Ref-C 헤더 (`147 18` / `4 31` / `256` / 빈 줄).
행렬 본문은 본체 파일과 **완전히 동일**하다 (`np.array_equal` = True로 실측).
→ 구 포맷 → Ref-C 변환은 **헤더 3줄 재작성만으로 충분**하며, 부호 재생성은 필요 없다.

세 번째 `.qc`인 `1_LDPC_revised/_pm/tasks/260803_iteration당속도측정/irregular_15x145_z256.qc`는
이미 Ref-C 헤더(`145 15` / `11 52` / `256`)이므로 **영향 없음**.

### 1-5. `llr_profile` / `llr_tables`

`llr_tables.py`는 **인터페이스 무변경**. 두 파일을 대조한 결과 차이는 docstring 4행("스텁" → "항상 0을
반환하는 임시 함수") 한 곳뿐이다. `LLRProfile`, `dv_group`, `ch_mag_by_col`, `load_profile`,
`_KEYS` 전부 동일 (`llr_tables.py:20-73` 양쪽 동일).
`MinSumDecoder(..., llr_profile=...)` 인자도 유지된다 (개정본 `decoder.py:24`).
`llr/*.txt` 프로파일 8개 전부 개정본 `load_profile`로 정상 파싱됨을 실행으로 확인했다.

### 1-6. `MinSumDecoder`

| 항목 | 본체 | 개정본 |
|------|------|--------|
| 생성자 | `(code, max_iter=20, beta=1.0, alpha=None, msg_clip=31.0, quantize=True, schedule="two_set", llr_profile=None)` `decoder.py:23-24` | 끝에 `llr_matrix=None` **추가** `decoder.py:23-24` |
| `decode_batch` | `(ch_llr, collect_profile=False)` `decoder.py:76` | **동일** `decoder.py:110` |
| 반환 dict 키 | `success`, `n_iter`, (+`profile`) `decoder.py:171-174` | **동일** `decoder.py:212-215` |
| 입력 허용 형태 | `(B,N_b,z)` float 배열만 | 배열 **또는** 채널 dict (HD 한정 어댑터) `decoder.py:120-124` |
| 신규 제약 | — | `llr_matrix` 지정 시 `llr_profile` 동시 금지 / `column_wise` 강제 / HD 전용 / `max_iter`는 파일이 결정 `decoder.py:57-70` |

→ **기존 호출부에 대해 하위 호환**이다. `MinSumDecoder(code, max_iter=..., schedule=..., llr_profile=...)`은
그대로 동작한다.

### 1-7. `run.py` `load_config` / `run_experiment` 반환 구조

| 항목 | 본체 | 개정본 |
|------|------|--------|
| `load_config(path)` 반환 | config dict (`code_file` 절대경로화, `channels[].points` 리스트 정규화) `run.py:32-52` | config dict (`H_matrix`/`decoder.llr_matrix` 절대경로화, `channel[use].points` 정규화) `run.py:34-65` |
| `setup(config)` 반환 | `(code, dec)` `run.py:65` | `(code, dec)` `run.py:83` — **동일** |
| `run_experiment` 반환 | `{channel_type: [point,...]}` — **채널 여러 개 가능** `run.py:105` | `{ch_type: [point,...]}` — **항상 키 1개** `run.py:131` |
| `report(results, config)` 반환 | `results` `run.py:118` | `results` `run.py:143` — 동일 |
| point dict | `run_fer_point` 결과 + `"param"` `run.py:101` | 동일 `run.py:127` |

→ 함수 이름·개수·시그니처는 유지되지만, **`run_experiment`가 한 번에 채널 1개만 처리**하도록 바뀐 것이
구조적 변화다 (아래 2-1 fer_curve.py 참조).

### 1-8. 목록에 없던 추가 변화 (자체 발견)

| # | 변화 | 근거 | 영향 |
|---|------|------|------|
| A1 | 모듈 실행 경로 문자열이 `python -m LDPC_base.run`으로 바뀜 | 개정본 `run.py:9`, `run.py:149` | 본체 반영 시 `python -m 2_LDPC_light.run`으로 되돌려야 함. 안 고치면 **문서상 안내만 틀림**(런타임 무해) |
| A2 | `output.dir` 기본값이 `base_dir` → `base_dir/Sim_Output` | 본체 `run.py:43` ↔ 개정본 `run.py:54` | `output.dir`를 안 쓰는 설정의 **출력 위치가 조용히 이동** |
| A3 | `report()` 폴백 기본값 `"."` → `"Sim_Output"` | 본체 `run.py:112` ↔ 개정본 `run.py:137` | 실사용 경로에선 `load_config`가 항상 채우므로 무해 |
| A4 | `encoder.py`는 docstring만 변경, 인터페이스 무변경 | 본체 `encoder.py:10,15` ↔ 개정본 `encoder.py:11,16` | 없음 |
| A5 | `__init__.py` 두 파일 **완전 동일** — `QCCode`, `MinSumDecoder`, `channel`, `encoder`, `sim` 재수출 | 양쪽 `__init__.py:6-10` | 간접 의존 경로 없음. 단 `import 2_LDPC_light`가 `channel`을 즉시 임포트하므로, 삭제된 함수는 **패키지 임포트 시점이 아니라 접근 시점**에 터진다 |
| A6 | 개정본 `pcm.py:15`가 "DV 내림차순 배치 전제"를 새로 선언했으나 **코드로 강제하지 않음** | `pcm.py` 전체에 검사 없음 | `examples/irregular_17x144_z256.qc`는 실측 결과 정보부가 **DV 오름차순**(3→4→10). 로드는 되지만 전제 위반이 **완전히 조용함** |
| A7 | `tools/gen_example_code.py:22`, `examples/select_irregular.py:29`가 `info_col_degrees` **오름차순** 사용 | 해당 라인 | A6과 같은 이유로 새로 생성되는 부호도 전제 위반. 조용함 |

---

## 2. 의존처 전수 목록 (파일별)

`_test/` 자신은 제외. `_pm/tasks/20260806_review/`, `docs/review/`(과거 리뷰 기록)는 리뷰 문서라 코드 파손
대상이 아니므로 별도 분류(2-11)했다.

### 2-1. `2_LDPC_light/examples/fer_curve.py` — **완전 파손**

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 67 | `config = runner.load_config(CONFIG_FILE)` | **KeyError: 'H_matrix'** (개정본 `run.py:46`에서 즉시) | 아니오 (즉시 예외) |
| 73 | `bsc, awgn = results["bsc"], results["awgn"]` | (67을 고쳐도) **KeyError** — 개정본 `run_experiment`는 `channel.use` 1개 키만 반환 | 아니오 |
| 23, 50-53, 78 | 2패널 플롯(BSC/AWGN 동시)이 전제 | **구조적 불가** — 개정본은 실행 1회당 채널 1개 | 아니오 (설계 재작성 필요) |
| 74 | `config["output"]["dir"]` | 동작 (개정본도 `output.dir`를 채움) | — |
| 23-63 | `plot(...)` 함수 본체 | 파손 없음 (순수 matplotlib) | — |

실증:
```
File ".../ldpclight/run.py", line 46, in load_config
    config["H_matrix"] = resolve(config["H_matrix"])
KeyError: 'H_matrix'
```

### 2-2. `2_LDPC_light/examples/fer_curve.json` — **키 5종 파손**

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 2 | `"code_file": "example_18x147_z256.qc"` | `H_matrix` 부재로 **KeyError** (개정본 `run.py:46`) | 아니오 |
| 4 | `"max_iter": 120` (decoder 하위) | (2를 고치면) **ValueError** "decoder.max_iter는 JSON에 두지 않는다" (개정본 `run.py:48-50`) | 아니오 |
| 7 | `"target_errors": 40` | **조용히 무시** → `max_frame_errors` 기본 50 사용 | **예 (조용함)** |
| 10 | `"stop_below": 5e-4` | **조용히 무시** → 조기 중단 없음 | **예 (조용함)** |
| 12-23 | `"channels": [{type:"bsc"},{type:"awgn"}]` | `channel` 부재로 **KeyError** (개정본 `run.py:57`) | 아니오 |
| 14, 19 | `"type": "bsc" / "awgn"` | 채널 이름 자체가 없어짐 (`rber`/`fixed_error`/`strong_error`) | 아니오 |
| 24-27 | `"output"` | 파손 없음 | — |

조용한 무시 실증 (`H_matrix`/`channel`만 신 스키마로 고치고 `target_errors`/`stop_below`는 남긴 설정):
```
load_config 통과 (구 키 검증 없음). run 하위 키: ['batch', 'max_frames', 'stop_below', 'target_errors']
  fixed_error [(5, 16, 0, 0.0), (10, 16, 2, 0.125)]
=> max_frame_errors 기본 50 사용(target_errors=3 무시), stop_below_fer=None(stop_below=0.5 무시)
```
첫 포인트 FER=0.0이 `stop_below=0.5`를 만족했는데도 스윕이 멈추지 않았다 — 무시가 실제로 결과를 바꾼다.

### 2-3. `2_LDPC_light/examples/fixed_error_sweep.py` — **임포트 시점 즉사**

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 15 | `from ..channel import fixed_error_llr` | **ImportError: cannot import name 'fixed_error_llr'** — 모듈 임포트 시점 | 아니오 |
| 24 | `TARGET_ERRORS, MAX_FRAMES, BATCH = 40, 3000, 128` | (15를 고쳐도) 39-41과 함께 파손 | — |
| 29 | `QCCode.load(code_file)` (기본값 `irregular_17x144_z256.qc`, 20행) | **ValueError: Ref-C 헤더가 아님** | 아니오 |
| 39 | `fixed_error_llr(code, n_err, b, rg)` | **NameError/AttributeError** (함수 부재) | 아니오 |
| 40 | `run_fer_point(..., target_errors=TARGET_ERRORS, ...)` | **TypeError: unexpected keyword argument 'target_errors'** | 아니오 |
| 16, 13, 14 | `from ..sim import run_fer_point` 등 | 임포트 자체는 성공 | — |

실증: `FAIL ldpclight.examples.fixed_error_sweep: ImportError: cannot import name 'fixed_error_llr' from 'ldpclight.channel'`

### 2-4. `2_LDPC_light/examples/llr_tune.py` — **임포트 시점 즉사**

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 18 | `from ..channel import fixed_error_llr` | **ImportError** — 모듈 임포트 시점 | 아니오 |
| 24, 49 | `CODE_FILE = .../irregular_17x144_z256.qc`, `QCCode.load(CODE_FILE)` | **ValueError: Ref-C 헤더가 아님** | 아니오 |
| 39 | `fixed_error_llr(code, n_err, b, rg, mag=mag)` | **AttributeError/NameError** | 아니오 |
| 40 | `run_fer_point(..., target_errors=TARGET_ERRORS, ...)` | **TypeError** | 아니오 |
| 19 | `from ..llr_tables import load_profile, ch_mag_by_col` | **파손 없음** (llr_tables 무변경) | — |
| 54, 62 | `MinSumDecoder(code, max_iter=..., schedule=..., llr_profile=prof)` | **파손 없음** (생성자 하위 호환) | — |
| 57-63 | `llr/*.txt` 8개 로드 | **파손 없음** (실행으로 8개 전부 확인) | — |

실증: `FAIL ldpclight.examples.llr_tune: ImportError: cannot import name 'fixed_error_llr' from 'ldpclight.channel'`

### 2-5. `2_LDPC_light/examples/select_irregular.py` — **임포트는 통과, 실행 중 사망**

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 20 | `from .. import channel as chan` | 성공 (모듈 임포트는 됨) — **지연 폭발** | 임포트 단계는 조용함 |
| 39-40 | `run_fer_point(..., target_errors=target_errors, max_frames=..., batch=...)` | **TypeError: unexpected keyword argument 'target_errors'** — `fer_at()` 첫 호출(60행)에서 | 아니오 |
| 38 | `chan.bsc_llr(code, zero_cw(b), rber, rg)` | **AttributeError: module has no attribute 'bsc_llr'** — 단, 39행 TypeError가 **먼저** 터져 여기까지 도달하지 않음 | 아니오 |
| 22 | `from ..tools.gen_example_code import build_code` | **파손 없음** | — |
| 51 | `build_code(Z, M, N, INFO_DEGREES, seed=sd)` | **파손 없음** (PEG/lifting 무변경) | — |
| 106 | `win_code.save(WINNER_FILE)` | **파손 없음** — `save()`는 이미 Ref-C 포맷 출력 (`pcm.py:45-52`, 양쪽 동일) | — |
| 29 | `INFO_DEGREES = [3]*65+[4]*31+[10]*31` (오름차순) | 개정본 `pcm.py:15`의 "DV 내림차순 전제" 위반 — **아무 경고 없음** | **예 (조용함)** |

실증 (호출 순서 확인):
```
--- (A) run_fer_point(target_errors=...) ---
  TypeError: run_fer_point() got an unexpected keyword argument 'target_errors'
--- (B) chan.bsc_llr 자체 ---
  AttributeError: module 'ldpclight.channel' has no attribute 'bsc_llr'
```
`import ldpclight.examples.select_irregular` 자체는 **OK**로 통과한다 — 즉 정적 임포트 검사로는 잡히지 않는다.

### 2-6. `2_LDPC_light/examples/*.qc` (자산 2개) — **로드 불가**

| 파일 | 헤더 실측 | 깨지는 방식 | 조용함 |
|------|-----------|-------------|--------|
| `examples/example_18x147_z256.qc` 1-2행 | `# QC-LDPC base matrix (-1 = zero block)` / `18 147 256` | **ValueError**: `Ref-C 헤더가 아님 (첫 줄 '# QC-LDPC ...' — 'N_b M_b' 정수 2개여야 함)` | 아니오 |
| `examples/irregular_17x144_z256.qc` 1-2행 | 동일 형태 / `17 144 256` | **ValueError** 동일 | 아니오 |

재생성 경로 상태:
- `example_18x147_z256.qc` → `tools/gen_example_code.py` 로 **재생성 가능** (실행 확인. `build_code` + `save()` 정상, 결과가 Ref-C로 저장되고 개정본 `load`로 재로드됨)
- `irregular_17x144_z256.qc` → `examples/select_irregular.py` 경유인데 그 스크립트가 2-5대로 죽으므로 **재생성 불가**
- 단, 개정본 `Input/H_matrix/example_18x147_z256.qc`와 본체 파일의 **행렬 본문이 완전 동일**함을 실측했으므로
  변환은 헤더 3줄 재작성으로 충분하다. `irregular_17x144`의 J/K는 실측 `J=10, K=40`.
  → **자산 소실 위험은 없다** (헤더만 바꾸면 됨). 재생성은 불필요.

### 2-7. `2_LDPC_light/mpi_runner.py` — **실행 중 사망**

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 15 | `from . import channel as chan` | 성공 — 지연 폭발 | 임포트 단계 조용함 |
| 44 | `code = QCCode.load(args.code_file)` | 인자로 본체 구 포맷 `.qc`를 주면 **ValueError: Ref-C 헤더가 아님** | 아니오 |
| 56-57 | `run_fer_point(code, fn, dec, rng, target_errors=10**9, max_frames=..., batch=...)` | **TypeError: unexpected keyword argument 'target_errors'** | 아니오 |
| 51 | `fn = lambda b, r: chan.bsc_llr(code, zero_cw(b), args.rber, r)` | **AttributeError** — 56행 TypeError가 먼저 터져 도달 안 함 | 아니오 |
| 53 | `fn = lambda b, r: chan.awgn_llr(code, zero_cw(b), args.ebn0, r)` | **AttributeError** — 동일 (도달 안 함) | 아니오 |
| 30-31 | `--rber` / `--ebn0` CLI 옵션 | AWGN 채널 자체가 개정본에 없음 → `--ebn0`는 **대응 불가** (rber 채널이 등가 AWGN이지만 인자 의미가 RBER) | 설계 판단 필요 |
| 45 | `MinSumDecoder(code, max_iter=args.max_iter)` | **파손 없음** | — |
| 4 | docstring `python -m 2_LDPC_light.mpi_runner <code.qc>` | 개정본 docstring은 `LDPC_base` 기준 — 본체 반영 시 상충 (A1) | 문서만 |

실증 (Ref-C `.qc`를 주고 실행):
```
File ".../ldpclight/mpi_runner.py", line 56, in main
    r = run_fer_point(code, fn, dec, rng, target_errors=10 ** 9,
TypeError: run_fer_point() got an unexpected keyword argument 'target_errors'
```
구 포맷 `.qc`를 주면:
```
File ".../ldpclight/pcm.py", line 61, in load
ValueError: .../irregular_17x144_z256.qc: Ref-C 헤더가 아님 ...
```

### 2-8. `2_LDPC_light/llr/README.md` — 문서 예시 파손

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 27 | `llr = fixed_error_llr(code, n_err, B, rng, mag=mag)` | 함수 부재 — **문서 예시가 죽음** (복사해 쓰면 AttributeError) | 문서라 조용함 |
| 24 | `prof = load_profile('2_LDPC_light/llr/chA_thmid.txt')` | **선행 문제**: `chA_thmid.txt`가 실재하지 않음 (실제 파일: `_hw_orig_ch.txt`, `ch5577_th842.txt`, `ch6666_th842.txt`, `ch66810_th842.txt`, `ch6688_th842.txt`, `ch6688_th952.txt`, `ch6688_th1052.txt`, `ch6688_thdv.txt`). **이번 개정과 무관한 기존 문서 표류** | 조용함 |
| 14-20 | 프로파일 표 5행 (`chA_thmid`/`chB_thmid`/`chA_thlow`/`chA_thhigh`) | 위와 동일 — 파일명 전부 실재하지 않음 (기존 표류) | 조용함 |
| 3, 25, 26 | `llr_tables.py` 참조, `MinSumDecoder(code, llr_profile=prof)`, `ch_mag_by_col` | **파손 없음** | — |

### 2-9. `2_LDPC_light/README.md` — 문서 서술 불일치 (런타임 무해)

| 라인 | 구문 | 깨지는 방식 | 조용함 |
|------|------|-------------|--------|
| 11 | "`pcm.py` … 자체 텍스트 포맷 입출력" | Ref-C 전용으로 바뀌어 서술 부정확 | 문서 |
| 13 | "`channel.py` BSC(hard) / AWGN(soft, 균일 양자화)" | 실제는 rber/fixed_error/strong_error 3종, 반환도 dict | 문서 |
| 15 | "`sim.py` … target_errors까지 배치 반복" | 키 이름이 `max_frame_errors`로 변경 | 문서 |
| 12, 44 | "`encode()`는 현재 스텁" | 개정본은 "임시 함수" 표현으로 통일 (내용 동일) | 문서 |
| 21-22, 28 | `examples/fer_curve.py`·`fer_curve.json` 실행 안내 | 2-1/2-2대로 실행 불가 | 문서 + 실행 |
| 34 | `python -m 2_LDPC_light.run 2_LDPC_light/examples/fer_curve.json` | 실행하면 **KeyError: 'H_matrix'** | 아니오 |
| 27 | `python -m 2_LDPC_light.tools.gen_example_code` | **파손 없음** | — |
| 39-45 | 알려진 갭 목록 | LLR matrix/syndrome-aided 도입이 반영되지 않음 | 문서 |

### 2-10. `2_LDPC_light/docs/plan.md` — 문서 서술 불일치 (런타임 무해)

| 라인 | 구문 | 상태 |
|------|------|------|
| 51 | "`pcm.py` H-matrix 파일 로드 (기존 포맷 그대로 파싱)" | 구 포맷 지원 삭제로 부정확 |
| 53 | "`llr_tables.py` 2-9 포맷 LLR 테이블 파일 로드" | 유효 (llr_tables 무변경). 단 DAO LLR_MATRIX 경로가 문서에 없음 |
| 54 | "`channel.py` AWGN/BSC + HD/2SD/3SD 양자화" | 개정본이 실제로 3SD까지 구현 — 오히려 계획에 근접했으나 함수명/반환형 기술 없음 |
| 56 | "`sim.py` … (`run_fer_point`)" | 함수명 유지되어 유효 |
| 57 | "`run.py` … load_config → setup → run_experiment → report" | 4단계 구조 유지되어 유효 |
| 128 | §7 #6 "config의 `channels` 리스트(채널별 `points` 리스트)로 단일·다중 채널·포인트를 동일하게 처리" | **확정 사항과 정면 충돌** — 개정본은 `channel.use`로 1개만 선택. 사용자 결정 사항이므로 **Decision 등급** |
| 126 | §7 #4 "max_iter = 120 (사용자 지정)" | 개정본은 LLR matrix 파일의 마지막 `iter_end`가 결정 — 확정 사항 갱신 필요 |
| 50 | `config.py` 행 (실재하지 않는 파일) | 기존 표류 |

### 2-11. `1_LDPC_revised/_pm/tasks/260803_iteration당속도측정/` — 저장소 밖(다른 프로젝트) 의존처

`measure_speed.py`는 `importlib.import_module("2_LDPC_light.*")`로 **문자열 동적 임포트**를 쓴다.
정적 grep으로 놓치기 쉬운 경로다.

| 파일:라인 | 구문 | 깨지는 방식 | 조용함 |
|-----------|------|-------------|--------|
| `measure_speed.py:38` | `chan = importlib.import_module("2_LDPC_light.channel")` | 임포트는 성공 — 지연 폭발 | 조용함 |
| `measure_speed.py:62` | `llr = chan.bsc_llr(code, rber, b, rng, mag=ch_mag)` | **AttributeError: module has no attribute 'bsc_llr'**. **주의: 이 줄은 개정 이전에 이미 깨져 있다** — 현행 본체 서명은 `bsc_llr(code, cw, rber, rng, mag)`라 `AttributeError: 'float' object has no attribute 'shape'`가 난다 (실증 확인). 즉 **기존 파손**이며 개정본이 에러 종류만 바꾼다 | 아니오 |
| `measure_speed.py:137` | `dec.decode_batch(chan.bsc_llr(code, args.rber[0], args.batch, rng_w, mag=ch_mag))` | 위와 동일 (기존 파손) | 아니오 |
| `measure_speed.py:110` | `code = QCCode.load(args.code)` | 기본값 `2_LDPC_light/examples/irregular_17x144_z256.qc`(42행) → **ValueError: Ref-C 헤더가 아님**. `--code`로 `irregular_15x145_z256.qc`(Ref-C)를 주면 **정상** | 아니오 |
| `measure_speed.py:36,37,39,40` | `pcm`/`decoder`/`llr_tables` 동적 임포트 | **파손 없음** | — |
| `measure_speed.py:70,74,77` | `dec.decode_batch(llr)`, `res["success"]`, `res["n_iter"]`, `dec.max_iter` | **파손 없음** (decode_batch 반환 키 동일) | — |
| `measure_speed.py:118-119` | `MinSumDecoder(code, max_iter=, schedule=, llr_profile=)` | **파손 없음** | — |
| `measure_speed.py:116-117` | `load_profile(path)`, `ch_mag_by_col(code, profile)` | **파손 없음** | — |
| `gen_code_15x145.py:25-26` | `import_module("2_LDPC_light.pcm").QCCode`, `..."2_LDPC_light.tools.gen_example_code").build_code` | **파손 없음** | — |
| `gen_code_15x145.py:43-44` | `QCCode(code.base[:, perm], Z)`, `code.save(OUT)` | **파손 없음** (save는 Ref-C 그대로) | — |
| `README.md:17` | "채널: BSC (bsc_llr)" | 문서 서술만 무효화 | 문서 |
| `README.md:56` | `--code ...irregular_15x145_z256.qc` | **파손 없음** (Ref-C 헤더 실측) | — |
| `README.md:89` | "`.qc` 부호 파일은 gitignore 대상이라 다른 환경에서는 `select_irregular.py` 재실행" | 2-5로 재실행 불가. 다만 `.qc` 2개는 실제로 git 추적 중(`git ls-files` 확인)이라 이 서술 자체가 부정확 | 문서 |

### 2-12. 파손되지 않는 본체 코드 (음성 결과는 4장에 정리)

`tools/peg.py`, `tools/lifting.py`, `tools/gen_example_code.py`, `tools/__init__.py`,
`examples/__init__.py`(빈 파일), `llr/*.txt` 8개, `examples/out/*` (결과 데이터).

### 2-13. 리뷰 기록 문서 (코드 파손 아님, 분류만)

`2_LDPC_light/docs/review/r1_*`·`r2_*`(과거 리뷰 기록), `_pm/tasks/20260806_review/*`(이번 리뷰),
`_pm/DONE.md:7,9,11,13`, `_pm/TODO.md`, `_pm/tasks/20260806_가독성리팩토링/*.md:99`,
`_pm/tasks/20260806_출력폴더_로그기능/*.md:78`.
이들은 **당시 시점 기록**이므로 갱신 대상이 아니다. 다만 `_pm/DONE.md:9`("`bsc_llr`/`awgn_llr`이
codeword를 인자로 받도록 변경")와 `_pm/DONE.md:11`("`run_fer_point`/`save_csv`는 유지")은
이번 변경으로 무효화되므로, **DONE.md에 새 항목을 추가**하는 방식으로 처리하면 된다 (기존 항목 수정 불필요).

---

## 3. 사용한 grep 패턴 전부 (재현용)

공통 제외 옵션:
```
EX='--exclude-dir=.git --exclude-dir=__pycache__ --exclude-dir=20260806_review --exclude-dir=review'
```
(첫 패턴만 `--exclude-dir=20260806_review` 없이 실행했다. 이후 전부 제외.)

저장소 루트(`d:/OneDrive/My_Projects/LDPC_dev`)에서:

```bash
# 나. channel.py 공개 함수
grep -rn --binary-files=without-match $EX -E "bsc_llr|awgn_llr|fixed_error_llr|awgn_rber" .

# 다. sim.py API
grep -rn --binary-files=without-match $EX -E "run_fer_point" .
grep -rn --binary-files=without-match $EX -E "save_csv" .
grep -rn --binary-files=without-match $EX -E "target_errors|TARGET_ERRORS" .
grep -rn --binary-files=without-match $EX -E "stop_below" .

# 가. 설정 JSON 키
grep -rn --binary-files=without-match $EX -E "code_file" .
grep -rn --binary-files=without-match $EX -E "\"channels\"|config\[.channels.\]|channels\]" .
grep -rn --binary-files=without-match $EX -E "max_iter" . --include="*.json" --include="*.md"

# 사. run.py API
grep -rn --binary-files=without-match $EX -E "load_config|run_experiment|runner\.|from \.\. import run" .

# 라. pcm.py / .qc
grep -rn --binary-files=without-match $EX -E "QCCode|\.qc\b" .

# 마. llr_profile / llr_tables
grep -rn --binary-files=without-match $EX -E "llr_profile|llr_tables|load_profile|ch_mag_by_col|LLRProfile|dv_group" .

# 바. decoder API
grep -rn --binary-files=without-match $EX -E "decode_batch|MinSumDecoder\(|\[.n_iter.\]|\[.success.\]|collect_profile" .

# 문자열 동적 접근 경로
grep -rn --binary-files=without-match $EX -E "getattr\(|globals\(\)|eval\(|import_module|__dict__|locals\(\)" .

# 채널 레지스트리 / 채널 이름 문자열
grep -rn --binary-files=without-match $EX -E "_CHANNEL_FNS|CHANNELS|CHANNEL_MODES|\"bsc\"|'bsc'|\"awgn\"|'awgn'" .

# _test 안에서 본체 임포트 여부
grep -rn --binary-files=without-match -E "2_LDPC_light|import_module|sys\.path" 2_LDPC_light/_test --exclude-dir=__pycache__

# CI/빌드/설정 파일 존재 여부
git ls-files | sed 's/.*\.//' | sort | uniq -c | sort -rn
git ls-files | grep -iE "\.(yml|yaml|toml|cfg|ini|bat|sh|ps1|mk|txt)$|Makefile|\.github|\.gitignore|requirements"
grep -n "2_LDPC_light\|LDPC_light" 0_LDPC_original/build.bat
git ls-files | grep -E "\.(qc|py|json)$|\.(qc|py|json)\"$"
```

파일 직접 확인:
```bash
head -8 2_LDPC_light/examples/example_18x147_z256.qc
head -8 2_LDPC_light/examples/irregular_17x144_z256.qc
head -8 "2_LDPC_light/_test/20260806_setup_구성_실험/Input/H_matrix/example_18x147_z256.qc"
head -3 "1_LDPC_revised/_pm/tasks/260803_iteration당속도측정/irregular_15x145_z256.qc"
```

스크래치패드 실증 스크립트: `t1_import.py`(모듈 17개 임포트), `t2_qc.py`(.qc 로드),
`t3.py`(시그니처 파손 순서), `t4.py`(.qc 행렬 대조), `cfg_migrated.json`/`cfg_nodir.json`(조용한 무시·기본값 이동).

---

## 4. "깨지지 않는다고 확인한 것" (음성 결과)

실행으로 확인한 것과 대조로 확인한 것을 구분해 적는다.

### 4-1. 실행으로 확인 (합성 트리에서 임포트/실행)

| 대상 | 결과 |
|------|------|
| `ldpclight` (패키지 루트, `__init__.py`) | OK |
| `pcm`, `channel`, `decoder`, `encoder`, `sim`, `run`, `llr_tables`, `llr_matrix` | 전부 OK |
| `mpi_runner` (임포트만) | OK (실행은 2-7대로 실패) |
| `tools.peg`, `tools.lifting`, `tools.gen_example_code` | 전부 OK |
| `examples.fer_curve` (임포트만) | OK (실행은 2-1대로 실패) |
| `examples.select_irregular` (임포트만) | OK (실행은 2-5대로 실패) |
| `tools.gen_example_code.build_code()` + `code.save()` + `QCCode.load()` 왕복 | **OK** — 생성된 헤더 `20 6 / 3 10 / 16`, 재로드 성공 |
| `llr/*.txt` 8개 × `load_profile()` | **8개 전부 OK** |
| `run_fer_point(..., max_frame_errors=...)` 신 시그니처 | OK (`{'frames': 8, 'errors': 3, 'fer': 0.375}`) |
| `MinSumDecoder` 반환 dict 키 `success`/`n_iter` | 변화 없음 (sim.py가 그대로 쓴다) |

### 4-2. 파일 대조로 확인

| 대상 | 결론 |
|------|------|
| `llr_tables.py` | 인터페이스 **완전 동일**. 차이는 docstring 4행 한 곳뿐 (`LLRProfile`/`dv_group`/`ch_mag_by_col`/`load_profile`/`_KEYS` 모두 동일) |
| `encoder.py` | 인터페이스 **완전 동일** (`generate_message`, `encode`). docstring만 변경 |
| `__init__.py` | 두 파일 **완전 동일** — 재수출 심볼 5개 그대로. 간접 의존 파손 경로 없음 |
| `sim.save_csv` | 본문 **완전 동일** — CSV 헤더 6열, 참조 키(`param`/`fer`/`frames`/`errors`/`avg_iter_ok`/`sec`) 불변 |
| `pcm.QCCode.save` | **완전 동일** (Ref-C 출력). 기존 `.save()` 호출부 3곳(`select_irregular.py:106`, `gen_example_code.py:54`, `gen_code_15x145.py:44`) 무영향 |
| `pcm.QCCode.__init__` / `syndrome` / `count_cycles4` / `summary` / 속성(`col_deg`, `edge_row`, `edge_shift`, `col_edges`, `E`, `N`, `K`, `rate`, `M_b`, `N_b`, `z`) | 전부 동일 |
| `MinSumDecoder.decode_batch` 시그니처·반환 키 | 동일. `collect_profile` 동작도 동일 |
| `MinSumDecoder` 생성자 | 인자 **추가만** (`llr_matrix=None`) — 기존 호출부 전부 하위 호환 |
| `tools/peg.py`, `tools/lifting.py` | `pcm`/`channel`/`sim`/`run` 어느 것도 참조하지 않음. **무영향** |
| `1_LDPC_revised/_pm/tasks/.../irregular_15x145_z256.qc` | 이미 Ref-C 헤더(`145 15`/`11 52`/`256`) — **로드 정상** |
| `0_LDPC_original/build.bat` | `2_LDPC_light` 참조 없음 |
| CI 설정 / `requirements.txt` / `pyproject.toml` / `setup.cfg` / `Makefile` | 저장소에 **존재하지 않음** (`git ls-files` 확인). 추적 파일 확장자는 md/patch/cpp/h/py/txt/qc/json/bat/gitkeep/gitignore뿐 |
| `_test/` 안 파일이 본체를 임포트하는가 | **아니오** — `LDPC_base/*.py`는 전부 상대 임포트(`from .pcm import ...`). `2_LDPC_light` 문자열은 docstring/README에만 등장 |
| `examples/out/*.csv`, `*.png` | 결과 데이터. gitignore(`out/`) 대상이라 추적조차 안 됨. 무영향 |
| `examples/__init__.py`, `tools/__init__.py` | 빈 파일. 무영향 |

### 4-3. "이번 개정 때문이 아닌" 기존 파손 (혼동 방지)

| 위치 | 내용 |
|------|------|
| `1_LDPC_revised/_pm/tasks/260803_iteration당속도측정/measure_speed.py:62,137` | `chan.bsc_llr(code, rber, b, rng, ...)`는 **현행 본체에서도 이미 실패**한다 (`AttributeError: 'float' object has no attribute 'shape'`, 실증 확인). 2026-08-05 cw 인자 도입 때 갱신되지 않은 잔존 파손 |
| `2_LDPC_light/llr/README.md:14-20,24` | 표에 적힌 프로파일 파일 5개(`chA_thmid.txt` 등)가 전부 실재하지 않음. 실제 파일명은 `ch6688_th842.txt` 계열. 기존 문서 표류 |
| `2_LDPC_light/docs/plan.md:50` | `config.py` 행 — 실재하지 않는 파일. 기존 표류 |
| `1_LDPC_revised/_pm/tasks/.../README.md:89` | "`.qc`는 gitignore 대상"이라 하나 실제로는 git 추적 중 |

---

## 5. 한눈 요약 — 파손 건수

| 분류 | 건수 | 대상 |
|------|------|------|
| 임포트 시점 즉사 (ImportError) | 2 | `examples/fixed_error_sweep.py:15`, `examples/llr_tune.py:18` |
| 실행 중 즉사 (TypeError/AttributeError) | 2 | `examples/select_irregular.py:39`, `mpi_runner.py:56` |
| 설정 로드 즉사 (KeyError/ValueError) | 2 | `examples/fer_curve.py:67` + `examples/fer_curve.json:2,4,12` |
| 데이터 로드 즉사 (ValueError) | 2 | `examples/*.qc` 2개 (변환은 헤더 3줄 재작성으로 해결 가능) |
| **조용한 무시 / 조용한 동작 변화** | 5 | `fer_curve.json:7` `target_errors`, `:10` `stop_below`, `output.dir` 기본값 이동(A2), `pcm.py:15` DV 내림차순 전제 미강제(A6), `select_irregular.py:29`·`gen_example_code.py:22` 오름차순 degree(A7) |
| 문서 서술 불일치 (런타임 무해) | 4 파일 | `README.md`, `docs/plan.md`(§7 #6은 **Decision** 등급), `llr/README.md`, `1_LDPC_revised/.../README.md` |
| 저장소 밖 의존처 | 1 파일 | `1_LDPC_revised/_pm/tasks/.../measure_speed.py` (`.qc` 기본값 + 기존 `bsc_llr` 파손) |
| **무영향 확인** | 다수 | `tools/` 4파일, `llr/*.txt` 8개, `llr_tables.py`, `encoder.py`, `__init__.py`, `save_csv`, `QCCode.save`, `decode_batch` 반환 키, `gen_code_15x145.py`, `irregular_15x145_z256.qc`, CI/빌드 설정(부재) |

가장 주의할 점: **조용히 무시되는 5건**이다. `target_errors`/`stop_below`는 예외 없이 기본값으로
대체되어 측정 조건이 바뀐 채 결과가 나오고, `output.dir` 기본값 이동은 결과 파일이 다른 폴더에 쌓인다.
`docs/plan.md:128` §7 #6("`channels` 리스트로 단일·다중 채널을 동일 처리")은 확정 사항과 정면 충돌하므로
**작업을 멈추고 사용자 확인이 필요한 Decision 등급**이다.
