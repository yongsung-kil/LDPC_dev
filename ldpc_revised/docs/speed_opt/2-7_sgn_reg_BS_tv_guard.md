# 2-7. `pre_exist_sgn_reg_BS` 3종을 TV 전용으로 가드

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.h`, `decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

`pre_exist_sgn_reg_BS` / `reg2_BS` / `reg3_BS`(barrel shift 전 old sign의 3단 지연 사본)의 데이터 흐름:

- 쓰기: `C2V_Cal()` element 루프에서 `pre_exist_sgn_reg_BS[mux_index][j] = edge_sgn;`
- 이동: `Delay_2clk()` clk마다 2단 시프트, `Clear_Delay_REG()` 클리어
- **최종 소비: `pre_v2c_sgn_before_BS` → tv_old_sgn 쓰기 (TV 전용, 2-5에서 가드됨) 하나뿐**

비고: barrel shift **후** 버전인 `pre_exist_sgn_reg`(무접미) 3종은 Ref-C 경로(`pre_v2c_sgn` → checksum 갱신)에서 실제 소비되므로 **건드리지 않음**.

## 무엇을 어떻게 바꿨나

선언 / NULL 초기화 / 할당 / 해제 2곳 / `Delay_2clk()` 시프트 2줄 / `Clear_Delay_REG()` 클리어 2줄 / `C2V_Cal()` 쓰기 1곳 — 전부 `#if defined (__ECC_TV__)` 가드.

## 검증

grep `_BS[` 전 occurrence(-B1) → pre_exist_sgn_reg*_BS 사용처 전부 가드 내부. `Punc_vote_Mag_Row_before_BS`는 별개 변수(`__ECC_TV_SYND_INTERNAL_DEBUG__` 계열) — 대상 아님.

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `_BS` 접미사의 sign 지연 배열을 검색 — "before barrel shift" 사본 계열이 대상
2. 무접미 원본(`pre_exist_sgn_reg` 계열)은 Ref-C에서 소비되므로 **혼동 금지** — 접미사 붙은 사본만 가드
3. 소비처 전수 확인 후 선언~쓰기 전 지점을 같은 매크로로 일괄 가드
