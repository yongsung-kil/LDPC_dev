# 커밋 인덱스 — speed_opt 관련 커밋 누적 기록

> 항목 하나 = 커밋 하나 원칙. 각 커밋의 해시는 **그다음 커밋에서** 이 파일에 추가된다 (한 박자 지연 — 의도된 방식).
> 전달받은 쪽: 이 표의 커밋 해시로 `git show <hash>`를 하면 해당 항목의 diff를 볼 수 있다 (git 히스토리를 함께 받은 경우).
> git 없이 받은 경우는 `patches/{ID}.patch`가 동일 내용이다.

| 커밋 | 구분 | 내용 | patch |
|------|------|------|-------|
| ab58a47 | 문서 | 속도 최적화 체크리스트 최초 작성 | — |
| 840425a | **항목 2-1** | shift_mem 순열 사전 계산 (ldpc_revised/decoder.{h,cpp}) + reference 문서 체계 도입 | [patches/2-1.patch](patches/2-1.patch) |
| 961c623 | 문서 | 전달 패키지 구조 구성 (checklist 이동, patches/, 이식 앵커) | — |
| f1c7e92 | 문서 | 커밋 인덱스(commits.md) 추가 | — |
| eefb0fa | **항목 2-2** | iteration 판정 루프 불변 hoisting — 프로브 방식 (C2V_Cal/V2C_Store) | [patches/2-2.patch](patches/2-2.patch) |
| 36ef51d | **항목 2-3** | 1bit-precision 판정 hoisting (C2V/V2C/VN_Cal_HD/HD_HCU) | [patches/2-3.patch](patches/2-3.patch) |
| 2f47032 | **항목 2-4** | stopping_criteria 판정 hoisting (VN_Cal 5종) | [patches/2-4.patch](patches/2-4.patch) |
| e4866ca | **항목 2-5** | V2C_Store before_BS dead code 제거 | [patches/2-5.patch](patches/2-5.patch) |
| 646d70a | **항목 2-6** | _nq 배열 체인 TV 가드 | [patches/2-6.patch](patches/2-6.patch) |
| d499b1f | **항목 2-7** | pre_exist_sgn_reg_BS 3종 TV 가드 | [patches/2-7.patch](patches/2-7.patch) |
| f9d4c8d | **항목 2-8** | Delay_2clk 행 단위 memcpy화 | [patches/2-8.patch](patches/2-8.patch) |
| 50e55d5 | **항목 2-9** | LLR 테이블 파일 파라미터화 (llr_tables.txt) | [patches/2-9.patch](patches/2-9.patch) |
| aa06935 | **항목 2-10** | Init_Log_Data 프레임당 호출 가드 | [patches/2-10.patch](patches/2-10.patch) |
| b4d7f3d | **항목 2-11** | magnitude 도메인 변환 산술화 | [patches/2-11.patch](patches/2-11.patch) |
| 7253778 | **항목 2-12** | 핫패스 % 2 → & 1 / ^ 1 치환 | [patches/2-12.patch](patches/2-12.patch) |
| cc39acd | **항목 2-13** | VN_Cal Mux_idx 로컬 캐시 | [patches/2-13.patch](patches/2-13.patch) |
| 69339be | **항목 2-14** | bit_pos 영역 분류 테이블화 | [patches/2-14.patch](patches/2-14.patch) |
| dad14dd | **항목 2-15** | Clear 계열 memset화 | [patches/2-15.patch](patches/2-15.patch) |
| a78c32a | **항목 2-16** | Clear_REG_min_value 무의미 분기 제거 | [patches/2-16.patch](patches/2-16.patch) |
| 21d7628 | **항목 2-17** | VN_Cal_Pre cwc 분기 축소 | [patches/2-17.patch](patches/2-17.patch) |
| 593306e | **항목 2-18** | Check_REG 평탄화 (+TV 뷰 어댑터) | [patches/2-18.patch](patches/2-18.patch) |
| 2078c08 | **항목 2-19** | VNU_out3_temp 복사 + no-op PMU 스킵 (2-20은 제외 결정) | [patches/2-19.patch](patches/2-19.patch) |
| 07cc553 | **항목 3-1** | partial_crc_HW_T4 스택 배열화 | [patches/3-1.patch](patches/3-1.patch) |
| 363e5d5 | **항목 3-2** | full CRC 버퍼 재사용 | [patches/3-2.patch](patches/3-2.patch) |
| 6be349d | **항목 3-3** | 인코더 PCM 전처리 Init 이동 | [patches/3-3.patch](patches/3-3.patch) |
| c4c2e7c | **항목 3-4** | 인코더 P 행렬 사전 계산 | [patches/3-4.patch](patches/3-4.patch) |
| 0e27fc3 | **항목 3-5** | 인코더 % 2 → XOR/AND | [patches/3-5.patch](patches/3-5.patch) |
| f7a1a7b | **항목 3-6** | xor_r25 시프트 memmove화 | [patches/3-6.patch](patches/3-6.patch) |
| 96bfe4a | **항목 3-7** | rand_sel_ep swap 역복원 | [patches/3-7.patch](patches/3-7.patch) |
| 2e2adef | **항목 3-11** | Print_Seed 파일 핸들 유지 | [patches/3-11.patch](patches/3-11.patch) |
| 044b89d | **항목 3-8** | 프레임 루프 5-버퍼 memcpy화 | [patches/3-8.patch](patches/3-8.patch) |
| 83ab668 | **항목 3-9** | SD 양자화 모드 분기 hoisting | [patches/3-9.patch](patches/3-9.patch) |
| 6302bde | **항목 3-10** | 에러 주입 flip ^= 1 | [patches/3-10.patch](patches/3-10.patch) |
| 0946f3b | **항목 3-12~14** | rber_dist 핸들 / 임시버퍼 재사용 / invert·copy 정리 | [patches/3-12_14.patch](patches/3-12_14.patch) |
| 71f9497 | 문서 | speed_opt Phase 2·3 완료 기록 (commits.md/TODO 갱신) | — |
| 9b1b109 | 문서 | 체크리스트 정리 반영 + 5-1 질문 답변 (슈퍼컴/MPI 관계) | — |
| 24dc5ef | **항목 4-3** | CN 상태 struct 묶음 (5배열 → CN_STATE[M]) + Print_TV_Cycle_Based 가드(2-18 회귀 해소) | [patches/4-3.patch](patches/4-3.patch) |
| a45320b | **항목 4-4** | 0/1 배열 int8_t 축소 (Check_SRAM_sgn/Variable_mem/cwc) | [patches/4-4.patch](patches/4-4.patch) |
| dc0fb6a | 문서 | speed_opt Phase 4 완료 기록 (commits.md/TODO 갱신) | — |
| 96509fe | **항목 5-6** | xor_r25 double 왕복 제거 (2^32 전수 검증 통과 → bit-exact) | [patches/5-6.patch](patches/5-6.patch) |
| ef4238e | **항목 6-1/6-2** | PMU_Read·DU_Manager 범위 밖 접근 해소 | [patches/6-1_6-2.patch](patches/6-1_6-2.patch) |
