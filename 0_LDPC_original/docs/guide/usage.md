# Usage — 빌드 및 실행 가이드

## 빌드

### 요구 사항
- **OS**: Windows 10 이상
- **컴파일러**: Visual Studio 2022 (MSVC cl.exe 19.44+)
- **외부 라이브러리**: 없음 (self-contained)

### 빌드 명령

```bat
cd 0_LDPC_original/src
build.bat
```

`build.bat`은 VS Developer Environment를 설정한 뒤 모든 .cpp를 한꺼번에 컴파일한다:
```
cl /EHsc /W3 /O2 /Fe:ldpc_sim.exe *.cpp
```

성공 시 `0_LDPC_original/src/ldpc_sim.exe`가 생성된다.

> **현재 상태**: 빌드 불가 — 일부 소스 파일에 손상된 텍스트가 포함되어 있어 별도 수정이 필요하다.

---

## 실행 모드

실행 모드는 **컴파일 시점**에 결정된다. `0_LDPC_original/src/mode.h`에서 매크로를 정의/해제한 뒤 다시 빌드해야 한다.

### Ref-C 모드 (성능 측정)

**목적**: 다양한 채널 조건에서 FER/BER을 통계적으로 측정한다.

**활성화**: `mode.h`에서 `__PROGRAM_MODE_REF_C__`를 `#define`한다.

**실행**:
```bat
ldpc_sim.exe [파라미터들]
```

[사람 확인 필요: 커맨드라인 파라미터 형식. `Setup_Ref_C()`에서 argv를 파싱하는 부분 확인 필요]

**입력 파일**:
- `H_Matrix/H_402091.txt` — H-matrix (Parity Check Matrix) 정의 파일. 디코더 구조를 결정한다.

**출력**:
- 콘솔에 FER/BER 통계가 출력된다
- 각 SNR 포인트별 프레임 수, 에러 프레임 수, FER 값

**주요 파라미터** (PARAM_REF_C 구조체):
- 시뮬레이션 프레임 수
- SNR 범위/스텝
- 채널 모드 (AWGN, RBER, Strong, Erasure 등)

**Corner 분석**: 수렴 실패 케이스가 발생하면 CornerChecker가 자동으로 seed/에러 패턴을 기록한다.

---

### TV Gen 모드 (HW 검증 데이터 생성)

**목적**: 특정 에러 패턴에 대해 디코더의 모든 중간 신호를 16진수 파일로 출력한다. 하드웨어 팀이 RTL 시뮬레이션과 bit-exact 비교에 사용한다.

**활성화**: `mode.h`에서 `__PROGRAM_MODE_REF_C__`를 **주석 처리** (기본값이 TV Gen).

**추가 스위치**:
- `__ECC_TV__` — 디코더 내부 신호 출력 활성화 (필수)
- `__ECC_TV_ITER__` — 매 iteration마다 출력 (선택, 데이터량 많음)

**입력**:
- H-matrix 파일 (동일)
- 에러 패턴 파라미터 (고정 위치 또는 랜덤)

**출력 파일 구조**:
디코더의 각 파이프라인 stage별로 hex 파일이 생성된다:

| 출력 항목 | 담당 함수 | 내용 |
|-----------|----------|------|
| 인코더 입력/출력 | `Print_TV_Enc_In/Out()` | 메시지, codeword |
| 디코더 입력/출력 | `Print_TV_Dec_In/Out()` | LLR 입력, 복호 결과 |
| C2V 메시지 | `Print_TV_old_sgn()` 등 | Check→Variable 중간 신호 |
| V2C 메시지 | `Print_TV_vtc_inp()` 등 | Variable→Check 중간 신호 |
| VN 처리 결과 | `Print_TV_new_sgn()` 등 | Variable Node 갱신 결과 |

HCU column (127, 128)은 별도의 `_HCU` 함수를 통해 출력된다.

**HW 팀 사용 방식**:
1. 특정 에러 패턴으로 TV 파일 생성
2. 동일 입력을 RTL 시뮬레이션에 투입
3. 각 stage별 출력을 bit-exact 비교
4. 불일치 발견 시 해당 stage 디버깅

---

## 컴파일 스위치 상세

`mode.h`에서 `#define` / 주석 처리로 토글한다. 빌드 후 재컴파일 필요.

| 스위치 | 기본 상태 | 효과 |
|--------|----------|------|
| `__PROGRAM_MODE_REF_C__` | OFF | ON: FER 측정 모드. OFF: TV 생성 모드 |
| `__ECC_TV__` | ON | 디코더 중간 신호 hex 출력. TV Gen에서 필수 |
| `__ECC_TV_ITER__` | OFF | iter마다 신호 출력. 데이터량 급증, 디버깅용 |
| `__HALF_COL_UPDATE__` | ON | col 127,128을 half로 나눠 처리. HW 타이밍 제약 대응 |
| `__HALF_COL_MODIFIED__` | ON | HCU 대상을 col 0,1 → 127,128로 이동 (현재 표준) |
| `__DUAL_UPDATE__` | ON | parity column을 even/odd로 나눠 교대 처리 |
| `__SHUFFLED_DUAL_DIAG__` | ON | 인코딩 시 column 순서 변환 (dual update 호환) |
| `__RUN_PUNCT_RECOVERY__` | ON | punctured bit 투표 복구 |
| `__RUN_MPI__` | OFF | MPI 병렬 시뮬 (슈퍼컴용, Windows에서는 stub) |
| `__AUTO_LLR_OPT__` | OFF | LLR 파라미터 자동 탐색 모드. Ref-C와 함께 사용 |

**일반적인 조합**:
- FER 성능 측정: `__PROGRAM_MODE_REF_C__` ON, `__ECC_TV__` OFF
- TV 파일 생성: `__PROGRAM_MODE_REF_C__` OFF, `__ECC_TV__` ON
- LLR 최적화: `__PROGRAM_MODE_REF_C__` ON, `__AUTO_LLR_OPT__` ON

---

## 참고

- 알고리즘 설명은 [algorithms.md](algorithms.md)
- 전체 구조는 [overview.md](overview.md)
- 파라미터 구조체 상세는 `0_LDPC_original/src/ecc_data.h`의 PARAM_DEC, PARAM_REF_C, PARAM_TV_GEN 참조
