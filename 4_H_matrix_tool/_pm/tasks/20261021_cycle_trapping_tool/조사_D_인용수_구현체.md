# 보고서 D: 정본 논문 인용 수, 아카이브 대조, 공개 구현체

확인 날짜는 2026-10-21입니다. 인용 수는 모두 OpenAlex(api.openalex.org) 값입니다. Google Scholar보다 대체로 낮게 나오므로 상대 순위용으로만 쓰십시오. Semantic Scholar는 HTTP 429로 막혔고 Google Scholar는 접근하지 못했습니다. 확인하지 못한 값은 "미확인"입니다. "txt"는 data/pdfs 아래 파일을 find로 확인한 결과이고, "미조회"는 확인하지 않은 것입니다.
약어: QC-LDPC(quasi-cyclic low-density parity-check, 준순환 저밀도 패리티 검사 부호), ETS(elementary trapping set, 기초 trapping set), ACE(approximate cycle extrinsic message degree, 사이클의 근사 외부 메시지 차수), TS(trapping set), girth(Tanner 그래프의 최단 사이클 길이).

## 1-1. 사이클 세기

| 논문 | 연도, 게재지 | 인용 수 | DB id | txt | 요지 |
|---|---|---|---|---|---|
| Halford, Chugg, An algorithm for counting short cycles in bipartite graphs | 2006, IEEE Trans. Inf. Theory | 95 | ieee:1564444 | 있음 | girth부터 girth+4 근처 사이클을 센다. 후속 연구의 비교 기준 |
| Karimi, Banihashemi, Message-passing algorithms for counting short cycles in a graph | 2013, IEEE Trans. Commun. | 60 (Emergent Mind의 arXiv판은 53) | ieee:6336765 (학회판 ieee:5503171) | 6336765 있음 | 메시지 전달로 길이 g부터 2g-2까지 센다. 복잡도 O(g|E|^2). 희소 그래프에서 빠르고 메모리가 적다 |
| Karimi, Banihashemi, Counting short cycles of QC protograph LDPC codes | 2012, IEEE Commun. Lett. | 34 | ieee:6150653 | 있음 | 순환 이동 값(지수 행렬)만으로 센다 |
| Dehghan, Banihashemi, Counting short cycles in bipartite graphs: a fast technique/algorithm and a hardness result | 2019-2020, IEEE Trans. Commun. | 17 | ieee:8943145 | 있음 | 방향 간선 행렬 기반 빠른 세기와 어려움 증명 |
| Dehghan, Banihashemi, On computing the number of short cycles ... spectrum of the directed edge matrix | 2020, IEEE Trans. Inf. Theory | 6 | ieee:9146593 (학회판 ieee:8625355, ieee:8989394) | 있음 | 방향 간선 행렬의 고유값으로 센다 |
| Dehghan, Banihashemi, On the Tanner graph cycle distribution of random LDPC, protograph and QC-LDPC codes | 2018, IEEE Trans. Commun. | 미확인 | ieee:8291725 | 있음 | 앙상블 평균 사이클 분포 |
| Blake, Lin, On short cycle enumeration in biregular bipartite graphs | 2018, IEEE 학회 (arXiv 1701.02292) | 미확인 | ieee:8225637 (제목 일치만 확인) | 미조회 | 열, 행 가중치 고정 그래프의 사이클 수 공식 |
| Fossorier, Quasicyclic LDPC codes from circulant permutation matrices | 2004, IEEE Trans. Inf. Theory | 1219 | ieee:1317123 | 있음 | 사이클 존재 조건(지수 교대합이 법 Z에서 0). QC 사이클 검사의 근거 |
| Tian 외, Construction of irregular LDPC codes with low error floors (ACE) | 2003 학회, OpenAlex는 2004 | 196 | ieee:1203996 | 있음 | ACE로 해로운 사이클 선별 |
| Abdu-Aguye 외, girth and ACE distributions algorithm | 2016 | 미확인 | ieee:7843313 | 있음 | girth와 ACE 분포 동시 계산 |
| Gómez-Fonseca, Smarandache 외, efficient strategy to count cycles in QC-LDPC Tanner graph | 2023 | 미확인 | ieee:10251427 | 있음 | 최근 QC 전용 (참고) |
| Gholami, Gholami, counting cycles in QC and APM LDPC codes | 2023, arXiv 2310.12556 | 미확인 | arxiv:2310.12556v1 | 미조회 | QC, APM 대상 (참고) |

## 1-2. trapping set, absorbing set, stopping set 열거

| 논문 | 연도, 게재지 | 인용 수 | DB id | txt | 요지 |
|---|---|---|---|---|---|
| Richardson, Error floors of LDPC codes | 2003, Allerton | 686 | 없음 | 없음 | trapping set 개념과 오류 마루 추정의 원조 |
| Karimi, Banihashemi, Efficient algorithm for finding dominant trapping sets | 2012, IEEE Trans. Inf. Theory | 107 | ieee:6259854 (학회판 ieee:5613902, ieee:6033699) | 있음 | 짧은 사이클에서 출발해 지배적 TS를 찾는다 |
| Hashemi, Banihashemi, Characterization of elementary trapping sets in irregular LDPC codes ... exhaustive search | 2018, IEEE Trans. Inf. Theory | 41 (variable-regular판 ieee:7575635는 62, ieee:7006675는 33) | ieee:8279531 | 있음 | 불규칙 부호 ETS 완전 탐색 |
| Hashemi, Banihashemi, Exhaustive enumeration of ETSs of an arbitrary Tanner graph | 2016 | 미확인 | ieee:7506265 | 있음 | 임의 Tanner 그래프 ETS 열거 |
| Hashemi 외, non-elementary trapping sets | 2019 | 미확인 | ieee:8434325 (arxiv:1801.02028) | 있음 | 비기초 TS 확장 |
| Hashemi 외, Hardness results on finding leafless ETS and elementary absorbing sets | 2019 | 미확인 | ieee:8667301 | 있음 | 열거가 어렵다는 증명 |
| Wang, Kulkarni, Poor, Finding all small error-prone substructures | 2009, IEEE Trans. Inf. Theory | 58 | ieee:4839029 | 있음 | 작은 stopping, trapping, absorbing 구조 전수 탐색 |
| Zhang, Siegel, Efficient algorithms to find all small error-prone substructures | 2011, GLOBECOM | 미확인 | ieee:6133832 | 있음 | Wang 방법의 효율 개선 |
| Rosnes, Ytrehus, Efficient algorithm to find all small-size stopping sets | 2009, IEEE Trans. Inf. Theory | 63 (Addendum ieee:6122000은 35) | ieee:5208476 | 있음 | 분기 한정 탐색 |
| McGregor, Milenkovic, Hardness of approximating stopping and trapping sets | 2010, IEEE Trans. Inf. Theory | 61 (학회판 28) | ieee:5437429 (학회판 ieee:4313082) | 5437429 없음 | NP-hard 증명 |
| Dolecek 외, Absorbing sets and fully absorbing sets of array-based LDPC codes | 2010, IEEE Trans. Inf. Theory | 207 | ieee:5361488 | 있음 | absorbing set 정의와 배열형 QC 열거 |
| Kyung, Wang, Exhaustive list of small fully absorbing sets | 2012, IEEE Trans. Commun. | 42 | ieee:6192273 (학회판 ieee:5513611) | 있음 | 완전 absorbing set 전수 탐색 |
| Vasic 외, Trapping set ontology | 2009, Allerton | 120 | ieee:5394825 | 있음 | TS 계층 분류 체계 |
| Dolecek 그룹, Cycle consistency matrix approach to absorbing sets in separable circulant-based codes | 2013 | 미확인 | ieee:6387307 | 미조회 | 순환형 부호의 absorbing set 분석 (QC 관련) |
| Usatyuk, Modified Cole's trapping sets enumerating | 2022-2023 | 미확인 | arxiv:2208.05795v1, ieee:10113442 | 미조회 | QC-LDPC용 열거 (참고) |

## 1-3. 디코딩 실패에서 원인 TS 식별

| 논문 | 연도, 게재지 | 인용 수 | DB id | txt | 요지 |
|---|---|---|---|---|---|
| Han, Ryan, Low-floor decoders for LDPC codes | 2009, IEEE Trans. Commun. | 123 | ieee:5089505 | 있음 | 불만족 검사 노드 집합으로 TS 식별 후 재복호 |
| Kang 외, Iterative decoding with backtracking | 2011, IEEE Trans. Commun. | 45 | ieee:5605921 | 있음 | 되짚어 오류 비트 후보 정정 |
| Zhang, Dolecek 외, Lowering LDPC error floors by postprocessing | 2008, GLOBECOM | 85 | ieee:4698365 | 있음 | 불만족 검사 정보로 후처리 |
| Cole 외, moderate length regular LDPC codes with low error floors | 2006, CISS | 미확인 | 없음 | 없음 | 중요도 표집으로 TS 탐색. 열거 구현체 다수의 기반 |
| Cavus 외, importance sampling applied to trapping sets | 2009, IEEE Trans. Commun. | 미확인 | ieee:5165375 | 있음 | 2005 학회판은 DB 미확인 |
| Chilappagari, Chertkov, Vasic, Instanton-based techniques | 2009, IEEE JSAC | 41 | ieee:5174515 | 있음 | 최소 가중 오류 패턴(instanton) |
| Stepanov, Chertkov, Instanton analysis | 2006, ISIT | 미확인 | ieee:4036023 | 있음 | instanton 개념 출발 |
| Error floor estimation of LDPC decoders (harmfulness of trapping sets) | 2020 | 미확인 | ieee:9005250 | 있음 | 복호기 무관 TS 위해도 측정 (참고) |
| He 외, post-processing on trapping sets for quantized NR LDPC decoders | 2021 | 미확인 | ieee:9613326 | 미조회 | 5G NR 후처리 (참고) |
| Learning to decode TS in QLDPC; Deep-learning for breaking TS | 2022-2023 | 미확인 | ieee:10273526, ieee:9729722 | 미조회 | 신경망 기반 (참고만) |

로컬 DB에 없는 정본은 Richardson 2003, Cole 2006, Cavus 2005 학회판입니다.

## 2. 공개 구현체 (별 수와 갱신일은 GitHub API, 2026-10-21 확인. 코드는 읽지 않았고 저장소 설명에 근거)

| 이름 | 링크 | 언어 | 기반 | 별, 최근 갱신 | 라이선스 | 활용 |
|---|---|---|---|---|---|---|
| trapping-sets-enumeration | github.com/Lcrypto/trapping-sets-enumeration | Jupyter Notebook (주제어 python, matlab) | Cole 중요도 표집 변형과 혼합 정수 선형 계획 | 23, 2025-07-31 | 표기 없음 | .alist 입력과 .trap 출력 형식 참고. 라이선스가 없으니 코드 복사는 피하고 방식만 참고 |
| Lolipop_cycles_count | github.com/Lcrypto/Lolipop_cycles_count | MATLAB | Halford, Chugg 알고리즘 | 10, 2023-04-28 | 표기 없음 | 내 구현의 사이클 수 검증 기준 |
| EMD-Spectrum-LDPC | github.com/Lcrypto/EMD-Spectrum-LDPC | C++ | 외부 메시지 차수 스펙트럼 (ACE 계열) | 9, 2024-04-16 | GPL-3.0 | 아이디어 참고. GPL이라 포함은 주의 |
| tanner-girth-cycle-counting | github.com/aarashahadiacademic-1/tanner-girth-cycle-counting | Python | 정확, 혼합 girth 사이클 세기 | 0, 2026-10-12 | 표기 없음 | 신생이라 신뢰도 낮음 |
| QC-LDPC-Performance-Evaluation | github.com/malihealiasgari20/QC-LDPC-Performance-Evaluation | 미표기 | QC-LDPC TS 선별 | 0, 2026-10-17 | 표기 없음 | 신생, 내용 미검증 |
| ldpc (Roffe) | github.com/quantumgizmos/ldpc, PyPI ldpc | C++ 핵심, Python 인터페이스 | BP, BP+OSD (양자 부호 중심. TS 열거는 확인하지 못함) | 229, 2026-06-02 | MIT | mod2 선형대수, 실패 코드워드 생성 |
| pyldpc | github.com/hichamjanati/pyldpc | Python | LDPC 생성과 복호 시뮬레이션 | 144, 2025-04-04 | BSD-3-Clause | 시뮬레이션 보조 |
| ldpc-toolbox | github.com/daniestevez/ldpc-toolbox | Rust | LDPC 설계 보조 (README에 girth, 사이클 언급 없음. docs.rs 미확인) | 29, 2025-11-26 | Apache-2.0 또는 MIT | 기능은 docs.rs로 먼저 확인 필요 |
| AFF3CT | github.com/aff3ct/aff3ct | C++ | 고속 오류정정 시뮬레이터 (TS 열거는 확인하지 못함) | 610, 2026-10-20 | MIT | 대량 실패 수집 참고 |
| Sionna, TS Ontology 웹사이트 | 미조사 | | | 미확인 | 미확인 | 조사하지 못함 |

결론: GitHub 검색(저장소 이름과 설명 기준)에서 성숙한 Python TS 열거 구현체는 찾지 못했습니다. 사이클 세기와 열거의 공개 구현은 MATLAB, C++, 소규모 신생 저장소뿐입니다. "없다"가 아니라 "찾지 못했다"입니다. 직접 Python 도구를 만들 근거가 됩니다.

## 3. 가장 신뢰할 만한 출발점

- 사이클 세기: ㉮ Halford, Chugg 2006(인용 95, 기준이 되는 원조), ㉯ Karimi, Banihashemi 2012-2013(인용 60, 희소 그래프에서 빠르고 메모리 절약). 열 가중치 3-4의 희소 H에는 메시지 전달 방식이 적합합니다. QC이므로 Fossorier 2004(인용 1219)의 지수 조건과 Karimi 2012 Commun. Lett.(인용 34)로 지수 행렬 수준에서 세면 부호 길이와 무관하게 빠릅니다. 소형 예에서 Halford 방식으로 교차 검증하십시오.
- TS 열거: ㉮ Karimi, Banihashemi 2012 지배적 TS 탐색(인용 107, 짧은 사이클에서 출발해 구현이 단순), ㉯ Hashemi, Banihashemi 2016-2018 ETS 열거 계열(후속 논문 다수). 라벨링은 Dolecek 2010(인용 207)과 Vasic 온톨로지(인용 120)를 쓰십시오. 일반 열거는 NP-hard(McGregor 2010 인용 61, Hashemi 2019)이므로 크기 상한을 둔 탐색이 필수입니다.
- 실패 원인 식별: ㉮ Han, Ryan 2009(인용 123), ㉯ Zhang 외 2008(인용 85). 실패 코드워드 하나로 동작하므로 목표 1에 직접적입니다. 미리 열거한 TS 목록과, 실패 시점의 불만족 검사 노드 및 오류 비트 집합을 대조하는 구성이 자연스럽습니다. Richardson 2003(인용 686)은 개념 근거로 인용합니다.

## 4. 한계

- 인용 수는 OpenAlex 한 곳 기준입니다. Google Scholar 값은 미확인입니다.
- Blake, Lin 2018, Cole 2006, Cavus 2005는 DB 대조와 인용 수를 끝내지 못했습니다.
- 구현체 기능은 저장소 설명에 근거하며 코드를 읽지 않았습니다. Sionna와 TS Ontology 웹사이트는 조사하지 못했습니다.
