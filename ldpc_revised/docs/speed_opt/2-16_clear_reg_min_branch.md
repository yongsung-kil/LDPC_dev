# 2-16. `Clear_REG_min_value()` 무의미 분기 제거

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 / 어떻게

M(4128) 루프 안에서 HD/1.5SD와 2SD/3SD를 매 원소 비교하지만 **양쪽 분기가 완전히 동일한 값**(3bit: `V_VERY_STRONG`, 4bit: `V_MAG7`)을 대입한다. 값을 루프 밖 `const int min_init`으로 빼고 분기 제거. 실행 빈도: restart iteration마다 (HD는 iter 0/1/HBF+1, SD는 restart 시점마다).

- 어떤 모드에서도 대입 값이 기존과 동일 → bit-exact
- 도달 불가 모드(둘 다 아닌 init_n)에서는 기존에 min1이 미대입이었으나, 해당 모드는 존재하지 않음(MODE_DEC_* 전수) — 주의로 기록

## 이식 앵커

`Clear_REG_min_value` 계열에서 분기별 대입 값이 정말 같은지 그 버전에서 다시 확인 후 적용 (값이 다르면 이 항목 자체가 해당 없음).
