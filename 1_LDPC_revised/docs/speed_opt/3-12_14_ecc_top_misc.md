# 3-12 / 3-13 / 3-14. ecc_top 잔여 소규모 항목 (통합)

| 항목 | 내용 |
|------|------|
| 상태 | **적용 완료** (일괄 진행, 통합 커밋) |
| 파일 | `1_LDPC_revised/ecc_top.cpp` |
| bit-exact | 보장 (3-13은 조건부 — 아래 참조) |
| 위험 | 낮음 |

## 3-12. `__SHOW_RBER_DIST__` 프레임당 fopen 제거

플래그 활성 시 매 프레임 `fopen("rber_dist.dat","a")`/`fclose` → static 핸들 유지 + fflush. 파일 내용 동일.

## 3-13. `Load_Dec_Input_Vector_Format()` 임시 버퍼 재사용

`MODE_SEED_LOAD_UNCOR_VECTOR` 모드에서 프레임당 `new int[len_noPS]` ×4 + delete ×4 → static 버퍼 재사용 (길이 증가 시 재할당).
주의: HD 모드에서 SD/CC/CD 버퍼는 **기존에도 미기록 상태로 복사에 사용**(UB, 쓰레기 값) — 재사용 후에는 이전 프레임 값(결정적)이 됨. UB → 결정적으로 바뀔 뿐이며 해당 값은 디코더가 HD 모드에서 읽지 않음.

## 3-14. 메시지 invert/copy 루프 정리

- `m_inv_msg[n] = (m_msg[n]+1)%2` ×4 → `^ 1`
- `m_cw[n] = (m_inv_cw[n]+1)%2` ×4 → `^ 1`
- all-zero codeword 모드의 원소별 copy ×8 → `memcpy`

## 이식 앵커

- 프레임 루프 안의 fopen("a")/fclose, `new`/`delete` 쌍, `(x+1)%2` invert, 원소별 copy 패턴을 각각 검색
- invert는 값 도메인 0/1 확인 후 적용
