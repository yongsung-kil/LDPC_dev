# Round 3 검증: 팀 V1 워커 1 (R2-1, R2-12)

작성: 2026-09-03 01:40:03

검증 대상: Round 2 발견 R2-1(CRITICAL)과 R2-12(MEDIUM)의 사실 가설과 처방 가설.
근거는 모두 [0_LDPC_original/src/](../../../../../0_LDPC_original/src/)의 현재 소스를 직접 읽어 확인했다.
코드와 문서는 수정하지 않았다.

전처리기 갈래 판정은 `/* */` 주석 안의 `#if`, `#endif`를 걷어낸 뒤 중첩 깊이를 세어 확인했다.
주석을 걷어내기 전에는 [decoder.cpp](../../../../../0_LDPC_original/src/decoder.cpp) 3013행의
주석 안 `#if`가 깊이를 어긋나게 만들어 판정이 뒤집힌다. 주석 제거 후 `#if` 310개와 `#endif` 310개로
균형이 맞고 최종 깊이가 0이다.

---

## 1. R2-1 증거 판정

### E1-1 `ECC_Top` 생성자가 `m_param_LLR`을 세우지 않는다 — 확인됨

[ecc_top.cpp:6-34](../../../../../0_LDPC_original/src/ecc_top.cpp#L6-L34)의 생성자는
`m_ecc_info`, `m_param_dec`, `m_param_ref_c`, `m_param_tv_gen`, 버퍼 포인터 열여덟 개,
`fp_uncor_seed`를 NULL로 두지만 `m_param_LLR`은 목록에 없다.
멤버 선언 [ecc_top.h:94](../../../../../0_LDPC_original/src/ecc_top.h#L94) `PARAM_LLR* m_param_LLR;`에
클래스 안 초기값도 없다. 따라서 `new ECC_Top()` 직후 이 포인터의 값은 정해지지 않는다.

`Decoder` 쪽도 같다. [decoder.cpp:5-8](../../../../../0_LDPC_original/src/decoder.cpp#L5-L8)의 생성자는
`Initialize_Dec()`만 부르고, [decoder.cpp:19-60](../../../../../0_LDPC_original/src/decoder.cpp#L19-L60)의
`Initialize_Dec`는 `m_ecc_info`(22행), `m_PCM`(23행), `m_param_dec`(24행)를 NULL로 두지만
`m_param_LLR`은 건드리지 않는다. 선언은
[decoder.h:210](../../../../../0_LDPC_original/src/decoder.h#L210)이고 여기에도 초기값이 없다.

### E1-2 4인자 `Init_ECC_Top`이 세우지 않은 값을 `Init_Dec`에 넘긴다 — 확인됨

- ㉮ 4인자 오버로드 [ecc_top.cpp:197-210](../../../../../0_LDPC_original/src/ecc_top.cpp#L197-L210):
  `m_ecc_info`, `m_param_dec`, `m_my_rank`, `m_num_process`만 세우고
  208행에서 `m_dec.Init_Dec(m_ecc_info, &m_PCM, m_param_dec, m_param_LLR, m_my_rank);`로
  세운 적 없는 `m_param_LLR`을 그대로 넘긴다
- ㉯ 5인자 오버로드 [ecc_top.cpp:216-230](../../../../../0_LDPC_original/src/ecc_top.cpp#L216-L230):
  222행 `m_param_LLR = param_LLR;`로 먼저 세우고 228행에서 넘긴다.
  두 오버로드의 차이는 오직 222행 한 줄이다
- ㉰ 2인자 오버로드 [ecc_top.cpp:236-247](../../../../../0_LDPC_original/src/ecc_top.cpp#L236-L247)는
  246행에서 `PARAM_LLR`이 없는 4인자 `Init_Dec`를 부른다.
  이 경로는 `Decoder::m_param_LLR`을 아예 대입하지 않으므로 역시 정해지지 않은 값으로 남는다

### E1-3 `m_param_LLR` 대입 전수 — 확인됨

식별자 `m_param_LLR`의 히트는 화살표 접근(`m_param_LLR->`)을 뺀 선언과 대입만 모아
아래 아홉 곳이고, 그중 대입은 두 곳뿐이다.

| 파일:줄 | 내용 | 종류 |
|---------|------|------|
| [decoder.cpp:436](../../../../../0_LDPC_original/src/decoder.cpp#L436) | `m_param_LLR = param_LLR;` | Decoder 대입 (유일) |
| [decoder.h:210](../../../../../0_LDPC_original/src/decoder.h#L210) | `PARAM_LLR* m_param_LLR;` | 선언 |
| [ecc_top.cpp:208](../../../../../0_LDPC_original/src/ecc_top.cpp#L208) | 4인자 `Init_ECC_Top`이 `Init_Dec`에 전달 | 읽기 |
| [ecc_top.cpp:222](../../../../../0_LDPC_original/src/ecc_top.cpp#L222) | `m_param_LLR = param_LLR;` | ECC_Top 대입 (유일) |
| [ecc_top.cpp:228](../../../../../0_LDPC_original/src/ecc_top.cpp#L228) | 5인자 `Init_ECC_Top`이 `Init_Dec`에 전달 | 읽기 |
| [ecc_top.h:94](../../../../../0_LDPC_original/src/ecc_top.h#L94) | `PARAM_LLR* m_param_LLR;` | 선언 |
| [local_opt.cpp:34](../../../../../0_LDPC_original/src/local_opt.cpp#L34) | `Read_LLR_info_Auto(&m_param_LLR, ...)` | LOCAL_OPT 값 멤버 |
| [local_opt.cpp:46](../../../../../0_LDPC_original/src/local_opt.cpp#L46) | `Init_ECC_Top(..., &m_param_LLR, ...)` | 5인자 호출 (유일) |
| [local_opt.h:30](../../../../../0_LDPC_original/src/local_opt.h#L30) | `PARAM_LLR m_param_LLR;` | 값 멤버 선언 |

`Decoder::m_param_LLR`에 대입하는 곳은 [decoder.cpp:436](../../../../../0_LDPC_original/src/decoder.cpp#L436)
하나뿐이고, 그 값의 출처는 인자로 받은 `param_LLR`이다.
`ECC_Top::m_param_LLR`에 대입하는 곳은 [ecc_top.cpp:222](../../../../../0_LDPC_original/src/ecc_top.cpp#L222)
하나뿐이며 5인자 오버로드 안에만 있다.

### E1-4 비AUTO 진입점이 4인자를 부른다 — 확인됨

- ㉮ [main.cpp:104-105](../../../../../0_LDPC_original/src/main.cpp#L104-L105) `Run_Simulation_Ref_C`가
  `Init_ECC_Top(&g_ecc_info, &g_param_dec, g_myrank, g_num_process)` (4인자)
- ㉯ [main.cpp:126-127](../../../../../0_LDPC_original/src/main.cpp#L126-L127) `Run_Simulation_TV_Gen`이
  같은 4인자 오버로드
- ㉰ 5인자를 부르는 곳은 [local_opt.cpp:46](../../../../../0_LDPC_original/src/local_opt.cpp#L46)
  하나뿐이다. 그 경로는 `LOCAL_OPT::Run_Simu_Curr_LLR`이고,
  `LOCAL_OPT` 객체를 만드는 곳은 [main.cpp:117](../../../../../0_LDPC_original/src/main.cpp#L117)
  `Run_Simulation_Local_Opt` 하나뿐이며,
  이 함수를 부르는 [main.cpp:93](../../../../../0_LDPC_original/src/main.cpp#L93)은
  [main.cpp:89-97](../../../../../0_LDPC_original/src/main.cpp#L89-L97)의
  `#if defined(__PROGRAM_MODE_TV_GEN__)`의 `#else` 안, 다시 `#if defined(__AUTO_LLR_OPT__)` 안에 있다

곧 `__AUTO_LLR_OPT__`가 정의되지 않으면 5인자 오버로드는 어디서도 불리지 않고,
`ECC_Top::m_param_LLR`은 프로그램 전체에서 한 번도 대입되지 않는다.

### E1-5 두 함수가 컴파일 스위치 없이 매 iteration 불린다 — 확인됨

`Is_Iter_Type_Edge_Clear` 호출 전수와 각 호출처의 전처리기 조건:

| 파일:줄 | 감싸는 조건 | 저장소 mode.h에서 컴파일되는가 |
|---------|------------|--------------------------------|
| [decoder.cpp:712](../../../../../0_LDPC_original/src/decoder.cpp#L712) | 없음 | 예 |
| [decoder.cpp:726](../../../../../0_LDPC_original/src/decoder.cpp#L726) | 없음 | 예 |
| [decoder.cpp:2314](../../../../../0_LDPC_original/src/decoder.cpp#L2314) | `#if defined (__RUN_PREPROCESSING__)` (2303행) | 아니오 |
| [decoder.cpp:2321](../../../../../0_LDPC_original/src/decoder.cpp#L2321) | 위의 `#else` | 예 |
| [decoder.cpp:2328](../../../../../0_LDPC_original/src/decoder.cpp#L2328) | 없음 | 예 |
| [decoder.cpp:3491](../../../../../0_LDPC_original/src/decoder.cpp#L3491) | `#if defined (__RUN_PREPROCESSING__)` (3480행) | 아니오 |
| [decoder.cpp:3498](../../../../../0_LDPC_original/src/decoder.cpp#L3498) | 위의 `#else` | 예 |
| [decoder.cpp:3504](../../../../../0_LDPC_original/src/decoder.cpp#L3504) | 없음 | 예 |

712와 726은 `Clear_Edge_Restart`
([decoder.cpp:709-739](../../../../../0_LDPC_original/src/decoder.cpp#L709-L739)) 안이고,
이 함수를 부르는 [decoder.cpp:1133](../../../../../0_LDPC_original/src/decoder.cpp#L1133)은
[decoder.cpp:1120](../../../../../0_LDPC_original/src/decoder.cpp#L1120)의
`for (mn = 0; mn < MN + 1; mn++)` 본문 첫머리이며 전처리기 조건이 없다.
곧 프레임마다, iteration마다 무조건 불린다.

`Is_Iter_Type_Init` 호출 전수는 열여섯 곳이며, 저장소 mode.h에서 모두 컴파일된다.
[2578](../../../../../0_LDPC_original/src/decoder.cpp#L2578),
[2602](../../../../../0_LDPC_original/src/decoder.cpp#L2602),
[2783](../../../../../0_LDPC_original/src/decoder.cpp#L2783),
[2993](../../../../../0_LDPC_original/src/decoder.cpp#L2993)는 조건이 없고,
[2863](../../../../../0_LDPC_original/src/decoder.cpp#L2863),
[2977](../../../../../0_LDPC_original/src/decoder.cpp#L2977)은
`#if defined (__ECC_TV__)`(2816행) 안인데 `__ECC_TV__`가
[mode.h:39](../../../../../0_LDPC_original/src/mode.h#L39)에서 켜져 있고,
[5700](../../../../../0_LDPC_original/src/decoder.cpp#L5700), 5708, 5716, 5740, 5748, 5756,
5824, 5903, 6058, 6139은 전처리기 조건이 없다.

### E1-6 8.1과 8.2의 수정 후 코드 — 확인됨 (8.2는 산문뿐)

- ㉮ 8.1 [code_diff.md:916](../code_diff.md)는 "`#if defined(__AUTO_LLR_OPT__)` 갈래만 남긴다"라고 적고,
  이어지는 수정 후 코드 블록(code_diff.md:918-948)에는 `#if`, `#else`, `#endif`가 하나도 없다.
  곧 [decoder.cpp:6566-6596](../../../../../0_LDPC_original/src/decoder.cpp#L6566-L6596)의
  `#else` 갈래가 통째로 사라진다
- ㉯ 8.2는 수정 후 코드 블록이 없다. code_diff.md:972의
  "같은 방식으로 `__AUTO_LLR_OPT__` 갈래만 남긴다. 조건은 그대로 둔다"라는 산문 한 줄이 전부다.
  적용 대상은 [decoder.cpp:6626-6674](../../../../../0_LDPC_original/src/decoder.cpp#L6626-L6674)의
  `#else` 갈래다
- ㉰ 남는 코드가 `m_param_LLR`을 역참조하는 줄

| 함수 | 남는 줄(현 소스 기준) | 내용 | 도달 조건 |
|------|----------------------|------|----------|
| `Is_Iter_Type_Edge_Clear` | [decoder.cpp:6549-6550](../../../../../0_LDPC_original/src/decoder.cpp#L6549-L6550) | `m_param_LLR->restart_num`, `m_param_LLR->restart_iter[i]` | HD 또는 1.5SD이고 `iter`가 0, 1, `ITER_MAX_HBF+1` 중 어느 것도 아닐 때 |
| `Is_Iter_Type_Edge_Clear` | [decoder.cpp:6560-6561](../../../../../0_LDPC_original/src/decoder.cpp#L6560-L6561) | 같음 | HD와 1.5SD가 아니고 `iter != 0`일 때 |
| `Is_Iter_Type_Init` | [decoder.cpp:6620-6621](../../../../../0_LDPC_original/src/decoder.cpp#L6620-L6621) | 같음 | HD와 1.5SD가 아니고 `iter != 0`일 때 |

여기서 R2-1의 문장을 한 가지 좁혀야 한다.
`Is_Iter_Type_Init`의 남는 갈래는 HD와 1.5SD에서는 `iter == 0`만 보고 끝나므로
`m_param_LLR`을 역참조하지 않는다 ([decoder.cpp:6610-6614](../../../../../0_LDPC_original/src/decoder.cpp#L6610-L6614)).
역참조는 2SD와 3SD에서만 일어난다.
반면 `Is_Iter_Type_Edge_Clear`는 HD와 1.5SD에서도 `iter`가 0, 1, 5가 아니면 곧바로 역참조한다.
곧 HD 실행에서는 `Is_Iter_Type_Edge_Clear` 한 함수만 매 iteration 역참조하고,
2SD와 3SD 실행에서는 두 함수가 모두 역참조한다.

### E1-7 저장소 mode.h 그대로면 `__AUTO_LLR_OPT__`가 정의되지 않는다 — 확인됨

[mode.h:8](../../../../../0_LDPC_original/src/mode.h#L8)은 `//#define __PROGRAM_MODE_REF_C__`로 주석이다.

- ㉮ Windows(`_WIN64` 또는 `_WIN32`): [mode.h:18-19](../../../../../0_LDPC_original/src/mode.h#L18-L19)의
  참 갈래가 잡혀 `__WIN_OS__`만 정의되고 20-26행 블록은 건너뛴다.
  `__AUTO_LLR_OPT__` 미정의
- ㉯ 비Windows: [mode.h:20-27](../../../../../0_LDPC_original/src/mode.h#L20-L27)의 `#else`로 들어가
  21행 `#ifdef __PROGRAM_MODE_REF_C__`를 만나는데 8행이 주석이라 거짓이다.
  22행 `#define __AUTO_LLR_OPT__`에 닿지 않는다. `__AUTO_LLR_OPT__` 미정의
- ㉰ 이어서 [mode.h:30](../../../../../0_LDPC_original/src/mode.h#L30)
  `#if defined(__PROGRAM_MODE_REF_C__)`가 거짓이므로 35-55행의 `#else`가 살아나
  [mode.h:38-40](../../../../../0_LDPC_original/src/mode.h#L38-L40)에서
  `__PROGRAM_MODE_TV_GEN__`, `__ECC_TV__`, `__ECC_TV_SYND_INTERNAL_DEBUG__`가 켜진다

곧 저장소 그대로는 Windows든 비Windows든 비AUTO TV Gen 빌드이며,
[main.cpp:77-81](../../../../../0_LDPC_original/src/main.cpp#L77-L81)에서 `Setup_TV_Gen`,
[main.cpp:89-90](../../../../../0_LDPC_original/src/main.cpp#L89-L90)에서 `Run_Simulation_TV_Gen`,
[main.cpp:127](../../../../../0_LDPC_original/src/main.cpp#L127)에서 4인자 `Init_ECC_Top`으로 이어진다.

덧붙여 세 번째 조합이 있다. Windows에서 사용자가 8행 주석을 풀면
`__WIN_OS__`가 켜지고 `__AUTO_LLR_OPT__`는 여전히 미정의이며,
30행이 참이 되어 `__PROGRAM_MODE_TV_GEN__`이 꺼진다.
그러면 [main.cpp:80](../../../../../0_LDPC_original/src/main.cpp#L80) `Setup_Ref_C`와
[main.cpp:95](../../../../../0_LDPC_original/src/main.cpp#L95) `Run_Simulation_Ref_C`를 거쳐
[main.cpp:105](../../../../../0_LDPC_original/src/main.cpp#L105)의 4인자 오버로드로 간다.
곧 비AUTO Ref-C 빌드도 같은 결함에 걸린다.

또한 [mode.h:63](../../../../../0_LDPC_original/src/mode.h#L63) `//#define __RUN_PREPROCESSING__`이
주석이므로 code_diff 8.3이 인용한
[decoder.cpp:1146-1156](../../../../../0_LDPC_original/src/decoder.cpp#L1146-L1156)의 Preprocessing 블록은
저장소 mode.h 그대로는 컴파일되지 않는다.
8.3은 "수정 전후 모두 그대로 둔다"이므로 R2-1의 결함과는 무관하지만,
8.3의 설명("`flag_BF_on`이 살아나면 조건이 저절로 맞는다")이 성립하려면
`__RUN_PREPROCESSING__`을 함께 켜야 한다는 전제가 문서에 없다.

### E1-8 restart 상수 8개와 AUTO 갈래의 대응 — 확인됨

- ㉮ 여덟 상수는 [common.h:679-686](../../../../../0_LDPC_original/src/common.h#L679-L686)에 있다.
  값은 `RSP1_2SD_PRIME_1` 241, `RSP1_2SD_PRIME_2` 581,
  `RSP1_3SD_PRIME_1` 171, `_2` 312, `_3` 653, `_4` 844, `_5` 1035, `_6` 1301
- ㉯ 이 블록은 [common.h:491](../../../../../0_LDPC_original/src/common.h#L491)에서 열린
  `#ifdef __4_BIT_LLR__`의 `#else` 안이고,
  [mode.h:12](../../../../../0_LDPC_original/src/mode.h#L12) `//#define __4_BIT_LLR__`이 주석이므로
  저장소 그대로 살아나는 갈래다
- ㉰ 비AUTO `Is_Iter_Type_Edge_Clear`가 쓰는 지점:
  2SD는 [decoder.cpp:6579-6580](../../../../../0_LDPC_original/src/decoder.cpp#L6579-L6580)의 2개,
  3SD는 [decoder.cpp:6586-6591](../../../../../0_LDPC_original/src/decoder.cpp#L6586-L6591)의 6개.
  비AUTO `Is_Iter_Type_Init`도 같은 값들을
  [decoder.cpp:6645-6646](../../../../../0_LDPC_original/src/decoder.cpp#L6645-L6646)과
  [decoder.cpp:6663-6668](../../../../../0_LDPC_original/src/decoder.cpp#L6663-L6668)에서 쓴다.
  합해 restart 지점 8개다
- ㉱ AUTO 갈래에는 이 상수들의 대응이 없다.
  AUTO 갈래는 `m_param_LLR->restart_iter[]`를 순회할 뿐이며
  ([decoder.cpp:6549-6552](../../../../../0_LDPC_original/src/decoder.cpp#L6549-L6552),
  [6560-6563](../../../../../0_LDPC_original/src/decoder.cpp#L6560-L6563),
  [6620-6623](../../../../../0_LDPC_original/src/decoder.cpp#L6620-L6623)),
  그 배열은 파일에서 읽는다
  ([local_opt.cpp:85-90](../../../../../0_LDPC_original/src/local_opt.cpp#L85-L90))

### E1-9 2SD와 3SD가 죽은 경로가 아니다 — 확인됨

모드 상수는 [common.h:75-78](../../../../../0_LDPC_original/src/common.h#L75-L78)에서
HD 1, 2SD 2, 3SD 3, 1.5SD 4다.

- ㉮ `Setup_Ref_C` [main.cpp:167-172](../../../../../0_LDPC_original/src/main.cpp#L167-L172):
  `(MODE_DEC_HD > init_n) || (MODE_DEC_1_5SD < init_n)`이면 오류이므로 허용 범위가 1에서 4다.
  2SD와 3SD가 들어온다
- ㉯ `Setup_TV_Gen` [main.cpp:518-528](../../../../../0_LDPC_original/src/main.cpp#L518-L528):
  `(MODE_DEC_HD <= init_n) && (MODE_DEC_1_5SD >= init_n)`이 통과 조건이므로 역시 1에서 4다.
  [main.cpp:521](../../../../../0_LDPC_original/src/main.cpp#L521)의 안내 문구도
  "1: HD, 2: 2SD, 3: 3SD, 4: 1.5SD(x)"로 2SD와 3SD를 명시한다

### E1-10 `matrix_sel` 가드 — 확인됨

- ㉮ 비AUTO 갈래는 `LAYOUT_PRIME_512B_TLC_VSS_OFF == m_ecc_info->matrix_sel` 조건으로 감싸여 있다.
  [decoder.cpp:6567](../../../../../0_LDPC_original/src/decoder.cpp#L6567)과
  [decoder.cpp:6627](../../../../../0_LDPC_original/src/decoder.cpp#L6627)
- ㉯ AUTO 갈래([decoder.cpp:6541-6565](../../../../../0_LDPC_original/src/decoder.cpp#L6541-L6565),
  [6609-6625](../../../../../0_LDPC_original/src/decoder.cpp#L6609-L6625))에는 이 조건이 없다
- ㉰ `LAYOUT_PRIME_512B_TLC_VSS_OFF`의 값은 1이고
  ([common.h:193](../../../../../0_LDPC_original/src/common.h#L193)),
  다른 LAYOUT 상수 다섯 개는 모두 주석 처리되어 있다
  ([common.h:194-198](../../../../../0_LDPC_original/src/common.h#L194-L198))
- ㉱ `Setup_TV_Gen`은 `matrix_sel`을 넓게 받는다.
  [main.cpp:499-508](../../../../../0_LDPC_original/src/main.cpp#L499-L508)의 조건은
  `LAYOUT_PRIME_512B_TLC_VSS_OFF <= g_ecc_info.matrix_sel`, 곧 1 이상이면 무엇이든 통과한다.
  2, 3, 11 같은 값이 그대로 들어온다
- ㉲ 비AUTO `Setup_Ref_C`는 좁다.
  [main.cpp:154-163](../../../../../0_LDPC_original/src/main.cpp#L154-L163)의 `#else` 갈래는
  `matrix_sel`이 1이 아니면 오류로 되돌린다

따라서 가드 소실의 영향은 빌드마다 다르다.
비AUTO Ref-C 빌드에서는 `matrix_sel`이 언제나 1이라 가드가 늘 참이므로 가드 소실 자체는 무해하다.
비AUTO TV Gen 빌드에서 `matrix_sel`이 1이 아니면 지금은 edge clear와 init이 한 번도 일어나지 않는데,
갈래를 합치면 iteration 0, 1, 5에서 edge clear가, iteration 0에서 init이 새로 생긴다.
R2-1의 딸린 가설 ㉯가 말한 그대로다.

한편 AUTO 빌드에서도 `matrix_sel`은 1로 고정되지 않는다.
[main.cpp:140-143](../../../../../0_LDPC_original/src/main.cpp#L140-L143)의 `#ifdef __AUTO_LLR_OPT__`
갈래는 `argc > 19`이면 `argv[19]`의 H-matrix 파일 이름을 그대로 받고
`matrix_sel` 값은 검사하지 않는다.
이 사실은 처방 판정(E1-11)에서 중요하다.

### E1-11 처방 Q1이 계획의 목적을 해치지 않는다 — 확인됨

code_diff 8.1의 수정 후 코드 블록(code_diff.md:918-948)의 본문을
현 AUTO 갈래 [decoder.cpp:6542-6565](../../../../../0_LDPC_original/src/decoder.cpp#L6542-L6565)와
한 줄씩 대조하면 조건, 순서, 값이 모두 같다.
8.2도 "조건은 그대로 둔다"라고 스스로 적었다.
곧 8.1과 8.2가 AUTO 빌드에 주는 변화는 0이다.
AUTO 빌드에서 이 두 함수의 동작이 달라지는 것은
`ITER_MAX_HBF`가 0에서 4로 바뀌는 것 때문이고
([common.h:403-407](../../../../../0_LDPC_original/src/common.h#L403-L407), code_diff 1.2장),
그 변화는 갈래를 합치지 않아도 그대로 일어난다.

상위 문서도 갈래 통일을 요구하지 않는다.
5.6절 표(상위 문서 281-285행)와 6.1절 표(상위 문서 302-303행)가 가리키는 줄 번호는
`6541-6565`와 `6609-6626`, 곧 AUTO 갈래의 범위다.
7장 미결정 ㉱(상위 문서 360-361행)가 다루는 비AUTO 하드코딩은
`Get_Cur_LLR_Idx_FILE`의 `decoder.cpp:7001-7020`이지 이 두 함수가 아니다.
비AUTO 갈래를 반드시 바꿔야 한다는 근거는 code_diff에도 상위 문서에도 없다.

다만 처방 Q1의 뒷부분("합친 갈래에 `matrix_sel` 조건을 유지한다")은 그대로 받으면 안 된다.
E1-10 ㉲에서 본 대로 AUTO 빌드도 `argc > 19`이면 `matrix_sel`이 1이 아닐 수 있고,
합친 갈래에 `matrix_sel == 1` 조건을 두면 그 실행에서 AUTO 빌드가
edge clear와 init을 통째로 잃는다. 지금은 없는 결함이 새로 생긴다.
따라서 Q1의 두 조각 중 앞의 것(`#if` 갈래를 유지한다)만 받아야 하고,
뒤의 것(합치되 `matrix_sel` 조건을 유지한다)은 받으면 안 된다.

### E1-12 대안 Q1c의 성립 조건 — 확인됨 (현재 성립하지 않는다)

- ㉮ `PARAM_LLR` 정의는 [ecc_data.h:179-198](../../../../../0_LDPC_original/src/ecc_data.h#L179-L198)이다
- ㉯ 실체 객체는 [local_opt.h:30](../../../../../0_LDPC_original/src/local_opt.h#L30)의
  `PARAM_LLR m_param_LLR;` 값 멤버 하나뿐이다.
  `ECC_Top`과 `Decoder`가 가진 것은 포인터다
  ([ecc_top.h:94](../../../../../0_LDPC_original/src/ecc_top.h#L94),
  [decoder.h:210](../../../../../0_LDPC_original/src/decoder.h#L210))
- ㉰ 그 객체를 채우는 곳은 `LOCAL_OPT::Read_LLR_info_Auto`
  ([local_opt.cpp:52-184](../../../../../0_LDPC_original/src/local_opt.cpp#L52-L184))이고,
  부르는 곳은 [local_opt.cpp:34](../../../../../0_LDPC_original/src/local_opt.cpp#L34) 하나다
- ㉱ `LOCAL_OPT` 객체를 만드는 곳은 [main.cpp:117](../../../../../0_LDPC_original/src/main.cpp#L117)
  하나뿐이고 `#if defined(__AUTO_LLR_OPT__)` 안이다.
  곧 비AUTO 빌드에서는 `PARAM_LLR` 객체가 하나도 만들어지지 않는다
- ㉲ `local_opt.cpp` 자체에는 AUTO 가드가 없어
  [build.bat](../../../../../0_LDPC_original/src/build.bat)의 컴파일 목록에 늘 들어가지만,
  컴파일만 되고 실행되지 않는다

따라서 Q1c를 하려면 비AUTO에 새 코드를 들여야 한다.
㉠ `ECC_Top` 또는 `Decoder`에 `PARAM_LLR` 값 멤버를 새로 두고,
㉡ 4인자 `Init_ECC_Top`([ecc_top.cpp:197-210](../../../../../0_LDPC_original/src/ecc_top.cpp#L197-L210))에서
그 주소를 `m_param_LLR`에 넣고,
㉢ `init_n`에 따라 `restart_num`과 `restart_iter[]`를 `new`로 잡아 채우고,
㉣ 소멸 시점에 해제해야 한다.
지금 코드에는 ㉠부터 ㉣까지 어느 것도 없다.

의미 대조는 채우기만 하면 정확히 맞는다.

| 함수와 모드 | 비AUTO 원본 조건 | 합친 갈래가 같아지려면 |
|-------------|-----------------|----------------------|
| Edge_Clear, HD와 1.5SD | `iter == 0 \|\| 1 \|\| ITER_MAX_HBF+1` ([6569-6573](../../../../../0_LDPC_original/src/decoder.cpp#L6569-L6573)) | `restart_num = 0` (AUTO 갈래가 같은 세 조건을 먼저 보고, 남는 `else`의 순회가 비면 된다) |
| Edge_Clear, 2SD | `iter == 0 \|\| 241 \|\| 581` ([6578-6580](../../../../../0_LDPC_original/src/decoder.cpp#L6578-L6580)) | `restart_num = 2`, `restart_iter = {241, 581}` |
| Edge_Clear, 3SD | `iter == 0 \|\| 171 \|\| 312 \|\| 653 \|\| 844 \|\| 1035 \|\| 1301` ([6585-6591](../../../../../0_LDPC_original/src/decoder.cpp#L6585-L6591)) | `restart_num = 6`, `restart_iter = {171, 312, 653, 844, 1035, 1301}` |
| Init, HD와 1.5SD | `iter == 0` ([6629-6631](../../../../../0_LDPC_original/src/decoder.cpp#L6629-L6631)) | AUTO 갈래가 이미 `iter == 0`만 본다. 그대로 같다 |
| Init, 2SD | `iter == 0 \|\| 241 \|\| 581` ([6634, 6645-6646](../../../../../0_LDPC_original/src/decoder.cpp#L6645-L6646)) | Edge_Clear 2SD와 같은 배열 |
| Init, 3SD | `iter == 0 \|\| 171 \|\| 312 \|\| 653 \|\| 844 \|\| 1035 \|\| 1301` ([6652, 6663-6668](../../../../../0_LDPC_original/src/decoder.cpp#L6663-L6668)) | Edge_Clear 3SD와 같은 배열 |

개수와 값은 2SD 2개, 3SD 6개로 정확히 대응한다.
다만 `restart_iter[]`가 모드마다 달라야 한다는 점이 걸림돌이다.
`restart_num`은 `PARAM_LLR` 하나에 담긴 값이라
HD 실행에서 2SD의 241과 581을 그대로 남겨 두면
HD 갈래의 `else` 순회가 iteration 241과 581에서 없던 edge clear를 일으킨다.
곧 Q1c는 `init_n`을 보고 배열을 다르게 채워야 하며, 그만큼 새 코드가 늘어난다.
또한 Q1c는 `matrix_sel` 가드 소실(E1-10)을 전혀 다루지 않는다.

### E1-13 대안 Q1b(NULL 초기화와 널 검사)의 결과 — 확인됨 (원본과 다르다)

포인터를 NULL로 두고 restart 순회 앞에 널 검사를 넣으면
비AUTO에서 두 함수의 반환값은 아래와 같다.

| 함수와 모드 | Q1b 적용 후 | 비AUTO 원본(`matrix_sel == 1`) | 같은가 |
|-------------|------------|-------------------------------|--------|
| Edge_Clear, HD와 1.5SD | `iter == 0, 1, 5`에서 TRUE | `iter == 0, 1, 5`에서 TRUE | 같다 |
| Edge_Clear, 2SD | `iter == 0`에서만 TRUE | `iter == 0, 241, 581`에서 TRUE | 다르다 (2개 소실) |
| Edge_Clear, 3SD | `iter == 0`에서만 TRUE | `iter == 0, 171, 312, 653, 844, 1035, 1301`에서 TRUE | 다르다 (6개 소실) |
| Init, HD와 1.5SD | `iter == 0`에서 TRUE | `iter == 0`에서 TRUE | 같다 |
| Init, 2SD | `iter == 0`에서만 TRUE | `iter == 0, 241, 581`에서 TRUE | 다르다 (2개 소실) |
| Init, 3SD | `iter == 0`에서만 TRUE | `iter == 0` 더하기 6개 | 다르다 (6개 소실) |

곧 널 검사는 정의되지 않은 동작만 막고, restart 지점 8개는 그대로 사라진다.
`matrix_sel != 1`인 TV Gen 실행에서 없던 edge clear와 init이 생기는 문제도 남는다.
Q1b는 R2-1이 든 세 갈래 피해 중 첫째만 막는다.

---

## 2. R2-12 증거 판정

### E1-14 `Get_Cur_LLR_Idx_FILE` 전수 — 확인됨

| 파일:줄 | 종류 |
|---------|------|
| [decoder.h:125](../../../../../0_LDPC_original/src/decoder.h#L125) | 선언 |
| [decoder.cpp:6973](../../../../../0_LDPC_original/src/decoder.cpp#L6973) | 정의 |
| [decoder.cpp:1138](../../../../../0_LDPC_original/src/decoder.cpp#L1138) | 호출 |

호출은 1138 하나뿐이다.

### E1-15 decoder.cpp:1136-1145 — 확인됨

```cpp
1136        if (mn > 0) {
1137    #if defined(__AUTO_LLR_OPT__)
1138            cur_set_idx = Get_Cur_LLR_Idx_FILE(mn);
1139    #else
1140            cur_set_idx = Get_VNU_Table_Idx(mn);
1141    #endif
1142        }
1143        else {
1144            cur_set_idx = 0;
1145        }
```

1137행은 `#if defined(__AUTO_LLR_OPT__)`이고 `#else` 갈래(1140행)는
`Get_VNU_Table_Idx(mn)`을 부른다.

### E1-16 `Get_VNU_Table_Idx`가 무조건 0을 돌려준다 — 확인됨

[decoder.cpp:7207-7210](../../../../../0_LDPC_original/src/decoder.cpp#L7207-L7210)의 전체 몸체다.

```cpp
int Decoder::Get_VNU_Table_Idx(int iter)
{
    return 0;
}
```

인자 `iter`를 읽지 않고 조건도 없다. 이 함수를 감싸는 전처리기 조건도 없다.

### E1-17 `Get_Cur_LLR_Idx_FILE` 정의는 `#if`로 감싸여 있지 않다 — 확인됨

주석을 걷어낸 뒤 중첩 깊이를 세면
[decoder.cpp:6973](../../../../../0_LDPC_original/src/decoder.cpp#L6973)의 깊이는 0이다.
선언 [decoder.h:125](../../../../../0_LDPC_original/src/decoder.h#L125)에도 조건이 없다.
함수 안쪽에만 [decoder.cpp:6984](../../../../../0_LDPC_original/src/decoder.cpp#L6984)의
`#if defined (__AUTO_LLR_OPT__)`가 있고,
비AUTO 갈래 [decoder.cpp:7001-7047](../../../../../0_LDPC_original/src/decoder.cpp#L7001-L7047)은
그 `#else`다.
곧 비AUTO 빌드에서도 이 함수는 컴파일되며, 불리지 않을 뿐이다.
R2-12의 "컴파일만 되고 실행되지 않는 코드"라는 표현이 정확하다.

### E1-18 비AUTO 갈래 안의 `flag_HD_*` 읽기와 code_diff 2.2의 맞물림 — 확인됨

두 멤버의 전수 히트는 아래와 같다.

| 파일:줄 | 내용 | 종류 |
|---------|------|------|
| [decoder.cpp:612](../../../../../0_LDPC_original/src/decoder.cpp#L612) | `flag_HD_1_4_Set = FLAG_LOW;` (`Clear_Flag`) | 쓰기 |
| [decoder.cpp:613](../../../../../0_LDPC_original/src/decoder.cpp#L613) | `flag_HD_5_8_Set = FLAG_LOW;` (`Clear_Flag`) | 쓰기 |
| [decoder.cpp:2090](../../../../../0_LDPC_original/src/decoder.cpp#L2090) | `Select_BF` 비AUTO 갈래 | 쓰기 |
| [decoder.cpp:2091](../../../../../0_LDPC_original/src/decoder.cpp#L2091), [2100](../../../../../0_LDPC_original/src/decoder.cpp#L2100), [2106](../../../../../0_LDPC_original/src/decoder.cpp#L2106), [2117](../../../../../0_LDPC_original/src/decoder.cpp#L2117), [2123](../../../../../0_LDPC_original/src/decoder.cpp#L2123) | `Select_BF` 비AUTO 갈래 | 쓰기 |
| [decoder.cpp:7002](../../../../../0_LDPC_original/src/decoder.cpp#L7002), [7006](../../../../../0_LDPC_original/src/decoder.cpp#L7006) | `Get_Cur_LLR_Idx_FILE` 비AUTO 갈래 | 읽기 |
| [decoder.cpp:7010](../../../../../0_LDPC_original/src/decoder.cpp#L7010), [7016](../../../../../0_LDPC_original/src/decoder.cpp#L7016) | 같음 | 읽기 |
| [decoder.h:297-298](../../../../../0_LDPC_original/src/decoder.h#L297-L298) | 선언 | 선언 |

7002, 7006, 7010, 7016은 R2-2의 컴파일 실패 목록에 넣지 않아야 한다.
code_diff 6.1의 수정 전 인용 블록이 `#endif // __AUTO_LLR_OPT__`까지 담고 있고
수정 후 블록에 그 `#else`가 없으므로, 6장이 이 네 줄을 함께 지우기 때문이다.
다만 6.1의 제목은 "6973-6999행"이라 실제 교체 범위(6973-7047)를 덜 적었다.
제목의 줄 범위를 실제 범위로 고치는 편이 R2-2의 목록을 세는 데 도움이 된다.
남는 곳은 612와 613뿐이며, 그것이 R2-2가 든 그대로다.

### E1-19 1137-1141을 그대로 두었을 때 비AUTO가 부르는 함수 — 확인됨

1137-1141이 그대로면 비AUTO 빌드는 여전히 1140행의 `Get_VNU_Table_Idx(mn)`을 부르고,
그 함수는 무조건 0을 돌려준다(E1-16).
`cur_set_idx`는 `mn == 0`일 때의 1144행 값과 같은 0이 되어 매 iteration 0이다.
이는 비AUTO 원본과 완전히 같다.

6장이 `Get_Cur_LLR_Idx_FILE`을 한 갈래로 합쳐도, 그 함수는 비AUTO에서 불리지 않으므로
합친 몸체가 `m_param_LLR`과 `cur_sw_branch_idx[]`를 역참조해도 실행되지 않는다.
컴파일은 성립한다. 합친 몸체가 쓰는 이름
(`sw_branch_idx_each_group`, `sw_span_idx_each_group`, `cur_sw_branch_idx`, `SW_BRANCH_NONE`)은
code_diff 1.1, 2.1, 2.2가 양쪽 빌드 모두에 넣는 것이라
`#if` 없이도 선언이 존재한다.

### E1-20 두 처방을 함께 적용했을 때 비AUTO의 최종 동작 — 확인됨 (일관된다)

Q1(8.1과 8.2의 `#if` 유지)과 Q2(1137-1141 유지)는 서로 다른 함수를 건드리므로 충돌하지 않는다.
둘 다 "비AUTO의 기존 경로를 그대로 둔다"라는 같은 방향이다.
두 처방을 함께 적용한 뒤 비AUTO 빌드의 항목별 동작은 아래와 같다.

| 항목 | 원본과 같은가 | 근거 |
|------|--------------|------|
| ㉮ `Is_Iter_Type_Edge_Clear` | 같다 | `#else` 갈래가 그대로 남고, `ITER_MAX_HBF`는 비AUTO에서 이미 4라 code_diff 1.2의 무조건 4와 값이 같다 |
| ㉯ `Is_Iter_Type_Init` | 같다 | 같은 이유 |
| ㉰ `cur_set_idx` | 같다 | `Get_VNU_Table_Idx`가 여전히 0을 돌려준다 (E1-19) |
| ㉱ 1bit precision 조건 네 곳 (code_diff 7장) | 같다 | 비AUTO 갈래가 이미 `iter <= ITER_MAX_HBF`였고 값도 4로 그대로다 ([2373-2379](../../../../../0_LDPC_original/src/decoder.cpp#L2373-L2379) 등) |
| ㉲ `Select_BF` (code_diff 5.1) | 관찰 가능한 동작은 같다 | 갈래를 합치지만 `flag_BF_on`, `mn`, `MN`의 결과가 원본과 같다. 새 `cur_sw_branch_idx[]`는 비AUTO에서 읽히지 않는다 (읽는 곳이 `Get_Cur_LLR_Idx_FILE`뿐이고 비AUTO에서 불리지 않는다). `__CORNER_CHECKER__`는 [mode.h:75](../../../../../0_LDPC_original/src/mode.h#L75)에서 꺼져 있다 |
| ㉳ `Init_Dec_Option` 문턱 (code_diff 4.1) | `matrix_sel == 1`이면 같고, 아니면 다르다 | 원본의 `default`는 `syn_th_BF`(읽는 곳 없음)에 넣고 `syn_th_BF0`를 세우지 않은 채 [2088행](../../../../../0_LDPC_original/src/decoder.cpp#L2088)에서 읽는다. 수정 후에는 `syn_th_BF0 = SW_TH_BF_DEFAULT`가 되어 값이 정해진다. 기존 결함을 고치는 쪽이지만 TV Gen에서 동작이 달라진다 |
| ㉴ `Clear_Flag` 612-613 | 아니다 | code_diff 어디에도 대체 코드가 없어 양쪽 빌드가 컴파일되지 않는다 (R2-2) |

㉳과 ㉴는 R2-1과 R2-12의 처방으로는 덮이지 않는 별개 항목이다.
㉳은 이번 검증에서 새로 확인한 것이라 아래 부가 관찰에 다시 적는다.

---

## 3. 판정

### R2-1 (CRITICAL)

- ㉮ 사실 가설 판정: **확인됨** (한 군데 좁힘)
  - ㉠ 저장소 mode.h 그대로는 비AUTO 빌드다 (E1-7)
  - ㉡ 그 빌드에서 `ECC_Top::m_param_LLR`은 생성자에서도 4인자 `Init_ECC_Top`에서도 세워지지 않고
    (E1-1, E1-2), 대입하는 유일한 곳은 AUTO에서만 도달하는 5인자 오버로드다 (E1-3, E1-4)
  - ㉢ `Is_Iter_Type_Edge_Clear`는 `Clear_Edge_Restart`를 거쳐 메인 루프에서 매 iteration
    조건 없이 불린다 (E1-5)
  - ㉣ 8.1이 `#else` 갈래를 지우면 남는 코드가 `m_param_LLR->restart_num`과
    `m_param_LLR->restart_iter[i]`를 역참조한다 (E1-6). 정의되지 않은 동작이 맞다
  - ㉤ 좁힐 점: `Is_Iter_Type_Init`의 남는 갈래는 HD와 1.5SD에서 `iter == 0`만 보므로
    역참조하지 않는다. 역참조는 2SD와 3SD에서만이다.
    "두 함수가 매 iteration 역참조한다"는 2SD와 3SD에서만 참이고,
    HD 실행에서는 `Is_Iter_Type_Edge_Clear` 한 함수가 그렇다.
    결론(정의되지 않은 동작)은 어느 모드에서도 뒤집히지 않는다
  - ㉥ 딸린 가설 ㉮(restart 지점 8개 소실) 확인됨 (E1-8, E1-13)
  - ㉦ 딸린 가설 ㉯(TV Gen에서 `matrix_sel` 가드 소실) 확인됨 (E1-10)

- ㉯ 처방 판정: **처방 수정 필요**
  - ㉠ Q1의 앞부분("두 함수의 `#if defined(__AUTO_LLR_OPT__)` 갈래를 유지한다")은 **처방 유효**다.
    8.1과 8.2가 AUTO 빌드에 주는 변화가 0이므로(E1-11) 계획의 목적을 조금도 해치지 않고,
    비AUTO의 세 가지 피해를 모두 막는다.
    상위 문서와 code_diff 어디에도 비AUTO 갈래를 바꿔야 할 근거가 없다
  - ㉡ Q1의 뒷부분("합친 갈래에 `matrix_sel` 조건을 유지한다")은 **처방 반대**다.
    AUTO 빌드도 `argc > 19`이면 `matrix_sel`이 1이 아닐 수 있으므로
    ([main.cpp:140-143](../../../../../0_LDPC_original/src/main.cpp#L140-L143)),
    합친 갈래에 이 조건을 두면 그 실행에서 AUTO가 edge clear와 init을 통째로 잃는다.
    지금 없는 결함을 새로 만든다
  - ㉢ Q1b(NULL 초기화와 널 검사)는 **처방 반대**다. 정의되지 않은 동작만 막고
    restart 지점 8개 소실과 `matrix_sel` 가드 소실은 그대로 남는다 (E1-13)
  - ㉣ Q1c(비AUTO에서 `restart_iter[]`를 하드코딩 상수로 채운다)는 **지금은 성립하지 않는다**.
    비AUTO에 `PARAM_LLR` 객체 자체가 없어 새 멤버, 새 할당, 새 해제, `init_n`별 분기 채우기를
    모두 들여야 하고(E1-12), 그러고도 `matrix_sel` 가드 문제는 남는다.
    의미 대조는 정확히 맞으므로 나중 정리 과제로는 성립하지만, 지금 수정에 넣을 처방은 아니다
  - ㉤ 권고: code_diff 8.1의 수정 후 코드에서 `#if defined(__AUTO_LLR_OPT__)`, `#else`, `#endif`를
    되살리고 비AUTO 갈래를 그대로 두며, 8.2는 "갈래를 그대로 두고 AUTO 갈래도 손대지 않는다"로
    다시 쓴다. 비AUTO 갈래 통일은 7장 미결정에 ㉲로 새로 세워 별도 결정으로 미룬다

- ㉰ 심각도 재판정: **CRITICAL 유지**
  저장소 기본 빌드에서 세운 적 없는 포인터를 매 iteration 역참조하는 코드를 문서가 지시하고 있고,
  실행하면 결과를 신뢰할 수 없다. 처방을 반영하기 전에는 8장을 적용하지 말아야 한다.

### R2-12 (MEDIUM)

- ㉮ 사실 가설 판정: **확인됨**
  - ㉠ `Get_Cur_LLR_Idx_FILE` 호출은 [decoder.cpp:1138](../../../../../0_LDPC_original/src/decoder.cpp#L1138)
    하나뿐이고 `#if defined(__AUTO_LLR_OPT__)` 안이다 (E1-14, E1-15)
  - ㉡ 함수 정의 자체에는 전처리기 조건이 없어 비AUTO에서도 컴파일된다 (E1-17).
    곧 [decoder.cpp:7001-7047](../../../../../0_LDPC_original/src/decoder.cpp#L7001-L7047)은
    컴파일만 되고 실행되지 않는 코드다
  - ㉢ 따라서 상위 문서 5.3-4의 "`1_4_Set`이 `TYPE_1`이면 `selected_group`이 -1로 남는다"는
    어떤 빌드에서도 실행되지 않는다.
    보태어, 그 상황이 실행된다 해도 `flag_HD_1_4_Set`에 `FLAG_HD_1_4_SET_TYPE_1`을 넣는 곳이
    소스 어디에도 없다 (E1-18의 쓰기 목록에 2090의 `TYPE_0` 하나뿐이다).
    두 겹으로 실체가 없다
  - ㉣ 7장 ㉱ 미결정은 "실행되지 않는 코드를 지울지"라는 정리 문제이지
    동작 선택 문제가 아니다. 실체를 잃는다는 표현이 정확하다

- ㉯ 처방 판정: **처방 유효** (한 줄 보탤 것)
  - ㉠ Q2("5.3-4와 7장 ㉱에 실행되지 않는 코드임을 적고, 1137-1141은 7장 ㉱ 결정에 따라
    삭제 여부를 정한다")를 적용하면 문제가 해결되고 새 문제가 생기지 않는다
  - ㉡ R2-1 처방(비AUTO 갈래 유지)과 모순되지 않는다.
    두 처방 모두 비AUTO의 기존 경로를 그대로 두는 방향이고 건드리는 함수가 다르다 (E1-20)
  - ㉢ 1137-1141을 그대로 두면 비AUTO는 `Get_VNU_Table_Idx`를 계속 불러 0을 받고,
    이는 원본과 같다 (E1-19)
  - ㉣ 보탤 것: 6.1의 제목 "6973-6999행"을 실제 교체 범위인 6973-7047행으로 고쳐야 한다 (E1-18).
    그래야 `flag_HD_1_4_Set`과 `flag_HD_5_8_Set`의 읽기 네 줄(7002, 7006, 7010, 7016)이
    6장에서 함께 지워진다는 것이 문서에서 읽히고, R2-2의 컴파일 실패 목록도 612와 613로 정확해진다

- ㉰ 심각도 재판정: **MEDIUM 유지 (LOW 쪽 경계)**
  코드 동작에 미치는 영향은 없고 문서의 사실 오류와 미결정 항목의 실체 유무 문제다.
  다만 7장 ㉱를 사용자 결정 항목으로 남겨 두면 결정할 것이 없는 질문에 시간을 쓰게 되고,
  6.1의 줄 범위 오기가 R2-2의 목록 세기와 얽히므로 MEDIUM이 지나치지 않다.

---

## 4. 부가 관찰 (검증 과정에서 새로 확인, R2-1과 R2-12 밖)

- ㉮ [mode.h:63](../../../../../0_LDPC_original/src/mode.h#L63) `__RUN_PREPROCESSING__`이 주석이라
  code_diff 8.3이 인용한 [decoder.cpp:1146-1156](../../../../../0_LDPC_original/src/decoder.cpp#L1146-L1156)
  Preprocessing 블록은 저장소 mode.h 그대로는 컴파일되지 않는다.
  8.3의 "`flag_BF_on`이 살아나면 조건이 저절로 맞는다"가 성립하려면
  이 스위치가 켜진 빌드라는 전제가 필요한데 문서에 없다
- ㉯ [decoder.cpp:472](../../../../../0_LDPC_original/src/decoder.cpp#L472)의 `default` 갈래는
  `syn_th_BF`(읽는 곳 없음)에만 값을 넣고 `syn_th_BF0`를 세우지 않는다.
  그런데 [decoder.cpp:2088](../../../../../0_LDPC_original/src/decoder.cpp#L2088)의 비AUTO `Select_BF`가
  `syn_th_BF0`를 읽는다. `matrix_sel != 1`인 TV Gen 실행에서 세운 적 없는 값으로 BF 진입을 정하는
  기존 결함이다. code_diff 4.1의 수정 후는 `default`에서 `syn_th_BF0 = SW_TH_BF_DEFAULT`로 채워
  이 결함을 없애지만, 그 결과 TV Gen의 동작이 달라진다는 설명이 code_diff에 없다
- ㉰ [main.cpp:140-143](../../../../../0_LDPC_original/src/main.cpp#L140-L143)의 AUTO 갈래는
  `argc > 19`일 때 `matrix_sel` 값을 검사하지 않는다.
  상위 문서 6.3 표(347행)가 `main.cpp`의 이 부분을 "손대지 않아도 되는 곳"으로 분류했는데,
  `matrix_sel` 가드를 다루는 어떤 처방이든 이 사실을 전제로 삼아야 한다
