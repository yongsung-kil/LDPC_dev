"""배치 벡터화 quantized min-sum 디코더 — DAO LLR_MATRIX 기반 syndrome-aided (원본 C++ 대응).

2026-08-07 리팩토링:
- legacy 경로(two_set 스케줄, 비-matrix signed LLR 경로) 삭제 (사용자 확정) —
  LLR_MATRIX 모드만 유지. 구버전은 본체 git 이력(커밋 72b825a 계열)에서 복구 가능
- 변수명을 원본 C++ 용어와 정합: sum_t, VNU_in/VNU_out(vnu_in/vnu_out),
  check_sum, edge_sgn, syndrome, min1/min2/min1_pos, prev_CSW(prev_csw) 등 —
  코드만 보고 decoder.cpp의 대응 위치를 찾을 수 있게 함
- 진입 함수는 decoder_main() (사용자 확정 2026-08-07). 단계별 함수 추출로 분리:
    decoder_main()             ← 흐름만: 아래를 순서대로 호출
    ├── _read_channel_input()  ← 채널 출력 해석 → read_bit
    ├── _init_state()          ← syndrome 계산, CN 상태·결과 버퍼 초기화
    ├── _run_iteration()       ← 한 iteration: Edge Clear → 테이블 row 선택 → column 루프 → CSW
    │   └── _process_column()  ← 한 column: C2V 합산 → 판정 → VNU 갱신 (교체용 함수 호출)
    ├── _record_iteration()    ← 로그 집계 + 프레임별 최종 상태 갱신
    ├── _check_errors()        ← 에러 검사(genie) — 성공/실패 확정 + 배치 압축(마스킹)
    └── _build_result()        ← 반환 dict 조립

syndrome-aided flip/magnitude 도메인 (모든 메시지가 초기 read bit 기준 상대값):
- read_bit 고정, syndrome = H·read_bit 1회 계산 후 유지 (C++ iteration 0
  Pre-update 대응 — 원본은 iter 0에서 V2C sign에 read bit를 실어 check_sum에
  신드롬을 누적한 뒤 syndrome 레지스터로 복사. 여기서는 직접 계산으로 등가)
- VN: sum_t = ch(항상 +, iteration/dv별 테이블값) + Σ VNU_in.
  sum_t <= 0 → 현재 bit 반전 판정 (동점도 반전 — VN_Cal_HD 원문, 변경 금지)
- C2V(VNU_in): mag = min1/min2 (EDGE 도메인, RESET=edge_mag[0]),
  sign = syndrome ⊕ check_sum ⊕ edge_sgn (C2V_Cal "Syndrome aided decoding")
- Edge Clear(iteration 1, restart): CN 상태(min/pos/check_sum/edge_sgn) 클리어,
  syndrome은 유지 → VNU_in = ±RESET, sign = syndrome. iteration 1부터 신드롬
  기반 정정이 즉시 일어난다 (Clear_Edge_Restart + C2V_Cal_New_Sgn 대응)
- restart row의 -1 값도 그대로 산술 사용: ch=-1 ≈ 채널 무시, th=-1 → 전 메시지
  최대 레벨 → 순수 syndrome bit-flip iteration (C++ 동작 그대로)
- CSW = Σ(check_sum ⊕ syndrome) (Compute_CSW 대응), iteration 1 진입 시
  prev_csw = |syndrome| (iter 0 종료 시점의 Compute_CSW와 동일)
- 성공 판정: genie — bit 오류 = read_bit ⊕ (sum_t <= 0) 을 정답 all-zero와 비교,
  성공 프레임은 배치에서 제외 (마스킹 = 속도 이득, 결과 불변)
- 조기종료(CRC) 없음, HCU/펑처링/Dual-Update 없음, 파이프라인 store 지연 미재현

배열 축: (B, N_b, z) — 프레임 배치 B × column block × z lane.

논문 아이디어 교체 지점 (2026-08-07 사용자 확정 — 교체 단위 = 원본 C++ 함수 경계):
"교체 지점"이란 본체가 특정 단계를 일부러 별도 함수로 분리해 둬서, 아이디어 버전이
그 함수만 갈아끼울 수 있게 만든 자리다 (업계 용어로는 hook).
아이디어는 이 클래스를 상속한 자식 클래스에서 아래 교체용 함수만 재정의한다
(재정의 = 부모 클래스의 함수를 자식 클래스에서 다른 내용으로 바꿔 채우는 것.
Ideas/{논문}/decoder.py에 작성, Ideas/registry.py에 등록 → config decoder.type으로 선택).
교체 지점에 안 들어맞는 근본적 변경은 decoder_main 전체 재정의 허용.

| 교체용 함수 | C++ 대응 | 커버 논문 유형 |
|-------------|----------|---------------|
| _c2v_reconstruct | C2V_Cal | min-sum 변형 (offset/normalized/adjusted), C2V 보정 |
| _vnu_quantize | VN_Cal_HD 양자화부 | 양자화 규칙, 비균일 임계, damping |
| _vn_decide | VN_Cal_HD 판정부 | 판정 규칙, 진동 억제 |
| _cnu_update | CNU_Remove_Old_Sgn / CNU_Update_New_Mag | CN 상태 갱신 변형 |
| _column_order | 메인 루프 스케줄 | layered / informed dynamic scheduling |
| _is_edge_clear_iter | Clear_Edge_Restart (Is_Iter_Type_Edge_Clear) | restart, perturbation, post-processing |
| 테이블 row 선택 | Get_Cur_LLR_Idx_FILE | LLRMatrix.row_index() — LLRMatrix 자식 클래스로 커버 |
"""
import numpy as np

# decoder_main(log=...)가 받는 로그 항목 (수집 방법은 각 수집부 주석 참조)
LOG_ITEMS = {"csw", "bit_err", "bit_err_by_dv", "fail_detail"}


class _DecodeState:
    """decoder_main 한 호출의 작업 상태 묶음 — 단계별 함수 사이를 오가는 배열들.
    값은 _init_state()가 채우고, iteration 임시값은 _run_iteration()이 매 iteration 갱신."""
    # 설정과 치수
    log: frozenset
    need_by_dv: bool
    z: int
    num_dv: int
    # 프레임 데이터 (genie 마스킹 시 배치 압축 대상)
    read_bit: np.ndarray
    syndrome: np.ndarray
    prev_csw: np.ndarray
    min1: np.ndarray
    min2: np.ndarray
    min1_pos: np.ndarray
    check_sum: np.ndarray
    edge_sgn: np.ndarray
    idx_active: np.ndarray
    # 결과와 로그 버퍼 (원 배치 크기 B 고정)
    success: np.ndarray
    decode_success_iteration: np.ndarray
    profile: list
    final_err_bits: np.ndarray
    final_csw: np.ndarray
    final_err_by_dv: np.ndarray
    log_active: list
    log_csw_sum: list
    log_err_sum: list
    log_err_by_dv_sum: list
    # iteration 임시값 (_run_iteration이 매 iteration 새로 채움)
    n_active: int
    frame_err: np.ndarray
    err_bits: np.ndarray
    err_by_dv: np.ndarray
    edge_clear: bool
    cur_ch: np.ndarray
    cur_th: np.ndarray


class MinSumDecoder:
    def __init__(self, code, llr_matrix):
        """code: pcm.QCCode. llr_matrix: llr_matrix.LLRMatrix (필수) —
        max_iter는 파일의 마지막 iter_end가 결정. 현재 HD, 3-bit(th 3개) 전용."""
        if llr_matrix is None:
            raise ValueError("llr_matrix는 필수 — DAO LLR_MATRIX 파일을 로드해 넘길 것")
        if llr_matrix.mode != "HD":
            raise NotImplementedError(
                "llr_matrix 2SD/3SD는 채널 region 매핑 미구현 — 현재 HD만 지원")
        if llr_matrix.th_len != 3:
            raise NotImplementedError("th 3개(EDGE_MAG 4레벨) 구성만 지원")
        self.code = code
        self.llr_matrix = llr_matrix
        self.max_iter = llr_matrix.max_iter              # 마지막 iter_end = max_iter
        self._col_dv_idx = llr_matrix.col_dv_idx(code)   # (N_b,) column→dv 구간 인덱스
        self._edge_mag = np.array([7, 5, 3, 1], np.float32)  # 3-bit VNU 출력 레벨

    # ---------- 논문 아이디어 교체 지점 (모듈 docstring의 표 참조) ----------
    def _is_edge_clear_iter(self, iteration):
        """[교체 지점: Is_Iter_Type_Edge_Clear 대응] 이 iteration에서 Edge Clear를 할지.
        True면 (iteration 1 제외) CN 상태가 클리어된다 (syndrome은 유지 — 엔진 소관)."""
        return iteration == 1 or self.llr_matrix.is_restart(iteration)

    def _column_order(self, iteration):
        """[교체 지점: 메인 루프 스케줄 대응] 이 iteration의 column block 처리 순서."""
        return range(self.code.N_b)

    def _c2v_reconstruct(self, iteration, edge, min1_row, min2_row, min1_pos_row,
                         syndrome_row, check_sum_row, edge_sgn_row):
        """[교체 지점: C2V_Cal 대응] CN 상태로부터 C2V 메시지 재구성 (CN 정렬, roll 전).
        mag = min1 (자신이 min1 위치면 min2), sign = syndrome ⊕ check_sum ⊕ edge_sgn
        ("Syndrome aided decoding"). *_row: 해당 CN row block 슬라이스 (n_active, z)."""
        check_out = np.where(min1_pos_row == edge, min2_row, min1_row)
        c2v_sgn = (syndrome_row ^ check_sum_row ^ edge_sgn_row).astype(bool)
        return np.where(c2v_sgn, -check_out, check_out)

    def _vn_decide(self, sum_t):
        """[교체 지점: VN_Cal_HD 판정부 대응] sum_t → 현재 bit 반전 여부.
        동점(sum_t==0) 반전은 decoder.cpp:4044 원문 — vanilla에서는 변경 금지 (F14)."""
        return sum_t <= 0

    def _vnu_quantize(self, raw, vnu_in, th):
        """[교체 지점: VN_Cal_HD 양자화부 대응] VNU 출력 양자화.
        th: (n_active, 3) — 프레임별(현재 row의 dv별) 임계값.
        C++ 캐스케이드(decoder.cpp:4112-4115) 그대로: |raw| >= th1 → 최대 레벨,
        아니고 >= th2 → 다음 레벨, ... (비단조 th도 C++와 같은 의미로 소비 — 리뷰 F8).
        raw==0이면 sign은 VNU_in에서."""
        mag_in = np.abs(raw)
        edge_mag = self._edge_mag
        mag = np.where(mag_in >= th[:, 0, None], edge_mag[0],
              np.where(mag_in >= th[:, 1, None], edge_mag[1],
              np.where(mag_in >= th[:, 2, None], edge_mag[2], edge_mag[3])))
        sgn = np.where(raw > 0, np.float32(1.0), np.float32(-1.0))
        zero = raw == 0
        if zero.any():
            sgn_zero = np.where(vnu_in > 0, np.float32(1.0), np.float32(-1.0))
            sgn = np.where(zero, sgn_zero, sgn)
        return sgn * mag

    def _cnu_update(self, edge, edge_clear, new_sgn, new_mag, row_blk,
                    min1, min2, min1_pos, check_sum, edge_sgn):
        """[교체 지점: CNU_Remove_Old_Sgn / CNU_Update_New_Mag 대응] CN 상태 갱신 (in-place).
        remove old(Edge Clear iteration은 생략) 후 insert new — <= 비교,
        min1 교체 시 min2=RESET (기존 min1을 min2로 내리지 않는 HW 특성, 원문 그대로)."""
        RESET = np.float32(self._edge_mag[0])
        cur_min1 = min1[:, row_blk, :]
        cur_min2 = min2[:, row_blk, :]
        cur_pos = min1_pos[:, row_blk, :]
        if not edge_clear:   # remove old (Edge Clear iteration은 옛 기여 없음)
            check_sum[:, row_blk, :] ^= edge_sgn[:, edge, :]
            was_min1 = cur_pos == edge
            cur_min1 = np.where(was_min1, cur_min2, cur_min1)
            cur_min2 = np.where(was_min1, RESET, cur_min2)
        is_new_min1 = new_mag <= cur_min1
        is_new_min2 = new_mag <= cur_min2
        min2[:, row_blk, :] = np.where(
            is_new_min1, RESET, np.where(is_new_min2, new_mag, cur_min2))
        min1[:, row_blk, :] = np.where(is_new_min1, new_mag, cur_min1)
        min1_pos[:, row_blk, :] = np.where(is_new_min1, edge, cur_pos)
        check_sum[:, row_blk, :] ^= new_sgn
        edge_sgn[:, edge, :] = new_sgn

    # ---------- decoder_main 단계별 함수 ----------
    def _read_channel_input(self, channel_out):
        """채널 출력 해석 → read_bit (B, N_b, z) uint8."""
        if isinstance(channel_out, dict):
            if channel_out["mode"] != self.llr_matrix.mode:
                raise ValueError(
                    f"채널 출력 모드 {channel_out['mode']} != LLR matrix 모드 {self.llr_matrix.mode}")
            read_bit = np.asarray(channel_out["hd"], np.uint8)
        else:                                            # signed LLR 배열 (테스트 편의)
            read_bit = (channel_out < 0).astype(np.uint8)
        _, N_b, z = read_bit.shape
        assert N_b == self.code.N_b and z == self.code.z
        return read_bit

    def _init_state(self, read_bit, log):
        """syndrome 계산(C++ iteration 0 Pre-update 등가) + CN 상태·결과 버퍼 초기화."""
        code = self.code
        B, _, z = read_bit.shape
        M_b, num_edges = code.M_b, code.E
        num_dv = self.llr_matrix.num_dv
        RESET = np.float32(self._edge_mag[0])            # V_VERY_STRONG 대응

        s = _DecodeState()
        s.log = log
        s.need_by_dv = bool(log & {"bit_err_by_dv", "fail_detail"})
        s.z = z
        s.num_dv = num_dv
        s.read_bit = read_bit
        s.syndrome = code.syndrome(read_bit)             # (B, M_b, z) = H·read_bit
        s.prev_csw = s.syndrome.sum(axis=(-2, -1)).astype(np.int64)

        s.min1 = np.full((B, M_b, z), RESET, np.float32)
        s.min2 = np.full((B, M_b, z), RESET, np.float32)
        s.min1_pos = np.full((B, M_b, z), -1, np.int32)
        s.check_sum = np.zeros((B, M_b, z), np.uint8)
        s.edge_sgn = np.zeros((B, num_edges, z), np.uint8)

        s.success = np.zeros(B, bool)
        s.decode_success_iteration = np.zeros(B, np.int32)
        s.idx_active = np.arange(B)
        s.profile = []
        # 프레임별 최종 상태 (매 iteration 활성 프레임 위치에 덮어써서 "마지막 처리
        # iteration의 값"이 남는다. 성공 프레임은 그 iteration의 에러 0이 기록됨)
        s.final_err_bits = np.zeros(B, np.int64)
        s.final_csw = np.zeros(B, np.int64)
        s.final_err_by_dv = np.zeros((B, num_dv), np.int64)
        s.log_active, s.log_csw_sum = [], []
        s.log_err_sum, s.log_err_by_dv_sum = [], []
        return s

    def _run_iteration(self, s, iteration):
        """한 iteration: Edge Clear → 테이블 row 선택 → column 루프 → CSW 갱신."""
        RESET = np.float32(self._edge_mag[0])
        s.n_active = s.read_bit.shape[0]
        s.frame_err = np.zeros(s.n_active, bool)
        s.err_bits = np.zeros(s.n_active, np.int64)
        s.err_by_dv = np.zeros((s.n_active, s.num_dv), np.int64)

        s.edge_clear = self._is_edge_clear_iter(iteration)
        if s.edge_clear and iteration > 1:
            # restart: syndrome만 유지하고 CN 상태 클리어 (Clear_Edge_Restart)
            s.min1.fill(RESET)
            s.min2.fill(RESET)
            s.min1_pos.fill(-1)
            s.check_sum.fill(0)
            s.edge_sgn.fill(0)
        table_row_idx = self.llr_matrix.row_index(iteration, s.prev_csw)  # (n_active,)
        s.cur_ch = self.llr_matrix.row_ch[table_row_idx, :, 0]            # (n_active, num_dv)
        s.cur_th = self.llr_matrix.row_th[table_row_idx]                  # (n_active, num_dv, 3)

        for col in self._column_order(iteration):
            self._process_column(s, iteration, col)

        s.prev_csw = (s.check_sum ^ s.syndrome).sum(axis=(-2, -1)).astype(np.int64)  # Compute_CSW

    def _process_column(self, s, iteration, col):
        """한 column: C2V 합산(sum_t) → 판정(genie 집계) → VNU 출력·CN 갱신."""
        code = self.code
        edges = code.col_edges[col]
        edge_row, edge_shift = code.edge_row, code.edge_shift
        dv_idx = self._col_dv_idx[col]
        # flip 도메인: 채널 항은 항상 +ch (read bit는 syndrome과 genie에만 반영)
        sum_t = np.broadcast_to(
            s.cur_ch[:, dv_idx, None], (s.n_active, s.z)).astype(np.float32).copy()
        vnu_in_list = []
        for edge in edges:
            row_blk, shift = edge_row[edge], edge_shift[edge]
            c2v = self._c2v_reconstruct(
                iteration, edge, s.min1[:, row_blk, :], s.min2[:, row_blk, :],
                s.min1_pos[:, row_blk, :], s.syndrome[:, row_blk, :],
                s.check_sum[:, row_blk, :], s.edge_sgn[:, edge, :])
            vnu_in = np.roll(c2v, shift, axis=-1)   # CN 정렬 → VN 정렬
            vnu_in_list.append(vnu_in)
            sum_t += vnu_in

        flip = self._vn_decide(sum_t)
        bit_err = s.read_bit[:, col, :] ^ flip
        s.frame_err |= bit_err.any(axis=-1)
        s.err_bits += bit_err.sum(axis=-1)
        if s.need_by_dv:
            s.err_by_dv[:, dv_idx] += bit_err.sum(axis=-1)

        for edge, vnu_in in zip(edges, vnu_in_list):
            row_blk, shift = edge_row[edge], edge_shift[edge]
            vnu_out_raw = sum_t - vnu_in         # C++ sum_t − VNU_in (무포화)
            vnu_out = self._vnu_quantize(vnu_out_raw, vnu_in, s.cur_th[:, dv_idx, :])
            vnu_out = np.roll(vnu_out, -shift, axis=-1)   # VN 정렬 → CN 정렬
            new_sgn = (vnu_out < 0).astype(np.uint8)
            new_mag = np.abs(vnu_out)
            self._cnu_update(edge, s.edge_clear, new_sgn, new_mag, row_blk,
                             s.min1, s.min2, s.min1_pos, s.check_sum, s.edge_sgn)

    def _record_iteration(self, s, collect_profile):
        """로그 집계(iteration별 활성 프레임 합) + 프레임별 최종 상태 갱신 + profile."""
        if s.log:
            s.log_active.append(s.n_active)
            if "csw" in s.log:
                s.log_csw_sum.append(int(s.prev_csw.sum()))
            if "bit_err" in s.log:
                s.log_err_sum.append(int(s.err_bits.sum()))
            if "bit_err_by_dv" in s.log:
                s.log_err_by_dv_sum.append(s.err_by_dv.sum(axis=0))
        s.final_err_bits[s.idx_active] = s.err_bits
        if "fail_detail" in s.log:
            s.final_csw[s.idx_active] = s.prev_csw
            s.final_err_by_dv[s.idx_active] = s.err_by_dv
        if collect_profile:
            s.profile.append((s.n_active, float(s.err_bits.mean())))

    def _check_errors(self, s, iteration):
        """에러 검사 (genie: 정답 all-zero와 비교) — 성공/실패 확정 + 성공 프레임
        배치 압축. True 반환 시 루프 종료."""
        ok = ~s.frame_err
        if ok.any():
            s.success[s.idx_active[ok]] = True
            s.decode_success_iteration[s.idx_active[ok]] = iteration
        keep = s.frame_err
        if not keep.any() or iteration == self.max_iter:
            return True
        s.idx_active = s.idx_active[keep]
        s.read_bit, s.syndrome, s.prev_csw = \
            s.read_bit[keep], s.syndrome[keep], s.prev_csw[keep]
        s.min1, s.min2, s.min1_pos = s.min1[keep], s.min2[keep], s.min1_pos[keep]
        s.check_sum, s.edge_sgn = s.check_sum[keep], s.edge_sgn[keep]
        return False

    def _build_result(self, s, collect_profile):
        """반환 dict 조립 (형식은 decoder_main docstring 참조)."""
        out = {"success": s.success, "decode_success_iteration": s.decode_success_iteration,
               "final_err_bits": s.final_err_bits}
        if collect_profile:
            out["profile"] = s.profile
        if s.log:
            out["log_active"] = np.array(s.log_active, np.int64)
            if "csw" in s.log:
                out["log_csw_sum"] = np.array(s.log_csw_sum, np.int64)
            if "bit_err" in s.log:
                out["log_err_sum"] = np.array(s.log_err_sum, np.int64)
            if "bit_err_by_dv" in s.log:
                out["log_err_by_dv_sum"] = np.array(s.log_err_by_dv_sum, np.int64)
            if "fail_detail" in s.log:
                out["final_csw"] = s.final_csw
                out["final_err_by_dv"] = s.final_err_by_dv
        return out

    # ---------- 진입 함수 ----------
    def decoder_main(self, channel_out, collect_profile=False, log=None):
        """디코딩 진입 함수 (구 이름 decode_batch — 사용자 확정으로 개명 2026-08-07).

        channel_out: channel.py 출력 dict {"mode", "hd", ...}
        (테스트 편의로 signed LLR 배열도 허용 — 음수 = read bit 1).
        log: LOG_ITEMS 부분집합 — 켠 항목만 수집 (속도 비용 발생).

        반환 dict:
          success:  (B,) bool — max_iter 내 genie 판정 성공
          decode_success_iteration: (B,) int — 성공한 iteration 번호 (1-base). 실패 프레임은 0
          final_err_bits: (B,) int — 각 프레임의 마지막 처리 iteration 잔여 에러 bit 수
            (성공 프레임 0. post-FEC BER 집계용, 항상 반환)
          profile:  iteration별 (활성 프레임 수, 평균 잔여 에러비트) (collect_profile 시)
          log_active/log_csw_sum/log_err_sum/log_err_by_dv_sum: iteration별 집계
            (log 항목별. 프레임 평균은 sum/active로 소비측에서 계산)
          final_csw, final_err_by_dv: (B,), (B, num_dv) — fail_detail 시
        """
        log = frozenset() if log is None else frozenset(log)
        unknown = log - LOG_ITEMS
        if unknown:
            raise ValueError(f"log 항목 {sorted(unknown)} 미지원 — 허용: {sorted(LOG_ITEMS)}")

        read_bit = self._read_channel_input(channel_out)
        s = self._init_state(read_bit, log)
        for iteration in range(1, self.max_iter + 1):
            self._run_iteration(s, iteration)
            self._record_iteration(s, collect_profile)
            if self._check_errors(s, iteration):
                break
        return self._build_result(s, collect_profile)
