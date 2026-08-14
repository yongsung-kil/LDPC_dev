# Round 2 / 팀 C (refactor_exec) 종합

작성: 2026-08-08 14:43:49 | 대상 커밋: e6282b1 (+ 미커밋 `2_LDPC_light/config.json`)
배정 관점: D(단계 함수 추출 동작 보존) + E(패키지 경계, 임포트) + I(실행 검증)

워커 3개를 정적 2 + 동적 1로 나눠 발사했다.

| 워커 | 담당 | 보고서 | 발견 |
|------|------|--------|------|
| C1 | 정적: 단계 함수 추출 동작 보존 (관점 D) | `worker_c_1.md` | 7건 (MEDIUM 2, LOW 5) + 타팀 이관 1 |
| C2 | 정적: 패키지 경계, 임포트 체인 (관점 E) | `worker_c_2.md` | 9건 (MEDIUM 3, LOW 6) |
| C3 | 동적: 실행 검증 6종 + 성능 실측 (관점 I) | `worker_c_3.md` | 7건 (MEDIUM 3, LOW 4) |

**총 23건. CRITICAL 0, HIGH 0, MEDIUM 8, LOW 15.** 별도로 타팀 이관 1건.

---

## 1. 워커 결과 요약

### C1 (관점 D): 동작 보존은 3중 근거로 확인됨

리팩토링 동작 보존 자체는 문제가 없다. 근거를 세 갈래로 확보했다.

- ㉮ **산출물 바이트 대조**: 단계 함수 추출 이전 커밋(e3ee25a, 08-07 13:35)에 실행된
  `Sim_Output/260807_142334_fixed_error/`의 로그 CSV 6종과, 같은 파라미터로 HEAD에서
  재실행한 결과가 전부 IDENTICAL
- ㉯ **독립 평면 참조 구현 대조**: 단계 함수 분해 없이 하나의 루프로 다시 쓴 참조 구현과
  8개 조건에서 전 출력 키가 배열 단위로 일치. 성공과 실패가 섞이는 조건을 포함해 배치 압축
  경로를 덮음
- ㉰ **문장 단위 대조**: 누락된 갱신, 순서가 바뀐 갱신, 조건이 달라진 분기 없음

배정 확인 항목은 전부 통과했다. `_DecodeState` 어노테이션 30개와 실제 할당 30개의 차집합이
양방향 공집합, 배치 압축 대상 8개가 프레임축 생존 배열 전부(압축 29회 전수 계측),
`final_*` 3종의 "마지막 처리 iteration 값" 의미가 성공, 실패, 조기 종료 전 경로에서 성립,
`_build_result`와 `sim.py` 키 집합 불일치 0건, **log 부분집합 16개 조합 전수 실행에서
KeyError 0건**이다.

발견은 동작 보존 밖에서 나왔다. 핵심은 F1(`_column_order` 재정의 시 성공 오판정)과
F7(저장소의 회귀 근거가 배치 압축 경로를 밟지 않음)이다.

### C2 (관점 E): 실행 루트가 둘이고 그 오류가 침묵으로 흡수됨

핵심 3건이 모두 "루트가 둘"이라는 한 뿌리에서 나온다.

- ㉮ C2-1: `Ideas` 임포트 실패가 아무 출력 없이 `MinSumDecoder` 대체로 끝난다
- ㉯ C2-2: `2_LDPC_light/`(flat)와 저장소 루트(package) 두 루트가 서로 배타적이며,
  겹치면 `LDPC_base.decoder`가 두 벌 적재된다 (`is` 비교 False를 실측)
- ㉰ C2-3: matplotlib이 없으면 완주한 실험의 `summary.txt`가 통째로 사라진다

**Round 1 가설 하나를 코드 근거로 정정했다.** agent_1 P6 ㉯와 agent_2 P7 ㉰이 지목한
"`Ideas.vanilla.decoder` 내부 import 실패까지 삼켜 오진"은 실재하지 않는다. 그 import는
`try` 블록 밖(`run.py:278`)이라 그대로 전파된다. 실제 오진 지점은 한 단계 위인
`Ideas/__init__.py`와 `Ideas/registry.py`이며, C2가 가짜 트리 3벌로 실증했다.

문제 없던 항목 중 셋은 Round 1이 의심했던 것을 해소했다. **저장소 루트에서
`python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code`가 정상 동작하고**(숫자로 시작하는
패키지명이 runpy에서 제약이 되지 않음), `__init__.py` 3개가 실재해 3단계 상대 import가
성립하며, `LDPC_base/__init__.py`가 `run`을 뺀 것은 순환 import 때문이 아니다(실측).

### C3 (관점 I): 실행 6종 전부 완주, 왕복 무손실

- ㉮ ① 파일 경로 config 완주 (10.5초, 산출물 9종 전부 생성)
- ㉯ ② 균일 양자화 경로 완주. `num_bits/channel_llr/max_iter/mode` 4개가 실제 적용됨을
  요약과 생성 파일 내용으로 확인
- ㉰ ③ **round-trip FER 완전 동일**. 같은 seed와 조건에서 FER, BER, avg_iter가 4개 포인트
  모두 일치하고 로그 CSV 12개 diff가 전부 SAME, PNG는 md5까지 같다
- ㉱ ④ registry 경유 확인(`Ideas.vanilla.decoder.VanillaDecoder`). 상대경로는 cwd가 아니라
  **config 파일 위치 기준**임을 cwd를 바꿔 실측
- ㉲ ⑤ 커밋된 uniform 파일이 재생성본과 **md5 일치**(`6267445e...`)
- ㉳ ⑥ 오류 4갈래 모두 원인을 짚는 메시지(등록 이름 목록, 허용 키 목록, 해석된 절대경로)

성능은 th 개수만이 비용을 가른다. 파일 경로 3-bit와 uniform 3-bit의 프레임x iteration 당
비용이 3.75ms 대 3.59ms로 사실상 같다.

---

## 2. 팀 내 교차 분석

### 교차 1. 세 워커가 같은 뿌리를 다른 각도에서 짚었다: 교체 지점 계약의 미명시

C1-F1, C1-F5, C2-C2-5가 서로 독립으로 나왔으나 한 뿌리다. **교체 지점 표가 실제 시그니처로
가능한 것보다 넓게 커버를 주장한다.**

| 워커 | 표의 주장 | 실제 제약 |
|------|-----------|-----------|
| C1-F1 | `_column_order`가 informed dynamic scheduling을 커버 | 에러 집계가 column 루프 **안**이라, 전 column을 정확히 한 번씩 방문하지 않으면 성공을 오판정 |
| C1-F5 | `_vnu_quantize`가 damping, `_vn_decide`가 진동 억제를 커버 | 두 함수 모두 iteration 번호도 직전 값도 받지 않아 구현 불가 |
| C2-C2-5 | "교체용 함수만 재정의" | 생성자 `(code, llr_matrix)` 유지가 암묵 전제이고 `issubclass` 검증도 없음 |

이 저장소의 목적이 **논문 아이디어 스크리닝**(루트 CLAUDE.md 프로젝트 간 흐름 ㉱)이므로,
"이 논문은 교체 지점 하나로 이식 가능"이라는 판정의 정확도가 곧 프로젝트의 산출물이다.
표를 믿고 판정한 논문이 막상 그 지점으로 구현되지 않거나(F5), 구현되더라도 조용히 낙관적인
FER을 내는(F1) 것은 세 건을 따로 볼 때보다 무겁다.

**팀 판정**: 세 건을 묶어 하나의 수리 대상으로 올린다. 현 상태 심각도는 MEDIUM이되,
스케줄 계열이나 damping 계열 아이디어가 하나라도 들어오는 시점에 HIGH가 된다.
C1의 F1 실측이 근거다 (마지막 column 하나를 건너뛰게 하면 29프레임이 성공으로 보고되고
그중 27프레임에 실제 에러가 남아 있으며 `final_err_bits`는 전부 0).

### 교차 2. C1-F7과 C3-③은 모순이 아니라 상보다

겉으로는 어긋나 보인다. C1-F7은 "저장소에 남은 회귀 근거가 배치 압축 경로를 한 번도 밟지
않는다"고 하고, C3-③은 "round-trip이 로그 CSV까지 완전 동일"이라고 한다.

코드와 실행 근거로 가르면 둘 다 맞다.

- ㉮ C3-①(파일 경로, `LLR_MATRIX_HD_1.txt`)은 두 포인트 모두 FER=1.0 [64/64]다.
  전 프레임 실패면 `keep`이 전부 True라 압축이 배열 길이를 바꾸지 않는다. C1-F7이 가리키는
  그 조합이다
- ㉯ C3-②③(균일 6-bit, fixed_error 300)은 FER=0, `avg_decode_success_iteration=7.47`이다.
  프레임이 서로 다른 iteration에 빠져나가므로 압축이 실제로 일어난다

**팀 판정**: 배치 압축 경로는 **균일 모드의 낮은 에러 포인트에서만** 밟힌다. 파일 매트릭스
경로(= 저장소 기본 config)로는 밟히지 않는다. C1-F7의 제안(성공과 실패가 섞이는 조건을
회귀 시나리오로 고정)이 유효하며, C3-②의 조건(uniform 6-bit, fixed_error 300)이 이미
그 역할을 하고 있으므로 그것을 고정 시나리오로 채택하면 된다.

### 교차 3. C2-1과 C3-④의 판정 차이는 관측 차이가 아니라 완화 요인의 유무다

C3-④는 `Ideas` 미존재 fallback을 "문서대로, 정상"으로, C2-1은 같은 동작을 MEDIUM으로 봤다.
관측된 동작은 동일하다(`_resolve_decoder_class('vanilla')` → `MinSumDecoder`, 무경고).
차이는 C2가 저장소 루트 실행이라는 **의도치 않은 발동 경로**를 추가로 찾은 데 있다.

여기에 C3의 실행 출력이 완화 요인 하나를 준다. `summary.txt`와 콘솔이 실제로 쓰인 클래스를
전체 모듈 경로로 찍는다.

```
정상 루트 : decoder: vanilla (Ideas.vanilla.decoder.VanillaDecoder), max_iter=20
repo 루트 : decoder: vanilla (2_LDPC_light.LDPC_base.decoder.MinSumDecoder), max_iter=20
```

**팀 판정**: MEDIUM 유지. 대체 사실이 기록에는 남으므로 사후 추적은 가능하다. 다만 실행
시점에 경고가 없어 사용자가 그 줄을 읽어야만 알아챈다. C2의 수리 방향(`err.name == "Ideas"`
확인 + 대체 시 콘솔 한 줄)이 그대로 적절하다.

### 교차 4. 저장소 오염 경로는 `Input/LLR/` 하나로 좁혀졌다

C2와 C3이 `.gitignore` 커버 범위를 서로 다른 방향에서 확인했고 결과가 맞물린다.

- ㉮ C2: `Sim_Output/`은 앞에 슬래시가 없어 모든 깊이에 적용된다. `Ideas/vanilla/Sim_Output/`에
  실행 결과 6벌이 있어도 `git status`가 깨끗함을 확인
- ㉯ C2: `tools/H_mat_gen/out/`도 `out/` 규칙이 덮는다
- ㉰ C3: `git check-ignore -v`로 `Input/LLR/foo.txt`가 **무시되지 않음**을 확인

여기에 C3-6(2SD 모드가 파일을 쓴 뒤에야 HD 전용 검사에 걸림)이 겹치면, 쓸 수 없는 고아
파일이 추적 디렉터리에 남는다. **C3-1과 C3-6은 한 묶음으로 수리하는 것이 맞다**
(생성 위치를 무시 대상으로 옮기거나 `Input/LLR/*uniform*`을 `.gitignore`에 넣으면 둘 다 닫힌다).

### 교차 5. 두 워커가 독립으로 같은 데이터 정합 문제에 도달했다 (타팀 이관)

C1(실측 중 부수 발견)과 C3-①(기본 config 실행)이 각각 저장소 기본 config가 FER=1.0을 내는
것을 관측했다. C1이 원인까지 추적했다.

- ㉮ `LLR_MATRIX_HD_1.txt`와 `HD_0.txt`의 dv 구간은 `[11, 4, 3, 2]`인데, 예제 H-matrix
  `example_18x147_z256.qc`의 column degree는 `{2:17, 3:1, 4:129}`다. dv=11 구간은 쓰이지 않는다
- ㉯ 두 파일의 row 2줄은 dv=11 구간의 ch 값만 다르므로, 이 부호에서는 iteration 1과 2~20의
  테이블이 사실상 같아진다
- ㉰ 결과로 에러 50비트에서도 32프레임 전량 실패한다. 손으로 만든 평범한 매트릭스로는
  300비트를 32/32 정정하므로 디코더 결함이 아니라 데이터와 부호의 정합 문제다
- ㉱ 균일 6-bit 경로는 fixed_error 300에서 FER=0이 나온다 (C3-②). 같은 부호, 같은 seed다

**팀 판정**: 디코더 로직 문제가 아니므로 팀 C의 발견 목록에서 빼고 **팀 D(관점 G, 데이터
무결성)와 팀 B(관점 C, config)로 이관한다.** 신규 사용자가 저장소를 pull해 기본 config로
처음 실행하면 FER=1.0을 본다는 점에서 영향이 작지 않다.

### 교차 6. 심각도 등급 적용에 판단이 갈리는 지점 하나 (Round 3 조정 요청)

C2-3(matplotlib 미설치 시 `summary.txt` 유실)은 팀 리더 기준으로 등급 경계에 있다.

- ㉮ 등급 정의의 문자 그대로 보면 "프로세스 중단"이라 CRITICAL에 걸린다 (exit code 1로 죽음)
- ㉯ 실제 손실 범위를 보면 FER 수치는 CSV로 남고, 사라지는 것은 재현성 정보(git 커밋 해시,
  부호 정보, LLR matrix 정보, 디코더 정보)다. 비가역 손상이라기보다 복구가 번거로운 수준

**팀 판정**: MEDIUM으로 두되 **팀 C MEDIUM 8건 중 수리 우선순위 1위**로 올린다.
근거는 이 저장소의 목적이 "외부에서 pull하여 성능을 확인"(루트 CLAUDE.md 프로젝트 간 흐름 ㉰)인데
`requirements.txt`, `pyproject.toml`, `setup.py`가 하나도 없고 두 config 모두
`fer_curve_png: true`가 기본값이라, 새 환경의 첫 실행이 정확히 이 경로를 탄다는 점이다.
등급 재판정은 Round 3에 맡긴다.

---

## 3. 발견 목록

CRITICAL 0건, HIGH 0건.

### MEDIUM (8건)

| ID | 문제 | 위치 | 근거 |
|----|------|------|------|
| C2-3 | matplotlib 미설치 시 완주한 실험의 `summary.txt`가 저장되지 않고 exit 1 (그림 저장이 summary 쓰기보다 앞) | `LDPC_base/run.py:496`, `run.py:561-566` | 가짜 matplotlib으로 재현. CSV만 남고 summary.txt 없음. 의존성 선언 파일이 저장소에 없음 |
| C1-F1 | `_column_order` 재정의 시 성공을 오판정 (에러 집계가 column 루프 안에 있어 방문 스케줄에 종속) | `LDPC_base/decoder.py:258-259`, `:283-288`, `:126-128`, `:53` | 마지막 column 하나를 건너뛰게 하면 29프레임 성공 보고 중 27프레임에 실제 에러 잔존, `final_err_bits`는 전부 0 |
| C2-1 | `Ideas` 임포트 실패가 무경고로 `MinSumDecoder` 대체. 저장소 루트 실행에서도 발동 | `LDPC_base/run.py:265-272` | 가짜 트리 3벌 실증. 오진 지점은 `Ideas/__init__.py`와 `Ideas/registry.py` (`Ideas.vanilla.decoder`는 `try` 밖이라 정상 전파) |
| C2-2 | 실행 루트 두 갈래가 배타적이고, 겹치면 `LDPC_base.decoder`가 두 벌 적재 | `Ideas/vanilla/decoder.py:6` 대 `tools/H_mat_gen/gen_example_code.py:15`, `select_irregular.py:23-25` | repo 루트 + `PYTHONPATH` 조합에서 `VanillaDecoder.__mro__[1] is run.MinSumDecoder` → False, `sys.modules`에 `decoder` 두 벌 |
| C3-1 | `use_input_llr_matrix: false`가 기본값으로 추적 디렉터리 `Input/LLR/`에 파일을 쓴다. `save()`가 텍스트 모드라 줄바꿈이 플랫폼 종속 | `LDPC_base/run.py:206-215`, `:300-303` | `git check-ignore -v`로 미무시 확인. 커밋된 uniform 파일이 그 산출물. `.gitattributes` 없음 |
| C3-2 | false 분기에서 `decoder.llr_matrix` 키맵 검사 누락. 같은 오타가 토글 값에 따라 잡히기도 안 잡히기도 함 | `LDPC_base/run.py:187-208` | `{"dir","flie"}`가 조용히 통과하고 완주. true 분기는 `ValueError` |
| C3-3 | `LLRMatrix.save()`가 floor flag를 항상 `-1`로 덮어씀 (`__init__`이 보관하지 않음) | `LDPC_base/llr_matrix.py:254-256`, `:86-92` | floor=1 파일로 왕복시켜 손실 실측. DAO 포맷 무변경 요구를 조용히 깰 수 있음 |
| C1-F7 | 저장소에 남은 회귀 근거가 배치 압축 경로를 한 번도 밟지 않음 (검증 커버리지) | `2_LDPC_light/config.json`, `Sim_Output/` 실행 기록 8건 | 파일 매트릭스 실행 8건이 전부 FER=1.0 [64/64]. C3-①이 재확인 |

### LOW (15건)

| ID | 문제 | 위치 |
|----|------|------|
| C1-F5 | 교체 지점 표가 damping과 진동 억제를 커버한다고 적었으나 두 함수가 iteration 정보를 받지 않음 | `decoder.py:50-51` 대 `:139`, `:144` |
| C2-5 | 등록 클래스의 생성자 계약 `(code, llr_matrix)`가 문서에 없고 `issubclass` 검증도 없음 | `run.py:306`, `Ideas/registry.py:3-8` |
| C1-F3 | `_cnu_update`만 전체 배열을 받아 in-place로 고치는 비대칭 (반환형으로 재정의하면 예외 없이 무동작) | `decoder.py:165-186` 대 `:130-137` |
| C1-F4 | `_record_iteration`이 `_check_errors`보다 먼저여야 한다는 제약이 코드에 없음 (어기면 `ValueError`, 조용한 오답은 아님) | `decoder.py:382-387`, `:310`, `:327` |
| C1-F2 | `cur_th` 축 주석이 th 개수 3 고정으로 남음 (균일 6-bit 실측 shape은 `(64, 1, 31)`) | `decoder.py:256` |
| C1-F6 | `final_csw`와 `final_err_bits`의 측정 시점이 다른데 같은 CSV 행에 놓임 | `decoder.py:261`, `:283-286`, `:304-313`, `run.py:429-455` |
| C2-4 | registry 문자열 형식 오류의 예외가 원인을 지목하지 못함 (Windows 경로 혼입 시 3조각) | `run.py:277` |
| C2-6 | `Ideas/vanilla/README.md`와 `tools/H_mat_gen/README.md`가 gitignore된 `_test/...`를 실행 루트로 안내 | `Ideas/vanilla/README.md:13`, `tools/H_mat_gen/README.md:16-17` |
| C2-7 | `select_irregular.py`가 구 API로 실행 중반에 멈춤 (39행이 최초 실패, TODO와 정합) | `tools/H_mat_gen/select_irregular.py:39, 42-44` |
| C2-8 | 참조되지 않는 `llr_tables.py`가 추적 중이라 LLR 파라미터 정본이 둘로 읽힘 | `2_LDPC_light/llr_tables.py` |
| C2-9 | 잘못된 위치에서 실행했을 때의 에러가 조치를 안내하지 않음 | `run.py:571-585` |
| C3-4 | LLR matrix 파일 부재가 raw `FileNotFoundError` (H-matrix는 안내문 있음) | `run.py:287-288` 대 `llr_matrix.py:171` |
| C3-5 | 오류 메시지의 줄표(`—`)가 cp949 콘솔에서 `—` 이스케이프로 깨짐. 프로젝트 문장 규칙과도 충돌 | `run.py`(40곳), `llr_matrix.py`(13곳), `decoder.py`(25곳) |
| C3-6 | 2SD/3SD 모드가 파일을 쓴 뒤에야 HD 전용 검사에 걸려 고아 파일이 남음 | `run.py:293-303` 대 `decoder.py:372` |
| C3-7 | `internal_quantize.num_bits` 상한 없음 (12-bit면 64프레임 배치가 약 8분으로 추산) | `run.py:195-197`, `decoder.py:156-157` |

### 타팀 이관 (1건)

| 문제 | 위치 | 이관처 |
|------|------|--------|
| `LLR_MATRIX_HD_0/1.txt`의 dv 구간 `[11,4,3,2]`가 예제 H-matrix의 column degree `{2,3,4}`와 어긋나 기본 config가 FER=1.0을 냄 | `Input/LLR/LLR_MATRIX_HD_0.txt`, `HD_1.txt`, `Input/H_matrix/example_18x147_z256.qc`, `config.json` | 팀 D(관점 G) + 팀 B(관점 C) |

---

## 4. 성능 실측 (참고)

`_vnu_quantize`의 파이썬 루프가 th 개수(`2^(num_bits-1)-1`)만큼 돈다. 같은 조건
(64프레임 1배치, 전 프레임 실패, 30 iteration 고정, 로그 끔)으로 측정했다.

| 경로 | th 개수 | 실행 시간 | 프레임x iteration 당 | 배수 |
|------|---------|-----------|----------------------|------|
| uniform 3-bit | 3 | 6.9 s | 3.59 ms | 1.00x |
| uniform 6-bit | 31 | 13.6 s | 7.08 ms | 1.97x |
| uniform 8-bit | 127 | 39.4 s | 20.52 ms | 5.72x |
| DAO 파일 3-bit | 3 | 4.8 s | 3.75 ms | 1.05x |

함수 단독은 93us(th 3) → 492us(th 31) → 1872us(th 127) → 28.35ms(th 2047, 12-bit)다.
이 부호는 base edge 553개라 30 iteration 배치의 호출이 16,590회이며, `_vnu_quantize`가
차지하는 몫이 3-bit 약 22%에서 8-bit 약 79%로 커진다.

**해석**: 파일이냐 생성이냐는 비용에 영향이 없고 th 개수만이 비용을 가른다. 스크리닝
용도로 num_bits 8까지는 실용 범위이며, 그 위는 `np.searchsorted`로 루프를 없애는 것이
수리 방향이다 (C3-7).

---

## 5. 미커버 영역

팀 C 범위 안에서 이번 라운드가 닿지 못한 것을 적는다.

- ㉮ **`needs_csw`가 False인데도 `prev_csw`를 매 iteration 계산하는 비용**(agent_2 P13 ㉱).
  세 워커 모두 정량화하지 않았다. `_vnu_quantize`가 지배적이라는 C3 실측을 보면 몫이 작을
  가능성이 높으나 측정 근거는 없다
- ㉯ **메모리 스케일**(agent_2 P13 ㉲, ㉰). `frames_per_batch` 기본 128과 `(B, M_b, z)` 버퍼
  5개, `row_values` 크기 `(R, num_dv, num_param)`가 num_bits에 따라 커지는 범위를 재지 않았다.
  시간 비용만 측정했다
- ㉰ **`cur_th` fancy indexing의 매 iteration 복사 여부**(agent_2 P13 ㉯). C1이 "매 iteration
  새 객체가 만들어진다"를 확인했으나 그것이 비용에서 차지하는 몫은 재지 않았다
- ㉱ **`select_irregular.py`의 실행 완주**. C2가 최초 실패 지점(39행)까지만 확인했고 그 뒤의
  구 API 잔재가 더 있는지는 정적 대조로만 봤다
- ㉲ **아이디어 서브클래스가 `decoder_main` 전체를 재정의하는 경로**. 교체 지점 6개는 전수로
  봤으나, 전체 재정의가 허용된다는 서술(`decoder.py:45`)에 따른 계약(무엇을 반환해야 하는가,
  어떤 state 불변식을 지켜야 하는가)은 검증하지 않았다
- ㉳ **다중 프로세스, MPI 경로**. `mpi_runner.py`가 삭제되어 대상이 없다 (팀 D의 P12 범위)

타팀 범위와 겹치나 팀 C 실행 중 근거가 나온 것은 다음 두 갈래다.

- 1. C3-3(floor flag 소실)은 팀 A(관점 A, save/load 왕복)와 겹친다. 팀 A의 정적 분석과
     대조해 중복이면 하나로 합치면 된다
- 2. C3-2(false 분기 키맵 미검사)는 팀 B(관점 C, config 검증)와 겹친다. 같은 판정이면 합치고,
     팀 B가 더 넓은 맥락을 잡았으면 그쪽을 정본으로 삼는다

---

## 6. 저장소 오염 확인

세 워커 모두 실행 후 `git status --short`가 세션 시작 시점과 동일함을 확인했다.

```
 M 2_LDPC_light/_pm/TODO.md
 M 2_LDPC_light/config.json
?? 2_LDPC_light/_pm/tasks/
```

세 항목 모두 리뷰 시작 전부터 있던 것이다(`config.json`은 리뷰 대상 미커밋 변경,
나머지 둘은 리뷰 프로세스 산출물). 실험 산출물, 생성 LLR matrix, 가짜 패키지 트리,
H-matrix 생성물은 전부 scratchpad에 두었다. `Input/LLR/`의 파일 3개는 갱신 시각까지
그대로이고, 저장소 `Sim_Output/`과 `Ideas/vanilla/Sim_Output/`에도 새 실행 폴더가 생기지
않았다. 저장소 안에 새로 생긴 것은 gitignore 대상인 `__pycache__/`의 `.pyc`뿐이다.
