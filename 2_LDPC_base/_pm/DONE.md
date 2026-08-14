# DONE — 완료 이력 (2_LDPC_light)

### 2026-08-14 — minsum_dual_clip 원인 규명 정정과 환경 대조, 실험 로그 신설
클리핑 악화 원인을 dv별 로그와 LLR 파일 실값으로 확정하고, 환경 대조로 논문
delta의 유효 조건을 재현. workspace 공통 실험 로그와 슬롯 config 체계 신설
- **배경**: 어제 결론의 원인 서술(채널 LLR 8, dv=2 반전 불능)이 균일 생성 경로
  값을 잘못 인용한 것이었음 (실험은 LLR 파일 로드, dv별 ch 5/10/13/28).
  H-matrix 품질이나 edge 양자화 자체가 원인 아니냐는 사용자 질문에서 출발
- **변경**:
  - ㉮ 원인 정정: 사망 경계는 dv 열 최대 extrinsic `Q + (dv-1)·P` < ch (dv별).
    지배 열 dv=4(ch=10)가 (2,3)에서 9로 사망, (2,5)는 11로 생존, dv별 에러
    로그로 직접 확인. dv=2(ch=28)는 무클립에서도 반전 불능(기지 위반)이라
    on/off 차이와 무관
  - ㉯ 환경 대조: headroom(edge 상한 15, ch=8)에서 무클립 붕괴를 논문 가이드
    (4,8)이 0/256로 복구, balanced(ch=16)에서는 역전. 클리핑 득실은 ch 대비
    edge 상한 여유가 결정한다는 인사이트 확보
  - ㉰ `workspace/실험로그.md` 신설 (실험 환경과 인사이트 상설 기록, 사용자 지시)
  - ㉱ 슬롯 config 체계: config_headroom/balanced/real.json 준비, scan.py를
    config와 쌍 목록 인자로 일반화. 실물 파일명 두 개만 채우면 즉시 실행
- **파일**: workspace/minsum_dual_clip/ (README, scan.py, config 3종),
  workspace/실험로그.md, _pm/done/20260813_minsum_dual_clip/, 3_LDPC_ideas/README.md

### 2026-08-13 — 논문 ieee:9496601 적용 실험 (minsum_dual_clip)
CNU min1/min2 이중 상한 클리핑(P ≤ Q)을 workspace 실험으로 적용, 토이 조건 판정 보류
- **배경**: 논문 아카이브 stage5 산출물(IEEE TCAD 2022, NAND 저비트폭 min-sum)을
  2_LDPC_light 교체 지점 구조로 첫 적용. 베이스 refactor 4건의 수치 불변도
  worktree 교차 실행으로 사전 검증
- **변경**: workspace/minsum_dual_clip/ 신설 (decoder.py의 MinSumDualClipDecoder,
  `_c2v_reconstruct`만 재정의, P와 Q는 클래스 속성, scan.py로 (P,Q) 10쌍 스캔).
  LDPC_base 무변경
- **결과**: (7,7) 무효과 조건에서 vanilla와 수치 완전 일치(구현 검증). 유효
  클리핑은 전부 악화, 원인은 토이 스케일(채널 LLR 8, 상한 7)에서 반전 가능 조건이
  ch ≤ P × dv로 줄어드는 것. P<Q가 P=Q보다 낫다는 구조 주장은 방향 재현.
  실물 파라미터 반입 후 재실험 (상세: done/20260813_minsum_dual_clip/)
- **파일**: 2_LDPC_light/workspace/minsum_dual_clip/ (신규), _pm/tasks → done 이동

### 2026-08-13 — edge 양자화 파라미터 분리 + config 스키마 재편
edge 메시지 레벨을 bit 수와 최대값 두 축으로 분리하고, config를 "자리를 미리
만들어 두고 플래그가 필요한 것만 골라 읽는" 구조로 재편 (사용자 설계 확정)
- **배경**: 기존 num_bits는 레벨 수와 최대값(2^(n-1)-1)이 묶여 있어 C++ 3bit의
  레벨 배치 {7,5,3,1}(최대 7을 4개 레벨로 벌린 형태)을 표현할 수 없었다.
  채널 LLR 대비 edge 무게(최대값)와 해상도(레벨 수)는 별개의 실험 축이다.
  또 사용자가 값 자리를 재구성하지 않고 스위치만 바꿔 경로를 오가는 config를 원했다
- **변경**:
  - ㉮ edge 양자화 분리: use_default_edge_quantization(decoder 레벨, 기본 true =
    bits 3 + max 7 = C++ 3bit 레벨 {7,5,3,1})이 false면 edge_quantization 블록
    {edge_resolution_bits(기본 3), edge_max_value(2^n-1 형태, 기본 7,
    2^(bits-1)-1 미만이면 오류)}를 읽는다. num_bits와 internal_quantize 키는 폐기
  - ㉯ 레벨 배치는 max부터 (max+1)/2^(bits-1) 간격의 내림차순 균일
    (edge_quantization_levels). th는 레벨값과 동일 (C++는 th가 LLR matrix의
    튜닝 데이터라 고정 규칙이 없고, 간격 1에서 th=[top..1]인 기존 균일 경로의
    확장으로 사용자 결정)
  - ㉰ load()의 균일 생성물 인식을 [n..1] 패턴에서 등차 감소(마지막 항 2d-1)
    패턴으로 일반화해 벌린 레벨 파일도 왕복 복원. 생성 파일명에 max 표기 추가
    (uniform_{bits}bit_max{max})
  - ㉱ decoder 스키마: mode, max_iter, channel_llr_HD/_2SD/_3SD(mode별 자리,
    강한 region부터, 길이 = region 수 1/2/4)를 decoder 레벨에 두고 균일 생성
    경로에서만 소비 (파일 로드 경로는 파일명과 파일 iter_end가 결정,
    "decoder.max_iter를 두면 에러" 규칙은 이 소비 구분으로 대체)
  - ㉲ channels 스키마: 리스트를 폐기하고 객체로. type(문자열 또는 리스트)이
    측정 채널을 고르고 값 공간은 자리를 미리 만들어 둔다 (고른 type이 쓰는 공간만
    소비, 존재하는 공간은 전부 형식 검사, points와 label 키 폐기).
    rber는 RBER 값 리스트, fixed_error는 프레임당 에러 bit 수 리스트로
    fixed_error type과 strong_error type이 공용 소비하고, strong_ratios가
    strong_error의 SER/SCR를 담는다 (에러 개수 자리 공유는 사용자 결정)
  - ㉳ log 스키마: enabled(상위 스위치)와 items(항목 묶음)로 분리.
    seed는 최상위에서 run.seed로 이동
  - ㉴ 설명 정본은 workspace/_template/config.json (실험 폴더 config는 정본 참조
    한 줄만). 템플릿 전 키가 기본값으로 채워져 있어 플래그만 바꾸면 동작.
    vanilla config도 새 스키마로 이행
- **검증**: 단위 24건(레벨 생성, 오류 조건, 저장/로드 왕복 4조합, DAO 파일 회귀,
  uniform 파일명 불일치 에러) + 스키마 14건(실파일 3종, 경로 전환, mode 전환,
  길이/범위/2^n-1 위반, type 리스트, 공간 누락, log 무력화, 구 스키마 거부) +
  E2E 3경로(파일 로드, 기본, bits3 max15 + ch 16). edge_max_value를 키울 때
  channel_llr을 같은 배율로 키우지 않으면 복호가 무너지는 스케일 효과 확인
- **파일**: LDPC_base/llr_matrix.py, LDPC_base/run.py, README.md,
  workspace/_template/config.json, workspace/vanilla/config.json

### 2026-08-10 — 진행 줄에 누적 지표 표시 + 시작 시각 기록
측정 중간에도 최종 줄과 같은 지표가 보이도록 확장 (사용자 지시 2026-08-10)
- **변경**:
  - ㉮ 진행 줄에 누적 fer, ber, avg_iter, 처리량(f/s, it/s)을 표시 (끝나야 보이던
    지표를 중간에도 출력, 콘솔 \r 갱신과 summary.txt 실시간 반영 양쪽.
    진행 줄과 최종 줄의 형식 동일)
  - ㉯ 표시명 decoding_iter를 avg_iter로 변경 (내부 키 avg_decoding_iteration과
    CSV 열명은 유지)
  - ㉰ summary.txt 머리의 code commit 다음 줄에 실험 시작 시각 기록
    (start: YYYY-MM-DD HH:MM:SS)
- **검증**: 실행 중간 summary에서 진행 줄의 누적 지표와 start 줄 확인,
  종료 후 최종 줄 대체 확인
- **파일**: LDPC_base/sim.py, LDPC_base/run.py

### 2026-08-10 — summary에 진행 줄 실시간 반영 + 초당 iteration 표시
측정 중 진행 줄까지 summary.txt에 반영하고 처리량에 it/s 추가 (사용자 지시 2026-08-10)
- **변경**:
  - ㉮ run_fer_point가 summary_path를 받아 진행 줄을 갱신 간격마다 파일 끝에 제자리
    갱신하고 (offset 기록 후 tail 교체), 포인트가 끝나면 최종 결과 줄로 대체.
    콘솔 \r 갱신과 같은 내용이며 터미널 여부와 무관하게 파일에는 항상 반영
  - ㉯ 결과 줄 처리량에 초당 합산 복호 iteration(it/s) 추가. 합산 iteration은
    성공 프레임의 수렴 iteration + 실패 프레임의 max_iter (avg_decoding_iteration과
    같은 분자, point_result 키 ips)
- **검증**: 백그라운드 실행 중간에 summary 꼬리에서 진행 줄 확인, 종료 후 최종 줄로
  대체 확인 (290 it/s = 14.5 f/s × 20 iter 일치), 다중 포인트 쌓임 확인
- **파일**: LDPC_base/sim.py, LDPC_base/run.py

### 2026-08-10 — summary 실시간 기록과 decoding iteration 지표 변경
summary.txt를 측정 중에 기록하고 iteration 지표가 실패 프레임을 포함하도록 변경
(사용자 지시 2026-08-10)
- **변경**:
  - ㉮ 실행 폴더와 summary.txt 머리(run 표기, code commit, 실험 요약)를 측정 시작
    전에 생성하고 (create_run_dir 분리), 포인트가 끝날 때마다 콘솔과 같은 결과 줄을
    summary.txt에 덧붙인다 (run_experiment의 summary_path). CSV/로그/그림은 종료 후 저장
  - ㉯ summary.txt의 결과 줄이 콘솔 출력과 동일해졌다 (sim.py가 summary_line으로 공유)
  - ㉰ avg_decode_success_iteration을 avg_decoding_iteration으로 개명하고 실패
    프레임을 max_iter로 집계에 포함 (표시명 decoding_iter, CSV 열명도 개명)
- **검증**: vanilla 실행에서 summary.txt 결과 줄이 콘솔과 문자 단위 동일, 전 프레임
  실패 실행의 decoding_iter가 0.0에서 20.0(max_iter)으로 바뀜, CSV 열명 확인
- **파일**: LDPC_base/sim.py, LDPC_base/run.py, README.md

### 2026-08-10 — 진행 줄 갱신 간격 파라미터화 (run.progress_interval_frames)
고정 100프레임이던 진행 줄 갱신 간격을 config 키로 이동 (사용자 지시 2026-08-10)
- **변경**: config `run.progress_interval_frames` (기본 100, 1 이상 정수 검증).
  run_fer_point 인자로 전달, config 2벌(vanilla, _template)과 README 스키마 반영
- **검증**: 간격 60 설정으로 64, 128, 192프레임 갱신 후 최종 줄 확인 (가짜 터미널)
- **파일**: LDPC_base/sim.py, LDPC_base/run.py, workspace/vanilla/config.json,
  workspace/_template/config.json, README.md

### 2026-08-10 — 콘솔 출력 정리 (요약 불릿 정렬 + 측정 중 진행 줄 갱신)
실험 시작 요약과 측정 중 진행 상황을 읽기 쉽게 재구성 (사용자 지시 2026-08-10)
- **배경**: 시작 요약이 형식이 제각각인 줄 나열이라 잘 안 읽혔고, 측정 중에는
  포인트가 끝날 때까지 아무 표시가 없었다
- **변경**:
  - ㉮ 요약을 구분선(= 64자) 사이의 "- 이름  값" 불릿 목록으로 재구성 (이름 열 정렬).
    LLR matrix는 파일명과 공급 경로만 표시하고 max iteration을 별도 항목으로 분리
  - ㉯ 측정 줄 머리에 "[채널라벨 p=포인트]" 표기를 붙이고 필드를 "e/fr = 에러/프레임,
    fer, ber, avg_iter" 형태로 간결화. 측정 중에는 100프레임 단위로 진행 줄을 캐리지 리턴으로
    같은 자리에 갱신하고 (터미널 출력일 때만, 리다이렉트 시 최종 줄만), 포인트가
    끝나면 결과 한 줄을 남기고 줄바꿈해 포인트별로 쌓인다. 채널 헤더 줄은 각 줄이
    자기 설명이 되어 제거
  - ㉰ summary.txt도 같은 불릿 목록을 쓴다 (구분선은 콘솔 전용)
- **검증**: vanilla 실행으로 요약과 측정 줄 형식 확인, 가짜 터미널로 갱신 줄 실증
  (128, 220프레임에서 \r 갱신 후 최종 줄 덮어쓰기, 포인트별 줄바꿈, 접두어 유지)
- **파일**: LDPC_base/run.py, LDPC_base/sim.py

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
