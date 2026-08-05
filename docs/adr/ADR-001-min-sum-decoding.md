# ADR-001: Min-Sum 기반 LDPC 복호 알고리즘

상태: 추정 (코드 역추적) | 날짜: 2026-05-08

## 제약
HW 구현 복잡도 제한. NAND Flash 컨트롤러 내장 ECC로 면적/전력 제약 있음.

## 결정
Min-Sum 변형 사용. CN 연산에서 min1/min2 값과 position만 추적 (`REG_min1_value`, `REG_min2_value`, `REG_min1_pos`). Sign은 XOR 기반 (`Check_SRAM_sgn`). Belief Propagation(BP)의 tanh 연산 대신 min 연산으로 대체.

## 거부한 대안
- Sum-Product (BP): tanh 연산 HW 비용 과다
- Offset/Normalized Min-Sum: 코드에 scaling factor 미확인 — 순수 min-sum 또는 별도 LLR 테이블로 보정하는 방식 추정

## 영향 파일
- `LDPC_Original/decoder.cpp` — `CNU_Update_New_Mag()`, `C2V_Cal_New_Sgn()`
- `LDPC_Original/decoder.h:79` — min1/min2/min1_pos 레지스터
