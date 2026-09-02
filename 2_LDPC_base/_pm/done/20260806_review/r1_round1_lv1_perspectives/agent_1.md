# 2_LDPC_light 개정본(`_test/20260806_setup_구성_실험/LDPC_base/`) 리뷰 — Round 1 관점 도출 (agent_1)

> 작성: 2026-08-06 22:50:10
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/` 아래 `LDPC_base/*.py`, `config.json`, `Input/`
> 성격: **관점 도출 전용**. "어디를 봐야 하는가"만 적으며 문제 판정과 수정 제안은 하지 않는다.
> 리뷰 라운드: Round 1 (관점 도출), 레벨 1

---

## 0. 이 변경의 리스크 지형 (관점 선정 근거)

이 개정본은 세 가지 성격이 겹쳐 있고, 각각 리스크의 종류가 다르다.

- ㉮ **대조군이 코드 바깥에 있다** — 채널 3종과 syndrome-aided 디코딩은 "원본 C++과 같게 만든 것"이 존재 이유다. 따라서 Python 안에서 자체 정합성이 맞아도 C++ 원문과 어긋나면 그대로 무효다. 원본은 `0_LDPC_original/`에 있으나 이 환경에서 빌드와 실행이 금지되어 있으므로(루트 `CLAUDE.md` 공통 규칙 ㉮), 검증 수단은 **소스 대조뿐**이다.
- ㉯ **본체를 대체할 예정이다** — 이 폴더의 코드가 `2_LDPC_light/` 본체의 새 원본이 된다(실험 README "구성"). 그런데 본체에는 이 개정본이 복사해 오지 않은 `examples/`, `tools/`, `mpi_runner.py`, `llr/`가 남아 있고, 이들은 구 인터페이스(`code_file`, `target_errors`, BSC/AWGN 채널, `llr_profile`)에 의존한다. 반영 시점의 파손 범위가 코드 자체의 정확성과 별개의 축이다.
- ㉰ **토이 데이터로만 돌았다** — 검증 기록(실험 README "검증 기록")은 18×147 예시 부호와 자작 LLR matrix 2개에 한정된다. 루트 `CLAUDE.md` ㉰가 요구하는 "외부 H-matrix와 파라미터를 넣어도 동작"이라는 목표 기준에서, 입력 가정이 어디까지 하드코딩되어 있는지가 별도 확인 축이다.

아래 관점 P1~P12는 이 세 축(C++ 대응, 본체 반영, 입력 일반성)에 자체 정확성 축을 더해 배치했다.

---

## 1. 관점 목록

### P1. C++ 대응 정확성 — syndrome-aided HD 디코딩 본체

`_decode_matrix()`가 개정의 핵심이며, 실험 README와 `차이.md` §2가 "등가"로 선언한 13개 항목이 모두 이 함수 안에 있다. 선언이 실제 C++ 원문과 맞는지를 함수 단위로 재대조한다.

| 확인 항목 | 대상 |
|---|---|
| flip 도메인 채널 항이 "항상 +ch"인지. `total`을 `ch_cur[:, dvmap[j]]`로만 초기화하고 read bit `r`을 부호로 싣지 않는 구조가 `VN_Cal_HD`의 채널 기여 처리와 같은지 | `decoder.py:384-396` / `0_LDPC_original/decoder.cpp:3973` `VN_Cal_HD` |
| VN 판정 `flip = total <= 0` (동점 반전)의 비교 연산자와 경계 처리 | `decoder.py:398` / `decoder.cpp:3973` `VN_Cal_HD` 내 판정부 |
| C2V sign이 `synd ^ csum ^ esgn`이고, edge clear iteration에서 `esgn`이 0이라 자동으로 `synd`만 남는 구조가 `C2V_Cal_New_Sgn`의 인자 구성과 일치하는지. 특히 `iter` 인자가 원본에서 무엇을 분기시키는지 | `decoder.py:393` / `decoder.cpp:2299` `C2V_Cal_New_Sgn(int iter, int synd, int check_sum, int edge_sgn, int col_idx)`, `decoder.cpp:2341` `C2V_Cal` |
| Edge Clear 조건이 `it == 1 or mx.is_restart(it)`인 것. 원본에서 `Clear_Edge_Restart()`가 호출되는 시점(iteration 진입 시점인지 특정 column 시점인지)과, 그 iteration **전체**에서 remove-old가 생략되는지 아니면 클리어 이후 첫 접촉 edge만 생략되는지 | `decoder.py:373-379`, `decoder.py:413-417` / `decoder.cpp:709` `Clear_Edge_Restart`, 호출 지점 전수 |
| `min1`/`min2` 클리어 값이 `RESET = edge_mag[0] = 7`(V_VERY_STRONG)인 것, `pos`를 -1로 두는 것이 `Get_Default_Min_Pos`와 결과적으로 같은지 | `decoder.py:353`, `375-379` / `decoder.cpp` `Get_Default_Min_Pos`, `Clear_REG_min_*` 계열 |
| insert-new의 `<=` 비교와 "min1 교체 시 min2를 RESET으로" 규칙이 원문 그대로인지, `update_flag`/`cur_pos_p2` 같은 원본 인자가 재현 대상에서 빠져도 되는지 | `decoder.py:418-425` / `decoder.cpp:3514` `CNU_Update_New_Mag(v2c_mag, min1_value, min2_value, min1_pos, cur_pos, cur_pos_p2, update_flag, row_idx)` |
| remove-old에서 `csum ^= esgn` 후 `was1 = (p == e)`이면 `m1 <- m2`, `m2 <- RESET`. 원본이 min2를 어떤 값으로 되돌리는지, `col_idx` 인자가 무엇을 분기시키는지 | `decoder.py:413-417` / `decoder.cpp:3476` `CNU_Remove_Old_Sgn(iter, pre_v2c_sgn, check_sum, col_idx)` |
| VNU 양자화 입력이 `raw = total - c2v`(= sum_t − VNU_in)이고 그 **절대값**을 th와 비교하는 것, 그리고 `raw == 0`일 때 sign을 `c2v`에서 가져오는 규칙 | `decoder.py:90-102`, `406-407` / `decoder.cpp:3973` `VN_Cal_HD`의 VNU 출력 양자화부(본체 plan.md는 4080-4120 구간으로 지목) |
| CSW 정의 `Σ(csum ^ synd)`와 갱신 시점(column 루프 종료 후 iteration 끝). 원본에 `Compute_CSW`와 `Compute_CSW_Auto` 두 개가 있는데 `__AUTO_LLR_OPT__` 빌드가 어느 쪽을 쓰는지, 두 함수의 정의가 같은지 | `decoder.py:427` / `decoder.cpp:7293` `Compute_CSW`, `decoder.cpp:7340` `Compute_CSW_Auto` |
| iteration 1 진입 시 `prev_csw = |synd|`라는 전제. 원본에서 `prev_CSW`가 세팅되는 시점과 `Get_Cur_LLR_Idx_FILE(iter)` 호출 시점의 선후 관계(같은 iteration 안에서 갱신된 값을 쓰는지, 직전 iteration 값을 쓰는지) | `decoder.py:355`, `380` / `decoder.cpp:6973` `Get_Cur_LLR_Idx_FILE` 호출 지점, `prev_CSW` 대입 지점 전수 |
| syndrome을 `H·r`로 직접 계산하는 대체가 원본 iteration 0(`VN_Cal_Pre` → check_sum 누적 → syndrome 레지스터 복사)과 실제로 등가인지. 특히 `VN_Cal_Pre`가 실어 보내는 값이 read bit 부호만인지, 채널 magnitude도 섞이는지 | `decoder.py:354` / `pcm.py:78-85` `syndrome()` / `decoder.cpp:3554` `VN_Cal_Pre` |
| 성공 판정(genie)이 **column 루프 안**에서 `frame_err |= bit_err.any()`로 누적되는 구조. iteration 경계 스냅샷이 아니라 column별 중간 상태를 OR로 모으므로, 앞 column에서 에러였다가 뒤 column 처리로 정정된 프레임의 판정이 어떻게 되는지, 그리고 이 정의가 `차이.md` §1 #7의 genie 서술과 같은지 | `decoder.py:398-402`, `431-434` / `차이.md` §1 #7 / 본체 `docs/plan.md` §7-1 |
| `cn_mag_fn()`(논문 아이디어 훅)이 `_decode_matrix()`에서는 호출되지 않음. 다른 두 경로에는 있음 | `decoder.py:105-108` vs `decoder.py:392`, `261-262`, `162-163` |

### P2. C++ 대응 정확성 — 채널 3종

`channel.py` 전체가 신규다. 세 함수 모두 원본의 대응 함수가 명시되어 있으므로 원문 대조가 가능하다.

| 확인 항목 | 대상 |
|---|---|
| `qfunc_inv` 계수 6+4개가 원본과 자리까지 같은지, 정의역(p 범위)과 분기(원본에 low/high 구간 분기가 있는지) | `channel.py:24-34` / `0_LDPC_original/channel.cpp` `qfunc_inv` |
| `dev_from_rber`의 변환식 `snr = qinv(p)^2/2`, `dev = sqrt(1/(2·snr))`가 원본 `dev_from_RBER`와 `SNR_from_RBER`의 조합과 같은지(rate 반영 여부, Eb/N0 대 Es/N0 구분) | `channel.py:37-40` / `channel.cpp` `dev_from_RBER`, `SNR_from_RBER` |
| BPSK 매핑 방향(`0 → +1`)과 hard decision 규칙. 코드 주석은 "C++: cwr >= 0 → HD 0"인데 구현은 `hd = (cwr < 0)`. 경계값 0의 처리와 원본 부등호 방향 | `channel.py:50-52` / `ecc_top.cpp:1795` `Make_Dec_Input_AWGN_Quantize`, `ecc_top.cpp:1828` 이전의 `Make_Dec_Input_AWGN` |
| `_R_OFFSET` 값(2SD 0.35, 3SD 0.15/0.35/0.55)과 임계 `th = 2·r_offset/var`가 원본 `Set_R_Offset`/`Set_LLR_Th`와 같은지, 원본이 LLR 크기와 비교하는지 수신값 자체와 비교하는지 | `channel.py:21`, `56-57` / `channel.cpp:11-29` `Set_R_Offset`, `Set_LLR_Th` |
| 2SD/3SD region 판정의 sd/cc 의미 배정. 3SD에서 `cc[m >= th3] = 1`(very strong)과 `cc[m < th1] = 1`(very weak)이 같은 배열에 겹쳐 쓰이는 구조가 원본 `Get_Mag_3SD`의 region 코드와 일대일 대응하는지 | `channel.py:58-67` / `channel.cpp` `Get_Mag_2SD`, `Get_Mag_3SD` |
| fixed_error의 e1/c1 배정과 위치 뽑기 길이(`err_pos_len = e1`), strong_error의 e2/e1/c2/c1 round 규칙과 `err_pos_len = e2+e1+c1` | `channel.py:76-114` / `ecc_top.cpp:1854-1881` |
| strong_error에서 뽑힌 위치 리스트의 **슬라이스 의미**. Python은 `[0:e2)`=strong 에러, `[e2:e2+e1)`=weak 에러, `[e2+e1:e2+e1+c1)`=weak 정정으로 가정하는데, 실제 적용 함수가 어떤 순서로 소비하는지 | `channel.py:109-112` / `ecc_top.cpp:1687-1795` `Make_Dec_Input_Fixed_4KB`(인자 순서 `c1,c2,c3,c4,e1,e2,e3,e4`) |
| SD 초기값을 전부 1(strong)로 두고 일부만 0으로 내리는 방식이 원본의 `SD_input[n] = 1` 초기화와 같은지, CC_input을 None으로 두는 것이 2SD에서 문제 없는지 | `channel.py:107-114` / `ecc_top.cpp:1847-1853` |
| `Set_Real_Err_Pos_4KB`(쇼트닝/펑처링 위치 보정)를 항등으로 간주한 전제. `len_noPS = N` 가정이 실물 파라미터에서도 성립하는지 | `channel.py` 모듈 docstring / `ecc_top.cpp:1839`, `Set_Real_Err_Pos_4KB` |
| `_rand_positions`가 `argpartition`으로 k개를 뽑음. 뽑힌 k개 집합의 균일성과 별개로, **k개 내부의 순서**가 무작위인지(위치 인덱스에 상관된 순서인지)가 strong/weak 슬라이스 배정의 편향으로 이어지는지 | `channel.py:71-73` / `random.cpp` `rand_sel_ep` |
| 경계 입력: `n_err = 0`(`argpartition(kth=-1)`), `n_err > N`, `n_err`가 실수로 들어온 경우, `E`가 `N`과 같아 `c1 = 0`이 되는 경우 | `channel.py:73`, `103-109` |
| all-zero codeword 전제가 채널에 남아 있는지. `cw`를 그대로 받아 flip하는 구조는 일반 codeword에도 성립하지만, 디코더의 genie 판정(`bit_err = r_bit ^ flip`)은 all-zero를 하드코딩 | `channel.py:82`, `107` / `decoder.py:399` / `encoder.py:16-19` |

### P3. LLR_MATRIX 로더의 포맷 정합과 런타임 선택 규칙

`llr_matrix.py`는 DAO 산출물 포맷을 읽는 신규 파서다. 포맷 원문(DAO 측 `DAO_LLR_MATRIX.py Read_Input_LLR_Matrix`)이 이 저장소 안에 없으므로, 확인 수단은 헤더 서술, 실제 파일 2개, C++ 소비 측(`Get_VNU_LLR_SET_FILE`, `Get_Cur_LLR_Idx_FILE`) 세 가지다.

| 확인 항목 | 대상 |
|---|---|
| 필드 순서와 개수가 원 포맷과 같은지. `num_restart = 0`이면 restart_iter 줄 자체가 없다는 가정(HD_1.txt가 그 형태)이 포맷 정의와 맞는지, `num_restart > 0`인데 줄이 비었을 때의 동작 | `llr_matrix.py:104-136` / `Input/LLR/LLR_MATRIX_HD_0.txt`, `LLR_MATRIX_HD_1.txt` |
| 모든 토큰을 `int()`로 파싱. 실수 값이나 16진 표기가 올 가능성, 그리고 빈 줄을 전부 무시하는 방식이 "빈 줄이 구분자 역할을 하는" 포맷에서 안전한지 | `llr_matrix.py:105-106` |
| `max_value`/`min_value`/`floor_flag`/`row_csw`(HD 파일에서 -1)를 읽고 나서 어디에도 쓰지 않는 것. 원본이 이 값들로 클리핑이나 분기를 하는지 | `llr_matrix.py:54-55`, `133` / `decoder.cpp:7074` `Get_VNU_LLR_SET_FILE`, `decoder.cpp:6973` |
| ch/th 분해 규칙 `ch_len = 2^(init_n-1)`(HD 1, 2SD 2, 3SD 4)와 `th_len = num_param - ch_len`. 원본이 같은 순서(ch들이 앞, th들이 뒤)로 읽는지 | `llr_matrix.py:31`, `59-60` / `decoder.cpp:7074-7139` |
| `_group_of_iter`가 **첫 매칭 그룹**을 고르는 반면, 원본은 `g = num_group-1`부터 내려오며 첫 매칭에서 break(= 가장 높은 인덱스 그룹). 그룹 구간이 겹칠 때 결과가 갈리는지, `_validate`의 연속성 검사가 겹침을 완전히 배제하는지 | `llr_matrix.py:154-158`, `80-87` / `decoder.cpp:6985-6999` |
| CSW 타입 row 선택. Python은 `range(a+1, b)`를 올라가며 `csw <= row_csw[r]`인 마지막 r을 남기고, 원본은 `i = num_candidate-1`부터 내려오며 첫 매칭에서 break. 두 방식이 임계값이 단조가 아닐 때도 같은 답을 주는지, 그룹 첫 row(index a)가 후보에서 빠지는 것이 원본과 같은지 | `llr_matrix.py:160-177` / `decoder.cpp:7059-7068` |
| `GROUP_TYPE_ITER`가 아니어도 `b - a == 1`이면 iteration 분기로 처리하는 단축 경로가 원본과 등가인지 | `llr_matrix.py:168` / `decoder.cpp:7051-7068` |
| `_validate`가 추가한 제약(그룹 iter_start가 직전 iter_end+1이어야 함, restart 그룹은 단일 iteration 단일 row여야 함, restart 그룹이 마지막이면 안 됨)의 근거가 포맷 정의에서 나오는지 아니면 이 구현의 자체 가정인지. 정당한 DAO 출력이 이 검사에 걸릴 여지 | `llr_matrix.py:73-94` |
| `col_dv_idx`의 구간 매칭(`dv >= dv_from & dv <= dv_to`)과 첫 매칭 채택. 파일의 `dv_from`/`dv_to`가 내림차순 배열이고 값이 같은 싱글턴(11,4,3,2)인 점, 구간이 겹치거나 역전(`dv_from > dv_to`)된 파일에 대한 방어 | `llr_matrix.py:139-149` / `Input/LLR/*.txt` 3~4번째 줄 / `decoder.cpp:7078-7082` |
| `max_iter = row_iter[-1, 1]`이 "마지막 row가 iteration 순서상 마지막"이라는 전제에 의존. 그룹이 iteration 순서와 다르게 나열된 파일에서의 동작 | `llr_matrix.py:63` |
| `is_restart(it)`가 `set` 멤버십인데 저장은 `int()` 변환, 조회는 Python `int`. numpy 정수가 들어오는 경로가 있는지 | `llr_matrix.py:53`, `151-152` / `decoder.py:373` |
| `needs_csw` 프로퍼티가 정의만 되고 호출되지 않음 | `llr_matrix.py:179-183` (호출처 전수) |
| 파일명으로 모드를 판별하는 설계의 견고성(대소문자, 경로에 `LLR_MATRIX_HD_`가 우연히 포함되는 경우, 이름 규칙을 지키지 않은 외부 파일) | `llr_matrix.py:34`, `99-103` |

### P4. 실행 흐름과 JSON 설정 계약

`run.py`가 4단계로 재편되면서 설정 키가 다수 개명되었다(`code_file` → `H_matrix`, `target_errors` → `max_frame_errors`, `stop_below` → `stop_below_fer`). 계약이 문서, 검증 코드, 실제 사용 사이에서 일치하는지가 축이다.

| 확인 항목 | 대상 |
|---|---|
| `load_config`가 검증하는 범위와 놓치는 범위. `H_matrix` 키 없음, `channel` 키 없음, `points`가 빈 리스트, `run` 하위 키 오타(조용히 기본값 사용), `output.csv_prefix` 없음 | `run.py:34-65`, `106-131` |
| `decoder` 딕셔너리의 나머지 키가 그대로 `MinSumDecoder(**dec_cfg)`로 전달되는 구조. 오타 키의 실패 지점과 메시지, 그리고 `max_iter` 금지 검사가 `llr_matrix` 없는 설정에도 적용되는 것이 의도인지 | `run.py:46-52`, `75-82` / `decoder.py:23-24` |
| `schedule`을 `column_wise`로 `setdefault`하는데 `llr_matrix` 모드는 `column_wise`만 허용. 사용자가 `two_set`을 명시하면 `NotImplementedError`. 이 조합 규칙이 문서에 있는지 | `run.py:80` / `decoder.py:60-61` / 실험 README "JSON 설정 스키마" |
| `output.dir` 기본값을 `base_dir` 기준으로 만든 뒤 다시 `resolve`를 통과시키는 이중 처리, 절대경로와 상대경로의 결과 차이 | `run.py:53-55` |
| 시드 우선순위(`channel.<use>.seed` → `run.seed` → 12345)와 시드 파생식 `default_rng([seed, int(1e6 * p)])`. 포인트가 부동소수일 때의 정수 변환, 서로 다른 포인트가 같은 시드로 접히는 경우, 포인트가 음수일 때 | `run.py:118`, `123` |
| `stop_below_fer`가 "포인트가 FER 내림차순으로 나열됨"을 전제하는지, `errors == 0`이면 `fer = 0`이 되어 즉시 중단되는 동작이 의도인지 | `run.py:129-130` / `sim.py:24` |
| `run_experiment` 반환이 `{ch_type: points}` 단일 항목인데, 본체 README는 "채널 1개/여러 개 모두 설정만으로 처리"라고 서술. `report`가 여러 채널 루프를 도는 구조와 실제 생성 데이터의 불일치 | `run.py:106-143` / 본체 `2_LDPC_light/README.md` `run.py` 행 |
| 모드 검증(`_make_channel_fn`)이 채널 함수 생성 시점에서 이루어져 포인트 루프마다 반복되는 것, `dec.matrix is None`이면 mode를 "HD"로 가정하는 fallback | `run.py:86-103` |
| 출력 책임 분산: `setup()` 안에서 `mx.summary()` 출력, `main()`에서 `code.summary()` 출력. 라이브러리로 임포트했을 때의 부작용 | `run.py:79`, `153` |
| CSV 컬럼 `param`이 채널 종류와 무관하게 고정. 채널마다 의미가 다름(RBER 값 대 에러 비트 수)이 출력에서 구분되는지 | `run.py:141` / `sim.py:36-43` |
| `config.json`의 실제 값이 유효한 실험인지. `max_frames = 256`, `batch = 64`, `max_frame_errors = 10`, `points = [200, 300]` 조합에서 측정 통계량이 성립하는 범위 | `config.json` / `sim.py:17-24` |

### P5. 디코더 3경로의 자체 정확성과 상호 일관성

`decode_batch`가 `_decode_matrix` / `_decode_column_wise` / two_set 본체로 갈라진다. 세 경로가 거의 같은 코드를 복제하고 있어 발산 위험이 있다.

| 확인 항목 | 대상 |
|---|---|
| 세 경로의 공통 구조(column 루프, edge 루프 2회 pass, 배치 압축, `n_iter` 기록)가 복제되어 있음. 한쪽만 고쳐질 때 드러나는 차이(예: `cn_mag_fn` 적용 여부, RESET 정의, edge clear 조건) | `decoder.py:146-215`, `247-317`, `368-441` |
| `decode_batch`가 dict 입력을 받았을 때 비-matrix 경로에서 `hd`를 ±8 signed로 변환하고 `sd`/`cc`를 버리는 어댑터. 이 경로로 2SD 채널 출력이 들어올 수 있는지 | `decoder.py:120-124` |
| `_decode_column_wise`의 `RESET`이 프로파일 없으면 `msg_clip`(31.0)이 되는데, 이때 `min1`/`min2` 초기값과 `_edge_mag` 부재의 상호작용 | `decoder.py:233`, `48-55` |
| two_set 경로의 `old_min1 = zeros`(빈 상태) 대 `_INF` 초기화된 `new_min1`의 비대칭, 배치 압축 시 `np.minimum(new_min1[keep], msg_clip)`으로 deg-1 row를 막는 처리 | `decoder.py:136-140`, `206-210`, `19` |
| CN 상태 갱신에서 `m1, m2, p = min1[:, i, :], min2[:, i, :], pos[:, i, :]`가 **뷰**인데 이후 `np.where` 결과를 같은 슬라이스에 다시 대입. 같은 iteration 안에서 같은 row `i`를 여러 edge가 건드릴 때(같은 column에 같은 row가 두 번 나오는 base matrix)의 순서 의존성 | `decoder.py:412-425`, `285-298`, `188-192` |
| 배치 압축 시 유지 배열 목록의 완전성. `_decode_matrix`는 `r_bit, synd, prev_csw, min1, min2, pos, csum, esgn`을 압축하는데, 다음 iteration의 `row_idx`, `ch_cur`, `th_cur`가 압축 후 크기와 맞는지 | `decoder.py:435-441`, `380-382` |
| `max_iter`가 1일 때, restart iteration이 `max_iter`와 같을 때, `max_iter`가 0 이하일 때의 루프 동작 | `decoder.py:368`, `436-437` / `llr_matrix.py:63` |
| `collect_profile` 경로가 `sim.py`에서 호출되지 않아 실행 경로에서 죽어 있음. 유지 여부와 정확성 검증 수단 | `decoder.py:110-117`, `194-195` / `sim.py:19` |
| `n_iter`가 실패 프레임에서 0인데 `sim.py`의 `avg_iter_ok = iter_sum / max(1, frames - errors)`가 누적 `frames`와 누적 `errors`를 쓰는 계산. 배치별 성공 수와 프레임 수의 대응 | `decoder.py:212`, `443` / `sim.py:20-28` |
| `msg_clip`, `quantize`, `beta`, `alpha`가 `llr_matrix` 모드에서 조용히 무시되는 것(생성자에서 `beta`만 0으로 덮어씀). 사용자가 지정했을 때 경고가 없는 구조 | `decoder.py:23-24`, `43-47`, `66-70` |

### P6. 입력 데이터 무결성과 코드 전제의 정합

| 확인 항목 | 대상 |
|---|---|
| `example_18x147_z256.qc`의 실제 column degree 분포가 LLR matrix의 dv 구간 `{11, 4, 3, 2}`(싱글턴 4개)를 **빠짐없이** 덮는지. 하나라도 어긋나면 `col_dv_idx`가 즉시 예외 | `Input/H_matrix/example_18x147_z256.qc` / `llr_matrix.py:139-149` / `pcm.py:43` `col_deg` |
| 헤더 `J K = 4 31`인데 LLR matrix의 dv 구간에 11이 있음. 헤더 J(최대 column degree)와 dv 테이블이 서로 다른 부호를 가정하고 있는지, 이 조합이 의도된 토이 설정인지 | `Input/H_matrix/example_18x147_z256.qc:2` / `Input/LLR/LLR_MATRIX_HD_*.txt:5-6` |
| 실험 README가 선언한 "column block은 DV 내림차순 배치"가 실제 파일에서 성립하는지, 그리고 코드 어딘가가 그 순서에 의존하는지(의존한다면 어디인지) | 실험 README "구성" 표 / `pcm.py:35-43` / `decoder.py:384` column 루프 |
| `QCCode.load`가 빈 줄을 모두 걸러내므로 "빈 줄 구분자"가 없어도 통과함. Ref-C 전용이라 선언한 포맷 강제성과 구 포맷(`#` 주석) 파일이 들어왔을 때의 실패 방식 | `pcm.py:54-75` / 실험 README "구성" 표 |
| shift 값 검증이 `np.any(base >= z)`뿐. -1보다 작은 음수, 비정수, `z <= 0`에 대한 방어 | `pcm.py:22-27` |
| `save`/`load` 왕복 정합(`J`, `K`를 실제 최대 degree로 다시 쓰므로 원본 헤더와 달라질 수 있음) | `pcm.py:46-52` vs `71-74` |
| `Sim_Output/`에 남아 있는 구 결과 파일(`fer_bsc.csv`, `fer_llr_bsc.csv`, `_tmp_rber.json`, `_tmp_strong.json`)이 현재 채널 이름 체계와 맞지 않음. 실험 산출물 정리 정책 | `Sim_Output/` 디렉토리 |
| `syndrome()`이 edge마다 `np.roll`을 도는 구현의 dtype 유지(uint8 XOR)와 배치 축 브로드캐스트 | `pcm.py:78-85` / `decoder.py:354` |

### P7. 본체 반영 시 파손 범위 (호출 체인 영향)

이 개정본은 본체를 대체할 예정이므로, 본체에 남는 파일들이 바뀐 인터페이스를 견디는지가 별도 축이다.

| 확인 항목 | 대상 |
|---|---|
| 구 JSON 키에 의존하는 본체 설정과 스크립트. `code_file`, `target_errors`, `stop_below`, `max_iter`, 채널 이름 `bsc`/`awgn` | `2_LDPC_light/examples/fer_curve.json`, `examples/fer_curve.py`, `examples/fixed_error_sweep.py`, `examples/llr_tune.py` / `run.py:34-65` |
| 구 채널 API(BSC/AWGN 함수)가 사라진 영향. 새 `channel.py`에는 `bsc`/`awgn`이 없고 출력도 배열이 아니라 dict | `2_LDPC_light/channel.py` vs `LDPC_base/channel.py` / 위 examples 전부 |
| 구 H-matrix 포맷(`#` 주석 + `M_b N_b z` 헤더) 지원 제거의 파급. 본체 `examples/*.qc` 2개와 `tools/gen_example_code.py`의 출력 포맷 | `2_LDPC_light/examples/example_18x147_z256.qc`, `examples/irregular_17x144_z256.qc`, `tools/` / `pcm.py:54-75` |
| `mpi_runner.py`가 `run.py`/`sim.py`의 어떤 함수 시그니처에 의존하는지(`run_fer_point`의 인자명이 `target_errors` → `max_frame_errors`로 바뀜) | `2_LDPC_light/mpi_runner.py` / `sim.py:7-8` |
| `llr_tables.py`와 `llr/*.txt` 8개 파일, 그리고 `decoder`의 `llr_profile` 경로의 처분. 제거 후보로 선언되어 있으나 `_decode_column_wise`와 `_vnu_quantize`가 여전히 `self.profile`을 분기 | 실험 README "구성" 주의 항목 / `llr_tables.py` 전체 / `decoder.py:48-55`, `72-88`, `233`, `275-276` |
| 본체 `_pm/TODO.md`, `_pm/DONE.md`에 이 개정 작업이 등록되어 있는지, 반영 절차(폴더 이동, examples 갱신, 문서 갱신)가 작업 단위로 정의되어 있는지 | `2_LDPC_light/_pm/TODO.md`, `_pm/DONE.md` |
| 이 개정본이 `_test/` 아래에 있어 `.gitignore` 대상. 커밋되지 않는 상태에서의 이력 보존과 반영 시점 | 루트 `.gitignore` / 실험 README "활용 방법" |

### P8. 사실 정확성 — 코드와 문서의 일치

| 확인 항목 | 대상 |
|---|---|
| 실험 README "채널 모델" 표의 서술(2SD r_offset 0.35, 3SD 0.15/0.35/0.55, `|2y/σ²|` 대 `2·r_offset/σ²` 비교)이 `channel.py` 구현과 일치하는지 | 실험 README "채널 모델" / `channel.py:43-68` |
| 실험 README "검증 기록"의 수치(RBER 0.01 → 측정 BER 0.0104, E=300/SER=0.3/SCR=0.6 → strong 에러 90, strong 정정 22399, fixed-error 30비트 → 잔여 4.4)가 현재 코드로 재현되는지. 22399는 N과 E로 역산 가능 | 실험 README "검증 기록" / `channel.py:103-112` / `pcm.py:30` `N` |
| `차이.md` §2 "등가로 확인된 항목" 13개가 P1의 대조 결과와 어긋나는 항목이 있는지(특히 #3 edge clear에서 edge_sgn 미포함, #8 CSW, #9 row 선택, #11 V 코드 대 EDGE 값 등가) | `차이.md` §2 / P1 대조 결과 |
| `차이.md` §1 #2가 "AUTO 빌드는 BF 비활성이므로 차이 없음"이라 판정한 근거(`ITER_MAX_HBF = 0`, `flag_BF_on` 상시 LOW)가 실제 소스에서 확인되는지 | `차이.md` §1 #2 / `0_LDPC_original/common.h`, `mode.h`, `decoder.cpp` |
| `decoder.py` 모듈 docstring이 "LLR 도메인: 수학적 등가인 signed 표현"이라고 서술하는데 `_decode_matrix`는 flip/magnitude 도메인. 모듈 서술과 실제 주 경로의 불일치 | `decoder.py:1-16` vs `decoder.py:319-338` |
| `run.py` 모듈 docstring의 4단계 서술과 `main()` 실제 호출, 그리고 "encode(임시: all-zero 반환)" 표기의 유지 | `run.py:1-19`, `146-156` / `encoder.py:16-19` |
| `llr_matrix.py` docstring의 "아래에서부터 처음으로 csw <= 임계값인 row"라는 서술과 구현(위로 올라가며 마지막 매칭)의 표현 일치 | `llr_matrix.py:16`, `160-177` |
| 본체 `README.md`와 `docs/plan.md`가 아직 구 구조(BSC/AWGN 채널, `target_errors`, signed LLR 도메인, "Get_VNU_Table_Idx 대응 테이블 전환 없음")를 서술. 반영 시 갱신 대상 목록 | `2_LDPC_light/README.md` 전체, `docs/plan.md` §2, §3.1, §3.2 |
| 루트 `CLAUDE.md` "작업 전 추가 로드" 표가 2_LDPC_light 작업 시 `README.md` + `docs/plan.md`를 지목. 이 실험 폴더의 문서가 그 체계 안에 편입되는지 | 루트 `CLAUDE.md` / 실험 README |
| 코드 주석의 C++ 행 번호 인용(예: "decoder.cpp:3476-3526", "decoder.cpp:4080-4120", "channel.cpp:11-29", "common.h:756-757")이 실제 파일 행과 맞는지 | `decoder.py:220-222`, `74`, `channel.py:20`, `llr_matrix.py:32` / `0_LDPC_original/` 해당 파일 |

### P9. 수치 표현과 타입 안정성

정수 도메인 HW를 float32로 모사하고 있어, 등가성이 성립하는 조건 자체가 확인 대상이다.

| 확인 항목 | 대상 |
|---|---|
| 채널은 float64, 디코더는 float32, 테이블 값은 파일에서 int로 읽어 float32로 변환. 경계 비교(`total <= 0`, `mag_new <= m1`, `m < th`)가 부동소수 오차에 노출되는 지점이 있는지, 아니면 모든 값이 작은 정수라 정확한지 | `channel.py:50-51` / `decoder.py:57-70`, `90-102`, `398`, `419-420` |
| `lvl = ((m < th[:, 0, None]).astype(np.int8) + (m < th[:, 1, None]) + (m < th[:, 2, None]))`의 dtype 승격과 인덱스 범위 0~3 보장. th가 내림차순이 아닌 파일(또는 -1 혼재)일 때 lvl이 범위를 벗어나는지 | `decoder.py:94-96` / `llr_matrix.py:60` |
| th에 -1이 들어간 restart row에서 `m < -1`이 항상 거짓이 되어 최대 레벨이 나오는 동작이 C++의 정수 비교와 같은지, 그리고 ch = -1이 `total` 초기값에 그대로 더해지는 것의 부호 효과 | `decoder.py:388`, `94-96` / `Input/LLR/LLR_MATRIX_HD_0.txt` 두 번째 row |
| `csum`, `esgn`, `synd`, `r_bit`가 모두 uint8이고 XOR 누적. `sgn_new = (v2c < 0).astype(np.uint8)`의 -0.0 처리 | `decoder.py:357-361`, `393`, `409`, `424` |
| `prev_csw`를 int64로 만든 뒤 `row_csw`(int64)와 비교. CSW 최대값(M_b × z = 4608)과 임계값 스케일의 정합 | `decoder.py:355`, `427` / `llr_matrix.py:61` |
| `np.broadcast_to(...).astype(np.float32).copy()`가 column마다 새 배열을 만드는 것, `total += c2v`의 in-place 누적이 브로드캐스트 뷰에 걸리지 않는지 | `decoder.py:387-396` |
| `int(1e6 * p)`의 부동소수 → 정수 변환 | `run.py:123` |

### P10. 성능과 확장성 (실물 파라미터 반입 대비)

| 확인 항목 | 대상 |
|---|---|
| column 루프(N_b회) × edge 루프(dv회) × 2회 pass × iteration의 Python 인터프리터 왕복 수. 실물 규모(N_b=147, dv 최대 11, z=256, batch 64, max_iter 20)에서의 프레임당 numpy 호출 횟수 | `decoder.py:384-425` |
| edge마다 `min1[:, i, :]` 형태의 fancy 슬라이싱과 `np.where` 3~4회. 같은 row `i`를 여러 번 건드릴 때의 중복 비용 | `decoder.py:412-425` |
| `syndrome()`이 E회 `np.roll`을 도는 비용(프레임 배치마다 1회) | `pcm.py:78-85` |
| `_rand_positions`가 프레임마다 (B, N) 난수 배열을 만들고 `argpartition`. N=37632, B=64 기준 비용과 메모리 | `channel.py:71-73` |
| `esgn` 배열 크기 (B, E, z) uint8의 메모리. 실물 E와 z=256, B=64 기준 | `decoder.py:361` |
| `sim.py`의 배치 루프가 `max_frames`를 넘지 않도록 `b = min(batch, max_frames - frames)`로 조정하는 것과 배치 압축의 상호작용 | `sim.py:17-22` |
| 배치 압축(성공 프레임 제외)이 결과 불변이라는 주장이 `row_index`가 프레임별로 다른 row를 고를 수 있는 CSW 모드에서도 성립하는지 | `decoder.py:435-441`, `380-382` / `llr_matrix.py:173-177` |

### P11. 요구사항 충족과 스코프 (본체의 새 원본이 될 자격)

| 확인 항목 | 대상 |
|---|---|
| 루트 `CLAUDE.md` ㉰의 목표("외부의 H-matrix와 파라미터를 넣어도 동작")에 비추어 남은 하드코딩. all-zero codeword 전제, `_edge_mag = [7,5,3,1]` 고정, `th_len != 3`이면 거부, HD 전용 | `decoder.py:62-70`, `399` / `encoder.py:16-19` |
| 미구현 항목이 **조용히 통과하지 않고 명시적으로 막히는지**. 2SD/3SD 디코딩, 4-bit 빌드, BF 구간, 파이프라인 지연 | `decoder.py:62-66` / `run.py:86-93` / `channel.py:47`, `79`, `98-99` |
| 실험 README "남은 근사/제한" 4개 항목이 코드의 실제 상태와 같은지, 그리고 각각이 FER에 미치는 방향이 기록되어 있는지 | 실험 README "남은 근사/제한" |
| `encoder.encode()`가 스텁인 상태에서 `generate_message()`가 매 배치 (B, K) 난수를 만들고 버리는 구조. 비용과 의도 | `encoder.py:11-19` / `run.py:98-101` |
| 제거 후보로 선언된 `llr_tables.py`와 `llr_profile` 경로를 실제로 제거할 때 남는 참조 | `llr_tables.py` / `decoder.py:48-55`, `72-88`, `233`, `275-276` |
| 원본 대응 채널 3종 외에 원본이 가진 다른 채널 모드(`MODE_CH_ERASURE`, `MODE_CH_3SD_FIXED`)를 스코프에서 뺀 결정이 문서에 기록되어 있는지 | `ecc_top.cpp:1882-1918` / 실험 README "채널 모델" |
| 리뷰 대상 스코프의 경계. 이 폴더가 `_test/` 아래이므로 글로벌 규칙상 "기존 데이터를 직접 수정하지 않음"과 "각 테스트 디렉토리에 README" 요건은 충족. 그 외 프로젝트 규칙(변경 등급, `_pm/tasks/` 문서) 적용 여부 | 글로벌 `CLAUDE.md` "테스트/예시 작업 규칙" / 루트 `CLAUDE.md` 변경 등급표 |

### P12. 에러 처리와 운용 견고성

| 확인 항목 | 대상 |
|---|---|
| 예외 타입의 일관성(`ValueError`, `NotImplementedError`, `FileNotFoundError`, `SystemExit`)과 메시지의 정보량. 어떤 값이 잘못됐고 어디를 고쳐야 하는지 메시지만으로 알 수 있는지 | `run.py:49-62`, `72-73` / `decoder.py:39-40`, `59-66` / `llr_matrix.py:47`, `74-94`, `101-132`, `145-147` / `channel.py:47`, `79`, `99` |
| 설정 오류가 `load_config` 시점이 아니라 `setup`이나 첫 배치 실행 시점에 드러나는 항목(dv 미매칭, 모드 불일치, 디코더 kwargs 오타). 긴 실험을 돌리기 전에 걸러지는지 | `run.py:34-103` / `llr_matrix.py:145-147` / `decoder.py:59-66` |
| 파일 파싱 실패 시 원본 예외가 그대로 올라오는 지점(`int()` 실패, `lines[2]` 인덱스 초과, `head = lines[0].split()` 전에 빈 파일) | `pcm.py:57-69` / `llr_matrix.py:104-121` |
| 결과 파일 덮어쓰기 정책. 같은 `csv_prefix`와 채널로 재실행 시 이전 결과가 무경고 소실 | `run.py:134-143` / `sim.py:36-43` |
| 재현성 기록. 어떤 시드와 어떤 설정으로 만든 CSV인지가 출력에 남는지 | `sim.py:36-43` / `run.py:118-128` |
| Windows 환경 전제(경로 구분자, `encoding="utf-8"` 명시 여부의 일관성) | `run.py:38`, `pcm.py:49`, `57` / `llr_matrix.py:104` / `sim.py:38` |

---

## 2. 관점 우선순위 (Round 2 배분 제안)

| 우선 | 관점 | 이유 |
|------|------|------|
| ★★★ | P1, P2 | 원본 C++ 대응이 이 개정의 존재 이유. 어긋나면 이후 실험 결과 전부가 무효가 된다 |
| ★★★ | P3 | LLR matrix 파싱과 row 선택이 틀리면 디코더가 잘못된 테이블로 조용히 수렴한다 (에러 없이 FER만 달라짐) |
| ★★☆ | P5, P6 | 자체 정확성과 입력 전제. 토이 데이터에서만 검증되어 실물 반입 시 처음 드러날 항목 |
| ★★☆ | P4, P7 | 본체 반영 시 곧바로 부딪히는 계약과 파손 범위 |
| ★☆☆ | P8, P9 | 문서 일치와 수치 안정성. 발견 비용이 낮고 수정도 국소적 |
| ★☆☆ | P10, P11, P12 | 실물 규모 확장과 운용 품질. 반영 후 보완으로 흡수 가능한 범위 |

## 3. 대조에 쓸 원본 앵커 모음

Round 2에서 C++ 대조가 필요할 때 바로 열 수 있도록 위치를 모아둔다.

| 항목 | 원본 위치 |
|------|-----------|
| Edge Clear (restart) | `0_LDPC_original/decoder.cpp:709` `Clear_Edge_Restart` |
| C2V sign 계산 | `decoder.cpp:2299` `C2V_Cal_New_Sgn` |
| C2V 본체 | `decoder.cpp:2341` `C2V_Cal` |
| CN 상태 remove-old | `decoder.cpp:3476` `CNU_Remove_Old_Sgn` |
| CN 상태 insert-new | `decoder.cpp:3514` `CNU_Update_New_Mag` |
| iteration 0 사전 계산 | `decoder.cpp:3554` `VN_Cal_Pre` |
| VN 판정과 VNU 양자화 | `decoder.cpp:3973` `VN_Cal_HD` |
| 테이블 row 선택 | `decoder.cpp:6973` `Get_Cur_LLR_Idx_FILE` (AUTO 경로는 6984-6999, ITER/CSW 분기는 7051-7068) |
| 테이블 값 분해와 dv 매칭 | `decoder.cpp:7074` `Get_VNU_LLR_SET_FILE` (dv 매칭 7078-7082) |
| CSW 계산 | `decoder.cpp:7293` `Compute_CSW`, `decoder.cpp:7340` `Compute_CSW_Auto` |
| 채널 상수와 양자화 | `channel.cpp` `Set_R_Offset`, `Set_LLR_Th`, `Get_Mag_2SD`, `Get_Mag_3SD`, `qfunc_inv`, `dev_from_RBER` |
| 고정 에러 채널 파라미터 산출 | `ecc_top.cpp:1828-1920` `Make_Dec_Input_Ref_C_Fixed_4KB` (fixed 1854-1866, strong 1867-1881) |
| 고정 에러 채널 적용 | `ecc_top.cpp:1687-1795` `Make_Dec_Input_Fixed_4KB` |
| AWGN 채널 양자화 | `ecc_top.cpp:1795` `Make_Dec_Input_AWGN_Quantize` |
| 채널 모드 상수 | `common.h:80-82` `MODE_CH_RBER` / `MODE_CH_FIXED_ERROR` / `MODE_CH_STRONG_ERROR` |
| 그룹 타입 상수 | `common.h:756-757` `GROUP_TYPE_ITER` / `GROUP_TYPE_CSW` (코드 주석 인용, 실제 행 확인 필요) |
