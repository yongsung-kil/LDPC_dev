# 2-5. before_BS dead code 제거 (V2C_Store)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/decoder.cpp` |
| bit-exact | 보장 (Ref-C: dead code 제거 / TV: write-only 변수 삭제) |
| 위험도 | 낮음 |

## 왜 해야 하나

`V2C_Store()`의 element 루프 최상단에서 매 원소마다 "barrel shift 이전(before BS)" 값들을 계산한다: `check_in_before_BS`(+`_nq`, `_mag`), `v2c_sgn_before_BS`, `v2c_mag_before_BS`, `pre_v2c_sgn_before_BS`. 소비처를 전수 추적한 결과:

- `check_in_before_BS`/`_nq`/`_mag`, `v2c_sgn_before_BS`, `pre_v2c_sgn_before_BS` → **유일한 소비처가 `#if defined(__ECC_TV__)` 블록 안의 tv 버퍼 쓰기** (tv_new_sgn_mag, tv_old_sgn 계열)
- `v2c_mag_before_BS` → **소비처 0건** (TV 빌드 포함 어디서도 읽지 않는 write-only 변수)

Ref-C 빌드에서는 이 계산 전체(로드 2회 + abs + 분기 체인 4~8단)가 결과에 전혀 기여하지 않는 순수 낭비 — V2C_Store 최내곽의 약 1/3.

## 무엇을 어떻게 바꿨나

1. 로컬 선언 6개 중 5개를 `#if defined (__ECC_TV__)` 가드로 이동, `v2c_mag_before_BS`는 **선언째 삭제**
2. 루프 내 계산 블록(`/* Read VNU output (before BS) */` ~ domain 변경)을 `#if defined (__ECC_TV__)` 가드. `v2c_mag_before_BS` 계산 체인(4bit/3bit 두 변형)은 완전 삭제
3. `pre_v2c_sgn_before_BS = pre_exist_sgn_reg3_BS[mux_idx][j];` 읽기도 가드

TV 빌드는 기존과 동일하게 동작 (삭제된 것은 write-only 변수뿐).

## 검증

- grep `v2c_mag_before_BS` → 0건
- grep `before_BS` → V2C_Store 내 잔여 사용처는 전부 `__ECC_TV__` 가드 내부 (Punc_vote_Mag_Row_before_BS는 별개 변수 — punct recovery TV 디버그용, 대상 아님)

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `before_BS` 전역 검색 → V2C 저장 함수의 element 루프 상단 계산 블록이 대상
2. **각 변수의 소비처를 먼저 전수 추적** — TV 출력 외 소비처가 있으면 그 변수는 가드 금지
3. write-only 변수(대입만 있고 읽기 0건)는 삭제, TV 전용 변수는 `#if defined(__ECC_TV__)` 가드
