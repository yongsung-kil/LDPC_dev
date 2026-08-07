"""아이디어 디코더 등록부 — config의 decoder.type 이름 → 클래스 경로.

새 아이디어 추가 절차:
  1. Ideas/{아이디어명}/ 폴더 생성 (decoder.py, config.json, README.md)
  2. decoder.py에 LDPC_base.decoder.MinSumDecoder를 상속한 자식 클래스 작성
     (교체용 함수만 재정의 — 목록은 LDPC_base/decoder.py docstring의 표)
  3. 아래 DECODERS에 "{아이디어명}": "Ideas.{아이디어명}.decoder:{클래스명}" 등록
  4. config.json의 decoder.type에 아이디어명 지정 후 실행
"""

DECODERS = {
    "vanilla": "Ideas.vanilla.decoder:VanillaDecoder",
}
