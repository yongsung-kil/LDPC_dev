"""atbf_quiescent: 비트별 적응 임계 BF, 휴면, 전이 검출 탈출 (ieee:5671820, 2010).

재정의: decoder_main 전체 (BF 계열은 교체용 함수 6개에 맞지 않음,
새논문적용규칙 2절 3항). HD 채널 출력으로 BF 단계를 먼저 돌리고,
BF가 못 푼 프레임은 부모 BaseDecoder(HD min-sum)로 재복호해 합산 FER를 만든다.
엔진 부품(_read_channel_input, 부모 decoder_main)은 부모 것을 호출해 재사용한다.

사다리 4단 (VARIANT, 공용 BF 엔진 _run_bf_stage 하나에 스위치로 구현):
  gdbf    : 고정 임계. 매 iteration ∆k < λ0 이면 반전 (λ 조임 없음, 기준 구현)
  atbf    : 비트별 λk. ∆k < λk 이면 반전, 아니면 λk = θ·λk 로 0 쪽 조임
  atbf_q  : atbf + 휴면. λk >= PHI1 인 비트는 다음 iteration부터 처리 스킵
  es_atbf : atbf_q + 전이 검출. 어느 비트든 λk가 PHI1에 처음 도달하는 순간
            BF 탈출 (ES_OBSERVE=True면 오판율 측정을 위해 창 끝까지 계속 돌려
            "트리거를 무시했다면 수렴했을지"를 기록하되, 성공/비트 처리 집계는
            트리거 시점에서 끊는다)

반전 함수 (HD 치환, 메모 4.2절):
  ∆k = (현재 판정이 채널 읽기와 일치하면 +W_dv, 불일치하면 -W_dv)
       + (dv - 2 x 불만족 검사 수)
  W_dv는 LLR matrix에서 ch가 유효한 첫 iteration row의 dv별 채널 LLR 크기를
  edge 최대 레벨로 나눈 비율. 신드롬 항이 검사당 1이므로 채널 항도 edge당
  크기 1 기준으로 맞춘 것이며, C++ HBF 구간의 sum_t(채널 LLR + dv개의
  ±EDGE_MAG_7 포화 edge 합)와 같은 비율이다. 채널 LLR 크기(8-10)를 그대로
  쓰면 dv가 2-4인 열에서 ∆k 하한이 W_dv - dv > 0 이 되어 채널과 일치하는
  비트의 첫 반전이 불가능하다 (메모 7㉳의 치환 등가성 질문에 대한 측정 결과).

자체 수집 지표 (인스턴스 누적 self.bf_stats, scan.py가 리셋하고 판독):
  bf_success / bf_syndrome_zero / bf_miscorrection, bf_iters_sum,
  bit_evals_sum (활성 비트 수 합, 전력 대리),
  blockskip_bit_evals_sum (z 블록 단위 스킵만 가능할 때의 처리 비트 수 합),
  iter_* (iteration별 곡선: 활성 프레임, 플립 수, 활성 비트, λ>=PHI1 비트,
  전부 휴면 블록 수), es_trigger_hist / es_misfire, fallback_*
"""
import numpy as np

from src.decoder import BaseDecoder

VARIANTS = ("gdbf", "atbf", "atbf_q", "es_atbf")


class ATBFLadderDecoder(BaseDecoder):
    VARIANT = "es_atbf"     # 사다리 단 선택 (VARIANTS 중 하나)
    BF_WINDOW = 8           # BF 창 (최대 BF iteration 수)
    LAMBDA0 = -4.0          # λ 초기값 (음수. 기본값은 scan phase 1 선정 조합)
    THETA = 0.5             # λ 조임 상수 (하드웨어는 2^-d 시프트)
    PHI1 = -0.25            # 휴면 임계 (λk >= PHI1 이면 휴면. 조임 궤적의 끝점)
    FALLBACK = True         # BF 실패 프레임을 부모 min-sum으로 재복호
    ES_OBSERVE = True       # es_atbf: 트리거 후에도 창 끝까지 돌려 수렴 여부 기록

    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix)
        if llr_matrix.mode != "HD":
            raise ValueError("ATBF 스크리닝은 HD 전용 (LLR matrix 파일명 확인)")
        if self.VARIANT not in VARIANTS:
            raise ValueError(f"VARIANT={self.VARIANT!r}: {VARIANTS} 중 하나여야 함")
        if not self.LAMBDA0 < 0:
            raise ValueError(f"LAMBDA0={self.LAMBDA0}: 음수여야 함")
        if not 0.0 < self.THETA < 1.0:
            raise ValueError(f"THETA={self.THETA}: 0-1 사이여야 함")
        # W_dv: ch가 전부 유효(>=1)한 첫 iteration row의 dv별 채널 LLR 크기
        w_dv = None
        for iteration in range(1, llr_matrix.max_iter + 1):
            row = int(llr_matrix.row_index(iteration, np.zeros(1, np.int64))[0])
            ch = llr_matrix.row_ch[row, :, 0]
            if np.all(ch >= 1):
                w_dv = ch.astype(np.float32)
                break
        if w_dv is None:
            raise ValueError("LLR matrix에서 유효한 채널 LLR row를 찾지 못함")
        self.w_dv = w_dv / np.float32(self._edge_mag[0])        # (num_dv,) 비율 정규화
        self.col_w = self.w_dv[self._col_dv_idx]                # (N_b,) column별 W_dv
        self.col_dv = code.col_deg.astype(np.float32)           # (N_b,) column별 dv
        self.reset_bf_stats()

    # ---------- 자체 수집 지표 ----------
    def reset_bf_stats(self):
        window = self.BF_WINDOW
        self.bf_stats = {
            "frames": 0,
            "bf_success": 0,            # BF 단계 genie 성공 (es는 트리거 전 수렴만)
            "bf_syndrome_zero": 0,      # 신드롬 0 도달 (genie 무관)
            "bf_miscorrection": 0,      # 신드롬 0인데 genie 실패 (오수렴)
            "bf_iters_sum": 0,          # BF iteration 소비 합 (es는 트리거에서 끊음)
            "bit_evals_sum": 0,         # 활성 비트 수 합 (비트 단위 스킵 전제)
            "blockskip_bit_evals_sum": 0,  # z 블록 단위 스킵 전제의 처리 비트 수 합
            "iter_active_frames": np.zeros(window, np.int64),
            "iter_flips": np.zeros(window, np.int64),
            "iter_active_bits": np.zeros(window, np.int64),
            "iter_reach_bits": np.zeros(window, np.int64),      # λk >= PHI1 비트 수
            "iter_full_q_blocks": np.zeros(window, np.int64),   # 전부 휴면 블록 수
            "es_trigger_hist": np.zeros(window + 1, np.int64),  # [0] = 미트리거
            "es_misfire": 0,            # 트리거 무시 시 창 안에서 수렴했을 프레임 수
            "fallback_frames": 0,
            "fallback_success": 0,
            "fallback_iters_sum": 0,    # 폴백 iteration 합 (실패 프레임은 max_iter)
        }

    # ---------- BF 단계 ----------
    def _bf_delta(self, decision_bits, read_bit, syndrome):
        """∆k 배열 (B, N_b, z). syndrome은 현재 판정 기준 H·decision_bits."""
        code = self.code
        B = decision_bits.shape[0]
        unsat = np.zeros((B, code.N_b, code.z), np.float32)
        for e in range(code.E):
            row_blk, col, shift = code.edge_row[e], code.edge_col[e], code.edge_shift[e]
            unsat[:, col, :] += np.roll(syndrome[:, row_blk, :], shift, axis=-1)
        agree_sign = np.where(decision_bits == read_bit,
                              np.float32(1.0), np.float32(-1.0))
        return (agree_sign * self.col_w[None, :, None]
                + self.col_dv[None, :, None] - 2.0 * unsat)

    def _run_bf_stage(self, read_bit):
        """BF 단계 실행. 반환: (bf_success 마스크 (B,), converge_iter (B,),
        BF 종료 시점 판정비트). 집계는 self.bf_stats에 누적."""
        code = self.code
        stats = self.bf_stats
        variant = self.VARIANT
        window = self.BF_WINDOW
        theta = np.float32(self.THETA)
        phi1 = np.float32(self.PHI1)
        adapt = variant != "gdbf"
        use_q = variant in ("atbf_q", "es_atbf")

        B, N_b, z = read_bit.shape
        N = N_b * z
        decision_bits = read_bit.copy()
        lam = np.full((B, N_b, z), np.float32(self.LAMBDA0), np.float32)
        quiescent = np.zeros((B, N_b, z), bool)
        running = np.ones(B, bool)
        converge_iter = np.zeros(B, np.int32)   # 0 = 창 안 미수렴
        trigger_iter = np.zeros(B, np.int32)    # 0 = 미트리거 (λ >= PHI1 첫 등장)
        stall_iter = np.zeros(B, np.int32)      # 0 = 전 비트 휴면 미발생
        # 프레임 x iteration 처리 비트 수 (1-base iteration, [:, 0]은 미사용)
        active_bits_ft = np.zeros((B, window + 1), np.int64)
        blockskip_bits_ft = np.zeros((B, window + 1), np.int64)

        for t in range(1, window + 1):
            # 직전 iteration 반전 결과의 수렴 검사 (t=1은 채널 자체 수렴 검사)
            syndrome = code.syndrome(decision_bits)
            syn_nonzero = syndrome.any(axis=(-2, -1))
            newly_converged = running & ~syn_nonzero
            converge_iter[newly_converged] = t - 1
            running &= syn_nonzero
            if not running.any():
                break
            # 처리량 집계 (이번 iteration에 평가하는 비트 수, 처리 전 상태 기준)
            q_count = quiescent.sum(axis=(1, 2)) if use_q else np.zeros(B, np.int64)
            full_q_blocks = quiescent.all(axis=2).sum(axis=1) if use_q \
                else np.zeros(B, np.int64)
            active_bits_ft[:, t] = np.where(running, N - q_count, 0)
            blockskip_bits_ft[:, t] = np.where(running, N - z * full_q_blocks, 0)
            stats["iter_active_frames"][t - 1] += int(running.sum())
            stats["iter_active_bits"][t - 1] += int(active_bits_ft[:, t].sum())
            stats["iter_full_q_blocks"][t - 1] += int(full_q_blocks[running].sum())
            # 반전 판정
            delta = self._bf_delta(decision_bits, read_bit, syndrome)
            flip = delta < lam
            if use_q:
                flip &= ~quiescent
            flip &= running[:, None, None]
            decision_bits ^= flip.astype(np.uint8)
            stats["iter_flips"][t - 1] += int(flip.sum())
            # λ 조임 (미반전 비트만. 휴면 비트는 유지)
            if adapt:
                scale = ~flip & running[:, None, None]
                if use_q:
                    scale &= ~quiescent
                lam = np.where(scale, lam * theta, lam)
                reach = lam >= phi1
                stats["iter_reach_bits"][t - 1] += int(reach[running].sum())
                newly_triggered = running & (trigger_iter == 0) & reach.any(axis=(1, 2))
                trigger_iter[newly_triggered] = t
                if use_q:
                    quiescent = reach
                    newly_stalled = running & (stall_iter == 0) & quiescent.all(axis=(1, 2))
                    stall_iter[newly_stalled] = t
                    running &= ~(stall_iter > 0)   # 전 비트 휴면 = 더 돌 수 없음
        else:
            # 창 마지막 iteration 반전 결과의 수렴 검사
            syndrome = code.syndrome(decision_bits)
            syn_nonzero = syndrome.any(axis=(-2, -1))
            newly_converged = running & ~syn_nonzero
            converge_iter[newly_converged] = window

        # 프레임별 유효 종료 시점 (집계 기준)
        converged = converge_iter > 0
        stop = np.where(converged, converge_iter, window)
        if use_q:
            stop = np.where(~converged & (stall_iter > 0),
                            np.minimum(stop, stall_iter), stop)
        if variant == "es_atbf":
            es_stop = np.where(trigger_iter > 0,
                               np.minimum(stop, trigger_iter), stop)
            bf_converged = converged & (converge_iter <= es_stop)
            stats["es_misfire"] += int(
                ((trigger_iter > 0) & converged
                 & (converge_iter > trigger_iter)).sum())
            np.add.at(stats["es_trigger_hist"],
                      np.where(bf_converged, 0, trigger_iter), 1)
            stop = es_stop
        else:
            bf_converged = converged

        # genie 판정 (information 구간 = 앞쪽 N_b - M_b개 column block)
        num_info_col_blocks = code.N_b - code.M_b
        genie_ok = ~decision_bits[:, :num_info_col_blocks, :].any(axis=(-2, -1))
        bf_success = bf_converged & genie_ok

        cum_active = np.cumsum(active_bits_ft, axis=1)
        cum_blockskip = np.cumsum(blockskip_bits_ft, axis=1)
        frame_idx = np.arange(B)
        stats["frames"] += B
        stats["bf_success"] += int(bf_success.sum())
        stats["bf_syndrome_zero"] += int(bf_converged.sum())
        stats["bf_miscorrection"] += int((bf_converged & ~genie_ok).sum())
        stats["bf_iters_sum"] += int(stop.sum())
        stats["bit_evals_sum"] += int(cum_active[frame_idx, stop].sum())
        stats["blockskip_bit_evals_sum"] += int(cum_blockskip[frame_idx, stop].sum())
        return bf_success, converge_iter, decision_bits

    # ---------- 진입 함수 ----------
    def decoder_main(self, channel_out, collect_profile=False, log=None):
        """BF 단계 → 실패 프레임 부모 min-sum 재복호. 반환 형식은 부모와 동일
        (success, decode_success_iteration, final_err_bits, final_info_err_bits).
        collect_profile과 log는 폴백 구간에만 전달한다."""
        read_bit, _ = self._read_channel_input(channel_out)
        B = read_bit.shape[0]
        bf_success, converge_iter, _ = self._run_bf_stage(read_bit)

        success = bf_success.copy()
        decode_success_iteration = np.where(bf_success, converge_iter, 0).astype(np.int32)
        final_err_bits = np.zeros(B, np.int64)
        final_info_err_bits = np.zeros(B, np.int64)

        fail_idx = np.flatnonzero(~bf_success)
        if self.FALLBACK and len(fail_idx):
            fallback_result = BaseDecoder.decoder_main(
                self, {"mode": "HD", "hd": read_bit[fail_idx],
                       "sd": None, "cc": None}, log=log)
            fb_success = fallback_result["success"]
            fb_iter = fallback_result["decode_success_iteration"]
            success[fail_idx] = fb_success
            decode_success_iteration[fail_idx] = fb_iter
            final_err_bits[fail_idx] = fallback_result["final_err_bits"]
            final_info_err_bits[fail_idx] = fallback_result["final_info_err_bits"]
            stats = self.bf_stats
            stats["fallback_frames"] += len(fail_idx)
            stats["fallback_success"] += int(fb_success.sum())
            stats["fallback_iters_sum"] += int(
                np.where(fb_success, fb_iter, self.max_iter).sum())
        return {"success": success,
                "decode_success_iteration": decode_success_iteration,
                "final_err_bits": final_err_bits,
                "final_info_err_bits": final_info_err_bits}
