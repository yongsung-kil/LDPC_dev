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

## 새 아이디어 추가

절차, 교체용 함수 표, 상속 경계 규칙, 지킬 규칙의 정본은
[docs/새논문적용규칙.md](../../docs/새논문적용규칙.md)다.
이 폴더의 config.json과 README.md가 새 아이디어 폴더의 틀이 된다.
