# 목표 2 논문 선별 보고서 (주어진 H의 사이클 조사 알고리즘)

## 요약
- 제목 825편을 훑고 초록 약 45편을 확인했습니다. 상위 후보는 본문 txt에서 복잡도 식, 실험 환경, 의사코드 유무를 확인했습니다.
- "추정"은 논문이 직접 말하지 않은 제 해석이고, "미확인"은 확인하지 못한 항목입니다.
- 1순위는 Karimi, Banihashemi 2013(ieee:6336765)입니다.
  - 근거 ㉮: 길이 g부터 2g-2까지 사이클 수를 정확히 세고, 시작 노드별 결과를 줍니다. 노드별 결과를 모든 시작 노드에 대해 합하면 전체 개수가 됩니다.
  - 근거 ㉯: 정수 덧셈과 뺄셈만 쓰는 메시지 전달이라 numpy 벡터화가 쉽습니다.
  - 근거 ㉰: 이후 논문(7282488, 8943145, 11148122, 10251427)이 모두 비교 기준으로 인용합니다.
  - 근거 ㉱: 복잡도는 O(g|E|²)입니다.
- 속도가 중요하면 3순위 FMPA(11148122, 2025)가 맞습니다. 10000×10000, 열가중치 3 부호에서 실측됐습니다(C++ 기준).
- 질문 목록의 정본 논문은 Mao-Banihashemi 2001과 Wang-Fossorier-Draper 계열을 뺀 전부 아카이브에 본문 txt와 함께 있습니다.

## 1. 추천 순위표
표기: n은 변수 노드 수, |E|는 간선 수, g는 girth(최단 사이클 길이), p는 순환 행렬(circulant) 크기, |V|는 노드 수, Δ는 최대 차수입니다. 본문 열의 T는 본문 txt 있음입니다. 본문 경로는 `../LDPC_Paper_Analysis/data/pdfs/ieee/연도/월/ieee_번호.txt`입니다. 게재지는 DB 날짜 형식과 논문 인용으로 판단했고, 확정하지 못한 것은 "미확인"입니다.

| 순위 | id | 연도 | 제목 | 저자(앞 2명) | 알고리즘 한 줄 | 출력물 | 복잡도(논문 식) | 신뢰성 근거 | Python 구현 메모 | 본문 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ieee:6336765 | 2013 | Message-Passing Algorithms for Counting Short Cycles in a Graph | Karimi, Banihashemi | 노드가 정수 메시지(덧셈과 뺄셈만)를 주고받아 길이 g, g+2, ..., 2g-2 사이클을 정확히 셈 | 정확. 시작 노드별 개수(전체는 합한 뒤 k로 나눔) | O(g\|E\|^2). 행렬곱 방식도 같은 복잡도 | DB 날짜 Feb. 2013. 이후 논문 4편이 비교 기준으로 인용 | numpy 벡터 메시지(길이 d_u)로 구현 가능. QC이면 순환 열 대표만 시작해 p배 절약(추정. 7282488이 QC에서 p배 절감을 명시) | T |
| 2 | ieee:8943145 | 2020 | Counting Short Cycles in Bipartite Graphs: A Fast Technique/Algorithm and a Hardness Result | Dehghan, Banihashemi | 너비 우선 탐색(BFS) 변형. 노드마다 g/2 층까지 경로 수를 세어 g, g+2, g+4 사이클 계산 | 정확. 길이 g, g+2, g+4 총개수 | g, g+2는 O(\|V\|^2 Δ), g+4는 O(\|V\|^2 Δ^2), 이분 정규 그래프는 g+4도 O(\|V\|^2 Δ). 기존 최고 O(g\|V\|^2 Δ^2)보다 낮음 | Banihashemi 그룹. DB 날짜 March 2020. 4개 부호에서 MPA 결과와 개수 일치(Table I) | 정리 1-3 기반이라 난이도 중간. scipy.sparse 인접 리스트로 가능(추정) | T |
| 3 | ieee:11148122 | 2025 | A Fast Messages-Passing Algorithm for Counting Short Cycles in Bipartite Graphs | Chen, He | IMPA(개선 메시지 전달)를 효율 구현하고 층별 활성화로 가속한 FMPA | 정확. g부터 2 l_max까지 원하는 길이별 개수 | 저장 O(δ\|E\|), 계산 O((l_max-g/2+1)\|E\|^2) | 2025 최신, 학회 발표(10-13 Aug. 2025), 게재지 미확인. 10000×10000 열가중치 3 부호까지 실측 | C++ 실측이라 Python은 느릴 것(추정). 메시지 전달 구조라 scipy.sparse 벡터화 가능(추정) | T |
| 4 | ieee:1564444 | 2006 | An algorithm for counting short cycles in bipartite graphs | Halford, Chugg | 정수 행렬 연산으로 길이 g, g+2, g+4 사이클 수를 모든 정점에 대해 계산 | 정확. 정점(U와 W 모두)별 g, g+2, g+4 개수 | O(g n^3), n = max(\|U\|,\|W\|) | 질문 목록의 정본(DB 날짜 Jan. 2006). 후속 논문이 모두 인용. 저자 C++ 구현 공개 언급 | 밀집 행렬 곱이라 n=1만 이상에서 비현실적(n^3은 약 1e12, 추정). 희소화 필요. 교차검증용 | T |
| 5 | ieee:7282488 | 2015 | Improved message-passing algorithm for counting short cycles in bipartite graphs | Li, Lin | Karimi 알고리즘 계산을 절반으로 줄임. QC는 p배 추가 절감 | 정확. 길이별 개수 | Karimi의 절반, QC이면 p배 추가 절감(초록) | Shu Lin 그룹. 학회(14-19 June 2015). 11148122이 IMPA로 계승 | QC 절감이 명시되어 목표에 직접 적합. MATLAB 실측 | T |
| 6 | ieee:10251427 | 2023 | An Efficient Strategy to Count Cycles in the Tanner Graph of Quasi-Cyclic LDPC Codes | Gomez-Fonseca, Smarandache | 다항식 패리티 검사 행렬로 보호 그래프(protograph)의 워크(walk)를 세어 사이클 수 계산 | 정확. 길이 k(g<=k<2g) 총개수 | 3×n_v 완전 연결: k=4는 O(n_v^2 log N), k=6은 O(n_v^2 log(n_v) log N), k=8은 O(n_v^4 log^4(n_v) log N). N에 로그 의존 | Smarandache 그룹(QC girth 이론). 게재지 미확인. 학회판 10207005 | QC 구조(순환 지수 행렬) 필수. 정리가 열가중치 3 완전 연결 형태 중심이라 다른 형태는 확장 필요 가능(미확인). Algorithm 1(6-사이클)과 예시 포함 | T |
| 7 | ieee:6150653 | 2012 | Counting Short Cycles of Quasi Cyclic Protograph LDPC Codes | Karimi, Banihashemi | 방향 간선 행렬을 블록 순환 행렬로 표현해 고유값 계산을 줄임 | 정확. 길이별 총개수 (N_k = 고유값 k제곱 합/(2k)) | 식 미확인. 실험: N=2000, 3×5 보호 그래프에서 18초(제안) 대 119초(기존), 다른 기존법은 메모리 부족 | 질문 목록의 Karimi 2012 (DB 날짜 March 2012) | QC 필수. 블록 순환 고유값은 FFT로 구현 가능(추정) | T |
| 8 | ieee:9146593 | 2020 | On Computing the Number of Short Cycles in Bipartite Graphs Using the Spectrum of the Directed Edge Matrix | Dehghan, Banihashemi | 인접 행렬 고유값에서 방향 간선 행렬 고유값을 유도, N_k = sum(eta_i^k)/(2k) | 정확. 길이 k<2g 총개수 | 이분 정규 O(\|V\|^3), 일반 O(\|E\|^3) | Banihashemi 그룹. DB 날짜 Oct. 2020 | 고유값 분해 필요라 n=수만은 비현실적(추정). 소규모 교차검증용 | T |
| 9 | ieee:8626151 | 2019 | On Computing the Multiplicity of Cycles in Bipartite Graphs Using the Degree Distribution and the Spectrum of the Graph | Dehghan, Banihashemi | Blake-Lin을 g+2, ..., 2g-2로 확장. 불규칙 그래프는 4, 6-사이클만 | 정확. 길이별 총개수 | 고유값 분해 O(\|V\|^3) 수준(9146593 초록 근거) | 질문 목록의 Dehghan 정본(June 2019) | 스펙트럼 방식 | T |
| 10 | ieee:8225637 | 2018 | On Short Cycle Enumeration in Biregular Bipartite Graphs | Blake, Lin | 그래프 이론과 스펙트럼으로 girth와 길이 g 사이클 수 계산 | 정확. girth, N_g | 미확인 | 질문 목록의 Blake-Lin 정본(Oct. 2018) | 이분 정규 한정 | T |
| 11 | ieee:7843313 | 2016 | An efficient algorithm for determining the girth and ACE distributions in LDPC code Tanner graphs | Abdu-Aguye, Ambroze | 단일 간선 트리 정점(SETA) 부분 그래프 확장으로 짧은 사이클 직접 탐색 | 정확. 변수 노드별 지역 girth와 ACE(approximate cycle extrinsic message degree), 그 분포 | O(nm), H는 m×n (초록) | 학회(19-21 Dec. 2016), 게재지 미확인. MPA, IMPA보다 빠르다는 표 포함 | 노드별 girth와 ACE를 한 번에 줘서 목표 2에 직접 적합. QC 부호용이 아님을 명시. 실측은 C | T |
| 12 | ieee:5503171 | 2010 | A message-passing algorithm for counting short cycles in a graph | Karimi, Banihashemi | 6336765의 학회판 | 정확 | O(g\|E\|^2) | 학회(6-8 Jan. 2010) | 6336765가 있으므로 참고용 | 미확인 |
| 13 | ieee:1327837 | 2004 | Selective avoidance of cycles in irregular LDPC code construction | Tian, Jones | EMD(extrinsic message degree) 정의와 근사값(ACE)으로 사이클 군집 회피 | 지표 정의 | 미확인 | 질문 목록의 Tian 2004 정본, ACE 출처 | 지표 정의 근거. 사이클 열거는 다른 논문 필요 | T |
| 14 | ieee:4036077 | 2006 | An Efficient Girth-Locating Algorithm for Quasi-Cyclic LDPC Codes | 미확인 | 다항식 패리티 검사 행렬로 QC 부호 girth 탐색 | girth | 미확인 | 학회(9-14 July 2006) | QC girth 전용 | 미확인 |
| 15 | ieee:4542738 | 2008 | A necessary and sufficient condition for determining the girth of quasi-cyclic LDPC codes | 미확인 | 다항식 행렬로 girth 필요충분조건 도출(사이클 열거 없이) | girth | 미확인 | DB 날짜 June 2008 | girth만 필요할 때 빠름 | 미확인 |

### n=10000 근처 실측 (ieee:11148122 Table III, C++, 2.5GHz, 16GB)
C5는 10000×10000, 열가중치 3 부호입니다. 시간은 초입니다.

| 방법 | l_max=g/2 | l_max=g/2+1 | l_max=g/2+2 |
|---|---|---|---|
| FMPA | 0.63 | 1.34 | 2.72 |
| 수정 BFS (8943145) | 0.50 | 1.63 | 10.24 |
| IMPA (7282488) | 267.40 | 350.77 | 450.21 |

## 2. 1순위 3편 상세

### 2-1. ieee:6336765 Karimi, Banihashemi (메시지 전달 알고리즘, MPA)
- ㉮ 시작 변수 노드 u가 d_u개 간선으로 길이 d_u의 단위 벡터 메시지를 보냅니다.
- ㉯ 매 반복마다 활성 노드가 입력 메시지를 모두 더하고, 간선별로 그 간선의 입력을 빼서 출력(extrinsic) 메시지를 만듭니다. 정수 덧셈과 뺄셈만 씁니다.
- ㉰ g-1번 반복하며, u로 돌아온 메시지로 u를 지나는 길이 2k 사이클 수를 얻습니다. 전체 개수는 한쪽 노드 집합 전체에 대해 합한 뒤 길이 2k는 k로 나눕니다(본문 597행).
- 복잡도(본문 664행): 시작 노드당 O(g|E|d_u).
- 주의 ㉮: QC에서 순환 열 대표만 시작해 p배 절감하는 것은 추정입니다.
- 주의 ㉯: g를 먼저 알아야 반복 횟수가 정해지므로 girth 계산이 선행됩니다.
- 주의 ㉰: 2g-2까지만 셉니다.
- 주의 ㉱: 행렬곱 대안(본문 809행)도 같은 복잡도입니다. 시작 노드 행을 합친 |V|×2|E| 행렬에 방향 간선 행렬을 반복해서 곱합니다.

### 2-2. ieee:8943145 Dehghan, Banihashemi (수정 BFS)
- ㉮ 각 노드 v에서 BFS를 g/2 층까지 돌려 L_{g/2}(v)의 각 노드 u까지 최단 경로 수 |P_v(u)|를 셉니다.
- ㉯ 정리 1이 이 경로 수의 제곱합으로 g-사이클 수를 줍니다. 본문 예시는 합이 4αβ이면 4-사이클 수가 4αβ/4입니다. 정확한 식 형태는 미확인입니다.
- ㉰ 정리 2, 3이 롤리팝(lollipop) 개수와 R1, R2 항으로 (g+2), (g+4)-사이클 수를 줍니다. 본문 예시는 6-사이클 = (20αβ-8αβ)/6입니다.
- 주의 ㉮: 그래프가 대칭이면 노드 하나만 돌리면 됩니다(본문 예시). QC에서 순환 열 대표만 돌리는 것은 추정입니다.
- 주의 ㉯: 정확히 g, g+2, g+4만 셉니다. 임의 길이 분포가 필요하면 MPA를 씁니다.
- 주의 ㉰: 본문 실험은 C++입니다.

### 2-3. ieee:11148122 Chen, He (FMPA)
- ㉮ IMPA를 효율 구현하고 층별 활성화로 필요한 노드만 갱신합니다.
- ㉯ 출력은 원하는 l_max in [g/2, g-1]까지 길이 2l 사이클 수 eta_{2l}입니다.
- ㉰ 복잡도는 저장 O(δ|E|), 계산 O((l_max-g/2+1)|E|^2)입니다.
- 주의 ㉮: 실측이 C++이므로 Python은 수십 배 느릴 수 있습니다(추정). numpy/scipy.sparse 벡터화가 필요합니다.
- 주의 ㉯: g와 g+2까지만 필요하면 l_max를 작게 잡아 크게 절약됩니다.
- 주의 ㉰: 의사코드는 본문에 알고리즘 항목이 15회 언급되는 것까지만 확인했고 상세는 미확인입니다.

## 3. 확인했지만 제외한 주요 논문
- girth-8, 10, 12 QC 구성법 논문 수십 편, PEG 변형: 구성이 목적이라 제외했습니다.
- ieee:9518241, 9594176, 6620709: "girth 필요충분 조건"이라 girth 판정만 되고 개수는 못 줍니다. 4542738만 참고로 15위에 뒀습니다.
- ieee:5371660 (Li 2009): 로직 대수로 모든 사이클을 검출한다고 하나 초록에 복잡도가 없고 검증 근거가 부족합니다.
- ieee:5689706 (Hu, Zhao 2010): 길이 4, 6, 8, 10 사이클을 행렬 패턴 열거로 검출합니다. 대형 부호 적용성 근거가 부족합니다.
- ieee:4697481 (Kong, Xiao 2008): QC의 작은 stopping set과 girth 세기입니다. 복잡도 근거가 부족합니다.
- ieee:8437844 (Cho 2018): 비이진 LDPC의 full-rank 조건 사이클이라 이진 H에는 해당이 없고 본문 txt도 없습니다.
- ieee:10207005는 10251427의 학회판으로 판단해 제외했습니다.
- ieee:8625355, 8989394는 Dehghan 스펙트럼 논문의 학회판이라 8626151, 9146593으로 대체했습니다.
- ieee:8291725, 9834637: 무작위 앙상블의 사이클 분포(점근 분석)이며 주어진 H의 계산이 아닙니다.
- ieee:6955087 (Deka 2014): ACE와 EMD 같음의 조건으로, 지표 이론이며 계산 알고리즘이 아닙니다.
- ieee:1606100 (John, Kwon 2005): ACE를 구성에 적용한 논문입니다.
- arxiv:2601.05340 (Smarandache, Mitchell 2026): 이분 정규 QC 그래프의 N_2k를 고유값으로 재귀 계산하고 k<=7 명시식을 줍니다. 프리프린트라 보조 후보로만 둡니다.
- arxiv:1808.00352 (Alinejad 2018): 이분 정규 스펙트럼 이론이라 제외했습니다.
- ieee:4036088, 1683938 (Halford): 4-사이클 없는 Tanner 그래프의 이론이라 구현 관련성이 낮습니다.

## 4. 아카이브 점검
아카이브에 있는 질문 목록 논문(본문 txt 포함):
- Halford-Chugg 2006 (ieee:1564444)
- Karimi-Banihashemi 2013 (ieee:6336765), 학회판 2010 (ieee:5503171)
- Karimi-Banihashemi QC 보호 그래프 2012 (ieee:6150653)
- Dehghan-Banihashemi 2019 (ieee:8626151), 2018 학회판 (ieee:8625355), 2020 (ieee:9146593)
- Blake-Lin 2018 (ieee:8225637)
- Fossorier 2004 (ieee:1317123): 순환 치환 행렬 QC 부호의 girth 상한 12와 girth 6, 8, 10, 12 조건. 사이클 열거 알고리즘은 아니라 순위표 밖입니다.
- Tian 등 2004 (ieee:1327837)

아카이브에 없는 정본 논문:
- Mao, Banihashemi 2001 girth 계산 논문: 저자와 제목 검색에서 미발견입니다. 제목이 불확실해 확정은 못 합니다.
- Wang, Fossorier, Draper 등 "행렬 거듭제곱/trace 사이클 세기" 계열: 해당 제목을 못 찾았습니다. 같은 방식이 Karimi 2013의 행렬곱 절과 Dehghan 스펙트럼 논문에 들어 있습니다.

## 5. 목표 2 종합 의견
- 길이 4/6/8/10 사이클 수와 노드별 수: Karimi MPA(6336765)와 FMPA(11148122)가 중심입니다.
- QC 구조 총개수: 10251427(다항식 H, N에 로그 의존)과 6150653(블록 순환 고유값)입니다.
- 노드별 girth와 ACE: 7843313(SETA)입니다. ACE 정의는 1327837입니다.
- 검증: 소규모 H에서 스펙트럼 방식(8626151, 9146593)과 비교해 교차 확인할 수 있습니다.
- 미확인: Python 실측 시간(어느 논문에도 없음), 8943145의 정확한 게재지, 7843313과 11148122의 학회명, 6150653의 복잡도 식.
