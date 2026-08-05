# 3-5. 인코더 `% 2` → XOR/AND

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/encoder.cpp` |
| bit-exact | 보장 (GF(2) 항등식) |
| 위험 | 낮음 |

## 왜 / 어떻게

인코더 핫루프(프레임당 실행)의 값이 전부 0/1인데 add + signed `% 2`를 사용 — MSVC signed modulo는 부호 보정 시퀀스를 생성한다. GF(2) 항등식으로 치환:

- 곱셈-누적 (P × Msg, 프레임당 kb×z_sb×z_sb ≈ 13만 회): `tmp = (tmp + P*M) % 2` → `tmp ^= P & M`
- parity 누적: `(Parity + tmp) % 2` → `Parity ^ tmp`
- back-substitution (프레임당 PCM edge 수 × z_sb ≈ 10만 회 이상, 두 오버로드 × wrap 2변형): `(Parity + Codeword[...]) % 2` → `Parity ^ Codeword[...]`

## 유지한 곳

- `Build_P_All()`의 `% 2` — Init 1회라 성능 무관, "기존 로직 그대로 이동" 검증 근거 보존
- `__ENC_TV_INTER_DEBUG__` 블록, `Column_Reordering`의 `num_Dv2 % 2` (홀짝 판정, 호출당 1회)

## bit-exact 근거

0/1 값에 대해 `(a + b) % 2 == a ^ b`, `(a * b) == a & b`. 피연산자 도메인: P_all ∈ {0,1} (GF(2) 토글 결과), Msg/Codeword/Parity ∈ {0,1} (초기화·대입 전수 확인).

## 이식 앵커

인코더의 parity 누적/back-substitution 루프에서 `% 2` 검색. 피연산자가 0/1임을 먼저 확인 (shift 값 등 다른 modulo와 혼동 금지).
