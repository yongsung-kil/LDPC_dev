# workspace: 기준 실험 공간

시뮬레이터 자체의 기준 실험(base_run)과 인프라 점검용 실험을 담는다.
논문 아이디어 실험은 `3_LDPC_ideas/` 아이디어 폴더에서 수행한다
(절차 정본: `3_LDPC_ideas/새논문적용규칙.md`).

- ㉮ `base_run/`는 재정의 없는 기준선이다 (모든 on/off 비교의 off 쪽)
- ㉯ 실행은 실험 폴더에서 `python run.py` (형제 config.json 사용,
  인자로 다른 config 경로도 지정 가능). 어느 위치에서 실행해도 동작한다
- ㉰ 새 기준 실험이 필요하면 `_template/`를 복사해 시작한다
  (run.py, config.json, README.md)
- ㉱ 결과는 각 실험 폴더의 `Sim_Output/`에 실행별 폴더로 쌓인다 (git 무시)
- ㉲ 입력(H-matrix, LLR)은 공용 `../Input/`을 쓴다 (config의 `../../Input/...`)
