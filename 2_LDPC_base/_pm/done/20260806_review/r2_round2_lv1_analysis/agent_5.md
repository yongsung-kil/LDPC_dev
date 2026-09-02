# Round 2 / agent_5 — V5. 실행 흐름·설정·인터페이스 계약

> 작성: 2026-08-06 23:04:03
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/` — `LDPC_base/run.py`, `sim.py`, `channel.py`,
> `decoder.py`(생성자/decode_batch/_decode_matrix 진입부), `llr_matrix.py`, `config.json`, 실험 `README.md`
> 관점 근거: Round 1 agent_1 P4·P12, agent_2 P4·P8·P14
> 검증 방식: 코드 정독 + 실제 실행(설정 변형 13종 load_config/setup 통과 여부, run_experiment 4종 실행)

---

## 요약

발견 20건 (HIGH 1, MEDIUM 11, LOW 8). 계약 자체의 산술 오류는 없으나,
**개명된 설정 키의 오타·구 이름이 조용히 무시되고 기본값으로 다른 실험이 돌아가는 구멍**이
가장 큰 위험이다. 그 외 `strong_error` 채널이 어떤 설정으로도 실행 불가인 채 `config.json`에
기본 포함된 점, 채널 dict의 `sd`/`cc`가 소비처 없는 죽은 출력인 점, `batch <= 0`에서 무한 루프,
CSV 무경고 덮어쓰기 + 재현성 메타 부재를 확인했다.

실제로 실행해 확인한 사실은 각 항목에 "실측"으로 표기했다.

---

## HIGH

### H-1. `run` 하위 키 오타와 구 이름이 조용히 무시되고 기본값으로 실행됨

- 위치: `run.py:109-114`
- 내용: `run_cfg.get(...)`만 쓰므로 `run` 아래 미지의 키는 검증 없이 통과한다.
  이번 변경의 핵심이 `target_errors` → `max_frame_errors`, `stop_below` → `stop_below_fer`
  개명인데, 구 이름을 그대로 둔 설정이 **에러 없이 통과해 기본값으로 실행**된다.
- 실측 (load_config 통과 확인):

  | 설정 변형 | 결과 |
  |---|---|
  | `run.target_errors: 5` 추가 | PASS — 무시되고 `max_frame_errors` 기본값 사용 |
  | `run.stop_below: 1e-3` 추가 | PASS — 무시되고 조기 중단 없음 |
  | `run` 블록 통째 삭제 | PASS — `max_frame_errors=50`, `max_frames=20000`, `batch=128` |

- 파급: `max_frames`를 256으로 지정하려던 설정이 20000으로 돌면 실행 시간이 78배가 되고,
  반대로 `max_frame_errors=1000`을 오타로 지정하면 50에서 조기 종료된 FER이 나온다.
  CSV에 어떤 `run` 설정으로 돌았는지 남지 않아(L-6) 사후 판별도 불가능하다.
- 참고: `code_file` → `H_matrix` 개명은 `run.py:46`이 직접 인덱싱하므로 KeyError로 걸린다.
  즉 **최상위 키만 걸리고 `run` 하위 키는 전부 새는** 비대칭 구조다.

---

## MEDIUM

### M-1. `max_iter` 금지 검사가 llr_matrix 없는 설정에도 걸려 max_iter 지정 수단이 사라짐

- 위치: `run.py:48-50` (무조건 검사) vs `decoder.py:23` (생성자 기본 `max_iter=20`),
  `decoder.py:70` (matrix 모드에서만 `self.max_iter = llr_matrix.max_iter`로 덮어씀)
- 내용: 금지의 근거는 "LLR matrix 파일의 마지막 iter_end가 max_iter를 결정"인데,
  검사는 `llr_matrix` 유무와 무관하게 `dec_cfg`에 `max_iter`가 있기만 하면 발동한다.
- 실측: `decoder`에서 `llr_matrix`를 빼고 `max_iter: 30`을 준 설정 →
  `ValueError: decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일의 마지막 iter_end가 결정`
  (llr_matrix가 없는데 llr_matrix를 근거로 거부하는 모순된 메시지)
- 결과: llr_matrix를 쓰지 않는 실험은 **max_iter가 20에 고정되고 설정으로 바꿀 방법이 없다**.
- 수정 방향: `if "max_iter" in dec_cfg and "llr_matrix" in dec_cfg:` 로 조건부화.

### M-2. `schedule` 기본값이 llr_matrix 있을 때만 적용되어, 없는 설정은 전혀 다른 디코더로 조용히 실행

- 위치: `run.py:76-82` (`setdefault("schedule","column_wise")`가 `if mx_path is not None:` 블록 안)
  / `decoder.py:24` (생성자 기본 `schedule="two_set"`) / `decoder.py:120-124` (±8 어댑터)
- 실측:

  | 설정 | setup 결과 |
  |---|---|
  | 기본 config (llr_matrix 있음) | `max_iter=20`(파일값) `schedule=column_wise` `matrix=True` |
  | `decoder.llr_matrix` 제거 | `max_iter=20`(생성자 기본) `schedule=two_set` `matrix=False` |

- 파급: llr_matrix 한 줄을 지우면 ㉮ 스케줄이 column_wise(원본 대응) → two_set(flooding 등가),
  ㉯ 채널 LLR이 테이블 ch 값 → 하드코딩 ±8(`decoder.py:124`), ㉰ max_iter가 파일값 → 20으로
  **동시에 세 가지가 바뀌는데 경고가 하나도 없다**. 같은 H-matrix·같은 채널의 FER을 비교하다
  전혀 다른 디코더 결과를 비교하게 된다.
- 문서: 실험 README "JSON 설정 스키마"에 `schedule` 키 자체가 없어 이 분기가 문서화되어 있지 않다.

### M-3. `strong_error` 채널은 어떤 설정으로도 실행 불가인데 `config.json`에 기본 포함

- 위치: `config.json:22-27` / `run.py:89-93` / `decoder.py:62-64` / `channel.py:124-128`
- 경로 분석 (모두 막힘):
  - ㉮ llr_matrix 없음 → `run.py:89`가 `mode="HD"` 고정 → `run.py:91` ValueError
  - ㉯ HD matrix 사용 → `mode="HD"` → 동일 ValueError
  - ㉰ 2SD matrix 파일 지정 → `decoder.py:62-64` `NotImplementedError: llr_matrix 2SD/3SD는
    채널 region 매핑 미구현 — 현재 HD만 지원` (생성자에서 즉사)
- 실측: `channel.use = "strong_error"` →
  `ValueError: channel strong_error은 ('2SD',) 전용 — 현재 디코딩 모드 HD (LLR matrix 파일명 확인)`
- 문제는 **에러 메시지가 막다른 길로 안내한다**는 점이다. "LLR matrix 파일명 확인"을 따라
  2SD 파일을 넣으면 다른 예외로 죽는다. 설정 파일에 실행 불가 조합이 기본으로 들어 있고,
  스키마 문서(실험 README:80)는 strong_error를 정상 선택지로 표기한다.
- 수정 방향: 메시지에 "2SD 디코딩 미구현"을 명시하거나, config.json의 strong_error 블록에
  주석 상당의 표시(README에 "현재 실행 불가" 명기)를 넣는다.

### M-4. 채널 dict의 `sd`/`cc`는 소비처가 전혀 없는 죽은 출력

- 위치: `channel.py:53,59,67,86,114` (생산) / 소비처 없음
- 실측: `LDPC_base/` 전체에서 `["sd"]` / `["cc"]` 읽기 grep 결과 **0건**.
  `_decode_matrix`는 `ch_llr["hd"]`(`decoder.py:345`)와 `ch_llr["mode"]`(`:342`)만 읽고,
  legacy 어댑터(`decoder.py:120-124`)도 `hd`만 쓴다.
- 파급: `rber_channel`의 2SD/3SD region 계산(`channel.py:56-67`)과 `strong_error_channel`의
  sd 배정(`channel.py:108-112`)은 계산 비용만 쓰고 버려진다. M-3과 합치면
  `strong_error_channel` 함수 전체가 `run.py` 경유로는 **도달 불가**하다.
- 실험 README "검증 기록"의 strong 정정 22399 검증도 디코더를 거치지 않은 채널 단독 검증이다.

### M-5. `batch <= 0` 설정에서 무한 루프 (hang)

- 위치: `sim.py:17-22` — `b = min(batch, max_frames - frames)`, `frames += b`
- `batch=0`이면 `b=0`이므로 `frames`가 영원히 증가하지 않고 `errors`도 0이라 두 종료 조건
  모두 만족되지 않는다. `decode_batch(B=0)`은 예외 없이 빈 결과를 반환하므로 조용히 돈다.
- 실측: `run.batch=0`으로 `run_experiment` 호출 → 25초 timeout까지 반환 없음 (hang 확인)
- 심각도 판단: 결과는 **무한 hang**이지만 트리거가 비정상 설정값이라 MEDIUM으로 둔다.
  가드 한 줄(`if batch <= 0: raise`)로 막을 수 있다.

### M-6. `max_frames <= 0` 또는 `max_frame_errors <= 0`에서 ZeroDivisionError

- 위치: `sim.py:24` `fer = errors / frames` (루프가 한 번도 안 돌면 `frames == 0`)
- 실측: `run.max_frames=0` → `ZeroDivisionError: division by zero` (설정 어느 키가 문제인지
  전혀 알 수 없는 메시지)

### M-7. `stop_below_fer`가 "FER 내림차순 포인트"를 전제하는데 config.json은 오름차순

- 위치: `run.py:129-130` / `config.json:20,26` / 실험 README:68-69
- `stop_below_fer`는 "측정 FER가 임계 미만이면 남은 포인트 중단"이므로 **points가 FER 내림차순**일 때만
  의미가 있다.
  - `rber` points `[0.008, 0.007, 0.006]` — RBER 내림차순 = FER 내림차순, **정상**
  - `fixed_error` points `[200, 300]`, `strong_error` points `[200, 300]` — 에러 비트 수
    오름차순 = FER **오름차순**. `stop_below_fer`를 켜면 가장 FER이 낮은 첫 포인트에서 즉시
    중단되어 정작 필요한 300 포인트가 측정되지 않는다.
- 현재 `stop_below_fer: null`이라 발현하지 않지만, 설정 파일이 그대로 복사되어 쓰이는 구조
  (실험 README:43 "config.json을 복사해서 만든다")라 잠재 함정이다.
- 문서에 순서 요건이 서술되어 있지 않다.

### M-8. `errors == 0` → `fer = 0` → 즉시 중단, CSV에는 측정치 0으로 기록

- 위치: `run.py:129` / `sim.py:24,42`
- `max_frames`를 다 쓰고도 에러가 0이면 `fer = 0/frames = 0.0`이 되어 `0 < stop_below_fer`가
  항상 참 → 남은 포인트 전부 중단된다. 의도(측정 하한 도달)에는 부합하지만,
  CSV에는 `0.000000e+00`으로 기록되어 **"측정 결과 FER=0"과 "측정 하한 미달(<1/frames)"이
  구분되지 않는다**. 중단으로 건너뛴 포인트는 CSV에 아예 행이 없어 "미측정"과 "실패"도
  구분 불가하다.
- 수정 방향: `errors == 0`이면 상한 `1/frames`를 별도 컬럼으로 남기거나 `censored` 플래그 추가.

### M-9. 필수 키 부재 시 bare KeyError — 어느 파일 어느 키인지 알 수 없음

- 실측 (load_config 호출 결과):

  | 제거한 키 | 예외 |
  |---|---|
  | `H_matrix` (`run.py:46`) | `KeyError: 'H_matrix'` |
  | `channel` (`run.py:57`) | `KeyError: 'channel'` |
  | `channel.use` (`run.py:58`) | `KeyError: 'use'` |
  | `channel.<use>.points` (`run.py:63`) | `KeyError: 'points'` |
  | `channel.strong_error.SCR` (`run.py:96`) | `KeyError: 'SCR'` (run_experiment 시점) |

- `channel.use`가 잘못된 값일 때만 친절하다
  (`ValueError: channel.use='fixed' — ['fixed_error', 'rber', 'strong_error'] 중 하나여야 함`).
  같은 함수 안에서 예외 품질이 크게 갈린다.
- `SCR`/`SER`은 `load_config`가 아니라 `_make_channel_fn`(`run.py:96`)에서 처음 접근하므로
  검증 단계가 아니다. 다만 첫 포인트의 첫 배치 **전에** 호출되므로 긴 실험이 낭비되지는 않는다.

### M-10. `points`가 빈 리스트면 조용히 통과하고, 헤더만 있는 CSV가 기존 결과를 덮어씀

- 위치: `run.py:63-64` (리스트 정규화만 하고 비었는지 검사 없음) / `run.py:121-131` / `sim.py:36-43`
- 실측: `fixed_error.points = []` → 예외 없이 `{'fixed_error': []}` 반환 →
  `saved: .../fer_fixed_error.csv` 출력 후 헤더 1줄만 있는 CSV 생성.

### M-11. CSV 무경고 덮어쓰기 + 재현성 메타 전무

- 위치: `sim.py:38` `open(path, "w", ...)` / `run.py:139-142`
- 파일명이 `{csv_prefix}_{ch_type}.csv`뿐이라 **H_matrix, llr_matrix, seed, decoder 설정,
  run 설정이 파일명에도 내용에도 남지 않는다**. CSV 컬럼은
  `param, fer, frames, errors, avg_iter_ok, sec`가 전부다.
- 같은 채널로 조건만 바꿔 재실행하면 이전 결과가 무경고로 소실된다. 실측에서
  빈 points 실행이 기존 `fer_fixed_error.csv`를 헤더만 남기고 덮어쓰는 것을 확인했다.
- 현 `Sim_Output/`에 구 이름 산출물(`fer_bsc.csv`, `fer_llr_bsc.csv`, `_tmp_rber.json`,
  `_tmp_strong.json`)과 새 산출물이 섞여 있어 이미 어느 설정의 결과인지 판별 불가한 상태다.

### M-12. `config.json` 기본값이 통계적으로 무의미한 실험 (FER=1.0만 나옴)

- 위치: `config.json:6-11,18-21`
- 실측 (기본 config 그대로 실행):

  ```
  param,fer,frames,errors,avg_iter_ok,sec
  200,1.000000e+00,64,64,0.000,3.7
  300,1.000000e+00,64,64,0.000,3.7
  ```

- 분석:
  - `max_frame_errors=10`, `batch=64`이므로 첫 배치(64프레임)에서 에러 64개 → 즉시 종료.
    `max_frames=256`은 도달조차 하지 않는다.
  - N = 147×256 = 37632 비트에 200/300 비트 에러를 넣으면 두 포인트 모두 정정 불가 →
    **FER=1.0으로 포화**되어 두 포인트가 구분되지 않는다 (곡선이 그려지지 않음).
  - `max_frames=256`은 0 에러여도 FER 하한이 1/256 ≈ 3.9e-3이라 실측 가능 구간이 극히 좁다.
  - `max_frame_errors=10`의 상대 표준오차는 약 1/√10 ≈ 32%로, 정량 비교용이 아니다.
- 즉 현재 `config.json`은 **동작 확인(smoke) 설정**인데 스키마 예시로도 그대로 쓰이고 있어
  (실험 README:51) 그 성격이 문서에 표기되어 있지 않다.

### M-13. 시드 파생 `int(1e6 * p)`의 포인트 접힘과 음수 포인트

- 위치: `run.py:123` `np.random.default_rng([seed, int(1e6 * p)])`
- 실측:

  | p | `1e6*p` | `int(...)` |
  |---|---|---|
  | 0.008 | 8000.0 | 8000 |
  | 0.0080001 | 8000.099999999999 | 8000 |
  | 0.0080002 | 8000.200000000001 | 8000 |

  → **1e-6보다 조밀한 포인트는 같은 시드로 접힌다.** 에러 플로어 탐색처럼 RBER를 1e-7 단위로
  훑으면 모든 포인트가 `[seed, 0]`을 공유해 잡음 실현이 완전히 동일해지고, 포인트 간 결과가
  인위적으로 상관되어 곡선이 매끄러워 보인다.
- 음수 포인트: `np.random.default_rng([12345, -1000])` → `ValueError: expected non-negative integer`
  (설정과 무관한 numpy 메시지).
- 현재 config.json 값(0.008/0.007/0.006, 200/300)에서는 충돌 없음을 확인했다.
- 참고: 포인트마다 `default_rng`를 새로 만들므로 **포인트 결과가 실행 순서에 의존하지 않는다**.
  이 부분은 올바르게 설계되어 있다 (`stop_below_fer`로 중단해도 앞 포인트 결과는 동일).

---

## LOW

### L-1. `_decode_matrix`의 legacy 배열 경로는 `run.py` 경유로 도달 불가

- 위치: `decoder.py:346-347` `else: r_bit = (ch_llr < 0).astype(np.uint8)`
- `self.matrix is not None`일 때만 진입하는데, 그 설정에서 `run.py`는 항상 `channel.py`의
  dict를 넘긴다(`run.py:101`). 직접 API 호출 시에만 살아 있는 경로다.

### L-2. legacy 어댑터의 non-HD 예외도 도달 불가

- 위치: `decoder.py:122-123` `raise NotImplementedError("legacy 경로는 HD 채널 출력만 지원")`
- 이 분기는 `matrix is None`일 때만 도달하는데, 그 경우 `run.py:89`가 `mode="HD"`로 고정하므로
  `ch_llr["mode"]`는 항상 "HD"다. 어댑터 자체(`decoder.py:124`, ±8 변환)는 llr_matrix 없는
  설정의 정상 경로로 살아 있다.

### L-3. 모드 검증이 3중으로 흩어져 있음

- `run.py:90` (채널이 모드를 지원하는가) / `decoder.py:62-64` (matrix가 HD인가) /
  `decoder.py:342-344` (채널 출력 모드 == matrix 모드). 세 검사는 서로 모순되지 않으나
  실패 시 서로 다른 예외 타입(ValueError / NotImplementedError / ValueError)이 나온다.

### L-4. `run_experiment` 반환은 단일 채널인데 `report`는 다중 채널 루프

- 위치: `run.py:131` `return {ch_type: points}` / `run.py:139` `for ch_type, points in results.items()`
- 루프는 항상 1회만 돈다. 동작 문제는 없으나 다중 채널 지원의 잔재다.
- 본체 `2_LDPC_light/README.md:16`은 아직 "채널 1개/여러 개 ... 모두 설정만으로 처리"라고
  서술하고, `README.md:15`는 아직 `target_errors`를 쓴다. 본체 반영 시 갱신 대상.

### L-5. `setup()` 안의 `print(mx.summary())`

- 위치: `run.py:79` (`main`의 `print(code.summary())`는 `run.py:153`으로 분리되어 있음)
- 라이브러리로 임포트해 `setup()`만 호출해도 표준출력이 오염된다. 출력 책임이 `setup`과 `main`에
  나뉘어 있어 일관성도 없다.

### L-6. 파일 부재 에러 처리의 비대칭

- `H_matrix`: `run.py:72-73`에서 존재 확인 후
  `FileNotFoundError: ... 없음 — H-matrix를 먼저 준비할 것` (친절)
- `decoder.llr_matrix`: 사전 확인 없이 `llr_matrix.py:104`의 `open()`이 그대로 던짐 →
  `FileNotFoundError: [Errno 2] No such file or directory: '...'` (실측)

### L-7. `_make_channel_fn`이 포인트마다 재생성·재검증

- 위치: `run.py:124` (루프 안에서 호출)
- 모드 검증(`run.py:90`)이 포인트 수만큼 반복된다. 첫 포인트에서 걸리므로 fail-fast는
  성립하지만, 검증은 루프 밖으로 뺄 수 있다.

### L-8. CSV `param` 컬럼의 의미가 채널마다 다름

- 위치: `run.py:127,141` / `sim.py:40`
- `rber`는 RBER 값, `fixed_error`/`strong_error`는 에러 비트 수인데 컬럼명은 고정 `param`이다.
  파일명(`fer_{ch_type}.csv`)으로만 구분된다. M-11(메타 부재)과 함께 보면 CSV 단독으로는
  해석 불가하다.

### L-9. `avg_iter_ok`가 성공 프레임 0일 때 0.000으로 기록

- 위치: `sim.py:27` `iter_sum / max(1, frames - errors)`
- 실측 CSV에서 성공 프레임이 하나도 없을 때 `avg_iter_ok=0.000`이 찍힌다. "데이터 없음"이
  "평균 0 iteration"으로 보여 오독 여지가 있다.

---

## 문제 없음을 확인한 항목

- ㉮ `output.dir`의 `setdefault` 후 `resolve` 이중 처리(`run.py:53-55`) — 기본값은 이미 절대경로라
  `resolve`가 항등, 사용자 상대경로는 base_dir 기준으로 정상 해석. 실질 문제 없음
- ㉯ 시드 우선순위 `channel.<use>.seed` → `run.seed` → 12345 (`run.py:118`) — 실험 README 스키마와
  일치하고, 포인트마다 `default_rng`를 새로 만들어 실행 순서 독립성이 보장됨
- ㉰ `points` 스칼라 → 리스트 정규화(`run.py:63-64`) 정상 동작
- ㉱ `decoder` 오타 키는 `MinSumDecoder(**dec_cfg)`에서 setup 단계에 TypeError로 즉시 노출
  (실측: `MinSumDecoder.__init__() got an unexpected keyword argument 'msg_clipp'`) — fail-fast 성립
- ㉲ `schedule: "two_set"` + `llr_matrix` 조합은 setup 단계에서
  `NotImplementedError: llr_matrix 모드는 column_wise 스케줄만 지원`으로 차단됨 (실측)
- ㉳ dv 미매칭(`llr_matrix.col_dv_idx`)은 디코더 생성자에서 호출되므로 setup 단계에 걸림 — fail-fast 성립
- ㉴ `stop_below_fer: null`이 `is not None` 검사로 안전하게 처리됨(`run.py:129`)
- ㉵ 파일 입출력의 `encoding="utf-8"` 명시는 `run.py:38`, `pcm.py:49,57`, `llr_matrix.py:104`,
  `sim.py:38` 전부 일관됨

---

## 수정 우선순위 제안

| 순위 | 항목 | 근거 |
|------|------|------|
| 1 | H-1 (`run` 하위 키 화이트리스트 검증) | 개명이 이번 변경의 핵심인데 구 이름이 조용히 무시됨 |
| 2 | M-1, M-2 (max_iter 조건부화, schedule 기본값 통일) | 설정 한 줄 차이로 디코더가 통째로 바뀌는데 무경고 |
| 3 | M-5, M-6 (`batch <= 0`, `max_frames <= 0` 가드) | hang과 무의미한 예외를 한 줄로 차단 |
| 4 | M-11, M-3 (CSV 메타/덮어쓰기, strong_error 표기) | 결과 추적성과 실행 불가 조합의 명시 |
| 5 | M-9, M-10 (필수 키 명시 검증, 빈 points) | 에러 메시지 품질 |
| 6 | M-12, M-7 (config.json 성격 표기, points 순서 요건 문서화) | 문서·설정 정합 |
