"""아이디어 디코더 등록부: config의 decoder.type 이름 → 클래스 경로.

"vanilla"는 재정의 없는 기준 실험이라 LDPC_base의 BaseDecoder를 직접 가리킨다.

새 아이디어 추가 절차:
  1. Ideas/{아이디어명}/ 폴더 생성 (decoder.py, config.json, README.md)
  2. decoder.py에 LDPC_base.decoder.BaseDecoder를 상속한 자식 클래스 작성
     (교체용 함수만 재정의하며, 목록은 LDPC_base/decoder.py docstring의 표.
     생성자는 (code, llr_matrix=...) 형태를 유지한다. run.py setup이 이렇게 호출)
  3. 아래 DECODERS에 "{아이디어명}": "Ideas.{아이디어명}.decoder:{클래스명}" 등록
  4. config.json의 decoder.type에 아이디어명 지정 후 실행
"""

DECODERS = {
    "vanilla": "LDPC_base.decoder:BaseDecoder",
}
