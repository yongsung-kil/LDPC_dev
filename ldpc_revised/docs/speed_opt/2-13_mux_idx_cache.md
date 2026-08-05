# 2-13. VN_Cal 계열의 `Mux_idx` 재조회 제거 (로컬 캐시)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

VN_Cal 계열 5개 함수의 j(z_sb) × ii(v_deg) 이중 루프에서 매 반복 `mux_idx = m_PCM->Mux_idx[ii][col_idx]`를 조회한다 (합산 루프 + 출력 루프 = 같은 값을 j마다 2회씩 재조회, 총 12개 지점). `Mux_idx`는 `[dv][N_b]` 레이아웃이라 ii 증가마다 N_b×4B(~516B) stride 점프 — 캐시 라인당 4B만 사용하는 비친화적 접근.

## 무엇을 어떻게 바꿨나

5개 함수(HD / HD-HCU / CD / SD / SD-HCU) 서두에서 1회 캐시:

```cpp
int mux_cache[MAX_DV_GLOBAL];
for (ii = 0; ii < v_deg; ii++) { mux_cache[ii] = m_PCM->Mux_idx[ii][col_idx]; }
```

루프 안 12개 지점: `mux_idx = m_PCM->Mux_idx[ii][col_idx];` → `mux_idx = mux_cache[ii];`

HCU 변형의 부분 루프(start_deg~end_deg)도 [0, v_deg) 부분집합이라 같은 캐시 사용.

## 검증

grep `mux_cache` = 22 (정의 5 + 채움 5 + 사용 12) — 사전 grep에서 확인한 `[ii][col_idx]` 조회 지점 수와 일치. `C2V_Cal`/`V2C_Store`(edge당 1회 조회)와 `VN_Cal_Pre`/PMU의 `[ii][jj]` 패턴은 대상 아님.

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. VN 계산 함수의 이중 루프 안 `Mux_idx[ii][...]` 조회를 검색
2. 캐시 크기는 최대 column degree 상수(MAX_DV_GLOBAL), 채움 범위는 v_deg
3. edge 단위 함수(C2V/V2C)의 1회 조회는 이득이 없으므로 대상 아님
