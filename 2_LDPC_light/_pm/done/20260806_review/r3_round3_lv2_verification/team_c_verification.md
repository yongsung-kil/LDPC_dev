# team_c — 본체 반영 검증 (Round 3, lv2)

> 작성: 2026-08-06 23:38:23
> 담당 발견: F4, F5, F6, F7 (HIGH, 본체 반영 시점 파손 — 전수성), F23 (MEDIUM, llr_tables 의존 목록), F7 처방(반영 순서 7단계)
> 워커: `worker_c_1.md`(독립 전수 수색), `worker_c_2.md`(자산 소실·반영 순서), `worker_c_3.md`(F23)
> 팀 리더 직접 재확인: `pcm.py` 양쪽 전문, `.gitignore` + `git ls-files` + `git check-ignore`, `.qc` 헤더 실측,
> 개정본 `decoder.py` 의존 라인 6곳, `Input/LLR/*.txt` dv 구간

---

## 0. 판정 요약

| 발견 | 판정 | 요지 |
|---|---|---|
| F4 fer_curve.json+py 파손 | **확인됨** | 5개 키 전부 재현. `target_errors`/`stop_below`의 조용한 무시가 실제로 결과를 바꾸는 것까지 실증 |
| F5 채널 함수 3종 삭제 | **확인됨 (파손 순서 1건 부정확)** | 의존처 목록은 정확. 단 `select_irregular.py`·`mpi_runner.py`는 `bsc_llr` AttributeError에 **도달하지 못한다** (TypeError가 먼저) |
| F6 run_fer_point 인자명 | **확인됨** | 호출부 4곳 전부 재현. 반환 dict 키와 `save_csv`가 무사한 것도 확인 |
| F7 `.qc` 2개 로드 불가 | **부분 확인** | 포맷 불일치·`ValueError`는 확인됨 |
| F7 「자산 소실」 | **반박됨** | 세 갈래 독립 복구 경로가 살아 있다 (아래 §3) |
| F7 처방(반영 순서 7단계) | **수정 필요** | 전제(역방향 위험)가 틀렸고, 최우선 항목이 잘못 지목됐다 |
| F23 llr_tables 의존 6곳 | **부분 확인 (과소 집계)** | 허위 0건이나 2곳 라인 부정확, 3곳 누락 — 실제 9곳 |
| F23 「제거 불가」 결론 | **반박됨** | 모듈 import는 **단 1곳**, 사용 심볼은 `dv_group` 하나뿐 |

**누락 파손 6건** 발견 (§5). 그중 `.gitignore` 건은 F7이 걱정한 자산 소실보다 실제 위험이 크다.

---

## 1. 가설 목록

| # | 가설 | 검증 방법 | 담당 |
|---|---|---|---|
| H-A | V6이 잡은 파손 목록이 전부다 (전수성) | V6 결론을 주지 않고 "바뀐 인터페이스 목록"만으로 독립 grep + 합성 트리 실행 | 워커1 |
| H-B | `irregular_17x144_z256.qc`는 재생성 불가 = 자산 소실 | 생성 경로 전수 수색 + git 추적 확인 + 시드 결정성 확인 | 워커2 |
| H-C | `tools/` 3파일은 무사하다 (본체 `pcm.save`가 Ref-C 출력) | 양쪽 save/load 코드 대조 + 왕복 실행 | 워커2 |
| H-D | 처방의 순서 의존성이 실재한다 (.qc 변환이 최우선) | 변환 도구 생존 여부 + 역방향 파손 여부 실증 | 워커2 |
| H-E | F23의 의존 6곳이 정확하고 전수다 | 라인 직접 대조 + 심볼 전수 grep (본체·개정본 양쪽) | 워커3 |

**독립성 고지**: 워커1의 첫 grep 결과에 `agent_6.md`의 몇 줄이 섞여 출력되었다(이후 전 grep에서 해당 폴더 제외).
다만 워커1이 V6에 없는 항목 3건을 새로 찾아냈고 V6의 판정 하나(자산 소실)를 반대로 결론지었으므로,
독립 수색은 실질적으로 성립했다고 본다.

---

## 2. F4 / F5 / F6 — 전수성 검증 결과

### 2-1. V6 목록은 **전부 실재한다** (허위 0건)

워커1이 독립 수색으로 재현한 결과, V6이 지목한 의존처는 하나도 빠짐없이 실재했다.
`fer_curve.json` 5개 키, `fer_curve.py` 3지점, `fixed_error_sweep.py:15`, `llr_tune.py:18`,
`select_irregular.py`, `mpi_runner.py`, `llr/README.md:27`, `.qc` 2개 — 전부 확인.

특히 **조용한 파손** 판정(`fer_curve.json:7` `target_errors`, `:10` `stop_below`)은 실행으로 확증됐다.
첫 포인트가 `FER=0.0`으로 `stop_below=0.5` 조건을 만족했는데도 스윕이 멈추지 않았다
(`worker_c_1.md` §2-2 실증 로그). 즉 "조용히 무시"가 관측 결과를 실제로 바꾼다.

### 2-2. 부정확 1건 — 파손 **순서**

V6은 `select_irregular.py:38` `chan.bsc_llr(...)` → AttributeError, `mpi_runner.py:51,53` → AttributeError로 적었다.
실제로는 같은 함수 호출의 **다음 줄** TypeError가 먼저 터져 AttributeError 지점에 도달하지 못한다.

- `select_irregular.py:39-40` `run_fer_point(..., target_errors=...)` → `TypeError` (`fer_at()` 첫 호출 60행에서)
- `mpi_runner.py:56` 동일 `TypeError`

실증(`worker_c_1.md` §2-5):
```
--- (A) run_fer_point(target_errors=...) ---
  TypeError: run_fer_point() got an unexpected keyword argument 'target_errors'
--- (B) chan.bsc_llr 자체 ---
  AttributeError: module 'ldpclight.channel' has no attribute 'bsc_llr'
```

수리 관점에서 함의가 있다. 두 파일은 **임포트가 통과**하므로 정적 임포트 검사로는 잡히지 않고,
`bsc_llr`만 고치면 다음 실행에서 TypeError가 새로 나온다. **두 결함을 한 번에 고쳐야 한다**.

### 2-3. 판정

- F4 — **확인됨**. 처방("반영 전 재작성") 유효. 단 `fer_curve.py`는 키 이름 교체로 살릴 수 없다.
  개정본 `run_experiment`가 채널 1개만 반환하므로 2패널(BSC+AWGN 동시) 설계 자체가 무효다
- F5 — **확인됨**(순서 1건 정정). 처방("갱신 또는 폐기") 유효
- F6 — **확인됨**. 호출부 4곳 전부 정확. 반환 dict 키 6종과 `save_csv` 시그니처가 동일해
  결과 소비 측이 무사하다는 V6의 음성 판정도 재확인됨

---

## 3. F7 — 자산 소실 판정 (반박됨)

V6-4의 결론은 "`irregular_17x144_z256.qc`는 로드도 재생성도 불가한 유일한 자산 소실 지점"이었다.
**세 갈래 독립 복구 경로**가 확인되어 이 결론은 성립하지 않는다.

### 3-1. 두 `.qc` 모두 git 추적 중 (리더 직접 확인)

```
$ git ls-files "*.qc"
1_LDPC_revised/_pm/tasks/260803_iteration당속도측정/irregular_15x145_z256.qc
2_LDPC_light/examples/example_18x147_z256.qc
2_LDPC_light/examples/irregular_17x144_z256.qc
```

워킹 트리도 깨끗하다. 어느 시점에 무엇을 덮어써도 `git show HEAD:...`로 원본 복원이 가능하다.
**"소실"이라는 표현 자체가 성립하지 않는다.**

### 3-2. 변환은 재생성이 아니라 헤더 3줄 재작성 (워커1·2 독립 확인)

본체 `pcm.py:45-52` `save()`와 개정본 `pcm.py:46-52` `save()`는 **바이트 단위로 동일**하며 둘 다 Ref-C를 출력한다.
따라서 본체 `pcm.load` → 개정본 `pcm.save` 왕복이면 끝이고, 워커2가 두 파일 모두 왕복 성공(base 동일=True)을 실증했다.
`irregular_17x144`의 실측 J/K는 `10, 40`이다.

### 3-3. 결정론적 재생성도 가능 (워커2)

`select_irregular.py:51` `build_code(Z, M, N, INFO_DEGREES, seed=sd)`는 시드 고정이다.
워커2가 후보 6개를 전수 대조해 **`build_code(256, 17, 144, [3]*65+[4]*31+[10]*31, seed=103)`으로
바이트 수준 완전 재현**에 성공했다(0.6초). 승자 시드 103은 `examples/out/select_irregular.csv`의 deep 단계 기록과 일치한다.

재생성 경로(`build_code` → `peg.py`/`lifting.py` → `pcm`)는 `channel`/`sim`/`decoder`를 전혀 참조하지 않으므로
**반영 후에도 죽지 않는다**. `select_irregular.py`에서 죽는 것은 FER 선별 루프뿐이다.

> 단, 시드를 기록한 `examples/out/select_irregular.csv`는 `.gitignore:11` `out/`으로 **미추적**이다(리더 확인).
> 이 재현 레시피는 로컬 파일에만 있다. `.qc` 본체가 추적 중이라 실무 위험은 없으나, 시드는 문서로 옮겨 둘 값이다.

### 3-4. `tools/` 3파일 무사 — 확인됨 (V6보다 강함)

`peg.py`, `lifting.py`, `gen_example_code.py`는 `..pcm`만 의존하고, 워커2가 개정본 pcm으로 갈아끼운 상태에서
실제로 돌려 **무수정 동작**을 확인했다. 워커1도 `build_code() → save() → 개정본 load()` 왕복 성공을 별도 확인했다.

### 3-5. F7 판정

- 포맷 불일치와 `ValueError` — **확인됨**
- 「재생성 경로도 죽어 자산 소실」 — **반박됨** (git 추적 + 헤더 재작성 + 시드 재현, 3중 복구 가능)
- **심각도 조정 권고: HIGH → MEDIUM.** 즉시 예외로 터지고, 원본이 버전 관리에 있으며, 복구가 2분 작업이다

---

## 4. F7 처방(반영 순서 7단계) 판정 — 수정 필요

처방 원문: "반영 전 .qc 2개를 Ref-C로 변환 (최우선), 이후: llr_profile 결정 → plan.md 기록 → max_iter 확정 → 코드 이동 → examples 갱신 → 문서 → Sim_Output 정리"

### 4-1. 역방향 위험 — **반박됨. 덮어쓰기가 정답이다** (리더 직접 확인)

본체 `pcm.py:53-79` `load()`는 **구 포맷과 Ref-C를 모두 수용**한다.

- `pcm.py:57` — `ln.split("#", 1)[0].strip()`으로 `#` 주석을 제거한다
- `pcm.py:60-64` — 첫 줄 정수 2개면 Ref-C 분기
- `pcm.py:65-68` — 정수 3개면 구 포맷 분기

개정본 `pcm.py:57-62`는 주석 제거가 없고 정수 2개만 받는다. 즉 **관대함이 한쪽 방향으로만 좁아졌다**.
따라서 지금 `.qc`를 Ref-C로 덮어써도 본체 `examples`/`tools`는 깨지지 않는다.
"사본 생성(`*_refc.qc`)" 방식은 소비처 4곳(`fixed_error_sweep.py:20`, `llr_tune.py:24`,
`select_irregular.py:26`, `measure_speed.py:42`)의 경로 수정을 불필요하게 유발하므로 **반대**한다.

### 4-2. 「최우선」 순위 — **근거 없음**

"이걸 먼저 하지 않으면 복구 불가"라는 전제가 §3에서 무너졌다. 변환은 언제 해도 되고,
반영 후에는 `git show HEAD:2_LDPC_light/examples/irregular_17x144_z256.qc`로 원본을 꺼내 변환하면 된다.

### 4-3. 7단계 중 실제 강제 의존은 1쌍뿐

- **실재하는 의존**: `코드 이동 → examples 갱신` (이동 전에는 신 인터페이스가 없어 갱신 대상이 확정되지 않음)
- **의존 아님**: `llr_profile 결정`, `plan.md 기록`, `문서 갱신`, `Sim_Output 정리`는 서로 독립이며 코드 이동과도 독립
- **단계 자체가 잘못됨**: `max_iter 확정`은 독립 결정 항목이 아니다. `llr_matrix.py:63`에서
  파일의 마지막 `iter_end`로 **파생**된다. 결정할 것은 max_iter 값이 아니라
  "`llr_matrix` 없는 설정에도 JSON `max_iter` 금지를 걸 것인가"(F 계열 별건)다

### 4-4. 처방에서 빠진 위험 — 이쪽이 더 중요하다

**㉮ `.gitignore`가 진짜 소실 경로다 (리더 직접 확인).** `core.ignorecase=true`이고 `.gitignore:40`에 `H_Matrix/`가 있다.

```
$ git check-ignore -v "2_LDPC_light/Input/H_matrix/example_18x147_z256.qc"
.gitignore:40:H_Matrix/	2_LDPC_light/Input/H_matrix/example_18x147_z256.qc
```

즉 개정본 `Input/H_matrix/`를 본체로 옮기는 순간, 지금까지 **추적되던** `.qc`가 조용히 미추적이 된다.
F7이 걱정한 "자산 소실"은 없지만, 처방을 그대로 따르면 **자산 소실이 새로 만들어진다**.
(`Input/LLR/`은 무영향 — `git check-ignore` exit=1 확인)

**㉯ irregular는 변환해도 개정본에서 못 쓴다 (워커2, 리더 재확인).**
`Input/LLR/LLR_MATRIX_HD_*.txt`의 dv 구간은 `dv_from=dv_to=[11,4,3,2]` 싱글턴인데,
`irregular_17x144`의 col_deg에는 dv=10이 있다. `llr_matrix.py:139-147` `col_dv_idx()`가 예외를 던진다.
변환해 둬도 주 경로에서 쓸 수 없으므로, "변환하면 살아난다"는 그림이 절반만 맞다. **Decision 등급**.

**㉰ 개정본 전체가 미추적이다.** `.gitignore:24` `_test/`. 본체의 새 원본이 될 코드가 버전 관리 밖에 있다.

**㉱ DV 내림차순 전제가 강제되지 않는다.** 개정본 `pcm.py:15`가 "column block은 DV 내림차순 배치를 전제"라고
선언했으나 검사 코드가 없다. `irregular_17x144`는 오름차순(3→4→10)이라 전제 위반이 **완전히 조용하다**.

### 4-5. 수정된 반영 순서 (권고)

- 1. **`.gitignore` 수정** — `H_Matrix/`를 경로 한정(예: `0_LDPC_original/H_Matrix/`)으로 좁힌다. 최우선
- 2. **개정본을 git에 올린다** (`_test/` 예외 등록 또는 별도 브랜치). 이동 전 되돌리기 지점 확보
- 3. `llr_profile` 존치 여부 결정 (Decision) / `channels`→`channel.use` 전환 기록 (Decision) / `max_iter` 금지 범위 확정 — **셋은 병렬 가능**
- 4. 코드 이동 (`LDPC_base/*.py` → 본체)
- 5. `.qc` 2개 Ref-C **덮어쓰기** 변환 (본체 `pcm.load`가 양쪽을 읽으므로 4번 전후 무관. 시드 103을 문서에 기록)
- 6. `examples/` 4개 + `mpi_runner.py` 갱신 또는 폐기 — 4번에 의존
- 7. 문서 갱신 / `Sim_Output` 정리 — 순서 무관

---

## 5. 누락 파손 목록 (V6이 놓친 것)

| # | 누락 항목 | 위치 | 성격 |
|---|---|---|---|
| N1 | **저장소 밖 의존처** — `importlib.import_module("2_LDPC_light.channel")` 동적 임포트 | `1_LDPC_revised/_pm/tasks/260803_iteration당속도측정/measure_speed.py:38,62,110,137` | 문자열 임포트라 정적 grep으로 안 잡힘. `.qc` 기본값(42행)도 구 포맷.<br>**단 `:62,137`은 개정 이전에 이미 파손**(현행 본체에서도 `AttributeError: 'float' object has no attribute 'shape'`) — 이번 변경 탓으로 오인 금지 |
| N2 | **`output.dir` 기본값 조용한 이동** — `base_dir` → `base_dir/Sim_Output` | 본체 `run.py:43` ↔ 개정본 `run.py:54` | 조용한 동작 변화. `output.dir` 미지정 설정의 결과 파일이 다른 폴더에 쌓인다. V6의 "조용한 것은 2건뿐" 판정을 수정해야 함 |
| N3 | **`.gitignore` `H_Matrix/`가 `Input/H_matrix/`를 삼킨다** | `.gitignore:40` + `core.ignorecase=true` | 반영 절차가 만들어내는 신규 자산 소실 경로 (§4-4 ㉮) |
| N4 | **irregular dv=10 vs LLR matrix dv 구간 `[11,4,3,2]`** | `llr_matrix.py:139-147`, `Input/LLR/LLR_MATRIX_HD_*.txt` | 변환해도 주 경로 사용 불가. Decision 등급 (§4-4 ㉯) |
| N5 | **DV 내림차순 전제 미강제** | 개정본 `pcm.py:15` (검사 코드 부재), `select_irregular.py:29`, `tools/gen_example_code.py:22` | 조용한 전제 위반. 새로 생성되는 부호도 오름차순 |
| N6 | **F23 의존 3곳 누락** | 개정본 `decoder.py:24`(생성자 인자), `:28-31`(docstring), `:58-59`(llr_matrix 상호배타) | §6 참조 |

---

## 6. F23 — llr_tables 의존 목록 판정

### 6-1. 지목된 6곳 (리더 직접 재확인, 개정본 `LDPC_base/decoder.py`)

| V6 지목 | 실제 | 판정 |
|---|---|---|
| 50 `from .llr_tables import dv_group` | `:50` 정확 일치 | 정확 |
| 48-55 `llr_profile` 분기 | `:48 self.profile = llr_profile`, `:49 if llr_profile is not None:`, `:51-55` 본문 | 정확 |
| 72-88 `_vnu_quantize()` 전체 | 함수 시작·끝 정확 일치 | 정확 |
| 233 `RESET = self._edge_mag[0] if ...` | 위치는 맞으나 실제는 `RESET = np.float32(self._edge_mag[0] if self.profile is not None else self.msg_clip)` — `np.float32(...)` 래핑 누락 | **인용 부정확** |
| 275-276 `_decode_column_wise` 분기 | `:275 if self.profile is not None:` / `:276 v2c = self._vnu_quantize(...)` | 정확 |
| 178 `decode_batch` two_set 분기 | 분기 **시작은 `:177`** (`if self.profile is not None:`), `:178`은 본문. `275-276`처럼 두 줄로 적어야 일관 | **범위 부정확** |

허위 위치 0건. 2곳 인용 부정확.

### 6-2. 전수성 — **과소 집계 (실제 9곳)**

워커3이 3곳을 추가 발견했다(리더 직접 확인).

- `decoder.py:24-25` — `MinSumDecoder.__init__` 시그니처의 `llr_profile=None` 인자
- `decoder.py:28-31` — docstring이 `llr_tables.LLRProfile`, `llr_tables.ch_mag_by_col`을 명시
- `decoder.py:58-59` — `llr_matrix`와의 상호배타 검사 (`raise ValueError("llr_profile과 llr_matrix는 동시 지정 불가")`)

### 6-3. **인과 구조 자체가 반박된다**

"6곳 의존이라 제거 불가"라는 논리가 성립하지 않는다.

- `llr_tables`를 **모듈로 import 하는 곳은 개정본 전체에서 `decoder.py:50` 단 1곳**이고, 심볼도 `dv_group` 하나뿐이다
- `load_profile` / `ch_mag_by_col` / `LLRProfile`은 개정본에서 **참조 0건**
- 나머지 8곳은 `llr_tables`가 아니라 `self.profile`(생성자로 주입된 객체)에 대한 의존이다

즉 걷어낼 대상은 "6곳의 llr_tables 의존"이 아니라 "`llr_profile` 모드 전체"이며, 그것은 하나의 결정이다.

### 6-4. 워커3의 실증 — 진입 경로가 이미 죽어 있다

- 개정본 `run.py`는 `llr_profile`을 **전혀 처리하지 않는다**. JSON에 넣으면 문자열이 그대로 넘어가
  `AttributeError: 'str' object has no attribute 'th'` → **JSON 진입점에서 도달 불가**
- 개정본 `channel.py` 3종 함수에 `mag` 인자가 없어 `ch_mag_by_col`(CH_HD)을 소비할 수 없다.
  디코더가 받는 채널 LLR은 `decoder.py:124`의 `±8.0` 고정 → **CH_HD는 영원히 무시된다**
- 반면 프로파일을 직접 주입하면 두 스케줄 모두 `_vnu_quantize`가 1659회 호출되며 정상 수렴한다

즉 코드는 살아 있고, 죽은 것은 **진입 경로·데이터·채널 통로 세 가지**다. 존치를 택하면
`run.py`에 `load_profile()` 호출 추가와 `channel.py`의 `mag` 인자 복원이 최소 보수다.

### 6-5. 부수 확인

- **H4 (파일 차이)** — 확인됨. `diff -u` 헝크 1개, docstring 4행 한 줄 치환뿐. 코드는 바이트 동일
- **H3 (본체 쪽)** — 확인됨. 본체 `decoder.py` 8곳. 실사용 소비처는 `examples/llr_tune.py` **한 파일뿐**이고
  `llr/` 7개 txt(`_hw_orig_ch.txt` 제외)가 이 스크립트 하나에만 소비된다. `run.py`/`mpi_runner.py`는 미사용
- **H5 (제거 범위)** — 확인됨. 제거 대상 파일 12개(코드 3 + llr txt 8 + `llr/README.md`).
  **남겨야 하는 것**: `self._edge_mag`(llr_matrix가 `:68`에서 독립 세팅, `:96`·`:353`에서 소비),
  `self.beta`/`cn_mag_fn`, `_mx_vnu_quantize`(이름만 비슷한 별개 함수), `msg_clip`/`quantize`.
  `llr_matrix.col_dv_idx()`는 `dv_group`과 무관한 독립 구현
- **제거 시 선행 조건**: `llr/_hw_orig_ch.txt`의 원본 C++ 실값(`CH_HD 21 14 12 10`, `EDGE_MAG 7 5 3 1`)은
  LLR_MATRIX 파일에 담기지 않는다. 삭제 전 문서로 이관하지 않으면 **유일한 보존처를 잃는다**

### 6-6. F23 판정

- 의존 목록 — **부분 확인**. 허위 0건, 인용 2곳 부정확, 3곳 누락(실제 9곳)
- 「제거 불가」 결론 — **반박됨**. 모듈 의존은 1곳뿐이며, 실제 안건은 "`llr_profile` 모드 존폐" 단일 Decision이다
- 처방("존치 여부 Decision") — **유효**. 다만 Decision 문서에 `_hw_orig_ch.txt` 값 이관을 선행 조건으로 명시할 것

---

## 7. 남는 Decision 안건 (사용자 확인 필요)

- ㉮ `llr_profile` 모드 존폐 (존치 시 `run.py`·`channel.py` 보수 필요, 폐기 시 `_hw_orig_ch.txt` 값 이관 선행)
- ㉯ `docs/plan.md:128` §7 #6 확정 사항(`channels` 리스트)과 개정본 `channel.use` 단수 선택의 **정면 충돌**
- ㉰ `irregular_17x144`(dv=10)를 개정본 주 경로에서 쓸 것인가 — 쓰려면 LLR_MATRIX dv 구간 확장이 필요
- ㉱ `.gitignore` `H_Matrix/` 규칙 범위 축소 (사실상 필수이나 다른 프로젝트 영향 확인 필요)
