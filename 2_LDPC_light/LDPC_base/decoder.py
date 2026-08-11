"""배치 벡터화 quantized min-sum 디코더: DAO LLR_MATRIX 기반 syndrome-aided (원본 C++ 대응).

변수명은 원본 C++ 용어를 따른다 (sum_t, vnu_in/vnu_out ↔ VNU_in/VNU_out,
check_sum, edge_sgn, syndrome, min1/min2/min1_pos, prev_csw ↔ prev_CSW 등).
코드만 보고 decoder.cpp의 대응 위치를 찾을 수 있다.

진입 함수는 decoder_main(). 단계별 구성:
    decoder_main()             ← 흐름만: 아래를 순서대로 호출
    ├── _read_channel_input()  ← 채널 출력 해석 → read_bit
    ├── _init_state()          ← syndrome 계산, CN 상태와 결과 버퍼 초기화
    ├── _run_iteration()       ← 한 iteration: Edge Clear → 테이블 row 선택 → column 루프 → CSW
    │   └── _process_column()  ← 한 column: C2V 합산 → 판정 → VNU 갱신 (교체용 함수 호출)
    ├── _record_iteration()    ← 로그 집계 + 프레임별 최종 상태 갱신
    ├── _check_errors()        ← 에러 검사(genie): 성공/실패 확정 + 배치 압축(마스킹)
    └── _build_result()        ← 반환 dict 조립

syndrome-aided flip/magnitude 도메인 (모든 메시지가 초기 read bit 기준 상대값):
- read_bit 고정, syndrome = H·read_bit 1회 계산 후 유지 (C++ iteration 0
  Pre-update와 등가다. 원본은 iter 0에서 V2C sign에 read bit를 실어 check_sum에
  신드롬을 누적한 뒤 syndrome 레지스터로 복사한다)
- VN: sum_t = ch(항상 +, iteration/dv별 테이블값) + Σ VNU_in.
  sum_t <= 0이면 현재 bit를 반전한다 (동점 포함, VN_Cal_HD 원문과 동일)
- C2V(VNU_in): mag = min1/min2 (EDGE 도메인, RESET=edge_mag[0]),
  sign = syndrome ⊕ check_sum ⊕ edge_sgn (C2V_Cal "Syndrome aided decoding")
- Edge Clear(iteration 1, restart): CN 상태(min/pos/check_sum/edge_sgn)를 클리어하고
  syndrome은 유지한다 → VNU_in = ±RESET, sign = syndrome. iteration 1부터 신드롬
  기반 정정이 즉시 일어난다 (Clear_Edge_Restart + C2V_Cal_New_Sgn 대응)
- restart row의 -1 값도 그대로 산술에 쓴다: ch=-1 ≈ 채널 무시, th=-1 → 전 메시지
  최대 레벨 → 순수 syndrome bit-flip iteration (C++ 동작 그대로)
- CSW = Σ(check_sum ⊕ syndrome) (Compute_CSW 대응), iteration 1 진입 시
  prev_csw = |syndrome| (iter 0 종료 시점의 Compute_CSW와 동일)
- 성공 판정: genie 방식. bit 오류 = read_bit ⊕ (sum_t <= 0)를 정답 all-zero와
  information 구간(앞쪽 N_b - M_b개 column block)만 비교하고 (C++ Check_Genie_CRC의
  q < N - M 범위 대응), 성공 프레임은 배치에서 제외한다 (마스킹 = 속도 이득, 결과 불변)
- 조기종료(CRC), HCU, 펑처링, Dual-Update, 파이프라인 store 지연은 범위 밖
  (original과의 차이 전체는 docs/차이.md 참조)

배열 축: (B, N_b, z). 프레임 배치 B × column block × z lane.

논문 아이디어 교체 지점 (교체 단위 = 원본 C++ 함수 경계):
"교체 지점"이란 본체가 특정 단계를 별도 함수로 분리해 둬서, 아이디어 버전이
그 함수만 갈아끼울 수 있게 만든 자리다. 교체용 함수 6개(_c2v_reconstruct,
_vnu_quantize, _vn_decide, _cnu_update, _column_order, _is_edge_clear_iter)는
각 함수 docstring의 [교체 지점] 표지에 C++ 대응 함수가 적혀 있다.
새 논문을 붙이는 절차, 교체용 함수 표, 상속 경계 규칙의 정본은
docs/새논문적용규칙.md다.
"""
import numpy as np

# decoder_main(log=...)가 받는 로그 항목 (수집 방법은 각 수집부 주석 참조)
LOG_ITEMS = {"csw", "bit_err", "bit_err_by_dv", "fail_detail"}


class _DecodeState:
    """decoder_main 한 호출의 작업 상태 묶음 (단계별 함수 사이를 오가는 배열들).
    값은 _init_state()가 채우고, iteration 임시값은 _run_iteration()이 매 iteration 갱신."""
    # 설정과 치수
    log: set
    need_by_dv: bool
    z: int
    num_dv: int
    # 프레임 데이터 (genie 마스킹 시 배치 압축 대상)
    read_bit: np.ndarray
    region: np.ndarray                # 2SD/3SD 비트별 ch 열 인덱스 (HD는 None)
    seed_mag: np.ndarray              # 2SD/3SD Pre 단계 채널 magnitude (HD는 None)
    decision_bits: np.ndarray
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
    final_info_err_bits: np.ndarray
    final_csw: np.ndarray
    final_err_by_dv: np.ndarray
    log_active: list
    log_csw_sum: list
    log_err_sum: list
    log_err_by_dv_sum: list
    # iteration 임시값 (_run_iteration이 매 iteration 새로 채움)
    num_active_frames: int
    frame_err: np.ndarray
    err_bits: np.ndarray
    info_err_bits: np.ndarray
    err_by_dv: np.ndarray
    edge_clear: bool
    cur_ch: np.ndarray
    cur_ch_all: np.ndarray            # (활성 프레임, num_dv, ch_len). 2SD/3SD의 region 색인용
    cur_th: np.ndarray


class BaseDecoder:
    def __init__(self, code, llr_matrix):
        """code: pcm.QCCode. llr_matrix: llr_matrix.LLRMatrix (필수).
        DAO 파일 로드 또는 LLRMatrix.make_internal_uniform_matrix()로 합성해 공급.
        max_iter와 VNU 출력 레벨(edge_mag)은 llr_matrix가 결정한다.
        디코딩 모드(HD/2SD/3SD)는 llr_matrix.mode를 따른다."""
        if llr_matrix is None:
            raise ValueError(
                "llr_matrix는 필수: DAO 파일 로드 또는 내부 합성(make_internal_uniform_matrix)")
        if llr_matrix.mode not in ("HD", "2SD", "3SD"):
            raise NotImplementedError("llr_matrix는 HD/2SD/3SD만 지원")
        self.code = code
        self.llr_matrix = llr_matrix
        self.max_iter = llr_matrix.max_iter              # 마지막 iter_end = max_iter
        self._col_dv_idx = llr_matrix.col_dv_idx(code)   # (N_b,) column→dv 구간 인덱스
        self._cols_by_dv = [np.flatnonzero(self._col_dv_idx == d)
                            for d in range(llr_matrix.num_dv)]  # dv 구간별 column 목록
        self._edge_mag = np.array(llr_matrix.edge_mag, np.float32)  # VNU 출력 레벨 사본 (내림차순)
        self._uniform_levels = llr_matrix.has_uniform_levels  # 균일 등가식 사용 여부 (값 기반)
        self._seed_levels = self._channel_seed_levels()  # SD Pre 단계 채널 magnitude (HD는 None)

    def _channel_seed_levels(self):
        """SD Pre 단계(iteration 0과 restart)가 CN에 심는 채널 magnitude (region 순).
        3-bit DAO 파일 대응은 C++ Make_LLR의 고정 상수다 (2SD [5, 1]: decoder.cpp:4905,
        3SD [7, 5, 3, 1]: decoder.cpp:4924. LLR matrix 파일에서 읽지 않는다).
        균일 n-bit 레벨은 C++ 대응이 없어 1..top을 region 수로 균등 분할한다
        (3-bit 3SD에서 C++ 값 [7, 5, 3, 1]과 일치)."""
        if self.llr_matrix.mode == "HD":
            return None
        num_regions = self.llr_matrix.ch_len
        if self._uniform_levels:
            top = float(self._edge_mag[0])
            return np.array(
                [round(1.0 + (top - 1.0) * (num_regions - 1 - k) / (num_regions - 1))
                 for k in range(num_regions)], np.float32)
        return np.array({2: [5.0, 1.0], 4: [7.0, 5.0, 3.0, 1.0]}[num_regions], np.float32)

    # ---------- 논문 아이디어 교체 지점 (모듈 docstring의 표 참조) ----------
    def _is_edge_clear_iter(self, iteration):
        """[교체 지점: Is_Iter_Type_Edge_Clear 대응] 이 iteration에서 Edge Clear를 할지.
        전 모드에서 restart iteration만 클리어한다 (사용자 결정 2026-08-09.
        원본 HD의 iteration 1 클리어는 Ref-C와 RTL의 iteration 0 저장 차이를 없애려는
        보정(decoder.cpp:6570 주석)이고, py는 그 차이가 없어 재현하지 않는다.
        iteration 1의 CN 상태는 초기값 그대로라 산술 결과도 같다).
        True면 CN 상태가 클리어된다 (syndrome은 유지, 엔진 소관)."""
        return self.llr_matrix.is_restart(iteration)

    def _column_order(self, iteration):
        """[교체 지점: 메인 루프 스케줄 대응] 이 iteration의 column block 처리 순서."""
        return range(self.code.N_b)

    def _c2v_reconstruct(self, iteration, edge, min1_row, min2_row, min1_pos_row,
                         syndrome_row, check_sum_row, edge_sgn_row):
        """[교체 지점: C2V_Cal 대응] CN 상태로부터 C2V 메시지 재구성 (CN 정렬, roll 전).
        mag = min1 (자신이 min1 위치면 min2), sign = syndrome ⊕ check_sum ⊕ edge_sgn
        ("Syndrome aided decoding"). *_row: 해당 CN row block 슬라이스 (num_active_frames, z)."""
        check_out = np.where(min1_pos_row == edge, min2_row, min1_row)
        c2v_sgn = (syndrome_row ^ check_sum_row ^ edge_sgn_row).astype(bool)
        return np.where(c2v_sgn, -check_out, check_out)

    def _vn_decide(self, sum_t):
        """[교체 지점: VN_Cal_HD 판정부 대응] sum_t → 현재 bit 반전 여부.
        동점(sum_t==0)도 반전한다 (decoder.cpp:4044 VN_Cal_HD 원문과 동일하게 유지)."""
        return sum_t <= 0

    def _vnu_quantize(self, raw, vnu_in, th):
        """[교체 지점: VN_Cal_HD 양자화부 대응] VNU 출력 양자화.
        th: (num_active_frames, th 개수). 프레임별(현재 row의 dv별) 임계값 (내림차순 관례).
        C++ 캐스케이드(decoder.cpp:4112-4115) 그대로: |raw| >= th1 → 최대 레벨,
        아니고 >= th2 → 다음 레벨, ..., 전부 아니면 마지막 레벨
        (비단조 th도 C++와 같은 의미로 소비, 위쪽 th의 참 조건이 우선).
        레벨 값과 개수는 llr_matrix.edge_mag가 결정한다 (파일 3-bit {7,5,3,1},
        내부 균일 n-bit는 최소 레벨 1). raw==0이면 sign은 VNU_in에서.
        균일 레벨(has_uniform_levels)이면 등가식 _uniform_saturate로 계산한다."""
        mag_in = np.abs(raw)
        edge_mag = self._edge_mag
        if self._uniform_levels:
            mag = self._uniform_saturate(mag_in)
        else:
            # 아래 레벨부터 덮어써서 가장 위(작은 k)의 참 조건이 최종값 (elif 체인과 동일)
            mag = np.full_like(mag_in, edge_mag[-1])
            for k in range(len(edge_mag) - 2, -1, -1):
                mag = np.where(mag_in >= th[:, k, None], edge_mag[k], mag)
        sgn = np.where(raw > 0, np.float32(1.0), np.float32(-1.0))
        zero = raw == 0
        if zero.any():
            sgn_zero = np.where(vnu_in > 0, np.float32(1.0), np.float32(-1.0))
            sgn = np.where(zero, sgn_zero, sgn)
        return sgn * mag

    def _uniform_saturate(self, mag_in):
        """균일 레벨용 양자화 등가식: max(min(|raw|, 최대 레벨), 1).
        정수 raw에서 캐스케이드(th [top..1], edge_mag [top..2,1,1])와 완전히 같고,
        th 개수만큼 돌던 루프가 상수 시간이 된다. 비정수 raw에서는 캐스케이드가
        내림 동작이라 등가가 아니다 (교체 지점 재정의로 비정수 raw가 생기면
        이 함수를 함께 재정의하거나 캐스케이드 경로를 쓸 것)."""
        return np.maximum(np.minimum(mag_in, self._edge_mag[0]), np.float32(1.0))

    def _cnu_update(self, edge, edge_clear, new_sgn, new_mag, row_blk,
                    min1, min2, min1_pos, check_sum, edge_sgn):
        """[교체 지점: CNU_Remove_Old_Sgn / CNU_Update_New_Mag 대응] CN 상태 갱신
        (받은 배열을 제자리에서 직접 고침). remove old(Edge Clear iteration은 생략) 후
        insert new: <= 비교, min1 교체 시 min2=RESET (기존 min1을 min2로 내리지 않는
        HW 특성, 원문 그대로). 재정의할 때도 받은 배열을 제자리에서 직접 고쳐야 한다
        (반환값은 쓰이지 않는다)."""
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
        """채널 출력 해석 → (read_bit, region). 둘 다 (B, N_b, z).
        region은 2SD/3SD에서 비트별 채널 ch 열 인덱스이며 0이 가장 강한 신뢰다
        (2SD: 1-sd, 3SD: 2(1-sd) + (cc XOR sd). 매핑 근거는 cpp_sd_analysis.md 1절,
        Mapper_2/3bit_SD와 VN_Cal_SD). HD는 region이 None이다."""
        region = None
        if isinstance(channel_out, dict):
            if channel_out["mode"] != self.llr_matrix.mode:
                raise ValueError(
                    f"채널 출력 모드 {channel_out['mode']} != LLR matrix 모드 {self.llr_matrix.mode}")
            read_bit = np.asarray(channel_out["hd"], np.uint8)
            if self.llr_matrix.mode == "2SD":
                sd = np.asarray(channel_out["sd"], np.uint8)
                region = (1 - sd).astype(np.int64)
            elif self.llr_matrix.mode == "3SD":
                sd = np.asarray(channel_out["sd"], np.uint8)
                cc = np.asarray(channel_out["cc"], np.uint8)
                region = (2 * (1 - sd) + (cc ^ sd)).astype(np.int64)
        else:                                            # signed LLR 배열 (테스트 편의, HD 전용)
            if self.llr_matrix.mode != "HD":
                raise ValueError("signed LLR 배열 입력은 HD 전용 (2SD/3SD는 dict 출력 필요)")
            read_bit = (channel_out < 0).astype(np.uint8)
        _, N_b, z = read_bit.shape
        assert N_b == self.code.N_b and z == self.code.z
        return read_bit, region

    def _init_state(self, read_bit, region, log):
        """syndrome 계산(C++ iteration 0 Pre-update 등가) + CN 상태와 결과 버퍼 초기화.
        2SD/3SD는 CN에 채널 magnitude를 심는 Pre 단계까지 수행한다 (HD는 RESET 시작)."""
        code = self.code
        B, _, z = read_bit.shape
        M_b, num_edges = code.M_b, code.E
        num_dv = self.llr_matrix.num_dv
        RESET = np.float32(self._edge_mag[0])            # V_VERY_STRONG 대응

        state = _DecodeState()
        state.log = log
        state.need_by_dv = bool(log & {"bit_err_by_dv", "fail_detail"})
        state.z = z
        state.num_dv = num_dv
        state.read_bit = read_bit
        state.region = region
        state.seed_mag = (None if region is None
                          else self._seed_levels[region])    # (B, N_b, z) float32
        state.decision_bits = read_bit.copy()    # 판정비트 (C++ cwc 대응): 현재 bit 추정, 1=에러
        state.syndrome = code.syndrome(read_bit)             # (B, M_b, z) = H·read_bit
        state.prev_csw = state.syndrome.sum(axis=(-2, -1)).astype(np.int64)

        state.min1 = np.full((B, M_b, z), RESET, np.float32)
        state.min2 = np.full((B, M_b, z), RESET, np.float32)
        state.min1_pos = np.full((B, M_b, z), -1, np.int32)
        state.check_sum = np.zeros((B, M_b, z), np.uint8)
        state.edge_sgn = np.zeros((B, num_edges, z), np.uint8)
        if region is not None:
            self._seed_channel_magnitudes(state)             # SD Pre 단계 (iteration 0 대응)

        state.success = np.zeros(B, bool)
        state.decode_success_iteration = np.zeros(B, np.int32)
        state.idx_active = np.arange(B)
        state.profile = []
        # 프레임별 최종 상태 (매 iteration 활성 프레임 위치에 덮어써서 "마지막 처리
        # iteration의 값"이 남는다. 성공 프레임은 그 iteration의 값이 기록되며,
        # information 구간은 에러 0이고 parity 구간 잔여 에러는 남을 수 있다)
        state.final_err_bits = np.zeros(B, np.int64)
        state.final_info_err_bits = np.zeros(B, np.int64)
        state.final_csw = np.zeros(B, np.int64)
        state.final_err_by_dv = np.zeros((B, num_dv), np.int64)
        state.log_active, state.log_csw_sum = [], []
        state.log_err_sum, state.log_err_by_dv_sum = [], []
        return state

    def _seed_channel_magnitudes(self, state):
        """SD Pre 단계 (C++ VN_Cal_Pre + V2C_Store 대응): 채널 magnitude를
        min1/min2/min1_pos에 심는다. VNU 출력의 부호는 read_bit, 크기는 region
        magnitude다 (decoder.cpp:3663, 3666). 심은 뒤 check_sum과 edge sign은 0으로
        되돌린다 (Pre는 edge sign SRAM에 0을 쓰고, iteration 끝에 check_sum을
        syndrome으로 복사한 뒤 리셋한다: decoder.cpp:2783-2785, 2993-3008.
        syndrome 값 자체는 H·read_bit과 같으므로 재계산하지 않는다)."""
        code = self.code
        edge_row, edge_shift = code.edge_row, code.edge_shift
        for col in self._column_order(0):
            sgn_vn = state.read_bit[:, col, :]
            mag_vn = np.asarray(state.seed_mag[:, col, :], np.float32)
            for edge in code.col_edges[col]:
                row_blk, shift = edge_row[edge], edge_shift[edge]
                new_sgn = np.roll(sgn_vn, -shift, axis=-1)    # VN 정렬 → CN 정렬
                new_mag = np.roll(mag_vn, -shift, axis=-1)
                self._cnu_update(edge, True, new_sgn, new_mag, row_blk,
                                 state.min1, state.min2, state.min1_pos,
                                 state.check_sum, state.edge_sgn)
        state.check_sum.fill(0)
        state.edge_sgn.fill(0)

    def _collect_error_metrics(self, state):
        """판정비트 배열을 훑어 프레임별 에러 지표를 만든다. column 루프 안에서
        세지 않으므로 _column_order가 일부 column만 방문해도 미방문 column의 에러가
        집계에 남는다 (성공 오판정 방지).
        성공 판정(frame_err)과 정보 구간 에러 수(info_err_bits, post-FEC BER 분자)는
        information 구간(앞쪽 N_b - M_b개 column block)만 검사한다 (C++
        Check_Genie_CRC의 q < N - M 범위 대응). 전체 에러 bit 수(err_bits)와
        dv별 집계는 codeword 전체를 센다 (로그와 profile 지표용)."""
        num_info_col_blocks = self.code.N_b - self.code.M_b
        info_decision_bits = state.decision_bits[:, :num_info_col_blocks, :]
        state.frame_err = info_decision_bits.any(axis=(-2, -1))
        state.info_err_bits = info_decision_bits.sum(axis=(-2, -1), dtype=np.int64)
        state.err_bits = state.decision_bits.sum(axis=(-2, -1), dtype=np.int64)
        if state.need_by_dv:
            state.err_by_dv = np.stack(
                [state.decision_bits[:, cols, :].sum(axis=(-2, -1), dtype=np.int64)
                 for cols in self._cols_by_dv], axis=1)
        else:
            state.err_by_dv = np.zeros((state.num_active_frames, state.num_dv), np.int64)

    def _run_iteration(self, state, iteration):
        """한 iteration: Edge Clear → 테이블 row 선택 → column 루프 → CSW 갱신.
        SD의 restart iteration은 일반 계산 대신 Pre 단계를 다시 돈다."""
        RESET = np.float32(self._edge_mag[0])
        state.num_active_frames = state.read_bit.shape[0]

        state.edge_clear = self._is_edge_clear_iter(iteration)
        if state.edge_clear:
            # restart: syndrome만 유지하고 CN 상태 클리어 (Clear_Edge_Restart)
            state.min1.fill(RESET)
            state.min2.fill(RESET)
            state.min1_pos.fill(-1)
            state.check_sum.fill(0)
            state.edge_sgn.fill(0)
        if state.seed_mag is not None and self.llr_matrix.is_restart(iteration):
            # SD restart는 Pre 단계다 (C++ Is_Iter_Type_Init, decoder.cpp:6616-6624):
            # 그 iteration의 row 값(ch, th)은 쓰이지 않고, 채널 magnitude를 CN에
            # 다시 심으며, 판정은 read_bit으로 돌아간다 (cwc = Variable_mem,
            # decoder.cpp:3733-3736). 종료 시 prev_csw는 |syndrome|이 된다
            self._seed_channel_magnitudes(state)
            state.decision_bits[:] = state.read_bit
            self._collect_error_metrics(state)
            state.prev_csw = (state.check_sum ^ state.syndrome).sum(axis=(-2, -1)).astype(np.int64)
            return
        table_row_idx = self.llr_matrix.row_index(iteration, state.prev_csw)  # (num_active_frames,)
        state.cur_ch_all = self.llr_matrix.row_ch[table_row_idx]              # (num_active_frames, num_dv, ch_len)
        state.cur_ch = state.cur_ch_all[:, :, 0]                              # (num_active_frames, num_dv) HD용
        state.cur_th = self.llr_matrix.row_th[table_row_idx]                  # (num_active_frames, num_dv, th_len)

        for col in self._column_order(iteration):
            self._process_column(state, iteration, col)

        self._collect_error_metrics(state)

        state.prev_csw = (state.check_sum ^ state.syndrome).sum(axis=(-2, -1)).astype(np.int64)  # Compute_CSW

    def _process_column(self, state, iteration, col):
        """한 column: C2V 합산(sum_t) → 판정비트 갱신 → VNU 출력과 CN 갱신."""
        code = self.code
        edges = code.col_edges[col]
        edge_row, edge_shift = code.edge_row, code.edge_shift
        dv_idx = self._col_dv_idx[col]
        # flip 도메인: 채널 항은 항상 +ch (read bit는 syndrome과 genie에만 반영).
        # HD는 dv별 ch 하나, 2SD/3SD는 비트별 region이 ch 열을 고른다
        # (VN_Cal_SD 대응, cpp_sd_analysis.md 1절)
        if state.region is None:
            sum_t = np.broadcast_to(
                state.cur_ch[:, dv_idx, None],
                (state.num_active_frames, state.z)).astype(np.float32).copy()
        else:
            sum_t = np.take_along_axis(
                state.cur_ch_all[:, dv_idx, :], state.region[:, col, :],
                axis=1).astype(np.float32)
        vnu_in_list = []
        for edge in edges:
            row_blk, shift = edge_row[edge], edge_shift[edge]
            c2v = self._c2v_reconstruct(
                iteration, edge, state.min1[:, row_blk, :], state.min2[:, row_blk, :],
                state.min1_pos[:, row_blk, :], state.syndrome[:, row_blk, :],
                state.check_sum[:, row_blk, :], state.edge_sgn[:, edge, :])
            vnu_in = np.roll(c2v, shift, axis=-1)   # CN 정렬 → VN 정렬
            vnu_in_list.append(vnu_in)
            sum_t += vnu_in

        flip = self._vn_decide(sum_t)
        # 판정비트 갱신: 현재 bit 추정 = read_bit ⊕ flip (정답 all-zero 기준 1 = 에러).
        # 에러 집계는 _run_iteration이 판정비트 배열 전체로 수행한다
        state.decision_bits[:, col, :] = state.read_bit[:, col, :] ^ flip

        for edge, vnu_in in zip(edges, vnu_in_list):
            row_blk, shift = edge_row[edge], edge_shift[edge]
            vnu_out_raw = sum_t - vnu_in         # C++ sum_t − VNU_in (무포화)
            vnu_out = self._vnu_quantize(vnu_out_raw, vnu_in, state.cur_th[:, dv_idx, :])
            vnu_out = np.roll(vnu_out, -shift, axis=-1)   # VN 정렬 → CN 정렬
            new_sgn = (vnu_out < 0).astype(np.uint8)
            new_mag = np.abs(vnu_out)
            self._cnu_update(edge, state.edge_clear, new_sgn, new_mag, row_blk,
                             state.min1, state.min2, state.min1_pos, state.check_sum, state.edge_sgn)

    def _record_iteration(self, state, collect_profile):
        """로그 집계(iteration별 활성 프레임 합) + 프레임별 최종 상태 갱신 + profile."""
        if state.log:
            state.log_active.append(state.num_active_frames)
            if "csw" in state.log:
                state.log_csw_sum.append(int(state.prev_csw.sum()))
            if "bit_err" in state.log:
                state.log_err_sum.append(int(state.err_bits.sum()))
            if "bit_err_by_dv" in state.log:
                state.log_err_by_dv_sum.append(state.err_by_dv.sum(axis=0))
        state.final_err_bits[state.idx_active] = state.err_bits
        state.final_info_err_bits[state.idx_active] = state.info_err_bits
        if "fail_detail" in state.log:
            state.final_csw[state.idx_active] = state.prev_csw
            state.final_err_by_dv[state.idx_active] = state.err_by_dv
        if collect_profile:
            state.profile.append((state.num_active_frames, float(state.err_bits.mean())))

    def _check_errors(self, state, iteration):
        """에러 검사 (genie: information 구간을 정답 all-zero와 비교). 성공/실패 확정 +
        성공 프레임 배치 압축. True 반환 시 루프 종료."""
        ok = ~state.frame_err
        if ok.any():
            state.success[state.idx_active[ok]] = True
            state.decode_success_iteration[state.idx_active[ok]] = iteration
        keep = state.frame_err
        if not keep.any() or iteration == self.max_iter:
            return True
        state.idx_active = state.idx_active[keep]
        state.read_bit, state.syndrome, state.prev_csw = \
            state.read_bit[keep], state.syndrome[keep], state.prev_csw[keep]
        state.decision_bits = state.decision_bits[keep]
        if state.region is not None:
            state.region = state.region[keep]
            state.seed_mag = state.seed_mag[keep]
        state.min1, state.min2, state.min1_pos = state.min1[keep], state.min2[keep], state.min1_pos[keep]
        state.check_sum, state.edge_sgn = state.check_sum[keep], state.edge_sgn[keep]
        return False

    def _build_result(self, state, collect_profile):
        """반환 dict 조립 (형식은 decoder_main docstring 참조)."""
        out = {"success": state.success, "decode_success_iteration": state.decode_success_iteration,
               "final_err_bits": state.final_err_bits,
               "final_info_err_bits": state.final_info_err_bits}
        if collect_profile:
            out["profile"] = state.profile
        if state.log:
            out["log_active"] = np.array(state.log_active, np.int64)
            if "csw" in state.log:
                out["log_csw_sum"] = np.array(state.log_csw_sum, np.int64)
            if "bit_err" in state.log:
                out["log_err_sum"] = np.array(state.log_err_sum, np.int64)
            if "bit_err_by_dv" in state.log:
                out["log_err_by_dv_sum"] = np.array(state.log_err_by_dv_sum, np.int64)
            if "fail_detail" in state.log:
                out["final_csw"] = state.final_csw
                out["final_err_by_dv"] = state.final_err_by_dv
        return out

    # ---------- 진입 함수 ----------
    def decoder_main(self, channel_out, collect_profile=False, log=None):
        """디코딩 진입 함수.

        channel_out: channel.py 출력 dict {"mode", "hd", ...}
        (테스트 편의로 signed LLR 배열도 허용, 음수 = read bit 1).
        log: LOG_ITEMS 부분집합. 켠 항목만 수집 (속도 비용 발생).

        반환 dict:
          success:  (B,) bool. max_iter 내 genie 판정 성공 (information 구간 에러 0 기준)
          decode_success_iteration: (B,) int. 성공한 iteration 번호 (1-base). 실패 프레임은 0
          final_err_bits: (B,) int. 각 프레임의 마지막 처리 iteration 잔여 에러 bit 수
            (codeword 전체 기준. 성공 프레임도 parity 구간 잔여 에러는 남을 수 있다.
            진단용, 항상 반환)
          final_info_err_bits: (B,) int. 각 프레임의 마지막 처리 iteration
            information 구간 잔여 에러 bit 수 (성공 프레임 0. post-FEC BER 분자,
            항상 반환)
          profile:  iteration별 (활성 프레임 수, 평균 잔여 에러비트) (collect_profile 시)
          log_active/log_csw_sum/log_err_sum/log_err_by_dv_sum: iteration별 집계
            (log 항목별. 프레임 평균은 sum/active로 소비측에서 계산)
          final_csw, final_err_by_dv: (B,), (B, num_dv) (fail_detail 시)
        """
        log = set() if log is None else set(log)
        unknown_log_items = log - LOG_ITEMS   # 허용 목록에 없는 항목 = 오타 검출
        if unknown_log_items:
            raise ValueError(f"log 항목 {sorted(unknown_log_items)} 미지원 (허용: {sorted(LOG_ITEMS)})")

        read_bit, region = self._read_channel_input(channel_out)
        state = self._init_state(read_bit, region, log)
        for iteration in range(1, self.max_iter + 1):
            self._run_iteration(state, iteration)
            self._record_iteration(state, collect_profile)  # 압축 전 인덱스를 쓰므로 _check_errors보다 먼저
            if self._check_errors(state, iteration):
                break
        return self._build_result(state, collect_profile)
