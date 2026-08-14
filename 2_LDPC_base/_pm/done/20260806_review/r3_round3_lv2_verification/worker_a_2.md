# Round 3 / worker A-2 — F3 (run 하위 키 조용한 무시) 검증

> 작성: 2026-08-06 23:31:39
> 담당: F3 (HIGH) 증거 확인 (E1~E5)
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/run.py`, 같은 폴더 `config.json`, `README.md`
> 검증 방식: 전수 grep + 스크래치패드 실측 (설정 변형 30종). 프로젝트 파일 무수정 확인 (`git status` 깨끗, 실험 `config.json`·`Sim_Output/` mtime 불변)

---

## 요약 판정

- **F3 발견 자체: 확인됨.** `run` 하위 6개 키 전부가 `.get()`만 쓰며, 구 이름(`target_errors`, `stop_below`)과 오타가 예외 없이 통과하고 기본값으로 실행되는 것을 실측 재현했다.
- **F3 진단의 한 문장은 반박됨.** agent_5 H-1의 "최상위 키만 걸리고 `run` 하위 키는 전부 새는 비대칭 구조"는 부정확하다. 실제 규칙은 "**직접 인덱싱(`config[...]`)하는 필수 키의 부재만 걸리고, `.get()`/`setdefault()`가 닿는 것은 최상위든 하위든 전부 샌다**"이다. 최상위에서도 선택 블록 3개(`decoder`, `run`, `output`)는 블록 이름 자체의 오타가 조용히 통과한다.
- **F3 처방(run 화이트리스트): 방향은 맞으나 불완전.** 같은 결함이 더 심한 형태로 `decoder` 블록 이름에 남는다. `decoder`를 `decoderr`로 한 글자 틀리면 디코더가 통째로 다른 것으로 바뀌면서 같은 실험의 FER이 0.9844에서 0.0000으로 갈리는 것을 실측했다. `run` 블록만 고치면 이 경로는 그대로 남는다.

---

## 증거별 판정표

| 증거 ID | 판정 | 근거 | 비고 |
|---|---|---|---|
| E1. `.get()` 전수 조사 | **확인됨** | `run.py:109` `config.get("run", {})`, `:110~:114` 5개, `:118` 1개. 실험 폴더 전체 grep 결과 `run_cfg`/`config["run"]`은 `run.py` 밖에 없음 | Round 2가 전제한 6개 키가 정확히 맞음. 빠진 키도, 없는 키도 없음 |
| E1-b. 타 모듈의 run 설정 접근 | **확인됨(없음)** | `sim.py`, `decoder.py`, `channel.py`, `llr_matrix.py`, `pcm.py`, `encoder.py` 전체에서 `config`/`cfg` 식별자 0건. `pcm.py:95-96`의 `by_row.get()`은 사이클 계수용 내부 dict로 설정과 무관 | `run.py`가 설정을 읽는 유일한 지점 |
| E2 ㉮ `run.target_errors: 5` | **확인됨** | 실측: `run PASS used={'max_frame_errors': 10, 'max_frames': 256, 'batch': 64, 'verbose': True}` (config의 `max_frame_errors: 10` 그대로, 5는 무시) | 예외 없음 |
| E2 ㉯ `run.stop_below: 1e-3` | **확인됨** | 실측: PASS, 2개 포인트 모두 실행 (`npoints=2`). 조기 중단 없음 | `stop_below_fer`는 `None` 유지 |
| E2 ㉰ `run` 블록 통째 삭제 | **확인됨** | 실측: `used={'max_frame_errors': 50, 'max_frames': 20000, 'batch': 128, 'verbose': True}` | 기본값 3종 Round 2 서술과 일치 |
| E2 ㉱ `run.max_frame_error` (s 누락) | **확인됨** | 실측: PASS, `max_frame_errors=10` (config 값) 사용. 오타 키는 무시 | |
| E2-추가. 구 이름만 넣은 `run` 블록 | **확인됨** | `{target_errors, stop_below, max_frame, batch_size}` 4개 전부 구/오타 이름 → `used={50, 20000, 128}` 전 기본값 | 최악의 조용한 오실행 형태 |
| E2-추가. `run.seed` 경로 | **확인됨** | `channel.<use>.seed` 제거 + `run.seed: 777` → rng `seed_seq.entropy = [777, 200000000]`. `run.seed`도 제거하면 `[12345, ...]` | `run.py:118`의 2단 폴백이 설계대로 작동 |
| E3 ㉮ 최상위 미지 키 | **반박됨(agent_5 서술)** | 실측: `H_matrix` 등을 정상 유지한 채 `foo`, `_comment`, `H_matrixx` 추가 → 전부 조용히 통과, 정상 실행. `H_marix` 오타는 원 키 `H_matrix`가 없어져서 `KeyError: 'H_matrix'`가 날 뿐, 오타 키 이름은 메시지에 나오지 않음 | 최상위는 "미지 키를 잡는" 것이 아니라 "필수 키 부재를 잡는" 것 |
| E3 ㉮-b 선택 블록 이름 오타 | **신규 발견(가장 심각)** | `decoderr` → setup PASS, `max_iter=20 schedule=two_set matrix=False` (디코더 교체). `runn` → 전 기본값. `outputt` → `output.dir`이 `{config위치}/Sim_Output`으로 조용히 이동 | `run.py:47,53,109`의 `setdefault`/`get`이 원인 |
| E3 ㉯ decoder 하위 키 TypeError | **확인됨** | 실측: `msg_clipp` → `TypeError: MinSumDecoder.__init__() got an unexpected keyword argument 'msg_clipp'`. `llr_matrixx`, `_comment`도 동일 | agent_5 ㉱ 재확인 성립 |
| E3 ㉯-b `load_config`가 손대는 키와의 상호작용 | **확인됨** | `max_iter` 금지 검사(`run.py:48-50`)는 `llr_matrix` 유무와 무관하게 발동 (실측: `llr_matrix` 제거 + `max_iter: 30` → 동일 ValueError). `llr_matrix` resolve(`:51-52`)는 키가 있을 때만 | M-1 재확인 |
| E3 ㉰ channel 블록 | **확인됨** | `channel` 이름 오타 → `KeyError: 'channel'`(`:57`). `use` 키 오타 → `KeyError: 'use'`(`:58`). `use` **값** 오타 → 친절한 ValueError(`:59-60`). 미지 채널 블록(`bsc`) 추가 → 조용히 무시. `channel.<use>` 하위 오타(`pointss`, `sed`, `SCRR`) → 조용히 무시 | |
| E3 ㉰-b `channel.<use>.seed` 오타 | **신규 발견** | 실측: `seed`를 `sead`로 오타 → 예외 없이 `run.seed`(없으면 12345)로 폴백. seed_seq가 `[20260806, ...]`에서 `[12345, ...]`로 바뀜 | 재현성이 조용히 깨지는 경로 |
| E3 ㉱ output 블록 | **확인됨** | 실측: `{dirr, csv_prefixx}` → `output.dir`이 `{config위치}/Sim_Output`, prefix가 `'fer'`. 예외 없음 | `run.py:53-55`, `:140` |
| E4 ㉮ 화이트리스트 확장성 | 아래 §4 참조 | | 대안 4종 비교 |
| E4 ㉯ 기존 검증 스타일 | **확인됨(일관)** | `llr_matrix._validate`(`llr_matrix.py:73-94`), `QCCode.load`(`pcm.py:59-74`), `MinSumDecoder.__init__`(`decoder.py:38-66`) 모두 fail-fast `raise ValueError/NotImplementedError` + 파일명·값 명시 | 단, 기존 검증은 전부 "있는 값의 정합성" 검사이고 "미지 키 거부"는 없음. 화이트리스트는 새 종류의 검사이나 스타일은 어긋나지 않음 |
| E4 ㉰ 엄격 검증이 깨뜨릴 것 | **확인됨(사실상 없음)** | 저장소 전체 JSON은 4개뿐. §5 표 참조. 본체에 구 이름이 남은 곳은 `examples/fer_curve.json:7,10`(`target_errors`, `stop_below`) 한 파일이며, 이 파일은 이미 `code_file`(`:2`) 때문에 `run.py:46`에서 먼저 죽는다(F4) | 화이트리스트가 새로 깨뜨리는 기존 자산 없음 |
| E4 ㉱ 주석 키 관행 | **확인됨(관행 없음)** | 저장소 JSON 4개 전부에서 `_comment`/`note`/`comment` grep 0건 | 다만 `decoder` 블록은 이미 `_comment`를 TypeError로 거부하므로, 주석 키를 쓰려면 별도 결정 필요 |
| E5-a "78배" 파급 | **부분 확인됨(조건부)** | 산술은 정확 (20000/256 = 78.125). 그러나 실현 조건은 `max_frame_errors`가 끝까지 도달하지 않는 저 FER 구간(FER < 50/20000 = 2.5e-3). 현행 config는 FER=1.0 포화라 첫 배치에서 종료 → 실측 파급은 **2.11배** (3.74s+3.62s → 7.91s+7.70s, frames 64→128) | "78배"는 상한이며 현행 설정에서는 발현하지 않음. 서술에 조건을 붙여야 정확 |
| E5-b CSV에 run 설정 미기록 | **확인됨** | `sim.py:40` 헤더가 `[param, fer, frames, errors, avg_iter_ok, sec]` 전부. 파일명은 `run.py:140` `{csv_prefix}_{ch_type}.csv`. run 설정·seed·H_matrix·llr_matrix 어느 것도 남지 않음 | M-11 연계 주장 성립. 사후 판별 불가 |

---

## 1. run 하위 합법 키 확정 목록

`run.py` 전체에서 `run_cfg`를 읽는 곳은 아래 6곳이 전부이며, 모두 `run_experiment()` 함수 안에 있다.

| 키 | 읽는 라인 | 기본값 | 타입 | 비고 |
|---|---|---|---|---|
| `max_frame_errors` | `run.py:110` | `50` | int | |
| `max_frames` | `run.py:111` | `20000` | int | |
| `batch` | `run.py:112` | `128` | int | |
| `stop_below_fer` | `run.py:113` | (없음 → `None`) | float 또는 null | 명시 기본값 없이 `.get()` 1인자 호출 |
| `verbose` | `run.py:114` | `True` | bool | 실험 README 스키마에 미기재 |
| `seed` | `run.py:118` | `12345` | int | `ch_cfg.get("seed", run_cfg.get("seed", 12345))`의 **2단 폴백 중간값**. `channel.<use>.seed`가 있으면 그것이 이기고, 없을 때만 쓰인다. 실험 README 스키마에 미기재 |

**결론: Round 2 처방이 전제한 6개 목록은 정확하다.** 빠진 키도 없고 존재하지 않는 키도 없다. 화이트리스트는 `run_experiment()` 안 한 곳에 두면 `:110~:114`와 `:118`을 모두 덮는다(둘 다 같은 함수 스코프).

`seed`에 대한 정밀 기록: `run_cfg.get("seed", 12345)`는 `ch_cfg.get`의 기본값 인자이므로 **매번 평가되지만, `ch_cfg`에 `seed`가 없을 때만 결과가 쓰인다**. 실측으로 세 갈래를 모두 확인했다.

- 1. `channel.<use>.seed = 20260806` 존재 → `seed_seq.entropy = [20260806, 200000000]`
- 2. `channel.<use>.seed` 제거 + `run.seed = 777` → `[777, 200000000]`
- 3. 둘 다 없음 → `[12345, 200000000]`

문서 격차: 실험 `README.md:51`의 스키마 예시는 `max_frame_errors`, `max_frames`, `batch`, `stop_below_fer` 4개만 보여 주고, 설명 항목(`README.md:66-69`)은 그중 2개만 서술한다. `verbose`와 `seed`는 문서 어디에도 없다. 화이트리스트로 6개를 합법화하면 문서와 코드의 합법 키 집합이 4대 6으로 어긋난다.

---

## 2. 블록별 검증 비대칭 지도

원리는 하나다. **`config[...]`로 직접 인덱싱하는 곳만 (그 키의 부재가) 예외를 낳고, `.get()`이나 `.setdefault()`가 닿는 곳은 전부 조용히 샌다.** 아래 표에서 "샘"으로 표시된 행이 그 결과다.

| 블록 / 대상 | 오타 시 동작 | 근거 라인 | 실측 |
|---|---|---|---|
| 최상위 `H_matrix` **부재** | `KeyError: 'H_matrix'` (오타 키 이름은 메시지에 없음) | `run.py:46` | 확인 |
| 최상위 `channel` **부재** | `KeyError: 'channel'` | `run.py:57` | 확인 |
| 최상위 **미지 키 추가** (`foo`, `H_matrixx`) | **샘** (조용히 무시, 정상 실행) | 검사 없음 | 확인 |
| 최상위 `decoder` → `decoderr` | **샘 + 최악** (디코더가 기본값 생성자로 교체: `max_iter=20`, `schedule=two_set`, `matrix=False`) | `run.py:47` `setdefault` | 확인 |
| 최상위 `run` → `runn` | **샘** (전 기본값 실행) | `run.py:109` `.get` | 확인 |
| 최상위 `output` → `outputt` | **샘** (출력이 `{config위치}/Sim_Output`으로 이동) | `run.py:53-55` `setdefault` | 확인 |
| `decoder.<하위키>` 오타 | `TypeError: ... unexpected keyword argument '...'` | `run.py:82` `MinSumDecoder(**dec_cfg)` | 확인 |
| `decoder.max_iter` | `ValueError` (llr_matrix 유무와 무관하게 발동) | `run.py:48-50` | 확인 (M-1) |
| `channel.use` **키 부재** | `KeyError: 'use'` | `run.py:58` | 확인 |
| `channel.use` **값** 오타 | 친절한 `ValueError` (후보 나열) | `run.py:59-60` | 확인 |
| `channel.<미지 블록>` 추가 (`bsc`) | **샘** | 검사 없음 | 확인 |
| `channel.<use>.points` **부재** | `KeyError: 'points'` | `run.py:63` | 확인 |
| `channel.<use>.seed` 오타 | **샘** (`run.seed` → 12345로 폴백, 재현성 조용히 변경) | `run.py:118` | 확인 |
| `channel.strong_error.SCR`/`SER` **부재** | `KeyError: 'SCR'` (단 현행 HD 모드에서는 `run.py:90` 모드 검사가 먼저 걸림) | `run.py:96` | 확인 |
| `output.dir` 오타 | **샘** (`{config위치}/Sim_Output` 기본값) | `run.py:53-55` | 확인 |
| `output.csv_prefix` 오타 | **샘** (`'fer'` 기본값) | `run.py:140` | 확인 |
| `run.<6개 키>` 오타 / 구 이름 | **샘** (각 기본값) | `run.py:110-114,118` | 확인 |

### 2-1. 가장 심각한 누수의 실측 (블록 이름 `decoderr`)

`decoder`를 한 글자 틀리면 `run.py:47`의 `config.setdefault("decoder", {})`가 빈 dict를 만들고, `MinSumDecoder(code)`가 전 기본값으로 생성된다. `llr_matrix`가 사라지므로 `run.py:89`의 `mode`가 `"HD"`로 고정되고 `fixed_error` 채널과도 호환되어, **경고 한 줄 없이 끝까지 돈다**.

FER 포화(M-12)를 피하려고 `fixed_error.points`를 30으로 낮추고 같은 seed로 비교한 실측이다.

```
[baseline]       max_iter=20 schedule=column_wise matrix=True  -> FER=0.9844 frames=64 errors=63 avg_iter_ok=1.00
[decoderr_typo]  max_iter=20 schedule=two_set     matrix=False -> FER=0.0000 frames=64 errors=0  avg_iter_ok=3.16
```

같은 H-matrix, 같은 채널, 같은 seed, 같은 `run` 설정인데 **한 글자 오타로 FER이 0.9844와 0.0000으로 갈린다**. `run` 하위 키 오타의 최악 파급(실행 시간 78배, 통계량 변화)보다 훨씬 나쁘다. 결과 수치 자체가 다른 알고리즘에서 나오기 때문이다.

이것은 M-2(schedule 기본값 분기)와 같은 뿌리이나, 트리거가 "llr_matrix 한 줄을 지움"이 아니라 "블록 이름 한 글자 오타"라는 점에서 훨씬 걸리기 쉽다.

### 2-2. 결론

**F3 처방이 `run` 블록만 고치면 위 표의 "샘" 행 중 마지막 한 줄만 막힌다.** 나머지 6개 누수(최상위 미지 키, `decoder`/`output` 블록 이름, 미지 채널 블록, `channel.<use>.seed`, `output` 하위 키)는 그대로 남고, 그중 하나(`decoderr`)는 F3 본체보다 심각하다.

---

## 3. E5 파급 서술의 정밀 검증

agent_5 H-1의 "실행 시간이 78배" 서술을 실측과 대조했다.

| 항목 | 값 |
|---|---|
| config.json `max_frames` | 256 (`config.json:8`) |
| 코드 기본값 `max_frames` | 20000 (`run.py:111`) |
| 산술 비 | 20000 / 256 = 78.125 |
| **현행 config에서의 실측 파급** | frames 64 → 128 (**2.11배**: 3.74s+3.62s → 7.91s+7.70s) |

78배가 실현되려면 `max_frames`가 종료를 결정해야 한다. 즉 `max_frame_errors`(기본 50)에 끝내 도달하지 않는 구간, 대략 FER < 50/20000 = 2.5e-3이어야 한다. 현행 config는 FER=1.0으로 포화(M-12)라 첫 배치에서 `max_frame_errors`가 먼저 걸리고, 기본값으로 돌 때도 `batch` 64→128, `max_frame_errors` 10→50이 함께 바뀌면서 실제 차이는 2.11배에 그친다.

**판정: 산술과 방향은 맞으나 "78배"는 저 FER 구간에서만 성립하는 상한이다.** Round 2 서술에 조건을 붙이는 것이 정확하다. 다만 이 정정은 F3의 심각도를 낮추지 않는다. 실물 H-matrix 반입 후 FER 곡선을 훑는 것이 이 시뮬레이터의 본래 용도이고, 그 구간이 바로 78배가 실현되는 구간이기 때문이다.

CSV 사후 판별 불가 주장도 확인했다. `sim.py:36-43`의 `save_csv`는 헤더를 `[param, fer, frames, errors, avg_iter_ok, sec]`로 고정하고, 파일명은 `run.py:140`에서 `{csv_prefix}_{ch_type}.csv`뿐이다. `run` 설정, seed, `H_matrix`, `llr_matrix` 어느 것도 파일명에도 내용에도 남지 않는다. 따라서 구 키 오실행이 일어나도 산출물만 보고는 판별할 수 없다.

---

## 4. 화이트리스트 처방의 확장성 검토

### 4-1. 대안 4종 비교

현재 코드 구조는 기본값이 `run.py:110-114,118` 여섯 줄에 흩어져 있고, 여섯 줄 모두 `run_experiment()` 한 함수 안에 있다. 이 구조가 대안 선택을 좌우한다.

| 대안 | 형태 | 장점 | 단점 |
|---|---|---|---|
| A. 하드코딩 화이트리스트 (Round 2 처방 문면) | `_RUN_KEYS = {...}` 상수 + `set(run_cfg) - _RUN_KEYS` 검사 | 변경량 최소(3줄), 기존 `.get()` 여섯 줄을 건드리지 않음 | **키 추가 시 두 곳 수정**(사용처 + 상수). 기본값은 여전히 흩어져 있어 문서화 근거가 코드에 없음 |
| B. 기본값 dict 단일 정본 | `_RUN_DEFAULTS = {"max_frame_errors": 50, ...}` 6개 → `unknown = set(run_cfg) - set(_RUN_DEFAULTS)` 검사 후 `cfg = {**_RUN_DEFAULTS, **run_cfg}` | 키와 기본값이 한 곳에 모임(이중 관리 소멸). 문서 생성·비교의 근거가 됨. `seed` 2단 폴백도 `ch_cfg.get("seed", cfg["seed"])`로 오히려 단순해짐 | `.get()` 여섯 줄을 인덱싱으로 바꾸는 소폭 리팩터. `stop_below_fer`의 기본값 `None`을 명시해야 함 |
| C. dataclass 또는 TypedDict | `@dataclass class RunConfig: max_frame_errors: int = 50 ...` → `RunConfig(**run_cfg)` | 미지 키 거부가 **공짜**(TypeError). 타입 힌트가 스키마 문서 역할. 단일 정본. **이 저장소가 이미 쓰는 메커니즘**(`run.py:82` `MinSumDecoder(**dec_cfg)`)과 동일하므로 블록 간 동작이 통일됨 | 예외가 `TypeError: RunConfig.__init__() got an unexpected keyword argument 'target_errors'`라 **어느 설정 블록인지 메시지에 없음**(`decoder` 블록이 이미 같은 약점). 개명 안내를 넣으려면 별도 처리 필요 |
| D. 경고만 하고 진행 | `print(f"[warn] run 미지 키 무시: {sorted(unknown)}")` | 기존 config를 하나도 깨뜨리지 않음 | **이번 결함의 본질이 "조용함"인데 표준출력 경고로는 못 막는다.** `setup()`이 이미 `print(mx.summary())`로 같은 스트림을 쓰고(L-5) `verbose` 출력도 섞인다. 개명 직후라 구 키가 실제로 존재(`examples/fer_curve.json`)하므로 경고로는 오실행이 그대로 일어난다 |

**의견: B 또는 C를 권한다.** 이유는 세 가지다.

- ㉮ A는 처방의 문면에 가장 가깝지만 이중 관리를 새로 만든다. 이 시뮬레이터는 실물 파라미터 반입을 앞두고 `run` 키가 늘어날 가능성이 있어(예: 프레임 상한 외 시간 상한) 이중 관리의 비용이 실재한다.
- ㉯ C는 `decoder` 블록과 메커니즘이 같아져 §2 표의 비대칭 자체를 줄인다. 다만 예외 메시지에 블록 이름이 없다는 약점을 `decoder`와 함께 물려받는다.
- ㉰ B는 예외 메시지를 직접 쓸 수 있어(구 이름 → 새 이름 안내 포함 가능) 개명 직후 상황에 가장 잘 맞는다. 개명이 이번 변경의 핵심이므로 `target_errors`를 만나면 "`max_frame_errors`로 개명됨"이라고 짚어 주는 메시지가 화이트리스트의 실질 가치다.

### 4-2. 기존 검증 패턴과의 일관성

이 실험 폴더의 기존 검증 스타일을 읽었다.

- `llr_matrix.py:73-94` `_validate` — 헤더 개수와 배열 길이, 그룹 iteration 연속성, restart 그룹 형태를 검사하고 `ValueError(f"{self.name}: ...")`로 파일명을 앞에 붙여 던진다
- `pcm.py:59-74` `QCCode.load` — 헤더 형식, 원소 수, 헤더 J/K와 실제 degree 대조를 검사하고 `ValueError(f"{path}: ...")`로 던진다
- `decoder.py:38-66` 생성자 — 지원하지 않는 조합을 `NotImplementedError`, 모순 조합을 `ValueError`로 던진다
- `run.py:59-62` — `channel.use` 값이 목록 밖이면 후보를 나열한 `ValueError`

공통 스타일은 **fail-fast + 어느 파일 어느 값이 문제인지 명시**다. 화이트리스트는 이 스타일과 어긋나지 않는다.

다만 한 가지 차이를 짚어 둔다. **기존 검증은 전부 "있는 값의 정합성" 검사이고, "미지 키 거부"는 이 저장소에 선례가 없다.** 유일한 예외가 `MinSumDecoder(**dec_cfg)`인데 이것도 의도한 검증이 아니라 파이썬 호출 규약의 부수 효과다. 따라서 화이트리스트는 새로운 종류의 검사이며, 도입한다면 `run`만이 아니라 어느 블록까지 적용할지를 함께 정하는 편이 일관된다(§2-2).

### 4-3. 엄격 검증이 깨뜨릴 수 있는 것

저장소 전체에서 `run` 블록을 가진 JSON은 4개뿐이다(`find . -name "*.json"` 결과 전수).

| 파일 | `run` 하위 키 | 화이트리스트 판정 |
|---|---|---|
| `_test/20260806_setup_구성_실험/config.json:6-11` | `max_frame_errors`, `max_frames`, `batch`, `stop_below_fer` | 전부 합법, 통과 |
| `_test/20260806_setup_구성_실험/README.md:51` (스키마 예시) | 동 4개 | 전부 합법, 통과 |
| `_test/.../Sim_Output/_tmp_rber.json`, `_tmp_strong.json` | 동 4개 | 전부 합법 (이전 세션이 남긴 임시 산출물) |
| `2_LDPC_light/examples/fer_curve.json:6-11` | `target_errors`, `max_frames`, `batch`, `stop_below` | **2개 거부**(`target_errors`, `stop_below`) |

**결론: 화이트리스트가 새로 깨뜨리는 자산은 없다.** 유일한 거부 대상 `examples/fer_curve.json`은 이미 다른 이유로 죽는다. 같은 파일 `:2`가 `code_file`을 쓰므로 `run.py:46`의 `config["H_matrix"]`에서 `KeyError`가 먼저 나고, `:12` `channels`(리스트) 구조와 `:4` `decoder.max_iter`도 개정본과 맞지 않는다(F4와 동일 판정). 즉 이 파일은 화이트리스트 유무와 무관하게 재작성 대상이며, 오히려 화이트리스트가 있으면 재작성 시 구 이름을 놓치지 않게 된다.

본체에 구 이름이 남은 곳은 위 `fer_curve.json` 한 파일이 전부다. 본체 `README.md:15`와 `mpi_runner.py:56`, `examples/*.py` 4곳의 `target_errors`는 JSON 키가 아니라 **`run_fer_point`의 파이썬 인자명**이므로 화이트리스트와 무관한 별개 사안이다(F6 소관).

### 4-4. 주석 키 관행

저장소 JSON 4개 전체에서 `_comment`, `note`, `comment`, `_note` grep 결과 **0건**. 주석 키를 넣는 관행은 없다.

다만 실측에서 갈래가 갈리는 것을 확인했다.

- ㉮ `run`, `channel.<use>`, `output`, 최상위에 `_comment`를 넣으면 현재는 조용히 통과한다 → 화이트리스트 도입 시 거부된다
- ㉯ `decoder`에 `_comment`를 넣으면 **지금도** `TypeError: MinSumDecoder.__init__() got an unexpected keyword argument '_comment'`로 거부된다

관행이 없으므로 거부해도 깨지는 것은 없다. 주석을 허용하려면 `_`로 시작하는 키를 예외로 두는 방식이 있으나, `decoder` 블록은 여전히 거부하므로 블록마다 규칙이 갈리게 된다. 관행이 없는 이상 **일괄 거부가 단순하고 일관된다**는 것이 의견이다.

---

## 5. 최종 판정 의견

### 5-1. F3 발견 자체 — **확인됨 (심각도 HIGH 유지)**

Round 2의 실측 3종(`target_errors`, `stop_below`, `run` 블록 삭제)을 독립 재현했고, 처방이 전제한 합법 키 6개 목록이 정확함을 전수 grep으로 확정했다. 추가로 순수 오타(`max_frame_error`), 구 이름만 남은 `run` 블록, `run.seed` 경로까지 확인해 발견의 범위가 Round 2 서술보다 넓다는 것도 확인했다.

심각도 HIGH가 타당한 근거는 파급의 크기가 아니라 **탐지 불가능성**이다. 잘못된 값으로 돈 실험이 정상 종료하고, CSV(`sim.py:40`)에 run 설정이 남지 않아 사후 판별도 불가능하다(E5-b 확인). 개명 직후라 구 이름을 쓴 설정이 실재한다는 점(`examples/fer_curve.json`)이 이 발견을 가설이 아니라 현재 상태로 만든다.

정정할 서술이 두 곳 있다.

- 1. **"최상위 키만 걸리고 `run` 하위 키는 전부 새는 비대칭 구조"는 부정확하다.** 정확한 규칙은 "직접 인덱싱하는 필수 키의 **부재**만 걸린다"이다. 최상위 미지 키 추가는 조용히 통과하고, 선택 블록 3개는 이름 자체도 샌다(§2).
- 2. **"실행 시간이 78배"는 조건부다.** FER < 2.5e-3 구간에서만 성립하며, 현행 config에서의 실측은 2.11배다(§3).

두 정정 모두 발견을 약화시키지 않는다. 1번은 오히려 결함 범위를 넓히고, 2번은 실물 반입 후 본래 용도 구간에서 여전히 성립한다.

### 5-2. F3 처방(run 하위 키 화이트리스트) — **방향 타당, 범위 불완전. 처방 확대 권고**

㉮ **타당한 부분**: 화이트리스트는 결함을 정확히 막고, 저장소의 fail-fast 검증 스타일과 어긋나지 않으며(§4-2), 기존 자산 중 새로 깨뜨리는 것이 없다(§4-3). 도입 비용이 낮고 위험이 사실상 없다.

㉯ **불완전한 부분**: `run` 블록만 고치면 §2 표의 누수 7종 중 1종만 막힌다. 특히 **`decoder` 블록 이름 오타는 F3 본체보다 심각한데 처방 범위 밖**이다. 같은 실험이 FER 0.9844와 0.0000으로 갈리는 것을 실측했다(§2-1). "설정 오타가 조용히 다른 실험을 돌린다"는 결함을 고치겠다면서 그 결함의 최악 사례를 남기는 처방이 된다.

㉰ **권고**: 처방을 "**`run` 하위 키 화이트리스트 + 최상위 키 화이트리스트**"로 확대한다. 최상위는 합법 키가 4개(`H_matrix`, `decoder`, `channel`, `run`, `output` 5개)로 고정되어 있어 추가 비용이 두어 줄이고, 이것만으로 `decoderr`/`runn`/`outputt` 세 누수가 동시에 막힌다. `channel.<use>.seed`와 `output` 하위 키는 남지만, 그 파급(재현성 변경, 출력 위치 이동)은 디코더 교체보다 한 단계 낮으므로 후속으로 미뤄도 된다.

㉱ **구현 방식**: 하드코딩 상수(대안 A)보다 **기본값 dict 단일 정본(대안 B)** 또는 **dataclass(대안 C)**를 권한다(§4-1). B는 개명 안내 메시지를 직접 쓸 수 있어 이번 상황에 가장 잘 맞고, C는 `decoder` 블록과 메커니즘이 통일되어 비대칭 자체를 줄인다.

㉲ **함께 처리할 것**: 화이트리스트가 6개 키를 합법화하는데 실험 `README.md:51`은 4개만 보여 준다. `verbose`와 `seed`가 문서에 없으므로 스키마 서술을 6개로 맞춰야 코드와 문서의 합법 키 집합이 일치한다.

---

## 부록. 실측 환경과 재현 방법

- 실행 위치: 스크래치패드 (`.../scratchpad/e2_probe.py`, `e3_probe2.py`, `e3_decoderr.py`)
- 방식: 실험 폴더를 `sys.path`에 추가해 `LDPC_base.run`을 임포트하고, `config.json`을 메모리로 읽어 `H_matrix`/`decoder.llr_matrix`를 절대경로로 치환한 사본을 스크래치패드에 기록해 `load_config` → `setup` → `run_experiment`를 직접 호출
- 파라미터 실측: `run.run_fer_point`를 감싸 호출 인자와 `rng.bit_generator.seed_seq.entropy`를 가로챔 (`report()`는 호출하지 않아 실험 폴더 `Sim_Output/` 무오염)
- 무수정 확인: `git status --short` 결과가 본 리뷰 폴더(`_pm/tasks/20260806_review/`) 하나뿐, 실험 `config.json`(mtime 22:36)과 `Sim_Output/` 6개 파일 mtime 모두 불변
- 유일한 부수 효과: `LDPC_base/__pycache__/run.cpython-311.pyc` 재생성 (바이트코드 캐시, `_test/`는 `.gitignore` 대상, 소스 무변경)
