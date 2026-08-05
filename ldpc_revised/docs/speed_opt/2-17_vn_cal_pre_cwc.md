# 2-17. `VN_Cal_Pre()` cwc hard-decision 분기 축소

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 / 어떻게

`VN_Cal_Pre()`의 hard decision 루프는 기본 판정(`Variable_mem == 0 ? 0 : 1`) 후 puncture 구간 3분기에서 **완전히 동일한 판정을 반복**한다 (원래 `cwc = 1` 강제였던 흔적이 주석으로 남아 있고, 현재는 전부 같은 동작). 원소당 최대 6개 비교가 순수 낭비 →

```cpp
cwc[bit_pos] = (Variable_mem[bit_pos] != 0);
```

한 줄로 축소. `(x != 0)`은 x가 어떤 값이어도 기존 `== 0 ? 0 : 1` 판정과 동일.

## 유지한 것 (중요)

**`VN_Cal_Pre_HCU()`의 같은 패턴은 유지** — 세 번째 분기(parity puncture)가 `cwc[bit_pos] = 1;` 강제로 **동작이 다름**. 앞의 두 분기는 중복이지만 부분 수정의 위험 대비 이득이 작아 전체 유지.

## 이식 앵커

"make hard decision" 주석 + puncture 예외처리 분기 검색. **분기마다 대입 내용이 정말 동일한지 반드시 확인** — HCU판처럼 강제 대입이 남아있는 변형은 축소 금지.
