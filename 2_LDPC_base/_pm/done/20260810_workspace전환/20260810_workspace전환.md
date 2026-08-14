# 20260810_workspace전환

## 목적

실험 공간을 `workspace/`로 통일하고, 실험 폴더 안의 `run.py` 하나만 실행하면 되는
진입점을 제공한다.

## 배경

- ㉮ 사용자 결정 (2026-08-10): `Ideas/` 이름을 `workspace/`로 변경한다. 실험마다
  폴더(논문, 실험환경 등 자유 명명)를 만들고 그 안에 run.py와 config.json을 둔다.
  run.py는 LDPC_base를 보거나 자기 폴더의 변형 디코더를 실행한다. LDPC_base는
  복사하지 않는다
- ㉯ registry는 진입점이 config(JSON) 하나이던 시절의 "이름 → 클래스" 변환표였다.
  run.py(코드)가 진입점이 되면 디코더 클래스를 직접 import할 수 있어 불필요하다

## 설계

- ㉮ `workspace/{실험}/run.py`: 자기 위치에서 상위로 올라가며 `LDPC_base/`가 보이는
  폴더(2_LDPC_light 루트)를 찾아 sys.path에 등록한 뒤 `LDPC_base.run.main()` 호출.
  어느 폴더에 복사해도 수정 없이 동작한다
  - ㉠ 디코더 선택: 파일 안의 `DECODER_CLASS` 한 곳 (None이면 BaseDecoder,
    변형이면 자기 폴더 decoder.py의 클래스를 import해 지정)
  - ㉡ config: 기본은 형제 위치 config.json, 인자로 다른 config 경로 복수 허용
- ㉯ `LDPC_base/run.py`: `main`/`setup`에 `decoder_class` 인자 추가 (None이면
  BaseDecoder). `_resolve_decoder_class`와 config의 `decoder.type` 키 삭제
  (디코더 선택이 코드 몫이 되므로 config에는 파라미터만 남긴다).
  요약에는 디코더 클래스 이름을 출력
- ㉰ `workspace/_template/`: run.py, config.json, README.md 골자 (새 실험 시작 시 복사)
- ㉱ 출력은 기존 그대로 config 위치 기준 `Sim_Output/` (루트 .gitignore가 무시)
- ㉲ 입력은 공용 `2_LDPC_light/Input/` (config의 `../../Input/...` 상대경로)

## 수정 대상 파일

- `Ideas/` → `workspace/` (git mv), `registry.py`와 `__init__.py` 2개 삭제
- `LDPC_base/run.py` (decoder_class 주입, type 키와 registry 조회 삭제)
- `workspace/vanilla/`: run.py 신설, config.json에서 type 키 삭제, README.md 실행법 갱신
- `workspace/_template/` 신설, `workspace/README.md` 신설
- 문서: `docs/새논문적용규칙.md` (절차 다시 쓰기), `README.md` (구성 표, 스키마,
  아이디어 구조 절), `__init__.py` docstring, `../3_LDPC_ideas/README.md` 역할 경계

## 안전성 체크리스트

- [x] vanilla를 run.py로 재실행한 결과가 기존 결과(260808_132800_vanilla)와 동일
      (같은 seed, frames_per_batch. 실행 260810_154140: 로그 CSV 6종 완전 일치,
      fer CSV의 차이는 경과시간 열 4.1초와 4.3초뿐)
- [x] 변형 디코더 주입 경로 동작 확인 (_test/20260810_workspace변형확인/에서
      NoTieFlipDecoder 실행, BER이 기준선과 달라져 재정의 반영 실증)
- [x] `python -m LDPC_base.run config.json` 경로 유지 (루트 config, 실행 260810_154447)
- [x] 정본 문서(새논문적용규칙.md)와 README 갱신, 잔여 Ideas/registry 참조 0건
      (과거 실행 결과물 config 사본 제외, git 무시 영역)

## 미결정 사항

- 없음 (설계 사용자 승인 2026-08-10, 폴더명 소문자 workspace 확정)
