# 팀 D (data_docs) — Round 2 종합

- 작성: 2026-08-08 14:33:28
- 배정 관점: G(데이터 파일 무결성) + H(문서-코드 일치 + 문장 작성 규칙 자기 적용)
- 워커 3개: `worker_d_1.md`(관점 G), `worker_d_2.md`(관점 H 전반부), `worker_d_3.md`(관점 H 후반부)
- 총 발견 40건 → 중복 통합 후 **31건 (HIGH 9, MEDIUM 12, LOW 10)**

---

## 1. 워커 결과 요약

| 워커 | 범위 | 발견 | 핵심 |
|------|------|------|------|
| worker_d_1 | `Input/LLR/` 3파일, `Input/H_matrix/` 1파일, 추적 정책 | 6건 (HIGH 1, MEDIUM 3, LOW 2) | `_validate` 5제약·H-matrix 헤더·uniform 재생성은 전부 무결. dv=2 구간 `ch=28`이 반전 상한을 넘어 비트 11.6%가 영구 고정되는 것을 실행으로 실측 |
| worker_d_2 | `README.md`, `docs/plan.md`, `docs/차이.md`, 하위 README 2종, docstring | 19건 (HIGH 5, MEDIUM 11, LOW 3) | 균일 n-bit 도입 후에도 "3-bit 전용" 서술이 남았고, 본체 반영 후에도 `_test/...` 경로 안내가 남았다. 교체 지점 표 3곳은 완전 일치 |
| worker_d_3 | 문장 규칙 ㉮㉯㉰ 자기 적용, % 마커, 삭제 파일 대 TODO 정합 | 15건 (HIGH 5, MEDIUM 4, LOW 6) | % 마커와 치환 후유증은 0건. `llr_tables.py` 사문화 잔존과 `llr_tune.py` 기능 유실이 새 발견. 사용자 결정 필요 5건 제기 |

세 워커 모두 실행·파싱으로 근거를 남겼다 (`_validate` 실호출, `col_dv_idx` 147개 전수, uniform 파일 재생성 바이트 비교, 32레벨 매트릭스 복호 실행, `inspect.signature` 대조, `git check-ignore`/`git hash-object` 실측).

---

## 2. 팀 내 교차 분석

### 2-1. 세 워커를 붙여야만 나오는 결론 (단일 워커는 도달 못 함)

**배포 기본 config로 실행하면 결과가 무효다.**

워커 1은 데이터만, 워커 2는 config만 봤기에 각자는 이 결합을 만들지 못했다. 팀 리더가 `config.json`을 직접 확인해 연결했다.

- `config.json`: `use_input_llr_matrix: true`, `llr_matrix.file = "LLR_MATRIX_HD_1.txt"`, `channels = fixed_error [200, 300]`
- 워커 1 실측: 그 `HD_1.txt`의 dv=2 구간 `ch=28`이 반전 상한 `7·dv=14`를 넘어 `sum_t >= 28 − 2·7 = 14 > 0`이 항상 성립. dv=2 column 17개 × z=256 = **4352 bit(전체 37632 bit의 11.6%)가 어떤 iteration에서도 반전되지 않는다**
- 워커 1 실행 로그: 20 iteration 내내 `bit_err_dv2_mean = 34.500` 불변, 최종 잔여 에러 41.88 중 34.5(82%)가 고정 비트, **FER 1.0 수렴**

즉 저장소를 받아 `python -m LDPC_base.run config.json`을 그대로 돌리면 FER이 1.0으로 나오고, 그 원인은 알고리즘이 아니라 동봉 데이터다. `_pm/TODO.md:18-21`에 미착수 항목으로 등록돼 있어 신규 결함은 아니나, **기본 config가 그 파일을 가리킨다는 점은 어디에도 기록돼 있지 않다.**

### 2-2. 워커 간 심각도 불일치 4건 (코드 근거로 조정)

| 사안 | w1 | w2 | w3 | 팀 판정 | 조정 근거 |
|------|----|----|----|---------|-----------|
| `docs/plan.md` 구 구조 서술 | — | MEDIUM | HIGH | **HIGH** | 사실 관계는 양쪽 동일(파일 부재를 각자 실측). w2가 추가로 찾은 D2-11이 결정타 — 머리 단서가 "결정 이력(§1, §7)은 계속 유효"라고 **보증하는데** §7 #4 `max_iter = 120`이 현행 규약(`run.py:178-181`이 `decoder.max_iter`를 에러 처리)과 충돌한다. 단서가 틀린 정보를 보증하므로 단순 낡음이 아니다 |
| `llr_tables.py` | — | MEDIUM | HIGH | **분리** | 고아 모듈 존재 자체는 MEDIUM. `_pm/DONE.md:70`이 "llr_tables.py 삭제"라고 **사실과 다르게 기록**한 부분은 이력 문서 신뢰성 문제라 HIGH. 팀 리더가 `git ls-files`로 파일 추적 상태 재확인 |
| uniform `iter30` 고아 파일 | MEDIUM | MEDIUM | LOW | **MEDIUM** | w1의 근거가 가장 강함(`load_config` 실호출로 생성 파일명 `iter120` 확인 + `git check-ignore -v`로 추적 대상 확인 + dv_max 4/6/11 재생성으로 내용 상이 확인) |
| `README.md:15` Input/LLR 설명 | LOW | MEDIUM | — | **MEDIUM** | w2가 "생성 파일이 쌓이는 폴더라는 성격 자체가 없다"는 추가 사실을 확보. 사용자가 추적 폴더에 산출물이 쌓이는 것을 예상할 수 없다 |

### 2-3. 상호 확증 (독립 경로로 같은 결론)

- **"3-bit 전용" 서술이 거짓**: w1이 uniform 파일(th 31개, 32레벨)이 `make_internal_uniform_matrix` 산출과 **바이트 단위로 일치**함을 확인했고, w2가 그 32레벨 매트릭스로 8프레임 **전부 복호 성공**함을 실행으로 확인했다. 데이터와 실행 양쪽에서 이중 확증 → `README.md:162`, `docs/차이.md:25`는 사실과 다르다.
- **`_test/...` 경로 2건**: w2와 w3이 서로 다른 관점(사실 일치 / 문장 규칙)에서 같은 두 줄을 독립 지목했다. w2는 "따라 하면 실행 불가"로, w3은 "규칙 ㉮ 위반 + 미래 시제"로 판정. 원인이 같으므로 한 번의 수리로 둘 다 해소된다.
- **`select_irregular.py`**: w3이 `inspect.signature` 실측으로 실패 원인 3건(`max_iter` 키워드, `bsc_llr` 부재, `target_errors`/`batch` 키워드)을 뽑았고, `_pm/TODO.md:22-24`가 든 손질 방향 3가지("채널 dict", "decoder_main", "LLR matrix 필수")와 **일대일로 정확히 대응**함을 확인. TODO는 맞고 같은 내용을 담은 `tools/H_mat_gen/README.md`만 틀렸다.

### 2-4. 모순 없음으로 확인한 것

세 워커 사이에 사실 관계가 어긋난 곳은 없다. `Input/` 데이터의 무결성(w1)과 그 데이터를 서술한 문서의 부정확성(w2)은 서로 다른 층의 문제이며 충돌하지 않는다.

---

## 3. 발견 목록 (통합, 심각도순)

### HIGH (9건)

| # | 문제 | 위치 | 근거 | 출처 |
|---|------|------|------|------|
| TD-1 | 배포 기본 config가 가리키는 LLR 파일의 dv=2 구간 `ch=28`이 반전 상한 `7·dv=14`를 넘어 비트 11.6%가 영구 고정. 기본 실행이 FER 1.0으로 수렴 | `Input/LLR/LLR_MATRIX_HD_1.txt` row1·row2 13번째 값, `config.json` `decoder.llr_matrix.file`, 판정식 `decoder.py:142`, 합산 `decoder.py:266-279` | 대수: `sum_t >= 28 − 2·7 = 14 > 0` 항상 성립. 실측: 20 iteration 내내 `bit_err_dv2_mean=34.500` 불변. `HD_0.txt` row1·row3도 동일 위반. `_pm/TODO.md:18-21` 미착수 등록 | w1 F1 + 리더 |
| TD-2 | "VNU 출력 레벨 {7,5,3,1} 고정 (3-bit 전용)"이 사실이 아니다. 레벨 수는 `edge_mag` 길이가 정한다 | `README.md:162` | `decoder.py:144-163`이 `len(edge_mag)` 기준 캐스케이드. 32레벨 복호 실행 성공. 같은 README `:66-71`이 n-bit를 설명해 자기모순 | w2 D2-1 |
| TD-3 | "3-bit 전용 (th 3개 아니면 에러)"의 한정 조건 누락. 그 에러는 uniform 표시 없는 파일 로드에만 걸린다 | `docs/차이.md:25` (#9) | `llr_matrix.py:67-71`은 `edge_mag is None`일 때만 raise. `load()`는 `:170,202`에서 uniform 파일에 edge_mag를 채운다 | w2 D2-2 |
| TD-4 | "`llr_matrix` 키는 있어도 무시된다"가 사실이 아니다. `llr_matrix.dir`가 생성 파일 저장 폴더를 정한다 | `README.md:70`, 같은 서술 `run.py:17-19`, `config.json:19-20` | `run.py:206-208`. 실행 확인: dir 지정 시 그 폴더, 키 삭제 시 `<config dir>/Input/LLR` | w2 D2-3 |
| TD-5 | 실행 안내가 존재하지 않는 `_test/20260806_setup_구성_실험/`를 실험 루트로 지목 (따라 하면 실행 실패) | `Ideas/vanilla/README.md:13` | 현 실행 루트는 `2_LDPC_light/` (`README.md:23`, `run.py:9`). `Ideas/vanilla/config.json`의 상대경로는 실행으로 유효 확인 — README만 틀림 | w2 D2-5, w3 H1 |
| TD-6 | "본체로 반영**할 때** 손봐야 한다"는 미래 시제가 이미 끝난 반영을 가리키고, 비존재 경로를 참조 | `tools/H_mat_gen/README.md:15-17` | 반영 커밋 2e600ea·3f596ef. 같은 사실을 `select_irregular.py:14-16`과 `_pm/TODO.md:22-24`는 "현재 실행 불가"로 현재형 서술 | w2 D2-4, w3 H2 |
| TD-7 | plan.md 머리 단서가 "결정 이력 §7은 계속 유효"라고 보증하는데 §7 #4 `max_iter = 120`이 현행 규약과 충돌. 단서가 지목하지 않은 §3.1b(4행 전부)·§3.2·§5도 어긋남. 단서 자체가 규칙 ㉮가 금지한 덧대기 | `docs/plan.md:4-6, 129, 70-79, 84, 110-112` | `run.py:178-181`(JSON `decoder.max_iter`는 에러), `decoder.py:116`, `llr_matrix.py:92`. 기본 config의 `HD_1.txt` max_iter는 20. §3.1 표가 `config.py`/`mpi_runner.py`/`examples/fer_curve.py` 등 부재 파일을 현재 모듈로 열거 | w2 D2-11/12, w3 H3 |
| TD-8 | `_pm/DONE.md:70`의 "llr_tables.py 삭제" 기록이 사실과 다르다. 파일은 추적 중이고, 읽을 `llr/` 폴더는 삭제됐으며, import처는 0건 | `_pm/DONE.md:70`, `2_LDPC_light/llr_tables.py:1`, `docs/plan.md:56` | 리더가 `git ls-files`로 추적 재확인. import 전수 grep 0건. 파일 실물 / DONE.md / plan.md 세 곳이 서로 다른 이야기 | w3 H4, w2 D2-8 |
| TD-9 | `examples/llr_tune.py`의 LLR 파라미터 탐색 절차가 대체 없이 사라졌고 TODO 미등록 | 삭제 파일 `examples/llr_tune.py` (75줄), `_pm/TODO.md` | 균일 양자화 모드는 매트릭스를 하나 **생성**할 뿐 여러 후보를 FER로 **비교·선별**하지 않는다. `make_internal_uniform_matrix`에 탐색 기능 없음 | w3 H5 |

### MEDIUM (12건)

| # | 문제 | 위치 | 근거 | 출처 |
|---|------|------|------|------|
| TD-10 | 추적 폴더 `Input/LLR/`에 매 실행 생성물이 쌓이고 `.gitignore`가 덮지 않는다. 커밋본 `iter30`은 어떤 config도 참조하지 않는 고아이고, 파일명에 `dv_max`가 없어 H-matrix 교체 시 같은 이름이 다른 내용으로 덮인다 | `config.json:33`, `run.py:205-215, 301-302`, 루트 `.gitignore`, `Input/LLR/..._iter30.txt` | `git check-ignore -v` 추적 대상 확인. `load_config` 실행 시 생성명 `..._iter120.txt`. dv_max 4/6/11 재생성 내용 상이 | w1 F2, w2 D2-6/10, w3 L11 |
| TD-11 | `Input/LLR/` 설명이 커밋 3개 중 2개만 담고, 생성 파일이 쌓이는 폴더라는 성격이 없다 | `README.md:15` | `git ls-files Input/`에 uniform 파일 포함. HD_0/HD_1 서술 자체는 파일 내용과 일치 | w1 F6, w2 D2-7 |
| TD-12 | `save()`가 `floor_flag`를 원본과 무관하게 `-1`로 고정 기입하고 `__init__`은 저장조차 않는다. DAO 파일 왕복 시 필드 소실 | `llr_matrix.py:254-255`, `:57`, `:86-91` | floor=3 가상 파일 왕복 실측: `['7','1','1','3'] → ['7','1','1','-1']`. 현 3파일은 전부 -1이라 관측 영향 없음 | w1 F3 |
| TD-13 | `.gitattributes` 부재로 `Input/` 텍스트 개행이 git 설정에 좌우된다. `core.autocrlf=false`에서는 생성 때마다 추적 파일이 수정 상태 | 저장소 전체, `llr_matrix.py:258` | `git hash-object` 설정별 실측: `true/input` 일치, `false` 불일치. 현 저장소(`true`)에서는 깨끗 | w1 F4 |
| TD-14 | 등가 항목 #4가 RESET을 "EDGE 7", #7이 양자화를 "→7/5/3/1" 4레벨로 못 박는다 | `docs/차이.md:34, 37` | `decoder.py:208, 240` `RESET = edge_mag[0]` (6-bit 균일에서 31), `:154-157` 임의 길이 캐스케이드 | w2 D2-13/14 |
| TD-15 | 모듈 docstring "내부 합성 — **파일 없이** 균일 n-bit 양자화로 디코딩"이 현 흐름(합성 → 파일 저장 → 파일 로드)과 반대 | `llr_matrix.py:5-7` | 같은 파일 `:212-213`과 `run.py:294-304`가 저장 후 로드를 실행. 커밋 e6282b1 취지 | w2 D2-15 |
| TD-16 | th 배열 shape 주석이 `3` 고정 (실제 마지막 축은 `th_len`, 6-bit에서 31) | `decoder.py:256` | `llr_matrix.py:89` `row_th`의 마지막 축 = `th_len`. **팀 A 관점 B와 중복 배정** | w2 D2-16 |
| TD-17 | `run.print_progress`가 README 스키마 예시·설명 어디에도 없다 | `README.md:50-51, 78-81` | `run.py:68-69 _RUN_KEYS`, `:35`, `:373` | w2 D2-9 |
| TD-18 | 원본 HW의 `CH_HD {21,14,12,10}` 실값이 저장소에서 사라졌고 그 사실이 기록돼 있지 않다 | 삭제 파일 `llr/_hw_orig_ch.txt` | 저장소 전체 grep에서 이 값 0건. `plan.md:104`가 "사용자 공급 필요"라 적은 실값 중 CH 쪽의 유일한 사본이었다. `git show ea88882:...`로 복구는 가능 | w3 M2 |
| TD-19 | README 머리말에 날짜 + 변경 이력 + "구 코드" 서술 (규칙 ㉮ 위반, DONE.md 소관) | `README.md:6` | 동일 내용이 `_pm/DONE.md:50-58`에 이미 기록 | w3 M1 |
| TD-20 | 줄표(—) 144건, 가운뎃점(·) 17건이 접속어·나열 기호로 쓰였다 | `run.py`(40), `decoder.py`(25), `plan.md`(23), `README.md`(18), `llr_matrix.py`(13) 외 | 전수 카운트. 곱셈 기호 용법은 제외. **규칙 충돌로 결정 필요 (D5 참조)** | w3 M3 |
| TD-21 | 핵심 축약어 VNU·CNU·LLR·CSW·DAO·dv·th·ch·HD/2SD/3SD의 원 이름이 저장소 어디에도 없거나 첫 등장에서 140행 뒤에 풀린다 | `README.md`, `docs/차이.md` 전반 | Variable/Check Node Unit 표기 저장소 0건, quasi-cyclic 0건, log-likelihood ratio 0건. `hook`·`genie`·`PEG`는 규칙대로 풀어 쓴 모범 사례 | w3 M4 |

### LOW (10건)

`llr_matrix.py:187-188` max/min_value 길이 미검사(w1 F5) / `llr_matrix.py:4` docstring이 uniform 로드 경로 배제(w2 D2-17) / `README.md:117-125` 교체 지점 표에 정본 표시 없음(w2 D2-18) / `docs/차이.md:4-5` 파생 시점 서술이 이후 4커밋을 못 담음(w2 D2-19) / `select_irregular.py:12-14` 작업 경위 서술(w3 L1) / `docs/차이.md:5`(w3 L2) / `pcm.py:7-8` 폐기 포맷 스펙 보존(w3 L3) / `channel.py:16`·`차이.md:47` "기존 결정"(w3 L4) / `run.py:180-181` 부정 선행 에러 메시지(w3 L5) / 나열 번호·줄바꿈 누락 5곳(w3 L6: `README.md:150-151, 162-167`, `Ideas/vanilla/README.md:34-36`, `decoder.py:17-35`, `llr_matrix.py:34-35`) / `tools/H_mat_gen/`에 개명 미적용 축약명(w3 L7) / `README.md:19`·`TODO.md:48`의 `docs/review/` 안내가 최신 리뷰를 못 가리킴(w3 L10) / `gen_example_code.py` 출력이 `out/`인데 `Input/H_matrix/`로 옮기라는 안내 없음(w3 L12)

---

## 4. 문제 없음으로 확정한 범위

| 항목 | 확인 방법 |
|------|-----------|
| LLR 3파일의 `_validate` 5제약(겹침·커버리지·restart 단일 row/단일 iteration·restart 마지막 금지·ITER 연속) | 헤더 직접 파싱 + `LLRMatrix.load()` 실호출, 예외·경고 0 |
| H-matrix 헤더 `147 18` / `4 31` / `256` | 실측 col degree max=4, row degree max=31, 원소 2646=18×147, shift 전부 0~255, DV 내림차순 성립 |
| LLR ↔ H-matrix dv 매칭 | `col_dv_idx` 147개 column block 전부 매칭(미매칭 0). dv=11 미사용은 직전 리뷰(`_pm/done/20260806_review/`)에서 확정된 의도 |
| uniform 파일 재생성 | `make_internal_uniform_matrix(6, 8, 30, dv_max=4)` → `save()` 결과가 커밋본과 **바이트 완전 일치**. 기대값 8항목 전부 일치 |
| 현 3파일 왕복 무결성 | `row_values`/`row_csw`/`row_iter`/`restart_iters`/`edge_mag` 전부 보존. 바이트 차이는 전부 형식층(개행·빈 줄·trailing space) |
| 교체 지점 표 3곳 | `README.md:117-125` ↔ `decoder.py:47-55` 7행 문자열까지 동일. 6개 메서드 + `LLRMatrix.row_index` 전부 실존 |
| % 마커 | `2_LDPC_light/` 전체 grep, 단어 뒤 `%` **0건** (검출 104건은 전부 `strftime` 포맷과 리뷰 기록 안의 C++ 인용) |
| 기계 치환 후유증 | d42ca8c 일괄 개명 7종을 `LDPC_base/` 전 파일에서 확인. 조사 어긋남·이름 중복·부분문자열 오염 0건 |
| `select_irregular.py` 상태 대 TODO | 최초 실패 `:39` `TypeError`, 원인 3건이 `TODO.md:22-24`의 손질 방향 3가지와 일대일 대응. **완전 일치** |
| README ↔ TODO 후순위 로그 7종, 출력 산출물 7종, 채널 3종 표 | 각각 `TODO.md:28-29`, `run.py:517-567`, `channel.py`와 대조 일치 |
| `gen_example_code` 실행 명령 | `python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code`를 repo 루트에서 실제 실행 성공 |

---

## 5. 사용자 결정이 필요한 사안 (6건)

| # | 사안 | 선택지 |
|---|------|--------|
| D1 | `docs/plan.md`의 성격 규정 (TD-7의 근본 해소책) | ㉮ §3.1·§3.1b 표를 현행 구조로 다시 쓰고 머리 단서 삭제 ㉯ plan.md를 결정 이력 전용으로 못 박고 §3·§5의 구조 서술 삭제(구조는 README 단일 정본). 지금처럼 단서만 붙은 상태는 어느 쪽도 아니다 |
| D2 | 코드 docstring의 "사용자 결정 (YYYY-MM-DD)" 표기 존폐 | `llr_matrix.py:15,27,29,32`, `pcm.py:7,15`, `decoder.py:141`, `channel.py:1,98` 외 20건 이상. 결정의 **근거**를 코드에 남기는 것은 유용하나 **날짜**는 이력에 가깝다. 날짜만 제거 / 통째로 유지 / 통째로 제거 |
| D3 | `docs/plan.md:63`의 결정 번복 서술 위치 | 결정 이력 절(§7)로 이동 / 현재 상태 서술로 다시 쓰기 |
| D4 | `Ideas/vanilla/README.md:34-35` 문형 | 규칙 ㉯의 금지 문형(뒤집기)에는 해당하지 않으나 부정 선행이다. 긍정문으로 다시 쓸지 |
| D5 | 줄표·가운뎃점 용법 규칙 명문화 (TD-20의 전제) | 글로벌 검사 루틴 1항은 "줄표를 접속어로 쓴 곳은 접속사·쉼표·괄호로 바꾼다"인데, 프로젝트 `CLAUDE.md` 규칙 ㉯는 "줄표 뒤에서 뒤집는 문형"만 금지한다. 144건 전부 수리 / 프로젝트 규칙을 "줄표는 부연에 한해 허용"으로 명문화. **결정 없이 부분 수정하면 문서마다 문체가 갈린다** |
| D6 | `Input/LLR/` 생성 산출물의 추적 정책 (TD-10의 전제) | ㉮ 생성물을 `.gitignore` 대상으로 돌리고 사람이 넣는 입력만 추적 ㉯ 파일명에 `dv_max`를 넣어 내용 식별성 확보 ㉰ 생성 위치를 `Sim_Output/` 계열로 이동 |

---

## 6. 미커버 영역

| 영역 | 사유 / 인계처 |
|------|--------------|
| 미커밋 `config.json` `_desc` 변경 1건의 문장 규칙 준수 여부 | 워커 3이 줄표 카운트에만 포함하고 정면 판정하지 않았다. 팀 B(관점 C/F) 범위와 경계 |
| `docs/차이.md` 전 항목(#1~#10) 대 코드 일대일 대조 | 표본(#4, #7, #9, #10)만 수행. 나머지 항목의 사실성 미확인 |
| `mode = 2SD/3SD`로 합성한 매트릭스의 데이터 무결성 (`ch_len` 2/4 경로) | 팀 A(관점 A) 범위. 팀 D는 HD 경로만 검증 |
| `decoder.py:256` shape 주석 (TD-16) | 팀 A 관점 B와 중복 배정. 팀 A 결과와 대조 필요 |
| `Ideas/` 최상위 README 부재 | `git ls-files` 결과 `Ideas/__init__.py`, `Ideas/registry.py`만 존재. 부재가 의도인지 미판정 |
| `.gitattributes` 도입 (TD-13) | 저장소 전역 정책이라 `2_LDPC_light/` 리뷰 범위를 넘는다. 루트 `_pm/`으로 인계 권고 |
| TD-1의 데이터 수정안 (`ch` 값 재설정) | 데이터 최적화는 `_pm/TODO.md:18-21`의 미착수 작업 본체. 이 리뷰는 "기본 config가 그 파일을 가리킨다"는 사실 기록까지만 수행 |

---

## 7. 우선 조치 권고

- 1. **TD-1** — 기본 config가 FER 1.0을 내는 데이터를 가리킨다는 사실을 `README.md`나 `_pm/TODO.md`에 명시한다 (데이터 수정 전까지의 최소 조치). 이 커브를 아이디어 비교의 기준선으로 쓰면 안 된다
- 2. **TD-2, TD-3, TD-4** — 사실과 다른 서술 3건. 사용자가 문서를 믿고 따르면 틀린 판단에 이른다
- 3. **TD-5, TD-6** — `_test/...` 경로 2건. 규칙 ㉮의 "처음부터 그렇게 설계됐던 것처럼 다시 쓴다"를 적용하면 한 번에 해소된다
- 4. **TD-8, TD-9** — `llr_tables.py` 존폐 결정과 `llr_tune.py` 탐색 기능의 TODO 등록
- 5. **TD-7 (D1)** — plan.md 성격 결정. 이것이 정해져야 TD-19(README 머리말) 처리 방향도 따라 정해진다
- 6. **TD-20 (D5), TD-21** — 규칙 확정 후 일괄 처리. 144건이므로 규칙 없이 손대면 안 된다
