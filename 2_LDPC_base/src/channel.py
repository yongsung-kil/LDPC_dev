"""채널 모델: original C++ 대응 3종 (2026-08-06 사용자 지시).

| 채널 | original 대응 | 지원 모드 |
|------|---------------|----------|
| rber | MODE_CH_RBER (ecc_top.cpp Make_Dec_Input_AWGN + channel.cpp 양자화) | HD, 2SD, 3SD |
| fixed_error | MODE_CH_FIXED_ERROR (Make_Dec_Input_Ref_C_Fixed_4KB) | HD |
| strong_error | MODE_CH_STRONG_ERROR (동 함수) | 2SD |

출력: dict {"mode", "hd", "sd", "cc"} (original의 HD_input/SD_input/CC_input 대응).
  hd (B, N_b, z) uint8: read bit. sd: 2SD/3SD strong 플래그. cc: 3SD very 플래그.
  (3SD region: sd=1,cc=1 very strong / 1,0 normal strong / 0,0 normal weak / 0,1 very weak)

cw는 encoder.encode()가 만든 (B, N_b, z) {0,1} 송신 codeword
(encode()는 실제 인코딩 없이 all-zero를 반환하는 임시 함수).
base 전제: 쇼트닝/펑처링 없음 → len_noPS = N, Set_Real_Err_Pos는 항등.
난수는 original XOR25 대신 numpy Generator (사용자 결정 2026-07-29).
"""
import numpy as np

# Set_R_Offset (channel.cpp:11-29)
_R_OFFSET = {"HD": (), "2SD": (0.35,), "3SD": (0.15, 0.35, 0.55)}


def qfunc_inv(p):
    """역 Q-function. channel.cpp qfunc_inv 계수 그대로 (근사식 동일 유지)."""
    c = (-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00)
    t = np.sqrt(-2.0 * np.log(p))
    num = ((((c[0] * t + c[1]) * t + c[2]) * t + c[3]) * t + c[4]) * t + c[5]
    den = (((d[0] * t + d[1]) * t + d[2]) * t + d[3]) * t + 1.0
    return -num / den


def dev_from_rber(p):
    """RBER → N(0, var) 표준편차 (channel.cpp dev_from_RBER: SNR=qinv(p)^2/2, var=1/(2SNR))."""
    snr = qfunc_inv(p) ** 2 / 2.0
    return np.sqrt(1.0 / (2.0 * snr))


def rber_channel(code, cw, rber, random_generator, mode="HD"):
    """MODE_CH_RBER: RBER 등가 AWGN. BPSK(0→+1) + N(0,var), HD = sign(cwr),
    2SD/3SD는 |Lq=2·cwr/var|를 LLR_th_k = 2·r_offset_k/var와 비교해 region 결정."""
    if mode not in _R_OFFSET:
        raise ValueError(f"rber 채널: 모드 {mode!r} 미지원 (HD/2SD/3SD)")
    dev = dev_from_rber(rber)
    var = dev * dev
    bpsk = 1.0 - 2.0 * np.asarray(cw, np.float64)
    cwr = bpsk + random_generator.normal(0.0, dev, size=cw.shape)
    hd = (cwr < 0).astype(np.uint8)          # C++: cwr >= 0 → HD 0
    out = {"mode": mode, "hd": hd, "sd": None, "cc": None}
    if mode == "HD":
        return out
    llr_mag = np.abs(2.0 * cwr / var)        # C++ Lq_ini_m
    th = [2.0 * offset / var for offset in _R_OFFSET[mode]]
    if mode == "2SD":                        # Get_Mag_2SD
        out["sd"] = (llr_mag >= th[0]).astype(np.uint8)
    else:                                    # Get_Mag_3SD (th1<th2<th3)
        th1, th2, th3 = th
        sd = np.zeros(cw.shape, np.uint8)
        cc = np.zeros(cw.shape, np.uint8)
        sd[llr_mag >= th2] = 1               # normal strong 이상
        cc[llr_mag >= th3] = 1               # very strong
        cc[llr_mag < th1] = 1                # very weak
        out["sd"], out["cc"] = sd, cc
    return out


def _rand_positions(random_generator, batch, N, k):
    """프레임별 무작위 k개 위치 (비복원). 뽑힌 k개의 집합만 균일하고 내부 순서는
    무작위가 아니므로, fixed_error처럼 집합 전체를 같은 방식으로 쓰는 경우 전용
    (구간 슬라이스로 나눠 쓰면 안 됨, 리뷰 F1)."""
    return np.argpartition(random_generator.random((batch, N)), max(k - 1, 0), axis=1)[:, :k]


def fixed_error_channel(code, cw, n_err, random_generator, mode="HD"):
    """MODE_CH_FIXED_ERROR (HD 전용): 프레임마다 정확히 n_err bit flip (e1=n_err, c1=나머지)."""
    if mode != "HD":
        raise ValueError("fixed_error 채널은 HD 전용")
    B = cw.shape[0]
    N = code.N
    hd = np.asarray(cw, np.uint8).reshape(B, N).copy()
    err_pos = _rand_positions(random_generator, B, N, int(n_err))
    frame_idx = np.arange(B)[:, None]
    hd[frame_idx, err_pos] ^= 1
    return {"mode": "HD", "hd": hd.reshape(B, code.N_b, code.z), "sd": None, "cc": None}


def strong_error_channel(code, cw, n_err, random_generator, scr, ser, mode="2SD"):
    """MODE_CH_STRONG_ERROR (2SD 전용). E=n_err, SER=에러 중 strong 비율,
    SCR=정정 중 strong 비율:
      e2 = round(E·SER)     → 에러 + strong(sd=1)
      c2 = round((N−E)·SCR) → 정정 + strong (기본값 sd=1 유지)
      나머지 에러 (E−e2)개와 정정 c1=(N−E−c2)개는 weak(sd=0)

    2단계 추출 (사용자 확정 2026-08-07, 리뷰 F1 후속):
      ① N개 중 에러 위치 E개 추출: 집합만 쓰므로 argpartition의 집합 균일성으로 충분
      ② strong/weak 배정: 에러 E개는 행별 독립 셔플(random_generator.permuted) 뒤 앞 e2개를
         strong으로, 정정 (N−E)개는 같은 난수의 여집합 순위 하위 c1개를 weak으로
    원본(Make_Dec_Input_Ref_C_Fixed_4KB: rand_sel_ep 부분 Fisher-Yates + 구간
    슬라이스)과 통계적으로 등가다. 균일 순열의 앞 k개는 균일 부분집합과 분포가 같다."""
    if mode != "2SD":
        raise ValueError("strong_error 채널은 2SD 전용")
    if not (0.0 <= ser <= 1.0) or not (0.0 <= scr <= 1.0):
        raise ValueError(f"SER/SCR는 0~1 범위여야 함 (SER={ser}, SCR={scr})")
    B = cw.shape[0]
    N = code.N
    E = int(n_err)
    if not (0 <= E <= N):
        raise ValueError(f"에러 비트 수 {E}가 0~N({N}) 범위 밖")
    e2 = int(np.floor(E * ser + 0.5))        # C++ round
    c2 = int(np.floor((N - E) * scr + 0.5))
    c1 = N - E - c2
    hd = np.asarray(cw, np.uint8).reshape(B, N).copy()
    sd = np.ones((B, N), np.uint8)           # 초기값 strong (SD_input=1)
    frame_idx = np.arange(B)[:, None]
    rand_vals = random_generator.random((B, N))
    # ① 에러 위치 E개: rand_vals가 가장 작은 E개 (집합 균일)
    err_pos = np.argpartition(rand_vals, max(E - 1, 0), axis=1)[:, :E]
    hd[frame_idx, err_pos] ^= 1
    # ② 에러 중 weak (E−e2)개: 행별 독립 셔플 뒤 앞 e2개를 strong으로 남김
    if E > 0:
        shuffled_err_pos = random_generator.permuted(err_pos, axis=1)
        sd[frame_idx, shuffled_err_pos[:, e2:]] = 0
    # ② 정정 중 weak c1개: 에러 위치를 제외한 여집합에서 rand_vals 순위 하위 c1개
    #    (여집합 내 균일)
    if c1 > 0:
        rand_masked = rand_vals.copy()
        rand_masked[frame_idx, err_pos] = 2.0   # [0,1) 밖 값이라 에러 위치는 항상 뒤로 밀림
        weak_cor_pos = np.argpartition(rand_masked, c1 - 1, axis=1)[:, :c1]
        sd[frame_idx, weak_cor_pos] = 0
    return {"mode": "2SD", "hd": hd.reshape(B, code.N_b, code.z),
            "sd": sd.reshape(B, code.N_b, code.z), "cc": None}


CHANNELS = {
    "rber": rber_channel,
    "fixed_error": fixed_error_channel,
    "strong_error": strong_error_channel,
}

# 채널별 지원 디코딩 모드
CHANNEL_MODES = {
    "rber": ("HD", "2SD", "3SD"),
    "fixed_error": ("HD",),
    "strong_error": ("2SD",),
}
