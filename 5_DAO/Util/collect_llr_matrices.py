"""
LLR Matrix 수집 유틸리티

9_Single_Row_Candidates/ 등에 이 파일을 넣고 바로 실행하면,
하위 디렉토리(FER/, CSW_T200/ 등)의 LLR_MATRIX_*.txt를
중복 없이 YYYYMMDD_HHMMSS/ 폴더로 복사한다.

사용법:
    python collect_llr_matrices.py

중복 판정:
    1차: 파일명(LLR_MATRIX_{idx}.txt) 기준 — 같은 idx면 동일 매트릭스
    2차: 파일명이 같을 경우 내용(바이트) 비교 — 내용도 같으면 스킵, 다르면 _dupN 접미사로 보존
"""

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path


def find_llr_matrices(source_dir: Path) -> list[Path]:
    """source_dir 하위를 재귀 탐색하여 LLR_MATRIX_*.txt 파일 목록 반환."""
    matrices = []
    for root, _, files in os.walk(source_dir):
        for f in files:
            if f.startswith("LLR_MATRIX_") and f.endswith(".txt"):
                matrices.append(Path(root) / f)
    return sorted(matrices)


def file_hash(path: Path) -> str:
    """파일 내용의 SHA-256 해시 반환."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(source_dir, output_parent, move, dry_run):
    # 매트릭스 파일 탐색
    matrices = find_llr_matrices(source_dir)
    if not matrices:
        print(f"[INFO] '{source_dir}'에서 LLR_MATRIX_*.txt 파일을 찾지 못했습니다.")
        return

    print(f"[INFO] {len(matrices)}개 파일 발견")

    # 출력 디렉토리 결정
    if output_parent is None:
        output_parent = source_dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_dir = output_parent / timestamp

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

    # 중복 판정 + 복사/이동
    seen_names: dict[str, str] = {}   # filename -> hash
    collected = 0
    skipped_dup = 0
    renamed = 0

    for mat in matrices:
        name = mat.name
        current_hash = file_hash(mat)

        if name in seen_names:
            if seen_names[name] == current_hash:
                # 파일명도 같고 내용도 같음 → 스킵
                skipped_dup += 1
                continue
            else:
                # 파일명은 같지만 내용이 다름 → 접미사 붙여서 보존
                stem = mat.stem           # LLR_MATRIX_123
                suffix = mat.suffix       # .txt
                dup_idx = 1
                while True:
                    new_name = f"{stem}_dup{dup_idx}{suffix}"
                    if new_name not in seen_names:
                        break
                    dup_idx += 1
                seen_names[new_name] = current_hash
                dest_path = dest_dir / new_name
                renamed += 1
                print(f"  [RENAME] {mat.relative_to(source_dir)} → {new_name}  (내용 다름)")
        else:
            seen_names[name] = current_hash
            dest_path = dest_dir / name

        if dry_run:
            action = "MOVE" if move else "COPY"
            print(f"  [{action}] {mat.relative_to(source_dir)} → {dest_dir.name}/{dest_path.name}")
        else:
            if move:
                shutil.move(str(mat), str(dest_path))
            else:
                shutil.copy2(str(mat), str(dest_path))
        collected += 1

    # 결과 요약
    print()
    print(f"[결과]")
    print(f"  출력 디렉토리 : {dest_dir}")
    print(f"  수집           : {collected}개")
    print(f"  중복 스킵      : {skipped_dup}개")
    if renamed:
        print(f"  이름 변경 보존 : {renamed}개 (내용 다른 동명 파일)")
    if dry_run:
        print(f"  (dry-run 모드 — 실제 파일 조작 없음)")


def main():
    source = Path(__file__).resolve().parent
    collect(source, output_parent=None, move=False, dry_run=False)


if __name__ == "__main__":
    main()
