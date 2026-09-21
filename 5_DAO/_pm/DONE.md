# DONE — 완료 이력 (5_DAO)

### 2026-09-21 — README의 uncor 폴더 구조와 실행 모드 설명을 현재 코드에 맞춤
Two-Stage 절이 Partial/Full 하위 폴더와 없는 설정 변수를 안내하던 것을 Dynamic Partial 구조로 다시 씀
- **배경**: 2SD uncor 폴더 구성을 확인하는 과정에서 README 1.2.2, 3.2, 4.1.3 절이 `Partial/`, `Full/` 하위 폴더와 PARTIAL_UNCOR_MATRIX_IDX, FULL_UNCOR_MATRIX_IDX를 안내했으나, 코드는 Full uncor만 `Uncors/{모드}/LLR_MATRIX_{idx}.txt/`에서 읽고 Partial은 초기 Full 테스트의 실패 uncor로 세션 안에 만든다. ExitAfterInitialMatrixMode 언급도 RunDAOMode로 바뀐 뒤였다
- **변경**: 1.2.1~1.2.3, 3.2.1~3.2.4, 3.2.5 판단 snippet, 4.1.1 실행 모드, 4.1.3 UNCOR_CONFIG, 4.1.8 경로 예시, 4.2.1 RunDAOMode, 4.3 설정 예시, 부록 A 경로, 부록 C 저장 구조를 코드 기준으로 다시 씀. uncor 파일 이름 표와 SAVE_UNCOR 결과를 최적화 입력 폴더로 옮기는 순서를 추가
- **파일**: README.md

### 2026-09-21 — uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정
SAVE_UNCOR 모드 초기 테스트에서 optimal_LLR_matrix가 None이라 멈추던 문제 해결
- **배경**: Test_LLR이 채널마다 부르는 Gather_And_Archive_Uncors가 optimal_LLR_matrix의 파일 이름을 읽는데, optimal은 Run_Initial_Test의 Update_Optimal_LLR(is_initial=True)에서 처음 채워지므로 초기 테스트 중에는 None이었다. Two-stage 모드의 _Build_Initial_Partial_Pool도 같은 순서 문제를 가졌다 (반입 원형부터 있던 문제, 사용자 결정 2026-09-21: 매트릭스를 인자로 받는 방식 채택)
- **변경**: Gather_And_Archive_Uncors와 _Get_Tmp_Partial_Uncor_Dir에 matrix 인자를 추가하고 보관 폴더 이름과 함께 저장하는 매트릭스 파일을 그 인자 기준으로 결정. 매트릭스 파일은 optimal_output_dir에서 복사하지 않고 Save_LLR_Matrix로 보관 폴더에 직접 저장. 호출처 6곳(Test_LLR, Process_Uncors, _Build_Initial_Partial_Pool, Rebuild_Partial_Pool)이 uncor를 만든 매트릭스를 넘김
- **파일**: SRC/DAO_Main.py (검증: _test/20260921_gather_uncors_matrix_arg/, 실제 LLR_OPT와 입력 매트릭스로 3건 통과)
