# Dynamic Partial의 redecode uncor 누적 수정

> 작성: 2026-09-22 10:06:39
> 등급: Review (동작 유지 의도의 로직 수정 2건, 코드 변경 3곳). 사용자 지시로 수정을 적용하고 라이트 리뷰로 검증한다.
> 관련: Dynamic Partial 구조 설명은 [README.md 3.2절](../../../README.md)

## 1. 목적

2단계 테스트(ENABLE_TWO_STAGE_TEST)에서 Partial 풀이 optimal 갱신마다 그 회차 실패 수만큼 더 커지는 현상을 없앤다. Partial 풀은 현재 optimal 매트릭스가 정정하지 못한 uncor만 담아야 한다.

## 2. 배경 (관측과 원인)

사용자 관측: Full uncor 1268개, 초기 Full 테스트 실패 914개, 첫 Partial 테스트에서 1828/1828, 이후 [updated]마다 증가.

원인은 두 가지가 겹친 것이다.

- ㉮ **redecode 파일이 누적된다.** Ref-C의 Print_Seed([random.cpp:209](../../../../0_LDPC_original/src/random.cpp))가 seed 파일을 이어쓰기(`"a"`)로 연다. mode_seed 12(LOAD_UNCOR_SEED_SAVE_UNCOR_SEED)에서 실패 seed는 각 rank의 `redecode_uncor_seed_..._{rank}.txt`에 붙는데, DAO에는 이 파일을 지우는 코드가 없다. Set_Test_Environment는 SAVE_UNCOR_SEED 모드의 working copy만 지우고, Cleanup_Test_Environment의 삭제 규칙(.bat, .sh, .tmp, result, log_CSW, Ref_C_result)에도 걸리지 않는다
- ㉯ **초기 update가 Full 테스트를 한 번 더 돌린다.** Test_Initial_LLR이 실패 uncor로 Partial 풀을 만든 직후 Run_Initial_Test가 Update_Optimal_LLR(is_initial=True)를 부르고, Determine_Update_Decision이 is_initial이면 OPTIMAL_MATRIX_FROM_CURRENT를 돌려준다. 그 값이 Update_Optimal_LLR 끝의 Rebuild_Partial_Pool 조건에 걸려 같은 매트릭스로 mode 12 Full 테스트를 다시 돌리고, ㉮ 때문에 실패 seed가 두 번 쌓인 파일을 읽어 1828이 된다

## 3. 설계 (수정 2건, 코드 변경 3곳)

| # | 위치 | 수정 | 효과 |
|---|------|------|------|
| 1 | `Delete_Own_Uncors` | `is_redecoded_uncor` 인자를 추가해 redecode 파일 이름으로도 지울 수 있게 함. 삭제 실패는 MPI_Abort로 멈춤 (풀 파일 쓰기 실패와 같은 정책) | 각 rank가 자기 redecode 파일만 병렬로 삭제하고, 실패가 조용히 넘어가 누적이 되살아나는 일을 막음 |
| 2 | `Set_Test_Environment` | seed 모드가 LOAD_UNCOR_SEED_SAVE_UNCOR_SEED이면 Ref-C 실행 전에 자기 redecode 파일을 지움 | 파일에 이번 실행분만 남아 누적이 끊김 |
| 3 | `Update_Optimal_LLR` | Rebuild_Partial_Pool 조건에 `not is_initial` 추가 | 초기 update에서 중복 Full 테스트 생략 |

Partial 풀의 다른 상태(total_num_partial_uncors, pool_has_uncor[PARTIAL], FERs_partial = 1.0)는 Test_Initial_LLR과 `_Build_Initial_Partial_Pool`이 이미 채우므로 초기 Rebuild를 빼도 빠지는 값이 없다. optimal의 FERs_partial은 Deep_Copy가 1.0으로 두거나 current의 1.0을 복사한다.

## 4. 수정 대상 파일

- `SRC/DAO_Main.py` (Delete_Own_Uncors, Set_Test_Environment, Update_Optimal_LLR)

## 5. 안전성 체크리스트

- ㉮ 삭제는 각 rank가 자기 local_session_dir 안의 자기 파일만 지운다 (다른 rank 파일 접근 없음)
- ㉯ 삭제 시점은 Set_Test_Environment의 첫 MPI_Barrier 뒤이며 Ref-C 실행 전이다. Gather는 Test_LLR이 끝난 뒤이므로 삭제와 겹치지 않는다
- ㉰ SAVE_UNCOR_SEED 모드, LOAD_UNCOR_SEED 모드, 2단계 테스트를 끄는 경우의 동작은 바뀌지 않는다
- ㉱ RunDAOMode.REDECODE(mode 12 한 번 실행 뒤 Input 저장)는 실행 전 삭제만 추가된다. 단일 매트릭스는 결과가 같고, INITIAL_MATRIX_IDX_LIST로 여러 매트릭스를 돌릴 때는 두 번째 매트릭스부터 앞 매트릭스의 실패 seed가 섞이지 않아 각 매트릭스가 정정하지 못한 uncor만 Input에 저장된다
- ㉲ 초기 실패 uncor가 0개인 경우 Test_Initial_LLR의 graceful stop 경로가 그대로 동작하고, 초기 Rebuild가 빠져 두 번째 신호는 나지 않는다. 신호 뒤 정상 종료 여부는 다음 stage의 모드에 달려 있다 (Full 전용 모드면 정상 종료, Partial 허용 모드면 빈 Partial 풀로 테스트가 돌아 MPI_Abort). 이것은 이번 수정과 무관한 기존 결함이며 별도 작업으로 등록했다
- ㉳ worker의 redecode 파일 삭제가 실패하면 그 rank의 파일에 이전 실행분이 남아 누적이 되살아난다. Write_Log_Lines가 root 전용이라 경고만으로는 보이지 않으므로 MPI_Abort로 멈춘다

## 6. 미결정 사항

없음. 사용자 결정(2026-09-22): 두 수정 모두 적용, fable 에이전트 라이트 리뷰로 검증. 리뷰 발견 중 삭제 실패 처리(MPI_Abort)는 반영했고, 이번 수정과 무관한 기존 결함 1건(graceful stop 뒤 빈 Partial 풀 테스트)은 별도 작업으로 등록했다.

## 7. 검증

- 라이트 리뷰 기록: `review/`
- 사용자 환경 MPI 재실행에서 "[Initial Partial] Dynamic partial pool created: N fail uncors"의 N이 초기 Full 테스트의 채널별 "(seed_errors/tests): X/Y"의 X를 모두 더한 값과 같은지, 이후 "[Rebuild_Partial_Pool] Partial pool reconstructed: M fail uncors"의 M이 그 회차 Full 테스트의 X 합과 같은지 확인. 초기 테스트 직후에는 "[Rebuild_Partial_Pool]" 줄이 나오지 않아야 한다
