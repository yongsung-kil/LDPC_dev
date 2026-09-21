# 워커 R-3: 문구와 문서 (R9, R10, R11)

> 시작 시점 커밋: `6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정`
> 기록: 2026-09-21

## 확인 범위

- ㉮ R9: `5_DAO/SRC/*.py` 4개 파일 전부. docstring은 `ast` 파싱으로 함수 229개(docstring 보유 194개)의 Args, Returns, Raises 절을 시그니처, 반환문, `raise`문과 기계 대조했다. 유니코드 문자는 Hangul과 ASCII를 뺀 전체 문자를 세어 자리를 적었다
- ㉯ R10: `5_DAO/README.md`(1,451줄)와 `5_DAO/DAO_spec.md`(603줄)에서 식별자 꼴 토큰을 전부 뽑아 `SRC/`와 `Util/` 전체 낱말 집합과 대조했다. 마크다운 링크 33개는 경로 존재 여부를 실제로 확인했다. 값이 적힌 설정은 `DAO_Config.py`, `DAO_Constants.py`와 하나씩 견주었다
- ㉰ R11: `5_DAO/Util/` 파이썬 7개와 `5_DAO/Util/fer_plot/fer_plot.py` 1개를 전부 읽었다

줄 번호는 모두 커밋 `6e035e6` 시점 파일 기준으로 다시 확인했다.

---

## ㉮ docstring 불일치 목록

### ㉠ 상태 dataclass 4개 전수 대조

| 클래스 | 줄 | docstring이 말하는 것 | 실제 | 처방 | 우선 | 위험 |
|--------|-----|---------------------|------|------|------|------|
| `ReorderState` | [207](5_DAO/SRC/DAO_Main.py#L207) | "변수 설명"에 `total_rounds`(227줄), `round_best_FER`(240줄), `round_best_avg_iter`(241줄) 세 필드를 설명하고 각각 "(사용되지않음)"을 붙였다 | 세 이름은 dataclass 필드에도 없고 저장소 어디에서도 읽거나 쓰지 않는다 (`SRC/`, `Util/`, 두 문서 전수 검색 결과 이 세 줄이 유일한 출현) | 227, 240, 241 세 줄을 지운다. 나머지 13개 필드는 docstring과 정확히 일치하므로 손대지 않는다 | 상 | 없음 (주석만 삭제) |
| `AdjustIterState` | [285](5_DAO/SRC/DAO_Main.py#L285) | 필드 7개 설명 | 필드 7개, 이름과 순서 모두 일치 | 문제 없음 | 하 | 없음 |
| `DeleteRowState` | [326](5_DAO/SRC/DAO_Main.py#L326) | 필드 9개 설명 | 필드 9개, 이름과 순서 모두 일치 | 문제 없음 | 하 | 없음 |
| `InsertRestartGroupState` | [380](5_DAO/SRC/DAO_Main.py#L380) | 동작만 3줄 적고 "변수 설명" 절이 없다 | 필드 9개 (`is_active`, `current_round`, `insertable_positions`, `current_candidate_idx`, `round_best_candidate_idx`, `round_best_matrix`, `round_baseline_matrix`, `round_trial_count`, `total_expected_trials`) | `DeleteRowState`(326줄)의 "생명주기"와 "변수 설명" 두 절 형식을 그대로 옮겨 9개 필드를 적는다. 네 상태 클래스가 같은 틀을 갖게 된다 | 중 | 없음 |

### ㉡ Args 절과 시그니처의 어긋남 (기계 대조 결과 8건, 전수)

| 함수 | 줄 | docstring이 말하는 것 | 실제 시그니처 | 처방 | 우선 | 위험 |
|------|-----|---------------------|--------------|------|------|------|
| `Run_ECC` | [7913](5_DAO/SRC/DAO_Main.py#L7913) | `Args: 없음.` | `Run_ECC(self, ch_idx)` | `없음.` 줄을 `ch_idx (int): ECC를 실행할 채널 인덱스.`로 바꾼다 | 상 | 없음 |
| `Gather_Ref_C_Results` | [1784](5_DAO/SRC/DAO_Main.py#L1784) | `matrix`만 | `(matrix, ch_idx, is_test_end)` | `ch_idx (int): 결과를 모을 채널 인덱스.`와 `is_test_end (bool): 테스트 종료 집계 여부.` 두 줄을 더한다 | 상 | 없음 |
| `Distribute_Uncors_To_Local_Session` | [1531](5_DAO/SRC/DAO_Main.py#L1531) | `src_path`만 | `(src_path, ch_idx, is_uncor_type_seed)` | `ch_idx (int): 분배 대상 채널 인덱스.`와 `is_uncor_type_seed (bool): True면 시드, False면 벡터.` 두 줄을 더한다 | 상 | 없음 |
| `Get_Result_File_Name` | [1604](5_DAO/SRC/DAO_Main.py#L1604) | `process_idx`만. 게다가 절 머리가 `Args:s`로 적혀 있다 | `(process_idx, ch_idx)` | `Args:s`를 `Args:`로 고치고 `ch_idx (int): 결과 파일이 속한 채널 인덱스.`를 더한다 | 상 | 없음 |
| `Print_Test_Result` | [7545](5_DAO/SRC/DAO_Main.py#L7545) | `matrix`, `is_test_optimal`만 | `(matrix, is_test_optimal, ch_idx, is_test_end)` | `ch_idx`와 `is_test_end` 두 줄을 더한다 | 중 | 없음 |
| `Set_Test_Environment` | [8449](5_DAO/SRC/DAO_Main.py#L8449) | `matrix`만 | `(matrix, ch_idx)` | `ch_idx (int): 테스트 환경을 준비할 채널 인덱스.`를 더한다 | 중 | 없음 |
| `Print_LLR_Matrix` | [7284](5_DAO/SRC/DAO_Main.py#L7284) | `matrix`만 | `(matrix, is_print_optimal)` | `is_print_optimal (Optional[bool]): 최적 매트릭스 머리글로 출력할지 여부.`를 더한다 | 중 | 없음 |
| `Gen_LLR_Regen_DV` | [3893](5_DAO/SRC/DAO_Main.py#L3893) | 인자 이름을 `matrix`로 적었다 | 인자 이름은 `input_matrix` | docstring의 `matrix (LLR_MATRIX)`를 `input_matrix (LLR_MATRIX)`로 고친다 | 중 | 없음 |

`DAO_LLR_MATRIX.py`에는 Args 절이 아예 없는 메서드 2개가 있다.

| 메서드 | 줄 | 인자 | 처방 | 우선 | 위험 |
|--------|-----|------|------|------|------|
| `LLR_MATRIX.get_line` | [467](5_DAO/SRC/DAO_LLR_MATRIX.py#L467) | `idx`, `field_name` | Args 절을 새로 쓴다 | 중 | **옆 세션과 겹침**. `get_line`은 출력 줄 구성의 중심이라 분기 필드 추가 작업이 같은 함수를 고칠 가능성이 높다. 옆 세션 작업이 끝난 뒤 고친다 |
| `LLR_MATRIX.Correct_Ch_Th_In_Row` | [603](5_DAO/SRC/DAO_LLR_MATRIX.py#L603) | `values`, `group_idx`, `row_idx` | Args 절을 새로 쓴다 | 중 | 유효성 규칙 확장과 겹칠 수 있다. 같은 이유로 뒤로 미룬다 |

### ㉢ Raises 절이 실제와 다른 곳 (전수 17건)

`Raises:` 절을 가진 함수는 17개이고, 그 가운데 16개는 파이썬 예외를 던진다고 적었으나 본문에는 `raise`문이 없고 `MPI_Abort`를 부른다. `MPI_Abort`([6800](5_DAO/SRC/DAO_Main.py#L6800))는 로그와 콘솔에 메시지를 남긴 뒤 `comm.Abort()`로 전체 프로세스를 끝내므로, 호출한 쪽이 잡을 수 있는 예외가 아니다. 읽는 사람이 `try` 블록으로 감쌀 수 있다고 오해하게 된다.

| 함수 | 줄 | docstring이 적은 예외 |
|------|-----|---------------------|
| `_generate_random_row` | [754](5_DAO/SRC/DAO_Main.py#L754) | `ValueError` |
| `_append_lines_without_rotation` | [787](5_DAO/SRC/DAO_Main.py#L787) | `OSError` |
| `Build_ECC` | [846](5_DAO/SRC/DAO_Main.py#L846) | `SystemExit` |
| `Copy_Uncors` | [1248](5_DAO/SRC/DAO_Main.py#L1248) | `ValueError` |
| `Copy_ECC_EXE` | [1307](5_DAO/SRC/DAO_Main.py#L1307) | `SystemExit` |
| `Gather_Ref_C_Results` | [1784](5_DAO/SRC/DAO_Main.py#L1784) | `ValueError` |
| `Generate_Initial_Random_Row` | [2036](5_DAO/SRC/DAO_Main.py#L2036) | `ValueError` |
| `Get_Decoder_Mode_Str` | [2055](5_DAO/SRC/DAO_Main.py#L2055) | `ValueError` |
| `Initialize_Log` | [2200](5_DAO/SRC/DAO_Main.py#L2200) | `RuntimeError` |
| `Load_Initial_LLR_Matrix` | [2561](5_DAO/SRC/DAO_Main.py#L2561) | `SystemExit` |
| `Gen_LLR_Mutate_CSW` | [3701](5_DAO/SRC/DAO_Main.py#L3701) | `ValueError` |
| `Gen_LLR_Mutate_Matrix` | [3731](5_DAO/SRC/DAO_Main.py#L3731) | `ValueError` |
| `Run_ECC` | [7913](5_DAO/SRC/DAO_Main.py#L7913) | `SystemExit` |
| `Read_FER_From_File` | [7971](5_DAO/SRC/DAO_Main.py#L7971) | `SystemExit` |
| `Set_Max_Error` | [8553](5_DAO/SRC/DAO_Main.py#L8553) | `ValueError` |
| `Update_Optimal_LLR` | [9548](5_DAO/SRC/DAO_Main.py#L9548) | `ValueError` |

처방: 위 16곳의 `Raises:` 절을 같은 형식의 한 줄로 다시 쓴다. 예를 들어 `Run_ECC`는

```
Raises:
    SystemExit: 외부 명령 실행이 실패한 경우.
```

를

```
종료:
    외부 명령 실행이 실패하면 MPI_Abort로 전체 프로세스를 끝낸다.
```

로 바꾼다. 절 이름을 `Raises`에서 `종료`로 바꾸면 "잡을 수 있는 예외"라는 오해가 남지 않는다. 우선 상, 위험 없음(주석만).

열일곱 번째는 `Write_Log_Lines`([9927](5_DAO/SRC/DAO_Main.py#L9927))다. `OSError`를 던진다고 적었으나 본문은 `_append_lines_without_rotation`에 넘기고, update 로그 쓰기의 `OSError`는 `_write_error_log`로 삼킨다. 처방: `Raises:` 절 세 줄을 지우고 `쓰기 실패는 _write_error_log로 기록하고 진행을 이어 간다.` 한 줄을 Returns 절 아래에 둔다. 우선 중.

### ㉣ 본문과 어긋나는 설명 문장

| 대상 | 줄 | docstring이 말하는 것 | 실제 | 처방 | 우선 | 위험 |
|------|-----|---------------------|------|------|------|------|
| `Set_Current_Optimal_Matrix` | [8688](5_DAO/SRC/DAO_Main.py#L8688) | "Change iteration mode의 경우, threshold를 활용하여 max iteration을 설정한다" | 본문은 `update_mode` 값에 따라 `optimal_LLR_matrix` 또는 `temp_optimal_LLR_matrix`에 `Deep_Copy` 결과를 넣을 뿐이다. "Change iteration mode"라는 이름은 코드 어디에도 없다 | 8688줄을 `update_mode 값에 따라 current 또는 temp_optimal 매트릭스를 optimal로 복사한다.`로 다시 쓴다 | 상 | 없음 |
| `Copy_Uncors` | [1248](5_DAO/SRC/DAO_Main.py#L1248) | Args에 `test_mode (TestMode): TestMode.FULL.`을 적었다 | 본문은 `test_mode`를 한 번도 읽지 않고 `UNCOR_CONFIG.UNCOR_MATRIX_IDX`만으로 경로를 정한다 | 인자 제거 여부는 T팀 판정에 달렸다. 인자를 남긴다면 Args 줄을 `test_mode (TestMode): 호출부 서명을 맞추기 위한 자리이며 경로 결정에 쓰이지 않는다.`로 정직하게 쓴다 | 중 | 인자 삭제는 동작 변경. **문구만 고치는 쪽을 먼저 한다** |

---

## ㉯ 문구 위반 목록 (자리와 개수)

### ㉠ 줄표 (em dash, U+2014): `DAO_Main.py` 17곳, `Util` 5곳

프로젝트 규칙은 줄표를 쓰지 않고 접속사나 쉼표로 잇고 부연은 괄호에 넣는다.

| 줄 | 종류 | 처방 (고칠 문구) |
|----|------|----------------|
| [1709](5_DAO/SRC/DAO_Main.py#L1709) | 로그 | `... CSW 파일 누락 — {CSW_file_path}` → `... CSW 파일 누락: {CSW_file_path}` |
| [1749](5_DAO/SRC/DAO_Main.py#L1749) | MPI_Abort | `... 병합 쓰기 실패 — {path}: {e}` → `... 병합 쓰기 실패 ({path}): {e}` |
| [1762](5_DAO/SRC/DAO_Main.py#L1762) | MPI_Abort | `... uncor_seed 쓰기 실패 — {path}: {e}` → `... uncor_seed 쓰기 실패 ({path}): {e}` |
| [2494](5_DAO/SRC/DAO_Main.py#L2494) | 로그 | `Matrix idx: {idx} — 검증 실패 ...` → `Matrix idx: {idx}, 검증 실패 ...` |
| [2496](5_DAO/SRC/DAO_Main.py#L2496) | 로그 | `Matrix idx: {idx} — 생성 실패 ...` → `Matrix idx: {idx}, 생성 실패 ...` |
| [7447](5_DAO/SRC/DAO_Main.py#L7447) | MPI_Abort | `풀 파일 쓰기 실패 — {dest_path}: {e}` → `풀 파일 쓰기 실패 ({dest_path}): {e}` |
| [7887](5_DAO/SRC/DAO_Main.py#L7887) | 로그 | `라인 수 읽기 실패 — {dst_file}: {e}` → `라인 수 읽기 실패 ({dst_file}): {e}` |
| [8070](5_DAO/SRC/DAO_Main.py#L8070) | 주석 | `... bcast로 동기화 — time_exceeded와 동일 패턴)` → `... bcast로 동기화, time_exceeded와 동일 패턴)` |
| [8135](5_DAO/SRC/DAO_Main.py#L8135) | 로그 | `{초}초 경과 — speed test 재실행` → `{초}초 경과, speed test 재실행` |
| [8271](5_DAO/SRC/DAO_Main.py#L8271) | 로그 | `... 결과 무시됨 — {file_path} ({e})` → `... 결과 무시됨 ({file_path}: {e})` |
| [9119](5_DAO/SRC/DAO_Main.py#L9119) | 주석 | `(excluded_cores 변경 시에만 — 복귀/제외된 ...)` → `(excluded_cores가 바뀐 때만 복귀하거나 제외된 ...)` |
| [9199](5_DAO/SRC/DAO_Main.py#L9199) | 주석 | `... 가지고 있음 — _Setup_Uncor_Pool_For_Channel이 처리` → `... 가지고 있고, _Setup_Uncor_Pool_For_Channel이 처리한다` |
| [10035](5_DAO/SRC/DAO_Main.py#L10035) | 주석 | `(Initial test/Rebalance 불필요 — Setup_Uncors에서 ...)` → `(Initial test와 Rebalance는 필요 없고 Setup_Uncors에서 ...)` |
| [10304](5_DAO/SRC/DAO_Main.py#L10304) | 출력 파일 | `# Ranking metric: FER — Frame Error Rate (낮을수록 상위)` → `# Ranking metric: FER (Frame Error Rate, 낮을수록 상위)` |
| [10309](5_DAO/SRC/DAO_Main.py#L10309) | MPI_Abort | `FER 요약 쓰기 실패 — {path}: {e}` → `FER 요약 쓰기 실패 ({path}): {e}` |
| [10331](5_DAO/SRC/DAO_Main.py#L10331) | 출력 파일 | `#uncor(csw≤{T}) — uncorrectable 중 ...` → `#uncor(csw≤{T}) (uncorrectable 가운데 ...)` |
| [10336](5_DAO/SRC/DAO_Main.py#L10336) | MPI_Abort | `CSW T={T} 요약 쓰기 실패 — {path}: {e}` → `... 실패 ({path}): {e}` |
| [Util/collect_llr_matrices.py:12](5_DAO/Util/collect_llr_matrices.py#L12) | docstring | `... 기준 — 같은 idx면 ...` → `... 기준 (같은 idx면 ...)` |
| [Util/collect_llr_matrices.py:13](5_DAO/Util/collect_llr_matrices.py#L13) | docstring | `... 비교 — 내용도 같으면 ...` → `... 비교 (내용도 같으면 ...)` |
| [Util/collect_llr_matrices.py:112](5_DAO/Util/collect_llr_matrices.py#L112) | 출력 | `(dry-run 모드 — 실제 파일 조작 없음)` → `(dry-run 모드이므로 실제 파일 조작 없음)` |
| [Util/remote_server_sync.py:313](5_DAO/Util/remote_server_sync.py#L313) | 로그 | `완료 — 다운로드: ...` → `완료. 다운로드: ...` |
| [Util/fer_plot/fer_plot.py:2](5_DAO/Util/fer_plot/fer_plot.py#L2) | docstring | `FER Plot Tool — LDPC 디코딩 결과 그래프 생성` → `FER Plot Tool: LDPC 디코딩 결과 그래프 생성` |

우선 상 (규칙 정면 위반, 22곳). 위험 없음. 출력 파일에 들어가는 10304와 10331은 요약 파일의 주석 줄이므로 파서에 영향이 없다.

### ㉡ 가운뎃점 (middle dot, U+00B7): 3줄 4개

| 줄 | 문구 | 처방 |
|----|------|------|
| [2315](5_DAO/SRC/DAO_Main.py#L2315) | `... 배포한 뒤 저장·검증을 수행한다.` | `... 배포한 뒤 저장하고 검증한다.` |
| [8006](5_DAO/SRC/DAO_Main.py#L8006) | `... 생성하고 검증·테스트·갱신 절차를 반복해 ...` | `... 생성하고 검증, 테스트, 갱신을 차례로 반복해 ...` |
| [8494](5_DAO/SRC/DAO_Main.py#L8494) | `... 바탕으로 시드 로딩·저장 모드를 결정한다.` | `... 바탕으로 시드 로딩 모드와 저장 모드를 결정한다.` |

우선 상, 위험 없음.

### ㉢ 유니코드 대체 문자 (U+FFFD): 1줄 3개

[6624](5_DAO/SRC/DAO_Main.py#L6624) `Make_Log_Backup` docstring이 `rename(종료 idx 추가)<U+FFFD><U+FFFD><U+FFFD>고 새 파일로 전환한다.`로 깨져 있다. 인코딩이 어긋나 "하" 한 글자가 3바이트 그대로 남았다.

처방: 해당 줄을 `최대 라인 수를 넘기면 현재 로그 파일 이름에 종료 idx를 붙여 rename하고 새 파일로 넘어간다.`로 다시 쓴다. 우선 상, 위험 없음.

### ㉣ 이모지와 장식 문자: 12줄

| 문자 | 줄 | 처방 |
|------|-----|------|
| `⚠️` | [1512](5_DAO/SRC/DAO_Main.py#L1512), [1529](5_DAO/SRC/DAO_Main.py#L1529), [1564](5_DAO/SRC/DAO_Main.py#L1564), [7418](5_DAO/SRC/DAO_Main.py#L7418), [9066](5_DAO/SRC/DAO_Main.py#L9066), [9082](5_DAO/SRC/DAO_Main.py#L9082), [9091](5_DAO/SRC/DAO_Main.py#L9091) | `⚠️`를 `[WARNING]`으로 바꾼다. 로그 파일을 `grep "[WARNING]"`으로 훑을 때 이 7줄이 함께 잡힌다 |
| `✓` | [4798](5_DAO/SRC/DAO_Main.py#L4798), [5685](5_DAO/SRC/DAO_Main.py#L5685), [5976](5_DAO/SRC/DAO_Main.py#L5976) | `✓ New round best:`를 `[Round best]`로 바꾼다 |
| `✗` | [5291](5_DAO/SRC/DAO_Main.py#L5291), [5376](5_DAO/SRC/DAO_Main.py#L5376) | `✗ Failed to create ...`를 `[FAILED] ...`로 바꾼다 |

우선 중. 위험 없음(로그 문구만). 로그를 기계로 읽는 코드는 없다(결과 파싱은 Ref-C 결과 파일만 대상으로 한다).

### ㉤ 구분선 표기가 세 갈래로 갈림

`DAO_Constants.py`는 `SEPARATOR_LENGTH = 20`으로 `SEPARATOR_TYPE1`(하이픈)과 `SEPARATOR_TYPE2`(등호)를 만든다([132](5_DAO/SRC/DAO_Constants.py#L132)). 그런데 코드에는 세 갈래가 섞여 있다.

- ㉠ 상수 사용: [1020](5_DAO/SRC/DAO_Main.py#L1020), [2351](5_DAO/SRC/DAO_Main.py#L2351), [7206](5_DAO/SRC/DAO_Main.py#L7206), [7233](5_DAO/SRC/DAO_Main.py#L7233), [7265](5_DAO/SRC/DAO_Main.py#L7265), [7275](5_DAO/SRC/DAO_Main.py#L7275), [8714](5_DAO/SRC/DAO_Main.py#L8714), [8961](5_DAO/SRC/DAO_Main.py#L8961), [9035](5_DAO/SRC/DAO_Main.py#L9035), [9098](5_DAO/SRC/DAO_Main.py#L9098), [9114](5_DAO/SRC/DAO_Main.py#L9114), [9125](5_DAO/SRC/DAO_Main.py#L9125), [9990](5_DAO/SRC/DAO_Main.py#L9990) (13곳)
- ㉡ 길이를 직접 적은 ASCII: `"="*80` 8곳([194](5_DAO/SRC/DAO_Main.py#L194), [203](5_DAO/SRC/DAO_Main.py#L203), [4513](5_DAO/SRC/DAO_Main.py#L4513), [4521](5_DAO/SRC/DAO_Main.py#L4521), [4592](5_DAO/SRC/DAO_Main.py#L4592), [4600](5_DAO/SRC/DAO_Main.py#L4600), [6762](5_DAO/SRC/DAO_Main.py#L6762), [6872](5_DAO/SRC/DAO_Main.py#L6872)), `"="*70` 4곳([7646](5_DAO/SRC/DAO_Main.py#L7646), [7674](5_DAO/SRC/DAO_Main.py#L7674), [7769](5_DAO/SRC/DAO_Main.py#L7769), [9466](5_DAO/SRC/DAO_Main.py#L9466)), `"="*50` 6곳([5211](5_DAO/SRC/DAO_Main.py#L5211), [5339](5_DAO/SRC/DAO_Main.py#L5339), [5476](5_DAO/SRC/DAO_Main.py#L5476), [5834](5_DAO/SRC/DAO_Main.py#L5834), [7848](5_DAO/SRC/DAO_Main.py#L7848), [7911](5_DAO/SRC/DAO_Main.py#L7911))
- ㉢ 상자 그리기 문자: `"═"*50` 2곳([5699](5_DAO/SRC/DAO_Main.py#L5699), [5989](5_DAO/SRC/DAO_Main.py#L5989)), 58자를 직접 적은 `═` 2곳([4827](5_DAO/SRC/DAO_Main.py#L4827), [4835](5_DAO/SRC/DAO_Main.py#L4835)), `"─"*50` 4곳([5194](5_DAO/SRC/DAO_Main.py#L5194), [5238](5_DAO/SRC/DAO_Main.py#L5238), [5487](5_DAO/SRC/DAO_Main.py#L5487), [5845](5_DAO/SRC/DAO_Main.py#L5845)), 주석 장식 `# ─── Step N ───` 7곳([9365](5_DAO/SRC/DAO_Main.py#L9365), [9373](5_DAO/SRC/DAO_Main.py#L9373), [9378](5_DAO/SRC/DAO_Main.py#L9378), [9381](5_DAO/SRC/DAO_Main.py#L9381), [9408](5_DAO/SRC/DAO_Main.py#L9408), [9434](5_DAO/SRC/DAO_Main.py#L9434), [9443](5_DAO/SRC/DAO_Main.py#L9443))

처방: `DAO_Constants.py`에 `SEPARATOR_SECTION = "=" * 80`, `SEPARATOR_SUBSECTION = "=" * 50`, `SEPARATOR_ROUND = "-" * 50` 세 상수를 더하고, 위 20곳을 이 이름으로 바꾼다. `═`와 `─`는 ASCII로 바꾼다. 4827과 4835의 58자 `═` 줄은 `SEPARATOR_SUBSECTION`으로 바꾼다. 주석 장식 7곳은 `# Step N: ...`으로 다듬는다. 우선 중, 위험 없음(로그 모양만 달라진다).

### ㉥ 로그 머리표 철자가 네 갈래

`[WARNING]` 11곳, `[WARN]` 10곳, `[Warning]` 2곳, `[Error]` 9곳이 한 파일에 섞여 있다. 처방: `[WARNING]`과 `[ERROR]` 두 갈래로 통일한다. 우선 중, 위험 없음.

### ㉦ 로그 문구의 한국어와 영어 혼용

`Write_Log_Lines`와 `MPI_Abort`에 들어가는 문자열 리터럴 314개 가운데 영어만 278개, 한국어만 5개, 한 문장 안에 둘이 섞인 것 31개다. 섞인 자리의 보기는 [1709](5_DAO/SRC/DAO_Main.py#L1709), [4299](5_DAO/SRC/DAO_Main.py#L4299), [7489](5_DAO/SRC/DAO_Main.py#L7489), [7845](5_DAO/SRC/DAO_Main.py#L7845), [8135](5_DAO/SRC/DAO_Main.py#L8135), [9091](5_DAO/SRC/DAO_Main.py#L9091), [9123](5_DAO/SRC/DAO_Main.py#L9123)이다.

처방: 규칙 하나를 정한다. 식별자와 상태 이름(`Rank`, `FER`, `Partial`, `excluded_cores`)은 영어 그대로 두고, 그것을 설명하는 서술부는 전부 한국어로 쓴다. 예를 들어 [7489](5_DAO/SRC/DAO_Main.py#L7489) `[Setup_Uncor_Pool] Pool 생성 완료.`는 그대로 두고, [8140](5_DAO/SRC/DAO_Main.py#L8140) `[Periodic Speed Test] excluded_cores 변경 없음, 균일 재분배 스킵`은 `... 균일 재분배를 건너뛴다`로 서술부만 한국어로 맞춘다. 우선 하, 위험 없음. 31곳을 한 번에 손대는 것보다 다른 수정과 함께 지나가는 자리마다 고치는 쪽이 낫다.

### ㉧ 과거가 어땠고 지금 어떻다를 서술하는 주석 (프로젝트 규칙 "수리는 다시 쓰기" 위반)

| 줄 | 지금 문구 | 다시 쓸 문구 | 우선 |
|----|----------|------------|------|
| [227](5_DAO/SRC/DAO_Main.py#L227), [240](5_DAO/SRC/DAO_Main.py#L240), [241](5_DAO/SRC/DAO_Main.py#L241) | `- total_rounds: 전체 Round 수 (사용되지않음)` 외 2줄 | 줄 자체를 지운다 (㉮ ㉠과 같은 처방) | 상 |
| [1805](5_DAO/SRC/DAO_Main.py#L1805) | `# === while 루프 중: root만 순차 읽기 (기존 로직) ===` | `# === while 루프 중: root만 순차로 읽는다 ===` | 상 |
| [7380](5_DAO/SRC/DAO_Main.py#L7380) | `# Fallback: 기존 직렬 방식` | `# Fallback: 프로세스마다 차례로 복사` | 상 |
| [8043](5_DAO/SRC/DAO_Main.py#L8043) | `# 기존 모드: Full 테스트만 수행` | `# Two-stage를 끈 경우: Full 테스트만 수행` | 상 |
| [8091](5_DAO/SRC/DAO_Main.py#L8091) | `# ENABLE_TWO_STAGE_TEST=False: 항상 True (기존 동작)` | `# ENABLE_TWO_STAGE_TEST=False: 항상 True` | 상 |
| [8112](5_DAO/SRC/DAO_Main.py#L8112) | `# 다른 모드는 기존대로` | `# 멀티라운드가 아닌 모드는 강제 종료 여부만 본다` | 상 |
| [9227](5_DAO/SRC/DAO_Main.py#L9227), [9483](5_DAO/SRC/DAO_Main.py#L9483) | `- False (기존 모드): Full 테스트만 수행` | `- False: Full 테스트만 수행` | 상 |
| [9237](5_DAO/SRC/DAO_Main.py#L9237) | `# 기존 모드: Full 테스트만` | `# Two-stage를 끈 경우: Full 테스트만` | 상 |
| [9460](5_DAO/SRC/DAO_Main.py#L9460) | `기존 DAO_END_FLAG 메커니즘을 활용하여 ...` | `DAO_END_FLAG 파일로 optimization loop에 ...` | 상 |
| [9492](5_DAO/SRC/DAO_Main.py#L9492) | `ENABLE_TWO_STAGE_TEST=False일 때는 항상 True (기존 동작 유지)` | `ENABLE_TWO_STAGE_TEST=False일 때는 항상 True` | 상 |
| [10016](5_DAO/SRC/DAO_Main.py#L10016) | `# 기존 최적화 경로` | `# 최적화 경로` | 상 |
| [DAO_Config.py:198](5_DAO/SRC/DAO_Config.py#L198) | `# False: 기존 방식 (Full 테스트만 수행, UNCOR_MATRIX_IDX 사용)` | `# False: Full 테스트만 수행하고 UNCOR_MATRIX_IDX를 쓴다` | 상 |

전부 주석과 docstring이므로 동작 변경이 없고 옆 세션과도 겹치지 않는다. "기존 파일 있으면 삭제"([1298](5_DAO/SRC/DAO_Main.py#L1298)) 같이 "이미 있는 파일"을 뜻하는 `기존`은 과거 서술이 아니므로 그대로 둔다.

---

## ㉰ 매직 넘버 목록

| 값 | 자리 | 뜻 | 제안 상수명과 둘 곳 | 우선 | 위험 |
|----|------|-----|-------------------|------|------|
| `100*60*60` | [2307](5_DAO/SRC/DAO_Main.py#L2307) | 단계 시간 제한을 껐다고 볼 문턱 (100시간) | `DAO_Constants.py`에 `STAGE_TIME_LIMIT_DISABLED_SECONDS = 100 * 60 * 60`. `TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS`의 주석([320](5_DAO/SRC/DAO_Config.py#L320))이 이미 "100시간 이상이면 제한 없음"이라고 같은 수를 말로 적고 있으므로, 한 이름으로 묶으면 두 자리가 어긋날 일이 없어진다 | 상 | 없음 (값이 같다) |
| `3600` | [6692](5_DAO/SRC/DAO_Main.py#L6692) | `MPI_Barrier`가 쓰는 최소 타임아웃 | `DAO_Config.py`의 `TIME_CONFIG`에 `MPI_BARRIER_MIN_TIMEOUT_SECONDS = 1 * 60 * 60` | 상 | 없음 |
| `1e-15` | [2540](5_DAO/SRC/DAO_Main.py#L2540), [4777](5_DAO/SRC/DAO_Main.py#L4777), [4778](5_DAO/SRC/DAO_Main.py#L4778), [6108](5_DAO/SRC/DAO_Main.py#L6108), [6113](5_DAO/SRC/DAO_Main.py#L6113) | FER과 평균 반복 횟수의 동점 판정 허용 오차 | `DAO_Constants.py`에 `FER_TIE_TOLERANCE = 1e-15`. 다섯 자리가 같은 뜻이므로 한 이름으로 묶는다 | 상 | 값이 같아 동작 변경 없음 |
| `12` | [7947](5_DAO/SRC/DAO_Main.py#L7947) | `errno` 메모리 부족 | `import errno`를 더하고 `error.errno == errno.ENOMEM`으로 바꾼다. 옆의 주석 `# Cannot allocate memory`가 필요 없어진다 | 중 | 값이 같아 동작 변경 없음 |
| `seq_len * 2` | [8172](5_DAO/SRC/DAO_Main.py#L8172) | 유효 LLR을 못 만든 stage가 몇 번 이어지면 끝낼지 | `DAO_Config.py`의 `DAO_CONFIG`에 `MAX_CONSECUTIVE_FAILED_STAGE_CYCLES = 2`를 두고 `seq_len * DAO_CONFIG.MAX_CONSECUTIVE_FAILED_STAGE_CYCLES`로 쓴다. "시퀀스를 두 바퀴 돌 동안 하나도 못 만들면 끝낸다"는 뜻이 이름에 드러난다 | 중 | 값이 같아 동작 변경 없음 |
| `10000` | [8752](5_DAO/SRC/DAO_Main.py#L8752) | rank별 시드 간격 | `DAO_Constants.py`에 `SEED_STRIDE_PER_RANK = 10000` | 중 | 없음 |
| `0.5` | [7942](5_DAO/SRC/DAO_Main.py#L7942) | ECC 실행 뒤 파일이 쓰이기를 기다리는 시간 | `TIME_CONFIG`에 `ECC_RESULT_FLUSH_WAIT_SECONDS = 0.5` | 중 | 없음 |
| `max_retries=3`, `retry_delay=0.1` | [8189](5_DAO/SRC/DAO_Main.py#L8189) | 결과 파일 파싱 재시도 | 기본 인자를 `TIME_CONFIG.RESULT_PARSE_MAX_RETRIES = 3`, `TIME_CONFIG.RESULT_PARSE_RETRY_DELAY_SECONDS = 0.1`로 옮긴다 | 하 | 없음 |
| `5`, `0.02` | [8211](5_DAO/SRC/DAO_Main.py#L8211), [8216](5_DAO/SRC/DAO_Main.py#L8216) | 결과 파일 크기가 멈출 때까지 최대 5회, 20ms 간격으로 본다 | `RESULT_SIZE_STABLE_CHECK_COUNT = 5`, `RESULT_SIZE_STABLE_INTERVAL_SECONDS = 0.02` | 하 | 없음 |
| `sleep_interval = 1` | [1361](5_DAO/SRC/DAO_Main.py#L1361) | 디버그 일시정지 폴링 간격. [1393](5_DAO/SRC/DAO_Main.py#L1393)에서 `* 3`으로 다시 쓰인다 | `DEBUG_PAUSE_POLL_SECONDS = 1`, `DEBUG_PAUSE_RESUME_WAIT_SECONDS = 3`으로 갈라 이름을 준다. `* 3`이 무엇인지 지금은 알 수 없다 | 중 | 없음 |
| `"Partial"` 문자열 | [1673](5_DAO/SRC/DAO_Main.py#L1673), [1732](5_DAO/SRC/DAO_Main.py#L1732), [2111](5_DAO/SRC/DAO_Main.py#L2111), [7404](5_DAO/SRC/DAO_Main.py#L7404), [7515](5_DAO/SRC/DAO_Main.py#L7515), [7691](5_DAO/SRC/DAO_Main.py#L7691), [8954](5_DAO/SRC/DAO_Main.py#L8954) | Partial 하위 디렉토리 이름과 표시 문자열 | `DAO_Constants.py`의 `TEST_MODE_DIR_NAME`([76](5_DAO/SRC/DAO_Constants.py#L76))이 바로 이 표인데 **저장소 어디에서도 쓰이지 않는다**(전수 검색 결과 정의 1곳뿐). 7곳을 `TEST_MODE_DIR_NAME`로 바꾸거나, T팀이 이 상수를 지우기로 하면 `PARTIAL_DIR_NAME = "Partial"` 하나를 두고 7곳을 묶는다 | 상 | **T팀 실마리 ㉳과 겹침**. 어느 쪽으로 정리할지 T팀 결론을 기다린 뒤 손댄다 |
| `"llr_matrix"` | [969](5_DAO/SRC/DAO_Main.py#L969) | 파일 이름 접두를 소문자로 견주는 자리 | `PATH_CONFIG.LLR_MATRIX_FILE_NAME_TEMPLATE`에서 접두를 뽑아 쓰거나 `LLR_MATRIX_FILE_NAME_PREFIX = "LLR_MATRIX_"`를 `DAO_Constants.py`에 둔다 | 중 | 없음 |
| `"collected"` | [10357](5_DAO/SRC/DAO_Main.py#L10357), [10378](5_DAO/SRC/DAO_Main.py#L10378) | 단일 row 후보 모음 디렉토리 이름 | `DAO_Constants.py`에 `COLLECTED_CANDIDATES_DIR_NAME = "collected"` | 중 | 없음 |
| `"Copied_uncors"` | [1285](5_DAO/SRC/DAO_Main.py#L1285), [1287](5_DAO/SRC/DAO_Main.py#L1287) | 복사한 uncor를 담는 디렉토리 이름 | `DAO_Constants.py`에 `COPIED_UNCORS_DIR_NAME = "Copied_uncors"` | 중 | 없음 |
| `1024` | [Util/Mock_ECC.py:59](5_DAO/Util/Mock_ECC.py#L59) | Mock ECC가 쓰는 최대 CSW | `DAO_Constants.py`의 `MAX_CSW = 1408`([140](5_DAO/SRC/DAO_Constants.py#L140))과 어긋난다. Mock_ECC는 `SRC/`를 import하지 않고 값을 따로 적어 두었다가 벌어진 차이다 | 상 | **값이 다르다**. 1408로 맞추면 Mock 출력이 달라지므로 T팀 확인이 필요하다 |

`DAO_Constants.py`에 정의만 있고 쓰이지 않는 이름이 두 개 더 있다. `TEST_MODE_DIR_NAME`([76](5_DAO/SRC/DAO_Constants.py#L76))과 `GenLLRModeHBF`([43](5_DAO/SRC/DAO_Constants.py#L43))이다. 둘 다 "쓰이는 줄 알고 읽다가 헛걸음하는" 자리라 가독성 비용이 크다. `GenLLRModeHBF`는 L팀 실마리 ㉯의 대상이므로 여기서는 자리만 적는다.

---

## ㉱ 문서와 코드의 이름 대조 전수표

식별자 꼴 토큰을 문서에서 전부 뽑아 코드 낱말 집합과 견준 결과다. 예시용 자리표시(`LLR_MATRIX_2`, `ch_1_uncor_0`, `Process_2`, `seed_ch0`, `new_group` 등)는 뺐다.

### ㉠ 코드에 없는 이름

| 문서가 쓴 이름 | 문서 위치 | 코드에 있는가 | 실제 코드 이름 | 처방 | 우선 |
|--------------|----------|-------------|--------------|------|------|
| `ExitAfterInitialMatrixMode` | README 57, 88, 341, 940, 1285, 1366 | 없음 | `RunDAOMode` ([63](5_DAO/SRC/DAO_Constants.py#L63)) | 전 자리를 `RunDAOMode`로 바꾼다 | 상 |
| `EXIT_AFTER_INITIAL_MATRIX_MODE` | README 57, 88, 341, 940, 1366 | 없음 | `DAO_CONFIG.RUN_DAO_MODE` ([130](5_DAO/SRC/DAO_Config.py#L130)) | 전 자리를 `RUN_DAO_MODE`로 바꾼다 | 상 |
| `EXIT_AFTER_TEST_FER` | README 88, 943, 1289, 1366 | 없음 | `RunDAOMode.TEST_FER` | 바꾼다 | 상 |
| `EXIT_AFTER_SAVE_UNCOR` | README 944, 1290, 1406 | 없음 | `RunDAOMode.SAVE_UNCOR` | 바꾼다 | 상 |
| `EXIT_AFTER_LOAD_AND_SAVE_UNCOR` | README 945, 1291, 1406 | 없음 | `RunDAOMode.REDECODE` | 바꾼다 | 상 |
| (문서에 없음) | README 4.2.1 | 있음 | `RunDAOMode.RUN_OPTIMIZATION`, `RunDAOMode.GEN_SINGLE_ROW` | README 4.2.1 목록에 두 값을 더한다. `GEN_SINGLE_ROW`(모드 4)는 README 전체에 한 번도 나오지 않는다 | 상 |
| `PARTIAL_UNCOR_MATRIX_IDX` | README 66, 359, 697, 709, 717, 720 외 | 없음 | 없음. Partial uncor는 `Rebuild_Partial_Pool`([9350 부근](5_DAO/SRC/DAO_Main.py#L9350))이 Full uncor 재디코딩으로 그때그때 만든다 | README 1.2.2, 3.2.2, 3.2.3, 4.1.3의 관련 단락을 "Partial은 동적으로 만든다"로 다시 쓴다 | 상 |
| `FULL_UNCOR_MATRIX_IDX` | README 67, 360, 698, 712, 718, 721 외 | 없음 | `UNCOR_CONFIG.UNCOR_MATRIX_IDX` ([206](5_DAO/SRC/DAO_Config.py#L206))가 Full 경로와 비 two-stage 경로를 겸한다 | 위와 같은 단락에서 `UNCOR_MATRIX_IDX` 하나로 다시 쓴다 | 상 |
| `MAX_STAGE_TIME_SECONDS` | README 388, 1126 | 없음 | `TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS` ([320](5_DAO/SRC/DAO_Config.py#L320)) | 이름을 바꾸고 값도 고친다 (아래 ㉡) | 상 |
| `effective_FERs` | README 279, 769 | 없음 | `LLR_MATRIX.FERs` ([66](5_DAO/SRC/DAO_LLR_MATRIX.py#L66)). 주석이 "비교에 사용되는 값"이라고 적고 있어 문서가 말하려던 것과 같다 | README 2.2.2와 3.2.5 코드 블록에서 줄을 지우고 `FERs` 설명을 "비교에 쓰는 FER"로 고친다 | 상 |
| `effective_FERs_partial` | README 286, 775 | 없음 | `LLR_MATRIX.FERs_partial` ([71](5_DAO/SRC/DAO_LLR_MATRIX.py#L71)) | 위와 같다 | 상 |
| `Read_LLR_from_File` | README 327 | 없음 | `LLR_MATRIX.Read_Input_LLR_Matrix` ([451](5_DAO/SRC/DAO_LLR_MATRIX.py#L451)) | 표의 이름을 바꾼다 | 상 |
| `Write_To_File` | README 328 | 없음 | `LLR_MATRIX.Save_Matrix` ([549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549)) | 표의 이름을 바꾼다 | 상 |
| `current_position` | DAO_spec 249 | 없음 | `ReorderState.current_donor_idx` ([260](5_DAO/SRC/DAO_Main.py#L260)) | 바꾼다 | 상 |
| `remaining_pool` | DAO_spec 251 | 없음 | `ReorderState.current_donor_pool` ([259](5_DAO/SRC/DAO_Main.py#L259)) | 바꾼다 | 상 |
| `best_matrix` | DAO_spec 252 | 없음 | `ReorderState.round_best_matrix` ([268](5_DAO/SRC/DAO_Main.py#L268)) | 바꾼다 | 상 |
| `Copy_Uncors(ch_idx, uncor_matrix_idx, test_mode)` | README 737 | 시그니처가 다름 | `Copy_Uncors(self, ch_idx, is_uncor_type_seed, test_mode)` ([1248](5_DAO/SRC/DAO_Main.py#L1248)) | README 3.2.4의 의사 코드를 실제 본문에 맞춰 다시 쓴다. 지금 의사 코드는 `TEST_MODE_DIR_NAME[test_mode]`로 경로를 나누지만 실제 본문에는 그런 분기가 없다 | 상 |
| `Test_LLR(matrix, test_mode=...)` | README 781, 790 | 인자가 없음 | `Test_LLR(self, matrix, is_test_initial, is_test_optimal, enable_early_channel_exit)` ([8937](5_DAO/SRC/DAO_Main.py#L8937)). 테스트 모드는 `self.current_test_mode`로 전달된다 | README 3.2.5의 의사 코드를 `self.current_test_mode = TestMode.PARTIAL` 뒤에 `Test_LLR(matrix)`를 부르는 꼴로 다시 쓴다 | 상 |
| `ECC_DIR` | DAO_spec 274 | 없음 | `PATH_CONFIG.ECC_DIR_NAME` ([443](5_DAO/SRC/DAO_Config.py#L443)) | 경로 예시의 자리표시를 `{ECC_DIR_NAME}`으로 바꾼다 | 중 |
| `WorkSpace/` | README 1181 | 없음 | `WORK_SPACE_DIR_NAME = "Work_Space"` ([90](5_DAO/SRC/DAO_Constants.py#L90)) | `Work_Space/`로 고친다 | 중 |
| `MODE_MAX_TRIAL_MAP` | DAO_spec 576 | 있음 (지역 변수) | `Set_Gen_Trial_LLR_Mode` 안의 지역 딕셔너리 ([8429](5_DAO/SRC/DAO_Main.py#L8429)) | 이름은 맞으므로 그대로 둔다. 다만 체크리스트를 보고 찾는 사람이 모듈 상수로 오해하지 않도록 "`Set_Gen_Trial_LLR_Mode` 안의 `MODE_MAX_TRIAL_MAP`"으로 자리를 적는다 | 하 |

### ㉡ 이름은 맞고 값이 다른 곳

| 항목 | 문서 위치 | 문서가 적은 값 | 코드 값 | 처방 | 우선 |
|------|----------|--------------|---------|------|------|
| `DAO_CONFIG.MAX_OPTIMIZATION_STAGE` | README 114, 879 | 500 | 9999 ([124](5_DAO/SRC/DAO_Config.py#L124)) | 9999로 고친다. 879줄 아래 "시퀀스 길이=9 → 55.5 사이클" 설명도 함께 지운다 | 상 |
| `DAO_CONFIG.MAX_OPTIMIZATION_TRIALS` | README 892 | 30 | 9999 ([125](5_DAO/SRC/DAO_Config.py#L125)) | 9999로 고친다 | 상 |
| `DAO_CONFIG.MAX_RUN_ECC_ERRORS` | README 955 | 5 | 9999 ([123](5_DAO/SRC/DAO_Config.py#L123)) | 9999로 고친다 | 상 |
| `DAO_CONFIG.Gen_LLR_Mode_SEQUENCE` | README 135, 916 | 9개 `[10, 11, 21, 30, 31, 40, 41, 50, 51]` | 12개 `[10, 11, 21, 30, 31, 40, 41, 42, 43, 50, 51, 70]` ([133](5_DAO/SRC/DAO_Config.py#L133)) | 12개로 고치고 빠진 42(INSERT_MUTATED_GROUP), 43(INSERT_MUTATED_ROW), 70(DELETE_ROW) 주석을 더한다 | 상 |
| `UNCOR_CONFIG.ENABLE_TWO_STAGE_TEST` | README 1019 | True | False ([200](5_DAO/SRC/DAO_Config.py#L200)) | False로 고친다 | 상 |
| `UNCOR_CONFIG.UNCOR_MATRIX_IDX` | README 1026 | `10 if not ENABLE_TWO_STAGE_TEST else -1` | `-1` (조건식 없음) ([206](5_DAO/SRC/DAO_Config.py#L206)) | `-1`로 고친다 | 상 |
| `TIME_CONFIG.MAX_STAGE_TIMEOUT_SECONDS` | README 1126 | `2 * 60 * 60` | `1 * 60 * 60` ([320](5_DAO/SRC/DAO_Config.py#L320)) | 이름과 값을 함께 고친다 | 상 |
| `TIME_CONFIG.MPI_COMM_TIMEOUT_SECONDS` | README 1132 | `1 * 60 * 60` (3600초) | `2*int(10*60) = 1200`초 ([323](5_DAO/SRC/DAO_Config.py#L323)) | 문서에는 "메모리 재시도 한계 시간의 2배로 계산한다"고 유도식을 적는다. 값 자체는 M팀 실마리 ㉲의 대상이므로 결론이 난 뒤 숫자를 적는다 | 상 |
| `SPEED_TEST_REFC_CONFIG.fn` | README 1085 | 50 | 1 ([229](5_DAO/SRC/DAO_Config.py#L229)) | 1로 고친다 | 상 |
| `SPEED_TEST_REFC_CONFIG.max_num_test` | README 1088 | 50 | 1 ([230](5_DAO/SRC/DAO_Config.py#L230)) | 1로 고친다 | 상 |
| `MUTATE_CONFIG.NUM_ELEMENTS_TO_MUTATE_CHTH` | README 1220 | 3 | 2 ([246](5_DAO/SRC/DAO_Config.py#L246)) | 2로 고친다 | 상 |
| `MUTATE_CONFIG.CSW_UPDATE_LIMIT_VALUE` | README 1235 | 무조건 128 | `ENABLE_CSW_UPDATE_LIMIT`이 참일 때만 정의된다 ([252](5_DAO/SRC/DAO_Config.py#L252)). 기본값이 False이므로 평소에는 속성 자체가 없다 | README에 `if ENABLE_CSW_UPDATE_LIMIT:` 블록을 그대로 보이고, 켰을 때만 생기는 값임을 적는다 | 상 |
| `MUTATE_CONFIG.ENABLE_CSW_UPDATE_LIMIT` 설명 | README 1229 | "CSW를 `CSW_UPDATE_LIMIT_VALUE` 이하로 제한" | 코드 주석은 "CSW가 한계값 미만인 row에 대해서만 mutation 수행" ([250](5_DAO/SRC/DAO_Config.py#L250)). 값의 상한이 아니라 mutation 대상 row를 고르는 기준이다 | 코드 주석 쪽 뜻으로 다시 쓴다 | 상 |
| `COPY_ROWS_CONFIG.MAX_EXTERNAL_CANDIDATES` | DAO_spec 270 | 기본 100 | 50 ([361](5_DAO/SRC/DAO_Config.py#L361)) | 50으로 고친다 | 상 |

### ㉢ 코드에 있고 문서에 없는 것

| 코드 이름 | 자리 | 처방 | 우선 |
|----------|------|------|------|
| `DAO_CONFIG.INITIAL_MATRIX_IDX_LIST`, `Get_Initial_Matrix_Idx_List` | [122](5_DAO/SRC/DAO_Config.py#L122), [139](5_DAO/SRC/DAO_Config.py#L139) | README 4.1.1에 더한다. 여러 매트릭스를 차례로 테스트하는 유일한 입구다 | 상 |
| `DAO_CONFIG.ENABLE_AVG_ITER_UPDATE` | [136](5_DAO/SRC/DAO_Config.py#L136) | README 4.1.1에 더한다. FER이 같을 때 평균 반복 횟수로 갱신을 허용하는 스위치라 결과에 직접 영향을 준다 | 상 |
| `SINGLE_ROW_CONFIG` (설정 8개) | [395](5_DAO/SRC/DAO_Config.py#L395) | README 4.1.9에 절을 새로 만든다. `RunDAOMode.GEN_SINGLE_ROW`와 짝이므로 둘을 같이 적는다 | 상 |
| `ADJUST_ITERATION_CONFIG` | [376](5_DAO/SRC/DAO_Config.py#L376) | README 4.1.9에 더한다. DAO_spec에도 없다 | 중 |
| `HBF_OPT_CONFIG` | [366](5_DAO/SRC/DAO_Config.py#L366) | README 4.1.9에 더한다 | 중 |
| `SPLIT_GROUP_CONFIG`, `GEN_INITIAL_GROUP_CONFIG`, `INSERT_MUTATED_GROUP_CONFIG`, `INSERT_MUTATED_ROW_CONFIG`, `COPY_GROUP_CONFIG` | [379](5_DAO/SRC/DAO_Config.py#L379) 이하 | DAO_spec 5장에는 있으나 README 4.1.9에 없다. README에서 DAO_spec 5장으로 넘기는 한 줄을 둔다 | 중 |
| `SPEED_TEST_REFC_CONFIG.RECHECK_INTERVAL_STAGES`, `RECHECK_INTERVAL_SECONDS` | [226](5_DAO/SRC/DAO_Config.py#L226) | README 4.1.4에 더한다. 주기적 속도 재측정을 켜는 유일한 자리다 | 상 |
| `TIME_CONFIG.MAX_ECC_MEMORY_RETRY`, `MAX_ECC_MEMORY_RETRY_DELAY` | [321](5_DAO/SRC/DAO_Config.py#L321) | README 4.1.6에 더한다. `MPI_COMM_TIMEOUT_SECONDS`가 이 둘에서 계산되므로 함께 보여야 한다 | 상 |
| `UNCOR_CONFIG.LEN_NO_PS` | [211](5_DAO/SRC/DAO_Config.py#L211) | README 4.1.3에 더한다 | 하 |
| `DEBUG_CONFIG`의 `ENABLE_PRINT_CLEAN_HISTORY`, `ENABLE_LLR_MATRIX_SAVE_LOGGING`, `IS_DEBUG_PAUSE_PRINT_SNAPSHOT`, `ENABLE_GET_RANDOM_STATE_FROM_CONFIG`, `RANDOM_STATE_TO_SET` | [326](5_DAO/SRC/DAO_Config.py#L326) 이하 | README 4.1.7에 더한다 | 중 |
| `MULTI_ROUND_MODES`, `MULTI_ROUND_FULL_ONLY_MODES`, `MULTI_ROUND_UPDATE_FUNC`, `MULTI_ROUND_INIT_FUNC` | [169](5_DAO/SRC/DAO_Constants.py#L169) 이하 | README 4.2절과 DAO_spec 7장에 더한다. 멀티라운드 모드를 새로 넣을 때 반드시 고쳐야 하는 네 표인데 지금 두 문서 어디에도 없다 | 상 |
| `Set_Configs_Manually`의 `SIM_IDX` 표 (10~12, 20~22, 30~32) | [22](5_DAO/SRC/DAO_Config.py#L22) 이하 | README 1장에 더한다. 실제로 실험을 시작하는 입구인데 문서에 없다 | 상 |

### ㉣ 문서 안의 변경 이력 서술 (프로젝트 규칙 "변경 이력은 `_pm/DONE.md`와 git이 담당" 위반)

| 자리 | 문구 | 처방 | 우선 |
|------|------|------|------|
| README [226](5_DAO/README.md#L226) | `# 코어 속도 테스트 관련 (신규)` | `(신규)`를 지운다 | 중 |
| README [354](5_DAO/README.md#L354), [366](5_DAO/README.md#L366), [378](5_DAO/README.md#L378), [385](5_DAO/README.md#L385) | `(신규 분리)`, `(신규)` | 괄호를 지운다 | 중 |
| README [1014](5_DAO/README.md#L1014), [1064](5_DAO/README.md#L1064), [1107](5_DAO/README.md#L1107), [1120](5_DAO/README.md#L1120) | 제목 뒤 `- 신규 클래스` | 제목에서 뺀다 | 중 |
| README [1285](5_DAO/README.md#L1285), [1294](5_DAO/README.md#L1294) | `(신규)`, `(단순화)` | 뺀다 | 중 |
| README [1305](5_DAO/README.md#L1305) | `MAX_CSW = 1408  # 최대 CSW 값 (1024 → 1408로 변경)` | `MAX_CSW = 1408  # 최대 CSW 값` | 중 |
| README [1309](5_DAO/README.md#L1309), [1311](5_DAO/README.md#L1311) | `(신규)` | 뺀다 | 중 |
| README [1440](5_DAO/README.md#L1440)~[1451](5_DAO/README.md#L1451) | `**업데이트:** 최신 변경사항 반영` 아래 변경 목록 12줄 | 절 전체를 지운다. 이력은 `5_DAO/_pm/DONE.md`와 git이 담당한다 | 중 |
| README [1021](5_DAO/README.md#L1021) | `- False: 기존 방식 (Full 테스트만 수행)` | `- False: Full 테스트만 수행` | 중 |

---

## ㉲ 링크 경로 오류 목록

두 문서의 마크다운 링크 34개 가운데 **33개가 이 저장소에 없는 경로를 가리킨다.** 전부 `DAO/SRC/...`로 시작하는데, 실제 소스는 `5_DAO/SRC/`에 있다. 살아 있는 링크는 README [1430](5_DAO/README.md#L1430)의 `[CLAUDE.md](CLAUDE.md)` 하나뿐이다.

| 문서 | 깨진 링크 수 | 줄 |
|------|------------|-----|
| `5_DAO/README.md` | 28 | 200, 235, 236, 237, 238, 239, 263, 327, 328, 329, 330, 332, 463, 487, 500, 513, 533, 547, 622, 635, 657, 733, 1386, 1404, 1431, 1432, 1433, 1434 |
| `5_DAO/DAO_spec.md` | 5 | 59, 600, 601, 602, 603 |

처방: `DAO/SRC/`를 `SRC/`로 일괄 치환한다. 두 문서 모두 `5_DAO/` 안에 있으므로 문서 기준 상대 경로 `SRC/DAO_Main.py`가 VSCode와 GitHub 모두에서 열린다. 치환 뒤 남은 `DAO/` 흔적이 없는지 다시 훑는다. 우선 상, 위험 없음.

링크에 붙은 줄 번호도 전부 어긋나 있다. 치환과 함께 고친다.

| 문서 위치 | 문서가 적은 줄 | 실제 줄 | 대상 |
|----------|--------------|---------|------|
| README 200 | `DAO_Main.py:255` | 481 | `class LLR_OPT` |
| README 239 | `DAO_Main.py:5313` | 9020 | `Test_Core_Speed` |
| README 263 | `DAO_LLR_MATRIX.py:34` | 34 (맞음) | `class LLR_MATRIX` |
| README 329 | `DAO_LLR_MATRIX.py:203` | 220 | `Deep_Copy` |
| README 330 | `DAO_LLR_MATRIX.py:242` | 266 | `Is_LLR_Valid` |
| README 1386 | `DAO_Config.py:35` | 135 | `INITIAL_TARGET_GROUP_IDX` (35줄은 `SIM_IDX == 10` 블록) |
| README 1404 | `DAO_Main.py:4627` | 7817 | `Update_Uncors_To_Input` |
| DAO_spec 59 | `DAO_LLR_MATRIX.py:266-449` | 266~449 (맞음) | `Is_LLR_Valid` |

줄 번호가 바로 낡는 것이 문제의 뿌리다. **처방: 함수 단위 링크에서는 줄 번호를 빼고 파일만 가리키며, 함수 이름을 본문에 적는다.** 예를 들어 README 200의 `#### 2.2.1 LLR_OPT ([DAO_Main.py:255](DAO/SRC/DAO_Main.py#L255))`을 `#### 2.2.1 LLR_OPT ([SRC/DAO_Main.py](SRC/DAO_Main.py)의 class LLR_OPT)`로 쓴다. 그러면 다음 수정 때 다시 틀어지지 않는다. 우선 상.

README 부록 A([1381](5_DAO/README.md#L1381))의 에러 문구 `Gen_LLR_Insert_Random_Group: Matrix must not be None`은 실제 코드와 마침표 하나만 다르다(코드는 [2594](5_DAO/SRC/DAO_Main.py#L2594)에서 `... must not be None.`). 같은 문구를 쓰는 함수가 10개이므로, 표의 항목을 `Gen_LLR_*: Matrix must not be None.`으로 넓혀 적는다. 우선 하.

---

## ㉳ Util 스크립트 표

| 파일 | 하는 일 | 실행 전제 | 사용법 안내 | 처방 | 우선 |
|------|--------|----------|-----------|------|------|
| [Util/check_result_files.py](5_DAO/Util/check_result_files.py) | 지정한 출력 디렉토리 아래 `Process_*` 폴더를 훑어 `result*.txt`가 없는 프로세스를 세어 출력한다 | 14줄 `dao_dir_path = r""`가 **빈 문자열**이다. 사용자가 이 줄을 고치지 않으면 언제나 "디렉토리를 찾을 수 없습니다"를 찍고 끝난다 | 모듈 docstring 2줄이 하는 일만 적고, 경로를 어디서 고치는지 말하지 않는다. 14줄 위 주석 `# ===== 여기에 DAO 디렉토리 절대 경로를 하드코딩하세요 =====`가 유일한 안내다 | ㉠ `sys.argv[1]`로 경로를 받고, 인자가 없으면 `dao_dir_path` 값을 쓰고, 그마저 비면 `사용법: python check_result_files.py <출력 세션 디렉토리>`를 찍고 끝낸다 ㉡ docstring에 `사용법:` 절을 더해 `Output/{session}/` 디렉토리를 가리킨다고 적는다 | 상 |
| [Util/remote_server_sync.py](5_DAO/Util/remote_server_sync.py) | paramiko SFTP로 원격 디렉토리를 로컬로 내려받고, 바뀐 파일만 받아 `sync_log.txt`에 기록한다. 기본은 1800초마다 되풀이한다 | ㉠ `paramiko` 설치 필요 ㉡ 28~41줄 `CONFIG` 딕셔너리에 접속 정보를 직접 적는다 (지금 값은 `your-server.com`, `your-username`, `C:\Users\you\.ssh\id_rsa` 같은 자리표시라 그대로는 접속되지 않는다) ㉢ `--host`, `--remote`, `--local`, `--interval`, `--once`를 argparse로 받는다 | docstring 6줄이 기능만 적고, `CONFIG`를 고쳐야 한다는 말도 CLI 인자가 있다는 말도 없다. argparse 도움말은 `-h`로만 보인다 | ㉠ docstring에 `사용법:` 절을 더해 `python remote_server_sync.py --once --host <주소> --remote <원격경로> --local <로컬경로>` 한 줄과 "되풀이 실행은 `--once`를 빼고 부른다"를 적는다 ㉡ `key_path`와 `password`는 CLI 인자가 없으므로 `CONFIG`에서 고쳐야 한다고 docstring에 명시한다 ㉢ `LOG_MAX_LINES = 10000`이 `DAO_Constants.py`의 같은 이름과 값을 따로 적고 있으니, 이 스크립트가 `SRC/`를 참조하지 않는 독립 도구임을 docstring 머리에 한 줄로 밝힌다 | 상 |
| [Util/merge_uecc.py](5_DAO/Util/merge_uecc.py) | 스크립트가 놓인 폴더 아래를 재귀로 훑어 `abc`로 시작하는 `.txt`를 모두 이어 붙여 `merged_output.txt`에 덧쓴다 | ㉠ **docstring이 하나도 없다** ㉡ 이 파일을 대상 폴더에 옮겨 놓고 실행하는 전제다 ㉢ 2줄 `INPUT_FILE_NAME_PREFIX = "abc"`를 대상 파일 접두로 바꿔야 한다 ㉣ 출력을 `"a"` 모드로 열어 덧쓰므로, 두 번 돌리면 같은 내용이 두 번 들어간다 | 없음 | ㉠ 모듈 docstring을 새로 쓴다: 하는 일, `이 파일을 대상 폴더에 넣고 python merge_uecc.py`, `INPUT_FILE_NAME_PREFIX`를 대상 접두로 고친다는 세 줄 ㉡ 파일 이름이 뜻을 가리지 않도록 `merge_uecc`를 `merge_text_files_by_prefix`로 바꾼다 (하는 일이 uecc 전용이 아니다) | 상 |
| [Util/rename_llr_idx.py](5_DAO/Util/rename_llr_idx.py) | 스크립트가 놓인 폴더의 `LLR_MATRIX_{idx}.txt` 파일 이름에서 idx를 N만큼 올린다 | ㉠ 이 파일을 대상 폴더에 옮겨 놓고 실행 ㉡ 17줄 `N = 500`을 바꿔야 한다 ㉢ 되돌리기가 없다 | **있다.** docstring에 `사용법: 이 파일을 대상 폴더에 넣고 실행 / python rename_llr_idx.py`가 적혀 있고 예시도 있다 | ㉠ `N`을 `sys.argv[1]`로도 받게 한다 ㉡ docstring에 "파일 이름만 바꾸고 파일 안의 내용은 건드리지 않는다"를 한 줄 더한다 (매트릭스 파일 본문에도 idx가 있는지 읽는 사람이 궁금해하는 자리다) | 중 |
| [Util/collect_llr_matrices.py](5_DAO/Util/collect_llr_matrices.py) | 스크립트가 놓인 폴더 아래의 `LLR_MATRIX_*.txt`를 중복 없이 `YYYYMMDD_HHMMSS/` 폴더로 모은다. 이름이 같고 내용이 다르면 `_dupN`을 붙여 남긴다 | ㉠ 이 파일을 `9_Single_Row_Candidates/` 같은 대상 폴더에 넣고 실행 ㉡ `collect()`는 `move`와 `dry_run` 인자를 받지만 `main()`이 둘 다 False로 고정해 부른다 | **있다.** docstring에 목적, 사용법, 중복 판정 규칙이 모두 적혀 있다. 8개 가운데 가장 잘 갖춰졌다 | ㉠ `--move`와 `--dry-run`을 argparse로 열어 준다. 안전한 예행 기능이 코드에 이미 있는데 사용자가 쓸 수 없다 ㉡ docstring 12, 13, 112줄의 줄표를 괄호로 바꾼다 (㉯ ㉠ 참조) | 중 |
| [Util/split_file.py](5_DAO/Util/split_file.py) | 텍스트 파일을 N줄씩 잘라 원본 폴더 아래 `1/`, `2/`, ... 폴더에 같은 이름으로 나눠 담는다 | 인자 두 개를 받는다. 원본은 그대로 둔다 | **있다.** `사용법: python split_file.py <파일경로> <라인수>`와 예시를 인자가 모자랄 때 찍는다 | ㉠ 모듈 docstring이 없으니 파일 머리에 한 줄 요약과 사용법을 적는다 (지금은 `split_file()` 함수 docstring에만 있다) ㉡ 출력 폴더가 이미 있으면 덮어쓴다는 점을 docstring에 적는다 | 중 |
| [Util/Mock_ECC.py](5_DAO/Util/Mock_ECC.py) | 외부 ECC 실행 파일의 출력 형식을 흉내 내어 `result_*.txt`와 `log_CSW_{rank}.txt`를 만든다 | ㉠ 인자 18개를 자리 순서대로 받는다 ㉡ numpy 필요 ㉢ PyInstaller로 exe를 만들어 쓰는 길도 있다 (`build_mock_ecc.bat`, `build_mock_ecc.sh`) | **가장 잘 갖춰졌다.** docstring에 사용법, 인자 18개 목록, 출력 파일 이름이 있고 별도 문서 [Util/README_Mock_ECC.md](5_DAO/Util/README_Mock_ECC.md)도 있다 | ㉠ 59줄 `MAX_CSW = 1024`가 `DAO_Constants.py`의 `MAX_CSW = 1408`과 어긋난다 (㉰ 참조). 값을 맞추거나, 일부러 다르게 둔 것이면 그 이유를 옆 주석에 적는다 ㉡ 6줄 `회사 외부에서 DAO 시스템의 동작을 검증할 때 사용합니다.`를 `외부 ECC 실행 파일 없이 DAO의 동작을 검증할 때 사용한다.`로 다시 쓴다 (실행 환경을 서술하지 않고 목적만 말한다) | 중 |
| [Util/fer_plot/fer_plot.py](5_DAO/Util/fer_plot/fer_plot.py) | 탭이나 공백으로 나뉜 표 데이터를 읽어 FER 곡선 그림을 `fig_YYMMDD_HH_MM_SS.png`로 저장한다 | ㉠ matplotlib 필요 ㉡ 인자로 데이터 파일 경로 하나 ㉢ 입력 파일 형식과 스타일 지정은 같은 폴더 `sample_data.txt`를 봐야 안다 ㉣ Times New Roman과 Malgun Gothic 글꼴을 쓴다 | 부분. docstring 4줄이 있고 `sample_data.txt`를 가리키지만, 스타일 키 이름(`color`, `marker`, `comments` 등)은 코드를 읽어야 안다 | ㉠ docstring에 `사용법: python fer_plot.py <데이터파일>`과 "출력은 데이터 파일과 같은 폴더에 저장된다"를 적는다 ㉡ 2줄의 줄표를 콜론으로 바꾼다 ㉢ `COLOR_MAP`, `MARKER_MAP`, `LINESTYLE_MAP`의 번호 체계가 `sample_data.txt`의 스타일 줄과 짝이라는 것을 docstring에 한 줄로 적는다 | 중 |

### Util 전체에 대한 처방

- ㉮ `5_DAO/Util/README.md`를 새로 쓴다. 위 표의 앞 세 열(파일, 하는 일, 실행 전제)을 그대로 옮긴 목록 하나면 충분하다. 지금은 `README_Mock_ECC.md` 하나만 있어서, 나머지 7개는 파일을 열어야 무엇인지 알 수 있다. 우선 상
- ㉯ `5_DAO/README.md`에서 그 목록으로 가는 링크를 한 줄 둔다. 지금 README는 `Util/install_requirements.bat` 한 줄만 언급한다. 우선 상
- ㉰ "이 파일을 대상 폴더에 옮겨 놓고 실행한다"는 전제를 가진 스크립트가 3개(`merge_uecc.py`, `rename_llr_idx.py`, `collect_llr_matrices.py`)다. 셋 다 `sys.argv[1]`로 대상 폴더를 받게 고치면 저장소 안의 파일을 옮기지 않아도 된다. 우선 중, 위험 없음 (인자가 없으면 지금처럼 자기 폴더를 쓰게 두면 된다)

---

## 처방 실행 순서와 옆 세션 충돌 주의

### 먼저 할 것 (동작 변경 없음, 옆 세션과 겹치지 않음)

- ㉮ `DAO_Main.py`의 줄표 17곳, 가운뎃점 3곳, U+FFFD 1곳을 고친다
- ㉯ ReorderState docstring의 허깨비 필드 3줄을 지우고, 과거 서술 주석 12곳을 다시 쓴다
- ㉰ Args 절 8곳과 `Set_Current_Optimal_Matrix` 설명 1곳을 고친다
- ㉱ `Raises:` 절 17곳을 `종료:` 절로 다시 쓴다
- ㉲ 두 문서의 `DAO/SRC/` 링크 33개를 `SRC/`로 바꾸고 줄 번호를 뺀다

### 그다음 (문서 다시 쓰기)

- ㉮ README의 이름 어긋남 18건과 값 어긋남 14건을 고친다
- ㉯ 문서에 없는 설정 13묶음을 더한다
- ㉰ 문서 안의 변경 이력 서술을 지운다

### 옆 세션(매트릭스 모델 분기 필드 확장)과 겹치는 자리

| 자리 | 겹치는 이유 | 처리 |
|------|-----------|------|
| `DAO_LLR_MATRIX.py`의 `get_line`([467](5_DAO/SRC/DAO_LLR_MATRIX.py#L467)), `Correct_Ch_Th_In_Row`([603](5_DAO/SRC/DAO_LLR_MATRIX.py#L603)) docstring | 분기 필드 추가가 같은 함수 본문을 고친다 | 옆 세션 반영 뒤에 손댄다 |
| README 2.2.2의 `LLR_MATRIX`, `LLR_Header`, `LLR_Row` 필드 목록 (263~325줄) | 분기 필드가 들어가면 이 목록이 다시 바뀐다 | 옆 세션 반영 뒤 한 번에 고친다. `effective_FERs` 두 줄만 먼저 지워도 된다 |
| DAO_spec 2.2, 2.3의 필드 표 | 위와 같다 | 옆 세션 반영 뒤에 고친다 |
| `"Partial"` 문자열 7곳과 `TEST_MODE_DIR_NAME` | T팀 실마리 ㉳이 이 상수를 살릴지 지울지 정한다 | T팀 결론 뒤에 손댄다 |
| `MPI_COMM_TIMEOUT_SECONDS` 문서 값 | M팀 실마리 ㉲이 값 자체를 바꿀 수 있다 | M팀 결론 뒤에 숫자를 적는다 |
| Mock_ECC의 `MAX_CSW = 1024` | 값을 1408로 맞추면 Mock 출력이 달라진다 | T팀 확인 뒤에 고친다 |

나머지 모든 처방은 주석, docstring, 로그 문구, 마크다운 문서만 건드리므로 옆 세션과 충돌하지 않는다.
