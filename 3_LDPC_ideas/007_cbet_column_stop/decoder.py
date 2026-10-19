"""cbet_column_stop: CB-ET(column 단위 조기 종료) 그림자 측정 (ieee:6865738, 2014).

재정의: _run_iteration (종료 로직 계측은 교체용 함수 6개에 해당하지 않음,
새논문적용규칙 2절 3항). _init_state와 _build_result는 기록 버퍼 추가용 확장.

그림자 측정: 실제 종료 판정(_check_errors의 genie 판정)은 BaseDecoder와 완전히
동일하게 두고, column마다 running CSW(check sum weight, 패리티 검사 위반 수)를
읽어 세 가지 종료 기준의 최초 발화 좌표만 프레임별로 기록한다. 판정에 개입하지
않으므로 FER는 정의상 불변이다 (run.py의 동등성 검증이 이를 실측 확인).

동시 산출하는 종료 기준 3개:
- ㉮ iteration 경계 종료: CSW == 0을 iteration 끝에서만 확인 (논문 비교 대상
  LC-ICA 대응)
- ㉯ PCRC 모사: 정보 column 구간을 4등분한 고정 지점 4개에서만 확인. CRC 통과를
  genie 정보 비트 오류 0으로 근사한다 (CRC 충돌 확률 무시)
- ㉰ CB-ET: column 블록 하나를 끝낼 때마다 running CSW == 0 확인

_run_iteration 본문은 BaseDecoder._run_iteration을 복제하고 계측만 끼워 넣었다
(본체는 수정 금지 대상이라 복제. 본체가 바뀌면 함께 갱신할 것). 복제가 본체와
어긋나면 iteration 끝의 assert 두 개가 즉시 잡는다.
"""
import numpy as np

from src.decoder import BaseDecoder


class CbEtShadowDecoder(BaseDecoder):
    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix=llr_matrix)
        # column별로 그 column의 edge가 닿는 CN row block 목록 (running CSW 증분 갱신용)
        self._col_row_blocks = [np.unique(code.edge_row[code.col_edges[col]])
                                for col in range(code.N_b)]
        # PCRC 모사 지점: 정보 column 구간(N_b - M_b개)의 4등분 경계 (처리 직후 확인)
        num_info = code.N_b - code.M_b
        self._pcrc_cols = [(num_info * k) // 4 - 1 for k in range(1, 5)]
        self._pcrc_point_of_col = {col: p for p, col in enumerate(self._pcrc_cols)}
        self._num_info = num_info
        self._shadow_records = []

    # ---------- 수집 API (run.py가 사용) ----------
    def shadow_reset(self):
        """포인트 측정 시작 전에 호출: 프레임별 기록 버퍼를 비운다."""
        self._shadow_records = []

    def shadow_frames(self):
        """지금까지 수집한 프레임별 기록을 배열 dict로 연결해 반환."""
        keys = ["success", "genie_iter", "boundary_hit_iter",
                "pcrc_hit_iter", "pcrc_hit_col",
                "cbet_hit_iter", "cbet_hit_col", "cbet_info_err", "cbet_total_err"]
        return {k: np.concatenate([r[k] for r in self._shadow_records])
                for k in keys}

    # ---------- 엔진 확장 (기록 버퍼) ----------
    def _init_state(self, read_bit, region, log):
        state = super()._init_state(read_bit, region, log)
        B = read_bit.shape[0]
        # 발화 iteration은 0 = 미발화 (iteration은 1부터)
        state.boundary_hit_iter = np.zeros(B, np.int32)
        state.pcrc_hit_iter = np.zeros(B, np.int32)
        state.pcrc_hit_col = np.full(B, -1, np.int32)
        state.cbet_hit_iter = np.zeros(B, np.int32)
        state.cbet_hit_col = np.full(B, -1, np.int32)
        state.cbet_info_err = np.full(B, -1, np.int64)   # 발화 순간 genie 정보 비트 오류
        state.cbet_total_err = np.full(B, -1, np.int64)  # 발화 순간 codeword 전체 오류
        return state

    def _build_result(self, state, collect_profile):
        out = super()._build_result(state, collect_profile)
        self._shadow_records.append({
            "success": state.success.copy(),
            "genie_iter": state.decode_success_iteration.copy(),
            "boundary_hit_iter": state.boundary_hit_iter,
            "pcrc_hit_iter": state.pcrc_hit_iter,
            "pcrc_hit_col": state.pcrc_hit_col,
            "cbet_hit_iter": state.cbet_hit_iter,
            "cbet_hit_col": state.cbet_hit_col,
            "cbet_info_err": state.cbet_info_err,
            "cbet_total_err": state.cbet_total_err,
        })
        return out

    # ---------- 계측 본체 ----------
    def _run_iteration(self, state, iteration):
        """BaseDecoder._run_iteration 복제 + column 경계 계측 (그림자 측정).
        계측은 상태를 읽기만 하고 판정 흐름에 개입하지 않는다."""
        RESET = np.float32(self._edge_mag[0])
        state.num_active_frames = state.read_bit.shape[0]

        state.edge_clear = self._is_edge_clear_iter(iteration)
        if state.edge_clear:
            state.min1.fill(RESET)
            state.min2.fill(RESET)
            state.min1_pos.fill(-1)
            state.check_sum.fill(0)
            state.edge_sgn.fill(0)
        if state.seed_mag is not None and self.llr_matrix.is_restart(iteration):
            # SD restart는 Pre 단계 (본체와 동일). column 계측 없이 경계 확인만 수행
            self._seed_channel_magnitudes(state)
            state.decision_bits[:] = state.read_bit
            self._collect_error_metrics(state)
            state.prev_csw = (state.check_sum ^ state.syndrome).sum(
                axis=(-2, -1)).astype(np.int64)
            self._shadow_boundary_check(state, iteration)
            return
        table_row_idx = self.llr_matrix.row_index(iteration, state.prev_csw)
        state.cur_ch_all = self.llr_matrix.row_ch[table_row_idx]
        state.cur_ch = state.cur_ch_all[:, :, 0]
        state.cur_th = self.llr_matrix.row_th[table_row_idx]

        # --- 계측 준비: 활성 프레임 기준 running 상태 ---
        idx_active = state.idx_active
        viol_rows = (state.check_sum ^ state.syndrome).sum(
            axis=-1, dtype=np.int64)                      # (활성, M_b) row block별 위반 수
        running_csw = viol_rows.sum(axis=1)               # (활성,)
        num_info = self._num_info
        info_err = state.decision_bits[:, :num_info, :].sum(axis=(1, 2), dtype=np.int64)
        total_err = state.decision_bits.sum(axis=(1, 2), dtype=np.int64)
        cbet_fired = state.cbet_hit_iter[idx_active] > 0
        pcrc_fired = state.pcrc_hit_iter[idx_active] > 0

        for col in self._column_order(iteration):
            old_col_err = state.decision_bits[:, col, :].sum(axis=-1, dtype=np.int64)
            self._process_column(state, iteration, col)
            # --- 계측: 판정비트 오류 수와 running CSW를 증분 갱신 ---
            delta_err = state.decision_bits[:, col, :].sum(
                axis=-1, dtype=np.int64) - old_col_err
            total_err += delta_err
            if col < num_info:
                info_err += delta_err
            rows = self._col_row_blocks[col]
            new_viol = (state.check_sum[:, rows, :] ^ state.syndrome[:, rows, :]).sum(
                axis=-1, dtype=np.int64)
            running_csw += new_viol.sum(axis=1) - viol_rows[:, rows].sum(axis=1)
            viol_rows[:, rows] = new_viol
            # ㉰ CB-ET: running CSW가 처음 0에 닿는 (iteration, column) 좌표
            newly_cbet = (running_csw == 0) & ~cbet_fired
            if newly_cbet.any():
                hit = idx_active[newly_cbet]
                state.cbet_hit_iter[hit] = iteration
                state.cbet_hit_col[hit] = col
                state.cbet_info_err[hit] = info_err[newly_cbet]
                state.cbet_total_err[hit] = total_err[newly_cbet]
                cbet_fired |= newly_cbet
            # ㉯ PCRC 모사: 4개 지점에서 genie 정보 비트 오류 0 확인
            point = self._pcrc_point_of_col.get(col)
            if point is not None:
                newly_pcrc = (info_err == 0) & ~pcrc_fired
                if newly_pcrc.any():
                    hit = idx_active[newly_pcrc]
                    state.pcrc_hit_iter[hit] = iteration
                    state.pcrc_hit_col[hit] = col
                    pcrc_fired |= newly_pcrc

        self._collect_error_metrics(state)
        state.prev_csw = (state.check_sum ^ state.syndrome).sum(
            axis=(-2, -1)).astype(np.int64)               # Compute_CSW
        # 계측 자가 검증: 증분 갱신이 본체 상태와 어긋나면 측정 버그
        assert np.array_equal(running_csw, state.prev_csw), "running CSW 불일치"
        assert np.array_equal(total_err, state.err_bits), "증분 오류 수 불일치"
        # ㉮ iteration 경계 종료 기준
        self._shadow_boundary_check(state, iteration)

    def _shadow_boundary_check(self, state, iteration):
        """iteration 끝에서 CSW == 0이 처음 되는 iteration 기록 (기준 ㉮)."""
        idx_active = state.idx_active
        newly = (state.prev_csw == 0) & (state.boundary_hit_iter[idx_active] == 0)
        if newly.any():
            state.boundary_hit_iter[idx_active[newly]] = iteration
