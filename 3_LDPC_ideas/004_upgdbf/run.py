"""UP-GDBF(ieee:9902993) 스크리닝 러너.

표준 런처(단일 DECODER_CLASS)와 달리 비교군 여러 개를 EBC 포인트 격자와
이중 루프로 돌며, 포인트마다 새 디코더 인스턴스를 만들어 FER와 자체 지표
(flip miss, 과교정, 플립 block 수)를 함께 수집한다.

- 입력 파일, EBC 격자, 프레임 수, seed: 형제 config.json이 담당
- 비교군(변형 디코더)과 BF 파라미터: 이 파일 상단 상수가 담당
- 결과: Sim_Output/{stamp}_upgdbf/ 에 results.csv와 summary.txt

실행 (이 폴더에서):
    python -X utf8 run.py                           # 전체 비교군, config.json 격자
    python -X utf8 run.py --frames 50 --points 60,120 --variants upgdbf_t2
                                                    # 빠른 확인용 축소 실행
    python -X utf8 run.py --bf-iter 100             # BF iteration 상한 조절
채널 난수는 포인트별로 비교군과 무관하게 같은 스트림을 쓰므로, 모든 비교군이
같은 에러 패턴을 본다.
"""
import datetime
import os
import sys

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))

_root = EXPERIMENT_DIR
while not os.path.isdir(os.path.join(_root, "2_LDPC_base", "src")):
    _parent = os.path.dirname(_root)
    if _parent == _root:
        raise SystemExit("상위 폴더에서 2_LDPC_base/src를 찾지 못함 "
                         "(이 파일은 LDPC_dev 하위 실험 폴더에 있어야 함)")
    _root = _parent
_base_root = os.path.join(_root, "2_LDPC_base")
if _base_root not in sys.path:
    sys.path.insert(0, _base_root)

import numpy as np

from src import channel as chan
from src import encoder
from src.decoder import BaseDecoder
from src.run import load_config, setup
from src.sim import run_fer_point

from decoder import UPGDBFDecoder

BF_MAX_ITER = 40     # BF iteration 상한 (--bf-iter로 조절)
P_ETA = 0.9          # 난수 penalty가 1일 확률 (t_active 초과 iteration)

# 비교군: (라벨, variant, t_active). variant None = 부모 BaseDecoder min-sum 기준선
COMPARISON_GROUPS = [
    ("upgdbf_t0", "upgdbf", 0),
    ("upgdbf_t2", "upgdbf", 2),
    ("upgdbf_t4", "upgdbf", 4),
    ("pgdbf_t2", "pgdbf", 2),
    ("noflip_t2", "no_flip_penalty", 2),
    ("dvnorm_t2", "upgdbf_dvnorm", 2),
    ("minsum", None, None),
]

BASE_COLUMNS = ["group", "EBC", "frames", "errors", "fer", "avg_iter", "sec"]


def make_channel_fn(code, n_err):
    """프레임당 고정 에러 수(EBC) 채널 (본체 fixed_error 사용)."""
    def channel_fn(batch, random_generator):
        msg = encoder.generate_message(code, batch, random_generator)
        cw = encoder.encode(msg, code)
        return chan.fixed_error_channel(code, cw, n_err, random_generator)
    return channel_fn


def parse_args(argv):
    """config 경로와 축소 실행용 덮어쓰기 플래그."""
    opts = {"config": os.path.join(EXPERIMENT_DIR, "config.json"),
            "frames": None, "points": None, "variants": None,
            "bf_iter": BF_MAX_ITER}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--frames":
            opts["frames"] = int(argv[i + 1]); i += 2
        elif arg == "--points":
            opts["points"] = [int(v) for v in argv[i + 1].split(",")]; i += 2
        elif arg == "--variants":
            opts["variants"] = argv[i + 1].split(","); i += 2
        elif arg == "--bf-iter":
            opts["bf_iter"] = int(argv[i + 1]); i += 2
        elif arg.endswith(".json"):
            opts["config"] = arg if os.path.isabs(arg) else os.path.join(
                os.getcwd(), arg)
            i += 1
        else:
            raise SystemExit(f"알 수 없는 인자 {arg!r} "
                             "(--frames N | --points a,b | --variants l1,l2 | --bf-iter N)")
    return opts


def main(argv=None):
    opts = parse_args(sys.argv[1:] if argv is None else argv)
    config = load_config(opts["config"])
    code, base_decoder = setup(config, None)
    llr_matrix = base_decoder.llr_matrix
    seed = config["seed"]
    run_config = config["run"]
    points = opts["points"] or config["channels"][0]["points"]
    max_frames = opts["frames"] or run_config["max_frames"]
    max_frame_errors = max_frames if opts["frames"] else run_config["max_frame_errors"]
    frames_per_batch = min(run_config["frames_per_batch"], max_frames)
    groups = [g for g in COMPARISON_GROUPS
              if opts["variants"] is None or g[0] in opts["variants"]]
    if not groups:
        raise SystemExit(f"--variants에 맞는 비교군 없음 "
                         f"(가능: {[g[0] for g in COMPARISON_GROUPS]})")

    stamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    run_dir = os.path.join(EXPERIMENT_DIR, "Sim_Output", f"{stamp}_upgdbf")
    os.makedirs(run_dir, exist_ok=True)
    summary_path = os.path.join(run_dir, "summary.txt")

    header_lines = [
        f"run: {stamp}_upgdbf",
        f"H matrix: {os.path.basename(config['H_matrix'])} "
        f"(base {code.M_b}x{code.N_b}, z={code.z}, N={code.N}, K={code.K})",
        f"LLR matrix: {os.path.basename(config['decoder']['_used_llr_matrix_path'])} "
        f"(min-sum max_iter={llr_matrix.max_iter})",
        f"BF: max_iter={opts['bf_iter']}, P_eta={P_ETA}",
        f"EBC points: {points}",
        f"frames/point: {max_frames} (max_frame_errors={max_frame_errors}), "
        f"batch={frames_per_batch}, seed={seed}",
        f"groups: {[g[0] for g in groups]}",
        "",
    ]
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header_lines))
    print("\n".join(header_lines))

    rows = []
    for group_index, (label, variant, t_active) in enumerate(groups):
        for point in points:
            if variant is None:
                point_decoder = BaseDecoder(code, llr_matrix=llr_matrix)
            else:
                point_decoder = UPGDBFDecoder(code, llr_matrix=llr_matrix).configure(
                    variant=variant, t_active=t_active, bf_max_iter=opts["bf_iter"],
                    p_eta=P_ETA,
                    eta_seed=[seed, 1000 + group_index, int(point)])
            # 채널 스트림은 비교군과 무관 (전 비교군이 같은 에러 패턴을 봄)
            random_generator = np.random.default_rng([seed, 0, int(1e6 * point)])
            point_result = run_fer_point(
                code, make_channel_fn(code, point), point_decoder, random_generator,
                max_frame_errors=max_frame_errors, max_frames=max_frames,
                frames_per_batch=frames_per_batch, print_progress=True,
                progress_label=f"{label} E={point}",
                progress_interval_frames=run_config.get("progress_interval_frames", 100),
                summary_path=summary_path)
            row = {"group": label, "EBC": point,
                   "frames": point_result["frames"], "errors": point_result["errors"],
                   "fer": point_result["fer"],
                   "avg_iter": point_result["avg_decoding_iteration"],
                   "sec": point_result["sec"]}
            if variant is not None:
                row.update(point_decoder.point_stats())
            rows.append(row)

    csv_path = os.path.join(run_dir, "results.csv")
    stat_columns = []
    for row in rows:
        for key in row:
            if key not in BASE_COLUMNS and key not in stat_columns:
                stat_columns.append(key)
    columns = BASE_COLUMNS + stat_columns
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(",".join(columns) + "\n")
        for row in rows:
            f.write(",".join(
                f"{row[c]:.6g}" if isinstance(row.get(c), float) else str(row.get(c, ""))
                for c in columns) + "\n")
    print(f"saved: {csv_path}")
    print(f"run dir: {run_dir}")


if __name__ == "__main__":
    main()
