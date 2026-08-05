"""FER 시뮬레이션 하니스: 배치 반복 → genie 판정 집계 → FER/평균 iteration."""
import time
import numpy as np

from .decoder import MinSumDecoder


def run_fer_point(code, channel_fn, dec: MinSumDecoder, rng,
                  target_errors=50, max_frames=20000, batch=128, verbose=False):
    """한 채널 조건의 FER 측정.

    channel_fn(batch, rng) -> (batch, N_b, z) LLR.
    target_errors 도달 또는 max_frames 소진 시 종료.
    """
    frames = errors = 0
    iter_sum = 0          # 성공 프레임의 수렴 iteration 합
    t0 = time.time()
    while frames < max_frames and errors < target_errors:
        b = min(batch, max_frames - frames)
        res = dec.decode_batch(channel_fn(b, rng))
        frames += b
        errors += int((~res["success"]).sum())
        iter_sum += int(res["n_iter"].sum())
    elapsed = time.time() - t0
    fer = errors / frames
    point = {
        "frames": frames, "errors": errors, "fer": fer,
        "avg_iter_ok": iter_sum / max(1, frames - errors),
        "sec": elapsed, "fps": frames / max(elapsed, 1e-9),
    }
    if verbose:
        print(f"  frames={frames:6d} errors={errors:4d} FER={fer:.3e} "
              f"avg_iter(ok)={point['avg_iter_ok']:.2f} ({point['fps']:.1f} f/s)")
    return point


def sweep(code, dec, points, make_channel_fn, seed=12345, stop_below=None,
          target_errors=50, max_frames=20000, batch=128, verbose=True):
    """points의 각 파라미터 값 p에 대해 FER 측정. make_channel_fn(p) -> channel_fn.

    stop_below: FER가 이 값 미만이면(신뢰 가능한 측정 한계 이하) 스윕 중단.
    """
    results = []
    for p in points:
        rng = np.random.default_rng([seed, int(1e6 * p)])
        if verbose:
            print(f"point={p}")
        r = run_fer_point(code, make_channel_fn(p), dec, rng,
                          target_errors=target_errors, max_frames=max_frames,
                          batch=batch, verbose=verbose)
        r["param"] = p
        results.append(r)
        if stop_below is not None and r["fer"] < stop_below:
            break
    return results


def save_csv(results, path, param_name="param"):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([param_name, "fer", "frames", "errors", "avg_iter_ok", "sec"])
        for r in results:
            w.writerow([r["param"], f"{r['fer']:.6e}", r["frames"], r["errors"],
                        f"{r['avg_iter_ok']:.3f}", f"{r['sec']:.1f}"])
