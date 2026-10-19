"""bf_stage_switch: 1bit 포화 단계와 3bit 단계의 2단 HD 복호 모형 (ieee:8742682, 2019).

재정의: decoder_main 전체 (단계 구조라는 근본 변경, 새논문적용규칙.md 2절 3번 갈래).
C++ 대응 (0_LDPC_original/src/decoder.cpp의 HD HBF 2단 구조):
  1단계 = VN_Cal_HD의 1bit precision 분기 (flag_BF_on, iter <= ITER_MAX_HBF,
          dv > 5 열의 VNU 출력을 ±EDGE_MAG_7로 고정)
  전환   = Is_Iter_Type_Edge_Clear(ITER_MAX_HBF + 1) → Clear_Edge_Restart
          (CN 상태를 비우고 syndrome만 유지. 1단계의 중간 결과는 2단계로 이어지지 않는다)
  2단계 = 3bit min-sum (부모 BaseDecoder 동작 그대로)

C++와 다른 점 (스크리닝 단순화):
  - ㉮ LLR 테이블: C++는 1단계용 row(반복 1-4)와 2단계용 row(반복 5 이후)를 따로 두지만,
    여기서는 3bit 단독용으로 튜닝된 테이블 하나를 1단계(반복 번호 그대로)와
    2단계(1부터 다시)가 나눠 쓴다. 2단계가 테이블을 1부터 다시 소비하므로
    switch_iter = 0이면 BaseDecoder(3bit 단독)와 같은 궤적이 된다
    (stage2_max_iter 반복 예산 안에서. scan.py가 이 동등성을 검증한다)
  - ㉯ 성공 판정은 본체 관례대로 genie다 (C++는 CRC)
  - ㉰ 진입 판정(Select_BF의 syn_th_BF0)은 디코더 안에 두지 않고 scan.py가
    초기 syndrome weight 궤적으로 후처리 평가한다

결과 dict 추가 항목 (나머지는 BaseDecoder.decoder_main과 동일):
  stage1_iterations / stage2_iterations: (B,) 단계별로 실제 돈 반복 수
  stage1_success: (B,) bool. 1단계 안에서 성공
  stage1_success_iteration / stage2_success_iteration: (B,) 각 단계 내부 번호 기준
    성공 반복 (실패 또는 해당 단계 미성공이면 0)
  decode_success_iteration: 성공 프레임이 실제로 돈 총 반복 수로 통일
    (sim.run_fer_point의 avg_iter 집계가 이 값을 쓴다)
  collect_stage1_trajectory 시 (전환 감지기 평가용, 열 i = 반복 i, 열 0 = 복호 전):
    stage1_traj_syndrome_weight: (B, switch_iter+1) 반복별 syndrome weight.
      성공으로 빠진 뒤의 칸은 -1
    stage1_traj_flip_count: (B, switch_iter+1) 직전 반복 대비 판정비트가 바뀐 수 (동일 규칙)
    stage1_traj_err_bits: (B, switch_iter+1) 반복별 잔여 오류 bit 수
      (genie, codeword 전체 기준. 동일 규칙)
"""
import numpy as np

from src.decoder import BaseDecoder, LOG_ITEMS


class StageSwitchDecoder(BaseDecoder):
    """1bit 포화 1단계 + 3bit 2단계. 전환 시 CN 상태를 비운다 (C++ HD 구조 대응)."""

    switch_iter = 4               # 1단계 반복 수 t (0이면 3bit 단독)
    stage2_max_iter = 30          # 전환 후 2단계 반복 예산 (0이면 1단계 단독)
    stage1_saturation_mag = 7.0   # 1bit 포화 크기 (C++ EDGE_MAG_7 대응)
    stage1_saturate_dv_above = 5  # 이 dv 초과 열만 포화 (C++ v_deg > DV_5 대응. 0이면 전 열)
    collect_stage1_trajectory = False

    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix)
        self._in_stage1 = False
        self._saturate_current_column = False

    # ---------- 1bit 포화 (C++ VN_Cal_HD 1bit precision 분기 대응) ----------
    def _process_column(self, state, iteration, col):
        self._saturate_current_column = (
            self._in_stage1
            and int(self.code.col_deg[col]) > self.stage1_saturate_dv_above)
        super()._process_column(state, iteration, col)

    def _vnu_quantize(self, raw, vnu_in, th):
        vnu_out = super()._vnu_quantize(raw, vnu_in, th)
        if self._saturate_current_column:
            mag = np.float32(self.stage1_saturation_mag)
            # 부모 출력의 부호를 유지하고 크기만 고정 (부모 출력 크기는 1 이상이라 0이 없고,
            # raw == 0일 때 VNU_in의 부호를 따르는 C++ Zero V-out 처리도 부모가 이미 했다)
            vnu_out = np.where(vnu_out > 0, mag, -mag)
        return vnu_out

    # ---------- 2단 복호 흐름 ----------
    def decoder_main(self, channel_out, collect_profile=False, log=None):
        log = set() if log is None else set(log)
        unknown_log_items = log - LOG_ITEMS
        if unknown_log_items:
            raise ValueError(
                f"log 항목 {sorted(unknown_log_items)} 미지원 (허용: {sorted(LOG_ITEMS)})")
        switch_iter = int(self.switch_iter)
        stage2_max_iter = int(self.stage2_max_iter)
        if not 0 <= switch_iter <= self.max_iter:
            raise ValueError(f"switch_iter={switch_iter}: 0-{self.max_iter} 범위여야 함")
        if not 0 <= stage2_max_iter <= self.max_iter:
            raise ValueError(f"stage2_max_iter={stage2_max_iter}: 0-{self.max_iter} 범위여야 함")

        read_bit, region = self._read_channel_input(channel_out)
        if region is not None:
            raise NotImplementedError("StageSwitchDecoder는 HD 전용 (C++ HBF가 HD 전용)")
        state = self._init_state(read_bit, region, log)
        batch_size = read_bit.shape[0]
        RESET = np.float32(self._edge_mag[0])

        stage1_iterations = np.zeros(batch_size, np.int64)
        stage2_iterations = np.zeros(batch_size, np.int64)
        if self.collect_stage1_trajectory:
            traj_shape = (batch_size, switch_iter + 1)
            traj_sw = np.full(traj_shape, -1, np.int64)
            traj_flip = np.full(traj_shape, -1, np.int64)
            traj_err = np.full(traj_shape, -1, np.int64)
            traj_sw[:, 0] = state.prev_csw
            traj_flip[:, 0] = 0
            traj_err[:, 0] = state.read_bit.sum(axis=(-2, -1), dtype=np.int64)
            prev_decision_bits = state.read_bit.copy()   # (B, N_b, z) 원 배치 크기 유지

        # ---- 1단계: 1bit 포화 min-sum ----
        self._in_stage1 = True
        all_frames_done = False
        try:
            for iteration in range(1, switch_iter + 1):
                self._run_iteration(state, iteration)
                stage1_iterations[state.idx_active] += 1
                if self.collect_stage1_trajectory:
                    idx = state.idx_active
                    traj_sw[idx, iteration] = state.prev_csw
                    traj_err[idx, iteration] = state.err_bits
                    traj_flip[idx, iteration] = (
                        (state.decision_bits ^ prev_decision_bits[idx])
                        .sum(axis=(-2, -1), dtype=np.int64))
                    prev_decision_bits[idx] = state.decision_bits
                self._record_iteration(state, collect_profile)
                if self._check_errors(state, iteration):
                    all_frames_done = True
                    break
        finally:
            self._in_stage1 = False
        stage1_success = state.success.copy()
        stage1_success_iteration = np.where(
            stage1_success, state.decode_success_iteration, 0).astype(np.int32)

        # ---- 전환: CN 상태를 비우고 syndrome 유지 (C++ Clear_Edge_Restart 대응) ----
        if not all_frames_done and stage2_max_iter > 0:
            state.min1.fill(RESET)
            state.min2.fill(RESET)
            state.min1_pos.fill(-1)
            state.check_sum.fill(0)
            state.edge_sgn.fill(0)
            state.prev_csw = state.syndrome.sum(axis=(-2, -1)).astype(np.int64)
            # ---- 2단계: 3bit min-sum (LLR 테이블을 1부터 다시 소비) ----
            for iteration in range(1, stage2_max_iter + 1):
                self._run_iteration(state, iteration)
                stage2_iterations[state.idx_active] += 1
                self._record_iteration(state, collect_profile)
                if self._check_errors(state, iteration):
                    break

        result = self._build_result(state, collect_profile)
        stage2_success = result["success"] & ~stage1_success
        result["stage1_iterations"] = stage1_iterations
        result["stage2_iterations"] = stage2_iterations
        result["stage1_success"] = stage1_success
        result["stage1_success_iteration"] = stage1_success_iteration
        result["stage2_success_iteration"] = np.where(
            stage2_success, result["decode_success_iteration"], 0).astype(np.int32)
        result["decode_success_iteration"] = np.where(
            result["success"], stage1_iterations + stage2_iterations, 0).astype(np.int32)
        if self.collect_stage1_trajectory:
            result["stage1_traj_syndrome_weight"] = traj_sw
            result["stage1_traj_flip_count"] = traj_flip
            result["stage1_traj_err_bits"] = traj_err
        return result
