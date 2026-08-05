# Dependency Map

> Level 2 문서 — 모듈 간 의존 관계와 변경 영향 범위.
> 파일 수정 전 영향 범위 판단 시 참조.

---

## 모듈 호출 그래프

```
main.cpp
  ├─→ ECC_Top (Init_ECC_Top, Run_ECC_Top_Ref_C, Run_ECC_Top_TV_Gen)
  └─→ LOCAL_OPT (Run_Local_Opt) [__AUTO_LLR_OPT__]

ECC_Top
  ├─→ Input (Load_H_Matrix, Get_Sector_Num, Get_DIN_noPS)
  ├─→ GT (Make_GT_HW, Release_GT)
  ├─→ Random (Set_Random_Seed_xor25, rand_msg_xor25, rand_sel_ep, Make_Msg_TV)
  ├─→ Encoder (Init_Enc, LDPC_encoder_4KB)
  ├─→ Channel (Set_R_Offset, Set_LLR_Th) [글로벌 함수]
  ├─→ Full_CRC (CRC_encoder)
  ├─→ Decoder (Init_Dec, Init_Dec_Option, LDPC_Decoder)
  ├─→ CornerChecker (Set_Param, Update, Print, Clear)
  ├─→ TV_Dec (Set_Param, Print_TV_Dec_In, Print_TV_Dec_Out)
  └─→ TV_Enc (Set_Param, Print_TV_Enc_In, Print_TV_Enc_Out, Print_TV_Enc_Inter)

Decoder
  ├─→ Partial_CRC (partial_crc_HW_T4) [4 LFSR]
  ├─→ Full_CRC (CRC_decoder)
  ├─→ CornerChecker (Event_Flag, Event_Power_Stopping, Event_Result)
  └─→ TV_Dec_Inter (Print_TV_* 시리즈) [__ECC_TV__]

LOCAL_OPT
  └─→ ECC_Top (Init_ECC_Top, Run_ECC_Top_Ref_C)
```

말단 모듈 (외부 호출 없음): Encoder, Channel, Input, Random, GT, Full_CRC, Partial_CRC, Corner, TV_Dec, TV_Enc, TV_Dec_Inter, MPI

---

## 계층 구조

```
Level 0 (Entry)     : main.cpp
Level 1 (Orchestr.) : ecc_top.cpp, local_opt.cpp
Level 2 (Processing): decoder.cpp, encoder.cpp
Level 3 (Utility)   : channel, input, random, full_CRC, partial_CRC, GT, corner
Level 4 (Output)    : TV_Dec, TV_Enc, TV_Dec_Inter
```

순환 의존 없음. 모든 호출은 상위→하위 방향.

---

## #include 의존 그래프

### 핵심 허브

```
mode.h ← common.h ← (거의 모든 .h)
                   ← ecc_data.h ← (decoder.h, encoder.h, ecc_top.h, input.h, GT.h, TV_*, corner.h)
```

### 헤더별 include 목록

| 헤더 | 포함하는 로컬 헤더 |
|------|-------------------|
| mode.h | (없음 — 최하위) |
| mpi.h | (없음) |
| common.h | mode.h, mpi.h |
| ecc_data.h | common.h |
| channel.h | common.h |
| full_CRC.h | common.h |
| partial_CRC.h | common.h |
| random.h | common.h |
| encoder.h | ecc_data.h |
| input.h | common.h, ecc_data.h |
| GT.h | common.h, ecc_data.h |
| corner.h | common.h, ecc_data.h |
| TV_Dec.h | common.h, ecc_data.h |
| TV_Enc.h | common.h, ecc_data.h |
| TV_Dec_Inter.h | common.h, ecc_data.h |
| decoder.h | common.h, ecc_data.h, partial_CRC.h, full_CRC.h, corner.h, random.h, TV_Dec_Inter.h |
| ecc_top.h | common.h, ecc_data.h, decoder.h, encoder.h, full_CRC.h, partial_CRC.h, random.h, input.h, GT.h, corner.h, channel.h, TV_Dec.h, TV_Enc.h |
| local_opt.h | common.h, ecc_data.h, decoder.h, encoder.h, full_CRC.h, partial_CRC.h, random.h, input.h, GT.h, ecc_top.h |

### 시스템 헤더

| 파일 | 시스템 헤더 |
|------|-----------|
| common.h | iostream, fstream, time.h, stdlib.h, string.h, math.h, direct.h (Win), sys/stat.h, sys/types.h, fcntl.h, unistd.h (Linux) |
| channel.h | math.h |

다른 모든 파일은 common.h를 통해 시스템 헤더에 간접 접근.

---

## 외부 의존성

| 의존성 | 용도 | 필수 | 버전 제약 |
|--------|------|------|-----------|
| MSVC (cl.exe) | 컴파일러 | Y | VS 2022 (19.44+) |
| C++ Standard Library | iostream, fstream, cmath 등 | Y | C++11 이상 |
| Windows SDK | `<direct.h>` (디렉토리 생성) | Y (Win) | Win10+ |
| MPI | 병렬 시뮬 | N | `mpi.h` stub으로 대체 |
| H-matrix 파일 | `H_Matrix/H_402091.txt` | Y (런타임) | 전용 포맷 |

외부 라이브러리 의존 없음 (self-contained).

---

## 빌드 시스템 분석

### 빌드 도구

`LDPC_Original/build.bat` — MSVC cl.exe 직접 호출 (단일 타겟)

```bat
cl /EHsc /W3 /O2 /Fe:ldpc_sim.exe *.cpp
```

- `/EHsc`: C++ 예외 처리
- `/W3`: 경고 레벨 3
- `/O2`: 최적화 (속도 우선)
- CMake/Makefile 없음, IDE 프로젝트 파일 없음

### 조건부 컴파일

`mode.h`의 `#define`으로 제어. 코드 포함/제외가 아닌 **분기 선택**:

| 매크로 | OFF 시 제외되는 코드 경로 |
|--------|--------------------------|
| `__PROGRAM_MODE_REF_C__` | Setup_Ref_C, Run_Ref_C 경로 |
| `__ECC_TV__` | 모든 Print_TV_* 호출 (decoder.cpp 내) |
| `__ECC_TV_ITER__` | iteration별 TV 출력 |
| `__HALF_COL_UPDATE__` | *_HCU() 함수 호출, HCU 버퍼 할당 |
| `__DUAL_UPDATE__` | DU_Manager, Column_Reordering |
| `__RUN_PUNCT_RECOVERY__` | punct_vote 복구 로직 |
| `__AUTO_LLR_OPT__` | LOCAL_OPT 경로 전체 |
| `__RUN_MPI__` | MPI 초기화/통신 |

모든 .cpp는 항상 컴파일에 포함됨 — 파일 단위 제외 없음.
링크 순서 제약 없음 (단일 cl.exe 호출).

---

## 변경 영향 맵

### 전역 영향 (수정 시 전체 리빌드 + 동작 변경)

| 파일 | 영향 |
|------|------|
| `mode.h` | **전체 리빌드 + 실행 경로 변경** |
| `common.h` | **전체 리빌드** (모든 파일이 직간접 include) |
| `ecc_data.h` | decoder, encoder, ecc_top, input, GT, TV_*, corner 리빌드 |

### 모듈별 영향

| 수정 파일 | 직접 영향 | 간접 영향 |
|-----------|----------|----------|
| `decoder.h` | decoder.cpp, ecc_top.cpp, local_opt.cpp | TV_Dec_Inter (포함됨) |
| `decoder.cpp` | (자기 자신) | 없음 — 하위 모듈 호출만 |
| `encoder.h` | encoder.cpp, ecc_top.cpp, local_opt.cpp | |
| `encoder.cpp` | (자기 자신) | |
| `ecc_top.h` | ecc_top.cpp, local_opt.cpp | main.cpp (ecc_top.h 직접 include) |
| `ecc_top.cpp` | (자기 자신) | |
| `channel.h` | channel.cpp, ecc_top.h (→ ecc_top.cpp, local_opt.cpp) | |
| `input.h` | input.cpp, ecc_top.h (→ ecc_top.cpp, local_opt.cpp) | |
| `partial_CRC.h` | partial_CRC.cpp, decoder.h (→ decoder.cpp, ecc_top.cpp) | |
| `full_CRC.h` | full_CRC.cpp, decoder.h (→ decoder.cpp, ecc_top.cpp) | |
| `GT.h` | GT.cpp, ecc_top.h (→ ecc_top.cpp, local_opt.cpp) | |
| `corner.h` | corner.cpp, decoder.h (→ decoder.cpp, ecc_top.cpp) | |
| `random.h` | random.cpp, decoder.h (→ decoder.cpp), ecc_top.h (→ ecc_top.cpp) | |
| `TV_Dec_Inter.h` | TV_Dec_Inter.cpp, decoder.h (→ decoder.cpp) | |
| `TV_Dec.h` | TV_Dec.cpp, ecc_top.h (→ ecc_top.cpp) | |
| `TV_Enc.h` | TV_Enc.cpp, ecc_top.h (→ ecc_top.cpp) | |
| `local_opt.h` | local_opt.cpp | main.cpp (local_opt.h 직접 include) |

### .cpp 수정 시

.cpp 파일 수정은 해당 파일만 재컴파일 (헤더 변경 없을 때).

---

## 참조

- [CLAUDE.md](../CLAUDE.md)
- [Architecture Overview](architecture.md)
- [ADR 목록](adr/README.md)
