# ADR-003: Shuffled Dual-Diagonal 인코딩

상태: 채택 | 날짜: 2026-05-08

## 제약
Dual Update 모드에서 parity column을 even/odd로 나눠 교대 처리해야 함. 인코딩 시 column 순서가 디코딩 시 dual update 순서와 맞아야 함.

## 결정
인코딩 후 parity column을 재배치 (`Column_Reordering_Dual_Update`). PCM_b → PCM_b_enc 변환 시 even/odd 분리 (`Generate_PCM_encoding`). `__SHUFFLED_DUAL_DIAG__` 매크로로 제어.

## 거부한 대안
- 순차 dual-diagonal: Dual Update 비활성 시 사용 가능하나 성능 열위

## 영향 파일
- `0_LDPC_original/src/encoder.cpp:245-335` — `Column_Reordering_Dual_Update`, `Generate_PCM_encoding`
- `0_LDPC_original/src/mode.h:65` — `__SHUFFLED_DUAL_DIAG__` 정의
