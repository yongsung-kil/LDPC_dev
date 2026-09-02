# Round 2 워커 I_4: 관점 8 (비AUTO 빌드 안전성과 컴파일 스위치 조합)

> 작성: 2026-09-03 01:13:44
> 팀 I (iteration 번호 체계와 빌드 갈래)

## 확인 범위

| 파일 | 읽은 줄 | 확인한 것 |
|------|--------|----------|
| [mode.h](../../../../../../0_LDPC_original/src/mode.h) | 1-82 (전체) | `__AUTO_LLR_OPT__` 정의 조건, `__RUN_MPI__` 활성 조건, 일곱 개 스위치의 현재 값 |
| [main.cpp](../../../../../../0_LDPC_original/src/main.cpp) | 40-199, 490-520 | 진입점 세 갈래, `Init_ECC_Top` 호출 인자, `Setup_Ref_C`와 `Setup_TV_Gen`의 `matrix_sel`과 `init_n` 허용 범위 |
| [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) | 1-60, 180-250, 860-863, 1115, 1246, 1336 | 생성자의 포인터 초기화 목록, `Init_ECC_Top` 세 오버로드, `LDPC_Decoder` 호출 오버로드 |
| [ecc_top.h](../../../../../../0_LDPC_original/src/ecc_top.h) | 94 | `m_param_LLR` 선언 |
| [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) | 1-45, 425-524, 600-620, 974-1044, 1110-1190, 1805-1839, 1955-1984, 2060-2135, 2160-2208, 2295-2335, 6530-6670, 6960-7080, 7207-7240, 8050-8115 | `m_param_LLR` 대입 지점 전수, `Select_BF`, `Is_Iter_Type_*`, `Get_Cur_LLR_Idx_FILE`, `Get_VNU_Table_Idx`, `Adjust_HD_Floor_Type`, PCRC 종료 조건 |
| [decoder.h](../../../../../../0_LDPC_original/src/decoder.h) | 24-27, 47, 124-125, 158-159, 212, 296-306 | `Init_Dec` 오버로드, `m_corner`, 지워지는 멤버 |
| [common.h](../../../../../../0_LDPC_original/src/common.h) | 75-78, 190-259, 402-408, 679-686, 717-725 | 모드 상수, SW 문턱 상수 두 갈래, `ITER_MAX_HBF`, `RSP1_*` |
| [corner.h](../../../../../../0_LDPC_original/src/corner.h) | 60-94 | `IDX_FLAG_HD_5_8_SET_TYPE_*` 연속성 |
| [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) | 110-139 | `MN` 보정에 걸린 `ITER_MAX_HBF` |
| grep 전수 | `ITER_MAX_HBF`, `m_param_LLR`, `m_corner`, `Is_Iter_Type_*`, `Get_Cur_LLR_Idx_FILE`, `flag_HD_*_Set`, `syn_th_*` | 호출처와 참조처 확인 |
| 리뷰 대상 | [상위 문서](../../20260902_SW_branch_LLR_matrix.md) 5.3, 5.5, 5.6, 6장, 7장 / [code_diff.md](../../code_diff.md) 4.1, 5.1, 6.1, 8.1, 8.2, 8.3 | |

전제로 확인한 현재 스위치 값 ([mode.h](../../../../../../0_LDPC_original/src/mode.h)):

| 스위치 | 줄 | 현재 값 |
|--------|-----|--------|
| `__PROGRAM_MODE_REF_C__` | 8 | 꺼짐 (주석) |
| `__AUTO_LLR_OPT__` | 22 | 꺼짐 (`__PROGRAM_MODE_REF_C__`가 꺼져 있어 정의되지 않음) |
| `__RUN_MPI__` | 10, 24 | 꺼짐 |
| `__12META__` | 11 | 꺼짐 |
| `__RUN_PREPROCESSING__` | 63 | 꺼짐 |
| `__DUAL_UPDATE__` | 64 | **켜짐** |
| `__HD_FLOOR_SET__` | 73 | 꺼짐 |
| `__CORNER_CHECKER__` | 75 | 꺼짐 |
| `__RUN_ITER34_HIGH_DV_SKIP__` | 78 | 꺼짐 |
| `__RUN_PARITY_SKIP__` | 79 | 꺼짐 |
| `__PROGRAM_MODE_TV_GEN__` | 38 | **켜짐** (`__PROGRAM_MODE_REF_C__`가 꺼져 있을 때) |

즉 저장소에 들어 있는 mode.h 그대로 빌드하면 비AUTO의 TV Gen 빌드가 된다. 아래 F1, F3, F4는 그 구성에서 바로 걸린다.

**컴파일 실패의 심각도 판정**: 컴파일 실패는 빌드 시점에 바로 드러나고 잘못된 결과를 만들지 않으므로 데이터 손상이 없다. 다만 작업 전체를 멈추므로 CRITICAL로 적되, 발견 시점이 빌드 시점임을 함께 적는다. 실행 시점에야 드러나는 F1이 더 위험하다.

---

## ㉮ 수정 후 코드를 그대로 적용하면 생기는 결함

### F1. CRITICAL: 비AUTO 빌드에서 `m_param_LLR`이 미초기화 포인터인 채 역참조된다

[code_diff.md 8.1](../../code_diff.md#ch8)과 8.2가 `#if defined(__AUTO_LLR_OPT__)` 갈래만 남기면, 남는 코드가 `m_param_LLR->restart_num`과 `m_param_LLR->restart_iter[i]`를 조건 없이 읽는다. 비AUTO 빌드에서 이 포인터는 어떤 값도 대입받은 적이 없다.

근거 (전부 소스 확인):

- ㉮ `ECC_Top::ECC_Top()`의 포인터 초기화 목록([ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp#L6-L34))에 `m_param_LLR`이 없다. 다른 포인터 열아홉 개는 모두 `NULL`로 초기화된다
- ㉯ 4인자 `Init_ECC_Top`([ecc_top.cpp:197-210](../../../../../../0_LDPC_original/src/ecc_top.cpp#L197-L210))은 `m_param_LLR`을 세우지 않은 채 [ecc_top.cpp:208](../../../../../../0_LDPC_original/src/ecc_top.cpp#L208)에서 그 값을 `Init_Dec`에 넘긴다. 5인자 오버로드([ecc_top.cpp:216-230](../../../../../../0_LDPC_original/src/ecc_top.cpp#L216-L230))만 `m_param_LLR = param_LLR`을 한다
- ㉰ `Decoder::Initialize_Dec`([decoder.cpp:19-...](../../../../../../0_LDPC_original/src/decoder.cpp#L19))의 초기화 목록에 `m_param_LLR`이 없다. grep 결과 `Decoder::m_param_LLR`에 대입하는 곳은 [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp#L436) 한 곳뿐이고, 그것은 5인자 `Init_Dec`이다
- ㉱ 비AUTO 진입점은 `Run_Simulation_Ref_C`([main.cpp:105](../../../../../../0_LDPC_original/src/main.cpp#L105))와 `Run_Simulation_TV_Gen`([main.cpp:127](../../../../../../0_LDPC_original/src/main.cpp#L127))이고, 둘 다 4인자 `Init_ECC_Top`을 부른다
- ㉲ `Is_Iter_Type_Edge_Clear`는 컴파일 스위치와 무관하게 [decoder.cpp:712, 726, 2314, 2321, 2328, 3491, 3498, 3504](../../../../../../0_LDPC_original/src/decoder.cpp#L712)에서 불린다. `Is_Iter_Type_Init`은 [decoder.cpp:2578, 2602, 2783, 2863, 2977, 2993, 5700, 5708, 5716, 5740, 5748, 5756, 5824, 5903, 6058, 6139](../../../../../../0_LDPC_original/src/decoder.cpp#L2578)에서 불린다. 두 함수 모두 매 iteration 실행된다

결과는 정해지지 않은 주소에서 `restart_num`을 읽고 그 값만큼 `restart_iter[]`를 훑는 것이다. 즉시 segmentation fault가 나거나, 쓰레기 값이 큰 정수로 읽혀 긴 루프를 돌다 죽는다.

같은 이유로 [code_diff.md 6.1](../../code_diff.md#ch6)의 합친 `Get_Cur_LLR_Idx_FILE`도 비AUTO 빌드에서 `m_param_LLR`을 읽지만, 이 함수는 비AUTO에서 불리지 않으므로(F5 아래 D1 참조) 실행 결함은 없다.

처방: 두 함수를 `#if defined(__AUTO_LLR_OPT__)` 갈래로 그대로 두거나, `m_param_LLR`을 생성자와 `Initialize_Dec`에서 `NULL`로 초기화하고 `NULL == m_param_LLR`이면 restart 루프를 건너뛰게 한다. **이 처방은 code_diff 8.1과 8.2가 요구한 코드 삭제를 되돌린다** (동작 변경 요구: 아니오, 기존 동작 보존 요구).

### F2. HIGH: 비AUTO 2SD와 3SD의 restart iteration이 통째로 사라진다

F1을 고쳐 포인터를 안전하게 만들어도 남는 결함이다.

비AUTO 원본은 2SD와 3SD의 restart 지점을 컴파일 상수로 못박아 두었다.

- ㉮ edge clear: [decoder.cpp:6577-6593](../../../../../../0_LDPC_original/src/decoder.cpp#L6577-L6593)
- ㉯ init: [decoder.cpp:6633-6669](../../../../../../0_LDPC_original/src/decoder.cpp#L6633-L6669)
- ㉰ 값: `RSP1_2SD_PRIME_1 = 241`, `RSP1_2SD_PRIME_2 = 581`, `RSP1_3SD_PRIME_1..6 = 171, 312, 653, 844, 1035, 1301` ([common.h:679-686](../../../../../../0_LDPC_original/src/common.h#L679-L686))

8.1과 8.2가 남기는 AUTO 갈래는 이 자리를 `m_param_LLR->restart_iter[]`로 대체한다. 비AUTO 빌드에는 LLR matrix 파일 자체가 없으므로 이 배열이 채워질 경로가 없고, 위 여덟 개 지점의 edge clear와 초기화가 전부 빠진다.

2SD와 3SD가 비AUTO에서 실제로 도는지 확인했다: `Setup_Ref_C`는 `MODE_DEC_HD <= init_n <= MODE_DEC_1_5SD`만 거른다([main.cpp:167-172](../../../../../../0_LDPC_original/src/main.cpp#L167-L172)). 상수는 `MODE_DEC_HD = 1`, `MODE_DEC_2SD = 2`, `MODE_DEC_3SD = 3`, `MODE_DEC_1_5SD = 4`([common.h:75-78](../../../../../../0_LDPC_original/src/common.h#L75-L78))이므로 2SD와 3SD가 범위 안이다. 즉 죽은 경로가 아니다.

처방: F1과 같다. 비AUTO 갈래를 유지한다 (동작 변경 요구: 아니오).

### F3. HIGH: TV Gen 빌드에서 `matrix_sel`이 1이 아닐 때 edge clear와 init 시점이 새로 생긴다

비AUTO 원본은 두 함수 전체를 `LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel` 안에 두었다([decoder.cpp:6567](../../../../../../0_LDPC_original/src/decoder.cpp#L6567), [decoder.cpp:6627](../../../../../../0_LDPC_original/src/decoder.cpp#L6627)). 그 밖의 `matrix_sel`에서는 `bClear`와 `bInit`가 `FALSE`로 남는다. 8.1과 8.2가 남기는 AUTO 갈래에는 이 `matrix_sel` 조건이 없다.

`Setup_TV_Gen`은 `LAYOUT_PRIME_512B_TLC_VSS_OFF <= matrix_sel`을 모두 받는다([main.cpp:500](../../../../../../0_LDPC_original/src/main.cpp#L500), `LAYOUT_PRIME_512B_TLC_VSS_OFF = 1`은 [common.h:193](../../../../../../0_LDPC_original/src/common.h#L193)). 따라서 `matrix_sel`이 2 이상인 TV 생성에서 iteration 0, 1, 5에 edge clear가 새로 걸리고 iteration 0에 init이 새로 걸린다.

TV 출력 hex 포맷은 변경 금지 대상이다(루트 [CLAUDE.md](../../../../../../CLAUDE.md) 공통 규칙 ㉯). 포맷 자체는 그대로지만 담기는 값이 달라진다. 두 문서 어디에도 이 조건 제거가 적혀 있지 않다.

처방: 합친 갈래에 `matrix_sel` 조건을 유지하거나, 비AUTO 갈래를 그대로 둔다 (동작 변경 요구: 아니오).

### F4. MEDIUM: `__CORNER_CHECKER__` 조합에서 Corner 이벤트의 대상과 시점이 바뀐다

[code_diff.md 5.1](../../code_diff.md#ch5)의 수정 후 코드는 `m_corner->Event_Flag(...)`를 `Select_BF` 끝에서 모드 구분 없이 한 번 부른다. 원본은 HD의 BF 진입, HD의 BF 미진입, 1.5SD 세 갈래 안에서만 불렀다([decoder.cpp:2093, 2102, 2108, 2119, 2125](../../../../../../0_LDPC_original/src/decoder.cpp#L2093)).

- ㉮ Ref-C 빌드에서 2SD와 3SD 프레임마다 `IDX_FLAG_HD_5_8_SET_TYPE_0`이 새로 찍힌다. 수정 후 코드에서 2SD와 3SD는 `else { flag_BF_on = FLAG_LOW; }`로 빠지지만 `cur_sw_branch_idx[1]`은 함수 앞머리에서 0으로 초기화되므로 `TYPE_0`이 찍힌다. Corner 통계의 뜻이 달라진다
- ㉯ TV Gen 빌드에서 `m_corner`는 `NULL`이다. TV Gen 경로는 `io_corner` 없는 오버로드를 쓰고([ecc_top.cpp:1115, 1246, 1336](../../../../../../0_LDPC_original/src/ecc_top.cpp#L1115)), 그 오버로드가 마지막 인자로 `NULL`을 넘긴다([decoder.cpp:994](../../../../../../0_LDPC_original/src/decoder.cpp#L994)). 다만 [decoder.cpp:2072-2076](../../../../../../0_LDPC_original/src/decoder.cpp#L2072-L2076)이 이미 같은 조합에서 `m_corner`를 무조건 역참조하므로, 이는 새로 생기는 결함이 아니라 기존 결함이 한 지점 늘어나는 것이다

처방: Corner 이벤트를 HD와 1.5SD 갈래 안에 두어 원래 범위를 지킨다 (동작 변경 요구: 예, 5.1의 수정 후 코드를 고쳐야 한다).

### F5. MEDIUM: `__DUAL_UPDATE__`가 켜진 상태에서 `ITER_MAX_HBF` 0→4가 PCRC 조기 종료 조건을 바꾼다

[decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp#L2169)의 `if (((mn == 1) || (mn == ITER_MAX_HBF + 1)))`은 지금은 `mn == 1 || mn == 1`이라 iteration 1에서만 참이다. 4로 바꾸면 iteration 5에서도 참이 되어, iteration 5가 "마지막 termination point에서만 종료할 수 있는 iteration"이 된다([decoder.cpp:2170-2176](../../../../../../0_LDPC_original/src/decoder.cpp#L2170-L2176)). 지금은 iteration 5가 `else` 갈래로 가서 네 개 termination point 어디서나 종료할 수 있다([decoder.cpp:2177-2188](../../../../../../0_LDPC_original/src/decoder.cpp#L2177-L2188)).

`__DUAL_UPDATE__`는 켜져 있다([mode.h:64](../../../../../../0_LDPC_original/src/mode.h#L64)). 이 변화는 throughput 최적화가 목표인 이 작업에서 iteration 5의 종료 시점을 직접 바꾸므로 결과에 바로 나타난다. 상위 문서 5.5장 표에 이 줄이 없다.

꺼진 스위치에도 같은 형태가 있다. 지금은 꺼져 있으므로 결함은 아니지만, 켜는 순간 함께 움직인다.

| 스위치 | 줄 | `ITER_MAX_HBF` 0→4가 바꾸는 것 |
|--------|-----|------------------------------|
| `__RUN_PARITY_SKIP__` (꺼짐) | [decoder.cpp:1448](../../../../../../0_LDPC_original/src/decoder.cpp#L1448), [1622](../../../../../../0_LDPC_original/src/decoder.cpp#L1622), [1828](../../../../../../0_LDPC_original/src/decoder.cpp#L1828) | parity skip과 클럭 보정이 mn 1에서만 걸리던 것이 mn 1과 5 두 번 걸린다 |
| `__RUN_ITER34_HIGH_DV_SKIP__` (꺼짐) | [decoder.cpp:6454](../../../../../../0_LDPC_original/src/decoder.cpp#L6454) | skip 대상 iteration이 3, 4에서 7, 8로 옮겨간다 |
| `__RUN_PREPROCESSING__` (꺼짐) | [decoder.cpp:1821](../../../../../../0_LDPC_original/src/decoder.cpp#L1821), [2310](../../../../../../0_LDPC_original/src/decoder.cpp#L2310), [3487](../../../../../../0_LDPC_original/src/decoder.cpp#L3487) | Preprocessing 클럭 가산과 `Intentional_Blank` 시점이 iteration 1에서 5로 옮겨간다 |

처방: 상위 문서 5.5장 표에 [decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp#L2169)와 위 세 줄을 스위치 이름과 함께 넣는다 (동작 변경 요구: 아니오, 문서 보강).

### F6. MEDIUM: `__12META__`를 켜면 [code_diff.md 4.1](../../code_diff.md#ch4)이 쓰는 두 상수가 정의되지 않는다 (기존 결함을 물려받음)

[common.h:200-227](../../../../../../0_LDPC_original/src/common.h#L200-L227)의 `__12META__` 갈래에 `SW_TH_BF0_512B_TLC_OFF`와 `SW_TH_BF1_512B_TLC_OFF`가 없다. 두 상수는 `#else` 갈래([common.h:236-237](../../../../../../0_LDPC_original/src/common.h#L236-L237))에만 있다.

4.1이 쓰는 나머지 상수는 양쪽 갈래에 모두 있다: `SW_TH_BF_DEFAULT`([common.h:202](../../../../../../0_LDPC_original/src/common.h#L202), [231](../../../../../../0_LDPC_original/src/common.h#L231)), `SW_TH_5_8_SET0_512B_TLC_OFF`([215](../../../../../../0_LDPC_original/src/common.h#L215), [244](../../../../../../0_LDPC_original/src/common.h#L244)), `SW_TH_5_8_SET0_DEFAULT`([211](../../../../../../0_LDPC_original/src/common.h#L211), [240](../../../../../../0_LDPC_original/src/common.h#L240)), `SW_TH_5_8_SET1_512B_TLC_OFF`([224](../../../../../../0_LDPC_original/src/common.h#L224), [251](../../../../../../0_LDPC_original/src/common.h#L251)).

**이는 기존 결함이다.** 지금 소스도 [decoder.cpp:467-468](../../../../../../0_LDPC_original/src/decoder.cpp#L467-L468)에서 같은 두 상수를 쓰므로 `__12META__`를 켜면 이미 컴파일되지 않는다. 계획이 새로 만들지 않고 그대로 물려받는다. `__12META__`가 꺼져 있고 계획이 원인이 아니므로 MEDIUM으로 적는다 (켜면 컴파일 실패이므로 그 상황에서는 CRITICAL).

처방: `__12META__` 갈래에 두 상수를 추가한다. code_diff 4.1이 "값은 기존 상수에서 가져온다"고 전제했으므로, 이 전제가 `__12META__` 조합에서 성립하지 않는다는 것을 문서에 적는다 (동작 변경 요구: 아니오).

### F7. MEDIUM: `__HD_FLOOR_SET__`을 켜면 `Adjust_HD_Floor_Type`이 컴파일되지 않는다 (기존 결함, 계획이 다루지 않음)

[decoder.cpp:8073](../../../../../../0_LDPC_original/src/decoder.cpp#L8073)이 여는 `if`는 [decoder.cpp:8076](../../../../../../0_LDPC_original/src/decoder.cpp#L8076)에서 닫히는데, [decoder.cpp:8082](../../../../../../0_LDPC_original/src/decoder.cpp#L8082)에 닫는 괄호가 하나 더 있다. 그 결과 [decoder.cpp:8083](../../../../../../0_LDPC_original/src/decoder.cpp#L8083)의 `else`가 짝을 잃는다. `__CORNER_CHECKER__`를 켜든 끄든(8077-8081) 괄호 셈이 맞지 않는다.

`Adjust_HD_Floor_Type`은 [code_diff.md 6.1](../../code_diff.md#ch6)의 수정 후 코드가 그대로 부른다([decoder.cpp:6980-6982](../../../../../../0_LDPC_original/src/decoder.cpp#L6980-L6982)). `__HD_FLOOR_SET__`은 꺼져 있어([mode.h:73](../../../../../../0_LDPC_original/src/mode.h#L73)) 지금 문제되지 않으며, 루트 [CLAUDE.md](../../../../../../CLAUDE.md)가 원본 소스 일부 손상을 밝히고 있으므로 계획의 결함이 아니다. 다만 "이 계획을 적용한 뒤 `__HD_FLOOR_SET__`을 켜서 error floor 대응과 throughput 최적화를 함께 보겠다"는 후속 작업은 이 지점에서 막힌다.

### F8. CRITICAL(빌드 시점): 지워지는 멤버를 `Clear_Flag`가 여전히 대입한다

[code_diff.md 2.2](../../code_diff.md#ch2)가 `flag_HD_1_4_Set`과 `flag_HD_5_8_Set`을 지우지만, [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp#L612-L613)의 `Clear_Flag`가 두 멤버에 대입하고 code_diff에 이 자리의 수정 후 코드가 없다. 두 빌드 모두 컴파일되지 않는다.

같은 형태로 [decoder.h:301](../../../../../../0_LDPC_original/src/decoder.h#L301) `syn_th_BF`와 [decoder.h:303](../../../../../../0_LDPC_original/src/decoder.h#L303) `syn_th_BF1`을 지우면 [decoder.cpp:472](../../../../../../0_LDPC_original/src/decoder.cpp#L472)의 `default: { syn_th_BF = SW_TH_BF_DEFAULT; break; }`가 code_diff 4.1로 대체되므로 그쪽은 닫힌다.

이 항목의 전수 조사는 관점 9(팀 D)의 몫이므로 여기서는 비AUTO 빌드가 함께 깨진다는 사실만 적는다.

---

## ㉯ 문서 서술 자체의 오류

### D1. MEDIUM: `Get_Cur_LLR_Idx_FILE`의 비AUTO 갈래는 실행되지 않는 코드다

상위 문서 5.3-4와 7장 ㉱이 [decoder.cpp:7001-7020](../../../../../../0_LDPC_original/src/decoder.cpp#L7001-L7020)을 "비AUTO 경로의 하드코딩"으로 다루며, 걷어낼지 그대로 둘지를 미결정 사항으로 남겼다. 확인 결과 이 갈래는 어느 빌드에서도 실행되지 않는다.

- ㉮ `Get_Cur_LLR_Idx_FILE`을 부르는 곳은 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp#L1138) 한 곳이고, 그 줄은 [decoder.cpp:1137](../../../../../../0_LDPC_original/src/decoder.cpp#L1137)의 `#if defined(__AUTO_LLR_OPT__)` 안에 있다 (grep 전수 확인)
- ㉯ 비AUTO는 [decoder.cpp:1140](../../../../../../0_LDPC_original/src/decoder.cpp#L1140)의 `Get_VNU_Table_Idx(mn)`를 쓰고, 그 함수는 [decoder.cpp:7207-7210](../../../../../../0_LDPC_original/src/decoder.cpp#L7207-L7210)에서 무조건 0을 돌려준다
- ㉰ 함수 정의 자체는 `#if`로 감싸지 않아 비AUTO에서도 컴파일된다. 즉 컴파일만 되고 실행되지 않는 죽은 코드다

따라서 5.3-4의 마지막 문장 "`1_4_Set`이 `TYPE_1`인 경우 `selected_group`이 -1로 남아 오류 출력으로 빠지는 것도 같이 정리해야 한다"는 일어날 수 없는 상황을 결함으로 적은 것이다. 7장 ㉱은 동작에 영향이 없고 코드 삭제 여부만 정하는 결정인데, 문서가 이를 밝히지 않아 사용자가 동작 위험이 있는 결정으로 오해할 수 있다.

처방: 5.3-4와 7장 ㉱에 "이 갈래는 실행되지 않는 코드이며 정리는 가독성 문제"라고 적는다 (동작 변경 요구: 아니오).

### D2. MEDIUM: [code_diff.md 8.3](../../code_diff.md#ch8)이 인용한 Preprocessing 조건에 감싸는 스위치가 빠져 있다

8.3은 [decoder.cpp:1148-1150](../../../../../../0_LDPC_original/src/decoder.cpp#L1148-L1150)만 인용하고 "두 수정이 들어가면 BF 진입 여부에 따라 1 또는 5로 갈린다"고 적었다. 실제로는 그 위에 두 겹이 더 있다.

- ㉮ [decoder.cpp:1146](../../../../../../0_LDPC_original/src/decoder.cpp#L1146) `#if defined (__RUN_PREPROCESSING__)`. 이 스위치는 꺼져 있다([mode.h:63](../../../../../../0_LDPC_original/src/mode.h#L63))
- ㉯ [decoder.cpp:1147](../../../../../../0_LDPC_original/src/decoder.cpp#L1147) `if ((MODE_DEC_HD == init_n) || (MODE_DEC_1_5SD == init_n))`

현재 구성에서는 `Preprocessing()`이 아예 실행되지 않으므로 8.3의 서술이 성립하지 않는다. 인용 블록에 `#if` 줄이 없어 읽는 사람이 이 조건을 알 수 없다.

처방: 인용 범위를 [decoder.cpp:1146-1156](../../../../../../0_LDPC_original/src/decoder.cpp#L1146-L1156) 전체로 넓히고, 서술을 "`__RUN_PREPROCESSING__`을 켰을 때"로 한정한다 (동작 변경 요구: 아니오).

### D3. MEDIUM: `__RUN_MPI__`는 어느 조합에서도 켜지지 않는다

상위 문서 6.3이 [mode.h:22-26](../../../../../../0_LDPC_original/src/mode.h#L22-L26)을 "`__PROGRAM_MODE_REF_C__`이고 Windows가 아닐 때만 켜진다"고 적었다. `__AUTO_LLR_OPT__`에 대해서는 맞다. 그러나 같은 블록의 `#if !defined(__AUTO_LLR_OPT__)`([mode.h:23](../../../../../../0_LDPC_original/src/mode.h#L23))는 바로 앞 줄([mode.h:22](../../../../../../0_LDPC_original/src/mode.h#L22))에서 `__AUTO_LLR_OPT__`를 정의한 직후이므로 항상 거짓이고, [mode.h:10](../../../../../../0_LDPC_original/src/mode.h#L10)의 `//#define __RUN_MPI__`도 주석이다. 따라서 `__RUN_MPI__`는 어느 조합에서도 켜지지 않고, [code_diff.md 3.7](../../code_diff.md#ch3)은 컴파일되지 않는 블록에 대한 수정이다.

관점 11(팀 P)과 겹치므로 판정만 남긴다. code_diff 3.7이 스스로 "어느 쪽인지 확인한 뒤 맞춘다"고 적어 미확인 상태임을 밝힌 것은 정확하다.

### D4. LOW: "12곳"이라는 셈이 `ITER_MAX_HBF` 전수와 맞지 않는다

[code_diff.md 1.2](../../code_diff.md#ch1_2)가 "이 상수를 쓰는 12곳(상위 문서 5.5장 표)이 모두 같은 값으로 돌아간다"고 적었으나, grep 전수에서 표 밖 히트가 있다: [decoder.cpp:1448, 1622, 1828, 2169, 2190](../../../../../../0_LDPC_original/src/decoder.cpp#L1448)과 로그 버퍼 크기 계산 [decoder.cpp:7717, 7751, 7782, 7812, 7877, 7889, 7898, 7921, 7931](../../../../../../0_LDPC_original/src/decoder.cpp#L7717). 전수 대조는 관점 6이 맡으므로 여기서는 스위치가 걸린 것만 F5에 적었다.

---

## 관점 8 확인 항목별 판정 요약

| 확인 항목 | 판정 |
|----------|------|
| 비AUTO 빌드에서 `m_param_LLR`이 설정되는가 | **설정되지 않는다.** 미초기화 포인터 (F1) |
| 8.1과 8.2가 `restart_num`을 무조건 읽는 문제 | **CRITICAL.** 비AUTO에서 비정의 동작, 고쳐도 2SD와 3SD의 restart 상실 (F1, F2) |
| `Get_Cur_LLR_Idx_FILE`의 `#else`가 죽은 코드인가, 문서 서술과 맞는가 | **죽은 코드다.** 상위 문서 5.3-4와 7장 ㉱의 서술이 이를 반영하지 않는다 (D1) |
| 비AUTO 2SD와 3SD의 `RSP1_*` 하드코딩 대체 시 동작 변화 | **여덟 개 restart 지점이 전부 사라진다** (F2) |
| `mode.h:18-27`의 AUTO 조건과 `__RUN_MPI__` 활성 조건 | AUTO는 Ref-C이고 비Windows일 때. `__RUN_MPI__`는 어느 조합에서도 켜지지 않는다 (D3) |
| `__12META__` 조합에서 `common.h:200-227`의 상수 유무 | `SW_TH_BF0_512B_TLC_OFF`와 `SW_TH_BF1_512B_TLC_OFF`만 없다. **기존 결함을 물려받는다** (F6) |
| `__HD_FLOOR_SET__` | 켜면 `Adjust_HD_Floor_Type`이 컴파일되지 않는다. 기존 결함 (F7) |
| `__CORNER_CHECKER__` | Corner 이벤트가 2SD와 3SD로 번지고, TV Gen에서 NULL 역참조가 한 지점 늘어난다 (F4) |
| `__RUN_PREPROCESSING__` | 꺼져 있어 8.3의 서술이 성립하지 않는다 (D2, F5) |
| `__DUAL_UPDATE__` | 켜져 있고, `ITER_MAX_HBF` 0→4가 iteration 5의 PCRC 종료 조건을 바꾼다. 문서 표에 없다 (F5) |
| `__RUN_PARITY_SKIP__` | 꺼져 있음. 켜면 skip과 클럭 보정이 두 번 걸린다 (F5) |
| `__RUN_ITER34_HIGH_DV_SKIP__` | 꺼져 있음. 켜면 skip 대상이 iteration 3, 4에서 7, 8로 옮겨간다 (F5) |

## 심각도별 건수

| 심각도 | 건수 | 항목 |
|--------|-----|------|
| CRITICAL | 2 | F1(실행 시점), F8(빌드 시점) |
| HIGH | 2 | F2, F3 |
| MEDIUM | 7 | F4, F5, F6, F7, D1, D2, D3 |
| LOW | 1 | D4 |
