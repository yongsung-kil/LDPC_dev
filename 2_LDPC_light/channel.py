"""채널 모델: 송신 codeword(cw)를 받아 read-bit/LLR을 만든다 (plan.md §7 #6).

원본 channel.cpp 대응 범위: 에러 주입 + read-bit/구간 결정까지.
여기서는 vanilla 뼈대로 BSC(hard)와 AWGN(soft, 균일 양자화)을 제공한다.
실물 HD/2SD/3SD region + VN 테이블 매핑은 실물 LLR 테이블 반입 후 추가 (plan.md §4 선행 조건).

반환 LLR 부호 규칙: +값 = bit 0 신뢰. cw는 encoder.encode()가 만든 (batch, N_b, z) {0,1}
송신 codeword다. 현재는 encoder가 스텁이라 항상 all-zero이지만, 채널 함수는 그 값을 그대로
따른다 (인코더가 실제로 채워지면 채널 수정 없이 그대로 동작).
"""
import numpy as np


def bsc_llr(code, cw, rber, rng, mag=8.0):
    """BSC(hard-decision read). cw: (batch, N_b, z) {0,1} 송신 codeword.
    rber 확률로 read bit flip, LLR = ±mag.
    mag: 스칼라 또는 (N_b,) column block별 값 (llr_tables.ch_mag_by_col 참조)."""
    mag = np.asarray(mag, np.float32)
    if mag.ndim == 1:
        mag = mag.reshape(1, -1, 1)          # (1, N_b, 1) → 브로드캐스트
    batch = cw.shape[0]
    flip = rng.random((batch, code.N_b, code.z)) < rber
    read_bit = np.asarray(cw, np.uint8) ^ flip.astype(np.uint8)
    return np.where(read_bit == 0, mag, -mag).astype(np.float32)


def fixed_error_llr(code, n_err, batch, rng, mag=8.0):
    """fixed-error(hard-decision read). 프레임마다 정확히 n_err개 비트를
    무작위 위치(전체 codeword N bit 중 비복원 추출)에 flip. 원본 channel.cpp의
    fixed-error 패턴 모드 대응. mag: 스칼라 또는 (N_b,) column block별 값."""
    N = code.N
    mag = np.asarray(mag, np.float32)
    flat = (np.full(N, float(mag), np.float32) if mag.ndim == 0
            else np.repeat(mag, code.z).astype(np.float32))     # bit = j*z + l
    llr = np.tile(flat, (batch, 1))
    # 행별 무작위 실수의 하위 n_err 인덱스 = 비복원 무작위 위치 추출
    pos = np.argpartition(rng.random((batch, N)), n_err - 1, axis=1)[:, :n_err]
    np.put_along_axis(llr, pos, -flat[pos], axis=1)
    return llr.reshape(batch, code.N_b, code.z)


def awgn_llr(code, cw, ebn0_db, rng, step=0.5, ch_clip=31, quantize=True):
    """BPSK + AWGN. cw: (batch, N_b, z) {0,1} 송신 codeword. Eb/N0 기준 (rate 반영).
    LLR = 2y/sigma^2 → step 균일 양자화 + 클리핑."""
    ebn0 = 10.0 ** (ebn0_db / 10.0)
    sigma2 = 1.0 / (2.0 * code.rate * ebn0)
    batch = cw.shape[0]
    bpsk = 1.0 - 2.0 * np.asarray(cw, np.float32)    # 0 -> +1, 1 -> -1
    y = bpsk + rng.normal(0.0, np.sqrt(sigma2), size=(batch, code.N_b, code.z))
    llr = (2.0 / sigma2) * y
    if quantize:
        llr = np.clip(np.rint(llr / step), -ch_clip, ch_clip)
    return llr.astype(np.float32)


def awgn_rber(ebn0_db, rate):
    """AWGN에서의 raw BER (hard-decision 기준) = Q(sqrt(2*R*Eb/N0))."""
    from math import erfc, sqrt
    ebn0 = 10.0 ** (ebn0_db / 10.0)
    return 0.5 * erfc(sqrt(rate * ebn0))
