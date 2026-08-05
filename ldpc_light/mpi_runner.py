"""mpi4py 래퍼: 코어당 sim 1개 (rank별 시드 분할) + 카운트 합산.

슈퍼컴 사용 예:
    mpirun -np 64 python -m ldpc_light.mpi_runner <code.qc> --rber 0.006 --frames 100000

mpi4py 미설치 환경(로컬 개발)에서는 단일 프로세스로 동작한다.
주의: 이 모듈은 로컬(MPI 없음)에서만 동작 확인됨 — 슈퍼컴 반입 시 검증 필요 (plan.md §5-6).
"""
import argparse

import numpy as np

from .pcm import QCCode
from .decoder import MinSumDecoder
from . import channel as chan
from .sim import run_fer_point


def _get_comm():
    try:
        from mpi4py import MPI
        return MPI.COMM_WORLD
    except ImportError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("code_file")
    ap.add_argument("--rber", type=float, help="BSC raw bit error rate")
    ap.add_argument("--ebn0", type=float, help="AWGN Eb/N0 (dB)")
    ap.add_argument("--frames", type=int, default=100000, help="총 프레임 (전 rank 합)")
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--max-iter", type=int, default=20)
    ap.add_argument("--seed", type=int, default=12345)
    args = ap.parse_args()
    if (args.rber is None) == (args.ebn0 is None):
        ap.error("--rber 또는 --ebn0 중 하나만 지정")

    comm = _get_comm()
    rank = comm.Get_rank() if comm else 0
    size = comm.Get_size() if comm else 1

    code = QCCode.load(args.code_file)
    dec = MinSumDecoder(code, max_iter=args.max_iter)
    rng = np.random.default_rng([args.seed, rank])
    if args.rber is not None:
        fn = lambda b, r: chan.bsc_llr(code, args.rber, b, r)
    else:
        fn = lambda b, r: chan.awgn_llr(code, args.ebn0, b, r)

    my_frames = args.frames // size + (1 if rank < args.frames % size else 0)
    r = run_fer_point(code, fn, dec, rng, target_errors=10 ** 9,
                      max_frames=my_frames, batch=args.batch)

    counts = np.array([r["frames"], r["errors"]], dtype=np.int64)
    if comm:
        total = np.zeros_like(counts)
        comm.Reduce(counts, total, root=0)
    else:
        total = counts
    if rank == 0:
        frames, errors = int(total[0]), int(total[1])
        print(f"ranks={size} frames={frames} errors={errors} "
              f"FER={errors / frames:.4e}")


if __name__ == "__main__":
    main()
