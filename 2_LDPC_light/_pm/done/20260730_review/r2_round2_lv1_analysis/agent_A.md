# Round 2 (lv1) — 축 A: 사실 정확성·정합성

> 대상: `docs/2_LDPC_light/plan.md`
> 검토자: 독립 리뷰 에이전트 A
> 방식: 인용된 C++ 심볼/상수/파일을 모두 직접 열어 확인 (코드 수정 없음)

---

## 요약

| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 6 |
| LOW | 5 |

계획의 골격(2단계 하이브리드, 모듈 분할, Calibration C1~C3)은 코드와 정합한다.
그러나 **부호 파라미터(N_b)** 와 **LLR 테이블의 iteration 의존성** 두 가지가 코드와 어긋나
있고, 그대로 구현하면 배열 차원과 bit-exact calibration이 모두 깨진다.

---

## 확인 결과 — 존재가 확인된 인용 (문제 없음)

| plan.md 인용 | 실제 위치 | 판정 |
|--------------|-----------|------|
| `ecc_top.cpp` `Load_PCM()` | `LDPC/ecc_top.cpp:251` (선언 `ecc_top.h:46`) | OK |
| `channel.cpp` `Set_R_Offset()` | `LDPC/channel.cpp:11` (선언 `channel.h:13`) | OK |
| `channel.cpp` `Set_LLR_Th()` | `LDPC/channel.cpp:33` (선언 `channel.h:14`) | OK |
| `decoder.cpp` `LDPC_Decoder()` | `LDPC/decoder.cpp:956, 999` | OK |
| `decoder.cpp` `C2V_Cal()` | `LDPC/decoder.cpp:2341` | OK |
| `decoder.cpp` `VN_Cal_*()` | `VN_Cal_Pre:3554`, `VN_Cal_HD:3973`, `VN_Cal_CD:4354`, `VN_Cal_SD:4493` | OK |
| `ecc_data.h` PARAM_DEC / PARAM_LLR | `LDPC/ecc_data.h:122`, `:179` | OK (단, LOW-3 참조) |
| `input.cpp` H-matrix 로드 | 실제 파싱은 `ecc_top.cpp:259-330` `Load_PCM()`이 수행 | 부분 OK |
| 링크 `../paper_screening_profile.md` | `docs/paper_screening_profile.md` 존재 | OK |
| 링크 `../../1_LDPC_revised/llr_tables_template.txt` | 존재 (1833 B) | OK |
| 링크 `../../LDPC/docs/20260413_ldpc_decoder_understanding/_ldpc_00_L2_단계별상세.md` | 존재 (30277 B) | OK |
| `CN_STATE` (speed_opt 4-3) | `1_LDPC_revised/decoder.h:30` | 존재 (단, MEDIUM-4 참조) |

상대경로 링크 3건 전부 유효하다.

---

## HIGH

### H-1. `N_b = 129`는 사실이 아니다 — 129는 `N_b - M_b`(정보 column block 수)

**대상**: plan.md:20 (§1 #6), plan.md:30 (§2), plan.md:80 (§3.2), plan.md:72 (§3.1b)

근거:

```
LDPC/decoder.cpp:185   HCU_start = m_PCM->N_b - m_PCM->M_b - m_PCM->punct_col_num;
LDPC/decoder.cpp:186   HCU_end   = m_PCM->N_b - m_PCM->M_b - 1;
```

`CLAUDE.md:55`가 `HCU_start/HCU_end = 127/128`, `punct_col_num = 2`라고 기록하므로
위 두 식에서 **`N_b - M_b = 129`** 가 유일하게 성립한다. 즉 129는 전체 column block 수가
아니라 **정보(information) column block 수**다.

보강 근거:

```
LDPC/main.cpp:599   if (LAYOUT_PRIME_512B_TLC_VSS_OFF == matrix_sel) {
LDPC/main.cpp:601       sprintf(str_folder2, "18_by_147_DvMax3\\");
```

H-matrix 폴더명이 `18_by_147` → `M_b = 18`, `N_b = 147`, `N_b - M_b = 129` (일치).
`LDPC/common.h:291 MAX_DV_GLOBAL 17`도 `M_b = 18`과 정합한다(열 무게 ≤ 행 블록 수).
`z_sb = 32`이면 정보 길이 = 129 × 32 = 4128 bit ≈ 512 B → 매크로명 `LAYOUT_PRIME_512B_*`와 일치.

따라서 plan.md의 서술은 다음과 같이 틀렸다:

- plan.md:20 `codeword = 129 × 256 = 33,024 bit ≈ 4KB`
  → 33,024 bit는 **codeword가 아니라 정보부 길이**다. codeword = `N_b × z_sb` = 147 × 256 = **37,632 bit**.
  (4KB라는 표현 자체는 정보부 기준으로는 맞다 — 라벨만 틀렸다.)
- plan.md:30 `Column-layered 순차 스케줄 (129 col 순서)` → 실제 column 순회는 `N_b` = **147**회.
- plan.md:80 `column 루프(129회 × iteration)` → 동일 오류. 배열 축 `(B, N_b, z_sb)`의 `N_b`를 129로 잡으면
  parity block 18개가 통째로 빠진다.

**각주 충분성 판정 (검토 항목 2)**: plan.md:20의 각주는 `z_sb=32`가 특정 H-matrix 기준이라는 점만
설명하고 — 이 부분은 정확하다(`ecc_top.cpp:264-270`에서 `N_b/M_b/J/K/z_sb`가 모두 H-matrix 파일
헤더에서 런타임으로 읽힌다) — **`M_b`와 `N_b`에 대해서는 아무 설명이 없다**. 그런데 정작 코드와
어긋나는 것은 `M_b`/`N_b` 쪽이다. 각주를 `N_b - M_b = 129`(= 정보 블록 수), 실물 `N_b = 147`,
`M_b = 18`로 확장해야 한다.

**부수 사실**: 루트 `CLAUDE.md:51-52`의 `N_b 129 / M_b 129` 표기 자체가 코드와 모순이다
(둘 다 129면 `N_b - M_b = 0` → `HCU_start = -2`). plan.md는 이 잘못된 표를 그대로 승계했다.
`LDPC/CLAUDE.md`는 같은 표에서 `N_b - M_b = 129`를 별도 줄로 적어 스스로 모순을 드러낸다.

### H-2. "iteration별 LLR 테이블"은 현재 C++ 동작과 다르다 — table_idx는 항상 0

**대상**: plan.md:31 (§2 "Quantized LLR 도메인 + iteration별 LLR 테이블 | 유지")

```
LDPC/decoder.cpp:7207        int Decoder::Get_VNU_Table_Idx(int iter) { return 0; }
1_LDPC_revised/decoder.cpp:7288  int Decoder::Get_VNU_Table_Idx(int iter) { return 0; }
호출부: LDPC/decoder.cpp:1140 / 1_LDPC_revised/decoder.cpp:1206
        cur_set_idx = Get_VNU_Table_Idx(mn);
```

원본과 speed_opt 파생본 **양쪽 모두** 무조건 `0`을 반환한다. 즉 `llr_tables.txt`의 행
(= `table_idx`)은 현재 빌드에서 **0행만 사용**되며, iteration에 따라 바뀌지 않는다.
`llr_tables_template.txt:20`의 "행 = table_idx (cur_set_idx, decoding status 기반 세트 번호)"는
설계 의도이지 현재 동작이 아니다.

영향: plan.md의 서술대로 py에 iteration 가변 테이블 선택을 구현하면 §4 C1(bit-exact 추적)이
1st iteration 이후부터 반드시 틀어진다. Calibration이 계획의 핵심 관문이므로 이 서술은 교정 필요.
"현 C++은 table_idx 고정 0 → py도 0행만 사용, 적응 테이블은 아이디어 훅으로 별도 취급"으로 적어야 한다.

한편 **포맷 자체는 "그대로 로드" 가능하다** (검토 항목 3의 나머지 답): 섹션 6종
(`CH_HD 63×4`, `CH_2SD 36×8`, `CH_3SD 66×16`, `TH_HD 63×12`, `TH_2SD 36×12`, `TH_3SD 66×12`),
고정 순서, `# 주석 + "이름 rows cols" + 행우선 정수` — 파서 이식에 모호함 없다.
열 인덱싱은 `dv_idx(0~3) × 항목수`이므로 **degree 구간 매핑 규칙**도 함께 이식해야 하는데
plan.md는 이를 언급하지 않는다 (LOW-5로 함께 기재).

---

## MEDIUM

### M-1. §7 #1(genie 판정)이 §1 #3 / §2(조기종료 제거·고정 iteration)와 충돌

- plan.md:17 (§1 #3): 제거 항목에 "조기종료(고정 iteration)"
- plan.md:35 (§2): "조기종료 (Partial/Full CRC) | 제거 — **고정 iteration** | 판정은 bitwise 비교"
- plan.md:123 (§7 #1): "**매 iteration** hard decision을 정답과 비교, 일치 시 그 프레임 성공 확정 (genie 판정)"

§7 #1은 사실상 genie 조기종료(early termination)를 도입한 것이라 "고정 iteration"과 양립하지 않는다.
두 방식의 FER은 다르다 — 중간 iteration에서 정답에 도달했다가 다시 발산하는 프레임을
genie 판정은 성공으로, 고정 iteration+최종판정은 실패로 센다. §4 C0의 C++ vanilla가 어느
쪽인지 명시되지 않아, C2(FER 곡선 비교)에서 구조적 편차가 생길 수 있다.
→ C++ vanilla와 py가 **같은 판정 규칙**을 쓰도록 §2와 §7을 한쪽으로 통일해야 한다.

### M-2. "LLR 기 최적화 값 사용"은 현재 리포지토리 상태로는 불가

**대상**: plan.md:19 (§1 #5)

- 리포지토리 전체에 `llr_tables.txt`(실값)는 없다. `1_LDPC_revised/llr_tables_template.txt`(빈 템플릿)만 존재.
- 템플릿 24행: "CH_3SD/TH_* 는 **소스 손상으로 코드 내장값이 소실됨(기본 0)** — 반드시 원본 값으로 채울 것"
- `1_LDPC_revised/decoder.cpp:7006` — `Ch_LLR_3SD[...] = {0}; // 원본 초기화 리스트 소실`
- `1_LDPC_revised/decoder.cpp:7220` — TH_* 동일
- `TODO.md:123` — "llr_tables.txt에 HW 원본 값 공급"이 **미완([ ])**

현재 확보된 실값은 `CH_HD`/`CH_2SD`뿐이다. §1 #5의 "기 최적화 값 사용"은 아직 성립하지 않으며,
2SD 이하 모드로만 calibration이 가능하다. §5 3단계에 이 제약을 명시해야 한다.

### M-3. §7 #3 "decoder 동작은 검증 완료 상태" 과장

**대상**: plan.md:125

- `1_LDPC_revised/README.md:3` — "이 폴더에는 **수정된 파일만** 복사해 둔다 (전체 복사 아님)".
  실제 8개 소스만 존재(decoder/ecc_top/encoder/full_CRC/partial_CRC/random) → **그 자체로 빌드 불가**,
  `ldpc_vanilla/`는 `LDPC/` 원본과 병합해야 한다.
- `1_LDPC_revised/README.md:6` — "이 환경에서는 빌드/실행하지 않는다"
- `TODO.md:123` — "원본 빌드 복구 후 동일 seed golden diff" 미완
- 루트 `CLAUDE.md:43` — "현재 빌드 불가 — 일부 소스 파일 손상"

즉 검증 상태는 "코드 리뷰 완료 / 런타임 검증 미완"이다. §7 #3의 "파라미터만 맞추면 됨"은
C0 작업량을 과소평가한다.

### M-4. §3.2의 CN_STATE 필드 서술이 실제와 다름 — sign은 CN_STATE에 없다

**대상**: plan.md:78

plan: "C++ 4-3의 CN_STATE와 동일 정보 (min1, min2, min1_idx, **sign**)"

실제 (`1_LDPC_revised/decoder.h:30-36`):

```cpp
struct CN_STATE {
    int min1_pos;
    int min1_value;
    int min2_value;
    int check_sum;      // 기존 Check_REG[i]
    int syndrome;       // 기존 Syndrome[i]
};
```

`sign`은 CN_STATE에 없다. edge별 부호는 별도 배열이다:

```
1_LDPC_revised/decoder.h:245   int8_t** Check_SRAM_sgn;  // [M][K] 값 0/1
```

py 설계에서 이 `(B, M, K)` 부호 메모리를 누락하면 remove-old/add-new 갱신을 재현할 수 없다.
CN_STATE 대응은 `{min1_pos, min1_value, min2_value, check_sum, syndrome}` + 별도 sign 배열로 적어야 한다.

### M-5. §3.1 `channel.py` ↔ `channel.cpp` 대응의 경계가 실제보다 넓게 잡혀 있음

**대상**: plan.md:53

`Set_R_Offset()`(channel.cpp:11-29)은 `r_offset/r_offset2/r_offset3`(0.35 / 0.15·0.35·0.55 등) 설정,
`Set_LLR_Th()`(channel.cpp:33-38)은 `LLR_th = 2*r_offset/var` 계산까지만 한다.
이후 `Get_Mag_2SD`/`Get_Mag_3SD`(channel.cpp:42-56)가 **읽기 비트(hd/sd/cc)** 를 만든다.
이 비트를 실제 **LLR 값**으로 바꾸는 것은 채널이 아니라 디코더 쪽이다:

```
LDPC/decoder.h:122   void Get_VNU_Ch_LLR_Adaptive(int dv, int col_idx, int table_idx, int* ch1..ch4);
LDPC/decoder.h:123   void Get_VNU_Th_Adaptive(...);
```

plan.md는 `channel.py`를 "AWGN + 양자화 → **채널 LLR**"로 적고 CH_* 테이블 로드는
`llr_tables.py`로 분리했는데, 실제로 CH_* 테이블은 VNU(디코더) 내부에서 매 column 조회된다.
모듈 경계를 그대로 두더라도, "channel.py는 read-bit까지, LLR 값 매핑은 decoder.py"임을 명시해야 혼선이 없다.

### M-6. §3.1 `mpi_runner.py` ↔ `mpi.cpp (__RUN_MPI__)` 대응이 실물과 다름

**대상**: plan.md:56, plan.md:88

- `LDPC/mpi.cpp` 전체 21줄은 `#ifndef ECCTG_MPI_H` 가드 + **함수 선언만** 있다
  (`mpi.h`와 내용 중복, 정의 0개). `__RUN_MPI__` 문자열도 등장하지 않는다.
- 실제 `__RUN_MPI__` 패턴은 다른 곳에 있다:
  - `LDPC/main.cpp:49-53` — `MPI_Init` / `MPI_Comm_size` / `MPI_Comm_rank`, `:66-68` `MPI_Finalize`
  - `LDPC/ecc_top.cpp:646-662`(rank별 누적 변수), `:674` / `:937` — `Gather_Result_MPI(...)` 호출
  - 단 `Gather_Result_MPI`는 `ecc_top.h:60`에 **선언만** 있고 `.cpp`에 정의가 없다(소스 손상).
- 집계 API도 stub 기준 `MPI_Reduce`(root 수집, `mpi.h:18-19`)이고 **`MPI_Allreduce`는 존재하지 않는다**.
  plan.md:88의 "Allreduce ... C++ `__RUN_MPI__`와 동일 패턴"은 부정확하다(기능상 문제는 없으나 "동일"은 아님).

→ 대응 셀을 `main.cpp` / `ecc_top.cpp`의 `__RUN_MPI__` 블록으로 바꾸고, 참조 구현이 손상되어
있음을 적어두는 편이 안전하다.

---

## LOW

### L-1. §3.1b 예시 부호 파라미터가 "실물과 동일 스케일"이 아님

plan.md:72 — "예시 부호 파라미터: 고rate NAND급 (예: N_b=129, M_b≈13, z_sb=256, rate≈0.9) — 실물과 동일 스케일"

실물은 `N_b=147, M_b=18` (H-1 근거), rate = 129/147 ≈ **0.878**.
또한 §1 #6의 129(정보부)와 §3.1b의 `N_b=129`(전체)가 서로 다른 의미로 쓰여 문서 내에서 충돌한다.
"실물과 동일 스케일"을 유지하려면 `N_b=147, M_b=18, 정보 블록 129`로 적는 편이 정확하다.

### L-2. GT 용어 — 문서 3곳 중 1곳이 다름 (plan.md는 다수 표기를 따름)

| 문서 | 표기 |
|------|------|
| 루트 `CLAUDE.md:113` | Graph Thinning MUX 테이블 |
| `docs/architecture.md:196` | Graph Thinning (MUX 기반 edge 선택) |
| `docs/architecture.md:55` | GT (Graph Thinning MUX 테이블) |
| `LDPC/CLAUDE.md:23, 119` | **Gaussian Trick** |

plan.md:38 "GT (Graph Thinning MUX)"는 루트 CLAUDE.md·architecture.md와 일치한다.
`LDPC/GT.cpp`의 실제 코드(`Make_GT_HW`, `Mux_Matrix[M_b][N_b]` 생성)는 MUX 매핑 테이블 생성이므로
"Graph Thinning" 쪽이 코드 동작과 부합한다. **plan.md의 오류가 아니라 `LDPC/CLAUDE.md`의 오기**로 보인다.
(plan.md 수정 불필요. 별건으로 `LDPC/CLAUDE.md` 정정 권고.)

### L-3. §3.1 `config.py` 대응이 `PARAM_DEC/PARAM_LLR`로만 적혀 있음

`N_b/M_b/J/K/z_sb`는 `PARAM_DEC`이 아니라 `PCM` 구조체(`ecc_data.h:149-156`)에 있고,
`ecc_top.cpp:264-270`에서 **H-matrix 파일 헤더 5개 정수**로부터 런타임에 채워진다:

```
fscanf → N_b, M_b, J, K, z_sb ;  N = N_b*z_sb ;  M = M_b*z_sb
```

즉 `config.py`가 `N_b/z_sb`를 소유하면 `pcm.py`(H-matrix 로더)와 소유권이 겹친다.
"부호 형상은 H-matrix 헤더가 진실 소스, config는 max_iter·양자화 비트 등 시뮬 파라미터"로 분리 명시 권고.

### L-4. §3.1 `llr_tables.py` 대응 `decoder.cpp`의 기준 트리가 모호

`Load_LLR_Tables()`는 `1_LDPC_revised/decoder.cpp:6730`(선언 `decoder.h:179`)에만 있고
`LDPC/decoder.cpp` 원본에는 없다(speed_opt 2-9로 추가된 기능). 표의 다른 행은 `LDPC/` 기준이므로
이 행만 `1_LDPC_revised/decoder.cpp`임을 밝혀야 한다.

### L-5. TODO.md ↔ §5 진행 순서 대조 (검토 항목 6)

`TODO.md:135-141`과 plan.md §5는 대체로 일치한다.

| TODO.md | plan.md §5 |
|---------|-----------|
| 뼈대 구현 | 1 |
| 예시 부호 도구 + FER 커브 | 2 |
| H-matrix·LLR 실물 확인 | 3 |
| **C++ vanilla 파생본 준비 (`ldpc_vanilla/`)** | **§5에 독립 단계 없음** (§4 C0에 "별도 작업"으로만) |
| Calibration C1 → C2/C3 | 4, 5 |
| mpi_runner + 슈퍼컴 | 6 |
| 아이디어 훅 → 스크리닝 | 7 |

`ldpc_vanilla/` 준비만 §5에 번호가 없다. §5 3.5단계로 넣거나 §5에 "C0는 3~4단계와 병행"이라고
적어두면 두 문서가 1:1로 대응한다. (M-3에 따라 이 단계의 작업량은 결코 작지 않다.)

추가로, LLR 테이블 로드 시 **열 인덱싱 규칙**(`dv_idx 0~3 = DV2/DV3/DV4/MIDDV·MAXDV 구간`,
`llr_tables_template.txt:21`)의 이식이 §3.1 `llr_tables.py` 설명에 빠져 있다. 로더만으로는
테이블을 사용할 수 없으므로 degree→dv_idx 매핑 이식을 명시 권고.

---

## 결론

- 구조·모듈 분할·Calibration 설계는 코드와 정합하며 인용된 C++ 심볼은 전부 실존한다.
- **착수 전 반드시 고칠 것**: H-1(`N_b=129` → `N_b-M_b=129`, 실물 `N_b=147/M_b=18`),
  H-2(table_idx는 현재 항상 0 — "iteration별"이 아님).
- **문서 정합 정리**: M-1(고정 iteration vs genie 판정 충돌), M-2(LLR 실값 부재),
  M-3(1_LDPC_revised는 부분 복사·미빌드), M-4(CN_STATE에 sign 없음).
