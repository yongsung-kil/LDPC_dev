"""ulpbf_1pass: 초기 syndrome 1 pass 일괄 플립 + CRC 판정, 실패 시 min-sum 폴백
(ieee:11449331, 2025 NVMSA).

재정의: decoder_main 전체 (BF 계열은 교체용 함수 6개 경계에 맞지 않음,
새논문적용규칙.md 2절 세 번째 갈래). 엔진 재사용: _read_channel_input과
폴백 단의 부모 decoder_main (min-sum).

동작 (논문 Algorithm 2 대응, HD 전용):
  1단 (ULPBF 1 pass): 초기 syndrome을 1회 계산하고, column마다 불만족 검사 합
    energy[j]를 구해 dv별 문턱 T[dv] = max(dv - THRESHOLD_OFFSET, T_MIN) 이상이면
    일괄 플립한다 (pass 1회, pass 도중 syndrome 갱신 없음).
    판정 2종을 동시 기록한다:
      ㉮ 플립 후 syndrome 0 여부 (이상적 판정, 재계산 비용이 드는 쪽)
      ㉯ CRC-32 모델: information 구간 비트를 바이트로 묶어 zlib.crc32를 구하고
         all-zero 메시지의 CRC와 비교한다 (거짓 통과까지 실제로 모델링된다)
  2단 (폴백): CRC 불통과 프레임만 플립 상태를 버리고 HD 원본(read_bit)으로
    부모 BaseDecoder의 min-sum decoder_main을 호출한다.

성공 선언은 논문대로 CRC가 한다. CRC가 통과했는데 information 구간에 에러가
남은 프레임(거짓 통과)은 조용한 오류이므로 success=False로 집계한다.

decode_success_iteration: 1단 성공 프레임은 1, 폴백 프레임은 min-sum의
iteration 번호 그대로다 (1 pass 지연은 더하지 않아 sim.py iter_hist의
크기 max_iter+1 범위를 유지한다).

log 항목과 collect_profile은 지원하지 않는다 (2단 구성의 iteration별 로그
병합이 정의되지 않음). 자체 지표는 stats dict에 누적하고 reset_stats()로
초기화한다 (scan.py가 포인트마다 소비. 키 뜻은 _STAT_KEYS 주석).
"""
import zlib

import numpy as np

from src.decoder import BaseDecoder

# stats 키: 전부 프레임 수 또는 비트 수의 합 (평균은 소비하는 쪽이 계산)
_STAT_KEYS = (
    "frames",              # 처리한 프레임 수
    "stage1_syn_zero",     # 1단 플립 후 syndrome이 0인 프레임 수
    "stage1_genie_ok",     # 1단 플립 후 information 구간 에러 0인 프레임 수 (genie)
    "stage1_crc_pass",     # CRC-32 모델 통과 프레임 수 (파이프라인의 성공 선언 기준)
    "crc_false_pass",      # CRC 통과인데 information 구간에 에러가 남은 프레임 수
                           # (위험한 미검출, 기대 확률 2^-32 차원)
    "crc_pass_syn_nonzero",  # CRC 통과이면서 syndrome이 0이 아닌 프레임 수.
                           # 대부분 parity 구간 잔여 에러로 information은 깨끗한
                           # 수용이다 (syndrome 판정이라면 버렸을 프레임)
    "syn_zero_genie_fail",  # syndrome 0인데 genie 실패 (다른 codeword로 수렴)
    "fail_frames",         # 1단 실패(CRC 불통과) 프레임 수
    "fail_misflip_sum",    # 1단 실패 프레임의 오플립(정상 비트를 뒤집음) 비트 합
    "fail_missed_sum",     # 1단 실패 프레임의 누락(에러 비트를 안 뒤집음) 비트 합
    "fail_residual_sum",   # 1단 실패 프레임의 플립 후 잔여 에러 비트 합
    "fallback_frames",     # 2단(min-sum)으로 간 프레임 수 (= fail_frames)
    "fallback_fail",       # 2단까지 실패한 프레임 수
    "fallback_iter_sum",   # 2단 min-sum iteration 합 (실패 프레임은 max_iter로 집계.
                           # min-sum 단독의 iteration 합과 비교하면 syndrome 갱신
                           # 생략량의 대리 지표가 된다)
)


class ULPBF1PassDecoder(BaseDecoder):
    THRESHOLD_OFFSET = 0   # T[dv] = max(dv - THRESHOLD_OFFSET, T_MIN)
    T_MIN = 2              # 문턱 하한 (T=1이면 불만족 검사 하나로도 뒤집어 과플립)
    T_BY_DV = {}           # dv별 문턱 직접 지정 (offset 계산 결과를 덮어씀)

    def __init__(self, code, llr_matrix):
        super().__init__(code, llr_matrix)
        if llr_matrix.mode != "HD":
            raise NotImplementedError("ulpbf_1pass는 HD 전용")
        self._col_T = np.array(
            [self.T_BY_DV.get(
                len(code.col_edges[j]),
                max(len(code.col_edges[j]) - self.THRESHOLD_OFFSET, self.T_MIN))
             for j in range(code.N_b)], np.int32)
        self._num_info_col_blocks = code.N_b - code.M_b
        info_bit_count = self._num_info_col_blocks * code.z
        if info_bit_count % 8:
            raise ValueError(
                "information 비트 수가 8의 배수가 아니어서 CRC 바이트 모델 불가")
        self._crc_of_all_zero_info = zlib.crc32(bytes(info_bit_count // 8))
        self.reset_stats()

    def reset_stats(self):
        self.stats = {key: 0 for key in _STAT_KEYS}

    def _stage1_flip_mask(self, syndrome):
        """초기 syndrome 읽기 전용 1 pass: column마다 불만족 검사 합을 구해
        T[dv] 이상이면 플립 표시 (일괄 적용, 플립 간 전파 없음).
        syndrome: (B, M_b, z). 반환: (B, N_b, z) bool."""
        code = self.code
        B, _, z = syndrome.shape
        flip = np.zeros((B, code.N_b, z), bool)
        syndrome_int = syndrome.astype(np.int32)
        for col in range(code.N_b):
            energy = np.zeros((B, z), np.int32)
            for edge in code.col_edges[col]:
                row_blk, shift = code.edge_row[edge], code.edge_shift[edge]
                # CN 정렬 syndrome을 VN 정렬로 (+shift roll, _process_column과 동일)
                energy += np.roll(syndrome_int[:, row_blk, :], shift, axis=-1)
            flip[:, col, :] = energy >= self._col_T[col]
        return flip

    def _crc_model_pass(self, bits):
        """CRC-32 모델 판정: information 구간을 바이트로 묶어 zlib.crc32를 구하고
        all-zero 메시지의 CRC와 비교. bits: (B, N_b, z). 반환: (B,) bool."""
        B = bits.shape[0]
        info_bits = bits[:, :self._num_info_col_blocks, :].reshape(B, -1)
        packed = np.packbits(info_bits, axis=1)
        return np.array(
            [zlib.crc32(packed[k].tobytes()) == self._crc_of_all_zero_info
             for k in range(B)], bool)

    def decoder_main(self, channel_out, collect_profile=False, log=None):
        """2단 구성 진입점. 반환 dict 형식은 부모와 같다 (log, profile 항목 제외)."""
        log = set() if log is None else set(log)
        if log or collect_profile:
            raise NotImplementedError(
                "ulpbf_1pass는 log 항목과 collect_profile 미지원 "
                "(config의 log.enabled를 false로 둘 것)")
        read_bit, region = self._read_channel_input(channel_out)
        B = read_bit.shape[0]
        syndrome = self.code.syndrome(read_bit)

        # 1단: 초기 syndrome 기반 일괄 플립
        flip = self._stage1_flip_mask(syndrome)
        flipped = read_bit ^ flip.astype(np.uint8)
        residual_err_bits = flipped.sum(axis=(-2, -1), dtype=np.int64)
        info_err_bits = flipped[:, :self._num_info_col_blocks, :].sum(
            axis=(-2, -1), dtype=np.int64)
        syn_zero = ~self.code.syndrome(flipped).any(axis=(-2, -1))
        genie_ok = info_err_bits == 0
        crc_pass = self._crc_model_pass(flipped)

        st = self.stats
        st["frames"] += B
        st["stage1_syn_zero"] += int(syn_zero.sum())
        st["stage1_genie_ok"] += int(genie_ok.sum())
        st["stage1_crc_pass"] += int(crc_pass.sum())
        st["crc_false_pass"] += int((crc_pass & ~genie_ok).sum())
        st["crc_pass_syn_nonzero"] += int((crc_pass & ~syn_zero).sum())
        st["syn_zero_genie_fail"] += int((syn_zero & ~genie_ok).sum())

        failed = ~crc_pass
        if failed.any():
            # genie 분해: 오플립(정상 비트를 뒤집음), 누락(에러 비트를 안 뒤집음)
            misflip_bits = (flip & (read_bit == 0)).sum(axis=(-2, -1), dtype=np.int64)
            missed_bits = ((read_bit == 1) & ~flip).sum(axis=(-2, -1), dtype=np.int64)
            st["fail_frames"] += int(failed.sum())
            st["fail_misflip_sum"] += int(misflip_bits[failed].sum())
            st["fail_missed_sum"] += int(missed_bits[failed].sum())
            st["fail_residual_sum"] += int(residual_err_bits[failed].sum())

        success = crc_pass & genie_ok
        decode_success_iteration = np.where(success, 1, 0).astype(np.int32)
        final_err_bits = residual_err_bits.copy()
        final_info_err_bits = info_err_bits.copy()

        # 2단: CRC 불통과 프레임만 HD 원본으로 부모 min-sum
        if failed.any():
            fallback_idx = np.flatnonzero(failed)
            fallback_out = {"mode": "HD", "hd": read_bit[failed],
                            "sd": None, "cc": None}
            fallback = super().decoder_main(fallback_out)
            success[fallback_idx] = fallback["success"]
            decode_success_iteration[fallback_idx] = \
                fallback["decode_success_iteration"]
            final_err_bits[fallback_idx] = fallback["final_err_bits"]
            final_info_err_bits[fallback_idx] = fallback["final_info_err_bits"]
            fallback_fail_count = int((~fallback["success"]).sum())
            st["fallback_frames"] += len(fallback_idx)
            st["fallback_fail"] += fallback_fail_count
            st["fallback_iter_sum"] += (
                int(fallback["decode_success_iteration"].sum())
                + fallback_fail_count * self.max_iter)

        return {"success": success,
                "decode_success_iteration": decode_success_iteration,
                "final_err_bits": final_err_bits,
                "final_info_err_bits": final_info_err_bits}
