# Round 3 검증: 팀 V1 워커 2 (R2-2, R2-4)

작성: 2026-09-03 01:41:20

검증 대상 문서: [code_diff.md](../../code_diff.md), [20260902_SW_branch_LLR_matrix.md](../../20260902_SW_branch_LLR_matrix.md)
검증 대상 소스: [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp), [decoder.h](../../../../../../0_LDPC_original/src/decoder.h), [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp), [ecc_data.h](../../../../../../0_LDPC_original/src/ecc_data.h), [ecc_top.h](../../../../../../0_LDPC_original/src/ecc_top.h), [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp), [common.h](../../../../../../0_LDPC_original/src/common.h)

용어: BF는 Bit Flipping(1bit precision 복호 모드), SW는 Syndrome Weight(신드롬 무게), CSW는 Check Sum Weight, AUTO 빌드는 `__AUTO_LLR_OPT__`가 정의된 빌드, 비AUTO 빌드는 정의되지 않은 빌드다.

---

## 1. 가설 형식화

### R2-2 사실 가설
`Decoder::Clear_Flag`가 `flag_HD_1_4_Set`과 `flag_HD_5_8_Set`에 대입하는데 code_diff 2.2가 두 멤버를 `decoder.h`에서 지우고 그 자리의 수정 후 코드를 code_diff 어느 장도 제시하지 않아, 전 장을 적용해도 AUTO 빌드와 비AUTO 빌드가 모두 컴파일되지 않는다.

### R2-2 처방 가설
`Clear_Flag`의 두 줄을 지우고 그 자리에 `cur_sw_branch_idx[]`를 0으로 채우는 반복문을 넣으면 ㉮ 컴파일 실패가 사라지고 ㉯ R2-4 ㉯의 미초기화도 함께 사라지며 ㉰ 최종 상태에서 `Select_BF` 앞머리 초기화와 중복되어도 해가 없다.

### R2-4 사실 가설
- ㉮ code_diff 9장 1단계(1장, 2장)만 적용하면 지워지는 이름의 대체 코드가 3.3과 4.1에 흩어져 있어 빌드가 깨진다.
- ㉯ 9장 3단계의 전제 "`cur_sw_branch_idx[]`가 모두 0"이 거짓이다.
- ㉰ `cur_sw_branch_idx[]`가 0이어도 3단계 검증 기준("기존 동작과 결과가 같아야 한다")이 뒤집힌다.

### R2-4 처방 가설
1단계를 1.1, 2장, 3.3, 4.1을 함께 넣는 것으로 고치거나 2.2의 멤버 삭제를 4단계로 미루고, 3단계 검증을 "분기 줄이 모두 -1인 파일로 기존 결과와 비교"로 다시 쓰면 각 단계가 빌드되고 검증 기준이 성립하며 새 문제가 생기지 않는다.

---

## 2. 증거 판정

### E2-1 `Clear_Flag` 전체와 호출처 — **확인됨**

[decoder.cpp:606-616](../../../../../../0_LDPC_original/src/decoder.cpp#L606-L616) 전문이다.

```cpp
void Decoder::Clear_Flag()
{
    real_mn = 0;
    flag_BF_on = FLAG_LOW;
    flag_dec_1iter = FLAG_LOW;
    //flag_HBF_HD_SMN = FLAG_LOW;
    flag_HD_1_4_Set = FLAG_LOW;
    flag_HD_5_8_Set = FLAG_LOW;
    state_hd_error_floor_set = FLAG_HD_FLOOR_TYPE_0;
    cnt_hd_error_floor = 0;
}
```

612행과 613행이 두 멤버에 대입한다. 컴파일 스위치 가드가 전혀 없어 AUTO 빌드와 비AUTO 빌드 양쪽에 들어간다.

`Clear_Flag` 전수 참조는 셋뿐이다.

| 파일:줄 | 성격 |
|---------|------|
| [decoder.cpp:606](../../../../../../0_LDPC_original/src/decoder.cpp#L606) | 정의 |
| [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp#L1091) | 호출 (`Decoder::LDPC_Decoder` 안, 메인 루프 진입 직전) |
| [decoder.h:130](../../../../../../0_LDPC_original/src/decoder.h#L130) | 선언 |

`LDPC_Decoder`는 [decoder.cpp:999](../../../../../../0_LDPC_original/src/decoder.cpp#L999)에서 시작하고, 메인 루프는 [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp#L1120)의 `for (mn = 0; mn < MN + 1; mn++)`이다.

### E2-2 두 멤버의 전수 히트와 장별 대조 — **확인됨**

`flag_HD_1_4_Set`과 `flag_HD_5_8_Set`의 저장소 `src/` 전수 히트는 14곳이다.

| 파일:줄 | 이름 | 컴파일 갈래 | code_diff 대응 |
|---------|------|------------|---------------|
| [decoder.h:297](../../../../../../0_LDPC_original/src/decoder.h#L297) | `flag_HD_1_4_Set` 선언 | 양쪽 | 2.2가 삭제 |
| [decoder.h:298](../../../../../../0_LDPC_original/src/decoder.h#L298) | `flag_HD_5_8_Set` 선언 | 양쪽 | 2.2가 삭제 |
| [decoder.cpp:612](../../../../../../0_LDPC_original/src/decoder.cpp#L612) | 대입 | 양쪽 | **없음** |
| [decoder.cpp:613](../../../../../../0_LDPC_original/src/decoder.cpp#L613) | 대입 | 양쪽 | **없음** |
| [decoder.cpp:2090](../../../../../../0_LDPC_original/src/decoder.cpp#L2090) | 대입 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:2091](../../../../../../0_LDPC_original/src/decoder.cpp#L2091) | 대입 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:2100](../../../../../../0_LDPC_original/src/decoder.cpp#L2100) | 대입 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:2106](../../../../../../0_LDPC_original/src/decoder.cpp#L2106) | 대입 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:2117](../../../../../../0_LDPC_original/src/decoder.cpp#L2117) | 대입 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:2123](../../../../../../0_LDPC_original/src/decoder.cpp#L2123) | 대입 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:7002](../../../../../../0_LDPC_original/src/decoder.cpp#L7002) | 비교 | 비AUTO만 | 6.1이 삭제 |
| [decoder.cpp:7006](../../../../../../0_LDPC_original/src/decoder.cpp#L7006) | 비교 | 비AUTO만 | 6.1이 삭제 |
| [decoder.cpp:7010](../../../../../../0_LDPC_original/src/decoder.cpp#L7010) | 비교 | 비AUTO만 | 6.1이 삭제 |
| [decoder.cpp:7016](../../../../../../0_LDPC_original/src/decoder.cpp#L7016) | 비교 | 비AUTO만 | 6.1이 삭제 |

7001-7020의 비AUTO 갈래가 6장에서 삭제되는지 따로 확인했다. code_diff 6.1의 수정 전 블록(code_diff.md:637-672)이 `#else`부터 `#endif // __AUTO_LLR_OPT__`까지를 그대로 담고 있고 수정 후 블록(code_diff.md:677-711)에는 `#if` 지시자 자체가 없다. 곧 비AUTO 갈래 전체가 삭제된다. **확인됨**

다만 6.1의 제목은 "6973-6999행"인데 실제 교체 범위는 6973-7047이다. 제목의 줄 범위가 실제보다 좁게 적혀 있다 (문서 정확성 지적, 빌드에는 영향 없음).

code_diff가 다루지 않는 히트는 **612와 613 두 줄뿐**이다. Round 2의 주장과 일치한다.

### E2-3 2.2가 지우는 멤버와 더하는 멤버 — **확인됨**

code_diff 2.2(code_diff.md:140-174)의 수정 전과 수정 후를 대조했다.

지워지는 이름: `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1` (여섯 개).
남는 이름: `flag_BF_on`, `syn_weight`, `psyn_weight`, `syn_th_BF0`.
더해지는 이름: `cur_sw_branch_idx[MAX_SW_SPAN]`, `num_sw_branch[MAX_SW_SPAN]`, `syn_th_sw_branch[MAX_SW_SPAN][MAX_SW_BRANCH - 1]` (세 개).

2.2의 제목 "decoder.h 296-306행"은 실제 [decoder.h:296-306](../../../../../../0_LDPC_original/src/decoder.h#L296-L306)과 정확히 일치한다.

`MAX_SW_SPAN`과 `MAX_SW_BRANCH`는 1.1이 `common.h`에 넣고, [decoder.h:4](../../../../../../0_LDPC_original/src/decoder.h#L4)가 `common.h`를 포함하므로 2.2의 새 선언은 1장과 함께면 컴파일된다.

### E2-4 code_diff 전체에서 `Clear_Flag`를 다루는 장 — **확인됨 (없음)**

[code_diff.md](../../code_diff.md) 전체에 `Clear_Flag` 문자열이 0회 등장한다 (Grep 전수, 매치 없음). 어느 장도 이 함수를 다루지 않는다.

### E2-5 `cur_sw_branch_idx[]` 크기와 반복문 변수 — **확인됨**

㉮ 배열 크기는 `MAX_SW_SPAN`이고 1.1(code_diff.md:52)이 `#define MAX_SW_SPAN 4`로 정한다.
㉯ [decoder.cpp:606-616](../../../../../../0_LDPC_original/src/decoder.cpp#L606-L616) 전체에 지역 변수 선언이 하나도 없다. 처방의 반복문은 자기 변수를 직접 선언해야 한다 (`for (int i = 0; i < MAX_SW_SPAN; i++)`). C++ 소스이므로 for 초기화절 선언이 가능하고, `decoder.cpp`가 `Decoder.h`를 통해 `common.h`를 끌어오므로 `MAX_SW_SPAN`이 보인다. 처방 적용에 걸림돌이 없다.

### E2-6 최종 상태에서 `Select_BF`의 앞머리 초기화와 호출 보장 — **확인됨**

㉮ code_diff 5.1의 수정 후 `Select_BF`는 함수 앞머리에서 `for (int i = 0; i < MAX_SW_SPAN; i++) cur_sw_branch_idx[i] = 0;`을 돌린다 (code_diff.md:554-556).

㉯ 호출 지점은 [decoder.cpp:1968-1970](../../../../../../0_LDPC_original/src/decoder.cpp#L1968-L1970)이다.

```cpp
        /* HBF algorithm (Part 1) */
        if (mn == 0) {
            Select_BF();
        }
    }// end for loop (mn)
```

메인 루프 몸통의 끝이고 `mn == 0`일 때만 돈다.

㉰ `Select_BF`가 불리지 않는 프레임 경로가 있는지 확인했다. 루프 몸통(1120-1971) 안에 `return` 문이 하나도 없고 `break`는 셋뿐이다.

| 줄 | 조건 | mn 0에서 도달 여부 |
|----|------|------------------|
| [decoder.cpp:1805](../../../../../../0_LDPC_original/src/decoder.cpp#L1805) | clk 루프 안 (1807에서 닫힘) | 안쪽 루프 탈출이라 무관 |
| [decoder.cpp:1957](../../../../../../0_LDPC_original/src/decoder.cpp#L1957) | `Check_End_Iter` | [decoder.cpp:1947-1949](../../../../../../0_LDPC_original/src/decoder.cpp#L1947-L1949)가 `mn == 0`을 else 갈래로 빼내므로 mn 0에서 실행되지 않음 |
| [decoder.cpp:1963](../../../../../../0_LDPC_original/src/decoder.cpp#L1963) | `Jump_Iter` | [decoder.cpp:506, 509](../../../../../../0_LDPC_original/src/decoder.cpp#L505-L510)가 `power_index`를 양쪽 갈래 모두 `MODE_POWER_STOPPING_OFF`로 고정하므로 실행되지 않음 |

곧 프레임마다 mn 0 회차가 끝날 때 `Select_BF`가 반드시 불린다. 최종 상태에서 `Clear_Flag`의 0 채우기는 순수 중복이다.

㉱ 중복의 해로움: `Get_Cur_LLR_Idx_FILE`을 부르는 유일한 지점 [decoder.cpp:1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp#L1136-L1142)가 `mn > 0` 가드 안에 있어, 배열을 읽는 시점은 언제나 `Select_BF`가 값을 세운 뒤다. 두 번 0으로 채워도 읽히는 값이 달라지지 않는다. **해 없음**

### E2-7 `Clear_Flag`와 `Select_BF`의 순서 — **확인됨**

한 프레임의 순서는 다음과 같다.

- ㉮ [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp#L1091) `Clear_Flag()`
- ㉯ [decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp#L1120) 메인 루프 진입, mn = 0
- ㉰ [decoder.cpp:1136-1142](../../../../../../0_LDPC_original/src/decoder.cpp#L1136-L1142) `mn > 0`이 거짓이라 `Get_Cur_LLR_Idx_FILE` 미호출
- ㉱ [decoder.cpp:1969](../../../../../../0_LDPC_original/src/decoder.cpp#L1969) `Select_BF()`
- ㉲ mn = 1 이후 회차에서 비로소 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp#L1138) `Get_Cur_LLR_Idx_FILE(mn)` 호출

`Clear_Flag`가 `Select_BF`보다 먼저이고, 둘 다 배열을 읽는 지점보다 먼저다. 순서가 처방의 유효성을 해치지 않고 오히려 뒷받침한다. `Select_BF`를 아직 고치지 않은 중간 단계(3단계)에서도 `Clear_Flag`의 0 채우기만으로 배열이 0으로 보장된다.

### E2-8 `floor_flag` 전수 히트와 3.3 대응 — **확인됨**

전수 히트는 넷이다.

| 파일:줄 | 성격 | code_diff 대응 |
|---------|------|---------------|
| [ecc_data.h:197](../../../../../../0_LDPC_original/src/ecc_data.h#L197) | `PARAM_LLR` 멤버 선언 | 2.1이 `sw_branch_idx`로 개명 |
| [local_opt.cpp:105](../../../../../../0_LDPC_original/src/local_opt.cpp#L105) | 배열 할당 | 3.3이 코드 블록으로 제시 |
| [local_opt.cpp:114](../../../../../../0_LDPC_original/src/local_opt.cpp#L114) | 파일 읽기 | 3.3이 코드 블록으로 제시 |
| [local_opt.cpp:178](../../../../../../0_LDPC_original/src/local_opt.cpp#L178) | 로그 출력 | 3.3이 **산문으로만** 다룸 |

Round 2가 든 세 줄(105, 114, 178)이 맞다. 178행은 code_diff.md:291의 한 문장("178행의 로그 출력도 같은 이름으로 바꾼다")뿐이고 수정 후 코드 블록이 없다. `local_opt.cpp`에는 `__AUTO_LLR_OPT__` 가드가 없으므로 세 줄 모두 양쪽 빌드에 들어간다.

### E2-9 문턱 낱개 변수 전수 히트와 4.1 대응 — **확인됨**

주석이 아닌 실코드 히트만 추렸다.

| 파일:줄 | 이름 | 컴파일 갈래 | code_diff 대응 |
|---------|------|------------|---------------|
| [decoder.h:301](../../../../../../0_LDPC_original/src/decoder.h#L301) | `syn_th_BF` 선언 | 양쪽 | 2.2가 삭제 |
| [decoder.h:303](../../../../../../0_LDPC_original/src/decoder.h#L303) | `syn_th_BF1` 선언 | 양쪽 | 2.2가 삭제 |
| [decoder.h:305](../../../../../../0_LDPC_original/src/decoder.h#L305) | `syn_th_5_8_Set_0` 선언 | 양쪽 | 2.2가 삭제 |
| [decoder.h:306](../../../../../../0_LDPC_original/src/decoder.h#L306) | `syn_th_5_8_Set_1` 선언 | 양쪽 | 2.2가 삭제 |
| [decoder.cpp:468](../../../../../../0_LDPC_original/src/decoder.cpp#L468) | `syn_th_BF1` 대입 | 양쪽 | 4.1이 대체 |
| [decoder.cpp:472](../../../../../../0_LDPC_original/src/decoder.cpp#L472) | `syn_th_BF` 대입 | 양쪽 | 4.1이 대체 |
| [decoder.cpp:480](../../../../../../0_LDPC_original/src/decoder.cpp#L480) | `syn_th_5_8_Set_0` 대입 | 양쪽 | 4.1이 대체 |
| [decoder.cpp:483](../../../../../../0_LDPC_original/src/decoder.cpp#L483) | `syn_th_5_8_Set_0` 대입 | 양쪽 | 4.1이 대체 |
| [decoder.cpp:489](../../../../../../0_LDPC_original/src/decoder.cpp#L489) | `syn_th_5_8_Set_1` 대입 | 양쪽 | 4.1이 대체 |
| [decoder.cpp:492](../../../../../../0_LDPC_original/src/decoder.cpp#L492) | `syn_th_5_8_Set_1` 대입 | 양쪽 | 4.1이 대체 |
| [decoder.cpp:2099](../../../../../../0_LDPC_original/src/decoder.cpp#L2099) | `syn_th_5_8_Set_0` 읽기 | 비AUTO만 | 5.1이 삭제 |
| [decoder.cpp:2116](../../../../../../0_LDPC_original/src/decoder.cpp#L2116) | `syn_th_5_8_Set_0` 읽기 | 비AUTO만 | 5.1이 삭제 |

Round 2가 든 여섯 줄(468, 472, 480, 483, 489, 492)이 맞고 모두 4.1의 교체 범위(459-493) 안에 든다. 4.1의 수정 후가 쓰는 반복문 변수 `i`는 [decoder.cpp:454](../../../../../../0_LDPC_original/src/decoder.cpp#L454)의 `int i;`가 이미 제공한다.

다만 4.1의 수정 전 블록은 주석 처리된 case 줄들(460-465, 469, 477-479, 481-482, 486-488, 490-491)을 생략한 정리본이다. 소스 원문과 글자 그대로 일치하지 않는다 (문서 정확성 지적).

Round 2 목록에 **빠진 두 줄이 2099와 2116**이다. 비AUTO 빌드에서만 컴파일되지만, 2.2가 `syn_th_5_8_Set_0`을 지우므로 1단계 직후 비AUTO 빌드가 여기서도 깨진다.

### E2-10 9장 1단계에서 5단계까지의 원문과 장 대응 — **확인됨**

code_diff.md:997-1006 원문이다.

```
- 1. 1장과 2장(상수, 구조체)을 먼저 넣는다. 빌드가 깨지는 곳이 이름 변경 지점이다
- 2. 3장(파일 읽기)을 넣고, 대조 검사(3.4장)로 파일이 제대로 읽히는지 본다
- 3. 6장(그룹 선택)을 넣는다. 이 단계까지는 `Select_BF`가 그대로라
     `cur_sw_branch_idx[]`가 모두 0이므로 분기 0만 쓰인다.
     기존 동작과 결과가 같아야 한다
- 4. 4장과 5장(문턱, 분기 결정)을 넣는다. 여기서 분기가 실제로 갈리기 시작한다
- 5. 1.2장, 7장, 8장(`ITER_MAX_HBF`와 딸린 곳)을 넣는다. BF가 살아난다
```

| 단계 | 넣는 장 |
|------|--------|
| 1 | 1장(1.1, 1.2), 2장(2.1, 2.2, 2.3) |
| 2 | 3장(3.1 ~ 3.7) |
| 3 | 6장(6.1, 6.2) |
| 4 | 4장(4.1), 5장(5.1) |
| 5 | 1.2장, 7장, 8장 |

1단계가 "1장과 2장"인 것이 맞다. **추가 발견**: 1.2장이 1단계(1장 전체)와 5단계(명시적으로 "1.2장") 양쪽에 들어 있다. 같은 장이 두 단계에 배정된 모순이다. 1.2가 1단계에 들어가면 `ITER_MAX_HBF`가 1단계부터 4가 되어 [local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp#L124-L131)의 `MN[i] -= ITER_MAX_HBF`가 곧바로 살아나고 3단계의 "기존 동작과 결과가 같아야 한다"가 그 자체로 성립할 수 없게 된다.

### E2-11 1단계 직후 깨지는 줄 — **부분 확인 (AUTO는 정확, 비AUTO는 Round 2 목록이 불완전)**

**AUTO 빌드** (Round 2 목록과 정확히 일치, 총 11줄):

| 파일:줄 | 깨지는 이름 |
|---------|-----------|
| [local_opt.cpp:105](../../../../../../0_LDPC_original/src/local_opt.cpp#L105) | `floor_flag` |
| [local_opt.cpp:114](../../../../../../0_LDPC_original/src/local_opt.cpp#L114) | `floor_flag` |
| [local_opt.cpp:178](../../../../../../0_LDPC_original/src/local_opt.cpp#L178) | `floor_flag` |
| [decoder.cpp:468](../../../../../../0_LDPC_original/src/decoder.cpp#L468) | `syn_th_BF1` |
| [decoder.cpp:472](../../../../../../0_LDPC_original/src/decoder.cpp#L472) | `syn_th_BF` |
| [decoder.cpp:480](../../../../../../0_LDPC_original/src/decoder.cpp#L480) | `syn_th_5_8_Set_0` |
| [decoder.cpp:483](../../../../../../0_LDPC_original/src/decoder.cpp#L483) | `syn_th_5_8_Set_0` |
| [decoder.cpp:489](../../../../../../0_LDPC_original/src/decoder.cpp#L489) | `syn_th_5_8_Set_1` |
| [decoder.cpp:492](../../../../../../0_LDPC_original/src/decoder.cpp#L492) | `syn_th_5_8_Set_1` |
| [decoder.cpp:612](../../../../../../0_LDPC_original/src/decoder.cpp#L612) | `flag_HD_1_4_Set` |
| [decoder.cpp:613](../../../../../../0_LDPC_original/src/decoder.cpp#L613) | `flag_HD_5_8_Set` |

과장된 줄은 없다.

**비AUTO 빌드**: 위 11줄에 더해 12줄이 깨진다. Round 2 목록에 없는 부분이다.

| 파일:줄 | 깨지는 이름 | 대응 장 |
|---------|-----------|--------|
| [decoder.cpp:2090](../../../../../../0_LDPC_original/src/decoder.cpp#L2090) | `flag_HD_1_4_Set` | 5.1 (4단계) |
| [decoder.cpp:2091](../../../../../../0_LDPC_original/src/decoder.cpp#L2091) | `flag_HD_5_8_Set` | 5.1 (4단계) |
| [decoder.cpp:2099](../../../../../../0_LDPC_original/src/decoder.cpp#L2099) | `syn_th_5_8_Set_0` | 5.1 (4단계) |
| [decoder.cpp:2100](../../../../../../0_LDPC_original/src/decoder.cpp#L2100) | `flag_HD_5_8_Set` | 5.1 (4단계) |
| [decoder.cpp:2106](../../../../../../0_LDPC_original/src/decoder.cpp#L2106) | `flag_HD_5_8_Set` | 5.1 (4단계) |
| [decoder.cpp:2116](../../../../../../0_LDPC_original/src/decoder.cpp#L2116) | `syn_th_5_8_Set_0` | 5.1 (4단계) |
| [decoder.cpp:2117](../../../../../../0_LDPC_original/src/decoder.cpp#L2117) | `flag_HD_5_8_Set` | 5.1 (4단계) |
| [decoder.cpp:2123](../../../../../../0_LDPC_original/src/decoder.cpp#L2123) | `flag_HD_5_8_Set` | 5.1 (4단계) |
| [decoder.cpp:7002](../../../../../../0_LDPC_original/src/decoder.cpp#L7002) | `flag_HD_1_4_Set` | 6.1 (3단계) |
| [decoder.cpp:7006](../../../../../../0_LDPC_original/src/decoder.cpp#L7006) | `flag_HD_1_4_Set` | 6.1 (3단계) |
| [decoder.cpp:7010](../../../../../../0_LDPC_original/src/decoder.cpp#L7010) | `flag_HD_5_8_Set` | 6.1 (3단계) |
| [decoder.cpp:7016](../../../../../../0_LDPC_original/src/decoder.cpp#L7016) | `flag_HD_5_8_Set` | 6.1 (3단계) |

### E2-12 2단계와 3단계 이후 남는 깨진 줄 — **확인됨**

**2단계(3장 적용) 이후**

- AUTO: `decoder.cpp` 468, 472, 480, 483, 489, 492, 612, 613 (8줄). `local_opt.cpp` 세 줄은 3.3이 수리 (178행은 산문 지시).
- 비AUTO: 위 8줄에 2090, 2091, 2099, 2100, 2106, 2116, 2117, 2123, 7002, 7006, 7010, 7016 (총 20줄).

**3단계(6장 적용) 이후**

- AUTO: `decoder.cpp` 468, 472, 480, 483, 489, 492, 612, 613 (8줄, 변화 없음). 6장은 AUTO 갈래만 건드리므로 AUTO 빌드의 깨진 줄을 하나도 줄이지 못한다.
- 비AUTO: 위 8줄에 2090, 2091, 2099, 2100, 2106, 2116, 2117, 2123 (총 16줄). 6.1이 7002-7016 네 줄을 수리한다.

**4단계(4장, 5장 적용) 이후**

- 양쪽 빌드 모두 [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp#L612-L613)만 남는다. 이것이 R2-2다. 곧 9장 전 단계를 순서대로 밟아도 마지막까지 빌드되지 않는다.

### E2-13 `Decoder` 객체의 생성 경로 — **확인됨**

[ecc_top.h:97](../../../../../../0_LDPC_original/src/ecc_top.h#L97)이 `Decoder m_dec;`로 값 멤버를 둔다. 포인터가 아니다.

`new ECC_Top()` 호출은 셋이다.

| 파일:줄 | 경로 |
|---------|------|
| [local_opt.cpp:45](../../../../../../0_LDPC_original/src/local_opt.cpp#L45) | `LOCAL_OPT::Run_Simu_Curr_LLR`, AUTO 빌드가 쓰는 경로 |
| [main.cpp:104](../../../../../../0_LDPC_original/src/main.cpp#L104) | 진입점 |
| [main.cpp:126](../../../../../../0_LDPC_original/src/main.cpp#L126) | 진입점 |

### E2-14 `Decoder` 생성자와 `Initialize_Dec` — **확인됨**

[decoder.cpp:5-8](../../../../../../0_LDPC_original/src/decoder.cpp#L5-L8)의 생성자는 `Initialize_Dec()` 호출 한 줄이 전부다.

[decoder.cpp:19-113](../../../../../../0_LDPC_original/src/decoder.cpp#L19-L113)의 `Initialize_Dec`는 모든 줄이 포인터 멤버에 `NULL`을 넣는 대입이고, `NULL` 대입이 아닌 문장은 [decoder.cpp:108](../../../../../../0_LDPC_original/src/decoder.cpp#L108)의 `m_TV_cycle_based_on = TRUE;` 하나뿐이다. 값 멤버 배열이나 int 멤버를 0으로 채우는 코드가 **없다**.

곧 `cur_sw_branch_idx[]`를 새로 넣어도 어느 생성 경로도 그 배열을 0으로 만들지 않는다.

### E2-15 `new ECC_Top()`의 초기화 성격 — **확인됨**

[ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp#L6-L34)의 `ECC_Top::ECC_Top()`은 본문이 있는 사용자 제공 기본 생성자(user-provided default constructor)다.

C++ 표준 근거는 `[dcl.init]`의 값 초기화(value initialization) 규정이다. `T`가 클래스 타입이고 그 기본 생성자가 사용자 제공이면 값 초기화는 곧 기본 초기화(default initialization)이며, 객체 저장 공간을 0으로 미리 채우는 단계(zero-initialization)가 일어나지 않는다. `new ECC_Top()`의 괄호가 값 초기화를 요청해도 이 규칙 때문에 0 채우기가 생략된다.

따라서 순서는 다음과 같다.

- ㉮ `new ECC_Top()` → `ECC_Top::ECC_Top()` 실행 (0 채우기 없음)
- ㉯ 값 멤버 `m_dec`가 기본 초기화되어 `Decoder::Decoder()` 실행
- ㉰ `Initialize_Dec()`가 포인터만 `NULL`로 둠 (E2-14)
- ㉱ `cur_sw_branch_idx[]`는 값이 정해지지 않은 상태로 남음

R2-4 ㉯의 사실 주장이 코드와 표준 양쪽에서 확인된다.

### E2-16 `cur_sw_branch_idx[]`를 채우는 곳 — **확인됨 (5.1뿐)**

[code_diff.md](../../code_diff.md) 전체에서 `cur_sw_branch_idx`의 히트는 11곳이다.

| 줄 | 성격 | 장 |
|----|------|-----|
| 25 | 이름 표 | 머리말 |
| 166 | 선언 | 2.2 |
| 171 | 산문 | 2.2 |
| 555 | **쓰기** (0 채우기) | 5.1 |
| 561 | **쓰기** | 5.1 |
| 562 | **쓰기** | 5.1 |
| 569 | **쓰기** | 5.1 |
| 576 | **쓰기** | 5.1 |
| 582 | 읽기 (Corner 이벤트) | 5.1 |
| 693 | 읽기 (분기 대조) | 6.1 |
| 768 | 읽기 (오류 출력) | 6.2 |

쓰기는 전부 5.1(4단계) 안에 있다. 3단계에는 이 배열에 값을 넣는 코드가 하나도 없다.

### E2-17 처방 적용 시 3단계 보장 — **확인됨**

`Clear_Flag`에 0 채우기를 넣으면 프레임마다 [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp#L1091)에서 배열이 0이 된다. 그 뒤 3단계의 `Select_BF`는 아직 옛 코드이므로 배열을 건드리지 않고(AUTO 갈래는 [decoder.cpp:2085](../../../../../../0_LDPC_original/src/decoder.cpp#L2085) 한 줄), 배열을 읽는 유일한 지점인 6.1의 분기 대조는 [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp#L1138) 호출을 통해서만 도달한다. 1091이 1138보다 먼저이고 1138은 `mn > 0`에서만 돈다 (E2-7).

곧 처방을 적용하면 3단계에서 배열이 모두 0으로 **보장된다**. R2-4 ㉯의 미초기화가 R2-2의 처방으로 함께 해결된다.

### E2-18 변환된 파일의 그룹별 iteration 범위와 분기 index — **확인됨**

[LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)를 [local_opt.cpp:61-115](../../../../../../0_LDPC_original/src/local_opt.cpp#L61-L115)의 토큰 순서로 풀었다.

머리 값: `num_para_each_set` 4, `num_dv` 4, `num_col` 16, `num_group` 12, `num_set_each_group` = 1 7 6 6 1 5 5 7 6 10 10 13, `num_row` = 77, `restart_num` 0.

상위 문서 4장 ㉮의 변환을 적용하면 `type_each_group` 줄이 `1 1 1 1 1 1 1 1 1 1 1 1`이 되고 분기 전용 줄 `0 0 1 0 1 1 -1 -1 -1 -1 -1 -1`이 새로 들어간다.

| 그룹 | row 범위 (전역 index) | `iter_start[start_idx]` | `iter_end[end_idx]` | 분기 index | 3.2가 계산하는 구간 번호 |
|------|---------------------|------------------------|--------------------|-----------|----------------------|
| 0 | 0 | 1 | 1 | 0 | 0 |
| 1 | 1 ~ 7 | 2 | 4 | 0 | 0 |
| 2 | 8 ~ 13 | 1 | 4 | 1 | 0 |
| 3 | 14 ~ 19 | 5 | 8 | 0 | 1 |
| 4 | 20 | 5 | 5 | 1 | 1 |
| 5 | 21 ~ 25 | 6 | 8 | 1 | 1 |
| 6 | 26 ~ 30 | 9 | 24 | -1 | -1 |
| 7 | 31 ~ 37 | 25 | 44 | -1 | -1 |
| 8 | 38 ~ 43 | 45 | 64 | -1 | -1 |
| 9 | 44 ~ 53 | 65 | 84 | -1 | -1 |
| 10 | 54 ~ 63 | 85 | 104 | -1 | -1 |
| 11 | 64 ~ 76 | 105 | 124 | -1 | -1 |

3.2의 구간 계산을 손으로 돌린 값이다 (`prev_branch` 초기값 `SW_BRANCH_NONE`).

| i | b | `b == 0 && prev != 0` | `num_sw_span` | `sw_span_idx_each_group[i]` | 다음 `prev` |
|---|---|---------------------|--------------|---------------------------|-----------|
| 0 | 0 | 참 (prev = -1) | 0 → 1 | 0 | 0 |
| 1 | 0 | 거짓 (prev = 0) | 1 | 0 | 0 |
| 2 | 1 | 거짓 | 1 | 0 | 1 |
| 3 | 0 | 참 (prev = 1) | 1 → 2 | 1 | 0 |
| 4 | 1 | 거짓 | 2 | 1 | 1 |
| 5 | 1 | 거짓 | 2 | 1 | 1 |
| 6 ~ 11 | -1 | 해당 없음 | 2 | -1 | -1 |

최종 `num_sw_span` = 2. code_diff 3.2의 표(code_diff.md:261-267)와 일치한다.

### E2-19 옛 AUTO 루프 손 실행 — **확인됨**

[decoder.cpp:6985-6999](../../../../../../0_LDPC_original/src/decoder.cpp#L6985-L6999)의 루프다. `g`를 11에서 0으로 내리며 처음 맞는 그룹에서 `break`한다. 비교식은 `(iter >= iter_start[start_idx]) && (iter <= iter_end[end_idx])`이고, 각 그룹의 구간은 E2-18 표와 같다.

| iter | 훑은 순서와 판정 | 선택 그룹 |
|------|----------------|----------|
| 1 | g11 [105,124] 거짓, g10 [85,104] 거짓, g9 [65,84] 거짓, g8 [45,64] 거짓, g7 [25,44] 거짓, g6 [9,24] 거짓, g5 [6,8] 거짓, g4 [5,5] 거짓, g3 [5,8] 거짓, **g2 [1,4] 참** | 2 |
| 2 | g11 ~ g3 거짓, **g2 [1,4] 참** (g1 [2,4]도 참이지만 g2에서 먼저 break) | 2 |
| 3 | 같음 | 2 |
| 4 | 같음 | 2 |
| 5 | g11 ~ g6 거짓, g5 [6,8] 거짓, **g4 [5,5] 참** | 4 |
| 6 | g11 ~ g6 거짓, **g5 [6,8] 참** | 5 |
| 7 | 같음 | 5 |
| 8 | 같음 | 5 |

### E2-20 새 루프를 `cur_sw_branch_idx[]` 전부 0으로 손 실행 — **확인됨**

code_diff 6.1 수정 후(code_diff.md:688-710)의 루프다. 분기 대조가 먼저 걸린다.

`cur_sw_branch_idx[0] = 0`, `cur_sw_branch_idx[1] = 0`일 때 그룹별 통과 여부는 iteration과 무관하게 다음과 같다.

| 그룹 | 분기 index | 구간 | `group_branch != cur_sw_branch_idx[span]` | 후보 여부 |
|------|-----------|------|----------------------------------------|----------|
| 0 | 0 | 0 | 0 != 0 거짓 | 후보 |
| 1 | 0 | 0 | 거짓 | 후보 |
| 2 | 1 | 0 | 1 != 0 참 | `continue`로 제외 |
| 3 | 0 | 1 | 거짓 | 후보 |
| 4 | 1 | 1 | 참 | 제외 |
| 5 | 1 | 1 | 참 | 제외 |
| 6 ~ 11 | -1 | 해당 없음 | 대조 자체를 건너뜀 | 후보 |

| iter | 훑은 순서와 판정 | 선택 그룹 |
|------|----------------|----------|
| 1 | g11 ~ g6 범위 거짓, g5 제외, g4 제외, g3 [5,8] 거짓, g2 제외, g1 [2,4] 거짓, **g0 [1,1] 참** | 0 |
| 2 | g5 g4 g2 제외, g3 [5,8] 거짓, **g1 [2,4] 참** | 1 |
| 3 | 같음 | 1 |
| 4 | 같음 | 1 |
| 5 | g5 g4 제외, **g3 [5,8] 참** | 3 |
| 6 | 같음 | 3 |
| 7 | 같음 | 3 |
| 8 | 같음 | 3 |

### E2-21 두 결과의 차이와 Round 2 주장 대조 — **확인됨**

| iter | 옛 루프 | 새 루프 (분기 전부 0) | 같은가 |
|------|--------|---------------------|-------|
| 1 | 2 | 0 | 다름 |
| 2 | 2 | 1 | 다름 |
| 3 | 2 | 1 | 다름 |
| 4 | 2 | 1 | 다름 |
| 5 | 4 | 3 | 다름 |
| 6 | 5 | 3 | 다름 |
| 7 | 5 | 3 | 다름 |
| 8 | 5 | 3 | 다름 |

Round 2의 주장("옛 루프는 1~4에서 그룹 2, 5에서 그룹 4, 6~8에서 그룹 5, 새 루프는 그룹 0, 1, 3")이 **글자 그대로 맞다**.

**추가로 확인한 더 강한 사실**: 고른 row까지 다르다. 옛 코드는 현재 파일의 `type_each_group`이 20 또는 21이라 [decoder.cpp:7051](../../../../../../0_LDPC_original/src/decoder.cpp#L7051)의 `GROUP_TYPE_ITER`(0)도 [decoder.cpp:7059](../../../../../../0_LDPC_original/src/decoder.cpp#L7059)의 `GROUP_TYPE_CSW`(1)도 맞지 않아 `table_row_idx`가 [decoder.cpp:6974](../../../../../../0_LDPC_original/src/decoder.cpp#L6974)의 초기값 0에 머문 채 반환된다. 곧 iteration 1~8에서 언제나 전역 row 0을 쓴다. 새 코드는 변환된 파일의 `type_each_group`이 전부 1이므로 CSW 기반 row 선택이 실제로 돌아 iteration 2 이상에서 row 1~7 등을 고른다. 그룹과 row 양쪽이 달라진다.

### E2-22 대안 기준("분기 줄이 모두 -1인 파일")의 성립 — **부분 확인 (조건을 더 달아야 성립)**

㉮ 분기 줄이 모두 -1이면 6.1의 대조가 모든 그룹에서 `group_branch != SW_BRANCH_NONE`을 거짓으로 만들어 `continue`가 한 번도 걸리지 않는다. 남는 코드는 옛 AUTO 루프와 훑는 방향, 범위 계산, 비교식이 글자 그대로 같다. 손 실행 결과도 같다.

| iter | 옛 루프 | 새 루프 (분기 전부 -1) |
|------|--------|---------------------|
| 1 ~ 4 | 2 | 2 |
| 5 | 4 | 4 |
| 6 ~ 8 | 5 | 5 |
| 9 이상 | 범위대로 | 같음 |

그룹 선택은 **일치한다**.

㉯ 그러나 그룹 선택만으로는 "기존 결과와 같다"가 성립하지 않는다. 세 조건을 더 달아야 한다.

- ㉠ 3단계 시점에는 2단계(3.2 파서)가 이미 들어가 있어 파일에 분기 전용 줄이 **반드시** 있어야 한다. 곧 3단계는 변환된 파일로만 돌릴 수 있다. 그런데 상위 문서 4장 ㉮의 변환은 분기 줄 추가와 `type_each_group` 교정(20, 21 → 1)을 함께 한다. 교정만으로도 iteration 1~8의 row 선택이 "전역 row 0 고정"에서 "그룹 안 CSW 선택"으로 바뀐다 (E2-21의 추가 사실). 따라서 비교 대상인 "기존 결과"를 **`type_each_group`만 교정하고 분기 줄은 넣지 않은 파일로 옛 코드를 돌린 결과**로 다시 정의해야 한다. 그 파일은 토큰 수가 옛 파서와 맞으므로 그대로 읽힌다.
- ㉡ 1.2장(`ITER_MAX_HBF` 0 → 4)이 3단계까지 들어가면 안 된다. [local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp#L124-L131)이 `MN[i] -= ITER_MAX_HBF`와 `MN[0] = ITER_MAX_HBF`를 돌려 iteration 수열 자체가 달라지기 때문이다. 9장 1단계의 "1장"에서 1.2를 빼야 한다 (E2-10의 모순).
- ㉢ 3.5장(최대 iteration 계산)은 이 파일에서 문제가 없다. 마지막 row의 `iter_end`가 124이고 전체 최댓값도 124라 `MN_num`이 같다.

㉰ 위 셋을 달면 3단계의 나머지 변경이 결과를 바꾸지 않는지도 확인했다. 6.1의 `table_row_idx` 초기값 0 → -1과 6.2의 오류 갈래 추가는, `type_each_group`이 전부 1(`GROUP_TYPE_CSW`)이면 [decoder.cpp:7060](../../../../../../0_LDPC_original/src/decoder.cpp#L7060)의 `table_row_idx = start_idx`가 언제나 먼저 실행되어 값이 음수로 남지 않는다. 반환값이 옛 코드와 같다.

곧 대안 기준은 **성립하되 위 세 조건을 문서에 함께 적어야** 한다.

### E2-23 옛 AUTO 루프를 현재 파일로 돌린 결과와 비교 기준 적합성 — **부분 확인 (상위 문서 서술이 과하게 일반화됨)**

㉮ 상위 문서 3장(20260902_SW_branch_LLR_matrix.md:83-85)은 "`20`, `21`을 넣으면 두 갈래 어디에도 걸리지 않는다 (중략) 결과는 오류 없이 항상 첫 번째 row의 파라미터를 쓰는 것이다"라고 적었다.

㉯ 코드로 확인한 사실은 다음과 같다. `type_each_group`이 20 또는 21인 그룹은 0 ~ 5뿐이고 이 그룹들이 덮는 iteration은 1 ~ 8이다. 그룹 6 ~ 11은 `type_each_group`이 1(`GROUP_TYPE_CSW`)이라 [decoder.cpp:7059-7068](../../../../../../0_LDPC_original/src/decoder.cpp#L7059-L7068)의 CSW 갈래가 정상으로 돈다. 곧 **iteration 1 ~ 8에서만** 전역 row 0으로 고정되고, iteration 9 ~ 124는 정상 동작한다. 상위 문서의 문장은 이 한정을 빠뜨렸다 (문서 정확성 지적).

㉰ 비교 기준 적합성 판정: **부적합**. 사유는 둘이다.

- ㉠ iteration 1 ~ 8 구간의 기존 결과가 "언제나 전역 row 0"이라는 퇴화한 값이라, 이 구간에서 무엇을 고르든 기존과 다를 수밖에 없다. 3단계 검증이 "달라야 정상"과 "같아야 정상"을 구별하지 못한다.
- ㉡ 3단계는 변환된 파일로만 돌릴 수 있는데(E2-22 ㉠), 변환에는 `type_each_group` 교정이 포함되어 이 퇴화가 곧바로 사라진다. 변환 전 파일로 돌린 옛 결과와 변환 후 파일로 돌린 새 결과는 그룹 선택 로직과 무관한 이유로 이미 다르다.

따라서 비교 기준은 `type_each_group`을 교정한 파일로 옛 코드를 돌린 결과여야 한다 (E2-22 ㉠과 같은 결론).

---

## 3. 판정

### R2-2

**㉮ 사실 가설 판정: 확인됨**

근거는 셋이다.

- ㉠ [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp#L612-L613)이 두 멤버에 대입하고 컴파일 스위치 가드가 없어 양쪽 빌드에 들어간다 (E2-1)
- ㉡ code_diff 2.2가 [decoder.h:297-298](../../../../../../0_LDPC_original/src/decoder.h#L297-L298)의 두 선언을 지운다 (E2-3)
- ㉢ [code_diff.md](../../code_diff.md) 전체에 `Clear_Flag` 문자열이 없고, 두 멤버의 다른 히트 12곳은 모두 2.2, 5.1, 6.1이 다룬다 (E2-2, E2-4)

전 장을 순서대로 적용해도 612-613이 남아 양쪽 빌드가 컴파일되지 않는다 (E2-12).

**㉯ 처방 판정: 처방 유효**

- ㉠ 컴파일 실패 해소: 지워진 이름의 대입을 없애므로 해결된다
- ㉡ R2-4 ㉯ 동시 해결: `Clear_Flag`가 프레임마다 [decoder.cpp:1091](../../../../../../0_LDPC_original/src/decoder.cpp#L1091)에서 불리고 배열을 읽는 유일한 지점([decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp#L1138))보다 앞서므로 3단계에서 0이 보장된다 (E2-7, E2-17)
- ㉢ 중복 무해: 최종 상태에서 `Select_BF`가 프레임마다 반드시 불리고(E2-6) 앞머리에서 같은 배열을 0으로 채우지만, 두 번 채워도 읽히는 값이 달라지지 않는다
- ㉣ 구현 걸림돌 없음: `Clear_Flag`에 지역 변수가 없어 반복문 변수를 새로 선언해야 하고, `MAX_SW_SPAN`은 `decoder.h`가 끌어오는 `common.h`에 있어 보인다 (E2-5)

한 가지 덧붙일 것이 있다. `Clear_Flag`의 0 채우기는 2.2가 `cur_sw_branch_idx[]`를 선언한 뒤에만 컴파일되므로, 이 수리는 2.2와 같은 단계에 들어가야 한다. code_diff에 "2.4 decoder.cpp 606-616행: `Clear_Flag`" 절을 새로 두고 9장에서 2장과 함께 적용하도록 적는 것이 명확하다.

**㉰ 심각도 재판정: HIGH 유지**

전 장을 적용해도 양쪽 빌드가 서지 않는 누락이라 계획 문서로서 완결되지 않았다. 다만 수리가 두 줄이고 처방이 이미 정확하므로 CRITICAL로 올릴 근거는 없다.

### R2-4 ㉮ (1단계 빌드 실패)

**㉮ 사실 가설 판정: 확인됨 (Round 2 목록은 AUTO 빌드 기준으로 정확, 비AUTO 빌드 기준으로 불완전)**

- ㉠ AUTO 빌드에서 1단계 직후 깨지는 줄은 `local_opt.cpp` 105, 114, 178과 `decoder.cpp` 468, 472, 480, 483, 489, 492, 612, 613으로 Round 2 목록과 정확히 일치한다. 과장된 줄이 없다 (E2-11)
- ㉡ 비AUTO 빌드에서는 여기에 `decoder.cpp` 2090, 2091, 2099, 2100, 2106, 2116, 2117, 2123, 7002, 7006, 7010, 7016 열두 줄이 더해진다. Round 2가 빠뜨린 부분이다 (E2-9, E2-11)
- ㉢ 대체 코드가 3.3(2단계)과 4.1(4단계)에 흩어져 있다는 지적도 맞다. 3단계까지 밟아도 AUTO 빌드의 깨진 줄이 8줄 그대로 남는다 (E2-12)

**㉯ 처방 판정: 처방 수정 필요**

Round 2의 처방은 두 갈래를 제시했다. 각각을 검증했다.

- ㉠ **갈래 하나("1단계를 1.1, 2장, 3.3, 4.1을 함께 넣는다"): 불충분**. 이대로면 AUTO 빌드는 [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp#L612-L613)이 남아 여전히 깨지고, 비AUTO 빌드는 2090 ~ 2123과 7002 ~ 7016까지 남아 크게 깨진다. 게다가 3.3만 떼어 오면 3.1(할당)과 3.2(파싱)가 빠져 `sw_branch_idx_each_group`이 할당되지 않은 채 남는다. 3.6(소멸자)까지 따라오면 초기화되지 않은 포인터를 `delete[]`하는 미정의 동작이 생긴다. 3.1, 3.2, 3.6은 떼어 쓸 수 없다.
- ㉡ **갈래 둘("2.2의 멤버 삭제를 4단계로 미룬다"): 유효**. 이쪽을 택하는 것이 옳다. 구체화하면 다음과 같다.

  1단계를 1.1, 2.1, 2.3, 그리고 2.2의 **추가분만**(`cur_sw_branch_idx[]`, `num_sw_branch[]`, `syn_th_sw_branch[][]` 선언)으로 한다. `flag_HD_1_4_Set`, `flag_HD_5_8_Set`, `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1`은 4단계까지 남긴다. 그러면 1단계에서 깨지는 것은 2.1의 `floor_flag` 개명이 부르는 `local_opt.cpp` 105, 114, 178 세 줄뿐이고, 3.3을 함께 넣으면 그마저 사라진다. 2단계, 3단계도 양쪽 빌드가 선다.

  4단계(4장, 5장)에 2.2의 삭제분과 R2-2의 `Clear_Flag` 수리를 함께 넣는다. 4장이 468 ~ 492를, 5장이 2090 ~ 2123을, 3단계에 이미 들어간 6장이 7002 ~ 7016을 치웠으므로 남는 참조가 없어 삭제가 안전하다.

  덧붙여 1.2장을 1단계에서 빼고 5단계에만 둔다 (E2-10의 모순 해소).

**㉰ 심각도 재판정: HIGH 유지**

계획대로 밟으면 첫 단계부터 빌드가 서지 않아 단계별 검증이라는 9장의 목적 자체가 무너진다. 비AUTO 빌드까지 세면 깨지는 줄이 23줄이라 Round 2가 본 것보다 넓다.

### R2-4 ㉯ (3단계 전제 "배열이 모두 0"이 거짓)

**㉮ 사실 가설 판정: 확인됨**

- ㉠ [ecc_top.h:97](../../../../../../0_LDPC_original/src/ecc_top.h#L97)이 `Decoder m_dec;`로 값 멤버를 둔다 (E2-13)
- ㉡ [ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp#L6-L34)의 `ECC_Top::ECC_Top()`이 사용자 제공 기본 생성자라 `new ECC_Top()`이 0 채우기를 하지 않는다 (E2-15)
- ㉢ [decoder.cpp:5-8](../../../../../../0_LDPC_original/src/decoder.cpp#L5-L8)의 생성자와 [decoder.cpp:19-113](../../../../../../0_LDPC_original/src/decoder.cpp#L19-L113)의 `Initialize_Dec`가 포인터에 `NULL`을 넣을 뿐 값 멤버 배열을 0으로 채우지 않는다 (E2-14)
- ㉣ code_diff에서 `cur_sw_branch_idx[]`에 값을 넣는 코드는 5.1(4단계)뿐이다 (E2-16)

3단계에서 배열은 값이 정해지지 않은 상태이고, 그 상태로 6.1이 `group_branch != cur_sw_branch_idx[span]`을 비교한다. 미정의 값 비교이므로 결과가 실행마다 달라질 수 있다.

**㉯ 처방 판정: 처방 유효 (R2-2의 처방이 이것을 함께 해결한다)**

별도 처방이 필요 없다. R2-2의 `Clear_Flag` 0 채우기를 2단계 이전에 넣으면 3단계에서 배열이 0으로 보장된다 (E2-17). 다만 R2-4 ㉮의 처방(2.2 삭제를 4단계로 미루기)을 택하면 `Clear_Flag`의 612-613 삭제도 4단계로 미뤄지므로, **0 채우기 추가만 1단계에 먼저 넣고 옛 두 줄 삭제는 4단계에 두는 두 토막 수리**로 적어야 한다. 곧 1단계의 `Clear_Flag`는 옛 두 줄과 새 반복문이 함께 있는 모습이 된다.

**㉰ 심각도 재판정: HIGH 유지**

미정의 값 비교라 3단계 검증 결과 자체를 믿을 수 없게 만든다.

### R2-4 ㉰ (배열이 0이어도 검증 기준이 뒤집힘)

**㉮ 사실 가설 판정: 확인됨**

손 실행으로 iteration 1 ~ 8 전 구간에서 옛 루프와 새 루프의 선택 그룹이 다름을 확인했다 (E2-19, E2-20, E2-21). Round 2가 든 값이 글자 그대로 맞다. 고르는 row까지 다르다는 것도 추가로 확인했다.

**㉯ 처방 판정: 처방 수정 필요**

"3단계 검증을 분기 줄이 모두 -1인 파일로 기존 결과와 비교하는 것으로 다시 쓴다"는 방향은 옳다. 분기 줄이 모두 -1이면 6.1의 대조가 한 번도 걸리지 않아 옛 AUTO 루프와 코드가 사실상 같아지고, 손 실행 결과도 iteration 전 구간에서 일치한다 (E2-22 ㉮).

그러나 그대로는 성립하지 않는다. 세 조건을 함께 적어야 한다.

- ㉠ 비교 대상인 "기존 결과"를 **`type_each_group`을 20, 21에서 0 또는 1로 교정하고 분기 줄은 넣지 않은 파일로 옛 코드를 돌린 결과**로 정의한다. 현재 파일 그대로 돌린 결과는 iteration 1 ~ 8이 전역 row 0으로 고정된 퇴화한 값이라 비교 기준이 될 수 없다 (E2-23)
- ㉡ 1.2장(`ITER_MAX_HBF` 0 → 4)을 3단계까지 넣지 않는다. 넣으면 [local_opt.cpp:124-131](../../../../../../0_LDPC_original/src/local_opt.cpp#L124-L131)이 `MN[]`을 통째로 밀어 iteration 수열이 달라진다 (E2-22 ㉡)
- ㉢ 비교에 쓰는 두 파일이 `type_each_group` 교정본과 그 위에 분기 줄 전부 -1을 얹은 것이라는 점, 곧 두 파일이 분기 줄 유무만 다르다는 점을 명시한다

이 셋을 달면 3단계에서 그룹 선택과 row 선택이 모두 일치해 "같아야 한다"가 실제 검증이 된다.

**㉰ 심각도 재판정: HIGH 유지**

세 가지 결함 중 실무 위험이 가장 크다. 검증 기준이 틀린 채로 진행하면 구현자가 정상 동작을 결함으로 오인해 되돌리거나, 반대로 깨진 상태를 통과로 판정한다. 코드 결함이 아니라 문서 결함이지만 계획 문서의 목적이 단계별 안전 확인이므로 HIGH가 맞다.

---

## 4. 검증 중 새로 확인한 것 (Round 2가 들지 않은 사항)

- ㉮ **9장 1.2장 이중 배정**: 1단계가 "1장과 2장"이라 1.2장을 포함하는데 5단계가 다시 "1.2장, 7장, 8장"이라고 적는다. 같은 장이 두 단계에 있다. 1.2가 1단계에 들면 3단계의 결과 비교가 그 자체로 성립하지 않는다 (E2-10)
- ㉯ **비AUTO 빌드의 1단계 추가 파손 12줄**: `decoder.cpp` 2090, 2091, 2099, 2100, 2106, 2116, 2117, 2123, 7002, 7006, 7010, 7016 (E2-11)
- ㉰ **3.1, 3.2, 3.6의 분리 불가**: 3.3만 앞 단계로 떼어 오면 `sw_branch_idx_each_group`이 할당 없이 남고, 3.6이 따라오면 초기화되지 않은 포인터 해제가 된다
- ㉱ **6.1 제목의 줄 범위 오기**: 제목은 "6973-6999행"이나 실제 교체 범위는 6973-7047이다 (비AUTO 갈래 포함)
- ㉲ **4.1 수정 전 블록의 원문 불일치**: 주석 처리된 case 줄들을 생략한 정리본이라 소스 원문과 글자 그대로 같지 않다
- ㉳ **상위 문서 3장의 과한 일반화**: "항상 첫 번째 row"는 `type_each_group`이 20 또는 21인 그룹이 덮는 iteration 1 ~ 8에만 해당하고, 그룹 6 ~ 11이 덮는 iteration 9 ~ 124는 CSW 갈래가 정상 동작한다 (E2-23)
