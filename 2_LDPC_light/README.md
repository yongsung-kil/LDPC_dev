# 2_LDPC_light: 논문 아이디어 스크리닝용 경량 QC-LDPC 시뮬레이터

> 확정 결정 기록: 아래 "확정 결정 기록" 절, original과의 로직 차이: [docs/차이.md](docs/차이.md)
> **주의**: py는 아이디어 상대 비교(on/off) 전용이라 C++ Ref-C와의 절대 FER 일치는 보장하지 않는다.
> 유효 아이디어의 최종 검증은 실물 C++(실제 형태)에 이식하여 수행한다 (확정 결정 기록 참조).
> 2026-08-07: `_test/20260806_setup_구성_실험/`의 개정본을 본체로 반영 (구 코드는 git 이력에 보존)

## 구성

| 경로 | 내용 |
|------|------|
| `LDPC_base/` | 코드: pcm, encoder, channel(원본 대응 3종), decoder(syndrome-aided + 논문 교체 지점), sim, run, llr_matrix |
| `Ideas/` | 논문 아이디어 폴더 (아래 "논문 아이디어 구조" 절). vanilla = reference |
| `Input/H_matrix/` | H-matrix(.qc) 파일 보관. **Ref-C 헤더 전용** (N_b M_b / J K / z / 빈 줄 / 행렬). column block은 **DV 내림차순 배치** |
| `Input/LLR/` | LLR 파일 보관. **DAO LLR_MATRIX 형식만 사용** (LLR_MATRIX_HD_0.txt=restart 포함 토이, HD_1.txt=restart 없는 20-iter 테스트용) |
| `Sim_Output/` | 실험 결과 출력 (git 무시, 실행마다 타임스탬프 폴더 생성) |
| `config.json` | 실험 설정 (아래 스키마 참조) |
| `tools/H_mat_gen/` | H-matrix 설계 툴 모음 (peg, lifting, gen_example_code, select_irregular). 실험 흐름과 분리된 수동 도구 |
| `docs/` | 차이.md(original 대비 로직 차이), review/(리뷰 기록) |

## 실행 방법

의존 패키지 설치 (최초 1회):

```bat
pip install -r requirements.txt
```

이 폴더(`2_LDPC_light/`)에서:

```bat
python -m LDPC_base.run config.json
python -m LDPC_base.run Ideas/vanilla/config.json   :: vanilla reference 실험
```

JSON의 상대경로(H_matrix, decoder.llr_matrix, output.dir)는 그 JSON 파일 위치 기준으로
해석된다. 새 실험 설정은 config.json을 복사해서 만든다.

H-matrix 생성 (repo 루트에서, 실험 흐름과 분리된 수동 도구):

```bat
python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code [출력경로]
```

시뮬 실행은 `2_LDPC_light/`, 도구 실행은 repo 루트가 기준 폴더다. 한 파이썬
프로세스에서 두 기준을 섞으면 같은 모듈이 두 벌 적재될 수 있으므로 섞지 않는다.

## 용어

| 약어 | 원어와 뜻 |
|------|-----------|
| LDPC | low-density parity-check code (저밀도 패리티 검사 부호) |
| QC | quasi-cyclic (순환 시프트 블록 구조) |
| LLR | log-likelihood ratio (로그 우도비, 비트 신뢰도) |
| VNU / CNU | variable / check node unit (변수 노드 / 검사 노드 연산부) |
| dv | variable node degree (변수 노드가 연결된 검사식 수, column degree) |
| CSW | check-sum weight (불만족 검사식 수) |
| FER / BER | frame / bit error rate (프레임 / 비트 에러율) |
| HD / 2SD / 3SD | hard decision / 2-bit, 3-bit soft decision 채널 양자화 |
| DAO | decoder auto optimizer (LLR 테이블 최적화 외부 도구) |

## JSON 설정 스키마 (2026-08-07 확정)

```json
{
  "H_matrix": { "dir": "Input/H_matrix", "file": "....qc" },
  "decoder": { "type": "vanilla",
               "use_input_llr_matrix": true,
               "llr_matrix": { "dir": "Input/LLR", "file": "LLR_MATRIX_HD_x.txt" },
               "internal_quantize": { "num_bits": 6, "channel_llr": 8,
                                      "max_iter": 120, "mode": "HD" } },
  "seed": 0,
  "run": { "max_frame_errors": 10, "max_frames": 256, "frames_per_batch": 64,
           "stop_below_fer": null },
  "channels": [
    { "type": "fixed_error", "points": [200, 300] }
  ],
  "log": { "csw_per_iter": true, "bit_err_per_iter": true, "bit_err_by_dv": true,
           "iter_histogram": true, "fer_vs_iter": true, "fail_frame_detail": true,
           "fer_curve_png": true },
  "output": { "dir": "Sim_Output", "csv_prefix": "fer" }
}
```

- ㉮ `H_matrix`, `decoder.llr_matrix`: **폴더와 파일명 분리** `{"dir", "file"}`.
  `use_input_llr_matrix`가 true(기본)면 llr_matrix 파일이 필수이고 **max_iter는
  파일의 마지막 iter_end가 결정**한다 (JSON에 decoder.max_iter를 쓰면 에러).
  디코딩 모드는 파일명(HD/2SD/3SD)으로 판별.
  false면 **균일 n-bit 양자화 매트릭스를 DAO 포맷 파일로 생성해 저장한 뒤 그
  파일을 로드**해 디코딩한다. `internal_quantize`의 num_bits(메시지 양자화
  bit 수, sign 포함), channel_llr(채널 LLR magnitude, 전 dv 공통), max_iter,
  mode(기본 HD)로 파일을 만들며, llr_matrix 키는 무시된다 (플래그 값만 바꿔
  두 방식을 오갈 수 있다). 생성 파일은 `output.dir` 하위 `_generated/`(git 무시 영역)에 저장된다
  (예: LLR_MATRIX_HD_uniform_6bit_ch8_dv4_iter120.txt).
  파일명의 **uniform은 사람이 만든 파일이 아니라는 표시**이고, 레벨 구성 인식은
  파일명이 아니라 th 값 패턴([n..1]이면 균일)으로 한다
- ㉯ `decoder.type`: 사용할 디코더 (기본 "vanilla", Ideas/registry.py 등록 이름)
- ㉰ `seed`: 실험 전체 난수 seed **하나** (기본 0). 채널과 포인트별 스트림은
  [seed, 채널 인덱스, 포인트]로 파생
- ㉱ `channels`: 채널 **리스트**. 항목 1개만으로도 실행 가능하며 순서대로 전부 실행.
  항목 키: `type`(rber/fixed_error/strong_error), `points`(스칼라 허용),
  strong_error는 `SER`/`SCR` 추가, 선택 키 `label`은 CSV 파일명 접미사
- ㉲ `run.max_frame_errors`: 프레임 에러가 이 수에 도달하면 해당 포인트 측정 종료
- ㉳ `run.frames_per_batch`: 한 번에 동시 복호하는 프레임 수 (속도와 메모리 조절용).
  통계 결과는 프레임 수가 충분하면 같고, 같은 seed의 수치 재현에는 이 값까지 같아야 한다
- ㉴ `run.stop_below_fer`: 측정 FER가 이 값 미만이면 해당 채널의 남은 포인트 측정 중단
  (null=사용 안 함, 다음 채널은 계속 진행)
- ㉵ `run.print_progress`: 진행 상황 콘솔 출력 여부 (기본 true)
- ㉶ `output.save_llr_matrix`: 사용한 LLR matrix 파일 사본을 실행 폴더에 저장할지
  (기본 true). 파일 로드와 균일 생성 어느 경로든 실제 사용된 파일이 남는다
- ㉷ 설정 검증: 키맵(허용 키 밖이면 에러) + 필수값 + 값 제약.
  `_`로 시작하는 키(예: `_desc`)는 **설명용으로 검사에서 무시**. JSON에 주석이 없어
  설명은 `_desc` 키로 단다 (문자열 배열 가능)

## 실행 폴더와 분석 로그

실행마다 `output.dir` 하위에 **`YYMMDD_HHMMSS_{라벨}/`** 폴더가 생기고 결과 일체가
그 안에 저장된다 (라벨 = `output.label`, 없으면 첫 채널 type):

```
Sim_Output/260807_133321_fixed_error/
├── config.json                  ← 실행에 쓴 설정 사본 (재현성)
├── summary.txt                  ← 요약 + 코드 git 커밋 해시
├── LLR_MATRIX_*.txt             ← 사용한 LLR matrix 사본 (save_llr_matrix 시)
├── fer_{라벨}.csv               ← FER 결과 (post_fec_ber 열 포함, 항상)
├── fer_curves.png               ← FER 커브 (fer_curve_png 시)
├── log_iter_{라벨}_p{포인트}.csv      ← iteration별 CSW/bit error 평균 (dv별 분해 포함)
├── log_iter_hist_{라벨}_p{포인트}.csv ← 수렴 iteration 히스토그램 + fer_vs_iter
└── log_fail_{라벨}_p{포인트}.csv      ← 실패 프레임별 잔여 에러/최종 CSW/dv별 분해
```

- ㉮ 로그 항목별 on/off (`log` 섹션). 켜면 iteration 루프 수집 비용으로 속도가 다소 떨어진다
- ㉯ `post_fec_ber`(복호 후 BER)는 로그와 무관하게 항상 FER CSV에 포함
- ㉰ `fer_vs_iter`: 프레임별 성공 iteration 기록으로 "max_iter를 k로 줄였다면"의 FER를
  한 번의 실행에서 산출
- ㉱ 후순위 로그 7종은 미구현 (`_pm/TODO.md` 참조)

## 논문 아이디어 구조

**교체 단위 = 원본 C++ 함수 경계.** "교체 지점"이란 본체가 특정 단계를 일부러
별도 함수로 분리해 둬서 아이디어 버전이 그 함수만 갈아끼울 수 있게 만든 자리다.
아이디어는 `LDPC_base`를 고치지 않고 `MinSumDecoder`를
상속한 자식 클래스에서 교체용 함수만 재정의한다(재정의 = 부모 클래스의 함수를
자식 클래스에서 다른 내용으로 바꿔 채우는 것). 스크리닝에서 살아남은 아이디어는
교체용 함수의 C++ 대응 함수가 곧 실물 이식 지점이 된다.

| 교체용 함수 | C++ 대응 | 커버 논문 유형 |
|-------------|----------|---------------|
| `_c2v_reconstruct` | C2V_Cal | min-sum 변형 (offset/normalized/adjusted), C2V 보정 |
| `_vnu_quantize` | VN_Cal_HD 양자화부 | 양자화 규칙, 비균일 임계 |
| `_vn_decide` | VN_Cal_HD 판정부 | 판정 규칙 |
| `_cnu_update` | CNU_Remove_Old_Sgn / CNU_Update_New_Mag | CN 상태 갱신 변형 |
| `_column_order` | 메인 루프 스케줄 | layered / informed dynamic scheduling |
| `_is_edge_clear_iter` | Clear_Edge_Restart (Is_Iter_Type_Edge_Clear) | restart, perturbation, post-processing |
| 테이블 row 선택 | Get_Cur_LLR_Idx_FILE | `LLRMatrix.row_index()` (LLRMatrix 자식 클래스로 커버) |

damping과 진동 억제처럼 직전 iteration 값이 필요한 아이디어는 교체용 함수가
이력을 받지 않으므로 `decoder_main` 전체 재정의로 구현한다. 등록 디코더는
생성자를 `(code, llr_matrix=...)` 형태로 유지한다.

```
Ideas/
├── registry.py       ← {"vanilla": "Ideas.vanilla.decoder:VanillaDecoder", ...}
└── vanilla/          ← reference (재정의 없음 = 정본). 새 아이디어의 템플릿
    ├── decoder.py / config.json / README.md
    └── Sim_Output/   ← 이 아이디어의 실험 결과
```

- ㉮ config `decoder.type`으로 디코더 선택 (기본 "vanilla")
- ㉯ on/off 비교는 같은 seed로 vanilla config와 아이디어 config를 각각 실행
- ㉰ 새 아이디어 추가 절차는 `Ideas/vanilla/README.md` 참조

## 채널 모델: original 대응 3종

`LDPC_base/channel.py`. 출력은 original의 HD_input/SD_input/CC_input 대응
dict {"mode", "hd", "sd", "cc"}.

| 채널 | original 대응 | 지원 모드 | points 의미 |
|------|---------------|----------|-------------|
| rber | MODE_CH_RBER. RBER를 역Q함수로 AWGN σ 환산(dev_from_RBER), BPSK+노이즈, HD=부호, 2SD/3SD는 \|2y/σ²\|를 LLR_th=2·r_offset/σ²와 비교 (r_offset: 2SD 0.35 / 3SD 0.15, 0.35, 0.55) | HD, 2SD, 3SD | RBER 값 |
| fixed_error | MODE_CH_FIXED_ERROR. 프레임마다 정확히 E개 무작위 bit flip | HD | E (에러 bit 수) |
| strong_error | MODE_CH_STRONG_ERROR. E 중 round(E·SER)개는 strong(sd=1) 에러이고 나머지는 weak, 정정 bit 중 round(C·SCR)개만 strong이고 나머지는 weak | 2SD | E (에러 bit 수) |

- 2SD/3SD는 채널 출력까지만 준비했고, 디코더가 HD 전용이라 현재 실행 불가 (TODO)
- 난수는 original XOR25 대신 numpy Generator

## DAO LLR_MATRIX: syndrome-aided decoding

`LDPC_base/llr_matrix.py`가 DAO(decoder auto optimizer)의 LLR_MATRIX 텍스트 포맷을
읽고, `LDPC_base/decoder.py`의 `decoder_main()`이 **원본 C++의 flip/magnitude
도메인(syndrome-aided)** 그대로 디코딩한다. 세부 구조와 original 대비 차이는
[docs/차이.md](docs/차이.md)와 `decoder.py` 모듈 설명 참조.

## 남은 근사/제한

- 사람이 만든 LLR matrix 파일은 3-bit(VNU 출력 레벨 {7,5,3,1}) 전용.
  균일 생성물(파일명 uniform)은 n-bit 레벨을 지원한다 (레벨 수는 edge_mag가 결정)
- 2SD/3SD 디코딩 미구현 (채널 출력까지만)
- 파이프라인 store 지연(2~3 col) 미재현 (restart 흔들기 전파가 원본과 다소 다를 수 있음)
- BF(1-bit precision) 구간 미구현 (vanilla, BF off 전제)
- 실물 H-matrix와 LLR_MATRIX 실값 미반입 (토이 예시 사용 중)
- `encoder.encode()`는 실제 인코딩 없이 all-zero 반환하는 임시 함수

## 확정 결정 기록

시뮬레이터의 방향을 정한 사용자 결정이다 (상세 경위는 `_pm/DONE.md`와 git 이력).

| 결정 | 내용 |
|------|------|
| 2단계 하이브리드 (2026-07-29) | Python으로 아이디어 스크리닝(FER 1e-2~1e-4 영역) 후, 유효 아이디어만 실물 C++에 이식해 최종 검증 |
| vanilla 형태는 Python에만 (2026-07-29) | 쇼트닝, 펑처링, HCU, CRC 조기종료를 뺀 vanilla는 py 전용. 아이디어가 유효하면 실제 형태의 C++에 적용해 재비교 |
| 제거 항목 (2026-07-29) | HCU, 쇼트닝/펑처링, CRC 조기종료, timing/SRAM/PMU/TV. GT(Graph Thinning)는 edge 라우팅 테이블일 뿐이라 FER 영향 0을 코드로 확인 후 제거 (2026-07-30) |
| 성공 판정 (2026-07-30) | genie: 매 iteration 결정을 정답과 bitwise 비교, 일치하면 그 프레임 성공 확정 (CRC 조기종료의 이상화 대응, 미스검출 없음) |
| codeword (2026-07-30) | all-zero (인코더 포팅 불필요, 대칭 채널과 대칭 복호기 전제) |
| Dual-Update (2026-07-30) | off (vanilla 취지). 실제 적용 형태와의 격차는 최종 C++ 검증에서 흡수 |
| 시뮬 방침 (2026-07-30) | max_iter=120 기준, numba 미사용 (numpy 프레임 배치만), 병렬화는 mpi4py로 코어당 sim 1개 (mpi_runner는 재설계 예정) |
| 실물 치수 | base M_b=18 × N_b=147, z_sb=256, codeword 37,632 bit, rate≈0.878, 정보 33,024 bit(4KB). 전 파라미터는 H-matrix 파일에서 읽는다 |
| 실물 파라미터 반입 필요 | H-matrix 실물 파일과 LLR 테이블 실값은 저장소에 없다 (LLR 실값은 원본 소스 손상으로 소실, 사용자 공급 필요). 실물 C++ 실행 시 z_sb=256이면 PMU/Clk 경로가 최초로 활성화되는 점 확인 필요 |
