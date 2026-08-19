"""QCCode.load의 2벌 H-matrix 파일 처리 검증.

Ref-C(ecc_top.cpp Load_PCM)는 헤더 5개 정수(N_b M_b J K z)와 첫 번째 행렬
M_b*N_b개 정수만 fscanf로 읽고 파일의 나머지 내용(두 번째 행렬 등)은 무시한다.
light의 QCCode.load도 같은 동작이어야 한다.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "2_LDPC_light"))
from LDPC_base.pcm import QCCode

WORK = Path(__file__).resolve().parent


def make_files():
    base = np.array([[0, 1, -1, 2],
                     [3, -1, 0, 1]], dtype=np.int32)   # M_b=2, N_b=4
    z = 4
    code = QCCode(base, z)

    one_set = WORK / "one_set.qc"
    code.save(one_set)

    # Ref-C H_Matrix 폴더 형태 모사: 첫 벌 뒤에 두 번째 행렬을 덧붙인다
    two_set = WORK / "two_set.qc"
    second = np.where(base >= 0, base, -1)             # shift 값 사본
    with open(one_set, encoding="utf-8") as f:
        text = f.read()
    with open(two_set, "w", encoding="utf-8") as f:
        f.write(text + "\n")
        for row in second:
            f.write(" ".join(str(v) for v in row) + "\n")

    # 원소 부족 파일: 헤더는 그대로, 행렬 마지막 1개 누락
    short = WORK / "short.qc"
    tokens = text.split()
    with open(short, "w", encoding="utf-8") as f:
        f.write(f"{tokens[0]} {tokens[1]}\n{tokens[2]} {tokens[3]}\n{tokens[4]}\n\n")
        f.write(" ".join(tokens[5:-1]) + "\n")

    return base, z, one_set, two_set, short


def main():
    base, z, one_set, two_set, short = make_files()

    # 1) 2벌 파일: 첫 벌만 읽고 성공해야 한다 (Ref-C 동작)
    loaded = QCCode.load(two_set)
    assert loaded.z == z, f"z 불일치: {loaded.z} != {z}"
    assert np.array_equal(loaded.base, base), "2벌 파일에서 첫 벌과 base 불일치"
    print("1) 2벌 파일 로드: OK (첫 벌 사용)")

    # 2) 1벌 파일: 기존과 동일하게 성공
    loaded1 = QCCode.load(one_set)
    assert np.array_equal(loaded1.base, base), "1벌 파일 base 불일치"
    print("2) 1벌 파일 로드: OK")

    # 3) 원소 부족 파일: ValueError 유지
    try:
        QCCode.load(short)
    except ValueError as e:
        print(f"3) 원소 부족 파일 ValueError: OK ({e})")
    else:
        raise AssertionError("원소 부족 파일이 에러 없이 로드됨")

    print("ALL OK")


if __name__ == "__main__":
    main()
