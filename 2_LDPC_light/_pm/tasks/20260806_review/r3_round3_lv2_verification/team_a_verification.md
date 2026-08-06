# Round 3 / team_a — 채널·실행 검증 (F1, F3, F19)

> 작성: 2026-08-06 23:44:26
> 담당 발견: F1 (HIGH, `channel.py` argpartition 순서 편향), F3 (HIGH, run 하위 키 조용한 무시),
> F19 (MEDIUM, `batch<=0` hang 심각도 재평가)
> 워커: `worker_a_1.md` (F1), `worker_a_2.md` (F3), `worker_a_3.md` (F19)
> 방법: 가설 형식화 → 증거 도출 → 워커 3개 병렬 독립 재확인 (Round 2 결론 무전제) → 팀 리더 교차 검토
> 환경: numpy 1.26.4, Python 3.11.7. 프로젝트 파일 수정 0건, C++ 빌드 0건

---

## 0. 판정 요약

| 발견 | 발견 자체 | 심각도 | 처방 |
|------|-----------|--------|------|
| F1 | **확인됨** (원본 대조·수치 실증 모두 재현) | HIGH → **조건 병기 "HIGH(2SD 디코딩 구현 시)"** | **수정 필요** — 적용 위치를 바꿔야 함 |
| F3 | **확인됨** (HIGH 유지) | HIGH 유지 | **부분 유효** — 방향 맞으나 범위 불완전 |
| F19 | **부분 확인** (hang 재현, 트리거 범위는 반박됨) | MEDIUM → **CRITICAL(batch = 정수 0일 때)** | **유효하되 확장 필요** |

신규 발견 2건이 나왔다. 둘 다 원 발견보다 파급이 크다.

- ㉮ **`decoder` 블록 이름 오타(`decoderr`)가 디코더를 통째로 교체하고 조용히 완주한다** (F3 확장, 아래 §3-4)
- ㉯ **`mpi_runner.py:55`의 `frames // size`가 계산으로 0이 되는 실 경로다** (F19의 실질 위험은 `batch`가 아니라 `max_frames`, 아래 §4-3)

---

## 1. 가설 목록

### F1 계열

| ID | 가설 |
|----|------|
| H1-a | `channel.py:73`의 argpartition은 앞 k개의 **집합**만 균일하고 **순서**는 introselect가 남긴 결정적 잔여라, `strong_error`가 `pos[:, :e2]`를 잘라 strong 에러로 쓸 때 위치가 column block에 편향된다 |
| H1-b | 원본 `random.cpp` `rand_sel_ep`는 부분 Fisher–Yates이므로 앞 `n_err_len`개의 **순서까지** 균일 무작위이고, 소비 측이 구간별로 잘라 쓰므로 순서 무작위성이 곧 strong/weak 배정의 무작위성이다 |
| H1-c | 처방 `rng.permuted(p, axis=1)`을 적용하면 원본과 통계적으로 등가가 되고, `fixed_error`(순서 무의미) 결과는 불변이며, rng 상태 소비 변화의 부작용이 없다 |
| H1-d | F1은 `strong_error` 전용이며 `fixed_error`, `rber`에는 영향이 없다 |

### F3 계열

| ID | 가설 |
|----|------|
| H3-a | `run.py:109-118`이 `run_cfg.get()`만 쓰므로 run 하위 미지 키(구 이름, 오타)가 무검증 통과하고 기본값으로 실행된다 |
| H3-b | run 하위 합법 키의 전수 목록은 6개(`max_frame_errors`, `max_frames`, `batch`, `stop_below_fer`, `verbose`, `seed`)이며, 화이트리스트가 이 6개를 덮으면 처방이 완결된다 |
| H3-c | 화이트리스트가 향후 확장을 막지 않으며, 기존 config 자산 중 거부되는 것이 없다 |
| H3-d | agent_5의 "최상위 키만 걸리고 run 하위 키는 전부 새는 비대칭"이라는 구조 서술이 정확하다 |

### F19 계열

| ID | 가설 |
|----|------|
| H19-a | `sim.py:17-18`에서 `batch <= 0`이면 `b = 0`이라 `frames`가 증가하지 않고 `errors`도 0이라 두 종료 조건이 영원히 미충족되어 hang한다 |
| H19-b | 심각도 기준표에 "hang = CRITICAL"이 실재하며, F19는 그 정의에 해당한다 |
| H19-c | 트리거가 비정상 설정값이라는 이유로 MEDIUM 강등한 Round 2 판단이 타당하다 |
| H19-d | 처방 `if batch <= 0: raise` 한 줄이 모든 hang 경로를 막는다 |

---

## 2. F1 — argpartition 순서 편향

### 2-1. 증거 확인 결과

| 증거 | 판정 | 근거 |
|------|------|------|
| E1. 원본 `rand_sel_ep`가 부분 Fisher–Yates | **확인됨** | `0_LDPC_original/random.cpp:343-369` (Round 2 인용 행 번호 정확). identity 초기화 `:351-354`, 셔플 `:356-368`의 `s = (tmp % (len_max - j)) + j` |
| E1-㉰. 앞 k개의 순서까지 균일 | **확인됨** | 원문을 그대로 전사해 실측. n=6, k=3, 60만 시행에서 순서있는 k-순열 카이제곱 114.1 (자유도 119). 모듈로 편향 8.76e-06으로 무시 가능 |
| E1-㉱. 소비 측이 구간별로 잘라 씀 | **확인됨** | `0_LDPC_original/ecc_top.cpp:1707-1723` (2SD 분기). 함수 실체는 `Make_Dec_Input_Ref_C_Fixed_4KB` = `ecc_top.cpp:1828-1920` |
| E2-㉮. 뽑힌 **집합**은 균일 | **확인됨** | 블록 카이제곱 85.5 (자유도 146). 집합에는 문제 없음 |
| E2-㉰. strong 위치 편향 | **확인됨** | strong 카이제곱 **2,439,055** (Round 2 보고 3,547,197과 10^6 자릿수 일치, 시드에 따라 2.27M~2.48M). 상위 2블록 점유율 **36.7%** (Round 2 37.1%), 블록별 개수도 1% 이내 일치 (블록0: 78,519 대 79,189) |
| E2 추가. 프레임 간 상관 | **확인됨 (신규)** | 프레임 간 strong 집합 교집합 평균 10.44개. 균일 기대 0.215의 **48배** |
| E3-㉮. `permuted(axis=1)`이 행별 독립 셔플 | **확인됨** | 20만 행 실측. `permutation`/`shuffle`은 전 행에 같은 순열을 적용하므로 **대체 불가**. 반드시 `permuted`여야 함 |
| E3-㉯㉰. permuted가 편향을 제거 | **확인됨** | permuted 후 카이제곱 150.9, argsort 151.1 (자유도 146). 두 방식의 동질성 카이제곱 143.9로 구분 불가 |
| E3-㉱. 비용 | **확인됨** | B=128, N=37632: argpartition 63.8ms / argpartition+permuted 94.1ms / argsort 288.3ms |
| E4-㉮. permuted가 rng 상태를 소비 | **확인됨** | 팀 리더 직접 재확인. 동일 시드에서 permuted 호출 뒤 `rng.random(3)`이 갈림 (`0.192463…` 대 `0.239489…`). 행별 집합은 보존됨 |
| **E4-㉲. "fixed_error 결과 불변"** | **부분 반박됨** | `_rand_positions` 내부에 permuted를 넣으면 **첫 배치만 동일하고 배치 1부터 전부 갈라진다** (frame0 교집합 1/300). 통계 단위로만 참이고 비트 단위 재현성은 깨진다 |
| E4 신규. argsort 전면 교체 | **확인됨 (신규)** | argsort는 fixed_error에 **비트 단위로 완전 무해**하다. 동일 시드 5배치 연속 실행에서 `hd` 배열도 rng tail도 현행과 완전 일치 (집합이 동일하고 fixed_error는 집합 전체를 flip하므로) |
| E5. strong_error 도달 불가 | **확인됨** | 3케이스 실제 실행. `run.py:89`가 mode를 항상 `"HD"`로 만들고 `run.py:90-93`이 ValueError. HD 파일을 `LLR_MATRIX_2SD_9.txt`로 위장해도 `decoder.py:62-64`가 NotImplementedError로 차단 |
| H1-d. fixed_error 무해 | **확인됨** | agent_2의 카이제곱 140.7 재현 (140.5). argpartition과 argsort의 카이제곱이 자릿수까지 동일 |

### 2-2. 판정 — 발견 자체: 확인됨

H1-a, H1-b, H1-d 모두 참이다. Round 2가 보고한 수치가 독립 재현으로 자릿수와 개별 블록 수준까지 일치했다. 원본 인용 행 번호도 전부 정확하다.

### 2-3. 판정 — 심각도: "HIGH(2SD 디코딩 구현 시)" 조건 병기

워커는 "실행 경로에 도달 불가"를 근거로 HIGH → MEDIUM 하향을 권고했으나, 팀 리더는 **조건 병기**가 옳다고 판정한다.

- ㉮ 기준표(`review.md:88`)의 HIGH는 "틀린 결과를 내지만 프로세스는 계속됨"이다. `strong_error`가 도달 불가인 현재로는 이 정의에 해당하지 않는다
- ㉯ 그러나 도달 불가의 원인은 F1과 무관한 별개 결함(`decoder.py:62-64`의 2SD 미구현 TODO)이다. 그 TODO가 풀리는 순간 F1은 **어떤 경고도 없이 발현**한다
- ㉰ Round 2 자신이 F4~F7을 "HIGH(반영 시)"로 조건 병기했다. 같은 관행을 따르면 F1은 **"HIGH(2SD 디코딩 구현 시)"** 이다. 단순 MEDIUM 하향은 "시한 결함"이라는 성질을 라벨에서 지운다

### 2-4. 판정 — 처방: 수정 필요 (적용 위치 변경)

Round 2 원 처방("`_rand_positions` 안에서 argpartition 결과에 permuted 추가")은 **정확성은 달성하나 부작용이 있다**. `_rand_positions`는 `fixed_error`(`channel.py:83`)와 `strong_error`(`channel.py:109`) 양쪽이 공유하므로, 내부에 permuted를 넣으면 `fixed_error`의 배치 1 이후 rng 흐름이 전부 갈라져 기존 실측 CSV가 재현되지 않는다.

대안 3종의 실측 비교:

| 대안 | 정확성 | fixed_error 재현성 | 비용 (B=128) | 권고 |
|------|--------|--------------------|--------------|------|
| ㉮ `strong_error_channel`에서만 permuted (`channel.py:109` 직후) | 해결 | **완전 보존** (호출 자체가 없음) | 실질 0 | **1순위** |
| ㉯ `np.argsort` 전면 교체 | 해결 | **완전 보존** (집합 동일, rng 소비 동일) | 63.8ms → 288.3ms (4.5배) | 2순위 |
| ㉰ `_rand_positions` 내부 permuted (Round 2 원안) | 해결 | **배치 0만 일치, 이후 상실** | 63.8ms → 94.1ms | 비권고 |

부수 조건: 어느 대안을 택하든 `channel.py:72` docstring의 "rand_sel_ep 대응"이라는 문구는 현재 거짓이므로 함께 손봐야 한다.

주의 사항: `rng.permutation` / `rng.shuffle`은 전 행에 같은 순열을 적용하므로 처방으로 쓸 수 없다. 반드시 `permuted(axis=1)`이어야 한다.

---

## 3. F3 — run 하위 키 조용한 무시

### 3-1. 증거 확인 결과

| 증거 | 판정 | 근거 |
|------|------|------|
| H3-a. `.get()` 전용 접근 | **확인됨** | `run.py:110-114` 5곳 + `run.py:118` 1곳. 설정 변형 30종 실측으로 Round 2 실측 3종을 독립 재현 |
| E2-㉮㉯. 구 이름 `target_errors`, `stop_below` 통과 | **확인됨** | 예외 없이 통과하고 기본값으로 실행 |
| E2-㉰. `run` 블록 통째 삭제 | **확인됨** | `max_frame_errors=50`, `max_frames=20000`, `batch=128` |
| E2-㉱. 순수 오타(`max_frame_error`) | **확인됨** | 통과 |
| H3-b. 합법 키 6개 | **확인됨** | 실험 폴더 전 모듈 grep 결과 run 설정을 읽는 곳은 `run.py` 한 곳뿐. 6곳 모두 `run_experiment()` 함수 스코프이므로 화이트리스트 한 곳으로 전부 덮인다. **Round 2 처방의 전제가 정확하다** |
| H3-c. 기존 자산 거부 없음 | **확인됨** | 저장소 JSON 4개 전수 확인. 거부 대상은 `examples/fer_curve.json`의 `target_errors`/`stop_below` 2개뿐이며, 이 파일은 이미 `code_file` 때문에 `run.py:46`에서 먼저 죽는다 (F4 소관). 주석 키(`_comment` 등) 관행 0건 |
| **H3-d. 비대칭 구조 서술** | **반박됨** | 정확한 규칙은 "최상위 키만 걸린다"가 아니라 **"`config[...]`로 직접 인덱싱하는 필수 키의 부재만 걸린다"**. 최상위 미지 키 추가는 조용히 통과하고, 선택 블록 3개(`decoder`/`run`/`output`)는 **블록 이름 자체가 샌다** |
| E5. "78배" 파급 | **조건부 확인** | 산술(20000/256 = 78.1)은 맞으나 FER < 2.5e-3 구간에서만 실현. 현행 config는 FER=1.0 포화라 실측 파급은 2.11배 (3.74초 → 7.91초, frames 64 → 128) |

### 3-2. run 하위 합법 키 확정 목록

| 키 | 읽는 라인 | 기본값 | 비고 |
|----|-----------|--------|------|
| `max_frame_errors` | `run.py:110` | 50 | |
| `max_frames` | `run.py:111` | 20000 | |
| `batch` | `run.py:112` | 128 | |
| `stop_below_fer` | `run.py:113` | None | |
| `verbose` | `run.py:114` | True | 실험 README 스키마에 미기재 |
| `seed` | `run.py:118` | 12345 | `ch_cfg.get("seed", run_cfg.get("seed", 12345))`의 2단계 fallback. 실험 README 스키마에 미기재 |

### 3-3. 판정 — 발견 자체: 확인됨 (HIGH 유지)

H3-a, H3-b, H3-c 모두 참이다. 처방이 전제한 합법 키 6개 목록도 정확하다. 다만 구조 서술(H3-d)은 부정확하므로 보고서 문구를 정정해야 한다.

### 3-4. 신규 발견 — `decoder` 블록 이름 오타가 디코더를 통째로 교체한다

H3-d 반박 과정에서 나온 것으로, **F3 본체보다 파급이 크다.**

원인은 `run.py:47` `dec_cfg = config.setdefault("decoder", {})`이다. 최상위 키를 `decoderr`로 한 글자 틀리면 `decoder` 블록이 없는 것으로 처리되어 빈 dict가 만들어지고, 디코더가 전 항목 기본값(`schedule="two_set"`, `matrix=None`, `max_iter=20`, 채널 LLR 하드코딩 ±8)으로 구성된 뒤 **예외 없이 완주한다**. 동일 H-matrix, 채널, seed, run 설정에서 실측:

```
baseline       column_wise  matrix=True   -> FER=0.9844  errors=63
decoderr_typo  two_set      matrix=False  -> FER=0.0000  errors=0
```

run 키 오타의 최악 파급(실행 시간, 통계량 변화)보다 나쁘다. 같은 실험을 표방하는 두 CSV가 **서로 다른 알고리즘의 수치**를 담게 되고, `sim.py:36-43`이 설정 메타를 하나도 남기지 않으므로 사후 판별도 불가능하다.

### 3-5. 판정 — 처방: 부분 유효 (방향 타당, 범위 불완전)

블록별 검증 비대칭 지도상 누수 7종 중 run 화이트리스트는 1종만 막는다.

| 블록 | 오타 시 동작 | 근거 |
|------|--------------|------|
| 최상위 필수 키 (`H_matrix`, `channel`) | KeyError (걸림) | `run.py:46`, `run.py:57` 직접 인덱싱 |
| 최상위 미지 키 추가 | 조용히 통과 | 검사 없음 |
| `decoder` 블록 이름 | **조용히 통과 + 디코더 교체** | `run.py:47` setdefault |
| `decoder` 하위 키 | TypeError (걸림) | `run.py:82` `MinSumDecoder(**dec_cfg)` |
| `run` 블록 이름/하위 키 | 조용히 통과 | `run.py:109-118` |
| `channel.<use>` 하위 키 | 조용히 통과 | `run.py:63`, `:96`, `:118` |
| `output` 블록 이름/하위 키 | 조용히 통과 | `run.py:53-55`, `:136-142` |

권고:

- ㉮ run 화이트리스트에 더해 **최상위 키 화이트리스트**를 함께 넣는다 (합법 키 5개 고정. 두어 줄로 `decoderr`/`runn`/`outputt` 3종을 동시에 차단)
- ㉯ 구현 방식은 하드코딩 상수보다 **기본값 dict 단일 정본**(`_RUN_DEFAULTS`에서 키를 읽어 검사) 또는 **dataclass**를 쓴다. 후자는 `run.py:82`의 `MinSumDecoder(**dec_cfg)`와 메커니즘이 같아져 비대칭 자체가 줄어든다. 하드코딩 목록은 사용처와 화이트리스트를 이중 관리하게 되므로 확장을 막는다
- ㉰ 화이트리스트가 6개를 합법화하는데 실험 `README.md:51` 스키마는 4개만 보여 준다 (`verbose`, `seed` 미기재). 문서를 함께 고쳐야 한다

---

## 4. F19 — `batch<=0` hang 심각도 재평가

### 4-1. 증거 확인 결과

| 증거 | 판정 | 근거 |
|------|------|------|
| H19-a. hang 재현 | **확인됨** | 계측 루프 2000회(65.5초) 후에도 `frames=0 errors=0`. 실제 `run_fer_point` 45초 timeout exit 124 |
| E1. `channel_fn(0)`, `decode_batch(B=0)`이 예외 없이 통과 | **확인됨** | `hd.shape=(0,147,256)`, `success=array([], dtype=bool)` 반환. 루프가 조용히 계속됨 |
| **E1-㉯㉰㉱. 트리거 범위 "`batch<=0`"** | **반박됨** | hang을 일으키는 값은 **정수 0 하나뿐**이다. 음수는 즉시 `ValueError: negative dimensions are not allowed`, 실수/bool은 `TypeError`, `null`은 `min()`에서 `TypeError`. 전부 0.00초 즉사 |
| E1-㉲. hang의 성질 | **확인됨** | 단일 코어 CPU 99.5~100%, RSS 32.5MB 고정 (30초간 증가 0). **OOM으로 죽지 않고 영원히 돈다** |
| E1-㉳. 복구 가능성 | **확인됨** | Ctrl+C latency 0.015초. CSV 쓰기는 `run_experiment` 반환 후이므로 **데이터 손상 없음** |
| E2-㉰. `batch>=1`에서 `b=0` 가능성 | **반박됨 (안전 확인)** | 원리적으로 불가능함을 증명하고 3481조합 전수 실측으로 확인. **정상 설정에서는 hang 경로가 없다** |
| E2-㉮. `batch`를 계산으로 만드는 코드 | **반박됨** | 저장소 전체 0건. 전부 상수 64/128 또는 argparse 기본값 |
| **E2 신규. `max_frames`는 계산 경로가 있다** | **확인됨 (신규)** | `mpi_runner.py:55` `my_frames = args.frames // size + …`. `--frames 63 -np 64`면 64랭크 중 1개가 `my_frames=0` → `sim.py:24`에서 ZeroDivisionError |
| E2-㉯. `run_fer_point` 직접 호출처 | **확인됨** | 4곳 (`mpi_runner.py:56`, `examples/` 3곳). **전부 `load_config`를 우회한다** |
| E2-㉰(CI). 무인 실행 맥락 | **부재 확인** | `.github` 없음. cron/slurm/nohup grep 0건 |
| **H19-b. 심각도 기준표 실재** | **확인됨** | 팀 리더 직접 확인. `C:\Users\yongs\.claude\prompts\review.md:87` — CRITICAL 정의가 문자 그대로 **"프로세스 중단/hang 또는 데이터 비가역 손상"**. context.md의 전제가 사실이다 |

### 4-2. batch 값 유형별 동작

| batch 값 | 동작 | 소요 |
|----------|------|------|
| 정수 0 (Python int, numpy 정수) | **무한 hang** (CPU 100%, 메모리 고정) | 영구 |
| 음수 | `ValueError: negative dimensions are not allowed` | 0.00초 |
| 실수 (0.5 등) | `TypeError` | 0.00초 |
| bool | `TypeError` | 0.00초 |
| `null` (None) | `min()`에서 `TypeError` | 0.00초 |
| 1 이상 정수 | 정상. `b=0`이 원리적으로 불가능 | 정상 |

### 4-3. 판정 — 심각도: CRITICAL(batch = 정수 0일 때) 조건 병기

기준표 문언이 명시적이므로 라벨을 바꾸지 않으면 보고서가 자기 기준과 모순된다.

- ㉮ **CRITICAL 승격이 맞다.** `review.md:87`의 CRITICAL은 결과가 hang이면 성립하며 트리거 조건을 완화 사유로 두지 않는다. MEDIUM 정의("엣지케이스 위험, 누락 커버리지")로 강등하려면 기준표 문언 자체를 고쳐야 한다
- ㉯ 다만 **조건 병기가 필요하다.** 유발값이 정수 0 하나뿐임이 실증되었으므로 "CRITICAL(batch가 정수 0일 때)"로 적는 것이 정확하다. Round 2가 F4~F7에 쓴 "HIGH(반영 시)"와 같은 관행이다
- ㉰ 기준표 자체의 결함도 기록해 둔다. CRITICAL/HIGH는 **결과** 축으로, MEDIUM은 **트리거** 축으로 정의되어 축이 섞여 있다. Round 2가 F19에서 겪은 혼선의 근원이다
- ㉱ **수정 우선순위는 F1/F3 다음이다.** 심각도 라벨과 수정 순서는 별개다. `2_LDPC_light`는 논문 아이디어 스크리닝용 시뮬레이터이므로(루트 `CLAUDE.md`), 조용히 틀린 수치가 판단을 오염시키는 F1/F3가 실질 피해는 더 크다. hang은 즉시 눈에 보이고 Ctrl+C로 0.015초에 복구되며 데이터 손상도 없다

H19-c(트리거 비정상성을 이유로 한 강등)는 **논거 자체는 타당하나 기준표와 충돌**한다. 강등 대신 조건 병기로 해소한다.

### 4-4. 판정 — 처방: 유효하되 확장 필요

H19-d는 참이다. 유발값이 정수 0뿐이므로 `batch <= 0` 한 줄로 hang은 완전히 막힌다. 다만 그대로 두면 불완전하다.

- ㉮ **위치**: `sim.py:run_fer_point` 진입부가 **필수**다. 직접 호출 4곳이 전부 `load_config`를 우회하기 때문이다. `run.py:load_config`에도 함께 두는 것을 권고한다 (fail-fast)
- ㉯ **타입 검사 선행**: `None`이나 문자열이면 `batch <= 0` 표현식 자체가 TypeError를 낸다. 설정 항목을 지목하는 메시지를 내려면 타입 검사가 먼저 와야 한다
- ㉰ **묶음 처리**: `max_frames <= 0`, `max_frame_errors <= 0`(agent_5 M-6)을 같은 곳에서 처리한다. 실질 위험은 오히려 `max_frames` 쪽이다 (§4-1 신규 발견)
- ㉱ **기존 설정 거부 위험 없음**: 저장소 전 config의 `batch`/`max_frames`/`max_frame_errors`가 모두 1 이상 정수임을 전수 확인했다
- ㉲ **연쇄 조건**: `mpi_runner.py`는 가드만 넣으면 `my_frames=0`인 랭크가 죽어 잡 전체가 실패한다. F6 수정 시 `my_frames == 0` 랭크 스킵을 함께 넣어야 한다

---

## 5. Round 2 보고서 정정 요청

| 항목 | Round 2 서술 | 정정 |
|------|--------------|------|
| F1 처방 | "`_rand_positions`의 argpartition 결과에 permuted 추가" | 적용 위치를 `strong_error_channel`로 한정하거나 argsort로 전면 교체. 현 위치는 `fixed_error` 비트 재현성을 깨뜨림 |
| F1 부작용 | "`fixed_error`는 영향 없음" | 통계 단위로만 참. 원 처방 적용 시 배치 1부터 비트 단위로 갈라짐 |
| F3 구조 (agent_5 H-1 마지막 줄) | "최상위 키만 걸리고 run 하위 키는 전부 새는 비대칭" | "직접 인덱싱하는 **필수** 키의 부재만 걸린다". 최상위 미지 키와 선택 블록 이름(`decoder`/`run`/`output`)은 전부 샘 |
| F3 파급 (agent_5 H-1) | "실행 시간이 78배" | 산술은 맞으나 FER < 2.5e-3 구간 한정. 현행 config 실측 파급은 2.11배 |
| F19 트리거 (agent_5 M-5) | "`batch <= 0`에서 무한 루프" | hang 유발값은 **정수 0 하나뿐**. 음수/실수/None은 0.00초 만에 예외 |

---

## 6. 검증 방법 기록

- 원문 대조: `0_LDPC_original/random.cpp` 330-370, `ecc_top.cpp` 1690-1930, `channel.py`/`run.py`/`sim.py` 전문, `review.md` 심각도 기준표
- 실행 실증(스크래치패드 전용, 프로젝트 파일 무수정): rand_sel_ep 원문 전사 후 60만 시행 순열 균일성 검정, argpartition/argsort/permuted 3방식 블록 카이제곱 대조, `permuted` 행별 독립성 20만 행 실측, rng 상태 소비 비교, 설정 변형 30종 `load_config`/`run_experiment` 실행, batch 유형 5종 + 3481조합 전수 실측, hang 프로세스 CPU/RSS 계측
- 부수 효과: `__pycache__/run.cpython-311.pyc` 재생성 (`_test/`는 gitignore 대상). `git status` 깨끗, 실험 `config.json`과 `Sim_Output/` mtime 불변 확인
