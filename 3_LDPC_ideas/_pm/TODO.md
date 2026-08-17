# TODO — 3_LDPC_ideas (Project 3)

> Claude 마지막 확인: 2026-08-17 18:17:49

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
  - 후보 10건 선별 완료 (2026-08-17, 조건: 양자화 hard-1bit/soft-2~3bit,
    rate > 0.6, 길이 8192bit 이상. stage3 6214건 중 148건 통과 후 접점 기준 선별):
    - 1. ieee:6865103 (2014) min1/min2 상한 + 비균일 양자화 + 동적 정규화,
         `_c2v_reconstruct`. 001 직계 확장이라 즉시성 최상
         [x] 2026-08-17 스크리닝 완료 → `002_minsum_dynamic_normalization/`,
             조건부 유효 (이득 조건에서 001 클리핑과 결합 시 전 조합 최량,
             격차 임계 T는 edge 레벨 간격으로 튜닝 필수). 실물 파라미터 반입
             후 config_real.json 스캔으로 최종 판정 (001과 같은 선행 조건)
    - 2. arxiv:2206.11532v1 (2022, ieee:9979226 동일 논문) 저차수 VN 메시지
         가중으로 error floor 감소, `_c2v_reconstruct` (dv별 가중)
    - 3. ieee:10001160 (2022) 상호정보 최대화 LUT 양자화 (RCQ 계열),
         `_vnu_quantize` + `_c2v_reconstruct`. LUT 오프라인 설계 선행
    - 4. ieee:11476755 (2026) RCQ LUT FPGA 구현판. 스크리닝은 3번으로, 구현 참고용
    - 5. ieee:6272052 (2012) HD 첫 iter 소형 LLR + offset/normalized 매핑,
         iteration별 LLR 테이블
    - 6. ieee:8351684 (2018) 2-bit 메시지 패싱 + syndrome weight C2V 보정,
         `_c2v_reconstruct` + `_column_order`
    - 7. ieee:11154047 (2026) SiDTBF 강/약 정보 bit-flipping. 패밀리가 달라
         `decoder_main` 전체 재정의 필요
    - 8. ieee:6804933 (2014, arxiv:1210.0149 연작) multi-read 전압 상호정보
         최적 배치, 채널 LLR 설계 (2SD/3SD threshold)
    - 9. ieee:10098900 (2023) 성공 프레임 채널 재추정 LLR 보정 후 재복호,
         run 루프 레벨
    - 10. ieee:11539179 (2026) syndrome 합 기반 복호 모드 적응 선택, 제어
          레벨 (`csw` 로그 재사용 가능)
- [ ] 유효 아이디어의 실물 C++ 이식과 최종 검증

## 새 작업 추가

(비어 있음)
