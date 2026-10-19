# 메모: CB-ET, column 단위 조기 종료 (ieee:6865738)

- 논문: "High-Throughput QC-LDPC Decoder with Cost-Effective Early Termination Scheme for Non-Volatile Memory Systems" (Lin 외, 2014 학회)
- 핵심 용어: CB-ET(column-based early termination, column 단위 조기 종료), QC-LDPC(quasi-cyclic low-density parity-check, 준순환 저밀도 패리티 검사 부호), NVM(non-volatile memory, 비휘발성 메모리)

---

## 1. 논문이 푸는 문제

- ㉮ NVM 저장장치용 LDPC 복호기는 반복 복호를 쓰는데, 이미 수렴한 뒤에도 최대 iteration까지 도는 잉여 연산이 처리량을 깎고 전력을 낭비한다
- ㉯ 기존 조기 종료의 한계 두 갈래:
  - ㉠ HDA(hard-decision-aided, 연속 두 iteration의 경판정 결과가 같으면 종료): 틀린 상태로 종료하는 거짓 종료가 가능해 NVM에 부적합하고, 직전 iteration의 판정 비트 전체를 저장할 메모리가 필요하다
  - ㉡ 패리티 검사 기반 기법 (논문 참고문헌 [8][9]): 거짓 종료는 없으나 iteration 경계에서만 종료할 수 있어 iteration 중간의 잉여 연산은 줄이지 못한다
- ㉰ 제안: layered min-sum(패리티 검사 행렬의 행 블록을 층으로 나눠 층마다 갱신하는 최소값 근사 복호) 복호기의 block-serial 처리(circulant 부분행렬을 한 번에 하나씩 직렬 처리)와 동시에 패리티 검사식(PCE, parity check equation, H v^T = 0)을 column 단위로 누적 검사하여, iteration 중간(sub-iteration 경계)에서 종료한다. 검사 회로는 XOR 레지스터, permuter(순환 시프터), OR 트리만으로 구현해 면적 부담을 낮춘다

## 2. 기법 상세

### 구조 전제

- ㉮ H는 M x N 배열의 b x b circulant로 구성 (논문 구현은 M = 6, N = 58, b = 160)
- ㉯ layered 복호: 행 블록 하나가 층(layer) 하나, iteration 하나는 M개의 sub-iteration으로 구성, sub-iteration 하나는 해당 층의 circulant N개를 직렬 처리
- ㉰ 갱신식 (논문 식 1-3, normalized min-sum 계수 0.5):
  - ㉠ prior = posterior에서 직전 extrinsic을 뺀 값
  - ㉡ extrinsic = 0.5 x (타 edge prior 부호의 XOR) x (타 edge prior 크기의 최소값)
  - ㉢ posterior = prior + 새 extrinsic

### 판정 로직 (무엇을 column 단위로 세나)

- ㉮ 검사 대상: 현재 posterior의 부호 비트, 곧 현재 경판정 벡터 v. 목표는 H v^T = 0 확인
- ㉯ 복호기가 column block j의 posterior를 갱신해 내보낼 때마다, 그 부호 비트 b개를 검사 대상 층 i의 shift 값에 맞춰 회전(복호 블록과 검사 블록의 shift 차 d_diff_ij 만큼)한 뒤 층별 누적 레지스터 C_i(b bit)에 XOR 누적한다. 층 M개 전부에 대해 병렬로 수행한다
- ㉰ 모든 column block이 한 바퀴(일순) 누적되면 C_i = H_i v^T (층 i의 패리티 검사 결과)가 된다
- ㉱ 종료 조건: OR(C_1, ..., C_M) == 0, 곧 모든 패리티 검사식 충족이면 즉시 종료
- ㉲ 검사는 복호와 완전히 겹쳐 돌므로 파이프라인 정지가 없고, 어떤 시점의 v에 대한 판정은 그보다 sub-iteration 1개 뒤에 확정된다 (논문 표현: 추가 sub-iteration 1개의 검사 비용만으로 iteration 내부 종료 가능)

### 의사코드 요지 (PDF 추출이 흐트러져 문맥으로 재구성)

```
초기화: check_all_zero <- 1 ; C_1..C_M <- 0
for k in 0 .. max_iteration-1:        # iteration
    for l in 0 .. M-1:                # 층 (sub-iteration)
        for j in 0 .. N-1:            # column block (block-serial)
            # 복호기가 block (l, j)를 처리해 column j의 posterior 부호 갱신
            for i in 1 .. M:          # 모든 층의 검사기에 병렬 공급
                delta_i <- permuter(d_diff_ij, sign(posterior_j))
                C_i <- XOR(C_i, delta_i)
        check_all_zero <- OR(C_1, ..., C_M)   # 층 처리가 끝날 때마다 확인
        if check_all_zero == 0: 조기 종료
```

- ㉮ 레지스터 리셋 시점(새 검사 창을 언제 여는지)과 zero block(해당 층에 circulant가 없는 column)의 건너뛰기 처리는 본문 텍스트만으로 확정되지 않는다 (원문 확인 필요, Fig 4, 5, 7이 그림이라 추출 텍스트에 없음)
- ㉯ 파라미터: 조정할 문턱값이 없다. 설계 선택은 검사 지점(층 경계)과 레지스터 구성뿐이다

### 무엇이 싸고 빠른가

- ㉮ H와 경판정이 모두 이진이므로 행렬 곱 H v^T가 XOR 누적으로 환원되고, block-serial 구조상 cycle마다 입력이 circulant 하나뿐이라 층마다 XOR 레지스터 쌍 하나로 충분하다
- ㉯ HDA처럼 직전 iteration 판정 비트 n개(논문 코드 기준 9280bit)를 저장할 메모리가 필요 없다
- ㉰ iteration 경계 종료 기법 [8][9]과 달리 sub-iteration 경계에서 멈추므로, 수렴 직후의 잔여 sub-iteration 연산을 아낀다

## 3. 보고된 이득 (수치와 측정 조건 그대로)

- ㉮ 코드와 복호기: (M, N, b) = (6, 58, 160), n = 9280 bit, rate 0.896, 최대 8 iteration, iteration당 6 sub-iteration, layered min-sum, 고정소수점 폭은 posterior 8bit, prior 7bit, extrinsic 6bit
- ㉯ 기능 검증: Xilinx ML605 에뮬레이션. coded BER 곡선(Fig 8)은 점마다 미정정 codeword 100개 수집, 거짓 종료 0건 (coded BER 열화 없음). 평균 sub-iteration 수(Fig 9)는 RBER(raw bit error rate, 정정 전 비트 오류율) 포인트당 codeword 1e8개
- ㉰ 처리량 (TSMC 90nm 합성, 200MHz, 비교 대상은 LC-ICA, low-complexity iteration control algorithm, 참고문헌 [9]):

| RBER | LC-ICA (Mb/s) | CB-ET (Mb/s) | 개선 |
|---|---|---|---|
| 6e-3 | 551 | 631 | 표기 1.4% (수치로 계산하면 14.5%, 원문 확인 필요) |
| 5e-3 | 751 | 917 | 21.8% |
| 4e-3 | 937 | 1211 | 29.5% |
| 3e-3 | 1123 | 1549 | 37.7% |

- ㉱ 면적: 730K gate에서 746K gate로 2.20% 증가 (검사 회로 약 16K gate), 동작 주파수 200MHz 유지
- ㉲ 37.7%와 2.2%의 조건: 비교 대상이 iteration 경계 종료 기법이라, 평균 수렴 iteration이 작은 저 RBER 구간일수록 iteration 내부 종료가 아끼는 몫의 비율이 커진다. 논문 스스로 저 RBER일수록 개선이 커진다고 보고하며, 이는 NVM의 수명 초반 조건과 맞는다

## 4. HBF/HD 적용 방법

### C++ 디코더(0_LDPC_original/src/decoder.cpp)와의 대응

이 코드베이스는 syndrome-aided 구조라서 CB-ET가 세려는 상태가 이미 레지스터에 있다:

- ㉮ Syndrome 레지스터는 read bit 기준 신드롬(H x read_bit)으로 고정된다 (iteration 0에서 계산)
- ㉯ check sum(Check_REG의 IDX_CHECK_SUM)은 column 처리마다 V2C 부호의 옛 기여 제거와 새 기여 반영으로 갱신된다 (CNU_Remove_Old_Sgn, CNU_Update_New_Sgn)
- ㉰ 따라서 임의의 column 경계에서 Syndrome XOR check_sum = H x (현재 판정 비트)다. CB-ET 판정은 이 값이 전 행에서 0인지 보는 검사로 환원되고, 논문의 permuter와 누적 레지스터 M벌은 이미 있는 상태로 대체된다. CSW(check sum weight, 패리티 검사 위반 수)가 0에 닿는 순간을 보는 것과 같다

적용 지점:

- ㉮ 검사 시점: V2C_Store가 끝나는 col_P4 경계마다. 파이프라인(col_M1에서 col_P4)에 아직 든 column의 기여는 직전 값 그대로라, 논문의 최근 일순 창과 같은 의미의 rolling 판정이 된다
- ㉯ 정지 경로: 기존 PCRC(partial cyclic redundancy check, 부분 CRC) 정지 배관을 재사용한다. stop_by_partial_crc에 새 stop 타입을 추가하면 decoder.cpp L1731-1806의 파이프라인 배수(Clk_Inc 진행과 V2C_Store skip 호출 뒤 break) 경로를 그대로 탄다
- ㉰ HBF(Hybrid Bit Flipping, 경판정 입력에서 처음 ITER_MAX_HBF(4)회를 1bit 정밀도로 돌리는 구조) 구간: BF iteration도 같은 check_sum 갱신 경로를 쓰므로 동일 검사가 그대로 적용된다. 현재 PCRC는 mn == 1(BF 미진입 시 ITER_MAX_HBF + 1)에서 마지막 termination point에서만 정지할 수 있으므로(Cal_PCRC L2190-2197), BF 1-4회 구간 내부의 열 단위 종료는 CB-ET가 새로 여는 영역이다
- ㉱ CRC와의 결합: CB-ET 발화 시 즉시 출력하지 않고 그 시점 판정 비트로 CRC를 확인한 뒤 종료하면 miscorrection(틀린 valid codeword 수락)을 차단한다. 또는 CB-ET는 연산 정지(전력 절감)만 맡기고 정합 확인은 기존 CRC 경로에 남긴다

### 기존 PCRC(4 지점 종료)와의 겹침 판별

- ㉮ PCRC는 이미 iteration 내부 4개 지점(idxTermination[0-3])에서 정지하므로, CB-ET의 순증 이득은 다음 세 가지로 좁혀진다:
  - ㉠ 지점 간격의 세분화: 열 단위 정지로, 평균 추가 절감의 상한은 지점 간격의 절반 (4지점 균등 배치 가정 시 iteration의 약 1/8)
  - ㉡ 정지 제약 해제: mn == 1과 BF 구간에서 PCRC가 막아둔 중간 정지를 연다
  - ㉢ 적용 범위 확장: PCRC 지점은 정보 column 구간(jj < N_b - M_b)에만 있으므로, 패리티 column 처리 중의 정지가 추가된다
- ㉯ 역방향 겹침: PCRC는 정보 비트의 CRC만 보므로 패리티 비트가 수렴하기 전에 먼저 정지하는 프레임이 있을 수 있고, 그 프레임에서는 CB-ET(전체 codeword 유효성)가 더 늦다. 두 기준의 발화 시점 차이는 스크리닝에서 프레임별로 직접 잰다
- ㉰ 하드웨어 유의점: RTL에서 check sum 상태가 레지스터가 아니라 SRAM에 있으면 전 행 OR 검사가 cycle마다 공짜가 아니다. 대안은 CSW 카운터를 column 처리마다 증분 갱신(그 열이 건드린 행만 delta 반영)하고 카운터 == 0에서 정지하는 구성이다. 비용 판정은 외부 검증 항목

### layered min-sum 전제의 강도 (1bit HBF 적용 가능성)

- ㉮ 논문은 행 layered 복호를 전제하지만, 알고리즘이 실제로 요구하는 것은 두 가지뿐이다:
  - ㉠ 판정 비트 부호가 column block 직렬로 갱신되어 흘러나올 것
  - ㉡ QC 구조 (shift 정렬이 permuter로 닫힘)
- ㉯ 이 코드베이스의 column block 직렬 처리와 syndrome-aided 구조는 두 조건을 충족하고, running 패리티 상태를 이미 유지하므로 전제가 논문보다 약해도 된다. 1bit HBF 단계도 min-sum 단계와 같은 check_sum 경로를 쓰므로 그대로 적용된다

### Python 스크리닝(2_LDPC_base/src/decoder.py BaseDecoder) 배치

- ㉮ 종료 로직 변경은 교체용 함수 6개에 해당하지 않으므로, 새논문적용규칙 2절 3항에 따라 `_run_iteration`을 재정의한다
- ㉯ column 루프에서 `_process_column` 호출 뒤 `(state.check_sum ^ state.syndrome)` 합(running CSW)이 0에 처음 닿는 (iteration, column) 좌표를 프레임별로 기록한다
- ㉰ 기본은 그림자 측정이다: 실제 종료 판정(`_check_errors`의 genie 판정)은 base와 동일하게 두고 좌표만 기록하면 FER(frame error rate, 프레임 오류율)이 정의상 불변이고, 한 실행에서 여러 종료 기준을 동시에 비교할 수 있다

## 5. 예상 이득과 위험

예상 이득:

- ㉮ 평가 영역(약 37000bit codeword, 프레임당 에러 0-150bit)은 대부분의 프레임이 적은 iteration에 수렴하는 영역이고, 논문도 저 RBER일수록 개선이 커진다고 보고한다 (3e-3에서 37.7%). 전력 감축 목표와 방향이 일치한다
- ㉯ BF 1-4회 구간 내부 종료가 열리면 저에러 프레임이 BF 안에서 조기 탈출해, min-sum 전환 전의 소모를 줄인다
- ㉰ 구현 비용이 매우 낮다. 시뮬레이터에서는 기존 상태의 비교 한 줄이고, 하드웨어에서도 논문 방식(permuter M벌)보다 싼 경로(기존 레지스터 재사용 또는 증분 카운터)가 있다

위험과 간극:

- ㉮ 성능 열화 가능성: syndrome == 0은 틀린 valid codeword도 통과시킨다. 논문은 1e8 프레임에서 거짓 종료 0건이지만 code와 에러 영역이 다르므로 거짓 정지율을 직접 측정해야 하고, CRC 확인과 결합하면 원천 차단된다
- ㉯ PCRC 4지점 내부 정지가 이미 있어 순증 이득이 제한될 수 있다. 상한이 대략 iteration의 1/8 수준 세분화와 BF 구간 해제분이면, 이득이 작게 나올 가능성을 열어 두어야 한다
- ㉰ 150bit 상단 간극: 에러가 많은 프레임은 수렴 iteration이 늘어 마지막 iteration의 부분 절감 비중이 작아지고, 미수렴 프레임에는 이득이 없다. 이득은 저에러 쪽에 몰린다
- ㉱ 파이프라인 중간 정지의 clk 모델(overall_clk 보정)이 기존 PCRC 정지와 같은 정확도인지 외부 검증이 필요하다

검증 포인트:

- ㉮ 거짓 정지율 0 확인 (genie 기준)
- ㉯ PCRC 모사 기준 대비 CB-ET의 평균 종료 시점 앞당김 폭
- ㉰ 그림자 측정에서 FER 완전 일치 (측정 코드가 판정에 개입하지 않음을 보증)

## 6. 실험 설계 초안

1단계, 그림자 측정 (FER 불변):

- ㉮ 구현: BaseDecoder 상속, `_run_iteration` 재정의. column마다 running CSW를 확인해 프레임별 처음 0 도달 좌표 (iteration, column)를 저장한다. 실제 종료는 base와 동일
- ㉯ 같은 실행에서 종료 기준 3개를 동시 산출해 비교한다:
  - ㉠ iteration 경계 종료 (CSW == 0을 iteration 끝에서만 확인, 논문의 비교 대상 [9] 대응)
  - ㉡ PCRC 모사: 4개 고정 지점에서만 확인. CRC 통과를 genie 정보 비트 오류 0으로 근사한다 (CRC 충돌 확률 무시)
  - ㉢ CB-ET: 열마다 확인
- ㉰ 산출 지표 (지표 계획 표에 올릴 후보):
  - ㉠ FER (불변 확인)
  - ㉡ 프레임당 평균 처리 column block 수 (연산 수 대리 지표), 기준 3개의 절감률
  - ㉢ 평균 iteration 환산값 (avg_iter와 log_active 분모 활용)
  - ㉣ 거짓 정지율: running CSW == 0이면서 genie 정보 비트 오류 > 0인 좌표 수
  - ㉤ 프레임 에러 수 구간별(0-50, 50-100, 100-150bit) 절감 분해
- ㉱ 입력 모드: HD(1bit BF 유사 구간 포함)와 2SD, 3SD 각각. 평가 대상 파라미터로 수행하고 파일은 이름과 치수로만 가리킨다

2단계 (1단계에서 이득이 확인되면):

- ㉮ 실제 열 단위 종료를 구현해 base_run과 같은 seed, 채널, 포인트로 FER과 평균 iteration을 비교한다
- ㉯ CRC 확인 결합안(발화 후 확인 뒤 종료)의 추가 지연을 같은 틀에서 잰다

## 7. 미해결 질문

원문 확인 필요:

- ㉮ 표 1의 RBER 6e-3 개선률 표기 1.4% (처리량 수치 551과 631로 계산하면 14.5%, 추출 손상 가능성)
- ㉯ 누적 레지스터의 리셋 시점과 검사 창 구성, zero block 건너뛰기 처리 (Fig 4, 5, 7이 그림이라 텍스트에 없음)
- ㉰ permuter가 층마다 전용인지 공유인지, b = 160bit 시프터 M개의 실제 구성과 16K gate의 내역
- ㉱ 비교 대상 LC-ICA [9]의 판정 세부 (iteration 경계 종료라는 점 외)

코드베이스 확인 필요:

- ㉮ 평가 대상 레이아웃(z = 256급)의 column block 수와 PCRC 지점 배치 (지점 간격이 넓을수록 CB-ET 세분화 이득이 커진다)
- ㉯ HD 모드에서 Cal_PCRC_Last_Only(단일 지점 변형)가 쓰이는 설정 조건과 적용 범위 (이 설정이면 iteration당 정지 기회가 1회로 줄어 CB-ET의 순증 이득이 커진다)
- ㉰ mn == 1에서 마지막 termination point만 허용하는 제약의 근거 (RTL 타이밍 제약인지 알고리즘 제약인지), CB-ET에도 같은 제약이 필요한지
- ㉱ flip 수 기반 Power stopping 경로(Jump_Iter, Check_Power_Stopping_Cond)와 CB-ET 정지 신호의 우선순위 정리
- ㉲ RTL에서 check sum 상태의 저장 형태 (레지스터면 OR 트리로 충분, SRAM이면 증분 CSW 카운터 구성 필요)

## 8. 등록 권고

중. 판정 로직이 이 코드베이스의 기존 syndrome-aided 상태(Syndrome XOR check_sum)로 거의 그대로 구현되어 스크리닝 비용이 낮고, 저에러 영역일수록 이득이 커지는 논문의 경향이 전력 감축 목표와 일치한다. 다만 PCRC 4지점의 iteration 내부 정지가 이미 있어 순증 이득이 지점 세분화, BF 구간 제약 해제, 패리티 구간 확장분으로 제한되므로, 그림자 측정으로 이득 크기를 먼저 확인한 뒤 본 등록을 정하는 것이 알맞다.
