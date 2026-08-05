# 3-1. `partial_crc_HW_T4()` 호출당 new/delete 제거

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행) |
| 파일 | `ldpc_revised/partial_CRC.cpp` |
| bit-exact | 보장 |
| 위험 | 낮음 |

## 왜 / 어떻게

`partial_crc_HW_T4()`는 **iteration당 column마다** 호출된다 (프레임당 수천~1만 회). 호출마다 `new int[CRC_LEN]` ×2 + `new int[DEC_D_LEN]` 할당과 delete 3회 = 프레임당 수만 회의 heap 연산.

크기가 컴파일 타임 상수(CRC_LEN=80, DEC_D_LEN=256)이므로 고정 지역 배열(`int tmp1[CRC_LEN];` 등, 스택 ~1.4KB)로 교체하고 delete 제거. **division 함수들(HW 생성 코드)은 일절 수정하지 않음.**

## bit-exact 근거

- tmp_dec_d는 기존과 동일하게 0으로 초기화 후 사용
- tmp1은 division_DEX가 항상 채움; tmp2는 특정 경로(TP4+Shortened≠0)에서 기존에도 미기록 상태로 XOR에 쓰였음(UB) — heap→스택 이동으로 UB 성격 동일 (동작 등급 불변, 잠재 이슈로 문서화)

## 이식 앵커

partial CRC의 heap 할당부만 교체. division_* 함수 본체는 절대 수정 금지 (HW 생성 코드 — 이 저장소 사본은 우측 잘림 손상까지 원본 그대로 유지 중).
