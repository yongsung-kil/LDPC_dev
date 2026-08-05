"""ldpc_light 디코더의 iteration당 처리 시간 측정 (C++ single core 비교용).

측정 방식: batch 단위로 decode_batch()만 perf_counter로 계시 (채널 생성 제외).
error 수준마다 수렴 iteration이 다르므로 "frame·iteration당 시간"으로 정규화한다.

  frame_iters = Σ(성공 프레임 n_iter) + 실패 프레임 수 × max_iter
    — 배치 압축(성공 프레임 즉시 제거) 덕에 "실제 계산된 프레임×iteration 수"와 일치
  us_per_frame_iter = decode_sec / frame_iters × 1e6      ← 같은 부호끼리 비교
  ns_per_edge_lane  = decode_sec / (frame_iters × E × z) × 1e9
    — 부호 크기가 다른 C++(129×129, z=32)와 비교할 때 쓰는 정규화 단위

실행 (프로젝트 루트에서):
  python _pm/tasks/260803_iteration당속도측정/measure_speed.py
  옵션: --frames 10000 --batch 128 --rber 0.007 0.009 0.0105
        --schedule column_wise|two_set --max-iter 120
        --llr-profile ch6688_th842   (HW-근사 3-bit 모드, ldpc_light/llr/*.txt)
        --shorten-bytes 31 --punct-bytes 1   (원본 대응: 선두 고degree(Dv10급)
        영역 shortening, parity 꼬리 puncturing. 에러는 전송 bit에만 주입됨)
출력: 환경/부호/설정 정보 + rber별 결과 표 + results/speed_*.csv
"""
import argparse
import csv
import os
import platform
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

from ldpc_light.pcm import QCCode                     # noqa: E402
from ldpc_light.decoder import MinSumDecoder          # noqa: E402
from ldpc_light import channel as chan                # noqa: E402
from ldpc_light.llr_tables import load_profile, ch_mag_by_col  # noqa: E402

DEFAULT_CODE = os.path.join(ROOT, "ldpc_light", "examples", "irregular_17x144_z256.qc")
SHORT_LLR = 31.0   # shortened bit: 디코더가 아는 bit → 채널 최대치보다 강한 신뢰


def measure_point(code, dec, rber, frames_target, batch, seed, ch_mag,
                  sh_bits=0, pu_bits=0):
    """한 rber 포인트 측정. 반환: 카운트/시간/정규화 지표 dict.

    sh_bits: 코드워드 선두 [0, sh_bits) shortening (LLR=+SHORT_LLR, 에러 없음).
      원본은 shortening이 Dv10 영역 — 부호를 degree 내림차순 배치로 생성하면
      선두가 최고 degree 영역이므로 여기 고정 (gen_code_15x145.py 참조).
    pu_bits: parity 꼬리 [N-pu_bits, N) puncturing (LLR=0, 미전송).
    flat bit 순서 = j*z + lane (pcm.py 규칙), info block = 0..K_b-1."""
    rng = np.random.default_rng([seed, int(rber * 1e7)])
    N = code.N
    frames = errors = frame_iters = 0
    decode_sec = ch_sec = 0.0
    while frames < frames_target:
        b = min(batch, frames_target - frames)
        t0 = time.perf_counter()
        llr = chan.bsc_llr(code, rber, b, rng, mag=ch_mag)
        if sh_bits or pu_bits:
            flat = llr.reshape(b, N)          # view — llr에 그대로 반영
            if sh_bits:
                flat[:, :sh_bits] = SHORT_LLR
            if pu_bits:
                flat[:, N - pu_bits:N] = 0.0
        t1 = time.perf_counter()
        res = dec.decode_batch(llr)
        t2 = time.perf_counter()
        ch_sec += t1 - t0
        decode_sec += t2 - t1
        n_fail = int((~res["success"]).sum())
        frames += b
        errors += n_fail
        frame_iters += int(res["n_iter"].sum()) + n_fail * dec.max_iter
    return {
        "rber": rber, "frames": frames, "errors": errors,
        "fer": errors / frames,
        "avg_iter": frame_iters / frames,
        "frame_iters": frame_iters,
        "decode_sec": decode_sec, "ch_sec": ch_sec,
        "us_per_frame_iter": decode_sec / frame_iters * 1e6,
        "ns_per_edge_lane": decode_sec / (frame_iters * code.E * code.z) * 1e9,
        "fps": frames / decode_sec,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--code", default=DEFAULT_CODE)
    ap.add_argument("--frames", type=int, default=10000, help="rber 포인트당 프레임 수")
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--max-iter", type=int, default=120)
    ap.add_argument("--schedule", default="column_wise",
                    choices=["column_wise", "two_set"])
    ap.add_argument("--rber", type=float, nargs="+", default=[0.007, 0.009, 0.0105],
                    help="BSC raw bit error rate (여러 개 = 포인트별 측정)")
    ap.add_argument("--llr-profile", default=None,
                    help="HW-근사 3-bit 모드 프로파일 (ldpc_light/llr/ 이름 또는 경로)")
    ap.add_argument("--shorten-bytes", type=int, default=0,
                    help="정보부 선두 고degree 영역 shortening (원본: 31)")
    ap.add_argument("--punct-bytes", type=int, default=0,
                    help="parity 꼬리 puncturing (원본: 1)")
    ap.add_argument("--seed", type=int, default=20260803)
    args = ap.parse_args()
    sh_bits, pu_bits = args.shorten_bytes * 8, args.punct_bytes * 8

    code = QCCode.load(args.code)
    profile = None
    ch_mag = 8.0
    if args.llr_profile:
        path = (args.llr_profile if os.path.exists(args.llr_profile)
                else os.path.join(ROOT, "ldpc_light", "llr", args.llr_profile + ".txt"))
        profile = load_profile(path)
        ch_mag = ch_mag_by_col(code, profile)
    dec = MinSumDecoder(code, max_iter=args.max_iter, schedule=args.schedule,
                        llr_profile=profile)

    print("== environment ==")
    print(f"  Python {sys.version.split()[0]} / numpy {np.__version__}")
    print(f"  OS  : {platform.platform()}")
    print(f"  CPU : {platform.processor()}")
    print("== code ==")
    print("  " + code.summary().replace("\n", "\n  "))
    print("== settings ==")
    mode = f"llr_profile({profile.name})" if profile else "vanilla(beta=1, clip=31)"
    print(f"  schedule={args.schedule}  mode={mode}  max_iter={args.max_iter}  "
          f"batch={args.batch}  frames/point={args.frames}  seed={args.seed}")
    if sh_bits or pu_bits:
        print(f"  shortening={args.shorten_bytes}B (선두 {sh_bits}bit, LLR=+{SHORT_LLR:g})  "
              f"puncturing={args.punct_bytes}B (꼬리 {pu_bits}bit, LLR=0)")

    # warm-up (첫 호출의 할당/캐시 효과를 계측에서 제외)
    rng_w = np.random.default_rng(0)
    dec.decode_batch(chan.bsc_llr(code, args.rber[0], args.batch, rng_w, mag=ch_mag))

    results = []
    hdr = (f"  {'rber':>7} {'frames':>7} {'errors':>6} {'FER':>9} {'avg_iter':>8} "
           f"{'decode_s':>8} {'us/f-iter':>9} {'ns/e-lane':>9} {'frames/s':>8}")
    print("== results ==")
    print(hdr)
    for rber in args.rber:
        r = measure_point(code, dec, rber, args.frames, args.batch, args.seed, ch_mag,
                          sh_bits=sh_bits, pu_bits=pu_bits)
        results.append(r)
        print(f"  {r['rber']:>7} {r['frames']:>7} {r['errors']:>6} {r['fer']:>9.3e} "
              f"{r['avg_iter']:>8.2f} {r['decode_sec']:>8.1f} "
              f"{r['us_per_frame_iter']:>9.2f} {r['ns_per_edge_lane']:>9.3f} "
              f"{r['fps']:>8.1f}")

    tot_sec = sum(r["decode_sec"] for r in results)
    tot_fi = sum(r["frame_iters"] for r in results)
    tot_fr = sum(r["frames"] for r in results)
    print(f"  {'total':>7} {tot_fr:>7} {'':>6} {'':>9} {tot_fi / tot_fr:>8.2f} "
          f"{tot_sec:>8.1f} {tot_sec / tot_fi * 1e6:>9.2f} "
          f"{tot_sec / (tot_fi * code.E * code.z) * 1e9:>9.3f} {tot_fr / tot_sec:>8.1f}")

    out_dir = os.path.join(HERE, "results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, time.strftime("speed_%Y%m%d_%H%M%S.csv"))
    cols = ["rber", "frames", "errors", "fer", "avg_iter", "frame_iters",
            "decode_sec", "ch_sec", "us_per_frame_iter", "ns_per_edge_lane", "fps"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["schedule", "mode", "max_iter", "batch",
                    "shorten_bytes", "punct_bytes"] + cols)
        for r in results:
            w.writerow([args.schedule, mode, args.max_iter, args.batch,
                        args.shorten_bytes, args.punct_bytes]
                       + [f"{r[c]:.6g}" if isinstance(r[c], float) else r[c]
                          for c in cols])
    print(f"csv saved: {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
