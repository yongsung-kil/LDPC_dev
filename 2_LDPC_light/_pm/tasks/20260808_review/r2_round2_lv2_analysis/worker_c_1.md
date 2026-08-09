# worker_c_1 — 정적 분석: 단계별 함수 추출 리팩토링의 동작 보존

## 확인 범위

- ㉮ 코드 전문 읽기: `LDPC_base/decoder.py`(388줄 전체), `LDPC_base/sim.py`(117줄 전체),
  `LDPC_base/run.py`(586줄 전체), `Ideas/vanilla/decoder.py`, `Ideas/registry.py`.
  보조로 `LDPC_base/llr_matrix.py`, `pcm.py`, `channel.py`
- ㉯ git 대조: `git show ea88882:2_LDPC_light/decoder.py`(구 `decode_batch` /
  `_decode_column_wise`), `git log --all -S decoder_main`, `_pm/done/20260807_가독성리팩토링/`,
  `_pm/DONE.md`
- ㉰ 산출물 대조: `Sim_Output/`과 `Ideas/vanilla/Sim_Output/`에 남은 실행 기록 10건의
  summary와 로그 CSV (커밋 해시가 박혀 있어 리팩토링 전후 시점 구분 가능)
- ㉱ 실측(전부 scratchpad에서 실행, 저장소 추적 파일 무수정):
  - 1. 계측 서브클래스로 `_DecodeState` 속성 전수 추적, 압축 후 shape 정합 전수 확인
  - 2. `log` 항목 16개 조합 전수로 `_build_result` 키 집합 대 `sim.py` 접근 키 집합 대조
  - 3. HEAD에서 구 config(`LLR_MATRIX_HD_1.txt`, fixed_error 200/300, seed 0)를 재실행해
       리팩토링 전(커밋 e3ee25a) 로그 CSV와 바이트 단위 대조
  - 4. 독립 평면(flat) 참조 구현을 새로 작성해 단계 함수 분해본과 전 출력 키 배열 단위 대조
       (파일 매트릭스 2종, 균일 6-bit, 합성 restart 매트릭스, 합성 CSW 그룹 매트릭스)

---

## 핵심 결론 (관점 D: 동작 보존)

**단계 함수 추출로 인한 동작 변화는 발견되지 않았다.** 근거 세 가지.

- ㉮ **리팩토링 전후 실행 산출물이 바이트 단위로 같다.**
  커밋 e3ee25a(2026-08-07 13:35, 단계 함수 추출 이전. 추출 완료 기록은 14:49 c97c6ed)에
  실행된 `Sim_Output/260807_142334_fixed_error/`의 로그 CSV 6종과, 같은 파라미터로 HEAD에서
  재실행한 결과가 전부 `IDENTICAL`이다.
  대상: `log_iter_*`(iteration별 csw_mean, bit_err_mean, dv별 bit_err_mean),
  `log_fail_*`(프레임별 잔여 에러, 최종 CSW, dv별 분해), `log_iter_hist_*`.
  같은 파라미터의 `Ideas/vanilla/Sim_Output/260807_142326`(추출 전) 대
  `260807_152821`(추출 후) 쌍도 `IDENTICAL`이다.
- ㉯ **독립 평면 참조 구현과 전 출력이 일치한다.**
  모듈 docstring의 알고리즘 서술과 ea88882의 `_decode_column_wise` 구조를 근거로, 단계 함수
  분해 없이 하나의 루프로 다시 쓴 참조 구현을 만들어 대조했다. 8개 조건 전부에서
  `success`, `decode_success_iteration`, `final_err_bits`, `final_csw`, `final_err_by_dv`,
  `log_active`, `log_csw_sum`, `log_err_sum`, `log_err_by_dv_sum`, `profile`이 배열 단위로 같다.
  조건: 파일 매트릭스 HD_1(200/300 에러), HD_0(200), 균일 6-bit(300/355/365/375/420 에러),
  합성 restart 매트릭스(50/200/300), 합성 CSW 그룹 매트릭스(200/300).
  성공과 실패가 섞인 조건(예: 365비트에서 25/48 성공)을 포함하므로 배치 압축 경로도 덮었다.
- ㉰ **문장 단위 대조**로 `_cnu_update`, `_c2v_reconstruct`, `_vnu_quantize`, 배치 압축,
  genie 집계의 갱신 순서와 조건 분기를 구 `_decode_column_wise`와 맞춰 읽었다. 누락된 갱신,
  순서가 바뀐 갱신, 조건이 달라진 분기는 없다.

**단, 대조 근거의 한계를 하나 밝힌다.** 리팩토링 직전 코드(syndrome-aided 평면 `decoder_main`)는
미추적 `_test/` 아래에 있었고 지금은 삭제되어 git에 없다. `git show ea88882:2_LDPC_light/decoder.py`가
주는 것은 syndrome-aided 이전 세대(`decode_batch` / `_decode_column_wise`)라 직접 대조 대상이
아니다. 그래서 위 ㉮(산출물 바이트 대조)와 ㉯(독립 재구현 대조)로 대체했다.

---

## 발견 목록

### F1 (MEDIUM) `_column_order` 교체 지점이 genie 에러 검사와 얽혀 있어 성공 오판정을 낳는다

- **위치**: `LDPC_base/decoder.py:258-259`(column 루프), `:283-288`(에러 집계),
  `:126-128`(`_column_order` 정의), `:53`(교체 지점 표)
- **근거**: 프레임 에러 판정(`state.frame_err`)과 잔여 에러 집계(`state.err_bits`)가
  column 루프 **안에서** 누적된다. 따라서 두 값은 "이 프레임의 에러 비트 수"가 아니라
  "이번 iteration에 방문한 column들에서 관찰된 에러 비트 수"다. 전 column을 정확히 한 번씩
  방문하는 기본 `_column_order`에서는 두 뜻이 같지만, 방문 횟수가 달라지면 갈라진다.
- **실측**: 균일 6-bit 매트릭스, fixed_error 300비트, 32프레임 기준
  - 1. `_column_order`가 마지막 column 하나를 건너뛰도록 재정의: 29프레임이 성공으로 보고되고,
       그중 **27프레임이 건너뛴 column에 실제 에러 비트를 그대로 남기고 있다**
       (남은 에러 1~4비트). 디코더가 보고한 `final_err_bits`는 전부 0이다.
  - 2. 전 column을 두 번씩 방문하도록 재정의: iteration 1의 `log_err_sum`이 151216에서
       178633로 바뀐다 (방문 횟수만큼 중복 계수).
- **영향**: 모듈 docstring 표(`:53`)는 `_column_order`가 "layered / informed dynamic
  scheduling"을 커버한다고 적어 두었다. informed dynamic scheduling 계열은 column 방문
  순서를 바꾸고 일부를 건너뛰거나 되풀이하는 것이 본질이므로, 표를 믿고 이 교체 지점만
  재정의한 아이디어는 **예외 없이 FER을 낙관적으로 틀리게 낸다**. 정본 디코더 자체는
  정상이라 MEDIUM으로 두지만, 스케줄 계열 아이디어가 하나라도 들어오는 순간 HIGH가 된다.
- **제안**: 에러 검사를 column 루프에서 떼어내 iteration 종료 시점에 전 column을 한 번
  훑는 형태로 분리하거나(방문 스케줄과 무관해짐), 표에서 스케줄 계열의 커버 범위를
  "전 column을 정확히 한 번씩 방문하는 순서 변경"으로 좁혀 적는다.

### F2 (LOW) `cur_th` 축 주석이 th 개수 3 고정으로 남아 있다

- **위치**: `LDPC_base/decoder.py:256`
  `state.cur_th = self.llr_matrix.row_th[table_row_idx]   # (num_active_frames, num_dv, 3)`
- **근거**: `LLRMatrix.row_th`의 마지막 축은 `th_len`이고, `th_len`은 `num_param - ch_len`으로
  매트릭스마다 다르다. 균일 6-bit 매트릭스(`LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`)에서
  실측 shape은 `(64, 1, 31)`이다.
- **영향**: 동작에는 영향이 없다. 캐스케이드 일반화(커밋 01251f5) 이후 이 주석만 이전 전제를
  남긴 것이라, 코드를 읽는 사람이 th 개수를 3으로 오해한다.
- **제안**: `# (num_active_frames, num_dv, th 개수)`로 고친다.

### F3 (LOW) `_cnu_update`만 전체 배열을 받아 in-place로 고치는 비대칭

- **위치**: `LDPC_base/decoder.py:165-186`(`_cnu_update`) 대 `:130-137`(`_c2v_reconstruct`)
- **근거**: `_c2v_reconstruct`는 이미 잘라 놓은 row 슬라이스(`min1_row` 등)를 받아 **값을 반환**한다.
  `_cnu_update`는 잘리지 않은 `(B, M_b, z)` 전체 배열과 `row_blk` 정수를 받아 **직접 고친다**.
  두 함수가 `state`를 받지 않는다는 계약 자체는 지켜져 있어서, 아이디어 서브클래스가
  `_DecodeState` 내부를 알 필요는 없다.
- **영향**: 재정의할 때 `_c2v_reconstruct`의 형태를 따라 "새 배열을 만들어 반환"하면 CN 상태가
  갱신되지 않은 채 **예외 없이** 디코딩이 진행된다 (반환값을 아무도 받지 않는다). 슬라이싱
  규약(`[:, row_blk, :]`와 `[:, edge, :]`)도 재정의하는 쪽이 직접 재현해야 한다.
- **제안**: docstring에 "반환값을 쓰지 않는다, 인자 배열을 직접 고쳐야 한다"를 한 줄 명시하거나,
  `_c2v_reconstruct`처럼 row 슬라이스를 받아 갱신된 5개 값을 반환하는 형태로 맞춘다.

### F4 (LOW) `_record_iteration`이 `_check_errors`보다 먼저 와야 한다는 제약이 코드에 드러나지 않는다

- **위치**: `LDPC_base/decoder.py:382-387`(호출 순서), `:310`(`final_err_bits[idx_active] = err_bits`),
  `:327`(`idx_active = idx_active[keep]`)
- **근거**: `_record_iteration`은 `state.idx_active`가 **압축 전** 인덱스(길이 =
  `num_active_frames`)라는 전제로 `final_err_bits`, `final_csw`, `final_err_by_dv`에
  써 넣는다. `_check_errors`가 먼저 돌면 `idx_active`가 짧아진다. 두 함수의 docstring에도,
  `_DecodeState`의 주석에도 이 선후 관계는 적혀 있지 않다.
- **실측**: 순서를 뒤집은 서브클래스로 재현했다. 압축이 실제로 일어나는 iteration에서
  `ValueError: shape mismatch: value array of shape (64,) could not be broadcast to
  indexing result of shape (62,)`로 즉시 실패한다. 조용히 틀린 값을 내지는 않는다.
  전 프레임이 실패해 압축이 한 번도 없는 경우(파일 매트릭스 기본 config가 이 경우다)에는
  결과가 같다.
- **영향**: 조용한 오답 경로가 아니므로 LOW. 다만 `decoder_main` 전체 재정의가 허용되어
  있으므로(`:45`), 재정의하는 쪽이 순서를 알 수 있어야 한다.
- **제안**: `_record_iteration` docstring에 "`_check_errors`(배치 압축)보다 먼저 호출한다"를
  한 줄 넣는다.

### F5 (LOW) 교체 지점 표의 커버 주장과 함수 시그니처가 어긋난다

- **위치**: `LDPC_base/decoder.py:50`(`_vnu_quantize` 커버에 damping),
  `:51`(`_vn_decide` 커버에 진동 억제) 대 `:139`, `:144`의 시그니처
- **근거**: `_vn_decide(self, sum_t)`와 `_vnu_quantize(self, raw, vnu_in, th)`는 iteration
  번호도, 직전 iteration의 값도 받지 않는다. damping은 직전 VNU 출력이, 진동 억제는 직전
  판정 이력이 있어야 성립한다.
- **영향**: 표를 근거로 이식 가능하다고 판정한 논문이 막상 그 교체 지점으로는 구현되지 않는다
  (`decoder_main` 전체 재정의로 넘어가야 한다). 스크리닝 판정의 정확도 문제다.
- **제안**: 두 항목의 커버 범위를 현재 시그니처로 실제 가능한 것(iteration 무관 양자화 규칙,
  비균일 임계 / 판정 임계 변경)으로 좁혀 적거나, 두 함수에 `iteration`을 넘긴다
  (`_c2v_reconstruct`는 이미 `iteration`을 받는다).

### F6 (LOW) `final_csw`와 `final_err_bits`의 측정 시점이 다른데 같은 행에 놓인다

- **위치**: `LDPC_base/decoder.py:261`(iteration 끝에서 `prev_csw` 갱신),
  `:283-286`(column 스윕 중 `err_bits` 누적), `:304-313`(둘을 같은 시점에 기록),
  `run.py:429-455`(같은 CSV 행에 `csw_mean`과 `bit_err_mean`)
- **근거**: `csw_mean`은 iteration k의 **전 column 스윕이 끝난 뒤**의 CSW이고,
  `bit_err_mean`은 iteration k의 **column 스윕 도중** 각 column 시점의 판정을 모은 값이다.
  layered 스케줄이라 원래 시점이 다르며, 이것 자체는 원본 C++와 같은 구조다.
- **영향**: 값은 맞지만 CSV를 읽는 사람이 같은 시점의 두 지표로 오해할 수 있다.
- **제안**: `decoder_main` docstring의 반환 설명에 각 값의 측정 시점을 한 줄씩 적는다.

### F7 (MEDIUM, 검증 커버리지) 저장소에 남은 회귀 근거가 배치 압축 경로를 한 번도 밟지 않는다

- **위치**: `2_LDPC_light/config.json`(`decoder.llr_matrix.file = LLR_MATRIX_HD_1.txt`),
  `Sim_Output/`과 `Ideas/vanilla/Sim_Output/`의 파일 매트릭스 실행 기록 8건 전부
- **근거**: 파일 LLR matrix를 쓰는 실행 기록 8건이 전부 `FER=1.000e+00 [64/64]`다. 전 프레임이
  실패하면 `_check_errors`가 압축을 수행해도 `keep`이 전부 True라 배열 길이가 변하지 않는다.
  즉 `final_err_bits[idx_active]` 대입과 `idx_active` 압축의 상호작용이 한 번도 시험되지 않는다.
  단계 함수 추출이 새로 만든 결합(F4)이 정확히 그 자리다.
- **영향**: 앞으로 이 경로에 회귀가 생겨도 기본 config 재실행으로는 잡히지 않는다.
- **제안**: 회귀 확인 시나리오에 성공과 실패가 섞이는 조건을 하나 고정해 둔다. 이번 리뷰에서
  쓴 조건이 그대로 쓸 만하다 (`LLR_MATRIX_HD_uniform_6bit_ch8_iter30.txt`, fixed_error
  355~375비트 구간에서 성공률이 90%에서 20%까지 내려간다).

### 참고 (팀 D/팀 B 이관) 예제 H-matrix와 `LLR_MATRIX_HD_*.txt`의 dv 구간이 맞지 않는다

동작 보존과는 별개지만 실측 중 드러났으므로 옮겨 적는다.

- ㉮ `LLR_MATRIX_HD_1.txt`와 `HD_0.txt`의 dv 구간은 `[11, 4, 3, 2]`인데, 예제 H-matrix
  `example_18x147_z256.qc`의 column degree는 `{2:17, 3:1, 4:129}`다. dv=11 구간은 쓰이지 않는다
- ㉯ 두 파일의 row 2줄은 dv=11 구간의 ch 값(1 대 5)만 다르고 나머지가 같다. 이 부호에서는
  iteration 1과 2~20의 테이블 값이 사실상 동일해진다
- ㉰ 결과로 이 조합은 에러 50비트에서도 32프레임 전량 실패한다 (실측). 반면 손으로 만든
  평범한 매트릭스(ch=6, th=8/4/2, iteration 6에 restart)로는 300비트를 32/32 정정한다.
  디코더 결함이 아니라 데이터와 부호의 정합 문제로 보인다
- ㉱ 기본 config가 이 조합을 가리키므로, 신규 사용자가 처음 실행하면 FER=1.0을 본다

---

## 확인했으나 문제 없던 항목

### ㉮ `_DecodeState` 어노테이션 대 실제 할당 (일대일 대응)

어노테이션 30개, 실행 중 실제로 할당된 속성 30개, 차집합 양방향 모두 공집합이다 (실측).
`log / need_by_dv / z / num_dv`와 결과 버퍼 11개는 `_init_state`가, 프레임 데이터 8개는
`_init_state` 후 `_check_errors`가 갱신, iteration 임시값 7개(`num_active_frames`,
`frame_err`, `err_bits`, `err_by_dv`, `edge_clear`, `cur_ch`, `cur_th`)는 `_run_iteration`
진입부가 매번 새로 채운다. 할당 전에 읽히는 속성은 없다.

### ㉯ 배치 압축 대상 목록의 완전성

`_check_errors`가 압축하는 8개(`read_bit`, `syndrome`, `prev_csw`, `min1`, `min2`,
`min1_pos`, `check_sum`, `edge_sgn`)와 `idx_active`가 프레임축을 가진 채 iteration을 넘어
살아남는 배열 전부다. 계측으로 압축 29회를 전수 확인한 결과, 압축 후 길이가 맞지 않는
배열은 다음 두 갈래뿐이고 둘 다 정상이다.

- 1. `cur_ch`, `cur_th`, `err_bits`, `err_by_dv`, `frame_err` — 다음 `_run_iteration`
     진입부(`:241-256`)가 무조건 새로 만든다. `cur_ch`/`cur_th`는 매 iteration
     `row_index()` 결과로 다시 뽑히며, 이전 객체가 재사용되는 iteration은 0회다 (실측)
- 2. `success`, `decode_success_iteration`, `final_err_bits`, `final_csw`,
     `final_err_by_dv` — 원 배치 크기 B 고정이 설계이며, 압축 전 길이와 우연히 같았던
     첫 압축 시점에만 목록에 잡혔다

### ㉰ 압축 직후 iteration의 shape 정합

`_run_iteration`이 `state.num_active_frames = state.read_bit.shape[0]`으로 다시 잡고,
`row_index(iteration, state.prev_csw)`가 `len(prev_csw)`만큼의 row 인덱스를 낸다.
계측 결과 전 iteration에서 `cur_ch.shape[0] == cur_th.shape[0] == num_active_frames`가
성립한다. 압축이 6회 이상 일어나는 조건(64 → 62 → 61 → 54 → 49 → …)에서도 어긋남이 없다.

### ㉱ `final_err_bits` / `final_csw` / `final_err_by_dv`의 "마지막 처리 iteration 값" 의미

프레임 인덱스를 추적해 독립 재구성한 값과 반환값이 전부 일치한다 (실측, 성공 35 / 실패 29 조건).

- 1. 성공 프레임: 성공한 iteration에서도 `_record_iteration`이 먼저 돌아 그 iteration의
     `err_bits`(= 0)가 기록된 뒤 배치에서 빠진다. 성공 프레임의 `final_err_bits`는 전부 0이다.
     `frame_err`가 False면 모든 column의 `bit_err`가 0이므로 `err_bits`도 반드시 0이다
- 2. 실패 프레임: max_iter까지 남아 마지막 iteration 값이 기록된다. 실패 프레임의
     `final_err_bits`는 전부 0보다 크다
- 3. 조기 종료(`not keep.any()`): 종료 판정 전에 `_record_iteration`이 이미 끝나 있어
     누락이 없다. `iteration == self.max_iter` 종료도 같다
- 4. `decode_success_iteration`은 `_check_errors`의 조기 반환보다 앞줄(`:322-323`)에서
     기록되므로 max_iter에서 성공한 프레임도 번호가 남는다

### ㉲ `_build_result` 키 집합과 `sim.py` 접근 키 집합의 일치

| 키 | `_build_result` 생성 조건 | `sim.py` 접근 조건 | 판정 |
|----|--------------------------|-------------------|------|
| `success` | 항상 | 항상 (`sim.py:58`) | 일치 |
| `decode_success_iteration` | 항상 | 항상 (`:60`, `:62`) | 일치 |
| `final_err_bits` | 항상 | 항상 (`:61`), fail_detail 시 추가 (`:76`) | 일치 |
| `log_active` | `log` 비어 있지 않음 | `if log:` (`:65`) | 일치 |
| `log_csw_sum` | `"csw" in log` | `if "csw" in log:` (`:67`) | 일치 |
| `log_err_sum` | `"bit_err" in log` | `if "bit_err" in log:` (`:69`) | 일치 |
| `log_err_by_dv_sum` | `"bit_err_by_dv" in log` | 동 조건 (`:71`) | 일치 |
| `final_csw` | `"fail_detail" in log` | 동 조건 (`:77`) | 일치 |
| `final_err_by_dv` | `"fail_detail" in log` | 동 조건 (`:78`) | 일치 |
| `profile` | `collect_profile` | 접근 없음 | 한쪽만 (의도된 분석용 출력) |

한쪽에만 있는 키는 `profile` 하나이며, `collect_profile`은 `sim.py`가 넘기지 않으므로
생성되지도 않는다. `run.py`는 `decode_result`를 직접 읽지 않고 `sim.py`가 조립한
`point_result`만 소비한다.

### ㉳ `log` 항목별 조건 분기의 짝 (KeyError 조합 전수 확인)

`LOG_ITEMS` 4개의 부분집합 16개를 전부 실행해 `_build_result`가 낸 키 집합과 `sim.py`가
접근하는 키 집합을 대조했다. 빠진 키(`MISSING`)도, 남는 키(`EXTRA`)도 0건이다.

`sim.py`는 `log=log or None`로 넘기므로 디코더 쪽 `log`와 항상 같은 집합이 된다.
`need_by_dv`가 `{"bit_err_by_dv", "fail_detail"}` 합집합으로 잡혀 있어,
`fail_detail`만 켠 조합에서도 `err_by_dv`가 채워진다.

`run.py`의 로그 CSV 작성부도 짝이 맞는다.

- 1. `_write_iter_log`는 `"iteration_totals" in point_result`와 세 항목 중 하나 이상을
     동시에 요구한다. `fail_frame_detail`만 켠 조합에서는 `iteration_totals`가 있어도
     쓰지 않는다
- 2. `_write_iter_hist_log`가 읽는 `iter_hist`와 `frames`는 `log`와 무관하게 항상 있다.
     `iter_histogram` / `fer_vs_iter`는 `_LOG_TO_ITEM`에 없어 디코더 로그를 켜지 않는다
- 3. `_write_fail_log`는 `"fail_frame_details" in point_result`로 막혀 있다

### ㉴ `cur_ch` / `cur_th`가 압축 대상에서 빠진 근거

`_run_iteration`의 `:254-256`이 조건 없이 매 iteration 재계산한다 (`edge_clear` 분기 밖,
column 루프 앞). 계측으로 전 iteration에서 새 객체가 만들어짐을 확인했다.

### ㉵ 교체 지점 시그니처가 `state`를 받지 않는지

`_is_edge_clear_iter`, `_column_order`, `_c2v_reconstruct`, `_vn_decide`, `_vnu_quantize`,
`_cnu_update` 6개 모두 `_DecodeState`를 받지 않는다. 아이디어 서브클래스가 상태 객체의
내부 구조를 알 필요는 없다. 비대칭 하나는 F3에 적었다.

### ㉶ `_cnu_update`의 view 별칭 위험

`cur_min1` / `cur_min2` / `cur_pos`는 `edge_clear`일 때 `min1` / `min2` / `min1_pos`의
view다. 그러나 대입 순서가 `min2` → `min1` → `min1_pos`이고 각 대입의 우변이 `np.where`로
먼저 새 배열을 만든 뒤 대입되므로, 읽기가 항상 쓰기보다 앞선다. 구
`_decode_column_wise`(ea88882:244-257)와 같은 구조다.

### ㉷ `_vnu_quantize` 캐스케이드의 elif 등가성

`edge_mag[-1]`로 채운 뒤 `k = len-2`부터 0까지 내려오며 덮어쓰므로, 최종값은 조건이 참인
가장 작은 `k`의 `edge_mag[k]`가 된다. C++의 `if / else if` 체인과 같고, 비단조 th에서도
"위쪽 th의 참 조건 우선"이 유지된다. `th_len >= 1`이 `LLRMatrix.__init__`에서 강제되므로
`edge_mag` 길이는 2 이상이고 루프가 최소 1회 돈다.

### ㉸ 그 밖에 확인한 것

- 1. `_read_channel_input`은 입력 dict의 `hd`를 in-place로 고치지 않는다. 같은 입력으로
     16회 반복 호출해 결과가 매번 같음을 확인했다. `code.syndrome()`도 인자를 고치지 않는다
- 2. `iteration 1`은 CN 상태를 지우지 않고 `_init_state`의 초기값(min=RESET, pos=-1,
     check_sum=0, edge_sgn=0)에 기대는데, 그 값이 restart의 클리어 결과와 같다
- 3. `bit_err`는 `uint8 ^ bool` → uint8이고, column당 합이 z=256 이하, 프레임당 합이
     N=37632 이하라 int64 누산에 넘침이 없다
- 4. restart iteration 경로(`edge_clear and iteration > 1`)와 CSW 타입 그룹의 프레임별
     row 선택 경로는 저장소 데이터에 없어, 합성 매트릭스를 만들어 평면 참조 구현과
     대조했다. 둘 다 배열 단위로 일치한다
