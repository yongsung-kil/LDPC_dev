# 3-11. `Print_Seed()` 파일 핸들 유지

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/random.cpp` |
| bit-exact | 보장 (파일 내용 동일) |
| 위험 | 낮음 |

## 왜 / 어떻게

uncor 발생 시마다(그리고 `MODE_SEED_SAVE_ALL_SEED` 모드에서는 **매 프레임**) `fopen(..., "a")` → fprintf → `fclose`를 반복했다. 핸들을 static으로 유지하고 줄마다 `fflush`(크래시 시 유실 방지)로 교체. 파일명이 바뀌면 기존 핸들을 닫고 새로 연다. append 모드 semantics가 유지되므로 파일 내용은 기존과 동일.

- 기존 `fp_uncor_seed` 인자는 원래부터 무시되고 있었음(함수 안에서 재대입) — 시그니처 호환을 위해 유지
- 프로세스 종료 시 핸들은 OS가 회수 (fflush로 데이터는 이미 기록됨)

## 이식 앵커

seed 저장 함수의 fopen("a")/fclose 반복 패턴 검색. 파일명이 런타임에 바뀔 수 있으면 이름 비교 가드 필수.
