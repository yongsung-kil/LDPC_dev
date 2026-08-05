# Round 2 결과: 분석 + 메인 최종 검증 (라이트 리뷰 종료)

> 2026-07-30. 에이전트 3개(Opus, lv1: A=사실 정확성, B=기술 타당성, C=실행 가능성).
> 라이트 리뷰이므로 Round 3 대신 **메인이 판정을 좌우하는 발견을 직접 코드로 검증**했다 (사용자 지시).
> 원문: agent_A.md / agent_B.md / agent_C.md

## 발견 요약: CRITICAL 1, HIGH 8(중복 통합 후 6), MEDIUM 다수, LOW 다수

## 메인 직접 검증 결과 (판정 좌우 발견)

| # | 발견 (에이전트) | 메인 검증 | 근거 |
|---|----------------|----------|------|
| 1 | **N_b=129는 오기 — 실물은 N_b=147, M_b=18, 129는 정보부(N_b−M_b)** (A-H1, B-M1, C-6) | **확인됨** | `decoder.cpp:185` HCU_start = N_b−M_b−punct = 127 → N_b−M_b=129. `main.cpp:601` H-matrix 폴더 `18_by_147_DvMax3`. 정보 129×256=33,024bit=4,128B≈4KB(사용자의 "4KB"=정보 길이), codeword 147×256=37,632bit, rate≈0.878. 루트/LDPC CLAUDE.md 상수표 자체가 자기모순(N_b=M_b=129인데 N_b−M_b=129) |
| 2 | **`Get_VNU_Table_Idx()`가 `return 0` 스텁 — "iteration별 LLR 테이블"은 현재 단일 세트** (A-H2, C-4) | **확인됨** | `decoder.cpp:7207-7209` |
| 3 | **CN 상태 명세 오류 — CN_STATE는 5필드(min1_pos/min1/min2/check_sum/syndrome), "old/new 2세트" 없음, edge별 sign 메모리 `Check_SRAM_sgn[M][K]`가 plan에서 누락** (B-H2, A-M) | **확인됨** | `1_LDPC_revised/decoder.h:30-36, 245` |
| 4 | **디코더는 signed-LLR이 아니라 flip/magnitude 도메인 — channel LLR은 비음수(0~31), 부호 정보는 Variable_mem(HD bit)+syndrome** (B-M5, C-7) | **확인됨** | `common.h:375-376` CH_LLR_MAX=31/CH_LLR_MIN=0, `decoder.cpp:4044-4045` "syndrome-aided decoding" — sum_t 부호로 HD 유지/flip 결정. channel.cpp는 read-bit/region까지만, LLR 값은 VN 단계 테이블 |
| 5 | **H-matrix 파일이 저장소에 없음** (C-2) | **확인됨** | Glob `**/H_Matrix/**` 0건. `main.cpp:594-651`은 `H_Matrix\18_by_147_DvMax3\` 상대경로 참조 — 외부 반입 자산 |
| 6 | **LLR 테이블 실값 부재 — 템플릿 값 공란, CH_3SD/TH_*는 소스 손상으로 소실** (A-M, C-3) | **확인됨** | `llr_tables_template.txt:23-24` 명시. "기 최적화 값 사용"은 사용자 값 공급 전까지 불가 |
| 7 | **파이프라인은 "알고리즘 무관"이 아님 — V2C store가 C2V 대비 지연되어 데이터 의존성 존재** (B-H1) | **확인됨(구조)** | `decoder.cpp:1488-1766` 같은 mn 루프에서 C2V는 col_P2, store는 prev_variable_node2 기준 — stage별 다른 column 동시 처리. 정확한 지연 깊이·의존 범위는 C1 단계에서 L2 문서+코드로 확정 |
| 8 | **genie 판정 ↔ "고정 iteration" 문서 내 표현 충돌, C++ vanilla와 채점 통일 필요** (B-H3, A-M) | **확인됨(문서 결함)** | plan.md §1#3 vs §7#1. 해소: "CRC 조기종료 제거 + 채점은 양쪽 모두 genie(매 iter 정답 비교)"로 통일 명시 |
| 9 | 예시 M_b≈13은 dv=17과 양립 불가(M_b≥17 필요) (B-M2; C는 "조합 가능" — 이견) | **확인됨(B가 옳음)** | base graph에서 column degree ≤ M_b. dv_max=17 쓰려면 M_b≥17. 실물 M_b=18 채택으로 해소 |
| 10 | C0~C3가 저장소에 없는 3종 자산(H-matrix·LLR 실값·빌드 가능 소스)에 동시 의존 (C-1 CRITICAL) | **확인됨** | #5·#6 + TODO.md Phase 0 빌드 BLOCKED. calibration은 사용자 빌드 환경+자산 공급 전제 — 계획에 명시해야 함 |

### 기타 (검증 생략, Round 2 요약을 정본으로 유지)
- z_sb=256 시 PMU factor(=z_sb/128) 경로 최초 활성화 — C++ 쪽 유의사항으로 기록 (B-H4)
- shift 순열 2종(정/역), np.roll 방향 주의 (B-L)
- GT 용어: 루트 CLAUDE.md·paper_screening_profile="Graph Thinning" vs LDPC/CLAUDE.md="Gaussian Trick" — 문서 간 불일치 존재(별도 정리 대상, plan 결함 아님) (A-L)
- §7#3 "검증 완료" 표현 과장(1_LDPC_revised는 부분 복사본·미빌드) (A-M, C-5)
- mpi.cpp 실제 MPI 코드는 main/ecc_top에 분산, Reduce 사용 (A-M)
- L2 문서 자체에 min2 갱신 비교연산 오류 가능성 — 권위는 decoder.cpp (B-M3)

## 종합 판정

**수정 필요 (문서 수정으로 해소 가능)** — 계획의 골격(2단계 하이브리드, vanilla 비교, py 벡터화+MPI)은 유효하나, 사실 오류(치수·CN 상태·LLR 도메인·channel 역할)와 전제 누락(외부 자산 3종, 파이프라인 의존성)을 plan.md에 반영해야 구현이 잘못되지 않는다. 수정 후 구현 진행.
