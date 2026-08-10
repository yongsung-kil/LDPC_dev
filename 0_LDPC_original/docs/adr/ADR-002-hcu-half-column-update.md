# ADR-002: Half Column Update (HCU) 모드

상태: 채택 | 날짜: 2026-05-08

## 제약
Col 127, 128은 punctured column과 parity의 경계에 위치하여 VN degree가 비대칭 (9/7). 한 cycle에 full column (degree 17)을 처리하면 타이밍 위반 발생 가능.

## 결정
Col 127, 128을 half로 나눠 2 cycle에 걸쳐 처리 (`__HALF_COL_UPDATE__`). Even/Odd iteration에서 G0/G1 그룹을 교번 처리. MUX 경계(8)로 물리적 분할, SEPARATE_V_DEG(9/7)로 논리적 분할.

## 거부한 대안
- Full column 처리: 타이밍 위반 위험
- Col 0,1 위치 사용 (`__HALF_COL_MODIFIED__` 미정의): 구형 방식, 현재 col 127,128로 이동 완료

## 영향 파일
- `0_LDPC_original/src/decoder.cpp` — `C2V_cal_HCU()`, `V2C_Cal_HCU()`, `VN_Cal_*_HCU()`, jj_temp 매핑 블록 2개소
- `0_LDPC_original/src/decoder.h:91-98` — HCU 전용 메서드
- `0_LDPC_original/src/TV_Dec_Inter.cpp` — `Print_TV_*_HCU()` 읽기 함수
- `0_LDPC_original/src/common.h:378-383` — `HCU_COL_1_IDX`, `SEPARATE_V_DEG_*`
