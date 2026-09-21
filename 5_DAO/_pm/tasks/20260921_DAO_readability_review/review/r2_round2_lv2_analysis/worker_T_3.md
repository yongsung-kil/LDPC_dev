# Worker T-3: uncor 파일과 세션 정리, Util (P9, P19)

> 시작 시점 커밋: 6e035e6 fix: 5_DAO uncor 아카이브가 optimal 대신 테스트한 매트릭스를 받도록 수정
> 기록: 2026-09-21 15:06:18

## 발견 요약

| # | 심각도 | 문제 | 위치 | 재현 조건 | 처방 |
|---|--------|------|------|----------|------|
| T3-1 | HIGH | 재디코딩 출력 파일(`redecode_uncor_seed_*.txt`)을 ECC 실행 전에 지우는 자리가 없어 Partial pool에 지난 라운드의 실패 프레임이 다시 섞인다 | [DAO_Main.py:8469](5_DAO/SRC/DAO_Main.py#L8469), [DAO_Main.py:1515](5_DAO/SRC/DAO_Main.py#L1515) | ENABLE_TWO_STAGE_TEST=True, LOAD_UNCOR_MODE=LOAD_SEED, optimal이 2회 이상 갱신되어 `Rebuild_Partial_Pool`이 2회 이상 도는 경우 | `Delete_Own_Uncors`에 `is_redecoded_uncor` 인자를 추가하고, `Set_Test_Environment` 8469줄 조건을 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`까지 넓혀 `is_redecoded_uncor=True`로 호출 |
| T3-2 | HIGH | `remote_server_sync.py`가 원격 스캔 실패를 오류로 집계하지 않아, 비거나 반쪽인 동기화 뒤에 이전 `server_sync_*` 폴더를 전부 되돌릴 수 없게 지운다 | [remote_server_sync.py:96](5_DAO/Util/remote_server_sync.py#L96), [remote_server_sync.py:210](5_DAO/Util/remote_server_sync.py#L210) | 원격 하위 디렉토리 나열이 실패하거나 `remote_path`가 비어 있는 상태로 30분 주기 실행 | `_scan`의 두 except 절에서 오류 목록에 항목을 추가하고, `delete_old_sync_folders` 호출 조건에 "내려받은 파일 수 > 0"과 "감지된 원격 파일 수 > 0"을 더한다 |
| T3-3 | HIGH | `Util/supercom/stop_after.sh`가 예제 Job ID(123456) 그대로 실행되면 그 번호 이상인 작업을 모두 정지시킨다 | [stop_after.sh:5](5_DAO/Util/supercom/stop_after.sh#L5) | 스크립트를 수정하지 않고 실행 | `MIN_JOBID`를 첫 번째 인자로 받고 값이 없으면 사용법을 출력하고 종료하도록 바꾸며, 정지 대상 목록을 먼저 출력하고 확인을 받는다 |
| T3-4 | MEDIUM | `Copy_Uncors`가 `test_mode` 인자를 본문에서 쓰지 않아 Partial 요청에도 Full 입력 파일을 복사한다 | [DAO_Main.py:1248](5_DAO/SRC/DAO_Main.py#L1248) | `Ensure_Uncors_Loaded`의 pool 미준비 분기로 들어가는 경우 (현재 설정 공간에서는 도달하지 않음) | `test_mode` 인자를 지우고 docstring에서 Partial 언급을 뺀다. 아울러 `Setup_Uncor_Pool`과 `Process_Uncors`의 `test_mode=` 전달을 제거한다 |
| T3-5 | MEDIUM | 입력 uncor 디렉토리 이름에 `.txt`가 붙는다. README는 확장자 없는 이름으로 적어, 문서대로 폴더를 만들면 시작하자마자 중단된다 | [DAO_Main.py:1276](5_DAO/SRC/DAO_Main.py#L1276), [README.md:724](5_DAO/README.md#L724), [README.md:1410](5_DAO/README.md#L1410) | `UNCOR_MATRIX_IDX >= 0`으로 두고 README대로 `HD/LLR_MATRIX_102/`에 uncor를 넣은 경우 | README 3.2.3과 6장 경로 예시를 `LLR_MATRIX_102.txt/`로 고친다. 코드를 바꾸려면 `Update_Uncors_To_Input`의 쓰기 경로도 같이 바꾸어야 한다 |
| T3-6 | MEDIUM | README 3.2.2부터 3.2.4까지가 존재하지 않는 설정과 상수를 설명한다 (`PARTIAL_UNCOR_MATRIX_IDX`, `FULL_UNCOR_MATRIX_IDX`, `TEST_MODE_DIR_NAME`) | [README.md:697](5_DAO/README.md#L697), [DAO_Constants.py:76](5_DAO/SRC/DAO_Constants.py#L76) | 문서를 읽고 설정하려는 모든 경우 | README 3.2.2부터 3.2.4를 Dynamic Partial 실제 동작으로 다시 쓰고, `TEST_MODE_DIR_NAME`을 `DAO_Constants.py`에서 지운다 |
| T3-7 | MEDIUM | 아카이브용 매트릭스 저장이 실패하면 최적화 전체가 중단된다 | [DAO_Main.py:2148](5_DAO/SRC/DAO_Main.py#L2148), [DAO_LLR_MATRIX.py:549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549) | 세션 디스크가 차거나 아카이브 경로 권한이 없는 상태에서 uncor 병합 도달 | 2148줄의 `Save_LLR_Matrix` 호출을 `try/except OSError`로 감싸고 경고만 기록한 뒤 계속 진행한다 |
| T3-8 | MEDIUM | `tmp_partial_uncors`와 `Redecoded_uncors`를 지우는 자리가 없어 optimal 갱신마다 하위 디렉토리가 늘어난다 | [DAO_Main.py:7501](5_DAO/SRC/DAO_Main.py#L7501), [DAO_Main.py:2109](5_DAO/SRC/DAO_Main.py#L2109), [DAO_Main.py:977](5_DAO/SRC/DAO_Main.py#L977) | 장시간 최적화에서 optimal이 수십 회 갱신되는 경우 | `Rebuild_Partial_Pool`이 새 디렉토리를 만든 직후 `tmp_partial_uncors` 아래에서 최신 하나를 남기고 나머지를 지우는 절차를 추가한다 |
| T3-9 | MEDIUM | `Gather_And_Archive_Uncors`가 `total_num_uncors`를 실패 프레임 수로 덮어써, 이후 Full uncor 수를 말하는 로그가 Partial 수를 가리킨다 | [DAO_Main.py:2144](5_DAO/SRC/DAO_Main.py#L2144), [DAO_Main.py:9330](5_DAO/SRC/DAO_Main.py#L9330) | ENABLE_TWO_STAGE_TEST=True로 `_Build_Initial_Partial_Pool`이 한 번이라도 돈 뒤의 모든 로그 | `Gather_And_Archive_Uncors`가 병합한 개수를 반환값에 담고, 호출처가 `total_num_uncors`나 `total_num_partial_uncors` 중 맞는 쪽에 넣는다 |
| T3-10 | MEDIUM | `Distribute_Uncors_To_Local_Session`이 `Delete_Uncors`를 uncor 종류 없이 불러, vector 모드에서 지난 내용을 지우지 못한 채 추가 모드로 덧붙인다 | [DAO_Main.py:1551](5_DAO/SRC/DAO_Main.py#L1551), [DAO_Main.py:1577](5_DAO/SRC/DAO_Main.py#L1577) | `Ensure_Uncors_Loaded`의 pool 미준비 분기에서 LOAD_VECTOR로 모드를 두 번 이상 전환 (현재 설정 공간에서는 도달하지 않음) | 1551줄을 `self.Delete_Uncors(ch_idx=ch_idx, is_uncor_type_seed=is_uncor_type_seed)`로 고친다. 이 분기 전체를 지우는 쪽이 더 낫다 (T3-14 참조) |
| T3-11 | MEDIUM | `check_result_files.py`의 빈 경로가 현재 디렉토리로 해석되어 존재 확인 가드가 통과하고 엉뚱한 곳을 훑는다 | [check_result_files.py:13](5_DAO/Util/check_result_files.py#L13) | 경로를 채우지 않고 실행 | 빈 문자열 검사를 앞에 두고 사용법을 출력한 뒤 종료한다. 경로는 첫 번째 명령행 인자로 받는다 |
| T3-12 | MEDIUM | `rename_llr_idx.py`가 확인 절차 없이 자기가 놓인 폴더의 LLR matrix 파일 이름을 한꺼번에 바꾼다 | [rename_llr_idx.py:15](5_DAO/Util/rename_llr_idx.py#L15) | 파일을 폴더에 넣고 실행 | 증가값을 명령행 인자로 받고, 바꿀 목록을 먼저 출력한 뒤 `--apply`가 있을 때만 `os.rename`을 부른다 |
| T3-13 | MEDIUM | `merge_uecc.py`가 결과 파일을 추가 모드로 열어 반복 실행마다 같은 내용을 덧붙인다 | [merge_uecc.py:21](5_DAO/Util/merge_uecc.py#L21) | 두 번 이상 실행 | 시작할 때 결과 파일을 한 번 새로 열고(`"w"`), 이후 같은 핸들에 이어 쓴다. 대상 접두사는 명령행 인자로 받는다 |
| T3-14 | LOW | `Ensure_Uncors_Loaded`의 pool 미준비 분기가 도달하지 않는데 그 안에 결함 두 개(T3-4, T3-10)가 들어 있다 | [DAO_Main.py:7377](5_DAO/SRC/DAO_Main.py#L7377) | 없음 (`Setup_Uncor_Pool`이 두 단계 테스트가 허용하는 모든 로드 모드에서 `is_uncor_pool_ready`를 True로 만든다) | 7377부터 7384까지의 else 분기를 지우고, 함께 죽는 `Distribute_Uncors_To_Local_Session`과 `Delete_Uncors`도 지운다 |
| T3-15 | LOW | `Cleanup_Session`이 `os.walk` 순회 중 하위 디렉토리를 통째로 지우면서 `dirs`를 줄이지 않는다 | [DAO_Main.py:996](5_DAO/SRC/DAO_Main.py#L996) | 항상 (마지막 정리 단계) | 디렉토리 삭제 루프를 `for dir_name in list(dirs):`로 돌리고 지운 이름을 `dirs.remove(dir_name)`으로 뺀다 |
| T3-16 | LOW | 지울 확장자 목록이 상수와 함수 안 지역 변수 두 벌로 갈라져 있다 | [DAO_Constants.py:128](5_DAO/SRC/DAO_Constants.py#L128), [DAO_Main.py:993](5_DAO/SRC/DAO_Main.py#L993) | 한쪽만 고칠 때 | `DAO_Constants.py`에 `SESSION_EXTENSIONS_TO_REMOVE = EXTENSIONS_TO_REMOVE + [".exe"]`를 두고 993줄에서 그것을 쓴다 |
| T3-17 | LOW | `Update_Uncors_To_Input`이 아카이브에 함께 저장된 LLR matrix 파일까지 uncor로 취급해 입력 트리에 복사한다 | [DAO_Main.py:7877](5_DAO/SRC/DAO_Main.py#L7877) | RUN_DAO_MODE가 SAVE_UNCOR 또는 REDECODE | 7877줄의 건너뛸 이름 검사에 현재 매트릭스 파일 이름 조건을 더한다 |
| T3-18 | LOW | `remote_server_sync.py`가 접속에 실패하면 만들어지지 않은 폴더에 로그를 쓰려다 주기 실행 루프가 죽는다 | [remote_server_sync.py:242](5_DAO/Util/remote_server_sync.py#L242) | 예제 호스트(`your-server.com`) 그대로 실행 | `write_sync_log`에서 `log_path.parent.mkdir(parents=True, exist_ok=True)`를 먼저 부른다 |
| T3-19 | LOW | `remote_server_sync.py`가 호스트 키를 확인 없이 받아들이고 접속 정보와 키 경로를 소스에 담는다 | [remote_server_sync.py:29](5_DAO/Util/remote_server_sync.py#L29), [remote_server_sync.py:118](5_DAO/Util/remote_server_sync.py#L118) | 실행할 때마다 | `CONFIG`를 같은 폴더의 설정 파일이나 환경 변수에서 읽고, 정책을 `RejectPolicy`로 바꾼 뒤 `load_system_host_keys()`를 쓴다 |
| T3-20 | LOW | `Mock_ECC.py`가 uncor 파일을 읽지도 쓰지도 않아 두 단계 테스트 경로를 흉내 내지 못한다 | [Mock_ECC.py:224](5_DAO/Util/Mock_ECC.py#L224) | ENABLE_TWO_STAGE_TEST=True로 Mock을 쓰는 경우 | `seed_mode`가 uncor 저장을 뜻할 때 `uncor_seed_*` 또는 `redecode_uncor_seed_*` 파일에 생성한 에러 수만큼 줄을 쓰도록 `run`에 추가한다 |
| T3-21 | LOW | `split_file.py`가 원본 폴더 아래 같은 번호 폴더의 동명 파일을 말없이 덮어쓴다 | [split_file.py:47](5_DAO/Util/split_file.py#L47) | 같은 파일을 두 번 분할하거나 대상 폴더에 `1/`, `2/`가 이미 있는 경우 | 출력 폴더를 `{원본이름}_split/{n}/`으로 두고, 그 폴더가 이미 있으면 안내 후 종료한다 |

## 발견 상세

### T3-1 (HIGH) 재디코딩 출력 uncor 파일이 지워지지 않는다

`Set_Test_Environment`는 ECC 실행 직전에 자기 프로세스의 uncor 작업 파일을 지운다. 다만 그 조건이 `SAVE_UNCOR_SEED` 한 가지다.

- [DAO_Main.py:8469](5_DAO/SRC/DAO_Main.py#L8469)
  ```python
  if self.current_seed_mode == SeedMode.SAVE_UNCOR_SEED:
      self.Delete_Own_Uncors(ch_idx=ch_idx)
  ```

`Delete_Own_Uncors`([DAO_Main.py:1515](5_DAO/SRC/DAO_Main.py#L1515))는 `Get_Uncor_File_Name(..., is_redecoded_uncor=False)`가 만드는 이름, 곧 `uncor_seed_...txt`만 지운다. 두 단계 테스트가 쓰는 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED` 모드에서는 ECC가 입력으로 `uncor_seed_...txt`를 읽고 출력으로 `redecode_uncor_seed_...txt`를 쓰는데, 그 출력 파일을 지우는 자리가 소스 전체에 없다. `Cleanup_Test_Environment`([DAO_Main.py:935](5_DAO/SRC/DAO_Main.py#L935))가 지우는 대상은 `result`, `log_CSW`, `Ref_C_result`로 시작하는 이름과 `.bat`, `.sh`, `.tmp` 확장자뿐이고, `Load_Uncors_From_Pool`([DAO_Main.py:7505](5_DAO/SRC/DAO_Main.py#L7505))이 지우는 대상도 재디코딩 접두사가 없는 이름이다.

`Gather_And_Archive_Uncors`([DAO_Main.py:2127](5_DAO/SRC/DAO_Main.py#L2127))는 그 `redecode_uncor_seed_...txt`를 모든 프로세스에서 읽어 하나로 합친 뒤 Partial pool의 원본으로 쓴다. 결과로 두 가지가 생긴다.

- ㉮ DAO가 `SAVE_UNCOR_SEED`에서 굳이 실행 전 삭제를 하는 것은 외부 ECC가 uncor 출력 파일을 추가 모드로 연다는 뜻이다. 같은 성질이 재디코딩 출력에도 적용되면, `Rebuild_Partial_Pool`이 돌 때마다 각 프로세스의 파일이 지난 라운드 내용 위에 쌓이고, Partial pool이 매번 부풀며 이미 복호에 성공한 프레임까지 실패 프레임으로 계속 들어간다.
- ㉯ 외부 ECC가 덮어쓰기로 연다고 해도, 이번 라운드에 ECC를 건너뛴 프로세스의 파일은 그대로 남는다. `Run_ECC`([DAO_Main.py:7931](5_DAO/SRC/DAO_Main.py#L7931))는 `has_uncor[ch_idx]`가 False면 바로 돌아오고, `Gather_And_Archive_Uncors`는 제외된 코어만 건너뛸 뿐 활성 코어이면서 uncor를 못 받은 프로세스의 지난 파일은 그대로 병합한다. 주기 재점검(`_Redistribute_Uncor_Pool_Uniform`, [DAO_Main.py:9158](5_DAO/SRC/DAO_Main.py#L9158))이 활성 코어 목록을 바꾸면 어느 프로세스가 uncor를 받는지가 달라지므로 이 상황이 실제로 만들어진다.

두 경우 모두 Partial FER이 현재 optimal 기준의 실패 프레임이 아닌 집합 위에서 계산되므로, Partial 단계의 선별 판정이 틀린 근거로 내려진다.

**처방**

- ㉮ `Delete_Own_Uncors` 서명을 `def Delete_Own_Uncors(self, ch_idx: int = 0, is_uncor_type_seed: bool = True, is_redecoded_uncor: bool = False)`로 넓히고, 1522줄의 `Get_Uncor_File_Name` 호출에 `is_redecoded_uncor=is_redecoded_uncor`를 넘긴다
- ㉯ [DAO_Main.py:8469](5_DAO/SRC/DAO_Main.py#L8469)를 다음으로 바꾼다
  ```python
  if self.current_seed_mode == SeedMode.SAVE_UNCOR_SEED:
      self.Delete_Own_Uncors(ch_idx=ch_idx)
  elif self.current_seed_mode == SeedMode.LOAD_UNCOR_SEED_SAVE_UNCOR_SEED:
      self.Delete_Own_Uncors(ch_idx=ch_idx, is_redecoded_uncor=True)
  ```

### T3-2 (HIGH) 원격 동기화가 실패를 성공으로 보고 이전 결과를 지운다

`sync_directory`는 오류가 하나도 없을 때 이전 동기화 폴더를 전부 지운다.

- [remote_server_sync.py:210](5_DAO/Util/remote_server_sync.py#L210)
  ```python
  if not result["errors"]:
      logger.info("동기화 성공 - 이전 폴더 정리 중...")
      delete_old_sync_folders(base_path, sync_folder_name)
  ```

`delete_old_sync_folders`는 `Path(config["local_path"]).glob("server_sync_*")`에 걸리는 디렉토리를 `shutil.rmtree`로 지운다([remote_server_sync.py:96](5_DAO/Util/remote_server_sync.py#L96)). 그런데 원격 목록 수집 쪽의 실패는 오류 목록에 들어가지 않는다.

- [remote_server_sync.py:67](5_DAO/Util/remote_server_sync.py#L67)
  ```python
  except PermissionError:
      logger.warning(f"권한 없음 (스킵): {current_remote}")
      return
  except Exception as e:
      logger.error(f"스캔 실패 (스킵): {current_remote} - {e}")
      return
  ```

따라서 원격 하위 트리를 읽지 못하거나 `remote_path`가 비어 있으면 `remote_files`가 비고, 내려받은 파일이 없고, 오류 목록도 비어 있으므로 "성공"으로 판정되어 이전에 받아 둔 동기화 폴더가 전부 사라진다. 기본 동작이 30분 주기 반복이라 한 번 이런 상태가 되면 사람이 보기 전에 결과가 없어진다.

**처방**

- ㉮ `_scan`의 두 except 절에서 상위로 오류를 알릴 수 있도록 `file_map` 대신 `(file_map, scan_errors)`를 반환하고, `sync_directory`에서 `result["errors"].extend(scan_errors)`를 수행한다
- ㉯ [remote_server_sync.py:210](5_DAO/Util/remote_server_sync.py#L210) 조건을 `if not result["errors"] and remote_files and result["downloaded"]:`로 좁힌다
- ㉰ `delete_old_sync_folders`에 `dry_run` 인자를 두고 기본값을 True로 하여, 실제 삭제는 명령행에서 `--prune`을 줄 때만 일어나게 한다

### T3-3 (HIGH) 클러스터 작업 정지 스크립트의 예제 Job ID

[stop_after.sh:5](5_DAO/Util/supercom/stop_after.sh#L5)의 `MIN_JOBID=123456`은 예제 값이다. 스크립트는 이 값 이상 번호의 작업을 상태와 무관하게 전부 `bstop`한다. 운영 중인 LSF 클러스터의 Job ID는 대개 이 값을 훨씬 넘기므로, 값을 고치지 않고 실행하면 그 사용자가 제어할 수 있는 작업이 사실상 모두 정지한다. 확인 절차나 대상 미리보기가 없다.

`stop_after_max.sh`도 현재 실행 중 최대 번호보다 큰 작업을 모두 정지시키며, 이 대상은 보통 방금 제출해 대기 중인 작업이다. 확인 절차가 없는 것은 같다.

**처방**

- ㉮ `MIN_JOBID`를 첫 번째 명령행 인자로 받고, 인자가 없으면 사용법을 출력하고 종료한다
- ㉯ `bstop`을 걸기 전에 대상 목록을 출력하고 확인 입력을 받는다
- ㉰ 두 스크립트 모두 머리에 "대상 확인 없이 실행하면 안 된다"는 주석을 붙인다

### T3-4 (MEDIUM) `Copy_Uncors`의 `test_mode`가 쓰이지 않는다

[DAO_Main.py:1248](5_DAO/SRC/DAO_Main.py#L1248)의 서명에 `test_mode: TestMode = TestMode.FULL`이 있지만 본문(1266줄부터 1305줄)은 `UNCOR_CONFIG.UNCOR_MATRIX_IDX` 하나로만 경로를 정하고 `test_mode`를 한 번도 읽지 않는다. docstring 자체가 "TestMode.FULL. (Partial은 Dynamic Partial에서 동적 생성)"이라 적어 인자가 뜻을 잃었음을 드러낸다.

호출처는 두 곳이다.

- ㉮ [DAO_Main.py:7482](5_DAO/SRC/DAO_Main.py#L7482) `Setup_Uncor_Pool`. `modes = [TestMode.FULL]`이므로 언제나 FULL이다
- ㉯ [DAO_Main.py:7336](5_DAO/SRC/DAO_Main.py#L7336) `Process_Uncors`. 이쪽은 `Ensure_Uncors_Loaded`의 pool 미준비 분기에서 PARTIAL이 들어올 수 있다

㉯에서 PARTIAL이 들어오면 Full 입력 파일이 복사되는데도 `current_loaded_test_mode`는 PARTIAL로 기록되어([DAO_Main.py:7384](5_DAO/SRC/DAO_Main.py#L7384)), Partial 단계가 Full uncor 전부를 돌리면서도 Partial로 기록된다. 다만 T3-14에서 보듯 이 분기는 현재 설정 공간에서 도달하지 않는다. 그래서 오늘의 영향은 없고, 인자가 남아 있는 한 다음 호출자가 같은 함정에 빠진다.

**처방** `Copy_Uncors`에서 `test_mode` 인자를 지우고, 두 호출처의 `test_mode=` 전달도 지운다. docstring의 Partial 문장을 빼고 "Full uncor를 Input에서 세션으로 복사한다"로 다시 쓴다.

### T3-5, T3-6 (MEDIUM) uncor 입력 경로와 README의 불일치

`Copy_Uncors`가 만드는 입력 경로는 다음과 같다.

- [DAO_Main.py:1272](5_DAO/SRC/DAO_Main.py#L1272) `base_uncor_dir = INPUT_UNCOR_DIR_PATH / MODE_MAP[init_n]`
- [DAO_Main.py:1276](5_DAO/SRC/DAO_Main.py#L1276) `LLR_matrix_file_name = PATH_CONFIG.LLR_MATRIX_FILE_NAME_TEMPLATE.format(matrix_idx=uncor_matrix_idx)` 이어서 `src_dir = base_uncor_dir / LLR_matrix_file_name`

`LLR_MATRIX_FILE_NAME_TEMPLATE`은 `"LLR_MATRIX_{matrix_idx}.txt"`이므로([DAO_Config.py:438](5_DAO/SRC/DAO_Config.py#L438)) 디렉토리 이름이 `LLR_MATRIX_102.txt`가 된다. 파일 이름 서식을 디렉토리 이름으로 다시 쓴 결과다. `Update_Uncors_To_Input`([DAO_Main.py:7838](5_DAO/SRC/DAO_Main.py#L7838))도 같은 이름을 써서 코드 안쪽은 일관되지만, README는 세 곳에서 확장자 없는 이름으로 적는다([README.md:717](5_DAO/README.md#L717), [README.md:724](5_DAO/README.md#L724), [README.md:1410](5_DAO/README.md#L1410)). 문서대로 폴더를 만들면 `src_path.exists()`가 거짓이 되어 [DAO_Main.py:1294](5_DAO/SRC/DAO_Main.py#L1294)의 `MPI_Abort`로 실행이 시작 단계에서 멈춘다.

README 3.2절은 그 밖에도 소스에 없는 것을 설명한다.

- ㉮ `UNCOR_CONFIG.PARTIAL_UNCOR_MATRIX_IDX`와 `UNCOR_CONFIG.FULL_UNCOR_MATRIX_IDX`([README.md:697](5_DAO/README.md#L697))는 `DAO_Config.py`와 `DAO_Main.py` 어디에도 없다. `UNCOR_CONFIG`에는 `UNCOR_MATRIX_IDX` 하나만 있다([DAO_Config.py:206](5_DAO/SRC/DAO_Config.py#L206))
- ㉯ README 3.2.3이 그리는 `HD/Partial/`, `HD/Full/` 입력 트리는 코드가 만들지 않는다. Partial uncor는 입력에서 읽지 않고 Full 테스트의 실패 프레임에서 만들어진다(`_Build_Initial_Partial_Pool`, [DAO_Main.py:9285](5_DAO/SRC/DAO_Main.py#L9285))
- ㉰ README 3.2.4의 `Copy_Uncors` 예시는 `uncor_matrix_idx`를 인자로 받고 `TEST_MODE_DIR_NAME[test_mode]`를 읽지만, 실제 함수는 그 인자를 받지 않고 설정에서 직접 읽으며 `TEST_MODE_DIR_NAME`을 쓰지 않는다
- ㉱ `TEST_MODE_DIR_NAME`([DAO_Constants.py:76](5_DAO/SRC/DAO_Constants.py#L76))을 읽는 자리는 `5_DAO/SRC` 전체에 없다. FULL 항목이 없어도 `KeyError`가 날 자리가 없다는 뜻이다. Partial 문자열은 `Get_Test_Mode_String`([DAO_Main.py:1662](5_DAO/SRC/DAO_Main.py#L1662))과 각 함수 안의 문자열 상수로 따로 만들어진다
- ㉲ README는 입력 uncor 파일 이름을 `ch_1_uncor_0.bin`으로 적지만 실제 이름은 `Get_Uncor_File_Name`([DAO_Main.py:2072](5_DAO/SRC/DAO_Main.py#L2072))이 만드는 `uncor_seed_H_{matrix_sel}_CH_{ch_type}_...{process_idx}.txt`와 `uncor_vector_...dat`다

**처방**

- ㉮ README 3.2.2부터 3.2.4까지를 Dynamic Partial 실제 흐름으로 다시 쓴다. 설정은 `ENABLE_TWO_STAGE_TEST`와 `UNCOR_MATRIX_IDX` 둘만 남기고, Partial 입력 트리 그림을 지운다
- ㉯ 입력 디렉토리 이름을 `LLR_MATRIX_102.txt/`로 고치고, 입력 파일 이름 예시를 `Get_Uncor_File_Name`의 실제 서식으로 바꾼다
- ㉰ `DAO_Constants.py`에서 `TEST_MODE_DIR_NAME`을 지운다. 문자열이 필요하면 `Get_Test_Mode_String` 하나로 모은다

### T3-7 (MEDIUM) 아카이브 저장 실패가 실행 전체를 끝낸다

[DAO_Main.py:2148](5_DAO/SRC/DAO_Main.py#L2148)에서 `Gather_And_Archive_Uncors`는 병합을 마친 뒤 `self.Save_LLR_Matrix(matrix, target_dir=str(dest_dir))`를 부른다. 그 끝에 있는 `Save_Matrix`([DAO_LLR_MATRIX.py:549](5_DAO/SRC/DAO_LLR_MATRIX.py#L549))는 실패하면 `OSError`를 다시 던진다.

```python
except OSError as e:
    raise OSError(f"Save_Matrix failed: {save_path} - {e}") from e
```

`Gather_And_Archive_Uncors`는 이것을 잡지 않으므로 예외가 모듈 끝의 `Main()` 처리기([DAO_Main.py:10404](5_DAO/SRC/DAO_Main.py#L10404))까지 올라가 `MPI_Abort`로 이어진다. root에서만 일어나는 일이므로 나머지 rank는 통신 도중 강제 종료된다.

같은 성격의 파일 조작인데도 대응이 제각각이다.

- ㉮ `Cleanup_Test_Environment`([DAO_Main.py:958](5_DAO/SRC/DAO_Main.py#L958))는 삭제 실패를 경고로 기록하고 계속한다
- ㉯ `Delete_Uncors`와 `Delete_Own_Uncors`도 경고 후 계속한다
- ㉰ `_Setup_Uncor_Pool_For_Channel`([DAO_Main.py:7447](5_DAO/SRC/DAO_Main.py#L7447))은 `MPI_Abort`를 부른다
- ㉱ `Gather_And_Archive_Uncors`의 매트릭스 저장은 예외를 그대로 올린다

㉰의 중단은 타당하다. pool 파일을 못 쓰면 다음 테스트가 성립하지 않는다. ㉱는 재현용 보관물이라 실행을 이어가도 되는데 중단시킨다. 장시간 돌린 최적화가 아카이브 저장 하나 때문에 끝난다.

**처방** [DAO_Main.py:2148](5_DAO/SRC/DAO_Main.py#L2148)을 다음처럼 다시 쓴다.

```python
try:
    self.Save_LLR_Matrix(matrix, target_dir=str(dest_dir))
    self.Write_Log_Lines(f"[LLR Matrix Archived]: {dest_dir / LLR_matrix_file_name}")
except OSError as error:
    self.Write_Log_Lines(f"[WARN] LLR matrix 아카이브 저장 실패, 계속 진행: {dest_dir} - {error}")
```

### T3-8 (MEDIUM) 임시 Partial uncor 디렉토리가 계속 늘어난다

`_Get_Tmp_Partial_Uncor_Dir`([DAO_Main.py:7491](5_DAO/SRC/DAO_Main.py#L7491))은 매트릭스 파일 이름을 하위 디렉토리 이름으로 쓴다. `Rebuild_Partial_Pool`([DAO_Main.py:9394](5_DAO/SRC/DAO_Main.py#L9394))은 optimal이 갱신될 때마다 그 이름으로 새 디렉토리를 만들고 채널 수만큼 파일을 복사한다. optimal의 `matrix_idx`는 시도마다 늘어나는 `current_LLR_matrix_idx`([DAO_Main.py:2347](5_DAO/SRC/DAO_Main.py#L2347))를 물려받으므로 갱신마다 이름이 달라진다.

이 디렉토리를 지우는 자리가 소스에 없다. `Cleanup_Session`([DAO_Main.py:977](5_DAO/SRC/DAO_Main.py#L977))은 `.exe`, `.bat`, `.sh`, `.tmp` 파일과 `Process`로 시작하는 디렉토리만 지우고, `5_Uncors` 아래의 `tmp_partial_uncors`, `Copied_uncors`, `Redecoded_uncors`는 건드리지 않는다. 같은 구조로 `Redecoded_uncors/{매트릭스 이름}/`도 갱신마다 늘고, 커밋 6e035e6 이후로는 각 디렉토리가 매트릭스 텍스트 파일 한 벌을 더 담는다.

덧붙여 `_Redistribute_Uncor_Pool_Uniform`([DAO_Main.py:9187](5_DAO/SRC/DAO_Main.py#L9187))은 쌓인 하위 디렉토리 중 수정 시각이 가장 늦은 것을 고른다.

```python
subdirs = [d for d in tmp_partial_base.iterdir() if d.is_dir()]
if subdirs:
    partial_src_dir = str(max(subdirs, key=lambda d: d.stat().st_mtime))
```

파일 복사나 백업 도구가 지난 디렉토리의 수정 시각을 건드리면 현재 optimal과 무관한 실패 프레임 집합이 Partial pool로 들어간다. 고른 디렉토리 이름과 현재 optimal 이름이 같은지 확인하지 않는다.

**처방**

- ㉮ `Rebuild_Partial_Pool`이 채널 루프를 마친 뒤 `tmp_partial_uncors` 아래에서 방금 만든 디렉토리만 남기고 나머지를 지우는 절차를 넣는다. `Redecoded_uncors`는 진단 자료이므로 유지한다
- ㉯ `_Redistribute_Uncor_Pool_Uniform`이 수정 시각 대신 `self.optimal_LLR_matrix.Get_LLR_Matrix_File_Name()`으로 디렉토리를 직접 지목하게 바꾸고, 그 이름이 없으면 재분배를 건너뛴다

### T3-9 (MEDIUM) `total_num_uncors`가 Partial 수로 덮인다

`Gather_And_Archive_Uncors`는 병합 결과를 세어 `self.total_num_uncors[ch_idx]`에 넣는다([DAO_Main.py:2144](5_DAO/SRC/DAO_Main.py#L2144)). `_Build_Initial_Partial_Pool`과 `Rebuild_Partial_Pool`은 이것을 실패 프레임 수로 쓰려고 `total_num_partial_uncors`에 복사하는데([DAO_Main.py:9330](5_DAO/SRC/DAO_Main.py#L9330), [DAO_Main.py:9416](5_DAO/SRC/DAO_Main.py#L9416)), 원본인 `total_num_uncors`는 되돌리지 않는다. 주석도 그 사실을 인정한다("Gather_And_Archive_Uncors가 total_num_uncors를 갱신했으므로 복사").

그 뒤로 `total_num_uncors`는 Full uncor 수가 아니라 마지막 실패 프레임 수를 담는다. FER 계산은 `num_tests`와 `num_errors`로 하므로 수치 결과는 어긋나지 않고, 영향은 로그와 `Setup_Uncors`의 0 검사([DAO_Main.py:8740](5_DAO/SRC/DAO_Main.py#L8740))에 한정된다. 다만 진단 로그가 Full uncor 수를 말하는 자리에서 Partial 수를 보여 주므로 성능 분석을 오도한다.

**처방** `Gather_And_Archive_Uncors`가 상태를 건드리는 대신 병합 개수를 돌려주게 바꾼다. 반환을 `(dest_path, num_merged)`로 하고, `Process_Uncors`는 `total_num_uncors`에, `_Build_Initial_Partial_Pool`과 `Rebuild_Partial_Pool`은 `total_num_partial_uncors`에 넣는다.

### T3-10, T3-14 (MEDIUM, LOW) 도달하지 않는 직렬 분배 경로

`Ensure_Uncors_Loaded`([DAO_Main.py:7377](5_DAO/SRC/DAO_Main.py#L7377))에는 pool이 준비되지 않았을 때의 대비 경로가 있다.

```python
if self.is_uncor_pool_ready:
    self.Load_Uncors_From_Pool(test_mode)
else:
    is_uncor_type_seed = (UNCOR_CONFIG.LOAD_UNCOR_MODE == DAOLoadUncorMode.LOAD_SEED)
    self.Process_Uncors(is_setup_stage=True, is_uncor_type_seed=is_uncor_type_seed,
                       should_distribute_uncors=True, test_mode=test_mode)
    self.current_loaded_test_mode = test_mode
```

이 else 분기는 현재 설정 공간에서 실행되지 않는다. `Ensure_Uncors_Loaded`는 `ENABLE_TWO_STAGE_TEST`가 거짓이면 바로 돌아가고([DAO_Main.py:7360](5_DAO/SRC/DAO_Main.py#L7360)), 참일 때 `LOAD_UNCOR_MODE=LOAD_NONE` 조합은 설정 검증이 막는다([DAO_Main.py:9798](5_DAO/SRC/DAO_Main.py#L9798)). 남는 LOAD_SEED와 LOAD_VECTOR에서는 `Setup_Uncor_Pool`([DAO_Main.py:7466](5_DAO/SRC/DAO_Main.py#L7466))이 끝까지 진행해 `is_uncor_pool_ready`를 True로 만들고, `_Redistribute_Uncor_Pool_Uniform`도 리셋 직후 `Setup_Uncor_Pool`을 다시 불러 True로 되돌린다.

이 죽은 분기에 딸린 함수 둘에 결함이 있다.

- ㉮ `Distribute_Uncors_To_Local_Session`([DAO_Main.py:1551](5_DAO/SRC/DAO_Main.py#L1551))이 `self.Delete_Uncors(ch_idx=ch_idx)`를 부른다. `Delete_Uncors`의 `is_uncor_type_seed` 기본값이 True이므로 항상 seed 이름(`uncor_seed_...txt`)만 지운다. 그런데 같은 함수가 파일을 쓸 때는 `is_uncor_type_seed=is_uncor_type_seed`로 이름을 만들고 추가 모드로 연다([DAO_Main.py:1577](5_DAO/SRC/DAO_Main.py#L1577)). LOAD_VECTOR에서는 `uncor_vector_...dat`를 지우지 못한 채 덧붙이므로, 모드를 전환할 때마다 각 프로세스의 vector 파일이 두 배, 세 배로 늘어난다
- ㉯ 같은 분기의 `is_uncor_type_seed` 계산식이 다른 자리와 다르다. `_Build_Initial_Partial_Pool`([DAO_Main.py:9294](5_DAO/SRC/DAO_Main.py#L9294))과 `Rebuild_Partial_Pool`([DAO_Main.py:9382](5_DAO/SRC/DAO_Main.py#L9382))은 `!= LOAD_VECTOR`를 쓰고, 이 분기와 `Load_Uncors_From_Pool`([DAO_Main.py:7513](5_DAO/SRC/DAO_Main.py#L7513))은 `== LOAD_SEED`를 쓴다. LOAD_NONE에서만 결과가 갈리는데 그 조합은 검증이 막으므로 지금은 같은 값이 나온다. 식이 두 벌이라 앞으로 로드 모드가 늘면 어긋난다

**처방**

- ㉮ [DAO_Main.py:7377](5_DAO/SRC/DAO_Main.py#L7377)부터 7384까지의 else 분기를 지우고, `is_uncor_pool_ready`가 거짓이면 `MPI_Abort`로 설정 오류를 알린다
- ㉯ 함께 죽는 `Distribute_Uncors_To_Local_Session`([DAO_Main.py:1531](5_DAO/SRC/DAO_Main.py#L1531))과 `Delete_Uncors`([DAO_Main.py:1490](5_DAO/SRC/DAO_Main.py#L1490)), 그리고 `Process_Uncors`의 `should_distribute_uncors` 인자를 지운다
- ㉰ 분기를 남기기로 한다면 1551줄에 `is_uncor_type_seed=is_uncor_type_seed`를 넘기고, `is_uncor_type_seed` 계산을 메서드 하나로 모은다

### T3-15, T3-16 (LOW) 세션 정리의 순회와 확장자 목록

`Cleanup_Session`([DAO_Main.py:996](5_DAO/SRC/DAO_Main.py#L996))은 `os.walk` 순회 중 `Process`로 시작하는 하위 디렉토리를 `shutil.rmtree`로 지우면서 `dirs` 목록에서 빼지 않는다. `os.walk`는 지워진 경로로 내려가려다 `os.scandir`에서 오류를 만나는데, 기본값 `onerror=None`이라 조용히 건너뛴다. 예외로 이어지지는 않고 헛도는 순회만 남는다.

지울 확장자 목록은 두 벌이다.

- ㉮ [DAO_Constants.py:128](5_DAO/SRC/DAO_Constants.py#L128) `EXTENSIONS_TO_REMOVE = [".bat", ".sh", ".tmp"]`. `Cleanup_Test_Environment`가 쓴다
- ㉯ [DAO_Main.py:993](5_DAO/SRC/DAO_Main.py#L993) `extensions_to_remove = [".exe", ".bat", ".sh", ".tmp"]`. `Cleanup_Session`의 지역 변수다

한쪽에 확장자를 더하면 다른 쪽이 따라가지 않는다.

**처방**

- ㉮ 디렉토리 삭제 루프를 `for dir_name in list(dirs):`로 돌리고, 지운 이름을 `dirs.remove(dir_name)`으로 빼 순회에서 제외한다
- ㉯ `DAO_Constants.py`에 `SESSION_EXTENSIONS_TO_REMOVE = EXTENSIONS_TO_REMOVE + [".exe"]`를 두고 993줄의 지역 목록을 그것으로 바꾼다

`Cleanup_Session`이 지운 뒤에도 진단 자료는 남는다. 오류 로그는 `session_dir/6_Error_Log/`에 있고([DAO_Main.py:2553](5_DAO/SRC/DAO_Main.py#L2553)) 프로세스 디렉토리 안에 있지 않다. 로그 디렉토리, `2_Optimal_LLR_matrix`, `5_Uncors`도 그대로 남는다.

시점도 문제없다. `Main`([DAO_Main.py:10020](5_DAO/SRC/DAO_Main.py#L10020))이 `MPI_Barrier` 뒤에 root만 `Cleanup_Session`을 부르고 그 뒤에 다시 `MPI_Barrier`를 두므로, root가 프로세스 디렉토리를 지우는 동안 다른 rank는 두 번째 장벽에 머물러 있고 그 디렉토리에 쓰지 않는다.

### T3-17 (LOW) 아카이브된 매트릭스 파일이 입력 uncor 트리로 복사된다

`Update_Uncors_To_Input`([DAO_Main.py:7857](5_DAO/SRC/DAO_Main.py#L7857))은 `Redecoded_uncors/{매트릭스 이름}/` 아래 모든 파일을 입력 트리로 복사하며, 건너뛰는 이름은 `uncor_log.txt` 하나다. 커밋 6e035e6 이후 그 디렉토리에는 `Gather_And_Archive_Uncors`가 저장한 `LLR_MATRIX_{idx}.txt`도 들어 있으므로, 매트릭스 파일이 uncor 파일과 함께 `Recoded_uncors_{시각}/`에 복사되고 줄 수까지 uncor_log에 기록된다.

**처방** [DAO_Main.py:7877](5_DAO/SRC/DAO_Main.py#L7877)의 건너뛸 이름 검사를 다음으로 넓힌다.

```python
if filename == "uncor_log.txt" or filename == current_matrix_file_name:
    continue
```

### T3-11, T3-12, T3-13, T3-18, T3-19, T3-21 (Util 나머지)

- ㉮ `check_result_files.py`([check_result_files.py:13](5_DAO/Util/check_result_files.py#L13))의 `dao_dir_path = r""`는 `Path("")`가 되고, `pathlib`는 이것을 현재 디렉토리로 다룬다. 따라서 `exists()`와 `is_dir()`이 모두 참이 되어 경로 미설정 안내가 나오지 않고, 현재 디렉토리에서 `Process_*`를 찾다가 "디렉토리를 찾을 수 없습니다" 대신 "Process_* 디렉토리를 찾을 수 없습니다"를 낸다. 읽기만 하므로 부작용은 없고 진단만 어긋난다. 경로를 첫 번째 명령행 인자로 받고 비어 있으면 사용법을 출력한 뒤 종료한다
- ㉯ `rename_llr_idx.py`([rename_llr_idx.py:15](5_DAO/Util/rename_llr_idx.py#L15))는 `N = 500`을 소스에 박고, 자기가 놓인 폴더의 `LLR_MATRIX_{idx}.txt`를 확인 없이 `os.rename`한다. 내림차순 정렬 덕에 대상 집합 안에서는 이름이 부딪히지 않지만, 되돌리는 방법이 없고 미리보기도 없다. 증가값을 명령행 인자로 받고 `--apply`가 있을 때만 실제로 이름을 바꾼다
- ㉰ `merge_uecc.py`([merge_uecc.py:21](5_DAO/Util/merge_uecc.py#L21))는 `with open(out_path, "a", ...)`로 파일마다 결과를 덧붙인다. 두 번 실행하면 `merged_output.txt`에 같은 내용이 두 벌 쌓인다. 대상 접두사도 `INPUT_FILE_NAME_PREFIX = "abc"` 예제 값이라 그대로 실행하면 아무것도 모으지 않는다. 시작할 때 결과 파일을 `"w"`로 한 번 열어 두고 같은 핸들에 이어 쓰며, 접두사를 명령행 인자로 받는다
- ㉱ `remote_server_sync.py`의 `write_sync_log`([remote_server_sync.py:242](5_DAO/Util/remote_server_sync.py#L242))는 `Path(local_path)/server_sync_{시각}/` 안에 로그를 쓴다. 그 폴더는 SSH 접속 성공 뒤에야 만들어지므로([remote_server_sync.py:157](5_DAO/Util/remote_server_sync.py#L157)), 예제 호스트 그대로 실행해 접속이 실패하면 없는 폴더에 쓰려다 `FileNotFoundError`가 나고 주기 실행 루프가 그대로 끝난다. `log_path.parent.mkdir(parents=True, exist_ok=True)`를 먼저 부른다
- ㉲ `remote_server_sync.py`는 `paramiko.AutoAddPolicy()`를 써서 호스트 키를 확인 없이 받아들이고([remote_server_sync.py:118](5_DAO/Util/remote_server_sync.py#L118)), 접속 주소, 사용자 이름, 개인 키 경로를 소스의 `CONFIG`에 담는다([remote_server_sync.py:29](5_DAO/Util/remote_server_sync.py#L29)). 중간자 공격을 막지 못하고, 키가 바뀌어도 알리지 않는다. `CONFIG`를 같은 폴더의 설정 파일이나 환경 변수에서 읽고, `load_system_host_keys()`와 `RejectPolicy`를 쓴다
- ㉳ `split_file.py`([split_file.py:47](5_DAO/Util/split_file.py#L47))는 원본을 지우지 않고 `{원본 폴더}/{번호}/{원본 이름}`에 `"w"`로 쓴다. 원본 폴더에 `1/`, `2/` 같은 폴더가 이미 있고 같은 이름 파일이 들어 있으면 말없이 덮어쓴다. 출력 폴더를 `{원본이름}_split/{번호}/`로 바꾸고, 그 폴더가 이미 있으면 안내한 뒤 종료한다

### T3-20 (LOW) `Mock_ECC.py`의 인자 규약과 흉내 범위

인자 순서는 `Get_Ref_C_Args`([DAO_Main.py:6407](5_DAO/SRC/DAO_Main.py#L6407))의 비 2.4 분기와 1번부터 18번까지 정확히 맞는다. 결과 파일 이름도 `Get_Result_File_Name`([DAO_Main.py:1618](5_DAO/SRC/DAO_Main.py#L1618))의 비 2.4 분기와 같은 서식이다. 19번째 `str_matrix_name`은 Mock이 읽지 않지만 `len(args) >= 18` 검사만 하므로 넘어와도 문제없다.

두 가지가 다르다.

- ㉮ `ECC_VER == "2.4"` 분기는 13번부터 16번이 `CRC_Option_F_P, mode_iter, CRC_skip_mode, HighDV_skip_mode`인데 Mock은 `mode_all_one_cw, CRC_Option_F_P, mode_iter, mode_scenario`로 읽는다. Mock 문서에 "ECC_VER 3.0 기준"이라 적혀 있으므로 알려진 제약이지만, 2.4로 Mock을 돌리면 결과 파일 이름의 시나리오 번호가 `HighDV_skip_mode` 값이 되어 DAO가 결과 파일을 찾지 못한다
- ㉯ Mock은 uncor 파일을 읽지도 쓰지도 않는다([Mock_ECC.py:224](5_DAO/Util/Mock_ECC.py#L224)의 `run`은 결과 파일과 CSW 로그만 만든다). 그래서 `seed_mode`가 `LOAD_UNCOR_SEED_SAVE_UNCOR_SEED`여도 `redecode_uncor_seed_*.txt`가 생기지 않고, `_Build_Initial_Partial_Pool`이 실패 프레임 0개를 보고 False를 돌려 `_Signal_Graceful_Stop_No_Partial`로 간다. 두 단계 테스트 경로 전체(T3-1이 지적한 자리 포함)를 Mock으로 확인할 수 없다

**처방** `MockECC.run`에 `seed_mode`가 uncor 저장을 뜻하는 값일 때 `Get_Uncor_File_Name`과 같은 서식으로 파일을 만들고 `num_errors`만큼 줄을 쓰는 절차를 넣는다. 2.4 인자 순서는 `README_Mock_ECC.md`에 지원 범위를 명시하고 Mock이 인자 개수와 `ECC_VER`을 검사해 맞지 않으면 즉시 종료하게 한다.

## 확인했으나 문제 없던 범위

- ㉮ **`Gather_And_Archive_Uncors`의 새 `matrix` 인자를 모든 호출처가 넘긴다.** `git show 6e035e6 -- 5_DAO/SRC`로 확인한 뒤 호출처 네 곳을 전부 확인했다. [DAO_Main.py:7339](5_DAO/SRC/DAO_Main.py#L7339)(`Process_Uncors`), [DAO_Main.py:8998](5_DAO/SRC/DAO_Main.py#L8998)(`Test_LLR`), [DAO_Main.py:9298](5_DAO/SRC/DAO_Main.py#L9298)(`_Build_Initial_Partial_Pool`), [DAO_Main.py:9384](5_DAO/SRC/DAO_Main.py#L9384)(`Rebuild_Partial_Pool`). `_Get_Tmp_Partial_Uncor_Dir`의 두 호출처도 매트릭스를 넘긴다. `Process_Uncors`의 `matrix` 기본값은 `None`이지만, gather 분기로 가는 호출처는 [DAO_Main.py:7808](5_DAO/SRC/DAO_Main.py#L7808) 하나이고 `matrix=self.current_LLR_matrix`를 넘긴다. 나머지 호출처는 `is_setup_stage=True`라 `Copy_Uncors` 쪽으로 간다
- ㉯ **`src_path=None`이 `_Setup_Uncor_Pool_For_Channel`로 넘어가는 경로는 막혀 있다.** `Gather_And_Archive_Uncors`와 `Copy_Uncors`가 `None`을 돌려주는 경우는 root가 아닐 때뿐이고, `_Setup_Uncor_Pool_For_Channel`은 `src_path`를 `if self.is_root:` 안에서만 만지며 그 안에서 `if not src_path or not src_path.exists():`로 한 번 더 막는다([DAO_Main.py:7406](5_DAO/SRC/DAO_Main.py#L7406)). 서명의 형 표기가 `src_path: Path`인 점만 실제와 다르므로 `Optional[Path]`로 고치면 된다
- ㉰ **`Load_Uncors_From_Pool`의 보호 없는 `unlink`와 `copy2`가 rank 사이 상태를 가르지는 않는다.** [DAO_Main.py:7529](5_DAO/SRC/DAO_Main.py#L7529)의 `unlink`와 7536줄의 `copy2`는 예외를 잡지 않는다. 다만 어느 rank에서 `OSError`가 나도 모듈 끝의 `Main()` 처리기가 `MPI_Abort`로 이어 전체를 끊으므로, 한 rank만 다른 상태로 남아 계속 도는 일은 없다. 이 함수에 들어가는 `has_uncor` 결정은 그 앞의 `pool_has_uncor`가 `_safe_bcast`로 맞춰진 값이라 rank 사이에 어긋나지 않는다. 모드 전환 때 pool에 자기 몫이 없는 프로세스는 작업 파일을 지우지 않고 건너뛰지만, `has_uncor`가 False이므로 `Run_ECC`([DAO_Main.py:7931](5_DAO/SRC/DAO_Main.py#L7931))가 그 프로세스를 건너뛰어 남은 파일이 쓰이지 않는다
- ㉱ **`Distribute_Uncors_To_Local_Session`의 조용한 실패가 rank를 가르지 않는다.** 원본 파일이 없거나 비면 `has_uncor_list`가 전부 False로 남고, 그 목록이 `_safe_bcast`를 거쳐 모든 rank에 같은 값으로 퍼진다([DAO_Main.py:1589](5_DAO/SRC/DAO_Main.py#L1589)). 테스트는 빈 결과가 되지만 rank 사이 상태는 같다
- ㉲ **`Delete_Uncors`와 `Delete_Own_Uncors`의 역할 구분은 뚜렷하다.** 앞은 root가 모든 프로세스 디렉토리에서 지우는 직렬 방식이고 `Distribute_Uncors_To_Local_Session` 안에서만 불린다. 뒤는 각 프로세스가 자기 것만 지우는 병렬 방식이고 `Set_Test_Environment`([DAO_Main.py:8471](5_DAO/SRC/DAO_Main.py#L8471))에서 `SAVE_UNCOR_SEED`일 때만 불린다. 제외된 코어를 건너뛰는 처리도 들어 있다. 누적 문제는 재디코딩 출력 쪽에만 있다(T3-1)
- ㉳ **`Gather_And_Archive_Uncors`와 `Cleanup_Test_Environment` 사이에 파일 경합이 없다.** root가 다른 프로세스 디렉토리를 읽는 동안 각 rank가 자기 디렉토리를 정리하지만, 정리 대상은 `result`, `log_CSW`, `Ref_C_result` 접두사와 `.bat`, `.sh`, `.tmp` 확장자뿐이라 `uncor_seed`나 `redecode_uncor_seed` 파일과 겹치지 않는다. 또 root가 병합을 시작하는 시점은 `Gather_Ref_C_Results`의 집단 통신 뒤라 모든 rank의 ECC가 끝난 뒤다
- ㉴ **`TEST_MODE_DIR_NAME`에 FULL 항목이 없어도 아무 일이 일어나지 않는다.** `5_DAO/SRC` 전체에서 이 딕셔너리를 읽는 자리가 없다. `KeyError`도 `.get` 기본값도 없다. 남은 문제는 죽은 상수가 있다는 것과 README가 그것을 살아 있는 것처럼 설명한다는 것뿐이다(T3-6)
- ㉵ **`Copied_uncors` 디렉토리는 늘어나지 않는다.** `Copy_Uncors`가 항상 같은 이름(`Copied_uncors/` 또는 `Copied_uncors/{UNCOR_MATRIX_IDX가 가리키는 이름}/`)으로 덮어쓰고, 쓰기 전에 기존 파일을 지운다([DAO_Main.py:1298](5_DAO/SRC/DAO_Main.py#L1298)). 용량이 계속 느는 쪽은 `tmp_partial_uncors`와 `Redecoded_uncors`다(T3-8)
- ㉶ **Util의 읽기 전용 스크립트.** `collect_llr_matrices.py`는 `main()`이 `move=False, dry_run=False`로 고정되어 복사만 하고 원본을 남긴다. `fer_plot/fer_plot.py`는 입력 파일을 읽고 그림을 저장할 뿐 지우거나 덮어쓰지 않는다. `list_running.sh`는 조회만 한다. `install_requirements.bat`은 pip 설치만 한다. `git_clone.bat`은 예제 저장소 주소(`bitbucket.org/yourname/yourrepo.git`)가 박혀 있어 그대로 실행하면 clone이 실패하고 빈 타임스탬프 폴더만 남는다 (부작용은 폴더 하나)
