"""Where a render of the muster scene differs from the accepted one, over the whole frame.

    python3 src/muster/differ.py <accepted frames> <new frames> [x0,y0,x1,y1 ...]

For every frame number that both folders hold: the regions where the two frames differ, as boxes on the plate with
the greatest difference in each. A box given on the command line is a region that was meant to change; the regions
inside such a box are counted and not listed. A change outside them is a fault until it is looked at.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

LIMIT, AREA = 10, 400                          # a region differs by more than LIMIT of 255, evened over 3 pixels, on more than AREA pixels with its border


def regions(a, b):
    d = cv2.GaussianBlur(np.abs(a - b).mean(-1), (0, 0), 3)
    stats = cv2.connectedComponentsWithStats(cv2.dilate((d > LIMIT).astype(np.uint8), np.ones((15, 15), np.uint8)), connectivity=8)[2][1:]
    return [((int(s[0]), int(s[1]), int(s[0] + s[2]), int(s[1] + s[3])), round(float(d[s[1]:s[1] + s[3], s[0]:s[0] + s[2]].max()), 1))
            for s in stats if s[4] > AREA]


if __name__ == "__main__":
    old, new = sys.argv[1:3]
    meant = [tuple(int(v) for v in box.split(",")) for box in sys.argv[3:]]
    for name in sorted(set(os.listdir(old)) & set(os.listdir(new))):
        if not name.startswith("f"):
            continue
        a, b = (np.asarray(Image.open(os.path.join(folder, name)).convert("RGB")).astype(np.float32) for folder in (old, new))
        found = regions(a, b)
        rest = [(box, peak) for box, peak in found if not any(box[0] >= m[0] and box[1] >= m[1] and box[2] <= m[2] and box[3] <= m[3] for m in meant)]
        print(f"{name}: mean difference {np.abs(a - b).mean():.2f} of 255; {len(found)} regions differ, {len(rest)} outside the boxes given:", rest)
