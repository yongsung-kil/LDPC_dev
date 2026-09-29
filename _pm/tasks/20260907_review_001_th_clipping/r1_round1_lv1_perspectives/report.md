## Round 1 결과: 관점 리스트업

작성 시각: 2026-09-07 22:50:14 이후 (에이전트 2개 취합)

에이전트 1은 관점 13개, 에이전트 2는 관점 13개를 냈다. 겹치는 것을 합치고 다섯 묶음으로 정리했다.

도출된 관점:

| # | 관점명 | 확인 항목 | 대상 파일/범위 |
|---|--------|----------|--------------|
| A1 | 양자화 모델 대 본체 동작 | raw 정의(sum_t - 자기 C2V), 캐스케이드 방향(아래 레벨부터 덮어쓰기 대 정방향 첫 매칭), 비단조 th 유무, 절댓값 비교와 부호 결합, \|raw\| 최댓값 ch + (dv-1)×7의 성립 조건 | decoder.py `_vnu_quantize` `_process_column`, llr_matrix.py `_validate`, th_as_clip.py `v2c_cap`, th_softness.py |
| A2 | min2 = RESET 승격과 C3 모델 | min1 교체 시 min2가 RESET(7)이 되므로 "둘째 최솟값 상한 = min2 상한" 모델이 성립하는지, min1_pos 초기값 -1의 효과, "min1 = 7"과 "min1 = min2 = 7"의 동일성(C10 ㉯의 전제) | decoder.py `_cnu_update` `_c2v_reconstruct` `_init_state`, th_as_clip.py caps 정렬부, 002 실험로그 인사이트 ㉮ |
| A3 | 정적 상한 모델의 한계 | column 직렬 제자리 갱신(같은 iteration 안 혼합 상태), iteration 1의 RESET 초기 구간, 그룹 경계의 iteration 간 결합, 상한 하락의 고정점(1회 통과 대 반복) | decoder.py `_run_iteration` `_process_column`, th_as_clip.py |
| A4 | 하위 임계값 th2, th3의 반대 방향 효과 | th3 ≤ 0 칸(최소 레벨 도달 불가), th2 < ch 칸(채널만으로 레벨 5)의 분포, 레벨 분포가 위로 밀리면 클리핑 개입 여지가 늘어나는 함의를 메모가 다뤘는지 | th_softness.py, 메모 C2 C4 |
| A5 | 균일 기준선 비교의 공정성 | th = [7,5,3] 기준선은 ch도 균일이라 need7 비교에 ch 차이가 섞이는지 | th_softness.py, llr_matrix.py `edge_quantization_levels` |
| B1 | 수치 재현 | 스크립트 4개 실행 결과와 메모 C2~C5 숫자 대조, 파일 서술(그룹, row, max_iter, 레벨, base 치수, degree 분포), 파싱 순서(dv_from 순 (ch, th1, th2, th3)) | 스크립트 4개, 메모 분석 대상 절 |
| B2 | CSW row 선택과 대표성 | `row_index` 순회 방향과 "임계값 초과 시 그룹 첫 row" 전제, 메모가 지목한 두 row가 실제 도달 가능한지, 57 row 균등 취급(228칸, 중앙값)이 실제 선택 빈도로 가중하면 달라지는지, row 1개 그룹의 iteration 분기 예외 | llr_matrix.py `row_index` `_group_of_iter`, 메모 C2 C3 C4 C5 |
| B3 | 정보 구간과 패리티 구간 | 뒤쪽 15개 column block의 degree, dv2 열이 판정 범위 밖이면 C2 C3의 dv2 관련 칸이 FER에 무관한지, 001 실험로그 인사이트 ㉱와 같은 구조인지 | decoder.py `_collect_error_metrics`, pcm.py 배치 전제, 실험로그 69~71행 |
| C1 | 반전 가능 조건 정본과 동점 | 세 후보(Q + (dv-1)P, dv·P, dv·Q)의 전제와 001 관측 대응, `_vn_decide` 동점 반전 대 flip_check.py의 `<=` 취급, flip_check.py 결과가 메모 본문에 인용되지 않은 점 | flip_check.py, 001 README 결론 ㉮, 실험로그 63~66행, decoder.py `_vn_decide` |
| C2 | 사전 지표의 이식성 | edge 레벨 집합({15,11,7,3} 대 {7,5,3,1})과 dv 분포가 다른 환경 사이에서 ch/(edge상한×dv)를 같은 축으로 읽어도 되는지, 지배 dv 기준인지 전 dv 중앙값인지, 관측점 3개 남짓 위의 결론 강도 | llr_headroom.py, 001 README 결론 ㉱, 메모 C5 |
| D1 | 논문 정합성 | 정규화 계수 alpha 부재, L = 2^(a-1) - 1과 edge 상한 7의 대응(가이드 P = L/4, Q = L/2가 어느 쌍이 되는지), 동점 시 단일 표시, 비트폭 이득 범위(CN 상태 저장 폭 포함 여부), 적용 시점 등가(001 docstring) | 논문 txt 154~196행, 230~235행, 001 decoder.py, 메모 C6 C9 |
| D2 | th 대 P, Q의 개념 대응 | 작용 지점(VN 출력 재양자화 대 CN 출력 상한), 비대칭의 성격(송신 dv별 대 수신 역할별), RESET 승격이 만드는 역할별 비대칭과의 겹침, 4레벨에서 서로 다른 (P,Q) 조합 수 | 메모 C3 C6, 001 decoder.py, decoder.py `_c2v_reconstruct` |
| D3 | 001과 002 인용 | 이득 환경과 손해 환경 구분, 결론 ㉰(같은 P에서 Q 증가 시 개선)의 성격, 002 인사이트 ㉮(RESET 승격)와 ㉰(결합 최량)의 반영, max_iter 20 대 120 차이 | 001 README, 002 README, 실험로그 |
| E1 | C7과 C8의 논리 | "클리핑 없는 디코더 기준 튜닝" 전제의 확인 가능성과 문장 규칙 충돌, 증거 비대칭(양성 강함, 음성 약함) 명시 여부, 사후 적용과 완전 재최적화 사이의 중간 경로(py에서 클리핑 켜고 ch/th 국소 재탐색) 검토 여부, DAO_Main.py 세 행 인용 정확성 | 메모 C7 C8, DAO_Main.py 454 898 7937행, 5_DAO README |
| E2 | C10 절차 | E 400~420 근거(기준 실행 390에서 9.8e-3, 실행 시간), 표본 256프레임의 분해능, 후보 쌍의 구별성과 논문 가이드 포함 여부, 포화 CN 비율의 정의와 판정 문턱, (3,7) (3,5)의 개입 조건 차이, config_target 슬롯과 scan.py 인자 | 메모 C10, config_target.json, scan.py, matrix_sel_1_HD_fixed Sim_Output |
| E3 | 대안 해석 | 이 시스템이 이미 가진 진폭 억제 경로(RESET, 그룹 배치, CSW로 후반 ch 낮추기)와의 기능 겹침, 실패 원인의 다른 후보(흡수 집합, 특정 dv 반전 불능)일 때 스캔이 답을 못 주는 갈래, 진단 지표 확장(min1 분포, sum_t 분포, dv별 오류 궤적), 001과 002 결합 경로 | 메모 전체, 002 README |
| E4 | 문서 규칙과 전달력 | 입력 파일 성격 서술 여부, 줄표와 가운뎃점, ㉮㉯ 나열, 용어 첫 등장 풀어쓰기, 두 질문에 대한 답이 한 자리에 모이는지, 어긋남 절이 어느 문서를 고칠지 제안하는지 | 메모 전체, CLAUDE.md 문장 규칙 |

## 다음 단계 결정

→ Round 2 (lv1, 에이전트 4개)
  사유: 관점이 17개지만 다섯 묶음이 서로 독립적이고 대상 파일이 겹치므로 flat 배정이 효율적이다. 묶음 A(메커니즘 대 모델)와 B(수치와 row 선택)가 C2 C3의 성립을 직접 정하므로 각각 전담 에이전트를 둔다.
  - 에이전트 1: A1 A2 A3 A4 A5 B3 (본체 코드 대 스크립트 모델)
  - 에이전트 2: B1 B2 C1 C2 (수치 재현, row 선택 대표성, 수식과 지표)
  - 에이전트 3: D1 D2 D3 E3 (논문과 001/002 인용, 개념 대응, 대안 해석)
  - 에이전트 4: E1 E2 E4 (결론 논리, 판정 절차, 문서 규칙)
