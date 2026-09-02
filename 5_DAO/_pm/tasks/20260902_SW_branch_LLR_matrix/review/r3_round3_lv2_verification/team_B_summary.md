# Round 3 팀 B (재탐색) 요약

작성: 2026-09-03 01:51:29

이전 라운드가 보지 않은 영역 일곱 가지(㉮에서 ㉴)를 워커 셋에 나눠 독립 탐색했다.
이전 라운드의 결론은 워커에게 전달하지 않았다.

대상 문서 (수정하지 않음): [상위 문서](../../20260902_SW_branch_LLR_matrix.md), [code_diff.md](../../code_diff.md)

---

## ㉮ 워커 결과 요약

| 워커 | 배정 영역 | 결과 파일 | 발견 수 |
|------|----------|----------|--------|
| B1 | ㉮ mode.h에서 켜진 스위치 다섯 개와 수정 후 코드의 맞물림, ㉳ `Get_VNU_LLR_SET_FILE` 경로와 새 파일 치수 | [worker_B_1.md](worker_B_1.md) | MEDIUM 7, LOW 2, 문제 없음 2 |
| B2 | ㉯ `MN[n]` 소비처 전수와 음수 값 동작, ㉲ BF 진입 프레임의 iteration 121에서 124 미도달 비대칭 | [worker_B_2.md](worker_B_2.md) | HIGH 2, MEDIUM 4, LOW 4, 정정 1 |
| B3 | ㉰ 2SD와 3SD 경로, ㉱ 극단 입력, ㉴ 프레임 간 초기화 전수 | [worker_B_3.md](worker_B_3.md) | CRITICAL 2, HIGH 3, MEDIUM 7, LOW 2, 반박 3, 문제 없음 1 |

BF는 Bit Flipping(하드 결정 복호 초기 iteration에서 1bit precision으로 도는 모드)이다.
SW는 Syndrome Weight(신드롬 무게)다.

리더가 직접 재확인한 것: [local_opt.cpp:101-131](../../../../../../0_LDPC_original/src/local_opt.cpp)의
행 할당과 `MN[]` 보정, [decoder.cpp:7074-7132](../../../../../../0_LDPC_original/src/decoder.cpp)의
dv 그룹별 column 오프셋, [decoder.h:328](../../../../../../0_LDPC_original/src/decoder.h)의 `int MN;`,
[common.h:75-78](../../../../../../0_LDPC_original/src/common.h)의 복호 모드 상수,
[DAO_Config.py](../../../../../SRC/DAO_Config.py)의 `init_n` 대입 아홉 곳.

---

## ㉯ 교차 분석

심각도는 워커 판정을 그대로 쓰되, 다른 워커의 근거로 발생 가능성이 바뀐 곳은 재판정하고 그 이유를 적었다.

### CRITICAL

| # | 문제 | 위치 | 근거 | 처방과 성격 | 지적 워커 |
|---|------|------|------|------------|----------|
| B-1 | `num_row`가 0인 파일에서 6.2의 `return 0` 뒤 `Get_VNU_LLR_SET_FILE`이 크기 0 배열의 원소 0을 역참조한다. code_diff 6.2 "바뀐 점 ㉰"의 안전 주장은 `num_row >= 1`에서만 참이다 | code_diff 6.2 수정 후 | [local_opt.cpp:75-80, 101](../../../../../../0_LDPC_original/src/local_opt.cpp), [decoder.cpp:1138](../../../../../../0_LDPC_original/src/decoder.cpp), [decoder.cpp:7089](../../../../../../0_LDPC_original/src/decoder.cpp) | 파서에서 `num_group <= 0` 또는 `num_row <= 0`을 오류로 잡고 멈춘다 (**코드 추가**) | B3 |
| B-2 | 3.5 수정 후 `max_iter_end`가 0이면 `MN_num`이 0이 되어 `MN[-1]`을 읽는 곳이 22곳이고, `decoder.cpp:564`는 그 값으로 `new int[]`를 잡는다. `ecc_top.cpp:875`는 `fr_4KB[-1]`에 쓴다 | code_diff 3.5 수정 후 | [local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp), [decoder.cpp:564, 587, 1118](../../../../../../0_LDPC_original/src/decoder.cpp), [ecc_top.cpp:638, 875](../../../../../../0_LDPC_original/src/ecc_top.cpp) | 3.5 뒤에 `max_iter_end <= 0`을 오류로 잡고 멈춘다 (**코드 추가**) | B3 |

**교차 판정 (B-2의 발생 가능성 상향)**: B3은 B-2를 이론상 극단 입력으로 보았으나, B2가 도달 경로를 찾았다.
DAO(Decoder Auto Optimizer)의 HBF 최적화 모드가 매트릭스 최대 iteration을 4 이하로 강제한다
([DAO_LLR_MATRIX.py:442-447](../../../../../SRC/DAO_LLR_MATRIX.py),
[DAO_Config.py:372](../../../../../SRC/DAO_Config.py)의 `HBF_MAX_ITERATION` 4).
그러면 `MN[MN_num-1] = max_iter - 4 <= 0`이 되어 B-4가 먼저 걸린다.
`max_iter`가 정확히 4보다 작으면 `MN_num`이 그만큼 줄어 B-2 인접 구간으로 들어간다.
두 발견은 같은 보정식 `local_opt.cpp:125-130`이 만드는 하나의 구멍이며, 처방도 한 자리에서 함께 닫아야 한다.

### HIGH

| # | 문제 | 위치 | 근거 | 처방과 성격 | 지적 워커 |
|---|------|------|------|------------|----------|
| B-3 | `ITER_MAX_HBF`를 4로 바꾸면 모든 프레임의 실제 복호 iteration이 124회에서 120회로 준다. `MN[123]`이 124에서 120으로 내려가 루프 상한이 되고, BF 진입 프레임은 iteration 120에서, 미진입 프레임은 상한 연장으로 124에서 끝난다. FER과 `avg_iteration`이 함께 바뀐다. 두 문서 어디에도 없다 | code_diff 1.2가 3.5, `local_opt.cpp:124-131`과 맞물린 결과 | [local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp), [decoder.cpp:1118, 1120, 2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp), code_diff 5.1 수정 후 | 문서에 결과를 명시하고 의도인지 결정을 받는다. 의도가 아니면 보정식이나 상한 연장 중 하나를 고친다 (**동작 변경**) | B2 (B1이 독립 계산으로 확인) |
| B-4 | 최대 iteration이 4 이하인 매트릭스에서 복호가 한 번도 일어나지 않는다. 루프가 `mn == 0` 한 번만 돌고 끝나 모든 프레임이 uncor가 된다. 게다가 `iter_num`이 프레임마다 초기화되지 않아 `-= 4`가 누적된다 | code_diff 1.2 + `local_opt.cpp:125-130` | [local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp), [decoder.cpp:1118-1120, 1136-1142, 1947-1951, 1976](../../../../../../0_LDPC_original/src/decoder.cpp), [DAO_LLR_MATRIX.py:442-447](../../../../../SRC/DAO_LLR_MATRIX.py) | 보정에 하한을 두거나(`max_iter <= ITER_MAX_HBF`이면 보정 생략) 파서가 검사해 멈춘다 (**동작 변경**) | B2 (B3-17이 `iter_num` 미초기화를 독립 확인) |
| B-5 | AUTO 빌드의 2SD와 3SD에서 고르는 그룹이 뒤집힌다. 수정 전 AUTO 루프는 뒤에서 훑어 iteration 1~4에 그룹 2, 5에 그룹 4, 6~8에 그룹 5(모두 분기 1)를 골랐는데, 수정 후 6.1의 분기 필터와 5.1의 `else`(분기 0 고정)가 겹쳐 그룹 0, 1, 3이 된다. 그룹 2, 4, 5의 row 12개가 오류 없이 도달 불가가 된다 (전체 77개 중) | code_diff 5.1과 6.1 수정 후 | [decoder.cpp:1968-1970, 6985-6999](../../../../../../0_LDPC_original/src/decoder.cpp), [common.h:75-78](../../../../../../0_LDPC_original/src/common.h), [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 헤더 | 2SD와 3SD도 SW로 분기를 고르게 하거나, 분기 0 고정을 결정으로 문서에 적고 파서가 SD 파일의 분기 그룹을 막는다 (**동작 변경 또는 문서 결정**) | B3 |
| B-6 | 어느 그룹의 `num_set_each_group[i]`가 0이면 `end_idx = start_idx - 1`이 되어 `iter_end[-1]`이나 앞 그룹 값을 읽는다. 그 그룹이 `GROUP_TYPE_CSW`이면 다음 그룹의 첫 row를 오류 표시 없이 쓴다. 3.4의 대조 검사도 빈 그룹은 잡지 않는다 | code_diff 6.1, 6.2, 3.4 수정 후 | [decoder.cpp:6986-6994, 7056-7065](../../../../../../0_LDPC_original/src/decoder.cpp), code_diff 3.4와 6.1 수정 후 | 파서에서 `num_set_each_group[i] <= 0`을 오류로 잡는다 (**코드 추가**) | B3 |
| B-7 | `Clear_Flag`의 두 줄이 2.2가 지우는 멤버에 대입하는데 code_diff 어느 장도 다루지 않아 양쪽 빌드가 컴파일되지 않는다. 전수 grep으로 남는 곳이 이 두 줄뿐임을 확인했다 | [decoder.cpp:612-613](../../../../../../0_LDPC_original/src/decoder.cpp) | `flag_HD_1_4_Set` 히트 5곳(`decoder.cpp:612, 2090, 7002, 7006`, `decoder.h:297`), `flag_HD_5_8_Set` 히트 9곳(`decoder.cpp:613, 2091, 2100, 2106, 2117, 2123, 7010, 7016`, `decoder.h:298`) | 612-613을 지우고 그 자리에 `cur_sw_branch_idx[]` 0 채우기를 넣는다 (**코드 삭제와 추가**) | B3 |
| B-8 | 2SD와 3SD 모드가 `LLR_MATRIX[row]` 행 밖을 읽는다. `num_para_each_set`이 4인데 2SD는 dv 그룹당 5칸(마지막 그룹에서 index 16), 3SD는 7칸(index 16에서 18)을 읽고 행은 16칸이다. 오류도 크래시도 없이 `th3`가 무작위 값이 된다 | [decoder.cpp:7108-7110, 7123-7125](../../../../../../0_LDPC_original/src/decoder.cpp) | 행 크기는 [local_opt.cpp:101](../../../../../../0_LDPC_original/src/local_opt.cpp)의 `new int[num_col]`이고 이 파일의 `num_col`은 16. 리더가 두 줄을 직접 읽어 확인 | 문서에 "이 형태의 파일은 HD와 1.5SD 전용"이라는 제약을 적고, `init_n`과 `num_para_each_set`을 대조해 어긋나면 멈춘다 (**코드 추가**) | B1 (B3이 도달 가능성 확인) |

**교차 판정 (B-8의 심각도 상향, MEDIUM에서 HIGH)**: B1은 "DAO가 2SD나 3SD 모드로 AUTO 빌드를 돌리는지 확인하지 않았다"를 미확인으로 남겼다.
B3이 그 답을 찾았다. [DAO_Config.py](../../../../../SRC/DAO_Config.py)가 `init_n`을 2로 세 곳(62, 74, 83행),
3으로 세 곳(94, 104, 111행) 세우고, [DAO_Main.py:6413, 6436](../../../../../SRC/DAO_Main.py)이 그것을
Ref-C 실행 인자 두 번째로 넣으며 [main.cpp:167-168](../../../../../../0_LDPC_original/src/main.cpp)이 받는다.
리더가 `grep -n "init_n" DAO_Config.py`로 아홉 곳을 직접 확인했다. 즉 행 밖 읽기는 실제 운용에서 도달한다.
기존 상태이지 계획이 만드는 결함은 아니지만, 계획이 2SD와 3SD의 동작을 바꾸면서(B-5) 이 제약을 적지 않는다.

**교차 판정 (B-5와 B-8의 결합)**: 두 발견은 같은 조건(AUTO 빌드에서 2SD 또는 3SD)에서 함께 일어난다.
B-5가 그룹을 잘못 고르고 B-8이 그 row의 마지막 문턱을 쓰레기 값으로 읽는다.
2SD와 3SD의 적용 범위를 정하는 결정 하나가 두 발견을 함께 처리한다.

### MEDIUM

| # | 문제 | 위치 | 근거 | 처방과 성격 | 지적 워커 |
|---|------|------|------|------------|----------|
| B-9 | 상위 5.5, 5.6 표가 든 `ITER_MAX_HBF` 소비처 셋과 code_diff 8.3이 다루는 블록이 꺼진 스위치 안이라 어느 빌드에도 들어가지 않는다. "`flag_BF_on`이 살아나면 조건이 저절로 맞는다"는 무효다 (Preprocessing 자체가 컴파일되지 않는다) | 상위 5.5, 5.6 표, code_diff 8.3 | [decoder.cpp:1146, 2303, 3480, 6450](../../../../../../0_LDPC_original/src/decoder.cpp), [mode.h:63, 78](../../../../../../0_LDPC_original/src/mode.h) | 표와 8.3에 꺼진 스위치임을 적고 BF 부활의 효과 목록에서 Preprocessing을 뺀다 (**문서**) | B1과 B3 (독립 확인 둘) |
| B-10 | 5.5 표에 빠진 살아있는 `ITER_MAX_HBF` 소비처가 있다. `decoder.cpp:2169`는 `__DUAL_UPDATE__`(켜짐) 안이고 partial CRC 조기 종료 제한 지점이 mn 1 하나에서 1과 5 둘로 늘어난다. 로그 배열 크기 계산도 15곳이 더 있다 | 상위 5.5 표 | [decoder.cpp:2169](../../../../../../0_LDPC_original/src/decoder.cpp), [mode.h:64](../../../../../../0_LDPC_original/src/mode.h), `MN_size` 계산 18곳 | 표에 두 항목을 넣는다. 배열 경계는 안전하므로 코드 변경은 없다 (**문서**) | B1 |
| B-11 | code_diff 8.1의 "BF에 진입하면 1에서, 진입하지 않으면 5에서 걸린다"가 사실과 다르다. `Is_Iter_Type_Edge_Clear`는 `flag_BF_on`을 보지 않고 조건이 {0, 1, 5}의 OR이므로 BF 진입 프레임은 iteration 5에서도 edge clear를 맞아 1에서 4까지 쌓은 edge를 통째로 지운다 | code_diff 8.1 설명 | [decoder.cpp:6538, 6543-6545, 709-724](../../../../../../0_LDPC_original/src/decoder.cpp) | 설명을 "0, 1, 5 세 지점에서 일어나고, 미진입 프레임은 1을 돌지 않아 0과 5에서만 걸린다"로 다시 쓴다 (**문서**) | B1 |
| B-12 | BF를 살리면 iteration 1에서 4 동안 차수가 5를 넘는 column이 파일의 `th1`, `th2`, `th3`를 쓰지 않는다. 분기 구간 row 14개의 1, 2, 3번 칸, 즉 42개 파라미터가 DAO 탐색에서 don't care가 된다 | 상위 5.5, code_diff 7장의 결과 | [decoder.cpp:4056, 4060-4079, 4275, 4279-4297, 7093-7095](../../../../../../0_LDPC_original/src/decoder.cpp), [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 5행과 6행 | 상위 5.5에 이 결과를 적는다 (**문서**) | B1 |
| B-13 | 1.5SD에서 iteration 125에서 128을 돈다. `local_opt.cpp:124`의 보정 조건이 `MODE_DEC_1_5SD`를 빠뜨려 `MN[]` 보정을 받지 못하는데 수정 후 `Select_BF`는 1.5SD에서 상한을 4 늘린다. 파일의 최대 `iter_end`가 124이므로 프레임마다 오류 4줄을 찍고 row 0으로 4 iteration을 돈다. 지금은 `ITER_MAX_HBF`가 0이라 없던 새 결함이다 | code_diff 5.1 + 1.2 | [local_opt.cpp:124](../../../../../../0_LDPC_original/src/local_opt.cpp), [common.h:78](../../../../../../0_LDPC_original/src/common.h), code_diff 5.1과 6.2 수정 후 | `local_opt.cpp:124`의 둘째 항을 `MODE_DEC_1_5SD`로 고친다. 그러면 1.5SD도 B-3의 축소를 함께 받는다 (**식별자 변경, 동작 변경**) | B2 |
| B-14 | 결과 파일 FER 열의 문턱이 음수와 중복이 된다. `MN = [4, -3, -2, -1, 0, 1, ..., 118, 120]`이라 열 1에서 4가 1.0 고정, 열 0과 8이 중복, 열 n(n >= 5)의 뜻이 iteration n-4로 밀린다 | `local_opt.cpp:125-130`의 결과 | [ecc_top.cpp:877-881, 2020-2024, 2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp), [main.cpp:313-320](../../../../../../0_LDPC_original/src/main.cpp) | 보정식을 고치거나 문서에 열 배치를 적는다 (**보정식 변경이면 동작 변경**) | B2 |
| B-15 | code_diff 3.5가 `local_opt.cpp:124-131`을 다루지 않아 `MN[]`의 최종 모습이 문서에 없다. 이 블록은 `ITER_MAX_HBF`가 0인 지금은 무효라 눈에 띄지 않지만 1.2장이 4로 바꾸는 순간 살아난다 | code_diff 3.5 제목이 116-123행 | 상위 5.5 표 262행이 언급만 하고 결과를 적지 않음 | 3.5에 124-131행을 살린다고 적고 그때의 `MN[]` 값을 표로 싣는다 (**문서**) | B2 |
| B-16 | BF 진입 프레임과 미진입 프레임의 iteration 수열 비대칭이 두 문서 어디에도 없다. 상위 2장은 "최대 iteration은 124다"라고만 적는다 | 상위 2장 62행, 5.5 표, code_diff 8.1 | [decoder.cpp:1118-1120, 2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp) | 상위 5.5에 두 프레임 종류의 `mn` 수열과 최대 도달 iteration을 표로 적는다 (**문서**) | B2 |
| B-17 | "2SD와 3SD는 분기 0 고정"이 두 문서 어디에도 없고, 3.2 파서가 분기 줄을 모드와 무관하게 무조건 읽으므로 SD 파일에도 그 줄이 필요하다는 서술도 없다. DAO의 Python 파서는 아직 그 줄을 모른다 | 상위 5.4와 7장, code_diff 3.2와 5.1 | [local_opt.cpp:52-184](../../../../../../0_LDPC_original/src/local_opt.cpp), [DAO_LLR_MATRIX.py:476-491](../../../../../SRC/DAO_LLR_MATRIX.py) | 상위 7장 미결정 사항에 모드별 적용 범위를 올리고, 3.2에 "모든 복호 모드의 파일이 분기 줄을 갖는다"를 전제로 적는다 (**문서**) | B3 |
| B-18 | dv 그룹에 걸리지 않는 column 차수가 조용히 dv 그룹 0을 쓴다. `table_col_idx`가 초기값 0으로 남고 오류가 없다. code_diff 6.2는 row 쪽 초기값만 -1로 바꾸고 col 쪽에는 아무 검사도 넣지 않는다. 이 파일의 dv 그룹은 {11}, {4}, {3}, {2} 단일값 넷뿐이고 `MAX_DV_GLOBAL`은 17이다 | [decoder.cpp:7075-7083](../../../../../../0_LDPC_original/src/decoder.cpp) | [common.h:291-293](../../../../../../0_LDPC_original/src/common.h), [decoder.cpp:5704, 5744](../../../../../../0_LDPC_original/src/decoder.cpp) | 탐색 반복문 뒤에 못 찾은 경우의 오류 출력을 넣는다 (**코드 추가**) | B1 |
| B-19 | code_diff 3.7의 MPI 전파는 이 저장소에서 컴파일될 수 없는 갈래다. `mode.h:22`가 `__AUTO_LLR_OPT__`를 정의한 바로 다음 줄에서 `#if !defined(__AUTO_LLR_OPT__)`로 `__RUN_MPI__`를 감싸 항상 거짓이고, `mpi.cpp`는 선언만 있고 정의가 없다. 3.7이 던진 물음("어느 쪽인지 확인한 뒤 맞춘다")은 이 저장소 안에서 답이 정해지지 않는다 | code_diff 3.7 | [mode.h:10, 21-26](../../../../../../0_LDPC_original/src/mode.h), [mpi.cpp](../../../../../../0_LDPC_original/src/mpi.cpp) 전체 | 3.7에 이 사실과 켜는 빌드에서 확인이 필요함을 적는다 (**문서**) | B1 |
| B-20 | `cur_sw_branch_idx[]`의 프레임 초기화가 `Select_BF` 안에만 있다. `Select_BF`를 건너뛸 수 있는 경로가 하나 있고(power stopping), 지금 안전한 근거가 `decoder.cpp:505`의 컴파일 스위치 하나에 달려 있다 | code_diff 5.1 수정 후 | [decoder.cpp:505-506, 1962-1970](../../../../../../0_LDPC_original/src/decoder.cpp), [decoder.cpp:606-616](../../../../../../0_LDPC_original/src/decoder.cpp) | 초기화를 `Clear_Flag`로 옮긴다. B-7의 처방과 같은 자리라 한 번에 처리된다 (**코드 이동**) | B3 |
| B-21 | `iter_num`이 프레임마다 초기화되지 않는다. 정상 흐름에서는 `Check_End_Iter`가 반드시 채우지만, 루프가 한 번도 돌지 않으면 앞 프레임 값이 그대로 나가고 `-= ITER_MAX_HBF`까지 그 값에 걸린다 | [decoder.h:324](../../../../../../0_LDPC_original/src/decoder.h) | [decoder.cpp:606-616, 1975-1978, 1998, 5344, 5355](../../../../../../0_LDPC_original/src/decoder.cpp) | `Clear_Flag`에 초기화를 넣는다 (**코드 추가**) | B3 |

### LOW

| # | 문제 | 위치 | 근거 | 처방과 성격 | 지적 워커 |
|---|------|------|------|------------|----------|
| B-22 | code_diff 4.1의 "문턱은 오름차순"이라는 서술과 실제 상수가 어긋난다. `SW_TH_5_8_SET0_512B_TLC_OFF` 1100이 `SW_TH_5_8_SET1_512B_TLC_OFF` 950보다 크다. `Select_SW_Branch`는 오름차순을 전제하므로 분기가 셋이 되면 마지막 분기가 영영 선택되지 않는다 | code_diff 4.1 447-449행과 473-474행, 5.1 542-547행 | [common.h:244, 251](../../../../../../0_LDPC_original/src/common.h) | 상위 7장 ㉯(문턱 출처)에 이 상수 순서를 근거로 붙인다 (**문서**) | B2 |
| B-23 | `__4_BIT_LLR__`를 켜면 HD 경로도 행 밖 4칸을 읽는다. `num_para_each_set >= 8`이 필요하다. 지금은 `mode.h:12`가 주석이라 일어나지 않는다 | [decoder.cpp:7096-7101](../../../../../../0_LDPC_original/src/decoder.cpp) | [mode.h:12](../../../../../../0_LDPC_original/src/mode.h) | B-8의 제약 문장에 함께 적는다 (**문서**) | B1 |
| B-24 | `__PRINT_LOG_DATA__`를 켜면 histogram 배열 밖을 쓴다. `size_histogram`이 480인데 `matrix_sel`이 다르면 `idx`가 495까지 올라간다. 같은 블록의 `+ 2` 계열 다섯 곳은 `ITER_MAX_HBF`를 더하지 않아 로그 커버리지가 126칸에서 122칸으로 준다. 지금은 `mode.h:31`이 주석이다 | [ecc_top.cpp:2805-2810, 2819](../../../../../../0_LDPC_original/src/ecc_top.cpp) | [ecc_top.cpp:2738, 2757, 2774, 2790, 2815](../../../../../../0_LDPC_original/src/ecc_top.cpp), [mode.h:31](../../../../../../0_LDPC_original/src/mode.h) | 다섯 곳에 `+ ITER_MAX_HBF`를 붙여 `decoder.cpp:7583` 계열과 맞춘다 (**코드 추가**) | B2 |
| B-25 | CSW 로그에 프레임 종류별 구멍이 생긴다. 배열 폭은 125로 그대로지만 BF 진입 프레임은 121에서 124칸이, 미진입 프레임은 1에서 4칸이 초기값 -1로 남는다. DAO는 이 파일을 병합만 하고 수치 판단에 쓰지 않는다 | [decoder.cpp:1919, 7742, 7774](../../../../../../0_LDPC_original/src/decoder.cpp) | [DAO_Main.py:1737-1749](../../../../../SRC/DAO_Main.py) | 문서에 적는다 (**문서**) | B2 |
| B-26 | 수정 후 5.1의 Corner 이벤트가 모드 갈래 밖에 있어 2SD와 3SD 프레임도 HD 전용 플래그를 켠다. 수정 전에는 다섯 호출이 모두 HD 또는 1.5SD 갈래 안이었다. `__CORNER_CHECKER__`가 `mode.h:75`에서 주석이라 지금 빌드 밖이다 | code_diff 5.1 수정 후 마지막 블록 | [decoder.cpp:2092-2126](../../../../../../0_LDPC_original/src/decoder.cpp), [corner.cpp:119-126](../../../../../../0_LDPC_original/src/corner.cpp), [mode.h:75](../../../../../../0_LDPC_original/src/mode.h) | 이벤트 호출을 HD와 1.5SD 갈래 안으로 되돌린다 (**동작 변경**) | B3 |
| B-27 | `Floor_Detect_CSW_TH1`과 `Floor_Detect_CSW_TH2`가 `__HD_FLOOR_SET__`(꺼짐) 안에서만 대입되어 미초기화 상태로 매 iteration 전달된다. 받는 함수가 인자를 쓰지 않아 영향은 없다. 계획과 무관한 기존 상태다 | [decoder.cpp:6982, 494-501, 8108-8113](../../../../../../0_LDPC_original/src/decoder.cpp) | [decoder.h:336-337](../../../../../../0_LDPC_original/src/decoder.h), [mode.h:73](../../../../../../0_LDPC_original/src/mode.h) | 없음 (**사실 기록**) | B1 |
| B-28 | 상위 5.1-4의 "`num_row`를 iteration 수로 간주하는 곳이 있으면 고쳐야 한다"는 실체가 없다. 전수 grep 결과 그런 곳이 하나도 없고, 현 파일도 이미 `num_row` 77에 `MN_num` 124다 | 상위 5.1 항목 4 | `num_row` 히트 전량: [decoder.cpp:6981, 7069](../../../../../../0_LDPC_original/src/decoder.cpp), [ecc_data.h:182](../../../../../../0_LDPC_original/src/ecc_data.h), [local_opt.cpp:22, 39, 43, 75, 79, 101-106, 116, 120, 170](../../../../../../0_LDPC_original/src/local_opt.cpp) | 문서에 "그런 곳은 없다"로 확정한다 (**문서**) | B3 |

### 교차 분석으로 정정된 전제 두 가지

**정정 1: `MN`은 포인터가 아니다.** 워커 셋이 각각 독립으로 확인했다
(B1의 1.4절 덧붙임, B2-10, B3-14). [decoder.h:328](../../../../../../0_LDPC_original/src/decoder.h)의 `MN`은 `int` 스칼라이며
[decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)에서 값을 받고
[decoder.cpp:1120](../../../../../../0_LDPC_original/src/decoder.cpp)의 루프 상한으로 쓰인다.
따라서 `MN = MN + ITER_MAX_HBF`는 포인터 이동이 아니라 상한 연장이다.
리더가 `decoder.h:325-330`을 직접 읽어 확인했다.
이 구분이 B-3의 결론을 정한다. 상한 연장이므로 iteration을 잃는 쪽은 BF 미진입 프레임이 아니라 **BF 진입 프레임**이다.
`int*`인 것은 [ecc_data.h:130](../../../../../../0_LDPC_original/src/ecc_data.h)의 `m_param_dec->MN` 하나뿐이고 이름만 겹친다.

**정정 2: "iteration 121에서 124 미도달"이 row 미사용을 뜻하지 않는다.** B2가 반박했다.
그룹 11은 `type_each_group`이 1, 즉 `GROUP_TYPE_CSW`이고
([common.h:757](../../../../../../0_LDPC_original/src/common.h)) 13개 row 전부가 `iter_start` 105, `iter_end` 124로 같다.
row 선택이 CSW 문턱으로만 갈리므로 iteration 105에서 120만 도는 프레임도 13개 row를 모두 고를 수 있다.
실제 비대칭은 다른 자리에 있다. 문턱 배치상 BF 진입 조건이 `syn_weight < 680`인데
구간 1의 분기 문턱이 1100이라, **그룹 4와 5는 BF 진입 프레임이 절대 고르지 않고 그룹 0, 1, 2는 미진입 프레임이 절대 고르지 않는다**
([common.h:236-244](../../../../../../0_LDPC_original/src/common.h), code_diff 4.1과 5.1 수정 후).
이 갈림 자체는 비AUTO 원본과 같은 결과이므로 결함이 아니지만,
DAO가 그룹 4와 5의 파라미터를 움직여도 `syn_weight >= 1100`인 프레임에만 반영된다는 사실은 최적화 설계에 필요하다.

### 배경 메모와의 대조 (리더 추가)

B-12(BF 진입 시 iteration 1에서 4의 문턱이 무효)는 배경 메모 [msg1.md:21](../../../../../../msg1.md)의
"bf라면 llr matrix에서 threshold를 받지 않아"와 같은 이야기다. 즉 코드 동작은 사용자가 이미 아는 성질이다.
그럼에도 두 문서 어디에도 적혀 있지 않으므로 B-12는 문서 누락으로 유지한다.

---

## ㉰ 문제 없음으로 확인한 범위

| 항목 | 판정 | 확인한 근거 |
|------|------|------------|
| `__RUN_PUNCT_RECOVERY__`([mode.h:61](../../../../../../0_LDPC_original/src/mode.h), 켜짐) | 맞물림 없음 | 살아있는 본체가 `if (iter == 0)` 하나로 묶여 있고([decoder.cpp:3011](../../../../../../0_LDPC_original/src/decoder.cpp)) `VN_Cal_Pre` 계열은 iteration 번호를 보지 않는다. 히트 전량을 워커 문서 1.1절에 실었다 |
| `__SHUFFLED_DUAL_DIAG__`([mode.h:65](../../../../../../0_LDPC_original/src/mode.h), 켜짐) | 맞물림 없음 | 히트가 `encoder.cpp:60, 87` 둘뿐이고 복호기에 닿지 않는다 |
| `__PMU_READ__`([mode.h:66](../../../../../../0_LDPC_original/src/mode.h), 켜짐) | 맞물림 없음 | `PMU_SRAM`이 column 축과 edge 축으로만 색인되고 iteration 축이 없다([decoder.cpp:179-184, 5836-5865](../../../../../../0_LDPC_original/src/decoder.cpp)) |
| `__HALF_COL_UPDATE__`와 `__HALF_COL_MODIFIED__`([mode.h:68, 70](../../../../../../0_LDPC_original/src/mode.h), 둘 다 켜짐) | 겹치지만 결함 아님 | 1bit precision 조건 두 곳(`decoder.cpp:4056`, `4275`)을 code_diff 7.3이 함께 덮는다. HCU 그룹 교번 여덟 곳이 모두 `(G_idx + mn) % 2` 형태이고 `ITER_MAX_HBF` 4가 짝수라 mn 도약이 패리티를 보존한다 |
| `PARAM_LLR` 구조체에 멤버 셋 삽입 (code_diff 2.1) | 안전 | `sizeof(PARAM_LLR)`와 `memcpy` 히트 0건, 전달은 전부 포인터, MPI는 개별 배열만 원소 수를 명시해 보낸다. 정의는 [ecc_data.h:179](../../../../../../0_LDPC_original/src/ecc_data.h) 한 곳뿐 |
| 상위 6.2절이 든 다섯 곳 | 서술이 맞다 | `VN_Cal_HD`, `VN_Cal_HD_HCU`, `VN_Cal_CD`, `VN_Cal_SD`, `VN_Cal_SD_HCU` 다섯 곳을 모두 읽어 형태가 문자 그대로 같음을 확인. 수정 후에도 갈림이 그대로다 |
| `syn_th_BF`, `syn_th_BF1`, `syn_th_5_8_Set_0`, `syn_th_5_8_Set_1` 참조 | 모두 덮인다 | 전수 히트가 `decoder.h:301, 303, 305, 306`과 `decoder.cpp:468, 472, 480, 483, 489, 492, 2099, 2116`이며 code_diff 2.2, 4.1, 5.1이 전부 덮는다. `local_opt.cpp`, `ecc_top.cpp`, `corner.cpp`, `TV_*`에는 히트가 없다 |
| `decoder.cpp:2328`의 `iter - 1` | 반박됨 (설계다) | 함수 머리 주석([decoder.cpp:2290-2291](../../../../../../0_LDPC_original/src/decoder.cpp))이 SD와 HD의 시점 차이를 명시한다. 호출처 8곳 전수 확인. 파일 `restart_iter`와 한 칸 어긋나는 새 경로는 생기지 않는다 |
| `syn_weight`, `psyn_weight`, `prev_CSW`, `flag_BF_on`, `state_hd_error_floor_set`, `num_sw_branch[]`, `syn_th_sw_branch[][]`, `MN_old`의 프레임 간 누수 | 반박됨 | 각각 프레임마다 새로 정해지거나 `Clear_Flag`가 지우거나 `Init_Dec_Option`이 한 번만 채우는 상수다. `Select_BF`는 `syn_weight` 계산보다 뒤에 불리고 `Get_Cur_LLR_Idx_FILE`은 `mn > 0`에서만 불려 순서가 어긋나지 않는다 |
| `num_row`와 `MN_num`의 대소 | 무해 | 두 배열을 따로 잡고 `num_row`를 iteration 수로 쓰는 곳이 없다 (B-28) |
| `MN[]` 값이 배열 index로 쓰이는 곳 | 없다 | 음수 index 접근은 발생하지 않는다. 값에서 index를 만드는 유일한 곳은 histogram이고 그것도 `o_iter_num` 기반이다 |
| 로그 배열 경계 | 안전 | `MN_size = 120 + 4 + 1 = 125`이고 mn 최대가 124다. `crc_dec_LFSR_iter`도 `real_mn - 1` 최대 119로 안전. B1과 B2가 독립으로 같은 값을 냈다 |
| DAO의 결과 파일 파싱 | 깨지지 않는다 | 열 개수가 `MN_num` 124로 그대로이고 음수 머리글은 DAO가 읽지 않는 파일과 stdout에만 간다. DAO가 읽는 `result_4KB_*.txt`에는 데이터 줄만 들어간다 |
| 상위 2장 표와 3장 CSW 표 | 파일과 일치 | 그룹 12줄과 CSW 나열 네 줄을 파일에서 손으로 세어 전부 일치. row 20칸 구성(16 LLR + `CSW_thr` + `iter_start` + `iter_end` + 마지막 칸)이 `local_opt.cpp:106-115`와 정확히 대응. 리더가 `local_opt.cpp:101-115`를 직접 읽어 재확인 |

---

## ㉱ 미커버 영역

- ㉮ 실제 H-matrix가 이 저장소에 없어 `m_PCM->ColW[jj]`의 차수 분포를 알 수 없다. B-18(dv 그룹에 걸리지 않는 차수의 조용한 대체)이 실제로 일어나는지는 미확인이다
- ㉯ `__12META__`가 정의된 빌드의 SW 문턱 상수([common.h:202-229](../../../../../../0_LDPC_original/src/common.h))는 읽지 않았다. code_diff 4.1이 대입하는 값이 그 갈래에서 어떻게 달라지는지 미확인이다
- ㉰ `TV_Dec.cpp`, `TV_Enc.cpp`, `TV_Dec_Inter.cpp`는 `flag_HD_*`와 `syn_th_*` 히트가 없음을 확인한 선에서 멈췄다. `ITER_MAX_HBF` 4가 TV 출력 시점이나 hex 포맷에 미치는 영향은 보지 않았다
- ㉱ MPI를 켠 빌드에서 각 rank가 파일을 따로 읽는지는 이 저장소에서 답이 정해지지 않는다 (B-19). code_diff 3.7의 물음은 외부 빌드에서 확인해야 한다
- ㉲ `Select_SW_Branch`가 분기 셋 이상을 다룰 때의 문턱 출처는 상위 7장 ㉯의 미결정 사항이라 대안을 평가하지 않았다
- ㉳ 파일 변환 절차(현 파일에서 code_diff가 전제하는 분기 전용 줄이 있는 형태로)는 이 팀의 배정 밖이라 다루지 않았다
