# worker_c_2 — 정적 분석: 패키지 경계, 임포트 체인, 실행 진입점

작성: 2026-08-08 14:28:43 / 팀 C(refactor_exec) 워커 2 / 관점 E(패키지 경계, 임포트) + I(실행 검증)

## 확인 범위

읽은 파일 (전문):
`LDPC_base/run.py`, `LDPC_base/__init__.py`, `LDPC_base/sim.py`, `LDPC_base/encoder.py`,
`LDPC_base/decoder.py`(docstring과 `__init__`), `LDPC_base/channel.py`(모듈 API 부분),
`2_LDPC_light/__init__.py`, `Ideas/__init__.py`, `Ideas/registry.py`,
`Ideas/vanilla/__init__.py`, `Ideas/vanilla/decoder.py`, `Ideas/vanilla/config.json`,
`Ideas/vanilla/README.md`, `tools/__init__.py`, `tools/H_mat_gen/__init__.py`,
`tools/H_mat_gen/gen_example_code.py`, `tools/H_mat_gen/select_irregular.py`,
`tools/H_mat_gen/README.md`, `2_LDPC_light/README.md`(실행 절), `2_LDPC_light/config.json`,
루트 `.gitignore`, `_pm/TODO.md`(해당 항목).

실행 검증 (전부 scratchpad 출력, 저장소 추적 파일 무수정):
- ㉮ `-m` 실행 시 `sys.path[0]` 실측 (`python -m site`)
- ㉯ 실행 루트 4종 비교 (`2_LDPC_light/`, repo 루트, 무관한 cwd, 파일 직접 실행)
- ㉰ 가짜 `Ideas` 트리 3종을 `sys.path` 앞에 놓아 `ImportError` fallback 범위 실증
- ㉱ registry 문자열 7종(콜론 없음, 콜론 2개, 빈 문자열, 없는 속성, 없는 모듈, 빈 모듈명)
- ㉲ 생성자 계약 위반 클래스 2종 등록 후 `setup()` 호출
- ㉳ README 실행 예 `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code` 실제 실행
- ㉴ 가짜 `matplotlib`(import 시 ImportError)로 `report()` 순서 실증
- ㉵ `LDPC_base` 공개 표면과 순환 import 여부 실측

---

## 발견 목록

### C2-1 (MEDIUM) `Ideas` 임포트 실패가 조용한 디코더 대체로 끝난다

**위치**: `LDPC_base/run.py:265-272` (`_resolve_decoder_class`의 `try/except ImportError`)

**근거**: `try` 블록이 감싸는 것은 `importlib.import_module("Ideas.registry")` 한 줄이고,
`except ImportError`는 "패키지 없음"과 "패키지 내부 import 실패"를 구분하지 않는다.
`decoder_type == "vanilla"`면 아무 출력 없이 `MinSumDecoder`를 돌려준다.

scratchpad 가짜 `Ideas` 트리로 실증한 결과 (cwd는 `2_LDPC_light/` 정상):

| 가짜 트리 | 결과 |
|-----------|------|
| `Ideas/__init__.py`에 없는 모듈 import | `LDPC_base.decoder.MinSumDecoder` **조용히 반환** |
| `Ideas/registry.py`에 없는 모듈 import | `LDPC_base.decoder.MinSumDecoder` **조용히 반환** |
| `Ideas/vanilla/decoder.py`에 오타 import | `ImportError` 전파 (정상) |

세 번째 항목은 해당 import가 `try` 밖(`run.py:278`)에 있어 오진하지 않는다.
즉 배정 가설이 지목한 "`Ideas.vanilla.decoder` 내부 실패의 오진"은 **실재하지 않고**,
오진 지점은 한 단계 위인 `Ideas/__init__.py`와 `Ideas/registry.py`다.

같은 fallback이 실행 루트 오류에서도 발동한다. repo 루트에서
`python -m 2_LDPC_light.LDPC_base.run <config>`를 돌리면 `Ideas`(최상위 이름)를 찾지
못해 실험이 **에러 없이 끝까지 완주**하며, 콘솔과 summary.txt에만 차이가 남는다.

```
정상 루트 : decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=20
repo 루트 : decoder: vanilla (2_LDPC_light.LDPC_base.decoder.MinSumDecoder), max_iter=20
```

**영향**: 현재 `VanillaDecoder`는 재정의가 없어 `MinSumDecoder`와 동작이 같으므로
지금 당장 틀린 FER이 나오지는 않는다. 다만 ㉮ 환경 오류가 침묵으로 흡수되고,
㉯ `decoder_type`이 vanilla가 아닐 때 나오는 메시지
(`Ideas 패키지를 찾을 수 없음 (2_LDPC_light/에서 실행했는지 확인)`)가
실제 원인이 registry 내부 import 실패인 경우에도 cwd를 지목해 오진을 유도한다.
`Ideas/vanilla/decoder.py`가 한 줄이라도 재정의를 갖는 순간 HIGH로 올라간다
(같은 config가 두 실행 루트에서 다른 FER을 내고 아무 경고도 없다).

**수리 방향**: `except ImportError` 조건을 "`Ideas` 자체가 없을 때"로 좁히고
(`err.name == "Ideas"` 확인), 대체가 일어나면 콘솔에 한 줄 알린다.

---

### C2-2 (MEDIUM) 실행 루트가 둘로 갈라져 있고 `LDPC_base`가 두 번 로드될 수 있다

**위치**: `Ideas/vanilla/decoder.py:6` (`from LDPC_base.decoder import MinSumDecoder`)
대 `tools/H_mat_gen/gen_example_code.py:15`, `tools/H_mat_gen/select_irregular.py:23-25`
(`from ...LDPC_base... import ...`)

**근거**: 저장소는 서로 배타적인 두 실행 루트를 동시에 요구한다.

| 루트 | 성립 | 불성립 |
|------|------|--------|
| `2_LDPC_light/` (flat) | `import LDPC_base.run` OK, `import Ideas.registry` OK | `import tools.H_mat_gen.gen_example_code` → `ImportError: attempted relative import beyond top-level package` |
| repo 루트 (package) | `2_LDPC_light.tools.H_mat_gen.*` OK, `2_LDPC_light.LDPC_base.run` OK | `Ideas` 최상위 이름 없음 → C2-1의 조용한 대체 |

두 루트가 겹치면 같은 코드가 두 개의 모듈 객체로 로드된다. repo 루트 + `PYTHONPATH=2_LDPC_light`
조합을 실측한 결과:

```
resolved                : Ideas.vanilla.decoder.VanillaDecoder
VanillaDecoder의 부모   : LDPC_base.decoder.MinSumDecoder
run.py가 쓰는 MinSumDecoder: 2_LDPC_light.LDPC_base.decoder.MinSumDecoder
같은 클래스 객체인가?   : False
로드된 decoder 모듈     : ['2_LDPC_light.LDPC_base.decoder', 'LDPC_base.decoder']
```

**영향**: 지금은 `run.py`와 `sim.py` 어디에도 `isinstance`/`issubclass` 검사가 없어
그대로 완주한다 (`sim.run_fer_point`의 `decoder: MinSumDecoder`는 주석 성격의 어노테이션일 뿐
강제되지 않는다). 그래서 오늘의 증상은 모듈 이중 적재로 인한 메모리 낭비와
`_experiment_summary_lines`가 찍는 모듈 경로 혼선에 그친다. 앞으로 타입 검사나
모듈 수준 상태(캐시, 전역 테이블)가 하나라도 들어오면 곧바로 깨진다.

**수리 방향**: 루트를 하나로 정하는 것이 근본 해법이다. `2_LDPC_light/`를 유일한 루트로
삼으려면 `tools/H_mat_gen/*`의 3단계 상대 import를 `from LDPC_base.pcm import QCCode`로
바꾸고 README 실행 예를 `python -m tools.H_mat_gen.gen_example_code`로 맞추면 된다.

---

### C2-3 (MEDIUM) matplotlib이 없으면 완주한 실험의 summary.txt가 통째로 사라진다

**위치**: `LDPC_base/run.py:496`(`_plot_fer_curves`의 지역 `import matplotlib`),
`run.py:561-566`(그림 저장이 summary.txt 쓰기보다 앞)

**근거**: `report()`의 실행 순서는 ㉮ 실행 폴더 생성, ㉯ config 사본, ㉰ FER CSV,
㉱ 로그 CSV, ㉲ **FER 커브 그림**, ㉳ **summary.txt** 이다. 가짜 `matplotlib`(import 시
ImportError)로 재현한 결과 exit code 1로 죽고 폴더에 남은 것은 다음뿐이다.

```
config.json
fer_fixed_error.csv
log_fail_fixed_error_p300.csv
log_iter_fixed_error_p300.csv
log_iter_hist_fixed_error_p300.csv
(summary.txt 없음)
```

`2_LDPC_light/config.json`과 `Ideas/vanilla/config.json` 둘 다 `fer_curve_png: true`가
기본값이고, 저장소에 `requirements.txt`, `pyproject.toml`, `setup.py`가 없어 의존성 선언도
없다 (README와 plan.md에도 matplotlib 언급 없음).

**영향**: 외부에서 pull해 성능을 확인하는 것이 이 프로젝트의 목표인데
(루트 CLAUDE.md 프로젝트 간 흐름 ㉰), 새 환경에 matplotlib이 없으면 몇 시간짜리 측정이
끝난 직후 실험 요약(부호 정보, LLR matrix 정보, 디코더 정보, git 커밋 해시, 포인트별 결과)이
기록되지 않고 프로세스가 죽는다. FER 수치 자체는 CSV로 남으므로 비가역 손실은 아니지만
재현성 정보(커밋 해시)는 복구가 번거롭다. `save_csv`의 `import csv`는 표준 라이브러리라
같은 위험이 없다.

**수리 방향**: summary.txt 쓰기를 그림 저장보다 앞에 두거나, 그림 저장 실패를 잡아
경고 한 줄로 낮춘다. 함께 `requirements.txt`에 numpy와 matplotlib을 명시한다.

---

### C2-4 (LOW) registry 문자열 형식 오류의 예외 메시지가 원인을 지목하지 못한다

**위치**: `LDPC_base/run.py:277` (`registry.DECODERS[decoder_type].split(":")`)

**근거**: 7종 실측 결과.

| registry 값 | 나오는 예외 |
|-------------|-------------|
| `Ideas.vanilla.decoder:VanillaDecoder` | 정상 |
| 콜론 없음 | `ValueError: not enough values to unpack (expected 2, got 1)` |
| `C:\Ideas\vanilla\decoder:VanillaDecoder` (Windows 경로 혼입) | `ValueError: too many values to unpack (expected 2)` |
| 빈 문자열 | `ValueError: not enough values to unpack (expected 2, got 1)` |
| `Ideas.vanilla.decoder:NoSuchClass` | `AttributeError: module 'Ideas.vanilla.decoder' has no attribute 'NoSuchClass'` |
| `Ideas.nope.decoder:VanillaDecoder` | `ModuleNotFoundError: No module named 'Ideas.nope'` |
| `:VanillaDecoder` | `ValueError: Empty module name` |

앞의 세 줄은 `decoder.type`도, registry 항목 값도, 기대 형식도 알려주지 않는다.
`ModuleNotFoundError`는 `ImportError`의 자식이지만 이 호출이 `try` 밖이라 삼켜지지 않는다
(C2-1 표 세 번째 줄과 같은 이유).

**영향**: 새 아이디어를 등록하다 형식을 틀렸을 때 registry를 의심하기까지 시간이 걸린다.
드라이브 문자가 섞이면(`C:\...`) 세 조각으로 갈라져 더 헷갈린다.

**수리 방향**: `rsplit(":", 1)`로 나누고 조각이 2개가 아니면
`"Ideas/registry.py의 {type} 값 {값!r} — \"모듈경로:클래스명\" 형식이어야 함"`처럼
직접 던진다.

---

### C2-5 (LOW) 등록 클래스의 생성자 계약이 문서에 명시되어 있지 않다

**위치**: `LDPC_base/run.py:306` (`decoder_class(code, llr_matrix=llr_matrix)`),
`Ideas/registry.py:3-8` (추가 절차), `Ideas/vanilla/README.md:19-30`

**근거**: `MinSumDecoder.__init__(self, code, llr_matrix)`를 그대로 상속하는 것이
registry 등록 클래스 전부의 전제인데, 추가 절차 문서는 "교체용 함수만 재정의"라고만
적고 생성자를 건드리지 말라고는 말하지 않는다. `_resolve_decoder_class`는 반환값이
클래스인지, `MinSumDecoder`의 자식인지 확인하지 않는다.

시그니처가 다른 클래스를 등록하면 `setup()`에서 다음처럼 멈춘다 (실측).

```
__init__(self, code, llr_matrix, beta) : TypeError: NeedsExtraArg.__init__() missing 1 required positional argument: 'beta'
__init__(self, code)                   : TypeError: TakesOnlyCode.__init__() got an unexpected keyword argument 'llr_matrix'
```

클래스 이름이 메시지에 나오므로 진단 자체는 가능하다. 다만 `MinSumDecoder`를 상속하지
않은 클래스는 `setup()`을 통과한 뒤 `main()`의 `_experiment_summary_lines`
(`run.py:321`의 `decoder.llr_matrix`, `run.py:323`의 `decoder.max_iter`)에서
`AttributeError`로 늦게 터진다.

**영향**: 아이디어 디코더는 하이퍼파라미터(offset β, damping 계수 등)를 갖기 마련인데
JSON에서 아이디어별 파라미터를 넘길 통로가 없어 생성자를 고치고 싶어지는 압력이 있다.
계약이 문서에 없으면 그 시점에 깨진다.

**수리 방향**: registry docstring에 "생성자는 `(code, llr_matrix)`를 유지한다"를 한 줄
추가하고, `_resolve_decoder_class` 반환 직전에 `issubclass(klass, MinSumDecoder)`를 확인한다.

---

### C2-6 (LOW) `Ideas/vanilla/README.md`가 존재하지 않는 실행 루트를 안내한다

**위치**: `Ideas/vanilla/README.md:13`, `tools/H_mat_gen/README.md:16-17`

**근거**: 두 문서 모두 실행 루트를 `_test/20260806_setup_구성_실험/`으로 적고 있다.
`_test/`는 루트 `.gitignore`에 등록되어 있어 저장소를 pull한 사람에게는 없는 경로다.
같은 명령의 올바른 루트는 `2_LDPC_light/`이며 `2_LDPC_light/README.md:23`은 맞게 적고 있다.

**영향**: `Ideas/vanilla/README.md`는 새 아이디어를 추가할 때 템플릿으로 읽는 문서라
잘못된 루트가 그대로 복제된다.

---

### C2-7 (LOW) `select_irregular.py`는 실행 중반에 구 API로 멈춘다 (TODO와 정합)

**위치**: `tools/H_mat_gen/select_irregular.py:39, 42-44`

**근거**: import 자체는 성립한다 (repo 루트에서
`2_LDPC_light.tools.H_mat_gen.select_irregular` 임포트 성공). 실패는 실행 중에 난다.

| 줄 | 구 API 호출 | 현재 시그니처 | 결과 |
|----|-------------|---------------|------|
| 39 | `MinSumDecoder(code, max_iter=MAX_ITER)` | `__init__(self, code, llr_matrix)` | `TypeError: unexpected keyword argument 'max_iter'` |
| 42 | `chan.bsc_llr(...)` | `channel.py`에 `bsc_llr` 없음 | `AttributeError` |
| 43-44 | `run_fer_point(..., target_errors=, batch=)` | `max_frame_errors=, frames_per_batch=` | `TypeError: unexpected keyword argument 'target_errors'` |

`main()`은 1단계 후보 생성 6개(개당 0.4초 수준)를 마친 뒤 2단계 첫 `fer_at` 호출에서
39행 `TypeError`로 죽는다. 그 전에 `out/` 폴더만 만들고 파일은 쓰지 않으므로 부작용은 없다
(`out/`은 gitignore 대상).

`_pm/TODO.md:22-23`에 "`tools/H_mat_gen/select_irregular.py`를 새 구조로 손질,
현재 실행 불가"가 미완으로 등록되어 있어 상태와 TODO는 정합한다.

**참고**: 파일 docstring 12-14행의 "주의 (2026-08-07): ... **현재 실행 불가** ...
import만 LDPC_base로 돌려놓은 상태다"는 CLAUDE.md 문장 작성 규칙 ㉮(과거와 현재를 대비하는
서술을 코드에 남기지 않는다)에 걸린다. 문서 담당 팀(D)이 다룰 항목으로 남긴다.

---

### C2-8 (LOW) `2_LDPC_light/llr_tables.py`가 참조되지 않는 채로 추적되고 있다

**위치**: `2_LDPC_light/llr_tables.py` (git 추적 중)

**근거**: 저장소 전체 grep에서 이 모듈을 import하는 `.py`가 없다. docstring은
`2_LDPC_light/llr/*.txt`에서 로드한다고 적고 있으나 그런 폴더가 없고, 역할은
`LDPC_base/llr_matrix.py`의 `LLRMatrix`(DAO LLR_MATRIX 포맷)로 대체되어 있다.
`2_LDPC_light/README.md:12`의 구성 표에도 이 파일이 없다.

**영향**: 패키지 루트에 놓여 `2_LDPC_light.llr_tables`로 import 가능한 상태라,
LLR 파라미터의 정본이 둘인 것처럼 읽힌다.

---

### C2-9 (LOW) 잘못된 위치에서 실행했을 때의 에러가 조치를 안내하지 않는다

**위치**: 실행 진입점 전반 (`LDPC_base/run.py:571-585`)

**근거**: 실행 위치별 실측.

| 실행 | 결과 |
|------|------|
| `2_LDPC_light/`에서 `python -m LDPC_base.run config.json` | 정상 |
| 무관한 cwd에서 `python -m LDPC_base.run ...` | `Error while finding module specification for 'LDPC_base.run' (ModuleNotFoundError: No module named 'LDPC_base')` |
| `python LDPC_base/run.py config.json` (파일 직접 실행) | `ImportError: attempted relative import with no known parent package` |
| repo 루트에서 `python -m 2_LDPC_light.LDPC_base.run ...` | **성공하되 디코더가 조용히 바뀜** (C2-1) |

2행과 3행은 Python 표준 메시지라 원인은 드러나지만 "`2_LDPC_light/`로 이동하라"는
조치는 담기지 않는다. 4행이 실질적 위험이며 C2-1에서 다룬다. 인자 없이 실행하면
`usage: python -m LDPC_base.run <config.json>`가 나오는데, repo 루트에서 실행한
경우에도 같은 문구라 실제로 친 명령과 다르다.

---

## 확인했으나 문제 없던 항목

- ㉮ **`-m` 실행이 cwd를 sys.path에 넣는 근거**: `2_LDPC_light/`에서 `python -m site`로
  실측한 `sys.path[0]`은 `D:\OneDrive\My_Projects\LDPC_dev\2_LDPC_light`(cwd 절대경로)다.
  이 덕분에 `LDPC_base`와 `Ideas`가 최상위 이름으로 잡힌다. `python -c`의 `sys.path[0]`은
  `''`이며, 스크립트 파일 실행은 스크립트 폴더가 들어가 cwd가 들어가지 않는다.
- ㉯ **미등록 `decoder.type`의 에러 메시지**: 등록 가능한 목록을 그대로 알려준다.
  `ValueError: decoder.type='offset_min_sum' — Ideas/registry.py 미등록 (등록된 이름: ['vanilla'])`
  (`run.py:273-276`). 적절하다.
- ㉰ **3단계 상대 import 성립 조건**: `2_LDPC_light/__init__.py`, `tools/__init__.py`,
  `tools/H_mat_gen/__init__.py` 세 파일이 모두 실재한다 (뒤 둘은 빈 파일, 셋 다 git 추적 중).
  `from ...LDPC_base.pcm import QCCode`는 `2_LDPC_light.tools.H_mat_gen` 기준 3단계 상승으로
  `2_LDPC_light.LDPC_base.pcm`을 정확히 가리킨다.
- ㉱ **숫자로 시작하는 패키지명의 `-m` 실행**: README 실행 예를 그대로 돌려 정상 동작을 확인했다.
  `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code <scratchpad 경로>` → 0.4초에
  `example_18x147_z256.qc` 생성, `lifted 4-cycles: 0`. `2_LDPC_light`는 파이썬 식별자로는
  쓸 수 없지만 runpy와 importlib은 문자열로 다루므로 제약이 없다.
  인자를 생략했을 때의 기본 출력 위치는 `tools/H_mat_gen/out/`이며 루트 `.gitignore`의
  `out/` 규칙이 덮는다.
- ㉲ **config 상대경로의 기준점**: `run.py:164`의 `base_dir = os.path.dirname(os.path.abspath(path))`가
  기준이며 cwd가 아니라 **config 파일 위치**로 풀린다. `_path_pair`(`run.py:118`),
  `output.dir`(`run.py:225-227`), 생성 LLR matrix 경로(`run.py:212-214`) 모두 같은 기준이다.
  `Ideas/vanilla/config.json`을 `2_LDPC_light/`에서 실행했을 때의 실측:

  | 키 | 해석 결과 |
  |----|-----------|
  | `H_matrix` | `2_LDPC_light\Ideas\vanilla\../../Input/H_matrix\example_18x147_z256.qc` |
  | `decoder.llr_matrix` | `2_LDPC_light\Ideas\vanilla\../../Input/LLR\LLR_MATRIX_HD_1.txt` |
  | `output.dir` | `2_LDPC_light\Ideas\vanilla\Sim_Output` |

  결과는 `Ideas/vanilla/Sim_Output/`에 쌓이며, 루트 `.gitignore`의 `Sim_Output/`은 앞에
  슬래시가 없어 모든 깊이에 적용된다. 실제로 그 폴더에 실행 결과 6벌이 있는데도
  `git status`는 깨끗하다. **커버된다.**
- ㉳ **`LDPC_base/__init__.py`에서 `run`을 뺀 이유**: 순환 import가 아니다.
  `import LDPC_base` 뒤에 `import LDPC_base.run`이 문제없이 성립하고, 그때
  `LDPC_base.run.MinSumDecoder is LDPC_base.MinSumDecoder`가 참이다. `run`은 실행 진입점이라
  라이브러리 표면에서 뺀 설계 선택으로 읽힌다.
- ㉴ **`__all__`과 실제 노출의 일치**: `__all__ = ["QCCode", "MinSumDecoder", "channel",
  "encoder", "sim"]`의 다섯 이름이 모두 실재한다. `decoder`, `pcm`은 서브모듈 import의
  부수효과로 접근 가능하지만 `__all__` 밖이라 `from LDPC_base import *`에는 들어가지 않는다.
  다만 `LLRMatrix`는 노출되지 않아 `from LDPC_base import LLRMatrix`가 `ImportError`다.
  `MinSumDecoder`가 `llr_matrix`를 필수 인자로 받는 구조에서 `QCCode`, `MinSumDecoder`와
  나란히 있어야 할 개념이 빠져 있다는 점만 기록해 둔다 (동작 영향 없음).
- ㉵ **`2_LDPC_light/__init__.py`와의 역할 분담**: 상위는 저장소 안내 docstring만 두고
  코드를 import하지 않으며, 하위 `LDPC_base/__init__.py`가 라이브러리 표면을 담당한다.
  역할이 겹치지 않는다.
- ㉶ **정본 경로의 모듈 정체성**: `2_LDPC_light/`에서 실행하면
  `VanillaDecoder.__mro__[1] is LDPC_base.decoder.MinSumDecoder`가 참이고,
  로드된 모듈은 `LDPC_base.*` 한 벌뿐이다. 이중 적재는 C2-2의 조건에서만 생긴다.
- ㉷ **`import csv` 지역 import**: `save_csv`(`sim.py`)와 `_write_iter_log`,
  `_write_iter_hist_log`, `_write_fail_log`(`run.py`)의 `import csv`는 표준 라이브러리라
  실패 경로가 없다. 문제는 matplotlib 하나이며 C2-3에서 다룬다.
- ㉸ **`_git_commit_hash()`의 cwd 비의존성**: `cwd=os.path.dirname(os.path.abspath(__file__))`
  (`run.py:417`)로 고정해 실행 위치와 무관하게 저장소 해시를 얻는다. 올바르다.

---

## git status 결과

작업 종료 시점 (`d:\OneDrive\My_Projects\LDPC_dev`):

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

세 항목 모두 이 리뷰가 시작되기 전부터 있던 것이다 (`config.json`은 리뷰 대상 미커밋
변경, `_pm/TODO.md`와 `_pm/tasks/`는 리뷰 진행 산출물). **이 워커가 만지거나 만든
추적 파일은 없다.**

실행 검증의 출력물은 전부 scratchpad로 보냈다.
- 생성한 config 사본 2개, 가짜 `Ideas` 트리 3벌, 가짜 `matplotlib`, 프로브 스크립트 5개
- 실험 출력 `Sim_Output/`, `Sim_Output_png/`, H-matrix 생성물 `hgen_out/`

저장소 안에 새로 생긴 것은 `__pycache__/`의 `.pyc`뿐이며(gitignore 대상),
`2_LDPC_light/Sim_Output/`과 `Ideas/vanilla/Sim_Output/`에는 새 실행 폴더가 만들어지지 않았다.
