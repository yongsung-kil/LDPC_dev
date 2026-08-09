# 검증팀 c (docs_data) 워커 3 — TD-7 / TD-8 / TD-9 독립 재확인

> 대상: `docs/plan.md` 머리 단서, `_pm/DONE.md:70`, 삭제된 `examples/llr_tune.py`
> 방법: 문서 원문 직접 열람, `git ls-files` / `git log` / `git show`, 저장소 전수 grep,
> `load_config()` 실행 실증
> 산출물 보관: 복구한 `llr_tune.py` 전문은 scratchpad에만 저장 (저장소 무수정)

---

## 판정 요약

| 가설 | 1단계 (서술 존재) | 2단계 (사실 불일치) | 최종 |
|------|------------------|---------------------|------|
| H7 (TD-7) | 확인됨 | 항목별로 갈림 | **부분 확인** |
| H8 (TD-8) | 확인됨 | 반박됨 | **반박됨** (별도 문제는 남음) |
| H9 (TD-9) | 확인됨 | 확인됨 | **확인됨** |

---

# H7 (TD-7) — plan.md 머리 단서가 틀린 정보를 보증하는가

## 1단계 — 서술 존재

**확인됨.** 라인 번호도 정확하다.

### E7-1. 머리 단서 원문 (`docs/plan.md:3-10`)

```
 3	> 생성일: 2026-07-29
 4	> **2026-08-07 구조 개편**: `_test/20260806_setup_구성_실험/` 개정본을 본체로 반영 —
 5	> 현행 구조·스키마·실행 방법은 [README.md](../README.md)가 정본이다. 이 문서의
 6	> §3.1 모듈 표 등 구조 서술은 개편 전 기준이며, 결정 이력(§1, §7)은 계속 유효.
 7	> **목적**: LDPC 논문 아이디어를 빠르게 적용/비교하기 위한 vanilla 형태의 경량 Python 시뮬레이터.
```

문언을 그대로 읽으면 단서는 두 갈래로 나뉜다.

- ㉮ **무효 선언 쪽**: "이 문서의 **§3.1 모듈 표 등 구조 서술**은 개편 전 기준" (`:5-6`).
  "§3.1 모듈 표"는 예시이고 실제 범위는 "**등 구조 서술**"이다. 문법적으로 §3.1b 도구 표,
  §3.2 배열 설계, §5 진행 순서는 모두 "구조 서술"에 해당하므로 이 무효 선언의 사정 범위 안이다.
- ㉯ **유효 보증 쪽**: "**결정 이력(§1, §7)은 계속 유효**" (`:6`). 절 번호로 §1 전체와 §7
  전체를 지목하며 한정 문구가 없다. 이 보증에는 예외 표시가 하나도 없다.

즉 가설이 말하는 "보증"은 §1과 §7에 한해 문언상 실재한다.

### E7-2. §7 #4 원문과 그 성격 (`docs/plan.md:122-129`)

```
122	## 7. 확정 사항 (2026-07-30 사용자 결정)
124	| # | 항목 | 결정 |
129	| 4 | 시뮬 파라미터 | **max_iter = 120** (2026-07-30 사용자 지정). SNR/RBER 범위·배치 크기는 실험별 설정 |
```

절 제목이 "확정 사항 (2026-07-30 사용자 결정)"이고 열 이름이 "항목 / 결정"이다.
항목명은 "**시뮬 파라미터**"이며 같은 칸이 "SNR/RBER 범위·배치 크기는 실험별 설정"이라고
덧붙인다. 따라서 §7 #4는 **실험 파라미터 값의 결정**이지 설정 파일 키 규약이 아니다.
`decoder.max_iter`라는 키 이름은 plan.md 어디에도 없다.

**판정: 서술 존재 확인됨. 다만 성격은 "config 키 규약"이 아니라 "실험 파라미터 값 결정"이다.**

## 2단계 — 항목별 사실 불일치 판정

### E7-3. `run.py:178-181` — `decoder.max_iter` 에러 처리

원문:

```python
177	    decoder_config = config.setdefault("decoder", {})
178	    if "max_iter" in decoder_config:
179	        raise ValueError(
180	            "decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(또는 "
181	            "internal_quantize.max_iter)이 결정")
```

**실행 실증** (scratchpad 사본 config에 `decoder.max_iter = 120` 추가 후 `load_config()` 호출):

```
RAISED ValueError : decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(또는 internal_quantize.max_iter)이 결정
```

대체 경로는 두 갈래다.

- ㉮ `use_input_llr_matrix=true`: `LLRMatrix.max_iter = int(self.row_iter[-1, 1])`
  (`LDPC_base/llr_matrix.py:92`) → `decoder.max_iter = llr_matrix.max_iter`
  (`LDPC_base/decoder.py:116`). 기본 config가 쓰는 `Input/LLR/LLR_MATRIX_HD_1.txt`의
  마지막 row는 `... -1  2  20  -1`이므로 **max_iter = 20**이다.
- ㉯ `use_input_llr_matrix=false`: `decoder.internal_quantize.max_iter`
  (`run.py:199-200`). 그리고 **현행 `config.json:33`은 이 값을 `120`으로 두고 있다.**

**판정: 에러 처리 확인됨. 그러나 "§7 #4와 충돌"은 성립하지 않는다.**
§7 #4가 확정한 것은 값 120이고, 그 값은 `config.json:33`
`"internal_quantize": { ..., "max_iter": 120, ... }`에 지금도 살아 있다. 없어진 것은
`decoder.max_iter`라는 **키 이름**뿐이며, 그 키 이름은 §7 #4가 결정한 적이 없다.

### E7-4. §3.1b, §3.2, §5 개별 판정

#### §3.1b 도구 표 (`docs/plan.md:70-79`)

| 라인 | 원문이 적은 파일 (역할 요약) | 실제 | 판정 |
|------|------------------------------|------|------|
| `:72` | `tools/peg.py` — PEG(Progressive Edge Growth)로 base graph 생성 | `2_LDPC_light/tools/H_mat_gen/peg.py` | **어긋남 확인됨** (경로) |
| `:73` | `tools/lifting.py` — base graph를 QC lifting | `2_LDPC_light/tools/H_mat_gen/lifting.py` | **어긋남 확인됨** (경로) |
| `:74` | `tools/gen_example_code.py` — 위 둘을 묶어 예시 H-matrix 파일 생성 | `2_LDPC_light/tools/H_mat_gen/gen_example_code.py` | **어긋남 확인됨** (경로) |
| `:75` | `examples/fer_curve.py` — 예시 부호로 FER 테스트 실행, 정정능력 커브 출력 | 파일 부재 (커밋 `6fb35cf`에서 삭제) | **어긋남 확인됨** (부재) |

파일시스템 확인 결과: `find 2_LDPC_light -name fer_curve.py` → 0건,
`ls 2_LDPC_light/examples` → `No such file or directory`.

`:77-79` 세 불릿(예시 부호 파라미터, LLR 매핑, 저장 포맷)은 예시 부호의 설계 방침 서술이며
현행과 충돌하는 사실 주장은 없다. 따라서 "**4행 전부**"는 표의 4개 행을 가리키는 것으로
읽을 때만 맞고, 절 전체(`:70-79` 10줄)를 가리키는 것으로 읽으면 과장이다.

#### §3.1 모듈 표 (`docs/plan.md:51-61`) — 단서가 명시적으로 지목한 절

`git ls-files`와 파일시스템으로 전수 확인했다.

| plan.md 열거 | 실제 | 판정 |
|--------------|------|------|
| `config.py` (`:53`) | 저장소 전체 0건 (JSON `config.json`이 역할 수행) | 부재 |
| `pcm.py` (`:54`) | `LDPC_base/pcm.py` | 경로 변경 |
| `encoder.py` (`:55`) | `LDPC_base/encoder.py` | 경로 변경 |
| `llr_tables.py` (`:56`) | `2_LDPC_light/llr_tables.py` 실재하나 import 0건 (H8 참조). 현행 로더는 `LDPC_base/llr_matrix.py` | 사문화 모듈 열거 |
| `channel.py` (`:57`) | `LDPC_base/channel.py` | 경로 변경 |
| `decoder.py` (`:58`) | `LDPC_base/decoder.py` | 경로 변경 |
| `sim.py` (`:59`) | `LDPC_base/sim.py` | 경로 변경 |
| `run.py` (`:60`) | `LDPC_base/run.py` | 경로 변경 |
| `mpi_runner.py` (`:61`) | 저장소 전체 0건 (삭제, `_pm/TODO.md:25-26` 재설계 등록) | 부재 |

이 절은 단서가 이름을 대어 무효화한 곳이므로 어긋남 자체는 단서와 모순되지 않는다.

#### §3.2 배열 설계 (`docs/plan.md:84`)

원문 발췌:

```
py도 (B, M_b, z) CN 상태 + (B, E, z) edge sign을 모두 갖는다.
...
py `schedule="column_wise"`(기본 대응)로 재현, `two_set`(flooding 등가)은 비교용으로 유지
```

| 부분 | 실제 | 판정 |
|------|------|------|
| `(B, M_b, z)` CN 상태 + `(B, E, z)` edge sign | `decoder.py:217-222` — `min1`/`min2`/`min1_pos`/`check_sum`이 `(B, M_b, z)`, `edge_sgn`이 `(B, num_edges, z)` | **어긋나지 않음** |
| `schedule="column_wise"`, `two_set`은 비교용으로 유지 | `two_set` / `column_wise` / `schedule` 심볼이 `LDPC_base/`, `config.json`, `Ideas/`에서 **0건** (grep 전수). two_set 경로는 DONE.md:128-130 기록대로 삭제됨 | **어긋남 확인됨** |

§3.2는 한 줄 안에서 절반은 맞고 절반은 틀리다.

#### §5 진행 순서 (`docs/plan.md:110-112`)

| 라인 | 원문 | 판정 |
|------|------|------|
| `:110` | `2. 예시 부호 도구(PEG/lifting/dual-diagonal) + 예시 FER 테스트 → 정정능력 커브 출력 (완료 2026-07-30)` | **어긋나지 않음.** 2026-07-30 시점의 완료 사실을 적은 진행 기록이며, 커브 출력 기능은 `run.py`의 `log.fer_curve_png`가 이어받았다 |
| `:111` | `3. H-matrix / LLR 테이블 실물 파일 확인 (z_sb=256 대상 파일 식별) → 실물 파라미터로 교체` | **어긋나지 않음.** `_pm/TODO.md:31`에 같은 항목이 미완으로 살아 있다. "LLR 테이블"이라는 옛 이름만 현행 "LLR_MATRIX"와 다르다 |
| `:112` | `4. mpi_runner + 슈퍼컴 반입` | **어긋나지 않음.** 파일은 삭제됐으나 `_pm/TODO.md:25-26, 33`이 재설계 후 반입을 그대로 계획으로 유지한다. 미래 계획 항목이라 부재가 곧 오류는 아니다 |

**§5는 어긋남이 확인되지 않는다.** 가설이 §5를 어긋남으로 든 것은 근거가 약하다.

### E7-5. false positive 반증 — "단서가 틀린 정보를 보증한다"는 판정은 과장인가

두 갈래를 모두 검토했다.

**반론 쪽 (판정이 과장이라는 주장)**

- ㉮ plan.md는 제목부터 "(계획)"이고 §1 제목이 "배경 — 확정된 결정 사항 (2026-07-29 논의)",
  §7 제목이 "확정 사항 (2026-07-30 사용자 결정)"이다. 절 제목이 결정 시점을 명시하는
  이력 문서이므로, 과거 시점의 구조를 서술하는 것 자체는 정상이다.
- ㉯ 단서의 무효 선언은 "§3.1 모듈 표 **등 구조 서술**"이라 열려 있다. §3.1b 도구 표,
  §3.2 배열 설계는 문언상 이 "등 구조 서술"에 포함된다. 따라서 "단서가 **지목하지 않은**
  §3.1b·§3.2"라는 가설의 표현은 문언에 어긋난다.
- ㉰ 가설이 핵심 증거로 든 §7 #4는 **값 120의 결정**이고, 그 값은 `config.json:33`에
  지금도 120으로 살아 있다. `run.py:178-181`이 막는 것은 키 이름 `decoder.max_iter`이며
  §7 #4는 키 이름을 결정한 적이 없다. **핵심 증거가 성립하지 않는다.**

**성립 쪽 (그럼에도 보증에 오류가 있다는 주장)**

단서가 "계속 유효"라고 보증한 §1 안에 현행과 정면으로 어긋나는 결정이 하나 있다.

`docs/plan.md:22` (§1 #5) 원문 발췌:
`speed_opt 2-9의 텍스트 파일 포맷([llr_tables_template.txt](../../1_LDPC_revised/llr_tables_template.txt))을 그대로 로드`

현행 코드는 이 포맷을 로드하지 않는다. `LDPC_base/llr_matrix.py:9-13`이
`파일 포맷 (DAO_LLR_MATRIX.py Read_Input_LLR_Matrix와 동일, 빈 줄 무시)`라고 밝히고,
`README.md:15`가 `Input/LLR/` 폴더를 `**DAO LLR_MATRIX 형식만 사용**`으로 못 박는다.
2-9 템플릿 포맷을 읽는 코드는 사문화된 `2_LDPC_light/llr_tables.py`뿐이며 import 0건이다.

또한 §1 #5의 `Get_VNU_Table_Idx()` 스텁 서술과 §1 #6의 CLAUDE.md 상수표 관련 서술은
`0_LDPC_original/` 기준 관찰이라 현행 Python과 무관하게 유지된다.

**결론**

- ㉮ "단서가 틀린 정보를 **보증하는 상태**"라는 결론 자체는 **성립한다.** 단서가 무조건
  유효를 선언한 §1 안에 §1 #5라는 현행 위배 항목이 실재하기 때문이다.
- ㉯ 그러나 가설이 제시한 **근거 구성은 대부분 성립하지 않는다.** 핵심 증거 §7 #4는
  충돌이 아니고, "단서가 지목하지 않은 §3.1b·§3.2"는 "등 구조 서술"에 포함되며,
  §5는 어긋남이 확인되지 않는다.
- ㉰ 따라서 **"단순한 낡음이 아니다"라는 강도 주장은 과장**이다. 확인된 실체는
  "단서의 유효 보증 범위(§1)에 예외 항목 1건(§1 #5)이 있고, 무효 선언 쪽 절들은
  단서 문언대로 낡은 것"이다.

### E7-6. CLAUDE.md 규칙 ㉮ 위반 여부

규칙 ㉮ 원문 (`CLAUDE.md:61-64`):
`**수리는 덧대기가 아니라 다시 쓰기**: 리뷰 반영이나 수정 시 기존 문장 뒤에 단서나
괄호를 덧붙이지 않는다. ... 과거가 어땠고 지금 어떻다는 서술을 코드와 문서에 남기지 않는다`

`git show d42ca8c --stat`을 포함한 델타 확인 결과, 이번 개편에서 plan.md에 들어간 변경은
`:4-6` 3줄이 전부이고 본문은 손대지 않았다. 문서 머리에 "개편 전 기준"이라는 단서를 붙여
본문을 무효화하는 방식은 규칙 ㉮가 지목한 **덧대기 그 자체**다.

**판정: 규칙 ㉮ 위반 확인됨.** 이것이 TD-7에서 가장 견고한 부분이다.

## H7 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E7-1 | 머리 단서 원문과 보증 범위 | **확인됨** | `docs/plan.md:4-6`. 무효 선언은 "§3.1 모듈 표 **등 구조 서술**", 유효 보증은 "결정 이력(§1, §7)" 무조건 |
| E7-2 | §7 #4의 성격 | **확인됨 (단, 성격은 값 결정)** | `docs/plan.md:129` 절 제목 "확정 사항", 항목명 "시뮬 파라미터". config 키 규약 아님 |
| E7-3 | `decoder.max_iter` 에러 처리 | **확인됨** | `run.py:178-181`, 실행 실증 `ValueError` 발생. 대체는 `llr_matrix.py:92`, `decoder.py:116`, `run.py:199-200` |
| E7-3b | §7 #4와의 "충돌" | **반박됨** | 값 120은 `config.json:33` `internal_quantize.max_iter`에 존속. 금지된 것은 키 이름뿐 |
| E7-4a | §3.1b 표 4행 경로·부재 | **어긋남 확인됨 (4행 모두)** | `plan.md:72-75` 대 `tools/H_mat_gen/{peg,lifting,gen_example_code}.py`, `fer_curve.py` 부재 |
| E7-4b | §3.1 표 모듈 부재 | **확인됨** | `config.py` 0건, `mpi_runner.py` 0건, 나머지 6개는 `LDPC_base/`로 이동 |
| E7-4c | §3.2 CN 상태 배열 서술 | **어긋나지 않음** | `decoder.py:217-222` 형상 일치 |
| E7-4d | §3.2 schedule 서술 | **어긋남 확인됨** | `two_set`/`column_wise`/`schedule` grep 0건 |
| E7-4e | §5 :110-112 | **어긋나지 않음** | 진행 기록·미완 계획이며 `_pm/TODO.md:25-26, 31, 33`과 정합 |
| E7-5 | 보증 범위 안의 실제 오류 | **확인됨 (§1 #5)** | `plan.md:22` "2-9 텍스트 파일 포맷 그대로 로드" 대 `llr_matrix.py:9-13`, `README.md:15` DAO 포맷 전용 |
| E7-6 | 규칙 ㉮ 덧대기 | **확인됨** | 델타 변경분이 `plan.md:4-6` 3줄뿐, 본문 무수정 |

## H7 최종 판정: **부분 확인**

- 성립: 머리 단서의 존재와 문언, §3.1b 4행 어긋남, §3.2 schedule 어긋남, 규칙 ㉮ 덧대기,
  그리고 보증 범위 안의 실제 오류 1건(§1 #5).
- 불성립: 핵심 증거로 제시된 §7 #4 max_iter 충돌(값은 존속), "단서가 지목하지 않은 §3.1b·§3.2"
  (문언상 포함됨), §5 어긋남.
- 심각도는 HIGH 유지가 어렵다. 근거가 §1 #5 한 건과 문서 규칙 위반으로 좁혀지므로
  **MEDIUM 하향을 권한다.** 처방은 Round 2의 D1(plan.md 성격 결정)이 그대로 유효하다.

---

# H8 (TD-8) — DONE.md "llr_tables.py 삭제"가 허위인가

## 1단계 — 서술 존재

**확인됨.** `_pm/DONE.md:70` 원문:

```
70	  F14 주석·문서화, llr_profile 제거(llr_tables.py 삭제), 채널 리스트 복원
```

## 2단계 — 사실 불일치 판정: **반박됨**

### E8-1. 항목이 속한 절 전체와 "삭제"의 지시 대상

`_pm/DONE.md:65-76` 절 전체를 읽으면 대상 범위가 절 안에서 명시된다.

```
65	### 2026-08-07 — LDPC_base 개정본 딥 리뷰 + 후속 수정 (완료 처리는 TODO 점검에서)
66	Round 1→2→3 딥 리뷰 후 사용자 확정 회신대로 후속 수정, 자동 검증 51건 통과
67	- **배경**: `_test/20260806_setup_구성_실험/LDPC_base/` 개정본(2026-08-06 시점)의 정합성 검증
68	- **변경** (후속 수정): 키맵+필수값+config checker, strong_error 2단계 추출,
69	  F8 캐스케이드 교체, F11 LLR matrix 제약 정리(겹침 거부·restart 제약 유지, DAO 규칙 정본),
70	  F14 주석·문서화, llr_profile 제거(llr_tables.py 삭제), 채널 리스트 복원
```

절의 **배경**이 대상을 `_test/20260806_setup_구성_실험/LDPC_base/` 개정본으로 못 박는다.
따라서 `:70`의 "llr_tables.py"는 그 개정본 안의 파일을 가리킨다.

**결정적 근거**: 같은 작업의 태스크 문서가 지시 대상을 경로까지 적어 두었다.
`_pm/done/20260807_리뷰후속수정/20260807_리뷰후속수정.md:85`:

```
85	- `LDPC_base/llr_tables.py` — 삭제 (llr_profile 제거에 딸림)
```

`_test/`는 `.gitignore:24`로 추적 제외이므로 이 파일은 git 이력에 없다
(`git log --all -- '*LDPC_base/llr_tables.py'` → 0건). 현재 파일시스템에도 없다
(`find 2_LDPC_light -name "llr_tables*"` → `2_LDPC_light/llr_tables.py`와 그 `.pyc`만).
즉 **`LDPC_base/llr_tables.py`는 실제로 삭제됐고, DONE.md의 기록은 그 대상에 대해 참이다.**

**판정: 반박됨.** DONE.md:70은 허위 기록이 아니다. 별개 경로(`2_LDPC_light/llr_tables.py`)의
존속을 그 문장이 부정한 적이 없다.

### E8-2. `2_LDPC_light/llr_tables.py`의 추적 상태

```
$ git ls-files 2_LDPC_light/llr_tables.py
2_LDPC_light/llr_tables.py
```

파일 실물도 존재한다 (`3075 B`, 74행). git 이력상 `fe49c74`(재구성 초기) → `a9f85f4`(폴더명 변경)
이후 손대지 않은 상태다.

**판정: 확인됨** (추적 중이고 실재).

### E8-3. import 전수 grep

저장소 전체를 `llr_tables`, `llr_profile`, `LLRProfile`, `load_profile`, `ch_mag_by_col`,
`dv_group` 6개 패턴으로 검색했다. **실행 코드에서 이 심볼을 참조하는 곳은 0건이며**,
검출된 매치는 전부 ㉮ 파일 자신의 정의부(`llr_tables.py:23,33,38,49,51,54,71`)
㉯ `_pm/`·`docs/review/` 아래 리뷰 기록 ㉰ `1_LDPC_revised/`의 C++ 쪽 동명이물
`llr_tables.txt`(별개 파일)뿐이다.

**판정: 확인됨** (import 0건, 사문화 모듈).

### E8-4. `llr/` 폴더의 삭제 시점

`llr_tables.py:1` 원문: `"""LLR 파라미터 프로파일: 2_LDPC_light/llr/*.txt 파일에서 로드.`

`git log --diff-filter=D -- '2_LDPC_light/llr/*'` → 커밋 **6fb35cf**
(`2026-08-07 15:30:02`, `chore: 구 예시 스크립트와 LLR 프로파일 삭제 (사용자 정리)`).
이 커밋이 `llr/README.md`와 `llr/*.txt` 8개를 전부 삭제했다.
현재 `find 2_LDPC_light -type d -name "llr*"` → 0건.

**판정: 확인됨** (읽을 파일이 없는 로더가 남았다).

### E8-5. `docs/plan.md:56`의 서술

```
56	| `llr_tables.py` | 2-9 포맷 LLR 테이블 파일 로드 | `decoder.cpp` LLR 테이블 로드 |
```

이 행은 §3.1 "코드 위치·모듈 구성" 표 안에 있고, 머리 단서가 §3.1을 이름 대어 무효화했다.

"세 곳이 서로 다른 이야기"라는 주장을 셋으로 나누어 판정한다.

| 곳 | 말하는 내용 | 판정 |
|----|-------------|------|
| 파일 실물 | `2_LDPC_light/llr_tables.py`가 추적된 채 남아 있고 import 0건, 읽을 `llr/`도 없음 | 사실 |
| `_pm/DONE.md:70` | `_test/.../LDPC_base/llr_tables.py`를 삭제했다 | 사실 (별개 파일) |
| `docs/plan.md:56` | 이 모듈이 모듈 구성의 하나다 | 낡음. 단, 단서가 §3.1을 무효화한 범위 안 |

**판정: "서로 다른 이야기"는 성립하지 않는다.** 세 서술은 각각 다른 대상을 말하고 있고
서로 모순되지 않는다. 남는 실제 문제는 **모순이 아니라 사문화 모듈의 존속**이다.

## H8 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E8-1 | DONE.md:70의 "삭제" 지시 대상 | **반박됨 (허위 아님)** | `DONE.md:65,67` 절 범위 + `_pm/done/20260807_리뷰후속수정/20260807_리뷰후속수정.md:85` `LDPC_base/llr_tables.py — 삭제`. `git log --all -- '*LDPC_base/llr_tables.py'` 0건 (`.gitignore:24` `_test/`) |
| E8-2 | `2_LDPC_light/llr_tables.py` 추적·실재 | **확인됨** | `git ls-files` 출력, 파일 74행 실재 |
| E8-3 | import 0건 | **확인됨** | 6패턴 저장소 전수 grep, 실행 코드 참조 0건 |
| E8-4 | `llr/` 폴더 삭제 | **확인됨** | 커밋 `6fb35cf` (2026-08-07 15:30:02), `llr/` 9개 파일 삭제. 현재 폴더 0건 |
| E8-5 | plan.md:56 서술과 3자 모순 | **부분 반박됨** | `plan.md:56` 존재는 확인. "세 곳이 다른 이야기"는 불성립 (대상이 각각 다름) |

## H8 최종 판정: **반박됨**

가설의 핵심 주장 "`_pm/DONE.md:70`이 사실과 다르다"는 **성립하지 않는다.**
그 문장의 지시 대상은 `_test/.../LDPC_base/llr_tables.py`이며 실제로 삭제됐다.

다만 부수 사실은 전부 확인됐다.

- ㉮ `2_LDPC_light/llr_tables.py`는 추적된 채 남아 있고 import 0건이다.
- ㉯ 이 모듈이 읽는 `llr/` 폴더는 커밋 `6fb35cf`에서 삭제됐다.
- ㉰ 이름이 같은 두 파일이 한 저장소에 있어 DONE.md 독자가 오독하기 쉽다.

**재구성 권고**: TD-8을 "DONE.md 허위 기록 (HIGH)"에서 **"사문화 모듈
`2_LDPC_light/llr_tables.py` 존속 (MEDIUM)"**으로 바꿔 쓸 것을 권한다. 처방은 파일 삭제와
`plan.md:56` 정리이며, 이때 `llr/_hw_orig_ch.txt`의 원본 CH_HD 실값 `{21,14,12,10}`이
`git show 6fb35cf^:2_LDPC_light/llr/_hw_orig_ch.txt`로만 남는다는 점을 함께 처리해야 한다.

---

# H9 (TD-9) — llr_tune.py 탐색 기능이 대체 없이 사라지고 미등록인가

## 1단계 — 삭제 사실과 파일 내용

**확인됨.**

### E9-1. 삭제 커밋과 파일 전문

- 삭제 커밋: `git log --diff-filter=D -- '*llr_tune.py'` → **6fb35cf**
  (`2026-08-07 15:30:02`). `--stat`상 `2_LDPC_light/examples/llr_tune.py | 75 ----`.
- 복구: `git show 6fb35cf^:2_LDPC_light/examples/llr_tune.py`
  → scratchpad에 저장, `wc -l` = **75**. **75줄 확인됨.**

파일 docstring(`:1-9`) 원문:

```
"""LLR 프로파일 튜닝: llr/ 폴더의 프로파일들을 fixed-error 포인트에서 비교.

HW-근사 3-bit internal precision(VNU 출력 {7,5,3,1} + dv별 채널 LLR)의 TH_HD
시작값 후보들을 비교해 좋은 것을 고른다 (TH 원본 소실 — plan.md 참조).
비교 기준선: 프로파일 없는 기존 6-bit 선형 모드.

실행: python -m 2_LDPC_light.examples.llr_tune
출력: out/llr_tune.csv
"""
```

코드를 읽어 실제 기능 범위를 정리한다.

- ㉮ **후보 집합**: `glob(llr/*.txt)` 중 `_` 시작 파일 제외 (`:57-58`). 즉 폴더에 놓인
  ch/th 프리셋 전부를 자동으로 후보로 삼는다.
- ㉯ **기준선**: 프로파일 없는 6-bit 선형 모드, `ch=8.0` (`:53-55`).
- ㉰ **지표**: 각 후보를 fixed-error 포인트 `[300, 340, 360, 380]` (`:31`)에서 실행해
  FER, 에러 수, 프레임 수를 측정 (`:39-44`).
- ㉱ **측정 조건 고정**: `MAX_ITER=120`, `TARGET_ERRORS=25`, `MAX_FRAMES=512`, `BATCH=128`
  (`:29,32`), 시드 `[20260731, n_err]`로 후보 간 동일 채널 실현값 보장 (`:38`).
- ㉲ **출력**: `out/llr_tune.csv`에 (프로파일 × 포인트) FER 행렬 (`:65-71`).

정확히 하면 **선별의 마지막 한 걸음(승자 확정)은 사람이 CSV를 보고 한다.** 스크립트가
자동화한 것은 후보 열거, 동일 조건 실행, FER 표 작성이다. 가설의 "비교·선별"이라는
표현 중 "비교"는 정확하고 "선별"은 사람 판단이 남는다.

## 2단계 — 대체 부재와 미등록 판정

### E9-2. `make_internal_uniform_matrix` 기능 범위

`LDPC_base/llr_matrix.py:209-231` 전문을 읽었다.

- 시그니처: `make_internal_uniform_matrix(cls, num_bits, channel_llr, max_iter, dv_max, mode="HD")`
- 본문: `top_level = 2**(num_bits-1) - 1` 계산 → `th = list(range(top_level, 0, -1))`
  → `edge_mag = uniform_edge_mag(top_level)` → `rows = [(values, -1, 1, max_iter, -1)]`
  → `cls(...)` 반환.
- 반복문 0개, 조건 분기 0개, FER 측정 0개, 파일 비교 0개.
- 반환값: `LLRMatrix` 인스턴스 **1개**.

호출부 `run.py:294-304`도 한 번 호출해 `save()` 후 `load()`할 뿐이다. `run.py` 전체에서
LLR matrix를 여러 개 순회하는 코드는 없다 (`grep -n "llr_matrix\|LLRMatrix" run.py` 전수 확인).

### E9-3. 기능 대조표

| 기능 항목 | `examples/llr_tune.py` (삭제) | `make_internal_uniform_matrix` + 현행 `run.py` | 판정 |
|-----------|-------------------------------|-----------------------------------------------|------|
| LLR 파라미터 후보를 **여러 개** 다루기 | ✓ `glob(llr/*.txt)` 자동 열거 (`:57`) | ✗ 한 번 호출 = 매트릭스 1개 (`llr_matrix.py:228-231`), config의 `llr_matrix`도 파일 1개 (`run.py:290-304`) | **대체 없음** |
| 후보별 FER 측정 | ✓ `run_fer_point`를 후보 × 포인트로 반복 (`:39-41`) | △ `run_fer_point`는 존속(`LDPC_base/sim.py`)하나, 매트릭스 축 반복은 호출자가 없음 | **대체 없음** (엔진만 존속) |
| 기준선 대비 비교 | ✓ 6-bit 선형 기준선 행을 함께 측정 (`:53-55`) | ✗ 기준선 개념 없음 | **대체 없음** |
| 후보 간 동일 채널 실현값 고정 | ✓ 시드 `[20260731, n_err]` 재생성 (`:38`) | △ `seed`는 `[seed, 채널 인덱스, 포인트]`로 파생(`README.md:73-74`)되어 실행 간 재현은 되나, 한 실행 안에서 후보를 나란히 놓지 않음 | **대체 없음** |
| 결과 표 산출 | ✓ `out/llr_tune.csv` (프로파일 × 포인트) (`:65-71`) | ✗ FER CSV는 (채널 × 포인트) 축뿐. 매트릭스 축이 없음 | **대체 없음** |
| 에러 비트 수 스윕 | ✓ `POINTS=[300,340,360,380]` (`:31`) | ✓ config `channels[].points` (`config.json:62`) | **대체 있음** |
| 디코딩 실행 엔진 | ✓ `MinSumDecoder` + `run_fer_point` | ✓ 동일 (`LDPC_base/decoder.py`, `sim.py`) | **대체 있음** |

**요약: 파라미터 축(여러 후보를 나란히 놓고 FER로 견주는 축)이 통째로 사라졌다.**
남은 것은 포인트 축(에러 비트 수)과 채널 축뿐이다.

### E9-4. false positive 반증 — 대체가 저장소 어딘가에 있는가

폭넓게 찾았다.

| 후보 | 확인 내용 | 대체인가 |
|------|-----------|----------|
| `LDPC_base/run.py` 스윕 | `channels[].points`는 **채널 조건** 축이다. LLR matrix는 실행당 1개 (`run.py:290-304`) | ✗ |
| `tools/H_mat_gen/select_irregular.py` | docstring `:1,7-8`: `Irregular QC-LDPC 후보 다중 생성 → FER 기준 선별` / `후보 SEEDS개 생성 → 스크리닝 포인트에서 전수 비교 → 상위 2개를 딥 포인트에서 재측정 → 승자 저장`. **후보 축이 H-matrix이지 LLR 파라미터가 아니다.** 게다가 `:12-14`가 `현재 실행 불가`를 명시하고 `_pm/TODO.md:22-24`에 손질 항목으로 등록돼 있다 | ✗ |
| `Ideas/` 등록 구조 | `registry.py` + `vanilla/`는 **디코더 알고리즘** 교체 구조다. LLR 파라미터 탐색과 축이 다르다 | ✗ |
| `Sim_Output/` 비교 스크립트 | `Sim_Output` 하위는 실행 산출물(config 사본, CSV, PNG)뿐이며 비교 스크립트는 0건 | ✗ |
| 외부 DAO | `README.md:153-158`이 `DAO(decoder auto optimizer)의 LLR_MATRIX 텍스트 포맷`을 읽는다고 하고, `llr_matrix.py:26`이 `DAO가 이 동작 기준으로 최적화하므로`라고 적는다. **LLR 파라미터 최적화의 주체가 외부 도구 DAO로 옮겨간 것으로 읽힌다** | △ 저장소 밖. 이 저장소 안에는 없음 |
| `_pm/TODO.md:19-21` | `LLR matrix 최적화 시 dv range 상한 고려 ... 를 최적화 탐색 범위에 반영` — "최적화 탐색"이라는 절차의 존재를 전제한다 | △ 절차의 소재를 밝히지 않음 |

**판정: "이 저장소 안에 대체가 없다"는 확인됨.** 다만 DAO 이관 정황이 있어
"기능이 유실됐다"보다 "탐색 주체가 외부 도구로 옮겨졌으나 그 사실이 문서화되지 않았다"가
더 정확한 서술일 수 있다. 이 갈래는 사용자 확인이 필요하다.

### E9-5. TODO 등록 여부

`2_LDPC_light/_pm/TODO.md` **전문(49행)**을 작업 트리 기준으로 읽었다.
`git diff -- 2_LDPC_light/_pm/TODO.md` 결과 미커밋 변경은 ㉮ "Claude 마지막 확인" 시각
㉯ "딥 리뷰" 항목 3줄 추가뿐이며, 커밋본과 실질 차이가 없다.

- 작업 목록 12개 항목 전수 확인: `llr_tune`, "탐색", "프로파일 비교"에 해당하는 항목 **0건**.
- 가장 가까운 항목은 `:19-21` `LLR matrix 최적화 시 dv range 상한 고려`이나, 이는
  **최적화 탐색 범위에 넣을 제약**을 다루며 탐색 절차 자체의 소재나 유실은 말하지 않는다.
- "새 작업 추가" 섹션 `:39-41`: `(비어 있음)`.
- 루트 `_pm/TODO.md` 전문도 확인: 항목 2개(원본 알고리즘 요약 문서, Project 3 폴더 신설)뿐,
  관련 항목 0건.

**판정: 미등록 확인됨.**

### E9-6. 삭제 커밋 메시지와 DONE.md의 기록 수준

커밋 `6fb35cf` 메시지 전문:

```
chore: 구 예시 스크립트와 LLR 프로파일 삭제 (사용자 정리)

- examples/ 구 실행 스크립트와 예시 부호, llr/ 구 프로파일 제거
- LDPC_base 개정본(_test/20260806_setup_구성_실험)이 대체, 복구는 git 이력으로 가능
```

`_pm/DONE.md:53`:

```
53	  - ㉮ 구 본체 삭제 — channel, decoder, encoder, pcm, run, sim, mpi_runner(재설계 예정), examples
```

두 기록 모두 **`examples/` 폴더 삭제라는 사실은 남겼다.** 그러나 `llr_tune.py`라는 이름도,
LLR 파라미터 탐색 기능이 사라진다는 사실도 적지 않았다. 오히려 커밋 메시지는
`LDPC_base 개정본이 대체`라고 적어 대체가 있는 것처럼 읽히는데, E9-3 대조표대로
LDPC_base에는 파라미터 탐색 축이 없다.

**판정: 삭제 사실은 기록됨, 기능 유실은 미기록.** "미등록"이 다소 완화되나 뒤집히지 않는다.

## H9 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E9-1 | 삭제 커밋과 75줄, 기능 범위 | **확인됨** | `git log --diff-filter=D` → `6fb35cf`, `--stat` 75줄, `git show`로 전문 열람 (`wc -l` 75). 후보 glob `:57`, 기준선 `:53-55`, 포인트 `:31`, CSV `:65-71` |
| E9-1b | "선별"까지 자동인가 | **부분 반박됨** | 스크립트는 FER 표까지 산출(`:65-71`). 승자 확정은 사람 판단 |
| E9-2 | `make_internal_uniform_matrix` 범위 | **확인됨 (생성 1회)** | `llr_matrix.py:209-231` — 반복·비교·FER 측정 0개, 반환 `LLRMatrix` 1개 |
| E9-3 | 기능 대조 | **확인됨 (파라미터 축 유실)** | 위 대조표 5개 항목 대체 없음, 2개 항목 대체 있음 |
| E9-4 | 저장소 내 대체 부재 | **확인됨** | `run.py` 매트릭스 1개, `select_irregular.py`는 H-matrix 축이며 실행 불가, `Ideas/`는 디코더 축, `Sim_Output/`은 산출물뿐 |
| E9-4b | 외부 DAO 이관 정황 | **미확인 (저장소 밖)** | `README.md:153-158`, `llr_matrix.py:26`. 저장소 안에서 검증 불가 |
| E9-5 | TODO 미등록 | **확인됨** | `2_LDPC_light/_pm/TODO.md` 전문 49행, 루트 `_pm/TODO.md` 전문. 관련 항목 0건, "새 작업 추가" 비어 있음 |
| E9-6 | 커밋·DONE.md 기록 수준 | **확인됨 (삭제만 기록)** | 커밋 `6fb35cf` 메시지, `_pm/DONE.md:53` |

## H9 최종 판정: **확인됨**

- 삭제 사실, 75줄, 기능 범위, 균일 양자화 모드의 기능 범위, 저장소 내 대체 부재,
  TODO 미등록이 모두 독립 재확인됐다.
- 표현 수정 2건을 권한다.
  - ㉮ "비교·선별" → "**동일 조건 비교와 FER 표 산출**" (승자 확정은 사람 판단이었다).
  - ㉯ "대체 없이 사라졌다" → "**이 저장소 안에 대체가 없다**"
    (외부 DAO 이관 정황이 있으므로).
- HIGH 유지가 타당하다. 다만 처방은 "복구"가 아니라 **결정 요청**이어야 한다.
  LLR 파라미터 탐색을 ㉮ 저장소 안에 새 구조(`LDPC_base.run` 기준)로 되살릴지
  ㉯ 외부 DAO 소관으로 못 박고 README에 명시할지를 사용자가 정해야 하며,
  어느 쪽이든 `_pm/TODO.md`에 항목이 서야 한다. 등록 자리는
  `_pm/TODO.md:19-21`의 "LLR matrix 최적화" 항목 아래가 자연스럽다.

---

# 부수 발견 (검증 과정에서 확인된 것)

| # | 내용 | 근거 |
|---|------|------|
| 1 | `plan.md:22` (§1 #5)가 "speed_opt 2-9 텍스트 파일 포맷을 그대로 로드"라고 하나, 현행은 DAO LLR_MATRIX 포맷 전용이다. 머리 단서가 "계속 유효"라고 보증한 §1 안의 오류다 | `plan.md:22` 대 `llr_matrix.py:9-13`, `README.md:15` |
| 2 | 원본 HW CH_HD 실값 `{21,14,12,10}`은 `llr_tables.py:7` 주석과 git 이력(`git show 6fb35cf^:2_LDPC_light/llr/_hw_orig_ch.txt`)에만 남아 있다. `llr_tables.py`를 삭제하면 주석 사본도 사라진다 | `llr_tables.py:7`, 커밋 `6fb35cf` |
| 3 | 저장소에 `llr_tables.py`가 두 갈래로 존재했다 (본체 `2_LDPC_light/llr_tables.py`, `_test/.../LDPC_base/llr_tables.py`). 이름 충돌이 TD-8 오판의 직접 원인이다 | `git ls-files`, `_pm/done/20260807_리뷰후속수정/20260807_리뷰후속수정.md:85` |

---

# 저장소 오염 점검

```
$ git status --short
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

시작 시점 정상 상태 3줄과 동일하다. 실행 산출물과 복구한 `llr_tune.py`는 전부
scratchpad에 두었다.

## 검증에 쓴 명령과 열람 파일

- git: `git ls-files`, `git log --all --oneline -- <path>`, `git log --diff-filter=D -- <path>`,
  `git show --stat 6fb35cf`, `git show 6fb35cf^:2_LDPC_light/examples/llr_tune.py`,
  `git diff -- 2_LDPC_light/_pm/TODO.md`, `git status --short`
- 실행: scratchpad config 사본에 `decoder.max_iter=120`을 넣고 `LDPC_base.run.load_config()` 호출
- 전문 열람: `docs/plan.md`(132행), `_pm/DONE.md`(173행), `_pm/TODO.md`(49행),
  루트 `_pm/TODO.md`, `LDPC_base/llr_matrix.py`(318행), `2_LDPC_light/llr_tables.py`(74행),
  복구한 `examples/llr_tune.py`(75행), `config.json`(91행), `Input/LLR/LLR_MATRIX_HD_1.txt`
- 부분 열람: `LDPC_base/run.py:140-239, 283-306`, `LDPC_base/decoder.py:105-125, 190-230`,
  `README.md:55-104, 150-168`, `tools/H_mat_gen/select_irregular.py:1-30`,
  `_pm/done/20260807_리뷰후속수정/20260807_리뷰후속수정.md:78-90`
- 전수 grep: `llr_tables|llr_profile|LLRProfile|load_profile|ch_mag_by_col|dv_group`,
  `two_set|column_wise|schedule`, `llr_tune`, `tune|sweep|candidate|후보|스윕|튜닝|비교`
