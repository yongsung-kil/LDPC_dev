# 4_H_matrix_tool: H-matrix 설계 툴 (Project 4)

H-matrix 설계 도구를 모은 프로젝트. 코드는 `src/`, 생성 결과는 `out/`(git 무시 대상)에 둔다.
디코딩과 FER 측정은 본체 시뮬레이터(`2_LDPC_base/src`)를 import해 사용한다 (복사 금지,
상위 폴더에서 `2_LDPC_base/src`를 찾는 부트스트랩 방식).

| 파일 | 역할 |
|------|------|
| `src/peg.py` | PEG(Progressive Edge Growth)로 base graph 생성 |
| `src/lifting.py` | greedy circulant shift 배정 (4-cycle 회피) |
| `src/gen_example_code.py` | 위 둘을 조립해 dual-diagonal parity QC-LDPC 예시 부호 생성 (Ref-C 포맷 저장) |
| `src/select_irregular.py` | irregular 후보를 여러 seed로 생성, FER 스크리닝으로 승자 선별과 저장 (부호 설계 실험용) |

- ㉮ 실행 예 (repo 루트에서): `python 4_H_matrix_tool/src/gen_example_code.py [출력경로]`
- ㉯ 출력 기본 위치는 `out/` (git 무시 대상)
- ㉰ **주의**: `select_irregular.py`는 구 본체 API 기준이라 현재 실행 불가.
  새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질해야 실행된다
  (`_pm/TODO.md` 등록 항목)
- ㉱ 이 도구들은 실험 실행 흐름과 분리되어 있다. 실험 실행 흐름(2_LDPC_base의 run)은
  H-matrix를 생성하지 않고 파일로만 받는다 (사용자 결정 2026-08-05)
