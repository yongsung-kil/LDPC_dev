# Review Context (라이트 리뷰: SW 분기 지원과 오류 수정 코드)

> 작성: 2026-09-22 22:39:24

## 리뷰 대상

`5_DAO/SRC` 네 파일의 변경분. 기준 커밋 6e035e6에서 HEAD(15ab8e3)까지.

```
git diff 6e035e6 HEAD -- 5_DAO/SRC          # 전체 변경분 (469줄 추가, 121줄 삭제)
git show 508f856 -- 5_DAO/SRC               # 자명한 오류 21건 수정
git show 0e69866 -- 5_DAO/SRC               # SW 분기 지원 (배치 계산, 유효성 규칙, 묶음 변이, 모드 제한)
git show 0eebbb6 -- 5_DAO/SRC               # 다른 세션의 수정 (redecode uncor 누적). 이 리뷰의 주 대상은 아니지만 연결되는 자리는 본다
git show af01630 -- 5_DAO/SRC               # 헤더 규약 확정 (1은 보통 그룹, 10은 묶음, 20과 21은 분기 2개)
git show 15ab8e3 -- 5_DAO/SRC               # 모드 제한을 타겟 기준으로 좁힘, 보호 구간 안전망
```

| 파일 | 바뀐 곳 |
|------|--------|
| `DAO_Config.py` | HBF 시퀀스 값, `TIME_CONFIG.MPI_TEST_BARRIER_TIMEOUT_SECONDS` |
| `DAO_Constants.py` | `SW_BRANCH_NONE`, `MAX_SW_BRANCH`, `SW_BRANCH_ALLOWED_MODES` |
| `DAO_LLR_MATRIX.py` | `LLR_Row.floor_flag` 뜻, 배치 속성, `Build_SW_Branch_Layout`, `Is_LLR_Valid`(RW2, G2 대체, G7, G9, G10, H6, H8, R3, R4, max_iteration), `Correct_LLR_Matrix`(CSW 보정, HBF 범위), 읽기 직후 배치 계산 |
| `DAO_Main.py` | `Update_Configs` 순서, `Update_RefC_Configs` ch_type 3, `Initialize_Stage`(호출 순서, 묶음 타겟), `Set_Gen_Trial_LLR_Mode`(REORDER trial 수, 묶음과 허용 검사), `Check_SW_Branch_Mode_Allowed`, `_Protected_Groups_Changed`, `Gen_Trial_LLR` 안전망, `Bcast_Trial_LLR_Mode` 튜플, `_Get_Target_Bundle_Groups`, `Generate_Random_Mutation`, `Mutate_CSW`, `_safe_allgather`, `MPI_Barrier` 타임아웃, 속도 테스트 시드, `Is_Matrix_Better`, ack 처리, `_write_error_log`, `Rebuild_Partial_Pool` 복원, `Validate_Config` 시퀀스 검사, GEN_SINGLE_ROW 종료 플래그, `Print_Mode_Target_Info` |

## 변경 목적

- ㉮ 508f856: 앞선 라이트 리뷰([r2 report](../../../20260921_DAO_readability_review/review/r2_round2_lv2_analysis/report.md))에서 자명하다고 판정한 CRITICAL 6건, HIGH 13건, 그 밖에 2건을 고쳤다
- ㉯ 0e69866, af01630, 15ab8e3: DAO가 SW(Syndrome Weight, 신드롬 무게) 분기가 있는 LLR matrix를 읽고 묶음 단위로 변이하게 했다. 설계와 결정은 [설계 문서](../20260921_SW_branch_DAO_support.md), 규칙은 [DAO_spec.md 3.7절](../../../../DAO_spec.md)에 있다

핵심 규칙 요약:
- 행 꼬리 칸 `floor_flag`가 분기 index(-1은 없음, 0 이상은 구간 안 분기 번호). 헤더 `type_each_group`은 10 미만이면 보통 그룹(꼬리 -1), 10 이상이면 `{분기 수}{분기 index}`(10은 분기 1개짜리 묶음, 20과 21은 분기 2개)
- 묶음은 한 구간 안에서 분기 index가 같은 그룹들. 구간은 index 0으로 시작해 0으로 되돌아가거나 -1이 나오기 전까지, 또는 헤더 표시 값이 바뀌는 자리까지
- 타겟 목록은 묶음 대표만 담는다. 타겟에 분기 그룹이 있으면 MUTATE_MATRIX, MUTATE_CSW만 허용하고 마지막 분기만 갱신한다. 타겟이 분기 구간 뒤의 보통 그룹뿐이면 다른 모드도 허용하되(GEN_INITIAL_GROUP 제외) 타겟 앞 그룹을 바꾼 trial은 버린다
- 두 변이 모드는 타겟 묶음의 그룹마다 따로 변이한다

예시 입력: `5_DAO/Input/Ref_C/Prime_ECC_3.0/Initial_LLR_matrix/LLR_MATRIX_1.txt`(분기 2개짜리 구간 둘), `LLR_MATRIX_2.txt`(iteration 1~4가 헤더 10인 묶음).

## 이미 한 검증

단일 프로세스 실행 검사 두 벌이 [checks/](../checks/)에 있다 (`cd 5_DAO/SRC && python <경로>`로 실행, mpiexec 없이 돈다).
- `check_dao_fixes.py`: 오류 수정 20건 검사
- `check_sw_branch.py`: SW 분기 40건 검사 (옛 형식 회귀, 파일 1과 2 왕복, 묶음과 구간, 거부 8종, 변이, 모드 허용 판정, 보호 구간)

MPI 실제 실행은 하지 않았다. 여러 rank가 도는 상황(집단 통신 짝, root 전용 블록의 탈출, bcast 되는 값)은 코드 읽기로만 확인했다.

## 리뷰 목적 (라이트 리뷰: Round 1 관점 도출, Round 2 분석에서 종료)

"이 변경분에 문제가 없는가"를 본다. 축은 둘이다.
- ㉮ 변경이 새로 만든 결함: 잘못된 로직, 엣지케이스, rank 사이 동기화 어긋남(bcast 튜플 변경, root 블록 안의 MPI_Abort, 보호 구간 검사가 root에서만 도는 것), 옛 형식 매트릭스에서의 회귀
- ㉯ 설계와 코드의 불일치: 설계 문서와 DAO_spec.md 3.7절이 말하는 규칙과 코드가 같은가, 예시 파일 두 개가 규칙대로 읽히는가

## 기술 맥락

- MPI(mpi4py): rank 0이 root(LLR 생성, 최적 판정), 나머지가 worker. root가 판단하고 `_safe_bcast`로 맞추는 관용구. 집단 통신은 모든 rank가 같은 횟수로 불러야 한다
- `Set_Gen_Trial_LLR_Mode`는 root 블록에서 모드와 타겟을 정하고 `Bcast_Trial_LLR_Mode`로 뿌린다. root 블록 안의 `MPI_Abort`는 전체를 죽이는 기존 패턴이다
- `Gen_Trial_LLR`은 root가 trial 매트릭스를 만들고 `generate_LLR_success`와 매트릭스를 bcast한다
- 프로젝트 문장 규칙(줄표와 가운뎃점 금지, 긍정문)과 파일 참조 규칙(markdown link)은 루트 `CLAUDE.md`를 따른다

## 심각도 기준

| 심각도 | 정의 |
|--------|------|
| CRITICAL | 프로세스 중단이나 hang, 데이터 비가역 손상 |
| HIGH | 틀린 결과를 내지만 프로세스는 계속됨 |
| MEDIUM | 엣지케이스 위험, 누락 커버리지 |
| LOW | 개선 제안 |
