# Worker T-1: 결과 파싱과 집계 (P4)

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 기록: 2026-09-21 15:16:50

배정 관점 P4(Ref-C 결과 파싱과 집계 두 경로)를 코드로 직접 확인했다. 줄 번호는 모두 현재
파일(`DAO_Main.py` 10,428줄) 기준으로 다시 확인했다. 결과 파일의 열 구성은 저장소 안의
원본 C++ 출력 코드([ecc_top.cpp:2093~2130](0_LDPC_original/src/ecc_top.cpp#L2093),
[common.cpp:83](0_LDPC_original/src/common.cpp#L83))를 읽어 대조했다.

---

## 발견 요약

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|----------|------|
| T1-1 | CRITICAL | 한 채널의 uncor 풀이 비면 그 채널에서 `total_tests=0`이 되어 `MPI_Abort`로 작업 전체가 죽는다 | [DAO_Main.py:1883](5_DAO/SRC/DAO_Main.py#L1883), [9426](5_DAO/SRC/DAO_Main.py#L9426) | 두 단계 테스트에서 채널 하나의 fail uncor가 0개, 다른 채널은 1개 이상 | `Test_LLR`의 채널 루프에 uncor 없는 채널 건너뛰기를 넣고, `Rebuild_Partial_Pool`의 0개 판정을 채널별로 바꾼다 |
| T1-2 | HIGH | 파싱 실패로 통째로 버려진 코어의 결과가 "정상 0"과 구분되지 않아 표본이 줄어든 채 FER이 계산된다 | [DAO_Main.py:8265~8275](5_DAO/SRC/DAO_Main.py#L8265), [1823~1831](5_DAO/SRC/DAO_Main.py#L1823) | 재시도 4회 안에 파일이 안정되지 않는 코어가 하나라도 있을 때 | 실패를 성공과 구별되는 값으로 돌려주고, 실패 코어가 있으면 그 라운드 결과를 판정에서 뺀다 |
| T1-3 | MEDIUM | while 루프 중 집계가 다른 rank의 Run_ECC 완료를 기다리지 않는다 (동기화 지점 없음) | [DAO_Main.py:8977~8983](5_DAO/SRC/DAO_Main.py#L8977), [1816~1834](5_DAO/SRC/DAO_Main.py#L1816) | 코어 사이 속도 차가 있는 모든 실행 | 루프 안 집계 앞에 `MPI_Barrier`를 두거나, 루프 안 집계를 각 rank의 오류 수 `Reduce`로 바꾼다 |
| T1-4 | MEDIUM | Partial 풀 재구성이 optimal의 Full FER, avg_iteration, num_tests를 재측정값으로 덮어쓴다 | [DAO_Main.py:9379](5_DAO/SRC/DAO_Main.py#L9379) | 두 단계 테스트에서 optimal이 갱신될 때마다 | 재구성 전에 optimal의 결과 필드를 복사해 두고 `Test_LLR` 뒤 되돌린다 |
| T1-5 | MEDIUM | `avg_iterations`의 미테스트 표시값 `-1.0`이 "낮을수록 좋음" 비교에서 가장 좋은 값으로 동작한다 | [DAO_Main.py:1189, 1194](5_DAO/SRC/DAO_Main.py#L1189), [2540~2542](5_DAO/SRC/DAO_Main.py#L2540) | 모든 채널 FER이 같고 한쪽에 미테스트 채널이 있을 때 | 미테스트 채널의 `avg_iterations`를 `float("inf")`로 채우거나, `num_tests==0`인 채널이 있으면 비교를 거부한다 |
| T1-6 | MEDIUM | Partial에서 걸러져 Full을 건너뛴 trial이 멀티라운드 결과 갱신에 FER 1.0, avg_iter -1.0으로 기록되고 로그에 측정값처럼 찍힌다 | [DAO_Main.py:8051~8052](5_DAO/SRC/DAO_Main.py#L8051), [5661~5669](5_DAO/SRC/DAO_Main.py#L5661) | `ENABLE_TWO_STAGE_TEST=True` + `DELETE_ROW` 또는 `INSERT_RESTART_GROUP` 모드 | `Test_Trial_LLR`의 반환값을 받아 Full 테스트가 없었으면 라운드 갱신 함수를 부르지 않는다 |
| T1-7 | MEDIUM | `Read_Ref_C_Result`의 재시도가 `ValueError`만 덮어 `OSError`는 설계 밖에서 프로세스를 끝낸다 | [DAO_Main.py:8210~8218](5_DAO/SRC/DAO_Main.py#L8210), [8265](5_DAO/SRC/DAO_Main.py#L8265) | 결과 파일이 읽기 도중 사라지거나 잠겼을 때 | `except (ValueError, OSError)`로 넓힌다 |
| T1-8 | MEDIUM | `LOAD_UNCOR_VECTOR`에서는 uncor 없는 코어가 Run_ECC를 건너뛰지 않는다 | [DAO_Main.py:7931~7934](5_DAO/SRC/DAO_Main.py#L7931), [639~644](5_DAO/SRC/DAO_Main.py#L639) | `LOAD_UNCOR_MODE=LOAD_VECTOR`이고 어떤 코어에 분배된 uncor가 0개 | 건너뛰기 조건을 `is_load_seed_mode`로 넓힌다 |
| T1-9 | LOW | 주석이 "누적 합산"이라 적혀 있으나 실제 집계는 대입이다 | [DAO_Main.py:586](5_DAO/SRC/DAO_Main.py#L586), [1888~1892](5_DAO/SRC/DAO_Main.py#L1888) | 항상 | 주석을 "그 시점까지의 합을 덮어쓴다"로 다시 쓴다 |
| T1-10 | LOW | iteration별 오류 수를 한 자리 유효숫자 FER에서 역산해 표시값이 부정확하다 | [DAO_Main.py:8250](5_DAO/SRC/DAO_Main.py#L8250) | `ENABLE_PRINT_ALL_ITER_FERs=True` | 표시값임을 로그 머리말에 밝히거나 Ref-C가 정수 오류 수를 함께 쓰게 한다 |
| T1-11 | LOW | 호출자 없는 결과 읽기 함수 두 개 (`Read_FER_From_File`, `Reset_Optimal_Results`) | [DAO_Main.py:7971](5_DAO/SRC/DAO_Main.py#L7971), [7957](5_DAO/SRC/DAO_Main.py#L7957) | 항상 | 삭제한다 |
| T1-12 | LOW | 결과 요약의 모드 목록에 `INSERT_RESTART_GROUP`이 빠져 temp_optimal 줄이 안 나온다 | [DAO_Main.py:7632~7643](5_DAO/SRC/DAO_Main.py#L7632) 대 [8626~8641](5_DAO/SRC/DAO_Main.py#L8626) | `INSERT_RESTART_GROUP` 모드 | 두 목록을 `MULTI_ROUND_MODES`처럼 한 상수로 합친다 |
| T1-13 | LOW | 재시도 횟수 로그 문구가 실제 시도 횟수와 하나 어긋난다 | [DAO_Main.py:8271](5_DAO/SRC/DAO_Main.py#L8271) | 파싱 실패 시 | `max_retries + 1`을 쓰거나 문구를 "재시도 3회 포함 4회 시도"로 고친다 |

---

## 발견 상세

### T1-1 (CRITICAL) 채널 하나의 uncor가 비면 작업 전체가 죽는다

`Gather_Ref_C_Results`의 공통 꼬리는 테스트 수가 0이면 작업을 끝낸다.

```
1883:        if total_tests == 0:
1884:            self.MPI_Abort(f"Gather_Ref_C_Results: total_tests=0 for ch_idx={ch_idx}. All cores failed to produce results.")
```

`MPI_Abort`는 마지막에 `self.comm.Abort(error_code)`를 부르므로([DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894))
MPI 작업 전체가 끝난다.

그런데 테스트 수가 0이 되는 길은 "모든 코어가 실패"만이 아니다. uncor를 싣는 모드에서
`Run_ECC`는 자기 채널 uncor가 없으면 아무것도 하지 않고 돌아간다.

```
7932:        if self.is_load_uncor_seed_file_mode:
7933:            if not self.has_uncor[ch_idx]:
7934:                return
```

그리고 `has_uncor[ch_idx]`는 그 채널의 풀이 비면 모든 rank에서 False가 된다
([DAO_Main.py:7521~7523](5_DAO/SRC/DAO_Main.py#L7521)). 풀이 빌 수 있는 이유는
`_Setup_Uncor_Pool_For_Channel`이 소스 파일이 없거나 줄이 없으면 `pool_has_uncor_list`를
모두 False로 남겨 두기 때문이다([DAO_Main.py:7407~7413](5_DAO/SRC/DAO_Main.py#L7407)).

빈 채널을 걸러 낼 기회가 두 군데 있는데 둘 다 채널별이 아니라 전체 합만 본다.

```
9426:        if total_partial_count == 0:          # Rebuild_Partial_Pool
9341:        if total_partial == 0:                # _Build_Initial_Partial_Pool
```

`total_partial_count`는 모든 채널의 합이므로, 채널 0의 fail uncor가 0개이고 채널 1에
100개가 있으면 합이 100이라 최적화가 계속된다. 다음 trial의 Partial 테스트에서
`Test_LLR`의 채널 루프([DAO_Main.py:8957](5_DAO/SRC/DAO_Main.py#L8957))는 채널 0을
건너뛰지 않고 그대로 돌며, 모든 rank의 `Run_ECC`가 즉시 돌아와 결과 파일이 하나도
생기지 않고, 루프 끝의 집계([DAO_Main.py:8991](5_DAO/SRC/DAO_Main.py#L8991))가
`total_tests=0`으로 작업을 끝낸다.

채널 0은 보통 오류가 가장 적은(가장 쉬운) 채널이므로 fail uncor가 먼저 마르는 채널이다.
즉 최적화가 잘 될수록 이 길에 먼저 도달한다. 로그에 남는 문구는
"All cores failed to produce results"라서 원인(그 채널에 시험할 uncor가 없음)을 가린다.

처방:

- ㉮ `Test_LLR`의 채널 루프 머리에 건너뛰기를 넣는다. `Set_Test_Environment` 앞에서
  `self.has_uncor[ch_idx]`를 모든 rank가 이미 같은 값으로 들고 있으므로
  (`Load_Uncors_From_Pool`이 `pool_has_uncor`를 bcast한 값에서 정한다) 갈라짐 없이
  같은 판정을 한다. 건너뛸 때 그 채널의 `matrix.FERs[ch_idx]`와 짝 필드를
  `_Fill_Untested_Channels`와 같은 규칙으로 채우고 로그에 이유를 남긴다.
- ㉯ `Rebuild_Partial_Pool`과 `_Build_Initial_Partial_Pool`의 0개 판정을 채널별로
  바꿔, 어느 한 채널이라도 0개면 그 채널을 "이미 목표 달성"으로 표시한다.
- ㉰ `Gather_Ref_C_Results`의 오류 문구에 제외 코어 수와 uncor 보유 코어 수를 함께 적어
  "결과를 만든 코어가 없음"과 "시험할 프레임이 없음"을 구분한다.

### T1-2 (HIGH) 파싱 실패가 표본만 줄이고 조용히 지나간다

`Read_Ref_C_Result`는 재시도를 다 쓰면 경고 한 줄만 남기고 빈 결과를 돌려준다.

```
8265:            except ValueError as e:
8266:                if attempt < max_retries:
8267:                    time.sleep(retry_delay)
8268:                    continue  # 재시도
8269:                else:
8271:                    self.Write_Log_Lines(f"[WARNING] Read_Ref_C_Result: {max_retries}회 재시도 후 파싱 실패, 결과 무시됨 — {file_path} ({e})")
8272:                    return 0, 0, 0, None
```

돌려주는 `(0, 0, 0, None)`은 상위에서 "결과 없음"과 "정상적으로 0건"이 구분되지 않는다.
root 순차 경로는 그 값을 그냥 더하고([DAO_Main.py:1826~1829](5_DAO/SRC/DAO_Main.py#L1826)),
rank별 경로는 sendbuf에 0을 담아 `Reduce`에 넣는다([DAO_Main.py:1852~1857](5_DAO/SRC/DAO_Main.py#L1852)).
어느 쪽도 "몇 개 코어의 결과가 빠졌는가"를 세지 않는다.

한 줄이 깨졌을 때 그 줄만 버리는 것이 아니라 파일 전체를 버린다는 점도 크다. 줄 단위
검사에서 `raise ValueError`를 던지면([DAO_Main.py:8234~8236](5_DAO/SRC/DAO_Main.py#L8234))
`for line in lines` 밖으로 튀어 그때까지 쌓은 `sum_test`, `sum_error`가 모두 사라지고
처음부터 다시 읽는다. Ref-C는 결과 파일에 이어 쓰므로(`fopen(..., "a")`,
[ecc_top.cpp:2090](0_LDPC_original/src/ecc_top.cpp#L2090)) 그 파일에는 그 채널에서 지금까지
돌린 모든 실행의 결과가 누적돼 있다. 즉 마지막 줄 하나가 아직 다 쓰이지 않았다는 이유로
그 코어의 누적 결과 전부가 빠진다.

이것이 판정에 닿는 이유는 비교에 허용 오차가 없기 때문이다.

```
2510:        le_all = all(a <= b for a, b in zip(A, B))
2511:        lt_one = any(a < b for a, b in zip(A, B))
```

코어가 N개일 때 한 코어가 빠지면 분모(`total_tests`)가 약 1/N 줄고 분자도 함께 줄지만
비율은 그 코어의 오류율만큼 움직인다. `Is_List_A_Strictly_Better`는 그 차이를 그대로
"개선"이나 "열화"로 읽으므로, 파싱 실패 한 번이 trial 채택 여부를 뒤집을 수 있다.

처방:

- ㉮ `Read_Ref_C_Result`의 실패 반환을 `None` 하나로 바꾸고(또는 다섯 번째 원소로
  `is_valid`를 더해) 호출부에서 구분한다.
- ㉯ `Gather_Ref_C_Results`에 `num_failed_cores`를 세는 변수를 두고, root 경로는 그 자리에서,
  rank별 경로는 sendbuf에 한 칸을 더해 `Reduce`로 모은다.
- ㉰ 실패 코어가 하나라도 있으면 그 채널 결과를 판정에 쓰지 않도록
  (`matrix.FERs[ch_idx]`를 1.0으로 채우고 로그에 남김) 처리하거나, 최소한 로그에
  "표본 M/N 코어"를 함께 적는다.
- ㉱ 줄 단위 실패를 파일 전체 실패로 키우지 않도록, 마지막 줄이 불완전하면 그 줄만 버리고
  나머지 줄의 집계를 살린다.

### T1-3 (MEDIUM) while 루프 중 집계가 다른 rank의 실행 완료를 기다리지 않는다

`Test_LLR`의 while 루프는 Run_ECC 직후 곧바로 집계를 부른다.

```
8978:                self.Run_ECC(ch_idx=ch_idx)
8980:                if not is_load_seed_mode:
8981:                    self.Gather_Ref_C_Results(matrix=matrix, ch_idx=ch_idx, is_test_end=False)
8982:                self.Check_Test_End(ch_idx=ch_idx)
```

`is_test_end=False` 경로는 root만 남고 나머지는 곧장 돌아간다
([DAO_Main.py:1804~1805](5_DAO/SRC/DAO_Main.py#L1804)). 그래서 이 사이에 집단 통신이
하나도 없고, root는 자기 Ref-C가 끝나자마자 다른 rank의 세션 디렉토리에 있는 결과 파일을
읽는다([DAO_Main.py:1820~1824](5_DAO/SRC/DAO_Main.py#L1820)). 느린 rank는 아직 이번 회차의
줄을 쓰지 않았거나 쓰는 중이다.

`Read_Ref_C_Result`의 크기 안정화 루프는 이 상황을 덮지 못한다.

```
8210:                prev_size = -1
8211:                for _ in range(5):  # 최대 5회 체크
8212:                    curr_size = os.path.getsize(file_path)
8213:                    if curr_size == prev_size:
8214:                        break
8215:                    prev_size = curr_size
8216:                    time.sleep(0.02)
```

이 루프는 "쓰기가 멈췄는가"만 본다. 아직 시작도 안 한 파일은 크기가 그대로이므로 첫
비교에서 바로 안정으로 판정돼 이전 회차까지의 내용만 읽힌다. 재시도까지 다 써도 최대
0.4초 정도이고, Ref-C 한 회차는 그보다 훨씬 길다.

결과: root가 오류 수를 과소 집계해 `Check_Test_End`의 `total_num_errors[ch_idx] >= max_error`
판정([DAO_Main.py:1067](5_DAO/SRC/DAO_Main.py#L1067))이 늦어지고, 필요 이상으로 회차를 더
돈다. 최종 FER은 루프를 빠져나온 뒤 barrier가 있는 `is_test_end=True` 경로에서 다시
집계되므로 틀리지 않는다. 그래서 심각도는 MEDIUM(낭비와 진단 혼란)으로 본다.

처방: `Run_ECC` 다음, 루프 안 집계 앞에 `self.MPI_Barrier()`를 넣는다. 루프 본문에는 현재
집단 통신이 없으므로 barrier를 하나 넣으면 모든 rank가 같은 횟수로 지나야 한다. 루프
탈출이 rank마다 다른 회차에서 일어날 수 있으므로(아래 "확인했으나 문제 없던 범위" 참고)
barrier는 반드시 `Run_ECC` 바로 뒤, `Read_Run_ECC_End_Flag`로 빠지는 break보다 뒤에 두어야
한다. 또는 루프 안 집계 자체를 각 rank가 자기 오류 수만 보내는 `Reduce` 한 번으로 바꾸면
파일을 남의 디렉토리에서 읽는 구조가 사라진다.

### T1-4 (MEDIUM) Partial 풀 재구성이 optimal의 측정값을 덮어쓴다

`Rebuild_Partial_Pool`은 optimal 매트릭스로 Full uncor를 다시 디코딩한다.

```
9379:        self.Test_LLR(self.optimal_LLR_matrix)
```

`Test_LLR`은 채널마다 `Gather_Ref_C_Results(matrix=..., is_test_end=True)`를 부르고, 그
꼬리가 `matrix.FERs`, `matrix.seed_FERs`, `matrix.num_errors`, `matrix.num_tests`,
`matrix.avg_iterations`를 모두 덮어쓴다([DAO_Main.py:1898~1958](5_DAO/SRC/DAO_Main.py#L1898)).
`self.optimal_LLR_matrix`가 그대로 넘어가므로 방금 승격된 optimal의 공식 측정값이 재구성
실행의 측정값으로 바뀐다.

같은 uncor 풀과 같은 매트릭스라 값이 같을 것이라고 기대할 수는 있지만, 이 함수는 그것을
보장하지 않는다. 시드 모드가 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`로 달라지고
([DAO_Main.py:9366~9372](5_DAO/SRC/DAO_Main.py#L9366)), 그 사이에 `Periodic_Recheck`로
제외 코어가 바뀌면 분배가 달라져 분모가 달라진다. 더 중요한 것은 이후 모든 비교의 기준이
되는 값(`Is_Matrix_Better`의 `matrix_B.FERs`)이 사용자가 보는 승격 시점 로그의 값과
달라질 수 있다는 점이다. `Print_Test_Summary`도 이 덮어쓴 값을 보여 준다.

처방: `Rebuild_Partial_Pool`에서 `Test_LLR` 앞에 optimal의 결과 필드를 `Deep_Copy`로
보관하고(`saved = self.optimal_LLR_matrix.Deep_Copy(copy_raw_FER=True, copy_seed_FER=True,
copy_partial_FER=True)`), Step 6 앞에서 `FERs`, `raw_FERs`, `seed_FERs`, `num_errors`,
`num_tests`, `avg_iterations`를 되돌린다. 재구성 실행의 측정값은 별도 로그 문구로만 남긴다.

### T1-5 (MEDIUM) 미테스트 표시값 -1.0이 비교에서 최선값이 된다

`_Fill_Untested_Channels`는 테스트하지 못한 채널을 이렇게 채운다.

```
1188:                matrix.FERs_partial[ch_idx] = 1.0
1189:                matrix.avg_iterations_partial[ch_idx] = -1.0
1193:                matrix.FERs[ch_idx] = 1.0
1194:                matrix.avg_iterations[ch_idx] = -1.0
```

FER 쪽 1.0은 "가장 나쁨"이라 의도대로 동작한다. 그러나 `avg_iterations`는 낮을수록 좋은
값이므로 -1.0은 "가장 좋음"이다. 매트릭스 생성자와 `Deep_Copy`도 같은 -1.0을 미테스트
표시로 쓴다([DAO_LLR_MATRIX.py:78~79](5_DAO/SRC/DAO_LLR_MATRIX.py#L78),
[247](5_DAO/SRC/DAO_LLR_MATRIX.py#L247)).

`Is_Matrix_Better`의 두 번째 단계가 이 값을 그대로 쓴다.

```
2539:        if DAO_CONFIG.ENABLE_AVG_ITER_UPDATE:
2540:            if all(abs(a - b) < 1e-15 for a, b in zip(matrix_A.FERs, matrix_B.FERs)):
2542:                return self.Is_List_A_Strictly_Better(matrix_A.avg_iterations, matrix_B.avg_iterations)
```

모든 채널 FER이 같을 때, 한쪽에 미테스트 채널이 있으면 그쪽이 반드시 이긴다. 반대로
전부 제대로 측정한 매트릭스는 미테스트 채널을 가진 상대를 절대 이기지 못한다
(`all(a <= b)`에서 `12.5 <= -1.0`이 거짓이므로).

도달 경로: `REORDER_GROUP`의 첫 후보는 비교 없이 temp_optimal이 된다
([DAO_Main.py:1410~1412](5_DAO/SRC/DAO_Main.py#L1410)). `Update_Reorder_Round_Result`의
첫 후보도 무조건 round best가 된다([DAO_Main.py:4766~4768](5_DAO/SRC/DAO_Main.py#L4766)).
그 첫 후보가 조기 채널 중단으로 뒤쪽 채널이 채워진 매트릭스이면, 이후 후보들은 뒤쪽
채널의 FER이 1.0으로 같아질 때(uncor 풀이 어려운 채널에서 실제로 생긴다) avg_iteration
동점 판정에서 진짜 측정값을 가진 쪽이 진다.

처방:

- ㉮ `_Fill_Untested_Channels`가 `avg_iterations`에 `float("inf")`를 넣는다. 로그 서식
  (`{avg_iter:.2f}`)이 `inf`를 그대로 찍으므로 표시도 오히려 분명해진다.
- ㉯ 더 확실하게는 `Is_Matrix_Better`가 두 번째 단계에 들어가기 전에
  `matrix_A.num_tests`와 `matrix_B.num_tests`에 0이 있으면 False를 돌려주게 한다.
  `_Fill_Untested_Channels`가 이미 `num_tests=0`을 남기므로 추가 상태가 필요 없다.

### T1-6 (MEDIUM) Full을 건너뛴 trial이 라운드 결과에 측정값처럼 기록된다

`Run_Optimization`은 `Test_Trial_LLR`의 반환값을 `should_check_update`로 받아 두고도,
멀티라운드 결과 갱신은 그 값과 무관하게 부른다.

```
8044:                should_check_update = self.Test_Trial_LLR()
8051:                    if update_func_name and self.is_root and self.current_LLR_matrix is not None:
8052:                        getattr(self, update_func_name)(self.current_LLR_matrix)
```

`Test_Trial_LLR`은 Partial에서 개선이 없으면 Full을 건너뛰고 False를 돌려준다
([DAO_Main.py:9525](5_DAO/SRC/DAO_Main.py#L9525)). 이때 `current_LLR_matrix.FERs`는
`Gen_Trial_LLR`의 `Deep_Copy(copy_raw_FER=False, copy_seed_FER=False)`가 넣은 1.0 그대로이고
`avg_iterations`는 -1.0 그대로다([DAO_LLR_MATRIX.py:245~249](5_DAO/SRC/DAO_LLR_MATRIX.py#L245)).

`DELETE_ROW`와 `INSERT_RESTART_GROUP`은 Partial 필터링을 허용하는 모드이므로
([DAO_Main.py:9494~9497](5_DAO/SRC/DAO_Main.py#L9494)) 이 조합이 실제로 생긴다. 결과:

```
5661:        for ch_idx in range(REFC_CONFIG.NUM_TARGET_CHANNELS):
5663:            self.Write_Log_Lines(
5664:                f"\t  → Result ch{ch_idx}({ch_param}): FER={tested_matrix.FERs[ch_idx]:.6e}, "
5665:                f"avg_iter={tested_matrix.avg_iterations[ch_idx]:.2f}"
```

로그에 `FER=1.000000e+00, avg_iter=-1.00`이 "Result"라는 이름으로 남는다. 측정한 적이 없는
값이 측정값 자리에 찍히므로 사람이 실험 기록을 볼 때 그 trial이 아주 나빴다고 읽게 된다.

판정 자체는 대부분 옳게 끝난다. `Is_Matrix_Better(tested, round_baseline)`가 FER 1.0을
baseline의 실제 FER과 비교해 False가 되기 때문이다([DAO_Main.py:5669](5_DAO/SRC/DAO_Main.py#L5669)).
다만 baseline의 FER이 모든 채널에서 1.0인 경우에는 T1-5의 -1.0 뒤집힘이 그대로 작동해
한 번도 Full 테스트하지 않은 후보가 라운드 best가 되고, `_Finalize_Delete_Row_Round`가
그 후보의 행 삭제를 확정한다([DAO_Main.py:5707](5_DAO/SRC/DAO_Main.py#L5707)).

처방: `Run_Optimization`에서 `if should_check_update:`로 감싸 Full 테스트가 끝난 trial만
라운드 갱신 함수에 넘긴다. Full을 건너뛴 trial은 "Partial 필터에서 제외"라는 별도 로그
한 줄만 남기고, 라운드 후보 진행 인덱스는 지금처럼 그대로 증가시킨다.

### T1-7 (MEDIUM) 재시도가 OSError를 덮지 않는다

`Read_Ref_C_Result`는 `os.path.getsize`와 `open`을 try 안에서 쓰면서 `except ValueError`만
잡는다([DAO_Main.py:8207~8218](5_DAO/SRC/DAO_Main.py#L8207), [8265](5_DAO/SRC/DAO_Main.py#L8265)).
파일 접근에서 나는 예외는 `OSError` 계열이므로 재시도를 그냥 지나쳐 위로 올라간다.

root 순차 경로는 `os.path.exists`로 확인한 직후에 읽지만, 그 파일을 소유한 rank의 Ref-C가
`fopen(..., "a")`로 열고 있는 중이다. 파일이 사라지거나(정리와 겹침) 공유 위반이 나면
"재시도 후 결과 무시"라는 설계와 다르게 프로세스가 끝난다.

처방: `except ValueError as e:`를 `except (ValueError, OSError) as e:`로 넓힌다. 크기 안정화
루프 안의 `os.path.getsize`도 같은 try 안에 있으므로 함께 보호된다.

### T1-8 (MEDIUM) 벡터 모드에서는 uncor 없는 코어가 실행을 건너뛰지 않는다

건너뛰기 조건이 시드 파일 모드에만 걸려 있다.

```
7932:        if self.is_load_uncor_seed_file_mode:
7933:            if not self.has_uncor[ch_idx]:
7934:                return
```

`is_load_uncor_seed_file_mode`는 `LOAD_UNCOR_SEED`와 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`만
포함한다([DAO_Main.py:639~644](5_DAO/SRC/DAO_Main.py#L639)). `LOAD_UNCOR_VECTOR`에서
uncor를 받지 못한 코어는 벡터 파일 없이 Ref-C를 돌리게 되고, 그 결과가 결과 파일에
섞여 집계에 들어간다.

처방: 조건을 `self.is_load_seed_mode`로 바꿔 세 모드 모두에서 같은 건너뛰기가 걸리게
한다. 이름도 목적에 맞게 `is_uncor_loaded_mode` 같은 쪽으로 다시 붙이면 두 속성의 차이가
읽는 사람에게 드러난다.

### T1-9 (LOW) 초기화 주석과 실제 집계 방식이 다르다

```
586:        # 2. Test 결과 누적값 (Gather_Ref_C_Results가 누적 합산하므로 반드시 초기화)
```

실제 집계는 누적이 아니라 대입이다.

```
1888:        self.total_num_tests[ch_idx] = total_tests
1889:        self.total_num_errors[ch_idx] = total_errors
```

한 번의 `Gather_Ref_C_Results`가 그 채널의 결과 파일 전체(Ref-C가 이어 쓴 모든 회차)를
다시 읽어 합한 값을 넣으므로, 들어가는 값은 "그 시점까지의 합"이고 대입이 맞다. 주석이
`+=`를 기대하게 만들어 잘못된 수리를 부를 수 있다.

덧붙여, 값이 대입이므로 매트릭스 단위 초기화만으로 충분하다는 점도 확인했다. 다만
조기 채널 중단으로 건너뛴 채널(`ch_idx` 이후)의 `self.total_num_*`에는 이전 trial 값이
남는다. 그 자리는 `Print_Test_Result`(건너뛴 채널에서는 호출되지 않음)와
`Check_Test_End`(그 채널의 집계 뒤에만 호출됨)에서만 읽히므로 판정에 닿지 않는다.
`_collect_error_state_snapshot`이 뜰 때만 헷갈리는 값으로 보인다.

처방: 주석을 "한 채널 집계가 끝나면 그 시점까지의 합을 덮어쓴다. 매트릭스가 바뀌면
남은 값이 다음 매트릭스로 새지 않도록 여기서 비운다"로 다시 쓴다.

### T1-10 (LOW) iteration별 오류 수는 역산값이라 정확하지 않다

```
8250:                    num_error_per_iteration = np.round(arr * num_test).astype('f8')
```

`arr`는 결과 파일의 FER 열인데, C++가 `fprintf(fp, "%.1e ", FER[i])`로 유효숫자 한 자리만
쓴다([ecc_top.cpp:2125](0_LDPC_original/src/ecc_top.cpp#L2125)). 거기에 테스트 수를 곱해
반올림하므로 오류 수가 최대 수 퍼센트 어긋난다. 이 값은
`self.total_num_error_per_iters`와 `self.total_FER_per_iters`로 흘러 로그에만 쓰이고
([DAO_Main.py:7597~7598](5_DAO/SRC/DAO_Main.py#L7597)) 판정에는 쓰이지 않는다.

같은 자리에서 확인한 것: `AUTO` 빌드는 `MN_num = 1`로 고정되므로
([main.cpp:776~778](0_LDPC_original/src/main.cpp#L776)) 결과 줄의 FER 열은 하나뿐이다.
따라서 "iteration별 분포"로 찍히는 배열은 첫 칸만 뜻이 있고 나머지 `max_iteration - 1`
칸은 항상 0이다. 길이 보정 분기([DAO_Main.py:1832~1835](5_DAO/SRC/DAO_Main.py#L1832))가
이 경우를 덮으므로 값 손실은 없다.

처방: 로그 문구를 "최종 iteration 오류 수(역산)"로 바꾸거나, Ref-C 출력에 정수 오류 수
열을 더해 그것을 읽는다.

### T1-11 (LOW) 결과 읽기 쪽 죽은 코드 둘

- `Read_FER_From_File`([DAO_Main.py:7971](5_DAO/SRC/DAO_Main.py#L7971)): 전수 grep 결과
  호출처가 없다. 게다가 `float(parts[-1])`로 마지막 토큰을 읽는데, 결과 줄의 마지막
  토큰은 `Print_Excuting_Time`이 쓴 `0hour(s)_0minute(s)_12sec(s)` 문자열이므로
  ([common.cpp:94](0_LDPC_original/src/common.cpp#L94)) 불렸더라도 `Invalid FER`로
  `MPI_Abort`가 났을 것이다.
- `Reset_Optimal_Results`([DAO_Main.py:7957](5_DAO/SRC/DAO_Main.py#L7957)):
  `Set_Ref_C_Parameters(is_test_optimal=True)`에서만 불리는데
  ([DAO_Main.py:8611~8612](5_DAO/SRC/DAO_Main.py#L8611)), `is_test_optimal=True`를 넘기는
  호출처가 전수 grep에 없다.

처방: 두 함수와 `Set_Ref_C_Parameters`의 `is_test_optimal` 분기를 지운다.
`Test_LLR`과 `Set_Ref_C_Parameters`의 `is_test_optimal` 인자도 함께 정리하면 시그니처가
줄어든다.

### T1-12 (LOW) 요약 출력의 모드 목록이 갱신 판정의 목록과 다르다

`Set_Update_Flags`의 목록에는 `INSERT_RESTART_GROUP`이 있고
([DAO_Main.py:8636](5_DAO/SRC/DAO_Main.py#L8636)), `Print_Test_Summary`의 같은 뜻의
목록에는 없다([DAO_Main.py:7632~7643](5_DAO/SRC/DAO_Main.py#L7632)). 그래서
`INSERT_RESTART_GROUP` 스테이지에서는 `has_temp_optimal`이 항상 False가 되어 요약에
temp_optimal 줄이 빠진다. 값 자체가 틀리지는 않고 보고서에서 한 줄이 사라진다.

처방: 두 목록을 모듈 상수 하나(`UPDATE_AT_LAST_TRIAL_MODES`)로 합쳐
`DAO_Constants.py`에 두고 두 곳에서 참조한다.

### T1-13 (LOW) 재시도 횟수 문구가 실제와 하나 다르다

`for attempt in range(max_retries + 1)`이므로 시도는 4회인데 문구는
`{max_retries}회 재시도 후 파싱 실패`라 3회로 읽힌다
([DAO_Main.py:8207](5_DAO/SRC/DAO_Main.py#L8207), [8271](5_DAO/SRC/DAO_Main.py#L8271)).
같은 줄의 줄표(em dash, U+2014)는 프로젝트 문장 규칙 위반이기도 하다(가독성 팀 R 소관).

---

## 확인했으나 문제 없던 범위

- ㉮ **`base_offset`과 `parts[result_offset:-3]` 슬라이싱이 실제 출력 열과 정확히 맞는다.**
  원본 C++의 결과 줄은 `[채널 열들] rn fr[MN_num-1] avg_iter FER[0..MN_num-1] avg_clk
  avg_clk_throughput 수행시간` 순서다([ecc_top.cpp:2093~2130](0_LDPC_original/src/ecc_top.cpp#L2093)).
  채널 열 수는 `ch_type=1`(RBER) 1개, `ch_type=2`(고정 오류) 1개, `ch_type=3`(강오류)
  3개이므로 `base_offset` 1/1/3이 맞다([common.h:80~82](0_LDPC_original/src/common.h#L80)).
  뒤쪽 세 토큰은 `avg_clk`, `avg_clk_throughput`, 그리고 공백이 없는 수행시간 문자열
  하나(`%dhour(s)_%dminute(s)_%dsec(s)`, [common.cpp:94](0_LDPC_original/src/common.cpp#L94))
  이므로 `-3`도 정확하다. `ch_type=1` 기준으로 세어 보면 전체 토큰은 `MN_num + 7`개이고
  `parts[4:-3]`은 인덱스 4부터 `MN_num+3`까지로 FER 열과 정확히 겹친다.
- ㉯ **`total_tests == 0` 검사가 나눗셈보다 앞에 온다.** `total_FER_per_iter` 계산은
  `if total_tests else np.zeros_like(...)`로 막혀 있고
  ([DAO_Main.py:1881](5_DAO/SRC/DAO_Main.py#L1881)), `FER_value`와 `avg_iteration`의
  나눗셈은 `MPI_Abort` 뒤에 있다([DAO_Main.py:1883~1886](5_DAO/SRC/DAO_Main.py#L1883)).
  ZeroDivisionError는 나지 않는다. root 전용 경로에서 root만 이 검사를 실행하는 것도
  갈라짐을 만들지 않는다. `MPI_Abort`가 `comm.Abort`로 작업 전체를 끝내기 때문이다
  ([DAO_Main.py:6894](5_DAO/SRC/DAO_Main.py#L6894)).
- ㉰ **두 집계 경로의 제외 코어 처리가 같은 기준이다.** root 경로는
  `if proc in self.excluded_cores: continue`, rank별 경로는
  `if not self.is_current_core_excluded:`로 0을 보낸다. 두 값은
  `Test_Core_Speed` 끝에서 `excluded_cores`를 bcast한 뒤
  `is_current_core_excluded = self.rank in self.excluded_cores`로 함께 정해지므로
  어긋나지 않는다([DAO_Main.py:9087~9089](5_DAO/SRC/DAO_Main.py#L9087)).
  파일이 없어 건너뛴 코어도 두 경로 모두 0을 더하므로 합산 결과는 같다. 다만 "제외된
  코어"와 "실패한 코어"를 구분하지 않는다는 점은 T1-2에 적었다.
- ㉱ **while 루프 안에는 집단 통신이 없다.** `Gather_Ref_C_Results(is_test_end=False)`는
  non-root에서 즉시 반환하고, `Check_Test_End`와 `Print_Test_Result`는 파일 입출력과
  root 전용 출력뿐이다. 그래서 root가 종료 플래그를 쓰는 시점 차이로 rank마다 루프
  횟수가 하나씩 달라져도 hang이 나지 않는다. 반대로 이 루프 본문에 집단 통신을
  하나라도 넣으면 곧바로 hang이 되므로, T1-3의 barrier 처방은 `Run_ECC` 바로 뒤
  (모든 rank가 반드시 지나는 자리)에만 넣어야 한다.
- ㉲ **`is_load_seed_mode`에서 while이 한 번만 돈다는 전제가 성립한다.**
  `Check_Test_End`의 첫 분기가 모든 rank에서 `self.is_test_end = True`를 세우므로
  ([DAO_Main.py:1057~1060](5_DAO/SRC/DAO_Main.py#L1057)) 루프 조건이 다음 회차에 거짓이
  된다. 플래그 파일 쓰기는 root 전용이지만 로컬 변수 설정이 모든 rank에서 일어나므로
  갈라지지 않는다. 따라서 루프 안 집계를 건너뛰어도 `is_test_end=True` 집계가 같은 값을
  낸다.
- ㉳ **`matrix.max_iteration`이 모든 rank에서 같은 값으로 정해진다.** 이 필드는
  `Read_Input_LLR_Matrix`가 아니라 `Is_LLR_Valid` 안에서 세워진다
  ([DAO_LLR_MATRIX.py:441](5_DAO/SRC/DAO_LLR_MATRIX.py#L441)). 그런데 trial 매트릭스는
  `Gen_Trial_LLR` 끝에서 bcast된 뒤([DAO_Main.py:2017](5_DAO/SRC/DAO_Main.py#L2017))
  모든 rank가 `Is_Current_LLR_Valid`를 부르므로 각자 같은 데이터에서 같은 값을 세운다.
  `GEN_SINGLE_ROW` 후보는 root의 `Build_Single_Row_Matrix`가 bcast 전에
  `Is_LLR_Valid`를 부르므로([DAO_Main.py:10224](5_DAO/SRC/DAO_Main.py#L10224)) 직렬화된
  객체에 값이 실려 간다. 따라서 `buf_size = 3 + max_iteration`이 rank마다 달라지는 일은
  없다.
- ㉴ **길이 보정이 값을 잃지 않는다.** `AUTO` 빌드의 FER 열은 하나뿐이라
  `len(sum_error_per_iter) < max_iteration`이고, 두 경로 모두 `min`으로 앞쪽만 더한다
  ([DAO_Main.py:1832~1835](5_DAO/SRC/DAO_Main.py#L1832),
  [1856~1857](5_DAO/SRC/DAO_Main.py#L1856)). 반대로 길이가 `max_iteration`보다 길어지면
  뒤쪽이 조용히 잘리지만, `MN_num=1` 고정이라 현재 구성에서는 일어나지 않는다.
- ㉵ **정리 대상 이름이 실제 파일 이름과 맞는다 (Round 1 실마리).**
  `HEADER_TO_REMOVE = ["result", "log_CSW", "Ref_C_result"]`
  ([DAO_Constants.py:129](5_DAO/SRC/DAO_Constants.py#L129))에 대해
  `Get_Result_File_Name`은 `result_4KB_...`
  ([DAO_Main.py:1615~1628](5_DAO/SRC/DAO_Main.py#L1615)),
  `Get_CSW_Log_File_Name`은 `log_CSW_{idx}.txt`
  ([DAO_Main.py:1601](5_DAO/SRC/DAO_Main.py#L1601)), C++의 표준출력 대체 파일은
  `Ref_C_result_{seed}.txt`([ecc_top.cpp:2168](0_LDPC_original/src/ecc_top.cpp#L2168))로
  세 접두사가 모두 맞는다. uncor 파일은 `uncor_`, `redecode_uncor_`로 시작하므로
  ([DAO_Main.py:2082~2086](5_DAO/SRC/DAO_Main.py#L2082)) 함께 지워지지 않는다.
  `Cleanup_Test_Environment`가 `Test_LLR` 끝마다 모든 rank에서 자기 디렉토리를 치우므로
  ([DAO_Main.py:9009](5_DAO/SRC/DAO_Main.py#L9009)) 앞 trial의 결과 파일이 다음 trial에
  섞이지 않는다. 채널 사이에는 지우지 않지만 결과 파일 이름에 채널 파라미터가 들어가
  구분된다.
- ㉶ **DAO가 만드는 결과 파일 이름이 C++가 만드는 이름과 맞는다.**
  `Set_Ref_C_Result_Filename`([main.cpp:673~698](0_LDPC_original/src/main.cpp#L673))과
  `Get_Result_File_Name`을 ch_type 1, 2, 3에 대해 서식 단위로 대조했다. `%.2e`와
  `{:.2e}`, `%d`와 `{:d}`, `_SC_%.2f_SE_%.2f`와 `_SC_{:.2f}_SE_{:.2f}`가 모두 같다.
- ㉷ **지원하지 않는 ch_type이 설정 검증에서 막힌다.** `Get_Result_File_Name`과
  `Get_Uncor_File_Name`은 ch_type 1, 2, 3 외의 else 가지가 없어 잘못된 이름이나
  `UnboundLocalError`로 갈 수 있지만, `Validate_Config`가 `Setup` 단계에서 그 밖의 값을
  `MPI_Abort`로 막는다([DAO_Main.py:9899~9900](5_DAO/SRC/DAO_Main.py#L9899)).
- ㉸ **조기 채널 중단이 채운 값이 잘못된 승격을 만들지는 않는다.**
  `_Is_Channel_Degraded`는 `current_fer > target_fer`일 때만 참이므로
  ([DAO_Main.py:1178](5_DAO/SRC/DAO_Main.py#L1178)) 채워 넣기가 일어난 매트릭스에는
  반드시 비교 대상보다 나쁜 채널이 하나 있다. 그래서
  `Is_List_A_Strictly_Better`의 `le_all`이 거짓이 되고, 1단계와 2단계 모두 False가 된다.
  비교 대상도 `Determine_Update_Decision`, `Check_Partial_Improvement`,
  `_Get_Compare_Target`이 같은 규칙(`is_update_at_last_trial`과 `temp_optimal` 유무)으로
  고르므로 어긋나지 않는다. 남은 위험은 T1-5의 avg_iteration 뒤집힘뿐이다.
- ㉹ **`_Is_Channel_Degraded`가 rank 사이에서 갈라지지 않는다.** 이 판정이 쓰는
  `matrix.FERs`는 `is_test_end=True` 집계의 `_safe_bcast` 결과에서 모든 rank가 같은 값을
  받고([DAO_Main.py:1877](5_DAO/SRC/DAO_Main.py#L1877)), `optimal_LLR_matrix`,
  `temp_optimal_LLR_matrix`, `is_update_at_last_trial`도 모두 bcast된다
  ([DAO_Main.py:9598~9599](5_DAO/SRC/DAO_Main.py#L9598),
  [8643](5_DAO/SRC/DAO_Main.py#L8643)). 그래서 조기 중단 `break`가 rank마다 달라져
  hang이 나는 일은 없다.
- ㉺ **평균 iteration 계산의 가중치가 맞다.** 줄마다 `avg_iteration * num_test`를 더한 뒤
  전체 테스트 수로 나누므로([DAO_Main.py:8240](5_DAO/SRC/DAO_Main.py#L8240),
  [1886](5_DAO/SRC/DAO_Main.py#L1886)) 줄마다 테스트 수가 달라도 가중 평균이 된다.
- ㉻ **uncor 수 집계의 나눗셈이 일관된다.** `Count_Gathered_Uncors`
  ([DAO_Main.py:1042](5_DAO/SRC/DAO_Main.py#L1042))와
  `_Setup_Uncor_Pool_For_Channel`([DAO_Main.py:7420](5_DAO/SRC/DAO_Main.py#L7420))이
  둘 다 `int(줄수 / NUM_LINES_PER_UNCOR)`로 내림하고, 분배도 `num_uncors * lines_per_uncor`
  까지만 쓰므로 끝에 남는 불완전한 기록이 한쪽에만 세어지는 일은 없다.
  `NUM_LINES_PER_UNCOR == 0`도 막혀 있다.

## 다른 팀과 겹치는 관찰

- `self.comm.Reduce`가 `_mpi_comm_with_timeout` 래퍼 없이 직접 불린다
  ([DAO_Main.py:1861](5_DAO/SRC/DAO_Main.py#L1861)). Round 1 실마리 ㉱와 같은 내용이므로
  팀 M에 넘긴다.
- `Gather_Ref_C_Results`의 docstring이 `ch_idx`와 `is_test_end`를 빠뜨리고 `Raises: ValueError`
  라고 적었으나 실제로는 `MPI_Abort`를 부른다([DAO_Main.py:1785~1797](5_DAO/SRC/DAO_Main.py#L1785)).
  Round 1 실마리 ㉹와 같으므로 팀 R에 넘긴다.
- `Read_Ref_C_Result`의 경고 문구와 `Is_Current_LLR_Valid`의 실패 문구에 줄표(em dash,
  U+2014)가 들어 있다([DAO_Main.py:8271](5_DAO/SRC/DAO_Main.py#L8271),
  [2494~2496](5_DAO/SRC/DAO_Main.py#L2494)). 문장 규칙 위반이므로 팀 R에 넘긴다.
