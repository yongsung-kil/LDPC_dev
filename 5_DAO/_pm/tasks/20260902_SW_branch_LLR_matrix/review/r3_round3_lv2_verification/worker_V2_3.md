# Round 3 검증: 팀 V2 워커 3 (R2-7, R2-16)

작성: 2026-09-03 01:38:06

검증 대상은 코드 수정 계획 문서다. C++ 소스는 수정되지 않았고 이 저장소에서 빌드하지 않는다.
아래 판정은 모두 소스 원문 읽기와 전수 Grep, 손 실행으로 얻었다.

---

## ㉮ 가설별 판정 요약

| 가설 | 판정 | 한 줄 근거 |
|------|------|-----------|
| E (R2-7 사실) | 부분 확인 | 전제 ㉡㉢㉣와 "미결정 목록에 없음"은 확인됨. 전제 ㉠("메모가 1~4를 분기 없음으로 적는다")은 조건부 확인이고, 결론 "코드에도 메모에도 근거가 없는 새 동작"은 반박됨 |
| E 처방 (7장에 Decision 추가) | 처방 유효, 보강 필요 | Decision으로 올리는 것은 맞다. 다만 "근거 없음"이 아니라 "코드가 자리만 만들어 두고 한 번도 실행한 적 없는 동작"으로 다시 써야 하고, 선택지별 코드 근거를 함께 실어야 한다 |
| F (R2-16 사실) | 확인됨, 심각도 상향 근거 있음 | mn 수열 건너뛰기와 `Is_Iter_Type_Edge_Clear(mn)` 비교는 코드에서 확인됨. "현 파일은 `restart_num`이 0이라 잠재 결함"이라는 단서는 불완전하다. 구 파일이 `restart_iter = 2`를 실제로 담고 있다 |
| F 처방 (`restart_iter[i] <= ITER_MAX_HBF`를 오류로) | 처방 수정 필요 | 그 규칙은 실재하는 구 파일을 거부하고, BF 진입 프레임에는 뜻이 있는 정상 사용까지 막는다. 게다가 파서의 오류 표시는 실행을 멈추지 못한다 (R2-8) |

심각도 재판정 의견:

- ㉠ R2-7: HIGH → MEDIUM. 계획이 고른 동작(1~4에 분기 둘, 경계 130)은 코드의 준비 흔적과 파일 양쪽이 지지한다. 남는 위험은 "130이 한 번도 실행된 적 없는 값"이라는 점 하나이며, 이는 결정 사항이지 오류가 아니다
- ㉡ R2-16: MEDIUM 유지. 다만 "잠재 결함"이 아니라 "실재하는 구 파일의 동작이 조용히 바뀌는 변경"으로 성격을 고쳐야 한다

---

## ㉯ Grep 히트 목록과 손 실행 표

### 확인 1: SW 문턱 멤버 전수 Grep

Grep 범위는 [0_LDPC_original/src/](../../../../../../0_LDPC_original/src/) 전체다.

`syn_th_BF1` 전체 히트 (2건):

| 파일:줄 | 줄 내용 | 분류 |
|---------|---------|------|
| [decoder.h:303](../../../../../../0_LDPC_original/src/decoder.h#L303) | `int         syn_th_BF1;   // S-4 Set` | 선언 |
| [decoder.cpp:468](../../../../../../0_LDPC_original/src/decoder.cpp#L468) | `syn_th_BF1 = SW_TH_BF1_512B_TLC_OFF;` | 대입 |

읽는 곳은 없다. 가설 E의 전제 ㉣ 확인됨.

다섯 멤버 전체 대조표 (주석 처리된 줄은 개수에서 제외하고 비고에 적는다):

| 멤버 | 선언 | 대입 | 읽기 | 비고 |
|------|------|------|------|------|
| `syn_th_BF` | 1 (decoder.h:301) | 1 (decoder.cpp:472, `default:` 갈래만) | 0 | decoder.cpp:460-465에 주석 처리된 대입 6줄 |
| `syn_th_BF0` | 1 (decoder.h:302) | 1 (decoder.cpp:467, `LAYOUT_PRIME_512B_TLC_VSS_OFF` 갈래만) | 1 (decoder.cpp:2088) | `default:` 갈래에서는 대입되지 않는다 (아래 ㉲ 새 사실 ㉱ 참조) |
| `syn_th_BF1` | 1 (decoder.h:303) | 1 (decoder.cpp:468) | 0 | decoder.cpp:469에 `syn_th_BF2` 주석 |
| `syn_th_5_8_Set_0` | 1 (decoder.h:305) | 2 (decoder.cpp:480, 483) | 2 (decoder.cpp:2099, 2116) | decoder.cpp:477-479, 481-482에 주석 처리된 대입 |
| `syn_th_5_8_Set_1` | 1 (decoder.h:306) | 2 (decoder.cpp:489, 492) | 0 | decoder.cpp:583의 주석 처리된 `printf`가 유일한 등장. 읽는 곳 없음 |

판정: `syn_th_BF1`뿐 아니라 `syn_th_BF`, `syn_th_5_8_Set_1`도 대입만 되고 읽히지 않는다.
읽히는 문턱은 `syn_th_BF0`(BF 진입 판정)과 `syn_th_5_8_Set_0`(5~8 분기 판정) 둘뿐이다.
즉 지금 코드가 실제로 쓰는 분기는 "BF 진입 여부" 하나와 "5~8 구간의 두 갈래" 하나가 전부다.

### 확인 2: 분기 flag enum 전수 Grep

`FLAG_HD_1_4_SET_TYPE_0` (4건):

| 파일:줄 | 분류 |
|---------|------|
| [common.h:718](../../../../../../0_LDPC_original/src/common.h#L718) | enum 정의 (`= 0`) |
| [decoder.cpp:2090](../../../../../../0_LDPC_original/src/decoder.cpp#L2090) | 대입 (`flag_HD_1_4_Set = FLAG_HD_1_4_SET_TYPE_0;`) |
| [decoder.cpp:7002](../../../../../../0_LDPC_original/src/decoder.cpp#L7002) | 비교 (`iter == 1` 갈래) |
| [decoder.cpp:7006](../../../../../../0_LDPC_original/src/decoder.cpp#L7006) | 비교 (`iter >= 2 && iter <= 4` 갈래) |

`FLAG_HD_1_4_SET_TYPE_1` (1건):

| 파일:줄 | 분류 |
|---------|------|
| [common.h:719](../../../../../../0_LDPC_original/src/common.h#L719) | enum 정의 (`= 1`) |

**대입도 비교도 없다.** 저장소 전체에서 이 값을 쓰는 코드는 존재하지 않는다. 가설 E의 전제 ㉢ 확인됨.

`FLAG_HD_5_8_SET_TYPE_0` (7건): common.h:723 정의, decoder.cpp:2091, 2100, 2117 대입, decoder.cpp:7010, 7016 비교, decoder.cpp:2093/2102/2119는 `CornerChecker::IDX_FLAG_HD_5_8_SET_TYPE_0` 호출 (별개 식별자).

`FLAG_HD_5_8_SET_TYPE_1` (3건): common.h:724 정의, decoder.cpp:2106, 2123 대입. 비교하는 곳은 없다 (7010, 7016이 `TYPE_0`인지만 보고 `else`로 처리한다).

`FLAG_HD_5_8_SET_TYPE_2`: **정의 자체가 없다.** 히트는 [corner.h:81](../../../../../../0_LDPC_original/src/corner.h#L81)과 [corner.cpp:176](../../../../../../0_LDPC_original/src/corner.cpp#L176)의 `IDX_FLAG_HD_5_8_SET_TYPE_2`뿐이며, 이는 corner 로그 열 이름이지 분기 값이 아니다.

`common.h:717-725` 원문:

```cpp
enum {
    FLAG_HD_1_4_SET_TYPE_0 = 0,
    FLAG_HD_1_4_SET_TYPE_1 = 1,
};

enum {
    FLAG_HD_5_8_SET_TYPE_0 = 0,
    FLAG_HD_5_8_SET_TYPE_1 = 1,
};
```

곁들여 확인한 사실: [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp#L612)의 `Clear_Flag`가
`flag_HD_1_4_Set = FLAG_LOW`를 대입한다. `FLAG_LOW`는 [common.h:45](../../../../../../0_LDPC_original/src/common.h#L45)에서 0이므로
`FLAG_HD_1_4_SET_TYPE_0`과 같은 값이다. 따라서 `flag_HD_1_4_Set`은 프레임 전체에서 0으로 고정된다.

### 확인 3: 선언 주석이 유일한 단서인가

[decoder.h:296-306](../../../../../../0_LDPC_original/src/decoder.h#L296) 원문:

```cpp
    int         flag_BF_on;     // 0 : 3bit precision mode, 1: 1bit precision mode
    int         flag_HD_1_4_Set;
    int         flag_HD_5_8_Set;
    int         syn_weight;     // partial syndrome
    int         psyn_weight;    // partial syndrome
    int         syn_th_BF;      //
    int         syn_th_BF0;   // S-4 Set
    int         syn_th_BF1;   // S-4 Set
    //int         syn_th_BF2;   // S-4 Set
    int       syn_th_5_8_Set_0;   // S-8 Set
    int       syn_th_5_8_Set_1;   // S-8 Set
```

[decoder.cpp:459-493](../../../../../../0_LDPC_original/src/decoder.cpp#L459)은 `matrix_sel`별 `switch` 세 개다.
첫 `switch`(459-473)가 `syn_th_BF0`과 `syn_th_BF1`을 함께 대입하고, 그 위 주석은
`// HBF 진입 판단 SW threshold`(decoder.cpp:458)다. 둘째와 셋째 `switch`(476-493) 위 주석은
`// 5_8 Set mode 진입 판단 SW threshold`(decoder.cpp:475)다.

`S-4 Set`, `S-8 Set` 표현의 저장소 전수 Grep 결과는 다섯 줄뿐이고 모두 이 선언부다
(`decoder.h:302-306`, 그리고 [1_LDPC_revised/decoder.h:349-351](../../../../../../1_LDPC_revised/decoder.h#L349)의 같은 사본).
[0_LDPC_original/docs/](../../../../../../0_LDPC_original/docs/)에는 BF 관련 서술이
`architecture.md:199`의 약어표 한 줄(`BF / HBF | Bit Flipping / Hard-decision BF`)뿐이다.

판정: 주석 `// S-4 Set`이 유일한 문자 단서인 것은 **확인됨**. 다만 "유일한 단서"는 아니다.
아래 세 가지 코드 단서가 더 있다 (증거 E-5, E-6, E-7).

### 확인 4: 배경 메모 원문 대조

[msg1.md](../../../../../../msg1.md) 전문을 읽었다. iteration 1~4 구간에 관한 원문은 다음 넷이다.

- ㉠ `msg1.md:9-11`: "decoder iteration(mn)은 error 가 낮을 경우 bit flipping(BF) mode로 동작하고,
  그렇지 않으면 normal decoding로 동작해 bf는 error가 적은 1~4용이야. error가적은지는 Syndrome Weight으로 결정하고
  SW threshold로 구분해."
- ㉡ `msg1.md:19-22`: "bf를 타면 iteration 0,1,2,3,4,5,6,7.. / bf를 안타면 iteration 0,5,6,7.. 으로 셈돼.
  bf는 타도 normal decoding처음부터시작하는거야 / bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리하는거야.
  dao는 이렇게 동작하는게 구현안되어있을거야. / 추가로 bf 구간은 늘어나지않아. 딱 1~4야"
- ㉢ `msg1.md:26-28`: "추가로 sw구간에 따라 llr matrix의 거의 마지막 column쯤에 있는 flag가 -1아닐 수 있어
  / 이건 1~8에서만 사용돼. / 낮은 error에서 구간별 llr matrix를 다르기 사용하기위함이야"
- ㉣ `msg1.md:29-34`: "위 520b tlc off의 경우 / iter start/iter end/flag라고하면 / 1/4/-1 / 5/8/0 / 5/8/1 / 5/8/2"

세 문장의 뜻 판정:

- ㉮ "bf라면 llr matrix에서 threshold를 받지 않아. -1로 처리하는거야" (`msg1.md:21`)
  → **row의 분기 칸을 뜻한다**고 판정한다. 근거 셋이다.
  ㉠ 이 문장이 나온 시점까지 메모가 말한 "threshold"는 `msg1.md:10-16`의 SW threshold
    (`SW_TH_BF_520B_TLC_OFF` 류)뿐이고, LLR matrix 안의 th 칸은 메모에 한 번도 등장하지 않는다.
  ㉡ 이어지는 `msg1.md:30-34`가 "iter start/iter end/flag"의 셋째 칸 값으로 `-1`을 적어 같은 `-1`을 가리킨다.
  ㉢ LLR matrix의 th 칸을 뜻한다는 해석은 코드와 어긋난다. BF 중에도 LLR matrix row는 읽힌다.
    [decoder.cpp:3986](../../../../../../0_LDPC_original/src/decoder.cpp#L3986)의 `Get_VNU_LLR_SET_FILE`이
    `cur_set_idx`로 ch와 th를 모두 가져오고, 1bit precision 우회는
    [decoder.cpp:4056](../../../../../../0_LDPC_original/src/decoder.cpp#L4056)의 `(TRUE == flag_BF_on) && (iter <= 4) && (v_deg > DV_5)`
    조건이 걸린 VN만 해당한다. `v_deg <= DV_5`인 VN은 BF 구간에서도 th1~th7을 그대로 쓴다.
    파일도 iteration 1~4에 row 14개를 실제로 담고 있다.
- ㉯ "추가로 bf 구간은 늘어나지않아. 딱 1~4야" (`msg1.md:22`)
  → **BF 구간의 iteration 길이**를 제약한다. 분기 개수나 flag 값이 아니라 `ITER_MAX_HBF`가 4로 고정이라는 뜻이다.
  코드의 `ITER_MAX_HBF`(비AUTO에서 4)와 `Select_BF`의 `mn + ITER_MAX_HBF`가 이 서술과 맞는다.
  이 문장은 iteration 1~4에 분기가 있느냐 없느냐에 대해서는 아무 말도 하지 않는다.
- ㉰ "이건 1~8에서만 사용돼" (`msg1.md:27`)
  → "이건"은 바로 앞 문장의 **"llr matrix의 거의 마지막 column쯤에 있는 flag가 -1이 아닌 상태"**를 가리킨다.
  즉 분기 index가 붙는 것은 iteration 1~8 범위뿐이라는 제약이다. 이 범위는 1~4를 **포함한다**.

메모 예시와 현 파일이 모순인가:

**부분 모순이며, 결정적 모순은 아니다**로 판정한다.

- ㉮ 예시 `1/4/-1`은 `msg1.md:29`가 "위 520b tlc off의 경우"라고 못박은 **특정 layout의 사례**다.
  현 파일이 쓰는 layout은 `LAYOUT_PRIME_512B_TLC_VSS_OFF`이고 (문턱 `SW_TH_BF0_512B_TLC_OFF` 680,
  `SW_TH_BF1_512B_TLC_OFF` 130), 예시의 520B와 다른 파라미터 집합이다.
- ㉯ 예시가 5~8에 분기 셋(`0`, `1`, `2`)을 두는데, 현 코드는 `FLAG_HD_5_8_SET_TYPE_2`가 **정의조차 없어**
  셋째 분기를 표현하지 못한다. 즉 예시 자체가 현 소스가 구현하지 않은 layout을 그린 것이다.
  예시를 현 소스의 사실 서술로 읽을 수 없다.
- ㉰ 반대로 `msg1.md:21`("bf라면 ... -1로 처리하는거야")은 layout을 한정하지 않은 일반 서술이고,
  현 파일이 iteration 1~4에 분기 `0`과 `1`을 둔 것과 **직접 충돌한다**.
- ㉱ 같은 메모 안 `msg1.md:27`("이건 1~8에서만 사용돼")은 분기가 1~4를 포함할 수 있다고 읽힌다.
  메모 내부에 긴장이 있다.

따라서 R2-7이 "메모는 1~4를 분기 없음으로 적는다"고 단정한 것은 절반만 맞다. 메모에는
1~4를 분기 없음으로 적은 문장(`msg1.md:21`, `msg1.md:31`)과 분기 범위를 1~8로 적은 문장(`msg1.md:27`)이
함께 있고, 숫자 예시는 다른 layout의 것이다.

### 확인 5: 상위 문서 7장 미결정 목록 대조

[20260902_SW_branch_LLR_matrix.md:353-361](../../20260902_SW_branch_LLR_matrix.md) 원문:

- ㉮ "표기를 4장 ㉮(분기 전용 줄 추가), ㉯(세 자리), ㉰(row 마지막 칸만) 중 무엇으로 갈지"
- ㉯ "SW 문턱을 컴파일 상수로 둘지, 파일이나 실행 인자로 받을지. 후자면 `PARAM_DEC` 또는 LLR matrix 파일에 자리를 만들어야 한다"
- ㉰ "분기가 있는 구간을 iteration 1~8로 못박을지, 임의 구간을 허용할지. `LLR_MATRIX_1.txt`는 1~8만 쓰지만 형태 자체는 어디든 허용한다"
- ㉱ "`__AUTO_LLR_OPT__`가 아닌 경로(`decoder.cpp:7001-7020`)의 하드코딩을 걷어내고 한 갈래로 통일할지, 두 경로를 그대로 둘지"

판정: **iteration 1~4에 분기를 둘지와 문턱 130을 쓸지는 네 항목 어디에도 없다. 확인됨.**

㉯가 덮는가: **덮지 않는다.** ㉯는 문턱 값의 **출처**(컴파일 상수인가 파일인가)를 묻는다.
"1~4 구간에 문턱이 하나라도 있어야 하는가", "있다면 그 값이 130인가"는 출처와 독립이다.
문턱을 파일에서 받기로 정해도 "1~4 구간에 분기가 있는가"는 여전히 미결이고,
컴파일 상수로 두기로 정해도 "그 상수가 130인가"는 여전히 미결이다.

㉰가 덮는가: **덮지 않는다.** ㉰는 분기 구간의 **iteration 범위**를 1~8로 못박을지를 묻는다.
1~8로 못박아도 그 안에서 1~4가 분기를 갖는지는 정해지지 않는다.
㉰를 "임의 구간 허용"으로 정하면 오히려 1~4 분기가 자동으로 허용되어 결정이 조용히 넘어간다.

### 확인 6: mn 수열 손 실행

읽은 코드:

- 메인 루프 `for (mn = 0; mn < MN + 1; mn++)` [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp#L1120)
- 루프 앞머리 `Clear_Iter_Start(); Clear_Edge_Restart();` [decoder.cpp:1131-1133](../../../../../../0_LDPC_original/src/decoder.cpp#L1131)
- `Clear_Edge_Restart` 정의 [decoder.cpp:709-739](../../../../../../0_LDPC_original/src/decoder.cpp#L709)
- `Select_BF` 호출 `if (mn == 0) { Select_BF(); }` [decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp#L1968)
- code_diff 5.1 수정 후 `Select_BF` ([code_diff.md 5장](../../code_diff.md#ch5))

㉮ `Is_Iter_Type_Edge_Clear`에 넘기는 인자: **`mn`이다.**
`Clear_Edge_Restart()`는 인자를 받지 않고, 본문 [decoder.cpp:712](../../../../../../0_LDPC_original/src/decoder.cpp#L712)와
[decoder.cpp:726](../../../../../../0_LDPC_original/src/decoder.cpp#L726)이 멤버 `mn`을 그대로 넘긴다.
별도의 `iter` 카운터는 없다. `iter`는 `Is_Iter_Type_Edge_Clear`의 매개변수 이름일 뿐이다.

호출 순서: 루프 몸통 앞머리(1133)에서 `Clear_Edge_Restart()`가 먼저 돌고,
몸통 끝(1968-1970)에서 `mn == 0`일 때 `Select_BF()`가 `mn`을 밀어 올린다.
따라서 `mn == 0`의 edge clear는 두 프레임 종류 모두 수행한다.

수정 후(`ITER_MAX_HBF` 4, `Select_BF` 부활) 손 실행 결과:

| 항목 | BF 진입 프레임 | BF 미진입 프레임 |
|------|---------------|-----------------|
| 진입 조건 | `MODE_BF_ON == BF_mode && syn_weight < syn_th_BF0`(680) | 그 밖 |
| `Select_BF`의 `mn` 조작 | 없음 | `mn = 0 + 4 = 4`, `MN = MN + 4` |
| `mn` 수열 | 0, 1, 2, 3, 4, 5, 6, ..., 120 | 0, 5, 6, 7, ..., 124 |
| `Clear_Edge_Restart` 평가 시점 | 위 수열의 모든 값 | 위 수열의 모든 값 (1~4는 평가 자체가 없음) |
| 고정 clear 지점 (`iter == 0/1/ITER_MAX_HBF+1`) | mn 0, 1, 5 | mn 0, 5 (`mn == 1`은 도달 불가) |

`MN` 값의 근거: `local_opt.cpp:116-131`이 HD에서 `MN[i] -= ITER_MAX_HBF`, `MN[0] = ITER_MAX_HBF`를 적용해
`MN[MN_num-1] = 124 - 4 = 120`이 된다. 메인 루프는 이 값을 쓴다(decoder.cpp:1118).
미진입 프레임은 `Select_BF`에서 `MN`이 다시 4 늘어 124가 된다.
두 프레임 모두 normal decoding을 120회 도는 셈이며, 이는 설계 의도와 맞는다.

㉰ `restart_iter`에 3이 든 파일:

| 프레임 | mn 3 도달 | `Is_Iter_Type_Edge_Clear(3)` 평가 | edge clear 수행 |
|--------|----------|----------------------------------|----------------|
| BF 진입 | 도달함 | 고정 조건 불일치 → restart 반복문에서 `3 == restart_iter[i]` 일치 → TRUE | **수행** |
| BF 미진입 | 도달 못함 (0 다음이 5) | 평가되지 않음 | **미수행** |

㉱ `restart_iter`에 10이 든 파일 (대조군):

| 프레임 | mn 10 도달 | 평가 결과 | edge clear 수행 |
|--------|-----------|----------|----------------|
| BF 진입 | 도달함 (0..120) | TRUE | 수행 |
| BF 미진입 | 도달함 (0, 5..124) | TRUE | 수행 |

대칭이다. 가설 F의 "restart 지점이 1 이상 4 이하일 때만 비대칭" 확인됨.

덧붙임: 미진입 프레임의 mn과 파일의 iteration 번호는 어긋나지 않는다.
`Get_Cur_LLR_Idx_FILE(mn)`이 `mn`을 그대로 쓰므로 미진입 프레임의 첫 복호 mn 5는
파일의 iteration 5 구간 row를 고른다. 메모 `msg1.md:20`의 "bf를 안타면 iteration 0,5,6,7.. 으로 셈돼"와 일치한다.
`iter_num -= ITER_MAX_HBF`(decoder.cpp:1976)는 결과 집계용 횟수 보정이며 row 선택과 무관하다.

### 확인 7: 비AUTO 원본의 동일성

[decoder.cpp:6538-6598](../../../../../../0_LDPC_original/src/decoder.cpp#L6538) `Is_Iter_Type_Edge_Clear`의 비AUTO(`#else`) 갈래는
`LAYOUT_PRIME_512B_TLC_VSS_OFF`일 때만 동작하며 세 갈래로 나뉜다.

| 모드 | restart 지점 | `restart_iter` 참조 |
|------|-------------|--------------------|
| HD, 1.5SD (6568-6576) | `iter == 0`, `iter == 1`, `iter == ITER_MAX_HBF + 1` | **없음** |
| 2SD (6577-6583) | `iter == 0`, `RSP1_2SD_PRIME_1`, `RSP1_2SD_PRIME_2` | 없음 |
| 3SD (6584-6594) | `iter == 0`, `RSP1_3SD_PRIME_1` ~ `_6` | 없음 |

`Is_Iter_Type_Init`의 비AUTO 갈래(6626-6673)도 같은 모양이며, HD와 1.5SD는 `iter == 0`만 본다.

[common.h:679-686](../../../../../../0_LDPC_original/src/common.h#L679) 상수 값:

```
RSP1_2SD_PRIME_1    241
RSP1_2SD_PRIME_2    581
RSP1_3SD_PRIME_1    171
RSP1_3SD_PRIME_2    312
RSP1_3SD_PRIME_3    653
RSP1_3SD_PRIME_4    844
RSP1_3SD_PRIME_5    1035
RSP1_3SD_PRIME_6    1301
```

여덟 값 모두 4보다 크다. 그리고 `Select_BF`의 `if / else if`는 `MODE_DEC_HD`와 `MODE_DEC_1_5SD`만 다루므로
(decoder.cpp:2087, 2113) 2SD와 3SD에서는 `mn`이 밀리지 않는다. 두 사정이 겹쳐 비AUTO 원본에는
"미진입 프레임만 restart를 놓치는" 상황이 **성립할 수 없다**.

판정: **새 결함이다.** 비AUTO 원본은 HD와 1.5SD에서 `restart_iter`를 아예 보지 않고,
`restart_iter`를 보는 2SD와 3SD는 `mn`이 밀리지 않으며 상수도 모두 5 이상이다.
현재 AUTO 빌드도 `ITER_MAX_HBF`가 0이라 `mn`이 밀리지 않아 모든 프레임이 mn 1~4를 돈다.
code_diff 1.2(`ITER_MAX_HBF` 4)와 5.1(`Select_BF` 부활)과 8.1(AUTO 갈래로 통일)이 **함께** 들어갈 때
처음으로 나타나는 조합이다.

### 확인 8: 검사 위치의 실행 가능성

파서가 `ITER_MAX_HBF`를 참조할 수 있는가: **가능하다. 확인됨.**
[local_opt.cpp:1](../../../../../../0_LDPC_original/src/local_opt.cpp#L1)이 `Local_Opt.h`를 포함하고
`Local_Opt.h:4`가 `common.h`를 포함한다. 실제로 같은 함수 안
[local_opt.cpp:126](../../../../../../0_LDPC_original/src/local_opt.cpp#L126)과
[local_opt.cpp:129](../../../../../../0_LDPC_original/src/local_opt.cpp#L129)가 이미 `ITER_MAX_HBF`를 쓴다.
`restart_iter`를 읽는 곳은 local_opt.cpp:85-90이고 그보다 뒤인 116-131에서 `ITER_MAX_HBF`를 쓰므로
검사를 85-90 자리에 넣든 그 뒤에 넣든 참조에 문제가 없다.

restart 지점이 iteration 1~4에 있는 것이 유효한 사용인가: **유효한 사용이다.**
BF 진입 프레임은 iteration 1, 2, 3, 4를 실제로 돌고, 그 안에서 edge를 지우고 다시 시작하는 것은
BF 구간 안 재시작이라는 뜻을 갖는다. 미진입 프레임이 그 지점을 수행하지 않는 것은
그 프레임이 iteration 1~4 자체를 돌지 않기 때문이며, 의미상 어긋난 동작이 아니다.
따라서 `restart_iter[i] <= ITER_MAX_HBF`를 오류로 잡으면 정상 사용을 막는다.

결정적 반례: [5_DAO/Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt](../../../../../Input/Ref_C/Prime_ECC_2.4/Initial_LLR_matrix/LLR_MATRIX_0.txt)는
`restart_num = 1`, `restart_iter[0] = 2`를 담고 있다 (파일 9행의 `1`과 11행의 `2`,
파서 순서 `num_group=3` → `num_set_each_group = 1 1 1` → `type_each_group = 1 1 1` → `restart_num = 1` → `restart_iter = 2`).
제안된 검사를 넣으면 이 파일이 곧바로 거부된다.

---

## ㉰ 증거 목록

### 가설 E 관련

| 번호 | 증거 | 분류 | 근거 |
|------|------|------|------|
| E-1 | 파일이 iteration 1~4에 분기 두 개(`0`, `1`)를 둔다 | 확인됨 | `LLR_MATRIX_1.txt` row 1~8이 `its=1~1`, `its=2~4`에 `flag=0`, row 9~14가 `its=1~4`에 `flag=1`. 헤더 11행 `20 20 21 20 21 21 1 1 1 1 1 1` |
| E-2 | 수정 전 코드가 `flag_HD_1_4_Set`을 `FLAG_HD_1_4_SET_TYPE_0`으로 못박는다 | 확인됨 | decoder.cpp:2090이 유일한 대입. decoder.cpp:612가 `FLAG_LOW`(=0=TYPE_0)로 초기화 |
| E-3 | `FLAG_HD_1_4_SET_TYPE_1`을 대입하는 코드가 저장소에 없다 | 확인됨 | 전수 Grep 히트가 common.h:719 정의 한 줄뿐 |
| E-4 | `syn_th_BF1`은 선언과 대입 두 곳뿐이고 읽는 곳이 없다 | 확인됨 | decoder.h:303, decoder.cpp:468. 다른 히트 없음 |
| E-5 | 130은 680보다 작아 BF 진입 영역 안을 가르는 값으로만 쓸 수 있다 | 확인됨 | common.h:236-237의 `SW_TH_BF0_512B_TLC_OFF` 680, `SW_TH_BF1_512B_TLC_OFF` 130. decoder.cpp:2088이 `syn_weight < 680`을 BF 진입 조건으로 쓴다 |
| E-6 | 비AUTO 그룹 선택이 `flag_HD_1_4_Set`을 실제로 읽어 iteration 1~4의 갈래를 나눌 자리를 갖고 있다 | 확인됨 | decoder.cpp:7002, 7006. `TYPE_0`이 아니면 `selected_group`이 -1로 남아 decoder.cpp:7049가 오류를 찍는다. 값을 만드는 곳만 없다 |
| E-7 | 주석이 `syn_th_BF0`과 `syn_th_BF1`을 한 묶음(`// S-4 Set`)으로, `syn_th_5_8_Set_0/1`을 다른 묶음(`// S-8 Set`)으로 나눈다 | 확인됨 | decoder.h:302-306. "S-8 Set" 묶음은 실제로 5~8 구간의 두 갈래를 만든다 (decoder.cpp:2099-2110) |
| E-8 | 메모가 iteration 1~4를 분기 없음(`-1`)으로 적는다 | 부분 확인 | `msg1.md:21`과 `msg1.md:31`은 그렇게 적는다. 그러나 `msg1.md:29`가 그 예시를 "520b tlc off의 경우"로 한정하고, `msg1.md:27`은 분기 범위를 1~8로 적는다 |
| E-9 | 메모 예시가 현 소스로 표현 불가능한 layout을 그린다 | 확인됨 | 예시 `5/8/2`의 셋째 분기를 담을 `FLAG_HD_5_8_SET_TYPE_2`가 common.h:722-725에 정의되어 있지 않다 |
| E-10 | 상위 문서 7장 미결정 네 항목에 이 결정이 없다 | 확인됨 | 20260902_SW_branch_LLR_matrix.md:353-361 |
| E-11 | 7장 ㉯가 이 항목을 덮는다 | 반박됨 | ㉯는 문턱 값의 출처만 묻는다. 구간에 문턱이 있어야 하는가와 그 값이 130인가는 출처와 독립이다 |
| E-12 | "코드에도 메모에도 근거가 없는 새 동작" | 반박됨 | E-5, E-6, E-7이 코드 쪽 근거다. 메모 쪽도 `msg1.md:27`이 분기 범위에 1~4를 포함한다 |

### 가설 F 관련

| 번호 | 증거 | 분류 | 근거 |
|------|------|------|------|
| F-1 | `Clear_Edge_Restart`가 mn 루프 안에서 멤버 `mn`을 그대로 넘긴다 | 확인됨 | decoder.cpp:1133 호출, decoder.cpp:712와 726이 `Is_Iter_Type_Edge_Clear(mn)` |
| F-2 | AUTO 갈래가 `iter == m_param_LLR->restart_iter[i]`를 그대로 비교한다 | 확인됨 | decoder.cpp:6549-6552 (HD, 1.5SD), 6560-6563 (그 밖). code_diff 8.1 수정 후도 같은 비교를 유지한다 |
| F-3 | BF 미진입 프레임의 mn 수열이 0, 5, 6, ...이다 | 확인됨 | `Select_BF`가 `mn = mn + ITER_MAX_HBF`(decoder.cpp:2097)를 mn 0에서 수행하고 for문이 증가시킨다 (decoder.cpp:1120, 1968-1970) |
| F-4 | `restart_iter`가 1 이상 4 이하이면 미진입 프레임만 edge clear를 놓친다 | 확인됨 | 확인 6 ㉰ 손 실행표 |
| F-5 | 비AUTO 원본에도 같은 건너뛰기가 이미 있다 | 반박됨 | decoder.cpp:6568-6576의 HD, 1.5SD 갈래는 `restart_iter`를 참조하지 않는다. 2SD와 3SD는 `Select_BF`가 `mn`을 밀지 않는다 (decoder.cpp:2087, 2113) |
| F-6 | 비AUTO restart 상수가 모두 4보다 커서 드러나지 않는다 | 확인됨 (다만 F-5가 더 앞선 이유다) | common.h:679-686의 여덟 값이 171 이상 |
| F-7 | "현 파일은 `restart_num`이 0이라 잠재 결함이다" | 부분 확인 | 새 파일 `LLR_MATRIX_1.txt`는 `restart_num = 0`이 맞다. 그러나 구 파일 `LLR_MATRIX_0.txt`는 `restart_num = 1`, `restart_iter[0] = 2`다 |
| F-8 | 파서가 `ITER_MAX_HBF`를 참조할 수 있다 | 확인됨 | local_opt.cpp:1이 Local_Opt.h를, Local_Opt.h:4가 common.h를 포함. local_opt.cpp:126, 129가 이미 사용 |
| F-9 | 파서의 검사 실패가 실행을 멈춘다 | 반박됨 | `err`는 local_opt.cpp:56 선언과 140 대입뿐이며 `Read_LLR_info_Auto`는 void다 (R2-8과 동일 사실) |

---

## ㉱ 처방 평가

### E 처방: "상위 7장에 Decision 항목을 추가하고 사용자 결정을 받는다"

**처방 유효, 다만 문안 보강이 필요하다.**

유효한 이유: 확인 5에서 본 대로 7장 ㉮~㉱ 어디도 이 결정을 덮지 않는다.
그리고 이 결정은 되돌리기 어렵다. 130을 쓰기로 하면 DAO가 그 문턱을 전제로 파라미터를 최적화하게 되고,
나중에 문턱을 바꾸면 최적화 결과가 통째로 무효가 된다.

보강해야 할 점 셋:

- ㉮ 발견 문구를 고쳐야 한다. "코드에도 메모에도 근거가 없는 새 동작"은 사실과 다르다.
  정확히는 "코드가 자리(`FLAG_HD_1_4_SET_TYPE_1`, `syn_th_BF1` = 130, `// S-4 Set` 묶음,
  decoder.cpp:7002와 7006의 읽는 쪽)를 만들어 두고 값을 만드는 쪽만 비워 둔 동작이며,
  이번 계획이 그 빈자리를 채운다"이다
- ㉯ 메모 인용을 바로잡아야 한다. `msg1.md:31`의 `1/4/-1`은 `msg1.md:29`가 "520b tlc off의 경우"로
  한정한 예시이고, 같은 메모 `msg1.md:27`은 분기가 iteration 1~8에서 쓰인다고 적는다.
  "메모가 1~4를 분기 없음으로 못박았다"고 쓰면 근거가 실제보다 세게 읽힌다
- ㉰ 선택지를 코드 근거와 함께 나열해야 한다 (아래)

문서가 지금 취할 기본값에 코드 근거가 있는가: **있다. 다만 결정적이지는 않다.**

분기 둘을 유지하고 130을 쓰는 쪽의 근거:

- ㉠ 130 < 680이므로 이 값은 BF 진입 영역(`syn_weight < 680`) 안을 가르는 용도로만 뜻이 선다 (E-5)
- ㉡ `decoder.h:302-303`이 `syn_th_BF0`과 `syn_th_BF1`을 `// S-4 Set` 한 묶음으로 적고,
  같은 방식의 `// S-8 Set` 묶음은 실제로 5~8 구간 두 갈래를 만든다 (E-7)
- ㉢ `FLAG_HD_1_4_SET_TYPE_1`이 정의되어 있고 decoder.cpp:7002, 7006이 그것을 읽을 준비를 갖췄다 (E-6)
- ㉣ 파일이 iteration 1~4에 분기 둘을 두고 row 14개를 실제로 채웠다 (E-1)

메모대로 1~4를 분기 없음으로 보는 쪽의 근거:

- ㉠ `msg1.md:21`의 일반 서술 (E-8)
- ㉡ 130은 저장소 어디에서도 실행된 적이 없는 값이다. 값의 타당성을 뒷받침하는 실험 기록이 없다 (E-4)
- ㉢ 1~4를 분기 없음으로 보면 파일의 row 9~14(그룹 2)가 통째로 쓰이지 않게 되어
  파일과 코드가 어긋난다. 즉 이 선택은 파일 수정을 함께 요구한다

정리하면 코드는 "분기 둘 + 130"을 지지하고 메모의 한 문장은 반대한다.
파일까지 함께 보면 "분기 둘"을 취하는 쪽이 파일 수정 없이 성립하는 유일한 선택이다.
문서는 이 비대칭을 적고, 사용자에게 물을 질문을 "130이라는 값이 실제 특성에서 타당한가"로 좁히는 것이 낫다.

권장 Decision 문안 (7장 ㉲로 추가):

> ㉲ iteration 1~4 구간에 SW 분기를 둘지, 둔다면 분기 경계를 무엇으로 할지.
>    `LLR_MATRIX_1.txt`는 이 구간에 분기 둘(row 14개)을 두었고,
>    소스에는 쓰이지 않는 상수 `SW_TH_BF1_512B_TLC_OFF`(130)와 쓰이지 않는 값
>    `FLAG_HD_1_4_SET_TYPE_1`이 그 자리를 위해 준비되어 있다.
>    130은 아직 한 번도 실행된 적이 없는 값이므로 그대로 쓸지 확인이 필요하다.
>    분기를 두지 않기로 하면 파일에서 그룹 2를 빼는 수정이 함께 필요하다.

### F 처방: "파서가 `restart_iter[i] <= ITER_MAX_HBF`를 오류로 잡거나 문서에 제약을 적는다"

**앞 갈래(오류로 잡기)는 처방 반대. 뒤 갈래(문서에 제약 적기)는 처방 유효하되 문구 수정 필요.**

앞 갈래에 반대하는 이유 셋:

- ㉮ 실재하는 파일을 거부한다. `LLR_MATRIX_0.txt`가 `restart_iter[0] = 2`를 담고 있다 (확인 8).
  DAO가 구 파일을 출발점으로 삼는 실행에서 곧바로 걸린다
- ㉯ 정상 사용을 막는다. BF 진입 프레임은 iteration 1~4를 실제로 돌고,
  그 안의 restart는 뜻이 있는 지정이다 (확인 8)
- ㉰ 애초에 멈추지 못한다. 파서의 `err`는 흐름을 바꾸지 않는다 (F-9, R2-8과 동일 사실).
  "오류로 잡는다"고 적어도 실행은 그대로 이어지고 로그 한 줄만 남는다.
  R2-8이 먼저 해결되지 않으면 이 처방은 형식만 갖춘 검사가 된다

대안:

- ㉮ 상위 문서 5.6장과 code_diff 8.1에 다음을 적는다.
  "`restart_iter`의 값이 1 이상 `ITER_MAX_HBF` 이하이면 그 지점은 BF 진입 프레임에서만 수행된다.
  BF 미진입 프레임은 그 iteration 자체를 돌지 않기 때문이다.
  두 프레임이 같은 지점에서 재시작하기를 바라면 `ITER_MAX_HBF`보다 큰 값을 쓴다"
- ㉯ 파서에는 오류가 아니라 정보 기록을 넣는다. `Read_LLR_info_Auto`가 이미 결과 파일에
  `restart_num`과 `restart_iter`를 적으므로(local_opt.cpp:156-161) 그 옆에
  "1 이상 4 이하 값은 BF 진입 프레임에만 적용됨"을 함께 적으면 실행을 막지 않고 사실이 남는다
- ㉰ 구 파일 `LLR_MATRIX_0.txt`의 `restart_iter = 2`가 이번 변경으로 동작이 달라지는 사례이므로,
  9장 적용 순서의 5단계(BF 부활) 검증 항목에 "구 파일로 돌렸을 때 미진입 프레임의 edge clear 횟수가
  줄어드는 것이 의도인지 확인"을 넣는다

---

## ㉲ 검증 중 새로 드러난 사실

- ㉮ **`syn_th_5_8_Set_1`도 읽히지 않는다.**
  대입은 decoder.cpp:489, 492 두 곳이고 읽는 곳은 없다 (유일한 등장이 decoder.cpp:583의 주석 처리된 `printf`).
  code_diff 2.2가 "`syn_th_BF`와 `syn_th_BF1`은 지금도 대입만 되고 읽히는 곳이 없으므로 지운다"고 적었는데,
  같은 상태인 멤버가 하나 더 있다. 실제로 읽히는 문턱은 `syn_th_BF0`과 `syn_th_5_8_Set_0` 둘뿐이다

- ㉯ **code_diff 4.1이 전제한 "문턱 오름차순"이 상수 값에서 깨진다.**
  `SW_TH_5_8_SET0_512B_TLC_OFF` = 1100, `SW_TH_5_8_SET1_512B_TLC_OFF` = 950 (common.h:244, 251)으로 내림차순이다.
  code_diff 4.1이 적은 대로 셋째 분기가 생겨 `syn_th_sw_branch[1][0] = 1100`, `syn_th_sw_branch[1][1] = 950`이 되면
  code_diff 5.1의 `Select_SW_Branch`는 `weight < 1100`에서 무조건 0을 돌려주므로
  **분기 1이 영영 선택되지 않는다**. `weight >= 1100`이면 `weight < 950`이 거짓이라 2를 돌려준다.
  R2-9가 지적한 "문턱 양수 오름차순 대조"가 필요한 구체적 사례다.
  심각도 MEDIUM으로 새 항목을 세울 값이 있다

- ㉰ **`FLAG_HD_5_8_SET_TYPE_2`는 정의되어 있지 않다.**
  common.h:722-725의 enum에는 `TYPE_0`과 `TYPE_1`뿐이다.
  corner.h:81과 corner.cpp:176의 `IDX_FLAG_HD_5_8_SET_TYPE_2`는 로그 열 이름이며 분기 값이 아니다.
  code_diff 5.1이 corner 이벤트를 `IDX_FLAG_HD_5_8_SET_TYPE_0 + cur_sw_branch_idx[1]`로 더해 쓰는 것은
  corner.h 쪽 세 값이 이어져 있어 성립하지만, 분기 값 자체의 enum은 두 개짜리라 셋째 분기를 표현하지 못한다.
  메모 예시(`5/8/2`)가 현 소스로 표현 불가능하다는 근거이기도 하다

- ㉱ **`syn_th_BF0`이 `default:` 갈래에서 대입되지 않는다.**
  decoder.cpp:459-473의 `switch`는 `LAYOUT_PRIME_512B_TLC_VSS_OFF`에서만 `syn_th_BF0`을 대입하고
  `default:`에서는 `syn_th_BF`(읽히지 않는 멤버)를 대입한다.
  그런데 decoder.cpp:2088은 `syn_th_BF0`을 무조건 읽는다.
  `Decoder::Initialize_Dec`(decoder.cpp:19-21)은 포인터만 초기화하므로 다른 layout에서는 값이 불확정이다.
  code_diff 4.1의 수정 후 코드가 `default: { syn_th_BF0 = SW_TH_BF_DEFAULT; break; }`로 이 구멍을 메운다.
  계획이 의도치 않게 고치는 기존 결함이므로 문서에 적어 두면 좋다

- ㉲ **구 파일 `LLR_MATRIX_0.txt`의 `restart_iter`가 2다.**
  `restart_num = 1`, `restart_iter[0] = 2`. R2-16이 "현 파일은 `restart_num`이 0이라 잠재 결함"이라고 적은 것이
  새 파일에는 맞지만 구 파일에는 맞지 않는다. 이번 변경은 실재하는 입력의 동작을 바꾼다

- ㉳ **code_diff 8.1의 갈래 통일이 HD와 1.5SD에 없던 기능을 새로 넣는다.**
  비AUTO 원본의 HD, 1.5SD 갈래(decoder.cpp:6568-6576)는 `restart_iter`를 아예 참조하지 않는다.
  AUTO 갈래(6542-6554)는 참조한다. 8.1이 AUTO 갈래만 남기면 비AUTO 빌드의 HD와 1.5SD가
  처음으로 파일 기반 restart를 갖게 된다. R2-1이 지적한 "비AUTO 2SD와 3SD restart 지점 8개 소실"과는
  방향이 반대인 별개의 변화이며, "갈래 통일"이라는 말로 덮이지 않는 동작 추가다

- ㉴ **BF 진입 프레임과 미진입 프레임의 mn 상한이 다르다.**
  진입 프레임은 mn 120까지, 미진입 프레임은 `Select_BF`가 `MN`을 4 늘려 mn 124까지 돈다 (확인 6 표).
  파일의 iteration 121~124 row(그룹 11의 뒷부분)는 미진입 프레임만 쓴다.
  두 프레임 모두 normal decoding 120회라는 점에서는 대칭이므로 설계 의도로 보이나,
  R2-5가 이 지점을 결함으로 적었다면 판정을 다시 볼 여지가 있다 (팀 V3 소관)

- ㉵ **DAO 쪽 검사가 분기 flag를 아직 막고 있다.**
  [DAO_LLR_MATRIX.py:344-346](../../../../../SRC/DAO_LLR_MATRIX.py#L344)이
  `row.floor_flag != -1`이면 무효로 판정한다. 메모 `msg1.md:21`의
  "dao는 이렇게 동작하는게 구현안되어있을거야"와 일치한다.
  분기를 살리는 결정과 함께 이 검사도 고쳐야 새 파일이 DAO를 통과한다 (R2-6과 겹치는 사실)
