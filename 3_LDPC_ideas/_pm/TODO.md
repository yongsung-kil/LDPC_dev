# TODO — 3_LDPC_ideas (Project 3)

> Claude 마지막 확인: 2026-08-14 11:05:05

> 이 파일은 Project 3 전용 작업만 관리한다.

---

## 작업 목록

- [ ] minsum_dual_clip (ieee:9496601) 실물 파라미터 최종 판정
  - 선행: 실물 H-matrix와 LLR 반입 (2_LDPC_base TODO의 반입 항목)
  - 실행: `001_minsum_dual_clip/config_real.json`에 파일명 두 개 채우고
    `python scan.py config_real.json 7,7 5,7 3,5 2,3`
  - 사전 지표: 실물 LLR set의 dv별 ch / (edge상한 × dv) 비율이 1에 가까우면
    클리핑 여지 없음 (실험로그.md 2026-08-14 항목 참조)

- [ ] 논문 아이디어 스크리닝 계속 (아카이브 stage5 산출물 순서대로 py 실험,
      실물 파라미터 반입 후에는 base_run reference 커브 확보를 선행)
- [ ] 유효 아이디어의 실물 C++ 이식과 최종 검증

## 새 작업 추가

(비어 있음)
