# base_run: 원본 대응 기준 실험

## 무엇인가

- ㉮ 원본 C++의 단순화 형태(HCU, 펑처링, 쇼트닝, dual update, CRC 조기종료 제거판)에
  대응하는 **비교 기준선(reference) 실험**. 디코더는 `src`(본체 코드)의 `BaseDecoder`를 재정의 없이
  그대로 쓴다 (run.py의 `DECODER_CLASS = None`이 그 연결이라 이 폴더에 decoder.py가 없다.
  재정의 0개가 곧 "본체와 완전히 같다"는 보증이다)
- ㉯ 모든 논문 아이디어의 on/off 비교에서 "off" 쪽이 이 실험이다
- ㉰ reference 실험(평가 대상 H-matrix와 LLR_MATRIX의 기준 FER 커브 확보 등)은
  이 폴더의 config.json으로 수행하고, 결과는 이 폴더의 `Sim_Output/`에 쌓는다

## 실행

이 폴더에서:

```bat
python run.py
```

## 새 실험 추가

절차, 교체용 함수 표, 상속 경계 규칙, 지킬 규칙의 정본은
[3_LDPC_ideas/새논문적용규칙.md](../../../3_LDPC_ideas/%EC%83%88%EB%85%BC%EB%AC%B8%EC%A0%81%EC%9A%A9%EA%B7%9C%EC%B9%99.md)다.
논문 아이디어 실험은 `3_LDPC_ideas/_template/`를 복사해 시작한다.
