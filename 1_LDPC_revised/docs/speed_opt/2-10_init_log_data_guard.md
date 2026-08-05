# 2-10. `Init_Log_Data()` 프레임당 호출 가드

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `1_LDPC_revised/decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

`LDPC_Decoder()` 서두에서 **매 프레임** `Init_Log_Data()`가 호출되어 로그 배열 전체 — MN_size × (N_b + M_b + 2×z_sb + 스칼라), SD 모드에서 수십만 대입 — 를 초기화한다. 그런데 이 배열들의 소비처는 전부 조건부 컴파일:

- `Update_Log_Data()` 호출: `__LOG_DECODING_STATUS__` 가드
- `Padding_Zero_Log()` / `Open/Print/Close_Log_Files()`: 본체 내부가 `__LOG_DECODING_STATUS__` 가드 (확인됨)
- `m_log_CSW_auto` 쓰기: `__AUTO_LLR_OPT__` 가드
- Getter(`Get_Log_Bit_Err_Col` 등): corner checker 경로

순수 Ref-C 빌드(위 매크로 전부 미정의)에서는 초기화가 완전 낭비.

## 무엇을 어떻게 바꿨나

호출부만 가드 (본체·할당·해제는 유지 — 1회성이라 런타임 비용 없음):

```cpp
#if defined (__LOG_DECODING_STATUS__) || defined (__PRINT_LOG_DATA__) || defined (__AUTO_LLR_OPT__) || defined (__CORNER_CHECKER__)
    Init_Log_Data();
#endif
```

로그를 쓰는 어떤 빌드에서도 기존과 동일하게 초기화가 수행된다.

## 검증

- grep으로 m_log_* 배열의 모든 쓰기/읽기 지점 추적 → Init/Alloc/Release 외의 접근은 전부 위 매크로 중 하나의 가드 내부임을 확인
- `Open/Print/Close_Log_Files()`는 본체가 이미 내부 가드라 추가 조치 불필요

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. 디코더 진입 함수(프레임당 1회) 서두의 로그 초기화 호출을 찾는다 ("decoding log 배열" 주석 계열)
2. 로그 배열의 소비처를 전수 추적해 **사용되는 매크로 집합**을 그 버전 기준으로 구성 — 가드 매크로 OR 목록은 버전마다 다를 수 있음
3. 할당(Alloc)은 가드하지 않아도 됨 (1회, 메모리만) — 프레임당 반복되는 초기화만 가드
