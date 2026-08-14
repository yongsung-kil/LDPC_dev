# Round 2 / 팀 B (config_run) 종합

작성: 2026-08-08 14:30:15
관점: C(`use_input_llr_matrix` 분기 + setup 부작용 + config 검증) + F(이름 수정 완결성 + 요약 출력 정확성)

## 워커 구성

| 워커 | 범위 | 보고서 |
|---|---|---|
| B-1 | `use_input_llr_matrix` 분기, setup의 파일 생성 부작용, 재현성, git 정책 | `worker_b_1.md` |
| B-2 | config 키맵 6종 전수 대조, `_desc` 규칙, in-place 정규화, 기본값 산재, 난수 파생, 검증 순서 | `worker_b_2.md` |
| B-3 | 의견1 이름 수정 항목별 대조, 기계 치환 후유증, 요약 출력 사실 정확성 | `worker_b_3.md` |

세 워커 모두 실행 없이 정적 분석으로 진행했고, 저장소 추적 파일은 수정하지 않았다.
팀 리더가 다음 주장을 코드로 직접 재확인했다: `channel_fn`의 난수 소비 순서(`run.py:353-357`,
`encoder.py:11-19`), `load_config`의 두 가지 분기(`run.py:183-215`), `setup`의 저장 순서
(`run.py:290-304`), `report`의 호출 순서(`run.py:530` vs `534-536`), `_git_commit_hash`의 예외 범위
(`run.py:413-420`), 미커밋 `config.json` diff, `Input/LLR/` 파일 3종.

---

## 발견 목록

심각도 기준: CRITICAL(중단·비가역 손상) / HIGH(틀린 결과를 내지만 진행) / MEDIUM(엣지케이스 위험) / LOW(개선 제안)

| # | 심각도 | 문제 | 위치 | 근거 |
|---|---|---|---|---|
| B-1 | **HIGH** | `frames_per_batch`를 바꾸면 같은 seed에서도 모든 프레임의 잡음 실현값이 달라진다. 원인은 `encode()`가 버리는 `msg`를 `generate_message`가 매 배치 뽑아 난수 스트림을 어긋내는 것. 문서 3곳이 "결과 영향 없음"을 단언한다 | `run.py:353-357`, `encoder.py:11-19`, `sim.py:54-79` / 서술 `run.py:33`, `config.json:44`, `README.md:79-80` | `channel_fn`이 배치마다 `generate_message`(난수 소비) → 채널(난수 소비) 순서로 돌아 배치 경계가 소비량을 바꾼다. numpy 재현 실험: 메시지 추출을 끼우면 128 vs 64 불일치, 잡음만 뽑으면 일치. `encode()`는 msg를 무시하고 all-zero를 반환하므로 이 소비는 결과에 기여하지 않고 스트림만 어긋낸다 |
| B-2 | MEDIUM | `use_input_llr_matrix=true`일 때 `internal_quantize`가 검증도 소비도 되지 않는다. 저장소 `config.json`이 정확히 그 상태(true + `max_iter: 120`)라 설정 파일만 보면 max_iter 120으로 도는 것처럼 읽히지만 실제 값은 `LLR_MATRIX_HD_1.txt`의 20이다 | `run.py:182`, `190-204` / `config.json:25`, `33` | true 가지(`run.py:187-189`)는 `llr_matrix`만 처리하고 `internal_quantize`는 `_DECODER_KEYS`(66행) 통과 뒤 방치된다. `"num_bits": "여섯"` 같은 타입 오류도 통과한다 |
| B-3 | MEDIUM | false 가지에서 `decoder.llr_matrix` dict가 `_check_keys`를 받지 않는다. `dir` 오타는 조용히 기본 폴더로 흘러가 엉뚱한 위치에 파일을 쓰고, `"dir": null`은 config 에러 대신 raw `TypeError`를 낸다 | `run.py:207-208` | `.get("dir", 기본값)`은 키가 있으면 `None`을 돌려주고 이어지는 `os.path.join(None, ...)`이 터진다. 같은 config가 토글 방향에 따라 통과·실패가 갈린다 |
| B-4 | MEDIUM (Decision) | git 추적 폴더 `2_LDPC_light/Input/LLR/`에 실행 산출물을 쓴다. 파라미터를 바꿔 스윕할 때마다 새 파일이 커밋 후보로 쌓이고, 커밋된 `..._iter30.txt`는 현 config와 무관한 고아다 | `run.py:301-303`, 루트 `.gitignore`, `config.json:33` | `git ls-files`로 uniform 파일이 추적 중임을 확인. 커밋 파일의 row 꼬리는 `-1 1 30 -1`(iter_end=30), config는 `max_iter: 120` |
| B-5 | MEDIUM | 생성 파일명이 `dv_max`를 담지 않는다. `dv_max`가 다른 H-matrix로 같은 `internal_quantize`를 돌리면 내용이 다른 파일이 같은 이름으로 무경고 덮어써진다 | `run.py:209-211`, `298`, `301-303` | 파일명에 mode/num_bits/channel_llr/max_iter만 들어가고 `dv_to`를 정하는 `code.col_deg.max()`는 빠진다. 저장 전 존재 확인이 없고 알림 print는 저장 뒤에 나온다 |
| B-6 | MEDIUM | "균일 매트릭스인가"라는 정보가 파일명에만 있고 조립부(`run.py`)와 판별부(`llr_matrix.py`)가 두 파일로 나뉘어 있다. `num_bits=3` 산출물을 사람이 개명하면 VNU 출력 레벨이 `[3,2,1,0]` 대신 DAO 기본값 `{7,5,3,1}`로 잡혀 진행은 되고 결과만 틀린다 | `run.py:209-211` ↔ `llr_matrix.py:46`, `170`, `202-203` | `num_bits=3`이면 `th_len == 3`이라 기본 분기가 열린다. `num_bits`가 3이 아니면 `NotImplementedError`로 드러나므로 조용히 틀리는 구간은 `num_bits=3` 하나다 |
| B-7 | MEDIUM | `internal_quantize.mode`가 2SD/3SD도 통과해, 추적 폴더에 파일을 다 쓴 뒤 첫 복호에서 `NotImplementedError`로 실패한다. 실행은 실패하고 쓰레기 파일만 남는다 | `run.py:201-204` → `294-303` → `decoder.py:371-374` | 합성·저장·재로드가 2SD에서도 성공하고, `_check_channel_mode`(`run.py:378-379`)도 rber에 2SD를 허용하므로 통과한다 |
| B-8 | MEDIUM | `internal_quantize.num_bits`와 `max_iter`에 상한이 없다. `num_bits` 비용은 `2**(num_bits-1)-1`로 늘어 오타 하나가 프로세스 정지로 이어진다 | `run.py:195-200`, `llr_matrix.py:222-227`, `decoder.py:156-157`, `sim.py:45-50` | `_vnu_quantize`가 임계값 수만큼 파이썬 루프로 `np.where`를 돌고, 그 루프가 iteration × column block 안쪽에 있다. `max_iter`는 `np.zeros((max_iter, num_dv))` 할당으로 직결된다 |
| B-9 | MEDIUM | 생성 폴더 기본값 `"Input/LLR"`이 config 파일 위치 기준으로 풀려, `Ideas/*/config.json`에서 플래그만 false로 바꾸면 `Ideas/vanilla/Input/LLR/`이라는 새 폴더가 `makedirs`로 조용히 생긴다 | `run.py:206-214`, `301` | `Ideas/vanilla/config.json`에는 `llr_matrix.dir`이 `"../../Input/LLR"`로 있어 지금은 공용 폴더를 가리키지만, 그 키가 없거나 dict가 아니면 기본값 경로를 탄다 |
| B-10 | MEDIUM | 난수 파생 `int(1e6 * point)`의 절단 때문에 1e-6보다 가까운 rber 포인트 두 개가 완전히 같은 난수 스트림을 쓴다 | `run.py:398` | `0.001`, `0.0010005`, `0.0010009`가 전부 `1000`이 된다. 채널 간 충돌은 `channel_index`가 막고, 음수 시드는 `_check_channel`이 막아 도달 불가 |
| B-11 | MEDIUM | `_git_commit_hash()`가 working tree dirty 여부를 기록하지 않아, 미커밋 변경 상태로 돌린 실험의 `code commit:` 줄이 실제 코드와 다른 커밋을 가리킨다 (현 저장소가 그 상태) | `run.py:413-420`, 사용처 `run.py:530` | `git rev-parse --short HEAD`만 실행한다. `git status`에 `M config.json`, `M TODO.md`가 있다 |
| B-12 | MEDIUM | `_git_commit_hash()`가 `except OSError`만 잡아 `subprocess.TimeoutExpired`가 전파된다. 이 호출이 CSV 저장 루프보다 **먼저**라 예외 시 전 측정 결과가 하나도 안 남는다 | `run.py:530` vs `534-536` | `TimeoutExpired`는 `SubprocessError` 계열이라 `OSError`로 잡히지 않는다. `report()` 순서는 config 사본 → `lines` 조립(여기서 호출) → CSV 저장 → summary.txt |
| B-13 | MEDIUM | 문서 3곳이 "false면 `llr_matrix` 키는 무시된다"고 적지만, 코드는 `llr_matrix.dir`을 생성 파일 위치로 실제 사용한다. `run.py` docstring은 17-18행에서 스스로 모순된다 | `run.py:17-18`, `207-208`, `config.json:19-20`, `README.md:69` | 서술과 동작 불일치. B-3, B-9와 한 뿌리다 |
| B-14 | LOW | true 가지 재현성: 산출물에 LLR matrix 파일명만 남고 내용·해시·절대경로가 남지 않아, 그 파일을 나중에 고치면 과거 실행을 재현할 수도 고쳤다는 사실을 알 수도 없다 | `run.py:527`, `530-531`, `llr_matrix.py:315-317` | `report`는 `shutil.copy`로 원본 config만 복사한다. false 가지는 config 사본의 4개 값 + summary의 `dv=[1]~[N]`으로 결정론적 재생성이 가능해 상대적으로 안전하다 |
| B-15 | LOW | `run` 기본값 3개(50 / 20000 / 128)가 검증·소비·요약 세 곳(+`sim.py` 시그니처)에 리터럴로 복제되어 있다. 현재 값은 전부 일치하지만 한쪽만 고치면 요약이 조용히 거짓을 찍는다 | `run.py:231-233` / `369-371` / `325-327`, `sim.py:11-12` | 다른 섹션 기본값은 `setdefault` 단일 출처라 비대칭이다 |
| B-16 | LOW | `print_progress`, `output.csv_prefix`, `output.label`, `channels[].label`에 타입 검증이 없다. 뒤 셋은 폴더·파일 이름에 그대로 들어간다 | `run.py:69-70`, `373`, `387`, `523`, `533` | 키맵만 통과하고 값 검사가 없다 |
| B-17 | LOW | `stop_below_fer` 중단 시 요약은 `points` 전체를 광고하는데 CSV에는 일부만 남는다. 서술 3곳이 "해당 채널의" 범위를 적지 않는다 | `run.py:407-408`, `313-315`, `run.py:34`, `config.json:45`, `README.md:81` | `break`는 포인트 루프만 빠져나오고 채널 루프는 계속 돈다 |
| B-18 | LOW | `points`에 같은 값을 두 번 넣으면 같은 시드로 같은 실험을 두 번 돌리고 로그 CSV 파일명이 겹쳐 덮어쓴다 | `run.py:397-398`, `550/555/559` | 시드가 `point` 값으로만 파생되어 중복 포인트가 구분되지 않는다 |
| B-19 | LOW | 실험 요약 누락: strong_error의 SER/SCR, 중복 해소된 실제 라벨, H-matrix 파일명, LLR matrix 전체 경로, "생성 후 로드"였다는 사실, `print_progress` | `run.py:310-330`, `313-315` vs `387-393`, `pcm.py:108` | 같은 type 채널 2개는 요약에서 구분되지 않는다 |
| B-20 | LOW | true 가지에서 LLR matrix 파일 부재 시 "파일 없음"이 아니라 "파일명에서 모드 판별 불가"가 먼저 뜬다. H-matrix 쪽 명시적 안내와 비대칭 | `run.py:287-288` vs `304`, `llr_matrix.py:165-168` | 이름 판별이 `open`보다 먼저 돈다 |
| B-21 | LOW | 키맵 밖 파생 키 `generated_llr_matrix_path`를 config dict에 주입한다. 지금은 재검증 경로가 없어 무해하나, 코드에 이미 있는 `_` 접두 무시 규칙을 쓰면 이름만으로 내부 값임이 드러난다 | `run.py:215` vs `66`, `83-85` | `load_config` 호출은 `run.py:576` 한 곳뿐이고 `report`는 원본 파일을 복사한다 |
| B-22 | LOW | 이름 스윕 미적용 잔존: `tools/H_mat_gen/*`의 `rng` 11곳, `run.py:501-504`의 `r`/`f`, `run.py:425`의 `f`/`t` | 워커 3 보고서 A절 표 | 의견1 #7이 `LDPC_base/`에만 적용됐다 |
| B-23 | LOW | 코드 주석에 결정 이력 서술 8건 잔존 (문장 작성 규칙 ㉮ 위반), 부정 먼저 뒤집는 문형 1건 (규칙 ㉯) | `pcm.py:8,15`, `channel.py:16,74,98`, `llr_matrix.py:15,27,29,32-35` / `run.py:180` | "(사용자 결정 2026-08-06)", "(리뷰 F1 후속)" 계열. 규칙을 도입한 커밋 자신이 위반 상태다 |
| B-24 | LOW | 모듈 docstring에 `run.max_frames`와 `output.csv_prefix` 설명 누락. `max_frames`는 측정량을 좌우하는 키다 | `run.py:31-35`, `41-43` vs `_RUN_KEYS run.py:68`, `_OUTPUT_KEYS run.py:70` | |

**분포: HIGH 1, MEDIUM 12, LOW 11. CRITICAL 0.**

---

## 문제 없음으로 확인한 항목

| 항목 | 근거 |
|---|---|
| 키맵 커버리지 | 키맵 6종(+채널 3종) 전 키를 grep으로 소비 위치까지 추적. 키맵 밖에서 읽히는 **사용자** 키는 없고(내부 주입 1건뿐), 완전히 죽은 키도 없다. `_LOG_TO_ITEM` 4개는 `decoder.LOG_ITEMS`와 정확히 일치. 두 config 파일 모두 키맵을 지킨다 |
| `_desc`(`_` 접두) 무시 규칙 | `_visible`이 `_check_keys`를 거쳐 최상위/decoder/internal_quantize/run/output/log/channels[] **및 `_path_pair` 내부**(H_matrix, llr_matrix)까지 빠짐없이 적용된다. `config.json:5-8`의 `H_matrix._desc`가 정상 통과 |
| `points` in-place 정규화의 파급 | 정규화가 전 소비부보다 먼저 끝나고, `report`는 변형 dict가 아니라 원본 파일을 복사한다(`run.py:527`). 라벨 생성은 `points`를 쓰지 않는다 |
| `_check_int` 되쓰기 비대칭 | `isinstance(value, int)`를 요구해 문자열 `"50"`도 실수 `50.0`도 막는다. 통과한 값은 이미 int라 타입 오염이 없다 |
| 기본값 리터럴 **값** 일치 | 50 / 20000 / 128 / None 네 개가 검증·소비·요약(+`sim.py` 시그니처) 네 곳에서 전부 같다. 어긋난 값 0건 |
| 검증 순서 | `decoder.max_iter` 금지 검사가 키 집합 검사보다 먼저라 사용자는 이유 있는 메시지를 본다 |
| `os.makedirs(os.path.dirname(...))` | `generated_path`가 항상 절대경로로 만들어진 뒤 호출되므로 빈 dirname이 되는 입력이 없다 |
| 생성 스킵 분기 부재 | `setup`에 파일 존재 확인이나 생성 스킵이 없어 "매번 재생성이라 stale 로드 없음" 전제는 코드에서 참이다 |
| 채널 간 시드 충돌, 음수 시드 | `channel_index`가 채널을 분리하고, `_check_channel`이 음수 포인트를 막아 도달 불가 |
| **의견1 이름 수정** | 18개 항목 중 16개 완료, 2개 부분(#7 tools/ 미적용, #15 주석 이력 서술). 구 이름(`decoder_cls`, `mx`, `verbose`, `fail_rows`, `agg_`, `res`, `n_it`, `n_active`, `frozenset`)은 Grep 전수 **0건** |
| **기계 치환 후유증** | 조사 어긋남 0, 이름 중복 0, 부분문자열 오염 0. `res`→`decode_result`가 `result`/`point_results`를, `b`→`batch`가 `frames_per_batch`를, `mx`→`llr_matrix`가 `matrix`를 건드리지 않았다 |
| 이름-의미 정합 | `total_active_frames`(iteration별 배치 누적 배열)와 소비부 계산(`sum[k]/active[k]`)이 일치. `final_err_bits`의 "마지막 처리 iteration 값" 의미가 계산부·docstring 양쪽에서 일치 |
| 외부 계약(dict 키 / CSV 헤더) | `decoder.py` → `sim.py` → `run.py` 3단 키 계약이 가드 조건까지 일치. CSV 헤더 파손 없음 |
| **요약 출력 정확성** | `.get(키, 기본값)` 전수를 실제 소비값과 대조 → 어긋남 0건. `QCCode.summary()`(3줄)와 `LLRMatrix.summary()`(1줄)가 `"\n".join`과 섞여도 줄 구성 정상. summary.txt는 콘솔 출력의 상위집합 |
| 균일 모드 판별 가능성 | 생성 파일명이 mode/num_bits/channel_llr/max_iter를 담고 그 파일명이 요약 2행에 실리므로, summary만으로 균일 모드와 파라미터를 판별할 수 있다 |
| `decoder.max_iter` vs `llr_matrix.max_iter` | `decoder.py:116` 단일 대입 이후 갱신이 없어 항상 같다. 중복 표시일 뿐 오류 아님 |
| `%` 마커 잔존 | 0건 |
| 미커밋 `config.json` diff | `_desc` 줄 분리 1건. 동작 영향 없고, 세 서술이 각각 `llr_matrix.py:165-169`, `llr_matrix.py:92`, `run.py:178-181`과 맞으며, 같은 `_desc` 블록의 `internal_quantize:` 항목과 형식이 일관된다 |

---

## 팀 내 교차 분석

### 워커 간 심각도 모순 해소 (코드 근거 우선)

1. **false 가지 `llr_matrix` 무검증** — B-1은 MEDIUM, B-2는 LOW로 매겼다.
   → **MEDIUM 채택.** 단순 무시가 아니라 **잘못된 위치에 파일을 쓰는 부작용**이 따라오고
   (`run.py:207-208`이 `dir`을 생성 위치로 실제 사용), 같은 config가 토글 방향에 따라
   통과·실패가 갈려 README가 광고하는 "플래그만 바꿔 토글"과 어긋난다.

2. **`int(1e6 * point)` 절단** — B-2는 MEDIUM, B-3은 LOW로 매겼다.
   → **MEDIUM 채택.** 이 리뷰의 심각도 정의에서 MEDIUM이 곧 "엣지케이스 위험"이고,
   `_check_channel`이 `0 < p < 0.5`만 요구해 촘촘한 스윕이 설정상 가능하다.

3. **생성 알림 print가 `print_progress`와 무관** — B-1은 LOW로 지적, B-3은 문제 없음으로 판정.
   → **문제 없음 채택.** `run.py:35` docstring이 이 키를 "진행 상황 콘솔 출력"으로 한정했고,
   `saved:` / `run dir:` / 요약도 모두 무조건 출력이라 계열이 일관된다.

### 워커 간 상호 보강 (한쪽만으로는 그림이 안 나오는 것)

4. **B-2 + B-4의 결합이 저장소 현재 상태를 설명한다.** 커밋된 `..._iter30.txt`는
   false 가지 실행의 산출물인데, 지금 config는 true 가지다. 즉 **저장소에 담긴 config로는
   그 파일이 영원히 쓰이지 않고**, 동시에 `internal_quantize.max_iter: 120`도 영원히 읽히지
   않는다. 커밋된 uniform 파일과 `internal_quantize` 블록 둘 다 현재 실행 경로에서 고립된
   상태다. 워커 1은 파일 쪽에서, 워커 2는 검증 쪽에서 같은 고립을 각각 짚었다.

5. **요약 출력은 무죄, 설계가 함정이다.** 워커 3은 요약이 찍는 `max_iter`가 실제값(20)이라
   정확함을 확인했고, 워커 1은 config 파일만 읽으면 120으로 오해한다고 지적했다.
   두 진술은 모순이 아니다. **오해는 실행 전 설정 설계 단계에서 생기고 실행 후 요약에서
   교정된다.** 따라서 수리 지점은 요약이 아니라 `load_config`의 무시 섹션 알림(B-2)이다.

6. **재현성의 취약점이 예상과 반대 방향이다.** 워커 1의 추적 결과 false 가지는
   config 사본의 4개 값 + summary의 `dv=[1]~[N]`으로 결정론적 재생성이 가능하고,
   오히려 **true 가지가 약하다**(파일 내용·해시가 산출물에 없음, B-14). 워커 3이 확인한
   "요약만으로 균일 모드 판별 가능"과 합치면, 산출물 기록의 구멍은 균일 모드가 아니라
   **사람이 만든 LLR 파일을 쓰는 기본 경로**에 있다.

7. **B-1(HIGH)이 팀 범위 밖 관점과 맞물린다.** `frames_per_batch`가 결과를 바꾼다는 것은
   아이디어 A/B 비교(이 시뮬레이터의 존재 이유)를 오염시킨다. 팀 C의 실행 검증에서
   같은 config를 `frames_per_batch`만 바꿔 두 번 돌리면 실측으로 확정된다.
   수리는 싸다: `encode()`가 msg를 쓰지 않는 동안 `generate_message` 호출을 빼거나
   별도 generator를 쓰면 스트림이 잡음 전용이 되어 배치 무관이 실제로 성립한다.
   실물 인코더가 들어오면 그 방법도 깨지므로, 배치 무관을 계약으로 유지하려면
   프레임 단위 스트림 파생이 필요하다.

### 한 뿌리로 묶이는 발견

- **B-3, B-9, B-13**은 모두 "`llr_matrix.dir`이 false 가지에서 살아 있는데 문서는 무시라고
  적었다"는 한 뿌리다. false 가지에서도 `llr_matrix`를 `_check_keys`로 검증하고 문서 서술을
  동작에 맞추면 셋이 함께 닫힌다.
- **B-2, B-7**은 "분기별 검증 커버리지가 비대칭"이라는 한 뿌리다. 분기와 무관하게
  `internal_quantize`가 있으면 항상 검증하고, `mode`를 디코더 지원 범위(현재 HD)로 좁히면
  둘이 함께 닫힌다.
- **B-4, B-5, B-6**은 "생성 산출물의 정체성이 파일명 하나에 걸려 있다"는 한 뿌리다.
  파일명 조립 함수를 `llr_matrix.py`로 옮겨 판별부와 짝을 이루게 하고, 산출물 폴더를
  추적 밖으로 빼면 셋이 함께 완화된다.
- **B-11, B-12**는 같은 함수(`_git_commit_hash`)의 두 결함이다. 한 번에 고칠 수 있다.

---

## 미커버 영역

팀 B 범위 안에서 이번에 닿지 못한 것:

- ㉮ `output.label` / `channels[].label`이 파일시스템 금지 문자나 경로 구분자를 담을 때의
  안전성. 타입 검증 부재(B-16)만 확인했고 실제 파일명 생성 결과는 미검증
- ㉯ `SER`/`SCR` 키를 `strong_error`가 아닌 채널에 넣었을 때 `_check_channel`의 처리
- ㉰ `stop_below_fer` 중단이 실제로 걸린 실행의 산출물 정합(요약과 CSV 불일치, B-17)을
  실측으로 확인하지 않음
- ㉱ B-1(`frames_per_batch`)의 FER 수치 영향 크기. 원인과 방향은 확정했으나
  실제 실험에서 얼마나 벌어지는지는 실행 검증이 필요하다

다른 팀 소관으로 넘긴 것:

- `llr_matrix.py`의 균일 양자화 수치 규약(`uniform_edge_mag`, `edge_mag[-1]==0`의 파급,
  `channel_llr` 상한 부재의 물리적 타당성) → **팀 A**. B-6의 "`num_bits=3` 개명 시 조용히
  틀림"과 B-8의 상한 부재는 팀 A의 수치 판정과 합쳐야 최종 심각도가 정해진다
- 실행 검증 전반(false 가지 완주, `Ideas/vanilla` 하위 생성 폴더 발현 여부, 배치 크기
  실측 비교), `2_LDPC_light/llr_tables.py` 고아 모듈 → **팀 C**
- `README.md` / `docs/` 문서 정합(`Input/LLR/` 설명에 uniform 파일 누락, `docs/` 어디에도
  `use_input_llr_matrix`·`internal_quantize` 서술 없음), 문서 .md의 문장 규칙 위반 → **팀 D**
