# ADR-004: Iteration별 적응형 LLR 테이블

상태: 추정 (코드 역추적) | 날짜: 2026-05-08

## 제약
고정 LLR threshold로는 다양한 에러 패턴/iteration 구간에서 최적 성능 달성 불가. NAND Flash 특성상 에러 분포가 비균일.

## 결정
Iteration 구간별 LLR 파라미터를 다르게 적용. `PARAM_LLR` 구조체에 구간별 테이블 저장. `Get_VNU_Table_Idx(iter)`로 현재 iteration에 맞는 테이블 선택. HD/2SD/3SD 모드별 별도 테이블 (63/36/66 행).

## 거부한 대안
- 고정 LLR: 단순하나 FER 성능 열위
- BP 정밀 LLR: HW 구현 비용 과다

## 영향 파일
- `LDPC_Original/decoder.h:122-126` — `Get_VNU_Table_Idx`, `Get_VNU_Ch_LLR_Adaptive`, `Get_VNU_Th_Adaptive`
- `LDPC_Original/common.h:396-688` — LLR 테이블 인덱스 enum, iteration 구간 상수
- `LDPC_Original/ecc_data.h:179-198` — `PARAM_LLR` 구조체
