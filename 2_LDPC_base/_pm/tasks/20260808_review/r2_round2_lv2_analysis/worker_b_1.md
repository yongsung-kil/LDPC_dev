# Round 2 / 팀 B 워커 1 — `use_input_llr_matrix` 분기, setup 파일 생성 부작용, 재현성

작성: 2026-08-08 14:22:11

## 확인 범위

- 읽은 파일: `LDPC_base/run.py`(전체), `LDPC_base/llr_matrix.py`(전체), `LDPC_base/decoder.py`(102~129, 350~379),
  `LDPC_base/channel.py`(CHANNEL_MODES), `config.json`(미커밋 diff 포함), `Ideas/vanilla/config.json`,
  루트 `.gitignore`, `Input/LLR/` 3개 파일, `README.md`
- 조회: `git diff -- 2_LDPC_light/config.json`, `git ls-files 2_LDPC_light/Input/`,
  `git check-ignore`, `git log -- Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`,
  `grep -rn "json.dump|load_config|generated_llr_matrix_path"`
- 실행 없음. 경로 결합 엣지케이스(`os.path.join(None, ...)`, 빈 dir, Ideas 기준 상대경로)만
  scratchpad에서 `os.path` 단독 검증

## 발견 표

| # | 심각도 | 문제 | 위치 |
|---|--------|------|------|
| F1 | MEDIUM (Decision) | git 추적 폴더 `Input/LLR/`에 실행 산출물을 쓴다. 파라미터를 바꿔 돌릴 때마다 새 파일이 커밋 후보로 쌓이고, 커밋된 `..._iter30.txt`는 현재 config(`max_iter: 120`)와 이미 어긋나 있다 | run.py:206-215, run.py:301-302, .gitignore(전체), config.json:33 |
| F2 | MEDIUM | `mode`가 2SD/3SD여도 load_config를 통과한다. 파일을 추적 폴더에 **먼저 쓴 뒤** 디코딩 첫 호출에서 실패해 쓰레기 파일이 남는다 | run.py:201-204 → run.py:294-303 → decoder.py:371-374 |
| F3 | MEDIUM | 생성 폴더 기본값 `"Input/LLR"`이 config 파일 위치 기준으로 풀려, `Ideas/*/config.json`에서 `use_input_llr_matrix=false`를 켜면 `Ideas/vanilla/Input/LLR/`이라는 새 폴더가 조용히 생긴다 | run.py:206-214 |
| F4 | MEDIUM | false 가지에서 `decoder.llr_matrix` dict가 전혀 검증되지 않는다. `"dir": null`이면 config 에러 대신 raw `TypeError`, 키 오타는 조용히 기본 폴더로 흘러간다 | run.py:207-208 |
| F5 | MEDIUM | true 가지에서 `internal_quantize`가 검증도 사용도 되지 않는데, 저장소 `config.json`이 바로 그 상태(true + `max_iter: 120`)라 실제 max_iter를 오해하게 만든다 | run.py:187-189, config.json:25-35 |
| F6 | MEDIUM | 파일명이 `dv_max`를 담지 않아, H-matrix만 다른 실행이 같은 이름을 **경고 없이** 덮어쓴다. 덮어쓰기 전 확인·로그 없음 (알림 print는 저장 뒤) | run.py:209-211, run.py:298, run.py:301-303 |
| F7 | MEDIUM | 파일명 규약이 조립부(run.py)와 판별부(llr_matrix.py)로 나뉘어 있고, uniform 파일임을 알리는 정보가 **파일명에만** 있다. `num_bits=3` 산출물의 이름에서 uniform이 빠지면 VNU 레벨이 조용히 `{7,5,3,1}`로 바뀐다 | run.py:209-211 ↔ llr_matrix.py:46, 170, 202-203 |
| F8 | LOW | 재현성: true 가지는 산출물에 LLR matrix **파일명만** 남고 내용·해시·절대경로가 남지 않는다 | run.py:527, run.py:530-531, llr_matrix.py:315-317 |
| F9 | LOW | true 가지 파일 부재 시 에러가 "파일 없음"이 아니라 "파일명에서 모드 판별 불가"로 뜬다. H-matrix 쪽 명시적 안내와 비대칭 | run.py:287-288 vs run.py:304, llr_matrix.py:165-168 |
| F10 | LOW | 키맵 밖 파생 키 `generated_llr_matrix_path`를 config dict에 주입한다. 지금은 재검증 경로가 없어 무해하나, `_` 접두 규칙을 쓰면 왕복 가능해진다 | run.py:215 vs run.py:66, run.py:83-85 |
| F11 | LOW | 생성 사실 print가 `run.print_progress`와 무관하게 항상 출력된다 (다만 `saved:`/`run dir:`과는 같은 계열이라 실질 불일치는 아님) | run.py:303, 537, 567 |
| — | 문제 없음 | `os.makedirs(os.path.dirname(...))`의 빈 dirname 위험 없음 | run.py:213-214, 301 |

---

## 상세

### A. `load_config`의 경로 조립과 주입

#### A-㉮ `generated_llr_matrix_path` 주입 → F10 (LOW)

`run.py:215`가 `decoder_config["generated_llr_matrix_path"]`를 주입하는데 이 키는 `_DECODER_KEYS`
(`run.py:66`)에 없다. config dict를 다시 검증하는 경로를 전 코드에서 추적한 결과:

- `load_config` 호출 지점은 `run.py:576` 한 곳뿐 (`grep`으로 확인). 항상 **파일에서** 새로 읽으므로
  주입된 dict가 `_check_keys`로 되돌아오는 경로는 없다.
- `report`(`run.py:527`)는 `shutil.copy(config_path, ...)` — **원본 파일을 복사**하지 변형된 dict를
  덤프하지 않는다. 따라서 실행 폴더의 `config.json` 사본에도 이 키는 없고, 사본을 그대로 재실행해도
  걸리지 않는다.
- 사용자가 JSON에 직접 `generated_llr_matrix_path`를 쓰면 `_check_keys`가 거부한다 (의도대로 동작).

즉 **현재 동작에는 문제가 없다.** 다만 config dict는 이미 왕복 불가 상태다 — `config["H_matrix"]`와
`decoder.llr_matrix`가 dict→문자열로 바뀌므로(`run.py:174-175`, `188-189`), 이 dict를 덤프해 다시
`load_config`에 넣으면 `_path_pair`가 "객체여야 함"으로 먼저 터진다. `generated_llr_matrix_path`는
그 왕복 불가 목록에 한 항목을 더한 것이다.

개선: 코드에 이미 `_` 시작 키를 검사에서 빼는 규칙(`_visible`, `run.py:83-85`)이 있다.
파생 키를 `_generated_llr_matrix_path`로 이름 지으면 "사용자 키가 아니라 코드가 만든 값"이라는 뜻이
이름에 드러나고, 나중에 dict 덤프 방식으로 바꿔도 재검증을 통과한다.

#### A-㉯ false일 때 `decoder.llr_matrix` 처리 범위 → F4 (MEDIUM)

```python
# run.py:206-208
generated_dir = "Input/LLR"
if isinstance(decoder_config.get("llr_matrix"), dict):
    generated_dir = decoder_config["llr_matrix"].get("dir", generated_dir)
```

false 가지는 `_path_pair`를 부르지 않으므로 `llr_matrix`에 대해 `_check_keys`도, `_require`도 돌지
않는다. 통과 범위:

- ㉮ `"llr_matrix": "Input/LLR/x.txt"` (문자열) — dict가 아니라 조용히 무시, 기본 폴더 사용.
  문서가 "무시"라고 했으니 의도대로다.
- ㉯ `"llr_matrix": {"dir": null, "file": "x"}` — **`.get("dir", 기본값)`은 키가 있으면 `None`을
  돌려준다**(검증 완료). 이어지는 `os.path.join(None, ...)`가 `TypeError: expected str, bytes or
  os.PathLike object, not NoneType`을 낸다. 다른 모든 null은 `_require`가 "없음 또는 null — 필수 값"
  으로 잡아주는데 여기만 스택트레이스가 그대로 노출된다.
- ㉰ `"dir": 5` 같은 비문자열 — 같은 `TypeError`.
- ㉱ `{"dirr": "..."}` 오타나 `{"dir": ..., "fille": ...}` — 조용히 통과. 같은 config를
  `use_input_llr_matrix=true`로 토글하면 그때는 `_check_keys`가 잡는다. **토글 방향에 따라 같은
  config가 통과하기도 실패하기도 한다**는 뜻이라, "플래그만 바꿔 토글"이라는 문서 서술
  (README.md:69-70)과 어긋난다.

권장: false 가지에서도 `llr_matrix`가 dict면 `_check_keys("decoder.llr_matrix", d, {"dir","file"})`를
돌리고, `dir` 값은 `isinstance(str)` 확인 후 사용한다.

#### A-㉰ 상대경로 기준 → F3 (MEDIUM)

`run.py:212-214`가 `generated_path`를 config 파일 위치(`base_dir`) 기준으로 절대화한다. 두 config에서:

| config 위치 | `llr_matrix.dir` | 결과 경로 |
|---|---|---|
| `2_LDPC_light/config.json` | `"Input/LLR"` | `2_LDPC_light/Input/LLR/` (의도대로) |
| `2_LDPC_light/config.json` | 키 없음 | `2_LDPC_light/Input/LLR/` (같음) |
| `Ideas/vanilla/config.json` | `"../../Input/LLR"` | `2_LDPC_light/Input/LLR/` (공용 폴더) |
| `Ideas/vanilla/config.json` | **키 없음** | `2_LDPC_light/Ideas/vanilla/Input/LLR/` ← 새 폴더 |

마지막 줄이 문제다. `os.makedirs(..., exist_ok=True)`(`run.py:301`)가 없는 폴더를 조용히 만들기
때문에 아이디어 폴더 안에 아무도 보지 않는 `Input/LLR/`이 생긴다. 현재 `Ideas/vanilla/config.json`에는
`use_input_llr_matrix` 키가 없어 기본 true라 아직 발현되지 않지만, README.md:69-70이 광고하는
"플래그만 바꿔 토글"을 아이디어 config에서 하는 순간 발생한다.

또한 문서(README.md:70, config.json:20, run.py:18)가 전부 "없으면 Input/LLR"이라고만 적어
**어느 Input/LLR인지** 알 수 없다. 기본값을 config 상대가 아니라 실험 루트 고정으로 정하든,
문서에 "config 파일 위치 기준"을 명시하든 한쪽으로 정해야 한다.

#### A-㉱ `os.path.dirname`이 빈 문자열일 위험 — 문제 없음

`run.py:213-214`가 `generated_path`를 항상 절대경로로 만든 뒤에 `run.py:301`의 `makedirs`가 돈다.
`"dir": ""`인 경우도 `os.path.join("", name)` → `"name"` → `isabs` False → `base_dir`와 결합되어
절대경로가 된다(검증 완료). 따라서 `os.path.dirname`이 빈 문자열이 되는 입력은 없다.

---

### B. 파일명 규약과 덮어쓰기

#### B-㉮ 파일명이 담는 것과 담지 않는 것 → F6 (MEDIUM)

```python
# run.py:209-211
generated_name = (f"LLR_MATRIX_{mode}_uniform_{internal_quantize['num_bits']}bit"
                  f"_ch{internal_quantize['channel_llr']}"
                  f"_iter{internal_quantize['max_iter']}.txt")
```

| 매트릭스 내용에 반영되는 값 | 파일명 반영 | 출처 |
|---|---|---|
| `mode` | O | config |
| `num_bits` (→ th 목록, edge_mag, num_param, max_value) | O | config |
| `channel_llr` (→ ch 값, max_value) | O | config |
| `max_iter` (→ row의 iter_end) | O | config |
| **`dv_max`** (→ `dv_to`) | **X** | H-matrix (`run.py:298`, `code.col_deg.max()`) |

`dv_max`가 이름에 없으므로, 같은 `internal_quantize`로 dv_max가 다른 H-matrix를 돌리면 **내용이
다른 파일이 같은 이름으로 덮어써진다.**

"setup이 매번 생성 후 로드하므로 stale 로드는 없다"는 전제는 **코드에서 참이다.** `run.py:293-303`에
파일 존재 확인이나 생성 스킵 분기가 없다 — 무조건 `make_internal_uniform_matrix` → `save` →
`load` 순서로 간다. 따라서 한 실행 안에서 옛 파일을 읽는 일은 없다.

남는 피해는 **저장소에 남은 파일의 의미가 조용히 바뀐다**는 것이다. 커밋된
`LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`를 dv_max가 다른 H-matrix로 한 번 돌리면 내용이 바뀌어
`git diff`에 뜨고, 그 파일을 근거로 과거 실행을 해석하던 사람이 틀린 표를 보게 된다.

#### B-㉯ 무경고 덮어쓰기 → F6 (MEDIUM)

`run.py:301-303`은 `makedirs` → `save` → `print` 순서다. **저장 전 존재 확인도, 덮어쓴다는 경고도
없고**, 알림 print는 이미 쓴 뒤에 나온다. `LLRMatrix.save`(`llr_matrix.py:258`)도 `open(path, "w")`
로 무조건 자른다.

사람이 만든 파일과 이름이 충돌할 범위는 좁다 — 규약상 사람이 만든 파일에는 `uniform`을 쓰지 않기로
했고(llr_matrix.py:163-164), 현재 `Input/LLR/`의 사람 파일은 `LLR_MATRIX_HD_0.txt`,
`LLR_MATRIX_HD_1.txt`다. 다만 이 규약은 문서에만 있고 코드가 강제하지 않으므로,
`uniform`이 들어간 파일을 사람이 손으로 만들어 두면 첫 false 실행에서 예고 없이 사라진다.
최소한 "기존 파일을 덮어씀"을 print에 남기는 정도는 필요하다.

#### B-㉰ 조립부와 판별부가 두 파일로 나뉜 구조 → F7 (MEDIUM)

- 조립: `run.py:209-211` (문자열 리터럴)
- 판별: `llr_matrix.py:46` `_NAME_RE = LLR_MATRIX_(HD|2SD|3SD)_`, `llr_matrix.py:170`
  `"uniform" in os.path.basename(path).lower()`, `llr_matrix.py:202-203` (판별 결과로 edge_mag 결정)

한쪽만 바뀌었을 때의 파급 (수치 정확성은 팀 A 소관이므로 구조 리스크만):

- ㉮ 조립부에서 `LLR_MATRIX_` 접두가 빠지면 → `load`의 `_NAME_RE`가 실패해
  "파일명에서 모드 판별 불가" ValueError. **크래시로 드러남.**
- ㉯ 조립부에서 `uniform`이 빠지면 → `edge_mag=None`으로 로드되어 `__init__`이 th 개수를 3으로
  기대한다(`llr_matrix.py:68-72`). `num_bits=6`이면 th 31개라 `NotImplementedError`로 **드러난다.**
- ㉰ **다만 `num_bits=3`은 조용히 틀린다.** `top_level = 2^2-1 = 3` → th `[3,2,1]` → `th_len == 3`이라
  기본 분기가 열리고 VNU 출력 레벨이 `[3,2,1,0]`이 아니라 DAO 3-bit 기본값 `{7,5,3,1}`로 잡힌다.
  파일명에서 `uniform`이 빠지는 경로가 코드 변경만은 아니다 — **생성된 파일을 사람이
  `LLR_MATRIX_HD_2.txt`처럼 정리용으로 개명하면 곧바로 이 상태가 된다.** 진행은 되고 결과만 틀린다.

근본 원인은 "uniform 매트릭스인가"라는 정보가 **파일명에만** 있다는 것이다. 저장 포맷은 변경 금지
대상이라 파일 안에 표시를 넣을 수 없으므로, 최소한 파일명 조립 함수를 `llr_matrix.py`에 두어
조립부와 판별부가 한 파일 안에서 짝을 이루게 하는 것이 현실적이다. 지금은 규약이
`run.py`, `llr_matrix.py`, `README.md` 세 곳에 흩어져 있다.

---

### C. setup의 부작용과 git 정책

#### C-㉮ 추적 폴더에 산출물 쓰기 → F1 (MEDIUM, 등급으로는 Decision)

루트 `.gitignore`에 `Sim_Output/`은 있으나 `Input/LLR/`은 없다. 실제 추적 상태:

```
$ git ls-files 2_LDPC_light/Input/
2_LDPC_light/Input/H_matrix/example_18x147_z256.qc
2_LDPC_light/Input/LLR/LLR_MATRIX_HD_0.txt
2_LDPC_light/Input/LLR/LLR_MATRIX_HD_1.txt
2_LDPC_light/Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt   ← 생성 산출물이 커밋됨
$ git check-ignore -v .../LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt
(exit 1 = 무시 대상 아님)
```

`Input/`은 이름이 말하듯 **입력** 폴더이고 `.gitignore` 39행 주석도 "2_LDPC_light/Input/H_matrix는
추적 대상"이라고 입력 자산 보관 의도를 밝히고 있다. 여기에 실행 산출물을 쓰면
`num_bits`/`channel_llr`/`max_iter`를 바꿔 스윕할 때마다 새 파일이 `git status`에 `??`로 쌓인다.
정책 선택지는 셋 중 하나여야 한다.

- 1. 생성물 전용 폴더(예: `Input/LLR/generated/` 또는 `Sim_Output` 계열)로 옮기고 `.gitignore`에 추가
- 2. `Input/LLR/*uniform*`을 `.gitignore`에 추가하고, 커밋된 uniform 파일은 삭제
- 3. 지금처럼 커밋 자산으로 유지하되, 어떤 파라미터의 파일을 저장소에 남길지 규칙을 문서화

설계 결정이 필요한 사항이므로 사용자 확인 대상이다.

#### C-㉯ 커밋된 파일과 config의 어긋남 → F1 (MEDIUM)

두 파일을 직접 대조한 결과 **어긋나 있다.**

- `config.json:33` — `"max_iter": 120`
- 커밋된 `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt` — 마지막 row 꼬리가
  `... -1  1  30  -1` 즉 `iter_start=1, iter_end=30`. 파일명도 `iter30`.
- `num_bits`/`channel_llr`는 일치한다: 헤더 `num_param=32`, ch 값 `8`, th `31..1` →
  `num_bits=6`(top_level 31), `channel_llr=8`.
- `git log`상 이 파일은 `e6282b1` 한 커밋에서 들어왔고, 같은 커밋에서 config의 `max_iter`는 120이었다.
  즉 `max_iter=30`짜리 임시 실행 산출물이 그대로 커밋된 것이다.

현 config로 `use_input_llr_matrix=false`를 켜고 실행하면:

- 새로 생김: `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt` (추적되지 않은 새 파일 → 커밋 후보)
- 그대로 남음: `..._iter30.txt` (아무도 참조하지 않는 고아 파일, 계속 추적됨)

README.md:15의 `Input/LLR/` 설명도 HD_0/HD_1만 적고 uniform 파일은 언급하지 않아, 이 파일이
저장소에 왜 있는지 알 방법이 없다 (문서 쪽은 팀 D 소관이라 지적만 남긴다).

#### C-㉰ 2SD/3SD 통과와 실패 순서 → F2 (MEDIUM)

`run.py:201-204`가 `mode`를 `("HD","2SD","3SD")`로 받는다. 2SD로 두고 rber 채널을 돌리면
실패 지점이 **파일을 다 쓴 뒤**다.

1. `load_config` 통과 (mode 2SD 허용)
2. `setup`(`run.py:294-303`) — `make_internal_uniform_matrix(mode="2SD")`가 정상 합성되고
   (`ch_len=2`, `num_param=2+top_level`, `th_len=top_level` → edge_mag 길이 검사 통과),
   **추적 폴더에 `LLR_MATRIX_2SD_uniform_....txt`를 저장**한 뒤 다시 로드한다.
   `_NAME_RE`도 `uniform` 판별도 2SD 이름에서 정상 동작하므로 왕복은 성공한다.
3. `MinSumDecoder.__init__`(`decoder.py:112`) — 2SD는 허용 목록에 있어 통과
4. `run_experiment`의 사전 확인 `_check_channel_mode`(`run.py:378-379`) — `channel.py:146`이
   rber에 `("HD","2SD","3SD")`를 허용하므로 **통과**
5. 첫 배치 복호에서 `decoder_main`(`decoder.py:371-374`)이
   `NotImplementedError: 2SD 디코딩 산술 미구현`

결과: 실행은 실패하고 `Sim_Output` 폴더는 생기지 않는데, **git 추적 폴더에는 2SD 파일이 남는다.**
`fixed_error`/`strong_error` 채널이면 4단계에서 더 일찍 실패하지만 파일은 이미 쓰인 뒤다.

수리 방향은 둘 중 하나다.

- 1. `load_config`에서 `internal_quantize.mode`를 당분간 `"HD"`만 받는다 (2SD/3SD 디코딩 구현 시 해제).
     디코더 제약을 설정 검증 단계로 끌어올리는 쪽이라 실패가 가장 이르다.
- 2. `setup`에서 파일을 쓰기 전에 모드 호환(디코더 지원 + 전 채널 호환)을 확인한다.

#### C-㉱ 생성 알림 print → F11 (LOW)

`run.py:303`의 `print(f"generated LLR matrix: ...")`는 `run.print_progress`와 무관하게 항상 나온다.
다만 파일 산출을 알리는 다른 출력도 모두 무조건이다 — `report`의 `saved: {csv_path}`(537),
`saved: {png_path}`(564), `run dir: {run_dir}`(567), `main`의 요약 출력(578-579).
`print_progress`는 `run_fer_point`의 측정 진행률과 `== channel=... ==`(394-395)만 끈다.
따라서 실질적인 불일치는 아니고, `print_progress`가 무엇을 끄는지 문서에
("측정 진행률만 끄며 산출물 알림은 항상 출력") 한 줄 적는 정도가 적절하다.

#### C-㉲ 재현성 → F8 (LOW)

실행 산출물에 남는 정보:

- `run_dir/config.json` — `shutil.copy(config_path, ...)`(`run.py:527`)로 **원본 파일 복사**.
  `internal_quantize`의 `num_bits`/`channel_llr`/`max_iter`/`mode`와 `H_matrix`의 dir·file이 그대로 남는다.
  변형된 dict가 아니므로 `generated_llr_matrix_path`(절대경로)는 남지 않는다.
- `run_dir/summary.txt` — `_experiment_summary_lines`가 `decoder.llr_matrix.summary()`를 넣는다
  (`run.py:319-321`). 내용은 `LLRMatrix {basename}: mode=HD (ch1+th31), dv=[1]~[dv_max],
  max_iter=..., groups: g1[1~max_iter]x1` (`llr_matrix.py:315-317`) — **파일명, 모드, ch/th 개수,
  dv 범위, max_iter가 남는다.** `code.summary()`로 H-matrix 정보도 남는다.
- git 커밋 해시(`run.py:530`).

판정:

- ㉮ **false 가지는 재현 가능하다.** config 사본의 `internal_quantize` 4개 값 + H-matrix로
  같은 파일을 다시 만들 수 있고, `dv_max`도 summary의 `dv=[1]~[N]`에 남는다.
  파일 자체나 해시는 남지 않지만 결정론적 합성이라 문제되지 않는다.
- ㉯ **true 가지가 약하다.** 남는 것은 config 사본의 `dir`/`file`과 summary의 basename뿐이고,
  **파일 내용은 어디에도 보존되지 않는다.** `Input/LLR/LLR_MATRIX_HD_1.txt`를 나중에 고치면
  과거 실행을 재현할 방법이 없고, 고쳤다는 사실조차 산출물에서 알 수 없다.
  summary에 LLR matrix 파일의 절대경로와 내용 해시 한 줄을 추가하면 해결된다
  (요약 출력 내용의 정확성 자체는 워커 3 소관).

---

### D. `use_input_llr_matrix=true` 가지

#### D-㉮ true인데 `internal_quantize`가 있으면 → F5 (MEDIUM)

`run.py:187-189`의 true 가지는 `llr_matrix`만 `_path_pair`로 처리하고 `internal_quantize`는
건드리지 않는다. `internal_quantize`는 `_DECODER_KEYS`(66행)에 있으므로 키맵도 통과한다. 결과:

- 값 검증 없음 — `"num_bits": "six"`, `"max_iter": -5`, `{"num_bts": 6}` 같은 오타가 전부 통과한다.
  `false`로 토글하는 순간에야 에러가 난다.
- 값 무시 — 디코딩에 아무 영향이 없다.

문서와의 일치: README.md:69-70과 config.json:19는 "false면 llr_matrix 키는 있어도 무시된다"만 적고,
**true일 때 internal_quantize가 무시된다는 서술은 README, config.json `_desc`, run.py docstring
(11-27행) 어디에도 없다.** run.py docstring 24행은 "use_input_llr_matrix=false일 때 필수"까지만 말한다.

실제 함정이 저장소에 이미 놓여 있다. 현재 `config.json`은 `use_input_llr_matrix: true`(25행)인데
`internal_quantize.max_iter: 120`(33행)을 달고 있다. 이 파일만 보면 max_iter 120으로 도는 것처럼
읽히지만 실제 max_iter는 `LLR_MATRIX_HD_1.txt`의 마지막 `iter_end`인 **20**이다.
`summary.txt`와 콘솔 요약에는 decoder에서 읽은 실제 값이 찍히므로(`run.py:322-323`) 결과 해석까지
틀리지는 않지만, 설정 파일을 근거로 실험을 설계하는 단계에서 오해를 부른다.

권장: 무시 대상 섹션이 존재하면 한 줄 알린다 (예:
`use_input_llr_matrix=true — internal_quantize는 사용하지 않음`). 양쪽 가지 대칭으로 두면
"플래그만 바꿔 토글"이라는 서술도 사실이 된다.

#### D-㉯ true 가지의 경로 해석과 파일 부재 에러 → F9 (LOW)

경로 해석은 `_path_pair`(`run.py:110-118`)가 담당하며 config 파일 위치 기준으로 절대화한다.
`Ideas/vanilla/config.json`의 `"../../Input/LLR"`도 공용 폴더로 정확히 풀린다(검증 완료).
이 부분은 문제 없다.

파일 부재 시:

- H-matrix는 `setup`(`run.py:287-288`)에서 `os.path.exists`로 먼저 확인하고
  `"{path} 없음 — H-matrix를 먼저 준비할 것"`이라는 안내를 낸다.
- LLR matrix는 사전 확인이 없다(`run.py:304`가 바로 `LLRMatrix.load`). `load` 안에서 파일명 판별
  (`llr_matrix.py:165-168`)이 `open`보다 먼저 돌기 때문에, 파일명이 규칙 밖이면
  **`"파일명에서 모드 판별 불가"`가 먼저 뜬다.** 사용자가 파일명을 오타냈을 때(가장 흔한 경우)
  "그런 파일이 없다"는 사실을 알려주지 않는다. 이름이 규칙에 맞으면 `open`의 raw `FileNotFoundError`
  가 그대로 올라온다.

권장: `setup`에서 H-matrix와 같은 형태로 존재 확인 한 줄을 추가한다.

---

## 참고 (다른 워커 소관이라 지적만)

- `README.md:15`의 `Input/LLR/` 설명이 커밋된 uniform 파일을 언급하지 않는다 (팀 D)
- `docs/` 아래 어디에도 `use_input_llr_matrix`/`internal_quantize` 서술이 없다 —
  `grep -rn "use_input_llr_matrix|internal_quantize|uniform" docs/` 무결과 (팀 D)
- `2_LDPC_light/llr_tables.py`가 패키지 밖 루트에 남아 있다 (`LDPC_base/`로 이동한 코드의 잔재로
  보인다 — 팀 C의 패키지 경계 관점)
