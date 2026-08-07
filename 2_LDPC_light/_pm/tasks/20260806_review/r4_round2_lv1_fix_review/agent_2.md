# agent_2 — 통합 정합, 잔재, 문서 일치 (라이트 재리뷰)

> 작성: 2026-08-07
> 대상: `2_LDPC_light/_test/20260806_setup_구성_실험/` (LDPC_base 개정본, config.json, README.md)
> 근거 문서: `_pm/tasks/20260807_리뷰후속수정/20260807_리뷰후속수정.md`, `_pm/tasks/20260806_review/r3_round3_lv2_verification/report.md`, `_pm/TODO.md`
> 검증 방식: 실험 폴더 전수 grep, 실행 시험(정상 1건), 설정 음성 시험 28종, 채널 통계 시험, LLR matrix 제약 시험 8종

**결과: MEDIUM 5건, LOW 8건 (CRITICAL, HIGH 없음)**

---

## 1. 문제 없음으로 확인한 범위

- ㉮ **삭제, 개편 잔재 없음**: `llr_tables`, `llr_profile`, `_vnu_quantize`, `self.profile`, `dv_group`, `LLRTables` 심볼이 코드에 하나도 없다. `decoder.py:36`과 `README.md:31`의 언급은 "제거했다"는 이력 서술로 의도된 것이다. `__pycache__`에도 `llr_tables` pyc가 남아 있지 않다
- ㉯ **`__init__.py` 유효**: `from .pcm import QCCode` / `from .decoder import MinSumDecoder` / `from . import channel, encoder, sim` 뿐이며 `llr_tables` 임포트가 없다. `python -m LDPC_base.run config.json` 정상 완주로 확인
- ㉰ **구 스키마 잔재 없음(코드, 설정)**: `channel.use`, `"use"` 키, `target_errors`, `stop_below`, `code_file`이 코드와 `config.json`에 없다. `chan.CHANNELS`(3종)와 `_CHANNEL_KEYS`(3종), `CHANNEL_MODES`(3종) 키가 서로 일치하며, `run.py:87`의 미지 type 에러가 `sorted(chan.CHANNELS)`를 그대로 안내한다
- ㉱ **`_rand_positions` 사용처 1곳**: `channel.py:85` `fixed_error_channel` 뿐이고 구간 슬라이스로 쓰는 곳이 없다. docstring(`channel.py:71-74`)에 전용 용도와 금지 사항이 명시됐다. 동일 시드 재현성도 실측 일치(명세 §3 "기존 결과 비트 단위 재현성 유지" 충족)
- ㉲ **strong_error 2단계 추출 정상**: N=37632, E=300, SER=0.3, SCR=0.6에서 프레임당 에러 300, strong 에러 90, strong 정정 22399, weak 정정 14933으로 `README.md:93-94`의 검증 수치와 정확히 일치. 위치 균일성은 N=20, B=40000 카이제곱으로 err 15.6, strong 에러 16.4, strong 정정 22.3 (자유도 19, 5% 임계 30.1)이라 F1 편향이 해소됐다. 경계(E=0, E=N, SER=0, SER=1)도 정상
- ㉳ **F11 제약 4종이 사용자 확정판대로 동작**: 겹침 거부, 1..max_iter 커버리지 검사, restart 단일 row/단일 iteration, restart 그룹 마지막 금지가 모두 `ValueError`로 발동하며 메시지도 구체적이다(미커버 구간 번호 나열 포함). `iter_start=0`은 허용된다. Round 3이 제시했던 완화 처방(restart 단일화 제거, restart 마지막 금지를 경고로 완화)은 **구현되지 않았다**. 겹침 금지와 `_group_of_iter` 정방향 순회가 한 쌍이라는 주석(`llr_matrix.py:86-89`)과 DAO 규칙 정본 원칙(`llr_matrix.py:26-29`)도 반영됐다
- ㉴ **F8, F14 반영 확인**: `_mx_vnu_quantize`가 중첩 `np.where` 캐스케이드(`decoder.py:70-72`)이고 비단조 th는 경고만 낸다(실측). F14 주석은 `decoder.py:146-148`(two_set 동점 유지), `decoder.py:244`(column_wise 동일), `decoder.py:372`(matrix 경로 동점 반전, 변경 금지) 세 곳에 있다
- ㉵ **키맵과 문서, 설정의 일치**: `_TOP_KEYS`, `_OUTPUT_KEYS`, `_CHANNEL_KEYS`는 README 스키마 절과 `config.json`에 모두 부합하고, `config.json`은 새 스키마로 유효하다(실행 확인)
- ㉶ **명세 §2 초안과의 의도된 차이**: `batch` 개명 보류와 `run.seed` fallback 유지는 `_pm/TODO.md`의 "폴더명, 파일명 분리" 항목으로 이관된 별도 작업이라 실수가 아니다. 최상위 키 이름을 `channel`이 아니라 `channels`로 둔 것도 명세 §2 ㉮의 "리스트 복원 후 구조에 맞춤"에 부합한다
- ㉷ **`llr_profile` 제거의 선행 조건 충족**: 하드웨어 원본 실값(CH_HD 21/14/12/10, EDGE_MAG 7/5/3/1)이 `README.md:33`과 후속수정 문서 §1에 남아 있고, README가 가리키는 상대경로 `../../_pm/tasks/20260807_리뷰후속수정/`도 실재한다

---

## 2. 발견 (MEDIUM)

### M1. 섹션 값이 null이나 비-dict면 어느 키가 문제인지 알 수 없는 raw 예외
**MEDIUM** / `run.py:52-54, 126-160`

실측 결과:

- `"run": null` → `TypeError: 'NoneType' object is not iterable` (`run.py:54` `_visible`)
- `"decoder": null` → `TypeError: argument of type 'NoneType' is not iterable` (`run.py:130`)
- `"output": null` → `TypeError: 'NoneType' object is not iterable` (`run.py:137`)
- `"run": []` → `AttributeError: 'list' object has no attribute 'get'` (`run.py:143`)

`config.setdefault("decoder", {})`는 키가 있고 값이 `None`이면 `{}`로 바꾸지 않으므로 그대로 흘러간다. 메시지에 섹션 이름이 없어 사용자가 고칠 키를 특정할 수 없고, 명세 §2 ㉯("null이면 에러")의 취지도 채우지 못한다. `_check_keys` 진입부에서 dict 여부를 확인하고 `config [run] 값이 객체가 아님` 식으로 바꾸면 해소된다.

### M2. 선택 키의 null이 검증을 통과해 런타임 크래시나 오작동으로 이어짐
**MEDIUM** / `run.py:96, 139, 150, 211-219, 230, 248`

- `channels[].seed: null`: `run.py:96`이 `if "seed" in ch and ch["seed"] is not None:`이라 검사를 건너뛴다. 이후 `run.py:218` `ch.get("seed", default_seed)`가 키 존재로 `None`을 돌려주고 `run.py:230` `np.random.default_rng([None, ...])`에서 `TypeError: object of type 'NoneType' has no len()`가 난다 (실측)
- `run.seed: null`: 채널이 seed를 생략한 경우 같은 크래시
- `output.dir: null`: `run.py:139` `resolve(None)`에서 `TypeError: expected str, bytes or os.PathLike object, not NoneType`
- `channels[].label: null`: CSV 파일명이 `fer_None.csv`가 된다
- `output.csv_prefix: null`: CSV 파일명이 `None_fixed_error.csv`가 된다
- `run.verbose: null`: 조용히 verbose off

명세 §1 F3 확정("필수 파라미터가 JSON 등 어디에서도 정의되지 않아 null/미초기화 상태면 그것도 에러")의 잔여 구멍이다. 값 제약 검사를 `.get(key)` 대신 "키가 있으면 값 검사"로 통일하면 한 번에 막힌다.

### M3. decoder 하위 키는 키맵 밖이라 fail-fast도 아니고 config 키를 지목하지도 못함
**MEDIUM** / `run.py:40-41, 171-178`

`run.py:41` 주석대로 의도된 설계지만, 실제 메시지는 `TypeError: MinSumDecoder.__init__() got an unexpected keyword argument 'betaa'` (실측)라서 `config [decoder]`라는 문맥이 없고, `load_config`가 아니라 `setup` 단계(H-matrix와 LLR matrix를 이미 읽고 요약을 출력한 뒤)에서 터진다. 명세 §2 ㉱ "검증 위치: `load_config`에서 일괄 (fail-fast)"과 어긋난다. 최상위 `decoder` 블록 이름 오타(Round 3 N-A1)는 최상위 키맵이 잡으므로 그 부분은 해소됐다.

### M4. `decoder.llr_matrix`를 생략하면 조용히 다른 디코더로 빠지고 max_iter를 줄 방법이 사라짐
**MEDIUM** / `run.py:129-134, 172-178`

실측: `decoder.llr_matrix`를 빼도 `load_config`와 `setup`을 통과하고 `matrix=False, schedule=two_set, max_iter=20`(하드코딩 기본값)으로 끝까지 완주한다. 그런데 `run.py:130`이 `decoder.max_iter`를 금지하므로, 이 경로에서는 JSON으로 iteration 수를 지정할 수단이 아예 없다. F3이 겨냥한 "조용한 무시가 결과를 바꾼다"는 부류가 그대로 남은 자리이고, README ㉯의 "max_iter는 이 파일의 마지막 iter_end가 결정"도 이 경우를 서술하지 않는다. `llr_matrix`를 필수값으로 올리거나(권장), 미지정 경로의 동작과 max_iter 취급을 README에 명시해야 한다.

### M5. 채널과 디코딩 모드의 불일치가 앞 채널을 다 돌린 뒤에 발견되고 결과가 전량 소실됨
**MEDIUM** / `run.py:184-190, 231-238, 262-263`

모드 호환 검사가 `_make_channel_fn` 안, 즉 `run_experiment` 루프 안에 있다. 실측(채널 1 fixed_error, 채널 2 strong_error)에서 채널 1을 끝까지 측정한 뒤 채널 2에서 `ValueError`가 나고, `report()`에 도달하지 못해 CSV가 한 건도 저장되지 않았다. 긴 측정에서는 손실이 크다. `setup()` 직후 전 채널을 한 번 선검사하면 해소된다.

---

## 3. 발견 (LOW)

### L1. Sim_Output에 구 스키마 config 잔재 2건
**LOW** / `Sim_Output/_tmp_rber.json`, `Sim_Output/_tmp_strong.json`

두 파일 모두 구 `channel.use` 단수 선택 스키마(2026-08-06 검증용 임시본)다. 지금 실행하면 최상위 키맵 에러가 난다. 확인 항목 1에서 찾은 **유일한 구 스키마 잔재**이며, 삭제하거나 새 스키마로 변환하는 것이 낫다. 출력 폴더에 설정 파일이 섞여 있는 것도 정리 대상이다.

### L2. README 스키마 절이 허용 키를 다 적지 않음
**LOW** / `README.md:46-75` 대 `run.py:43, 212, 218-225`

`_RUN_KEYS`에 있는 `verbose`와 `seed`가 README 어디에도 없다. 특히 `run.seed`는 채널이 `seed`를 생략했을 때 쓰이는 기본 시드(`run.py:212`, 기본값 12345)라서 재현성에 직결된다. 채널 `seed` 생략 시의 기본값과, `label`이 겹칠 때 번호 접미사를 붙이는 규칙(`run.py:220-225`)도 미기재다.

부수 사항: 기본값 3종(50, 20000, 128)이 `load_config`(`run.py:143-145`)와 `run_experiment`(`run.py:207-209`) 두 곳에 중복 정의돼 있다. 현재 값은 일치하지만 한쪽만 고치면 어긋난다.

### L3. 명세 §5가 요구한 "경로 간 수치 정밀 비교 금지"가 문서에 없음
**LOW** / `README.md`, `차이.md`

`decoder.py:146-148`에 주석으로는 있으나, 실험 README와 `차이.md` 어디에도 세 디코드 경로의 동점 규칙 차이와 FER 상대 약 7% 계통 오차 언급이 없다. 명세 §7이 실험 README를 문서 반영 대상으로 지정했으므로 미반영분이다.

### L4. README의 알려진 부정확 서술이 남아 있음
**LOW** / `README.md:124`

"잔여 floor는 전량 dv2 파리티 비트로 확인됨"의 "전량"은 Round 3에서 과장으로 판정된 표현이다(실측 88.9~96.6%). F2가 "나중에 수정"으로 유예된 항목이라 이번 수정 범위 밖일 수 있으나, 문서 정확성 항목으로 남아 있다.

### L5. 대기 중 TODO 항목의 문언이 새 스키마와 어긋남
**LOW** / `_pm/TODO.md` "폴더명, 파일명 분리" 항목

"seed는 채널별(`rber.seed` 등)에서 한 단계 위(`channel.seed`)로 올려 하나만 두고"라는 서술은 `channel`이 단수 객체였을 때의 구조를 전제한다. `channels`가 리스트로 복원된 지금은 그 자리가 없으므로, 착수 전에 문언을 갱신해야 한다(리스트 바깥의 공통 seed를 새로 둘 것인지가 결정 사항이 된다).

### L6. README와 docstring의 문서 서술 규칙 위반
**LOW** / `README.md:72-75, 86, 90-92`, `channel.py:99-103`

- `README.md:90-92`가 `① ... ②`를 쓴다. 전역 규칙상 ①②는 대화 전용이고 문서 나열은 ㉮㉯ 및 하위 ㉠㉡다 (`channel.py:99-103` docstring도 동일)
- `README.md:86`이 "strong(sd=1) 에러·나머지 weak"처럼 가운뎃점을 나열 기호로 쓴다
- `README.md:72-75`의 ㉠㉡㉢ 항목이 한 줄에 붙어 있어 항목별 줄바꿈이 없다

### L7. 에러 메시지의 줄표가 기본 콘솔에서 이스케이프로 표시됨
**LOW** / `run.py`, `llr_matrix.py` 에러 메시지 전반

실측으로 이 환경의 `sys.stdout.encoding`은 cp949다. 미처리 예외 트레이스백에서 `— 허용 키:` 부분이 `— ...`로 나온다(stderr가 backslashreplace라 죽지는 않는다). 가독성만의 문제이며, 줄표 대신 쉼표나 괄호를 쓰면 사라진다(전역 문서 규칙과도 같은 방향).

### L8. 명세 §7의 문서 반영분 미수행
**LOW** / `docs/plan.md:128`, `_pm/DONE.md`

명세 §1 Decision ②가 "plan.md, DONE.md에 이력 기록"을 지시했으나 두 문서 모두 원 결정(리스트) 문장 그대로다. 단수 `channel.use`로 갔다가 되돌린 경위가 남지 않아, 나중에 같은 논의가 반복될 여지가 있다. 작업이 아직 `tasks/`에 있으므로 완료 처리 시 함께 반영하면 된다.

---

## 4. 확인 방법 기록

- 실험 폴더 전수 grep: `llr_tables`, `llr_profile`, `_vnu_quantize`, `self.profile`, `channel.use`, `"use"`, `_rand_positions`, `target_errors`, `stop_below`, `code_file`, `frames_per_batch`, `dv_group`, `LLRTables`
- 정상 실행: `python -m LDPC_base.run config.json` 완주, CSV 저장 확인
- 설정 음성 시험 28종: 구 스키마, 섹션 오타, 키 오타, 값 범위 위반, null 주입, 스칼라 points, 단일 dict channels, `_desc` 무시, decoder 오타, max_iter 금지 등
- 채널 통계 시험: strong_error 개수 일치, 카이제곱 위치 균일성 3종, 경계 4종, fixed_error 재현성
- LLR matrix 제약 시험 8종: 정상, 겹침, 빈틈, restart 마지막, restart 다중 row, iter_start=0, 시작 지연, 범위 밖 restart, 비단조 th 경고
