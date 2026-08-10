# DONE — 완료 이력 (2_LDPC_light)

### 2026-08-10 — 루트 config.json 삭제 (config 골자는 workspace/_template로 단일화)
루트와 template의 config 이중화를 해소 (사용자 결정 2026-08-10)
- **배경**: 루트 config는 스키마 예시 겸 빠른 실행용이었는데, 스키마 설명은 README가
  담당하고 실행 표준은 workspace라 역할이 겹쳤다. 스키마 변경 때마다 config 여러 벌을
  고치는 비용과 어긋남 위험 제거
- **변경**: config.json 삭제, README 구성 표에서 config.json과 Sim_Output 행 제거,
  실행 방법을 workspace 중심으로 정리 (python -m은 config 경로 지정 방식으로 안내).
  루트 config에 있던 인라인 설명(_desc 전체)은 template config에 복원 (사용자 지시)
- **검증**: `python -m LDPC_base.run workspace/vanilla/config.json` 정상 실행,
  복원한 template config의 load_config 검증 통과
- **파일**: config.json(삭제), README.md, LDPC_base/run.py(docstring)

### 2026-08-10 — log 섹션 상위 스위치 (log.enabled) 추가
로그 전체를 한 키로 on/off (사용자 지시 2026-08-10)
- **배경**: 하위 항목 7개를 일일이 끄지 않고 로그 수집 여부를 먼저 정하는 상위 스위치 필요
- **변경**: config `log.enabled` (기본 true). false면 하위 항목이 true여도 전부 끈 것으로
  취급 (load_config에서 정규화하므로 소비 코드는 무변경). config 3벌과 README 스키마 반영
- **검증**: enabled=false 실행에서 log CSV와 png 미생성 (필수 산출물 4종만),
  enabled=true는 기존과 동일 (log_iter CSV가 기준 실행과 일치)
- **파일**: LDPC_base/run.py, config.json, workspace/vanilla/config.json,
  workspace/_template/config.json, README.md

### 2026-08-10 — workspace 전환 (Ideas 개명, registry 폐지, 실험 폴더 run.py 진입점)
실험 공간을 workspace/로 통일하고 실험 폴더 단독 실행을 제공
- **배경**: 실험을 폴더 단위로 자유롭게 만들고 그 안의 run.py만 실행하면 되게 하라는
  사용자 결정 (2026-08-10). registry는 진입점이 config(JSON) 하나이던 시절의
  이름 변환표라 코드(run.py) 진입점에서는 불필요
- **변경**:
  - ㉮ Ideas/를 workspace/로 개명 (git mv), registry.py와 __init__.py 2개 삭제
  - ㉯ LDPC_base/run.py: main/setup에 decoder_class 주입 (None이면 BaseDecoder),
    decoder.type 키와 registry 조회 삭제, 요약에 디코더 클래스 이름 출력
  - ㉰ 상위 탐색 런처 run.py (vanilla와 _template, 복사 후 수정 없이 동작),
    workspace/README.md와 _template/(config, README 골자) 신설
  - ㉱ 문서: 새논문적용규칙.md 절차를 run.py 스위치 기준으로 재작성, README 구조/실행/
    스키마 절 갱신, "아이디어 스크리닝은 2_에서" 류 문구 제거 (3_LDPC_ideas와
    역할 혼동 방지, 사용자 지시)
- **검증**: vanilla 재실행이 기존 실행(260808_132800)과 수치 완전 동일 (로그 CSV 6종
  일치, 차이는 경과시간 열뿐), 변형 디코더 주입 실증, python -m 경로 회귀 확인
- **파일**: workspace/ (구 Ideas/), LDPC_base/run.py, README.md, __init__.py,
  docs/새논문적용규칙.md, ../3_LDPC_ideas/README.md, ../CLAUDE.md

### 2026-08-09 — 2SD/3SD 디코딩 구현 (toy 파일 + 균일 생성 지원)
HD 전용이던 디코더를 2SD/3SD까지 확장. C++ 원본 정적 분석(파일:라인 근거)으로 설계를 확정했다
- **배경**: 채널(rber 2SD/3SD, strong_error)과 로더는 준비되어 있었고 디코더 산술만 막혀
  있었다. 사용자 확정: toy LLR_MATRIX로 개발 후 실물 교체, 균일 생성도 2SD/3SD 지원
- **변경**:
  - ㉮ region 매핑 (2SD `1-sd`, 3SD `2(1-sd)+(cc XOR sd)`, ch 열 0..3 = 신뢰 내림차순)과
    비트별 채널 항 선택. VN 판정과 양자화와 CSW와 row 선택은 HD와 같은 경로임을 확정
  - ㉯ SD Edge Clear 규칙 (restart만 클리어)과 Pre 단계 (iteration 0과 SD restart에서
    채널 magnitude를 min1/min2에 시딩, check_sum과 edge sign은 0, restart 판정은
    read bit로 복귀). 시딩 magnitude는 3-bit 파일 [5,1]/[7,5,3,1] 고정, 균일 n-bit는
    1..top 균등 분할
  - ㉰ 균일 생성의 channel_llr를 region별 리스트로 확장 (2SD 2개, 3SD 4개, 강한 쪽부터),
    생성 파일명에 ch10-3 형식 반영
  - ㉱ toy 파일 2종 (`LLR_MATRIX_2SD_toy0.txt`, `LLR_MATRIX_3SD_toy0.txt`, restart 포함,
    반전 가능 조건 ch <= 7·dv 준수)
- **검증**: HD 회귀 2종 산출물 완전 일치, region 매핑 전 조합, restart의 Pre 재실행 실증
  (iteration 11 에러 수 = 채널 에러 수), e2e 4종 완주 (rber 2SD/3SD FER 0, strong_error,
  균일 2SD). 상세: `done/20260809_2SD3SD구현/`
- **파일**: `LDPC_base/decoder.py`, `LDPC_base/llr_matrix.py`, `LDPC_base/run.py`,
  `Input/LLR/LLR_MATRIX_{2SD,3SD}_toy0.txt`, `config.json`, `README.md`, `docs/차이.md`

### 2026-08-08 — 균일 n-bit 양자화 모드 (매트릭스 파일 생성 후 로드)
사용자 확정 설계: LLR matrix 파일이 없으면 균일 양자화 매트릭스를 **DAO 포맷 파일로
생성해 저장한 뒤 그 파일을 로드** — 디코더는 파일 로드 단일 경로만 탄다
- **변경**:
  - ㉮ `LLRMatrix.make_internal_uniform_matrix(num_bits, channel_llr, max_iter, dv_max, mode)`
    — 정수 th [최대 레벨..1], 레벨 [최대..0], 전 dv 공통 ch, 그룹 1개 구성 합성.
    flip 도메인 값이 전부 정수라 캐스케이드가 상한 클리핑과 정확히 같음
  - ㉯ `LLRMatrix.save(path)` — DAO 포맷 저장 (정수만 기록, load와 round-trip 일치).
    생성 파일명 `LLR_MATRIX_{mode}_uniform_...` — uniform은 사람이 만든 파일이
    아니라는 표시이며, load()가 이 표시로 균일 레벨(edge_mag [th 개수..0])을 잡는다
  - ㉰ LLRMatrix가 edge_mag(VNU 출력 레벨)를 보유 — 사람이 만든 파일은 3-bit
    {7,5,3,1}, uniform 파일은 [최대..0]. decoder `_vnu_quantize` 캐스케이드를
    th 개수 임의로 일반화
  - ㉱ JSON: `decoder.use_input_llr_matrix`(기본 true)로 토글,
    `decoder.internal_quantize` {num_bits, channel_llr, max_iter, mode}.
    생성 위치는 llr_matrix.dir(없으면 Input/LLR)
  - ㉲ 디코더 생성자는 HD/2SD/3SD를 받되(사용자 수정 반영, "3SD]" 오타 수리)
    산술은 HD 전용이라 decoder_main에서 2SD/3SD 명시적 에러 (조용한 오답 방지)
- **검증**: 파일 경로 고정 입력 회귀 배열 단위 완전 일치 (캐스케이드 일반화 후에도 불변).
  합성↔저장 후 로드 round-trip에서 디코딩 결과 배열 단위 동일.
  6-bit uniform: fixed-error 300비트 256프레임 전량 정정(FER 0, 평균 7.6 iteration),
  정정 한계 380~420비트 사이 — 구 6-bit 기준선과 부합. internal_quantize 누락 시
  명시적 에러 확인
- **파일**: `LDPC_base/llr_matrix.py`, `decoder.py`, `run.py`, `config.json`, `README.md`

### 2026-08-08 — 의견1 반영 (이름 명확화 2차 + 실험 요약 출력 + 문장 작성 규칙)
사용자 리뷰 노트(의견1.md, `done/20260808_의견1_반영/` 보존)의 전 항목 반영
- **이름 변경** (LDPC_base 전반):
  - ㉮ run.py — decoder_cls→decoder_class, mx→llr_matrix, dec→decoder, ch→channel_config,
    p→point, r→point_result, points→point_results, rng→random_generator,
    verbose→print_progress (JSON 키 run.print_progress), dec_type→decoder_type,
    sbf→stop_below_fer. _make_channel_fn 결과는 channel_fn 변수로 받아서 전달
  - ㉯ sim.py — b→batch, res→decode_result, unknown→unknown_log_items,
    agg_*→total_*(iteration별 합계), n_it→num_iterations_run,
    fail_rows→fail_frame_details, 결과 키 log_agg→iteration_totals
    (하위 키 active_frames/csw_sum/bit_err_sum/bit_err_by_dv_sum)
  - ㉰ decoder.py — s→state, n_active→num_active_frames, frozenset→set(용어 제거)
  - ㉱ channel/encoder — rng→random_generator
- **실험 요약 출력**: setup 직후와 summary.txt 상단에 부호 정보, LLR matrix 정보,
  디코더 정보(type, class, max_iter), 읽은 config 정보(seed, 채널·포인트, run 설정,
  켜진 로그)를 출력 (`_experiment_summary_lines`)
- **문장 작성 규칙 등록** (루트 CLAUDE.md): ㉮ 수리는 덧대기가 아니라 다시 쓰기
  (이력 서술은 코드·문서에 남기지 않음 — DONE.md와 git이 담당) ㉯ 규칙은 긍정문
  ㉰ 이름·용어는 명확성 우선. 기존 LDPC_base docstring의 이력 서술도 정리
- **검증**: 고정 입력 회귀 배열 단위 완전 일치, 루트·vanilla config end-to-end 정상
- **파일**: `LDPC_base/` 전 파일, 루트 `CLAUDE.md`

### 2026-08-07 — 개정본 본체 반영 (구 코드 삭제 + `_test` 산출물 이동)
사용자 확정: `_test` 개정본을 본체로 이동, 구 코드는 삭제 (git 이력으로 복구 가능)
- **변경**:
  - ㉮ 구 본체 삭제 — channel, decoder, encoder, pcm, run, sim, mpi_runner(재설계 예정), examples
  - ㉯ 개정본 이동 — LDPC_base/, Ideas/, Input/, Sim_Output/, config.json을 `2_LDPC_light/`
    바로 아래로 (sandbox 구조 그대로라 import·registry 무수정 동작). 차이.md는 docs/로
  - ㉰ `.gitignore` — `H_Matrix/`를 `0_LDPC_original/` 한정으로 축소 (Input/H_matrix 추적
    가능해짐), `Sim_Output/` 무시 추가
  - ㉱ tools/H_mat_gen import 보정 (`...pcm` → `...LDPC_base.pcm`), select_irregular는
    실행 불가 상태 명시 (손질 TODO 잔류)
  - ㉲ README 전면 갱신 (본체 정본), plan.md에 구조 개편 안내, sandbox에는 이동 안내만 남김
- **검증**: `python -m LDPC_base.run config.json`, vanilla config, H_mat_gen 생성까지
  새 위치에서 전부 정상 실행
- **파일**: `2_LDPC_light/` 전반, `.gitignore` — 이번 반영으로 개정본이 git 추적 시작

### 2026-08-07 — LDPC_base 개정본 딥 리뷰 + 후속 수정 (완료 처리는 TODO 점검에서)
Round 1→2→3 딥 리뷰 후 사용자 확정 회신대로 후속 수정, 자동 검증 51건 통과
- **배경**: `_test/20260806_setup_구성_실험/LDPC_base/` 개정본(2026-08-06 시점)의 정합성 검증
- **변경** (후속 수정): 키맵+필수값+config checker, strong_error 2단계 추출,
  F8 캐스케이드 교체, F11 LLR matrix 제약 정리(겹침 거부·restart 제약 유지, DAO 규칙 정본),
  F14 주석·문서화, llr_profile 제거(llr_tables.py 삭제), 채널 리스트 복원
- **Decision 해소**: ㉮ llr_profile 제거 ㉯ 채널 설정 리스트 복원 ㉰ dv는 H-matrix 기준,
  LLR_MATRIX 미커버 시 에러 ㉱ .gitignore는 본체 반영 시 조치로 이관
- **검증**: 자동 검증 51건 통과 + 라이트 재리뷰(r4) 수리 4건 반영
- **잔여 이관**: config checker 키별 허용값 확장(TODO 별도 항목),
  legacy 경로 존폐는 가독성 리팩토링에서 삭제로 해소
- **기록**: `done/20260806_review/`, `done/20260807_리뷰후속수정/`

### 2026-08-07 — 이름 정확성 일괄 수정 (수단이 아닌 목적이 이름)
사용자 지적: `_apply_genie`는 수단(genie)이 이름 — error check가 목적이므로 이름이어야 함.
같은 기준으로 전수 감사 후 일괄 수정. **원칙 확정: 이름은 길어져도 명확한 것이 우선**
- **변경**:
  - ㉮ `_apply_genie` → `_check_errors` (에러 검사가 목적, genie는 수단)
  - ㉯ `n_iter` → `decode_success_iteration` (프레임별 "디코딩이 성공한 iteration 번호",
    실패 프레임은 0 — "iteration 수"로 오독되던 이름)
  - ㉰ `avg_iter_ok`/`avg_iter_success` → `avg_decode_success_iteration`
    (성공 프레임들의 성공까지 평균 iteration 수. CSV 열 이름 포함)
  - ㉱ decoder 속성 `self.matrix` → `self.llr_matrix` (H-matrix와 혼동 방지)
  - ㉲ `_restart_policy` → `_is_edge_clear_iter` (반환값 그대로, C++ Is_Iter_Type_Edge_Clear 정합)
  - ㉳ 문서 잔존 옛 이름 `_decode_matrix()` → `decoder_main()` (README, 차이.md)
- **검증**: 고정 입력 회귀 배열 단위 완전 일치, 루트·vanilla config end-to-end 정상
- **파일**: `LDPC_base/decoder.py`, `sim.py`, `run.py`, `README.md`, `차이.md` — `_test/` 아래

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
- **계획 리뷰**: 라이트 리뷰 완료 (실물 base는 18×147, LLR 도메인은 flip/magnitude, CN_STATE 5필드+Check_SRAM_sgn, 외부 자산 3종 필요). 기록: `_pm/done/20260730_review/`
