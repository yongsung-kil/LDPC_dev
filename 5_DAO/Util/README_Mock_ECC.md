# Mock ECC Simulator

Prime_ECC_3.0.exe의 출력을 모사하는 도구입니다.
회사 외부에서 DAO 시스템의 동작을 검증할 때 사용합니다.

## 파일 구성

| 파일 | 설명 |
|------|------|
| `Mock_ECC.py` | Mock ECC Python 스크립트 |
| `build_mock_ecc.bat` | Windows용 exe 빌드 스크립트 |
| `build_mock_ecc.sh` | Linux/Mac용 빌드 스크립트 |

## 사용 방법

### 방법 1: Python 직접 실행

```bash
# Python으로 직접 실행
python Util/Mock_ECC.py <args...>
```

DAO 시스템에서 사용하려면 `DAO_Config.py`의 `PATHConfig.ECC_EXE_NAME`을 수정해야 합니다:

```python
# DAO_Config.py 수정
ECC_EXE_NAME = "python Mock_ECC.py"  # 또는 적절한 경로
```

### 방법 2: exe 빌드 후 사용 (권장)

#### Windows
```batch
cd Util
build_mock_ecc.bat
```

빌드 후 `dist\Prime_ECC_3.0.exe`가 생성되며,
자동으로 `Input\Ref_C\Prime_ECC_3.0\EXE\` 폴더로 복사됩니다.

#### Linux/Mac
```bash
cd Util
chmod +x build_mock_ecc.sh
./build_mock_ecc.sh
```

빌드 후 `dist/Prime_ECC_3.0`이 생성되며,
자동으로 `Input/Ref_C/Prime_ECC_3.0/EXE/` 폴더로 복사됩니다.

## 인자 형식 (ECC_VER 3.0)

총 18개의 인자가 필요합니다:

| 순서 | 인자명 | 설명 |
|-----|--------|------|
| 1 | matrix_sel | 매트릭스 선택 |
| 2 | init_n | 디코더 모드 (1=HD, 2=2SD, 3=3SD) |
| 3 | ch_type | 채널 타입 (1=RBER, 2=FIXED_ERROR, 3=STRONG_ERROR) |
| 4 | RBER | Raw Bit Error Rate |
| 5 | num_fixed_errs | 고정 오류 수 |
| 6 | fixed_SCRs | Strong Cell Ratio |
| 7 | fixed_SERs | Strong Error Ratio |
| 8 | fixed_erasure_ratios | Erasure Ratio |
| 9 | fn | 파일 수 |
| 10 | max_num_test | 테스트 수 |
| 11 | seed_mode | 시드 모드 |
| 12 | rank | 프로세스 번호 |
| 13 | mode_all_one_cw | All-one Codeword 모드 |
| 14 | CRC_Option_F_P | CRC 옵션 |
| 15 | mode_iter | Iteration 모드 |
| 16 | mode_scenario | 시나리오 모드 |
| 17 | matrix_idx | LLR 매트릭스 인덱스 |
| 18 | enable_print_CSW_log | CSW 로그 출력 여부 |

## 출력 파일

### 결과 파일
파일명 형식: `result_4KB_S_{scenario}_H_{matrix_sel}_CH_{ch_type}_E{...}_init_n_{init_n}_seed_{rank}.txt`

예시:
- ch_type=2: `result_4KB_S_0_H_1_CH_2_E390_init_n_3_seed_0.txt`

### CSW 로그 파일
`enable_print_CSW_log=1`인 경우 생성됩니다.

파일명: `log_CSW_{rank}.txt`

## Mock 동작 설명

Mock ECC는 실제 ECC 디코딩을 수행하지 않고, 통계적으로 그럴듯한 결과를 생성합니다:

1. **FER 생성**: `num_fixed_errs`에 비례하는 기본 FER을 계산하고, 랜덤 노이즈를 추가합니다.
2. **Iteration별 FER**: 각 iteration마다 FER이 점진적으로 감소하는 패턴을 생성합니다.
3. **CSW 로그**: 랜덤한 CSW 값을 생성합니다.
4. **재현성**: 동일한 `rank`와 `matrix_idx`에 대해 동일한 결과를 생성합니다.

## 의존성

- Python 3.7+
- numpy
- PyInstaller (exe 빌드 시)

```bash
pip install numpy pyinstaller
```

## 주의사항

1. **LLR 매트릭스 파일**: Mock ECC는 현재 디렉토리에서 `LLR_MATRIX_{matrix_idx}.txt`를 읽어 `max_iteration`을 결정합니다. 파일이 없으면 기본값 50을 사용합니다.

2. **시뮬레이션 결과**: Mock ECC의 결과는 실제 ECC 디코더와 다릅니다. 이 도구는 DAO 시스템의 파이프라인 검증용으로만 사용해야 합니다.

3. **보안**: 이 도구는 회사 외부에서 검증 목적으로만 사용하세요. 실제 ECC 알고리즘이나 성능 데이터는 포함되어 있지 않습니다.
