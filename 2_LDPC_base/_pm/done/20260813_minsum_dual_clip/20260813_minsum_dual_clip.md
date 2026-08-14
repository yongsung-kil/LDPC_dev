# minsum_dual_clip: CNU min1/min2 이중 상한 클리핑 (ieee:9496601)

날짜: 2026-08-13 | 등급: Review (베이스 무변경, 실험 폴더 신규만)

## 목적

논문 ieee:9496601 (A Low Bit-Width LDPC Min-Sum Decoding Scheme for NAND Flash,
IEEE TCAD 2022)의 핵심 delta를 workspace 실험으로 얹어 vanilla 대비 on/off
상대 비교를 수행한다.

## 배경

- ㉮ 논문 요지: CNU에서 min1은 상한 P로, min2는 상한 Q로 각각 클리핑한다
  (P ≤ Q ≤ 진폭 상한). 진폭 성장 속도를 늦춰 저비트폭에서 error floor를 지연시킨다
- ㉯ 논문 아카이브(형제 저장소 LDPC_Paper_Analysis)의 stage5 산출물이 준비되어 있다:
  `criteria/stage5/results/ieee_9496601/` (pseudocode.md, impl.py,
  integration_patch.md, verification_plan.md)
- ㉰ 실물 C++ 이식 지점은 `decoder.cpp`의 `CNU_Update_New_Mag()`이다
  (min1/min2 확정 직후 clip 2줄)

## 설계

- ㉮ 실험 폴더: `workspace/minsum_dual_clip/`
- ㉯ `BaseDecoder` 상속, `_c2v_reconstruct` 하나만 재정의 (C++ 대응: C2V_Cal).
  min1_row는 P로, min2_row는 Q로 클리핑한 뒤 기존 선택식을 그대로 쓴다
- ㉰ 저장 상태(`_cnu_update`)를 건드리지 않는 이유: 이 시뮬레이터는 min1/min2를
  증분 갱신(remove old, insert new)하므로 저장 상태를 클리핑하면 remove old
  추적이 오염된다. 출력 재구성 시점 클리핑이 논문의 식(3) 대입 직전 클리핑과 등가다
- ㉱ P, Q는 실험 decoder.py의 클래스 속성으로 전달한다 (사용자 확정 2026-08-13).
  config 통로 신설(checker 허용 키 확장 + setup 전달)은 별도 작업으로 미룬다
- ㉲ P, Q 도메인: edge magnitude 레벨 도메인 (기본 3-bit 레벨 {7,5,3,1}, 상한 7).
  정수 클리핑이므로 균일 등가식 전제(비정수 메시지 금지)를 지킨다

## 사전 검증 (완료)

- ㉮ 베이스 회귀: refactor 4건(045de23, 8841f51, 348f568, c031910) 전후 수치 일치.
  refactor 직전 30e3708을 worktree로 꺼내 vanilla 동일 조건 실행,
  E=200 FER 4.84e-01 BER 2.51e-05 avg_iter 12.2, E=300 FER 9.84e-01
  BER 1.52e-04 avg_iter 19.9로 현재 HEAD와 완전 일치 (2026-08-13)
- ㉯ 260810 기준 실행(FER 1.0)과의 차이는 성공 판정 변경(2bd85c9, information
  구간만 검사)과 post-FEC BER 기준 변경(229f0d5)의 의도된 결과다

## 수정 대상 파일

- ㉮ 신규: `workspace/minsum_dual_clip/` (run.py, config.json, README.md, decoder.py)
- ㉯ `LDPC_base/`는 변경하지 않는다

## 안전성 체크리스트

- [x] LDPC_base 무변경 (아이디어 코드는 실험 폴더에만)
- [x] vanilla 재정의 0개 유지
- [x] 재정의 함수의 인자 목록이 부모와 동일
- [x] on/off 비교 시 seed, 채널, 포인트, frames_per_batch 동일

## 실험 결과 (2026-08-13)

- ㉮ 스캔 범위: (P,Q) 10쌍, P=Q 대조군 3쌍 포함. (7,7)은 클리핑 무효과 조건으로
  vanilla와 수치 완전 일치, 구현 동등성 검증됨
- ㉯ 원 토이 환경에서 모든 유효 클리핑이 악화 (P가 작을수록 단조 악화). 원인 규명
  (2026-08-14 dv별 로그와 LLR 파일 실값으로 확정): dv 열의 최대 extrinsic
  `Q + (dv-1)·P`가 그 dv의 채널 LLR(파일 실값 dv=4: 10, dv=3: 13, dv=2: 28)보다
  작으면 반전 불능. 지배 열 dv=4가 (2,3)에서 9 < 10으로 사망
- ㉰ 같은 P에서 Q를 키우면 일관 개선: 이중 상한(P<Q)이 단일 상한(P=Q)보다 낫다는
  논문의 구조 주장은 방향 재현
- ㉱ 환경 대조 (2026-08-14): edge 상한 15 + 균일 ch=8(headroom)에서는 무클립이
  붕괴(FER 1.0)하고 논문 가이드 (4,8)이 0/256로 완전 복구. ch=16(balanced)으로
  비율을 되돌리면 무클립이 건강해지고 (4,8)은 사망. 클리핑 득실은 채널 LLR
  스케일 대비 edge 상한 여유가 결정
- ㉲ 판정: 조건부 유효. 실물 H-matrix와 LLR 반입 후 최종 판정
  (사전 지표와 슬롯 config: 실험 폴더 README.md)

## 한계 (인지 사항)

토이 파라미터(z=256 예시 H-matrix) 상대 비교라 절대 성능 판단은 불가하다.
논문 이득은 저비트폭 대형 부호의 error floor 영역에서 발현되므로 토이 부호에서
효과가 뚜렷하지 않을 수 있다. 실물 H-matrix와 LLR 반입 후 재검증한다.
