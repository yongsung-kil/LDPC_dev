# minsum_dual_clip

날짜: 2026-08-14 | 출처: ieee:9496601 (A Low Bit-Width LDPC Min-Sum Decoding Scheme
for NAND Flash, IEEE TCAD 2022) | 상태: 조건부 유효 (실물 파라미터로 최종 판정 대기)

## 목적

CNU에서 min1은 상한 P로, min2는 상한 Q로 각각 클리핑(1 ≤ P ≤ Q)하면 진폭 성장이
늦어져 저비트폭 성능 손실이 완화된다는 논문 delta를 vanilla 대비 on/off로 확인한다.

## 바꾼 것

- 디코더: decoder.py의 MinSumDualClipDecoder, 재정의 함수: `_c2v_reconstruct`
  (C++ 대응: C2V_Cal). P, Q는 클래스 속성 CLIP_P, CLIP_Q로 전달
- 설정: config.json은 vanilla와 동일 조건 (seed 0, fixed_error [200, 300],
  frames_per_batch 64), label만 변경
- (P,Q) 스캔은 scan.py로 실행. config 파일과 쌍 목록을 인자로 받는다:
  `python scan.py [config파일] [P,Q P,Q ...]`

## 준비된 실험 (config 슬롯)

| config | 확인하려는 것 | 채울 슬롯 | 실행 |
|--------|--------------|-----------|------|
| config.json | 원 토이 환경 on/off (LLR 파일 로드, edge 상한 7) | 없음 (바로 실행) | `python scan.py` |
| config_headroom.json | edge 상한 여유의 영향 (균일 ch=8, edge 상한 15) | 없음 | `python scan.py config_headroom.json 15,15 8,11 4,8` |
| config_balanced.json | ch/edge 비율 복원 대조 (균일 ch=16, edge 상한 15) | 없음 | `python scan.py config_balanced.json 15,15 8,15 4,8` |
| config_real.json | 실물 파라미터 최종 판정 | H_matrix.file, decoder.llr_matrix.file 두 개 | `python scan.py config_real.json 7,7 5,7 3,5 2,3` |

config_real.json은 실물 H-matrix와 LLR 파일을 `Input/H_matrix/`, `Input/LLR/`에
넣고 파일명 두 개만 채우면 바로 실행된다. 스캔에 (7,7)을 포함하면 무클립
기준선이 같은 스캔 안에서 나온다 (3-bit 파일 기준. edge 상한이 다른 파일이면
무클립 쌍은 (상한, 상한)으로 바꾼다).

## 결과 (E=200 FER, 2026-08-13 ~ 08-14)

### 원 토이 환경 (LLR_MATRIX_HD_1.txt, dv별 ch 5/10/13/28, edge 상한 7)

| (P,Q) | FER | BER | avg_iter |
|-------|-----|-----|----------|
| vanilla | 4.84e-01 | 2.51e-05 | 12.2 |
| (7,7) 클리핑 무효과 | 4.84e-01 | 2.51e-05 | 12.2 |
| (5,7) | 5.16e-01 | 2.55e-05 | 12.6 |
| (5,5) | 9.38e-01 | 1.21e-04 | 19.0 |
| (3,7) | 8.59e-01 | 8.61e-05 | 17.9 |
| (3,5) | 9.38e-01 | 1.45e-04 | 19.2 |
| (3,3) | 1.00e+00 | 2.45e-03 | 20.0 |
| (2,5) | 9.69e-01 | 1.81e-04 | 19.6 |
| (2,3) 논문 가이드 근방 | 1.00e+00 | 2.40e-03 | 20.0 |
| (1,3) | 1.00e+00 | 2.42e-03 | 20.0 |
| (1,1) | 1.00e+00 | 5.33e-03 | 20.0 |

(7,7)이 vanilla와 수치 완전 일치하여 구현 동등성이 검증됨. 유효 클리핑은 전부 악화.

### 환경 대조 (edge 상한 15, 균일 LLR 생성)

| 환경 | 무클립 (15,15) | (8,11) | 논문 가이드 (4,8) |
|------|---------------|--------|-------------------|
| headroom (ch=8) | 1.00e+00 (BER 6.69e-02, 붕괴) | 6.41e-01 | **0.00e+00 (0/256)** |
| balanced (ch=16) | 0.00e+00 (0/256, 건강) | 2.50e-01 | 1.00e+00 |

## 결론

클리핑의 득실은 **채널 LLR 스케일 대비 edge magnitude 상한의 여유**가 결정한다.

- ㉮ 반전 가능 조건이 사망 경계를 정확히 예측한다: dv 열의 최대 extrinsic
  `Q + (dv-1)·P`가 그 dv의 ch보다 작으면 반전 불능. 원 토이의 지배 열
  dv=4(147개 중 129개)는 ch=10이라 (2,3)은 9로 사망(FER 1.0), (2,5)는 11로
  겨우 생존(9.69e-01). dv별 에러 로그로 직접 확인됨 ((2,3)에서 dv=4 에러가
  iter 2부터 79.2로 동결)
- ㉯ 원 토이의 dv별 ch(10/13/28)는 edge 상한 7 기준 반전 조건에 빠듯하게 튜닝되어
  있어 클리핑 여지가 없다 (dv=2는 ch=28 > 14라 무클립에서도 반전 불능,
  기지 위반). 반면 무클립이 과확신으로 붕괴하는 headroom 환경에서는 논문
  가이드값(P=상한/4, Q=상한/2)이 FER 1.0을 0으로 되돌린다: 논문의 이득 조건
  (내부 진폭이 채널 LLR보다 크게 성장하는 저비트폭 환경)이 토이에서도 재현됨
- ㉰ 같은 P에서 Q를 키우면 일관 개선: 이중 상한(P<Q)이 단일 상한(P=Q)보다 낫다는
  논문의 구조 주장은 모든 환경에서 방향 재현
- ㉱ 실물 판정 사전 지표: 실물 LLR set의 dv별 `ch / (edge상한 × dv)` 비율이 1에
  가까우면 클리핑 여지가 없고, 낮으면 (P,Q) 스캔 가치가 있다

유효 시 실물 C++ 이식 지점은 `decoder.cpp` `CNU_Update_New_Mag()`에 min1/min2
확정 직후 clip 2줄 (`M1m=min(M1m,P)`, `M2m=min(M2m,Q)`).
