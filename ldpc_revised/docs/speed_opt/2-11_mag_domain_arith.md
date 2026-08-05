# 2-11. magnitude 도메인 변환 분기 체인 → 산술식

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/decoder.cpp` |
| bit-exact | 보장 (유한 도메인 전수 일치) |
| 위험도 | 낮음 |

## 왜 해야 하나

V 도메인({V_VERY_STRONG..V_VERY_WEAK} = {3,2,1,0})과 EDGE 도메인({EDGE_MAG_7..1} = {7,5,3,1}) 사이 고정 사상을 element마다 3단 if-chain으로 처리한다. 상수 값을 common.h에서 확인한 결과 **EDGE = (V << 1) | 1**, **V = EDGE >> 1**의 산술 관계가 정확히 성립.

## 무엇을 어떻게 바꿨나 (둘 다 `__4_BIT_LLR__`의 `#else` 분기, 즉 3bit 경로)

- `C2V_Cal()` V→EDGE: 4분기 체인 → `check_out = (check_out_temp << 1) | 1;`
- `V2C_Store()` EDGE→V (barrel shift 후, Ref-C 실경로): 4분기 체인 → `v2c_mag = check_in_mag >> 1;`

## bit-exact 근거

- 전수 검증: 3→7, 2→5, 1→3, 0→1 / 7→3, 5→2, 3→1, 1→0 — 기존 체인과 완전 일치
- 입력 도메인 보장: `check_out_temp`는 REG_min 값(초기 V_VERY_STRONG, 갱신은 v2c_mag {0..3})만 가능. `check_in_mag`는 VNU_out 양자화 산출(±{1,3,5,7})의 abs
- 기존 체인의 else(도메인 밖 값)는 실제로 도달 불가한 방어 코드였음

## 주의

- **`__4_BIT_LLR__` 빌드의 체인(V_MAG0~7 ↔ EDGE_MAG_1~8)은 도메인이 달라 그대로 유지** — 그쪽도 산술화하려면 해당 상수 값으로 별도 전수 검증 필요

## 다른 버전 코드에서 위치 찾는 법 (이식 앵커)

1. `V_VERY_STRONG` / `EDGE_MAG_7` 상호 변환 if-chain 검색 (C2V mag 계산, V2C 도메인 변경 주석)
2. **반드시 그 버전의 상수 값을 먼저 확인** — {3,2,1,0}↔{7,5,3,1}이 아닐 경우 산술식이 달라지거나 성립하지 않음
3. 입력 도메인(도달 가능한 값 집합)을 확인한 뒤 치환
