# 팀 V3 검증: iteration 번호 체계, 결과 파일, 파일 변환 (R2-5, R2-6, R2-8)

작성: 2026-09-03 01:52:12

> 팀 리더: 팀 V3 리더 에이전트
> 워커: [worker_V3_1.md](worker_V3_1.md)(R2-5 사실 축), [worker_V3_2.md](worker_V3_2.md)(R2-5 처방 네 갈래와 R2-8 전체), [worker_V3_3.md](worker_V3_3.md)(R2-6 사실과 처방)
> 리더가 직접 읽어 확정한 소스: [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp) 45-184,
> [decoder.cpp](../../../../../../0_LDPC_original/src/decoder.cpp) 498-515, 1108-1125, 1935-2004, 2082-2130, 4950-5299, 5300-5362, 6973-7073,
> [ecc_top.cpp](../../../../../../0_LDPC_original/src/ecc_top.cpp) 870-900, 2006-2060, 2224-2290,
> [main.cpp](../../../../../../0_LDPC_original/src/main.cpp) 45-75,
> [DAO_Main.py](../../../../../SRC/DAO_Main.py) 1840-1940, 7925-8005, 8187-8273,
> [DAO_LLR_MATRIX.py](../../../../../SRC/DAO_LLR_MATRIX.py) 115-200, 335-355, 470-540,
> [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 전체,
> [code_diff.md](../../code_diff.md) 3장과 6.2

용어: LLR(Log Likelihood Ratio, 로그 우도비), FER(Frame Error Rate, 프레임 오류율), BF(Bit Flipping, 비트 뒤집기),
HD(Hard Decision, 경판정), SD(Soft Decision, 연판정), SW(Syndrome Weight, 신드롬 무게), CSW(Check Sum Weight),
DAO(Decoder Auto Optimizer), MPI(Message Passing Interface, 프로세스 사이 메시지 전달 규격),
UB(Undefined Behavior, 정의되지 않은 동작), CRC(Cyclic Redundancy Check, 순환 중복 검사).

리뷰 대상은 코드가 아니라 코드 수정 계획 문서 두 개다. "수정 후 코드"는 [code_diff.md](../../code_diff.md)의
수정 후 블록을 그대로 적용한 상태를 뜻한다.

---

## ㉮ 가설 목록

### R2-5: `ITER_MAX_HBF` 4가 `MN[]`과 결과 파일과 iteration 예산을 바꾼다

사실 가설:

- ㉠ **H5-A**: `ITER_MAX_HBF`가 4일 때 [local_opt.cpp:116-131](../../../../../../0_LDPC_original/src/local_opt.cpp)의
  보정이 `MN[]`을 `[4, -3, -2, -1, 0, ..., 118, 120]`으로 만든다
- ㉡ **H5-B**: 그 결과 [ecc_top.cpp:877-879](../../../../../../0_LDPC_original/src/ecc_top.cpp)의
  iteration별 FER 집계에서 열 1~3이 1.0으로 고정되고
  [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 머리글에 음수가 찍힌다
- ㉢ **H5-C**: 실행 iteration이 124회에서 120회로 줄고 BF 진입 프레임이 파일의 121~124 row에 닿지 못한다
- ㉣ **H5-D**: `Check_End_Iter`가 mn 0에서 성공을 돌려주면
  [decoder.cpp:1973-1979](../../../../../../0_LDPC_original/src/decoder.cpp)의 `iter_num -= ITER_MAX_HBF`가
  `iter_num`을 -4로 만든다
- ㉤ **H5-E**: `iter_num` 보정이 DAO가 읽는 `avg_iteration` 척도를 바꾼다

처방 가설:

- ㉠ **P5-㉮**: 보정식을 음수가 나오지 않게 고치면 결과 파일 열이 정상으로 돌아오고 새 문제가 생기지 않는다
- ㉡ **P5-㉯**: AUTO에서도 비AUTO처럼 검사점 다섯 개로 바꾸면 문제가 해결되고 DAO 파싱이 깨지지 않는다
- ㉢ **P5-㉰**: 배열을 그대로 두고 열 배치를 문서에 적으면 문제가 실질적으로 닫힌다
- ㉣ **P5-㉱**: mn 0 종료 경로에서 보정을 건너뛰면 `iter_num` 음수가 해결되고 새 문제가 생기지 않는다

### R2-6: 변환된 파일을 전제하는데 변환 절차와 파일이 없다

사실 가설:

- ㉠ **H6-A**: 현재 [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)를
  code_diff 3.2의 수정 후 파서에 넣으면 분기 줄이 restart 줄부터 읽혀 이후 헤더가 밀리고 row가 12토큰씩 어긋난다
- ㉡ **H6-B**: DAO의 Python 파서([DAO_LLR_MATRIX.py:476-537](../../../../../SRC/DAO_LLR_MATRIX.py))가
  줄 index 기반이라 새로 넣은 분기 줄을 `num_restart`로 읽는다
- ㉢ **H6-C**: `Is_LLR_Valid`의 RW2 검사([DAO_LLR_MATRIX.py:344-345](../../../../../SRC/DAO_LLR_MATRIX.py))가
  `floor_flag == -1`을 강제해 type을 전부 1로 바꾼 형태를 거부한다

처방 가설:

- ㉠ **P6**: 9장 2단계 앞에 파일 변환 단계를 넣고 변환된 파일을 함께 두면 문제가 해결되고 새 문제가 생기지 않는다.
  전제로 C++ 토큰 기반 파서와 DAO 줄 index 기반 파서가 동시에 받을 수 있는 헤더 배치가 존재해야 한다

### R2-8: 대조 검사의 실패가 어디에도 닿지 않는다

사실 가설:

- ㉠ **H8**: code_diff 3.4의 `err = TRUE`는 읽는 곳이 없고 함수가 void이며,
  `printf`는 DAO가 읽는 파일에 남지 않고, [main.cpp:69](../../../../../../0_LDPC_original/src/main.cpp)가
  `return 0` 고정이라 종료 코드로도 알 수 없다. 결과로 어긋난 파일에서 DAO 최적화가 그대로 진행된다

처방 가설:

- ㉠ **P8**: 검사 실패 시 프로세스를 멈추거나 종료 코드를 바꾸고 DAO가 그것을 읽게 하면
  검사가 실효를 얻고 새 문제가 생기지 않는다

---

## ㉯ 증거 확인 결과

### R2-5 사실 축

| # | 증거 | 판정 | 근거 | 확인 |
|---|------|------|------|------|
| 5-1 | `MN_num`은 파일 마지막 row의 `iter_end`이며 값은 124 | 확인됨 | [local_opt.cpp:116](../../../../../../0_LDPC_original/src/local_opt.cpp), [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 105행의 `iter_end` 124. code_diff 3.5의 새 식(전체 최댓값)도 같은 값 | V3_1, 리더 |
| 5-2 | 보정 전 `MN` = [0, 1, ..., 122, 124], 보정 후 `MN` = [4, -3, -2, -1, 0, ..., 118, 120] | 확인됨 | [local_opt.cpp:118-131](../../../../../../0_LDPC_original/src/local_opt.cpp) 손 실행 | V3_1, V3_2, 리더 |
| 5-3 | code_diff 3.5가 124-131 보정 블록을 다루지 않아 블록이 그대로 남는다 | 확인됨 | [code_diff.md 3.5](../../code_diff.md#ch3)의 수정 후 코드가 116-123만 대체 | 리더 |
| 5-4 | 집계식은 `if (o_iter_num > MN[n]) fr_4KB[n]++`이고 루프는 `n < MN_num - 1` | 확인됨 | [ecc_top.cpp:876-880](../../../../../../0_LDPC_original/src/ecc_top.cpp) | V3_1, V3_2, 리더 |
| 5-5 | **1.0 고정 열은 셋이 아니라 넷(index 1~4)이다** | **반박됨** (Round 2 정정) | `MN[4]` = 0이고 `o_iter_num >= 1`이 항상 성립하므로 `o_iter_num > 0`도 항상 참. 비교가 엄격한 `>`다 ([ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp)) | V3_1, V3_2, 리더 |
| 5-6 | 머리글에 음수가 찍힌다 | 확인됨 | [ecc_top.cpp:2052-2056](../../../../../../0_LDPC_original/src/ecc_top.cpp)이 `MN[n]`을 그대로 출력 | V3_1, V3_2, 리더 |
| 5-7 | **음수 머리글은 DAO가 읽는 파일에 들어가지 않는다** | 확인됨 (Round 2 보강) | 머리글은 `Ref_C_result_%d.txt` 전용이고, DAO는 이 이름을 [DAO_Constants.py:129](../../../../../SRC/DAO_Constants.py)의 삭제 목록에 두고 [DAO_Main.py:946-957](../../../../../SRC/DAO_Main.py)에서 지운다. 읽는 코드 없음 | V3_1, V3_2 |
| 5-8 | 메인 루프 상한은 `MN[MN_num-1]`이고 `for (mn = 0; mn < MN + 1; mn++)`이다 | 확인됨 | [decoder.cpp:1118-1120](../../../../../../0_LDPC_original/src/decoder.cpp) | 리더 |
| 5-9 | 실행 iteration이 124회에서 120회로 준다 (진입 프레임 mn 1~120, 미진입 mn 5~124) | 확인됨 | [decoder.cpp:2097-2098](../../../../../../0_LDPC_original/src/decoder.cpp)의 `mn += ITER_MAX_HBF`, `MN += ITER_MAX_HBF` | V3_1, V3_2, 리더 |
| 5-10 | **"파일의 121~124 row에 닿지 않는다"는 실체가 없다** | **반박됨** (Round 2 정정) | 파일 row는 77개이고 iteration으로 색인되지 않는다. 마지막 그룹 11은 13개 row가 모두 `iter_start` 105, `iter_end` 124이고 `type_each_group[11]` = 1 = `GROUP_TYPE_CSW`다. [decoder.cpp:7052-7062](../../../../../../0_LDPC_original/src/decoder.cpp)가 이 그룹의 row를 `prev_CSW`로만 고르므로 iteration 상한이 120으로 줄어도 **도달 불가가 되는 row는 없다**. 어느 그룹의 `iter_start`도 121 이상이 아니다 (최댓값 105) | V3_1, 리더 |
| 5-11 | mn 0에서 `Check_End_Iter`가 호출되지 않는다 | 확인됨 | [decoder.cpp:1947-1951](../../../../../../0_LDPC_original/src/decoder.cpp)의 `if (mn == 0) { CRC_flag = FLAG_HIGH; } else { ... Check_End_Iter ... }` | V3_1, V3_2, 리더 |
| 5-12 | `Jump_Iter`는 호출되지 않는다 | 확인됨 | [decoder.cpp:506, 509](../../../../../../0_LDPC_original/src/decoder.cpp)가 AUTO와 비AUTO 두 갈래에서 모두 `power_index = MODE_POWER_STOPPING_OFF`. 호출은 [decoder.cpp:1961-1965](../../../../../../0_LDPC_original/src/decoder.cpp)의 `MODE_POWER_STOPPING_ON` 안 | 리더, V3_1, V3_2 |
| 5-13 | `iter_num`을 쓰는 곳은 `Check_End_Iter` 둘과 `Jump_Iter` 다섯뿐이다 | 확인됨 | grep `iter_num` 히트 [decoder.cpp:4965, 5077, 5105, 5205, 5273, 5344, 5355](../../../../../../0_LDPC_original/src/decoder.cpp). 앞 다섯은 `Jump_Iter` 안, 뒤 둘은 `Check_End_Iter` 안 | 리더 |
| 5-14 | **`iter_num`은 항상 1 이상이며 -4가 되는 경로가 없다** | **반박됨** (Round 2 항목 소멸) | 5-11, 5-12, 5-13의 결합. 루프는 늦어도 `mn == MN`에서 `Check_End_Iter`가 TRUE를 돌려 `iter_num = mn`을 남기고 끝난다. `real_mn`도 mn 0 본문의 [decoder.cpp:1966](../../../../../../0_LDPC_original/src/decoder.cpp)에서 1이 되므로 5315행의 `real_mn - 1` 색인도 음수가 되지 않는다 | 리더, V3_1, V3_2 |
| 5-15 | **DAO의 결과 파서는 `Read_Ref_C_Result`이고 `Read_FER_From_File`은 호출자가 없는 죽은 코드다** | 확인됨 (Round 2와 context 인용 정정) | [DAO_Main.py:8187-8273](../../../../../SRC/DAO_Main.py) 정의, 호출 [1824, 1851](../../../../../SRC/DAO_Main.py). `Read_FER_From_File`([7969](../../../../../SRC/DAO_Main.py)) 전수 grep 히트는 정의뿐 | V3_1, V3_2, 리더 |
| 5-16 | DAO가 판정에 쓰는 FER은 `MN[]`과 무관하다 | 확인됨 | `FER_value = total_errors / total_tests`([DAO_Main.py:1885](../../../../../SRC/DAO_Main.py)). `total_errors`는 `parts[2]` 곧 C++의 `fr[MN_num-1]`이고 이는 [ecc_top.cpp:874-876](../../../../../../0_LDPC_original/src/ecc_top.cpp)에서 `o_CRC_flag`로만 센다 | V3_1, V3_2, 리더 |
| 5-17 | iteration별 FER 열은 DAO에서 로그에만 쓰인다 | 확인됨 | `total_num_error_per_iters`와 `total_FER_per_iters`의 전수 히트 6개 가운데 소비는 [DAO_Main.py:7595-7596](../../../../../SRC/DAO_Main.py)의 로그 문자열뿐 | V3_2, 리더 |
| 5-18 | DAO가 읽는 `avg_iteration`은 C++의 `iter_num`에서 오고 판정에 쓰인다 | 확인됨 | [DAO_Main.py:8246](../../../../../SRC/DAO_Main.py)의 `avg_iteration = float(parts[result_offset])`, [1886, 1935-1937](../../../../../SRC/DAO_Main.py). 비교는 [2541-2544](../../../../../SRC/DAO_Main.py)(`ENABLE_AVG_ITER_UPDATE` 기본 False)와 [6076-6085](../../../../../SRC/DAO_Main.py)(REORDER_GROUP 모드, 조건 없음) | V3_1, V3_2, 리더 |

### R2-5 처방 축

| # | 증거 | 판정 | 근거 | 확인 |
|---|------|------|------|------|
| 5P-1 | 보정 블록은 검사점 배열 보정과 iteration 상한 축소 두 일을 겹쳐 한다 | 확인됨 | 소비처가 [ecc_top.cpp:878](../../../../../../0_LDPC_original/src/ecc_top.cpp)(배열)와 [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)(상한)로 완전히 다르다 | V3_2 |
| 5P-2 | 상한 축소를 버리면 `type_each_group[-1]` 범위 밖 읽기가 난다 | 확인됨 (Round 2보다 무겁다) | `MN`이 124로 남으면 미진입 프레임이 128까지 돌아 `selected_group`이 -1로 남고, [decoder.cpp:7048-7051](../../../../../../0_LDPC_original/src/decoder.cpp)이 `printf` 뒤 그대로 `type_each_group[selected_group]`을 읽는다 | V3_2 |
| 5P-3 | P5-㉮의 세 후보 모두 상한 120을 유지한다 | 확인됨 | 후보 ㉠ 마지막 원소만 보정, ㉡ `MN_num`까지 축소, ㉢ 음수 clamp | V3_2 |
| 5P-4 | 후보 ㉢(음수 clamp)은 실체를 고치지 못한다 | 확인됨 | `MN` = [4, 0, 0, 0, 0, 1, ...]이 되어 열 1~4가 여전히 1.0 고정 | V3_2 |
| 5P-5 | 후보 ㉠(마지막 원소만 보정)은 새 부작용을 만든다 | 확인됨 | `MN` = [0, 1, ..., 122, 120]이 되어 단조가 깨지고 `MN[n]`이 120 이상인 열 세 개가 항상 0.0이 된다 | V3_2 |
| 5P-6 | **DAO 파싱은 결과 파일 열 수 변경을 견딘다** | 확인됨 (Round 2의 "DAO 파싱까지 영향" 과장 정정) | 열 수를 코드가 고정하지 않고 `parts[result_offset:-3]`으로 파일에서 추론한다([DAO_Main.py:8244](../../../../../SRC/DAO_Main.py)). 길이 불일치는 [8241](../../../../../SRC/DAO_Main.py)과 [1831-1836, 1856](../../../../../SRC/DAO_Main.py)에서 이미 방어된다 | V3_2, 리더 |
| 5P-7 | 비AUTO 검사점은 상수 다섯 개이며 마지막이 `ITER_MAX_HD_PRIME` 120으로 못박힌다 | 확인됨 | [main.cpp:704-781](../../../../../../0_LDPC_original/src/main.cpp) `Set_Ref_C_Iteration`, `#ifndef __AUTO_LLR_OPT__` 안 | V3_2 |
| 5P-8 | 비AUTO 상수 배열을 그대로 가져오면 파일 기반 iteration 예산이 무너진다 | 확인됨 | 상한이 [decoder.cpp:1118](../../../../../../0_LDPC_original/src/decoder.cpp)의 마지막 원소라 파일의 `iter_end`가 무시된다. `MN_size` 로그 버퍼와 histogram 크기도 파일과 무관해진다 | V3_2 |
| 5P-9 | P5-㉱의 대상(mn 0 종료)이 존재하지 않는다 | 확인됨 | 5-14와 같다 | 리더, V3_1, V3_2 |
| 5P-10 | 보정 자체는 두 프레임 종류의 척도를 맞추는 정규화라 유지가 옳다 | 확인됨 | 진입 프레임 mn 1~120, 미진입 mn 5~124를 모두 1~120 척도로 맞춘다 | V3_2 |
| 5P-11 | `MN[n]` 중간 원소를 읽는 소비처는 네 곳뿐이다 | 확인됨 | [ecc_top.cpp:878, 2022, 2054](../../../../../../0_LDPC_original/src/ecc_top.cpp), [main.cpp:317](../../../../../../0_LDPC_original/src/main.cpp). 나머지 히트는 모두 `MN[MN_num-1]`이나 `MN_size` 루프 | V3_2 |

### R2-6

| # | 증거 | 판정 | 근거 | 확인 |
|---|------|------|------|------|
| 6-1 | 파일은 105줄, 데이터 row 77개, 토큰 1584개이며 현행 파서와 정확히 맞는다 | 확인됨 | 헤더 44토큰 + 77 × 20 = 1584. 손 실행 | V3_1, V3_3, 리더 |
| 6-2 | 3.2 신규 반복문이 토큰 12개를 앞당겨 먹는다 | 확인됨 | `sw_branch_idx_each_group`이 13행 `0`, 15행 `31 31 31 31`, 16행 `0 0 0 0`, row 0의 앞 세 칸을 담아 `[0, 31, 31, 31, 31, 0, 0, 0, 0, 21, 0, 0]`이 된다 | V3_3, 리더 |
| 6-3 | 밀림 폭이 정확히 상수 12토큰이다 | 확인됨 (Round 2 표현 정확) | 손 실행 대조 | V3_3, 리더 |
| 6-4 | 마지막 12회의 `fscanf`가 파일 끝을 넘고 반환값을 아무도 검사하지 않는다 | 확인됨 | [local_opt.cpp](../../../../../../0_LDPC_original/src/local_opt.cpp)의 `fscanf` 14곳 모두 반환값을 버린다 | V3_3 |
| 6-5 | **code_diff 6.2 ㉯ "지금 형태의 파일을 넣으면 여기서 걸린다"가 사실이 아니다** | **반박됨** | 밀린 뒤 type 20, 21 그룹은 분기 index 31이거나 iteration 구간이 비어 후보에서 영구히 빠지므로 `[Error] (3)`이 도달 불가 코드가 된다. 실제로 나오는 것은 3.4 대조 오류와 6.2 `(1)` 두 종류다 | V3_3 |
| 6-6 | 밀린 `iter_end` 최댓값이 11이라 `MN_num`이 124에서 11로, 상한이 120에서 7로 무너진다 | 확인됨 (Round 2가 못 본 사실) | 3.5의 새 식(전체 최댓값)에 밀린 값을 넣은 결과. 멈추지 않고 조용히 완주한다 | V3_3 |
| 6-7 | 3.2를 넣고 3.5를 함께 넣지 않으면 `MN_num`이 -1이 되어 `new int[-1]`로 즉사한다 | 확인됨 (Round 2가 못 본 사실) | 옛 식은 `iter_end[num_row-1]`을 쓰는데 밀린 마지막 row의 그 칸이 -1이다 | V3_3 |
| 6-8 | **3.2 수정은 구 형태 파일까지 깨뜨린다** | 확인됨 (Round 2가 못 본 사실) | 저장소가 추적하는 `Prime_ECC_2.3`과 `2.4`의 `LLR_MATRIX_0.txt`가 3토큰 밀려 `sw_branch_idx_each_group = [1, 2, 31]`이 된다 (R2-10이 든 예와 같은 자리) | V3_3 |
| 6-9 | DAO 파서는 줄 index 기반이며 `type_each_group` 다음 줄을 무조건 `num_restart`로 읽는다 | 확인됨 | [DAO_LLR_MATRIX.py:483-485](../../../../../SRC/DAO_LLR_MATRIX.py)의 순차 `idx_line` | V3_3, 리더 |
| 6-10 | 분기 줄을 헤더에 넣은 형태는 DAO에서 예외 없이 한 줄 밀린 뒤 원인과 무관한 메시지로 거부된다 | 확인됨 | `max_value length mismatch`로 나온다. 마지막 row 하나가 잘린다 | V3_3 |
| 6-11 | `Is_LLR_Valid` RW2가 `floor_flag != -1`을 거부한다 | 확인됨 | [DAO_LLR_MATRIX.py:343-346](../../../../../SRC/DAO_LLR_MATRIX.py)의 `if row.floor_flag != -1: return False` | V3_3, 리더 |
| 6-12 | 현재 파일은 이미 마지막 칸에 분기 index를 담고 있어 RW2를 통과하지 못한다 | 확인됨 | 77개 row의 마지막 칸 분포가 -1 51개, 0 14개, 1 12개 | 리더 |
| 6-13 | 구 형태 파일은 두 파서를 모두 통과한다 | 확인됨 | | V3_3 |
| 6-14 | **두 파서가 동시에 받는 배치가 존재한다** | 확인됨 (Round 2 미커버 항목의 답) | ㉮ 분기 줄을 모든 row 뒤 마지막 줄로 두면 DAO는 [DAO_LLR_MATRIX.py:510](../../../../../SRC/DAO_LLR_MATRIX.py)의 슬라이싱으로 잉여 줄을 무시한다. ㉯ row의 마지막 칸만 쓰면 파일 줄 배치가 구 형태와 같다 | V3_3 |
| 6-15 | **어느 배치를 골라도 DAO를 고치지 않고는 되지 않는다** | 확인됨 | RW2([344-346](../../../../../SRC/DAO_LLR_MATRIX.py))와 G2([305-312](../../../../../SRC/DAO_LLR_MATRIX.py))가 분기 구조 자체를 거부한다 | V3_3 |
| 6-16 | **DAO는 trial마다 LLR matrix를 새로 쓰며 쓰기 경로에 분기 줄 자리가 없다** | 확인됨 (처방을 무너뜨리는 사실) | `Save_LLR_Matrix` 호출 9곳([DAO_Main.py:2013, 2338, 2340, 8461, 9137, 9584, 9587, 9624, 9909](../../../../../SRC/DAO_Main.py)). `Build_LLR_Matrix_Output_Lines`([DAO_LLR_MATRIX.py:122-145](../../../../../SRC/DAO_LLR_MATRIX.py))가 `type_each_group` 다음에 바로 `num_restart`를 적고 `LLR_Header`에 분기 필드가 없다. row 마지막 칸은 [193](../../../../../SRC/DAO_LLR_MATRIX.py)이 보존한다 | V3_3, 리더 |

### R2-8

| # | 증거 | 판정 | 근거 | 확인 |
|---|------|------|------|------|
| 8-1 | `err`의 참조는 선언과 대입 둘뿐이고 읽는 곳이 없다 | 확인됨 | [local_opt.cpp:56](../../../../../../0_LDPC_original/src/local_opt.cpp) 선언, [140](../../../../../../0_LDPC_original/src/local_opt.cpp) 대입. 전수 grep 히트 2 | V3_2, 리더 |
| 8-2 | `Read_LLR_info_Auto`는 void다 | 확인됨 | [local_opt.cpp:52](../../../../../../0_LDPC_original/src/local_opt.cpp) 정의, [Local_Opt.h:23](../../../../../../0_LDPC_original/src/Local_Opt.h) 선언 | V3_2 |
| 8-3 | code_diff가 `err`를 읽는 코드를 추가하지 않는다 | 확인됨 | [code_diff.md](../../code_diff.md) 전체에서 `err` 히트가 3.4의 한 줄뿐 | V3_2, 리더 |
| 8-4 | **140행의 `if (NULL == matrix_in)` 검사는 `fclose` 뒤에 있어 이미 도달 불가에 가깝다** | 확인됨 (Round 2 보강) | `fopen`은 [60](../../../../../../0_LDPC_original/src/local_opt.cpp), 첫 `fscanf`는 [61](../../../../../../0_LDPC_original/src/local_opt.cpp), `fclose`는 [132](../../../../../../0_LDPC_original/src/local_opt.cpp), 검사는 [139](../../../../../../0_LDPC_original/src/local_opt.cpp). 열리지 않았다면 61행에서 이미 널 포인터 역참조로 죽는다 | V3_2, 리더 |
| 8-5 | DAO의 EXE 실행에 `stdout`, `stderr`, `capture_output` 인자가 없다 | 확인됨 | [DAO_Main.py:7937, 7939](../../../../../SRC/DAO_Main.py). `check=True`와 `timeout`만 있다 | V3_2, 리더 |
| 8-6 | EXE 실행 지점은 두 곳뿐이다 | 확인됨 | `subprocess\.`, `os.system`, `Popen` 전수. 히트는 [898](../../../../../SRC/DAO_Main.py)(빌드, 이쪽만 `capture_output=True`), [7937, 7939](../../../../../SRC/DAO_Main.py) | V3_2 |
| 8-7 | `main`은 `return 0` 고정이며 `Setup`의 오류도 버린다 | 확인됨 (Round 2 보강) | [main.cpp:60-69](../../../../../../0_LDPC_original/src/main.cpp). `err = Setup(...)`으로 받고도 69행이 0을 돌려준다 | 리더, V3_2 |
| 8-8 | 저장소 소스 전체에 `exit`, `abort`, `EXIT_FAILURE`, `assert`가 하나도 없다 | 확인됨 | [0_LDPC_original/src](../../../../../../0_LDPC_original/src) 전수 grep 히트 0 | V3_2 |
| 8-9 | `printf`는 DAO가 읽는 어떤 파일에도 남지 않는다 | 확인됨 | 배치 스크립트에 리다이렉션 없음([DAO_Main.py:6557-6567](../../../../../SRC/DAO_Main.py)), `Ref_C_result_*.txt`는 DAO의 삭제 대상 | V3_2 |
| 8-10 | 0이 아닌 종료 코드는 `CalledProcessError`로 올라와 `MPI_Abort`가 DAO 전체를 끝낸다 | 확인됨 | Linux 배치가 `set -euo pipefail`([DAO_Main.py:6565](../../../../../SRC/DAO_Main.py)), 예외 처리 [7951-7952](../../../../../SRC/DAO_Main.py), `comm.Abort` [6812](../../../../../SRC/DAO_Main.py) | V3_2 |
| 8-11 | **AUTO 빌드에서 `__RUN_MPI__`가 정의되지 않아 C++ 쪽 MPI 전파 걱정은 실체가 없다** | 확인됨 | [mode.h:18-27](../../../../../../0_LDPC_original/src/mode.h)에서 `__AUTO_LLR_OPT__`를 정의한 바로 다음 줄이 `#if !defined(__AUTO_LLR_OPT__)`라 항상 거짓이다. DAO의 MPI는 Python 계층(mpi4py)이고 각 rank가 단일 프로세스 EXE 하나를 부른다 | V3_2 |
| 8-12 | 3.4 검사는 변환된 정상 파일에서 오탐을 내지 않는다 | 확인됨 | [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)의 row 마지막 칸이 그룹 안에서 모두 균일하다 (그룹 0, 1은 0, 그룹 2는 1, 그룹 3은 0, 그룹 4, 5는 1, 그룹 6~11은 -1) | V3_2, 리더 |
| 8-13 | 변환 전 파일에서는 3.4가 반드시 걸리므로 P8을 먼저 넣으면 첫 실행이 즉시 중단된다 | 확인됨 | 6-2와 8-12의 결합 | V3_2, V3_3 |

---

## ㉰ 판정 표

| 발견 | 사실 판정 | 처방 판정 | 심각도 재판정 |
|------|----------|----------|--------------|
| **R2-5** | **부분 확인.** `MN[]` 값(5-2), 열 포화(5-4, 5-5), 머리글 음수(5-6), iteration 124회에서 120회(5-9), `avg_iteration` 척도 변경(5-18)은 확인됐다. 세 곳을 정정한다. ㉮ 1.0 고정 열은 셋이 아니라 **넷**(index 1~4)이고 원본에서도 이미 열 0 하나가 1.0이었으므로 실제 변화는 한 개에서 네 개다(5-5). ㉯ **"파일의 121~124 row 미도달"은 반박됨**. 마지막 그룹이 `GROUP_TYPE_CSW`라 row가 iteration으로 색인되지 않아 도달 불가가 되는 row가 없다. 실체는 실행 iteration 네 회 감소다(5-10). ㉰ **"mn 0 종료 프레임 `iter_num` -4"는 반박됨.** mn 0에서 `Check_End_Iter`가 불리지 않고 `Jump_Iter`는 power stopping이 꺼져 있어 불리지 않는다(5-14) | ㉮ **처방 수정 필요.** 후보 셋 가운데 `MN_num`까지 함께 줄이는 안만 깨끗하다. 음수 clamp는 열 포화를 못 고치고, 마지막 원소만 보정하면 뒤쪽 열 세 개가 항상 0.0이 되는 새 부작용이 생긴다(5P-3~5P-5). ㉯ **처방 수정 필요.** "마지막 원소는 파일 값을 유지한다"를 함께 적어야만 성립한다. 비AUTO 상수 배열을 그대로 가져오면 파일 기반 iteration 예산이 무너진다(5P-8). 다만 **Round 2가 든 "결과 파일 열 수 변경으로 DAO 파싱까지 영향"은 과장이다.** DAO는 열 수를 파일에서 추론하고 길이 불일치를 이미 방어한다(5P-6). ㉰ **처방 유효.** 열 배치는 문서로 닫힌다. iteration별 FER 열은 DAO 로그에만 쓰이고 판정에 들어가지 않는다(5-16, 5-17). ㉱ **처방 반대.** 대상이 도달 불가이므로 조건을 덧붙이면 없는 상황을 위해 정규화 코드를 복잡하게 만들 뿐이다. 보정 자체는 두 프레임 종류의 척도를 맞추는 정규화라 유지가 옳다(5P-9, 5P-10) | **HIGH → MEDIUM.** HIGH를 지탱하던 두 근거(`iter_num` 음수, row 미도달)가 모두 반박됐다. 남는 것은 사람이 읽는 지표의 왜곡(열 넷과 머리글 음수, DAO가 읽지 않는 파일)과 `avg_iteration` 절대 척도 변경, 실행 iteration 네 회 감소다. 척도 변경은 비교되는 두 matrix가 같은 빌드에서 측정되므로 DAO 순위를 계통적으로 뒤집지 않는다. 실행 iteration 감소는 실재하는 동작 변경이므로 MEDIUM 아래로는 내리지 않는다 |
| **R2-6** | **확인됨 (사실이 Round 2보다 무겁다).** 밀림 폭이 정확히 12토큰이라는 표현까지 정확하다(6-3). Round 2가 못 본 세 가지가 더 나왔다. ㉮ 밀린 값으로 `MN_num`이 124에서 11로, 상한이 120에서 7로 무너지면서도 멈추지 않고 조용히 완주한다(6-6). ㉯ 3.2만 넣고 3.5를 안 넣으면 `new int[-1]`로 즉사한다(6-7). ㉰ 3.2 수정이 저장소가 추적 중인 구 형태 파일까지 깨뜨린다(6-8). 반박 하나: **code_diff 6.2 ㉯의 "지금 형태의 파일을 넣으면 여기서 걸린다"는 사실이 아니다.** 그 오류 갈래는 밀림 때문에 오히려 도달 불가 코드가 된다(6-5). Round 2가 대안으로 제시한 문구("오류 셋이 섞여 나온다")도 부정확하다. 실제로는 두 종류다 | **처방 수정 필요.** "파일 변환 단계를 넣고 변환된 파일을 함께 둔다"만으로는 닫히지 않는다. ㉮ 두 파서가 동시에 받는 배치는 존재한다(분기 줄을 모든 row 뒤에 두거나, row 마지막 칸만 쓰기)(6-14). ㉯ 그러나 어느 배치를 골라도 DAO의 `Is_LLR_Valid` RW2와 G2가 분기 구조를 거부하므로 **DAO 검증기 수정이 필수다**(6-15). ㉰ 더 큰 것은 DAO가 trial마다 LLR matrix를 새로 쓰는데 쓰기 경로에 분기 줄 자리가 없다는 점이다. 변환 파일을 한 번 두는 것으로 끝나지 않고 **DAO 쓰기 경로도 함께 고쳐야 한다**(6-16). ㉱ 6.2 ㉯의 대체 문구는 Round 2가 제안한 것이 아니라 "변환 전 파일은 3.4 대조 오류와 6.2 `(1)` 두 종류만 내고 `MN_num`이 무너진 채 완주한다"로 적어야 한다. ㉲ 파일 이름이 `LLR_MATRIX_%d.txt`로 고정이라 같은 폴더에 두 벌을 둘 수 없으므로 정본 지정이 필요하다 | **HIGH 유지.** 오히려 파급이 넓어졌다. 적용 계획 전체를 막는 데다 구 형태 파일 호환까지 깨고, 처방이 DAO 쪽 수정을 부르므로 이 작업의 범위 판단(상위 7장)에 영향을 준다 |
| **R2-8** | **확인됨.** 다섯 증거 모두 코드에서 확인됐고 반례가 없다. Round 2보다 강한 보강 셋이 나왔다. ㉮ 140행 검사 자체가 `fclose` 뒤라 이미 도달 불가에 가깝다(8-4). ㉯ `main`은 `Setup`이 돌려준 오류까지 버린다(8-7). ㉰ 저장소 소스 전체에 `exit`, `abort`, `assert`가 하나도 없다(8-8). 인용 정정 하나: **Round 2와 context가 든 `Read_FER_From_File`은 호출자가 없는 죽은 코드다.** 실제 파서는 `Read_Ref_C_Result`이며, 이 정정은 R2-8의 결론을 바꾸지 않는다(오히려 DAO가 stdout도 결과 파일의 오류 표시도 보지 않는다는 결론이 그대로다)(5-15) | **처방 유효.** 0이 아닌 종료 코드가 `CalledProcessError`를 거쳐 `MPI_Abort`로 DAO 전체를 끝내며, DAO 쪽에 추가 수정이 필요 없다(8-10). **MPI 경로 걱정은 실체가 없다.** AUTO 빌드에서 `__RUN_MPI__`가 정의되지 않으며 전파는 Python 계층에서 일어난다(8-11). 정상 파일에서 오탐이 없다(8-12). 갈래는 두 가지다. ㉠ `main`의 `return 0`을 `return err`로 바꾸고 반환 사슬을 잇는 안(저장소 관례에 맞으나 `Read_LLR_info_Auto`부터 `Run_Simulation`까지 사슬을 고쳐야 하고, 기존 `Print_Input_Err_Code` 경로까지 함께 살아나는 범위 밖 개선이 딸린다). ㉡ `exit(1)`을 쓰는 안(수정 범위가 좁으나 저장소에 용례가 없다). **두 갈래를 상위 문서에 나란히 적고 사용자 결정을 받는 것이 옳다.** 대안 둘(DAO가 stdout을 받기, 결과 파일에 오류 줄 남기기)은 각각 장시간 실행에서 출력이 메모리에 쌓이는 문제와 원인이 "파싱 실패"로 가려지는 문제가 있어 권하지 않는다. **단서**: 9장 적용 순서에서 파일 변환 단계를 P8보다 앞에 두어야 한다. 변환 전 파일은 3.4를 반드시 걸리게 하므로 순서가 뒤바뀌면 첫 실행이 즉시 중단된다(8-13) | **HIGH 유지.** 근거가 모두 확인됐고 반례가 없다. 처방을 적용하지 않으면 3.4를 넣는 의미가 사라진다 |

---

## ㉱ 검증 중 새로 드러난 사실

- ㉮ **`iter_num`의 최솟값이 1이라는 사실이 R2-5의 두 항목을 동시에 정리한다.**
  [decoder.cpp:1947-1951](../../../../../../0_LDPC_original/src/decoder.cpp)의 mn 0 가로채기와
  [decoder.cpp:506, 509](../../../../../../0_LDPC_original/src/decoder.cpp)의 power stopping 꺼짐이 겹쳐
  `iter_num`을 쓰는 일곱 지점 가운데 실제로 실행되는 것은 `Check_End_Iter`의 둘뿐이고 둘 다 mn 1 이상에서만 걸린다.
  이 사실이 ㉠ "mn 0 종료 프레임 `iter_num` -4"를 지우고, ㉡ 동시에 `MN[4]` = 0 열도 1.0으로 포화시킨다.
  Round 2 팀 I 리더가 상충 2에서 "열 4는 `o_iter_num`이 0이 될 수 있으므로 1.0 고정이 아니다"라고 판정한 것은
  같은 사실을 반대로 쓴 것이다

- ㉯ **`Read_FER_From_File`이 죽은 코드라는 사실이 Round 2와 context의 인용을 무효화한다.**
  R2-5의 검증 축과 R2-8의 근거가 모두 [DAO_Main.py:7969-7999](../../../../../SRC/DAO_Main.py)를 가리켰으나
  호출자가 없다. 두 발견의 결론은 그대로 서지만 근거 줄을
  [DAO_Main.py:8187-8273](../../../../../SRC/DAO_Main.py)로 바꿔 적어야 한다.
  덧붙여 이 죽은 함수는 불렸어도 `parts[-1]`이 실행 시간 문자열이라 예외가 났을 것이다

- ㉰ **결과 파일의 마지막 FER 열은 `MN[]`과 무관하다.**
  [ecc_top.cpp:874-876](../../../../../../0_LDPC_original/src/ecc_top.cpp)의 `fr_4KB[MN_num-1]`은
  `o_CRC_flag`로만 센다. DAO가 읽는 파일을 쓰는 `Print_Result_Part2_Memory_Opt`이
  [ecc_top.cpp:2201](../../../../../../0_LDPC_original/src/ecc_top.cpp)에서 이 값을 FER 열과 별개의 칸으로 찍고
  (형제 자리는 [2120](../../../../../../0_LDPC_original/src/ecc_top.cpp)과
  [2272](../../../../../../0_LDPC_original/src/ecc_top.cpp)),
  DAO는 그 칸을 `parts[2]`로 읽는다.
  판정용 FER이 이 값에서 오므로, `MN[]` 왜곡이 최적화 결과를 직접 바꾸지 않는다는 결론의 뿌리가 여기다

- ㉱ **DAO 파서와 결과 파일 사이에 이미 한 칸 어긋남이 있다.**
  `parts[result_offset:-3]`은 FER 열 `MN_num`개 가운데 마지막 하나를 뒤쪽 세 토큰과 함께 잘라 내므로
  배열 길이가 123이 되는데 `matrix.max_iteration`은 124다.
  [DAO_Main.py:1831-1836](../../../../../SRC/DAO_Main.py)과 [1856](../../../../../SRC/DAO_Main.py)이 이를 잘라 맞춘다.
  이 작업과 무관한 기존 상태이며 로그 표시에만 영향을 준다

- ㉲ **현재 파일은 DAO 자신의 검증기를 통과하지 못한다.**
  [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt)의 row 77개 가운데
  26개가 마지막 칸에 0이나 1을 담고 있어
  [DAO_LLR_MATRIX.py:344-346](../../../../../SRC/DAO_LLR_MATRIX.py)의 RW2 검사에 걸린다.
  곧 파일 변환 문제는 계획이 만든 것이 아니라 이미 존재하는 상태이며, 상위 문서 4장의 형태 논의가
  "무엇으로 바꿀 것인가"가 아니라 "지금 어긋나 있는 것을 어느 쪽으로 맞출 것인가"임을 뜻한다

- ㉳ **`local_opt.cpp:124`의 조건 둘째 항 `MODE_DEC_1_SSD`는 정의가 없다.**
  R2-15의 사실 주장과 일치하며 팀 V3의 검증에서도 재확인됐다.
  DAO는 `init_n` 1(HD)을 쓰므로([DAO_Config.py:171](../../../../../SRC/DAO_Config.py)) 첫째 항만으로 블록이 동작하고,
  R2-5의 셈은 이 손상과 무관하게 성립한다

- ㉴ **워커 간 상충 한 건과 판정.**
  워커 1은 "도달 불가가 되는 row는 없다"라 했고 워커 2는 "row 121~124는 BF 미진입 프레임만 쓴다"를 확인됨으로 두고
  이를 근거로 R2-5의 HIGH 유지를 주장했다.
  **판정: 워커 1이 맞다.** 리더가 소스와 파일로 확정했다.
  [LLR_MATRIX_1.txt](../../../../../Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt) 93행에서 105행까지
  13개 row가 모두 `iter_start` 105, `iter_end` 124이고 `type_each_group[11]`이 1(`GROUP_TYPE_CSW`)이므로
  [decoder.cpp:7052-7062](../../../../../../0_LDPC_original/src/decoder.cpp)가 이 그룹 안에서 row를 `prev_CSW`로만 고른다.
  iteration 상한이 120으로 줄어도 13개 row 전부가 여전히 선택 대상이며,
  어느 그룹의 `iter_start`도 121 이상이 아니다(최댓값 105).
  따라서 워커 2의 심각도 유지 근거는 성립하지 않고 R2-5는 MEDIUM으로 내린다
