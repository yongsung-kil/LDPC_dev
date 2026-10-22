# 알고리즘 노트 B: trapping set 완전 탐색 (Hashemi 2016, Hashemi 2017 irregular, Karimi 2012 본문 정독)

> 출처 본문 (형제 저장소 `../LDPC_Paper_Analysis/data/pdfs/ieee/` 기준): Hashemi 2016 = `2016/12/ieee_7575635.txt`, Hashemi 2017 = `2017/06/ieee_8006717.txt`, Karimi 2012 = `2012/11/ieee_6259854.txt`. 2017 논문의 상세판은 arXiv 1611.10014.
> 공통 주의: txt에서 Table II 내용, III, IV, V, VI, VII, VIII, IX 및 실험 표 X-XVII의 칸 값은 거의 전부 그림이라 추출되지 않았다. 표의 존재와 읽는 법만 확인했고 칸 값은 "표 손상". 표 칸 값이 필요하면 같은 폴더의 PDF 원본을 봐야 한다. Karimi 2012 Algorithm 1은 수식 기호가 txt에서 소실되어 줄 번호 골격만 복원된다. "추정"은 논문에 없는 해석.

## 절 1. 정의와 식 (Hashemi 2016, II.A)

- Tanner graph G = (V ∪ C, E). V는 변수 노드 집합, C는 검사 노드 집합. 변수 노드 degree dv_i, 검사 노드 degree dc_i.
- variable-regular: 모든 변수 노드 degree가 dv. 논문은 dv ≥ 3 이고 4-cycle이 없는 경우(girth g > 4)만 다룹니다.
- Γ(S): S의 이웃 검사 노드 집합. G(S): 노드 S ∪ Γ(S), 간선은 S와 Γ(S) 사이 간선만 포함하는 유도 부분 그래프. 연결 그래프만 가정하며, 비연결은 연결 성분의 합집합으로 봅니다.
- Γo(S): G(S)에서 degree가 홀수인 검사 노드(unsatisfied). Γe(S): degree가 짝수인 검사 노드(satisfied). size는 S의 변수 노드 수.
- (a,b) trapping set(TS): |S| = a 이고 |Γo(S)| = b.
- elementary trapping set(ETS): G(S)의 모든 검사 노드 degree가 1 또는 2.
- absorbing set(AS): TS이고 S의 모든 변수 노드가 o(S)보다 e(S)에 더 많이 연결됨.
- elementary absorbing set(EAS): AS이면서 ETS. fully absorbing set(FAS): V\S의 모든 노드가 Γo(S)보다 C\Γo(S)에 엄격히 더 많이 연결됨. FEAS: EAS이면서 FAS 조건 만족.
- normal graph: ETS의 G(S)에서 degree 1 검사 노드와 그 간선을 지우고, degree 2 검사 노드와 두 간선을 간선 하나로 바꾼 그래프. 노드는 변수 노드뿐입니다. G(S)와 일대일 대응.
- Lemma 1: normal graph의 노드 수는 a, 간선 수는 e = (a*dv - b)/2. 즉 b = a*dv - 2e.
- leafless: 연결이고 최소 degree δ ≥ 2. LETS는 normal graph가 leafless인 ETS. leaf는 degree 1 노드(변수 노드가 만족 검사 노드 1개에만 연결된 경우에 해당).
- 관계: EAS는 LETS의 부분집합이고, dv = 3이면 LETS와 EAS는 같습니다.
- 표기: s_k 는 길이 k의 chordless(simple) cycle, c_k 는 chord가 있는 길이 k cycle, n_k 는 cycle이 아닌 prime 구조(dot 확장으로 얻을 수 없는 구조)의 크기 k.
- 인용된 사실: girth g에서 가장 작은 LETS는 s_{g/2} 이며 이 크기의 유일한 LETS입니다(Remark 1). 크기 a의 LETS 중 b가 가장 큰 것은 simple cycle s_a 로 (a, a*(dv-2)) 클래스의 유일한 구조(Proposition 2).
- 비교 구조: (a,b) 클래스 안의 구조는 normal graph 동형 여부로 구분. nauty의 geng으로 (노드 a, 간선 (a*dv-b)/2, 연결, 최소 degree 2, 최대 degree dv, 병렬 간선 없음, g ≥ 8이면 triangle-free) 옵션을 주면 모든 비동형 LETS 구조를 생성합니다. 이것이 알고리즘 1에서 완전성 검사에 쓰입니다.

## 절 2. 확장 세 가지 (IV.A, III.A)

공통: 모두 normal graph 공간에서 정의. 확장 전 S는 LETS.

- dot_m (depth-one tree): 새 변수 노드 1개(root, degree m)를 추가하고 S의 노드 m개와 간선 m개로 연결. 대상 m개 노드는 S에서 degree가 dv 미만이어야 하고, 2 ≤ m ≤ min{dv, b}. Proposition 1: (a,b) -> (a+1, b + dv - 2m). Tanner graph 쪽 조건(Routine 6): V\S 의 변수 노드 중 Γo(S)의 검사 노드와 2개 이상 연결되고 Γe(S)와는 연결이 없는 노드를 추가.
- path pa_m: 길이 m+1 경로를 붙임. 새 노드 m개(m ≥ 2, 즉 길이 3 이상. pa_1o는 dot_2와 같고 pa_1c는 4-cycle이라 제외). open(pa_m^o)은 양끝이 S의 서로 다른 두 노드(둘 다 degree < dv), closed(pa_m^c)는 양끝이 S의 같은 한 노드(그 노드 degree < dv - 1). Proposition 3: (a,b) -> (a+m, b - 2 + m(dv-2)), 조건 b ≥ 2.
- lollipop lo_m^c: S의 한 노드(degree < dv)에서 길이 d(≥1)의 경로가 나가고 끝에 길이 c(≥3)의 cycle이 달린 lollipop walk. 새 노드 m개, 길이 m+1 = d + c. Proposition 4: m ≥ 3, 3 ≤ c ≤ m 일 때 (a,b) -> (a+m, b - 2 + m(dv-2)), 조건 b ≥ 1. Tanner graph 상에서는 girth 때문에 실제 c는 g/2 이상.
- Lemma 5와 Theorem 1: 최소 특성화(각 단계가 더 작은 확장으로 쪼개질 수 없고 중간 구조가 모두 LETS)에서 쓰이는 확장은 dot, path, lollipop 셋뿐이며 simple cycle에서 시작해 모든 LETS를 만들 수 있습니다. Proposition 5의 증명 요지: dot-prime(더 작은 LETS에 dot으로 붙여 만들 수 없는) 구조가 cycle이 아니면 가장 큰 LETS 부분 구조에 path 또는 lollipop을 붙인 것입니다.
- Routine 1 (PathExpansion(S, m)): F = S에서 degree < dv 인 노드, F' = degree < dv - 1 인 노드. F의 크기 2 부분집합마다 pa_m^o 적용, F'의 노드마다 pa_m^c 적용. 결과를 합집합.
- Routine 2 (LollipopExpansion(S, m, c)): F = degree < dv 인 노드. 각 노드마다 lo_m^c 적용.

## 절 3. Algorithm 1 (dpl 특성화 표 생성, IV.B)

- 입력: a_max, b_max, dv, g. 출력: K(필요한 simple cycle 최대 길이), {L_{g/2}, ..., L_K}(각 cycle s_k 에서 파생된 비동형 LETS 집합), 표 EX(각 (a,b) 클래스에 적용할 확장 집합).
- 줄 단위 골격:
  - 1-2: 입력 받고 L = ∅, a = g/2, b'_max = b_max, EX(a,b) <- {dot} (모든 a in {g/2..a_max - 1}, b in {2..b'_max}).
  - 3: K = floor(b_max/(dv-2)).
  - 4-7: k = g/2..K 에 대해 L_k = DotExpansion(s_k, L, a_max); L = L ∪ L_k.
  - 8-20 (path와 lollipop 보충 단계): while a ≤ a_max: 크기 a의 LETS 클래스가 geng 결과와 비교해 불완전하면, 불완전한 (a,b) 클래스(1 ≤ b ≤ b_max)마다, k = g/2..K 에 대해 (L_tem, EX_tem) = PaLoExpansion(a, b, L_k, L); L_tem = DotExpansion(L_tem, L, a_max); L = L ∪ L_tem; L_k = L_k ∪ L_tem; EX = EX ∪ EX_tem. 이후 a = a + 1.
  - 21-42 (b 범위 확장 단계): 구조가 아직 모두 안 나왔으면 b'_max = b'_max + 1, a = g/2 로 두고 while a < a_max: EX(a,b'_max) <- dot. (a, b'_max)가 simple cycle 클래스이면 K = K + 1, L_K = DotExpansion(s_K, L, a_max), L = L ∪ L_K, L_K = ∅ 이면 EX(a,b'_max)에서 dot 제거. 아니면 k = g/2..K 에 대해 8-20 단계와 같이 PaLoExpansion(a, b'_max, L_k, L), DotExpansion, 갱신. a = a + 1.
  - 43: 출력 K, {L_{g/2}..L_K}, EX.
- Routine 3 (DotExpansion(P_k, L, a_max)): L_k^k <- P_k. a = k..a_max - 1 마다: 각 LETS S에 대해 F = degree < dv 인 노드, m = 2..dv 에 대해 F의 크기 m 부분집합마다 새 노드를 붙여 dot_m 적용, L_tem에 모음. L_k^{a+1} = L_tem \ L (이미 찾은 것 제외). 최종 L_k = 모든 a에 대한 합집합.
- Routine 4 (PaLoExpansion(a, b, L_k, L)): 줄 2-25. a' = a - 2 부터 g/2까지 감소. m = a - a'. 대상은 (a', b' = b + 2 - m(dv-2)) 클래스의 L_k 구조들 (Proposition 3, 4의 역계산). 각 구조에 PathExpansion(S, m)과 모든 가능한 c의 LollipopExpansion(S, m, c)을 적용하여 L_tem^p, L_tem^{c}에 모음. 새 구조(이미 L에 없는 것)가 생기면 EX_tem(a',b')에 pa_m 또는 lo_m^c를 기록하고, lollipop 결과는 L_tem에 합칩니다. 줄 14-15 조건 문장은 txt가 깨졌으며 요지는 "L에 없는 새 구조가 나올 때만 해당 확장을 EX에 넣는다" 입니다 (줄 19의 조건도 같은 취지: 새 구조가 있고 이미 L_tem에 없을 때). 이 줄 조건의 정확한 형태는 미확인.
- 정리: Theorem 2는 이 알고리즘이 K(필요 simple cycle 최대 길이)와 b'_max를 최소화한다는 최적성 주장. Remark 3, 4: 범위 안에서 새 구조를 못 만드는 확장은 EX에서 제거(예: Table VI에서 pa4를 s3에서, pa2를 s3에서 제거). Remark 5: 새 simple cycle이 새 구조를 못 만들면 표의 prime에 넣지 않음(Table VIII의 s6).

## 절 4. Algorithm 2와 Routine (IV.D, 실제 H에서 탐색)

- 입력: K, EX, g, a_max, b_max. 출력: I_k (k = g/2..K), 각각 s_k에서 파생된 크기 a_max 이하의 LETS 인스턴스(변수 노드 index 집합) 모음. I는 지금까지 찾은 모든 인스턴스.
- 줄 단위:
  - 1-7: I <- ∅, 모든 k = g/2..K 와 a = k..a_max 에 대해 I_k^a <- ∅.
  - 8-9: k = g/2..K 마다 I_k^k = CycSrch(s_k), a = k.
  - 10-24: while a < a_max: I_tem^{a+1} = DotSrch(I_k^a, I). EX에 있는 각 pa_m에 대해 I_tem^{a+m} = PathSrch(I_k^a, I, EX, m). EX에 있는 각 lo_m^c 에 대해 I_tem^{a+m} = LolliSrch(I_k^a, I_c^c, I, EX, m). t = a+1..a_max 에 대해 I_k^t = I_k^t ∪ I_tem^t, I = I ∪ I_tem^t. a = a + 1.
  - 25-27: I_k = 모든 a에 대한 I_k^a 합집합, 출력 {I_{g/2}..I_K}.
- 확장 대상은 EX가 그 클래스에 지정한 확장만 적용(PathSrch, LolliSrch 입력의 EX). 클래스는 I_k^a 안 인스턴스의 (a,b)로 판단합니다.
- 중복 제거: 각 Search 루틴이 "Item \ I" 연산으로 이미 찾은 인스턴스를 뺍니다. 인스턴스는 변수 노드 집합 S로 식별 (정렬된 index 튜플이나 집합으로 해시할 것은 추정).
- Routine 5 CycSrch(s_k): 각 변수 노드 v_l 마다, 그 이웃 검사 노드 c_i 마다 c_i에서 시작하고 v_l을 지나지 않는 Tanner graph 상 길이 k-1 경로 집합 PA_{i,l}을 구합니다. v_l의 서로 다른 이웃 검사 노드 쌍 (c_i, c_j) 에 대해 pa in PA_{i,l}, pa' in PA_{j,l} 가 같은 노드에서 끝나고 그 노드가 유일한 공통 노드이며, 마지막 변수 노드 v, v'를 뺀 두 경로의 변수 노드들이 공통 검사 노드를 갖지 않으면 (chordless 조건) S = {v_l} ∪ 두 경로의 변수 노드 집합을 I_k^k에 추가. 복잡도 O(n (dv dc)^k). 따라서 이 루틴이 반환하는 것은 chord가 없는 simple cycle입니다.
- Routine 6 DotSrch(I_k^a, I): 각 인스턴스 S에 대해 V\S 중 Γo(S)의 검사 노드와 2개 이상 연결되고 Γe(S)와 연결이 없는 변수 노드 v를 모두 찾아 S ∪ {v} 추가. 결과에서 I를 뺌. 복잡도 O(N_{a,b} b^2 dc^2).
- Routine 7 PathSrch(I_k^a, I, EX, m): EX가 pa_m을 요구하는 인스턴스 S마다 각 c_k in Γo(S)에서 시작하는 Tanner graph 경로 집합 PA_k (길이 m으로 표기되어 있으나 Tanner graph 상의 길이 정의는 txt에서 불명확. 변수 노드 m개를 얻는 경로라는 것이 취지, 정확한 간선 수는 미확인)를 구하고, 서로 다른 c_k, c_j in Γo(S) 쌍에 대해 두 경로가 같은 노드에서 끝나고 그 노드가 유일한 공통 노드이며, 두 경로의 변수 노드와 검사 노드가 G(S)에 없으면 S ∪ (두 경로의 변수 노드) 추가. 복잡도 O(N_{a,b} b^2 (dv dc)^m).
- Routine 8 LolliSrch(I_k^a, I_c^c, I, EX, m): d = m + 1 - c. EX가 lo_m^c를 요구하는 인스턴스 S마다, Γo(S)의 검사 노드 c0 중 G(S)와 c0 외에 공통 노드가 없는 것에서 시작하는 길이 2(d-1) 경로 집합 PA를 구함. 입력 simple cycle 집합 I_c^c 중 G(S')가 G(S)와 공통 노드가 없는 S'에 대해, 경로가 S'의 Γo(S') 검사 노드에서 끝나고 그 검사 노드가 경로와 Γo(S')의 유일한 공통 노드이면 S ∪ (경로의 변수 노드) ∪ S' 추가 (줄 7 "pa ∪ G(S')"의 정확한 의미는 txt 손상, 위는 취지). 복잡도 O(N_{a,b} N_c b c (dv dc)^d).
- 종료: 모든 k 에 대해 a가 a_max에 이르면 종료. 별도의 b 필터링 문구는 알고리즘 본문에 없음 (b <= b_max 필터는 EX 표 구성으로 간접 보장. 실제 출력 시 b 계산해 거르는 것은 추정).
- 메모리: 한 클래스의 인스턴스 저장량 O(a N_{a,b}).

## 절 5. 특성화 표 (dv=3, dv=4)

- 표 읽는 법 (Tables VI-VIII 설명 문단): 열은 a, 행은 b. 각 (a,b) 칸의 위쪽 항목(점선 위)은 그 클래스 LETS의 부모 simple cycle과 괄호 안 비동형 구조 수 (예 s_i(x), s_j(y) -> x+y개 구조). 아래쪽 항목은 그 클래스의 모든 구조에 적용할 확장 (예: dot, pa_m, lo_m^c). "-" 단독은 불가능 클래스(위쪽) 또는 확장 없음(아래쪽). 이중선 아래(b > b_max)는 구조 수 미기재. 굵은 s_k 가 필요한 prime cycle.
- Table II (dot 기반, dv=3, g=6, a ≤ 9, b ≤ 9) 읽는 예: (7,5) 클래스 = s6(3), c7(1), n7(2), 총 6개 구조. 칸 값은 표 손상.
- Table III (dot 기반, dv=3, g=6, 10 ≤ a ≤ 12, b ≤ 5): 예시로 (11,1) 클래스 비동형 구조 114개, 부모는 s6 50, s7 26, c7 10, n7 7, s8 4, c8 6, n8 9, n9 2개로 분해됨. 나머지 칸 표 손상. 본문 사실: dv=3, g=6의 dot-prime은 s3, s4, s5, s6, c6, n6, s7, c7, n7 등. (4,4)는 s4 (dot으로 안 나옴). (6,6)에 s6, (6,4)에 c6, (7,5)에 n7 2개 (c7은 1개).
- Table V (dv, g, a_max, b_max별 요약, 표 손상): 열 4, 7, 10 이 각각 Table VI, VII, VIII. 본문에서 복원된 것:
  - Table VI: dv=3, g=6, a_max=10, b_max=3. 필요 cycle s3, s4, s5. 필요 확장 dot, pa2, pa3, lo_3^3, lo_4^3, lo_4^4. 생성해야 하는 b 최대는 5 (dot 방식은 a ≤ 8, b ≤ 8 필요, Example 7). 중간 부호율 0.3-0.7, n < 8000 용도 (Example 9).
  - Table VII: dv=3, g=8, a_max=12, b_max=4. (8,4) 클래스는 구조 10개(9개는 s4 부모, 1개는 s5 부모), 여기에 dot과 pa2를 적용하면 (9,1), (9,3), (10,4) 클래스를 만듦 (Example 10).
  - Table VIII: dv=4, g=6, a_max=10, b_max=10. s6은 새 구조를 못 만들어 prime으로 넣지 않음 (Remark 5).
  - 그 외 조합의 표는 저자 기술 보고서 [14]에 있다고만 되어 있음.
- 표를 직접 쓰지 않아도 되는 이유: 표는 Algorithm 1의 출력이라 Python에서 같은 알고리즘으로 재생성 가능(geng 필요, 추정). 또는 표 없이 "모든 클래스에 dot, pa_m, lo_m^c를 모두 적용하고 b'<=상한 가지치기" 방식으로 대체 가능하나 완전성 증명은 표 기반(추정).

## 절 6. 실험 표와 한계 (V, VI)

- 부호 목록은 Table IX (표 손상). 본문으로 복원한 부호: C1 dv=3, g=6, R=0.87, n=16383 (a ≤ 8, b ≤ 3, 약 27분, 필요 cycle s3, s4만). C2, C3 (3,6) 정규 n=816, 1008 (a ≤ 12, b ≤ 5, 각 16분, 14분. a ≤ 10, b ≤ 3은 약 20초). C4 (3,6) n=20000 (a ≤ 12, b ≤ 5, 약 9분, s6까지만 열거. dot 방식은 s10, s11 필요해 1일 이상 또는 8GB 초과). C5 Tanner (155,64) dc=5, g=8 (a ≤ 12, b ≤ 4, 442초. a ≤ 10, b ≤ 4는 28초 대 dot 392초). C6, C7 PEG (3,6) (a ≤ 12, b ≤ 4, 561초, 157초. a ≤ 10, b ≤ 4는 38초, 17초 대 dot 1563초, 1466초). C8 Margulis (2640,1320) g=8 (a ≤ 14, b ≤ 6, 약 42분). C9 dv=4, g=6, n=16383 (a ≤ 8, b ≤ 6, 133분. a ≤ 6, b ≤ 4는 3분). C10 (4,8) 정규 g=6, n=8000 (a ≤ 10, b ≤ 10, EAS 없음. a ≤ 9, b ≤ 8은 4분. dot은 s7 열거만 10시간 초과). C11 (5,10) 정규 g=6, n=816 (a ≤ 9, b ≤ 11, 약 6분).
- 실험 환경: 2.4GHz CPU, 8GB 메모리 데스크톱. 찾은 LETS 수는 표 X-XVII 칸이라 표 손상. 몇 개 본문 값: C1 (7,1) 37개 (s3 자식 34, s4 자식 3), (7,3) 250,466개. C4에서 (4,2), (5,1), (6,2), (7,1), (8,2) 클래스는 LETS 0개. C2/C3 FEAS 대 [21]의 FAS 결과는 4개 클래스에서 다름(저자는 오타 또는 비기본 AS 탓으로 추정).
- 예시 수치: Example 5, 4의 (3,6) n=20000 부호는 s3 161개, s8 6,219,941개; prime 크기 8, 9 구조 합이 6천만 개 이상(dot 방식 한계).
- 복잡도: cycle 열거 O(n (dv dc)^k) (n에 선형, 길이에 지수). 확장은 절 4의 식. N_k는 n에 거의 무관하고 degree와 k에 따라 급증(경험적, [19] 인용). 메모리 O(a N_{a,b}).
- 한계 (본문 직접): variable-regular 가정(dv 고정), g > 4 (4-cycle 없음, 본문 "g ≥ 6" 적용), 연결된 ETS만(비연결은 합집합으로 처리), LETS에 한정(leaf가 있는 ETS와 비기본 TS는 이 논문 범위 밖; leaf 있는 ETS는 2017 논문이 다룸), 구조적 부호의 automorphism은 활용 안 함. 표는 "제안일 뿐 최적이라 주장하지 않음". a_max, b_max는 사용자가 정해야 하며 우세 클래스를 포함하도록 부호율과 길이에 맞춰 선택. 복잡도는 N_k와 N_{a,b} 폭증에 취약.
- 보조: 기존 [18] Karimi 알고리즘은 완전성 보장이 없고, C5, C6, C8의 일부 클래스((9,3), (11,3) 등)에서 인스턴스를 놓쳤다고 보고.

## 절 7. Hashemi 2017 irregular 차이점

- 시작 구조: simple cycle 외에 degree b 이하의 단일 변수 노드(ETSL 탐색용 시작, 2절 Algorithm 1 줄 3-5).
- 표현: normal graph만으로는 irregular에서 변수 degree 정보가 사라져 quasi-normal graph 도입. 모든 검사 노드를 간선 하나로 대체하되, 검사 노드가 degree 1이면 한쪽이 열린 singly-connected 간선으로 남겨 변수 degree를 보존. 같은 normal graph에 여러 quasi-normal 구조가 대응.
- 확장 클래스 변화 (Proposition 3): dot_m^k (루트 degree k, 2 ≤ m ≤ k) -> (a+1, b + k - 2m). pa_m -> (a+m, b - 2 + sum_{i=1..m}(dv_i - 2)). lo_m^c -> (a+m, 같은 식). dv_i는 확장에 쓰인 노드 각각의 degree.
- 최소 b (Proposition 4): dot -> (b + min{z - 2a, -y})+; pa -> (b - 2 + m(dv_min - 2))+; lo -> (b - 2 + (m-1)(dv_min - 2) + d - 2)+. y = a 이하 최대 변수 degree, z = a 초과 최소 변수 degree, d = dv_min (dv_min > 2일 때) 또는 2 초과 최소 degree (dv_min = 2일 때).
- 보조 결과: Lemma 1은 (a,b) LETS 범위에서 변수 노드 degree < a_max + b_max. Lemma 2는 degree 최대인 s_a가 b = a(dv_max - 2)로 최대, 범위 내에서는 η = (a_max + b_max 미만 최대 degree)로 a(η - 2). Proposition 1, 2: variable-regular LETS는 irregular의 사영(투영). Theorem 1 (정규 부호 표 재활용): t = a_max 미만 최대 degree로 정규 dv = t 의 표를 b ≤ b_max + a_max(t - dv_min) 까지 만들면 충분. 단 a_max나 t가 크거나 degree-2 노드가 있으면 범위가 폭증해 비실용.
- 대안 (Theorem 2, 이쪽이 실제 방식): 클래스 기반 후방 재귀로 크기별 b 상한 b_max^a = min{ b_max^{a+1} + max{y, 2a - z}, a(η - 2) }, 초기 b_max^{a_max} = b_max (z는 a 초과이고 a_max + b_max 미만인 최소 degree). dot은 a ≤ a_max - 1 인 모든 클래스에, pa_m과 lo_m^c는 a ≤ a_max - m 에 적용하되 결과 b가 상한 이하일 때만. 탐색에서는 인스턴스마다 변수 index와 (정규 사영 클래스 사용 시) 그 클래스를 보관하고, 확장 뒤 결과가 범위 안인지 검사.
- ETS with leaf(ETSL): leaf 있는 ETS는 LETS를 부분 구조로 포함하는 ETSL1과 포함하지 않는 ETSL2로 나뉨. ETSL1은 가장 큰 LETS 부분 구조에 dot_k^1 (m=1)을 반복 적용해 얻음 (Proposition 5). 적용 조건: dv_min - 2 ≤ i ≤ b_max - 1 인 i마다 b = b_max - i 이고 a ≤ a_max - 1 인 LETS와 ETSL1에 k ≤ i + 2 인 dot_k^1. ETSL2는 트리이며 degree ≤ b_max 인 단일 변수 노드에 dot_k^1 반복 (Proposition 6). Algorithm 1(ETSL): 입력 G, a_max, LETS 인스턴스 I, g. 줄 3-5 I_tem^{1,b}에 degree b 변수 노드 집합. 줄 6-16 a=1..a_max-1, b=1..b_max 마다 I_tem^{a,b} ∪= I^{a,b}; 각 구조 S에 대해 V\S 중 degree ≤ b_max + 2 - b 이고 Γo(S)에 정확히 하나만 연결, Γe(S)에는 연결 없는 v에 대해 I_ETSL^{a+1,b'} 와 I_tem^{a+1,b'} 에 S ∪ {v}, b' = b + deg(v) - 2. 출력 I_ETSL. 조건 dv_min ≥ 2. ETS 완전 탐색은 이를 LETS 탐색과 합침.
- 실험 (표 I, 범위 a ≤ 10, b ≤ 2): IEEE 802.16e girth 6 부호 두 개(n=576, 1056)와 PEG girth 8 (n=504, degree 2,3,4,5,7,14,15). 예: C1 (10,2) ETS 1560개 LETS 168개, 시간 38분, 18분, 20분. [1] Falsafain 결과와 ETS 수 완전 일치. [1]은 41, 189, 273분. 복잡도가 block length 증가 시 줄어드는 경향(차수 분포 고정)이라고 주장.

## 절 8. Karimi 2012 Algorithm 1 (손상 많음)

- 목적: 초기 ETS 목록(입력 짧은 cycle 등)에서 변수 노드를 붙여 크기 a_max 이하이고 불만족 검사 노드 수가 상한 b_max 이하인 더 큰 ETS를 모두 모으는 한 단계 확장. 입력: 입력 ETS 목록, 그래프 G, 최대 크기와 불만족 검사 노드 상한(기호는 txt에서 소실: 줄 19의 b 문턱), 깊이(layer) 상한 ℓ(줄 8, 기호 소실). 출력: 확장된 ETS 목록 (줄 24).
- 의사코드 골격(기호 소실로 복원 가능 부분만):
  - 3 repeat: 4. 입력 목록에서 ETS 하나 S를 선택.
  - 5. S의 변수 노드, 간선, S의 이웃(만족 검사 노드 포함, Remark 1: Lemma 2-4에 의해 만족 검사 노드와 그 이웃 변수는 확장에 쓰일 수 없음)을 G에서 제거해 새 그래프 G' 생성. (비기본 TS 확장은 이 줄을 "S의 노드와 간선만 제거"로 변경, 즉 인접 노드는 남김.)
  - 7-16. Γo(S) 속 각 노드(불만족 검사 노드)에서 G' 이웃을 한 층씩 최대 ℓ층까지 살펴 S의 다른 불만족 검사 노드로 가는 경로(경로상 새 변수 노드 수 최소), 또는 거기서 시작하는 lollipop walk를 찾음. 모든 후보 중 가장 짧은 것들만 집합에 모음.
  - 17-22. 모인 각 후보를 S에 붙인 결과가 조건 (b 문턱과 크기 조건)을 만족하면 출력 목록에 추가.
  - 23. 입력 목록의 모든 원소를 처리할 때까지 반복.
- 원리 (Lemma 2, 3, 4): S보다 큰 ETS S''에서 S''\S의 변수 노드는 S의 불만족 검사 노드에만 연결. 크기 차 1이면 새 노드 하나가 불만족 검사 노드 2개 이상에 연결(dot), 크기 차 2이면 두 노드 구성이 Fig. 3(b)(girth > 4일 때 유일). 입력 ETS 중 같은 크기의 부분집합이 있어야 도달 가능.
- 입력 선택: girth g 일 때 길이 g와 g+2의 cycle (예: 6, 8) 정도가 대부분 충분. 희소 그래프는 g+4까지 필요. Remark 6: 초기 크기와 포함하는 최소 ETS 크기의 차이가 보통 작음.
- 한계: 완전성 보장 없음 (Remark 3: 한 번의 적용은 포함하는 가장 작은 ETS를 모두 찾지만 재귀 적용으로 모든 포함 ETS를 얻는다는 보장은 없음. Example 3). 문턱 b는 복잡도 억제용 (Remark 2).
- 복잡도: cycle 열거 O(n(dv dc)^k), 확장은 평균 degree에 지수적으로 증가, block length에는 덜 민감 (n ≈ 10000까지 실용적이라고 주장). 구체 식은 소실.
- irregular 확장: degree 2 변수 노드가 없으면 수정 없이 사용, 있으면 초기 집합을 보강(Algorithm 2: 2-chain 등, Algorithm 3: 1, 2 결합). Algorithm 2, 3 내용은 읽지 않음, 미확인.

## 절 9. Python 구현 시 주의점

논문에서 직접 언급:
- 인스턴스는 변수 노드 index 집합으로 저장하고 매 단계에서 이미 찾은 집합 I를 빼서 중복 제거 (Routine 6-8의 I_tem \ I).
- cycle 열거 비용이 n에 선형이고 길이에 지수적이므로 K를 작게 유지. girth 6이면 s3부터, dv=3 b_max=3이면 s3, s4, s5만 필요 (Table VI 경우).
- dot 확장은 Γo(S)에만 연결되고 Γe(S)에 연결 없는 변수 노드 후보를 쓰므로 후보 검사가 O(b dc).
- path 확장 시 새 경로의 변수와 검사 노드는 G(S)와 겹치면 안 됨. 두 경로가 끝 노드만 공유.
- lollipop 확장은 입력 cycle 집합 I_c^c 와 결합해 구현 (cycle을 다시 찾지 않고 재사용).
- 비동형 구조 분류 대신 클래스 (a,b)별 EX 표만 있으면 탐색이 진행됨. 표 생성이 번거롭지만 geng 호출이나 사전 계산 표 필요.
- 구조적 부호의 대칭을 이용하지 않아도 되지만 실제 수행시간은 길다 (예: C8 42분, 데스크톱 C 구현으로 추정되나 언어는 논문 미언급).

추정(논문에서 직접 언급 안 함):
- a_max, b_max를 크게 잡으면 s_k 열거와 N_{a,b} 폭증으로 Python에서 즉시 한계. 인스턴스는 정렬된 tuple 또는 frozenset으로 해시 집합 관리, 검사 노드 인접 리스트와 변수 노드 인접 리스트를 numpy 배열이 아닌 Python set으로 두면 구현 단순.
- 우리 H가 QC-LDPC로 변수 degree가 열마다 다르면 2017 irregular 방식(Theorem 2의 b 상한 재귀)을 써야 하며, 이때 클래스별 확장 선택은 Proposition 3의 식으로 b 예측이 가능.
- Python 이식 시 첫 검증은 논문 C5 Tanner (155,64)의 (8,2)와 (10,2) 클래스가 우세하다는 사실, 그리고 Table XIII 값(표 손상이라 직접 비교 불가)을 PDF 원본에서 확인하는 것.
