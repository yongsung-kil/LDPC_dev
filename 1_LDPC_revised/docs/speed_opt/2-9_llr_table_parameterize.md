# 2-9. LLR/threshold 테이블 파라미터화 (텍스트 파일 로드) + 호출당 스택 재구성 제거

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) — 사용자 결정: static const 대신 파일 파라미터화 |
| 파일 | `1_LDPC_revised/decoder.h`, `decoder.cpp`, `llr_tables_template.txt` |
| bit-exact | 조건부 — 아래 "bit-exact 논의" 참조 |
| 위험도 | 낮음~중간 |

## 왜 해야 하나

`Get_VNU_Ch_LLR_Adaptive()` / `Get_VNU_Th_Adaptive()`는 **호출마다**(컬럼당 각 1회 × 129 × iteration) 함수 로컬 2~3KB 테이블을 스택에 재구성했다. 또한 값 변경 시마다 재컴파일이 필요했고, 3SD/threshold 테이블은 소스 손상으로 초기화 리스트가 소실된 상태(읽으면 스택 쓰레기 값 = UB)였다.

## 무엇을 어떻게 바꿨나 — 3층 구조

1. **함수 로컬 테이블 → `static const`** (이름 유지: `Ch_LLR_HD`, `Ch_LLR_2SD`, `Ch_LLR_3SD`, `table_HD/2SD/3SD`)
   - 초기화 리스트가 살아있는 `Ch_LLR_HD`/`Ch_LLR_2SD`는 데이터 그대로 `static const`화 → .rdata 상주, 호출당 복사 0
   - 소실된 4개(`Ch_LLR_3SD`, `table_HD/2SD/3SD`)는 `static const ... = {0};` — **기존 UB(쓰레기 읽기)가 0 읽기로 바뀜** (주석으로 파일 공급 필요 명시)
2. **멤버 배열 6개 + `Load_LLR_Tables()`** — `Alloc_Dec()` 마지막에 1회 호출. `llr_tables.txt`가 실행 디렉토리에 있으면 파싱해서 멤버에 저장하고 `m_llr_from_file = TRUE`. 없으면 코드 기본 테이블 사용. 섹션 이름/행/열 검증 실패 시 에러 출력 후 기본 테이블로 폴백
3. **읽기 지점**: 각 모드 분기에서 행 포인터 1회 선택 후 인덱싱 —
   ```cpp
   const int* row = (TRUE == m_llr_from_file) ? m_Ch_LLR_HD[table_idx] : Ch_LLR_HD[table_idx];
   *ch1 = row[dv_idx];
   ```
   dv_idx 계산·인덱싱 구조(행=table_idx, 열=dv_idx×항목수)는 기존과 완전 동일.

## 파일 포맷 (`llr_tables_template.txt` 참조)

- `#` 시작 줄 = 주석 (섹션 헤더 앞에서만)
- 섹션: `이름 rows cols` 한 줄 + rows×cols개 정수 (행 우선). 순서 고정: CH_HD, CH_2SD, CH_3SD, TH_HD, TH_2SD, TH_3SD
- rows/cols는 빌드의 `PRIME_*` 상수와 일치해야 로드됨 (3bit 빌드: 63×4, 36×8, 66×16, 63×12, 36×12, 66×12)

## bit-exact 논의

- **파일 없음 + HD/2SD ch 값**: 기존과 완전 동일 (데이터 이동 없이 static const화만)
- **소실 4개 테이블 경로**: 기존이 UB(스택 쓰레기)라 엄밀한 bit-exact 비교 자체가 불가 — 이제 결정적(0 또는 파일 값)이 됨. **원본 값을 파일로 공급하면 원본(손상 전) 동작과 일치**
- **재현성**: 사용한 테이블 파일을 결과와 함께 보관할 것 (로드 성공 시 `[Info] LLR tables loaded...` 출력됨)

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. "excel로부터 생성한 txt에서 복사" 주석 또는 `Ch_LLR`/`table_HD` 계열 함수 로컬 대형 배열을 검색
2. 그 버전의 초기화 리스트가 온전하면: 값을 그대로 `llr_tables.txt`로 추출(엑셀 원본에서 재생성 가능)하고 동일한 로더 구조 적용
3. 인덱싱(행/열 의미)이 이 버전과 같은지 먼저 확인 — 다르면 파일 포맷의 열 배치를 그 버전 기준으로 맞출 것
4. `__AUTO_LLR_OPT__`용 `Get_VNU_LLR_SET_FILE()`(이미 파일 기반, m_param_LLR 사용)과는 별개 경로 — 혼동 금지
