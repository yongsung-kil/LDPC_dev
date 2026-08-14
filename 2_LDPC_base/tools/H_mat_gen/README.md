# H_mat_gen: H-matrix 설계 툴 모음

H-matrix 설계 관련 도구를 이 폴더에 모은다 (사용자 지시 2026-08-07).

| 파일 | 역할 |
|------|------|
| `peg.py` | PEG(Progressive Edge Growth)로 base graph 생성 |
| `lifting.py` | greedy circulant shift 배정 (4-cycle 회피) |
| `gen_example_code.py` | 위 둘을 조립해 dual-diagonal parity QC-LDPC 예시 부호 생성 (Ref-C 포맷 저장) |
| `select_irregular.py` | irregular 후보를 여러 seed로 생성 → FER 스크리닝 → 승자 선별과 저장 (부호 설계 실험용) |

- ㉮ 실행 예 (repo 루트에서):
  `python -m 2_LDPC_base.tools.H_mat_gen.gen_example_code [출력경로]`
- ㉯ 출력 기본 위치는 이 폴더의 `out/` (git 무시 대상)
- ㉰ **주의**: `select_irregular.py`는 구 본체 API 기준이라 현재 실행 불가.
  새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질해야 실행된다
  (`_pm/TODO.md` 등록 항목)
- ㉱ 이 도구들은 실험 실행 흐름(run.py)과 분리되어 있다. 실행 흐름은 H-matrix를
  생성하지 않고 파일로만 받는다 (사용자 결정 2026-08-05)
