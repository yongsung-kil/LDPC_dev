# worker_d_3 — 팀 D(data_docs) 워커 3: 문장 규칙 자기 적용 + 구 코드 유실과 TODO 정합

> 관점 H 후반부. 검사 범위: `git diff ea88882..HEAD -- 2_LDPC_light/` + 미커밋 `config.json`.
> 판정 기준: 루트 `CLAUDE.md` "문장 작성 규칙" ㉮㉯㉰ + 글로벌 "문서 수정 후 검사 루틴" 4항.
> 확인 방법: 대상 파일 전문 읽기, Grep 전수 검색, `git diff --name-status -M`,
> 현행 API와 구 API 시그니처 실측 대조(`inspect.signature`).

---

## 요약

| 심각도 | 건수 | 내용 |
|--------|------|------|
| HIGH | 5 | H1 vanilla README 실행 안내 오류 / H2 H_mat_gen README 시제·경로 오류 / H3 plan.md 헤더 덧대기 + §3.1 유령 모듈표 / H4 `llr_tables.py` 사문화 잔존 + DONE.md 허위 기록 / H5 `llr_tune.py` 탐색 기능 유실 미등록 |
| MEDIUM | 4 | M1 README 이력 줄 / M2 `llr/` 프리셋 지식 부분 유실 / M3 줄표·가운뎃점 접속·나열 용법 전면 / M4 용어 미풀이 (VNU·CNU·DAO·CSW 등) |
| LOW | 6 | L1~L6 (아래) |
| 문제 없음 | 3 | % 마커 잔존 없음, 기계 치환 후유증 없음, `select_irregular` 실행 불가 상태와 TODO 서술 정확히 일치 |

---

# 파트 1 — 문장 작성 규칙 자기 적용

## 1-1. 규칙 ㉮ 위반 (과거·현재 대비 서술 금지)

> "리뷰 반영이나 수정 시 기존 문장 뒤에 단서나 괄호를 덧붙이지 않는다. 그 문장을 처음부터
> 그렇게 설계됐던 것처럼 다시 쓴다. 과거가 어땠고 지금 어떻다는 서술을 코드와 문서에
> 남기지 않는다 (변경 이력은 `_pm/DONE.md`와 git이 담당)"

### 위반

| # | 심각도 | 파일:라인 | 인용 | 판정 근거 |
|---|--------|-----------|------|-----------|
| H1 | HIGH | `2_LDPC_light/Ideas/vanilla/README.md:13` | `실험 루트(_test/20260806_setup_구성_실험/)에서:` | 삭제·미추적된 sandbox 경로를 실행 위치로 안내한다. 현행 실행 위치는 `2_LDPC_light/` (README.md:23, run.py:9와 불일치). 이 README를 그대로 따르면 실행 실패 |
| H2 | HIGH | `2_LDPC_light/tools/H_mat_gen/README.md:15-17` | `㉰ **주의**: select_irregular.py는 구 본체 API(구 decoder/sim/channel) 기준 — _test/20260806_setup_구성_실험/LDPC_base 개정본을 본체로 반영할 때 새 구조(채널 dict, decoder_main)로 손봐야 실행된다` | ㉠ "구 본체 API"가 과거 대비 서술 ㉡ 본체 반영은 커밋 2e600ea에서 이미 끝났는데 "반영할 때"라는 미래형 ㉢ 존재하지 않는 경로 참조. 세 겹으로 오도 |
| H3 | HIGH | `2_LDPC_light/docs/plan.md:4-6` | `**2026-08-07 구조 개편**: _test/20260806_setup_구성_실험/ 개정본을 본체로 반영 — 현행 구조·스키마·실행 방법은 README.md가 정본이다. 이 문서의 §3.1 모듈 표 등 구조 서술은 개편 전 기준이며, 결정 이력(§1, §7)은 계속 유효.` | 이번 델타에서 plan.md에 들어간 변경은 **이 3줄이 전부**다. 규칙 ㉮가 금지하는 "덧대기"의 교과서적 사례이며, 그 결과 §3.1 표(53~61행)가 존재하지 않는 파일 4종(`config.py`, `llr_tables.py`(사문화), `mpi_runner.py`(삭제), `examples/fer_curve.py`(삭제))을 모듈 구성으로 계속 열거한다. 헤더 한 줄로 무효화 선언만 하고 본문은 그대로 둔 상태 |
| M1 | MEDIUM | `2_LDPC_light/README.md:6` | `> 2026-08-07: _test/20260806_setup_구성_실험/의 개정본을 본체로 반영 (구 코드는 git 이력에 보존)` | 날짜 + 변경 이력 + "구 코드" 3박자. 정본 README 머리말 자리에 DONE.md 소관 내용이 들어가 있다. 동일 내용이 `_pm/DONE.md:50-58`에 이미 기록됨 |
| L1 | LOW | `2_LDPC_light/tools/H_mat_gen/select_irregular.py:12-14` | `주의 (2026-08-07): 이 스크립트는 구 본체 API 기준이라 **현재 실행 불가** — 새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질 필요 (TODO 등록됨). import만 LDPC_base로 돌려놓은 상태다.` | "현재 실행 불가"는 사실이라 남겨야 하나, "구 본체 API 기준", "import만 …돌려놓은 상태다"는 작업 경위 서술이라 규칙 ㉮ 위반 |
| L2 | LOW | `2_LDPC_light/docs/차이.md:5` | `본체 커밋 72b825a에서 파생하여 2026-08-06 개정)` | 문서 개정 이력을 문서 안에 남김 |
| L3 | LOW | `2_LDPC_light/LDPC_base/pcm.py:7-8` | `이 포맷만 지원 (2026-08-06 사용자 결정 — 구 포맷('#' 주석 + 'M_b N_b z' 헤더) 지원 제거)` | 폐기된 포맷의 스펙까지 코드 주석에 보존. "Ref-C 포맷만 지원한다"로 다시 쓰면 충분 |
| L4 | LOW | `LDPC_base/channel.py:16`, `docs/차이.md:47` | `난수는 original XOR25 대신 numpy Generator (plan.md 기존 결정과 동일).` / `(채널 소관, plan.md 기존 결정)` | "기존 결정"의 "기존"이 시간 대비를 부른다. "plan.md 결정"으로 충분 |

### 예외 후보 (이력 문서 성격 — 위반 목록에서 분리)

| 대상 | 예외로 보는 근거 |
|------|-----------------|
| `_pm/` 전체 (`TODO.md`, `DONE.md`, `tasks/`, `done/`) | 규칙 ㉮ 본문이 "변경 이력은 `_pm/DONE.md`와 git이 담당"이라고 이력의 종착지를 명시적으로 지정했다. 이력 서술이 이 폴더에 있는 것이 규칙의 의도 |
| `docs/plan.md` §1 결정 사항 표(14~24행), §7 확정 사항 표(122~131행) | 절 제목 자체가 "확정된 결정 사항 (2026-07-29 논의)", "확정 사항 (2026-07-30 사용자 결정)"이다. 결정에는 결정 시점이 붙는 것이 정상이며, "과거가 어땠고 지금 어떻다"는 대비 서술이 아니라 결정의 근거·시점 기록 |
| `docs/plan.md` §2 대응표의 근거 열 (`2026-08-03 사용자 확인`, `리뷰 반영` 등) | 위와 같은 성격 (결정 근거 열) |
| `docs/차이.md` §1~§2 본문 | 이 문서의 대비 대상은 "자기 과거"가 아니라 "외부 original C++"이다. 규칙 ㉮의 사정 범위 밖 |
| git 커밋 메시지 | 규칙 ㉮가 지정한 이력 담당처 |

### 판단 필요 (사용자 결정 요청)

| # | 사안 | 선택지 |
|---|------|--------|
| D1 | `docs/plan.md`의 성격 규정 | ㉮ §3.1 모듈 표·§3.1b 도구 표를 현행 구조(`LDPC_base/`, `Ideas/`, `Input/`, `tools/H_mat_gen/`)로 다시 쓰고 헤더 3줄 삭제 ㉯ plan.md를 "결정 이력 전용 문서"로 못박고 §3, §5의 구조 서술을 삭제(구조는 README.md 단일 정본) — H3의 근본 해소책은 둘 중 하나여야 하며, 지금처럼 헤더 단서만 붙은 상태로는 어느 쪽도 아니다 |
| D2 | 코드 docstring의 "사용자 결정 (YYYY-MM-DD)" 표기 | `llr_matrix.py:15,27,29,32`, `pcm.py:7,15`, `decoder.py:141`, `channel.py:1,98`, `docs/차이.md` 다수에 있다. 결정의 **근거**를 코드에 남기는 것은 유용하나 **날짜**는 이력에 가깝다. 규칙 ㉮ 적용 대상인지(날짜만 제거할지, 통째로 둘지) 확정 필요. 건수가 20건 이상이라 일괄 처리 대상 |
| D3 | `docs/plan.md:63` | `2026-08-05부터 encoder.py에 … 마련해 … (§7 #6, 기존 "인코더 불필요" 결정을 구조상 보완)` — §3 설계 절 본문에 놓인 결정 번복 서술. 결정 이력 절(§7)로 옮길지, 현재 상태 서술로 다시 쓸지 |

## 1-2. 규칙 ㉯ 위반 (규칙은 긍정문)

> "하는 일을 바로 말한다. '~하지 않는다 — 실제로는 …한다'처럼 부정을 먼저 말하고
> 줄표 뒤에서 뒤집는 문형을 쓰지 않는다"

전수 검색(`않는다|않음|아니라|아니고|없다` + 줄표/쉼표 뒤집기 패턴) 결과 **금지 문형에 정확히 해당하는 것은 1건**이다. 이 규칙은 대체로 잘 지켜졌다.

### 위반

| # | 심각도 | 파일:라인 | 인용 | 판정 |
|---|--------|-----------|------|------|
| L5 | LOW | `2_LDPC_light/LDPC_base/run.py:180-181` | `"decoder.max_iter는 JSON에 두지 않는다 — LLR matrix 파일(또는 internal_quantize.max_iter)이 결정"` | 부정 선언 후 줄표 뒤에서 실제 규칙을 말하는 문형. 긍정문 형태는 "max_iter는 LLR matrix 파일(또는 internal_quantize.max_iter)이 결정한다 — JSON의 decoder.max_iter는 받지 않는다". 다만 이것은 사용자에게 보이는 **에러 메시지**라 "무엇이 잘못됐는지"를 먼저 말하는 편이 자연스러울 수 있어, 규칙 예외로 둘지 판단 여지 있음 |

### 판단 필요

| # | 사안 | 인용 |
|---|------|------|
| D4 | `Ideas/vanilla/README.md:34-35` | `LDPC_base(정본)에는 아이디어 코드를 넣지 않는다 — 베이스 개선은 모든 아이디어에 자동 전파되어야 하므로` — 부정으로 시작하지만 줄표 뒤가 **뒤집기가 아니라 이유**다. 규칙 ㉯의 금지 문형("실제로는 …한다")에는 해당하지 않는다고 판정. 다만 "아이디어 코드는 `Ideas/{이름}/`에만 둔다 — 베이스 개선이 모든 아이디어에 자동 전파되어야 하므로"로 쓰면 규칙 취지에 더 맞다 |

### 위반 아님으로 판정한 것

- `llr_matrix.py:29-30` "원본 C++의 조용한 col_idx=0 fallback은 재현하지 않음" — original과의 차이 서술(외부 대비)이라 규칙 밖.
- `LDPC_base/__init__.py:4` "절대 FER 일치는 보장하지 않으며, 최종 검증은 실물 C++ 이식으로 수행한다" — 뒤집기가 아니라 병렬 서술.
- `Ideas/vanilla/README.md:6` "어떤 교체용 함수도 재정의하지 않아 LDPC_base 정본과 동작이 같다" — 부정이 사실 서술 자체.

## 1-3. 규칙 ㉰ 위반 (이름과 용어는 명확성 우선)

> "사용자가 모를 수 있는 업계 용어·축약어는 풀어 쓴다" + 글로벌 규칙 "업계 은어·약어를
> 처음 쓸 때는 반드시 풀어서 정의하고 원 이름을 함께 적는다"

**M4 (MEDIUM).** 아래 표는 각 문서에서 그 용어가 **처음 등장하는 위치**와 그 자리에서 풀어 썼는지를 대조한 것이다.

| 용어 | README.md 첫 등장 | 풀이 | docs/차이.md 첫 등장 | 풀이 | 그 밖 |
|------|-------------------|------|----------------------|------|-------|
| DAO | `:15` `**DAO LLR_MATRIX 형식만 사용**` | ✗ (풀이는 `:155` `DAO(decoder auto optimizer)` — 140행 뒤) | `:4` `DAO 연동 빌드` | ✗ | `llr_matrix.py:1` ✗ |
| LLR | `:15` | ✗ (log-likelihood ratio 미표기, 저장소 전체에 없음) | `:18` | ✗ | ✗ |
| VNU | `:162` `VNU 출력 레벨 {7,5,3,1}` | ✗ | `:24` | ✗ | 저장소 전체에 Variable Node Unit 표기 **0건** |
| CNU | `:122` | ✗ | `:36` | ✗ | 저장소 전체에 Check Node Unit 표기 **0건** |
| CSW | `:97` `iteration별 CSW/bit error 평균` | ✗ | `:19` | ✗ | `llr_matrix.py:21`에만 `check-sum weight` 풀이 있음 |
| FER | `:4` | ✗ (frame error rate 미표기) | — | — | ✗ |
| BER / RBER | `:103` `post_fec_ber(복호 후 BER)` | △ (한글 뜻만, 원 이름 없음) | — | — | RBER은 `README:146`에서 무풀이 |
| dv / dc | `:68` `전 dv 공통` | ✗ (column degree 표기는 `llr_matrix.py:29`, `pcm.py:10`에만) | `:18` | ✗ | — |
| th / ch | (스키마 밖 `:68` `channel_llr`) | △ | `:21`, `:32` | ✗ | `decoder.py`, `llr_matrix.py` 전반 ✗ |
| mag / sgn | — | — | `:37` `VNU 양자화` 맥락 | ✗ | `decoder.py:132-137` ✗ |
| HD / 2SD / 3SD | `:15` | ✗ (hard decision 풀이는 `plan.md:126`에만, soft decision은 저장소 전체 0건) | `:17` | ✗ | — |
| EDGE / EDGE_MAG | `:162` (`VNU 출력 레벨`로 간접 설명) | △ | `:22` `±EDGE_MAG_3` | ✗ | — |
| restart | `:15` | ✗ (동작 설명은 `차이.md:35`, `llr_matrix.py:23-26`) | `:34` | ✗ | — |
| floor flag | — | — | `:19` `error floor 감지 상태머신` | △ | `llr_matrix.py:13` `floor_flag` 무풀이 |
| min-sum | `:119` | ✗ | — | — | — |
| layered | `:123` `layered / informed dynamic scheduling` | ✗ | — | — | — |
| QC | `:1` 제목 `경량 QC-LDPC 시뮬레이터` | ✗ (quasi-cyclic 표기 저장소 전체 0건) | — | — | `pcm.py:1` ✗ |
| lifting | `:18` (파일명 나열) | ✗ | — | — | `plan.md:73`에서 간접 설명 △, `tools README:8` ✗ |
| PEG | `:18` (파일명 나열) | ✗ | — | — | `plan.md:72`, `tools README:7`, `peg.py:1` 모두 `PEG(Progressive Edge Growth)` ✓ |
| shift / circulant | `:14` (헤더 포맷) | ✗ | — | — | `pcm.py:3-5` 연결 규칙으로 설명 ✓ |
| z (lifting size) | `:14` (헤더 포맷 나열) | ✗ | `:48` `z lane` | ✗ | `pcm.py:4` 맥락 설명 △ |
| genie | (README에 미등장) | — | `:23` `**genie**: 매 iteration 결정을 정답(all-zero)과 비교…` | ✓ | `plan.md:126` ✓ |
| hook | `:112` `(업계 용어로는 hook)` | ✓ 모범 사례 | — | — | `decoder.py:41` ✓ |

**판정**: `hook`, `genie`, `PEG`는 규칙대로 풀어 썼다(`README.md:110-115`의 "교체 지점" 정의 문단은 이 규칙의 모범 사례다). 그러나 이 프로젝트에서 가장 자주 쓰이는 축약어 **VNU, CNU, LLR, CSW, DAO, dv, th, ch, HD/2SD/3SD**는 저장소 어디에서도 원 이름이 나오지 않거나, 첫 등장에서 140행 뒤에 풀린다. "사용자가 모르는 용어가 하나라도 있으면 그 문서는 검토·승인이 불가능하다"는 글로벌 규칙 기준에서 README.md와 docs/차이.md는 현재 검토 불가 상태다.

**권고**: README.md 상단이나 `docs/`에 용어 대조표(약어 / 원 이름 / 한 줄 뜻) 1개를 두고, 각 문서 첫 등장 자리에서 그 표를 가리키는 방식이 문서 수를 늘리지 않으면서 규칙을 충족한다. 이 방식 채택 여부는 사용자 결정 사항.

## 1-4. 추가 검사 (글로벌 "문서 수정 후 검사 루틴")

### ㉮ 줄표(—)·가운뎃점(·)을 접속어나 나열 기호로 쓴 곳 — M3 (MEDIUM)

전수 카운트 (변경 대상 파일):

| 파일 | 줄표 | 파일 | 줄표 |
|------|------|------|------|
| `LDPC_base/run.py` | 40 | `README.md` | 18 |
| `LDPC_base/decoder.py` | 25 | `LDPC_base/llr_matrix.py` | 13 |
| `docs/plan.md` | 23 | `LDPC_base/channel.py` | 8 |
| `LDPC_base/sim.py` | 6 | `tools/H_mat_gen/README.md` | 3 |
| `LDPC_base/pcm.py` | 3 | `config.json` | 2 |
| `Ideas/vanilla/README.md` | 2 | `Ideas/vanilla/config.json` | 1 |
| **합계** | **144** | `docs/차이.md`, `encoder.py` | 0 |

대표 사례 (전부 "즉·왜냐하면·그리고"를 줄표로 대신한 접속 용법):

- `README.md:15` `LLR 파일 보관 — **DAO LLR_MATRIX 형식만 사용**`
- `README.md:67` `파일을 로드**해 디코딩한다 — \`internal_quantize\`의 num_bits(…)`
- `LDPC_base/run.py:24` `decoder.internal_quantize: use_input_llr_matrix=false일 때 필수 —`
- `LDPC_base/decoder.py:14` `_check_errors() ← 에러 검사(genie) — 성공/실패 확정 + 배치 압축(마스킹)`
- `LDPC_base/llr_matrix.py:29` `구간에도 없으면 에러 (사용자 결정 —`

가운뎃점 나열 용법 (곱셈 기호 `H·r`, `E·SER`, `2·r_offset`은 정당하므로 제외):

| 파일:라인 | 인용 |
|-----------|------|
| `README.md:3` | `계획·결정 사항·제약:` |
| `README.md:19` | `plan.md(계획·결정), 차이.md(…)` |
| `README.md:73` | `채널·포인트별 스트림은` |
| `README.md:166` | `실물 H-matrix·LLR_MATRIX 실값 미반입` |
| `docs/plan.md:5` | `현행 구조·스키마·실행 방법은` |
| `docs/plan.md:47` | `### 3.1 코드 위치·모듈 구성` |
| `docs/plan.md:33` | `column 단위 연산·업데이트는 반영` |
| `docs/plan.md:114` | `실물 C++ 이식·최종 검증` |
| `docs/plan.md:129` | `SNR/RBER 범위·배치 크기는` |
| `docs/plan.md:131` | `단일·다중 채널·포인트를 동일하게 처리` |
| `Ideas/vanilla/README.md:30` | `(채널·포인트 동일하게)` |
| `tools/H_mat_gen/README.md:10` | `승자 선별·저장` |
| `LDPC_base/decoder.py:10,203` | `syndrome 계산, CN 상태·결과 버퍼 초기화` |
| `LDPC_base/decoder.py:264` | `VNU 출력·CN 갱신` |
| `LDPC_base/run.py:28` | `채널·포인트별 난수 스트림은` |
| `LDPC_base/run.py:39` | `잔여 에러·최종 CSW·dv별 분해` |
| `LDPC_base/llr_matrix.py:128` | `같은 규칙(겹침·빈틈 금지)으로` |

**규칙 충돌 지적 (사용자 결정 요청, D5)**: 글로벌 검사 루틴 1항은 "줄표를 접속어로 쓴 곳은 접속사·쉼표·괄호로 바꾼다"고 하는데, 프로젝트 `CLAUDE.md` 규칙 ㉯는 "줄표 뒤에서 **뒤집는** 문형을 쓰지 않는다"고만 하여 줄표 자체는 허용하는 것처럼 읽힌다. 144건을 전부 고칠지, 프로젝트 규칙을 "줄표는 부연에 한해 허용"으로 명문화할지 결정이 필요하다. 결정 없이 부분 수정하면 문서마다 문체가 갈린다.

### ㉯ 조건·항목 나열에 번호 누락

| 심각도 | 파일:라인 | 내용 |
|--------|-----------|------|
| L6 | `README.md:150-151` | "채널 모델" 절 하단 2개 항목이 무번호 `-` 불릿. 같은 문서 다른 절(62~84, 102~106, 135~137)은 ㉮㉯㉰를 지킴 |
| L6 | `README.md:162-167` | "남은 근사/제한" 6개 항목 전부 무번호 `-` 불릿 |
| L6 | `Ideas/vanilla/README.md:34-36` | "주의" 절 2개 항목 무번호. 같은 문서의 "무엇인가" 절은 ㉮㉯㉰, "새 아이디어 추가 절차"는 `- 1.` ~ `- 6.`으로 규칙을 지킴 → 한 문서 안에서 불일치 |
| L6 | `LDPC_base/decoder.py:17-35` | 모듈 docstring "syndrome-aided flip/magnitude 도메인" 8개 항목 무번호 (코드 docstring도 규칙 대상이라고 `CLAUDE.md`가 명시) |

`docs/차이.md` §3(47-48행 ㉮㉯), `tools/H_mat_gen/README.md`(12-19행 ㉮㉯㉰㉱), `LDPC_base/llr_matrix.py:3-7`(㉮㉯)은 규칙을 지켰다.

### ㉰ 번호 나열의 항목별 줄바꿈 누락

| 심각도 | 파일:라인 | 인용 |
|--------|-----------|------|
| L6 | `LDPC_base/llr_matrix.py:34-35` | `검사 항목: 그룹 겹침 금지, 1..max_iter 커버리지(빈틈 금지), restart 그룹은 단일 row/단일 iteration, restart 그룹은 마지막이면 안 됨.` — 4개 항목을 한 줄에 쉼표로 나열. 항목별 줄바꿈 + 번호 필요 |

`docs/차이.md:18`은 표 칸 안에서 `<br>`를 써서 규칙을 지켰다 (모범 사례).

### ㉱ 기계 치환 후유증 (조사 어긋남, 이름 중복, 부분문자열 오염)

**문제 없음.** 커밋 d42ca8c의 일괄 개명(`s`→`state`, `rng`→`random_generator`, `cfg`→`run_config`/`log_config`/`output_config`, `dec`→`decoder`, `n_active`→`num_active_frames`, `res`→`point_result`, `verbose`→`print_progress`) 결과를 `LDPC_base/` 전 파일에서 확인했다. 조사 어긋남, 이름 중복(`state.state` 류), 부분문자열 오염 사례 없음. `frames_per_batch`와 지역변수 `batch`가 공존하지만 이는 의미가 다른 별개 값이라 오염이 아니다.

**부수 관찰 (L7, LOW)**: 개명이 `LDPC_base/`에만 적용되어 `tools/H_mat_gen/`에는 `rng`(`gen_example_code.py:28`, `lifting.py:10`, `peg.py:32`), `conn`, `s0`, `dec`, `cands`가 남아 있다. `gen_example_code.py`는 이번 델타에서 수정된 파일(R085)이므로 규칙 ㉰의 사정 범위 안이다.

## 1-5. % 마커 잔존

**문제 없음.** `2_LDPC_light/` 전체를 Grep한 결과 한글·영문 단어 바로 뒤에 붙은 `%`는 **0건**이다. 검출된 `%` 104건은 전부 오탐 범주였다:

- `LDPC_base/run.py:524` — `strftime("%y%m%d_%H%M%S")` 포맷 문자열
- 나머지 103건 — `_pm/done/`, `docs/review/` 아래 리뷰 기록 안의 C++ 코드 인용(`(…+1)%2`, `"LLR_MATRIX_%d.txt"`, `s=(tmp%(len_max-j))+j`)

---

# 파트 2 — 구 코드 유실과 TODO 정합

## 2-1. 이동 (대체 경로 확인됨)

`git diff --name-status -M ea88882..HEAD`로 rename 검출, 이동 후 파일의 실재와 내용을 표본 확인했다.

| 구 경로 | 새 경로 | git 판정 | 내용 이동 확인 |
|---------|---------|----------|----------------|
| `2_LDPC_light/pcm.py` | `LDPC_base/pcm.py` | R080 | ✓ `QCCode` 클래스, `load`/`save`/`syndrome`/`count_cycles4`/`summary` 전부 존재 |
| `2_LDPC_light/channel.py` | `LDPC_base/channel.py` | D+A (내용 개정으로 rename 미검출) | ✓ 3종 채널(`rber`/`fixed_error`/`strong_error`)로 재작성, 출력이 dict로 변경 |
| `2_LDPC_light/decoder.py` | `LDPC_base/decoder.py` | D+A | ✓ `MinSumDecoder.decoder_main()` + 단계 함수 7개 |
| `2_LDPC_light/encoder.py` | `LDPC_base/encoder.py` | D+A | ✓ `generate_message`/`encode` |
| `2_LDPC_light/sim.py` | `LDPC_base/sim.py` | D+A | ✓ `run_fer_point`/`save_csv` |
| `2_LDPC_light/run.py` | `LDPC_base/run.py` | D+A | ✓ 4단계 구조(`load_config`/`setup`/`run_experiment`/`report`) |
| `tools/peg.py` | `tools/H_mat_gen/peg.py` | R100 | ✓ 무변경 |
| `tools/lifting.py` | `tools/H_mat_gen/lifting.py` | R100 | ✓ 무변경 |
| `tools/gen_example_code.py` | `tools/H_mat_gen/gen_example_code.py` | R085 | ✓ import 경로 + 기본 출력 위치만 변경 |
| `examples/select_irregular.py` | `tools/H_mat_gen/select_irregular.py` | R089 | ✓ import 경로 + 주의 docstring만 변경 (본문 로직 동일) |
| `examples/example_18x147_z256.qc` | `Input/H_matrix/example_18x147_z256.qc` | R099 | ✓ |
| `examples/__init__.py` | `Ideas/vanilla/__init__.py` | R100 | ✓ (빈 파일) |

**신설(대응 없음)**: `LDPC_base/llr_matrix.py`, `LDPC_base/__init__.py`, `Ideas/{__init__,registry}.py`, `Ideas/vanilla/{decoder.py,config.json,README.md}`, `Input/LLR/*.txt` 3종, `config.json`, `tools/H_mat_gen/{__init__.py,README.md}`, `docs/차이.md`.

## 2-2. 유실 — TODO 등록됨

| 삭제 파일 | TODO 항목 | 정합 |
|-----------|-----------|------|
| `mpi_runner.py` | `_pm/TODO.md:25-26` "mpi_runner 재설계 (사용자 확정 2026-08-07: 나중에 진행) / 구버전은 본체 반영 때 삭제 — 새 구조(LDPC_base.run) 기준으로 새로 설계" | ✓ 삭제 사실과 재설계 방침이 모두 기록됨. `TODO.md:33` "mpi_runner 슈퍼컴 반입 (재설계 완료 후)"으로 후속까지 연결 |
| `examples/irregular_17x144_z256.qc` | `_pm/TODO.md:24` "irregular 재현 시드(103)는 `done/20260807_리뷰후속수정/` 문서 §6에 기록됨" | ✓ 파일 자체는 사라졌으나 `select_irregular.py`가 시드 103으로 재생성 가능하고 시드가 기록됨 |
| (이동분) `select_irregular.py` 실행 불가 | `_pm/TODO.md:22-24` | ✓ 아래 2-5 참조 |

## 2-3. 유실 — TODO 미등록

| # | 심각도 | 삭제 파일 | 담당하던 기능 | 대체 존재 여부 | TODO |
|---|--------|-----------|---------------|----------------|------|
| H5 | **HIGH** | `examples/llr_tune.py` (75줄) | `llr/` 폴더의 프로파일 후보들을 fixed-error 포인트에서 **FER로 비교해 좋은 것을 고르는 탐색 스크립트**. docstring: "HW-근사 3-bit internal precision(VNU 출력 {7,5,3,1} + dv별 채널 LLR)의 TH_HD 시작값 후보들을 비교해 좋은 것을 고른다 (TH 원본 소실 — plan.md 참조)" | **없음.** 균일 양자화 모드(`LLRMatrix.make_internal_uniform_matrix`)는 매트릭스를 **하나 생성**할 뿐, 여러 후보를 실행해 FER로 **비교·선별**하지 않는다. 파라미터 탐색 절차 전체가 사라졌다 | ✗ 미등록 |
| M2 | MEDIUM | `llr/README.md` + `llr/ch{5577,6666,66810,6688}_th*.txt` 6종 + `llr/ch6688_thdv.txt` + `llr/_hw_orig_ch.txt` | ch/th 조합 프리셋과 **튜닝 결론 지식** | **부분 계승.** 아래 상세 | △ 부분 |
| L8 | LOW | `examples/fer_curve.py` + `examples/fer_curve.json` | 예시 부호 정정능력 커브(FER vs RBER / Eb/N0) 생성 + PNG | ✓ `LDPC_base/run.py`의 `_plot_fer_curves()` + config `log.fer_curve_png`가 대체. 단 AWGN Eb/N0 축은 `channels.rber`로 흡수되어 축 의미가 바뀜 | ✗ 미등록 (대체가 있으므로 낮음) |
| L9 | LOW | `examples/fixed_error_sweep.py` | error bits 300부터 20bit 단위 스윕 | ✓ config `channels[].points` 리스트가 대체 (`plan.md:131` "sweep이라는 이름/개념 대신 channels 리스트로") | ✗ 미등록 (설계상 흡수됨) |
| H4 | **HIGH** | (삭제되지 않고 **잔존**) `2_LDPC_light/llr_tables.py` | 위 `llr/*.txt` 포맷 로더 (`LLRProfile`, `load_profile`, `ch_mag_by_col`, `dv_group`) | — | ✗ 미등록. 아래 상세 |

### H4 상세 — `llr_tables.py` 사문화 잔존 + DONE.md 허위 기록

- `2_LDPC_light/llr_tables.py`는 **지금도 git 추적 중**이다 (`git ls-files` 확인).
- 그런데 이 모듈의 docstring 1행은 `"""LLR 파라미터 프로파일: 2_LDPC_light/llr/*.txt 파일에서 로드.` 이고, **`llr/` 폴더는 이번 델타에서 전부 삭제됐다**. 읽을 파일이 존재하지 않는 로더가 남았다.
- `LLRProfile`, `load_profile`, `ch_mag_by_col`, `dv_group`을 import하는 코드는 `2_LDPC_light/` 전체에 **0건**이다 (Grep 전수 확인).
- 반면 `_pm/DONE.md:70`은 이렇게 적고 있다: `F14 주석·문서화, llr_profile 제거(llr_tables.py 삭제), 채널 리스트 복원` — **"llr_tables.py 삭제"는 사실이 아니다.**
- 추가로 `docs/plan.md:56`은 이 파일을 현재 모듈 구성표에 올려 두고 있다: `| llr_tables.py | 2-9 포맷 LLR 테이블 파일 로드 | decoder.cpp LLR 테이블 로드 |`.

→ 세 곳(파일 실물 / DONE.md 기록 / plan.md 모듈표)이 서로 다른 이야기를 한다. 조치는 ㉮ 파일 삭제 후 DONE.md·plan.md 정합화, 또는 ㉯ 파일을 살릴 근거가 있다면 `llr/` 프리셋 복구와 TODO 등록 중 하나여야 한다.

### M2 상세 — `llr/` 프리셋이 담던 지식의 행방

삭제된 `llr/README.md`와 프리셋 파일에 있던 내용을 현재 저장소에서 추적한 결과:

| 사라진 내용 | 현재 남아 있는가 |
|-------------|------------------|
| "낮은 dv의 ch는 메시지 최대(7) 미만이어야 CN 하나로도 flip 가능" (`ch6688_th842.txt` 헤더 주석, 2026-08-03 2차 튜닝 그리드의 핵심 발견) | ✓ `_pm/TODO.md:19-21`에 일반화된 형태로 계승: "반전 가능 조건 `ch ≤ 7·dv` (3-bit 기준, EDGE_MAG 최대 7 × 해당 비트의 dv)를 최적화 탐색 범위에 반영" |
| "벤더 참고값 dv=2 ch=10" | ✓ `_pm/TODO.md:21` |
| **원본 decoder.cpp 실값 `CH_HD 21 14 12 10`** (`_hw_orig_ch.txt`, LAYOUT_PRIME_512B_TLC_VSS_OFF 빌드 기준) | ✗ **사라짐.** 저장소 전체 Grep에서 이 값 없음. 현재 `Input/LLR/LLR_MATRIX_HD_1.txt`의 ch는 dv 구간별 `28/10/28/10`으로 전혀 다른 토이 값이고, `TODO.md:21`은 "현 토이 파일의 dv=2 ch=28 위반"만 언급 |
| `EDGE_MAG {7,5,3,1}`이 원본 실값이라는 출처 | △ `docs/차이.md:25`, `README.md:162`에 값은 있으나 "원본 decoder.cpp 실값"이라는 출처 표기는 없음 |
| "TH_HD 원본은 소실 — 전부 추정값" | ✓ `_pm/TODO.md:32` "소실된 HW TH/CH 실값 없이는 추정 튜닝 한계", `plan.md:22` |
| ch/th 조합 7종의 실제 값과 각각의 FER 결과 | ✗ 사라짐. 튜닝을 재개하려면 처음부터 다시 |

**판정**: 핵심 결론(반전 가능 조건, 벤더 참고값, TH 소실)은 TODO에 계승됐다. 그러나 **원본 HW의 CH_HD 실값 {21,14,12,10}은 어디에도 남지 않았다.** 이 값은 `plan.md:104`가 "사용자 공급 필요"라고 적은 바로 그 실값 중 CH 쪽이며, 저장소에 유일하게 남아 있던 사본이었다. 복구는 git 이력(`git show ea88882:2_LDPC_light/llr/_hw_orig_ch.txt`)으로 가능하므로 데이터 손실은 아니지만, 그 사실이 어디에도 기록돼 있지 않다.

## 2-4. 삭제된 파일을 아직 참조하는 문서·코드 (Grep 전수)

| 심각도 | 참조 위치 | 참조 대상 | 상태 |
|--------|-----------|-----------|------|
| H3 | `docs/plan.md:56` | `llr_tables.py` | 사문화 모듈을 현재 모듈 구성표에 열거 |
| H3 | `docs/plan.md:61` | `mpi_runner.py` | 삭제된 파일을 현재 모듈 구성표에 열거 |
| H3 | `docs/plan.md:75` | `examples/fer_curve.py` | 삭제된 파일을 현재 도구표에 열거 |
| H3 | `docs/plan.md:112` | `4. mpi_runner + 슈퍼컴 반입` (진행 순서) | 삭제된 파일 기준 |
| H3 | `docs/plan.md:104` | `llr_tables 템플릿은 공란` | 사문화 모듈 참조 |
| H3 | `docs/plan.md:73-74` | `tools/lifting.py`, `tools/gen_example_code.py` | 실제 경로는 `tools/H_mat_gen/` |
| H3 | `docs/plan.md:131` | `기존 examples/fer_curve.py의 자동 생성 폴백 제거`, `tools/gen_example_code.py` | 결정 이력 절이므로 예외 후보이나 경로가 구식 |
| H4 | `llr_tables.py:1` | `2_LDPC_light/llr/*.txt` | 존재하지 않는 폴더 |
| H1 | `Ideas/vanilla/README.md:13` | `_test/20260806_setup_구성_실험/` | 미추적·비존재 경로 |
| H2 | `tools/H_mat_gen/README.md:16` | `_test/20260806_setup_구성_실험/LDPC_base` | 미추적·비존재 경로 |
| M1 | `README.md:6`, `docs/plan.md:4` | `_test/20260806_setup_구성_실험/` | 이력 서술 안의 참조 (M1/H3와 같은 건) |
| L10 | `_pm/TODO.md:48`, `README.md:19` | `docs/review/` | 존재하기는 하나 **2026-07-30 plan.md 리뷰 기록**이고, 최근 리뷰 기록은 `_pm/done/20260806_review/`와 `_pm/tasks/20260808_review/`에 있다. "리뷰 기록: `docs/review/`"라는 안내를 따르면 최신 리뷰를 찾지 못한다 |

정상 참조로 확인한 것: `select_irregular.py:10,30`의 `irregular_17x144_z256.qc`는 자기 자신의 `out/` 산출물 경로이므로 유실 참조가 아니다.

## 2-5. `select_irregular.py` 구 API 잔존 — 정적 실패 지점 지목

현행 API를 `inspect.signature`로 실측해 대조했다.

| 실행 순서 | `select_irregular.py` 코드 | 현행 `LDPC_base` API | 결과 |
|-----------|---------------------------|---------------------|------|
| import | `from ...LDPC_base.{decoder,channel,sim} import ...`, `from .gen_example_code import build_code` | 전부 존재 | ✓ **import 성공** (실측 확인) |
| `main()` 1단계 | `build_code(Z, M, N, INFO_DEGREES, seed=sd)` (`:55`) | `build_code(z, M, N, info_col_degrees, seed)` | ✓ 일치 |
| `main()` 1단계 | `code.count_cycles4()` (`:57`) | `QCCode.count_cycles4()` 존재 | ✓ 일치 |
| `main()` 2단계 | `fer_at()` → **`MinSumDecoder(code, max_iter=MAX_ITER)`** (`:39`) | **`MinSumDecoder.__init__(self, code, llr_matrix)`** | ✗ **여기서 최초 실패**. `TypeError: unexpected keyword argument 'max_iter'` (동시에 필수 인자 `llr_matrix` 누락) |
| (도달 못 함) | `run_fer_point(…, target_errors=…, batch=…)` (`:43-44`) | `run_fer_point(code, channel_fn, decoder, random_generator, max_frame_errors=…, max_frames=…, frames_per_batch=…, …)` | ✗ `TypeError` — `target_errors`/`batch` 키워드 없음 |
| (도달 못 함) | `chan.bsc_llr(code, zero_cw(b), rber, rg)` (`:42`) | `channel.py`에 `bsc_llr` **없음** (`CHANNELS = {rber, fixed_error, strong_error}`, 반환도 배열이 아닌 dict) | ✗ `AttributeError` (실측: `hasattr(chan,'bsc_llr') == False`) |
| (도달 못 함) | `win_code.save(WINNER_FILE)` (`:110`) | `QCCode.save()` 존재 | ✓ 일치 |
| (도달 못 함) | `r["fps"]`, `r["sec"]`, `r["fer"]`, `r["errors"]`, `r["frames"]` (`:66,79,103,114`) | `run_fer_point` 반환 dict에 전부 존재 | ✓ 일치 |

**최초 실패 지점**: `tools/H_mat_gen/select_irregular.py:39` — 후보 생성(1단계)까지는 진행되고, 2단계 스크리닝 포인트 탐색의 첫 `fer_at()` 호출에서 `TypeError`.

**TODO 정합**: `_pm/TODO.md:22-24`는 이렇게 적고 있다.

```
- [ ] `tools/H_mat_gen/select_irregular.py`를 새 구조(채널 dict, decoder_main, LLR matrix 필수)로 손질
  - 현재 실행 불가 (구 API 기준, import만 LDPC_base로 보정된 상태)
```

→ ㉮ "실행 불가" ✓ ㉯ "구 API 기준" ✓ ㉰ "import만 LDPC_base로 보정된 상태" ✓ ㉱ 손질 방향으로 든 "채널 dict"(`bsc_llr` → `CHANNELS[...]` dict 반환), "decoder_main"(진입 함수 개명), "LLR matrix 필수"(`__init__`의 `llr_matrix` 필수화) 3가지가 위 표의 실패 원인 3건과 정확히 일대일 대응한다. **TODO 서술은 실제 코드 상태와 완전히 일치한다.** 이 항목은 정합 문제 없음.

단, 같은 내용을 담은 `tools/H_mat_gen/README.md:15-17`은 H2에서 지적한 대로 시제와 경로가 틀렸다. TODO는 맞고 README는 틀린 상태다.

## 2-6. 부수 관찰 (팀 D 관점 G와 경계)

| 심각도 | 내용 |
|--------|------|
| L11 | `Input/LLR/LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`가 추적 대상으로 커밋돼 있으나, `config.json`의 `internal_quantize.max_iter`는 120이라 어떤 config도 이 파일을 참조하지 않는다. `README.md:71`의 예시 파일명도 `..._iter120.txt`다. 자동 생성 산출물을 저장소에 남길지 판단 필요 |
| L12 | `gen_example_code.py`의 기본 출력이 `tools/H_mat_gen/out/`(git 무시)로 바뀌었는데, 실험이 읽는 위치는 `Input/H_matrix/`다. README.md:33-37은 생성 명령만 안내하고 `Input/H_matrix/`로 옮기라는 안내가 없다 |
| L10 | `README.md:15`의 `LLR_MATRIX_HD_0.txt=restart 포함 토이, HD_1.txt=restart 없는 20-iter 테스트용` 서술은 실제 파일과 대조한 결과 **정확하다** (HD_0: num_restart=1, restart iter=2, max_iter=5 / HD_1: num_restart=0, iter_end=20). `README.md:106`의 "후순위 로그 7종"도 `TODO.md:27-30`의 7개 항목과 정확히 일치한다 |

---

## 우선 조치 권고 (순서대로)

- 1. **H1, H2** — `Ideas/vanilla/README.md:13`, `tools/H_mat_gen/README.md:15-17`의 `_test/...` 경로와 미래 시제를 현재 상태로 다시 쓴다. 두 곳 모두 규칙 ㉮의 "처음부터 그렇게 설계됐던 것처럼 다시 쓴다"를 적용하면 자연히 해소된다.
- 2. **H4** — `llr_tables.py`의 존폐를 정한다. 삭제한다면 `DONE.md:70`의 기록이 그제서야 사실이 되고 `plan.md:56`도 함께 정리된다.
- 3. **H5** — `llr_tune.py`가 담당하던 파라미터 탐색 절차의 자리를 무엇이 메울지 TODO에 등록한다 (`TODO.md:19-21`의 "LLR matrix 최적화" 항목 아래 서브태스크가 자연스러운 자리로 보인다).
- 4. **H3 / D1** — `docs/plan.md`의 성격을 결정한다 (구조 서술 갱신 vs 결정 이력 전용화). 이것이 정해져야 M1(README.md:6) 처리 방향도 따라 정해진다.
- 5. **D5 / M3** — 줄표·가운뎃점 용법에 대한 프로젝트 규칙을 명문화한 뒤 일괄 처리한다. 144건이므로 규칙 확정 없이 손대면 안 된다.
- 6. **M4** — 용어 대조표 도입 여부를 결정한다.
