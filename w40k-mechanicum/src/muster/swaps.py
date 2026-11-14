"""Order changes between figures of the muster crowd that overlap on the plate: counted from the scene data, no render.

A figure is a card at one depth. Two cards that overlap on the plate change their order in one frame, over their
whole overlap. This counts, for the figures at least `rows` plate rows tall, the pairs whose order changes from one
frame to the next, the plate pixels of their overlap, and the pairs that change order more than once in the loop.

    python3 src/muster/swaps.py [walk] [rows] [frames]
"""
import os, sys
import numpy as np
from scipy.spatial import cKDTree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import muster as M


def main(w=0, rows=12, frames=M.FRAMES - 1):
    w, rows, frames = int(w), float(rows), int(frames)
    c = dict(np.load(M.SCENE + "_crowd.npz"))
    ch = {key[6:]: c[key] for key in c if key.startswith("chain_")}
    g = {key[5:]: c[key][w] for key in c if key.startswith("walk_")}
    line = M.parapet(g["zp"], g["line"], g["eye"], g["span"])
    k = np.flatnonzero(c["walk"].astype(int) == w)
    of, turn, wide = c["slot"].astype(int)[k], c["turn"].astype(np.float64)[k], c["wide"][k]
    lane = ch["lane"][of].astype(int)

    def at(i):
        f, r = M.way(ch, of, turn, (i % M.FRAMES) / M.FRAMES)[:2]
        x, y, tall, depth, ok = M.place(g, f, r)
        return x, y, tall, depth, ok & (tall >= rows), f

    seen, flips, area, same, close, across, moved = {}, [], [], 0, [], [], 0.0
    x, y, tall, depth, ok, r = at(0)
    for i in range(1, frames + 1):
        x1, y1, tall1, depth1, ok1, r1 = at(i)
        moved = max(moved, float(np.abs(r1 - r).max()))
        both = np.flatnonzero(ok & ok1)
        pairs = cKDTree(np.stack([x[both], y[both]], 1)).query_pairs(float(tall[both].max()), output_type="ndarray")
        a, b = both[pairs[:, 0]], both[pairs[:, 1]]
        over_x = 0.5 * (tall[a] * wide[a] + tall[b] * wide[b]) - np.abs(x[a] - x[b])
        over_y = np.minimum(y[a], y[b]) - np.maximum(y[a] - tall[a], y[b] - tall[b])
        turned = (np.sign(depth[a] - depth[b]) != np.sign(depth1[a] - depth1[b])) & (over_x > 0) & (over_y > 0)
        flips.append(int(turned.sum()))
        area += (over_x * over_y)[turned].tolist()
        same += int((lane[a] == lane[b])[turned].sum())
        across += np.abs(r[a] - r[b])[turned].tolist()
        for p, q in zip(a[turned].tolist(), b[turned].tolist()):
            seen[(p, q)] = seen.get((p, q), 0) + 1
        if i == 1:
            near = (over_x > 0) & (over_y > 0)
            close = np.abs(depth[a] - depth[b])[near] * 1.8
            print(f"walk {w}: {ok.sum()} figures of {rows:.0f} rows and more; {near.sum()} pairs overlap on the plate, "
                  f"{(close < 0.3).sum()} of them less than 0.3 m apart in depth")
        x, y, tall, depth, ok, r = x1, y1, tall1, depth1, ok1, r1
    often, across = np.array(list(seen.values())), np.array(across)
    print(f"apart across the walk at the change, in figure heights: 1 of 10 below {np.quantile(across, 0.1):.3f}, median {np.median(across):.3f}; "
          f"{(across < 0.1).sum()} below 0.1, {(across < 0.2).sum()} below 0.2; a figure moves across the walk by {moved:.4f} per frame at most")
    print(f"{frames} frames: {np.mean(flips):.1f} pairs change order per frame (least {min(flips)}, most {max(flips)}); "
          f"overlap at the change {np.median(area):.0f} plate pixels (median), {np.quantile(area, 0.9):.0f} (9 of 10 below); "
          f"{same} of {sum(flips)} changes within one lane")
    print(f"{len(often)} pairs changed order; {(often > 1).sum()} more than once, {(often > 2).sum()} more than twice, at most {often.max()} times")


if __name__ == "__main__":
    main(*sys.argv[1:])
