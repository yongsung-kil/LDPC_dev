# Review Context

## 변경 목적

2_LDPC_light(논문 아이디어 스크리닝용 경량 Python LDPC 시뮬레이터)의 마지막 딥 리뷰(r4 라이트 재리뷰, 커밋 ea88882, 2026-08-07 12:35) 이후 변경분 리뷰. 델타 5갈래:

1. 가독성 리팩토링 — decoder_main 개명, 단계별 함수 추출 (미추적 _test/에서 작업 후 커밋 2e600ea에서 본체 반영)
2. 본체 반영·패키지화 (2e600ea, 3f596ef) — 구 flat 파일 삭제, `LDPC_base/` 패키지, `Ideas/`(vanilla 교체 지점), `Input/`, `tools/H_mat_gen/` 신설
3. 의견1 반영 (d42ca8c) — 축약·불명확 이름 일괄 수정, setup 직후와 summary.txt에 실험 요약 출력
4. 내부 균일 n-bit 양자화 모드 (01251f5) — `LLRMatrix.make_internal_uniform_matrix()`, `_vnu_quantize` 캐스케이드 th 개수 일반화, JSON `decoder.use_input_llr_matrix` 토글
5. 균일 양자화 매트릭스를 파일로 생성 후 로드하는 방식으로 변경 (e6282b1) — `LLRMatrix.save()` 신설, 정수 th [최대..1] 전환, 파일명 uniform 표시 자동 인식

추가: 미커밋 `2_LDPC_light/config.json` _desc 문구 1건.

## 변경 범위

- diff 명령: `git diff ea88882..HEAD -- 2_LDPC_light/` + 미커밋 `git diff -- 2_LDPC_light/config.json`
- 참고: r4까지의 리뷰와 자동 검증 51건이 구 코드 계보를 커버. 순수 이동분(channel.py, encoder.py, pcm.py, sim.py의 알고리즘 본문)은 가볍게, 델타 로직은 깊게
- 리뷰 대상 아님: `_pm/` 아래 리뷰 기록 파일 이동(rename), DONE.md/TODO.md 갱신

## 배정된 관점 (Round 1 report의 9축)

- 팀 A (uniform_numeric): 관점 A(균일 양자화 수치 규약 + 저장/로드 왕복) + B(캐스케이드 일반화 + 0 레벨 도입 파급)
- 팀 B (config_run): 관점 C(use_input_llr_matrix 분기 + setup 부작용 + config 검증) + F(이름 수정 완결성 + 요약 출력 정확성)
- 팀 C (refactor_exec): 관점 D(단계 함수 추출 동작 보존) + E(패키지 경계·임포트) + I(실행 검증)
- 팀 D (data_docs): 관점 G(데이터 파일 무결성) + H(문서-코드 일치 + 문장 규칙 자기 적용)

상세 확인 항목: `../r1_round1_lv1_perspectives/report.md`와 `agent_1.md`, `agent_2.md` 참조.

## 기술 맥락

- C++ HW 시뮬레이터(0_LDPC_original, 1_LDPC_revised)의 동작을 Python으로 재현한 경량판. C++ 빌드는 이 환경에서 금지, Python은 로컬 실행 가능
- 디코더는 layered min-sum, HD(hard decision) 전용. 2SD/3SD는 채널 출력까지만 준비됨 (디코더 미구현, 명시적 에러가 정상)
- LLR matrix 파일은 DAO 포맷(외부 HW 팀 포맷) 호환이 요구사항. 파일 포맷은 변경 금지 대상
- `Ideas/` 교체 지점 구조: 아이디어 서브클래스가 `MinSumDecoder`의 교체용 함수만 재정의하는 설계
- 실행 진입: `2_LDPC_light/`에서 `python -m LDPC_base.run config.json`
- 실행 검증 시 규칙: 저장소 추적 파일을 수정·생성하지 않는다. config 사본을 scratchpad에 만들어 출력 경로(output.dir, llr_matrix.dir 등)를 scratchpad로 돌려 실행한다. `Sim_Output/`은 gitignore 대상이라 허용
