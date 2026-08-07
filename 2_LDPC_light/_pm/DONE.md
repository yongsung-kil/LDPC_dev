# DONE — 완료 이력 (2_LDPC_light)

### 2026-08-07 — decoder 진입 함수 개명 + 단계별 함수 추출
사용자 확정: 진입 함수 decode_batch → decoder_main. 본문을 단계별 함수로 추출
(함수 추출 = 긴 함수 본문을 의미 단위의 작은 함수로 나누는 리팩토링 기법)
- **변경**: decoder_main()은 흐름만 남기고(약 10줄) 단계를 분리 —
  _read_channel_input(채널 해석) / _init_state(상태 초기화) /
  _run_iteration(한 iteration) / _process_column(한 column) /
  _record_iteration(로그·최종 상태) / _apply_genie(판정·배치 압축) / _build_result(반환 조립).
  상태 배열은 _DecodeState 묶음 객체로 전달 (필드 목록을 클래스에 주석으로 명시)
- **불변**: 교체 지점 7개 시그니처 그대로 (아이디어 코드 영향 없음)
- **검증**: 고정 입력 회귀 배열 단위 완전 일치, 루트·vanilla config end-to-end 정상
- **파일**: `LDPC_base/decoder.py`, `sim.py`(호출부), `Ideas/vanilla/README.md` — `_test/` 아래

### 2026-08-07 — 논문 아이디어 교체 지점 구조 + Ideas/ 뼈대 (vanilla reference 포함)
아이디어 적용 구조 사용자 확정: 교체 단위 = 원본 C++ 함수 경계, 아이디어는 자식 클래스.
(교체 지점 = 본체가 단계를 별도 함수로 분리해 둬 그 함수만 갈아끼울 수 있는 자리, 업계 용어 hook)
- **배경**: 논문 아이디어를 하나씩 적용할 때의 모듈화 수준 논의 — 전 파일 복사(전파 불가)와
  decoder 통짜 교체(중복) 대신, C++ 함수 단위 교체 지점 + 아이디어별 자식 클래스로 확정.
  vanilla(원본 대응 정본)도 Ideas의 한 항목으로 두어 reference 실험까지 같은 틀로 통일 (사용자 제안)
- **변경**:
  - ㉮ decoder.py 교체용 함수 분리 — _c2v_reconstruct(C2V_Cal), _vn_decide(VN_Cal_HD 판정),
    _vnu_quantize(기존), _cnu_update(CNU_*), _column_order(스케줄), _restart_policy(Clear_Edge_Restart).
    교체용 함수 표를 모듈 docstring에 기록
  - ㉯ Ideas/ 신설 — registry.py(이름→클래스 경로) + vanilla/(재정의 없는 reference
    서브클래스, config, README에 새 아이디어 추가 절차). 아이디어 결과는 각 폴더 Sim_Output/에
  - ㉰ run.py decoder.type 연결 — config로 디코더 선택 (기본 vanilla, Ideas 없는 환경은
    vanilla만 정본으로 동작)
- **검증**: 교체용 함수 분리 후 고정 입력 회귀 배열 단위 완전 일치. vanilla config와 루트 config
  end-to-end 실행 확인. 데모 자식 클래스(_c2v_reconstruct에 offset)로 재정의 실효 확인
- **파일**: `LDPC_base/decoder.py`, `run.py`, `Ideas/`(신설), `README.md` — `_test/` 아래 (git 미추적)

### 2026-08-07 — LDPC_base 가독성 리팩토링 + JSON 개편 2차 + 실행 폴더·분석 로그
대기 중이던 3개 작업을 사용자 착수 승인 후 일괄 수행 (`_test/` 개정본 대상)
- **배경**: 외부 LDPC 동작 확인 완료로 착수 조건 해제. 미결정 3건 사용자 확정
  (㉮ 메시지 변수명 VNU_in/VNU_out ㉯ legacy 경로 삭제 ㉰ 로그는 핵심 세트 먼저)
- **변경**:
  - ㉮ 가독성 리팩토링 — legacy 경로(two_set 스케줄, 비-matrix signed LLR 경로) 삭제로
    decoder를 syndrome-aided 단일 경로로 축소. 변수명을 원본 C++ 용어와 정합
    (sum_t, vnu_in/vnu_out, check_sum, edge_sgn, syndrome, min1_pos, prev_csw,
    table_row_idx 등). llr_matrix.py/channel.py의 축약 변수도 풀어 씀
  - ㉯ JSON 개편 2차 — `H_matrix`/`decoder.llr_matrix`를 `{"dir","file"}` 분리,
    seed를 최상위 하나로 단일화(기본 0, [seed, 채널 인덱스, 포인트]로 스트림 파생),
    `batch`→`frames_per_batch`, `_desc` 설명 키 규칙 적용 (config.json에 실제 반영)
  - ㉰ 실행 폴더 — 실행마다 `Sim_Output/YYMMDD_HHMMSS_{라벨}/` 생성, config 사본과
    summary.txt(git 커밋 해시 포함) 저장
  - ㉱ 분석 로그 핵심 세트 — csw_per_iter, bit_err_per_iter, bit_err_by_dv(실값 dv 라벨),
    iter_histogram, fail_frame_detail + post_fec_ber(FER CSV 상시 열),
    fer_vs_iter("max_iter를 k로 줄였다면"의 FER), fer_curve_png.
    후순위 로그 7종은 TODO 잔류
- **검증**: 리팩토링 전후 고정 입력(2개 매트릭스 × 2채널 × 16프레임) decode 결과
  배열 단위 완전 일치. end-to-end 실행으로 실행 폴더/로그 CSV/그림 생성 확인
  (dv별 로그가 토이 매트릭스의 dv2 고착을 그대로 드러내는 것 확인)
- **파일**: `LDPC_base/decoder.py`(재작성), `run.py`(재작성), `sim.py`(재작성),
  `channel.py`, `llr_matrix.py`, `config.json`, `README.md` — 전부 `_test/` 아래 (git 미추적)

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
