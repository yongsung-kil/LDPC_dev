# 알고리즘 노트 C: 디코딩 실패에서 trapping set 식별 (논문 본문 정독)

> 출처 본문 (형제 저장소 `../LDPC_Paper_Analysis/data/pdfs/` 기준): Kang = `ieee/2011/01/ieee_5605921.txt`, Han 2022 = `ieee/2022/05/ieee_9729722.txt`, Han-Ryan = `ieee/2009/06/ieee_5089505.txt`, Zhang = `ieee/2009/11/ieee_5336848.txt`. 모두 `grep -a` 필요 (binary 판정됨).
> 식은 평문. "미확인"은 본문에서 못 찾은 것. "추정"은 논문에 없는 해석.

## 절 1. Kang 2011 (IEEE Trans. Commun. 59(1))

### 1-1. 기호
- K_max: 최대 반복 수 (원 디코딩과 재디코딩 모두 같은 값을 가정한 복잡도 식. 재디코딩만 K_max^(1) <= K_max 로 줄일 수 있다고 적음)
- C0: 반복 1..K_max 전체에서 불만족 검사 노드(CN, check node) 수가 가장 적은 반복의 불만족 CN 집합. "smallest set of unsatisfied CNs of all iterations up to K_max"
- u0: C0에 대응하는 디코더 상태. i번째 상태 = i번째 반복 끝의 hard decision 워드
- tau: 임계값. |C0| <= tau 이면 "작은 trapping set (T0; C0)에 빠졌다"고 선언. T0 = u0 안의 틀린 비트 집합(미지수)
- N(C0): C0의 CN에 이웃한 변수 노드(VN) 집합. T0 와 N(C0)의 교집합 원소를 boundary node(BN)라 부름
- eta: 가능한 최대 양의 LLR 값. chi(0)=+1, chi(1)=-1 (BPSK). y = x + noise, y_LLR = 입력 LLR
- 첨자: u_i, C_i = i번째 trial 실패 시 상태와 불만족 CN 집합. lambda_i = <y, chi(u_i)> (수신 실수 벡터 y와 chi(u_i)의 내적), Gamma = {i : u_i != u0}, gamma = 두 번째 backtracking 후보 수

### 1-2. 저장하는 상태
- 원 디코딩에서 최소 불만족 반복의 hard decision u0 와 그 불만족 CN 집합 C0 (메모리에 저장). LLR 메시지 전체는 저장하지 않음 (미저장으로 읽힘, 명시 문장은 없음)
- 재디코딩은 항상 원래 채널 입력 y_LLR 에서 시작 (매 trial마다 y'_LLR <- y_LLR 로 복사 후 한 VN만 수정). 즉 메시지 상태를 이어받지 않고 처음부터 다시 디코딩
- 2차 backtracking용으로 trial별 u_i, C_i 와 lambda_i

### 1-3. 절차 (Table I, II 줄 단위)
첫 번째 backtracking (Table I):
```
초기화: y_LLR, eta, C0, N(C0), u0 (원 디코딩 결과)
for each v in N(C0):
    y'_LLR <- y_LLR
    y'_LLR[v] <- -chi(u0[v]) * eta
    y'_LLR 를 입력으로 재디코딩 (최대 K_max^(1) 반복)
    if 재디코딩 성공: 종료
end
```
- 후보 선택 순서: N(C0) 전체를 순서 제한 없이 하나씩 (순서 규정 미확인). 한 번에 VN 하나만 수정
- LLR 변경: 그 VN의 입력 LLR을 "u0의 비트값 chi(u0_v)와 반대 극성, 크기 eta(최대값)"로 설정. 나머지 입력은 원래 y_LLR
- 성공 판정: 불만족 CN 수가 0 (Table II: |C_i| = 0 이면 u_i 를 코드워드로 출력)
- 재디코딩 반복 수: K_max^(1) <= K_max. 구체 값은 미확인(복잡도 식에서는 K_max로 가정)
- 한 trial이 실패해도 u0 는 유지하고 다음 v로 진행

Double-backtracking (Table II):
```
초기화: y, y_LLR, eta, C0, N(C0), u0
(첫 번째)
i <- 0; Gamma <- 공집합
for each v in N(C0):
    i <- i+1
    y'_LLR <- y_LLR; y'_LLR[v] <- -chi(u0[v]) * eta
    재디코딩 -> u_i, C_i
    if |C_i| = 0: u_i 를 출력하고 종료
    else if u_i != u0: lambda_i <- <y, chi(u_i)>; i 를 Gamma 에 삽입
end
{lambda_i} (i in Gamma) 중 가장 큰 gamma 개를 골라 해당 u*_l, C*_l (l=1..gamma)
(두 번째)
for l = 1..gamma:
    for each v in N(C*_l):
        y'_LLR <- y_LLR; y'_LLR[v] <- -chi(u*_l[v]) * eta
        재디코딩; 성공이면 종료
```
- 두 번째 backtracking 조건: 첫 번째 backtracking의 trial이 모두 실패했을 때. 두 번째의 y'_LLR 는 첫 번째 flip을 유지하지 않고 원래 y_LLR 에서 새로 한 VN만 수정 (표의 y'_LLR <- y_LLR). 따라서 두 번째에서도 한 번에 VN 하나만 뒤집음
- hit-trial 선택 근거: u_i != u0 인 trial만 후보. 최대 우도(ML) 의미로 lambda_i 가 최대인 것이 hit-trial일 가능성이 가장 높음
- hit-trial 실패 시 trapping set은 원래의 부분집합, miss-trial 실패 시 같거나 상위집합이 된다는 관찰이 근거 (논문 주장, VN만 비교)
- lambda_i 계산: u_i 와 u0 는 보통 1-2비트만 다르므로 다른 비트에 해당하는 y 성분의 가중합만 계산 가능

### 1-4. 매개변수와 실험 수치
- tau 선택 근거: 오류 블록 500개를 모아 |C0| 히스토그램을 그려 대부분을 덮도록 정함
  - 예 1 (1890,1512) 규칙 (3,15) QC-LDPC, 4.6 dB: 오류 블록의 98%가 |C0| <= 2, 최대 관측 9와 10. tau=4 와 tau=10 비교. gamma=3
  - 예 2 (1056,528) WiMAX 불규칙 부호, 3.4 dB: tau=6 이 오류 블록의 99%를 덮음. tau=10 도 비교. gamma=3
- 디코더: 6비트 고정소수점 scaled min-sum (scaling factor 0.75, 최대 50 반복). WiMAX는 3.3 양자화, scaling 0.815
- 효과: 예 1은 tau=4 에서 첫 backtracking이 error floor를 약 2 자릿수 낮춤, 두 번째는 tau=4 에서 추가 개선이 작고 tau=10 에서 1 자릿수 더 낮춤. 예 2는 첫 backtracking이 1 자릿수 이상, 두 번째까지 합쳐 2 자릿수 개선, tau 6->10 은 미미
- 복잡도 상한: K_bt,ave <= K_ave + P_B (M1 + M2) K_max, M1 = |N(C0)|, M2 = sum over l of |N(C*_l)|. 근사 K_ave + P_B * tau * (1+gamma) * d_c * K_max. P_B = 블록오류율. 예 1에서 4 dB 의 P_B(M1+M2) 약 1e-3
- 예 5 (4000,3200) PEG 부호: 중요 trapping set이 모두 홀수 차수 CN 6개라 두 번째 backtracking 불필요, 첫 backtracking만으로 4 자릿수 이상 개선

### 1-5. 한계 (논문 언급)
- 낮은 SNR에서는 |C0| 가 커져 tau 를 키우지 않으면 성능 저하, P_B 가 크면 계산 비용 증가. 높은 SNR(error floor 영역)에서 효율적
- 첫 backtracking은 모든 오류를 못 고침: 홀수 차수 CN이 많은 trapping set과 absorbing 구조의 부분집합에서 재실패 가능 (그래서 두 번째가 존재)
- backtracking 하면 undetected error(잘못된 코드워드 수렴)가 원 디코딩보다 약간 증가 (trapping set 밖 비트를 뒤집어 엉뚱한 코드워드로 수렴할 수 있음)

## 절 2. Han 2022 (IEEE Trans. Commun. 70(5)) 정의

기호: Imax = 최대 반복, C_rho = rho번째 반복의 불만족 CN 집합, b = |C_U|, mu = |lambda| (LLR 크기, LM).

1. Definition 1 (TS): rho_min = argmin over rho in {1,...,Imax} of |C_rho|. 동률이면 가장 작은 rho. TS = rho_min 번째 반복의 오류 VN 집합. rho_min 을 "trapped iteration"이라 부름. (a,b) TS = a개 VN이 b개의 불만족 CN과 임의 개수의 mis-satisfied CN을 유도하는 부분그래프. 논문은 b < tau 인 TS를 대상, a는 미지수, b는 관측값
2. Definition 2: C_U = C_{rho_min}
3. mis-satisfied CN: TS 안에서 패리티는 만족되나 오류 VN이 연결된 CN (오류 VN에 이웃함, 그 VN을 현재 값으로 강화)
4. Definition 3 (길이 l의 error path): C_U 안의 두 불만족 CN 사이 경로로, 오류 VN과 (l-1)개의 mis-satisfied CN으로만 구성. P = {v_k1, ..., v_kl} 순서 집합, v_kj 와 v_k(j+1) 은 공통 mis-satisfied CN에 이웃, v_k1 과 v_kl 은 각각 시작과 끝 불만족 CN에 이웃. 길이 = VN 개수 (예: P1 = {v5,v9,v11,v12,v8} 길이 5)
5. Definition 4: shallow VN = 불만족 CN에 인접한 VN, 나머지 = deep VN. shallow 오류 VN은 만족 CN과 불만족 CN에서 상충 메시지를 받고, deep 오류 VN은 mis-satisfied CN만 이웃하여 일관된 메시지를 받음
6. b = 1 (|C_U| = 1) 이면 그 CN에서 나가 자기 자신으로 돌아오는 경로로 수정: 길이 1, 이웃 VN 하나씩 (Nv(c_u1) 각 원소가 후보)
7. 가정: TS가 유도하는 부분그래프는 연결. 비연결이면 연결 성분 각각에 반복 적용
8. 열거 절차 (Algorithm 1, NEP 검출기. AEP는 가지치기 버전):
   - b > 1: 각 c in {c_u1, ..., c_u(b-1)} 를 뿌리로 깊이 d = 2*l_max 인 트리 생성 (CN 뿌리, 한 단계 VN, 다음 CN 순으로 교대). 처리한 뿌리는 C_U 에서 제거(`C_U := C_U \ {c}`)하여 같은 쌍을 중복 열거하지 않음. 트리 안 C_U 의 CN c' 로 가는 경로 P 를 Omega 에 저장 (논문 본문: 다른 불만족 CN을 가로지르지 않는 경로만)
   - 경로 길이는 l_max 이하. l_max = 트리의 VN 수가 부호 길이 n 보다 커지는 최소 정수 ((d_c-1)(d_v-1))^(l_max-1) > n. 예: (2640,1320) l_max=5, 불규칙 (648) l_max=3. 이 선택은 길이 제한이자 BFS 깊이 제한
   - 경로 점수화: NEP는 DNN(은닉층 3, 뉴런 30) 점수 phi_k 상위 M 개. AEP는 경로의 LM 최댓값(MLM) 이 작을수록 error path일 확률이 높다는 관찰로 MLM 최소 M 개 큐 유지. ordered AEP는 뿌리의 shallow VN을 LM 오름차순으로 탐색하고 VN의 LM이 큐의 M번째 MLM 이하일 때만 확장 (가지치기)
9. 재디코딩: y_k,i = -sign(lambda_i) * eta (v_i in P_k), 그 외는 y_i. sign(x)=1 (x>=0), -1 (그 외). 경로의 모든 VN을 한꺼번에 뒤집음(Kang은 1개씩). Rmax 반복, 성공하면 종료, 점수순으로 시도, 전부 실패하면 실패 선언
10. 입력 특징 (NEP): 경로 위 VN들의 LM 벡터 mu_k = (mu_k1, ..., mu_kl). 길이가 n_b(=l_max) 보다 짧으면 평균 mu_bar 를 가운데에 끼워 길이 n_b 로 맞춤: xi_k = [mu_k1..mu_k(l/2), mu_bar x (n_b-l), mu_k(l/2+1)..mu_kl]. 그 외 입력 특징 없음 (메시지 통계 미사용). 사용 상태 = trapped iteration 의 a posteriori LLR lambda 와 bit decision u~
11. 수치: scaled MSA alpha=0.75, Imax=50, Rmax=20, 양자화 -7.5..7.5 (eta=7.5), 간격 0.5, tau=10 (모든 부호), M=5. tau=10 일 때 평균 경로 658개 중 M=5 후보에 error path 1개 이상 포함 확률 94% 이상 (NEP). 가정: 전송 코드워드 전부 0. 정의는 DNN과 무관하게 직접 구현 가능

## 절 3. Han, Ryan 2009 (IEEE Trans. Commun. 57(6))

1. 실패 유형 3종:
   - (1) unstable error events: 반복마다 동적으로 변함, w와 v가 큼
   - (2) stable trapping sets: 고정, w와 v가 작음, error floor의 주원인
   - (3) oscillating trapping sets: 반복 수에 따라 주기적으로 변함 (Margulis 부호에서 주기 2의 (6,18) 쌍 또는 (7,21) 쌍, 그 합집합이 (12,4)와 (14,4) trapping set). 때로 stable의 부분집합
   - (w,v) = (VN 수, 불만족 CN 수 = syndrome 가중치). 판별 임계 반복 수는 미확인 ("충분한 반복" 후 도달)
   - 두 번째 모드(후처리) 활성화 조건: 오류 사건의 syndrome 가중치가 목표 trapping set들의 syndrome 가중치 집합에 속할 때 (QC 부호는 5 또는 7, Margulis는 4)
2. 트리 확장 절차:
   - 뿌리 = 모든 불만족 CN (v개의 트리). 불만족 CN의 d_c 이웃 VN 전부를 erasure로 표시 (오류 비트의 LLR 크기가 최소라는 보장이 없어서)
   - 깊이: 부호 구조에 의존. w <= v (모든 VN이 불만족 CN에 인접) 이면 트리 2단계(VN 한 층)로 충분 (QC (5,5), (5,7): 각각 34개, 54개 erasure). 아니면 더 깊이 (Margulis는 4단계 트리). 너무 키우면 stopping set(BEC 위 trapping set) 때문에 erasure 복호가 막히므로 제한
   - Margulis (12,4)/(14,4) 보조 Algorithm 1: ① 불만족 CN 4개로 4단계 트리 4개 ② 2단계(레벨 2) VN 전부 erase, 플래그 "A" ③ 4단계 VN 전부 erase, 플래그 "B" ④ 레벨 3의 각 CN에서 플래그 A VN 개수 세기, A인 이웃이 2개인 CN c_a 를 처음 찾으면 중단, 그 VN을 va1, va2 ⑤ va1, va2 의 비트를 뒤집고 syndrome 재계산, 새 불만족 CN 4개 ⑥ 새 syndrome 으로 ①-③ 반복 (기존 erasure에 추가), ⑦ A와 B 플래그 VN 전체에 대해 반복적 erasure 복호를 모든 erasure가 해소될 때까지
   - 겹침 판정: 레벨 2의 두 VN이 레벨 3의 공통 CN을 공유하는 쌍을 찾는 것이 (12,4)와 (14,4)의 구별. (12,4)에서 뒤집은 쌍은 사실 맞는 비트이나 그대로 뒤집어도 (14,4)가 되어 올바르게 복원됨
   - 변형: erasure 외 비트는 유지하고 erasure LLR을 0으로 설정 후 일반 반복 복호(partial-soft-erasing). 불만족 CN 하나씩 그 이웃의 LLR을 0으로 하고 복호, 실패하면 초기화 후 다음 불만족 CN (10GBASE-T (8,8) trapping set에 평균 약 20 추가 반복)
3. 가정과 한계:
   - elementary trapping set 가정: 유도 부분그래프의 CN이 차수 1 또는 2뿐, 불만족 CN은 보통 한 번만 연결 (불만족 CN당 오류 비트 1개). 단 "적용이 이에 한정되지는 않는다"고만 주장
   - 부호별로 트리 깊이와 보조 단계를 직접 설계해야 함 (Margulis 전용 단계 존재). 부호를 아는 목표 trapping set의 syndrome 가중치 집합 필요
   - 비구조 부호는 trapping set 종류가 다양해 덜 적용되기 쉬움 (논문 언급)

## 절 4. Zhang 외 2009 (IEEE Trans. Wireless Commun. 8(11))

1. 고정형/진동형 판정: 일관된 정량 기준 미확인. 실험은 모든 0 코드워드 전송, sum-product 로 200 반복, 수렴 실패 시 마지막 16 반복을 기록. "수렴 실패이며 마지막 반복들에서 모든 비트의 hard decision 이 동일하게 유지"되면 absorbing set 오류(고정형)로 분류. 진동형은 오류 비트 수가 반복마다 커졌다 작아지는 경우 (설명: 소수의 오류 비트가 불만족 CN을 통해 오류를 퍼뜨려 약 2단계 후 불만족 CN이 충분히 많아져 다시 줄어듦). 진동형 판정 수식은 미확인
2. absorbing set 판정 (V는 VN 집합, F는 CN 집합, D는 V의 부분집합): O(D) = D의 이웃 CN 중 D와 연결 수가 홀수인 CN 집합. (a,b) absorbing set = |D| = a, |O(D)| = b, 그리고 D의 모든 VN v 에 대해 |이웃 CN 중 O(D) 에 속하는 수| < |이웃 CN 중 F\O(D) 에 속하는 수| (불만족 이웃 수가 만족 이웃 수보다 엄격히 작음). fully absorbing set 은 D 밖 모든 VN에도 같은 부등식이 성립
3. (a,b) 산출: 논문은 실패 trace에서 (a,b)를 산출하는 절차를 별도로 적지 않음 (미확인). 위 정의에 맞춰 최종 hard decision 오류 비트 집합을 D로 놓고 계산하면 됨 (추정). trapping set 은 [32,33] 에서 길이 n 비트 벡터 (a = 해밍 가중치, b = 불만족 CN 수) 로 정의했다고 서술
4. 부가: weak/strong absorbing set 구분이 있음 (weak 는 최적 디코더 구현으로 제거 가능). 원인 분석은 양자화(Q3.2 의 LLR 범위 [-4, 3.75] 클리핑)와 연관

## 절 5. 네 논문 정의의 차이

- trapping set의 관측 시점: Kang 은 K_max 반복 전체 중 |C(k)|가 최소인 반복의 상태 u0 (동률 규칙 미확인). Han 2022 는 같은 방식이되 동률이면 가장 작은 rho 로 명시. Han-Ryan 은 "충분한 반복 후" 도달한 상태의 syndrome 가중치. Zhang 은 마지막 16 반복의 hard decision 이 고정되는지를 봄 (최종 상태 기준). 구현 시 u0 를 최종 반복이 아닌 최소 불만족 반복에서 저장해야 함 (Kang, Han 2022)
- 대상: Kang 은 |C0| <= tau (tau 4-10), Han 2022 는 b < tau 로 tau=10 고정, Han-Ryan 은 목표 trapping set의 정확한 syndrome 가중치 집합, Zhang 은 비교 부등식 기준
- 오류 VN 후보: Kang 은 N(C0) 전체를 하나씩 뒤집음, Han 2022 는 불만족 CN 쌍 사이 error path 를 점수화해 M=5 개를 경로 단위로 뒤집음, Han-Ryan 은 트리로 이웃 VN을 전부 erasure(LLR 0)로 두고 erasure 복호, Zhang 은 후보 선정을 하지 않음 (분석용)
- 조작: Kang 과 Han 2022 는 LLR 를 -sign * eta (최대 신뢰도 반대 극성), Han-Ryan 은 LLR 0 (지움), 두 번째 모드에서 비트 flip 후 syndrome 재계산도 사용
- 용어: Kang 은 absorbing set을 "각 VN의 CN 중 다수가 짝수 차수"로 느슨히 설명, Zhang 은 위 부등식으로 엄밀 정의. Zhang 은 absorbing set을 디코더 독립 조합 객체로, Richardson 의 trapping set은 디코더 의존으로 구별. Han 2022 의 TS 는 디코더 의존(반복 rho_min), Kang 은 (T0; C0) 로 표기
- 실패 유형: Kang 은 false convergence(고정)와 oscillation, Han-Ryan 은 unstable 포함 3종, Zhang 은 oscillatory 와 absorbing set 수렴 두 종, 기준 수치는 어느 논문도 명시하지 않음

## 절 6. Python 구현 시 주의점

논문에서 직접 언급:
- 재디코딩은 항상 원래 채널 LLR y_LLR 로 시작하고 trial마다 한 VN(Kang) 또는 경로 VN 전체(Han 2022)만 바꿈. 매 trial 전에 y_LLR 복사본을 새로 만들 것
- 뒤집을 값은 원 y_LLR 부호가 아니라 저장해 둔 u0(Kang) 또는 trapped iteration의 a posteriori LLR lambda(Han 2022)의 부호의 반대. 크기는 양자화 최대 eta (Han 2022: 7.5)
- K_max 반복 동안 매 반복의 불만족 CN 수를 추적하고, 최솟값 반복(Han 2022는 동률 시 첫 번째)의 hard decision 과 불만족 CN 집합, (Han 2022는 LLR lambda 도) 저장
- 성공 = 불만족 CN 0. Kang 은 코드워드를 찾으면 즉시 종료, 한 trial이라도 성공 시 나머지 건너뜀
- 두 번째 backtracking 후보 선택은 u_i != u0 인 trial만 대상, lambda_i = <y, chi(u_i)> 의 상위 gamma 개 (u_i 와 u0 가 다른 비트만 계산해도 됨)
- 오류 경로 열거(Han 2022): 불만족 CN 뿌리에서 깊이 2*l_max 트리, 처리한 뿌리는 C_U 에서 제거해 쌍 중복 방지, b=1 이면 이웃 VN 하나씩
- 복잡도: 호출 수가 |N(C0)| 약 |C0| * d_c 이므로 P_B가 작을 때만 이득

추정 (논문에 없음):
- Kang 의 N(C0) 순서 규정은 없으므로 VN 색인 순서면 무방하다고 판단됨
- Zhang 의 fixed 대 oscillating 판정은 마지막 16 반복의 hard decision 변화 여부로 구현 가능
- (a,b) 계산은 오류 비트 집합 D(전송 코드워드를 아는 시뮬레이션에서) 에 대해 O(D) 와 만족/불만족 이웃 수를 세면 됨
- Python 속도를 위해 H 를 희소 인접 리스트(CN별, VN별)로 두고 트리 확장은 파이썬 집합 연산이나 scipy.sparse 로 하는 것이 합리적 (논문 언급 없음)

미확인 항목 요약: Kang 의 K_max^(1) 구체 값과 동률 규칙, Han-Ryan 의 "충분한 반복" 횟수와 안정/진동 판별 반복 수, Zhang 의 fixed/oscillating 정량 판정 및 (a,b) 산출 절차.
