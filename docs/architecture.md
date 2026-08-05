# Architecture Overview

> Level 1 문서 — 전체 조감도.
> 새 기능 추가 또는 큰 리팩토링 전에 참조.

---

## 데이터 흐름

```
H-matrix 파일 (H_402091.txt)
    │
    ▼
Load_PCM() ──→ PCM 구조체 채움
    │
    ▼
┌──────────────── 시뮬레이션 루프 (rn = 0..num_run) ────────────────┐
│                                                                    │
│  rand_msg_xor25() ──→ m_msg                                       │
│       │                                                            │
│       ▼                                                            │
│  LDPC_encoder_4KB() ──→ m_cw (dual-diagonal + column reorder)     │
│       │                                                            │
│       ▼                                                            │
│  Channel_Simulation ──→ m_HD/SD/CC/CD_input                       │
│  (AWGN/RBER/Fixed)     (LLR 양자화: 1bit HD ~ 3bit 3SD)          │
│       │                                                            │
│       ▼                                                            │
│  LDPC_Decoder() ──→ cwc[] (복호 결과)                              │
│  (iteration loop, pipeline simulation)                             │
│       │                                                            │
│       ▼                                                            │
│  Count_Errors + Print_Results                                      │
│  (TV Gen: hex 파일 출력 / Ref-C: FER 통계)                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 모듈 맵

```
main.cpp
  ├─→ ECC_Top (오케스트레이션)
  │     ├─→ Load_PCM → input.cpp (H-matrix 로드)
  │     ├─→ Encoder (dual-diagonal 인코딩)
  │     ├─→ channel.cpp (AWGN/고정 에러 주입, 글로벌 함수)
  │     ├─→ Decoder (복호 핵심)
  │     │     ├─→ Partial_CRC / Full_CRC
  │     │     ├─→ TV_Dec_Inter (중간 신호 hex 출력)
  │     │     └─→ CornerChecker (수렴 실패 추적)
  │     ├─→ TV_Dec (디코더 TV 입출력 파일)
  │     ├─→ TV_Enc (인코더 TV 출력)
  │     ├─→ GT (Graph Thinning MUX 테이블)
  │     └─→ Random (XOR25 난수)
  └─→ LOCAL_OPT (Auto-LLR 최적화, ECC_Top 래핑)
```

---

## 실행 모드별 경로

### Ref-C 모드 (`__PROGRAM_MODE_REF_C__` 정의)

```
main → Setup_Ref_C(argv) → Run_Simulation_Ref_C()
  → ECC_Top::Run_ECC_Top_Ref_C()
    → Run_Ref_C_Scenario_4KB()      # RBER/Fixed/Strong/Erasure 채널
    → 루프: Encode → Channel(AWGN) → Decode → FER 통계
```

### TV Gen 모드 (기본, `__PROGRAM_MODE_TV_GEN__`)

```
main → Setup_TV_Gen(argv) → Run_Simulation_TV_Gen()
  → ECC_Top::Run_ECC_Top_TV_Gen()
    → Run_TV_Gen_Scenario_4KB()     # 고정 에러 패턴
    → 루프: Encode → Channel(Fixed) → Decode → hex TV 파일 출력
```

### Auto-LLR 최적화 (`__AUTO_LLR_OPT__` + Ref-C)

```
main → Setup_Ref_C(argv) → Run_Simulation_Local_Opt()
  → LOCAL_OPT::Run_Local_Opt()
    → LLR 파라미터 탐색 루프 → ECC_Top 반복 실행
```

---

## 조건 분기 맵

| 매크로 | 활성화 경로 | 비활성화 경로 |
|--------|------------|--------------|
| `__PROGRAM_MODE_REF_C__` | Setup_Ref_C, Run_Ref_C | Setup_TV_Gen, Run_TV_Gen |
| `__HALF_COL_UPDATE__` | C2V_cal_HCU, V2C_Cal_HCU (col 127,128) | C2V_cal 통합 처리 |
| `__HALF_COL_MODIFIED__` | HCU col = 127,128 | HCU col = 0,1 (구형) |
| `__DUAL_UPDATE__` | DU_Manager, Column_Reordering | 단일 업데이트 |
| `__SHUFFLED_DUAL_DIAG__` | Generate_PCM_encoding 변환 | PCM_enc = PCM_b 동일 |
| `__RUN_PUNCT_RECOVERY__` | punct_vote 투표로 복구 | punctured bit 무시 |
| `__ECC_TV__` | TV_Dec_Inter Print_TV_* 호출 | TV 출력 생략 |
| `__ECC_TV_ITER__` | iteration마다 TV 출력 | 최종만 출력 |
| `__AUTO_LLR_OPT__` | LOCAL_OPT 경로, 파일 기반 LLR | 내장 LLR 테이블 |

---

## 주요 데이터 구조

### PCM (Parity Check Matrix)
| 필드 | 타입 | 의미 |
|------|------|------|
| N_b, M_b | int | col/row block 수 (129, 129) |
| N, M | int | 총 VN/CN 수 (N_b×z_sb, M_b×z_sb) |
| z_sb | int | 병렬화 크기 (32) |
| PCM_b | int** | 복호용 base matrix [M_b][N_b] |
| PCM_b_enc | int** | 부호용 base matrix (column reorder 후) |
| ColW / RowW | int* | column/row weight |
| V_net_b | int** | VN 연결 정보 |
| Mux_Matrix / Mux_idx | int** | GT MUX 매핑 |
| punct_col_num | int | punctured col 수 (2) |

### Decoder 핵심 버퍼
| 변수 | 의미 |
|------|------|
| `Check_SRAM_sgn[row][col]` | CN sign 메모리 |
| `Variable_mem[bit]` | VN 메모리 (경판정) |
| `VNU_in/out[mux][z]` | VN Unit 입출력 |
| `Syndrome[row]` | 패리티 체크 결과 |
| `cwc[bit]` | 현재 복호 결과 |
| `REG_min1/2_value[row]` | CN min-sum 레지스터 |
| `tv_*` 시리즈 | TV 출력용 버퍼 (HCU/non-HCU 별도) |

---

## 디코더 파이프라인

HW 클록 시뮬. column-by-column 처리, 서로 다른 stage가 병렬 동작:

```
stage   │ 처리 내용                    │ 변수
────────┼──────────────────────────────┼──────────
col_M1  │ MAIN SRAM 읽기 요청         │ col_M1
col_Z   │ PCRC 초기화, Syndrome       │ col_Z
col_P1  │ C2V 계산 (Check→Variable)   │ col_P1
col_P2  │ V2C 계산 ★TV 출력 지점     │ col_P2
col_P3  │ VN 처리 (HD/SD/CD)          │ col_P3
col_P4  │ V2C 저장                     │ col_P4
```

**HCU dispatch**: `col_P2 ∈ [HCU_start, HCU_end]` → `C2V_cal_HCU()` (half edge)
나머지 → `C2V_cal()` (full edge)

---

## TV 출력 시스템

두 경로 (non-HCU / HCU):

| 구분 | 쓰기 (decoder.cpp) | 읽기 (TV_Dec_Inter.cpp) |
|------|--------------------|-----------------------|
| Non-HCU (col 0~126, 129+) | `tv_*[jj]` 직접 | `Print_TV_*()` col_blk 순회 |
| HCU (col 127, 128) | `tv_*_HCU[jj_temp]` 매핑 | `Print_TV_*_HCU()` (col_blk, G_idx) 매핑 |

**HCU 버퍼 매핑 (even iter)**: col 127 mux<8→buf[127], mux≥8→buf[128], col 128 mux<8→buf[129], mux≥8→buf[130]. odd iter는 G0/G1 교번.

---

## 외부 의존성

| 항목 | 상세 |
|------|------|
| 컴파일러 | MSVC (VS 2022, cl.exe 19.44+) |
| 표준 라이브러리 | iostream, fstream, cmath, cstdlib, cstring, ctime |
| OS API | `<direct.h>` (Win), `<sys/stat.h>` (Linux) |
| MPI | 선택적 (Windows: `mpi.cpp` 더미 stub) |
| 외부 라이브러리 | 없음 (self-contained) |
| 입력 데이터 | `H_Matrix/H_402091.txt` (H-matrix 파일) |

---

## 도메인 용어 사전

| 약어/변수명 | 의미 |
|-------------|------|
| FER | Frame Error Rate |
| PCM / H-matrix | Parity Check Matrix |
| CN / VN | Check Node / Variable Node |
| LLR | Log-Likelihood Ratio |
| TV | Test Vector (HW 검증용) |
| HCU | Half Column Update (col 127,128 특수 처리) |
| C2V / V2C | Check→Variable / Variable→Check 메시지 |
| PCRC | Partial CRC (4개 termination point 조기 종료) |
| AWGN | Additive White Gaussian Noise |
| RBER | Raw Bit Error Rate |
| GT | Graph Thinning (MUX 기반 edge 선택) |
| Dual Update | parity column 재배치 후 두 번에 나눠 처리 |
| Shuffled Dual-Diag | 부호 시 column 순서 변환 (even/odd 분리) |
| BF / HBF | Bit Flipping / Hard-decision BF |
| `jj` | column block index |
| `ii` | edge index within CN |
| `mn` | mini-iteration number |
| `G_idx` | HCU group (0=G0 even, 1=G1 odd) |
| `mux_index` | MUX 채널 (0~15), 물리 edge 매핑 |
| `jj_temp` | HCU 버퍼 매핑 후 인덱스 |
| `col_M1~P4` | pipeline stage별 column |
| `m_PCM` | Decoder 내 PCM 포인터 |

---

## 참조

- [CLAUDE.md](../CLAUDE.md) — 빌드, 규칙, AI 역할
- [ADR 목록](adr/README.md) — 설계 결정 기록
- [디코더 상세](../LDPC_Original/CLAUDE.md) — HCU 매핑, 파이프라인, 변수 상세
