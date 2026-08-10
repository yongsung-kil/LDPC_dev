"""QC-LDPC 부호 표현 및 파일 입출력.

base matrix: (M_b, N_b) int 배열. -1 = zero block, 그 외 = circulant shift 값 s (0 <= s < z).
연결 규칙: edge (i, j, s)에서 CN block i의 lane k는 VN block j의 lane (k+s) mod z와 연결.
  → VN 정렬 배열 v에서 CN 정렬로: cn = np.roll(v, -s) / CN 정렬 c를 VN 정렬로: vn = np.roll(c, +s)

파일 포맷: Ref-C(원본 C++ ecc_top.cpp Load_PCM)와 동일, 이 포맷만 지원 (2026-08-06
사용자 결정으로 구 포맷('#' 주석 + 'M_b N_b z' 헤더) 지원 제거):
  N_b M_b
  J K          (J = 최대 column degree, K = 최대 row degree)
  z
  (빈 줄)
  M_b행 x N_b열 shift 행렬 (-1 = zero block)
  (이후 내용은 무시)
주석 없이 저장하므로 C++ fscanf("%d")가 그대로 읽을 수 있다. 로드는 Ref-C의
fscanf처럼 행렬 M_b*N_b개 값까지만 읽으므로, Ref-C H_Matrix 폴더 파일처럼
행렬이 2벌 들어 있어도 첫 벌만 사용한다.
column block은 DV 내림차순 배치를 전제로 한다 (예시 부호도 재배열 완료, 2026-08-06 정정).
"""
import numpy as np


class QCCode:
    def __init__(self, base, z):
        base = np.asarray(base, dtype=np.int32)
        if base.ndim != 2:
            raise ValueError("base must be 2-D (M_b, N_b)")
        if np.any(base >= z):
            raise ValueError("shift value out of range (>= z)")
        self.base = base
        self.M_b, self.N_b = base.shape
        self.z = int(z)
        self.N = self.N_b * self.z          # codeword bit 수
        self.M = self.M_b * self.z          # parity bit 수
        self.K = self.N - self.M            # 정보 bit 수 (쇼트닝/펑처링 없음)
        self.rate = self.K / self.N

        rows, cols = np.nonzero(base >= 0)
        order = np.lexsort((rows, cols))    # column 우선 정렬 (column-loop 친화)
        self.edge_row = rows[order].astype(np.int32)
        self.edge_col = cols[order].astype(np.int32)
        self.edge_shift = base[rows[order], cols[order]].astype(np.int32)
        self.E = len(self.edge_row)
        self.col_edges = [np.flatnonzero(self.edge_col == j) for j in range(self.N_b)]
        self.row_deg = np.bincount(self.edge_row, minlength=self.M_b)
        self.col_deg = np.bincount(self.edge_col, minlength=self.N_b)

    # ---------- 파일 입출력 (Ref-C 포맷) ----------
    def save(self, path):
        """Ref-C 포맷 저장: N_b M_b / J K / z / 빈 줄 / shift 행렬. 주석 없음."""
        J, K = int(self.col_deg.max()), int(self.row_deg.max())
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{self.N_b} {self.M_b}\n{J} {K}\n{self.z}\n\n")
            for i in range(self.M_b):
                f.write(" ".join(str(v) for v in self.base[i]) + "\n")

    @classmethod
    def load(cls, path):
        """Ref-C 포맷 로드: N_b M_b / J K / z / 빈 줄 / shift 행렬.

        Ref-C(ecc_top.cpp Load_PCM)의 fscanf처럼 행렬 M_b*N_b개 값까지만 읽고
        이후 내용(두 번째 행렬 등)은 무시한다.
        """
        with open(path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        head = lines[0].split()
        if len(head) != 2:
            raise ValueError(
                f"{path}: Ref-C 헤더가 아님 (첫 줄 {lines[0]!r}, 'N_b M_b' 정수 2개여야 함)")
        N_b, M_b = map(int, head)
        J, K = map(int, lines[1].split())
        z = int(lines[2])
        vals = " ".join(lines[3:]).split()
        if len(vals) < M_b * N_b:
            raise ValueError(f"{path}: 행렬 원소 수 {len(vals)} < {M_b}x{N_b}")
        base = np.array([int(v) for v in vals[:M_b * N_b]], dtype=np.int32)
        code = cls(base.reshape(M_b, N_b), z)
        if code.col_deg.max() > J or code.row_deg.max() > K:
            raise ValueError(
                f"{path}: 헤더 J/K=({J},{K})보다 실제 degree"
                f"({int(code.col_deg.max())},{int(code.row_deg.max())})가 큼")
        return code

    # ---------- 검증 유틸 ----------
    def syndrome(self, bits):
        """bits: (..., N_b, z) 0/1. 반환: (..., M_b, z) syndrome (mod 2)."""
        bits = np.asarray(bits)
        syn = np.zeros(bits.shape[:-2] + (self.M_b, self.z), dtype=bits.dtype)
        for e in range(self.E):
            i, j, s = self.edge_row[e], self.edge_col[e], self.edge_shift[e]
            syn[..., i, :] ^= np.roll(bits[..., j, :], -s, axis=-1)
        return syn

    def count_cycles4(self):
        """lifting 후 남은 길이-4 사이클 수 (base 패턴 × shift 조건 mod z)."""
        cnt = 0
        by_row = {}
        for e in range(self.E):
            by_row.setdefault(int(self.edge_row[e]), []).append(e)
        for i1 in range(self.M_b):
            for i2 in range(i1 + 1, self.M_b):
                cols1 = {int(self.edge_col[e]): int(self.edge_shift[e]) for e in by_row.get(i1, [])}
                cols2 = {int(self.edge_col[e]): int(self.edge_shift[e]) for e in by_row.get(i2, [])}
                shared = sorted(set(cols1) & set(cols2))
                for a in range(len(shared)):
                    for b in range(a + 1, len(shared)):
                        j1, j2 = shared[a], shared[b]
                        if (cols1[j1] - cols2[j1] + cols2[j2] - cols1[j2]) % self.z == 0:
                            cnt += 1
        return cnt

    def summary(self):
        dv = np.bincount(self.col_deg)
        dc = np.bincount(self.row_deg)
        return (f"QC-LDPC: base {self.M_b}x{self.N_b}, z={self.z}, "
                f"N={self.N}, K={self.K}, rate={self.rate:.4f}, E(base)={self.E}\n"
                f"  col degree hist: {{{', '.join(f'{d}:{c}' for d, c in enumerate(dv) if c)}}}\n"
                f"  row degree hist: {{{', '.join(f'{d}:{c}' for d, c in enumerate(dc) if c)}}}")
