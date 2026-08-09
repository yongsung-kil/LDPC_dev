"""아이디어 디코더 등록부: config의 decoder.type 이름 → 클래스 경로.

"vanilla"는 재정의 없는 기준 실험이라 LDPC_base의 BaseDecoder를 직접 가리킨다.
새 아이디어 등록은 "{아이디어명}": "Ideas.{아이디어명}.decoder:{클래스명}" 형식이며,
절차와 규칙의 정본은 docs/새논문적용규칙.md다.
"""

DECODERS = {
    "vanilla": "LDPC_base.decoder:BaseDecoder",
}
