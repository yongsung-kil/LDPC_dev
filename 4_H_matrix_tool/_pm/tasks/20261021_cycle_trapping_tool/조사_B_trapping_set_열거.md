# 보고서 B: 주어진 H에서 유해 부분 구조(trapping set 등)를 찾는 알고리즘 논문 선별

범위: 후보 592편 제목 전수 확인, 약 45편 초록 확인, 상위 약 12편은 본문 txt에서 실험 길이와 시간을 직접 확인했습니다. 본문에서 확인하지 못한 항목은 "미확인"으로 표시했습니다.
약어: ETS(elementary trapping set, 기본 trapping set), LETS(leafless elementary trapping set, 잎 없는 기본 trapping set), EAS(elementary absorbing set), FAS(fully absorbing set), FEAS(fully elementary absorbing set), SS(stopping set), B&B(branch and bound, 분기한정법), ILP(integer linear programming, 정수 선형 계획), QC(quasi-cyclic, 준순환), dpl(depth-one tree, path, lollipop 세 확장 기법).
본문 경로: `../LDPC_Paper_Analysis/data/pdfs/ieee/{연도}/{월}/ieee_{번호}.txt` (아래 표의 모든 논문에 본문 txt 있음, 예외는 따로 표시).

## 1. 추천 순위표

| 순위 | id | 연도 | 제목 | 저자(앞 2명) | 찾는 구조 | 탐색 방식 | 복잡도와 실험 길이(본문 인용) | 신뢰성 근거 | Python 구현 메모 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ieee:7575635 | 2016 | New Characterization and Efficient Exhaustive Search Algorithm for Leafless Elementary Trapping Sets of Variable-Regular LDPC Codes | Hashemi, Banihashemi | LETS (a, b 범위 지정, 예 a<=12,b<=5), 부분집합 EAS와 FEAS. 열 가중치 규칙형 | 짧은 사이클에서 출발, dpl 세 확장으로 완전 탐색. dv와 girth로 확장 계획표를 먼저 계산 | 2.4GHz 데스크톱. n=16383, R=0.87, dv=3 부호의 a<=8,b<=3 LETS 전수 약 27분. n=16383, dv=4 부호의 a<=8,b<=6 약 133분. n=8000 (4,8)-정규 a<=10,b<=10도 수행. 구조 부호 대칭은 쓰지 않은 전수 | IEEE Trans. IT. 같은 그룹 2017, 2019 후속 논문의 기반. Kyung-Wang FAS 결과와 일치 확인 | 중상. pseudo-code(Algorithm 1, 2, Routine 1-5) 있음. 사이클 열거와 부분 그래프 중복 제거가 핵심 |
| 2 | ieee:6259854 | 2012 | Efficient Algorithm for Finding Dominant Trapping Sets of LDPC Codes | Karimi, Banihashemi | 지배적(dominant) ETS, absorbing set, ZP(Zyablov-Pinsker) trapping set | 짧은 사이클에서 출발해 이웃 변수 노드를 하나씩 붙이는 재귀 확장(Algorithm 1). 완전 탐색은 아님 | 본문 주장: 블록 길이 약 10000까지 일반 데스크톱 처리 가능. 실험은 길이 1000 부호가 중심. 개별 시간표는 일부만 확인 | IEEE Trans. IT. Hashemi 논문이 "dot-based"로 계승하고 비교 | 상. 알고리즘이 한 절 분량이라 쉬움 |
| 3 | ieee:8434325 | 2019 | Characterization and Efficient Search of Non-Elementary Trapping Sets of LDPC Codes With Applications to Stopping Sets | Hashemi, Banihashemi | 비기본 TS, 응용으로 stopping distance(s_min)의 하한과 상한 | ETS에서 출발하는 계층적 확장. 조건부 완전 탐색 | R=0.87, n=16383 부호(C9): 하한 7을 약 2분, 상한 9를 약 3분. 길이 5219 구조 부호의 정확한 s_min 913초. (155,64) Tanner 상한 18을 45초 | IEEE Trans. IT | 중. 순위 1의 확장 기법이 선행 |
| 4 | ieee:7511551, ieee:7541754 | 2016 | An efficient exhaustive search algorithm for ETS of variable-regular LDPC codes; Minimal characterization and provably efficient exhaustive search algorithm for ETS | Hashemi, Banihashemi | ETS 전체(LETS 포함) | 순위 1과 같은 dpl 방식의 학회판 | 7511551: n=1057 dv=3 a<=8,b<=3 약 3분, n=16383 약 27분, dv=4 n=4095 약 68분, n=16383 약 133분. dot 방식은 하루 이상 | 학회판 (정본은 순위 1과 2017 TIT) | 순위 1과 동일 |
| 5 | ieee:8006717 | 2017 | Characterization and efficient exhaustive search algorithm for elementary trapping sets of irregular LDPC codes | Hashemi, Banihashemi | ETS (열 가중치가 섞인 irregular 부호) | dpl 특성화, 사이클 또는 단일 변수 노드에서 시작 | 실험 길이와 시간 미확인 | IEEE Trans. IT | 대상이 열 가중치 3-4 규칙형이면 순위 1로 충분 |
| 6 | ieee:6133832 | 2011 | Efficient Algorithms to Find All Small Error-Prone Substructures in LDPC Codes | Zhang, Siegel | 완전 탐색: stopping set, trapping set, absorbing set (변수 노드 amax 이하, 불만족 검사 노드 bmax 이하), 별도 알고리즘으로 FAS | 후보 벡터를 스택에 쌓는 트리 탐색. QC 부호는 시작 후보를 순환 이동으로 줄여 가속 | (155,64) Tanner: 후보 6.8e6개, QC 이용 시 6.0e5개. 실험 부호는 (816,408), (1008,504), (256,128) 등 길이 약 1000 이하. PEGR504 FAS(amax=bmax=5) 알고리즘 1이 59분, 알고리즘 2가 3분 | Globecom 2011. Kyung-Wang과 비교 | 중상. H만 있으면 됨. 수만 길이는 미실험 |
| 7 | ieee:6192273 (학회판 ieee:5513611) | 2012 | Finding the Exhaustive List of Small Fully Absorbing Sets and Designing the Corresponding Low Error-Floor Decoder | Kyung, Wang | FAS 완전 탐색 (n<1000에서 크기<7, 불만족 검사<3이면 크기<14) | ILP로 정식화한 B&B와 가지치기 | 길이 1000 이하. 802.16e n=2304에서 SS 크기 28 이하도 본문 주장. 일부 설정에서 6시간55분, 45시간43분 (비교 설정, 세부 미확인) | IEEE Trans. Commun. Hashemi 논문이 비교 대상으로 인용 (그 논문에 따르면 FAS 탐색 5-48시간) | 중. 가지치기 규칙 구현 필요, 느림 |
| 8 | ieee:4557664 (+ Addendum ieee:6122000) | 2007, 2012 | An Algorithm to Find All Small-Size Stopping Sets of LDPC Matrices | Rosnes, Ytrehus | stopping set 완전 탐색, 부호어 무게 스펙트럼 초기 부분 | 선형 계획 완화 트리 탐색과 자기동형군 이용 | (155,64) Tanner 크기 18 이하 전부 데스크톱 약 1분. (504,252) 여러 부호 크기 20 이하. (2184,1092) Ramanujan-Margulis까지 | IEEE Trans. IT, stopping set 정본 | 중하. linprog 필요, 수만 길이 미실험 |
| 9 | ieee:4839029 (arXiv cs/0609046은 초록만) | 2009 | Finding All Small Error-Prone Substructures in LDPC Codes | Wang, Kulkarni | stopping set (크기 13 이하), trapping set (크기 11 이하) 완전 탐색, NP 완전성 증명 | 트리 기반 stopping set 소거 탐색 | 길이 약 500 실용 부호. Golay 부호 130개 최소 SS를 2초 | IEEE Trans. IT | 순위 6의 선행 연구, 큰 n에는 부적합 |
| 10 | ieee:7506265 | 2016 | Exhaustive Enumeration of Elementary Trapping Sets of an Arbitrary Tanner Graph | Falsafain, Mousavi | (omega,nu)-ETS 완전 열거 | 0-1 ILP의 LP 완화 기반 B&B | (155,64) Tanner ETS(omega<=12, nu<=4) 연결형 전체 11660초. (504,252) PEG는 omega<=15,nu=1에서 1531초 | IEEE Trans. IT 계열 | 하. solver 의존, 수천 이상 비현실적 |
| 11 | ieee:6502981 | 2013 | An efficient exhaustive low-weight codeword search for structured LDPC codes | Khatami, Danjean | (a,0) trapping set = 저무게 부호어, QC 부호 전수 | 작은 trapping set으로 분해, 가능한 위상은 앙상블에서 알려진 것 사용 | 시간과 길이 미확인 | Vasic 그룹 계열 | 중. 위상 목록 필요 |
| 12 | ieee:9366194 | 2020 | The 5G New Radio Code: Elementary Absorbing Sets and Error Floor Performance | Otarinia, Fuja | 5G NR QC-LDPC의 EAS (core 열 1개, 2개 조합) | 기저 행렬 구조에서 core 열 조합을 열거하고 리프팅 값 Z별로 식별 | Z=16-60, N=832-3120 (본문 표) | 학회 논문 (게재지 미확인) | 상. 기저 행렬 위 조합 열거라 n에 둔감. 5G 구조 전용 |
| 13 | ieee:8901173 | 2020 | Construction of QC LDPC Codes With Low Error Floor by Efficient Systematic Search and Elimination of Trapping Sets | Karimi, Banihashemi | QC 프로토그래프 부호의 목표 LETS 집합 | 부모 구조만 찾는 층별 탐색 | (2133,1817) 배열 부호 예시. 시간 미확인 | Banihashemi 그룹 | 중. QC 구조가 제거하는 trapping set 특성화에 도움 |
| 14 | ieee:5394825 | 2009 | Trapping set ontology | Vasic, Chilappagari | trapping set 분류와 critical number | 탐색 알고리즘이 아니라 분류 체계 | 해당 없음 | Allerton, Vasic 그룹 | 지배 구조 판별 참고 자료 |
| 15 | ieee:6387307, ieee:5743618 | 2013, 2011 | The Cycle Consistency Matrix Approach to Absorbing Sets in Separable Circulant-Based LDPC Codes; LDPC absorbing sets, the null space of the cycle consistency matrix | Wang, Dolecek | separable circulant-based(SCB) QC 부호의 absorbing set 존재 판정 | 사이클 일관성 행렬의 GF(2) 계수로 존재 판정 | 대수 계산이라 n에 거의 무관. SCB 구조에 한정 | IEEE Trans. IT | 상. 순환 이동 지수만으로 계수 계산, numpy 가능. 구조 제약 있음 |

## 2. 1순위 3편 상세

### 1순위 ieee:7575635 (Hashemi, Banihashemi 2016, LETS 완전 탐색)
- ㉮ dv와 girth로 가능한 LETS 구조를 (a,b) 클래스별로 특성화(Algorithm 1).
- ㉯ 각 구조를 "어느 기본 구조(짧은 사이클)에서 어떤 확장(dot, path, lollipop)으로 생기는가" 표로 만든다.
- ㉰ 실제 H에서는 작은 사이클(s3, s4, 필요하면 s6까지)만 Routine 5로 열거하고 표대로 확장(Algorithm 2).
- ㉱ dot 단독보다 최대 세 자릿수 빠르다고 보고 (dot은 s5 인스턴스 16,710,009개를 찾는 데만 43분).
- 구현 주의: 사이클 인스턴스가 폭발하므로 (a,b) 범위를 작게 시작해 올린다. 중복 제거는 변수 노드 집합의 정렬 튜플 해시. 논문은 QC 대칭을 쓰지 않으므로 순환 이동 대표만 탐색하고 곱하는 최적화를 직접 넣으면 큰 이득. 대상 부호와 가장 닮은 R=0.87, n=16383, dv=3, 4 실험이 있음.

### 2순위 ieee:6259854 (Karimi, Banihashemi 2012, 지배적 trapping set)
- ㉮ 짧은 사이클 집합을 입력으로, trapping set마다 이웃 변수 노드를 하나 붙여 (a+1, b') 구조를 만드는 확장을 반복(Algorithm 1).
- ㉯ 불만족 검사 노드 수 상한 T로 가지치기. irregular 부호는 차수 2 변수 노드와 낮은 ACE 사이클도 입력(2011 irregular판 ieee:6033699).
- 구현 주의: 완전 탐색이 아니라 "지배적" 목록용. 순위 1의 완전 탐색과 교차 검증이 안전. 사이클 길이 상한과 T가 결과를 좌우.

### 3순위 ieee:8434325 (Hashemi, Banihashemi 2019, 비기본 TS와 stopping set)
- ㉮ ETS를 뼈대로 계층적 임베디드 그래프로 비기본 TS를 확장.
- ㉯ 이를 이용해 stopping distance의 상하한 산출 (Algorithm 3은 irregular 상한용).
- 구현 주의: 순위 1의 확장 기법이 선행. 비기본 구조가 불필요하면 생략 가능. n=16383에서 2-3분 보고라 확장성 근거로 가치가 큼.

## 3. 확인했지만 제외한 주요 논문
- 설계/제거 중심: ieee:10510143, ieee:8792126, ieee:6169192, ieee:7874123 외 "Free of Small Trapping Sets" 류.
- 앙상블 평균 열거(특정 H 아님): ieee:5695100(Abu-Surra), ieee:10032179, ieee:10330177, ieee:9899448, ieee:8736998, ieee:8625374.
- 해석적 분석: ieee:5361488(Dolecek, 배열 부호 해석, 임의 H 탐색 아님), ieee:11240558(Turan 수, 이론), ieee:8525278, ieee:8437465, ieee:7935340(크기 하한).
- 어려움 증명: ieee:4313082, ieee:5437429(McGregor, Milenkovic), ieee:8437485, ieee:8667301(LETS 탐색 NP 어려움), ieee:4067794. "완전 탐색은 범위 제한이 불가피"하다는 근거로 유용.
- 확률적/표본 기반: ieee:4578623, ieee:5654357, ieee:5755900(Richter, 오류 임펄스법).
- 단일 최솟값 LP/ILP: ieee:6204555, ieee:10510058(Usatyuk, CPLEX 필요, (2640,1320) Margulis와 (1008,504) 비교만 있어 신뢰성 낮다고 판단), ieee:10113442(Usatyuk, 설계 목적).
- 기타: ieee:7050116, ieee:6487954(순위 2의 하위 호환 성격), ieee:4697991, ieee:1549481(Landner), arxiv:1705.05996(서베이, 초록만).

## 4. 요청 목록 대비 아카이브 보유 현황
- 아카이브에 없음: Richardson, "Error floors of LDPC codes" (Allerton 2003). 제목 목록과 DB 모두에서 검색되지 않았습니다.
- 있음: Karimi 2012(ieee:6259854), Hashemi 2014(ieee:6847681, 정오표 ieee:7041306), 2016(ieee:7575635), 2017(ieee:8006717), 2019(ieee:8434325), Wang 2009(ieee:4839029), Rosnes 2007(ieee:4557664), Zhang 2011(ieee:6133832), Kyung 2012(ieee:6192273), Trapping set ontology(ieee:5394825), Nguyen 2012(ieee:6169192, 설계 논문), McGregor(ieee:4313082), Dolecek 2010(ieee:5361488), Abu-Surra 2011(ieee:5695100), Hashemi 하한(ieee:7935340).
- 있으나 본문 txt 없음(초록만): Cole 2006(arxiv:cs/0605051), Wang arXiv판(cs/0609046), 비기본 TS arXiv판(1801.02028).
- 2020년 이후 QC 전용 열거: 순위 12, 13이 전부로 보이며, cycle consistency matrix 계열은 2011-2013판만 확인했습니다. 더 최신 논문은 후보 목록에서 찾지 못했습니다.

## 5. 요약과 권고
- 구현 1순위: ieee:7575635. 이유: ㉮ H만 있으면 됨, ㉯ 고부호율(0.87), n=16383, dv=3, 4 실험 시간이 본문에 있음(27분과 133분), ㉰ pseudo-code 완비, ㉱ 후속 논문이 기반으로 사용.
- 보조: 지배적 구조 판별에 ieee:6259854와 ieee:5394825. QC 구조 이용 가속에 ieee:6387307, ieee:9366194.
- 주의: 수만 길이에서 현실적인 것은 Hashemi 그룹의 dpl 계열(순위 1-5)뿐입니다. 나머지 완전 탐색(순위 6-10)은 실험 길이가 약 2000 이하이고 ILP나 LP solver에 의존합니다. 이들은 C++급 구현의 시간이므로 순수 Python은 더 느릴 것이라는 점은 추정입니다.
