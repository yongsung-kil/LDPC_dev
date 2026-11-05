# 003 ulpbf_1pass: ULPBF 1 pass (초기 syndrome 일괄 플립 + CRC 판정)

출처: ieee:11449331 (NVMSA 2025) | 상태: 조건부 유효 (에러 16bit 이하 전용 1단, C++ 반영 검토 대기)

## 📌 요약

- **논문 아이디어**:
    - 에러가 아주 적은 프레임 전용의 **1단계 비트 플립**(ULPBF, Ultra-Low Power
      Bit-Flipping): 처음 한 번 계산한 syndrome만 보고 문턱을 넘는 비트를 한꺼번에
      뒤집고, 성공은 CRC로 판정함
    - 복호 시작 때 한 번 계산한 **syndrome**(패리티 검사 결과 벡터)만 읽어, 비트마다
      **불만족 검사 합**(그 비트가 걸린 패리티 검사 중 어긋난 것의 개수)을 구함
    - 불만족 검사 합이 **dv**(변수 노드 차수, 그 비트가 걸린 검사 개수)별 문턱 T[dv]
      이상이면 **한꺼번에 뒤집음** (pass 1회, 도중에 syndrome을 다시 계산하지 않음)
    - 성공 확인은 syndrome 재계산 대신 **CRC**(cyclic redundancy check, 순환 중복
      검사)로 함
    - 실패하면 원본으로 되돌려 기존 min-sum 디코더를 돌림 (2단 구성)
- **제안 이유**:
    - iteration(반복)마다 들던 syndrome 레지스터 갱신과 채널 원본 저장소 접근이
      이 1 pass에는 전혀 없음
    - 에러가 충분히 적으면 에러 비트만 자기 검사 대부분에서 어긋나므로 문턱 플립
      한 번으로 바로잡힘
- **성공시 효과**:
    - 저에러 프레임이 iteration 1회 분량의 연산으로 끝남
    - 그 프레임의 syndrome 갱신량(전력 대리 지표)이 0이 됨
    - 논문은 (5, 50)-regular 코드에서 decoding 단계 전력 42% 감소를 보고함
- **개선 확인방법**:
    - 1단 단독 성공률의 t(프레임당 에러 수) 곡선
    - 실패 시 오플립 수, 2단 구성 FER(frame error rate, 프레임 오류율)의 비열화
    - CRC 거짓 통과 수, min-sum iteration 생략률 (상세는 아래 평가 계획 표)
- **실험 결과**:
    - **판정: 조건부 유효**. 에러 16bit 이하 프레임 전용의 맨 앞 단으로 성립: 1단 단독
      성공률 <span class="better">t=8에서 86.2%</span>, 그 프레임의 min-sum iteration
      <span class="better">84-100% 생략</span>, 2단 구성 FER(프레임 오류율)는 비열화
    - 1단 단독 성공률(최선 문턱, CRC 판정)은 <span class="better">t=8에서 86.2%,
      t=16에서 46.6%</span> (50% 교차 t=15 부근). t ≥ 50은 0%
    - t ≤ 8 프레임은 <span class="better">min-sum iteration의 84-100%가 생략됨</span>
      (잔존비 0.000-0.155)
    - 2단 구성 FER = min-sum 단독 FER (비열화), CRC 거짓 통과 0/55,000프레임
    - 조건 1: 논문의 일률 문턱 T=dv-1은 이 비규칙 H-matrix에서 <span class="worse">t=8
      성공률 1.7%로 동작하지 않음</span>. dv별 혼합 문턱(T=dv 기본, dv 11만 10)이 필수
    - 조건 2: 이득은 저에러 프레임의 비율에 비례함 (평가 영역 전체의 대체물이 아님)

## 📄 출처 상세

- **논문**:
    - "Ultra-Low Power LDPC Decoder Design for NAND Flash Storage" (NVMSA 2025,
      IEEE Non-Volatile Memory Systems and Applications Symposium)
    - 아카이브 ID ieee:11449331
- **핵심 아이디어**:
    - 1 pass 일괄 플립과 CRC 판정으로 syndrome 재계산과 GD 메모리(채널 원본
      저장소)를 없앰
    - 실패하면 GDBF(gradient descent bit flipping)로 재시작하는 2단 구조
- **적용 분석 메모**:
    - [메모_ieee11449331_ULPBF.md](../_pm/tasks/%EC%A0%84%EB%A0%A5%EA%B0%90%EC%B6%95_%EB%85%BC%EB%AC%B8%EC%A0%95%EB%8F%85/%EB%A9%94%EB%AA%A8_ieee11449331_ULPBF.md)

## 📊 평가 계획

| 지표 | 무엇을 판별하는지 | 수집 방법 |
|------|------------------|-----------|
| FER, BER, avg_iter | 최종 성능 | 항상 수집 |
| 1단 단독 성공률 vs t | 경량 1 pass의 유효 한계 (논문 그림 7 대응) | 자체 수집 (decoder.py stats) |
| 1단 실패 프레임의 오플립, 누락, 잔여 에러 (genie 기준) | 실패한 pass가 다음 단에 짐이 되는지 | 자체 수집 |
| 2단 구성 FER 대 min-sum 단독 FER (같은 채널 실현) | 성능 비열화 확인 | scan.py 동시 측정 |
| CRC 거짓 통과 수 | 미검출 위험 정량화 | 자체 수집 (CRC-32를 실제로 계산) |
| min-sum iteration 잔존비 | syndrome 갱신 생략량의 대리 전력 지표 | 자체 수집 (iteration 합 비교) |

- **min-sum iteration 잔존비**: 2단 구성이 쓴 min-sum iteration 합을 min-sum
  단독의 합으로 나눈 값
    - 1에서 빼면 생략률
    - iteration당 syndrome 갱신량이 일정하므로 syndrome 갱신 생략의 대리 지표가 됨

## 🔬 py 스크리닝 실험

### 바꾼 것

| 항목 | 내용 |
|------|------|
| **디코더** | decoder.py의 ULPBF1PassDecoder. `decoder_main` 전체 재정의 (BF 계열은 교체용 함수 6개 경계에 맞지 않음, 새논문적용규칙.md 2절 세 번째 갈래) |
| **1단** | 초기 syndrome을 읽기 전용으로 써서 1 pass 일괄 플립 (pass 도중 syndrome 갱신 없음) |
| **판정** | CRC-32 모델 (information 구간을 zlib.crc32로 실제 계산, 거짓 통과까지 모델링). syndrome 0 여부와 genie 판정도 동시 기록 |
| **2단** | CRC 불통과 프레임만 플립을 버리고 HD(hard decision, 경판정) 원본으로 부모 BaseDecoder min-sum 폴백 |
| **문턱 변형 5종** | T[dv] = max(dv - offset, 2)의 offset 0, 1, 2와 dv별 혼합 두 가지 (mixA: dv 11만 10, mixB: dv 11은 10에 dv 4는 3) |
| **채널** | fixed_error (프레임당 고정 에러 수 t 주입, 본체 channel.py 제공), t = 1-150 격자 |

### 실험 환경

| 항목 | 값 |
|------|-----|
| H-matrix | matrix_sel_1.txt (base 15x145, z=256, N=37120, K=33280, dv 분포 {2:14, 3:69, 4:20, 11:42}) |
| LLR matrix | LLR_MATRIX_HD_matrix_sel_1.txt (HD, max_iter 120) |
| 프레임 | seed 0, 포인트당 1000 프레임, frames_per_batch 64 |
| 기준선 | min-sum 단독에 같은 채널 실현을 공급 (scan.py가 t마다 한 번 생성해 모든 디코더에 입력) |

### 준비된 실험 (config 슬롯)

| config | 확인하려는 것 | 채울 슬롯 | 실행 |
|--------|--------------|-----------|------|
| config.json | 2단 구성 FER (표준 하니스) | 없음 | `python run.py` |
| config.json + scan.py | 1단 성공률, 오플립, 거짓 통과, iteration 잔존비, 문턱 5종 비교 | 없음 | `python -X utf8 scan.py` |

### 결과

#### 결과 1. 1단 단독 성공률 (%, CRC 판정 기준, 포인트당 1000 프레임)

> - **조건**: 문턱 5종, t는 프레임당 에러 수
> - **핵심**: <span class="better">dv별 혼합 문턱 mixA가 전 구간 최선</span>. 논문의
>   일률 T=dv-1은 <span class="worse">t=8에서 1.7%</span>로 동작하지 않음

| 문턱 \ t | 1 | 2 | 4 | 8 | 12 | 16 | 20 | 30 | 50-150 |
|---|---|---|---|---|---|---|---|---|---|
| T=dv | 100 | 99.1 | 95.5 | 80.5 | 60.7 | 34.6 | 19.7 | 1.9 | 0 |
| T=dv-1 | 100 | 82.7 | 37.2 | <span class="worse">1.7</span> | 0 | 0 | 0 | 0 | 0 |
| T=dv-2 | 100 | 74.6 | 25.5 | 0 | 0 | 0 | 0 | 0 | 0 |
| T=mixA (dv11만 10) | 100 | 99.4 | 97.1 | <span class="better">86.2</span> | <span class="better">69.8</span> | <span class="better">46.6</span> | 30.0 | 4.7 | 0 |
| T=mixB (dv11은 10, dv4는 3) | 100 | 99.6 | 97.9 | 86.6 | 69.7 | 45.8 | 26.3 | 2.4 | 0 |

#### 결과 2. 최선 변형 T=mixA의 상세

> - **조건**: 결과 1과 같은 실행, 포인트당 1000 프레임
> - **핵심**: CRC 판정이 syndrome 0 판정보다 성공률을 크게 올림. <span class="better">CRC
>   거짓 통과 0건, 2단 구성 FER = 기준 FER</span>. t ≤ 8에서 min-sum iteration 잔존비
>   0.000-0.155

| t | 성공률 CRC 판정 (%) | 성공률 syndrome 0 판정 (%) | 실패 프레임 평균 오플립 | 평균 누락 | 평균 잔여 에러 | min-sum iteration 잔존비 | CRC 거짓 통과 | 2단 / 기준 FER |
|---|---|---|---|---|---|---|---|---|
| 1 | 100 | 100 | 0 | 0 | 0 | <span class="better">0.000</span> | 0 | 0 / 0 |
| 2 | 99.4 | 98.7 | 0.00 | 1.17 | 1.17 | 0.007 | 0 | 0 / 0 |
| 4 | 97.1 | 89.8 | 0.00 | 1.31 | 1.31 | 0.032 | 0 | 0 / 0 |
| 8 | 86.2 | 59.8 | 0.52 | 1.12 | 1.64 | <span class="better">0.155</span> | 0 | 0 / 0 |
| 12 | <span class="better">69.8</span> | 30.5 | 1.11 | 1.43 | 2.54 | 0.339 | 0 | 0 / 0 |
| 16 | 46.6 | 9.1 | 1.96 | 1.47 | 3.44 | 0.566 | 0 | 0 / 0 |
| 20 | 30.0 | 3.3 | 2.89 | 1.79 | 4.68 | 0.722 | 0 | 0 / 0 |
| 30 | 4.7 | 0 | 6.46 | 3.02 | 9.48 | 0.956 | 0 | 0 / 0 |
| 50 | <span class="worse">0</span> | 0 | 19.1 | 8.6 | 27.6 | <span class="worse">1.000</span> | 0 | 0 / 0 |
| 100 | 0 | 0 | 81.1 | 33.7 | 114.8 | 1.000 | 0 | 0 / 0 |
| 150 | 0 | 0 | 188.2 | 71.1 | 259.3 | 1.000 | 0 | 0 / 0 |

#### 지표별 해석

1. **유효 한계**:
    - 1단 성공률 50% 교차점이 t = 15 부근이고, t ≤ 8에서 86-100%, t ≥ 50에서 0%
    - 메모의 대략 추정(t 15-25 부근까지 성립, t 40-50부터 대부분 실패)과 들어맞음
    - <span class="better">저에러 프레임 전용의 맨 앞 단이라는 자리가 실측으로 확인됨</span>
2. **문턱은 T=dv가 기본, 큰 dv만 한 칸 내림**:
    - 논문의 T = dv - 1 (regular dv 5 기준)은 이 비규칙 H-matrix에 그대로 옮기면
      <span class="worse">t = 8에서 성공률 1.7%</span>
    - 까닭: dv 2-3 열이 전체 비트의 57%인데 문턱이 2가 되면 정상 비트 오플립이 폭증함
    - dv 11만 10으로 내린 mixA는 전 구간에서 T=dv보다 좋음 (t = 12에서 60.7% 대 69.8%)
    - 검사 공유 충돌 1회를 허용해 에러 누락을 줄이면서, 정상 dv 11 비트가 10개
      검사에서 동시에 어긋날 확률은 무시할 만큼 작기 때문
3. **CRC 판정이 syndrome 판정보다 성공률을 크게 올림**:
    - parity 구간에 잔여 에러가 있어도 information 구간이 깨끗하면 CRC는 통과시킴
      (t = 12에서 30.5% 대 <span class="better">69.8%</span>)
    - C++의 PCRC(partial CRC) 조기 종료와 같은 수용 기준이라 구조가 일치함
    - syndrome 0을 기다리는 판정보다 1 pass의 실질 성공 범위를 넓힘
4. **미검출 위험은 관찰되지 않음**:
    - CRC 거짓 통과(information 구간에 에러가 남았는데 CRC 통과)는 전 변형, 전
      포인트 55,000 프레임에서 0건
    - 기대 확률이 2^-32 차원이라 이 규모에서 0이 정상
5. **비열화 확인**:
    - 같은 채널 실현에서 2단 구성 FER = min-sum 단독 FER (전 포인트 에러 0 대 0,
      포인트당 1000 프레임 해상도)
    - 실패 시 HD 원본으로 되돌리는 설계라 1단의 오플립이 2단에 전파되지 않음
6. **전력 대리 지표**:
    - t ≤ 8인 프레임은 <span class="better">min-sum iteration의 84-100%가 사라짐</span>
      (mixA 잔존비 0.000-0.155)
    - 실제 전력 수치는 C++/HW 측정이 필요함

## ✅ 결론

- **판정: 조건부 유효**
- **근거**: 1 pass + CRC 판정의 2단 구성은 t ≤ 16 영역에서 높은 성공률(47-100%)로
  min-sum iteration을 대부분 생략하면서 FER 비열화와 미검출 0건을 확인함
- **조건**:
    1. 이득이 저에러 프레임의 비율에 비례함. 평가 영역(프레임당 0-150bit) 전체의
       대체물이 아니라 다단 구조의 맨 앞 단이며, t ≥ 50 프레임에는 이득이 없음
       (게이트로 걸러 기존 경로로 보내므로 손해도 1 pass 지연뿐)
    2. 문턱은 비규칙 H-matrix에 맞춰야 함 (T=dv 기본에 dv 11만 10. 논문의 일률
       dv - 1은 역효과)

## ⏭ 후속

- 반영 대기: C++ 반영 시 `Select_BF`에 2차 문턱(ULPBF 게이트)을 추가하고, 1 pass
  모드에서 syndrome 레지스터 갱신을 끄고 PCRC로만 판정 (메모의 "끼워 넣는 지점" 절)
- 추가 확인 1: 평가 영역의 프레임당 에러 수 분포 실측 (게이트 문턱과 기대 적용률
  산정의 근거, 메모 7절 ㉴)
- 추가 확인 2: 게이트를 초기 syndrome weight로 걸었을 때의 적용률과 낭비 pass율
  (이번 스크리닝은 전 프레임에 1단을 적용함)
