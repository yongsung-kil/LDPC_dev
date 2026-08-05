# 3-6. `xor_r25()` 상태 시프트를 memmove로

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/random.cpp` |
| bit-exact | 보장 (상태 배열 표현·출력 시퀀스 동일) |
| 위험 | 낮음 |

## 왜 / 어떻게

XOR25 난수 1개 생성마다 25-word 상태 배열을 24회 원소별로 밀었다 — 메시지 bit당 + AWGN bit당 호출되어 프레임당 수십만 회의 원소 이동. `memmove(a, a+1, 24*sizeof(unsigned int))` 단일 호출로 치환 (src/dst가 겹치므로 memcpy가 아닌 memmove).

## bit-exact 근거

상태 배열의 선형 표현이 그대로 유지되므로 출력 w 시퀀스, `Get/Set_Random_Seed`의 seed 저장/복원 포맷 모두 기존과 완전 동일.

## 더 나아갈 수 있는 것 (미적용)

circular index 방식(O(24)→O(1))은 seed 저장/복원 시 선형 정규화가 필요해 검증 부담이 있어 보류 — checklist 원안의 2단계. double 왕복 제거는 Phase 5-6(검증 필요 항목).

## 이식 앵커

XOR25(또는 유사 LFSR 계열)의 상태 시프트 루프 검색. 배열 표현을 바꾸지 않는 memmove까지만이 무검증 안전 범위.
