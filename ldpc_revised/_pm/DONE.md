# DONE — 완료 이력 (ldpc_revised)

### 2026-07-23 — 속도 최적화 체크리스트 전 항목 종료
`docs/speed_opt/checklist.md` 전 항목 적용 완료, 전달 패키지 완성 (checklist + 항목 문서 28편 + patches + commits.md)
- **배경**: Ref-C 실행 시간 단축. 항목당 1커밋, grep 검증, 상세 문서, patch 생성 방식으로 진행
- **변경**:
  - Phase 2 전체 (2-1 ~ 2-19, 2-20은 제외 결정): shift_mem 사전 계산, 루프 불변 hoisting, LLR 텍스트 파일 파라미터화 등
  - Phase 3 전체 (3-1 ~ 3-14): CRC 버퍼, encoder 사전 계산, memcpy 치환 등
  - Phase 4: 4-3 CN 상태 struct 묶음, 4-4 int8_t 축소 (4-1, 4-2는 사용자가 체크리스트에서 제거). 4-3에서 2-18 유래 비TV 빌드 컴파일 회귀(Print_TV_Cycle_Based) 발견, 해소
  - Phase 5: 5-6 xor_r25 double 왕복 제거, 2^32 전수 검증(mismatch 0)으로 bit-exact 승격 후 적용 (5-1, 5-2는 사용자가 제거)
  - Phase 6: 6-1 PMU_Read/PMU_Read_HCU OOB 읽기와 쓰기 수정(factor 반영), 6-2 DU_Manager 범위 검사 순서. FER 무관
- **파일**: `decoder.cpp/.h`, `encoder.cpp/.h`, `ecc_top.cpp`, `full_CRC.cpp`, `partial_CRC.cpp`, `random.cpp/.h` (수정 파일만 이 폴더에 보관)

### 2026-08-03 — iteration당 속도 측정 시뮬레이션 추가
15x145 z256 부호 생성 스크립트와 측정 스크립트 작성 (상세: `_pm/tasks/260803_iteration당속도측정/`)
- **배경**: 속도 개선 효과를 iteration당 시간으로 정량화
- **변경**: 원본 대응 shortening/puncturing 반영 (15x145 degree 내림차순 재배치), H-matrix 파일 포맷을 Ref-C 원본 Load_PCM과 동일하게 변경
- **파일**: `_pm/tasks/260803_iteration당속도측정/` (gen_code_15x145.py, measure_speed.py, irregular_15x145_z256.qc)
