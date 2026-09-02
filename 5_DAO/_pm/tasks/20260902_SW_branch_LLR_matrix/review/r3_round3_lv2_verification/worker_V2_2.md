# Round 3 검증: 팀 V2 워커 2 (R2-9, R2-11)

작성: 2026-09-03 01:40:29

대상 발견: R2-9(구간별 분기 개수와 컴파일 상수 대조 없음), R2-11(분기 일치를 넣어도 순서 의존이 남음).
검증 방식: 소스 직접 읽기, Grep 전수, 손 실행. 코드와 문서는 수정하지 않았다.

---

## ㉮ 가설별 판정 요약

| 가설 | 내용 | 판정 |
|------|------|------|
| C (R2-9 사실) | default 갈래의 `num_sw_branch[0] = 1` 때문에 `matrix_sel`이 1이 아니면 iteration 1~4 구간의 분기 1 그룹(현 파일의 그룹 2)이 영영 후보가 되지 않고 오류도 없다 | **확인됨** |
| C 도달 경로 | AUTO 빌드에서 `argc > 19`이면 임의 `matrix_sel`이 통과한다 | **확인됨** (다만 DAO의 현재 설정은 `matrix_sel = 1`이라 실사용에서는 도달하지 않는다. 심각도 재판정 아래 참조) |
| C-처방1 (`PARAM_LLR`에 기록하고 `Init_Dec_Option` 끝에서 대조) | 문제가 해결되고 새 문제가 생기지 않는다 | **처방 수정 필요** (호출 순서는 성립하나, 멈추는 수단과 비AUTO 빌드 가드 두 가지를 보태야 한다) |
| C-처방2 (파서가 `num_sw_branch[]`를 직접 채운다) | 문제가 해결되고 새 문제가 생기지 않는다 | **처방 반대** (분기 3개 이상일 때 문턱 값의 출처가 코드에 없고, 침묵 오선택이 그대로 남는다) |
| D (R2-11 사실) | 후보 집합 안에서 iteration이 겹치면 그룹 index가 큰 쪽이 이긴다. 배치를 뒤집으면 결과가 바뀐다 | **확인됨** (두 배치 모두 손 실행으로 재현) |
| D 부가 주장 | 수정 전 AUTO 갈래도 같은 성질이므로 6.1이 새로 만든 결함이 아니다 | **확인됨** |
| D-처방 (문서에 전제 명기 + 파서에 범위 겹침 검사) | 문제가 해결되고 새 문제가 생기지 않는다 | **처방 유효** (검사 위치를 3.2가 아니라 3.4 자리로 잡아야 한다는 조건 붙음) |

### 심각도 재판정

- ㉮ R2-9: MEDIUM 유지가 타당하나 근거를 바꾼다. DAO는 [DAO_Config.py:170](../../../../../../5_DAO/SRC/DAO_Config.py)에서 `matrix_sel = 1`을 고정으로 넘기므로 default 갈래는 사용자가 설정을 직접 바꾸기 전에는 실행되지 않는다. 반면 `matrix_sel != 1`은 이 코드베이스 전반에서 애초에 지원되지 않는 값이다 (PCRC termination point도 [decoder.cpp:536-541](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `matrix_sel == 1`일 때만 채워지고 그 밖에는 미초기화로 남는다). 따라서 진짜 처방은 "분기 개수 대조"보다 "`matrix_sel` 값 자체를 검증해 지원하지 않는 값이면 멈추는 것"에 가깝다
- ㉯ R2-11: MEDIUM 유지. 새 결함이 아니고 현 파일에서는 겹침이 없으므로 문서 전제와 파서 검사로 충분하다

---

## ㉯ 확인과 손 실행

### 확인 1: 도달 경로 (가설 C)

**㉮ `main.cpp`의 `matrix_sel` 대입 전수 (Grep 히트)**

| 줄 | 내용 | 성격 |
|-----|------|------|
| [main.cpp:139](../../../../../../0_LDPC_original/src/main.cpp) | `g_ecc_info.matrix_sel = atoi(argv[1]);` (`Setup_Ref_C`) | 대입 |
| [main.cpp:499](../../../../../../0_LDPC_original/src/main.cpp) | `g_ecc_info.matrix_sel = atoi(argv[1]);` (`Setup_TV_Gen`) | 대입 |
| main.cpp:339-341 | 주석 처리된 옛 대입 | 주석 |
| main.cpp:145, 155, 274, 500, 509, 599, 618, 641, 679-693, 795 | 비교, 출력, 파일 이름 조립 | 읽기 |

대입은 두 곳뿐이고 둘 다 `atoi(argv[1])`이다. 검증 없이 그대로 들어간다.

**㉯ `Setup_Ref_C`의 AUTO 갈래 인용** ([main.cpp:139-153](../../../../../../0_LDPC_original/src/main.cpp))

```cpp
    g_ecc_info.matrix_sel = atoi(argv[1]);
#ifdef __AUTO_LLR_OPT__
    if (argc > 19) {
        Get_H_Filename(g_ecc_info.str_matrix_name, argv[19]);
    }
    else {
        if (LAYOUT_PRIME_512B_TLC_VSS_OFF == g_ecc_info.matrix_sel) { ... }
        else { err = TRUE; Print_Input_Err_Code(1); return err; }
    }
#else
    if (LAYOUT_PRIME_512B_TLC_VSS_OFF == g_ecc_info.matrix_sel) { ... }
    else { err = TRUE; Print_Input_Err_Code(1); return err; }
#endif
```

`argc > 19`이면 H matrix 이름을 `argv[19]`에서 가져오고 `matrix_sel` 검사를 건너뛴다. 즉 AUTO 빌드에서 `matrix_sel`은 값 검증 없이 통과한다. 확인됨.

**㉰ layout 상수** ([common.h:192-198](../../../../../../0_LDPC_original/src/common.h))

| 상수 | 값 | 상태 |
|------|-----|------|
| `LAYOUT_PRIME_512B_TLC_VSS_OFF` | 1 | 유일하게 살아 있는 정의 |
| `LAYOUT_PRIME_512B_TLC_VSS_ON` | 2 | 주석 |
| `LAYOUT_PRIME_520B_TLC_VSS_OFF` | 11 | 주석 |
| `LAYOUT_PRIME_520B_TLC_VSS_ON` | 12 | 주석 |
| `LAYOUT_PRIME_512B_QLC_VSS_OFF` | 3 | 주석 |
| `LAYOUT_PRIME_512B_QLC_VSS_ON` | 4 | 주석 |

살아 있는 값이 1 하나뿐이므로 `matrix_sel != 1`은 이름 붙은 어떤 layout도 아니다.

**㉱ DAO가 실제로 넘기는 인자**

- ㉠ [DAO_Config.py:169-189](../../../../../../5_DAO/SRC/DAO_Config.py): `ECC_VER = "3.0"`, `matrix_sel = 1`, `str_matrix_name = "H_402091"`
- ㉡ [DAO_Main.py:6434-6455](../../../../../../5_DAO/SRC/DAO_Main.py): `ECC_VER`가 "2.4"가 아니므로 else 갈래를 타고 18개 인자를 만든 뒤 `str_matrix_name`이 비어 있지 않으므로 19번째로 덧붙인다
- ㉢ [DAO_Main.py:6550-6555](../../../../../../5_DAO/SRC/DAO_Main.py): `command_line = f"{exe_command} {' '.join(arg_lst)}"` 로 배치 파일 한 줄을 쓴다. 실행 파일 이름이 `argv[0]`이므로 `argc = 20`
- ㉣ [DAO_Main.py:7937-7939](../../../../../../5_DAO/SRC/DAO_Main.py): 그 배치 파일을 `subprocess.run`으로 돌린다
- ㉤ `matrix_sel`을 다른 값으로 바꾸는 코드는 `5_DAO/SRC` 전체 Grep에서 없다 (히트는 모두 읽기이거나 파일 이름 조립)

**판정**: `argc = 20 > 19`이므로 AUTO 갈래의 검사 생략 경로를 실제로 탄다. 다만 `matrix_sel` 값은 1이므로 `Init_Dec_Option`의 default 갈래는 DAO의 현재 설정에서 실행되지 않는다. default 갈래는 사용자가 `DAO_Config.py`의 `matrix_sel`을 바꾸는 순간 도달한다. 도달 경로 존재는 확인됨, 현행 실행에서의 발생은 미발생.

### 확인 2: 호출 순서 (가설 C-처방1)

| 순번 | 위치 | 동작 |
|------|------|------|
| 1 | [local_opt.cpp:34](../../../../../../0_LDPC_original/src/local_opt.cpp) | `Read_LLR_info_Auto(&m_param_LLR, &m_param_OPT)` 로 파일을 읽어 `m_param_LLR`을 채운다 |
| 2 | [local_opt.cpp:38-44](../../../../../../0_LDPC_original/src/local_opt.cpp) | MPI 전파 (`LLR_MATRIX`, `CSW_thr`) |
| 3 | [local_opt.cpp:45-46](../../../../../../0_LDPC_original/src/local_opt.cpp) | `new ECC_Top()` 후 5인자 `Init_ECC_Top(..., &m_param_LLR, ...)` |
| 4 | [ecc_top.cpp:228](../../../../../../0_LDPC_original/src/ecc_top.cpp) | `m_dec.Init_Dec(m_ecc_info, &m_PCM, m_param_dec, m_param_LLR, m_my_rank)` 가 [decoder.cpp:436](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `m_param_LLR = param_LLR` |
| 5 | [ecc_top.cpp:229](../../../../../../0_LDPC_original/src/ecc_top.cpp) | `m_dec.Init_Dec_Option()` |

**판정**: `Init_Dec_Option`은 파서가 채운 뒤에 불리고 그 시점에 `m_param_LLR` 포인터가 이미 세워져 있으므로, 대조 검사를 `Init_Dec_Option` 끝에 두는 것은 성립한다. 확인됨.

보강 증거: `Init_Dec_Option`은 이미 [decoder.cpp:564](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `m_param_dec->MN[m_param_dec->MN_num - 1]`을 읽는다. 이 배열은 파서가 [local_opt.cpp:117-123](../../../../../../0_LDPC_original/src/local_opt.cpp)에서 할당하므로, 순서가 반대였다면 지금도 터진다.

**조건**: `Init_Dec_Option`은 비AUTO 경로도 함께 쓴다. 4인자 `Init_ECC_Top`([ecc_top.cpp:197-210](../../../../../../0_LDPC_original/src/ecc_top.cpp))은 `m_param_LLR`을 세우지 않고 그대로 넘기며, `ECC_Top` 생성자([ecc_top.cpp:6-34](../../../../../../0_LDPC_original/src/ecc_top.cpp))도 이 멤버를 NULL로 두지 않는다. 따라서 `Init_Dec_Option` 안에 `m_param_LLR->...` 역참조를 가드 없이 넣으면 비AUTO 빌드(`main.cpp:105`, `main.cpp:127`)가 부정 포인터를 읽는다. 처방1은 이 가드를 반드시 포함해야 한다.

### 확인 3: 문턱 값의 출처 (가설 C-처방2)

분기가 n개면 문턱은 n-1개가 필요하다 (`Select_SW_Branch`가 문턱 배열을 `num_sw_branch[span]-1`까지만 훑는다, code_diff 5.1).

`common.h`의 SW 문턱 상수 전수 ([common.h:200-252](../../../../../../0_LDPC_original/src/common.h), `__12META__`는 [mode.h:11](../../../../../../0_LDPC_original/src/mode.h)에서 주석이라 미정의 갈래 230-251행이 유효):

| 구간 | 상수 | 값 | 쓰임 |
|------|------|-----|------|
| BF 진입 | `SW_TH_BF_DEFAULT` | 630 | 4.1 default에서 `syn_th_BF0` |
| BF 진입 | `SW_TH_BF_520B_TLC_ON` | 440 | 대입처 없음 |
| BF 진입 | `SW_TH_BF_520B_TLC_OFF` | 500 | 대입처 없음 |
| BF 진입 | `SW_TH_BF_512B_TLC_ON` | 560 | 대입처 없음 |
| BF 진입 | `SW_TH_BF_512B_TLC_OFF` | 630 | 대입처 없음 (주석 처리된 case) |
| BF 진입 | `SW_TH_BF0_512B_TLC_OFF` | 680 | `matrix_sel == 1`의 `syn_th_BF0` |
| 구간 0 (iteration 1~4) 분기 | `SW_TH_BF1_512B_TLC_OFF` | 130 | `matrix_sel == 1`에서만 존재 |
| 구간 1 (iteration 5~8) 분기 | `SW_TH_5_8_SET0_DEFAULT` | 960 | default의 첫 문턱 |
| 구간 1 분기 | `SW_TH_5_8_SET0_520B_TLC_ON` | 550 | 대입처 주석 |
| 구간 1 분기 | `SW_TH_5_8_SET0_520B_TLC_OFF` | 600 | 대입처 주석 |
| 구간 1 분기 | `SW_TH_5_8_SET0_512B_TLC_ON` | 650 | 대입처 주석 |
| 구간 1 분기 | `SW_TH_5_8_SET0_512B_TLC_OFF` | 1100 | `matrix_sel == 1`의 첫 문턱 |
| 구간 1 분기 | `SW_TH_5_8_SET1_DEFAULT` | 950 | 대입만, 읽는 곳 없음 |
| 구간 1 분기 | `SW_TH_5_8_SET1_520B_TLC_ON` | 710 | 대입처 주석 |
| 구간 1 분기 | `SW_TH_5_8_SET1_520B_TLC_OFF` | 790 | 대입처 주석 |
| 구간 1 분기 | `SW_TH_5_8_SET1_512B_TLC_ON` | 860 | 대입처 주석 |
| 구간 1 분기 | `SW_TH_5_8_SET1_512B_TLC_OFF` | 950 | 대입만, 읽는 곳 없음 |

세어 보면 이렇다.

- ㉮ 구간 0의 분기 문턱: `matrix_sel == 1`에 1개(130), 그 밖의 `matrix_sel`에는 0개. 따라서 구간 0은 최대 분기 2개까지만 상수로 지탱된다
- ㉯ 구간 1의 분기 문턱: SET0과 SET1 각각 1개씩 최대 2개. 따라서 구간 1은 최대 분기 3개까지 지탱된다
- ㉰ 분기가 3개인 파일이 구간 0에 들어오면 세 번째 분기의 문턱을 가져올 상수가 코드 어디에도 없다. 구간 1에 들어오면 SET1을 두 번째 문턱으로 쓸 수 있지만 값이 뒤집혀 있다 (아래 ㉲ 절 참조)

**판정**: 파서가 `num_sw_branch[]`를 채우면 문턱 개수가 모자란다. 코드에 근거가 없다. 확인됨(처방2 반박 근거).

### 확인 4: 겹침 검사의 실행 가능성 (가설 D-처방)

| 파서 안 위치 | 그 시점에 아는 것 | 모르는 것 |
|--------------|------------------|-----------|
| 3.2 분기 줄 읽기 직후 ([local_opt.cpp:81-84](../../../../../../0_LDPC_original/src/local_opt.cpp) 뒤) | `num_group`, `num_set_each_group[]`, `type_each_group[]`, `sw_branch_idx_each_group[]`, `sw_span_idx_each_group[]` | 그룹별 iteration 범위 (`iter_start`, `iter_end`가 아직 안 읽혔다) |
| 3.4 대조 검사 자리 ([local_opt.cpp:115](../../../../../../0_LDPC_original/src/local_opt.cpp) 뒤) | 위의 전부에 더해 row별 `iter_start[]`, `iter_end[]`, `sw_branch_idx[]` | 없음 |

`iter_start`, `iter_end`는 row 반복문 [local_opt.cpp:106-115](../../../../../../0_LDPC_original/src/local_opt.cpp)에서 비로소 채워진다.

**판정**: 3.2 자리에서는 iteration 범위를 모르므로 겹침 검사를 넣을 수 없다. 검사는 3.4가 놓이는 자리(115행 뒤)에 두어야 하며, 거기서는 그룹 경계(`row_base` 누적)와 `iter_start[row_base]`, `iter_end[row_base + num_set_each_group[i] - 1]`로 그룹별 범위를 구할 수 있다. 확인됨.

### 손 실행 1: default 갈래

전제: `matrix_sel != 1`이라 4.1의 default 갈래가 실행된다. `syn_th_BF0 = SW_TH_BF_DEFAULT = 630` ([common.h:231](../../../../../../0_LDPC_original/src/common.h)), `num_sw_branch[0] = 1`, `num_sw_branch[1] = 2`, `syn_th_sw_branch[1][0] = SW_TH_5_8_SET0_DEFAULT = 960` ([common.h:240](../../../../../../0_LDPC_original/src/common.h)), 나머지 문턱은 0. 복호 모드는 `MODE_DEC_HD`, `BF_mode`는 `MODE_BF_ON`.

`Select_SW_Branch(0, weight)`는 반복문 조건이 `i < num_sw_branch[0] - 1 = 0`이라 한 번도 돌지 않고 곧바로 `num_sw_branch[0] - 1 = 0`을 돌려준다.

| syn_weight | `syn_weight < 630` | flag_BF_on | `cur_sw_branch_idx[0]` | `cur_sw_branch_idx[1]` | mn, MN |
|------------|--------------------|-----------|------------------------|------------------------|--------|
| 100 | 참 | FLAG_HIGH | 0 (`Select_SW_Branch(0,100)`) | 0 (100 < 960) | 그대로 |
| 500 | 참 | FLAG_HIGH | 0 | 0 (500 < 960) | 그대로 |
| 700 | 거짓 | FLAG_LOW | 0 (앞머리 초기화값) | 0 (700 < 960) | +4 |
| 1000 | 거짓 | FLAG_LOW | 0 | 1 (1000 >= 960) | +4 |
| 1200 | 거짓 | FLAG_LOW | 0 | 1 | +4 |

`cur_sw_branch_idx[0]`은 어떤 syn_weight에서도 0이다.

이어서 6.1 수정 후 루프를 파일의 그룹 배치로 손 실행한다. 파일에서 직접 확인한 배치는 이렇다 (상위 문서 2장 표와 일치, [LLR_MATRIX_1.txt](../../../../../../5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 헤더와 row의 17~20번째 칸에서 읽음).

| 그룹 | row 범위 | iteration | 분기 index | 파서가 매긴 구간 |
|------|---------|-----------|-----------|-----------------|
| 0 | 0~0 | 1~1 | 0 | 0 |
| 1 | 1~7 | 2~4 | 0 | 0 |
| 2 | 8~13 | 1~4 | 1 | 0 |
| 3 | 14~19 | 5~8 | 0 | 1 |
| 4 | 20~20 | 5~5 | 1 | 1 |
| 5 | 21~25 | 6~8 | 1 | 1 |
| 6~11 | 26~76 | 9~24, 25~44, 45~64, 65~84, 85~104, 105~124 | -1 | -1 |

`cur_sw_branch_idx[0] = 0` 고정, `cur_sw_branch_idx[1]`은 0 또는 1.

| iter | cur[1] | 루프가 훑는 순서와 판정 | 선택 그룹 |
|------|--------|------------------------|----------|
| 1 | 0 | g11~g6 분기 없음, iteration 범위 밖 → 계속. g5, g4 분기 1 대 cur[1] 0 → 건너뜀. g3 분기 0 통과, [5,8]에 1 없음 → 계속. **g2 분기 1 대 cur[0] 0 → 건너뜀**. g1 통과, [2,4]에 1 없음 → 계속. g0 통과, [1,1] → break | 0 |
| 3 | 0 | 위와 같고 g1의 [2,4]에 3이 들어감 → break | 1 |
| 5 | 0 | g5, g4 건너뜀. g3 통과, [5,8]에 5 → break | 3 |
| 5 | 1 | g5 통과, [6,8]에 5 없음 → 계속. g4 통과, [5,5] → break | 4 |
| 6 | 0 | g5, g4 건너뜀. g3 통과, [5,8]에 6 → break | 3 |
| 6 | 1 | g5 통과, [6,8]에 6 → break | 5 |

**판정**: 그룹 2는 `cur_sw_branch_idx[0] == 1`일 때만 뽑히는데 default 갈래에서 그 값은 절대 1이 되지 않는다. 그룹 2(row 8~13)는 어떤 프레임에서도 쓰이지 않는다. iteration 1~4는 그룹 0과 1이 빈틈없이 덮으므로 `selected_group`이 -1이 되지 않아 오류 출력도 없다. 가설 C 확인됨.

부가: 구간 1의 분기 1 그룹(4, 5)은 default 갈래에서도 살아 있다. 못 쓰게 되는 것은 구간 0의 분기 1 그룹뿐이다. R2-9의 서술과 정확히 일치한다.

### 손 실행 2: 순서 의존 배치 (6.1 수정 후 루프)

**배치 ㉮ (같은 분기 안에서 iteration 겹침).** 그룹 A는 분기 0, iteration 5~8, row 1개. 그룹 B는 분기 0, iteration 6~8, row 1개. 파서의 구간 계산으로 둘 다 구간 0 (A에서 `b == 0 && prev != 0`이라 구간이 하나 생기고, B는 `prev == 0`이라 늘지 않는다). `cur_sw_branch_idx[0] = 0`. iteration 7을 묻는다.

| 배치 | g | 그룹 | 분기 필터 | start_idx | end_idx | iteration 범위 | 판정 | break |
|------|---|------|----------|-----------|---------|---------------|------|-------|
| A 먼저 (g0=A, g1=B) | 1 | B | 0 == cur[0] 0, 통과 | 1 | 1 | 6~8 | 7 포함 | 예 |
| A 먼저 | 0 | A | 도달 안 함 | | | | | |
| B 먼저 (g0=B, g1=A) | 1 | A | 0 == cur[0] 0, 통과 | 1 | 1 | 5~8 | 7 포함 | 예 |
| B 먼저 | 0 | B | 도달 안 함 | | | | | |

결과: A 먼저면 B가, B 먼저면 A가 뽑힌다. **결과가 바뀐다.**

**배치 ㉯ (분기 없는 그룹이 1~8을 통째로 덮음).** 그룹 A는 분기 없음(-1), iteration 1~8, row 1개. 그룹 B는 분기 0, iteration 5~8, row 1개. `cur_sw_branch_idx[span] = 0`. iteration 6을 묻는다.

| 배치 | g | 그룹 | 분기 필터 | start_idx | end_idx | iteration 범위 | 판정 | break |
|------|---|------|----------|-----------|---------|---------------|------|-------|
| A 먼저 (g0=A, g1=B) | 1 | B | 분기 0, 구간 0, cur[0] 0, 통과 | 1 | 1 | 5~8 | 6 포함 | 예 |
| A 먼저 | 0 | A | 도달 안 함 | | | | | |
| B 먼저 (g0=B, g1=A) | 1 | A | 분기 -1, 필터 없음 | 1 | 1 | 1~8 | 6 포함 | 예 |
| B 먼저 | 0 | B | 도달 안 함 | | | | | |

결과: A 먼저면 B가, B 먼저면 A가 뽑힌다. **결과가 바뀐다.**

두 배치 모두 "후보 집합 안에서 그룹 index가 큰 쪽이 이긴다"로 설명된다. 가설 D 확인됨.

### 손 실행 3: 수정 전 AUTO 갈래

수정 전 루프 ([decoder.cpp:6984-6999](../../../../../../0_LDPC_original/src/decoder.cpp))에는 분기 필터가 없고 나머지는 같다.

| 배치 | 배치 순서 | g | 그룹 | iteration 범위 | 판정 | 선택 |
|------|----------|---|------|---------------|------|------|
| ㉮ (iter 7) | A 먼저 | 1 | B | 6~8 | 포함 | B |
| ㉮ (iter 7) | B 먼저 | 1 | A | 5~8 | 포함 | A |
| ㉯ (iter 6) | A 먼저 | 1 | B | 5~8 | 포함 | B |
| ㉯ (iter 6) | B 먼저 | 1 | A | 1~8 | 포함 | A |

**판정**: 수정 전에도 뒤쪽(그룹 index가 큰) 그룹이 이긴다. "6.1이 새로 만든 결함이 아니다"는 Round 2 판정은 맞다. 확인됨.

다만 범위는 다르다. 수정 전에는 후보가 전체 그룹이므로 순서 의존이 더 넓게 걸린다. 현 파일로 수정 전 루프를 돌리면 iteration 1~4에서 g5(6~8) 불일치, g4(5~5) 불일치, g3(5~8) 불일치를 지나 g2(1~4)가 먼저 잡혀 항상 그룹 2가 뽑히고, iteration 5는 g4, iteration 6~8은 g5가 뽑힌다. 6.1의 분기 필터는 이 범위를 후보 집합 안으로 좁히지만 없애지는 못한다. R2-11의 "실제 범위를 넘는다"는 서술이 정확하다.

---

## ㉰ 증거 목록

### 확인됨

| # | 증거 | 근거 |
|---|------|------|
| E1 | AUTO 빌드의 `Setup_Ref_C`는 `argc > 19`일 때 `matrix_sel` 값을 검증하지 않는다 | [main.cpp:139-153](../../../../../../0_LDPC_original/src/main.cpp) |
| E2 | `matrix_sel` 대입은 `main.cpp` 전체에서 139행과 499행 두 곳뿐이고 둘 다 `atoi(argv[1])`이다 | Grep 전수, 히트 목록은 확인 1 ㉮ |
| E3 | 살아 있는 layout 상수는 `LAYOUT_PRIME_512B_TLC_VSS_OFF` 1 하나뿐이다 | [common.h:192-198](../../../../../../0_LDPC_original/src/common.h) |
| E4 | DAO는 `matrix_sel = 1`과 `str_matrix_name = "H_402091"`을 고정으로 넘기고 인자 19개(argc 20)를 만든다 | [DAO_Config.py:170, 189](../../../../../../5_DAO/SRC/DAO_Config.py), [DAO_Main.py:6434-6455, 6550-6555](../../../../../../5_DAO/SRC/DAO_Main.py) |
| E5 | `Read_LLR_info_Auto`가 `Init_Dec_Option`보다 먼저 불린다 | [local_opt.cpp:34, 46](../../../../../../0_LDPC_original/src/local_opt.cpp), [ecc_top.cpp:216-230](../../../../../../0_LDPC_original/src/ecc_top.cpp) |
| E6 | `Init_Dec_Option`은 이미 파서가 채운 `m_param_dec->MN`을 읽는다 | [decoder.cpp:564](../../../../../../0_LDPC_original/src/decoder.cpp), [local_opt.cpp:117-123](../../../../../../0_LDPC_original/src/local_opt.cpp) |
| E7 | 4인자 `Init_ECC_Top`은 `m_param_LLR`을 세우지 않고 넘기며 생성자도 NULL로 두지 않는다 | [ecc_top.cpp:6-34, 197-210](../../../../../../0_LDPC_original/src/ecc_top.cpp) |
| E8 | 구간 0의 분기 문턱 상수는 `matrix_sel == 1`용 `SW_TH_BF1_512B_TLC_OFF` 하나뿐이다 | [common.h:230-251](../../../../../../0_LDPC_original/src/common.h) |
| E9 | `syn_th_BF1`, `syn_th_5_8_Set_1`, `syn_th_BF`는 대입만 되고 읽히지 않는다 | Grep 전수: `syn_th_BF1`은 [decoder.h:303](../../../../../../0_LDPC_original/src/decoder.h)와 [decoder.cpp:468](../../../../../../0_LDPC_original/src/decoder.cpp), `syn_th_5_8_Set_1`은 decoder.h:306, decoder.cpp:489, 492와 주석 처리된 decoder.cpp:583, `syn_th_BF`는 decoder.h:301과 decoder.cpp:472 |
| E10 | `iter_start`, `iter_end`는 row 반복문에서 비로소 채워지므로 3.2 자리에서는 겹침 검사가 불가능하다 | [local_opt.cpp:106-115](../../../../../../0_LDPC_original/src/local_opt.cpp) |
| E11 | 파일의 그룹 배치가 상위 문서 2장 표와 일치한다 (분기 `0 0 1 0 1 1 -1 x6`, 구간 0 = 그룹 0~2, 구간 1 = 그룹 3~5) | [LLR_MATRIX_1.txt](../../../../../../5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 헤더와 각 row의 17~20번째 칸 |
| E12 | 수정 전 AUTO 루프에도 분기 필터가 없어 뒤쪽 그룹이 이긴다 | [decoder.cpp:6984-6999](../../../../../../0_LDPC_original/src/decoder.cpp) |

### 미확인

| # | 항목 | 사유 |
|---|------|------|
| U1 | 사용자가 실제로 `matrix_sel`을 1이 아닌 값으로 돌린 적이 있는지 | 저장소 안에 실행 기록이 없다. 설정 파일의 현재 값만 확인 가능 |
| U2 | 분기 3개짜리 파일이 실제로 들어올 계획인지 | 상위 문서 2장이 형태로는 최대 9개를 허용한다고만 적고, 현재 파일은 구간마다 2개다 |

### 반박됨

| # | 항목 | 사유 |
|---|------|------|
| R1 | "이 조합은 DAO 실행에서 발생한다" (R2-9 서술이 이렇게 읽힐 여지가 있다) | DAO는 `matrix_sel = 1`을 고정으로 넘긴다 (E4). 도달 가능성은 참이지만 현행 실행에서는 발생하지 않는다 |

---

## ㉱ 처방 평가

### C-처방1: 파서가 세어 `PARAM_LLR`에 기록, `Init_Dec_Option` 끝에서 대조

**처방 수정 필요.** 방향은 옳고 호출 순서도 성립한다(E5, E6). 다음 두 가지를 보태야 성립한다.

- ㉮ **멈추는 수단이 없다.** `Init_Dec_Option`은 void이고 호출처([ecc_top.cpp:229](../../../../../../0_LDPC_original/src/ecc_top.cpp))도 반환값을 받지 않는다. `printf`는 DAO에 닿지 않는다(R2-8과 같은 구조). 대조에 실패했을 때 실제로 멈추려면 종료 코드를 바꾸는 경로가 필요하다. R2-8의 처방과 한 벌로 묶어야 한다
- ㉯ **비AUTO 빌드 가드가 필요하다.** `Init_Dec_Option`은 4인자 `Init_ECC_Top` 경로에서도 불리고 그때 `m_param_LLR`은 부정 포인터다(E7). 대조 코드를 `#if defined(__AUTO_LLR_OPT__)` 안에 넣거나 널 검사를 앞세워야 한다. code_diff 8.1, 8.2가 AUTO 갈래만 남기는 방향(R2-1)과 함께 결정해야 한다

부작용 점검: 현 파일과 `matrix_sel == 1` 조합에서는 구간마다 분기 2개, 문턱 1개씩이라 "양수 오름차순" 검사가 공허하게 참이 되어 통과한다. 새로 막히는 실행은 없다. `matrix_sel != 1`로 현 파일을 돌리면 지금은 조용히 잘못 돌던 것이 멈추게 되는데, 이것이 이 처방의 목적이다.

### C-처방2: 파서가 세어 `num_sw_branch[]`를 직접 채운다

**처방 반대.** 사유는 둘이다.

- ㉮ **문턱 출처가 없다.** 분기 n개에는 문턱 n-1개가 필요한데 `common.h`에는 구간 0에 최대 1개(그것도 `matrix_sel == 1`에만), 구간 1에 최대 2개뿐이다(E8). 파일이 구간 0에 분기 3개를 실어 오면 세 번째 분기를 가르는 값이 코드 어디에도 없다
- ㉯ **침묵 오선택이 그대로 남는다.** 4.1의 초기화가 `syn_th_sw_branch[i][j] = 0`이므로, 파서가 `num_sw_branch[0] = 3`으로 채우고 문턱이 하나만 실제 값이면 `Select_SW_Branch`는 `weight < 0` 비교에서 항상 거짓이 되어 분기 1을 영영 고르지 않는다. R2-9가 지적한 것과 같은 종류의 침묵 오류가 자리만 옮겨 남는다

이 처방은 문턱을 파일이나 실행 인자로 받는 결정(상위 문서 7장 ㉯)이 먼저 서야 성립한다. 그 결정 없이 단독으로 적용하면 안 된다.

### D-처방: 문서에 전제를 적고 파서에 범위 겹침 검사를 넣는다

**처방 유효.** 조건 하나가 붙는다.

- ㉮ 검사 위치는 3.2(분기 줄 읽기 직후)가 아니라 3.4가 놓이는 자리(115행 뒤)여야 한다(E10). 그 자리에서 그룹별 `iter_start`, `iter_end`를 알 수 있고, 3.4의 대조 검사와 같은 `row_base` 누적을 재사용할 수 있다
- ㉯ 검사 대상 집합은 "한 구간의 같은 분기에 속한 그룹들" 과 "분기 없는 그룹들"을 합친 것이다. 현 파일은 이 집합 안에서 겹침이 없다 (구간 0 분기 0은 1~1과 2~4, 구간 0 분기 1은 1~4 하나, 구간 1 분기 0은 5~8 하나, 구간 1 분기 1은 5~5와 6~8, 분기 없는 그룹은 9~24부터 105~124까지 서로 붙어 있다). 검사를 넣어도 현 파일은 통과한다
- ㉰ 멈추는 수단은 처방1과 같은 문제를 공유한다. R2-8과 한 벌로 처리해야 한다

문서 전제 문구도 함께 적어야 한다. 6.1이 "분기 일치를 넣으면 결과가 순서에 좌우되지 않는다"라고 단정한 부분(상위 문서 5.3-2, code_diff 6.1 바뀐 점 ㉯)을 "한 분기의 그룹들과 분기 없는 그룹을 합친 집합 안에서 iteration 범위가 겹치지 않는다는 전제 아래 순서에 좌우되지 않는다"로 다시 써야 한다.

---

## ㉲ 검증 중 새로 드러난 사실

- ㉮ **`SW_TH_5_8_SET0_*`과 `SW_TH_5_8_SET1_*`은 오름차순이 아니다.** `matrix_sel == 1`에서 SET0은 1100, SET1은 950이고([common.h:244, 251](../../../../../../0_LDPC_original/src/common.h)), default에서도 SET0 960, SET1 950이다([common.h:240, 247](../../../../../../0_LDPC_original/src/common.h)). code_diff 4.1은 "`SW_TH_5_8_SET1_*`은 분기가 셋 이상일 때 `syn_th_sw_branch[1][1]`에 들어간다"라고 적고 `Select_SW_Branch`는 문턱이 오름차순임을 전제한다. 그대로 넣으면 `syn_th_sw_branch[1][0] = 1100`, `[1][1] = 950`이 되어 분기 1은 절대 선택되지 않는다 (weight < 1100이면 반복문 첫 회에 0을 돌려주고, 아니면 950 비교도 거짓이라 마지막 분기 2를 돌려준다). 처방1이 넣으려는 "문턱의 양수 오름차순 대조"는 바로 이 조합을 잡아내므로 처방1의 가치를 높인다. 동시에 4.1의 설명 문장은 고쳐야 한다
- ㉯ **수정 전 코드에는 `matrix_sel != 1`에서 `syn_th_BF0`이 초기화되지 않는 결함이 있다.** [decoder.cpp:472](../../../../../../0_LDPC_original/src/decoder.cpp)의 default 갈래는 읽히지 않는 `syn_th_BF`에만 대입하고, BF 진입 판정([decoder.cpp:2088](../../../../../../0_LDPC_original/src/decoder.cpp))은 `syn_th_BF0`을 읽는다. 비AUTO `Setup_Ref_C`는 `matrix_sel != 1`을 거르지만 `Setup_TV_Gen`([main.cpp:500](../../../../../../0_LDPC_original/src/main.cpp))은 `LAYOUT_PRIME_512B_TLC_VSS_OFF <= matrix_sel`만 보므로 2 이상이 통과한다. code_diff 4.1의 수정 후 코드는 default에서 `syn_th_BF0 = SW_TH_BF_DEFAULT`를 넣어 이 결함을 함께 고친다. 계획의 부수 이득이므로 문서에 적을 값어치가 있다
- ㉰ **`matrix_sel != 1`은 SW 문턱 밖에서도 지원되지 않는다.** PCRC termination point는 [decoder.cpp:536-541](../../../../../../0_LDPC_original/src/decoder.cpp)에서 `matrix_sel == 1`일 때만 채워지고, `idxTermination`은 [decoder.h:356](../../../../../../0_LDPC_original/src/decoder.h)의 평범한 멤버 배열이라 그 밖에는 부정값으로 남아 [decoder.cpp:2140-2143](../../../../../../0_LDPC_original/src/decoder.cpp) 등에서 읽힌다. 따라서 R2-9가 가리키는 진짜 구멍은 "분기 개수 대조가 없다"보다 "AUTO 갈래가 `matrix_sel` 값 자체를 검증하지 않는다"에 가깝다. 처방을 정할 때 `main.cpp:141-143`에 `matrix_sel` 검증을 넣는 갈래를 함께 올리는 것이 낫다
- ㉱ **`MAX_SW_SPAN`이 4인데 4.1은 구간 0과 1만 채운다.** 나머지 두 구간은 `num_sw_branch[i] = 1`로 남으므로, 파일이 구간을 셋 이상 만들면(분기 index가 0으로 두 번 넘게 되돌아가면) 구간 2 이상의 분기 1번 이후 그룹이 전부 후보에서 빠진다. 가설 C와 같은 구조가 구간 축으로 한 번 더 있다. 처방1의 대조 검사는 `num_sw_span`까지 함께 보므로 이것도 잡는다
- ㉲ **수정 전 AUTO 루프의 현 파일 결과를 재확인했다.** iteration 1~4는 그룹 2, iteration 5는 그룹 4, iteration 6~8은 그룹 5가 뽑힌다. 6.1 수정 후에는 분기가 0일 때 iteration 1은 그룹 0, 2~4는 그룹 1, 5~8은 그룹 3이 된다. R2-4 ㉰의 "3단계 검증 기준이 뒤집힌다"는 서술과 일치한다 (팀 V1 담당 항목이나 손 실행 과정에서 같은 결론이 나왔다)
