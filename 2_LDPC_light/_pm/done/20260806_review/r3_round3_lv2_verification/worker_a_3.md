# Round 3 / worker A-3 — F19 (`batch<=0` hang) 심각도 재평가 검증

> 작성: 2026-08-06 23:37:23
> 담당: F19 증거 확인 (E1 hang 메커니즘 재현, E2 트리거 현실성, E3 심각도 기준표, E4 정합성, E5 가드 처방)
> 검증 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/sim.py:14-24`
> 방법: 코드 정독 + 스크래치패드 실측 6종 (프로젝트 파일 무수정, 모든 무한 루프에 타임아웃/반복 상한 부과)
> Round 2 원 발견: `../r2_round2_lv1_analysis/agent_5.md` M-5(105-112행), M-6(114-118행)

---

## 0. 결론 요약

- ㉮ hang 자체는 **확인됨**. 다만 Round 2 표기 "`batch<=0` 무한 hang"은 **부정확**하다.
  실제로 hang하는 값은 **정수 0 하나뿐**이고, 음수/실수/None/문자열/bool은 전부 **즉시 예외**다.
- ㉯ hang의 성질: **단일 코어 100% busy loop, 메모리 증가 0, Ctrl+C로 15 ms 만에 중단 가능,
  데이터 손상 없음**. OOM으로 죽지 않고 영원히 돈다.
- ㉰ 심각도 기준표는 **실재한다** (`C:\Users\yongs\.claude\prompts\review.md:83-90`).
  CRITICAL 정의에 "hang"이 문자 그대로 들어 있다. context.md의 전제는 사실이다.
- ㉱ 트리거를 **계산으로** 0으로 만드는 경로는 `batch`에는 없고 **`max_frames`에는 있다**
  (`2_LDPC_light/mpi_runner.py:55`). 즉 F19의 무게 중심은 M-5(batch)가 아니라 **M-6(max_frames)** 쪽이다.
- ㉲ 판정 의견: **CRITICAL 승격 (조건부 표기 "CRITICAL(batch가 정수 0일 때만)")**, 단 수정 순서는
  F1/F3 다음. 근거는 §6.

---

## 1. 증거별 판정표

| 증거 ID | 판정 | 근거 (파일:라인 / 실측 출력) | 비고 |
|---|---|---|---|
| **E1-㉮** `batch=0` 무한 루프 | **확인됨** | `sim.py:18` `b = min(0, 256-0) = 0` → `sim.py:20` `frames += 0`. 계측 루프 2000회 반복 후에도 `frames=0 errors=0` (65.5 s, 31 it/s). 실 `run_fer_point(batch=0)`를 별도 프로세스에서 45 s timeout → exit 124 (강제 종료) | Round 2의 25 s 실측을 45 s와 2000회로 재확인 |
| **E1-㉮'** `decode_batch(B=0)` 무예외 | **확인됨** | 실측: `channel_fn(0, rng)` → `mode=HD hd.shape=(0,147,256)`, `dec.decode_batch(...)` → `success=array([],dtype=bool)`, `n_iter=array([],dtype=int32)`, `(~success).sum()=0`. `rng.random((0,N))`, `np.argpartition(..., 199, axis=1)[:, :200]` → `(0,200)` 정상. `_decode_matrix`는 `decoder.py:436` `keep.any()==False`로 iteration 1에서 break | 예외 없이 "빈 결과"를 돌려주므로 루프가 조용히 계속됨 |
| **E1-㉯** `batch=-1` | **반박됨 (hang 아님, 즉시 예외)** | 실측: `run_fer_point(batch=-1)` → 0.00 s `ValueError: negative dimensions are not allowed`. 발생 지점은 `encoder.py:12` `rng.integers(0,2,size=(-1,K))` (`run.py:99`가 먼저 호출) | Round 2 표기 "`batch<=0`"의 음수 부분은 성립하지 않음 |
| **E1-㉰** `batch=0.5` | **반박됨 (hang 아님, 즉시 예외)** | 실측: 0.00 s `TypeError: 'float' object cannot be interpreted as an integer` (`encoder.py:12`). `frames += 0.5`는 `sim.py:20`으로 `sim.py:19`의 예외보다 뒤에 있어 도달하지 않음 | 실수는 "천천히 종료"가 아니라 즉사 |
| **E1-㉱** `batch=null`(None) | **확인됨 (즉시 TypeError)** | 실측: 0.00 s `TypeError: '<' not supported between instances of 'int' and 'NoneType'` (`sim.py:18`의 `min()`에서 발생) | 메시지가 설정 항목을 지목하지 못함 (M-9와 같은 품질 문제) |
| **E1-㉲** busy loop 여부와 메모리 | **확인됨 (busy loop, 메모리 증가 없음)** | 자식 프로세스 30 s 샘플링(3 s 간격 10점): CPU **99.5~100.0 %** (논리 코어 24개 중 1개 포화), RSS **32.5 MB 고정, 증가 0**. 계측 루프 2000회에서도 RSS 불변 | 매 반복 배열이 모두 shape (0, …)이고 즉시 재바인딩되어 누적 없음 → **OOM으로 죽지 않고 영원히 돈다**. 전력과 열은 코어 1개분 |
| **E1-㉳** Ctrl+C 중단 가능성 | **확인됨** | 실측: `_thread.interrupt_main()`(CPython이 SIGINT 수신 시 세우는 것과 동일한 pending 플래그)로 8 s 시점 인터럽트 → `KeyboardInterrupt` **latency 0.015 s**, 중단 지점 `numpy/core/multiarray.py:346 where` | 순수 Python 루프 + 짧은 numpy 호출이라 bytecode 경계가 촘촘함. 별도 프로세스 CTRL_BREAK 전달 실측에서도 즉시 종료(exit 0xC000013A) |
| **E2-㉮** `batch` 계산 경로 | **반박됨 (계산으로 0이 되는 경로 없음)** | repo 전수 grep: `batch` 대입은 `run.py:112` `run_cfg.get("batch",128)`, `mpi_runner.py:33` argparse `type=int default=128`, `examples/fixed_error_sweep.py:24` `BATCH=128`, `examples/llr_tune.py:32` `BATCH=128`, `examples/select_irregular.py:34` `batch=128`. **나눗셈이나 모듈로로 batch를 만드는 코드 0건** | 다만 `mpi_runner.py:33` argparse는 `--batch 0` / `--batch -1`을 그대로 통과시킴(실측). CLI 오타는 가능 |
| **E2-㉮'** JSON 직접 지정 | **확인됨 (0만 hang)** | JSON 리터럴별 실측: `0`→int 0→**HANG**, `0.0`→float→TypeError, `-1`→ValueError, `null`→TypeError, `false`/`true`→TypeError, `"64"`→TypeError, `1e2`→TypeError. numpy 정수 0(`np.int64(0)`, `np.uint8(0)`)도 **HANG** | 저장소 내 모든 config의 batch 값은 64 또는 128 (§5-㉱) |
| **E2-㉯** `run_fer_point` 직접 호출처 | **확인됨 (4곳)** | `mpi_runner.py:56`, `examples/fixed_error_sweep.py:40`, `examples/llr_tune.py:41`, `examples/select_irregular.py:38`. 네 곳 모두 `load_config`를 거치지 않는 라이브러리 직접 호출 | 이 중 `mpi_runner.py:57`만 batch가 **런타임 값**(`args.batch`), 나머지 3곳은 상수 128 |
| **E2-㉰** batch>0에서 `b=0` 가능성 | **반박됨 (불가능, 증명 + 전수 실측)** | 증명: 루프 진입 조건이 `frames < max_frames`이므로 `d = max_frames - frames >= 1`(정수). `b = min(batch, d)`이므로 `batch >= 1`이면 `b >= 1` → 매 반복 `frames`가 1 이상 증가, 최대 `max_frames`회 만에 종료. 실측: `max_frames 1..59 × batch 1..59` 3481조합 전수 → `b<=0` 또는 비종료 사례 **0건** | 즉 **정상 설정(정수 batch>=1)에서 hang은 원리적으로 불가능**. `b == 0 ⟺ batch <= 0` |
| **E2-㉰'** float `max_frames` 상호작용 | **확인됨 (hang 아니라 예외)** | 실측: `max_frames=256.5, batch=64` → 4배치 후 `b=0.5` → `channel_fn` TypeError. `max_frames=100.5, batch=128` → `b=100.5` → TypeError. `max_frames=256.0`(정수값 float)은 정상 종료 | 소수점 `max_frames`는 마지막 부분 배치에서 즉사 |
| **E2-㉱** `max_frames<=0` | **확인됨 (hang 아니라 ZeroDivisionError)** | 실측: `max_frames=0` → `ZeroDivisionError: division by zero` (`sim.py:24` `fer = errors / frames`), `max_frames=-5` → 동일, `max_frame_errors=0` → 동일. 셋 다 0.00 s | agent_5 M-6 재확인. hang과 명확히 구분됨 |
| **E2-㉱'** `max_frames`의 계산 경로 | **확인됨 (실재)** | `mpi_runner.py:55` `my_frames = args.frames // size + (1 if rank < args.frames % size else 0)`. 실측: `--frames 63 -np 64` → 64랭크 중 **1개 랭크만 my_frames=0**, `--frames 32 -np 64` → 32/64 랭크가 0, `--frames 100 -np 128` → 28/128 랭크가 0 | **나눗셈이 0을 만드는 유일한 실 경로.** 단 현행 개정본에서는 `mpi_runner.py:56`이 구 인자명 `target_errors=`를 써서 F6의 TypeError가 먼저 나므로, F6 수정 후에 드러난다 |
| **E3** 심각도 기준표 실재 | **확인됨** | `C:\Users\yongs\.claude\prompts\review.md:83-90` (원문 §3). Round 2에서 실제로 인용해 쓴 흔적: `r2/agent_2.md:22` "**심각도: HIGH** (틀린 결과를 내지만 예외 없이 진행됨)", `r2/agent_2.md:94` "**심각도: MEDIUM** (엣지케이스, ...)" | context.md의 "심각도 기준표상 hang은 CRITICAL"은 **사실** |
| **E4-㉰** 자동화와 무인 실행 맥락 | **반박됨 (없음)** | `.github/` 없음, `*.yml`/`*.yaml` 0건, `nohup`/`cron`/`schtasks`/`sbatch`/`slurm`/`qsub` grep 0건. MPI 언급은 `mpi_runner.py:4` docstring의 `mpirun` 사용 예시 1건과 `docs/plan.md:21,109`, `2_LDPC_light/_pm/TODO.md:30` "mpi_runner 슈퍼컴 반입"(미완 작업)뿐 | 현재는 **대화형 단일 실행**만 존재. 다만 슈퍼컴 반입이 TODO에 있어 장래에는 무인 맥락이 생긴다 |
| **E5** 가드 유효성 | **부분 확인됨** | `batch <= 0` 단일 가드는 0/0.0/-1/False/numpy 0을 잡지만, `None`과 `str`에서는 **가드 표현식 자체가 TypeError**를 낸다(실측). 상세 §5 | 현행 동작도 None/str에서 TypeError이므로 퇴행은 아니나 메시지 개선도 없음 |

---

## 2. `batch` 값 유형별 동작 표 (전건 실측)

`run.py:112` → `sim.py:18` `b = min(batch, max_frames - frames)` → `sim.py:19` `channel_fn(b, rng)`
→ `run.py:99` `encoder.generate_message(code, b, rng)` → `encoder.py:12` `rng.integers(0,2,size=(b,K))`

| JSON 리터럴 | Python 값 | `min()` 결과 | 채널/인코더 단계 | 최종 동작 | 소요 |
|---|---|---|---|---|---|
| `"batch": 64` (정상) | `int 64` | `64` | OK | 정상 측정 (`frames=64 errors=64 fer=1.0`) | 3.96 s |
| **`"batch": 0`** | **`int 0`** | **`0`** | **OK (빈 배열)** | **무한 hang (busy loop)** | **∞** |
| `"batch": -1` | `int -1` | `-1` | `ValueError: negative dimensions are not allowed` | 즉시 예외 | 0.00 s |
| `"batch": 0.5` | `float 0.5` | `0.5` | `TypeError: 'float' object cannot be interpreted as an integer` | 즉시 예외 | 0.00 s |
| `"batch": 0.0` | `float 0.0` | `0.0` | 동일 TypeError | 즉시 예외 | 0.00 s |
| `"batch": 1e2` | `float 100.0` | `100.0` | 동일 TypeError | 즉시 예외 | 0.00 s |
| `"batch": null` | `None` | `TypeError: '<' not supported between instances of 'int' and 'NoneType'` | (미도달) | 즉시 예외 (`sim.py:18`) | 0.00 s |
| `"batch": false` | `bool False` | `False` | `TypeError: an integer is required` | 즉시 예외 | 0.00 s |
| `"batch": true` | `bool True` | `True` | 동일 TypeError | 즉시 예외 | 0.00 s |
| `"batch": "64"` | `str '64'` | `TypeError: '<' not supported between instances of 'int' and 'str'` | (미도달) | 즉시 예외 | 0.00 s |
| (코드 경유) `np.int64(0)` | numpy 정수 0 | `0` | OK (빈 배열) | **무한 hang** | ∞ |

> **핵심 정정**: hang을 일으키는 값은 **정수 0 (파이썬 int 또는 numpy 정수)** 뿐이다.
> Round 2의 "`batch<=0` 무한 hang"이라는 표기는 음수를 포함하는 것처럼 읽히나, 음수는 즉시 `ValueError`다.

### hang 상태의 성질 (30 s 샘플링 실측)

| 항목 | 측정값 | 해석 |
|---|---|---|
| CPU | 99.5~100.0 % (논리 코어 24 중 1개) | GIL 단일 스레드 busy loop. 대기(sleep/IO)가 아님 |
| RSS | 32.5 MB 고정, 30 s 동안 증가 0 | 매 반복 shape (0, …) 배열만 만들고 즉시 재바인딩 → **누적 없음 → OOM으로 죽지 않음** |
| 진행률 | 2000 반복 후에도 `frames=0 errors=0` | 종료 조건 두 개 모두 영원히 거짓 |
| 반복 속도 | 31 it/s (반복당 약 32 ms) | B=0이어도 `decoder.py:384` `for j in range(code.N_b)` 147회 × 20 iteration이 그대로 돌아 오버헤드만 소비 |
| 출력 | 없음 | `sim.py:30-32` verbose print는 포인트 종료 후라 화면에 아무것도 안 나옴 |
| Ctrl+C | latency 0.015 s로 `KeyboardInterrupt` | **복구 가능** |
| 데이터 영향 | 없음 | CSV 쓰기는 `run.py:155` `report()`, 즉 `run_experiment` 반환 후. hang 중에는 파일을 건드리지 않음 |

---

## 3. 심각도 기준표 — 원문 인용

정본 위치: `C:\Users\yongs\.claude\prompts\review.md:83-90` (`review` 프롬프트 "### 심각도 기준"). 원문 그대로:

```
### 심각도 기준

| 심각도 | 정의 | 액션 |
|--------|------|------|
| CRITICAL | 프로세스 중단/hang 또는 데이터 비가역 손상 | 즉시 수정 |
| HIGH | 틀린 결과를 내지만 프로세스는 계속됨 | 수정 권고 |
| MEDIUM | 엣지케이스 위험, 누락 커버리지 | 검토 후 판단 |
| LOW | 개선 제안 | 참고 |
```

프로젝트 `CLAUDE.md`와 `docs/`에는 별도 심각도표가 없다 (변경 등급표 Safe/Review/Decision은 별개 축).
Round 1과 Round 2 문서에도 기준표 원문 복사본은 없고, 위 표를 인용해 쓴 흔적만 있다.

### 기준표를 F19에 적용할 때 드러나는 구조 문제

- ㉮ **정의 축이 섞여 있다.** CRITICAL/HIGH는 **결과**로 정의되고(hang / 틀린 결과), MEDIUM은
  **트리거**로 정의된다(엣지케이스). F19는 결과 축으로는 CRITICAL, 트리거 축으로는 MEDIUM에
  동시에 해당한다. agent_5가 "결과는 무한 hang이지만 트리거가 비정상 설정값이라 MEDIUM"
  (`r2/agent_5.md:111`)이라고 쓴 것은 이 충돌을 트리거 축으로 해소한 판단이다.
- ㉯ **Round 2 관행은 결과 축을 우선하되 조건을 병기하는 쪽이었다.** F4~F7은 "지금은 아무것도
  깨지지 않는" 상태인데도 심각도를 낮추지 않고 **"HIGH(반영 시)"** 로 조건을 붙였다
  (`r2/agent_6.md:9` "본체 반영 파손은 '반영 시점에 터진다'는 조건부이므로 심각도 뒤에 조건을 적었다").
  **F19만 조건 병기가 아니라 등급 강등으로 처리된 것이 관행과 어긋난다.**
- ㉰ 다만 F5/F6(즉시 ImportError/TypeError)이 HIGH로 분류된 것을 보면, 실무에서
  "프로세스 중단"을 "모든 미포착 예외"로 넓게 읽지는 않았다. 넓게 읽으면 fail-fast 검증 예외까지
  전부 CRITICAL이 되어 무의미해지기 때문이다. **hang은 그런 해석 여지가 없는 유일한 항목**이다.

---

## 4. 다른 발견과의 심각도 정합성 (E4)

### ㉮ Round 2 HIGH 항목의 실피해 (`r2/report.md:12-18`)

| # | 실제 피해 유형 | 프로세스 | 탐지 가능성 |
|---|---|---|---|
| F1 `channel.py:71-73` | strong_error 에러 위치가 column block에 극단 편향(상위 2블록 37.1%) → **FER 수치가 틀림** | 계속됨 | **불가** (정상 종료, CSV에 정상 숫자) |
| F2 `decoder.py:68,388,398` | dv=2 구간 영구 미정정 11.6% → 현행 config FER ≡ 1.0 | 계속됨 | 어려움 (FER=1.0이 "정상 포화"로도 읽힘) |
| F3 `run.py:109-114` | 구 키와 오타가 조용히 무시되고 **다른 파라미터로 실험이 돎** | 계속됨 | **불가** (CSV에 run 설정 미기록) |
| F4~F7 (조건부) | 본체 반영 시 KeyError/ImportError/TypeError로 **즉사**, F7만 자산 소실 | 중단 | 즉시 (예외 메시지) |

즉 같은 HIGH 안에 **"조용히 틀린 결과"(F1, F2, F3)** 와 **"즉시 예외로 죽음"(F5, F6)** 이 섞여 있다.
기준표 문언대로면 후자는 HIGH 정의("틀린 결과를 내지만 프로세스는 계속됨")에 맞지 않는다.
agent_6은 이 어긋남을 "조건부" 라벨로 흡수했다.

### ㉯ hang(F19) vs 조용히 틀린 결과(F1, F3) — 실질 피해 비교

이 프로젝트의 목적은 `CLAUDE.md:14` "**논문 아이디어 스크리닝용 경량 Python 시뮬레이터**"다.
산출물은 아이디어 on/off의 상대 FER 비교이고, 그 숫자가 채택/기각 판단의 근거가 된다.

- **hang(F19)**: ㉠ 즉시 눈에 보인다(출력이 멈추고 CPU 1코어가 100%), ㉡ Ctrl+C로 15 ms 만에
  복구된다, ㉢ CSV를 건드리지 않으므로 기존 결과가 손상되지 않는다, ㉣ 메모리 누적이 없어
  시스템을 위협하지 않는다. 손실은 **사용자가 알아챌 때까지의 시간과 코어 1개분 전력**이다.
- **조용히 틀린 결과(F1, F3)**: ㉠ 정상 종료하고 그럴듯한 숫자를 남긴다, ㉡ CSV에 시드와 설정
  메타가 없어(F20/M-11) 사후 판별이 불가능하다, ㉢ 그 숫자로 아이디어를 채택/기각하면
  **오염이 후속 작업 전체로 전파된다**, ㉣ 되돌리려면 어떤 결과가 오염됐는지 특정해야 하는데
  그 수단이 없다.

**결론: 실질 피해는 F1과 F3 쪽이 크다.** F19를 CRITICAL로 올리더라도 **수정 순서에서 F1과 F3보다
앞세울 이유는 없다**. 기준표의 "액션" 열(CRITICAL=즉시 수정)은 난이도가 한 줄인 F19에는
사실상 비용이 0이므로, "같은 커밋에 함께 넣는다" 정도로 충족된다.

### ㉰ 무인 실행 맥락

현재 저장소에는 CI(`.github/` 없음), 스케줄러(`cron`/`schtasks`/`sbatch` grep 0건), 배치 실행
스크립트가 **없다**. 실행 형태는 `README.md`의 `python -m LDPC_base.run config.json` 대화형 1건뿐이다.
따라서 **"밤새 돌려놓고 아침에 보니 0 프레임"** 시나리오는 현재 성립하지 않으며, 이는 F19의
심각도를 낮추는 방향의 사실이다.

단 `2_LDPC_light/_pm/TODO.md:30` "mpi_runner 슈퍼컴 반입"이 미완 작업으로 등록되어 있고
`docs/plan.md:21,109`가 mpi4py 다중 랭크 실행을 계획하고 있다. **슈퍼컴 반입 시점에는
무인 다중 랭크 맥락이 생기고, 그때 실제로 위험한 것은 `batch`가 아니라 `max_frames`다**
(E2-㉱', `--frames 63 -np 64`에서 1개 랭크만 `my_frames=0`이 되는 부분 실패는 알아채기 어렵다).

---

## 5. 가드 처방 검증 (E5)

### ㉮ `if batch <= 0: raise ValueError(...)` 한 줄로 충분한가 — **부분적으로만**

| batch 값 | 현행 동작 | `batch <= 0` 가드의 반응 | 판정 |
|---|---|---|---|
| `int 0` | **hang** | `True` → ValueError | **막힘 (핵심 목적 달성)** |
| `np.int64(0)` | **hang** | `True` → ValueError | 막힘 |
| `int -1` | ValueError(numpy) | `True` → ValueError | 메시지 개선 |
| `float 0.0` / `-0.5` | TypeError(numpy) | `True` → ValueError | 메시지 개선 |
| `float 0.5` / `1e2` | TypeError(numpy) | `False` → **통과 후 같은 TypeError** | 미개선 |
| `bool False` | TypeError(numpy) | `True` → ValueError | 메시지 개선 |
| `bool True` | TypeError(numpy) | `False` → 통과 후 TypeError | 미개선 |
| `None` | TypeError(`min`) | **가드 표현식 자체가 TypeError** (`'<=' not supported between 'NoneType' and 'int'`) | 퇴행은 아니나 미개선 |
| `str '64'` | TypeError(`min`) | **가드 표현식 자체가 TypeError** | 퇴행은 아니나 미개선 |

**판정**: hang이라는 유일한 무한 증상은 `batch <= 0` 한 줄로 **완전히 막힌다**(hang 유발 값이 정수 0뿐이므로).
나머지 유형은 이미 즉시 예외라 hang 위험이 없다. 다만 메시지 품질(M-9와 같은 문제)까지 고치려면
타입 검사를 함께 넣는 편이 낫다:

```python
# 권고 형태 (한 곳에서 3개 키를 함께 처리)
for _name, _v in (("batch", batch), ("max_frames", max_frames),
                  ("max_frame_errors", max_frame_errors)):
    if isinstance(_v, bool) or not isinstance(_v, (int, np.integer)) or _v < 1:
        raise ValueError(f"run.{_name}는 1 이상의 정수여야 함 — 현재 {_v!r}")
```

- 이 형태는 None/str/bool/실수까지 **설정 항목 이름이 박힌 메시지**로 잡는다.
- 주의: JSON `"max_frames": 1e6`처럼 **정수값 실수**를 쓰던 설정이 있으면 거부된다.
  현재 저장소에는 그런 설정이 없다(§㉱). 허용하려면 `float`이고 `v.is_integer()`일 때
  `int(v)`로 강제 변환하는 분기를 추가한다. **어느 쪽을 택할지는 Decision 사항이 아니라
  취향 수준**이지만, 선택한 쪽을 실험 README 스키마에 한 줄로 명시해야 한다.

### ㉯ 가드 위치 — **둘 다 (필수: `sim.py`, 권고: `run.py`)**

- **`sim.py:run_fer_point` 진입부는 필수.** `run_fer_point`는 `load_config`를 거치지 않는
  **라이브러리 직접 호출처가 4곳** 있다: `mpi_runner.py:56`, `examples/fixed_error_sweep.py:40`,
  `examples/llr_tune.py:41`, `examples/select_irregular.py:38`. 이 중 `mpi_runner.py:57`은
  `--batch`가 argparse 런타임 값이고(실측: `--batch 0`, `--batch -1` 모두 통과),
  `mpi_runner.py:55`의 `max_frames`는 **나눗셈 계산값**이다. `load_config`에만 가드를 두면
  이 경로가 전부 무방비다.
- **`run.py:load_config` 검증 단계는 권고.** F3(run 하위 키 화이트리스트) 처방과 자연스럽게
  한 덩어리가 된다. 어차피 `run` 블록을 검증하는 코드를 새로 넣기 때문이다.
  fail-fast 이득은 실측상 크지 않다(`load_config` 0.000 s vs `setup` 0.002 s, 현 토이 코드 기준).
  실익은 **시간 절약보다 "설정 파일의 어느 키가 잘못됐다"를 설정 로드 단계에서 말해주는 것**이다.

### ㉰ 인접 값(`max_frames`, `max_frame_errors`)을 함께 막을 수 있는가 — **가능하고, 그렇게 하는 것이 맞다**

- 위 §㉮의 3-튜플 루프 한 덩어리로 세 키가 모두 처리된다.
- **묶어야 하는 실질적 이유**: E2-㉱' 실측대로 `max_frames`가 **실제로 계산으로 0이 되는 유일한 경로**
  (`mpi_runner.py:55`, `--frames 63 -np 64`에서 1개 랭크)를 갖고 있다. F19(M-5, batch)만 막고
  M-6(max_frames)를 남기면 실 위험이 큰 쪽을 놓친다.
- 다만 `mpi_runner.py` 경로는 지금 F6(인자명 변경)의 TypeError가 먼저 나므로, **F6 수정 시
  같은 커밋에서 `my_frames == 0`도 함께 처리**해야 한다 (예: `if my_frames == 0: 이 랭크는 스킵`).
  가드만 넣으면 랭크 일부가 ValueError로 죽어 MPI 잡 전체가 실패한다. 즉 **가드는 필요조건이지
  충분조건이 아니다**.

### ㉱ 기존 정상 설정을 거부하지 않는가 — **거부하지 않음 (전수 수집 확인)**

| 위치 | batch | max_frames | max_frame_errors / target_errors |
|---|---|---|---|
| `_test/.../config.json:7-9` | 64 | 256 | 10 |
| `_test/.../Sim_Output/_tmp_rber.json`, `_tmp_strong.json` | 64 | 256 | 10 |
| `2_LDPC_light/examples/fer_curve.json:7-9` | 128 | 3000 | 40 (구 이름 `target_errors`) |
| `examples/fixed_error_sweep.py:24` | 128 | 3000 | 40 |
| `examples/llr_tune.py:32` | 128 | 512 | 25 |
| `examples/select_irregular.py:60,73,97,109` | 128 (기본) | 512 / 3000 / 15000 / 1000 | 30 / 40 / 25 / 10**9 |
| `mpi_runner.py:33,55,56` | 128 (기본) | `frames//size + …` (계산값) | 10**9 |
| `sim.py:8` 기본값 / `run.py:110-112` 기본값 | 128 | 20000 | 50 |

전부 **1 이상의 정수**다. 유일한 위험은 `mpi_runner.py:55`의 계산값 `max_frames`가 0이 될 수 있는 것으로,
이는 §㉰에서 다룬 대로 가드 대상이자 별도 처리 대상이다.

---

## 6. F19 심각도 판정 — 의견과 근거

### 판정: **CRITICAL 승격, 단 조건 병기 — "CRITICAL(`batch`가 정수 0일 때만)"**

**근거**

- ㉮ **기준표 문언이 결과 축으로 정의되어 있고, hang이 명시적으로 열거되어 있다**
  (`review.md:87` "프로세스 중단/hang 또는 데이터 비가역 손상"). 트리거 희소성으로 등급을 내리는
  단서가 표 어디에도 없다.
- ㉯ **Round 2 자신의 관행이 "조건은 병기하고 등급은 결과로 매긴다"이다** (`r2/agent_6.md:9`,
  F4~F7의 "HIGH(반영 시)"). F19만 강등으로 처리한 것은 같은 보고서 안에서 일관되지 않는다.
  조건부 표기를 쓰면 "무섭게 보이는 라벨"과 "실제로는 잘 안 걸린다"가 동시에 전달된다.
- ㉰ **hang은 기준표의 다른 항목처럼 해석 여지가 넓지 않다.** "프로세스 중단"은 fail-fast 예외까지
  포함하면 무의미해지지만(그래서 F5/F6은 HIGH로 둔 것이 타당), "hang"에는 그런 확장 해석 문제가 없다.
- ㉱ **액션 열이 요구하는 "즉시 수정"의 비용이 사실상 0이다**. 가드 한 덩어리(3키 동시)로 끝나고,
  F3 처방(run 키 화이트리스트)과 같은 자리에 들어간다. CRITICAL로 두어도 작업 계획을 왜곡하지 않는다.

**함께 기록해야 할 완화 사실 (심각도 라벨과 별개로 보고서에 남길 것)**

- ㉠ hang 유발 값은 **정수 0 하나뿐**. Round 2 표기 "`batch<=0`"은 부정확하며 음수는 즉시 ValueError다.
- ㉡ 정상 설정(정수 `batch>=1`)에서는 **원리적으로 hang이 불가능**하다 (§E2-㉰ 증명 + 3481조합 전수 실측).
- ㉢ hang은 **조용하지 않다**: CPU 1코어 100%, 출력 정지. **Ctrl+C로 15 ms 복구**, 메모리 누적 0,
  CSV 무손상. "프로세스가 죽지 않고 자원만 먹는" 최악형 hang이 아니다.
- ㉣ 저장소에 **CI, 스케줄러, 무인 배치 실행 맥락이 없다**. 발견 즉시 사람이 개입할 수 있는 환경이다.
- ㉤ 수정 순서에서는 **F1과 F3(조용히 틀린 결과)이 우선**이다. 이 시뮬레이터의 산출물은
  논문 아이디어 채택/기각 판단의 근거이고, 그 숫자가 조용히 오염되는 쪽이 실질 손해가 크다.

**MEDIUM 유지가 정당화되는 유일한 조건**: 심각도 라벨을 "최악 결과"가 아니라 "기대 피해
(결과 × 발생 확률)"로 정의하기로 팀이 합의하는 경우다. 그러면 F19는 MEDIUM이 맞고 F4~F7의
조건부 HIGH도 재검토 대상이 된다. **다만 그 경우 `review.md:83-90` 기준표 문언을 함께 고쳐야 한다.
현재 상태는 라벨이 문서화된 기준과 모순되며, 둘 중 하나는 바뀌어야 한다.**

**HIGH는 부적절**하다. HIGH 정의는 "틀린 결과를 내지만 프로세스는 계속됨"인데 F19는 결과를
내지 않고 프로세스도 진행하지 않는다. 절충용 중간값으로 HIGH를 쓰면 기준표가 더 훼손된다.

### 가드 처방 판정: **채택 — 단, 세 키 묶음 + 두 지점 배치로 확장**

| 항목 | 판정 |
|---|---|
| `if batch <= 0: raise` 한 줄로 hang을 막을 수 있는가 | **예** (hang 유발 값이 정수 0뿐이므로 완전히 막힌다) |
| 그 한 줄로 충분한가 | **아니오**. `max_frames`/`max_frame_errors`(M-6)를 같이 막아야 하고, 타입 검사를 넣어야 None/str/실수까지 메시지가 개선된다 |
| 배치 위치 | **`sim.py:run_fer_point` 진입부 필수** (직접 호출 4곳이 `load_config`를 우회) + **`run.py:load_config` 권고** (F3 화이트리스트와 한 덩어리) |
| M-6과 묶을 것인가 | **묶어야 한다.** 계산으로 0이 되는 실 경로를 가진 쪽은 `batch`가 아니라 `max_frames`다 (`mpi_runner.py:55`) |
| 기존 설정 거부 위험 | **없음**. 저장소 전 설정의 세 값이 모두 1 이상의 정수 (§5-㉱ 표) |
| 추가 필요 조치 | `mpi_runner.py`는 가드만으로는 랭크 일부가 ValueError로 죽어 잡 전체가 실패한다. F6 수정 시 `my_frames == 0` 랭크 스킵 처리를 함께 넣을 것 |

---

## 7. 검증 방법 기록

스크래치패드 스크립트 4개 (프로젝트 파일 무수정, 모든 무한 루프에 타임아웃 또는 반복 상한 부과):

- `probe_prims.py` — `min()`, `rng.integers`, `np.zeros`, `np.argpartition`, `rng.normal`의 B ∈ {0, -1, 0.5} 동작,
  가드 표현식 반응
- `probe_real.py` — 실제 `LDPC_base` 패키지 로드 후 케이스별 1프로세스 실행
  (`normal` / `b0decode` / `loopprobe`(반복 상한 2000) / `hang0`(외부 45 s timeout) / `neg` / `half` / `none` /
  `mf0` / `mfe0` / `mfneg`)
- `probe_hang_props.py` — 자식 프로세스 30 s CPU와 RSS 샘플링(psutil 6.0.0) + CTRL_BREAK 전달
- `probe_ctrlc.py` — `_thread.interrupt_main()`으로 Ctrl+C 시뮬레이션, KeyboardInterrupt latency 측정

환경: Python 3.11.7, numpy 1.26.4, Windows 10, 논리 코어 24.
C++ 빌드와 실행 없음. 프로젝트 파일 수정 없음 (이 문서 작성만).
