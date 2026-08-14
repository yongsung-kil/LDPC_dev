# 재리뷰 결과 (라이트, 2026-08-07 후속 수정분)

> 작성: 2026-08-07 12:34:03
> 대상: `_pm/tasks/20260807_리뷰후속수정/` 명세에 따른 LDPC_base 수정 (run.py 재작성,
> sim.py, channel.py, decoder.py, llr_matrix.py, config.json, README.md, llr_tables.py 삭제)
> 에이전트: 2 (lv1, Opus). 상세: `agent_1.md`(수정 정확성·회귀), `agent_2.md`(통합·문서 정합)
> Round 1 생략 사유: 수정 재리뷰로 관점이 수정 명세에서 직접 도출됨 (메인 결정)

## 발견 요약

CRITICAL 0, HIGH 0, MEDIUM 8, LOW 14.

핵심 통과 확인:
- strong_error 2단계 추출: C++ 원문 직역과 결합분포까지 일치 (카이제곱 160.1, 자유도 179), 개수 수치(300/90/22399) 정확
- `_mx_vnu_quantize` 캐스케이드: 1080케이스 전수 스칼라 원문 일치, float32 유지
- 회귀 없음: fixed_error와 rber의 난수 소비가 수정 전과 비트 단위 동일
- llr_tables/llr_profile 잔재 0건, `__init__.py` 유효, F11 4종이 사용자 확정판대로 동작 (Round 3 완화 처방이 실수로 들어가지 않음)

## 수리 완료 (재리뷰 발견 중 4건, 회귀 테스트 추가 후 51건 전부 통과)

| # | 발견 | 수리 |
|---|------|------|
| 1 | `_validate` 커버리지가 그룹 경계만 검사 — ITER 다중 row 그룹의 내부 빈틈·겹침 통과 (agent_1 M1·M2) | 그룹 내부 row 구간 연속성 검사 추가 (`llr_matrix.py`) |
| 2 | `seed: null`이 검증 통과 후 시뮬 도중 TypeError (agent_1 M3, agent_2 ㉯) | run/channel 양쪽에서 null seed 거부 (`run.py`) |
| 3 | 섹션이 null이면 (`"run": null`) 원인을 지목하지 않는 raw TypeError (agent_2 ㉮) | decoder/run/output 섹션 dict 타입 검사 (`run.py`) |
| 4 | 다중 채널에서 모드 불일치가 앞 채널 측정 후 발견 — 측정 결과 소실 (agent_2 ㉲) | `run_experiment` 진입 시 전 채널 모드 사전 확인 (`run.py` `_check_channel_mode`) |

## 수리 보류 (근거와 함께 기록)

| 발견 | 보류 사유 |
|------|-----------|
| decoder 하위 키 오타가 load_config가 아닌 setup 시점 TypeError (agent_2 ㉰) | 의도된 설계 — 허용 키를 load_config에 중복 관리하지 않고 `MinSumDecoder(**kwargs)`의 거부에 위임. 측정 시작 전 실패라 fail-fast는 성립 |
| `decoder.llr_matrix` 생략 시 조용히 two_set 기본으로 완주 (agent_2 ㉱) | Round 2 F17과 동일 건 — 사용자 미결정 항목, 리뷰 기록 유지 |
| LOW 14건 | `agent_1.md`, `agent_2.md` 참조 (메시지 품질, 문서 표현 등) |
| 실험 폴더의 `Sim_Output_test/` 빈 폴더, `Sim_Output/_tmp_*.json` 구 산출물 | 도구 권한 제약으로 삭제 보류 — 수동 정리 대상 (V6-21과 동일 맥락) |

## 종합 판정

**수정 반영 완료** — 이 세션 확정분(키맵·필수값·값 제약, strong_error 2단계, F8 캐스케이드, F11 확정판, F14 주석, llr_profile 제거, channels 리스트)은 구현·검증·재리뷰를 마쳤다.
자동 검증: 51 PASS / 0 FAIL (설정 검증 12, sim 가드 3, strong_error 통계·경계 12, F8 등가성 5, _validate 7, 디코더 경로 3, 수리 회귀 7 외).
스모크: `python -m LDPC_base.run config.json` 정상 (FER=1.0은 토이 LLR 파일의 dv=2 상한 위반 특성 — 파라미터는 사용자가 추후 수정, TODO "dv range 상한" 항목).
