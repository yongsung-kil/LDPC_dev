# ADR (Architecture Decision Records)

> Level 2 문서 — 설계 결정 기록.
> 해당 모듈 변경 전에 관련 ADR 확인.
> **코드에서 읽을 수 없는 것(왜 이 선택을 했는가, 무엇을 거부했는가)만 기록.**

---

## ADR 목록

| ID | 제목 | 상태 | 날짜 |
|----|------|------|------|
| [ADR-001](ADR-001-min-sum-decoding.md) | Min-Sum 기반 LDPC 복호 알고리즘 | 추정 | 2026-05-08 |
| [ADR-002](ADR-002-hcu-half-column-update.md) | Half Column Update (HCU) 모드 | 채택 | 2026-05-08 |
| [ADR-003](ADR-003-dual-diagonal-encoding.md) | Shuffled Dual-Diagonal 인코딩 | 채택 | 2026-05-08 |
| [ADR-004](ADR-004-adaptive-llr-table.md) | Iteration별 적응형 LLR 테이블 | 추정 | 2026-05-08 |

---

## ADR 작성 템플릿

새 ADR은 `ADR-{NNN}-{제목}.md` 파일로 작성. **~300토큰 이내** 유지.

```markdown
# ADR-NNN: {제목}

상태: 채택 | 날짜: YYYY-MM-DD

## 제약
{이 결정을 강제한 조건 — HW 스펙, 호환성, 성능 요구 등}

## 결정
{무엇을 선택했는가 — 1~2줄}

## 거부한 대안
- 대안A: {왜 안 됨 — 1줄}
- 대안B: {왜 안 됨 — 1줄}

## 영향 파일
- `파일:L범위` — 어떤 부분
```

AI가 ADR에서 얻어야 하는 것:
1. 이 모듈을 건드릴 때 **피해야 할 접근법**
2. 현재 구현이 **이래야만 하는 제약**
3. 과거 **실험 결과** (FER 수치 등 — 같은 실험 반복 방지)

---

## 운영 규칙

- AI가 "더 나은 방법"을 제안하기 전에 관련 ADR 존재 여부 확인
- 폐기된 ADR은 삭제하지 않고 상태를 `폐기`로 변경
- 실험 결과(FER 수치 등)는 ADR에 포함하여 재현 가능하게

---

## TODO

- [x] src 코드 import 후 기존 결정 역추적 — 초기 ADR 세트 작성
  - [x] 디코딩 알고리즘 선택 근거 → ADR-001
  - [ ] scaling factor 값 선택 근거 (코드에서 확인 불가 — 사람 확인 필요)
  - [ ] H-matrix 포맷 결정 (현재 H_402091.txt 사용, 선택 근거 미상)
  - [ ] 채널 모델 선택 근거 (AWGN/RBER/Fixed 등 지원, 선택 기준 미상)
- [ ] ADR 작성 경험 쌓으면서 템플릿 보완

---

## 참조

- [CLAUDE.md](../../CLAUDE.md)
- [Architecture Overview](../architecture.md)
