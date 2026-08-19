# H-matrix 2벌 파일 로드 테스트

- 목적: Ref-C의 H_Matrix 폴더 파일처럼 헤더 뒤에 행렬이 2벌 들어 있는 파일을
  `QCCode.load`가 Ref-C(ecc_top.cpp Load_PCM의 fscanf)와 동일하게 읽는지 확인
- 배경: Ref-C는 헤더 5개 정수와 첫 번째 행렬(M_b×N_b개)만 읽고 이후 내용은 무시한다.
  수정 전 light는 헤더 뒤 전체를 행렬로 취급해 2벌 파일에서
  "행렬 원소 수 != M_b×N_b" ValueError가 났다
- 활용 방법: 이 폴더에서 `python test_two_set_load.py` 실행 (내부에서
  `2_LDPC_light/`를 sys.path에 추가). 전부 통과하면 OK 출력
