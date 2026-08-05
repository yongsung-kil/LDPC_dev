# DONE — 완료 이력 (2_LDPC_light)

### 2026-08-05 — 실행 흐름을 JSON 설정 기반 4단계 구조로 재편
사용자 지시로 실행 흐름을 파라미터/코드 분리 + 함수 분리 구조로 변경
- **배경**: 기존 `examples/fer_curve.py`는 파라미터가 코드에 하드코딩되어 있었고, BSC/AWGN 스윕이 `sim.sweep()`에 고정되어 있었으며, H-matrix 생성(`tools/gen_example_code.py`)이 실행 흐름에 자동으로 섞여 있었음
- **변경**:
  - ㉮ `run.py` 신설 — `load_config`(JSON 읽기) → `setup`(PCM 로드/디코더 구성) → `run_experiment`(msg 생성 → encode → channel → decode 반복) → `report`(요약+CSV) 4단계 함수로 분리. `config["channels"]` 리스트로 채널 1개/여러 개, 포인트 1개/여러 개를 동일한 경로로 처리 (`sweep` 개념/이름 제거)
  - ㉯ `encoder.py` 신설 — `generate_message()`(실장, K bit 무작위 생성)와 `encode()`(스텁, all-zero 반환) 추가. 채점 결과는 기존과 동일(all-zero)하지만 실물 인코더 반입 시 `encode()`만 교체하면 되는 구조 마련
  - ㉰ `channel.py`의 `bsc_llr`/`awgn_llr`이 codeword(cw)를 인자로 받도록 변경 — `encoder.encode()` 출력을 실제로 흘려받음. 호출부(`mpi_runner.py`, `examples/select_irregular.py`)는 all-zero cw를 명시적으로 넘기도록 최소 보정만 함 (두 파일은 이번 재편 대상에서 제외, 기존 CLI 구조 유지)
  - ㉱ `examples/fer_curve.py`는 `run.py` 위에서 그래프 출력만 담당하도록 축소, 파라미터는 `examples/fer_curve.json`으로 분리. H-matrix 자동 생성 폴백 제거(생성은 `tools/gen_example_code.py` 수동 실행으로 분리)
  - ㉲ `sim.py`의 `sweep()`은 미사용이 되어 삭제, `run_fer_point`/`save_csv`는 유지 (run.py가 재사용)
- **검증**: `run.py`/`fer_curve.py` 실제 실행으로 단일 포인트·다중 포인트·BSC·AWGN 조합 스모크 테스트 확인 (FER 값이 기존 채널 공식과 동일하게 나옴을 확인)
- **파일**: `run.py`(신설), `encoder.py`(신설), `channel.py`, `sim.py`, `examples/fer_curve.py`, `examples/fer_curve.json`(신설), `mpi_runner.py`, `examples/select_irregular.py`, `__init__.py`, `README.md`, `docs/plan.md`(§3.1, §7 #6)

### 2026-08-03 — column_wise 스케줄 구현 + 3-bit internal precision 튜닝 2, 3차
사용자 정정 반영 (원본은 column-wise, phase만 제거)
- **핵심 발견**:
  - ㉮ 낮은 dv의 ch가 메시지 최대(7) 이상이면 trapping (ch[6,6,8,8]로 해소)
  - ㉯ th842는 300비트 클린(FER 1e-2)에 340 절벽, th952는 380비트까지 버티나 약 7% 잔여 floor
  - ㉰ BF 1-bit 구간은 vanilla에서 무효과. 6-bit 기준선(column_wise)은 380비트 0/512
- **한계**: 3-bit 잔여 갭은 소실된 HW TH/CH 실값 없이는 추정 튜닝 한계. 실값 반입 시 재검증

### 2026-07-30 — 뼈대 구현 + 예시 부호 + 측정 (max_iter=120 확정)
- **구현**: pcm/channel/decoder(offset min-sum, old/new 2세트, genie 판정과 마스킹)/sim/mpi_runner(로컬 fallback만 검증)
- **예시 부호**: PEG+greedy lifting(4-cycle 0)+dual-diagonal, 18×147 z=256 rate 0.878. irregular 17×144 후보 6개 생성, 선별 승자 seed 103
- **측정**: regular 커브 FER 1e-3 교차 BSC RBER 0.90%, AWGN 3.55dB. fixed-error 스윕 정정 한계 약 380~400비트 (RBER 1.03~1.09%). 1000 frames @120iter: 60~133초/코어
- **결정 사항**: genie 판정 / all-zero / Dual-Update off / numba 안 함. C++ vanilla 파생본은 만들지 않음, 최종 검증은 실물 C++ 이식으로
- **계획 리뷰**: 라이트 리뷰 완료 (실물 base는 18×147, LLR 도메인은 flip/magnitude, CN_STATE 5필드+Check_SRAM_sgn, 외부 자산 3종 필요). 기록: `docs/review/`
