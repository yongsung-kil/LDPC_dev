"""전환 시점 스크리닝 스캔 (ieee:8742682 적용 실험).

같은 채널 프레임에 대해 세 가지를 측정한다:
  ㉮ 1단계 단독 (1bit 포화 min-sum, WINDOW회, 궤적 수집)
  ㉯ 3bit 단독 (STAGE2_BUDGET회)
  ㉰ 고정 4회 전환 실측 (합성 검증 겸 기준선)
전환 정책(고정 전환, genie 상한, 감지기, 진입 임계)은 ㉮㉯의 프레임별 기록에서
후처리로 합성한다. 합성이 정확한 근거: 현 C++ HD 구조는 전환 시 CN 상태를 비우고
syndrome만 유지하므로 (decoder.py 모듈 docstring), 2단계 결과가 1단계 진행과
무관하다. 따라서 전환 시점 t의 결과는 프레임별 (1단계 성공 반복 s1, 3bit 단독 성공
반복 s3) 두 값만으로 재구성된다. 구조적 따름정리: 프레임별 최적 전환은
t = s1(1단계 성공까지 유지) 또는 t = 0(1단계 건너뛰기) 둘 중 하나다
(중간 t는 1단계 진행이 버려지므로 결코 최적이 아니다). 합성의 정확성은
고정 4회 실측(㉰)과의 전 프레임 일치로 매 포인트 검증한다.

실행 (이 폴더에서): python -X utf8 scan.py [프레임수]
결과: 콘솔 표 + Sim_Output/scan_{시각}/ CSV (수치는 README.md 표에 옮겨 적는다)
"""
import csv
import datetime
import os
import sys

import numpy as np

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

from src import channel as chan                      # noqa: E402
from src import encoder                              # noqa: E402
from src.decoder import BaseDecoder                  # noqa: E402
from src.llr_matrix import LLRMatrix                 # noqa: E402
from src.pcm import QCCode                           # noqa: E402

from decoder import StageSwitchDecoder               # noqa: E402

H_MATRIX_PATH = os.path.join(_base_root, "Input", "H_matrix", "matrix_sel_1.txt")
LLR_MATRIX_PATH = os.path.join(_base_root, "Input", "LLR",
                               "LLR_MATRIX_HD_matrix_sel_1.txt")

GRID = [10, 30, 50, 70, 90, 110, 120, 130, 140, 150]   # 프레임당 주입 에러 bit 수
FRAMES_PER_POINT = 320
FRAMES_PER_BATCH = 64
SEED = 0
WINDOW = 8            # 1단계 관측 창 = genie 전수 탐색 상한 (전환 시점 0-8회)
FIXED_SWITCH = 4      # 기준선 고정 전환 (C++ ITER_MAX_HBF 대응)
STAGE2_BUDGET = 30    # 2단계 반복 예산 (실패 프레임은 예산 전부 소모로 계상)
W1 = 1.0              # 1bit 반복 가중치 (에너지 대리)
W3 = 3.0              # 3bit 반복 가중치
W3_SENSITIVITY = (2.0, 4.0)
SWEEP_POINTS = (130, 150)                # 포화 크기 재튜닝 소규모 실험의 에러 포인트
SWEEP_SATURATION_MAGS = (7.0, 5.0, 3.0, 1.0)
SWEEP_DV_VARIANTS = (5, 0)               # 5 = C++ (dv>5 열만 포화), 0 = 전 열 포화


def make_decoder(code, llr_matrix, **attrs):
    decoder = StageSwitchDecoder(code, llr_matrix)
    for key, value in attrs.items():
        if not hasattr(type(decoder), key):
            raise AttributeError(f"StageSwitchDecoder에 {key} 없음")
        setattr(decoder, key, value)
    return decoder


def make_channel_batches(code, n_err, frames, seed):
    """고정 에러 수 채널 배치 목록 (프레임당 정확히 n_err bit 반전)."""
    rng = np.random.default_rng([seed, int(n_err)])
    batches = []
    done = 0
    while done < frames:
        batch = min(FRAMES_PER_BATCH, frames - done)
        msg = encoder.generate_message(code, batch, rng)
        cw = encoder.encode(msg, code)
        batches.append(chan.fixed_error_channel(code, cw, int(n_err), rng))
        done += batch
    return batches


def run_frames(decoder, chan_batches, fields):
    """배치마다 디코딩하고 지정 필드를 프레임 축으로 이어 붙인다."""
    collected = {name: [] for name in fields}
    for chan_out in chan_batches:
        result = decoder.decoder_main(chan_out)
        for name in fields:
            collected[name].append(result[name])
    return {name: np.concatenate(parts) for name, parts in collected.items()}


# ---------- 정책 합성 ----------
def stage2_cost_each(s3):
    """프레임별 2단계 소모 반복 수 (실패 프레임은 예산 전부)."""
    return np.where(s3 > 0, s3, STAGE2_BUDGET).astype(np.float64)


def weighted_cost(w1, w3, s1_eff, s3, switch_time):
    """전환 시점 switch_time(스칼라 또는 프레임별)의 가중 반복 수와 성공 여부."""
    t = np.broadcast_to(np.asarray(switch_time, np.float64), s1_eff.shape)
    rescued = s1_eff <= t
    cost = np.where(rescued, w1 * s1_eff, w1 * t + w3 * stage2_cost_each(s3))
    success = rescued | (s3 > 0)
    return cost, success


def genie_policy(w1, w3, s1_eff, s3, window):
    """전환 시점 0-window 전수 탐색의 프레임별 최적 (사후 최적 = 이득 상한).
    최적은 t = s1(유지) 또는 t = 0(건너뛰기) 둘 중 하나다 (모듈 docstring)."""
    stay = np.where(s1_eff <= window, w1 * s1_eff, np.inf)
    skip = w3 * stage2_cost_each(s3)
    cost = np.minimum(stay, skip)
    success = (s1_eff <= window) | (s3 > 0)
    stay_chosen = stay <= skip
    return cost, success, stay_chosen


def detector_conditions(traj_sw, traj_flip):
    """감지기 조건 행렬 (F, WINDOW+1). 열 i = 반복 i 끝에서 조건 성립.
    성공으로 빠진 프레임의 칸은 -1이지만, 소비 측이 i < s1_eff로 거른다."""
    stall = np.zeros(traj_sw.shape, bool)
    stall[:, 1:] = (traj_sw[:, 1:] >= traj_sw[:, :-1]) & (traj_sw[:, :-1] >= 0)
    osc2 = np.zeros(traj_sw.shape, bool)
    osc2[:, 2:] = (traj_sw[:, 2:] == traj_sw[:, :-2]) & (traj_sw[:, 2:] >= 0)
    flip_zero = traj_flip == 0
    flip_zero[:, 0] = False
    return {"sw_stall": stall, "sw_osc2": osc2, "flip_zero": flip_zero}


def detector_switch_time(cond, s1_eff, cap):
    """감지기 발화에 따른 프레임별 전환 시점 (발화 없으면 cap, 성공 전 발화만 유효)."""
    num_frames = cond.shape[0]
    switch_time = np.full(num_frames, float(cap))
    fired = np.zeros(num_frames, bool)
    for i in range(1, cap):
        fire_now = (~fired) & cond[:, i] & (i < s1_eff)
        switch_time[fire_now] = float(i)
        fired |= fire_now
    return switch_time, fired


def detector_metrics(cond, s1_eff, s3, cap, w1, w3, cost_fixed_mean, cost_genie_mean):
    switch_time, fired = detector_switch_time(cond, s1_eff, cap)
    cost, success = weighted_cost(w1, w3, s1_eff, s3, switch_time)
    rescuable = s1_eff <= cap           # cap 안에서 1단계가 성공할 프레임
    hopeless = ~rescuable
    false_alarm = float((fired & rescuable).sum() / max(int(rescuable.sum()), 1))
    miss = float(((~fired) & hopeless).sum() / max(int(hopeless.sum()), 1))
    gain_denominator = cost_fixed_mean - cost_genie_mean
    attain = ((cost_fixed_mean - float(cost.mean())) / gain_denominator
              if gain_denominator > 1e-12 else float("nan"))
    return {"cost": float(cost.mean()), "fer": float(1.0 - success.mean()),
            "early_rate": float(fired.mean()), "false_alarm": false_alarm,
            "miss": miss, "attain": attain}


def rho_at(traj_err, s1_eff, iteration):
    """반복 iteration까지 1단계가 실패 중인 프레임의 평균 잔여 오류 bit 수 (논문 ρ 대응)."""
    failing = s1_eff > iteration
    if not failing.any():
        return float("nan")
    return float(traj_err[failing, iteration].mean())


def entry_threshold_scan(sw0, cost_enter, cost_skip):
    """초기 syndrome weight 임계(진입 게이트) 전수 탐색: sw0 < th만 1단계 진입.
    반환: (최적 진입 비율, 최적 임계 근사값, 최적 평균 비용)."""
    order = np.argsort(sw0, kind="stable")
    delta_sorted = (cost_enter - cost_skip)[order]
    prefix = np.concatenate([[0.0], np.cumsum(delta_sorted)])
    k_best = int(np.argmin(prefix))
    cost_best = (cost_skip.sum() + prefix[k_best]) / len(sw0)
    sw0_sorted = sw0[order]
    if k_best == 0:
        threshold = 0
    elif k_best == len(sw0):
        threshold = int(sw0_sorted[-1]) + 1
    else:
        threshold = int(sw0_sorted[k_best - 1]) + 1   # 진입 쪽 마지막 sw0 직후
    return k_best / len(sw0), threshold, float(cost_best)


# ---------- 합성 검증 ----------
def verify_fixed_composition(point, s1_eff, s3, fixed_run):
    """고정 4회 실측과 (s1, s3) 합성의 전 프레임 일치 검증."""
    rescued = s1_eff <= FIXED_SWITCH
    predicted_success = rescued | (s3 > 0)
    predicted_stage1 = np.where(rescued, s1_eff, FIXED_SWITCH).astype(np.int64)
    predicted_stage2 = np.where(rescued, 0,
                                np.where(s3 > 0, s3, STAGE2_BUDGET)).astype(np.int64)
    ok = (np.array_equal(predicted_success, fixed_run["success"])
          and np.array_equal(predicted_stage1, fixed_run["stage1_iterations"])
          and np.array_equal(predicted_stage2, fixed_run["stage2_iterations"]))
    if not ok:
        mismatch = int((predicted_success != fixed_run["success"]).sum()
                       + (predicted_stage1 != fixed_run["stage1_iterations"]).sum()
                       + (predicted_stage2 != fixed_run["stage2_iterations"]).sum())
        raise RuntimeError(
            f"E={point}: 고정 4회 실측과 합성 불일치 {mismatch}건 "
            "(전환 시 CN 상태 초기화 전제가 깨짐)")


def verify_base_equivalence(code, llr_matrix, chan_batch, s3_batch):
    """switch_iter=0 모형과 BaseDecoder(3bit 단독)의 궤적 동등성 검증 (첫 배치)."""
    base_result = BaseDecoder(code, llr_matrix).decoder_main(chan_batch)
    base_iter = base_result["decode_success_iteration"]
    expected = np.where(base_result["success"] & (base_iter <= STAGE2_BUDGET),
                        base_iter, 0)
    if not np.array_equal(s3_batch.astype(np.int64), expected.astype(np.int64)):
        raise RuntimeError("switch_iter=0 모형이 BaseDecoder와 불일치 "
                           "(2단계 테이블 재시작 전제가 깨짐)")


def main():
    frames_per_point = FRAMES_PER_POINT
    if len(sys.argv) > 1:
        frames_per_point = int(sys.argv[1])

    code = QCCode.load(H_MATRIX_PATH)
    llr_matrix = LLRMatrix.load(LLR_MATRIX_PATH)
    print(f"H: {os.path.basename(H_MATRIX_PATH)} "
          f"(base {code.M_b}x{code.N_b}, z={code.z}, N={code.N}, K={code.K})")
    print(f"LLR: {os.path.basename(LLR_MATRIX_PATH)} (max_iter={llr_matrix.max_iter})")
    print(f"frames/point={frames_per_point}, window={WINDOW}, fixed={FIXED_SWITCH}, "
          f"stage2_budget={STAGE2_BUDGET}, w1={W1}, w3={W3}, seed={SEED}")

    decoder_stage1 = make_decoder(code, llr_matrix, switch_iter=WINDOW,
                                  stage2_max_iter=0, collect_stage1_trajectory=True)
    decoder_3bit = make_decoder(code, llr_matrix, switch_iter=0,
                                stage2_max_iter=STAGE2_BUDGET)
    decoder_fixed = make_decoder(code, llr_matrix, switch_iter=FIXED_SWITCH,
                                 stage2_max_iter=STAGE2_BUDGET)

    stamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    out_dir = os.path.join(EXPERIMENT_DIR, "Sim_Output", f"scan_{stamp}")
    os.makedirs(out_dir, exist_ok=True)

    main_rows = []
    detector_rows = []
    point_data = {}          # E -> dict (풀링 분석과 재튜닝 스윕이 재사용)
    base_checked = False

    for point in GRID:
        chan_batches = make_channel_batches(code, point, frames_per_point, SEED)
        r1 = run_frames(decoder_stage1, chan_batches,
                        ["stage1_success_iteration", "stage1_traj_syndrome_weight",
                         "stage1_traj_flip_count", "stage1_traj_err_bits"])
        r3 = run_frames(decoder_3bit, chan_batches,
                        ["stage2_success_iteration", "success"])
        rf = run_frames(decoder_fixed, chan_batches,
                        ["success", "stage1_iterations", "stage2_iterations"])

        s1 = r1["stage1_success_iteration"].astype(np.int64)
        s1_eff = np.where(s1 > 0, s1, np.inf)
        s3 = r3["stage2_success_iteration"].astype(np.int64)
        traj_sw = r1["stage1_traj_syndrome_weight"]
        traj_flip = r1["stage1_traj_flip_count"]
        traj_err = r1["stage1_traj_err_bits"]

        if not base_checked:
            verify_base_equivalence(code, llr_matrix, chan_batches[0],
                                    s3[:chan_batches[0]["hd"].shape[0]])
            base_checked = True
        verify_fixed_composition(point, s1_eff, s3, rf)

        cost_skip, _ = weighted_cost(W1, W3, s1_eff, s3, 0)        # 3bit 단독
        cost_fixed4, success_fixed4 = weighted_cost(W1, W3, s1_eff, s3, FIXED_SWITCH)
        cost_fixed8, _ = weighted_cost(W1, W3, s1_eff, s3, WINDOW)
        cost_genie4, _, _ = genie_policy(W1, W3, s1_eff, s3, FIXED_SWITCH)
        cost_genie8, success_genie8, stay_chosen = genie_policy(W1, W3, s1_eff, s3, WINDOW)

        row = {
            "E": point,
            "sw0_mean": float(traj_sw[:, 0].mean()),
            "p_s1_le4": float((s1_eff <= FIXED_SWITCH).mean()),
            "p_s1_le8": float((s1_eff <= WINDOW).mean()),
            "s1_mean": float(s1[s1 > 0].mean()) if (s1 > 0).any() else float("nan"),
            "s3_mean": float(s3[s3 > 0].mean()) if (s3 > 0).any() else float("nan"),
            "rho4": rho_at(traj_err, s1_eff, FIXED_SWITCH),
            "cost_3bit": float(cost_skip.mean()),
            "cost_fixed4": float(cost_fixed4.mean()),
            "cost_fixed8": float(cost_fixed8.mean()),
            "cost_genie4": float(cost_genie4.mean()),
            "cost_genie8": float(cost_genie8.mean()),
            "genie_gain_pct": float(100.0 * (cost_fixed4.mean() - cost_genie8.mean())
                                    / cost_fixed4.mean()),
            "genie_stay_frac": float(stay_chosen.mean()),
            "fer_fixed4": float(1.0 - success_fixed4.mean()),
            "fer_genie8": float(1.0 - success_genie8.mean()),
        }
        main_rows.append(row)
        print(f"[E={point:3d}] sw0={row['sw0_mean']:7.1f} "
              f"p(s1<=4)={row['p_s1_le4']:.3f} p(s1<=8)={row['p_s1_le8']:.3f} "
              f"rho4={row['rho4']:6.1f} | cost 3bit={row['cost_3bit']:6.2f} "
              f"fixed4={row['cost_fixed4']:6.2f} fixed8={row['cost_fixed8']:6.2f} "
              f"genie4={row['cost_genie4']:6.2f} genie8={row['cost_genie8']:6.2f} "
              f"(genie 절감 {row['genie_gain_pct']:5.1f}%, stay={row['genie_stay_frac']:.3f})")

        conditions = detector_conditions(traj_sw, traj_flip)
        for det_name, cond in conditions.items():
            for cap in (FIXED_SWITCH, WINDOW):
                met = detector_metrics(cond, s1_eff, s3, cap, W1, W3,
                                       float(cost_fixed4.mean()),
                                       float(cost_genie8.mean()))
                detector_rows.append({"E": point, "detector": det_name,
                                      "cap": cap, **met})

        point_data[point] = {
            "s1_eff": s1_eff, "s3": s3, "traj_err": traj_err,
            "sw0": traj_sw[:, 0].copy(),
            "cost_fixed4": cost_fixed4, "cost_skip": cost_skip,
            "chan_batches": chan_batches if point in SWEEP_POINTS else None,
        }

    # ---------- 감지기 표 ----------
    print("\n감지기 비교 (cap = 전환 상한, attain = genie8 대비 달성률):")
    print("  E   detector   cap   cost   FER      조기전환률 오경보율 미검출률 달성률")
    for row in detector_rows:
        print(f"  {row['E']:3d} {row['detector']:<10s} {row['cap']:3d} "
              f"{row['cost']:6.2f} {row['fer']:.2e} {row['early_rate']:9.3f} "
              f"{row['false_alarm']:8.3f} {row['miss']:8.3f} {row['attain']:6.3f}")

    # ---------- 진입 임계 (syn_th_BF0 대응) 풀링 탐색 ----------
    sw0_all = np.concatenate([point_data[p]["sw0"] for p in GRID])
    cost_enter_all = np.concatenate([point_data[p]["cost_fixed4"] for p in GRID])
    cost_skip_all = np.concatenate([point_data[p]["cost_skip"] for p in GRID])
    enter_frac, threshold, cost_best = entry_threshold_scan(
        sw0_all, cost_enter_all, cost_skip_all)
    always_enter = float(cost_enter_all.mean())
    never_enter = float(cost_skip_all.mean())
    oracle_entry = float(np.minimum(cost_enter_all, cost_skip_all).mean())
    print(f"\n진입 임계 탐색 (전 포인트 풀링, 에러 수 격자 균등 가중):")
    print(f"  항상 진입 {always_enter:.2f} | 진입 없음(3bit 단독) {never_enter:.2f} | "
          f"최적 단일 임계 sw0<{threshold} (진입율 {enter_frac:.3f}) {cost_best:.2f} | "
          f"프레임별 oracle 진입 {oracle_entry:.2f}")

    # ---------- w3 민감도 (풀링) ----------
    print("\nw3 민감도 (풀링 평균 가중 반복, genie8 절감률):")
    s1_all = np.concatenate([point_data[p]["s1_eff"] for p in GRID])
    s3_all = np.concatenate([point_data[p]["s3"] for p in GRID])
    sensitivity_rows = []
    for w3 in (W3,) + W3_SENSITIVITY:
        cost_fixed, _ = weighted_cost(W1, w3, s1_all, s3_all, FIXED_SWITCH)
        cost_genie, _, _ = genie_policy(W1, w3, s1_all, s3_all, WINDOW)
        gain = 100.0 * (cost_fixed.mean() - cost_genie.mean()) / cost_fixed.mean()
        sensitivity_rows.append({"w3": w3, "cost_fixed4": float(cost_fixed.mean()),
                                 "cost_genie8": float(cost_genie.mean()),
                                 "gain_pct": float(gain)})
        print(f"  w1={W1}, w3={w3}: fixed4={cost_fixed.mean():6.2f} "
              f"genie8={cost_genie.mean():6.2f} 절감 {gain:5.1f}%")

    # ---------- 1bit 포화 크기와 포화 범위 재튜닝 (소규모) ----------
    print("\n포화 크기 재튜닝 (rho4 = 반복 4 실패 프레임 평균 잔여 오류 bit):")
    print("  E   dv조건  포화크기  p(s1<=4) p(s1<=8)  rho4    cost_fixed4")
    sweep_rows = []
    for point in SWEEP_POINTS:
        data = point_data[point]
        for dv_above in SWEEP_DV_VARIANTS:
            for mag in SWEEP_SATURATION_MAGS:
                if dv_above == 5 and mag == 7.0:
                    s1_eff_v, traj_err_v = data["s1_eff"], data["traj_err"]
                else:
                    decoder_variant = make_decoder(
                        code, llr_matrix, switch_iter=WINDOW, stage2_max_iter=0,
                        collect_stage1_trajectory=True,
                        stage1_saturation_mag=mag, stage1_saturate_dv_above=dv_above)
                    rv = run_frames(decoder_variant, data["chan_batches"],
                                    ["stage1_success_iteration", "stage1_traj_err_bits"])
                    s1_v = rv["stage1_success_iteration"].astype(np.int64)
                    s1_eff_v = np.where(s1_v > 0, s1_v, np.inf)
                    traj_err_v = rv["stage1_traj_err_bits"]
                cost_v, _ = weighted_cost(W1, W3, s1_eff_v, data["s3"], FIXED_SWITCH)
                sweep_row = {
                    "E": point, "dv_above": dv_above, "mag": mag,
                    "p_s1_le4": float((s1_eff_v <= FIXED_SWITCH).mean()),
                    "p_s1_le8": float((s1_eff_v <= WINDOW).mean()),
                    "rho4": rho_at(traj_err_v, s1_eff_v, FIXED_SWITCH),
                    "cost_fixed4": float(cost_v.mean()),
                }
                sweep_rows.append(sweep_row)
                dv_label = f"dv>{dv_above}" if dv_above else "전열"
                print(f"  {point:3d} {dv_label:<6s} {mag:7.0f} "
                      f"{sweep_row['p_s1_le4']:9.3f} {sweep_row['p_s1_le8']:8.3f} "
                      f"{sweep_row['rho4']:7.1f} {sweep_row['cost_fixed4']:10.2f}")

    # ---------- CSV 저장 ----------
    def save_rows(path, rows):
        if not rows:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    save_rows(os.path.join(out_dir, "main_table.csv"), main_rows)
    save_rows(os.path.join(out_dir, "detector_table.csv"), detector_rows)
    save_rows(os.path.join(out_dir, "sweep_table.csv"), sweep_rows)
    save_rows(os.path.join(out_dir, "w3_sensitivity.csv"), sensitivity_rows)
    with open(os.path.join(out_dir, "entry_threshold.txt"), "w", encoding="utf-8") as f:
        f.write(f"always_enter={always_enter:.4f}\nnever_enter={never_enter:.4f}\n"
                f"best_threshold_sw0={threshold} (enter_frac={enter_frac:.4f}, "
                f"cost={cost_best:.4f})\noracle_entry={oracle_entry:.4f}\n")
    print(f"\nsaved: {out_dir}")


if __name__ == "__main__":
    main()
