"""배치 벡터화 quantized min-sum 디코더 (vanilla).

구조 (plan.md §3.2, 리뷰 반영):
- CN 상태 old/new 2세트: C2V는 직전 iteration에서 확정된 old 상태(min1/min2/min1_pos/sign)로
  재구성하고, 이번 iteration의 V2C는 new 상태에 누적한다 — C++의 old/new 분리 구조 대응.
  (파이프라인 지연 의존성은 미재현 — 실물 C++ 정합이 필요해지면 추가)
- edge별 V2C sign 저장 (C++ Check_SRAM_sgn 대응) → C2V sign = sign누적 ⊕ 해당 edge sign
- LLR 도메인: 수학적 등가인 signed 표현 (원본 C++는 flip/magnitude 도메인)
- 성공 판정: genie — 매 iteration hard decision을 정답(all-zero)과 bitwise 비교,
  일치한 프레임은 그 시점 성공 확정 후 배치에서 제외 (마스킹 = 속도 이득, 결과 불변)
- 조기종료(CRC) 없음, HCU/펑처링/Dual-Update 없음

배열 축: (B, N_b, z) — 프레임 배치 B × column block × z lane.

논문 아이디어 훅: cn_mag_fn(C2V magnitude 변형), 서브클래스로 스케줄/업데이트 교체.
"""
import numpy as np

_INF = np.float32(3.0e38)


class MinSumDecoder:
    def __init__(self, code, max_iter=20, beta=1.0, alpha=None, msg_clip=31.0,
                 quantize=True, schedule="two_set", llr_profile=None):
        """beta: offset min-sum offset (정수 도메인 친화, 기본).
        alpha: normalized min-sum 계수 (지정 시 beta 무시, float 도메인).
        msg_clip: V2C/총합 클리핑 한계 (HW 5bit+sign ≈ 31 대응).
        llr_profile: llr_tables.LLRProfile — 지정 시 HW-근사 internal precision 모드:
          V2C를 threshold 비교로 EDGE_MAG 4레벨(3-bit) 양자화 (decoder.cpp:4080-4120 대응),
          beta는 프로파일 값(기본 0)으로 대체. 채널 LLR은 channel.py에
          llr_tables.ch_mag_by_col(code, profile)를 넘겨 dv별 값 적용.
        """
        if schedule not in ("two_set", "column_wise"):
            raise NotImplementedError(
                "schedule은 two_set(flooding 등가) 또는 column_wise(원본 대응)")
        self.schedule = schedule
        self.code = code
        self.max_iter = int(max_iter)
        self.beta = np.float32(beta)
        self.alpha = None if alpha is None else np.float32(alpha)
        self.msg_clip = np.float32(msg_clip)
        self.quantize = bool(quantize)
        self.profile = llr_profile
        if llr_profile is not None:
            from .llr_tables import dv_group
            groups = np.array([dv_group(int(d)) for d in code.col_deg])
            self._col_th = llr_profile.th[groups]        # (N_b, 3) th1>th2>th3
            self._col_bf = code.col_deg > 5              # 1-bit precision 대상 (dv>5)
            self._edge_mag = llr_profile.edge_mag        # (4,) 내림차순 {7,5,3,1}
            self.beta = np.float32(llr_profile.beta)

    def _vnu_quantize(self, raw, c2v, j, it):
        """C++ VNU 출력 양자화 재현: |sum_t−VNU_in|을 th1~th3와 비교해 EDGE_MAG
        4레벨 magnitude로, 0이면 sign은 VNU_in(=c2v)에서. BF 구간(iter<=BF_ITERS,
        dv>5)은 magnitude를 최대 레벨로 고정하는 1-bit precision."""
        m = np.abs(raw)
        if self.profile.bf_iters and it <= self.profile.bf_iters and self._col_bf[j]:
            mag = np.full_like(m, self._edge_mag[0])
        else:
            th = self._col_th[j]
            lvl = ((m < th[0]).astype(np.int8) + (m < th[1]) + (m < th[2]))
            mag = self._edge_mag[lvl]
        sgn = np.where(raw > 0, np.float32(1.0), np.float32(-1.0))
        zero = raw == 0
        if zero.any():
            sgn_z = np.where(c2v > 0, np.float32(1.0), np.float32(-1.0))
            sgn = np.where(zero, sgn_z, sgn)
        return sgn * mag

    # 논문 아이디어 훅: C2V magnitude 후처리 (offset/normalization 교체 지점)
    def cn_mag_fn(self, mag, it):
        if self.alpha is not None:
            return mag * self.alpha
        return np.maximum(mag - self.beta, np.float32(0.0))

    def decode_batch(self, ch_llr, collect_profile=False):
        """ch_llr: (B, N_b, z) float32, all-zero 송신 가정.

        반환 dict:
          success:  (B,) bool — max_iter 내 genie 판정 성공
          n_iter:   (B,) int  — 성공 iteration (1-base). 실패 프레임은 0
          profile:  iteration별 (활성 프레임 수, 평균 잔여 에러비트) (collect_profile=True 시)
        """
        if self.schedule == "column_wise":
            return self._decode_column_wise(ch_llr, collect_profile)
        code = self.code
        B, N_b, z = ch_llr.shape
        assert N_b == code.N_b and z == code.z
        Mb, E = code.M_b, code.E
        er, es = code.edge_row, code.edge_shift

        ch = ch_llr.astype(np.float32, copy=True)
        # old 상태 = 빈 상태 (min=0 → C2V=0)
        old_min1 = np.zeros((B, Mb, z), np.float32)
        old_min2 = np.zeros((B, Mb, z), np.float32)
        old_pos = np.full((B, Mb, z), -1, np.int32)
        old_sgnp = np.zeros((B, Mb, z), np.uint8)
        old_esgn = np.zeros((B, E, z), np.uint8)

        success = np.zeros(B, bool)
        n_iter = np.zeros(B, np.int32)
        idx_active = np.arange(B)
        profile = []

        for it in range(1, self.max_iter + 1):
            Ba = ch.shape[0]
            new_min1 = np.full((Ba, Mb, z), _INF, np.float32)
            new_min2 = np.full((Ba, Mb, z), _INF, np.float32)
            new_pos = np.full((Ba, Mb, z), -1, np.int32)
            new_sgnp = np.zeros((Ba, Mb, z), np.uint8)
            new_esgn = np.zeros((Ba, E, z), np.uint8)
            frame_err = np.zeros(Ba, bool)
            err_bits = np.zeros(Ba, np.int64) if collect_profile else None

            for j in range(code.N_b):
                edges = code.col_edges[j]
                total = ch[:, j, :].copy()
                c2v_vn = []
                for e in edges:
                    i, s = er[e], es[e]
                    mag = np.where(old_pos[:, i, :] == e, old_min2[:, i, :], old_min1[:, i, :])
                    mag = self.cn_mag_fn(mag, it)
                    sgn = (old_sgnp[:, i, :] ^ old_esgn[:, e, :]).astype(bool)
                    c2v = np.roll(np.where(sgn, -mag, mag), s, axis=-1)
                    c2v_vn.append(c2v)
                    total += c2v

                # genie 판정용 hard decision (all-zero: total<0 = 비트 에러)
                frame_err |= (total < 0).any(axis=-1)
                if collect_profile:
                    err_bits += (total < 0).sum(axis=-1)

                for e, c2v in zip(edges, c2v_vn):
                    i, s = er[e], es[e]
                    raw = total - c2v            # HW sum_t − VNU_in (내부 합은 무포화)
                    if self.profile is not None:
                        v2c = self._vnu_quantize(raw, c2v, j, it)
                    else:
                        v2c = np.clip(raw, -self.msg_clip, self.msg_clip)
                        if self.quantize:
                            v2c = np.rint(v2c)
                    v2c = np.roll(v2c, -s, axis=-1)
                    sgn = v2c < 0
                    mag = np.abs(v2c)
                    new_sgnp[:, i, :] ^= sgn
                    new_esgn[:, e, :] = sgn
                    m1 = new_min1[:, i, :]
                    better = mag < m1
                    new_min2[:, i, :] = np.where(better, m1, np.minimum(new_min2[:, i, :], mag))
                    new_min1[:, i, :] = np.where(better, mag, m1)
                    new_pos[:, i, :] = np.where(better, e, new_pos[:, i, :])

            if collect_profile:
                profile.append((Ba, float(err_bits.mean())))
            ok = ~frame_err
            if ok.any():
                success[idx_active[ok]] = True
                n_iter[idx_active[ok]] = it
            keep = frame_err
            if not keep.any() or it == self.max_iter:
                break
            # 성공 프레임 제거 (배치 압축) + old/new 스왑
            idx_active = idx_active[keep]
            ch = ch[keep]
            old_min1 = np.minimum(new_min1[keep], self.msg_clip)   # deg-1 row 방어
            old_min2 = np.minimum(new_min2[keep], self.msg_clip)
            old_pos = new_pos[keep]
            old_sgnp = new_sgnp[keep]
            old_esgn = new_esgn[keep]

        out = {"success": success, "n_iter": n_iter}
        if collect_profile:
            out["profile"] = profile
        return out

    def _decode_column_wise(self, ch_llr, collect_profile=False):
        """원본 C++ 대응 column-wise 스케줄: 단일 CN 상태(min1/min2/min1_pos/check_sum +
        edge sign)를 column 진행 중 즉시 remove-old → insert-new 갱신.
        - 제거: check_sum ⊕= old_sign; min1_pos==e 이면 min1←min2, min2←RESET
          (CNU_Remove_Old_Sgn / CNU_Update_New_Mag 앞부분, decoder.cpp:3476-3526)
        - 삽입: v2c<=min1 이면 min1=v2c, pos=e, **min2=RESET** (C++ 원문 그대로 —
          기존 min1을 min2로 내리지 않는 HW 근사), 아니고 v2c<=min2 이면 min2=v2c
        - RESET = 최대 magnitude 레벨 (V_VERY_STRONG=코드 도메인 최대 = 값 도메인
          edge_mag[0]; 비프로파일 모드는 msg_clip)
        - iteration 1은 Edge_Clear: C2V=0, 제거 생략, 삽입만 (상태 축적)
        파이프라인 store 지연(2~3 col)은 미재현 — 즉시 반영."""
        code = self.code
        B, N_b, z = ch_llr.shape
        assert N_b == code.N_b and z == code.z
        Mb, E = code.M_b, code.E
        er, es = code.edge_row, code.edge_shift
        RESET = np.float32(self._edge_mag[0] if self.profile is not None else self.msg_clip)

        ch = ch_llr.astype(np.float32, copy=True)
        min1 = np.full((B, Mb, z), RESET, np.float32)
        min2 = np.full((B, Mb, z), RESET, np.float32)
        pos = np.full((B, Mb, z), -1, np.int32)
        csum = np.zeros((B, Mb, z), np.uint8)
        esgn = np.zeros((B, E, z), np.uint8)

        success = np.zeros(B, bool)
        n_iter = np.zeros(B, np.int32)
        idx_active = np.arange(B)
        profile = []

        for it in range(1, self.max_iter + 1):
            Ba = ch.shape[0]
            frame_err = np.zeros(Ba, bool)
            err_bits = np.zeros(Ba, np.int64) if collect_profile else None

            for j in range(code.N_b):
                edges = code.col_edges[j]
                total = ch[:, j, :].copy()
                c2v_vn = []
                for e in edges:
                    i, s = er[e], es[e]
                    if it == 1:
                        c2v = np.zeros((Ba, z), np.float32)
                    else:
                        mag = np.where(pos[:, i, :] == e, min2[:, i, :], min1[:, i, :])
                        mag = self.cn_mag_fn(mag, it)
                        sgn = (csum[:, i, :] ^ esgn[:, e, :]).astype(bool)
                        c2v = np.roll(np.where(sgn, -mag, mag), s, axis=-1)
                    c2v_vn.append(c2v)
                    total += c2v

                frame_err |= (total < 0).any(axis=-1)
                if collect_profile:
                    err_bits += (total < 0).sum(axis=-1)

                for e, c2v in zip(edges, c2v_vn):
                    i, s = er[e], es[e]
                    raw = total - c2v
                    if self.profile is not None:
                        v2c = self._vnu_quantize(raw, c2v, j, it)
                    else:
                        v2c = np.clip(raw, -self.msg_clip, self.msg_clip)
                        if self.quantize:
                            v2c = np.rint(v2c)
                    v2c = np.roll(v2c, -s, axis=-1)
                    sgn_new = (v2c < 0).astype(np.uint8)
                    mag_new = np.abs(v2c)

                    m1, m2, p = min1[:, i, :], min2[:, i, :], pos[:, i, :]
                    if it >= 2:   # remove old (iter 1 = Edge_Clear, 옛 기여 없음)
                        csum[:, i, :] ^= esgn[:, e, :]
                        was1 = p == e
                        m1 = np.where(was1, m2, m1)
                        m2 = np.where(was1, RESET, m2)
                    # insert new (C++ CNU_Update_New_Mag 원문, <= 비교)
                    le1 = mag_new <= m1
                    le2 = mag_new <= m2
                    min2[:, i, :] = np.where(le1, RESET, np.where(le2, mag_new, m2))
                    min1[:, i, :] = np.where(le1, mag_new, m1)
                    pos[:, i, :] = np.where(le1, e, p)
                    csum[:, i, :] ^= sgn_new
                    esgn[:, e, :] = sgn_new

            if collect_profile:
                profile.append((Ba, float(err_bits.mean())))
            ok = ~frame_err
            if ok.any():
                success[idx_active[ok]] = True
                n_iter[idx_active[ok]] = it
            keep = frame_err
            if not keep.any() or it == self.max_iter:
                break
            idx_active = idx_active[keep]
            ch = ch[keep]
            min1, min2, pos = min1[keep], min2[keep], pos[keep]
            csum, esgn = csum[keep], esgn[keep]

        out = {"success": success, "n_iter": n_iter}
        if collect_profile:
            out["profile"] = profile
        return out
