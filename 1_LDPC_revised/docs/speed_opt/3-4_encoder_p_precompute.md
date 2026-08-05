# 3-4. 인코더 P 행렬 사전 계산

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/encoder.h`, `encoder.cpp` |
| bit-exact | 보장 (동일 로직을 Init으로 이동, 값 동일) |
| 위험 | 중간 — 인코더 출력 codeword 전수 비교 검증 권장 |

## 왜 / 어떻게

`LDPC_encoder_dual_diagonal()`은 프레임마다 kb(≈129)개 column 각각에 대해 32×32 P 행렬을 clear(1024 대입) → M_b(129)행 스캔으로 재구축 → 32×32 곱을 수행했다. P는 **PCM_b_enc column j만의 함수**(메시지 무관)라 프레임마다 재구축할 이유가 없다.

- `P_all[kb][z_sb][z_sb]`(≈2MB) 멤버 신설, `Build_P_All()`이 **기존과 동일한 구축 로직**으로 Init에서 1회 채움 (3-3의 Generate_PCM_encoding 직후 — PCM_b_enc 완성 시점)
- 두 dual_diagonal 오버로드의 clear+재구축 블록 삭제 → `int** Pj = P_all[j];` 참조 후 곱셈만 수행
- 기존 멤버 `P`(단일 32×32 작업 버퍼)는 제거

## bit-exact 근거

- Build_P_All의 구축 코드는 기존 루프를 그대로 옮긴 것 (조건·순서·`% 2` 포함 동일) — P 값 자체가 동일
- 곱셈·누적 식 무변경 (연산 형태는 3-5에서 별도 처리)
- 전제: dual_diagonal은 항상 `PCM_b_enc`로 호출됨 (두 호출부 전수 확인 — 주석으로 명시)

## 이식 앵커

1. dual-diagonal 인코더의 "column마다 P 재구축" 루프를 검색
2. 구축 로직을 **문자 그대로** Init 전처리로 복사 (임의 재작성 금지 — 값 동일성이 검증 근거)
3. 그 버전에서 dual_diagonal에 전달되는 PCM이 단일(불변) 소스인지 호출부 전수 확인 — 여러 PCM으로 호출되면 column 키에 PCM 구분 추가 필요
4. 적용 후 기존/신규 인코더의 출력 codeword를 수천 프레임 전수 비교
