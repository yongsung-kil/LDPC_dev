# Algorithms — 주요 알고리즘 설명

이 문서는 코드에서 사용하는 알고리즘의 **직관적 이해**를 목적으로 한다.
수학적 정밀성보다는 "왜 이렇게 하는지", "대안은 뭐가 있었는지"에 초점을 맞춘다.

---

## LDPC 디코딩 기본 원리

### Tanner Graph와 Message Passing

LDPC 코드는 Parity Check Matrix(PCM, H-matrix)로 정의된다. 이 행렬을 **Tanner Graph**라는 이분 그래프(bipartite graph)로 표현할 수 있다:

- **Variable Node (VN)**: 각 codeword bit에 하나씩. "이 bit가 0일 확률이 얼마인가?"를 추정한다.
- **Check Node (CN)**: 각 parity check equation에 하나씩. "이 체크식이 만족되는가?"를 검사한다.
- **Edge**: H-matrix에서 1인 위치에 연결. VN과 CN이 메시지를 주고받는 통로.

디코딩은 이 그래프에서 **메시지를 반복 교환**하는 과정이다:

1. **초기화**: 채널에서 받은 LLR(Log-Likelihood Ratio)을 VN에 설정
2. **VN → CN (V2C)**: 각 VN이 자신의 현재 추정을 연결된 CN들에게 전달
3. **CN → VN (C2V)**: 각 CN이 받은 메시지를 종합하여 피드백
4. **반복**: 2-3을 수렴하거나 최대 iteration에 도달할 때까지 반복
5. **판정**: 최종 VN 값으로 경판정(hard decision)

직관적으로, VN들은 "내가 0인지 1인지 모르겠으니 주변에 물어본다"고 할 수 있다. CN은 패리티 조건을 통해 "네가 0이면 나머지가 맞고, 1이면 틀린다"라는 힌트를 돌려준다. 여러 번 반복하면 대부분의 bit가 올바른 값으로 수렴한다.

---

## Min-Sum 알고리즘

### 왜 Min-Sum인가

이론적으로 최적인 디코딩 알고리즘은 **Sum-Product (Belief Propagation)**이다. CN 연산에서 `tanh` 함수를 사용해야 하는데, 이것은 하드웨어로 구현하기에 면적과 전력 비용이 크다.

**Min-Sum**은 `tanh` 연산을 **min 연산으로 근사**한 것이다. 성능은 Sum-Product보다 약간 떨어지지만, 하드웨어 구현 비용이 크게 줄어든다. NAND Flash 컨트롤러처럼 면적/전력 제약이 큰 환경에서 표준적인 선택이다.

### 이 코드의 구현

CN 연산에서 각 행(row)에 대해:
- **min1**: 연결된 V2C 메시지 중 최솟값
- **min2**: 두 번째 최솟값
- **min1_pos**: min1이 어느 edge에서 왔는지

C2V 메시지 계산 시:
- min1을 제공한 edge에는 min2를 돌려보낸다 (자기 자신의 기여를 제외하기 위해)
- 나머지 edge에는 min1을 돌려보낸다

부호(sign)는 XOR 기반으로 별도 관리된다 (`Check_SRAM_sgn`).

관련 코드: `decoder.cpp` — `CNU_Update_New_Mag()`, `C2V_Cal_New_Sgn()`
설계 결정 기록: [ADR-001](../adr/ADR-001-min-sum-decoding.md)

---

## Half Column Update (HCU)

### 왜 필요한가

이 LDPC 코드에서 대부분의 column은 degree 17 (17개의 check node와 연결)이다. 하드웨어는 한 클록에 한 column의 모든 edge를 처리하도록 설계되어 있다.

그런데 column 127과 128은 punctured column과 parity 영역의 경계에 위치하여 **비대칭 degree (9와 7)**를 갖는다. 이 두 column을 합치면 degree 16이지만, 하드웨어 타이밍 관점에서 한 번에 full column(degree 17)을 처리하면 **타이밍 위반**이 발생할 수 있다.

### 어떻게 동작하는가

해결책은 column 127, 128을 **half로 나눠 2 cycle에 걸쳐 처리**하는 것이다:

- MUX 경계(8)로 물리적 분할: mux_index < 8 → 첫 번째 half, mux_index >= 8 → 두 번째 half
- SEPARATE_V_DEG(9/7)로 논리적 분할: 실제 edge 수는 9개와 7개

**주의**: 물리적 MUX 경계(8)와 논리적 edge 분할(9/7)이 일치하지 않는다. 이것이 이 코드에서 가장 실수하기 쉬운 부분이다.

Even/Odd iteration에서 G0/G1 그룹이 교번 처리된다. 이 교번 로직은 `G_idx = iter % 2` 기반이지만, 실제 매핑은 더 복잡하다.

관련 코드: `decoder.cpp` — `C2V_cal_HCU()`, `V2C_Cal_HCU()`, jj_temp 매핑 블록
설계 결정 기록: [ADR-002](../adr/ADR-002-hcu-half-column-update.md)

---

## Dual Update와 Shuffled Dual-Diagonal 인코딩

### Dual Update

일반적인 LDPC 디코딩은 모든 column을 순차적으로 한 번 처리하면 1 iteration이다. **Dual Update**는 parity column을 even/odd로 나눠 교대로 처리하는 기법이다. 수렴 속도를 높이는 효과가 있다.

### 왜 인코딩에 영향을 주는가

Dual Update를 사용하면 디코딩 시 column 처리 순서가 변한다. 인코딩 시 생성한 parity의 column 순서가 디코딩 순서와 맞아야 하므로, 인코딩 후 parity column을 **재배치**하는 전처리가 필요하다.

`Column_Reordering_Dual_Update()`가 이 재배치를 수행하고, `Generate_PCM_encoding()`이 부호용 PCM(`PCM_b_enc`)을 생성한다. 복호용 PCM(`PCM_b`)과 부호용 PCM(`PCM_b_enc`)이 **다르다**는 점에 주의해야 한다.

관련 코드: `encoder.cpp:245-335`
설계 결정 기록: [ADR-003](../adr/ADR-003-dual-diagonal-encoding.md)

---

## 적응형 LLR 테이블

### 왜 적응적이어야 하는가

채널에서 받은 신호를 디코더에 전달할 때 LLR(Log-Likelihood Ratio)로 양자화한다. 이 양자화의 threshold 값이 디코딩 성능에 큰 영향을 미친다.

NAND Flash는 셀 상태에 따라 에러 분포가 비균일하다. 또한 디코딩 **iteration이 진행될수록** 최적 threshold가 달라진다 — 초기에는 넓은 범위의 soft information이 유리하고, 후반에는 좀 더 확신 있는 값이 유리하다.

### 어떻게 구현하는가

`PARAM_LLR` 구조체에 iteration 구간별 LLR 테이블을 저장한다. `Get_VNU_Table_Idx(iter)`가 현재 iteration에 맞는 테이블 인덱스를 반환하고, `Get_VNU_Ch_LLR_Adaptive()`와 `Get_VNU_Th_Adaptive()`가 해당 테이블의 값을 참조한다.

HD/2SD/3SD 모드별로 별도 테이블이 있다 (각각 63/36/66 행).

관련 코드: `decoder.h:122-126`, `common.h:396-688`, `ecc_data.h:179-198`
설계 결정 기록: [ADR-004](../adr/ADR-004-adaptive-llr-table.md)

---

## Partial CRC (조기 종료)

### 왜 필요한가

LDPC 디코딩은 반복 알고리즘이므로, 이미 올바른 결과에 도달했는데도 계속 반복하면 시간(하드웨어에서는 전력)이 낭비된다. **CRC(Cyclic Redundancy Check)**로 결과가 올바른지 검사하여, 맞으면 즉시 종료할 수 있다.

Full CRC는 정확하지만 검사에 시간이 걸린다. **Partial CRC**는 codeword를 4구간으로 나눠 각 구간의 CRC를 별도로 검사한다. 4개 termination point 중 하나라도 통과하면 조기 종료 후보가 된다. 하드웨어에서는 이것이 latency와 전력 절감에 직접적으로 기여한다.

관련 코드: `partial_CRC.cpp` — `partial_crc_HW_T4()` (4개 LFSR)

---

## Graph Thinning (GT)

MUX 기반으로 Tanner Graph의 edge 중 일부만 선택적으로 활성화하는 기법이다. 하드웨어에서 한 클록에 처리해야 하는 edge 수를 줄여 메모리 접근과 연산량을 제한한다. `Mux_Matrix`가 어떤 edge가 어떤 MUX 채널에 매핑되는지를 정의한다.

관련 코드: `GT.cpp` — `Make_GT_HW()`

---

## 파이프라인 시뮬레이션

### 왜 파이프라인을 시뮬레이션하는가

이 시뮬레이터의 목적은 단순히 "디코딩 결과가 맞는지"만 확인하는 것이 아니다. 하드웨어와 **bit-exact 동일한 중간 결과**를 생성해야 한다. 하드웨어는 파이프라인으로 동작하므로, 시뮬레이터도 동일한 파이프라인 타이밍을 모사해야 한다.

### 파이프라인 구조

한 클록에 6개 stage가 서로 다른 column을 동시 처리:

| Stage | 역할 | 변수 |
|-------|------|------|
| col_M1 | SRAM 읽기 요청 | col_M1 |
| col_Z | PCRC 초기화, Syndrome | col_Z |
| col_P1 | C2V 계산 | col_P1 |
| col_P2 | V2C 계산, TV 출력 | col_P2 |
| col_P3 | VN 처리 | col_P3 |
| col_P4 | V2C 저장 | col_P4 |

예를 들어, col_P1이 column 5의 C2V를 계산하는 동안, col_P2는 column 4의 V2C를, col_P3는 column 3의 VN을 동시에 처리한다.

관련 코드: `decoder.cpp` — 이터레이션 루프 내 stage 변수들

---

## 성능 관련 파라미터

디코딩 성능(FER)에 영향을 미치는 주요 파라미터:

| 파라미터 | 위치 | FER 영향 |
|----------|------|---------|
| LLR threshold | PARAM_LLR | 직접적. 최적값은 채널 조건마다 다름 |
| Maximum iteration | PARAM_DEC | 높을수록 성능↑, 지연↑ |
| Scaling factor | [사람 확인 필요: 코드에서 확인 불가] | Min-Sum 보정 계수. 있으면 성능↑ |
| H-matrix 구조 | H_Matrix/H_402091.txt | 근본적 성능 결정. 변경 시 전체 재검증 필요 |
| Puncturing 전략 | punct_col_num = 2 | code rate에 영향 |

---

## 참고

- 구조 상세는 [architecture.md](../architecture.md) 참조
- 각 기법의 설계 결정 이력은 [ADR](../adr/README.md) 참조
