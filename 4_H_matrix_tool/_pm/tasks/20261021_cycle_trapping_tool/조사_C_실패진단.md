# 보고서 C: 디코딩 실패 진단 논문 선별

용어: TS = trapping set(포획 집합). (a,b) TS는 a개 오류 변수 노드(VN)와 b개 불만족 검사 노드(CN)를 뜻합니다. FAID = finite alphabet iterative decoder(유한 알파벳 반복 디코더).

근거: 제목 목록 C(386편)와 B(592편)를 전수로 훑었습니다. 초록을 읽었고, 상위 후보는 본문 txt에서 식별 절차를 확인했습니다. 확인하지 못한 것은 "미확인"으로 적었습니다.

전체 경향: "실패 출력 하나를 받아 TS를 식별"하는 결정적 절차를 명시한 논문은 소수입니다. 대부분은 TS를 미리 알고 디코더를 설계하는 논문이거나, 실패 모음에서 지배 TS를 통계로 뽑는 논문입니다. 순위는 두 가지를 조합해 쓰도록 매겼습니다.

## 1. 추천 순위표

각 칸은 입력 / 출력 / 절차 한 줄 / 신뢰성 근거 / Python 메모 / 본문 유무 순서입니다.

1. **ieee:5605921 (2011), Kang, Huang. "An Iterative Decoding Algorithm with Backtracking to Lower the Error-Floors of LDPC Codes"**
   - 입력: H, 채널 LLR 입력, 반복별 불만족 CN 집합과 디코더 상태. 실패 샘플 1개면 충분하고 송신 codeword 없이도 동작합니다.
   - 출력: 최소 불만족 CN 집합 C0, 이웃 VN 후보 N(C0), 재디코딩이 성공하는 VN(TS 경계 노드).
   - 절차: 전 반복 중 불만족 CN 수가 최소인 반복의 상태 u0를 저장합니다. |C0|이 임계값 tau 이하이면 N(C0)의 각 VN 입력 LLR을 최대치로 뒤집어 재디코딩합니다.
   - 근거: IEEE Trans. Commun. 2011, Shu Lin 그룹입니다. 하드웨어판(ieee:5954141)과 ieee:9729722가 후속 또는 비교 대상으로 다룹니다.
   - 메모: 결정적이고 구현이 쉽습니다. 반복별 불만족 CN 수 추적만 추가하면 됩니다. N(C0)가 작아 n이 수만이어도 현실적입니다.
   - 본문: 있음.
2. **ieee:5089505 (2009), Han, Ryan. "Low-floor decoders for LDPC codes"**
   - 입력: H, 최종 hard decision, 불만족 CN 집합. 진단용으로는 송신 codeword를 추가합니다.
   - 출력: 불만족 CN을 뿌리로 한 flagging tree, 오류 VN 쌍 후보, TS 클래스(안정형, 진동형).
   - 절차: 신드롬 가중치로 TS 클래스를 조회합니다. 불만족 CN마다 4단계 트리를 확장해 VN에 표시하고, 표시가 겹치는 CN에서 두 VN을 뒤집은 뒤 신드롬을 다시 계산합니다.
   - 근거: IEEE Trans. Commun. 2009, William Ryan 그룹입니다. Kang 논문이 선행 비교 대상으로 인용합니다.
   - 메모: 결정적이고 트리 확장은 BFS입니다. 규칙이 Margulis (2640,1320)와 QC (640,192) 전용이라 일반화가 필요합니다.
   - 본문: 있음.
3. **ieee:9729722 (2022), Han, Oh. "Deep-Learning for Breaking the Trapping Sets in Low-Density Parity-Check Codes"**
   - 입력: H, 최종 hard decision, 불만족 CN 집합, 메시지 크기. DNN을 학습하려면 다수의 실패 샘플과 송신 codeword 라벨이 필요합니다.
   - 출력: 불만족 CN 쌍 사이의 error path와 오류 VN 판정.
   - 절차: TS를 "불만족 CN 수가 최소인 반복의 오류 VN 집합"으로 정의합니다. error path(오류 VN과 mis-satisfied CN으로만 이은 경로)를 정의하고, shallow/deep 오류 VN을 구분해 경로 위 VN의 오류 여부를 분류합니다.
   - 근거: IEEE 2022, Jeongseok Ha 그룹입니다. Kang 방식과 비교 평가했습니다.
   - 메모: 정의가 진단 도구에 가장 알맞습니다. 송신 codeword를 알면 DNN 없이 BFS로 error path를 열거할 수 있습니다.
   - 본문: 있음.
4. **ieee:5336848 (2009), Zhang, Dolecek. "Design of LDPC decoders for improved low error rate performance: quantization and algorithm choices"**
   - 입력: H, 반복별 hard decision 궤적(error trace), 송신 codeword.
   - 출력: 실패를 고정형과 진동형으로 분류하고, 오류 VN을 (a,b) absorbing set으로 분류.
   - 절차: 에뮬레이션으로 실패 trace를 수집합니다. 최종 오류 VN의 유도 부분 그래프를 absorbing set 조건(각 VN의 만족 CN이 불만족 CN보다 많음)으로 검사합니다.
   - 근거: IEEE Trans. Commun. 2009, Nikolic/Anantharam 그룹입니다. absorbing set 문헌에서 표준으로 인용됩니다.
   - 메모: 분류 기준이 명확해 이식이 쉽습니다. 식별은 서술형이고 pseudo-code는 없습니다.
   - 본문: 있음.
5. **ieee:1651870 (2005, Cavus, Daneshrad) 및 ieee:5165375 (2009, Cavus, Haymes). 제목: "A performance improvement and error floor avoidance technique for BP decoding" / "Low BER performance estimation of LDPC codes via application of importance sampling to trapping sets"**
   - 입력: H(사이클 목록), 디코더, 올 제로 codeword.
   - 출력: 지배 TS 목록.
   - 절차: 짧은 사이클의 VN을 편향해 디코딩합니다. 20 반복 뒤에도 남는 오류 VN을 TS로 기록하고, 행마다 반복합니다.
   - 근거: 2009년 판은 IEEE에 실렸습니다. Cole 논문이 TS 탐색 선행 연구로 인용합니다.
   - 메모: 사이클 기반 시드라 목표 2와 직결됩니다. 통계적 절차입니다.
   - 본문: 둘 다 있음.
6. **arxiv:cs/0605051v1 (2006), Cole, Wilson. "A General Method for Finding Low Error Rates of LDPC Codes"**
   - 입력: H, 디코더, 올 제로 codeword.
   - 출력: 지배 TS 목록, 오류 경계까지 거리, 중요도 샘플링 FER 추정.
   - 절차: 3단계입니다. 부분 그래프 탐색, 오류 경계 거리 측정, 중요도 샘플링 순입니다.
   - 근거: "Cole 방식"으로 후속 연구가 인용합니다(ieee:10113442 등).
   - 메모: n이 수만이면 1단계 탐색 비용이 큽니다. 논문도 Margulis에서 (14,4) TS를 전부 찾지는 못한다고 적었습니다. 통계적 절차입니다.
   - 본문: 있음. JSONL의 txt는 null이지만 `../LDPC_Paper_Analysis/data/pdfs/arxiv/2006/05/cs_0605051v1.txt`가 존재합니다.
7. **ieee:5174515 (2009), Chilappagari, Chertkov. "Instanton-based techniques for analysis and reduction of error floors of LDPC codes"**
   - 입력: H, 디코더(BP, Gallager, LP).
   - 출력: instanton(실패를 일으키는 최소 노이즈 구성)과 오류 VN 집합.
   - 절차: 임의의 노이즈에서 시작해 최소 노이즈 실패 구성으로 반복 수렴시킵니다.
   - 근거: IEEE JSAC 2009, Vasic/Chertkov 그룹입니다.
   - 메모: 디코더 내부를 반복 호출해야 합니다. min-sum 적용성은 미확인입니다.
   - 본문: 있음.
8. **ieee:4698365 (2008), Zhang, Dolecek. "Lowering LDPC Error Floors by Postprocessing"**
   - 입력: H, 알려진 absorbing set 목록, 실패 시 불만족 CN.
   - 출력: 실패가 알려진 absorbing set과 일치하는지 판정.
   - 절차: 알려진 (8,8) 구조와 비교한 뒤 선택 메시지를 편향합니다.
   - 근거: IEEE Globecom 2008.
   - 메모: 목록이 먼저 필요합니다(목표 2 산출물). 초록만 확인했고 상세 절차는 미확인입니다.
   - 본문: 있음.
9. **ieee:6259854 (2012), Karimi, Banihashemi. "Efficient Algorithm for Finding Dominant Trapping Sets of LDPC Codes"**
   - 학회판 ieee:5613902, 불규칙 부호판 ieee:6033699가 있습니다.
   - 입력: H만.
   - 출력: 부호의 지배 TS 목록.
   - 절차: 짧은 사이클에서 시작해 재귀 확장합니다.
   - 근거: IEEE Trans. Inf. Theory 2012, Banihashemi 그룹.
   - 메모: 부호 쪽 열거라 목표 2 성격이 강합니다. 진단 결과를 이 목록과 대조하는 용도로 씁니다.
   - 본문: 있음.
10. **ieee:6120280 (2011), Zhang, Schlegel. "Causes and dynamics of LDPC error floors on AWGN channels"**
    - 입력: 지배 TS 목록, 디코더.
    - 출력: TS별 오류 전파 선형 모델과 FER 기여 추정.
    - 근거: IEEE 2011, Schlegel 그룹.
    - 메모: TS별 기여도 순위용입니다. 세부는 미확인입니다.
    - 본문: 있음.
11. **ieee:9005250 (2020), Farsiabi, Banihashemi. "Error Floor Estimation of LDPC Decoders: A Code Independent Approach to Measuring the Harmfulness of Trapping Sets"**
    - 입력: TS 구조, 디코더 모델.
    - 출력: TS별 유해도.
    - 근거: IEEE 2020, Banihashemi 그룹.
    - 메모: 식별 결과의 유해도 순위화에 씁니다.
    - 본문: 있음.
12. **ieee:6965878 (2014), Sibel, Crussiere. "Analysis of Decoding Failures of DVB-S2 LDPC Codes"**
    - 입력: 실패 샘플, 반복 전후 비트, 송신 codeword.
    - 출력: persistent error(BP 전후 모두 오류)와 created error(BP가 새로 만든 오류) 구분, 노드 차수별 분석.
    - 근거: IEEE 2014 학회, 인지도는 낮습니다.
    - 메모: 가장 단순한 보조 지표입니다.
    - 본문: 있음.
13. **ieee:6004950 (2011), Tsatsaragkos, Kanistras. "A syndrome-based LDPC decoder with very low error floor"**
    - 입력: 반복별 신드롬.
    - 출력: 불만족 CN이 최소인 반복의 출력.
    - 절차: Kang의 C0 추적과 같은 착상입니다.
    - 메모: 구현은 한 줄 수준입니다.
    - 본문: 있음.
14. **ieee:4024284 (2006), Chilappagari, Sankaranarayanan. "Error Floors of LDPC Codes on the Binary Symmetric Channel"**
    - Gallager B에서 TS별 오류 확률을 반분석(semi-analytical)으로 계산합니다.
    - Vasic 그룹 논문이고 제목과 초록만 확인했습니다. min-sum이 아니라 Gallager B 중심입니다.
    - 본문: 미확인.
15. **ieee:1549481 (2005), Landner, Milenkovic. "Algorithmic and combinatorial analysis of trapping sets in structured LDPC codes"**
    - 입력은 H이고, 출력은 구조화 부호의 TS 매개변수입니다.
    - 초록상 부호 쪽 분석이며 실패 출력 입력 절차는 미확인입니다.
    - 본문: 있음.

보조(순위 외):
- ieee:5954141: backtracking 하드웨어판. Kang 구현 참고용입니다.
- ieee:6874922: ADMM 페널티 디코더의 instanton 탐색.
- arxiv:1108.5547v2: Stepanov, 반복 디코딩이 순환하는 instanton.
- ieee:9366194: 5G NR 부호의 elementary absorbing set 식별.

## 2. 1순위 3편 상세

### (1) Kang 등, backtracking (ieee:5605921)
- ㉮ 매 반복의 불만족 CN 집합과 디코더 상태를 보관합니다. Kmax 반복 중 크기가 최소인 C0와 그때의 상태 u0를 저장합니다.
- ㉯ |C0|이 tau 이하이면 "작은 TS에 갇힘"으로 판정합니다. TS T0는 u0의 오류 비트 집합이고 디코더는 이를 모릅니다.
- ㉰ 후보는 C0의 이웃 VN 집합 N(C0)입니다. 각 후보 v의 입력 LLR을 u0 극성 반대의 최대 크기로 바꿔 재디코딩합니다.
- ㉱ 성공하는 v가 T0의 경계 노드입니다. 한 번에 안 풀리면 double-backtracking(첫 뒤집기 뒤 실패 상태의 C를 다시 사용)을 씁니다.
- 주의: 시뮬레이션이면 T0 = (u0 XOR 송신 codeword)의 지지 집합으로 바로 얻어집니다. 이때 재디코딩은 검증용으로만 병행할 수 있습니다.
- 주의: tau는 부호마다 정해야 합니다. 불만족 CN 수 최소값의 히스토그램을 먼저 모으는 것이 첫 작업입니다.

### (2) Han, Ryan, bi-mode (ieee:5089505)
- ㉮ 실패 유형은 안정형 TS, 진동형 TS 등입니다. 신드롬 가중치가 목표 TS 집합의 값에 들 때만 후처리를 활성화합니다.
- ㉯ 불만족 CN마다 트리(CN, 이웃 VN, 그 VN의 다른 CN, ...)를 4단계까지 확장해 VN에 표시합니다.
- ㉰ 예: 불만족 CN이 4개이면 4단계 트리 4개를 만듭니다. 표시가 둘 이상 겹치는 CN을 찾으면 그 두 VN을 뒤집고 신드롬을 재계산합니다.
- ㉱ 불만족 CN 하나당 오류 이웃이 정확히 하나인 elementary TS를 가정합니다. 비 elementary는 일반화가 필요합니다.
- 주의: 트리가 너무 크면 stopping set이 되어 지우기 복호가 막히므로 단계 수를 제한해야 합니다. "신드롬 가중치에서 TS 클래스" 표는 실패 모음에서 직접 만들 수 있습니다.

### (3) Han 등, error path (ieee:9729722)
- ㉮ TS 정의: 불만족 CN 수가 최소인 반복 rho_min의 오류 VN 집합입니다. CU는 그 반복의 불만족 CN 집합입니다.
- ㉯ error path: CU의 두 CN 사이를 오류 VN과 mis-satisfied CN(짝수 개 오류 이웃 때문에 만족으로 보이는 CN)으로만 이은 경로입니다. 불만족 CN에 인접한 오류 VN은 shallow, 그 밖은 deep입니다.
- ㉰ 실패 샘플에서 error path를 열거하고 경로 위 VN의 오류 여부를 분류합니다. 논문은 LLR 크기와 메시지 통계를 입력으로 DNN을 씁니다.
- 주의: 분석 목적이면 학습이 필요 없습니다. 송신 codeword로 오류 VN을 정확히 알면 error path를 BFS로 열거할 수 있습니다.
- 주의: 논문 예시는 Margulis (12,4), (14,4) TS입니다. 고부호율 QC 부호에서의 동작은 미확인입니다.

## 3. 진단 도구 조합 절차 초안
1. 실패 샘플 수집: Imax 후 신드롬이 0이 아니면 반복별 (불만족 CN 집합, hard decision)을 기록합니다. 불만족 CN 수가 최소인 반복 rho_min을 선택합니다 (Kang 5605921, Tsatsaragkos 6004950).
2. 오류 VN 집합 T = 그 반복 hard decision XOR 송신 codeword의 지지 집합입니다. 불만족 CN 집합 CU를 계산하고 (a,b)를 산출합니다 (정의는 Han 9729722, Zhang 5336848).
3. 유도 부분 그래프 추출: T와 그 이웃 CN을 뽑습니다. 차수 1(불만족)과 차수 2(mis-satisfied)를 구분하고, elementary 여부와 absorbing 조건을 검사합니다 (Zhang 5336848).
4. 사이클 분석: 유도 부분 그래프 안의 최단 사이클과 사이클 공유 구조를 봅니다. 결과를 Karimi 6259854의 지배 TS 목록과 대조합니다.
5. 진동 판정: 반복별 불만족 CN 수와 T 크기 시계열의 주기성으로 안정형과 진동형을 분류합니다 (Han 5089505, Zhang 5336848).
6. 경로 분석: CU 쌍 사이의 error path와 shallow/deep VN을 구분합니다 (Han 9729722).
7. 통계 집계: 실패 N개를 (a,b)와 동형(isomorphism) 클래스로 묶어 지배 TS 빈도표를 만듭니다. 샘플이 부족하면 Cole(cs/0605051)이나 Cavus(5165375)의 사이클 시드 편향과 중요도 샘플링으로 보강합니다.
8. 유해도 순위(선택): Farsiabi 9005250과 Zhang 6120280의 선형 모델로 TS별 기여를 추정합니다.

## 4. 확인했지만 제외한 주요 논문
- **ieee:7050116** (TS 식별 기법, Vasilopoulos): 제목은 맞지만 본문은 H에서 사이클을 열거해 TS를 조합하는 부호 쪽 열거입니다(목표 2). 실패 출력 입력이 없습니다.
- **ieee:4697991** (Fast identification of error-prone patterns): 본문은 ACE 기반 사이클 식별과 인터리버 설계이고 실패 진단이 아닙니다.
- **ieee:8395069, 8359616, 7804004** (후처리 디코더): 불안정 비트를 지우거나 LLR을 교란할 뿐 원인 구조를 식별하는 절차가 없습니다.
- **ieee:9613326** (NR 후처리): 오류 위치를 순환 이동 CRC 검출로 추정하며 TS 식별 절차는 약합니다.
- **ieee:9295784, 9594253**: 식별이 아니라 디코더 개선입니다(DNN, FAID 다양화).
- **ETS 열거와 정수계획 계열** (ieee:8279531, 8006717, 7541754, 6204555 등): 부호 쪽 탐색이라 목표 2 영역입니다.
- **양자 LDPC 계열** (ieee:10273526, 10273573, arxiv:2012.15297 등): 양자 부호라 직접 이식이 안 됩니다.
- **ieee:9369532** (로지스틱 회귀 실패 예측): 조기 종료용 예측이고 원인 구조 식별이 아닙니다.
- **ieee:9902993** (UP-GDBF), **ieee:11079633** (AsLDPC): NAND 대상이지만 디코더나 부호 설계 개선이고 진단 절차는 초록상 없습니다. AsLDPC 본문은 미확인입니다.
- NAND 분야에서 실패 패턴 분류 자체를 다룬 논문은 제목 기준으로 찾지 못했습니다.

## 5. 아카이브에 없는 정본 논문
- **Richardson, "Error floors of LDPC codes" (Allerton 2003)**: DB 제목과 저자 검색에서 모두 미발견이므로 없는 것으로 판단합니다.
- 아카이브에 있는 것: Kang, Han-Ryan, Cavus 두 편, Landner, Chilappagari instanton, Cole, Zhang 두 편(4698365, 5336848).
- Declercq, Planjery, Vasic의 FAID 정본 본편은 확인하지 못했습니다(미확인). FAID Tanner code 논문(ieee:5613861)과 FAID 다양성 논문(ieee:7094412, ieee:9594253)은 있습니다.

## 1순위 추천 이유와 요약
- **Kang backtracking(5605921)**: 실패 출력에서 TS 경계 VN을 식별하는 절차가 pseudo-code로 명시돼 있습니다. 입력이 반복별 불만족 CN 수와 디코더 상태뿐이라 min-sum에 바로 붙습니다. 송신 codeword가 있으면 오류 VN 집합을 직접 얻을 수 있습니다.
- **Han-Ryan(5089505)**: 불만족 CN에서 시작하는 트리 확장과 신드롬 가중치별 TS 클래스 조회라는 구체적 틀을 줍니다.
- **Han error path(9729722)**: error path와 shallow/deep 정의가 진단 지표로 가장 깔끔합니다.
- 분류와 통계 부분은 Zhang(5336848), Cole(cs/0605051), Cavus(5165375)가 보완합니다.
