# 2_LDPC_light — 논문 아이디어 스크리닝용 경량 QC-LDPC 시뮬레이터 (vanilla)

> 계획·결정 사항·제약: [docs/plan.md](docs/plan.md)
> **주의**: py는 아이디어 상대 비교(on/off) 전용 — C++ Ref-C와의 절대 FER 일치는 보장하지 않는다.
> 유효 아이디어의 최종 검증은 실물 C++(실제 형태)에 이식하여 수행한다 (plan.md §4).

## 현재 상태 (2026-08-07, 과도기)

**이 폴더의 코드는 구버전이다.** 개정본은 `_test/20260806_setup_구성_실험/LDPC_base/`에서
작업 중이며(syndrome-aided 디코더, DAO LLR_MATRIX, 원본 대응 채널 3종, JSON 설정,
논문 아이디어 교체 지점 구조), 확정되면 이 폴더의 새 원본으로 반영한다.
반영 시 조치 항목은 `_pm/TODO.md`의 "본체 반영 시 조치" 참조.
구 예시 스크립트(examples/)와 구 LLR 프로파일(llr/)은 2026-08-07 삭제했다
(복구는 git 이력으로 가능).

## 구성

| 파일 | 역할 |
|------|------|
| `pcm.py` | QC-LDPC 표현 (base matrix + shift), 파일 입출력, 4-cycle 카운트 |
| `encoder.py` | 메시지 생성 + 인코딩 (`encode()`는 all-zero를 반환하는 임시 함수) |
| `channel.py` | 채널 모델 (구버전 — 개정본은 원본 대응 3종: rber, fixed_error, strong_error) |
| `decoder.py` | 디코더 (구버전 — 개정본은 syndrome-aided + DAO LLR_MATRIX) |
| `sim.py` | FER 측정 하니스 |
| `run.py` | 실험 진입점 (구버전 JSON 스키마) |
| `mpi_runner.py` | mpi4py 래퍼 (미검증, JSON 설정과 미통일) |
| `tools/H_mat_gen/` | **H-matrix 설계 툴 모음** (사용자 지시 2026-08-07 신설) — peg, lifting, gen_example_code, select_irregular. 상세: `tools/H_mat_gen/README.md` |

## H-matrix 생성 (실험 흐름과 분리된 수동 도구)

```bat
python -m 2_LDPC_light.tools.H_mat_gen.gen_example_code [출력경로]
```

## 알려진 갭 (구버전 기준 — 개정본에서 다수 해소)

- 실물 H-matrix·LLR 테이블 실값 미반입
- mpi_runner는 MPI 환경 미검증
- `encoder.encode()`는 실제 인코딩 없이 all-zero 반환 (실물 인코더 미반입)
