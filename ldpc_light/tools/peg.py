"""PEG (Progressive Edge Growth) — base graph 생성.

column을 순서대로 처리하며, 각 VN의 edge를 "현재 그래프에서 가장 먼(local girth 최대)
CN + 최저 degree CN" 원칙으로 배치한다 (Hu-Eleftheriou-Arnold 2005의 base graph 적용).
"""
from collections import deque

import numpy as np


def _bfs_cn_depths(vn2cn, cn2vn, root_vn, M):
    """root VN에서 각 CN까지의 최단 거리(트리 전개 depth). 미도달 = -1."""
    depth = np.full(M, -1, np.int32)
    seen_vn = {root_vn}
    frontier = deque((c, 0) for c in vn2cn[root_vn])
    for c, _ in frontier:
        depth[c] = 0
    frontier = deque(frontier)
    while frontier:
        c, d = frontier.popleft()
        for v in cn2vn[c]:
            if v in seen_vn:
                continue
            seen_vn.add(v)
            for c2 in vn2cn[v]:
                if depth[c2] < 0:
                    depth[c2] = d + 1
                    frontier.append((c2, d + 1))
    return depth


def peg_base(M, col_degrees, rng, fixed_edges=None):
    """base graph 생성. 반환: connectivity (M, N) bool.

    col_degrees: 길이 N. 0인 column은 건너뜀 (fixed_edges로만 연결된 column 허용).
    fixed_edges: [(row, col), ...] — 사전 고정 edge (예: dual-diagonal parity).
    """
    N = len(col_degrees)
    conn = np.zeros((M, N), bool)
    vn2cn = [set() for _ in range(N)]
    cn2vn = [set() for _ in range(M)]
    if fixed_edges:
        for i, j in fixed_edges:
            conn[i, j] = True
            vn2cn[j].add(i)
            cn2vn[i].add(j)
    cn_deg = conn.sum(axis=1).astype(np.int64)

    for j in range(N):
        for t in range(col_degrees[j]):
            if t == 0 and not vn2cn[j]:
                cand = np.flatnonzero(cn_deg == cn_deg.min())
            else:
                depth = _bfs_cn_depths(vn2cn, cn2vn, j, M)
                unreached = np.flatnonzero(depth < 0)
                if len(unreached):
                    cand = unreached
                else:
                    cand = np.flatnonzero(depth == depth.max())   # 가장 먼 CN
                dmin = cn_deg[cand].min()
                cand = cand[cn_deg[cand] == dmin]
            i = int(rng.choice(cand))
            conn[i, j] = True
            vn2cn[j].add(i)
            cn2vn[i].add(j)
            cn_deg[i] += 1
    return conn
