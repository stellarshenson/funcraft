"""Loop seam check for a folder of rendered frames.

    python3 seamcheck.py FRAMES_DIR [--threshold 8] [--trace X0 Y0 X1 Y1]

Compares f000.png with seam-check.png (the frame at phase 1.0) and counts the
pixels whose largest channel difference exceeds the threshold; exits 1 if any
do. --trace prints the mean brightness of a region for every frame and the
step from the frame before, to find where something jumps.
"""
import argparse, glob, os
import numpy as np
from PIL import Image


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--threshold", type=int, default=8)
ap.add_argument("--trace", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
a = ap.parse_args()

diff = np.abs(load(os.path.join(a.dir, "f000.png")) - load(os.path.join(a.dir, "seam-check.png"))).max(2)
bad = int((diff > a.threshold).sum())
print(f"SEAM {a.dir}: {bad} of {diff.size} pixels differ by more than {a.threshold}/255 (largest {diff.max()})")

if a.trace:
    x0, y0, x1, y1 = a.trace
    prev = None
    for f in sorted(glob.glob(os.path.join(a.dir, "f*.png"))) + [os.path.join(a.dir, "seam-check.png")]:
        m = load(f)[y0:y1, x0:x1].mean()
        print(f"{os.path.basename(f):16s} mean {m:6.1f}" + ("" if prev is None else f"  step {m - prev:+6.1f}"))
        prev = m

raise SystemExit(1 if bad else 0)
