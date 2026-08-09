# r4 이후 변경분 리뷰 — Round 1 관점 도출 (agent_2)

> 대상: `git diff ea88882..HEAD -- 2_LDPC_light/` + 미커밋 `config.json`
> 작성 방침: 문제를 단정하지 않고 "어디를 어떤 기준으로 봐야 하는가"만 적는다.
> 가중치: 순수 이동(구 flat → `LDPC_base/`)은 가볍게, 델타 로직(균일 양자화 2건,
> 이름 일괄 수정, 요약 출력, 패키지 경계 신설)은 깊게 본다.

---

## 우선순위 요약

| 순위 | 관점 | 한 줄 |
|------|------|-------|
| 1 | P1 균일 양자화 매트릭스 합성의 수치 규약 | num_bits → th/edge_mag/num_param 파생이 "균일 n-bit"의 정의와 맞는가 |
| 2 | P2 save/load 왕복 충실도 | 파일을 거치며 잃거나 바뀌는 필드가 있는가 |
| 3 | P3 파일명이 의미를 결정하는 구조 | `uniform` 문자열과 모드 정규식이 유일한 판별 근거인 점 |
| 4 | P4 캐스케이드 th 개수 일반화의 파급 | `_vnu_quantize`, RESET, edge_mag 0 레벨 도입 영향 |
| 5 | P5 setup의 파일 생성 부작용 | 추적 대상 `Input/LLR/`에 산출물을 쓰는 정책과 재현성 |
| 6 | P6 config 검증 확장분 | `use_input_llr_matrix` 분기의 키맵·값 제약 커버리지 |
| 7 | P7 패키지 경계와 실행 진입점 | `LDPC_base` / `Ideas` / `tools` 세 갈래의 import 루트 정합 |
| 8 | P8 이름 일괄 수정의 완결성 | 의견1 항목별 반영 여부와 잔여 축약명 |
| 9 | P9 요약 출력의 사실 정확성 | setup 직후 출력과 summary.txt가 실제 실행값과 같은가 |
| 10 | P10 데이터 파일 무결성 | 새 `Input/` 3개 LLR 파일과 H-matrix의 자기 정합·상호 정합 |
| 11 | P11 문서와 코드 일치 | README·plan.md·차이.md가 델타 4~6을 반영하는가 |
| 12 | P12 새 문장 작성 규칙의 자기 적용 | 이번에 도입한 규칙을 이번 변경분 문서·주석이 지키는가 |
| 13 | P13 성능·메모리 스케일 | num_bits가 커질 때의 비용 |
| 14 | P14 실행 검증 | 두 경로(파일/균일)를 실제로 돌려 본 증거 |

---

## P1. 균일 양자화 매트릭스 합성의 수치 규약

**무엇을 보는가**: `make_internal_uniform_matrix()`가 만드는 값들이 "균일 n-bit 양자화"
라는 이름이 약속하는 바와 일치하는지, 그리고 디코더가 그 값을 소비했을 때 실제로
균일 양자화가 되는지.

- ㉮ `top_level = 2**(num_bits-1) - 1`, `th = [top_level..1]`, `edge_mag = [top_level..0]`의
  세 파생값이 서로 모순 없이 맞물리는가 (th 개수 = top_level, edge_mag 길이 = th 개수 + 1
  이라는 `__init__` 불변식)
- ㉯ num_bits 경계값에서의 동작: 2(top_level 1, th 1개), 1 이하(검증에서 차단되는지),
  큰 값(상한 없음)
- ㉰ docstring이 주장하는 "flip 도메인 값이 전부 정수라 캐스케이드가 |값|의 상한
  클리핑과 같아진다"가 성립하는 전제 확인. `sum_t`가 float32이고 ch가 테이블에서
  오는 값인데, 정수성이 깨질 경로가 있는지 (`_c2v_reconstruct` 출력, `np.roll` 이후,
  edge_mag/ th의 dtype 변환)
- ㉱ `max_value`/`min_value`에 `[max(top_level, channel_llr)] * num_param`과 `[0] * num_param`을
  넣은 근거. DAO 포맷에서 이 두 줄이 파라미터별 상·하한이라면 ch 칸과 th 칸의 의미가
  다른데 같은 값을 채우는 것이 의도인지
- ㉲ row 꼬리값 규약: csw `-1`, floor_flag `-1`이 DAO 파일의 관례와 같은 뜻인지
  (HD_0/HD_1 실파일의 값과 대조)
- ㉳ 단일 dv 구간 `[1, dv_max]`가 전 column을 덮는지. `code.col_deg.min()`이 1 미만인
  H-matrix가 들어오면 `col_dv_idx()`가 어떻게 되는가
- ㉴ `mode`가 2SD/3SD로 지정됐을 때 ch를 `[channel_llr] * ch_len`으로 복제하는 것이
  2SD/3SD의 ch 의미(region별 채널 LLR)와 맞는지, 아니면 디코더 미구현 에러 전에
  잘못된 파일이 먼저 만들어지는지

**대상**: `LDPC_base/llr_matrix.py:49-51, 209-231`, `LDPC_base/decoder.py:144-163`,
`Input/LLR/LLR_MATRIX_HD_0.txt`, `Input/LLR/LLR_MATRIX_HD_1.txt`

---

## P2. save/load 왕복 충실도

**무엇을 보는가**: e6282b1이 "합성 → 저장 → 로드"를 단일 경로로 만들었으므로,
파일을 거치는 동안 값이 보존되는지가 이 설계의 성립 조건이다.

- ㉮ `save()`가 쓰는 필드 순서와 `load()`가 읽는 순서의 1:1 대응 (num_param, num_dv,
  dv_from, dv_to, num_group, group_rows, group_type, num_restart, restart, max/min, rows)
- ㉯ restart가 없을 때 `save()`가 restart 줄을 생략하고 `load()`가 `num_restart > 0`에서만
  읽는 조건이 양쪽에서 같은가
- ㉰ `int(v)` 캐스팅의 손실 가능성: 합성값은 float64, 로드된 매트릭스의 `row_values`는
  float32다. 로드한 매트릭스를 다시 `save()`하면 어떤 값이 변하는가 (음수 -1의 절단
  방향 포함)
- ㉱ `__init__`이 보관하지 않는 필드가 `save()`에서 어떻게 복원되는가. rows 튜플의
  floor_flag는 `__init__`에서 버려지고 `save()`는 `-1`을 고정 기입한다. 파일 → 객체 →
  파일 왕복이 원본 파일과 같아지는지
- ㉲ `edge_mag`가 파일에 기록되지 않는 점. 로드 시 파일명으로만 복원되므로 왕복의
  정보 손실 지점이 어디인지 (P3와 연결)
- ㉳ 합성 직후 객체와 재로드 객체가 동등한지 검사하는 코드가 있는가. `setup()`은 합성
  객체를 버리고 재로드본만 쓰므로, 불일치가 조용히 통과할 수 있는 구간이 존재하는지
- ㉴ `save()`의 빈 줄 삽입 규칙이 `load()`의 빈 줄 무시와 DAO 실제 파서 양쪽에서
  모두 안전한지, 마지막 `rstrip("\n") + "\n"` 처리 포함

**대상**: `LDPC_base/llr_matrix.py:158-206, 233-259`, `LDPC_base/run.py:281-307`

---

## P3. 파일명이 의미를 결정하는 구조

**무엇을 보는가**: 모드(HD/2SD/3SD)와 레벨 구성(uniform 여부) 두 가지가 모두 파일명
문자열로 결정된다. 이 규약의 오탐·누락 경로.

- ㉮ `"uniform" in os.path.basename(path).lower()`의 오탐 범위. 사람이 만든 3-bit 파일에
  이 단어가 우연히 들어가면 `edge_mag`가 `[th 개수..0]`으로 잡히고 조용히 다른 디코딩이
  된다. 반대로 생성 파일을 사용자가 개명하면 `th_len != 3`에서 NotImplementedError가 난다
- ㉯ `_NAME_RE`가 `LLR_MATRIX_(HD|2SD|3SD)_`를 `search`로 찾는 점. 경로 중간이 아니라
  basename만 보므로 안전한지, `LLR_MATRIX_HD_uniform_6bit_ch8_iter120.txt`가 규칙에
  맞는지, 대소문자 무시가 의도인지
- ㉰ 생성 파일명 조립(`run.py:209-211`)과 로드 측 판별 규칙이 한 쌍으로 유지되는가.
  파일명 규약이 두 파일에 나뉘어 있는데 한쪽만 바뀌면 어디서 깨지는가
- ㉱ `use_input_llr_matrix=true`로 두고 생성된 uniform 파일을 직접 지정하는 사용법이
  성립하는가 (문서가 그 사용을 권하거나 막고 있는가)
- ㉲ 파일명에 담기지 않는 파라미터(mode 외 dv 범위, group 구성)가 나중에 달라졌을 때
  같은 이름으로 덮어써지는지

**대상**: `LDPC_base/llr_matrix.py:46, 158-206`, `LDPC_base/run.py:205-215`,
`Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`, `README.md:62-71`

---

## P4. 캐스케이드 th 개수 일반화의 파급

**무엇을 보는가**: 01251f5가 th 3개 고정을 일반 길이로 풀었다. 3개 전제를 남긴 자리와,
새로 생긴 magnitude 0 레벨의 영향.

- ㉮ `_vnu_quantize`의 루프 범위 `range(len(edge_mag)-2, -1, -1)`가 th 인덱스와 정확히
  대응하는지, "아래 레벨부터 덮어써서 가장 위의 참 조건이 최종값"이 C++ elif 체인과
  같은 결과인지 (비단조 th 포함)
- ㉯ 3 고정이 남은 자리 전수 확인. `decoder.py:256`의 주석 `(num_active_frames, num_dv, 3)`,
  `README.md`의 "VNU 출력 레벨 {7,5,3,1} 고정 — 3-bit 전용", `docs/차이.md` 9번 항목
- ㉰ `edge_mag[-1] == 0`이 도입되면서 생기는 동작 변화 지점:
  - ㉠ `new_mag = 0`인 메시지가 `_cnu_update`의 `<=` 비교에서 항상 min1을 차지하는 경로
  - ㉡ `vnu_out = sgn * 0`이 `-0.0`이 되어 `new_sgn = (vnu_out < 0)`가 항상 0이 되는 점
  - ㉢ `RESET = edge_mag[0]`가 3-bit의 7 대신 top_level이 되며 min1/min2 초기값,
    Edge Clear 후 C2V magnitude, restart 동작이 함께 바뀌는 범위
- ㉱ `th=-1` restart row 규약(전 메시지 최대 레벨)이 균일 매트릭스에는 restart가 없어
  적용되지 않는데, 두 경로에서 같은 코드가 다른 의미를 갖게 되는 지점이 있는지
- ㉲ `_validate`의 th 내림차순 경고가 균일 매트릭스에서 항상 통과하는지, 경고를
  `warnings.warn`으로 낸 선택이 배치 실행에서 묻히지 않는지

**대상**: `LDPC_base/decoder.py:118, 144-186, 208, 240-256`, `LDPC_base/llr_matrix.py:54-100, 150-155`

---

## P5. setup의 파일 생성 부작용

**무엇을 보는가**: e6282b1로 `setup()`이 실험 준비 단계에서 git 추적 대상 폴더에
파일을 쓴다. 부작용의 범위와 재현성.

- ㉮ 기존 동일 이름 파일을 조건 없이 덮어쓰는 정책. 사용자가 손댄 파일이 있을 때의
  처리, 덮어쓰기 전 확인이나 로그가 필요한지
- ㉯ 생성 위치가 `llr_matrix.dir`(없으면 `Input/LLR`)인 점. `use_input_llr_matrix=false`
  일 때 `llr_matrix` 키는 "무시"된다고 문서화됐지만 `dir`은 읽는다. 문서와 동작의 일치
- ㉰ 산출물이 `Input/`(추적 대상)에 쌓이는 것과 `.gitignore` 정책의 정합. 현재
  `Sim_Output/`, `out/`, `_test/`는 무시되지만 `Input/LLR/`은 추적된다. num_bits나 max_iter를
  바꿔 실험할 때마다 새 파일이 커밋 후보로 남는 구조가 의도인지
- ㉱ 커밋된 `LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`와 `config.json`의
  `internal_quantize.max_iter=120`이 어긋나 있는 점. 실행 시 iter120 파일이 새로 생기고
  iter30 파일은 남는데 이것이 의도된 상태인지
- ㉲ 실행 폴더에 저장되는 `config.json` 사본만으로 재현이 가능한가. 생성된 LLR
  파일 자체나 그 해시가 실행 산출물에 남는지 (`summary.txt` 내용 확인)
- ㉳ `os.makedirs(os.path.dirname(...), exist_ok=True)`가 dir이 빈 문자열인 경우를
  포함해 안전한지

**대상**: `LDPC_base/run.py:281-307, 517-568`, 루트 `.gitignore`, `Input/LLR/`

---

## P6. config 검증 확장분

**무엇을 보는가**: `use_input_llr_matrix` 분기가 생기며 검증 경로가 둘로 갈라졌다.
양쪽 가지의 커버리지가 대칭인지.

- ㉮ false 가지에서 `decoder_config["llr_matrix"]`가 dict로 남는데 `_check_keys`나
  `_path_pair` 검증을 받지 않는 점. 오타 키가 조용히 통과하는지
- ㉯ `_check_int` 호출들이 반환값을 버리고 `config`에 기본값을 되쓰지 않는 점.
  `max_frame_errors`, `max_frames`, `frames_per_batch`의 기본값 리터럴이 `load_config`,
  `run_experiment`, `_experiment_summary_lines` 세 곳에 각각 적혀 있어 단일 출처가 아닌 구조
- ㉰ `internal_quantize`의 값 제약 범위: `num_bits` 하한 2만 있고 상한 없음,
  `channel_llr` 하한 1, `max_iter` 하한 1. TODO의 "config checker 키별 허용값 확장"과
  겹치는 부분과 남는 부분
- ㉱ `decoder.max_iter` 금지 검사가 `_check_keys("decoder", ...)`보다 먼저 오는 순서.
  에러 메시지가 어느 쪽으로 나가는 게 사용자에게 유용한지
- ㉲ `generated_llr_matrix_path`를 `config["decoder"]`에 주입하는 것이 `_DECODER_KEYS`
  키맵과 충돌하지 않는지, 검증 후 주입이라는 순서 의존이 드러나 있는지
- ㉳ `_visible()`의 `_` 접두 무시 규칙이 중첩 객체(`H_matrix`, `llr_matrix`,
  `internal_quantize`, `channels[]`)에서도 일관되게 적용되는지
- ㉴ 미커밋 `config.json` 변경(`_desc` 첫 줄 분리)이 `_desc` 배열의 다른 항목들과
  들여쓰기·문장 단위 관례를 맞추는지

**대상**: `LDPC_base/run.py:64-255`, `config.json` (미커밋 diff 포함), `Ideas/vanilla/config.json`

---

## P7. 패키지 경계와 실행 진입점

**무엇을 보는가**: 2e600ea/3f596ef가 `LDPC_base/`, `Ideas/`, `tools/H_mat_gen/`
세 패키지를 만들었다. 각각이 가정하는 import 루트가 서로 다르다.

- ㉮ 실행 루트의 이중성: `run.py`는 `2_LDPC_light/`에서 `python -m LDPC_base.run`을
  전제하고(`Ideas.registry` 절대 import), `tools/H_mat_gen/*`는 repo 루트에서
  `python -m 2_LDPC_light.tools.H_mat_gen.*`를 전제한다(`from ...LDPC_base.pcm import`).
  두 전제가 한 저장소에서 공존 가능한지, 문서가 그 차이를 밝히는지
- ㉯ `2_LDPC_light`가 숫자로 시작해 일반 `import` 문으로는 쓸 수 없는 이름인 점.
  `-m`으로는 동작하더라도 상대 import 3단계(`...`)가 성립하는 조건이 무엇인지
- ㉰ `_resolve_decoder_class`의 ImportError fallback: `Ideas`가 없으면 vanilla를
  `MinSumDecoder`로 대체한다. `Ideas`는 있지만 그 하위 import가 실패하는 경우
  (예: `Ideas.vanilla.decoder`의 `from LDPC_base...`)에도 같은 fallback이 걸리는지
- ㉱ 아이디어 디코더 생성자 계약: `decoder_class(code, llr_matrix=llr_matrix)`가
  registry에 등록될 모든 클래스의 시그니처 전제가 되는 점이 문서화됐는지
- ㉲ `Ideas/vanilla/config.json`의 상대경로(`../../Input/...`, `Sim_Output`)가
  config 위치 기준 해석 규칙과 맞는지, 결과가 `Ideas/vanilla/Sim_Output/`에 쌓일 때
  `.gitignore`가 덮는지
- ㉳ `LDPC_base/__init__.py`의 `__all__`에 `run`, `llr_matrix`, `decoder`의 노출 여부가
  의도대로인지, `2_LDPC_light/__init__.py`가 하는 일과 겹치지 않는지

**대상**: `LDPC_base/run.py:258-278`, `LDPC_base/__init__.py`, `__init__.py`,
`Ideas/__init__.py`, `Ideas/registry.py`, `Ideas/vanilla/decoder.py`,
`tools/H_mat_gen/gen_example_code.py`, `tools/H_mat_gen/select_irregular.py`

---

## P8. 이름 일괄 수정의 완결성 (d42ca8c)

**무엇을 보는가**: 의견1의 지적 항목이 하나도 남지 않고 반영됐는지, 그리고 기계
치환의 후유증이 없는지.

- ㉮ 항목별 대조표를 만들어 확인: `decoder_cls→decoder_class`, `mx→llr_matrix`,
  `verbose→print_progress`, `rng→random_generator`, `unknown→unknown_log_items`,
  `fail_rows→fail_frame_details`, `agg_*→total_*`, `b→batch`, `res→decode_result`,
  `n_it→num_iterations_run`, `s→state`, `n_active→num_active_frames`,
  `frozenset→set`, `_make_channel_fn`을 변수로 받아 넘기기
- ㉯ 미반영으로 남은 지적: "`points`를 더 풀어써야 한다"는 요구가 JSON 스키마 키라서
  유지된 것인지, 유지 결정이 어딘가에 기록됐는지
- ㉰ 이동해 온 파일에 남은 축약명 스캔. `run.py:_plot_fer_curves`의 `r`, `xs`, `f`,
  `_dv_labels`의 `f`, `t`, `_write_iter_log`의 `k`, `d`, `pcm.py`의 `e`, `i`, `j`, `s`,
  `c4`, `llr_matrix.py`의 `m`, `i`, `off`, `r`. 이번 범위에 포함할지 판단
- ㉱ 치환 후유증 검사(gcm 규칙 4): 조사 어긋남, 이름 중복, 부분문자열 오염
- ㉲ 이름과 실제 의미의 일치: `total_active_frames`가 "합"인지 "iteration별 활성 수의
  누적"인지, `final_err_bits`가 "마지막 처리 iteration"의 값이라는 점이 이름에서 읽히는지

**대상**: `LDPC_base/sim.py`, `LDPC_base/run.py`, `LDPC_base/decoder.py`,
`LDPC_base/llr_matrix.py`, `LDPC_base/pcm.py`, `_pm/done/20260808_의견1_반영/의견1.md`

---

## P9. 요약 출력의 사실 정확성

**무엇을 보는가**: d42ca8c가 추가한 setup 직후 콘솔 출력과 `summary.txt`가 실제
실행에 쓰인 값과 같은지.

- ㉮ `_experiment_summary_lines`가 `.get(키, 기본값)`으로 다시 읽는 값과
  `run_experiment`가 실제로 쓰는 값이 항상 같은지 (P6 ㉯와 연결)
- ㉯ 요약에 LLR matrix 공급 경로(파일 로드인지 생성 후 로드인지)와 생성 파라미터가
  드러나는가. `LLRMatrix.summary()`가 name/mode/dv/max_iter/groups를 내는데
  `edge_mag`(레벨 구성)는 빠져 있어 균일 모드 실행 기록으로 충분한지
- ㉰ `channels_desc`가 points를 그대로 찍는데 스칼라 정규화·라벨 접미사(`_2`)가
  반영된 뒤 값인지
- ㉱ `decoder.max_iter`와 `llr_matrix.max_iter`를 각각 찍는 두 줄이 항상 같은 값인지
- ㉲ `summary.txt`의 `code commit` 해시가 실행 시점 작업트리 상태(미커밋 변경)를
  반영하지 않는 점이 재현성 기록으로 충분한지
- ㉳ `code.summary()`가 여러 줄을 반환해 `"\n".join(lines)`와 섞일 때 형식이 깨지지 않는지

**대상**: `LDPC_base/run.py:310-330, 413-421, 517-568, 571-581`,
`LDPC_base/llr_matrix.py:309-317`, `LDPC_base/pcm.py:summary()`

---

## P10. 데이터 파일 무결성

**무엇을 보는가**: `Input/` 아래 새로 들어온 파일 4개가 로더의 검증을 통과하는지,
그리고 서로 정합한지.

- ㉮ 각 LLR 파일의 자기 정합: 헤더 개수 필드와 배열 길이, row 길이 `num_dv*num_param+4`,
  group_rows 합 = row 수, 커버리지 1..max_iter 빈틈 없음, restart 그룹 단일 row/단일
  iteration, restart 그룹이 마지막이 아님
- ㉯ `LLR_MATRIX_HD_0.txt`의 dv 구간 `11/4/3/2`와 `example_18x147_z256.qc`의 실제
  column degree 분포가 전부 매칭되는지. 매칭 실패는 `col_dv_idx`에서 에러가 되므로
  두 파일은 한 쌍으로 검증해야 한다
- ㉰ `LLR_MATRIX_HD_1.txt`가 restart 없이 group 2개, max_iter 20인 구성이 README의
  "restart 없는 20-iter 테스트용" 서술과 맞는지
- ㉱ 균일 파일(`..._6bit_ch8_iter30.txt`)이 `make_internal_uniform_matrix(6, 8, 30, 4)`의
  산출과 정확히 일치하는지 (재생성 후 바이트 비교가 가능한 검증)
- ㉲ H-matrix `example_18x147_z256.qc`의 6줄 변경 내용. 헤더 `147 18 / 4 31 / 256`이
  실제 degree와 맞는지(`pcm.load`의 J/K 검사), "column block DV 내림차순 배치"
  전제가 실제 배치와 맞는지
- ㉳ TODO에 남은 "dv=2에서 ch=28은 반전 가능 조건 `ch ≤ 7·dv` 위반" 항목이 새로
  들어온 파일에도 그대로 있는지, 데이터로서 알고 있는 문제인지
- ㉴ 개행/인코딩: 파일이 탭 구분에 UTF-8인지, CRLF/LF 혼재가 `save()` 출력과 다르지 않은지

**대상**: `Input/LLR/*.txt`, `Input/H_matrix/example_18x147_z256.qc`,
`LDPC_base/llr_matrix.py:102-155, 262-272`, `LDPC_base/pcm.py:load()`

---

## P11. 문서와 코드 일치

**무엇을 보는가**: 델타 4~6이 도입한 새 동작이 문서 3종에 반영됐는지, 반대로
문서에만 남은 옛 서술이 있는지.

- ㉮ `README.md` "남은 근사/제한"의 "VNU 출력 레벨 {7,5,3,1} 고정 — 3-bit 전용"이
  균일 n-bit 모드 도입 후에도 맞는 서술인지
- ㉯ `docs/차이.md` 9번 "LLR 정밀도 빌드: 3-bit 전용(th 3개 아니면 에러)"과
  `edge_mag` 일반화의 관계. 차이 문서가 다루는 대상이 파일 경로 한정인지 명시됐는지
- ㉰ README의 JSON 스키마 예시(`max_iter: 120`)와 실제 `config.json`, 커밋된 생성
  파일(iter30)의 삼자 정합
- ㉱ README `Input/LLR/` 행이 커밋된 파일 3개 중 2개만 설명하는 점
  (uniform 파일 설명 유무)
- ㉲ `Ideas/vanilla/README.md`의 실행 안내 "실험 루트(`_test/20260806_setup_구성_실험/`)에서"가
  본체 반영 후 경로와 맞는지
- ㉳ `tools/H_mat_gen/README.md` ㉰의 "본체로 반영할 때 손봐야 한다"는 서술이
  이미 반영이 끝난 현재 상태와 맞는지
- ㉴ `docs/plan.md`의 §3.1 모듈 표(`mpi_runner.py`, `tools/peg.py`, `examples/fer_curve.py`)가
  삭제된 파일을 가리키는 점과, 문서 머리의 "이 문서의 구조 서술은 개편 전 기준"
  단서만으로 충분한지
- ㉵ 교체 지점 표가 README, `decoder.py` docstring, `Ideas/vanilla/README.md` 세 곳에
  중복 기재된 점. 정본이 어디인지와 동기화 비용

**대상**: `README.md`, `docs/plan.md`, `docs/차이.md`, `Ideas/vanilla/README.md`,
`tools/H_mat_gen/README.md`, `LDPC_base/decoder.py:1-56`

---

## P12. 새 문장 작성 규칙의 자기 적용

**무엇을 보는가**: 의견1이 도입하고 루트 `CLAUDE.md`에 등재된 세 규칙을 이번
변경분 자신이 지키는지. 규칙 도입 커밋의 산출물이 규칙 위반이면 규칙이 서지 않는다.

- ㉮ 규칙 ㉮(수리는 덧대기가 아니라 다시 쓰기, 과거·현재 서술 금지) 대조 대상:
  - ㉠ `README.md:6` "2026-08-07: `_test/...`의 개정본을 본체로 반영 (구 코드는 git 이력에 보존)"
  - ㉡ `docs/plan.md:4-6` "2026-08-07 구조 개편 ... 이 문서의 §3.1 모듈 표 등 구조
    서술은 개편 전 기준이며"
  - ㉢ `tools/H_mat_gen/select_irregular.py` docstring "현재 실행 불가 ... import만
    LDPC_base로 돌려놓은 상태다"
  - ㉣ `docs/차이.md` 머리말 "본체 커밋 72b825a에서 파생하여 2026-08-06 개정"
  - ㉤ `llr_matrix.py`, `decoder.py`, `pcm.py`의 "(사용자 결정 2026-08-06)",
    "(리뷰 F1 후속)" 같은 결정 이력 주석. 변경 이력은 `_pm/DONE.md`와 git이 담당한다는
    규칙과 어디까지 양립하는지 판단이 필요하다
- ㉯ 규칙 ㉯(규칙은 긍정문): "~하지 않는다" 뒤 줄표로 뒤집는 문형이 남은 곳
- ㉰ 규칙 ㉰(이름과 용어는 명확성 우선): 처음 등장하는 업계 용어를 풀어 썼는지
  (hook, EDGE, CSW, DAO, genie, dv, restart, floor flag, lifting, PEG)
- ㉱ gcm 문서 검사 루틴: 줄표(—)를 접속어로 쓴 곳, 나열 번호 누락, 항목별 줄바꿈 누락
- ㉲ 개인 프로젝트·개인 경로 언급 금지 규칙 대비 확인(`_test/...` 경로 언급 포함)

**대상**: 이번 변경분의 모든 `.md`와 모듈 docstring, 루트 `CLAUDE.md` 문장 작성 규칙 절

---

## P13. 성능·메모리 스케일

**무엇을 보는가**: 균일 n-bit 모드는 th 개수가 `2^(num_bits-1) - 1`로 지수 증가한다.
3-bit 파일 경로에서 잡힌 비용 가정이 그대로 성립하는지.

- ㉮ `_vnu_quantize`의 파이썬 루프 횟수가 th 개수만큼이고, 그것이
  iteration × column × edge 안쪽에 있는 점. num_bits 6(31회)과 8(127회)의 실측 비용
- ㉯ `cur_th`가 `(num_active_frames, num_dv, th_len)` 뷰인 점과 `row_th[table_row_idx]`의
  fancy indexing이 매 iteration 복사를 만드는지
- ㉰ `row_values` 크기 `(R, num_dv, num_param)`가 num_bits에 따라 커지는 범위
- ㉱ 균일 모드에서 `needs_csw`가 False인데도 `prev_csw`를 매 iteration 계산하는 비용
- ㉲ `frames_per_batch` 기본 128과 `(B, M_b, z)` 버퍼 5개의 메모리 (z=256, M_b=18 기준)

**대상**: `LDPC_base/decoder.py:144-163, 238-298`, `LDPC_base/llr_matrix.py:284-307`

---

## P14. 실행 검증 (교차 검증 축)

**무엇을 보는가**: 이 저장소에서 Python은 실행 가능하다. 리뷰가 정적 읽기로만
끝나지 않도록 최소 실행 세트를 정한다.

- ㉮ `python -m LDPC_base.run config.json` (파일 경로, HD_1, 20 iter)
- ㉯ `use_input_llr_matrix`를 false로 바꾼 실행 (생성 → 저장 → 로드 경로)
- ㉰ `python -m LDPC_base.run Ideas/vanilla/config.json` (아이디어 경로, registry 조회)
- ㉱ 두 경로의 산출물 비교: 생성된 LLR 파일을 `use_input_llr_matrix=true`로 다시 지정해
  같은 seed로 돌렸을 때 FER이 동일한지 (P2 왕복 충실도의 실측)
- ㉲ 커밋된 uniform 파일을 재생성해 바이트 단위로 같은지
- ㉳ 실행 루트를 바꿨을 때(repo 루트에서 실행) 나오는 에러가 안내로 충분한지 (P7)
- ㉴ 로그 전 항목을 켠 상태에서 CSV 열 구성과 dv 라벨이 LLR matrix의 dv 구간과
  맞는지 (`_dv_labels`)

**대상**: `2_LDPC_light/` 전체, 산출물은 `Sim_Output/`(git 무시)

---

## 이번 리뷰에서 가볍게 볼 범위

- ㉮ 구 flat 파일 → `LDPC_base/` 순수 이동분: `channel.py`, `encoder.py`, `pcm.py`,
  `sim.py`의 알고리즘 본문. r4까지의 리뷰와 자동 검증이 계보를 덮었다
- ㉯ 삭제된 파일(`examples/`, `llr/`, `mpi_runner.py`)은 참조 잔재만 확인 (P11 ㉴)
- ㉰ `_pm/` 아래 리뷰 기록 파일 이동(rename), `DONE.md`/`TODO.md` 갱신은 리뷰 대상 밖
