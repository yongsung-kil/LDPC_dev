# 2_LDPC_base: 경량 QC-LDPC 시뮬레이터

> 확정 결정 기록: 아래 "확정 결정 기록" 절, original과의 로직 차이: [docs/차이.md](docs/차이.md)
> **주의**: py는 상대 비교(on/off) 전용이라 C++ Ref-C와의 절대 FER 일치는 보장하지 않는다.
> 2026-08-07: `_test/20260806_setup_구성_실험/`의 개정본을 본체로 반영 (구 코드는 git 이력에 보존)

## 구성

| 경로 | 내용 |
|------|------|
| `src/` | 코드: pcm, encoder, channel(원본 대응 3종), decoder(syndrome-aided + 논문 교체 지점), sim, run, llr_matrix |
| `workspace/` | 실험 공간: 실험마다 폴더 하나, 폴더 안의 run.py로 실행 (아래 "실험 공간 구조" 절). base_run = reference |
| `Input/H_matrix/` | H-matrix(.qc) 파일 보관. **Ref-C 헤더 전용** (N_b M_b / J K / z / 빈 줄 / 행렬). 행렬 뒤 내용은 Ref-C fscanf처럼 무시하므로 행렬이 2벌 든 파일은 첫 벌만 사용. column block은 **DV 내림차순 배치** |
| `Input/LLR/` | LLR 파일 보관. **DAO LLR_MATRIX 형식만 사용** (HD_0=restart 포함 토이, HD_1=restart 없는 20-iter 테스트용, 2SD_toy0/3SD_toy0=2SD/3SD restart 포함 토이) |
| `docs/` | 차이.md(original 대비 로직 차이), review/(리뷰 기록). 논문 적용 절차 정본은 `3_LDPC_ideas/새논문적용규칙.md` |

## 실행 방법

의존 패키지 설치 (최초 1회):

```bat
pip install -r requirements.txt
```

실험은 `workspace/{실험}/` 폴더에서 (어느 위치에서 실행해도 동작):

```bat
python run.py                    :: 형제 config.json 사용 (예: workspace/base_run/)
python run.py 다른설정.json      :: 인자로 다른 config 지정 (복수 가능)
```

config 경로를 직접 주는 `python -m src.run <config 경로>` 실행도 가능하다
(`2_LDPC_base/`에서, 디코더는 BaseDecoder 고정).

JSON의 상대경로(H_matrix, decoder.llr_matrix, output.dir)는 그 JSON 파일 위치 기준으로
해석된다. 새 실험은 `workspace/_template/`를 복사해서 만든다 (config 골자 포함,
스키마 상세는 아래 절).

H-matrix 생성 도구는 `4_H_matrix_tool/` 프로젝트가 담당한다 (실험 흐름과 분리,
`4_H_matrix_tool/README.md` 참조). 실험 실행 흐름은 H-matrix를 생성하지 않고
파일로만 받는다.

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
  "decoder": { "use_input_llr_matrix": true,
               "llr_matrix": { "dir": "Input/LLR", "file": "LLR_MATRIX_HD_x.txt" },
               "mode": "HD", "max_iter": 120,
               "channel_llr_HD": [8], "channel_llr_2SD": [6, 10],
               "channel_llr_3SD": [4, 6, 8, 10],
               "use_default_edge_quantization": true,
               "edge_quantization": { "edge_resolution_bits": 3, "edge_max_value": 7 } },
  "run": { "seed": 0, "max_frame_errors": 10, "max_frames": 256,
           "frames_per_batch": 64, "stop_below_fer": null,
           "progress_interval_frames": 100 },
  "channels": { "type": "fixed_error",
                "rber": [0.001, 0.002],
                "fixed_error": [200, 300],
                "strong_ratios": { "SER": 0.5, "SCR": 0.5 } },
  "log": { "enabled": true,
           "items": { "csw_per_iter": true, "bit_err_per_iter": true,
                      "bit_err_by_dv": true, "iter_histogram": true,
                      "fer_vs_iter": true, "fail_frame_detail": true,
                      "fer_curve_png": true } },
  "output": { "dir": "Sim_Output", "csv_prefix": "fer" }
}
```

- ㉮ `H_matrix`, `decoder.llr_matrix`: **폴더와 파일명 분리** `{"dir", "file"}`.
  `use_input_llr_matrix`가 true(기본)면 llr_matrix 파일이 필수이고 **mode는
  파일명(HD/2SD/3SD)이, max_iter는 파일의 마지막 iter_end가 결정**한다
  (decoder.mode와 decoder.max_iter는 이 경로에서 읽지 않는다).
  false면 **decoder.mode(기본 HD), decoder.max_iter(이 경로에서 필수),
  decoder.channel_llr_{mode}, edge 양자화 키로 균일 배치 양자화 매트릭스를
  DAO 포맷 파일로 생성해 저장한 뒤 그 파일을 로드**해 디코딩한다
  (llr_matrix 키는 무시, 플래그 값만 바꿔 두 방식을 오갈 수 있다).
  decoder.channel_llr_HD/_2SD/_3SD는 mode별 채널 LLR 크기 리스트
  (전 dv 공통, 강한 region부터, 길이 = region 수 HD 1개 / 2SD 2개 / 3SD 4개)이고
  현재 mode의 것만 소비된다.
  decoder.use_default_edge_quantization이 true(기본)면 기본 edge 양자화(bits 3,
  max 7, 레벨 {7,5,3,1} = C++ 3bit 빌드와 동일)를 쓰고 edge_quantization 블록을
  읽지 않으며, false면 `edge_quantization`의 키로 레벨을 만든다:
  edge_resolution_bits(VNU와 CNU 사이를 오가는 edge 메시지(V2C/C2V)의 양자화
  bit 수. 부호 1bit 포함, 기본 3, 레벨 수 = 2^(bits-1), 채널 LLR의 bit 수가 아님),
  edge_max_value(edge magnitude 최대 레벨 값, 2^n-1 형태, 기본 7. 레벨은 max부터
  (max+1)/레벨수 간격의 내림차순 균일 배치이고 th는 레벨값과 같음.
  예: bits 3, max 15면 {15,11,7,3}. 2^(bits-1)-1보다 작으면 오류).
  생성 파일은 `output.dir` 하위 `_generated/`(git 무시 영역)에 저장된다
  (예: LLR_MATRIX_HD_uniform_3bit_max7_ch8_dv4_iter120.txt).
  파일명의 **uniform은 사람이 만든 파일이 아니라는 표시**이고, 레벨 구성 인식은
  파일명이 아니라 th 값 패턴(공차 d의 등차 감소이고 마지막 항이 2d-1이면 균일)으로 한다
- ㉯ 디코더 선택은 config가 아니라 실험 폴더 run.py의 `DECODER_CLASS`가 한다
  (None이면 BaseDecoder = base_run 기준선, config에는 파라미터만 담는다)
- ㉰ `run.seed`: 실험 전체 난수 seed **하나** (기본 0). 채널과 포인트별 스트림은
  [seed, 채널 인덱스, 포인트]로 파생
- ㉱ `channels`: **객체**. `type`(문자열 또는 문자열 리스트, 리스트면 순서대로 전부
  실행)이 측정할 채널을 고르고, 값 공간은 자리를 미리 만들어 둔다
  (고른 type이 쓰는 공간만 소비하며 그것이 필수, 존재하는 공간은 전부 형식 검사):
  `rber`(RBER 값 리스트, HD/2SD/3SD), `fixed_error`(프레임당 에러 bit 수 리스트,
  fixed_error type(HD)과 strong_error type(2SD)이 **공용으로 소비**),
  `strong_ratios`(`{"SER": 0~1, "SCR": 0~1}`, strong_error type이 fixed_error
  공간과 함께 소비)
- ㉲ `run.max_frame_errors`: 프레임 에러가 이 수에 도달하면 해당 포인트 측정 종료
- ㉳ `run.frames_per_batch`: 한 번에 동시 복호하는 프레임 수 (속도와 메모리 조절용).
  통계 결과는 프레임 수가 충분하면 같고, 같은 seed의 수치 재현에는 이 값까지 같아야 한다
- ㉴ `run.stop_below_fer`: 측정 FER가 이 값 미만이면 해당 채널의 남은 포인트 측정 중단
  (null=사용 안 함, 다음 채널은 계속 진행)
- ㉵ `run.print_progress`: 진행 상황 콘솔 출력 여부 (기본 true).
  `run.progress_interval_frames`: 측정 중 진행 줄 갱신 간격 (프레임 단위, 기본 100)
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
├── summary.txt                  ← 요약 + 코드 git 커밋 해시 + 결과 줄 (측정 중 실시간 기록, 콘솔과 동일)
├── LLR_MATRIX_*.txt             ← 사용한 LLR matrix 사본 (save_llr_matrix 시)
├── fer_{라벨}.csv               ← FER 결과 (post_fec_ber 열 포함, 항상)
├── fer_curves.png               ← FER 커브 (fer_curve_png 시)
├── log_iter_{라벨}_p{포인트}.csv      ← iteration별 CSW/bit error 평균 (dv별 분해 포함)
├── log_iter_hist_{라벨}_p{포인트}.csv ← 수렴 iteration 히스토그램 + fer_vs_iter
└── log_fail_{라벨}_p{포인트}.csv      ← 실패 프레임별 잔여 에러/최종 CSW/dv별 분해
```

- ㉮ `log.enabled`가 로그 전체 상위 스위치다 (false면 `log.items`가 true여도 전부 끈
  것으로 취급, 기본 true). 항목별 on/off는 `log.items` 묶음 안의 키로 하며, 켜면
  iteration 루프 수집 비용으로 속도가 다소 떨어진다
- ㉯ `post_fec_ber`(복호 후 BER)는 로그와 무관하게 항상 FER CSV에 포함
- ㉰ `fer_vs_iter`: 프레임별 성공 iteration 기록으로 "max_iter를 k로 줄였다면"의 FER를
  한 번의 실행에서 산출
- ㉱ 후순위 로그 7종은 미구현 (`_pm/TODO.md` 참조)

## 실험 공간 구조

`workspace/`는 기준 실험(base_run) 전용이고, 논문 아이디어 실험은
`3_LDPC_ideas/` 아이디어 폴더에서 src를 import해 수행한다.
디코더 변형은 `src`(본체 코드)를 고치지 않고 `BaseDecoder`를 상속한 자식 클래스에서
교체용 함수만 재정의한다. **새 논문을 붙이는 절차, 교체용 함수 표, 상속 경계
규칙의 정본은 [3_LDPC_ideas/새논문적용규칙.md](../3_LDPC_ideas/%EC%83%88%EB%85%BC%EB%AC%B8%EC%A0%81%EC%9A%A9%EA%B7%9C%EC%B9%99.md)다.**

```
workspace/
├── _template/        ← 새 실험 시작 시 복사 (run.py, config.json, README.md)
├── base_run/          ← 기준 실험 (재정의 없는 BaseDecoder 그대로, DECODER_CLASS=None)
│   ├── run.py / config.json / README.md
│   └── Sim_Output/   ← 이 실험의 결과 (실행별 폴더, git 무시)
└── {실험}/           ← 논문이나 실험환경별로 자유 생성 (+ 변형이면 decoder.py)
```

- run.py는 상위로 올라가며 src가 있는 폴더를 찾아 검색 경로에 넣는 런처라
  복사 후 수정 없이 동작한다. 디코더 선택은 파일 안 `DECODER_CLASS` 한 곳이다

## 채널 모델: original 대응 3종

`src/channel.py`. 출력은 original의 HD_input/SD_input/CC_input 대응
dict {"mode", "hd", "sd", "cc"}.

| 채널 | original 대응 | 지원 모드 | points 의미 |
|------|---------------|----------|-------------|
| rber | MODE_CH_RBER. RBER를 역Q함수로 AWGN σ 환산(dev_from_RBER), BPSK+노이즈, HD=부호, 2SD/3SD는 \|2y/σ²\|를 LLR_th=2·r_offset/σ²와 비교 (r_offset: 2SD 0.35 / 3SD 0.15, 0.35, 0.55) | HD, 2SD, 3SD | RBER 값 |
| fixed_error | MODE_CH_FIXED_ERROR. 프레임마다 정확히 E개 무작위 bit flip | HD | E (에러 bit 수) |
| strong_error | MODE_CH_STRONG_ERROR. E 중 round(E·SER)개는 strong(sd=1) 에러이고 나머지는 weak, 정정 bit 중 round(C·SCR)개만 strong이고 나머지는 weak | 2SD | E (에러 bit 수) |

- 2SD/3SD 디코딩: LLR matrix를 2SD/3SD 파일(또는 균일 생성 mode)로 지정하고
  rber 또는 strong_error 채널과 조합한다
- 난수는 original XOR25 대신 numpy Generator

## DAO LLR_MATRIX: syndrome-aided decoding

`src/llr_matrix.py`가 DAO(decoder auto optimizer)의 LLR_MATRIX 텍스트 포맷을
읽고, `src/decoder.py`의 `decoder_main()`이 **원본 C++의 flip/magnitude
도메인(syndrome-aided)** 그대로 디코딩한다. 세부 구조와 original 대비 차이는
[docs/차이.md](docs/차이.md)와 `decoder.py` 모듈 설명 참조.

## 남은 근사/제한

- 사람이 만든 LLR matrix 파일은 3-bit(VNU 출력 레벨 {7,5,3,1}) 전용.
  균일 생성물(파일명 uniform)은 n-bit 레벨을 지원한다 (레벨 수는 edge_mag가 결정)
- 파이프라인 store 지연(2~3 col) 미재현 (restart 흔들기 전파가 원본과 다소 다를 수 있음)
- BF(1-bit precision) 구간 미구현 (단순화 형태, BF off 전제)
- 저장소에 담긴 H-matrix와 LLR_MATRIX는 예시 파일이다 (평가할 파일은 `Input/`에
  넣고 config에서 파일명으로 지정한다)
- `encoder.encode()`는 실제 인코딩 없이 all-zero 반환하는 임시 함수

## 확정 결정 기록

시뮬레이터의 방향을 정한 사용자 결정이다 (상세 경위는 `_pm/DONE.md`와 git 이력).

| 결정 | 내용 |
|------|------|
| 상대 비교 전용 (2026-07-29) | Python은 후보 기법의 on/off 상대 비교(FER 1e-2~1e-4 영역)를 맡는다 |
| 단순화 형태는 Python에만 (2026-07-29) | 쇼트닝, 펑처링, HCU, CRC 조기종료를 뺀 단순화 형태는 py 전용. 유효한 기법은 실제 형태의 C++에 적용해 재비교 |
| 제거 항목 (2026-07-29) | HCU, 쇼트닝/펑처링, CRC 조기종료, timing/SRAM/PMU/TV. GT(Graph Thinning)는 edge 라우팅 테이블일 뿐이라 FER 영향 0을 코드로 확인 후 제거 (2026-07-30) |
| 성공 판정 (2026-07-30) | genie: 매 iteration 결정을 정답과 bitwise 비교, 일치하면 그 프레임 성공 확정 (CRC 조기종료의 이상화 대응, 미스검출 없음) |
| codeword (2026-07-30) | all-zero (인코더 포팅 불필요, 대칭 채널과 대칭 복호기 전제) |
| Dual-Update (2026-07-30) | off (단순화 취지). 실제 적용 형태와의 격차는 최종 C++ 검증에서 흡수 |
| 시뮬 방침 (2026-07-30) | max_iter=120 기준, numba 미사용 (numpy 프레임 배치만), 병렬화는 mpi4py로 코어당 sim 1개 (mpi_runner는 재설계 예정) |
| 기준 치수 | base M_b=18 × N_b=147, z_sb=256, codeword 37,632 bit, rate≈0.878, 정보 33,024 bit(4KB). 전 파라미터는 H-matrix 파일에서 읽는다 |
| 입력 파일은 외부 공급 | H-matrix와 LLR 테이블은 저장소에 담지 않는다 (LLR 값은 원본 소스 손상으로 소실되어 사용자가 `Input/`에 넣는다). z_sb=256이면 C++ 쪽 PMU/Clk 경로가 최초로 활성화되는 점 확인 필요 |
| edge 양자화 파라미터 분리 (2026-08-13) | internal_quantize의 edge 레벨을 bit 수(edge_resolution_bits)와 최대값(edge_max_value)으로 분리, 기본은 C++ 3bit 레벨 {7,5,3,1}. th 배치는 레벨값과 동일 (C++는 th가 LLR matrix의 튜닝 데이터라 고정 규칙이 없고, 간격 1에서 th=[top..1]인 기존 균일 경로의 확장으로 결정) |
