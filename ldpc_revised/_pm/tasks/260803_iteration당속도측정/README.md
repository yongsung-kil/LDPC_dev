# iteration당 속도 측정 (ldpc_light vs C++ single core)

## 목적

ldpc_light(numpy 벡터화 파이썬 디코더)의 처리 속도를 **1 frame당 1 iteration당 시간**으로
정량화하여, 원본 C++ 시뮬레이터를 single core로 돌릴 때와 속도를 비교할 기준을 만든다.

## 배경

- error 수준(rber)에 따라 수렴 iteration 수가 달라지므로 총 시간만으로는 비교 불가.
  "frame·iteration당 시간"으로 정규화하면 error 수준과 무관한 비교가 가능하다.
- ldpc_light는 batch 벡터화(기본 128 frame) + 배치 압축(수렴 프레임 즉시 제거) 구조라
  "실제 계산된 frame×iteration 수"가 곧 알고리즘상 필요한 수와 일치한다.

## 측정 방법

- 채널: BSC (bsc_llr), all-zero codeword, genie 판정
- 계시 구간: `decode_batch()` 호출만 (`time.perf_counter`). 채널 생성 시간은 별도 집계(ch_sec)
- warm-up 1 batch는 계측 제외
- 지표 정의:

| 지표 | 정의 | 용도 |
|------|------|------|
| frame_iters | Σ(성공 frame의 n_iter) + 실패 frame 수 × max_iter | 실제 계산량 |
| us_per_frame_iter | decode_sec ÷ frame_iters × 10⁶ | **같은 부호**끼리 비교 |
| ns_per_edge_lane | decode_sec ÷ (frame_iters × E × z) × 10⁹ | **다른 부호**(C++ 129×129, z=32)와 비교 |
| frames/s | frames ÷ decode_sec | 처리량 감각 |

## 실행

```bat
cd d:\OneDrive\My_Projects\LDPC_2
python _pm\tasks\260803_iteration당속도측정\measure_speed.py
```

기본값: irregular_17x144_z256 부호, column_wise 스케줄(원본 대응), vanilla 모드,
max_iter=120, batch=128, rber ∈ {0.007, 0.009, 0.0105} (포인트당 10000 frame).

### 15x145 부호로 측정 (6bit급 = vanilla, 2026-08-03 추가)

사용자 지정 분포 Dv11:42 / Dv4:20 / Dv3:69 / Dv2:14 (rate ≈ 0.897, E=777).
`gen_code_15x145.py`가 seed 고정으로 생성하며, 생성본 `irregular_15x145_z256.qc`는
이 폴더에 커밋되어 있어 재생성 없이 바로 사용 가능하다.

컬럼 배치는 원본 H-matrix 대응으로 **정보부 degree 내림차순** (선두 Dv11 → Dv4 →
Dv3 → parity). column-wise 스케줄이 원본처럼 매 iteration을 고degree부터 복호한다.

원본에는 information 31byte shortening (Dv10 영역 = 선두 고degree 영역)과 1byte
puncturing이 있으므로 아래처럼 옵션을 지정한다. shortening은 코드워드 선두
248bit(LLR=+31, 에러 없음), puncturing은 parity 꼬리 8bit(LLR=0)로 모델링했다.
puncturing 위치는 가정이므로 원본과 다르면 measure_point()를 조정할 것.
검산: 4640B − 31B − 1B = 4608B = 4.5KB 전송.

```bat
python _pm\tasks\260803_iteration당속도측정\measure_speed.py ^
    --code _pm\tasks\260803_iteration당속도측정\irregular_15x145_z256.qc ^
    --rber 0.005 0.007 0.009 --shorten-bytes 31 --punct-bytes 1
```

rber 포인트는 rate가 높아진 만큼 낮춰 잡았다 (사전 확인: 0.007까지 FER≈0·avg 9 iter,
0.009는 FER≈9e-2로 수렴 한계 부근. 기본값의 0.0105는 이 부호에선 거의 전 프레임
실패 × 120 iter라 측정이 매우 오래 걸린다).

옵션:
- `--llr-profile ch6688_th842` — HW-근사 3-bit 모드 (`ldpc_light/llr/*.txt` 이름)
- `--schedule two_set` — flooding 등가 스케줄
- `--rber`, `--frames`, `--batch`, `--max-iter`, `--code`, `--seed`

출력: 콘솔 표 + `results/speed_{일시}.csv`

## C++ 측 대응 측정 방법

C++ single core에서 같은 지표를 얻으려면:
1. 프레임 루프에서 `LDPC_Decoder()` 호출 시간만 합산 (인코딩/채널 제외)
2. 프레임별 실제 수행 iteration 수를 합산 → frame_iters
3. us_per_frame_iter = 총시간 ÷ frame_iters × 10⁶
4. 부호가 다르므로 최종 비교는 ns_per_edge_lane = 총시간 ÷ (frame_iters × E × z_sb) × 10⁹
   (C++ 129×129 부호의 E는 base matrix 비영 블록 수, z_sb=32)

## 주의 (비교 해석 시)

1. **종료 판정 차이**: Python은 genie(정답 비교), C++는 syndrome/CRC — iteration 수가
   약간 다를 수 있다. 지표가 "iteration당"이라 영향은 제한적.
2. **배치 점유율 효과**: us_per_frame_iter는 배치가 압축되어 후반 iteration에 활성
   프레임이 적을수록 불리해진다 (파이썬 호출 고정비용이 소수 프레임에 분배).
   FER가 높은 포인트(실패 프레임이 max_iter까지 소수로 돌아가는 경우)에서 값이 커진다.
3. **미재현 기능**: Python은 HCU/파이프라인 지연/CRC 조기종료 없음 — C++ 쪽이 하는
   일이 조금 더 많다.
4. `.qc` 부호 파일은 gitignore 대상이라 다른 환경에서는 `select_irregular.py` 재실행
   또는 파일 복사가 필요하다.
