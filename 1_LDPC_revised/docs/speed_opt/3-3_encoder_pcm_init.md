# 3-3. 인코더 PCM 전처리를 Init으로 이동

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/encoder.cpp` |
| bit-exact | 보장 |
| 위험 | 낮음 |

## 왜 / 어떻게

`LDPC_encoder_4KB()`(두 오버로드)가 **매 프레임** `Generate_PCM_encoding()`으로 인코딩용 PCM(`PCM_b_enc`)을 재생성했다 — 입력(`PCM_b`)은 시뮬레이션 내내 불변인데 M_b×N_b(수만 int) 복사+재배열을 반복.

호출을 `Init_Enc()`로 이동 (1회). 두 오버로드에서 호출 제거. `shuffled_dual_diag` 플래그는 컴파일 스위치라 Init에서 동일하게 결정.

## 안전성 확인

- 호출 순서: `Load_PCM()` → `Init_Enc()` (ecc_top.cpp 3개 Setup 경로 전수 확인) — Init 시점에 PCM_b가 채워져 있음
- PCM_b를 런타임에 변경하는 지점 없음 (기존 분석에서 확인)

## 이식 앵커

인코딩 함수 안의 `Generate_PCM_encoding` 계열(입력이 불변 PCM뿐인 전처리) 호출을 찾아 Encoder 초기화로 이동. **반드시 그 버전의 Init 호출 시점에 PCM이 로드 완료 상태인지 확인.**
