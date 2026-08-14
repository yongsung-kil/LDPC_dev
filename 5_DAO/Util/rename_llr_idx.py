"""
LLR Matrix 파일 idx 일괄 증가

스크립트와 같은 폴더의 LLR_MATRIX_{idx}.txt 파일들의 idx를 N만큼 증가시킨다.
예: N=500 → LLR_MATRIX_1.txt → LLR_MATRIX_501.txt

사용법:
    이 파일을 대상 폴더에 넣고 실행
    python rename_llr_idx.py
"""

import os
import re
from pathlib import Path

N = 500  # ← 증가시킬 값

def main():
    target_dir = Path(__file__).resolve().parent
    pattern = re.compile(r"^LLR_MATRIX_(\d+)\.txt$")

    # 파일 목록 수집
    files = []
    for f in os.listdir(target_dir):
        m = pattern.match(f)
        if m:
            files.append((int(m.group(1)), f))

    if not files:
        print(f"[INFO] LLR_MATRIX_*.txt 파일을 찾지 못했습니다.")
        return

    # 큰 idx부터 rename (충돌 방지)
    files.sort(reverse=True)

    renamed = 0
    for old_idx, old_name in files:
        new_name = f"LLR_MATRIX_{old_idx + N}.txt"
        os.rename(target_dir / old_name, target_dir / new_name)
        renamed += 1

    print(f"[결과] {renamed}개 파일 idx += {N}")
    print(f"  범위: {files[-1][0]}~{files[0][0]} → {files[-1][0]+N}~{files[0][0]+N}")


if __name__ == "__main__":
    main()
