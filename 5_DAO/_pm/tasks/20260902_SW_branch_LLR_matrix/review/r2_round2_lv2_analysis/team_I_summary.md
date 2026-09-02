# 팀 I 요약: iteration 번호 체계와 빌드 갈래 (관점 2, 6, 7, 8, 12)

> 작성: 2026-09-03 01:20:25
> 팀 리더: 팀 I 리더 에이전트
> 워커: [worker_I_1.md](worker_I_1.md)(관점 2, 7), [worker_I_2.md](worker_I_2.md)(관점 6), [worker_I_3.md](worker_I_3.md)(관점 12), [worker_I_4.md](worker_I_4.md)(관점 8)
> 리뷰 대상은 코드가 아니라 코드 수정 계획 문서 두 개다. 아래에서 "수정 후 코드"는 [code_diff.md](../../code_diff.md)의 수정 후 블록을 그대로 적용한 상태를 뜻한다.

---

## ㉮ 워커 결과 요약 표

| 워커 | 관점 | CRITICAL | HIGH | MEDIUM | LOW | 문제 없음 | 핵심 발견 한 줄 |
|------|------|----------|------|--------|-----|----------|----------------|
| I_1 | 2 배경 메모 정합, 7 MN 배열과 iteration 번호 | 0 | 1 | 6 | 3 | 4 | iteration 1~4 구간의 분기 여부와 문턱 130이 메모, 파일, code_diff 세 곳에서 다르고 미결정에 없다. `ITER_MAX_HBF`를 4로 하면 실행 iteration이 120회로 줄고 `MN[]`에 음수가 생긴다 |
| I_2 | 6 `ITER_MAX_HBF` 딸린 곳 전수 | 0 | 1 | 5 | 2 | 5 | 표 밖 히트 가운데 [decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp)만 AUTO 빌드에서 실제 실행되며 PCRC 종료 시점을 바꾼다. "12곳"은 표(13곳)와도 소스(49곳)와도 맞지 않는다 |
| I_3 | 12 `__AUTO_LLR_OPT__` 분류 재검토 | 0 | 1 | 4 | 2 | 6 | 6.3으로 넘긴 것 가운데 `ecc_top.cpp:652, 680, 944-950`(결과 출력) 하나만 조건부 오분류다. 6장 전수 목록에서 `m_log_CSW_auto` 네 블록이 빠졌다 |
| I_4 | 8 비AUTO 빌드 안전성과 스위치 조합 | 2 | 2 | 7 | 1 | 0 | code_diff 8.1과 8.2가 비AUTO 갈래를 지우면 `m_param_LLR`을 미초기화 포인터인 채 역참조한다. 비AUTO 2SD, 3SD의 restart 지점 여덟 개가 사라진다 |

용어: BF는 Bit Flipping(1bit precision으로 도는 HD 복호 초기 모드), HD는 Hard Decision, SD는 Soft Decision, PCRC는 Partial CRC, SW는 Syndrome Weight(신드롬 무게), CSW는 Check Sum Weight, TV는 Test Vector, VNU는 Variable Node Unit, MN은 디코더의 iteration 상한 배열이다.

---

## ㉯ 교차 분석

### 1. `MN[]`에 음수가 들어가 결과 파일의 iteration별 FER 열이 깨진다 (HIGH)

- 위치: 상위 문서 5.5, [code_diff.md 3.5](../../code_diff.md#ch3)
- 근거: [local_opt.cpp:118-131](../../../../../../0_LDPC_original/src/local_opt.cpp)이 `MN[i] = i`로 채운 뒤 HD에서 전 원소에 `-= ITER_MAX_HBF`를 걸고 `MN[0]`만 되돌린다. `ITER_MAX_HBF`가 4가 되면 `MN = [4, -3, -2, -1, 0, 1, ..., 118, 120]`이다. [ecc_top.cpp:877-879](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `if (o_iter_num > MN[n]) fr_4KB[n]++`가 열 1, 2, 3에서 모든 프레임을 세고, [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp)이 열 머리글에 `4 -3 -2 -1 0 1 ...`을 찍는다
- 열 개수 판정: 항상 1.0이 되는 열은 1, 2, 3 세 개다. 열 4는 `MN[4] = 0`이라 "iteration 0에서 끝나지 않은 프레임 비율"이 된다 (워커 간 상충 2 참조)
- 처방: ㉮ 보정식을 음수가 나오지 않게 고치거나, ㉯ AUTO에서도 비AUTO처럼 검사점 다섯 개로 바꾸거나, ㉰ 지금 배열을 두고 열 배치를 문서에 적는다. **㉮와 ㉯는 동작 변경을 요구한다** (㉯는 결과 파일의 열 수가 124에서 5로 바뀌어 DAO 파싱까지 걸린다)
- 지적한 워커: I_1(3-5), I_2(F1), I_3(발견 1). 팀 P의 6번 항목과 같은 뿌리이며, 팀 P는 DAO가 읽는 `avg_iteration` 척도 변경 쪽을 짚었다
- **Round 3 검증 필요.** 이유: HIGH이고 처방 세 갈래가 서로 다른 동작 변경을 요구한다. 사용자 결정(I_1 D5)이 붙는다

### 2. code_diff 3.5가 `local_opt.cpp:124-131`을 다루지 않고, 그 안의 `MODE_DEC_1_SSD`는 정의가 없다 (CRITICAL 빌드 시점, 겸 MEDIUM 문서 누락)

- 위치: [code_diff.md 3.5](../../code_diff.md#ch3)(제목이 "116-123행"), 상위 문서 5.5 표의 `local_opt.cpp:126-130` 행
- 근거: 리더가 저장소 전체를 grep해 재확인했다. `MODE_DEC_1_SSD`는 [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp) 한 곳에만 나오고 정의가 없다. 정의된 이름은 [common.h:78](../../../../../../0_LDPC_original/src/common.h)의 `MODE_DEC_1_5SD`이며 나머지 57곳이 모두 이 이름을 쓴다. [local_opt.cpp:1-9](../../../../../../0_LDPC_original/src/local_opt.cpp)에 `#if defined(__AUTO_LLR_OPT__)` 가드가 없으므로 이 파일이 들어가는 빌드는 컴파일되지 않는다
- 이 블록이 없으면 `MN[MN_num - 1]`이 120이 아니라 124로 남아 BF 미진입 프레임이 mn 128까지 돌고, [decoder.cpp:7048-7050](../../../../../../0_LDPC_original/src/decoder.cpp)의 `selected_group = -1` 오류 출력에 빠진 뒤 row 0으로 복호한다. 곧 블록은 지우면 안 되고 살려야 한다
- 처방: ㉮ 3.5에 "124-131은 살린다"를 적고 ㉯ 조건의 두 번째 항을 `MODE_DEC_1_5SD`로 고친다. **㉯는 코드 수정이며, 1.5SD 프레임이 MN 보정을 받게 되므로 동작 변경을 뜻한다** (의도는 원래 그것으로 보이나 근거가 소스에 없다)
- 지적한 워커: I_1(3-3), I_3(발견 1의 일부). 리더가 grep으로 재확인
- **Round 3 검증 필요.** 이유: 계획이 원인이 아닌 기존 손상이지만 처방이 식별자 변경(동작 변경)이고, 외부 환경의 소스가 이 줄에서 다를 수 있어 재현 조건이 불확실하다

### 3. 비AUTO 빌드에서 `m_param_LLR`이 미초기화 포인터인 채 역참조된다 (CRITICAL 실행 시점)

- 위치: [code_diff.md 8.1, 8.2](../../code_diff.md#ch8)
- 근거: `ECC_Top` 생성자([ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp))의 포인터 초기화 목록에 `m_param_LLR`이 없다. 4인자 `Init_ECC_Top`([ecc_top.cpp:197-210](../../../../../../0_LDPC_original/src/ecc_top.cpp))은 이 포인터를 세우지 않고 208행에서 그 값을 넘긴다. `Decoder::m_param_LLR`에 대입하는 곳은 5인자 `Init_Dec`인 [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp) 하나뿐이다. 비AUTO 진입점 [main.cpp:105](../../../../../../0_LDPC_original/src/main.cpp)와 [main.cpp:127](../../../../../../0_LDPC_original/src/main.cpp)은 둘 다 4인자 오버로드를 부른다. `Is_Iter_Type_Edge_Clear`와 `Is_Iter_Type_Init`은 컴파일 스위치 없이 매 iteration 불린다([decoder.cpp:712, 2314, 2578, 5700](../../../../../../0_LDPC_original/src/decoder.cpp) 등)
- 처방: 두 함수의 `#if defined(__AUTO_LLR_OPT__)` 갈래를 유지하거나, 포인터를 `NULL`로 초기화하고 널 검사를 넣는다. **이 처방은 code_diff 8.1과 8.2가 요구한 코드 삭제를 되돌린다** (기존 동작 보존)
- 지적한 워커: I_4(F1) 단독
- **Round 3 검증 필요.** 이유: CRITICAL이고 단일 워커 지적이며, 처방이 계획의 핵심 방향(AUTO 갈래로 통일)을 되돌린다

### 4. 비AUTO 2SD와 3SD의 restart 지점 여덟 개가 통째로 사라진다 (HIGH)

- 위치: [code_diff.md 8.1, 8.2](../../code_diff.md#ch8)
- 근거: 비AUTO 원본은 edge clear([decoder.cpp:6577-6593](../../../../../../0_LDPC_original/src/decoder.cpp))와 init([decoder.cpp:6633-6669](../../../../../../0_LDPC_original/src/decoder.cpp))에서 `RSP1_2SD_PRIME_1 = 241`, `RSP1_2SD_PRIME_2 = 581`, `RSP1_3SD_PRIME_1..6 = 171, 312, 653, 844, 1035, 1301`([common.h:679-686](../../../../../../0_LDPC_original/src/common.h))을 쓴다. AUTO 갈래는 이 자리를 `m_param_LLR->restart_iter[]`로 대체하는데 비AUTO에는 LLR matrix 파일이 없어 배열이 채워질 경로가 없다. 2SD와 3SD는 `Setup_Ref_C`([main.cpp:167-172](../../../../../../0_LDPC_original/src/main.cpp))가 허용하는 범위 안이라 죽은 경로가 아니다
- 처방: 3번과 같다. 비AUTO 갈래를 유지한다 (동작 변경 요구 아님, 기존 동작 보존)
- 지적한 워커: I_4(F2) 단독
- **Round 3 검증 필요.** 이유: HIGH이고 단일 워커이며 3번과 한 묶음으로 처방이 정해진다

### 5. TV Gen 빌드에서 `matrix_sel` 가드가 사라져 edge clear와 init 시점이 새로 생긴다 (HIGH)

- 위치: [code_diff.md 8.1, 8.2](../../code_diff.md#ch8)
- 근거: 비AUTO 원본은 두 함수 전체를 `LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel` 안에 둔다([decoder.cpp:6567](../../../../../../0_LDPC_original/src/decoder.cpp), [decoder.cpp:6627](../../../../../../0_LDPC_original/src/decoder.cpp)). AUTO 갈래에는 이 조건이 없다. `Setup_TV_Gen`은 `matrix_sel`이 1 이상이면 모두 받는다([main.cpp:500](../../../../../../0_LDPC_original/src/main.cpp))
- TV 출력 hex 포맷은 변경 금지 대상이다. 포맷은 그대로지만 담기는 값이 달라진다
- 처방: 합친 갈래에 `matrix_sel` 조건을 유지한다 (동작 변경 요구 아님, 기존 동작 보존)
- 지적한 워커: I_4(F3) 단독
- **Round 3 검증 필요.** 이유: HIGH이고 단일 워커이며 변경 금지 대상에 인접하다

### 6. iteration 1~4 구간의 분기 여부와 문턱 130의 출처가 세 곳에서 다르다 (HIGH)

- 위치: 상위 문서 2장, 7장, [code_diff.md 2.2, 4.1, 5.1](../../code_diff.md#ch5)
- 근거: 메모 [msg1.md:31](../../../../../../msg1.md)의 예시는 iteration 1~4를 `1/4/-1`(분기 없음)로 적는다. `LLR_MATRIX_1.txt:18-33`은 1~4에 분기 두 개를 둔다. 기존 코드는 1~4를 `FLAG_HD_1_4_SET_TYPE_0`으로 못박고([decoder.cpp:2090](../../../../../../0_LDPC_original/src/decoder.cpp)) `TYPE_1`을 고르는 코드가 없다. `syn_th_BF1`(130)은 [decoder.cpp:472](../../../../../../0_LDPC_original/src/decoder.cpp)에서 대입만 되고 읽는 곳이 없다. 수정 후 `Select_BF`는 SW < 130을 분기 0과 1의 경계로 쓰는데 이 동작의 근거가 소스에도 메모에도 없다
- 처방: 상위 문서 7장에 미결정 항목을 추가하고 사용자 결정을 받는다 (I_1 D1). 결정에 따라 code_diff 4.1의 `syn_th_sw_branch[0][0]`이나 `num_sw_branch[0]`이 바뀐다 (동작 변경)
- 지적한 워커: I_1(2-1) 단독. 팀 D의 관점 5와 겹칠 수 있다
- **Round 3 검증 필요.** 이유: HIGH이고 단일 워커이며 사용자 결정이 걸린다

### 7. `Clear_Flag`가 지워지는 멤버를 여전히 대입해 두 빌드가 모두 깨진다 (CRITICAL 빌드 시점)

- 위치: [code_diff.md 2.2](../../code_diff.md#ch2)
- 근거: [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp)의 `Clear_Flag`가 `flag_HD_1_4_Set`과 `flag_HD_5_8_Set`에 대입하는데 code_diff에 이 자리의 수정 후 코드가 없다
- 처방: `Clear_Flag`의 수정 후 코드를 code_diff에 넣는다. **코드 삭제를 요구한다** (지워지는 멤버의 대입문 제거)
- 지적한 워커: I_4(F8). 전수 조사는 관점 9(팀 D)의 몫이므로 팀 I는 비AUTO 빌드도 함께 깨진다는 사실만 기록한다
- **Round 3 검증 필요.** 이유: CRITICAL이며 팀 D의 관점 9 결과와 대조해 중복인지 확인해야 한다

### 8. `decoder.cpp:2169`가 AUTO 빌드에서 실제 실행되는 유일한 표 밖 히트다 (MEDIUM)

- 위치: 상위 문서 5.5 표 (없음)
- 근거: [decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp)의 `if (((mn == 1) || (mn == ITER_MAX_HBF + 1)))`은 `__DUAL_UPDATE__` 안에 있고 이 스위치는 [mode.h:64](../../../../../../0_LDPC_original/src/mode.h)에서 켜져 있다. 지금은 두 항이 모두 `mn == 1`이라 iteration 1에서만 걸리지만, 4로 바꾸면 iteration 5도 걸려 그 iteration이 마지막 termination point에서만 종료할 수 있게 된다([decoder.cpp:2170-2188](../../../../../../0_LDPC_original/src/decoder.cpp)). `stop_by_partial_crc`와 `overall_clk`이 바뀌며, `overall_clk`은 이번 변경의 목적인 throughput 지표다
- 처방: 5.5 표에 이 줄과 짝인 2190을 추가하고, 9장 5단계 기대 결과에 throughput 수치가 바뀐다고 적는다. 코드 변경 요구 없음 (동작 자체는 비AUTO 원본과 같다)
- 지적한 워커: I_2(F2), I_4(F5) 독립 일치
- Round 3 검증 생략 가능. 이유: MEDIUM이고 grep과 스위치 값으로 근거가 자명하며 두 워커가 일치한다

### 9. 같은 스위치 안의 형제 히트 다섯이 5.5 표에서 빠졌다 (MEDIUM)

- 위치: 상위 문서 5.5 표
- 근거: [decoder.cpp:1448, 1622, 1828](../../../../../../0_LDPC_original/src/decoder.cpp)(`__RUN_PARITY_SKIP__`), [decoder.cpp:1821](../../../../../../0_LDPC_original/src/decoder.cpp)(`__RUN_PREPROCESSING__`, 같은 스위치의 1149, 2310, 3487은 표에 있다), [decoder.cpp:2190](../../../../../../0_LDPC_original/src/decoder.cpp)(`__DUAL_UPDATE__`의 `#else`). 다섯 곳 모두 지금은 미컴파일이지만 표가 전수를 표방한다
- 처방: 표에 다섯 줄을 스위치 이름과 함께 추가한다. 코드 변경 요구 없음
- 지적한 워커: I_2(F3), I_4(F5 표) 독립 일치
- Round 3 검증 생략 가능. 이유: grep 확정, MEDIUM

### 10. 6장 전수 목록에서 `m_log_CSW_auto` 네 블록이 빠졌고 "86"이라는 수가 재현되지 않는다 (MEDIUM)

- 위치: 상위 문서 6.1, 6.2, 6.3
- 근거: `__AUTO_LLR_OPT__` grep 히트는 87곳이며 파일별 분포가 Round 1 계수와 정확히 같다. 6장 항목이 덮는 히트는 77곳이고, 6장 어디에도 없는 살아 있는 코드는 [decoder.cpp:7741-7743, 7773-7775, 7803-7805, 7928-7938](../../../../../../0_LDPC_original/src/decoder.cpp) 네 블록이다. `main.cpp:329, 485`는 주석 처리된 전처리기라 빠진 것이 맞다
- 처방: 6.3 표에 네 블록을 추가하고 "86"의 셈법을 밝힌다. 코드 변경 요구 없음
- 지적한 워커: I_3(발견 3) 단독
- Round 3 검증 생략 가능. 이유: grep 확정이고 처방이 문서 보강뿐이다

### 11. 6.1이 "고쳐야 하는 곳"으로 적은 두 곳에 수정 후 코드가 없다 (MEDIUM)

- 위치: 상위 문서 6.1, [code_diff.md 8.2](../../code_diff.md#ch8)
- 근거: [decoder.cpp:1137-1141](../../../../../../0_LDPC_original/src/decoder.cpp)(`Get_Cur_LLR_Idx_FILE`과 `Get_VNU_Table_Idx`의 갈림)은 code_diff 어느 장에도 없다. code_diff 6장이 `Get_Cur_LLR_Idx_FILE`을 한 갈래로 합치는데 1137의 갈래를 두면 비AUTO 빌드에서 합친 함수가 불리지 않는다. [decoder.cpp:6609-6626](../../../../../../0_LDPC_original/src/decoder.cpp)(`Is_Iter_Type_Init`)은 8.2에 산문만 있고 수정 후 코드 블록이 없어 8.1과 형식이 어긋난다
- 처방: 두 곳의 수정 후 코드를 넣는다. **`decoder.cpp:1137-1141`은 7장 ㉱ 결정에 따라 코드 삭제를 요구할 수 있다**
- 지적한 워커: I_3(발견 4) 단독. 3번, 12번과 같은 결정에 묶인다
- **Round 3 검증 필요.** 이유: 처방이 코드 삭제를 요구할 수 있고 3번(비AUTO 안전성)과 상충할 소지가 있다

### 12. `Get_Cur_LLR_Idx_FILE`의 비AUTO 갈래는 실행되지 않는 코드이며, 7장 ㉱ 미결정이 실체를 잃는다 (MEDIUM)

- 위치: 상위 문서 5.3-4, 7장 ㉱
- 근거: 이 함수를 부르는 곳은 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp) 하나뿐이고 그 줄은 [decoder.cpp:1137](../../../../../../0_LDPC_original/src/decoder.cpp)의 `#if defined(__AUTO_LLR_OPT__)` 안이다. 비AUTO는 [decoder.cpp:7207-7210](../../../../../../0_LDPC_original/src/decoder.cpp)의 `Get_VNU_Table_Idx`를 쓰고 그 함수는 무조건 0을 돌려준다. 함수 정의 자체는 `#if`로 감싸지 않아 컴파일만 되고 실행되지 않는다. 따라서 5.3-4의 "`1_4_Set`이 `TYPE_1`인 경우 `selected_group`이 -1로 남는다"는 일어날 수 없는 상황이다
- 처방: 5.3-4와 7장 ㉱에 "이 갈래는 실행되지 않는 코드이며 정리는 가독성 문제"라고 적는다. 코드 변경 요구 없음
- 지적한 워커: I_4(D1) 단독
- **Round 3 검증 필요.** 이유: 사용자에게 올라간 미결정 항목 하나를 무효화하는 판정이라 확인 값이 크다. 근거는 grep 확정이므로 확인은 짧다

### 13. Corner 이벤트가 2SD와 3SD로 번지고 TV Gen에서 NULL 역참조가 한 지점 늘어난다 (MEDIUM)

- 위치: [code_diff.md 5.1](../../code_diff.md#ch5)
- 근거: 수정 후 코드는 `m_corner->Event_Flag(...)`를 `Select_BF` 끝에서 모드 구분 없이 한 번 부른다. 원본은 HD의 BF 진입, HD의 BF 미진입, 1.5SD 세 갈래 안에서만 불렀다([decoder.cpp:2093, 2102, 2108, 2119, 2125](../../../../../../0_LDPC_original/src/decoder.cpp)). 2SD와 3SD 프레임마다 `IDX_FLAG_HD_5_8_SET_TYPE_0`이 새로 찍혀 Corner 통계의 뜻이 달라진다. TV Gen에서 `m_corner`는 NULL이나([decoder.cpp:994](../../../../../../0_LDPC_original/src/decoder.cpp)) [decoder.cpp:2072-2076](../../../../../../0_LDPC_original/src/decoder.cpp)이 이미 같은 조합에서 무조건 역참조하므로 새 결함이 아니라 기존 결함이 한 지점 늘어나는 것이다
- 처방: Corner 이벤트를 HD와 1.5SD 갈래 안에 둔다. **동작 변경을 요구한다** (5.1의 수정 후 코드를 고쳐야 한다)
- 지적한 워커: I_4(F4) 단독. 팀 D의 관점 5와 겹친다
- **Round 3 검증 필요.** 이유: 처방이 동작 변경을 요구하고 팀 D 결과와 대조가 필요하다

### 14. BF 구간에서도 파일 row가 실제로 쓰인다는 사실이 문서에 없다 (MEDIUM)

- 위치: 상위 문서 2장, 5.5, 6.2, [code_diff.md 7장](../../code_diff.md#ch7)
- 근거: [decoder.cpp:4019](../../../../../../0_LDPC_original/src/decoder.cpp)의 `channel_llr = ch1`은 1bit 갈래 밖에 있어 `sum_t`의 초기값이 된다([decoder.cpp:4026](../../../../../../0_LDPC_original/src/decoder.cpp)). 1bit 갈래([decoder.cpp:4056-4079](../../../../../../0_LDPC_original/src/decoder.cpp))는 `v_deg > DV_5`인 column에서만 타고, `v_deg <= DV_5`인 column은 BF 구간에서도 4bit 갈래([decoder.cpp:4080-4120](../../../../../../0_LDPC_original/src/decoder.cpp))로 가서 `th1~th7`을 쓴다. 파일의 iteration 1~4 row도 dv 11 그룹만 th 칸이 0이고 나머지 dv 그룹에는 값이 있다. 메모의 "bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리"가 row의 분기 칸을 뜻하는지 th 칸을 뜻하는지 두 문서가 정하지 않았다
- 처방: 6.2와 2장에 "BF가 살아나면 iteration 1~4에서도 파일 row가 쓰이며 `ch1`은 모든 column에, `th1~th7`은 `v_deg <= DV_5` column에 적용된다"를 적고, 메모의 -1이 무엇을 가리키는지 사용자에게 확인한다 (I_1 D2). 코드 변경 요구 없음
- 지적한 워커: I_1(2-3), I_3(발견 5) 독립 일치
- Round 3 검증 생략 가능. 이유: 두 워커가 같은 소스 줄로 같은 결론에 닿았다. 다만 메모 해석은 사용자 결정 사항으로 올린다

### 15. SW 문턱 상수가 오름차순이 아니라 분기 셋 이상에서 중간 분기가 선택되지 않는다 (MEDIUM)

- 위치: [code_diff.md 4.1, 5.1](../../code_diff.md#ch4)
- 근거: [common.h:244](../../../../../../0_LDPC_original/src/common.h)의 `SW_TH_5_8_SET0_512B_TLC_OFF`는 1100, [common.h:251](../../../../../../0_LDPC_original/src/common.h)의 `SET1`은 950이고 default도 960 > 950이다. `Select_SW_Branch`는 `weight < th[i]`를 앞에서부터 보므로 `th = {1100, 950}`이면 SW 1000은 분기 0, SW 1200은 분기 2를 받아 분기 1이 영원히 선택되지 않는다 (손 계산 실증)
- 처방: 4.1의 서술을 고치고 파일 대조 시 문턱 오름차순 검사를 넣는다. 코드 추가이며 동작 변경은 없다
- 지적한 워커: I_1(2-2) 단독. 팀 D 관점 5의 확인 항목이기도 하다
- Round 3 검증 생략 가능. 이유: 손 계산으로 실증되었고 지금 파일(분기 둘)에서는 드러나지 않는 엣지케이스다

### 16. 실행 iteration이 124회에서 120회로 줄고 BF 진입 프레임은 파일의 121~124 row에 닿지 않는다 (MEDIUM)

- 위치: 상위 문서 2장, 5.5, [code_diff.md 1.2](../../code_diff.md#ch1_2)
- 근거: `MN = MN[MN_num - 1]`은 120이 되고([local_opt.cpp:126](../../../../../../0_LDPC_original/src/local_opt.cpp)), `Select_BF`가 BF 미진입 프레임에만 4를 더한다([decoder.cpp:2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp)). 진입 프레임은 mn 1~120, 미진입은 5~124로 둘 다 120회다. 현재 AUTO는 124회다. 메모 [msg1.md:25](../../../../../../msg1.md)는 DAO가 BF 없음을 가정해 세므로 DAO의 124와 디코더의 120이 어긋난다
- 처방: 두 문서에 "파일의 마지막 iter_end는 BF 미진입 프레임의 절대 마지막 번호이고 실행 횟수는 그보다 4 적다"를 적는다. 예산을 124회로 유지하려면 파일이나 보정 블록을 바꿔야 한다 (I_1 D3, 후자는 동작 변경)
- 지적한 워커: I_1(3-4), I_2(F8) 독립 일치
- Round 3 검증 생략 가능. 이유: 손 계산이 두 워커에서 일치한다. 예산 결정은 사용자 몫으로 올린다

### 17. `iter_num -= ITER_MAX_HBF` 보정이 한 layout에만 걸려 통계 뜻이 갈리고 default layout에서 histogram 색인이 넘친다 (MEDIUM)

- 위치: 상위 문서 5.5, [code_diff.md 1.2](../../code_diff.md#ch1_2)
- 근거: [decoder.cpp:1973-1979](../../../../../../0_LDPC_original/src/decoder.cpp)는 `matrix_sel`이 `LAYOUT_PRIME_512B_TLC_VSS_OFF`일 때만 4를 뺀다. histogram 크기는 `MN[MN_num - 1] * 4`로 480이 되는데([ecc_top.cpp:2760](../../../../../../0_LDPC_original/src/ecc_top.cpp)) 색인은 `(iter_num - 1) * 4 + 3`이다([ecc_top.cpp:2808](../../../../../../0_LDPC_original/src/ecc_top.cpp)). layout 1은 보정으로 `iter_num` 최대가 120이라 색인 479로 안전하고, default layout은 124가 남아 495로 범위를 넘는다. 이 경로는 `__PRINT_LOG_DATA__`가 켜질 때만 컴파일되며 [mode.h:31](../../../../../../0_LDPC_original/src/mode.h)에서 꺼져 있다
- 처방: layout별 뜻을 문서에 적고, 넘침을 막으려면 `size_histogram`을 `(MN[MN_num - 1] + ITER_MAX_HBF) * 4`로 맞춘다. **후자는 코드 변경이며 할당 크기만 바꾸므로 복호 결과에는 영향이 없다**. layout 조건을 없애는 것은 통계가 바뀌는 동작 변경이다 (I_1 D4)
- 지적한 워커: I_1(3-6), I_2(F6). 넘침 조건에서 두 워커가 갈렸고 I_1이 정확하다 (워커 간 상충 3 참조)
- Round 3 검증 생략 가능. 리더가 조건을 확정했다

### 18. code_diff 8.1의 edge clear 설명이 코드와 다르다 (MEDIUM)

- 위치: [code_diff.md 8.1](../../code_diff.md#ch8) 끝줄
- 근거: 조건은 [decoder.cpp:6542-6547](../../../../../../0_LDPC_original/src/decoder.cpp)의 `iter == 0 || iter == 1 || iter == ITER_MAX_HBF + 1`이고 `flag_BF_on`을 보지 않는다. BF 진입 프레임은 iteration 0, 1, 5 세 곳에서 걸리고 미진입 프레임은 5에서만 걸린다. 8.1의 "BF에 진입하면 1에서, 진입하지 않으면 5에서 걸린다"는 진입 프레임의 5를 빠뜨렸다. 이 문장을 믿고 `flag_BF_on` 조건을 덧붙이면 비AUTO 빌드와 결과가 갈린다
- 처방: 문장을 다시 쓴다. 코드 변경 요구 없음
- 지적한 워커: I_2(F4). I_1(3-2 표)이 같은 사실을 독립 확인했다
- Round 3 검증 생략 가능. 이유: 소스 조건문으로 근거가 자명하다

### 19. "12곳" 셈법이 표와도 소스와도 맞지 않는다 (MEDIUM)

- 위치: [code_diff.md 1.2](../../code_diff.md#ch1_2), 상위 문서 5.5
- 근거: 5.5 첫 표는 11행이고 담긴 위치는 13개다. 소스의 실제 코드 히트는 decoder.cpp 41곳, local_opt.cpp 2곳, main.cpp 1곳, TV_Dec_Inter.cpp 5곳으로 49곳이다 (I_2가 주석과 주석 처리된 코드를 걸러 Round 1 계수를 재검증했고 파일별로 일치했다). "값이 바뀌면 동작이 달라지는 곳만 싣는다"는 선별 기준이 문서에 없다
- 처방: 수를 13으로 고치고 표 머리에 선별 기준을 적는다. 코드 변경 요구 없음
- 지적한 워커: I_2(F5), I_4(D4) 독립 일치
- Round 3 검증 생략 가능

### 20. `__12META__`와 `__HD_FLOOR_SET__`을 켜면 컴파일되지 않는다 (MEDIUM, 기존 결함)

- 위치: [code_diff.md 4.1, 6.1](../../code_diff.md#ch4)
- 근거: `SW_TH_BF0_512B_TLC_OFF`와 `SW_TH_BF1_512B_TLC_OFF`는 [common.h:236-237](../../../../../../0_LDPC_original/src/common.h)의 `#else` 갈래에만 있고 `__12META__` 갈래([common.h:200-227](../../../../../../0_LDPC_original/src/common.h))에는 없다. code_diff 4.1이 이 두 상수를 쓴다. 다만 지금 소스도 [decoder.cpp:467-468](../../../../../../0_LDPC_original/src/decoder.cpp)에서 같은 상수를 쓰므로 계획이 새로 만드는 결함이 아니다. `__HD_FLOOR_SET__` 쪽은 [decoder.cpp:8073-8083](../../../../../../0_LDPC_original/src/decoder.cpp)의 괄호 짝이 맞지 않는 기존 손상이며, code_diff 6.1의 수정 후 코드가 `Adjust_HD_Floor_Type`을 그대로 부른다
- 처방: code_diff 4.1의 "값은 기존 상수에서 가져온다"는 전제가 `__12META__` 조합에서 성립하지 않는다고 문서에 적는다. 코드 변경 요구 없음
- 지적한 워커: I_4(F6, F7) 단독
- Round 3 검증 생략 가능. 이유: 기존 손상이며 루트 [CLAUDE.md](../../../../../../CLAUDE.md)가 원본 소스 일부 손상을 이미 밝히고 있다

### 21. code_diff 8.3이 인용한 Preprocessing 조건에 감싸는 스위치 두 겹이 빠졌다 (MEDIUM)

- 위치: [code_diff.md 8.3](../../code_diff.md#ch8)
- 근거: 인용 범위인 [decoder.cpp:1148-1150](../../../../../../0_LDPC_original/src/decoder.cpp) 위에 [decoder.cpp:1146](../../../../../../0_LDPC_original/src/decoder.cpp)의 `#if defined (__RUN_PREPROCESSING__)`(꺼짐)과 [decoder.cpp:1147](../../../../../../0_LDPC_original/src/decoder.cpp)의 모드 조건이 있다. 현재 구성에서는 `Preprocessing()`이 실행되지 않아 8.3의 서술이 성립하지 않는다
- 처방: 인용 범위를 1146-1156으로 넓히고 서술을 스위치를 켰을 때로 한정한다. 코드 변경 요구 없음
- 지적한 워커: I_4(D2) 단독
- Round 3 검증 생략 가능

### 22. CSW 로그에 프레임이 탄 분기 index가 남지 않는다 (MEDIUM)

- 위치: 상위 문서 6.3
- 근거: [decoder.cpp:1918-1919](../../../../../../0_LDPC_original/src/decoder.cpp)가 `m_log_CSW_auto[mn]`에 iteration 자리로만 값을 넣고, [decoder.cpp:7929-7937](../../../../../../0_LDPC_original/src/decoder.cpp)의 출력에 분기 자리가 없다. BF가 살아나면 미진입 프레임의 자리 1~4가 [decoder.cpp:7742](../../../../../../0_LDPC_original/src/decoder.cpp)가 넣은 -1로 남아 한 열에 -1과 실제 CSW가 섞인다
- 처방: 로그에 `cur_sw_branch_idx[]`를 함께 찍거나, 6.3에 "코드는 그대로 두되 로그 해석이 바뀐다"를 적는다. 앞쪽은 코드 추가이며 복호 동작은 바꾸지 않는다
- 지적한 워커: I_3(발견 2) 단독
- Round 3 검증 생략 가능. 이유: 처방이 문서 보강으로 닫힌다

### 23. mn 0에서 끝나는 프레임의 `iter_num`이 -4가 된다 (MEDIUM, 리더 추가 발견)

- 위치: 상위 문서 5.5, [code_diff.md 1.2](../../code_diff.md#ch1_2)
- 근거: `flag_BF_on`은 프레임마다 [decoder.cpp:609](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `FLAG_LOW`로 시작하고, `Select_BF`는 mn 0 루프 끝([decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp))에서 불린다. `Check_End_Iter`가 mn 0에서 성공을 돌려주면 `iter_num = mn = 0`이 되고([decoder.cpp:5344](../../../../../../0_LDPC_original/src/decoder.cpp)) 루프를 빠져나온 뒤 [decoder.cpp:1975-1976](../../../../../../0_LDPC_original/src/decoder.cpp)이 `flag_BF_on`이 `FLAG_LOW`이므로 4를 빼서 -4를 만든다. [ecc_top.cpp:887](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `iter_effective = (double)o_iter_num`이 이 값을 받아 평균 iteration 통계에 들어가고, DAO가 그 값을 읽는다
- 미확정 부분: mn 0에서 종료가 실제로 도달 가능한지는 확정하지 못했다. `Check_End_Iter`의 [decoder.cpp:5315](../../../../../../0_LDPC_original/src/decoder.cpp)가 `crc_dec_LFSR_iter[CRC_LEN * (real_mn - 1)]`을 쓰는데 `real_mn`은 [decoder.cpp:608](../../../../../../0_LDPC_original/src/decoder.cpp)에서 0으로 시작해 [decoder.cpp:1966](../../../../../../0_LDPC_original/src/decoder.cpp)에서 증가하므로, mn 0에서 이 함수에 닿으면 색인이 음수가 된다
- 처방: 보정에 하한을 두거나 mn 0 종료 경로에서 보정을 건너뛴다. **동작 변경을 요구한다.** 1번의 처방과 함께 정해야 한다
- 지적한 워커: 없음 (리더가 워커 간 상충 2를 풀다 발견)
- **Round 3 검증 필요.** 이유: 재현 조건(mn 0 종료 도달 가능성)이 확정되지 않았고 처방이 동작 변경을 요구한다

### 24. LOW 묶음

| 항목 | 위치 | 지적 워커 | 처방의 성격 |
|------|------|----------|------------|
| default layout의 `syn_th_BF0` 미초기화를 수리하면서 동작 변경임을 적지 않음 | [code_diff.md 4.1](../../code_diff.md#ch4) | I_1(2-4) | 문서 표시만 (수리 자체는 유지) |
| 분기(프레임 시작 SW)와 row 선택(직전 CSW)의 역할 구분이 한 곳에 없음 | 상위 3장 ㉯, 5.4 | I_1(2-6) | 문서 |
| iteration 0은 row 0 고정이라 분기를 타지 않음을 미서술 | 상위 5.3, [code_diff.md 6.1](../../code_diff.md#ch6) | I_1(3-7) | 문서 |
| `iter <= 4`의 다섯째 히트([decoder.cpp:7005](../../../../../../0_LDPC_original/src/decoder.cpp))가 비AUTO 갈래라 표의 넷과 성격이 다름 | 상위 5.5 둘째 표 | I_2(F7) | 문서 |
| BF 진입과 미진입 프레임의 iteration 예산이 4만큼 다름을 메모가 흐림 | [msg1.md](../../../../../../msg1.md), 상위 5.5 | I_2(F8) | 문서 (16번과 같은 뿌리) |
| 결과 파일의 `SW_Threshold`가 `SW_TH_BF_DEFAULT`(630)를 찍는데 실제 문턱은 680 | [main.cpp:308](../../../../../../0_LDPC_original/src/main.cpp) | I_3(발견 6) | 코드 수정이나 복호 동작은 불변 |
| `Mock_ECC.py:221-233`의 CSW 로그 형식이 실제 출력과 이미 어긋남 | [Mock_ECC.py](../../../../../Util/Mock_ECC.py) | I_3(발견 7) | 범위 밖, 사실 기록 |

Round 3 검증 모두 생략 가능 (LOW, 처방이 문서 보강에 그친다).

---

## ㉰ 작성자 요청 판정

| 요청 | 판정 | 확인 범위와 근거 |
|------|------|-----------------|
| 요청 5: `ITER_MAX_HBF`를 4로 통일할 때 딸려오는 12곳에 빠진 곳이 있는지 | **빠진 곳이 있다.** ㉮ AUTO 빌드에서 실제 컴파일되고 실행되는 누락 한 곳([decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp), `__DUAL_UPDATE__` 켜짐, PCRC 종료 시점과 `overall_clk`을 바꾼다). ㉯ 스위치를 켜면 살아나는 누락 다섯 곳(1448, 1622, 1821, 1828, 2190). ㉰ 표에는 있으나 결과가 깨지는 것을 다루지 않은 한 곳([local_opt.cpp:126-130](../../../../../../0_LDPC_original/src/local_opt.cpp), 발견 1). ㉱ "12곳"이라는 수 자체가 표(13곳)와도 소스(49곳)와도 맞지 않는다 | `ITER_MAX_HBF` 전 히트를 저장소 소스 전체에서 grep해 주석과 주석 처리된 코드를 걸러 재계수했고 파일별 수가 Round 1 계수와 일치했다(decoder.cpp 41, local_opt.cpp 2, main.cpp 1, TV_Dec_Inter.cpp 5). 표 밖 히트마다 감싸는 스위치를 [mode.h](../../../../../../0_LDPC_original/src/mode.h) 전체와 대조해 AUTO 빌드 실행 여부를 판정했다. **문제 없음으로 확정한 범위**: `MN_size` 계열 17곳과 [decoder.cpp:564](../../../../../../0_LDPC_original/src/decoder.cpp)는 `MN[MN_num-1]`이 4만큼 줄고 `ITER_MAX_HBF`가 4만큼 늘어 상쇄되므로 값이 불변이다. [main.cpp:719](../../../../../../0_LDPC_original/src/main.cpp)는 AUTO에서 미컴파일이고 비AUTO에서는 이미 4다. TV_Dec_Inter.cpp 다섯 곳은 `__ECC_TV__`와 `__AUTO_LLR_OPT__`가 [mode.h:21-39](../../../../../../0_LDPC_original/src/mode.h)에서 상호 배타이므로 TV 출력 hex 포맷과 시점 모두 영향이 없다 |
| 요청 6: `__AUTO_LLR_OPT__` 86곳 분류에서 손대지 않아도 되는 곳으로 넘긴 것 중 실제로 고쳐야 하는 것이 있는지 | **한 곳이 조건부 오분류다.** `ecc_top.cpp:652, 680, 944-950`(결과 출력)의 전처리기 갈래 자체는 고칠 것이 없으나, 그 갈래가 부르는 출력 함수가 `ITER_MAX_HBF` 4와 겹쳐 결과 파일의 iteration별 FER 열을 망가뜨린다 (발견 1). **나머지 후보는 분류가 맞다**: `decoder.cpp:505-510`(AUTO와 비AUTO 갈래가 모두 `MODE_POWER_STOPPING_OFF`라 `Jump_Iter`가 실행되지 않고 `Select_BF`는 항상 도달), `decoder.cpp:7339-7352`(`Compute_CSW_Auto`는 분기와 무관), `decoder.cpp:7522-7578`(파일 열기, 닫기, 호출뿐), `main.cpp:140-144`(H-matrix 파일 이름 인자), `main.cpp:706`(`Set_Ref_C_Iteration`이 통째로 빠지고 `local_opt.cpp`가 대신하는 것이 맞음), `decoder.cpp:8109-8113`(두 갈래가 글자까지 동일). `decoder.cpp:1929`와 `main.cpp:308`은 `__AUTO_LLR_OPT__` 히트가 아니라 6장 대상이 아니다 | grep 히트 87곳을 뽑아 파일별 분포가 Round 1 계수와 정확히 일치함을 확인했다. 6장 항목 63개가 덮는 히트는 77곳이고, 6장에 없는 살아 있는 코드는 [decoder.cpp:7741-7743, 7773-7775, 7803-7805, 7928-7938](../../../../../../0_LDPC_original/src/decoder.cpp) 네 블록뿐이다 (발견 10). 6.2 다섯 곳은 BF 1bit 경로에서 어느 값을 쓰는지 소스로 확인했다 (발견 14). "86"이라는 수는 어느 셈법으로도 재현되지 않는다 |

---

## ㉱ 워커 간 상충과 판정

### 상충 1: 저장소에 들어 있는 `mode.h`에서 `__AUTO_LLR_OPT__`가 켜져 있는가

- I_1은 확인 범위 표에 "`__AUTO_LLR_OPT__` 켜짐"이라고 적었고, I_2는 AUTO 빌드를 전제로 표 밖 히트의 실행 여부를 판정했다. I_4는 [mode.h:8](../../../../../../0_LDPC_original/src/mode.h)의 `__PROGRAM_MODE_REF_C__`가 주석이므로 꺼져 있다고 적었다
- **판정: I_4가 맞다.** 리더가 [mode.h](../../../../../../0_LDPC_original/src/mode.h) 전체를 읽어 확인했다. 8행이 주석이므로 21행의 `#ifdef __PROGRAM_MODE_REF_C__`가 거짓이고 `__AUTO_LLR_OPT__`는 정의되지 않는다. 게다가 18행의 `_WIN64` 검사가 앞서므로 Windows에서는 이 블록에 아예 닿지 않는다. 저장소 그대로 빌드하면 38행의 `__PROGRAM_MODE_TV_GEN__`이 켜진 비AUTO TV Gen 빌드가 된다
- **파급**: ㉮ I_2의 "AUTO 빌드에서 실행됨" 판정은 사용자가 외부 환경에서 `__PROGRAM_MODE_REF_C__`를 켜고 비Windows로 빌드한 경우를 뜻하며, 그 전제에서는 옳다 (DAO가 쓰는 빌드가 그것이다). ㉯ I_4의 발견 3과 5(비AUTO 결함)는 저장소에 있는 `mode.h` 그대로의 빌드에서 바로 걸리므로 가정 위의 위험이 아니다. 두 판정 모두 유효하며 전제만 다르다

### 상충 2: `MN[]` 음수로 1.0이 되는 FER 열이 몇 개인가

- I_2는 열 1, 2, 3 세 개라 했고, I_1과 I_3은 열 1~4 네 개라 했다
- **판정: 항상 1.0인 열은 세 개(1, 2, 3)다.** 리더가 소스로 확인했다. `MN[4] = 0`이고 [ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 비교는 `o_iter_num > MN[n]`이다. `o_iter_num`은 [decoder.cpp:1998](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `iter_num`을 받고 `iter_num`은 `mn`을 그대로 받으므로([decoder.cpp:5344, 5355](../../../../../../0_LDPC_original/src/decoder.cpp)) 0이 될 수 있다. 곧 열 4는 "iteration 0에서 끝나지 않은 프레임 비율"이며 실제 값은 1.0에 가깝지만 정의상 1.0 고정이 아니다
- 이 확인 과정에서 발견 23(mn 0 종료 프레임의 `iter_num`이 -4가 된다)이 나왔다

### 상충 3: histogram 색인 넘침이 어느 조건에서 생기는가

- I_1은 default layout에서만 넘친다고 했고, I_2는 BF 미진입 프레임 일반에서 넘친다고 했다
- **판정: I_1이 맞다.** [decoder.cpp:1973-1979](../../../../../../0_LDPC_original/src/decoder.cpp)의 보정이 `matrix_sel`이 `LAYOUT_PRIME_512B_TLC_VSS_OFF`일 때만 걸리므로, 그 layout에서는 `iter_num` 최대가 120이 되어 색인 479로 크기 480 안에 든다. 보정이 걸리지 않는 default layout에서만 124가 남아 색인 495로 넘는다

### 상충 4 (상충 아님): `local_opt.cpp:124-131`의 처방이 세 갈래로 갈렸다

- I_1은 블록을 살리고 식별자만 고치라 했고, I_2는 보정식을 음수가 안 나오게 고치라 했고, I_3은 수정 후 코드를 code_diff에 넣고 기준을 정하라 했다
- **판정: 사실 판단은 셋이 같다** (블록을 지우면 iteration 예산이 128까지 늘어 오류 경로로 빠지고, 살리면 `MN[]`에 음수가 생긴다). 처방만 다르므로 발견 1의 세 갈래 선택지로 합쳐 사용자 결정으로 올린다

### 상충 5 (상충 아님): 팀 P의 6번 항목

- 팀 P는 `ITER_MAX_HBF` 4가 DAO가 읽는 `avg_iteration` 척도를 바꾼다고 적었다. 팀 I는 독립적으로 같은 뿌리에 닿았고([decoder.cpp:1973-1978](../../../../../../0_LDPC_original/src/decoder.cpp)과 [ecc_top.cpp:877-881](../../../../../../0_LDPC_original/src/ecc_top.cpp)), 발견 1, 17, 23에서 세 갈래의 파급을 각각 확정했다. 팀 P의 판정과 어긋나지 않으며 근거가 더 좁혀졌다

---

## ㉲ 미커버 영역

- ㉮ **AUTO 빌드가 실제로 컴파일되는지 확인하지 못했다.** 이 저장소에서는 C++ 빌드를 하지 않으며, 발견 2(`MODE_DEC_1_SSD` 미정의)와 발견 20(`__12META__` 상수 미정의)은 외부 환경의 소스가 이 줄에서 다를 가능성을 배제할 수 없다. Round 3에서 사용자에게 외부 소스의 해당 줄을 확인받는 것이 가장 확실하다
- ㉯ **관점 8의 스위치 조합 검사가 확인 항목에 열거된 일곱 개로 한정되었다.** [mode.h](../../../../../../0_LDPC_original/src/mode.h)에서 켜져 있는 `__RUN_PUNCT_RECOVERY__`(61행), `__SHUFFLED_DUAL_DIAG__`(65행), `__PMU_READ__`(66행), `__HALF_COL_UPDATE__`와 `__HALF_COL_MODIFIED__`(68-70행)는 어느 워커도 수정 후 코드와 대조하지 않았다
- ㉰ **`Check_End_Iter`가 mn 0에서 도달 가능한지 확정하지 못했다** (발견 23). 이 판정에 따라 발견 23이 실재 결함인지 이론상 경로인지가 갈린다
- ㉱ **`MN[]` 중간 원소의 소비처 전수는 부분 확인에 그쳤다.** I_1이 [ecc_top.cpp:877-881](../../../../../../0_LDPC_original/src/ecc_top.cpp), 2020-2024, 2052-2056, [corner.cpp:103](../../../../../../0_LDPC_original/src/corner.cpp)을 확인했으나 `MN[n]`을 읽는 곳의 전수 grep 목록은 만들지 않았다
- ㉲ **Corner 이벤트의 enum 연속성 검사는 팀 D 관점 5의 몫으로 남겼다.** I_4는 발견 13에서 이벤트가 불리는 범위만 다루었고, `IDX_FLAG_HD_5_8_SET_TYPE_0 + idx`가 분기 넷 이상에서 `IDX_FLAG_HD_FLOOR_TYPE_0`을 침범하는지는 확인하지 않았다
- ㉳ **비AUTO 빌드에서 `restart_iter`를 채울 대안 경로가 있는지 조사하지 않았다** (발견 4). I_4는 파일이 없어 채울 경로가 없다고 판정했으나, 하드코딩 상수를 배열에 미리 채우는 초기화를 새로 넣는 안은 검토하지 않았다

---

## 심각도별 집계 (교차 분석 후)

| 심각도 | 건수 | 항목 |
|--------|------|------|
| CRITICAL | 3 | 2(빌드 시점, 기존 손상), 3(실행 시점), 7(빌드 시점) |
| HIGH | 4 | 1, 4, 5, 6 |
| MEDIUM | 16 | 2의 문서 누락 면, 8~23 |
| LOW | 7 | 24의 일곱 항목 |

Round 3 검증 필요: 발견 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 23 (열한 건).
Round 3 검증 생략 가능: 발견 8, 9, 10, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24 (근거가 grep 확정이거나 손 계산으로 실증되었고 처방이 문서 보강에 그친다).
