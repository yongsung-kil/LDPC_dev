# workspace: 실험 공간

실험(논문 아이디어, 조건 탐색)마다 폴더 하나를 만들어 그 안에서 실행하고 결과를 쌓는다.

- ㉮ 새 실험은 `_template/`를 복사해 시작한다 (run.py, config.json, README.md).
  폴더 이름은 논문이나 실험 내용으로 자유롭게 짓는다
- ㉯ 실행은 실험 폴더에서 `python run.py` (형제 config.json 사용,
  인자로 다른 config 경로도 지정 가능). 어느 위치에서 실행해도 동작한다
- ㉰ 디코더 변형은 실험 폴더에 decoder.py를 만들고 run.py의 `DECODER_CLASS`로
  지정한다 (절차 정본: [docs/새논문적용규칙.md](../docs/새논문적용규칙.md))
- ㉱ `vanilla/`는 재정의 없는 기준선이다 (모든 on/off 비교의 off 쪽)
- ㉲ 결과는 각 실험 폴더의 `Sim_Output/`에 실행별 폴더로 쌓인다 (git 무시)
- ㉳ 입력(H-matrix, LLR)은 공용 `../Input/`을 쓴다 (config의 `../../Input/...`)
