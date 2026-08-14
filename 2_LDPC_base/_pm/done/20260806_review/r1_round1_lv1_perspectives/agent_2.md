# Round 1 / agent_2 — 리뷰 관점 도출

> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/LDPC_base/` 개정본 + `config.json` + `Input/`
> 목적: 본체(`2_LDPC_light/`) 반영 전 "어디를 봐야 하는가"를 도출한다 (문제 지적은 Round 2 소관).
> 작성 시 확인한 배경: 루트 `CLAUDE.md`, 실험 폴더 `README.md`, `2_LDPC_light/docs/plan.md`,
> 기존 리뷰 기록 `2_LDPC_light/docs/review/`, 본체 `run.py`/`channel.py`/`pcm.py`/`sim.py`/`decoder.py`.

## 사전 확인한 사실 (관점 정의의 근거, 판정 아님)

- ㉮ 원본 C++ 소스가 `0_LDPC_original/`에 전량 존재한다 (`decoder.cpp`, `channel.cpp`, `ecc_top.cpp`,
  `common.h`). `Get_Cur_LLR_Idx_FILE`, `Compute_CSW`, `Clear_Edge_Restart`, `MODE_CH_STRONG_ERROR`
  모두 grep으로 잡힌다. 즉 이번 신규 구현 3종은 **원문 대조가 가능한 상태**다.
- ㉯ 반면 `llr_matrix.py` docstring이 근거로 든 `DAO_LLR_MATRIX.py`(`Read_Input_LLR_Matrix`)는
  저장소 어디에도 없다. LLR_MATRIX 포맷 해석의 근거는 코드 주석과 예시 파일 2개뿐이다.
- ㉰ 예시 부호 실측: base 18x147, z=256, E=553, col degree 히스토그램 `{2:17, 3:1, 4:129}`,
  row degree `{30:5, 31:13}`, column DV 내림차순 성립. LLR matrix의 dv 구간은 `[11,4,3,2]`이므로
  dv=11 그룹은 미사용이고 dv=3은 column block 1개뿐이다.
- ㉱ 예시 LLR matrix 2개 모두 CSW 그룹의 row가 1개씩이라 `needs_csw`가 거짓이다. 즉
  **CSW 기반 row 선택 경로는 현재 입력 데이터로 한 번도 실행되지 않는다.**
- ㉲ 본체 대비 인터페이스가 바뀐 지점: `code_file` → `H_matrix`, `channels`(리스트) →
  `channel.use`(단수), `target_errors` → `max_frame_errors`, `stop_below` → `stop_below_fer`,
  `bsc_llr`/`awgn_llr`/`fixed_error_llr` 삭제, pcm 구 포맷 파서 삭제.

---

## 관점 목록

### P1. 원본 C++ 원문과의 산술 대조 (syndrome-aided 디코딩)

이번 변경의 핵심 주장이 "원본 C++ 그대로"이므로, 주장 자체를 원문으로 검증해야 한다.

- ㉮ `C2V_Cal`의 sign 합성이 `synd ⊕ check_sum ⊕ edge_sgn`인지, 피연산자 3개가 같은 정렬
  (CN 정렬 대 VN 정렬)에서 XOR되는지
- ㉯ `VN_Cal_HD`에서 반전 조건이 `sum_t <= 0`인지 `< 0`인지 (동점 처리 방향)
- ㉰ `Clear_Edge_Restart` + `C2V_Cal_New_Sgn`이 실제로 syndrome만 남기고 min/pos/check_sum/
  edge_sgn을 모두 지우는지, 그리고 클리어 직후 C2V magnitude가 `V_VERY_STRONG`인지
- ㉱ `V_VERY_STRONG`의 실제 상수값이 코드가 쓰는 `edge_mag[0]=7`과 같은 도메인인지
  (`common.h` 상수 확인). EDGE magnitude 도메인과 채널 LLR 도메인(0~31)이 섞여 있지 않은지
- ㉲ `CNU_Update_New_Mag`의 `<=` 비교와 "min1 교체 시 min2=RESET" 근사가 원문과 일치하는지
- ㉳ iteration 0 Pre-update를 `syndrome = H·r` 직접 계산으로 대체한 것이 등가인지
  (원본은 iter 0에서 V2C sign에 r을 실어 check_sum에 누적한 뒤 syndrome 레지스터로 복사)
- ㉴ `Compute_CSW`가 참조하는 상태의 시점 (column 루프 도중인지 iteration 종료 후인지)

대상: `LDPC_base/decoder.py:319-446` 전체, `0_LDPC_original/decoder.cpp`, `common.h`

---

### P2. flip 도메인 상태 갱신과 genie 판정의 의미

flip 도메인에서는 read bit r이 고정이고 판정이 매 column 재계산된다. 판정 타이밍이 결과를 바꾼다.

- ㉮ `r_bit`이 iteration 중 한 번도 갱신되지 않는데, C++의 `Variable_mem`도 그러한지
  (갱신된다면 syndrome 고정 유지 전제가 무너진다)
- ㉯ `frame_err |= bit_err.any(...)`가 column 루프 **도중** 누적된다. column j의 판정 시점과
  iteration 종료 시점의 상태가 다르므로, "iteration k에서 성공"의 정의가 column 순서에 의존한다.
  세 경로(`_decode_matrix` / `_decode_column_wise` / two_set)가 동일 정의를 쓰는지
- ㉰ 이 정의가 plan.md §7#1 genie 판정 (매 iteration hard decision을 정답과 비교)과 같은지,
  아니면 더 낙관/비관적인지
- ㉱ `n_iter` 기록과 성공 프레임 배치 제외가 이 정의 위에서 일관된지
- ㉲ 실패 프레임의 `n_iter=0` 규약이 `sim.py`의 `avg_iter_ok` 계산과 맞는지

대상: `decoder.py:384-403`, `:431-441`, `:169-172`, `:268-270`, `sim.py:14-28`

---

### P3. 채널 3종의 원본 대조 및 수치 경계

- ㉮ `qfunc_inv` 계수/부호와 `dev_from_rber`의 SNR 정의(`qinv^2/2`, `var=1/(2·SNR)`)가
  `channel.cpp`와 일치하는지, rate 반영 여부가 원본과 같은지
- ㉯ HD 결정 경계 `cwr < 0` (주석은 "C++: cwr >= 0 → HD 0")의 등호 위치
- ㉰ 2SD/3SD region 비교 방향(`>=` 대 `>`)과 3SD에서 `cc[m>=th3]=1` 후 `cc[m<th1]=1`로
  두 번 대입하는 순서가 `Get_Mag_3SD` 원문과 같은지 (th 대소 관계 가정 포함)
- ㉱ `_rand_positions`의 `argpartition(..., k-1)`이 비복원 균일 추출인지, `k=0`/`k=N`/`k>N`
  경계에서 어떻게 되는지
- ㉲ `strong_error_channel`의 슬라이스 `[0:e2+e1]` flip, `[e2:e2+e1+c1]` weak이
  `Make_Dec_Input_Ref_C_Fixed_4KB` 원문의 e2/e1/c2/c1 배치와 일치하는지.
  `c2`가 계산만 되고 쓰이지 않는 점, `c1 = N-E-c2`가 음수가 될 조건
- ㉳ `int(np.floor(x+0.5))`가 C++ `round`와 음수/정확히 .5인 경우까지 같은지
- ㉴ README의 검증 수치(RBER 0.01 → BER 0.0104, E=300/SER=0.3/SCR=0.6 → strong 정정 22399)를
  현재 코드로 재현할 수 있는지

대상: `channel.py` 전체, `0_LDPC_original/channel.cpp`, `ecc_top.cpp` `Make_Dec_Input_*`

---

### P4. 채널 ↔ 디코더 인터페이스 계약과 데드 경로

채널 출력이 배열에서 dict로 바뀌었다. 계약이 세 디코드 경로에 걸쳐 일관한지 봐야 한다.

- ㉮ dict `{"mode","hd","sd","cc"}`를 소비하는 곳이 `_decode_matrix`뿐이고,
  legacy 경로는 `hd`만 ±8 signed LLR로 바꾼다. `sd`/`cc`는 어디서도 읽히지 않는다.
  즉 **strong_error 채널의 2SD 정보는 현재 소비처가 없다**
- ㉯ `strong_error`는 2SD 전용인데 디코더는 HD matrix만 지원하므로 (`decoder.py:62-64`),
  `config.json`에 정의된 strong_error가 실제로 실행 가능한 조합인지 (실행 불가라면
  설정 스키마와 구현 범위의 불일치를 어떻게 표시할지)
- ㉰ 디코딩 모드의 유일한 출처가 LLR matrix **파일명**이다. 파일명 오타나 모드 불일치가
  조용한 오동작이 되는지 명시적 에러가 되는지 (`llr_matrix.py:99-103`, `run.py:89-93`,
  `decoder.py:341-345` 3중 검사의 중복/누락)
- ㉱ `dec.matrix is None`일 때 `mode = "HD"` 기본값이 rber 2SD/3SD 실험을 막는지
- ㉲ 배열 입력(legacy) 경로가 `_decode_matrix`에서 `(ch_llr < 0)`으로 r_bit을 만드는데,
  matrix 모드에서 이 경로가 실제로 도달 가능한지 (도달 불가면 죽은 코드)

대상: `run.py:86-103`, `decoder.py:110-124`, `:341-347`, `channel.py:117-128`

---

### P5. LLR_MATRIX 포맷 해석의 근거와 필드 활용 완전성

포맷 정본(`DAO_LLR_MATRIX.py`)이 저장소에 없으므로 파싱 가정 전체가 검토 대상이다.

- ㉮ row 값 배치를 `reshape(R, num_dv, num_param)` 즉 **dv-major (ch, th1, th2, th3) 반복**으로
  가정했다. param-major 배치(`ch 전부` 다음 `th 전부`)와 예시 파일로 구분 가능한지.
  예시 row `1 28 9 5 | 10 10 9 4 | 13 31 10 7 | 28 12 10 8`을 두 해석으로 각각 읽었을 때
  dv2 ch=28인지 dv2 ch=5인지가 갈린다. README의 "dv2 ch=28" 서술 근거 확인
- ㉯ 헤더 필드 순서와 조건부 줄(`num_restart=0`이면 restart 줄 없음) 처리, `num_group` 미검증,
  탭/CRLF/후행 공백/마지막 줄 개행 없음 처리
- ㉰ 값이 정수가 아니거나 필드 수가 어긋날 때의 에러 (`int(v)` ValueError가 그대로 노출)
- ㉱ **로드만 하고 쓰지 않는 필드**: `max_value`/`min_value`(어떤 클리핑에도 미적용),
  `floor_flag`(파싱만 하고 클래스에 저장 안 함), `needs_csw`(호출처 없음).
  원본이 이 값들을 산술에 쓰는지 확인
- ㉲ `-1` 값의 산술 효과: `th=-1`이면 `m < -1`이 항상 거짓 → 레벨 0 → 최대 magnitude,
  `ch=-1`이면 total에 -1이 더해진다. README의 "채널 기여 거의 0" 표현이 실제 산술과 맞는지
  (ch=0이 아니라 -1이므로 약한 반전 압력이 있다)
- ㉳ `_validate`의 그룹 iteration 연속성(`iter_start == 이전 iter_end + 1`)과 restart 그룹
  제약(단일 row/단일 iteration, 마지막 그룹 금지)이 DAO 파일 일반에 성립하는 가정인지,
  아니면 예시 2개에 맞춘 과잉 제약인지
- ㉴ `max_iter = row_iter[-1,1]`이 그룹 순서와 row 순서가 iteration 오름차순이라는 가정에 의존

대상: `llr_matrix.py` 전체, `Input/LLR/LLR_MATRIX_HD_0.txt`, `LLR_MATRIX_HD_1.txt`

---

### P6. row 선택 로직 (Get_Cur_LLR_Idx_FILE 대응)과 CSW 경로 미검증

- ㉮ `group_type`이 CSW인데 row가 1개면 ITER 분기로 처리(`b - a == 1` 단락)한다.
  C++도 같은 단락을 하는지
- ㉯ CSW 선택이 `for r in a+1..b: sel = where(csw <= row_csw[r], r, sel)` 즉 조건을 만족하는
  **가장 큰 r**을 고른다. docstring의 "아래에서부터 처음으로"와 코드가 같은 의미인지,
  그리고 C++의 순회 방향/비교 방향(`<=` 대 `<`)과 같은지
- ㉰ 조건 불만족 시 그룹 첫 row fallback이 원문과 같은지
- ㉱ `prev_csw` 초기값 `|synd|`의 근거, iteration 종료 시점 `(csum ^ synd).sum()`의
  csum이 column-wise 즉시 갱신 상태라는 점 (iteration 경계에서 어떤 column까지 반영된 값인지)
- ㉲ 프레임별로 다른 row가 선택되므로 `ch_cur (Ba, num_dv)` / `th_cur (Ba, num_dv, 3)`가
  column 루프 안에서 브로드캐스트되는데, 배치 압축 후 `row_idx` 재계산 시점과 크기가 맞는지
- ㉳ **예시 파일 2개 모두 CSW 다중 row 그룹이 없어 이 경로가 실행되지 않는다.**
  검증용 입력을 만들어 돌려볼 필요가 있는지, 아니면 미검증 상태로 본체에 넣어도 되는지

대상: `llr_matrix.py:154-183`, `decoder.py:355`, `:380-382`, `:427`

---

### P7. 배치 압축(active frame masking)과 상태 배열 슬라이싱 정합

세 디코드 경로가 각각 "성공 프레임 제거" 로직을 중복 보유한다. 줄여야 할 배열 목록이 경로마다 다르다.

- ㉮ matrix 경로에서 keep 시 줄이는 배열: `r_bit, synd, prev_csw, min1, min2, pos, csum, esgn`.
  누락된 상태가 없는지 (특히 `idx_active`와 profile 집계)
- ㉯ two_set 경로의 `old_*` 5종, column_wise 경로의 `min1/min2/pos/csum/esgn` 각각 전수 확인
- ㉰ restart 처리의 `min1.fill(RESET)` 등 in-place 연산이 직전 iteration에서
  `min1 = min1[keep]`로 새로 만들어진 배열에 걸리는지 (뷰/사본 혼동 여지)
- ㉱ `m1, m2, p = min1[:, i, :], min2[:, i, :], pos[:, i, :]`는 뷰인데 이어지는
  `m1 = np.where(...)`가 새 배열을 만든다. remove-old 결과가 원본에 반영되는 경로와
  반영되지 않는 경로가 섞여 있지 않은지
- ㉲ `csum[:, i, :] ^= esgn[:, e, :]`를 remove와 insert에서 두 번 XOR하는 순서 의존성
- ㉳ 배치 압축이 결과 불변(프레임 독립)이라는 전제가 matrix 모드에서도 성립하는지
  (프레임별 row 선택이 배치 인덱스에 의존하지 않는지)

대상: `decoder.py:200-210`, `:306-312`, `:435-441`, `:404-425`

---

### P8. 실행 흐름과 설정 계약 (run.py 4단계 재편)

- ㉮ 필수 키 부재 시 동작: `H_matrix`, `channel`, `channel.use`, `points`, strong_error의
  `SCR`/`SER`가 없을 때 KeyError가 그대로 나오는지 명시적 에러인지
- ㉯ `decoder` 하위 키가 `MinSumDecoder(**dec_cfg)`로 그대로 전달된다. 오타 키의 TypeError,
  그리고 `max_iter` 금지 검사가 **llr_matrix를 안 쓰는 설정에서도** 걸리는 점
  (그 경우 max_iter를 지정할 방법이 없어진다)
- ㉰ `dec_cfg.setdefault("schedule", "column_wise")`가 llr_matrix가 있을 때만 적용된다.
  llr_matrix 없는 설정은 여전히 `two_set` 기본값 — 의도인지
- ㉱ `output.dir`을 `setdefault`로 절대경로 지정한 뒤 다시 `resolve`하는 2중 처리
- ㉲ 시드 파생 `np.random.default_rng([seed, int(1e6 * p)])`: p가 정수(200, 300)일 때
  1e6 배수라 충돌 여지는 없는지, RBER(0.008)과 fixed_error(200)가 같은 seed 축을 공유하는 점,
  포인트 간/실행 간 재현성
- ㉳ `ch_cfg.get("seed", run_cfg.get("seed", 12345))` 우선순위가 README 스키마와 일치하는지
- ㉴ `stop_below_fer` 조기 중단 시 CSV에 남는 포인트가 "미측정"과 구분되는지,
  `errors=0`이면 `fer=0`이라 첫 포인트에서 즉시 중단되는 경우
- ㉵ `b = min(batch, max_frames - frames)`와 `max_frame_errors` 종료 조건의 상호작용
  (배치 단위 종료라 실제 frames가 max_frames를 넘지 않는지, FER 추정 편향)

대상: `run.py` 전체, `sim.py:7-33`, `config.json`

---

### P9. 본체 반영 시 호출 체인 파괴 지점

`LDPC_base/`가 본체의 새 원본이 되면, 복사하지 않은 본체 자산이 전부 깨진다. 그 목록이 필요하다.

- ㉮ `pcm.load` 구 포맷('#' 주석 + `M_b N_b z`) 지원 삭제 → 본체 `examples/*.qc`,
  `tools/gen_example_code.py` 출력이 Ref-C 포맷인지 전수 확인
- ㉯ `channel.bsc_llr` / `awgn_llr` / `fixed_error_llr` / `awgn_rber` 삭제 →
  `examples/fer_curve.py`, `llr_tune.py`, `fixed_error_sweep.py`, `select_irregular.py`,
  `mpi_runner.py` 참조 전수
- ㉰ `sim.run_fer_point` 인자명 `target_errors` → `max_frame_errors` 호출부
- ㉱ config 키 변경(`code_file` → `H_matrix`, `channels` 리스트 → `channel.use` 단수) →
  본체 `examples/fer_curve.json` 등 기존 설정 파일
- ㉲ 디코더 반환 dict 계약(`success`/`n_iter`/`profile`)이 유지되는지
- ㉳ `llr_tables.py`와 `llr_profile` 모드 제거를 결정할 경우 딸려 사라지는 것:
  `_vnu_quantize`, `_col_th`, `_col_bf`, 두 경로의 `if self.profile is not None` 분기,
  `RESET` 계산식, 본체 `llr/*.txt` 8개 파일, `examples/llr_tune.py`
- ㉴ 실험 폴더의 `Input/` 배치(H_matrix, LLR 분리)를 본체에서도 쓸지, 본체 `examples/`와
  어떻게 공존시킬지

대상: `2_LDPC_light/` 전체 grep, `LDPC_base/*` 대 본체 동명 파일 diff

---

### P10. 요구사항 충족과 스코프 완성도

- ㉮ README가 스스로 밝힌 미구현: 2SD/3SD, BF(1-bit) 구간, 파이프라인 store 지연,
  4-bit 빌드. 이것들이 본체 반영 시 plan.md/README에 이관 기록되는지
- ㉯ `encoder.encode()`가 여전히 all-zero 스텁이다. 실물 인코더가 들어오면
  `bit_err = r_bit ^ flip`(정답 0 전제) 판정이 그대로 깨진다. 스텁 교체만으로 끝나는
  구조라는 README/plan 주장이 matrix 경로에서도 성립하는지
- ㉰ plan.md §7#4 "max_iter = 120"과 "max_iter는 LLR matrix 파일이 결정"의 충돌 정리
- ㉱ plan.md §3.1 모듈표에 `llr_matrix.py`가 없고 `config.py`가 남아 있는 상태
- ㉲ 세 디코드 경로(two_set / column_wise / matrix)를 모두 유지할지, 논문 스크리닝 목적에서
  어느 것이 정본인지 (경로 3개는 훅 추가 시 3중 수정 부담)
- ㉳ `cn_mag_fn` 훅이 matrix 경로에서는 호출되지 않는다. "논문 아이디어 훅"의 진입점이
  경로별로 다른 점

대상: `docs/plan.md`, 실험 폴더 `README.md`, `LDPC_base/encoder.py`, `decoder.py:105-108`

---

### P11. 수치 도메인, dtype, 오버플로

- ㉮ float32/float64 혼용: `channel.py`는 float64로 노이즈를 만들고, decoder는 float32다.
  `np.roll`, `np.where`, 브로드캐스트 후 dtype 승격 지점
- ㉯ `np.broadcast_to(ch_cur[...]).astype(np.float32).copy()`의 중복 (astype이 이미 사본)
- ㉰ `csum`, `esgn`, `synd`, `r_bit`의 uint8 일관성. `code.syndrome()`이 입력 dtype을 그대로
  쓰므로 bool 입력이 들어오면 결과 dtype이 바뀐다
- ㉱ `lvl = (m < th0).astype(int8) + (m < th1) + (m < th2)` 의 dtype 승격과 값 범위 0~3 보장,
  `th`에 NaN/-1이 섞였을 때
- ㉲ matrix 모드에서 V2C가 항상 `{7,5,3,1}`로 양자화되므로 min1/min2가 RESET(7)을
  넘지 못한다. 이때 `total`(ch + Σ C2V)의 크기 범위와 `max_value=31` 제약의 관계
- ㉳ `prev_csw` int64 합산, `err_bits` int64 합산의 overflow 여지 (실물 크기에서)
- ㉴ `assert N_b == code.N_b and z == code.z`가 `python -O`에서 사라지는 점

대상: `decoder.py` 전반, `pcm.py:78-85`, `channel.py:43-68`

---

### P12. 입력 데이터 무결성과 커버리지

- ㉮ `example_18x147_z256.qc`: 헤더 `J K = 4 31`과 실측 degree(4, 31) 정합,
  DV 내림차순 성립(확인됨), shift 값 범위 `0 <= s < z` 검사
- ㉯ dv 히스토그램 `{2:17, 3:1, 4:129}` 대 LLR matrix dv 구간 `[11,4,3,2]`:
  dv=11 그룹이 죽은 파라미터인 점, dv=3 column이 1개뿐이라 그 그룹의 테이블 값이
  FER에 거의 영향을 못 주는 점 (실물 부호에서는 달라지는지)
- ㉰ `col_dv_idx`가 `hit[0]`(첫 매칭)을 쓴다. 구간이 겹칠 때의 우선순위
- ㉱ LLR matrix 파일의 탭 구분/CRLF/후행 공백/마지막 줄 개행 없음이 파서에서 안전한지
- ㉲ HD_0의 restart row가 전부 -1, `csw=-1`, `floor=-1`인 점. `csw=-1` row가 CSW 선택에
  들어가면 `csw <= -1`은 거의 항상 거짓이 되는데 이 값의 의미가 "미사용"인지 확인
- ㉳ `max_value 31 31 31 31` / `min_value 0 0 0 0` 대 실제 값(ch 최대 28, th 최대 31) 범위 정합
- ㉴ 예시 데이터가 토이라서 검증하지 못하는 조합 목록화 (CSW 다중 row, 2SD/3SD,
  restart 다중, dv=11 그룹)

대상: `Input/H_matrix/example_18x147_z256.qc`, `Input/LLR/*.txt`, `llr_matrix.py:139-149`

---

### P13. 문서와 코드의 일치 (사실 정확성)

- ㉮ `decoder.py` 모듈 docstring이 여전히 two_set/signed LLR 기준으로만 서술되어 있고
  matrix 경로(flip 도메인)를 반영하지 않는다
- ㉯ 실험 폴더 README의 채널 표(2SD r_offset 0.35, 3SD 0.15/0.35/0.55)와 `_R_OFFSET` 일치
- ㉰ README "max_iter를 JSON에 쓰면 에러"가 llr_matrix 미사용 설정에도 적용되는 점이
  스키마 설명과 어긋나지 않는지
- ㉱ README "llr_tables.py와 llr_profile 모드는 사실상 미사용, 제거 후보" 대 코드 잔존 상태
- ㉲ README 검증 기록의 수치가 현재 코드로 재현되는지 (P3 ㉴와 연결)
- ㉳ `llr_matrix.py` docstring이 인용하는 `DAO_LLR_MATRIX.py`, `Read_Input_LLR_Matrix`,
  `common.h:756-757`, `Get_Cur_LLR_Idx_FILE` 등 참조의 실존 여부와 행 번호 정확성
- ㉴ `channel.py` docstring의 `Make_Dec_Input_Ref_C_Fixed_4KB` 등 함수명 실존 확인

대상: 실험 폴더 `README.md`, `LDPC_base/*.py` docstring 전부, `docs/plan.md`,
`0_LDPC_original/` 심볼 실존 확인

---

### P14. 에러 처리와 조용한 오동작 회피

이번 변경이 명시적으로 "원본의 조용한 fallback을 재현하지 않는다"를 택했으므로, 그 일관성을 본다.

- ㉮ 원본이 조용히 넘어가는 지점 중 여기서 에러로 바꾼 것과 그대로 둔 것의 목록
  (dv 미매칭은 에러, 그 외는?)
- ㉯ 경계 입력: `points`에 0/음수, `n_err > N`, `rber <= 0` 또는 `>= 0.5`
  (`qfunc_inv`의 `log(p)`), `batch > max_frames`, `max_frames=0`
- ㉰ 에러 메시지가 원인을 지목하는지 (파일명 모드 판별 실패, iteration 커버 그룹 없음,
  헤더 개수 불일치)
- ㉱ 파일 인코딩 `utf-8` 고정이 BOM/CP949 입력에서 어떻게 되는지
  (외부에서 반입되는 실물 파일 전제)
- ㉲ 실패를 조용히 흡수하는 곳: `sim.py`의 `max(1, frames - errors)`,
  `max(elapsed, 1e-9)` 등이 이상값을 감추는지

대상: 전 파일, 특히 `llr_matrix.py:97-136`, `channel.py:24-40`, `run.py:34-65`

---

### P15. 성능과 실물 규모 대응

경량 시뮬레이터의 존재 이유가 스크리닝 속도이므로 규모 확장성이 요구사항의 일부다.

- ㉮ column 루프(147) x edge 루프(평균 3.8) x iteration x 배치에서 `np.roll`이
  edge마다 2회 호출된다. 실물 max_iter(문서상 120)에서의 비용
- ㉯ `pcm.syndrome`이 E=553 edge를 Python 루프로 돈다. 배치마다 1회 호출되는 위치
- ㉰ restart iteration의 `fill()` 전체 재초기화 비용과 빈도
- ㉱ 메모리: `(B, E, z)` uint8 esgn, `(B, M_b, z)` float32 4종. batch=64에서 실제 사용량과
  실물 파라미터에서의 증가
- ㉲ 배치 압축이 실제로 속도 이득을 주는 구간(FER이 낮으면 대부분 조기 성공)
- ㉳ `mpi_runner`가 복사되지 않았는데 새 config 스키마와 어떻게 맞출지

대상: `decoder.py` 루프 전체, `pcm.py:78-85`, `sim.py`, 본체 `mpi_runner.py`

---

## 관점 간 관계 (MECE 점검)

- P1/P2/P6은 "원본 대조" 축이지만 대상이 다르다 (산술 / 판정 타이밍 / 테이블 선택).
- P4/P9는 둘 다 인터페이스지만 P4는 이 폴더 내부 계약, P9는 본체 반영 시 외부 파괴다.
- P5/P12는 둘 다 LLR matrix지만 P5는 파서 코드, P12는 데이터 파일 자체와 커버리지다.
- P10/P13은 둘 다 문서지만 P10은 "무엇을 안 했나"(스코프), P13은 "쓴 것이 맞나"(사실)다.
- 우선순위 제안: P1, P2, P5, P6이 결과 정확성을 좌우하는 축이고,
  P9는 본체 반영 자체를 막을 수 있는 축이다.
