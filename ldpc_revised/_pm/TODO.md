# TODO — ldpc_revised (Project 1: 속도, 메모리 최적화)

> Claude 마지막 확인: 2026-08-05 16:10:48

> 진행 방식: 한 번에 한 항목씩 수정, 사용자 검토 후 다음 항목. 이 환경에서 C++ 빌드와 실행은 하지 않는다.
> 범위: `__PROGRAM_MODE_REF_C__` 성능만 (TV Gen과 log 모드 성능은 대상 아님).
> 확정된 변경만 외부 저장소로 반영한다 (단방향).

---

## 작업 목록

- [ ] 사후 검증 (외부에서 수행, 결과 회신 대기)
  - 원본 빌드 복구 후 동일 seed golden diff (FER, iter, uncor 번호)
  - `llr_tables.txt`에 HW 원본 값 공급
  - overall_clk 변동 시 신값 기준 채택 (6-1, 6-2 문서 참조)
- [ ] LLR table 등 파라미터 파일화 확장 (백로그, 시기와 범위는 추후 논의)

## 새 작업 추가

(비어 있음)

---

## 주의사항 (진행 중 발견, 유지할 것)

- ㉮ 2-1: shift 테이블 조회는 `PCM_b` shift 값이 0 ~ z_sb-1 범위라는 전제. 범위 밖 값이 오면 out-of-bounds (기존 shift_mem은 s = z_sb도 동작했음). H-matrix 로드 시 범위 검증 추가 권장
- ㉯ 2-9: 사용자 결정으로 LLR 테이블은 static const 대신 **텍스트 파일 파라미터화** (Setup에서 1회 로드). 소실된 초기화 리스트는 복원 불필요, 파일이 진실 소스
- ㉰ 2-2: 프로브 패턴 전제는 `C2V_Cal_New_Sgn`/`CNU_Remove_Old_Sgn`의 clear 판정이 (iter, col, mode)만의 함수라는 것. 이후 이 함수들에 per-element 의존 로직을 추가하면 프로브 호출이 깨짐

---

## 참조

- 체크리스트와 항목별 상세: `docs/speed_opt/` (checklist.md, 항목 문서 28편, patches/, commits.md)
- 폴더 규칙: `README.md` (수정된 파일만 보관, 원본은 `../LDPC_Original/`)
