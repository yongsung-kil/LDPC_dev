"""upgdbf: UP-GDBF 전역 탐색 비트 플리핑 엔진 (ieee:9902993, 2022).

재정의: decoder_main 전체 (새논문적용규칙 2절 3항: 두 pass 구조의 BF는
교체용 함수 6개에 맞지 않는 근본 변경). 채널 입력 해석(_read_channel_input) 등
엔진 부품은 부모 BaseDecoder 것을 재사용한다.

도메인: all-zero codeword 전제라 read bit가 곧 에러 패턴이고, 추정 비트 x의
1이 곧 잔여 에러다 (본체 decoder.py의 flip 도메인과 같은 전제).

한 iteration은 논문의 두 pass 구조를 따른다:
  최대 탐색 pass: 비트별 에너지
      E = (x XOR y) + (연결된 위반 검사 수) + (직전 iteration 미플립이면 +1) + 난수(0/1)
    를 계산해 프레임 전역 최대 Emax를 찾는다
  플리핑 pass: E == Emax 인 비트를 모두 반전한다
난수 penalty는 iteration <= t_active 동안 꺼지고(결정적 동작), 이후
Bernoulli(p_eta)로 1이 된다 (논문 식 (5)의 active iteration 메커니즘).

변형(variant):
    upgdbf          난수를 에너지 가산항으로 통합 (논문 제안)
    pgdbf           난수를 에너지에서 빼고 플립 허가 조건으로 되돌린 PGDBF 상당판
                    (난수 소프트 제약화의 기여 분리용)
    no_flip_penalty 플리핑 penalty(직전 미플립 +1) 제거판 (momentum 기여 분리용)
    upgdbf_dvnorm   에너지에서 자기 차수(dv)를 뺀 진단판. 위반 수 대신
                    (위반 수 - 만족 수) 기준이 되어 차수가 다른 column끼리
                    전역 최대 비교가 공정해진다 (논문 부호는 dv 균일이라 두 기준이
                    같고, 평가 대상 파라미터는 dv 혼합이라 갈린다. 차수 불일치가
                    실패 원인인지 분리하는 용도)

종료: 프레임별로 syndrome 전부 0(코드워드 수렴) 또는 genie 성공(information
구간 에러 0, 본체와 같은 판정)이면 그 프레임을 멈춘다. syndrome 0인데 genie
실패면 miscorrection(다른 코드워드로 수렴)으로 실패 처리한다.

fallback_minsum=True면 BF 실패 프레임을 부모 min-sum decoder_main으로 read bit
그대로 재복호한다 (HBF의 BF 실패 후 min-sum 전환 대응). 스크리닝 기본은 False
(BF 단독 성능 측정).

자체 지표는 self.stats에 쌓인다 (포인트마다 configure()로 리셋):
    frame_iters      수행한 (프레임, iteration) 쌍의 수
    flips_sum        플립된 비트 수 합
    flip_miss_sum    그 iteration에서 플립되지 못한 에러 비트 수 합 (genie 기준,
                     논문 Fig 3의 flip miss 대응)
    overcorr_iters   플립 수 > 그 시점 에러 수 인 (프레임, iteration) 수 (과교정)
    flip_blocks_sum  플립이 발생한 column block(z lane 묶음) 수 합
                     (energy-based backtracking의 cycle 절감 대리 지표)
    miscorrections   syndrome 0인데 genie 실패로 끝난 프레임 수
    flips_by_dv      dv(변수 노드 차수)별 플립 수 합 (전역 최대 비교가 특정 dv에
                     쏠리는지 관찰)
    fail_err_by_dv   BF 실패 프레임의 잔여 에러를 dv별로 합산 (교정이 멈춘 곳 관찰)
"""
import numpy as np

from src.decoder import BaseDecoder

VARIANTS = ("upgdbf", "pgdbf", "no_flip_penalty", "upgdbf_dvnorm")


class UPGDBFDecoder(BaseDecoder):
    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix)
        if llr_matrix.mode != "HD":
            raise NotImplementedError("UP-GDBF 스크리닝은 HD 전용")
        self.configure()

    def configure(self, variant="upgdbf", t_active=2, bf_max_iter=40,
                  p_eta=0.9, fallback_minsum=False, eta_seed=12345):
        """변형과 파라미터 설정 + 지표 리셋. 반환은 self (체이닝용).
        eta_seed는 난수 penalty 전용 시드다 (채널 난수와 분리해 재현 보장)."""
        if variant not in VARIANTS:
            raise ValueError(f"variant={variant!r}: {VARIANTS} 중 하나여야 함")
        self.variant = variant
        self.t_active = int(t_active)
        self.bf_max_iter = int(bf_max_iter)
        self.p_eta = float(p_eta)
        self.fallback_minsum = bool(fallback_minsum)
        self._minsum_max_iter = self.llr_matrix.max_iter
        # sim.py가 실패 프레임을 max_iter로 집계하므로 BF 단독이면 BF 상한,
        # min-sum 재복호까지 하면 두 단계 합이 max_iter가 된다
        self.max_iter = self.bf_max_iter + (
            self._minsum_max_iter if self.fallback_minsum else 0)
        self._eta_rng = np.random.default_rng(eta_seed)
        self._dv_values = sorted(int(v) for v in np.unique(self.code.col_deg))
        self._dv_cols = {dv: np.flatnonzero(self.code.col_deg == dv)
                         for dv in self._dv_values}
        self.stats = {"frame_iters": 0, "flips_sum": 0, "flip_miss_sum": 0,
                      "overcorr_iters": 0, "flip_blocks_sum": 0,
                      "miscorrections": 0,
                      "flips_by_dv": {dv: 0 for dv in self._dv_values},
                      "fail_err_by_dv": {dv: 0 for dv in self._dv_values}}
        return self

    def point_stats(self):
        """포인트 집계용 자체 지표 (iteration당 평균 꼴 + dv별 합)."""
        frame_iters = max(self.stats["frame_iters"], 1)
        out = {
            "bf_frame_iters": self.stats["frame_iters"],
            "avg_flips_per_iter": self.stats["flips_sum"] / frame_iters,
            "avg_flip_miss_per_iter": self.stats["flip_miss_sum"] / frame_iters,
            "overcorr_rate": self.stats["overcorr_iters"] / frame_iters,
            "avg_flip_blocks_per_iter": self.stats["flip_blocks_sum"] / frame_iters,
            "miscorrections": self.stats["miscorrections"],
        }
        for dv in self._dv_values:
            out[f"flips_dv{dv}"] = self.stats["flips_by_dv"][dv]
            out[f"fail_err_dv{dv}"] = self.stats["fail_err_by_dv"][dv]
        return out

    def _connected_syndrome_sum(self, syndrome):
        """비트별 연결 syndrome 합 (B, N_b, z). CN 정렬 값을 VN 정렬로 roll(+shift)."""
        code = self.code
        out = np.zeros((syndrome.shape[0], code.N_b, code.z), np.int16)
        for e in range(code.E):
            out[:, code.edge_col[e], :] += np.roll(
                syndrome[:, code.edge_row[e], :], code.edge_shift[e], axis=-1)
        return out

    def decoder_main(self, channel_out, collect_profile=False, log=None):
        """BF 엔진 진입 함수. 반환 dict 형식은 부모와 같다 (log 항목은 미지원,
        자체 지표는 self.stats로 수집)."""
        if log:
            raise NotImplementedError(
                "UP-GDBF 스크리닝은 본체 log 항목 미지원 (자체 지표는 self.stats)")
        read_bit, _ = self._read_channel_input(channel_out)
        B = read_bit.shape[0]
        num_info_col_blocks = self.code.N_b - self.code.M_b

        x = read_bit.copy()                     # 현재 추정 (1 = 에러)
        y = read_bit                            # 채널 초기값 (이후 불변)
        y_active = read_bit
        not_flipped_last = np.ones_like(x)      # 논문의 li (1 = 직전 미플립)
        syndrome = self.code.syndrome(x)

        success = np.zeros(B, bool)
        decode_success_iteration = np.zeros(B, np.int32)
        final_err_bits = np.zeros(B, np.int64)
        final_info_err_bits = np.zeros(B, np.int64)
        idx_active = np.arange(B)

        for it in range(1, self.bf_max_iter + 1):
            num_active = x.shape[0]
            # ---- 최대 탐색 pass: 에너지와 전역 최대 ----
            energy = (x ^ y_active).astype(np.int16)
            energy += self._connected_syndrome_sum(syndrome)
            if self.variant == "upgdbf_dvnorm":
                # 위반 수에서 자기 차수를 빼 (위반 - 만족) 기준으로 바꾼다
                energy -= self.code.col_deg[None, :, None].astype(np.int16)
            if self.variant != "no_flip_penalty":
                energy += not_flipped_last
            if it <= self.t_active:
                eta = None                      # 결정적 (전 비트 +1과 등가, 최대 비교에 영향 없음)
            else:
                eta = self._eta_rng.random(x.shape) < self.p_eta
            if self.variant == "pgdbf":
                # 난수를 하드 제약으로: 후보(기본 에너지 == 최대) 중 허가된 비트만 플립
                emax = energy.max(axis=(1, 2))
                flip = energy == emax[:, None, None]
                if eta is not None:
                    flip &= eta
            else:
                if eta is not None:
                    energy += eta
                emax = energy.max(axis=(1, 2))
                flip = energy == emax[:, None, None]

            # ---- 자체 지표 (플립 확정 직후, 적용 전 상태 기준) ----
            err_before = x.sum(axis=(1, 2), dtype=np.int64)
            flips_per_frame = flip.sum(axis=(1, 2), dtype=np.int64)
            self.stats["frame_iters"] += num_active
            self.stats["flips_sum"] += int(flips_per_frame.sum())
            self.stats["flip_miss_sum"] += int(((x == 1) & ~flip).sum())
            self.stats["overcorr_iters"] += int((flips_per_frame > err_before).sum())
            self.stats["flip_blocks_sum"] += int(flip.any(axis=2).sum())
            for dv in self._dv_values:
                self.stats["flips_by_dv"][dv] += int(flip[:, self._dv_cols[dv], :].sum())

            # ---- 플리핑 pass ----
            flip_u8 = flip.astype(np.uint8)
            x ^= flip_u8
            not_flipped_last = 1 - flip_u8
            syndrome ^= self.code.syndrome(flip_u8)

            # ---- 종료 판정 (genie 성공 또는 syndrome 0) ----
            genie_ok = ~x[:, :num_info_col_blocks, :].any(axis=(1, 2))
            syndrome_zero = ~syndrome.any(axis=(1, 2))
            done = genie_ok | syndrome_zero
            if done.any():
                done_global = idx_active[done]
                success[done_global] = genie_ok[done]
                decode_success_iteration[done_global] = np.where(genie_ok[done], it, 0)
                final_err_bits[done_global] = x[done].sum(axis=(1, 2), dtype=np.int64)
                final_info_err_bits[done_global] = \
                    x[done][:, :num_info_col_blocks, :].sum(axis=(1, 2), dtype=np.int64)
                self.stats["miscorrections"] += int((syndrome_zero & ~genie_ok).sum())
            keep = ~done
            if not keep.any():
                x = x[:0]
                break
            if keep.sum() < num_active:
                x, y_active, syndrome = x[keep], y_active[keep], syndrome[keep]
                not_flipped_last = not_flipped_last[keep]
                idx_active = idx_active[keep]

        # ---- BF 실패 프레임 마감 (선택: min-sum 재복호) ----
        if x.shape[0]:
            final_err_bits[idx_active] = x.sum(axis=(1, 2), dtype=np.int64)
            final_info_err_bits[idx_active] = \
                x[:, :num_info_col_blocks, :].sum(axis=(1, 2), dtype=np.int64)
            for dv in self._dv_values:
                self.stats["fail_err_by_dv"][dv] += int(x[:, self._dv_cols[dv], :].sum())
            if self.fallback_minsum:
                parent = super().decoder_main(
                    {"mode": "HD", "hd": y_active.copy(), "sd": None, "cc": None})
                success[idx_active] = parent["success"]
                decode_success_iteration[idx_active] = np.where(
                    parent["success"],
                    self.bf_max_iter + parent["decode_success_iteration"], 0)
                final_err_bits[idx_active] = parent["final_err_bits"]
                final_info_err_bits[idx_active] = parent["final_info_err_bits"]

        out = {"success": success,
               "decode_success_iteration": decode_success_iteration,
               "final_err_bits": final_err_bits,
               "final_info_err_bits": final_info_err_bits}
        if collect_profile:
            out["profile"] = []
        return out
