# 2-8. `Delay_2clk()` 원소별 복사 → 행 단위 memcpy

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.cpp` |
| bit-exact | 보장 |
| 위험도 | 낮음 |

## 왜 해야 하나

`Delay_2clk()`는 파이프라인 레지스터를 에뮬레이션하기 위해 **clk마다** J(17)×z_sb(32) 크기 배열들의 3단 시프트(3←2, 2←1)를 이중 루프 원소별 대입으로 수행한다. clk 수 = (컬럼 수 + 파이프라인 깊이) × iteration이므로 프레임당 수천 회 × 배열 4개(Ref-C 기준, 2-6/2-7 가드 이후) × 544 원소.

이중 포인터 행 구조라 컴파일러의 memcpy 패턴 인식이 보장되지 않는다 — 명시적 행 단위 memcpy로 치환.

## 무엇을 어떻게 바꿨나

```cpp
// 기존: for (ii) for (i) { dst[ii][i] = src[ii][i]; ... 8개 배열 }
// 변경:
for (ii = 0; ii < m_PCM->J; ii++) {
    memcpy(pre_exist_sgn_reg3[ii], pre_exist_sgn_reg2[ii], m_PCM->z_sb * sizeof(int));
    memcpy(pre_exist_sgn_reg2[ii], pre_exist_sgn_reg[ii],  m_PCM->z_sb * sizeof(int));
    memcpy(VNU_out3[ii], VNU_out2[ii], m_PCM->z_sb * sizeof(int));
    memcpy(VNU_out2[ii], VNU_out[ii],  m_PCM->z_sb * sizeof(int));
#if defined (__ECC_TV__)
    /* _BS/_nq 4개도 동일하게 memcpy (TV 빌드 전용) */
#endif
}
```

미사용이 된 지역 변수 `int i;` 제거.

## bit-exact 근거

- 3←2를 2←1보다 먼저 수행 — 원소별 대입과 동일 순서
- src/dst는 서로 다른 heap 블록이라 겹침 없음 (memcpy 안전)
- **포인터 회전(swap) 방식은 채택하지 않음** — VN_Cal이 활성 컬럼의 mux 행만 부분 갱신하므로, 버퍼를 돌려쓰면 잔존 데이터의 의미가 달라져 결과가 바뀔 수 있음 (함수 내 주석으로 명시)

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. clk 지연 에뮬레이션 함수(Delay 계열 이름 또는 "2 clock delay" 주석)를 검색
2. 3단 시프트의 **복사 순서(3←2 먼저)**를 그대로 유지
3. 포인터 swap으로 바꾸고 싶어도 금지 — 부분 갱신 배열이면 결과가 달라진다
