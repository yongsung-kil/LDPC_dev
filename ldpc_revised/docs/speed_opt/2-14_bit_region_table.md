# 2-14. bit_pos 영역 분류 테이블화

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.h`, `decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

VN_Cal 계열 5개 함수가 element마다 최대 6구간 × 2비교(12 비교)의 if-else 체인으로 bit 위치를 shortening/puncturing/table 구간으로 분류한다. 구간 경계(`m_ecc_info->bit_pos.*`)는 시뮬레이션 내내 불변 — 분류는 bit 위치의 순수 함수다.

## 무엇을 어떻게 바꿨나

1. `Build_Bit_Region()` 신설 — 기존 체인과 **같은 순서**의 if-else로 `m_bit_region[N]` 테이블을 채움 (값: `BIT_REGION_SH/PUNC/TABLE/NONE`). `LDPC_Decoder()` 최초 호출 시 1회 실행 (`m_bit_region_ready` 플래그 — bit_pos 경계가 있는 `m_ecc_info`는 이 시점에 보장됨)
2. 5개 VN 함수의 체인을 switch로 치환:
   ```cpp
   switch (m_bit_region[bit_pos]) {
   case BIT_REGION_SH:    channel_llr = CH_LLR_MAX; break;
   case BIT_REGION_PUNC:  channel_llr = CH_LLR_MIN; break;
   case BIT_REGION_TABLE: bTable = TRUE; break;
   default: break;    // 구간 밖 — 기존 동작(channel_llr 값 유지) 보존
   }
   ```
3. 텍스트 변형 대응: HD/CD/SD는 동일 체인(일괄 치환), HD-HCU는 주석 블록 포함 변형, SD-HCU는 `//mag값 인가` 주석 변형 — 각각 개별 치환 (주석만 다르고 로직 동일 확인)

## bit-exact 근거

- 테이블 생성이 기존 체인과 같은 조건·같은 순서(겹치는 구간이 있어도 우선순위 동일)
- 어느 구간에도 안 걸리는 bit는 기존에 channel_llr가 이전 원소 값을 유지했음 → `BIT_REGION_NONE` + `default: break`로 동일 동작 보존
- CD의 erasure 검사(`CD[bit_pos] == 1`)는 런타임 값 의존이라 그대로 유지 (switch는 그 else 블록 안)

## 검증

- `m_bit_region[bit_pos]` switch 5곳 = VN 함수 수와 일치
- 잔여 `info_sh_start`는 Build_Bit_Region / Make_LLR(프레임당 1회) / punct recovery / VN_Cal_Pre(초기 iteration 전용)만 — 의도적 유지

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `bit_pos.info_sh_start` 계열 비교 체인을 element 루프 안에서 검색
2. **체인 순서를 테이블 생성에 그대로 복사**할 것 (구간이 겹치면 순서가 곧 우선순위)
3. "어느 구간에도 안 걸리면 값 유지"라는 암묵 동작을 default에서 깨지 않도록 주의
4. 런타임 값 의존 분기(CD erasure 등)는 테이블화 대상이 아님
