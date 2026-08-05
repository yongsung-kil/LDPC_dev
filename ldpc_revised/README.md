# ldpc_revised — 속도 최적화 항목별 수정 검토용

> 원본: `LDPC_Original/`. 이 폴더에는 **수정된 파일만** 복사해 둔다 (전체 복사 아님).
> 체크리스트: `docs/speed_opt/checklist.md` — **한 번에 한 항목** 수정 → 사용자 검토 → 다음 항목.
> 항목별 상세(왜/어떻게/주의/검토 상태)는 `docs/speed_opt/{ID}_*.md` reference 문서 참조.
> 이 환경에서는 빌드/실행하지 않는다. 원본과 diff 하면 해당 항목까지의 변경만 보인다.

## 적용 이력

| ID | 항목 | 파일 | 상태 | 상세 |
|----|------|------|------|------|
| 2-1 | shift_mem 순열 사전 계산 | decoder.h, decoder.cpp | 검토 완료 | [docs/speed_opt/2-1_shift_mem.md](docs/speed_opt/2-1_shift_mem.md) |
| 2-2 | iteration 판정 루프 불변 hoisting | decoder.cpp | 검토 완료 | [docs/speed_opt/2-2_iter_invariant_hoist.md](docs/speed_opt/2-2_iter_invariant_hoist.md) |
| 2-3 | 1bit-precision 판정 hoisting | decoder.cpp | 검토 완료 | [docs/speed_opt/2-3_1bit_precision_hoist.md](docs/speed_opt/2-3_1bit_precision_hoist.md) |
| 2-4 | stopping_criteria 판정 hoisting | decoder.cpp | 적용 완료 | [docs/speed_opt/2-4_stopping_criteria_hoist.md](docs/speed_opt/2-4_stopping_criteria_hoist.md) |
| 2-5 | before_BS dead code 제거 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-5_before_BS_dead_code.md](docs/speed_opt/2-5_before_BS_dead_code.md) |
| 2-6 | _nq 배열 체인 TV 가드 | decoder.h, decoder.cpp | 적용 완료 | [docs/speed_opt/2-6_nq_arrays_tv_guard.md](docs/speed_opt/2-6_nq_arrays_tv_guard.md) |
| 2-7 | pre_exist_sgn_reg_BS 3종 TV 가드 | decoder.h, decoder.cpp | 적용 완료 | [docs/speed_opt/2-7_sgn_reg_BS_tv_guard.md](docs/speed_opt/2-7_sgn_reg_BS_tv_guard.md) |
| 2-8 | Delay_2clk 행 단위 memcpy | decoder.cpp | 적용 완료 | [docs/speed_opt/2-8_delay_2clk_memcpy.md](docs/speed_opt/2-8_delay_2clk_memcpy.md) |
| 2-9 | LLR 테이블 파일 파라미터화 | decoder.h, decoder.cpp, llr_tables_template.txt | 적용 완료 | [docs/speed_opt/2-9_llr_table_parameterize.md](docs/speed_opt/2-9_llr_table_parameterize.md) |
| 2-10 | Init_Log_Data 프레임당 호출 가드 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-10_init_log_data_guard.md](docs/speed_opt/2-10_init_log_data_guard.md) |
| 2-11 | magnitude 매핑 산술화 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-11_mag_domain_arith.md](docs/speed_opt/2-11_mag_domain_arith.md) |
| 2-12 | % 2 → & 1 / ^ 1 치환 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-12_mod2_to_bitand.md](docs/speed_opt/2-12_mod2_to_bitand.md) |
| 2-13 | VN_Cal Mux_idx 로컬 캐시 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-13_mux_idx_cache.md](docs/speed_opt/2-13_mux_idx_cache.md) |
| 2-14 | bit_region 분류 테이블화 | decoder.h, decoder.cpp | 적용 완료 | [docs/speed_opt/2-14_bit_region_table.md](docs/speed_opt/2-14_bit_region_table.md) |
| 2-15 | Clear 계열 memset화 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-15_clear_memset.md](docs/speed_opt/2-15_clear_memset.md) |
| 2-16 | Clear_REG_min_value 분기 제거 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-16_clear_reg_min_branch.md](docs/speed_opt/2-16_clear_reg_min_branch.md) |
| 2-17 | VN_Cal_Pre cwc 분기 축소 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-17_vn_cal_pre_cwc.md](docs/speed_opt/2-17_vn_cal_pre_cwc.md) |
| 2-18 | Check_REG 평탄화 | decoder.h, decoder.cpp | 적용 완료 | [docs/speed_opt/2-18_check_reg_flatten.md](docs/speed_opt/2-18_check_reg_flatten.md) |
| 2-19 | VNU_out3_temp/PMU no-op 스킵 | decoder.cpp | 적용 완료 | [docs/speed_opt/2-19_pmu_noop_skip.md](docs/speed_opt/2-19_pmu_noop_skip.md) |
| 2-20 | (제외) 마지막-edge 검사 이동 | — | 제외 | 효과/위험 비 불충족 — checklist 참조 |
| 3-1 | partial_crc_HW_T4 스택 배열화 | partial_CRC.cpp | 적용 완료 | [docs/speed_opt/3-1_partial_crc_stack.md](docs/speed_opt/3-1_partial_crc_stack.md) |
| 3-2 | full CRC 버퍼 재사용 | full_CRC.cpp | 적용 완료 | [docs/speed_opt/3-2_full_crc_buffer_reuse.md](docs/speed_opt/3-2_full_crc_buffer_reuse.md) |
| 3-3 | 인코더 PCM 전처리 Init 이동 | encoder.cpp | 적용 완료 | [docs/speed_opt/3-3_encoder_pcm_init.md](docs/speed_opt/3-3_encoder_pcm_init.md) |
| 3-4 | 인코더 P 행렬 사전 계산 | encoder.h, encoder.cpp | 적용 완료 | [docs/speed_opt/3-4_encoder_p_precompute.md](docs/speed_opt/3-4_encoder_p_precompute.md) |
| 3-5 | 인코더 % 2 → XOR/AND | encoder.cpp | 적용 완료 | [docs/speed_opt/3-5_encoder_xor.md](docs/speed_opt/3-5_encoder_xor.md) |
| 3-6 | xor_r25 시프트 memmove화 | random.cpp | 적용 완료 | [docs/speed_opt/3-6_xor25_memmove.md](docs/speed_opt/3-6_xor25_memmove.md) |
| 3-7 | rand_sel_ep swap 역복원 | random.cpp | 적용 완료 | [docs/speed_opt/3-7_rand_sel_ep_restore.md](docs/speed_opt/3-7_rand_sel_ep_restore.md) |
| 3-11 | Print_Seed 파일 핸들 유지 | random.cpp | 적용 완료 | [docs/speed_opt/3-11_print_seed_handle.md](docs/speed_opt/3-11_print_seed_handle.md) |
| 3-8 | 프레임 루프 5-버퍼 memcpy화 | ecc_top.cpp | 적용 완료 | [docs/speed_opt/3-8_frame_copy_memcpy.md](docs/speed_opt/3-8_frame_copy_memcpy.md) |
| 3-9 | SD 양자화 모드 분기 hoisting | ecc_top.cpp | 적용 완료 | [docs/speed_opt/3-9_quantize_mode_hoist.md](docs/speed_opt/3-9_quantize_mode_hoist.md) |
| 3-10 | 에러 주입 flip ^= 1 | ecc_top.cpp | 적용 완료 | [docs/speed_opt/3-10_error_flip_xor.md](docs/speed_opt/3-10_error_flip_xor.md) |
| 3-12~14 | rber_dist 핸들/임시버퍼 재사용/invert 정리 | ecc_top.cpp | 적용 완료 | [docs/speed_opt/3-12_14_ecc_top_misc.md](docs/speed_opt/3-12_14_ecc_top_misc.md) |
| 4-3 | CN 상태 struct 묶음 (5배열 → CN_STATE[M]) | decoder.h, decoder.cpp | 적용 완료 | [docs/speed_opt/4-3_cn_state_struct.md](docs/speed_opt/4-3_cn_state_struct.md) |
| 4-4 | 0/1 배열 int → int8_t 축소 (Check_SRAM_sgn/Variable_mem/cwc) | decoder.h, decoder.cpp | 적용 완료 | [docs/speed_opt/4-4_int8_narrowing.md](docs/speed_opt/4-4_int8_narrowing.md) |
| 5-6 | xor_r25 double 왕복 제거 (2^32 전수 검증 통과) | random.h, random.cpp, ecc_top.cpp | 적용 완료 | [docs/speed_opt/5-6_xor25_no_double.md](docs/speed_opt/5-6_xor25_no_double.md) |
| 6-1 | PMU_Read/PMU_Read_HCU OOB 읽기·쓰기 수정 (factor 반영) | decoder.cpp | 적용 완료 | [docs/speed_opt/6-1_6-2_oob_fixes.md](docs/speed_opt/6-1_6-2_oob_fixes.md) |
| 6-2 | DU_Manager 범위 검사 순서 수정 (OOB 해소) | decoder.cpp | 적용 완료 | [docs/speed_opt/6-1_6-2_oob_fixes.md](docs/speed_opt/6-1_6-2_oob_fixes.md) |
