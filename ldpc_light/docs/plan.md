# ldpc_light — 논문 아이디어 스크리닝용 경량 Python 시뮬레이터 (계획)

> 생성일: 2026-07-29
> **목적**: LDPC 논문 아이디어를 빠르게 적용/비교하기 위한 vanilla 형태의 경량 Python 시뮬레이터.
> HW 모사 요소(timing/SRAM/PMU/TV)를 제거하고 알고리즘만 남긴다.
> 스크리닝에서 살아남은 아이디어만 C++ Ref-C에 이식하여 최종 검증한다.
> 논문 이식성 판정 기준: [paper_screening_profile.md](../../docs/paper_screening_profile.md)

---

## 1. 배경 — 확정된 결정 사항 (2026-07-29 논의)

| # | 결정 | 내용 |
|---|------|------|
| 1 | 2단계 하이브리드 | Python으로 아이디어 스크리닝 (FER 1e-2~1e-4 영역) → 유효 아이디어만 C++ 이식 후 최종 검증 |
| 2 | Vanilla 형태 | vanilla(쇼트닝/펑처링/HCU/조기종료 제거)는 **Python에만** 적용. 아이디어가 유효하면 실제 형태의 C++에 적용해 재비교 |
| 3 | 제거 항목 (사용자 결정) | HCU, 쇼트닝/펑처링, 조기종료(고정 iteration), timing/SRAM/PMU/TV, 기타 성능 영향 없는 HW 요소 |
| 4 | 성공 판정 | Partial CRC 대신 **송신 codeword와 bitwise 비교** |
| 5 | LLR 관련 | quantization/ch/th 매핑은 기 최적화 값 사용 (필요 시 약간 튜닝). speed_opt 2-9의 텍스트 파일 포맷([llr_tables_template.txt](../../ldpc_revised/llr_tables_template.txt))을 그대로 로드. **주의(리뷰 확인)**: 템플릿에 실값은 공란이고 CH_3SD/TH_*는 소스 손상으로 소실 — 실값은 사용자 공급 필요. 현재 코드의 `Get_VNU_Table_Idx()`는 `return 0` 스텁이라 사실상 단일 세트 동작 |
| 6 | 파라미터 | z_sb = **256**. **실물 치수(리뷰 확정)**: base **M_b=18 × N_b=147** (`H_Matrix/18_by_147_DvMax3/`, `HCU_start=N_b−M_b−punct=127`로 역산 일치). 정보부 = N_b−M_b = 129 block = 33,024 bit = 4,128 B ≈ **4KB(정보 길이)**, codeword = 147×256 = 37,632 bit, rate ≈ 0.878. CLAUDE.md 상수표(N_b=M_b=129)는 자기모순으로 신뢰 불가 — light 버전은 전부 H-matrix 파일에서 파라미터로 읽는다 |
| 7 | 병렬화 | GPU 불가. 슈퍼컴 멀티코어에서 **mpi4py로 코어당 sim 1개** + 각 sim 내부에서 **numpy 프레임 배치 벡터화** |

## 2. 유지 / 제거 대응표

FER에 영향을 주는 것은 알고리즘 요소이므로, 제거는 "HW 구조 요소 + 사용자가 vanilla 비교를 위해 뺀 알고리즘 요소"로 한정한다.

| 원본 (.cpp) 요소 | light .py | 근거 |
|------------------|-----------|------|
| Min-Sum CN 연산 (min1/min2 + sign) | **유지** (동일 표현) | 핵심 알고리즘 |
| **Column-wise 순차 스케줄** (col 순서대로 C2V→V2C→CN 상태 즉시 갱신) | **유지** — `schedule="column_wise"` (2026-08-03 사용자 확인: phase는 없애되 column 단위 연산·업데이트는 반영) | 수렴 특성 결정 — flooding으로 바꾸면 안 됨 |
| Quantized LLR 도메인 + iteration별 LLR 테이블 | **유지** (2-9 파일 로드) | FER 직결 |
| 채널 (AWGN + HD/2SD/3SD 양자화, th/ch 매핑) | **유지** | FER 직결 |
| HCU (127/128 half-column) | 제거 | 사용자 결정 (vanilla) |
| 쇼트닝 / 펑처링 (punct_col_num=2) | 제거 | 사용자 결정 — C++ vanilla도 동일하게 제거하므로 동조건 비교 |
| 조기종료 (Partial/Full CRC) | 제거 — **CRC 기반** 조기종료만 제거. 채점은 genie(매 iter 정답과 bitwise 비교, 일치 시 성공 확정) | 사용자 결정 + 리뷰 반영 |
| col_M1~P4 파이프라인 / SRAM / PMU / overall_clk | 클록/타이밍 모델은 제거. column-wise 즉시 갱신은 `schedule="column_wise"`로 재현 (C++ `CNU_Remove_Old_Sgn`/`CNU_Update_New_Mag` 원문 로직 — 단일 CN 상태 remove-old/insert-new, min1 교체 시 min2=RESET(V_VERY_STRONG) 근사, `<=` 비교 포함). **phase별 store 지연(2~3 col)만 미재현** | 리뷰 발견 B-H1 + 2026-08-03 사용자 확인 반영 |
| TV 출력 전체 | 제거 | HW 검증 전용 |
| GT (Graph Thinning MUX) | 제거 | 코드 검증(2026-07-30): `Mux_idx`는 edge→MUX 채널 **라우팅 테이블**일 뿐 모든 edge가 매 iteration 처리됨 (`GT.cpp` `Make_GT_HW`, `decoder.cpp` 사용처 전수 인덱싱 용도) → **FER 영향 0**, 클록/면적만의 문제 |
| corner 추적 / local_opt / XOR25 RNG | 제거 — numpy RNG 사용 | 시뮬 부가 기능 (시드 재현성은 numpy `Generator`로 확보) |
| Dual-Update (parity even/odd 교대) | **off (확정)** | 사용자 결정 (2026-07-30) — vanilla 취지. 실제 적용 형태와의 격차는 최종 C++ 검증에서 흡수 |

## 3. 설계

### 3.1 코드 위치·모듈 구성

신규 폴더 `ldpc_light/` (repo 루트, `ldpc_revised/`와 형제):

| 파일 | 역할 | C++ 대응 |
|------|------|----------|
| `config.py` | 파라미터 (N_b, z_sb, max_iter, 양자화 비트 등) | `ecc_data.h` PARAM_DEC/PARAM_LLR |
| `pcm.py` | H-matrix 파일 로드 (기존 포맷 그대로 파싱), base matrix + circulant shift | `ecc_top.cpp` `Load_PCM()`, `input.cpp` |
| `llr_tables.py` | 2-9 포맷 LLR 테이블 파일 로드 | `decoder.cpp` LLR 테이블 로드 |
| `channel.py` | AWGN/BSC + HD/2SD/3SD 양자화 → **read-bit/구간(region)까지** (리뷰 확인: 원본 channel.cpp도 여기까지만 담당. LLR **값** 부여는 VN 단계 테이블 소관 → decoder.py) | `channel.cpp` `Set_R_Offset()`, `Set_LLR_Th()` |
| `decoder.py` | quantized min-sum, column-wise(기본)/two_set 스케줄, HW-근사 3-bit 프로파일, 배치 벡터화 | `decoder.cpp` `LDPC_Decoder()`, `C2V_Cal()`, `VN_Cal_*()`, `CNU_*` |
| `sim.py` | FER 하니스: 배치 생성 → 복호 → bitwise 판정 → 통계 | `ecc_top.cpp` 프레임 루프 |
| `mpi_runner.py` | mpi4py: rank별 시드 분할, 에러 카운트 Allreduce | `mpi.cpp` (`__RUN_MPI__`) |

- 인코더: **all-zero codeword** 사용 확정 (대칭 채널 + 대칭 복호기에서는 all-zero로 FER 측정 가능 → 인코더 불필요).
- 논문 아이디어는 `decoder.py`의 훅(예: CN/VN 업데이트 함수 교체, 스케줄 순서 함수 교체)으로 붙인다. 아이디어별 코드는 `ldpc_light/ideas/` 하위에 분리.

### 3.1b 예시 부호 생성 도구 (2026-07-30 사용자 추가 지시)

실물 H-matrix 없이도 end-to-end 검증과 논문의 부호설계 실험이 가능하도록, 예시 QC-LDPC 생성 도구를 함께 만든다:

| 파일 | 역할 |
|------|------|
| `tools/peg.py` | PEG(Progressive Edge Growth)로 base graph 생성 — 정보부 컬럼의 CN 연결을 girth(최단 사이클 길이) 최대화 방향으로 배치 |
| `tools/lifting.py` | base graph → QC lifting: 각 edge에 circulant shift 값 부여 (z_sb 파라미터, 짧은 사이클 회피 검사) |
| `tools/gen_example_code.py` | 위 둘을 묶어 **dual-diagonal parity 구조의 QC-LDPC** 예시 H-matrix 파일 생성 (기존 입력 포맷) |
| `examples/fer_curve.py` | 예시 부호로 FER 테스트 실행 → **정정능력 커브** (FER vs SNR/RBER) 데이터·그래프 출력 |

- 예시 부호 파라미터: **실물과 동일 치수 M_b=18, N_b=147, z_sb=256, rate≈0.878** (리뷰 반영: M_b≈13은 dv_max=17과 양립 불가 — base graph column degree ≤ M_b)
- 예시 실행의 LLR 매핑은 기본 양자화 프로파일로 (실물 테이블은 파일 확인 후 교체 가능하게 분리)
- 예시 H-matrix 저장은 우선 자체 텍스트 포맷 (실물 H-matrix 파일이 저장소에 없어 원본 포맷 대조 불가 — 실물 반입 후 `pcm.py`에 원본 포맷 파서 추가)

### 3.2 배열 설계 (벡터화 축)

- 채널 LLR: `(B, N_b, z_sb)` — B = 프레임 배치 크기 (32~128 예상)
- CN 상태 (리뷰로 정정): 실제 C++ `CN_STATE`는 **5필드 {min1_pos, min1_value, min2_value, check_sum, syndrome}** (`ldpc_revised/decoder.h:30-36`)이고, **edge별 V2C sign은 별도 메모리 `Check_SRAM_sgn[M][K]`** — py도 (B, M_b, z) CN 상태 + (B, E, z) edge sign을 모두 갖는다. C2V 재구성: mag = (해당 edge가 min1_pos면 min2, 아니면 min1), sign = sign 누적 ⊕ 해당 edge 저장 sign. **스케줄 (2026-08-03 정정)**: 원본은 old/new 2세트가 아니라 **단일 CN 상태를 column 진행 중 즉시 remove-old→insert-new 갱신하는 column-wise** (`CNU_Remove_Old_Sgn`/`CNU_Update_New_Mag`) — py `schedule="column_wise"`(기본 대응)로 재현, `two_set`(flooding 등가)은 비교용으로 유지
- LLR 도메인 (리뷰로 확인): 원본 디코더는 signed LLR이 아니라 **magnitude(비음수 0~31) + HD bit(Variable_mem) + syndrome의 flip 도메인** (`common.h` CH_LLR_MIN=0, `decoder.cpp` "syndrome-aided decoding"). py 뼈대는 수학적으로 등가인 signed 표현으로 구현 (실물 C++ 정합이 필요해지면 flip 도메인 모드 추가). 스펙 우선순위: **decoder.cpp 코드 > L2 문서** (L2 문서에도 오류 존재 가능 — 리뷰 B-M3)
- circulant shift는 사전 계산한 인덱스 배열(또는 `np.roll`)로 처리 (speed_opt 2-1과 동일 발상)
- column 루프(129회 × iteration)는 Python 루프로 유지, 그 내부 연산만 `(B, dv, z_sb)` 배열 연산

### 3.3 병렬화 구조

```
총 처리량 = 코어 수 (mpi4py, rank당 sim 1개) × 프레임 배치 벡터화 (rank 내부, 10~30배)
```

- rank 간 통신: 시드 분할 + 에러/프레임 카운트 합산(Allreduce)만. C++ `__RUN_MPI__`와 동일 패턴
- 로컬(Windows) 개발 시에는 MPI 없이 단일 프로세스로 동작해야 함 (mpi4py 미설치 시 fallback)

## 4. 검증 방식

- py는 **상대 비교(아이디어 on/off) 전용**. py↔C++ 절대 FER 대조(calibration)는 수행하지 않는다.
- 유효 아이디어의 최종 검증: **실물 C++(실제 형태 — 펑처링/HCU/CRC 조기종료 포함)에 직접 이식**하여 기존 대비 FER 비교.
- 실물 파라미터 반입 (py 재현도 향상용):
  1. H-matrix 실물 파일 (`H_Matrix/18_by_147_DvMax3/` — 저장소에 없음, 외부 반입)
  2. LLR 테이블 실값 (llr_tables 템플릿은 공란, CH_3SD/TH_* 소스 소실 — 사용자 공급)
- z_sb=256 주의(실물 C++ 실행 시): `factor = z_sb/PMU_UNIT_SIZE`가 0→2로 바뀌어 PMU/Clk 경로가 최초 활성화됨 (speed_opt 2-19/6-1 문서는 z_sb=32 전제) — 확인 필요.

## 5. 진행 순서

1. `ldpc_light/` 뼈대: pcm → channel → decoder → sim (완료 2026-07-30)
2. 예시 부호 도구(PEG/lifting/dual-diagonal) + 예시 FER 테스트 → 정정능력 커브 출력 (완료 2026-07-30)
3. H-matrix / LLR 테이블 실물 파일 확인 (z_sb=256 대상 파일 식별) → 실물 파라미터로 교체
4. mpi_runner + 슈퍼컴 반입
5. 논문 아이디어 훅 설계 → 스크리닝 시작
6. 유효 아이디어 → 실물 C++ 이식·최종 검증 (§4)

## 6. 안전성 체크리스트

- [ ] 기존 `LDPC_Original/`, `ldpc_revised/` 코드는 **수정하지 않음** (신규 폴더 `ldpc_light/`만 생성)
- [ ] 이 환경에서 C++ 빌드/실행하지 않음 (기존 규칙 유지)
- [ ] TV 포맷/HCU 버퍼/Partial CRC 다항식/H-matrix 파싱 등 "절대 건드리면 안 되는 것"과 무관 (읽기만)

## 7. 확정 사항 (2026-07-30 사용자 결정)

| # | 항목 | 결정 |
|---|------|------|
| 1 | 성공 판정 시점 | **매 iteration hard decision을 정답과 비교, 일치 시 그 프레임 성공 확정** (genie 판정) |
| 2 | codeword 생성 | **all-zero** (인코더 포팅 불필요) |
| 3 | Dual-Update | **off** |
| 4 | 시뮬 파라미터 | **max_iter = 120** (2026-07-30 사용자 지정). SNR/RBER 범위·배치 크기는 실험별 설정 |
| 5 | numba | **사용 안 함** — numpy 배치만. 추후 필요 시 재검토 |
