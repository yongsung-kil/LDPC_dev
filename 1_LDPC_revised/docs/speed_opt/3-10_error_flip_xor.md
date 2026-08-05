# 3-10. 에러 주입 flip `(x+1)%2` → `^= 1`

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/ecc_top.cpp` |
| bit-exact | 보장 (값 도메인 0/1) |
| 위험 | 낮음 |

## 왜 / 어떻게

fixed-error 채널의 에러 주입이 위치마다 이중 인덱싱 2회 + add + signed modulo(`HD_input[pos] = (HD_input[pos] + 1) % 2`)를 수행. `^= 1`로 치환 (HD 4곳 + CD 1곳). 프레임당 에러 수만큼 실행.

## 이식 앵커

`m_err_position` 기반 flip 루프 검색. 값이 0/1인 bit 버퍼에만 적용.
