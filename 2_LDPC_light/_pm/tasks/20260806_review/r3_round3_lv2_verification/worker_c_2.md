# worker_c_2 — 자산 소실 경로 검증 + 반영 순서 처방 검증 (F7)

검증 대상: Round 2 발견 F7 — "구 포맷 .qc 2개 로드 불가, `irregular_17x144_z256.qc`는 재생성
경로도 죽어 **자산 소실**" + 처방 "반영 전 .qc 2개를 Ref-C로 변환 (최우선), 이후 순서:
llr_profile 결정 → plan.md 기록 → max_iter 확정 → 코드 이동 → examples 갱신 → 문서 →
Sim_Output 정리".

실증 환경: 스크래치패드 사본 (`scratchpad/w2/`). 프로젝트 파일은 읽기만 했다.

---

## 판정 요약

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| H1 포맷 불일치 실재 | **확인됨** | 개정본 `pcm.load`가 두 파일 모두 `ValueError` |
| H2 irregular 재생성 불가 = 자산 소실 | **반박됨** | git 추적 중 + `seed=103`으로 완전 동일 재생성 성공 |
| H3 tools/ 3파일 무사 | **확인됨** | 본체 `save()`가 이미 Ref-C 출력, 개정본 pcm 위에서 tools/ 그대로 동작 |
| H4 처방 순서 타당성 | **수정 필요** | 역방향 위험 없음(덮어쓰기 안전), "최우선" 근거 없음, **빠진 위험 4건** |

처방 총평: **수정 필요**. 변환 자체는 옳지만 (㉮) 근거로 든 "자산 소실"이 사실이 아니고,
(㉯) "최우선" 배치의 근거가 없으며, (㉰) 정작 진짜 자산 소실을 일으키는 `.gitignore` 충돌과
`dv=10` 미매칭이 처방에서 빠졌다.

---

## H1. 포맷 불일치가 실재하는가 → **확인됨**

### 증거 1: 두 .qc 파일의 실제 헤더

`2_LDPC_light/examples/example_18x147_z256.qc:1-2`

```
# QC-LDPC base matrix (-1 = zero block)
18 147 256
```

`2_LDPC_light/examples/irregular_17x144_z256.qc:1-2`

```
# QC-LDPC base matrix (-1 = zero block)
17 144 256
```

둘 다 구 포맷(`#` 주석 + `M_b N_b z` 정수 3개)이다.

대조 — 개정본 `_test/20260806_setup_구성_실험/Input/H_matrix/example_18x147_z256.qc:1-3`

```
147 18
4 31
256
```

Ref-C 포맷(`N_b M_b` / `J K` / `z`)이다.

### 증거 2: 파서 규칙 대조

| 항목 | 본체 `2_LDPC_light/pcm.py` | 개정본 `LDPC_base/pcm.py` |
|------|---------------------------|--------------------------|
| `save()` | 45-52행 — **Ref-C 출력** | 46-52행 — Ref-C 출력 (본체와 동일 구현) |
| `load()` 주석 제거 | 57행 `ln.split("#", 1)[0].strip()` — **`#` 제거함** | 58행 `ln.strip()` — **`#` 제거 안 함** |
| Ref-C 분기 | 60-64행 (`len(head)==2`) | 63-66행 (분기 없이 전제) |
| 구 포맷 분기 | 65-68행 (`len(head)==3`) | **없음** — 60-62행에서 `ValueError` |

즉 불일치의 실체는 두 겹이다. ㉮ 개정본은 `#` 주석 줄을 제거하지 않아 주석이 첫 줄로 들어오고,
㉯ 헤더 정수 3개 분기가 삭제되었다. 어느 한쪽만 고쳐도 통과하지 못한다.

### 증거 3: 실행 출력 (`scratchpad/w2/t_h1.py`)

```
[OK]   BODY   .load(example_18x147_z256.qc) -> M_b=18 N_b=147 z=256 E=553
[FAIL] REVISED .load(example_18x147_z256.qc) -> ValueError: ...: Ref-C 헤더가 아님
       (첫 줄 '# QC-LDPC base matrix (-1 = zero block)' — 'N_b M_b' 정수 2개여야 함)
[OK]   BODY   .load(irregular_17x144_z256.qc) -> M_b=17 N_b=144 z=256 E=664
[FAIL] REVISED .load(irregular_17x144_z256.qc) -> ValueError: ...: Ref-C 헤더가 아님
       (첫 줄 '# QC-LDPC base matrix (-1 = zero block)' — 'N_b M_b' 정수 2개여야 함)
[OK]   BODY   .load(refc_example_18x147_z256.qc) -> M_b=18 N_b=147 z=256 E=553
[OK]   REVISED .load(refc_example_18x147_z256.qc) -> M_b=18 N_b=147 z=256 E=553
```

**판정: 확인됨.** Round 2(V6)의 F7 전제 중 "포맷 불일치" 부분은 정확하다.

부수 확인: 개정본 `Input/H_matrix/example_18x147_z256.qc`는 본체 `examples/`판과 **base 배열이
완전 동일**하다 (`base 배열 완전 동일: True`, `E: 553 vs 553`). 즉 이 파일은 이미 변환이 끝나
있으며, 내용 변경 없이 헤더만 바뀐 것이다.

---

## H2. `irregular_17x144_z256.qc`가 정말 재생성 불가인가 → **반박됨**

### 증거 1: 두 파일 모두 git 추적 중 (복원 가능)

```
$ git ls-files | grep -i "\.qc$"
2_LDPC_light/examples/example_18x147_z256.qc
2_LDPC_light/examples/irregular_17x144_z256.qc

$ git log --all --oneline -- "**/irregular_17x144_z256.qc"
a9f85f4 refactor: 하위 프로젝트 폴더명을 번호 접두 형식으로 변경
fe49c74 feat: 프로젝트 재구성 초기 커밋 (구 LDPC_2에서 이관)

$ git status --porcelain 2_LDPC_light/examples/
(출력 없음 = clean)

$ git show HEAD:2_LDPC_light/examples/irregular_17x144_z256.qc | head -2
# QC-LDPC base matrix (-1 = zero block)
17 144 256
```

두 파일 모두 커밋되어 있고 워킹 트리가 깨끗하다. 덮어쓰든 지우든 `git checkout` 한 줄로
원본이 돌아온다. **"자산 소실"의 전제 자체가 성립하지 않는다.**

### 증거 2: 생성 경로 전수 수색 결과

`irregular_17x144_z256.qc`를 **쓰는(write)** 곳은 저장소 전체에서 한 곳뿐이다.

- `2_LDPC_light/examples/select_irregular.py:26` — `WINNER_FILE = os.path.join(HERE, "irregular_17x144_z256.qc")`
- `2_LDPC_light/examples/select_irregular.py:106` — `win_code.save(WINNER_FILE)`

소비처(읽는 곳)는 두 곳이다.

- `2_LDPC_light/examples/fixed_error_sweep.py:20` — `DEFAULT_CODE = os.path.join(HERE, "irregular_17x144_z256.qc")`
- `2_LDPC_light/examples/llr_tune.py:24` — `CODE_FILE = os.path.join(HERE, "irregular_17x144_z256.qc")`

여기까지는 V6의 서술과 같다. 그러나 **행렬을 만드는 부분과 승자를 고르는 부분은 서로 다른
모듈**이며, 개정본이 깨뜨리는 것은 후자뿐이다.

`select_irregular.py`의 import (12-22행):

| import | 개정본에서 | 근거 |
|--------|-----------|------|
| `from ..tools.gen_example_code import build_code` | **무사** | H3 참조 |
| `from ..decoder import MinSumDecoder` | 생존 (API 변경 있음) | — |
| `from .. import channel as chan` → `chan.bsc_llr` (38행) | **파손** | 개정본 `channel.py`에 `bsc_llr` 없음 (`rber_channel`로 대체) |
| `from ..sim import run_fer_point` → `target_errors=` (39행) | **파손** | 개정본 `sim.py:8` `max_frame_errors=`로 개명 |

즉 죽는 것은 **FER 측정 기반 후보 선별 루프**이고, 행렬 생성 자체(`build_code`)는 전혀 건드려지지
않는다. `build_code` → `tools/peg.py`(numpy, collections만 import) → `tools/lifting.py`(numpy만
import) → `pcm.QCCode` 경로에 channel/sim/decoder 의존이 하나도 없다.

### 증거 3: 결정론 확인 + 저장본 재현 성공

`select_irregular.py`의 난수는 전부 고정 시드다.

- `select_irregular.py:30` — `SEEDS = [101, 102, 103, 104, 105, 106]`
- `select_irregular.py:29` — `INFO_DEGREES = [3] * 65 + [4] * 31 + [10] * 31`
- `tools/gen_example_code.py:27` — `rng = np.random.default_rng(seed)` (build_code 내부 유일 난수원)

6개 후보를 전부 재생성해 저장본과 대조한 결과 (`scratchpad/w2/t_h2.py`):

```
  seed 101: E=664, 저장본과 base 완전 일치=False (0.1s)
  seed 102: E=664, 저장본과 base 완전 일치=False (0.1s)
  seed 103: E=664, 저장본과 base 완전 일치=True (0.1s)
  seed 104: E=664, 저장본과 base 완전 일치=False (0.1s)
  seed 105: E=664, 저장본과 base 완전 일치=False (0.1s)
  seed 106: E=664, 저장본과 base 완전 일치=False (0.1s)

=> 저장본을 재현하는 seed: 103

  build_code(seed=103) 2회 결과 동일: True
```

**`build_code(256, 17, 144, [3]*65 + [4]*31 + [10]*31, seed=103)` 한 줄로 저장본이 바이트
수준으로 재현된다.** 전수 대조에 0.6초 걸렸다.

독립 교차 확인 — `2_LDPC_light/examples/out/select_irregular.csv`에 승자가 기록되어 있다.

```
deep,103,0.0099,1.7439e-03,25/14336
deep,102,0.0099,2.4771e-03,26/10496
timing1000,103,0.0099,1.0000e-03,59.5s
```

deep 단계 승자가 seed 103이다. 내 재생성 결과와 일치한다.

`example_18x147_z256.qc`도 마찬가지다.

```
  build_example() 기본 seed=20260730: E=553 (0.1s)
  저장본과 base 완전 일치: True
```

**판정: 반박됨.** ㉮ git에 있어 복원 가능하고, ㉯ 시드가 고정이라 재생성 가능하며, ㉰ 재생성
경로(`build_code`)는 개정본 반영 후에도 죽지 않는다 (H3에서 실증). 세 갈래 모두에서 자산이
살아 있다. F7의 "자산 소실" 서술은 철회되어야 한다.

---

## H3. `tools/` 3파일이 정말 무사한가 → **확인됨**

### 증거 1: import와 사용 API 전수

```
tools/gen_example_code.py:10  import sys
tools/gen_example_code.py:12  import numpy as np
tools/gen_example_code.py:14  from ..pcm import QCCode
tools/gen_example_code.py:15  from .peg import peg_base
tools/gen_example_code.py:16  from .lifting import lift_greedy
tools/peg.py:6                from collections import deque
tools/peg.py:8                import numpy as np
tools/lifting.py:7            import numpy as np
```

`pcm` 외의 프로젝트 모듈 의존이 **없다**. 사용하는 `pcm` API는 `QCCode(base, z)`(44행),
`.save()`(54행), `.summary()`(55행), `.count_cycles4()`(56행) 넷뿐이고, 전부 개정본
`LDPC_base/pcm.py`에 같은 이름, 같은 구현으로 존재한다 (본체 `pcm.py:45,91,109` ↔ 개정본
`pcm.py:46,87,105`).

### 증거 2: 본체 `save()`는 **이미 Ref-C** (핵심)

본체 `2_LDPC_light/pcm.py:46-52`:

```python
def save(self, path):
    """Ref-C 포맷 저장: N_b M_b / J K / z / 빈 줄 / shift 행렬. 주석 없음."""
    J, K = int(self.col_deg.max()), int(self.row_deg.max())
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{self.N_b} {self.M_b}\n{J} {K}\n{self.z}\n\n")
```

개정본 `LDPC_base/pcm.py:47-50`과 **문자 단위로 같다**. 본체 `pcm.py:7-14` docstring이
"파일 포맷: Ref-C ... (사용자 지시 2026-08-03)"이고 14행이 "load()는 구 포맷도 자동 감지해
읽는다 (기존 파일 호환)"이다 — 즉 본체는 이미 2026-08-03에 save를 Ref-C로 바꿨고, 기존
`examples/*.qc` 2개만 구 포맷인 채로 남아 있는 상태다.

### 증거 3: 왕복 실증 (본체 save → 개정본 load)

`scratchpad/w2/t_h1.py` 출력:

```
본체 save(example_18x147_z256.qc) 출력 첫 4줄: ['147 18', '4 31', '256', '']
[OK]   개정본 load(본체 save 출력) -> M_b=18 N_b=147 z=256 E=553 / base 동일=True
본체 save(irregular_17x144_z256.qc) 출력 첫 4줄: ['144 17', '10 40', '256', '']
[OK]   개정본 load(본체 save 출력) -> M_b=17 N_b=144 z=256 E=664 / base 동일=True
```

**두 파일 모두** 본체 save 출력을 개정본이 그대로 읽는다. 따라서 변환은 재생성 없이
`QCCode.load(구파일).save(같은경로)` 두 줄이면 끝난다.

### 증거 4: 개정본 pcm 위에서 tools/ 실행 (반영 후 시나리오 모의)

`scratchpad/w2/t_h3.py` — `pkg/pcm.py`를 개정본 pcm으로 교체한 뒤 tools/ 3파일을 그대로 실행:

```
  사용 중인 pcm 모듈: pkg2.pcm (load docstring: 'Ref-C 포맷 로드: N_b M_b / J K / z / 빈 줄 / shift 행렬.')
  build_example() 성공: QC-LDPC: base 18x147, z=256, N=37632, K=33024, rate=0.8776, E(base)=553  (0.1s)
  save() 첫 3줄: ['147 18', '4 31', '256']
  count_cycles4(): 0
  build_code(seed=103) 성공: E=664 (0.1s)

  [반영 후 재생성 == 기존 저장본]
    example_18x147 : True
    irregular_17x144: True

  개정본 load(regen_example_18x147_z256.qc): OK M_b=18 N_b=147 z=256 E=553
  개정본 load(regen_irregular_17x144_z256.qc): OK M_b=17 N_b=144 z=256 E=664
```

**판정: 확인됨 (그리고 V6가 생각한 것보다 강함).** V6의 "example_18x147은 재생성 가능"은
맞지만, 실제로는 ㉮ 두 파일 다 재생성 가능하고, ㉯ 재생성조차 필요 없이 변환 두 줄이면
되며, ㉰ tools/ 3파일은 개정본 반영 후에도 수정 없이 동작한다.

`tools/`가 개정본의 pcm 외 인터페이스 변화에 걸리는 곳은 없다 (import 목록에 pcm 외
프로젝트 모듈이 없으므로 구조적으로 불가능).

---

## H4. 처방(반영 순서 7단계)의 순서 의존성 검증

### ㉮ 변환 도구가 반영 후에도 동작하는가 → **반쯤 그렇다 (되돌릴 수 있음)**

개정본 `LDPC_base/pcm.py:57-62`에 구 포맷 fallback이 **없다**.

```python
lines = [ln.strip() for ln in f if ln.strip()]      # 58행 — '#' 제거 안 함
head = lines[0].split()
if len(head) != 2:
    raise ValueError(...)                            # 60-62행
```

따라서 본체 `pcm.py`를 개정본으로 갈아엎으면 트리 안에서 구 포맷을 읽을 수단이 사라진다.
다만 **막다른 길은 아니다**.

```
$ git show HEAD:2_LDPC_light/pcm.py | sed -n '53,70p'
    @classmethod
    def load(cls, path):
        """Ref-C 포맷(헤더 첫 줄 정수 2개) / 구 포맷(정수 3개) 자동 감지 로드."""
        ...
        elif len(head) == 3:                     # 구 포맷: M_b N_b z
```

구 `pcm.load`도, 구 `.qc` 원본도 git에서 그대로 꺼낼 수 있다. 게다가 H2/H3에서 보였듯
`build_code(seed=103)` 재생성 경로가 반영 후에도 살아 있다. 즉 **변환을 나중에 해도 복구
가능**하다. "최우선"이라는 강도는 근거보다 과하다. 다만 반영 전에 하면 두 줄로 끝나므로
비용 면에서 앞에 두는 것 자체는 합리적이다.

### ㉯ 역방향 문제 (지금 덮어쓰면 본체가 먼저 깨지는가) → **반박됨. 안 깨진다**

본체 `2_LDPC_light/pcm.py:60-68`은 Ref-C(정수 2개)와 구 포맷(정수 3개)을 **둘 다** 받는다.
실증:

```
======================================================================
H4-b: 본체 pcm.load 가 Ref-C 포맷을 받아들이는가 (덮어쓰기 안전성)
======================================================================
[OK]   본체 load(Ref-C 포맷) -> M_b=18 N_b=147 z=256 / 원본과 base 동일=True
```

또한 `refc_example_18x147_z256.qc`(개정본 Input의 실물)를 본체 pcm으로 읽는 시험도 통과했다
(`[OK] BODY .load(refc_example_18x147_z256.qc) -> M_b=18 N_b=147 z=256 E=553`).

**따라서 지금 .qc를 Ref-C로 덮어써도 본체 `examples/fixed_error_sweep.py`, `llr_tune.py`,
`select_irregular.py`, `tools/`는 전혀 영향받지 않는다.** V6가 우려한 역방향 파손은 없다.

### ㉰ 덮어쓰기 vs 사본 생성 → **덮어쓰기가 맞다**

| 기준 | 덮어쓰기 | 사본(`*_refc.qc`) |
|------|---------|------------------|
| 본체 즉시 파손 | 없음 (㉯ 실증) | 없음 |
| 소비처 경로 수정 | 불필요 | `fixed_error_sweep.py:20`, `llr_tune.py:24`, `select_irregular.py:26`, `fer_curve.json:2` 4곳 수정 필요 |
| 되돌리기 | `git checkout` 한 줄 | — |
| 이후 관리 | 파일 1개 | 파일 2개가 갈라짐 (어느 쪽이 정본인지 모호) |

덮어쓰기는 본체를 깨지 않고, git이 변경을 추적하며, 사본 방식이 요구하는 4개 경로 수정을
없앤다. **덮어쓰기 채택.** 커밋을 분리해 두면(변환만 담은 커밋 1개) 되돌리기도 깨끗하다.

### ㉱ 7단계의 실제 선후 의존

| 쌍 | 처방의 순서 | 실제 의존 | 판정 |
|----|-----------|----------|------|
| .qc 변환 → 나머지 전부 | 최우선 | **없음** (변환은 본체 pcm만 사용, 다른 모듈 무관) | 순서 과잉. 코드 이동 이전이기만 하면 충분 |
| llr_profile 결정 → max_iter 확정 | 선후 | **파생 관계** — `max_iter`는 별도 결정 항목이 아니라 LLR matrix 파일에서 유도된다. `llr_matrix.py:63` `self.max_iter = int(self.row_iter[-1, 1])` (마지막 row의 iter_end) | 단계 아님. llr matrix 파일 확정의 결과로 자동 결정. 별도 단계로 세우면 혼선 |
| plan.md 기록 → max_iter 확정 | 선후 | **없음** (문서 작업) | 순서 불필요 |
| 코드 이동 → examples 갱신 | 선후 | **있음** — F5(`bsc_llr` 등 삭제), F6(`run_fer_point` 인자명) 때문에 examples는 새 API 확정 후에만 고칠 수 있다 | 타당 |
| examples 갱신 → 문서 | 선후 | 약한 의존 (문서가 examples 사용법을 서술) | 타당하나 강제 아님 |
| Sim_Output 정리 | 마지막 | **없음** | 어디든 무방 |

정리하면 **실제로 강제되는 의존은 "코드 이동 → examples 갱신" 하나뿐**이다. 나머지는 순서가
불필요하게 강하게 못박혀 있고, `max_iter 확정`은 아예 독립 단계가 아니다.

### ㉲ 처방에서 빠진 위험 — 4건 (이쪽이 F7 본문보다 중요)

**빠진 위험 1 (치명): `.gitignore`가 개정본 H-matrix 경로를 삼킨다 — 진짜 자산 소실 경로**

`.gitignore:40`에 `H_Matrix/`가 있고, 이 저장소는 `core.ignorecase = true`다.

```
$ git config core.ignorecase
true

$ git check-ignore -v "2_LDPC_light/Input/H_matrix/example_18x147_z256.qc"
.gitignore:40:H_Matrix/	2_LDPC_light/Input/H_matrix/example_18x147_z256.qc
```

**소문자 `Input/H_matrix/`가 `.gitignore`의 `H_Matrix/`에 걸린다.** 개정본 레이아웃
(`config.json:2` `"H_matrix": "Input/H_matrix/example_18x147_z256.qc"`)을 본체로 옮기는 순간,
**지금 git이 추적 중인 .qc 2개가 조용히 미추적 상태가 된다.** 이것이 실제로 자산 소실을
일으킬 수 있는 유일한 경로인데 F7은 이를 언급하지 않는다.

대응: `.gitignore`에 `!2_LDPC_light/Input/` 예외를 넣거나, `H_Matrix/` 패턴을 원래 의도한
경로로 한정(`/H_Matrix/` 등)한다. **반영 전에 처리해야 하는 진짜 최우선 항목은 이것이다.**

**빠진 위험 2 (높음): `irregular_17x144_z256.qc`는 포맷을 변환해도 개정본에서 못 쓴다**

이 부호의 column degree 분포:

```
[irregular_17x144_z256.qc]
  col_deg 히스토그램: {2:16, 3:66, 4:31, 10:31}
```

개정본 LLR matrix(`Input/LLR/LLR_MATRIX_HD_0.txt`, `_1.txt`)의 dv 구간은 **싱글턴 4개**
`dv_from = dv_to = [11, 4, 3, 2]`이고, `llr_matrix.py:143-147`은 미매칭 dv에서 예외를 던진다
(`차이.md:24` — 원본 C++의 조용한 `col_idx=0` fallback을 일부러 재현하지 않기로 한 사용자 결정).

Ref-C 변환 후 개정본 스택에 태운 실측 (`scratchpad/w2/t_h2.py`):

```
[example_18x147_z256.qc] -> conv_example_18x147_z256.qc
  개정본 QCCode.load: OK (M_b=18, N_b=147, z=256)
  col_dv_idx(LLR_MATRIX_HD_0.txt): OK  (dv_from=[11, 4, 3, 2], idx 고유값=[1, 2, 3])
  col_dv_idx(LLR_MATRIX_HD_1.txt): OK  (dv_from=[11, 4, 3, 2], idx 고유값=[1, 2, 3])

[irregular_17x144_z256.qc] -> conv_irregular_17x144_z256.qc
  개정본 QCCode.load: OK (M_b=17, N_b=144, z=256)
  col_dv_idx(LLR_MATRIX_HD_0.txt): FAIL ValueError: LLR_MATRIX_HD_0.txt: dv=10 (col block 96)가
    dv_from/dv_to [11, 4, 3, 2]~[11, 4, 3, 2] 어느 구간에도 없음
  col_dv_idx(LLR_MATRIX_HD_1.txt): FAIL ValueError: (동일)
```

**포맷 변환은 성공하지만 그 다음 단계에서 죽는다.** 처방이 "변환하면 된다"로 끝나면 이
부호는 반영 후 사용 불가 상태로 남는다. 선택지는 셋이다.

- 1. dv=10을 덮는 dv 구간을 가진 LLR matrix 파일을 준비한다 (예: `dv_from=10`)
- 2. `INFO_DEGREES`의 `[10]*31`을 `[11]*31`로 바꿔 `build_code(..., seed=103)`으로 재생성한다 (기존 dv 구간 `11`에 맞음. 단 저장본과 다른 부호가 됨)
- 3. 이 부호를 반영 대상에서 제외하고 `example_18x147`만 가져간다 (소비처 `fixed_error_sweep.py`, `llr_tune.py`도 함께 정리)

어느 쪽이든 **설계 결정(Decision 등급)**이므로 사용자 확인이 필요하다.

**빠진 위험 3 (중간): DV 내림차순 배치 전제 위반**

개정본이 새 전제를 문서화했다.

- `LDPC_base/pcm.py:15` — "column block은 DV 내림차순 배치를 전제로 한다 (예시 부호도 재배열 완료, 2026-08-06 정정)."
- `README.md:26` — "column block은 **DV 내림차순 배치** (예시 부호 재배열 완료)"

실측:

```
[example_18x147_z256.qc]
  DV 내림차순 배치? True
[irregular_17x144_z256.qc]
  DV 내림차순 배치? False
```

`irregular_17x144`의 col_deg는 앞 65개가 3, 그다음 31개가 4, 그다음 31개가 10, 마지막이
패리티부(3, 2×15) 순이다 (`select_irregular.py:29` `INFO_DEGREES = [3]*65 + [4]*31 + [10]*31`
그대로). 내림차순이 아니다.

이 전제를 **강제하는 코드는 개정본 어디에도 없다** (grep 결과 `pcm.py:15` docstring과
`README.md:26` 서술뿐이며, `decoder.py:51-53`의 `dv_group`/`_col_bf`는 column별 계산이라
순서 무관). 따라서 지금은 조용한 규약이고, 위반해도 예외가 안 난다. 그래서 오히려 위험하다.
처방은 ㉮ 전제를 강제(로드 시 검사)할지, ㉯ 문서에서 내릴지, ㉰ irregular를 재배열할지를
정해야 한다.

**빠진 위험 4 (중간): 개정본 전체가 현재 git 미추적**

```
$ git check-ignore -v "2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/pcm.py"
.gitignore:24:_test/	"2_LDPC_light/_test/.../LDPC_base/pcm.py"
```

`.gitignore:24`의 `_test/` 때문에 **새 원본이 될 개정본 코드 전체가 버전 관리 밖에 있다.**
`git clean -xdf` 한 번이면 사라진다. 같은 이유로 `out/`(`.gitignore:11`)도 무시되어
`examples/out/select_irregular.csv`(승자 seed 103 기록)가 미추적이다. 다만 이 CSV가 사라져도
후보 6개 전수 대조로 0.6초 만에 seed를 다시 찾을 수 있으므로 심각도는 낮다.

`__pycache__/`는 `.gitignore` 마지막 줄에 있어 문제 없다. 개정본
`LDPC_base/__pycache__/`에 `.opt-1.pyc`가 남아 있으나 이동 시 그냥 빼면 된다.

---

## 처방 판정 및 수정안

### 판정: **수정 필요**

F7 처방의 뼈대(".qc를 Ref-C로 변환")는 옳지만, ㉮ 근거로 든 "자산 소실"이 사실이 아니고
(H2 반박됨), ㉯ "최우선" 배치의 순서 근거가 없으며 (H4-㉮/㉯), ㉰ 변환만으로 해결되지 않는
문제 2건(dv=10 미매칭, DV 배치)과 진짜 소실 경로 1건(`.gitignore` 충돌)이 빠져 있다.

### 수정안

**F7 본문 수정**

> 구 포맷 .qc 2개는 개정본 `pcm.load`가 거부한다 (`pcm.py:60-62`). 다만 **자산 소실은 아니다** —
> 두 파일 모두 git 추적 중이고(`git ls-files`), `tools/gen_example_code.build_code`로 완전
> 동일하게 재생성된다(`example_18x147`은 `build_example()`, `irregular_17x144`는
> `build_code(256, 17, 144, [3]*65+[4]*31+[10]*31, seed=103)`). 재생성 경로는 pcm 외 의존이
> 없어 반영 후에도 살아남는다. 심각도를 HIGH → **MEDIUM**으로 조정한다.
>
> 별건으로 **`irregular_17x144_z256.qc`는 포맷을 변환해도 개정본에서 동작하지 않는다** —
> dv=10이 LLR matrix의 dv 구간 `[11,4,3,2]`에 없어 `llr_matrix.py:143-147`이 예외를 던진다.
> 이건 새 발견이며 **Decision 등급**이다.

**반영 순서 수정안**

- 1. **`.gitignore` 수정** (신규, 진짜 최우선) — `H_Matrix/`(40행)가 `core.ignorecase=true` 때문에 개정본의 `Input/H_matrix/`를 삼킨다. 예외 규칙을 넣지 않으면 이동 즉시 .qc가 미추적이 된다
- 2. **개정본을 `_test/` 밖으로 옮기거나 우선 커밋** (신규) — `_test/`가 gitignore라 새 원본이 버전 관리 밖에 있다
- 3. **irregular_17x144 처리 방침 결정** (신규, Decision) — dv 구간 확장 / dv=11로 재생성 / 폐기 중 택일. `fixed_error_sweep.py:20`, `llr_tune.py:24` 처리도 함께
- 4. **DV 내림차순 전제 확정** (신규, Decision) — 강제(로드 시 검사) / 문서에서 철회 / 부호 재배열 중 택일
- 5. **.qc 변환** — 본체 pcm으로 `QCCode.load(p).save(p)` **덮어쓰기**. 본체 load가 Ref-C를 받으므로(실증) 본체 examples/tools는 안 깨진다. 커밋 분리 권장
- 6. **LLR matrix 파일 확정** (기존 "llr_profile 결정") — `max_iter`는 여기서 파생되므로 독립 단계에서 제거 (`llr_matrix.py:63`)
- 7. **코드 이동**
- 8. **examples 갱신** (7 이후여야 함 — F5/F6 API 변경 때문. 유일하게 강제되는 순서 의존)
- 9. **plan.md, 문서 갱신, Sim_Output 정리** (순서 무관, 병행 가능)

기존 처방 대비 핵심 차이: **1~4번(전부 신규)이 실제로 반영을 막는 항목**이고, 원 처방이
"최우선"으로 지목한 .qc 변환은 5번으로 내려가도 안전하다.

---

## 부록: 실행 스크립트 위치

스크래치패드 `.../scratchpad/w2/` — `t_h1.py`(포맷·왕복), `t_h2.py`(재생성·dv 매칭),
`t_h3.py`(개정본 pcm 위 tools/ 구동). 프로젝트 파일은 사본만 사용했고 원본은 수정하지 않았다.
