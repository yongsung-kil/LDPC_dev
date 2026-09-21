# DONE — 완료 이력 (5_DAO)

### 2026-09-21 — uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정
SAVE_UNCOR 모드 초기 테스트에서 optimal_LLR_matrix가 None이라 멈추던 문제 해결
- **배경**: Test_LLR이 채널마다 부르는 Gather_And_Archive_Uncors가 optimal_LLR_matrix의 파일 이름을 읽는데, optimal은 Run_Initial_Test의 Update_Optimal_LLR(is_initial=True)에서 처음 채워지므로 초기 테스트 중에는 None이었다. Two-stage 모드의 _Build_Initial_Partial_Pool도 같은 순서 문제를 가졌다 (반입 원형부터 있던 문제, 사용자 결정 2026-09-21: 매트릭스를 인자로 받는 방식 채택)
- **변경**: Gather_And_Archive_Uncors와 _Get_Tmp_Partial_Uncor_Dir에 matrix 인자를 추가하고 보관 폴더 이름과 함께 저장하는 매트릭스 파일을 그 인자 기준으로 결정. 매트릭스 파일은 optimal_output_dir에서 복사하지 않고 Save_LLR_Matrix로 보관 폴더에 직접 저장. 호출처 6곳(Test_LLR, Process_Uncors, _Build_Initial_Partial_Pool, Rebuild_Partial_Pool)이 uncor를 만든 매트릭스를 넘김
- **파일**: SRC/DAO_Main.py (검증: _test/20260921_gather_uncors_matrix_arg/, 실제 LLR_OPT와 입력 매트릭스로 3건 통과)
