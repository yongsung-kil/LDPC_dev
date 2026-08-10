# Claude 세션 컨텍스트: LDPC 디코더 C++ 코드베이스

> 이 폴더([0_LDPC_original/](./))는 LDPC 디코더 C++ 전체 코드베이스. 소스는 [src/](src/) 하위.
> 이 파일은 **새 Claude 세션이 이 코드로 디버깅/기능 추가/리팩토링할 때 빠르게 컨텍스트 회복하는 용도**.
> 사람용 문서는 [docs/](docs/) 하위. 이 파일만 읽으면 대부분 작업 시작 가능.
> 저장소 공통 규칙은 상위 [../CLAUDE.md](../CLAUDE.md) 참조.

---

## 아키텍처 한눈에

```
main()
  └─ ECC_Top  ← 오케스트레이션 (시뮬레이션 루프, 통계, 파일 I/O)
       ├─ Encoder        ← LDPC 인코딩 (dual-diagonal)
       ├─ Channel*       ← AWGN/RBER/고정 에러 (글로벌 함수)
       ├─ Decoder        ← LDPC 복호 핵심 (파이프라인 시뮬레이션)
       ├─ TV_Enc         ← 인코더 중간신호 파일 출력
       ├─ TV_Dec         ← 디코더 입출력 파일 관리
       └─ TV_Dec_Inter   ← 디코더 내부 신호 16진 출력 (Print_TV_*)
```

보조: `Partial_CRC`, `Full_CRC`, `GT` (Gaussian Trick), `Corner`, `Local_Opt`, `Input`, `Random`, `MPI`

---

## 실행 진입점

`main.cpp` (47줄) → `Setup*()` → `Run_Simulation*()` → `ECC_Top::Run_ECC_Top_*()`

**모드 분기** (`mode.h`):
- `__PROGRAM_MODE_REF_C__` 정의 → `Setup_Ref_C` / `Run_ECC_Top_Ref_C` (성능 측정)
- 미정의 → `Setup_TV_Gen` / `Run_ECC_Top_TV_Gen` (기본, TV 생성)

**시뮬레이션 루프** (`ecc_top.cpp`):
```cpp
for (rn = 0; rn < num_run; rn++) {
    LDPC_encoder();       // msg → codeword
    Channel_Simulation(); // 에러 주입
    LDPC_Decoder();       // 복호 (이터레이션 루프 포함)
    Count_Errors();
    Print_Results();
}
```

---

## 핵심 상수 (암기 필수)

```
N_b = 129                  // column block 수
M_b = 129                  // row block 수
z_sb = 32                  // 병렬화 단위 (codeword = N_b * z_sb bit)
punct_col_num = 2          // punctured column 수
HCU_start = N_b - M_b - punct_col_num = 127
HCU_end   = N_b - M_b - 1              = 128
N_b - M_b = 129
MAX_DV_GLOBAL      = 17    // 일반 VN degree
MAX_DV_GLOBAL_HALF = 10    // HCU VN degree
SEPARATE_V_DEG_1 = 9       // HCU col 127 1st half edge 수
SEPARATE_V_DEG_2 = 7       // HCU col 128 1st half edge 수
MUX 분할 경계 = 8          // mux_index < 8 / >= 8
CRC_LEN = 80
NUM_PCRC_TERMINATION_POINT = 4
SEED_LEN = 25              // XOR25 RNG
```

**주의**: `SEPARATE_V_DEG(9,7) ≠ MUX 경계(8)` — 논리 edge 분할과 물리 MUX 채널 분할이 다름.

---

## 주요 컴파일 스위치 (`mode.h`)

| 매크로 | 의미 |
|--------|------|
| `__PROGRAM_MODE_REF_C__` | 성능 시뮬 모드 (미정의 = TV 생성) |
| `__ECC_TV__` | 디코더 내부 신호 출력 활성 |
| `__ECC_TV_ITER__` | iter별 TV 출력 |
| `__HALF_COL_UPDATE__` | HCU 모드 활성 |
| `__HALF_COL_MODIFIED__` | HCU를 col 0,1 (OLD) → 127,128 (NEW)로 이동 |
| `__DUAL_UPDATE__` | 이중 업데이트 |
| `__RUN_PUNCT_RECOVERY__` | punctured bit 복구 |
| `__SHUFFLED_DUAL_DIAG__` | shuffled dual-diag 인코딩 |
| `__RUN_MPI__` | MPI 병렬 |
| `__AUTO_LLR_OPT__` | LLR 파라미터 자동 최적화 |

---

## 파일 목록 (38개)

### 핵심 디코더/인코더
| 파일 | 역할 |
|------|------|
| `decoder.cpp` / `.h` | LDPC 복호 전체 (C2V, V2C, VN, HCU 포함). 1100+ 줄 |
| `encoder.cpp` / `.h` | LDPC 인코딩 (dual-diagonal) |
| `ecc_top.cpp` / `.h` | 시뮬 오케스트레이션, 버퍼, 결과 통계 |
| `ecc_data.h` | PCM, PARAM_DEC, PARAM_REF_C, ECC_INFO 구조체 |
| `common.cpp` / `.h` | 전역 상수, 매크로, 초기화 |
| `mode.h` | 컴파일 스위치 모음 |

### 채널/입출력
| 파일 | 역할 |
|------|------|
| `channel.cpp` / `.h` | AWGN, RBER, Gaussian, SD 양자화 (글로벌 함수) |
| `input.cpp` / `.h` | H-matrix 파일 로드, 경로 관리 |

### TV (Test Vector) 출력
| 파일 | 역할 |
|------|------|
| `TV_Dec_Inter.cpp` / `.h` | 디코더 중간 신호 출력 (`Print_TV_old_sgn`, `Print_TV_vtc_inp`, `Print_TV_new_sgn` 각 HCU/non-HCU 쌍) |
| `TV_Dec.cpp` / `.h` | 디코더 TV 버퍼/파일 할당 |
| `TV_Enc.cpp` / `.h` | 인코더 중간 신호 출력 |

### CRC / 복구
| 파일 | 역할 |
|------|------|
| `partial_CRC.cpp` / `.h` | Partial CRC (4개 termination point) |
| `full_CRC.cpp` / `.h` | Full CRC (Ref-C 모드) |
| `GT.cpp` / `.h` | Gaussian Trick 테이블 생성 |
| `corner.cpp` / `.h` | Corner case 추적 (수렴 실패 분석) |

### 부가
| 파일 | 역할 |
|------|------|
| `random.cpp` / `.h` | XOR25 난수 생성기 |
| `local_opt.cpp` / `.h` | Auto-LLR 파라미터 최적화 |
| `mpi.cpp` / `.h` | MPI 병렬화 |
| `main.cpp` | 진입점, Setup 위임 |

---

## 디코더 파이프라인 스테이지

하드웨어 클록 시뮬. 각 clock cycle마다 여러 파이프라인 stage가 서로 다른 column을 동시 처리:

```
col_M1         ← M1 읽기
col_M1_temp    ← M1 지연
col_Z          ← PCRC 초기화, Syndrome
col_P1         ← C2V 계산 (Check→Variable)
col_P2         ← V2C 계산 시작 (Variable→Check) ★ TV 출력 지점
col_P3         ← VN 처리 (HD/SD/CD)
col_P4         ← V2C 저장
```

**HCU dispatch**: `col_P2 >= HCU_start && col_P2 < HCU_end+1` → `C2V_cal_HCU()` (half edge만)
나머지는 → `C2V_cal()` (full edge)

**이터레이션 루프** (`decoder.cpp` L1370+):
```cpp
while (!end_iteration) {
    C2V_cal(col_P2);      // or C2V_cal_HCU for HCU columns
    V2C_Cal(col_P2);
    V2C_Store(col_P2);
    end_iteration = Check_End_Iter();
}
```

---

## 네이밍/변수 규칙

| 약어 | 의미 |
|------|------|
| `jj` | column index (0 ~ N_b-1) |
| `ii` | edge index (Check node 내 위치) |
| `mn` | mini-iteration 번호 |
| `iter` | 전체 iteration 번호 |
| `G_idx` | HCU even/odd group index (0=G0, 1=G1) |
| `col_M1~P4` | 파이프라인 stage column |
| `mux_index` / `mux_idx` | MUX 채널 (edge당 0~15). C2V_Cal에선 `mux_index`, V2C_Store에선 `mux_idx` |
| `jj_temp` | 매핑된 버퍼 인덱스 (HCU 레이아웃) |
| `VNU_in/out` | Variable Node Unit 입출력 |
| `Check_SRAM_sgn` | Check node sign 메모리 |
| `Variable_mem` | VN 메모리 |
| `Syndrome` | 패리티 체크 결과 |
| `m_PCM` | Decoder의 PCM 포인터 (대부분 메서드에서 참조) |

**함수명**: PascalCase + 약어 (예: `C2V_Cal`, `VN_Cal_HD`, `Get_Mag_2SD`)

---

## TV 출력 시스템 (중요)

두 경로:

**Non-HCU** (일반 col 0~126, 129+):
- `C2V_Cal()` 내에서 `tv_vtc_inp[jj]`, `tv_new_sgn_mag[jj]` 등에 직접 쓰기
- `Print_TV_old_sgn()`, `Print_TV_vtc_inp()`, `Print_TV_new_sgn()` — col_blk 그대로 순회

**HCU** (col 127, 128):
- `C2V_Cal()` / `V2C_Store()` 내 `jj_temp` 매핑으로 `tv_*_HCU` 버퍼에 쓰기
- `Print_TV_*_HCU()` 함수들이 col_blk → (col_blk_effective, G_idx) 매핑 후 읽기

**HCU 버퍼 레이아웃** (현 최신 수정본 기준, even iter):
```
col 127, mux<8   → buf[127]
col 127, mux>=8  → buf[128]
col 128, mux<8   → buf[129]
col 128, mux>=8  → buf[130]
col 129+         → buf[jj + punct_col_num]
col 0~126        → buf[jj]
```
odd iter는 G0/G1 교번.

**decoder.cpp의 두 매핑 블록 (항상 동기화 필요)**:
- `C2V_Cal` L2482-2504 (변수: `mux_index` / `mux_index_temp`)
- `V2C_Store` L2819-2841 (변수: `mux_idx` / `mux_idx_temp`)

---

## ECC 데이터 흐름

1. `input.cpp::Load_H_Matrix()` → H-matrix 파일 → `PCM` 구조 채움
2. `ecc_top.cpp::Load_PCM()` → `PCM` 초기화 (puncture, shift, V_net 등)
3. `Decoder::Init_Dec()` → `m_PCM` 포인터 저장
4. `LDPC_Decoder()` → `m_PCM` 참조하여 연산

`PARAM_DEC` (mode, LLR threshold, BF option) → `Setup_*()`에서 로드 → `Init_ECC_Top()`이 Decoder에 전달.

**주의**: 복호는 `PCM_b`, 부호는 `PCM_b_enc` (다름).

---

## 코드 스타일

- **한글 주석** 다수 (특히 함수 섹션 divider)
- **함수명**: PascalCase + 약어
- **메모리**: 수동 new/delete (`Alloc_` / `Release_` 쌍)
- **에러 처리**: assert 거의 없음, NULL 체크 선택적
- **상수**: `#define` + struct 혼용

---

## 실수하기 쉬운 곳 (디버깅 시 체크리스트)

1. **HCU 두 매핑 블록 동기화**: `decoder.cpp` L2482-2504와 L2819-2841. 변수명만 다름 (`mux_index` vs `mux_idx`)
2. **MUX 경계 vs SEPARATE_V_DEG**: 8 vs 9/7. 물리 MUX와 논리 edge 분할이 다름
3. **even/odd 교번**: `G_idx` 결정 로직 확인. `iter % 2` 단독으론 부족
4. **buf 범위**: HCU 버퍼 크기 = N_b + punct_col_num (= 131). 0~130 인덱스
5. **col_P1~P4 구분**: TV 호출 위치가 어느 stage인지 확인 필수
6. **Partial CRC**: 4개 termination point 각각 로직 상이
7. **PCM vs PCM_b_enc**: 복호/부호 서로 다른 PCM 사용
8. **#else 블록 버그**: `decoder.cpp` L2535-2537 `jj==1, mux>=8, even`에 `mux_index - 8` 누락 (OLD 코드 — 현재 경로와 무관하나 혼동 주의)

---

## 참조 문서 (필요시만)

- [docs/architecture.md](docs/architecture.md) (전체 조감도), [docs/guide/](docs/guide/) (알고리즘, 사용법), [docs/adr/](docs/adr/) (설계 결정 기록)

---

## 작업 시작 전 빠른 체크

- [ ] 어떤 모드? (Ref-C? TV_Gen? HCU on/off?)
- [ ] 수정할 스테이지는? (C2V / V2C / VN / TV 출력)
- [ ] HCU column 관련? → 두 매핑 블록 동기화 확인
- [ ] TV 출력 관련? → 쓰기(decoder.cpp)와 읽기(TV_Dec_Inter.cpp) 양쪽 확인
- [ ] 전체 빌드 영향? → `mode.h` 스위치 조합 확인