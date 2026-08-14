# Round 3 검증 워커 b_1 — B-1 (frames_per_batch가 난수 실현값을 바꾼다)

작성: 2026-08-08 15:28:04
대상: HEAD (e6282b1) + 작업트리. 실행 환경 numpy 1.26.4, CPU 24코어

---

## 1. 가설별 판정

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| H1 (사실) frames_per_batch만 128→64로 바꾸면 FER / post_fec_ber / 실패 프레임 상세가 달라진다 | **확인됨** | 실측: fixed_error p360에서 FER 3.867e-1 → 3.750e-1, 실패 프레임 수 198 → 192. p350은 FER 동일이나 BER 7.572e-4 → 7.527e-4, `log_fail` 내용 전면 불일치 |
| H2 (원인) 원인은 `channel_fn`이 배치마다 `generate_message`로 batch×K개 난수를 먼저 소비하는 순서다 | **확인됨** | 그 호출만 난수를 소비하지 않는 스텁으로 바꾼 대조군에서 두 배치 크기의 결과가 CSV 바이트 단위로 일치 |
| H3 (숨은 전제) 난수 스트림만 고치면 배치 무관이 성립한다 | **반박됨** | 대조군(스트림 정렬 완료)에서도 `max_frame_errors`가 구속하면 종료 프레임 수가 배치 경계로 양자화되어 결과가 갈린다. 실측: p380에서 b128은 frames=128/errors=119/FER 9.297e-1, b64는 frames=64/errors=61/FER 9.531e-1 |
| H4 (처방 P1) `generate_message` 호출 제거로 문제가 해소되고 새 문제가 없다 | **부분 확인** | fixed_error와 rber는 해소. strong_error는 해소되지 않음(채널 자체가 배치 분해 불가). 또한 H3 때문에 "배치 무관"은 여전히 성립하지 않음. 부작용으로 기존 실행 기록과의 비트 단위 재현성이 끊어짐 |
| H5 (처방 P2) 프레임 단위 스트림 파생은 실물 인코더 도입 후에도 배치 무관을 계약으로 유지한다. 더 싼 대안(잡음 전용 generator 분리)도 같은 효과를 낸다 | **부분 확인** | 프레임 단위 파생은 채널 3종 전부에서 배치 무관 성립, 비용은 배치 1회 호출과 사실상 동일(1.0배). 반면 "generator 분리"는 fixed_error와 rber에서만 성립하고 strong_error에서는 실패하므로 **같은 효과가 아니다**. 그리고 어느 처방도 H3의 종료 규칙 문제는 건드리지 못한다 |

**종합**: B-1의 사실 부분은 확인. 심각도 HIGH 유지가 타당하다(같은 seed·같은 config에서 서로 다른 수치가 나오고 문서 3곳이 반대로 단언).
다만 Round 2가 붙인 처방은 **불완전**하다. 처방을 적용해도 (ㄱ) strong_error는 여전히 배치 의존이고 (ㄴ) `max_frame_errors` 종료 규칙 때문에 배치 무관은 성립하지 않는다.
문서를 "결과에 영향 없음"에서 고칠 때, 무엇을 보장하는지의 문언까지 같이 정해야 한다(아래 §4).

---

## 2. 증거표

| 증거 | 판정 | 코드 근거 | 실측 |
|------|------|----------|------|
| **E1** `generate_message` 난수 소비량과 `encode`의 msg 폐기 | **확인됨** | `LDPC_base/encoder.py:13` `random_generator.integers(0, 2, size=(batch, code.K), dtype=np.uint8)`, `encoder.py:19` `return np.zeros((msg.shape[0], code.N_b, code.z), ...)` (msg는 shape만 쓰고 값은 버림) | K=33024. batch=128이면 호출당 4,227,072개 소비. 소비 후 generator 상태가 batch에 따라 다름을 직접 확인(E4-7) |
| **E2** 호출 순서, generator 생성 지점, 배치 루프와 종료 조건 | **확인됨** | `run.py:353-357` `channel_fn`이 `generate_message` → `encode` → `chan.CHANNELS[...]` 순서. `run.py:398` `random_generator = np.random.default_rng([seed, channel_index, int(1e6 * point)])` (포인트마다 1개, 배치마다가 아님). `sim.py:54-55` `while frames < max_frames and errors < max_frame_errors:` / `batch = min(frames_per_batch, max_frames - frames)` | 종료 검사는 배치 1개를 다 돌린 뒤에만 일어난다 |
| **E3** 문서 3곳의 "결과 영향 없음" 서술 | **확인됨** | ㉮ `LDPC_base/run.py:32-33` "frames_per_batch: 한 번에 동시 복호하는 프레임 수 (속도와 메모리 조절용, 결과에 영향 없음)"<br>㉯ `2_LDPC_light/config.json:44` "frames_per_batch: 한 번에 동시 복호하는 프레임 수 (속도/메모리용, 결과 영향 없음)"<br>㉰ `2_LDPC_light/README.md:79-80` "`run.frames_per_batch`: 한 번에 동시 복호하는 프레임 수 (속도와 메모리 조절용, 결과에 영향 없음)" | `Ideas/vanilla/config.json`에는 같은 서술 **없음**(`run` 블록에 `_desc` 자체가 없다, `Ideas/vanilla/config.json:23-28`). 문서 수정 대상은 3곳이 맞다 |
| **E4** 채널별 배치 분해성 | **확인됨(채널마다 갈림)** | `channel.py:75` `_rand_positions`가 `random_generator.random((batch, N))` 1회, `channel.py:119,125` strong_error는 `random((B,N))` **뒤에** `permuted(err_pos, axis=1)`를 호출(난수 소비자 2개가 끼어듦) | fixed_error(300/400) **SAME**, rber(HD/3SD) **SAME**, strong_error(SER·SCR 2조합) **DIFF**. 단독 원시함수 확인: `random` SAME, `normal` SAME, `permuted` SAME, `integers(0,2,uint8)` SAME |
| **E5** end-to-end 본실험 | **확인됨** | 동작점 스윕으로 0<FER<1 구간 확보(아래 §3-A) | ㉮ 비포화(p350/p360, 종료 비구속): FER·BER·avg_iter·`log_fail`·`log_iter_hist` 전부 불일치<br>㉯ 포화(FER=1.0, 기본 config 계열 p200/p300): FER은 1.0으로 같고 **BER과 `log_fail` 내용이 다름**(6.309e-4 vs 6.319e-4) |
| **E6** 대조군(P1 검증, `generate_message` 스텁) | **확인됨** | `runner.py`가 `LDPC_base.encoder.generate_message`를 난수 0 소비 스텁으로 교체 후 `LDPC_base.run.main()` 호출 | 종료 비구속 조건에서 b128과 b64의 `fer_*.csv`(sec 열 제외 전 열), `log_fail_*.csv`, `log_iter_hist_*.csv`가 **완전 일치**. 포화 구간도 완전 일치. 원인 귀속(H2)과 P1의 유효 범위가 동시에 지지됨 |
| **E7(가)** 종료 규칙 비구속 + max_frames가 공배수 | **확인됨(완전 일치)** | `max_frame_errors=10^9`, `max_frames=512`(=128·4=64·8) | 대조군에서 두 배치 크기 결과 완전 일치. 곧 **디코더 자체는 배치 무관**이다(genie 마스킹 압축이 프레임별 결과를 바꾸지 않음) |
| **E7(나)** 종료 규칙 구속 | **반박됨(H3 성립 안 함)** | `sim.py:54` 종료 검사가 배치 루프의 while 조건에만 있음. 정지 프레임 수 = `frames_per_batch × ceil(f*/frames_per_batch)` (f* = 에러가 임계에 처음 도달한 프레임) | 대조군·`max_frame_errors=10`에서 p360: b128 frames=128/errors=37/FER 2.891e-1, b64 frames=64/errors=19/FER 2.969e-1. p380: b128 frames=128/errors=119/FER 9.297e-1, b64 frames=64/errors=61/FER 9.531e-1 |
| **E8** 처방 부작용 조사(all-zero 전제 위치) | **확인됨. `encoder.py` docstring 주장은 거짓** | 호출처 전수: `generate_message`는 `run.py:354` 1곳, `encode`는 `run.py:355` 1곳뿐. `cw`는 `channel.py`(43,50-51,78,84,91,116)까지만 가고 디코더로 전달되지 않는다. `decoder.py`의 genie는 `decoder.py:284` `bit_err = state.read_bit[:, col, :] ^ flip`로 **복호 비트 자체를 에러로 센다**(정답 all-zero 하드코딩, `decoder.py:32`·`decoder.py:318` 주석과 일치). `decoder_main(channel_out, ...)`에 cw 인자가 없음(`decoder.py:354`) | `encoder.py:5-6`의 "실물 인코더가 필요해지면 이 함수 내용만 채우면 되고 … 다른 곳은 손댈 필요가 없다"는 **거짓**. 실물 인코더 도입은 최소한 `decoder_main` 시그니처, `_process_column`의 에러 집계, `sim.py:61,84`의 post_fec_ber 집계까지 건드린다 |
| **E9** 기존 기록의 재현성 | **확인됨(git 회귀 근거는 아님, 다만 명시적 설계 제약은 있었음)** | `.gitignore:45` `Sim_Output/` → `2_LDPC_light/Sim_Output/`(10개)과 `Ideas/vanilla/Sim_Output/`(6개) **전부 미추적**(`git ls-files` 0건, `git check-ignore` 확인). README·docs에 수치 기준선 인용 없음 | 그러나 `_pm/done/20260807_리뷰후속수정/20260807_리뷰후속수정.md:49`에 "`fixed_error`가 쓰는 `_rand_positions`는 건드리지 않는다 (기존 결과 비트 단위 재현성 유지, r3 team_a 검증 결론)"가 남아 있다. P1·P2·대안 어느 쪽도 이 비트 단위 재현성을 끊는다. 저장소 회귀 테스트가 깨지지는 않지만 **과거 실행 기록과의 비교는 무효가 된다** |
| **E10** 처방 대안 비교 | **확인됨** | 아래 §4 표 | 비용 실측(batch=128 기준): `generate_message` 5.90 ms, `fixed_error_channel` 57.62 ms, `rber_channel` 93.31 ms, 프레임 단위 파생 128프레임 57.16 ms(배치 1회의 **1.0배**), `spawn(128)` 1.95 ms. 실행 전체는 7 f/s 수준이라 프레임당 복호가 약 143 ms이고 `generate_message`는 프레임당 0.046 ms(전체의 0.03%) |

---

## 3. 실측 원자료

공통: `seed=0`, `H_matrix=Input/H_matrix/example_18x147_z256.qc` (N=37632, K=33024, dv 히스토그램 {2:17, 3:1, 4:129}), `decoder.type=vanilla`.
실행: `d:\OneDrive\My_Projects\LDPC_dev\2_LDPC_light`에서 scratchpad의 `runner.py`가 `LDPC_base.run.main()`을 호출.
`--stub`은 `encoder.generate_message`를 `np.zeros((batch, code.K), np.uint8)` 반환(난수 소비 0)으로 교체한 대조군.

### A. 동작점 탐색 (균일 6-bit, channel_llr 8, max_iter 30, fixed_error, 128프레임)

| 에러 bit | 300 | 310 | 320 | 330 | 340 | 350 | 360 | 380 | 400 | 500~1000 |
|---|---|---|---|---|---|---|---|---|---|---|
| FER | 0 | 0 | 0 | 0 | 7.8e-3 | 9.4e-2 | 3.9e-1 | 9.5e-1 | 1.0 | 1.0 |

본실험 동작점으로 **350과 360**을 채택.

### B. E5 + E7(가): 종료 비구속 (`max_frame_errors=10^9`, `max_frames=512`)

| 조건 | point | FER | post_fec_ber | errors/frames | avg_decode_success_iteration |
|------|-------|-----|--------------|---------------|------------------------------|
| HEAD b128 | 350 | 8.984375e-02 | 7.571785e-04 | 46/512 | 14.970 |
| HEAD b64  | 350 | 8.984375e-02 | **7.527150e-04** | 46/512 | **15.030** |
| HEAD b128 | 360 | **3.867188e-01** | 3.407070e-03 | **198**/512 | 17.955 |
| HEAD b64  | 360 | **3.750000e-01** | 3.408263e-03 | **192**/512 | 18.181 |
| STUB b128 | 350 | 1.015625e-01 | 7.042917e-04 | 52/512 | 14.533 |
| STUB b64  | 350 | 1.015625e-01 | 7.042917e-04 | 52/512 | 14.533 |
| STUB b128 | 360 | 3.164062e-01 | 2.783950e-03 | 162/512 | 17.183 |
| STUB b64  | 360 | 3.164062e-01 | 2.783950e-03 | 162/512 | 17.183 |

로그 CSV 비교:

- HEAD: `log_fail_*_p350.csv` DIFF (첫 행부터 프레임 번호와 `final_err_bits`/`final_csw`가 다름. 예 A `0,42,302,42` ↔ B `0,331,943,331`), `log_fail_*_p360.csv` DIFF (행 수 199 ↔ 193), `log_iter_hist_*` 두 포인트 모두 DIFF
- STUB: `log_fail_*`, `log_iter_hist_*` 전부 **SAME**. `fer_*.csv`는 `sec`(실행 시간) 열만 다름

### C. E5 포화 구간 (기본 config 계열: `use_input_llr_matrix=true`, `LLR_MATRIX_HD_1.txt`, `max_frames=256`)

| 조건 | point | FER | post_fec_ber |
|------|-------|-----|--------------|
| HEAD b128 | 200 | 1.000000e+00 | 6.309042e-04 |
| HEAD b64  | 200 | 1.000000e+00 | **6.319422e-04** |
| HEAD b128 | 300 | 1.000000e+00 | 1.059085e-03 |
| HEAD b64  | 300 | 1.000000e+00 | **1.068738e-03** |
| STUB b128 | 200 | 1.000000e+00 | 6.408691e-04 |
| STUB b64  | 200 | 1.000000e+00 | 6.408691e-04 |
| STUB b128 | 300 | 1.000000e+00 | 1.051196e-03 |
| STUB b64  | 300 | 1.000000e+00 | 1.051196e-03 |

HEAD의 `log_fail_*_p200.csv`는 첫 행부터 다르다(A `0,23,74,0,0,0,23` ↔ B `0,25,82,0,0,0,25`).
곧 **FER가 1.0으로 포화된 구간에서도 실패 프레임 상세와 post-FEC BER은 배치 크기에 따라 달라진다.** STUB에서는 완전 일치.

### D. E7(나): 종료 구속

D-1. HEAD, `max_frame_errors=20`, `max_frames=4096`

| 조건 | point | FER | post_fec_ber | errors/frames | avg_iter |
|------|-------|-----|--------------|---------------|----------|
| HEAD b128 | 350 | 1.054688e-01 | 8.795083e-04 | 27/256 | 15.153 |
| HEAD b64  | 350 | 8.984375e-02 | 7.313839e-04 | 23/256 | 15.133 |
| HEAD b128 | 360 | 3.906250e-01 | 3.607718e-03 | 50/**128** | 18.564 |
| HEAD b64  | 360 | 3.437500e-01 | 3.302127e-03 | 22/**64** | 17.452 |

D-2. STUB, `max_frame_errors=20`, `max_frames=4096` (이 설정에서는 정지 프레임 수가 우연히 일치)

| 조건 | point | FER | post_fec_ber | errors/frames |
|------|-------|-----|--------------|---------------|
| STUB b128 | 350 | 8.593750e-02 | 6.205241e-04 | 22/256 |
| STUB b64  | 350 | 8.593750e-02 | 6.205241e-04 | 22/256 |
| STUB b128 | 360 | 2.890625e-01 | 2.599807e-03 | 37/128 |
| STUB b64  | 360 | 2.890625e-01 | 2.599807e-03 | 37/128 |

D-3. **STUB, `max_frame_errors=10`** (H3 반증. 난수 스트림이 완전히 정렬된 상태인데도 결과가 갈린다)

| 조건 | point | FER | post_fec_ber | errors/frames | avg_iter |
|------|-------|-----|--------------|---------------|----------|
| STUB b128 | 360 | 2.891e-01 | 2.600e-03 | 37/**128** | 16.65 |
| STUB b64  | 360 | 2.969e-01 | 2.453e-03 | 19/**64** | 16.98 |
| STUB b128 | 380 | 9.297e-01 | 1.081e-02 | 119/**128** | 22.33 |
| STUB b64  | 380 | 9.531e-01 | 1.118e-02 | 61/**64** | **29.00** |

정지 프레임 수 = `frames_per_batch × ceil(f* / frames_per_batch)`이므로 f*가 64보다 작으면 b64는 64에서, b128은 128에서 멈춘다.
스트림이 정렬되면 b64의 측정은 b128 측정의 **앞부분 표본**이 되지만, 보고되는 수치는 여전히 다르다.
`avg_decode_success_iteration`은 22.33 → 29.00으로 30% 가까이 벌어졌다.

### E. E4 채널별 배치 분해성 (batch=128 한 번 vs batch=64 두 번)

| 채널 | 조건 | 결과 |
|------|------|------|
| fixed_error | n_err=300 | SAME (128/128 프레임 일치) |
| fixed_error | n_err=400 | SAME |
| rber | p=0.01, HD | SAME |
| rber | p=0.01, 3SD (hd/sd/cc 전부) | SAME |
| strong_error | E=300, SER 0.5, SCR 0.5 | **DIFF** (hd는 프레임 64부터, sd는 프레임 0부터) |
| strong_error | E=300, SER 0.3, SCR 0.9 | **DIFF** (동일 양상) |

원시 함수 단독: `random((B,N))` SAME, `normal(0,1,(B,N))` SAME, `permuted((B,300), axis=1)` SAME, `integers(0,2,(B,K),uint8)` SAME.

strong_error가 깨지는 이유는 원시 함수가 아니라 **순서**다.
`channel.py:119`가 `random((B,N))`을 먼저 뽑고 `channel.py:125`가 `permuted`를 호출하므로,
batch=64로 두 번 부르면 두 번째 `random` 호출이 첫 번째 `permuted`가 소비한 만큼 밀린다(hd 프레임 64부터 불일치).
`permuted`는 `random` 소비량이 batch에 비례해 달라진 뒤 시작하므로 sd는 프레임 0부터 불일치한다.
현재 strong_error는 2SD 전용이고 디코더가 2SD 산술 미구현이라(`decoder.py:371-374`) end-to-end로는 도달하지 않는다.
2SD 디코딩을 여는 순간 이 경로가 살아난다.

---

## 4. 처방 판정

### 4-1. 대안 비교표 (E10)

| 대안 | 배치 무관이 성립하는 범위 | 비용 | 실물 인코더 도입 후 유지 | 판정 |
|------|--------------------------|------|------------------------|------|
| **(ㄷ) P1: `generate_message` 호출 제거** (`run.py:354` 삭제, `encode`에 batch를 직접 넘김) | fixed_error ○, rber ○, **strong_error ✗** | 프레임당 0.046 ms 절약(전체의 0.03%) | **✗** 실물 인코더가 들어오면 `generate_message`를 되살려야 하고 그 순간 문제가 그대로 재발 | **처방 수정 필요** |
| **(ㄴ) 메시지용/잡음용 generator 분리** (포인트마다 generator 2개를 파생, 채널에는 잡음용만 전달) | fixed_error ○, rber ○, **strong_error ✗** | 추가 비용 사실상 0 (generator 1개 더 생성) | **○** 메시지 스트림 소비가 잡음 스트림을 밀지 않는다. `integers(0,2,(B,K),uint8)` 자체도 배치 분해 가능이라 msg 내용도 배치 무관 | **처방 유효(범위 한정)** |
| **(ㄱ) P2: 프레임 단위 스트림 파생** (포인트 generator에서 프레임마다 자식 generator를 뽑아 프레임 1개씩 생성 후 배치로 쌓음) | fixed_error ○, rber ○, **strong_error ○** | 128프레임 생성 57.16 ms 대 배치 1회 57.62 ms로 **1.0배**. `spawn(128)`은 1.95 ms. 복호가 프레임당 143 ms이므로 무시 가능 | **○** | **처방 유효** |

보조 사실:

- ㉮ `numpy.random.Generator.spawn`은 증분 호출이 안전하다. 같은 부모에서 `spawn(64)`를 두 번 부른 결과가 `spawn(128)` 한 번과 같다(실측 확인). 곧 배치 크기와 무관한 프레임 스트림을 배치 루프 안에서 그대로 만들 수 있다
- ㉯ 세 대안 모두 **기존 실행 기록과의 비트 단위 재현성을 끊는다**(E9). 끊는 것 자체는 불가피하며, 끊는 시점을 한 번으로 모으는 것이 이득이다

### 4-2. 판정

- **P1 (`generate_message` 호출 제거): 처방 수정 필요**
  - 사유 ㉮: 문제의 근본은 "쓸모없는 소비"가 아니라 "메시지 스트림과 잡음 스트림이 한 generator를 공유한다"는 점이다. 호출을 지우면 증상은 사라지지만, 실물 인코더가 들어오는 순간 같은 결함이 되살아난다. 그 사이에 쌓인 실험 기록은 다시 한 번 무효가 된다
  - 사유 ㉯: strong_error는 이 처방으로 해결되지 않는다(E4)
  - 대안: (ㄴ) 또는 (ㄱ)

- **P2 (프레임 단위 스트림 파생): 처방 유효**
  - 채널 3종 전부에서 배치 무관이 성립하는 유일한 안이고, 비용이 실측상 배치 호출과 같다
  - 실물 인코더 도입 후에도 계약이 유지된다
  - 구현 시 `_make_channel_fn`의 `channel_fn(batch, random_generator)` 계약을 "프레임 인덱스 구간을 받아 프레임별 독립 스트림으로 생성"으로 바꿔야 한다. `sim.py`가 이미 `frames` 카운터를 들고 있으므로 프레임 시작 번호를 넘기면 된다

- **"잡음 전용 generator 분리"(더 싼 대안): 처방 유효, 단 H5의 "같은 효과" 주장은 반박됨**
  - fixed_error와 rber만 쓰는 동안에는 P2와 결과가 같고 비용이 0이다
  - strong_error(2SD 디코딩 개방 시)에서는 성립하지 않는다. 2SD를 열 때 함께 P2로 올리거나, `strong_error_channel` 내부의 난수 소비를 `random((B, N))` 한 번으로 합쳐 분해 가능하게 고쳐야 한다

- **추가 처방(Round 2 목록에 없던 항목): 종료 규칙**
  - H3가 반박되었으므로 난수 처방만으로는 "결과에 영향 없음"을 회복할 수 없다
  - 선택지 ㉮: `sim.py`의 종료 검사를 프레임 단위로 내린다(마지막 배치에서 임계 도달 프레임 이후를 잘라 집계). 정확하지만 집계 코드가 늘어난다
  - 선택지 ㉯: 종료 규칙을 그대로 두고 문서 문언을 정확히 고친다. 예를 들어 "프레임별 채널 실현값은 `frames_per_batch`와 무관하다. 측정 종료는 배치 경계에서 판정하므로 총 프레임 수는 `frames_per_batch`의 배수로 반올림된다"
  - 이 선택은 **Decision 등급**(설계 선택)이라 사용자 확인이 필요하다

- **문서 수정 대상(E3)**: `LDPC_base/run.py:32-33`, `2_LDPC_light/config.json:44`, `2_LDPC_light/README.md:79-80`의 3곳. `Ideas/vanilla/config.json`은 해당 서술이 없어 대상 아님

- **연쇄 발견(E8, 문서 오류)**: `LDPC_base/encoder.py:5-6`의 "이 함수 내용만 채우면 되고 다른 곳은 손댈 필요가 없다"는 거짓이다. genie 판정이 정답을 all-zero로 고정하고(`decoder.py:284`) 디코더가 cw를 받지 않으므로(`decoder.py:354`), 실물 인코더 도입은 `decoder_main` 시그니처와 에러 집계, `sim.py`의 post_fec_ber 집계까지 파급된다. B-1의 처방을 고를 때 "실물 인코더 도입 시나리오"의 비용 산정에 이 사실을 반영해야 한다

---

## 5. 저장소 오염 확인

`git status --short` 결과가 세션 시작 기준선과 정확히 일치한다.

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

추가 확인:

- ㉮ `2_LDPC_light/Input/LLR/` 파일 3개로 변동 없음(생성 LLR matrix는 scratchpad의 `LLR/`에만 떨어짐. config의 `decoder.llr_matrix.dir`을 scratchpad 절대경로로 지정해 `run.py:206-215`의 생성 경로를 돌렸다)
- ㉯ `2_LDPC_light/Sim_Output/` 16개 항목, `Ideas/vanilla/Sim_Output/` 6개 항목으로 변동 없음(실험 출력은 전부 scratchpad `out/`)
- ㉰ 저장소 파일 수정 0건. 검증용 스크립트·config·산출물은 전부 `…\96aaaa04-61b8-4b90-ac92-52ca7348de60\scratchpad\`에 있다
  (`e4_channel_decomposability.py`, `e10_alternatives.py`, `runner.py`, `make_configs.py`, `make_h3_configs.py`, `compare.py`, `cfg_*.json`, `out/`, `logs/`, `LLR/`)
