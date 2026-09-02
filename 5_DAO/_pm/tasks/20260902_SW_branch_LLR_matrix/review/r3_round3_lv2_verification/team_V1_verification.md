# 팀 V1 검증: 빌드 성립과 갈래 통일 (R2-1, R2-2, R2-4, R2-12, R2-15)

> 작성: 2026-09-03 01:42:28
> 검증 대상: Round 2 발견 R2-1(CRITICAL), R2-2(HIGH), R2-4(HIGH), R2-12(MEDIUM), R2-15(MEDIUM)
> 워커: [worker_V1_1.md](worker_V1_1.md)(R2-1, R2-12), [worker_V1_2.md](worker_V1_2.md)(R2-2, R2-4), [worker_V1_3.md](worker_V1_3.md)(R2-15, R2-4 ㉰ 독립 재현)
> 팀 리더가 세 워커와 별개로 소스를 직접 읽어 모든 핵심 고리를 독립 확인했고, 워커 사이가 갈린 두 곳을 코드 근거로 확정했다
> 리뷰 대상은 코드가 아니라 코드 수정 계획 문서 두 개다. 아래에서 "수정 후 코드"는 [code_diff.md](../../code_diff.md)의 수정 후 블록을 그대로 적용한 상태를 뜻한다

용어: BF는 Bit Flipping(Hard Decision 복호의 초기 iteration을 1bit precision으로 도는 모드), HD는 Hard Decision, SD는 Soft Decision, SW는 Syndrome Weight(신드롬 무게), TV는 Test Vector, MN은 디코더의 iteration 상한 배열이다. LLR, CSW, DAO는 그대로 쓴다.

---

## ㉮ 가설 목록

### R2-1

- ㉠ 사실 가설 F1: 저장소 [mode.h](../../../../../../0_LDPC_original/src/mode.h) 그대로의 비AUTO 빌드에서, [code_diff 8.1과 8.2](../../code_diff.md#ch8)가 `Is_Iter_Type_Edge_Clear`와 `Is_Iter_Type_Init`의 `#else` 갈래를 삭제하면, 두 함수가 세워지지 않은 포인터 `m_param_LLR`을 매 iteration 역참조하여 정의되지 않은 동작이 일어난다
- ㉡ 사실 가설 F1b: 비AUTO 2SD와 3SD의 restart 지점 여덟 개가 사라진다
- ㉢ 사실 가설 F1c: TV Gen 빌드에서 `matrix_sel` 가드가 사라져 edge clear와 init 시점이 새로 생긴다
- ㉣ 처방 가설 P1: 두 함수의 `#if defined(__AUTO_LLR_OPT__)` 갈래를 유지하고 합친 갈래에 `matrix_sel` 조건을 유지하면 문제가 해결되고 새 문제가 생기지 않으며 계획의 목적과 충돌하지 않는다
- ㉤ 처방 가설 P1b(대안): 포인터를 `NULL`로 초기화하고 널 검사를 넣으면 해결된다
- ㉥ 처방 가설 P1c(대안): 비AUTO에서 `restart_iter[]`를 하드코딩 상수로 채우는 초기화를 넣으면 갈래를 정말로 통일할 수 있다

### R2-2

- ㉠ 사실 가설 F2: [code_diff 2.2](../../code_diff.md#ch2)가 `flag_HD_1_4_Set`과 `flag_HD_5_8_Set`을 지우는데 `Decoder::Clear_Flag`([decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp))가 두 멤버에 대입하고 이 자리의 수정 후 코드가 어느 장에도 없어 두 빌드가 모두 컴파일되지 않는다. 두 멤버의 참조 전수에서 code_diff가 다루지 않는 곳은 612-613뿐이다
- ㉡ 처방 가설 P2: 612-613을 지우고 그 자리에 `cur_sw_branch_idx[]`를 0으로 두는 반복문을 넣으면 컴파일 실패가 해결되고, R2-4 ㉯의 미초기화도 함께 해결되며, 최종 상태에서 `Select_BF` 앞머리 초기화와 중복되어도 해가 없다

### R2-4

- ㉠ 사실 가설 F4a: 9장 1단계(1장, 2장)만 넣으면 [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) 3줄과 [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) 8줄에서 빌드가 깨진다
- ㉡ 사실 가설 F4b: 9장 3단계의 전제 "`cur_sw_branch_idx[]`가 모두 0"이 거짓이다
- ㉢ 사실 가설 F4c: 배열이 0이어도 3단계 검증 기준("기존 동작과 결과가 같아야 한다")이 뒤집힌다. 옛 AUTO 루프는 iteration 1~4에 그룹 2, 5에 그룹 4, 6~8에 그룹 5를 잡고 새 루프는 그룹 0, 1, 3을 잡는다
- ㉣ 처방 가설 P4: 1단계를 1.1, 2장, 3.3, 4.1을 함께 넣는 것으로 고치거나 2.2의 멤버 삭제를 4단계로 미루고, 3단계 검증을 "분기 줄이 모두 -1인 파일로 기존 결과와 비교"로 다시 쓰면 각 단계가 빌드되고 검증 기준이 성립한다

### R2-12

- ㉠ 사실 가설 F12: `Get_Cur_LLR_Idx_FILE`을 부르는 곳은 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp) 하나뿐이고 그 줄이 `#if defined(__AUTO_LLR_OPT__)` 안이므로 이 함수의 비AUTO 갈래(7001-7047)는 실행되지 않는 코드다. 따라서 상위 5.3-4의 "`TYPE_1`이면 `selected_group`이 -1로 남는다"는 일어나지 않고 7장 ㉱ 미결정이 실체를 잃는다
- ㉡ 처방 가설 P12: 5.3-4와 7장 ㉱에 실행되지 않는 코드임을 적고 1137-1141을 그대로 두면 문제가 해결되고 R2-1 처방과 모순되지 않는다

### R2-15

- ㉠ 사실 가설 F15: [code_diff 3.5](../../code_diff.md#ch3)가 [local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp)을 다루지 않는다. 이 블록을 지우면 BF 미진입 프레임이 파일의 마지막 iteration을 넘겨 돌아 오류 경로로 빠지므로 살려야 한다. 블록 안 `MODE_DEC_1_SSD`는 정의가 없는 기존 손상이다
- ㉡ 처방 가설 P15: 3.5에 "124-131은 살린다"를 적고 조건 둘째 항을 `MODE_DEC_1_5SD`로 고치면 문제가 해결되고 새 문제가 생기지 않는다

---

## ㉯ 증거 확인 결과

### R2-1 관련

| 증거 | 판정 | 코드 근거 | 확인 |
|------|------|----------|------|
| E1-1 `ECC_Top` 생성자 초기화 목록에 `m_param_LLR`이 없다 | **확인됨** | [ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp). 포인터 21개를 `NULL`로 두는데 `m_param_LLR`은 목록에 없다 | 리더, V1_1 |
| E1-2 4인자 `Init_ECC_Top`이 미결정 값을 그대로 넘긴다 | **확인됨** | [ecc_top.cpp:197-210](../../../../../../0_LDPC_original/src/ecc_top.cpp). 199-202행이 네 멤버만 세우고 208행이 `m_dec.Init_Dec(..., m_param_LLR, ...)`로 5인자 `Init_Dec`에 미결정 값을 넘긴다. 5인자 `Init_ECC_Top`([ecc_top.cpp:216-230](../../../../../../0_LDPC_original/src/ecc_top.cpp))만 222행에서 대입한다 | 리더, V1_1 |
| E1-3 `m_param_LLR` 대입처 전수 | **확인됨** | grep 히트는 [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp)과 [ecc_top.cpp:222](../../../../../../0_LDPC_original/src/ecc_top.cpp) 두 곳뿐이다. 선언 [decoder.h:210](../../../../../../0_LDPC_original/src/decoder.h)과 [ecc_top.h:94](../../../../../../0_LDPC_original/src/ecc_top.h)은 컴파일 스위치 없이 놓인다 | 리더, V1_1 |
| E1-4 비AUTO 진입점이 4인자를 부른다 | **확인됨** | [main.cpp:105](../../../../../../0_LDPC_original/src/main.cpp)와 [main.cpp:127](../../../../../../0_LDPC_original/src/main.cpp). [main.cpp:87-95](../../../../../../0_LDPC_original/src/main.cpp)의 분기로 TV Gen 빌드는 127, 비AUTO Ref-C 빌드는 105에 닿고 AUTO 빌드만 `Run_Simulation_Local_Opt`로 빠진다 | 리더, V1_1 |
| E1-5 두 함수가 스위치 없이 매 iteration 불린다 | **확인됨** | grep 히트 24곳. `Is_Iter_Type_Edge_Clear`는 [decoder.cpp:712, 726, 2314, 2321, 2328, 3491, 3498, 3504](../../../../../../0_LDPC_original/src/decoder.cpp), `Is_Iter_Type_Init`은 2578, 2602, 2783, 2863, 2977, 2993, 5700, 5708, 5716, 5740, 5748, 5756, 5824, 5903, 6058, 6139이다. 712와 726은 `Clear_Edge_Restart`([decoder.cpp:709-738](../../../../../../0_LDPC_original/src/decoder.cpp)) 안이고 이 함수는 메인 루프 [decoder.cpp:1133](../../../../../../0_LDPC_original/src/decoder.cpp)에서 스위치 없이 매 mn마다 네 모드 모두에서 불린다 | 리더, V1_1 |
| E1-6 8.1 수정 후가 `#else`를 삭제하고 `m_param_LLR`을 역참조한다 | **확인됨** | [code_diff.md 916-948행](../../code_diff.md#ch8)이 "`#if defined(__AUTO_LLR_OPT__)` 갈래만 남긴다"라 적고 남는 코드의 929, 940행이 `m_param_LLR->restart_num`과 `restart_iter[i]`를 읽는다. 8.2는 수정 후 코드 블록이 없고 972행의 산문뿐이다 | 리더, V1_1 |
| E1-6b 역참조가 걸리는 범위 | **확인됨(Round 2 서술 정밀화)** | AUTO 갈래의 HD와 1.5SD 경로([decoder.cpp:6543-6547](../../../../../../0_LDPC_original/src/decoder.cpp))는 iteration 0, 1, `ITER_MAX_HBF + 1`에서 역참조 없이 끝나고 그 밖 모든 iteration에서 6549행이 역참조한다. 2SD와 3SD는 iteration 0을 뺀 전부에서 6560행이 역참조한다. **`Is_Iter_Type_Init`은 HD와 1.5SD에서 역참조하지 않고**([decoder.cpp:6610-6614](../../../../../../0_LDPC_original/src/decoder.cpp)) 2SD와 3SD에서만 6620행이 역참조한다. 곧 Round 2의 "두 함수가 매 iteration 역참조"는 `Is_Iter_Type_Edge_Clear`에만 온전히 들어맞는다 | 리더, V1_1 |
| E1-7 저장소 mode.h 그대로는 비AUTO다 | **확인됨** | [mode.h:8](../../../../../../0_LDPC_original/src/mode.h)의 `__PROGRAM_MODE_REF_C__`가 주석이라 21-22행의 `__AUTO_LLR_OPT__`가 정의되지 않고, 18행의 `_WIN64` 검사가 앞서므로 Windows에서는 이 블록에 닿지도 않는다. 30행이 거짓이라 38-39행의 `__PROGRAM_MODE_TV_GEN__`과 `__ECC_TV__`가 켜진다. 곧 Windows와 비Windows 어느 쪽으로 빌드해도 비AUTO다 | 리더, V1_1 |
| E1-8 restart 상수 여덟 개가 정의되어 있고 AUTO 갈래에 대응이 없다 | **확인됨** | [common.h:679-686](../../../../../../0_LDPC_original/src/common.h). 이 줄들은 [common.h:491](../../../../../../0_LDPC_original/src/common.h)의 `#ifdef __4_BIT_LLR__`에 딸린 494행 `#else` 갈래 안이고 `__4_BIT_LLR__`가 [mode.h:12](../../../../../../0_LDPC_original/src/mode.h)에서 주석이라 현재 빌드에 정의된다. 비AUTO 갈래 [decoder.cpp:6577-6593, 6633-6672](../../../../../../0_LDPC_original/src/decoder.cpp)가 이를 쓰고 AUTO 갈래에 대응 자리가 없다 | 리더 |
| E1-9 2SD와 3SD가 죽은 경로가 아니다 | **확인됨** | [common.h:75-78](../../../../../../0_LDPC_original/src/common.h)이 HD 1, 2SD 2, 3SD 3, 1.5SD 4다. [main.cpp:168](../../../../../../0_LDPC_original/src/main.cpp)의 `(MODE_DEC_HD > init_n) || (MODE_DEC_1_5SD < init_n)` 검사가 1에서 4까지를 통과시킨다 | 리더 |
| E1-10 비AUTO 갈래에만 `matrix_sel` 가드가 있다 | **확인됨** | [decoder.cpp:6567](../../../../../../0_LDPC_original/src/decoder.cpp)과 [decoder.cpp:6627](../../../../../../0_LDPC_original/src/decoder.cpp)이 갈래 전체를 `LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel`로 감싼다. AUTO 갈래에는 없다 | 리더, V1_1 |
| E1-10b **AUTO 빌드도 `matrix_sel`이 1이 아닐 수 있다** | **확인됨(새 사실)** | [main.cpp:140-143](../../../../../../0_LDPC_original/src/main.cpp)의 `#ifdef __AUTO_LLR_OPT__` 갈래는 `argc > 19`이면 H-matrix 파일 이름을 인자로 받고 `matrix_sel` 값을 검사하지 않는다. 곧 AUTO 실행에서 `matrix_sel != 1`이 가능하다 | V1_1 |
| E1-11 처방 Q1 앞부분이 계획의 목적을 해치지 않는다 | **확인됨** | [code_diff.md 918-948행](../../code_diff.md#ch8)의 8.1 수정 후 코드는 현 AUTO 갈래([decoder.cpp:6542-6565](../../../../../../0_LDPC_original/src/decoder.cpp))와 조건, 순서, 값이 한 줄씩 같다. 8.2는 972행이 "조건은 그대로 둔다"라 적는다. 곧 8.1과 8.2가 AUTO 빌드에 주는 변화는 0이다. AUTO에서 두 함수의 동작이 달라지는 것은 `ITER_MAX_HBF`가 0에서 4로 바뀌는 [code_diff 1.2](../../code_diff.md#ch1_2) 때문이며 갈래를 합치지 않아도 그대로 일어난다. 상위 문서도 갈래 통일을 요구하지 않는다(5.6과 6.1 표가 가리키는 줄이 AUTO 갈래 범위이고, 7장 ㉱의 비AUTO 하드코딩은 `Get_Cur_LLR_Idx_FILE` 쪽이다) | 리더, V1_1 |
| E1-11b 처방 Q1 뒷부분("합친 갈래에 `matrix_sel` 조건 유지")은 받으면 안 된다 | **반박됨** | E1-10b에 따라 AUTO 실행에서 `matrix_sel != 1`이 가능하므로, 합친 갈래에 `matrix_sel == LAYOUT_PRIME_512B_TLC_VSS_OFF` 조건을 두면 그 실행에서 AUTO 빌드가 edge clear와 init을 통째로 잃는다. 지금 없는 결함이 새로 생긴다 | V1_1 |
| E1-12 대안 Q1c는 현재 성립하지 않는다 | **확인됨** | `PARAM_LLR` 정의는 [ecc_data.h:179-198](../../../../../../0_LDPC_original/src/ecc_data.h)이고 실체 객체는 [local_opt.h:30](../../../../../../0_LDPC_original/src/local_opt.h)의 값 멤버 하나뿐이다. `LOCAL_OPT`를 만드는 곳은 [main.cpp:117](../../../../../../0_LDPC_original/src/main.cpp) 하나이며 `#if defined(__AUTO_LLR_OPT__)` 안이라 비AUTO에서는 `PARAM_LLR` 객체가 하나도 만들어지지 않는다. 값 대응 자체는 2SD 2개, 3SD 6개로 정확히 맞지만, `restart_iter[]`가 모드마다 달라야 해서(HD 실행에 2SD 값을 남기면 iteration 241과 581에서 없던 edge clear가 생긴다) `init_n`별로 채우는 새 코드가 필요하고, `matrix_sel` 가드 소실은 여전히 다루지 못한다 | V1_1 |
| E1-13 대안 Q1b는 첫째 피해만 막는다 | **확인됨** | 널 검사를 넣으면 비AUTO에서 Edge_Clear는 HD와 1.5SD의 iteration 0, 1, 5에서만, 2SD와 3SD는 iteration 0에서만 참이 된다. [decoder.cpp:6579-6591, 6645-6668](../../../../../../0_LDPC_original/src/decoder.cpp)의 여덟 지점이 그대로 사라지고 `matrix_sel` 가드 소실도 남는다 | 리더, V1_1 |

### R2-2 관련

| 증거 | 판정 | 코드 근거 | 확인 |
|------|------|----------|------|
| E2-1 `Clear_Flag`가 두 멤버에 대입하고 프레임마다 불린다 | **확인됨** | [decoder.cpp:606-616](../../../../../../0_LDPC_original/src/decoder.cpp)의 612, 613행. 호출은 [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp)이며 메인 루프 [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp) 앞이라 프레임마다 한 번이다 | 리더, V1_2 |
| E2-2 두 멤버 참조 전수와 장별 대조 | **확인됨** | `flag_HD_1_4_Set` 히트는 [decoder.h:297](../../../../../../0_LDPC_original/src/decoder.h)과 [decoder.cpp:612, 2090, 7002, 7006](../../../../../../0_LDPC_original/src/decoder.cpp) 다섯 곳, `flag_HD_5_8_Set` 히트는 [decoder.h:298](../../../../../../0_LDPC_original/src/decoder.h)과 [decoder.cpp:613, 2091, 2100, 2106, 2117, 2123, 7010, 7016](../../../../../../0_LDPC_original/src/decoder.cpp) 아홉 곳이다. 선언 두 줄은 2.2가, 2090~2123은 5.1이(`Select_BF` 비AUTO 갈래 통째 교체), 7002~7016은 6.1이 처리한다. 남는 것은 612와 613뿐이다 | 리더, V1_2 |
| E2-3 2.2가 지우는 이름과 더하는 이름 | **확인됨** | [code_diff.md 144-169행](../../code_diff.md#ch2). 지우는 것은 `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1`, 남기는 것은 `flag_BF_on`, `syn_weight`, `psyn_weight`, `syn_th_BF0`, 더하는 것은 `cur_sw_branch_idx[MAX_SW_SPAN]`, `num_sw_branch[MAX_SW_SPAN]`, `syn_th_sw_branch[MAX_SW_SPAN][MAX_SW_BRANCH - 1]`이다 | 리더, V1_2 |
| E2-4 code_diff에 `Clear_Flag` 장이 없다 | **확인됨** | [code_diff.md](../../code_diff.md) 제목 전수(1.1~9장)에 `Clear_Flag`를 다루는 장이 없다 | 리더, V1_2 |
| E2-5 반복문 변수 | **확인됨** | [decoder.cpp:606-616](../../../../../../0_LDPC_original/src/decoder.cpp)에 지역 변수 선언이 없어 반복문 변수는 초기화절에서 선언해야 한다 | 리더, V1_2 |
| E2-6 최종 상태에서 `Select_BF`가 앞머리에서 0으로 채운다 | **확인됨** | [code_diff.md 554-556행](../../code_diff.md#ch5). 호출은 [decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp)의 `if (mn == 0) Select_BF();`이고 mn 0에서 이보다 앞서 루프를 벗어나는 경로가 없다([decoder.cpp:1947-1949](../../../../../../0_LDPC_original/src/decoder.cpp)가 mn 0에서 `Check_End_Iter`를 건너뛰고 [decoder.cpp:1961-1965](../../../../../../0_LDPC_original/src/decoder.cpp)의 파워 스토핑은 `Init_Dec_Option`이 OFF로 굳힌다) | 리더, V1_2 |
| E2-7 `Clear_Flag`가 모든 읽기보다 앞선다 | **확인됨** | [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp) → 루프 1120 → [decoder.cpp:1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp)(`mn > 0`에서만 `Get_Cur_LLR_Idx_FILE`) → [decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp) | 리더, V1_2 |

### R2-4 관련

| 증거 | 판정 | 코드 근거 | 확인 |
|------|------|----------|------|
| E2-8 `floor_flag` 히트 | **확인됨** | [local_opt.cpp:105, 114, 178](../../../../../../0_LDPC_original/src/local_opt.cpp)과 [ecc_data.h:197](../../../../../../0_LDPC_original/src/ecc_data.h). [code_diff 3.3](../../code_diff.md#ch3)은 105와 114만 코드로 다루고 178은 산문뿐이다 | 리더, V1_2 |
| E2-9 문턱 낱개 변수 히트 | **확인됨** | 대입은 [decoder.cpp:467](../../../../../../0_LDPC_original/src/decoder.cpp)(`syn_th_BF0`, 2.2가 남기므로 무해), 468, 472, 480, 483, 489, 492. 읽기는 2088, 2099, 2116. 선언은 [decoder.h:301-306](../../../../../../0_LDPC_original/src/decoder.h) | 리더, V1_2 |
| E2-11 1단계 직후 깨지는 줄 | **부분 확인(AUTO는 정확, 비AUTO는 목록이 불완전)** | **AUTO 빌드 11줄**은 Round 2 목록과 정확히 같고 과장이 없다(`local_opt.cpp` 105, 114, 178과 `decoder.cpp` 468, 472, 480, 483, 489, 492, 612, 613. 467이 빠진 것도 옳다). **비AUTO 빌드는 12줄이 더 깨진다**: [decoder.cpp:2090, 2091, 2099, 2100, 2106, 2116, 2117, 2123](../../../../../../0_LDPC_original/src/decoder.cpp)(5.1, 4단계)과 [decoder.cpp:7002, 7006, 7010, 7016](../../../../../../0_LDPC_original/src/decoder.cpp)(6.1, 3단계) | 리더, V1_2 |
| E2-12 단계별로 남는 깨진 줄 | **확인됨** | 2단계 뒤 AUTO 8줄, 비AUTO 20줄. 3단계 뒤 AUTO 8줄(6장이 AUTO 갈래만 건드려 하나도 줄지 않는다), 비AUTO 16줄. 4단계 뒤 양쪽 모두 612-613만 남는다. 곧 **9장 다섯 단계를 순서대로 다 밟아도 마지막까지 빌드되지 않는다** | V1_2 |
| E2-13 `Decoder`가 `ECC_Top`의 값 멤버다 | **확인됨** | [ecc_top.h:97](../../../../../../0_LDPC_original/src/ecc_top.h) `Decoder m_dec;`. `ECC_Top`이 사용자 정의 생성자([ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp))를 가지므로 [main.cpp:104, 126](../../../../../../0_LDPC_original/src/main.cpp)의 `new ECC_Top()`이 값 초기화 대신 그 생성자만 부른다 | 리더, V1_2 |
| E2-14 `Initialize_Dec`가 포인터만 세운다 | **확인됨** | [decoder.cpp:5-8](../../../../../../0_LDPC_original/src/decoder.cpp)의 생성자가 `Initialize_Dec()`만 부르고, `Initialize_Dec`는 `/* pointers */` 아래에서 포인터 멤버만 `NULL`로 둔다. 값 멤버 배열을 채우는 코드가 없다 | 리더, V1_2 |
| E2-16 배열을 채우는 곳이 5.1뿐이다 | **확인됨** | [code_diff.md](../../code_diff.md) 전체에서 `cur_sw_branch_idx`에 값을 넣는 곳은 5.1의 554-556, 561-562, 569, 576행뿐이며 모두 4단계다 | 리더, V1_2 |
| E2-18 파일의 그룹 배치 | **확인됨** | [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 8행 `12`, 10행 `1 7 6 6 1 5 5 7 6 10 10 13`(합 77), 11행 `20 20 21 20 21 21 1 1 1 1 1 1`, 13행 `0`. 그룹 0은 iteration 1~1, 그룹 1은 2~4, 그룹 2는 1~4, 그룹 3은 5~8, 그룹 4는 5~5, 그룹 5는 6~8이다 | 리더, V1_2, V1_3 |
| E2-19 옛 AUTO 루프 손 실행 | **확인됨** | [decoder.cpp:6985-6999](../../../../../../0_LDPC_original/src/decoder.cpp)는 `g = 11`부터 내려가며 범위가 `iter`를 덮는 첫 g에서 break한다. iteration 1~4는 g5(6~8), g4(5~5), g3(5~8) 불일치 뒤 g2(1~4) 일치 → **그룹 2**. iteration 5는 g5 불일치 뒤 g4 일치 → **그룹 4**. iteration 6~8은 g5 일치 → **그룹 5** | 리더, V1_2, V1_3 (세 곳 독립 일치) |
| E2-20 새 루프 손 실행 | **확인됨** | [code_diff.md 688-710행](../../code_diff.md#ch6)의 분기 필터가 배열이 모두 0일 때 분기 1인 그룹 2, 4, 5를 걸러낸다. iteration 1 → **그룹 0**, 2~4 → **그룹 1**, 5~8 → **그룹 3** | 리더, V1_2, V1_3 |
| E2-21 두 결과가 다르다 | **확인됨** | 옛 {2, 2, 2, 2, 4, 5, 5, 5}와 새 {0, 1, 1, 1, 3, 3, 3, 3}이 iteration 1~8 전부에서 다르다. Round 2 주장이 정확하고 [code_diff.md 720-728행](../../code_diff.md#ch6)의 6.1 자체 확인표와도 일치한다 | 리더, V1_2, V1_3 |
| E2-22 대안 기준의 성립 | **부분 확인(조건 셋을 더 달아야 성립)** | ㉠ 분기 줄이 모두 -1이면 `continue`가 한 번도 걸리지 않아 두 루프의 순회가 글자 그대로 같아지고 그룹 선택이 일치한다(손 실행으로 확인). ㉡ 그러나 3단계는 이미 3.2 파서가 들어간 뒤라 **변환된 파일로만** 돌릴 수 있고, 변환에 딸린 `type_each_group` 교정이 iteration 1~8의 row 선택을 바꾼다. 비교 기준을 "`type_each_group`을 교정하고 분기 줄은 넣지 않은 파일로 옛 코드를 돌린 결과"로 다시 정의해야 한다. ㉢ 1.2장이 3단계까지 들어가면 안 된다([local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp)이 iteration 수열을 바꾼다) | V1_2 |
| E2-22b **`type_each_group`을 교정해야 하는가** (워커 상충) | **V1_2가 맞다** | V1_3은 원래 값(20, 21)을 두어야 한다고 했으나 코드가 반박한다. [code_diff.md 679행](../../code_diff.md#ch6)이 `table_row_idx` 초기값을 0에서 -1로 바꾸고 718행이 이를 바뀐 점으로 밝힌다. `type`이 20 또는 21이면 [decoder.cpp:7051](../../../../../../0_LDPC_original/src/decoder.cpp)의 `GROUP_TYPE_ITER`(0)와 [7059](../../../../../../0_LDPC_original/src/decoder.cpp)의 `GROUP_TYPE_CSW`(1) 어느 쪽도 참이 아니라 값이 초기값에 머문다. 곧 옛 코드는 0을, 새 코드는 -1을 돌려주어 **결과가 갈린다**. `type`을 1로 교정하면 [decoder.cpp:7060](../../../../../../0_LDPC_original/src/decoder.cpp)의 `table_row_idx = start_idx`가 언제나 먼저 실행되어 양쪽이 같아진다 | 리더 확정 |
| E2-23 옛 루프의 현 파일 결과는 비교 기준이 될 수 없다 | **확인됨(상위 문서 서술은 과한 일반화)** | 퇴화(전역 row 0 고정)는 `type`이 20 또는 21인 **그룹 0~5가 덮는 iteration 1~8에서만** 일어나고, 그룹 6~11(`type` 1)이 덮는 iteration 9~124는 [decoder.cpp:7059-7068](../../../../../../0_LDPC_original/src/decoder.cpp)의 CSW 갈래가 정상으로 돈다. 상위 문서 3장의 "항상 첫 번째 row"는 이 한정을 빠뜨렸다. 비교 기준 적합성 판정은 그대로 **부적합**이다 | V1_2 |

### R2-12 관련

| 증거 | 판정 | 코드 근거 | 확인 |
|------|------|----------|------|
| E1-14 호출처가 하나뿐이다 | **확인됨** | grep 히트는 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp)(호출), [decoder.cpp:6973](../../../../../../0_LDPC_original/src/decoder.cpp)(정의), [decoder.h:125](../../../../../../0_LDPC_original/src/decoder.h)(선언) 셋뿐이다 | 리더, V1_1 |
| E1-15 1138이 AUTO 갈래 안이다 | **확인됨** | [decoder.cpp:1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp). 1137행 `#if defined(__AUTO_LLR_OPT__)`, 1139행 `#else`, 1140행 `Get_VNU_Table_Idx(mn)` | 리더, V1_1 |
| E1-16 `Get_VNU_Table_Idx`가 무조건 0을 돌려준다 | **확인됨** | [decoder.cpp:7207-7210](../../../../../../0_LDPC_original/src/decoder.cpp)의 몸체는 `return 0;` 한 줄이다 | 리더, V1_1 |
| E1-17 함수 정의가 `#if`로 감싸이지 않았다 | **확인됨** | [decoder.cpp:6973](../../../../../../0_LDPC_original/src/decoder.cpp) 앞에 전처리기 갈래가 없고 [decoder.h:125](../../../../../../0_LDPC_original/src/decoder.h) 선언도 무조건이다. 비AUTO에서도 컴파일은 되고 실행만 되지 않는다 | 리더, V1_1 |
| E1-18 비AUTO 갈래가 지워지는 멤버를 읽는다 | **확인됨** | [decoder.cpp:7002, 7006, 7010, 7016](../../../../../../0_LDPC_original/src/decoder.cpp). 6.1이 이 갈래를 지우므로 2.2의 멤버 삭제와 짝이 맞는다 | 리더, V1_1, V1_2 |
| E1-19, E1-20 처방의 일관성 | **확인됨** | 1137-1141을 그대로 두면 비AUTO는 `Get_VNU_Table_Idx`(항상 0)를 계속 써 원본과 동작이 같다. 반대로 이 줄을 고쳐 합친 `Get_Cur_LLR_Idx_FILE`을 무조건 부르게 하면 그 몸체가 [decoder.cpp:6985, 6988, 6995](../../../../../../0_LDPC_original/src/decoder.cpp) 자리에서 `m_param_LLR`을 역참조해 **R2-1과 똑같은 결함이 한 지점 더 생긴다** | 리더, V1_1 |
| E1-21 6.1 제목의 줄 범위 오기 | **확인됨(새 사실)** | [code_diff.md](../../code_diff.md) 6.1 제목은 "6973-6999행"이나 실제 교체 범위는 비AUTO 갈래를 포함한 6973-7047이다. 제목을 고쳐야 R2-2의 "남는 것은 612-613뿐"이 독자에게도 확인 가능해진다 | V1_1, V1_2 |

### R2-15 관련

| 증거 | 판정 | 코드 근거 | 확인 |
|------|------|----------|------|
| E3-1 두 블록의 구실 | **확인됨** | [local_opt.cpp:116-123](../../../../../../0_LDPC_original/src/local_opt.cpp)이 `MN_num`을 마지막 row의 `iter_end`로 잡고 `MN[i] = i`로 채우되 마지막 원소만 `iter_end`로 둔다. 124-131은 HD 계열에서 전 원소에 `-= ITER_MAX_HBF`를 걸고 `MN[0]`만 `ITER_MAX_HBF`로 되돌린다 | 리더, V1_3 |
| E3-2 3.5의 인용 범위 | **확인됨(Round 2 서술 일부 반박)** | [code_diff.md 317-349행](../../code_diff.md#ch3)의 3.5는 제목이 "116-123행"이고 수정 전 블록이 116-123행과 정확히 같다. 124-131은 인용 밖이므로 **계획을 그대로 적용하면 삭제되지 않고 자연히 남는다**. Round 2의 "지우면"은 조건법이며 계획이 삭제를 지시하지는 않는다 | 리더, V1_3 |
| E3-3 `MODE_DEC_1_SSD` 히트 | **확인됨** | 저장소 전체 grep 결과 [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp) 한 곳뿐이고 정의가 없다 | 리더, V1_3 |
| E3-4 정의된 이름 | **확인됨** | [common.h:78](../../../../../../0_LDPC_original/src/common.h) `#define MODE_DEC_1_5SD 4`. 철자 차이는 숫자 5가 문자 S로 바뀐 형태다 | 리더, V1_3 |
| E3-5 `local_opt.cpp`가 모든 빌드에 들어간다 | **확인됨(V1_3의 유보를 리더가 해소)** | [local_opt.cpp:1-12](../../../../../../0_LDPC_original/src/local_opt.cpp)에 전처리기 가드가 없다. V1_3은 빌드 파일이 없어 소스 목록 포함 여부를 확정하지 못한다고 유보했으나, 리더가 [build.bat](../../../../../../0_LDPC_original/src/build.bat)을 확인했다. 이 파일은 `cl` 명령에 `local_opt.cpp`를 조건 없이 넣고, `mode.h` 그대로의 Windows 빌드는 비AUTO다. 곧 **저장소 사본은 기본 빌드에서 124행 때문에 컴파일되지 않는다** | 리더 확정 |
| E3-6, E3-7 블록이 없을 때의 iteration 수열 | **확인됨** | 파일의 마지막 `iter_end`가 124이므로 보정이 없으면 `MN[MN_num-1] = 124`다. [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)이 이를 `MN`으로 삼고 1120이 `mn < MN + 1`을 돈다. BF 미진입 프레임은 [decoder.cpp:2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp)에서 4를 더해 mn이 5에서 128까지 간다 | 리더, V1_3 |
| E3-8 범위 밖 iteration의 귀결 | **확인됨** | [decoder.cpp:7048-7050](../../../../../../0_LDPC_original/src/decoder.cpp)이 오류를 찍고 흐름을 멈추지 않는다. 이어 7051행이 `type_each_group[-1]`을 읽는 정의되지 않은 동작에 들어가고 row 0으로 복호가 이어진다 | 리더, V1_3 |
| E3-9 식별자를 고쳤을 때의 1.5SD 동작 | **확인됨** | [decoder.cpp:2113-2115](../../../../../../0_LDPC_original/src/decoder.cpp)의 1.5SD 갈래는 BF 판정 없이 언제나 `mn`과 `MN`에 4를 더한다. 보정이 걸리지 않으면 `MN = 124 + 4 = 128`이 되어 iteration 125~128이 파일 범위를 넘고, 걸리면 `MN = 120 + 4 = 124`가 되어 파일의 1~124와 정확히 맞는다 | 리더, V1_3 |
| E3-10 1.5SD 보정이 의도라는 소스 단서 | **확인됨(V1_3의 결정적 발견, 리더 재확인)** | [main.cpp:704-781](../../../../../../0_LDPC_original/src/main.cpp)의 `Set_Ref_C_Iteration`이 `#ifndef __AUTO_LLR_OPT__` 안에서 `MN[]`을 직접 채운다. HD는 `MN_num = 5`, `MN[0] = ITER_MAX_HBF`(4), `MN[4] = ITER_MAX_HD_PRIME`(120)이고, **1.5SD는 `MN_num = 1`, `MN[0] = ITER_MAX_HD_PRIME`(120)**이다([common.h:398, 401, 414](../../../../../../0_LDPC_original/src/common.h)). 디코더가 쓰는 `MN[MN_num-1]`은 두 모드 모두 120이다. 곧 비AUTO에서 1.5SD 프레임은 120에 `Select_BF`의 +4가 붙어 mn 5~124를 돈다. AUTO에서 같은 수열이 나오려면 파일의 124에서 4를 빼는 보정이 HD와 1.5SD **양쪽에** 걸려야 한다. 2SD와 3SD가 조건에서 빠지는 것도 옳다(두 모드는 `Select_BF`에서 `mn`을 밀지 않는다) | 리더 재확인 |
| E3-11 조건의 구성 | **확인됨** | [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp)은 첫 항이 `MODE_DEC_HD`이고 `||`로 이어진다. 고치면 참이 되는 집합이 {HD}에서 {HD, 1.5SD}로 넓어진다. 지금은 식별자가 선언되지 않아 **비교할 "현재 동작"이 존재하지 않는다** | 리더, V1_3 |

---

## ㉰ 판정 표

| 발견 | 사실 판정 | 처방 판정 | 심각도 재판정 |
|------|----------|----------|--------------|
| **R2-1** | **확인됨.** 다섯 고리(생성자 미초기화, 4인자 `Init_ECC_Top`이 미결정 값을 5인자 `Init_Dec`에 전달, 비AUTO 진입점 둘 다 4인자, 두 함수가 스위치 없이 매 iteration 호출, 8.1 수정 후가 `#else` 삭제)가 모두 코드로 확인되었고 반례가 없다. 딸린 F1b와 F1c도 확인됨. 서술 하나만 정밀화가 필요하다: 매 iteration 역참조는 `Is_Iter_Type_Edge_Clear`에 해당하고, `Is_Iter_Type_Init`은 2SD와 3SD에서만 역참조한다 | **처방 앞부분 유효, 뒷부분 반대.** `#if` 갈래를 유지하는 것은 옳고 AUTO 동작 변화가 0이다. 나아가 **8.1과 8.2를 계획에서 통째로 빼는 것**이 같은 효과에 부작용이 더 적다(8.1 수정 후가 현 AUTO 갈래와 한 줄씩 같고 8.2는 "조건은 그대로 둔다"라 적으므로 두 장의 AUTO 기여가 0이다). **"합친 갈래에 `matrix_sel` 조건을 유지한다"는 적용하면 안 된다**: AUTO 실행도 `argc > 19`이면 `matrix_sel != 1`이 가능해([main.cpp:140-143](../../../../../../0_LDPC_original/src/main.cpp)) 그 실행에서 edge clear와 init을 통째로 잃는 새 결함이 생긴다. 갈래를 남기면 이 조건 문제 자체가 사라진다. **Q1b는 처방 수정 필요**(역참조만 막고 restart 여덟 개와 `matrix_sel` 가드 소실은 남는다). **Q1c는 처방 반대**(비AUTO에 `PARAM_LLR` 객체가 없어 새 소유자, 생명주기, `init_n`별 배열 채우기를 다 만들어야 하고 `matrix_sel` 문제는 여전히 남는다) | **CRITICAL 유지** |
| **R2-2** | **확인됨.** grep 전수로 두 멤버의 히트 14곳을 code_diff 장과 대조했고 다루어지지 않는 곳은 [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp) 두 줄뿐임이 확정되었다. 과장 없음 | **처방 유효.** `Clear_Flag`가 [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp)에서 프레임마다, 메인 루프와 `Select_BF`보다 먼저 불리므로 그 자리의 0 채우기가 R2-4 ㉯의 미초기화까지 함께 닫는다. 최종 상태에서 `Select_BF` 앞머리 초기화와 겹치지만 같은 값을 두 번 쓰는 것이라 무해하다. 실행 세부: `Clear_Flag`에 지역 변수가 없으므로 반복문 변수는 초기화절에서 선언해야 한다 | **HIGH 유지** |
| **R2-4 ㉮** | **확인됨(범위를 넓혀야 한다).** AUTO 빌드에서 깨지는 11줄은 Round 2 목록과 정확히 같고 과장이 없다(`decoder.cpp:467`을 뺀 것도 옳다). **비AUTO 빌드에서는 12줄이 더 깨진다.** 더 무거운 사실이 함께 확인되었다: 9장 다섯 단계를 순서대로 다 밟아도 612-613 때문에 **마지막까지 빌드되지 않는다** | **처방 유효, 한 갈래를 골라야 한다.** "2.2의 멤버 삭제를 4단계로 미룬다" 쪽이 낫다. 그러면 5.1과 6.1이 이미 들어간 뒤라 비AUTO의 12줄도 같은 단계에서 함께 해소된다. "1단계를 1.1, 2장, 3.3, 4.1로 묶는다" 쪽을 고르면 비AUTO는 4단계까지 여전히 깨지므로 그 묶음에 5.1과 6.1까지 넣어야 한다. 어느 쪽을 고르든 R2-2의 `Clear_Flag` 수리가 함께 들어가야 비로소 빌드된다 | **HIGH 유지** |
| **R2-4 ㉯** | **확인됨.** `Decoder`는 `ECC_Top`의 값 멤버([ecc_top.h:97](../../../../../../0_LDPC_original/src/ecc_top.h))이고 `ECC_Top`이 사용자 정의 생성자를 가지므로 `new ECC_Top()`이 값 초기화를 하지 않는다. `Initialize_Dec`는 포인터만 세우고 배열을 채우는 곳은 5.1(4단계)뿐이다 | **처방 유효.** R2-2의 처방과 같은 자리에서 함께 닫힌다 | **HIGH 유지** |
| **R2-4 ㉰** | **확인됨.** 리더와 워커 둘이 각각 손 실행해 옛 루프 {1~4: 그룹 2, 5: 그룹 4, 6~8: 그룹 5}와 새 루프 {1: 그룹 0, 2~4: 그룹 1, 5~8: 그룹 3}을 재현했고 세 결과가 일치한다. Round 2 주장이 정확하다 | **처방 수정 필요(조건 셋을 달아야 성립).** "분기 줄이 전부 -1"이면 그룹 선택은 두 루프가 반드시 일치한다(확인됨). 그러나 "기존 결과와 같다"가 성립하려면 ㉠ 비교용 파일의 `type_each_group`을 1로 **교정해야** 한다(교정하지 않으면 6.1이 바꾼 `table_row_idx` 초기값 -1 때문에 옛 코드는 row 0을, 새 코드는 -1을 돌려주어 결과가 갈린다), ㉡ 비교 기준을 "그 교정한 파일에 분기 줄을 넣지 않고 옛 코드로 돌린 결과"로 다시 정의해야 한다, ㉢ 1.2장이 3단계까지 들어가면 안 된다. 세 조건을 문서에 함께 적어야 한다 | **HIGH 유지** |
| **R2-12** | **확인됨.** 호출처는 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp) 하나뿐이고 AUTO 갈래 안이며 비AUTO는 항상 0을 돌려주는 `Get_VNU_Table_Idx`를 쓴다. 함수 정의가 무조건 컴파일되므로 "컴파일은 되고 실행되지 않는 코드"라는 규정이 정확하다. 상위 5.3-4의 상황이 일어나지 않고 7장 ㉱가 가독성 문제로 줄어든다는 결론도 맞다 | **처방 유효, 근거를 더 강하게 적어야 한다.** 1137-1141을 그대로 두는 것은 R2-1 처방과 모순되지 않을 뿐 아니라 **R2-1 처방이 요구하는 바**다. 이 줄을 고쳐 합친 함수를 무조건 부르게 하면 비AUTO에서 `m_param_LLR` 역참조 지점이 하나 더 생겨 R2-1과 같은 결함이 재발한다. 문서에는 "가독성 문제라 손대지 않는다"가 아니라 "비AUTO 안전을 위해 갈래를 유지한다"로 적어야 한다. 곁들여 6.1 제목의 줄 범위를 6973-7047로 고쳐야 한다 | **MEDIUM 유지.** 다만 R2-1과 한 결정으로 묶어야 한다 |
| **R2-15** | **부분 확인(한 서술은 반박됨).** `MODE_DEC_1_SSD`가 저장소 전체에서 한 곳뿐이고 정의가 없다는 것, `local_opt.cpp`에 가드가 없고 [build.bat](../../../../../../0_LDPC_original/src/build.bat)이 이를 조건 없이 컴파일해 **저장소 사본이 기본 빌드에서 서지 않는다**는 것은 확인됨. **반박되는 부분**: 3.5의 수정 전 블록이 116-123행과 정확히 일치해 124-131은 인용 밖이므로, 계획을 그대로 적용하면 이 블록은 삭제되지 않고 자연히 남는다. 곧 "지우면 mn 128까지 돈다"는 실재하는 위험이 아니라 적용자가 범위를 넓게 읽었을 때의 가정이다. 문서 명시가 필요하다는 결론 자체는 유효하다 | **처방 유효, 근거를 격상해야 한다.** "124-131은 살린다"는 옳다. `MODE_DEC_1_5SD`로 고치는 것을 Round 2는 "동작 변경"으로 조심스럽게 달았으나, **동작 변경이 아니라 비AUTO와의 어긋남 제거**다. [main.cpp:704-781](../../../../../../0_LDPC_original/src/main.cpp)에서 비AUTO 1.5SD가 `MN[0] = ITER_MAX_HD_PRIME`(120)을 쓰고 `Select_BF`의 +4로 mn 5~124를 도는데, AUTO에서 같은 수열이 나오려면 보정이 1.5SD에도 걸려야 한다. 고치지 않으면 1.5SD의 `MN`이 128이 되어 iteration 125~128이 파일 범위를 넘고 매 iteration 오류를 찍으며 row 0으로 돈다. 다만 이 줄은 저장소 사본이 컴파일되지 않는 지점이므로 **외부 소스의 해당 줄을 먼저 확인받아야 한다**. 외부 소스가 이미 `MODE_DEC_1_5SD`이면 처방은 문서 명시만 남는다 | **MEDIUM 유지.** 단 식별자 항목은 "적용 전 확인 전제"로 따로 세우기를 권한다. `ITER_MAX_HBF` 4와 1.5SD 모드가 함께 쓰이면 HIGH로 올라간다 |

---

## ㉱ 검증 중 새로 드러난 사실

- ㉮ **code_diff 8.1과 8.2는 AUTO 빌드에 아무 기여를 하지 않는다.** 8.1의 수정 후 코드가 현 AUTO 갈래([decoder.cpp:6542-6565](../../../../../../0_LDPC_original/src/decoder.cpp))와 한 줄씩 같고 8.2는 "조건은 그대로 둔다"라 적는다. 두 장이 실제로 하는 일은 비AUTO 갈래 삭제뿐이며 그것이 R2-1의 원인이다. 따라서 처방은 "갈래를 유지한다"보다 "8.1과 8.2를 계획에서 뺀다"로 적는 편이 정확하고 잃는 것이 없다.
- ㉯ **AUTO 빌드도 `matrix_sel`이 1이 아닐 수 있다.** [main.cpp:140-143](../../../../../../0_LDPC_original/src/main.cpp)의 AUTO 갈래는 `argc > 19`이면 H-matrix 파일 이름을 인자로 받고 `matrix_sel` 값을 검사하지 않는다. 이 사실은 R2-1 처방의 뒷부분을 무효로 만들고, 동시에 R2-9(분기 수 대조)가 든 도달 경로를 뒷받침한다.
- ㉰ **`m_param_LLR`에 미결정 값이 담기는 것은 이미 오늘의 코드에서 일어난다.** [ecc_top.cpp:208](../../../../../../0_LDPC_original/src/ecc_top.cpp)이 세워지지 않은 `ECC_Top::m_param_LLR`을 5인자 `Init_Dec`에 넘겨 [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp)이 그대로 받는다. 지금은 비AUTO에서 이 포인터를 읽는 코드가 없어 드러나지 않을 뿐이다. 곧 R2-1은 새 결함을 만드는 것이 아니라 잠자던 결함을 깨우는 것이며, 4인자 `Init_ECC_Top`에 `m_param_LLR = NULL;` 한 줄을 넣는 것은 어느 처방을 고르든 함께 해 둘 값어치가 있다.
- ㉱ **9장을 다 밟아도 빌드되지 않는다.** 단계별로 남는 깨진 줄은 2단계 뒤 AUTO 8줄과 비AUTO 20줄, 3단계 뒤 AUTO 8줄과 비AUTO 16줄, 4단계 뒤 양쪽 612-613이다. 6장은 AUTO 갈래만 건드리므로 AUTO 빌드의 깨진 줄을 하나도 줄이지 못한다. R2-2를 함께 고쳐야 비로소 5단계가 성립한다.
- ㉲ **9장의 1.2장 이중 배정.** 1단계가 "1장과 2장"이라 1.2장을 포함하는데 5단계가 다시 "1.2장, 7장, 8장"이라 적는다. 1.2가 1단계에 들면 [local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp)이 iteration 수열을 바꾸어 3단계의 결과 비교가 그 자체로 성립하지 않는다.
- ㉳ **6.1 제목의 줄 범위 오기.** 제목은 "6973-6999행"이나 실제 교체 범위는 비AUTO 갈래를 포함한 6973-7047이다. 이 오기 때문에 "지워지는 멤버의 참조가 6.1에서 처리된다"는 사실이 독자에게 보이지 않고, R2-2의 "남는 것은 612-613뿐"이 확인 불가능해 보인다.
- ㉴ **상위 문서 3장의 과한 일반화.** "결과는 항상 첫 번째 row"는 `type_each_group`이 20 또는 21인 그룹 0~5가 덮는 iteration 1~8에만 해당한다. 그룹 6~11이 덮는 iteration 9~124는 CSW 갈래가 정상 동작한다.
- ㉵ **저장소 사본은 기본 빌드에서 컴파일되지 않는다.** [build.bat](../../../../../../0_LDPC_original/src/build.bat)이 `local_opt.cpp`를 조건 없이 컴파일하고 그 파일 124행의 `MODE_DEC_1_SSD`가 정의되지 않았다. 곧 Round 2와 Round 3의 모든 빌드 성립 판정은 이 한 줄이 외부 소스에서 올바른 이름이라는 전제 위에 있다. 사용자에게 외부 소스의 이 줄을 확인받는 것이 R2-15와 R2-1 양쪽의 전제를 굳힌다.
- ㉶ **R2-12와 R2-1은 한 결정이다.** 상위 7장 ㉱("비AUTO 갈래 통일")를 "통일한다"로 결정하면 R2-1의 결함과 함께 `decoder.cpp:1137-1141`에서 같은 결함이 재발한다. "통일하지 않는다"로 결정하면 8.1과 8.2를 빼고 1137-1141을 그대로 두는 것으로 양쪽이 한 번에 닫힌다. 두 발견을 따로 올리면 사용자가 상충하는 결정을 내릴 수 있다.

---

## ㉲ 워커 사이가 갈린 곳과 리더 확정

| 항목 | 워커별 주장 | 리더 판정 |
|------|------------|----------|
| 3단계 비교용 파일의 `type_each_group` | V1_3은 원래 값(20, 21)을 두어야 새 코드도 row 0을 돌려주어 일치한다고 했다. V1_2는 1로 교정해야 한다고 했다 | **V1_2가 맞다.** [code_diff.md 679행과 718행](../../code_diff.md#ch6)이 `table_row_idx` 초기값을 0에서 -1로 바꾼다. `type`이 20 또는 21이면 [decoder.cpp:7051, 7059](../../../../../../0_LDPC_original/src/decoder.cpp)의 두 조건이 모두 거짓이라 값이 초기값에 머물러 옛 코드는 0을, 새 코드는 -1을 돌려준다. 곧 교정하지 않으면 결과가 갈린다. `type`을 1로 두면 [decoder.cpp:7060](../../../../../../0_LDPC_original/src/decoder.cpp)이 언제나 먼저 실행되어 양쪽이 같아진다 |
| `local_opt.cpp`가 모든 빌드에 들어가는가 | V1_3은 빌드 파일이 저장소에 없어 확정할 수 없다고 유보했다. V1_1은 [build.bat](../../../../../../0_LDPC_original/src/build.bat)을 근거로 늘 들어간다고 했다 | **V1_1이 맞다.** 리더가 [build.bat](../../../../../../0_LDPC_original/src/build.bat)을 직접 읽었다. `cl` 명령의 소스 목록에 `local_opt.cpp`가 조건 없이 들어 있고, `mode.h` 그대로의 Windows 빌드는 비AUTO다. 곧 저장소 사본은 기본 빌드에서 124행 때문에 서지 않는다 |
| `Is_Iter_Type_Init`의 역참조 범위 | Round 2는 두 함수가 모두 매 iteration 역참조한다고 적었다. V1_1과 리더는 `Is_Iter_Type_Init`이 HD와 1.5SD에서는 역참조하지 않음을 확인했다 | **정밀화 반영.** [decoder.cpp:6610-6614](../../../../../../0_LDPC_original/src/decoder.cpp)의 HD와 1.5SD 경로에는 `m_param_LLR` 접근이 없다. 결론(R2-1의 결함 성립)은 `Is_Iter_Type_Edge_Clear` 하나로 이미 충분하므로 심각도는 바뀌지 않는다 |
