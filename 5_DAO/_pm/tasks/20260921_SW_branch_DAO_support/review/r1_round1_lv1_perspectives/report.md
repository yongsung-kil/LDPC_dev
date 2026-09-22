# Round 1 결과: 관점 리스트업

> 기록: 2026-09-22 22:54:27
> 에이전트 2개(A, B, 모델 Opus) 독립 도출. 원본은 [agent_A.md](agent_A.md)(28개), [agent_B.md](agent_B.md)(22개)

두 에이전트의 관점 50개를 겹치는 것끼리 묶어 16개로 정리했다. "출처" 열은 각 문서의 관점 번호다. 상세 확인 항목은 출처 문서의 해당 행에 있다.

## 축 ㉮ 변경이 새로 만든 결함 (P1~P11)

| # | 관점명 | 확인 항목 (요약) | 대상 | 출처 |
|---|--------|----------------|------|------|
| P1 | 배치 계산기의 상태 전이와 엣지케이스 | 다섯 갈래 전이에서 `expected_start`가 늘 정해지는지, `close_span`의 `nonlocal`, 빈 그룹과 그룹 하나와 첫 그룹, `type_each_group` 길이 불일치 대체, 헤더 0과 1, `INITIAL_TARGET_GROUP_IDX` 범위 밖 | `Build_SW_Branch_Layout`, `Initialize_Stage`, `_Get_Target_Bundle_Groups` | A:A1 A2 A17, B:A1 A6 |
| P2 | 배치 계산의 부작용과 오류 반환 무시 | `max_iteration`을 다시 쓰는 부작용이 닿는 곳(`Gather_Ref_C_Results`의 Reduce 버퍼 크기 등), 오류로 중간에 빠져나올 때 `span_of_group`이 일부만 채워진 상태로 쓰이는 호출처 5곳 | `Build_SW_Branch_Layout` 호출처 전부 | A:참고㉮, B:A2 A3 |
| P3 | 옛 형식 회귀와 restart 섞인 SD 매트릭스 | 삭제된 G2와 새 계산이 첫 그룹, restart 그룹, 빈 그룹에서 같은 판정인지, `Prime_ECC_2.3`과 `2.4` 입력, restart 그룹이 앞 그룹의 꼬리를 물려받는 두 자리, R3과 R4가 기존 생성 함수와 맞는지, `Gen_LLR_Insert_Restart_Group`의 iteration 재번호 | `Is_LLR_Valid`, `_create_restart_group`, `_Build_Inserted_Restart_Matrix` | A:A3 A4, B:A7 A8 |
| P4 | 헤더 대 본문 신규 검사와 생성 모드의 충돌 | H6과 G7이 새로 생겼으므로 그룹과 행을 늘리고 줄이는 모든 생성 함수가 `num_group`, `num_row_each_group`, `type_each_group`을 함께 갱신하는지 전수 | 구조 변경 모드 전부 | A:A5 |
| P5 | CSW 보정과 HBF 경로 | 배수 맞춤과 범위 자르기와 중복 내리기의 순서, `int(round())`의 짝수 붙음, 연쇄 내리기, `ValueError`를 잡는 호출처, HBF 시퀀스 다섯 모드를 `Gen_Trial_LLR`이 다 처리하는지, dv 0 범위 | `Correct_LLR_Matrix`, `Correct_Ch_Th_In_Row`, `Mutate_CSW`, `Gen_Trial_LLR` | A:A6 A7, B:A9 |
| P6 | rank 사이 동기화: bcast 튜플, root 블록 안 MPI_Abort, trial 버림 흐름 | 튜플 7개의 송수신 순서, root 블록 안 `MPI_Abort` 시 worker 상태, 보호 구간 검사가 root에서만 돌고 `generate_LLR_success` 하나로 나가는 흐름의 집단 통신 횟수, 버려진 trial이 남기는 상태(`prev_generated_mutation`, tuning) | `Bcast_Trial_LLR_Mode`, `Set_Gen_Trial_LLR_Mode`, `Gen_Trial_LLR` | A:A8 A9, B:A4 |
| P7 | 보호 구간 검사가 보는 범위 | 헤더 배열과 `restart_groups`를 비교하지 않는 것, `num_protected = min(target_group_indices)`가 맞는지, `Gen_LLR_Reorder_Group`이 `type_each_group`을 다시 만드는 것 | `_Protected_Groups_Changed` | A:A10 참고㉰, B:A8 참고㉶ |
| P8 | 타임아웃 값과 allgather 감시 | 약 10.6시간이 ECC를 사이에 두지 않는 모든 배리어에도 걸리는 영향, `Check_Barrier_Sync`의 allgather가 `_safe_allgather`를 쓰지 않는 것, 감시 thread | `MPI_Barrier`, `_safe_allgather`, `Check_Barrier_Sync` | A:A11 참고㉱, B:A5 |
| P9 | ack와 uncor 파일 수명, Partial 복원, GEN_SINGLE_ROW 종료, redecode 수정 | ack 폴더 비우기와 worker 쓰기 사이 배리어, `_Report_Missing_Acks` 두 자리, `_Restore_State_After_Partial_Rebuild`의 bcast 횟수와 `prev_seed_mode` 정합, 모든 rank가 같은 후보 index에서 멈추는지, `Delete_Own_Uncors(is_redecoded_uncor=True)`와 SW 변경의 접점 | `Initialize_Run_ECC_End_Flag`, `Test_LLR`, `Rebuild_Partial_Pool`, `Run_Single_Row_Generation`, `Set_Test_Environment` | A:A12 A13 A14, B:A11 |
| P10 | 설정 순서와 채널 배열, 단일 값 교체 처방 | `Update_Exit_After_Run_Configs` 선행이 다른 종속을 깨지 않는지, ch_type 3 채널 확장, 속도 테스트 인자 12번, `Is_Matrix_Better`의 inf 치환, REORDER trial 수, C2 호출 순서 | `Update_Configs`, `Update_RefC_Configs`, `Get_Ref_C_Args_For_Speed_Test`, `Is_Matrix_Better`, `Set_Gen_Trial_LLR_Mode` | A:A15 A18, B:A10 |
| P11 | 묶음 변이가 다른 장치에 주는 파급 | mutation 목록이 그룹 수만큼 늘어난 뒤 `Generate_All_Fine_Tuning_Mutations` 조합 수와 `max_possible_tuning_mutation_count`, `Mutate_CSW`의 `random.randint(1, max)` 분포 | `Gen_LLR_Mutate_Matrix`, tuning 두 함수, `Mutate_CSW` | A:A16, B:B7 |

## 축 ㉯ 설계와 코드의 불일치 (P12~P16)

| # | 관점명 | 확인 항목 (요약) | 대상 | 출처 |
|---|--------|----------------|------|------|
| P12 | 타겟 목록의 묶음 단위가 모든 생성 자리에 적용되는가 | 묶음으로 접는 곳이 `Initialize_Stage` 하나인데 `Initialize_LLR_Matrix`, optimal 갱신 뒤 복원, 구조 변경 모드의 조정 목록은 `range(...)` 그대로인 것 | `Initialize_LLR_Matrix`, `Update_Optimal_LLR`, INSERT 계열 | A:B1 참고㉯, B:B4 |
| P13 | 모드 허용 판정의 단위와 마지막 분기 규칙 | 코드는 목록 전체를 펼쳐 보는데 문서는 "타겟 그룹"이라 적은 것, 마지막이 아닌 분기가 타겟이면 abort하는 정책. B의 관찰: 파일 1은 기본 `INITIAL_TARGET_GROUP_IDX`(1)로 타겟 목록이 [0, 2, 3, 4, 6, ...]이 되어 첫 순환에서 타겟 0(분기 0)에 걸려 멈춘다. 마지막이 아닌 분기를 목록에서 자동으로 빼는 편이 맞는지 판단 | `Check_SW_Branch_Mode_Allowed`, `Initialize_Stage` | A:B2 B3, B:B5 B6 참고㉰ |
| P14 | 헤더 규약과 H8, 묶음과 구간 정의, 데이터 모델 | 헤더 0(restart 그룹 표시)이 "10 미만은 보통 그룹" 규칙에 맞는지, 새 row와 새 그룹의 꼬리 기본값(`Gen_LLR_Gen_Initial_Group`은 아직 0), 새 그룹의 헤더 값, `max_iteration` 두 정의와 `Change_Max_Iteration`, 상수 값, 묶음이 "같은 리스트 객체"인 것 | `Is_LLR_Valid` H8, `Gen_LLR_Gen_Initial_Group`, `Change_Max_Iteration`, `DAO_Constants.py` | A:B4 B7 B8, B:B1 B2 B3 B8 참고㉳ |
| P15 | 예시 파일 두 개, spec 규칙표 1대1, 검사 커버리지 | 두 파일의 묶음과 구간과 max_iteration이 설계 2.1 표와 같은지(두 에이전트가 파일 1은 확인함), 왕복 토큰 일치, spec 규칙 이름과 오류 문구가 코드와 짝이 맞는지, 검사 40건과 20건이 안전성 체크리스트를 덮는지와 못 덮는 자리 | `DAO_spec.md` 3장, `checks/` | A:B5 B9 B10, B:B9 B10 |
| P16 | HBF 최적화 모드와 SW 분기의 결합 | spec 3.7 ㉲가 다루지 않는다고 적은 조합에서 코드가 무엇을 하는지(`IS_HBF_OPT`와 분기 매트릭스, HBF 시퀀스의 INSERT 계열이 허용 검사에 걸리는지) | `Set_Gen_Trial_LLR_Mode`, `Is_LLR_Valid` HBF 검사 | B:B11 |

## Round 1 실마리 (검증 전 관찰)

- ㉮ `Build_SW_Branch_Layout`의 오류 반환값을 받는 곳은 `Is_LLR_Valid` 하나. 다른 호출처 5곳은 버린다 (A, B)
- ㉯ 타겟 목록을 묶음으로 접는 코드가 `Initialize_Stage`에만 있다 (A, B)
- ㉰ `_Protected_Groups_Changed`는 헤더 배열과 `restart_groups`를 비교하지 않는다 (A, B)
- ㉱ `Check_Barrier_Sync`의 allgather는 `_safe_allgather`를 쓰지 않는다 (A)
- ㉲ `Gen_LLR_Gen_Initial_Group`의 꼬리 기본값이 아직 0이다 (A, B)
- ㉳ `current_target_bundle`은 bcast되지만 로그 한 줄에만 쓰인다. 실제 변이 대상은 `_Get_Target_Bundle_Groups`가 다시 계산한다 (B)
- ㉴ 파일 1은 기본 `INITIAL_TARGET_GROUP_IDX`로 첫 순환에서 분기 0 타겟에 걸려 멈춘다 (B)
- ㉵ `Build_SW_Branch_Layout`이 `max_iteration`을 덮어쓰며, 이 값은 `Gather_Ref_C_Results`의 Reduce 버퍼 크기를 정한다 (B)
- ㉶ restart 그룹을 만드는 두 자리가 앞 그룹의 꼬리를 물려받고 헤더에 1 또는 0을 적는다. `Gen_LLR_Insert_Restart_Group`은 삽입 뒤 모든 그룹의 iteration을 1부터 다시 매긴다 (B)
- ㉷ 두 에이전트 모두 검사 60건 재실행 통과, 파일 1의 묶음과 구간이 설계 표와 같음을 확인 (A, B)

## 다음 단계 결정

→ Round 2 (lv1, 에이전트 4개)
  사유: 대상이 469줄 diff와 그 호출처로 한정되어 lv1로 충분하다. 관점 16개를 파일과 주제로 묶어 넷에 나눈다.

| 에이전트 | 배정 관점 | 주제 |
|---------|----------|------|
| 1 | P1, P2, P3 | 배치 계산기와 유효성 (DAO_LLR_MATRIX.py 중심, 옛 형식과 restart 회귀) |
| 2 | P4, P5, P11, P14 | 생성 모드와 보정, 데이터 모델 (헤더 갱신 전수, CSW와 HBF 보정, 변이 파급, 꼬리 기본값, max_iteration) |
| 3 | P6, P7, P8, P9 | MPI 동기화와 실행 흐름 (bcast, abort, 보호 구간, 타임아웃, ack와 uncor와 Partial과 단일 row) |
| 4 | P10, P12, P13, P15, P16 | 설정 처방과 설계 대조 (타겟 단위 적용 범위, 모드 허용과 마지막 분기 정책, 예시 파일, spec 표, 검사 커버리지, HBF 결합) |

라이트 리뷰이므로 Round 2에서 종료한다.
