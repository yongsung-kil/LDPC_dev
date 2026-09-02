# Round 1 결과: 관점 리스트업

> 에이전트 2개(opus)가 각각 13개, 14개 관점을 도출. 중복 통합 후 9개 축으로 정리.

도출된 관점:

| # | 관점명 | 확인 항목 (요약) | 대상 파일/범위 |
|---|--------|----------------|--------------|
| A | 균일 양자화 수치 규약 + 저장/로드 왕복 | num_bits 파생값 정합, edge_mag 이원 복원식, save/load 필드 1:1, int 캐스팅·float32 정밀도, 파일명 규약(uniform 문자열, _NAME_RE), max/min_value 의미, restart 생략 대칭, floor_flag 고정 기입 | `LDPC_base/llr_matrix.py`, `Input/LLR/*uniform*.txt` |
| B | 캐스케이드 일반화 + 0 레벨 도입의 디코더 파급 | _vnu_quantize 루프 vs C++ elif 체인, mag 0의 min1/min2 점유, sgn×0의 -0.0 부호 판정, RESET=top_level 파급, 정수성 전제, 3 고정 잔재(주석·문서), 비단조 th | `LDPC_base/decoder.py` (_vnu_quantize, _cnu_update, _init_state) |
| C | use_input_llr_matrix 분기 + setup 파일 생성 부작용 + config 검증 | generated_llr_matrix_path 주입과 키맵 충돌, 파일명에 dv_max 미포함(무경고 덮어쓰기), Input/LLR 추적 정책, 기본값 리터럴 3중 산재, false 가지 llr_matrix dict 미검증, 난수 스트림 파생 충돌, iter30 파일 vs max_iter120 config 어긋남 | `LDPC_base/run.py` (load_config, setup), `config.json`, `Ideas/vanilla/config.json`, `.gitignore` |
| D | 단계별 함수 추출 리팩토링의 동작 보존 | _DecodeState 속성 대응, _record_iteration→_check_errors 순서 제약, 배치 압축 대상 목록 완전성, final_* 의미 보존, _build_result↔sim.py 키 계약, 교체 지점 시그니처 | `LDPC_base/decoder.py` (단계 함수, decoder_main), `LDPC_base/sim.py` |
| E | 패키지 경계·임포트 체인·실행 진입점 | 실행 루트 이중성(LDPC_base vs tools), ImportError fallback 오진 범위, registry 파싱, 숫자 시작 패키지명 -m 동작, __init__ 노출 기준 | `LDPC_base/run.py`, `__init__.py` 3종, `Ideas/`, `tools/H_mat_gen/` |
| F | 이름 일괄 수정 완결성 + 요약 출력 정확성 | 의견1 항목별 대조표, 치환 후유증(조사·부분문자열), 요약 출력과 실제 소비값 일치, summary만으로 균일 모드 실행 판별 가능 여부, git hash dirty 미표시 | `LDPC_base/sim.py`, `run.py`, `_pm/done/20260808_의견1_반영/의견1.md` |
| G | 데이터 파일 무결성 | LLR 3파일 자기 정합(_validate 5제약), H-matrix 헤더·dv 분포 상호 정합, dv 11 구간 비매칭 의도, uniform 파일 재생성 대조, 개행/인코딩 | `Input/LLR/*.txt`, `Input/H_matrix/*.qc` |
| H | 문서-코드 일치 + 문장 작성 규칙 자기 적용 | README "3-bit 전용" 서술 잔존, 차이.md #9, plan.md 구 모듈 표, tools README 시제 불일치, 교체 지점 표 3중 기재 동기화, 문장 규칙 ㉮㉯㉰ 위반 잔존, 구 코드 유실(examples/, llr/ 프리셋) | `README.md`, `docs/plan.md`, `docs/차이.md`, `Ideas/vanilla/README.md`, `tools/H_mat_gen/README.md` |
| I | 실행 검증 | 파일 경로·균일 경로·vanilla config 3종 실행, round-trip FER 동일성 실측, uniform 파일 재생성 바이트 비교, 오류 경로(모드 불일치, 미등록 decoder.type), 성능 스케일(num_bits↑) | `2_LDPC_light/` 전체 (산출물은 scratchpad/Sim_Output) |

## 다음 단계 결정

→ Round 2 (lv2, 4팀)
  사유: 대상이 코드 약 1,600줄 + 데이터 4파일 + 문서 5종 + 실행 검증으로 크고, 관점 9축이 서로 다른 파일 묶음에 몰려 있어 팀별 교차 분석이 유효. 팀 구성:
  - 팀 A (uniform_numeric): 관점 A + B — 균일 양자화 델타 로직의 수치 정확성
  - 팀 B (config_run): 관점 C + F — run.py 분기·검증·부작용·요약 출력·이름 수정
  - 팀 C (refactor_exec): 관점 D + E + I — 리팩토링 동작 보존, 패키지 구조, 실제 실행
  - 팀 D (data_docs): 관점 G + H — 데이터 무결성, 문서 정합, 문장 규칙
