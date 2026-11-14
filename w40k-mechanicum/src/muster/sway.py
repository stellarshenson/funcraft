"""How every cloth of the muster scene stands and moves over the loop, in metres and in plate pixels: its mean offset
from rest, its change in time, and the width of its lower quarter against its width at rest.

A cloth that the wind holds away from rest looks skewed, and one that is fastened along its post is wider or narrower
at its lower end than at rest; a cloth whose change in time is small does not seem to move.

    python3 src/muster/sway.py [banners.npz wind.npz]      # default: wip/scene3d/muster_banners.npz, muster_wind.npz
"""
import os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import muster as M


def main(banners=M.SCENE + "_banners.npz", wind=M.SCENE + "_wind.npz"):
    b, w, d = np.load(banners), np.load(wind), np.load(M.SCENE + "_back.npz")
    K, (H, W) = d["intrinsics"], d["depth"].shape
    px = lambda p: np.stack([(p[..., 0] / p[..., 1] * K[0, 0] + K[0, 2]) * W - 0.5, (-p[..., 2] / p[..., 1] * K[1, 1] + K[1, 2]) * H - 0.5], -1)
    posts = np.load(M.SCENE + "_posts.npz")
    print("lower quarter of each cloth over the loop: depth offset from rest and its change in time (m) | in the picture: mean shift, "
          "change in time, greatest shift of a vertex (px, + is right) | width at rest, mean (px) | cloth right of the left side of its post: "
          "share of the vertices on average and in the worst frame (%), farthest (px)")
    for k, el in enumerate([el for el in M.ELEMENTS if el["kind"] == "banner"], 1):
        v, p = b[f"v{k}"], w[f"p{k}"]
        rest, pic = px(v), px(p)
        low = rest[:, 1] > rest[:, 1].min() + 0.75 * (rest[:, 1].max() - rest[:, 1].min())
        wide = (pic[:, low, 0].max(1) - pic[:, low, 0].min(1)).mean()
        at, r = posts[f"{el['id']}_at"], float(np.median(posts[f"{el['id']}_r"]))
        side = np.polyval(np.polyfit(at[:, 1], at[:, 0], 1), pic[..., 1]) - r      # the left side of the post at the row of each vertex
        over = np.where((pic[..., 1] > at[:, 1].min()) & (pic[..., 1] < at[:, 1].max()), pic[..., 0] - side, -np.inf)
        beyond = (over > 1).mean(1) * 100
        print(f"  {el['id']:4s} {(p[:, low, 1] - v[low, 1]).mean():+.2f} {p[:, low, 1].std(0).mean():.3f} | {(pic[:, low, 0] - rest[low, 0]).mean():+6.1f} "
              f"{pic[:, low, 0].std(0).mean():5.1f} {np.abs(pic[..., 0] - rest[:, 0]).max():6.1f} | {rest[low, 0].max() - rest[low, 0].min():6.1f} {wide:6.1f} | "
              f"{beyond.mean():5.1f} {beyond.max():5.1f} {max(over.max(), 0):6.1f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
