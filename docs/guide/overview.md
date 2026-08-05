# Overview — LDPC Simulator

## 이 프로젝트는 무엇인가

NAND Flash 메모리 컨트롤러에 내장되는 LDPC(Low-Density Parity-Check) ECC 엔진의 **소프트웨어 시뮬레이터**이다. "Prime ECC 3.x"라는 이름의 실제 하드웨어 ECC 블록을 C++로 모사한다.

크게 두 가지를 한다:
1. **성능 측정 (Ref-C 모드)**: 다양한 채널 조건(SNR, RBER 등)에서 인코딩→에러 주입→디코딩을 반복하여 FER(Frame Error Rate)을 통계적으로 측정한다. 하드웨어 설계 전에 알고리즘 성능을 검증하는 목적.
2. **HW 검증 데이터 생성 (TV Gen 모드)**: 특정 에러 패턴에 대해 디코더 내부의 모든 중간 신호를 16진수 파일로 출력한다. 하드웨어 팀이 RTL 시뮬레이션 결과와 bit-exact 비교하는 용도.

---

## 전체 데이터 흐름

```
H-matrix 파일 (PCM 정의)
    │
    ▼
① PCM 로드 + 초기화
    │
    ▼
② 랜덤 메시지 생성
    │
    ▼
③ LDPC 인코딩 (dual-diagonal 방식)
    │    → 메시지 + 패리티 = codeword
    │
    ▼
④ 채널 시뮬레이션 (에러 주입)
    │    → AWGN 노이즈 또는 고정 에러 패턴
    │    → LLR 양자화 (HD 1bit / 2SD 2bit / 3SD 3bit)
    │
    ▼
⑤ LDPC 디코딩 (iterative message passing)
    │    → Min-Sum 알고리즘, 파이프라인 시뮬레이션
    │    → Partial CRC로 조기 종료 판단
    │
    ▼
⑥ 결과 처리
     → Ref-C: 에러 수 카운트, FER/BER 누적 통계
     → TV Gen: 중간 신호를 hex 파일로 출력
```

각 단계가 어떤 모듈에서 수행되는지:

| 단계 | 담당 모듈 | 핵심 함수 |
|------|----------|----------|
| ① PCM 로드 | input.cpp + ecc_top.cpp | `Load_H_Matrix()`, `Load_PCM()` |
| ② 메시지 생성 | random.cpp | `rand_msg_xor25()` |
| ③ 인코딩 | encoder.cpp | `LDPC_encoder_4KB()` |
| ④ 채널 | channel.cpp | `Set_R_Offset()`, `Set_LLR_Th()` |
| ⑤ 디코딩 | decoder.cpp | `LDPC_Decoder()` |
| ⑥ 결과 | ecc_top.cpp / TV_*.cpp | `Count_Errors()`, `Print_TV_*()` |

---

## 주요 모듈

### ECC_Top (ecc_top.cpp)
시뮬레이션의 지휘자 역할. 위 ①~⑥을 순서대로 호출하고, 전체 통계를 관리한다. 모든 주요 모듈의 인스턴스를 멤버로 보유하며, Ref-C와 TV Gen 시나리오를 각각 별도 함수로 운영한다.

### Decoder (decoder.cpp)
코드베이스에서 가장 크고 복잡한 모듈 (7000+ 줄). 하드웨어 디코더의 **파이프라인 동작을 클록 레벨로 시뮬레이션**한다. column 단위로 처리하며, 한 클록에 여러 파이프라인 stage가 서로 다른 column을 동시 처리하는 것을 모사한다. HCU(Half Column Update) 같은 하드웨어 특화 동작도 포함.

### Encoder (encoder.cpp)
Dual-diagonal 방식의 LDPC 인코딩을 수행한다. Dual Update 모드에서는 column 순서를 재배치하는 전처리(`Column_Reordering_Dual_Update`)가 추가된다. 외부 모듈 의존 없이 독립적으로 동작한다.

### Channel (channel.cpp)
에러가 있는 채널을 시뮬레이션한다. AWGN(가우시안 노이즈) 채널이 기본이고, RBER/고정 에러 패턴도 지원한다. 수신 값을 다양한 해상도(HD 1bit, 2SD 2bit, 3SD 3bit)로 양자화하여 디코더에 전달한다.

### TV_Dec_Inter (TV_Dec_Inter.cpp)
디코더 내부 신호를 16진수로 출력하는 전용 모듈. 하드웨어 팀과의 인터페이스 역할이므로 출력 포맷을 절대 변경해서는 안 된다. HCU column과 일반 column에 대해 별도의 출력 경로를 갖는다.

### 보조 모듈
- **Partial_CRC / Full_CRC**: 디코딩 중간에 CRC를 검사하여 조기 종료 여부를 판단. Partial CRC는 4개의 termination point가 있어 이터레이션을 일찍 끝낼 수 있다.
- **GT (Graph Thinning)**: MUX 기반 edge 선택 테이블. 하드웨어에서 메모리 접근을 줄이기 위한 기법.
- **Corner**: 디코딩 수렴 실패 케이스를 추적하고 통계를 내는 디버깅용 모듈.
- **Random**: XOR25 기반 의사 난수 생성기. 재현 가능한 시뮬레이션을 위해 seed 고정 가능.
- **LOCAL_OPT**: LLR 파라미터를 자동으로 탐색하는 최적화 래퍼. ECC_Top을 반복 실행하며 최적값을 찾는다.

---

## 파일 구조와 설계 의도

```
0_LDPC_original/
├── main.cpp              ← 진입점 (모드 분기만)
├── ecc_top.cpp/.h        ← 오케스트레이션 (모든 모듈 조합)
├── decoder.cpp/.h        ← 디코딩 핵심 (파이프라인 시뮬)
├── encoder.cpp/.h        ← 인코딩
├── ecc_data.h            ← 공유 데이터 구조체 정의
├── common.cpp/.h         ← 전역 상수/매크로
├── mode.h                ← 컴파일 스위치
├── channel.cpp/.h        ← 채널 모델
├── input.cpp/.h          ← H-matrix 파일 I/O
├── TV_Dec_Inter.cpp/.h   ← 디코더 중간 신호 출력
├── TV_Dec.cpp/.h         ← 디코더 TV 파일 관리
├── TV_Enc.cpp/.h         ← 인코더 TV 출력
├── partial_CRC.cpp/.h    ← Partial CRC (조기 종료)
├── full_CRC.cpp/.h       ← Full CRC
├── GT.cpp/.h             ← Graph Thinning 테이블
├── corner.cpp/.h         ← 수렴 실패 추적
├── random.cpp/.h         ← 난수 생성
├── local_opt.cpp/.h      ← LLR 파라미터 최적화
├── mpi.cpp/.h            ← MPI stub (Windows)
└── build.bat             ← 빌드 스크립트
```

파일 분리 기준은 **하드웨어 블록 대응**이다. 실제 칩에서 Encoder, Decoder, CRC 체커가 별도 블록이듯이, 시뮬레이터도 각각 별도 파일로 분리되어 있다. `ecc_top`이 이들을 조합하는 상위 컨트롤러에 해당한다.

---

## 확장 포인트

| 하고 싶은 일 | 건드릴 곳 |
|-------------|----------|
| 새 디코딩 알고리즘 | `decoder.cpp` — `LDPC_Decoder()` 내부 이터레이션 루프 |
| 새 채널 모델 추가 | `channel.cpp` — 새 함수 추가 + `ecc_top.cpp`에서 호출 |
| LLR 테이블 변경 | `ecc_data.h` (PARAM_LLR) + `decoder.h` (Get_VNU_* 함수) |
| 새 H-matrix 포맷 | `input.cpp` — `Load_H_Matrix()` 파서 수정 |
| 새 컴파일 모드 | `mode.h`에 매크로 추가 + 관련 파일에 `#if defined()` 분기 |
| 새 TV 출력 항목 | `TV_Dec_Inter.cpp`에 Print 함수 추가 + `decoder.cpp`에서 호출 |

---

## 참고

- 기술 상세는 [architecture.md](../architecture.md) (AI용, 테이블 중심)
- 설계 결정 이력은 [ADR](../adr/README.md)
- 의존성/영향 범위는 [dependency_map.md](../dependency_map.md)
