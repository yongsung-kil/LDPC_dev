# Round 3 검증 워커 b_2 결과

대상: C1-F1 (`_column_order` 재정의 시 성공 오판정, MEDIUM), C2-3 (matplotlib 부재 시 summary.txt 유실, 등급 재판정)
작성 시각: 2026-08-08 15:27:16
검증자: 워커 b_2 (Round 2 실측을 참조하지 않고 스크립트를 새로 작성해 독립 재확인)

## 0. 실험 조건

Round 2가 쓴 파일 매트릭스 config는 FER=1.0을 내므로(TD-1) 수치 보존 판정에 쓸 수 없다.
그래서 내부 균일 양자화 경로를 썼다.

| 항목 | 값 |
|------|-----|
| H-matrix | `Input/H_matrix/example_18x147_z256.qc` (N_b=147, M_b=18, z=256, N=37632, E=553) |
| LLR matrix | 내부 균일 합성 (num_bits=6, channel_llr=8, max_iter=30, mode=HD) |
| 채널 | fixed_error, seed 0 |
| 동작점 | point=300 (FER 0.000, avg_iter 7.47), point=360 (FER 0.367) |
| 프레임 | 128 (frames_per_batch=64), `max_frame_errors`를 1e9로 두어 전 판본이 같은 프레임을 처리 |
| 실행 산출물 | 전부 scratchpad (`.../scratchpad/wb2/`) |

스크립트: `c1f1_variants.py`(디코더 변형), `e2_e3_e4.py`, `e5_e7.py`, `e5b_detail.py`,
`block_mpl_run.py`, `e10_e13_e14.py`. 모두 scratchpad에만 있다.

---

## 1. 가설별 판정

| 가설 | 판정 | 요지 |
|------|------|------|
| H1 (미방문 column 에러가 미집계되어 성공 확정) | **확인됨** | 빈 스케줄에서 전 64프레임이 iteration 1에 `success=True`, `final_err_bits=0`. 마지막 column 하나를 건너뛰면 59프레임 성공 보고 중 49프레임에 실제 에러 잔존 |
| H2 (중복 방문 시 `err_bits` 이중 계상) | **확인됨** | 같은 스케줄에서 집계 방식만 바꿔 비교하면 iteration 1 합이 300067 대 299663으로 404 bit 부풀려짐 |
| H3 (에러 집계를 루프 밖으로 옮기면 H1이 해소되고 본체 수치가 보존됨) | **반박됨** | 두 해석 중 어느 쪽도 두 조건을 함께 만족하지 못한다. (가)는 수치를 보존하나 H1을 못 고치고, (나)는 H1을 고치나 본체 수치를 바꾸고 미방문 column의 에러 수를 지어낸다 |
| H4 (matplotlib 부재 시 summary.txt 유실 + 비정상 종료) | **확인됨** | exit code 1, run 디렉터리에 config 사본과 CSV 4종만 남고 summary.txt 없음. traceback이 matplotlib을 지목 |
| H5 (등급) | **HIGH 제안** | 3절 참조 |
| H6 (처방 A: 그림을 summary 뒤로) | **부분 확인** | summary.txt는 보존되나 프로세스는 여전히 exit 1 |
| H7 (처방 B: try/except) | **확인됨** | summary.txt 보존, exit code 0, 실패 사유 콘솔 출력 |

추가로 확인한 사실: **C++ 원본은 판정 비트를 지속 배열 `cwc[]`에 쌓고 에러 검사는 그 배열의
전 범위 스윕으로 따로 한다.** 즉 대안 처방 (ㄴ)은 원본에서 벗어나는 대안이 아니라 원본 구조 그 자체다.

---

## 2. 증거표

### 과제 1: C1-F1

| ID | 판정 | 코드 근거 (파일:라인) | 실측 |
|----|------|----------------------|------|
| E1 | **확인됨** | column 루프 `LDPC_base/decoder.py:258-259`. 집계 `:283-288` (`flip=self._vn_decide(sum_t)` 283, `bit_err=read_bit^flip` 284, `frame_err\|=` 285, `err_bits+=` 286, `err_by_dv+=` 288). 성공 확정 `_check_errors` `:317-332` (`ok=~state.frame_err` 320, `success[...]=True` 322). `final_err_bits` 기록 `:310`. 교체 지점 표의 커버 주장 `:53`, `_column_order` 정의 `:126-128`. 매 iteration 집계 버퍼 초기화 `:242-244` | 집계 3줄이 전부 `_process_column` 안에 있고 `_check_errors`는 `frame_err`만 본다 |
| E2 | **확인됨** | `_column_order`가 `range(0)`을 반환하는 서브클래스 | 프레임당 실제 에러 300 bit인데 **64/64 전부 `success=True`**, `decode_success_iteration`이 전부 1, `final_err_bits` 합 0. post-FEC BER 보고값 0.000e+00 대 실제 7.972e-03 |
| E3 | **확인됨** | `_column_order = range(N_b-1)` (col 146 미방문) | 성공 59/64. 미방문 column에 실제 에러가 남은 프레임 54개 중 **49개가 성공으로 보고**. 성공 보고 프레임의 `final_err_bits`는 전부 0 (`np.unique` 결과 `[0]`). 미집계된 실제 에러 합 107 bit |
| E4 | **확인됨** | `_column_order = range(N_b) + [0]` | 이중 계상 확인 (E4b). 같은 중복 스케줄에서 집계 방식만 바꾸면 iteration 1 err_bits 합이 300067(본체 집계) 대 299663(판정비트 배열 집계), `final_err_bits` 합이 27331 대 25924. 차이가 곧 col 0의 중복 계상분. 덧붙여 중복 방문은 `_cnu_update`의 remove-old를 두 번 태워 복호 자체도 무너진다 (성공 0/64, 본체 스케줄은 64/64) |
| E5 | **처방 반박** | 아래 상세표 | |
| E6 | **확인됨** | C++ `0_LDPC_original/decoder.cpp` | 판정은 column 루프 **안**(`VN_Cal_HD` `:4044-4045`가 `cwc[bit_pos]`에 기록), 에러 검사는 루프 **밖**의 전 배열 스윕(`Check_Genie_CRC` `:4939-4949`, `Get_Err_Cnt` `:5369-5411`, `Count_Error_Bit` `:7274-7285`). `cwc`는 프레임 내내 유지되는 배열이며 초기값은 read bit(`VN_Cal_Pre` `:3735-3751`). column 단위 에러 세기도 `cwc` 배열을 읽는다(`Count_Error_Bit_Column` `:7255-7267`). `Get_Err_Cnt` 호출은 복호 종료 후 1회 `:2001` |
| E7 | **아래 상세표** | | |

#### E5, E7 상세: 판본별 본체 수치 보존과 H1 해소

본체 스케줄(전 column 1회 방문)에서의 수치 (128 프레임, seed 0):

| 판본 | point=300 avg_iter | point=300 iter_hist | point=360 FER | point=360 BER | point=360 avg_iter | 본체와 동일? |
|------|--------------------|---------------------|---------------|---------------|--------------------|-------------|
| 본체 (`MinSumDecoder`) | 7.4688 | [6]=5 [7]=66 [8]=49 [9]=8 | 3.6719e-01 | 3.4935e-03 | 18.4321 | 기준 |
| (가) 루프뒤 flip 합산 | 7.4688 | 동일 | 3.6719e-01 | 3.4935e-03 | 18.4321 | **완전 동일** |
| (나) 루프뒤 재계산 | **7.1641** | **[6]=15 [7]=79 [8]=32 [9]=2** | 3.6719e-01 | **3.5843e-03** | **18.0988** | **다름** |
| (ㄴ) 판정비트 배열 | 7.4688 | 동일 | 3.6719e-01 | 3.4935e-03 | 18.4321 | **완전 동일** |
| (ㄱ) 순열 assert | 7.4688 | 동일 | 3.6719e-01 | 3.4935e-03 | 18.4321 | **완전 동일** |

동일 여부는 FER, post_fec_ber, avg_decode_success_iteration, iter_hist, iteration별 bit_err 합,
iteration별 csw 합을 전부 비교한 결과다. (ㄴ)은 프레임 단위 배열까지 대조했고
`success`, `decode_success_iteration`, `final_err_bits`, `log_active`, `log_csw_sum`,
`log_err_sum`, `log_err_by_dv_sum`, `final_csw`, `final_err_by_dv` 9종이 전부 일치했다.

(나)가 본체와 달라지는 이유는 과제 지시가 예상한 대로다. `_cnu_update`(`decoder.py:165-186`)가
column 루프 도중 `min1`, `min2`, `check_sum`, `edge_sgn`을 in-place로 갱신하므로,
iteration 말단에서 다시 계산한 `sum_t`는 방문 시점의 `sum_t`와 다르다. 차이의 크기는
point=300에서 수렴 iteration 평균 7.4688 대 7.1641 (4.1% 빠름), point=360에서
post_fec_ber 3.4935e-03 대 3.5843e-03 (2.6% 나쁨)이다. FER 자체는 이 두 점에서 우연히 같았다.

미방문 column이 있는 스케줄(col 146 건너뜀)에서의 H1 해소:

| 판본 | success | 미방문 column에 실제 에러가 남았는데 성공 보고 |
|------|---------|--------------------------------------------|
| 본체 | 59/64 | 49 |
| (가) | 59/64 | 49 |
| (나) | 60/64 | 50 (성격이 다름, 아래 설명) |
| (ㄴ) | 10/64 | **0** |
| (ㄱ) | 실행 거부 (`ValueError: _column_order 미방문 column 존재`) | 해당 없음 |

(나)의 50건은 단순 오판정이 아니다. (나)는 iteration 말단에 **전 column의 판정을 새로 만들어**
집계하므로, 미방문 column도 신드롬 기반으로 판정을 받는다. 즉 (나)는 회계를 고치는 대신
디코더를 바꾼다. 이 성격은 빈 스케줄에서 뚜렷하다.

| 빈 `_column_order` | success | `final_err_bits` 합 |
|---------------------|---------|--------------------|
| (나) 루프뒤 재계산 | 0/64 | **64405** (실제 채널 에러는 19200) |
| (ㄴ) 판정비트 배열 | 0/64 | **19200** (실제와 정확히 일치) |

메시지 전달을 한 번도 하지 않은 스케줄에서 (나)는 실제보다 3.4배 큰 에러 수를 지어내고,
(ㄴ)은 채널 에러 수를 정확히 보고한다.

비용 (64 프레임 1배치, point=300, 3회 중 최솟값):

| 판본 | 시간 | 본체 대비 |
|------|------|----------|
| 본체 | 3.606s | 기준 |
| (가) | 3.679s | +2.0% |
| (나) | 3.886s | **+7.8%** |
| (ㄴ) | 3.603s | -0.1% (측정 잡음 범위) |
| (ㄱ) | 3.649s | +1.2% |

(가)와 (ㄴ)의 오버헤드는 대부분 검증용 뼈대(`_run_iteration`, `_process_column`을 파이썬으로
다시 쓴 것)에서 온다. 본체에 통합하면 (ㄴ)의 추가 비용은 배열 쓰기 한 줄과 루프 뒤 합산뿐이다.

(ㄴ)의 메모리 비용 (B=64):

| 배열 | 크기 |
|------|------|
| 추가되는 `decision_bit` (B, N_b, z) uint8 | 2.41 MB |
| 기존 `read_bit` (같은 shape, dtype) | 2.41 MB |
| 기존 `edge_sgn` (B, E, z) uint8 | 9.06 MB |
| 기존 `min1` (B, M_b, z) float32 | 1.18 MB |

기존 `edge_sgn`의 27% 수준이며 프레임 배치 크기에 선형으로 늘어난다.

(ㄱ)의 해결 범위와 비용: 계약 위반을 실행 시점에 즉시 잡아내고 비용은 +1.2%다.
다만 informed dynamic scheduling처럼 일부 column만 방문하는 아이디어를 아예 막으므로,
교체 지점 표(`decoder.py:53`)가 그 유형을 커버한다는 주장을 지키지 못한다.
표에서 그 유형을 내리는 문서 수정이 함께 필요하다.

### 과제 2: C2-3

| ID | 판정 | 코드 근거 (파일:라인) | 실측 |
|----|------|----------------------|------|
| E8 | **확인됨** | `report()` `LDPC_base/run.py:517-568`. 순서는 run 디렉터리 생성 `:526`, config 사본 `:527`, CSV와 로그 `:534-560`, **그림 저장 `:561-564`**, **summary.txt 쓰기 `:565-566`**, `run dir:` 출력 `:567`, `return results` `:568`. `_plot_fer_curves` 안에서 `import matplotlib` `:496` | 그림 저장이 summary 쓰기보다 두 줄 앞이라 ImportError가 summary를 건너뛴다 |
| E9 | **확인됨** | `sys.meta_path`에 matplotlib만 ImportError로 막는 finder를 꽂고 `LDPC_base.run.main()` 호출 | 측정 완주 후 **exit code 1**. run 디렉터리에 남은 파일: `config.json`, `fer_fixed_error.csv`, `log_fail_fixed_error_p300.csv`, `log_iter_fixed_error_p300.csv`, `log_iter_hist_fixed_error_p300.csv` (5개). **summary.txt 없음**. traceback 마지막 프레임이 `run.py:496 import matplotlib`, 메시지가 `ImportError: No module named 'matplotlib'`이라 원인 지목은 명확 |
| E10 | **확인됨** | `report()` `run.py:530-531`, `_experiment_summary_lines` `:310-330`, config 사본은 원본 파일 그대로 복사 `:527`, `save_csv` 열 구성 `sim.py:104-117` | 아래 손실 범위 표 |
| E11 | **확인됨** | 의존성 선언 파일 없음(`git ls-files`로 requirements, pyproject, setup.py, setup.cfg, environment.yml, Pipfile 전무). README에 설치 안내 없음(`pip install` 문자열 0건). `2_LDPC_light/config.json:80`과 `Ideas/vanilla/config.json:44` 둘 다 `"fer_curve_png": true`. 코드 기본값은 `run.py:561`의 `log_config.get("fer_curve_png")`라 키가 없으면 그림 저장을 건너뛴다 | 새 환경의 첫 실행이 두 config 어느 쪽으로도 이 경로를 탄다 |
| E12 | **확인됨** | 난수 파생 `run.py:398` `np.random.default_rng([seed, channel_index, int(1e6*point)])` | 같은 config를 두 번 실행해 fer CSV를 대조하면 `sec`(벽시계)만 다르고 param, fer, post_fec_ber, frames, errors, avg_decode_success_iteration이 전부 동일. 재실행 비용은 저장소 기본 config 기준 8.3초(기존 산출물 summary의 4.1s + 4.2s), 이번 검증용 config 기준 3.6초 |
| E13 | **확인됨** | `_plot_fer_curves` `run.py:494-514`는 `r["param"]`, `r["fer"]`, `r["errors"]`, `r["frames"]`만 읽는다 | 호출 전후로 `results`를 deepcopy 대조해 불변 확인. `report()` 반환값은 `results` 그대로(`:568`)라 순서를 바꿔도 영향 없음. 콘솔 순서는 `saved: {png}`가 `run dir:` 앞에 오는 것만 유지하면 되고, summary.txt 쓰기는 출력이 없다. **순서를 바꿔도 그림 저장이 실패하면 프로세스는 여전히 exit 1** (실측: summary.txt와 CSV는 남고 예외는 그대로 전파) |
| E14 | **확인됨** | `_plot_fer_curves` 안에서 import와 `fig.savefig` `:513`이 같은 함수에 있음 | `try/except Exception`으로 감싸 실측하면 summary.txt 보존, **exit code 0**, 콘솔에 `FER 커브 그림 저장 실패 (측정 결과는 저장됨): ImportError: No module named 'matplotlib'` 출력 |

#### E10 손실 범위 정량화

summary.txt 한 파일에만 있는 정보와 복구 가능성:

| 항목 | 다른 산출물에 있는가 | 재실행 없이 복구 가능한가 |
|------|---------------------|------------------------|
| run 스탬프와 라벨 | run 디렉터리 이름 | 가능 |
| **git 커밋 해시** (`run.py:530`) | 없음 | **불가**. 실행 시각으로 git log를 추정하는 방법뿐 |
| 부호 요약 (`code.summary()`, N, K, rate, degree 분포) | 없음 | 조건부 가능. config 사본이 가리키는 H-matrix 파일이 그대로 있으면 다시 뽑을 수 있다 |
| LLR matrix 요약 (`llr_matrix.summary()`, mode, dv 구간, max_iter, group) | 없음 | 조건부 가능. 같은 조건 |
| **실제로 쓰인 디코더 클래스 전체 경로** (`run.py:321-323`) | 없음. config 사본에는 `"type": "vanilla"`만 있다 | **불가** |
| 실효 run 설정 (기본값이 채워진 값) | config 사본에는 원본 파일에 적힌 키만 있다 | 조건부 가능. 코드의 기본값을 읽어 유추 |
| 포인트별 FER/BER 줄 | `fer_*.csv`에 param, fer, post_fec_ber, frames, errors, avg_decode_success_iteration, sec 전부 있음 | 가능 |

디코더 클래스 항목을 실측으로 확인했다. `Ideas` 임포트를 막고 `decoder.type="vanilla"`로 실행하면
`_resolve_decoder_class`(`run.py:266-269`)가 조용히 `MinSumDecoder`로 대체하고, summary.txt만
`decoder: vanilla (LDPC_base.decoder.MinSumDecoder)`로 바뀐다 (정상 경로는
`decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder)`). config 사본과 CSV 어디에도 이 구분이 없다.
즉 C2-1이 발동한 실행에서 summary.txt를 잃으면 **어떤 디코더가 돌았는지 사후에 알 방법이 없다.**

---

## 3. C2-3 등급 판정 제안

**제안 등급: HIGH**

심각도 정의는 CRITICAL(프로세스 중단 또는 비가역 손상), HIGH(틀린 결과를 내지만 진행),
MEDIUM(엣지케이스 위험)이다. 이 발견은 세 정의 어디에도 그대로 들어맞지 않으므로
정의 문구를 하나씩 대조해 판정한다.

- ㉮ CRITICAL의 "프로세스 중단"은 문자 그대로 성립한다 (exit code 1로 죽는다). 그러나
  중단 시점이 측정 완주 이후이고, summary.txt를 뺀 산출물 전부가 이미 디스크에 있다.
  CRITICAL의 다른 축인 "비가역 손상"은 성립하지 않는다. 난수 스트림이 seed에서 결정되어
  같은 config의 재실행이 같은 수치를 낸다는 것을 실측으로 확인했고(E12), 재실행 비용은
  저장소 기본 config에서 8.3초다. 두 축 중 하나만 걸리고 그 하나도 "일을 못 끝냄"이 아니라
  "다 끝내고 마지막 한 줄에서 죽음"이므로 CRITICAL로 올리지 않는다.
- ㉯ MEDIUM의 "엣지케이스 위험"은 성립하지 않는다. 저장소에 의존성 선언 파일이 하나도 없고
  README에 설치 안내가 없으며 두 config 모두 `fer_curve_png: true`다 (E11). 즉 새 환경에서
  저장소를 가져와 안내대로 실행하면 **기본 경로가 곧 이 경로**다. 이 저장소의 목적이
  "외부에서 pull하여 성능을 확인"(루트 CLAUDE.md 프로젝트 간 흐름 ㉰)이므로 발동 확률은 높다.
- ㉰ HIGH의 "틀린 결과를 내지만 진행"과는 결과의 성격이 다르다. 다만 손실의 무게는 HIGH급이다.
  잃는 것이 재현성 기록 전체이고, 그중 git 커밋 해시와 **실제로 쓰인 디코더 클래스**는
  재실행 없이는 복구할 수 없다 (E10). 특히 후자는 C2-1(임포트 실패 시 조용한 `MinSumDecoder`
  대체)이 발동한 실행에서 유일한 흔적이다. 아이디어 디코더를 돌린 줄 알았던 실행이
  실은 정본이었다는 사실이 summary.txt와 함께 사라진다.

**결론**: 발동 확률이 기본 경로 수준이고 손실 항목 중 둘이 재실행 없이 복구 불가라 MEDIUM은
과소평가다. 손상이 가역이고 실패가 조용하지 않아(traceback이 matplotlib을 지목) CRITICAL은
과대평가다. **HIGH**로 두고, Round 2 팀 C의 "수리 우선순위 1위" 판단은 유지한다.

---

## 4. 처방 판정

### C1-F1

| 처방 | 판정 | 사유 |
|------|------|------|
| Round 2 원처방 "에러 집계를 column 루프 밖으로" 해석 (가): 루프 안 `flip`을 저장해 뒀다가 루프 뒤 합산 | **처방 반대** | 본체 수치는 완전 보존되나 **H1이 그대로 남는다** (건너뛴 스케줄에서 성공 오판정 49건 동일). 방문한 column만 저장하므로 문제의 원인인 "방문 스케줄 종속"이 바뀌지 않는다 |
| 해석 (나): 루프 뒤 전 column의 `sum_t`와 `flip`을 다시 계산해 집계 | **처방 반대** | 두 가지 이유다. ㉮ 본체 수치가 바뀐다 (point=300 avg_iter 7.4688 → 7.1641, iter_hist 분포 이동, point=360 BER 3.4935e-03 → 3.5843e-03) ㉯ 회계를 고치는 대신 디코더를 바꾼다. 미방문 column에 신드롬 기반 판정을 새로 만들어 집계하므로, 빈 스케줄에서도 실제 에러 19200 대신 64405를 보고한다. 스케줄 아이디어의 실제 동작을 감추는 쪽으로 틀린다. 비용도 +7.8% |
| 대안 (ㄱ): `_column_order`가 `range(N_b)`의 순열인지 assert | **처방 유효 (부분)** | 본체 수치 완전 보존, 비용 +1.2%, 계약 위반을 즉시 잡아낸다. 다만 일부 column만 방문하는 스케줄을 아예 막으므로, 교체 지점 표(`decoder.py:53`)에서 informed dynamic scheduling 항목을 내리는 문서 수정이 함께 가야 한다. 단독으로 쓰면 C1-F1의 "표의 커버 주장이 과하다"는 지적을 코드가 아니라 문서 쪽에서 인정하는 결말이 된다 |
| 대안 (ㄴ): 판정 비트를 `(B, N_b, z)` 배열에 보관(초기값 `read_bit`)하고 루프 뒤 집계 | **처방 유효 (권장)** | ㉮ 본체 스케줄에서 프레임 단위 배열 9종이 전부 일치 (완전 보존) ㉯ H1 해소 (건너뛴 스케줄 오판정 0건, 빈 스케줄에서 실제 채널 에러 19200을 정확히 보고) ㉰ 비용 -0.1% (측정 잡음 범위) ㉱ 메모리 +2.41 MB(B=64), 기존 `edge_sgn`의 27% ㉲ **C++ 원본과 같은 구조다.** 원본도 판정을 지속 배열 `cwc[]`에 쌓고(`decoder.cpp:4044-4045`, 초기값은 `:3735-3751`) 에러 검사는 전 배열 스윕으로 따로 한다(`:4939-4949`, `:5369-5411`). 원본 동작 재현이라는 목적과 충돌하지 않고 오히려 가까워진다 |

권장 조합: (ㄴ)을 본체에 넣는다. (ㄱ)은 "전 column 방문" 계약을 유지하고 싶을 때만 추가하되,
(ㄴ)이 들어가면 부분 방문 스케줄도 정직한 수치를 내므로 (ㄱ)의 필요가 줄어든다.
중복 방문(H2)은 (ㄴ)이 자동으로 해소한다 (배열의 마지막 쓰기만 남으므로 이중 계상이 사라진다).

### C2-3

| 처방 | 판정 | 사유 |
|------|------|------|
| A: 그림 저장을 summary.txt 쓰기 뒤로 이동 | **처방 유효 (단독으로는 불충분)** | summary.txt가 보존된다 (실측: `config.json`, `fer_*.csv`, `summary.txt` 남음). 부작용 없음 (`_plot_fer_curves`가 `results`를 변형하지 않음을 deepcopy 대조로 확인, `report()` 반환값도 그대로). 콘솔 순서는 `saved: {png}`를 `run dir:` 앞에 두면 유지된다. 그러나 **그림 저장이 실패하면 프로세스는 여전히 exit 1**이라 자동화 파이프라인은 여전히 실패로 본다 |
| B: `try/except`로 감싸기 | **처방 유효** | summary.txt 보존, exit code 0, 실패 사유 출력. 잡을 범위는 `ImportError`만으로는 부족하다. matplotlib이 있어도 `fig.savefig`(`run.py:513`)가 경로나 권한 문제로 실패할 수 있으므로 `except Exception`으로 잡고 `type(exc).__name__: exc`를 포함한 메시지를 찍어 침묵을 막는다. exit code 0은 타당하다. 측정은 완주했고 산출물이 전부 저장됐으며 실패한 것은 선택 항목인 그림 하나이기 때문이다 |
| A + B 병용 | **가능하며 권장** | 서로 배타적이지 않다. A가 "summary는 어떤 경우에도 먼저 남는다"를 보장하고, B가 "그림 실패로 실행 전체가 실패로 기록되지 않는다"를 보장한다. B만 쓰면 그림 저장 실패가 아닌 다른 예외(예: 로그 CSV 쓰기 실패)가 여전히 summary를 날리므로 A의 순서 교체가 방어선으로 남는다 |

부수 권고 (등급 판정과 별개): 의존성 선언 파일이 없다는 사실 자체가 C2-3의 발동 확률을
결정한다 (E11). 처방 A와 B는 손실을 막을 뿐 원인을 없애지 않으므로, `requirements.txt` 또는
README 설치 안내를 함께 두는 편이 낫다.

---

## 5. 저장소 오염 확인

작업 종료 시점 `git status --short`:

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

세션 시작 기준선과 동일하다. 확인 사항:

- ㉮ 실행 산출물(run 디렉터리 8개)은 전부 scratchpad 하위에 생성했다 (`out`, `out_mpl`, `out_rx`, `out_det`)
- ㉯ 내부 균일 LLR matrix 생성 파일도 scratchpad(`.../wb2/LLR/`)로 돌려, 추적 디렉터리 `Input/LLR/`은 변하지 않았다
- ㉰ 디코더 변형 클래스는 전부 scratchpad의 `c1f1_variants.py`에 서브클래스로 두었고, `LDPC_base/`와 `Ideas/`는 읽기만 했다
- ㉱ C++는 `0_LDPC_original/decoder.cpp`를 읽기만 했고 빌드하지 않았다
- ㉲ 이 보고서는 미추적 디렉터리 `_pm/tasks/` 하위에 쓰므로 기준선을 바꾸지 않는다
