# 3-2. full CRC 버퍼 재사용 (프레임당 517회 할당 제거)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/full_CRC.cpp` |
| bit-exact | ShortenedBit == 0 경로에서 보장 (아래 참조) |
| 위험 | 낮음 |

## 왜 / 어떻게

`CRC_encoder()` / `CRC_decoder()`(오버로드 2종)는 프레임마다 `msg = new int*[516]` + 행별 `new int[ZSB_CRC]` 516회 + delete 516회를 반복 — 프레임당 heap 연산 1000회 이상. 버퍼를 함수 static으로 승격해 최초 1회만 할당하고 재사용 (행 수가 커지면 재할당하는 방어 로직 포함). GEN_CRC80 / CRC_LFSR / 다항식은 **일절 무수정**.

## bit-exact 근거 / 주의

- `ShortenedBit == 0`(통상 경로): msg 전 셀과 crc_par가 매 호출 완전히 덮어써짐 → 재사용해도 값 동일
- `ShortenedBit != 0` 경로: **기존 코드도 msg/crc_par를 채우지 않은 채 사용(UB, 쓰레기 값)** — 재사용 후에는 이전 프레임 값(결정적)을 읽게 됨. UB → 결정적 동작으로 바뀔 뿐, 정상 경로 아님 (원본의 잠재 버그로 문서화)
- 프로그램 종료 시 static 버퍼는 해제하지 않음 (프로세스 종료로 회수 — 의도적)

## 이식 앵커

CRC encoder/decoder의 `new int*[...]` 패턴 검색. GEN_CRC80 계열과 다항식 상수는 수정 금지. ShortenedBit 경로의 미기록 사용이 그 버전에도 있는지 확인해 둘 것.
