# Prime ECC 3.1 (LDPC_2) — 논문 이식성 판정용 코드 프로파일

> 생성일: 2026-07-02
> **용도**: 논문 분석 agent가 "이 논문 기법을 이 코드(Prime ECC 3.1 = LDPC_2)에 이식 가능한가"를
> 판정할 때 참조하는 **자기완결 요약**. 이 파일 하나로 판정 가능.
> Prime ECC 3.1 = 현재 LDPC_2 프로젝트 코드다.
> 코드를 실제로 수정/디버깅할 때는 [CLAUDE.md](../CLAUDE.md) / [architecture.md](architecture.md) / [guide/algorithms.md](guide/algorithms.md) 참조 (이 파일은 판정 전용).

---

## 1. 한 문장 정체성

NAND Flash 컨트롤러에 내장되는 **binary QC-LDPC** ECC 엔진(Prime ECC 3.x)의
**bit-exact C++ 시뮬레이터**. 실제 HW(RTL) 디코더/인코더를 클록 레벨로 모사한다.
→ 판정 기준은 항상 "**NAND용 고전 binary QC-LDPC의 부호설계→디코더→HW**에 떼어 쓸 수 있는가".

## 2. 부호 스펙 (판정 카테고리 직결)

| 항목 | 값 | 비고 |
|------|-----|------|
| 부호종류 | **QC-LDPC** (base matrix + circulant shift), **binary** | `PCM_b` = base+shift (`ecc_data.h:157`) |
| lifting / 병렬단위 | `z_sb = 32` | row 단위 병렬 |
| 구조 | `N_b = 129` col-block, `punct_col_num = 2`, VN degree 17 | HCU col 2개만 degree 9/7 |
| 부호 rate | **high-rate (NAND ECC급, ~0.9 추정)** | ⚠ 정확 rate/length는 H-matrix(`matrix_sel`) 종속. 문서상 `N_b/M_b` 표기에 내부 불일치 있어 **정확값 미검증** — 논문의 rate와 비교 시 "고rate QC-LDPC"로만 취급 |
| 연판정 | `hard-1bit`(HD) / `soft-2~3bit`(2SD/3SD) 지원 | NAND read 비용과 직결. soft-4bit+ 는 미지원 |
| 채널 | AWGN / RBER / fixed-error 패턴 | `channel.cpp` |

## 3. 이미 보유한 기법 (중복 기여는 추천도↓)

디코더 핵심:
- **Min-Sum** (min1/min2 + sign XOR). Sum-Product의 `tanh`를 min 근사 (HW 면적/전력). scaling/normalized factor는 코드상 명시 미확인 — magnitude 양자화 테이블 기반.
- **iterative message passing** (C2V → V2C), **Dual-Update**(parity even/odd 교대 스케줄) 옵션.
- **조기종료**: Partial CRC 4 termination point + Full CRC.
- **적응형 LLR**: iteration 구간별 LLR threshold 테이블 (HD/2SD/3SD 별도).

HW 특화 (이미 구현):
- **pipeline 6-stage** bit-exact 시뮬 (col_M1/Z/P1~P4).
- **Graph Thinning (GT)**: MUX 기반 edge 선택으로 클록당 처리 edge 축소.
- **HCU (Half Column Update)**: 비대칭 degree col(127,128)을 2 cycle half-column 처리.
- 인코딩: **dual-diagonal** (shuffled dual-diag 옵션). 복호 PCM(`PCM_b`) ≠ 부호 PCM(`PCM_b_enc`).

## 4. 이식 관점 — 논문이 건드리는 레이어 → 우리 코드 대응

| 논문이 개선하는 것 | 우리 대응 위치 | 이식 난이도 |
|---|---|---|
| 디코더 알고리즘 (min-sum 변형, 스케줄링, post-processing, error-floor 대책) | `decoder.cpp` `LDPC_Decoder()` 이터레이션 루프 | **낮음 (가장 쉬움)** |
| soft-info / 양자화 / LLR 설계 | `channel.cpp` + LLR 테이블 (`PARAM_LLR`) | 낮음~중 (NAND read 비용 고려) |
| HW arch (병렬화, 메모리, 라우팅, pipeline) | 디코더 HW 모델 (z=32, HCU, GT) | 중 (우리 구조와 정합 필요) |
| 부호설계 (H-matrix / protograph / QC 구성) | `ecc_top.cpp` `Load_PCM()` + H-matrix | **높음** (특정 QC-LDPC 고정, 재검증 부담 큼) |
| 인코더 | `encoder.cpp` (dual-diagonal 고정) | 중~높음 |

## 5. 판정 필터 (이 코드 기준)

- **binary LDPC 전용**. non-binary(GF(q)) LDPC 기법은 이식성 대체로 `하`.
- **이미 보유**(§3)와 중복되는 기여(min-sum/HCU/dual-update/partial-CRC 조기종료/적응형 LLR/graph thinning)는 추천도↓.
- **관심 높음(추천도↑)**: min-sum 성능 개선(waterfall/error-floor), avg iteration·latency 감소, soft-read 비용 절감, HW 면적/throughput 개선, 고rate QC-LDPC 부호설계.
- **관련성**: NAND/SSD 직접 타깃 or 고전 binary LDPC = `직접`; 일반 binary LDPC 이식가능 = `간접`; non-binary·광통신·5G/무선 특화·NN 전면 대체 = 대체로 `낮음`.

## 6. 모듈 지도 (코드 접근 없이 이 표만으로 C섹션 작성)

**파일별 역할** — 논문 요소가 어느 모듈에 닿는지 판단용:

| 파일 | 역할 (한 줄) |
|------|------|
| `decoder.cpp/.h` | LDPC 복호 전체: min-sum CN 연산, VN 처리, 이터레이션 루프, HCU, pipeline, LLR 테이블 참조 |
| `encoder.cpp/.h` | dual-diagonal 인코딩, 부호용 PCM(`PCM_b_enc`) 생성, dual-update column 재배치 |
| `ecc_top.cpp/.h` | 시뮬 오케스트레이션, H-matrix/PCM 로드, 통계 |
| `ecc_data.h` | 핵심 구조체 (PCM, PARAM_DEC, LLR 파라미터 등) |
| `channel.cpp/.h` | AWGN/RBER/fixed 에러 주입, soft-read LLR 양자화·threshold |
| `input.cpp/.h` | 입력(DIN/MSG) 파싱 |
| `partial_CRC.cpp` / `full_CRC.cpp` | 조기종료용 CRC (Partial=4 termination point) |
| `GT.cpp/.h` | Graph Thinning: MUX 기반 edge 선택 테이블 |
| `TV_Dec_Inter/TV_Dec/TV_Enc` | HW 검증용 중간신호 hex 출력 (알고리즘 무관) |
| `corner.cpp` `random.cpp` `local_opt.cpp` `mpi.cpp` | 수렴실패 추적 / XOR25 난수 / LLR 자동최적화 / MPI stub |

**논문 요소 → 모듈·함수 (실존 검증됨)** — C섹션에 이 이름만 사용:

| 논문 요소 (예) | Prime ECC 모듈 |
|---|---|
| 디코딩 알고리즘 전체 | `decoder.cpp` `LDPC_Decoder()`, `C2V_Cal()` |
| CN min-sum 연산 | `decoder.cpp` `CNU_Update_New_Mag()`, `C2V_Cal_New_Sgn()` |
| VN 처리 / 양자화 | `decoder.cpp` `VN_Cal_HD()` 등 (HD/2SD/3SD), `decoder.h` `Get_VNU_*` |
| iteration별 LLR 테이블 | `ecc_data.h` `PARAM_LLR`, `decoder.cpp` `Get_VNU_Table_Idx()` |
| 조기종료(CRC) | `partial_CRC.cpp` `partial_crc_HW_T4()`, `full_CRC.cpp` |
| 인코딩 / 부호 PCM 생성 | `encoder.cpp` `LDPC_encoder_4KB()`, `Generate_PCM_encoding()`, `Column_Reordering_Dual_Update()` |
| 채널 / soft-read threshold | `channel.cpp` `Set_R_Offset()`, `Set_LLR_Th()` |
| H-matrix / 부호구조 로드 | `ecc_top.cpp` `Load_PCM()` |
| HW edge/MUX(그래프 씨닝) | `GT.cpp` `Make_GT_HW()` |
| (대응 없음 예시) | NN/딥러닝 디코더, non-binary LDPC, full-`tanh` Sum-Product, turbo/polar |

> C섹션엔 **위 표의 파일·함수명만** 사용한다 (코드 직접 확인 불필요). 표에 없는 논문 요소는 "대응 없음".
