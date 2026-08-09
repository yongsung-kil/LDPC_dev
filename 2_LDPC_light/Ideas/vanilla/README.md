# vanilla: 원본 대응 기준 실험

## 무엇인가

- ㉮ 원본 C++ vanilla(HCU, 펑처링, 쇼트닝, dual update, CRC 조기종료 제거판)에 대응하는
  **비교 기준선(reference) 실험**. 디코더는 `LDPC_base`의 `BaseDecoder`를 재정의 없이
  그대로 쓴다 (registry가 직접 연결하므로 이 폴더에 decoder.py가 없다.
  재정의 0개가 곧 "본체와 완전히 같다"는 보증이다)
- ㉯ 모든 논문 아이디어의 on/off 비교에서 "off" 쪽이 이 실험이다
- ㉰ reference 실험(실물 H-matrix, LLR_MATRIX 반입 후 기준 FER 커브 확보 등)은
  이 폴더의 config.json으로 수행하고, 결과는 이 폴더의 `Sim_Output/`에 쌓는다

## 실행

`2_LDPC_light/`에서:

```bat
python -m LDPC_base.run Ideas/vanilla/config.json
```

## 새 아이디어 추가 절차 (이 폴더를 템플릿으로)

- 1. `Ideas/{아이디어명}/` 폴더를 만들고 이 폴더의 config.json과 README.md를 복사,
     빈 `__init__.py`와 새 `decoder.py`를 만든다
- 2. `decoder.py`: `BaseDecoder`를 상속한 자식 클래스에서 **교체용 함수만 재정의**
     (재정의 = 부모 클래스의 함수를 자식 클래스에서 다른 내용으로 바꿔 채우는 것.
     교체용 함수 목록과 C++ 대응은 `LDPC_base/decoder.py` 모듈 docstring의 표 참조.
     교체 지점에 안 들어맞는 근본적 변경만 `decoder_main` 전체 재정의.
     생성자는 `(code, llr_matrix=...)` 형태를 유지한다)
- 3. `Ideas/registry.py`의 DECODERS에 등록
- 4. `config.json`의 `decoder.type`을 아이디어명으로 바꾸고 실행
- 5. `README.md`에 기록: 논문 출처, 요지, 재정의한 교체용 함수, **실물 C++ 이식 시
     수정할 함수**(교체용 함수의 C++ 대응이 그대로 답이 된다), 결과 요약
- 6. vanilla와의 비교: 같은 seed로 두 config를 각각 실행 (채널과 포인트 동일하게)

## 주의

- 베이스 개선이 모든 아이디어에 자동 전파되어야 하므로, LDPC_base(정본)에는
  아이디어 코드를 넣지 않는다
- vanilla 실험에는 디코더 코드를 두지 않는다 (BaseDecoder 그대로가 기준선이다)
