# 2_LDPC_light — 논문 아이디어 스크리닝용 경량 QC-LDPC 시뮬레이터 (vanilla)

> 계획·결정 사항·제약: [docs/plan.md](docs/plan.md)
> **주의**: py는 아이디어 상대 비교(on/off) 전용 — C++ Ref-C와의 절대 FER 일치는 보장하지 않는다.
> 유효 아이디어의 최종 검증은 실물 C++(실제 형태)에 이식하여 수행한다 (plan.md §4).

## 구성

| 파일 | 역할 |
|------|------|
| `pcm.py` | QC-LDPC 표현 (base matrix + shift), 자체 텍스트 포맷 입출력, 4-cycle 카운트 |
| `channel.py` | BSC(hard) / AWGN(soft, 균일 양자화) — all-zero codeword 전제 |
| `decoder.py` | 배치 벡터화 offset/normalized min-sum. CN 상태 old/new 2세트 + edge sign 메모리 (C++ 구조 대응), genie 판정 + 성공 프레임 마스킹 |
| `sim.py` | FER 하니스 (포인트 측정, 스윕, CSV 저장) |
| `mpi_runner.py` | mpi4py 래퍼 (코어당 sim 1개, 시드 분할, Reduce 합산). 미설치 시 단일 프로세스 |
| `tools/peg.py` | PEG base graph 생성 |
| `tools/lifting.py` | greedy circulant shift 배정 (4-cycle 회피) |
| `tools/gen_example_code.py` | 예시 부호 생성 (18×147, z=256, dual-diagonal parity + PEG 정보부 dv=4) |
| `examples/fer_curve.py` | 예시 부호 정정능력 커브 (FER vs RBER / Eb/N0) 생성 |

## 빠른 실행 (repo 루트에서)

```bat
python -m 2_LDPC_light.tools.gen_example_code       # 예시 부호 생성
python -m 2_LDPC_light.examples.fer_curve           # FER 커브 (CSV+PNG → 2_LDPC_light/examples/out/)
```

## 알려진 갭

- LLR 도메인: signed 등가 구현 (원본은 magnitude+HD flip 도메인) — plan.md §3.2
- 파이프라인 V2C store 지연 의존성 미재현 (old/new 2세트로 근사) — plan.md §2
- 실물 H-matrix·LLR 테이블 실값 미반입 (예시 부호 + 균일 양자화 프로파일 사용 중)
- `Get_VNU_Table_Idx` 대응 iteration별 테이블 세트 전환 없음 (원본도 현재 스텁)
- mpi_runner는 MPI 환경 미검증 (로컬 fallback만 확인)
