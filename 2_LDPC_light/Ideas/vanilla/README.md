# vanilla: 원본 대응 reference

## 무엇인가

- ㉮ 원본 C++ vanilla(HCU, 펑처링, 쇼트닝, dual update, CRC 조기종료 제거판)에 대응하는
  **비교 기준선(reference)**. 어떤 교체용 함수도 재정의하지 않아 LDPC_base 정본과 동작이 같다
- ㉯ 모든 논문 아이디어의 on/off 비교에서 "off" 쪽이 이 디코더다
- ㉰ reference 실험(실물 H-matrix, LLR_MATRIX 반입 후 기준 FER 커브 확보 등)은
  이 폴더의 config.json으로 수행하고, 결과는 이 폴더의 `Sim_Output/`에 쌓는다

## 실행

`2_LDPC_light/`에서:

```bat
python -m LDPC_base.run Ideas/vanilla/config.json
```

## 새 아이디어 추가 절차 (이 폴더를 템플릿으로)

- 1. `Ideas/{아이디어명}/` 폴더를 만들고 이 폴더의 4개 파일을 복사
- 2. `decoder.py`: `MinSumDecoder`를 상속한 자식 클래스에서 **교체용 함수만 재정의**
     (재정의 = 부모 클래스의 함수를 자식 클래스에서 다른 내용으로 바꿔 채우는 것.
     교체용 함수 목록과 C++ 대응은 `LDPC_base/decoder.py` 모듈 docstring의 표 참조.
     교체 지점에 안 들어맞는 근본적 변경만 `decoder_main` 전체 재정의)
- 3. `Ideas/registry.py`의 DECODERS에 등록
- 4. `config.json`의 `decoder.type`을 아이디어명으로 바꾸고 실행
- 5. `README.md`에 기록: 논문 출처, 요지, 재정의한 교체용 함수, **실물 C++ 이식 시
     수정할 함수**(교체용 함수의 C++ 대응이 그대로 답이 된다), 결과 요약
- 6. vanilla와의 비교: 같은 seed로 두 config를 각각 실행 (채널·포인트 동일하게)

## 주의

- 베이스 개선이 모든 아이디어에 자동 전파되어야 하므로, LDPC_base(정본)에는
  아이디어 코드를 넣지 않는다
- 이 vanilla 폴더의 decoder.py도 비워 둔 채(재정의 없음) 유지한다
