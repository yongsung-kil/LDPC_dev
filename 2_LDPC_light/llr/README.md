# llr/ — LLR 파라미터 프로파일 폴더

파일 하나 = 실험 구성 하나. 포맷은 [llr_tables.py](../llr_tables.py) 도크스트링 참조.
`_`로 시작하는 파일은 튜닝 스크립트(`examples/llr_tune.py`)에서 제외.

## 원본 실값과 예시 부호의 충돌 (2026-07-31 발견)

- `EDGE_MAG {7,5,3,1}`(VNU 출력 레벨)과 `CH_HD {21,14,12,10}`은 원본 decoder.cpp 실값.
- 그러나 **예시 부호(dv2 컬럼 16개)에 CH_HD 원본을 그대로 쓰면 dv2 정정 불가**:
  dv2 외부정보 최대 2×7=14 < ch 21 → 해당 비트가 절대 안 뒤집혀 FER≈1.
  원본 값은 실물 H-matrix의 degree 구성 전제. → 예시 부호용은 ch도 튜닝 대상.
- `TH_HD`(VNU 양자화 임계)는 원본 소실 — 전부 추정값, 튜닝 대상.

| 파일 | ch (DV2/3/4/5+) | th | 비고 |
|------|----------------|----|------|
| `_hw_orig_ch.txt` | 21 14 12 10 (원본 실값) | 추정 | 보존용 — 예시 부호에선 FER≈1 |
| `chA_thmid.txt` | 10 균일 | 24/14/6 | 기준 |
| `chB_thmid.txt` | 12 10 9 8 | 24/14/6 | 원본 경향 축소판 |
| `chA_thlow.txt` | 10 균일 | 18/10/4 | 빠른 포화 |
| `chA_thhigh.txt` | 10 균일 | 30/18/8 | 보수적 |

사용:
```python
prof = load_profile('2_LDPC_light/llr/chA_thmid.txt')
dec = MinSumDecoder(code, llr_profile=prof)                 # VNU 3-bit 양자화
mag = ch_mag_by_col(code, prof)                             # dv별 채널 LLR
llr = fixed_error_llr(code, n_err, B, rng, mag=mag)
```
프로파일 미지정 시 기존 동작(선형 6-bit, 균일 채널 LLR) 유지.
