# H-matrix 사이클과 trapping set 조사 도구

> 작성: 2026-10-21 18:19:27
> 상태: 설계안 작성 완료 (사용자 결정 1건 대기: [판정요청_설계_261022.md](%ED%8C%90%EC%A0%95%EC%9A%94%EC%B2%AD_%EC%84%A4%EA%B3%84_261022.md))
> 변경 등급: Review (새 모듈 추가. `2_LDPC_base/src`는 수정하지 않고 상속으로 디코더 상태를 기록)
> 설계 정본: [설계.md](%EC%84%A4%EA%B3%84.md). 근거: [논문조사.md](%EB%85%BC%EB%AC%B8%EC%A1%B0%EC%82%AC.md), 알고리즘 노트 [A](%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98%EB%85%B8%ED%8A%B8_A_%EC%82%AC%EC%9D%B4%ED%81%B4%EC%84%B8%EA%B8%B0.md), [B](%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98%EB%85%B8%ED%8A%B8_B_trapping_set_%ED%83%90%EC%83%89.md), [C](%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98%EB%85%B8%ED%8A%B8_C_%EC%8B%A4%ED%8C%A8%EC%A7%84%EB%8B%A8.md)

---

## 목적

Python 도구 하나로 두 가지를 한다.

- ㉮ 실패 진단: 디코딩에 실패한 codeword(최대 반복 후에도 신드롬이 0이 아닌 출력)가 있을 때, 현재 H-matrix의 어떤 사이클이나 trapping set(디코더가 갇히는 변수 노드 집합) 때문에 못 고치는지 식별한다
- ㉯ H 조사: 현재 H-matrix의 사이클 구조(girth, 길이 4/6/8/10 사이클 수, 변수 노드별 사이클 수, ACE 분포)와 유해 구조(trapping set, absorbing set) 목록을 만든다

## 배경

- ㉮ 지금 저장소에는 [pcm.py](../../../../2_LDPC_base/src/pcm.py)의 `QCCode.count_cycles4()`만 있다. base matrix 위에서 순환 이동 값의 교대합 조건(Fossorier 2004)으로 길이 4 사이클 수를 센다. 길이 6 이상, 노드별 분포, trapping set 탐색, 실패 진단은 없다
- ㉯ 논문 아카이브(형제 저장소 `LDPC_Paper_Analysis`)에서 후보 1,565편을 선별한 결과, 기반 논문은 다음 셋으로 정했다 (상세와 보조 논문은 논문조사.md)
  - ㉠ 사이클 세기: Karimi, Banihashemi 2013 메시지 전달 알고리즘 (ieee:6336765). 정수 덧셈과 뺄셈만으로 길이 g부터 2g-2까지 노드별 개수를 정확히 센다
  - ㉡ trapping set 열거: Hashemi, Banihashemi 2016 leafless elementary trapping set 완전 탐색 (ieee:7575635). H만 입력이고, 길이 16383, rate 0.87, 열 가중치 3 부호에서 a≤8, b≤3 전수 탐색 27분 실측이 본문에 있다
  - ㉢ 실패 진단: Kang 외 2011 backtracking (ieee:5605921). 불만족 검사 노드 수가 최소인 반복의 상태를 저장하고 이웃 변수 노드를 뒤집어 재디코딩하는 결정적 절차. 보조로 Han, Ryan 2009 (ieee:5089505)와 Han 외 2022의 error path 정의 (ieee:9729722)
- ㉰ 성숙한 공개 Python 구현체는 찾지 못했다 (사이클 세기는 MATLAB과 C++, trapping set 열거는 노트북 하나). 직접 만든다
- ㉱ 모든 논문의 실측이 C++ 또는 MATLAB이라 순수 Python 속도는 미확인이다. numpy와 scipy.sparse 벡터화를 전제로 하고, 부족하면 미결정 ㉱에서 다룬다

## 설계 (초안. 모듈 구성, 알고리즘, 검증 계획, 단계별 구현 계획의 정본은 [설계.md](%EC%84%A4%EA%B3%84.md))

| 모듈 | 하는 일 | 기반 논문 | 입력 | 출력 |
|------|--------|----------|------|------|
| 사이클 조사 | girth, 길이별 사이클 수, 변수 노드별 사이클 수와 ACE 분포 | Karimi 2013 (ieee:6336765). QC 블록의 대표 노드만 시작해 순환 블록 크기만큼 절감 (Li, Lin 2015 ieee:7282488). 소형 H는 Halford, Chugg 2006 (ieee:1564444) 밀집 행렬 방식으로 교차 검증 | `QCCode` (base matrix, z) | 길이별 개수 표, 노드별 개수 배열 |
| trapping set 열거 | (a,b) 상한 안의 leafless elementary trapping set과 absorbing set 목록, 지배 구조 | Hashemi 2016 (ieee:7575635) 완전 탐색. 빠른 근사는 Karimi 2012 (ieee:6259854). 분류 이름은 Vasic의 trapping set ontology (ieee:5394825) | `QCCode`, (a_max, b_max) | 변수 노드 집합 목록과 (a,b) 분류, 사이클 골격 |
| 실패 진단 | 실패 샘플 하나에서 오류 변수 노드 집합, (a,b), 유도 부분 그래프, 그 안의 사이클, 안정형과 진동형, error path를 뽑고 열거 목록과 대조 | Kang 2011 (ieee:5605921), Han 2022 (ieee:9729722), Zhang 2009 (ieee:5336848) | 디코더의 반복별 hard decision과 신드롬, 송신 codeword | 실패 1건 진단 보고, 실패 N건 (a,b) 빈도표 |

진단 절차 초안 (논문조사.md 2절)

- 1. 실패 샘플 기록: 반복별 (불만족 검사 노드 집합, hard decision)을 보관하고 불만족 검사 노드 수가 최소인 반복을 고른다
- 2. 오류 변수 노드 집합 = 그 반복의 hard decision XOR 송신 codeword. 불만족 검사 노드 집합과 (a,b)를 산출한다
- 3. 유도 부분 그래프를 뽑아 검사 노드 차수 1(불만족)과 2(mis-satisfied)를 구분하고 elementary 여부와 absorbing 조건을 검사한다
- 4. 유도 부분 그래프 안의 최단 사이클과 사이클 공유 구조를 보고, 열거 모듈의 목록과 대조한다
- 5. 반복별 불만족 검사 노드 수와 오류 수의 주기성으로 안정형과 진동형을 나눈다
- 6. Kang의 backtracking대로 경계 변수 노드의 LLR을 뒤집어 재디코딩이 성공하는지 확인한다 (송신 codeword 없이도 되는 절차)
- 7. 실패 N건을 (a,b)와 동형 클래스로 묶어 빈도표를 만든다

디코더 연계: [decoder.py](../../../../2_LDPC_base/src/decoder.py)의 `BaseDecoder.decoder_main(channel_out, collect_profile=False, log=None)`에 이미 `collect_profile` 옵션과 `_record_iteration`이 있다. 실패 진단 모듈이 필요한 반복별 hard decision과 신드롬을 이 경로로 받을 수 있는지 설계 단계에서 확인하고, 부족하면 기록 옵션을 추가한다 (기본값 꺼짐).

## 수정 대상 파일

- ㉮ 신규: `4_H_matrix_tool/src/` 아래 모듈 3개 (파일 이름은 설계 문서에서 확정. 수단이 아니라 목적이 이름이 되게 짓는다)
- ㉯ 수정: [decoder.py](../../../../2_LDPC_base/src/decoder.py) (반복별 hard decision과 신드롬 기록 옵션이 부족할 때만, 기본값 꺼짐)
- ㉰ 수정: [README.md](../../../README.md)의 파일 표에 모듈 3개 추가
- ㉱ 유지: [pcm.py](../../../../2_LDPC_base/src/pcm.py)의 `count_cycles4()` (길이 4 결과의 교차 검증 기준으로 쓴다)

## 안전성 체크리스트

- [ ] 디코더 기록 옵션은 기본 꺼짐이고, 끈 상태의 FER 결과가 비트 단위로 이전과 같다
- [ ] 길이 4 사이클 수가 `count_cycles4()`와 일치한다
- [ ] 소형 H에서 길이 6, 8 사이클 수가 Halford, Chugg 밀집 행렬 방식과 일치한다
- [ ] trapping set 탐색은 (a_max, b_max)가 필수 인자이고 시간 상한 옵션이 있다
- [ ] 진단 모듈이 뽑은 오류 변수 노드 집합의 신드롬이 디코더가 보고한 불만족 검사 노드 집합과 일치한다
- [ ] 문서, 주석, 로그에 입력 파일의 성격을 적지 않는다 (파일은 이름과 치수로만, 평가 대상은 "평가 대상 파라미터")
- [ ] 평가 대상 파라미터에서 모듈별 실행 시간을 측정해 설계 문서에 적는다

## 미결정 사항

설계 단계에서 설계자가 정한 것 (되돌리기 쉬움, 상세는 설계.md 9절)
- ㉮ 사이클 세기 알고리즘: Karimi 2013 메시지 전달 + QC 대표 노드로 z배 절감. QC 전용 다항식 방식은 열 가중치 혼합 H에 바로 맞지 않아 제외
- ㉯ trapping set 탐색 범위 기본값: a_max 6, b_max 2, 시간 상한 30분 (모두 인자, 실측 뒤 조정)
- ㉰ 실패 샘플 공급: 5_DAO RowStack의 실패 seed 파일 형식(`uncor_seeds.txt`, `info.json`)을 입력으로 받고 수집기도 같은 형식으로 씀. 실험 run과 src 수정 없음
- ㉱ 속도 보강: numpy만 사용 (시뮬레이터의 numba 미사용 결정과 같게). 1단계 실측 뒤 부족하면 판정요청

사용자 결정 대기
- ㉲ trapping set 탐색 방식 (확장 규칙 전부 적용 + b 상한 가지치기 / 논문의 특성화 표를 nauty geng으로 생성 / dot 확장만): [판정요청_설계_261022.md](%ED%8C%90%EC%A0%95%EC%9A%94%EC%B2%AD_%EC%84%A4%EA%B3%84_261022.md)

## 진행 기록

- 2026-10-21 논문 조사 완료 (후보 1,565편, 선별 보고서 4편), 작업 등록
- 2026-10-22 기반 논문 3편 알고리즘 노트 작성, 설계.md 작성, 구현자 관점 검토 질문 3건 반영, 판정요청 1건 발행
