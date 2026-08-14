# Round 3 검증 보고 — 검증팀 c(docs_data) 워커 2

> 작성: 2026-08-08 15:08:53
> 대상: TD-3, TD-4, TD-5, TD-6 (전부 HIGH)
> 방법: 문서·코드 직접 열람, 실행 재현(출력은 전부 scratchpad), git 이력 대조
> 판정 체계: 1단계(지적된 서술이 그 위치에 그 내용으로 존재하는가), 2단계(그 서술이 사실과 다른가)

## 최종 판정 요약

| 발견 | 1단계 (서술 존재) | 2단계 (사실 불일치) | 최종 |
|------|------------------|--------------------|------|
| TD-3 (차이.md #9) | 확인됨 | 확인됨 | **확인됨** |
| TD-4 ("llr_matrix 무시") | 확인됨 (README는 라인 1칸 어긋남) | README 확인됨, run.py·config.json 부분 확인 | **부분 확인** (README만 온전한 결함) |
| TD-5 (vanilla README 실행 루트) | 확인됨 | 확인됨 | **확인됨** |
| TD-6 (tools README 미래 시제) | 확인됨 (select_irregular.py는 라인 2칸 어긋남) | 확인됨 | **확인됨** |

---

## H3 (TD-3) — `docs/차이.md:25` 항목 #9의 한정 조건 누락

### 1단계: 서술 존재 — **확인됨** (라인 일치)

`docs/차이.md:25` 원문 (표 한 행 전체):

```
| 9 | LLR 정밀도 빌드 | 3-bit(EDGE 4레벨, th 3개)와 `__4_BIT_LLR__`(EDGE 8레벨, th 7개) 두 빌드 | **3-bit 전용** (EDGE {7,5,3,1} 고정, th 3개 아니면 에러) | **사용자 확정 (2026-08-06): LLR은 3-bit만 사용, 4-bit 확장 계획 없음** |
```

문맥:

- ㉮ 절 제목은 `docs/차이.md:13` "## 1. 차이가 있는 항목"
- ㉯ 표 머리는 `docs/차이.md:15` `| # | 항목 | original | 현재 .py | 비고 |`
- ㉰ 지적된 문구 "**3-bit 전용** (EDGE {7,5,3,1} 고정, th 3개 아니면 에러)"는 **"현재 .py" 열**의 내용이다. 특정 파일 경로나 특정 로드 방식으로 좁히는 한정어가 그 칸에 없다
- ㉱ 문서 머리(`docs/차이.md:4-5`)는 비교 대상 .py를 "이 폴더의 `LDPC_base/decoder.py` `decoder_main()` (syndrome-aided, HD 전용, 본체 커밋 72b825a에서 파생하여 2026-08-06 개정)"으로 밝힌다

### 2단계: 사실 불일치 — **확인됨**

th 3개 검사는 `edge_mag`가 주어지지 않았을 때만 실행되고, uniform 표시가 있는 파일에는 `load()`가 `edge_mag`를 채워 준다. 실행으로도 확인했다.

또한 "EDGE {7,5,3,1} 고정"은 `decoder.py:150-151`이 직접 부정한다: "레벨 값과 개수는 llr_matrix.edge_mag가 결정한다 (파일 3-bit {7,5,3,1}, 내부 균일 n-bit [최대..0])".

### E3-5 false positive 반증 시도

"uniform 표시 없는 일반 LLR 파일 경로에 한정한 서술"로 읽으면 참이 되는가를 따졌다. 결론은 **그 읽기가 성립하지 않는다**.

- ㉮ 열 이름이 "현재 .py"이므로 대상은 Python 구현 전체이며, 칸 안에 "파일 로드 시" 같은 한정 문구가 없다
- ㉯ 가장 좁게 읽어 대상을 `decoder_main()`으로 한정해도, 그 함수가 쓰는 `_vnu_quantize`는 레벨을 `llr_matrix.edge_mag`에서 받는다 (`decoder.py:153-157`). 즉 `decoder_main()` 기준으로도 "EDGE {7,5,3,1} 고정"은 거짓이다
- ㉰ 균일 n-bit 매트릭스는 **파일로 저장한 뒤 파일로 로드해서** 소비된다 (`run.py:294-304`). "파일 경로 한정"이라는 방어선 자체가 성립하지 않는다

곁가지로, `llr_matrix.py:70`의 에러 문구 "파일 매트릭스는 3-bit(th 3개) 전용"도 같은 문제를 안는다. uniform 표시가 붙은 파일 매트릭스는 th가 3개가 아니어도 로드된다.

### 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E3-1 | 차이.md #9는 "현재 .py" 열의 무조건 서술이며 파일 경로 한정어가 없다 | 확인됨 | `docs/차이.md:13, 15, 25` |
| E3-2 | raise는 `edge_mag is None`인 경우 안에 중첩되어 있고, th 개수 3 검사는 그 안쪽 조건이다 | 확인됨 | `LDPC_base/llr_matrix.py:67-71` (`if edge_mag is None:` → `if self.th_len != 3:` → `raise NotImplementedError`) |
| E3-3 | uniform 판별은 **파일명 부분문자열**이고, 참이면 `edge_mag`를 `[th 개수..0]`으로 채운다 | 확인됨 | `llr_matrix.py:170` `is_uniform = "uniform" in os.path.basename(path).lower()`, `:202-203` `edge_mag = (uniform_edge_mag(num_param - MODE_CH_LEN[mode]) if is_uniform else None)` |
| E3-4 | th 31개 매트릭스를 내용은 같게 두고 파일명만 바꿔 로드: uniform 표시 있으면 성공, 없으면 에러 | 확인됨 | 실행 출력 아래 인용 |
| E3-5 | "파일 경로 한정" 읽기로도 서술이 참이 되지 않는다 | 확인됨 (반증 실패) | `decoder.py:150-157`, `run.py:294-304` |

E3-4 실행 출력 (`scratchpad/e3_uniform_th_test.py`):

```
합성 성공: LLRMatrix internal_uniform_6bit: mode=HD (ch1+th31), dv=[1]~[10], max_iter=20, groups: g1[1~20]x1 | th_len = 31 | edge_mag 앞 5개 = [31.0, 30.0, 29.0, 28.0, 27.0]
㉮ uniform 표시 있음: 로드 성공 — th_len=31, edge_mag 앞 5개=[31.0, 30.0, 29.0, 28.0, 27.0]
㉯ uniform 표시 없음: NotImplementedError: LLR_MATRIX_HD_9.txt: th 31개 — 파일 매트릭스는 3-bit(th 3개) 전용. 다른 레벨 구성은 edge_mag를 지정해 합성할 것
```

두 파일은 바이트 단위로 같은 내용이며 파일명만 다르다 (`shutil.copyfile`로 복제).

### H3 최종 판정: **확인됨**

사유: 지적된 서술이 지적된 위치에 무조건 서술로 존재하고, 균일 n-bit 경로에서 th 3개가 아니어도 에러가 나지 않음을 실행으로 재현했다. 문맥을 최대한 좁게 읽어도 "EDGE {7,5,3,1} 고정"이 거짓이라 방어 가능한 해석이 없다.

---

## H4 (TD-4) — "`llr_matrix` 키는 있어도 무시된다" 서술

### 1단계: 서술 존재 — **확인됨** (README는 라인 1칸 어긋남)

㉮ `README.md` (지적 라인 70, 실제 문장은 **69-70행에 걸침**):

```
  mode(기본 HD)로 파일을 만들며, llr_matrix 키는 있어도 무시된다 (플래그만
  바꿔 토글 가능). 생성 파일명의 **uniform은 사람이 만든 파일이 아니라는 표시**
```

㉯ `LDPC_base/run.py:17-19` (라인 일치):

```
    false면 균일 n-bit 양자화 매트릭스를 **DAO 포맷 파일로 생성해 저장한 뒤
    그 파일을 로드**해 디코딩 (internal_quantize 설정 사용, llr_matrix 키는
    있어도 무시). 생성 파일은 llr_matrix.dir(없으면 Input/LLR)에
```

㉰ `config.json:19-20` (작업 트리 기준, 라인 일치):

```
      "  로드해 디코딩 (internal_quantize 사용, llr_matrix 키는 무시).",
      "  생성 위치: llr_matrix.dir(없으면 Input/LLR), 파일명 LLR_MATRIX_{mode}_uniform_...",
```

세 서술 모두 `use_input_llr_matrix`가 false일 때를 다루는 문단 안에 있다.

### 2단계: 사실 불일치 — README 확인됨, run.py·config.json 부분 확인

`llr_matrix.dir`는 생성 파일의 저장 폴더를 정한다.

```python
206	        generated_dir = "Input/LLR"
207	        if isinstance(decoder_config.get("llr_matrix"), dict):
208	            generated_dir = decoder_config["llr_matrix"].get("dir", generated_dir)
```

실측 결과 (E4-3):

- ㉮ `llr_matrix.dir`를 `"generated_here"`로 준 경우
  `...\scratchpad\e4\generated_here\LLR_MATRIX_HD_uniform_4bit_ch5_iter6.txt`
- ㉯ `llr_matrix` 키를 통째로 뺀 경우
  `...\scratchpad\e4\Input/LLR\LLR_MATRIX_HD_uniform_4bit_ch5_iter6.txt`

두 경우 모두 config 사본을 scratchpad에 두어 `<config dir>`가 scratchpad가 되게 했고, 저장소 `Input/LLR/`에는 파일이 생기지 않았다.

정확한 동작은 "**`file` 하위 키는 쓰이지 않고 `dir` 하위 키는 저장 폴더로 쓰인다**"이다. 즉 `llr_matrix` 키는 부분적으로만 무시된다.

### E4-4 false positive 반증 시도

"LLR matrix 파일을 **읽는 용도로는** 무시된다"는 뜻으로 읽힐 여지가 있는가를 따졌다. 세 곳의 판정이 갈린다.

- ㉮ `run.py:17-19`와 `config.json:19-20`은 "무시" 바로 다음 문장에서 "생성 파일은 llr_matrix.dir(없으면 Input/LLR)에 저장된다", "생성 위치: llr_matrix.dir(없으면 Input/LLR)"를 명시한다. 같은 문단을 끝까지 읽은 독자는 "읽기 용도로 무시, 저장 폴더로는 사용"으로 정확히 이해한다. 따라서 이 두 곳은 **한 문단 안에서 앞 문장이 뒷 문장에 뒤집히는 표현 결함**이며, 독자가 틀린 정보를 얻는 결함은 아니다 → **부분 확인**
- ㉯ `README.md:69-70`에는 그 정정 문장이 없다. 이어지는 내용은 생성 파일**명**의 uniform 표시 설명뿐이고, 생성 **위치**를 어디서도 다루지 않는다. README만 읽은 독자는 `llr_matrix` 키가 완전히 무력하다고 결론 내린다 → **확인됨**

### E4-5 커밋본 대조

`git show HEAD:2_LDPC_light/config.json`과 작업 트리의 차이는 `use_input_llr_matrix:` 설명 첫 줄을 두 줄로 나눈 것뿐이다. 문제의 서술("llr_matrix 키는 무시" + "생성 위치: llr_matrix.dir")은 커밋본(18-19행)과 작업 트리(19-20행)가 같은 내용이다. 서술 차이 없음.

### 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E4-1 | 세 곳 모두 `use_input_llr_matrix=false` 문단 안에 "llr_matrix 키는 무시" 서술이 있다 | 확인됨 | `README.md:69-70`, `LDPC_base/run.py:17-19`, `config.json:19-20` |
| E4-2 | `llr_matrix.dir`가 생성 파일 저장 폴더를 정한다 | 확인됨 | `run.py:206-208`, 이어 `:212-215`에서 경로 결합, `setup()`의 `:300-302`에서 그 경로로 저장 |
| E4-3 ㉮ | `dir` 지정 시 그 폴더에 생성된다 | 확인됨 | 실행 출력 `generated_llr_matrix_path = ...\e4\generated_here\LLR_MATRIX_HD_uniform_4bit_ch5_iter6.txt` |
| E4-3 ㉯ | 키 삭제 시 `<config dir>/Input/LLR`에 생성된다 | 확인됨 | 실행 출력 `generated_llr_matrix_path = ...\e4\Input/LLR\LLR_MATRIX_HD_uniform_4bit_ch5_iter6.txt` |
| E4-4 | run.py·config.json은 다음 문장이 정정하므로 독자 오해가 발생하지 않는다 | 반박됨(해당 두 곳 한정) | `run.py:19`, `config.json:20` |
| E4-4 | README에는 정정 문장이 없어 무조건 서술로 남는다 | 확인됨 | `README.md:66-71` 전체에 생성 위치 언급 없음 |
| E4-5 | 커밋본과 작업 트리의 서술 차이 없음 (줄 나눔만 다름) | 확인됨 | `git diff -- 2_LDPC_light/config.json` |

### H4 최종 판정: **부분 확인**

사유: "무시되지 않는다"는 지적 자체는 코드와 실측으로 성립한다. 다만 지적된 세 곳 중 `run.py`와 `config.json`은 바로 다음 문장에서 `llr_matrix.dir` 사용을 명시하므로 독자에게 틀린 정보를 주지 않는다. 온전한 결함은 정정 문장이 없는 `README.md:69-70` 한 곳이다. 수리 시 README에 생성 위치를 넣고, 세 곳 모두 "`file`은 쓰이지 않고 `dir`가 생성 위치를 정한다"로 다시 쓰는 것이 맞다.

---

## H5 (TD-5) — `Ideas/vanilla/README.md:13`의 실행 루트

### 1단계: 서술 존재 — **확인됨** (라인 일치)

`Ideas/vanilla/README.md:11-17` 원문:

```
## 실행

실험 루트(`_test/20260806_setup_구성_실험/`)에서:

```bat
python -m LDPC_base.run Ideas/vanilla/config.json
```
```

### 2단계: 사실 불일치 — **확인됨**

- ㉮ `git ls-files 2_LDPC_light/_test`는 결과가 없다. 저장소에 추적되는 파일이 하나도 없다
- ㉯ 파일시스템에는 `2_LDPC_light/_test/20260806_setup_구성_실험/`이 남아 있으나 그 안에는 `README.md` 하나뿐이다 (`find . -maxdepth 2` 결과가 `.`과 `./README.md`). `LDPC_base/`도 `Ideas/`도 없다
- ㉰ 그 `README.md:1-4`는 스스로 "이 폴더에서 개발한 개정본(LDPC_base, Ideas, Input, config.json, 문서)은 2026-08-07에 **본체(`2_LDPC_light/`)로 이동**했다"라고 밝힌다
- ㉱ 안내대로 그 폴더에서 실행하면 실패한다 (아래 출력)

올바른 실행 방법 (E5-3):

- ㉮ `README.md:23`은 "이 폴더(`2_LDPC_light/`)에서:"라고 적고 `:27`에 `python -m LDPC_base.run Ideas/vanilla/config.json`을 둔다
- ㉯ `LDPC_base/run.py:9`는 "실행: 2_LDPC_light/에서 python -m LDPC_base.run config.json"이라고 적는다
- ㉰ `Ideas/vanilla/config.json`의 상대경로는 `../../Input/H_matrix`, `../../Input/LLR`이다. config 파일 위치(`2_LDPC_light/Ideas/vanilla/`) 기준이므로 `../../`가 `2_LDPC_light/`를 가리켜 현 배치와 맞는다
- ㉱ 결론: **`2_LDPC_light/`에서 `python -m LDPC_base.run Ideas/vanilla/config.json`**. 작업 디렉토리가 `2_LDPC_light/`여야 하는 이유는 `LDPC_base` 모듈과 `Ideas` 패키지 import이며(`run.py:262-263`), 데이터 경로는 config 위치 기준으로 따로 풀린다

### 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E5-1 | 실험 루트를 `_test/20260806_setup_구성_실험/`로 지목 | 확인됨 | `Ideas/vanilla/README.md:13` |
| E5-2 | 저장소 추적 파일 0개, 파일시스템에는 README.md만 존재 | 확인됨 | `git ls-files 2_LDPC_light/_test` 무출력, `_test/20260806_setup_구성_실험/` 목록이 `README.md` 단일 |
| E5-2 | 그 폴더 README가 본체 이동 완료를 명시 | 확인됨 | `_test/20260806_setup_구성_실험/README.md:3-4, 10` |
| E5-3 | 올바른 루트는 `2_LDPC_light/` | 확인됨 | `README.md:23, 27`, `LDPC_base/run.py:9`, `run.py:262-263` |
| E5-4 | README 안내대로 하면 실패 | 확인됨 | 실행 출력 아래 인용 |
| E5-4 | 올바른 루트에서는 상대경로가 유효하고 실행이 끝까지 진행 | 확인됨 | 실행 출력 아래 인용 |

E5-4 실행 출력 (README 안내대로, `_test/20260806_setup_구성_실험/`에서):

```
$ python -m LDPC_base.run Ideas/vanilla/config.json
python.exe: Error while finding module specification for 'LDPC_base.run' (ModuleNotFoundError: No module named 'LDPC_base')
exit=1
```

E5-4 실행 출력 (`2_LDPC_light/`에서 실제 `Ideas/vanilla/config.json`을 `load_config` + `setup`, 파일 생성 없음):

```
H_matrix -> D:\...\2_LDPC_light\Ideas\vanilla\../../Input/H_matrix\example_18x147_z256.qc | exists: True
llr      -> D:\...\2_LDPC_light\Ideas\vanilla\../../Input/LLR\LLR_MATRIX_HD_1.txt | exists: True
setup OK: QC-LDPC: base 18x147, z=256, N=37632, K=33024, rate=0.8776, E(base)=553
          LLRMatrix LLR_MATRIX_HD_1.txt: mode=HD (ch1+th3), dv=[11, 4, 3, 2]~[11, 4, 3, 2], max_iter=20, groups: g1[1~1]x1, g2[2~20]x1
```

E5-4 전체 파이프라인 (같은 설정을 절대경로·scratchpad 출력으로 복제한 사본, `2_LDPC_light/`에서 실행):

```
decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=20
== channel=fixed_error (fixed_error) ==
  frames=    64 errors=  64 FER=1.000e+00 BER=6.261e-04 avg_decode_success_iteration=0.00 (14.3 f/s)
run dir: C:\...\scratchpad\e5\Sim_Output_scratch\260808_150726_vanilla
```

(FER 1.0은 TD-1의 별건 사안이며, 여기서는 경로와 실행 루트만 판정 대상이다.)

### H5 최종 판정: **확인됨**

사유: 지적된 서술이 그 위치에 그대로 있고, 그 경로에는 실행에 필요한 파일이 남아 있지 않으며, 안내대로 따라 하면 `ModuleNotFoundError`로 실패함을 실행으로 확인했다. 올바른 루트는 `2_LDPC_light/`이며 저장소 README와 `run.py` docstring이 이미 그렇게 적고 있다. 문맥상 참으로 읽힐 여지가 없다.

---

## H6 (TD-6) — `tools/H_mat_gen/README.md:15-17`의 미래 시제

### 1단계: 서술 존재 — **확인됨** (select_irregular.py는 라인 2칸 어긋남)

`tools/H_mat_gen/README.md:15-17` 원문:

```
- ㉰ **주의**: `select_irregular.py`는 구 본체 API(구 decoder/sim/channel) 기준 —
  `_test/20260806_setup_구성_실험/LDPC_base` 개정본을 본체로 반영할 때
  새 구조(채널 dict, decoder_main)로 손봐야 실행된다
```

문서 안 위치: 4행짜리 도구 표(`:5-10`) 다음의 불릿 4개(㉮㉯㉰㉱) 가운데 세 번째다. 문서 성격은 도구 폴더 안내이며, 앞 불릿 ㉮가 실행 예를 "repo 루트에서"로 적는 것으로 보아 저장소 전체 배치를 전제로 쓰였다.

`select_irregular.py`의 대응 서술은 지적된 14-16행이 아니라 **12-14행**에 있다:

```
주의 (2026-08-07): 이 스크립트는 구 본체 API 기준이라 **현재 실행 불가** — 새 구조
(채널 dict, decoder_main, LLR matrix 필수)로 손질 필요 (TODO 등록됨). import만
LDPC_base로 돌려놓은 상태다.
```

`_pm/TODO.md:22-24`는 라인이 일치한다:

```
- [ ] `tools/H_mat_gen/select_irregular.py`를 새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질
  - 현재 실행 불가 (구 API 기준, import만 LDPC_base로 보정된 상태)
  - irregular 재현 시드(103)는 `done/20260807_리뷰후속수정/` 문서 §6에 기록됨
```

### 2단계: 사실 불일치 — **확인됨**

- ㉮ 참조 경로 `_test/20260806_setup_구성_실험/LDPC_base`가 실재하지 않는다 (`ls -d` 결과 `No such file or directory`). 그 폴더에는 `README.md` 하나만 남아 있다
- ㉯ "본체로 반영"은 이미 끝났다. `git show --stat 2e600ea`가 `2_LDPC_light/LDPC_base/{__init__,channel,decoder,encoder,llr_matrix,run,sim}.py` 추가와 `2_LDPC_light/pcm.py → 2_LDPC_light/LDPC_base/pcm.py` 이동(R080)을 보여 준다. 커밋 메시지도 "LDPC_base, Ideas(vanilla reference), Input(H_matrix/LLR), config.json을 2_LDPC_light/ 바로 아래로 이동"이라고 적는다
- ㉰ 커밋 순서가 결정적이다. `3f596ef`(2026-08-07 15:36:53)가 이 README를 만들었고, 12분 뒤 `2e600ea`(15:48:52)가 반영을 끝냈다. 같은 커밋에서 `select_irregular.py`의 docstring은 미래 시제에서 현재 시제로 고쳐졌으나 README는 손대지 않았다. `git log -- tools/H_mat_gen/README.md`의 결과가 `3f596ef` 한 줄뿐이다

`2e600ea`의 `select_irregular.py` diff (같은 문장이 어떻게 갈렸는지):

```
-주의 (2026-08-07 이동): 이 스크립트는 구 본체 API(구 decoder/sim/channel) 기준이다.
-LDPC_base 개정본을 본체로 반영할 때 새 구조(채널 dict, decoder_main)로 손봐야 실행된다.
+주의 (2026-08-07): 이 스크립트는 구 본체 API 기준이라 **현재 실행 불가** — 새 구조
+(채널 dict, decoder_main, LLR matrix 필수)로 손질 필요 (TODO 등록됨). import만
+LDPC_base로 돌려놓은 상태다.
```

즉 README의 문장은 `3f596ef` 시점의 원문이 그대로 화석으로 남은 것이다.

"현재 실행 불가"가 사실인지도 확인했다. `select_irregular.py:39`는 `MinSumDecoder(code, max_iter=MAX_ITER)`로 호출하는데 현 시그니처는 `MinSumDecoder.__init__(self, code, llr_matrix)`이다. `max_iter` 인자를 받지 않으므로 호출 즉시 `TypeError`가 난다.

### E6-5 false positive 반증 시도

"tools 폴더의 독립 도구 관점에서 남은 작업을 가리킨다"고 읽으면 참이 되는가를 따졌다. 결론은 **그 읽기가 성립하지 않는다**.

- ㉮ 문장이 가리키는 남은 작업은 "손질"이지 "반영"이 아니다. README는 "개정본을 본체로 반영할 때 ... 손봐야 실행된다"고 적어 손질의 조건절로 **이미 끝난 반영**을 걸어 둔다. 조건절이 이미 참이 되어 버려 독자는 어느 시점을 기다려야 할지 알 수 없다
- ㉯ 조건절이 지목하는 경로 `_test/20260806_setup_구성_실험/LDPC_base`가 실재하지 않는다. 독립 도구 관점이라 해도 존재하지 않는 폴더를 기준점으로 삼을 수는 없다
- ㉰ 같은 사실을 `select_irregular.py:12-14`와 `_pm/TODO.md:22-24`가 현재형("현재 실행 불가")으로 적어 두었다. 세 문서가 같은 사실을 다르게 말하며, 셋 중 README만 어긋난다

프로젝트 CLAUDE.md 문장 작성 규칙 ㉮ 대비 판정: 규칙은 "과거가 어땠고 지금 어떻다는 서술을 코드와 문서에 남기지 않는다"이고 "그 문장을 처음부터 그렇게 설계됐던 것처럼 다시 쓴다"이다. README의 이 불릿은 이전 배치를 전제로 한 미래 계획 서술을 그대로 남겨 규칙을 위반한다. 수리는 조건절과 죽은 경로를 지우고 "`select_irregular.py`는 새 구조(채널 dict, `decoder_main`, LLR matrix 필수)로 손질해야 실행된다"처럼 현재 사실만 남기는 것이다.

### 증거표

| 증거 ID | 내용 | 판정 | 근거 |
|---------|------|------|------|
| E6-1 | 미래 시제 서술이 도구 안내 불릿 ㉰로 존재 | 확인됨 | `tools/H_mat_gen/README.md:15-17` |
| E6-2 | 참조 경로 `_test/20260806_setup_구성_실험/LDPC_base` 부재 | 확인됨 | `ls -d` 실패(exit 2), 해당 폴더 목록은 `README.md` 단일 |
| E6-3 | 본체 반영 완료 | 확인됨 | `git show --stat 2e600ea` (LDPC_base 7개 파일 A, pcm.py R080), `git show --stat 3f596ef` (tools/H_mat_gen 이동, README 생성) |
| E6-3 | README는 반영 커밋보다 12분 먼저 쓰였고 이후 갱신 없음 | 확인됨 | `git log --date=format` 3f596ef 15:36:53 / 2e600ea 15:48:52, `git log -- tools/H_mat_gen/README.md` 결과 1건 |
| E6-4 | 같은 사실을 코드와 TODO는 현재형으로 적음 | 확인됨 | `select_irregular.py:12-14` (지적 14-16에서 2칸 어긋남), `_pm/TODO.md:22-24` |
| E6-4 | "현재 실행 불가"가 사실 | 확인됨 | `select_irregular.py:39` `MinSumDecoder(code, max_iter=MAX_ITER)` vs 현 시그니처 `(self, code, llr_matrix)` |
| E6-5 | "남은 작업" 읽기로도 서술이 참이 되지 않는다 | 확인됨 (반증 실패) | 위 ㉮㉯㉰ |

### H6 최종 판정: **확인됨**

사유: 서술이 지적된 위치에 있고, 조건절이 가리키는 반영이 `2e600ea`로 이미 끝났으며, 참조 경로가 실재하지 않는다. 같은 커밋에서 코드 docstring만 현재형으로 고쳐지고 README가 누락된 이력까지 확인했다. 지적 라인 중 `select_irregular.py`만 실제 12-14행으로 2칸 어긋난다.

---

## 검증 중 발견한 곁가지 (참고)

- ㉮ `llr_matrix.py:70`의 에러 문구 "파일 매트릭스는 3-bit(th 3개) 전용"도 사실과 어긋난다. uniform 표시가 붙은 파일 매트릭스는 th 개수와 무관하게 로드된다. TD-3 수리 시 이 문구도 함께 다시 쓰는 것이 맞다
- ㉯ `run.py`의 false 분기는 `llr_matrix`의 `file` 하위 키를 전혀 쓰지 않고 `dir`만 쓴다. `_path_pair`를 거치지 않으므로 `file` 키가 없어도 동작한다. TD-4 수리 문구는 이 비대칭(`dir`는 쓰이고 `file`은 안 쓰임)을 그대로 적는 편이 정확하다

---

## 작업 위생

실행은 전부 scratchpad 사본 config로 수행했고, 저장소의 `Input/LLR/`과 `Sim_Output/`은 실행 전후 목록이 같다 (`Input/LLR` 3개 파일 동일, `Sim_Output` 항목 수 16 동일). `Ideas/vanilla/Sim_Output/`의 최신 항목은 `260808_132800_vanilla`로 이 세션 시작(15:07) 이전 것이다.

```
$ git status --short
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

시작 시점과 같은 3줄이다. 오염 없음.
