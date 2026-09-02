# Round 3 검증 — 팀 a 워커 2 (A-2 / A-3 / A-4)

검증 대상: A-2·A-3 (파일명 오인식 양방향), A-4 (-0.0 부호 소실, 승격 판정, 처방).
Round 2의 스크립트와 결론을 쓰지 않고 코드에서 직접 유도한 뒤 새로 실행해 증거를 확보했다.

---

## ㉮ 가설별 증거 확인 표

### H1 (A-2) 정방향 오인식 — 사람이 만든 3-bit 파일 이름에 `uniform`이 들어가면 균일 레벨로 읽힌다

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|-----------|------|
| E1-1 부분문자열 검사 | 확인됨 | `llr_matrix.py:170` `is_uniform = "uniform" in os.path.basename(path).lower()`, `llr_matrix.py:202-203` `edge_mag = uniform_edge_mag(num_param - MODE_CH_LEN[mode]) if is_uniform else None`, `llr_matrix.py:46` `_NAME_RE = re.compile(r"LLR_MATRIX_(HD\|2SD\|3SD)_", re.IGNORECASE)` + `llr_matrix.py:165` `_NAME_RE.search(os.path.basename(path))` | 모드 판별이 `search`라 basename 어디에서든 매칭하고, uniform 판별은 basename 전체에 대한 부분문자열 검사다 |
| E1-2 독립 재현 (로드) | 확인됨 | 위와 동일 | 아래 표, 6개 이름 전부 예외 0건·경고 0건 |
| E1-3 끝까지 조용히 복호 | 확인됨 | 예외·경고 경로 없음 | FER 0.8906 대 0.9688, BER 최대 5.3배 차이 |
| E1-4 config 도달 가능 | 확인됨 | `run.py:187-189` `_path_pair("decoder.llr_matrix", ...)` → `run.py:117` `os.path.join(_require(..., "dir"), _require(..., "file"))`. 파일명 제약 없음 | 실측 이름 전부 `load_config` → `setup` → 디코딩까지 도달 |

**E1-2 실측** (`Input/LLR/LLR_MATRIX_HD_1.txt`를 scratchpad에 복사한 뒤 이름만 바꿔 `LLRMatrix.load`):

| 파일명 | 결과 | th_len | edge_mag | 경고 |
|--------|------|--------|----------|------|
| `LLR_MATRIX_HD_1.txt` (대조군) | 정상 | 3 | `[7, 5, 3, 1]` | 없음 |
| `LLR_MATRIX_HD_nonuniform_1.txt` | 정상 | 3 | `[3, 2, 1, 0]` | 없음 |
| `LLR_MATRIX_HD_uniformity_1.txt` | 정상 | 3 | `[3, 2, 1, 0]` | 없음 |
| `LLR_MATRIX_HD_uniform_backup_1.txt` | 정상 | 3 | `[3, 2, 1, 0]` | 없음 |
| `LLR_MATRIX_HD_1_UNIFORM.txt` | 정상 | 3 | `[3, 2, 1, 0]` | 없음 |
| `my_uniform_dir_LLR_MATRIX_HD_1.txt` | 정상 | 3 | `[3, 2, 1, 0]` | 없음 |

마지막 두 줄은 `lower()` 때문에 대문자 표기도 걸리고, `_NAME_RE.search`가 basename 중간의
`LLR_MATRIX_HD_`도 잡아내 접두사가 붙은 이름까지 로드된다는 뜻이다.

**E1-3 실측** (H-matrix `example_18x147_z256.qc`, `fixed_error` 채널, seed 0, 128 프레임, 배치 128):

| 매트릭스 | edge_mag | 에러 20 bit FER | 에러 20 bit BER | 에러 100 bit BER | 에러 200 bit BER |
|----------|----------|------|------|------|------|
| `LLR_MATRIX_HD_1.txt` | `[7,5,3,1]` | 0.8906 | 5.937e-05 | 3.199e-04 | 6.280e-04 |
| `LLR_MATRIX_HD_nonuniform_1.txt` | `[3,2,1,0]` | 0.9688 | 8.906e-05 | 9.826e-04 | 3.339e-03 |
| `LLR_MATRIX_HD_0.txt` | `[7,5,3,1]` | 0.8906 | 6.062e-05 | 4.106e-04 | |
| `LLR_MATRIX_HD_nonuniform_0.txt` | `[3,2,1,0]` | 0.9688 | 9.487e-05 | 1.228e-03 | |

같은 파일 내용, 같은 seed, 같은 프레임인데 FER이 0.8906 대 0.9688로 갈리고 BER은 최대 5.3배
차이가 난다. 두 실행 모두 예외 0건, 경고 0건으로 끝까지 복호하고 FER을 보고한다.
"조용히 다른 결과"라는 Round 2의 주장은 실증되었다.

### H2 (A-3) 역방향 오인식 — 생성된 3-bit 균일 매트릭스에서 `uniform`이 빠지면 `[7,5,3,1]`로 읽힌다

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|-----------|------|
| E2-1 `edge_mag=None`일 때 th_len==3만 통과 | 확인됨 | `llr_matrix.py:67-72` `if edge_mag is None: if self.th_len != 3: raise NotImplementedError(...)` → `edge_mag = [7, 5, 3, 1]` | 아래 표 |
| E2-2 num_bits=3 → num_param=4 산술 | 확인됨 | `llr_matrix.py:222` `top_level = 2**(num_bits-1) - 1 = 3`, `:224` `th = list(range(3, 0, -1)) = [3,2,1]`, `:227` `num_param = ch_len + top_level = 1 + 3 = 4`, `:64` `th_len = num_param - ch_len = 3` | num_param=4, th_len=3 실측 일치 |
| E2-3 독립 재현 | 확인됨 | 위와 동일 | 아래 표 |
| E2-4 num_bits 4·5·6은 `NotImplementedError` | 확인됨 | `llr_matrix.py:68-71` | 아래 표 |
| E2-5 `num_bits` 하한만 검사, 상한 없음 | 확인됨 | `run.py:195-196` `_check_int("decoder.internal_quantize", "num_bits", ..., 2)`, `run.py:102-107`은 하한만 본다 | num_bits=1 거부. 2·3·8·33·1000 전부 `load_config` 통과 |
| E2-6 자동 생성 이름에는 항상 `uniform`이 들어간다 | 확인됨 (Round 2 서술 일부 반박) | `run.py:209-211` `generated_name = f"LLR_MATRIX_{mode}_uniform_{num_bits}bit_ch{...}_iter{...}.txt"` | 아래 판정 |

**E2-3 / E2-4 실측** (`make_internal_uniform_matrix(channel_llr=8, max_iter=10, dv_max=4, mode="HD")`
합성 → `save()` → scratchpad에서 이름만 바꿔 `load()`):

| num_bits | top_level | num_param | th_len | `uniform` 포함 이름의 edge_mag | `uniform` 제거 이름의 결과 |
|----------|-----------|-----------|--------|-------------------------------|---------------------------|
| 2 | 1 | 2 | 1 | `[1, 0]` | `NotImplementedError` (th 1개) |
| **3** | **3** | **4** | **3** | **`[3, 2, 1, 0]`** | **`edge_mag=[7, 5, 3, 1]`, 예외 0건, 경고 0건** |
| 4 | 7 | 8 | 7 | `[7..0]` | `NotImplementedError` (th 7개) |
| 5 | 15 | 16 | 15 | `[15..0]` | `NotImplementedError` (th 15개) |
| 6 | 31 | 32 | 31 | `[31..0]` | `NotImplementedError` (th 31개) |

"3-bit만 조용히 통과한다"는 한정은 정확하다. num_bits=2도 `th_len=1`이라 걸리므로 조용히
통과하는 경우는 num_bits=3 하나뿐이다.

**E2-6 도달 경로 판정**: `run.py:209-211`의 생성 파일명 규약은 `uniform`을 항상 포함하므로,
코드가 스스로 `uniform` 없는 이름을 만드는 경로는 없다. 역방향 오인식(A-3)이 성립하려면
사람이 생성 파일을 옮기거나 이름을 바꿔야 한다. Round 2의 "사용자 실수만의 문제가 아니다"는
**역방향(A-3)에 대해서는 반박됨**이다.

정방향(A-2)은 사정이 다르다. DAO 매트릭스는 그 성격이 비균일(non-uniform) 양자화이므로
`LLR_MATRIX_HD_nonuniform_1.txt` 같은 이름은 이 분야에서 자연스러운 작명이고, 그 이름이
정반대 의미(균일)로 해석된다. `llr_matrix.py:164`의 "사람이 만든 3-bit 파일에는 uniform이라는
단어를 쓰지 않는다"는 규약은 코드 주석에만 있고 검사도 경고도 없다. A-2 쪽은
"사용자 실수만의 문제가 아니다"가 성립한다.

### H3 (A-4) `-0.0` 부호 소실이 이미 실사용 출력을 틀리게 만드는가

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|-----------|------|
| E3-1 `-0.0` 발생·전파·소실 | 확인됨 | `decoder.py:155-157` `mag = np.full_like(mag_in, edge_mag[-1])` (균일 모드에서 `edge_mag[-1] = 0`, `llr_matrix.py:51` `uniform_edge_mag`), `decoder.py:158-163` `sgn = ±1` 후 `return sgn * mag`, `decoder.py:294` `np.roll`, `decoder.py:295` `new_sgn = (vnu_out < 0)` | `float32(-1)*float32(0) = -0.0`, `signbit(-0.0)=True`, `(-0.0 < 0)=False`, `np.roll`은 `-0.0` 보존(대조 일치), `np.abs(-0.0)=0.0` |
| E3-2 부호 소실 건수 계측 | 확인됨 | 위와 동일 | 아래 계측표 |
| E3-3 출력 오염 실증 | 확인됨 | `decoder.py:305-306` `log_csw_sum.append(int(prev_csw.sum()))` ← `decoder.py:261` `prev_csw = (check_sum ^ syndrome).sum(...)`; `decoder.py:312` `final_csw[idx_active] = prev_csw`; `decoder.py:343` / `:349` `_build_result`; `sim.py:67` `total_csw += log_csw_sum`, `sim.py:77` `int(decode_result["final_csw"][k])`; `run.py:448-449` `csw_mean` 열, `run.py:487-490` `final_csw` 열 | 아래 CSV 대조 |
| E3-4 복호 결과 불변 | 확인됨 (실측 범위 내) | `llr_matrix.py:292` `if self.group_type[group_idx] == GROUP_TYPE_ITER or row_end - row_start == 1:` → `prev_csw`를 쓰지 않고 row 반환. `make_internal_uniform_matrix`는 `llr_matrix.py:229`에서 ITER 타입 단일 row 그룹 1개를 만든다 | 아래 lockstep 대조 |
| E3-5 승격 판정 | 의견 제시 | | ㉰ 절 |

**E3-2 계측** (계측판은 `_vnu_quantize`를 서브클래스에서 재정의해 `super()` 호출 후 출력 배열을
세는 방식. `np.roll`은 순열이라 roll 전후 집계가 같음을 같은 실행에서 확인했다):

| 실행 조건 | `_vnu_quantize` 출력 원소 수 | magnitude 0 | `-0.0` 부호 소실 | mag0 대비 | roll 후 소실 | min\|vnu_out\| |
|-----------|------------------------------|-------------|------------------|-----------|--------------|----------------|
| 균일 6bit, ch=8, iter30, 64프레임, fixed_error 200 | 46,575,872 | 3,437 (0.007%) | 1,487 | 43.3% | 1,487 | 0.0 |
| 균일 6bit, 위와 같고 128프레임 | 91,877,632 | 7,180 (0.008%) | 3,109 | 43.3% | 3,109 | 0.0 |
| `LLR_MATRIX_HD_0.txt`, 64프레임 | 45,301,760 | **0** | **0** | — | 0 | **1.0** |
| `LLR_MATRIX_HD_1.txt`, 64프레임 | 181,207,040 | **0** | **0** | — | 0 | **1.0** |

**E3-3 CSV 오염 실증** (`python -m LDPC_base.run` 전 경로를 scratchpad 출력으로 실행. 균일 6bit,
`fixed_error` 600, 64프레임, log 전 항목 on. 원본판과 `np.signbit` 판정판을 같은 seed로 각각 실행):

| CSV 파일 | 열 | 다른 행 / 전체 | 원본판 앞부분 | `np.signbit` 판정판 앞부분 |
|----------|-----|----------------|---------------|---------------------------|
| `log_iter_{label}_p600.csv` | `csw_mean` | **30 / 30** | 2301.45, 1667.52, 1667.80, 1640.14, 1636.48 | 2300.62, 1657.88, 1590.28, 1511.86, 1503.47 |
| `log_fail_{label}_p600.csv` | `final_csw` | **64 / 64** | 1640, 1649, 1626, 1637, 1636 | 1513, 1503, 1492, 1489, 1482 |
| `fer_{label}.csv` | `fer` | 0 / 1 | 1.000000e+00 | 1.000000e+00 |

`csw_mean`은 최대 약 8.7%, `final_csw`는 최대 약 8.4% 어긋난다. 사용자가 `log.csw_per_iter`와
`log.fail_frame_detail`을 켜서 받는 CSV 값이 두 부호 판정 사이에서 전 행 다르다.

**E3-4 lockstep 대조** (원본판과 처방판을 같은 채널 출력으로 돌리고 iteration마다 `_vn_decide`의
판정 배열, `check_sum`, `min1`, `min1_pos`를 통째로 비교. 32프레임):

| 조건 | 판정(flip) 배열 전 iteration 동일 | `success` 동일 | iteration 경계에서 `check_sum`이 갈린 자리 | 그 자리의 `min1` |
|------|-----------------------------------|----------------|-------------------------------------------|------------------|
| 균일 6bit, fixed_error 300 | 동일 | 동일 | 7,040 | 전부 0 |
| 균일 6bit, fixed_error 600 | 동일 | 동일 | 249,283 | 전부 0 |
| 균일 6bit + 부분 스케줄, 300 | 동일 | 동일 | 13,639 | 전부 0 |
| 균일 6bit + 부분 스케줄, 600 | 동일 | 동일 | 218,787 | 전부 0 |

`check_sum`이 갈린 자리는 전부 `min1 == 0`이었다. 그 CN을 읽는 다른 엣지의 C2V magnitude가
0이므로 부호가 뒤집혀도 `sum_t`에 수치 기여가 없다. 이것이 "로그는 이미 오염됐는데 복호
결과는 같다"가 양립하는 실제 이유다. `llr_matrix.py:292`(ITER 단일 row 그룹은 `prev_csw`로 row를
고르지 않음)는 필요조건이고, 충분조건은 이 magnitude 0 성질이다.

다만 이 불변성은 구조적으로 보장된 것이 아니다. `min1 == 0`인 CN에서 `min1_pos`가 가리키는
엣지만은 `min2`(= RESET, 균일 6bit에서 31)를 읽으므로 magnitude가 0이 아니고, 그 엣지의 C2V
부호가 두 판정에서 갈리는 자리를 직접 세어 보면 존재한다.

| 조건 (32프레임) | `min1==0`인 CN 자리 | `min1_pos` 엣지의 C2V 부호가 갈린 자리 | 그중 magnitude 0이 아닌 것 |
|------|------|------|------|
| 균일 6bit, 300 | 18,542 | 138 | 138 |
| 균일 6bit, 600 | 594,958 | 21,768 | 21,768 |
| 균일 6bit, 900 | 669,784 | 29,377 | 29,377 |

기본 column 순서(`decoder.py:126-128` `range(self.code.N_b)`)에서는 이 자리가 실제로 소비되기 전에
같은 CN의 더 앞선 zero 엣지가 `min1_pos`를 가져가 magnitude 0으로 덮이기 때문에 결과가 같게
나온다. 순서를 깨면 결과까지 갈린다 (E4-5 참조).

### H4 (A-4 처방) `new_sgn = np.signbit(vnu_out).astype(np.uint8)`

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|-----------|------|
| E4-1 3-bit 파일 경로는 magnitude 0 불가 | 확인됨 | `llr_matrix.py:72` `edge_mag = [7, 5, 3, 1]`, `decoder.py:155` `mag = np.full_like(mag_in, edge_mag[-1])` = 1, `decoder.py:156-157` 캐스케이드는 `edge_mag[k]` (7·5·3) 중 하나로만 덮어쓴다. 어떤 th·raw 조합에서도 mag ∈ {7,5,3,1}이라 최소가 1이다. `decoder.py:158-163` `sgn * mag`의 절대값도 최소 1 | `HD_0` 45,301,760 원소, `HD_1` 181,207,040 원소 전수에서 `min\|vnu_out\| = 1.0`, mag0 0건 |
| E4-2 restart row의 -1 값 경로 포함 | 확인됨 | `LLR_MATRIX_HD_0.txt`는 restart iteration 2를 가지며 `row_th` 최소 -1, `row_ch`에 -1 포함. `decoder.py:157` `mag = np.where(mag_in >= th[:, k, None], edge_mag[k], mag)`에서 th=-1이면 `mag_in >= -1`이 항상 참이라 k=0까지 덮어써 `edge_mag[0] = 7`이 된다 | 위 실측이 restart iteration을 포함한 5 iteration 전체이며 mag0 0건 |
| E4-3 비트 단위 보존 | 확인됨 | | 아래 표 |
| E4-4 균일 모드에서의 변화 방향 | 확인됨 (단 "더 옳다"의 근거는 C++에서 나오지 않음) | | 아래 |
| E4-5(a) CSW 타입 그룹 잠복 경로 | 확인됨 (코드 근거) | `llr_matrix.py:297-301`은 `prev_csw <= self.row_csw[row]`로 row를 고른다. 오염된 `prev_csw`가 곧 row 선택이 되므로 복호 결과가 갈린다. 현재 `make_internal_uniform_matrix`는 `llr_matrix.py:229`에서 ITER 단일 row 그룹만 만들어 이 경로가 잠자고 있다 | 미실행 (코드로 판정 가능) |
| E4-5(b) `_column_order` 재정의 잠복 경로 | 확인됨 | `decoder.py:126-128` `_column_order`는 교체 지점이다 | 아래 스케줄 표 |
| E4-6 처방의 dtype 부작용 | 확인됨 (부작용 없음) | `decoder.py:185` `check_sum[:, row_blk, :] ^= new_sgn`, `decoder.py:186` `edge_sgn[:, edge, :] = new_sgn` | `np.signbit(int32 배열)` 동작, `uint8 ^= bool` in-place 동작(dtype uint8 유지), `uint8[...] = bool` 대입 동작, `.astype(np.uint8)`도 정상 |

**E4-3 비트 단위 보존 실측** (같은 채널 출력으로 원본판과 처방판을 각각 돌려 `np.array_equal` 대조.
64프레임, `fixed_error` 200):

| 매트릭스 | success | decode_success_iteration | final_err_bits | log_active | log_csw_sum | log_err_sum | final_csw | final_err_by_dv |
|----------|---------|--------------------------|----------------|------------|-------------|-------------|-----------|-----------------|
| `LLR_MATRIX_HD_0.txt` (restart 포함) | 동일 | 동일 | 동일 | 동일 | 동일 | 동일 | 동일 | 동일 |
| `LLR_MATRIX_HD_1.txt` | 동일 | 동일 | 동일 | 동일 | 동일 | 동일 | 동일 | 동일 |

두 파일 모두 8개 배열 전부 동일하다. column 순서를 forward / reverse / alternate / shuffle 넷으로
바꿔 돌려도 3-bit 파일 경로는 전 항목 동일했다. **처방이 3-bit 파일 경로 동작을 비트 단위로
보존한다는 주장은 확인됨**이다.

**E4-4 균일 모드에서의 변화** (같은 실행에서):

- ㉮ 바뀌는 것: `log_csw_sum`(전 iteration), `final_csw`(64프레임 중 55프레임, 최대 차이 7),
  CSV의 `csw_mean`과 `final_csw` 열
- ㉯ 바뀌지 않는 것: `success`, `decode_success_iteration`, `final_err_bits`, `log_err_sum`,
  `final_err_by_dv`, FER, BER (기본 column 순서에서 fixed_error 300·400·450·500·600 전부)
- ㉰ "더 옳은 값"의 근거: **C++에서는 나오지 않는다.** C++의 부호 추출은
  `decoder.cpp:2750-2755` `check_in = VNU_out3[...]; if (check_in >= 0) v2c_sgn = V_PLUS; else v2c_sgn = V_MINUS;`
  로, 지금의 `decoder.py:295` `new_sgn = (vnu_out < 0)`와 정확히 같은 규칙이다. 그리고 C++의
  레벨 집합에는 magnitude 0이 없다 (`common.h:337` `EDGE_MAG_1 1`, `common.h:341` `EDGE_MAG_1 1`이
  최소 레벨). 즉 C++에는 "magnitude 0인 메시지"라는 상태 자체가 없어 어느 부호가 옳은지에 대한
  판례를 주지 않으며, 굳이 C++ 규칙을 문자 그대로 적용하면 magnitude 0은 PLUS다.
  `-0.0`을 부호 있는 값으로 취급할 근거는 `decoder.py:159-162`의 zero 처리 의도
  (`raw==0`이면 `vnu_in`의 부호를 물려준다)뿐이다. 처방을 채택하면 이 의도가 CN 상태까지
  일관되게 이어지고, 채택하지 않으면 의도가 `_vnu_quantize` 안에서만 살고 밖에서 버려진다.

**E4-5(b) `_column_order` 재정의 잠복 경로 실측** (32프레임, 균일 6bit ch8 iter30):

| column 순서 | 균일 6bit 복호 결과 (`final_err_bits`) | 균일 6bit `log_csw_sum` | 3-bit 파일(`HD_1`) 전 항목 |
|-------------|----------------------------------------|--------------------------|----------------------------|
| forward (`range(N_b)`, 본체 기본) | 동일 (300: 0 vs 0, 600: 31676 vs 31676) | 다름 | 동일 |
| reverse (`range(N_b-1, -1, -1)`) | 동일 (600: 31809 vs 31809) | 다름 | 동일 |
| alternate (홀수 iteration만 역순) | **다름** (300: 29050 vs 28571, 600: 44030 vs 44101) | 다름 | 동일 |
| shuffle (iteration별 무작위 순열) | **다름** (300: 14241 vs 14393, 600: 35150 vs 35204) | 다름 | 동일 |

Round 2가 든 잠복 경로 (b)는 **확인됨**이다. `_column_order`를 iteration마다 순서가 달라지는
스케줄(layered, informed dynamic scheduling 계열)로 재정의하면 `-0.0` 부호 소실이 복호 결과의
잔여 에러 비트까지 바꾼다. 부분 갱신 스케줄(`range(start, N_b, keep)`)처럼 순서가 단조 증가로
유지되는 경우에는 결과가 보존됐다. 즉 위험 조건은 "부분 갱신"이 아니라 "iteration 사이의 순서
뒤바뀜"이다.

---

## ㉯ Round 2 수치와 독립 재현 수치의 대조

| 항목 | Round 2 | 이번 독립 재현 | 대조 |
|------|---------|----------------|------|
| `-0.0` 부호 소실 건수 | 3,847 | 1,487 (64프레임) / 3,109 (128프레임) | 실행 조건이 달라 절대값은 다르다. 두 결과 모두 "0이 아닌 다수 발생" |
| 전체 원소 수 | 17,979,136 | 46,575,872 (64프레임) / 91,877,632 (128프레임) | Round 2 값은 `553 x 256 x 127`로 프레임-iteration 누계가 127. 이번은 같은 지표로 329(64프레임) |
| mag0 중 부호 소실 비율 | 38.5% | **43.3%** (64프레임과 128프레임 모두) | 같은 크기 대역. 채널 포인트와 iteration 수 차이로 설명된다 |
| 3-bit 파일 경로 mag0 | 0 (구조적 주장) | **0** (`HD_0` 45,301,760 원소, `HD_1` 181,207,040 원소 전수, `min\|vnu_out\| = 1.0`) | 일치, 실측으로 뒷받침 |
| 복호 결과 불변 | 불변 | 기본 순서에서 불변 (판정 배열까지 비트 동일). 순서를 뒤바꾸는 스케줄에서는 **가변** | 조건부로 일치 |
| CSW 로그 오염 | 오염됨 | 오염됨 (`csw_mean` 30/30행, `final_csw` 64/64행 다름, 최대 8.7% 어긋남) | 일치, 수치 추가 |

절대 건수를 맞추려면 Round 2가 쓴 config(프레임 수, 채널 포인트, `num_bits`, `channel_llr`,
`max_iter`)가 필요하다. 이번 재현은 조건을 명시했으므로 그대로 재실행하면 같은 수가 나온다.

---

## ㉰ A-4 HIGH 승격 판정 의견

심각도 정의: CRITICAL(프로세스 중단·비가역 손상) / HIGH(틀린 결과를 내지만 진행) /
MEDIUM(엣지케이스 위험).

**HIGH를 지지하는 논거**

- ㉮ 사용자가 `log.csw_per_iter`와 `log.fail_frame_detail`을 켜서 받는 CSV의 값이 이미 틀리다.
  실측에서 `csw_mean` 30행 전부, `final_csw` 64행 전부가 다른 값이었고 어긋남이 최대 8.7%다.
  가설적 위험이 아니라 현재 산출물의 값이다
- ㉯ CSW는 이 시뮬레이터에서 수렴 진단의 주 지표다. `run.py:36-39`가 CSW 로그를 분석 목적으로
  내세우고 `docs`의 스크리닝 흐름도 여기에 기댄다. 아이디어 스크리닝에서 CSW 곡선을 보고
  판단하면 틀린 근거로 판단하게 된다
- ㉰ 오류가 조용하다. 예외도 경고도 없고, `-0.0`은 `np.abs`를 통과하면 `0.0`과 구별되지 않아
  값만 보고는 알아챌 수 없다
- ㉱ 잠복 경로가 실재한다. E4-5(b)에서 `_column_order`를 재정의하면 복호 결과의 잔여 에러
  비트까지 갈렸다. 이 저장소의 목적이 논문 아이디어 이식이고 `_column_order`가 명시된 교체
  지점(`decoder.py:126-128`, 모듈 docstring 표의 layered / informed dynamic scheduling)이므로,
  의도된 사용 방식을 따랐을 때 결과 오류가 되는 경로다

**MEDIUM을 지지하는 논거**

- ㉠ 논문 스크리닝의 1차 판정 지표인 FER, BER, 수렴 iteration은 정확하다. 실측에서 `success`,
  `decode_success_iteration`, `final_err_bits`, `log_err_sum`, `final_err_by_dv`가 전부 동일했다
- ㉡ 발현 조건이 균일 양자화 모드(`use_input_llr_matrix: false`)로 한정된다. DAO 파일 경로에는
  magnitude 0 레벨이 없어 영향이 0이다 (전수 실측)
- ㉢ 오염의 크기가 8% 대이고 방향이 한쪽(원본판이 더 큰 CSW)으로 치우쳐 있어, 곡선의 모양과
  수렴 추세 자체는 뒤집히지 않는다
- ㉣ 결과를 바꾸는 잠복 경로(E4-5(a)(b))는 현재 코드에 존재하는 실행 경로가 아니라 앞으로
  작성될 자식 클래스에서 열린다

**결론 (이것은 의견이다)**: **HIGH로 승격하는 데 찬성한다.** 결정적인 것은 ㉮와 ㉯다. 심각도
정의의 HIGH는 "틀린 결과를 내지만 진행"이고, 사용자가 명시적으로 켠 로그 옵션의 출력 숫자가
전 행 틀린 채로 CSV에 저장되는 것은 이 정의에 그대로 들어맞는다. "결과"를 FER/BER으로만 좁게
읽으면 MEDIUM이지만, 이 시뮬레이터가 사용자에게 내주는 산출물 전체를 결과로 보면 HIGH다.
㉱의 잠복 경로가 교체 지점이라는 설계 의도와 맞물리는 점이 판단을 굳혔다.

한 가지 단서를 붙인다. 승격의 근거는 "CSW 로그가 틀렸다"이지 "복호가 틀렸다"가 아니므로,
보고서 본문에는 "FER/BER은 정확하고 CSW 계열 로그만 틀리다"를 함께 적어야 한다. 그래야
사용자가 이미 낸 FER 결과를 불필요하게 폐기하지 않는다.

---

## ㉱ 처방 판정

**처방 유효** — `decoder.py:295`를 `new_sgn = np.signbit(vnu_out).astype(np.uint8)`로 바꾸는 처방을
채택할 수 있다.

- ㉮ 3-bit 파일 경로 보존: 두 파일 전수(`HD_0` 45,301,760 원소, `HD_1` 181,207,040 원소)에서
  `min|vnu_out| = 1.0`, magnitude 0이 0건이므로 `-0.0`이 발생할 수 없고, 실측에서 8개 결과
  배열이 전부 비트 단위로 동일했다. restart row의 -1 값 경로(`HD_0` iteration 2)도 포함된다.
  column 순서를 넷으로 바꿔도 동일했다
- ㉯ dtype 부작용 없음: `np.signbit`은 정수 배열에도 동작하고, `.astype(np.uint8)`를 붙이면
  `decoder.py:185` `check_sum ^= new_sgn`(uint8 XOR)과 `decoder.py:186` `edge_sgn[...] = new_sgn`의
  dtype 계약이 지금과 동일하게 유지된다. `.astype` 없이 bool을 넘겨도 numpy 1.26.4에서
  in-place XOR과 대입 모두 정상 동작하지만, `_cnu_update`가 교체 지점이라 자식 클래스가
  `new_sgn.dtype`에 기댈 수 있으므로 `.astype(np.uint8)`를 붙이는 쪽을 권한다
- ㉰ 균일 모드에서 CSW 로그 값이 바뀐다. 이것은 처방의 목적이며, 바뀐 값이 "옳다"는 근거는
  C++가 아니라 `decoder.py:159-162`가 raw==0에 부호를 부여하는 설계 의도의 일관성이다
  (E4-4 ㉰ 참조). 처방을 넣는 커밋에는 이 판단 근거를 함께 남겨야 한다

**함께 검토할 대안** (배타 아님, 조합 가능)

- ㉠ 이 처방은 `-0.0`이라는 IEEE 754 표현에 의존한다. `_vnu_quantize`를 재정의한 자식 클래스가
  `mag`를 정수 dtype으로 돌려주면 `-0.0`이 존재하지 않아 처방이 조용히 무력해진다.
  부호를 값의 비트가 아니라 별도 배열로 돌려주는 구조(`_vnu_quantize`가 `(sgn, mag)` 쌍을
  반환)가 근본적이다. 다만 교체 지점의 시그니처를 바꾸는 변경이라 등급이 올라간다
- ㉡ 팀 A의 A-5 처방("0 레벨 제거, 최소 1")을 채택하면 `-0.0` 자체가 발생하지 않아 A-4가
  소멸한다. A-5 처방이 채택되면 이 처방은 방어선으로만 남는다. 두 처방은 배타적이지 않다

---

## ㉲ Round 2가 놓쳤거나 틀리게 적은 것

- ㉮ **A-3의 도달 경로 서술이 과하다.** `run.py:209-211`의 생성 파일명은 항상 `uniform`을
  포함하므로 역방향 오인식은 사람이 파일을 옮기거나 개명해야만 성립한다. "사용자 실수만의
  문제가 아니다"는 A-2에는 맞고 A-3에는 맞지 않는다
- ㉯ **A-2의 위험도가 오히려 과소 서술됐다.** DAO 매트릭스는 그 자체가 비균일 양자화이므로
  `nonuniform`이라는 단어가 파일명에 들어가는 것이 자연스럽고, 그 이름이 정반대로 해석된다.
  또한 `_NAME_RE.search`(`llr_matrix.py:165`)가 basename 어디서든 매칭하므로
  `uniform_grid_LLR_MATRIX_HD_1.txt` 같은 접두사 붙은 이름까지 로드된다
- ㉰ **A-4의 "복호 결과 불변"은 조건부다.** 기본 column 순서에서만 성립한다. `_column_order`를
  iteration마다 순서가 뒤바뀌는 스케줄로 재정의하면 잔여 에러 비트까지 갈린다 (실측:
  29050 vs 28571). Round 2는 이 잠복 경로를 언급했으나 "magnitude 0이 아닌 C2V까지 잘못된
  부호를 받는다"의 실제 기제를 특정하지 않았다. 기제는 `min1 == 0`인 CN에서 `min1_pos`가
  가리키는 엣지만 `min2`(= RESET)를 읽는다는 점이다 (`decoder.py:135` `np.where(min1_pos_row == edge, min2_row, min1_row)`,
  `decoder.py:181-183` min1 교체 시 min2 = RESET). 실측으로 그런 자리가 fixed_error 600에서
  21,768개 존재함을 확인했다
- ㉱ **"부분 갱신 스케줄이면 위험"은 정확하지 않다.** 순서가 단조 증가로 유지되는 부분 갱신
  (`range(start, N_b, keep)`)에서는 결과가 보존됐다. 위험 조건은 iteration 사이의 순서 뒤바뀜이다
- ㉲ **처방이 "더 옳은 값"이라는 근거를 C++에서 찾을 수 없다.** `decoder.cpp:2750-2755`의
  `check_in >= 0 → V_PLUS`는 현재 파이썬 규칙과 같고, C++ 레벨 집합에 magnitude 0이 없어
  (`common.h:337`, `common.h:341` `EDGE_MAG_1 1`) 판례를 주지 않는다. 처방의 정당화는 C++ 대조가
  아니라 `decoder.py:159-162`의 설계 의도 일관성에서 나온다
- ㉳ **`num_bits` 상한 부재는 별도 위험이다.** `run.py:195-196`은 하한 2만 본다. num_bits=1000도
  `load_config`를 통과하며, `llr_matrix.py:222-224`가 `2**999 - 1` 길이의 th 리스트를 만들려
  하므로 메모리가 터진다. A-3 검증 과정에서 나온 부수 발견이다

---

## ㉳ 실행 환경 정보와 `git status --short`

- Python 3.11.7 (MSC v.1937 64bit), numpy 1.26.4, Windows 10 Home 19045
- cwd: `d:/OneDrive/My_Projects/LDPC_dev/2_LDPC_light` (전 실행 공통)
- H-matrix: `Input/H_matrix/example_18x147_z256.qc` (base 18x147, z=256, N=37632, K=33024,
  rate 0.8776, base edge 553개, column degree 분포 {2:17, 3:1, 4:129} → dv_max=4)
- 실험 스크립트, config 사본, 복사·개명한 LLR matrix, 시뮬 산출물은 전부 scratchpad
  (`.../scratchpad/w_a2/`)에 두었다. 저장소 파일은 읽기만 했고, 코드 변형은 원본 수정 없이
  서브클래스 재정의(`SignbitMixin`, `CountingMixin`, `RecordMixin`, `_column_order` 재정의)로만 했다
- 작업 종료 시 `cd d:/OneDrive/My_Projects/LDPC_dev && git status --short` 결과:

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

사전 상태와 동일한 3줄이다. `Input/LLR/`의 파일 3개도 변동 없고 `Sim_Output/`에 새 폴더가
생기지 않았다. 저장소 오염 없음.
