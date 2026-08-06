# worker_c_3 — F23 (llr_tables 의존 목록) 정확성·전수성 검증

- 작성: 2026-08-06 23:29:47
- 담당: team_c 워커 3
- 대상: F23 "llr_tables.py 제거 불가 — decoder.py 6곳 의존 (50, 48-55, 72-88, 233, 275-276, 178)"
- 경로 표기: 본체 = `2_LDPC_light/`, 개정본 = `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/`

---

## 총평 (선요약)

- ㉮ **H1 (라인 번호 정확성)**: 6곳 중 5곳 정확, 1곳(`178`)은 분기 시작 줄이 `177`이라 `177-178`로 적어야 한다. 라인 `233`은 위치는 정확하나 인용 구문에 `np.float32(...)` 감싼 부분이 빠졌다. → **부분 확인**
- ㉯ **H2 (전수성)**: 개정본 `decoder.py`에 V6 목록이 놓친 의존처가 **3곳 더** 있다 (`24`, `28-31`, `58-59`). 실제는 6곳이 아니라 **9곳**이다. → **반박됨(과소 집계)**
- ㉰ **핵심 반전**: `llr_tables.py`를 **모듈로서** import 하는 곳은 개정본 전체에서 **단 1곳**(`decoder.py:50`)뿐이다. 나머지 8곳은 "llr_profile 모드"라는 기능의 코드이지 `llr_tables` 모듈 의존이 아니다. 즉 "6곳 의존이라 제거 불가"라는 논리 구조 자체가 부정확하다.
- ㉱ **개정본 기준 llr_profile 모드는 이미 반쯤 죽어 있다** (실증):
  - JSON 진입점(`run.py`)에 `llr_profile` 처리가 전혀 없어 `config.json`으로는 **도달 불가** (문자열이 그대로 넘어가 `AttributeError`)
  - 개정본 `channel.py` 3종 함수 모두 `mag` 인자가 없어 `ch_mag_by_col`(=CH_HD)을 **소비할 수 없다**. 디코더가 받는 채널 LLR은 `decoder.py:124`의 `±8.0` 고정
  - 즉 프로파일 5개 키 중 CH_HD는 도달 불가, TH_HD/EDGE_MAG/BETA/BF_ITERS만 살아 있다
- ㉲ **H4 (두 파일 차이)**: 정말 **docstring 한 줄뿐**이다. → **확인됨**

---

## H1. V6가 지목한 개정본 decoder.py 의존 6곳의 라인 정확성

| # | V6 주장 위치 | 개정본 실제 구문 (원문 인용) | 판정 |
|---|-------------|---------------------------|------|
| 1 | 50 — `from .llr_tables import dv_group` | `decoder.py:50` `            from .llr_tables import dv_group` | **정확** |
| 2 | 48-55 — llr_profile 분기 | `decoder.py:48` `self.profile = llr_profile` / `:49` `if llr_profile is not None:` / `:50` import / `:51` `groups = np.array([dv_group(int(d)) for d in code.col_deg])` / `:52` `self._col_th = llr_profile.th[groups]` / `:53` `self._col_bf = code.col_deg > 5` / `:54` `self._edge_mag = llr_profile.edge_mag` / `:55` `self.beta = np.float32(llr_profile.beta)` | **정확** (블록 시작·끝 모두 일치) |
| 3 | 72-88 — `_vnu_quantize()` 전체 | `decoder.py:72` `    def _vnu_quantize(self, raw, c2v, j, it):` ~ `:88` `        return sgn * mag` | **정확** (함수 시작·끝 정확히 일치) |
| 4 | 233 — `RESET = self._edge_mag[0] if self.profile is not None else self.msg_clip` | `decoder.py:233` `        RESET = np.float32(self._edge_mag[0] if self.profile is not None else self.msg_clip)` | **위치 정확 / 인용 부정확** (`np.float32(...)` 래핑 누락) |
| 5 | 275-276 — `_decode_column_wise`의 프로파일 분기 | `decoder.py:275` `                    if self.profile is not None:` / `:276` `                        v2c = self._vnu_quantize(raw, c2v, j, it)` | **정확** |
| 6 | 178 — `decode_batch` two_set 경로의 프로파일 분기 | `decoder.py:177` `                    if self.profile is not None:` / `:178` `                        v2c = self._vnu_quantize(raw, c2v, j, it)` | **부정확(범위 누락)** — 분기 시작은 177. #5는 `275-276`으로 두 줄을 적었으므로 같은 형태라면 `177-178`이어야 표기가 일관된다 |

**H1 판정: 부분 확인.** 6개 중 4개는 완전 정확, 1개(233)는 위치만 정확하고 인용 구문이 실제와 다르며, 1개(178)는 분기 시작 줄을 빠뜨렸다. 다만 지목된 위치가 존재하지 않거나 다른 곳을 가리키는 사례는 **없다** (허위 위치 0건).

---

## H2. 누락된 의존처 (전수성)

### H2-1. `llr_tables.py`가 정의한 공개 심볼 목록 (먼저 확정)

개정본 `LDPC_base/llr_tables.py` 전문 확인 결과 공개 심볼은 4개다.

| 심볼 | 정의 위치 | 개정본 내 참조처 |
|------|----------|-----------------|
| `LLRProfile` (클래스) | `llr_tables.py:23` | `llr_tables.py:71` (자기 자신) 외 **없음** |
| `dv_group(dv)` | `llr_tables.py:38` | `decoder.py:50,51`, `llr_tables.py:51` |
| `ch_mag_by_col(code, profile)` | `llr_tables.py:49` | `decoder.py:31`(docstring뿐) 외 **코드 참조 없음** |
| `load_profile(path)` | `llr_tables.py:54` | 개정본 전체 **참조 없음** |
| (모듈 내부) `_KEYS` | `llr_tables.py:20` | `load_profile` 내부 전용 |

즉 개정본에서 `llr_tables` 모듈로부터 실제로 import 되는 심볼은 **`dv_group` 하나뿐**이고, import 문도 **`decoder.py:50` 단 한 줄**이다.

### H2-2. V6 목록이 놓친 개정본 decoder.py 의존처 (3곳 추가)

| 추가 # | 위치 | 실제 구문 | 성격 |
|--------|------|----------|------|
| A | `decoder.py:24` | `                 quantize=True, schedule="two_set", llr_profile=None, llr_matrix=None):` | 생성자 시그니처의 `llr_profile` 인자 — 제거 시 반드시 함께 삭제 |
| B | `decoder.py:28-31` | `:28` `llr_profile: llr_tables.LLRProfile — 지정 시 HW-근사 internal precision 모드:` / `:29` `  V2C를 threshold 비교로 EDGE_MAG 4레벨(3-bit) 양자화 ...` / `:30` `  beta는 프로파일 값(기본 0)으로 대체. 채널 LLR은 channel.py에` / `:31` `  llr_tables.ch_mag_by_col(code, profile)를 넘겨 dv별 값 적용.` | docstring이 `llr_tables` 두 심볼을 명시적으로 안내 — 제거 시 고아 문서 |
| C | `decoder.py:58-59` | `:58` `            if llr_profile is not None:` / `:59` `                raise ValueError("llr_profile과 llr_matrix는 동시 지정 불가")` | llr_matrix 분기 안의 상호배타 검사 — profile 제거 시 이 검사도 무의미 |

**개정본 decoder.py 의존처는 6곳이 아니라 9곳이다** (V6 6곳 + A/B/C).

참고로 `self.profile` 참조는 총 5곳(`48`, `77`, `177`, `233`, `275`)이며 `77`은 `_vnu_quantize` 내부(72-88 범위)라 V6 목록에 포함된다. `_col_th`는 `52`(정의)/`80`(사용), `_col_bf`는 `53`(정의)/`77`(사용)로 모두 기존 범위 안이다.

### H2-3. 개정본 `LDPC_base/` 나머지 파일의 의존처 — **0곳**

전수 grep(`llr_tables|dv_group|load_profile|ch_mag_by_col|LLRProfile|llr_profile|_col_th|_col_bf|_edge_mag|self.profile|self.beta|_vnu_quantize`, `--include=*.py --include=*.json --include=*.md`, `__pycache__` 제외) 결과:

- `LDPC_base/__init__.py`, `pcm.py`, `encoder.py`, `channel.py`, `sim.py`, `llr_matrix.py`, `run.py` — **히트 0**
- `config.json` — `llr_profile` 키 **없음** (`decoder` 하위는 `llr_matrix` 하나뿐)
- 실험 폴더 `README.md:31` — `` `LDPC_base/llr_tables.py`(구 프로파일 로더)와 decoder의 `llr_profile` 모드는 코드만 남아 있고 데이터 파일이 없어 사실상 미사용 — 본체 반영 시 제거 후보. `` (F23의 발단 문장)
- `Input/LLR/` 실제 파일 = `LLR_MATRIX_HD_0.txt`, `LLR_MATRIX_HD_1.txt` 둘뿐 → **프로파일 `.txt` 데이터 0개** (README 주장 "데이터 파일이 없어" 사실 확인)

`llr_matrix.py`는 `dv_group`을 쓰지 않고 자체 `col_dv_idx()`(`llr_matrix.py:139-149`)로 매트릭스 파일의 `dv_from/dv_to` 구간을 직접 매칭한다. 즉 **matrix 모드는 `llr_tables`에 전혀 의존하지 않는다**.

### H2-4. `MinSumDecoder(llr_profile=...)` 호출처 전수

| 코드베이스 | 호출처 | 상태 |
|-----------|--------|------|
| 개정본 | **없음** | `run.py:82` `dec = MinSumDecoder(code, **dec_cfg)`가 유일한 생성 지점이고, `dec_cfg`는 JSON `decoder` 블록 그대로. `run.py:76` 은 `llr_matrix`만 pop/resolve 하며 `llr_profile`은 전혀 다루지 않는다 |
| 본체 | `examples/llr_tune.py:62` `dec = MinSumDecoder(code, max_iter=MAX_ITER, llr_profile=prof, schedule=SCHEDULE)` | 유일한 실사용 호출처 |
| 본체 | `mpi_runner.py:47` `dec = MinSumDecoder(code, max_iter=args.max_iter)` | `llr_profile` 미사용 |
| 본체 | `run.py:64` `dec = MinSumDecoder(code, **config.get("decoder", {}))` | JSON 경유 가능하나 실제 config(`examples/fer_curve.json`)의 `decoder`는 `{"max_iter": 120}`뿐 |

### H2-5. JSON 설정 키로서의 `llr_profile` — 개정본에서 **도달 불가** (실증)

스크래치패드 사본에서 `config.json`의 `decoder`를 `{"llr_profile": "ch6688_th842.txt"}`로 바꿔 `run.load_config` → `run.setup`을 호출한 결과:

```
[7] load_config 통과, decoder cfg = {'llr_profile': 'ch6688_th842.txt'}
[7] setup 실패: AttributeError 'str' object has no attribute 'th'
  File ".../LDPC_base/run.py", line 82, in setup
    dec = MinSumDecoder(code, **dec_cfg)
  File ".../LDPC_base/decoder.py", line 52, in __init__
    self._col_th = llr_profile.th[groups]
```

`load_config`는 `llr_profile` 경로를 resolve 하지 않고, `setup`은 `load_profile()`을 호출하지 않는다. 따라서 **JSON 진입점에서 llr_profile 모드는 사용할 수 없다.**

### H2-6. `self.profile is None` 여부로 갈리는 모든 분기 (개정본 전수)

| 위치 | 분기 | 비고 |
|------|------|------|
| `decoder.py:49` | `if llr_profile is not None:` → 프로파일 속성 4종 세팅 | 생성자 |
| `decoder.py:58` | `if llr_profile is not None:` → matrix와 동시 지정 금지 예외 | **V6 누락** |
| `decoder.py:77` | `if self.profile.bf_iters and it <= self.profile.bf_iters and self._col_bf[j]:` | `_vnu_quantize` 내부 BF 분기 |
| `decoder.py:177` | `if self.profile is not None:` → `_vnu_quantize` vs `clip+rint` | two_set |
| `decoder.py:233` | `self._edge_mag[0] if self.profile is not None else self.msg_clip` | column_wise의 RESET |
| `decoder.py:275` | `if self.profile is not None:` → `_vnu_quantize` vs `clip+rint` | column_wise |

`_decode_matrix()`(319-446)에는 `self.profile` 분기가 **없다** (생성자 58-59의 상호배타 검사로 항상 None이 보장되므로).

**H2 판정: 반박됨(과소 집계).** V6의 6곳은 존재하는 곳을 가리키지만 전수가 아니다. 실제 9곳이며, 더 중요하게는 **모듈 import는 1곳뿐**이라 "6곳 의존 → 제거 불가"라는 인과가 성립하지 않는다.

---

## H2 부록. llr_profile 모드 자체는 "코드로서는" 아직 살아 있다 (실증)

README의 "사실상 미사용"이 "코드가 죽었다"는 뜻이라면 부정확하다. 스크래치패드 사본에서 본체 `llr/ch6688_th842.txt`를 읽어 개정본 디코더에 직접 주입한 결과:

```
[1] load_profile OK: LLRProfile(ch6688_th842: ch=[6.0, 6.0, 8.0, 8.0],
    th=[[8.0,4.0,2.0], ...], mag=[7.0,5.0,3.0,1.0], beta=0.0, bf=0)
[2:two_set]     _col_th=(147, 3) _col_bf=(147,) _edge_mag=[7.0,5.0,3.0,1.0] beta=0.0
[3:two_set]     _vnu_quantize 호출 1659회, success=[True, True, True, True]
[2:column_wise] _col_th=(147, 3) _col_bf=(147,) _edge_mag=[7.0,5.0,3.0,1.0] beta=0.0
[3:column_wise] _vnu_quantize 호출 1659회, success=[True, True, True, True]
```

두 스케줄 모두 `_vnu_quantize`가 실제로 호출되고 정상 수렴한다. 즉 **프로그램적으로 직접 구성하면 동작하는 살아 있는 코드**이며, 죽은 것은 "진입 경로(JSON)"와 "데이터 파일"과 "채널 magnitude 소비 경로" 세 가지다.

### 채널 magnitude 경로는 개정본에서 이미 끊겼다

```
[4] ch_mag_by_col shape: (147,) 고유값: [6.0, 8.0]
[5] rber_channel(code, cw, rber, rng, mode='HD')            -> 'mag' 인자 있음? False
[5] fixed_error_channel(code, cw, n_err, rng, mode='HD')    -> 'mag' 인자 있음? False
[5] strong_error_channel(code, cw, n_err, rng, scr, ser, mode='2SD') -> 'mag' 인자 있음? False
[6] dict 채널 -> 디코더가 받은 채널 LLR |값| 집합: [8.0]  (CH_HD [6.0,6.0,8.0,8.0] 은 미반영)
```

개정본 `channel.py`는 3종 함수 모두 `mag` 인자를 없앴고 dict를 반환한다. `decoder.py:120-124`의 legacy 어댑터가 dict를 `±8.0` signed LLR로 바꾸므로, llr_profile 모드를 켜도 **CH_HD는 절대 반영되지 않는다**. 본체 `channel.py:17`의 `mag: 스칼라 또는 (N_b,) column block별 값 (llr_tables.ch_mag_by_col 참조)` 주석에 해당하는 통로가 개정본에는 없다.

이는 F23 판정에 중요하다. 존치하더라도 **현재 개정본의 llr_profile 모드는 원래 설계(CH_HD + TH_HD 동시 적용)의 절반만 재현한다.**

---

## H3. 본체(`2_LDPC_light/`) 쪽 의존처

### H3-1. 본체 `decoder.py` (개정본과 라인이 다름)

| 대응 | 본체 라인 | 실제 구문 | 개정본 대응 라인 |
|------|----------|----------|-----------------|
| 시그니처 | `24` | `                 quantize=True, schedule="two_set", llr_profile=None):` | 24 |
| docstring | `28-31` | `llr_profile: llr_tables.LLRProfile — ...` / `llr_tables.ch_mag_by_col(code, profile)를 넘겨 dv별 값 적용.` | 28-31 |
| 프로파일 분기 | `43-50` | `:43` `self.profile = llr_profile` / `:44` `if llr_profile is not None:` / `:45` `from .llr_tables import dv_group` / `:46-49` `_col_th`/`_col_bf`/`_edge_mag` / `:50` `self.beta = np.float32(llr_profile.beta)` | 48-55 |
| `_vnu_quantize` | `52-68` | `:52` `def _vnu_quantize(self, raw, c2v, j, it):` ~ `:68` `return sgn * mag` | 72-88 |
| two_set 분기 | `136-137` | `if self.profile is not None:` / `v2c = self._vnu_quantize(raw, c2v, j, it)` | 177-178 |
| RESET | `192` | `RESET = np.float32(self._edge_mag[0] if self.profile is not None else self.msg_clip)` | 233 |
| column_wise 분기 | `234-235` | `if self.profile is not None:` / `v2c = self._vnu_quantize(raw, c2v, j, it)` | 275-276 |

본체에는 llr_matrix 모드가 없으므로 개정본의 추가 의존 C(`58-59` 상호배타 검사)에 해당하는 코드가 없다. 즉 **본체는 8곳, 개정본은 9곳**이다.

### H3-2. 본체의 llr_profile 소비처

| 파일:라인 | 구문 | 성격 |
|-----------|------|------|
| `examples/llr_tune.py:19` | `from ..llr_tables import load_profile, ch_mag_by_col` | 유일한 `load_profile`/`ch_mag_by_col` 실사용 |
| `examples/llr_tune.py:60` | `prof = load_profile(path)` | `llr/*.txt` 글롭 로드 (`_` 시작 파일 제외, `:58`) |
| `examples/llr_tune.py:62` | `dec = MinSumDecoder(code, max_iter=MAX_ITER, llr_profile=prof, schedule=SCHEDULE)` | 유일한 `llr_profile=` 호출 |
| `examples/llr_tune.py:63` | `rows.append(measure(code, dec, ch_mag_by_col(code, prof), prof.name))` | CH_HD를 `fixed_error_llr(..., mag=mag)`(`:39`)로 주입 |
| `examples/llr_tune.py:25` | `LLR_DIR = os.path.join(os.path.dirname(HERE), "llr")` | `llr/` 폴더를 가리키는 유일한 코드 |
| `channel.py:17` | `mag: 스칼라 또는 (N_b,) column block별 값 (llr_tables.ch_mag_by_col 참조).` | `bsc_llr(..., mag=8.0)`·`fixed_error_llr(..., mag=8.0)`의 `mag` 인자 근거 |
| `llr/README.md:3,24-26` | `포맷은 [llr_tables.py](../llr_tables.py) 도크스트링 참조` / `prof = load_profile(...)` / `dec = MinSumDecoder(code, llr_profile=prof)` / `mag = ch_mag_by_col(code, prof)` | 사용법 문서 |
| `docs/plan.md:53` | 파일 목록 표의 한 행: `llr_tables.py` = "2-9 포맷 LLR 테이블 파일 로드", C++ 대응 = "`decoder.cpp` LLR 테이블 로드" | 파일 목록 표 |
| `docs/plan.md:19,101` | `speed_opt 2-9의 텍스트 파일 포맷(llr_tables_template.txt)을 그대로 로드` / `LLR 테이블 실값 (llr_tables 템플릿은 공란 ...)` | 계획 근거 |
| `README.md:41` | `실물 H-matrix·LLR 테이블 실값 미반입 (예시 부호 + 균일 양자화 프로파일 사용 중)` | 현황 서술 |

`mpi_runner.py`와 본체 `run.py`는 `llr_profile`을 전혀 쓰지 않는다 (`mpi_runner.py:47`은 `max_iter`만 전달).

### H3-3. `llr/` 폴더 8개 `.txt` + README의 소비 경로

`llr/` 실제 파일 8개: `_hw_orig_ch.txt`, `ch5577_th842.txt`, `ch6666_th842.txt`, `ch66810_th842.txt`, `ch6688_th1052.txt`, `ch6688_th842.txt`, `ch6688_th952.txt`, `ch6688_thdv.txt`.

소비 경로는 **단 하나**다.

```
examples/llr_tune.py:57  glob(LLR_DIR/*.txt)  →  :58 '_' 시작 제외
   →  :60 load_profile()  →  :62 MinSumDecoder(llr_profile=prof)
                           →  :63 ch_mag_by_col() → :39 fixed_error_llr(mag=mag)
```

즉 `_hw_orig_ch.txt`(`_` 시작이라 글롭 제외, 보존 전용)를 뺀 **7개가 `llr_tune.py` 하나에만 소비된다.** `run.py`/`mpi_runner.py`/다른 examples는 `llr/`를 참조하지 않는다.

**부수 발견 (F23 범위 밖, 문서 드리프트):** `llr/README.md`의 파일 표는 `chA_thmid.txt`, `chB_thmid.txt`, `chA_thlow.txt`, `chA_thhigh.txt` 4개를 나열하는데 이 이름의 파일은 **하나도 실재하지 않는다** (실재 7개는 `ch5577_th842` 계열). README 표가 이전 세대 파일명에 머물러 있다. `llr/README.md:24`의 예시 경로 `2_LDPC_light/llr/chA_thmid.txt`도 존재하지 않는 파일이다.

**H3 판정: 확인됨.** 본체에서도 llr_profile 소비의 실체는 `examples/llr_tune.py` 한 파일이며, 디코더 쪽 의존은 개정본과 같은 8개 지점(라인만 다름)이다.

---

## H4. 본체 `llr_tables.py` vs 개정본 `LDPC_base/llr_tables.py` 차이

`diff -u` 실행 결과 (전문):

```diff
@@ -1,7 +1,7 @@
 """LLR 파라미터 프로파일: 2_LDPC_light/llr/*.txt 파일에서 로드.

 원본 C++ (3-bit 빌드, decoder.cpp Get_VNU_Ch_LLR_Adaptive / Get_VNU_Th_Adaptive)의
-internal precision 구조를 1세트로 단순화한 포맷 (Get_VNU_Table_Idx()가 스텁이라
+internal precision 구조를 1세트로 단순화한 포맷 (Get_VNU_Table_Idx()가 항상 0을 반환하는 임시 함수라
 원본도 사실상 1세트 동작):
```

파일 크기 차이 3075 B → 3104 B(+29 B)가 이 한 줄 치환분과 정확히 대응한다. 헝크는 이것 하나뿐이며, 코드(`_KEYS`, `LLRProfile`, `dv_group`, `ch_mag_by_col`, `load_profile`)는 **바이트 단위로 동일**하다.

**H4 판정: 확인됨.** 차이는 docstring 4행 한 줄("스텁" → "항상 0을 반환하는 임시 함수")뿐이다. 이는 용어 순화 규칙(약어·은어 금지) 적용의 흔적으로 보인다.

---

## H5. 제거 시 딸려 나가는 자산 범위

### H5-A. 완전 제거 대상 (llr_profile 전용, 다른 경로가 쓰지 않음)

| 구분 | 대상 | 근거 |
|------|------|------|
| 파일 | 개정본 `LDPC_base/llr_tables.py` 전체(74행) | 참조가 `decoder.py:50` 하나뿐 |
| 파일 | 본체 `llr_tables.py` 전체(74행) | 참조가 `decoder.py:45`, `examples/llr_tune.py:19` |
| 파일 | 본체 `llr/*.txt` 8개 | 소비처가 `examples/llr_tune.py`뿐 |
| 파일 | 본체 `llr/README.md` | 8개 txt의 사용 문서 (표가 이미 실재 파일과 어긋남) |
| 파일 | 본체 `examples/llr_tune.py` 전체(76행) | 파일 전체가 프로파일 튜닝 전용 |
| 코드 | `decoder.py` 개정본 **9곳** = `24`(인자), `28-31`(docstring), `48-55`(분기), `58-59`(상호배타 검사), `72-88`(`_vnu_quantize`), `177-178`, `233`(조건부 → `msg_clip` 고정으로 단순화), `275-276` | H1·H2 |
| 코드 | `decoder.py` 본체 **8곳** = `24`, `28-31`, `43-50`, `52-68`, `136-137`, `192`, `234-235` (상호배타 검사 없음) | H3-1 |
| 코드 | 본체 `channel.py`의 `mag` 인자 (`bsc_llr` `:14`, `fixed_error_llr` `:27`) + `:17` 주석 | 유일 사용처가 `llr_tune.py:39` (`fixed_error_sweep.py:39`·`select_irregular.py:38`은 mag 미지정). **단 기본값 8.0 동작 유지를 위해 인자 제거는 선택 사항** |
| 문서 | 개정본 `README.md:31`(제거 후보 주의문), 본체 `docs/plan.md:53`(파일 목록 행) | 제거 시 갱신 필요 |
| 문서 | 본체 `docs/plan.md:19,101`, `README.md:41` | "프로파일" 서술 재조정 필요 (llr_matrix 모드로 대체됨을 반영) |

### H5-B. 반드시 남겨야 하는 것 (다른 경로도 쓰는 공유 코드)

| 대상 | 남겨야 하는 이유 (근거 라인) |
|------|--------------------------|
| `self._edge_mag` 속성 자체 | llr_matrix 모드가 독립적으로 `decoder.py:68`에서 `np.array([7,5,3,1])`로 세팅하고, `:96`(`_mx_vnu_quantize`)과 `:353`(`_decode_matrix`의 RESET)에서 소비한다. **프로파일 제거와 무관하게 존속** |
| `self.beta` / `cn_mag_fn()` | `:44`(생성자 기본 인자), `:69`(matrix 모드가 0.0으로 덮어씀), `:108`(`cn_mag_fn`)에서 쓰인다. 프로파일은 `:55`에서 값만 덮어쓸 뿐 |
| `_mx_vnu_quantize()` (`:90-102`) | matrix 모드 전용. `_vnu_quantize`와 이름이 비슷하나 **별개 함수**이므로 함께 지우면 안 된다 |
| `self.msg_clip` / `self.quantize` | 비프로파일 경로(`:180-182`, `:278-280`)와 `:206-207`(deg-1 row 방어)에서 사용 |
| `llr_matrix.py`의 `col_dv_idx()` (`:139-149`) | `dv_group`과 무관한 독립 구현. `llr_tables` 제거의 영향 없음 |
| 본체 `channel.py`의 `bsc_llr`/`fixed_error_llr`/`awgn_llr` 함수 자체 | `mag` 인자만 프로파일 연계이고 함수는 `run.py:27-28`, `mpi_runner.py:51,53`, `examples/fixed_error_sweep.py:39`, `examples/select_irregular.py:38`이 쓴다 |

### H5-C. 제거 시 회귀 위험이 낮은 이유

- ㉮ 개정본 기준 `llr_profile`은 JSON에서 도달 불가 (H2-5 실증) → 실행 경로 회귀 없음
- ㉯ 개정본 `Input/LLR/`에 프로파일 데이터가 0개 → 데이터 자산 손실 없음
- ㉰ 개정본은 이미 채널 magnitude 통로를 끊어 CH_HD가 무시되므로(H2 부록), 존치해도 반쪽 기능
- ㉱ 대체 기능인 llr_matrix 모드가 EDGE_MAG 4레벨 양자화(`_mx_vnu_quantize`)를 **iteration/CSW 적응형으로 상위 호환** 제공한다 (`decoder.py:90-102`, `407`)

### H5-D. 제거 시 실제로 잃는 것 (존치 논거)

- ㉮ 본체 `llr/` 7개 튜닝 프로파일과 `examples/llr_tune.py`의 **비교 실험 자산** (2026-08-03 튜닝 그리드 기록 포함, `llr/ch6688_th842.txt:1-2` 주석)
- ㉯ `_hw_orig_ch.txt`에 보존된 **원본 C++ 실값** `CH_HD 21 14 12 10`, `EDGE_MAG 7 5 3 1` (`llr/_hw_orig_ch.txt:4,6`). 이 값은 llr_matrix 파일에는 담기지 않으므로, 파일을 지우면 원본 실값의 유일한 보존처가 사라진다. **최소한 이 파일 또는 그 값은 문서로 이관해야 한다**
- ㉰ llr_matrix 파일이 없는 상황에서의 3-bit 근사 실험 수단 (현재 `Input/LLR/`에 matrix 파일이 있으므로 실질 영향은 작음)

**H5 판정: 확인됨(범위 확정).** 제거 대상은 파일 12개(코드 3 + 데이터 8 + README 1)와 디코더 코드 9곳(개정본)/8곳(본체)이며, `_edge_mag`·`beta`·`_mx_vnu_quantize`는 matrix 모드가 계속 쓰므로 **남겨야 한다**.

---

## 최종 판정 요약

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| H1 — 6곳 라인 정확성 | **부분 확인** | 4곳 완전 정확, `233`은 인용 구문 부정확, `178`은 `177-178`이어야 함. 허위 위치 0건 |
| H2 — 전수성 | **반박됨(과소 집계)** | `24`, `28-31`, `58-59` 누락 → 실제 9곳. 더불어 모듈 import는 `50` 단 1곳 |
| H3 — 본체 쪽 의존 | **확인됨** | 디코더 8곳(라인 다름) + `examples/llr_tune.py` 1파일 + `llr/` 8파일 + `channel.py` mag 인자 |
| H4 — docstring 한 줄뿐 | **확인됨** | `diff -u` 헝크 1개, 4행 한 줄 치환 |
| H5 — 제거 범위 | **확인됨** | 제거 12파일 + 코드 9곳, 유지 대상은 `_edge_mag`/`beta`/`_mx_vnu_quantize` 등 matrix 공유분 |

### F23 처방에 대한 권고 (Decision 안건 정리)

- ㉮ V6의 "6곳 의존이라 제거 불가"는 **논거로서 부적절**하다. 의존 수는 제거 난이도를 뜻할 뿐이고, 실제 결합도는 import 1줄 + 기능 코드 8곳이며 모두 한 기능에 국한된다
- ㉯ 개정본 README의 "제거 후보" 판단은 **사실 관계에서 옳다** (JSON 도달 불가 + 데이터 0개 + CH_HD 통로 단절). 다만 "미사용"이라는 표현은 "코드가 죽었다"로 오독될 수 있어 "진입 경로 없음"으로 고쳐 쓰는 편이 정확하다
- ㉰ 제거를 택할 경우 **선행 조건 하나**: `llr/_hw_orig_ch.txt`의 원본 실값(`CH_HD 21 14 12 10`, `EDGE_MAG 7 5 3 1`)을 문서(`docs/plan.md` 또는 `0_LDPC_original/CLAUDE.md` 상수표)로 이관한 뒤 삭제할 것
- ㉱ 존치를 택할 경우 **최소 보수 두 가지**: `run.py`에 `llr_profile` 경로 resolve + `load_profile()` 호출 추가, 개정본 `channel.py`에 `mag` 인자 복원(그렇지 않으면 CH_HD가 영원히 무시됨)

---

## 검증 방법 기록

- 파일 직접 열람: 개정본 `decoder.py`(447행 전문), `llr_tables.py`(74행 전문), `run.py`, `channel.py`, `sim.py`, `__init__.py`, `config.json`, 실험 `README.md`; 본체 `decoder.py:1-75`, `channel.py`, `run.py`, `mpi_runner.py`, `examples/llr_tune.py`, `llr/README.md`, `llr/_hw_orig_ch.txt`, `llr/ch6688_th842.txt`
- 전수 grep: `llr_tables|dv_group|load_profile|ch_mag_by_col|LLRProfile|llr_profile|_col_th|_col_bf|_edge_mag|self.profile|self.beta|_vnu_quantize|profile\b` (`*.py`, `*.json`, `*.md`, `*.txt`; `__pycache__` 제외)
- `diff -u` 로 두 `llr_tables.py` 대조
- 스크래치패드 사본 실행 (`.../scratchpad/f23/probe.py`) — 프로젝트 파일은 읽기만 함, 수정 없음
